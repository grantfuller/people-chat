# People Chat 🧑‍💼

**AI-powered HR data analyst. Ask questions in English, get answers from your data.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

Turn your HR data into answers. People Chat ingests employee CSVs, builds a searchable database, and lets you ask questions in plain English. It generates SQL queries using an LLM, executes them against your data, and returns results as tables or charts.

```bash
# One-command demo
people-chat demo

# Or use your own data
people-chat init ./employees.csv
people-chat ask "Which department has the most turnover?"
people-chat ask "Chart salary distribution by department"
people-chat chat
```

## Quick Start

```bash
pip install -e .
echo "LLM_API_KEY=***" > ~/.people-chat/.env
echo "LLM_PROVIDER=deepseek" >> ~/.people-chat/.env

# Load your data
people-chat init ./employees.csv

# Start asking questions
people-chat ask "How many active employees do we have?"
```

## Features

- 🗣️ **Natural language queries** — Ask in English, get answers
- 📊 **Tables + charts** — Results formatted for humans, charts open in browser
- 🏢 **HR-aware** — Understands turnover, comp-ratio, tenure, headcount
- 🔌 **BYO LLM** — Works with DeepSeek, OpenAI, Anthropic, or local Ollama
- 📁 **CSV ingestion** — Load any employee export
- 🛡️ **SQL safety** — Read-only queries, injection protection, error recovery

## Commands

| Command | Description |
|---------|-------------|
| `init <csv>` | Ingest CSV into SQLite, generate glossary |
| `ask <question>` | Ask one question |
| `chat` | Interactive Q&A session |
| `stats` | Show data overview |
| `status` | Show configuration |
| `demo` | One-command demo with sample data |

## Architecture

```
CSV → SQLite → Schema + Glossary → LLM → SQL → Results → Table/Chart
```

## LLM Providers

| Provider | Env Setup | Est. Cost |
|----------|-----------|:---------:|
| DeepSeek | `LLM_PROVIDER=deepseek` + API key | ~$0.02/query |
| OpenAI | `LLM_PROVIDER=openai` + API key | ~$0.05/query |
| Anthropic | `LLM_PROVIDER=anthropic` + API key | ~$0.08/query |
| Ollama | `LLM_PROVIDER=ollama` (local, free) | Free |

## Project Status

| Phase | Component | Status |
|:-----|:----------|:------:|
| 0 | Foundation | ✅ |
| 1 | Data Ingestion | ✅ |
| 2 | LLM Provider Layer | ✅ |
| 3 | Query Engine | ✅ |
| 4 | Output Formatting | ✅ |
| 5 | CLI Interface | ✅ |
| 6 | Demo Mode | 🔄 |
| 7 | Documentation & Polish | ⏳ |
| 8 | GitHub Launch | ⏳ |

## Demo Data

Includes synthetic data for **The Guild** — 750 employees, 48 departments, 7 divisions.
Company is D&D-themed (CEO: Alistair Ironwood, CTO: Dorian Blackthorn, etc.).
Radford-level salary bands with realistic ranges.

## License

MIT
