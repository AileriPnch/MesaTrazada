"""Fondo cacheado de una pantalla (madera, paño...): una imagen opaca por clave (tamaño, DPR y lo que la
defina). Al redimensionar se estira la versión anterior y se regenera `MOTION.rebuild_ms` después del último
cambio: generar las texturas cuesta y no tiene que frenar el arrastre del borde de la ventana."""
from PyQt6.QtCore import QPointF, QRectF, QTimer
from PyQt6.QtGui import QPainter, QPixmap

from src.common.theme import MOTION


class CachedBackdrop:
    """El fondo de un widget, cacheado por clave: (ancho, alto, dpr, lo que lo defina)."""

    def __init__(self, widget):
        self.widget = widget
        self.key = None
        self.layer: tuple[QPointF, QPixmap] | None = None
        self.builds = 0
        self.timer = QTimer(widget)
        self.timer.setSingleShot(True)
        self.timer.setInterval(MOTION.rebuild_ms)
        self.timer.timeout.connect(widget.update)

    def resized(self) -> None:
        if self.layer is not None:
            self.timer.start()

    def paint(self, p: QPainter, key: tuple, render) -> None:
        """`key` empieza con (ancho, alto, dpr); `render()` genera la capa para la clave actual."""
        width, height, dpr = key[:3]
        if self.layer is None or (key != self.key and not (self.timer.isActive() and dpr == self.key[2])):
            self.layer, self.key = render(), key
            self.builds += 1
        pos, pixmap = self.layer
        p.save()
        p.scale(1 / dpr, 1 / dpr)
        if key == self.key:
            p.drawPixmap(pos, pixmap)
        else:
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawPixmap(QRectF(0, 0, width * dpr, height * dpr), pixmap, QRectF(pixmap.rect()))
        p.restore()
