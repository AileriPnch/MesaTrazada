"""Objetos de la interfaz de la partida, apoyados sobre la mesa: planilla (portapapeles de cuero, clip de latón,
hoja marfil con renglones impresos), bandeja de capturadas (nogal + fieltro bordó), reloj de madera y latón,
placas-botón y carteles de latón, tarjeta de fin de partida, perilla del volumen y el rey acostado (jaque mate).

Uso (línea de comandos, sin abrir Blender):
    blender.exe -b blender/ajedrez.blend -P blender/generar_interfaz.py -- <modo>
  mock      -> blender/previews/interfaz_mock.png: la escena completa armada como en la app maximizada (1920 x 1009,
               casilla de 110 px), cámara cenital, baja calidad. Sin piezas ni textos (los pone el código).
  planos    -> assets/ajedrez/interfaz/: planilla, bandeja, placas (4 estados), cartel, tarjeta, perilla (3 estados);
               cada uno con _sombra y _contacto. Cámara cenital, como el tablero y la mesa.
  volumen   -> reloj (3 estados + luces + sombra + contacto) a 20°, como las piezas, y {color}_rey_acostado (los 5
               pases de las piezas).
  revisar   -> interfaz.json (anclas y rectángulos) + revisión de alfas y caja visible de todos los PNG.
  anclas    -> recalcula las anclas del reloj sin renderizar.
  placa_principal,bandeja,... -> sólo esos objetos planos (planilla, bandeja, placa_principal, placa_secundaria,
               cartel, tarjeta, perilla).
  (sin modo = planos + volumen + revisar)

Reusa materiales, luces, cámaras y utilidades de generar_ajedrez.py (sin ejecutar su parte final, que reconstruye la
escena y guarda el .blend). No guarda ajedrez.blend. Unidades: 1 = 1 casilla; origen en el centro del tablero; la
mesa está en Z = -0,30. Cada objeto se renderiza EN SU LUGAR de la disposición (recibe la luz de la lámpara que le
toca) con una luz de relleno que sólo ve la interfaz (el papel tiene que leerse marfil lejos de la lámpara).
"""
import bpy, json, math, os, sys
from mathutils import Matrix, Vector, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
_fuente = open(os.path.join(AQUI, "generar_ajedrez.py"), encoding="utf-8").read()
exec(_fuente.split("# ---------------- Main ----------------")[0], globals())

DEST = os.path.join(PROYECTO, "assets", "ajedrez", "interfaz")
MESA_Z = -0.30
PX = 256                 # px por casilla de los sprites de la interfaz
PX_PERILLA = 512         # la perilla es chica: más densidad
MARGEN = 0.3             # casillas alrededor de cada objeto (sombra)
MUESTRAS = 1024
# Disposición en casillas: la misma que el mock de la app (en la fase C pasa a tokens de theme.py)
BOARD, GAP, TRAY, COL = 8.4, 0.25, 1.1, 3.6
PLATE_H, CLOCK_W, CLOCK_H = 0.5, 2.4, 1.15
TRAY_H = 3.0             # alto de cada bandeja (centrada en su mitad del tablero)
PRIMARY_H, SECONDARY_H, STACK_GAP, BUTTON_GAP = 0.72, 0.6, 0.15, 0.25
CLIP_TOP, PAPER_MARGIN, HEADER, ROW, FOOTER = 0.4, 0.12, 0.3, 0.3, 0.26
NUM_COL = 0.16           # ancho de la columna de números (fracción del papel)
VENTANA_PX, CASILLA_PX = (1920, 1009), 110
COLORES = dict(papel="#f3ead6", cuero="#3b2418", laton="#c9a25a", laton_cepillado="#cfa96a", bronce="#b8915a",
               madera="#3a2416",
               fieltro="#4a1420", esfera="#f3ead6", tinta_impresa="#9aa3bf", luz="#ffbf55", lente="#3a2410",
               aguja="#1a1410", apagado="#a39885")
PAPEL_OBJETIVO = 0.80    # luminancia lineal objetivo del centro del papel (~ #efe6d2 en sRGB)


# ---------------- GPU ----------------
def configurar_gpu():
    """OptiX explícito; si no hay, CUDA (y lo avisa); si tampoco, CPU."""
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = tipo
        except TypeError:
            continue
        prefs.get_devices()
        devs = [d for d in prefs.devices if d.type == tipo]
        if devs:
            for d in prefs.devices:
                d.use = d.type == tipo
            scn.cycles.device = 'GPU'
            if tipo != "OPTIX":
                print("AVISO: no hay OptiX; se usa CUDA")
            print("GPU:", tipo, [d.name for d in devs])
            return tipo
    scn.cycles.device = 'CPU'
    print("AVISO: sin GPU (ni OptiX ni CUDA): se renderiza con CPU")
    return "CPU"


def base(muestras):
    render_base(muestras); configurar_gpu()
    if EXPOSICION_TABLERO is None:
        calibrar_exposicion()
    scn.view_settings.exposure = EXPOSICION_TABLERO


# ---------------- Disposición ----------------
def rectangulos():
    """Rectángulos (x0, y0, x1, y1) en casillas, con +Y hacia arriba en pantalla. Bandeja al costado."""
    top, bottom = BOARD / 2, -BOARD / 2
    x = BOARD / 2 + GAP
    mitad = (BOARD - GAP) / 2
    alto_b = min(TRAY_H, mitad)
    centro_r, centro_p = top - mitad / 2, bottom + mitad / 2  # cada bandeja, centrada en su mitad del tablero
    r = {"bandeja_rival": (x, centro_r - alto_b / 2, x + TRAY, centro_r + alto_b / 2),
         "bandeja_propia": (x, centro_p - alto_b / 2, x + TRAY, centro_p + alto_b / 2)}
    x += TRAY + GAP
    x1 = x + COL
    r["cartel_rival"] = (x, top - PLATE_H, x1, top)
    y = top - PLATE_H - STACK_GAP
    cx = (x + x1) / 2
    r["reloj"] = (cx - CLOCK_W / 2, y - CLOCK_H, cx + CLOCK_W / 2, y)
    y -= CLOCK_H + STACK_GAP
    sec_w = (COL - STACK_GAP) / 2
    r["deshacer"] = (x, bottom, x + sec_w, bottom + SECONDARY_H)
    r["menu"] = (x1 - sec_w, bottom, x1, bottom + SECONDARY_H)
    yp = bottom + SECONDARY_H + STACK_GAP
    r["nueva"] = (x, yp, x1, yp + PRIMARY_H)
    yp += PRIMARY_H + BUTTON_GAP
    r["cartel_propio"] = (x, yp, x1, yp + PLATE_H)
    r["planilla"] = (x, yp + PLATE_H + STACK_GAP, x1, y)
    r["tarjeta"] = (cx - 1.5, r["planilla"][1] + 1.0, cx + 1.5, r["planilla"][1] + 2.5)
    return r


