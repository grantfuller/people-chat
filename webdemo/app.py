"""
People Chat — Web Demo (Streamlit)

AI-powered HR data analyst demo. Ask questions in English, get answers
from synthetic HR data (The Guild — 750 fictional employees).

Deployment: Streamlit Community Cloud (free). Set DEMO_PASSCODE as a
Streamlit secret (or env var). The LLM provider reads standard
PEOPLE_CHAT / LLM_* env vars (see people_chat/config.py).

Run locally:
    pip install -r requirements.txt
    DEMO_PASSCODE=yourcode LLM_API_KEY=sk-... streamlit run webdemo/app.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from people_chat.query_engine import ask  # noqa: E402

DB_PATH = REPO_ROOT / "demo_hr.db"
if not DB_PATH.exists():
    DB_PATH = REPO_ROOT / "people_chat" / "data" / "demo_hr.db"

DEMO_PASSCODE = os.getenv("DEMO_PASSCODE", "cachevalley")

st.set_page_config(page_title="People Chat — HR Data Demo", page_icon="🧑‍💼", layout="wide")

# ─── Passcode gate ───────────────────────────────────────────────────────────
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🧑‍💼 People Chat — HR Data Demo")
    st.caption("An AI-powered HR data analyst demo. Ask questions in English, get answers from data.")
    code = st.text_input("Demo passcode", type="password", placeholder="Enter the passcode from your outreach email")
    if st.button("Enter demo"):
        if code == DEMO_PASSCODE:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Incorrect passcode. (This demo is private — request access for a code.)")
    st.stop()

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🧑‍💼 People Chat — HR Data Demo")
st.caption("Synthetic data · 750 fictional employees · Ask anything about headcount, pay, tenure, departments")

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
st.caption("Try one of these:")
cols = st.columns(4)
for i, q in enumerate(SAMPLE_QUESTIONS):
    if cols[i % 4].button(q, key=f"sq_{i}"):
        st.session_state.pending = q

question = st.chat_input("Ask about the data… (e.g. 'average salary by department')")
if "pending" in st.session_state and st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Generating SQL and querying…"):
            try:
                result = ask(question, str(DB_PATH))
            except Exception as e:  # noqa: BLE001
                result = {"success": False, "error": str(e), "explanation": str(e)}

        if not result.get("success"):
            err = result.get("error") or result.get("explanation") or "Something went wrong."
            st.warning(f"I need a bit more info — {err}")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {err}"})
        else:
            explanation = result.get("explanation") or ""
            if explanation:
                st.markdown(explanation)
            cols_ = (result.get("results") or {}).get("columns") or result.get("columns") or []
            rows_ = (result.get("results") or {}).get("rows") or result.get("rows") or []
            if rows_:
                df = pd.DataFrame(rows_)
                st.dataframe(df, use_container_width=True)
                msg = {"role": "assistant", "content": explanation or "Here you go:", "table": df}
                # simple bar chart for single-metric-by-category results
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
st.caption("© Cache Valley Analytics · Demo uses synthetic data only · Built on People Chat (MIT)")
