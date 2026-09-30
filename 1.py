import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DB_NAME = "expenses.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            expense_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# ADD EXPENSE
# --------------------------------------------------

def add_expense(amount, category, description, expense_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (amount, category, description, expense_date)
        VALUES (?, ?, ?, ?)
    """, (amount, category, description, expense_date))

    conn.commit()
    conn.close()


# --------------------------------------------------
# GET EXPENSES
# --------------------------------------------------

def get_expenses():
    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM expenses ORDER BY expense_date DESC",
        conn
    )

    conn.close()
    return df


# --------------------------------------------------
# DELETE EXPENSE
# --------------------------------------------------

def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    conn.commit()
    conn.close()


# --------------------------------------------------
# UPDATE EXPENSE
# --------------------------------------------------

def update_expense(expense_id, amount, category, description, expense_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE expenses
        SET amount = ?,
            category = ?,
            description = ?,
            expense_date = ?
        WHERE id = ?
    """, (
        amount,
        category,
        description,
        expense_date,
        expense_id
    ))

    conn.commit()
    conn.close()


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

create_table()

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Smart Expense Tracker")
st.write("Track, analyze and manage your daily expenses.")


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("⚙️ Settings")

monthly_budget = st.sidebar.number_input(
    "Monthly Budget (₹)",
    min_value=0.0,
    value=10000.0,
    step=500.0
)


# --------------------------------------------------
# ADD EXPENSE FORM
# --------------------------------------------------

st.subheader("➕ Add Expense")

with st.form("expense_form"):

    col1, col2 = st.columns(2)

    with col1:
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            step=10.0
        )

        category = st.selectbox(
            "Category",
            [
                "Food",
                "Transport",
                "Shopping",
                "Education",
                "Entertainment",
                "Bills",
                "Health",
                "Other"
            ]
        )

    with col2:
        description = st.text_input(
            "Description",
            placeholder="Example: Lunch"
        )

        expense_date = st.date_input(
            "Date",
            value=date.today()
        )

    submit = st.form_submit_button("Add Expense")

    if submit:

        if amount <= 0:
            st.error("Please enter an amount greater than ₹0.")

        else:
            add_expense(
                amount,
                category,
                description,
                expense_date.strftime("%Y-%m-%d")
            )

            st.success("Expense added successfully!")
            st.rerun()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = get_expenses()


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

st.divider()
st.subheader("📊 Dashboard")

