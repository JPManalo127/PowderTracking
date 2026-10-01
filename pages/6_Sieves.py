import streamlit as st
from datetime import datetime

from database import (
    Session,
    Sieve,
    SieveRun,
    SieveRunBuild,
    Build,
    BuildConsumption,
    Batch,
    BatchComponent,
    PowderTransaction,
    get_recovery_batch
)

session = Session()

st.title("Powder Recovery")

# ==========================================
# Sieve Status Cards
# ==========================================

st.header("Current Sieve Status")

sieves = (
    session.query(Sieve)
    .order_by(Sieve.sieve_id)
    .all()
)

cols = st.columns(4)

for col, sieve in zip(cols, sieves):

    with col:

        st.subheader(sieve.sieve_id)

        if sieve.status == "ACTIVE":

            st.success("ACTIVE")

        else:

            st.info("INACTIVE")

        st.write(
            f"Material: "
            f"{sieve.material}"
        )

# ==========================================
# Create Recovery Event
# ==========================================

st.header("Create Recovery Event")

available_sieves = (
    session.query(Sieve)
    .filter_by(status="INACTIVE")
    .order_by(Sieve.sieve_id)
    .all()
)

if available_sieves:

    selected_sieve = st.selectbox(
        "Select Sieve",
        [s.sieve_id for s in available_sieves]
    )

    if st.button("Create Recovery Event"):

        existing = (
            session.query(SieveRun)
            .filter_by(
                sieve_id=selected_sieve,
                status="ACTIVE"
            )
            .first()
        )

        if existing:

            st.warning(
                f"{selected_sieve} already has an active recovery event."
            )

        else:

            sieve = (
                session.query(Sieve)
                .filter_by(
                    sieve_id=selected_sieve
                )
                .first()
            )

            new_run = SieveRun(
                sieve_id=sieve.sieve_id,
                status="ACTIVE",
                date_created=datetime.now()
            )

            session.add(new_run)

            sieve.status = "ACTIVE"

            session.commit()

            st.success(
                f"Recovery Event created for "
                f"{sieve.sieve_id}"
            )

            st.rerun()

else:

    st.warning(
        "No inactive sieves available."
    )

st.header("Active Recovery Events")

show_closed = st.checkbox(
    "Show Closed Events",
    value=False
)

if show_closed:

    active_runs = (
        session.query(SieveRun)
        .order_by(SieveRun.id.desc())
        .all()
    )

else:

    active_runs = (
        session.query(SieveRun)
        .filter_by(status="ACTIVE")
        .order_by(SieveRun.id.desc())
        .all()
    )

if not active_runs:

    st.info("No active recovery events.")

