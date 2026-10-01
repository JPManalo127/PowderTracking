import streamlit as st
from database import Session, Build, Dispenser, DispenserLayer, BuildConsumption, Batch, BatchComponent, PowderTransaction, get_recovery_batch, Sieve, SieveRun, WasteReport
from datetime import date, datetime

session = Session()
waste_factors={
    "BOH L718 API": 0.075,
    "HOG Ti64 G2-3": 0.03,
    "HOG Ti64 G5": 0.03,
    "316L": 0.05,
    "BOH L718 AMS": 0.075,
    "BOH L175": 0.1205
    }

st.title("Builds")
st.subheader("Record Build")
with st.form("record_build"):
    build_number = st.text_input("Build Number")
    dispensers = (
        session.query(Dispenser)
        .filter_by(status="ACTIVE")
        .all())
    machine_options = {
        d.current_machine: d
        for d in dispensers}
    selected_machine = st.selectbox(
        "Machine",
        list(machine_options.keys()),
        format_func=lambda x:
            f"{x} ({machine_options[x].kg_in_dispenser:.2f} kg)")
    dispenser = machine_options[selected_machine]
    start_disp = st.number_input(
        "Start Dispenser Weight (kg)",
        min_value=0.0 )
    submit = st.form_submit_button("Record Build")
    if submit:
        build = Build(
            build_number=build_number,
            build_date=datetime.now(),
            dispenser_name=dispenser.dispenser_name,
            powder_used=start_disp)
        session.add(build)
        session.commit()
        st.success(
            f"Build {build_number} recorded.")
        st.rerun()
st.divider()
st.header("Build History")
builds_per_page=10
total_builds=session.query(Build).count()
import math
total_pages=max(
    1,
    math.ceil(total_builds/builds_per_page))
if "build_page" not in st.session_state:
    st.session_state.build_page=1
offset = (
    st.session_state.build_page - 1
) * builds_per_page
builds = (
    session.query(Build)
    .order_by(Build.id.desc())
    .offset(offset)
    .limit(builds_per_page)
    .all())
st.caption(f"Showing {builds_per_page} builds per page")
for build in builds:
    with st.expander(
        f"{build.build_number} | "
        f"{build.build_date:%Y-%m-%d %H:%M}"):
        st.write(f"Dispenser: {build.dispenser_name}")
        st.write(
            f"Start Weight: "
            f"{build.powder_used:.2f} kg")
        if build.total_processed:
            st.write(
                f"Total Processed: "
                f"{build.total_processed:.2f} kg")
        save_end_disp = False
        if build.build_end:
            st.success(
                f"Build Completed: "
                f"{build.build_end:%Y-%m-%d %H:%M}")
            st.write(
                f"End Weight: "
                f"{build.build_weight:.2f} kg")
            st.write(
                f"Remaining Powder: "
                f"{(build.remaining_powder or 0):.2f} kg"
            )

            st.write(
                f"Waste: "
                f"{(build.waste or 0):.2f} kg"
            )
            st.divider()

            if (build.remaining_powder or 0) > 0:

                if st.button(
                    "Declare Remaining Powder as Waste",
                    key=f"waste_{build.id}"
                ):

                    remaining = (
                        build.remaining_powder or 0
                    )

                    build.waste = (
                        build.waste or 0
                    ) + remaining

                    build.remaining_powder = 0

                    session.commit()

                    st.success(
                        f"{remaining:.2f} kg declared as waste."
                    )

                    st.rerun()
        else:
            end_disp = st.number_input(
                "End Dispenser Weight (kg)",
                min_value=0.0,
                key=f"end_disp_{build.id}")
            save_end_disp = st.button(
                "Complete Build",
                key=f"save_end_disp_{build.id}")
        if save_end_disp:
            existing_consumption = (
                session.query(BuildConsumption)
                .filter_by(
                    build_number=build.build_number
                )
                .first()
            )
            if existing_consumption:
                st.warning(
                    "Build already completed."
                )
                st.stop()
            build.build_weight = end_disp
            build.build_end = datetime.now()

            dispenser = (
                session.query(Dispenser)
                .filter_by(
                    dispenser_name=build.dispenser_name
                )
                .first()
            )
            added_transactions = (
                session.query(PowderTransaction)
                .filter(
                    PowderTransaction.transaction_date >= build.build_date,
                    PowderTransaction.transaction_date <= build.build_end,
                    PowderTransaction.transaction_type
                    == dispenser.current_machine
                )
                .all()
            )
            added_powder = abs(
                sum(
                    t.amount
                    for t in added_transactions
                    if t.amount < 0
                )
            )
            total_processed = (
                build.powder_used
                + added_powder
                - build.build_weight
            )
            if total_processed <= 0:
                st.error( "Total processed powder must be greater than zero.")
                st.stop()
            build.total_processed = total_processed
            build.remaining_powder = total_processed
            if dispenser.feed_direction == "DOWN":
                layers = (
                    session.query(DispenserLayer)
                    .filter_by(
                        dispenser_id=dispenser.id
                    )
                    .order_by(
                        DispenserLayer.position.asc()
                    )
                    .all()
                )
            else:
                layers = (
                    session.query(DispenserLayer)
                    .filter_by(
                        dispenser_id=dispenser.id
                    )
                    .order_by(
                        DispenserLayer.position.desc()
                    )
                    .all()
                )
            remaining = total_processed
            for layer in layers:
                if remaining <= 0:
                    break
                consumed = min(
                    layer.kg,
                    remaining)
                session.add(
                    BuildConsumption(
                        build_number=build.build_number,
                        batch_number=layer.batch_number,
                        kg=consumed))
                layer.kg -= consumed
                remaining -= consumed
                if layer.kg <= 0:
                    session.delete(layer)
            if remaining > 0:
                session.rollback()
                st.error(
                    f"Not enough powder available. "
                    f"Short {remaining:.2f} kg.")
                st.stop()
            remaining_layers = (
                session.query(DispenserLayer)
                .filter_by(
                    dispenser_id=dispenser.id
                )
                .all())
            dispenser.kg_in_dispenser = sum(
                layer.kg
                for layer in remaining_layers)
            session.commit()
            st.success(
                f"Build completed. "
                f"Total processed = "
                f"{total_processed:.2f} kg")
            st.rerun()
        st.subheader("Build Consumption")
        if build.build_end:

            consumption_records = (
                session.query(BuildConsumption)
                .filter_by(
                    build_number=build.build_number
                )
                .all()
            )

            if not consumption_records:

                st.warning(
                    "Build completed but no genealogy records found."
                )

            else:

                processed = build.total_processed or 0

                for record in consumption_records:

                    if processed > 0:

                        percent = (
                            record.kg
                            / processed
                        ) * 100

                    else:

                        percent = 0

                    st.write(
                        f"{record.batch_number}: "
                        f"{record.kg:.2f} kg "
                        f"({percent:.2f}%)"
                    )
        else:
            st.info("Build not completed.")
st.divider()
col1, col2, col3 = st.columns([1,2,1])
with col1:
    if st.button("< Previous"):
        if st.session_state.build_page > 1:
            st.session_state.build_page -= 1
            st.rerun()
with col2:
    st.markdown(
        f"### Page {st.session_state.build_page} of {total_pages}")
with col3:
    if st.button("Next >"):
        if st.session_state.build_page < total_pages:
            st.session_state.build_page += 1
            st.rerun()
