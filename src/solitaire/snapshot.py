"""Instantáneas inmutables del estado de una partida, para deshacer. Sin Qt."""
from dataclasses import dataclass

from src.solitaire.cards import Card


@dataclass(frozen=True)
class GameState:
    tableau: tuple[tuple[tuple[Card, ...], int], ...]  # (cartas, cantidad boca abajo) por columna
    stock: tuple[Card, ...]
    waste: tuple[Card, ...]
    foundations: tuple[tuple[Card, ...], ...]
    actions: int


def take(game) -> GameState:
    return GameState(
        tableau=tuple((tuple(col.cards), col.hidden) for col in game.tableau),
        stock=tuple(game.stock),
        waste=tuple(game.waste),
        foundations=tuple(tuple(f) for f in game.foundations),
        actions=game.actions,
    )


def restore(game, state: GameState) -> None:
    for column, (cards, hidden) in zip(game.tableau, state.tableau):
        column.cards, column.hidden = list(cards), hidden
    game.stock = list(state.stock)
    game.waste = list(state.waste)
    game.foundations = [list(f) for f in state.foundations]
    game.actions = state.actions
