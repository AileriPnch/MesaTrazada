"""Escena de Blender del ajedrez: piezas Staunton, tablero de pizarra laqueada y mesa de nogal.

Uso (desde Blender, con un archivo vacío o con blender/ajedrez.blend abierto):
    PROYECTO = r"<proyecto>"   # sólo hace falta con un archivo vacío (si no, se deduce del .blend abierto)
    exec(open(r"<proyecto>/blender/generar_ajedrez.py", encoding="utf-8").read())
Reconstruye todo desde cero (borra lo que haya en el archivo) y guarda blender/ajedrez.blend. Después:
    render_preview()                      -> blender/previews/ajedrez_preview.png (cámara de las piezas)
    render_sprites(dest, muestras, piezas) -> {color}_{pieza}{,_sombra,_contacto,_reflejo,_brillo}.png
    render_tablero(dest, px, muestras)     -> tablero.png (cenital, con marco, fondo transparente)
    render_mesa(dest, res, muestras)       -> mesa.png (cenital, sin tablero)
    export_all()                          -> todo lo anterior a assets/ajedrez/ con la calidad final

Unidades: 1 unidad de Blender = 1 casilla. Origen: centro del tablero, sobre la superficie de las casillas.
+X a la derecha, +Y hacia las negras (arriba en la vista cenital), +Z arriba. Cada pieza tiene el origen en el
centro de su base, apoyado en Z = 0. Sin texturas externas: la madera es procedural.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Euler

# ---------------- Parámetros ----------------
def _raiz_del_proyecto():
    """La carpeta del proyecto, sin rutas fijas: un PROYECTO definido antes del exec(), la ubicación de este script
    (blender -P, o desde generar_interfaz.py) o la del .blend abierto (blender/ajedrez.blend)."""
    if globals().get("PROYECTO"):
        return globals()["PROYECTO"]
    if "__file__" in globals():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if bpy.data.filepath:
        return os.path.dirname(os.path.dirname(bpy.data.filepath))
    raise RuntimeError('Definí PROYECTO = r"<carpeta del proyecto>" antes de exec(...)')


PROYECTO = _raiz_del_proyecto()
BLEND = os.path.join(PROYECTO, "blender", "ajedrez.blend")
PREVIEWS = os.path.join(PROYECTO, "blender", "previews")
EXPORT_DIR = os.path.join(PROYECTO, "assets", "ajedrez")

INCLINACION_PIEZAS = 20.0   # grados hacia abajo de la cámara de las piezas
SPRITE_PX = 512             # sprites cuadrados de 512 x 512
SPRITE_ESCALA = 1.20        # lado visible del sprite en casillas -> 1 casilla = 512 / 1,2 = 426,67 px
SPRITE_APOYO_V = 0.13       # el apoyo (centro de la base) queda a 13 % del alto desde abajo
REFLEJO_APOYO_V = 0.90      # en los reflejos el apoyo queda arriba (el reflejo cuelga hacia abajo)
TABLERO_PX = 2048
MARCO = 0.20                # ancho del marco en casillas (BoardLook.frame)
MESA_PX = (3840, 2880)      # 4:3; para 16:9 se recorta arriba y abajo
MESA_ANCHO = 16.0           # casillas visibles a lo ancho en mesa.png
MUESTRAS_PIEZAS = 1024
MUESTRAS_TABLERO = 1024
LACA_ROUGH = 0.06           # laca del tablero para el pase de reflejo
BRILLO_UMBRAL = 0.30        # luminancia lineal desde la que un especular cuenta como "fuerte"
SOMBRA_FUERZA = 0.62        # opacidad del núcleo de la sombra proyectada
CONTACTO_FUERZA = 0.90      # opacidad máxima de la oclusión de contacto

# Luz: principal arriba a la izquierda (sombra abajo a la derecha), relleno bajo, contraluces atrás a la derecha
LUZ_PRINCIPAL_DIR = Vector((-1.0, 0.35, 1.85))
LUZ_RELLENO_DIR = Vector((0.5, -1.0, 0.5))
LUZ_CONTRA_DIR = Vector((1.0, 1.1, 0.45))
LUZ_CONTRA_NEGRAS_DIR = Vector((1.0, 0.85, 0.30))
LAMPARA_POS = (-3.0, 3.0, 13.0)
LAMPARA_MIRA = (-0.6, 0.6, 0.0)
DISCO_LAMPARA = dict(centro=(-2.4, 2.4, 8.0), radio=2.6, fuerza=1.6)   # sólo se ve en los reflejos de la laca

# Colores de src/common/theme.py
C = dict(
    ivory_piece="#e6dac2", lacquer_piece="#2b2622",
    square_light="#5d6574", square_dark="#2b3140", board_frame="#14171d", board_edge="#0a0807",
    wood_deep="#0d0a08", wood="#1b1410", wood_grain="#3b2a1d", lamp="#ffe3b8",
    lamp_luz="#fff6ec",   # la luz que tira la lámpara: cálida pero sin comerse el azul de la pizarra
)

scn = bpy.context.scene

def lin(hexs):
    h = hexs.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)

def sock(nodo, ident):
    for s in nodo.inputs:
        if s.identifier == ident:
            return s
    return None

def setv(nodo, ident, v):
    s = sock(nodo, ident)
    if s is not None:
        s.default_value = v

# ---------------- Limpieza ----------------
def limpiar():
    if bpy.data.filepath and not bpy.data.filepath.lower().endswith("ajedrez.blend") and bpy.data.is_dirty:
        raise RuntimeError("Hay otro archivo abierto con cambios sin guardar: guardalo o abrí uno vacío.")
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
                 bpy.data.curves, bpy.data.node_groups, bpy.data.images):
        for d in list(coll):
            coll.remove(d)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for w in list(bpy.data.worlds):
        if w != scn.world:
            bpy.data.worlds.remove(w)

def coleccion(nombre, enlazar=True):
    c = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    if enlazar and c.name not in scn.collection.children:
        scn.collection.children.link(c)
    return c

# ---------------- Materiales ----------------
def principled(nombre, color, rough, coat=0.0, coat_rough=0.05, sss=0.0, spec=0.5):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    setv(b, "Base Color", lin(color) if isinstance(color, str) else color)
    setv(b, "Roughness", rough); setv(b, "Specular IOR Level", spec)
    setv(b, "Coat Weight", coat); setv(b, "Coat Roughness", coat_rough); setv(b, "Coat IOR", 1.5)
    if sss:
        setv(b, "Subsurface Weight", sss); setv(b, "Subsurface Radius", (0.10, 0.06, 0.03))
        setv(b, "Subsurface Scale", 0.04)
    return m

class Nodos:
    """Atajos para armar árboles de nodos."""
    def __init__(self, nt):
        self.nt = nt
    def n(self, tipo, **props):
        nd = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd
    def link(self, salida, entrada):
        if hasattr(salida, "is_output"):
            self.nt.links.new(salida, entrada)
        else:
            entrada.default_value = salida
    def math(self, op, a, b=0.0, c=None):
        nd = self.n("ShaderNodeMath", operation=op)
        self.link(a, nd.inputs[0]); self.link(b, nd.inputs[1])
        if c is not None:
            self.link(c, nd.inputs[2])
        return nd.outputs[0]
    def vmath(self, op, a, b=(0, 0, 0), escala=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self.link(a, nd.inputs[0]); self.link(b, nd.inputs[1])
        if escala is not None:
            self.link(escala, nd.inputs[3])
        return nd.outputs["Value"] if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else nd.outputs[0]
    def rampa(self, fac, paradas):
        nd = self.n("ShaderNodeValToRGB"); self.link(fac, nd.inputs["Fac"])
        el = nd.color_ramp.elements
        el[0].position, el[0].color = paradas[0]
        el[1].position, el[1].color = paradas[-1]
        for pos, col in paradas[1:-1]:
            e = el.new(pos); e.color = col
        return nd.outputs["Color"]

ALTO_TABLA = 1.35      # casillas
LARGO_TABLA = 7.0

def material_madera():
    """Nogal laqueado: vetas irregulares (wave deformada por noise), grano distinto en cada tabla,
    figura, poros finos estirados a lo largo de la tabla y juntas."""
    m = bpy.data.materials.new("Nogal_Mesa"); m.use_nodes = True
    N = Nodos(m.node_tree)
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    tc = N.n("ShaderNodeTexCoord")
    sep = N.n("ShaderNodeSeparateXYZ"); N.link(tc.outputs["Object"], sep.inputs[0])
    fila = N.math('FLOOR', N.math('DIVIDE', sep.outputs["Y"], ALTO_TABLA))
    comb = N.n("ShaderNodeCombineXYZ")
    N.link(fila, comb.inputs[0]); N.link(N.math('MULTIPLY', fila, 7.31), comb.inputs[1]); N.link(0.5, comb.inputs[2])
    azar = N.n("ShaderNodeTexWhiteNoise", noise_dimensions='3D'); N.link(comb.outputs[0], azar.inputs["Vector"])
    # grano propio de cada tabla: corrimiento grande de las coordenadas
    p = N.vmath('ADD', tc.outputs["Object"], N.vmath('SCALE', azar.outputs["Color"], escala=37.0))
    estira = N.n("ShaderNodeMapping"); N.link(p, estira.inputs["Vector"])
    estira.inputs["Scale"].default_value = (0.11, 1.0, 1.0)
    ruido = N.n("ShaderNodeTexNoise"); N.link(estira.outputs[0], ruido.inputs["Vector"])
    ruido.inputs["Scale"].default_value = 1.8; ruido.inputs["Detail"].default_value = 7.0
    ruido.inputs["Roughness"].default_value = 0.58
    q = N.vmath('ADD', estira.outputs[0],
                N.vmath('SCALE', N.vmath('SUBTRACT', ruido.outputs["Color"], (0.5, 0.5, 0.5)), escala=0.85))
    onda = N.n("ShaderNodeTexWave", wave_type='BANDS', bands_direction='Y', wave_profile='SAW')
    N.link(q, onda.inputs["Vector"]); onda.inputs["Scale"].default_value = 3.4
    onda.inputs["Distortion"].default_value = 5.0; onda.inputs["Detail"].default_value = 3.0
    onda.inputs["Detail Scale"].default_value = 1.8; onda.inputs["Detail Roughness"].default_value = 0.62
    veta = N.math('POWER', onda.outputs["Fac"], 1.8)
    color = N.rampa(veta, [(0.0, lin("#0b0806")), (0.35, lin(C["wood"])), (0.75, lin("#2f2016")),
                           (1.0, lin("#4a3122"))])
    # figura: manchas grandes más claras/oscuras
    fig = N.n("ShaderNodeTexNoise"); N.link(estira.outputs[0], fig.inputs["Vector"])
    fig.inputs["Scale"].default_value = 0.5; fig.inputs["Detail"].default_value = 3.0
    k_fig = N.math('MULTIPLY_ADD', fig.outputs["Fac"], 0.80, 0.62)
    # tono propio de cada tabla
    k_tabla = N.math('MULTIPLY_ADD', azar.outputs["Value"], 0.30, 0.82)
    # poros: ruido muy fino, estirado a lo largo de X
    pmap = N.n("ShaderNodeMapping"); N.link(p, pmap.inputs["Vector"])
    pmap.inputs["Scale"].default_value = (6.0, 140.0, 6.0)
    poro_n = N.n("ShaderNodeTexNoise"); N.link(pmap.outputs[0], poro_n.inputs["Vector"])
    poro_n.inputs["Scale"].default_value = 1.0; poro_n.inputs["Detail"].default_value = 2.0
    poro = N.n("ShaderNodeMapRange"); N.link(poro_n.outputs["Fac"], poro.inputs["Value"])
    poro.inputs["From Min"].default_value = 0.60; poro.inputs["From Max"].default_value = 0.72
    k_poro = N.math('MULTIPLY_ADD', poro.outputs["Result"], -0.40, 1.0)
    # juntas: a lo largo (entre filas) y a lo ancho (fin de cada tabla, corrido por fila)
    fy = N.math('FRACT', N.math('DIVIDE', sep.outputs["Y"], ALTO_TABLA))
    dy = N.math('MULTIPLY', N.math('MINIMUM', fy, N.math('SUBTRACT', 1.0, fy)), ALTO_TABLA)
    fx = N.math('FRACT', N.math('DIVIDE', N.math('MULTIPLY_ADD', azar.outputs["Value"], LARGO_TABLA, sep.outputs["X"]),
                                 LARGO_TABLA))
    dx = N.math('MULTIPLY', N.math('MINIMUM', fx, N.math('SUBTRACT', 1.0, fx)), LARGO_TABLA)
    junta = N.math('SMOOTH_MIN', N.math('SMOOTH_MIN', dy, dx, 0.002), 1.0, 0.0)
    k_junta = N.n("ShaderNodeMapRange"); N.link(junta, k_junta.inputs["Value"])
    k_junta.inputs["From Min"].default_value = 0.0; k_junta.inputs["From Max"].default_value = 0.012
    k_junta.inputs["To Min"].default_value = 0.25; k_junta.inputs["To Max"].default_value = 1.0
    k = N.math('MULTIPLY', N.math('MULTIPLY', k_fig, k_tabla), N.math('MULTIPLY', k_poro, k_junta.outputs["Result"]))
    final = N.vmath('SCALE', color, escala=k)
    N.link(final, b.inputs["Base Color"])
    N.link(N.math('MULTIPLY_ADD', poro.outputs["Result"], 0.25, 0.36), b.inputs["Roughness"])
    bump = N.n("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.18; bump.inputs["Distance"].default_value = 0.004
    N.link(N.math('MULTIPLY', poro.outputs["Result"], k_junta.outputs["Result"]), bump.inputs["Height"])
    N.link(bump.outputs["Normal"], b.inputs["Normal"])
    setv(b, "Coat Weight", 0.5); setv(b, "Coat Roughness", 0.09)
    return m

def materiales():
    return {
        # marfil: laca sobre un cuerpo con algo de subsurface; ébano: especular fuerte bajo una laca nítida
        "blancas": principled("Marfil_Laqueado", C["ivory_piece"], 0.38, coat=0.65, coat_rough=0.05, sss=0.25),
        "negras": principled("Ebano_Laqueado", C["lacquer_piece"], 0.28, coat=1.0, coat_rough=0.03, spec=0.75),
        # pizarra y marco: clearcoat nítido encima, pizarra mate debajo (sin especular propio: el brillo es de la laca)
        "clara": principled("Pizarra_Clara", C["square_light"], 0.65, coat=1.0, coat_rough=0.05, spec=0.0),
        "oscura": principled("Pizarra_Oscura", C["square_dark"], 0.65, coat=1.0, coat_rough=0.05, spec=0.0),
        "marco": principled("Marco_Laqueado", C["board_frame"], 0.35, coat=1.0, coat_rough=0.03, spec=0.8),
        "madera": material_madera(),
    }

# ---------------- Perfiles torneados ----------------
class Perfil:
    """Perfil (radio, altura) de abajo hacia arriba: tramos rectos y curvas cuadráticas."""
    def __init__(self):
        self.p = [(0.0, 0.0)]
    def l(self, r, z):
        self.p.append((r, z)); return self
    def q(self, cr, cz, r, z, n=7):
        r0, z0 = self.p[-1]
        for i in range(1, n + 1):
            t = i / n; a, b2, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
            self.p.append((a * r0 + b2 * cr + c * r, a * z0 + b2 * cz + c * z))
        return self

def base(R):
    """Base Staunton: plinto redondeado, toro grueso, escocia y anillo fino."""
    P = Perfil()
    P.l(R - 0.010, 0).q(R, 0, R, 0.010)
    P.l(R, 0.020).q(R, 0.031, R - 0.013, 0.032)
    P.l(R * 0.93, 0.034)
    P.q(R * 1.00, 0.046, R * 0.91, 0.061)            # toro
    P.q(R * 0.78, 0.065, R * 0.77, 0.075)            # escocia
    P.q(R * 0.85, 0.081, R * 0.77, 0.093)            # anillo fino
    P.l(R * 0.68, 0.097)
    return P

def collar(P, r_tallo, r1, z, r2=None):
    """Collar doble marcado: disco ancho + anillo chico encima. Devuelve la altura final."""
    P.q(r_tallo, z + 0.006, r1 - 0.006, z + 0.008).q(r1 + 0.008, z + 0.015, r1 - 0.004, z + 0.027)
    P.q(r1 - 0.02, z + 0.033, r_tallo + 0.004, z + 0.035)
    if r2:
        P.q(r2 + 0.006, z + 0.039, r2 - 0.004, z + 0.048).q(r2 - 0.01, z + 0.054, r_tallo - 0.004, z + 0.056)
        return z + 0.056
    return z + 0.035

def perfil_peon():
    P = base(0.21)
    P.q(0.100, 0.105, 0.088, 0.16).l(0.064, 0.290)
    z = collar(P, 0.064, 0.128, 0.290)
    P.l(0.050, z + 0.012)
    P.q(0.120, z + 0.022, 0.113, z + 0.115).q(0.106, z + 0.212, 0.030, z + 0.226).l(0, z + 0.228)
    return P.p

def perfil_torre():
    P = base(0.24)
    P.q(0.150, 0.105, 0.145, 0.155).l(0.134, 0.395)                         # cuerpo ancho y recto
    P.q(0.134, 0.403, 0.152, 0.405).q(0.164, 0.410, 0.160, 0.424).q(0.156, 0.434, 0.138, 0.436)  # anillo
    P.q(0.152, 0.455, 0.176, 0.468).l(0.178, 0.578).q(0.178, 0.590, 0.166, 0.590)            # corona
    P.l(0.130, 0.590).q(0.122, 0.590, 0.122, 0.580).l(0.122, 0.545).l(0, 0.545)
    return P.p

def perfil_alfil():
    P = base(0.23)
    P.q(0.108, 0.105, 0.096, 0.16).l(0.060, 0.345)                          # tallo fino
    z = collar(P, 0.060, 0.124, 0.345, 0.090)
    P.l(0.052, z + 0.004)
    P.q(0.104, z + 0.030, 0.100, z + 0.100).q(0.096, z + 0.170, 0.042, z + 0.215)   # mitra alta en punta
    P.q(0.026, z + 0.224, 0.018, z + 0.226).l(0.014, z + 0.230)
    P.q(0.030, z + 0.232, 0.029, z + 0.250).q(0.027, z + 0.272, 0, z + 0.273)       # bolita
    return P.p

def perfil_dama():
    P = base(0.25)
    P.q(0.118, 0.105, 0.106, 0.16).l(0.072, 0.360)
    z = collar(P, 0.072, 0.138, 0.360, 0.100)
    P.q(0.074, z + 0.06, 0.112, z + 0.135).q(0.136, z + 0.165, 0.152, z + 0.182)     # copa que se abre
    P.q(0.160, z + 0.190, 0.150, z + 0.198)                                          # labio de la corona
    P.q(0.118, z + 0.202, 0.088, z + 0.204)
    P.q(0.068, z + 0.218, 0.050, z + 0.230).q(0.030, z + 0.238, 0.020, z + 0.241)    # domo
    P.l(0.015, z + 0.245).q(0.032, z + 0.247, 0.030, z + 0.262).q(0.028, z + 0.285, 0, z + 0.286)   # bolita
    return P.p, z + 0.198

def perfil_rey():
    P = base(0.26)
    P.q(0.124, 0.105, 0.112, 0.16).l(0.076, 0.372)
    z = collar(P, 0.076, 0.144, 0.372, 0.104)
    P.q(0.078, z + 0.06, 0.114, z + 0.125).q(0.134, z + 0.150, 0.140, z + 0.160)
    P.q(0.148, z + 0.168, 0.138, z + 0.176)
    P.q(0.108, z + 0.180, 0.078, z + 0.183).q(0.050, z + 0.195, 0.036, z + 0.200).l(0.034, z + 0.206).l(0, z + 0.206)
    return P.p, z + 0.200

def perfil_caballo_base():
    P = base(0.24)
    P.q(0.150, 0.100, 0.150, 0.116).q(0.152, 0.130, 0.140, 0.136).l(0, 0.136)
    return P.p

# Silueta de la cabeza del caballo (x, z), de perfil mirando a la izquierda (-X)
CABALLO = [(0.175, 0.120), (0.200, 0.200), (0.205, 0.280), (0.195, 0.360), (0.170, 0.440), (0.130, 0.510),
           (0.085, 0.565), (0.040, 0.595), (-0.020, 0.590), (-0.085, 0.560), (-0.150, 0.510), (-0.205, 0.462),
           (-0.240, 0.430), (-0.256, 0.405), (-0.250, 0.380), (-0.232, 0.368), (-0.205, 0.372), (-0.216, 0.352),
           (-0.196, 0.335), (-0.140, 0.325), (-0.090, 0.335), (-0.058, 0.315), (-0.064, 0.270), (-0.095, 0.215),
           (-0.125, 0.165), (-0.140, 0.120)]

# ---------------- Construcción de mallas ----------------
def objeto_temporal(nombre, me):
    o = bpy.data.objects.new(nombre, me); scn.collection.objects.link(o); return o

def tornear(nombre, perfil):
    me = bpy.data.meshes.new(nombre + "_perfil")
    vs = [(r, 0, z) for r, z in perfil]
    me.from_pydata(vs, [(i, i + 1) for i in range(len(vs) - 1)], [])
    o = objeto_temporal(nombre + "_tmp", me)
    sc = o.modifiers.new("Screw", "SCREW"); sc.axis = 'Z'; sc.steps = 96; sc.render_steps = 96
    sc.use_merge_vertices = True; sc.merge_threshold = 1e-4; sc.use_smooth_shade = True
    try:
        sc.use_normal_calculate = True
    except AttributeError:
        pass
    return o

def cortar(o, cutters):
    for i, c in enumerate(cutters):
        c.hide_render = True; c.display_type = 'WIRE'
        b = o.modifiers.new(f"Corte{i}", "BOOLEAN"); b.operation = 'DIFFERENCE'; b.object = c; b.solver = 'EXACT'

def caja(nombre, size, loc, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o = objeto_temporal(nombre, me); o.scale = size; o.location = loc; o.rotation_euler = rot
    return o

def esfera(nombre, r, loc, seg=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = objeto_temporal(nombre, me); o.location = loc
    return o

def hornear(nombre, objs, sharp_deg=48):
    """Aplica los modificadores, une los objetos en una malla final y la sombrea suave salvo aristas vivas."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    final = bpy.data.meshes.new(nombre); bm.to_mesh(final); bm.free()
    final.shade_smooth()
    if sharp_deg is not None:
        try:
            final.set_sharp_from_angle(angle=math.radians(sharp_deg))
        except AttributeError:
            pass
    return final

