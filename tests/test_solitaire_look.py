"""Aspecto del solitario: palos y distribución de las cartas, fundaciones con su palo, animaciones que nunca
hacen esperar, destinos marcados al arrastrar y textos sin cortar."""
import pytest
from PyQt6.QtCore import QPoint
from PyQt6.QtTest import QTest

from src.solitaire.card_assets import CardAssets
from src.solitaire.card_painter import PIPS
from src.solitaire.cards import Card, Suit, new_deck
from src.solitaire.klondike import Column, KlondikeGame, PileKind, PileRef
from src.solitaire.solitaire_screen import SolitaireScreen
from src.solitaire.suit_shapes import suit_path
from src.solitaire.table_layout import foundation_labels
from src.solitaire.table_motion import CELEBRATION_MS
from tests.test_layout_fit import clipped
from tests.test_solitaire_ui import LEFT, NO_MOD, card_point, clear_table, screen, tab  # noqa: F401 (fixture)

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS


def test_pip_layouts_have_one_pip_per_point():
    assert all(len(PIPS[rank]) == rank for rank in range(2, 11))


def test_suits_are_own_vector_shapes():
    boxes = {suit: suit_path(suit, QPoint(0, 0), 10).boundingRect() for suit in Suit}
    assert all(abs(b.height() - 10) < 0.6 and b.width() > 6 for b in boxes.values())


def test_every_card_renders_once_per_size(qapp):
    assets = CardAssets(60, 84, 1.0)
    for card in new_deck():
        assert not assets.face(card).pixmap.isNull()
    assert not assets.back().pixmap.isNull() and assets.renders == 53
    assets.face(Card(12, H))
    assert assets.renders == 53  # la segunda vez sale de la caché


def test_empty_foundations_show_a_suit_that_is_still_missing():
    game = KlondikeGame(1)
    assert foundation_labels(game) == [H, C, D, S]
    game.foundations[0] = [Card(1, S)]  # un As de picas en el lugar de corazones (vale: cualquiera vacío)
    labels = foundation_labels(game)
    assert labels[0] is None and S not in labels and set(labels[1:]) == {C, D, H}


def test_double_click_sends_an_ace_to_the_foundation_showing_its_suit(screen):
    clear_table(screen)
    screen.game.tableau[2].cards = [Card(1, D)]
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(2)))
    assert screen.game.foundations[2] == [Card(1, D)]  # ♥ ♣ ♦ ♠: el de diamantes es el tercero


def test_animations_never_make_the_player_wait(screen):
    view = screen.view
    screen.new_game()
    assert view.motion.active and len(view.motion.tweens) == 28  # reparto animado
    assert sum(len(col.cards) for col in screen.game.tableau) == 28  # la partida ya está repartida
    QTest.mouseClick(view, LEFT, NO_MOD, card_point(screen, PileRef(PileKind.STOCK)))
    assert len(screen.game.waste) == 1  # el clic robó igual...
    assert set(view.motion.tweens) == {screen.game.waste[-1]}  # ...y el reparto ya terminó: sólo vuela la robada
    QTest.qWait(600)
    assert not view.motion.active  # las animaciones terminan solas


def test_drag_marks_only_valid_destinations_and_invalid_drop_returns(screen):
    clear_table(screen)
    game = screen.game
    game.tableau[0] = Column([Card(9, D), Card(8, S)], 0)
    game.tableau[3] = Column([Card(10, C)], 0)
    game.tableau[5] = Column([Card(10, S)], 0)
    view = screen.view
    start = card_point(screen, tab(0), 0)
    QTest.mousePress(view, LEFT, NO_MOD, start)
    QTest.mouseMove(view, start + QPoint(12, 12))
    QTest.mouseMove(view, start + QPoint(30, 40))
    assert view.drag.targets == [PileRef(PileKind.TABLEAU, 3), PileRef(PileKind.TABLEAU, 5)]
    QTest.mouseRelease(view, LEFT, NO_MOD, QPoint(5, view.height() - 5))  # suelta en la nada
    assert game.tableau[0].cards == [Card(9, D), Card(8, S)]
    assert set(view.motion.tweens) == {Card(9, D), Card(8, S)}  # vuelven volando a su lugar


def test_victory_celebrates(screen):
    clear_table(screen)
    game = screen.game
    game.foundations = [[Card(r, s) for r in range(1, 14)] for s in Suit]
    game.tableau[0].cards = [game.foundations[3].pop()]
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(0)))
    assert screen.view.motion.celebration is not None
    QTest.qWait(CELEBRATION_MS + 120)
    assert not screen.view.motion.active
    screen.victory_box.reject()


@pytest.mark.parametrize("size", [(800, 600), (1000, 720), (1920, 1080)])
def test_bar_and_dialogs_fit(qapp, size):
    from src.app.stylesheet import apply_theme
    from src.solitaire import dialogs

    apply_theme(qapp)
    s = SolitaireScreen()
    s.resize(*size)
    s.show()
    s.deal(3)
    QTest.qWait(30)
    assert clipped(s) == []
    for box in (dialogs.show_victory(s, s.new_game), dialogs.show_stuck(s, True, s.new_game, s.undo)):
        QTest.qWait(20)
        assert clipped(box) == []
        box.reject()
    s.shutdown()
    s.close()
