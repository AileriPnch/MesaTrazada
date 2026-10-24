"""Arrastre en curso (qué cartas se levantaron, dónde se agarraron, destinos válidos para marcarlos) y adónde
va una carta con doble clic. Sólo consulta las reglas de `KlondikeGame`: no cambia ninguna."""
from dataclasses import dataclass, field

from PyQt6.QtCore import QPointF, QRectF, QSizeF

from src.common.theme import CARD_LOOK
from src.solitaire.cards import Card
from src.solitaire.klondike import FOUNDATIONS, TABLEAU_COLUMNS, KlondikeGame, PileKind, PileRef
from src.solitaire.table_layout import UP_OFFSET, TableLayout, foundation_labels


@dataclass
class DragState:
    src: PileRef
    index: int
    cards: list[Card]
    grab: QPointF  # posición del cursor relativa a la esquina de la primera carta
    start: QPointF
    pos: QPointF
    active: bool = False
    targets: list[PileRef] = field(default_factory=list)  # destinos válidos (se calculan al levantar)

    def is_dragged(self, ref: PileRef, index: int) -> bool:
        return self.active and self.src == ref and index >= self.index

    def card_rects(self, layout: TableLayout) -> list[QRectF]:
        """Cartas levantadas: un poco más grandes, escaladas alrededor del cursor."""
        s = CARD_LOOK.lift_scale
        corner = self.pos - self.grab * s
        size = QSizeF(layout.card_w * s, layout.card_h * s)
        return [QRectF(corner + QPointF(0, i * layout.card_h * UP_OFFSET * s), size) for i in range(len(self.cards))]

    def bounds(self, layout: TableLayout) -> QRectF:
        """Lo que ocupan las cartas levantadas, con su sombra."""
        rects = self.card_rects(layout)
        margin = layout.card_w * 0.32
        return rects[0].united(rects[-1]).adjusted(-margin, -margin, margin, margin)


def drop_targets(game: KlondikeGame, src: PileRef, index: int) -> list[PileRef]:
    """Destinos válidos de lo que se levantó: se marcan con un resplandor mientras dura el arrastre."""
    refs = [PileRef(PileKind.FOUNDATION, i) for i in range(FOUNDATIONS)]
    refs += [PileRef(PileKind.TABLEAU, col) for col in range(TABLEAU_COLUMNS)]
    return [ref for ref in refs if game.can_move(src, index, ref)]


def auto_foundation(game: KlondikeGame, ref: PileRef, index: int) -> PileRef | None:
    """Fundación del doble clic: un As va a la que muestra su palo (cualquiera vacía es válida)."""
    target = game.foundation_target(ref, index)
    card = game.pile(ref)[index]
    if target is not None and card.rank == 1:
        for i, label in enumerate(foundation_labels(game)):
            preferred = PileRef(PileKind.FOUNDATION, i)
            if label is card.suit and game.can_move(ref, index, preferred):
                return preferred
    return target


def card_rect(layout: TableLayout, game: KlondikeGame, ref: PileRef, index: int) -> QRectF:
    if ref.kind is PileKind.TABLEAU:
        return layout.column_rects(game, ref.index)[index]
    if ref.kind is PileKind.WASTE:
        return dict(layout.waste_rects(game))[index]
    return layout.slot_rect(ref)
