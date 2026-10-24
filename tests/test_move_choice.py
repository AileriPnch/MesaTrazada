"""Elección humana entre candidatas: softmax con semilla, descuidos, ver lo obvio, candidatas inválidas."""
import math
import random
from collections import Counter
from dataclasses import replace

import chess
import chess.engine

from config import HumanLevel
from src.chess_game.move_choice import MATE_CP, Candidate, candidates, choose, softmax_weights

QUIET = HumanLevel(elo=500, depth=4, multipv=8, temperature=100, blunder=0.0, blunder_min_cp=150,
                   blunder_max_cp=400, obvious=0.0, obvious_cp=250)
DRAWS = 10_000


def cands(board: chess.Board, cps: list[int]) -> list[Candidate]:
    moves = sorted(board.legal_moves, key=lambda m: (board.is_capture(m), m.uci()))  # sin capturas primero
    return [Candidate(m, cp) for m, cp in zip(moves, cps)]


def frequencies(cs, board, params, seed=7):
    rng = random.Random(seed)
    picks = Counter(choose(cs, board, params, rng).move for _ in range(DRAWS))
    return [picks[c.move] / DRAWS for c in cs]


def test_softmax_distribution_matches_temperature():
    board = chess.Board()
    cs = cands(board, [0, -50, -100, -300])
    weights = [math.exp(-loss / 100) for loss in (0, 50, 100, 300)]
    expected = [w / sum(weights) for w in weights]
    got = frequencies(cs, board, QUIET)
    assert all(abs(g - e) < 0.02 for g, e in zip(got, expected)), (got, expected)


def test_same_seed_same_choices():
    board = chess.Board()
    cs = cands(board, [0, -20, -40, -60, -80])
    runs = [[choose(cs, board, QUIET, rng).move for _ in range(50)] for rng in (random.Random(3), random.Random(3))]
    assert runs[0] == runs[1]


def test_zero_temperature_always_best():
    assert softmax_weights([0, 5, 300], 0) == [1.0, 0.0, 0.0]
    board = chess.Board()
    cs = cands(board, [0, -5, -300])
    assert frequencies(cs, board, replace(QUIET, temperature=0))[0] == 1.0


def test_blunder_stays_in_range_prefers_smaller_losses_and_never_mated():
    board = chess.Board()
    cs = cands(board, [0, -50, -200, -350, -600, -MATE_CP + 2, -MATE_CP + 3])
    got = frequencies(cs, board, replace(QUIET, blunder=1.0, blunder_max_cp=MATE_CP * 2))
    assert got[5] == got[6] == 0  # recibir mate nunca es un descuido, aunque esté en el rango
    in_range = replace(QUIET, blunder=1.0)
    got = frequencies(cs, board, in_range)
    assert got[0] == got[1] == got[4] == 0
    assert abs(got[2] - (1 / 200) / (1 / 200 + 1 / 350)) < 0.02  # peso inverso a la pérdida


def test_blunder_without_candidates_in_range_falls_back_to_softmax():
    board = chess.Board()
    cs = cands(board, [0, -20, -900])
    rng = random.Random(1)
    reasons = {choose(cs, board, replace(QUIET, blunder=1.0), rng).reason for _ in range(200)}
    assert reasons == {"softmax"}


def test_obvious_capture_and_mate_in_one():
    board = chess.Board("4k3/8/8/8/8/8/3q4/2B1K3 w - - 0 1")  # la dama negra se cuelga en d2
    capture = board.parse_san("Bxd2")
    others = [m for m in board.legal_moves if m != capture][:3]
    cs = [Candidate(capture, 800)] + [Candidate(m, -100 - i) for i, m in enumerate(others)]
    sees = replace(QUIET, temperature=1000, blunder=1.0, blunder_max_cp=2000, obvious=1.0)
    assert {choose(cs, board, sees, random.Random(i)).reason for i in range(50)} == {"obvia"}
    assert "obvia" not in {choose(cs, board, replace(sees, obvious=0.0), random.Random(i)).reason for i in range(50)}

    fools = chess.Board()
    for san in ("f3", "e5", "g4"):
        fools.push_san(san)
    mate = fools.parse_san("Qh4#")
    cs = [Candidate(mate, MATE_CP - 1), Candidate(fools.parse_san("Nc6"), MATE_CP - 3)]  # gana igual: no es "gratis"
    assert choose(cs, fools, replace(QUIET, obvious=1.0, temperature=10_000), random.Random(0)).move == mate


def test_candidates_skip_illegal_empty_and_repeated_pv():
    board = chess.Board()
    e4, d4 = chess.Move.from_uci("e2e4"), chess.Move.from_uci("d2d4")
    score = lambda cp: chess.engine.PovScore(chess.engine.Cp(cp), chess.WHITE)
    infos = [{"pv": [d4], "score": score(10)}, {"pv": [chess.Move.from_uci("e7e5")], "score": score(90)},
             {"pv": [], "score": score(50)}, {"pv": [e4]}, {"pv": [e4], "score": score(30)},
             {"pv": [e4], "score": score(-99)}]
    got = candidates(infos, board)
    assert [(c.move, c.cp) for c in got] == [(e4, 30), (d4, 10)]


def test_candidates_are_from_the_side_to_move():
    board = chess.Board()
    board.push_san("e4")  # juegan negras: un +200 de las blancas es -200 para ellas
    move = chess.Move.from_uci("e7e5")
    info = {"pv": [move], "score": chess.engine.PovScore(chess.engine.Cp(200), chess.WHITE)}
    assert candidates([info], board)[0].cp == -200
