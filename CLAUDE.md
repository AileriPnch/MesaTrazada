# Mesa Trazada (antes "Ajedrez y Solitario")

## Qué es
App de escritorio Windows con dos juegos: Ajedrez contra Stockfish y Solitario Klondike.
Sobria y funcional. Animaciones cortas que nunca hacen esperar: el hover del inicio (180 ms) y, en el
solitario, reparto, giros, vuelos a la fundación, reacomodo del descarte y la luz de la victoria.
Sonidos cortos y suaves (packs CC0 de Kenney) con un volumen global. Se abre desde un acceso directo con
`pythonw.exe` (sin consola).

## Stack
- Python 3.12 (venv en `.venv`) + PyQt6 (dibujo con QPainter; el ajedrez usa renders de Blender en
  `assets/ajedrez/`, el resto se dibuja por código)
- `chess` (python-chess) para reglas y UCI
- QtMultimedia (viene con PyQt6; `QSoundEffect` para los efectos, WAV) — sin dependencias nuevas
- Stockfish 19 en `engine/stockfish.exe` (gitignored)
- pytest; PyInstaller (sólo el build de Windows)
- Licencia GPLv3 (como Stockfish, python-chess y PyQt6): `LICENSE` (encabezado + texto completo) y `CREDITS.md`

