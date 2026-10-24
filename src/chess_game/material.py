"""Piezas capturadas y diferencia de material, a partir del tablero (lógica pura, sin Qt). Una coronación no
cuenta como captura: la pieza coronada "devuelve" el peón que le falta a ese color."""
import chess

VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
START = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
ORDER = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN)  # de mayor a menor valor


def lost_pieces(board: chess.Board, color: chess.Color) -> list[chess.Piece]:
    """Las piezas de `color` que ya no están (las capturó el rival), de mayor a menor valor."""
    counts = {t: len(board.pieces(t, color)) for t in START}
    promoted = sum(max(0, counts[t] - START[t]) for t in START if t != chess.PAWN)
    missing = {t: max(0, START[t] - counts[t]) for t in START}
    missing[chess.PAWN] = max(0, START[chess.PAWN] - counts[chess.PAWN] - promoted)
    return [chess.Piece(t, color) for t in ORDER for _ in range(missing[t])]


def balance(board: chess.Board, color: chess.Color) -> int:
    """Material de `color` menos el del rival (1, 3, 3, 5, 9)."""
    def total(side: chess.Color) -> int:
        return sum(VALUES[t] * len(board.pieces(t, side)) for t in VALUES)
    return total(color) - total(not color)
