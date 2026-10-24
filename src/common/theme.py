"""Tokens de diseño de toda la app: color, tipografía, espaciado, radios, botones, neón y movimiento.

Las medidas (tipografía, espaciado, radios, neón) están en unidades que se multiplican por la escala de la
pantalla (`u`, 1.0 con la ventana de 1000x720): así todo queda proporcional a la ventana.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    # Interfaz
    window: str = "#26292d"
    panel: str = "#2e3237"
    surface: str = "#363a40"
    border: str = "#464b52"
    text: str = "#e4e1db"
    text_muted: str = "#9a9690"
    error: str = "#d0604f"
    accent: str = "#d19a3a"  # ámbar: el único acento
    accent_hover: str = "#dcaa52"
    accent_pressed: str = "#b9852e"
    accent_dark: str = "#8f6a2a"
    ivory: str = "#efe9dc"
    ink: str = "#1b1d20"
    glass: str = "#121416"  # fondo de paneles flotantes (se usa con transparencia)
    # Mesa de juego (pantalla de inicio)
    wood_deep: str = "#0d0a08"
    wood: str = "#1b1410"
    wood_grain: str = "#3b2a1d"
    felt_deep: str = "#0b0f0e"
    felt: str = "#18201e"
    lamp: str = "#ffe3b8"  # luz cálida de la lámpara sobre la mesa
    shadow: str = "#000000"
    # Tablero de ajedrez: pizarra laqueada
    square_light: str = "#5d6574"  # gris azulado
    square_dark: str = "#2b3140"  # azul pizarra profundo
    board_frame: str = "#14171d"  # marco laqueado
    board_edge: str = "#0a0807"
    check: str = "#d0453a"
    # Cartas
    card_red: str = "#b3261e"
    card_border: str = "#b8b0a0"
    card_back: str = "#2b2a27"
    slot_border: str = "#4d535b"
    paper_lit: str = "#f9f4ea"  # papel marfil hacia la luz
    paper: str = "#efe7d6"
    paper_shade: str = "#ddd2bc"
    card_gold: str = "#b98b3c"  # oro de las figuras y del dorso (familia del ámbar)
    card_gold_lit: str = "#f2cf86"
    # Mesa del solitario: paño de casino profundo
    felt_table_lit: str = "#24503b"  # bajo el foco
    felt_table: str = "#173a2b"
    felt_table_deep: str = "#08140f"  # bordes, fuera del foco
    # Mesa del ajedrez: tinta de la planilla y grabado del latón
    pen_ink: str = "#1f2a44"  # tinta azul-negra (jugadas, resultado)
    print_ink: str = "#4c5060"  # impreso de la planilla (encabezados, números)
    highlighter: str = "#f0be50"  # resaltador detrás de la última jugada
    engrave: str = "#2a1a08"  # letras grabadas en el latón
    engrave_light: str = "#fff0c8"  # filo de luz debajo del grabado
    thinking: str = "#ffbe55"  # luz del reloj del lado de Stockfish mientras piensa


@dataclass(frozen=True)
class TypeScale:
    """Fuentes embebidas en assets/fonts (OFL; las registra `src/common/fonts.py`). Tamaños en unidades;
    tracking = espaciado entre letras en px por unidad. Sin pesos Light/Thin: el neón sobre trazos finos
    se ve borroso."""
    title_family: str = "Playfair Display"  # nombre de la app y de cada juego
    title_weight: int = 600  # SemiBold
    ui_family: str = "Inter"  # subtítulos, rótulos y botones
    ui_weight: int = 400
    ui_strong: int = 600  # botón principal
    display: float = 40  # nombre de cada juego
    title: float = 24  # nombre de la app
    body: float = 14.5  # línea de detalle
    control: float = 13.5  # botones
    label: float = 12  # rótulos de opciones
    title_tracking: float = 0.3
    ui_tracking: float = 0.1
    games_family: str = "Segoe UI"  # los juegos usan la del sistema hasta que hereden estos tokens
    hand_family: str = "Caveat"  # lo escrito a mano en la planilla del ajedrez
    hand_weight: int = 500  # Medium


@dataclass(frozen=True)
class Spacing:
    xs: float = 4
    sm: float = 8
    md: float = 12
    lg: float = 16
    xl: float = 24
    xxl: float = 32
    xxxl: float = 48


@dataclass(frozen=True)
class Radii:
    sm: float = 4
    md: float = 6
    lg: float = 10
    xl: float = 14


@dataclass(frozen=True)
class ButtonTokens:
    bg: str
    text: str
    border: str
    hover_bg: str
    hover_text: str
    hover_border: str
    pressed_bg: str
    checked_bg: str
    checked_text: str
    checked_border: str
    disabled_bg: str
    disabled_text: str
    disabled_border: str
    strong: bool = False  # peso: TYPE.ui_strong (si no, TYPE.ui_weight)
    pad_v: float = 8  # unidades
    pad_h: float = 16


@dataclass(frozen=True)
class PlaqueTokens:
    """Cartel detrás del título de cada mitad: se ajusta al texto (medidas en unidades)."""
    pad_h: float = 34
    pad_v: float = 16
    radius: float = 7
    fill_alpha: float = 0.5  # relleno COLORS.glass semitransparente: separa el texto del fondo
    rest: float = 0.16  # contorno ámbar en reposo: neón casi apagado
    hover: float = 0.36  # contorno + brillo con el mouse encima (por debajo del tablero/abanico)


@dataclass(frozen=True)
class NeonTokens:
    color: str = "#e0a94a"  # ámbar del brillo
    core: str = "#ffd69a"  # centro de la línea, más claro
    line: float = 1.0  # grosor de la línea (unidades; mínimo 1 px)
    glow_radius: float = 12  # radio del brillo (unidades)
    divider: float = 0.45  # intensidad del brillo de la línea divisoria
    name_rest: float = 0.16  # brillo del nombre del juego en reposo
    name_hover: float = 0.5  # ... y con el mouse encima
    outline: float = 0.55  # contorno del tablero / abanico con el mouse encima
    light: float = 0.07  # cuánto se aclara la mitad con el mouse encima
    dim: float = 0.3  # cuánto se atenúa la otra mitad


@dataclass(frozen=True)
class PieceLook:
    """Piezas renderizadas (Blender). Al arrastrar, la pieza se levanta: medidas en fracción del lado de la
    casilla; luz arriba a la izquierda, así que la sombra se aleja hacia abajo a la derecha."""
    lift_scale: float = 1.08  # crece un poco (se re-escala desde el render: nítida)...
    lift_shadow_alpha: float = 0.6  # ... la sombra (sin el contacto) se aleja, se difumina y se aclara ...
    lift_shadow_blur: float = 0.06
    lift_shadow_dx: float = 0.1
    lift_shadow_dy: float = 0.1
    lift_reflection_gap: float = 0.08  # ... y el reflejo se separa de la base
    lift_reflection: float = 0.5  # (y se apaga a la mitad)


@dataclass(frozen=True)
class BoardLook:
    """Tablero renderizado + lo que se dibuja por código encima (fracciones del lado de la casilla)."""
    frame: float = 0.2  # marco del render (48,76 / 243,81)
    shadow: float = 0.55  # sombra del tablero sobre la mesa
    lamp: float = 0.07  # refuerzo de la luz de la lámpara sobre las casillas
    gloss: float = 0.07  # brillo claro de la laca hacia la luz (arriba a la izquierda; reemplaza el del render)
    reflection: float = 0.6  # multiplica el alfa del reflejo horneado (Fresnel, máx. ~0,15)
    piece_scale: float = 1.1  # piezas sobre la escala del render (426,67 px por casilla): el rey ~0,89 de la casilla
    bloom: float = 3.0  # bloom ámbar del brillo de la pieza elegida (se suma; en las negras se ve más)
    bloom_blur: float = 0.04
    halo: float = 0.55  # halo ámbar de la silueta de la pieza elegida (debajo de la pieza)
    halo_blur: float = 0.05
    coords: float = 0.17  # tamaño de las coordenadas (Inter)
    coords_alpha: float = 0.85
    coords_halo: float = 0.02  # halo del color de la casilla detrás de cada coordenada (sobre las sombras)
    coords_halo_alpha: float = 0.9
    last_move: float = 0.2  # tinte ámbar suave del último movimiento
    selected: float = 0.18  # tinte de la casilla de la pieza elegida
    target_dot: float = 0.12  # radio del punto de las casillas legales
    target_glow: float = 0.75
    table_light: float = 0.1  # charco de luz de la lámpara sobre la mesa, alrededor del tablero
    table_light_radius: float = 0.85  # radio del charco, en lados del marco del tablero
    vignette: float = 0.75


@dataclass(frozen=True)
class CardLook:
    """Cartas del solitario (fracciones del ancho de la carta). Misma luz que el ajedrez: arriba a la
    izquierda, casi cenital."""
    radius: float = 0.07
    border: float = 0.011
    grain: float = 0.07  # textura del papel
    shadow_alpha: float = 0.4
    shadow_blur: float = 0.035
    shadow_dx: float = 0.012
    shadow_dy: float = 0.026
    contact_alpha: float = 0.32
    lift_scale: float = 1.03  # al arrastrar: un poco más grande...
    lift_shadow_alpha: float = 0.34  # ... y la sombra se aleja, crece y se difumina
    lift_shadow_blur: float = 0.09
    lift_shadow_dx: float = 0.05
    lift_shadow_dy: float = 0.09
    target_glow: float = 0.85  # destinos válidos mientras se arrastra
    foil: float = 0.55  # brillo del enrejado del dorso bajo el foco


@dataclass(frozen=True)
class TableLook:
    """Mesa de la partida de ajedrez: objetos apoyados alrededor del tablero (renders de blender/generar_interfaz.py).
    Medidas en casillas (la disposición con la que se renderizaron); textos en fracción de la casilla o del renglón,
    con mínimos en px lógicos."""
    pad: float = 0.35  # aire alrededor del conjunto
    gap: float = 0.25  # tablero | bandeja | columna
    tray_w: float = 1.1
    tray_h: float = 3.0  # cada bandeja, centrada en su mitad del tablero (más chica si no entra)
    col_w: float = 3.6
    plate_h: float = 0.5
    clock_h: float = 1.0  # lugar del reloj: su caja visible entra entera, sin deformarse
    primary_h: float = 0.72
    secondary_h: float = 0.6
    stack_gap: float = 0.15
    button_gap: float = 0.25
    captured: float = 0.6  # casilla de una pieza capturada (el peón mide ~0,4)
    card_w: float = 3.0
    card_h: float = 1.5
    plate_text: float = 0.2  # carteles
    primary_text: float = 0.24  # "Nueva partida"
    secondary_text: float = 0.2
    captured_text: float = 0.16  # "+N"
    sheet_text: float = 0.8  # jugadas: fracción del alto del renglón
    sheet_print: float = 0.42  # encabezados impresos: fracción del renglón
    card_title: float = 0.3
    card_text: float = 0.16
    min_text: int = 11  # px lógicos
    min_hand: int = 13  # la letra a mano de la planilla, nunca más chica
    highlight: float = 0.43  # opacidad del resaltador
    glow: float = 0.22  # radio de la luz del reloj (casillas)
    glow_alpha: float = 0.6
    focus_width: float = 0.025  # filete de foco de las placas (casillas)
    focus_inset: float = 0.07  # a qué distancia del borde de la placa
    knob: float = 0.82  # la perilla ocupa esta fracción de la esquina (el resto: su sombra)


@dataclass(frozen=True)
class CornerTokens:
    """Control de volumen: siempre en la esquina superior derecha de la ventana (unidades)."""
    size: float = 34
    inset: float = 12  # distancia a los bordes superior y derecho
    gap: float = 8  # aire hasta lo que tenga debajo o a la izquierda
    panel_width: float = 240


@dataclass(frozen=True)
class Motion:
    hover_ms: int = 180  # transición de hover (150-200 ms)
    rebuild_ms: int = 120  # espera tras el último cambio de tamaño para regenerar los pixmaps


COLORS = Colors()
TYPE = TypeScale()
SPACE = Spacing()
RADIUS = Radii()
NEON = NeonTokens()
PLAQUE = PlaqueTokens()
MOTION = Motion()
CORNER = CornerTokens()
CARD_LOOK = CardLook()
PIECE_LOOK = PieceLook()
BOARD_LOOK = BoardLook()
TABLE_LOOK = TableLook()

PRIMARY = ButtonTokens(  # ámbar relleno
    bg=COLORS.accent, text=COLORS.ink, border=COLORS.accent,
    hover_bg=COLORS.accent_hover, hover_text=COLORS.ink, hover_border=COLORS.accent_hover,
    pressed_bg=COLORS.accent_pressed,
    checked_bg=COLORS.accent, checked_text=COLORS.ink, checked_border=COLORS.accent,
    disabled_bg=COLORS.surface, disabled_text=COLORS.text_muted, disabled_border=COLORS.surface,
    strong=True, pad_v=9, pad_h=20)

SECONDARY = ButtonTokens(  # contorno; "checked" para opciones elegidas
    bg="rgba(255, 255, 255, 0.02)", text=COLORS.text, border=COLORS.border,
    hover_bg="rgba(255, 255, 255, 0.05)", hover_text=COLORS.text, hover_border=COLORS.accent_dark,
    pressed_bg="rgba(0, 0, 0, 0.25)",
    checked_bg="rgba(209, 154, 58, 0.12)", checked_text=COLORS.accent_hover, checked_border=COLORS.accent,
    disabled_bg="transparent", disabled_text=COLORS.text_muted, disabled_border=COLORS.surface)


def px(value: float, u: float, minimum: int = 1) -> int:
    """Medida en unidades → píxeles lógicos para la escala `u`."""
    return max(minimum, round(value * u))


def window_scale(width: float, height: float) -> float:
    """Escala `u` de una pantalla: 1.0 con 1000x720, proporcional a la ventana (como el inicio). En pasos de
    0,05: así los estilos no se regeneran a cada píxel al redimensionar y todos usan la misma."""
    return max(0.05, round(min(width / 1000, height / 720) * 20) / 20)
