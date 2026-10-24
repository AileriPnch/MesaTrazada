"""Clase base de las pantallas de juego: señal para volver al menú y gancho de cierre."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget


class GameScreen(QWidget):
    """Pantalla de un juego. La ventana principal la crea al entrar y la destruye al salir."""

    back_requested = pyqtSignal()
    title = "Juego"

    def shutdown(self) -> None:
        """Libera recursos externos (p. ej. el proceso del motor). Debe ser idempotente."""
