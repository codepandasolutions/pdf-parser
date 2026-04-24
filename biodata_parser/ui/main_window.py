from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from biodata_parser.logging_config import configure_logging


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Biodata Parser")
        self.resize(1000, 700)
        self.setCentralWidget(QLabel("Biodata Parser Desktop skeleton"))


def run_app() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
