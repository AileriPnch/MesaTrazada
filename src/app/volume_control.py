"""Control de volumen: un parlante en la esquina superior derecha de la ventana, el mismo en el menú y en
los dos juegos. Al tocarlo se abre un panel con el deslizador y el botón de silencio; Esc o un clic afuera
lo cierran (ese clic sólo cierra)."""
from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, QRectF, Qt
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from src.app.speaker_button import SpeakerButton
from src.common import theme
from src.common.qss import button_qss, rgba
from src.common.theme import COLORS, CORNER, NEON, RADIUS, SECONDARY, SPACE, px
from src.common.volume import Volume


def panel_qss(u: float) -> str:
    t = theme.TYPE
    label = f"font-family: '{t.ui_family}'; font-size: {px(t.label, u, 9)}px; background: transparent;"
    groove = px(4, u)
    handle = px(14, u)
    return f"""
QFrame#volumePanel {{
    background: {rgba(COLORS.glass, 0.96)}; border: 1px solid {rgba(COLORS.border, 0.9)};
    border-radius: {px(RADIUS.xl, u)}px;
}}
QLabel#volumeLabel {{ {label} color: {COLORS.text_muted}; font-weight: {t.ui_weight}; }}
QLabel#volumeValue {{ {label} color: {COLORS.text}; font-weight: {t.ui_strong}; }}
QSlider#volumeSlider {{ background: transparent; min-height: {handle + 4}px; }}
QSlider#volumeSlider::groove:horizontal {{
    height: {groove}px; background: {rgba(COLORS.border, 0.9)}; border-radius: {groove // 2}px;
}}
QSlider#volumeSlider::sub-page:horizontal {{ background: {COLORS.accent}; border-radius: {groove // 2}px; }}
QSlider#volumeSlider[muted="true"]::sub-page:horizontal {{ background: {COLORS.text_muted}; }}
QSlider#volumeSlider::handle:horizontal {{
    background: {NEON.core}; width: {handle}px; margin: -{(handle - groove) // 2}px 0; border-radius: {handle // 2}px;
}}
""" + button_qss("QPushButton#volumeMute", SECONDARY, u)


class VolumePanel(QFrame):
    def __init__(self, volume: Volume, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("volumePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation)
        self.volume = volume
        self.value = QLabel()
        self.value.setObjectName("volumeValue")
        title = QLabel("Volumen")
        title.setObjectName("volumeLabel")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setObjectName("volumeSlider")
        self.slider.setRange(0, 100)
        self.slider.setAccessibleName("Volumen")
        self.mute = QPushButton("Silenciar")
        self.mute.setObjectName("volumeMute")
        self.mute.setCheckable(True)
        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.value)
        self._column = QVBoxLayout(self)
        self._column.addLayout(header)
        self._column.addWidget(self.slider)
        self._column.addWidget(self.mute)
        self.slider.valueChanged.connect(self._on_slider)
        self.mute.toggled.connect(volume.set_muted)
        volume.changed.connect(self.refresh)
        self.refresh()

    def _on_slider(self, value: int) -> None:
        self.volume.set_level(value)
        if self.volume.muted and value > 0:
            self.volume.set_muted(False)  # mover el volumen saca el silencio

    def refresh(self) -> None:
        for widget, setter, value in ((self.slider, self.slider.setValue, self.volume.level),
                                      (self.mute, self.mute.setChecked, self.volume.muted)):
            widget.blockSignals(True)
            setter(value)
            widget.blockSignals(False)
        self.value.setText("Silencio" if self.volume.muted else f"{self.volume.level} %")
        self.mute.setText("Activar sonido" if self.volume.muted else "Silenciar")
        self.slider.setProperty("muted", self.volume.muted)
        self.slider.style().polish(self.slider)

    def apply_scale(self, u: float) -> None:
        self.setStyleSheet(panel_qss(u))
        pad = px(SPACE.lg, u)
        self._column.setContentsMargins(pad, px(SPACE.md, u), pad, pad)
        self._column.setSpacing(px(SPACE.sm, u))
        self.setFixedWidth(px(CORNER.panel_width, u))
        self.adjustSize()


class VolumeControl(QObject):
    """Botón + panel, hijos de la ventana principal y siempre por encima de la pantalla actual."""

    def __init__(self, window: QWidget, volume: Volume):
        super().__init__(window)
        self.window = window
        self.button = SpeakerButton(volume, window)
        self.panel = VolumePanel(volume, window)
        self.panel.hide()
        self.button.clicked.connect(self.toggle)
        self.u = None

    @property
    def is_open(self) -> bool:
        return self.panel.isVisible()

    def place(self, u: float) -> None:
        if u != self.u:
            self.u = u
            self.panel.apply_scale(u)
        size, inset = px(CORNER.size, u), px(CORNER.inset, u)
        self.button.setGeometry(QRect(self.window.width() - inset - size, inset, size, size))
        self.panel.move(QPoint(self.window.width() - inset - self.panel.width(), inset + size + px(CORNER.gap, u)))
        self.button.raise_()
        self.panel.raise_()

    def toggle(self) -> None:
        if self.is_open:
            self.close()
        else:
            self.open()

    def open(self) -> None:
        self.panel.adjustSize()
        self.panel.show()
        self.panel.raise_()
        self.panel.slider.setFocus()
        self.button.set_open(True)
        QApplication.instance().installEventFilter(self)

    def close(self) -> None:
        QApplication.instance().removeEventFilter(self)
        self.panel.hide()
        self.button.set_open(False)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.close()
            return True
        if event.type() == QEvent.Type.MouseButtonPress and isinstance(obj, QWidget) and obj.window() is self.window:
            inside = QRectF(self.panel.geometry()).united(QRectF(self.button.geometry()))
            if not inside.contains(self.window.mapFromGlobal(event.globalPosition())):
                self.close()
                return True  # el clic afuera sólo cierra
        return False
