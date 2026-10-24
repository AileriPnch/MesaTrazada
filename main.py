"""Punto de entrada de la app. Pensado para correr con pythonw.exe (sin consola)."""
import logging
import sys
from time import perf_counter

from src.common.logging_setup import setup_logging
from src.common.paths import default_log_dir, frozen, migrate_legacy_data

STARTED = perf_counter()  # para medir el arranque (prueba de humo del build)

DEFAULT_LOG_DIR = default_log_dir()  # logs/ del proyecto, o %LOCALAPPDATA% en el build

logger = logging.getLogger("main")


def _log_uncaught(exc_type, exc_value, exc_tb) -> None:
    """Sin este hook, PyQt6 aborta la app ante una excepción no capturada en un slot."""
    logger.critical("Excepción no capturada", exc_info=(exc_type, exc_value, exc_tb))


def _show_fatal_error(message: str) -> None:
    """Muestra el error en pantalla: con pythonw no hay consola donde verlo."""
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841 (debe vivir)
        QMessageBox.critical(None, "Error al iniciar", message)
    except Exception:
        logger.exception("No se pudo mostrar el diálogo de error")


def _start_sound() -> None:
    """QtMultimedia tarda en arrancar: se carga con la ventana ya visible. Si falla, la app sigue sin sonido."""
    from src.common import sound

    try:
        sound.install(player=sound.SoundPlayer(sound.volume()))
    except Exception:
        logger.exception("No se pudo iniciar el sonido; la app sigue sin sonido")


def _run() -> int:
    # Imports diferidos: un .env inválido o un PyQt6 roto también deben quedar en el log.
    from config import settings

    if settings.log_dir != DEFAULT_LOG_DIR or settings.log_level.upper() != "INFO":
        setup_logging(settings.log_dir, settings.log_level)

    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication

    from src.app.main_window import APP_TITLE, MainWindow
    from src.app.stylesheet import apply_theme
    from src.app.windows_integration import load_app_icon, set_app_user_model_id
    from src.common import sound
    from src.common.fonts import load_fonts
    from src.common.volume import Volume, settings_store

    set_app_user_model_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setWindowIcon(load_app_icon())
    load_fonts()
    apply_theme(app)
    sound.install(Volume(settings_store()))  # volumen y silencio de la sesión anterior
    window = MainWindow()
    window.show()
    QTimer.singleShot(0, _start_sound)
    from src.app.smoke_test import run_smoke_test, smoke_output

    if (report := smoke_output(sys.argv)) is not None:  # build: --autoprueba <informe.json>
        run_smoke_test(window, report, STARTED)
    logger.info("App iniciada")
    code = app.exec()
    logger.info("App cerrada (código %s)", code)
    return code


def main() -> int:
    migrated = migrate_legacy_data() if frozen() else "nada"  # antes de abrir el log nuevo
    setup_logging(DEFAULT_LOG_DIR)
    if migrated != "nada":
        logger.info("Datos del nombre anterior: %s", migrated)
    sys.excepthook = _log_uncaught
    try:
        return _run()
    except Exception as exc:
        logger.exception("Error fatal al iniciar la app")
        _show_fatal_error(f"{type(exc).__name__}: {exc}\n\nDetalle en {DEFAULT_LOG_DIR / 'app.log'}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
