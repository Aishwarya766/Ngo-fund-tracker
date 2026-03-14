from __future__ import annotations

import os
from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
import requests
import streamlit as st


BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
REQ_TIMEOUT = 10


def api_get(path: str) -> Any:
    headers = {"Authorization": "Bearer demo_token_123"}
    resp = requests.get(f"{BACKEND_URL}{path}", headers=headers, timeout=REQ_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, payload: dict[str, Any]) -> Any:
    headers = {"Authorization": "Bearer demo_token_123"}
    resp = requests.post(f"{BACKEND_URL}{path}", json=payload, headers=headers, timeout=REQ_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def money(x: float) -> str:
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)


def download_csv(df: pd.DataFrame, filename: str, label: str) -> None:
    data = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=data, file_name=filename, mime="text/csv")


def dashboard_page() -> None:
    st.title("NGO Fund Tracker — Dashboard")

    try:
        dash = api_get("/dashboard")
        donations = api_get("/donations")
        expenses = api_get("/expenses")
        projects = api_get("/projects")
    except requests.RequestException as e:
        st.error(f"Backend not reachable at {BACKEND_URL}. Error: {e}")
        st.info("Start the API first: `uvicorn backend.main:app --reload` from the project root.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Donations", money(dash["total_donations"]))
    c2.metric("Total Expenses", money(dash["total_expenses"]))
    c3.metric("Remaining Balance", money(dash["remaining_balance"]))
    c4.metric("Total Donors", int(dash["total_donors"]))

    st.divider()

    donations_df = pd.DataFrame(donations)
    expenses_df = pd.DataFrame(expenses)
    projects_df = pd.DataFrame(projects)

    if not donations_df.empty:
        donations_df["date"] = pd.to_datetime(donations_df["date"], errors="coerce")
        trend = (
            donations_df.dropna(subset=["date"])
            .set_index("date")
            .resample("D")["amount"]
            .sum()
            .sort_index()
        )
        st.subheader("Donation Trend")
        st.line_chart(trend)
    else:
        st.subheader("Donation Trend")
        st.caption("No donations yet.")

    st.subheader("Expense Breakdown (by Project)")
    if not expenses_df.empty:
        breakdown = expenses_df.groupby("project_name", as_index=True)["amount"].sum().sort_values(ascending=False)
        st.bar_chart(breakdown)
    else:
        st.caption("No expenses yet.")

    st.subheader("Project Spending")
    if not projects_df.empty:
        chart_df = projects_df[["name", "allocated_budget", "total_spent", "remaining_budget"]].set_index("name")
        st.bar_chart(chart_df[["allocated_budget", "total_spent"]])
        over = projects_df[projects_df["remaining_budget"] < 0]
        if not over.empty:
            st.warning("Some projects have exceeded budget.")
            st.dataframe(over[["name", "allocated_budget", "total_spent", "remaining_budget"]], use_container_width=True)
    else:
        st.caption("No projects yet.")

    st.divider()
    st.subheader("Exports")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if not donations_df.empty:
            download_csv(donations_df, "donations.csv", "Download donations CSV")
    with col_b:
        if not expenses_df.empty:
            download_csv(expenses_df, "expenses.csv", "Download expenses CSV")
    with col_c:
        if not projects_df.empty:
            download_csv(projects_df, "projects.csv", "Download projects CSV")


def add_donation_page() -> None:
    st.title("Add Donation")

    try:
        donors = api_get("/donors")
    except requests.RequestException as e:
        st.error(f"Backend not reachable at {BACKEND_URL}. Error: {e}")
        return

    with st.form("donation_form", clear_on_submit=True):
        st.subheader("Donor")
        mode = st.radio("Donor mode", ["Existing donor", "New donor"], horizontal=True)

        donor_id = None
        if mode == "Existing donor":
            if not donors:
                st.info("No donors yet. Switch to 'New donor' to create one.")
            else:
                options = {f'{d["name"]} (id={d["id"]})': d["id"] for d in donors}
                donor_label = st.selectbox("Select donor", list(options.keys()),key="donor_select")
                donor_id = options[donor_label]
        else:
            donor_name = st.text_input("Donor name", value="")
            donor_email = st.text_input("Email (optional)", value="")
            donor_phone = st.text_input("Phone (optional)", value="")

        st.subheader("Donation")
        amount = st.number_input("Amount", min_value=0.0, step=100.0, value=0.0)
        donation_type = st.selectbox("Donation type", ["general", "education", "medical", "food", "other"])
        notes = st.text_area("Notes (optional)", value="")
        include_date = st.checkbox("Set donation date/time", value=False)
        donation_dt = st.date_input("Date", value=datetime.now().date(), disabled=not include_date)
        donation_tm = st.time_input("Time", value=datetime.now().time().replace(microsecond=0), disabled=not include_date)

        submitted = st.form_submit_button("Submit donation")

    if not submitted:
        return

    try:
        if mode == "New donor":
            if not donor_name.strip():
                st.error("Donor name is required.")
                return
            donor_payload = {
                "name": donor_name.strip(),
                "email": donor_email.strip() or None,
                "phone": donor_phone.strip() or None,
            }
            donor = api_post("/donor", donor_payload)
            donor_id = donor["id"]

        if donor_id is None:
            st.error("Please select or create a donor.")
            return

        payload: dict[str, Any] = {
            "donor_id": int(donor_id),
            "amount": float(amount),
            "type": donation_type,
            "notes": notes.strip() or None,
        }
        if include_date:
            dt = datetime.combine(donation_dt, donation_tm)
            payload["date"] = dt.isoformat()

        donation = api_post("/donation", payload)
        st.success(f'Donation recorded (id={donation["id"]}) for donor: {donation["donor_name"]}')
        st.rerun()
    except requests.HTTPError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            pass
        st.error(f"Failed: {detail or str(e)}")
    except requests.RequestException as e:
        st.error(f"Failed: {e}")


