"""
People Chat — Web Demo (Streamlit)

AI-powered HR data analyst demo over synthetic data (The Guild, 750
fictional employees). Two modes:

1. CANNED (default, zero cost): the sample questions are answered with
   pre-written SQL executed directly against the demo DB. No LLM call,
   no API key, nothing billed. This keeps the host's wallet safe.

2. BYOK (optional): a visitor can paste their OWN API key in the sidebar
   (password field, held only in their session state) to ask free-text
   questions. The key is never stored, never logged, never sent anywhere
   except the chosen LLM provider.

The host's API key is NOT used anywhere in this app. Streamlit secrets
are optional and only used for the passcode.

Deployment: Streamlit Community Cloud (free). See webdemo/README.md.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from people_chat.query_engine import execute_sql  # noqa: E402

DEMO_PASSCODE = os.getenv("DEMO_PASSCODE", "cachevalley")


def _load_passcodes() -> tuple[dict[str, str], str | None]:
    """Load passcodes. Prefers DEMO_PASSCODES (JSON dict: code -> label) for
    per-prospect tracking; falls back to a single DEMO_PASSCODE string.
    Returns (map, default_code)."""
    raw = os.getenv("DEMO_PASSCODES", "")
    if raw.strip():
        try:
            import json

            mapping = json.loads(raw)
            if isinstance(mapping, dict) and mapping:
                return mapping, None
        except Exception:  # noqa: BLE001 - fall through to single-code mode
            pass
    single = os.getenv("DEMO_PASSCODE", "cachevalley")
    return {single: None}, single


PASSCODE_MAP, _ = _load_passcodes()

st.set_page_config(page_title="People Chat — HR Data Demo", page_icon="🧑‍💼", layout="wide")

DB_PATH = None  # resolved on first use


def _ensure_db() -> Path:
    """Build the demo DB from committed sample CSVs if missing (cloud-friendly)."""
    global DB_PATH
    if DB_PATH and DB_PATH.exists():
        return DB_PATH
    from people_chat.ingestion import ingest

    sample_dir = REPO_ROOT / "people_chat" / "data" / "sample"
    csv = sample_dir / "employees.csv"
    if not csv.exists():
        raise FileNotFoundError(
            f"Sample data not found at {csv}. Run generate_demo_data.py first."
        )
    DB_PATH = REPO_ROOT / "demo_hr.db"
    ingest(str(csv), str(DB_PATH), table_name="employees")
    return DB_PATH


# ─── Canned answers (zero-cost mode) ─────────────────────────────────────────
CANNED = [
    {
        "match": "how many active",
        "sql": 'SELECT COUNT(*) AS active_employees FROM employees WHERE "Employment Status" = \'Active\'',
        "explanation": "Here's the current active headcount:",
    },
    {
        "match": "average salary by department",
        "sql": 'SELECT "Department" AS department, CAST(AVG("Pay rate") AS INTEGER) AS avg_salary FROM employees GROUP BY "Department" ORDER BY avg_salary DESC',
        "explanation": "Average pay rate by department (rounded):",
    },
    {
        "match": "top 10 highest paid",
        "sql": 'SELECT "First Name Last Name" AS name, "Job Title" AS title, CAST("Pay rate" AS INTEGER) AS pay FROM employees ORDER BY "Pay rate" DESC LIMIT 10',
        "explanation": "The ten highest-paid employees:",
    },
    {
        "match": "salary distribution by level",
        "sql": 'SELECT "Radford Level" AS level, CAST(AVG("Pay rate") AS INTEGER) AS avg_salary, COUNT(*) AS employees FROM employees GROUP BY "Radford Level" ORDER BY avg_salary DESC',
        "explanation": "Average pay by Radford level:",
    },
    {
        "match": "most turnover",
        "sql": """SELECT "Department" AS department,
                  SUM(CASE WHEN "Employment Status" = 'Terminated' THEN 1 ELSE 0 END) AS terminations,
                  COUNT(*) AS headcount,
                  ROUND(100.0 * SUM(CASE WHEN "Employment Status" = 'Terminated' THEN 1 ELSE 0 END) / COUNT(*), 1) AS turnover_pct
                  FROM employees GROUP BY "Department" ORDER BY turnover_pct DESC""",
        "explanation": "Departments ranked by turnover (share of terminations in current file):",
    },
    {
        "match": "headcount by division",
        "sql": 'SELECT "Division" AS division, COUNT(*) AS employees FROM employees GROUP BY "Division" ORDER BY employees DESC',
        "explanation": "Headcount by division:",
    },
    {
        "match": "average tenure by department",
        "sql": """SELECT "Department" AS department,
                  ROUND(AVG((julianday('now') - julianday("Hire Date")) / 365.25), 1) AS avg_tenure_years,
                  COUNT(*) AS employees
                  FROM employees GROUP BY "Department" ORDER BY avg_tenure_years DESC""",
        "explanation": "Average tenure in years by department:",
    },
    {
        "match": "engineering",
        "sql": """SELECT COUNT(*) AS engineering_headcount FROM employees
                  WHERE "Department" LIKE '%Engineering%'""",
        "explanation": "Headcount across Engineering-related departments:",
    },
]

SAMPLE_QUESTIONS = [
    "How many active employees do we have?",
    "What's the average salary by department?",
    "Who are the top 10 highest paid employees?",
    "Show me the salary distribution by level",
    "What departments have the most turnover?",
    "Show me headcount by division",
    "What's the average tenure by department?",
    "How many employees are in Engineering?",
]


def _match_canned(question: str) -> dict | None:
    q = question.lower()
    for c in CANNED:
        if c["match"] in q:
            return c
    return None


def run_canned(canned: dict) -> dict:
    db_path = _ensure_db()
    result = execute_sql(str(db_path), canned["sql"])
    return {
        "success": result.get("success", False),
        "sql": canned["sql"],
        "explanation": canned["explanation"],
        "results": result.get("results") or result,
        "error": result.get("error"),
    }


# ─── BYOK free-text mode ─────────────────────────────────────────────────────
def run_byok(question: str, provider: str, api_key: str, model: str) -> dict:
    import people_chat.config as cfg
    from people_chat.query_engine import ask

    conf = cfg.ProviderConfig()
    conf.provider = provider
    conf.api_key = api_key
    conf.model = model
    conf = cfg.apply_defaults(conf)
    result = ask(question, str(_ensure_db()), config=conf)
    return result


# ─── Passcode gate ───────────────────────────────────────────────────────────
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🧑‍💼 People Chat — HR Data Demo")
    st.caption("An AI-powered HR data analyst demo. Ask questions in English, get answers from data.")
    code = st.text_input("Demo passcode", type="password", placeholder="Enter the passcode from your outreach email")
    if st.button("Enter demo"):
        if code in PASSCODE_MAP:
            st.session_state.authed = True
            st.session_state.visitor_label = PASSCODE_MAP.get(code)
            st.rerun()
        else:
            st.error("Incorrect passcode. (This demo is private — request access for a code.)")
    st.stop()

visitor_label = st.session_state.get("visitor_label")

# ─── Sidebar: BYOK config ────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")
    st.caption("**Sample questions work with no key.** For free-text questions, bring your own LLM key (optional).")
    byok_key = st.text_input(
        "Your API key (optional)",
        type="password",
        placeholder="sk-... (OpenAI/DeepSeek/etc.)",
        help="Held only in your browser session. Never stored or logged.",
    )
    byok_provider = st.selectbox("Provider", ["openai", "deepseek", "anthropic"])
    byok_model = st.text_input(
        "Model",
        value="gpt-4o-mini" if byok_provider == "openai" else "deepseek-chat",
        help="e.g. gpt-4o-mini, deepseek-chat, claude-sonnet-4-5",
    )
    st.divider()
    st.caption("🔒 Your key never touches the server — it lives in this browser tab only.")

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🧑‍💼 People Chat — HR Data Demo")
if visitor_label:
    st.caption(f"👋 Welcome, {visitor_label}! · Synthetic data · 750 fictional employees · Sample questions run free (no key) · Free-text needs your own key")
else:
    st.caption("Synthetic data · 750 fictional employees · Sample questions run free (no key) · Free-text needs your own key")

# ─── Chat UI ─────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "table" in msg:
            st.dataframe(msg["table"], use_container_width=True)
        if "chart" in msg and msg["chart"] is not None:
            st.plotly_chart(msg["chart"], use_container_width=True)

st.markdown("---")
st.caption("Try one of these (free, no key needed):")
cols = st.columns(4)
for i, q in enumerate(SAMPLE_QUESTIONS):
    if cols[i % 4].button(q, key=f"sq_{i}"):
        st.session_state.pending = q

question = st.chat_input("Ask about the data… (sample questions are free; anything else needs your key in the sidebar)")
if "pending" in st.session_state and st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        canned = _match_canned(question)
        if canned:
            with st.spinner("Querying demo data…"):
                result = run_canned(canned)
            mode = "canned"
        elif byok_key.strip():
            with st.spinner("Generating SQL and querying…"):
                try:
                    result = run_byok(question, byok_provider, byok_key.strip(), byok_model.strip())
                except Exception as e:  # noqa: BLE001
                    result = {"success": False, "error": str(e), "explanation": str(e)}
            mode = "byok"
        else:
            result = {
                "success": False,
                "explanation": "Add your own API key in the sidebar to ask free-text questions — or try one of the sample questions above (no key needed).",
            }
            mode = "none"

        if not result.get("success"):
            err = result.get("error") or result.get("explanation") or "Something went wrong."
            st.info(f"{err}")
            st.session_state.messages.append({"role": "assistant", "content": f"ℹ️ {err}"})
        else:
            explanation = result.get("explanation") or ""
            results = result.get("results") or {}
            cols_ = results.get("columns") or []
            rows_ = results.get("rows") or []
            if explanation:
                st.markdown(explanation)
            if rows_:
                df = pd.DataFrame(rows_)
                st.dataframe(df, use_container_width=True)
                msg = {"role": "assistant", "content": explanation or "Here you go:", "table": df}
                if len(cols_) == 2 and len(df) <= 25:
                    try:
                        import plotly.express as px

                        cat, val = cols_[0], cols_[1]
                        if pd.api.types.is_numeric_dtype(df[val]):
                            fig = px.bar(df, x=cat, y=val, title=f"{val} by {cat}")
                            st.plotly_chart(fig, use_container_width=True)
                            msg["chart"] = fig
                    except Exception:  # noqa: BLE001
                        pass
            else:
                msg = {"role": "assistant", "content": explanation or "No rows returned."}
                st.markdown(explanation or "No rows returned.")
            if result.get("sql"):
                with st.expander("SQL used"):
                    st.code(result["sql"], language="sql")
            st.session_state.messages.append(msg)

st.markdown("---")
st.caption("© Cache Valley Analytics · Demo uses synthetic data only · Built on People Chat (MIT) · No server-side API key")