## Estructura
```
config.py                     Settings (dataclass) leído de .env OPCIONAL (junto al .exe en el build); defaults si no
                              está; rutas relativas → raíz del proyecto (en el build, `_internal/`)
main.py                       Entrada: logging → excepthook → _run() (imports diferidos) → diálogo si falla;
                              `--autoprueba <informe.json>` corre la prueba de humo (build)
LICENSE / CREDITS.md          GPLv3 con encabezado "Juan Scandizzo" / cada componente de terceros (versión, autor,
                              licencia, enlace; Stockfish con tag sf_19 y commit)
README.md                     Público (español + resumen en inglés), capturas de docs/capturas/
docs/TECNICO.md               El README técnico de antes + "Build de Windows"
docs/capturas/                Capturas del README (JPG, versionadas; sólo la ventana)
docs/lanzamiento/             itchio.md (textos de la página), nombres.md (propuestas verificadas), LEEME.txt (va
                              junto al .exe)
assets/app_icon.ico|_256.png  Ícono por código (scripts/generar_icono.py): lo usa el encabezado del inicio
assets/app_icon_blender.*     Ícono PROPUESTO (caballo de Blender + naipe; scripts/generar_icono_blender.py): ventana,
                              acceso directo y .exe
assets/ajedrez/               Arte del ajedrez renderizado en Blender (versionado): 60 sprites de 512 px (pieza,
                              _sombra, _contacto, _reflejo, _brillo por color y pieza), tablero.png, mesa.png
assets/ajedrez/interfaz/      Objetos de la mesa (48 PNG + interfaz.json con anclas y revisión de alfas): planilla,
                              bandeja, placas (4 estados), cartel, tarjeta, reloj (3 estados + luces), perilla, rey
                              acostado
blender/                      generar_ajedrez.py + generar_interfaz.py + ajedrez.blend + INTEGRACION.md (medidas y
                              orden de dibujo); previews/ y *.blend1 NO versionados (.gitignore)
assets/fonts/<Familia>/       Fuentes embebidas (google/fonts, variables) + su OFL.txt: Playfair Display, Inter y
                              Caveat (lo escrito a mano en la planilla del ajedrez)
assets/sounds/                13 WAV (mono 16 bits 44,1 kHz) + LICENCIA.txt (CC0 de Kenney) + FUENTES.md (origen
                              de cada uno). Los genera scripts/preparar_sonidos.py desde los packs descargados
docs/screenshots/             Capturas de revisión (NO versionadas: .gitignore)
src/app/
  main_window.py              QMainWindow + QStackedWidget: inicio fijo + UNA pantalla de juego a la vez;
                              open_chess(color, dificultad) / open_solitaire(robo) arrancan sin página intermedia
  stylesheet.py               Estilo global de los juegos: Fusion + paleta + QSS con objectNames (segmentButton…)
  palette.py                  Alias de colores que usan los juegos; los valores vienen de common/theme.py
  volume_control.py           VolumeControl: parlante + panel (deslizador, silencio) hijos de la ventana, en la
                              esquina superior derecha de TODAS las pantallas; Esc / clic afuera (sólo cierra)
  speaker_button.py           Botón redondo con el parlante dibujado por código (ondas según volumen, cruz); una
                              pantalla puede cambiarle la "piel" (`set_skin`): el ajedrez pone la perilla de latón
  home/                       Pantalla de inicio "mesa de juego" (ver sección propia)
    home_screen.py            HomeScreen: mitades clickeables, hover, opciones (Esc / clic afuera cierra),
                              regeneración diferida al cambiar el tamaño; señales chess_/solitaire_requested
    home_layout.py            Side, HomeLayout: geometría y tipografía proporcionales (u = 1 a 1000x720)
    home_layers.py            HomeLayers: capas pre-renderizadas por tamaño+DPR y composición del frame
    hover_fader.py            HoverFader: intensidad 0..1 por mitad con QVariantAnimation (180 ms)
    options_panel.py          OptionsPanel (grupos excluyentes + botón principal), chess_/solitaire_panel,
                              check_engine (sin Stockfish: mensaje y "Jugar" deshabilitado)
    chess_art.py              Tablero en perspectiva (QTransform.quadToQuad) + piezas de partida avanzada (los
                              cuerpos renderizados de Blender, sin cargar el resto del arte)
    cards_art.py              Naipes sueltos + abanico con card_painter (mismo diseño que el juego)
    neon.py                   Neón: línea divisoria, contorno del tablero/abanico, halo del nombre
  icon_painter.py             Ícono por código: caballo (path propio) + naipe rotado; ≤24 px sólo caballo
  windows_integration.py      AppUserModelID + carga del ícono (app_icon_blender.ico)
  about_dialog.py             "Acerca de" (GlassDialog): versión, licencia, créditos agrupados por rol, donaciones
                              (sólo las que tengan enlace), "Ver licencias" (abre paths.licenses_dir); F1 o el enlace
                              discreto abajo a la derecha del inicio (`HomeScreen.about_link`)
  smoke_test.py               Prueba de humo del build (inicio, Acerca de, 3 jugadas contra cada nivel, el motor muere,
                              solitario, sonido que llega a sonar, cierre) → JSON + capturas
src/common/theme.py           TOKENS de diseño de toda la app: Colors, TypeScale (Playfair Display + Inter), Spacing,
                              Radii, ButtonTokens
                              (PRIMARY ámbar relleno / SECONDARY contorno, con hover/pressed/checked/disabled),
                              PlaqueTokens (cartel del título), NeonTokens, Motion, CornerTokens (volumen),
                              PieceLook (pieza levantada), BoardLook (marco, lámpara, reflejo, halo/bloom de la
                              elegida, coordenadas, tintes ámbar, charco de luz de la mesa), TableLook (objetos de
                              la mesa del ajedrez: medidas en casillas, textos, foco, luz del reloj), CardLook
                              (solitario); colores pen_ink / print_ink / highlighter / engrave / thinking;
                              px(valor, u), window_scale(w, h)
src/common/app_info.py        UN lugar: APP_NAME, VERSION (1.0.0), AUTHOR, SOURCE_URL, DONATIONS (vacías = ocultas),
                              CREDITS (los usa el Acerca de; test: también en CREDITS.md)
src/common/paths.py           Carpetas desde el código o empaquetada: recursos, instalación (.env, licencias/), logs
                              (%LOCALAPPDATA%\MesaTrazada\logs en el build; migra la carpeta vieja
                              AjedrezSolitario una vez: migrate_legacy_data)
src/common/glow.py            render_layer / to_device / blurred / blur_image (desenfoque pirámide) / glow_layer
src/common/textures.py        Madera (a media resolución), paño del inicio y paño de casino (paint_casino_felt), ruido
                              en mosaico, luz de lámpara, viñeteado
src/common/backdrop.py        CachedBackdrop: fondo de pantalla cacheado; al redimensionar se estira y se regenera después
src/common/raster.py          Capas en px físicos: clip (máscara), edge_band (silueta menos ella corrida), tint
src/common/glass_dialog.py    GlassDialog: diálogo sin marco, vidrio oscuro, título Playfair + texto Inter, centrado
src/common/sound.py           Sound (enum de efectos), SoundPlayer (un QSoundEffect por sonido, sin ráfagas),
                              install / play / play_later (sin reproductor instalado no hace nada: tests)
src/common/volume.py          Volume (0-100 + silencio, señal changed) y settings_store(): QSettings del usuario
src/common/qss.py             rgba() y button_qss(selector, tokens, u): QSS de botones desde los tokens
src/common/fonts.py           load_fonts(): registra assets/fonts en QFontDatabase (main.py y conftest, una vez)
src/common/game_screen.py     Base GameScreen: señal back_requested, shutdown()
src/common/logging_setup.py   setup_logging(log_dir, level)
src/common/pixmap_cache.py    PixmapCache: pixmaps por (clave, tamaño, DPR); se vacía al cambiar la escala
src/chess_game/
  game_state.py               ChessGame: lógica pura (turnos, deshacer, resultado + motivo, SAN). Sin Qt
  difficulty.py               Difficulty (6 niveles) → EngineLevel(mode, elo, seconds, human) desde Settings;
                              Mode: HUMAN (propio) / LIMITED (UCI_Elo) / FULL; describe() = tooltip del inicio
  move_choice.py              Modo humano: candidatas del MultiPV → obvia / descuido / softmax por pérdida en cp.
                              Sin Qt, RNG inyectable
  engine_search.py            search_move(engine, board, level, rng): configura TODAS las opciones del modo y
                              busca; jugada única sin buscar. La usan el worker y la calibración. Sin Qt
  engine_worker.py            EngineWorker (vive en QThread): abre Stockfish, think() → search_move (log DEBUG de la
                              jugada y su pérdida), shutdown() thread-safe
  engine_controller.py        EngineController (hilo UI): request_move / cancel / shutdown; descarta pedidos viejos;
                              retiene la jugada hasta `min_reply` (ritmo humano, QTimer cancelable)
  art_library.py              Arte de Blender (assets/ajedrez/): medidas (426,67 px por casilla, apoyos, tablero
                              243,81/48,76, mesa 240), ArtLibrary (todos los PNG), prefetch() en otro hilo,
                              library() (espera o carga), piece_body() (sólo cuerpos: el inicio); `ui` =
                              InterfaceArt (objetos de la mesa); toppled(color, capa) = el rey acostado
  interface_art.py            InterfaceArt: los PNG de assets/ajedrez/interfaz/ + interfaz.json (`box`, `visible`)
  board_glare.py              Saca el velo del brillo del render (b6-b7: agrisaba las casillas) restando el exceso
                              de cada casilla sobre la caída normal de la luz; lo usa ArtLibrary al cargar
  piece_sprites.py            Sprites escalados (Smooth) por tamaño de casilla: en reposo suelo (contacto +
                              sombra), reflejo (x BOARD_LOOK.reflection) y cuerpo (pieza + brillo); levantada;
                              halo (silueta) y bloom (brillo) ámbar de la elegida; toppled_sprites (rey acostado).
                              Offsets respecto del apoyo
  piece_painter.py            piece_pixmap (sprite entero, inicio) / piece_icon (recortada, coronación)
  board_painter.py            BoardGeometry (casillas de px físicos enteros) + render_board (tablero.png escalado
                              a la grilla + refuerzo de la lámpara) + coordinate_labels (una imagen por etiqueta)
  board_assets.py             BoardAssets: tablero + coordenadas + sprites + marcas (punto, anillo, jaque) por
                              geometría/DPR, generados a demanda; anchor(sq) = apoyo de la pieza
  board_scene.py              scene_order (qué y en qué orden, puro: se testea) + paint_position (sólo copia
                              pixmaps, en px físicos; reflejos recortados a las casillas; `toppled`: rey acostado)
  board_view.py               Widget del tablero: clic-clic y arrastrar-soltar → move_attempted(desde, hasta);
                              repintado parcial al arrastrar; al redimensionar estira y regenera después
  chess_table.py              ChessTable(GameScreen): ubica tablero y objetos con table_layout (sin layouts de Qt),
                              fondo cacheado con las sombras de los objetos horneadas; `volume_skin` (perilla)
  chess_backdrop.py           Fondo: mesa.png centrada en el tablero (escala s/240 o la que cubra), charco de luz,
                              sombra del tablero, sombras/contactos de los objetos, viñeteado (CachedBackdrop)
  table_layout.py             table_layout(ancho, alto, dpr) → TableLayout (puro): tablero, bandejas, carteles,
                              reloj, planilla, placas y la esquina del volumen, en casillas (TABLE_LOOK)
  table_sprites.py            Placement/place (la caja de un PNG dentro de un rectángulo), UiSprites (PNG escalados
                              por tamaño y DPR; estira mientras se redimensiona), engrave (texto grabado)
  table_object.py             Placed (mixin: ubica el PNG y da sus sombras para el fondo) + TableObject (QWidget)
  table_side.py               TableSide: crea y ubica todos los objetos; set_info / set_status / set_moves /
                              set_board / show_card; señales undo / new_game / back
  score_sheet.py              ScoreSheet: planilla (Caveat, encabezados impresos, resaltador, hojas, rueda y
                              RePág/AvPág, resultado al pie)
  chess_clock.py              ChessClock: turno (botón del que acaba de mover hundido), luz de Stockfish, parejos
  table_plates.py             NamePlate (cartel grabado) + CapturedTray (bandeja: capturadas en 2 columnas, "+N")
  brass_button.py             BrassButton(QAbstractButton): placa en 4 estados, texto grabado, Tab/Enter/Espacio,
                              filete de foco
  result_card.py              ResultCard: tarjeta de fin de partida (o motor faltante) sobre la planilla; clic/Esc
  knob_skin.py                KnobSkin: perilla de latón del volumen (marca del nivel, silencio), sólo en el ajedrez
  material.py                 lost_pieces / balance: capturadas y diferencia de material (coronación ≠ captura). Sin Qt
  chess_dialogs.py            MessageDialog: error del motor (GlassDialog, no bloquea)
  move_sound.py               move_sound(board, jugada) / end_sound(resultado, jugador). Sin Qt
  promotion_dialog.py         Diálogo de coronación (GlassDialog; ask_promotion)
  color_choice.py             ColorChoice: blancas / negras / al azar (resolve() sortea en cada partida)
  chess_screen.py             ChessScreen(ChessTable): orquesta partida y motor; start_game(color, dificultad);
                              _push suena y mueve; _advance() decide quién mueve y actualiza la mesa (reloj,
                              planilla, bandejas, tarjeta, rey acostado); engine_error en la tarjeta
src/solitaire/
  cards.py                    Suit, Card (frozen), new_deck(). Sin Qt
  rules.py                    can_place_on_tableau / can_place_on_foundation / is_valid_sequence. Sin Qt
  klondike.py                 KlondikeGame: reparto, draw() con reciclado, movable_cards/can_move/move,
                              foundation_target, volteo automático, is_won, `actions`, undo(). Sin Qt
  snapshot.py                 GameState inmutable + take/restore: historial para deshacer. Sin Qt
  search_state.py             Estado compacto para la búsqueda de traba (enteros, columnas canónicas, ciclo del
                              mazo con puntero). Sin Qt
  search_moves.py             successors(): todas las jugadas legales + poda exacta de devoluciones inútiles. Sin Qt
  stuck_detector.py           StuckSearch: búsqueda en anchura acotada (nodos + tiempo), reanudable por porciones;
                              is_stuck(), board_key(). Sin Qt, no muta la partida
  stuck_watcher.py            Corre la búsqueda en porciones de 10 ms dentro del bucle de eventos; emite `stuck`
  table_layout.py             TableLayout: escala con la ventana, abanico del descarte, compresión de
                              columnas en 2 etapas, hit_test, top_rect, drop_target (mayor superposición válida);
                              foundation_labels (palo que muestra cada fundación vacía)
  suit_shapes.py              Palos propios con QPainterPath (corazón, diamante, pica, trébol)
  card_painter.py             Frente: papel marfil (luz + grano), índices (Inter; J/Q/K en Playfair), palos en la
                              distribución clásica (PIPS), As ornamentado — vectorial (también lo usa el inicio)
  court_art.py                Figuras J/Q/K (diseño propio): panel con enrejado dorado, medallón con la letra
  court_emblems.py            Emblemas: corona (K), diadema (Q), escudo con estrella (J)
  card_back.py                Dorso: enrejado ámbar refinado + draw_back_foil (brillo aparte, según el foco)
  card_assets_base.py         Sprite (pixmap + offset + tamaño de carta) y lienzos en px físicos
  card_assets.py              CardAssets: sprites por tamaño de carta + DPR, a demanda: cartas con sombra (reposo y
                              levantadas), foil, lugares, resplandor, luz de victoria
  table_marks.py              Lugares hundidos en el paño (palo / K / reciclado), resplandor de destino, bloom ámbar
  table_painter.py            TablePainter: un frame (sólo copia sprites, px físicos, recortado a la región sucia;
                              estira los sprites mientras se redimensiona)
  table_motion.py             TableMotion: tweens (vuelo + giro simulado) y celebración; finish() = todo al final
  table_animations.py         Qué animar: diferencia de cartas visibles antes/después (vuela, gira, se reacomoda);
                              reparto escalonado
  drag_state.py               DragState (cartas levantadas ×1.03, destinos válidos), drop_targets, auto_foundation
                              (el As va a la fundación que muestra su palo), card_rect
  felt_backdrop.py            Fondo: paño de casino, foco cenital, viñeteado, sombra bajo la barra
  solitaire_style.py          QSS de la barra (Inter, principal ámbar, contorno sobre vidrio)
  solitaire_bar.py            SolitaireBar: modo de robo, estado, Deshacer, Nueva partida, Volver; esquina libre
  solitaire_view.py           Mesa: clic en mazo, arrastrar-soltar (update parcial), doble clic → changed; anima
  dialogs.py                  ChoiceDialog (GlassDialog): confirmación, victoria y "No quedan movimientos"
  solitaire_screen.py         deal(robo) + barra + paño cacheado; _after_change() reevalúa botones, victoria y traba
tests/                        pytest; conftest: raíz en sys.path, QT_QPA_PLATFORM=offscreen + QT_QPA_FONTDIR
                              (fuentes reales de Windows: si no, offscreen mide con otra fuente), fixture qapp
  fakes.py                    FakeEngine (lento/guionado, quit() interrumpe play(); analyse() con evaluaciones
                              guionadas; `options` con el rango de UCI_Elo y `config` como python-chess) + wait_until()
  test_stockfish_process.py   Stockfish REAL: el proceso muere al volver/cambiar/cerrar; opciones de cada nivel
                              (Club → Principiante → Máximo en el mismo proceso) (skip si no está)
  test_move_choice.py         Softmax con semilla (distribución), descuido en su rango y nunca mate en contra, caída
                              al softmax, ve lo obvio, candidatas ilegales/repetidas, punto de vista del que mueve
  test_engine_search.py       Opciones que no se heredan entre niveles, UCI_Elo ajustado al rango, Máximo = mejor,
                              jugada única sin buscar, menos candidatas que MultiPV, nunca una jugada ilegal
  test_klondike.py            Reglas del solitario (puras)
  test_klondike_undo.py       Deshacer de cada acción (incl. volteo) + abanico del descarte
  test_stuck_detector.py      Traba agotada y avance (incl. caso real: salida que exige devolver de la fundación),
                              robo de a 3. Fixtures dead_game / huge_dead_game (traba imposible de agotar)
  test_stuck_search_limits.py Corte por límite de nodos o de tiempo (no es traba), búsqueda por porciones
  test_solitaire_ui.py        Solitario con mouse/teclado simulados (QTest): sueltas, doble clic, modo,
                              victoria, Deshacer/Ctrl+Z
  test_solitaire_stuck_ui.py  Aviso de traba: 3 opciones, "Seguir mirando", sin aviso por límite, porciones y
                              pausa durante un arrastre
  test_rendering_cache.py     Arrastrar no regenera pixmaps; cambiar la escala sí (después del redimensionado)
  test_solitaire_look.py      Palos y distribución, todas las cartas se generan una vez, fundaciones con su palo,
                              As al lugar de su palo, animaciones que no hacen esperar, destinos marcados, victoria,
                              barra y avisos sin cortes
  test_home.py                Inicio: abrir/cerrar opciones (Esc, clic afuera/adentro), Jugar/Repartir con lo
                              elegido, sin Stockfish, hover sin regenerar, una sola regeneración al redimensionar
  test_layout_fit.py          Inicio de 800x600 a 1920x1080: textos, carteles de título y paneles abiertos sin
                              cortes
  test_fonts.py               Sólo las fuentes usadas (Playfair, Inter, Caveat), con licencia; pesos reales
  test_piece_art.py           Arte de Blender: archivos y tamaños, altos medidos y orden (rey > ... > peón), apoyo a
                              0,15 y rey dentro de su casilla, orden de dibujo (suelos -> reflejos -> coordenadas ->
                              cuerpos de atrás adelante), reflejos sin pisar el marco, tablero igual con negras,
                              levantada (x1,08, sin contacto, sombra lejos), halo/bloom, ícono de coronación,
                              carga diferida (proceso aparte: el inicio sólo lee cuerpos)
  test_chess_layout_fit.py    Mesa del ajedrez de 800x600 a 1920x1080: ningún objeto pisa a otro (el reloj tampoco al
                              cartel), ni al tablero, ni el volumen; textos dentro de placas, carteles, planilla
  test_table_layout.py        Disposición pura en 12 tamaños x 3 escalas: sin choques, bandejas centradas en su
                              mitad, casilla mínima; capturadas y material (coronación no es captura)
  test_table_objects.py       Planilla (hojas, rueda, RePág/AvPág), reloj (turno, luz, final), placas (Enter/Espacio,
                              deshabilitada, "Menú"), tarjeta (Esc/clic), rey acostado, perilla sólo en el ajedrez,
                              contraste WCAG (tinta, impreso, grabado en cada estado), pintar no genera pixmaps,
                              tablero = el render real sin el velo (board_glare) y con el brillo por código
  test_sound.py               Sonido de cada jugada, volumen que guarda sólo volumen+silencio, sin ráfagas, sin audio
  test_sound_hooks.py         Cada acción del ajedrez y del solitario dispara su sonido
  test_volume_control.py      Parlante (perilla en el ajedrez) en la misma esquina libre en todas las pantallas;
                              Esc/clic afuera; volumen
  test_about.py               Versión en un solo lugar, enlace del inicio y F1, créditos (también en CREDITS.md),
                              LICENSE completa, donaciones ocultas sin enlace, textos sin cortes a 3 escalas
  test_release.py             Nada personal en lo versionado (rutas C:\Users\…, metadatos de PNG), .env nunca
                              versionado, .env.example sólo con variables conocidas, nombre del zip con la versión
scripts/calibrar_dificultad.py Calibración: escalera de niveles (≥ 70 %) + anclas (azar, glotón, Stockfish 1320);
                              procesos según la memoria libre (deja 1,5 GB, máx. 4); tope de tiempo por tanda (--max-minutes). calibracion_partidas.py: jugadores
                              y una partida
scripts/crear_acceso_directo.ps1    Acceso directo (ícono + AppUserModelID). Lo ejecuta el usuario
scripts/generar_icono.py      Regenera assets/ desde icon_painter.py
scripts/generar_icono_blender.py    Ícono propuesto (--comparar: lámina viejo/nuevo en docs/screenshots/)
scripts/build_windows.py      Build reproducible: PyInstaller --onedir --windowed, poda de Qt, licencias/, LEEME, zip
                              versionado en dist/ (+ sha256) y prueba en carpeta limpia (probar_build.py)
scripts/probar_build.py       Descomprime el zip en %TEMP%, sin venv en el PATH: arranque x3 + --autoprueba; mira que
                              no quede ningún stockfish.exe de ESA carpeta (por ruta; sólo cierra lo que lanzó)
scripts/limpiar_metadatos_png.py    Saca tEXt/zTXt/iTXt/tIME de los PNG (Blender graba la ruta del .blend con el
                              usuario de la PC); los píxeles no cambian
```

