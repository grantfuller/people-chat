# People Chat 🧑‍💼

**AI-powered HR data analyst. Ask questions in English, get answers from your data.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()
[![Demo Ready](https://img.shields.io/badge/demo-ready-brightgreen.svg)]()

Turn your HR data into answers. People Chat ingests employee CSVs, builds a searchable database, and lets you ask questions in plain English. It generates SQL queries using an LLM, executes them against your data, and returns results as formatted tables or interactive charts.

```bash
# Quick demo — no setup needed
people-chat demo

# Or use your own data
people-chat init ./employees.csv
people-chat ask "How many active employees do we have?"
people-chat ask "What's the average salary by department?" --chart
people-chat chat
```

## 🚀 Quick Start

### 1. Install

```bash
# Clone or cd into the project
cd people-chat

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

### 2. Configure your LLM

```bash
mkdir -p ~/.people-chat
cat > ~/.people-chat/.env << 'EOF'
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-your-key-here
EOF
```

**Getting a key:**
- **DeepSeek (recommended):** Sign up at [platform.deepseek.com](https://platform.deepseek.com) → API Keys → Create key. ~$0.02/query.
- **OpenAI:** [platform.openai.com](https://platform.openai.com) → API keys → Create secret key. ~$0.05/query.

### 3. Try the demo

```bash
people-chat demo --guided
```

This loads 750 synthetic employees from **The Guild** (a D&D-themed company), generates a glossary, and walks through 6 example queries showing different capabilities.

### 4. Use your own data

```bash
people-chat init ./my_employees.csv
people-chat ask "What's the headcount by department?"
```

## 📖 Usage

### Commands

| Command | Description |
|---------|-------------|
| `init <csv>` | Ingest a CSV into SQLite with automatic type detection |
| `ask <question>` | Ask one question, get a table or chart |
| `chat` | Interactive Q&A session with history |
| `stats` | Show data overview (tables, columns, row counts) |
| `status` | Show configuration check |
| `validate` | Validate glossary against database schema |
| `demo` | One-command demo with sample data |
| `demo --guided` | Guided tour showing all capabilities |

### Command examples

```bash
# Ask a question
people-chat ask "How many active employees do we have?"

# Ask with chart
people-chat ask "Show average salary by department" --chart

# See the SQL being generated
people-chat ask "Which department has the most turnover?" --show-sql

# Interactive session
people-chat chat

# Validate glossary against database schema
people-chat validate
```

### Chat commands

Inside `people-chat chat`:
- `/sql` — Toggle SQL display on/off
- `/help` — Show available commands
- `exit` or `quit` — Leave the session

## 🔧 Configuration

All configuration is via environment variables or `~/.people-chat/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `deepseek` | Provider: `deepseek`, `openai`, `anthropic`, `ollama` |
| `LLM_API_KEY` | — | API key for your provider |
| `LLM_MODEL` | `deepseek-chat` | Model name (provider-specific) |
| `LLM_BASE_URL` | provider default | Custom API endpoint |
| `LLM_MAX_TOKENS` | `4096` | Max response tokens |
| `LLM_TEMPERATURE` | `0.1` | Generation temperature (lower = more deterministic) |
| `LLM_TIMEOUT` | `30` | API timeout in seconds |

### Provider defaults

| Provider | Default Model | Cost/Query | Requires |
|----------|--------------|:----------:|----------|
| DeepSeek | deepseek-chat | ~$0.02 | API key |
| OpenAI | gpt-4o-mini | ~$0.05 | API key |
| Anthropic | claude-3-5-haiku | ~$0.08 | API key |
| Ollama | llama3.2 | Free | Local Ollama server |

## 🏢 Demo Data: The Guild

The demo dataset features **The Guild** — a fantasy-themed tech company with 750 employees.

**Leadership team:**
- **Alistair Ironwood** — CEO (founded in 2015)
- **Meredith Kingsley** — CFO, **Dorian Blackthorn** — CTO
- **Seraphina Ravenscroft** — CMO, **Thorne Ashford** — CRO
- **Gideon Stonewall** — COO, **Eleanor Whitmore** — General Counsel

**Organization:**
- 48 departments across 7 divisions (Engineering & Technology, Product, Sales & Revenue, Marketing, Customer Success, G&A, Operations)
- Radford-level salary bands (S1-S6, P1-P6, M1-M6, E1-E6)
- Active, terminated, contractor, leave of absence, and part-time employees
- Realistic compensation data with bonus structures

## 🏗️ Architecture

```
┌──────────┐    ┌──────────────┐    ┌────────┐    ┌───────────┐    ┌──────────────┐
│  CSV     │ →  │  SQLite DB   │ →  │ Schema │ →  │  LLM      │ →  │  Results     │
│ (ingest) │    │ (automatic   │    │ +      │    │ (generates│    │  (table or   │
│          │    │  type detect)│    │Glossary│    │  SQL)     │    │  chart)      │
└──────────┘    └──────────────┘    └────────┘    └───────────┘    └──────────────┘
```

**Pipeline:**
1. **Ingestion** — CSV → SQLite with automatic type detection (INTEGER, REAL, TEXT, DATE)
2. **Schema + Glossary** — Introspects DB structure + generates HR-aware column descriptions
3. **LLM Query** — Natural language → SQL via LLM with few-shot HR examples + safety rules
4. **Execution** — Validates (read-only, injection protection), executes, retries on error
5. **Formatting** — Rich terminal tables + Plotly charts (auto-detects bar/line/pie)

## ✨ Features

- **Natural language queries** — Ask in plain English, get answers from your people data
- **HR-aware glossary** — Understands turnover, comp-ratio, tenure, headcount, diversity metrics
- **Smart charts** — Auto-detects chart type (bar, line, pie) from data shape
- **Interactive chat** — Multi-turn conversations with context history
- **SQL transparency** — Toggle SQL display to see and learn what's being generated
- **Error recovery** — Auto-retries with error feedback when SQL fails
- **Safety first** — Read-only queries, injection protection, DDL blocking
- **Flexible LLM** — Works with DeepSeek, OpenAI, Anthropic, or local Ollama
- **Zero-config demo** — `people-chat demo` loads sample data and starts immediately

## ⚠️ Known Limitations

- Single CSV/database at a time (no cross-DB joins)
- No write-back (read-only analytics)
- Chart auto-open requires a browser
- SQLite only (not designed for production-scale databases)
- LLM latency (~1-5s per query depending on provider)
- Complex multi-step questions may need refinement

## ❓ Troubleshooting

**"LLM_API_KEY is missing"**
```bash
echo "LLM_API_KEY=sk-your-key" >> ~/.people-chat/.env
```

**"No database found"**
```bash
people-chat init ./employees.csv
```
Or try the demo: `people-chat demo`

**"Unknown provider"**
Check your `.env` for typos. Supported: `deepseek`, `openai`, `anthropic`, `ollama`.

**"Could not extract SQL"**
The LLM may need a different approach. Try rephrasing your question, or check that the glossary accurately describes your data columns.

**"SQL execution failed"**
The generated SQL might reference columns that don't exist. Check `people-chat stats` for available columns. The system auto-retries once with error feedback.

**Charts not opening?**
Ensure Plotly is installed: `pip install plotly`. Also check that a browser is available — charts open via `webbrowser.open()`.

## 🏠 Project Structure

```
people-chat/
├── people_chat/
│   ├── __init__.py          # Package marker
│   ├── cli.py               # CLI entry point (argparse)
│   ├── config.py            # Environment config loader
│   ├── llm.py               # LLM provider abstraction
│   ├── ingestion.py         # CSV → SQLite with type detection
│   ├── schema.py            # DB introspection
│   ├── glossary.py          # Glossary YAML gen + validation
│   ├── query_engine.py      # NL → SQL → results pipeline
│   ├── formatter.py         # Output formatting (tables + charts)
│   ├── demo_guide.py        # Guided demo tour
│   ├── prompts/
│   │   ├── system.md        # System prompt with HR rules
│   │   └── few_shot.sql     # 14 Q&A examples
│   └── data/sample/
│       ├── employees.csv    # 750-employee Guild dataset
│       ├── current_team.csv
│       ├── job_catalog.csv
│       ├── reporting_structure.csv
│       └── glossary.yaml    # Pre-generated glossary
├── generate_demo_data.py    # Synthetic data generator
├── pyproject.toml           # Project config + deps
├── README.md                # You are here
├── CONTRIBUTING.md          # Contribution guide
├── LICENSE
└── .gitignore
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, style, and PR guidelines.

Check the [open issues](https://github.com/grantfuller/people-chat/issues) for ideas.

## 📋 Project Status

| Phase | Component | Status |
|:------|:----------|:------:|
| 0 | Foundation | ✅ |
| 1 | Data Ingestion | ✅ |
| 2 | LLM Provider Layer | ✅ |
| 3 | Query Engine | ✅ |
| 4 | Output Formatting | ✅ |
| 5 | CLI Interface | ✅ |
| 6 | Demo Mode Polish | ✅ |
| 7 | Documentation & Polish | ✅ |
| 8 | GitHub Launch | ⏳ |

## 📄 License

MIT — see [LICENSE](LICENSE)
