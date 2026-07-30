"""
SQLite schema introspection. Reads an existing database and returns
structured info about tables, columns, types, and constraints.
"""

import sqlite3
from pathlib import Path
from typing import Any


def get_tables(db_path: str) -> list[str]:
    """Get list of all table names in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_columns(db_path: str, table_name: str) -> list[dict[str, Any]]:
    """
    Get column metadata for a table.
    
    Returns list of dicts with: name, type, nullable, default, pk
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2],
                "nullable": not bool(row[3]),
                "default": row[4],
                "pk": bool(row[5])
            })
    except sqlite3.OperationalError as e:
        conn.close()
        raise ValueError(f"Table '{table_name}' not found: {e}")
    
    conn.close()
    return columns


def get_row_count(db_path: str, table_name: str) -> int:
    """Get row count for a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    conn.close()
    return count


def get_sample_rows(db_path: str, table_name: str, limit: int = 5) -> list[dict[str, Any]]:
    """Get sample rows from a table as list of dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT ?', (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows


def get_null_counts(db_path: str, table_name: str) -> dict[str, int]:
    """Get count of NULLs per column."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get columns first
    columns = get_columns(db_path, table_name)
    null_counts = {}
    
    for col in columns:
        col_name = col["name"]
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NULL')
        null_counts[col_name] = cursor.fetchone()[0]
    
    conn.close()
    return null_counts


def introspect(db_path: str, table_name: str | None = None) -> dict[str, Any]:
    """
    Full introspection of a database.
    
    Returns structured metadata about all tables (or a specific table).
    Includes: column info, row counts, sample data, null analysis.
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    tables = get_tables(db_path)
    
    if table_name:
        tables = [t for t in tables if t == table_name]
        if not tables:
            raise ValueError(f"Table '{table_name}' not found in database")
    
    result = {
        "db_path": str(Path(db_path).resolve()),
        "tables": {}
    }
    
    for tbl in tables:
        columns = get_columns(db_path, tbl)
        row_count = get_row_count(db_path, tbl)
        sample = get_sample_rows(db_path, tbl)
        null_counts = get_null_counts(db_path, tbl)
        
        result["tables"][tbl] = {
            "columns": columns,
            "row_count": row_count,
            "sample_rows": sample,
            "null_counts": null_counts
        }
    
    return result
