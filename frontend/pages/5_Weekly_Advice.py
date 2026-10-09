"""
Weekly Advice Page: Actionable Budget Recommendations & AI Explanation.
"""
import streamlit as st
from api_client import FinanceAPIClient

st.set_page_config(page_title="Weekly Advice - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to access weekly advice.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("💡 Weekly Advisor Recommendations")
st.caption("Proactive, Python-calculated budget recommendations rephrased into plain-language guidance")

try:
    summary = api.get_weekly_advice()
except Exception as e:
    st.error(f"Error loading weekly advice: {e}")
    st.stop()

if not summary:
    st.info("No weekly advice generated yet. Import a statement or run the weekly advisor.")
else:
    st.markdown("### AI Financial Explanation")
    st.info(summary.get("llm_explanation", ""))

    st.markdown("### Python-Calculated Recommendations")
    recs = summary.get("recommendations", [])

    for idx, r in enumerate(recs):
        rs_val = r.get("rs_change", 0.0)
        sign_str = f"Rs. {rs_val:+,.2f}" if rs_val != 0 else "Maintain"
        
        with st.expander(f"Recommendation {idx+1}: {r.get('category')} ({sign_str})", expanded=True):
            st.write(f"**Reason:** {r.get('reason')}")
            st.write(f"**Effect on Savings Goal:** {r.get('savings_effect')}")

    st.markdown("---")
    if summary.get("is_accepted"):
        st.success("✅ Recommendations accepted for this week!")
    else:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Accept Recommendations", type="primary", use_container_width=True):
                try:
                    api.accept_weekly_recommendations(summary["id"])
                    st.success("Recommendations accepted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to accept advice: {e}")
