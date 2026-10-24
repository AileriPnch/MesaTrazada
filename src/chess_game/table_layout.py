"""Disposición de la mesa del ajedrez (función pura, sin widgets): el tablero y cada objeto apoyado alrededor
(bandejas de capturadas, carteles, reloj, planilla, placas) para un tamaño de ventana.

Todo se mide en casillas (TABLE_LOOK) a partir de la casilla real del tablero (px físicos enteros): los objetos
escalan con el tablero. El conjunto (tablero | bandejas | columna) queda centrado; la esquina del volumen queda
libre (si la columna llega hasta ahí, empieza debajo)."""
from dataclasses import dataclass

from PyQt6.QtCore import QRect, QRectF

from src.chess_game.board_painter import MARGIN, BoardGeometry
from src.common.theme import CORNER, TABLE_LOOK, px, window_scale

BOARD_SIDE = 8 + 2 * MARGIN  # casillas que ocupa el widget del tablero (tablero + marco + aire)


@dataclass(frozen=True)
class TableLayout:
    s: float  # lado de la casilla (px lógicos)
    board_view: QRect  # el widget del tablero
    frame: QRectF  # el marco del tablero
    tray_rival: QRectF  # bandeja junto a la mitad del rival: las piezas que perdiste
    tray_own: QRectF  # junto a tu mitad: las que capturaste
    rival_plate: QRectF
    clock: QRectF  # el reloj entra entero acá (su caja visible), sin deformarse
    sheet: QRectF
    own_plate: QRectF
    primary: QRectF  # Nueva partida
    secondary: tuple[QRectF, QRectF]  # Deshacer, Menú
    corner: QRectF  # esquina del volumen

    @property
    def objects(self) -> dict[str, QRectF]:
        """Los objetos apoyados en la mesa (ninguno pisa a otro, ni al tablero, ni la esquina del volumen)."""
        return dict(tray_rival=self.tray_rival, tray_own=self.tray_own, rival_plate=self.rival_plate,
                    clock=self.clock, sheet=self.sheet, own_plate=self.own_plate, primary=self.primary,
                    undo=self.secondary[0], menu=self.secondary[1])


def corner_rect(width: float, height: float) -> QRectF:
    u = window_scale(width, height)
    size, inset = px(CORNER.size, u), px(CORNER.inset, u)
    return QRectF(width - inset - size, inset, size, size)


def table_layout(width: int, height: int, dpr: float = 1.0) -> TableLayout:
    t = TABLE_LOOK
    span = BOARD_SIDE + 2 * t.gap + t.tray_w + t.col_w  # ancho del conjunto, en casillas
    guess = max(1.0, min(width / (span + 2 * t.pad), height / (BOARD_SIDE + 2 * t.pad)))
    side = round(BOARD_SIDE * guess)
    view = QRect(round((width - span * guess) / 2), round((height - side) / 2), side, side)
    g = BoardGeometry.fit(view.width(), view.height(), False, dpr)  # casillas de px físicos enteros
    s = g.square
    frame, board = g.frame_rect.translated(view.x(), view.y()), g.board_rect.translated(view.x(), view.y())
    # bandejas: cada una centrada en su mitad del tablero, más bajas si no entran
    tray_h = min(t.tray_h, 4 - 2 * t.stack_gap) * s
    x = frame.right() + t.gap * s
    trays = [QRectF(x, board.top() + (k + 0.5) * 4 * s - tray_h / 2, t.tray_w * s, tray_h) for k in (0, 1)]
    # columna: de arriba hacia abajo, cartel del rival, reloj, planilla (lo que sobra), tu cartel y las placas
    x = trays[0].right() + t.gap * s
    width_col = t.col_w * s
    corner = corner_rect(width, height)
    top, bottom = frame.top(), frame.bottom()
    gap = px(CORNER.gap, window_scale(width, height))
    if x + width_col > corner.left() - gap:  # la esquina del volumen queda libre
        top = max(top, corner.bottom() + gap)
    rival = QRectF(x, top, width_col, t.plate_h * s)
    clock = QRectF(x, rival.bottom() + t.stack_gap * s, width_col, t.clock_h * s)
    half = (width_col - t.stack_gap * s) / 2
    secondary_top = bottom - t.secondary_h * s
    secondary = (QRectF(x, secondary_top, half, t.secondary_h * s),
                 QRectF(x + width_col - half, secondary_top, half, t.secondary_h * s))
    primary = QRectF(x, secondary_top - t.stack_gap * s - t.primary_h * s, width_col, t.primary_h * s)
    own = QRectF(x, primary.top() - t.button_gap * s - t.plate_h * s, width_col, t.plate_h * s)
    sheet_top = clock.bottom() + t.stack_gap * s
    sheet = QRectF(x, sheet_top, width_col, max(s, own.top() - t.stack_gap * s - sheet_top))
    return TableLayout(s, view, frame, trays[0], trays[1], rival, clock, sheet, own, primary, secondary, corner)
