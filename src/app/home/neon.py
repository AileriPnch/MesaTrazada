"""Neón tenue ámbar: línea divisoria, contorno del tablero/abanico, cartel y brillo del nombre de cada juego.

Cada brillo se pre-renderiza con su intensidad final; en el frame sólo se copia con más o menos opacidad.
"""
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QFontMetricsF, QPainter, QPainterPath, QPen

from src.common.glow import Layer, faded_line_pen, glow_layer, neon_color
from src.app.home.home_layout import TEXTS, HomeLayout, Side
from src.common.theme import COLORS, NEON, PLAQUE


def divider(layout: HomeLayout, dpr: float) -> Layer:
    """Línea vertical fina entre las dos mitades, con brillo suave y extremos desvanecidos."""
    top, bottom = layout.divider
    radius = NEON.glow_radius * layout.u
    strip = QRectF(top.x() - radius * 3, top.y(), radius * 6, bottom.y() - top.y())

    def glow(q: QPainter) -> None:
        q.setPen(faded_line_pen(NEON.color, NEON.divider, radius * 0.5, top, bottom))
        q.drawLine(top, bottom)

    def line(p: QPainter) -> None:
        p.setPen(faded_line_pen(NEON.core, 0.75, max(1.0, NEON.line * layout.u), top, bottom))
        p.drawLine(top, bottom)

    return glow_layer(strip, dpr, radius, glow, line)


def outline(path: QPainterPath, half: QRectF, u: float, dpr: float, intensity: float = NEON.outline) -> Layer:
    """Contorno neón de una silueta (tablero, abanico, cartel), para la capa que se enciende con el hover."""
    radius = NEON.glow_radius * u

    def glow(q: QPainter) -> None:
        q.setPen(QPen(neon_color(NEON.color, 0.9), radius * 0.45))
        q.drawPath(path)

    def line(p: QPainter) -> None:
        p.setPen(QPen(neon_color(NEON.core, 0.8), max(1.0, NEON.line * u)))
        p.drawPath(path)

    return glow_layer(half, dpr, radius, glow, line, intensity)


def plaque_path(layout: HomeLayout, side: Side) -> QPainterPath:
    path = QPainterPath()
    radius = PLAQUE.radius * layout.u
    path.addRoundedRect(layout.plaque_rect(side).adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
    return path


def paint_plaque(p: QPainter, layout: HomeLayout, side: Side) -> None:
    """Cartel en reposo (va al fondo): relleno muy oscuro semitransparente y contorno casi apagado."""
    fill = QColor(COLORS.glass)
    fill.setAlphaF(PLAQUE.fill_alpha)
    p.setBrush(fill)
    p.setPen(QPen(neon_color(NEON.color, PLAQUE.rest), max(1.0, NEON.line * layout.u)))
    p.drawPath(plaque_path(layout, side))


def name_path(layout: HomeLayout, side: Side) -> QPainterPath:
    """Nombre del juego como trazo, en el mismo lugar donde `drawText(AlignCenter)` lo escribe."""
    name, rect, font = TEXTS[side][0], layout.name_rect(side), layout.name_font
    metrics = QFontMetricsF(font)
    origin = QPointF(rect.center().x() - metrics.horizontalAdvance(name) / 2,
                     rect.top() + (rect.height() - metrics.height()) / 2 + metrics.ascent())
    path = QPainterPath()
    path.addText(origin, font, name)
    return path


def name_glow(layout: HomeLayout, side: Side, dpr: float) -> Layer:
    """Halo detrás del nombre del juego (a pleno; la opacidad del frame da reposo / hover)."""
    radius = NEON.glow_radius * layout.u * 0.8
    box = layout.name_rect(side).adjusted(-radius * 3, -radius * 2, radius * 3, radius * 2)
    path = name_path(layout, side)

    def glow(q: QPainter) -> None:
        q.setPen(QPen(neon_color(NEON.color, 1.0), max(1.0, 1.2 * layout.u)))  # títulos SemiBold: trazo fino
        q.setBrush(neon_color(NEON.color, 1.0))
        q.drawPath(path)

    return glow_layer(box, dpr, radius, glow)
