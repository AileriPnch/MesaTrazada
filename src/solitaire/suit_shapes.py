"""Palos dibujados con QPainterPath (propios, sin fuentes de símbolos): caja de -1..1 centrada en 0, y hacia
abajo. `suit_path(suit, center, size)` los ubica: `size` es el alto total."""
from functools import lru_cache

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath, QTransform

from src.solitaire.cards import Suit


def _heart() -> QPainterPath:
    path = QPainterPath(QPointF(0, 0.96))
    path.cubicTo(-0.36, 0.62, -1.0, 0.24, -1.0, -0.3)
    path.cubicTo(-1.0, -0.76, -0.56, -1.0, -0.26, -0.92)
    path.cubicTo(-0.1, -0.88, 0.0, -0.74, 0.0, -0.58)
    path.cubicTo(0.0, -0.74, 0.1, -0.88, 0.26, -0.92)
    path.cubicTo(0.56, -1.0, 1.0, -0.76, 1.0, -0.3)
    path.cubicTo(1.0, 0.24, 0.36, 0.62, 0.0, 0.96)
    path.closeSubpath()
    return path


def _diamond() -> QPainterPath:
    path = QPainterPath(QPointF(0, -1.0))
    path.quadTo(0.32, -0.36, 0.8, 0.0)
    path.quadTo(0.32, 0.36, 0.0, 1.0)
    path.quadTo(-0.32, 0.36, -0.8, 0.0)
    path.quadTo(-0.32, -0.36, 0.0, -1.0)
    path.closeSubpath()
    return path


def _spade() -> QPainterPath:
    path = QPainterPath(QPointF(0, -1.0))
    path.cubicTo(0.3, -0.62, 1.0, -0.3, 1.0, 0.18)
    path.cubicTo(1.0, 0.6, 0.6, 0.8, 0.3, 0.68)
    path.cubicTo(0.18, 0.63, 0.09, 0.55, 0.05, 0.44)
    path.cubicTo(0.1, 0.74, 0.2, 0.9, 0.4, 1.0)
    path.lineTo(-0.4, 1.0)
    path.cubicTo(-0.2, 0.9, -0.1, 0.74, -0.05, 0.44)
    path.cubicTo(-0.09, 0.55, -0.18, 0.63, -0.3, 0.68)
    path.cubicTo(-0.6, 0.8, -1.0, 0.6, -1.0, 0.18)
    path.cubicTo(-1.0, -0.3, -0.3, -0.62, 0.0, -1.0)
    path.closeSubpath()
    return path


def _club() -> QPainterPath:
    path = QPainterPath()
    for cx, cy in ((0.0, -0.5), (-0.5, 0.1), (0.5, 0.1)):
        circle = QPainterPath()
        circle.addEllipse(QPointF(cx, cy), 0.43, 0.43)
        path = path.united(circle)
    core = QPainterPath()
    core.addEllipse(QPointF(0, 0.02), 0.26, 0.26)
    stem = QPainterPath(QPointF(0.06, 0.2))
    stem.cubicTo(0.1, 0.62, 0.2, 0.88, 0.4, 1.0)
    stem.lineTo(-0.4, 1.0)
    stem.cubicTo(-0.2, 0.88, -0.1, 0.62, -0.06, 0.2)
    stem.closeSubpath()
    return path.united(core).united(stem).simplified()


_BUILDERS = {Suit.HEARTS: _heart, Suit.DIAMONDS: _diamond, Suit.SPADES: _spade, Suit.CLUBS: _club}


@lru_cache(maxsize=None)
def _unit(suit: Suit) -> QPainterPath:
    return _BUILDERS[suit]()


def suit_path(suit: Suit, center: QPointF, size: float, upside_down: bool = False) -> QPainterPath:
    """El palo de alto `size` centrado en `center` (invertido para la mitad de abajo de la carta)."""
    k = size / 2
    t = QTransform().translate(center.x(), center.y()).scale(k, -k if upside_down else k)
    return t.map(_unit(suit))
