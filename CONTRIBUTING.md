# Contributing to People Chat

## Development Setup

```bash
git clone <your-fork>
cd people-chat
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Code Style

- Ruff for linting: `ruff check people_chat/`
- Line length: 100
- Follow existing patterns (modular, documented, tested)

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Run ruff and fix any issues
4. Add tests if applicable
5. Open a PR with a clear description of what and why

## Architecture Notes

- Each module in `people_chat/` has a single responsibility
- The query pipeline is: `CLI → QueryEngine → LLM → SQL → DB → Formatter`
- New LLM providers: add to `llm.py`'s `PROVIDER_REGISTRY`
- New chart types: add to `formatter.py`'s chart detection
- Prompts are in `people_chat/prompts/` as separate files
