from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


APP_STYLESHEET = """
QMainWindow, QDialog {
    background: #eef2f6;
    color: #233240;
}

QWidget#AppShell, QWidget#DialogShell {
    background: transparent;
}

QWidget#SidebarCard {
    background: #203245;
    border-right: 1px solid #162431;
}

QWidget#TopBarCard, QWidget#ToolbarCard, QWidget#MetricCard, QWidget#TableCard, QWidget#PanelCard, QWidget#RawTextCard {
    background: #ffffff;
    border: 1px solid #d8e0e8;
    border-radius: 14px;
}

QWidget#TableCard {
    border-radius: 18px;
}

QLabel#SidebarTitle {
    color: #f3f6fa;
    font-size: 20px;
    font-weight: 700;
}

QLabel#SidebarSubtitle {
    color: #aab9c7;
    font-size: 12px;
}

QLabel#SectionTitle {
    color: #203245;
    font-size: 18px;
    font-weight: 700;
}

QLabel#SectionHint {
    color: #708191;
    font-size: 12px;
}

QLabel#MetricLabel {
    color: #748392;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

QLabel#MetricValue {
    color: #203245;
    font-size: 24px;
    font-weight: 700;
}

QLabel#MetricAccent {
    color: #1e5aa6;
    font-size: 12px;
    font-weight: 600;
}

QLabel#TableTitle {
    color: #203245;
    font-size: 16px;
    font-weight: 700;
}

QLabel#TableHint {
    color: #7a8793;
    font-size: 12px;
}

QPushButton {
    min-height: 18px;
    padding: 10px 14px;
    background: #f5f8fb;
    color: #243240;
    border: 1px solid #d4dde6;
    border-radius: 10px;
    font-weight: 600;
}

QPushButton:hover {
    background: #ebf1f6;
}

QPushButton:pressed {
    background: #dfe8f0;
}

QPushButton#SidebarButton {
    background: transparent;
    color: #dce6ef;
    text-align: left;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 12px 14px;
}

QPushButton#SidebarButton:hover {
    background: #294154;
    border: 1px solid #355168;
}

QPushButton#PrimaryButton {
    background: #1f5fa8;
    color: #ffffff;
    border: 1px solid #174a84;
}

QPushButton#PrimaryButton:hover {
    background: #1a538f;
}

QPushButton#DangerButton {
    background: #fff1f0;
    color: #a53d34;
    border: 1px solid #efcbc7;
}

QPushButton#GhostButton {
    background: transparent;
}

QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QTableView, QScrollArea {
    background: #ffffff;
    color: #22303d;
    border: 1px solid #d3dde6;
    border-radius: 10px;
}

QLineEdit, QComboBox {
    padding: 10px 12px;
}

QTextEdit, QPlainTextEdit {
    padding: 10px;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QTableView:focus {
    border: 1px solid #1f5fa8;
}

QTableView {
    gridline-color: #e8edf3;
    alternate-background-color: #f8fafc;
    selection-background-color: #d9e8f7;
    selection-color: #203245;
    padding: 4px;
}

QHeaderView::section {
    background: #f2f6fa;
    color: #556474;
    padding: 12px 10px;
    border: none;
    border-bottom: 1px solid #dfe6ed;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background: transparent;
    border: none;
    margin: 3px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #c6d2de;
    border-radius: 6px;
    min-height: 24px;
    min-width: 24px;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QStatusBar {
    background: #dfe7ee;
    color: #445463;
}
"""


def apply_app_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#eef2f6"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.Text, QColor("#22303d"))
    palette.setColor(QPalette.Button, QColor("#f5f8fb"))
    palette.setColor(QPalette.ButtonText, QColor("#243240"))
    palette.setColor(QPalette.Highlight, QColor("#1f5fa8"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(APP_STYLESHEET)
