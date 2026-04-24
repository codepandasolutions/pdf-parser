from __future__ import annotations

import csv
from pathlib import Path

from biodata_parser.db.repository import ProfileRepository
from biodata_parser.parsing.field_config import load_field_config


def export_profiles_to_csv(
    repository: ProfileRepository,
    config_path: Path,
    destination_path: Path,
    profiles: list[dict] | None = None,
) -> Path:
    rows = profiles or repository.list_profiles()
    fields = load_field_config(config_path)
    fieldnames = [field["csv_column"] for field in fields] + [
        "Source File",
        "Review Status",
        "Overall Confidence",
    ]

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with destination_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for profile in rows:
            row = {}
            parsed = profile["parsed_json"]
            for field in fields:
                row[field["csv_column"]] = parsed.get(field["key"], "")
            row["Source File"] = profile["source_file_name"]
            row["Review Status"] = profile["review_status"]
            row["Overall Confidence"] = profile["overall_confidence"]
            writer.writerow(row)
    return destination_path
