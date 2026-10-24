"""Estado de una partida jugador vs motor. Lógica pura sobre python-chess, sin Qt."""
from dataclasses import dataclass

import chess

_REASONS = {
    chess.Termination.CHECKMATE: "Jaque mate",
    chess.Termination.STALEMATE: "Ahogado",
    chess.Termination.INSUFFICIENT_MATERIAL: "Material insuficiente",
    chess.Termination.SEVENTYFIVE_MOVES: "Regla de los 75 movimientos",
    chess.Termination.FIVEFOLD_REPETITION: "Quíntuple repetición",
    chess.Termination.FIFTY_MOVES: "Regla de los 50 movimientos",
    chess.Termination.THREEFOLD_REPETITION: "Triple repetición",
}


@dataclass(frozen=True)
class GameResult:
    winner: chess.Color | None  # None = tablas
    termination: chess.Termination
    headline: str  # "Ganaste", "Ganó Stockfish", "Tablas"
    reason: str


class ChessGame:
    def __init__(self, player_color: chess.Color, fen: str = chess.STARTING_FEN):
        self.player_color = player_color
        self.board = chess.Board(fen)

    @property
    def is_over(self) -> bool:
        return self.result() is not None

    @property
    def is_player_turn(self) -> bool:
        return self.board.turn == self.player_color and not self.is_over

    @property
    def is_engine_turn(self) -> bool:
        return self.board.turn != self.player_color and not self.is_over

    @property
    def last_move(self) -> chess.Move | None:
        return self.board.move_stack[-1] if self.board.move_stack else None

    def legal_targets(self, square: chess.Square) -> set[chess.Square]:
        return {m.to_square for m in self.board.legal_moves if m.from_square == square}

    def needs_promotion(self, from_sq: chess.Square, to_sq: chess.Square) -> bool:
        return any(m.promotion for m in self.board.legal_moves if m.from_square == from_sq and m.to_square == to_sq)

    def find_move(self, from_sq: chess.Square, to_sq: chess.Square, promotion: int | None = None) -> chess.Move | None:
        move = chess.Move(from_sq, to_sq, promotion=promotion)
        return move if move in self.board.legal_moves else None

    def push(self, move: chess.Move) -> None:
        if self.is_over or move not in self.board.legal_moves:
            raise ValueError(f"Jugada ilegal en esta posición: {move}")
        self.board.push(move)

    def plies_to_undo(self) -> int:
        """Medias jugadas a deshacer para volver a la última posición en que me tocaba mover.

        - Turno del motor (está pensando o le di mate): deshago sólo mi jugada.
        - Mi turno: deshago la respuesta del motor y mi jugada. Si sólo existe la primera
          jugada del motor (juego con negras), no hay nada mío para deshacer.
        """
        plies = len(self.board.move_stack)
        if plies == 0:
            return 0
        if self.board.turn != self.player_color:
            return 1
        return 2 if plies >= 2 else 0

    def undo(self) -> int:
        count = self.plies_to_undo()
        for _ in range(count):
            self.board.pop()
        return count

    def checked_king_square(self) -> chess.Square | None:
        return self.board.king(self.board.turn) if self.board.is_check() else None

    def result(self) -> GameResult | None:
        outcome = self.board.outcome()  # mate, ahogado, material insuficiente, 75 movs, 5 repeticiones
        if outcome is None:
            # Se aplican automáticamente, pero sólo cuando YA ocurrieron. No usar
            # outcome(claim_draw=True): también reclama si una jugada posible las alcanzaría.
            if self.board.is_repetition(3):
                outcome = chess.Outcome(chess.Termination.THREEFOLD_REPETITION, None)
            elif self.board.halfmove_clock >= 100:
                outcome = chess.Outcome(chess.Termination.FIFTY_MOVES, None)
            else:
                return None
        if outcome.winner is None:
            headline = "Tablas"
        elif outcome.winner == self.player_color:
            headline = "Ganaste"
        else:
            headline = "Ganó Stockfish"
        return GameResult(outcome.winner, outcome.termination, headline, _REASONS[outcome.termination])

    def san_moves(self) -> list[str]:
        replay = self.board.root()
        sans = []
        for move in self.board.move_stack:
            sans.append(replay.san(move))
            replay.push(move)
        return sans
