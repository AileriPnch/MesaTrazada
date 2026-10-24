"""Dorso: el enrejado ámbar de siempre, refinado (doble filete, rombo central, perlas en las esquinas) y con un
brillo tipo foil que va aparte (`draw_back_foil`): se copia encima con más o menos opacidad según cuánto le
llegue el foco de la mesa."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPainterPathStroker, QPen

from src.common.theme import CARD_LOOK, COLORS
from src.solitaire.card_painter import card_shape


def _inner(rect: QRectF) -> QRectF:
    w = rect.width()
    return rect.adjusted(w * 0.075, w * 0.075, -w * 0.075, -w * 0.075)


def _lattice(rect: QRectF) -> QPainterPath:
    """Enrejado diagonal + doble filete + rombo central, como trazo (para pintarlo o recortar el foil)."""
    w, inner = rect.width(), _inner(rect)
    lines = QPainterPath()
    step, span = w * 0.105, inner.width() + inner.height()
    x = -span
    while x < span:
        lines.moveTo(inner.left() + x, inner.top())
        lines.lineTo(inner.left() + x + inner.height(), inner.bottom())
        lines.moveTo(inner.left() + x, inner.bottom())
        lines.lineTo(inner.left() + x + inner.height(), inner.top())
        x += step
    clip = QPainterPath()
    clip.addRoundedRect(inner, w * 0.04, w * 0.04)
    stroker = QPainterPathStroker()
    stroker.setWidth(max(0.8, w * 0.009))
    shape = stroker.createStroke(lines).intersected(clip)
    frames = QPainterPath()
    for inset, width in ((0.0, 0.02), (w * 0.03, 0.007)):
        ring = QPainterPath()
        r = inner.adjusted(inset, inset, -inset, -inset)
        ring.addRoundedRect(r, w * 0.04, w * 0.04)
        stroker.setWidth(max(0.8, w * width))
        frames = frames.united(stroker.createStroke(ring))
    return shape.united(frames)


def _diamond(rect: QRectF, scale: float) -> QPainterPath:
    c, d = rect.center(), rect.width() * 0.1 * scale
    path = QPainterPath(QPointF(c.x(), c.y() - d * 1.45))
    path.lineTo(c.x() + d, c.y())
    path.lineTo(c.x(), c.y() + d * 1.45)
    path.lineTo(c.x() - d, c.y())
    path.closeSubpath()
    return path


def draw_card_back(p: QPainter, rect: QRectF) -> None:
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    w, shape = rect.width(), card_shape(rect)
    base = QLinearGradient(rect.topLeft(), rect.bottomRight())
    base.setColorAt(0.0, QColor(COLORS.card_back).lighter(118))
    base.setColorAt(1.0, QColor(COLORS.card_back).darker(125))
    p.fillPath(shape, base)
    gold = QLinearGradient(rect.topLeft(), rect.bottomRight())  # oro: más vivo hacia la luz
    gold.setColorAt(0.0, QColor(COLORS.card_gold_lit))
    gold.setColorAt(0.5, QColor(COLORS.accent))
    gold.setColorAt(1.0, QColor(COLORS.accent_dark))
    p.save()
    p.setOpacity(0.55)
    p.fillPath(_lattice(rect), gold)
    p.restore()
    p.fillPath(_diamond(rect, 1.25), QColor(COLORS.card_back))
    p.setPen(QPen(gold, max(1.0, w * 0.014)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(_diamond(rect, 1.25))
    p.fillPath(_diamond(rect, 0.62), gold)
    inner = _inner(rect)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(gold)
    for corner in (inner.topLeft(), inner.topRight(), inner.bottomLeft(), inner.bottomRight()):
        toward = (rect.center() - corner) * 0.06
        p.drawEllipse(corner + toward, w * 0.016, w * 0.016)
    p.setPen(QPen(QColor(COLORS.accent_dark), max(1.0, w * 0.01)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(card_shape(rect.adjusted(0.5, 0.5, -0.5, -0.5)))
    p.restore()


def draw_back_foil(p: QPainter, rect: QRectF) -> None:
    """Sólo el brillo metálico del enrejado: una banda clara en diagonal, recortada al oro."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    band = QLinearGradient(rect.topLeft(), rect.bottomRight())
    light = QColor(COLORS.card_gold_lit)
    for stop, alpha in ((0.0, 0.0), (0.28, 0.0), (0.42, 1.0), (0.56, 0.0), (1.0, 0.0)):
        light.setAlphaF(alpha * CARD_LOOK.foil)
        band.setColorAt(stop, QColor(light))
    p.fillPath(_lattice(rect).united(_diamond(rect, 0.62)), band)
    p.restore()
