"""Props for game 5 (Frostpeak Games): podium on a medal stage, flagpole, spectators (tinted per instance), snowy
pine and spruce, torch cauldron, floodlight mast, finish arch, start gate, grandstand section and its end wall,
scoreboard, TV camera tower, judges' tower and the jump's start house. Deterministic; output CC BY-SA 4.0;
provenance: this script.
Run: blender -b --factory-startup -P tools/blender/frostpeak_models.py -- godot/games/frostpeak/art/models
1 unit = 1 m, Z up in Blender, fronts face -Y. The ice oval and the jump hill are built by the game from the
events' own geometry, so what you see is what the physics uses.
Materials the game recolours or replaces by name: "coat" (spectator, instance colour), "hat" and "scarf" (instance
custom colour), "face" (skin tones), "pine_needles" (snow-on-branches shader).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Matrix, Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
MATS = {}


def mat(name, color, rough=0.6, metal=0.0, emit=0.0, coat=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    MATS[name] = m
    return m


def active():
    return bpy.context.active_object


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def put(o, material, smooth=False, bevel=0.0):
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 2
        b.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=b.name)
    o.data.materials.clear()
    o.data.materials.append(material)
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def box(size, loc, material, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, bevel=bevel)


def cyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=20, smooth=True):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return put(active(), material, smooth)


def sphere(r, loc, material, scale=(1, 1, 1), segs=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, True)


class Kit:
    """Many simple parts gathered into one bmesh per material (fast: no operator per part). obj() turns each
    material's bmesh into an object, ready to join and export."""

    def __init__(self):
        self.bms = {}
        self.smooth = {}

    def _bm(self, m, smooth=False):
        if m.name not in self.bms:
            self.bms[m.name] = (bmesh.new(), m)
        if smooth:
            self.smooth[m.name] = True
        return self.bms[m.name][0]

    def box(self, m, center, size, rz=0.0, rx=0.0, ry=0.0):
        mt = (Matrix.Translation(center) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
              @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*size, 1)))
        bmesh.ops.create_cube(self._bm(m), size=1.0, matrix=mt)

    def bar(self, m, a, b, w, h=None):
        """A square beam from point a to point b."""
        a, b = Vector(a), Vector(b)
        d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        mt = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((w, h or w, d.length, 1))
        bmesh.ops.create_cube(self._bm(m), size=1.0, matrix=mt)

    def tube(self, m, a, b, r, r2=None, segs=8, smooth=True):
        a, b = Vector(a), Vector(b)
        d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        mt = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.create_cone(self._bm(m, smooth), cap_ends=True, segments=segs, radius1=r,
                              radius2=r if r2 is None else r2, depth=d.length, matrix=mt)

    def ball(self, m, center, r, scale=(1, 1, 1), segs=10, rings=6):
        mt = Matrix.Translation(center) @ Matrix.Diagonal((*scale, 1))
        bmesh.ops.create_uvsphere(self._bm(m, True), u_segments=segs, v_segments=rings, radius=r, matrix=mt)

    def rings(self, m, rings, smooth=True, cap=True):
        """A lofted surface through rings of points (same count each), bottom to top; capped."""
        bm = self._bm(m, smooth)
        vs = [[bm.verts.new(p) for p in ring] for ring in rings]
        n = len(vs[0])
        for k in range(len(vs) - 1):
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
        if cap:
            bm.faces.new(list(reversed(vs[0])))
            bm.faces.new(vs[-1])

    def obj(self):
        out = []
        for name, (bm, m) in self.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = bpy.data.meshes.new(name)
            bm.to_mesh(me)
            bm.free()
            if self.smooth.get(name):
                me.shade_smooth()
            o = bpy.data.objects.new(name, me)
            bpy.context.collection.objects.link(o)
            o.data.materials.append(m)
            out.append(o)
        self.bms = {}
        self.smooth = {}
        return out


def export(parts, name):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    active().name = name
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)
    reset()


SNOW = mat("snow", (0.95, 0.97, 1.0), 0.6)
WOOD = mat("wood", (0.5, 0.35, 0.22), 0.8)
STEEL = mat("steel", (0.7, 0.72, 0.76), 0.35, 0.9)
DARK_STEEL = mat("dark_steel", (0.22, 0.24, 0.28), 0.45, 0.8)
CONCRETE = mat("stand_concrete", (0.66, 0.67, 0.7), 0.85)
GLASS = mat("glass", (0.55, 0.75, 0.9), 0.05, 0.2, alpha=0.35)
WINDOW = mat("window", (0.28, 0.42, 0.55), 0.08, 0.4, coat=1.0)
LAMP = mat("flood_lamp", (1.0, 0.97, 0.9), 0.3, emit=6.0)
RED = mat("venue_red", (0.78, 0.1, 0.12), 0.45)
WHITE = mat("venue_white", (0.93, 0.94, 0.96), 0.5)
BLUE = mat("venue_blue", (0.1, 0.25, 0.62), 0.5)


