from __future__ import annotations

import re
import unicodedata


def normalize_text(raw_text: str) -> str:
    text = unicodedata.normalize("NFKC", raw_text or "")
    text = text.replace("\t", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[|=]", ":", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(raw_text: str) -> list[str]:
    return [line.strip() for line in normalize_text(raw_text).splitlines() if line.strip()]
