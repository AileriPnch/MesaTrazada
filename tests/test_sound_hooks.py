"""Cada acción de los juegos dispara su sonido (con un reproductor que sólo anota)."""
import chess
import pytest
from PyQt6.QtTest import QTest

from config import settings
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from src.common import sound
from src.common.sound import Sound
from src.solitaire.cards import Card, Suit
from src.solitaire.klondike import Column, PileKind, PileRef
from src.solitaire.solitaire_screen import WIN_DELAY_MS, SolitaireScreen
from src.solitaire.solitaire_view import FLIP_DELAY_MS
from tests.fakes import FakeEngine, factory_for, wait_until
from tests.test_sound import Recorder

S, H = Suit.SPADES, Suit.HEARTS


@pytest.fixture
def played(qapp):
    QTest.qWait(450)  # sonidos diferidos de tests anteriores: que suenen antes (sin reproductor, no hacen nada)
    rec = Recorder()
    sound.install(player=rec)
    yield rec.played
    sound.install(player=None)


def test_chess_moves_and_game_end_play_their_sounds(played, monkeypatch):
    monkeypatch.setattr(settings, "club_time", 0.01)
    screen = ChessScreen(engine_factory=factory_for(FakeEngine(script=["e7e5", "d8h4"])))
    try:  # toda ChessScreen pasa por shutdown(): si no, el hilo del motor aborta el proceso
        assert wait_until(lambda: screen.engine.is_ready)
        screen.start_game(ColorChoice.WHITE, Difficulty.CLUB)
        screen._on_player_move(chess.F2, chess.F3)
        assert wait_until(lambda: len(screen.game.board.move_stack) == 2)
        assert played == [Sound.MOVE, Sound.MOVE]  # la mía y la del motor
        screen._on_player_move(chess.G2, chess.G4)
        assert wait_until(lambda: screen.game.result() is not None)
        assert played[-1] is Sound.CHECK  # el mate llega como jaque...
        QTest.qWait(500)
        assert played[-1] is Sound.LOSE  # ...y después el final: perdí
    finally:
        screen.shutdown()


def _clear(screen: SolitaireScreen) -> None:
    game = screen.game
    game.tableau = [Column() for _ in range(7)]
    game.stock, game.waste = [], []
    game.foundations = [[] for _ in range(4)]


def test_solitaire_actions_play_their_sounds(played):
    screen = SolitaireScreen()
    screen.deal(1)
    assert played == [Sound.DEAL]
    view, game = screen.view, screen.game
    view._draw()
    assert played[-1] is Sound.DRAW_CARD
    game.stock = []
    QTest.qWait(120)  # fuera de la ventana anti-ráfaga
    view._draw()
    assert played[-1] is Sound.RECYCLE
    _clear(screen)
    game.tableau[0] = Column([Card(13, S), Card(1, H)], hidden=1)  # el As tapa un rey boca abajo
    assert view._move(PileRef(PileKind.TABLEAU, 0), 1, PileRef(PileKind.FOUNDATION, 0))
    assert played[-1] is Sound.FOUNDATION
    QTest.qWait(FLIP_DELAY_MS + 60)
    assert played[-1] is Sound.FLIP  # el rey quedó destapado y se dio vuelta
    game.tableau[1] = Column([Card(12, H)])
    QTest.qWait(120)
    assert view._move(PileRef(PileKind.TABLEAU, 1), 0, PileRef(PileKind.TABLEAU, 0))  # Q♥ sobre el K♠
    assert played[-1] is Sound.PLACE
    screen.shutdown()


def test_solitaire_victory_sound(played):
    screen = SolitaireScreen()
    screen.deal(1)
    _clear(screen)
    game = screen.game
    game.foundations = [[Card(r, s) for r in range(1, 14)] for s in Suit]
    game.foundations[0].pop()
    game.tableau[0] = Column([Card(13, list(Suit)[0])])
    assert screen.view._move(PileRef(PileKind.TABLEAU, 0), 0, PileRef(PileKind.FOUNDATION, 0))
    QTest.qWait(WIN_DELAY_MS + 80)
    assert played[-2:] == [Sound.FOUNDATION, Sound.WIN]
    screen.shutdown()