def podium():
    """The medal stage: a raised platform with steps, the three blocks, a curved backdrop with bands of colour."""
    white = mat("podium", (0.95, 0.95, 0.97), 0.4, coat=0.3)
    gold = mat("podium_gold", (1.0, 0.8, 0.3), 0.3, 1.0)
    silver = mat("podium_silver", (0.8, 0.82, 0.86), 0.3, 1.0)
    bronze = mat("podium_bronze", (0.8, 0.5, 0.3), 0.35, 1.0)
    carpet = mat("stage_carpet", (0.12, 0.2, 0.45), 0.9)
    parts = [box((1.4, 1.2, 1.2), (0, 0, 0.6), white), box((1.4, 1.2, 0.85), (-1.45, 0, 0.425), white),
             box((1.4, 1.2, 0.55), (1.45, 0, 0.275), white)]
    for x, z, m in ((0, 1.2, gold), (-1.45, 0.85, silver), (1.45, 0.55, bronze)):
        parts.append(box((1.3, 0.04, 0.3), (x, -0.61, z - 0.3), m, bevel=0.01))
        parts.append(box((1.36, 1.16, 0.03), (x, 0, z + 0.005), m, bevel=0.005))  # a metal cap on each block
    k = Kit()
    # numbers on the fronts: 1 = one bar, 2 = two, 3 = three (plain bars, readable from afar)
    for x, n, z in ((0, 1, 0.6), (-1.45, 2, 0.42), (1.45, 3, 0.26)):
        for i in range(n):
            k.box(BLUE, (x + (i - (n - 1) / 2) * 0.16, -0.605, z), (0.07, 0.02, 0.34))
    # the stage under the podium: carpeted top, white skirt, two steps at the front
    k.box(carpet, (0, 0.6, -0.02), (7.0, 4.6, 0.04))
    k.box(WHITE, (0, 0.6, -0.25), (7.1, 4.7, 0.42))
    for i in range(2):
        k.box(WHITE, (0, -1.85 - i * 0.35, -0.3 - i * 0.14), (3.0, 0.35, 0.3))
    # the backdrop: a curve of panels in the games' colours, a white band with a blue stripe on top
    for i in range(11):
        a = math.radians(-50 + i * 10)
        r = 6.0
        x, y = math.sin(a) * r, 2.9 - math.cos(a) * r + r - 3.0
        cm = (BLUE, WHITE, RED)[i % 3] if i not in (4, 5, 6) else BLUE
        k.box(cm, (x, y + 3.0, 1.9), (1.05, 0.12, 3.8), rz=a)
        k.box(WHITE, (x, y + 3.0, 3.95), (1.05, 0.16, 0.3), rz=a)
        k.box(DARK_STEEL, (x, y + 3.15, 1.9), (0.08, 0.08, 3.9), rz=a)
    # the games' emblem on the backdrop: a white peak with a snow-cap on the blue centre panels
    em = k
    em.rings(WHITE, [[(-1.2, 2.84, 1.9), (1.2, 2.84, 1.9), (0.0, 2.84, 3.4)], [(-1.2, 2.8, 1.9), (1.2, 2.8, 1.9), (0.0, 2.8, 3.4)]], smooth=False)
    em.rings(BLUE, [[(-0.55, 2.78, 2.35), (0.55, 2.78, 2.35), (0.0, 2.78, 2.95)], [(-0.55, 2.76, 2.35), (0.55, 2.76, 2.35), (0.0, 2.76, 2.95)]], smooth=False)
    parts += k.obj()
    export(parts, "podium")


def flagpole():
    k = Kit()
    k.tube(STEEL, (0, 0, 0), (0, 0, 8.0), 0.06, 0.04, 12)
    k.tube(DARK_STEEL, (0, 0, 0), (0, 0, 0.5), 0.12, 0.1, 12)
    k.ball(mat("pole_ball", (1.0, 0.8, 0.3), 0.3, 1.0), (0, 0, 8.06), 0.09)
    k.tube(mat("halyard", (0.9, 0.9, 0.9), 0.8), (0.07, 0, 0.9), (0.07, 0, 7.95), 0.008, segs=4)
    export(k.obj(), "flagpole")


