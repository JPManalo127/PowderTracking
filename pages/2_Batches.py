import streamlit as st
from database import Session, Batch, Dispenser, DispenserLayer, PowderTransaction
from datetime import date

session = Session()

st.title("Powder Inventory")

batches = session.query(Batch).all()
customers=["Baker","Canada"]
with st.expander("+ Add New Batch"):
    with st.form("add_batch"):
        batch_number = st.text_input("Batch Number")
        grade = st.selectbox(
            "Grade",
            ["BOH L718 AMS","BOH L718 API","BOH L175","HOG Ti64 G5","HOG Ti64 G2-3","BOH W722", "316L"])
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
        location = st.selectbox("Location",
                                ["Powder Storage","Outside Lab","Inside Lab"])
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
            transaction=PowderTransaction(
                transaction_date=date.today(),
                grade=grade,
                heat_no=batch_number,
                condition=condition,
                amount=kg,
                transaction_type="Powder Received"
                )
            session.add(transaction)
            session.commit()
            st.success("Batch added.")
with st.expander("Ship Batch"):
    active_batches=(
        session.query(Batch)
        .filter_by(status="ACTIVE")
        .all())
    batch_options={
        f"{b.batch_number} | {b.grade} | {b.kg:.2f} kg": b
        for b in active_batches}
    selected_batch_label=st.selectbox(
        "Select Batch",
        batch_options.keys())
    selected_batch=batch_options[selected_batch_label]
    customer=st.selectbox(
        "Customer",
        customers)
    ship_weight=st.number_input(
        "Weight to Ship (kg)",
        min_value=0.0,
        step=0.1)
    ship=st.button("Ship")
    if ship:
        if ship_weight<=0:
            st.error("Weight must be greater than zero.")
        elif ship_weight>selected_batch.kg:
            st.error(f"Only {selected_batch.kg:.2f} kg available.")
        else:
            selected_batch.kg -= ship_weight
            transaction=PowderTransaction(
                transaction_date=date.today(),
                grade=selected_batch.grade,
                heat_no=selected_batch.batch_number,
                condition=selected_batch.condition,
                amount=-ship_weight,
                transaction_type=f"To {customer}",
                reference_id=selected_batch.id)
            session.add(transaction)
            session.commit()
            st.success(f"{ship_weight:.2f} kg shipped to {customer}")
            st.rerun()
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
                            old_kg=batch.kg or 0
                            new_kg = kg
                            if new_kg < old_kg:
                                st.error(
                                    "Quantity reductions are not allowed."
                                    "Investigate and correct transaction."
                                    )
                            else:
                                difference=new_kg - old_kg
                                batch.grade=grade
                                batch.condition=condition
                                batch.kg=new_kg
                                batch.location=location
                                if difference>0:
                                    transaction=PowderTransaction(
                                        transaction_date=date.today(),
                                        grade=batch.grade,
                                        heat_no=batch.batch_number,
                                        condition=batch.condition,
                                        amount=difference,
                                        transaction_type="Powder Received",
                                        reference_id=batch.id)
                                    session.add(transaction)
                                session.commit()
                                st.success("Batch updated")
                                st.rerun()
                    st.divider()
                    if batch.status == "ACTIVE":
                        archive = st.button(
                            "Archive Batch",
                            key=f"archive_{batch.id}")
                        if archive:
                            batch.status = "ARCHIVED"
                            session.commit()
                            st.success(
                                f"{batch.batch_number} archived.")
                            st.rerun()
                    else:
                        unarchive = st.button(
                            "Unarchive Batch",
                            key=f"unarchive_{batch.id}")
                        if unarchive:
                            batch.status = "ACTIVE"
                            session.commit()
                            st.success(f"{batch.batch_number} unarchived.")
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
                                transaction=PowderTransaction(
                                    transaction_date=date.today(),
                                    grade=batch.grade,
                                    heat_no=batch.batch_number,
                                    condition=batch.condition,
                                    amount=-batch.kg,
                                    transaction_type="Batch Creation Error",
                                    reference_id=batch.id)
                                session.add(transaction)
                                session.delete(batch)
                                session.commit()
                                st.success("Batch deleted.")
                                st.rerun()

