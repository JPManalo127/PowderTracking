import streamlit as st
from database import (Session, Batch, BatchComponent)

session = Session()

st.header("Geneology")

search_text=st.text_input(
    "Search Batch Number")

col1, col2 = st.columns(2)
with col1:
    grades=sorted(
        set(
            batch.grade
            for batch in session.query(Batch).all()
            )
        )
    selected_grade=st.selectbox(
        "Grade",
        ["All"] + grades)
with col2:
    show_archived=st.checkbox(
        "Show Archived",
        value=False)
query=session.query(Batch).filter(
    Batch.batch_number.like("RB%")
if not show_archived:
    query=query.filter_by(
        status="ACTIVE")
if selected_grade !="All":
    query=query.filter_by(
        grade=selected_grade)
if search_text:
    query=query.filter(
        Batch.batch_number.contains(
            search_text)
        )
batches=query.order_by(
    Batch.batch_number.desc()
    ).all()
st.divider()
for batch in batches:
    with st.expander(f"{batch.grade} | {batch.batch_number}"):
        st.write(f"Grade: {batch.grade}")
        st.write(f"Weight: {batch.kg:.2f} kg")
        st.write("Composition:")
        components=session.query(
            BatchComponent
            ).filter_by(
                parent_batch=batch.batch_number
                ).all()
        if not components:
            st.info("No composition records found.")
        else:
            for component in components:
                st.write(
                    f"{component.component_batch}: "
                    f"{component.kg:.2f} kg")

            
