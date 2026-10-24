"""Ningún texto de la pantalla de inicio queda cortado, del mínimo a 1920x1080 (también con las opciones
abiertas y el mensaje largo de Stockfish faltante)."""
import pytest
from PyQt6.QtGui import QFontMetricsF
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QAbstractButton, QLabel, QWidget

from config import settings
from src.app.home.home_layout import APP_NAME, TEXTS, HomeLayout, Side
from src.app.home.home_screen import HomeScreen
from src.app.stylesheet import apply_theme

SIZES = [(800, 600), (1000, 720), (1280, 720), (1536, 864), (1920, 1009), (1920, 1080)]


def fits(rect, text, font) -> bool:
    return QFontMetricsF(font).horizontalAdvance(text) <= rect.width() and QFontMetricsF(font).height() <= rect.height() + 0.5


@pytest.mark.parametrize("size", SIZES)
def test_painted_texts_fit_their_boxes(qapp, size):
    layout = HomeLayout(*size)
    header = layout.header_rect
    assert header.left() >= 0 and header.right() <= layout.width
    assert QFontMetricsF(layout.title_font).horizontalAdvance(APP_NAME) <= header.width() - layout.icon_size
    for side in Side:
        half, name, detail = layout.half(side), layout.name_rect(side), layout.detail_rect(side)
        assert fits(name, TEXTS[side][0], layout.name_font) and fits(detail, TEXTS[side][1], layout.detail_font)
        assert half.contains(name) and half.contains(detail) and name.top() >= layout.header_bottom
        assert layout.art_rect(side).top() >= detail.bottom() and layout.art_rect(side).height() > 100
        assert_plaque_wraps_title(layout, side)


def assert_plaque_wraps_title(layout: HomeLayout, side: Side) -> None:
    """El cartel envuelve nombre + detalle con aire, queda centrado en su mitad y no pisa nada."""
    plaque, half, name, detail = layout.plaque_rect(side), layout.half(side), layout.name_rect(side), layout.detail_rect(side)
    names, details = QFontMetricsF(layout.name_font), QFontMetricsF(layout.detail_font)
    text_w = max(names.horizontalAdvance(TEXTS[side][0]), details.horizontalAdvance(TEXTS[side][1]))
    assert plaque.width() >= text_w + 2 * 20 * layout.u  # se ajusta al texto con padding (no ancho fijo)
    assert half.adjusted(8, 0, -8, 0).contains(plaque) and abs(plaque.center().x() - half.center().x()) <= 1
    ink = names.tightBoundingRect(TEXTS[side][0]).translated(0, name.top() + names.ascent())
    assert plaque.top() + 8 * layout.u <= ink.top()  # aire arriba de las letras
    assert detail.top() + details.ascent() + 8 * layout.u <= plaque.bottom()  # y abajo del detalle
    assert plaque.top() >= layout.header_bottom and layout.art_rect(side).top() >= plaque.bottom()


def clipped(panel: QWidget) -> list[str]:
    bad = []
    for w in panel.findChildren(QWidget):
        if not w.isVisible() or not isinstance(w, (QLabel, QAbstractButton)):
            continue
        need = w.heightForWidth(w.width()) if w.hasHeightForWidth() else w.sizeHint().height()
        if w.height() < need or w.width() < w.minimumSizeHint().width():
            bad.append(f"{type(w).__name__} {w.text()!r}: {w.width()}x{w.height()}")
    return bad


@pytest.mark.parametrize("size", SIZES)
def test_open_options_fit_inside_their_half(qapp, monkeypatch, tmp_path, size):
    apply_theme(qapp)
    monkeypatch.setattr(settings, "stockfish_path", tmp_path / "una carpeta con nombre largo" / "stockfish.exe")
    home = HomeScreen()
    home.resize(*size)
    home.show()
    for side in Side:  # el ajedrez con el mensaje de error (el panel más alto)
        home.open_options(side)
        QTest.qWait(20)
        panel = home.panels[side]
        assert home.home_layout().half(side).contains(panel.geometry().toRectF()), side
        assert clipped(panel) == [], side
        home.close_options()
    home.close()
