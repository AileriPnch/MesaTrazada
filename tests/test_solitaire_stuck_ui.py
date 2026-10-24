"""Aviso "No quedan movimientos" en la pantalla: opciones, "Seguir mirando", límite y porciones."""
import logging

from PyQt6.QtTest import QTest

from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import PileKind, PileRef
from tests.fakes import wait_until
from tests.test_solitaire_ui import LEFT, NO_MOD, card_point, screen, tab  # noqa: F401 (fixture)

H = Suit.HEARTS


def load(screen, source) -> None:
    game = screen.game
    game.tableau, game.stock, game.waste, game.foundations = source.tableau, source.stock, source.waste, source.foundations
    screen.view.update()


def make_nearly_stuck(screen):
    """Posición muerta salvo un As en la columna 3: llevarlo a la fundación deja la partida trabada."""
    from tests.test_stuck_detector import dead_game

    load(screen, dead_game())
    screen.game.tableau[3].cards = [Card(1, H)]


def button(box, text):
    return next(b for b in box.buttons() if b.text() == text)


def test_stuck_warning_offers_three_options(screen):
    make_nearly_stuck(screen)
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(3)))
    box = screen.stuck_box
    assert box is not None and box.isVisible() and box.windowTitle() == "No quedan movimientos"
    assert {b.text() for b in box.buttons()} == {"Nueva partida", "Deshacer", "Seguir mirando"}
    button(box, "Nueva partida").click()
    assert len(screen.game.stock) == 24 and not screen.game.can_undo


def test_keep_looking_does_not_warn_again_until_position_changes(screen):
    make_nearly_stuck(screen)
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(3)))
    first = screen.stuck_box
    button(first, "Seguir mirando").click()
    assert not first.isVisible()
    for _ in range(8):  # recorrer el mazo y reciclar no vuelve a avisar
        QTest.mouseClick(screen.view, LEFT, NO_MOD, card_point(screen, PileRef(PileKind.STOCK)))
    assert screen.stuck_box is first and not first.isVisible()


def test_undo_from_warning_reevaluates(screen):
    make_nearly_stuck(screen)
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(3)))
    first = screen.stuck_box
    button(first, "Deshacer").click()
    assert screen.game.tableau[3].cards == [Card(1, H)]  # volvió el As: ya no está trabada
    assert not first.isVisible() and screen.stuck_box is first
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(3)))
    assert screen.stuck_box is not first and screen.stuck_box.isVisible()  # misma traba: avisa de nuevo


def test_no_warning_when_the_search_hits_its_limit(screen, caplog):
    from tests.test_stuck_detector import huge_dead_game

    load(screen, huge_dead_game())  # trabada de verdad, pero imposible de agotar
    with caplog.at_level(logging.INFO):
        QTest.mouseClick(screen.view, LEFT, NO_MOD, card_point(screen, PileRef(PileKind.STOCK)))
        assert screen.watcher.running  # no terminó en la primera porción: sigue sin frenar la UI
        assert wait_until(lambda: not screen.watcher.running, timeout=5)
    assert screen.stuck_box is None and "cortada por límite" in caplog.text


def test_slow_search_runs_in_slices_and_waits_for_a_drag(screen, monkeypatch):
    from src.solitaire import stuck_watcher

    monkeypatch.setattr(stuck_watcher, "SLICE_SECONDS", 0)  # un estado por porción: queda pendiente
    make_nearly_stuck(screen)
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(3)))
    assert screen.watcher.running and screen.stuck_box is None
    point = card_point(screen, tab(1))
    QTest.mousePress(screen.view, LEFT, NO_MOD, point)  # agarra el 9♥: el aviso no puede abrirse ahora
    QTest.qWait(100)
    assert screen.watcher.running and screen.stuck_box is None
    QTest.mouseRelease(screen.view, LEFT, NO_MOD, point)
    assert wait_until(lambda: screen.stuck_box is not None and screen.stuck_box.isVisible())