### Ciclo de vida de las pantallas
`MainWindow.open_game(cls)` crea la pantalla nueva; volver al menú, cambiar de juego o cerrar la
ventana llaman a `game.shutdown()` y la destruyen (`deleteLater`). Todo recurso externo de un juego
(proceso de Stockfish, hilos) se libera en `shutdown()`, que debe ser idempotente.

### Pantalla de inicio ("mesa de juego", neón tenue)
- Dos mitades clickeables: ajedrez (tablero en perspectiva sobre madera muy oscura) | solitario (naipes
  y abanico sobre paño oscuro desaturado). Arriba al centro, ícono + "Mesa Trazada" (APP_NAME). Todo por código.
- Clic en una mitad → su `OptionsPanel` aparece sobre el dibujo (ajedrez: color + dificultad + "Jugar";
  solitario: robo + "Repartir"). Reemplaza las páginas intermedias de antes (no hay SetupPage/StartPage).
  Esc o clic afuera cierra (el clic afuera SÓLO cierra); Enter = botón principal. Las opciones elegidas
  se recuerdan mientras la app está abierta. Sin Stockfish: mensaje en el panel y "Jugar" deshabilitado.
- **Cartel del título** (nombre + detalle de cada mitad): rectángulo de esquinas apenas redondeadas,
  ajustado al texto con padding proporcional (`PLAQUE`), centrado en su mitad; relleno muy oscuro
  semitransparente y contorno ámbar casi apagado en reposo (va en el fondo estático). Su contorno
  encendido está en la capa "encendida" de la mitad: misma transición que el título, sin costo por frame.
- Hover: la mitad se aclara (luz de lámpara), se encienden el contorno neón del tablero/abanico y el del
  cartel, y sube el halo del nombre; la otra mitad se atenúa. `HoverFader` anima 0→1 en `MOTION.hover_ms`. Nada continuo.
- Sólo tokens de `common/theme.py`. Intensidades del neón en `NEON` (si se duda, bajar).
- **Tipografía** (`theme.TYPE`, fuentes embebidas; elegida por el usuario entre 3 variantes): títulos (nombre
  de la app y de cada juego) en Playfair Display SemiBold; subtítulos, rótulos y botones en Inter (Regular;
  SemiBold el botón principal). Nada de Light/Thin (el neón los emborrona). Los juegos siguen con
  `TYPE.games_family` (Segoe UI) hasta que hereden los tokens.
- **Rendimiento**: `HomeLayers.build` pre-renderiza todo (fondo opaco con texturas, dibujos, sombras y
  viñeteado y carteles; por mitad la capa "encendida" = luz + contornos; halos; textos; divisoria; encabezado) por
  (tamaño, DPR). El frame sólo copia pixmaps con opacidad + un `fillRect` semitransparente. Al
  redimensionar se estira la última versión y se regenera `MOTION.rebuild_ms` después del último cambio.
  Brillos: desenfoque pirámide UNA vez por tamaño (nunca QGraphicsBlurEffect por frame).
