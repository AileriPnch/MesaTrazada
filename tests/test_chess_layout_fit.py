"""Mesa del ajedrez sin cortes ni superposiciones, de 800x600 a 1920x1080 (125/150 %: correr con QT_SCALE_FACTOR):
ningún objeto pisa a otro (el reloj tampoco al cartel del rival), ni al tablero, ni la esquina del volumen; los
textos entran en sus placas, carteles, planilla y tarjeta; el tablero entra entero con casillas de px enteros."""
import chess
import pytest
from PyQt6.QtCore import QRect, QRectF
from PyQt6.QtGui import QFontMetricsF
from PyQt6.QtTest import QTest

from src.app.stylesheet import apply_theme
from src.chess_game.board_painter import BoardGeometry
from src.chess_game.chess_dialogs import MessageDialog
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from src.chess_game.promotion_dialog import PromotionDialog
from tests.fakes import FakeEngine, factory_for
from tests.test_layout_fit import SIZES, clipped

LONGEST_SAN = ["exd8=Q+", "Qxf7+", "Nbxd7", "O-O-O+"]


@pytest.fixture
def screen(qapp):
    apply_theme(qapp)
    s = ChessScreen(engine_factory=factory_for(FakeEngine()))
    s.start_game(ColorChoice.WHITE, Difficulty.ADVANCED)
    yield s
    s.shutdown()
    s.close()


def fits(rect: QRectF, text: str, font) -> bool:
    metrics = QFontMetricsF(font)
    return metrics.horizontalAdvance(text) <= rect.width() and metrics.height() <= rect.height() + 1


@pytest.mark.parametrize("size", SIZES)
def test_table_objects_never_overlap_and_the_board_is_whole(screen, size):
    screen.resize(*size)
    screen.show()
    QTest.qWait(30)
    side, view = screen.side, screen.board_view
    g = view.geometry_()
    assert view.rect().toRectF().contains(g.frame_rect)  # el tablero entra entero, con su marco
    assert g.square >= 40
    frame = g.frame_rect.translated(view.pos().toPointF()).toAlignedRect()
    rects = {name: getattr(side, name).geometry() for name in
             ("tray_rival", "tray_own", "rival_plate", "clock", "sheet", "own_plate", "new_game_button", "undo_button",
              "back_button")}
    rects["tablero"] = frame
    rects["volumen"] = screen.table.corner.toAlignedRect()
    names = list(rects)
    for i, a in enumerate(names):
        assert screen.rect().contains(rects[a]), a
        for b in names[i + 1:]:
            assert not rects[a].intersects(rects[b]), (a, b)
    clock = side.clock
    drawn = clock.at.rect(clock.box())  # lo que se ve del reloj (botones incluidos), dentro de su lugar
    assert QRectF(clock.rect()).adjusted(-1, -1, 1, 1).contains(drawn)


@pytest.mark.parametrize("size", SIZES)
def test_texts_fit_on_plates_sheet_and_card(screen, size):
    screen.resize(*size)
    screen.show()
    QTest.qWait(30)
    side = screen.side
    for button in (side.new_game_button, side.undo_button, side.back_button):
        assert fits(button.face(), button.text(), button.text_font()), button.text()
    side.rival_plate.set_text("Principiante · ≈500")  # el más largo
    for plate in (side.rival_plate, side.own_plate):
        assert fits(plate.face(), plate.text, plate.text_font()), plate.text
    sheet = side.sheet
    assert sheet.hand_font().pixelSize() >= 13  # la letra a mano, nunca más chica
    for san in LONGEST_SAN:
        assert QFontMetricsF(sheet.hand_font()).horizontalAdvance(san) <= sheet.move_cell_width(), san
    side.show_card("Ganó Stockfish", "Regla de los 50 movimientos · ½–½")
    QTest.qWait(20)
    card = side.card
    assert card.isVisible() and card.geometry().intersects(sheet.geometry())
    assert QRect(screen.rect()).contains(card.geometry())


def test_square_is_whole_physical_pixels_at_fractional_scales():
    for dpr in (1.0, 1.25, 1.5):
        g = BoardGeometry.fit(733, 701, False, dpr)
        assert abs(g.square * dpr - round(g.square * dpr)) < 1e-9
        assert abs(g.left * dpr - round(g.left * dpr)) < 1e-9 and abs(g.top * dpr - round(g.top * dpr)) < 1e-9


@pytest.mark.parametrize("size", [(800, 600), (1920, 1080)])
def test_dialogs_fit(screen, size):
    screen.resize(*size)
    screen.show()
    for dialog in (PromotionDialog(chess.WHITE, screen),
                   MessageDialog(screen, screen.u, "Error del motor", "Stockfish dejó de responder: proceso cerrado")):
        dialog.show()
        QTest.qWait(20)
        assert clipped(dialog) == [], type(dialog).__name__
        assert screen.window().frameGeometry().contains(dialog.frameGeometry())
        dialog.reject()
