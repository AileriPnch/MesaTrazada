"""Geometría del tablero y su imagen cacheada: el render de Blender (`tablero.png`, marco incluido) escalado
para que sus casillas caigan en la grilla de píxeles físicos enteros y el refuerzo de la luz de la lámpara; las
coordenadas (Inter, dentro de las casillas) en imágenes aparte. Con negras la imagen es la misma (a1 y h8 son
oscuras); cambian las coordenadas y dónde va cada pieza."""
from dataclasses import dataclass

import chess
from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QRadialGradient

from src.chess_game.art_library import BOARD_FRAME, BOARD_SQUARE
from src.common.glow import blur_image
from src.common import theme
from src.common.theme import BOARD_LOOK, COLORS

FORMAT = QImage.Format.Format_ARGB32_Premultiplied
MARGIN = BOARD_LOOK.frame + 0.06  # marco + aire, en casillas


@dataclass(frozen=True)
class BoardGeometry:
    left: float
    top: float
    square: float
    margin: float
    flipped: bool  # True: se ve desde las negras

    @classmethod
    def fit(cls, width: int, height: int, flipped: bool, dpr: float = 1.0) -> "BoardGeometry":
        """Tablero centrado; cada casilla mide un número entero de píxeles físicos (sin costuras)."""
        side = max(8.0, min(width, height)) * dpr
        square = max(1, int(side / (8 + 2 * MARGIN)))
        left = round((width * dpr - 8 * square) / 2)
        top = round((height * dpr - 8 * square) / 2)
        return cls(left / dpr, top / dpr, square / dpr, MARGIN * square / dpr, flipped)

    @property
    def board_rect(self) -> QRectF:
        return QRectF(self.left, self.top, 8 * self.square, 8 * self.square)

    @property
    def frame_rect(self) -> QRectF:
        frame = BOARD_LOOK.frame * self.square
        return self.board_rect.adjusted(-frame, -frame, frame, frame)

    def cell(self, sq: chess.Square) -> tuple[int, int]:
        """(columna, fila) en pantalla."""
        file, rank = chess.square_file(sq), chess.square_rank(sq)
        return (7 - file, rank) if self.flipped else (file, 7 - rank)

    def square_rect(self, sq: chess.Square) -> QRectF:
        col, row = self.cell(sq)
        return QRectF(self.left + col * self.square, self.top + row * self.square, self.square, self.square)

    def square_at(self, point: QPointF) -> chess.Square | None:
        col = int((point.x() - self.left) // self.square)
        row = int((point.y() - self.top) // self.square)
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        file, rank = (7 - col, row) if self.flipped else (col, 7 - row)
        return chess.square(file, rank)


def _alpha(hex_color: str, alpha: float) -> QColor:
    color = QColor(hex_color)
    color.setAlphaF(alpha)
    return color


def _lamp(p: QPainter, board: QRectF) -> None:
    """Refuerzo de la luz de la lámpara sobre las casillas (el render ya la trae; esto la acerca a la mesa)."""
    lamp = QRadialGradient(board.center(), board.width() * 0.62)
    lamp.setColorAt(0.0, _alpha(COLORS.lamp, BOARD_LOOK.lamp))
    lamp.setColorAt(1.0, _alpha(COLORS.lamp, 0.0))
    p.fillRect(board, lamp)


def _gloss(p: QPainter, board: QRectF) -> None:
    """Brillo claro y suave de la laca hacia la luz (arriba a la izquierda). Reemplaza el del render, que
    agrisaba las casillas (board_glare); en modo Screen aclara sin quitarles el azul."""
    center = QPointF(board.left() + board.width() * 0.27, board.top() + board.height() * 0.22)
    gloss = QRadialGradient(center, board.width() * 0.38)
    gloss.setColorAt(0.0, _alpha("#ffffff", BOARD_LOOK.gloss))
    gloss.setColorAt(1.0, _alpha("#ffffff", 0.0))
    p.save()
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
    p.fillRect(board, gloss)
    p.restore()


def _rendered_board(p: QPainter, board: QImage, origin: QPoint, square: int) -> None:
    """El render escalado (suave) a casillas de `square` px físicos, con la casilla a8 (o h1) en `origin`."""
    scale = square / BOARD_SQUARE
    side = round(board.width() * scale)
    scaled = board.scaled(side, side, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    frame = round(BOARD_FRAME * side / board.width())
    p.drawImage(origin - QPoint(frame, frame), scaled)


def coordinate_labels(g: BoardGeometry, dpr: float) -> list[tuple[chess.Square, QImage]]:
    """Coordenadas, una imagen del tamaño de la casilla por etiqueta: números arriba a la izquierda en la
    columna de la izquierda y letras abajo a la derecha en la fila de abajo, cada una en el tono de la casilla
    opuesta. Van aparte del tablero porque se dibujan sobre las sombras y los reflejos de las piezas (si no,
    la sombra de la fila de abajo, que cae hacia abajo a la derecha, tapa las letras)."""
    side = round(g.square * dpr)
    font = QFont(theme.TYPE.ui_family)
    font.setWeight(QFont.Weight(theme.TYPE.ui_strong))
    font.setPixelSize(max(round(8 * dpr), round(side * BOARD_LOOK.coords)))
    pad = side * 0.06
    edge = 7 if g.flipped else 0  # columna de la izquierda y fila de abajo, según de qué lado se mire
    labels = [(chess.square(edge, i), chess.RANK_NAMES[i], Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
              for i in range(8)]
    labels += [(chess.square(i, edge), chess.FILE_NAMES[i], Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
               for i in range(8)]
    box = QRectF(0, 0, side, side).adjusted(pad, pad * 0.6, -pad, -pad * 0.6)

    def text_image(text: str, align, color: QColor, spread: float = 0.0) -> QImage:
        """El texto; con `spread`, engrosado (dibujado corrido en 8 direcciones): la base del halo."""
        image = QImage(side, side, FORMAT)
        image.fill(Qt.GlobalColor.transparent)
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setFont(font)
        p.setPen(color)
        shifts = [(0.0, 0.0)] + [(dx * spread, dy * spread) for dx, dy in
                                 ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7))]
        for dx, dy in shifts if spread else shifts[:1]:
            p.drawText(box.translated(dx, dy), align, text)
        p.end()
        return image

    images = []
    for sq, text, align in labels:
        light = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
        own, other = (COLORS.square_light, COLORS.square_dark) if light else (COLORS.square_dark, COLORS.square_light)
        # Halo del color de la casilla: la letra se lee aunque caiga sobre la sombra de una pieza.
        spread = side * BOARD_LOOK.coords_halo
        image = blur_image(text_image(text, align, _alpha(own, BOARD_LOOK.coords_halo_alpha), spread), spread)
        p = QPainter(image)
        p.drawImage(0, 0, text_image(text, align, _alpha(other, BOARD_LOOK.coords_alpha)))
        p.end()
        images.append((sq, image))
    return images


def render_board(g: BoardGeometry, width: int, height: int, dpr: float, board: QImage) -> QImage:
    """Imagen del tablero del tamaño del widget (píxeles físicos, fondo transparente)."""
    image = QImage(max(1, round(width * dpr)), max(1, round(height * dpr)), FORMAT)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    _rendered_board(p, board, QPoint(round(g.left * dpr), round(g.top * dpr)), round(g.square * dpr))
    p.save()
    p.scale(dpr, dpr)
    _lamp(p, g.board_rect)
    _gloss(p, g.board_rect)
    p.restore()
    p.end()
    return image
