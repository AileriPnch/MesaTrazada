"""Worker que vive en un QThread y habla con Stockfish (llamadas bloqueantes de python-chess)."""
import logging
import random
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

import chess
import chess.engine
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.chess_game.difficulty import EngineLevel
from src.chess_game.engine_search import search_move

logger = logging.getLogger(__name__)

ENGINE_TIMEOUT = 5.0  # margen de python-chess sobre el tiempo de cada comando


def open_stockfish(path: Path) -> chess.engine.SimpleEngine:
    popen_args = {}
    if sys.platform == "win32":
        # python-chess no lo pone: sin esto, desde pythonw.exe se abre una consola para Stockfish.
        popen_args["creationflags"] = subprocess.CREATE_NO_WINDOW
    return chess.engine.SimpleEngine.popen_uci(str(path), timeout=ENGINE_TIMEOUT, **popen_args)


class EngineWorker(QObject):
    ready = pyqtSignal()
    failed = pyqtSignal(str)
    move_found = pyqtSignal(int, object)  # request_id, chess.Move

    def __init__(self, engine_path: Path, factory: Callable[[Path], object] | None = None,
                 rng: random.Random | None = None):
        super().__init__()
        self._path = engine_path
        self._factory = factory or open_stockfish
        self._lock = threading.Lock()
        self._engine = None
        self._closing = False
        self._rng = rng or random.Random()

    @property
    def engine(self):
        with self._lock:
            return self._engine

    @pyqtSlot()
    def start(self) -> None:
        try:
            engine = self._factory(self._path)
        except Exception as exc:
            logger.exception("No se pudo iniciar el motor en %s", self._path)
            self.failed.emit(f"No se pudo iniciar Stockfish ({self._path}): {exc}")
            return
        with self._lock:
            closing = self._closing
            if not closing:
                self._engine = engine
        if closing:  # se pidió cerrar mientras arrancaba
            self._close_engine(engine)
            return
        logger.info("Motor iniciado: %s", self._path)
        self.ready.emit()

    @pyqtSlot(int, object, object)
    def think(self, request_id: int, board: chess.Board, level: EngineLevel) -> None:
        engine = self.engine
        if engine is None:
            return
        try:
            choice = search_move(engine, board, level, self._rng)
        except Exception as exc:
            with self._lock:
                closing = self._closing
            if not closing:  # al cerrar, la búsqueda en curso termina con error: es esperable
                logger.exception("Error del motor durante la búsqueda")
                self.failed.emit(f"Stockfish dejó de responder: {exc}")
            return
        if choice is not None:
            logger.debug("Pedido %s: %s (%s, pierde %s cp, nivel %s)", request_id, choice.move, choice.reason,
                         choice.loss, level.mode.value)
            self.move_found.emit(request_id, choice.move)

    def shutdown(self) -> None:
        """Llamable desde cualquier hilo: los métodos de SimpleEngine son thread-safe."""
        with self._lock:
            self._closing = True
            engine, self._engine = self._engine, None
        if engine is not None:
            self._close_engine(engine)

    @staticmethod
    def _close_engine(engine) -> None:
        try:
            engine.quit()  # interrumpe una búsqueda en curso; el proceso termina
        except Exception:
            logger.warning("quit() del motor falló; se fuerza el cierre", exc_info=True)
        finally:
            engine.close()  # cierra el transporte; si el proceso sigue vivo, lo mata
        logger.info("Motor cerrado")
