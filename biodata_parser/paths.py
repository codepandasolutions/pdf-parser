from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from biodata_parser.constants import APP_NAME


@dataclass(frozen=True)
class AppPaths:
    root: Path
    config_dir: Path
    uploads_dir: Path
    logs_dir: Path
    exports_dir: Path
    database_path: Path
    field_config_path: Path
    log_file_path: Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return get_project_root()


def get_default_config_path() -> Path:
    return get_runtime_base_dir() / "config" / "default_fields.yaml"


def get_app_data_dir() -> Path:
    override = os.environ.get("BIODATA_PARSER_APP_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return get_project_root() / "app_data_dev" / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def ensure_app_paths() -> AppPaths:
    root = get_app_data_dir()
    config_dir = root / "config"
    uploads_dir = root / "uploads" / "copied_pdf_files"
    logs_dir = root / "logs"
    exports_dir = root / "exports"

    for directory in (root, config_dir, uploads_dir, logs_dir, exports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    field_config_path = config_dir / "fields.yaml"
    if not field_config_path.exists():
        shutil.copy2(get_default_config_path(), field_config_path)
    else:
        from biodata_parser.parsing.field_config import sync_field_config

        sync_field_config(field_config_path, get_default_config_path())

    return AppPaths(
        root=root,
        config_dir=config_dir,
        uploads_dir=uploads_dir,
        logs_dir=logs_dir,
        exports_dir=exports_dir,
        database_path=root / "app.db",
        field_config_path=field_config_path,
        log_file_path=logs_dir / "app.log",
    )
