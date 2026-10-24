"""Caché de pixmaps pre-renderizados (cartas, piezas) para no redibujar vectores en cada frame."""
from typing import Callable, Hashable

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPixmap

Renderer = Callable[[QPainter, QRectF], None]


class PixmapCache:
    """Guarda un pixmap por (clave, tamaño). Se vacía cuando cambia la escala (tamaño base o DPR),
    así no crece sin límite al redimensionar la ventana."""

    def __init__(self):
        self._scale: Hashable = None
        self._items: dict[Hashable, QPixmap] = {}
        self.renders = 0  # cantidad de pixmaps generados (para tests/diagnóstico)

    def set_scale(self, scale: Hashable) -> None:
        if scale != self._scale:
            self._scale = scale
            self._items.clear()

    def get(self, key: Hashable, width: int, height: int, dpr: float, render: Renderer) -> QPixmap:
        full_key = (key, width, height, dpr)
        pixmap = self._items.get(full_key)
        if pixmap is None:
            pixmap = QPixmap(max(1, round(width * dpr)), max(1, round(height * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            render(painter, QRectF(0, 0, width, height))
            painter.end()
            self._items[full_key] = pixmap
            self.renders += 1
        return pixmap

    def __len__(self) -> int:
        return len(self._items)
