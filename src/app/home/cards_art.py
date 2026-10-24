"""Naipes desparramados y un abanico, con el mismo diseño de cartas del juego (card_painter)."""
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QTransform

from src.common.glow import blurred
from src.solitaire.card_back import draw_card_back
from src.solitaire.card_painter import draw_card_face
from src.solitaire.cards import Card, Suit
from src.solitaire.table_layout import ASPECT

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS
FAN = [Card(10, D), Card(11, C), Card(12, H), Card(13, S), Card(1, H)]
FAN_SPREAD = 13.0  # grados entre cartas del abanico
FAN_PIVOT = 1.25  # distancia del eje del abanico al centro de la carta, en altos de carta

# Cartas sueltas: (x, y relativos al área, ángulo, carta o None = dorso). Se dibujan en orden.
SCATTER = [
    (0.11, 0.25, -21.0, None), (0.13, 0.27, -14.0, None), (0.15, 0.29, -8.0, None),  # pila del mazo
    (0.88, 0.22, 17.0, Card(7, C)), (0.88, 0.78, -12.0, None), (0.12, 0.79, 8.0, Card(3, D)),
]


@dataclass(frozen=True)
class PlacedCard:
    center: QPointF
    angle: float
    card: Card | None

    def transform(self) -> QTransform:
        return QTransform().translate(self.center.x(), self.center.y()).rotate(self.angle)


def _card_rect(width: float) -> QRectF:
    return QRectF(-width / 2, -width * ASPECT / 2, width, width * ASPECT)


def card_width(area: QRectF) -> float:
    return min(area.width() * 0.19, area.height() / ASPECT * 0.5)


def placements(area: QRectF) -> tuple[list[PlacedCard], list[PlacedCard]]:
    """(sueltas, abanico) en coordenadas de pantalla."""
    w = card_width(area)
    loose = [PlacedCard(QPointF(area.left() + x * area.width(), area.top() + y * area.height()), a, c)
             for x, y, a, c in SCATTER]
    pivot = QPointF(area.center().x(), area.center().y() + w * ASPECT * (FAN_PIVOT + 0.05))
    fan = []
    for i, card in enumerate(FAN):
        angle = (i - (len(FAN) - 1) / 2) * FAN_SPREAD
        t = QTransform().translate(pivot.x(), pivot.y()).rotate(angle)
        fan.append(PlacedCard(t.map(QPointF(0, -w * ASPECT * FAN_PIVOT)), angle, card))
    return loose, fan


def fan_outline(area: QRectF) -> QPainterPath:
    """Silueta del abanico (unión de sus cartas): ahí se enciende el neón."""
    w = card_width(area)
    path = QPainterPath()
    for placed in placements(area)[1]:
        shape = QPainterPath()
        shape.addRoundedRect(_card_rect(w), w * 0.08, w * 0.08)
        path = path.united(placed.transform().map(shape))
    return path.simplified()


def _paint_card(p: QPainter, placed: PlacedCard, width: float) -> None:
    p.save()
    p.setTransform(placed.transform(), combine=True)
    if placed.card is None:
        draw_card_back(p, _card_rect(width))
    else:
        draw_card_face(p, _card_rect(width), placed.card)
    p.restore()


def _shadows(p: QPainter, cards: list[PlacedCard], bounds: QRectF, width: float, dpr: float) -> None:
    def draw(q: QPainter) -> None:
        q.translate(-bounds.left() + width * 0.04, -bounds.top() + width * 0.07)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(0, 0, 0, 170))
        for placed in cards:
            q.save()
            q.setTransform(placed.transform(), combine=True)
            q.drawRoundedRect(_card_rect(width), width * 0.08, width * 0.08)
            q.restore()

    p.drawImage(bounds.topLeft(), blurred(bounds.width(), bounds.height(), dpr, width * 0.08, draw))


def paint_cards(p: QPainter, area: QRectF, bounds: QRectF, dpr: float) -> None:
    """Dibuja las cartas ubicadas en `area`; las sombras se calculan sobre `bounds` (la mitad entera)."""
    width = card_width(area)
    loose, fan = placements(area)
    _shadows(p, loose, bounds, width, dpr)
    for placed in loose:
        _paint_card(p, placed, width)
    _shadows(p, fan, bounds, width, dpr)
    for placed in fan:
        _paint_card(p, placed, width)
