"""Intensidad animada (0 = reposo, 1 = encendida) de cada mitad de la pantalla de inicio."""
from PyQt6.QtCore import QEasingCurve, QObject, QVariantAnimation, pyqtSignal

from src.app.home.home_layout import Side
from src.common.theme import MOTION


class _SideAnimation(QVariantAnimation):
    def __init__(self, side: Side, parent: QObject):
        super().__init__(parent)
        self.side = side


class HoverFader(QObject):
    """Sin lambdas en las conexiones: una lambda que captura `self` forma un ciclo a través de Qt; el GC de
    Python le borra los argumentos por defecto y, si la señal se emite después, el slot falla y PyQt aborta."""

    changed = pyqtSignal()  # en cada paso de la animación (sólo durante la transición: nada continuo)

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self.values = {side: 0.0 for side in Side}
        self._animations: dict[Side, QVariantAnimation] = {}
        for side in Side:
            animation = _SideAnimation(side, self)
            animation.setDuration(MOTION.hover_ms)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.valueChanged.connect(self._on_value)
            self._animations[side] = animation

    def light(self, active: Side | None) -> None:
        """Enciende `active` y apaga la otra (None: las dos en reposo), desde donde estén."""
        for side, animation in self._animations.items():
            target = 1.0 if side is active else 0.0
            running = animation.state() == QVariantAnimation.State.Running
            if running and animation.endValue() == target:
                continue
            animation.stop()
            if self.values[side] != target:
                animation.setStartValue(self.values[side])
                animation.setEndValue(target)
                animation.start()

    def reset(self) -> None:
        for side, animation in self._animations.items():
            animation.stop()
            self.values[side] = 0.0
        self.changed.emit()

    def _on_value(self, value) -> None:
        self.values[self.sender().side] = float(value)
        self.changed.emit()
