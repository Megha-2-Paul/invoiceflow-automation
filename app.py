"""InvoiceFlow Streamlit application entry point."""

import streamlit as st

from config.settings import APP_NAME
from src.database.db import init_db

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def initialize_database() -> None:
    """Initialize the local database once per app session."""
    init_db()


initialize_database()

st.title("🧾 InvoiceFlow")
st.caption("Smart invoice processing and expense intelligence")

st.info(
    "Your workspace is ready. Invoice extraction and validation are being "
    "built in the next development phase."
)

col1, col2, col3 = st.columns(3)
col1.metric("Invoices processed", "—")
col2.metric("Pending review", "—")
col3.metric("Total expenses", "—")

st.subheader("Getting started")
st.write(
    "InvoiceFlow will help you extract invoice details from PDF files, "
    "review data quality, detect possible duplicates, and prepare clean "
    "financial exports."
)

with st.expander("Privacy and data handling"):
    st.write(
        "This portfolio application is intended to run locally. Invoice "
        "documents and the SQLite database should remain private. Always "
        "review extracted information before relying on it."
    )
