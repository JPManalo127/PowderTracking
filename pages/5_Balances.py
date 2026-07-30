import streamlit as st
import pandas as pd
from database import Session, PowderTransaction

st.title("Monthly Balances")

session = Session()

transactions=session.query(PowderTransaction).all()
df=pd.DataFrame([
    {
        "date":t.transaction_date,
        "grade":t.grade,
        "heat_no":t.heat_no,
        "condition":t.condition,
        "amount":t.amount,
        "reason":t.transaction_type
        }
    for t in transactions
    ])
if df.empty:
    st.warning("No transactions found.")
    st.stop()
df["date"]=pd.to_datetime(df["date"])
df["year"]=df["date"].dt.year
df["month"]=df["date"].dt.month
years=sorted(df["year"].unique())
selected_year=st.selectbox(
    "Year",
    years,
    index=len(years)-1)
df=df[
    df["year"] == selected_year]
monthly_balance = (
    df.groupby(
        ["grade", "month"]
    )["amount"]
    .sum()
    .unstack(fill_value=0))
monthly_balance=monthly_balance.reindex(
    columns=range(1,13),
    fill_value=0)
monthly_balance = monthly_balance.cumsum(axis=1)
current_month=pd.Timestamp.today().month
for month in range(current_month + 1, 13):
    if month in monthly_balance.columns:
        monthly_balance[month]=None

month_names = {
    1:"Jan",
    2:"Feb",
    3:"Mar",
    4:"Apr",
    5:"May",
    6:"Jun",
    7:"Jul",
    8:"Aug",
    9:"Sep",
    10:"Oct",
    11:"Nov",
    12:"Dec"
}

monthly_balance.rename(
    columns=month_names,
    inplace=True
)

st.subheader("Monthly Powder Balances")

st.dataframe(
    monthly_balance,
    use_container_width=True
)
st.divider()
virgin_df = df[df["condition"] == "Virgin"]
grades = sorted(virgin_df["grade"].unique())
st.subheader("Virgin Powder")
for grade in grades:
    grade_df = virgin_df[
    virgin_df["grade"] == grade]
    grade_total=(
        grade_df
        .groupby("month")["amount"]
        .sum()
        .reindex(range(1,13), fill_value=0)
        .cumsum())
    current_month=pd.Timestamp.today().month
    for month in range(current_month+1,13):
        grade_total.loc[month]=None
    with st.expander(f"{grade}"):
        total_df=pd.DataFrame(
            [grade_total.values],
            columns=[
                month_names[m]
                for m in grade_total.index])
        st.write("Grade Total")
        st.dataframe(
            total_df,
            hide_index=True,
            use_container_width=True)
        heat_pivot=(
            grade_df.groupby(
                ["heat_no","month"]
                )["amount"]
            .sum()
            .unstack(fill_value=0))
        heat_pivot=heat_pivot.reindex(
            columns=range(1,13),
            fill_value=0)
        heat_pivot=heat_pivot.cumsum(axis=1)
        current_month=pd.Timestamp.today().month
        for month in range(current_month+1,13):
            if month in heat_pivot.columns:
                heat_pivot[month]=None
        heat_pivot.rename(
            columns=month_names,
            inplace=True)
        st.dataframe(
            heat_pivot,
            use_container_width=True)
    
