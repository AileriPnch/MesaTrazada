"""Niveles de dificultad y su traducción a parámetros del motor (desde Settings)."""
from dataclasses import dataclass
from enum import Enum

from config import HumanLevel, Settings


class Difficulty(Enum):
    BEGINNER = "Principiante"
    NOVICE = "Novato"
    AMATEUR = "Aficionado"
    CLUB = "Club"
    ADVANCED = "Avanzado"
    MAXIMUM = "Máximo"


class Mode(Enum):
    HUMAN = "humano"  # debilitamiento propio: MultiPV + softmax + descuidos (move_choice)
    LIMITED = "limitado"  # UCI_LimitStrength + UCI_Elo de Stockfish
    FULL = "pleno"  # Stockfish sin límite


@dataclass(frozen=True)
class EngineLevel:
    mode: Mode
    elo: int = 0  # aproximado (humano) o UCI_Elo pedido (limitado); 0 = sin límite
    seconds: float = 0.0  # tiempo por jugada (limitado y pleno; el humano limita por profundidad)
    human: HumanLevel | None = None


def level_for(difficulty: Difficulty, settings: Settings) -> EngineLevel:
    table = {
        Difficulty.BEGINNER: _human(settings.principiante),
        Difficulty.NOVICE: _human(settings.novato),
        Difficulty.AMATEUR: _human(settings.aficionado),
        Difficulty.CLUB: EngineLevel(Mode.LIMITED, settings.club_elo, settings.club_time),
        Difficulty.ADVANCED: EngineLevel(Mode.LIMITED, settings.avanzado_elo, settings.avanzado_time),
        Difficulty.MAXIMUM: EngineLevel(Mode.FULL, 0, settings.maximo_time),
    }
    return table[difficulty]


def _human(params: HumanLevel) -> EngineLevel:
    return EngineLevel(Mode.HUMAN, params.elo, 0.0, params)


def describe(level: EngineLevel) -> str:
    """Texto del tooltip en el inicio."""
    if level.mode is Mode.FULL:
        return f"Stockfish a pleno, sin límite · {level.seconds:g} s por jugada"
    return f"≈ {level.elo} Elo"
