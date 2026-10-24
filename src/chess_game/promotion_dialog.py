"""Diálogo de coronación: el jugador elige dama, torre, alfil o caballo (Esc o cerrar: no se corona)."""
import chess
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QHBoxLayout, QToolButton, QWidget

from src.chess_game.piece_painter import piece_icon
from src.common import theme
from src.common.glass_dialog import GlassDialog
from src.common.qss import button_qss
from src.common.theme import SECONDARY, SPACE, px, window_scale

_CHOICES = [(chess.QUEEN, "Dama"), (chess.ROOK, "Torre"), (chess.BISHOP, "Alfil"), (chess.KNIGHT, "Caballo")]
ICON_SIZE = 72  # unidades


class PromotionDialog(GlassDialog):
    def __init__(self, color: chess.Color, parent: QWidget | None = None):
        window = parent.window() if parent is not None else None
        u = window_scale(window.width(), window.height()) if window is not None else 1.0
        super().__init__(parent, u, "Coronación")
        self.choice: int | None = None
        self.add_label("Elegí la pieza para coronar.")
        self.setStyleSheet(self.styleSheet() + button_qss("QToolButton#promotionButton", SECONDARY, u))
        row = QHBoxLayout()
        row.setSpacing(px(SPACE.sm, u))
        icon = px(ICON_SIZE, u)
        label_font = QFont(theme.TYPE.ui_family)
        label_font.setPixelSize(px(theme.TYPE.control, u, 9))
        self.buttons: dict[int, QToolButton] = {}
        for piece_type, name in _CHOICES:
            button = QToolButton()
            button.setObjectName("promotionButton")
            button.setIcon(QIcon(piece_icon(chess.Piece(piece_type, color), icon, self.devicePixelRatioF())))
            button.setIconSize(QSize(icon, icon))
            button.setText(name)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setFont(label_font)  # QToolButton no toma la fuente de la hoja de estilos
            button.setToolTip(name)
            button.setAccessibleName(name)
            button.setProperty("piece_type", piece_type)
            button.clicked.connect(self._choose)  # sin lambda: ver HoverFader
            row.addWidget(button)
            self.buttons[piece_type] = button
        self.body.addSpacing(px(SPACE.sm, u))
        self.body.addLayout(row)

    def _choose(self) -> None:
        self.choice = self.sender().property("piece_type")
        self.accept()


def ask_promotion(color: chess.Color, parent: QWidget | None = None) -> int | None:
    """Devuelve el tipo de pieza elegido, o None si se cancela (la jugada no se hace)."""
    dialog = PromotionDialog(color, parent)
    dialog.exec()
    return dialog.choice
