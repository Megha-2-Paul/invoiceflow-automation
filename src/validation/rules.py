"""Deterministic invoice quality checks and duplicate heuristics."""
from decimal import Decimal
from typing import Any

REQUIRED_FIELDS = ("invoice_number", "vendor", "invoice_date", "total_amount")

def validate_invoice(data: dict[str, Any], *, tolerance: Decimal = Decimal("0.02")) -> dict[str, Any]:
    """Return status, issues and warnings without mutating extracted data."""
    errors: list[str] = []
    warnings: list[str] = []
    for field in REQUIRED_FIELDS:
        if data.get(field) in (None, ""):
            errors.append(f"Missing required field: {field.replace('_', ' ')}.")
    subtotal = data.get("subtotal")
    tax = data.get("tax_amount")
    total = data.get("total_amount")
    if total is not None and total <= 0:
        errors.append("Invoice total must be greater than zero.")
    if subtotal is not None and subtotal < 0:
        errors.append("Subtotal cannot be negative.")
    if tax is not None and tax < 0:
        warnings.append("Tax amount is negative; verify the source document.")
    if subtotal is not None and tax is not None and total is not None:
        difference = abs((subtotal + tax) - total)
        if difference > tolerance:
            errors.append(
                f"Amount mismatch: subtotal + tax differs from total by {difference:.2f}."
            )
    invoice_date = data.get("invoice_date")
    due_date = data.get("due_date")
    if invoice_date and due_date and due_date < invoice_date:
        warnings.append("Due date is earlier than invoice date; verify both dates.")
    confidence = data.get("confidence")
    if confidence is not None and confidence < 0.5:
        warnings.append("Low extraction coverage; manual review is strongly recommended.")
    return {
        "is_valid": not errors,
        "status": "ready" if not errors and not warnings else "needs_review",
        "errors": errors,
        "warnings": warnings,
    }

def find_duplicate_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag repeated source hashes or vendor/invoice-number combinations."""
    seen_hashes: dict[str, int] = {}
    seen_invoice_keys: dict[tuple[str, str], int] = {}
    duplicates = []
    for index, record in enumerate(records):
        reasons = []
        digest = record.get("source_sha256")
        vendor = str(record.get("vendor") or "").strip().casefold()
        number = str(record.get("invoice_number") or "").strip().casefold()
        if digest and digest in seen_hashes:
            reasons.append(f"Same file content as record {seen_hashes[digest] + 1}.")
        elif digest:
            seen_hashes[digest] = index
        key = (vendor, number)
        if vendor and number and key in seen_invoice_keys:
            reasons.append(f"Same vendor and invoice number as record {seen_invoice_keys[key] + 1}.")
        elif vendor and number:
            seen_invoice_keys[key] = index
        if reasons:
            duplicates.append({"index": index, "reasons": reasons})
    return duplicates
