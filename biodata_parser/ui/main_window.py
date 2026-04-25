from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from biodata_parser.constants import (
    REVIEW_STATUS_FAILED,
    REVIEW_STATUS_NEEDS_REVIEW,
    REVIEW_STATUS_PARSED,
    REVIEW_STATUS_REVIEWED,
)
from biodata_parser.db.database import connect_database, initialize_database
from biodata_parser.db.repository import ProfileRepository
from biodata_parser.logging_config import configure_logging
from biodata_parser.parsing.field_config import load_field_config
from biodata_parser.paths import ensure_app_paths
from biodata_parser.services.export_service import export_profiles_to_csv
from biodata_parser.services.import_service import ImportService
from biodata_parser.services.pdf_open_service import open_pdf
from biodata_parser.services.update_service import check_for_updates
from biodata_parser.ui.record_dialog import RecordDialog
from biodata_parser.ui.settings_dialog import SettingsDialog
from biodata_parser.ui.table_model import RecordsTableModel
from biodata_parser.ui.theme import apply_app_theme


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_paths = ensure_app_paths()
        self.connection = connect_database(self.app_paths.database_path)
        initialize_database(self.connection)
        self.repository = ProfileRepository(self.connection)
        self.import_service = ImportService(self.repository, self.app_paths)
        self.field_config = load_field_config(self.app_paths.field_config_path)

        self.setWindowTitle("Biodata Parser")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 760)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", REVIEW_STATUS_PARSED, REVIEW_STATUS_NEEDS_REVIEW, REVIEW_STATUS_REVIEWED, REVIEW_STATUS_FAILED]
        )
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search name, phone, city, education, occupation...")
        self.search_box.setClearButtonEnabled(True)

        self.table_model = RecordsTableModel(self._build_columns())
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(False)
        self.table_view.setWordWrap(False)
        self.table_view.setSortingEnabled(False)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.doubleClicked.connect(self.open_selected_record)

        self.total_records_card, self.total_records_label = self._create_summary_card("Records", "0")
        self.review_queue_card, self.review_queue_label = self._create_summary_card("Needs Review", "0")
        self.reviewed_card, self.reviewed_label = self._create_summary_card("Reviewed", "0")
        self.failed_card, self.failed_label = self._create_summary_card("Failed", "0")

        central_widget = QWidget()
        central_widget.setObjectName("AppShell")
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(24, 24, 24, 18)
        central_layout.setSpacing(18)
        central_layout.addWidget(self._build_hero_card())
        central_layout.addWidget(self._build_filters_card())
        central_layout.addWidget(self._build_summary_row())
        central_layout.addWidget(self._build_table_card(), stretch=1)
        self.setCentralWidget(central_widget)
        self.setStatusBar(QStatusBar())

        self.status_filter.currentTextChanged.connect(self.reload_records)
        self.search_box.textChanged.connect(self.reload_records)

        self.reload_records()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.connection.close()
        super().closeEvent(event)

    def import_pdf(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
        try:
            profile = self.import_service.import_pdf(file_path)
        except Exception as exc:
            self._show_error("Import failed", str(exc))
            return
        self.statusBar().showMessage(f"Imported {profile['source_file_name']}", 5000)
        self.reload_records()

    def import_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Import Folder")
        if not folder_path:
            return
        try:
            results = self.import_service.import_folder(folder_path)
        except Exception as exc:
            self._show_error("Import folder failed", str(exc))
            return
        self.statusBar().showMessage(f"Imported {len(results)} PDF(s) from folder", 5000)
        self.reload_records()

    def export_csv(self) -> None:
        default_name = f"biodata_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            str(self.app_paths.exports_dir / default_name),
            "CSV Files (*.csv)",
        )
        if not destination:
            return
        try:
            export_profiles_to_csv(
                repository=self.repository,
                config_path=self.app_paths.field_config_path,
                destination_path=Path(destination),
                profiles=self.table_model.rows,
            )
        except Exception as exc:
            self._show_error("Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Exported CSV to {destination}", 5000)

    def view_selected_pdf(self) -> None:
        profile = self._get_selected_profile()
        if profile is None:
            self._show_error("No selection", "Please select a record first.")
            return
        try:
            open_pdf(profile["source_file_path"])
        except Exception as exc:
            self._show_error("Open PDF failed", str(exc))

    def open_selected_record(self, *_args) -> None:
        profile = self._get_selected_profile()
        if profile is None:
            self._show_error("No selection", "Please select a record first.")
            return

        dialog = RecordDialog(profile, self.field_config, self)
        if dialog.exec() == dialog.Accepted:
            if dialog.is_reparse_requested():
                overwrite = True
                if profile["manual_edits_json"]:
                    reply = QMessageBox.question(
                        self,
                        "Confirm Re-parse",
                        "This record has manual edits. Re-parse and overwrite those edited values?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    overwrite = reply == QMessageBox.StandardButton.Yes
                try:
                    self.import_service.reparse_profile(profile["id"], overwrite_manual_edits=overwrite)
                except Exception as exc:
                    self._show_error("Re-parse failed", str(exc))
                    return
            elif dialog.is_save_requested() or dialog.should_mark_reviewed():
                prompt_title = "Confirm Review Save" if dialog.should_mark_reviewed() else "Confirm Save"
                prompt_text = (
                    "Save changes and mark this record as Reviewed?"
                    if dialog.should_mark_reviewed()
                    else "Save your manual changes to this record?"
                )
                reply = QMessageBox.question(
                    self,
                    prompt_title,
                    prompt_text,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                try:
                    self.import_service.save_manual_edits(
                        profile["id"],
                        dialog.get_manual_edits(),
                        mark_reviewed=dialog.should_mark_reviewed(),
                    )
                except Exception as exc:
                    self._show_error("Save failed", str(exc))
                    return
            self.reload_records()

    def delete_selected_record(self) -> None:
        profile = self._get_selected_profile()
        if profile is None:
            self._show_error("No selection", "Please select a record first.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Record",
            f"Delete the record for {profile['source_file_name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted_profile = self.repository.delete_profile(profile["id"])
        if deleted_profile is None:
            return

        source_path = deleted_profile["source_file_path"]
        if self.repository.count_profiles_by_source_path(source_path) == 0:
            pdf_path = Path(source_path)
            if pdf_path.exists():
                pdf_path.unlink()
        self.repository.create_log(profile["id"], "delete", "Deleted record")
        self.reload_records()

    def check_updates(self) -> None:
        result = check_for_updates()
        if result["message"]:
            QMessageBox.information(self, "Check for Updates", result["message"])
            return
        if result["update_available"]:
            QMessageBox.information(
                self,
                "Update Available",
                f"Version {result['latest_version']} is available.\nDownload: {result['download_url']}",
            )
            return
        QMessageBox.information(self, "Check for Updates", "You already have the latest version.")

    def open_settings(self) -> None:
        SettingsDialog().exec()

    def reload_records(self) -> None:
        records = [self._flatten_profile(profile) for profile in self.repository.list_profiles()]
        filtered_records = self._apply_filters(records)
        self.table_model.set_rows(filtered_records)
        self.table_view.resizeColumnsToContents()
        self._update_summary_cards(records)
        self.statusBar().showMessage(f"{len(filtered_records)} record(s)", 3000)

    def _build_columns(self) -> list[tuple[str, str]]:
        field_columns = [(field["key"], field["display_name"]) for field in self.field_config]
        metadata_columns = [
            ("source_file_name", "Source File"),
            ("review_status", "Review Status"),
            ("overall_confidence", "Overall Confidence"),
            ("created_at", "Created At"),
            ("updated_at", "Updated At"),
        ]
        return field_columns + metadata_columns

    def _apply_filters(self, records: list[dict]) -> list[dict]:
        status_value = self.status_filter.currentText()
        query = self.search_box.text().strip().lower()
        filtered = records
        if status_value != "All":
            filtered = [record for record in filtered if record.get("review_status") == status_value]
        if query:
            filtered = [
                record
                for record in filtered
                if query in " ".join(str(value).lower() for value in record.values() if value is not None)
            ]
        return filtered

    def _flatten_profile(self, profile: dict) -> dict:
        flattened = dict(profile["parsed_json"])
        flattened["id"] = profile["id"]
        flattened["source_file_name"] = profile["source_file_name"]
        flattened["source_file_path"] = profile["source_file_path"]
        flattened["review_status"] = profile["review_status"]
        flattened["overall_confidence"] = profile["overall_confidence"]
        flattened["created_at"] = profile["created_at"]
        flattened["updated_at"] = profile["updated_at"]
        flattened["raw_text"] = profile["raw_text"]
        flattened["confidence_json"] = profile["confidence_json"]
        flattened["evidence_json"] = profile["evidence_json"]
        flattened["manual_edits_json"] = profile["manual_edits_json"]
        return flattened

    def _get_selected_profile(self) -> dict | None:
        index = self.table_view.currentIndex()
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self.table_model.rows):
            return None
        return self.table_model.rows[row]

    def _show_error(self, title: str, message: str) -> None:
        self.logger.error("%s: %s", title, message)
        QMessageBox.critical(self, title, message)

    def _build_hero_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("HeroCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(20)

        copy_layout = QVBoxLayout()
        copy_layout.setSpacing(6)
        title = QLabel("Biodata Review Workspace")
        title.setObjectName("HeroTitle")
        subtitle = QLabel(
            "Import biodata PDFs, review extracted values, and prepare a clean export for final decisions."
        )
        subtitle.setObjectName("HeroSubtitle")
        subtitle.setWordWrap(True)
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        for text in ("Local only", "Windows release ready", "Rule-based extraction"):
            chip = QLabel(text)
            chip.setObjectName("ChipLabel")
            chips_layout.addWidget(chip)
        chips_layout.addStretch(1)
        copy_layout.addWidget(title)
        copy_layout.addWidget(subtitle)
        copy_layout.addLayout(chips_layout)

        actions_layout = QGridLayout()
        actions_layout.setHorizontalSpacing(10)
        actions_layout.setVerticalSpacing(10)
        action_specs = [
            ("Import PDF", self.import_pdf, "PrimaryButton"),
            ("Import Folder", self.import_folder, ""),
            ("Export CSV", self.export_csv, ""),
            ("View PDF", self.view_selected_pdf, ""),
            ("Open Record", self.open_selected_record, ""),
            ("Delete Record", self.delete_selected_record, "DangerButton"),
            ("Check Updates", self.check_updates, "GhostButton"),
            ("Settings", self.open_settings, "GhostButton"),
        ]
        for index, (label, handler, object_name) in enumerate(action_specs):
            button = QPushButton(label)
            if object_name:
                button.setObjectName(object_name)
            button.clicked.connect(handler)
            actions_layout.addWidget(button, index // 2, index % 2)

        layout.addLayout(copy_layout, stretch=3)
        layout.addLayout(actions_layout, stretch=2)
        return card

    def _build_filters_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("PanelCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        title = QLabel("Browse Records")
        title.setObjectName("SectionTitle")
        hint = QLabel("Filter by review status and search across the extracted table.")
        hint.setObjectName("SectionHint")
        controls = QHBoxLayout()
        controls.setSpacing(12)
        self.status_filter.setMinimumWidth(210)
        self.search_box.setMinimumWidth(360)
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("GhostButton")
        refresh_button.clicked.connect(self.reload_records)
        controls.addWidget(self.status_filter, stretch=0)
        controls.addWidget(self.search_box, stretch=1)
        controls.addWidget(refresh_button, stretch=0)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addLayout(controls)
        return card

    def _build_summary_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        for card in (
            self.total_records_card,
            self.review_queue_card,
            self.reviewed_card,
            self.failed_card,
        ):
            layout.addWidget(card)
        return row

    def _build_table_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("TableCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        title = QLabel("Imported Biodata Records")
        title.setObjectName("SectionTitle")
        hint = QLabel("Double-click a row to review or correct the extracted fields.")
        hint.setObjectName("SectionHint")
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.table_view, stretch=1)
        return card

    def _create_summary_card(self, label_text: str, value_text: str) -> tuple[QWidget, QLabel]:
        card = QWidget()
        card.setObjectName("PanelCard")
        card.setMinimumHeight(92)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("SummaryLabel")
        value = QLabel(value_text)
        value.setObjectName("SummaryValue")
        layout.addWidget(label)
        layout.addWidget(value)
        return card, value

    def _update_summary_cards(self, records: list[dict]) -> None:
        self.total_records_label.setText(str(len(records)))
        self.review_queue_label.setText(str(sum(1 for row in records if row.get("review_status") == REVIEW_STATUS_NEEDS_REVIEW)))
        self.reviewed_label.setText(str(sum(1 for row in records if row.get("review_status") == REVIEW_STATUS_REVIEWED)))
        self.failed_label.setText(str(sum(1 for row in records if row.get("review_status") == REVIEW_STATUS_FAILED)))


def run_app() -> int:
    app_paths = ensure_app_paths()
    configure_logging(app_paths.log_file_path)
    app = QApplication(sys.argv)
    apply_app_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()
