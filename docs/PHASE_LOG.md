# People Chat — Phase Log

---

## Phase 0: Foundation & Environment
**Status:** ✅ Complete | **Date:** 2026-07-27
Project skeleton, venv, pyproject.toml, README skeleton, docs.

## Phase 1: Data Ingestion Engine
**Status:** ✅ Complete | **Date:** 2026-07-27
- ingestion.py — CSV → SQLite with auto-type detection (INT, REAL, DATE, TEXT)
- schema.py — DB introspection (columns, types, nulls, sample data)
- glossary.py — YAML generation + validation against schema

## Phase 2: LLM Provider Layer
**Status:** ✅ Complete | **Date:** 2026-07-27
- config.py — Env var loader (.env) + provider defaults
- llm.py — Abstract provider + OpenAICompatible (DeepSeek/Groq/OpenAI), Anthropic, Ollama
- Tested with DeepSeek v4 Flash

## Phase 3: Query Engine (The Brain)
**Status:** ✅ Complete | **Date:** 2026-07-27
- prompts/system.md — System prompt with safety rules + HR query patterns
- prompts/few_shot.sql — 14 example Q&A pairs
- query_engine.py — build_prompt → extract_sql → validate_sql → execute_sql → explain
- Error recovery: 1 retry on failed SQL with error fed back to LLM
- "Needs info" detection for unanswerable questions
- SQL injection protection (multi-statement detection)
- **Fix:** Active-only default for headcount, explicit language for total

## Phase 4: Output Formatting
**Status:** ✅ Complete | **Date:** 2026-07-27
- formatter.py — Rich terminal tables, Plotly HTML charts, auto table/chart detection
- format_result() — Unified dispatcher for all result types
- Chart types: bar, line, pie (auto-detected from data shape)

## Phase 5: CLI Interface
**Status:** ✅ Complete | **Date:** 2026-07-27
- cli.py — 6 commands using argparse (zero new deps)
- `init` — CSV → SQLite + glossary generation
- `ask` — One-shot natural language question
- `chat` — Interactive REPL with /sql toggle
- `stats` — Data overview with column/type breakdown
- `status` — Configuration check
- `demo` — One-command sample data experience
- Installed via `pip install -e .` → `people-chat` command available globally

## Phase 6: Demo Mode
**Status:** 🔄 Mostly Built (needs polish)
- `people-chat demo` command exists and works
- Auto-loads sample data, starts chat session

## Phase 7: Documentation & Polish
**Status:** ⏳ Not Started

## Phase 8: Launch
**Status:** ⏳ Not Started
