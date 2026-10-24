"""Prueba el .zip del build en una carpeta limpia, fuera del repo y sin el venv: descomprime en %TEMP%, corre
`MesaTrazada.exe --autoprueba` (inicio, cada nivel de ajedrez, solitario, sonido, cierre; ver
src/app/smoke_test.py) y mide el arranque (hasta que la ventana está visible) varias veces.

Uso: .\\.venv\\Scripts\\python.exe scripts\\probar_build.py dist\\MesaTrazada-<versión>-windows-x64.zip
Sólo cierra lo que lanza (por PID / su propia ventana).
"""
import ctypes
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from ctypes import wintypes
from pathlib import Path

logger = logging.getLogger("probar_build")
user32 = ctypes.windll.user32 if sys.platform == "win32" else None
WM_CLOSE = 0x0010
STARTUP_RUNS = 3


def clean_env() -> dict[str, str]:
    """Sin el venv ni Python en el PATH: el .exe tiene que traer todo."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("PYTHON", "VIRTUAL_ENV", "QT_"))}
    parts = [p for p in env.get("PATH", "").split(os.pathsep) if "python" not in p.lower() and ".venv" not in p.lower()]
    env["PATH"] = os.pathsep.join(parts)
    return env


def visible_window(pid: int) -> int | None:
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
            found.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)
    return found[0] if found else None


def measure_startup(exe: Path, env: dict[str, str]) -> float:
    """Segundos desde lanzar el .exe hasta su ventana visible; después la cierra (WM_CLOSE a SU ventana)."""
    start = time.perf_counter()
    process = subprocess.Popen([str(exe)], cwd=exe.parent, env=env)
    try:
        while (hwnd := visible_window(process.pid)) is None:
            if process.poll() is not None or time.perf_counter() - start > 60:
                raise RuntimeError("la ventana no apareció")
            time.sleep(0.01)
        elapsed = time.perf_counter() - start
        time.sleep(1.0)
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        process.wait(timeout=20)
        return elapsed
    finally:
        if process.poll() is None:
            process.kill()  # el que lanzamos nosotros, por su handle


def leftover_engines(folder: Path) -> list[int]:
    """Stockfish que hayan quedado vivos DE ESTA carpeta (sólo se miran, por ruta)."""
    query = ("Get-CimInstance Win32_Process -Filter \"Name='stockfish.exe'\" | "
             "ForEach-Object { \"$($_.ProcessId)|$($_.ExecutablePath)\" }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", query], capture_output=True, text=True).stdout
    root = str(folder.resolve()).lower()
    return [int(line.split("|")[0]) for line in out.splitlines() if "|" in line and line.split("|", 1)[1].lower().startswith(root)]


def test_zip(archive: Path) -> bool:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    folder = Path(tempfile.gettempdir()) / "mesatrazada_prueba_limpia"
    shutil.rmtree(folder, ignore_errors=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(folder)
    exe = next(folder.glob("*/*.exe"))
    env = clean_env()
    report = folder / "informe.json"
    times = [measure_startup(exe, env) for _ in range(STARTUP_RUNS)]  # la 1.ª: recién descomprimido
    start = time.perf_counter()
    code = subprocess.run([str(exe), "--autoprueba", str(report)], cwd=exe.parent, env=env, timeout=600).returncode
    elapsed = time.perf_counter() - start
    data = json.loads(report.read_text(encoding="utf-8")) if report.exists() else {"ok": False, "errors": ["sin informe"]}
    data["leftover_engines"] = leftover_engines(folder)
    data["startup_seconds"] = [round(t, 2) for t in times]
    data["smoke_seconds"] = round(elapsed, 1)
    data["exit_code"] = code
    data["folder_mb"] = round(sum(p.stat().st_size for p in exe.parent.rglob("*") if p.is_file()) / 2**20, 1)
    report.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = data["ok"] and code == 0 and not data["leftover_engines"]
    logger.info("Prueba en %s: %s. Arranque %s s. Informe: %s", folder, "OK" if ok else "FALLÓ", data["startup_seconds"], report)
    return ok


if __name__ == "__main__":
    sys.exit(0 if test_zip(Path(sys.argv[1])) else 1)
