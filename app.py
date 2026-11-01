"""InvoiceFlow Streamlit application entry point."""
from __future__ import annotations

import streamlit as st
from sqlalchemy import func, select

from config.settings import APP_NAME, MAX_UPLOAD_MB
from src.database.db import SessionLocal, init_db
from src.database.models import Invoice
from src.processing.service import extract_invoice_record, save_invoice_record

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
st.caption("PDF invoice extraction, validation and accounts-payable review")

with SessionLocal() as session:
    total_count = session.scalar(select(func.count(Invoice.id))) or 0
    review_count = session.scalar(
        select(func.count(Invoice.id)).where(Invoice.status == "needs_review")
    ) or 0
    ready_count = session.scalar(
        select(func.count(Invoice.id)).where(Invoice.status == "ready")
    ) or 0

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Invoices stored", f"{total_count:,}")
metric2.metric("Ready for review", f"{ready_count:,}")
metric3.metric("Needs attention", f"{review_count:,}")

st.divider()
st.subheader("Upload invoices")
st.write(
    "Upload one or more text-based PDF invoices. InvoiceFlow extracts common "
    "fields, checks arithmetic and required information, and flags possible duplicates."
)
uploads = st.file_uploader(
    "Choose PDF invoices",
    type=["pdf"],
    accept_multiple_files=True,
    help=f"Maximum size per file: {MAX_UPLOAD_MB} MB. Scanned PDFs are not OCR-processed yet.",
)

if st.button("Process invoices", type="primary", disabled=not uploads):
    results = []
    progress = st.progress(0)
    for index, uploaded in enumerate(uploads, start=1):
        try:
            content = uploaded.getvalue()
            if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
            record = extract_invoice_record(uploaded.name, content)
            with SessionLocal() as session:
                saved = save_invoice_record(session, record)
            validation = record["validation"]
            results.append({
                "File": uploaded.name,
                "Vendor": record.get("vendor") or "Not detected",
                "Invoice number": record.get("invoice_number") or "Not detected",
                "Invoice date": record.get("invoice_date"),
                "Total": (
                    f'{record.get("currency", "")} {record["total_amount"]}'
                    if record.get("total_amount") is not None else "Not detected"
                ),
                "Validation": validation["status"],
                "Result": saved["reason"] if saved["duplicate"] else (
                    "Saved" if saved["saved"] else "Not saved"
                ),
                "Errors": "; ".join(validation["errors"]),
                "Warnings": "; ".join(validation["warnings"] + record.get("pdf_warnings", [])),
            })
        except Exception as exc:
            results.append({
                "File": uploaded.name,
                "Vendor": "—",
                "Invoice number": "—",
                "Invoice date": None,
                "Total": "—",
                "Validation": "Error",
                "Result": str(exc),
                "Errors": "",
                "Warnings": "",
            })
        progress.progress(index / len(uploads))
    st.session_state["last_processing_results"] = results
    st.success("Processing finished. Review the results below before relying on any extracted values.")

if "last_processing_results" in st.session_state:
    st.subheader("Latest processing results")
    st.dataframe(st.session_state["last_processing_results"], use_container_width=True, hide_index=True)

st.divider()
st.subheader("Recent invoices")
with SessionLocal() as session:
    recent = session.scalars(
        select(Invoice).order_by(Invoice.created_at.desc()).limit(100)
    ).all()
    recent_rows = [{
        "ID": item.id,
        "Vendor": item.vendor.name if item.vendor else "Not detected",
        "Invoice number": item.invoice_number or "Not detected",
        "Invoice date": item.invoice_date,
        "Currency": item.currency,
        "Total": item.total_amount,
        "Status": item.status,
        "File": item.source_filename,
    } for item in recent]

if recent_rows:
    st.dataframe(recent_rows, use_container_width=True, hide_index=True)
else:
    st.info("No invoices have been processed yet. Upload PDF files above to get started.")

with st.expander("Privacy, limitations and review guidance"):
    st.write(
        "InvoiceFlow is intended for local execution. Uploaded documents and "
        "extracted text are stored in the local SQLite database. Do not use "
        "confidential client documents in a public demo deployment."
    )
    st.write(
        "Extraction currently supports selectable text in PDFs and common invoice "
        "labels. Scanned-image OCR, editable correction workflows and accounting "
        "or tax integrations are not included yet. Always verify extracted values "
        "against the original invoice before payment or reporting."
    )
