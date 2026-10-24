"""Operaciones de imagen para pre-renderizar efectos: recortes por máscara, franjas de borde (una silueta menos
ella misma corrida) y teñido. Todo en píxeles físicos."""
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QImage, QPainter

from src.common.glow import blur_image

FORMAT = QImage.Format.Format_ARGB32_Premultiplied


def clip(layer: QImage, mask: QImage) -> QImage:
    p = QPainter(layer)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
    p.drawImage(0, 0, mask)
    p.end()
    return layer


def edge_band(mask: QImage, dx: float, dy: float, blur: float) -> QImage:
    """Franja interior del borde que mira en contra de (dx, dy): la silueta menos ella misma corrida."""
    band_image = QImage(mask)
    p = QPainter(band_image)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
    p.drawImage(QPointF(dx, dy), mask)
    p.end()
    return clip(blur_image(band_image, blur), mask)


def tint(alpha_image: QImage, color: QColor) -> QImage:
    p = QPainter(alpha_image)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(alpha_image.rect(), color)
    p.end()
    return alpha_image
