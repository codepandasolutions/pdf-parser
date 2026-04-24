from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from biodata_parser.ui.main_window import run_app

    runtime_dir = project_root / "app_data_dev_runtime"
    os.environ.setdefault("BIODATA_PARSER_APP_DATA_DIR", str(runtime_dir))
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
