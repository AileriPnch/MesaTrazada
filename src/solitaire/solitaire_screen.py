"""Pantalla de solitario: barra superior y mesa sobre el paño. El modo de robo inicial se elige en la pantalla
de inicio."""
import logging

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QKeySequence, QPainter, QShortcut
from PyQt6.QtWidgets import QVBoxLayout

from src.common import sound
from src.common.backdrop import CachedBackdrop
from src.common.game_screen import GameScreen
from src.common.sound import Sound
from src.common.theme import CORNER, px, window_scale
from src.solitaire import dialogs
from src.solitaire.felt_backdrop import render_felt
from src.solitaire.klondike import KlondikeGame
from src.solitaire.solitaire_bar import SolitaireBar
from src.solitaire.solitaire_style import solitaire_qss
from src.solitaire.solitaire_view import SolitaireView
from src.solitaire.stuck_detector import board_key
from src.solitaire.stuck_watcher import StuckWatcher

logger = logging.getLogger(__name__)

WIN_DELAY_MS = 300  # el sonido de victoria llega después del de la última carta


class SolitaireScreen(GameScreen):
    title = "Solitario"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # paintEvent pinta todo el paño
        self.confirm = dialogs.ask_confirmation  # reemplazable en tests
        self.game: KlondikeGame | None = None
        self.victory_box: dialogs.ChoiceDialog | None = None
        self.stuck_box: dialogs.ChoiceDialog | None = None
        self._dismissed_key = None  # tras "Seguir mirando" no se repite el aviso para esta posición
        self.backdrop = CachedBackdrop(self)

        self.view = SolitaireView()
        self.watcher = StuckWatcher(self, is_busy=lambda: self.view.drag is not None)
        self.bar = SolitaireBar(self)  # modo de robo, estado, Deshacer, Nueva partida, Volver
        self.mode_group, self.mode_buttons, self.status = self.bar.mode_group, self.bar.mode_buttons, self.bar.status
        self.undo_button = self.bar.undo_button
        self.bar.undo_button.clicked.connect(self.undo)
        self.bar.new_game_button.clicked.connect(self.new_game)
        self.bar.back_button.clicked.connect(self.back_requested.emit)
        self._column = QVBoxLayout(self)
        self._column.addLayout(self.bar.layout)
        self._column.addWidget(self.view, 1)
        QShortcut(QKeySequence(QKeySequence.StandardKey.Undo), self, activated=self.undo)
        self.u = None
        self._apply_scale(1.0)

        self.mode_group.idClicked.connect(self._on_mode_clicked)
        self.view.changed.connect(self._after_change)
        self.watcher.stuck.connect(self._on_stuck)

    def _apply_scale(self, u: float) -> None:
        """Todo proporcional a la ventana; la barra arranca a la altura del parlante y le deja su esquina."""
        if u == self.u:
            return
        self.u = u
        self.setStyleSheet(solitaire_qss(u))
        inset = px(CORNER.inset, u)
        self._column.setContentsMargins(inset, inset, inset, inset)
        self.bar.apply_scale(u)
        self._column.invalidate()

    def resizeEvent(self, event) -> None:
        self._apply_scale(window_scale(self.width(), self.height()))
        self.backdrop.resized()
        super().resizeEvent(event)

    def _spot(self) -> QPointF:
        """Foco cenital: sobre el centro de la mesa (un poco arriba, donde están las columnas)."""
        corner = self.view.mapTo(self, QPoint(0, 0))
        return QPointF(corner.x() + self.view.width() / 2, corner.y() + self.view.height() * 0.4)

    def paintEvent(self, event) -> None:
        spot, dpr = self._spot(), self.devicePixelRatioF()
        self.view.spot = spot - QPointF(self.view.mapTo(self, QPoint(0, 0)))
        bar_bottom = self.view.mapTo(self, QPoint(0, 0)).y()
        key = (self.width(), self.height(), dpr, round(spot.x()), round(spot.y()), bar_bottom)
        p = QPainter(self)
        self.backdrop.paint(p, key, lambda: render_felt(self.width(), self.height(), dpr, spot, bar_bottom))

    # --- partida ----------------------------------------------------------------
    def deal(self, draw_count: int) -> None:
        sound.play(Sound.DEAL)
        self.game = KlondikeGame(draw_count)
        self._dismissed_key = None
        self.view.set_game(self.game)
        self.mode_buttons[draw_count].setChecked(True)
        logger.info("Solitario repartido (robo de a %s)", draw_count)
        self._after_change()

    def new_game(self) -> None:
        self.deal(self.game.draw_count if self.game else 1)

    def undo(self) -> None:
        if self.game is None or self.game.is_won or not self.game.undo():
            return
        self.view.cancel_drag()
        self._after_change()

    @property
    def in_progress(self) -> bool:
        return self.game is not None and self.game.actions > 0 and not self.game.is_won

    def _on_mode_clicked(self, draw_count: int) -> None:
        if self.game is None or draw_count == self.game.draw_count:
            return
        text = "Cambiar el modo de robo empieza una partida nueva.\n¿Abandonar la partida en curso?"
        if self.in_progress and not self.confirm(self, text):
            self.mode_buttons[self.game.draw_count].setChecked(True)  # se mantiene el modo actual
            return
        self.deal(draw_count)

    def shutdown(self) -> None:
        self.watcher.cancel()
        self.view.motion.finish()

    def _after_change(self) -> None:
        """Tras repartir, cada acción y cada deshacer: estado, botones, victoria y traba."""
        game = self.game
        self.watcher.cancel()  # la búsqueda en curso era sobre el estado anterior
        self.view.update()
        self.undo_button.setEnabled(game.can_undo and not game.is_won)
        if game.is_won:
            self.status.setText("¡Ganaste!")
            self.view.interactive = False
            logger.info("Solitario ganado")
            sound.play_later(Sound.WIN, WIN_DELAY_MS)
            self.victory_box = dialogs.show_victory(self, self.new_game)
            return
        self.status.setText(f"En fundaciones: {sum(len(f) for f in game.foundations)}/52")
        key = board_key(game)  # robar/reciclar no lo cambia; mover o deshacer un movimiento, sí
        if key != self._dismissed_key:
            self._dismissed_key = None  # cambió la posición: el próximo atasco se vuelve a avisar
        if self._dismissed_key is None and not self._box_open():
            self.watcher.start(game)  # si prueba la traba emite `stuck`; si corta por límite, nada

    def _on_stuck(self) -> None:
        self._dismissed_key = board_key(self.game)
        self.stuck_box = dialogs.show_stuck(self, self.game.can_undo, self.new_game, self.undo)

    def _box_open(self) -> bool:
        return self.stuck_box is not None and self.stuck_box.isVisible()
