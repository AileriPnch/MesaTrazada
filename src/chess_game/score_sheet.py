"""Planilla de la partida: el portapapeles renderizado (hoja con renglones impresos, vacía) y, por código, las
jugadas escritas a mano (Caveat, tinta azul-negra), los encabezados impresos, la última jugada con resaltador y
el resultado al pie. Partidas largas: hojas de `filas` renglones; se ve la última y con la rueda del mouse (o
RePág / AvPág con foco) se miran las anteriores."""
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QWidget

from src.chess_game.table_object import TableObject
from src.chess_game.table_sprites import UiSprites, font
from src.common import theme
from src.common.theme import COLORS, TABLE_LOOK

LEFT, RIGHT = Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignRight
MIDDLE = Qt.AlignmentFlag.AlignVCenter


class ScoreSheet(TableObject):
    def __init__(self, sprites: UiSprites, parent: QWidget):
        super().__init__(sprites, "planilla", parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Planilla")
        self.moves: list[str] = []
        self.result = ""
        self.page = 0
        self.info = sprites.ui.info["planilla"]

    @property
    def rows(self) -> int:
        return self.info["filas"]

    @property
    def pages(self) -> int:
        return max(1, -(-((len(self.moves) + 1) // 2) // self.rows))

    def set_moves(self, sans: list[str]) -> None:
        self.moves = list(sans)
        self.page = self.pages - 1  # siempre a la vista la hoja de la última jugada
        self.update()

    def set_result(self, text: str) -> None:
        self.result = text
        self.update()

    def show_page(self, page: int) -> None:
        self.page = max(0, min(self.pages - 1, page))
        self.update()

    def wheelEvent(self, event) -> None:
        step = event.angleDelta().y()
        if step:
            self.show_page(self.page + (-1 if step > 0 else 1))
        event.accept()

    def keyPressEvent(self, event) -> None:
        moves = {Qt.Key.Key_PageUp: -1, Qt.Key.Key_PageDown: 1}
        if event.key() in moves:
            self.show_page(self.page + moves[event.key()])
            return
        super().keyPressEvent(event)

    def row_height(self) -> float:
        ys = self.info["renglones"]
        return (ys[1] - ys[0]) * self.at.scale

    def hand_font(self) -> QFont:
        return font(theme.TYPE.hand_family, max(TABLE_LOOK.min_hand, self.row_height() * TABLE_LOOK.sheet_text),
                    theme.TYPE.hand_weight)

    def move_cell_width(self) -> float:
        """Ancho donde se escribe una jugada (columna menos el margen de la pluma)."""
        x = self.info["columnas"]
        return (x[2] - x[1]) * self.at.scale - self.row_height() * 0.3

    def paintEvent(self, event) -> None:
        if self.at is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.sprites.draw(p, "planilla", self.at, self.dpr())
        at, info, t = self.at, self.info, TABLE_LOOK
        xs = [at.point(x, 0).x() for x in info["columnas"]]  # papel, fin de los números, mitad, papel
        ys = [at.point(0, y).y() for y in info["renglones"]]
        row = ys[1] - ys[0]
        head = (at.point(0, info["encabezado"][0]).y(), ys[0])
        printed = QColor(COLORS.print_ink)
        p.setPen(printed)
        p.setFont(font(theme.TYPE.ui_family, max(t.min_text, row * t.sheet_print), theme.TYPE.ui_strong))
        for text, a, b in (("BLANCAS", xs[1], xs[2]), ("NEGRAS", xs[2], xs[3])):
            p.drawText(QRectF(a, head[0], b - a, head[1] - head[0]), Qt.AlignmentFlag.AlignCenter, text)
        hand = self.hand_font()
        number = font(theme.TYPE.ui_family, max(t.min_text, row * 0.5), theme.TYPE.ui_weight)
        pad = row * 0.3
        first = self.page * self.rows
        for k in range(self.rows):
            n = first + k
            if 2 * n >= len(self.moves):
                break
            top = ys[k]
            p.setFont(number)
            p.setPen(printed)
            p.drawText(QRectF(xs[0], top, xs[1] - xs[0] - pad * 0.6, row), RIGHT | MIDDLE, f"{n + 1}.")
            for c in (0, 1):
                i = 2 * n + c
                if i >= len(self.moves):
                    break
                cell = QRectF(xs[1 + c] + pad, top, xs[2 + c] - xs[1 + c] - pad, row)
                if i == len(self.moves) - 1:  # resaltador detrás de la última (la tinta sigue oscura)
                    mark = QColor(COLORS.highlighter)
                    mark.setAlphaF(t.highlight)
                    p.fillRect(QRectF(cell.left() - pad * 0.5, top + row * 0.2, cell.width() * 0.8, row * 0.62), mark)
                p.setFont(hand)
                p.setPen(QColor(COLORS.pen_ink))
                p.drawText(cell, LEFT | MIDDLE, self.moves[i])
        foot = QRectF(xs[0] + pad, ys[-1], xs[3] - xs[0] - 2 * pad, at.point(0, info["pie"][1]).y() - ys[-1])
        p.setFont(font(theme.TYPE.ui_family, max(t.min_text, row * t.sheet_print), theme.TYPE.ui_weight))
        p.setPen(printed)
        if self.pages > 1:
            p.drawText(foot, RIGHT | MIDDLE, f"Hoja {self.page + 1} de {self.pages}")
        if self.result and self.page == self.pages - 1:
            p.setFont(hand)
            p.setPen(QColor(COLORS.pen_ink))
            p.drawText(foot, LEFT | MIDDLE, self.result)
