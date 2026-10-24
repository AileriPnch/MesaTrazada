"""Panel flotante con las opciones de arranque de un juego y el botón para empezar."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem,
                             QVBoxLayout, QWidget)

from config import settings
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty, describe, level_for
from src.common.qss import button_qss, rgba
from src.common import theme
from src.common.theme import COLORS, PRIMARY, RADIUS, SECONDARY, SPACE, px

Option = tuple[object, str, str]  # (valor, texto, tooltip)
PER_ROW = 3  # un grupo con más opciones sigue en otra fila (la dificultad: 2 filas de 3)


def panel_qss(u: float) -> str:
    t = theme.TYPE
    label = f"font-family: '{t.ui_family}'; font-size: {px(t.label, u, 9)}px; font-weight: {t.ui_weight};"
    return f"""
QFrame#homePanel {{
    background: {rgba(COLORS.glass, 0.95)}; border: 1px solid {rgba(COLORS.border, 0.9)};
    border-radius: {px(RADIUS.xl, u)}px;
}}
QLabel#homeLabel {{ color: {COLORS.text_muted}; {label} background: transparent; }}
QLabel#homeMessage {{ color: {COLORS.error}; {label} background: transparent; }}
""" + button_qss("QPushButton#homeOption", SECONDARY, u) + button_qss("QPushButton#homePrimary", PRIMARY, u)


class OptionsPanel(QFrame):
    def __init__(self, groups: list[tuple[str, list[Option], object]], primary_text: str, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("homePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation)  # un clic adentro no cierra el panel
        self._groups: dict[str, dict[object, QPushButton]] = {}
        self._rows: list[QHBoxLayout] = []
        self._gaps: list[QSpacerItem] = []  # aire antes de cada grupo (menos el primero) y del botón
        self._column = QVBoxLayout(self)
        for title, options, default in groups:
            if self._rows:
                self._add_gap()
            label = QLabel(title)
            label.setObjectName("homeLabel")
            self._column.addWidget(label)
            exclusive = QButtonGroup(self)
            buttons = {}
            for index, (value, text, tip) in enumerate(options):
                if index % PER_ROW == 0:
                    row = QHBoxLayout()
                    self._column.addLayout(row)
                    self._rows.append(row)
                button = QPushButton(text)
                button.setObjectName("homeOption")
                button.setCheckable(True)
                button.setChecked(value == default)
                button.setToolTip(tip)
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                exclusive.addButton(button)
                row.addWidget(button, 1)
                buttons[value] = button
            self._groups[title] = buttons
        self.message = QLabel()
        self.message.setObjectName("homeMessage")
        self.message.setWordWrap(True)
        self.message.hide()
        self._column.addWidget(self.message)
        self._add_gap()
        self.primary = QPushButton(primary_text)
        self.primary.setObjectName("homePrimary")
        self._column.addWidget(self.primary)
        self.scale = None

    def _add_gap(self) -> None:
        gap = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._column.addSpacerItem(gap)
        self._gaps.append(gap)

    def buttons(self, title: str) -> dict[object, QPushButton]:
        return self._groups[title]

    def value(self, title: str) -> object:
        return next(value for value, button in self._groups[title].items() if button.isChecked())

    def set_message(self, text: str) -> None:
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def apply_scale(self, u: float) -> None:
        if u == self.scale:
            return
        self.scale = u
        self.setStyleSheet(panel_qss(u))
        pad = px(SPACE.xl, u)
        self._column.setContentsMargins(pad, pad, pad, pad)
        self._column.setSpacing(px(SPACE.sm, u))
        for row in self._rows:
            row.setSpacing(px(SPACE.sm, u))
        for gap in self._gaps:
            gap.changeSize(0, px(SPACE.md, u), QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._column.invalidate()

    def height_for(self, width: int) -> int:
        """Alto que necesita el panel a ese ancho (con el mensaje, si hay, en varias líneas)."""
        column = self._column
        hint = column.totalHeightForWidth(width) if column.hasHeightForWidth() else column.totalSizeHint().height()
        return max(hint, column.totalMinimumSize().height())


def check_engine(panel: OptionsPanel) -> None:
    """Sin Stockfish no se puede jugar: se avisa en el mismo panel y "Jugar" queda deshabilitado."""
    found = settings.stockfish_path.is_file()
    panel.set_message("" if found else f"No se encontró Stockfish en:\n{settings.stockfish_path}\n"
                                       "Revisá STOCKFISH_PATH en el archivo .env.")
    panel.primary.setEnabled(found)


def chess_panel(parent: QWidget) -> OptionsPanel:
    colors = [(choice, choice.value, "") for choice in ColorChoice]
    levels = [(d, d.value, describe(level_for(d, settings))) for d in Difficulty]
    return OptionsPanel([("Color", colors, ColorChoice.WHITE), ("Dificultad", levels, Difficulty.BEGINNER)],
                        "Jugar", parent)


def solitaire_panel(parent: QWidget) -> OptionsPanel:
    return OptionsPanel([("Robo", [(1, "De a 1", "Robar de a una carta"), (3, "De a 3", "Robar de a tres cartas")], 1)],
                        "Repartir", parent)
