"""Tests for InvoiceFlow's extraction-to-database workflow."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.db import Base
from src.processing import service
from src.processing.service import extract_invoice_record, save_invoice_record


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        yield db
    Base.metadata.drop_all(engine)
    engine.dispose()


def record(**overrides):
    data = {
        "vendor": "Acme Office Supplies",
        "invoice_number": "AC-101",
        "invoice_date": date(2026, 10, 1),
        "due_date": date(2026, 10, 15),
        "currency": "INR",
        "subtotal": Decimal("1000.00"),
        "tax_amount": Decimal("180.00"),
        "total_amount": Decimal("1180.00"),
        "confidence": 1.0,
        "extracted_text": "sample invoice",
        "source_filename": "invoice.pdf",
        "source_sha256": "a" * 64,
        "page_count": 1,
        "pdf_warnings": [],
        "validation": {
            "is_valid": True,
            "status": "ready",
            "errors": [],
            "warnings": [],
        },
    }
    data.update(overrides)
    return data


def test_extract_invoice_record_parses_and_hashes_pdf(monkeypatch):
    from src.extraction.pdf_reader import PDFText

    monkeypatch.setattr(
        service,
        "extract_pdf_text",
        lambda _: PDFText(
            text="Vendor: Acme Ltd\nInvoice Number: A-1",
            page_count=1,
            warnings=[],
        ),
    )
    result = extract_invoice_record("../invoice.pdf", b"%PDF-test")
    assert result["source_filename"] == "invoice.pdf"
    assert len(result["source_sha256"]) == 64
    assert result["page_count"] == 1
    assert result["vendor"] == "Acme Ltd"
    assert result["validation"]["status"] == "needs_review"


def test_extraction_rejects_non_pdf(monkeypatch):
    monkeypatch.setattr(
        service,
        "extract_pdf_text",
        lambda _: pytest.fail("PDF reader must not run for non-PDF files"),
    )
    with pytest.raises(ValueError, match="Only PDF"):
        extract_invoice_record("invoice.docx", b"not a PDF")


def test_save_invoice_and_skip_identical_file_duplicate(session):
    first = save_invoice_record(session, record())
    second = save_invoice_record(session, record(source_filename="copy.pdf"))

    assert first["saved"] is True
    assert first["duplicate"] is False
    assert second["saved"] is False
    assert second["duplicate"] is True
    assert "identical file content" in second["reason"]
    assert session.query(service.Invoice).count() == 1
    assert session.query(service.Vendor).count() == 1


def test_duplicate_vendor_invoice_key_is_case_and_space_insensitive(session):
    save_invoice_record(session, record())
    duplicate = save_invoice_record(
        session,
        record(
            vendor="  ACME   OFFICE SUPPLIES ",
            invoice_number="ac-101",
            source_sha256="b" * 64,
        ),
    )
    assert duplicate["duplicate"] is True
    assert "vendor and invoice number" in duplicate["reason"]
    assert session.query(service.Invoice).count() == 1


def test_incomplete_invoice_can_be_saved_for_manual_review(session):
    incomplete = record(
        vendor=None,
        invoice_number=None,
        invoice_date=None,
        subtotal=None,
        tax_amount=None,
        total_amount=None,
        source_sha256="c" * 64,
        validation={
            "is_valid": False,
            "status": "needs_review",
            "errors": ["Missing required fields."],
            "warnings": [],
        },
    )
    result = save_invoice_record(session, incomplete)
    saved = session.get(service.Invoice, result["invoice_id"])
    assert result["saved"] is True
    assert saved.invoice_number is None
    assert saved.vendor_id is None
    assert saved.status == "needs_review"
