import streamlit as st

st.title("Admin")

with open("powder_tracker.db", "rb") as f:
    st.download_button(
        "Download Current Database",
        data=f,
        file_name="powder_tracker_backup.db")
