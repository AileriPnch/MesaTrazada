"""Saca el velo del brillo de la lámpara que trae `tablero.png` (arriba a la izquierda, en b6-b7): aclara las
casillas pero les quita el azul, y a la vista queda como una mancha oscura y sucia. El brillo se repone por
código, claro y suave (board_painter._gloss).

Cómo: el color medio de cada casilla contra lo esperable para su tipo (clara u oscura) a su distancia del
centro, que es la caída normal de la luz (recta ajustada sin las casillas del brillo). El exceso (sólo positivo,
por canal) se interpola suave entre los centros de las casillas y se resta: invertir, sumar, invertir (QPainter
no tiene modo "restar"). Se hace una vez, al cargar el arte (también en el hilo de la precarga)."""
from math import hypot

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter

SAMPLES = (0.2, 0.35, 0.5, 0.65, 0.8)  # dónde se mide cada casilla (fracción del lado)
CLEAN_RADIUS = 2.5  # casillas: alrededor del brillo no se usan para ajustar la caída
NOISE = 6  # suma de canales por debajo de la cual no se corrige nada


def _square_means(board: QImage, square: float, frame: float) -> dict[tuple[int, int], tuple[float, ...]]:
    means = {}
    for col in range(8):
        for row in range(8):
            colors = [board.pixelColor(int(frame + (col + fx) * square), int(frame + (row + fy) * square))
                      for fx in SAMPLES for fy in SAMPLES]
            means[(col, row)] = tuple(sum(getattr(c, ch)() for c in colors) / len(colors)
                                      for ch in ("red", "green", "blue"))
    return means


def _distance(cell: tuple[int, int]) -> float:
    return hypot(cell[0] + 0.5 - 4, cell[1] + 0.5 - 4)


def _fit(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Recta por mínimos cuadrados: valor = a + b * distancia."""
    n = len(points)
    mx, my = sum(x for x, _ in points) / n, sum(y for _, y in points) / n
    var = sum((x - mx) ** 2 for x, _ in points)
    b = sum((x - mx) * (y - my) for x, y in points) / var if var else 0.0
    return my - b * mx, b


def glare_excess(board: QImage, square: float, frame: float) -> dict[tuple[int, int], tuple[float, ...]]:
    """Exceso de color de cada casilla (columna, fila desde arriba) sobre la caída normal de la luz."""
    means = _square_means(board, square, frame)

    def residuals(cells):
        out = {}
        for light in (True, False):
            group = [c for c in means if ((c[0] + c[1]) % 2 == 0) == light]  # a8 (0, 0) es clara
            used = [c for c in group if c in cells]
            fits = [_fit([(_distance(c), means[c][ch]) for c in used]) for ch in range(3)]
            for c in group:
                out[c] = tuple(means[c][ch] - (fits[ch][0] + fits[ch][1] * _distance(c)) for ch in range(3))
        return out

    first = residuals(set(means))
    glare = max(first, key=lambda c: sum(first[c]))
    clean = {c for c in means if hypot(c[0] - glare[0], c[1] - glare[1]) > CLEAN_RADIUS}
    excess = {}
    for cell, r in residuals(clean).items():
        positive = tuple(max(0.0, v) for v in r)
        excess[cell] = positive if sum(positive) >= NOISE else (0.0, 0.0, 0.0)
    return excess


def remove_glare(board: QImage, square: float, frame: float) -> QImage:
    excess = glare_excess(board, square, frame)
    field = QImage(8, 8, QImage.Format.Format_RGB32)
    for (col, row), (r, g, b) in excess.items():
        field.setPixelColor(col, row, QColor(*(min(255, round(v)) for v in (r, g, b))))
    side = round(8 * square)
    smooth = field.scaled(side, side, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    result = board.copy()
    area = QRectF(frame, frame, 8 * square, 8 * square)
    p = QPainter(result)
    p.setClipRect(area)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
    p.fillRect(area, QColor(255, 255, 255))  # 1 - color
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
    p.drawImage(area, smooth)  # 1 - color + exceso
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
    p.fillRect(area, QColor(255, 255, 255))  # color - exceso
    p.end()
    return result
