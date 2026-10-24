"""search_move con el motor falso: opciones de cada modo, Máximo = mejor jugada, bordes, nunca ilegal."""
import logging
import random

import chess
import pytest

from config import settings
from src.chess_game.difficulty import Difficulty, EngineLevel, Mode, level_for
from src.chess_game.engine_search import search_move
from tests.fakes import ELO_MAX, ELO_MIN, FakeEngine


def level(difficulty: Difficulty) -> EngineLevel:
    return level_for(difficulty, settings)


def test_options_never_carry_over_between_levels():
    engine = FakeEngine()
    board = chess.Board()
    search_move(engine, board, level(Difficulty.CLUB), random.Random(0))
    club = level(Difficulty.CLUB).elo
    assert engine.config == {"UCI_LimitStrength": True, "UCI_Elo": min(max(club, ELO_MIN), ELO_MAX),
                             "Skill Level": 20, "MultiPV": 1}
    search_move(engine, board, level(Difficulty.BEGINNER), random.Random(0))
    assert engine.config == {"UCI_LimitStrength": False, "UCI_Elo": ELO_MAX, "Skill Level": 20,
                             "MultiPV": settings.principiante.multipv}
    search_move(engine, board, level(Difficulty.MAXIMUM), random.Random(0))
    assert engine.config == {"UCI_LimitStrength": False, "UCI_Elo": ELO_MAX, "Skill Level": 20, "MultiPV": 1}


def test_elo_outside_engine_range_is_clamped(caplog):
    engine = FakeEngine()
    with caplog.at_level(logging.WARNING):
        search_move(engine, chess.Board(), EngineLevel(Mode.LIMITED, 600, 0.01), random.Random(0))
    assert engine.config["UCI_Elo"] == ELO_MIN and "fuera del rango" in caplog.text
    search_move(engine, chess.Board(), EngineLevel(Mode.LIMITED, 9000, 0.01), random.Random(0))
    assert engine.config["UCI_Elo"] == ELO_MAX


def test_maximum_plays_the_engine_best_move():
    engine = FakeEngine(script=["g1f3"])
    choice = search_move(engine, chess.Board(), level(Difficulty.MAXIMUM), random.Random(0))
    assert choice.move == chess.Move.from_uci("g1f3") and choice.loss == 0


def test_single_legal_move_is_played_without_searching():
    board = chess.Board("7k/8/8/8/8/8/6q1/7K w - - 0 1")  # sólo Kxg2
    assert board.legal_moves.count() == 1
    engine = FakeEngine()
    choice = search_move(engine, board, level(Difficulty.BEGINNER), random.Random(0))
    assert choice.move in board.legal_moves and choice.reason == "única" and engine.searches == 0


def test_fewer_candidates_than_multipv():
    engine = FakeEngine(evals={"e2e4": 30, "d2d4": 20})  # analyse devuelve 2 aunque se pidan 12
    picks = {search_move(engine, chess.Board(), level(Difficulty.BEGINNER), random.Random(i)).move.uci()
             for i in range(40)}
    assert picks <= {"e2e4", "d2d4"} and engine.config["MultiPV"] == settings.principiante.multipv


def test_analysis_of_another_position_falls_back_to_a_legal_move():
    engine = FakeEngine(evals={"e7e5": 0}, script=["e2e4"])  # PV de negras con blancas a mover
    choice = search_move(engine, chess.Board(), level(Difficulty.NOVICE), random.Random(0))
    assert choice.move == chess.Move.from_uci("e2e4")


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_never_returns_an_illegal_move(difficulty):
    rng = random.Random(difficulty.value)
    engine = FakeEngine()
    for _ in range(4):  # partidas al azar: el nivel juega en cada posición de su turno
        board = chess.Board()
        while not board.is_game_over() and board.ply() < 120:
            choice = search_move(engine, board, level(difficulty), rng)
            assert choice is not None and choice.move in board.legal_moves
            board.push(rng.choice(list(board.legal_moves)) if board.ply() % 2 else choice.move)
