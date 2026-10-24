import random

import pytest

from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import Column, KlondikeGame, PileKind, PileRef

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS
WASTE = PileRef(PileKind.WASTE)


def tab(i: int) -> PileRef:
    return PileRef(PileKind.TABLEAU, i)


def fnd(i: int) -> PileRef:
    return PileRef(PileKind.FOUNDATION, i)


def empty_game(draw_count: int = 1) -> KlondikeGame:
    game = KlondikeGame(draw_count, random.Random(0))
    game.tableau = [Column() for _ in range(7)]
    game.stock, game.waste = [], []
    game.foundations = [[] for _ in range(4)]
    return game


# --- reparto --------------------------------------------------------------------
def test_deal_layout():
    game = KlondikeGame(1, random.Random(42))
    all_cards = game.stock + [c for col in game.tableau for c in col.cards]
    assert len(all_cards) == 52 and len(set(all_cards)) == 52
    assert sum(len(col.cards) for col in game.tableau) == 28 and len(game.stock) == 24
    for i, col in enumerate(game.tableau):
        assert len(col.cards) == i + 1 and col.hidden == i  # sólo la última boca arriba
    assert game.waste == [] and all(f == [] for f in game.foundations)


def test_deal_is_shuffled_and_draw_count_validated():
    assert KlondikeGame(1, random.Random(1)).stock != KlondikeGame(1, random.Random(2)).stock
    with pytest.raises(ValueError):
        KlondikeGame(2)


# --- columnas -------------------------------------------------------------------
def test_tableau_alternating_color_descending():
    game = empty_game()
    game.tableau[0].cards = [Card(8, S)]
    game.waste = [Card(7, H)]
    assert game.can_move(WASTE, 0, tab(0))
    game.waste = [Card(7, C)]  # mismo color
    assert not game.can_move(WASTE, 0, tab(0))
    game.waste = [Card(6, H)]  # no es el siguiente
    assert not game.can_move(WASTE, 0, tab(0))


def test_only_king_or_king_sequence_to_empty_column():
    game = empty_game()
    game.waste = [Card(12, H)]
    assert not game.can_move(WASTE, 0, tab(0))
    game.waste = [Card(13, H)]
    assert game.can_move(WASTE, 0, tab(0))
    game.tableau[1].cards = [Card(5, C), Card(13, S), Card(12, H), Card(11, C)]
    game.tableau[1].hidden = 1
    assert game.move(tab(1), 1, tab(2))  # secuencia que empieza con Rey
    assert [str(c) for c in game.tableau[2].cards] == ["K♠", "Q♥", "J♣"]


def test_multi_card_sequence_moves_and_invalid_sequence_rejected():
    game = empty_game()
    game.tableau[0].cards = [Card(9, D), Card(8, S), Card(7, H)]
    game.tableau[1].cards = [Card(10, C)]
    assert game.movable_cards(tab(0), 0) == game.tableau[0].cards
    assert game.move(tab(0), 0, tab(1))
    assert len(game.tableau[1].cards) == 4 and game.tableau[0].cards == []
    game.tableau[2].cards = [Card(9, D), Card(8, D)]  # no alterna color
    assert game.movable_cards(tab(2), 0) == []


def test_face_down_cards_cannot_be_moved():
    game = empty_game()
    game.tableau[0].cards = [Card(13, S), Card(4, H)]
    game.tableau[0].hidden = 1
    assert game.movable_cards(tab(0), 0) == []


# --- fundaciones ----------------------------------------------------------------
def test_foundation_ace_then_same_suit_ascending():
    game = empty_game()
    game.waste = [Card(2, H)]
    assert not game.can_move(WASTE, 0, fnd(0))  # vacía: sólo As
    game.foundations[0] = [Card(1, H)]
    assert game.can_move(WASTE, 0, fnd(0))
    game.waste = [Card(2, D)]  # otro palo
    assert not game.can_move(WASTE, 0, fnd(0))


def test_only_single_card_to_foundation_and_double_click_target():
    game = empty_game()
    game.foundations[2] = [Card(1, S)]
    game.tableau[0].cards = [Card(3, H), Card(2, S)]
    assert game.foundation_target(tab(0), 1) == fnd(2)
    assert game.foundation_target(tab(0), 0) is None  # dos cartas
    game.waste = [Card(1, D)]
    assert game.foundation_target(WASTE, 0) == fnd(0)  # primera fundación vacía


def test_card_can_return_from_foundation_to_tableau():
    game = empty_game()
    game.foundations[0] = [Card(1, H), Card(2, H), Card(3, H)]
    game.tableau[0].cards = [Card(4, C)]
    assert not game.can_move(fnd(0), 1, tab(0))  # sólo la de arriba
    assert game.move(fnd(0), 2, tab(0))
    assert game.tableau[0].cards[-1] == Card(3, H) and len(game.foundations[0]) == 2


# --- volteo automático ------------------------------------------------------------
def test_exposed_face_down_card_flips():
    game = empty_game()
    game.tableau[0].cards = [Card(2, C), Card(9, S), Card(8, H)]
    game.tableau[0].hidden = 2
    game.tableau[1].cards = [Card(9, C)]
    assert game.move(tab(0), 2, tab(1))
    assert game.tableau[0].hidden == 1 and game.tableau[0].is_face_up(1)


# --- robo y reciclado -------------------------------------------------------------
def test_draw_one_and_three():
    one = KlondikeGame(1, random.Random(3))
    top = one.stock[-1]
    one.draw()
    assert one.waste == [top] and len(one.stock) == 23
    three = KlondikeGame(3, random.Random(3))
    expected = three.stock[-3:][::-1]
    three.draw()
    assert three.waste == expected and len(three.stock) == 21


def test_draw_three_with_fewer_left_takes_what_remains():
    game = empty_game(3)
    game.stock = [Card(5, S), Card(6, S)]
    game.draw()
    assert game.waste == [Card(6, S), Card(5, S)] and game.stock == []


def test_draw_three_only_top_of_waste_is_playable():
    game = empty_game(3)
    game.waste = [Card(13, S), Card(13, H), Card(1, C)]
    assert game.movable_cards(WASTE, 2) == [Card(1, C)]
    assert game.movable_cards(WASTE, 1) == [] and not game.can_move(WASTE, 1, tab(0))


@pytest.mark.parametrize("draw_count", [1, 3])
def test_recycle_is_unlimited_and_preserves_order(draw_count):
    game = KlondikeGame(draw_count, random.Random(5))
    original = list(game.stock)
    for _ in range(3):  # varias pasadas completas
        while game.stock:
            game.draw()
        assert len(game.waste) == 24 and game.stock == []
        assert game.draw()  # recicla
        assert game.stock == original and game.waste == []


def test_draw_with_everything_empty_does_nothing():
    game = empty_game()
    assert not game.draw()


# --- victoria ---------------------------------------------------------------------
def test_victory_detection():
    game = empty_game()
    game.foundations = [[Card(r, s) for r in range(1, 14)] for s in Suit]
    game.foundations[3].pop()
    game.waste = [Card(13, C)]
    assert not game.is_won
    assert game.move(WASTE, 0, fnd(3))
    assert game.is_won
