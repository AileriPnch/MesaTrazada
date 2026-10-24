"""Detección de partida trabada ("No quedan movimientos") por búsqueda acotada. Puro: no muta el juego.

Avance = llegar a un estado con más cartas en fundación que ahora o con una carta boca abajo destapada.
Se recorren en anchura TODOS los estados alcanzables sin avance (movimientos entre columnas, del mazo,
devoluciones desde la fundación y el ciclo del mazo según el modo de robo; ver `search_moves`), sin
repetir estados. Principio conservador: sólo es traba (STUCK) si se agotaron los estados sin encontrar
avance; si se corta por límite de nodos o de tiempo el resultado es LIMIT y NO se avisa.
"""
import math
import time
from collections import deque
from enum import Enum

from src.solitaire.cards import Card
from src.solitaire.search_moves import successors
from src.solitaire.search_state import encode, positions

MAX_NODES = 20_000  # estados distintos; el peor caso real medido usó ~9 300
MAX_SECONDS = 0.5  # cálculo total, sumando todas las porciones (red de seguridad en PCs lentas)


class Outcome(Enum):
    PROGRESS = "hay avance"
    STUCK = "traba probada"
    LIMIT = "cortada por límite"


class StuckSearch:
    """Búsqueda reanudable: `advance(porción)` trabaja como mucho esos segundos y se puede retomar, para
    repartirla entre vueltas del bucle de eventos sin trabar la UI. Opera sobre una copia codificada."""

    def __init__(self, game, max_nodes: int | None = None, max_seconds: float | None = None):
        self.max_nodes = MAX_NODES if max_nodes is None else max_nodes
        self.max_seconds = MAX_SECONDS if max_seconds is None else max_seconds
        self.elapsed = 0.0  # segundos de cálculo acumulados
        self.outcome: Outcome | None = Outcome.PROGRESS if game.is_won else None  # ganada: no es traba
        self._ctx, root = encode(game)
        self._visited = {root}
        self._queue = deque([root])
        self._nodes = 1

    @property
    def nodes(self) -> int:
        """Estados distintos visitados."""
        return self._nodes if self.outcome is not None else len(self._visited)

    def run(self) -> Outcome:
        return self.advance(None)

    def advance(self, slice_seconds: float | None) -> Outcome | None:
        """Sigue la búsqueda (al menos un estado por llamada). Devuelve el resultado, o None si se
        terminó la porción antes."""
        if self.outcome is not None:
            return self.outcome
        start = time.perf_counter()
        stop = start + min(self.max_seconds - self.elapsed, math.inf if slice_seconds is None else slice_seconds)
        outcome = self._expand()
        while outcome is None and time.perf_counter() < stop:
            outcome = self._expand()
        self.elapsed += time.perf_counter() - start
        if outcome is None and self.elapsed >= self.max_seconds:
            outcome = Outcome.LIMIT
        if outcome is not None:
            self.outcome, self._nodes = outcome, len(self._visited)
            self._visited, self._queue = set(), deque()  # libera memoria
        return outcome

    def _expand(self) -> Outcome | None:
        children = successors(self._queue.popleft(), self._ctx)
        if children is None:
            return Outcome.PROGRESS
        visited = self._visited
        for child in children:
            if child not in visited:
                if len(visited) >= self.max_nodes:
                    return Outcome.LIMIT
                visited.add(child)
                self._queue.append(child)
        return None if self._queue else Outcome.STUCK


def is_stuck(game, max_nodes: int | None = None, max_seconds: float | None = None) -> bool:
    return StuckSearch(game, max_nodes, max_seconds).run() is Outcome.STUCK


def accessible_stock_cards(game) -> list[Card]:
    """Cartas del mazo/descarte que quedan arriba del descarte en algún momento (robando y reciclando)."""
    cycle = game.waste + game.stock[::-1]
    _, (_, _, _, ptr) = encode(game)
    return [cycle[q - 1] for q in positions(len(cycle), ptr, game.draw_count)]


def board_key(game) -> tuple:
    """Columnas + fundaciones. Robar/reciclar no lo cambia: tras "Seguir mirando" no se vuelve a
    avisar por recorrer el mazo, sí después de un movimiento o de deshacer uno."""
    return (tuple((tuple(c.cards), c.hidden) for c in game.tableau), tuple(tuple(f) for f in game.foundations))
