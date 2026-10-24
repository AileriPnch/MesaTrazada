"""Botón redondo con el ícono de un parlante dibujado por código: ondas según el volumen, cruz si está en
silencio. Vidrio oscuro con borde; en ámbar con el mouse encima o con el panel abierto. Una pantalla puede
ponerle otra "piel" (`set_skin`): el ajedrez la cambia por una perilla de latón."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QAbstractButton, QWidget

from src.common.theme import COLORS, NEON
from src.common.volume import Volume


def _color(hex_color: str, alpha: float) -> QColor:
    color = QColor(hex_color)
    color.setAlphaF(alpha)
    return color


def speaker_path(box: QRectF) -> QPainterPath:
    """Parlante (cuerpo + cono) mirando a la derecha, en la mitad izquierda de `box`."""
    x, y, w, h = box.x(), box.y(), box.width(), box.height()
    path = QPainterPath()
    path.moveTo(x + 0.18 * w, y + 0.38 * h)
    path.lineTo(x + 0.34 * w, y + 0.38 * h)
    path.lineTo(x + 0.54 * w, y + 0.2 * h)
    path.lineTo(x + 0.54 * w, y + 0.8 * h)
    path.lineTo(x + 0.34 * w, y + 0.62 * h)
    path.lineTo(x + 0.18 * w, y + 0.62 * h)
    path.closeSubpath()
    return path


class SpeakerButton(QAbstractButton):
    def __init__(self, volume: Volume, parent: QWidget):
        super().__init__(parent)
        self.volume = volume
        self.opened = False
        self.skin = None  # objeto con paint(p, rect, lit, down, volume, dpr), o None = el parlante
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Volumen")
        self.setAccessibleName("Volumen")
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        volume.changed.connect(self.update)

    def set_skin(self, skin) -> None:
        self.skin = skin
        self.update()

    def set_open(self, opened: bool) -> None:
        self.opened = opened
        self.update()

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        lit = self.opened or self.underMouse()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.skin is not None:
            self.skin.paint(p, QRectF(self.rect()), lit, self.isDown(), self.volume, self.devicePixelRatioF())
            return
        circle = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(_color(NEON.color if lit else COLORS.border, 0.9 if lit else 0.8), 1.0))
        p.setBrush(_color(COLORS.glass, 0.72))
        p.drawEllipse(circle)
        icon = circle.adjusted(circle.width() * 0.2, circle.height() * 0.2, -circle.width() * 0.16, -circle.height() * 0.2)
        ink = _color(NEON.core if lit else COLORS.text, 0.95 if lit else 0.8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(ink)
        p.drawPath(speaker_path(icon))
        pen = QPen(ink, max(1.2, icon.width() * 0.08))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        center = QPointF(icon.x() + icon.width() * 0.5, icon.center().y())
        if self.volume.muted or self.volume.level == 0:
            r = icon.width() * 0.13
            right = QPointF(icon.x() + icon.width() * 0.8, center.y())
            p.drawLine(right + QPointF(-r, -r), right + QPointF(r, r))
            p.drawLine(right + QPointF(-r, r), right + QPointF(r, -r))
            return
        waves = 1 if self.volume.level < 50 else 2
        for i in range(waves):
            r = icon.width() * (0.2 + 0.18 * i)
            p.drawArc(QRectF(center.x() - r, center.y() - r, 2 * r, 2 * r), -50 * 16, 100 * 16)