- Medido (plataforma Windows real, hover): pintado mediana 0,7–3,6 ms, p95 ≤ 6,3 ms; frames cada
  ~16 ms (60 fps) a 100/125/150 %, en 1000x720 y maximizada. Regenerar: 31–65 ms a 1000x720,
  62–142 ms maximizada (una vez, al terminar de redimensionar; varía con la carga de la máquina).

### Ajedrez: aspecto (arte de Blender + marcas por código, todo pre-renderizado)
- Tablero, piezas y mesa: renders de Blender (Cycles) en `assets/ajedrez/`; `blender/INTEGRACION.md` da escala,
  apoyos, orden y medidas; se regeneran con `blender/generar_ajedrez.py` (`export_all()`). Por código: coordenadas
  (Inter, dentro de las casillas, con halo del color de su casilla para leerse sobre las sombras), tintes ámbar
  (última jugada, elegida), jaque, puntos/anillos de las legales, halo + bloom de la elegida, lámpara, viñeteado.
- Tablero: el velo del brillo de la lámpara que trae el render en b6-b7 (aclaraba pero agrisaba: se veía como una
  mancha oscura) se resta al cargar (`board_glare`, ~30 ms) y se reemplaza por un brillo claro en modo Screen
  (`BOARD_LOOK.gloss`, arriba a la izquierda). `tablero.png` escalado por `s / 243,81` (s = lado de la casilla en
  px físicos) y ubicado para que sus casillas caigan en la grilla entera de `BoardGeometry` (error <= 1 px). Con
  negras la imagen es la misma.
  Coordenadas: números arriba a la izquierda en la columna de la izquierda, letras abajo a la derecha en la fila
  de abajo (de la vista); van como imágenes aparte, DESPUÉS de sombras y reflejos (la sombra de la fila de abajo
  cae justo sobre las letras).
- Piezas: escala `s x BOARD_LOOK.piece_scale / 426,67` (1,10: el rey ~0,89 de la casilla, ver Trampas), apoyo
  (256; 445,4) centrado y a 0,15 s del borde inferior de la casilla. Frame:
  suelos (contacto + sombra: negro sobre negro, el orden entre piezas no cambia nada) -> reflejos (recortados a
  las 8 x 8 casillas) -> coordenadas -> cuerpos (pieza + brillo horneados juntos: la pieza de adelante tapa el
  brillo de la de atrás) de la fila de atrás a la de adelante -> legales -> pieza levantada. ~3 copias por pieza.
- Levantada: x1,08 re-escalada desde el render, sin contacto, sombra corrida/difusa/más clara, reflejo separado y
  a la mitad (`PIECE_LOOK`). Reflejos al 60 % del horneado (`BOARD_LOOK.reflection`). En su casilla queda sólo
  el cuerpo al 25 %. Elegida: halo ámbar de la silueta
  (debajo) + bloom ámbar del brillo sumado en modo Plus (encima). En las blancas el bloom solo no se ve (sus
  brillos ya son casi blancos): por eso el halo.
- Fondo: `mesa.png` centrada en el tablero (no en la ventana: la columna lo corre), escala máx(`s / 240`, la mínima
  para cubrir la ventana desde ese centro) + charco de luz (`table_light*`) + sombra del tablero + viñeteado.
- Carga (`art_library`): al arrancar sólo los cuerpos que dibuja el inicio (~2,3 ms c/u); el resto (~340 ms) se
  precarga en un hilo al abrir las opciones del ajedrez, y `library()` espera o carga al abrir el ajedrez. Los
  originales quedan en memoria (~125 MB) para re-escalar al redimensionar.
- Rendimiento: `BoardAssets` guarda la imagen del tablero y los sprites por tamaño de casilla + DPR (a demanda;
  arrastrar no genera nada salvo, una vez por pieza, la levantada). Frame en px físicos. Al redimensionar se
  estira lo anterior y se regenera `MOTION.rebuild_ms` después (igual el fondo, `CachedBackdrop`).
- Medido (plataforma Windows real, arrastrando con eventos cada 4 ms; 2026-10-23): pintado del tablero mediana
  0,56-0,61 ms, p95 <= 0,79 ms, máx <= 1,6 ms; un frame por evento (~250/s) a 100/125/150 %, en 1000x720 y
  maximizada. Frame completo maximizado (tras cada jugada) mediana 1,9 ms. Generar un tamaño: tablero 6-10 ms +
  12 piezas 18-21 ms; fondo ~19 ms; cargar el arte ~340 ms (una vez).
- Disposición: ver "la mesa de la partida" (`table_layout`): todo se mide en casillas y escala con el tablero.

### Sonido y volumen
- `QSoundEffect` (baja latencia, asincrónico) con un efecto por sonido: si se pide de nuevo mientras suena
  vuelve a empezar (nunca dos copias) y `MIN_GAP` evita ráfagas. Se carga después de mostrar la ventana
  (`main._start_sound`); sin QtMultimedia, sin dispositivo o sin archivo: sigue mudo y lo loguea.
- Ajedrez (`move_sound`): jaque > coronar > enroque > captura > mover; el final (`end_sound`: ganar o
  perder/tablas) llega `END_DELAY_MS` después. Solitario (`SolitaireView._draw/_move`): robar o reciclar,
  apoyar o fundación, voltear (`FLIP_DELAY_MS` después) y en la pantalla repartir y victoria.
- Volumen global único (`sound.volume()`); `main.py` instala uno con `QSettings` (registro del usuario) que
  guarda SÓLO `audio/volume` y `audio/muted`. En tests es en memoria (no tocan el registro).
- Control: `VolumeControl` (hijo de MainWindow, siempre encima) en la esquina superior derecha; el ajedrez y
  el solitario le dejan libre esa esquina (`CORNER`). Mover el deslizador saca el silencio. En el ajedrez el
  botón usa la "piel" de la pantalla (`ChessTable.volume_skin`: perilla de latón con la marca del nivel); la pone
  y la saca `MainWindow` al abrir/cerrar cada juego.

### Solitario: aspecto (mesa de casino, todo pre-renderizado)
- Distribución clásica: mazo y descarte arriba a la izquierda, 4 fundaciones arriba a la derecha, 7 columnas.
  Boca abajo con escalón chico (`DOWN_OFFSET` 0,10), boca arriba con más (`UP_OFFSET` 0,28: el índice entero).
- Paño de casino profundo (`felt_table*`) con grano de fibra, foco cenital sobre el centro de la mesa, viñeteado
  y sombra bajo la barra. Lugares vacíos = un leve hundido (sombra interior arriba a la izquierda, filo de luz
  abajo a la derecha). Fundaciones vacías con el palo de un As que FALTA (orden ♥ ♣ ♦ ♠; la regla no cambió:
  cualquier As va a cualquier fundación vacía); con doble clic el As va a la que muestra su palo.
- Cartas: papel marfil con grano y la luz de la app (arriba a la izquierda), sombra de contacto + proyectada
  (cada carta sombrea a la de abajo en las columnas). Figuras J/Q/K de diseño propio. Dorso: enrejado ámbar con
  foil que brilla según cuánto le llega el foco (opacidad por posición). Tokens: `CARD_LOOK`, colores `paper*`,
  `card_gold*`.
- Arrastre: la carta se levanta (×1.03, sombra más lejos y difusa) y los destinos válidos se marcan con un
  resplandor ámbar. Animaciones (`table_motion`): reparto, giro de la carta destapada, vuelo a la fundación
  (doble clic), reacomodo del descarte, robar/reciclar, suelta que se acomoda o vuelve, luz de la victoria.
  REGLA: la partida ya está en su estado final cuando la animación empieza; cualquier clic, Deshacer o partida
  nueva llama a `motion.finish()` y todo queda en su lugar al instante.
- Rendimiento: `CardAssets` por tamaño de carta + DPR (a demanda; arrastrar no genera nada salvo, una vez, las
  versiones levantadas y el resplandor). El frame sólo copia sprites en px físicos; el paño lo cachea
  `CachedBackdrop`. Medido en plataforma Windows real a 100/125/150 %, 1000x720 y maximizada: arrastrar 12
  cartas, pintado mediana 0,76–0,93 ms, p95 ≤ 1,21 ms (un frame por evento, ~250/s); reparto animado
  mediana 1,7–2,2 ms, p95 ≤ 4,4 ms, un frame cada 16 ms (~62 fps) durante los ~0,8 s que dura.

### Solitario
- La UI nunca modifica el estado directo: consulta `movable_cards` / `can_move` y aplica con `move` /
  `draw`. Durante un arrastre no se toca el modelo; si la suelta no es válida simplemente se repinta.
- Fundaciones: 4 lugares; cualquier As va a uno vacío y ese lugar queda para su palo.
- "Partida en curso" (para pedir confirmación al cambiar el modo) = `game.actions > 0` y no ganada.
  Recién repartida, cambiar de modo reparte de nuevo sin preguntar.
