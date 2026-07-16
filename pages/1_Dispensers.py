import streamlit as st
from database import Session, Dispenser, Batch, DispenserLayer

session = Session()

st.title("Dispensers")

dispensers = session.query(Dispenser).all()

with st.expander("➕ Add New Dispenser"):

    with st.form("add_dispenser"):

        name = st.text_input("Dispenser Name")
        machine = st.text_input("Current Machine")
        material = st.text_input("Material")
        weight = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            value=0.0
        )
        feed_direction = st.selectbox(
            "Feed Direction",
            ["UP", "DOWN"])
        status = st.selectbox(
            "Status",
            ["ACTIVE","INACTIVE"]
            )
        submitted = st.form_submit_button("Add Dispenser")
        if submitted:
            dispenser = Dispenser(
                dispenser_name=name,
                current_machine=machine,
                material=material,
                kg_in_dispenser=weight,
                feed_direction=feed_direction,
                status=status
            )
            session.add(dispenser)
            session.commit()
            st.success("Dispenser added.")
            st.rerun()
st.divider()
st.header("Current Dispensers")
st.write(f"Total Dispensers: {len(dispensers)}")
for dispenser in dispensers:
    with st.expander(
        f"{dispenser.dispenser_name} | {dispenser.material or "None"} | {dispenser.kg_in_dispenser} kg | {dispenser.current_machine or "N/A"} | {dispenser.status}"
    ):
        st.write(f"Machine: {dispenser.current_machine}")
        st.write(f"Material: {dispenser.material}")
        st.write(f"Weight: {dispenser.kg_in_dispenser} kg")
        st.write(f"Status: {dispenser.status}")
        st.divider()
        st.subheader("Batches In Dispenser")
        layers = session.query(DispenserLayer).filter_by(
            dispenser_id=dispenser.id
            ).all()
        if not layers:
            st.info("No batches currently assigned.")
        else:
            for layer in sorted(
                layers,
                key=lambda x: x.position,
                reverse=True
                ):
                st.write(
                    f"Position {layer.position} | {layer.batch_number} | {layer.kg} kg"
                    )
        with st.expander("Add Batch to Dispenser"):
            with st.form(f"add_batch_{dispenser.id}"):
                batches = session.query(Batch).all()
                batch_options = {
                    batch.batch_number: batch
                    for batch in batches
                    if batch.kg > 0
                    }
                selected_batch = st.selectbox(
                    "Select Batch",
                    list(batch_options.keys())
                    )
                amount = st.number_input(
                    "Amount (kg)",
                    min_value=0.0,
                    step=0.1
                    )
                add_batch = st.form_submit_button("Add Batch to Dispenser")
                add_all = st.form_submit_button("Add All")
                batch=batch_options[selected_batch]
                if add_all:
                    amount=batch.kg
                if add_batch or add_all:
                    if amount > batch.kg:
                        st.error(
                            f"Only{batch.kg} kg available."
                            )
                    else:
                        highest_position=max(
                            [
                                layer.position
                                for layer in session.query(
                                    DispenserLayer
                                    ).filter_by(
                                            dispenser_id=dispenser.id
                                        ).all()
                                ],
                            default=0
                            )
                        new_layer = DispenserLayer(
                        dispenser_id=dispenser.id,
                        batch_number=batch.batch_number,
                        kg=amount,
                        position=highest_position + 1
                        )
                        batch.kg -= amount
                        dispenser.kg_in_dispenser += amount
                        session.add(new_layer)
                        session.commit()
                        st.success(
                            f"{amount} kg added from {batch.batch_number}"
                            )
                    st.rerun()
        st.divider()
        with st.expander("Edit Dispenser"):
            with st.form(f"edit_{dispenser.id}"):
                machine = st.text_input(
                    "Current Machine",
                    value=dispenser.current_machine or "")
                material = st.text_input(
                    "Material",
                    value=dispenser.material or "")
                weight = st.number_input(
                    "Weight (kg)",
                    min_value=0.0,
                    value=float(dispenser.kg_in_dispenser or 0.0))
                feed_options=["UP", "DOWN"]
                feed_direction = st.selectbox(
                    "Feed Direction",
                    feed_options,
                    index=(
                        feed_options.index(dispenser.feed_direction)
                        if dispenser.feed_direction in feed_options
                        else 0))
                status = st.selectbox(
                    "Status",
                    ["ACTIVE", "INACTIVE"],
                    index=0 if dispenser.status == "ACTIVE" else 1,
                    key=f"status_{dispenser.id}")
                save = st.form_submit_button("Save Changes")
                if save:
                    dispenser.current_machine = machine
                    dispenser.material = material
                    dispenser.kg_in_dispenser = weight
                    dispenser.status = status
                    dispenser.feed_direction = feed_direction
                    session.commit()
                    st.success("Dispenser updated.")
                    st.rerun()
