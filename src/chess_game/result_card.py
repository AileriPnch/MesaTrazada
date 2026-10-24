"""Tarjeta de fin de partida apoyada sobre la planilla (reemplaza al diálogo): título (Playfair) y motivo (Inter)
escritos por código. También avisa si falta el motor. Un clic o Esc la levanta; "Nueva partida" sigue a mano.
Dibuja su propia sombra y su contacto (cae sobre la planilla, no sobre la mesa)."""
from PyQt6.QtCore import QRect, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from src.chess_game.table_object import TableObject
from src.chess_game.table_sprites import UiSprites, font, place
from src.common import theme
from src.common.theme import COLORS, TABLE_LOOK


class ResultCard(TableObject):
    dismissed = pyqtSignal()

    def __init__(self, sprites: UiSprites, parent: QWidget):
        super().__init__(sprites, "tarjeta", parent)
        self.headline = ""
        self.text = ""
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide()

    def place(self, target: QRectF, s: float) -> None:
        """`target` = la tarjeta; el widget abarca también su sombra."""
        at = place(self.box(), target)
        image = self.sprites.ui.image("tarjeta")
        full = QRectF(at.origin.x(), at.origin.y(), image.width() * at.scale, image.height() * at.scale)
        geometry = QRect(round(full.x()), round(full.y()), round(full.width()), round(full.height()))
        self.setGeometry(geometry)
        self.s = s
        self.at = at.translated(-geometry.x(), -geometry.y())
        self.update()

    def show_card(self, headline: str, text: str) -> None:
        self.headline, self.text = headline, text
        self.setAccessibleName(f"{headline}. {text}")
        self.show()
        self.raise_()
        self.update()

    def dismiss(self) -> None:
        if self.isVisible():
            self.hide()
            self.dismissed.emit()

    def mousePressEvent(self, event) -> None:
        self.dismiss()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        if self.at is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        dpr = self.dpr()
        for name in ("tarjeta_contacto", "tarjeta_sombra", "tarjeta"):
            self.sprites.draw(p, name, self.at, dpr)
        area = self.at.rect(self.sprites.ui.box("tarjeta", "texto"))
        t = theme.TYPE
        p.setPen(QColor(COLORS.pen_ink))
        p.setFont(font(t.title_family, max(16, self.s * TABLE_LOOK.card_title), t.title_weight))
        p.drawText(area.adjusted(0, 0, 0, -area.height() * 0.48),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self.headline)
        p.setPen(QColor(COLORS.print_ink))
        p.setFont(font(t.ui_family, max(TABLE_LOOK.min_text, self.s * TABLE_LOOK.card_text), t.ui_weight))
        flags = (Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop).value | Qt.TextFlag.TextWordWrap.value
        p.drawText(area.adjusted(0, area.height() * 0.58, 0, 0), flags, self.text)
