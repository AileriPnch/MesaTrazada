"""Fondo de la pantalla del ajedrez: la mesa de nogal renderizada (`mesa.png`), la luz de la lámpara en un
charco alrededor del tablero, la sombra del tablero (hacia abajo a la derecha, lejos de la luz), las sombras y
contactos de los objetos apoyados alrededor (planilla, reloj, placas...: horneados acá, no en cada frame) y
viñeteado.
Una imagen opaca por tamaño y DPR, en píxeles físicos (la cachea CachedBackdrop).

La mesa comparte el centro con el tablero (así la renderizó Blender) y se escala para que su veta tenga la
escala del tablero (`s / 240`) o más, lo justo para cubrir toda la ventana desde ese centro."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap

from src.chess_game import art_library
from src.chess_game.art_library import TABLE_SQUARE
from src.common.glow import blurred, render_layer, to_device
from src.common.textures import paint_light, paint_vignette
from src.common.theme import BOARD_LOOK


def table_scale(table: QImage, width: float, height: float, center: QPointF, square: float) -> float:
    """Escala de la mesa: la de la veta del tablero o la mínima para cubrir la ventana desde `center`."""
    cover_x = 2 * max(center.x(), width - center.x()) / table.width()
    cover_y = 2 * max(center.y(), height - center.y()) / table.height()
    return max(square / TABLE_SQUARE, cover_x, cover_y)


def _paint_table(p: QPainter, table: QImage, width: float, height: float, center: QPointF, square: float,
                 dpr: float) -> None:
    """La mesa escalada (suave) a px físicos y centrada en el tablero."""
    scale = table_scale(table, width, height, center, square) * dpr
    w, h = round(table.width() * scale), round(table.height() * scale)
    scaled = table.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    x, y = round(center.x() * dpr - w / 2), round(center.y() * dpr - h / 2)  # px físicos enteros
    p.drawImage(QRectF(x / dpr, y / dpr, w / dpr, h / dpr), scaled)  # el pintor ya escala por el DPR: 1 a 1


def render_backdrop(width: int, height: int, dpr: float, frame: QRectF, square: float,
                    shadows: list[tuple[QImage, QRectF]] = ()) -> tuple[QPointF, QPixmap]:
    full = QRectF(0, 0, width, height)
    table = art_library.library().table
    center = frame.center() if not frame.isEmpty() else full.center()

    def shadow(q: QPainter) -> None:
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(0, 0, 0))
        q.drawRoundedRect(frame.translated(square * 0.08, square * 0.14), square * 0.06, square * 0.06)

    def draw(p: QPainter) -> None:
        _paint_table(p, table, width, height, center, max(square, 1.0), dpr)
        if not frame.isEmpty():
            paint_light(p, center, frame.width() * BOARD_LOOK.table_light_radius, BOARD_LOOK.table_light)
            p.setOpacity(BOARD_LOOK.shadow)
            p.drawImage(QPointF(0, 0), blurred(width, height, dpr, square * 0.32, shadow))
            p.setOpacity(1.0)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        for image, rect in shadows:  # contacto y sombra de cada objeto, sobre la madera
            p.drawImage(rect, image)
        paint_vignette(p, full, BOARD_LOOK.vignette)

    return to_device(render_layer(full, dpr, draw, opaque=True), dpr)
