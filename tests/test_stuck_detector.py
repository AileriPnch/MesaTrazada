import copy
import random

from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import Column
from src.solitaire.stuck_detector import Outcome, StuckSearch, accessible_stock_cards, is_stuck
from tests.test_klondike import empty_game, fnd, tab

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS
FILLER = [Card(7, D), Card(3, S), Card(12, C), Card(5, D), Card(9, S), Card(6, H)]  # ninguna juega


def dead_game(draw_count: int = 1):
    """Posición sin avance posible: base de los casos."""
    game = empty_game(draw_count)
    game.tableau[0].cards = [Card(4, C), Card(9, C)]  # 9♣ necesita 10 rojo: no hay
    game.tableau[0].hidden = 1
    game.tableau[1].cards = [Card(2, D), Card(10, C), Card(9, H)]
    game.tableau[1].hidden = 1
    game.tableau[2].cards = [Card(10, S)]
    game.tableau[2].hidden = 0
    game.stock = list(FILLER)
    return game


def huge_dead_game(draw_count: int = 1):
    """Traba real con un espacio de estados enorme: Ases y 3 boca abajo, ninguna columna se puede vaciar
    y 36 cartas del mazo se pueden colgar de los 4 Reyes de muchísimas formas. No se puede agotar."""
    game = empty_game(draw_count)
    bases = [([Card(1, S), Card(3, H), Card(2, C)], Card(13, H)), ([Card(1, H), Card(3, D)], Card(13, S)),
             ([Card(1, D), Card(3, S)], Card(13, C)), ([Card(1, C), Card(3, C)], Card(13, D)),
             ([], Card(2, S)), ([], Card(2, H)), ([], Card(2, D))]
    game.tableau = [Column(hidden + [up], len(hidden)) for hidden, up in bases]
    game.stock = [Card(r, s) for r in range(4, 13) for s in Suit]
    random.Random(1).shuffle(game.stock)
    return game


def test_dead_position_is_stuck_and_detection_does_not_mutate():
    game = dead_game()
    before = copy.deepcopy((game.tableau, game.stock, game.waste, game.foundations))
    assert is_stuck(game)
    assert (game.tableau, game.stock, game.waste, game.foundations) == before


def test_shuffle_between_columns_is_explored_but_is_not_progress():
    # 9♥ puede pasar de la columna 1 al 10♠ de la columna 2 (y volver), pero no destapa nada.
    game = dead_game()
    assert game.can_move(tab(1), 2, tab(2))
    search = StuckSearch(game)
    assert search.run() is Outcome.STUCK and search.nodes == 2  # las dos disposiciones, agotadas


def test_move_that_reveals_a_card_is_progress():
    game = dead_game()
    game.tableau[3].cards = [Card(10, D)]  # 9♣ (toda la parte boca arriba) va encima y destapa el 4♣
    assert not is_stuck(game)


def test_emptying_a_column_is_progress_only_if_something_uses_it():
    # Cambio de criterio: antes vaciar una columna contaba como productivo por sí solo.
    game = dead_game()
    game.tableau[3].cards, game.tableau[5].cards, game.tableau[6].cards = [Card(13, S)], [Card(13, C)], [Card(13, D)]
    game.tableau[4].cards = [Card(8, D)]  # 8♦ sobre el 9♣ vacía la columna 4...
    assert is_stuck(game)  # ...pero ningún Rey con cartas boca abajo puede aprovecharla
    game.tableau[6].cards, game.tableau[6].hidden = [Card(5, S), Card(13, H)], 1
    assert not is_stuck(game)  # ahora el K♥ pasa a la columna vacía y destapa el 5♠


def test_card_to_foundation_is_progress():
    game = dead_game()
    game.tableau[3].cards = [Card(1, H)]
    assert not is_stuck(game)


