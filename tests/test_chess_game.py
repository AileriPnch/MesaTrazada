import chess
import pytest

from src.chess_game.game_state import ChessGame


def _play(game: ChessGame, *sans: str) -> None:
    for san in sans:
        game.push(game.board.parse_san(san))


# --- estado de partida --------------------------------------------------------
def test_initial_state_player_white():
    game = ChessGame(chess.WHITE)
    assert game.is_player_turn and not game.is_engine_turn
    assert game.last_move is None and game.result() is None
    assert game.legal_targets(chess.E2) == {chess.E3, chess.E4}
    assert game.legal_targets(chess.E7) == set()  # pieza rival


def test_initial_state_player_black_engine_moves_first():
    game = ChessGame(chess.BLACK)
    assert game.is_engine_turn and not game.is_player_turn


def test_illegal_move_rejected():
    game = ChessGame(chess.WHITE)
    assert game.find_move(chess.E2, chess.E5) is None
    with pytest.raises(ValueError):
        game.push(chess.Move(chess.E2, chess.E5))


def test_san_list_and_last_move():
    game = ChessGame(chess.WHITE)
    _play(game, "e4", "e5", "Nf3")
    assert game.san_moves() == ["e4", "e5", "Nf3"]
    assert game.last_move == chess.Move.from_uci("g1f3")


def test_castling_and_en_passant_are_available():
    game = ChessGame(chess.WHITE, "r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 0 1")
    assert chess.G1 in game.legal_targets(chess.E1) and chess.C1 in game.legal_targets(chess.E1)
    game.push(game.find_move(chess.E5, chess.D6))  # al paso
    assert game.board.piece_at(chess.D5) is None


def test_check_square():
    game = ChessGame(chess.WHITE)
    _play(game, "e4", "f5", "Qh5+")
    assert game.checked_king_square() == chess.E8


# --- coronación ---------------------------------------------------------------
PROMO_FEN = "8/P7/8/8/8/8/8/k6K w - - 0 1"


def test_promotion_requires_choice():
    game = ChessGame(chess.WHITE, PROMO_FEN)
    assert game.needs_promotion(chess.A7, chess.A8)
    assert game.find_move(chess.A7, chess.A8) is None
    assert not game.needs_promotion(chess.H1, chess.H2)


@pytest.mark.parametrize("piece_type", [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
def test_promotion_to_each_piece(piece_type):
    game = ChessGame(chess.WHITE, PROMO_FEN)
    game.push(game.find_move(chess.A7, chess.A8, piece_type))
    assert game.board.piece_at(chess.A8) == chess.Piece(piece_type, chess.WHITE)
    assert game.san_moves()[0].startswith("a8=")


# --- fin de partida -----------------------------------------------------------
def test_checkmate_from_both_perspectives():
    for player, headline in ((chess.WHITE, "Ganó Stockfish"), (chess.BLACK, "Ganaste")):
        game = ChessGame(player)
        _play(game, "f3", "e5", "g4", "Qh4#")
        result = game.result()
        assert result.reason == "Jaque mate" and result.headline == headline
        assert result.winner == chess.BLACK
        assert not game.is_player_turn and not game.is_engine_turn


def test_stalemate():
    result = ChessGame(chess.WHITE, "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1").result()
    assert (result.headline, result.reason) == ("Tablas", "Ahogado")


@pytest.mark.parametrize("fen", ["8/8/8/8/8/8/8/K6k w - - 0 1", "8/8/8/8/8/8/8/KB5k w - - 0 1"])
def test_insufficient_material(fen):
    result = ChessGame(chess.WHITE, fen).result()
    assert (result.headline, result.reason) == ("Tablas", "Material insuficiente")


def test_threefold_repetition_only_when_it_happens():
    game = ChessGame(chess.WHITE)
    _play(game, "Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1")
    assert game.board.can_claim_threefold_repetition()  # python-chess ya permitiría reclamar...
    assert game.result() is None  # ...pero la partida sigue hasta que ocurra
    _play(game, "Ng8")
    assert game.result().reason == "Triple repetición"


def test_fifty_move_rule_only_when_it_happens():
    game = ChessGame(chess.WHITE, "8/8/8/8/8/8/R7/K6k w - - 99 80")
    assert game.result() is None
    _play(game, "Ra3")
    assert game.result().reason == "Regla de los 50 movimientos"


# --- deshacer -----------------------------------------------------------------
def test_undo_my_move_and_engine_reply():
    game = ChessGame(chess.WHITE)
    _play(game, "e4", "e5")
    assert game.undo() == 2
    assert game.board.fen() == chess.STARTING_FEN


def test_undo_while_engine_to_move_only_removes_my_move():
    game = ChessGame(chess.WHITE)
    _play(game, "e4")
    assert game.undo() == 1 and game.is_player_turn


def test_undo_as_black_never_removes_engine_first_move_alone():
    game = ChessGame(chess.BLACK)
    assert game.undo() == 0
    _play(game, "e4")
    assert game.plies_to_undo() == 0
    _play(game, "e5", "Nf3")
    assert game.undo() == 2
    assert game.san_moves() == ["e4"] and game.is_player_turn


def test_undo_after_game_over_reopens_game():
    game = ChessGame(chess.WHITE)
    _play(game, "f3", "e5", "g4", "Qh4#")
    assert game.undo() == 2
    assert game.result() is None and game.is_player_turn
