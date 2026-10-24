"""Todo lo que la mesa copia en cada frame, en píxeles físicos y por tamaño de carta + DPR: frentes y dorso con
su sombra (en reposo y levantados), el foil del dorso, los lugares vacíos hundidos en el paño, el resplandor
de los destinos válidos y la luz de la victoria. Se generan a demanda; arrastrar no genera nada nuevo."""
from math import ceil
from typing import Callable, Hashable

from PyQt6.QtCore import QPoint, QRectF, QSize
from PyQt6.QtGui import QColor, QPainter, QPixmap

from src.common.glow import blur_image
from src.common.theme import CARD_LOOK
from src.solitaire.card_assets_base import Sprite, canvas, painter
from src.solitaire.card_back import draw_back_foil, draw_card_back
from src.solitaire.card_painter import card_shape, draw_card_face
from src.solitaire.cards import Card, Suit
from src.solitaire.table_marks import bloom, glow, recess


def _card_sprite(draw: Callable[[QPainter, QRectF], None], w: int, h: int, lifted: bool) -> Sprite:
    """La carta con su sombra: de contacto (en reposo) y proyectada hacia abajo a la derecha, lejos de la luz.
    Levantada: un poco más grande, sombra más lejos y más difusa."""
    look = CARD_LOOK
    scale = look.lift_scale if lifted else 1.0
    cw, ch = round(w * scale), round(h * scale)
    pad = ceil(cw * 0.2)
    image = canvas(cw + 2 * pad, ch + 2 * pad)
    shadows = [(look.lift_shadow_dx, look.lift_shadow_dy, look.lift_shadow_blur, look.lift_shadow_alpha)] if lifted else \
        [(look.shadow_dx, look.shadow_dy, look.shadow_blur, look.shadow_alpha), (0.003, 0.006, 0.01, look.contact_alpha)]
    p = painter(image)
    for dx, dy, blur, alpha in shadows:
        mask = canvas(image.width(), image.height())
        q = painter(mask)
        q.fillPath(card_shape(QRectF(pad + dx * cw, pad + dy * cw, cw, ch)), QColor(0, 0, 0))
        q.end()
        p.setOpacity(alpha)
        p.drawImage(0, 0, blur_image(mask, blur * cw))
    p.setOpacity(1.0)
    draw(p, QRectF(pad, pad, cw, ch))
    p.end()
    return Sprite(QPixmap.fromImage(image), QPoint(-pad, -pad), QSize(cw, ch))


def _plain(draw: Callable[[QPainter, QRectF], None], w: int, h: int) -> Sprite:
    image = canvas(w, h)
    p = painter(image)
    draw(p, QRectF(0, 0, w, h))
    p.end()
    return Sprite(QPixmap.fromImage(image), QPoint(0, 0), QSize(w, h))


class CardAssets:
    """Sprites de una medida de carta (px físicos enteros) y un DPR."""

    def __init__(self, w: int, h: int, dpr: float):
        self.w, self.h, self.dpr = w, h, dpr
        self._items: dict[Hashable, Sprite] = {}
        self.renders = 0

    def matches(self, w: int, h: int, dpr: float) -> bool:
        return (self.w, self.h, self.dpr) == (w, h, dpr)

    def _get(self, key: Hashable, make: Callable[[], Sprite]) -> Sprite:
        sprite = self._items.get(key)
        if sprite is None:
            sprite = self._items[key] = make()
            self.renders += 1
        return sprite

    def face(self, card: Card, lifted: bool = False) -> Sprite:
        return self._get(("face", card, lifted),
                         lambda: _card_sprite(lambda p, r: draw_card_face(p, r, card), self.w, self.h, lifted))

    def back(self) -> Sprite:
        return self._get("back", lambda: _card_sprite(draw_card_back, self.w, self.h, False))

    def foil(self) -> Sprite:
        return self._get("foil", lambda: _plain(draw_back_foil, self.w, self.h))

    def slot(self, symbol: Suit | str | None) -> Sprite:
        return self._get(("slot", symbol), lambda: recess(self.w, self.h, symbol))

    def glow(self) -> Sprite:
        return self._get("glow", lambda: glow(self.w, self.h))

    def bloom(self) -> Sprite:
        return self._get("bloom", lambda: bloom(self.w))

    def __len__(self) -> int:
        return len(self._items)
