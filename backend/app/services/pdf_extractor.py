"""
Document Processor (Day 1 scope): extracts raw text from PDF, CSV, and plain
text uploads. This is Stage 1 (Extract) of the AI pipeline described in the
spec — it preserves original source information so later stages (Day 2+) can
cite exact source text and page numbers.

Uses PyMuPDF (fitz) as the primary PDF backend with pdfplumber as a fallback,
per the recommended stack.
"""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from a PDF, page by page. Returns (text, page_count).

    Text is prefixed per-page with a marker like `[PAGE 1]` so downstream
    stages can preserve traceability (source page references).
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            pages.append(f"[PAGE {i}]\n{text.strip()}")
        doc.close()
        full_text = "\n\n".join(pages).strip()
        if full_text:
            return full_text, len(pages)
    except Exception:
        pass

    # Fallback: pdfplumber
    try:
        import pdfplumber

        pages = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(f"[PAGE {i}]\n{text.strip()}")
        full_text = "\n\n".join(pages).strip()
        return full_text, len(pages)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")


def extract_text_from_csv(file_bytes: bytes) -> tuple[str, int]:
    """Extract a readable text representation from a CSV upload."""
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")

    lines = [f"Columns: {', '.join(str(c) for c in df.columns)}"]
    for idx, row in df.iterrows():
        row_text = ", ".join(f"{col}: {row[col]}" for col in df.columns)
        lines.append(f"Row {idx + 1}: {row_text}")
    text = "\n".join(lines)
    return text, len(df)


def extract_text_from_plain(file_bytes: bytes) -> tuple[str, int]:
    """Decode a plain text upload."""
    text = file_bytes.decode("utf-8", errors="ignore")
    return text.strip(), 1


def detect_document_type(filename: str, content_type: Optional[str]) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith(".csv"):
        return "csv"
    if lower.endswith((".txt", ".md")):
        return "text"
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    if content_type:
        if "pdf" in content_type:
            return "pdf"
        if "csv" in content_type:
            return "csv"
        if "text" in content_type:
            return "text"
        if "image" in content_type:
            return "image"
    return "unknown"


def extract_text(filename: str, content_type: Optional[str], file_bytes: bytes) -> tuple[str, str, int]:
    """Dispatch to the right extractor based on document type.

    Returns (document_type, extracted_text, page_or_row_count).
    """
    doc_type = detect_document_type(filename, content_type)

    if doc_type == "pdf":
        text, count = extract_text_from_pdf(file_bytes)
    elif doc_type == "csv":
        text, count = extract_text_from_csv(file_bytes)
    elif doc_type == "text":
        text, count = extract_text_from_plain(file_bytes)
    elif doc_type == "image":
        # Image OCR / vision extraction is out of scope for Day 1.
        # Placeholder so uploads don't fail; wire up an AI vision call on
        # Day 2+ via the AIProvider abstraction.
        text = (
            "[Image uploaded — visual extraction not yet implemented. "
            "This will be handled by the AI vision pipeline.]"
        )
        count = 1
    else:
        raise ValueError(f"Unsupported file type for '{filename}'")

    return doc_type, text, count
