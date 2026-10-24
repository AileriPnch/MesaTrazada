"""Brillos y sombras suaves pre-renderizados: el desenfoque se calcula una sola vez por tamaño.

Desenfoque "pirámide": se dibuja la forma a baja resolución y se amplía de a 2x con interpolación suave.
Da una caída gaussiana aproximada sin artefactos y cuesta poco; nunca se recalcula por frame.
"""
from math import ceil, log2
from typing import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen, QPixmap

Draw = Callable[[QPainter], None]
Layer = tuple[QPointF, QPixmap]  # posición (lógica) + pixmap listo para copiar
_FORMAT = QImage.Format.Format_ARGB32_Premultiplied


def render_layer(rect: QRectF, dpr: float, draw: Draw, opacity: float = 1.0, opaque: bool = False) -> Layer:
    """Pixmap del tamaño de `rect` (coordenadas de pantalla) con lo que dibuja `draw`.
    `opacity` deja guardada la intensidad final (p. ej. la del neón) para no aplicarla en cada frame.
    `opaque`: sin canal alfa (fondos), así copiarlo en el frame es una copia directa y no una mezcla."""
    pixmap = QPixmap(max(1, round(rect.width() * dpr)), max(1, round(rect.height() * dpr)))
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.GlobalColor.black if opaque else Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setOpacity(opacity)
    p.translate(-rect.topLeft())
    draw(p)
    p.end()
    return rect.topLeft(), pixmap


def to_device(layer: Layer, dpr: float) -> Layer:
    """La misma capa ubicada en píxeles físicos (pixmap con DPR 1). Con escalado fraccionario (125 %, 150 %)
    Qt copia los pixmaps con DPR por un camino escalado, hasta 6 veces más lento; en píxeles físicos y en
    posiciones enteras la copia es directa."""
    pos, pixmap = layer
    pixmap.setDevicePixelRatio(1.0)
    return QPointF(round(pos.x() * dpr), round(pos.y() * dpr)), pixmap


def blurred(width: float, height: float, dpr: float, radius: float, draw: Draw) -> QImage:
    """Imagen de `width`x`height` (lógicos) con lo que dibuja `draw`, desenfocado ~`radius` px lógicos."""
    full_w, full_h = max(1, ceil(width * dpr)), max(1, ceil(height * dpr))
    levels = max(0, round(log2(max(1.0, radius * dpr / 1.5))))
    factor = 2 ** levels
    small = QImage(max(1, ceil(full_w / factor)), max(1, ceil(full_h / factor)), _FORMAT)
    small.fill(Qt.GlobalColor.transparent)
    p = QPainter(small)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(dpr / factor, dpr / factor)
    draw(p)
    p.end()
    image = small
    for _ in range(levels):  # ampliar de a 2x: cada paso suaviza el anterior
        image = image.scaled(image.width() * 2, image.height() * 2, Qt.AspectRatioMode.IgnoreAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    if (image.width(), image.height()) != (full_w, full_h):
        image = image.copy(0, 0, full_w, full_h)
    image.setDevicePixelRatio(dpr)
    return image


def blur_image(image: QImage, radius: float) -> QImage:
    """La misma imagen desenfocada ~`radius` px (pirámide: reducir y volver a ampliar de a 2x)."""
    levels = max(0, round(log2(max(1.0, radius / 1.5))))
    if levels == 0:
        return image
    factor = 2 ** levels
    w, h = image.width(), image.height()
    small = image.scaled(max(1, ceil(w / factor)), max(1, ceil(h / factor)), Qt.AspectRatioMode.IgnoreAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    for _ in range(levels):
        small = small.scaled(small.width() * 2, small.height() * 2, Qt.AspectRatioMode.IgnoreAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    return small.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)


def neon_color(hex_color: str, alpha: float) -> QColor:
    color = QColor(hex_color)
    color.setAlphaF(max(0.0, min(1.0, alpha)))
    return color


def faded_line_pen(color: str, alpha: float, width: float, start: QPointF, end: QPointF) -> QPen:
    """Pincel de una línea que se desvanece en sus dos extremos."""
    gradient = QLinearGradient(start, end)
    for stop, a in ((0.0, 0.0), (0.12, alpha), (0.88, alpha), (1.0, 0.0)):
        gradient.setColorAt(stop, neon_color(color, a))
    pen = QPen(gradient, width)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    return pen


def glow_layer(rect: QRectF, dpr: float, radius: float, source: Draw, sharp: Draw | None = None,
               opacity: float = 1.0) -> Layer:
    """Capa con `source` desenfocado (el brillo) y, encima, `sharp` nítido (la línea de neón)."""
    def draw(p: QPainter) -> None:
        def shifted(q: QPainter) -> None:
            q.translate(-rect.left(), -rect.top())
            source(q)

        p.drawImage(rect.topLeft(), blurred(rect.width(), rect.height(), dpr, radius, shifted))
        if sharp is not None:
            sharp(p)

    return render_layer(rect, dpr, draw, opacity)
