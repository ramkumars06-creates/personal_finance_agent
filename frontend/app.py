"""
Streamlit Multi-Page Main Application.
Manages session state, authentication, sidebar navigation, dark mode styling, and landing view.
"""
import streamlit as st
from api_client import FinanceAPIClient

# Page Configuration
st.set_page_config(
    page_title="Personal Finance Agent - Agentic AI Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tokens & Modern Styling
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stMetric {
        background: linear-gradient(135deg, #1E2640 0%, #0F172A 100%);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .disclaimer-banner {
        background-color: #1E293B;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 0.9em;
        color: #94A3B8;
    }
    .alert-card-high {
        background-color: #451A1A;
        border-left: 4px solid #EF4444;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .alert-card-medium {
        background-color: #3B2E1E;
        border-left: 4px solid #F59E0B;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "execution_id" not in st.session_state:
    st.session_state.execution_id = None

api = FinanceAPIClient()
if st.session_state.token:
    api.set_token(st.session_state.token)

# Sidebar & Global Header
st.sidebar.title("💰 Finance Agent")
st.sidebar.caption("Agentic AI Budget & Spending Assistant")

# Always show disclaimer
st.markdown("""
<div class="disclaimer-banner">
    ℹ️ <strong>Financial Awareness Disclaimer:</strong> This tool supports financial awareness and planning; it is not a replacement for a financial adviser. No recommendation is executed automatically.
</div>
""", unsafe_allow_html=True)

if not st.session_state.token:
    # Public Landing Page & Auth Tabs
    st.title("Personal Finance Agent: Agentic AI Budget Assistant")
    st.subheader("Observe ➔ Understand ➔ Detect ➔ Recommend ➔ Improve")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        ### Features Built For Public Users in India:
        - 📊 **Automatic Transaction Categorization**: Hybrid keyword rules & LLM fallback.
        - 🚨 **Explainable Anomaly Alerts**: Z-Score & statistical signal triggers.
        - 🎯 **Budget-vs-Actual Tracking**: Weekly target tracking in INR (Rs.).
        - 💡 **Weekly AI Recommendations**: Deterministic Python recommendations with plain-language explanations.
        - 🔒 **DPDP Act 2023 Ready**: Granular consent, export data, and account deletion rights.
        """)

        st.markdown("---")
        if st.button("🚀 Try Instant Demo Mode (No Signup Required)", type="primary", use_container_width=True):
            try:
                res = api.seed_demo()
                st.session_state.token = res["access_token"]
                st.session_state.user_email = res["email"]
                st.success("Demo environment loaded! Select any page from the sidebar to explore.")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading demo: {e}")

    with col2:
        tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

        with tab_login:
            st.write("### Access Account")
            login_email = st.text_input("Email Address", key="login_email")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In", use_container_width=True):
                try:
                    res = api.login(login_email, login_pass)
                    st.session_state.token = res["access_token"]
                    st.session_state.user_email = res["email"]
                    st.success("Logged in successfully!")
                    st.rerun()
                except Exception as e:
                    st.error("Login failed. Check your email or password.")

        with tab_signup:
            st.write("### Create Public Account")
            signup_email = st.text_input("Email Address", key="signup_email")
            signup_pass = st.text_input("Password (min 8 chars)", type="password", key="signup_pass")
            age_check = st.checkbox("I confirm I am 18 years of age or older (Mandatory Age Gate)", value=True)
            consent_store = st.checkbox("Consent to store transactions for budget analysis", value=True)
            consent_llm = st.checkbox("Consent to AI processing for categorization & advice", value=True)

            if st.button("Create Account & Sign In", use_container_width=True):
                if not age_check:
                    st.error("You must confirm you are 18+ to register.")
                else:
                    try:
                        res = api.signup({
                            "email": signup_email,
                            "password": signup_pass,
                            "age_confirmed": age_check,
                            "transaction_storage_consent": consent_store,
                            "llm_processing_consent": consent_llm
                        })
                        st.session_state.token = res["access_token"]
                        st.session_state.user_email = res["email"]
                        st.success("Account created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Signup failed: {e}")
else:
    st.sidebar.success(f"Signed in as: **{st.session_state.user_email}**")
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.user_email = None
        st.rerun()

    # Statement Uploader Sidebar Section
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Import Bank Statement")
    uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel Statement", type=["csv", "xlsx", "xls"])
    if uploaded_file is not None:
        if st.sidebar.button("Run AI Agent Pipeline", type="primary", use_container_width=True):
            with st.spinner("Executing LangGraph Multi-Agent Pipeline..."):
                try:
                    bytes_data = uploaded_file.getvalue()
                    res = api.upload_statement(bytes_data, uploaded_file.name)
                    st.session_state.execution_id = res["execution_id"]
                    st.sidebar.success(f"Parsed {res['total_rows_parsed']} rows! Flagged {res['anomalies_flagged']} anomalies.")
                except Exception as e:
                    st.sidebar.error(f"Upload failed: {e}")

    st.title("Personal Finance Agent Dashboard")
    st.info("Use the sidebar navigation to explore Overview, Transactions, Alerts, Budget, Weekly Advice, Agent Trace, and Settings.")
