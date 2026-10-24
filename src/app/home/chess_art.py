"""Tablero de ajedrez en perspectiva (QTransform) con unas pocas piezas de una partida avanzada (las piezas
son los renders del juego: sólo sus cuerpos, ver art_library)."""
from dataclasses import dataclass

import chess
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QRadialGradient,
                         QTransform)

from src.common.glow import blurred
from src.chess_game.piece_painter import ground_ratio, piece_pixmap
from src.common.theme import COLORS

POSITION = "4r1k1/5pp1/2n2q1p/3p4/3P4/2N2N1P/5PP1/3R2K1"  # medio juego avanzado, blancas abajo
TOP_RATIO = 0.64  # ancho del borde lejano / borde cercano
DEPTH_RATIO = 0.5  # profundidad en pantalla / borde cercano
FRAME = 0.45  # marco, en casillas
THICKNESS = 0.03  # canto del tablero, relativo al borde cercano
PIECE_SCALE = 1.45  # lado del sprite / ancho de su casilla (el render cubre 1,2: un poco más grandes, se leen)
PIECE_RENDER = 160  # px: el render se reduce una vez a este tamaño y después a cada casilla


@dataclass(frozen=True)
class BoardPose:
    transform: QTransform  # casillas (x = columna 0..8, y = fila 0..8 desde la octava) → pantalla
    near_width: float

    def at(self, x: float, y: float) -> QPointF:
        return self.transform.map(QPointF(x, y))

    def quad(self, x0: float, y0: float, x1: float, y1: float) -> QPolygonF:
        return QPolygonF([self.at(x0, y0), self.at(x1, y0), self.at(x1, y1), self.at(x0, y1)])

    @property
    def edge(self) -> QPolygonF:
        """Canto delantero (el grosor del tablero)."""
        a, b = self.at(-FRAME, 8 + FRAME), self.at(8 + FRAME, 8 + FRAME)
        down = QPointF(0, self.near_width * THICKNESS)
        return QPolygonF([a, b, b + down, a + down])

    @property
    def outline(self) -> QPainterPath:
        """Silueta del tablero (marco + canto): ahí se enciende el neón."""
        path = QPainterPath()
        path.addPolygon(self.quad(-FRAME, -FRAME, 8 + FRAME, 8 + FRAME))
        edge = QPainterPath()
        edge.addPolygon(self.edge)
        return path.united(edge).simplified()


def board_pose(area: QRectF, max_width: float) -> BoardPose:
    """Tablero centrado en `area`, con el borde cercano de hasta `max_width` de ancho."""
    overhang = TOP_RATIO / (8 + 2 * FRAME) * PIECE_SCALE  # piezas de la fila lejana sobre el borde
    near = min(max_width, area.height() / (DEPTH_RATIO + overhang + THICKNESS + 0.02))
    top = area.top() + (area.height() - near * (DEPTH_RATIO + overhang + THICKNESS)) / 2 + near * overhang
    cx, far = area.center().x(), near * TOP_RATIO
    target = QPolygonF([QPointF(cx - far / 2, top), QPointF(cx + far / 2, top),
                        QPointF(cx + near / 2, top + near * DEPTH_RATIO), QPointF(cx - near / 2, top + near * DEPTH_RATIO)])
    source = QPolygonF([QPointF(-FRAME, -FRAME), QPointF(8 + FRAME, -FRAME),
                        QPointF(8 + FRAME, 8 + FRAME), QPointF(-FRAME, 8 + FRAME)])
    transform = QTransform()
    QTransform.quadToQuad(source, target, transform)
    return BoardPose(transform, near)


def _board_shadow(p: QPainter, pose: BoardPose, bounds: QRectF, dpr: float) -> None:
    def draw(q: QPainter) -> None:
        q.translate(-bounds.left(), -bounds.top() + pose.near_width * 0.03)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(0, 0, 0, 200))
        q.drawPath(pose.outline)

    p.drawImage(bounds.topLeft(), blurred(bounds.width(), bounds.height(), dpr, pose.near_width * 0.035, draw))


def _piece_shadow(p: QPainter, base: QPointF, width: float) -> None:
    gradient = QRadialGradient(QPointF(0, 0), width * 0.4)
    gradient.setColorAt(0, QColor(0, 0, 0, 150))
    gradient.setColorAt(1, QColor(0, 0, 0, 0))
    p.save()
    p.translate(base)
    p.scale(1.0, 0.34)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(gradient)
    p.drawEllipse(QPointF(0, 0), width * 0.4, width * 0.4)
    p.restore()


def paint_chess(p: QPainter, pose: BoardPose, bounds: QRectF, dpr: float) -> None:
    """Dibuja el tablero en su pose; la sombra se calcula sobre `bounds` (la mitad entera)."""
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    sprites: dict[chess.Piece, QPixmap] = {}
    _board_shadow(p, pose, bounds, dpr)
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    front = QLinearGradient(pose.edge.boundingRect().topLeft(), pose.edge.boundingRect().bottomLeft())
    front.setColorAt(0, QColor(COLORS.board_frame))
    front.setColorAt(1, QColor(COLORS.board_edge))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(front)
    p.drawPolygon(pose.edge)
    p.setBrush(QColor(COLORS.board_frame))
    p.drawPolygon(pose.quad(-FRAME, -FRAME, 8 + FRAME, 8 + FRAME))
    for row in range(8):
        for col in range(8):
            p.setBrush(QColor(COLORS.square_light if (row + col) % 2 == 0 else COLORS.square_dark))
            p.drawPolygon(pose.quad(col, row, col + 1, row + 1))
    rim = QColor(COLORS.text)
    rim.setAlphaF(0.12)
    p.setPen(QPen(rim, max(1.0, pose.near_width * 0.002)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolygon(pose.quad(0, 0, 8, 8))
    board = chess.Board(POSITION + " w - - 0 30")
    for row in range(8):  # de atrás hacia adelante: las piezas cercanas tapan a las lejanas
        for col in range(8):
            piece = board.piece_at(chess.square(col, 7 - row))
            if piece is None:
                continue
            base = pose.at(col + 0.5, row + 0.64)
            width = pose.at(col + 1, row + 0.64).x() - pose.at(col, row + 0.64).x()
            _piece_shadow(p, base, width)
            size = width * PIECE_SCALE
            if piece not in sprites:
                sprites[piece] = piece_pixmap(piece, PIECE_RENDER)
            p.drawPixmap(QRectF(base.x() - size / 2, base.y() - size * ground_ratio(), size, size), sprites[piece],
                         QRectF(sprites[piece].rect()))
    p.restore()
