"""Capas pre-renderizadas de la pantalla de inicio y su composición por frame.

Todo lo caro (texturas, dibujos, brillos desenfocados) se genera una vez por tamaño y DPR. Un frame del
hover sólo copia pixmaps con opacidad y rellena un rectángulo semitransparente: no dibuja vectores.
"""
from time import perf_counter

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap

from src.app.home import neon
from src.app.home.cards_art import fan_outline, paint_cards
from src.app.home.chess_art import board_pose, paint_chess
from src.common.glow import Layer, render_layer, to_device
from src.app.home.home_layout import APP_NAME, TEXTS, HomeLayout, Side
from src.common.textures import paint_felt, paint_light, paint_top_shade, paint_vignette, paint_wood
from src.app.icon_painter import render_app_icon
from src.common.theme import COLORS, NEON, PLAQUE

BOARD_WIDTH = 0.86  # ancho máximo del borde cercano del tablero, relativo a la mitad


class HomeLayers:
    def __init__(self):
        self.key = None
        self.layout: HomeLayout | None = None
        self.builds = 0  # cantidad de regeneraciones (tests / diagnóstico)
        self.build_ms = 0.0

    def is_current(self, layout: HomeLayout, dpr: float) -> bool:
        return self.key == (layout.width, layout.height, dpr)

    def build(self, layout: HomeLayout, dpr: float) -> None:
        start = perf_counter()
        full = QRectF(0, 0, layout.width, layout.height)
        self.background = render_layer(full, dpr, lambda p: self._paint_table(p, layout, dpr), opaque=True)
        self.lit: dict[Side, Layer] = {}  # luz de lámpara + contorno neón, juntos: una sola mezcla por frame
        self.glow: dict[Side, Layer] = {}
        self.text: dict[Side, Layer] = {}
        for side in Side:
            half, art = layout.half(side), layout.art_rect(side)
            silhouette = board_pose(art, half.width() * BOARD_WIDTH).outline if side is Side.CHESS else fan_outline(art)
            outline = neon.outline(silhouette, half, layout.u, dpr)
            plaque = neon.outline(neon.plaque_path(layout, side), half, layout.u, dpr, PLAQUE.hover)
            radius = max(half.width(), half.height()) * 0.7

            def lit(p: QPainter, center=art.center(), radius=radius, layers=(outline, plaque)) -> None:
                paint_light(p, center, radius, NEON.light)
                for layer in layers:
                    p.drawPixmap(*layer)

            self.lit[side] = render_layer(half, dpr, lit)
            self.glow[side] = neon.name_glow(layout, side, dpr)
            box = layout.name_rect(side).united(layout.detail_rect(side))
            self.text[side] = render_layer(box, dpr, lambda p, s=side: self._paint_texts(p, layout, s))
        self.divider = neon.divider(layout, dpr)
        self.header = render_layer(layout.header_rect, dpr, lambda p: self._paint_header(p, layout, dpr))
        self.background, self.divider, self.header = (to_device(x, dpr) for x in (self.background, self.divider, self.header))
        for layers in (self.lit, self.glow, self.text):
            for side in Side:
                layers[side] = to_device(layers[side], dpr)
        self.halves = {side: QRectF(layout.half(side).topLeft() * dpr, layout.half(side).size() * dpr) for side in Side}
        self.layout = layout
        self.key = (layout.width, layout.height, dpr)
        self.builds += 1
        self.build_ms = (perf_counter() - start) * 1000

    def paint(self, p: QPainter, hover: dict[Side, float]) -> None:
        """Un frame: fondo + por mitad luz/contorno (hover) o atenuado (hover de la otra) + textos.
        Se dibuja en píxeles físicos (ver `to_device`)."""
        dpr = self.key[2]
        p.save()
        p.scale(1 / dpr, 1 / dpr)
        p.drawPixmap(*self.background)  # opaco: copia directa
        for side in Side:
            lit, other = hover[side], hover[side.other]
            if lit > 0:
                p.setOpacity(lit)
                p.drawPixmap(*self.lit[side])
                p.setOpacity(1.0)
            if other > 0:
                p.fillRect(self.halves[side], QColor(0, 0, 0, round(255 * NEON.dim * other)))
            fade = 1.0 - NEON.dim * other
            p.setOpacity((NEON.name_rest + (NEON.name_hover - NEON.name_rest) * lit) * fade)
            p.drawPixmap(*self.glow[side])
            p.setOpacity(fade)
            p.drawPixmap(*self.text[side])
            p.setOpacity(1.0)
        p.drawPixmap(*self.divider)
        p.drawPixmap(*self.header)
        p.restore()

    @staticmethod
    def _paint_table(p: QPainter, layout: HomeLayout, dpr: float) -> None:
        for side, texture in ((Side.CHESS, paint_wood), (Side.SOLITAIRE, paint_felt)):
            half, art = layout.half(side), layout.art_rect(side)
            p.save()
            p.setClipRect(half)
            texture(p, half)
            paint_light(p, art.center(), max(half.width(), half.height()) * 0.62, 0.05)
            if side is Side.CHESS:
                paint_chess(p, board_pose(art, half.width() * BOARD_WIDTH), half, dpr)
            else:
                paint_cards(p, art, half, dpr)
            p.restore()
        full = QRectF(0, 0, layout.width, layout.height)
        paint_vignette(p, full)
        paint_top_shade(p, full, layout.header_bottom * 1.6)
        for side in Side:
            neon.paint_plaque(p, layout, side)

    @staticmethod
    def _paint_texts(p: QPainter, layout: HomeLayout, side: Side) -> None:
        name, detail = TEXTS[side]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(COLORS.text))
        p.drawPath(neon.name_path(layout, side))  # mismo trazo que su brillo: quedan alineados
        p.setFont(layout.detail_font)
        p.setPen(QColor(COLORS.text_muted))
        p.drawText(layout.detail_rect(side), Qt.AlignmentFlag.AlignCenter, detail)

    @staticmethod
    def _paint_header(p: QPainter, layout: HomeLayout, dpr: float) -> None:
        rect, size = layout.header_rect, layout.icon_size
        icon = QPixmap.fromImage(render_app_icon(round(size * dpr)))
        icon.setDevicePixelRatio(dpr)
        p.drawPixmap(QPointF(rect.left(), rect.top()), icon)
        p.setFont(layout.title_font)
        p.setPen(QColor(COLORS.text))
        text = QRectF(rect.left() + size, rect.top(), rect.width() - size, rect.height())
        p.drawText(text, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, APP_NAME)
