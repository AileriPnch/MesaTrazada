"""Calibra los niveles de dificultad del ajedrez: partidas entre niveles y contra anclas, con la tabla final.

Escalera: cada nivel contra el de abajo (criterio: >= 70 % para el de arriba; Máximo-Avanzado no se juega:
el resultado es obvio). Anclas (sólo se informan): Principiante contra un jugador al azar y uno "glotón",
Novato y Aficionado contra Stockfish con UCI_Elo mínimo. Usa los parámetros del .env (o los que se pasen con
--set) y el mismo código que la app.

Procesos: los que entren dejando MIN_FREE_GB de memoria disponible, hasta MAX_WORKERS (en esta PC corren otras
cosas pesadas); si no entra ninguno, espera y vuelve a medir (MEMORY_TRIES veces) y si sigue sin
entrar, no juega. Cada Stockfish con Threads=1 y Hash=16 MB.

Uso:
  .venv\\Scripts\\python.exe scripts\\calibrar_dificultad.py [--games 40] [--pairs novato-principiante,...]
                                                          [--set PRINCIPIANTE_TEMP=200 ...]
"""
import argparse
import ctypes
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LADDER = [("novato", "principiante"), ("aficionado", "novato"), ("club", "aficionado"), ("avanzado", "club")]
ANCHORS = [("principiante", "azar"), ("principiante", "gloton"), ("novato", "sf1320"), ("aficionado", "sf1320")]
FEWER = {("club", "aficionado"): 0.5, ("avanzado", "club"): 0.5}  # lentos (tiempo por jugada): la mitad
THRESHOLD = 0.70
MIN_FREE_GB = 1.5
MEMORY_TRIES = 5  # sin memoria para un proceso: se vuelve a medir cada MEMORY_WAIT_S
MEMORY_WAIT_S = 60
MAX_WORKERS = 4
PYTHON_MB = 80  # un proceso de partida, sin los motores
STOCKFISH_MB = 250  # un Stockfish 19 (red NNUE embebida + Hash 16 MB), con margen
WITHOUT_ENGINE = {"azar", "gloton"}


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in ("total_phys", "avail_phys", "total_page", "avail_page",
                                                "total_virtual", "avail_virtual", "avail_extended")]


