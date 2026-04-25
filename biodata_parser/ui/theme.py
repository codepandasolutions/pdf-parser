from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


APP_STYLESHEET = """
QMainWindow, QDialog {
    background: #f4f1ea;
    color: #1f2933;
}

QWidget#AppShell, QWidget#DialogShell {
    background: transparent;
}

QWidget#HeroCard, QWidget#PanelCard, QWidget#TableCard, QWidget#MetaCard, QWidget#RawTextCard {
    background: #fffdf8;
    border: 1px solid #e5ddcf;
    border-radius: 18px;
}

QWidget#HeroCard {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #fbf6ea, stop: 1 #efe5d2);
    border: 1px solid #dccfb6;
}

QLabel#HeroTitle {
    font-size: 26px;
    font-weight: 700;
    color: #402a1f;
}

QLabel#HeroSubtitle {
    font-size: 13px;
    color: #72584a;
}

QLabel#SectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #2d3b45;
}

QLabel#SectionHint {
    font-size: 12px;
    color: #6a7a86;
}

QLabel#SummaryLabel {
    font-size: 12px;
    color: #7a685d;
}

QLabel#SummaryValue {
    font-size: 22px;
    font-weight: 700;
    color: #2c3a43;
}

QLabel#ChipLabel {
    background: #f2e8d7;
    color: #61483b;
    border: 1px solid #e0cfb4;
    border-radius: 12px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton {
    background: #f8f2e7;
    border: 1px solid #dccfb6;
    border-radius: 12px;
    padding: 10px 14px;
    color: #433229;
    font-weight: 600;
}

QPushButton:hover {
    background: #f1e5d0;
}

QPushButton:pressed {
    background: #e8d8bc;
}

QPushButton#PrimaryButton {
    background: #2c6e63;
    color: white;
    border: 1px solid #24584f;
}

QPushButton#PrimaryButton:hover {
    background: #275f56;
}

QPushButton#DangerButton {
    background: #fbebe8;
    color: #8a3128;
    border: 1px solid #e5b6af;
}

QPushButton#GhostButton {
    background: transparent;
    border: 1px solid #d9cfbe;
}

QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QTableView, QScrollArea {
    background: #fffdfa;
    border: 1px solid #ddd4c6;
    border-radius: 12px;
    color: #24323b;
}

QLineEdit, QComboBox {
    min-height: 18px;
    padding: 10px 12px;
}

QTextEdit, QPlainTextEdit {
    padding: 10px;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QTableView:focus {
    border: 1px solid #2c6e63;
}

QTableView {
    gridline-color: #efe7da;
    selection-background-color: #e8f0eb;
    selection-color: #1f2933;
    alternate-background-color: #fbf8f1;
}

QHeaderView::section {
    background: #f5efe4;
    color: #5c4a3e;
    padding: 10px 8px;
    border: none;
    border-bottom: 1px solid #e5ddcf;
    font-weight: 700;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background: transparent;
    border: none;
    margin: 2px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #d8cbb7;
    border-radius: 6px;
    min-height: 28px;
    min-width: 28px;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QStatusBar {
    background: #efe8db;
    color: #5b483c;
}
"""


def apply_app_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f4f1ea"))
    palette.setColor(QPalette.Base, QColor("#fffdfa"))
    palette.setColor(QPalette.AlternateBase, QColor("#fbf8f1"))
    palette.setColor(QPalette.Text, QColor("#24323b"))
    palette.setColor(QPalette.Button, QColor("#f8f2e7"))
    palette.setColor(QPalette.ButtonText, QColor("#433229"))
    palette.setColor(QPalette.Highlight, QColor("#2c6e63"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(APP_STYLESHEET)
