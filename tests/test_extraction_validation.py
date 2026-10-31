"""Tests for invoice text parsing, validation and duplicate detection."""
from datetime import date
from decimal import Decimal

from src.extraction.parser import parse_invoice_text
from src.validation.rules import find_duplicate_candidates, validate_invoice

SAMPLE = """ACME Office Supplies
Vendor: ACME Office Supplies
Invoice Number: AC-2026-014
Invoice Date: 01/10/2026
Due Date: 15/10/2026
Subtotal: 1,000.00
GST: 180.00
Grand Total: 1,180.00
"""

def test_parse_common_invoice_fields():
    result = parse_invoice_text(SAMPLE)
    assert result["invoice_number"] == "AC-2026-014"
    assert result["vendor"] == "ACME Office Supplies"
    assert result["invoice_date"] == date(2026, 10, 1)
    assert result["due_date"] == date(2026, 10, 15)
    assert result["subtotal"] == Decimal("1000.00")
    assert result["tax_amount"] == Decimal("180.00")
    assert result["total_amount"] == Decimal("1180.00")

def test_validation_accepts_reconciled_invoice():
    parsed = parse_invoice_text(SAMPLE)
    result = validate_invoice(parsed)
    assert result["is_valid"] is True
    assert result["errors"] == []

def test_validation_flags_amount_mismatch():
    parsed = parse_invoice_text(SAMPLE.replace("Grand Total: 1,180.00", "Grand Total: 1,200.00"))
    result = validate_invoice(parsed)
    assert result["is_valid"] is False
    assert any("Amount mismatch" in issue for issue in result["errors"])

def test_validation_flags_missing_fields():
    result = validate_invoice({"confidence": 0.1})
    assert result["is_valid"] is False
    assert len(result["errors"]) == 4
    assert result["warnings"]

def test_duplicate_detection_by_hash_and_invoice_key():
    records = [
        {"vendor": "Acme Ltd", "invoice_number": "INV-1", "source_sha256": "abc"},
        {"vendor": "ACME LTD", "invoice_number": "inv-1", "source_sha256": "def"},
        {"vendor": "Other", "invoice_number": "INV-2", "source_sha256": "abc"},
    ]
    duplicates = find_duplicate_candidates(records)
    assert [item["index"] for item in duplicates] == [1, 2]
    assert "Same vendor and invoice number as record 1." in duplicates[0]["reasons"]
    assert "Same file content as record 1." in duplicates[1]["reasons"]
