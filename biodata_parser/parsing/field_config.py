from __future__ import annotations

from pathlib import Path

import yaml

from biodata_parser.paths import get_default_config_path


def load_field_config(config_path: Path | None = None) -> list[dict]:
    path = config_path or get_default_config_path()
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload.get("fields", [])
