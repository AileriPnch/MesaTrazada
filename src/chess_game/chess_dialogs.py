"""Avisos del ajedrez con el estilo de la app (no bloquean): el error del motor. (El fin de la partida va en
la tarjeta apoyada sobre la planilla: result_card.py.)"""
from PyQt6.QtWidgets import QWidget

from src.common.glass_dialog import GlassDialog
from src.common.theme import px

MIN_WIDTH = 340  # unidades


class MessageDialog(GlassDialog):
    """Título (Playfair Display), texto (Inter) y un botón principal "Aceptar"."""

    def __init__(self, parent: QWidget, u: float, title: str, text: str):
        super().__init__(parent, u, title)
        self.setMinimumWidth(px(MIN_WIDTH, u))
        self.message = self.add_label(text)
        self.accept_button = self.add_buttons(("Aceptar", True))[0]
        self.accept_button.clicked.connect(self.accept)
        self.accept_button.setDefault(True)

    def text(self) -> str:
        return f"{self.title.text()}\n\n{self.message.text()}"


def show_engine_error(parent: QWidget, u: float, message: str) -> MessageDialog:
    dialog = MessageDialog(parent, u, "Error del motor", message)
    dialog.open()
    return dialog
