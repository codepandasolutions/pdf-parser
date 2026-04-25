from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
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
        self.resize(1520, 920)
        self.setMinimumSize(1240, 780)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", REVIEW_STATUS_PARSED, REVIEW_STATUS_NEEDS_REVIEW, REVIEW_STATUS_REVIEWED, REVIEW_STATUS_FAILED]
        )
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search across names, cities, education, phones, occupations...")
        self.search_box.setClearButtonEnabled(True)

        self.table_model = RecordsTableModel(self._build_columns())
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(False)
        self.table_view.setWordWrap(False)
        self.table_view.setSortingEnabled(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_view.doubleClicked.connect(self.open_selected_record)

        self.total_records_card, self.total_records_label, self.total_records_accent = self._create_metric_card(
            "Total Records", "0", "Loaded from local storage"
        )
        self.review_queue_card, self.review_queue_label, self.review_queue_accent = self._create_metric_card(
            "Needs Review", "0", "Awaiting manual correction"
        )
        self.reviewed_card, self.reviewed_label, self.reviewed_accent = self._create_metric_card(
            "Reviewed", "0", "Confirmed by user"
        )
        self.failed_card, self.failed_label, self.failed_accent = self._create_metric_card(
            "Failed", "0", "Extraction needs attention"
        )

        central_widget = QWidget()
        central_widget.setObjectName("AppShell")
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar(), stretch=0)
        root_layout.addWidget(self._build_workspace(), stretch=1)
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
        self._update_metrics(records, filtered_records)
        self.statusBar().showMessage(f"{len(filtered_records)} record(s) visible", 3000)

    def _build_columns(self) -> list[tuple[str, str]]:
        field_columns = [(field["key"], field["display_name"]) for field in self.field_config]
        metadata_columns = [
            ("source_file_name", "Source File"),
            ("review_status", "Review Status"),
            ("overall_confidence", "Confidence"),
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

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("SidebarCard")
        sidebar.setFixedWidth(250)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 22, 20, 18)
        layout.setSpacing(12)

        title = QLabel("Biodata ERP")
        title.setObjectName("SidebarTitle")
        subtitle = QLabel("Records, review and export")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(14)

        for label, handler, object_name in (
            ("Import Single PDF", self.import_pdf, "SidebarButton"),
            ("Import Folder", self.import_folder, "SidebarButton"),
            ("Open Selected Record", self.open_selected_record, "SidebarButton"),
            ("View Source PDF", self.view_selected_pdf, "SidebarButton"),
            ("Export Filtered CSV", self.export_csv, "SidebarButton"),
            ("Delete Selected Record", self.delete_selected_record, "SidebarButton"),
            ("Check for Updates", self.check_updates, "SidebarButton"),
            ("Settings", self.open_settings, "SidebarButton"),
        ):
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.clicked.connect(handler)
            layout.addWidget(button)

        layout.addStretch(1)
        footnote = QLabel("Local-first arranged-marriage biodata operations console")
        footnote.setObjectName("SidebarSubtitle")
        footnote.setWordWrap(True)
        layout.addWidget(footnote)
        return sidebar

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)
        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_toolbar_card())
        layout.addWidget(self._build_metrics_row())
        layout.addWidget(self._build_table_card(), stretch=1)
        return workspace

    def _build_top_bar(self) -> QWidget:
        card = QWidget()
        card.setObjectName("TopBarCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title = QLabel("Profile Registry")
        title.setObjectName("SectionTitle")
        hint = QLabel("Review parsed biodata rows, verify details and export a clean working dataset.")
        hint.setObjectName("SectionHint")
        text_layout.addWidget(title)
        text_layout.addWidget(hint)

        quick_chip = QLabel("Windows Test Release")
        quick_chip.setObjectName("MetricAccent")
        quick_chip.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(quick_chip, stretch=0)
        return card

    def _build_toolbar_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("ToolbarCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        self.status_filter.setMinimumWidth(200)
        self.search_box.setMinimumWidth(360)

        export_button = QPushButton("Export CSV")
        export_button.setObjectName("PrimaryButton")
        export_button.clicked.connect(self.export_csv)

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("GhostButton")
        refresh_button.clicked.connect(self.reload_records)

        layout.addWidget(self.status_filter, stretch=0)
        layout.addWidget(self.search_box, stretch=1)
        layout.addWidget(refresh_button, stretch=0)
        layout.addWidget(export_button, stretch=0)
        return card

    def _build_metrics_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        for card in (self.total_records_card, self.review_queue_card, self.reviewed_card, self.failed_card):
            layout.addWidget(card)
        return row

    def _build_table_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("TableCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("Biodata Records Grid")
        title.setObjectName("TableTitle")
        hint = QLabel("The records grid is the primary workspace. Double-click any row to review and correct parsed fields.")
        hint.setObjectName("TableHint")
        hint.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(hint)

        focus_button = QPushButton("Open Selected")
        focus_button.setObjectName("PrimaryButton")
        focus_button.clicked.connect(self.open_selected_record)

        header_row.addLayout(title_block, stretch=1)
        header_row.addWidget(focus_button, stretch=0)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #dfe6ed;")

        layout.addLayout(header_row)
        layout.addWidget(divider)
        layout.addWidget(self.table_view, stretch=1)
        return card

    def _create_metric_card(self, label_text: str, value_text: str, accent_text: str) -> tuple[QWidget, QLabel, QLabel]:
        card = QWidget()
        card.setObjectName("MetricCard")
        card.setMinimumHeight(96)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        value = QLabel(value_text)
        value.setObjectName("MetricValue")
        accent = QLabel(accent_text)
        accent.setObjectName("MetricAccent")
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addWidget(accent)
        return card, value, accent

    def _update_metrics(self, records: list[dict], filtered_records: list[dict]) -> None:
        self.total_records_label.setText(str(len(records)))
        self.total_records_accent.setText(f"{len(filtered_records)} currently visible")

        needs_review_count = sum(1 for row in records if row.get("review_status") == REVIEW_STATUS_NEEDS_REVIEW)
        reviewed_count = sum(1 for row in records if row.get("review_status") == REVIEW_STATUS_REVIEWED)
        failed_count = sum(1 for row in records if row.get("review_status") == REVIEW_STATUS_FAILED)

        self.review_queue_label.setText(str(needs_review_count))
        self.review_queue_accent.setText("Rows requiring manual validation")
        self.reviewed_label.setText(str(reviewed_count))
        self.reviewed_accent.setText("Completed and confirmed rows")
        self.failed_label.setText(str(failed_count))
        self.failed_accent.setText("Rows with extraction failure")


def run_app() -> int:
    app_paths = ensure_app_paths()
    configure_logging(app_paths.log_file_path)
    app = QApplication(sys.argv)
    apply_app_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()