- Descarte: siempre se ven las últimas 3 cartas en abanico (`WASTE_VISIBLE`), en los dos modos; sólo
  la de arriba se juega.
- **Deshacer**: `KlondikeGame` guarda un `GameState` antes de cada `move`/`draw` (incluye reciclados y
  dobles clics, que son `move`). `undo()` restaura el último: así una carta volteada automáticamente
  vuelve boca abajo sin lógica inversa. Ilimitado hasta el reparto. Deshabilitado sin historial o ganada.
- **Aviso "No quedan movimientos" = búsqueda acotada, no heurística** (reemplazó a una regla fija que dio
  un falso positivo: la única salida empezaba devolviendo el 9♣ de la fundación).
  - `StuckSearch` recorre en anchura, sobre una copia codificada (no muta la partida), TODOS los estados
    alcanzables con jugadas legales: entre columnas (también parciales), del mazo a columna o fundación,
    devoluciones desde la fundación y el ciclo del mazo según el modo de robo. Estados repetidos: hash.
  - **Avance** = un estado con más cartas en fundación que ahora o con una carta boca abajo destapada.
  - **Conservador**: avisa SÓLO si agotó los estados sin avance (STUCK). Si corta por límite
    (`MAX_NODES` = 20 000 o `MAX_SECONDS` = 0,5 s de cálculo) el resultado es LIMIT y NO se avisa.
    STUCK es una prueba: la partida está perdida (ganar exige subir cartas).
  - Reducciones, todas exactas: (1) robar/reciclar no son estados: desde cada estado se puede jugar toda
    carta que el mazo deje arriba (robo de a 1: todas; de a 3: topes de tanda de la pasada en curso + del
    ciclo principal tras reciclar; puntero canónico `MAIN`); (2) columnas sin cartas boca abajo son
    intercambiables y se guardan ordenadas; (3) `search_moves._useful` poda devoluciones que no pueden
    servir: una carta devuelta sólo sirve de base para una de un valor menos y otro color, o para poder
    devolver la de abajo de su palo; si todas esas están boca abajo o en fundación sin servir a su vez,
    nada de afuera puede terminar encima, y quitar esas jugadas de cualquier camino con salida lo deja
    válido. Bajó el peor caso medido de 162 000 a 9 300 estados.
  - Validado (scripts descartables): 0 diferencias contra una fuerza bruta sobre `KlondikeGame` real
    (cada robo un estado, sin reducciones) en ~1 100 posiciones no triviales, y con/sin la poda en
    ~29 000 posiciones de partidas simuladas.
  - UI (`StuckWatcher`): la primera porción (10 ms) corre en el acto y resuelve el 99 % de los casos; el
    resto sigue con `QTimer(0)` entre eventos. Durante un arrastre se pausa (no abre el aviso en medio).
    Cada cambio cancela la búsqueda anterior; `shutdown()` también.
- "Seguir mirando": no se vuelve a avisar mientras `board_key` (columnas + fundaciones) no cambie.
  Robar o reciclar no lo cambia (recorrer el mazo no re-avisa); mover o deshacer un movimiento, sí.

### Rendimiento del pintado
- Nunca dibujar cartas ni piezas vectoriales en cada frame: se renderizan una vez por escala en
  `PixmapCache` y se copian. Al arrastrar se invalida sólo la unión de la posición vieja y la nueva.
- Medido en esta máquina (DPR 1.0), mediana por frame, antes → después: arrastrar 1 carta 20.7 → 0.8 ms;
  12 cartas 46.4 → 0.8 ms; redimensionar 69 → 10.6 ms (el pintado es 0.8 ms; el resto es Qt reacomodando
  la ventana); pieza de ajedrez 11.4 → 1.1 ms.
- Causas reales (cProfile): el dorso dibujaba ~60 líneas antialias por carta (0.64 ms c/u, 22 por frame);
  en ajedrez, rellenar los glifos de las piezas era el 81 % del frame.
- Chequeo de traba (≈38 000 posiciones de 400 partidas simuladas): mediana 0,03 ms, p99 ≈ 9 ms, peor
  ≈ 0,5 s (= límite). En la app real (plataforma Windows) el bucle de eventos se frenó como máximo 29 ms
  durante las búsquedas más pesadas (porciones de 10 ms + pausas del GC de Python).
- Pantalla de inicio y tablero de ajedrez: ver sus secciones (sprites pre-renderizados; frame en píxeles
  físicos). El tablero ya no usa `PixmapCache` sino `BoardAssets` (las cifras de arriba son de la versión
  anterior con glifos).

### Dificultad: calibración (2026-10-23, semilla 1, valores del .env)
| Emparejamiento | Partidas | G-E-P | % | Dif. Elo [IC 95 %] |
|---|---|---|---|---|
| Novato vs Principiante | 80 | 64-6-10 | 83,8 | +285 [+203, +407] |
| Aficionado vs Novato | 80 | 73-0-7 | 91,2 | +407 [+302, +632] |
| Club vs Aficionado | 20 | 19-0-1 | 95,0 | +512 [+308, +636] |
| Avanzado vs Club | 20 | 18-0-2 | 90,0 | +382 [+208, +636] |
| Principiante vs azar (ancla) | 80 | 80-0-0 | 100 | — |
| Principiante vs glotón (ancla) | 80 | 37-40-3 | 71,2 | +158 [+108, +214] |
| Novato vs Stockfish 1320 a 0,3 s (ancla) | 24 | 0-0-24 | 0 | ≤ −669 |
| Aficionado vs Stockfish 1320 a 0,3 s (ancla) | 24 | 0-1-23 | 2,1 | ≤ −476 |
- Criterio del usuario: Principiante le gana claro al azar y le gana al glotón SIN aplastarlo (si lo aplasta, es
  demasiado fuerte para un principiante real); la escalera ≥ 70 %; las anclas de Stockfish sólo se informan.
- Lo que mueve la fuerza: la PROFUNDIDAD pesa mucho (1 → 2 → 3 son saltos grandes) y el ruido (TEMP, BLUNDER) ajusta
  dentro de cada profundidad. Con poco ruido y profundidad 3-4 el modo humano ya le gana a Club a 0,3 s.
- La escala no es lisa: entre Novato y Stockfish 1320 a 0,3 s hay > 900 Elo con un solo nivel en el medio. Se
  eligió Aficionado ~400 sobre Novato y ≥ 500 bajo Club (el reparto más parejo encontrado).
- MultiPV 20 en Principiante lo dejaba casi parejo con el glotón (57 %): más candidatas = más jugadas malas.
- Las corridas con la misma semilla dan exactamente lo mismo (verificado con los niveles humanos).

### Ajedrez: la mesa de la partida (objetos de Blender + texto por código)
- La interfaz no es un panel: son objetos apoyados en la mesa, renderizados con la misma luz que el tablero
  (`blender/generar_interfaz.py`, `assets/ajedrez/interfaz/`, anclas en `interfaz.json`). Disposición (en casillas,
  `TABLE_LOOK`, función pura `table_layout`): tablero | bandejas de capturadas (cada una de 3 casillas, centrada en
  su mitad del tablero; la del rival, tus piezas perdidas, desde arriba; la tuya desde abajo) | columna: cartel del
  rival, reloj, planilla (lo que sobra), tu cartel, "Nueva partida", "Deshacer" + "Menú". El conjunto queda centrado;
  la esquina del volumen, libre. Casilla: 55 px en 800x600, 69 en 1000x720, 109 maximizada.
- Cada objeto es un widget del tamaño EXACTO de su objeto (`Placed`): su sombra y su contacto van horneados en el
  fondo cacheado (`TableSide.shadow_layers` → `render_backdrop`), así los márgenes no se pisan ni roban clics. La
  placa apretada usa su cuerpo `_pressed`; `_sombra_pressed` queda sin uso (la diferencia es de 1-2 px).
- En el render: los objetos vacíos y sus estados. En código: todo el texto (jugadas en Caveat 500 ≥ 13 px y tinta
  azul-negra, encabezados impresos en Inter, carteles y placas grabados: oscuro + filo de luz debajo), el resaltador
  de la última jugada, la luz ámbar del reloj, el "+N", la tarjeta, la marca de la perilla, el filete de foco.
- Estados de la partida: reloj = turno (el que acaba de mover tiene su botón hundido) y luz del lado de Stockfish
  mientras piensa (reemplaza "Stockfish está pensando…", que queda como tooltip/descripción accesible); fin =
  botones parejos + resultado escrito en la planilla ("1–0 · Jaque mate") + tarjeta sobre la planilla (clic o Esc
  la levanta) + con jaque mate el rey vencido se acuesta (`BoardView.toppled`). Sin motor o si falla: tarjeta (y el
  diálogo de error si falla en medio de la partida).
- Planilla: hojas de `filas` (10) renglones; siempre se ve la última; rueda del mouse o RePág/AvPág (con foco) para
  mirar las anteriores; "Hoja n de m" al pie. No se puede hacer clic en una jugada (no estaba antes).
