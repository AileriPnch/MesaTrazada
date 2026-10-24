"""Pantalla de inicio: mitades clickeables, opciones de arranque, Esc / clic afuera y hover sin regenerar."""
from pathlib import Path

import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from config import settings
from src.app.home.home_layout import Side
from src.app.home.home_screen import HomeScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from tests.fakes import wait_until

LEFT = Qt.MouseButton.LeftButton
NO_MOD = Qt.KeyboardModifier.NoModifier


@pytest.fixture
def home(qapp, monkeypatch):
    monkeypatch.setattr(settings, "stockfish_path", Path(__file__))  # "existe": no depende del motor real
    screen = HomeScreen()
    screen.resize(1000, 720)
    screen.show()
    QTest.qWait(20)
    yield screen
    screen.close()


def art_center(home: HomeScreen, side: Side) -> QPoint:
    return home.home_layout().art_rect(side).center().toPoint()


def hover(home: HomeScreen, point: QPoint) -> None:
    event = QMouseEvent(QEvent.Type.MouseMove, QPointF(point), QPointF(home.mapToGlobal(point)),
                        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, NO_MOD)
    QApplication.sendEvent(home, event)


def test_click_on_a_half_opens_its_options_and_escape_closes(home):
    QTest.mouseClick(home, LEFT, NO_MOD, art_center(home, Side.SOLITAIRE))
    assert home.opened is Side.SOLITAIRE and home.panels[Side.SOLITAIRE].isVisible()
    assert not home.panels[Side.CHESS].isVisible()
    QTest.keyClick(home.panels[Side.SOLITAIRE].primary, Qt.Key.Key_Escape)  # sube desde el botón con foco
    assert home.opened is None and not home.panels[Side.SOLITAIRE].isVisible()


def test_click_inside_panel_keeps_it_open_and_click_outside_closes(home):
    home.open_options(Side.CHESS)
    panel = home.panels[Side.CHESS]
    QTest.mouseClick(panel, LEFT, NO_MOD, QPoint(12, 12))  # fondo del panel, no un botón
    assert home.opened is Side.CHESS
    QTest.mouseClick(home, LEFT, NO_MOD, art_center(home, Side.SOLITAIRE))
    assert home.opened is None and not panel.isVisible()  # el clic afuera sólo cierra


def test_header_is_not_a_half(home):
    QTest.mouseClick(home, LEFT, NO_MOD, home.home_layout().header_rect.center().toPoint())
    assert home.opened is None


def test_play_emits_selected_chess_options(home):
    home.open_options(Side.CHESS)
    panel = home.panels[Side.CHESS]
    panel.buttons("Color")[ColorChoice.BLACK].click()
    panel.buttons("Dificultad")[Difficulty.MAXIMUM].click()
    got = []
    home.chess_requested.connect(lambda color, level: got.append((color, level)))
    panel.primary.click()
    assert got == [(ColorChoice.BLACK, Difficulty.MAXIMUM)] and home.opened is None


def test_enter_deals_solitaire_with_selected_draw(home):
    home.open_options(Side.SOLITAIRE)
    home.panels[Side.SOLITAIRE].buttons("Robo")[3].click()
    got = []
    home.solitaire_requested.connect(got.append)
    QTest.keyClick(home.panels[Side.SOLITAIRE].primary, Qt.Key.Key_Return)
    assert got == [3]


def test_missing_stockfish_disables_play(home, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "stockfish_path", tmp_path / "no_esta" / "stockfish.exe")
    home.open_options(Side.CHESS)
    panel = home.panels[Side.CHESS]
    assert not panel.primary.isEnabled()
    assert panel.message.isVisible() and "No se encontró Stockfish" in panel.message.text()
    got = []
    home.chess_requested.connect(lambda *args: got.append(args))
    QTest.keyClick(home, Qt.Key.Key_Return)
    assert got == []


def test_hover_animates_without_regenerating_pixmaps(home):
    home._rebuild_now()
    builds = home.layers.builds
    hover(home, art_center(home, Side.CHESS))
    assert wait_until(lambda: home.hover[Side.CHESS] == 1.0, timeout=1)
    assert home.hover[Side.SOLITAIRE] == 0.0
    hover(home, art_center(home, Side.SOLITAIRE))
    assert wait_until(lambda: home.hover[Side.SOLITAIRE] == 1.0 and home.hover[Side.CHESS] == 0.0, timeout=1)
    QApplication.sendEvent(home, QEvent(QEvent.Type.Leave))
    assert wait_until(lambda: home.hover[Side.SOLITAIRE] == 0.0, timeout=1)
    home.repaint()
    assert home.layers.builds == builds


def test_resize_regenerates_once_when_it_settles(home):
    home._rebuild_now()
    builds = home.layers.builds
    for width in (1050, 1100, 1150, 1200):
        home.resize(width, 760)
        home.repaint()  # mientras cambia: se estira la versión anterior, no se regenera
    assert home.layers.builds == builds
    assert wait_until(lambda: home.layers.builds == builds + 1, timeout=2)
    QTest.qWait(200)
    assert home.layers.builds == builds + 1 and home.layers.is_current(home.home_layout(), home.devicePixelRatioF())


def test_chess_panel_offers_six_levels_in_two_rows(home):
    home.open_options(Side.CHESS)
    QTest.qWait(20)
    buttons = home.panels[Side.CHESS].buttons("Dificultad")
    assert list(buttons) == list(Difficulty)
    assert [b.text() for b in buttons.values()] == ["Principiante", "Novato", "Aficionado", "Club", "Avanzado",
                                                    "Máximo"]
    assert home.panels[Side.CHESS].value("Dificultad") is Difficulty.BEGINNER  # default
    assert all("Elo" in b.toolTip() for d, b in buttons.items() if d is not Difficulty.MAXIMUM)
    tops = [b.geometry().top() for b in buttons.values()]
    assert tops[0] == tops[1] == tops[2] < tops[3] == tops[4] == tops[5]
