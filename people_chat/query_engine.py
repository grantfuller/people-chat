"""
Query Engine — the brain of People Chat.
Takes natural language questions → generates SQL via LLM → executes → returns results.
"""

import re
import sqlite3
from pathlib import Path
from typing import Any

from . import config as cfg
from . import schema as db_schema
from .llm import get_provider

# ─── Prompt Templates ────────────────────────────────────

PROMPTS_DIR = Path(__file__).parent / "prompts"

def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text().strip()
    return f"# {filename} not found"


def _detect_intent(question: str) -> str:
    """Detect if the user wants a chart, table, or auto."""
    chart_keywords = ["chart", "graph", "plot", "visualize", "distribution", "trend"]
    question_lower = question.lower()
    for kw in chart_keywords:
        if kw in question_lower:
            return "chart"
    return "auto"


def build_prompt(
    question: str,
    db_path: str,
    table_name: str | None = None,
    glossary_path: str | None = None,
) -> str:
    """
    Build the complete prompt for the LLM.
    
    Injects: schema, glossary, metrics, few-shot examples, and the user question.
    """
    # Load system prompt
    system_prompt = _load_prompt("system.md")
    
    # Get schema
    tables = db_schema.get_tables(db_path)
    schema_parts = []
    for tbl in tables:
        if table_name and tbl != table_name:
            continue
        columns = db_schema.get_columns(db_path, tbl)
        schema_parts.append(f"Table: {tbl}")
        for col in columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            pk = " PK" if col["pk"] else ""
            schema_parts.append(f"  {col['name']} ({col['type']}, {nullable}{pk})")
    
    schema_text = "\n".join(schema_parts) if schema_parts else f"Table: {table_name or 'unknown'}\n  (no columns found)"
    
    # Get glossary
    glossary_text = "# No glossary loaded"
    if glossary_path:
        try:
            with open(glossary_path) as f:
                import yaml
                glossary_data = yaml.safe_load(f)
                if glossary_data:
                    gloss_parts = ["## Column Definitions"]
                    for col_name, col_info in glossary_data.get("columns", {}).items():
                        desc = col_info.get("description", "")
                        if desc:
                            gloss_parts.append(f"  {col_name}: {desc}")
                    
                    metrics = glossary_data.get("metrics", {})
                    if metrics:
                        gloss_parts.append("\n## HR Metric Definitions")
                        for m_name, m_info in metrics.items():
                            desc = m_info.get("description", "")
                            formula = m_info.get("formula", "")
                            if desc:
                                gloss_parts.append(f"  {m_name}: {desc}")
                            if formula:
                                gloss_parts.append(f"    Formula: {formula}")
                    
                    glossary_text = "\n".join(gloss_parts)
        except Exception:  # noqa: BLE001  # noqa: BLE001
            glossary_text = "# Error loading glossary"
    
    # Load few-shot examples
    few_shot = _load_prompt("few_shot.sql")
    
    # Detect intent
    intent = _detect_intent(question)
    intent_note = ""
    if intent == "chart":
        intent_note = "\nThe user wants a CHART. Generate a query that produces 2+ numeric columns suitable for visualization (x-axis + y-axis values)."
    
    # Build the full prompt
    prompt = f"""{system_prompt}

## DATABASE SCHEMA
{schema_text}

## FIELD GLOSSARY
{glossary_text}

## EXAMPLE QUESTIONS AND QUERIES
These are examples of how to translate HR questions into SQLite queries:

{few_shot}

## USER QUESTION
{question}{intent_note}

Respond with:
1. The SQL query in a markdown code block
2. A brief 1-2 sentence explanation
"""
    return prompt


# ─── SQL Extraction ──────────────────────────────────────

