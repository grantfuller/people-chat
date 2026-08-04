# People Chat — Web Demo (Streamlit)

Prospect-facing web demo of People Chat: an AI-powered HR data analyst.
Ask questions in English about synthetic HR data (750 fictional employees
from "The Guild"), get answers as tables and charts.

**Purpose:** outreach proof-point for Cache Valley Analytics (T1/T2).
**Data:** 100% synthetic, seeded PRNG, no real company data.
**Gate:** passcode-protected (set via `DEMO_PASSCODE` secret).

## Cost model — the host's API key is never used 🛡️

Two modes, and **neither bills the host**:

1. **CANNED mode (default, $0):** the 8 sample questions are answered with
   pre-written SQL executed directly against the demo DB. No LLM call, no
   API key, nothing billed. This is what prospects see first.
2. **BYOK mode (visitor-funded):** a visitor can paste their **own** API key
   into the sidebar (password field) to ask free-text questions. The key is
   held only in their browser session (`st.session_state`) — never stored,
   never logged, never sent anywhere except the LLM provider they chose.

**Streamlit secrets are therefore optional** — only `DEMO_PASSCODE` is
required. Do NOT put an `LLM_API_KEY` in secrets; the app doesn't read one.

## Deploy (Streamlit Community Cloud — free)

1. Push this repo to GitHub (already public: `grantfuller/people-chat`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** →
   select repo, branch `main`, main file `webdemo/app.py`.
3. **Secrets** (Settings → Secrets) — only the passcode:
   ```
   DEMO_PASSCODE = "your-code-here"
   ```
4. App deploys at `https://<app>.streamlit.app`. Save secrets, then
   **Rerun/Restart** from the ⋮ menu.

## Run locally

```bash
cd people-chat
python3 -m venv .venv && ./.venv/bin/pip install -r webdemo/requirements.txt
DEMO_PASSCODE=cachevalley ./.venv/bin/streamlit run webdemo/app.py
```

The demo DB auto-builds on first run from the committed sample CSVs
(`people_chat/data/sample/employees.csv`), so no setup is needed.

## Notes

- BYOK supported providers: `openai` (gpt-4o-mini), `deepseek`
  (deepseek-chat), `anthropic` (claude-sonnet-4-5) — selectable in the
  sidebar with a free-text model override.
- The query engine lives in `people_chat/` — the web UI wraps
  `query_engine.ask()` (BYOK) and `query_engine.execute_sql()` (canned).
- If you want to allow *trusted* guests to use the host's key, add a
  second passcode check — but the default design intentionally never
  touches a server-side key.
