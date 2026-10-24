"""Fuentes embebidas: se cargan desde assets/fonts con su licencia y Qt usa el peso real pedido."""
from PyQt6.QtGui import QFont, QFontInfo

from src.common.fonts import FONT_DIR, load_fonts
from src.common.theme import TYPE


def test_only_the_used_fonts_ship_each_with_its_license():
    families = {path.parent.name for path in FONT_DIR.glob("*/*.ttf")}
    assert families == {"PlayfairDisplay", "Inter", "Caveat"}
    for path in FONT_DIR.glob("*/*.ttf"):
        assert "SIL OPEN FONT LICENSE Version 1.1" in (path.parent / "OFL.txt").read_text(encoding="utf-8")


def test_type_tokens_use_embedded_fonts_with_real_weights_never_light(qapp):
    assert {TYPE.title_family, TYPE.ui_family, TYPE.hand_family} == {"Playfair Display", "Inter", "Caveat"}
    assert {TYPE.title_family, TYPE.ui_family, TYPE.hand_family} <= load_fonts()
    weights = ((TYPE.title_family, TYPE.title_weight), (TYPE.ui_family, TYPE.ui_weight), (TYPE.ui_family, TYPE.ui_strong),
               (TYPE.hand_family, TYPE.hand_weight))
    for family, weight in weights:
        assert weight >= 400  # nada de Light ni Thin: el neón sobre trazos finos se ve borroso
        font = QFont(family)
        font.setWeight(QFont.Weight(weight))
        info = QFontInfo(font)
        assert info.family() == family and info.weight() == weight  # instancia real, no negrita simulada