def borrar(objs):
    for o in objs:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)

def pieza_peon():
    o = tornear("peon", perfil_peon()); me = hornear("Peon", [o]); borrar([o]); return me

def pieza_torre():
    o = tornear("torre", perfil_torre())
    cs = [caja(f"almena{i}", (0.44, 0.056, 0.12), (0, 0, 0.60), (0, 0, math.radians(60 * i))) for i in range(3)]
    cortar(o, cs); me = hornear("Torre", [o]); borrar([o] + cs); return me

def pieza_alfil():
    o = tornear("alfil", perfil_alfil())
    c = caja("corte_mitra", (0.20, 0.40, 0.030), (0.035, 0, 0.535), (0, math.radians(-38), 0))
    cortar(o, [c]); me = hornear("Alfil", [o]); borrar([o, c]); return me

def pieza_dama():
    perfil, z_labio = perfil_dama()
    o = tornear("dama", perfil)
    n = 9; cs, bolas = [], []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        cs.append(esfera(f"feston{i}", 0.044, (0.168 * math.cos(a), 0.168 * math.sin(a), z_labio + 0.046)))
        a = 2 * math.pi * i / n
        bolas.append(esfera(f"bolita{i}", 0.021, (0.150 * math.cos(a), 0.150 * math.sin(a), z_labio + 0.010), 24))
    cortar(o, cs)
    me = hornear("Dama", [o] + bolas); borrar([o] + cs + bolas); return me

