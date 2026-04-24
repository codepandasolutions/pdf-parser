from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def ensure_pdf_exists(file_path: str) -> Path:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing PDF file: {file_path}")
    return path


def open_pdf(file_path: str) -> None:
    path = ensure_pdf_exists(file_path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return
    subprocess.Popen(["xdg-open", str(path)])
