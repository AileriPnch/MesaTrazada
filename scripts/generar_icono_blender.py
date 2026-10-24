"""Ícono propuesto para el lanzamiento, con el arte de Blender: el caballo blanco renderizado (cuerpo + brillos) y un
naipe con el dorso del solitario detrás, sobre un cuadrado de nogal (`mesa.png`) con filo ámbar. En 16-32 px va sólo
el caballo, más grande (el naipe no se distinguía). Genera assets/app_icon_blender.ico (multi-tamaño) y app_icon_blender_256.png;
con --comparar deja también una lámina ícono viejo / nuevo en docs/screenshots/.

Uso: .venv\\Scripts\\python.exe scripts\\generar_icono_blender.py [--comparar]
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPointF, QRect, QRectF, Qt  # noqa: E402
from PyQt6.QtGui import (QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath,  # noqa: E402
                         QPen, QRadialGradient)

from scripts.generar_icono import SIZES, _png_bytes, build_ico  # noqa: E402
from src.common.theme import COLORS  # noqa: E402

ART = ROOT / "assets" / "ajedrez"
ASSETS = ROOT / "assets"


def _opaque_bounds(image: QImage, threshold: int = 8) -> QRect:
    alpha = image.convertToFormat(QImage.Format.Format_Alpha8)
    xs, ys = [], []
    step = 2
    for y in range(0, alpha.height(), step):
        row = alpha.constScanLine(y)
        row.setsize(alpha.bytesPerLine())
        data = bytes(row)
        for x in range(0, alpha.width(), step):
            if data[x] > threshold:
                xs.append(x)
                ys.append(y)
    return QRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def knight_image() -> QImage:
    """Cuerpo + brillo del caballo blanco (como en el tablero: el brillo se suma en modo Plus), recortado."""
    body = QImage(str(ART / "blancas_caballo.png")).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    shine = QImage(str(ART / "blancas_caballo_brillo.png")).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    p = QPainter(body)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
    p.drawImage(0, 0, shine)
    p.end()
    return body.copy(_opaque_bounds(body))


def _tile(p: QPainter, size: int) -> QPainterPath:
    rect = QRectF(0, 0, size, size).adjusted(0.5, 0.5, -0.5, -0.5)
    tile = QPainterPath()
    tile.addRoundedRect(rect, size * 0.2, size * 0.2)
    p.save()
    p.setClipPath(tile)
    wood = QImage(str(ART / "mesa.png"))
    crop = QRectF(wood.width() * 0.30, wood.height() * 0.30, wood.width() * 0.25, wood.height() * 0.25)
    p.drawImage(rect, wood, crop)
    p.fillRect(rect, QColor(0, 0, 0, 120))  # el nogal oscuro, para que resalten el caballo y el naipe
    light = QRadialGradient(QPointF(size * 0.3, size * 0.25), size * 0.9)
    light.setColorAt(0, QColor(255, 227, 184, 70))  # la lámpara arriba a la izquierda (COLORS.lamp)
    light.setColorAt(1, QColor(0, 0, 0, 90))
    p.fillRect(rect, light)
    p.restore()
    return tile


def _card(p: QPainter, size: int) -> None:
    from src.solitaire.card_back import draw_back_foil, draw_card_back

    w, h = size * 0.42, size * 0.60
    p.save()
    p.translate(size * 0.66, size * 0.44)
    p.rotate(14)
    rect = QRectF(-w / 2, -h / 2, w, h)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 110))
    p.drawRoundedRect(rect.translated(size * 0.02, size * 0.03), size * 0.04, size * 0.04)  # sombra (luz arriba izq.)
    draw_card_back(p, rect)
    draw_back_foil(p, rect)
    p.restore()


def render_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    tile = _tile(p, size)
    simple = size <= 32
    if not simple:
        _card(p, size)
    knight = knight_image()
    height = size * (0.92 if simple else 0.76)
    width = height * knight.width() / knight.height()
    left = (size - width) / 2 if simple else size * 0.06
    top = size - height - size * (0.04 if simple else 0.08)
    p.drawImage(QRectF(left, top, width, height), knight)
    rim = QLinearGradient(0, 0, size, size)
    rim.setColorAt(0, QColor(COLORS.accent_hover))
    rim.setColorAt(1, QColor(COLORS.accent_dark))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(rim, max(1.0, size / 64)))
    p.drawPath(tile)
    p.end()
    return image


def comparison(old: dict[int, QImage], new: dict[int, QImage]) -> QImage:
    sizes = (256, 64, 48, 32, 24, 16)
    width = sum(sizes) + 40 * (len(sizes) + 1)
    sheet = QImage(width, 2 * 256 + 3 * 40, QImage.Format.Format_ARGB32_Premultiplied)
    sheet.fill(QColor("#202225"))
    p = QPainter(sheet)
    for row, images in enumerate((old, new)):
        x = 40
        for s in sizes:
            p.drawImage(QPointF(x, 40 + row * (256 + 40) + (256 - s) / 2), images[s])
            x += s + 40
    p.end()
    return sheet


def main(argv: list[str]) -> None:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841
    sizes = sorted(set(SIZES) | {24})
    images = {size: render_icon(size) for size in sizes}
    (ASSETS / "app_icon_blender.ico").write_bytes(build_ico({s: _png_bytes(i) for s, i in images.items()}))
    images[256].save(str(ASSETS / "app_icon_blender_256.png"))
    print(f"Generado {ASSETS / 'app_icon_blender.ico'} ({', '.join(map(str, sizes))} px)")
    if "--comparar" in argv:
        from src.app.icon_painter import render_app_icon

        old = {s: render_app_icon(s) for s in (256, 64, 48, 32, 24, 16)}
        out = ROOT / "docs" / "screenshots" / "icono_viejo_vs_propuesta.png"
        comparison(old, {s: render_icon(s) for s in old}).save(str(out))
        print(f"Comparación: {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
