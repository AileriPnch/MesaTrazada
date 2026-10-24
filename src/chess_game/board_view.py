"""Widget del tablero: dibuja la partida y traduce clic-clic y arrastrar-soltar en jugadas.

El frame sólo copia pixmaps pre-renderizados (`BoardAssets`) en píxeles físicos; al arrastrar se repinta
únicamente donde estaba y donde está la pieza levantada. Al redimensionar se estira la última versión y se
regenera `MOTION.rebuild_ms` después del último cambio."""
import chess
from PyQt6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QTransform
from PyQt6.QtWidgets import QSizePolicy, QWidget

from src.chess_game.board_assets import BoardAssets
from src.chess_game.board_painter import BoardGeometry
from src.chess_game.board_scene import lifted_rect, paint_position
from src.chess_game.game_state import ChessGame
from src.common.theme import MOTION

DRAG_THRESHOLD = 4  # px antes de considerar que el clic es un arrastre


class BoardView(QWidget):
    move_attempted = pyqtSignal(int, int)  # desde, hasta

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.game: ChessGame | None = None
        self.flipped = False
        self.interactive = False
        self.selected: chess.Square | None = None
        self.toppled: chess.Square | None = None  # rey vencido por jaque mate: acostado
        self._press_pos: QPointF | None = None
        self._drag_pos: QPointF | None = None
        self.assets: BoardAssets | None = None
        self.renders = 0  # pixmaps generados (tests / diagnóstico)
        self._rebuild = QTimer(self)
        self._rebuild.setSingleShot(True)
        self._rebuild.setInterval(MOTION.rebuild_ms)
        self._rebuild.timeout.connect(self.update)

    # --- estado -------------------------------------------------------------
    def set_game(self, game: ChessGame | None, flipped: bool) -> None:
        self.game, self.flipped = game, flipped
        self.toppled = None
        self.clear_selection()

    def set_toppled(self, square: chess.Square | None) -> None:
        self.toppled = square
        self.update()

    def set_interactive(self, interactive: bool) -> None:
        self.interactive = interactive
        if not interactive:
            self.clear_selection()
        self.update()

    def clear_selection(self) -> None:
        self.selected = None
        self._press_pos = self._drag_pos = None
        self.update()

    def geometry_(self) -> BoardGeometry:
        return BoardGeometry.fit(self.width(), self.height(), self.flipped, self.devicePixelRatioF())

    def _targets(self) -> set[chess.Square]:
        if self.game is None or self.selected is None:
            return set()
        return self.game.legal_targets(self.selected)

    def _is_own_piece(self, sq: chess.Square | None) -> bool:
        if sq is None or self.game is None:
            return False
        piece = self.game.board.piece_at(sq)
        return piece is not None and piece.color == self.game.player_color

    # --- mouse --------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self.interactive or self.game is None:
            return
        pos = event.position()
        sq = self.geometry_().square_at(pos)
        if self.selected is not None and sq in self._targets():
            origin = self.selected
            self.clear_selection()
            self.move_attempted.emit(origin, sq)
            return
        if self._is_own_piece(sq):
            self.selected = sq
            self._press_pos = pos
        else:
            self.selected = None
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._press_pos is None or self.selected is None:
            return
        pos = event.position()
        if self._drag_pos is None:
            if (pos - self._press_pos).manhattanLength() >= DRAG_THRESHOLD:
                self._drag_pos = pos
                self.update()  # empieza el arrastre: la pieza se levanta
            return
        old = self._drag_rect()
        self._drag_pos = pos
        # Sólo se repinta donde estaba y donde está la pieza levantada (con su sombra y su reflejo).
        self.update(old.united(self._drag_rect()).adjusted(-2, -2, 2, 2).toAlignedRect())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._press_pos is None:
            return
        was_dragging = self._drag_pos is not None
        self._press_pos = self._drag_pos = None
        if not was_dragging or self.selected is None:
            self.update()  # clic simple: la pieza queda seleccionada para clic-clic
            return
        target = self.geometry_().square_at(event.position())
        origin = self.selected
        if target is not None and target in self._targets():
            self.clear_selection()
            self.move_attempted.emit(origin, target)
        elif target != origin:
            self.clear_selection()  # suelta inválida: la pieza vuelve a su casilla
        else:
            self.update()

    def resizeEvent(self, event) -> None:
        if self.assets is not None:
            self._rebuild.start()  # se regenera al terminar de redimensionar
        super().resizeEvent(event)

    # --- dibujo -------------------------------------------------------------
    def _drag_center(self) -> QPointF | None:
        if self._drag_pos is None:
            return None
        return self._drag_pos * self.devicePixelRatioF()

    def _drag_rect(self) -> QRectF:
        """Rectángulo (lógico) de la pieza levantada, con su sombra y su reflejo."""
        assets, dpr = self._current_assets(), self.devicePixelRatioF()
        rect = lifted_rect(assets, self.game.board.piece_at(self.selected), self._drag_center())
        return QRectF(rect.x() / dpr, rect.y() / dpr, rect.width() / dpr, rect.height() / dpr)

    def _current_assets(self) -> BoardAssets:
        """Los pixmaps de la geometría actual. Mientras se redimensiona (mismo DPR y orientación) se sigue
        usando la versión anterior, estirada; si no, se regeneran ya."""
        g, dpr = self.geometry_(), self.devicePixelRatioF()
        assets = self.assets
        if assets is not None and assets.matches(g, self.width(), self.height(), dpr):
            return assets
        if assets is not None and self._rebuild.isActive() and assets.dpr == dpr and assets.g.flipped == g.flipped:
            return assets
        self.renders += assets.renders if assets is not None else 0
        self.assets = BoardAssets(g, self.width(), self.height(), dpr)
        return self.assets

    @property
    def total_renders(self) -> int:
        """Pixmaps generados desde que existe la vista (tablero + sprites)."""
        return self.renders + (self.assets.renders if self.assets is not None else 0)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        dpr = self.devicePixelRatioF()
        assets, g = self._current_assets(), self.geometry_()
        p.scale(1 / dpr, 1 / dpr)
        if not assets.matches(g, self.width(), self.height(), dpr):  # redimensionando: la anterior, estirada
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            scale = round(g.square * dpr) / assets.square
            stretch = QTransform.fromTranslate(round(g.left * dpr), round(g.top * dpr)).scale(scale, scale)
            p.setTransform(stretch.translate(-assets.origin.x(), -assets.origin.y()) * p.transform())
        p.drawPixmap(0, 0, assets.board)
        if self.game is not None:
            clip = QRect(event.rect().topLeft() * dpr, event.rect().size() * dpr)
            paint_position(p, assets, self.game, self.selected, self._targets(), self._drag_center(), clip,
                           self.toppled)
