from __future__ import annotations

import re
from datetime import datetime


DATE_FORMATS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d.%m.%y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
    "%B %d %Y",
)


def clean_value_for_type(value: str, field_type: str) -> str:
    value = value.strip().rstrip(":|-")
    value = re.sub(r"\s{2,}", " ", value)
    if field_type == "phone":
        candidates = extract_phone_candidates(value)
        return candidates[0] if candidates else value
    if field_type == "date":
        normalized_date = normalize_date_string(value)
        if normalized_date is not None:
            return normalized_date
    if field_type == "email":
        emails = extract_email_candidates(value)
        return emails[0] if emails else value.lower()
    if field_type == "string":
        return strip_inline_field_labels(value)
    return value


def strip_inline_field_labels(value: str) -> str:
    return re.sub(
        r"\s*(?:weight|occupation|education|salary|address|contact details|contact no|phone number)\s*[:=-].*$",
        "",
        value,
        flags=re.IGNORECASE,
    ).strip()


def normalize_date_string(value: str) -> str | None:
    candidate = value.strip()
    candidate = candidate.replace(",", " ")
    candidate = re.sub(r"(\d)(st|nd|rd|th)", r"\1", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", candidate)
    candidate = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", candidate)
    candidate = re.sub(r"\s{2,}", " ", candidate).strip()

    for date_format in DATE_FORMATS:
        try:
            parsed = datetime.strptime(candidate, date_format)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    match = re.search(
        r"\b\d{1,4}[./-]\d{1,2}[./-]\d{1,4}\b|\b\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{2,4}\b",
        candidate,
        flags=re.IGNORECASE,
    )
    if match:
        return normalize_date_string(match.group(0))

    compact_candidate = re.sub(r"[\./]", "-", candidate)
    for date_format in ("%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(compact_candidate, date_format)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def extract_phone_candidates(value: str) -> list[str]:
    matches = re.findall(r"(?:\+91[-\s]?)?[6-9](?:[\s-]?\d){9}", value)
    normalized: list[str] = []
    seen: set[str] = set()
    for match in matches:
        digits = re.sub(r"[^\d+]", "", match)
        if digits.startswith("91") and not digits.startswith("+91"):
            digits = f"+{digits}"
        if digits not in seen:
            normalized.append(digits)
            seen.add(digits)
    return normalized


def extract_email_candidates(value: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value.lower())
