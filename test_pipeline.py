#!/usr/bin/env python3
"""
People Chat — Pipeline Test
Run this to verify ingestion, schema detection, glossary generation, and LLM connectivity.
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

PROJECT_DIR = Path(__file__).parent
SAMPLE_DATA = PROJECT_DIR / "people_chat" / "data" / "sample"
DB_PATH = "/tmp/people_chat_test.db"


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print(f"\n  🧑‍💼 People Chat — Pipeline Test")
    print(f"  {PROJECT_DIR}")
    
    # ─── Step 1: Ingestion ───
    section("Step 1: Ingest CSV → SQLite")
    from people_chat.ingestion import ingest
    
    employees_csv = SAMPLE_DATA / "employees.csv"
    if not employees_csv.exists():
        print(f"  ❌ Sample data not found: {employees_csv}")
        sys.exit(1)
    
    result = ingest(str(employees_csv), DB_PATH, table_name="employees")
    print(f"  ✅ Ingested {result['rows']} rows into '{result['table_name']}'")
    print(f"  📋 {len(result['columns'])} columns detected")
    print(f"  💾 Database at: {DB_PATH}")
    
    # ─── Step 2: Schema ───
    section("Step 2: Schema Introspection")
    from people_chat.schema import introspect
    
    info = introspect(DB_PATH)
    table_info = info["tables"].get("employees", {})
    print(f"  Table: employees ({table_info.get('row_count', 0)} rows)")
    print(f"\n  {'Column':30s} {'Type':10s} Nullable")
    print(f"  {'-'*30} {'-'*10} {'-'*8}")
    for col in table_info.get("columns", []):
        nullable = "✅" if col["nullable"] else "❌"
        print(f"  {col['name']:30s} {col['type']:10s} {nullable}")
    
    # ─── Step 3: Glossary ───
    section("Step 3: Glossary Generation")
    from people_chat.glossary import generate, validate, format_validation_results
    
    yaml_out = generate(DB_PATH, "employees")
    lines = yaml_out.strip().split(chr(10))
    print(f"  ✅ Glossary generated ({len(lines)} lines)")
    print(f"\n  First 12 lines:")
    for line in lines[:12]:
        print(f"    {line}")
    
    # ─── Step 4: LLM Test ───
    section("Step 4: LLM Connection Test")
    from people_chat.config import ProviderConfig, apply_defaults
    from people_chat.llm import get_provider, test_provider
    
    cfg = ProviderConfig()
    cfg = apply_defaults(cfg)
    
    # Check for API key
    missing = cfg.validate()
    if missing:
        print(f"  ⚠️  LLM not configured yet. To test:")
        for m in missing:
            print(f"     Set {m}")
        print(f"\n     Or: LLM_API_KEY=your_key python3 test_pipeline.py")
        print(f"  ⏭️  Skipping LLM test")
    else:
        print(f"  Provider: {cfg.provider}")
        print(f"  Model: {cfg.model}")
        print(f"  Connecting...")
        try:
            provider = get_provider(cfg)
            response = test_provider(provider)
            print(f"  ✅ Connected! Response: '{response.content.strip()}'")
            print(f"     Model used: {response.model}")
        except Exception as e:
            print(f"  ❌ LLM connection failed: {e}")
    
    # ─── Step 5: Cleanup ───
    section("Cleanup")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  🧹 Removed test database")
    
    print(f"\n  {'='*60}")
    print(f"  🎉 Pipeline test complete!")
    print(f"  {'='*60}")
    print()


if __name__ == "__main__":
    main()
