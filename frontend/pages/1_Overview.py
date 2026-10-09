"""
Overview Page: KPI Cards, Spend Breakdown Chart, and Overview Metrics.
"""
import streamlit as st
import pandas as pd
from api_client import FinanceAPIClient

st.set_page_config(page_title="Overview - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to access your financial overview.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("📊 Financial Overview")
st.caption("Real-time spending metrics and category allocation in INR (Rs.)")

try:
    txns = api.get_transactions()
    budgets = api.get_budgets()
    alerts = api.get_alerts()
except Exception as e:
    st.error(f"Error loading overview data: {e}")
    st.stop()

total_spend = sum(t["amount"] for t in txns if t.get("transaction_type") == "debit")
pending_alerts = len([a for a in alerts if a.get("user_feedback") == "pending"])
overbudget_count = len([b for b in budgets if b.get("is_overbudget")])

# KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Spending", f"Rs. {total_spend:,.2f}")
col2.metric("Total Transactions", len(txns))
col3.metric("Pending Anomaly Alerts", pending_alerts, delta_color="inverse")
col4.metric("Overbudget Categories", overbudget_count, delta_color="inverse")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Category Allocation (INR)")
    if txns:
        df = pd.DataFrame(txns)
        debits = df[df["transaction_type"] == "debit"]
        if not debits.empty:
            cat_totals = debits.groupby("category")["amount"].sum().reset_index()
            cat_totals.columns = ["Category", "Amount (Rs.)"]
            cat_totals["Category"] = cat_totals["Category"].str.title()
            st.bar_chart(cat_totals.set_index("Category"))
        else:
            st.info("No debit transactions found.")
    else:
        st.info("No transaction data imported yet. Upload a statement via the sidebar.")

with col_right:
    st.subheader("Budget vs Actual Summary")
    if budgets:
        b_df = pd.DataFrame(budgets)
        b_df_display = b_df[["category", "weekly_target_amount", "actual_amount", "variance_rs", "is_overbudget"]].copy()
        b_df_display.columns = ["Category", "Target (Rs.)", "Actual (Rs.)", "Variance (Rs.)", "Overbudget?"]
        b_df_display["Category"] = b_df_display["Category"].str.title()
        st.dataframe(b_df_display, use_container_width=True)
    else:
        st.info("No budgets defined yet.")
