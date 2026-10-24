"""Controlador del motor en el hilo de la UI: hilo de trabajo, pedidos y descarte de respuestas viejas."""
import logging
import math
import time
from pathlib import Path
from typing import Callable

import chess
from PyQt6.QtCore import QCoreApplication, QObject, Qt, QThread, QTimer, pyqtSignal

from src.chess_game.difficulty import EngineLevel
from src.chess_game.engine_worker import EngineWorker

logger = logging.getLogger(__name__)

THREAD_STOP_TIMEOUT_MS = 8000


class EngineController(QObject):
    ready = pyqtSignal()
    failed = pyqtSignal(str)
    move_ready = pyqtSignal(object)  # chess.Move, sólo del pedido vigente

    _start_requested = pyqtSignal()
    _think_requested = pyqtSignal(int, object, object)

    def __init__(self, engine_path: Path, factory: Callable[[Path], object] | None = None, parent=None,
                 min_reply: float = 0.0):
        super().__init__(parent)
        self._request_id = 0
        self._pending: int | None = None
        # Ritmo humano: una jugada que llega antes de min_reply segundos se retiene hasta cumplirlos.
        self._min_reply = min_reply
        self._asked_at = 0.0
        self._held: chess.Move | None = None
        self._release = QTimer(self)
        self._release.setSingleShot(True)
        self._release.setTimerType(Qt.TimerType.PreciseTimer)  # el grueso puede adelantarse un 5 %
        self._release.timeout.connect(self._deliver)
        self._closed = False
        self.is_ready = False

        self._thread = QThread()
        self._thread.setObjectName("stockfish-worker")
        self._worker = EngineWorker(engine_path, factory)
        self._worker.moveToThread(self._thread)
        self._start_requested.connect(self._worker.start)
        self._think_requested.connect(self._worker.think)
        self._worker.ready.connect(self._on_ready)
        self._worker.failed.connect(self._on_failed)
        self._worker.move_found.connect(self._on_move_found)
        app = QCoreApplication.instance()
        if app is not None:  # red de seguridad si la app sale sin pasar por closeEvent
            app.aboutToQuit.connect(self.shutdown)

    @property
    def is_thinking(self) -> bool:
        return self._pending is not None

    def start(self) -> None:
        self._thread.start()
        self._start_requested.emit()

    def request_move(self, board: chess.Board, level: EngineLevel) -> None:
        if self._closed:
            return
        self._drop_held()
        self._request_id += 1
        self._pending = self._request_id
        self._asked_at = time.monotonic()
        logger.debug("Pedido %s al motor (%s, Elo %s)", self._request_id, level.mode.value, level.elo)
        self._think_requested.emit(self._request_id, board.copy(), level)

    def cancel(self) -> None:
        """Invalida la búsqueda en curso (o la jugada retenida): si su jugada llega después, se descarta."""
        if self._pending is not None:
            logger.info("Búsqueda %s cancelada", self._pending)
        self._drop_held()
        self._request_id += 1
        self._pending = None

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.cancel()
        self._worker.shutdown()
        self._thread.quit()
        if not self._thread.wait(THREAD_STOP_TIMEOUT_MS):
            logger.error("El hilo del motor no terminó a tiempo")

    def _on_ready(self) -> None:
        self.is_ready = True
        self.ready.emit()

    def _on_failed(self, message: str) -> None:
        self._drop_held()
        self._pending = None
        if not self._closed:
            self.failed.emit(message)

    def _on_move_found(self, request_id: int, move: chess.Move) -> None:
        if self._closed or request_id != self._pending:
            logger.info("Jugada %s del pedido %s descartada (vigente: %s)", move, request_id, self._pending)
            return
        self._held = move
        wait = self._min_reply - (time.monotonic() - self._asked_at)
        if wait > 0:
            self._release.start(math.ceil(wait * 1000))
        else:
            self._deliver()

    def _deliver(self) -> None:
        move, self._held = self._held, None
        if move is None or self._closed:
            return
        self._pending = None
        self.move_ready.emit(move)

    def _drop_held(self) -> None:
        self._release.stop()
        self._held = None
