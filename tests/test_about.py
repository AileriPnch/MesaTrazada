"""Acerca de: versión única, enlace del inicio y F1 en cualquier pantalla, créditos completos (también en
CREDITS.md), donaciones ocultas sin enlace, textos sin cortes y licencias presentes."""
import re
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.app import about_dialog
from src.app.about_dialog import AboutDialog
from src.common import app_info

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def window(qapp):
    from src.app.main_window import MainWindow

    w = MainWindow()
    w.show()
    QTest.qWait(30)
    yield w
    if w.about is not None:
        w.about.close()
    w.close()


def test_version_lives_in_one_place():
    assert re.fullmatch(r"\d+\.\d+\.\d+", app_info.VERSION)
    sources = [p for p in (ROOT / "src").rglob("*.py") if p.name != "app_info.py"] + [ROOT / "main.py", ROOT / "config.py"]
    assert not [p for p in sources if f'"{app_info.VERSION}"' in p.read_text(encoding="utf-8")]


def test_home_link_and_f1_open_about(window):
    link = window.home.about_link
    assert link.isVisible() and window.home.rect().contains(link.geometry())
    QTest.mouseClick(link, Qt.MouseButton.LeftButton)
    assert window.about is not None and window.about.isVisible()
    QTest.keyClick(window.about, Qt.Key.Key_Escape)
    assert not window.about.isVisible()
    window.open_solitaire(1)
    QTest.keyClick(window.game, Qt.Key.Key_F1)
    assert window.about.isVisible()
    assert app_info.VERSION in window.about.version.text()


def test_about_lists_every_credit_with_link_and_license(qapp, window):
    dialog = AboutDialog(window, 1.0)
    text = dialog.credits.text()
    for credit in app_info.CREDITS:
        assert credit.name in text and credit.url in text and credit.license in text
    assert app_info.LICENSE_URL in dialog.license.text()


def test_credits_file_covers_every_component():
    credits = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
    for credit in app_info.CREDITS:
        assert credit.name.split(",")[0] in credits and credit.url in credits, credit.name
    assert "sf_19" in credits  # la versión exacta del código fuente de Stockfish (GPL)


def test_license_is_full_gplv3_with_copyright():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert f"Copyright (C) 2026 {app_info.AUTHOR}" in text
    assert "GNU GENERAL PUBLIC LICENSE" in text and "Version 3, 29 June 2007" in text
    assert "END OF TERMS AND CONDITIONS" in text and "How to Apply These Terms to Your New Programs" in text


def test_donations_hidden_until_they_have_a_link(qapp, window, monkeypatch):
    assert all(url == "" for _, url in app_info.DONATIONS)  # marcadores: todavía sin cuentas
    assert AboutDialog(window, 1.0).donations is None
    monkeypatch.setattr(app_info, "DONATIONS", (("Cafecito", ""), ("Ko-fi", "https://ko-fi.com/ejemplo")))
    dialog = AboutDialog(window, 1.0)
    assert "ko-fi.com/ejemplo" in dialog.donations.text() and "Cafecito" not in dialog.donations.text()


@pytest.mark.parametrize("size", [(800, 600), (1000, 720), (1920, 1080)])
def test_about_texts_are_not_cut(window, size, monkeypatch):
    monkeypatch.setattr(app_info, "DONATIONS", (("Cafecito", "https://cafecito.app/x"), ("Ko-fi", "https://ko-fi.com/x"),
                                                ("GitHub Sponsors", "https://github.com/sponsors/x")))
    window.resize(*size)
    QTest.qWait(20)
    dialog = window.show_about()
    QTest.qWait(30)
    assert dialog.geometry().height() <= window.screen().availableGeometry().height()
    for label in (dialog.version, dialog.license, dialog.credits, dialog.donations):
        assert label.heightForWidth(label.width()) <= label.height() + 1, label.text()[:40]
    for button in (dialog.licenses_button, dialog.close_button):
        assert button.width() >= button.sizeHint().width()


def test_open_licenses_points_at_an_existing_folder(monkeypatch):
    opened = []
    monkeypatch.setattr(about_dialog.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()))
    AboutDialog.open_licenses()
    assert Path(opened[0]).is_dir() and (Path(opened[0]) / "LICENSE").exists()
