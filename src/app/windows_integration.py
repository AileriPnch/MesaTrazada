"""Integración con el shell de Windows: AppUserModelID e ícono de la app."""
import ctypes
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Debe coincidir con el que crear_acceso_directo.ps1 graba en el acceso directo.
APP_USER_MODEL_ID = "JScandizzo.MesaTrazada"
ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "app_icon_blender.ico"  # el del .exe (build_windows.py)


def set_app_user_model_id(app_id: str = APP_USER_MODEL_ID) -> None:
    """Sin esto la barra de tareas agrupa la ventana bajo el ícono de pythonw.exe.

    Debe llamarse antes de crear cualquier ventana.
    """
    if sys.platform != "win32":
        return
    try:
        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ctypes.c_wchar_p(app_id))
        if result != 0:
            logger.warning("SetCurrentProcessExplicitAppUserModelID devolvió 0x%08X", result & 0xFFFFFFFF)
    except (AttributeError, OSError):
        logger.exception("No se pudo fijar el AppUserModelID")


def load_app_icon():
    from PyQt6.QtGui import QIcon

    if not ICON_PATH.exists():
        logger.warning("No se encontró el ícono en %s", ICON_PATH)
        return QIcon()
    return QIcon(str(ICON_PATH))