def add_expense_page() -> None:
    st.title("Add Expense")

    try:
        projects = api_get("/projects")
    except requests.RequestException as e:
        st.error(f"Backend not reachable at {BACKEND_URL}. Error: {e}")
        return

    if not projects:
        st.info("No projects yet. Create one below first.")

    with st.expander("Create a project", expanded=not bool(projects)):
        with st.form("project_form", clear_on_submit=True):
            name = st.text_input("Project name", value="")
            description = st.text_area("Description (optional)", value="")
            allocated_budget = st.number_input("Allocated budget", min_value=0.0, step=1000.0, value=0.0)
            create_project = st.form_submit_button("Create project")
        if create_project:
            try:
                proj = api_post(
                    "/project",
                    {
                        "name": name.strip(),
                        "description": description.strip() or None,
                        "allocated_budget": float(allocated_budget),
                    },
                )
                st.success(f'Project created (id={proj["id"]})')
            except requests.HTTPError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", "")
                except Exception:
                    pass
                st.error(f"Failed: {detail or str(e)}")
            except requests.RequestException as e:
                st.error(f"Failed: {e}")

    try:
        projects = api_get("/projects")
    except requests.RequestException:
        projects = []

    with st.form("expense_form", clear_on_submit=True):
        if projects:
            options = {f'{p["name"]} (id={p["id"]})': p["id"] for p in projects}
            project_label = st.selectbox("Project", list(options.keys()))
            project_id = options[project_label]
        else:
            project_id = None
            st.warning("Create a project to record expenses.")

        amount = st.number_input("Amount", min_value=0.0, step=100.0, value=0.0)
        description = st.text_input("Description", value="")
        include_date = st.checkbox("Set expense date/time", value=False)
        expense_dt = st.date_input("Date", value=datetime.now().date(), disabled=not include_date, key="exp_date")
        expense_tm = st.time_input(
            "Time", value=datetime.now().time().replace(microsecond=0), disabled=not include_date, key="exp_time"
        )
        submitted = st.form_submit_button("Submit expense")

    if not submitted:
        return
    if project_id is None:
        st.error("Project is required.")
        return
    if not description.strip():
        st.error("Description is required.")
        return

    payload: dict[str, Any] = {
        "project_id": int(project_id),
        "amount": float(amount),
        "description": description.strip(),
    }
    if include_date:
        dt = datetime.combine(expense_dt, expense_tm)
        payload["date"] = dt.isoformat()

    try:
        expense = api_post("/expense", payload)
        st.success(f'Expense recorded (id={expense["id"]}) for project: {expense["project_name"]}')
    except requests.HTTPError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            pass
        st.error(f"Failed: {detail or str(e)}")
    except requests.RequestException as e:
        st.error(f"Failed: {e}")


def projects_page() -> None:
    st.title("Projects")
    try:
        projects = api_get("/projects")
    except requests.RequestException as e:
        st.error(f"Backend not reachable at {BACKEND_URL}. Error: {e}")
        return

    df = pd.DataFrame(projects)
    if df.empty:
        st.info("No projects yet.")
        return

    df = df.rename(
        columns={
            "name": "Project Name",
            "allocated_budget": "Allocated Budget",
            "total_spent": "Total Spent",
            "remaining_budget": "Remaining Budget",
        }
    )
    st.dataframe(
        df[["Project Name", "Allocated Budget", "Total Spent", "Remaining Budget"]],
        use_container_width=True,
    )
    download_csv(df, "projects.csv", "Download projects CSV")


def donors_page() -> None:
    st.title("Donors")
    try:
        donors = api_get("/donors")
        donations = api_get("/donations")
    except requests.RequestException as e:
        st.error(f"Backend not reachable at {BACKEND_URL}. Error: {e}")
        return

    donors_df = pd.DataFrame(donors)
    donations_df = pd.DataFrame(donations)
    if donors_df.empty:
        st.info("No donors yet.")
        return

    if not donations_df.empty:
        totals = donations_df.groupby("donor_id", as_index=False)["amount"].sum().rename(columns={"amount": "Total Donations"})
        donors_df = donors_df.merge(totals, left_on="id", right_on="donor_id", how="left").drop(columns=["donor_id"])
    donors_df["Total Donations"] = donors_df.get("Total Donations", 0).fillna(0.0)

    donors_df = donors_df.rename(columns={"name": "Donor Name", "email": "Email", "phone": "Phone"})
    st.dataframe(donors_df[["Donor Name", "Email", "Phone", "Total Donations"]], use_container_width=True)
    download_csv(donors_df, "donors.csv", "Download donors CSV")


st.set_page_config(page_title="NGO Fund Tracker", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Page", ["Dashboard", "Add Donation", "Add Expense", "Projects", "Donors"])
st.sidebar.caption(f"Backend: {BACKEND_URL}")

if page == "Dashboard":
    dashboard_page()
elif page == "Add Donation":
    add_donation_page()
elif page == "Add Expense":
    add_expense_page()
elif page == "Projects":
    projects_page()
elif page == "Donors":
    donors_page()

