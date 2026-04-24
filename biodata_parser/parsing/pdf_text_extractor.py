from __future__ import annotations

from pathlib import Path

from biodata_parser.constants import DEFAULT_MIN_TEXT_LENGTH
from biodata_parser.parsing.ocr_extractor import extract_text_with_ocr


def extract_text_from_pdf(file_path: str) -> dict:
    file_path = str(Path(file_path))
    pymupdf_result = _try_pymupdf(file_path)
    if pymupdf_result["text"] and len(pymupdf_result["text"].strip()) >= DEFAULT_MIN_TEXT_LENGTH:
        return pymupdf_result

    pdfplumber_result = _try_pdfplumber(file_path)
    if pdfplumber_result["text"] and len(pdfplumber_result["text"].strip()) >= DEFAULT_MIN_TEXT_LENGTH:
        return pdfplumber_result

    ocr_result = extract_text_with_ocr(file_path)
    if ocr_result["text"].strip():
        return ocr_result

    return {
        "text": pymupdf_result["text"] or pdfplumber_result["text"] or "",
        "method": "failed",
        "pages": pymupdf_result["pages"] or pdfplumber_result["pages"],
        "errors": [*pymupdf_result["errors"], *pdfplumber_result["errors"], *ocr_result["errors"]],
    }


def _try_pymupdf(file_path: str) -> dict:
    try:
        import fitz
    except ImportError:
        return {"text": "", "method": "failed", "pages": [], "errors": ["PyMuPDF is not installed"]}

    pages: list[dict] = []
    try:
        with fitz.open(file_path) as document:
            for page_index, page in enumerate(document, start=1):
                page_text = page.get_text("text", sort=True)
                pages.append({"page": page_index, "text": page_text})
    except Exception as exc:  # pragma: no cover - PDF library behavior
        return {"text": "", "method": "failed", "pages": [], "errors": [f"PyMuPDF failed: {exc}"]}

    return {
        "text": "\n\n".join(page["text"] for page in pages).strip(),
        "method": "pymupdf",
        "pages": pages,
        "errors": [],
    }


def _try_pdfplumber(file_path: str) -> dict:
    try:
        import pdfplumber
    except ImportError:
        return {"text": "", "method": "failed", "pages": [], "errors": ["pdfplumber is not installed"]}

    pages: list[dict] = []
    try:
        with pdfplumber.open(file_path) as document:
            for page_index, page in enumerate(document.pages, start=1):
                text = page.extract_text(layout=True) or ""
                pages.append({"page": page_index, "text": text})
    except Exception as exc:  # pragma: no cover - PDF library behavior
        return {"text": "", "method": "failed", "pages": [], "errors": [f"pdfplumber failed: {exc}"]}

    return {
        "text": "\n\n".join(page["text"] for page in pages).strip(),
        "method": "pdfplumber",
        "pages": pages,
        "errors": [],
    }
