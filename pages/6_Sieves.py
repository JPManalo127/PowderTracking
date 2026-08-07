import streamlit as st
from database import Session, Sieve

session = Session()
for i in range(1, 5):
    existing = (
        session.query(Sieve)
        .filter_by(
            sieve_id=f"Sieve {i}"
        )
        .first()
    )
    if not existing:
        session.add(
            Sieve(
                sieve_id=f"Sieve {i}",
                status="INACTIVE"
            )
        )
session.commit()
st.title("Sieves")
st.header("Current Sieve Status")
sieves = (
    session.query(Sieve)
    .order_by(Sieve.sieve_id)
    .all())
cols = st.columns(4)
for col, sieve in zip(cols, sieves):
    with col:
        st.subheader(sieve.sieve_id)
        st.write(f"**{sieve.status}**")
        st.write(
            sieve.build_number
            if sieve.build_number
            else "---")
st.divider()
st.header("Edit Sieve Materials")
for sieve in sieves:
    with st.expander(
        f"{sieve.sieve_id}"
    ):
        material = st.text_input(
            "Material",
            value=sieve.material or "",
            key=f"material_{sieve.id}")
        save = st.button(
            "Save",
            key=f"save_{sieve.id}")
        if save:
            sieve.material = material
            session.commit()
            st.success(
                f"{sieve.sieve_id} updated.")
            st.rerun()
