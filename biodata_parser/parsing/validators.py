from __future__ import annotations

import re
from datetime import datetime


DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y")


def clean_value_for_type(value: str, field_type: str) -> str:
    value = value.strip().rstrip(":|-")
    value = re.sub(r"\s{2,}", " ", value)
    if field_type == "phone":
        digits = re.sub(r"[^\d+]", "", value)
        if digits.startswith("91") and not digits.startswith("+91"):
            digits = f"+{digits}"
        return digits
    if field_type == "date":
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(value, date_format).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return value
