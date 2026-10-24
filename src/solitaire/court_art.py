"""Figuras J, Q y K: diseño propio. Panel central con enrejado dorado tenue y doble filete, medallón con la
letra en Playfair Display y un emblema por figura (rey: corona de puntas; dama: diadema de arcos con perlas;
jota: escudo con el palo y una estrella), espejado abajo como en una carta de doble cabeza."""
from math import cos, pi, sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient

from src.common import theme
from src.common.theme import COLORS
from src.solitaire.cards import Card
from src.solitaire.court_emblems import crown, diadem, gold_brush, shield
from src.solitaire.suit_shapes import suit_path


def _panel(p: QPainter, rect: QRectF, ink: QColor) -> QRectF:
    w, h = rect.width(), rect.height()
    panel = QRectF(rect.left() + w * 0.27, rect.top() + h * 0.06, w * 0.46, h * 0.88)
    shape = QPainterPath()
    shape.addRoundedRect(panel, w * 0.035, w * 0.035)
    tint = QColor(ink)
    tint.setAlphaF(0.05)
    p.fillPath(shape, QColor(COLORS.paper_lit))
    p.fillPath(shape, tint)
    p.save()
    p.setClipPath(shape)
    lattice = QColor(COLORS.card_gold)
    lattice.setAlphaF(0.16)
    p.setPen(QPen(lattice, max(0.6, w * 0.004)))
    step = w * 0.065
    x = -panel.height()
    while x < panel.width() + panel.height():
        p.drawLine(QPointF(panel.left() + x, panel.top()), QPointF(panel.left() + x + panel.height(), panel.bottom()))
        p.drawLine(QPointF(panel.left() + x, panel.bottom()), QPointF(panel.left() + x + panel.height(), panel.top()))
        x += step
    p.restore()
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor(COLORS.card_gold), max(1.0, w * 0.014)))
    p.drawPath(shape)
    inner = QColor(ink)
    inner.setAlphaF(0.55)
    p.setPen(QPen(inner, max(0.6, w * 0.005)))
    p.drawRoundedRect(panel.adjusted(w * 0.022, w * 0.022, -w * 0.022, -w * 0.022), w * 0.02, w * 0.02)
    return panel


def _medallion(p: QPainter, rect: QRectF, card: Card, ink: QColor) -> float:
    w, c = rect.width(), rect.center()
    r = w * 0.19
    for side in (-1, 1):  # volutas doradas a los costados
        scroll = QPainterPath(QPointF(c.x() + side * r, c.y()))
        scroll.cubicTo(c.x() + side * (r + w * 0.03), c.y() - w * 0.06, c.x() + side * (r + w * 0.07), c.y() - w * 0.02,
                       c.x() + side * (r + w * 0.05), c.y() + w * 0.03)
        scroll.moveTo(QPointF(c.x() + side * r, c.y()))
        scroll.cubicTo(c.x() + side * (r + w * 0.03), c.y() + w * 0.06, c.x() + side * (r + w * 0.07), c.y() + w * 0.02,
                       c.x() + side * (r + w * 0.05), c.y() - w * 0.03)
        p.setPen(QPen(QColor(COLORS.card_gold), max(0.8, w * 0.009)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(scroll)
    face = QRadialGradient(c - QPointF(r * 0.3, r * 0.35), r * 1.2)
    face.setColorAt(0.0, QColor(COLORS.paper_lit))
    face.setColorAt(1.0, QColor(COLORS.paper))
    p.setPen(QPen(gold_brush(c - QPointF(r, r), c + QPointF(r, r)), max(1.0, w * 0.02)))
    p.setBrush(face)
    p.drawEllipse(c, r, r)
    p.setPen(QPen(ink, max(0.6, w * 0.006)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, r - w * 0.03, r - w * 0.03)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(COLORS.card_gold))
    for i in range(16):  # cuentas doradas alrededor
        a = 2 * pi * i / 16
        p.drawEllipse(c + QPointF(cos(a), sin(a)) * (r + w * 0.032), w * 0.008, w * 0.008)
    font = QFont(theme.TYPE.title_family)
    font.setPixelSize(round(w * (0.26 if card.rank == 12 else 0.29)))  # la cola de la Q no sale del anillo
    font.setWeight(QFont.Weight.DemiBold)
    p.setFont(font)
    p.setPen(ink)
    p.drawText(QRectF(c.x() - r, c.y() - r * 1.06, 2 * r, 2 * r), Qt.AlignmentFlag.AlignCenter, card.label)
    return r


def _half(p: QPainter, rect: QRectF, panel: QRectF, card: Card, ink: QColor, r: float) -> None:
    """Mitad de arriba: emblema de la figura y un palo chico sobre el medallón."""
    w, c = rect.width(), rect.center()
    x0, y0 = c.x() - w * 0.15, panel.top() + w * 0.06
    if card.rank == 13:
        crown(p, x0, y0, w, ink)
    elif card.rank == 12:
        diadem(p, x0, y0, w, ink)
    else:
        shield(p, x0, y0, w, card, ink)
    p.fillPath(suit_path(card.suit, QPointF(c.x(), c.y() - r - w * 0.075), w * 0.08), ink)


def draw_court(p: QPainter, rect: QRectF, card: Card) -> None:
    ink = QColor(COLORS.card_red if card.is_red else COLORS.ink)
    panel = _panel(p, rect, ink)
    r = rect.width() * 0.19
    _half(p, rect, panel, card, ink, r)
    p.save()  # la mitad de abajo, girada: carta de doble cabeza
    p.translate(rect.center())
    p.rotate(180)
    p.translate(-rect.center())
    _half(p, rect, panel, card, ink, r)
    p.restore()
    _medallion(p, rect, card, ink)
