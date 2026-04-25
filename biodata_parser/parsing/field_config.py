from __future__ import annotations

from pathlib import Path

import yaml

from biodata_parser.paths import get_default_config_path


def load_field_config(config_path: Path | None = None) -> list[dict]:
    path = config_path or get_default_config_path()
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload.get("fields", [])


def sync_field_config(config_path: Path, default_config_path: Path | None = None) -> list[dict]:
    default_path = default_config_path or get_default_config_path()
    default_fields = load_field_config(default_path)
    current_fields = load_field_config(config_path) if config_path.exists() else []

    current_by_key = {field["key"]: field for field in current_fields if "key" in field}
    merged_fields: list[dict] = []

    for default_field in default_fields:
        current_field = current_by_key.get(default_field["key"])
        if current_field is None:
            merged_fields.append(default_field)
            continue
        merged = dict(default_field)
        merged.update(current_field)
        merged_fields.append(merged)

    existing_keys = {field["key"] for field in merged_fields if "key" in field}
    for current_field in current_fields:
        key = current_field.get("key")
        if key and key not in existing_keys:
            merged_fields.append(current_field)

    save_field_config(config_path, merged_fields)
    return merged_fields


def save_field_config(config_path: Path, fields: list[dict]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump({"fields": fields}, handle, sort_keys=False, allow_unicode=True)


def build_known_labels(field_config: list[dict]) -> set[str]:
    labels: set[str] = set()
    for field in field_config:
        for label in field.get("labels", []):
            labels.add(label)
    return labels
