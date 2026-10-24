"""Estado compacto de la partida para el detector de traba. Puro, sin Qt.

Estado = (columnas, fundaciones, ciclo, puntero), todo inmutable y hasheable:
  - columnas: la parte boca arriba de cada columna, como tuplas de enteros (carta = palo*13 + valor-1).
    Lo boca abajo no cambia dentro de la búsqueda (destapar ya es avance): va aparte, en `Context`.
    Las columnas sin cartas boca abajo son intercambiables y se guardan ordenadas (estado canónico).
  - fundaciones: valor del tope por palo (0 = vacía).
  - ciclo: descarte + mazo en orden de robo (`waste + stock[::-1]`); robar no lo cambia.
  - puntero: cartas del ciclo que están en el descarte, o MAIN si está en el ciclo principal
    (0, d, 2d, …, n), cuyas posiciones son todas alcanzables entre sí robando y reciclando.
"""
from dataclasses import dataclass
from functools import lru_cache

from src.solitaire.cards import Card, Suit

SUIT_INDEX = {suit: i for i, suit in enumerate(Suit)}
RANK = [i % 13 + 1 for i in range(52)]
SUIT = [i // 13 for i in range(52)]
RED = [list(Suit)[i // 13].is_red for i in range(52)]
MAIN = -1


@dataclass(frozen=True)
class Context:
    draw_count: int
    hidden: tuple[int, ...]  # cartas boca abajo por columna (fijas durante la búsqueda)
    free: tuple[int, ...]  # columnas sin cartas boca abajo: intercambiables
    base_total: int  # cartas en fundación al empezar; superarlo es avance
    hidden_cards: frozenset[int]  # boca abajo: dentro de la búsqueda nunca se mueven


def card_id(card: Card) -> int:
    return SUIT_INDEX[card.suit] * 13 + card.rank - 1


def pointer(position: int, cycle_len: int, draw_count: int) -> int:
    """Puntero canónico: MAIN si `position` (cartas en el descarte) está en el ciclo principal."""
    return MAIN if position % draw_count == 0 or position == cycle_len else position


@lru_cache(maxsize=None)
def positions(cycle_len: int, ptr: int, draw_count: int) -> tuple[int, ...]:
    """Largos del descarte alcanzables robando: el tope de cada uno es `ciclo[q-1]`.
    Primero lo que resta de esta pasada (si el puntero está fuera del ciclo principal), después el ciclo."""
    if not cycle_len:
        return ()
    rest = list(range(ptr, cycle_len, draw_count)) + [cycle_len] if ptr != MAIN else []
    main = list(range(draw_count, cycle_len, draw_count)) + [cycle_len]
    return tuple(dict.fromkeys(q for q in rest + main if q > 0))


def encode(game) -> tuple[Context, tuple]:
    """Contexto fijo y estado inicial de la búsqueda a partir de la partida (no la modifica)."""
    hidden = tuple(min(col.hidden, len(col.cards)) for col in game.tableau)
    free = tuple(i for i, h in enumerate(hidden) if h == 0)
    found = [0] * 4
    for pile in game.foundations:
        if pile:
            found[SUIT_INDEX[pile[-1].suit]] = pile[-1].rank
    cycle = tuple(card_id(c) for c in game.waste + game.stock[::-1])
    cols = [tuple(card_id(c) for c in col.cards[h:]) for col, h in zip(game.tableau, hidden)]
    buried = frozenset(card_id(c) for col, h in zip(game.tableau, hidden) for c in col.cards[:h])
    ctx = Context(game.draw_count, hidden, free, sum(found), buried)
    return ctx, (canon(cols, free), tuple(found), cycle, pointer(len(game.waste), len(cycle), game.draw_count))


def canon(cols: list, free: tuple[int, ...]) -> tuple:
    """Ordena las columnas intercambiables: posiciones simétricas quedan como un solo estado."""
    for i, run in zip(free, sorted(cols[i] for i in free)):
        cols[i] = run
    return tuple(cols)
