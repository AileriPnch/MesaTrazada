"""Configuración central: lee .env (opcional: sin él valen los defaults) y expone un dataclass Settings."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from src.common import paths

PROJECT_ROOT = Path(__file__).resolve().parent  # recursos (en el build: _internal/)
load_dotenv(paths.install_dir() / ".env")  # junto al .exe en el build; si no existe, defaults


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _resolve(path: str) -> Path:
    """Rutas relativas se resuelven contra la raíz del proyecto, no contra el cwd."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


@dataclass(frozen=True)
class HumanLevel:
    """Debilitamiento propio (niveles por debajo del mínimo de UCI_Elo): ver chess_game/move_choice.py."""
    elo: int  # aproximado, sólo para mostrar
    depth: int  # profundidad de la búsqueda
    multipv: int  # candidatas que se evalúan
    temperature: float  # cp del softmax: más alta = elige peores más seguido
    blunder: float  # probabilidad de descuido
    blunder_min_cp: int  # el descuido pierde entre min y max centipeones
    blunder_max_cp: int
    obvious: float  # probabilidad de ver el mate en 1 o la captura gratis
    obvious_cp: int  # ventaja sobre la 2.ª candidata para que una captura sea "gratis"


def _human(prefix: str, elo: int, depth: int, multipv: int, temperature: float, blunder: float,
           blunder_min_cp: int, blunder_max_cp: int, obvious: float) -> HumanLevel:
    return HumanLevel(
        elo=_env_int(f"{prefix}_ELO", elo),
        depth=_env_int(f"{prefix}_DEPTH", depth),
        multipv=_env_int(f"{prefix}_MULTIPV", multipv),
        temperature=_env_float(f"{prefix}_TEMP", temperature),
        blunder=_env_float(f"{prefix}_BLUNDER", blunder),
        blunder_min_cp=_env_int(f"{prefix}_BLUNDER_MIN_CP", blunder_min_cp),
        blunder_max_cp=_env_int(f"{prefix}_BLUNDER_MAX_CP", blunder_max_cp),
        obvious=_env_float(f"{prefix}_OBVIOUS", obvious),
        obvious_cp=_env_int("OBVIOUS_CP", 250),
    )


@dataclass
class Settings:
    log_level: str = field(default_factory=lambda: _env_str("LOG_LEVEL", "INFO"))
    log_dir: Path = field(default_factory=lambda: _resolve(os.environ["LOG_DIR"]) if os.getenv("LOG_DIR")
                          else paths.default_log_dir())
    stockfish_path: Path = field(
        default_factory=lambda: _resolve(_env_str("STOCKFISH_PATH", "engine/stockfish.exe"))
    )
    # Dificultad. Niveles bajos: debilitamiento propio; Club y Avanzado: UCI_Elo de Stockfish (se ajusta
    # al rango que reporta el motor); Máximo: sin límite. *_TIME = segundos por jugada.
    # _human(prefijo, elo, depth, multipv, temp, blunder, blunder_min_cp, blunder_max_cp, obvious)
    principiante: HumanLevel = field(
        default_factory=lambda: _human("PRINCIPIANTE", 500, 1, 12, 300, 0.5, 150, 900, 0.5))
    novato: HumanLevel = field(default_factory=lambda: _human("NOVATO", 800, 2, 12, 250, 0.4, 150, 700, 0.7))
    aficionado: HumanLevel = field(
        default_factory=lambda: _human("AFICIONADO", 1100, 2, 10, 150, 0.25, 150, 600, 0.9))
    club_elo: int = field(default_factory=lambda: _env_int("CLUB_ELO", 1400))
    club_time: float = field(default_factory=lambda: _env_float("CLUB_TIME", 0.3))
    avanzado_elo: int = field(default_factory=lambda: _env_int("AVANZADO_ELO", 1800))
    avanzado_time: float = field(default_factory=lambda: _env_float("AVANZADO_TIME", 0.5))
    maximo_time: float = field(default_factory=lambda: _env_float("MAXIMO_TIME", 1.0))
    # El motor nunca responde antes de esto (aunque calcule en menos): ritmo humano
    engine_min_reply: float = field(default_factory=lambda: _env_float("ENGINE_MIN_REPLY", 0.6))


settings = Settings()
