import streamlit as st
from datetime import datetime
import requests
import pandas as pd


API_URL = "http://127.0.0.1:8001"


def analytics_tab():
    st.title("💰 Expense Analytics")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", datetime(2024, 8, 1))

    with col2:
        end_date = st.date_input("End Date", datetime(2024, 8, 5))

    if st.button("Get Analytics"):
        payload = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }

        response = requests.post(f"{API_URL}/analytics/", json=payload)
        analytics = response.json()

        if not isinstance(analytics, dict) or not analytics:
            st.warning("No data available for the selected date range.")
            return

        data = {
            "Category": list(analytics.keys()),
            "Total": [analytics[cat]["total"] for cat in analytics],
            "Percentage": [analytics[cat]["percentage"] for cat in analytics],
        }

        df = pd.DataFrame(data)
        df_sorted = df.sort_values(by="Percentage", ascending=False)

        st.title("Expense Breakdown By Category")

        st.bar_chart(data=df_sorted.set_index("Category")['Percentage'], width=0, height=0, use_container_width=True)

        df_sorted["Total"] = df_sorted["Total"].map("{:.2f}".format)
        df_sorted["Percentage"] = df_sorted["Percentage"].map("{:.2f}".format)

        st.table(df_sorted)
