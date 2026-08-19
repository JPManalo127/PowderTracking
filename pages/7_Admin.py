import streamlit as st
import os
import shutil
import pandas as pd

from io import BytesIO
from datetime import datetime

from database import (
    Session,
    Batch,
    Dispenser,
    DispenserLayer,
    Build,
    BuildConsumption,
    BatchComponent,
    MonthlyBalance,
    PowderTransaction,
    Sieve,
    SieveRun,
)

# ====================================================
# PAGE CONFIG
# ====================================================

st.set_page_config(
    page_title="Admin",
    layout="wide")

DB_FILE = "powder_tracker.db"
BACKUP_DIR = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

session = Session()

password = st.text_input(
    "Admin Password",
    type="password"
)

if password != st.secrets["ADMIN_PASSWORD"]:
    st.stop()

st.title("Admin Tools")

st.header("Database Information")

if os.path.exists(DB_FILE):

    size_mb = os.path.getsize(DB_FILE) / (1024 * 1024)

    modified = datetime.fromtimestamp(
        os.path.getmtime(DB_FILE))

    st.write(f"**Database:** {DB_FILE}")
    st.write(f"**Size:** {size_mb:.2f} MB")
    st.write(f"**Last Modified:** {modified}")

else:

    st.error("Database file not found.")

st.divider()
st.header("Table Counts")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Batches",
        session.query(Batch).count())
    st.metric(
        "Dispensers",
        session.query(Dispenser).count())
    st.metric(
        "Dispenser Layers",
        session.query(DispenserLayer).count())
with col2:
    st.metric(
        "Builds",
        session.query(Build).count())
    st.metric(
        "Build Consumption",
        session.query(BuildConsumption).count())
    st.metric(
        "Batch Components",
        session.query(BatchComponent).count())
with col3:
    st.metric(
        "Transactions",
        session.query(PowderTransaction).count())
    st.metric(
        "Sieves",
        session.query(Sieve).count())
    st.metric(
        "Sieve Runs",
        session.query(SieveRun).count())
st.divider()
st.header("Database Backups")
if st.button("Create Backup"):
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S")
    backup_file = os.path.join(
        BACKUP_DIR,
        f"powder_tracker_{timestamp}.db")
    shutil.copy2(
        DB_FILE,
        backup_file)
    st.success(
        f"Backup created:\n{backup_file}")
backup_files = sorted(
    [
        file
        for file in os.listdir(BACKUP_DIR)
        if file.endswith(".db")
    ],
    reverse=True
)
if backup_files:
    selected_backup = st.selectbox(
        "Available Backups",
        backup_files)
    selected_backup_path = os.path.join(
        BACKUP_DIR,
        selected_backup)
    with open(selected_backup_path, "rb") as f:
        st.download_button(
            "Download Selected Backup",
            data=f,
            file_name=selected_backup,
            mime="application/octet-stream")
else:
    st.info("No backups available.")
st.divider()
st.header("Database Restore")
uploaded_file = st.file_uploader(
    "Upload Backup Database",
    type=["db"])
if uploaded_file is not None:
    if st.button("Restore Uploaded Backup"):
        restore_backup = os.path.join(
            BACKUP_DIR,
            f"pre_restore_"
            f"{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(
            DB_FILE,
            restore_backup)

        with open(DB_FILE, "wb") as f:
            f.write(
                uploaded_file.getbuffer())
        st.success("Database restored successfully.")

        st.info(
            f"Current database was backed up as:\n"
            f"{restore_backup}"
        )

