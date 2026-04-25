from __future__ import annotations

from pathlib import Path

import yaml

from biodata_parser.parsing.field_config import load_field_config, sync_field_config


def test_sync_field_config_adds_missing_default_fields(tmp_path: Path) -> None:
    default_config = tmp_path / "default_fields.yaml"
    default_config.write_text(
        yaml.safe_dump(
            {
                "fields": [
                    {"key": "full_name", "display_name": "Full Name", "labels": ["name"]},
                    {"key": "occupation", "display_name": "Occupation", "labels": ["occupation"]},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    runtime_config = tmp_path / "fields.yaml"
    runtime_config.write_text(
        yaml.safe_dump({"fields": [{"key": "full_name", "display_name": "Name", "labels": ["name"]}]}, sort_keys=False),
        encoding="utf-8",
    )

    synced = sync_field_config(runtime_config, default_config)

    assert [field["key"] for field in synced] == ["full_name", "occupation"]
    assert load_field_config(runtime_config)[1]["key"] == "occupation"
