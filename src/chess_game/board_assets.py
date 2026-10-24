"""Todo lo que el tablero copia en cada frame, generado una vez por tamaño de casilla y DPR: la imagen del
tablero, los sprites de las piezas (en reposo, levantadas, halo y bloom de la elegida) y las marcas de casillas
legales y de jaque. Se generan a demanda y se guardan; arrastrar una pieza no genera nada nuevo (la versión
levantada se genera al empezar el arrastre, una vez por pieza)."""
from typing import Callable, Hashable

import chess
from PyQt6.QtCore import QPoint, QPointF, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QRadialGradient

from src.chess_game import art_library
from src.chess_game.art_library import ANCHOR_UP
from src.chess_game.board_painter import FORMAT, BoardGeometry, coordinate_labels, render_board
from src.chess_game.piece_sprites import (PieceSprites, Sprite, bloom_sprite, halo_sprite, lifted_sprites,
                                          rest_sprites, toppled_sprites)
from src.common.glow import blur_image
from src.common.theme import BOARD_LOOK, COLORS, NEON


def _alpha(hex_color: str, alpha: float) -> QColor:
    color = QColor(hex_color)
    color.setAlphaF(max(0.0, min(1.0, alpha)))
    return color


def _mark(size: int, draw: Callable[[QPainter, float], None], glow: float = 0.0) -> Sprite:
    """Marca del tamaño de una casilla; con `glow`, primero su versión desenfocada (el resplandor)."""
    def layer() -> QImage:
        image = QImage(size, size, FORMAT)
        image.fill(Qt.GlobalColor.transparent)
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        draw(p, size)
        p.end()
        return image

    image = layer()
    if glow:
        halo = blur_image(layer(), size * glow)
        p = QPainter(halo)
        p.drawImage(0, 0, image)
        p.end()
        image = halo
    return Sprite(QPixmap.fromImage(image), QPoint(0, 0))  # las marcas se ubican por la esquina de la casilla


def _dot(p: QPainter, s: float) -> None:
    center, radius = QPointF(s / 2, s / 2), s * BOARD_LOOK.target_dot
    gradient = QRadialGradient(center, radius)
    gradient.setColorAt(0.0, _alpha(NEON.core, BOARD_LOOK.target_glow))
    gradient.setColorAt(1.0, _alpha(NEON.color, BOARD_LOOK.target_glow * 0.85))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(gradient)
    p.drawEllipse(center, radius, radius)


def _ring(p: QPainter, s: float) -> None:
    p.setPen(QPen(_alpha(NEON.color, BOARD_LOOK.target_glow), s * 0.04))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(s / 2, s / 2), s * 0.42, s * 0.42)


def _check(p: QPainter, s: float) -> None:
    gradient = QRadialGradient(QPointF(s / 2, s / 2), s * 0.62)
    gradient.setColorAt(0.0, _alpha(COLORS.check, 0.85))
    gradient.setColorAt(1.0, _alpha(COLORS.check, 0.0))
    p.fillRect(0, 0, round(s), round(s), gradient)


class BoardAssets:
    """Imagen del tablero + sprites para una geometría, un tamaño de widget y un DPR."""

    def __init__(self, g: BoardGeometry, width: int, height: int, dpr: float):
        self.g, self.size, self.dpr = g, (width, height), dpr
        self.art = art_library.library()
        self.square = round(g.square * dpr)
        self.origin = QPoint(round(g.left * dpr), round(g.top * dpr))
        self.board = QPixmap.fromImage(render_board(g, width, height, dpr, self.art.board))
        self.labels = [(self.cell_origin(sq), QPixmap.fromImage(image)) for sq, image in coordinate_labels(g, dpr)]
        self._items: dict[Hashable, object] = {}
        self.renders = 1

    def matches(self, g: BoardGeometry, width: int, height: int, dpr: float) -> bool:
        return (self.g, self.size, self.dpr) == (g, (width, height), dpr)

    @property
    def board_area(self) -> QRect:
        """Las 8 x 8 casillas (sin el marco): ahí se recortan los reflejos."""
        return QRect(self.origin, QSize(8 * self.square, 8 * self.square))

    def cell_origin(self, sq: chess.Square) -> QPoint:
        col, row = self.g.cell(sq)
        return self.origin + QPoint(col * self.square, row * self.square)

    def anchor(self, sq: chess.Square) -> QPoint:
        """Punto de apoyo de la pieza: centrado y a ANCHOR_UP del lado por encima del borde inferior."""
        return self.cell_origin(sq) + QPoint(self.square // 2, self.square - round(ANCHOR_UP * self.square))

    def _get(self, key: Hashable, make: Callable[[], object]):
        item = self._items.get(key)
        if item is None:
            item = self._items[key] = make()
            self.renders += 1
        return item

    def rest(self, piece: chess.Piece) -> PieceSprites:
        return self._get(("rest", piece), lambda: rest_sprites(self.art, piece, self.square))

    def toppled(self, color: chess.Color) -> PieceSprites:
        return self._get(("toppled", color), lambda: toppled_sprites(self.art, color, self.square))

    def lifted(self, piece: chess.Piece) -> PieceSprites:
        return self._get(("lifted", piece), lambda: lifted_sprites(self.art, piece, self.square))

    def bloom(self, piece: chess.Piece) -> Sprite:
        return self._get(("bloom", piece), lambda: bloom_sprite(self.art, piece, self.square))

    def halo(self, piece: chess.Piece) -> Sprite:
        return self._get(("halo", piece), lambda: halo_sprite(self.art, piece, self.square))

    def dot(self) -> Sprite:
        return self._get("dot", lambda: _mark(self.square, _dot, glow=0.09))

    def ring(self) -> Sprite:
        return self._get("ring", lambda: _mark(self.square, _ring, glow=0.05))

    def check(self) -> Sprite:
        return self._get("check", lambda: _mark(self.square, _check))
