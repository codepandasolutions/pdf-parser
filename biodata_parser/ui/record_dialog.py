from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QPushButton,
    QSizePolicy,
    QSplitter,
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
        self._mark_reviewed_requested = False
        self._save_requested = False

        self.setWindowTitle(f"Record: {profile['source_file_name']}")
        self.resize(1180, 780)

        layout = QVBoxLayout(self)
        shell = QWidget()
        shell.setObjectName("DialogShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(16)

        hero_card = QWidget()
        hero_card.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        hero_layout.setSpacing(6)
        title = QLabel(profile["source_file_name"])
        title.setObjectName("HeroTitle")
        subtitle = QLabel(f"Source PDF: {profile['source_file_path']}")
        subtitle.setObjectName("HeroSubtitle")
        status_chip = QLabel(f"Status: {profile['review_status']}  |  Confidence: {profile['overall_confidence']:.2f}")
        status_chip.setObjectName("ChipLabel")
        status_chip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addWidget(status_chip, alignment=Qt.AlignLeft)
        shell_layout.addWidget(hero_card)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignTop | Qt.AlignLeft)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(14)
        parsed = profile["parsed_json"]
        confidence = profile["confidence_json"]
        for field in field_config:
            key = field["key"]
            label = f"{field['display_name']} ({confidence.get(key, 0):.2f})"
            if field.get("multiline"):
                widget = QTextEdit()
                widget.setMinimumHeight(80)
                widget.setPlainText(str(parsed.get(key, "")))
            else:
                widget = QLineEdit(str(parsed.get(key, "")))
            self.inputs[key] = widget
            form_layout.addRow(label, widget)

        form_widget = QWidget()
        form_widget.setLayout(form_layout)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setWidget(form_widget)
        form_card = QWidget()
        form_card.setObjectName("PanelCard")
        form_card_layout = QVBoxLayout(form_card)
        form_card_layout.setContentsMargins(18, 18, 18, 18)
        form_card_layout.setSpacing(10)
        form_title = QLabel("Review Extracted Fields")
        form_title.setObjectName("SectionTitle")
        form_hint = QLabel("Edit values where needed before saving or marking the record as reviewed.")
        form_hint.setObjectName("SectionHint")
        form_card_layout.addWidget(form_title)
        form_card_layout.addWidget(form_hint)
        form_card_layout.addWidget(form_scroll)

        raw_text = QTextEdit()
        raw_text.setPlainText(profile["raw_text"])
        raw_text.setReadOnly(True)
        raw_card = QWidget()
        raw_card.setObjectName("RawTextCard")
        raw_card_layout = QVBoxLayout(raw_card)
        raw_card_layout.setContentsMargins(18, 18, 18, 18)
        raw_card_layout.setSpacing(10)
        raw_title = QLabel("Raw Extracted Text")
        raw_title.setObjectName("SectionTitle")
        raw_hint = QLabel("Use this panel to cross-check parsing issues against the original extracted content.")
        raw_hint.setObjectName("SectionHint")
        raw_card_layout.addWidget(raw_title)
        raw_card_layout.addWidget(raw_hint)
        raw_card_layout.addWidget(raw_text)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(form_card)
        splitter.addWidget(raw_card)
        splitter.setSizes([640, 420])
        shell_layout.addWidget(splitter, stretch=1)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.reparse_button = QPushButton("Re-parse")
        self.reparse_button.setObjectName("GhostButton")
        self.reviewed_button = QPushButton("Save and Mark Reviewed")
        self.reviewed_button.setObjectName("PrimaryButton")
        actions.addWidget(self.reparse_button)
        actions.addWidget(self.reviewed_button)
        actions.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        if save_button is not None:
            save_button.setText("Save Draft Changes")
        if cancel_button is not None:
            cancel_button.setObjectName("GhostButton")
        shell_layout.addLayout(actions)
        shell_layout.addWidget(buttons)
        layout.addWidget(shell)

        self.reparse_button.clicked.connect(self._request_reparse)
        self.reviewed_button.clicked.connect(self._save_as_reviewed)
        buttons.accepted.connect(self._save_changes)
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

    def should_mark_reviewed(self) -> bool:
        return self._mark_reviewed_requested

    def is_save_requested(self) -> bool:
        return self._save_requested

    def _save_changes(self) -> None:
        self._save_requested = True
        self.accept()

    def _request_reparse(self) -> None:
        self._reparse_requested = True
        self.accept()

    def _save_as_reviewed(self) -> None:
        self._mark_reviewed_requested = True
        self.accept()
