"""Fondo de la pantalla del solitario: paño de casino profundo con grano de fibra, un foco cenital que deja el
centro de la mesa más iluminado, viñeteado hacia los bordes y una sombra arriba para que la barra se lea.
Una imagen opaca por tamaño y DPR, en píxeles físicos (la regenera `CachedBackdrop`)."""
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainter, QPixmap

from src.common.glow import render_layer, to_device
from src.common.textures import paint_casino_felt, paint_light, paint_top_shade, paint_vignette


def render_felt(width: int, height: int, dpr: float, spot: QPointF, bar_bottom: float) -> tuple[QPointF, QPixmap]:
    full = QRectF(0, 0, width, height)

    def draw(p: QPainter) -> None:
        paint_casino_felt(p, full, spot)
        paint_light(p, spot, max(width, height) * 0.55, 0.06)
        paint_vignette(p, full, 0.72)
        paint_top_shade(p, full, bar_bottom * 1.6, 0.5)

    return to_device(render_layer(full, dpr, draw, opaque=True), dpr)
