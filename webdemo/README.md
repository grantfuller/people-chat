# People Chat — Web Demo (Streamlit)

Prospect-facing web demo of People Chat: an AI-powered HR data analyst.
Ask questions in English about synthetic HR data (750 fictional employees
from "The Guild"), get SQL-generated answers as tables and charts.

**Purpose:** outreach proof-point for Cache Valley Analytics (T1/T2).
**Data:** 100% synthetic, seeded PRNG, no real company data.
**Gate:** passcode-protected (set via `DEMO_PASSCODE` secret) to prevent
API abuse and keep it invitation-only for prospects.

## Deploy (Streamlit Community Cloud — free)

1. Push this repo to GitHub (already public: `grantfuller/people-chat`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** →
   select repo, branch `main`, main file `webdemo/app.py`.
3. **Secrets** (Settings → Secrets):
   ```
   DEMO_PASSCODE = "your-code-here"
   LLM_PROVIDER = "deepseek"      # or openai / anthropic / groq
   LLM_API_KEY = "sk-..."          # DeepSeek key
   LLM_MODEL = "deepseek-chat"
   ```
4. App deploys at `https://<app>.streamlit.app`.

## Run locally

```bash
cd people-chat
pip install -r webdemo/requirements.txt
python3 generate_demo_data.py        # builds people_chat/data/sample CSVs (already committed)
python3 - <<'EOF'
from people_chat.ingestion import ingest
from pathlib import Path
ingest("people_chat/data/sample/employees.csv", "demo_hr.db", table_name="employees")
EOF
DEMO_PASSCODE=cachevalley LLM_API_KEY=sk-... streamlit run webdemo/app.py
```

## Notes

- The query engine lives in `people_chat/` — the web UI is a thin wrapper
  around `query_engine.ask()` (same brain as the CLI).
- Sample questions in the UI mirror the CLI demo guide.
- Rate-limit / abuse: passcode gate + Streamlit Cloud's built-in app
  limits. For heavier protection, add a simple per-IP counter or switch
  the LLM to a cheap model with low `max_tokens`.