def _person(k, coat, face, dark, hat, scarf, boots, pose):
    """One spectator in a padded coat, trousers, boots, a scarf and a bobble hat. pose: "cheer" (arms up), "clap"
    (hands together in front), "flag" (one arm up holding a small flag on a stick)."""
    for s in (-1, 1):  # legs and boots
        k.tube(dark, (0.1 * s, 0, 0.1), (0.1 * s, 0, 0.8), 0.075, 0.085, 8)
        k.ball(boots, (0.1 * s, -0.04, 0.07), 0.08, (0.9, 1.4, 0.7), 8, 5)
    # the coat: a padded loft from hip to shoulder, a little wider at the chest
    rings = []
    for z, rx, ry in ((0.72, 0.19, 0.14), (0.82, 0.21, 0.15), (1.0, 0.22, 0.16), (1.18, 0.23, 0.16), (1.32, 0.21, 0.14), (1.4, 0.12, 0.09)):
        rings.append([(rx * math.cos(2 * math.pi * i / 10), ry * math.sin(2 * math.pi * i / 10), z) for i in range(10)])
    k.rings(coat, rings)
    k.box(dark, (0, -0.155, 1.05), (0.025, 0.02, 0.6))  # the zip
    # scarf round the neck, one end hanging down the front
    k.tube(scarf, (0, 0, 1.36), (0, 0, 1.46), 0.1, 0.085, 10)
    k.box(scarf, (0.07, -0.13, 1.2), (0.09, 0.03, 0.3), rx=-0.15)
    k.ball(face, (0, -0.01, 1.56), 0.115, (0.9, 0.95, 1.05), 12, 8)
    k.ball(face, (0, -0.12, 1.55), 0.022, (0.9, 1, 1), 6, 4)  # nose
    # hat with a folded brim and a bobble
    k.tube(hat, (0, 0.005, 1.58), (0, 0.005, 1.7), 0.118, 0.1, 12)
    k.tube(scarf, (0, 0.005, 1.58), (0, 0.005, 1.63), 0.122, 0.122, 12)
    k.ball(scarf, (0, 0.01, 1.76), 0.055, (1, 1, 1), 8, 5)
    glove = dark
    for s in (-1, 1):
        sh = Vector((0.23 * s, 0, 1.32))
        if pose == "cheer" or (pose == "flag" and s > 0):
            el = sh + Vector((0.12 * s, -0.02, 0.26))
            hd = el + Vector((0.02 * s, -0.03, 0.28))
        elif pose == "clap":
            el = sh + Vector((0.04 * s, -0.2, -0.2))
            hd = Vector((0.03 * s, -0.36, 1.2))
        else:
            el = sh + Vector((0.06 * s, 0.02, -0.28))
            hd = el + Vector((0.0, -0.08, -0.26))
        k.tube(coat, sh, el, 0.07, 0.065, 8)
        k.tube(coat, el, hd, 0.062, 0.055, 8)
        k.ball(glove, hd, 0.05, (1, 1, 1), 8, 5)
        if pose == "flag" and s > 0:
            k.tube(DARK_STEEL, hd - Vector((0, 0, 0.1)), hd + Vector((0, 0, 0.55)), 0.01, segs=4)
            k.box(hat, hd + Vector((-0.2, 0, 0.42)), (0.4, 0.01, 0.26))


def spectator():
    """Three spectator poses; the game tints the coat (instance colour), hat and scarf (instance custom) per person."""
    coat = mat("coat", (1, 1, 1), 0.85)
    face = mat("face", (0.92, 0.72, 0.58), 0.6)
    dark = mat("trousers", (0.13, 0.13, 0.17), 0.85)
    hat = mat("hat", (1, 1, 1), 0.9)
    scarf = mat("scarf", (1, 1, 1), 0.9)
    boots = mat("spectator_boots", (0.2, 0.14, 0.1), 0.7)
    for name, pose in (("spectator", "cheer"), ("spectator_clap", "clap"), ("spectator_flag", "flag")):
        k = Kit()
        _person(k, coat, face, dark, hat, scarf, boots, pose)
        export(k.obj(), name)


def _tree(k, needles, trunk, height, tiers, spread, rng, slender=1.0):
    """A conifer of drooping tiers: each tier a jagged skirt of branch tips (flat on top, where the snow lies, and
    steep at the tips), smaller towards the top, with a crooked leader."""
    k.tube(trunk, (0, 0, 0), (0, 0, height * 0.35), 0.1 * spread, 0.07 * spread, 7)
    for t in range(tiers):
        f = t / (tiers - 1)
        z = height * (0.18 + 0.74 * f)
        r = spread * (1.0 - 0.82 * f) * (1.0 + rng.uniform(-0.08, 0.08))
        h = height * 0.22 * (1.0 - 0.4 * f)
        n = 14
        ring_top, ring_mid, ring_tip, ring_under = [], [], [], []
        rot = rng.uniform(0, 6.28)
        for i in range(n):
            a = rot + 2 * math.pi * i / n
            tip = 1.0 if i % 2 == 0 else 0.72
            tip *= 1.0 + rng.uniform(-0.12, 0.12)
            ca, sa = math.cos(a) * slender, math.sin(a) * slender
            ring_top.append((ca * r * 0.12, sa * r * 0.12, z + h))
            ring_mid.append((ca * r * 0.62 * tip, sa * r * 0.62 * tip, z + h * 0.42 + rng.uniform(-0.05, 0.05)))
            ring_tip.append((ca * r * tip, sa * r * tip, z - h * 0.08 * tip))
            ring_under.append((ca * r * 0.35, sa * r * 0.35, z + h * 0.05))
        k.rings(needles, [ring_under, ring_tip, ring_mid, ring_top], smooth=True)
    k.tube(needles, (0, 0, height * 0.9), (rng.uniform(-0.05, 0.05), 0, height * 1.02), 0.08 * spread, 0.0, 6)