def esquina_perilla():
    """Centro de la perilla (esquina del volumen, CORNER a escala 1) en casillas, y su radio."""
    w, h = VENTANA_PX
    total = BOARD + GAP + TRAY + GAP + COL
    cam_x = total / 2 - BOARD / 2
    px_ = (w - 12 - 17, 12 + 17)
    return (cam_x + (px_[0] - w / 2) / CASILLA_PX, (h / 2 - px_[1]) / CASILLA_PX), 17 / CASILLA_PX


# ---------------- Materiales ----------------
def emision(nombre, color, fuerza):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    em.inputs["Color"].default_value = lin(color) if isinstance(color, str) else color
    em.inputs["Strength"].default_value = fuerza
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def metal(nombre, color, rough):
    m = principled(nombre, color, rough, spec=0.5)
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    setv(b, "Metallic", 1.0)
    return m


def cuero_mat():
    """Cuero mate (sin barniz: no refleja el panel de luz), con grano fino."""
    m = principled("Cuero_Oscuro", COLORES["cuero"], 0.62)
    N = Nodos(m.node_tree)
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    ruido = N.n("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = 180.0
    ruido.inputs["Detail"].default_value = 6.0
    bump = N.n("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.002
    N.link(ruido.outputs["Fac"], bump.inputs["Height"]); N.link(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def laton_cepillado_mat():
    """Latón cepillado: veta fina a lo largo de la placa (ruido muy estirado) que modula la rugosidad y apenas el
    tono (sin anisotropía: con la tangente por defecto, radial, deja un remolino). Cálido y pulido (rugosidad baja):
    la placa principal se destaca por brillo especular frente al bronce de las secundarias, sin ser amarillo plano."""
    m = metal("Laton_Cepillado", COLORES["laton_cepillado"], 0.3)
    N = Nodos(m.node_tree)
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    tc = N.n("ShaderNodeTexCoord")
    mapeo = N.n("ShaderNodeMapping"); N.link(tc.outputs["Object"], mapeo.inputs["Vector"])
    mapeo.inputs["Scale"].default_value = (1.5, 160.0, 1.0)  # las coordenadas del objeto van de -0,5 a 0,5
    ruido = N.n("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = 6.0; ruido.inputs["Detail"].default_value = 8.0
    N.link(mapeo.outputs["Vector"], ruido.inputs["Vector"])
    rango = N.n("ShaderNodeMapRange"); N.link(ruido.outputs["Fac"], rango.inputs["Value"])
    rango.inputs["To Min"].default_value = 0.1; rango.inputs["To Max"].default_value = 0.3
    N.link(rango.outputs["Result"], b.inputs["Roughness"])
    claro = lin(COLORES["laton_cepillado"])
    oscuro = tuple(c * 0.85 for c in claro[:3]) + (1.0,)
    N.link(N.rampa(ruido.outputs["Fac"], [(0.3, oscuro), (0.7, claro)]), b.inputs["Base Color"])
    return m


def fieltro_mat():
    m = principled("Fieltro_Bordo", COLORES["fieltro"], 1.0, spec=0.2)
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    setv(b, "Sheen Weight", 0.6); setv(b, "Sheen Roughness", 0.5)
    N = Nodos(m.node_tree)
    ruido = N.n("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = 400.0
    bump = N.n("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15; bump.inputs["Distance"].default_value = 0.001
    N.link(ruido.outputs["Fac"], bump.inputs["Height"]); N.link(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def materiales_interfaz():
    E = bpy.data.materials
    return dict(
        papel=principled("Papel_Marfil", COLORES["papel"], 0.85, sss=0.05),
        cuero=cuero_mat(),
        laton=metal("Laton_Pulido", COLORES["laton"], 0.22),
        laton_cepillado=laton_cepillado_mat(),
        bronce=metal("Bronce_Envejecido", COLORES["bronce"], 0.42),
        apagado=metal("Laton_Apagado", COLORES["apagado"], 0.65),
        madera=principled("Madera_Reloj", COLORES["madera"], 0.35, coat=0.6, coat_rough=0.08),
        fieltro=fieltro_mat(),
        esfera=principled("Esfera_Reloj", COLORES["esfera"], 0.5, coat=0.4),
        tinta=principled("Tinta_Impresa", COLORES["tinta_impresa"], 0.9),
        aguja=principled("Aguja_Reloj", COLORES["aguja"], 0.4),
        lente=principled("Lente_Apagada", COLORES["lente"], 0.08, coat=1.0),
        luz=emision("Luz_Reloj", COLORES["luz"], 2.5),
        marfil=E["Marfil_Laqueado"], ebano=E["Ebano_Laqueado"],
    )


# ---------------- Geometría ----------------
INTERFAZ, METALES, RELLENO, RELOJ = None, None, None, None   # colecciones (se crean en preparar())


def _a_coleccion(o, metalico=False):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    INTERFAZ.objects.link(o); RELLENO.objects.link(o)
    if metalico:
        METALES.objects.link(o)
    if o.name.startswith("Reloj_"):  # sólo el reloj recibe la luz de frente (sus esferas miran a la cámara)
        RELOJ.objects.link(o)
    return o


def bloque(nombre, x0, y0, x1, y1, alto, mat, z=MESA_Z, bisel=0.02, metalico=False):
    o = caja(nombre, (x1 - x0, y1 - y0, alto), ((x0 + x1) / 2, (y0 + y1) / 2, z + alto / 2))
    if bisel:
        b = o.modifiers.new("Bisel", "BEVEL"); b.width = bisel; b.segments = 3; b.limit_method = 'ANGLE'
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return _a_coleccion(o, metalico)


def cilindro(nombre, r, alto, loc, mat, seg=48, rot=(0, 0, 0), metalico=False):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=alto, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = nombre
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return _a_coleccion(o, metalico)


def toro(nombre, r_mayor, r_menor, loc, rot, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=r_mayor, minor_radius=r_menor, location=loc, rotation=rot,
                                     major_segments=64, minor_segments=12)
    o = bpy.context.active_object; o.name = nombre
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return _a_coleccion(o, True)


def placa(nombre, rect, mat, M, alto=0.05):
    x0, y0, x1, y1 = rect
    objs = [bloque(nombre, x0, y0, x1, y1, alto, mat, bisel=0.02, metalico=True)]
    cy = (y0 + y1) / 2
    for i, x in enumerate((x0 + 0.12, x1 - 0.12)):  # tornillos
        objs.append(cilindro(f"{nombre}_tornillo{i}", 0.035, 0.02, (x, cy, MESA_Z + alto + 0.005), M["laton"], 24,
                             metalico=True))
    return objs


def papel_rect(rect):
    x0, y0, x1, y1 = rect
    return (x0 + PAPER_MARGIN, y0 + PAPER_MARGIN, x1 - PAPER_MARGIN, y1 - CLIP_TOP)


def renglones(paper):
    """Líneas impresas de la hoja: debajo del encabezado y de cada renglón, y las de las columnas."""
    x0, y0, x1, y1 = paper
    filas = int((y1 - y0 - HEADER - FOOTER) / ROW)
    ys = [y1 - HEADER - k * ROW for k in range(filas + 1)]
    num_x = x0 + (x1 - x0) * NUM_COL
    mid_x = num_x + (x1 - num_x) / 2
    return filas, ys, num_x, mid_x


def planilla(rect, M):
    x0, y0, x1, y1 = rect
    objs = [bloque("Planilla_Cuero", x0, y0, x1, y1, 0.04, M["cuero"], bisel=0.03)]
    paper = papel_rect(rect)
    zp = MESA_Z + 0.04
    objs.append(bloque("Planilla_Hoja", *paper, 0.004, M["papel"], z=zp, bisel=0.0))
    filas, ys, num_x, mid_x = renglones(paper)
    zl = zp + 0.004
    for k, y in enumerate(ys):
        objs.append(bloque(f"Planilla_Linea{k}", paper[0] + 0.05, y - 0.004, paper[2] - 0.05, y + 0.004, 0.0006,
                           M["tinta"], z=zl, bisel=0.0))
    for k, x in enumerate((num_x, mid_x)):
        objs.append(bloque(f"Planilla_Columna{k}", x - 0.004, ys[-1], x + 0.004, ys[0], 0.0006, M["tinta"], z=zl,
                           bisel=0.0))
    cx = (x0 + x1) / 2
    objs.append(bloque("Planilla_Clip", cx - 0.6, y1 - 0.36, cx + 0.6, y1 - 0.06, 0.07, M["laton"], z=zp, bisel=0.03,
                       metalico=True))
    objs.append(cilindro("Planilla_Clip_Rodillo", 0.035, 1.1, (cx, y1 - 0.08, zp + 0.06), M["laton"], 32,
                         rot=(0, math.pi / 2, 0), metalico=True))
    return objs


def bandeja(rect, M):
    """Bandeja de nogal con fondo de fieltro bordó."""
    x0, y0, x1, y1 = rect
    borde, alto = 0.08, 0.12
    objs = [bloque("Bandeja_Fondo", x0, y0, x1, y1, 0.03, M["madera"], bisel=0.01)]
    objs.append(bloque("Bandeja_Fieltro", x0 + borde, y0 + borde, x1 - borde, y1 - borde, 0.006, M["fieltro"],
                       z=MESA_Z + 0.03, bisel=0.0))
    for nombre, r in (("N", (x0, y1 - borde, x1, y1)), ("S", (x0, y0, x1, y0 + borde)),
                      ("O", (x0, y0 + borde, x0 + borde, y1 - borde)), ("E", (x1 - borde, y0 + borde, x1, y1 - borde))):
        objs.append(bloque(f"Bandeja_Borde{nombre}", *r, alto, M["madera"], bisel=0.015))
    return objs


def tarjeta(rect, M):
    x0, y0, x1, y1 = rect
    objs = [bloque("Tarjeta", x0, y0, x1, y1, 0.006, M["papel"], bisel=0.0)]
    z = MESA_Z + 0.006
    for k, d in enumerate((0.08, 0.11)):  # doble filete impreso
        for lado, r in (("N", (x0 + d, y1 - d - 0.006, x1 - d, y1 - d)), ("S", (x0 + d, y0 + d, x1 - d, y0 + d + 0.006)),
                        ("O", (x0 + d, y0 + d, x0 + d + 0.006, y1 - d)), ("E", (x1 - d - 0.006, y0 + d, x1 - d, y1 - d))):
            objs.append(bloque(f"Tarjeta_Filete{k}{lado}", *r, 0.0006, M["tinta"], z=z, bisel=0.0))
    return objs


def perilla(M, centro, r, alto=0.12):
    o = cilindro("Perilla_Volumen", r, alto, (centro[0], centro[1], MESA_Z + alto / 2), M["laton"], 96, metalico=True)
    b = o.modifiers.new("Bisel", "BEVEL"); b.width = r * 0.18; b.segments = 4
    tapa = cilindro("Perilla_Tapa", r * 0.62, 0.012, (centro[0], centro[1], MESA_Z + alto + 0.006), M["laton"], 64,
                    metalico=True)
    return [o, tapa]


def reloj(rect, M, hundido=None):
    """Reloj de ajedrez (decorativo): caja de madera, dos esferas de frente (miran a -Y, hacia la cámara de 20°)
    con bisel de latón, agujas fijas, botones arriba (marfil = blancas, ébano = negras; `hundido` = el apretado) y
    una lente por lado bajo cada esfera. Izquierda = blancas, derecha = negras."""
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ancho, fondo, alto = CLOCK_W, 0.75, 0.6
    objs = [bloque("Reloj_Caja", cx - ancho / 2, cy - fondo / 2, cx + ancho / 2, cy + fondo / 2, alto, M["madera"],
                   bisel=0.06)]
    frente = cy - fondo / 2
    lentes = {}
    for i, lado in enumerate(("blancas", "negras")):
        dx = cx + (-0.6 if i == 0 else 0.6)
        zc = MESA_Z + 0.36
        objs.append(cilindro(f"Reloj_Esfera_{lado}", 0.34, 0.02, (dx, frente - 0.005, zc), M["esfera"], 64,
                             rot=(math.pi / 2, 0, 0)))
        objs.append(toro(f"Reloj_Bisel_{lado}", 0.35, 0.025, (dx, frente - 0.012, zc), (math.pi / 2, 0, 0), M["laton"]))
        for h in range(12):  # marcas de las horas
            a = h * math.pi / 6
            o = bloque(f"Reloj_Marca_{lado}{h}", -0.006, -0.002, 0.006, 0.002, 0.05, M["aguja"], z=0, bisel=0.0)
            o.location = (dx + 0.27 * math.sin(a), frente - 0.017, zc + 0.27 * math.cos(a) - 0.025)
            o.rotation_euler = (0, -a, 0)
            objs.append(o)
        for nombre, largo, ang in (("hora", 0.17, -60), ("minuto", 0.25, 60)):  # 10:10, fijas
            o = bloque(f"Reloj_Aguja_{nombre}_{lado}", -0.008, -0.002, 0.008, 0.002, largo, M["aguja"], z=0, bisel=0.0)
            a = math.radians(ang)  # la aguja sale del centro: su caja se corre medio largo en su dirección
            o.location = (dx + math.sin(a) * largo / 2, frente - 0.02, zc + math.cos(a) * largo / 2 - largo / 2)
            o.rotation_euler = (0, a, 0)
            objs.append(o)
        sube = 0.04 if lado == hundido else 0.12
        objs.append(cilindro(f"Reloj_Boton_{lado}", 0.14, sube, (dx, cy + 0.05, MESA_Z + alto + sube / 2),
                             M["marfil"] if lado == "blancas" else M["ebano"], 48))
        objs.append(toro(f"Reloj_Aro_{lado}", 0.15, 0.02, (dx, cy + 0.05, MESA_Z + alto + 0.005), (0, 0, 0), M["laton"]))
        lente = esfera(f"Reloj_Lente_{lado}", 0.05, (dx, frente - 0.02, MESA_Z + 0.09), 32)
        lente.data.materials.append(M["lente"])
        lentes[lado] = _a_coleccion(lente)
        objs.append(lente)
    return objs, lentes


# ---------------- Luces de la interfaz ----------------
def luces_interfaz():
    """Relleno suave sobre la columna (sólo lo ve la interfaz) y panel claro que sólo aparece en los reflejos de
    los metales (el latón pulido visto desde arriba reflejaría el mundo negro)."""
    L = bpy.data.lights.new("Relleno_Interfaz", "AREA"); L.shape = 'RECTANGLE'; L.size = 8.0; L.size_y = 12.0
    L.energy = 400.0; L.color = (1.0, 0.96, 0.9)
    relleno = bpy.data.objects.new("Relleno_Interfaz", L); INTERFAZ.objects.link(relleno)
    relleno.location = (8.0, 0.5, 9.0)
    relleno.visible_glossy = False
    relleno.light_linking.receiver_collection = RELLENO
    F = bpy.data.lights.new("Frente_Interfaz", "AREA"); F.shape = 'RECTANGLE'; F.size = 4.0; F.size_y = 1.5
    F.energy = 60.0; F.color = (1.0, 0.95, 0.88)
    frente = bpy.data.objects.new("Frente_Interfaz", F); INTERFAZ.objects.link(frente)
    frente.location = (7.6, -1.0, MESA_Z + 1.2)  # de frente al reloj (sus esferas miran a -Y): que no se vean grises
    frente.rotation_euler = (Vector((7.6, 3.0, MESA_Z + 0.35)) - frente.location).to_track_quat('-Z', 'Y').to_euler()
    frente.visible_glossy = False
    frente.light_linking.receiver_collection = RELOJ
    frente.hide_render = True  # se enciende sólo para el reloj: con la colección vacía, Blender ignora el vínculo
    me = bpy.data.meshes.new("Panel_Reflejo")
    me.from_pydata([(-3.0, -5.5, 0), (3.0, -5.5, 0), (3.0, 5.5, 0), (-3.0, 5.5, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(emision("Panel_Reflejo", "#fff1dc", 1.4))
    panel = bpy.data.objects.new("Panel_Reflejo", me); INTERFAZ.objects.link(panel)
    panel.location = (7.6, 1.0, 6.0); panel.rotation_euler = (math.pi, 0, 0)
    for prop in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        setattr(panel, prop, False)
    panel.light_linking.receiver_collection = METALES
    return relleno, panel


# ---------------- Escena ----------------
def escena_existente():
    O = bpy.data.objects
    luces = dict(principal=O["Luz_Principal"], relleno=O["Luz_Relleno"], contra=O["Luz_Contra"],
                 contra_n=O["Luz_Contra_Negras"], lampara=O["Lampara"], disco=O["Disco_Lampara"])
    camaras = dict(cenital=O["Cam_Cenital"], piezas=O["Cam_Piezas"], reflejo=O["Cam_Reflejo"], preview=O["Cam_Preview"])
    piezas = {tuple(o.name.split("_", 1)): o for o in bpy.data.collections["Piezas"].objects
              if o.name.split("_", 1)[0] in ("blancas", "negras")}
    preview = list(bpy.data.collections["Preview"].objects) if "Preview" in bpy.data.collections else []
    return dict(luces=luces, camaras=camaras, tablero=[O["Casillas"], O["Marco"]], mesa=O["Mesa"], preview=preview,
                piezas=piezas, suelo=O["Suelo_Sombra"])


def preparar():
    global INTERFAZ, METALES, RELLENO, RELOJ
    INTERFAZ = coleccion("Interfaz")
    RELOJ = coleccion("Interfaz_Reloj", enlazar=False)
    METALES = coleccion("Interfaz_Metal", enlazar=False)
    RELLENO = coleccion("Interfaz_Relleno", enlazar=False)
    M = materiales_interfaz()
    luces = luces_interfaz()
    me = bpy.data.meshes.new("Suelo_Interfaz")
    me.from_pydata([(-30, -30, MESA_Z), (30, -30, MESA_Z), (30, 30, MESA_Z), (-30, 30, MESA_Z)], [], [(0, 1, 2, 3)])
    suelo = bpy.data.objects.new("Suelo_Interfaz", me); INTERFAZ.objects.link(suelo)
    suelo.is_shadow_catcher = True; suelo.hide_render = True
    return M, luces, suelo


# ---------------- Cámaras y pases ----------------
def camara_cenital(rect, margen=MARGEN, px=PX):
    """Encuadre cenital del rectángulo + margen. Devuelve (ancho_px, alto_px, función casillas -> px)."""
    x0, y0, x1, y1 = rect
    w, h = (x1 - x0) + 2 * margen, (y1 - y0) + 2 * margen
    cam = ESCENA["camaras"]["cenital"]
    cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, 30); cam.rotation_euler = (0, 0, 0)
    cam.data.ortho_scale = max(w, h)
    cam.data.sensor_fit = 'HORIZONTAL' if w >= h else 'VERTICAL'
    scn.camera = cam
    wp, hp = round(w * px), round(h * px)
    scn.render.resolution_x, scn.render.resolution_y = wp, hp
    ox, oy = x0 - margen, y1 + margen
    return wp, hp, lambda x, y: (round((x - ox) * px, 1), round((oy - y) * px, 1))


def camara_20(centro, ancho, alto_vista, px=PX):
    """Cámara ortográfica inclinada 20° (como la de las piezas) mirando a `centro`."""
    cam = bpy.data.objects.get("Cam_Interfaz_20")
    if cam is None:
        cd = bpy.data.cameras.new("Cam_Interfaz_20"); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 200
        cam = bpy.data.objects.new("Cam_Interfaz_20", cd); INTERFAZ.objects.link(cam)
    rot = Euler((math.radians(90 - INCLINACION_PIEZAS), 0, 0))
    fwd = rot.to_matrix() @ Vector((0, 0, -1))
    cam.rotation_euler = rot; cam.location = Vector(centro) - fwd * 20
    cam.data.ortho_scale = ancho; cam.data.sensor_fit = 'HORIZONTAL'
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = round(ancho * px), round(alto_vista * px)
    return cam


def _luces_cuerpo(relleno, panel, panel_fuerza=1.4):
    luces_modo("tablero"); _mundo(1.0)
    relleno.hide_render = False; panel.hide_render = False
    em = next(n for n in panel.data.materials[0].node_tree.nodes if n.bl_idname == "ShaderNodeEmission")
    em.inputs["Strength"].default_value = panel_fuerza


def _desvanecer(ruta, ancho_px):
    """Alfa que cae suave a 0 en los últimos `ancho_px` de cada borde: la sombra y el contacto no se cortan en el
    borde del sprite (el contacto es oclusión local; lejos del objeto ya casi no hay)."""
    import numpy as np
    a = _px(ruta)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(np.float32)
    f = np.clip(d / max(1.0, ancho_px), 0, 1)
    a[..., 3] *= f * f * (3 - 2 * f)
    _guardar(ruta, a)


def pases(ruta, objs, suelo, relleno, panel, estados=None, sombras=None):
    """cuerpo(s) + _sombra + _contacto, como las piezas. `estados`: {sufijo: preparar()} para variantes del
    cuerpo; `sombras`: {sufijo: preparar()} para variantes de la sombra (p. ej. la placa apretada)."""
    L = ESCENA["luces"]; t = {}
    scn.render.film_transparent = True
    for sufijo, prep in (estados or {"": lambda: None}).items():
        prep()
        solo(objs); _luces_cuerpo(relleno, panel, getattr(prep, "panel", 1.4))
        t[sufijo or "cuerpo"] = _render(f"{ruta}{sufijo}.png")
    for sufijo, prep in (sombras or {"": lambda: None}).items():
        prep()
        for k in ("relleno", "contra", "contra_n", "lampara", "disco"):
            L[k].hide_render = True
        relleno.hide_render = True; panel.hide_render = True; L["principal"].hide_render = False
        _mundo(0.0)
        solo(objs + [suelo])
        for o in objs:
            o.visible_camera = False
        borde = 0.45 * MARGEN * scn.render.resolution_x / (scn.camera.data.ortho_scale or 1)
        t["sombra" + sufijo] = _render(f"{ruta}_sombra{sufijo}.png"); _escalar_alfa(f"{ruta}_sombra{sufijo}.png", SOMBRA_FUERZA)
        _desvanecer(f"{ruta}_sombra{sufijo}.png", borde)
        if sufijo == "":
            L["principal"].hide_render = True; _mundo(1.0, (1, 1, 1))
            t["contacto"] = _render(f"{ruta}_contacto.png"); _escalar_alfa(f"{ruta}_contacto.png", CONTACTO_FUERZA)
            _desvanecer(f"{ruta}_contacto.png", borde)
        for o in objs:
            o.visible_camera = True
    return t


# ---------------- Calibración del papel ----------------
def calibrar_relleno(relleno, panel, M, rect):
    """Ajusta la luz de relleno para que el centro del papel dé PAPEL_OBJETIVO (lineal): marfil cálido, no apagado."""
    import numpy as np, tempfile
    objs = planilla(rect, M)
    paper = papel_rect(rect)
    for _ in range(4):
        base(96)
        wp, hp, a_px = camara_cenital(rect, px=64)
        scn.render.film_transparent = True
        solo(objs); _luces_cuerpo(relleno, panel)
        ruta = os.path.join(tempfile.gettempdir(), "calib_papel.png"); _render(ruta)
        img = _a_lin(_px(ruta)[..., :3]); os.remove(ruta)
        cx, cy = a_px((paper[0] + paper[2]) / 2, (paper[1] + paper[3]) / 2)
        y = hp - int(cy)  # la imagen de Blender está de abajo hacia arriba
        lum = float(img[y - 4:y + 4, int(cx) - 4:int(cx) + 4].reshape(-1, 3).mean(axis=0)
                    @ np.array([0.2126, 0.7152, 0.0722]))
        factor = PAPEL_OBJETIVO / max(lum, 1e-4)
        print(f"calibración papel: lum {lum:.3f} (objetivo {PAPEL_OBJETIVO}) -> relleno x{factor:.2f}")
        if abs(factor - 1) < 0.04:
            break
        relleno.data.energy *= max(0.2, min(5.0, factor)) ** 1.1
    _limpiar(objs)
    return relleno.data.energy


# ---------------- Render final ----------------
DATOS = {}


def _entrada(nombre, wp, hp, a_px, rect, px=PX, **extra):
    x0, y0, x1, y1 = rect
    DATOS[nombre] = dict(px_por_casilla=px, tamaño=[wp, hp], ancla=list(a_px((x0 + x1) / 2, (y0 + y1) / 2)),
                         objeto=[*a_px(x0, y1), *a_px(x1, y0)], **extra)


def _limpiar(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def _estado(cuerpo, material, alto, escala_z, fuerza):
    def prep():
        cuerpo.data.materials[0] = material
        cuerpo.scale.z = escala_z; cuerpo.location.z = MESA_Z + escala_z * alto / 2
    prep.panel = fuerza
    return prep


def _estado_perilla(cuerpo, tapa, baja, fuerza):
    def prep():
        cuerpo.location.z = MESA_Z + 0.06 - baja; tapa.location.z = MESA_Z + 0.126 - baja
    prep.panel = fuerza
    return prep


def render_planos(M, relleno, panel, suelo, que=None):
    os.makedirs(DEST, exist_ok=True)
    R = rectangulos(); t = {}
    base(MUESTRAS)
    hacer = lambda nombre: not que or nombre in que  # noqa: E731
    if hacer("planilla"):
        _render_planilla(R, M, relleno, panel, suelo, t)
    if hacer("bandeja"):
        _render_bandeja(R, M, relleno, panel, suelo, t)
    for nombre, rect, mat, alto in (("placa_principal", R["nueva"], M["laton_cepillado"], 0.06),
                                    ("placa_secundaria", R["deshacer"], M["bronce"], 0.05)):
        if hacer(nombre):
            _render_placa(nombre, rect, mat, alto, M, relleno, panel, suelo, t)
    if hacer("cartel"):
        _render_cartel(R, M, relleno, panel, suelo, t)
    if hacer("tarjeta"):
        _render_tarjeta(R, M, relleno, panel, suelo, t)
    if hacer("perilla"):
        _render_perilla(M, relleno, panel, suelo, t)
    return t


def _render_planilla(R, M, relleno, panel, suelo, t):
    objs = planilla(R["planilla"], M)
    wp, hp, a_px = camara_cenital(R["planilla"])
    paper = papel_rect(R["planilla"]); filas, ys, num_x, mid_x = renglones(paper)
    _entrada("planilla", wp, hp, a_px, R["planilla"], papel=[*a_px(paper[0], paper[3]), *a_px(paper[2], paper[1])],
             encabezado=[a_px(0, paper[3])[1], a_px(0, ys[0])[1]], renglones=[a_px(0, y)[1] for y in ys], filas=filas,
             columnas=[a_px(paper[0], 0)[0], a_px(num_x, 0)[0], a_px(mid_x, 0)[0], a_px(paper[2], 0)[0]],
             pie=[a_px(0, ys[-1])[1], a_px(0, paper[1])[1]])
    t["planilla"] = pases(os.path.join(DEST, "planilla"), objs, suelo, relleno, panel); _limpiar(objs)


def _render_bandeja(R, M, relleno, panel, suelo, t):
    """La misma bandeja para los dos lados."""
    rect = R["bandeja_propia"]
    objs = bandeja(rect, M)
    wp, hp, a_px = camara_cenital(rect)
    x0, y0, x1, y1 = rect
    _entrada("bandeja", wp, hp, a_px, rect, fieltro=[*a_px(x0 + 0.08, y1 - 0.08), *a_px(x1 - 0.08, y0 + 0.08)])
    t["bandeja"] = pases(os.path.join(DEST, "bandeja"), objs, suelo, relleno, panel); _limpiar(objs)


def _render_placa(nombre, rect, mat, alto, M, relleno, panel, suelo, t):
    """Placa-botón en 4 estados: principal (latón cepillado) o secundaria (bronce)."""
    objs = placa(nombre, rect, mat, M, alto)
    cuerpo = objs[0]
    wp, hp, a_px = camara_cenital(rect)
    x0, y0, x1, y1 = rect
    _entrada(nombre, wp, hp, a_px, rect, cara=[*a_px(x0 + 0.24, y1 - 0.06), *a_px(x1 - 0.24, y0 + 0.06)])
    estados = {"_normal": _estado(cuerpo, mat, alto, 1.0, 1.4), "_hover": _estado(cuerpo, mat, alto, 1.0, 2.3),
               "_pressed": _estado(cuerpo, mat, alto, 0.55, 1.1),
               "_disabled": _estado(cuerpo, M["apagado"], alto, 1.0, 1.0)}
    sombras = {"": _estado(cuerpo, mat, alto, 1.0, 1.4), "_pressed": _estado(cuerpo, mat, alto, 0.55, 1.4)}
    t[nombre] = pases(os.path.join(DEST, nombre), objs, suelo, relleno, panel, estados, sombras)
    _limpiar(objs)


def _render_cartel(R, M, relleno, panel, suelo, t):
    """Cartel de bronce, sin estados."""
    rect = R["cartel_propio"]
    objs = placa("cartel", rect, M["bronce"], M)
    wp, hp, a_px = camara_cenital(rect)
    x0, y0, x1, y1 = rect
    _entrada("cartel", wp, hp, a_px, rect, cara=[*a_px(x0 + 0.24, y1 - 0.05), *a_px(x1 - 0.24, y0 + 0.05)])
    t["cartel"] = pases(os.path.join(DEST, "cartel"), objs, suelo, relleno, panel); _limpiar(objs)


def _render_tarjeta(R, M, relleno, panel, suelo, t):
    """Tarjeta de fin de partida (se apoya sobre la planilla)."""
    rect = R["tarjeta"]
    objs = tarjeta(rect, M)
    wp, hp, a_px = camara_cenital(rect)
    x0, y0, x1, y1 = rect
    _entrada("tarjeta", wp, hp, a_px, rect, texto=[*a_px(x0 + 0.2, y1 - 0.2), *a_px(x1 - 0.2, y0 + 0.2)])
    t["tarjeta"] = pases(os.path.join(DEST, "tarjeta"), objs, suelo, relleno, panel); _limpiar(objs)


def _render_perilla(M, relleno, panel, suelo, t):
    """Perilla del volumen: normal / hover / pressed."""
    centro, r = esquina_perilla()
    objs = perilla(M, centro, r)
    rect = (centro[0] - r, centro[1] - r, centro[0] + r, centro[1] + r)
    wp, hp, a_px = camara_cenital(rect, margen=0.12, px=PX_PERILLA)
    _entrada("perilla", wp, hp, a_px, rect, px=PX_PERILLA)
    cuerpo, tapa = objs
    t["perilla"] = pases(os.path.join(DEST, "perilla"), objs, suelo, relleno, panel,
                         {"_normal": _estado_perilla(cuerpo, tapa, 0.0, 1.4),
                          "_hover": _estado_perilla(cuerpo, tapa, 0.0, 2.3),
                          "_pressed": _estado_perilla(cuerpo, tapa, 0.03, 0.9)},
                         {"": _estado_perilla(cuerpo, tapa, 0.0, 1.4)})
    _limpiar(objs)


def rey_acostado(color):
    """Copia del rey con la malla acostada (cae hacia la derecha, girado 25°), apoyada en Z = 0 y centrada."""
    src = ESCENA["piezas"][(color, "rey")]
    me = src.data.copy(); me.name = f"{color}_rey_acostado"
    me.transform(Matrix.Rotation(math.radians(25), 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'Y'))
    vs = [v.co for v in me.vertices]
    minz = min(v.z for v in vs)
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2
    me.transform(Matrix.Translation((-cx, -cy, -minz)))
    o = src.copy(); o.data = me; o.name = f"{color}_rey_acostado"  # el material va en el objeto (como el original)
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    bpy.data.collections["Piezas"].objects.link(o)
    if color == "negras":
        bpy.data.collections["Recibe_Contra_Negras"].objects.link(o)
    ESCENA["piezas"][(color, "rey_acostado")] = o
    return o


def _apretar(botones, lado):
    def prep():
        for l, o in botones.items():
            sube = 0.04 if l == lado else 0.12
            o.scale.z = sube / 0.12
            o.location.z = MESA_Z + 0.6 + sube / 2
    return prep


def datos_reloj(objs, lentes, rect):
    """Encuadre del reloj (cámara de 20°) y sus anclas en px: centro de su base, luces y esferas."""
    from bpy_extras.object_utils import world_to_camera_view
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cam = camara_20((cx + 0.2, cy, MESA_Z + 0.3), CLOCK_W + 1.2, 2.0)  # más lugar a la derecha: ahí cae la sombra
    bpy.context.view_layer.update()  # sin esto, la proyección usa la posición vieja de la cámara
    wp, hp = scn.render.resolution_x, scn.render.resolution_y

    def a_px(x, y, z=MESA_Z):
        v = world_to_camera_view(scn, cam, Vector((x, y, z)))
        return [round(v.x * wp, 1), round((1 - v.y) * hp, 1)]
    frente = cy - 0.375
    DATOS["reloj"] = dict(px_por_casilla=PX, tamaño=[wp, hp], ancla=a_px(cx, cy), camara="20 grados",
                          izquierda="blancas", derecha="negras",
                          caja=[*a_px(x0, cy - 0.375, MESA_Z + 0.6), *a_px(x1, cy - 0.375, MESA_Z)],
                          luces={lado: a_px(l.location.x, l.location.y, l.location.z) for lado, l in lentes.items()},
                          esferas={lado: a_px(cx + (-0.6 if lado == "blancas" else 0.6), frente, MESA_Z + 0.36)
                                   for lado in ("blancas", "negras")})


def render_volumen(M, relleno, panel, suelo):
    os.makedirs(DEST, exist_ok=True)
    R = rectangulos(); t = {}
    base(MUESTRAS)
    objs, lentes = reloj(R["reloj"], M)  # con los dos botones arriba (0,12): los estados los escalan
    datos_reloj(objs, lentes, R["reloj"])
    botones = {lado: next(o for o in objs if o.name == f"Reloj_Boton_{lado}") for lado in ("blancas", "negras")}
    ruta = os.path.join(DEST, "reloj")
    bpy.data.objects["Frente_Interfaz"].hide_render = False
    t["reloj"] = pases(ruta, objs, suelo, relleno, panel,
                       {"_blancas": _apretar(botones, "blancas"), "_negras": _apretar(botones, "negras"),
                        "_parejos": _apretar(botones, None)},
                       {"": _apretar(botones, None)})
    # luces: sólo la lente encendida; el resto del reloj la tapa (holdout) donde corresponde
    _apretar(botones, None)()
    lente_mat = M["lente"]
    for lado, lente in lentes.items():
        for o in objs:
            o.is_holdout = o is not lente
        lente.data.materials[0] = M["luz"]
        solo(objs); _luces_cuerpo(relleno, panel); scn.render.film_transparent = True
        t[f"luz_{lado}"] = _render(f"{ruta}_luz_{lado}.png")
        lente.data.materials[0] = lente_mat
    for o in objs:
        o.is_holdout = False
    bpy.data.objects["Frente_Interfaz"].hide_render = True
    _limpiar(objs)
    # rey acostado (jaque mate): los mismos pases que las piezas
    for color in ("blancas", "negras"):
        rey_acostado(color)
    scn.render.resolution_percentage = 100
    t["reyes"] = render_sprites(DEST, MUESTRAS, piezas=[("blancas", "rey_acostado"), ("negras", "rey_acostado")])
    for color in ("blancas", "negras"):  # acostado es más ancho que una pieza parada: el contacto llega al borde
        for pase in ("_sombra", "_contacto"):
            _desvanecer(os.path.join(DEST, f"{color}_rey_acostado{pase}.png"), 40)
    DATOS["rey_acostado"] = dict(px_por_casilla=round(SPRITE_PX / SPRITE_ESCALA, 2), tamaño=[SPRITE_PX, SPRITE_PX],
                                 ancla=[256.0, 445.4], reflejo_ancla=[256.0, 51.2], camara="20 grados (la de las piezas)")
    return t


# ---------------- Revisión ----------------
def revisar():
    """interfaz.json (anclas y rectángulos en px de cada PNG) y revisión de alfas: nada cortado en los bordes, nada
    vacío. Lo que falle queda en `revision` del JSON y se imprime."""
    informe = {}
    for nombre in sorted(os.listdir(DEST)):
        if not nombre.endswith(".png"):
            continue
        a = _px(os.path.join(DEST, nombre))[..., 3]
        borde = max(a[0].max(), a[-1].max(), a[:, 0].max(), a[:, -1].max())
        informe[nombre] = dict(alfa_max=round(float(a.max()), 3), borde=round(float(borde), 3),
                               ok=bool(a.max() > 0.02 and borde < 0.02))
        filas, cols = (a >= 0.5).any(axis=1).nonzero()[0], (a >= 0.5).any(axis=0).nonzero()[0]
        if len(filas):  # la imagen de Blender está de abajo hacia arriba
            h = a.shape[0]
            informe[nombre]["visible"] = [int(cols[0]), int(h - 1 - filas[-1]), int(cols[-1] + 1), int(h - filas[0])]
    malos = {k: v for k, v in informe.items() if not v["ok"]}
    print(f"revisión de alfas: {len(informe)} PNG, {len(malos)} con problemas: {malos}")
    previo = {}
    ruta = os.path.join(DEST, "interfaz.json")
    if os.path.exists(ruta):
        previo = json.load(open(ruta, encoding="utf-8"))
    datos = {**previo.get("sprites", {}), **DATOS}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(dict(unidades="px de cada PNG, origen arriba a la izquierda; ancla = centro del objeto apoyado en "
                                "la mesa; objeto = caja del objeto (x0, y0, x1, y1)",
                       sprites=datos, revision=informe), f, ensure_ascii=False, indent=1)
    return malos


# ---------------- Mock (fase A) ----------------
def render_mock(ruta=os.path.join(AQUI, "previews", "interfaz_mock.png"), muestras=32, porcentaje=50):
    M, (relleno, panel), suelo = preparar()
    R = rectangulos()
    objs = planilla(R["planilla"], M) + reloj(R["reloj"], M, "blancas")[0]
    objs += bandeja(R["bandeja_rival"], M) + bandeja(R["bandeja_propia"], M)
    for nombre in ("cartel_rival", "cartel_propio", "deshacer", "menu"):
        objs += placa(nombre, R[nombre], M["bronce"], M)
    objs += placa("nueva", R["nueva"], M["laton"], M, alto=0.06)
    centro, r = esquina_perilla()
    objs += perilla(M, centro, r)
    w, h = VENTANA_PX
    total = BOARD + GAP + TRAY + GAP + COL
    base(muestras)
    _luces_cuerpo(relleno, panel)
    cam = ESCENA["camaras"]["cenital"]
    cam.location = (total / 2 - BOARD / 2, 0, 30); cam.data.ortho_scale = w / CASILLA_PX
    cam.data.sensor_fit = 'HORIZONTAL'; scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = w, h
    scn.render.resolution_percentage = porcentaje
    scn.render.film_transparent = False
    solo(list(ESCENA["tablero"]) + [ESCENA["mesa"]] + objs)
    print(f"mock: {ruta} en {_render(ruta)} s")


# ---------------- Main ----------------
ESCENA = escena_existente()
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
_modo = _argv[0] if _argv else ""
if len(_argv) > 1:  # pruebas: -- <modo> <muestras> <carpeta>
    MUESTRAS = int(_argv[1])
if len(_argv) > 2:
    DEST = _argv[2]
if _modo == "mock":
    render_mock()
elif _modo == "revisar":
    revisar()
elif _modo == "anclas":  # recalcula las anclas del reloj sin renderizar
    M, _, _ = preparar()
    _objs, _lentes = reloj(rectangulos()["reloj"], M)
    datos_reloj(_objs, _lentes, rectangulos()["reloj"])
    revisar()
else:
    M, (relleno, panel), suelo = preparar()
    print("relleno calibrado:", round(calibrar_relleno(relleno, panel, M, rectangulos()["planilla"]), 1))
    tiempos = {}
    if _modo in ("", "planos"):
        tiempos.update(render_planos(M, relleno, panel, suelo))
    elif _modo != "volumen":  # -- placa_principal,bandeja,...: sólo esos objetos planos
        tiempos.update(render_planos(M, relleno, panel, suelo, set(_modo.split(","))))
    if _modo in ("", "volumen"):
        tiempos.update(render_volumen(M, relleno, panel, suelo))
    revisar()
    print("tiempos:", tiempos)
