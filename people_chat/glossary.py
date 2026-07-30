"""
Glossary YAML generator and validator for People Chat.
Reads database schema → generates YAML template with column descriptions.
Validates YAML against actual schema to catch drift.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from . import schema as db_schema

# ─── YAML Template Generation ───────────────────────────

COMMON_HR_COLUMNS = {
    "employee #": "Unique employee identifier",
    "employee_#": "Unique employee identifier",
    "eeid": "Enterprise employee ID",
    "first name": "Employee's legal first name",
    "first_name": "Employee's legal first name",
    "last name": "Employee's legal last name",
    "last_name": "Employee's legal last name",
    "preferred name": "Name the employee prefers to go by",
    "preferred_name": "Name the employee prefers to go by",
    "job title": "Current position title",
    "job_title": "Current position title",
    "department": "Department name (e.g., Engineering, Sales, Marketing)",
    "division": "Top-level organizational division (e.g., G&A, Product, Tech)",
    "reporting to": "Manager's Employee ID",
    "reporting_to": "Manager's Employee ID",
    "hire date": "Date employee started at the company",
    "hire_date": "Date employee started at the company",
    "work email": "Company email address",
    "work_email": "Company email address",
    "birth date": "Employee's date of birth",
    "birth_date": "Employee's date of birth",
    "gender": "Employee gender identity",
    "employment status": "Current employment status (Active, Terminated, etc.)",
    "employment_status": "Current employment status (Active, Terminated, etc.)",
    "termination date": "Date employee left the company. NULL = still employed.",
    "termination_date": "Date employee left the company. NULL = still employed.",
    "pay rate": "Annual base salary in USD",
    "pay_rate": "Annual base salary in USD",
    "time type": "How pay is calculated (Hourly or Salary)",
    "time_type": "How pay is calculated (Hourly or Salary)",
    "exempt": "FLSA exemption status (Exempt or Non-Exempt)",
    "pay schedule": "How often employee is paid (Bi-Weekly, Monthly, etc.)",
    "pay_schedule": "How often employee is paid (Bi-Weekly, Monthly, etc.)",
    "radford level": "Radford job level (S1-S6, P1-P6, M1-M6, E1-E6)",
    "radford_level": "Radford job level (S1-S6, P1-P6, M1-M6, E1-E6)",
    "bonus type": "Type of bonus plan (Annual Bonus, Commission, No Bonus)",
    "bonus_type": "Type of bonus plan (Annual Bonus, Commission, No Bonus)",
    "bonus amount": "Annual bonus target amount in USD",
    "bonus_amount": "Annual bonus target amount in USD",
    "annualized pay": "Total annual compensation including bonus/commission in USD",
    "annualized_pay": "Total annual compensation including bonus/commission in USD",
    "annual pay": "Annual base salary in USD (same as Pay rate)",
    "annual_pay": "Annual base salary in USD (same as Pay rate)",
    "people leader?": "Whether the employee manages direct reports (Yes/No)",
    "people_leader?": "Whether the employee manages direct reports (Yes/No)",
    "people leader": "Whether the employee manages direct reports (Yes/No)",
    "people_leader": "Whether the employee manages direct reports (Yes/No)",
    "hrbp": "HR Business Partner assigned to this employee/org",
    "job code": "Internal job code referencing the Job Catalog",
    "job_code": "Internal job code referencing the Job Catalog",
    "band number": "Numeric band within Radford level (1-6)",
    "band_number": "Numeric band within Radford level (1-6)",
    "min": "Minimum of the salary band for this position",
    "mid": "Midpoint of the salary band for this position",
    "max": "Maximum of the salary band for this position",
    "rp %": "Range penetration percentage (actual pay as % of band midpoint)",
    "rp%": "Range penetration percentage (actual pay as % of band midpoint)",
    "rp_pct": "Range penetration percentage (actual pay as % of band midpoint)",
    "position title": "Formal job title from the Job Catalog",
    "position_title": "Formal job title from the Job Catalog",
    "job family": "Career track / job family grouping",
    "job_family": "Career track / job family grouping",
    "active or inactive": "Whether the job catalog entry is currently active",
    "active_or_inactive": "Whether the job catalog entry is currently active",
    "hourly or salary": "Whether the position is paid hourly or salaried",
    "hourly_or_salary": "Whether the position is paid hourly or salaried",
    "exemption status": "FLSA exemption classification",
    "exemption_status": "FLSA exemption classification",
    "eeoc category": "EEO job category for compliance reporting",
    "eeoc_category": "EEO job category for compliance reporting",
    "equity structure": "Type of equity compensation (Options, RSU, etc.)",
    "equity_structure": "Type of equity compensation (Options, RSU, etc.)",
    "salary_or_hourly": "Whether the employee is salaried or hourly",
    "annual_salary": "Annual salary amount in USD",
    "hourly_rate": "Hourly pay rate in USD",
    "typical_hours": "Standard hours per week for hourly employees",
}

COMMON_HR_METRICS = {
    "headcount": {
        "description": "Total number of active employees",
        "formula": "COUNT(*) WHERE employment_status = 'Active'"
    },
    "turnover_rate": {
        "description": "Voluntary separations during a period divided by average headcount, expressed as a percentage",
        "formula": "(voluntary_exits_in_period / avg_headcount_in_period) * 100"
    },
    "avg_tenure_years": {
        "description": "Average employee tenure in years (based on hire date vs today or termination date)",
        "formula": "AVG(JULIANDAY(COALESCE(termination_date, CURRENT_DATE)) - JULIANDAY(hire_date)) / 365.25"
    },
    "compensation_ratio": {
        "description": "Salary divided by the midpoint of the salary band. 1.0 = paid at market rate.",
        "formula": "pay_rate / mid"
    },
    "gender_diversity": {
        "description": "Gender distribution across organization",
        "formula": "COUNT(*) GROUP BY gender"
    },
    "avg_salary_by_department": {
        "description": "Average salary grouped by department",
        "formula": "AVG(pay_rate) GROUP BY department"
    },
    "promotion_rate": {
        "description": "Percentage of employees who received a promotion in a period",
        "formula": "pending — needs job_history table"
    }
}


def normalize_column_name(name: str) -> str:
    """Normalize column name for matching against common names dict."""
    return name.strip().lower().replace("-", "_").replace(":", "").replace("?", "")


def generate(db_path: str, table_name: str, output_path: str | None = None) -> str:
    """
    Generate a glossary YAML template from database schema.
    
    Args:
        db_path: Path to SQLite database
        table_name: Name of the table to generate glossary for
        output_path: Optional file path to write the YAML
    
    Returns:
        The generated YAML string
    """
    # Get table info from schema
    info = db_schema.introspect(db_path, table_name)
    table_info = info["tables"].get(table_name, {})
    columns = table_info.get("columns", [])
    
    if not columns:
        raise ValueError(f"No columns found for table '{table_name}'")
    
    # Get sample data for value hints
    sample_rows = table_info.get("sample_rows", [])
    sample = sample_rows[0] if sample_rows else {}
    
    # Get null counts
    
    # Build glossary structure
    glossary: dict[str, Any] = {
        "data_source": Path(db_path).stem,
        "description": f"Auto-generated glossary for table '{table_name}'",
        "generated_at": str(datetime.now(UTC).date()),
        "columns": {}
    }
    
    for col in columns:
        col_name = col["name"]
        normalized = normalize_column_name(col_name)
        col_type = col["type"]
        nullable = col["nullable"]
        is_pk = col["pk"]
        
        # Try to match against common HR column names
        description = COMMON_HR_COLUMNS.get(normalized, "")
        
        # Get sample value for hint
        sample_value = sample.get(col_name)
        sample_hint = ""
        if sample_value is not None:
            sample_hint = f" (e.g., {sample_value})"
        
        # Build column entry
        entry: dict[str, Any] = {
            "type": col_type.lower(),
            "nullable": nullable,
            "description": sample_hint if not description else description + sample_hint,
        }
        
        if is_pk:
            entry["primary_key"] = True
        
        glossary["columns"][col_name] = entry
    
    # Add metrics section (pre-populated common HR metrics)
    glossary["metrics"] = {}
    for metric_name, metric_info in COMMON_HR_METRICS.items():
        glossary["metrics"][metric_name] = {
            "description": metric_info["description"],
            "formula": metric_info["formula"]
        }
    
    # Generate YAML
    yaml_str = yaml.dump(
        glossary,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=100
    )
    
    # Write to file if output_path provided
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(yaml_str)
    
    return yaml_str


# ─── Glossary Validation ────────────────────────────────

def validate(db_path: str, glossary_path: str) -> list[dict[str, Any]]:
    """
    Validate a glossary YAML file against the actual database schema.
    
    Returns list of issues found. Each issue has:
    - severity: "error" or "warning"
    - message: description of the issue
    - column: column name (if applicable)
    """
    issues = []
    
    # Load glossary
    glossary_path = Path(glossary_path)
    if not glossary_path.exists():
        return [{"severity": "error", "message": f"Glossary file not found: {glossary_path}", "column": None}]
    
    with open(glossary_path) as f:
        glossary = yaml.safe_load(f)
    
    if not glossary:
        return [{"severity": "error", "message": "Glossary file is empty", "column": None}]
    
    # Check required top-level fields
    if "columns" not in glossary:
        issues.append({"severity": "error", "message": "Glossary is missing 'columns' section", "column": None})
        return issues
    
    # Get actual schema
    tables = db_schema.get_tables(db_path)
    if not tables:
        issues.append({"severity": "error", "message": f"No tables found in database: {db_path}", "column": None})
        return issues
    
    # Validate against each table
    glossary_columns = set(glossary.get("columns", {}).keys())
    
    for table_name in tables:
        actual_columns = db_schema.get_columns(db_path, table_name)
        actual_names = {c["name"] for c in actual_columns}
        
        # Check for columns in glossary that don't exist in DB
        for col_name in glossary_columns:
            if col_name not in actual_names:
                issues.append({
                    "severity": "warning",
                    "message": f"Column '{col_name}' is in glossary but not found in table '{table_name}'",
                    "column": col_name
                })
        
        # Check for columns in DB that are missing from glossary
        for col in actual_columns:
            if col["name"] not in glossary_columns:
                issues.append({
                    "severity": "warning",
                    "message": f"Column '{col['name']}' in table '{table_name}' is missing from glossary (type: {col['type']})",
                    "column": col["name"]
                })
        
        # Check for empty descriptions
        for col_name, col_config in glossary.get("columns", {}).items():
            if col_name in actual_names:
                desc = col_config.get("description", "")
                if not desc or desc.strip() == "":
                    issues.append({
                        "severity": "warning",
                        "message": f"Column '{col_name}' has an empty description",
                        "column": col_name
                    })
    
    # Check metrics section
    if "metrics" in glossary:
        for metric_name, metric_config in glossary["metrics"].items():
            if isinstance(metric_config, dict):
                if not metric_config.get("description"):
                    issues.append({
                        "severity": "warning",
                        "message": f"Metric '{metric_name}' has no description",
                        "column": metric_name
                    })
                if not metric_config.get("formula"):
                    issues.append({
                        "severity": "warning",
                        "message": f"Metric '{metric_name}' has no formula",
                        "column": metric_name
                    })
    
    return issues


def format_validation_results(issues: list[dict[str, Any]]) -> str:
    """Format validation results as a human-readable string."""
    if not issues:
        return "✅ Glossary is valid — all columns accounted for."
    
    lines = []
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    
    if errors:
        lines.append(f"❌ {len(errors)} error(s):")
        for issue in errors:
            lines.append(f"  - {issue['message']}")
    
    if warnings:
        lines.append(f"⚠️  {len(warnings)} warning(s):")
        for issue in warnings:
            col = f"[{issue['column']}] " if issue.get("column") else ""
            lines.append(f"  - {col}{issue['message']}")
    
    return "\n".join(lines)
