"""El arreglo de rendimiento: pixmaps cacheados por escala y repintado parcial al arrastrar."""
import chess
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest

from src.chess_game.board_view import BoardView
from src.chess_game.game_state import ChessGame
from src.solitaire.solitaire_screen import SolitaireScreen

LEFT, NO_MOD = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier


def test_solitaire_drag_reuses_cached_cards_and_resize_rerenders(qapp):
    from src.common.theme import MOTION

    screen = SolitaireScreen()
    screen.resize(1000, 720)
    screen.show()
    screen.deal(1)
    QTest.qWait(20)  # que se procese el cambio de página y la vista quede expuesta
    view = screen.view
    view.repaint()
    painter = view.painter
    assert painter.renders > 0
    rect = view.layout_().column_rects(screen.game, 6)[-1]
    start = rect.center().toPoint()
    QTest.mousePress(view, LEFT, NO_MOD, start)
    for i in range(1, 4):  # al levantarla se generan una vez su versión levantada y el resplandor de destino
        QTest.mouseMove(view, start + QPoint(i * 4, i))
        view.repaint()
    rendered = painter.renders
    for i in range(4, 40):
        QTest.mouseMove(view, start + QPoint(i * 4, i))
        view.repaint()
    assert view.drag is not None and view.drag.active
    assert painter.renders == rendered  # arrastrar no genera pixmaps nuevos
    QTest.mouseRelease(view, LEFT, NO_MOD, start)
    old = painter.assets
    screen.resize(800, 600)
    QTest.qWait(20)
    view.repaint()
    assert painter.assets is old  # mientras se redimensiona se estira lo que hay
    QTest.qWait(MOTION.rebuild_ms + 80)
    view.repaint()
    assert painter.assets is not old and painter.renders > rendered  # cambió la escala: se regeneran
    screen.close()


def test_chess_drag_and_drop_still_works_with_partial_updates(qapp):
    view = BoardView()
    view.resize(640, 640)
    view.show()
    view.set_game(ChessGame(chess.WHITE), flipped=False)
    view.set_interactive(True)
    QTest.qWait(20)
    moves = []
    view.move_attempted.connect(lambda a, b: moves.append((a, b)))
    g = view.geometry_()
    start, end = g.square_rect(chess.E2).center().toPoint(), g.square_rect(chess.E4).center().toPoint()
    QTest.mousePress(view, LEFT, NO_MOD, start)
    for i in range(1, 11):
        QTest.mouseMove(view, start + (end - start) * i / 10)
        view.repaint()
    rendered = view.total_renders
    QTest.mouseMove(view, end + QPoint(1, 1))
    view.repaint()
    assert view.total_renders == rendered  # arrastrar no genera pixmaps nuevos
    QTest.mouseRelease(view, LEFT, NO_MOD, end)
    assert moves == [(chess.E2, chess.E4)]


def test_chess_resize_stretches_then_rebuilds_once(qapp):
    from src.common.theme import MOTION

    view = BoardView()
    view.resize(640, 640)
    view.show()
    view.set_game(ChessGame(chess.WHITE), flipped=False)
    QTest.qWait(20)
    view.repaint()
    first = view.assets
    for side in range(650, 720, 10):  # arrastrando el borde de la ventana
        view.resize(side, side)
        view.repaint()
    assert view.assets is first  # mientras tanto se estira la versión anterior: nada se regenera
    QTest.qWait(MOTION.rebuild_ms + 80)
    view.repaint()
    assert view.assets is not first
    assert view.assets.matches(view.geometry_(), view.width(), view.height(), view.devicePixelRatioF())
    view.close()
