import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest

from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import Column, PileKind, PileRef
from src.solitaire.solitaire_screen import SolitaireScreen
from src.solitaire.table_layout import TableLayout

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS
LEFT = Qt.MouseButton.LeftButton
NO_MOD = Qt.KeyboardModifier.NoModifier


@pytest.fixture
def screen(qapp):
    s = SolitaireScreen()
    s.resize(1000, 720)
    s.show()
    s.deal(1)
    QTest.qWait(10)
    yield s
    s.close()


def clear_table(screen: SolitaireScreen) -> None:
    game = screen.game
    game.tableau = [Column() for _ in range(7)]
    game.stock, game.waste = [], []
    game.foundations = [[] for _ in range(4)]


def card_point(screen, ref: PileRef, index: int = -1) -> QPoint:
    """Punto en la franja visible de una carta (en coordenadas de la mesa)."""
    layout = screen.view.layout_()
    if ref.kind is PileKind.TABLEAU:
        rect = layout.column_rects(screen.game, ref.index)[index]
    elif ref.kind is PileKind.WASTE:
        rect = layout.waste_rects(screen.game)[-1][1]
    else:
        rect = layout.slot_rect(ref)
    return QPoint(int(rect.center().x()), int(rect.top() + 12))


def drag(screen, start: QPoint, end: QPoint) -> None:
    view = screen.view
    QTest.mousePress(view, LEFT, NO_MOD, start)
    QTest.mouseMove(view, start + QPoint(10, 10))
    QTest.mouseMove(view, end)
    QTest.mouseRelease(view, LEFT, NO_MOD, end)


def tab(i: int) -> PileRef:
    return PileRef(PileKind.TABLEAU, i)


def test_deal_with_mode_chosen_on_home(qapp):
    s = SolitaireScreen()
    s.deal(3)  # la pantalla de inicio reparte con el modo elegido: no hay página intermedia
    assert s.game.draw_count == 3 and s.mode_buttons[3].isChecked()


def test_click_stock_draws(screen):
    QTest.mouseClick(screen.view, LEFT, NO_MOD, card_point(screen, PileRef(PileKind.STOCK)))
    assert len(screen.game.waste) == 1 and len(screen.game.stock) == 23


def test_drag_sequence_to_valid_column(screen):
    clear_table(screen)
    screen.game.tableau[0].cards = [Card(9, D), Card(8, S), Card(7, H)]
    screen.game.tableau[3].cards = [Card(10, C)]
    screen.view.update()
    drag(screen, card_point(screen, tab(0), 0), card_point(screen, tab(3), -1))
    assert [str(c) for c in screen.game.tableau[3].cards] == ["10♣", "9♦", "8♠", "7♥"]
    assert screen.game.tableau[0].cards == []


def test_invalid_drop_returns_cards_to_origin(screen):
    clear_table(screen)
    screen.game.tableau[0].cards = [Card(9, D)]
    screen.game.tableau[3].cards = [Card(10, H)]  # mismo color: inválido
    before = [list(col.cards) for col in screen.game.tableau]
    drag(screen, card_point(screen, tab(0)), card_point(screen, tab(3)))
    assert [col.cards for col in screen.game.tableau] == before
    assert screen.view.drag is None
    drag(screen, card_point(screen, tab(0)), QPoint(5, 700))  # suelta en la nada
    assert [col.cards for col in screen.game.tableau] == before


def test_double_click_sends_card_to_foundation(screen):
    clear_table(screen)
    screen.game.tableau[2].cards = [Card(1, H)]
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(2)))
    assert screen.game.foundations[0] == [Card(1, H)] and screen.game.tableau[2].cards == []


def test_change_mode_without_progress_redeals_without_asking(screen):
    screen.confirm = lambda *a: pytest.fail("no debía preguntar")
    screen.mode_buttons[3].click()
    assert screen.game.draw_count == 3


@pytest.mark.parametrize("accept", [False, True])
def test_change_mode_with_game_in_progress_asks(screen, accept):
    asked = []
    screen.confirm = lambda parent, text: asked.append(text) or accept
    screen.game.draw()
    game_before = screen.game
    screen.mode_buttons[3].click()
    assert asked and "partida nueva" in asked[0]
    if accept:
        assert screen.game is not game_before and screen.game.draw_count == 3
    else:
        assert screen.game is game_before and screen.mode_buttons[1].isChecked()


def test_victory_message_and_new_game(screen):
    clear_table(screen)
    screen.game.foundations = [[Card(r, s) for r in range(1, 14)] for s in Suit]
    king = screen.game.foundations[3].pop()
    screen.game.tableau[0].cards = [king]
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(0)))
    assert screen.game.is_won and screen.status.text() == "¡Ganaste!"
    assert screen.victory_box is not None and not screen.view.interactive
    new_game = next(b for b in screen.victory_box.buttons() if b.text() == "Nueva partida")
    new_game.click()
    assert not screen.game.is_won and len(screen.game.stock) == 24 and screen.view.interactive


def test_cards_scale_with_window_and_long_columns_fit(screen):
    small, big = TableLayout.fit(700, 500), TableLayout.fit(1400, 1000)
    assert big.card_w > small.card_w * 1.8
    clear_table(screen)
    column = screen.game.tableau[6]
    column.cards = [Card(r, D) for r in range(1, 7)] + [Card(r, S if r % 2 else H) for r in range(13, 0, -1)]
    column.hidden = 6
    for width, height in ((1000, 720), (700, 500)):
        layout = TableLayout.fit(width, height)
        rects = layout.column_rects(screen.game, 6)
        assert rects[-1].bottom() <= height
        assert all(b.top() - a.top() >= layout.card_h * 0.12 for a, b in zip(rects[6:], rects[7:]))


# --- deshacer -----------------------------------------------------------------------
CTRL = Qt.KeyboardModifier.ControlModifier


def test_undo_button_state_and_ctrl_z(screen):
    assert not screen.undo_button.isEnabled()  # recién repartido: sin historial
    stock_point = card_point(screen, PileRef(PileKind.STOCK))
    QTest.mouseClick(screen.view, LEFT, NO_MOD, stock_point)
    assert screen.undo_button.isEnabled() and len(screen.game.waste) == 1
    screen.activateWindow()
    QTest.keyClick(screen, Qt.Key.Key_Z, CTRL)
    assert screen.game.waste == [] and len(screen.game.stock) == 24
    assert not screen.undo_button.isEnabled()


def test_undo_double_click_to_foundation(screen):
    clear_table(screen)
    screen.game.tableau[2].cards = [Card(5, C), Card(1, H)]
    screen.game.tableau[2].hidden = 1
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(2)))
    assert screen.game.foundations[0] == [Card(1, H)] and screen.game.tableau[2].hidden == 0
    screen.undo_button.click()
    assert screen.game.tableau[2].cards[-1] == Card(1, H) and screen.game.tableau[2].hidden == 1


def test_undo_disabled_after_victory(screen):
    clear_table(screen)
    screen.game.foundations = [[Card(r, s) for r in range(1, 14)] for s in Suit]
    screen.game.tableau[0].cards = [screen.game.foundations[3].pop()]
    QTest.mouseDClick(screen.view, LEFT, NO_MOD, card_point(screen, tab(0)))
    assert screen.game.is_won and not screen.undo_button.isEnabled()
    screen.undo()
    assert screen.game.is_won
