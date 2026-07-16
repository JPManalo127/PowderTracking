import streamlit as st
from database import Session, Build, Dispenser, DispenserLayer, BuildConsumption, Batch, BatchComponent, get_recovery_batch

session = Session()

st.title("Builds")

st.subheader("Record Build")
with st.form("record_build"):
    build_number = st.text_input("Build Number")
    build_date = st.date_input("Build Date")
    dispensers = session.query(
        Dispenser
        ).filter_by(
            status="ACTIVE"
            ).all()
    machine_options = {
        d.current_machine: d
        for d in dispensers
        }
    selected_machine = st.selectbox("Machine",
                                      list(machine_options.keys())
                                      )
    dispenser=machine_options[selected_machine]
    powder_used = st.number_input(
        "Build Weight (kg)",
        min_value=0.0
        )
    submit = st.form_submit_button("Record Build")
    if submit:
        if powder_used > dispenser.kg_in_dispenser:
            st.error(
                f"only {dispenser.kg_in_dispenser} kg available in this dispenser."
                )
        else:
            build = Build(build_number=build_number,
                          build_date=str(build_date),
                          dispenser_name=dispenser.dispenser_name,
                          powder_used=powder_used
                          )
            session.add(build)
            session.commit()
            st.success(f"Build {build_number} recorded.")
            st.rerun()    
st.divider()
st.header("Build History")
builds = session.query(
    Build
    ).order_by(
        Build.id.desc()
        ).all()
for build in builds:
    with st.expander(
        f"{build.build_number} | {build.build_date} | {build.powder_used} kg "
        ):
        with st.expander("Generate Recovery Batch"):
            recovery_weight = st.number_input(
                "Recovered Weight (kg)",
                min_value=0.0,
                key=f"recover_{build.id}"
                )
            generate = st.button(
                "Generate Batch",
                key=f"generate_{build.id}"
                )
            if generate:
                if build.recovery_batch:
                    st.warning(f"Recovery Batch {build.recovery_batch} already exists.")
                    st.stop()
                total_processed=(build.powder_used+recovery_weight)
                dispenser = session.query(
                    Dispenser
                    ).filter_by(
                        dispenser_name=build.dispenser_name
                        ).first()
                if dispenser.feed_direction=="DOWN":
                    layers = session.query(
                        DispenserLayer
                        ).filter_by(
                            dispenser_id=dispenser.id
                            ).order_by(
                                DispenserLayer.position.asc()
                                ).all()
                else:
                    layers=session.query(
                        DispenserLayer
                        ).filter_by(
                            dispenser_id=dispenser.id
                            ).order_by(
                                DispenserLayer.position.desc()
                                ).all()
                available_powder=sum(
                    layer.kg
                    for layer in layers)
                if available_powder < total_processed:
                    st.error(
                        f"Not enough powder available."
                        f"Need {total_processed:.2f} kg,"
                        f"but only {available_powder:.2f} kg exists."
                        )
                    st.stop()
                remaining = total_processed
                consumption_records=[]
                for layer in layers:
                    if remaining <= 0:
                        break
                    consumed = min(layer.kg,
                                   remaining)
                    consumption = BuildConsumption(
                        build_number=build.build_number,
                        batch_number=layer.batch_number,
                        kg=consumed)
                    session.add(consumption)
                    consumption_records.append(consumption)
                    layer.kg-=consumed
                    remaining-=consumed
                    if layer.kg <= 0:
                        session.delete(layer)
                if remaining>0:
                    st.error(f"Not enough powder available."
                             f"Short {remaining:,2f}kg.")
                    session.rollack()
                    st.stop
                remaining_layers = session.query(
                    DispenserLayer
                ).filter_by(
                    dispenser_id=dispenser.id
                ).all()
                dispenser.kg_in_dispenser = sum(
                    layer.kg
                    for layer in remaining_layers
                )
                consumption_records=session.query(
                    BuildConsumption
                    ).filter_by(
                        build_number=build.build_number
                        ).all()
                source_batch=session.query(
                    Batch
                    ).filter_by(
                        batch_number=consumption_records[0].batch_number
                        ).first()
                grade=source_batch.grade
                new_batch_number=get_recovery_batch(session)
                new_batch=Batch(
                    batch_number=new_batch_number,
                    grade=grade,
                    condition="Sieved",
                    kg=recovery_weight,
                    location="Sieve",
                    status="ACTIVE"
                    )
                for record in consumption_records:
                    percent=record.kg/total_processed
                    component_weight=(
                        recovery_weight*percent)
                    component=BatchComponent(
                    parent_batch=new_batch_number,
                    component_batch=record.batch_number,
                    kg=component_weight)
                    session.add(component)
                build.recovery_batch=new_batch_number
                build.recovery_weight=recovery_weight
                session.add(new_batch)
                session.commit()
                st.success(f"Recovery Batch {new_batch_number} created.")
                st.rerun()
        st.write(
            f"Dispenser: {build.dispenser_name}"
            )
        st.write(
            f"Build Number: {build.build_number}"
            )
        st.write(
            f"Build Date: {build.build_date}"
            )
        st.subheader("Build Composition")
        st.write(f"Build Weight: {build.powder_used:.2f} kg")
        consumption_records=session.query(
            BuildConsumption
            ).filter_by(
                build_number=build.build_number
                ).all()
        total_processed=(build.powder_used+(build.recovery_weight or 0))
        for record in consumption_records:
            ratio=(record.kg/total_processed)
            build_component=(build.powder_used*ratio)
            st.write(f"{record.batch_number}: "
                     f"{build_component:.2f} kg")
        st.divider()
        if build.recovery_batch:
            st.subheader("Traceability Summary")
            consumption_records=session.query(
                BuildConsumption
                ).filter_by(
                    build_number=build.build_number
                    ).all()
            total_processed=(build.powder_used+build.recovery_weight)
            for record in consumption_records:
                st.write(f"{record.batch_number}: {record.kg:.2f} kg")     
            st.write(f"Total Powder Consumed: {total_processed:.2f} kg")
            st.divider()
            st.subheader("Recovery Batch")
            st.write(f"Batch: {build.recovery_batch}")
            st.write(f"Recovered Powder Weight: {build.recovery_weight} kg")
            st.write("")
            st.write("Composition:")            
            components=session.query(
                BatchComponent
                ).filter_by(
                    parent_batch=build.recovery_batch
                    ).all()
            for component in components:
                st.write(
                    f"{component.component_batch}:"
                    f"{component.kg: .2f} kg"
                    )
        else:
            st.info("No powder recovery information.")
        
