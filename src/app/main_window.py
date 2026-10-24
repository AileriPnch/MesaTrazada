"""Ventana principal: pantalla de inicio y navegación entre juegos."""
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from src.app.about_dialog import AboutDialog, show_about

from src.app.home.home_screen import HomeScreen
from src.app.volume_control import VolumeControl
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from src.common import sound
from src.common.app_info import APP_NAME
from src.common.game_screen import GameScreen
from src.common.theme import window_scale
from src.solitaire.solitaire_screen import SolitaireScreen

logger = logging.getLogger(__name__)

APP_TITLE = APP_NAME


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 720)
        self.setMinimumSize(800, 600)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        self.home = HomeScreen()
        self.home.chess_requested.connect(self.open_chess)
        self.home.solitaire_requested.connect(self.open_solitaire)
        self.home.about_requested.connect(self.show_about)
        self._stack.addWidget(self.home)
        self.game: GameScreen | None = None
        self.volume_control = VolumeControl(self, sound.volume())  # misma esquina en todas las pantallas
        self.about: AboutDialog | None = None
        QShortcut(QKeySequence(Qt.Key.Key_F1), self, self.show_about)  # en cualquier pantalla

    def show_about(self) -> AboutDialog:
        if self.about is None or not self.about.isVisible():
            self.volume_control.close()
            self.about = show_about(self, window_scale(self.width(), self.height()))
        return self.about

    def open_chess(self, color: ColorChoice, difficulty: Difficulty) -> None:
        self.open_game(ChessScreen).start_game(color, difficulty)

    def open_solitaire(self, draw_count: int) -> None:
        self.open_game(SolitaireScreen).deal(draw_count)

    def open_game(self, screen_cls: type[GameScreen]) -> GameScreen:
        self._close_game()
        logger.info("Abriendo %s", screen_cls.title)
        self.game = screen_cls()
        self.game.back_requested.connect(self.show_menu)
        self._stack.addWidget(self.game)
        self._stack.setCurrentWidget(self.game)
        self.volume_control.close()
        self.volume_control.button.set_skin(getattr(self.game, "volume_skin", None))  # el ajedrez: perilla de latón
        self.setWindowTitle(f"{APP_TITLE} — {screen_cls.title}")
        return self.game

    def show_menu(self) -> None:
        self._close_game()
        self.home.reset()
        self.volume_control.close()
        self._stack.setCurrentWidget(self.home)
        self.setWindowTitle(APP_TITLE)

    def _close_game(self) -> None:
        """Cada juego se destruye al salir para liberar sus recursos (motor, etc.)."""
        if self.game is None:
            return
        logger.info("Cerrando %s", self.game.title)
        self.volume_control.button.set_skin(None)
        self.game.shutdown()
        self._stack.removeWidget(self.game)
        self.game.deleteLater()
        self.game = None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.volume_control.place(window_scale(self.width(), self.height()))

    def closeEvent(self, event) -> None:
        self._close_game()
        super().closeEvent(event)
