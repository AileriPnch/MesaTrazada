"""Arte renderizado del ajedrez (Blender, ver blender/INTEGRACION.md): carga de los PNG y sus medidas.

Nada se carga al arrancar la app: la pantalla de inicio pide sólo los cuerpos de las piezas que dibuja
(`piece_body`); el resto (mesa, tablero, sombras, reflejos, brillos) se precarga en otro hilo al abrir las
opciones del ajedrez (`prefetch`) y, si hace falta, se termina de cargar al abrir el ajedrez (`library`).
"""
import logging
import threading
import time

import chess
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QImage

from config import PROJECT_ROOT
from src.chess_game.board_glare import remove_glare
from src.chess_game.interface_art import InterfaceArt

logger = logging.getLogger(__name__)

ART_DIR = PROJECT_ROOT / "assets" / "ajedrez"
FORMAT = QImage.Format.Format_ARGB32_Premultiplied

# Sprites de las piezas: 512 x 512, 1 casilla = 426,67 px; punto de apoyo (centro de la base).
SPRITE_SQUARE = 426.67
ANCHOR = QPointF(256.0, 445.4)
REFLECTION_ANCHOR = QPointF(256.0, 51.2)  # el reflejo cuelga hacia abajo desde acá
ANCHOR_UP = 0.15  # el apoyo va a 0,15 del lado de la casilla por encima de su borde inferior
# Tablero: 2048 x 2048, casillas desde (48,76; 48,76). Mesa: 3840 x 2880, mismo centro que el tablero.
BOARD_SQUARE = 243.81
BOARD_FRAME = 48.76
TABLE_SQUARE = 240.0

LAYERS = ("", "sombra", "contacto", "reflejo", "brillo")  # "" = la pieza
_COLORS = {chess.WHITE: "blancas", chess.BLACK: "negras"}
_NAMES = {chess.KING: "rey", chess.QUEEN: "dama", chess.ROOK: "torre", chess.BISHOP: "alfil",
          chess.KNIGHT: "caballo", chess.PAWN: "peon"}


def file_name(piece: chess.Piece, layer: str = "") -> str:
    name = f"{_COLORS[piece.color]}_{_NAMES[piece.piece_type]}"
    return f"{name}_{layer}.png" if layer else f"{name}.png"


def all_pieces() -> list[chess.Piece]:
    return [chess.Piece(t, c) for c in chess.COLORS for t in chess.PIECE_TYPES]


def _load(name: str) -> QImage:
    image = QImage(str(ART_DIR / name))
    if image.isNull():
        raise FileNotFoundError(f"No se pudo leer {ART_DIR / name}")
    return image.convertToFormat(FORMAT)


class ArtLibrary:
    """Todas las imágenes del ajedrez, una vez por sesión (se re-escalan desde acá al cambiar el tamaño)."""

    def __init__(self):
        started = time.perf_counter()
        self.table = _load("mesa.png")
        self.board = remove_glare(_load("tablero.png"), BOARD_SQUARE, BOARD_FRAME)  # sin el velo de b6-b7
        self._layers = {(piece, layer): _load(file_name(piece, layer)) for piece in all_pieces() for layer in LAYERS}
        self.ui = InterfaceArt(ART_DIR / "interfaz", FORMAT)  # planilla, reloj, placas, bandeja, tarjeta, perilla
        logger.info("Arte del ajedrez cargado en %.0f ms", (time.perf_counter() - started) * 1000)

    def layer(self, piece: chess.Piece, layer: str = "") -> QImage:
        return self._layers[(piece, layer)]

    def toppled(self, color: chess.Color, layer: str = "") -> QImage:
        """El rey acostado (jaque mate), con los mismos pases y el mismo encuadre que las piezas."""
        return self.ui.image(f"{_COLORS[color]}_rey_acostado{'_' + layer if layer else ''}.png")


_library: ArtLibrary | None = None
_loader: threading.Thread | None = None
_lock = threading.Lock()
_bodies: dict[chess.Piece, QImage] = {}


def _load_library() -> None:
    global _library
    try:
        library = ArtLibrary()
    except Exception:  # se reintenta (y se informa) al pedirla en el hilo de la UI
        logger.exception("Falló la precarga del arte del ajedrez")
        return
    with _lock:
        _library = library


def prefetch() -> None:
    """Empieza a cargar todo en otro hilo (QImage se puede leer fuera del hilo de la UI). Idempotente."""
    global _loader
    with _lock:
        if _library is not None or _loader is not None:
            return
        _loader = threading.Thread(target=_load_library, name="chess-art", daemon=True)
        _loader.start()


def library() -> ArtLibrary:
    """Todo el arte; espera a la precarga si está en curso o carga en el momento si nunca empezó."""
    global _library
    with _lock:
        loader = _loader
    if _library is None and loader is not None:
        loader.join()
    if _library is None:
        loaded = ArtLibrary()
        with _lock:
            _library = loaded
    return _library


def is_loaded() -> bool:
    return _library is not None


def piece_body(piece: chess.Piece) -> QImage:
    """Sólo la pieza (sin sombra ni reflejo). La usa el inicio sin cargar el resto del arte."""
    if _library is not None:
        return _library.layer(piece)
    body = _bodies.get(piece)
    if body is None:
        body = _bodies[piece] = _load(file_name(piece))
    return body
