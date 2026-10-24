"""Superficies de la mesa por código: madera muy oscura, paño desaturado, ruido, luz y viñeteado."""
import random
from functools import lru_cache
from math import ceil, sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                         QRadialGradient)

from src.common.theme import COLORS

NOISE_TILE = 192


@lru_cache(maxsize=8)
def noise_tile(seed: int, dpr: float) -> QPixmap:
    """Mosaico de ruido gris (determinístico) a la resolución física: grano de 1 px real."""
    data = random.Random(seed).randbytes(NOISE_TILE * NOISE_TILE)
    image = QImage(data, NOISE_TILE, NOISE_TILE, NOISE_TILE, QImage.Format.Format_Grayscale8).copy()
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


def _grain(p: QPainter, rect: QRectF, opacity: float, seed: int) -> None:
    p.save()
    p.setOpacity(opacity)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
    p.drawTiledPixmap(rect, noise_tile(seed, p.device().devicePixelRatioF()))
    p.restore()


WOOD_RESOLUTION = 0.5  # las vetas son difusas: se dibujan a media resolución y se amplían (mitad de costo)


def _planks(p: QPainter, rect: QRectF, seed: int) -> None:
    """Tablones horizontales con vetas onduladas y juntas oscuras."""
    base = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    base.setColorAt(0, QColor(COLORS.wood_deep))
    base.setColorAt(0.55, QColor(COLORS.wood))
    base.setColorAt(1, QColor(COLORS.wood_deep))
    p.fillRect(rect, base)
    rng = random.Random(seed)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    plank = rect.height() / 5.5
    grain = QColor(COLORS.wood_grain)
    for i in range(int(rect.height() / max(2.0, plank / 14)) + 1):
        y = rect.top() + i * plank / 14 + rng.uniform(-2, 2)
        amp, freq, phase = rng.uniform(1, plank * 0.18), rng.uniform(1.5, 4.5), rng.uniform(0, 6.3)
        path = QPainterPath(QPointF(rect.left(), y))
        steps = 24
        for s in range(1, steps + 1):
            x = rect.left() + rect.width() * s / steps
            path.lineTo(x, y + amp * sin(phase + freq * s / steps * 6.283))
        grain.setAlphaF(rng.uniform(0.05, 0.22))
        p.setPen(QPen(grain, rng.uniform(0.6, 2.2)))
        p.drawPath(path)
    seam = QColor(COLORS.wood_deep)
    seam.setAlphaF(0.9)
    p.setPen(QPen(seam, max(1.0, plank * 0.02)))
    y = rect.top() + plank * rng.uniform(0.3, 0.8)
    while y < rect.bottom():
        p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
        y += plank


def paint_wood(p: QPainter, rect: QRectF, seed: int = 7) -> None:
    """Madera muy oscura: tablones (a media resolución) y un grano fino encima (a resolución completa)."""
    scale = p.device().devicePixelRatioF() * WOOD_RESOLUTION
    image = QImage(max(1, ceil(rect.width() * scale)), max(1, ceil(rect.height() * scale)), QImage.Format.Format_RGB32)
    q = QPainter(image)
    q.scale(scale, scale)
    q.translate(-rect.topLeft())
    _planks(q, rect, seed)
    q.end()
    p.save()
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.drawImage(rect, image)
    p.restore()
    _grain(p, rect, 0.10, seed)


def paint_felt(p: QPainter, rect: QRectF, seed: int = 11) -> None:
    """Paño muy oscuro y desaturado: degradé suave + fibras (ruido fino)."""
    base = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.75)
    base.setColorAt(0, QColor(COLORS.felt))
    base.setColorAt(1, QColor(COLORS.felt_deep))
    p.fillRect(rect, base)
    _grain(p, rect, 0.14, seed)


def paint_casino_felt(p: QPainter, rect: QRectF, spot: QPointF, seed: int = 31) -> None:
    """Paño de casino profundo: más claro bajo el foco cenital (`spot`) y cayendo hacia los bordes; grano de
    fibra fino y una mancha más amplia, muy suave, para que se lea como tela."""
    base = QRadialGradient(spot, max(rect.width(), rect.height()) * 0.72)
    base.setColorAt(0.0, QColor(COLORS.felt_table_lit))
    base.setColorAt(0.42, QColor(COLORS.felt_table))
    base.setColorAt(1.0, QColor(COLORS.felt_table_deep))
    p.fillRect(rect, base)
    _grain(p, rect, 0.16, seed)
    p.save()  # mancha de la tela: el mismo ruido, ampliado y suavizado
    p.setOpacity(0.07)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.scale(6, 6)
    p.drawTiledPixmap(QRectF(rect.topLeft() / 6, rect.size() / 6), noise_tile(seed + 1, 1.0))
    p.restore()


def paint_light(p: QPainter, center: QPointF, radius: float, alpha: float) -> None:
    """Luz cálida de lámpara: círculo difuso que aclara lo que hay debajo."""
    gradient = QRadialGradient(center, radius)
    for stop, a in ((0.0, alpha), (0.45, alpha * 0.55), (1.0, 0.0)):
        color = QColor(COLORS.lamp)
        color.setAlphaF(a)
        gradient.setColorAt(stop, color)
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(gradient))
    p.drawEllipse(center, radius, radius)
    p.restore()


def paint_vignette(p: QPainter, rect: QRectF, strength: float = 0.78) -> None:
    """Oscurece suavemente hacia los bordes (elíptico, acompaña la proporción de la ventana)."""
    p.save()
    p.translate(rect.center())
    p.scale(rect.width() / rect.height(), 1.0)
    radius = rect.height() * 0.78
    gradient = QRadialGradient(QPointF(0, 0), radius)
    for stop, a in ((0.0, 0.0), (0.55, 0.0), (0.8, strength * 0.45), (1.0, strength)):
        color = QColor(COLORS.shadow)
        color.setAlphaF(a)
        gradient.setColorAt(stop, color)
    p.fillRect(QRectF(-radius * 2, -radius * 2, radius * 4, radius * 4), gradient)
    p.restore()


def paint_top_shade(p: QPainter, rect: QRectF, height: float, alpha: float = 0.55) -> None:
    """Sombra arriba para que el encabezado se lea sobre cualquier textura."""
    gradient = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + height))
    top, bottom = QColor(COLORS.shadow), QColor(COLORS.shadow)
    top.setAlphaF(alpha)
    bottom.setAlphaF(0.0)
    gradient.setColorAt(0, top)
    gradient.setColorAt(1, bottom)
    p.fillRect(QRectF(rect.left(), rect.top(), rect.width(), height), gradient)
