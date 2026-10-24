"""Base de los objetos apoyados en la mesa (planilla, reloj, carteles, bandejas, placas): cada widget ocupa
exactamente la caja de su objeto; su sombra y su contacto van horneados en el fondo de la mesa (ver
`shadow_layers`), así los márgenes de sombra no se pisan entre vecinos ni roban clics."""
from PyQt6.QtCore import QRect, QRectF
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QWidget

from src.chess_game.interface_art import Box
from src.chess_game.table_sprites import Placement, UiSprites, place


class Placed:
    """Mixin (las placas son QAbstractButton y el resto QWidget): ubica el PNG `key` para que su caja caiga en el
    rectángulo del widget."""
    key: str
    sprites: UiSprites
    s: float = 1.0
    at: Placement | None = None

    def box(self) -> Box:
        return self.sprites.ui.box(self.key)

    def place(self, target: QRectF, s: float) -> None:
        geometry = QRect(round(target.x()), round(target.y()), round(target.width()), round(target.height()))
        self.setGeometry(geometry)
        self.s = s
        self.at = place(self.box(), QRectF(target).translated(-geometry.x(), -geometry.y()))
        self.update()

    def shadow_names(self) -> tuple[str, ...]:
        return f"{self.key}_contacto", f"{self.key}_sombra"

    def shadow_layers(self) -> list[tuple[QImage, QRectF]]:
        """Contacto y sombra del objeto en coordenadas de la mesa (para hornearlos en el fondo)."""
        if self.at is None:
            return []
        out = []
        for name in self.shadow_names():
            image = self.sprites.ui.image(name)
            corner = self.at.origin + self.pos().toPointF()
            out.append((image, QRectF(corner.x(), corner.y(), image.width() * self.at.scale,
                                      image.height() * self.at.scale)))
        return out

    def dpr(self) -> float:
        return self.devicePixelRatioF()


class TableObject(Placed, QWidget):
    def __init__(self, sprites: UiSprites, key: str, parent: QWidget):
        QWidget.__init__(self, parent)
        self.sprites, self.key = sprites, key
