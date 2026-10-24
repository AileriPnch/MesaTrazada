"""Barra del solitario con los tokens del tema, a la escala de la ventana: Inter, "Nueva partida" ámbar relleno,
el resto en contorno (sobre vidrio oscuro, para que se lea encima del paño) y el modo de robo como segmentos."""
from dataclasses import replace

from src.common import theme
from src.common.qss import button_qss, rgba
from src.common.theme import COLORS, PRIMARY, SECONDARY, px

ON_FELT = replace(SECONDARY, bg=rgba(COLORS.glass, 0.55), hover_bg=rgba(COLORS.glass, 0.75))


def solitaire_qss(u: float) -> str:
    t = theme.TYPE
    return f"""
QLabel#solStatus {{
    font-family: '{t.ui_family}'; font-size: {px(t.body, u, 10)}px; font-weight: {t.ui_strong};
    color: {COLORS.text}; background: transparent;
}}
""" + button_qss("QPushButton#solMode", ON_FELT, u) + button_qss("QPushButton#solButton", ON_FELT, u) \
        + button_qss("QPushButton#solPrimary", PRIMARY, u)
