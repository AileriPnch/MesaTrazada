"""Integración con Stockfish real: el proceso del motor muere siempre al salir del juego."""
import ctypes
import random
import sys
from dataclasses import replace

import chess
import pytest
from PyQt6.QtTest import QTest

from config import settings
from src.app.main_window import MainWindow
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty, level_for
from src.chess_game.engine_search import elo_range, search_move
from src.chess_game.engine_worker import open_stockfish
from src.solitaire.solitaire_screen import SolitaireScreen
from tests.fakes import wait_until

pytestmark = [
    pytest.mark.skipif(sys.platform != "win32", reason="chequeo de procesos con la API de Windows"),
    pytest.mark.skipif(not settings.stockfish_path.is_file(), reason="Stockfish no instalado"),
]

SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0


def process_exited(pid: int, timeout_ms: int = 3000) -> bool:
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return True  # ya no existe
    try:
        return kernel32.WaitForSingleObject(ctypes.c_void_p(handle), timeout_ms) == WAIT_OBJECT_0
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def _open_chess_thinking(window: MainWindow) -> int:
    """Abre ajedrez, espera el motor real y lo deja pensando (jugador con negras, nivel Máximo)."""
    window.open_game(ChessScreen)
    screen = window.game
    assert wait_until(lambda: screen.engine.is_ready, timeout=15)
    pid = screen.engine._worker.engine.transport.get_pid()
    assert not process_exited(pid, 0)
    screen.start_game(ColorChoice.BLACK, Difficulty.MAXIMUM)
    QTest.qWait(100)
    assert screen.engine.is_thinking
    return pid


def test_real_engine_plays_legal_move(qapp):
    window = MainWindow()
    window.open_game(ChessScreen)
    screen = window.game
    assert wait_until(lambda: screen.engine.is_ready, timeout=15)
    screen.start_game(ColorChoice.BLACK, Difficulty.BEGINNER)
    assert wait_until(lambda: len(screen.game.board.move_stack) == 1, timeout=10)
    assert screen.game.board.turn == chess.BLACK and screen.board_view.interactive
    window.close()


@pytest.mark.parametrize("exit_action", ["back_to_menu", "switch_game", "close_window"])
def test_engine_process_dies_while_thinking(qapp, exit_action):
    window = MainWindow()
    pid = _open_chess_thinking(window)
    if exit_action == "back_to_menu":
        window.game.back_requested.emit()
    elif exit_action == "switch_game":
        window.open_game(SolitaireScreen)
    else:
        window.close()
    assert process_exited(pid), f"stockfish.exe (pid {pid}) sigue vivo tras {exit_action}"
    window.close()


def test_real_engine_options_follow_each_level():
    """Mismo proceso: Club -> Principiante -> Máximo. Lo que python-chess dejó enviado al motor (config)."""
    engine = open_stockfish(settings.stockfish_path)
    try:
        low, high = elo_range(engine)
        board, rng = chess.Board(), random.Random(0)
        expected = {
            Difficulty.CLUB: (True, min(max(settings.club_elo, low), high), 1),
            Difficulty.BEGINNER: (False, high, settings.principiante.multipv),
            Difficulty.MAXIMUM: (False, high, 1),
        }
        for difficulty, (limited, elo, multipv) in expected.items():
            level = level_for(difficulty, settings)
            if difficulty is Difficulty.MAXIMUM:
                level = replace(level, seconds=0.05)  # rápido: sólo importan las opciones
            assert search_move(engine, board, level, rng).move in board.legal_moves
            config = engine.protocol.config
            assert (config["UCI_LimitStrength"], config["UCI_Elo"], config["MultiPV"]) == (limited, elo, multipv)
    finally:
        engine.quit()