def trees():
    """Two conifers: a broad pine and a tall, slender spruce. Snow on the branches comes from the game's shader
    (white where a surface faces up), so the same model sits in any light."""
    needles = mat("pine_needles", (0.1, 0.26, 0.16), 0.85)
    trunk = mat("bark", (0.3, 0.2, 0.14), 0.9)
    rng = random.Random(7)
    k = Kit()
    _tree(k, needles, trunk, 5.2, 7, 1.7, rng)
    export(k.obj(), "snowy_pine")
    k = Kit()
    _tree(k, needles, trunk, 7.0, 10, 1.15, rng, 1.0)
    export(k.obj(), "snowy_spruce")


def cauldron():
    """The torch cauldron on a flared column with a ring of stone steps; the flame is emissive tongues."""
    bronze = mat("cauldron", (0.75, 0.5, 0.25), 0.35, 1.0)
    flame = mat("flame", (1.0, 0.55, 0.15), 0.5, emit=8.0)
    core = mat("flame_core", (1.0, 0.85, 0.5), 0.5, emit=12.0)
    stone = mat("plinth", (0.8, 0.8, 0.82), 0.7)
    k = Kit()
    for i in range(3):
        k.tube(stone, (0, 0, i * 0.2), (0, 0, i * 0.2 + 0.2), 2.2 - i * 0.5, segs=32, smooth=False)
    k.tube(STEEL, (0, 0, 0.6), (0, 0, 2.3), 0.28, 0.2, 16)
    for i in range(6):  # a flared tripod-like cradle
        a = i * math.pi / 3
        k.tube(bronze, (0.3 * math.cos(a), 0.3 * math.sin(a), 1.6), (0.85 * math.cos(a), 0.85 * math.sin(a), 2.9), 0.05, segs=6)
    bowl = []
    for z, r in ((2.35, 0.25), (2.5, 0.65), (2.75, 0.95), (3.05, 1.08), (3.12, 1.1), (3.1, 0.98), (2.95, 0.9)):
        bowl.append([(r * math.cos(2 * math.pi * i / 28), r * math.sin(2 * math.pi * i / 28), z) for i in range(28)])
    k.rings(bronze, bowl)
    k.tube(mat("cauldron_rim", (1.0, 0.8, 0.35), 0.25, 1.0), (0, 0, 3.08), (0, 0, 3.16), 1.12, segs=28)
    for i in range(7):
        a = i * 2 * math.pi / 7
        k.tube(flame, (0.4 * math.cos(a), 0.4 * math.sin(a), 3.0), (0.3 * math.cos(a + 0.3), 0.3 * math.sin(a + 0.3), 4.6 - (i % 3) * 0.35), 0.32, 0.01, 8)
    for i in range(3):
        a = i * 2 * math.pi / 3
        k.tube(core, (0.15 * math.cos(a), 0.15 * math.sin(a), 3.0), (0.05 * math.cos(a), 0.05 * math.sin(a), 4.0), 0.25, 0.01, 8)
    export(k.obj(), "cauldron")


def floodlight():
    """A lattice mast with a service ladder, a head frame of twelve lamps in hoods, and a small platform."""
    hood = mat("lamp_hood", (0.2, 0.21, 0.24), 0.4, 0.8)
    k = Kit()
    h = 18.0
    for s in ((-1, -1), (1, -1), (1, 1), (-1, 1)):  # the tapering lattice
        k.tube(STEEL, (0.6 * s[0], 0.6 * s[1], 0), (0.3 * s[0], 0.3 * s[1], h), 0.05, segs=6)
    for i in range(12):
        z0, z1 = i * h / 12, (i + 1) * h / 12
        w0, w1 = 0.6 - 0.3 * z0 / h, 0.6 - 0.3 * z1 / h
        for a, b in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            k.tube(STEEL, (w0 * a[0], w0 * a[1], z0), (w1 * b[0], w1 * b[1], z1), 0.025, segs=4)
            k.tube(STEEL, (w1 * a[0], w1 * a[1], z1), (w1 * b[0], w1 * b[1], z1), 0.025, segs=4)
    k.box(DARK_STEEL, (0, 0.2, h - 0.2), (2.4, 1.6, 0.1))  # platform
    for x in (-1.2, 1.2):
        k.bar(DARK_STEEL, (x, -0.6, h - 0.2), (x, -0.6, h + 0.8), 0.05)
    k.bar(DARK_STEEL, (-1.2, 1.0, h + 0.8), (1.2, 1.0, h + 0.8), 0.05)
    # the head frame, tilted down towards the venue (+Y in Blender is the back, lamps face -Y)
    tilt = 0.35
    k.box(DARK_STEEL, (0, 0.3, h + 1.8), (3.6, 0.15, 2.6), rx=tilt)
    for i in range(4):
        for j in range(3):
            c = Vector((-1.25 + i * 0.83, 0.0, h + 0.95 + j * 0.85))
            c.y = 0.3 - (c.z - h - 1.8) * math.sin(tilt) - 0.25
            k.box(hood, c, (0.7, 0.35, 0.7), rx=tilt)
            k.box(LAMP, c + Vector((0, -0.19, 0)), (0.58, 0.04, 0.58), rx=tilt)
    export(k.obj(), "floodlight")


