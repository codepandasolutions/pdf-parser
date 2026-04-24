from __future__ import annotations

import re

from biodata_parser.parsing.field_config import build_known_labels
from biodata_parser.parsing.confidence import calculate_overall_confidence
from biodata_parser.parsing.text_normalizer import normalize_text, split_lines
from biodata_parser.parsing.validators import (
    clean_value_for_type,
    extract_phone_candidates,
    normalize_date_string,
)


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
    known_labels = {_normalize_label(label) for label in build_known_labels(field_config)}
    values: dict[str, str] = {}
    confidence: dict[str, float] = {}
    evidence: dict[str, dict] = {}
    missing_required: list[str] = []

    for field in field_config:
        key = field["key"]
        match = _extract_field_from_lines(lines, field, known_labels)
        if match is None:
            heuristic_match = _extract_field_from_heuristics(lines, raw_text, field, known_labels)
            if heuristic_match is not None:
                value = clean_value_for_type(heuristic_match, field.get("type", "string"))
                if value:
                    values[key] = value
                    confidence[key] = field.get("confidence", {}).get("regex_match", 0.7)
                    evidence[key] = {
                        "matched_label": None,
                        "source_line": heuristic_match,
                        "method": "heuristic",
                    }
                    continue

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


def _extract_field_from_lines(lines: list[str], field: dict, known_labels: set[str]) -> tuple[str, str, str] | None:
    labels = [_normalize_label(label) for label in field.get("labels", [])]
    pattern_cache = [
        re.compile(rf"^\s*{_build_label_pattern(label)}\s*{SEPARATORS}\s*(.+?)\s*$", re.IGNORECASE) for label in labels
    ]

    for index, line in enumerate(lines):
        normalized_line = _normalize_label(line)
        for label, pattern in zip(labels, pattern_cache, strict=False):
            direct_match = pattern.match(line)
            if direct_match:
                value = _postprocess_line_value(direct_match.group(1), field)
                return value, label, line
            if normalized_line == label:
                next_value = _collect_following_lines(lines, index, field, known_labels)
                return next_value, label, line
    return None


def _collect_following_lines(lines: list[str], start_index: int, field: dict, known_labels: set[str]) -> str:
    if start_index + 1 >= len(lines):
        return ""

    if field.get("multiline"):
        max_lines = int(field.get("max_lines", 3))
        values: list[str] = []
        for candidate in lines[start_index + 1 : start_index + 1 + max_lines]:
            normalized_candidate = _normalize_label(candidate)
            if not candidate.strip():
                break
            if field.get("stop_at_next_label", True) and _line_looks_like_label(normalized_candidate, known_labels):
                break
            values.append(candidate.strip())
        return " ".join(values).strip()

    next_line = lines[start_index + 1].strip()
    if _line_looks_like_label(_normalize_label(next_line), known_labels):
        return ""
    return next_line


def _line_looks_like_label(normalized_line: str, known_labels: set[str]) -> bool:
    if normalized_line in known_labels:
        return True

    for known_label in known_labels:
        if normalized_line.startswith(f"{known_label}:"):
            return True
        if normalized_line.startswith(f"{known_label} -"):
            return True
        if normalized_line.startswith(f"{known_label} ="):
            return True
    return False


def _extract_field_from_regex(text: str, field: dict) -> str | None:
    if field.get("key") == "age":
        return None
    for regex_pattern in field.get("regex_patterns", []):
        match = re.search(regex_pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _extract_field_from_heuristics(lines: list[str], raw_text: str, field: dict, known_labels: set[str]) -> str | None:
    key = field.get("key")
    if key == "full_name":
        return _extract_heading_name(lines, known_labels)
    if key == "date_of_birth":
        return _extract_date_candidate(raw_text)
    return None


def _extract_heading_name(lines: list[str], known_labels: set[str]) -> str | None:
    ignored_headings = {
        "bio data",
        "biodata",
        "personal details",
        "about me",
        "family background",
        "family details",
        "expectations",
        "contact details",
        "education",
        "occupation",
    }
    for line in lines[:8]:
        candidate = line.strip()
        normalized = _normalize_label(candidate)
        if not candidate or normalized in ignored_headings or _line_looks_like_label(normalized, known_labels):
            continue
        if any(char.isdigit() for char in candidate):
            continue
        words = [word for word in re.split(r"\s+", candidate) if word]
        if not (2 <= len(words) <= 5):
            continue
        if any(len(word) <= 1 for word in words):
            continue
        if all(re.fullmatch(r"[A-Za-z.'’-]+", word) for word in words):
            return candidate.title() if candidate.isupper() else candidate
    return None


def _extract_date_candidate(raw_text: str) -> str | None:
    candidates = re.findall(
        r"\b\d{1,4}[./-]\d{1,2}[./-]\d{1,4}\b|\b\d{1,2}(?:st|nd|rd|th)?[A-Za-z]+\s*,?\s*\d{2,4}\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December),?\s+\d{2,4}\b",
        raw_text,
        flags=re.IGNORECASE,
    )
    for candidate in candidates:
        normalized = normalize_date_string(candidate)
        if normalized:
            return candidate
    return None


def _postprocess_line_value(value: str, field: dict) -> str:
    key = field.get("key")
    field_type = field.get("type", "string")

    if key == "alternate_contact_number":
        candidates = extract_phone_candidates(value)
        return candidates[1] if len(candidates) > 1 else (candidates[0] if candidates else value)

    if field_type == "phone":
        candidates = extract_phone_candidates(value)
        return candidates[0] if candidates else value

    if key == "age":
        match = re.search(r"\b(\d{1,2})\b", value)
        return match.group(1) if match else ""

    if key == "height":
        match = re.search(
            r"\b\d\s*(?:ft|feet|'|’)?\s*\d{0,2}\s*(?:in|inch|inches|\"|”)?\b|\b\d{2,3}\s*cm\b",
            value,
            flags=re.IGNORECASE,
        )
        return match.group(0).strip() if match else value

    if key == "weight":
        match = re.search(r"\b\d{2,3}\s*(?:kg|kgs)\b", value, flags=re.IGNORECASE)
        return match.group(0).strip() if match else value

    if key == "date_of_birth":
        candidate = _extract_date_candidate(value)
        return candidate or value

    return value
