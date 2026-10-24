"""Perilla de latón del volumen, sólo en el ajedrez (el inicio y el solitario usan el parlante): el render en tres
estados (normal / hover / apretada) y, por código, la marca del nivel (de -135° a +135°) y el silencio (la marca
al mínimo y la tapa en sombra). La marca es clara con sombra debajo: la tapa del centro es oscura. La usa
SpeakerButton como "piel" mientras el ajedrez está abierto."""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen

from src.chess_game.table_sprites import UiSprites, place
from src.common.theme import COLORS, TABLE_LOOK
from src.common.volume import Volume


class KnobSkin:
    def __init__(self, sprites: UiSprites):
        self.sprites = sprites

    def paint(self, p: QPainter, rect: QRectF, lit: bool, down: bool, volume: Volume, dpr: float) -> None:
        side = rect.width() * TABLE_LOOK.knob
        target = QRectF(0, 0, side, side)
        target.moveCenter(rect.center() - QPointF(1, 1) * (rect.width() - side) / 4)  # lugar para la sombra
        ui = self.sprites.ui
        at = place(ui.box("perilla"), target)
        state = "pressed" if down else ("hover" if lit else "normal")
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for name in ("perilla_contacto", "perilla_sombra", f"perilla_{state}"):
            self.sprites.draw(p, name, at, dpr)
        x0, _, x1, _ = ui.box("perilla")
        radius = (x1 - x0) / 2 * at.scale
        center = at.point(*ui.info["perilla"]["ancla"])
        muted = volume.muted or volume.level == 0
        if muted:
            shade = QColor(0, 0, 0, 80)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(shade)
            p.drawEllipse(center, radius * 0.62, radius * 0.62)
        angle = math.radians(-135 + 270 * (0 if muted else volume.level) / 100)
        way = QPointF(math.sin(angle), -math.cos(angle))
        start, end = center + way * radius * 0.12, center + way * radius * 0.82  # hasta el aro: se lee chica
        width = max(2.0, radius * 0.17)
        # marca clara con sombra debajo: la tapa del centro es oscura (una marca oscura ahí no se ve)
        for color, offset in ((QColor(COLORS.engrave), 0.9), (QColor(COLORS.engrave_light), 0.0)):
            color.setAlphaF(0.7 if offset else 0.95)
            pen = QPen(color, width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(start + QPointF(0, offset), end + QPointF(0, offset))
