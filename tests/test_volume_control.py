"""Control de volumen: siempre en la misma esquina (menú y los dos juegos, sin nada debajo), Esc o clic
afuera lo cierran (el clic sólo cierra) y maneja el volumen global."""
import pytest
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QAbstractButton, QLabel

from src.app.main_window import MainWindow
from src.chess_game.chess_screen import ChessScreen
from src.common import sound
from src.common.volume import Volume
from tests.fakes import FakeEngine, factory_for

LEFT, NO_MOD = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier


class FakeChess(ChessScreen):
    def __init__(self):
        super().__init__(engine_factory=factory_for(FakeEngine()))


@pytest.fixture
def window(qapp):
    previous = sound.volume()
    sound.install(Volume(), player=None)  # volumen en memoria: los tests no tocan el registro
    win = MainWindow()
    win.resize(1000, 720)
    win.show()
    QTest.qWait(30)
    yield win
    win.close()
    sound.install(previous, player=None)


def _in_window(widget, window) -> QRect:
    return QRect(widget.mapTo(window, QPoint(0, 0)), widget.size())


def _assert_corner_is_free(window) -> None:
    button = window.volume_control.button
    corner = button.geometry()
    assert window.childAt(corner.center()) is button  # encima de todo
    for widget in window.game.findChildren((QAbstractButton, QLabel)):
        if widget.isVisible():
            assert not _in_window(widget, window).intersects(corner), widget.text()


@pytest.mark.parametrize("size", [(800, 600), (1000, 720), (1920, 1080)])
def test_speaker_sits_in_the_same_free_corner_on_every_screen(window, size):
    window.resize(*size)
    QTest.qWait(30)
    corner = window.volume_control.button.geometry()
    assert corner.right() < window.width() and corner.top() > 0
    window.open_game(FakeChess)
    QTest.qWait(30)
    assert window.volume_control.button.geometry() == corner
    _assert_corner_is_free(window)
    window.open_solitaire(1)
    QTest.qWait(30)
    assert window.volume_control.button.geometry() == corner
    _assert_corner_is_free(window)


def test_esc_or_click_outside_closes_and_the_click_only_closes(window):
    control = window.volume_control
    QTest.mouseClick(control.button, LEFT)
    assert control.is_open
    QTest.keyClick(control.panel.slider, Qt.Key.Key_Escape)
    assert not control.is_open
    QTest.mouseClick(control.button, LEFT)
    assert control.is_open
    QTest.mouseClick(window.home, LEFT, NO_MOD, QPoint(200, 400))  # sobre la mitad del ajedrez
    assert not control.is_open and window.home.opened is None  # no abrió las opciones del ajedrez
    QTest.mouseClick(window.home, LEFT, NO_MOD, QPoint(200, 400))
    assert window.home.opened is not None  # el siguiente clic sí


def test_slider_and_mute_drive_the_global_volume(window):
    control = window.volume_control
    control.open()
    control.panel.slider.setValue(40)
    assert sound.volume().level == 40
    control.panel.mute.click()
    assert sound.volume().muted and sound.volume().gain == 0.0
    assert control.panel.value.text() == "Silencio"
    control.panel.slider.setValue(55)  # mover el volumen saca el silencio
    assert not sound.volume().muted and sound.volume().level == 55
    control.close()