def finish_arch():
    """An inflatable-looking finish arch: rounded red legs and beam, a white band, a digital clock on top."""
    red = mat("arch_red", (0.85, 0.1, 0.12), 0.5)
    k = Kit()
    for x in (-5.5, 5.5):
        k.tube(red, (x, 0, 0), (x, 0, 5.2), 0.42, 0.36, 16)
        k.box(DARK_STEEL, (x, 0, 0.1), (1.0, 1.0, 0.2))
    k.tube(red, (-5.6, 0, 5.3), (5.6, 0, 5.3), 0.5, segs=16)
    k.tube(mat("arch_white", (1, 1, 1), 0.5), (-4.6, 0, 5.3), (4.6, 0, 5.3), 0.52, segs=16)
    k.box(DARK_STEEL, (0, 0, 6.3), (2.6, 0.4, 1.0))
    k.box(mat("clock_face", (1.0, 0.6, 0.15), 0.3, emit=3.0), (0, -0.21, 6.3), (2.3, 0.02, 0.7))
    k.box(mat("clock_face", (1.0, 0.6, 0.15), 0.3, emit=3.0), (0, 0.21, 6.3), (2.3, 0.02, 0.7))
    export(k.obj(), "finish_arch")


def start_gate():
    k = Kit()
    k.box(WOOD, (0, 0, 0.1), (3.0, 1.2, 0.2))
    for x in (-1.4, 1.4):
        k.box(STEEL, (x, 0, 0.8), (0.15, 0.15, 1.6))
    k.box(mat("gate_blue", (0.1, 0.3, 0.8), 0.4), (0, 0, 1.5), (3.0, 0.2, 0.3))
    k.box(mat("gate_bar", (0.95, 0.8, 0.15), 0.4), (0, -0.3, 0.45), (2.7, 0.06, 0.06))
    export(k.obj(), "start_gate")


# --------------------------------------------------------------------------- the grandstand
# One 24 m section; the game lines several up. Tiers rise to the back (+Y); the front wall stands at y = 0.
SEC = 24.0
ROWS = 12
Y0, TREAD, Z0, RISE = 0.6, 0.85, 1.0, 0.42  # row i: tread from Y0 + i * TREAD, top at Z0 + i * RISE


