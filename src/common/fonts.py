"""Fuentes embebidas (assets/fonts, licencia OFL): se registran en Qt al arrancar, sin depender de lo
instalado en la PC. Son fuentes variables: Qt elige la instancia real de cada peso (SemiBold, Medium…)."""
import logging
from pathlib import Path

from PyQt6.QtGui import QFontDatabase

from src.common import theme

logger = logging.getLogger(__name__)

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
_loaded: set[str] = set()


def load_fonts() -> set[str]:
    """Registra todas las fuentes de assets/fonts (una vez; requiere QGuiApplication). Devuelve las familias."""
    if _loaded:
        return _loaded
    for path in sorted(FONT_DIR.glob("*/*.ttf")):
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            logger.warning("No se pudo cargar la fuente %s", path)
            continue
        _loaded.update(QFontDatabase.applicationFontFamilies(font_id))
    for family in {theme.TYPE.title_family, theme.TYPE.ui_family, theme.TYPE.hand_family} - _loaded:
        logger.warning("Falta la fuente %r: Qt va a usar una de reemplazo", family)
    return _loaded
