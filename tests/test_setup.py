import logging

import chess.engine
import pytest

from config import PROJECT_ROOT, Settings
from src.common.logging_setup import setup_logging


def test_settings_defaults_resolve_against_project_root(monkeypatch):
    monkeypatch.setenv("STOCKFISH_PATH", "engine/stockfish.exe")
    s = Settings()
    assert s.stockfish_path == PROJECT_ROOT / "engine" / "stockfish.exe"
    human = [s.principiante, s.novato, s.aficionado]
    assert [h.elo for h in human] == sorted(h.elo for h in human) and human[-1].elo < s.club_elo < s.avanzado_elo
    assert [h.depth for h in human] == sorted(h.depth for h in human)
    assert all(0 <= h.blunder <= 1 and 0 <= h.obvious <= 1 and h.blunder_min_cp <= h.blunder_max_cp for h in human)
    assert 0 < s.club_time and 0 < s.avanzado_time and 0 < s.maximo_time and s.engine_min_reply >= 0


def test_settings_read_env(monkeypatch):
    monkeypatch.setenv("NOVATO_TEMP", "65.5")
    monkeypatch.setenv("PRINCIPIANTE_BLUNDER_MAX_CP", "700")
    monkeypatch.setenv("OBVIOUS_CP", "300")
    monkeypatch.setenv("CLUB_ELO", "1500")
    monkeypatch.setenv("ENGINE_MIN_REPLY", "0.8")
    s = Settings()
    assert s.novato.temperature == 65.5 and s.principiante.blunder_max_cp == 700
    assert s.aficionado.obvious_cp == 300 and s.club_elo == 1500 and s.engine_min_reply == 0.8


def test_logging_writes_file(tmp_path):
    setup_logging(tmp_path, "INFO")
    logging.getLogger("test").info("hola")
    for h in logging.getLogger().handlers:
        h.flush()
    content = (tmp_path / "app.log").read_text(encoding="utf-8")
    assert "INFO - test: hola" in content


def test_stockfish_responds_to_uci():
    path = Settings().stockfish_path
    if not path.exists():
        pytest.skip(f"Stockfish no encontrado en {path}")
    engine = chess.engine.SimpleEngine.popen_uci(str(path))
    try:
        assert "Stockfish" in engine.id.get("name", "")
        assert {"UCI_LimitStrength", "UCI_Elo", "MultiPV"} <= set(engine.options)
    finally:
        engine.quit()


def test_frozen_build_reads_env_beside_the_exe_and_logs_to_local_appdata(monkeypatch, tmp_path):
    """Empaquetada (PyInstaller): el .env es opcional y va junto al .exe; los logs, en %LOCALAPPDATA%."""
    import sys

    from src.common import paths

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app" / "Ajedrez.exe"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("LOG_DIR", raising=False)
    assert paths.install_dir() == tmp_path / "app"
    assert paths.licenses_dir() == tmp_path / "app" / "licencias"
    assert Settings().log_dir == tmp_path / "local" / paths.DATA_DIR_NAME / "logs"
    assert Settings().stockfish_path == PROJECT_ROOT / "engine" / "stockfish.exe"  # dentro del paquete


def test_settings_without_env_file_use_defaults(monkeypatch):
    """Sin .env (como el .zip publicado) todo tiene su valor por defecto."""
    import os

    for name in [n for n in os.environ if n.split("_")[0] in ("PRINCIPIANTE", "NOVATO", "AFICIONADO", "CLUB",
                                                               "AVANZADO", "MAXIMO", "ENGINE", "OBVIOUS", "LOG")]:
        monkeypatch.delenv(name)
    s = Settings()
    assert (s.principiante.depth, s.novato.depth, s.aficionado.depth) == (1, 2, 2)
    assert (s.club_elo, s.avanzado_elo, s.maximo_time, s.engine_min_reply) == (1400, 1800, 1.0, 0.6)
