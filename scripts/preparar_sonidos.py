"""Genera assets/sounds/*.wav a partir de tres packs CC0 de Kenney (https://kenney.nl):
Casino Audio (naipes), Impact Sounds (madera, campana) y Music Jingles (pizzicato).

Uso:  .venv\\Scripts\\python.exe -I scripts\\preparar_sonidos.py <carpeta>
<carpeta> tiene las subcarpetas casino/, impact/ y jingles/ con el contenido de cada zip descomprimido
(kenney.nl/assets/casino-audio, /impact-sounds, /music-jingles).

Cada sonido: se decodifica (QAudioDecoder), se recorta el silencio, se suaviza (paso bajo en los naipes),
se mezclan sus capas, se corta a una duración máxima con fundido y se normaliza el volumen para que todos
suenen parejo. Salida: WAV mono 16 bits 44,1 kHz (lo que QSoundEffect reproduce con baja latencia).
"""
import math
import sys
import wave
from array import array
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QEventLoop, QUrl
from PyQt6.QtMultimedia import QAudioDecoder, QAudioFormat

RATE = 44100
OUT = Path(__file__).resolve().parents[1] / "assets" / "sounds"

# nombre: (capas [(archivo, desfase ms, ganancia dB)], duración máx ms, paso bajo Hz o 0, RMS objetivo dBFS)
RECIPES = {
    "ajedrez_mover": ([("impact/Audio/impactWood_light_002.ogg", 0, 0)], 220, 0, -21),
    "ajedrez_capturar": ([("impact/Audio/impactWood_medium_002.ogg", 0, 0),
                          ("impact/Audio/impactWood_light_004.ogg", 35, -7)], 300, 0, -20),
    "ajedrez_enroque": ([("impact/Audio/impactWood_light_001.ogg", 0, 0),
                         ("impact/Audio/impactWood_light_003.ogg", 120, -1)], 360, 0, -21),
    "ajedrez_jaque": ([("impact/Audio/impactWood_light_002.ogg", 0, 0),
                       ("impact/Audio/impactBell_heavy_004.ogg", 25, -8)], 420, 0, -21),
    "ajedrez_coronar": ([("impact/Audio/impactWood_light_002.ogg", 0, 0),
                         ("jingles/Audio/Pizzicato jingles/jingles_PIZZI16.ogg", 70, -3)], 700, 0, -23),
    "ganar": ([("jingles/Audio/Pizzicato jingles/jingles_PIZZI10.ogg", 0, 0)], 1100, 0, -24),
    "perder_o_tablas": ([("jingles/Audio/Pizzicato jingles/jingles_PIZZI11.ogg", 0, 0)], 1100, 0, -25),
    "solitario_robar": ([("casino/Audio/card-slide-1.ogg", 0, 0)], 260, 8000, -25),
    "solitario_apoyar": ([("casino/Audio/card-place-1.ogg", 0, 0)], 300, 8000, -24),
    "solitario_voltear": ([("casino/Audio/card-slide-2.ogg", 0, 0)], 340, 8000, -26),
    "solitario_fundacion": ([("casino/Audio/card-place-3.ogg", 0, 0),
                             ("casino/Audio/chip-lay-3.ogg", 40, -9)], 420, 8000, -24),
    "solitario_reciclar": ([("casino/Audio/card-fan-1.ogg", 0, 0)], 760, 8000, -26),
    "solitario_repartir": ([("casino/Audio/card-shuffle.ogg", 0, 0)], 1100, 8000, -27),
}


def decode(path: Path) -> list[float]:
    fmt = QAudioFormat()
    fmt.setSampleRate(RATE)
    fmt.setChannelCount(1)
    fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    decoder = QAudioDecoder()
    decoder.setAudioFormat(fmt)
    decoder.setSource(QUrl.fromLocalFile(str(path)))
    data, loop, errors = array("h"), QEventLoop(), []

    def ready() -> None:
        while decoder.bufferAvailable():
            buffer = decoder.read()
            data.frombytes(bytes(buffer.constData().asstring(buffer.byteCount())))

    def failed(_error) -> None:
        errors.append(decoder.errorString())
        loop.quit()

    decoder.bufferReady.connect(ready)
    decoder.finished.connect(loop.quit)
    decoder.error.connect(failed)
    decoder.start()
    loop.exec()
    if errors or not data:
        raise RuntimeError(f"No se pudo decodificar {path}: {errors}")
    return [v / 32768 for v in data]


def trim(x: list[float]) -> list[float]:
    """Desde 2 ms antes del primer sonido hasta el último por encima de -50 dB del pico."""
    peak = max(abs(v) for v in x)
    loud = [i for i, v in enumerate(x) if abs(v) > peak * 10 ** (-50 / 20)]
    return x[max(0, loud[0] - RATE // 500): loud[-1] + 1]


def lowpass(x: list[float], cutoff: float) -> list[float]:
    """Paso bajo de 2 polos (dos de 1 polo en cascada): suaviza el roce de los naipes, no lo apaga."""
    alpha = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    for _ in range(2):
        y, out = 0.0, []
        for v in x:
            y += alpha * (v - y)
            out.append(y)
        x = out
    return x


def rms(x: list[float]) -> float:
    return math.sqrt(sum(v * v for v in x) / max(1, len(x)))


def build(base: Path, layers, max_ms: int, cutoff: int, target_db: float) -> list[float]:
    mix: list[float] = []
    for name, offset_ms, gain_db in layers:
        x = trim(decode(base / name))
        scale = 10 ** (gain_db / 20) / max(rms(x), 1e-9)  # capas a igual volumen + su ganancia
        x = [v * scale for v in x]
        start = round(offset_ms * RATE / 1000)
        mix.extend([0.0] * max(0, start + len(x) - len(mix)))
        for i, v in enumerate(x):
            mix[start + i] += v
    if cutoff:
        mix = lowpass(mix, cutoff)
    mix = mix[: round(max_ms * RATE / 1000)]
    fade_in, fade_out = round(0.003 * RATE), min(len(mix) // 3, round(0.06 * RATE))
    for i in range(fade_in):
        mix[i] *= i / fade_in
    for i in range(fade_out):
        mix[-1 - i] *= i / fade_out
    gain = 10 ** (target_db / 20) / max(rms(mix), 1e-9)
    gain = min(gain, 10 ** (-3 / 20) / max(abs(v) for v in mix))  # pico a -3 dBFS como máximo
    return [v * gain for v in mix]


def write_wav(path: Path, x: list[float]) -> None:
    samples = array("h", (max(-32767, min(32767, round(v * 32767))) for v in x))
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(samples.tobytes())


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    app = QCoreApplication([])  # noqa: F841 (tiene que vivir mientras se decodifica)
    base = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (layers, max_ms, cutoff, target) in RECIPES.items():
        x = build(base, layers, max_ms, cutoff, target)
        write_wav(OUT / f"{name}.wav", x)
        peak = 20 * math.log10(max(abs(v) for v in x))
        print(f"{name:22s} {len(x) / RATE * 1000:5.0f} ms  pico {peak:5.1f} dB  rms {20 * math.log10(rms(x)):5.1f} dB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
