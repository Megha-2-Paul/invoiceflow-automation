# InvoiceFlow — Smart Invoice & Expense Automation

InvoiceFlow is a Python business-automation application that turns PDF invoices into structured, validated financial records. It is designed as a practical portfolio project for small-business accounts payable workflows.

## Planned capabilities
- Upload text-based PDF invoices (single or batch)
- Extract invoice metadata and line-item text
- Validate required fields and reconcile totals
- Flag likely duplicate invoices for human review
- Store records locally in SQLite
- Explore spending by vendor and month
- Export structured records to Excel and CSV
- Provide processing status and actionable errors

> **Important:** InvoiceFlow is a decision-support and data-entry aid, not accounting or tax advice. Extracted values must be reviewed before being used for payment or statutory reporting. OCR for scanned PDFs will be added in a later phase.

## Technology
Python, Streamlit, Pandas, pdfplumber, SQLAlchemy, SQLite, Plotly, openpyxl, pytest.

## Run locally
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` if you want to customize local settings.
4. Run: `streamlit run app.py`

## Project status
Phase 1: foundation and application shell. Extraction, validation, analytics, exports and tests will be implemented in subsequent phases.

## Privacy
This initial version is designed for local execution. Do not upload confidential customer invoices to a public repository. Sample documents must be synthetic or appropriately licensed and anonymized.