if not df.empty:

    # Convert date
    df["expense_date"] = pd.to_datetime(df["expense_date"])

    # Current month
    current_month = date.today().strftime("%Y-%m")

    monthly_df = df[
        df["expense_date"].dt.strftime("%Y-%m") == current_month
    ]

    total_spent = monthly_df["amount"].sum()

    # Budget percentage
    if monthly_budget > 0:
        budget_percentage = (
            total_spent / monthly_budget
        ) * 100
    else:
        budget_percentage = 0

    # Dashboard cards
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💰 Total Spent",
        f"₹{total_spent:,.2f}"
    )

    col2.metric(
        "💳 Monthly Budget",
        f"₹{monthly_budget:,.2f}"
    )

    col3.metric(
        "📈 Budget Used",
        f"{budget_percentage:.1f}%"
    )

    col4.metric(
        "🧾 Number of Expenses",
        len(monthly_df)
    )

    # Budget warning
    if budget_percentage >= 100:

        st.error(
            "🚨 You have exceeded your monthly budget!"
        )

    elif budget_percentage >= 85:

        st.warning(
            f"⚠️ You've used {budget_percentage:.1f}% "
            "of your monthly budget."
        )

    else:

        st.success(
            f"✅ You have used {budget_percentage:.1f}% "
            "of your monthly budget."
        )


    # --------------------------------------------------
    # CATEGORY SUMMARY
    # --------------------------------------------------

    st.subheader("📂 Category-wise Spending")

    category_data = (
        monthly_df
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:

        st.dataframe(
            category_data,
            use_container_width=True,
            hide_index=True
        )

    with col2:

        if not category_data.empty:

            pie_chart = px.pie(
                category_data,
                values="amount",
                names="category",
                title="Spending by Category"
            )

            st.plotly_chart(
                pie_chart,
                use_container_width=True
            )


    # --------------------------------------------------
    # BAR CHART
    # --------------------------------------------------

    st.subheader("📊 Spending Analysis")

    bar_chart = px.bar(
        category_data,
        x="category",
        y="amount",
        title="Category-wise Spending",
        labels={
            "category": "Category",
            "amount": "Amount (₹)"
        }
    )

    st.plotly_chart(
        bar_chart,
        use_container_width=True
    )


    # --------------------------------------------------
    # EXPENSE SEARCH / FILTER
    # --------------------------------------------------

    st.subheader("🔎 Search & Filter")

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search description"
        )

    with col2:

        filter_category = st.selectbox(
            "Filter by category",
            ["All"] + sorted(df["category"].unique())
        )

    with col3:

        selected_month = st.selectbox(
            "Filter by month",
            ["All"] +
            sorted(
                df["expense_date"]
                .dt.strftime("%Y-%m")
                .unique(),
                reverse=True
            )
        )

    filtered_df = df.copy()

    # Search
    if search:

        filtered_df = filtered_df[
            filtered_df["description"]
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # Category filter
    if filter_category != "All":

        filtered_df = filtered_df[
            filtered_df["category"] == filter_category
        ]

    # Month filter
    if selected_month != "All":

        filtered_df = filtered_df[
            filtered_df["expense_date"]
            .dt.strftime("%Y-%m")
            == selected_month
        ]


    # --------------------------------------------------
    # DISPLAY EXPENSES
    # --------------------------------------------------

    st.subheader("📋 All Expenses")

    display_df = filtered_df.copy()

    display_df["expense_date"] = (
        display_df["expense_date"]
        .dt.strftime("%d/%m/%Y")
    )

    display_df["amount"] = (
        display_df["amount"]
        .apply(lambda x: f"₹{x:,.2f}")
    )

    display_df = display_df[
        [
            "id",
            "amount",
            "category",
            "description",
            "expense_date"
        ]
    ]

    display_df.columns = [
        "ID",
        "Amount",
        "Category",
        "Description",
        "Date"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------
    # EDIT EXPENSE
    # --------------------------------------------------

    st.subheader("✏️ Edit Expense")

    expense_ids = df["id"].tolist()

    selected_id = st.selectbox(
        "Select Expense ID",
        expense_ids
    )

    selected_expense = df[
        df["id"] == selected_id
    ].iloc[0]

    with st.form("edit_form"):

        edit_amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=float(selected_expense["amount"]),
            step=10.0
        )

        edit_category = st.selectbox(
            "Category",
            [
                "Food",
                "Transport",
                "Shopping",
                "Education",
                "Entertainment",
                "Bills",
                "Health",
                "Other"
            ],
            index=[
                "Food",
                "Transport",
                "Shopping",
                "Education",
                "Entertainment",
                "Bills",
                "Health",
                "Other"
            ].index(selected_expense["category"])
        )

        edit_description = st.text_input(
            "Description",
            value=selected_expense["description"]
        )

        edit_date = st.date_input(
            "Date",
            value=selected_expense["expense_date"].date()
        )

        update_button = st.form_submit_button(
            "Update Expense"
        )

        if update_button:

            update_expense(
                selected_id,
                edit_amount,
                edit_category,
                edit_description,
                edit_date.strftime("%Y-%m-%d")
            )

            st.success("Expense updated successfully!")
            st.rerun()


    # --------------------------------------------------
    # DELETE EXPENSE
    # --------------------------------------------------

    st.subheader("🗑️ Delete Expense")

    delete_id = st.selectbox(
        "Select Expense ID to Delete",
        df["id"].tolist(),
        key="delete"
    )

    if st.button("Delete Selected Expense"):

        delete_expense(delete_id)

        st.success("Expense deleted successfully!")
        st.rerun()


else:

    st.info(
        "No expenses recorded yet. "
        "Add your first expense above! 💰"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Smart Expense Tracker | Python + Streamlit + SQLite"
)