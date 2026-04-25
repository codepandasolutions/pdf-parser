from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


class RecordsTableModel(QAbstractTableModel):
    def __init__(self, columns: list[tuple[str, str]] | None = None) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.columns: list[tuple[str, str]] = columns or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> str | None:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < len(self.columns):
            return self.columns[section][1]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        key = self.columns[index.column()][0]
        value = row.get(key, "")
        if role == Qt.DisplayRole:
            if key == "overall_confidence" and value not in ("", None):
                return f"{float(value):.2f}"
            return "" if value is None else str(value)
        if role == Qt.TextAlignmentRole:
            if key == "overall_confidence":
                return int(Qt.AlignCenter)
            return int(Qt.AlignVCenter | Qt.AlignLeft)
        if role == Qt.ForegroundRole and key == "review_status":
            status_colors = {
                "Parsed": QColor("#245b52"),
                "Needs Review": QColor("#8b5a16"),
                "Reviewed": QColor("#1f5ea8"),
                "Failed": QColor("#8c2f39"),
            }
            return status_colors.get(str(value))
        return None

    def set_rows(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()
