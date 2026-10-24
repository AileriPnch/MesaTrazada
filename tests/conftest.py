import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if Path("C:/Windows/Fonts").is_dir():  # offscreen sin esto usa una fuente de reserva con otras medidas
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    from src.common.fonts import load_fonts

    app = QApplication.instance() or QApplication([])
    load_fonts()  # fuentes embebidas (assets/fonts), igual que main.py
    yield app


@pytest.fixture(autouse=True)
def instant_engine_reply(monkeypatch):
    """Sin el ritmo humano (ENGINE_MIN_REPLY) en los tests; test_engine_controller lo prueba aparte."""
    from config import settings

    monkeypatch.setattr(settings, "engine_min_reply", 0.0)
