# Página de itch.io (borrador, sin publicar)

> Todo lo de acá es texto para copiar en el panel de itch.io cuando se cree la página. Nombre elegido: *Mesa Trazada*
> (ver `nombres.md`).

## Datos del proyecto
| Campo | Valor |
|---|---|
| Título | Mesa Trazada |
| URL sugerida | `<usuario>.itch.io/mesa-trazada` |
| Tipo | Downloadable · Game |
| Estado | Released |
| Precio | **$0 o donación** ("No payment" + "Allow donations": sugerido USD 2) |
| Plataforma | Windows |
| Archivo | `MesaTrazada-1.0.0-windows-x64.zip` (~130 MB), marcado como Windows |
| Género | Card Game (secundario: Strategy / Board Game) |
| Idioma | Spanish (la interfaz); la página también en inglés |
| Licencia del código | GPLv3 (enlace al repositorio en la descripción) |
| Herramientas (Made with) | Python, Qt, Blender |
| Accesibilidad | Teclado (Tab/Enter/Espacio en las placas, Ctrl+Z, Esc), alto contraste de los textos, sin parpadeos |
| Contenido | Sin violencia, sin datos personales, sin conexión, sin publicidad |

## Descripción corta (tagline, ≤ 140 caracteres)
Ajedrez contra Stockfish en 6 niveles y Solitario Klondike, sobre una mesa iluminada por una lámpara. Gratis y libre.

*EN:* Chess against Stockfish (6 levels) and Klondike solitaire on a lamp-lit table. Free and open source.

## Descripción larga

**Mesa Trazada** es una mesa de juego tranquila para Windows con dos clásicos de siempre, sin publicidad, sin
cuentas y sin conexión a internet.

### ♟ Ajedrez contra Stockfish
- **6 niveles calibrados**: Principiante (~500), Novato (~800), Aficionado (~1100), Club (1400), Avanzado (1800) y
  Máximo (Stockfish 19 a pleno). Los niveles bajos juegan como una persona que está aprendiendo: miran poco hacia
  adelante, a veces se descuidan, pero ven el mate en una.
- Todo lo que hay sobre la mesa está renderizado en 3D con la misma luz: el tablero laqueado, las piezas Staunton, una
  **planilla** donde las jugadas quedan escritas a mano, un **reloj** que marca el turno (y se ilumina mientras
  Stockfish piensa), **bandejas** con las piezas capturadas y la diferencia de material, y **placas de latón** que hacen
  de botones.
- Arrastrar o clic-clic, coronación, deshacer, y al dar mate el rey vencido se acuesta en su casilla.

### 🂡 Solitario Klondike
- Robo de a 1 o de a 3, **deshacer ilimitado** (Ctrl+Z) y doble clic para subir cartas a la fundación.
- Cartas y figuras de diseño propio sobre un paño de casino; animaciones cortas que nunca hacen esperar.
- Un aviso honesto de **"No quedan movimientos"**: la app prueba todas las combinaciones y sólo avisa cuando está segura.

### También
- Sonidos suaves (Kenney, CC0) con un único volumen.
- Interfaz en español.
- **Código abierto (GPLv3)**: <!-- TODO: enlace al repositorio -->

### Instalación
Descomprimí el .zip y abrí `MesaTrazada.exe`. No hace falta instalar nada. Windows 10/11 de 64 bits.
La app no está firmada: si SmartScreen avisa, elegí **Más información → Ejecutar de todas formas**.

### Créditos
Motor: Stockfish 19 (GPLv3) · Reglas: python-chess · Interfaz: PyQt6 / Qt · Fuentes: Playfair Display, Inter, Caveat
(OFL) · Sonidos: Kenney (CC0). Detalle y licencias en `CREDITS.md` y en la carpeta `licencias/` del .zip.

---

**EN —** *Mesa Trazada is a calm game table for Windows with two classics: chess against Stockfish with six calibrated levels (from a
~500 Elo beginner that plays like a human learner, to full-strength Stockfish 19) and Klondike solitaire with
unlimited undo and an honest "no moves left" notice. Everything on the chess table — lacquered board, Staunton pieces,
a hand-written scoresheet, a chess clock, captured-piece trays and brass plates as buttons — is rendered in 3D under a
single lamp. No ads, no accounts, works offline. Interface in Spanish. Free and open source (GPLv3).*

## Etiquetas (tags)
`chess`, `solitaire`, `klondike`, `card-game`, `board-game`, `stockfish`, `singleplayer`, `relaxing`, `offline`,
`open-source`, `spanish`, `free`

(itch.io admite hasta 10 visibles en la página: priorizar las 10 primeras.)

## Capturas para subir (en este orden)
1. `docs/capturas/ajedrez_partida.jpg` (portada / imagen principal)
2. `docs/capturas/solitario.jpg`
3. `docs/capturas/ajedrez_mate.jpg`
4. `docs/capturas/inicio.jpg`
5. `docs/capturas/acerca_de.jpg`

Imagen de portada (cover, 630 x 500): recortar `ajedrez_partida.jpg` sobre el tablero y la planilla.

## Donaciones
Activar "Allow donations" con monto sugerido. Enlaces externos (Cafecito, Ko-fi, GitHub Sponsors) en la descripción
cuando existan las cuentas: <!-- TODO -->
