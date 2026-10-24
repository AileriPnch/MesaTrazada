"""Sprites de las piezas desde los renders de Blender, escalados una vez por tamaño de casilla (px físicos).

En reposo, tres capas por pieza: suelo (contacto + sombra: negro sobre negro, el orden entre piezas no cambia
el resultado), reflejo y cuerpo (pieza + brillo). Levantada (arrastre): más grande, sin contacto, la sombra
lejos y difusa y el reflejo separado. Elegida: halo ámbar tenue de la silueta (debajo de la pieza: en las
blancas el bloom del brillo casi no se ve) y bloom ámbar del brillo (encima). Cada offset es la esquina del
sprite respecto del punto de apoyo de la pieza (centro de la base)."""
from dataclasses import dataclass
from math import ceil
from typing import Callable

import chess
from PyQt6.QtCore import QPoint, QPointF, QRect, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap

from src.chess_game.art_library import ANCHOR, FORMAT, REFLECTION_ANCHOR, SPRITE_SQUARE, ArtLibrary
from src.common.glow import blur_image
from src.common.raster import tint
from src.common.theme import BOARD_LOOK, NEON, PIECE_LOOK


@dataclass(frozen=True)
class Sprite:
    pixmap: QPixmap
    offset: QPoint  # esquina del sprite respecto del punto de apoyo (px físicos)

    def rect(self, anchor: QPoint) -> QRect:
        return QRect(anchor + self.offset, self.pixmap.size())


@dataclass(frozen=True)
class PieceSprites:
    ground: Sprite  # contacto + sombra (levantada: sólo la sombra, lejos)
    reflection: Sprite
    body: Sprite  # pieza + brillo

    def rect(self, anchor: QPoint) -> QRect:
        return self.ground.rect(anchor).united(self.reflection.rect(anchor)).united(self.body.rect(anchor))


def _canvas(width: int, height: int) -> QImage:
    image = QImage(width, height, FORMAT)
    image.fill(Qt.GlobalColor.transparent)
    return image


def _over(*layers: QImage) -> QImage:
    image = _canvas(layers[0].width(), layers[0].height())
    p = QPainter(image)
    for layer in layers:
        p.drawImage(0, 0, layer)
    p.end()
    return image


def _amplified(image: QImage, factor: float) -> QImage:
    """Alfa (y color, premultiplicado) por `factor`. Arriba de 1 se suma la imagen a sí misma (modo Plus):
    exacto hasta saturar."""
    result = _canvas(image.width(), image.height())
    p = QPainter(result)
    p.setOpacity(min(1.0, factor))
    p.drawImage(0, 0, image)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
    extra = factor - 1.0
    while extra > 0:
        p.setOpacity(min(1.0, extra))
        p.drawImage(0, 0, image)
        extra -= 1.0
    p.end()
    return result


def _scaled(image: QImage, scale: float, anchor: QPointF) -> tuple[QImage, QPoint]:
    """La imagen escalada (suave) y la esquina respecto del apoyo, ya en px físicos enteros."""
    w, h = max(1, round(image.width() * scale)), max(1, round(image.height() * scale))
    sx, sy = w / image.width(), h / image.height()
    scaled = image.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return scaled, QPoint(-round(anchor.x() * sx), -round(anchor.y() * sy))


def _blurred(image: QImage, radius: float) -> tuple[QImage, int]:
    """Desenfocada con margen para que la caída no se corte en el borde; devuelve el margen agregado."""
    pad = ceil(radius * 2)
    canvas = _canvas(image.width() + 2 * pad, image.height() + 2 * pad)
    p = QPainter(canvas)
    p.drawImage(pad, pad, image)
    p.end()
    return blur_image(canvas, radius), pad


def _sprite(image: QImage, offset: QPoint) -> Sprite:
    return Sprite(QPixmap.fromImage(image), offset)


def _resting(layer: Callable[[str], QImage], square: int) -> PieceSprites:
    scale = square * BOARD_LOOK.piece_scale / SPRITE_SQUARE
    ground = _scaled(_over(layer("sombra"), layer("contacto")), scale, ANCHOR)
    reflection = _scaled(_amplified(layer("reflejo"), BOARD_LOOK.reflection), scale, REFLECTION_ANCHOR)
    body = _scaled(_over(layer(""), layer("brillo")), scale, ANCHOR)
    return PieceSprites(_sprite(*ground), _sprite(*reflection), _sprite(*body))


def rest_sprites(art: ArtLibrary, piece: chess.Piece, square: int) -> PieceSprites:
    return _resting(lambda layer: art.layer(piece, layer), square)


def toppled_sprites(art: ArtLibrary, color: chess.Color, square: int) -> PieceSprites:
    """El rey acostado (jaque mate): mismo encuadre, apoyo y pases que las piezas."""
    return _resting(lambda layer: art.toppled(color, layer), square)


def lifted_sprites(art: ArtLibrary, piece: chess.Piece, square: int) -> PieceSprites:
    """Levantada: ×lift_scale (re-escalada desde el render: nítida), sin contacto, la sombra corrida (lejos de
    la luz), difusa y más clara; el reflejo separado de la base y apagado."""
    look = PIECE_LOOK
    scale = square * BOARD_LOOK.piece_scale * look.lift_scale / SPRITE_SQUARE
    shadow, offset = _scaled(_amplified(art.layer(piece, "sombra"), look.lift_shadow_alpha), scale, ANCHOR)
    shadow, pad = _blurred(shadow, look.lift_shadow_blur * square)
    shift = QPoint(round(look.lift_shadow_dx * square), round(look.lift_shadow_dy * square))
    ground = _sprite(shadow, offset + shift - QPoint(pad, pad))
    alpha = BOARD_LOOK.reflection * look.lift_reflection
    reflection, offset = _scaled(_amplified(art.layer(piece, "reflejo"), alpha), scale, REFLECTION_ANCHOR)
    gap = QPoint(0, round(look.lift_reflection_gap * square))
    body = _scaled(_over(art.layer(piece), art.layer(piece, "brillo")), scale, ANCHOR)
    return PieceSprites(ground, _sprite(reflection, offset + gap), _sprite(*body))


def bloom_sprite(art: ArtLibrary, piece: chess.Piece, square: int) -> Sprite:
    """Bloom ámbar del brillo de la pieza elegida: se suma (modo Plus) sobre la pieza."""
    shine, offset = _scaled(art.layer(piece, "brillo"), square * BOARD_LOOK.piece_scale / SPRITE_SQUARE, ANCHOR)
    glow, pad = _blurred(tint(shine, QColor(NEON.color)), BOARD_LOOK.bloom_blur * square)
    return _sprite(_amplified(glow, BOARD_LOOK.bloom), offset - QPoint(pad, pad))


def halo_sprite(art: ArtLibrary, piece: chess.Piece, square: int) -> Sprite:
    """Resplandor ámbar tenue alrededor de la silueta de la pieza elegida: se dibuja debajo de la pieza."""
    body, offset = _scaled(art.layer(piece), square * BOARD_LOOK.piece_scale / SPRITE_SQUARE, ANCHOR)
    glow, pad = _blurred(tint(body, QColor(NEON.color)), BOARD_LOOK.halo_blur * square)
    return _sprite(_amplified(glow, BOARD_LOOK.halo), offset - QPoint(pad, pad))
