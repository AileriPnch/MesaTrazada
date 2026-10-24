import time
from pathlib import Path

import chess
import pytest
from PyQt6.QtTest import QTest

from src.chess_game.difficulty import EngineLevel, Mode
from src.chess_game.engine_controller import EngineController
from tests.fakes import FakeEngine, factory_for, wait_until

LEVEL = EngineLevel(Mode.LIMITED, elo=1500, seconds=0.01)


@pytest.fixture
def make_controller(qapp):
    created = []

    def make(engine, min_reply=0.0):
        controller = EngineController(Path("fake"), factory_for(engine), min_reply=min_reply)
        moves, errors = [], []
        controller.move_ready.connect(moves.append)
        controller.failed.connect(errors.append)
        controller.start()
        assert wait_until(lambda: controller.is_ready)
        created.append(controller)
        return controller, moves, errors

    yield make
    for controller in created:
        controller.shutdown()


def test_move_is_delivered_and_level_configured(make_controller):
    engine = FakeEngine()
    controller, moves, _ = make_controller(engine)
    controller.request_move(chess.Board(), LEVEL)
    assert controller.is_thinking
    assert wait_until(lambda: moves)
    assert moves[0] in chess.Board().legal_moves
    assert engine.config["UCI_LimitStrength"] is True and engine.config["UCI_Elo"] == 1500
    assert not controller.is_thinking


def test_cancelled_search_is_discarded(make_controller):
    engine = FakeEngine(delay=0.3)
    controller, moves, _ = make_controller(engine)
    controller.request_move(chess.Board(), LEVEL)
    QTest.qWait(50)
    controller.cancel()
    assert not controller.is_thinking
    QTest.qWait(600)
    assert engine.searches == 1 and moves == []


def test_only_latest_request_is_delivered(make_controller):
    engine = FakeEngine(delay=0.2)
    controller, moves, _ = make_controller(engine)
    old = chess.Board()
    old.push_san("e4")  # posición vieja: el motor respondería con negras
    controller.request_move(old, LEVEL)
    QTest.qWait(30)
    controller.cancel()  # "Nueva partida" mientras piensa
    controller.request_move(chess.Board(), LEVEL)
    assert wait_until(lambda: engine.searches == 2 and not controller.is_thinking)
    QTest.qWait(50)
    assert len(moves) == 1
    assert moves[0] in chess.Board().legal_moves  # jugada de blancas, no la vieja de negras


def test_shutdown_during_search_is_fast_and_closes_engine(make_controller):
    engine = FakeEngine(delay=30)
    controller, moves, errors = make_controller(engine)
    controller.request_move(chess.Board(), LEVEL)
    QTest.qWait(50)
    controller.shutdown()
    assert engine.quit_called and engine.closed
    assert controller._thread.isFinished()
    QTest.qWait(50)
    assert moves == [] and errors == []  # el error esperable al cerrar no se reporta
    controller.shutdown()  # idempotente


def test_start_failure_is_reported(qapp):
    def broken(path):
        raise FileNotFoundError("no existe")

    controller = EngineController(Path("no-existe.exe"), broken)
    errors = []
    controller.failed.connect(errors.append)
    controller.start()
    assert wait_until(lambda: errors)
    assert "no existe" in errors[0] and not controller.is_ready
    controller.shutdown()


def test_fast_reply_is_held_until_min_reply(make_controller):
    engine = FakeEngine()
    controller, moves, _ = make_controller(engine, min_reply=0.4)
    asked = time.monotonic()
    arrived = []
    controller.move_ready.connect(lambda move: arrived.append(time.monotonic()))
    controller.request_move(chess.Board(), LEVEL)
    assert wait_until(lambda: engine.searches == 1)
    QTest.qWait(150)
    assert moves == [] and controller.is_thinking  # ya la calculó, pero la retiene
    assert wait_until(lambda: moves)
    assert arrived[0] - asked >= 0.4 and not controller.is_thinking


def test_slow_reply_is_not_delayed_further(make_controller):
    engine = FakeEngine(delay=0.3)
    controller, moves, _ = make_controller(engine, min_reply=0.1)
    asked = time.monotonic()
    controller.request_move(chess.Board(), LEVEL)
    assert wait_until(lambda: moves)
    assert time.monotonic() - asked < 0.6


@pytest.mark.parametrize("action", ["cancel", "new_request", "shutdown"])
def test_held_move_is_dropped(make_controller, action):
    engine = FakeEngine(script=["a2a3", "b1c3"])
    controller, moves, _ = make_controller(engine, min_reply=0.3)
    controller.request_move(chess.Board(), LEVEL)
    assert wait_until(lambda: engine.searches == 1)
    QTest.qWait(50)  # la jugada ya llegó y espera el tiempo mínimo
    if action == "cancel":
        controller.cancel()
        assert not controller.is_thinking
    elif action == "new_request":
        controller.request_move(chess.Board(), LEVEL)
    else:
        controller.shutdown()
    QTest.qWait(700)
    expected = [chess.Move.from_uci("b1c3")] if action == "new_request" else []
    assert moves == expected  # la retenida (a2a3) nunca se entrega
