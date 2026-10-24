"""Un frame del tablero: copia, en píxeles físicos, la imagen del tablero y los sprites de `BoardAssets`.

Orden (blender/INTEGRACION.md): tintes ámbar (último movimiento, casilla elegida) y jaque; el suelo
(contacto + sombra) de todas las piezas; sus reflejos, recortados a las 8 x 8 casillas; las coordenadas; los
cuerpos (pieza + brillo) de la fila de atrás a la de adelante según la vista, con el halo (debajo) y el bloom
(encima) de la elegida; las
casillas legales; y por último la pieza levantada. No dibuja vectores."""
import chess
from PyQt6.QtCore import QPoint, QPointF, QRect, QSize
from PyQt6.QtGui import QColor, QPainter

from src.chess_game.art_library import ANCHOR_UP
from src.chess_game.board_assets import BoardAssets
from src.chess_game.board_painter import BoardGeometry
from src.chess_game.game_state import ChessGame
from src.common.theme import BOARD_LOOK, NEON, PIECE_LOOK

GHOST = 0.25  # opacidad de la pieza en su casilla mientras se la arrastra (sólo el cuerpo: está "arriba")
Step = tuple[str, chess.Square | None]  # capa: ground / reflection / labels / halo / body / bloom / ghost


def neon(alpha: float) -> QColor:
    color = QColor(NEON.color)
    color.setAlphaF(alpha)
    return color


def scene_order(board: chess.Board, g: BoardGeometry, selected: chess.Square | None, dragging: bool) -> list[Step]:
    """Qué se dibuja y en qué orden. La pieza arrastrada deja en su casilla sólo el fantasma del cuerpo."""
    squares = sorted(board.piece_map(), key=lambda sq: g.cell(sq)[::-1])  # (fila, columna): de atrás adelante
    lifted = selected if dragging else None
    resting = [sq for sq in squares if sq != lifted]
    order = [("ground", sq) for sq in resting] + [("reflection", sq) for sq in resting] + [("labels", None)]
    for sq in squares:
        if sq == lifted:
            order.append(("ghost", sq))
            continue
        if sq == selected:
            order += [("halo", sq), ("body", sq), ("bloom", sq)]
        else:
            order.append(("body", sq))
    return order


def lifted_anchor(assets: BoardAssets, center: QPointF) -> QPoint:
    """Apoyo de la pieza levantada para que la pieza quede centrada en `center` (px físicos)."""
    rise = (0.5 - ANCHOR_UP) * assets.square * PIECE_LOOK.lift_scale
    return QPoint(round(center.x()), round(center.y() + rise))


def lifted_rect(assets: BoardAssets, piece: chess.Piece, center: QPointF) -> QRect:
    return assets.lifted(piece).rect(lifted_anchor(assets, center))


def _draw(p: QPainter, sprite, anchor: QPoint, clip: QRect, board_area: QRect | None = None,
          plus: bool = False) -> None:
    """Copia el sprite si toca la región a repintar. `board_area`: recortado a las casillas (reflejos)."""
    rect = sprite.rect(anchor)
    if not clip.intersects(rect):
        return
    if board_area is None and not plus:
        p.drawPixmap(rect.topLeft(), sprite.pixmap)
        return
    p.save()
    if board_area is not None:
        p.setClipRect(board_area)
    if plus:
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
    p.drawPixmap(rect.topLeft(), sprite.pixmap)
    p.restore()


def _under_pieces(p: QPainter, assets: BoardAssets, game: ChessGame, selected: chess.Square | None) -> None:
    """Tintes ámbar (último movimiento, casilla elegida) y el jaque, sobre el tablero."""
    last, side = game.last_move, QSize(assets.square, assets.square)
    tints = [(sq, BOARD_LOOK.last_move) for sq in ((last.from_square, last.to_square) if last else ())]
    if selected is not None:
        tints.append((selected, BOARD_LOOK.selected))
    for sq, alpha in tints:
        p.fillRect(QRect(assets.cell_origin(sq), side), neon(alpha))
    check = game.checked_king_square()
    if check is not None:
        p.drawPixmap(assets.cell_origin(check), assets.check().pixmap)


def paint_position(p: QPainter, assets: BoardAssets, game: ChessGame, selected: chess.Square | None,
                   targets: set[chess.Square], drag_center: QPointF | None, clip: QRect,
                   toppled: chess.Square | None = None) -> None:
    """`toppled`: el rey vencido por jaque mate, que se dibuja acostado en su casilla."""
    board, area = game.board, assets.board_area
    _under_pieces(p, assets, game, selected)
    for kind, sq in scene_order(board, assets.g, selected, drag_center is not None):
        if kind == "labels":
            for corner, label in assets.labels:
                if clip.intersects(QRect(corner, label.size())):
                    p.drawPixmap(corner, label)
            continue
        piece, anchor = board.piece_at(sq), assets.anchor(sq)
        resting = assets.toppled(piece.color) if sq == toppled else assets.rest(piece)
        if kind == "ghost":
            p.setOpacity(GHOST)
            _draw(p, assets.rest(piece).body, anchor, clip)
            p.setOpacity(1.0)
        elif kind == "halo":
            _draw(p, assets.halo(piece), anchor, clip)
        elif kind == "bloom":
            _draw(p, assets.bloom(piece), anchor, clip, plus=True)
        elif kind == "reflection":  # el reflejo no cae sobre el marco ni sobre la mesa
            _draw(p, resting.reflection, anchor, clip, area)
        else:
            _draw(p, getattr(resting, kind), anchor, clip)
    for sq in targets:
        mark = assets.ring() if board.piece_at(sq) is not None else assets.dot()
        p.drawPixmap(assets.cell_origin(sq), mark.pixmap)
    if drag_center is not None:
        sprites, anchor = assets.lifted(board.piece_at(selected)), lifted_anchor(assets, drag_center)
        _draw(p, sprites.ground, anchor, clip)
        _draw(p, sprites.reflection, anchor, clip, area)
        _draw(p, sprites.body, anchor, clip)
