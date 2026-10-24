"""Nombres de colores que usan los juegos y el estilo global. Los valores vienen de los tokens de
`src/common/theme.py` (única fuente); este módulo queda hasta que los juegos usen los tokens directo."""
from src.common.theme import COLORS as _C

ACCENT = _C.accent
ACCENT_HOVER = _C.accent_hover
ACCENT_DARK = _C.accent_dark

WINDOW_BG = _C.window
PANEL_BG = _C.panel
SURFACE = _C.surface
BORDER = _C.border
TEXT = _C.text
TEXT_MUTED = _C.text_muted
ERROR = _C.error

IVORY = _C.ivory
INK = _C.ink

# Tablero de ajedrez
SQUARE_LIGHT = _C.square_light
SQUARE_DARK = _C.square_dark
BOARD_FRAME = _C.board_frame
CHECK = _C.check

# Cartas
CARD_RED = _C.card_red
CARD_BORDER = _C.card_border
CARD_BACK = _C.card_back
SLOT_BORDER = _C.slot_border
