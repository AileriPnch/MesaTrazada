"""Geometría y tipografía de la pantalla de inicio, proporcionales al tamaño de la ventana."""
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QFont, QFontMetricsF

from src.common import theme
from src.common.app_info import APP_NAME
from src.common.theme import PLAQUE, SPACE

BASE_SIZE = (1000, 720)  # tamaño de referencia: escala u = 1


class Side(Enum):
    CHESS = 0
    SOLITAIRE = 1

    @property
    def other(self) -> "Side":
        return Side.SOLITAIRE if self is Side.CHESS else Side.CHESS


TEXTS = {
    Side.CHESS: ("Ajedrez", "Contra Stockfish · 6 niveles"),
    Side.SOLITAIRE: ("Solitario", "Klondike · robo de a 1 o de a 3"),
}


def font(family: str, size: float, weight: int, tracking: float = 0.0) -> QFont:
    f = QFont(family)
    f.setPixelSize(max(8, round(size)))
    f.setWeight(QFont.Weight(weight))
    if tracking:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, tracking)
    return f


@dataclass(frozen=True)
class HomeLayout:
    width: float
    height: float

    @property
    def u(self) -> float:
        return min(self.width / BASE_SIZE[0], self.height / BASE_SIZE[1])

    # --- encabezado -----------------------------------------------------------------------------
    @cached_property
    def title_font(self) -> QFont:
        t = theme.TYPE  # se lee al usarse: así se pueden comparar variantes (tests, capturas)
        return font(t.title_family, t.title * self.u, t.title_weight, t.title_tracking * self.u)

    @property
    def icon_size(self) -> float:
        return round(40 * self.u)

    @cached_property
    def header_rect(self) -> QRectF:
        """Ícono + nombre de la app, centrados arriba."""
        gap = SPACE.md * self.u
        text_w = QFontMetricsF(self.title_font).horizontalAdvance(APP_NAME) + 2
        w = self.icon_size + gap + text_w
        return QRectF((self.width - w) / 2, SPACE.xl * self.u, w, self.icon_size)

    @property
    def header_bottom(self) -> float:
        return self.header_rect.bottom() + SPACE.lg * self.u

    # --- mitades ----------------------------------------------------------------------------------
    def half(self, side: Side) -> QRectF:
        w = self.width / 2
        return QRectF(0 if side is Side.CHESS else w, 0, w, self.height)

    def side_at(self, point: QPointF) -> Side | None:
        pad = SPACE.lg * self.u
        if self.header_rect.adjusted(-pad, -pad, pad, pad).contains(point):
            return None
        if not (0 <= point.x() < self.width and 0 <= point.y() < self.height):
            return None
        return Side.CHESS if point.x() < self.width / 2 else Side.SOLITAIRE

    @cached_property
    def name_font(self) -> QFont:
        t = theme.TYPE
        return font(t.title_family, t.display * self.u, t.title_weight, t.title_tracking * self.u)

    @cached_property
    def detail_font(self) -> QFont:
        t = theme.TYPE
        return font(t.ui_family, t.body * self.u, t.ui_weight, t.ui_tracking * self.u)

    @cached_property
    def plaque_top(self) -> float:
        return max(self.header_bottom + SPACE.md * self.u, self.height * 0.13)

    def name_rect(self, side: Side) -> QRectF:
        """Caja de línea del nombre: lo más alto de las letras queda a `pad_v` del borde del cartel."""
        half, metrics = self.half(side), QFontMetricsF(self.name_font)
        ink_top = metrics.tightBoundingRect(TEXTS[Side.CHESS][0] + TEXTS[Side.SOLITAIRE][0]).top()  # igual en las dos
        baseline = self.plaque_top + PLAQUE.pad_v * self.u - ink_top
        return QRectF(half.left(), baseline - metrics.ascent(), half.width(), metrics.height())

    def detail_rect(self, side: Side) -> QRectF:
        name = self.name_rect(side)
        h = QFontMetricsF(self.detail_font).height()
        return QRectF(name.left(), name.bottom() + SPACE.xs * self.u, name.width(), h)

    def plaque_rect(self, side: Side) -> QRectF:
        """Cartel del título: ajustado al texto (nombre + detalle) con padding proporcional, centrado en la mitad."""
        name, detail = TEXTS[side]
        names, details = QFontMetricsF(self.name_font), QFontMetricsF(self.detail_font)
        width = max(names.horizontalAdvance(name), details.horizontalAdvance(detail)) + 2 * PLAQUE.pad_h * self.u
        baseline = self.detail_rect(side).top() + details.ascent()
        bottom = baseline + details.descent() * 0.4 + PLAQUE.pad_v * self.u
        left = round(self.half(side).center().x() - width / 2)  # en píxeles enteros: contorno de 1 px nítido
        return QRectF(left, round(self.plaque_top), round(width), round(bottom - self.plaque_top))

    def art_rect(self, side: Side) -> QRectF:
        """Zona del tablero o de las cartas (y de las opciones cuando se abren)."""
        half = self.half(side)
        top = self.plaque_rect(side).bottom() + SPACE.xl * self.u
        inset = max(SPACE.xl * self.u, half.width() * 0.07)
        return QRectF(half.left() + inset, top, half.width() - 2 * inset, self.height - top - SPACE.xxl * self.u)

    @property
    def divider(self) -> tuple[QPointF, QPointF]:
        x = self.width / 2
        return QPointF(x, self.header_bottom), QPointF(x, self.height - SPACE.xl * self.u)

    def panel_rect(self, side: Side, height: float, width: float) -> QRectF:
        """Panel de opciones centrado en la zona del dibujo (sin salirse de la mitad)."""
        art, half = self.art_rect(side), self.half(side)
        top = max(art.top(), min(art.center().y() - height / 2, half.bottom() - height - SPACE.lg * self.u))
        return QRectF(art.center().x() - width / 2, top, width, height)

    def panel_width(self, side: Side) -> float:
        half = self.half(side)
        return min(half.width() - 2 * SPACE.xl * self.u, 400 * self.u)
