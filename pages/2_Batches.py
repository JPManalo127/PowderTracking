import streamlit as st
from database import Session, Batch, Dispenser, DispenserLayer

session = Session()

st.title("Powder Inventory")

batches = session.query(Batch).all()

with st.expander("+ Add New Batch"):

    with st.form("add_batch"):

        batch_number = st.text_input("Batch Number")
        grade = st.selectbox(
            "Grade",
            ["BOH L718AMS","BOH L718 API","BOH L175","HOG Ti64 G5","HOG Ti64 G2-3","BOH W722"])
        condition = st.selectbox(
            "Condition",
            ["Virgin","Sieved","Not Sieved"]
            )
        kg = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            step=0.1,
            value=0.0
        )
        location = st.text_input("Location")

        submitted = st.form_submit_button("Add Batch")

        if submitted:

            batch = Batch(
                batch_number=batch_number,
                grade=grade,
                condition=condition,
                kg=kg,
                location=location
            )

            session.add(batch)
            session.commit()

            st.success("Batch added.")

st.divider()

st.header("Current Inventory")
show_archived = st.checkbox(
    "Show Archived Batches",
    value=False
    )
if show_archived:
    batches = session.query(Batch).all()
else:
    batches = session.query(Batch).filter_by(
        status="ACTIVE"
        ).all()
from collections import defaultdict
grades = defaultdict(list)
for batch in batches:
    grades[batch.grade].append(batch)
for grade_name, grade_batches in grades.items():
    grade_total=sum(
        batch.kg
        for batch in grade_batches)
    st.write(
        f"**{grade_name}**:"
        f"{grade_total:.2f} kg")
st.divider()
for grade_name, grade_batches in grades.items():
    grade_total=sum(
        batch.kg
        for batch in grade_batches)
    with st.expander(f"{grade_name} ({grade_total:.2f} kg)"):
        virgin_total=sum(
            batch.kg
            for batch in grade_batches
            if batch.condition == "Virgin")
        sieved_total=sum(
            batch.kg
            for batch in grade_batches
            if batch.condition == "Sieved")
        not_sieved_total=sum(
            batch.kg
            for batch in grade_batches
            if batch.condition == "Not Sieved")
        st.write(f"Virgin Powder: {virgin_total:.2f} kg")
        st.write(f"Sieved Powder: {sieved_total:.2f} kg")
        st.write(f"Not Sieved Powder: {not_sieved_total:.2f} kg")
        st.divider()
        for batch in grade_batches:
            with st.expander(f"{batch.batch_number} | {batch.condition} | {batch.kg:.2f} kg"):
                st.write(f"Grade: {batch.grade}")
                st.write(f"Condition: {batch.condition}")
                st.write(f"Quantity: {batch.kg} kg")
                st.write(f"Location: {batch.location}")
                st.divider()
                with st.expander("Edit Batch"):
                    with st.form(f"edit_batch_{batch.id}"):
                        grade = st.text_input(
                            "Grade",
                            value=batch.grade or "")
                        condition = st.selectbox(
                            "Condition",
                            ["Virgin","Sieved","Not Sieved"],
                            index=[
                                "Virgin",
                                "Sieved",
                                "Not Sieved"
                            ].index(batch.condition)
                            if batch.condition in [
                                "Virgin",
                                "Sieved",
                                "Not Sieved"
                            ]
                            else 0)
                        kg = st.number_input(
                            "Weight (kg)",
                            min_value=0.0,
                            value=float(batch.kg or 0.0))
                        location = st.text_input(
                            "Location",
                            value=batch.location or "")
                        save = st.form_submit_button("Save Changes")
                        if save:

                            batch.grade = grade
                            batch.condition = condition
                            batch.kg = kg
                            batch.location = location
                            session.commit()
                            st.success("Batch updated.")
                    st.divider()
                    archive=st.button(
                        "Archive Batch",
                        key=f"archive_{batch.id}"
                        )
                    if archive:
                        batch.status = "ARCHIVED"
                        session.commit()
                        st.success(
                            f"{batch.batch_number} archived."
                            )
                        st.rerun()
                    st.divider()
                    with st.expander("Delete Batch"):
                        confirm = st.checkbox("I understand this cannot be undone.",
                            key=f"confirm_delete_{batch.id}"
                            )
                        delete=st.button("Delete Batch",
                            key=f"delete_{batch.id}"
                            )
                        if delete and confirm:
                            existing_layers = session.query(
                                DispenserLayer
                                 ).filter_by(
                                    batch_number=batch.batch_number
                                    ).count()
                            if existing_layers>0:
                                    st.error("Cannot delete batch because it exists in a dispenser.")
                            else:
                                session.delete(batch)
                                session.commit()
                                st.success("Batch deleted.")
                                st.rerun()

