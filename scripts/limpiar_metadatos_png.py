"""Saca los metadatos de texto de los PNG (Blender graba ahí la ruta del .blend, con el usuario de la PC, la fecha y
los tiempos de render). Sólo quita los bloques tEXt / zTXt / iTXt / tIME: los píxeles no cambian.

Uso: .\\.venv\\Scripts\\python.exe scripts\\limpiar_metadatos_png.py [carpeta ...]   (por defecto: assets/)
"""
import logging
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIGNATURE = b"\x89PNG\r\n\x1a\n"
DROP = {b"tEXt", b"zTXt", b"iTXt", b"tIME"}

logger = logging.getLogger("limpiar_metadatos_png")


def chunks(data: bytes):
    """(tipo, bloque entero con largo y CRC) de cada bloque del PNG."""
    i = len(SIGNATURE)
    while i < len(data):
        length, kind = struct.unpack(">I4s", data[i:i + 8])
        end = i + 12 + length
        yield kind, data[i:end]
        i = end


def text_chunks(data: bytes) -> list[bytes]:
    return [kind for kind, _ in chunks(data) if kind in DROP]


def strip(data: bytes) -> bytes:
    if not data.startswith(SIGNATURE):
        raise ValueError("no es un PNG")
    return SIGNATURE + b"".join(chunk for kind, chunk in chunks(data) if kind not in DROP)


def clean_folder(folder: Path) -> int:
    changed = 0
    for path in sorted(folder.rglob("*.png")):
        data = path.read_bytes()
        if text_chunks(data):
            path.write_bytes(strip(data))
            changed += 1
    return changed


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    folders = [Path(a) for a in argv] or [ROOT / "assets"]
    for folder in folders:
        logger.info("%s: %d PNG limpiados", folder, clean_folder(folder))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
