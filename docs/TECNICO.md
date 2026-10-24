# Mesa Trazada: documentación técnica

App de escritorio para Windows con dos juegos: **Ajedrez contra Stockfish** y **Solitario Klondike**.
Python + PyQt6; reglas de ajedrez con python-chess. El tablero, las piezas, la mesa y los objetos de la partida de
ajedrez son renders propios de Blender (`assets/ajedrez/`); cartas, inicio e ícono se dibujan por código. Sonidos
cortos y sobrios (packs CC0 de Kenney) con volumen global. La presentación para jugadores está en el
[README](../README.md); esta página es para correr, ajustar y compilar desde el código.

## Requisitos
- Windows 10/11 x86-64
- Python 3.10+ (el venv del proyecto usa 3.12)
- Stockfish 19 (`engine/stockfish.exe`, no se versiona)

## Instalación
Desde la raíz del proyecto, en PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```
**Stockfish:** descargar `stockfish-windows-x86-64-universal.zip` de
https://github.com/official-stockfish/Stockfish/releases, extraer el `.exe` y guardarlo como
`engine\stockfish.exe` (o apuntar `STOCKFISH_PATH` en `.env` a otra ruta). El build "universal"
elige solo las instrucciones de la CPU (AVX2, VNNI, etc.).

**Acceso directo en el Escritorio** (abre sin consola, con el ícono de la app; reemplaza uno existente
y funciona aunque el Escritorio esté redirigido a la nube):
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\crear_acceso_directo.ps1
```
Si Windows sigue mostrando un ícono viejo: `ie4uinit.exe -show`; si no alcanza, reiniciar el
Explorador (`Stop-Process -Name explorer -Force`, vuelve a abrirse solo).

## Ejecutar
- Con el acceso directo del Escritorio, o
- `.\.venv\Scripts\python.exe main.py` (con consola, útil para ver el log en vivo).

El log queda en `logs\app.log`. Si algo falla al iniciar, se muestra un diálogo y el detalle va al log.

## Pantalla de inicio
Una mesa de juego partida al medio: a la izquierda el ajedrez, a la derecha el solitario. Al pasar el
mouse, esa mitad se ilumina. Con un clic aparecen ahí mismo las opciones para empezar (Esc o un clic
afuera las cierra; Enter empieza).

## Ajedrez
- Desde el inicio: color (blancas / negras / al azar) y dificultad, y **Jugar**. Con negras, el tablero
  se ve desde tu lado y Stockfish abre la partida. Si falta Stockfish, el inicio lo avisa y no deja jugar.
- Mover arrastrando o con clic en origen y clic en destino. Se marcan en ámbar las casillas legales, la
  pieza elegida y la última jugada, y en rojo el rey en jaque. La coronación abre un diálogo para elegir
  la pieza.
- Aspecto: el tablero (pizarra laqueada con marco), las piezas Staunton y la mesa de nogal son renders de
  Blender (Cycles) incluidos en `assets/ajedrez/`: cada pieza con su sombra de contacto, su sombra proyectada,
  su reflejo en la laca y sus brillos, todo con una única luz arriba a la izquierda. Por código se dibujan
  las coordenadas (dentro de las casillas), las marcas ámbar (pieza elegida con un bloom de sus brillos,
  casillas legales, última jugada), el jaque, la luz de la lámpara y el viñeteado. Al arrastrar, la pieza
  "se levanta": crece un poco, su sombra se aleja y se difumina y el reflejo se separa.
- Alrededor del tablero, sobre la mesa y renderizados con la misma luz: el **cartel del rival** (nivel y Elo
  aproximado) y el tuyo, un **reloj de ajedrez** decorativo (sin cuenta de tiempo) que indica el turno (el que
  acaba de mover tiene su botón hundido) y enciende una luz del lado de Stockfish mientras piensa, la
  **planilla** con las jugadas escritas a mano (la última con resaltador; en partidas largas, hojas: rueda del
  mouse o RePág/AvPág para ver las anteriores), dos **bandejas** de nogal y fieltro con las piezas capturadas y la
  ventaja de material ("+N"), y las **placas de latón** que funcionan como botones.
