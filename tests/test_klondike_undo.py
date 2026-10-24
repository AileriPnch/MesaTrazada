import random

import pytest
from PyQt6.QtCore import QPointF

from src.solitaire import snapshot
from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import KlondikeGame, PileKind, PileRef
from src.solitaire.table_layout import TableLayout
from tests.test_klondike import WASTE, empty_game, fnd, tab

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS


def test_no_history_after_deal():
    game = KlondikeGame(1, random.Random(0))
    assert not game.can_undo and not game.undo()


def test_undo_move_restores_auto_flipped_card_face_down():
    game = empty_game()
    game.tableau[0].cards = [Card(2, C), Card(9, S), Card(8, H)]
    game.tableau[0].hidden = 2
    game.tableau[1].cards = [Card(9, C)]
    before = snapshot.take(game)
    assert game.move(tab(0), 2, tab(1)) and game.tableau[0].hidden == 1  # se volteó el 9♠
    assert game.undo()
    assert snapshot.take(game) == before and game.tableau[0].hidden == 2  # 9♠ boca abajo otra vez


def test_undo_draw_and_recycle():
    game = KlondikeGame(3, random.Random(4))
    start = snapshot.take(game)
    game.draw()
    after_one = snapshot.take(game)
    assert game.undo() and snapshot.take(game) == start
    game.draw()
    assert snapshot.take(game) == after_one
    while game.stock:
        game.draw()
    exhausted = snapshot.take(game)
    game.draw()  # reciclado
    assert game.stock and not game.waste
    assert game.undo() and snapshot.take(game) == exhausted


def test_undo_move_to_foundation():
    game = empty_game()
    game.waste = [Card(1, D)]
    target = game.foundation_target(WASTE, 0)  # lo que hace el doble clic
    assert game.move(WASTE, 0, target)
    assert game.undo()
    assert game.waste == [Card(1, D)] and game.foundations[0] == []


def test_undo_is_unlimited_back_to_the_deal():
    game = KlondikeGame(1, random.Random(9))
    dealt = snapshot.take(game)
    rng = random.Random(1)
    for _ in range(200):  # acciones al azar válidas: robos y movimientos
        refs = [PileRef(PileKind.WASTE)] + [tab(i) for i in range(7)] + [fnd(i) for i in range(4)]
        moves = [(s, i, d) for s in refs for i in range(len(game.pile(s))) for d in refs if game.can_move(s, i, d)]
        if moves and rng.random() < 0.5:
            game.move(*rng.choice(moves))
        else:
            game.draw()
    undone = 0
    while game.undo():
        undone += 1
    assert undone == 200 and snapshot.take(game) == dealt and game.actions == 0


@pytest.mark.parametrize("draw_count", [1, 3])
def test_waste_fan_shows_last_three_and_restacks_after_playing_top(draw_count):
    game = empty_game(draw_count)
    game.waste = [Card(5, S), Card(8, D), Card(4, C), Card(13, H)]
    layout = TableLayout.fit(1000, 700)
    shown = layout.waste_rects(game)
    assert [game.waste[i] for i, _ in shown] == [Card(8, D), Card(4, C), Card(13, H)]
    assert layout.hit_test(game, shown[-1][1].center()) == (WASTE, 3)  # sólo la de arriba
    assert layout.hit_test(game, QPointF(shown[0][1].left() + 3, shown[0][1].center().y())) != (WASTE, 1)
    assert game.move(WASTE, 3, tab(0))  # el Rey va a la columna vacía
    shown = layout.waste_rects(game)
    assert [game.waste[i] for i, _ in shown] == [Card(5, S), Card(8, D), Card(4, C)]
    assert layout.hit_test(game, shown[-1][1].center()) == (WASTE, 2)  # la anterior quedó arriba
