"""Datos públicos de la app en UN solo lugar: nombre, versión, enlaces (código fuente, donaciones) y créditos.

Los usan el "Acerca de", la ventana, el build (`scripts/build_windows.py` lee VERSION de acá) y los tests.
Un enlace vacío no se muestra (ni el del código fuente ni el de una donación).
"""
from dataclasses import dataclass

APP_NAME = "Mesa Trazada"
APP_ID = "MesaTrazada"  # sin espacios: .exe, .zip, carpeta de datos, registro, AppUserModelID
LEGACY_ID = "AjedrezSolitario"  # el nombre anterior (hasta 1.0.0): sus datos se migran una vez
VERSION = "1.0.1"
AUTHOR = "Juan Scandizzo"
LICENSE_NAME = "GNU GPL v3"
LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"
SOURCE_URL = "https://github.com/AileriPnch/MesaTrazada"

# Donaciones opcionales: (nombre, enlace).
DONATIONS: tuple[tuple[str, str], ...] = (
    ("Cafecito", "https://cafecito.app/aileri"),
    ("Ko-fi", "https://ko-fi.com/aileri57918"),
)


@dataclass(frozen=True)
class Credit:
    role: str  # para qué se usa
    name: str
    author: str
    license: str
    url: str


CREDITS: tuple[Credit, ...] = (
    Credit("Motor de ajedrez", "Stockfish 19", "The Stockfish developers", "GPLv3",
           "https://github.com/official-stockfish/Stockfish/tree/sf_19"),
    Credit("Reglas del ajedrez", "python-chess", "Niklas Fiekas", "GPLv3", "https://github.com/niklasf/python-chess"),
    Credit("Interfaz", "PyQt6", "Riverbank Computing", "GPLv3", "https://www.riverbankcomputing.com/software/pyqt/"),
    Credit("Interfaz", "Qt 6", "The Qt Company", "LGPLv3", "https://www.qt.io/"),
    Credit("Fuentes", "Playfair Display", "The Playfair Display Project Authors", "SIL OFL 1.1",
           "https://github.com/clauseggers/Playfair-Display"),
    Credit("Fuentes", "Inter", "The Inter Project Authors", "SIL OFL 1.1", "https://github.com/rsms/inter"),
    Credit("Fuentes", "Caveat", "The Caveat Project Authors", "SIL OFL 1.1", "https://github.com/googlefonts/caveat"),
    Credit("Sonidos", "Kenney", "Kenney Vleugels", "CC0 1.0", "https://kenney.nl"),
    Credit("Configuración", "python-dotenv", "Saurabh Kumar", "BSD-3-Clause", "https://github.com/theskumar/python-dotenv"),
)


def donation_links() -> list[tuple[str, str]]:
    """Sólo las donaciones con enlace."""
    return [(name, url) for name, url in DONATIONS if url.strip()]
