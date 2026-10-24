"""Cartas francesas y mazo de 52. Sin Qt."""
from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

    @property
    def is_red(self) -> bool:
        return self in (Suit.HEARTS, Suit.DIAMONDS)


RANK_LABELS = {1: "A", 11: "J", 12: "Q", 13: "K"}
ACE, KING = 1, 13


@dataclass(frozen=True)
class Card:
    rank: int  # 1 (As) a 13 (Rey)
    suit: Suit

    @property
    def is_red(self) -> bool:
        return self.suit.is_red

    @property
    def label(self) -> str:
        return RANK_LABELS.get(self.rank, str(self.rank))

    def __str__(self) -> str:
        return f"{self.label}{self.suit.value}"


def new_deck() -> list[Card]:
    return [Card(rank, suit) for suit in Suit for rank in range(ACE, KING + 1)]
