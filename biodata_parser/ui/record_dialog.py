from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)


class RecordDialog(QDialog):
    def __init__(self, profile: dict, field_config: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.profile = profile
        self.field_config = field_config
        self.inputs: dict[str, QWidget] = {}
        self._reparse_requested = False

        self.setWindowTitle(f"Record: {profile['source_file_name']}")
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        info_label = QLabel(f"Source PDF: {profile['source_file_path']}\nStatus: {profile['review_status']}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        form_layout = QFormLayout()
        parsed = profile["parsed_json"]
        confidence = profile["confidence_json"]
        for field in field_config:
            key = field["key"]
            label = f"{field['display_name']} ({confidence.get(key, 0):.2f})"
            if field.get("multiline"):
                widget = QTextEdit()
                widget.setPlainText(str(parsed.get(key, "")))
            else:
                widget = QLineEdit(str(parsed.get(key, "")))
            self.inputs[key] = widget
            form_layout.addRow(label, widget)

        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)

        raw_text = QTextEdit()
        raw_text.setPlainText(profile["raw_text"])
        raw_text.setReadOnly(True)
        layout.addWidget(QLabel("Raw Extracted Text"))
        layout.addWidget(raw_text)

        actions = QHBoxLayout()
        self.reparse_button = QPushButton("Re-parse")
        self.reviewed_button = QPushButton("Save and Mark Reviewed")
        actions.addWidget(self.reparse_button)
        actions.addWidget(self.reviewed_button)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        self.reparse_button.clicked.connect(self._request_reparse)
        self.reviewed_button.clicked.connect(self._save_as_reviewed)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def get_manual_edits(self) -> dict:
        values: dict[str, str] = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QTextEdit):
                values[key] = widget.toPlainText().strip()
            else:
                values[key] = widget.text().strip()
        return values

    def is_reparse_requested(self) -> bool:
        return self._reparse_requested

    def _request_reparse(self) -> None:
        self._reparse_requested = True
        self.accept()

    def _save_as_reviewed(self) -> None:
        self.profile["review_status"] = "Reviewed"
        self.accept()
