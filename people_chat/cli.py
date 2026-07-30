#!/usr/bin/env python3
"""
People Chat — CLI Interface
Ask HR data questions in plain English.

Usage:
    people-chat init <csv>             Ingest CSV and setup
    people-chat ask <question>          Ask one question
    people-chat chat                    Interactive Q&A session
    people-chat stats [--db PATH]       Data overview
    people-chat status                  Configuration check
    people-chat demo                    One-command demo
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# ─── Paths ───────────────────────────────────────────────

DEFAULT_DB_DIR = Path.home() / ".people-chat"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "hr.db"
DEFAULT_GLOSSARY_PATH = DEFAULT_DB_DIR / "glossary.yaml"


def _ensure_db_dir():
    DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_db_path(db_path: Optional[str] = None) -> str:
    if db_path:
        return str(Path(db_path).resolve())
    _ensure_db_dir()
    return str(DEFAULT_DB_PATH.resolve())


def _resolve_glossary_path(db_path: str) -> str:
    """Derive glossary path from db path."""
    db = Path(db_path)
    return str(db.parent / f"{db.stem}_glossary.yaml")


def _load_context(db_arg: Optional[str] = None) -> tuple[str, Optional[str]]:
    """Resolve db path and glossary path, exiting if the DB doesn't exist."""
    db_path = _resolve_db_path(db_arg)
    if not os.path.exists(db_path):
        print(f"❌ No database found at {db_path}")
        print(f"   Run 'people-chat init <csv>' first")
        sys.exit(1)
    glossary_path = _resolve_glossary_path(db_path)
    if not os.path.exists(glossary_path):
        glossary_path = None
    return db_path, glossary_path


# ─── Command: init ───────────────────────────────────────

def cmd_init(args):
    """Ingest a CSV file into SQLite and generate glossary."""
    from .ingestion import ingest
    from .glossary import generate
    
    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)
    
    db_path = _resolve_db_path(args.db)
    table_name = args.table or Path(csv_path).stem.replace(" ", "_").replace("-", "_").lower()
    
    print(f"📥 Ingesting {csv_path} → {db_path}")
    
    try:
        result = ingest(csv_path, db_path, table_name=table_name)
        print(f"   ✅ {result['rows']} rows into table '{result['table_name']}'")
        print(f"   📋 {len(result['columns'])} columns detected")
    except Exception as e:
        print(f"   ❌ Ingestion failed: {e}")
        sys.exit(1)
    
    # Generate glossary
    glossary_path = _resolve_glossary_path(db_path)
    print(f"📝 Generating glossary → {glossary_path}")
    
    try:
        yaml_out = generate(db_path, table_name, str(glossary_path))
        line_count = len(yaml_out.strip().split('\n'))
        print(f"   ✅ {line_count} lines written")
        print(f"\n   Edit the glossary to add HR context:")
        print(f"   $ nano {glossary_path}")
    except Exception as e:
        print(f"   ⚠️  Glossary generation failed: {e}")
        print(f"   (You can generate it later with: glossary.py)")
    
    print(f"\n💾 Database: {db_path}")
    print(f"📖 Glossary:  {glossary_path}")
    print(f"\nNow try: people-chat ask \"How many employees do we have?\"")


# ─── Command: ask ────────────────────────────────────────

def cmd_ask(args):
    """Ask one question and get an answer."""
    from .query_engine import ask
    from .formatter import format_result, format_without_rich
    
    db_path, glossary_path = _load_context(args.db)
    question = args.question
    
    try:
        result = ask(question, db_path, glossary_path=glossary_path)
        formatted = format_result(result, show_sql=args.show_sql, force_chart=args.chart)
        
        # Clean output for terminal
        output = format_without_rich(formatted['text'])
        print(output)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


# ─── Command: chat ───────────────────────────────────────

def cmd_chat(args):
    """Interactive chat session."""
    from .query_engine import ask
    from .formatter import format_result, format_without_rich
    
    db_path, glossary_path = _load_context(args.db)
    print(f"\n  🧑‍💼 People Chat — ask anything about your people data")
    print(f"  Type 'exit' or 'quit' to leave, '/sql' to show SQL")
    print(f"  {'='*50}\n")
    
    show_sql = False
    history = []
    
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if not question:
            continue
        
        if question.lower() in ('exit', 'quit', '/exit', '/quit'):
            break
        
        if question.lower() == '/sql':
            show_sql = not show_sql
            print(f"  SQL display: {'ON' if show_sql else 'OFF'}")
            continue
        
        if question.lower() == '/help':
            print("  Commands:")
            print("    /sql     Toggle SQL display")
            print("    /help    Show this help")
            print("    exit     Leave chat")
            continue
        
        try:
            result = ask(question, db_path, glossary_path=glossary_path)
            formatted = format_result(result, show_sql=show_sql)
            
            output = format_without_rich(formatted['text'])
            print(output)
            print()
            
            history.append({"question": question, "result": result})
        except Exception as e:
            print(f"  ❌ {e}\n")


