"""
Anomaly Alerts Page: Explainable Detection Signals & Feedback Loop.
"""
import streamlit as st
from api_client import FinanceAPIClient

st.set_page_config(page_title="Anomaly Alerts - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to view anomaly alerts.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("🚨 Anomaly Alerts")
st.caption("Deterministic, explainable spending anomaly flags requiring user feedback")

try:
    alerts = api.get_alerts()
except Exception as e:
    st.error(f"Error loading alerts: {e}")
    st.stop()

if not alerts:
    st.success("🎉 No spending anomalies detected in your imported statement!")
else:
    st.write(f"Total Alerts: **{len(alerts)}**")

    for alert in alerts:
        severity = alert.get("severity", "medium")
        css_class = "alert-card-high" if severity == "high" else "alert-card-medium"
        
        st.markdown(f"""
        <div class="{css_class}">
            <h4>⚠️ {alert.get('merchant')} - Rs. {alert.get('amount', 0.0):,.2f}</h4>
            <p><strong>Reason:</strong> {alert.get('plain_language_reason')}</p>
            <p><strong>Signals Fired:</strong> <code>{', '.join(alert.get('signals_fired', []))}</code> | <strong>Severity:</strong> <code>{severity.upper()}</code></p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        status = alert.get("user_feedback", "pending")
        col1.write(f"Current Status: **{status.title()}**")

        if status == "pending":
            if col2.button("✅ Mark Expected", key=f"exp_{alert['id']}"):
                try:
                    api.submit_alert_feedback(alert["id"], "expected")
                    st.success("Marked as expected. Future baselines adjusted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

            if col3.button("🚩 Mark Suspicious", key=f"susp_{alert['id']}"):
                try:
                    api.submit_alert_feedback(alert["id"], "suspicious")
                    st.warning("Marked as suspicious.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        st.markdown("---")