- El arte se carga la primera vez que se abre el ajedrez (empieza en segundo plano al abrir sus opciones en
  el inicio); al arrancar, el inicio sólo lee las piezas que dibuja.
- **Deshacer** retrocede tu jugada y la del motor (también mientras piensa). **Nueva partida** empieza
  otra con el mismo color y dificultad (con "al azar" vuelve a sortear); para cambiarlos, **Menú**. Las placas
  se recorren con Tab y se activan con Enter o Espacio.
- Fin de partida: el resultado queda escrito en la planilla ("1–0 · Jaque mate") y una tarjeta apoyada encima
  dice quién ganó y por qué (mate, ahogado, material insuficiente, triple repetición o regla de los 50
  movimientos); un clic o Esc la levanta. Con jaque mate, el rey vencido queda acostado en su casilla.
- En el ajedrez, el control de volumen es una perilla de latón (la marca indica el nivel).

## Solitario (Klondike)
- Mesa de casino: paño verde profundo bajo un foco, cartas de papel marfil con sombras, figuras J/Q/K de diseño
  propio y dorso con enrejado ámbar. Las fundaciones vacías muestran el palo que falta; con doble clic un As va
  a la que muestra su palo.
- Animaciones cortas (reparto, giros, vuelo a la fundación, descarte) que nunca hacen esperar: cualquier clic
  las completa al instante. Al arrastrar, la carta se levanta y se marcan en ámbar los destinos válidos.
- Desde el inicio: robar de a 1 o de a 3, y **Repartir**. Durante la partida se puede cambiar desde la
  barra superior; si ya jugaste, pide confirmación porque empieza una partida nueva.
- Clic en el mazo para robar; con el mazo vacío, el clic recicla el descarte (sin límite).
- Arrastrar cartas o secuencias válidas entre columnas y a las fundaciones; si la suelta no es válida,
  vuelven a su lugar. **Doble clic** manda la carta a la fundación si se puede. También se puede
  devolver una carta de la fundación a una columna.
- El descarte muestra las últimas 3 cartas en abanico (en los dos modos); sólo la de arriba se juega.
- **Deshacer** (botón o **Ctrl+Z**): ilimitado hasta el reparto; deshace movimientos, robos y reciclados.
- Si ya no hay forma de subir otra carta a las fundaciones ni de destapar una carta boca abajo
  (probando todas las combinaciones: movimientos entre columnas, recorrer el mazo, devolver cartas de la
  fundación), aparece un aviso con *Nueva partida*, *Deshacer* o *Seguir mirando*. Sólo avisa cuando lo
  pudo comprobar; en las pocas posiciones con demasiadas combinaciones prefiere no avisar.

## Sonido y volumen
- El parlante de la esquina superior derecha (el mismo en el inicio y en los dos juegos) abre el volumen:
  deslizador y botón de silencio. Esc o un clic afuera lo cierran. Es un único volumen para toda la app y
  es lo único que se recuerda entre sesiones.
- Ajedrez: mover, capturar, jaque, enroque, coronar y fin de partida (uno para ganar, otro para perder o
  tablas). Solitario: robar, apoyar una carta, voltear, subir a la fundación, reciclar el mazo, repartir y
  victoria.
