"""Sonido: qué suena en cada jugada, volumen global que se guarda (sólo volumen y silencio), sin ráfagas del
mismo sonido y la app sigue muda si falta el audio."""
import logging

import chess
import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtTest import QTest

from src.chess_game.game_state import ChessGame
from src.chess_game.move_sound import end_sound, move_sound
from src.common import sound
from src.common.sound import MIN_GAP, Sound, SoundPlayer
from src.common.volume import Volume


class Recorder:
    def __init__(self):
        self.played: list[Sound] = []

    def play(self, item: Sound) -> None:
        self.played.append(item)


@pytest.fixture
def recorder():
    rec = Recorder()
    sound.install(player=rec)
    yield rec
    sound.install(player=None)


def _sound(fen: str, uci: str) -> Sound:
    return move_sound(chess.Board(fen), chess.Move.from_uci(uci))


def test_each_kind_of_move_has_its_sound():
    assert _sound(chess.STARTING_FEN, "e2e4") is Sound.MOVE
    assert _sound("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "e4d5") is Sound.CAPTURE
    assert _sound("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1") is Sound.CASTLE
    assert _sound("8/P7/8/8/8/8/8/k6K w - - 0 1", "a7a8q") is Sound.CHECK  # corona dando jaque: manda el jaque
    assert _sound("8/P7/8/8/8/8/8/1k5K w - - 0 1", "a7a8n") is Sound.PROMOTE
    assert _sound("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "a1a8") is Sound.CHECK


def test_end_sound_win_versus_loss_or_draw():
    win = ChessGame(chess.WHITE, "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    win.push(chess.Move.from_uci("a1a8"))
    assert end_sound(win.result(), chess.WHITE) is Sound.WIN
    assert end_sound(win.result(), chess.BLACK) is Sound.LOSE
    draw = ChessGame(chess.WHITE, "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")  # ahogado
    assert end_sound(draw.result(), chess.WHITE) is Sound.LOSE


def test_volume_persists_only_level_and_mute(tmp_path, qapp):
    store = QSettings(str(tmp_path / "audio.ini"), QSettings.Format.IniFormat)
    volume = Volume(store)
    assert (volume.level, volume.muted) == (70, False)
    volume.set_level(35)
    volume.set_muted(True)
    store.sync()
    again = Volume(QSettings(str(tmp_path / "audio.ini"), QSettings.Format.IniFormat))
    assert (again.level, again.muted) == (35, True)
    assert again.gain == 0.0
    assert set(store.allKeys()) == {"audio/volume", "audio/muted"}  # nada más se guarda


class FakeEffect:
    def __init__(self):
        self.plays = 0
        self.volume = None

    def play(self):
        self.plays += 1

    def setVolume(self, volume):  # noqa: N802 (API de QSoundEffect)
        self.volume = volume


def test_same_sound_is_not_repeated_in_a_burst(qapp, tmp_path):
    player = SoundPlayer(Volume(), directory=tmp_path)  # sin archivos: se le inyecta un efecto falso
    effect = FakeEffect()
    player._effects = {Sound.DRAW_CARD: effect}
    for _ in range(5):
        player.play(Sound.DRAW_CARD)
    assert effect.plays == 1
    QTest.qWait(round(MIN_GAP * 1000) + 30)
    player.play(Sound.DRAW_CARD)
    assert effect.plays == 2
    player.volume.set_muted(True)
    QTest.qWait(round(MIN_GAP * 1000) + 30)
    player.play(Sound.DRAW_CARD)
    assert effect.plays == 2  # en silencio no se reproduce nada


def test_missing_sound_files_leave_the_app_silent_and_logged(qapp, tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        player = SoundPlayer(Volume(), directory=tmp_path)
    player.play(Sound.MOVE)  # no explota
    assert not player.available
    assert any("Sin sonido" in r.getMessage() or "Falta el sonido" in r.getMessage() for r in caplog.records)


def test_every_sound_file_exists():
    for item in Sound:
        assert (sound.SOUND_DIR / f"{item.value}.wav").is_file(), item
