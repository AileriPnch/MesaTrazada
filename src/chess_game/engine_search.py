"""Una jugada del motor según el nivel. La usan EngineWorker (app) y scripts/calibrar_dificultad.py. Sin Qt.

Cada búsqueda deja configuradas TODAS las opciones de su modo (UCI_LimitStrength, UCI_Elo, Skill Level): el
mismo proceso pasa de una partida en Club a una en Principiante sin heredar nada. MultiPV no se puede fijar con
configure() (python-chess lo maneja): play() lo vuelve a 1 y analyse() lo fija con su argumento `multipv`.
"""
import logging
import random

import chess
import chess.engine

from src.chess_game.difficulty import EngineLevel, Mode
from src.chess_game.move_choice import Choice, candidates, choose

logger = logging.getLogger(__name__)

MAX_SKILL = 20


def elo_range(engine) -> tuple[int, int]:
    """Mínimo y máximo de UCI_Elo según lo que reporta el motor (Stockfish 19: 1320-3190)."""
    option = engine.options["UCI_Elo"]
    return int(option.min), int(option.max)


def configure_for(engine, level: EngineLevel) -> None:
    low, high = elo_range(engine)
    limited = level.mode is Mode.LIMITED
    elo = min(max(level.elo, low), high) if limited else high
    if limited and elo != level.elo:
        logger.warning("UCI_Elo %s fuera del rango del motor (%s-%s): se usa %s", level.elo, low, high, elo)
    engine.configure({"UCI_LimitStrength": limited, "UCI_Elo": elo, "Skill Level": MAX_SKILL})


def search_move(engine, board: chess.Board, level: EngineLevel, rng: random.Random) -> Choice | None:
    legal = list(board.legal_moves)
    if not legal:
        return None
    if len(legal) == 1:  # no hay nada que pensar
        return Choice(legal[0], 0, "única")
    configure_for(engine, level)
    if level.mode is Mode.HUMAN:
        params = level.human
        infos = engine.analyse(board, chess.engine.Limit(depth=params.depth), multipv=params.multipv)
        cands = candidates(infos, board)
        if cands:
            return choose(cands, board, params, rng)
        logger.warning("El análisis no dio candidatas legales: se juega la mejor de una búsqueda simple")
        limit = chess.engine.Limit(depth=params.depth)
    else:
        limit = chess.engine.Limit(time=level.seconds)
    result = engine.play(board, limit)
    if result.move is None or result.move not in board.legal_moves:
        return None
    return Choice(result.move, 0, "mejor")
