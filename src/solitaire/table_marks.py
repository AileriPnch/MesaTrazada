"""Marcas de la mesa: lugares vacíos hundidos en el paño (con su pista), el resplandor ámbar de los destinos
válidos y la luz cálida de la victoria. Píxeles físicos, una vez por tamaño de carta."""
from math import ceil

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPen, QPixmap, QRadialGradient

from src.common import theme
from src.common.glow import blur_image
from src.common.raster import edge_band, tint
from src.common.theme import CARD_LOOK, COLORS, NEON
from src.solitaire.card_assets_base import Sprite, canvas, painter
from src.solitaire.card_painter import card_shape
from src.solitaire.cards import Suit
from src.solitaire.suit_shapes import suit_path


def recess(w: int, h: int, symbol: Suit | str | None) -> Sprite:
    """Lugar vacío: un leve hundido en el paño (sombra interior arriba a la izquierda, filo de luz abajo a la
    derecha) con su pista tenue: el palo de la fundación, la K de las columnas o el reciclado del mazo."""
    image = canvas(w, h)
    rect = QRectF(0.5, 0.5, w - 1, h - 1)
    mask = canvas(w, h)
    q = painter(mask)
    q.fillPath(card_shape(rect), QColor(255, 255, 255))
    q.end()
    p = painter(image)
    p.fillPath(card_shape(rect), QColor(0, 0, 0, 52))
    d = max(1.5, w * 0.045)
    p.setOpacity(0.6)
    p.drawImage(0, 0, tint(edge_band(mask, d, d, w * 0.03), QColor(0, 0, 0)))
    p.setOpacity(0.1)
    p.drawImage(0, 0, tint(edge_band(mask, -d * 0.5, -d * 0.5, w * 0.012), QColor(COLORS.lamp)))
    p.setOpacity(1.0)
    p.setPen(QPen(QColor(255, 255, 255, 16), 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(card_shape(rect))
    mark = QColor(COLORS.lamp)
    mark.setAlphaF(0.13)
    c = QPointF(w / 2, h / 2)
    if isinstance(symbol, Suit):
        p.fillPath(suit_path(symbol, c, w * 0.42), mark)
    elif symbol == "K":
        font = QFont(theme.TYPE.title_family)
        font.setPixelSize(round(w * 0.42))
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(mark)
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "K")
    elif symbol == "recycle":
        pen = QPen(mark, max(1.5, w * 0.05))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        r = w * 0.2
        p.drawArc(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), 60 * 16, 290 * 16)
        tip = QPointF(c.x() + r * 0.5, c.y() - r * 0.87)
        p.drawLine(tip, tip + QPointF(-w * 0.09, -w * 0.03))
        p.drawLine(tip, tip + QPointF(-w * 0.03, w * 0.09))
    p.end()
    return Sprite(QPixmap.fromImage(image), QPoint(0, 0), QSize(w, h))


def glow(w: int, h: int) -> Sprite:
    """Resplandor neón ámbar tenue alrededor de un destino válido (hueco: no tapa la carta)."""
    pad = ceil(w * 0.22)
    rect = QRectF(pad, pad, w, h)
    ring = canvas(w + 2 * pad, h + 2 * pad)
    q = painter(ring)
    q.setPen(QPen(QColor(NEON.color), w * 0.05))
    q.drawPath(card_shape(rect))
    q.end()
    image = blur_image(ring, w * 0.07)
    p = painter(image)
    core = QColor(NEON.core)
    core.setAlphaF(0.85)
    p.setPen(QPen(core, max(1.0, w * 0.014)))
    p.drawPath(card_shape(rect.adjusted(-1, -1, 1, 1)))
    p.end()
    out = canvas(image.width(), image.height())
    p = painter(out)
    p.setOpacity(CARD_LOOK.target_glow)
    p.drawImage(0, 0, image)
    p.end()
    return Sprite(QPixmap.fromImage(out), QPoint(-pad, -pad), QSize(w, h))


def bloom(w: int) -> Sprite:
    """Luz ámbar cálida y amplia (celebración de la victoria)."""
    size = round(w * 6)
    image = canvas(size, size)
    p = painter(image)
    glow = QRadialGradient(QPointF(size / 2, size / 2), size / 2)
    for stop, alpha in ((0.0, 0.5), (0.4, 0.2), (1.0, 0.0)):
        color = QColor(NEON.color)
        color.setAlphaF(alpha)
        glow.setColorAt(stop, color)
    p.fillRect(image.rect(), glow)
    p.end()
    return Sprite(QPixmap.fromImage(image), QPoint(-size // 2, -size // 2), QSize(0, 0))