def grandstand():
    seat_a = mat("seat_blue", (0.1, 0.3, 0.75), 0.45, coat=0.4)
    seat_b = mat("seat_white", (0.92, 0.93, 0.95), 0.45, coat=0.4)
    roof = mat("roof", (0.9, 0.91, 0.93), 0.4, 0.6)
    fascia = mat("fascia", (0.1, 0.22, 0.55), 0.5)
    clad = mat("cladding", (0.32, 0.38, 0.48), 0.6, 0.3)
    k = Kit()
    half = SEC / 2
    # the front wall with a glass balustrade on steel posts
    k.box(CONCRETE, (0, 0.15, 0.6), (SEC, 0.3, 1.2))
    k.box(GLASS, (0, 0.3, 1.55), (SEC, 0.03, 0.7))
    k.box(STEEL, (0, 0.3, 1.92), (SEC, 0.08, 0.06))
    for i in range(13):
        k.box(STEEL, (-half + i * 2.0, 0.3, 1.55), (0.06, 0.06, 0.75))
    # the tiers, with seats in two colours making a chevron pattern, and half an aisle at each end
    for r in range(ROWS):
        y = Y0 + r * TREAD
        z = Z0 + r * RISE
        k.box(CONCRETE, (0, y + TREAD / 2, z / 2), (SEC, TREAD, z))
        k.box(CONCRETE, (0, y + 0.02, z + 0.005), (SEC, 0.04, 0.01))
        n = 40
        for s in range(n):
            x = -half + 1.2 + (s + 0.5) * (SEC - 2.4) / n
            m = seat_b if (abs(((s + r) % 10) - 5) == 0 or (s - r) % 20 == 0) else seat_a
            k.box(m, (x, y + 0.36, z + 0.4), (0.46, 0.4, 0.06))
            k.box(m, (x, y + 0.6, z + 0.66), (0.46, 0.05, 0.46), rx=-0.12)
            k.box(DARK_STEEL, (x, y + 0.38, z + 0.2), (0.06, 0.3, 0.4))
        for side in (-1, 1):  # aisle steps: two per tier
            for st in range(2):
                k.box(CONCRETE, (side * (half - 0.35), y + st * TREAD / 2 + TREAD / 4, (z - RISE / 2 + st * RISE / 2) / 2 + 0.1),
                      (0.7, TREAD / 2, z - RISE / 2 + st * RISE / 2 + 0.2))
            k.box(STEEL, (side * (half - 0.72), y + 0.4, z + 0.95), (0.05, 0.05, 1.0))
    top_y = Y0 + ROWS * TREAD
    top_z = Z0 + (ROWS - 1) * RISE
    for side in (-1, 1):  # the aisle handrails
        k.bar(STEEL, (side * (half - 0.72), Y0 + 0.4, Z0 + 1.45), (side * (half - 0.72), top_y - 0.45, top_z + 1.45), 0.05)
    # the back wall and the concourse behind, clad in ribbed panels up to the roof
    k.box(CONCRETE, (0, top_y + 0.25, (top_z + 1.4) / 2), (SEC, 0.5, top_z + 1.4))
    k.box(clad, (0, top_y + 0.6, 9.9), (SEC, 0.2, 5.8))
    for i in range(24):
        k.box(clad, (-half + 0.5 + i, top_y + 0.72, 9.9), (0.12, 0.08, 5.8))
    k.box(CONCRETE, (0, top_y + 0.6, (top_z + 1.4) / 2 - 0.3), (SEC, 0.3, top_z + 0.8))
    for i in range(7):  # pilasters on the outside
        k.box(CONCRETE, (-half + 2 + i * 3.333, top_y + 0.85, 3.5), (0.5, 0.4, 7.0))
    k.box(LAMP, (0, top_y + 0.05, top_z + 1.2), (SEC, 0.05, 0.08))  # the concourse light strip
    # the roof: steel columns at the back, cantilevered trusses, a ribbed sheet on top, a fascia at the front
    back, front = top_y + 0.9, -2.0
    for x in (-half / 2, half / 2):
        k.box(DARK_STEEL, (x, back, 6.4), (0.5, 0.5, 12.8))
        tb, tf = Vector((x, back, 13.0)), Vector((x, front, 12.25))
        bb, bf = Vector((x, back, 9.8)), Vector((x, front, 11.7))
        k.bar(DARK_STEEL, tb, tf, 0.3)
        k.bar(DARK_STEEL, bb, bf, 0.25)
        n = 7
        for i in range(n + 1):
            f0, f1 = i / n, min(1.0, (i + 0.5) / n)
            top0, bot0 = tb.lerp(tf, f0), bb.lerp(bf, f0)
            k.bar(DARK_STEEL, top0, bot0, 0.12)
            if i < n:
                k.bar(DARK_STEEL, bot0, tb.lerp(tf, (i + 1) / n), 0.1)
    slope = math.atan2(13.0 - 12.25, back - front)
    mid = Vector((0, (back + front) / 2, (13.0 + 12.25) / 2 + 0.25))
    length = math.hypot(back - front, 13.0 - 12.25) + 0.6
    k.box(roof, mid, (SEC, length, 0.14), rx=slope)
    for i in range(int(SEC / 0.8)):  # standing seams on the roof sheet
        k.box(roof, (-half + 0.4 + i * 0.8, mid.y, mid.z + 0.1), (0.06, length, 0.08), rx=slope)
    for x in (-half, 0.0, half):  # purlins under the sheet
        pass
    for j in range(6):
        f = j / 5
        p = Vector((0, back, 13.1)).lerp(Vector((0, front, 12.35)), f)
        k.box(DARK_STEEL, (0, p.y, p.z), (SEC, 0.14, 0.2))
    k.box(fascia, (0, front - 0.3, 12.0), (SEC, 0.25, 1.3))
    k.box(WHITE, (0, front - 0.44, 12.62), (SEC, 0.04, 0.1))
    k.box(WHITE, (0, front - 0.44, 11.38), (SEC, 0.04, 0.1))
    for i in range(8):  # lamps under the roof edge, lighting the stand
        k.box(LAMP, (-half + 1.5 + i * 3.0, front + 0.6, 11.55), (1.2, 0.3, 0.06))
    export(k.obj(), "grandstand")


def grandstand_end():
    """The side wall that closes a row of sections: stepped along the tiers, rising to the roof."""
    k = Kit()
    for r in range(ROWS):
        y = Y0 + r * TREAD
        z = Z0 + r * RISE
        k.box(CONCRETE, (0, y + TREAD / 2, (z + 1.1) / 2), (0.4, TREAD, z + 1.1))
    k.box(CONCRETE, (0, 0.15, 0.95), (0.4, 0.3, 1.9))
    top_y = Y0 + ROWS * TREAD
    k.box(mat("cladding", (0.32, 0.38, 0.48), 0.6, 0.3), (0, top_y + 0.4, 6.8), (0.4, 1.2, 13.6))
    k.box(STEEL, (0, Y0 + 0.3, Z0 + 1.2), (0.45, 0.06, 0.06))
    export(k.obj(), "grandstand_end")


