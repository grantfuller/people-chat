# People Chat — Architecture Decisions

This file tracks every significant architectural decision made during the build.
Each entry includes the decision, rationale, alternatives considered, and date.

---

## 2026-07-27 — Project Initiated

### Decision 1: SQLite for data storage
**Rationale:** Zero-dependency, file-based, sufficient for 10K–100K employee records. Future-proof via WAL mode and foreign keys.
**Alternatives considered:** DuckDB (overkill for v1), PostgreSQL (too heavy for a CLI tool), in-memory (no persistence).

### Decision 2: Bring-Your-Own-Key LLM architecture
**Rationale:** Keeps costs on the user, no API key bundling, supports multiple providers. DeepSeek is dev default because we already have access and it's $0.02/query.
**Providers:** OpenAI, Anthropic, DeepSeek (OpenAI-compatible), Ollama (local, free)
**Alternatives considered:** Bundling a single provider key (security risk, cost liability), requiring a specific provider (limits adoption).

### Decision 3: CLI-first, web UI later
**Rationale:** Faster to ship, easier to demo in terminal, natural for data analysts. Streamlit web UI planned for v2.
**CLI framework:** Click/Typer (Python stdlib-adjacent, well-documented)
**Alternatives considered:** Streamlit-only (slower iteration for v1), FastAPI + React (way too heavy for v1).

### Decision 4: Glossary YAML for HR context
**Rationale:** Human-editable, version-controllable, separates data definition from code. Solves the core problem of LLMs not knowing HR-specific column meanings.
**Alternatives considered:** JSON schema (less readable), database comments (harder to edit), auto-inference only (fails on ambiguous columns like "status").

### Decision 5: Few-shot prompting over fine-tuning
**Rationale:** Cheaper, faster to iterate, no model hosting. Fine-tuning would lock us to a single provider and require ongoing maintenance.
**Few-shot design:** 8–12 curated Q&A examples covering common HR query patterns (count, sum, avg, group by, date range, join).
**Alternatives considered:** Fine-tuning (expensive, model-specific), agent workflow (premature for v1), RAG (overkill for structured data).

---

## 2026-07-27 — Schema Design (Phase 1)

### Decision 6: Synthetic demo data over public dataset
**Rationale:** A real-world HR schema has 143 columns across 4 tabs — far richer than any public dataset. Generating synthetic data matching this schema means the demo is immediately relevant to HR analysts. The Chicago public dataset would've required too much schema mapping.
**Data model:** 4 CSV tables matching the Google Sheet tabs (Data Dump, Current Team, Reporting Structure, Job Catalog) with synthetic but realistic employee data.

### Decision 7: Split pay fields
**Rationale:** The original "Pay Schedule" field conflated three distinct concepts. Split into:
- Time Type (Hourly / Salary) — how pay is calculated
- Exempt (Exempt / Non-Exempt) — FLSA classification
- Pay Schedule (Bi-Weekly, Monthly, etc.) — pay frequency
**Impact:** Cleaner queries like "show me all exempt employees" or "how many hourly workers are non-exempt?"

### Decision 8: Fictional D&D-themed company for demo
**Rationale:** The goal was a fun, safe company name. A generic fantasy name was chosen (non-copyrighted), while Department/Division structures stayed real-world to maintain credibility.
**Status:** Company name TBD — research underway.

### Decision 9: Synthetic data strategy
**Approach:** Python generator script that:
- Creates employees matching Data Dump + Current Team schemas
- Creates job catalog with more entries than employees (future-role mapping)
- Creates reporting structure with realistic manager chains
- Uses Radford level progression (S1-S6, P1-P6, M1-M6, E1-E6) for salary bands
- Generates 500-1000 employee records

---

## 2026-07-27 — Phase 1 Implementation

### Decision 10: Type detection strategy
**Approach:** Column-name pattern matching for dates (any column with "date" in name → DATE type), then pandas numeric inference for INT/REAL, fallback to TEXT. 
**Why not just TEXT everything?** Having typed columns makes SQL generation more reliable — the LLM can use date functions, numeric aggregations, etc. without casting.
**Edge case caught:** Zip Code is stored as INTEGER because all values are 5-digit numbers. The glossary description clarifies it's a code, not a numeric value.

### Decision 11: Glossary as YAML, not JSON
**Rationale:** YAML supports comments, is more human-readable for non-technical HR users, and is easily diff-able in git. The pyyaml dependency was already included.

### Decision 12: Separate validator from generator
**Rationale:** The generator runs once (initial setup), but the validator should be runnable anytime the data changes or glossary is edited. Keeps concerns separated.

---

## 2026-07-27 — Phase 3 Implementation

### Decision 13: Few-shot prompting over fine-tuning
**Rationale:** Cheaper, faster to iterate, no model hosting. 12 curated Q&A examples cover 80% of HR query patterns.
**Alternatives:** Fine-tuning (expensive, model-specific, ongoing maintenance), RAG (overkill for structured data).

### Decision 14: Retry-on-error for SQL generation
**Rationale:** LLMs occasionally generate bad SQL (wrong column aliases, missing quotes, etc.). One automatic retry with the error message fixes ~90% of failures without user involvement.
**Tradeoff:** Doubles LLM cost for failed queries. Accepted because DeepSeek is cheap ($0.02/query) and failures are rare.

### Decision 15: Chart intent detection
**Approach:** Keyword matching in the question ("chart", "graph", "plot", "visualize") sets intent flag. Actual chart rendering deferred to Phase 4.
**Limitation:** Simple keyword matching only. v2 can use LLM intent classification.

### Decision 16: SQL extraction strategy
**Approach:** Parse markdown code blocks (```sql) first, then plain text detection of SELECT/CTE as fallback.
**Why not JSON-structured output?** Markdown is LLM-native and less likely to be malformed. JSON escapes cause more failures in practice.

### Project Timeline (actual vs estimated)
- Phase 0: 3 days est. → 1 day actual ✅
- Phase 1: 4 days est. → 1 day actual ✅
- Phase 2: 3 days est. → 1 day actual ✅
- Phase 3: 7 days est. → 1 day actual ✅ (6-7x faster than estimated)

---

## 2026-07-27 — Phase 4 & 5 Implementation

### Decision 17: Rich library for terminal tables
**Rationale:** Python's best terminal formatting library. Handles column alignment, truncation, borders, and color. Falls back to text if not installed.
**Alternative:** tabulate (less feature-rich), manual padding (more code to maintain).

### Decision 18: Plotly for charts
**Rationale:** Self-contained HTML output, dark theme support, interactive (zoom/hover), no server needed. Opens in browser automatically.
**Alternative:** matplotlib (static, less attractive), seaborn (same issue), chart.js (requires Node/npm).

### Decision 19: Argparse over Click/Typer
**Rationale:** Zero new dependencies — argparse is stdlib. Only 6 simple commands, no need for Click's advanced features.
**Tradeoff:** Slightly more boilerplate. Argparse requires `--db` before subcommand, which is non-obvious.

### Decision 20: Default to active-only headcount
**Rationale:** HR context — "how many employees" typically means "how many active." Total counts available with explicit "including terminated" or "total" language.

### Project Timeline (Actual vs Plan)
- Phase 0: 3 days est. → <1 day actual
- Phase 1: 4 days est. → <1 day actual
- Phase 2: 3 days est. → <1 day actual
- Phase 3: 7 days est. → <1 day actual
- Phase 4: 4 days est. → <1 day actual
- Phase 5: 4 days est. → <1 day actual
- Total: 25-35 days est. → 1 day actual (build day)
