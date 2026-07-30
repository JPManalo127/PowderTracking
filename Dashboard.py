import streamlit as st
import pandas as pd
from database import Session, Batch, PowderTransaction

st.set_page_config(
    page_title="Powder Tracking",
    layout="wide"
)
st.title("Dashboard")
session = Session()
batches=(
    session.query(Batch)
    .filter(Batch.status =="ACTIVE")
    .all())
df=pd.DataFrame([
    {
        "grade":b.grade,
        "kg":b.kg
        }
    for b in batches
    ])
grade_totals=(
    df.groupby("grade")["kg"]
    .sum()
    .sort_values(ascending=False))
st.header("Inventory by grade")
cols=st.columns(3)
for i, (grade, total) in enumerate(grade_totals.items()):
    with cols[i % 3]:
        st.metric(
            grade,
            f"{total:,.1f} kg")
st.divider()
low_limit=300
low_inventory=(
    session.query(Batch)
    .filter(
        Batch.status == "ACTIVE"
        ).all()
    )
grade_inventory=(
    df.groupby("grade")["kg"]
    .sum()
    .reset_index())
low_inventory=grade_inventory[
    grade_inventory["kg"]<low_limit]
st.header("Low Inventory")
if not low_inventory.empty:
    for _, row in low_inventory.iterrows():
        st.warning(
            f"{row['grade']} -"
            f"{row['kg']:,.1f} kg")
else:
    st.success("No low inventory.")
st.divider()
chart_df=(
    df.groupby("grade")["kg"]
    .sum()
    .reset_index())
st.header("Inventory by Grade Chart")
st.bar_chart(
    chart_df.set_index("grade"))
st.divider()
recent=(
    session.query(PowderTransaction)
    .order_by(
        PowderTransaction.id.desc())
    .limit(10)
    .all())
st.header("Recent Activity")
for t in recent:
    st.write(
        f"{t.transaction_date} | "
        f"{t.heat_no} | "
        f"{t.amount:+.1f} kg | "
        f"{t.transaction_type}")
