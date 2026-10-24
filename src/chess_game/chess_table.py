"""Mesa del ajedrez: el tablero y los objetos apoyados alrededor (bandejas de capturadas, carteles, reloj,
planilla, placas-botón) sobre la mesa de nogal, proporcionales a la ventana (`table_layout`, función pura). Las
sombras de los objetos van horneadas en el fondo cacheado. La perilla de latón del volumen (`volume_skin`) la
toma la ventana mientras esta pantalla está abierta. La lógica de la partida va en ChessScreen."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter

from src.chess_game import art_library
from src.chess_game.board_view import BoardView
from src.chess_game.chess_backdrop import render_backdrop
from src.chess_game.knob_skin import KnobSkin
from src.chess_game.table_layout import TableLayout, table_layout
from src.chess_game.table_side import TableSide
from src.chess_game.table_sprites import UiSprites
from src.common.backdrop import CachedBackdrop
from src.common.game_screen import GameScreen
from src.common.theme import window_scale


class ChessTable(GameScreen):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # paintEvent pinta todo el fondo
        self.u = 1.0
        art = art_library.library()  # todo el arte del ajedrez (precargado al abrir sus opciones en el inicio)
        self.sprites = UiSprites(art.ui)
        self.backdrop = CachedBackdrop(self)
        self.backdrop.timer.timeout.connect(self._resized)
        self.board_view = BoardView(self)
        self.side = TableSide(self, self.sprites, art)
        self.volume_skin = KnobSkin(self.sprites)
        self.table: TableLayout = table_layout(self.width(), self.height(), self.devicePixelRatioF())

    def _place(self) -> None:
        self.u = window_scale(self.width(), self.height())
        self.table = table_layout(self.width(), self.height(), self.devicePixelRatioF())
        self.board_view.setGeometry(self.table.board_view)
        self.side.place(self.table)

    def resizeEvent(self, event) -> None:
        self._place()
        self.backdrop.resized()
        self.sprites.stretching = self.backdrop.timer.isActive()  # mientras se arrastra el borde: estirar
        super().resizeEvent(event)

    def _resized(self) -> None:
        """Terminó de redimensionarse: los objetos se regeneran a su tamaño final (el fondo, en su paintEvent)."""
        self.sprites.stretching = False
        for widget in self.side.objects + [self.side.card]:
            widget.update()

    def paintEvent(self, event) -> None:
        table, dpr = self.table, self.devicePixelRatioF()
        key = (self.width(), self.height(), dpr, table.frame.getRect())
        p = QPainter(self)
        self.backdrop.paint(p, key, lambda: render_backdrop(self.width(), self.height(), dpr, table.frame, table.s,
                                                            self.side.shadow_layers()))
