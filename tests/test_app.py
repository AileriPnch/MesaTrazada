import logging

import main
from src.app.main_window import MainWindow
from src.chess_game.chess_screen import ChessScreen
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from src.solitaire.solitaire_screen import SolitaireScreen


def _current(window):
    return window.centralWidget().currentWidget()


def _spy_shutdown(monkeypatch, calls):
    """Registra la llamada y ejecuta el shutdown real: sin él, el hilo del motor queda vivo."""
    original = ChessScreen.shutdown

    def spy(self):
        calls.append("chess")
        original(self)

    monkeypatch.setattr(ChessScreen, "shutdown", spy)


def test_starts_on_menu(qapp):
    window = MainWindow()
    assert _current(window) is window.home
    assert window.game is None


def test_home_starts_each_game_with_its_options_and_back(qapp):
    window = MainWindow()
    window.home.chess_requested.emit(ColorChoice.WHITE, Difficulty.BEGINNER)
    screen = _current(window)
    assert isinstance(screen, ChessScreen) and screen.game is not None  # sin página intermedia
    assert screen.color_choice is ColorChoice.WHITE and screen.difficulty is Difficulty.BEGINNER
    window.game.back_requested.emit()
    assert _current(window) is window.home
    assert window.game is None

    window.home.solitaire_requested.emit(3)
    assert isinstance(_current(window), SolitaireScreen) and window.game.game.draw_count == 3
    window.show_menu()
    assert _current(window) is window.home and window.home.opened is None


def test_leaving_or_closing_calls_shutdown(qapp, monkeypatch):
    calls = []
    _spy_shutdown(monkeypatch, calls)
    window = MainWindow()
    window.open_chess(ColorChoice.WHITE, Difficulty.CLUB)
    window.show_menu()
    assert calls == ["chess"]

    window.open_chess(ColorChoice.WHITE, Difficulty.CLUB)
    window.close()
    assert calls == ["chess", "chess"]
    assert window.game is None


def test_switching_games_shuts_down_previous(qapp, monkeypatch):
    calls = []
    _spy_shutdown(monkeypatch, calls)
    window = MainWindow()
    window.open_game(ChessScreen)
    window.open_game(SolitaireScreen)
    assert calls == ["chess"]
    assert window.centralWidget().count() == 2  # menú + juego actual


def test_startup_error_is_logged(tmp_path, monkeypatch):
    def boom():
        raise RuntimeError("falla simulada")

    shown = []
    monkeypatch.setattr(main, "DEFAULT_LOG_DIR", tmp_path)
    monkeypatch.setattr(main, "_run", boom)
    monkeypatch.setattr(main, "_show_fatal_error", shown.append)
    monkeypatch.setattr("sys.excepthook", main.sys.excepthook)

    assert main.main() == 1
    for handler in logging.getLogger().handlers:
        handler.flush()
    log = (tmp_path / "app.log").read_text(encoding="utf-8")
    assert "ERROR - main: Error fatal al iniciar la app" in log
    assert "RuntimeError: falla simulada" in log
    assert shown and "falla simulada" in shown[0]


def test_app_icon_has_all_sizes(qapp):
    from src.app.windows_integration import load_app_icon

    sizes = {s.width() for s in load_app_icon().availableSizes()}
    assert {16, 24, 32, 48, 64, 256} <= sizes


def test_app_user_model_id_is_set():
    import ctypes
    import sys

    import pytest

    from src.app.windows_integration import APP_USER_MODEL_ID, set_app_user_model_id

    if sys.platform != "win32":
        pytest.skip("sólo Windows")
    set_app_user_model_id()
    value = ctypes.c_wchar_p()
    ctypes.windll.shell32.GetCurrentProcessExplicitAppUserModelID(ctypes.byref(value))
    assert value.value == APP_USER_MODEL_ID
    ctypes.windll.ole32.CoTaskMemFree(value)


def test_shortcut_script_uses_same_app_id():
    from pathlib import Path

    from src.app.windows_integration import APP_USER_MODEL_ID

    script = (Path(main.__file__).resolve().parent / "scripts" / "crear_acceso_directo.ps1").read_text(encoding="utf-8-sig")
    assert f"$appUserModelId = '{APP_USER_MODEL_ID}'" in script
