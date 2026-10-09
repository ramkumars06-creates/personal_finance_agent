"""
Agent Trace Page: Explores LangGraph multi-agent execution pipeline timing and nodes.
"""
import streamlit as st
import pandas as pd
from api_client import FinanceAPIClient

st.set_page_config(page_title="Agent Trace - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to view execution traces.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("🕵️ LangGraph Agent Execution Trace")
st.caption("Inspect multi-agent node execution order, status, latency (ms), and fallback mode flag")

exec_id = st.session_state.get("execution_id", "demo_exec_id")

try:
    trace_res = api.get_agent_trace(exec_id)
except Exception as e:
    st.error(f"Error fetching execution trace: {e}")
    st.stop()

st.markdown(f"**Execution ID:** `{trace_res.get('execution_id')}` | **Total Latency:** `{trace_res.get('total_duration_ms')} ms` | **Fallback Mode:** `{trace_res.get('fallback_mode_used')}`")

steps = trace_res.get("steps", [])
if steps:
    df_steps = pd.DataFrame(steps)
    df_steps.columns = ["Step #", "Agent Name", "Status", "Duration (ms)", "Summary Output"]
    st.dataframe(df_steps, use_container_width=True)

    st.markdown("### Execution Pipeline Timeline")
    for s in steps:
        st.markdown(f"""
        - **Step {s['step']}: {s['agent_name']}** — `{s['status'].upper()}` ({s['duration_ms']} ms)
          *Summary:* {s['summary']}
        """)
else:
    st.info("No trace data recorded for this session.")
