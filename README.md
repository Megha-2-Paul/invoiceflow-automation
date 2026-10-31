# InvoiceFlow — Smart Invoice & Expense Automation

InvoiceFlow is a Python business-automation application that turns PDF invoices into structured, validated financial records. It is designed as a practical portfolio project for small-business accounts payable workflows.

## Implemented
- Text-based PDF reading with clear invalid/empty-file errors and scanned-page warnings
- Rule-based extraction of vendor, invoice number, invoice/due dates, currency, subtotal, tax and total
- Extraction coverage score to guide human review
- Required-field, positive-total, date-order and subtotal-plus-tax validation
- Duplicate candidate detection by file SHA-256 and normalized vendor/invoice number
- SQLite vendor/invoice schema and Streamlit application shell
- Unit tests for parser, validation and duplicate detection

## Planned next
- Batch upload and persistence workflow
- OCR support for image-only/scanned invoices
- Review-and-correct interface
- Vendor and expense analytics
- Excel/CSV exports and downloadable reports
- End-to-end tests and deployment guide

> **Important:** InvoiceFlow is a decision-support and data-entry aid, not accounting or tax advice. Extracted values must be reviewed before payment or statutory reporting. Rule-based extraction is layout-dependent; OCR is not yet implemented.

## Technology
Python, Streamlit, Pandas, pdfplumber, SQLAlchemy, SQLite, Plotly, openpyxl, pytest.

## Run locally
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` if you want to customize local settings.
4. Run: `streamlit run app.py`

## Run tests
`pytest -q`

## Privacy
This application is designed for local execution. Do not commit real customer invoices, credentials, or confidential financial information. Use synthetic or appropriately licensed and anonymized sample documents in the public repository.
