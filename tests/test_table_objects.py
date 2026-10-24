"""Objetos de la mesa del ajedrez: planilla (hojas, rueda, RePág/AvPág, resultado), reloj (turno, luz de
Stockfish, final), placas (teclado, deshabilitada), tarjeta (Esc / clic), rey acostado, perilla del volumen sólo
en el ajedrez, contraste del texto (WCAG) y que pintar no genere pixmaps nuevos."""
import json

import chess
import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QColor, QImage, QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from src.chess_game.art_library import ART_DIR
from src.chess_game.board_assets import BoardAssets
from src.chess_game.board_painter import BoardGeometry
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from src.common.theme import COLORS
from tests.fakes import FakeEngine, factory_for
from tests.test_piece_art import bounds

INFO = json.loads((ART_DIR / "interfaz" / "interfaz.json").read_text(encoding="utf-8"))["sprites"]


@pytest.fixture
def screen(qapp):
    s = ChessScreen(engine_factory=factory_for(FakeEngine(delay=600)))  # el motor "piensa" sin responder
    s.resize(1280, 800)
    s.show()
    s.start_game(ColorChoice.WHITE, Difficulty.NOVICE)
    QTest.qWait(30)
    yield s
    s.shutdown()
    s.close()


def wheel(widget, up: bool) -> None:
    pos = QPointF(widget.width() / 2, widget.height() / 2)
    event = QWheelEvent(pos, widget.mapToGlobal(pos), QPoint(), QPoint(0, 120 if up else -120),
                        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(widget, event)


def test_sheet_pages_wheel_keys_and_result(screen):
    sheet = screen.side.sheet
    rows = INFO["planilla"]["filas"]
    sheet.set_moves(["e4", "e5"] * (rows + 3))  # una hoja y algo más
    assert sheet.pages == 2 and sheet.page == 1  # se ve la hoja de la última jugada
    wheel(sheet, up=True)
    assert sheet.page == 0
    wheel(sheet, up=True)
    assert sheet.page == 0  # no hay hoja anterior
    sheet.setFocus()
    QTest.keyClick(sheet, Qt.Key.Key_PageDown)
    assert sheet.page == 1
    sheet.set_moves(["e4"])
    assert sheet.pages == 1 and sheet.page == 0


def test_clock_shows_whose_turn_and_lights_while_stockfish_thinks(screen):
    clock = screen.side.clock
    assert clock.state == "negras" and clock.thinking is None  # mueven las blancas: el último botón fue el negro
    screen._push(chess.Move.from_uci("e2e4"))
    assert clock.state == "blancas" and clock.thinking == chess.BLACK
    assert "pensando" in screen.side.status_text and "pensando" in clock.toolTip()
    clock.set_over()
    assert clock.state == "parejos" and clock.thinking is None


def test_brass_plates_click_with_keyboard_and_disable(screen):
    side = screen.side
    clicks = []
    side.new_game_requested.connect(lambda: clicks.append("nueva"))
    for key in (Qt.Key.Key_Return, Qt.Key.Key_Space):
        side.new_game_button.setFocus()
        QTest.keyClick(side.new_game_button, key)
        QTest.qWait(200)  # animateClick
    assert clicks == ["nueva", "nueva"]
    assert not side.undo_button.isEnabled() and side.undo_button.state == "disabled"  # sin jugadas
    assert side.back_button.text() == "Menú"
    assert side.new_game_button.focusPolicy() == Qt.FocusPolicy.StrongFocus  # se llega con Tab


def test_card_shows_over_the_sheet_and_escape_or_click_lifts_it(screen):
    card = screen.side.card
    screen.side.show_card("Tablas", "Ahogado · ½–½")
    assert card.isVisible() and card.geometry().intersects(screen.side.sheet.geometry())
    QTest.keyClick(card, Qt.Key.Key_Escape)
    assert card.isHidden()
    screen.side.show_card("Tablas", "Ahogado · ½–½")
    QTest.mouseClick(card, Qt.MouseButton.LeftButton)
    assert card.isHidden()


def test_checkmate_lays_the_king_down(screen, qapp):
    game = screen.game
    for san in ("f3", "e5", "g4", "Qh4#"):
        game.push(game.board.parse_san(san))
    screen._advance()
    assert screen.board_view.toppled == chess.E1
    g = BoardGeometry.fit(640, 640, False)
    body = bounds(BoardAssets(g, 640, 640, 1.0).toppled(chess.WHITE).body.pixmap.toImage())
    assert body.width() > body.height()  # acostado: más ancho que alto


def test_painting_the_table_twice_generates_nothing_new(screen):
    screen.repaint()
    QTest.qWait(20)
    for widget in screen.side.objects:
        widget.repaint()
    made = screen.sprites.renders
    for widget in screen.side.objects:
        widget.repaint()
    assert screen.sprites.renders == made


def test_volume_knob_only_in_chess(qapp):
    from src.app.main_window import MainWindow

    class FakeChess(ChessScreen):
        def __init__(self):
            super().__init__(engine_factory=factory_for(FakeEngine()))

    window = MainWindow()
    try:
        button = window.volume_control.button
        assert button.skin is None  # inicio: el parlante
        window.open_game(FakeChess)
        assert button.skin is window.game.volume_skin  # ajedrez: perilla de latón
        window.open_solitaire(1)
        assert button.skin is None
        window.open_game(FakeChess)
        window.show_menu()
        assert button.skin is None
    finally:
        window.close()


def _luminance(color: QColor) -> float:
    def channel(v: int) -> float:
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(color.red()) + 0.7152 * channel(color.green()) + 0.0722 * channel(color.blue())


def _contrast(a: QColor, b: QColor) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _mean(name: str, box) -> QColor:
    image = QImage(str(ART_DIR / "interfaz" / name))
    x0, y0, x1, y1 = (int(v) for v in box)
    colors = [image.pixelColor(x, y) for y in range(y0, y1, 3) for x in range(x0, x1, 3)]
    return QColor(*(round(sum(getattr(c, k)() for c in colors) / len(colors)) for k in ("red", "green", "blue")))


def test_text_contrast_on_paper_and_brass(qapp):
    paper = _mean("planilla.png", INFO["planilla"]["papel"])
    assert _contrast(paper, QColor(COLORS.pen_ink)) >= 7  # la tinta
    assert _contrast(paper, QColor(COLORS.print_ink)) >= 4.5  # lo impreso
    assert _contrast(_mean("tarjeta.png", INFO["tarjeta"]["texto"]), QColor(COLORS.pen_ink)) >= 7
    engrave = QColor(COLORS.engrave)
    for key in ("placa_principal", "placa_secundaria"):
        for state, minimum in (("normal", 4.5), ("hover", 4.5), ("pressed", 4.5), ("disabled", 3.0)):
            face = _mean(f"{key}_{state}.png", INFO[key]["cara"])
            assert _contrast(face, engrave) >= minimum, (key, state)
    assert _contrast(_mean("cartel.png", INFO["cartel"]["cara"]), engrave) >= 4.5
    assert _contrast(_mean("bandeja.png", INFO["bandeja"]["fieltro"]), QColor(COLORS.text)) >= 4.5  # el "+N"


def test_board_is_the_real_render_without_glare_and_with_the_code_gloss(qapp, monkeypatch):
    """La mesa usa tablero.png de verdad: sin el velo de b6-b7 (board_glare) y con el brillo claro por código."""
    from dataclasses import replace

    from src.chess_game import art_library, board_painter

    art = art_library.library()
    raw = QImage(str(ART_DIR / "tablero.png")).convertToFormat(art.board.format())
    assert art.board != raw  # al cargar se le sacó el velo
    g = BoardGeometry.fit(640, 640, False)
    lit = board_painter.render_board(g, 640, 640, 1.0, art.board)
    monkeypatch.setattr(board_painter, "BOARD_LOOK", replace(board_painter.BOARD_LOOK, gloss=0.0))
    flat = board_painter.render_board(g, 640, 640, 1.0, art.board)
    corner = g.square_rect(chess.B7).center().toPoint()  # arriba a la izquierda: donde va el brillo
    assert _luminance(lit.pixelColor(corner)) > _luminance(flat.pixelColor(corner))
