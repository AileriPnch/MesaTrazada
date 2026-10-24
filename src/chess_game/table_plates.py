"""Carteles de torneo (rival y jugador, texto grabado) y bandejas de capturadas: nogal con fieltro bordó, las
piezas paradas adentro con su sombra (los mismos sprites del tablero, más chicos) y la ventaja de material "+N"."""
import chess
from PyQt6.QtCore import QPoint, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QWidget

from src.chess_game.art_library import ANCHOR_UP, ArtLibrary
from src.chess_game.piece_sprites import PieceSprites, rest_sprites
from src.chess_game.table_object import TableObject
from src.chess_game.table_sprites import UiSprites, engrave, font
from src.common import theme
from src.common.theme import COLORS, TABLE_LOOK


class NamePlate(TableObject):
    def __init__(self, sprites: UiSprites, parent: QWidget):
        super().__init__(sprites, "cartel", parent)
        self.text = ""

    def set_text(self, text: str) -> None:
        self.text = text
        self.setAccessibleName(text)
        self.update()

    def paintEvent(self, event) -> None:
        if self.at is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.sprites.draw(p, "cartel", self.at, self.dpr())
        engrave(p, self.face(), self.text, self.text_font())

    def face(self) -> QRectF:
        return self.at.rect(self.sprites.ui.box("cartel", "cara"))

    def text_font(self) -> QFont:
        size = max(TABLE_LOOK.min_text, self.s * TABLE_LOOK.plate_text)
        return font(theme.TYPE.ui_family, size, theme.TYPE.ui_strong)


class CapturedTray(TableObject):
    """Las piezas de un color que ya salieron del tablero, en dos columnas, desde el lado de su dueño en la mesa
    (la bandeja del rival se llena desde arriba; la tuya, desde abajo). Si son muchas, las filas se juntan: las de
    adelante tapan un poco a las de atrás, como en una mesa. El "+N" va pegado a las piezas."""

    def __init__(self, sprites: UiSprites, art: ArtLibrary, parent: QWidget, from_bottom: bool = False):
        super().__init__(sprites, "bandeja", parent)
        self.art = art
        self.from_bottom = from_bottom
        self.pieces: list[chess.Piece] = []
        self.advantage = 0
        self._sprites: dict[tuple, PieceSprites] = {}

    def set_pieces(self, pieces: list[chess.Piece], advantage: int) -> None:
        if (pieces, advantage) != (self.pieces, self.advantage):
            self.pieces, self.advantage = list(pieces), advantage
            self.update()

    def _piece(self, piece: chess.Piece, size: int) -> PieceSprites:
        key = (piece, size)
        if key not in self._sprites:
            if len(self._sprites) > 24:
                self._sprites.clear()
            self._sprites[key] = rest_sprites(self.art, piece, size)
        return self._sprites[key]

    def paintEvent(self, event) -> None:
        if self.at is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        dpr = self.dpr()
        self.sprites.draw(p, "bandeja", self.at, dpr)
        felt = self.at.rect(self.sprites.ui.box("bandeja", "fieltro"))
        size = TABLE_LOOK.captured * self.s
        label_h = self.s * 0.36 if self.advantage > 0 else 0.0
        rows = (len(self.pieces) + 1) // 2
        step = size if rows < 2 else min(size, (felt.height() - label_h - size) / (rows - 1))
        if self.from_bottom:  # filas desde abajo; el "+N", arriba de la última
            tops = [felt.bottom() - size - r * step for r in range(rows)]
            label_y = (tops[-1] if tops else felt.bottom()) - label_h
        else:
            tops = [felt.top() + r * step for r in range(rows)]
            label_y = (tops[-1] + size) if tops else felt.top()
        placed = sorted(((tops[i // 2], i % 2, piece) for i, piece in enumerate(self.pieces)), key=lambda t: t[0])
        p.save()
        p.scale(1 / dpr, 1 / dpr)  # los sprites de las piezas están en px físicos
        for top, column, piece in placed:  # de atrás (arriba) hacia adelante
            sprites = self._piece(piece, round(size * dpr))
            x = felt.left() + (column + 0.5) * felt.width() / 2
            anchor = QPoint(round(x * dpr), round((top + size * (1 - ANCHOR_UP)) * dpr))
            for layer in (sprites.ground, sprites.body):
                p.drawPixmap(layer.rect(anchor).topLeft(), layer.pixmap)
        p.restore()
        if self.advantage > 0:
            p.setPen(QColor(COLORS.text))
            p.setFont(font(theme.TYPE.ui_family, max(TABLE_LOOK.min_text, self.s * TABLE_LOOK.captured_text),
                           theme.TYPE.ui_strong))
            label = QRectF(felt.left(), label_y, felt.width(), label_h)
            p.drawText(label, Qt.AlignmentFlag.AlignCenter, f"+{self.advantage}")
