"""Estado y movimientos de una partida de Klondike. Lógica pura, sin Qt."""
import random
from dataclasses import dataclass, field
from enum import Enum

from src.solitaire.cards import KING, Card, new_deck
from src.solitaire import snapshot
from src.solitaire.rules import can_place_on_foundation, can_place_on_tableau, is_valid_sequence

TABLEAU_COLUMNS = 7
FOUNDATIONS = 4


class PileKind(Enum):
    STOCK = "mazo"
    WASTE = "descarte"
    FOUNDATION = "fundación"
    TABLEAU = "columna"


@dataclass(frozen=True)
class PileRef:
    kind: PileKind
    index: int = 0


@dataclass
class Column:
    cards: list[Card] = field(default_factory=list)
    hidden: int = 0  # las primeras `hidden` cartas están boca abajo

    def is_face_up(self, i: int) -> bool:
        return i >= self.hidden


class KlondikeGame:
    def __init__(self, draw_count: int = 1, rng: random.Random | None = None):
        if draw_count not in (1, 3):
            raise ValueError("draw_count debe ser 1 o 3")
        self.draw_count = draw_count
        deck = new_deck()
        (rng or random.Random()).shuffle(deck)
        self.tableau = [Column() for _ in range(TABLEAU_COLUMNS)]
        for col in range(TABLEAU_COLUMNS):  # columna i: i+1 cartas, sólo la última boca arriba
            self.tableau[col].cards = [deck.pop() for _ in range(col + 1)]
            self.tableau[col].hidden = col
        self.stock: list[Card] = deck  # tope = último elemento; 24 cartas
        self.waste: list[Card] = []
        self.foundations: list[list[Card]] = [[] for _ in range(FOUNDATIONS)]
        self.actions = 0  # robos + movimientos hechos (para saber si hay partida en curso)
        self._history: list[snapshot.GameState] = []  # estados previos a cada acción

    # --- consultas ------------------------------------------------------------
    def pile(self, ref: PileRef) -> list[Card]:
        if ref.kind is PileKind.STOCK:
            return self.stock
        if ref.kind is PileKind.WASTE:
            return self.waste
        if ref.kind is PileKind.FOUNDATION:
            return self.foundations[ref.index]
        return self.tableau[ref.index].cards

    @property
    def is_won(self) -> bool:
        return all(len(f) == KING for f in self.foundations)

    def movable_cards(self, src: PileRef, index: int) -> list[Card]:
        """Cartas que se levantan al tomar `index` de `src`; vacío si no se puede."""
        pile = self.pile(src)
        if not 0 <= index < len(pile) or src.kind is PileKind.STOCK:
            return []
        if src.kind in (PileKind.WASTE, PileKind.FOUNDATION):  # sólo la de arriba
            return [pile[-1]] if index == len(pile) - 1 else []
        column = self.tableau[src.index]
        if not column.is_face_up(index):
            return []
        cards = pile[index:]
        return cards if is_valid_sequence(cards) else []

    def can_move(self, src: PileRef, index: int, dst: PileRef) -> bool:
        cards = self.movable_cards(src, index)
        if not cards or src == dst:
            return False
        if dst.kind is PileKind.FOUNDATION:
            return len(cards) == 1 and can_place_on_foundation(cards[0], self.foundations[dst.index])
        if dst.kind is PileKind.TABLEAU:
            target = self.tableau[dst.index].cards
            return can_place_on_tableau(cards[0], target[-1] if target else None)
        return False

    def foundation_target(self, src: PileRef, index: int) -> PileRef | None:
        """Fundación a la que puede ir la carta (doble clic), o None."""
        for i in range(FOUNDATIONS):
            ref = PileRef(PileKind.FOUNDATION, i)
            if self.can_move(src, index, ref):
                return ref
        return None

    # --- acciones -------------------------------------------------------------
    def move(self, src: PileRef, index: int, dst: PileRef) -> bool:
        if not self.can_move(src, index, dst):
            return False
        self._history.append(snapshot.take(self))
        source = self.pile(src)
        cards = source[index:]
        del source[index:]
        self.pile(dst).extend(cards)
        if src.kind is PileKind.TABLEAU:
            self._flip_exposed(self.tableau[src.index])
        self.actions += 1
        return True

    def draw(self) -> bool:
        """Roba `draw_count` cartas (o las que queden). Con el mazo vacío, recicla el descarte."""
        if not self.stock and not self.waste:
            return False
        self._history.append(snapshot.take(self))
        if not self.stock:
            self.stock = self.waste[::-1]  # el descarte vuelve al mazo boca abajo, en orden original
            self.waste = []
        else:
            for _ in range(min(self.draw_count, len(self.stock))):
                self.waste.append(self.stock.pop())
        self.actions += 1
        return True

    # --- deshacer ---------------------------------------------------------------
    @property
    def can_undo(self) -> bool:
        return bool(self._history)

    def undo(self) -> bool:
        """Vuelve al estado anterior a la última acción (movimiento, robo o reciclado)."""
        if not self._history:
            return False
        snapshot.restore(self, self._history.pop())
        return True

    @staticmethod
    def _flip_exposed(column: Column) -> None:
        if column.cards and column.hidden >= len(column.cards):
            column.hidden = len(column.cards) - 1
