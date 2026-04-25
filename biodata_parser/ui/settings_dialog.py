from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget


class SettingsDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(520, 220)
        layout = QVBoxLayout(self)
        shell = QWidget()
        shell.setObjectName("DialogShell")
        shell_layout = QVBoxLayout(shell)
        card = QWidget()
        card.setObjectName("PanelCard")
        card_layout = QVBoxLayout(card)
        title = QLabel("Settings")
        title.setObjectName("SectionTitle")
        label = QLabel(
            "Version 1 does not support editing field configuration from the UI.\n"
            "Update the YAML config file directly if field changes are needed."
        )
        label.setWordWrap(True)
        label.setObjectName("SectionHint")
        card_layout.addWidget(title)
        card_layout.addWidget(label)
        shell_layout.addWidget(card)
        layout.addWidget(shell)
