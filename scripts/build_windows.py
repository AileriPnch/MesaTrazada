"""Build de Windows reproducible: PyInstaller en modo carpeta + licencias + .zip versionado en dist/.

Uso (desde la raíz, con el venv del proyecto):
    .\\.venv\\Scripts\\python.exe scripts\\build_windows.py            # build + .zip + prueba en carpeta limpia
    .\\.venv\\Scripts\\python.exe scripts\\build_windows.py --sin-prueba

Modo carpeta (no un solo .exe): arranca sin descomprimir ~250 MB a %TEMP% en cada apertura y da menos falsos
positivos de antivirus (los .exe que se autoextraen son un patrón típico de malware). La versión sale de
src/common/app_info.py. Requiere engine/stockfish.exe y engine/Copying.txt (no se versionan).
"""
import hashlib
import logging
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.common import app_info  # noqa: E402

NAME = app_info.APP_ID  # MesaTrazada.exe, MesaTrazada-<versión>-windows-x64.zip
WORK = ROOT / "build" / "pyinstaller"
APP_DIR = ROOT / "build" / "app" / NAME
DIST = ROOT / "dist"
ICON = ROOT / "assets" / "app_icon_blender.ico"
ENGINE = ROOT / "engine"
SITE = Path(sys.prefix) / "Lib" / "site-packages"
# Lo que PyInstaller arrastra y la app no usa: PDF, TLS/OpenSSL de Qt (sin red), información de red y FFmpeg (los WAV
# suenan con el backend de Windows Media; la prueba de humo verifica que suenen). Verificado con probar_build.py.
QT = "_internal/PyQt6/Qt6"
PRUNE = (f"{QT}/bin/opengl32sw.dll", f"{QT}/translations", f"{QT}/bin/Qt6Pdf.dll", f"{QT}/plugins/imageformats/qpdf.dll",
         f"{QT}/plugins/tls", "_internal/libcrypto-3-x64.dll", "_internal/libssl-3-x64.dll",
         f"{QT}/plugins/networkinformation", f"{QT}/plugins/multimedia/ffmpegmediaplugin.dll",
         *(f"{QT}/bin/{dll}" for dll in ("avcodec-61.dll", "avformat-61.dll", "avutil-59.dll", "swresample-5.dll",
                                         "swscale-8.dll")))
EXCLUDES = ("tkinter", "pytest", "_pytest", "PyInstaller", "unittest", "pydoc", "pdb", "doctest")

logger = logging.getLogger("build_windows")


def zip_name() -> str:
    return f"{NAME}-{app_info.VERSION}-windows-x64.zip"


def version_file() -> Path:
    """Recurso VERSIONINFO del .exe (Propiedades > Detalles): nombre, versión, autor, licencia."""
    nums = tuple(int(n) for n in app_info.VERSION.split(".")) + (0,)
    fields = {"CompanyName": app_info.AUTHOR, "FileDescription": app_info.APP_NAME, "FileVersion": app_info.VERSION,
              "InternalName": NAME, "LegalCopyright": f"© 2026 {app_info.AUTHOR} · {app_info.LICENSE_NAME}",
              "OriginalFilename": f"{NAME}.exe", "ProductName": app_info.APP_NAME, "ProductVersion": app_info.VERSION}
    strings = ",\n".join(f"        StringStruct({k!r}, {v!r})" for k, v in fields.items())
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1,
                    subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040a04b0', [
{strings}])]),
        VarFileInfo([VarStruct('Translation', [0x040a, 1200])])])
"""
    path = WORK / "version_info.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run_pyinstaller() -> None:
    import PyInstaller.__main__

    sep = ";"
    args = [str(ROOT / "main.py"), "--name", NAME, "--onedir", "--windowed", "--noconfirm", "--clean",
            "--icon", str(ICON), "--version-file", str(version_file()),
            "--distpath", str(APP_DIR.parent), "--workpath", str(WORK), "--specpath", str(WORK),
            "--add-data", f"{ROOT / 'assets'}{sep}assets",
            "--add-data", f"{ENGINE / 'stockfish.exe'}{sep}engine",
            "--add-data", f"{ENGINE / 'Copying.txt'}{sep}engine"]
    for module in EXCLUDES:
        args += ["--exclude-module", module]
    PyInstaller.__main__.run(args)


def prune() -> None:
    for rel in PRUNE:
        target = APP_DIR / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def copy_licenses() -> None:
    """Junto al .exe: LICENSE, CREDITS.md, un LEEME y la licencia de cada componente en licencias/."""
    out = APP_DIR / "licencias"
    out.mkdir(exist_ok=True)
    files = {
        "LICENSE.txt": ROOT / "LICENSE", "CREDITS.md": ROOT / "CREDITS.md",
        "Stockfish-Copying.txt": ENGINE / "Copying.txt",
        "PyQt6-LICENSE.txt": next(SITE.glob("PyQt6-*.dist-info")) / "licenses" / "LICENSE",
        "Qt6-LGPLv3.txt": next(SITE.glob("pyqt6_qt6-*.dist-info")) / "LICENSE",
        "python-chess-LICENSE.txt": next(SITE.glob("chess-*.dist-info")) / "licenses" / "LICENSE.txt",
        "python-dotenv-LICENSE.txt": next(SITE.glob("python_dotenv-*.dist-info")) / "licenses" / "LICENSE",
        "PyQt6-sip-LICENSE.txt": next(SITE.glob("pyqt6_sip-*.dist-info")).joinpath("licenses", "LICENSE"),
        "Python-LICENSE.txt": Path(sys.base_prefix) / "LICENSE.txt",
        "Kenney-sonidos-CC0.txt": ROOT / "assets" / "sounds" / "LICENCIA.txt",
    }
    for family in (ROOT / "assets" / "fonts").iterdir():
        files[f"{family.name}-OFL.txt"] = family / "OFL.txt"
    missing = [name for name, src in files.items() if not src.is_file()]
    if missing:
        raise SystemExit(f"Faltan licencias: {missing}")
    for name, src in files.items():
        shutil.copyfile(src, out / name)
    shutil.copyfile(ROOT / "LICENSE", APP_DIR / "LICENSE.txt")
    shutil.copyfile(ROOT / ".env.example", APP_DIR / "config.env.ejemplo")
    shutil.copyfile(ROOT / "docs" / "lanzamiento" / "LEEME.txt", APP_DIR / "LEEME.txt")


def make_zip() -> Path:
    DIST.mkdir(exist_ok=True)
    target = DIST / zip_name()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(APP_DIR.rglob("*")):
            if path.is_file():
                z.write(path, Path(NAME) / path.relative_to(APP_DIR))
    return target


def folder_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for required in (ENGINE / "stockfish.exe", ENGINE / "Copying.txt", ICON):
        if not required.is_file():
            raise SystemExit(f"Falta {required}")
    from scripts.limpiar_metadatos_png import clean_folder

    clean_folder(ROOT / "assets")  # nada personal en los PNG que se empaquetan
    shutil.rmtree(APP_DIR, ignore_errors=True)
    run_pyinstaller()
    prune()
    copy_licenses()
    archive = make_zip()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    logger.info("Carpeta: %s (%.1f MB)", APP_DIR, folder_size(APP_DIR) / 2**20)
    logger.info("Zip: %s (%.1f MB) sha256 %s", archive, archive.stat().st_size / 2**20, digest)
    if "--sin-prueba" not in argv:
        from scripts.probar_build import test_zip

        return 0 if test_zip(archive) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