def extract_sql(response: str) -> str | None:
    """Extract SQL from LLM response. Handles markdown code blocks and plain text."""
    # Try to find SQL in markdown code blocks
    sql_blocks = re.findall(r'```sql\s*([\s\S]*?)```', response, re.IGNORECASE)
    if sql_blocks:
        return sql_blocks[0].strip()
    
    # Try generic code blocks
    code_blocks = re.findall(r'```\s*([\s\S]*?)```', response)
    for block in code_blocks:
        block = block.strip()
        if block.upper().startswith(('SELECT', 'WITH', '--')):
            return block
    
    # Try to find SELECT statement in plain text
    lines = response.strip().split('\n')
    select_lines = []
    in_sql = False
    for line in lines:
        if line.strip().upper().startswith('SELECT'):
            in_sql = True
        if in_sql:
            select_lines.append(line)
            if line.strip().endswith(';'):
                break
    
    if select_lines:
        return '\n'.join(select_lines)
    
    return None


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate that SQL is read-only and safe to execute."""
    sql_upper = sql.strip().upper()
    
    # Check for dangerous operations
    dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'PRAGMA', 'ATTACH', 'REPLACE', 'VACUUM']
    # Use regex to match whole words only
    for keyword in dangerous:
        if re.search(r'\b' + keyword + r'\b', sql_upper):
            return False, f"Query contains forbidden keyword: {keyword}"
    
    # Must start with SELECT or WITH
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH') and not sql_upper.startswith('--'):
        return False, "Query must start with SELECT or WITH"
    
    # Check for multiple statements (semicolons in middle of query)
    stripped = sql.strip()
    # Remove comments
    no_comments = re.sub(r'--.*', '', stripped)
    # Count semicolons outside of string literals
    semicolon_count = no_comments.count(';')
    if semicolon_count > 1:
        return False, "Multiple SQL statements detected (only single SELECT allowed)"
    if semicolon_count == 1 and not stripped.rstrip().endswith(';'):
        return False, "Unexpected semicolon in middle of query"
    
    return True, "OK"


# ─── SQL Execution ───────────────────────────────────────

def execute_sql(db_path: str, sql: str) -> dict[str, Any]:
    """Execute a SQL query and return structured results."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "error": None
        }
    except sqlite3.OperationalError as e:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(e)
        }
    finally:
        conn.close()


def extract_explanation(response: str) -> str:
    """Extract the explanation part from the LLM response (everything after the SQL block)."""
    # Remove SQL blocks
    text = re.sub(r'```sql\s*[\s\S]*?```', '', response)
    text = re.sub(r'```\s*[\s\S]*?```', '', text)
    text = text.strip()
    
    if not text:
        return ""
    
    # Remove the user question from the beginning if it appears
    lines = text.split('\n')
    # Filter out lines that look like code/query remnants
    meaningful = [l for l in lines if l.strip() and not l.strip().startswith('```')]
    
    return '\n'.join(meaningful).strip()


# ─── Retry Logic ─────────────────────────────────────────

MAX_SQL_RETRIES = 1


def _build_retry_prompt(original_question: str, bad_sql: str, error_message: str) -> str:
    """Build a prompt asking the LLM to fix broken SQL."""
    return f"""The SQL query below failed with an error. Please fix it.

ORIGINAL QUESTION: {original_question}

FAILED SQL:
{bad_sql}

ERROR:
{error_message}

Please respond with the corrected SQL query in a markdown code block, followed by a brief explanation.
"""


def _check_needs_info(response_text: str) -> bool:
    """Check if the LLM is saying it needs more information (not a SQL failure)."""
    # If the response has a SQL block, it's trying to answer
    if re.search(r'```sql', response_text, re.IGNORECASE):
        return False
    
    # Check for "I need more information" patterns
    info_patterns = [
        "i need more information",
        "i don't have enough information",
        "the data doesn't include",
        "cannot answer this question",
        "i'm not able to",
        "i cannot determine",
        "the available data",
        "does not contain",
        "no information about",
        "missing from the schema",
        "not available in the schema",
        "can't find",
        "could you provide",
        "could you clarify",
    ]
    
    response_lower = response_text.lower()
    for pattern in info_patterns:
        if pattern in response_lower:
            return True
    
    return False


