"""Geometría de la mesa: tamaños que escalan con la ventana, abanicos y detección de clics/sueltas."""
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, QSizeF

from src.solitaire.cards import Suit
from src.solitaire.klondike import FOUNDATIONS, TABLEAU_COLUMNS, KlondikeGame, PileKind, PileRef

ASPECT = 1.4  # alto / ancho de una carta
GAP_RATIO = 0.16  # separación entre columnas, relativa al ancho de carta
DOWN_OFFSET = 0.1  # escalón de las cartas boca abajo, relativo al alto (poco: sólo se ve el canto)
UP_OFFSET = 0.28  # escalón de las boca arriba: deja leer valor y palo enteros
MIN_DOWN_OFFSET = 0.045  # mínimo para boca abajo al comprimir
WASTE_FAN = 0.24  # abanico del descarte, relativo al ancho
WASTE_VISIBLE = 3  # cartas del descarte a la vista (en los dos modos); sólo la de arriba se juega
MIN_HEIGHT_IN_CARDS = 4.1  # fila superior + columna de ~7 cartas sin comprimir


@dataclass(frozen=True)
class TableLayout:
    left: float
    top: float
    card_w: float
    gap: float
    height: float  # alto total disponible

    @classmethod
    def fit(cls, width: float, height: float, margin: float = 16) -> "TableLayout":
        by_width = (width - 2 * margin) / (TABLEAU_COLUMNS + (TABLEAU_COLUMNS - 1) * GAP_RATIO)
        by_height = (height - 2 * margin) / (MIN_HEIGHT_IN_CARDS * ASPECT)
        card_w = max(24.0, min(by_width, by_height))
        gap = card_w * GAP_RATIO
        used = TABLEAU_COLUMNS * card_w + (TABLEAU_COLUMNS - 1) * gap
        return cls((width - used) / 2, margin, card_w, gap, height - margin)

    @property
    def card_h(self) -> float:
        return self.card_w * ASPECT

    @property
    def card_size(self) -> QSizeF:
        return QSizeF(self.card_w, self.card_h)

    def _slot(self, col: int, y: float) -> QRectF:
        return QRectF(self.left + col * (self.card_w + self.gap), y, self.card_w, self.card_h)

    @property
    def tableau_top(self) -> float:
        return self.top + self.card_h + self.gap * 2

    def slot_rect(self, ref: PileRef) -> QRectF:
        if ref.kind is PileKind.STOCK:
            return self._slot(0, self.top)
        if ref.kind is PileKind.WASTE:
            return self._slot(1, self.top)
        if ref.kind is PileKind.FOUNDATION:
            return self._slot(TABLEAU_COLUMNS - FOUNDATIONS + ref.index, self.top)
        return self._slot(ref.index, self.tableau_top)

    def top_rect(self, game: KlondikeGame, ref: PileRef) -> QRectF:
        """Donde se apoyaría una carta en `ref`: sobre la última de la columna, o el lugar si está vacía."""
        if ref.kind is PileKind.TABLEAU and game.tableau[ref.index].cards:
            return self.column_rects(game, ref.index)[-1]
        return self.slot_rect(ref)

    def waste_rects(self, game: KlondikeGame) -> list[tuple[int, QRectF]]:
        """(índice, rect) de las cartas visibles del descarte: la de arriba va última."""
        visible = min(len(game.waste), WASTE_VISIBLE)
        base = self.slot_rect(PileRef(PileKind.WASTE))
        first = len(game.waste) - visible
        return [(first + i, base.translated(i * self.card_w * WASTE_FAN, 0)) for i in range(visible)]

    def column_rects(self, game: KlondikeGame, col: int) -> list[QRectF]:
        column = game.tableau[col]
        base = self.slot_rect(PileRef(PileKind.TABLEAU, col))
        down, up = self._offsets(len(column.cards) - 1, column.hidden, base.top())
        rects, y = [], base.top()
        for i in range(len(column.cards)):
            rects.append(QRectF(base.left(), y, self.card_w, self.card_h))
            y += up if column.is_face_up(i) else down
        return rects

    def _offsets(self, n: int, hidden: int, top: float) -> tuple[float, float]:
        """Solapamientos (boca abajo, boca arriba) para `n` cartas tapadas por otra.

        Columnas largas se comprimen en dos etapas para no salirse de la ventana: primero las
        boca abajo (hasta MIN_DOWN_OFFSET), después las boca arriba."""
        down, up = DOWN_OFFSET * self.card_h, UP_OFFSET * self.card_h
        downs = min(hidden, n)
        ups = n - downs
        available = max(0.0, self.height - top - self.card_h)
        if downs * down + ups * up <= available:
            return down, up
        if downs:
            down = max(MIN_DOWN_OFFSET * self.card_h, (available - ups * up) / downs)
        if downs * down + ups * up > available and ups:
            up = (available - downs * down) / ups
        if up < 0 or (not ups and downs * down > available):  # caso extremo: reparto parejo
            down = up = available / n
        return down, up

    def hit_test(self, game: KlondikeGame, point: QPointF) -> tuple[PileRef, int] | None:
        stock = PileRef(PileKind.STOCK)
        if self.slot_rect(stock).contains(point):
            return stock, 0
        waste = self.waste_rects(game)
        if waste and waste[-1][1].contains(point):
            return PileRef(PileKind.WASTE), waste[-1][0]
        for i in range(FOUNDATIONS):
            ref = PileRef(PileKind.FOUNDATION, i)
            if game.foundations[i] and self.slot_rect(ref).contains(point):
                return ref, len(game.foundations[i]) - 1
        for col in range(TABLEAU_COLUMNS):
            for index, rect in reversed(list(enumerate(self.column_rects(game, col)))):
                if rect.contains(point):
                    return PileRef(PileKind.TABLEAU, col), index
        return None

    def drop_target(self, game: KlondikeGame, src: PileRef, index: int, card_rect: QRectF) -> PileRef | None:
        """Destino válido con mayor superposición con la carta arrastrada, o None."""
        candidates = [PileRef(PileKind.FOUNDATION, i) for i in range(FOUNDATIONS)]
        candidates += [PileRef(PileKind.TABLEAU, c) for c in range(TABLEAU_COLUMNS)]
        scored = []
        for ref in candidates:
            overlap = self.top_rect(game, ref).intersected(card_rect)
            area = overlap.width() * overlap.height()
            if area > 0:
                scored.append((area, ref))
        for _, ref in sorted(scored, key=lambda item: -item[0]):
            if game.can_move(src, index, ref):
                return ref
        return None


LABEL_ORDER = (Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS, Suit.SPADES)  # palos de las fundaciones vacías


def foundation_labels(game: KlondikeGame) -> list[Suit | None]:
    """Palo que muestra cada fundación vacía: uno que todavía falta (cualquier As va a cualquier lugar vacío,
    así que nunca se muestra un palo que ya tiene su fundación). None si está ocupada."""
    free = [s for s in LABEL_ORDER if not any(pile and pile[0].suit is s for pile in game.foundations)]
    labels: list[Suit | None] = [None] * FOUNDATIONS
    empty = [i for i in range(FOUNDATIONS) if not game.foundations[i]]
    for i in empty:  # primero cada una con su palo de siempre, si sigue libre
        if LABEL_ORDER[i] in free:
            labels[i] = LABEL_ORDER[i]
            free.remove(LABEL_ORDER[i])
    for i in empty:
        if labels[i] is None and free:
            labels[i] = free.pop(0)
    return labels
