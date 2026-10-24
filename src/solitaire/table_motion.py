"""Animaciones de la mesa: cartas en vuelo (reparto, doble clic a la fundación, descarte, sueltas), giros y la
luz de la victoria. Son sólo visuales: la partida ya está en su estado final cuando empiezan, nada espera a
que terminen y cualquier acción del jugador las completa al instante (`finish`)."""
from dataclasses import dataclass
from math import cos, pi
from time import monotonic

from PyQt6.QtCore import QObject, QRectF, Qt, QTimer

from src.solitaire.cards import Card

FRAME_MS = 16
CELEBRATION_MS = 1900


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


@dataclass
class Tween:
    card: Card
    start: QRectF
    end: QRectF
    begin: float  # ms (monotonic) en que empieza a moverse; antes espera en `start`
    duration: float
    face_from: bool
    face_to: bool

    def state(self, now: float) -> tuple[QRectF, bool, float]:
        """(rectángulo, boca arriba, escala horizontal) en `now`. Un cambio de cara es un giro simulado: la
        carta se angosta hasta el canto y vuelve a abrirse mostrando la otra cara."""
        t = min(1.0, max(0.0, (now - self.begin) / self.duration))
        k = _ease_out(t)
        a, b = self.start, self.end
        rect = QRectF(a.x() + (b.x() - a.x()) * k, a.y() + (b.y() - a.y()) * k,
                      a.width() + (b.width() - a.width()) * k, a.height() + (b.height() - a.height()) * k)
        if self.face_from == self.face_to:
            return rect, self.face_to, 1.0
        return rect, self.face_to if t >= 0.5 else self.face_from, max(0.04, abs(cos(pi * t)))


class TableMotion(QObject):
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.tweens: dict[Card, Tween] = {}
        self.celebration: float | None = None
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(FRAME_MS)
        self.timer.timeout.connect(self._tick)

    @staticmethod
    def now() -> float:
        return monotonic() * 1000

    @property
    def active(self) -> bool:
        return bool(self.tweens) or self.celebration is not None

    def add(self, card: Card, start: QRectF, end: QRectF, duration: float, delay: float = 0.0,
            face_from: bool = True, face_to: bool = True) -> None:
        self.tweens.pop(card, None)  # vuelve al final: se dibuja encima de las anteriores
        self.tweens[card] = Tween(card, QRectF(start), QRectF(end), self.now() + delay, duration, face_from, face_to)
        self._run()

    def celebrate(self) -> None:
        self.celebration = self.now()
        self._run()

    def covers(self, card: Card) -> bool:
        return card in self.tweens

    def frames(self, now: float) -> list[tuple[Card, QRectF, bool, float]]:
        return [(card, *tween.state(now)) for card, tween in self.tweens.items()]

    def celebration_level(self, now: float) -> float | None:
        """0..1 del avance de la celebración, o None si no hay."""
        if self.celebration is None:
            return None
        return min(1.0, (now - self.celebration) / CELEBRATION_MS)

    def finish(self) -> None:
        """Todo a su estado final ya: el jugador actuó (o se repartió otra partida)."""
        if self.active:
            self.tweens.clear()
            self.celebration = None
            self.timer.stop()
            self.widget.update()

    def _run(self) -> None:
        if not self.timer.isActive():
            self.timer.start()
        self.widget.update()

    def _tick(self) -> None:
        now = self.now()
        for card in [c for c, t in self.tweens.items() if now >= t.begin + t.duration]:
            del self.tweens[card]
        if self.celebration is not None and now - self.celebration >= CELEBRATION_MS:
            self.celebration = None
        if not self.active:
            self.timer.stop()
        self.widget.update()
