"""Avisos del solitario con el estilo de la app (vidrio oscuro, título en Playfair, Inter, botón principal
ámbar): confirmación, victoria y "No quedan movimientos". Victoria y traba no bloquean. Cada botón cierra el
aviso ANTES de hacer lo suyo (igual que antes con QMessageBox)."""
from typing import Callable

from PyQt6.QtWidgets import QDialog, QPushButton, QWidget

from src.common.glass_dialog import GlassDialog
from src.common.theme import px, window_scale

MIN_WIDTH = 380  # unidades


class ChoiceDialog(GlassDialog):
    def __init__(self, parent: QWidget, title: str, text: str, buttons: list[tuple[str, bool]]):
        window = parent.window()
        u = window_scale(window.width(), window.height())
        super().__init__(parent, u, title)
        self.setMinimumWidth(px(MIN_WIDTH, u))
        self.add_label(text)
        self._buttons = self.add_buttons(*buttons)

    def buttons(self) -> list[QPushButton]:
        return self._buttons

    def button(self, text: str) -> QPushButton:
        return next(b for b in self._buttons if b.text() == text)


def ask_confirmation(parent: QWidget, text: str) -> bool:
    dialog = ChoiceDialog(parent, "Partida en curso", text, [("Cancelar", False), ("Empezar otra", True)])
    dialog.button("Cancelar").clicked.connect(dialog.reject)
    dialog.button("Empezar otra").clicked.connect(dialog.accept)
    dialog.button("Empezar otra").setDefault(True)
    return dialog.exec() == QDialog.DialogCode.Accepted


def show_victory(parent: QWidget, on_new_game: Callable[[], None]) -> ChoiceDialog:
    dialog = ChoiceDialog(parent, "¡Ganaste!", "Completaste las cuatro fundaciones.",
                          [("Cerrar", False), ("Nueva partida", True)])
    dialog.button("Cerrar").clicked.connect(dialog.reject)
    new_game = dialog.button("Nueva partida")
    new_game.clicked.connect(dialog.accept)
    new_game.clicked.connect(on_new_game)
    new_game.setDefault(True)
    dialog.open()
    return dialog


def show_stuck(parent: QWidget, can_undo: bool, on_new_game: Callable[[], None],
               on_undo: Callable[[], None]) -> ChoiceDialog:
    dialog = ChoiceDialog(parent, "No quedan movimientos", "No quedan movimientos que hagan avanzar la partida.",
                          [("Seguir mirando", False), ("Deshacer", False), ("Nueva partida", True)])
    dialog.button("Seguir mirando").clicked.connect(dialog.reject)  # Esc también: seguir mirando
    undo = dialog.button("Deshacer")
    undo.setEnabled(can_undo)
    undo.clicked.connect(dialog.reject)
    undo.clicked.connect(on_undo)
    new_game = dialog.button("Nueva partida")
    new_game.clicked.connect(dialog.accept)
    new_game.clicked.connect(on_new_game)
    dialog.open()
    return dialog
