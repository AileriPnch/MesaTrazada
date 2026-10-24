"""Sonidos de la app: efectos cortos (WAV en assets/sounds) con QSoundEffect, que reproduce sin frenar la
interfaz, y un único volumen global con silencio.

Si QtMultimedia, el dispositivo de audio o un archivo fallan, la app sigue sin ese sonido y lo deja en el
log. Sin reproductor instalado (tests) `play` no hace nada."""
import logging
from enum import Enum
from functools import partial
from pathlib import Path
from time import monotonic

from PyQt6.QtCore import QObject, QTimer, QUrl

from src.common.volume import Volume

logger = logging.getLogger(__name__)

SOUND_DIR = Path(__file__).resolve().parents[2] / "assets" / "sounds"
MIN_GAP = 0.09  # s: el mismo sonido no se repite en ráfaga (ni se superpone consigo mismo)


class Sound(Enum):
    MOVE = "ajedrez_mover"
    CAPTURE = "ajedrez_capturar"
    CHECK = "ajedrez_jaque"
    CASTLE = "ajedrez_enroque"
    PROMOTE = "ajedrez_coronar"
    WIN = "ganar"  # ajedrez ganado y solitario completado
    LOSE = "perder_o_tablas"
    DRAW_CARD = "solitario_robar"
    PLACE = "solitario_apoyar"
    FLIP = "solitario_voltear"
    FOUNDATION = "solitario_fundacion"
    RECYCLE = "solitario_reciclar"
    DEAL = "solitario_repartir"


class SoundPlayer(QObject):
    """Un QSoundEffect por sonido, cargados una vez (en segundo plano, los carga Qt)."""

    def __init__(self, volume: Volume, directory: Path = SOUND_DIR, parent: QObject | None = None):
        super().__init__(parent)
        self.volume = volume
        self._effects = {}
        self._last: dict[Sound, float] = {}
        try:
            from PyQt6.QtMultimedia import QMediaDevices, QSoundEffect
        except ImportError as exc:  # PyQt6 sin QtMultimedia
            logger.warning("Sin sonido: no se pudo cargar QtMultimedia (%s)", exc)
            return
        if QMediaDevices.defaultAudioOutput().isNull():
            logger.warning("Sin sonido: no hay dispositivo de salida de audio")
            return
        for item in Sound:
            path = directory / f"{item.value}.wav"
            if not path.is_file():
                logger.warning("Falta el sonido %s", path)
                continue
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.statusChanged.connect(self._on_status)
            self._effects[item] = effect
        self._apply_volume()
        volume.changed.connect(self._apply_volume)
        logger.info("Sonido listo: %s efectos", len(self._effects))

    @property
    def available(self) -> bool:
        return bool(self._effects)

    def play(self, item: Sound) -> None:
        effect = self._effects.get(item)
        if effect is None or self.volume.gain == 0.0:
            return
        now = monotonic()
        if now - self._last.get(item, -1.0) < MIN_GAP:
            return
        self._last[item] = now
        effect.play()  # asincrónico; si ya sonaba, vuelve a empezar (nunca dos copias superpuestas)

    def _apply_volume(self) -> None:
        for effect in self._effects.values():
            effect.setVolume(self.volume.gain)

    def _on_status(self) -> None:
        effect = self.sender()
        if effect.status() == effect.Status.Error:
            logger.warning("No se pudo cargar el sonido %s", effect.source().toLocalFile())


_volume: Volume | None = None
_player: SoundPlayer | None = None


def volume() -> Volume:
    """El volumen global (en memoria hasta que `main.py` instale uno que se guarda)."""
    global _volume
    if _volume is None:
        _volume = Volume()
    return _volume


def install(new_volume: Volume | None = None, player: SoundPlayer | None = None) -> None:
    global _volume, _player
    if new_volume is not None:
        _volume = new_volume
    _player = player


def play(item: Sound) -> None:
    if _player is not None:
        _player.play(item)


def play_later(item: Sound, delay_ms: int) -> None:
    QTimer.singleShot(delay_ms, partial(play, item))