else:

    for run in active_runs:

        sieve = (
            session.query(Sieve)
            .filter_by(
                sieve_id=run.sieve_id
            )
            .first()
        )

        assigned = (
            session.query(SieveRunBuild)
            .filter_by(
                sieve_run_id=run.id
            )
            .all()
        )

        build_count = len(assigned)

        if build_count == 0:

            header_text = (
                f"{run.sieve_id} | "
                f"No Builds Assigned"
            )

        elif build_count == 1:

            header_text = (
                f"{run.sieve_id} | "
                f"{assigned[0].build_number}"
            )

        else:

            header_text = (
                f"{run.sieve_id} | "
                f"{build_count} Builds Assigned"
            )

        with st.expander(header_text):

            # ----------------------------------
            # Summary
            # ----------------------------------

            st.write(
                f"Material: "
                f"{sieve.material or 'Not Assigned'}"
            )

            st.write(
                f"Status: "
                f"{sieve.status}"
            )

            total_source = sum(
                (item.source_weight or 0)
                for item in assigned
            )

            st.write(
                f"Total Source Powder: "
                f"{total_source:.2f} kg"
            )

            st.divider()

            # ----------------------------------
            # Assign Build
            # ----------------------------------
            st.subheader("Assign Build")

            multi_build = st.checkbox(
                "Multiple Builds",
                key=f"multi_build_{run.id}"
            )

            available_builds = []

            builds = (
                session.query(Build)
                .order_by(Build.build_date.desc())
                .all()
            )

            for build in builds:

                if not build.build_end:
                    continue

                if (build.remaining_powder or 0) <= 0:
                    continue

                available_builds.append(build)

            # ==================================
            # SINGLE BUILD MODE
            # ==================================

            if not multi_build:

                if len(assigned) >= 1:

                    st.info(
                        "This recovery event already has a build assigned."
                    )

                elif available_builds:

                    selected_build = st.selectbox(
                        "Completed Build",
                        available_builds,
                        format_func=lambda x:
                            f"{x.build_number} "
                            f"({(x.remaining_powder or 0):.2f} kg available)",
                        key=f"assign_build_{run.id}"
                    )

                    if st.button(
                        "Assign Build",
                        key=f"assign_btn_{run.id}"
                    ):

                        session.add(
                            SieveRunBuild(
                                sieve_run_id=run.id,
                                build_number=selected_build.build_number
                            )
                        )

                        session.commit()

                        st.success(
                            f"{selected_build.build_number} assigned."
                        )

                        st.rerun()

                else:

                    st.info(
                        "No completed builds available."
                    )

            # ==================================
            # MULTI BUILD MODE (UI ONLY)
            # ==================================

            else:

                build_count = st.selectbox(
                    "Number of Builds",
                    list(range(1, 11)),
                    key=f"build_count_{run.id}"
                )

                selected_builds = []

                st.divider()

                for i in range(build_count):

                    st.markdown(
                        f"### Build {i + 1}"
                    )

                    build_selection = st.selectbox(
                        "Build Number",
                        available_builds,
                        format_func=lambda x:
                            f"{x.build_number}"
                            f" ({(x.remaining_powder or 0):.2f} kg available)",
                        key=f"multi_build_{run.id}_{i}"
                    )

                    entered_weight = st.number_input(
                        "Weight (kg)",
                        min_value=0.0,
                        step=0.1,
                        key=f"multi_weight_{run.id}_{i}"
                    )

                    selected_builds.append(
                        build_selection.build_number
                    )

                    st.divider()

                if len(selected_builds) != len(set(selected_builds)):

                    st.error(
                        "The same build cannot be selected more than once."
                    )

                if st.button(
                    "Assign Multiple Builds",
                    key=f"assign_multi_{run.id}"
                ):
                    selected_records=[]
                    for i in range(build_count):
                        build_obj = st.session_state[
                            f"multi_build_{run.id}_{i}"
                        ]
                        weight = st.session_state[
                            f"multi_weight_{run.id}_{i}"
                            ]
                        if weight <= 0:
                            st.error(
                                f"Build {i + 1} requires a weight."
                                )
                            st.stop()
                        if weight > (
                            build_obj.remaining_powder or 0
                        ):
                            st.error(
                                f"{build_obj.build_number} "
                                f"only has "
                                f"{build_obj.remaining_powder:.2f} kg "
                                f"available."
                            )
                            st.stop()
                        selected_records.append(
                            (build_obj, weight)
                            )
                    selected_names = [
                        b.build_number
                        for b, w in selected_records
                    ]
                    if len(selected_names) != len(set(selected_names)):
                        st.error(
                        "The same build cannot be selected more than once."
                        )
                        st.stop()
                    for build_obj, weight in selected_records:
                        session.add(
                            SieveRunBuild(
                                sieve_run_id=run.id,
                                build_number=build_obj.build_number,
                                source_weight=weight
                            )
                        )
                    session.commit()
                    st.success(
                    f"{len(selected_records)} builds assigned."
                    )
                    st.rerun()

            # ----------------------------------
            # Assigned Builds
            # ----------------------------------

            st.subheader("Assigned Builds")

            if not assigned:

                st.warning(
                    "Please assign a build number."
                )

            else:

                for item in assigned:

                    build = (
                        session.query(Build)
                        .filter_by(
                            build_number=item.build_number
                        )
                        .first()
                    )

                    st.write(
                        f"Build: "
                        f"{build.build_number}"
                    )

                    st.write(
                        f"Completed: "
                        f"{build.build_end:%Y-%m-%d %H:%M}"
                    )

                    if item.source_weight is not None:

                        assigned_weight = item.source_weight

                    else:

                        assigned_weight = (
                            build.remaining_powder or 0
                        )

                    st.write(
                        f"Assigned Weight: "
                        f"{assigned_weight:.2f} kg"
                    )
                    st.divider()

            # ----------------------------------
            # Recovered Weight
            # ----------------------------------

            st.subheader("Recovered Weight")

            recovered_weight = st.number_input(
                "Recovered Weight (kg)",
                min_value=0.0,
                value=float(
                    run.recovered_weight or 0
                ),
                key=f"weight_{run.id}"
            )

            if st.button(
                "Save Recovered Weight",
                key=f"save_weight_{run.id}"
            ):

                run.recovered_weight = recovered_weight

                sieve.status = "INACTIVE"

                session.commit()

                st.success(
                    f"Recovered Weight Saved: "
                    f"{recovered_weight:.2f} kg"
                )

                st.rerun()
                
            st.divider()

            # ----------------------------------
            # Recovery summary
            # ----------------------------------
            
            st.subheader("Recovery Summary")

            total_source = 0

            for item in assigned:

                build = (
                    session.query(Build)
                    .filter_by(
                        build_number=item.build_number
                    )
                    .first()
                )

                if item.source_weight is not None:

                    total_source += (
                        item.source_weight or 0
                    )

                else:

                    total_source += (
                        build.remaining_powder or 0
                    )
            recovered = run.recovered_weight or 0

            st.write(
                f"Total Source Powder: "
                f"{total_source:.2f} kg"
            )

            st.write(
                f"Recovered Powder: "
                f"{recovered:.2f} kg"
            )
            
            if (
                recovered > 0
                and
                len(assigned) > 0
            ):

                generate_batch = st.button(
                    "Generate Recovery Batch",
                    key=f"generate_batch_{run.id}"
                )
                
                if generate_batch:
                    
                    if not run.recovered_weight:

                        st.error(
                            "Please enter recovered weight first."
                        )

                        st.stop()

                    assigned = (
                        session.query(SieveRunBuild)
                        .filter_by(
                            sieve_run_id=run.id
                        )
                        .all()
                    )

                    if not assigned:

                        st.error(
                            "No builds assigned."
                        )

                        st.stop()

                    if run.recovery_batch:

                        st.warning(
                            f"Recovery Batch "
                            f"{run.recovery_batch} "
                            f"already exists."
                        )

                        st.stop()
                    combined_batches = {}
                    total_source = 0
                    grade = None

                    for assignment in assigned:

                        build = (
                            session.query(Build)
                            .filter_by(
                                build_number=assignment.build_number
                            )
                            .first()
                        )

                        consumption_records = (
                            session.query(BuildConsumption)
                            .filter_by(
                                build_number=assignment.build_number
                            )
                            .all()
                        )

                        build_total = (
                            build.total_processed or 0
                        )

                        if assignment.source_weight is not None:

                            assigned_weight = assignment.source_weight

                        else:

                            assigned_weight = (
                                build.remaining_powder or 0
                            )

                        for record in consumption_records:

                            if build_total > 0:

                                weighted_kg = (
                                    record.kg
                                    / build_total
                                ) * assigned_weight

                            else:

                                weighted_kg = 0

                            combined_batches.setdefault(
                                record.batch_number,
                                0
                            )

                            combined_batches[
                                record.batch_number
                            ] += weighted_kg

                            total_source += weighted_kg

                            if grade is None:

                                source_batch = (
                                    session.query(Batch)
                                    .filter_by(
                                        batch_number=record.batch_number
                                    )
                                    .first()
                                )

                                if source_batch:

                                    grade = source_batch.grade

                    if total_source <= 0:

                        st.error(
                            "No genealogy source found."
                        )

                        st.stop()

                    new_batch_number = (
                        get_recovery_batch(session)
                    )

                    new_batch = Batch(
                        batch_number=new_batch_number,
                        grade=grade,
                        condition="Sieved",
                        kg=run.recovered_weight,
                        location="Powder Storage",
                        status="ACTIVE"
                    )

                    session.add(new_batch)

                    for batch_number, source_kg in combined_batches.items():

                        percent = (
                            source_kg
                            / total_source
                        )

                        component_weight = (
                            run.recovered_weight
                            * percent
                        )

                        component = BatchComponent(
                            parent_batch=new_batch_number,
                            component_batch=batch_number,
                            kg=component_weight
                        )

                        session.add(component)

                    for assignment in assigned:

                        build = (
                            session.query(Build)
                            .filter_by(
                                build_number=assignment.build_number
                            )
                            .first()
                        )

                        if assignment.source_weight is not None:

                            build.remaining_powder = max(
                                0,
                                (build.remaining_powder or 0)
                                - assignment.source_weight
                            )

                        else:

                            build.remaining_powder = max(
                                0,
                                (build.remaining_powder or 0)
                                - run.recovered_weight
                            )

                    transaction = PowderTransaction(
                        transaction_date=datetime.now(),
                        grade=grade,
                        heat_no=new_batch_number,
                        condition="Sieved",
                        amount=run.recovered_weight,
                        transaction_type="Recovery Batch",
                        reference_id=run.id
                    )

                    session.add(transaction)

                    run.recovery_batch = new_batch_number

                    session.commit()

                    st.success(
                        f"Recovery Batch "
                        f"{new_batch_number} created."
                    )

                    st.rerun()
    
            # ----------------------------------
            # Event Actions
            # ----------------------------------

            st.divider()

            col1, col2 = st.columns(2)

            with col1:

                if run.recovered_weight:

                    if st.button(
                        "Close Event",
                        key=f"close_{run.id}"
                    ):

                        run.status = "CLOSED"

                        sieve.status = "INACTIVE"

                        run.date_completed = datetime.now()

                        session.commit()

                        st.success(
                            "Recovery event closed."
                        )

                        st.rerun()

            with col2:

                if st.button(
                    "Delete Event",
                    key=f"delete_{run.id}"
                ):

                    sieve = (
                        session.query(Sieve)
                        .filter_by(
                            sieve_id=run.sieve_id
                        )
                        .first()
                    )

                    if sieve:

                        sieve.status = "INACTIVE"

                    session.query(
                        SieveRunBuild
                    ).filter_by(
                        sieve_run_id=run.id
                    ).delete()

                    session.delete(run)

                    session.commit()

                    st.success(
                        "Recovery event deleted."
                    )

                    st.rerun()

