import logging

import chess
import pytest
from PyQt6.QtTest import QTest

from config import settings
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from tests.fakes import FakeEngine, factory_for, wait_until


@pytest.fixture
def make_screen(qapp, monkeypatch):
    monkeypatch.setattr(settings, "club_time", 0.01)
    screens = []

    def make(engine: FakeEngine, color=ColorChoice.WHITE) -> ChessScreen:
        screen = ChessScreen(engine_factory=factory_for(engine))
        assert wait_until(lambda: screen.engine.is_ready)
        screen.start_game(color, Difficulty.CLUB)
        screens.append(screen)
        return screen

    yield make
    for screen in screens:
        screen.shutdown()


def _move(screen: ChessScreen, uci: str) -> None:
    move = chess.Move.from_uci(uci)
    screen._on_player_move(move.from_square, move.to_square)


def test_white_player_moves_then_engine_replies(make_screen):
    screen = make_screen(FakeEngine())
    assert screen.side.clock.state == "negras" and screen.side.clock.thinking is None  # mueven las blancas
    assert screen.board_view.interactive and not screen.board_view.flipped
    _move(screen, "e2e4")
    assert not screen.board_view.interactive  # bloqueado mientras piensa
    assert screen.side.clock.thinking == chess.BLACK  # la luz del lado de Stockfish
    assert wait_until(lambda: len(screen.game.board.move_stack) == 2)
    assert screen.board_view.interactive and screen.game.is_player_turn
    assert screen.side.move_texts[0] == "e4"


def test_black_player_engine_moves_first_and_board_flipped(make_screen):
    screen = make_screen(FakeEngine(), ColorChoice.BLACK)
    assert screen.board_view.flipped
    assert wait_until(lambda: len(screen.game.board.move_stack) == 1)
    assert screen.game.is_player_turn and screen.board_view.interactive


def test_undo_during_engine_search_discards_its_move(make_screen):
    engine = FakeEngine(delay=0.3)
    screen = make_screen(engine)
    _move(screen, "e2e4")
    QTest.qWait(50)
    assert screen.engine.is_thinking
    screen.undo()
    assert screen.game.board.fen() == chess.STARTING_FEN
    assert screen.board_view.interactive and not screen.engine.is_thinking
    QTest.qWait(600)  # la búsqueda vieja termina y su jugada llega: debe descartarse
    assert screen.game.board.fen() == chess.STARTING_FEN
    assert screen.side.move_texts == []


def test_new_game_during_engine_search_discards_its_move(make_screen):
    engine = FakeEngine(delay=0.3)
    screen = make_screen(engine)
    _move(screen, "e2e4")
    QTest.qWait(50)
    screen.new_game()  # empieza otra con el mismo color y dificultad, sin página intermedia
    assert screen.game.board.move_stack == [] and screen.game.is_player_turn
    QTest.qWait(600)
    assert screen.game.board.move_stack == [] and screen.game.is_player_turn


def test_new_game_repeats_color_and_difficulty(make_screen):
    screen = make_screen(FakeEngine(), ColorChoice.BLACK)
    assert wait_until(lambda: len(screen.game.board.move_stack) == 1)
    screen.new_game()
    assert screen.game.player_color == chess.BLACK and screen.board_view.flipped
    assert screen.difficulty is Difficulty.CLUB
    assert wait_until(lambda: len(screen.game.board.move_stack) == 1)  # el motor vuelve a empezar


def test_new_game_as_black_during_search_gets_fresh_engine_move(make_screen):
    engine = FakeEngine(delay=0.2, script=["e7e5", "d2d4"])
    screen = make_screen(engine)
    _move(screen, "e2e4")  # el motor (negras) empieza a pensar "e7e5"
    QTest.qWait(30)
    screen.start_game(ColorChoice.BLACK, Difficulty.CLUB)  # cancela la búsqueda vieja
    assert wait_until(lambda: len(screen.game.board.move_stack) == 1, timeout=3)
    QTest.qWait(300)
    assert screen.game.san_moves() == ["d4"]  # "e7e5" (de la partida vieja) se descartó


def test_promotion_uses_dialog_choice(make_screen, monkeypatch):
    screen = make_screen(FakeEngine())
    screen.game.board.set_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    screen.ask_promotion = lambda color, parent: chess.KNIGHT
    _move(screen, "a7a8")
    assert screen.game.board.piece_at(chess.A8) == chess.Piece(chess.KNIGHT, chess.WHITE)


def test_promotion_cancelled_keeps_position(make_screen):
    screen = make_screen(FakeEngine())
    screen.game.board.set_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    screen.ask_promotion = lambda color, parent: None
    _move(screen, "a7a8")
    assert screen.game.board.piece_at(chess.A7) is not None and screen.game.is_player_turn


def test_game_over_shows_result_and_reason(make_screen):
    screen = make_screen(FakeEngine(script=["e7e5", "d8h4"]))
    _move(screen, "f2f3")
    assert wait_until(lambda: len(screen.game.board.move_stack) == 2)
    _move(screen, "g2g4")
    assert wait_until(lambda: screen.game.result() is not None)
    card = screen.side.card  # la tarjeta sobre la planilla (ya no hay diálogo)
    assert not card.isHidden() and card.headline == "Ganó Stockfish" and "Jaque mate" in card.text
    assert "Jaque mate" in screen.side.status_text
    assert screen.side.sheet.result == "0–1 · Jaque mate"
    assert screen.board_view.toppled == chess.E1  # el rey vencido se acuesta
    assert screen.side.clock.state == "parejos" and screen.side.clock.thinking is None
    assert not screen.board_view.interactive
    screen.undo()  # deshacer el mate: el rey se levanta y la tarjeta se va
    assert screen.board_view.toppled is None and card.isHidden()


def test_missing_stockfish_shows_error_without_crashing(qapp, monkeypatch, tmp_path, caplog):
    missing = tmp_path / "no_esta" / "stockfish.exe"
    monkeypatch.setattr(settings, "stockfish_path", missing)
    with caplog.at_level(logging.ERROR):
        screen = ChessScreen()
    assert screen.engine is None
    screen.start_game(ColorChoice.WHITE, Difficulty.CLUB)
    assert "No se encontró Stockfish" in screen.side.status_text
    assert not screen.side.card.isHidden() and str(missing) in screen.side.card.text
    assert not screen.board_view.interactive
    assert any("No se encontró Stockfish" in r.getMessage() for r in caplog.records)
    screen.shutdown()


def test_promotion_dialog_returns_choice_or_none(qapp):
    from src.chess_game.promotion_dialog import PromotionDialog

    dialog = PromotionDialog(chess.BLACK)
    dialog.buttons[chess.ROOK].click()
    assert dialog.choice == chess.ROOK
    cancelled = PromotionDialog(chess.WHITE)
    cancelled.reject()  # Esc o cerrar: no se corona
    assert cancelled.choice is None
