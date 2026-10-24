"""Barra superior del solitario: modo de robo (segmentos), estado, Deshacer, Nueva partida (principal) y Volver.
Deja libre a la derecha la esquina del control de volumen. El estilo sale de `solitaire_style`."""
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem, QWidget

from src.common.theme import CORNER, SPACE, px

DRAW_OPTIONS = {1: "Robar de a 1", 3: "Robar de a 3"}


class SolitaireBar:
    def __init__(self, owner: QWidget):
        self.layout = QHBoxLayout()
        self.status = QLabel()
        self.status.setObjectName("solStatus")
        self.mode_group = QButtonGroup(owner)
        self.mode_buttons: dict[int, QPushButton] = {}
        for count, text in DRAW_OPTIONS.items():
            button = QPushButton(text)
            button.setObjectName("solMode")
            button.setCheckable(True)
            self.mode_group.addButton(button, count)
            self.mode_buttons[count] = button
            self.layout.addWidget(button)
        self._status_gap = QSpacerItem(0, 0)
        self.layout.addSpacerItem(self._status_gap)
        self.layout.addWidget(self.status)
        self.layout.addStretch(1)
        self.undo_button = self._button("Deshacer", "solButton")
        self.undo_button.setToolTip("Deshacer (Ctrl+Z)")
        self.new_game_button = self._button("Nueva partida", "solPrimary")
        self.back_button = self._button("Volver al menú", "solButton")
        self._corner = QSpacerItem(0, 0)
        self.layout.addSpacerItem(self._corner)  # la esquina del control de volumen queda libre

    def _button(self, text: str, name: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(name)
        self.layout.addWidget(button)
        return button

    def apply_scale(self, u: float) -> None:
        size = px(CORNER.size, u)
        self.layout.setSpacing(px(SPACE.sm, u))
        self._status_gap.changeSize(px(SPACE.lg, u), 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._corner.changeSize(size + px(CORNER.gap, u), size, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
