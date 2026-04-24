from __future__ import annotations

from pathlib import Path

from biodata_parser.constants import APP_NAME


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_default_config_path() -> Path:
    return get_project_root() / "config" / "default_fields.yaml"


def get_app_data_dir() -> Path:
    return Path.home() / "app_data_dev" / APP_NAME
