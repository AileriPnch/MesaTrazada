"""Pieza suelta como pixmap, desde el mismo render que el tablero (sin sombra ni reflejo): el dibujo de la
pantalla de inicio (`piece_pixmap`, el sprite entero con su punto de apoyo) y el diálogo de coronación
(`piece_icon`, recortada a su silueta para que llene el ícono). Usa sólo el cuerpo de cada pieza: el inicio
no carga el resto del arte."""
from functools import lru_cache

import chess
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QBitmap, QImage, QPainter, QPixmap, QRegion

from src.chess_game.art_library import ANCHOR, FORMAT, piece_body


def _smooth(image: QImage, width: int, height: int) -> QImage:
    return image.scaled(max(1, width), max(1, height), Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)


def piece_pixmap(piece: chess.Piece, size: int, dpr: float = 1.0) -> QPixmap:
    """El sprite entero (cubre 1,2 casillas) en `size` x `size` px lógicos; apoya en `ground_ratio()`."""
    side = max(1, round(size * dpr))
    pixmap = QPixmap.fromImage(_smooth(piece_body(piece), side, side))
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


def ground_ratio() -> float:
    """Altura del punto de apoyo (centro de la base) dentro del sprite (0..1)."""
    return ANCHOR.y() / 512.0


@lru_cache(maxsize=None)
def _bounds(piece: chess.Piece) -> QRect:
    """Caja de la silueta de la pieza en el render (alfa >= 50 %)."""
    mask = piece_body(piece).createAlphaMask(Qt.ImageConversionFlag.ThresholdAlphaDither)
    return QRegion(QBitmap.fromImage(mask)).boundingRect()


def piece_icon(piece: chess.Piece, size: int, dpr: float = 1.0) -> QPixmap:
    """La pieza recortada a su silueta y centrada en un cuadrado de `size` px lógicos (sin deformar)."""
    side = max(1, round(size * dpr))
    box = _bounds(piece)
    fit = side / max(box.width(), box.height())
    image = _smooth(piece_body(piece).copy(box), round(box.width() * fit), round(box.height() * fit))
    canvas = QImage(side, side, FORMAT)
    canvas.fill(Qt.GlobalColor.transparent)
    p = QPainter(canvas)
    p.drawImage(QPoint((side - image.width()) // 2, (side - image.height()) // 2), image)
    p.end()
    pixmap = QPixmap.fromImage(canvas)
    pixmap.setDevicePixelRatio(dpr)
    return pixmap
