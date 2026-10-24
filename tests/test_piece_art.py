"""Arte renderizado del ajedrez (Blender): archivos, medidas, apoyo, orden de dibujo, reflejos recortados al
tablero, pieza levantada, bloom de la elegida, tablero igual con negras y carga diferida."""
import os
import subprocess
import sys
from pathlib import Path

import chess
import pytest
from PyQt6.QtCore import QPoint, QPointF, QRect, Qt
from PyQt6.QtGui import QBitmap, QColor, QImage, QPainter, QPixmap, QRegion

from src.chess_game.art_library import (ANCHOR_UP, ART_DIR, BOARD_FRAME, BOARD_SQUARE, LAYERS, SPRITE_SQUARE,
                                        all_pieces, file_name, library)
from src.chess_game.board_glare import _square_means, glare_excess
from src.chess_game.board_assets import BoardAssets
from src.chess_game.board_painter import BoardGeometry, render_board
from src.chess_game.board_scene import paint_position, scene_order
from src.chess_game.game_state import ChessGame
from src.chess_game.piece_painter import piece_icon
from src.chess_game.piece_sprites import PieceSprites, Sprite
from src.common.theme import BOARD_LOOK, PIECE_LOOK

# Alto de cada pieza en casillas medido en los PNG (alfa >= 50 %, escala de 426,67 px por casilla). La tabla de
# blender/INTEGRACION.md da otros valores (rey 0,892, torre 0,719 < caballo 0,759): no coincide con los renders.
HEIGHTS = {chess.KING: 0.809, chess.QUEEN: 0.745, chess.BISHOP: 0.712, chess.KNIGHT: 0.689, chess.ROOK: 0.691,
           chess.PAWN: 0.600}


def bounds(image: QImage, min_alpha: int = 128) -> QRect:
    """Caja de lo que tiene alfa >= min_alpha (recorre los píxeles: usar con sprites chicos)."""
    xs, ys = [], []
    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y).alpha() >= min_alpha:
                xs.append(x)
                ys.append(y)
    return QRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1) if xs else QRect()


def mask_bounds(image: QImage) -> QRect:
    """Caja de lo que tiene alfa >= 50 %, rápida (para los renders de 512 px)."""
    mask = image.convertToFormat(QImage.Format.Format_ARGB32).createAlphaMask(Qt.ImageConversionFlag.ThresholdAlphaDither)
    return QRegion(QBitmap.fromImage(mask)).boundingRect()


def make_assets(flipped: bool = False, size: int = 640) -> BoardAssets:
    g = BoardGeometry.fit(size, size, flipped)
    return BoardAssets(g, size, size, 1.0)


def test_all_art_files_exist_with_the_documented_sizes(qapp):
    for piece in all_pieces():
        for layer in LAYERS:
            image = QImage(str(ART_DIR / file_name(piece, layer)))
            assert (image.width(), image.height()) == (512, 512), file_name(piece, layer)
    assert QImage(str(ART_DIR / "tablero.png")).size().width() == 2048
    table = QImage(str(ART_DIR / "mesa.png"))
    assert (table.width(), table.height()) == (3840, 2880)


@pytest.mark.parametrize("color", chess.COLORS)
def test_heights_and_order_of_the_rendered_pieces(qapp, color):
    """Rey > dama > alfil > caballo ≈ torre > peón; las dos colores con las mismas medidas."""
    art = library()
    heights = {t: mask_bounds(art.layer(chess.Piece(t, color))).height() / SPRITE_SQUARE for t in HEIGHTS}
    for piece_type, expected in HEIGHTS.items():
        assert heights[piece_type] == pytest.approx(expected, abs=0.01), chess.piece_name(piece_type)
    h = heights
    assert h[chess.KING] > h[chess.QUEEN] > h[chess.BISHOP] > max(h[chess.KNIGHT], h[chess.ROOK])
    assert min(h[chess.KNIGHT], h[chess.ROOK]) > h[chess.PAWN]


def test_on_the_board_the_king_is_about_089_of_its_square(qapp):
    """En el tablero las piezas van a BOARD_LOOK.piece_scale de la escala del render: el rey ~0,89."""
    assets = make_assets()
    for piece_type, measured in HEIGHTS.items():
        body = assets.rest(chess.Piece(piece_type, chess.WHITE)).body.pixmap.toImage()
        expected = measured * BOARD_LOOK.piece_scale
        assert bounds(body).height() / assets.square == pytest.approx(expected, abs=0.03), chess.piece_name(piece_type)
    king = assets.rest(chess.Piece(chess.KING, chess.BLACK)).body.pixmap.toImage()
    assert bounds(king).height() / assets.square == pytest.approx(0.89, abs=0.02)


