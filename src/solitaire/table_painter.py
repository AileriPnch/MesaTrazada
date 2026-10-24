"""Un frame de la mesa: sólo copia sprites ya renderizados (`CardAssets`), en píxeles físicos y recortado a la
región sucia. Orden: lugares hundidos, mazo, descarte, fundaciones, columnas (cada carta proyecta su sombra
sobre la de abajo), destinos válidos, cartas en vuelo, cartas levantadas y la luz de la victoria."""
from math import pi, sin

from PyQt6.QtCore import QPoint, QPointF, QRect, QRectF
from PyQt6.QtGui import QPainter

from src.solitaire.card_assets import CardAssets
from src.solitaire.card_assets_base import Sprite
from src.solitaire.cards import Card
from src.solitaire.drag_state import DragState
from src.solitaire.klondike import FOUNDATIONS, TABLEAU_COLUMNS, KlondikeGame, PileKind, PileRef
from src.solitaire.table_layout import TableLayout, foundation_labels

class TablePainter:
    def __init__(self):
        self.assets: CardAssets | None = None
        self.old_renders = 0

    @property
    def renders(self) -> int:
        return self.old_renders + (self.assets.renders if self.assets is not None else 0)

    def prepare(self, layout: TableLayout, dpr: float, resizing: bool) -> None:
        w, h = round(layout.card_w * dpr), round(layout.card_h * dpr)
        a = self.assets
        if a is None or (not a.matches(w, h, dpr) and not (resizing and a.dpr == dpr)):
            self.old_renders += a.renders if a is not None else 0
            self.assets = CardAssets(w, h, dpr)

    def _put(self, p: QPainter, sprite: Sprite, rect: QRectF, opacity: float = 1.0, xscale: float = 1.0) -> None:
        """Sprite cuya carta va en `rect` (lógico). Si los sprites son de otro tamaño (redimensionando) o la carta
        gira (`xscale`), se estiran; si no, copia directa en píxeles enteros."""
        dpr = self._dpr
        s = rect.width() * dpr / sprite.size.width()
        exact = abs(rect.width() * dpr - sprite.size.width()) < 1.5 and abs(rect.height() * dpr - sprite.size.height()) < 1.5
        if exact and xscale == 1.0:
            corner = QPoint(round(rect.x() * dpr), round(rect.y() * dpr)) + sprite.offset
            if not self._clip.intersects(QRect(corner, sprite.pixmap.size())):
                return
            p.setOpacity(opacity)
            p.drawPixmap(corner, sprite.pixmap)
        else:
            cx = rect.center().x() * dpr
            w, h = sprite.pixmap.width() * s * xscale, sprite.pixmap.height() * s
            target = QRectF(cx + (sprite.offset.x() - sprite.size.width() / 2) * s * xscale,
                            rect.y() * dpr + sprite.offset.y() * s, w, h)
            if not self._clip.intersects(target.toAlignedRect()):
                return
            p.setOpacity(opacity)
            p.drawPixmap(target, sprite.pixmap, QRectF(sprite.pixmap.rect()))
        p.setOpacity(1.0)

    def _card(self, p: QPainter, rect: QRectF, card: Card | None, face_up: bool, xscale: float = 1.0) -> None:
        if face_up and card is not None:
            self._put(p, self.assets.face(card), rect, xscale=xscale)
            return
        self._put(p, self.assets.back(), rect, xscale=xscale)
        self._put(p, self.assets.foil(), rect, self._foil(rect), xscale)

    def _foil(self, rect: QRectF) -> float:
        """El brillo del dorso depende de cuánto le llega el foco cenital."""
        d = rect.center() - self._spot
        distance = (d.x() ** 2 + d.y() ** 2) ** 0.5
        return max(0.2, 1.0 - distance / self._reach)

    def paint(self, p: QPainter, game: KlondikeGame, layout: TableLayout, drag: DragState | None,
              clip: QRect, dpr: float, motion=None, spot: QPointF | None = None) -> None:
        self._clip, self._dpr = clip, dpr
        self._spot = spot if spot is not None else QPointF(layout.left + 3.5 * layout.card_w, layout.top)
        self._reach = layout.card_w * 9
        now = motion.now() if motion is not None else 0.0
        covered = motion.covers if motion is not None else (lambda card: False)
        dragged = drag.is_dragged if drag is not None else (lambda ref, index: False)
        a = self.assets
        p.save()
        p.scale(1 / dpr, 1 / dpr)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        stock = PileRef(PileKind.STOCK)
        stock_rect = layout.slot_rect(stock)
        self._put(p, a.slot("recycle" if not game.stock and game.waste else None), stock_rect)
        self._put(p, a.slot(None), layout.slot_rect(PileRef(PileKind.WASTE)))
        for i, label in enumerate(foundation_labels(game)):
            self._put(p, a.slot(label), layout.slot_rect(PileRef(PileKind.FOUNDATION, i)))
        for col in range(TABLEAU_COLUMNS):
            self._put(p, a.slot("K"), layout.slot_rect(PileRef(PileKind.TABLEAU, col)))

        if game.stock:  # el mazo tiene espesor: hasta 3 cantos asomando abajo a la derecha
            thick = max(1.0, layout.card_w * 0.012)
            layers = min(3, 1 + len(game.stock) // 8)
            for k in reversed(range(layers)):
                self._card(p, stock_rect.translated(k * thick, k * thick), None, False)
        waste = PileRef(PileKind.WASTE)
        for index, rect in layout.waste_rects(game):
            card = game.waste[index]
            if not dragged(waste, index) and not covered(card):
                self._card(p, rect, card, True)
        for i in range(FOUNDATIONS):
            ref, pile = PileRef(PileKind.FOUNDATION, i), game.foundations[i]
            for index in range(len(pile) - 1, -1, -1):  # la de arriba que no esté en vuelo ni levantada
                if not covered(pile[index]) and not dragged(ref, index):
                    self._card(p, layout.slot_rect(ref), pile[index], True)
                    break
        for col in range(TABLEAU_COLUMNS):
            ref, column = PileRef(PileKind.TABLEAU, col), game.tableau[col]
            for index, rect in enumerate(layout.column_rects(game, col)):
                if dragged(ref, index):
                    break
                if not covered(column.cards[index]):
                    self._card(p, rect, column.cards[index], column.is_face_up(index))

        if drag is not None and drag.active:
            for ref in drag.targets:
                self._put(p, a.glow(), layout.top_rect(game, ref))
        if motion is not None:
            for card, rect, face_up, xscale in motion.frames(now):
                self._card(p, rect, card, face_up, xscale)
        if drag is not None and drag.active:
            for card, rect in zip(drag.cards, drag.card_rects(layout)):
                self._put(p, a.face(card, lifted=True), rect)
        level = motion.celebration_level(now) if motion is not None else None
        if level is not None:
            self._celebrate(p, layout, level)
        p.restore()

    def _celebrate(self, p: QPainter, layout: TableLayout, level: float) -> None:
        """Victoria: una luz ámbar cálida crece sobre las fundaciones y cada rey se enciende, uno tras otro."""
        bloom = self.assets.bloom()
        first = layout.slot_rect(PileRef(PileKind.FOUNDATION, 0))
        last = layout.slot_rect(PileRef(PileKind.FOUNDATION, FOUNDATIONS - 1))
        center = first.united(last).center() * self._dpr
        p.setOpacity(sin(pi * level) * 0.8)
        p.drawPixmap(QPoint(round(center.x()), round(center.y())) + bloom.offset, bloom.pixmap)
        for i in range(FOUNDATIONS):
            t = min(1.0, max(0.0, (level - i * 0.08) / 0.7))
            if t > 0:
                self._put(p, self.assets.glow(), layout.slot_rect(PileRef(PileKind.FOUNDATION, i)), sin(pi * t))
        p.setOpacity(1.0)
