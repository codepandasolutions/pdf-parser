from __future__ import annotations

import re

from biodata_parser.parsing.confidence import calculate_overall_confidence
from biodata_parser.parsing.text_normalizer import normalize_text, split_lines
from biodata_parser.parsing.validators import clean_value_for_type


SEPARATORS = r"[:=\-|–—]"


def _normalize_label(label: str) -> str:
    return re.sub(r"[\s.]+", " ", label.strip().lower()).strip()


def _build_label_pattern(label: str) -> str:
    parts = _normalize_label(label).split()
    escaped_parts = [re.escape(part) for part in parts]
    return r"[\s.]*".join(escaped_parts)


def extract_fields(raw_text: str, field_config: list[dict]) -> dict:
    normalized_text = normalize_text(raw_text)
    lines = split_lines(normalized_text)
    values: dict[str, str] = {}
    confidence: dict[str, float] = {}
    evidence: dict[str, dict] = {}
    missing_required: list[str] = []

    for field in field_config:
        key = field["key"]
        match = _extract_field_from_lines(lines, field)
        if match is None:
            regex_match = _extract_field_from_regex(normalized_text, field)
            if regex_match is not None:
                value = clean_value_for_type(regex_match, field.get("type", "string"))
                values[key] = value
                confidence[key] = field.get("confidence", {}).get("regex_match", 0.7)
                evidence[key] = {
                    "matched_label": None,
                    "source_line": regex_match,
                    "method": "regex",
                }
            elif field.get("required"):
                missing_required.append(key)
                confidence[key] = 0.0
            continue

        value, matched_label, source_line = match
        value = clean_value_for_type(value, field.get("type", "string"))
        values[key] = value
        confidence[key] = field.get("confidence", {}).get("label_match", 0.9)
        evidence[key] = {
            "matched_label": matched_label,
            "source_line": source_line,
            "method": "label",
        }

    return {
        "values": values,
        "confidence": confidence,
        "evidence": evidence,
        "missing_required": missing_required,
        "overall_confidence": calculate_overall_confidence(confidence),
    }


def _extract_field_from_lines(lines: list[str], field: dict) -> tuple[str, str, str] | None:
    labels = [_normalize_label(label) for label in field.get("labels", [])]
    pattern_cache = [
        re.compile(rf"^\s*{_build_label_pattern(label)}\s*{SEPARATORS}\s*(.+?)\s*$", re.IGNORECASE) for label in labels
    ]

    for index, line in enumerate(lines):
        normalized_line = _normalize_label(line)
        for label, pattern in zip(labels, pattern_cache, strict=False):
            direct_match = pattern.match(line)
            if direct_match:
                return direct_match.group(1), label, line
            if normalized_line == label:
                next_value = _collect_following_lines(lines, index, field)
                return next_value, label, line
    return None


def _collect_following_lines(lines: list[str], start_index: int, field: dict) -> str:
    if start_index + 1 >= len(lines):
        return ""

    if field.get("multiline"):
        max_lines = int(field.get("max_lines", 3))
        values: list[str] = []
        for candidate in lines[start_index + 1 : start_index + 1 + max_lines]:
            if not candidate.strip():
                break
            values.append(candidate.strip())
        return " ".join(values).strip()

    return lines[start_index + 1].strip()


def _extract_field_from_regex(text: str, field: dict) -> str | None:
    for regex_pattern in field.get("regex_patterns", []):
        match = re.search(regex_pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None
