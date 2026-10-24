"""Lanzamiento: nada personal en lo versionado (rutas de la PC, metadatos de los PNG), .env fuera del repo y
.env.example con sólo variables que existen, y el build lee la versión de app_info."""
import re
import subprocess
from pathlib import Path

import pytest

from scripts.limpiar_metadatos_png import strip, text_chunks

ROOT = Path(__file__).resolve().parents[1]
USER_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!<|%|\.\.\.)\w", re.IGNORECASE)  # C:\Users\<alguien>


def tracked() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("sin git")
    return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]


def test_no_personal_paths_in_tracked_text():
    found = []
    for path in tracked():
        if path.suffix.lower() in (".py", ".md", ".txt", ".json", ".ps1", ".example", ".gitignore", ".toml", ".spec"):
            found += [f"{path.name}: {m.group(0)}" for m in USER_PATH.finditer(path.read_text(encoding="utf-8-sig"))]
    assert not found


def test_pngs_have_no_text_metadata():
    """Blender graba la ruta del .blend (con el usuario de la PC) en cada PNG: scripts/limpiar_metadatos_png.py."""
    dirty = [p.relative_to(ROOT).as_posix() for p in (ROOT / "assets").rglob("*.png") if text_chunks(p.read_bytes())]
    assert not dirty


def test_strip_keeps_the_image(tmp_path):
    from PyQt6.QtGui import QImage

    original = ROOT / "assets" / "app_icon_256.png"
    data = original.read_bytes()
    marked = data[:33] + b"\x00\x00\x00\x08tEXtFile\x00abc" + b"\x00\x00\x00\x00" + data[33:]  # bloque de texto falso
    cleaned = tmp_path / "x.png"
    cleaned.write_bytes(strip(marked))
    assert not text_chunks(cleaned.read_bytes())
    assert QImage(str(cleaned)) == QImage(str(original))


def test_env_is_never_tracked_and_example_only_has_known_variables():
    files = {p.relative_to(ROOT).as_posix() for p in tracked()}
    assert ".env" not in files and ".env.example" in files
    known = set(re.findall(r'"([A-Z_]+)"', (ROOT / "config.py").read_text(encoding="utf-8")))
    known |= {f"{prefix}_{suffix}" for prefix in ("PRINCIPIANTE", "NOVATO", "AFICIONADO")
              for suffix in ("ELO", "DEPTH", "MULTIPV", "TEMP", "BLUNDER", "BLUNDER_MIN_CP", "BLUNDER_MAX_CP", "OBVIOUS")}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, value = line.split("=", 1)
            assert name in known, name
            assert not re.search(r"(?i)key|token|secret|password", name) and "Users" not in value


def test_build_script_takes_the_version_from_app_info():
    from scripts import build_windows
    from src.common import app_info

    assert build_windows.zip_name() == f"MesaTrazada-{app_info.VERSION}-windows-x64.zip"


def test_legacy_data_folder_is_migrated_once_without_overwriting(tmp_path, monkeypatch):
    from src.common import paths

    old = tmp_path / "AjedrezSolitario" / "logs"
    old.mkdir(parents=True)
    (old / "app.log").write_text("viejo", encoding="utf-8")
    assert paths.migrate_legacy_data(tmp_path) == "movida"
    assert (tmp_path / "MesaTrazada" / "logs" / "app.log").read_text(encoding="utf-8") == "viejo"
    assert paths.migrate_legacy_data(tmp_path) == "nada"  # una sola vez
    old.mkdir(parents=True)  # reaparece la vieja: la nueva no se pisa
    (old / "app.log").write_text("otro", encoding="utf-8")
    assert paths.migrate_legacy_data(tmp_path) == "nada"
    assert (tmp_path / "MesaTrazada" / "logs" / "app.log").read_text(encoding="utf-8") == "viejo"


def test_legacy_folder_in_use_is_copied_and_kept(tmp_path, monkeypatch):
    from src.common import paths

    (tmp_path / "AjedrezSolitario").mkdir()
    (tmp_path / "AjedrezSolitario" / "app.log").write_text("x", encoding="utf-8")

    def busy(self, target):
        raise PermissionError("en uso")

    monkeypatch.setattr(Path, "rename", busy)
    assert paths.migrate_legacy_data(tmp_path) == "copiada"
    assert (tmp_path / "MesaTrazada" / "app.log").exists() and (tmp_path / "AjedrezSolitario" / "app.log").exists()


def test_saved_volume_is_migrated_from_the_old_name_once(qapp, tmp_path):
    from PyQt6.QtCore import QSettings

    from src.common.volume import migrate_settings

    old = QSettings(str(tmp_path / "viejo.ini"), QSettings.Format.IniFormat)
    new = QSettings(str(tmp_path / "nuevo.ini"), QSettings.Format.IniFormat)
    old.setValue("audio/volume", 35)
    old.setValue("audio/muted", True)
    assert migrate_settings(old, new)
    assert new.value("audio/volume", type=int) == 35 and new.value("audio/muted", type=bool)
    old.setValue("audio/volume", 90)
    assert not migrate_settings(old, new) and new.value("audio/volume", type=int) == 35  # no pisa lo nuevo
    assert old.value("audio/volume", type=int) == 90  # la vieja queda


def test_new_name_everywhere():
    from src.app.windows_integration import APP_USER_MODEL_ID
    from src.common import app_info, paths

    assert app_info.APP_NAME == "Mesa Trazada" and APP_USER_MODEL_ID.endswith(app_info.APP_ID)
    assert paths.DATA_DIR_NAME == "MesaTrazada"
    for doc in ("README.md", "LICENSE", "CREDITS.md", "docs/lanzamiento/LEEME.txt", "docs/lanzamiento/itchio.md"):
        assert "Mesa Trazada" in (ROOT / doc).read_text(encoding="utf-8").replace("MESA TRAZADA", "Mesa Trazada"), doc
    script = (ROOT / "scripts" / "crear_acceso_directo.ps1").read_text(encoding="utf-8-sig")
    assert "'Mesa Trazada.lnk'" in script
