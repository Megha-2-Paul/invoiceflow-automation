"""Rule-based extraction for common invoice text layouts."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y")

def _first(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip(" :#\t")
    return None

def _parse_date(value: str | None):
    if not value:
        return None
    cleaned = value.strip().replace(",", "")
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None

def _parse_amount(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = value.replace(",", "").replace(" ", "").strip()
    cleaned = re.sub(r"^(USD|INR|EUR|GBP|\$|₹|€|£)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"(USD|INR|EUR|GBP)$", "", cleaned, flags=re.I)
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    try:
        amount = Decimal(cleaned)
        return -amount if negative else amount
    except InvalidOperation:
        return None

def parse_invoice_text(text: str) -> dict[str, Any]:
    """Extract likely invoice fields; all values require human review."""
    invoice_number = _first([
        r"(?:invoice\s*(?:number|no\.?|#)|bill\s*(?:number|no\.?|#))\s*[:#-]?\s*([A-Z0-9][A-Z0-9/_-]+)",
    ], text)
    vendor = _first([
        r"(?:vendor|supplier|from|billed\s*by)\s*[:\-]\s*([^\n]+)",
    ], text)
    invoice_date_raw = _first([
        r"(?:invoice\s*date|date\s*of\s*issue|issued\s*on)\s*[:\-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
    ], text)
    due_date_raw = _first([
        r"(?:due\s*date|payment\s*due)\s*[:\-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
    ], text)
    def amount(label_patterns):
        raw = _first(label_patterns, text)
        return _parse_amount(raw)
    total = amount([r"\b(?:grand\s*total|total\s*due|amount\s*due|invoice\s*total|total)\b\s*[:\-]?\s*([₹$€£]?\s*\(?-?[\d,]+\.\d{2}\)?)"])
    tax = amount([r"(?:tax|gst|vat|sales\s*tax)\s*[:\-]?\s*([₹$€£]?\s*\(?-?[\d,]+\.\d{2}\)?)"])
    total = amount([r"(?:grand\s*total|total\s*due|amount\s*due|invoice\s*total|total)\s*[:\-]?\s*([₹$€£]?\s*\(?-?[\d,]+\.\d{2}\)?)"])
    currency = "INR" if "₹" in text or re.search(r"\bINR\b", text, re.I) else (
        "EUR" if "€" in text else "GBP" if "£" in text else "USD" if "$" in text else "USD"
    )
    found = [invoice_number, vendor, invoice_date_raw, subtotal, tax, total]
    confidence = round(sum(value is not None for value in found) / len(found), 2)
    return {
        "invoice_number": invoice_number,
        "vendor": vendor,
        "invoice_date": _parse_date(invoice_date_raw),
        "invoice_date_raw": invoice_date_raw,
        "due_date": _parse_date(due_date_raw),
        "due_date_raw": due_date_raw,
        "currency": currency,
        "subtotal": subtotal,
        "tax_amount": tax,
        "total_amount": total,
        "confidence": confidence,
        "extracted_text": text,
    }
