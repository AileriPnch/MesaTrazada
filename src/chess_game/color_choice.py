"""Color con el que juega la persona: blancas, negras o al azar (se resuelve al empezar cada partida)."""
import random
from enum import Enum

import chess


class ColorChoice(Enum):
    WHITE = "Blancas"
    BLACK = "Negras"
    RANDOM = "Al azar"

    def resolve(self) -> chess.Color:
        if self is ColorChoice.RANDOM:
            return random.choice([chess.WHITE, chess.BLACK])
        return chess.WHITE if self is ColorChoice.WHITE else chess.BLACK
