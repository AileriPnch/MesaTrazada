"""Placa de latón grabada que funciona como botón (Nueva partida, Deshacer, Menú). El render trae los cuatro
estados (normal / hover / pressed / disabled); el texto va grabado por código (nítido a cualquier escala). Se
recorre con Tab y se activa con Enter o Espacio; con foco lleva un filete grabado oscuro (contrasta con el latón;
el ámbar sobre latón casi no se veía)."""
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton, QWidget

from src.chess_game.table_object import Placed
from src.chess_game.table_sprites import UiSprites, engrave, font
from src.common import theme
from src.common.theme import COLORS, TABLE_LOOK

PRIMARY, SECONDARY = "placa_principal", "placa_secundaria"


class BrassButton(Placed, QAbstractButton):
    def __init__(self, text: str, key: str, sprites: UiSprites, parent: QWidget):
        QAbstractButton.__init__(self, parent)
        self.sprites, self.key = sprites, key
        self.setText(text)
        self.setAccessibleName(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @property
    def state(self) -> str:
        if not self.isEnabled():
            return "disabled"
        if self.isDown():
            return "pressed"
        return "hover" if self.underMouse() else "normal"

    def text_font(self) -> QFont:
        share = TABLE_LOOK.primary_text if self.key == PRIMARY else TABLE_LOOK.secondary_text
        return font(theme.TYPE.ui_family, max(TABLE_LOOK.min_text, self.s * share), theme.TYPE.ui_strong)

    def face(self) -> QRectF:
        return self.at.rect(self.sprites.ui.box(self.key, "cara"))

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.isEnabled():
            self.animateClick()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        if self.at is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        state = self.state
        self.sprites.draw(p, f"{self.key}_{state}", self.at, self.dpr())
        face = self.face().translated(0, 1 if state == "pressed" else 0)  # apretada: la placa baja
        engrave(p, face, self.text(), self.text_font())  # deshabilitada: la placa gris lo dice; el texto, legible
        if self.hasFocus():
            width = max(2.0, self.s * TABLE_LOOK.focus_width)
            inset = self.s * TABLE_LOOK.focus_inset
            ring = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
            p.setBrush(Qt.BrushStyle.NoBrush)
            for color, dy in ((QColor(COLORS.engrave_light), 1.0), (QColor(COLORS.engrave), 0.0)):  # grabado
                color.setAlphaF(0.5 if dy else 0.95)
                p.setPen(QPen(color, width))
                p.drawRoundedRect(ring.translated(0, dy), self.s * 0.04, self.s * 0.04)
