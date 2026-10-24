"""Configuración de logging estándar: consola (si existe) + logs/app.log."""
import logging
import sys
from pathlib import Path

LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_dir: Path, level: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
    ]
    # Con pythonw.exe no hay consola y sys.stderr es None: un StreamHandler fallaría.
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=handlers,
        force=True,
    )
