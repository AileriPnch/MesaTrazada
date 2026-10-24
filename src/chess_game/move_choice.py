"""Elección "humana" entre las candidatas del motor (niveles por debajo del mínimo de UCI_Elo). Sin Qt.

Orden: (1) ve lo obvio (mate en 1 o captura gratis) con probabilidad `obvious`; (2) descuido con probabilidad
`blunder`: una candidata que pierde entre blunder_min_cp y blunder_max_cp, nunca una que deje mate en contra,
más probable cuanto menos pierde; si no hay ninguna en el rango, sigue al softmax; (3) softmax sobre la
pérdida respecto de la mejor: P ∝ exp(-pérdida / temperature).
"""
import math
import random
from dataclasses import dataclass

import chess
import chess.engine

from config import HumanLevel

MATE_CP = 10_000  # un mate vale esto (menos las jugadas que faltan)
LOSS_CAP = 1_000  # tope de la pérdida en el softmax: perder la dama o recibir mate pesan casi igual


@dataclass(frozen=True)
class Candidate:
    move: chess.Move
    cp: int  # evaluación desde el lado que mueve

    @property
    def mated(self) -> bool:
        return self.cp <= -MATE_CP // 2


@dataclass(frozen=True)
class Choice:
    move: chess.Move
    loss: int  # centipeones que pierde respecto de la mejor candidata
    reason: str  # única / obvia / descuido / softmax / mejor


def candidates(infos: list[dict], board: chess.Board) -> list[Candidate]:
    """Candidatas legales y sin repetir, de la mejor a la peor. Ignora PV vacíos o de otra posición."""
    found: dict[chess.Move, Candidate] = {}
    for info in infos:
        pv, score = info.get("pv"), info.get("score")
        if not pv or score is None or pv[0] not in board.legal_moves or pv[0] in found:
            continue
        found[pv[0]] = Candidate(pv[0], score.pov(board.turn).score(mate_score=MATE_CP))
    return sorted(found.values(), key=lambda c: -c.cp)


def softmax_weights(losses: list[int], temperature: float) -> list[float]:
    if temperature <= 0:
        return [1.0 if loss == min(losses) else 0.0 for loss in losses]
    return [math.exp(-min(loss, LOSS_CAP) / temperature) for loss in losses]


def is_obvious(cands: list[Candidate], board: chess.Board, gap_cp: int) -> bool:
    """La mejor da mate en 1, o es una captura que le saca al menos gap_cp a la segunda."""
    best = cands[0].move
    board = board.copy(stack=False)
    capture = board.is_capture(best)
    board.push(best)
    if board.is_checkmate():
        return True
    return capture and (len(cands) == 1 or cands[0].cp - cands[1].cp >= gap_cp)


def choose(cands: list[Candidate], board: chess.Board, params: HumanLevel, rng: random.Random) -> Choice:
    best = cands[0]
    losses = [best.cp - c.cp for c in cands]
    if is_obvious(cands, board, params.obvious_cp) and rng.random() < params.obvious:
        return Choice(best.move, 0, "obvia")
    if rng.random() < params.blunder:
        pool = [(c, loss) for c, loss in zip(cands, losses)
                if params.blunder_min_cp <= loss <= params.blunder_max_cp and not c.mated]
        if pool:  # perder menos es más probable: peso inverso a la pérdida
            c, loss = rng.choices(pool, weights=[1 / max(loss, 1) for _, loss in pool])[0]
            return Choice(c.move, loss, "descuido")
    index = rng.choices(range(len(cands)), weights=softmax_weights(losses, params.temperature))[0]
    return Choice(cands[index].move, losses[index], "softmax")
