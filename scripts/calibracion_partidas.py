"""Jugadores y una partida para scripts/calibrar_dificultad.py. Sin Qt.

Cada partida abre sus propios procesos de Stockfish (Threads=1, tabla hash limpia) y cada jugador usa su
propio RNG con semilla: con la misma semilla la partida se repite igual (salvo los niveles por tiempo,
que dependen de la carga de la máquina).
"""
import random
import time
from dataclasses import dataclass, replace

import chess

from config import settings
from src.chess_game.difficulty import Difficulty, level_for
from src.chess_game.engine_search import elo_range, search_move
from src.chess_game.engine_worker import open_stockfish

PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
MAX_PLIES = 600  # 300 jugadas por lado sin final = tablas
LEVELS = {"principiante": Difficulty.BEGINNER, "novato": Difficulty.NOVICE, "aficionado": Difficulty.AMATEUR,
          "club": Difficulty.CLUB, "avanzado": Difficulty.ADVANCED, "maximo": Difficulty.MAXIMUM}
# Aperturas cortas y equilibradas: cada una se juega con los dos colores (no repetir partidas).
OPENINGS = [
    "e2e4 e7e5 g1f3 b8c6", "e2e4 c7c5 g1f3 d7d6", "d2d4 d7d5 c2c4 e7e6", "d2d4 g8f6 c2c4 g7g6",
    "e2e4 e7e6 d2d4 d7d5", "e2e4 c7c6 d2d4 d7d5", "c2c4 e7e5 b1c3 g8f6", "g1f3 d7d5 g2g3 g8f6",
    "e2e4 e7e5 f1c4 g8f6", "d2d4 d7d5 g1f3 g8f6",
]


class Player:
    """Un nivel de la app, Stockfish con UCI_Elo fijo ("sf1320"), "azar" o "gloton"."""

    def __init__(self, spec: str, rng: random.Random):
        self.spec, self.rng, self.engine, self.level = spec, rng, None, None
        if spec in LEVELS or spec.startswith("sf"):
            self.engine = open_stockfish(settings.stockfish_path)
            self.engine.configure({"Threads": 1, "Hash": 16})
            if spec.startswith("sf"):  # ancla: Stockfish limitado, al mismo tiempo por jugada que Club
                elo = max(int(spec[2:]), elo_range(self.engine)[0])
                self.level = replace(level_for(Difficulty.CLUB, settings), elo=elo)
            else:
                self.level = level_for(LEVELS[spec], settings)

    def move(self, board: chess.Board) -> chess.Move:
        if self.engine is not None:
            return search_move(self.engine, board, self.level, self.rng).move
        moves = list(board.legal_moves)
        if self.spec == "gloton":  # captura lo más valioso que pueda; si no hay capturas, al azar
            captures = [m for m in moves if board.is_capture(m)]
            if captures:
                best = max(_captured_value(board, m) for m in captures)
                moves = [m for m in captures if _captured_value(board, m) == best]
        return self.rng.choice(moves)

    def close(self) -> None:
        if self.engine is not None:
            self.engine.quit()


def _captured_value(board: chess.Board, move: chess.Move) -> int:
    if board.is_en_passant(move):
        return PIECE_VALUE[chess.PAWN]
    return PIECE_VALUE[board.piece_type_at(move.to_square)]


@dataclass(frozen=True)
class GameResult:
    score: float  # del primer jugador (el "de arriba"): 1, 0.5 o 0
    plies: int
    seconds: float


def finished(board: chess.Board) -> bool:
    return (board.is_game_over() or board.is_repetition(3) or board.halfmove_clock >= 100
            or board.ply() >= MAX_PLIES)


def play_game(task: tuple[str, str, int, int]) -> tuple[str, str, GameResult]:
    """task = (jugador, rival, número de partida, semilla). Las pares, el jugador lleva blancas."""
    upper, lower, index, seed = task
    started = time.monotonic()
    upper_white = index % 2 == 0
    players = {chess.WHITE: None, chess.BLACK: None}
    try:
        players[upper_white] = Player(upper, random.Random(f"{seed}-{index}-{upper}"))
        players[not upper_white] = Player(lower, random.Random(f"{seed}-{index}-{lower}"))
        board = chess.Board()
        for uci in OPENINGS[(index // 2) % len(OPENINGS)].split():
            board.push_uci(uci)
        while not finished(board):
            board.push(players[board.turn].move(board))
    finally:
        for player in players.values():
            if player is not None:
                player.close()
    if board.is_checkmate():
        winner_white = board.turn == chess.BLACK
        score = 1.0 if winner_white == upper_white else 0.0
    else:
        score = 0.5
    return upper, lower, GameResult(score, board.ply(), time.monotonic() - started)

