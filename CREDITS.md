# Créditos y componentes de terceros

**Mesa Trazada** © 2026 Juan Scandizzo. Se distribuye bajo la **GNU GPL v3** (ver `LICENSE`), la misma
licencia de Stockfish, python-chess y PyQt6. Cada componente de terceros conserva su licencia; en el build de
Windows los textos completos están en la carpeta `licencias/`.

| Componente | Versión | Autor | Licencia | Enlace |
|---|---|---|---|---|
| Stockfish (motor de ajedrez) | 19 | The Stockfish developers (ver su archivo AUTHORS) | GPLv3 | https://github.com/official-stockfish/Stockfish/tree/sf_19 |
| python-chess (`chess`) | 1.11.2 | Niklas Fiekas | GPLv3 o posterior | https://github.com/niklasf/python-chess |
| PyQt6 | 6.11.0 | Riverbank Computing | GPLv3 | https://www.riverbankcomputing.com/software/pyqt/ |
| Qt 6 (bibliotecas, vía PyQt6-Qt6) | 6.11.2 | The Qt Company | LGPLv3 | https://www.qt.io/ — código: https://download.qt.io/official_releases/qt/6.11/ |
| PyQt6-sip | 13.13.0 | Riverbank Computing | BSD-2-Clause | https://pypi.org/project/PyQt6-sip/ |
| python-dotenv | 1.2.4 | Saurabh Kumar | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| Playfair Display (fuente) | variable | The Playfair Display Project Authors | SIL OFL 1.1 | https://github.com/clauseggers/Playfair-Display |
| Inter (fuente) | variable | The Inter Project Authors | SIL OFL 1.1 | https://github.com/rsms/inter |
| Caveat (fuente) | variable | The Caveat Project Authors | SIL OFL 1.1 | https://github.com/googlefonts/caveat |
| Casino Audio, Impact Sounds, Music Jingles (sonidos) | 1.1 / 1.0 / — | Kenney (Kenney Vleugels) | CC0 1.0 | https://kenney.nl |
| Python (intérprete incluido en el build) | 3.12 | Python Software Foundation | PSF License | https://www.python.org/ |
| PyInstaller (sólo el cargador del build) | 6.22.3 | PyInstaller Development Team | GPLv2+ con excepción para el cargador | https://pyinstaller.org/ |

## Stockfish: código fuente (GPL)
El build incluye `stockfish.exe` **sin modificar**: es el binario oficial de
`stockfish-windows-x86-64-universal.zip` (elige las instrucciones de la CPU al arrancar) de la versión **Stockfish 19**, tag `sf_19` (commit `edb0d9db6731067ec50ce619ff372b463bc4dd5d`).
- Código fuente de esa versión: https://github.com/official-stockfish/Stockfish/tree/sf_19
  (archivo: https://github.com/official-stockfish/Stockfish/archive/refs/tags/sf_19.zip)
- Publicación: https://github.com/official-stockfish/Stockfish/releases/tag/sf_19
- Licencia: `licencias/Stockfish-Copying.txt` (GPLv3).

La app se comunica con Stockfish como un programa aparte, por el protocolo UCI.

## Código fuente de esta app
El código completo (incluidos los scripts que generan el arte, los sonidos y el build) está en el repositorio del
proyecto. Para reconstruir el .exe: `scripts/build_windows.py` (ver `docs/TECNICO.md`).

## Recursos propios
- **Arte del ajedrez** (tablero, piezas, mesa, planilla, reloj, placas, etc.): renders propios hechos en Blender con
  `blender/generar_ajedrez.py` y `blender/generar_interfaz.py`; escena en `blender/ajedrez.blend`. Bajo la licencia de la
  app (GPLv3).
- **Cartas, figuras J/Q/K, dorso, ícono y pantalla de inicio**: dibujados por código (PyQt6), propios.

## Fuentes
Descargadas de [google/fonts](https://github.com/google/fonts). Cada carpeta de `assets/fonts/` incluye su `OFL.txt`.
"Playfair Display" es un nombre de fuente reservado (Reserved Font Name): se usa sin modificar.

## Sonidos
Derivados (recortados, mezclados y normalizados con `scripts/preparar_sonidos.py`) de tres packs de
[Kenney](https://kenney.nl) con licencia CC0 1.0 (dominio público). El crédito no es obligatorio, pero se agradece:
detalle de cada archivo en `assets/sounds/FUENTES.md` y textos de licencia en `assets/sounds/LICENCIA.txt`.
