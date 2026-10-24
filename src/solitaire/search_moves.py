"""Sucesores de un estado del detector de traba (ver `search_state`). Puro, sin Qt.

Robar y reciclar no generan estados propios: desde un estado se puede jugar toda carta que el mazo deje
arriba del descarte en algún momento (exacto según el modo de robo, no una aproximación).
"""
from src.solitaire.cards import KING
from src.solitaire.search_state import RANK, RED, SUIT, Context, canon, pointer, positions

SLOT = [RANK[i] * 2 + RED[i] for i in range(52)]  # clave de "lugar donde puede ir" la carta
PARENT = [(RANK[i] - 1) * 2 + (not RED[i]) for i in range(52)]  # clave de lo que acepta encima
KING_SLOTS = (KING * 2, KING * 2 + 1)
CHILDREN = [tuple(c for c in range(52) if RANK[c] == RANK[i] - 1 and RED[c] != RED[i]) for i in range(52)]


def _with(found: tuple, suit: int, rank: int) -> tuple:
    return found[:suit] + (rank,) + found[suit + 1:]


def _slots(cols: tuple, empty: int | None) -> dict[int, list[int]]:
    """Columnas que aceptan cada clase de carta (valor + color). Vacía: sólo Rey, y sólo la primera."""
    slots = {}
    for t, dst in enumerate(cols):
        if dst:
            slots.setdefault(PARENT[dst[-1]], []).append(t)
    if empty is not None:
        for key in KING_SLOTS:
            slots[key] = slots.get(key, []) + [empty]
    return slots


def _change(cols: tuple, ctx: Context, i: int, run: tuple, j: int | None = None, other: tuple = ()) -> tuple:
    """Columnas con la i reemplazada por `run` (y la j por `other`), en forma canónica."""
    new = list(cols)
    new[i] = run
    if j is not None:
        new[j] = other
    if i in ctx.free or j in ctx.free:
        return canon(new, ctx.free)
    return tuple(new)


def _useful(card: int, found: tuple, ctx: Context, memo: dict) -> bool:
    """¿Devolver `card` (tope de su fundación) puede servir para algo? Sólo sirve como base para una carta
    de un valor menos y otro color (CHILDREN) o para poder devolver la de abajo de su mismo palo.
    Falso si todas esas cartas están boca abajo o en fundación sin poder servir a su vez: entonces nada
    de afuera puede terminar encima y la devolución es inútil (podarla no oculta ninguna salida)."""
    if card not in memo:
        memo[card] = RANK[card] > 1 and (any(
            x not in ctx.hidden_cards and (found[SUIT[x]] < RANK[x] or _useful(x, found, ctx, memo))
            for x in CHILDREN[card]) or _useful(card - 1, found, ctx, memo))
    return memo[card]


def successors(node: tuple, ctx: Context) -> list[tuple] | None:
    """Estados a una jugada (robar incluido) de `node`, o None si alguna jugada es un avance."""
    cols, found, cycle, ptr = node
    hidden = ctx.hidden
    room = ctx.base_total - sum(found)  # cartas que pueden subir sin superar el total inicial
    empty = next((i for i in ctx.free if not cols[i]), None)  # todas las vacías son equivalentes
    slots = _slots(cols, empty)
    out = []
    for i, run in enumerate(cols):
        if not run:
            continue
        top = run[-1]
        if found[SUIT[top]] == RANK[top] - 1:  # a la fundación
            if room == 0 or (len(run) == 1 and hidden[i]):
                return None
            out.append((_change(cols, ctx, i, run[:-1]), _with(found, SUIT[top], RANK[top]), cycle, ptr))
        start = len(run) - 1  # comienzo de la secuencia movible
        while start and RANK[run[start - 1]] == RANK[run[start]] + 1 and RED[run[start - 1]] != RED[run[start]]:
            start -= 1
        for k in range(start, len(run)):
            for t in slots.get(SLOT[run[k]], ()):
                if t == i:
                    continue
                if k == 0:
                    if hidden[i]:
                        return None  # vacía la parte boca arriba: destapa una carta
                    if not cols[t]:
                        continue  # columna entera con Rey de base a otra vacía: el mismo estado
                out.append((_change(cols, ctx, t, cols[t] + run[k:], i, run[:k]), found, cycle, ptr))
    memo = {}
    for suit, rank in enumerate(found):  # devoluciones desde la fundación (sólo las que pueden servir)
        card = suit * 13 + rank - 1
        if rank and _useful(card, found, ctx, memo):
            for t in slots.get(SLOT[card], ()):
                out.append((_change(cols, ctx, t, cols[t] + (card,)), _with(found, suit, rank - 1), cycle, ptr))
    for q in positions(len(cycle), ptr, ctx.draw_count):  # cartas que el mazo deja arriba del descarte
        card = cycle[q - 1]
        rest, after = cycle[:q - 1] + cycle[q:], pointer(q - 1, len(cycle) - 1, ctx.draw_count)
        if found[SUIT[card]] == RANK[card] - 1:
            if room == 0:
                return None
            out.append((cols, _with(found, SUIT[card], RANK[card]), rest, after))
        for t in slots.get(SLOT[card], ()):
            out.append((_change(cols, ctx, t, cols[t] + (card,)), found, rest, after))
    return out
