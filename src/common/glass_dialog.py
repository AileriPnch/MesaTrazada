"""Diálogo con el estilo de la app: panel de vidrio oscuro sin marco de Windows, título en la fuente de
títulos (Playfair Display) y texto en la de interfaz (Inter). Se centra sobre su ventana; Esc cancela."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLayout, QPushButton, QVBoxLayout, QWidget

from src.common import theme
from src.common.qss import button_qss, rgba
from src.common.theme import COLORS, PRIMARY, RADIUS, SECONDARY, SPACE, px


def dialog_qss(u: float) -> str:
    t = theme.TYPE
    return f"""
QFrame#glassDialog {{
    background: {rgba(COLORS.glass, 0.97)}; border: 1px solid {rgba(COLORS.accent_dark, 0.8)};
    border-radius: {px(RADIUS.xl, u)}px;
}}
QLabel#dialogTitle {{
    font-family: '{t.title_family}'; font-size: {px(t.title, u, 14)}px; font-weight: {t.title_weight};
    color: {COLORS.text}; background: transparent;
}}
QLabel#dialogHeading {{
    font-family: '{t.ui_family}'; font-size: {px(t.label, u, 9)}px; font-weight: {t.ui_strong};
    color: {COLORS.text}; background: transparent;
}}
QLabel#dialogText {{
    font-family: '{t.ui_family}'; font-size: {px(t.body, u, 10)}px; font-weight: {t.ui_weight};
    color: {COLORS.text_muted}; background: transparent;
}}
""" + button_qss("QPushButton#dialogPrimary", PRIMARY, u) + button_qss("QPushButton#dialogButton", SECONDARY, u)


class GlassDialog(QDialog):
    def __init__(self, parent: QWidget | None, u: float, title: str):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(title)
        self.u = u
        self.setStyleSheet(dialog_qss(u))
        frame = QFrame(self)
        frame.setObjectName("glassDialog")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)  # nunca más chico que su contenido
        outer.addWidget(frame)
        self.body = QVBoxLayout(frame)
        pad = px(SPACE.xl, u)
        self.body.setContentsMargins(pad, pad, pad, pad)
        self.body.setSpacing(px(SPACE.sm, u))
        self.title = self.add_label(title, "dialogTitle")

    def add_label(self, text: str, name: str = "dialogText") -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        label.setWordWrap(name == "dialogText")
        self.body.addWidget(label)
        return label

    def add_buttons(self, *buttons: tuple[str, bool]) -> list[QPushButton]:
        """Fila de botones alineada a la derecha: (texto, principal)."""
        row = QHBoxLayout()
        row.setSpacing(px(SPACE.sm, self.u))
        row.addStretch(1)
        made = []
        for text, primary in buttons:
            button = QPushButton(text)
            button.setObjectName("dialogPrimary" if primary else "dialogButton")
            row.addWidget(button)
            made.append(button)
        self.body.addSpacing(px(SPACE.md, self.u))
        self.body.addLayout(row)
        return made

    def showEvent(self, event) -> None:
        super().showEvent(event)
        window = self.parentWidget().window() if self.parentWidget() is not None else None
        if window is not None:
            self.adjustSize()
            frame = window.frameGeometry()
            self.move(frame.center() - self.rect().center())
