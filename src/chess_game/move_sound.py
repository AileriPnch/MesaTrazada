"""Qué sonido corresponde a cada jugada y al final de la partida. Lógica pura sobre python-chess."""
import chess

from src.chess_game.game_state import GameResult
from src.common.sound import Sound

END_DELAY_MS = 380  # el sonido del final llega después del de la última jugada


def move_sound(board: chess.Board, move: chess.Move) -> Sound:
    """Sonido de `move` en `board` (antes de hacerla). Si da jaque, manda el jaque."""
    if board.gives_check(move):
        return Sound.CHECK
    if move.promotion:
        return Sound.PROMOTE
    if board.is_castling(move):
        return Sound.CASTLE
    if board.is_capture(move):
        return Sound.CAPTURE
    return Sound.MOVE


def end_sound(result: GameResult, player: chess.Color) -> Sound:
    """Un sonido para ganar y otro para perder o tablas."""
    return Sound.WIN if result.winner == player else Sound.LOSE