# ─── Main Query Function ─────────────────────────────────

def ask(
    question: str,
    db_path: str,
    table_name: str | None = None,
    glossary_path: str | None = None,
    config: cfg.ProviderConfig | None = None,
) -> dict[str, Any]:
    """
    Ask a natural language question about your HR data.
    
    Args:
        question: The user's question in plain English
        db_path: Path to the SQLite database
        table_name: Optional specific table to query
        glossary_path: Optional path to glossary YAML
        config: Optional provider config (uses env vars by default)
    
    Returns:
        Dict with: question, sql, explanation, results (columns + rows), 
                  intent, success, error
    """
    # Build the prompt
    prompt = build_prompt(question, db_path, table_name, glossary_path)
    
    # Load system prompt
    system_prompt = _load_prompt("system.md")
    
    # Send to LLM
    if config is None:
        config = cfg.ProviderConfig()
        config = cfg.apply_defaults(config)
    
    provider = get_provider(config)
    llm_response = provider.send_prompt(prompt, system=system_prompt)
    
    # Check if LLM needs more information
    if _check_needs_info(llm_response.content):
        # Extract the explanation from the response
        explanation = extract_explanation(llm_response.content)
        if not explanation:
            explanation = llm_response.content.strip()[:500]
        
        return {
            "question": question,
            "sql": None,
            "explanation": explanation,
            "results": None,
            "intent": _detect_intent(question),
            "success": False,
            "needs_info": True,
            "error": explanation,
            "model_used": llm_response.model,
            "provider_used": llm_response.provider,
        }
    
    # Extract SQL
    sql = extract_sql(llm_response.content)
    
    if not sql:
        # Check if the response is a "needs info" that we missed
        explanation = extract_explanation(llm_response.content) or llm_response.content.strip()[:500]
        return {
            "question": question,
            "sql": None,
            "explanation": explanation,
            "results": None,
            "intent": _detect_intent(question),
            "success": False,
            "needs_info": True,
            "error": "Could not extract SQL from LLM response. The LLM may need more information.",
            "model_used": llm_response.model,
            "provider_used": llm_response.provider,
        }
    
    # Validate SQL
    is_valid, validation_msg = validate_sql(sql)
    if not is_valid:
        return {
            "question": question,
            "sql": sql,
            "explanation": validation_msg,
            "results": None,
            "intent": _detect_intent(question),
            "success": False,
            "error": f"SQL validation failed: {validation_msg}",
            "model_used": llm_response.model,
            "provider_used": llm_response.provider,
        }
    
    # Execute SQL (with retry)
    results = execute_sql(db_path, sql)
    
    if not results["success"]:
        # First retry: send the error back to the LLM
        retry_prompt = _build_retry_prompt(question, sql, results["error"])
        retry_response = provider.send_prompt(retry_prompt, system=system_prompt)
        
        retry_sql = extract_sql(retry_response.content)
        if retry_sql:
            retry_valid, _ = validate_sql(retry_sql)
            if retry_valid:
                results = execute_sql(db_path, retry_sql)
                if results["success"]:
                    sql = retry_sql
                    llm_response = retry_response
    
    if not results["success"]:
        return {
            "question": question,
            "sql": sql,
            "explanation": f"SQL execution error: {results['error']}",
            "results": None,
            "intent": _detect_intent(question),
            "success": False,
            "error": f"SQL execution failed: {results['error']}",
            "model_used": llm_response.model,
            "provider_used": llm_response.provider,
            "retried": True,
        }
    
    # Extract explanation
    explanation = extract_explanation(llm_response.content) or f"Query returned {results['row_count']} rows."
    
    return {
        "question": question,
        "sql": sql,
        "explanation": explanation,
        "results": {
            "columns": results["columns"],
            "rows": results["rows"],
            "row_count": results["row_count"],
        },
        "intent": _detect_intent(question),
        "success": True,
        "error": None,
        "model_used": llm_response.model,
        "provider_used": llm_response.provider,
        "retried": results.get("retried", False),
    }
