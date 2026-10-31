"""PDF text extraction with safe, actionable error reporting."""
from dataclasses import dataclass
from io import BytesIO
import pdfplumber

@dataclass
class PDFText:
    text: str
    page_count: int
    warnings: list[str]

def extract_pdf_text(file_bytes: bytes) -> PDFText:
    """Extract selectable text from a PDF byte stream.

    Scanned/image-only PDFs return a warning; OCR is intentionally a later
    extension and is not silently claimed as supported here.
    """
    if not file_bytes:
        raise ValueError("The uploaded file is empty.")
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("This file does not appear to be a valid PDF.")
    pages_text = []
    warnings = []
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                raise ValueError("The PDF contains no pages.")
            for index, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    warnings.append(f"Page {index} contains no selectable text; it may be scanned.")
                pages_text.append(page_text)
            return PDFText("\n".join(pages_text).strip(), len(pdf.pages), warnings)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to read this PDF: {exc}") from exc
