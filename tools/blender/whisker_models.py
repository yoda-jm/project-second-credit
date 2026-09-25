"""Props for game 4 (Whisker Alley): the alley (trash can, fence, washing, window, shutter, street lamp, boot) and the
rooms (bowl, goldfish, eel, cheese, mouse, canary, cage, broom, furniture). Deterministic; output CC BY-SA 4.0;
provenance: this script.
Run: blender -b --factory-startup -P tools/blender/whisker_models.py -- godot/games/whisker/art/models
1 unit = 1 m, Z up in Blender, fronts face -Y (towards the camera). Materials named "wood", "metal", "brick" are
swapped for the shared PBR ones in the game.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

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
        m.blend_method = "BLEND"
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
    else:
        bpy.ops.object.shade_flat()
    return o


def box(size, loc, material, rot=(0, 0, 0), bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, bevel=bevel)


def cyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=24, smooth=True, bevel=0.0):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return put(active(), material, smooth, bevel)


def sphere(r, loc, material, scale=(1, 1, 1), segs=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, True)


def tube(points, r, material, r_end=None):
    cu = bpy.data.curves.new("t", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (*p, 1)
        sp.points[i].radius = 1.0 + ((r_end if r_end is not None else r) / r - 1.0) * i / max(1, len(points) - 1)
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    o = bpy.data.objects.new("t", cu)
    bpy.context.collection.objects.link(o)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return put(active(), material, True)


def lathe(profile, material, segs=40):
    me = bpy.data.meshes.new("lathe")
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z))
                      for i in range(segs)])
    for k in range(len(rings) - 1):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("lathe", me)
    bpy.context.collection.objects.link(o)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    return put(o, material, True)


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


WOOD = mat("wood", (0.55, 0.38, 0.22), 0.8)
METAL = mat("metal", (0.55, 0.57, 0.6), 0.45, 0.8)
DARK = mat("dark_metal", (0.2, 0.21, 0.23), 0.5, 0.7)


# ------------------------------------------------------------------ alley

def trash_can():
    body = lathe([(0.52, 0.0), (0.56, 0.05), (0.6, 1.1), (0.62, 1.12)], METAL, 36)
    parts = [body]
    for z in (0.25, 0.6, 0.95):  # ribs
        parts.append(cyl(0.61, 0.05, (0, 0, z), METAL, verts=36))
    lid = lathe([(0.66, 1.12), (0.66, 1.17), (0.5, 1.25), (0.0, 1.29)], METAL, 36)
    parts += [lid, tube([(-0.12, 0, 1.28), (-0.1, 0, 1.36), (0.1, 0, 1.36), (0.12, 0, 1.28)], 0.02, DARK)]
    for s in (-1, 1):
        parts.append(tube([(0.6 * s, -0.12, 0.95), (0.66 * s, 0, 0.98), (0.6 * s, 0.12, 0.95)], 0.02, DARK))
    export(parts, "trash_can")


def fence():
    """A 2 m fence panel, 3.2 m tall: planks, two rails and a capping board (the walkable top)."""
    rnd = random.Random(2)
    parts = []
    for i in range(10):
        h = 3.05 + rnd.uniform(-0.05, 0.05)
        parts.append(box((0.19, 0.06, h), (-0.9 + i * 0.2, 0, h / 2), WOOD, bevel=0.012))
    for z in (0.7, 2.4):
        parts.append(box((2.0, 0.07, 0.14), (0, 0.06, z), WOOD))
    parts.append(box((2.0, 0.3, 0.07), (0, 0.02, 3.17), WOOD))
    export(parts, "fence")


def washing():
    rnd = random.Random(5)
    cols = [(0.9, 0.25, 0.25), (0.25, 0.5, 0.9), (0.95, 0.85, 0.3), (0.95, 0.95, 0.95), (0.4, 0.8, 0.45)]
    peg = mat("peg", (0.85, 0.7, 0.45), 0.7)
    for name, build in (("shirt", 0), ("socks", 1), ("towel", 2), ("dress", 3)):
        c = mat("cloth_" + name, cols[build % len(cols)], 0.9)
        parts = []
        if build == 0:
            parts.append(box((0.5, 0.04, 0.55), (0, 0, -0.33), c, bevel=0.02))
            for s in (-1, 1):
                parts.append(box((0.2, 0.04, 0.26), (0.32 * s, 0, -0.17), c, rot=(0, 0.5 * s, 0), bevel=0.02))
            parts.append(box((0.16, 0.05, 0.06), (0, -0.01, -0.07), mat("collar", (0.95, 0.95, 0.95), 0.9)))
        elif build == 1:
            for s in (-1, 1):
                parts.append(tube([(0.12 * s, 0, 0), (0.12 * s, 0, -0.3), (0.12 * s + 0.1, 0, -0.38)], 0.05, c))
                parts.append(cyl(0.052, 0.06, (0.12 * s, 0, -0.03), mat("sock_band", (0.95, 0.95, 0.95), 0.9)))
        elif build == 2:
            parts.append(box((0.55, 0.03, 0.8), (0, 0, -0.4), c, bevel=0.01))
            for z in (-0.15, -0.65):
                parts.append(box((0.56, 0.035, 0.06), (0, 0, z), mat("towel_stripe", (0.9, 0.3, 0.3), 0.9)))
        else:
            parts.append(cyl(0.12, 0.3, (0, 0, -0.15), c, r2=0.1, verts=16))
            parts.append(cyl(0.35, 0.5, (0, 0, -0.55), c, r2=0.12, verts=20))
        for s in (-1, 1):
            parts.append(box((0.03, 0.05, 0.1), (0.18 * s, 0, 0.0), peg, bevel=0.005))
        export(parts, name)


def window():
    """A window opening 1.6 x 1.5 (bottom at z = 0): frame, sill, a flower box. The dark room behind and the
    shutters are separate (the game opens and lights them)."""
    frame = mat("window_frame", (0.92, 0.9, 0.85), 0.5)
    box_m = mat("flower_box", (0.35, 0.55, 0.3), 0.7)
    parts = [box((1.8, 0.14, 0.1), (0, -0.02, 1.55), frame), box((1.8, 0.14, 0.1), (0, -0.02, -0.05), frame)]
    for s in (-1, 1):
        parts.append(box((0.1, 0.14, 1.6), (0.85 * s, -0.02, 0.75), frame))
    parts.append(box((2.0, 0.3, 0.07), (0, -0.14, -0.12), frame))  # sill
    parts.append(box((1.4, 0.24, 0.22), (0, -0.2, -0.28), box_m, bevel=0.02))
    rnd = random.Random(7)
    for i in range(9):
        x = -0.6 + i * 0.15
        stem = mat("flower_stem", (0.2, 0.5, 0.15), 0.7)
        c = mat("flower_%d" % (i % 3), [(0.95, 0.3, 0.4), (1.0, 0.85, 0.2), (0.7, 0.4, 0.95)][i % 3], 0.5)
        h = rnd.uniform(0.1, 0.22)
        parts.append(tube([(x, -0.2, -0.17), (x, -0.22, -0.17 + h)], 0.01, stem))
        parts.append(sphere(0.045, (x, -0.22, -0.15 + h), c, (1, 1, 0.7), 10, 6))
    export(parts, "window")
    shutter = mat("shutter", (0.12, 0.3, 0.2), 0.6)
    parts = [box((0.8, 0.05, 1.5), (0.4, 0, 0.75), shutter, bevel=0.01)]
    for k in range(9):
        parts.append(box((0.7, 0.07, 0.05), (0.4, -0.03, 0.12 + k * 0.155), shutter, rot=(0.4, 0, 0), bevel=0.005))
    export(parts, "shutter")  # hinged at x = 0


def lamp():
    iron = mat("lamp_iron", (0.08, 0.09, 0.1), 0.45, 0.6)
    glow = mat("lamp_glow", (1.0, 0.8, 0.45), 0.3, emit=6.0)
    parts = [cyl(0.06, 4.2, (0, 0, 2.1), iron, verts=12), cyl(0.18, 0.3, (0, 0, 0.15), iron, r2=0.08, verts=12)]
    parts.append(tube([(0, 0, 4.1), (0, -0.3, 4.4), (0, -0.7, 4.3)], 0.04, iron))
    parts.append(cyl(0.2, 0.25, (0, -0.7, 4.1), iron, r2=0.06, verts=12))
    parts.append(sphere(0.13, (0, -0.7, 3.95), glow))
    export(parts, "lamp")


def boot():
    leather = mat("boot", (0.3, 0.18, 0.1), 0.5, coat=0.3)
    sole = mat("boot_sole", (0.1, 0.08, 0.07), 0.8)
    parts = [box((0.18, 0.34, 0.06), (0, -0.04, 0.03), sole, bevel=0.02),
             sphere(0.12, (0, -0.12, 0.1), leather, (0.75, 1.3, 0.6)), cyl(0.09, 0.3, (0, 0.07, 0.22), leather, verts=16)]
    parts.append(tube([(-0.05, -0.1, 0.16), (0.05, -0.05, 0.2), (-0.05, 0.0, 0.24)], 0.008, mat("lace", (0.9, 0.9, 0.85), 0.8)))
    export(parts, "boot")


# ------------------------------------------------------------------ rooms

def bowl():
    glass = mat("glass", (0.8, 0.95, 1.0), 0.05, alpha=0.25)
    rim = mat("glass_rim", (0.85, 0.95, 1.0), 0.05, alpha=0.5)
    gravel = mat("gravel", (0.75, 0.55, 0.35), 0.9)
    parts = [box((6.0, 1.6, 4.2), (0, 0, 2.1), glass, bevel=0.1), box((6.1, 1.7, 0.08), (0, 0, 4.2), rim, bevel=0.03)]
    parts.append(box((5.9, 1.5, 0.3), (0, 0, 0.15), gravel, bevel=0.05))
    weed = mat("weed", (0.2, 0.6, 0.25), 0.6)
    rnd = random.Random(3)
    for i in range(7):
        x = -2.6 + i * 0.85 + rnd.uniform(-0.2, 0.2)
        h = rnd.uniform(1.0, 2.4)
        parts.append(tube([(x, 0.3, 0.3), (x + 0.15, 0.3, 0.3 + h * 0.4), (x - 0.1, 0.3, 0.3 + h * 0.75), (x + 0.1, 0.3, 0.3 + h)], 0.05, weed, 0.02))
    castle = mat("toy_castle", (0.9, 0.75, 0.55), 0.7)
    parts += [box((0.6, 0.5, 0.7), (2.0, 0.3, 0.65), castle), cyl(0.2, 0.9, (2.35, 0.3, 0.75), castle, verts=12)]
    export(parts, "bowl")


def goldfish():
    orange = mat("goldfish", (1.0, 0.45, 0.05), 0.3, coat=0.6)
    fin = mat("goldfish_fin", (1.0, 0.65, 0.25), 0.4)
    eye = mat("fish_eye", (0.02, 0.02, 0.02), 0.1, coat=1.0)
    parts = [sphere(0.2, (0, 0, 0), orange, (1.5, 0.6, 1.0))]
    parts.append(sphere(0.14, (0.38, 0, 0), fin, (0.8, 0.15, 1.3)))  # tail (+x is the tail; the fish faces -x)
    parts.append(sphere(0.08, (0.0, 0, 0.2), fin, (1.2, 0.15, 0.8)))
    for s in (-1, 1):
        parts.append(sphere(0.035, (-0.18, 0.1 * s, 0.05), eye))
    export(parts, "goldfish")


def eel():
    green = mat("eel", (0.2, 0.45, 0.2), 0.3, coat=0.5)
    zap = mat("eel_stripe", (1.0, 0.95, 0.3), 0.3, emit=1.5)
    eye = mat("eel_eye", (1, 1, 0.5), 0.2, emit=2.0)
    pts = [(-0.6 + i * 0.12, 0, 0.08 * math.sin(i * 0.9)) for i in range(11)]
    parts = [tube(pts, 0.09, green, 0.02)]
    for i in (2, 4, 6, 8):
        p = pts[i]
        parts.append(cyl(0.1 - i * 0.008, 0.03, p, zap, rot=(0, math.pi / 2, 0), verts=12))
    parts.append(sphere(0.02, (-0.62, -0.06, 0.04), eye))
    parts.append(sphere(0.02, (-0.62, 0.06, 0.04), eye))
    export(parts, "eel")


def cheese():
    """The cheese: a wedge in three tiers matching the room (tier tops at 2 and 4 m, 1.2 m inset per tier)."""
    ch = mat("cheese", (1.0, 0.8, 0.25), 0.5)
    hole = mat("cheese_hole", (0.75, 0.5, 0.1), 0.7)
    parts = []
    for k, (w, h) in enumerate(((9.0 - 2.4, 2.0), (9.0 - 4.8, 4.0))):
        parts.append(box((w, 2.0, h - (2.0 if k else 0.0)), (0, 0, (h + (2.0 if k else 0.0)) / 2), ch, bevel=0.05))
    rnd = random.Random(9)
    for i in range(14):  # holes on the face
        x = rnd.uniform(-3.0, 3.0)
        z = rnd.uniform(0.3, 3.6)
        if (z > 2.0 and abs(x) > 2.1) or abs(x) > 3.1:
            continue
        parts.append(cyl(rnd.uniform(0.12, 0.3), 0.06, (x, -1.0, z), hole, rot=(math.pi / 2, 0, 0), verts=16))
    export(parts, "cheese")


def mouse():
    grey = mat("mouse", (0.6, 0.58, 0.6), 0.8)
    pinkm = mat("mouse_pink", (0.95, 0.6, 0.65), 0.5)
    eye = mat("mouse_eye", (0.02, 0.02, 0.02), 0.1, coat=1.0)
    parts = [sphere(0.12, (0, 0, 0.1), grey, (1.5, 0.9, 0.85)), sphere(0.07, (-0.2, 0, 0.13), grey, (1.3, 0.9, 0.9))]
    for s in (-1, 1):
        parts.append(sphere(0.05, (-0.15, 0.06 * s, 0.22), pinkm, (0.4, 1, 1)))
        parts.append(sphere(0.015, (-0.26, 0.04 * s, 0.16), eye))
    parts.append(sphere(0.018, (-0.3, 0, 0.12), pinkm))
    parts.append(tube([(0.17, 0, 0.08), (0.3, 0, 0.12), (0.42, 0, 0.2)], 0.012, pinkm, 0.005))
    export(parts, "mouse")


def canary():
    yellow = mat("canary", (1.0, 0.85, 0.15), 0.5)
    beak = mat("beak", (1.0, 0.55, 0.1), 0.4)
    eye = mat("canary_eye", (0.02, 0.02, 0.02), 0.1, coat=1.0)
    parts = [sphere(0.13, (0, 0, 0), yellow, (1.3, 0.9, 1.0)), sphere(0.09, (-0.14, 0, 0.1), yellow)]
    parts.append(sphere(0.03, (-0.24, 0, 0.09), beak, (1.4, 0.7, 0.7)))
    for s in (-1, 1):
        parts.append(sphere(0.015, (-0.18, 0.06 * s, 0.13), eye))
        parts.append(sphere(0.08, (0.02, 0.12 * s, 0.03), yellow, (1.2, 0.3, 0.6)))  # wings
    parts.append(sphere(0.07, (0.2, 0, 0.02), yellow, (1.2, 0.3, 0.4)))
    export(parts, "canary")


def cage():
    gold = mat("cage_gold", (1.0, 0.75, 0.3), 0.3, 1.0)
    parts = [cyl(0.7, 0.08, (0, 0, 0.04), gold, verts=24), cyl(0.7, 0.05, (0, 0, 1.2), gold, verts=24)]
    for i in range(16):
        a = i * math.pi / 8
        parts.append(cyl(0.012, 1.2, (0.68 * math.cos(a), 0.68 * math.sin(a), 0.6), gold, verts=6))
    dome = lathe([(0.7, 1.2), (0.62, 1.4), (0.4, 1.55), (0.0, 1.6)], gold, 24)
    parts += [dome, tube([(0, 0, 1.6), (0, 0, 1.75), (0.08, 0, 1.82)], 0.02, gold)]
    parts.append(cyl(0.012, 1.3, (0, 0, 0.7), gold, rot=(0, math.pi / 2, 0), verts=6))  # perch
    export(parts, "cage")


def broom():
    straw = mat("broom_straw", (0.85, 0.7, 0.35), 0.9)
    band = mat("broom_band", (0.7, 0.15, 0.1), 0.5)
    parts = [cyl(0.03, 1.6, (0, 0, 1.2), WOOD, verts=10), cyl(0.2, 0.55, (0, 0, 0.27), straw, r2=0.07, verts=16)]
    parts.append(cyl(0.08, 0.06, (0, 0, 0.5), band, verts=16))
    export(parts, "broom")


def furniture():
    for name, (w, h) in {"chair": (1.4, 1.8), "cabinet": (1.6, 3.4), "dresser": (1.6, 2.4), "table": (7.2, 1.0),
                         "stool": (1.6, 1.4), "shelf": (1.5, 2.8), "bookcase": (1.4, 3.0), "small_chair": (1.0, 1.2)}.items():
        parts = []
        if name in ("chair", "small_chair", "stool"):
            parts.append(box((w, 0.9, 0.1), (0, 0, h - 0.05), WOOD, bevel=0.02))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    parts.append(box((0.08, 0.08, h - 0.1), (sx * (w / 2 - 0.08), sy * 0.35, (h - 0.1) / 2), WOOD))
            if name != "stool":
                parts.append(box((w, 0.08, 0.9), (0, 0.4, h + 0.45), WOOD, bevel=0.02))
        elif name == "table":
            parts.append(box((w, 1.8, 0.12), (0, 0, h - 0.06), WOOD, bevel=0.02))
            cloth = mat("tablecloth", (0.85, 0.25, 0.25), 0.8)
            parts.append(box((w + 0.1, 1.85, 0.03), (0, 0, h + 0.01), cloth))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    parts.append(box((0.12, 0.12, h - 0.12), (sx * (w / 2 - 0.2), sy * 0.7, (h - 0.12) / 2), WOOD))
        else:
            parts.append(box((w, 0.9, h), (0, 0, h / 2), WOOD, bevel=0.03))
            knob = mat("knob", (0.9, 0.75, 0.3), 0.3, 1.0)
            rows = max(1, int(h / 0.8))
            for k in range(rows):
                z = 0.4 + k * (h - 0.4) / rows
                parts.append(box((w - 0.2, 0.05, (h - 0.4) / rows - 0.12), (0, -0.46, z + ((h - 0.4) / rows) / 2 - 0.05), WOOD, bevel=0.01))
                parts.append(sphere(0.04, (0, -0.5, z + ((h - 0.4) / rows) / 2), knob))
            if name == "bookcase":
                rnd = random.Random(4)
                for k in range(10):
                    c = mat("book_%d" % (k % 4), [(0.7, 0.2, 0.2), (0.2, 0.4, 0.7), (0.2, 0.55, 0.3), (0.8, 0.65, 0.2)][k % 4], 0.7)
                    parts.append(box((0.1, 0.5, rnd.uniform(0.4, 0.6)), (-0.5 + (k % 5) * 0.22, -0.2, 1.0 + (k // 5) * 1.0 + 0.3), c))
        export(parts, name)


reset()
trash_can()
fence()
washing()
window()
lamp()
boot()
bowl()
goldfish()
eel()
cheese()
mouse()
canary()
cage()
broom()
furniture()
