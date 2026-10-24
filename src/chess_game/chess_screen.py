"""Pantalla de ajedrez: une partida, motor, tablero y los objetos de la mesa (reloj, planilla, carteles,
bandejas, placas, tarjeta de fin de partida). Color y dificultad se eligen en la pantalla de inicio; "Nueva
partida" repite esa elección (al azar vuelve a sortear)."""
import logging

import chess

from config import settings
from src.chess_game.chess_dialogs import MessageDialog, show_engine_error
from src.chess_game.chess_table import ChessTable
from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty, Mode, level_for
from src.chess_game.engine_controller import EngineController
from src.chess_game.game_state import ChessGame
from src.chess_game.move_sound import END_DELAY_MS, end_sound, move_sound
from src.chess_game.promotion_dialog import ask_promotion
from src.common import sound

logger = logging.getLogger(__name__)

SCORES = {chess.WHITE: "1–0", chess.BLACK: "0–1", None: "½–½"}


def rival_label(difficulty: Difficulty) -> str:
    """Lo que dice el cartel del rival: nivel y Elo aproximado."""
    level = level_for(difficulty, settings)
    return f"{difficulty.value} · Stockfish" if level.mode is Mode.FULL else f"{difficulty.value} · ≈{level.elo}"


class ChessScreen(ChessTable):
    title = "Ajedrez"

    def __init__(self, parent=None, engine_factory=None):
        super().__init__(parent)
        self.ask_promotion = ask_promotion  # reemplazable en tests
        self.game: ChessGame | None = None
        self.color_choice = ColorChoice.WHITE
        self.difficulty = Difficulty.BEGINNER
        self.error_box: MessageDialog | None = None
        self.engine_error: str | None = None  # si el motor falta o falló: se muestra en la tarjeta

        self.side.back_requested.connect(self.back_requested.emit)
        self.side.undo_requested.connect(self.undo)
        self.side.new_game_requested.connect(self.new_game)
        self.board_view.move_attempted.connect(self._on_player_move)

        self.engine = self._create_engine(engine_factory)

    def _create_engine(self, factory) -> EngineController | None:
        path = settings.stockfish_path
        if factory is None and not path.is_file():
            logger.error("No se encontró Stockfish en %s", path)
            self.engine_error = f"No se encontró Stockfish en {path}. Revisá STOCKFISH_PATH en el archivo .env."
            return None
        engine = EngineController(path, factory, parent=self, min_reply=settings.engine_min_reply)
        engine.ready.connect(self._on_engine_ready)
        engine.failed.connect(self._on_engine_failed)
        engine.move_ready.connect(self._on_engine_move)
        engine.start()
        return engine

    # --- flujo de la partida ------------------------------------------------
    def start_game(self, color: ColorChoice, difficulty: Difficulty) -> None:
        if self.engine is not None:
            self.engine.cancel()  # una búsqueda de la partida anterior se descarta
        player = color.resolve()
        self.color_choice, self.difficulty = color, difficulty
        self.game = ChessGame(player)
        self.board_view.set_game(self.game, flipped=player == chess.BLACK)
        self.side.set_info(rival_label(difficulty), player)
        side = "blancas" if player == chess.WHITE else "negras"
        logger.info("Partida nueva: jugador con %s, dificultad %s", side, difficulty.value)
        self._advance()

    def new_game(self) -> None:
        self.start_game(self.color_choice, self.difficulty)

    def undo(self) -> None:
        if self.game is None or self.game.plies_to_undo() == 0:
            return
        if self.engine is not None:
            self.engine.cancel()
        undone = self.game.undo()
        logger.info("Deshechas %s medias jugadas", undone)
        self._advance()

    def _on_player_move(self, from_sq: int, to_sq: int) -> None:
        if self.game is None or not self.game.is_player_turn:
            return
        promotion = None
        if self.game.needs_promotion(from_sq, to_sq):
            promotion = self.ask_promotion(self.game.player_color, self)
            if promotion is None:
                return
        move = self.game.find_move(from_sq, to_sq, promotion)
        if move is None:
            return
        self._push(move)

    def _on_engine_move(self, move: chess.Move) -> None:
        # Defensa extra además del descarte por número de pedido.
        if self.game is None or not self.game.is_engine_turn or move not in self.game.board.legal_moves:
            logger.warning("Jugada del motor %s ignorada: no corresponde a la posición actual", move)
            return
        self._push(move)

    def _push(self, move: chess.Move) -> None:
        sound.play(move_sound(self.game.board, move))
        self.game.push(move)
        self._advance()

    def _advance(self) -> None:
        """Refresca la UI y decide quién mueve después de cada cambio de posición."""
        game, side = self.game, self.side
        side.set_moves(game.san_moves())
        side.set_board(game.board)
        side.undo_button.setEnabled(game.plies_to_undo() > 0)
        result = game.result()
        mate = result is not None and result.termination == chess.Termination.CHECKMATE
        self.board_view.set_toppled(game.board.king(game.board.turn) if mate else None)  # el rey vencido se acuesta
        side.sheet.set_result(f"{SCORES[result.winner]} · {result.reason}" if result else "")
        if result is not None:
            self.board_view.set_interactive(False)
            side.clock.set_over()
            side.set_status(f"{result.headline} — {result.reason}")
            self._show_result(result)
        elif self.engine_error is not None:
            self.board_view.set_interactive(False)
            side.clock.set_over()
            side.set_status(self.engine_error)
            side.show_card("Sin motor", self.engine_error)
        elif game.is_engine_turn and self.engine is not None:
            self.board_view.set_interactive(False)
            side.hide_card()
            side.clock.set_turn(game.board.turn, thinking=True)  # la luz de su lado: "Stockfish está pensando"
            side.set_status("Stockfish está pensando…")
            self.engine.request_move(game.board, level_for(self.difficulty, settings))
        else:
            self.board_view.set_interactive(True)
            side.hide_card()
            side.clock.set_turn(game.board.turn)
            side.set_status("Jaque. Tu turno." if game.board.is_check() else "Tu turno.")
        self.board_view.update()

    def _show_result(self, result) -> None:
        logger.info("Fin de la partida: %s (%s)", result.headline, result.reason)
        sound.play_later(end_sound(result, self.game.player_color), END_DELAY_MS)
        self.side.show_card(result.headline, f"{result.reason} · {SCORES[result.winner]}")

    def _on_engine_ready(self) -> None:
        logger.info("Motor listo")

    def _on_engine_failed(self, message: str) -> None:
        logger.error("Falló el motor: %s", message)
        self.engine_error = "El motor dejó de funcionar. Volvé al menú para reintentar."
        if self.game is not None:
            self.board_view.set_interactive(False)
            self.side.clock.set_over()
            self.side.set_status(self.engine_error)
            self.side.show_card("Error del motor", self.engine_error)
            self.error_box = show_engine_error(self, self.u, message)

    def shutdown(self) -> None:
        if self.engine is not None:
            self.engine.shutdown()