def pieza_rey():
    perfil, z_top = perfil_rey()
    o = tornear("rey", perfil)
    alto = 0.755 - z_top
    v = caja("cruz_v", (0.046, 0.046, alto + 0.01), (0, 0, z_top - 0.005 + (alto + 0.01) / 2))
    h = caja("cruz_h", (0.118, 0.046, 0.044), (0, 0, z_top + alto * 0.58))
    for c in (v, h):
        bv = c.modifiers.new("Bevel", "BEVEL"); bv.width = 0.007; bv.segments = 3
    me = hornear("Rey", [o, v, h]); borrar([o, v, h]); return me

def _poligono_extruido(nombre, pts, espesor, bisel=0.0, segmentos=3):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([(x, 0, z) for x, z in pts], [], [list(range(len(pts)))])
    o = objeto_temporal(nombre, me)
    so = o.modifiers.new("Solidify", "SOLIDIFY"); so.thickness = espesor; so.offset = 0.0
    if bisel:
        o.modifiers.new("Tri", "TRIANGULATE")
        bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = bisel; bv.segments = segmentos
        bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
    return o

def _crin():
    """Tira dentada sobre la nuca y el cuello (la crin tallada), en el plano medio de la cabeza."""
    tramo = CABALLO[1:7][::-1]          # de la nuca hacia abajo
    # remuestreo
    import itertools
    seg = list(zip(tramo[:-1], tramo[1:]))
    largos = [math.dist(a, b) for a, b in seg]; total = sum(largos)
    N = 48; pts = []
    for k in range(N + 1):
        s = total * k / N
        for (a, b), L_ in zip(seg, largos):
            if s <= L_ or (a, b) == seg[-1]:
                t = min(1.0, s / L_) if L_ else 0
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)); break
            s -= L_
    centro = (0.0, 0.38)
    afuera, adentro = [], []
    for k, p in enumerate(pts):
        a = pts[max(0, k - 1)]; b = pts[min(N, k + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]; L_ = math.hypot(dx, dz) or 1
        nx, nz = dz / L_, -dx / L_
        if (p[0] - centro[0]) * nx + (p[1] - centro[1]) * nz < 0:
            nx, nz = -nx, -nz
        s = k / N
        diente = abs(((s * 9) % 1.0) * 2 - 1)            # 9 mechones
        env = math.sin(math.pi * min(1.0, s * 1.15)) ** 0.6
        off = (0.010 + 0.026 * diente) * env
        afuera.append((p[0] + nx * off, p[1] + nz * off))
        adentro.append((p[0] - nx * 0.035, p[1] - nz * 0.035))
    return _poligono_extruido("crin", afuera + adentro[::-1], 0.085, bisel=0.008)

def pieza_caballo():
    b = tornear("caballo_base", perfil_caballo_base())
    cab = _poligono_extruido("cabeza", CABALLO, 0.205)
    rm = cab.modifiers.new("Remesh", "REMESH"); rm.mode = 'VOXEL'; rm.voxel_size = 0.0045
    sm = cab.modifiers.new("Suavizar", "SMOOTH"); sm.factor = 0.6; sm.iterations = 10
    cabeza = hornear("cabeza_hor", [cab], sharp_deg=None); borrar([cab])
    # volumen: el hocico más angosto que el cuello, la frente un poco más angosta que las mejillas
    for v in cabeza.vertices:
        if v.co.z > 0.14:
            t = min(1.0, max(0.0, (v.co.x + 0.256) / 0.30))
            k = 0.58 + 0.42 * t
            if v.co.z > 0.52:
                k *= 0.92
            v.co.y *= k
    oc = objeto_temporal("cabeza_obj", cabeza)
    cortes = [esfera(f"ojo{s}", 0.021, (-0.068, s * 0.096, 0.505)) for s in (-1, 1)]
    cortes += [esfera(f"narina{s}", 0.017, (-0.238, s * 0.062, 0.410)) for s in (-1, 1)]
    cortes.append(caja("boca", (0.075, 0.40, 0.009), (-0.228, 0, 0.371), (0, math.radians(-8), 0)))
    cortes.append(caja("mejilla", (0.09, 0.40, 0.006), (-0.10, 0, 0.395), (0, math.radians(32), 0)))
    cortar(oc, cortes)
    crin = _crin()
    orejas = []
    for s in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.030, radius2=0.004, depth=0.075)
        me = bpy.data.meshes.new("oreja"); bm.to_mesh(me); bm.free()
        o = objeto_temporal("oreja", me); o.location = (0.030, s * 0.040, 0.600)
        o.rotation_euler = (math.radians(-12 * s), math.radians(-14), 0)
        sm2 = o.modifiers.new("Sub", "SUBSURF"); sm2.levels = sm2.render_levels = 1
        orejas.append(o)
    final = hornear("Caballo", [b, oc, crin] + orejas, sharp_deg=55)
    borrar([b, oc, crin] + orejas + cortes)   # borra también la malla intermedia de la cabeza
    return final

