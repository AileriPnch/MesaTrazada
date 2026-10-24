# Integración del arte renderizado del ajedrez

Generado por `blender/generar_ajedrez.py` (escena en `blender/ajedrez.blend`). Todo está en `assets/ajedrez/`.
Render: Cycles + OptiX, denoise OptiX, máximo 1024 muestras por píxel con muestreo adaptativo (umbral 0,01),
transformación de vista Standard (los PNG son sRGB, 8 bits, RGBA).

## Archivos

| Archivo | Tamaño | Qué es |
|---|---|---|
| `{color}_{pieza}.png` | 512 × 512 | La pieza, fondo transparente |
| `{color}_{pieza}_sombra.png` | 512 × 512 | Sombra proyectada (sólo alfa útil; negro) |
| `{color}_{pieza}_contacto.png` | 512 × 512 | Oclusión de contacto de la base (sólo alfa útil; negro) |
| `{color}_{pieza}_reflejo.png` | 512 × 512 | Reflejo en la laca, con alfa (Fresnel real) |
| `{color}_{pieza}_brillo.png` | 512 × 512 | Sólo los especulares fuertes, alfa por intensidad |
| `tablero.png` | 2048 × 2048 | Tablero cenital con marco, fondo transparente, sin coordenadas |
| `mesa.png` | 3840 × 2880 | Mesa de nogal cenital (4:3), sin tablero |

`{color}` = `blancas` / `negras`; `{pieza}` = `rey`, `dama`, `torre`, `alfil`, `caballo`, `peon`.

## Sprites de las piezas

- Cámara ortográfica inclinada 20° hacia abajo; todas las piezas con la misma escala.
- **Escala: 1 casilla = 426.67 px** en el sprite (el sprite cubre 1,2 casillas). Para una casilla de
  `s` px: escalar todos los sprites por `s / 426.67`.
- **Punto de apoyo** (centro de la base, apoyada en el tablero):
  - pieza, `_sombra`, `_contacto`, `_brillo`: **(256.0, 445.4)** px (desde arriba a la izquierda).
  - `_reflejo`: **(256.0, 51.2)** px: el reflejo cuelga hacia abajo desde ahí.
- **Ubicación en la casilla:** el apoyo va centrado en X y a **0,15 del lado de la casilla por encima de su borde
  inferior**. Con eso el rey entra completo en la casilla.
- Medidas en fracción del lado de la casilla (vista del juego):

| Pieza | Alto total | Por encima del apoyo | Por debajo del apoyo |
|---|---|---|---|
| rey | 0.892 | 0.803 | 0.089 |
| dama | 0.831 | 0.745 | 0.086 |
| alfil | 0.791 | 0.712 | 0.079 |
| caballo | 0.759 | 0.677 | 0.082 |
| torre | 0.719 | 0.637 | 0.082 |
| peon | 0.663 | 0.591 | 0.072 |

- Los dos caballos miran a la izquierda.

## Orden de dibujo (por frame)

1. Tablero (`tablero.png`) sobre la mesa.
2. `_contacto` de todas las piezas.
3. `_sombra` de todas las piezas.
4. `_reflejo` de todas las piezas, **recortado al área de las 8 × 8 casillas** (no se refleja en el marco ni en la mesa;
   sin recorte, los de la primera fila caen sobre el marco).
5. Piezas, de la fila de atrás (arriba en pantalla) hacia la de adelante.
6. `_brillo` encima de cada pieza (alpha compositing normal; para bloom, desenfocarlo y sumarlo).

## Opacidades ya horneadas y ajustes desde el código

- `_sombra`: núcleo con alfa 0.62 (incluye el disco bajo la base: es la sombra de la base cuando se levanta).
- `_contacto`: máximo 0.9.
- `_reflejo`: alfa = Fresnel de la laca a este ángulo (máximo ≈ 0,15). Es tenue a propósito; si se quiere más, multiplicar el
  alfa desde el código.
- `_brillo`: luminancia lineal > 0.3 (umbral), alfa proporcional a la intensidad; el color es el del especular normalizado.
- Al levantar una pieza: `_contacto` se apaga; `_sombra` se desplaza (abajo a la derecha, lejos de la luz) y se difumina;
  `_reflejo` se separa de la base y se apaga.
