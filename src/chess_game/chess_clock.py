"""Reloj de ajedrez (decorativo, sin cuenta de tiempo): indica de quién es el turno. Como en un reloj real, el que
acaba de mover aprieta su botón: con el botón blanco hundido mueven las negras. Mientras Stockfish piensa, se
enciende la luz de su lado (la lente del render + un resplandor ámbar suave, fijo: nada titila). Al terminar la
partida, los dos botones quedan parejos."""
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QPainter, QRadialGradient
from PyQt6.QtWidgets import QWidget

import chess

from src.chess_game.interface_art import Box
from src.chess_game.table_object import TableObject
from src.chess_game.table_sprites import UiSprites
from src.common.theme import COLORS, TABLE_LOOK

SIDES = {chess.WHITE: "blancas", chess.BLACK: "negras"}


class ChessClock(TableObject):
    def __init__(self, sprites: UiSprites, parent: QWidget):
        super().__init__(sprites, "reloj", parent)
        self.state = "parejos"  # o el lado con el botón hundido
        self.thinking: chess.Color | None = None

    def box(self) -> Box:
        """Lo que se ve del reloj (botones arriba incluidos): entra entero en su lugar."""
        return self.sprites.ui.visible["reloj_parejos.png"]

    def set_turn(self, turn: chess.Color, thinking: bool = False) -> None:
        self.state = SIDES[not turn]  # el que acaba de mover apretó su botón
        self.thinking = turn if thinking else None
        self.update()

    def set_over(self) -> None:
        self.state, self.thinking = "parejos", None
        self.update()

    def paintEvent(self, event) -> None:
        if self.at is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dpr = self.dpr()
        self.sprites.draw(p, f"reloj_{self.state}", self.at, dpr)
        if self.thinking is None:
            return
        side = SIDES[self.thinking]
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        self.sprites.draw(p, f"reloj_luz_{side}", self.at, dpr)
        center = self.at.point(*self.sprites.ui.info["reloj"]["luces"][side])
        radius = TABLE_LOOK.glow * self.s
        glow = QRadialGradient(center, radius)
        color = QColor(COLORS.thinking)
        color.setAlphaF(TABLE_LOOK.glow_alpha)
        glow.setColorAt(0.0, color)
        color.setAlphaF(0.0)
        glow.setColorAt(1.0, color)
        p.fillRect(QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius), glow)
