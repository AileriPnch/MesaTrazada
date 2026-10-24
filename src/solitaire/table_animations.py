"""Qué animar después de cada acción: se compara dónde estaba y dónde quedó cada carta visible. Si cambió de
lugar, vuela; si cambió de cara, gira (la que queda destapada, la que sale del mazo); el descarte se
reacomoda solo. El reparto tiene su propia coreografía."""
from PyQt6.QtCore import QRectF

from src.solitaire.cards import Card
from src.solitaire.klondike import FOUNDATIONS, TABLEAU_COLUMNS, KlondikeGame, PileKind, PileRef
from src.solitaire.table_layout import TableLayout
from src.solitaire.table_motion import TableMotion

FLIGHT_MS = 200  # doble clic a la fundación, robar del mazo
SETTLE_MS = 110  # la carta soltada se acomoda en su lugar
RETURN_MS = 160  # suelta inválida: vuelve a su origen
FLIP_MS = 200  # giro de la carta que queda destapada
FLIP_DELAY_MS = 60
STAGGER_MS = 45  # robo de a 3: una carta tras otra
DEAL_STEP_MS = 22  # reparto: una carta cada tanto...
DEAL_FLIGHT_MS = 210  # ... y cada una tarda esto en llegar

Snapshot = dict[Card, tuple[QRectF, bool]]


def visible_cards(game: KlondikeGame, layout: TableLayout) -> Snapshot:
    """Cada carta a la vista: (rectángulo, boca arriba). Del mazo sólo cuenta la de arriba."""
    out: Snapshot = {}
    if game.stock:
        out[game.stock[-1]] = (layout.slot_rect(PileRef(PileKind.STOCK)), False)
    for index, rect in layout.waste_rects(game):
        out[game.waste[index]] = (rect, True)
    for i in range(FOUNDATIONS):
        if game.foundations[i]:
            out[game.foundations[i][-1]] = (layout.slot_rect(PileRef(PileKind.FOUNDATION, i)), True)
    for col in range(TABLEAU_COLUMNS):
        column = game.tableau[col]
        for index, rect in enumerate(layout.column_rects(game, col)):
            out[column.cards[index]] = (rect, column.is_face_up(index))
    return out


def _same(a: QRectF, b: QRectF) -> bool:
    return abs(a.x() - b.x()) < 0.5 and abs(a.y() - b.y()) < 0.5 and abs(a.width() - b.width()) < 0.5


def animate_change(motion: TableMotion, game: KlondikeGame, layout: TableLayout, before: Snapshot,
                   duration: float, overrides: Snapshot | None = None) -> None:
    """Anima de `before` (o de `overrides`, p. ej. las cartas levantadas) al estado actual de la partida."""
    after = visible_cards(game, layout)
    stock = layout.slot_rect(PileRef(PileKind.STOCK))
    from_stock = 0
    for card, (rect, face) in after.items():
        if overrides and card in overrides:
            start, start_face = overrides[card]
        elif card in before:
            start, start_face = before[card]
        elif card in game.waste:  # salió del mazo (de a 3, sólo la de arriba se veía)
            start, start_face = stock, False
        else:
            continue
        delay = 0.0
        if card in game.waste and (card not in before or not before[card][1]):  # recién robada
            delay = from_stock * STAGGER_MS
            from_stock += 1
        if _same(start, rect) and start_face == face:
            continue
        if _same(start, rect):  # misma posición, otra cara: la carta que quedó destapada gira
            motion.add(card, start, rect, FLIP_MS, FLIP_DELAY_MS, start_face, face)
        else:
            motion.add(card, start, rect, duration, delay, start_face, face)
    for card, (rect, face) in before.items():  # reciclado: el descarte vuelve al mazo boca abajo
        if card not in after and card in game.stock:
            motion.add(card, rect, stock, duration, 0.0, face, False)


def animate_deal(motion: TableMotion, game: KlondikeGame, layout: TableLayout) -> None:
    """Reparto: las 28 cartas salen del mazo de a una, fila por fila; las de arriba giran al llegar."""
    stock = layout.slot_rect(PileRef(PileKind.STOCK))
    rects = [layout.column_rects(game, col) for col in range(TABLEAU_COLUMNS)]
    k = 0
    for row in range(TABLEAU_COLUMNS):
        for col in range(row, TABLEAU_COLUMNS):
            column = game.tableau[col]
            if row < len(column.cards):
                motion.add(column.cards[row], stock, rects[col][row], DEAL_FLIGHT_MS, k * DEAL_STEP_MS,
                           False, column.is_face_up(row))
                k += 1
