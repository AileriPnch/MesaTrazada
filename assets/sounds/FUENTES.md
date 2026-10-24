# Origen de cada sonido

Todos salen de packs de [Kenney](https://kenney.nl) con licencia **CC0 1.0** (dominio público; ver
`LICENCIA.txt`). `scripts/preparar_sonidos.py` los recorta, mezcla las capas, suaviza los naipes (paso bajo
a 8 kHz), aplica fundidos y normaliza el volumen. WAV mono, 16 bits, 44,1 kHz.

| Archivo | Cuándo suena | Original(es) | Pack |
|---|---|---|---|
| `ajedrez_mover.wav` | jugada común | `impactWood_light_002` | Impact Sounds |
| `ajedrez_capturar.wav` | captura | `impactWood_medium_002` + `impactWood_light_004` (35 ms después, -7 dB) | Impact Sounds |
| `ajedrez_enroque.wav` | enroque | `impactWood_light_001` + `impactWood_light_003` (120 ms después: rey y torre) | Impact Sounds |
| `ajedrez_jaque.wav` | jaque (manda sobre los demás) | `impactWood_light_002` + `impactBell_heavy_004` (-8 dB) | Impact Sounds |
| `ajedrez_coronar.wav` | coronación | `impactWood_light_002` + `jingles_PIZZI16` (-3 dB) | Impact Sounds, Music Jingles |
| `ganar.wav` | ganar al ajedrez y completar el solitario | `jingles_PIZZI10` (sube) | Music Jingles |
| `perder_o_tablas.wav` | perder o tablas | `jingles_PIZZI11` (baja) | Music Jingles |
| `solitario_robar.wav` | robar del mazo | `card-slide-1` | Casino Audio |
| `solitario_apoyar.wav` | apoyar una carta en una columna | `card-place-1` | Casino Audio |
| `solitario_voltear.wav` | se da vuelta una carta tapada | `card-slide-2` | Casino Audio |
| `solitario_fundacion.wav` | subir a la fundación | `card-place-3` + `chip-lay-3` (-9 dB) | Casino Audio |
| `solitario_reciclar.wav` | reciclar el mazo | `card-fan-1` | Casino Audio |
| `solitario_repartir.wav` | repartir partida nueva | `card-shuffle` (primeros 1,1 s) | Casino Audio |

Descargas: [Casino Audio](https://kenney.nl/assets/casino-audio),
[Impact Sounds](https://kenney.nl/assets/impact-sounds), [Music Jingles](https://kenney.nl/assets/music-jingles).