def test_the_render_glare_is_removed_without_touching_the_rest(qapp):
    """El velo de b6-b7 del render agrisaba las casillas (mancha oscura): después de sacarlo, ninguna casilla
    se aparta de la caída normal de la luz, y lejos del brillo los colores no cambian."""
    original = QImage(str(ART_DIR / "tablero.png")).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    assert max(sum(v) for v in glare_excess(original, BOARD_SQUARE, BOARD_FRAME).values()) > 40  # el render lo trae
    fixed = library().board
    assert max(sum(v) for v in glare_excess(fixed, BOARD_SQUARE, BOARD_FRAME).values()) < 16  # ~5 por canal
    before, after = _square_means(original, BOARD_SQUARE, BOARD_FRAME), _square_means(fixed, BOARD_SQUARE, BOARD_FRAME)
    for cell in ((4, 4), (6, 6), (7, 7), (5, 2)):  # e4, g2, h1, f6: lejos del brillo
        assert all(abs(a - b) <= 1 for a, b in zip(before[cell], after[cell])), cell
    b6, d6 = after[(1, 2)], after[(3, 2)]  # oscuras: b6 vuelve a ser azul pizarra como d6
    assert (b6[2] - b6[0]) >= 0.8 * (d6[2] - d6[0])


@pytest.mark.parametrize("flipped", [False, True])
def test_pieces_stand_on_their_anchor_and_the_king_fits_its_square(qapp, flipped):
    assets = make_assets(flipped)
    s = assets.square
    for sq in (chess.E1, chess.E8, chess.A1, chess.H8):
        cell = QRect(assets.cell_origin(sq), QPixmap(s, s).size())
        anchor = assets.anchor(sq)
        assert anchor.x() == pytest.approx(cell.center().x(), abs=1)
        assert cell.bottom() + 1 - anchor.y() == pytest.approx(ANCHOR_UP * s, abs=1)
        king = assets.rest(chess.Piece(chess.KING, chess.WHITE)).body
        box = bounds(king.pixmap.toImage()).translated(king.rect(anchor).topLeft())
        assert box.top() >= cell.top() and box.bottom() <= cell.bottom()  # el rey entra completo


def test_draw_order_grounds_then_reflections_then_labels_then_bodies_back_to_front():
    board = chess.Board()
    for flipped in (False, True):
        g = BoardGeometry.fit(640, 640, flipped)
        order = scene_order(board, g, None, dragging=False)
        kinds = [kind for kind, _ in order]
        n = len(board.piece_map())
        assert kinds == ["ground"] * n + ["reflection"] * n + ["labels"] + ["body"] * n
        rows = [g.cell(sq)[1] for kind, sq in order if kind == "body"]
        assert rows == sorted(rows)  # de la fila de atrás (arriba en pantalla) a la de adelante
        first_rank = 7 if not flipped else 0  # arriba en pantalla: la octava con blancas, la primera con negras
        assert chess.square_rank(order[-n][1]) == first_rank


def test_selected_piece_gets_halo_and_bloom_and_the_dragged_one_leaves_only_a_ghost():
    board, g = chess.Board(), BoardGeometry.fit(640, 640, False)
    order = scene_order(board, g, chess.E2, dragging=False)
    at = order.index(("body", chess.E2))
    assert order[at - 1] == ("halo", chess.E2) and order[at + 1] == ("bloom", chess.E2)
    dragging = scene_order(board, g, chess.E2, dragging=True)
    assert ("ghost", chess.E2) in dragging
    assert not [step for step in dragging if step[1] == chess.E2 and step[0] != "ghost"]  # sin suelo ni reflejo


def _paint(assets: BoardAssets, game: ChessGame) -> QImage:
    w, h = assets.size
    image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor("black"))
    p = QPainter(image)
    p.drawPixmap(0, 0, assets.board)
    paint_position(p, assets, game, None, set(), None, QRect(0, 0, w, h))
    p.end()
    return image