- Accesibilidad (medido en `test_table_objects`): tinta/papel 11,3:1, impreso 6,4:1, grabado sobre latón y bronce
  ≥ 4,6:1 en normal/hover/apretada, deshabilitada ≥ 3,4:1 (texto opaco: la placa gris ya lo dice). Placas con Tab,
  Enter y Espacio; filete de foco oscuro grabado (el ámbar sobre latón no se veía).
- Carga: los 48 PNG de la interfaz entran en la misma precarga (`ArtLibrary`, ~530 ms en total, en otro hilo); el
  inicio no los carga. ~7,7 MB en el repo.
- Medido (plataforma Windows real, 100/125/150 %, 1000x720 y maximizada): arrastre mediana 0,53-0,59 ms, p95 ≤ 0,86
  (igual que antes); repintado completo 1,9-4,1 ms; repintado tras una jugada (tablero + planilla + reloj + bandejas)
  3,5-7,3 ms; regenerar todo para un tamaño nuevo (fondo con sombras + sprites) 12-35 ms, una vez.

### Lanzamiento (build de Windows, licencias, privacidad)
- Build: `scripts/build_windows.py` → `build/app/MesaTrazada/` (no versionado) y
  `dist/MesaTrazada-<versión>-windows-x64.zip`. Modo carpeta, no onefile (arranque y antivirus: ver
  docs/TECNICO.md). Poda: Qt6Pdf, TLS + OpenSSL de Qt, networkinformation y FFmpeg (QSoundEffect suena con el backend
  windowsmediaplugin; la prueba de humo verifica `isPlaying`). Medido 2026-10-23: carpeta 192 MB, zip 132 MB; arranque
  hasta la ventana 1,3 s recién descomprimido, 0,46 s después; prueba de humo completa ~29 s, OK.
- Recursos en el build: `sys._MEIPASS` = `_internal/`; los módulos ubican assets con `Path(__file__)` y funcionan
  igual. `.env` y `licencias/` van junto al .exe (`paths.install_dir`); el log a %LOCALAPPDATA%.
- Donaciones y repositorio: `app_info.DONATIONS` / `SOURCE_URL` vacíos (TODO del usuario: sin cuentas todavía).
- Privacidad (auditoría 2026-10-23): sin secretos ni .env en la historia. En la historia SÍ quedan: el mail de los
  commits, el usuario de Windows en rutas de CLAUDE.md, en los metadatos de 36 PNG (todas sus versiones) y en el .blend
  de dd4d5ba. El árbol de trabajo ya está limpio (PNG, .blend, CLAUDE.md); la historia NO se reescribió: el usuario
  eligió publicar un repo nuevo con un único commit (`../MesaTrazada`). Cambios futuros: hacerlos acá y llevarlos allá.

### Motor (ajedrez)
- **Niveles** (`difficulty.py`, parámetros en `.env`, tabla en el README): Principiante, Novato y Aficionado =
  modo humano propio (`UCI_Elo` de Stockfish 19 no baja de 1320); Club y Avanzado = `UCI_LimitStrength` +
  `UCI_Elo` (ajustado al rango que reporta el motor, nunca hardcodeado); Máximo = sin límite. Skill Level
  queda siempre en 20: no se usa para debilitar (se equivoca de forma poco humana).
- **Modo humano** (`move_choice`): `analyse(depth, multipv)` → pérdidas respecto de la mejor (mates = ±10 000,
  tope 1000 en el softmax). (1) mate en 1 o captura que le saca `OBVIOUS_CP` a la 2.ª: la juega con prob.
  `obvious`; (2) descuido con prob. `blunder`: una candidata en [min, max] cp, nunca mate en contra, peso
  1/pérdida; si no hay ninguna en el rango, sigue al softmax; (3) softmax exp(−pérdida/T). Sólo candidatas
  del motor (nunca una jugada al azar). PV ilegal/vacío se descarta; sin candidatas, `play()` a esa profundidad.
- **Opciones por jugada**: `configure_for` fija SIEMPRE `UCI_LimitStrength`, `UCI_Elo` y `Skill Level` (el mismo
  proceso pasa de Club a Principiante sin heredar nada). `MultiPV` lo maneja python-chess (ver Trampas).
- **Ritmo humano**: `EngineController` retiene la jugada hasta `ENGINE_MIN_REPLY` (0,6 s) desde el pedido, con un
  `QTimer` (PreciseTimer) que `cancel()`, un pedido nuevo, `failed` y `shutdown()` paran. Mientras tanto
  `is_thinking` sigue en True. En los tests un fixture autouse lo pone en 0 (`test_engine_controller` lo prueba).
- **Reproducibilidad**: la app NO es determinista a propósito (RNG sin semilla; la tabla hash se comparte entre
  partidas del mismo proceso porque python-chess sólo manda `ucinewgame` en la primera). Sólo la calibración lo
  es: cada partida abre sus propios Stockfish (Threads=1, Hash=16, tabla limpia) y cada jugador tiene un RNG con
  semilla; los niveles por tiempo (Club, Avanzado, sf1320) igual dependen de la carga de la máquina.
- `EngineController.request_move` incrementa `_request_id`; `cancel()` lo vuelve a incrementar.
  `_on_move_found` descarta toda jugada cuyo id no sea el vigente. `ChessScreen._on_engine_move` además
  verifica que sea el turno del motor y que la jugada sea legal (doble defensa).
- "Deshacer" y "Nueva partida" llaman a `cancel()`. La búsqueda vieja termina sola (≤ tiempo por jugada)
  y su resultado se descarta; los pedidos se serializan en el hilo del worker.
- `shutdown()`: `worker.shutdown()` desde el hilo UI (`quit()` interrumpe la búsqueda; `close()` mata el
  proceso si hiciera falta) → `thread.quit()` → `thread.wait()`. También conectado a `aboutToQuit`.

## Cómo correr
```
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe scripts\generar_icono.py      # si cambia icon_painter.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\crear_acceso_directo.ps1
```

## Estado actual
- [x] Fase 0 — Setup: venv, deps, Stockfish 19 verificado (`uciok`), estructura, config, logging.
- [x] Fase 1 — Esqueleto + acceso directo. Verificado con pythonw.exe real (cierre limpio, error de
  arranque logueado con diálogo).
- [x] Identidad visual: ícono propio (.ico 16–256 + PNG), ícono de ventana, AppUserModelID en proceso y
  en el .lnk, tema con acento ámbar.
- [x] Fase 2 — Ajedrez completo. 51 tests. Verificado con pythonw real: Stockfish sin ventana de consola;
  muere al cerrar la ventana (pensando en Difícil) y también si la app se mata con `taskkill /F`.
- [x] Fase 3 — Solitario Klondike completo. Verificado en plataforma Windows real (no sólo offscreen).
- [x] Correcciones del solitario: aviso de traba, rendimiento (caché de pixmaps + repintado parcial,
  también en el tablero de ajedrez), descarte de 3 en ambos modos, Deshacer ilimitado con Ctrl+Z.
- [x] Aviso de traba por búsqueda acotada y conservadora (corrige el falso positivo con devolución desde
  la fundación).
- [x] Textos cortados: radios de "Modo de robo" (y el mismo bug latente en la config. del ajedrez).
  Revisadas todas las pantallas y diálogos a 100/125/150 % y en ventana 1000x720 y 800x600.
- [x] Pantalla de inicio "mesa de juego" + tokens de diseño (`common/theme.py`). Las opciones de arranque
  están en el inicio (sin páginas intermedias). Los juegos todavía no usan los tokens directo (siguiente
  paso, a pedido del usuario).
- [x] Git: commit 1 "Versión funcional…" (reescrito para sacar las capturas: el repo no tiene imágenes salvo
  el ícono; sin .env, engine/, .venv/, logs). Las capturas de revisión quedan en disco, ignoradas.
- [x] Tipografía Playfair Display + Inter (embebidas) y carteles de título con neón (commit 2).
- [x] Rediseño visual del ajedrez (pizarra, piezas Staunton propias con luz única, sombras, reflejos,
  elevación, neón ámbar), panel y diálogos con los tokens, fondo de madera; sonidos (Kenney CC0) en los dos
  juegos y control de volumen global. Ajuste de las negras (carbón cálido, luz de borde continua, brillos
  amplios) y piezas más grandes (commit 061c51d).
- [x] Rediseño visual del solitario (mesa de casino, cartas y figuras propias, sombras, foil, animaciones que no
  hacen esperar, destinos marcados, victoria con luz ámbar; barra y avisos con los tokens). SIN COMMITEAR hasta
  que el usuario confirme.

- [x] Dificultad del ajedrez: 6 niveles (Principiante … Máximo), modo humano propio para los bajos, UCI_Elo para
  Club/Avanzado, ritmo humano (0,6 s), selección en el inicio (2 filas de 3), calibrada con
  `scripts/calibrar_dificultad.py` (commit 4c6d9df).

- [x] Arte de Blender en el ajedrez (tablero, piezas, mesa; carga diferida; halo + bloom de la elegida;
  coordenadas sobre las sombras). Capturas de revisión en `docs/screenshots/blender_*.png` (commit dd4d5ba).

- [x] Ajustes finos: piezas x1,10 (`piece_scale`), velo del render en b6-b7 reemplazado por un brillo claro,
  reflejos al 60 % (commit 775b072).
