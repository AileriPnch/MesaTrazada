"""Límites y porciones de la búsqueda de traba: cortar por límite nunca es "trabada"."""
import random

from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import KlondikeGame
from src.solitaire.stuck_detector import Outcome, StuckSearch, is_stuck
from tests.test_stuck_detector import dead_game, huge_dead_game

D, C = Suit.DIAMONDS, Suit.CLUBS


def test_search_cut_by_node_limit_is_not_reported_as_stuck():
    game = huge_dead_game()
    search = StuckSearch(game, max_nodes=500)
    assert search.run() is Outcome.LIMIT and search.nodes == 500
    assert not is_stuck(game, max_nodes=500)
    assert is_stuck(dead_game(), max_nodes=2)  # alcanza justo para agotar: sí es traba


def test_search_cut_by_time_limit_is_not_reported_as_stuck():
    game = huge_dead_game(3)
    search = StuckSearch(game, max_seconds=0.02)
    assert search.run() is Outcome.LIMIT and 0.02 <= search.elapsed < 0.1


def test_search_resumes_in_slices_with_the_same_result():
    game = dead_game()
    game.foundations[0] = [Card(1, D), Card(2, D)]
    game.tableau[3].cards = [Card(3, C)]
    search, calls = StuckSearch(game), 1
    while search.advance(0) is None:  # porción nula: un estado por llamada
        calls += 1
    assert search.outcome is Outcome.STUCK and search.nodes == 4 and calls > 1


def test_draws_do_not_change_the_draw_one_search_state():
    game = KlondikeGame(1, random.Random(3))
    before = StuckSearch(game).run()
    for _ in range(30):  # robar y reciclar no cambia nada para la búsqueda en robo de a 1
        game.draw()
        assert StuckSearch(game).run() is before
