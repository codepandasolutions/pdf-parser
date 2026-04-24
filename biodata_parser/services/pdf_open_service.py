from __future__ import annotations

from pathlib import Path


def ensure_pdf_exists(file_path: str) -> Path:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing PDF file: {file_path}")
    return path