st.divider()
st.header("Reports and Exporting")
table_name = st.selectbox(
    "Select Table",
    [
        "Transactions",
        "Batches",
        "Dispensers",
        "Dispenser Layers",
        "Builds",
        "Build Consumption",
        "Batch Components",
        "Monthly Balances",
        "Sieves",
        "Sieve Runs"
    ]
)
table_mapping = {
    "Transactions": PowderTransaction,
    "Batches": Batch,
    "Dispensers": Dispenser,
    "Dispenser Layers": DispenserLayer,
    "Builds": Build,
    "Build Consumption": BuildConsumption,
    "Batch Components": BatchComponent,
    "Monthly Balances": MonthlyBalance,
    "Sieves": Sieve,
    "Sieve Runs": SieveRun,
}
model = table_mapping[table_name]
records = session.query(model).all()
df = pd.DataFrame([
    row.__dict__
    for row in records
])
if not df.empty:
    if "_sa_instance_state" in df.columns:
        df.drop(
            columns=["_sa_instance_state"],
            inplace=True)

    st.subheader("Preview")
    st.dataframe(
        df,
        use_container_width=True)

    csv = df.to_csv(
        index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{table_name}.csv",
        mime="text/csv")
    excel_buffer = BytesIO()
    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            sheet_name=table_name,
            index=False
        )
    st.download_button(
        label="Download Excel",
        data=excel_buffer.getvalue(),
        file_name=f"{table_name}.xlsx",
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )
else:
    st.info(f"No records found in {table_name}.")
st.divider()
st.header("Transaction Report Generator")

transaction_start = st.date_input(
    "Start Date",
    key="report_transaction_start"
)

transaction_end = st.date_input(
    "End Date",
    key="report_transaction_end"
)

transaction_types = (
    session.query(
        PowderTransaction.transaction_type
    )
    .distinct()
    .all()
)

transaction_type_options = [
    row[0]
    for row in transaction_types
    if row[0]
]

selected_type = st.selectbox(
    "Transaction Type",
    ["All"] + sorted(transaction_type_options)
)

grades = (
    session.query(
        PowderTransaction.grade
    )
    .distinct()
    .all()
)

grade_options = [
    row[0]
    for row in grades
    if row[0]
]

selected_grade = st.selectbox(
    "Grade",
    ["All"] + sorted(grade_options)
)

query = session.query(
    PowderTransaction
)

query = query.filter(
    PowderTransaction.transaction_date >= transaction_start
)

query = query.filter(
    PowderTransaction.transaction_date <= transaction_end
)

if selected_type != "All":
    query = query.filter(
        PowderTransaction.transaction_type == selected_type
    )

if selected_grade != "All":
    query = query.filter(
        PowderTransaction.grade == selected_grade
    )

report_records = query.all()

report_df = pd.DataFrame(
    [
        record.__dict__
        for record in report_records
    ]
)

if not report_df.empty:

    if "_sa_instance_state" in report_df.columns:
        report_df.drop(
            columns=["_sa_instance_state"],
            inplace=True
        )

    st.subheader("Report Preview")

    st.dataframe(
        report_df,
        use_container_width=True
    )

    st.subheader("Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Transactions",
            len(report_df)
        )

    with col2:
        st.metric(
            "Total Amount",
            f"{report_df['amount'].sum():,.2f}"
        )

    with col3:
        st.metric(
            "Grades",
            report_df["grade"].nunique()
        )

    report_csv = report_df.to_csv(
        index=False
    )

    st.download_button(
        "Download Report CSV",
        report_csv,
        file_name=(
            f"transactions_"
            f"{transaction_start}_"
            f"{transaction_end}.csv"
        )
    )

    report_excel = BytesIO()

    with pd.ExcelWriter(
        report_excel,
        engine="openpyxl"
    ) as writer:

        report_df.to_excel(
            writer,
            sheet_name="Transactions",
            index=False
        )

    st.download_button(
        "Download Report Excel",
        report_excel.getvalue(),
        file_name=(
            f"transactions_"
            f"{transaction_start}_"
            f"{transaction_end}.xlsx"
        ),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("Transaction Breakdown")

    breakdown = (
        report_df.groupby(
            "transaction_type"
        )["amount"]
        .sum()
        .reset_index()
    )

    st.dataframe(
        breakdown,
        use_container_width=True
    )

else:
    st.info(
        "No transactions found for selected criteria."
    )
session.close()
