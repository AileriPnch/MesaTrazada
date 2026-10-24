"""Genera assets/app_icon.ico (multi-tamaño) y assets/app_icon_256.png desde src/app/icon_painter.py.

Uso: .venv\\Scripts\\python.exe scripts\\generar_icono.py
"""
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QBuffer, QIODevice  # noqa: E402
from PyQt6.QtGui import QGuiApplication  # noqa: E402

from src.app.icon_painter import render_app_icon  # noqa: E402

SIZES = (16, 24, 32, 48, 64, 256)
ASSETS = ROOT / "assets"


def _png_bytes(image) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def build_ico(images: dict[int, bytes]) -> bytes:
    """ICO con entradas PNG (soportado desde Windows Vista). Cada tamaño se dibuja nativo."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, blobs = b"", b""
    for size, data in sorted(images.items()):
        dim = 0 if size >= 256 else size  # 0 significa 256 en el formato ICO
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    return header + entries + blobs


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841
    ASSETS.mkdir(exist_ok=True)
    images = {size: _png_bytes(render_app_icon(size)) for size in SIZES}
    (ASSETS / "app_icon.ico").write_bytes(build_ico(images))
    (ASSETS / "app_icon_256.png").write_bytes(images[256])
    print(f"Generado {ASSETS / 'app_icon.ico'} ({', '.join(map(str, SIZES))} px)")


if __name__ == "__main__":
    main()