# ─── Command: stats ──────────────────────────────────────

def cmd_stats(args):
    """Show data overview of the database."""
    from .schema import introspect, get_tables
    
    db_path = _resolve_db_path(args.db)
    if not os.path.exists(db_path):
        print(f"❌ No database found at {db_path}")
        sys.exit(1)
    
    try:
        info = introspect(db_path)
    except Exception as e:
        print(f"❌ Database introspection failed: {e}")
        sys.exit(1)
    
    print(f"\n  📊 People Chat — Data Overview")
    print(f"  Database: {db_path}")
    print(f"  {'='*50}")
    
    total_rows = 0
    for table_name, table_info in info['tables'].items():
        rows = table_info['row_count']
        cols = len(table_info['columns'])
        total_rows += rows
        
        print(f"\n  📋 {table_name} ({rows} rows, {cols} columns)")
        
        # Show column summary
        col_list = [c['name'] for c in table_info['columns']]
        type_list = [c['type'] for c in table_info['columns']]
        
        # Show first 5 columns as preview
        preview = col_list[:5]
        if len(col_list) > 5:
            preview.append(f"... +{len(col_list) - 5} more")
        print(f"     {'  '.join(preview)}")
        
        # Show type distribution
        type_counts = {}
        for t in type_list:
            type_counts[t] = type_counts.get(t, 0) + 1
        type_summary = '  '.join(f"{k}: {v}" for k, v in type_counts.items())
        print(f"     Types: {type_summary}")
    
    print(f"\n  📈 Total: {total_rows} rows across {len(info['tables'])} tables\n")


# ─── Command: status ─────────────────────────────────────

def cmd_status(args):
    """Show current configuration."""
    from .config import ProviderConfig, apply_defaults
    
    cfg = ProviderConfig()
    cfg = apply_defaults(cfg)
    missing = cfg.validate()
    
    print(f"\n  ⚙️  People Chat — Status")
    print(f"  {'='*50}")
    
    # Project path
    project_dir = Path(__file__).parent.parent
    print(f"\n  📁 Project: {project_dir}")
    
    # Database
    db_path = _resolve_db_path(args.db)
    db_exists = os.path.exists(db_path)
    if db_exists:
        db_size = os.path.getsize(db_path) / 1024
        print(f"  💾 Database: {db_path} ({db_size:.0f} KB) ✅")
    else:
        print(f"  💾 Database: {db_path} ❌ Not found")
        print(f"     Run 'people-chat init <csv>' to create it")
    
    # Glossary
    glossary_path = _resolve_glossary_path(db_path)
    glossary_exists = os.path.exists(glossary_path)
    print(f"  📖 Glossary: {'✅ Found' if glossary_exists else '❌ Not found'}")
    
    # LLM Provider
    print(f"\n  🔌 LLM Provider: {cfg.provider}")
    print(f"     Model: {cfg.model}")
    print(f"     API Key: {'✅ Set' if cfg.api_key else '❌ Missing'}")
    print(f"     Base URL: {cfg.base_url}")
    
    if missing:
        print(f"\n  ⚠️  Configuration issues:")
        for m in missing:
            print(f"     - {m}")
    
    print()


# ─── Command: validate ──────────────────────────────────

def cmd_validate(args):
    """Validate glossary against database schema."""
    from .glossary import validate as validate_glossary, format_validation_results
    
    db_path = _resolve_db_path(args.db)
    if not os.path.exists(db_path):
        print(f"❌ No database found at {db_path}")
        print(f"   Run 'people-chat init <csv>' first")
        sys.exit(1)
    
    glossary_path = args.glossary or _resolve_glossary_path(db_path)
    if not os.path.exists(glossary_path):
        print(f"❌ Glossary not found at {glossary_path}")
        print(f"   Run 'people-chat init <csv>' to generate one, or specify --glossary")
        sys.exit(1)
    
    print(f"  🔍 Validating glossary against database schema...")
    print(f"     Database: {db_path}")
    print(f"     Glossary: {glossary_path}\n")
    
    try:
        issues = validate_glossary(db_path, glossary_path)
        result = format_validation_results(issues)
        print(f"  {result}")
    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        sys.exit(1)


# ─── Command: demo ───────────────────────────────────────

