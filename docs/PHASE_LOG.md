# People Chat — Phase Log

---

## Phase 0: Foundation & Environment
**Status:** ✅ Complete | **Date:** 2026-07-27
Created project skeleton, venv, pyproject.toml, README, docs.

## Phase 1: Data Ingestion Engine
**Status:** ✅ Complete | **Date:** 2026-07-27
- ingestion.py — CSV → SQLite with auto-type detection
- schema.py — DB introspection (types, nulls, sample data)
- glossary.py — YAML generation + validation
- Synthetic data: 750 employees, 117 jobs, 749 org hierarchy

## Phase 2: LLM Provider Layer
**Status:** ✅ Complete | **Date:** 2026-07-27
- config.py — Env var loader with provider defaults (OpenAI, Anthropic, DeepSeek, Ollama)
- llm.py — Abstract provider + OpenAICompatible, Anthropic, Ollama implementations
- Tested with DeepSeek (deepseek-v4-flash) — OK response verified

## Phase 3: Query Engine (The Brain)
**Status:** ✅ Complete | **Date:** 2026-07-27
### Wave 3a — Prompt Infrastructure
- prompts/system.md — System prompt with safety rules + HR query patterns
- prompts/few_shot.sql — 12 example Q&A pairs (headcount, salary, tenure, turnover, compa-ratio)
- query_engine.py — build_prompt(), extract_sql(), validate_sql(), execute_sql(), ask()
- **Tested:** 3 questions (headcount, dept salary, top earners) — all passed

### Wave 3b — Error Recovery & Safeguards
- _check_needs_info() — Detects "I need more information" patterns from LLM
- _build_retry_prompt() — Sends SQL error back to LLM for one fix attempt
- validate_sql() — Now catches multiple/semicolons, INSSERT/UPDATE/DELETE/DROP
- **Tested:** 5 questions including edge cases + a chart request — all passed, retry recovered from one bad SQL

## Phase 4: Output Formatting
**Status:** ⏳ Not Started

## Phase 5: CLI Interface
**Status:** ⏳ Not Started

## Phase 6: Demo Mode
**Status:** ⏳ Not Started

## Phase 7: Documentation & Polish
**Status:** ⏳ Not Started

## Phase 8: Launch
**Status:** ⏳ Not Started
