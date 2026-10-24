"""Hojas de estilo (QSS) generadas desde los tokens de `theme.py`, escaladas con la ventana."""
from PyQt6.QtGui import QColor

from src.common import theme
from src.common.theme import RADIUS, ButtonTokens, px


def rgba(hex_color: str, alpha: float) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha:.3f})"


def button_qss(selector: str, t: ButtonTokens, u: float) -> str:
    """Botón con sus estados (hover, pressed, checked, disabled) a la escala `u`, con la fuente de interfaz."""
    ts = theme.TYPE
    return f"""
{selector} {{
    background: {t.bg}; color: {t.text}; border: 1px solid {t.border};
    border-radius: {px(RADIUS.md, u)}px; padding: {px(t.pad_v, u)}px {px(t.pad_h, u)}px;
    font-family: '{ts.ui_family}'; font-size: {px(ts.control, u, 9)}px;
    font-weight: {ts.ui_strong if t.strong else ts.ui_weight};
}}
{selector}:hover {{ background: {t.hover_bg}; color: {t.hover_text}; border-color: {t.hover_border}; }}
{selector}:pressed {{ background: {t.pressed_bg}; }}
{selector}:checked {{ background: {t.checked_bg}; color: {t.checked_text}; border-color: {t.checked_border}; }}
{selector}:disabled {{ background: {t.disabled_bg}; color: {t.disabled_text}; border-color: {t.disabled_border}; }}
"""