- [x] Mesa de la partida: la interfaz del ajedrez son objetos de Blender apoyados en la mesa (planilla, reloj,
  bandejas, carteles, placas, tarjeta, perilla); Caveat embebida; "Menú". Capturas `docs/screenshots/mesa_*.png`.
  SIN COMMITEAR hasta que el usuario lo revise.

- [x] Lanzamiento 1.0.0 como **Mesa Trazada** (local, NADA publicado): auditoría de privacidad, LICENSE GPLv3 +
  CREDITS.md, "Acerca de" (F1), versión y donaciones en app_info, build PyInstaller + zip + prueba en carpeta limpia,
  ícono, README público + docs/TECNICO.md, textos de itch.io. Datos con el nombre anterior (carpeta de
  %LOCALAPPDATA% y volumen del registro) se migran una vez. El repo público es OTRO: `../MesaTrazada` (un único commit
  "Mesa Trazada 1.0.0", autor con el mail noreply de GitHub, sin remoto); este repo queda con su historia.

**299 tests.** Pendiente: que el usuario juegue contra Principiante; cuentas de donación y URL del repositorio
(`app_info`); crear el remoto y publicar (lo hace el usuario).

Fuera de alcance: guardar partidas, estadísticas, reloj, pistas, evaluación en vivo, .exe.

## Convenciones
- snake_case archivos/funciones, PascalCase clases; archivos de ~150 líneas máx.
- Config: `.env` + `Settings` en `config.py`. Nada de rutas ni parámetros de dificultad hardcodeados.
- Logging: `[%(asctime)s] %(levelname)s - %(name)s: %(message)s` a consola y `logs/app.log`; `logger = logging.getLogger(__name__)` por módulo.
- Tokens de diseño (colores, tipografía, espaciado, radios, botones, neón, tiempos) SÓLO desde
  `src/common/theme.py`. `src/app/palette.py` es un alias temporal para los juegos. Estilos de widgets vía
  `objectName` + QSS (`src/app/stylesheet.py` global; `common/qss.py` para generarlos desde tokens).
- Cada dependencia nueva va inmediatamente a `requirements.txt` pinneada.
- Fuentes: sólo embebidas en `assets/fonts/<Familia>/` con su licencia (OFL), cargadas con `load_fonts()`;
  nunca depender de lo instalado en la PC.
- Sin alturas fijas en píxeles para widgets con texto: que el layout calcule el alto según el contenido.
- **Al probar la app, cerrar SÓLO los procesos lanzados por uno mismo, por su PID.** Nunca cierres ni
  señales por nombre de proceso o título de ventana: en esta PC corren otras apps PyQt como pythonw.exe
  (otras apps del usuario).
- Trabajo por fases: al cerrar cada una, tests + actualizar este archivo + esperar confirmación del usuario.

## Trampas conocidas
- **pythonw.exe**: `sys.stderr`/`sys.stdout` son `None`. `setup_logging` sólo agrega StreamHandler si hay stderr. No usar `print` en código de la app.
- **python-chess**: el paquete PyPI `python-chess` es un shim (1.999) que instala `chess`. En requirements se pinnea `chess` directamente.
- **python-chess NO pasa `CREATE_NO_WINDOW`**: sin `creationflags=subprocess.CREATE_NO_WINDOW` (en `open_stockfish`), desde pythonw aparece una consola de Stockfish. Queda un `conhost.exe` hijo sin ventana: es normal.
- **Tablas reclamables**: NO usar `board.outcome(claim_draw=True)`: también "reclama" si alguna jugada *posible* llevaría a triple repetición / 50 movimientos. `ChessGame.result()` usa `is_repetition(3)` y `halfmove_clock >= 100`.
- **QThread vivo al destruir** = abort del proceso ("QThread: Destroyed while thread is still running"). Toda ChessScreen debe pasar por `shutdown()`. En tests, si se espía `shutdown`, llamar al original.
- **SimpleEngine es thread-safe** (`run_coroutine_threadsafe`): `quit()`/`close()` se llaman desde el hilo UI aunque el worker esté bloqueado en `play()`; esa búsqueda termina con `EngineTerminatedError`, que el worker ignora si está cerrando.
- Si la app muere a la fuerza, Stockfish termina solo al cerrarse su stdin (verificado con `taskkill /F`).
- **MultiPV es una opción "manejada" de python-chess**: `configure({"MultiPV": ...})` tira EngineError.
  `play()` la vuelve al default (1) y `analyse(multipv=k)` la fija; lo enviado se ve en `engine.protocol.config`.
  `_setoption` sólo manda lo que cambió respecto de esa config.
- **`ucinewgame`**: python-chess lo manda en la primera búsqueda o si cambia el argumento `game=`; la app no lo
  pasa (no hace falta: no es determinista).
- **Memoria al calibrar**: con Blender/Chrome abiertos, 12 procesos (2 Stockfish c/u) dejaron a la PC sin memoria
  y Claude Code cortó la corrida. El script calcula los procesos con `GlobalMemoryStatusEx` (deja `MIN_FREE_GB` = 1,5 GB,
  máx. 4; sin lugar para un proceso, vuelve a medir cada 60 s hasta 5 veces).
- **Stockfish 19** sólo publica builds "universal" (dispatch en runtime). En esta máquina (i7-13620H) elige `x86-64-avxvnni`. Pesa ~100 MB (NNUE embebida); la carga tarda un instante y se hace en el worker.
- Rutas: el acceso directo puede lanzar con cualquier cwd; `config._resolve` ancla rutas relativas a `PROJECT_ROOT`.
- **PyQt6 + excepciones en slots**: con el `sys.excepthook` por defecto, una excepción no capturada en un slot aborta la app (qFatal). `main.py` instala `_log_uncaught`.
- **Imports en main.py**: `config` y PyQt6 se importan dentro de `_run()` a propósito (errores de arranque al log). No moverlos arriba.
- **AppUserModelID** `JScandizzo.MesaTrazada`: se fija antes de crear QApplication y debe coincidir con el del `.lnk` (test `test_shortcut_script_uses_same_app_id`). WScript.Shell no puede grabarlo: el .ps1 usa IPropertyStore vía Add-Type.
- **Venv en Windows**: `.venv\Scripts\pythonw.exe` es un lanzador que crea un segundo proceso. Ver 2 procesos es normal; el que lanza Stockfish es el hijo.
- **Escritorio redirigido a la nube**: usar `[Environment]::GetFolderPath('Desktop')`.
- **.ps1 con acentos**: guardar con BOM UTF-8; PowerShell 5.1 lee sin BOM como ANSI.
- **Caché de íconos de Windows**: tras cambiar el .ico, `ie4uinit.exe -show`; si no alcanza, reiniciar el Explorador.
- **Capturas offscreen**: `QT_QPA_PLATFORM=offscreen` + `QT_QPA_FONTDIR=C:/Windows/Fonts`; el tema fija Segoe UI.
- **Doble clic en el mazo**: Qt reemplaza el 2.º clic por `mouseDoubleClickEvent`; si no se trata como
  otro robo, dos clics rápidos roban una sola vez. `SolitaireView.mouseDoubleClickEvent` lo maneja.
- **Repintado parcial**: si algo nuevo cambia durante un arrastre (además de las cartas/pieza), hay que
  invalidar también su región o queda basura en pantalla. Al EMPEZAR y TERMINAR un arrastre se hace
  `update()` completo. `DIRTY_MARGIN` cubre el redondeo de posiciones de los pixmaps.
- **`WA_OpaquePaintEvent`** en `SolitaireView`: Qt no borra el fondo, `paintEvent` lo pinta. No quitar el
  `fillRect` inicial.
- **Caché y escala**: `PixmapCache.set_scale` (cartas) vacía todo al cambiar tamaño de carta o DPR;
  `BoardAssets` (ajedrez) se reemplaza entero al cambiar geometría o DPR. Si se cambia el dibujo de una carta
  o pieza en caliente, hay que vaciar la caché (`piece_painter._bounds` además tiene `lru_cache`).
- **Tests con `repaint()` en offscreen**: tras `show()`/cambio de página hace falta `QTest.qWait(...)` para
  que el widget quede expuesto; si no, `repaint()` no pinta.
- **Botones de QMessageBox**: el diálogo se oculta ANTES de que corra el slot conectado a `clicked`; por eso
  "Deshacer" desde el aviso de traba puede volver a avisar enseguida si la posición sigue trabada.
- **Búsqueda de traba = copia del reglamento**: `search_moves.successors` reimplementa las reglas de
  `klondike.py`/`rules.py` sobre enteros. Si cambia una regla, cambiar las dos y revalidar contra una
  fuerza bruta (BFS sobre `KlondikeGame` real con `snapshot.take/restore`, robo como estado). Igual si se
  toca `_useful` o la codificación: una poda mal hecha da falsos avisos.
- **Pausas del GC de Python**: con muchos objetos vivos, una recolección completa puede tardar >100 ms
  (se vio en benchmarks que guardaban miles de posiciones). En la app, ~20 ms. Al medir porciones, medir
  dentro de la app, no en un script que acumula datos.
