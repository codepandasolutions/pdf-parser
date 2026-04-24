from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    from PySide6.QtWidgets import QApplication
    from biodata_parser.ui.main_window import MainWindow

    runtime_dir = project_root / "app_data_dev_runtime"
    os.environ.setdefault("BIODATA_PARSER_APP_DATA_DIR", str(runtime_dir))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QApplication([])
    window = MainWindow()
    print(window.windowTitle())
    print(window.app_paths.root)
    window.close()
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
