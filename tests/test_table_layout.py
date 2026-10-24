"""Disposición de la mesa del ajedrez (función pura) y material capturado (lógica pura)."""
import chess
import pytest
from PyQt6.QtCore import QRectF

from src.chess_game.material import balance, lost_pieces
from src.chess_game.table_layout import table_layout
from src.common.theme import TABLE_LOOK

SIZES = [(800, 600), (900, 900), (1000, 720), (1024, 768), (1280, 720), (1366, 768), (1536, 864), (1920, 1009),
         (1920, 1080), (2560, 1080), (2560, 1440), (3440, 1440)]


@pytest.mark.parametrize("dpr", [1.0, 1.25, 1.5])
@pytest.mark.parametrize("size", SIZES)
def test_objects_fit_the_window_and_never_overlap(size, dpr):
    w, h = size
    t = table_layout(w, h, dpr)
    rects = dict(t.objects, tablero=t.frame, volumen=t.corner)
    window = QRectF(0, 0, w, h)
    names = list(rects)
    for i, a in enumerate(names):
        assert window.contains(rects[a]), a
        for b in names[i + 1:]:
            assert not rects[a].intersects(rects[b]), (a, b)  # el reloj tampoco pisa el cartel del rival
    assert QRectF(t.board_view).contains(t.frame)
    assert t.sheet.height() >= 3 * t.s  # la planilla siempre tiene lugar para sus renglones
    assert t.s * dpr == pytest.approx(round(t.s * dpr))  # casillas de px físicos enteros


@pytest.mark.parametrize("size", SIZES)
def test_trays_are_centered_on_their_half_of_the_board(size):
    t = table_layout(*size)
    board_top = t.frame.top() + 0.2 * t.s  # el marco mide 0,2 casillas
    for tray, half in ((t.tray_rival, 0), (t.tray_own, 1)):
        assert tray.height() <= TABLE_LOOK.tray_h * t.s + 0.5  # no son columnas vacías gigantes
        assert tray.center().y() == pytest.approx(board_top + (half + 0.5) * 4 * t.s, abs=1)
        assert tray.left() > t.frame.right()


def test_small_windows_keep_a_playable_board():
    assert table_layout(800, 600).s >= 55
    assert table_layout(1000, 720).s >= 68


def test_lost_pieces_and_material_balance():
    board = chess.Board()
    for san in ("e4", "d5", "exd5", "Qxd5", "Nc3", "Qxa2", "Rxa2"):
        board.push_san(san)
    assert lost_pieces(board, chess.WHITE) == [chess.Piece(chess.PAWN, chess.WHITE)] * 2
    black = chess.BLACK
    assert lost_pieces(board, black) == [chess.Piece(chess.QUEEN, black), chess.Piece(chess.PAWN, black)]
    assert balance(board, chess.WHITE) == 9 + 1 - 2


def test_promotion_is_not_a_capture():
    board = chess.Board("8/P6k/8/8/8/8/1PPPPPPP/RNBQKBNR w KQ - 0 1")  # a las blancas les falta 1 peón (a7)
    assert lost_pieces(board, chess.WHITE) == []
    board.push_san("a8=Q")
    assert lost_pieces(board, chess.WHITE) == []  # la dama nueva "devuelve" el peón que coronó
    assert balance(board, chess.WHITE) == 7 * 1 + 2 * 9 + 2 * 5 + 2 * 3 + 2 * 3  # 7 peones, 2 damas...; negras: rey
