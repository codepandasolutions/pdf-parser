from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QToolBar,
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
        self.resize(1300, 800)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", REVIEW_STATUS_PARSED, REVIEW_STATUS_NEEDS_REVIEW, REVIEW_STATUS_REVIEWED, REVIEW_STATUS_FAILED]
        )
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search name, phone, city, education, occupation...")

        self.table_model = RecordsTableModel(self._build_columns())
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.doubleClicked.connect(self.open_selected_record)

        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        for label, handler in (
            ("Import PDF", self.import_pdf),
            ("Import Folder", self.import_folder),
            ("Export CSV", self.export_csv),
            ("View PDF", self.view_selected_pdf),
            ("Open/Edit Record", self.open_selected_record),
            ("Delete Record", self.delete_selected_record),
            ("Check for Updates", self.check_updates),
            ("Settings", self.open_settings),
        ):
            action = toolbar.addAction(label)
            action.triggered.connect(handler)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.status_filter)
        controls_layout.addWidget(self.search_box)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.reload_records)
        controls_layout.addWidget(refresh_button)

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.addLayout(controls_layout)
        central_layout.addWidget(self.table_view)
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
        self.statusBar().showMessage(f"Imported {len(results)} PDF(s)", 5000)
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
            else:
                manual_edits = dialog.get_manual_edits()
                self.repository.update_profile(
                    profile["id"],
                    parsed=manual_edits,
                    confidence=profile["confidence_json"],
                    evidence=profile["evidence_json"],
                    review_status=profile.get("review_status", REVIEW_STATUS_REVIEWED),
                    manual_edits=manual_edits,
                    raw_text=profile["raw_text"],
                    overall_confidence=profile["overall_confidence"],
                )
                self.repository.create_log(profile["id"], "manual_edit", "Saved manual edits")
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


def run_app() -> int:
    app_paths = ensure_app_paths()
    configure_logging(app_paths.log_file_path)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
