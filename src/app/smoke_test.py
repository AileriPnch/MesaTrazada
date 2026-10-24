"""Prueba de humo del build: `MesaTrazada.exe --autoprueba <informe.json>`.

Recorre la app de verdad (la misma ventana, Stockfish y sonidos empaquetados): inicio, "Acerca de", una partida corta
contra CADA nivel (3 jugadas tuyas y sus respuestas), vuelta al menú (el proceso del motor tiene que morir),
solitario (repartir, robar, subir a la fundación), sonido y cierre. Escribe el informe y capturas de cada pantalla
junto al JSON y cierra la ventana. La usa `scripts/build_windows.py` sobre una copia limpia del build.
"""
import ctypes
import json
import logging
import random
import sys
from pathlib import Path
from time import monotonic, perf_counter

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtGui import QFontDatabase

from src.chess_game.color_choice import ColorChoice
from src.chess_game.difficulty import Difficulty
from src.common import app_info, paths, sound
from src.common.sound import Sound
from src.solitaire.klondike import PileKind, PileRef, TABLEAU_COLUMNS

logger = logging.getLogger(__name__)

PLAYER_MOVES = 3
POLL_MS = 50


def process_exited(pid: int, timeout_ms: int) -> bool:
    if sys.platform != "win32":
        return True
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if not handle:
        return True
    try:
        return kernel32.WaitForSingleObject(ctypes.c_void_p(handle), timeout_ms) == 0
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


class SmokeTest(QObject):
    """Un guion (generador) que cede esperas: ms fijos o (condición, tope en ms)."""

    def __init__(self, window, out: Path, started: float):
        super().__init__(window)
        self.window, self.out, self.started = window, out, started
        self.report = {"version": app_info.VERSION, "frozen": paths.frozen(), "errors": []}
        self._script = self._run()
        self._waiting = None
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._poll)

    def start(self) -> None:
        self._resume(None)

    def _resume(self, value) -> None:
        try:
            step = self._script.send(value)
        except StopIteration:
            return
        except Exception as exc:  # el informe tiene que salir igual
            logger.exception("Falló la prueba de humo")
            self.report["errors"].append(f"{type(exc).__name__}: {exc}")
            self._finish()
            return
        if isinstance(step, int):
            QTimer.singleShot(step, lambda: self._resume(None))
        else:
            condition, timeout_ms = step
            self._waiting = (condition, monotonic() + timeout_ms / 1000)
            self._timer.start()

    def _poll(self) -> None:
        condition, deadline = self._waiting
        done = condition()
        if done or monotonic() > deadline:
            self._timer.stop()
            self._resume(bool(done))

    def _grab(self, name: str) -> None:
        self.window.grab().save(str(self.out.with_name(f"{self.out.stem}_{name}.png")))

    def _run(self):
        w, r = self.window, self.report
        r["ms_to_home"] = round((perf_counter() - self.started) * 1000)
        yield 400
        r["fonts"] = {f: f in QFontDatabase.families() for f in ("Playfair Display", "Inter", "Caveat")}
        self._grab("inicio")
        about = w.show_about()
        yield 250
        self._grab("acerca_de")
        about.accept()
        r["chess"] = []
        for level in Difficulty:
            r["chess"].append((yield from self._play(level)))
        r["solitaire"] = yield from self._solitaire()
        player = sound._player
        r["sound"] = {"available": bool(player and player.available),
                      "ready": sorted(i.value for i, e in (player._effects.items() if player else [])
                                      if e.status() == e.Status.Ready)}
        effect = player._effects.get(Sound.WIN) if player else None
        if effect is not None:
            effect.play()  # directo: aunque el volumen guardado esté en silencio, tiene que llegar a sonar
            r["sound"]["played"] = yield (effect.isPlaying, 3000)
        yield 900
        self._finish()

    def _play(self, level: Difficulty):
        w = self.window
        w.open_chess(ColorChoice.WHITE, level)
        screen = w.game
        ready = yield (lambda: screen.engine is not None and screen.engine.is_ready, 30000)
        entry = {"level": level.name, "engine_ready": ready, "replies": []}
        if not ready:
            return entry
        pid = screen.engine._worker.engine.transport.get_pid()
        rng = random.Random(level.value)
        for _ in range(PLAYER_MOVES):
            board = screen.game.board
            if screen.game.result() is not None:
                break
            move = rng.choice([m for m in board.legal_moves if m.promotion is None])
            plies, start = len(board.move_stack), monotonic()
            screen._on_player_move(move.from_square, move.to_square)
            replied = yield (lambda: len(screen.game.board.move_stack) >= plies + 2 or screen.game.result() is not None,
                             20000)
            reply = screen.game.board.peek() if replied and len(screen.game.board.move_stack) >= plies + 2 else None
            entry["replies"].append({"you": move.uci(), "engine": reply.uci() if reply else None,
                                     "seconds": round(monotonic() - start, 2)})
        entry["legal"] = screen.game.board.is_valid()
        if level in (Difficulty.BEGINNER, Difficulty.MAXIMUM):
            self._grab(f"ajedrez_{level.name.lower()}")
        w.show_menu()
        entry["engine_closed"] = process_exited(pid, 5000)
        yield 100
        return entry

    def _solitaire(self):
        w = self.window
        w.open_solitaire(1)
        screen = w.game
        yield 1200  # reparto animado
        draws = 0
        for _ in range(8):
            screen.view._draw()
            draws += 1
            yield 120
        moved = 0
        sources = [PileRef(PileKind.WASTE)] + [PileRef(PileKind.TABLEAU, i) for i in range(TABLEAU_COLUMNS)]
        for src in sources:
            pile = screen.game.pile(src)
            if pile and (dst := screen.game.foundation_target(src, len(pile) - 1)) is not None:
                moved += screen.view._move(src, len(pile) - 1, dst)
                yield 300
        self._grab("solitario")
        result = {"draws": draws, "to_foundation": moved, "actions": screen.game.actions}
        w.show_menu()
        return result

    def _finish(self) -> None:
        r = self.report
        chess_ok = len(r.get("chess", [])) == len(Difficulty) and all(
            e["engine_ready"] and e["replies"] and all(x["engine"] for x in e["replies"]) and e["engine_closed"]
            for e in r["chess"])
        r["ok"] = (not r["errors"] and chess_ok and all(r.get("fonts", {}).values())
                   and r.get("solitaire", {}).get("draws", 0) > 0 and r.get("sound", {}).get("played", False))
        self.out.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Prueba de humo: %s", "OK" if r["ok"] else "FALLÓ")
        self.window.close()


def run_smoke_test(window, out: Path, started: float) -> SmokeTest:
    test = SmokeTest(window, out, started)
    QTimer.singleShot(0, test.start)
    return test


def smoke_output(argv: list[str]) -> Path | None:
    """La ruta del informe si se pidió `--autoprueba <ruta>`."""
    if "--autoprueba" in argv:
        i = argv.index("--autoprueba")
        if i + 1 < len(argv):
            return Path(argv[i + 1]).resolve()
    return None

