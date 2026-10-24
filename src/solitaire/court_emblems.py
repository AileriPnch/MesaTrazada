"""Emblemas de las figuras, en oro con detalles del color del palo: corona de puntas (rey), diadema de arcos
con perlas y roseta (dama) y escudo con el palo, estrella y laureles (jota). Medidas en anchos de carta."""
from math import cos, pi, sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF

from src.common.theme import COLORS
from src.solitaire.cards import Card
from src.solitaire.suit_shapes import suit_path


def gold_brush(top_left: QPointF, bottom_right: QPointF) -> QLinearGradient:
    gradient = QLinearGradient(top_left, bottom_right)
    gradient.setColorAt(0.0, QColor(COLORS.card_gold_lit))
    gradient.setColorAt(0.6, QColor(COLORS.card_gold))
    gradient.setColorAt(1.0, QColor(COLORS.card_gold).darker(135))
    return gradient


def gold_pen(w: float, k: float = 0.006) -> QPen:
    return QPen(QColor(COLORS.card_gold).darker(150), max(0.7, w * k))


def crown(p: QPainter, x0: float, y0: float, w: float, ink: QColor) -> None:
    bw = w * 0.3
    body = QPolygonF([QPointF(x0, y0 + w * 0.15), QPointF(x0 + w * 0.02, y0 + w * 0.045),
                      QPointF(x0 + w * 0.085, y0 + w * 0.11), QPointF(x0 + bw / 2, y0 + w * 0.01),
                      QPointF(x0 + bw - w * 0.085, y0 + w * 0.11), QPointF(x0 + bw - w * 0.02, y0 + w * 0.045),
                      QPointF(x0 + bw, y0 + w * 0.15)])
    p.setPen(gold_pen(w))
    p.setBrush(gold_brush(QPointF(x0, y0), QPointF(x0 + bw, y0 + w * 0.2)))
    p.drawPolygon(body)
    p.drawRoundedRect(QRectF(x0 - w * 0.01, y0 + w * 0.145, bw + w * 0.02, w * 0.055), w * 0.012, w * 0.012)
    for x, y in ((x0 + w * 0.02, y0 + w * 0.045), (x0 + bw / 2, y0 + w * 0.01), (x0 + bw - w * 0.02, y0 + w * 0.045)):
        p.drawEllipse(QPointF(x, y - w * 0.012), w * 0.018, w * 0.018)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(ink)
    for i in range(3):  # piedras en la banda
        p.drawEllipse(QPointF(x0 + bw * (0.22 + 0.28 * i), y0 + w * 0.1725), w * 0.016, w * 0.012)


def diadem(p: QPainter, x0: float, y0: float, w: float, ink: QColor) -> None:
    bw = w * 0.3
    shape = QPainterPath()
    shape.addRoundedRect(QRectF(x0, y0 + w * 0.14, bw, w * 0.05), w * 0.015, w * 0.015)
    tops = []
    for i in range(3):
        cx, radius = x0 + bw * (1 / 6 + i / 3), bw / 6 - w * 0.004
        arch = QPainterPath()
        tall = radius * (1.75 if i == 1 else 1.35)
        arch.addEllipse(QPointF(cx, y0 + w * 0.15), radius, tall)
        shape = shape.united(arch)
        tops.append(QPointF(cx, y0 + w * 0.15 - tall))
    clip = QPainterPath()
    clip.addRect(QRectF(x0 - w, y0 - w, bw + 2 * w, w * 1.19))
    p.setPen(gold_pen(w))
    p.setBrush(gold_brush(QPointF(x0, y0), QPointF(x0 + bw, y0 + w * 0.2)))
    p.drawPath(shape.intersected(clip))
    p.setBrush(QColor(COLORS.paper_lit))
    for top in tops:  # perlas
        p.drawEllipse(top - QPointF(0, w * 0.012), w * 0.017, w * 0.017)
    center = QPointF(x0 + bw / 2, y0 + w * 0.105)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(ink)
    for i in range(6):  # roseta
        a = 2 * pi * i / 6
        p.drawEllipse(center + QPointF(cos(a), sin(a)) * (w * 0.022), w * 0.013, w * 0.013)
    p.setBrush(QColor(COLORS.card_gold_lit))
    p.drawEllipse(center, w * 0.012, w * 0.012)


def shield(p: QPainter, x0: float, y0: float, w: float, card: Card, ink: QColor) -> None:
    cx = x0 + w * 0.15
    star = QPolygonF()
    for i in range(16):  # estrella de ocho puntas
        a = -pi / 2 + i * pi / 8
        radius = w * (0.04 if i % 2 == 0 else 0.016)
        star.append(QPointF(cx + cos(a) * radius, y0 + w * 0.035 + sin(a) * radius))
    p.setPen(gold_pen(w, 0.004))
    p.setBrush(gold_brush(QPointF(cx - w * 0.04, y0), QPointF(cx + w * 0.04, y0 + w * 0.08)))
    p.drawPolygon(star)
    shield = QPainterPath(QPointF(cx - w * 0.08, y0 + w * 0.085))
    shield.lineTo(cx + w * 0.08, y0 + w * 0.085)
    shield.cubicTo(cx + w * 0.08, y0 + w * 0.15, cx + w * 0.05, y0 + w * 0.19, cx, y0 + w * 0.215)
    shield.cubicTo(cx - w * 0.05, y0 + w * 0.19, cx - w * 0.08, y0 + w * 0.15, cx - w * 0.08, y0 + w * 0.085)
    p.setPen(QPen(QColor(COLORS.card_gold), max(0.8, w * 0.012)))
    p.setBrush(QColor(COLORS.paper_lit))
    p.drawPath(shield)
    p.fillPath(suit_path(card.suit, QPointF(cx, y0 + w * 0.14), w * 0.085), ink)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(COLORS.card_gold))
    for side in (-1, 1):  # hojas de laurel a los costados
        for k in range(3):
            p.save()
            p.translate(cx + side * w * (0.1 + 0.012 * k), y0 + w * (0.1 + 0.04 * k))
            p.rotate(side * (35 - 12 * k))
            p.drawEllipse(QPointF(0, 0), w * 0.011, w * 0.024)
            p.restore()