def cmd_demo(args):
    """One-command demo: build DB from sample, start chat."""
    from .ingestion import ingest
    from .glossary import generate as gen_glossary
    from .schema import introspect
    from .query_engine import execute_sql

    sample_dir = Path(__file__).parent / "data" / "sample"
    employees_csv = sample_dir / "employees.csv"

    if not employees_csv.exists():
        print(f"❌ Sample data not found at {employees_csv}")
        print(f"   Regenerate with: python3 generate_demo_data.py")
        sys.exit(1)

    db_path = _resolve_db_path("demo_hr.db")

    # Welcome screen
    print()
    print("  🧑‍💼 People Chat — Demo Mode")
    print("  ═══════════════════════════════════════════")
    print()
    print("  Setting up The Guild...")

    # Load data
    try:
        result = ingest(str(employees_csv), db_path, table_name="employees")
        print(f"  ✅ {result['rows']} employees loaded")
        print(f"  📊 {len(result['columns'])} data fields detected")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    # Generate glossary — this is critical for the LLM to understand the data
    demo_glossary = _resolve_glossary_path(db_path)
    print(f"  📖 Analyzing data structure...")
    try:
        gen_glossary(db_path, "employees", str(demo_glossary))
        print(f"  ✅ HR context glossary created with field definitions + HR metrics")
    except Exception as e:
        print(f"  ⚠️  Glossary generation skipped: {e}")
        demo_glossary = None

    # Data summary — use existing execution helper instead of raw sqlite3
    def _summary_count(sql: str) -> str:
        result = execute_sql(db_path, sql)
        if result["success"] and result["rows"]:
            val = result["rows"][0]["cnt"]
            return str(val) if val is not None else "?"
        return "?"

    active = _summary_count('SELECT COUNT(*) AS cnt FROM employees WHERE "Employment Status" = \'Active\'')
    total = _summary_count('SELECT COUNT(*) AS cnt FROM employees')
    dept_count = _summary_count('SELECT COUNT(DISTINCT "Department") AS cnt FROM employees')
    div_count = _summary_count('SELECT COUNT(DISTINCT "Division") AS cnt FROM employees')

    print(f"\n  📊 The Guild — Sample Data Overview")
    print(f"     {active} active employees ({total} total)")
    print(f"     {dept_count} departments across {div_count} divisions")
    print()

    # Guided or interactive mode
    if args.guided:
        from .demo_guide import run_guided_tour
        run_guided_tour(db_path, str(demo_glossary) if demo_glossary else None)

    # Show suggested questions
    print("  💡 Try asking:")
    print(f"    • \"How many active employees do we have?\"")
    print(f"    • \"What's the average salary by department?\"")
    print(f"    • \"Show me the salary distribution by Radford level\"")
    print(f"    • \"Who are the top 10 highest paid employees?\"")
    print(f"    • \"What departments have the most turnover?\"")
    print(f"    • \"Show me the gender distribution by division\"")
    if not args.guided:
        print(f"\n  🎮 Or try 'people-chat demo --guided' for a guided tour!")
    print()

    # Launch chat
    args.db = db_path
    cmd_chat(args)


# ─── Main Entry Point ────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🧑‍💼 People Chat — AI-powered HR data analyst",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  people-chat init ./employees.csv                         Load data
  people-chat ask "How many employees?"                     Ask one question
  people-chat ask "Show turnover by dept" --show-sql        Ask with SQL visible
  people-chat ask "Show salaries" --chart                   Force chart output
  people-chat chat                                           Interactive session
  people-chat stats                                          Data overview
  people-chat status                                         Configuration check
  people-chat validate                                       Validate glossary
  people-chat demo                                           One-command demo
        """
    )
    
    parser.add_argument('--db', help='Path to SQLite database (default: ~/.people-chat/hr.db)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init
    init_parser = subparsers.add_parser('init', help='Ingest CSV into SQLite')
    init_parser.add_argument('csv', help='Path to CSV file')
    init_parser.add_argument('--table', help='Table name (default: CSV filename)')
    
    # ask
    ask_parser = subparsers.add_parser('ask', help='Ask one question')
    ask_parser.add_argument('question', help='Your question in plain English')
    ask_parser.add_argument('--show-sql', action='store_true', help='Show the generated SQL')
    ask_parser.add_argument('--chart', action='store_true', help='Force chart output')
    
    # chat
    subparsers.add_parser('chat', help='Interactive chat session')
    
    # stats
    stats_parser = subparsers.add_parser('stats', help='Show data overview')
    
    # status
    status_parser = subparsers.add_parser('status', help='Show configuration')
    
    # demo
    demo_parser = subparsers.add_parser('demo', help='One-command demo with sample data')
    demo_parser.add_argument('--guided', action='store_true', help='Guided tour showing different capabilities')
    
    # validate
    validate_parser = subparsers.add_parser('validate', help='Validate glossary against database schema')
    validate_parser.add_argument('--glossary', help='Path to glossary YAML file (default: auto-detected from database)')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Route to command handler
    commands = {
        'init': cmd_init,
        'ask': cmd_ask,
        'chat': cmd_chat,
        'stats': cmd_stats,
        'status': cmd_status,
        'demo': cmd_demo,
        'validate': cmd_validate,
    }
    
    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
