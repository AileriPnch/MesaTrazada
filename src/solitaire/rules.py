"""Reglas de apilado del Klondike como funciones puras."""
from src.solitaire.cards import ACE, KING, Card


def can_place_on_tableau(card: Card, top: Card | None) -> bool:
    """Columna vacía: sólo Rey. Si no, color alternado y un valor menos."""
    if top is None:
        return card.rank == KING
    return card.is_red != top.is_red and card.rank == top.rank - 1


def can_place_on_foundation(card: Card, pile: list[Card]) -> bool:
    """Fundación vacía: sólo As. Si no, mismo palo y un valor más."""
    if not pile:
        return card.rank == ACE
    top = pile[-1]
    return card.suit == top.suit and card.rank == top.rank + 1


def is_valid_sequence(cards: list[Card]) -> bool:
    """Una secuencia movible: descendente y alternando color."""
    return all(can_place_on_tableau(lower, upper) for upper, lower in zip(cards, cards[1:]))