- Luz: principal arriba a la izquierda (sombras abajo a la derecha); contraluz atrás a la derecha (sólo las negras reciben la
  más fuerte). El brillo de la lámpara en el tablero y la contraluz se refuerzan desde el código.

## Tablero (`tablero.png`)

- 2048 × 2048 px, fondo transparente fuera del marco. Cubre 8 casillas + marco de 0.2 casilla de cada lado (8,4 casillas).
- **Casilla: 243.81 px. Marco: 48.76 px.** Las casillas empiezan en (48.76, 48.76) px.
- a1 abajo a la izquierda y oscura (vista con blancas abajo). Sin coordenadas (las dibuja el código).
- Exposición calibrada para que las casillas claras centrales den el color del tema. Medido en el archivo:
  e4 (clara) `#5e636d` (tema `#5d6574`), d4 (oscura) `#2d313d` (tema `#2b3140`); hacia los bordes oscurece por la lámpara
  (h1 `#4a4e56`), arriba a la izquierda el brillo suave de la laca.

## Mesa (`mesa.png`)

- 3840 × 2880 px (4:3), vista cenital, sin el tablero. Cubre 16 × 12 casillas: **240 px por casilla**.
- Mismo centro que el tablero. Para ventanas 16:9 recortar el centro a 3840 × 2160; para 4:3 se usa entera.
- Para que la veta tenga la misma escala que el tablero dibujado con casillas de `s` px, escalar la mesa por `s / 240`
  (si no alcanza para cubrir la ventana, se puede escalar más: es fondo).

## Regenerar

En Blender: `exec(open(r"<proyecto>/blender/generar_ajedrez.py", encoding="utf-8").read())` y después `export_all()`.

# Interfaz de la partida (objetos sobre la mesa)

Generado por `blender/generar_interfaz.py` (reusa materiales, luces y cámaras de `generar_ajedrez.py`; no guarda el
`.blend`). Todo está en `assets/ajedrez/interfaz/`, con `interfaz.json` (anclas y rectángulos de cada PNG) y la
revisión de alfas. Mismo render que el tablero: Cycles + OptiX, denoise OptiX, 1024 muestras, vista Standard, PNG sRGB
de 8 bits RGBA.

## Archivos

