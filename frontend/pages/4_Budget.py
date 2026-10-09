"""
Budget Page: Editable Weekly Category Targets and Budget vs Actual Progress.
"""
import streamlit as st
import pandas as pd
from api_client import FinanceAPIClient

st.set_page_config(page_title="Budget Manager - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to access budget settings.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("🎯 Weekly Category Budgets")
st.caption("Manage target weekly spend per category and observe real-time variance in INR (Rs.)")

try:
    budgets = api.get_budgets()
except Exception as e:
    st.error(f"Error loading budget data: {e}")
    st.stop()

tab_view, tab_edit = st.tabs(["Budget vs Actual Tracking", "Edit Weekly Targets"])

with tab_view:
    if budgets:
        df = pd.DataFrame(budgets)
        
        for idx, row in df.iterrows():
            cat_title = row["category"].title()
            target = row["weekly_target_amount"]
            actual = row["actual_amount"]
            variance = row["variance_rs"]
            pct = row["variance_pct"]
            is_over = row["is_overbudget"]

            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.metric(
                    label=f"Category: {cat_title}",
                    value=f"Rs. {actual:,.2f}",
                    delta=f"Rs. {variance:+,.2f} ({pct:+.1f}%)",
                    delta_color="inverse" if is_over else "normal"
                )
            with col_b:
                progress = min(1.0, actual / target) if target > 0 else 0.0
                st.caption(f"Target: Rs. {target:,.2f} | Actual: Rs. {actual:,.2f}")
                st.progress(progress)
            st.markdown("---")
    else:
        st.info("No budgets configured yet.")

with tab_edit:
    st.subheader("Update Category Target Amounts")
    with st.form("budget_form"):
        new_targets = []
        for b in budgets:
            cat = b["category"]
            curr_target = b["weekly_target_amount"]
            val = st.number_input(f"Target for {cat.title()} (Rs.)", value=float(curr_target), min_value=0.0, step=100.0, key=f"inp_{cat}")
            new_targets.append({"category": cat, "weekly_target_amount": val})
        
        if st.form_submit_button("Save Target Budgets"):
            try:
                api.update_budgets(new_targets)
                st.success("Successfully updated weekly target budgets!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save targets: {e}")
