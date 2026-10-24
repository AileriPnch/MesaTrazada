"""Piezas comunes de los sprites de la mesa: el sprite (pixmap + dónde va respecto de su carta) y lienzos
transparentes en píxeles físicos."""
from dataclasses import dataclass

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap

from src.common.raster import FORMAT


@dataclass(frozen=True)
class Sprite:
    pixmap: QPixmap
    offset: QPoint  # esquina del sprite respecto de la esquina de la carta
    size: QSize  # la carta (sin sombra)


def canvas(width: int, height: int) -> QImage:
    image = QImage(max(1, width), max(1, height), FORMAT)
    image.fill(Qt.GlobalColor.transparent)
    return image


def painter(image: QImage) -> QPainter:
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    return p