- Si la PC no tiene audio, la app funciona igual (sin sonido) y lo anota en el log.
- Origen: packs de [Kenney](https://kenney.nl) con licencia CC0 (dominio público): Casino Audio, Impact
  Sounds y Music Jingles. Detalle de cada archivo en `assets/sounds/FUENTES.md` y licencias en
  `assets/sounds/LICENCIA.txt`. Para regenerarlos desde los packs descargados:
  `.\.venv\Scripts\python.exe -I scripts\preparar_sonidos.py <carpeta con casino\, impact\ y jingles\>`.

## Ajustar la dificultad del ajedrez
Seis niveles, de menor a mayor fuerza. El Elo de cada uno se ve al apoyar el mouse sobre él en el inicio.

| Nivel | Elo aprox. | Cómo juega |
|---|---|---|
| Principiante | ~500 | Debilitamiento propio: busca poco, elige entre varias candidatas y a veces se descuida |
| Novato | ~800 | Igual, con un poco más de profundidad y menos descuidos |
| Aficionado | ~1100 | Igual, con menos descuidos todavía |
| Club | 1400 | Stockfish con `UCI_LimitStrength` + `UCI_Elo` |
| Avanzado | 1800 | Stockfish con `UCI_LimitStrength` + `UCI_Elo` |
| Máximo | — | Stockfish sin límite |

Los niveles humanos (Principiante, Novato, Aficionado) existen porque `UCI_Elo` no baja de 1320 en Stockfish 19.
En cada jugada el motor analiza `MULTIPV` candidatas a profundidad `DEPTH` y después:
1. Si la mejor da mate en 1 o es una captura que le saca al menos `OBVIOUS_CP` a la segunda, la juega con
   probabilidad `OBVIOUS` (no es ciego).
2. Si no, con probabilidad `BLUNDER` se descuida: juega una candidata que pierde entre `BLUNDER_MIN_CP` y
   `BLUNDER_MAX_CP` centipeones (nunca una que deje mate), más seguido las que pierden menos.
3. Si no, elige con probabilidad ∝ exp(−pérdida / `TEMP`): cuanto más alta la temperatura, más seguido
   juega jugadas peores que la mejor.

Editar `.env` (se lee al abrir la app; cerrarla y volver a abrirla después de cambiarlo). Las variables de
los niveles humanos llevan el prefijo del nivel (`PRINCIPIANTE_`, `NOVATO_`, `AFICIONADO_`):

| Variable | Principiante / Novato / Aficionado | Uso |
|---|---|---|
| `*_ELO` | 500 / 800 / 1100 | Elo aproximado que se muestra (no cambia cómo juega) |
| `*_DEPTH` | 1 / 2 / 2 | Profundidad de la búsqueda |
| `*_MULTIPV` | 12 / 12 / 10 | Candidatas que se evalúan |
| `*_TEMP` | 300 / 250 / 150 | Temperatura del softmax, en centipeones |
| `*_BLUNDER` | 0.5 / 0.4 / 0.25 | Probabilidad de descuido por jugada |
| `*_BLUNDER_MIN_CP` / `*_BLUNDER_MAX_CP` | 150-900 / 150-700 / 150-600 | Cuánto pierde un descuido |
| `*_OBVIOUS` | 0.5 / 0.7 / 0.9 | Probabilidad de ver el mate en 1 o la captura gratis |

| Variable | Default | Uso |
|---|---|---|
| `OBVIOUS_CP` | 250 | Ventaja sobre la 2.ª candidata para que una captura cuente como "gratis" |
| `CLUB_ELO` / `CLUB_TIME` | 1400 / 0.3 | `UCI_Elo` y segundos por jugada de Club |
| `AVANZADO_ELO` / `AVANZADO_TIME` | 1800 / 0.5 | Ídem Avanzado |
| `MAXIMO_TIME` | 1.0 | Segundos por jugada de Máximo |
| `ENGINE_MIN_REPLY` | 0.6 | El motor nunca responde antes de esto (aunque calcule en menos) |

Si `CLUB_ELO` o `AVANZADO_ELO` quedan fuera del rango que reporta el motor (Stockfish 19: 1320-3190), se usa
el límite más cercano y se anota en el log. Para un nivel humano más fácil: subir `BLUNDER` o `TEMP`, o bajar
`DEPTH`. Para comprobar un cambio, `scripts\calibrar_dificultad.py` hace jugar a los niveles entre sí y contra
anclas (azar, glotón, Stockfish con UCI_Elo 1320) y muestra el puntaje de cada emparejamiento.
Calibración de los valores actuales (cada nivel contra el de abajo; criterio ≥ 70 %): Novato–Principiante
83,8 %, Aficionado–Novato 91,2 %, Club–Aficionado 95 %, Avanzado–Club 90 %. Principiante le gana siempre a un
jugador al azar y al "glotón" (captura lo más valioso que puede) le saca 71 %, con muchas tablas: le cuesta
dar mate, como a un principiante.

Otras variables:

| Variable | Default | Uso |
|---|---|---|
| `STOCKFISH_PATH` | `engine/stockfish.exe` | Relativa a la raíz del proyecto o absoluta |
| `LOG_LEVEL` | INFO | Nivel de logging (DEBUG muestra los pedidos al motor y cada jugada elegida con su pérdida en centipeones) |
| `LOG_DIR` | logs | Carpeta de `app.log` |

## Arte del ajedrez (Blender)
El tablero, las piezas y la mesa salen de `blender/generar_ajedrez.py` (escena en `blender/ajedrez.blend`;
Cycles + OptiX). Los PNG están en `assets/ajedrez/` y `blender/INTEGRACION.md` describe escala, puntos de
apoyo, orden de dibujo y medidas. Para regenerarlos, en la consola de Python de Blender:
`exec(open(r"<proyecto>/blender/generar_ajedrez.py", encoding="utf-8").read())` y después `export_all()`.
Las vistas previas (`blender/previews/`) y los respaldos `*.blend1` no se versionan.

## Fuentes
La pantalla de inicio y la del ajedrez usan fuentes embebidas en `assets/fonts/` (Playfair Display, Inter y
Caveat, la letra a mano de la planilla; descargadas de
[google/fonts](https://github.com/google/fonts), licencia SIL Open Font License 1.1; cada carpeta incluye
su `OFL.txt`). Se cargan al iniciar la app, así que no hace falta instalarlas.

## Ícono
Se dibuja en `src/app/icon_painter.py`. Para regenerar `assets\app_icon.ico` y `assets\app_icon_256.png`:
```powershell
.\.venv\Scripts\python.exe scripts\generar_icono.py
```

## Build de Windows (.zip para publicar)
```powershell
.\.venv\Scripts\python.exe scripts\build_windows.py
```
- PyInstaller en **modo carpeta** (`--onedir --windowed`): un .exe junto a `_internal/` (Python, Qt, Stockfish,
  assets). Se eligió sobre "un solo .exe" porque éste se descomprime entero (~190 MB) en `%TEMP%` cada vez que se
  abre (arranque de varios segundos) y es un patrón que los antivirus marcan más seguido. Nuitka no se usa: necesita un
  compilador de C, tarda mucho más y el arranque lo domina Qt igual.
- Incluye `engine/stockfish.exe` y su `Copying.txt` (no versionados: hay que tenerlos), las fuentes, los sonidos, el
  arte, `LICENSE.txt`, `LEEME.txt`, `config.env.ejemplo` y `licencias/` (cada componente). Saca lo que Qt arrastra y la
  app no usa (PDF, TLS, FFmpeg: los WAV suenan con el backend de Windows Media).
- Versión: `src/common/app_info.py` (`VERSION`, único lugar). Resultado: `dist/MesaTrazada-<versión>-windows-x64.zip`
  y el sha256 en la salida. Ícono del .exe: `assets/app_icon_blender.ico` (`scripts/generar_icono_blender.py`).
- Al final prueba el .zip en una carpeta limpia (`%TEMP%\mesatrazada_prueba_limpia`, sin el venv en el PATH):
  `scripts/probar_build.py` mide el arranque y corre `MesaTrazada.exe --autoprueba informe.json`
  (`src/app/smoke_test.py`: inicio, "Acerca de", 3 jugadas contra cada nivel, el motor se cierra, solitario, sonido,
  cierre). `--sin-prueba` la saltea.
- El .exe empaquetado busca un `.env` opcional junto a él y escribe el log en `%LOCALAPPDATA%\MesaTrazada\logs` (la carpeta del nombre anterior,
  `AjedrezSolitario`, se migra una vez; el volumen guardado en el registro, también).
- Antes de empaquetar se sacan los metadatos de texto de los PNG (`scripts/limpiar_metadatos_png.py`: Blender graba
  ahí la ruta del .blend, con el usuario de la PC).

## Tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```
Incluye tests con Stockfish real (se saltean si no está instalado) que verifican que el proceso del
motor se cierra al volver al menú, cambiar de juego o cerrar la ventana.