def construir_piezas(M):
    col = coleccion("Piezas")
    mallas = {"peon": pieza_peon(), "torre": pieza_torre(), "alfil": pieza_alfil(),
              "dama": pieza_dama(), "rey": pieza_rey(), "caballo": pieza_caballo()}
    for me in mallas.values():
        me.materials.append(M["blancas"])
    objs = {}
    negras = coleccion("Recibe_Contra_Negras", enlazar=False)
    for color in ("blancas", "negras"):
        for nombre, me in mallas.items():
            o = bpy.data.objects.new(f"{color}_{nombre}", me); col.objects.link(o)
            o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = M[color]
            if color == "negras":
                negras.objects.link(o)
            objs[(color, nombre)] = o
    return mallas, objs

# ---------------- Tablero y mesa ----------------
# Perfil del marco: (distancia hacia afuera desde el borde de las casillas, altura)
PERFIL_MARCO = [(0.000, -0.003), (0.000, 0.003), (0.006, 0.010), (0.014, 0.018), (0.026, 0.024), (0.045, 0.030),
                (0.075, 0.035), (0.105, 0.037), (0.135, 0.035), (0.160, 0.029), (0.178, 0.020), (0.191, 0.008),
                (0.198, -0.006), (0.200, -0.030), (0.200, -0.300)]

