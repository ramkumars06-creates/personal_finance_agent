"""
Settings Page: Consent Management, DPDP Data Export, Account Deletion & Legal Drafts.
"""
import json
import streamlit as st
from api_client import FinanceAPIClient

st.set_page_config(page_title="Settings - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to manage settings.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("⚙️ Account Settings & Privacy Controls")
st.caption("India DPDP Act 2023 Compliance Controls: Granular Consents, Export Data & Account Erasure")

tab_profile, tab_privacy, tab_legal = st.tabs(["Profile & Goals", "DPDP Rights & Consent", "Legal Drafts & Explainer"])

with tab_profile:
    st.subheader("Update Financial Profile")
    try:
        profile = api.get_profile()
        curr_income = float(profile.get("monthly_income") or 50000.0)
        curr_goal = float(profile.get("savings_goal") or 10000.0)
        
        inc_val = st.number_input("Monthly Income (INR)", value=curr_income, step=5000.0)
        goal_val = st.number_input("Monthly Savings Goal (INR)", value=curr_goal, step=1000.0)

        if st.button("Save Profile"):
            api.update_profile({"monthly_income": inc_val, "savings_goal": goal_val})
            st.success("Profile saved successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error loading profile: {e}")

with tab_privacy:
    st.subheader("DPDP Act Granular Consent Settings")
    try:
        consent = api.get_consent()
        store_c = st.checkbox("Consent to store raw transaction records", value=consent.get("transaction_storage_consent", True))
        llm_c = st.checkbox("Consent to AI processing for categorization and advice", value=consent.get("llm_processing_consent", True))

        if st.button("Update Consent Preferences"):
            api.update_consent(store_c, llm_c)
            st.success("Consent preferences updated.")
            st.rerun()
    except Exception as e:
        st.error(f"Error loading consent: {e}")

    st.markdown("---")
    st.subheader("📥 Export My Personal Data (DPDP Data Portability)")
    if st.button("Generate Complete JSON Data Export"):
        try:
            export_payload = api.export_data()
            json_str = json.dumps(export_payload, indent=2)
            st.download_button(
                label="Download Personal Data Export (JSON)",
                data=json_str,
                file_name="my_personal_finance_data.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Failed to export data: {e}")

    st.markdown("---")
    st.subheader("⚠️ Delete Account & Erase All Data (Right to be Forgotten)")
    st.write("This action will permanently delete your account and hard-purge all transactions, budgets, alerts, and summaries.")
    if st.button("Permanently Erase My Account & Data", type="primary"):
        try:
            res = api.delete_account()
            st.success(res.get("message"))
            st.session_state.token = None
            st.session_state.user_email = None
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete account: {e}")

with tab_legal:
    st.subheader("Draft Policy Templates & AI Explainer")
    st.warning("Note: These documents are draft templates for educational purposes and must be reviewed by qualified legal counsel.")

    st.markdown("#### How the AI Makes Decisions")
    st.write("""
    1. **Observation**: Transactions are normalized and mapped using keyword rules and LLM fallback.
    2. **Detection**: Statistical baselines (Z-score & IQR) flag spending deviations above standard thresholds.
    3. **Recommendation**: Actionable savings targets are computed deterministically in Python. The LLM only phrases plain-language text explanations.
    4. **Safety**: No automated actions are ever taken without explicit user review and confirmation.
    """)

    with st.expander("Privacy Policy Draft"):
        st.write("""
        This Privacy Policy describes how Personal Finance Agent collects, uses, and protects personal data in compliance with India's Digital Personal Data Protection (DPDP) Act 2023.
        Data collected includes encrypted transaction descriptions, categories, and account goals. You retain full rights to withdraw consent, export data, or erase your account at any time.
        """)

    with st.expander("Terms of Use Draft"):
        st.write("""
        This tool provides financial awareness and spending tracking only. It is NOT a licensed financial adviser, investment counselor, or credit agency.
        All AI recommendations must be independently verified by the user before taking action.
        """)