def available_gb() -> float:
    status = _MemoryStatus()
    status.dwLength = ctypes.sizeof(_MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.avail_phys / 2 ** 30


def workers_for(pairs: list[tuple[str, str]]) -> tuple[int, float, int]:
    """(procesos, GB disponibles, MB por proceso): los que entran dejando MIN_FREE_GB libres, hasta MAX_WORKERS."""
    engines = max(sum(name not in WITHOUT_ENGINE for name in pair) for pair in pairs)
    per_worker = PYTHON_MB + engines * STOCKFISH_MB
    free = available_gb()
    fits = int((free - MIN_FREE_GB) * 1024 // per_worker)
    return max(0, min(MAX_WORKERS, fits)), free, per_worker


def elo_diff(score: float) -> float:
    return -400 * math.log10(1 / score - 1)


def summarize(scores: list[float]) -> tuple[float, str]:
    n = len(scores)
    mean = sum(scores) / n
    se = math.sqrt(sum((s - mean) ** 2 for s in scores) / n / n)
    clamp = lambda s: min(max(s, 0.5 / n), 1 - 0.5 / n)  # noqa: E731 (0 % o 100 % no tienen Elo finito)
    low, high = clamp(mean - 1.96 * se), clamp(mean + 1.96 * se)
    return mean, f"{elo_diff(clamp(mean)):+5.0f} [{elo_diff(low):+5.0f}, {elo_diff(high):+5.0f}]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--games", type=int, default=40, help="partidas por emparejamiento (par)")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-minutes", type=float, default=8.0,
                        help="tope de la tanda: después no empieza partidas nuevas (las que juega, las termina)")
    parser.add_argument("--pairs", default="", help="sólo estos emparejamientos (ej.: novato-principiante)")
    parser.add_argument("--set", action="append", default=[], metavar="VAR=VALOR",
                        help="pisa una variable del .env (también en los procesos hijos)")
    args = parser.parse_args()
    for assignment in args.set:
        name, value = assignment.split("=", 1)
        os.environ[name] = value  # antes de importar config: load_dotenv no pisa variables ya definidas

    from scripts.calibracion_partidas import play_game

    wanted = {tuple(pair.split("-")) for pair in args.pairs.split(",") if pair}
    pairings = [(p, kind) for kind, group in (("escalera", LADDER), ("ancla", ANCHORS)) for p in group
                if not wanted or p in wanted]
    if wanted - {p for p, _ in pairings}:
        sys.exit(f"Emparejamientos desconocidos: {wanted - {p for p, _ in pairings}}")
    for attempt in range(1, MEMORY_TRIES + 1):
        workers, free, per_worker = workers_for([p for p, _ in pairings])
        print(f"Memoria disponible {free:.1f} GB; ~{per_worker} MB por proceso -> {workers} proceso(s)", flush=True)
        if workers:
            break
        if attempt < MEMORY_TRIES:
            print(f"Intento {attempt}/{MEMORY_TRIES}: se vuelve a medir en {MEMORY_WAIT_S} s", flush=True)
            time.sleep(MEMORY_WAIT_S)
    else:
        sys.exit(f"No hay memoria para jugar dejando {MIN_FREE_GB:g} GB libres ({MEMORY_TRIES} intentos): no se juega.")
    tasks = []
    for (upper, lower), _ in pairings:
        games = max(2, round(args.games * FEWER.get((upper, lower), 1)) // 2 * 2)
        tasks += [(upper, lower, i, args.seed) for i in range(games)]
    tasks.sort(key=lambda task: task[2])  # intercaladas: si se corta por tiempo, todos quedan con partidas

    started = time.monotonic()
    results: dict[tuple[str, str], list] = {p: [] for p, _ in pairings}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(play_game, task) for task in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            if future.cancelled():
                continue
            upper, lower, result = future.result()
            results[(upper, lower)].append(result)
            print(f"\r{done}/{len(tasks)} partidas ({time.monotonic() - started:.0f} s)", end="", flush=True)
            if time.monotonic() - started > args.max_minutes * 60 and not any(f.cancelled() for f in futures):
                cancelled = sum(f.cancel() for f in futures)  # las que ya empezaron no se cancelan
                print(f"\nTope de {args.max_minutes:g} min: {cancelled} partidas sin jugar", flush=True)
    print(f"\n\nParámetros: {' '.join(args.set) or '(los del .env)'}  ·  semilla {args.seed}\n")
    print(f"{'Emparejamiento':<26} {'Tipo':<9} {'G-E-P':>9} {'%':>6}  {'Dif. Elo [IC 95 %]':<24} "
          f"{'Jug.':>5} {'s/part.':>7}  Criterio")
    for (upper, lower), kind in pairings:
        games = results[(upper, lower)]
        if not games:
            print(f"{upper + ' vs ' + lower:<26} {kind:<9} (sin partidas)")
            continue
        scores = [g.score for g in games]
        wins, draws = scores.count(1.0), scores.count(0.5)
        mean, elo = summarize(scores)
        plies = sum(g.plies for g in games) / len(games) / 2
        seconds = sum(g.seconds for g in games) / len(games)
        verdict = ("OK" if mean >= THRESHOLD else "NO") if kind == "escalera" else "-"
        print(f"{upper + ' vs ' + lower:<26} {kind:<9} {f'{wins}-{draws}-{len(scores) - wins - draws}':>9} "
              f"{mean:6.1%}  {elo:<24} {plies:5.0f} {seconds:7.1f}  {verdict}")
    print(f"\nTotal: {time.monotonic() - started:.0f} s")


if __name__ == "__main__":
    main()
