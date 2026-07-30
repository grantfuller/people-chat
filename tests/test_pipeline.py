"""Tests for People Chat core functions."""

import pytest
import os
import sys
from pathlib import Path
import tempfile
import csv
import sqlite3


# ─── Helper: create a mini CSV for testing ───

def _create_test_csv(tmp_path, rows=5):
    """Create a small employee CSV for pipeline testing."""
    path = tmp_path / "test_employees.csv"
    fieldnames = [
        "Employee #", "First Name", "Last Name", "Department",
        "Division", "Pay rate", "Employment Status", "Hire Date"
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(rows):
            status = "Active" if i < 4 else "Terminated"
            writer.writerow({
                "Employee #": f"EMP{i+1:05d}",
                "First Name": f"First{i}",
                "Last Name": f"Last{i}",
                "Department": "Engineering" if i % 2 == 0 else "Sales",
                "Division": "Tech" if i % 2 == 0 else "Revenue",
                "Pay rate": 50000 + i * 10000,
                "Employment Status": status,
                "Hire Date": f"202{i}-01-0{i+1}",
            })
    return str(path)


def _create_test_db(tmp_path, rows=5):
    """Create a test SQLite DB directly with an employees table."""
    db_path = str(tmp_path / "test_hr.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE employees (
            "Employee #" TEXT,
            "First Name" TEXT,
            "Last Name" TEXT,
            "Department" TEXT,
            "Division" TEXT,
            "Pay rate" INTEGER,
            "Employment Status" TEXT,
            "Hire Date" TEXT
        )
    """)
    for i in range(rows):
        conn.execute(
            'INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (f"EMP{i+1:05d}", f"First{i}", f"Last{i}",
             "Engineering" if i % 2 == 0 else "Sales",
             "Tech" if i % 2 == 0 else "Revenue",
             50000 + i * 10000,
             "Active" if i < 4 else "Terminated",
             f"202{i}-01-0{i+1}")
        )
    conn.commit()
    conn.close()
    return db_path


# ─── Test: Ingestion ───

class TestIngestion:
    def test_ingest_creates_table(self, tmp_path):
        """Ingesting a CSV should create a SQLite table."""
        from people_chat.ingestion import ingest
        csv_path = _create_test_csv(tmp_path, rows=5)
        db_path = str(tmp_path / "test_hr.db")
        result = ingest(csv_path, db_path, table_name="employees")
        assert result["rows"] == 5
        assert result["table_name"] == "employees"
        assert len(result["columns"]) == 8
        assert os.path.exists(db_path)

    def test_ingest_with_custom_table_name(self, tmp_path):
        """Should respect custom table name."""
        from people_chat.ingestion import ingest
        csv_path = _create_test_csv(tmp_path, rows=3)
        db_path = str(tmp_path / "custom.db")
        result = ingest(csv_path, db_path, table_name="my_team")
        assert result["table_name"] == "my_team"

    def test_ingest_refuses_missing_file(self, tmp_path):
        """Should raise FileNotFoundError for missing CSV."""
        from people_chat.ingestion import ingest
        db_path = str(tmp_path / "nope.db")
        with pytest.raises(FileNotFoundError):
            ingest("/nonexistent/file.csv", db_path)

    def test_ingest_with_empty_csv(self, tmp_path):
        """Empty CSV should create table with 0 rows."""
        from people_chat.ingestion import ingest
        csv_path = str(tmp_path / "empty.csv")
        with open(csv_path, "w") as f:
            f.write("Name,Department,Pay rate\n")
        db_path = str(tmp_path / "empty.db")
        result = ingest(csv_path, db_path, table_name="empty")
        assert result["rows"] == 0
        assert len(result["columns"]) == 3


# ─── Test: Schema ───

class TestSchema:
    def test_introspect_returns_tables(self, tmp_path):
        from people_chat.schema import introspect
        db_path = _create_test_db(tmp_path, rows=5)
        info = introspect(db_path)
        assert "tables" in info
        assert "employees" in info["tables"]

    def test_introspect_column_details(self, tmp_path):
        from people_chat.schema import introspect
        db_path = _create_test_db(tmp_path, rows=5)
        info = introspect(db_path)
        table_info = info["tables"]["employees"]
        assert table_info["row_count"] == 5
        columns = {c["name"]: c for c in table_info["columns"]}
        assert "Employee #" in columns
        assert "Pay rate" in columns
        assert columns["Pay rate"]["type"] == "INTEGER"

    def test_get_tables(self, tmp_path):
        from people_chat.schema import get_tables
        db_path = _create_test_db(tmp_path, rows=5)
        tables = get_tables(db_path)
        assert "employees" in tables

    def test_get_columns(self, tmp_path):
        from people_chat.schema import get_columns
        db_path = _create_test_db(tmp_path, rows=5)
        columns = get_columns(db_path, "employees")
        names = [c["name"] for c in columns]
        assert "Employee #" in names
        assert "Department" in names


# ─── Test: Glossary ───

class TestGlossary:
    def test_generate_creates_yaml(self, tmp_path):
        from people_chat.glossary import generate
        db_path = _create_test_db(tmp_path, rows=5)
        yaml_out = generate(db_path, "employees")
        assert yaml_out is not None
        assert "columns" in yaml_out or "Employee #" in yaml_out
        assert "metrics" in yaml_out or "headcount" in yaml_out

    def test_generate_writes_file(self, tmp_path):
        from people_chat.glossary import generate
        db_path = _create_test_db(tmp_path, rows=5)
        output_path = str(tmp_path / "glossary.yaml")
        yaml_out = generate(db_path, "employees", output_path)
        assert os.path.exists(output_path)
        assert len(yaml_out) > 0

    def test_validate_missing_glossary(self, tmp_path):
        from people_chat.glossary import validate
        db_path = _create_test_db(tmp_path, rows=5)
        issues = validate(db_path, str(tmp_path / "nonexistent.yaml"))
        assert any(i["severity"] == "error" for i in issues)

    def test_validate_against_schema(self, tmp_path):
        from people_chat.glossary import generate, validate
        db_path = _create_test_db(tmp_path, rows=5)
        glossary_path = str(tmp_path / "glossary.yaml")
        generate(db_path, "employees", glossary_path)
        issues = validate(db_path, glossary_path)
        assert not any(i["severity"] == "error" for i in issues)

    def test_validate_detects_drift(self, tmp_path):
        """Add a column to the DB that the glossary doesn't know about."""
        from people_chat.glossary import generate, validate
        db_path = _create_test_db(tmp_path, rows=3)
        glossary_path = str(tmp_path / "glossary.yaml")
        generate(db_path, "employees", glossary_path)
        conn = sqlite3.connect(db_path)
        conn.execute('ALTER TABLE employees ADD COLUMN "New Field" TEXT')
        conn.commit()
        conn.close()
        issues = validate(db_path, glossary_path)
        warnings = [i for i in issues if i["severity"] == "warning"]
        assert any("New Field" in i["message"] for i in warnings)


# ─── Test: SQL Extraction ───

class TestSQL:
    def test_extract_sql_from_markdown_block(self, tmp_path):
        from people_chat.query_engine import extract_sql
        response = "Here's the query:\n```sql\nSELECT * FROM employees\n```\nThis returns everything."
        sql = extract_sql(response)
        assert sql == "SELECT * FROM employees"

    def test_extract_sql_from_code_block(self, tmp_path):
        from people_chat.query_engine import extract_sql
        response = "```\nSELECT COUNT(*) FROM employees\n```"
        sql = extract_sql(response)
        assert sql == "SELECT COUNT(*) FROM employees"

    def test_extract_sql_from_plain_text(self, tmp_path):
        from people_chat.query_engine import extract_sql
        response = "The query is:\nSELECT e.*\nFROM employees e\nWHERE status = 'Active';"
        sql = extract_sql(response)
        assert sql is not None
        assert "SELECT" in sql.upper()

    def test_extract_sql_returns_none_when_missing(self, tmp_path):
        from people_chat.query_engine import extract_sql
        response = "I cannot answer that question."
        sql = extract_sql(response)
        assert sql is None

    def test_validate_sql_allows_select(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("SELECT * FROM employees")
        assert valid is True

    def test_validate_sql_allows_with(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("WITH cte AS (SELECT * FROM employees) SELECT * FROM cte")
        assert valid is True

    def test_validate_sql_blocks_insert(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("INSERT INTO employees VALUES (1)")
        assert valid is False
        assert "forbidden" in msg.lower()

    def test_validate_sql_blocks_drop(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("DROP TABLE employees")
        assert valid is False

    def test_validate_sql_blocks_attach(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("ATTACH DATABASE 'malicious.db' AS evil")
        assert valid is False

    def test_validate_sql_blocks_replace(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("REPLACE INTO employees VALUES (1)")
        assert valid is False

    def test_validate_sql_blocks_vacuum(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("VACUUM")
        assert valid is False

    def test_validate_sql_blocks_multiple_statements(self, tmp_path):
        from people_chat.query_engine import validate_sql
        valid, msg = validate_sql("SELECT * FROM employees; SELECT * FROM departments")
        assert valid is False


# ─── Test: Type Detection ───

class TestTypeDetection:
    def test_integer_detection(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series([1, 2, 3, 4, 5])
        assert detect_sql_type(series) == "INTEGER"

    def test_float_detection(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series([1.5, 2.5, 3.0, 4.2])
        assert detect_sql_type(series) == "REAL"

    def test_text_detection(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series(["hello", "world", "test"])
        assert detect_sql_type(series) == "TEXT"

    def test_date_column_detection(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series(["2024-01-01", "2024-06-15"])
        series.name = "hire_date"
        assert detect_sql_type(series) == "DATE"

    def test_date_column_name(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series(["Jan 1, 2024", "Jun 15, 2024"])
        series.name = "Termination Date"
        assert detect_sql_type(series) == "DATE"

    def test_integer_zip_code_not_parsed_as_date(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series([84101, 84102, 84103])
        series.name = "Zip Code"
        assert detect_sql_type(series) == "INTEGER"

    def test_empty_series_returns_text(self, tmp_path):
        from people_chat.ingestion import detect_sql_type
        import pandas as pd
        series = pd.Series([], dtype=object)
        assert detect_sql_type(series) == "TEXT"


# ─── Test: Safety ───

class TestSafety:
    def test_detect_intent_chart_keywords(self, tmp_path):
        from people_chat.query_engine import _detect_intent
        assert _detect_intent("Show me a chart of salaries") == "chart"
        assert _detect_intent("Plot the headcount by department") == "chart"
        assert _detect_intent("Graph the salary distribution") == "chart"

    def test_detect_intent_auto(self, tmp_path):
        from people_chat.query_engine import _detect_intent
        assert _detect_intent("How many active employees?") == "auto"
        assert _detect_intent("What's the average salary?") == "auto"

    def test_needs_info_detection(self, tmp_path):
        from people_chat.query_engine import _check_needs_info
        assert _check_needs_info("I need more information about your data") is True
        assert _check_needs_info("I don't have enough information to answer") is True
        assert _check_needs_info("The available data does not contain salary info") is True
        assert _check_needs_info("SELECT * FROM employees") is False
        assert _check_needs_info("Here is the query you asked for") is False

    def test_validate_sql_with_comments(self, tmp_path):
        from people_chat.query_engine import validate_sql
        sql = "-- Count active employees\nSELECT COUNT(*) FROM employees WHERE status = 'Active'"
        valid, msg = validate_sql(sql)
        assert valid is True