def construir_tablero(M):
    col = coleccion("Tablero")
    me = bpy.data.meshes.new("Casillas")
    vs, fs, mats = [], [], []
    for j in range(9):
        for i in range(9):
            vs.append((i - 4.0, j - 4.0, 0.0))
    for j in range(8):
        for i in range(8):
            a = j * 9 + i
            fs.append((a, a + 1, a + 10, a + 9)); mats.append(0 if (i + j) % 2 == 0 else 1)  # a1 oscura
    me.from_pydata(vs, [], fs)
    me.materials.append(M["oscura"]); me.materials.append(M["clara"])
    for p, mi in zip(me.polygons, mats):
        p.material_index = mi
    cas = bpy.data.objects.new("Casillas", me); col.objects.link(cas)
    # marco barrido: un anillo cuadrado por cada punto del perfil (esquinas a inglete)
    bm = bmesh.new(); anillos = []
    for d, z in PERFIL_MARCO:
        h = 4.0 + d
        anillos.append([bm.verts.new(v) for v in ((-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z))])
    for a, b in zip(anillos[:-1], anillos[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(anillos[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Marco"); bm.to_mesh(me); bm.free()
    me.materials.append(M["marco"])
    marco = bpy.data.objects.new("Marco", me); col.objects.link(marco)
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(50))
    except AttributeError:
        pass
    return [cas, marco]

def construir_mesa(M):
    col = coleccion("Mesa")
    me = bpy.data.meshes.new("Mesa")
    S = 30
    me.from_pydata([(-S, -S, -0.30), (S, -S, -0.30), (S, S, -0.30), (-S, S, -0.30)], [], [(0, 1, 2, 3)])
    me.materials.append(M["madera"])
    o = bpy.data.objects.new("Mesa", me); col.objects.link(o)
    return o

# ---------------- Luces ----------------
def sol(nombre, direccion, fuerza, angulo, color=(1, 1, 1), col=None, sombra=True):
    L = bpy.data.lights.new(nombre, "SUN"); L.energy = fuerza; L.angle = math.radians(angulo); L.color = color
    L.use_shadow = sombra
    o = bpy.data.objects.new(nombre, L); col.objects.link(o)
    o.rotation_euler = (-direccion.normalized()).to_track_quat('-Z', 'Y').to_euler()
    return o

def construir_luces():
    col = coleccion("Luces")
    principal = sol("Luz_Principal", LUZ_PRINCIPAL_DIR, 4.0, 3, (1.0, 0.96, 0.90), col)
    relleno = sol("Luz_Relleno", LUZ_RELLENO_DIR, 0.30, 30, (0.90, 0.94, 1.0), col, sombra=False)
    contra = sol("Luz_Contra", LUZ_CONTRA_DIR, 2.5, 10, (1.0, 0.98, 0.95), col, sombra=False)
    contra_n = sol("Luz_Contra_Negras", LUZ_CONTRA_NEGRAS_DIR, 7.0, 7, (1.0, 0.97, 0.93), col, sombra=False)
    try:  # sólo ilumina las piezas negras (light linking de Cycles)
        contra_n.light_linking.receiver_collection = bpy.data.collections["Recibe_Contra_Negras"]
    except Exception:
        pass
    Ld = bpy.data.lights.new("Lampara", "SPOT"); Ld.energy = 6500; Ld.color = lin(C["lamp_luz"])[:3]
    Ld.spot_size = math.radians(70); Ld.spot_blend = 1.0; Ld.shadow_soft_size = 3.0
    lamp = bpy.data.objects.new("Lampara", Ld); col.objects.link(lamp); lamp.location = LAMPARA_POS
    lamp.rotation_euler = (Vector(LAMPARA_MIRA) - Vector(LAMPARA_POS)).to_track_quat('-Z', 'Y').to_euler()
    lamp.visible_glossy = False   # su reflejo lo da el disco (suave); la esfera de la lámpara dejaba un anillo duro
    # disco de la lámpara: sólo aparece en los reflejos (brillo suave de la laca arriba a la izquierda)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=64, radius=DISCO_LAMPARA["radio"])
    me = bpy.data.meshes.new("Disco_Lampara"); bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new("Disco_Lampara"); m.use_nodes = True; N = Nodos(m.node_tree); m.node_tree.nodes.clear()
    out = N.n("ShaderNodeOutputMaterial"); em = N.n("ShaderNodeEmission"); tc = N.n("ShaderNodeTexCoord")
    rango = N.n("ShaderNodeMapRange"); N.link(N.vmath('LENGTH', tc.outputs["Object"]), rango.inputs["Value"])
    rango.inputs["From Min"].default_value = 0.0; rango.inputs["From Max"].default_value = DISCO_LAMPARA["radio"]
    rango.inputs["To Min"].default_value = 1.0; rango.inputs["To Max"].default_value = 0.0
    N.link(N.math('MULTIPLY', N.math('POWER', rango.outputs["Result"], 2.2), DISCO_LAMPARA["fuerza"]), em.inputs["Strength"])
    em.inputs["Color"].default_value = lin(C["lamp"])
    N.link(em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    disco = bpy.data.objects.new("Disco_Lampara", me); col.objects.link(disco)
    disco.location = DISCO_LAMPARA["centro"]; disco.rotation_euler = (math.pi, 0, 0)
    for prop in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        setattr(disco, prop, False)
    return dict(principal=principal, relleno=relleno, contra=contra, contra_n=contra_n, lampara=lamp, disco=disco)

def mundo():
    w = scn.world or bpy.data.worlds.new("Mundo")
    scn.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.010, 0.009, 0.008, 1); bg.inputs["Strength"].default_value = 1.0

def _mundo(fuerza, color=(0.010, 0.009, 0.008)):
    bg = next(n for n in scn.world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*color, 1); bg.inputs["Strength"].default_value = fuerza

# ---------------- Cámaras ----------------
def camara(nombre, rot, escala, col):
    cd = bpy.data.cameras.new(nombre); cd.type = 'ORTHO'; cd.ortho_scale = escala; cd.sensor_fit = 'HORIZONTAL'
    cd.clip_start = 0.01; cd.clip_end = 200
    o = bpy.data.objects.new(nombre, cd); col.objects.link(o); o.rotation_euler = rot
    return o

def construir_camaras():
    col = coleccion("Camaras")
    cen = camara("Cam_Cenital", (0, 0, 0), 8 + 2 * MARCO, col); cen.location = (0, 0, 30)
    rot = Euler((math.radians(90 - INCLINACION_PIEZAS), 0, 0))
    fwd = rot.to_matrix() @ Vector((0, 0, -1)); up = rot.to_matrix() @ Vector((0, 1, 0))
    pz = camara("Cam_Piezas", rot, SPRITE_ESCALA, col)
    pz.location = up * ((0.5 - SPRITE_APOYO_V) * SPRITE_ESCALA) - fwd * 20
    rf = camara("Cam_Reflejo", rot, SPRITE_ESCALA, col)
    rf.location = up * ((0.5 - REFLEJO_APOYO_V) * SPRITE_ESCALA) - fwd * 20
    pv = camara("Cam_Preview", rot, 9.4, col)
    pv.location = up * 0.55 - fwd * 40
    return dict(cenital=cen, piezas=pz, reflejo=rf, preview=pv)

# ---------------- Render: utilidades ----------------
def render_base(muestras):
    r = scn.render; r.engine = 'CYCLES'; scn.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type == 'OPTIX')
    scn.cycles.samples = muestras; scn.cycles.use_denoising = True
    try:
        scn.cycles.denoiser = 'OPTIX'
    except TypeError:
        pass
    scn.cycles.max_bounces = 12; scn.cycles.glossy_bounces = 6; scn.cycles.caustics_reflective = False
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.image_settings.color_depth = '8'
    r.resolution_percentage = 100; r.film_transparent = False
    # Sin metadatos en los PNG: Blender grabaría la ruta del .blend (con el usuario de la PC), fecha y tiempos
    for k in ("date", "time", "render_time", "frame", "frame_range", "memory", "hostname", "camera", "lens",
              "scene", "marker", "filename", "sequencer_strip", "note"):
        if hasattr(r, "use_stamp_" + k):
            setattr(r, "use_stamp_" + k, False)
    scn.view_settings.view_transform = 'Standard'; scn.view_settings.look = 'None'
    scn.view_settings.exposure = 0.0

LUCES_SIEMPRE = ("Disco_Lampara",)

def solo(visibles):
    """Deja visibles en render sólo estos objetos (más las luces)."""
    for o in scn.objects:
        if o.type in ('LIGHT', 'CAMERA') or o.name in LUCES_SIEMPRE:
            continue
        o.hide_render = o not in visibles

def luces_modo(modo):
    L = ESCENA["luces"]
    piezas = modo in ("piezas", "preview")
    for k in ("principal", "disco"):
        L[k].hide_render = False
    L["lampara"].hide_render = modo == "piezas"
    for k in ("relleno", "contra", "contra_n"):
        L[k].hide_render = not piezas
    L["principal"].data.energy = {"piezas": 4.0, "preview": 3.0}.get(modo, 1.0)

def _render(ruta):
    import time
    scn.render.filepath = ruta
    t = time.time(); bpy.ops.render.render(write_still=True)
    return round(time.time() - t, 1)

def _px(ruta):
    import numpy as np
    im = bpy.data.images.load(ruta, check_existing=False)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    bpy.data.images.remove(im)
    return a

def _guardar(ruta, rgba):
    import numpy as np
    h, w = rgba.shape[:2]
    im = bpy.data.images.new("tmp_guardar", w, h, alpha=True)
    im.pixels.foreach_set(np.clip(rgba, 0, 1).astype(np.float32).ravel())
    im.filepath_raw = ruta; im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im)

def _a_lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def _a_srgb(c):
    import numpy as np
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)