def scoreboard():
    """A big screen on two legs: a dark frame, a black face (the game writes on it), a coloured crown."""
    k = Kit()
    for x in (-3.2, 3.2):
        k.box(DARK_STEEL, (x, 0.3, 3.0), (0.5, 0.5, 6.0))
    k.box(DARK_STEEL, (0, 0.3, 8.6), (9.4, 0.9, 5.4))
    k.box(mat("screen", (0.02, 0.03, 0.05), 0.2, coat=1.0), (0, -0.16, 8.5), (8.8, 0.04, 4.6))
    k.box(BLUE, (0, 0.3, 11.6), (9.6, 1.0, 0.7))
    k.box(WHITE, (0, -0.21, 11.6), (9.6, 0.02, 0.12))
    k.box(DARK_STEEL, (0, 0.3, 0.2), (7.4, 1.2, 0.4))
    export(k.obj(), "scoreboard")


def tv_tower():
    """A scaffold TV tower: a platform on a braced frame with a ladder, a camera on a tripod, the operator under
    a little canopy."""
    k = Kit()
    h = 5.0
    tube = mat("scaffold", (0.72, 0.74, 0.78), 0.35, 0.9)
    for x in (-1.0, 1.0):
        for y in (-1.0, 1.0):
            k.tube(tube, (x, y, 0), (x, y, h + 1.1), 0.04, segs=6)
    for z in (0.1, 1.7, 3.3, h):
        for a, b in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            k.tube(tube, (a[0], a[1], z), (b[0], b[1], z), 0.035, segs=6)
    for (a, b) in (((-1, -1), (1, -1)), ((1, 1), (-1, 1)), ((1, -1), (1, 1)), ((-1, 1), (-1, -1))):
        k.tube(tube, (a[0], a[1], 0.1), (b[0], b[1], 3.3), 0.03, segs=6)
    for z in (h + 0.5, h + 1.05):  # railings
        for a, b in (((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            k.tube(tube, (a[0], a[1], z), (b[0], b[1], z), 0.03, segs=6)
    k.box(WOOD, (0, 0, h + 0.05), (2.2, 2.2, 0.1))
    k.box(mat("tower_skirt", (0.1, 0.25, 0.62), 0.6), (0, -1.03, h - 0.3), (2.1, 0.03, 0.6))
    for i in range(10):  # the ladder at the back
        k.box(tube, (0, 1.05, 0.4 + i * 0.5), (0.5, 0.04, 0.04))
    for x in (-0.25, 0.25):
        k.tube(tube, (x, 1.05, 0), (x, 1.05, h), 0.025, segs=4)
    # the camera: tripod, a long body with a lens hood, a viewfinder
    cam_body = mat("tv_camera", (0.12, 0.12, 0.14), 0.4, 0.3)
    for a in range(3):
        ang = a * 2 * math.pi / 3
        k.tube(DARK_STEEL, (0, -0.3, h + 1.2), (0.45 * math.cos(ang), -0.3 + 0.45 * math.sin(ang), h + 0.1), 0.02, segs=4)
    k.box(cam_body, (0, -0.35, h + 1.35), (0.3, 0.7, 0.35))
    k.tube(cam_body, (0, -0.7, h + 1.35), (0, -1.05, h + 1.35), 0.12, 0.15, 12)
    k.tube(mat("lens", (0.3, 0.4, 0.6), 0.05, 0.5), (0, -1.05, h + 1.35), (0, -1.07, h + 1.35), 0.13, segs=12)
    k.box(cam_body, (0.2, -0.2, h + 1.55), (0.12, 0.18, 0.12))
    # the operator, in a padded jacket and a beanie
    jacket = mat("crew_jacket", (0.9, 0.45, 0.1), 0.8)
    k.tube(mat("trousers", (0.13, 0.13, 0.17), 0.85), (0.1, 0.35, h + 0.1), (0.1, 0.3, h + 0.9), 0.14, 0.16, 8)
    k.tube(jacket, (0.1, 0.25, h + 0.9), (0.1, 0.1, h + 1.55), 0.22, 0.17, 10)
    k.ball(mat("face", (0.92, 0.72, 0.58), 0.6), (0.1, 0.05, h + 1.72), 0.11)
    k.ball(mat("beanie", (0.1, 0.1, 0.12), 0.9), (0.1, 0.07, h + 1.78), 0.115, (1, 1, 0.8))
    k.tube(jacket, (0.3, 0.1, h + 1.45), (0.2, -0.2, h + 1.4), 0.06, segs=6)
    # the canopy on a pole
    k.tube(tube, (0.9, 0.9, h), (0.9, 0.9, h + 2.6), 0.03, segs=6)
    k.tube(mat("canopy", (0.95, 0.95, 0.97), 0.6), (0.9, 0.9, h + 2.3), (0.9, 0.9, h + 2.75), 1.4, 0.05, 12, smooth=False)
    export(k.obj(), "tv_tower")


def judges_tower():
    """The judges' tower: a concrete shaft with stepped, glazed boxes facing the hill (-Y), a flat roof with
    antennae, an outside stair."""
    k = Kit()
    k.box(CONCRETE, (0, 0.5, 6.0), (4.2, 4.2, 12.0))
    for i in range(3):  # three judges' floors stepping forward as they go up
        z = 8.0 + i * 2.6
        y = -1.0 - i * 0.4
        k.box(WHITE, (0, y, z), (5.6, 4.0, 2.5))
        k.box(WINDOW, (0, y - 2.01, z + 0.15), (5.3, 0.04, 1.6))
        for x in (-1.8, -0.6, 0.6, 1.8):
            k.box(WHITE, (x, y - 2.03, z + 0.15), (0.08, 0.04, 1.6))
        k.box(RED, (0, y - 2.05, z - 1.05), (5.6, 0.06, 0.25))
    k.box(DARK_STEEL, (0, -1.2, 15.2), (6.2, 5.0, 0.3))
    for x in (-1.5, 1.8):
        k.tube(STEEL, (x, 0.5, 15.3), (x, 0.5, 17.8), 0.04, segs=6)
    # the stair up the side
    for i in range(24):
        k.box(DARK_STEEL, (2.6, 1.8 - (i % 12) * 0.3, 0.3 + i * 0.5), (1.0, 0.3, 0.06))
    for i in range(2):
        k.box(DARK_STEEL, (2.6, -2.0 + i * 4.2, 6.0), (1.0, 0.3, 0.06))
    k.bar(STEEL, (3.1, 1.8, 1.0), (3.1, -1.8, 6.5), 0.05)
    k.bar(STEEL, (3.1, 1.8, 7.0), (3.1, -1.8, 12.5), 0.05)
    k.box(BLUE, (0, 2.62, 6.0), (4.2, 0.04, 1.2))
    export(k.obj(), "judges_tower")


def start_house():
    """The start house at the top of the in-run: a timber-clad cabin with a pitched, snowy roof, a glazed front
    looking down the track, a balcony and the coaches' platform."""
    timber = mat("timber", (0.45, 0.28, 0.16), 0.8)
    k = Kit()
    k.box(timber, (0, 0, 2.2), (6.0, 6.0, 4.4))
    for i in range(10):  # cladding boards
        k.box(timber, (-3.02, -2.7 + i * 0.6, 2.2), (0.05, 0.12, 4.4))
        k.box(timber, (3.02, -2.7 + i * 0.6, 2.2), (0.05, 0.12, 4.4))
    k.box(WINDOW, (0, -3.02, 2.6), (4.6, 0.05, 1.8))
    for x in (-1.5, 0.0, 1.5):
        k.box(WHITE, (x, -3.05, 2.6), (0.1, 0.05, 1.9))
    k.box(WINDOW, (3.03, 0, 2.6), (0.05, 3.0, 1.4))
    k.box(WINDOW, (-3.03, 0, 2.6), (0.05, 3.0, 1.4))
    # the pitched roof, with snow on it
    for s in (-1, 1):
        k.box(RED, (s * 1.7, 0, 5.15), (3.8, 7.0, 0.2), ry=s * 0.45)
        k.box(SNOW, (s * 1.66, 0, 5.3), (3.6, 6.8, 0.14), ry=s * 0.45)
    for y in (-3.0, 2.9):  # the gables
        k.rings(timber, [[(-3.0, y, 4.4), (3.0, y, 4.4), (0.0, y, 5.85)], [(-3.0, y + 0.1, 4.4), (3.0, y + 0.1, 4.4), (0.0, y + 0.1, 5.85)]], smooth=False)
    # the balcony
    k.box(DARK_STEEL, (0, -3.8, 1.2), (6.0, 1.6, 0.12))
    for x in range(7):
        k.box(STEEL, (-3.0 + x, -4.55, 1.7), (0.05, 0.05, 1.0))
    k.box(STEEL, (0, -4.55, 2.2), (6.0, 0.06, 0.06))
    k.box(BLUE, (0, -4.57, 1.6), (6.0, 0.04, 0.6))
    k.tube(STEEL, (2.7, 2.7, 5.0), (2.7, 2.7, 8.5), 0.04, segs=6)
    export(k.obj(), "start_house")


def boulder():
    """A rock with a snow cap, for the forests and the valley edges."""
    rock = mat("rock_grey", (0.36, 0.36, 0.38), 0.9)
    rng = random.Random(3)
    k = Kit()
    rings = []
    for j, (z, r) in enumerate(((0.0, 1.0), (0.4, 1.1), (0.9, 0.95), (1.3, 0.6), (1.5, 0.15))):
        rings.append([((r + rng.uniform(-0.15, 0.15)) * math.cos(2 * math.pi * i / 9) * 1.3,
                       (r + rng.uniform(-0.15, 0.15)) * math.sin(2 * math.pi * i / 9), z + rng.uniform(-0.1, 0.1)) for i in range(9)])
    k.rings(rock, rings, smooth=False)
    k.rings(SNOW, [[(p[0] * 0.9, p[1] * 0.9, p[2] + 0.12) for p in rings[3]], [(p[0], p[1], p[2] + 0.1) for p in rings[4]]], smooth=True)
    export(k.obj(), "boulder")


reset()
podium()
flagpole()
spectator()
trees()
cauldron()
floodlight()
finish_arch()
start_gate()
grandstand()
grandstand_end()
scoreboard()
tv_tower()
judges_tower()
start_house()
boulder()
