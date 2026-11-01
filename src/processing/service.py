"""End-to-end invoice extraction and persistence workflow."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models import Invoice, Vendor
from src.extraction.parser import parse_invoice_text
from src.extraction.pdf_reader import extract_pdf_text
from src.validation.rules import validate_invoice


def normalize_vendor_name(value: str) -> str:
    """Normalize vendor names for duplicate matching."""
    return re.sub(r"\s+", " ", value).strip().casefold().strip().casefold()


def extract_invoice_record(filename: str, file_bytes: bytes) -> dict[str, Any]:
    """Extract, validate and annotate one uploaded PDF without saving it."""
    safe_filename = Path(filename).name
    if Path(safe_filename).suffix.casefold() != ".pdf":
        raise ValueError("Only PDF invoices are supported.")
    digest = hashlib.sha256(file_bytes).hexdigest()
    pdf_result = extract_pdf_text(file_bytes)
    if not pdf_result.text.strip():
        raise ValueError("No selectable text was found. This may be a scanned PDF; OCR support is planned.")
    parsed = parse_invoice_text(pdf_result.text)
    validation = validate_invoice(parsed)
    parsed.update({
        "source_filename": safe_filename,
        "source_sha256": digest,
        "page_count": pdf_result.page_count,
        "pdf_warnings": pdf_result.warnings,
        "validation": validation,
    })
    return parsed


def find_existing_invoice(session: Session, record: dict[str, Any]) -> tuple[Invoice | None, str | None]:
    """Find an existing invoice by identical file hash or vendor/invoice key."""
    existing = session.scalar(
        select(Invoice).where(Invoice.source_sha256 == record["source_sha256"])
    )
    if existing:
        return existing, "An invoice with identical file content is already stored."

    vendor_name = record.get("vendor")
    invoice_number = record.get("invoice_number")
    if vendor_name and invoice_number:
        normalized = normalize_vendor_name(vendor_name)
        vendor = session.scalar(
            select(Vendor).where(Vendor.normalized_name == normalized)
        )
        if vendor:
            existing = session.scalar(
                select(Invoice).where(
                    Invoice.vendor_id == vendor.id,
                    func.lower(Invoice.invoice_number) == invoice_number.casefold(),
                )
            )
            if existing:
                return existing, "This vendor and invoice number are already stored."
    return None, None


def save_invoice_record(session: Session, record: dict[str, Any]) -> dict[str, Any]:
    """Persist a parsed invoice, skipping duplicates and retaining review notes."""
    existing, reason = find_existing_invoice(session, record)
    if existing:
        return {"saved": False, "duplicate": True, "reason": reason, "invoice_id": existing.id}

    vendor = None
    vendor_name = record.get("vendor")
    if vendor_name:
        normalized = normalize_vendor_name(vendor_name)
        vendor = session.scalar(
            select(Vendor).where(Vendor.normalized_name == normalized)
        )
        if vendor is None:
            vendor = Vendor(name=vendor_name.strip(), normalized_name=normalized)
            session.add(vendor)
            session.flush()

    validation = record["validation"]
    notes = {
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "pdf_warnings": record.get("pdf_warnings", []),
        "confidence": record.get("confidence"),
        "page_count": record.get("page_count"),
    }
    invoice = Invoice(
        vendor_id=vendor.id if vendor else None,
        invoice_number=record.get("invoice_number"),
        invoice_date=record.get("invoice_date"),
        due_date=record.get("due_date"),
        currency=record.get("currency") or "USD",
        subtotal=record.get("subtotal"),
        tax_amount=record.get("tax_amount"),
        total_amount=record.get("total_amount"),
        source_filename=record["source_filename"],
        source_sha256=record["source_sha256"],
        status=validation["status"],
        validation_notes=json.dumps(notes, default=str),
        extracted_text=record.get("extracted_text"),
    )
    try:
        session.add(invoice)
        session.commit()
        return {"saved": True, "duplicate": False, "reason": None, "invoice_id": invoice.id}
    except Exception:
        session.rollback()
        raise
