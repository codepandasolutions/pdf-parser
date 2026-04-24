from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout


class SettingsDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        label = QLabel(
            "Version 1 does not support editing field configuration from the UI.\n"
            "Update the YAML config file directly if field changes are needed."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