def _escalar_alfa(ruta, factor):
    a = _px(ruta); a[..., 3] *= factor; _guardar(ruta, a)

def _mat_temp():
    m = bpy.data.materials.get("_Emision_Blanca")
    if m is None:
        m = bpy.data.materials.new("_Emision_Blanca"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
        e.inputs["Strength"].default_value = 1.0; nt.links.new(e.outputs[0], o.inputs["Surface"])
    espejo = bpy.data.materials.get("_Laca_Espejo")
    if espejo is None:
        espejo = principled("_Laca_Espejo", (0, 0, 0, 1), LACA_ROUGH, spec=0.5)
    return m, espejo

def _mat_especular(fuente):
    m = fuente.copy(); m.name = "_Esp_" + fuente.name
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    setv(b, "Base Color", (0, 0, 0, 1)); setv(b, "Subsurface Weight", 0.0)
    return m

def _espejo():
    _, espejo_mat = _mat_temp()
    e = bpy.data.objects.get("_Espejo")
    if e is None:
        me = bpy.data.meshes.new("_Espejo")
        me.from_pydata([(-4, -4, 0), (4, -4, 0), (4, 4, 0), (-4, 4, 0)], [], [(0, 1, 2, 3)])
        me.materials.append(espejo_mat)
        e = bpy.data.objects.new("_Espejo", me); coleccion("Piezas").objects.link(e)
    return e

# ---------------- Render: piezas ----------------
def render_sprites(dest, muestras=MUESTRAS_PIEZAS, piezas=None):
    import numpy as np
    os.makedirs(dest, exist_ok=True)
    tiempos = {}
    suelo = ESCENA["suelo"]; L = ESCENA["luces"]
    blanco, _ = _mat_temp(); espejo = _espejo()
    for o in ESCENA["preview"]:
        o.hide_render = True
    render_base(muestras)
    scn.render.resolution_x = scn.render.resolution_y = SPRITE_PX
    lista = [(k, o) for k, o in ESCENA["piezas"].items() if not piezas or k in piezas]
    for (color, nombre), o in lista:
        ruta = os.path.join(dest, f"{color}_{nombre}")
        o.location = (0, 0, 0); o.visible_camera = True; o.hide_viewport = False
        mat_orig = o.material_slots[0].material
        # 1) pieza
        luces_modo("piezas"); _mundo(1.0)
        scn.camera = ESCENA["camaras"]["piezas"]; scn.render.film_transparent = True
        solo([o]); tiempos[f"{color}_{nombre}"] = _render(ruta + ".png")
        # 2) sombra proyectada: sólo la luz principal sobre un shadow catcher, opacidad del núcleo SOMBRA_FUERZA
        for k in ("relleno", "contra", "contra_n", "lampara", "disco"):
            L[k].hide_render = True
        _mundo(0.0)
        solo([o, suelo]); o.visible_camera = False
        tiempos[f"{color}_{nombre}_sombra"] = _render(ruta + "_sombra.png")
        _escalar_alfa(ruta + "_sombra.png", SOMBRA_FUERZA)
        # 3) contacto: sin luces, cielo uniforme -> oclusión ambiente de la base sobre el tablero
        L["principal"].hide_render = True
        _mundo(1.0, (1, 1, 1))
        tiempos[f"{color}_{nombre}_contacto"] = _render(ruta + "_contacto.png")
        _escalar_alfa(ruta + "_contacto.png", CONTACTO_FUERZA)
        o.visible_camera = True
        # 4) reflejo en la laca: color (A) y cobertura x Fresnel (B: la pieza emite blanco, sin luces)
        luces_modo("piezas"); _mundo(1.0)
        scn.camera = ESCENA["camaras"]["reflejo"]; scn.render.film_transparent = False
        solo([o, espejo]); o.visible_camera = False
        tmp_a = ruta + "__a.png"; tmp_b = ruta + "__b.png"
        t = _render(tmp_a)
        o.material_slots[0].material = blanco
        for k in L:
            L[k].hide_render = True
        _mundo(0.0)
        t += _render(tmp_b)
        o.material_slots[0].material = mat_orig; o.visible_camera = True
        A = _a_lin(_px(tmp_a)[..., :3]); B = _a_lin(_px(tmp_b)[..., :3]).mean(axis=2)
        alfa = np.clip(B, 0, 1)
        col = np.where(alfa[..., None] > 1e-4, A / np.maximum(alfa[..., None], 1e-4), 0)
        _guardar(ruta + "_reflejo.png", np.dstack([_a_srgb(col), alfa]))
        os.remove(tmp_a); os.remove(tmp_b)
        tiempos[f"{color}_{nombre}_reflejo"] = round(t, 1)
        # 5) brillos fuertes: sólo el especular de la pieza, umbral y alfa por intensidad
        luces_modo("piezas"); _mundo(1.0)
        scn.camera = ESCENA["camaras"]["piezas"]; scn.render.film_transparent = True
        esp = _mat_especular(mat_orig); o.material_slots[0].material = esp
        solo([o]); tmp = ruta + "__e.png"
        tiempos[f"{color}_{nombre}_brillo"] = _render(tmp)
        o.material_slots[0].material = mat_orig; bpy.data.materials.remove(esp)
        E = _px(tmp); os.remove(tmp)
        lin_e = _a_lin(E[..., :3]) * E[..., 3:4]
        lum = lin_e @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        alfa = np.clip((lum - BRILLO_UMBRAL) / (1.0 - BRILLO_UMBRAL), 0, 1) ** 0.8
        tono = lin_e / np.maximum(lin_e.max(axis=2, keepdims=True), 1e-4)
        _guardar(ruta + "_brillo.png", np.dstack([_a_srgb(tono), alfa]))
        o.hide_render = True
    _mundo(1.0); luces_modo("piezas")
    return tiempos

# ---------------- Render: tablero y mesa ----------------
EXPOSICION_TABLERO = None

def calibrar_exposicion():
    """Ajusta la exposición del render cenital para que las casillas claras del centro den #5d6574."""
    global EXPOSICION_TABLERO
    import numpy as np, tempfile
    render_base(48); luces_modo("tablero"); _mundo(1.0)
    cam = ESCENA["camaras"]["cenital"]; cam.data.ortho_scale = 8 + 2 * MARCO; scn.camera = cam
    scn.render.resolution_x = scn.render.resolution_y = 420
    solo(list(ESCENA["tablero"]) + [ESCENA["mesa"]])
    ruta = os.path.join(tempfile.gettempdir(), "calib_tablero.png"); _render(ruta)
    a = _a_lin(_px(ruta)[..., :3]); os.remove(ruta)
    px = 420 / (8 + 2 * MARCO)
    def muestra(i, j):   # casilla (columna i, fila j) desde abajo a la izquierda; la imagen está abajo-arriba
        cx = (MARCO + i + 0.5) * px; cy = (MARCO + j + 0.5) * px
        return a[int(cy) - 6:int(cy) + 6, int(cx) - 6:int(cx) + 6].reshape(-1, 3).mean(axis=0)
    lum = lambda c: float(c @ np.array([0.2126, 0.7152, 0.0722]))
    medido = (lum(muestra(4, 3)) + lum(muestra(3, 4))) / 2
    objetivo = lum(np.array(lin(C["square_light"])[:3]))
    EXPOSICION_TABLERO = max(-4.0, min(4.0, math.log2(objetivo / medido)))
    return EXPOSICION_TABLERO

def render_tablero(dest, px=TABLERO_PX, muestras=MUESTRAS_TABLERO):
    os.makedirs(dest, exist_ok=True)
    if EXPOSICION_TABLERO is None:
        calibrar_exposicion()
    for o in ESCENA["preview"]:
        o.hide_render = True
    render_base(muestras); luces_modo("tablero"); _mundo(1.0)
    scn.view_settings.exposure = EXPOSICION_TABLERO
    cam = ESCENA["camaras"]["cenital"]; cam.data.ortho_scale = 8 + 2 * MARCO; scn.camera = cam
    scn.render.resolution_x = scn.render.resolution_y = px
    scn.render.film_transparent = True
    solo(list(ESCENA["tablero"]) + [ESCENA["mesa"]]); ESCENA["mesa"].visible_camera = False
    t = _render(os.path.join(dest, "tablero.png"))
    ESCENA["mesa"].visible_camera = True
    return t

def render_mesa(dest, res=MESA_PX, muestras=MUESTRAS_TABLERO):
    os.makedirs(dest, exist_ok=True)
    if EXPOSICION_TABLERO is None:
        calibrar_exposicion()
    for o in ESCENA["preview"]:
        o.hide_render = True
    render_base(muestras); luces_modo("tablero"); _mundo(1.0)
    scn.view_settings.exposure = EXPOSICION_TABLERO
    cam = ESCENA["camaras"]["cenital"]; cam.data.ortho_scale = MESA_ANCHO; scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    solo([ESCENA["mesa"]])
    t = _render(os.path.join(dest, "mesa.png"))
    cam.data.ortho_scale = 8 + 2 * MARCO
    return t

def export_all(dest=EXPORT_DIR):
    t = render_sprites(dest)
    t["tablero"] = render_tablero(dest); t["mesa"] = render_mesa(dest)
    return t

# ---------------- Vista previa 3D ----------------
def posicion_inicial():
    col = coleccion("Preview")
    negras = bpy.data.collections["Recibe_Contra_Negras"]
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    fila = ["torre", "caballo", "alfil", "dama", "rey", "alfil", "caballo", "torre"]
    # piezas movidas: caballo negro sobre casilla oscura (e5) y piezas juntas para ver reflejos cruzados
    mover = {("negras", 6, 7): (4, 4), ("negras", 3, 6): (3, 4), ("blancas", 3, 0): (3, 3), ("blancas", 5, 0): (4, 3)}
    objs = []
    for color, r_p, r_f in (("blancas", 1, 0), ("negras", 6, 7)):
        for i in range(8):
            for r, nombre in ((r_f, fila[i]), (r_p, "peon")):
                src = ESCENA["piezas"][(color, nombre)]
                o = src.copy(); col.objects.link(o)
                if color == "negras":
                    negras.objects.link(o)
                ni, nr = mover.get((color, i, r), (i, r))
                o.location = (ni - 3.5, nr - 3.5, 0)
                objs.append(o)
    for o in ESCENA["piezas"].values():
        o.hide_render = True
    return objs

def render_preview(muestras=384, ruta=os.path.join(PREVIEWS, "ajedrez_preview.png")):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    render_base(muestras); luces_modo("preview"); _mundo(1.0)
    solo(list(ESCENA["tablero"]) + [ESCENA["mesa"]] + ESCENA["preview"])
    scn.camera = ESCENA["camaras"]["preview"]
    scn.render.resolution_x, scn.render.resolution_y = 2400, 1600
    return _render(ruta)

def datos_sprite():
    from bpy_extras.object_utils import world_to_camera_view
    scn.render.resolution_x = scn.render.resolution_y = SPRITE_PX
    v = world_to_camera_view(scn, ESCENA["camaras"]["piezas"], Vector((0, 0, 0)))
    vr = world_to_camera_view(scn, ESCENA["camaras"]["reflejo"], Vector((0, 0, 0)))
    ang = math.radians(INCLINACION_PIEZAS); altos = {}
    for nombre, me in ESCENA["mallas"].items():
        top = max(p.co.z for p in me.vertices)
        r = max(math.hypot(p.co.x, p.co.y) for p in me.vertices if p.co.z < 0.05)
        altos[nombre] = dict(alto=round(top, 3), radio_base=round(r, 3),
                             alto_en_vista=round(top * math.cos(ang) + 2 * r * math.sin(ang), 3),
                             sobre_apoyo=round(top * math.cos(ang) + r * math.sin(ang), 3),
                             bajo_apoyo=round(r * math.sin(ang), 3))
    return dict(apoyo_px=(round(v.x * SPRITE_PX, 1), round((1 - v.y) * SPRITE_PX, 1)),
                apoyo_reflejo_px=(round(vr.x * SPRITE_PX, 1), round((1 - vr.y) * SPRITE_PX, 1)),
                px_por_casilla=round(SPRITE_PX / SPRITE_ESCALA, 2), piezas=altos)

# ---------------- Main ----------------
limpiar()
M = materiales()
mallas, piezas = construir_piezas(M)
tablero = construir_tablero(M)
mesa = construir_mesa(M)
luces = construir_luces()
mundo()
camaras = construir_camaras()
suelo_me = bpy.data.meshes.new("Suelo_Sombra")
suelo_me.from_pydata([(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
suelo = bpy.data.objects.new("Suelo_Sombra", suelo_me); coleccion("Piezas").objects.link(suelo)
suelo.is_shadow_catcher = True; suelo.hide_render = True
ESCENA = dict(M=M, mallas=mallas, piezas=piezas, tablero=tablero, mesa=mesa, luces=luces, camaras=camaras, suelo=suelo)
ESCENA["preview"] = posicion_inicial()
scn.camera = camaras["preview"]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
