from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class RecordsTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.columns: list[str] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        column = self.columns[index.column()]
        return str(row.get(column, ""))
