"""Motor falso para tests: imita la API de SimpleEngine que usa EngineWorker."""
import threading
import time
from types import SimpleNamespace

import chess
import chess.engine
from chess.engine import Option
from PyQt6.QtTest import QTest

ELO_MIN, ELO_MAX = 1320, 3190  # lo que reporta Stockfish 19


class FakeEngine:
    def __init__(self, delay: float = 0.0, script: list[str] | None = None, evals: dict[str, int] | None = None):
        self.delay = delay
        self.script = list(script or [])
        self.evals = evals  # uci -> cp (lado que mueve) para analyse(); None = todas 0, -10, -20...
        self.options = {
            "UCI_Elo": Option("UCI_Elo", "spin", 1320, ELO_MIN, ELO_MAX, []),
            "UCI_LimitStrength": Option("UCI_LimitStrength", "check", False, None, None, []),
            "Skill Level": Option("Skill Level", "spin", 20, 0, 20, []),
            "MultiPV": Option("MultiPV", "spin", 1, 1, 256, []),
        }
        self.config = {}  # opciones vigentes, como las lleva python-chess
        self.searches = 0
        self.quit_called = False
        self.closed = False
        self._stop = threading.Event()

    def configure(self, options):
        self.config.update(options)

    def _wait(self):
        self.searches += 1
        if self._stop.wait(self.delay):  # quit() interrumpe la búsqueda como el motor real
            raise chess.engine.EngineTerminatedError("engine terminated")

    def play(self, board: chess.Board, limit):
        self._wait()
        self.config["MultiPV"] = 1  # python-chess lo vuelve al default en cada play()
        if self.script:
            move = chess.Move.from_uci(self.script.pop(0))
        else:
            move = sorted(board.legal_moves, key=lambda m: m.uci())[0]
        return SimpleNamespace(move=move)

    def analyse(self, board: chess.Board, limit, multipv=None):
        self._wait()
        self.config["MultiPV"] = multipv or 1
        if self.evals is None:
            moves = sorted(board.legal_moves, key=lambda m: m.uci())
            scored = [(m, -10 * i) for i, m in enumerate(moves)]
        else:
            scored = sorted(((chess.Move.from_uci(u), cp) for u, cp in self.evals.items()), key=lambda x: -x[1])
        return [{"pv": [m], "score": chess.engine.PovScore(chess.engine.Cp(cp), board.turn)}
                for m, cp in scored[:multipv or 1]]

    def quit(self):
        self.quit_called = True
        self._stop.set()

    def close(self):
        self.closed = True
        self._stop.set()


def factory_for(engine: FakeEngine):
    return lambda path: engine


def wait_until(predicate, timeout: float = 3.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        QTest.qWait(10)
    return predicate()
