"""Volumen global de la app (0-100) y silencio. Es lo único que se guarda entre sesiones (QSettings)."""
from PyQt6.QtCore import QObject, QSettings, pyqtSignal

from src.common.app_info import APP_ID, LEGACY_ID

DEFAULT_LEVEL = 70
ORGANIZATION = "JScandizzo"
KEYS = ("audio/volume", "audio/muted")


def migrate_settings(old: QSettings, new: QSettings) -> bool:
    """Una vez: si la clave nueva está vacía, copia volumen y silencio de la del nombre anterior (la vieja queda)."""
    if any(new.contains(k) for k in KEYS) or not any(old.contains(k) for k in KEYS):
        return False
    for key in KEYS:
        if old.contains(key):
            new.setValue(key, old.value(key))
    new.sync()
    return True


def settings_store() -> QSettings:
    """Registro del usuario (HKCU\\Software\\JScandizzo\\MesaTrazada): sólo volumen y silencio."""
    store = QSettings(ORGANIZATION, APP_ID)
    migrate_settings(QSettings(ORGANIZATION, LEGACY_ID), store)
    return store


class Volume(QObject):
    """Volumen global 0-100 y silencio. Con `store` se recuerdan entre sesiones; nada más se guarda."""
    changed = pyqtSignal()

    def __init__(self, store: QSettings | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._store = store
        level = store.value("audio/volume", DEFAULT_LEVEL, type=int) if store is not None else DEFAULT_LEVEL
        self._level = max(0, min(100, level))
        self._muted = store.value("audio/muted", False, type=bool) if store is not None else False

    @property
    def level(self) -> int:
        return self._level

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def gain(self) -> float:
        """Ganancia 0..1 con curva perceptiva (la mitad del deslizador suena a la mitad)."""
        return 0.0 if self._muted else (self._level / 100) ** 2

    def set_level(self, level: int) -> None:
        level = max(0, min(100, int(level)))
        if level != self._level:
            self._level = level
            self._save("audio/volume", level)

    def set_muted(self, muted: bool) -> None:
        if muted != self._muted:
            self._muted = muted
            self._save("audio/muted", muted)

    def _save(self, key: str, value) -> None:
        if self._store is not None:
            self._store.setValue(key, value)
        self.changed.emit()
