# People Chat 🧑‍💼

**AI-powered HR data analyst. Ask questions in English, get answers from your data.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

People Chat is a CLI tool that connects to your HR data and lets you ask questions in plain English. It generates SQL queries using an LLM, executes them against your data, and returns results as tables or charts.

```bash
# One-command demo (coming in Phase 6)
# people-chat demo

# Ask questions about your data
# people-chat ask "Which department had the most turnover last quarter?"
# people-chat ask "Show me employees with less than 5 days PTO"
# people-chat ask "Chart headcount by month for 2025"
```

## Status

**Phase 3 of 8 complete.** The query engine is working — you can ask natural language questions and get SQL-generated answers. CLI interface is next.

## Quick Start (Developer Preview)

```bash
# Clone and install
git clone https://github.com/YOUR_USER/people-chat.git
cd people-chat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up your LLM
echo "LLM_API_KEY=your-key" > ~/.people-chat/.env
echo "LLM_PROVIDER=deepseek" >> ~/.people-chat/.env

# Test with sample data
python3 test_pipeline.py
```

## Architecture

```
CSV → SQLite → Schema + Glossary → LLM → SQL → Results
```

| Component | Module | Status |
|-----------|--------|--------|
| CSV Ingestion | ingestion.py | ✅ |
| Schema Introspection | schema.py | ✅ |
| Glossary Generation | glossary.py | ✅ |
| LLM Provider Layer | llm.py + config.py | ✅ |
| Query Engine | query_engine.py | ✅ |
| CLI Interface | cli.py | 🔜 |
| Output Formatting | formatter.py | 🔜 |

## LLM Providers

| Provider | Env Setup | Cost |
|----------|-----------|------|
| DeepSeek | `LLM_PROVIDER=deepseek` + API key | ~$0.02/query |
| OpenAI | `LLM_PROVIDER=openai` + API key | ~$0.05/query |
| Anthropic | `LLM_PROVIDER=anthropic` + API key | ~$0.08/query |
| Ollama | `LLM_PROVIDER=ollama` (local) | Free |

## Roadmap

- **Phase 3 ✓** — Query engine (natural language → SQL → results)
- **Phase 4** — Output formatting (tables with rich, charts with Plotly)
- **Phase 5** — CLI interface (init, ask, chat commands)
- **Phase 6** — Demo mode (one-command experience)
- **Phase 7** — Documentation & polish
- **Phase 8** — GitHub launch

## Demo Data

The repo includes synthetic demo data for "The Guild" — a fantasy-themed tech company with 750 employees across 7 divisions and 48 departments. Generated from realistic Radford-level salary bands and job titles.

## License

MIT