| Archivo | Cámara | Px por casilla | Estados / pases |
|---|---|---|---|
| `planilla` | cenital | 256 | cuerpo (portapapeles de cuero, clip de latón, hoja marfil con renglones impresos), `_sombra`, `_contacto` |
| `bandeja` | cenital | 256 | nogal + fieltro bordó, 1,1 x 3 casillas (la misma para los dos lados), `_sombra`, `_contacto` |
| `placa_principal` | cenital | 256 | `_normal` / `_hover` / `_pressed` / `_disabled` (latón cepillado #cfa96a: cálido, pulido y con veta fina a lo largo; más brillo especular que el bronce de las secundarias), `_sombra`, `_sombra_pressed`, `_contacto` |
| `placa_secundaria` | cenital | 256 | ídem en bronce (#b8915a; Deshacer y Menú usan la misma) |
| `cartel` | cenital | 256 | placa de bronce sin estados, `_sombra`, `_contacto` |
| `tarjeta` | cenital | 256 | tarjeta de papel con doble filete (fin de partida), `_sombra`, `_contacto` |
| `perilla` | cenital | 512 | `_normal` / `_hover` / `_pressed`, `_sombra`, `_contacto` (sólo en el ajedrez) |
| `reloj` | 20° (la de las piezas) | 256 | `_blancas` / `_negras` (botón hundido) / `_parejos`, `_luz_blancas`, `_luz_negras` (sólo la lente encendida), `_sombra`, `_contacto` |
| `{color}_rey_acostado` | 20° | 426,67 | los 5 pases de las piezas (cuerpo, `_sombra`, `_contacto`, `_reflejo`, `_brillo`) |

Total: 48 PNG, 7,7 MB.

## Anclas (`interfaz.json`)

Todas las medidas en px del PNG, origen arriba a la izquierda:
- `ancla`: centro del objeto apoyado en la mesa; `objeto`: su caja (x0, y0, x1, y1). Para ubicarlo en la app:
  escalar por `s / px_por_casilla` (s = lado de la casilla) y hacer coincidir `objeto` con su lugar.
- `planilla`: `papel`, `encabezado` (y0, y1), `renglones` (y de cada línea impresa), `filas` (10),
  `columnas` (papel izquierda, fin de los números, mitad, papel derecha) y `pie` (y0, y1, para "Hoja n de m").
- `bandeja`: `fieltro` (donde se apoyan las piezas). Placas y cartel: `cara` (donde va el texto grabado, sin los
  tornillos). Tarjeta: `texto`.
- `reloj`: `ancla` = centro de la base; `caja` = el frente de la caja; `luces` y `esferas` por lado.
  Izquierda = blancas (botón marfil), derecha = negras (botón ébano). Como en un reloj real, el que acaba de mover
  aprieta su botón: con el botón blanco hundido mueven las negras.
- `rey_acostado`: mismo encuadre y apoyo que las piezas (256; 445,4), reflejo (256; 51,2).
- `revision.<archivo>.visible`: la caja de lo que se ve (alfa >= 50 %) de cada PNG. La app la usa para el reloj
  (`reloj_parejos.png`, con los botones arriba): esa caja entra entera en su lugar, así no pisa el cartel de arriba.

## Luz y materiales

- Cada objeto se renderiza en su lugar de la disposición de la app (bandeja al costado del tablero, columna a la
  derecha): recibe la luz de la lámpara que le toca, con la luz principal arriba a la izquierda (sombras abajo a la
  derecha).
- Relleno de área sobre la columna, con light linking sólo hacia la interfaz: el papel se calibra a luminancia lineal
  0,80 en su centro (marfil cálido); la mesa no lo recibe.
- Panel claro visible sólo en los reflejos de los metales (light linking): el latón pulido visto desde arriba
  reflejaría el mundo negro y saldría oscuro. El cuero no tiene barniz y no lo refleja.
- Luz de frente sólo para el reloj (sus esferas miran a la cámara de 20°). Se enciende sólo mientras se renderiza el
  reloj: con la colección de destino vacía, Blender ignora el light linking y la luz ilumina todo.
- `_sombra` y `_contacto`: como las piezas (shadow catcher en la mesa; núcleo 0,62 y máximo 0,9) y con el alfa que
  cae suave a 0 cerca de los bordes del PNG (el contacto es oclusión local y no se corta en el borde).
- El texto (jugadas, números, encabezados, carteles, botones, tarjeta) NO está en los renders: lo dibuja el código.
- Contraste (letra grabada oscura, `#2a1a08`; medido en `tests/test_table_objects.py`): el bronce de las secundarias y
  del cartel es #b8915a (con el #8a6a3c original ni el negro llegaba a 4,5:1) y el latón apagado de "deshabilitada"
  #a39885; la placa apretada se oscurece poco (panel 1,1). Resultado: ≥ 4,6:1 en normal/hover/apretada y ≥ 3,4:1
  deshabilitada.
- Latón cepillado: ruido muy estirado a lo largo de la placa que modula rugosidad (0,10-0,30: más especular que el bronce) y tono (±15 %). Sin
  anisotropía: con la tangente por defecto (radial alrededor del eje del objeto) deja un remolino en el centro.

## Regenerar la interfaz

```
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b blender\ajedrez.blend -P blender\generar_interfaz.py -- planos
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b blender\ajedrez.blend -P blender\generar_interfaz.py -- volumen
```
Sólo algunos objetos planos: `-- placa_principal,bandeja` (nombres: planilla, bandeja, placa_principal,
placa_secundaria, cartel, tarjeta, perilla). `mock` = la escena completa a baja calidad
(`blender/previews/interfaz_mock.png`); `anclas` = recalcula las anclas del reloj sin renderizar; `revisar` = rehace
`interfaz.json` y la revisión de alfas. Para pruebas: `-- <modo> <muestras> <carpeta>`. OptiX explícito; si no hay,
avisa y usa CUDA (o CPU).