def test_reflections_never_paint_the_frame(qapp):
    """Reflejos reemplazados por rojo puro: nada rojo fuera de las 8 x 8 casillas (la primera fila cae sobre
    el marco si no se recorta)."""
    assets = make_assets()
    game = ChessGame(chess.WHITE)
    for piece in set(game.board.piece_map().values()):
        rest = assets.rest(piece)
        red = QPixmap(rest.reflection.pixmap.size())
        red.fill(QColor(255, 0, 0))
        assets._items[("rest", piece)] = PieceSprites(rest.ground, Sprite(red, rest.reflection.offset), rest.body)
    image, area = _paint(assets, game), assets.board_area
    reflection = assets.rest(chess.Piece(chess.ROOK, chess.WHITE)).reflection.rect(assets.anchor(chess.A1))
    assert reflection.bottom() > area.bottom()  # sin recorte caería sobre el marco
    for y in range(area.bottom() + 1, min(image.height(), reflection.bottom() + 1)):
        for x in range(area.left(), area.right() + 1, 3):
            assert image.pixelColor(x, y) != QColor(255, 0, 0), (x, y)


def test_board_image_is_the_same_from_both_sides(qapp):
    """Con negras el tablero se ve igual (a1 y h8 son oscuras): sólo cambian coordenadas y piezas."""
    art = library()
    images = [render_board(BoardGeometry.fit(500, 500, flipped), 500, 500, 1.0, art.board) for flipped in (0, 1)]
    assert images[0] == images[1]


def test_lifted_piece_is_bigger_without_contact_and_its_shadow_moves_away(qapp):
    assets = make_assets()
    piece = chess.Piece(chess.QUEEN, chess.BLACK)
    rest, lifted = assets.rest(piece), assets.lifted(piece)
    rest_box, lifted_box = bounds(rest.body.pixmap.toImage()), bounds(lifted.body.pixmap.toImage())
    assert lifted_box.height() / rest_box.height() == pytest.approx(PIECE_LOOK.lift_scale, abs=0.03)

    def centroid(sprite: Sprite) -> QPointF:
        box = bounds(sprite.pixmap.toImage(), 40).translated(sprite.offset)
        return QPointF(box.center()) / assets.square  # respecto del apoyo, en casillas

    assert centroid(lifted.ground).x() > centroid(rest.ground).x() + 0.05  # lejos de la luz
    assert centroid(lifted.ground).y() > centroid(rest.ground).y() + 0.05
    gap = PIECE_LOOK.lift_reflection_gap * assets.square  # menos lo que sube el apoyo del reflejo al agrandarse
    assert lifted.reflection.offset.y() - rest.reflection.offset.y() >= gap - 2
    base = rest.ground.pixmap.toImage()  # el contacto (oscuro justo bajo la base) no está en la levantada
    under = -rest.ground.offset + QPoint(0, round(0.05 * assets.square))
    assert base.pixelColor(under).alphaF() > 0.5


def test_bloom_of_the_selected_piece_is_amber(qapp):
    bloom = make_assets().bloom(chess.Piece(chess.KING, chess.WHITE)).pixmap.toImage()
    box = bloom.rect()
    colors = [bloom.pixelColor(x, y) for y in range(box.top(), box.bottom(), 2) for x in range(box.left(), box.right(), 2)]
    lit = [c for c in colors if c.alpha() > 10]
    assert lit
    r, g, b = (sum(getattr(c, ch)() for c in lit) for ch in ("red", "green", "blue"))
    assert r > g > b  # ámbar


def test_promotion_icon_fills_its_square(qapp):
    icon = piece_icon(chess.Piece(chess.KING, chess.BLACK), 72).toImage()
    box = bounds(icon)
    assert box.height() >= 68 and abs(box.center().x() - 36) <= 2


def test_home_loads_only_piece_bodies_and_the_rest_waits_for_chess(tmp_path):
    """Proceso aparte (estado limpio): el inicio no carga la mesa ni el tablero; abrir las opciones del
    ajedrez los precarga; abrir el ajedrez los deja cargados."""
    script = """
import sys
sys.path.insert(0, r"%s")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
app = QApplication([])
from src.chess_game import art_library
from src.app.home.home_layout import Side
from src.app.home.home_screen import HomeScreen
home = HomeScreen(); home.resize(1000, 720); home.show(); QTest.qWait(200)
print("inicio", art_library.is_loaded(), len(art_library._bodies))
home.open_options(Side.CHESS)
art_library.library()
print("ajedrez", art_library.is_loaded())
""" % Path(__file__).resolve().parent.parent
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, timeout=60)
    assert out.returncode == 0, out.stderr
    lines = out.stdout.split("\n")
    home_line = next(line for line in lines if line.startswith("inicio")).split()
    assert home_line[1] == "False" and 0 < int(home_line[2]) <= 12  # sólo los cuerpos que dibuja
    assert "ajedrez True" in out.stdout
