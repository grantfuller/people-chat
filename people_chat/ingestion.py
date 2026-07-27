"""
CSV → SQLite ingestion engine with automatic type detection.
Reads CSV files, infers column types, creates SQLite tables, inserts data.
"""

import csv
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def detect_sql_type(series: pd.Series) -> str:
    """
    Infer the best SQLite column type from a pandas Series.
    
    Rules:
    - If column name contains 'date' (case-insensitive), try date parsing
    - If all values are integers → INTEGER
    - If all values are floats (or mixed int/float) → REAL
    - If values look like dates → TEXT (ISO format)
    - Everything else → TEXT
    """
    col_name = str(series.name).lower()
    
    # Drop nulls for type detection
    non_null = series.dropna()
    if len(non_null) == 0:
        return "TEXT"
    
    # Check if it looks like a date column
    if any(word in col_name for word in ['date', 'termination', 'hire', 'birth', 'compensation']):
        return "DATE"
    
    # Try numeric detection
    try:
        numeric = pd.to_numeric(non_null, errors='coerce')
        valid_numeric = numeric.dropna()
        if len(valid_numeric) == len(non_null):
            if all(valid_numeric == valid_numeric.astype(int)):
                return "INTEGER"
            return "REAL"
    except (ValueError, TypeError):
        pass
    
    return "TEXT"


def build_create_table_sql(table_name: str, columns: Dict[str, str]) -> str:
    """Generate CREATE TABLE SQL from column name → type mapping."""
    col_defs = []
    for col_name, col_type in columns.items():
        safe_name = f'"{col_name}"'
        col_defs.append(f"    {safe_name} {col_type}")
    
    sql = f"""CREATE TABLE IF NOT EXISTS "{table_name}" (
{',\n'.join(col_defs)}
);"""
    return sql


def read_csv_to_dataframe(csv_path: str) -> pd.DataFrame:
    """Read CSV file and clean column names (strip whitespace)."""
    df = pd.read_csv(csv_path, dtype_backend='numpy_nullable')
    
    # Clean column names
    df.columns = [col.strip() for col in df.columns]
    
    # Convert empty strings to NaN
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    
    return df


def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Infer SQLite column types from a DataFrame."""
    schema = {}
    for col in df.columns:
        schema[col] = detect_sql_type(df[col])
    return schema


def create_table(cursor: sqlite3.Cursor, table_name: str, schema: Dict[str, str]):
    """Create a SQLite table if it doesn't exist."""
    sql = build_create_table_sql(table_name, schema)
    cursor.execute(sql)


def insert_data(
    cursor: sqlite3.Cursor,
    table_name: str,
    df: pd.DataFrame,
    schema: Dict[str, str],
    batch_size: int = 100
) -> int:
    """Insert DataFrame rows into SQLite table. Returns row count."""
    columns = list(df.columns)
    placeholders = ", ".join(["?" for _ in columns])
    col_names = ", ".join([f'"{c}"' for c in columns])
    
    insert_sql = f'INSERT OR REPLACE INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
    
    rows_inserted = 0
    records = df.to_dict('records')
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        values_batch = []
        for record in batch:
            row_values = []
            for col in columns:
                val = record[col]
                # Convert NaN/NaT to None for SQLite
                if pd.isna(val):
                    row_values.append(None)
                elif schema.get(col) == "DATE" and val is not None:
                    # Ensure date is string
                    row_values.append(str(val)[:10] if hasattr(val, 'strftime') else str(val))
                elif schema.get(col) == "INTEGER" and val is not None:
                    row_values.append(int(val))
                elif schema.get(col) == "REAL" and val is not None:
                    row_values.append(float(val))
                else:
                    row_values.append(val)
            values_batch.append(tuple(row_values))
        
        cursor.executemany(insert_sql, values_batch)
        rows_inserted += len(batch)
    
    return rows_inserted


def ingest(
    csv_path: str,
    db_path: str,
    table_name: Optional[str] = None,
    if_exists: str = "replace"
) -> Dict[str, Any]:
    """
    Full CSV → SQLite ingestion pipeline.
    
    Args:
        csv_path: Path to CSV file
        db_path: Path to SQLite database file
        table_name: Table name (defaults to CSV filename without extension)
        if_exists: What to do if table exists ("replace", "fail", "append")
    
    Returns:
        Dict with: table_name, rows, columns, schema, db_path
    """
    if table_name is None:
        table_name = Path(csv_path).stem.replace(" ", "_").replace("-", "_").lower()
    
    # Read CSV
    df = read_csv_to_dataframe(csv_path)
    
    # Infer schema
    schema = infer_schema(df)
    
    # Connect and create table
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    cursor = conn.cursor()
    
    if if_exists == "replace":
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    
    create_table(cursor, table_name, schema)
    
    # Insert data
    rows = insert_data(cursor, table_name, df, schema)
    
    conn.commit()
    conn.close()
    
    return {
        "table_name": table_name,
        "rows": rows,
        "columns": list(schema.keys()),
        "schema": schema,
        "db_path": str(Path(db_path).resolve())
    }
