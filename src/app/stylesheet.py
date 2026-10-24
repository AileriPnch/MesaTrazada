"""Estilo global de la app (juegos y diálogos): Fusion + paleta + hoja de estilos con un único acento.

La pantalla de inicio tiene su propia hoja de estilos (`src/app/home/home_style.py`); las dos salen de los
tokens de `src/common/theme.py`.
"""
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from src.app import palette as c
from src.common.theme import TYPE

_ROLES = {
    QPalette.ColorRole.Window: c.WINDOW_BG,
    QPalette.ColorRole.WindowText: c.TEXT,
    QPalette.ColorRole.Base: c.PANEL_BG,
    QPalette.ColorRole.AlternateBase: c.SURFACE,
    QPalette.ColorRole.Text: c.TEXT,
    QPalette.ColorRole.Button: c.SURFACE,
    QPalette.ColorRole.ButtonText: c.TEXT,
    QPalette.ColorRole.Highlight: c.ACCENT_DARK,
    QPalette.ColorRole.HighlightedText: "#ffffff",
    QPalette.ColorRole.ToolTipBase: c.SURFACE,
    QPalette.ColorRole.ToolTipText: c.TEXT,
    QPalette.ColorRole.PlaceholderText: c.TEXT_MUTED,
}

STYLESHEET = f"""
QPushButton, QToolButton {{
    background: {c.SURFACE}; color: {c.TEXT}; border: 1px solid {c.BORDER};
    border-radius: 6px; padding: 7px 16px;
}}
QPushButton:hover, QToolButton:hover {{ border-color: {c.ACCENT}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {c.PANEL_BG}; }}
QPushButton:disabled {{ color: {c.TEXT_MUTED}; border-color: {c.SURFACE}; }}
QPushButton#segmentButton {{ padding: 6px 12px; }}
QPushButton#segmentButton:checked {{ background: {c.PANEL_BG}; border-color: {c.ACCENT}; color: {c.ACCENT}; }}
QFrame#sidePanel {{ background: {c.PANEL_BG}; border: 1px solid {c.BORDER}; border-radius: 10px; }}
QLabel#statusMuted {{ color: {c.TEXT_MUTED}; }}
QLabel#statusLine {{ font-size: 11pt; font-weight: 600; }}
QTableWidget {{ background: {c.WINDOW_BG}; border: 1px solid {c.BORDER}; border-radius: 6px; }}
QHeaderView::section {{ background: {c.PANEL_BG}; color: {c.TEXT_MUTED}; border: none; padding: 4px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {c.BORDER}; border-radius: 5px; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont(TYPE.games_family, 10))
    pal = QPalette()
    for role, color in _ROLES.items():
        pal.setColor(role, QColor(color))
    disabled = QPalette.ColorGroup.Disabled
    for role in (QPalette.ColorRole.ButtonText, QPalette.ColorRole.Text, QPalette.ColorRole.WindowText):
        pal.setColor(disabled, role, QColor(c.TEXT_MUTED))
    app.setPalette(pal)
    app.setStyleSheet(STYLESHEET)
