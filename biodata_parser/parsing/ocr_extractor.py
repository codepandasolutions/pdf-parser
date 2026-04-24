from __future__ import annotations


def extract_text_with_ocr(file_path: str) -> dict:
    return {
        "text": "",
        "method": "ocr",
        "pages": [],
        "errors": ["OCR not yet implemented"],
    }
