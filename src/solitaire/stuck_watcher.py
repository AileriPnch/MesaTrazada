"""Corre la búsqueda de traba en porciones cortas dentro del bucle de eventos: la UI nunca se frena."""
import logging
from typing import Callable

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.solitaire.stuck_detector import Outcome, StuckSearch

logger = logging.getLogger(__name__)

SLICE_SECONDS = 0.01  # cálculo máximo por vuelta del bucle de eventos
BUSY_RETRY_MS = 30  # durante un arrastre se espera (sin girar en vacío) y se reintenta


class StuckWatcher(QObject):
    stuck = pyqtSignal()  # la búsqueda agotó los estados alcanzables sin encontrar avance

    def __init__(self, parent: QObject, is_busy: Callable[[], bool]):
        super().__init__(parent)
        self._is_busy = is_busy
        self.search: StuckSearch | None = None
        self._timer = QTimer(self, singleShot=True, timeout=self._step)

    @property
    def running(self) -> bool:
        return self.search is not None

    def start(self, game) -> None:
        """Busca sobre el estado actual. La primera porción corre en el acto (casi siempre alcanza)."""
        self.cancel()
        self.search = StuckSearch(game)
        self._step()

    def cancel(self) -> None:
        self._timer.stop()
        self.search = None

    def _step(self) -> None:
        search = self.search
        if search is None:
            return
        if self._is_busy():  # no competir con un arrastre ni abrir el aviso en medio de uno
            self._timer.start(BUSY_RETRY_MS)
            return
        outcome = search.advance(SLICE_SECONDS)
        if outcome is None:
            self._timer.start(0)  # sigue en la próxima vuelta, después de atender eventos y pintar
            return
        self.search = None
        ms = search.elapsed * 1000
        if outcome is Outcome.STUCK:
            logger.info("Partida trabada: %d estados recorridos sin avance (%.1f ms)", search.nodes, ms)
            self.stuck.emit()
        elif outcome is Outcome.LIMIT:
            logger.info("Búsqueda de traba cortada por límite (%d estados, %.0f ms): no se avisa", search.nodes, ms)
        else:
            logger.debug("Hay avance posible (%d estados, %.1f ms)", search.nodes, ms)
