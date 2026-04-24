from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


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
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        key = self.columns[index.column()][0]
        value = row.get(key, "")
        return "" if value is None else str(value)

    def set_rows(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()
