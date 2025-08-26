import streamlit as st
import requests
from add_update_tab import add_update_ui
from analtyics_ui import analytics_tab

API_URL = "http://127.0.0.1:8001"

st.set_page_config(page_title="Expense Manager", layout="centered")
st.title("💰 Expense Manager")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.username = ""
    st.session_state.role = None

def login_ui():
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.warning("Please enter username and password.")
            return

        response = requests.post(
            f"{API_URL}/login",
            data={"username": username, "password": password}
        )

        if response.status_code == 200:
            result = response.json()
            st.success("Login successful.")
            st.session_state.token = result["access_token"]
            st.session_state.username = username
            st.session_state.role = result["role"]
            st.rerun()
        else:
            st.error("Invalid credentials.")

def admin_ui():
    tab1, tab2, tab3 = st.tabs(["➕ Add User", "📊 Analytics", "📁 View User Expenses"])

    with tab1:
        st.subheader("Create New User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        new_role = st.selectbox("Select Role", ["user", "admin"])
        if st.button("Create User"):
            if new_user and new_pass:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                payload = {"username": new_user, "password": new_pass, "role": new_role}
                res = requests.post(f"{API_URL}/admin/create_user", json=payload, headers=headers)
                if res.status_code == 200:
                    st.success("User created successfully.")
                else:
                    st.error(res.json().get("detail", "Error creating user"))
            else:
                st.warning("Username and password required.")

    with tab2:
        analytics_tab()

    with tab3:
        st.subheader("View User Expenses")
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        users = requests.get(f"{API_URL}/admin/all_users", headers=headers)
        if users.status_code == 200:
            usernames = users.json()
            selected_user = st.selectbox("Select User", usernames)
            date_selected = st.date_input("Expense Date")

            if st.button("Fetch Expenses"):
                res = requests.get(f"{API_URL}/admin/user_expenses/{selected_user}/{date_selected}", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        st.write(f"Expenses for {selected_user} on {date_selected}:")
                        import pandas as pd
                        df = pd.DataFrame(data)
                        st.table(df)
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button("📥 Download CSV", data=csv, file_name="user_expenses.csv", mime="text/csv")
                    else:
                        st.info("No expenses found.")
                else:
                    st.error(res.json().get("detail", "Error fetching expenses."))

def user_ui():
    tab1, tab2 = st.tabs(["📝 Add/Update", "📈 Analytics"])
    with tab1:
        add_update_ui()
    with tab2:
        analytics_tab()

if not st.session_state.token:
    login_ui()
else:
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.token = None
        st.session_state.username = ""
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == "admin":
        admin_ui()
    else:
        user_ui()
