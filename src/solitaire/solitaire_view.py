"""Mesa de solitario: traduce clics, doble clic y arrastres en acciones; el dibujo va en TablePainter y las
animaciones en TableMotion. Las animaciones nunca hacen esperar: cualquier clic las completa al instante."""
from PyQt6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QSizePolicy, QWidget

from src.common import sound
from src.common.sound import Sound
from src.common.theme import MOTION
from src.solitaire.drag_state import DragState, auto_foundation, card_rect, drop_targets
from src.solitaire.klondike import KlondikeGame, PileKind, PileRef
from src.solitaire.table_animations import (FLIGHT_MS, RETURN_MS, SETTLE_MS, animate_change, animate_deal,
                                            visible_cards)
from src.solitaire.table_layout import TableLayout
from src.solitaire.table_motion import TableMotion
from src.solitaire.table_painter import TablePainter

DRAG_THRESHOLD = 4
DIRTY_MARGIN = 3  # px extra al invalidar, por el redondeo de posiciones
FLIP_DELAY_MS = 130  # la carta que queda destapada se voltea después de apoyar la otra (sonido)


class SolitaireView(QWidget):
    changed = pyqtSignal()  # tras cada robo o movimiento aplicado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 420)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.game: KlondikeGame | None = None
        self.interactive = True
        self.drag: DragState | None = None
        self.painter = TablePainter()
        self.motion = TableMotion(self)
        self.spot: QPointF | None = None  # foco de la mesa (lo fija la pantalla)
        self._resize = QTimer(self)
        self._resize.setSingleShot(True)
        self._resize.setInterval(MOTION.rebuild_ms)
        self._resize.timeout.connect(self.update)

    def set_game(self, game: KlondikeGame | None, animate: bool = True) -> None:
        self.motion.finish()
        self.game, self.drag, self.interactive = game, None, True
        if game is not None and animate:
            animate_deal(self.motion, game, self.layout_())
        self.update()

    def cancel_drag(self) -> None:
        self.motion.finish()
        self.drag = None
        self.update()

    def layout_(self) -> TableLayout:
        return TableLayout.fit(self.width(), self.height())

    # --- mouse ----------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        self.motion.finish()  # el jugador manda: lo que se estaba animando llega ya a su lugar
        if event.button() != Qt.MouseButton.LeftButton or not self.interactive or self.game is None:
            return
        pos = event.position()
        layout = self.layout_()
        hit = layout.hit_test(self.game, pos)
        if hit is None:
            return
        ref, index = hit
        if ref.kind is PileKind.STOCK:
            self._draw()
            return
        cards = self.game.movable_cards(ref, index)
        if cards:
            corner = card_rect(layout, self.game, ref, index).topLeft()
            self.drag = DragState(ref, index, cards, pos - corner, pos, pos)

    def mouseMoveEvent(self, event) -> None:
        drag = self.drag
        if drag is None:
            return
        layout = self.layout_()
        old = drag.bounds(layout)
        drag.pos = event.position()
        if not drag.active:
            if (drag.pos - drag.start).manhattanLength() >= DRAG_THRESHOLD:
                drag.active = True
                drag.targets = drop_targets(self.game, drag.src, drag.index)
                self.update()  # las cartas se levantan y se marcan los destinos: repintado completo una vez
            return
        # Sólo se repinta lo que cambió: dónde estaban las cartas (con su sombra) y dónde están ahora.
        dirty = old.united(drag.bounds(layout)).adjusted(-DIRTY_MARGIN, -DIRTY_MARGIN, DIRTY_MARGIN, DIRTY_MARGIN)
        self.update(dirty.toAlignedRect())

    def mouseReleaseEvent(self, event) -> None:
        drag, self.drag = self.drag, None
        if drag is None or not drag.active:
            return
        layout = self.layout_()
        lifted = {card: (rect, True) for card, rect in zip(drag.cards, drag.card_rects(layout))}
        rect = QRectF(drag.pos - drag.grab, layout.card_size)
        target = layout.drop_target(self.game, drag.src, drag.index, rect)
        if target is None or not self._move(drag.src, drag.index, target, SETTLE_MS, lifted):
            here = visible_cards(self.game, layout)  # sólo las levantadas vuelven a su origen
            animate_change(self.motion, self.game, layout, here, RETURN_MS, lifted)
            self.update()

    def mouseDoubleClickEvent(self, event) -> None:
        self.motion.finish()
        if event.button() != Qt.MouseButton.LeftButton or not self.interactive or self.game is None:
            return
        self.drag = None
        hit = self.layout_().hit_test(self.game, event.position())
        if hit is None:
            return
        if hit[0].kind is PileKind.STOCK:  # Qt reemplaza el 2.º clic por el doble clic: es otro robo
            self._draw()
            return
        target = auto_foundation(self.game, *hit)
        if target is not None:
            self._move(hit[0], hit[1], target, FLIGHT_MS)

    # --- acciones ---------------------------------------------------------------
    def _draw(self) -> None:
        recycling = not self.game.stock
        before = visible_cards(self.game, self.layout_())
        if self.game.draw():
            sound.play(Sound.RECYCLE if recycling else Sound.DRAW_CARD)
            animate_change(self.motion, self.game, self.layout_(), before, FLIGHT_MS)
            self._changed()

    def _move(self, src: PileRef, index: int, dst: PileRef, duration: float = FLIGHT_MS, overrides=None) -> bool:
        hidden = sum(column.hidden for column in self.game.tableau)
        before = visible_cards(self.game, self.layout_())
        if not self.game.move(src, index, dst):
            return False
        sound.play(Sound.FOUNDATION if dst.kind is PileKind.FOUNDATION else Sound.PLACE)
        if sum(column.hidden for column in self.game.tableau) < hidden:
            sound.play_later(Sound.FLIP, FLIP_DELAY_MS)
        animate_change(self.motion, self.game, self.layout_(), before, duration, overrides)
        if self.game.is_won:
            self.motion.celebrate()
        self._changed()
        return True

    def _changed(self) -> None:
        self.update()
        self.changed.emit()

    # --- dibujo ---------------------------------------------------------------
    def resizeEvent(self, event) -> None:
        if self.painter.assets is not None:
            self._resize.start()  # mientras se redimensiona se estiran los sprites; después se regeneran
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        if self.game is None:
            return
        p = QPainter(self)
        dpr = self.devicePixelRatioF()
        layout = self.layout_()
        self.painter.prepare(layout, dpr, self._resize.isActive())
        clip = QRect(event.rect().topLeft() * dpr, event.rect().size() * dpr).adjusted(-2, -2, 2, 2)
        self.painter.paint(p, self.game, layout, self.drag, clip, dpr, self.motion, self.spot)