- **Tests de la búsqueda por porciones**: `stuck_watcher.SLICE_SECONDS = 0` hace un estado por porción
  (fuerza el camino asíncrono); los límites de `stuck_detector` se leen al crear la búsqueda, así que
  `monkeypatch` de `MAX_NODES`/`MAX_SECONDS` funciona.
- **`AlignHCenter` + texto con ajuste de línea = texto cortado**: al agregar a un QBoxLayout un widget con
  alineación, Qt calcula su alto (heightForWidth) para el ancho COMPLETO del layout pero lo dibuja a su
  ancho preferido; si un QLabel con `setWordWrap` ocupa más renglones a ese ancho, el resto se comprime
  (así se cortaban los radios de "Modo de robo"). Centrar con espaciadores, o (como el panel de opciones
  del inicio) fijar el ancho y pedir `totalHeightForWidth(ancho)`. Escalas: `QT_SCALE_FACTOR=1.25` / `1.5`.
- **Lambdas que capturan `self` en `connect`**: forman un ciclo a través de Qt; el GC de Python limpia la
  lambda (le borra los argumentos por defecto) y si la señal se emite después, el slot tira TypeError y
  PyQt aborta el proceso (0xC0000409, sin traza; se ve con `QT_FORCE_STDERR_LOGGING=1`). Pasaba en la
  suite completa, según el orden de los tests. Conectar métodos y usar `self.sender()` (ver HoverFader).
- **Escalado fraccionario (125 %, 150 %)**: copiar un pixmap con DPR fraccionario va por un camino escalado
  de Qt (hasta 6x más lento). `HomeLayers` compone el frame en píxeles físicos (`to_device`: pixmaps con
  DPR 1, posiciones enteras, `painter.scale(1/dpr)`). Un fondo sin alfa (`opaque=True`) se copia directo.
- **Fuentes variables** (google/fonts sólo publica `Familia[wght].ttf`): Qt registra las instancias con
  nombre y `QFont.setWeight(600)` elige la SemiBold real (verificado en plataforma Windows y offscreen;
  `test_fonts` lo chequea con QFontInfo). No hace falta `setVariableAxis`.
- **`theme.TYPE` se lee al usarse** en el código del inicio (`from src.common import theme`; `theme.TYPE`),
  no con `from theme import TYPE`: así un test o un script de capturas puede reemplazarlo con monkeypatch.
  Las fuentes tienen que estar registradas (`load_fonts()`) antes de crear widgets; si no, Qt usa otra.
- **Columnas largas**: `TableLayout._offsets` comprime primero las boca abajo (mín. `MIN_DOWN_OFFSET`) y
  después las boca arriba. Peor caso (6 tapadas + K→A, 19 cartas): siempre entra en la ventana; a
  1000x720 (tamaño por defecto) los índices se leen, cerca del mínimo (~700x500 de mesa) quedan
  recortados (K/Q/J apenas visibles). Si se agrandan los índices (`card_painter._corner`), revisar.
- **Orden del reciclado**: el descarte vuelve al mazo invertido (`waste[::-1]`) para repetir el orden de
  robo original; hay test que lo verifica en varias pasadas.
- **Consola de Windows (cp1252)** no imprime ♠♥♦♣: en scripts que impriman cartas usar `PYTHONIOENCODING=utf-8`.
- **`wmic` no existe** en este Windows 11; usar `Get-CimInstance Win32_Process`.
- **`QTest.mouseMove` en la plataforma real (windows) mueve el cursor de verdad**: en scripts de medición
  mandar `QMouseEvent` con `QApplication.sendEvent` (no toca el cursor del usuario).
- **`app.quit()` en Qt 6 cierra las ventanas** (y `MainWindow.closeEvent` destruye el juego): para medir en un
  script, salir de un `QEventLoop` propio, no de `app.exec()`.
- **QToolButton no toma la fuente de la hoja de estilos** (sí el resto del QSS): en el diálogo de coronación
  se le pone con `setFont`.
- **QSoundEffect sólo lee WAV** (por eso los OGG de Kenney se convierten con `QAudioDecoder` en
  `preparar_sonidos.py`; ese script necesita la QCoreApplication viva mientras decodifica).
- **Sonidos diferidos en tests**: `play_later` usa `QTimer.singleShot`; un timer de un test anterior puede
  sonar en el siguiente. `test_sound_hooks` espera antes de instalar su reproductor.
- **`QTableWidget.scrollToItem` justo después de agregar filas no desplaza** (la lista de jugadas quedaba
  arriba en partidas largas): `scrollToBottom()`.
- **GlassDialog y el tamaño**: el tamaño se calcula antes de que el estilo agrande las fuentes; sin
  `setSizeConstraint(SetMinimumSize)` el diálogo quedaba en su ancho mínimo y apretaba los botones.
- **Animaciones del solitario en tests**: tras `deal`/`new_game` hay tweens activos (el timer pinta cada 16 ms);
  el modelo ya está completo, así que los tests no esperan. Un clic las termina (`motion.finish()`).
- **Mixins con widgets en PyQt6**: una clase no puede heredar de dos clases Qt (QAbstractButton y QWidget); los objetos
  de la mesa comparten `Placed`, un mixin de Python puro (`class BrassButton(Placed, QAbstractButton)`).
- **Tests de visibilidad**: si la pantalla del test no está mostrada, `isVisible()` de sus hijos da False aunque se
  hayan mostrado; usar `isHidden()`.
- **Flags de texto**: `Qt.AlignmentFlag | Qt.TextFlag` no se combinan en PyQt6; pasar
  `(alineación).value | Qt.TextFlag.TextWordWrap.value` (int) a `drawText`.
- **Contraste sobre metal**: con letra oscura, el bronce de las placas secundarias tuvo que aclararse (#8a6a3c →
  #b8915a) para llegar a 4,5:1 también apretada; con un bronce oscuro ni el negro alcanza. Medir con
  `test_text_contrast_on_paper_and_brass` si se re-renderiza.
- **Lado de la luz**: el render tiene la luz arriba a la izquierda (sombras abajo a la derecha); lo que se dibuje
  por código (sombra de la levantada, sombra del tablero, lámpara) tiene que respetarla.
- **La tabla de alturas de `blender/INTEGRACION.md` no coincide con los PNG**: medidos (alfa >= 50 %, 426,67 px
  por casilla) rey 0,809, dama 0,745, alfil 0,712, torre 0,691, caballo 0,689, peón 0,600 (la tabla dice rey
  0,892 y caballo más alto que la torre). La escala y los apoyos sí coinciden con la cámara. Por eso en el tablero
  van a `piece_scale` = 1,10 (rey ~0,89; con el apoyo a 0,15 el rey sigue entrando: arriba le quedan ~0,055).
  `test_piece_art` usa las medidas reales; si se re-renderiza, re-medir.
- **Alfa por más de 1** (reflejo, halo, bloom): `piece_sprites._amplified` suma la imagen a sí misma en modo Plus
  (premultiplicado: exacto hasta saturar). `setOpacity` no pasa de 1.
- **Pintar en un pixmap con DPR**: el pintor ya escala por el DPR (no es parte de la transformación del mundo;
  `resetTransform` no lo saca). Para copiar 1 a 1 una imagen en px físicos, dar el destino en px lógicos
  (`QRectF(x / dpr, ...)`), como hace `chess_backdrop._paint_table`.
- **QSS agregado después en un GlassDialog no se aplica** (`setStyleSheet(self.styleSheet() + regla)` en el
  constructor de una subclase: la regla nueva se ignora hasta mostrar el diálogo). Las reglas compartidas van en
  `glass_dialog.dialog_qss` (por eso existe `QLabel#dialogHeading`).
- **Diálogos con párrafos largos**: con `SetMinimumSize` el layout calcula el alto para otro ancho y corta el texto;
  `AboutDialog.showEvent` fija ancho y alto con `totalHeightForWidth`.
- **Blender graba metadatos en los PNG** (ruta del .blend con el usuario de Windows, fecha, tiempos): `generar_ajedrez.py`
  apaga los `use_stamp_*`; si igual aparecen, `scripts/limpiar_metadatos_png.py` (test_release lo exige).
- **Rutas en el .blend**: los campos son char[N] fijos; asignar una ruta más corta deja la vieja detrás del `\0`
  (y se guarda). Para borrar: asignar primero un texto largo y después el nuevo. El explorador de archivos del
  workspace "Shading" guardaba la última carpeta.
- **tmp_path largo y test_layout_fit**: el panel del ajedrez sin Stockfish muestra la ruta; una palabra sin espacios
  muy larga (p. ej. `--basetemp` en una carpeta de nombre largo) lo ensancha más que su mitad a 800x600. Con la
  carpeta de siempre pasa. (Una ruta real así también lo haría: pendiente menor.)
- **QImage en otro hilo**: leer PNG con `QImage` fuera del hilo de la UI es seguro (`art_library.prefetch`);
  `QPixmap` NO: los pixmaps se crean siempre en el hilo de la UI (`BoardAssets`).

## Dependencias
Ver `requirements.txt`: PyQt6 6.11.0, chess 1.11.2, python-dotenv 1.2.4, pytest 9.1.1.
