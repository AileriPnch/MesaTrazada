"""Carpetas de la app, desde el código o empaquetada (PyInstaller). Sólo biblioteca estándar (y app_info): main.py
lo usa antes de configurar nada.

- Recursos (assets, engine): junto al código; en el build, dentro de `_internal/` (`sys._MEIPASS`).
- Instalación: la raíz del proyecto, o la carpeta del .exe (ahí va el `.env` opcional y `licencias/`).
- Logs: `logs/` del proyecto, o `%LOCALAPPDATA%\\MesaTrazada\\logs` en el build (la carpeta del .exe puede no
  tener permiso de escritura). La carpeta del nombre anterior (`AjedrezSolitario`) se migra una vez.
"""
import os
import shutil
import sys
from pathlib import Path

from src.common.app_info import APP_ID, LEGACY_ID

DATA_DIR_NAME = APP_ID  # el mismo nombre que usa QSettings (src/common/volume.py)


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    return Path(__file__).resolve().parents[2]


def install_dir() -> Path:
    return Path(sys.executable).resolve().parent if frozen() else resource_root()


def local_appdata() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local"))


def default_log_dir() -> Path:
    if not frozen():
        return resource_root() / "logs"
    return local_appdata() / DATA_DIR_NAME / "logs"


def migrate_legacy_data(base: Path | None = None) -> str:
    """Una sola vez: si existe la carpeta del nombre anterior y todavía no la nueva, la renombra (o, si algo la
    tiene abierta, la copia y deja la vieja). Nunca pisa ni borra datos de la nueva. Devuelve qué hizo."""
    base = base or local_appdata()
    old, new = base / LEGACY_ID, base / DATA_DIR_NAME
    if not old.is_dir() or new.exists():
        return "nada"
    try:
        old.rename(new)
        return "movida"
    except OSError:
        try:
            shutil.copytree(old, new)
            return "copiada"
        except OSError:
            shutil.rmtree(new, ignore_errors=True)  # a medias no sirve: queda la vieja y se reintenta la próxima
            return "falló"


def licenses_dir() -> Path:
    """Licencias y créditos: `licencias/` junto al .exe; desde el código, la raíz (LICENSE, CREDITS.md)."""
    return install_dir() / "licencias" if frozen() else resource_root()
