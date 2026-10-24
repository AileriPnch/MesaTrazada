"""Frente de las cartas, por código: papel marfil con grano sutil y la luz de la app (arriba a la izquierda,
casi cenital), índices grandes, palos en la distribución clásica y As ornamentado. Las figuras (J, Q, K)
están en `court_art`; el dorso, en `card_back`. Todo vectorial: se pre-renderiza por tamaño."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen

from src.common import theme
from src.common.textures import noise_tile
from src.common.theme import CARD_LOOK, COLORS
from src.solitaire.cards import Card
from src.solitaire.court_art import draw_court
from src.solitaire.suit_shapes import suit_path

# Palos centrales: (columna -1 / 0 / 1, fila 0..1 dentro del área de palos).
_T, _M = 1 / 3, 2 / 3
PIPS = {
    2: [(0, 0), (0, 1)],
    3: [(0, 0), (0, 0.5), (0, 1)],
    4: [(-1, 0), (1, 0), (-1, 1), (1, 1)],
    5: [(-1, 0), (1, 0), (0, 0.5), (-1, 1), (1, 1)],
    6: [(-1, 0), (1, 0), (-1, 0.5), (1, 0.5), (-1, 1), (1, 1)],
    7: [(-1, 0), (1, 0), (0, 0.25), (-1, 0.5), (1, 0.5), (-1, 1), (1, 1)],
    8: [(-1, 0), (1, 0), (0, 0.25), (-1, 0.5), (1, 0.5), (0, 0.75), (-1, 1), (1, 1)],
    9: [(-1, 0), (1, 0), (-1, _T), (1, _T), (0, 0.5), (-1, _M), (1, _M), (-1, 1), (1, 1)],
    10: [(-1, 0), (1, 0), (0, 1 / 6), (-1, _T), (1, _T), (-1, _M), (1, _M), (0, 5 / 6), (-1, 1), (1, 1)],
}


def card_shape(rect: QRectF) -> QPainterPath:
    path = QPainterPath()
    r = rect.width() * CARD_LOOK.radius
    path.addRoundedRect(rect, r, r)
    return path


def ink(card: Card) -> QColor:
    return QColor(COLORS.card_red if card.is_red else COLORS.ink)


def _font(family: str, size: float, weight: int) -> QFont:
    font = QFont(family)
    font.setPixelSize(max(6, round(size)))
    font.setWeight(QFont.Weight(weight))
    return font


def draw_paper(p: QPainter, rect: QRectF) -> None:
    """Papel marfil: degradé de luz (arriba a la izquierda), grano muy sutil, borde fino y el filo de arriba
    a la izquierda apenas iluminado."""
    shape = card_shape(rect)
    light = QLinearGradient(rect.topLeft(), rect.bottomRight())
    light.setColorAt(0.0, QColor(COLORS.paper_lit))
    light.setColorAt(0.55, QColor(COLORS.paper))
    light.setColorAt(1.0, QColor(COLORS.paper_shade))
    p.fillPath(shape, light)
    p.save()
    p.setClipPath(shape)
    p.setOpacity(CARD_LOOK.grain)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
    p.drawTiledPixmap(rect, noise_tile(23, p.device().devicePixelRatioF()))
    p.restore()
    w = rect.width()
    edge = QLinearGradient(rect.topLeft(), rect.bottomRight())
    edge.setColorAt(0.0, QColor(255, 255, 255, 170))
    edge.setColorAt(0.45, QColor(255, 255, 255, 0))
    p.setPen(QPen(edge, max(1.0, w * 0.012)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    inset = max(1.0, w * 0.012)
    p.drawPath(card_shape(rect.adjusted(inset, inset, -inset, -inset)))
    border = QColor(COLORS.card_border)
    p.setPen(QPen(border, max(1.0, w * CARD_LOOK.border)))
    p.drawPath(card_shape(rect.adjusted(0.5, 0.5, -0.5, -0.5)))


def _index(p: QPainter, rect: QRectF, card: Card) -> None:
    """Valor y palo en la franja de arriba a la izquierda (lo único que se ve de una carta apilada)."""
    w = rect.width()
    court = card.rank > 10
    family = theme.TYPE.title_family if court else theme.TYPE.ui_family
    font = _font(family, w * (0.205 if court else 0.2), 600)
    if card.rank == 10:
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 88)
    p.setFont(font)
    p.setPen(ink(card))
    p.drawText(QRectF(rect.left() + w * 0.02, rect.top() + w * 0.03, w * 0.25, w * 0.24),
               Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, card.label)
    p.fillPath(suit_path(card.suit, QPointF(rect.left() + w * 0.145, rect.top() + w * 0.315), w * 0.13), ink(card))


def _pips(p: QPainter, rect: QRectF, card: Card) -> None:
    w, h = rect.width(), rect.height()
    area = QRectF(rect.left() + w * 0.345, rect.top() + h * 0.2, w * 0.31, h * 0.6)  # libre de los índices
    size = w * (0.16 if card.rank < 9 else 0.145)
    for col, row in PIPS[card.rank]:
        center = QPointF(area.center().x() + col * area.width() / 2, area.top() + row * area.height())
        p.fillPath(suit_path(card.suit, center, size, upside_down=row > 0.5), ink(card))


def _ace(p: QPainter, rect: QRectF, card: Card) -> None:
    """As: un palo grande con grabado interior y un anillo dorado fino alrededor."""
    w, c = rect.width(), rect.center()
    gold = QColor(COLORS.card_gold)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for radius, width in ((w * 0.36, w * 0.014), (w * 0.335, w * 0.005)):
        p.setPen(QPen(gold, max(0.8, width)))
        p.drawEllipse(c, radius, radius)
    for i in range(4):  # cuatro perlas en los puntos cardinales del anillo
        offset = QPointF(*((0, -1), (1, 0), (0, 1), (-1, 0))[i]) * (w * 0.36)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gold)
        p.drawEllipse(c + offset, w * 0.022, w * 0.022)
    big = suit_path(card.suit, c, w * 0.46)
    p.fillPath(big, ink(card))
    engraving = suit_path(card.suit, c, w * 0.34)
    paper = QColor(COLORS.paper_lit)
    paper.setAlphaF(0.4)
    p.setPen(QPen(paper, max(0.8, w * 0.008)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(engraving)


def draw_card_face(p: QPainter, rect: QRectF, card: Card) -> None:
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    draw_paper(p, rect)
    _index(p, rect, card)
    p.save()  # índice opuesto, rotado
    p.translate(rect.center())
    p.rotate(180)
    p.translate(-rect.center())
    _index(p, rect, card)
    p.restore()
    if card.rank == 1:
        _ace(p, rect, card)
    elif card.rank > 10:
        draw_court(p, rect, card)
    else:
        _pips(p, rect, card)
    p.restore()
