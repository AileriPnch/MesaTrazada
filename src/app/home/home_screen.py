"""Pantalla de inicio "mesa de juego": dos mitades clickeables (ajedrez | solitario) con neón tenue.

Clic en una mitad → aparecen ahí sus opciones de arranque y el botón para empezar. Esc o clic afuera
las cierra. El dibujo sale de capas pre-renderizadas (`HomeLayers`); el hover sólo cambia opacidades. Abajo a la
derecha, un enlace discreto abre el "Acerca de".
"""
from PyQt6.QtCore import QPointF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter
from PyQt6.QtWidgets import QPushButton, QWidget

from src.app.home.home_layers import HomeLayers
from src.app.home.home_layout import HomeLayout, Side
from src.app.home.hover_fader import HoverFader
from src.app.home.options_panel import OptionsPanel, check_engine, chess_panel, solitaire_panel
from src.chess_game import art_library
from src.common import theme
from src.common.app_info import VERSION
from src.common.theme import COLORS, CORNER, MOTION, px


def about_link_qss(u: float) -> str:
    t = theme.TYPE
    return f"""
QPushButton#aboutLink {{
    background: transparent; border: none; padding: {px(2, u)}px {px(4, u)}px; color: {COLORS.text_muted};
    font-family: '{t.ui_family}'; font-size: {px(t.label, u, 9)}px; font-weight: {t.ui_weight};
}}
QPushButton#aboutLink:hover, QPushButton#aboutLink:focus {{ color: {COLORS.accent}; }}
"""


class HomeScreen(QWidget):
    chess_requested = pyqtSignal(object, object)  # ColorChoice, Difficulty
    solitaire_requested = pyqtSignal(int)  # cartas por robo
    about_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # paintEvent pinta todo el fondo
        self.layers = HomeLayers()
        self.fader = HoverFader(self)
        self.fader.changed.connect(self.update)
        self.hovered: Side | None = None
        self.opened: Side | None = None
        self.panels: dict[Side, OptionsPanel] = {Side.CHESS: chess_panel(self), Side.SOLITAIRE: solitaire_panel(self)}
        for side, panel in self.panels.items():
            panel.hide()
            panel.primary.clicked.connect(self._on_primary)  # sin lambda: ver HoverFader
        self.about_link = QPushButton("Acerca de", self)
        self.about_link.setObjectName("aboutLink")
        self.about_link.setToolTip(f"Versión {VERSION} · licencia, créditos (F1)")
        self.about_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.about_link.clicked.connect(self._on_about)
        self._link_u = None
        self._rebuild = QTimer(self)
        self._rebuild.setSingleShot(True)
        self._rebuild.setInterval(MOTION.rebuild_ms)
        self._rebuild.timeout.connect(self._rebuild_now)

    @property
    def hover(self) -> dict[Side, float]:
        return self.fader.values

    def home_layout(self) -> HomeLayout:
        return HomeLayout(self.width(), self.height())

    # --- opciones -----------------------------------------------------------------------------------
    def open_options(self, side: Side) -> None:
        self.opened = side
        panel = self.panels[side]
        if side is Side.CHESS:
            check_engine(panel)
            art_library.prefetch()  # mientras se eligen las opciones, el arte del ajedrez carga en otro hilo
        self._place_panel(side)
        panel.show()
        panel.raise_()
        (panel.primary if panel.primary.isEnabled() else self).setFocus()
        self._update_cursor()
        self.fader.light(side)

    def close_options(self) -> None:
        if self.opened is None:
            return
        self.panels[self.opened].hide()
        self.opened = None
        self.setFocus()
        cursor = QPointF(self.mapFromGlobal(QCursor.pos()))
        self.hovered = self.home_layout().side_at(cursor) if self.rect().contains(cursor.toPoint()) else None
        self.fader.light(self.hovered)
        self._update_cursor()

    def reset(self) -> None:
        """Al volver al menú: sin opciones abiertas ni mitades encendidas."""
        if self.opened is not None:
            self.panels[self.opened].hide()
        self.opened = self.hovered = None
        self.fader.reset()
        self._update_cursor()

    def _on_about(self) -> None:
        self.close_options()
        self.about_requested.emit()

    def _place_about_link(self) -> None:
        u = self.home_layout().u
        if u != self._link_u:
            self._link_u = u
            self.about_link.setStyleSheet(about_link_qss(u))
            self.about_link.adjustSize()
        inset = px(CORNER.inset, u)
        link = self.about_link
        link.move(self.width() - inset - link.width(), self.height() - inset - link.height())

    def _on_primary(self) -> None:
        self._start(next(side for side, panel in self.panels.items() if panel.primary is self.sender()))

    def _start(self, side: Side) -> None:
        panel = self.panels[side]
        self.close_options()
        if side is Side.CHESS:
            self.chess_requested.emit(panel.value("Color"), panel.value("Dificultad"))
        else:
            self.solitaire_requested.emit(panel.value("Robo"))

    def _place_panel(self, side: Side) -> None:
        layout, panel = self.home_layout(), self.panels[side]
        panel.apply_scale(layout.u)
        width = max(round(layout.panel_width(side)), panel.minimumSizeHint().width())  # nunca más angosto
        panel.setGeometry(layout.panel_rect(side, panel.height_for(width), width).toRect())

    def _set_hovered(self, side: Side | None) -> None:
        if side is not self.hovered:
            self.hovered = side
            self.fader.light(side)
        self._update_cursor()

    def _update_cursor(self) -> None:
        if self.opened is None and self.hovered is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()

    # --- eventos ------------------------------------------------------------------------------------
    def mouseMoveEvent(self, event) -> None:
        if self.opened is None:
            self._set_hovered(self.home_layout().side_at(event.position()))

    def leaveEvent(self, event) -> None:
        if self.opened is None:
            self._set_hovered(None)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.opened is not None:
            self.close_options()  # clic afuera del panel (adentro no llega: WA_NoMousePropagation)
            return
        side = self.home_layout().side_at(event.position())
        if side is not None:
            self.open_options(side)

    def mouseDoubleClickEvent(self, event) -> None:
        """El 2.º clic de un doble clic no debe cerrar lo que abrió el 1.º."""

    def keyPressEvent(self, event) -> None:
        if self.opened is not None and event.key() == Qt.Key.Key_Escape:
            self.close_options()
        elif self.opened is not None and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            primary = self.panels[self.opened].primary
            if primary.isEnabled():
                primary.click()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        self._rebuild.start()  # regenerar recién cuando se deja de cambiar el tamaño
        self._place_about_link()
        if self.opened is not None:
            self._place_panel(self.opened)

    def _rebuild_now(self) -> None:
        layout, dpr = self.home_layout(), self.devicePixelRatioF()
        if not self.layers.is_current(layout, dpr):
            self.layers.build(layout, dpr)
            self.update()

    def paintEvent(self, event) -> None:
        layout, dpr = self.home_layout(), self.devicePixelRatioF()
        current = self.layers.is_current(layout, dpr)
        if not current and (self.layers.key is None or self.layers.key[2] != dpr):
            self.layers.build(layout, dpr)  # primera vez o cambio de pantalla: hace falta ya
            current = True
        p = QPainter(self)
        if not current:  # cambiando de tamaño: se estira la última versión hasta regenerar
            old = self.layers.layout
            p.scale(layout.width / old.width, layout.height / old.height)
        self.layers.paint(p, self.hover)
        p.end()
