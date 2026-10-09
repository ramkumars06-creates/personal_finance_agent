"""
Transactions Page: Search, Filter, and Category Correction.
"""
import streamlit as st
import pandas as pd
from api_client import FinanceAPIClient

st.set_page_config(page_title="Transactions - Personal Finance Agent", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please log in on the main home page to access your transactions.")
    st.stop()

api = FinanceAPIClient()
api.set_token(st.session_state.token)

st.title("💳 Transactions Ledger")
st.caption("Filter, search, and correct merchant categories with automatic per-user rule learning")

categories = ["all", "food", "groceries", "transport", "bills", "rent", "shopping", "entertainment", "health", "education", "other"]

col_filter1, col_filter2 = st.columns([1, 2])
with col_filter1:
    selected_cat = st.selectbox("Filter Category", categories)
with col_filter2:
    search_query = st.text_input("Search Description or Merchant", "")

try:
    cat_param = None if selected_cat == "all" else selected_cat
    search_param = search_query if search_query.strip() else None
    txns = api.get_transactions(category=cat_param, search=search_param)
except Exception as e:
    st.error(f"Error loading transactions: {e}")
    st.stop()

if not txns:
    st.info("No matching transactions found.")
else:
    df = pd.DataFrame(txns)
    st.write(f"Showing **{len(df)}** transactions:")

    for idx, row in df.iterrows():
        with st.expander(f"{row['transaction_date']} | {row['normalized_merchant']} | Rs. {row['amount']:,.2f} ({row['category'].title()})"):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Description:** {row['description']}")
            c2.write(f"**Categorization Method:** `{row['categorization_method']}` (Confidence: {row['category_confidence']:.2f})")
            c3.write(f"**Type:** `{row['transaction_type'].upper()}`")

            # Category correction form
            st.markdown("#### Correct Category")
            col_sel, col_btn = st.columns([2, 1])
            with col_sel:
                new_cat = st.selectbox(
                    "Assign New Category",
                    [c for c in categories if c != "all"],
                    key=f"sel_{row['id']}"
                )
            with col_btn:
                st.write("")
                st.write("")
                if st.button("Update & Set Rule", key=f"btn_{row['id']}"):
                    try:
                        api.update_transaction_category(row["id"], new_cat)
                        st.success(f"Updated category to {new_cat.title()} and created auto-rule for {row['normalized_merchant']}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update category: {e}")