def test_real_stuck_exhausts_all_states_including_returns_from_foundation():
    game = dead_game()
    game.foundations[0] = [Card(1, D), Card(2, D)]
    game.tableau[3].cards = [Card(3, C)]  # el 2♦ puede volver sobre el 3♣, pero no habilita nada
    search = StuckSearch(game)
    assert search.run() is Outcome.STUCK
    assert search.nodes == 4  # (9♥ en su lugar o sobre el 10♠) x (2♦ arriba o devuelto): todos vistos


def test_regression_exit_that_needs_a_card_back_from_the_foundation():
    """Patrón del caso real: la única salida empieza devolviendo el 9♣ de la fundación."""
    game = empty_game()
    game.foundations = [[Card(r, C) for r in range(1, 10)], [Card(r, D) for r in range(1, 7)],
                        [Card(r, S) for r in range(1, 9)], []]
    game.tableau[0].cards = [Card(13, S), Card(12, H), Card(11, S), Card(10, D)]
    game.tableau[1].cards, game.tableau[1].hidden = [Card(3, H), Card(10, H), Card(9, S), Card(8, D)], 1
    game.tableau[2].cards = [Card(10, S)]
    assert not is_stuck(game)
    # La salida existe de verdad: 9♣ al 10♦, 8♦ al 9♣, 9♠ y 10♠ a la fundación (una carta más que antes).
    assert game.move(fnd(0), 8, tab(0)) and game.move(tab(1), 3, tab(0))
    assert game.move(tab(1), 2, fnd(2)) and game.move(tab(2), 0, fnd(2))
    assert sum(len(f) for f in game.foundations) == 24


def test_waste_card_to_column_counts_only_if_it_leads_somewhere():
    # Cambio de criterio: antes jugar del descarte a una columna contaba como productivo por sí solo.
    game = dead_game()
    game.waste = [Card(9, D)]  # 9♦ puede ir al 10♠, pero después no hay nada más
    assert is_stuck(game)
    game.tableau[1].cards = [Card(2, D), Card(10, C)]  # sin el 9♥ que servía de base al 8♣
    game.tableau[3].cards, game.tableau[3].hidden = [Card(6, S), Card(8, C)], 1
    assert not is_stuck(game)  # 9♦ al 10♣ y el 8♣ encima: se destapa el 6♠


def test_draw_one_every_stock_card_is_accessible():
    game = dead_game(1)
    game.stock.insert(0, Card(1, S))  # al fondo del mazo
    assert not is_stuck(game)


def test_draw_three_only_group_tops_are_accessible():
    # Orden de robo = stock[::-1]. Grupos de 3: sólo la última de cada grupo queda arriba.
    game = dead_game(3)
    order = [Card(7, D), Card(1, S), Card(12, C), Card(5, D), Card(9, S), Card(6, H)]
    game.stock = order[::-1]
    assert Card(1, S) not in accessible_stock_cards(game)
    assert is_stuck(game)  # el As está en el medio de un grupo: nunca queda arriba
    order[1], order[2] = order[2], order[1]  # ahora es la tercera del primer grupo
    game.stock = order[::-1]
    assert not is_stuck(game)


def test_draw_three_only_exit_is_after_recycling():
    # Descarte [w1, w2], mazo por robar [c1..c4]. En esta pasada quedan arriba w2, c3 y c4;
    # tras reciclar, la pasada completa [w1, w2, c1 | c2, c3, c4] deja arriba a c1 y c4.
    game = dead_game(3)
    w1, w2, c1, c2, c3, c4 = FILLER
    game.waste = [w1, w2]
    game.stock = [c4, c3, c2, c1]
    assert accessible_stock_cards(game) == [w2, c3, c4, c1]
    game.stock = [c4, c3, c2, Card(1, H)]  # c1 = As: sólo se alcanza tras reciclar
    assert not is_stuck(game)
    game.waste, game.stock = [Card(1, H), w2], [c4, c3, c2, c1]  # As en w1: nunca queda arriba
    assert is_stuck(game)


def test_won_game_is_not_stuck():
    game = empty_game()
    game.foundations = [[Card(r, s) for r in range(1, 14)] for s in Suit]
    assert not is_stuck(game)
