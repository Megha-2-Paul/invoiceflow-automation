"""Centralized application settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

APP_NAME = os.getenv("APP_NAME", "InvoiceFlow")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(PROJECT_ROOT / 'data' / 'invoiceflow.db').as_posix()}",
)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))

DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_INVOICES_DIR = DATA_DIR / "sample_invoices"
PROCESSED_DIR = DATA_DIR / "processed"

for directory in (DATA_DIR, SAMPLE_INVOICES_DIR, PROCESSED_DIR):
    directory.mkdir(parents=True, exist_ok=True)
