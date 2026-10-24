"""Ícono de la app dibujado con QPainter: caballo de ajedrez delante de un naipe rotado."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen

from src.app import palette

# Silueta del caballo en un lienzo de 100x100 (mira a la izquierda).
_KNIGHT_OUTLINE = [
    ("M", 30, 87), ("C", 29, 72, 31, 66, 38, 60), ("C", 33, 59, 26, 60, 21, 61),
    ("C", 15, 62, 11, 58, 12, 53), ("C", 13, 48, 20, 42, 26, 36), ("C", 30, 30, 34, 24, 40, 20),
    ("L", 42, 9), ("L", 49, 17), ("C", 63, 19, 75, 30, 77, 48), ("C", 79, 62, 74, 72, 72, 87),
    ("Z",),
]
_BASE = (24, 82, 52, 12)  # x, y, ancho, alto


def _knight_path(rect: QRectF) -> QPainterPath:
    sx, sy = rect.width() / 100, rect.height() / 100

    def pt(x, y):
        return QPointF(rect.x() + x * sx, rect.y() + y * sy)

    path = QPainterPath()
    for cmd, *v in _KNIGHT_OUTLINE:
        if cmd == "M":
            path.moveTo(pt(*v))
        elif cmd == "L":
            path.lineTo(pt(*v))
        elif cmd == "C":
            path.cubicTo(pt(v[0], v[1]), pt(v[2], v[3]), pt(v[4], v[5]))
        else:
            path.closeSubpath()
    bx, by, bw, bh = _BASE
    base = QPainterPath()
    base.addRoundedRect(QRectF(pt(bx, by), pt(bx + bw, by + bh)), 3 * sx, 3 * sy)
    return path.united(base)


def _draw_card(p: QPainter, size: float) -> None:
    w, h = size * 0.46, size * 0.62
    p.save()
    p.translate(size * 0.64, size * 0.42)
    p.rotate(14)
    card = QRectF(-w / 2, -h / 2, w, h)
    p.setPen(QPen(QColor(palette.ACCENT_DARK), max(1.0, size / 64)))
    p.setBrush(QColor(palette.ACCENT))
    p.drawRoundedRect(card, size * 0.05, size * 0.05)
    # Diamante (palo) en la esquina, en tinta oscura.
    pip = QPainterPath()
    cx, cy, r = card.right() - w * 0.24, card.top() + h * 0.2, w * 0.11
    pip.moveTo(cx, cy - r)
    pip.lineTo(cx + r, cy)
    pip.lineTo(cx, cy + r)
    pip.lineTo(cx - r, cy)
    pip.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(palette.INK))
    p.drawPath(pip)
    p.restore()


def paint_app_icon(p: QPainter, size: int) -> None:
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    simple = size <= 24
    bg = QRectF(0, 0, size, size).adjusted(0.5, 0.5, -0.5, -0.5)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(palette.WINDOW_BG))
    p.drawRoundedRect(bg, size * 0.2, size * 0.2)

    if simple:
        knight_rect = QRectF(size * 0.06, size * 0.04, size * 0.88, size * 0.9)
    else:
        _draw_card(p, size)
        knight_rect = QRectF(size * 0.04, size * 0.14, size * 0.72, size * 0.78)
    knight = _knight_path(knight_rect)
    outline = 0 if simple else max(1.0, size / 40)
    p.setPen(QPen(QColor(palette.INK), outline) if outline else Qt.PenStyle.NoPen)
    p.setBrush(QColor(palette.IVORY))
    p.drawPath(knight)
    if size >= 48:  # ojo sólo cuando hay resolución para verlo
        sx, sy = knight_rect.width() / 100, knight_rect.height() / 100
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(palette.INK))
        p.drawEllipse(QPointF(knight_rect.x() + 36 * sx, knight_rect.y() + 36 * sy), 3.2 * sx, 3.2 * sy)


def render_app_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    paint_app_icon(painter, size)
    painter.end()
    return image
