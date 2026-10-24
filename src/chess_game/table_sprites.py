"""Dibujar los objetos de la mesa: dónde va cada PNG para que la caja de su objeto caiga en un rectángulo, los
pixmaps escalados (suave, una vez por tamaño y DPR: pintar sólo los copia) y el texto grabado del latón."""
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, QSizeF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap

from src.chess_game.interface_art import Box, InterfaceArt
from src.common.theme import COLORS

MAX_CACHED = 240


@dataclass(frozen=True)
class Placement:
    """Escala (px lógicos por px del PNG) y esquina del PNG (coordenadas lógicas del widget)."""
    scale: float
    origin: QPointF

    def point(self, x: float, y: float) -> QPointF:
        return QPointF(self.origin.x() + x * self.scale, self.origin.y() + y * self.scale)

    def rect(self, box: Box) -> QRectF:
        x0, y0, x1, y1 = box
        return QRectF(self.point(x0, y0), self.point(x1, y1))

    def translated(self, dx: float, dy: float) -> "Placement":
        return Placement(self.scale, self.origin + QPointF(dx, dy))


def place(box: Box, target: QRectF) -> Placement:
    """La caja `box` (px del PNG) entera dentro de `target`, centrada y sin deformar."""
    x0, y0, x1, y1 = box
    scale = min(target.width() / (x1 - x0), target.height() / (y1 - y0))
    origin = target.center() - QPointF((x0 + x1) / 2 * scale, (y0 + y1) / 2 * scale)
    return Placement(scale, origin)


class UiSprites:
    """Los PNG de la interfaz escalados a demanda. La clave es el tamaño final en px físicos: mientras no cambie
    la ventana, dibujar no genera nada nuevo. Mientras se redimensiona (`stretching`), se estira el último pixmap de
    cada PNG en vez de generar uno por paso; al terminar se generan los del tamaño final."""

    def __init__(self, ui: InterfaceArt):
        self.ui = ui
        self._cache: dict[tuple, QPixmap] = {}
        self._last: dict[str, QPixmap] = {}
        self.stretching = False
        self.renders = 0

    def pixmap(self, name: str, scale: float, dpr: float) -> QPixmap:
        image = self.ui.image(name)
        w, h = max(1, round(image.width() * scale * dpr)), max(1, round(image.height() * scale * dpr))
        key = (name, w, h)
        pixmap = self._cache.get(key)
        if pixmap is None:
            if len(self._cache) > MAX_CACHED:
                self._cache.clear()
            pixmap = QPixmap.fromImage(image.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
            pixmap.setDevicePixelRatio(dpr)
            self._cache[key] = pixmap
            self._last[name] = pixmap
            self.renders += 1
        return pixmap

    def draw(self, p: QPainter, name: str, at: Placement, dpr: float) -> None:
        """Copia el PNG ya escalado; la esquina va a un px físico entero (copia directa, sin re-muestrear)."""
        image = self.ui.image(name)
        size = QSizeF(image.width() * at.scale, image.height() * at.scale)
        key = (name, max(1, round(size.width() * dpr)), max(1, round(size.height() * dpr)))
        if self.stretching and key not in self._cache and name in self._last:
            last = self._last[name]
            p.save()
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawPixmap(QRectF(at.origin, size), last, QRectF(last.rect()))
            p.restore()
            return
        pixmap = self.pixmap(name, at.scale, dpr)
        p.drawPixmap(QPointF(round(at.origin.x() * dpr) / dpr, round(at.origin.y() * dpr) / dpr), pixmap)


def font(family: str, size: float, weight: int) -> QFont:
    f = QFont(family)
    f.setPixelSize(max(1, round(size)))
    f.setWeight(QFont.Weight(weight))
    return f


def engrave(p: QPainter, rect: QRectF, text: str, f: QFont, alpha: float = 1.0) -> None:
    """Letras grabadas en el latón: oscuras, con un filo de luz debajo (la luz viene de arriba a la izquierda)."""
    p.setFont(f)
    light, dark = QColor(COLORS.engrave_light), QColor(COLORS.engrave)
    light.setAlphaF(0.45 * alpha)
    dark.setAlphaF(alpha)
    p.setPen(light)
    p.drawText(rect.translated(0, 1), Qt.AlignmentFlag.AlignCenter, text)
    p.setPen(dark)
    p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
