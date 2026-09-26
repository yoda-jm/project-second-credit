"""Props for game 4 (Whisker Alley): the alley (trash can, fence, washing, window, shutter, street lamp, boot), the
rooms (bowl, goldfish, eel, cheese, mouse, canary, cage, broom, furniture) and the rooms' dressing (sash window,
curtains and stage drapes, sconce, pendant lamp, picture frames, clock, potted plant). Deterministic; output CC BY-SA 4.0;
provenance: this script.
Run: blender -b --factory-startup -P tools/blender/whisker_models.py -- godot/games/whisker/art/models [cheese,furniture,...]
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


def sphere(r, loc, material, scale=(1, 1, 1), segs=20, rings=12, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc, rotation=rot)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, True)


def torus(R, r, loc, material, rot=(0, 0, 0), segs=24):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=segs, minor_segments=10)
    return put(active(), material, True)


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


def carve(o, cutters):
    """Boolean-subtracts the cutters from o (carved faces keep the cutters' materials), then deletes them."""
    col = bpy.data.collections.new("cutters")
    bpy.context.scene.collection.children.link(col)
    for c in cutters:
        for uc in list(c.users_collection):
            uc.objects.unlink(c)
        col.objects.link(c)
    m = o.modifiers.new("carve", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.operand_type = "COLLECTION"
    m.collection = col
    m.solver = "EXACT"
    try:
        m.material_mode = "TRANSFER"
    except Exception:
        pass
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=m.name)
    for c in cutters:
        bpy.data.objects.remove(c)
    bpy.data.collections.remove(col)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=0.7)
    except Exception:
        pass
    return o


def turned(h, r, loc, material, segs=16):
    """A turned leg or post of height h and radius r, standing on loc."""
    prof = [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.75, 0.03 * h), (r * 0.55, 0.1 * h), (r * 0.5, 0.42 * h),
            (r * 0.82, 0.5 * h), (r * 0.55, 0.56 * h), (r * 0.62, 0.66 * h), (r, 0.7 * h), (r, h), (0.0, h)]
    o = lathe(prof, material, segs)
    o.location = loc
    return o


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
    """The fish tank: glass, a rim, coloured pebbles, weed and a toy castle (the water is drawn by the game)."""
    glass = mat("glass", (0.8, 0.95, 1.0), 0.05, alpha=0.18)
    rim = mat("glass_rim", (0.2, 0.22, 0.25), 0.35, 0.6)
    sand = mat("gravel", (0.78, 0.66, 0.48), 0.9)
    parts = [box((6.0, 1.6, 4.2), (0, 0, 2.1), glass, bevel=0.1), box((6.1, 1.7, 0.1), (0, 0, 4.22), rim, bevel=0.03)]
    parts.append(box((6.1, 1.7, 0.12), (0, 0, 0.06), rim, bevel=0.03))
    parts.append(box((5.9, 1.5, 0.22), (0, 0, 0.23), sand, bevel=0.05))
    rnd = random.Random(3)
    pebble = [mat("pebble_%d" % i, c, 0.35, coat=0.6) for i, c in enumerate(
        [(0.85, 0.3, 0.3), (0.3, 0.5, 0.85), (0.95, 0.85, 0.4), (0.4, 0.75, 0.45), (0.92, 0.9, 0.86), (0.35, 0.3, 0.3)])]
    for i in range(110):
        x = rnd.uniform(-2.8, 2.8)
        y = rnd.uniform(-0.65, 0.65)
        parts.append(sphere(rnd.uniform(0.06, 0.11), (x, y, 0.36), pebble[rnd.randrange(len(pebble))], (1.2, 1.0, 0.6), 8, 5,
                            (0, 0, rnd.uniform(0, 3))))
    weed = mat("weed", (0.2, 0.6, 0.25), 0.6)
    weed2 = mat("weed_dark", (0.12, 0.42, 0.22), 0.6)
    for i in range(9):
        x = -2.7 + i * 0.66 + rnd.uniform(-0.2, 0.2)
        if 1.2 < x < 2.9:
            continue
        h = rnd.uniform(1.0, 2.6)
        y = rnd.uniform(0.1, 0.5)
        for k in range(3):
            dx = (k - 1) * 0.12
            parts.append(tube([(x + dx, y, 0.3), (x + dx + 0.18, y, 0.3 + h * 0.35), (x + dx - 0.12, y, 0.3 + h * 0.7), (x + dx + 0.1, y, 0.3 + h * (0.8 + 0.1 * k))],
                              0.045, weed if k != 1 else weed2, 0.012))
    stone = mat("toy_castle", (0.86, 0.78, 0.66), 0.75)
    roof = mat("toy_roof", (0.75, 0.25, 0.2), 0.5, coat=0.4)
    dark = mat("toy_door", (0.08, 0.06, 0.05), 0.9)
    cx = 2.0
    parts.append(box((0.9, 0.6, 0.7), (cx, 0.25, 0.7), stone, bevel=0.02))
    for k in range(4):
        parts.append(box((0.14, 0.6, 0.12), (cx - 0.36 + k * 0.24, 0.25, 1.11), stone, bevel=0.01))
    for tx, th in ((cx - 0.5, 1.25), (cx + 0.5, 1.0)):
        parts.append(cyl(0.2, th, (tx, 0.25, 0.35 + th / 2), stone, verts=16))
        parts.append(cyl(0.26, 0.42, (tx, 0.25, 0.35 + th + 0.21), roof, r2=0.0, verts=16))
    parts.append(cyl(0.14, 0.1, (cx, -0.06, 0.55), dark, rot=(math.pi / 2, 0, 0), verts=16))
    parts.append(box((0.28, 0.1, 0.2), (cx, -0.06, 0.45), dark))
    parts.append(box((0.12, 0.1, 0.16), (cx + 0.2, -0.06, 0.85), dark))
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
    """The cheese: two tiers of a cut block matching the room (tier tops at 2 and 4 m, 1.2 m inset per tier), with
    a waxy rind on top, rounded edges and holes carved into the cut faces."""
    ch = mat("cheese", (1.0, 0.8, 0.33), 0.42, coat=0.15)
    hole = mat("cheese_hole", (0.93, 0.64, 0.22), 0.55)
    rind = mat("cheese_rind", (0.92, 0.6, 0.12), 0.28, coat=0.6)
    rnd = random.Random(9)
    parts = []
    for k, (w, z0, z1) in enumerate(((6.6, 0.0, 2.0), (4.2, 2.0, 4.0))):
        h = z1 - z0 - 0.08
        body = box((w, 2.0, h), (0, 0, z0 + h / 2), ch, bevel=0.1)
        cutters, placed = [], []

        def fits(x, z, r):
            return all((x - px) ** 2 + (z - pz) ** 2 > (r + pr + 0.1) ** 2 for px, pz, pr in placed)

        tries = 0
        while len(placed) < (16 if k == 0 else 10) and tries < 400:  # holes on the front face
            tries += 1
            r = rnd.uniform(0.09, 0.36) if rnd.random() < 0.8 else rnd.uniform(0.05, 0.09)
            x = rnd.uniform(-w / 2 + 0.25, w / 2 - 0.25)
            z = rnd.uniform(z0 + 0.15, z0 + h - 0.1)
            if k == 0 and abs(x) < 2.1 + r and z > 1.6:  # hidden under the upper tier anyway
                continue
            if not fits(x, z, r):
                continue
            placed.append((x, z, r))
            cutters.append(sphere(r, (x, -1.0 + r * rnd.uniform(-0.1, 0.35), z), hole, segs=24, rings=14))
        for sx in (-1, 1):  # a few on the cut ends, and bites out of the edges
            for i in range(3):
                r = rnd.uniform(0.12, 0.28)
                cutters.append(sphere(r, (sx * (w / 2 + r * 0.2), rnd.uniform(-0.8, 0.5), rnd.uniform(z0 + 0.3, z0 + h - 0.3)), hole, segs=20, rings=12))
        cutters.append(sphere(0.3, (-w / 2 + 0.6, -1.05, z0 + h - 0.05), hole, segs=24, rings=14))
        carve(body, cutters)
        parts.append(body)
        parts.append(box((w - 0.04, 1.96, 0.1), (0, 0, z1 - 0.05), rind, bevel=0.04))
    for i in range(9):  # crumbs at the foot of the cheese
        parts.append(sphere(rnd.uniform(0.04, 0.08), (rnd.uniform(-3.8, 3.8), rnd.uniform(-1.6, -1.05), 0.03), ch, (1, 1, 0.6), 8, 5,
                            (rnd.random(), rnd.random(), rnd.random())))
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


WALNUT = mat("wood_dark", (0.35, 0.2, 0.12), 0.6)
BRASS = mat("brass", (1.0, 0.76, 0.38), 0.28, 1.0)
VELVET = mat("upholstery", (0.5, 0.14, 0.17), 0.9)


def panel(w, h, loc, material):
    """A raised-panel front (drawer or door): a flat board with a bevelled field standing out of it."""
    x, y, z = loc
    return [box((w, 0.05, h), (x, y, z), material, bevel=0.015),
            box((w - 0.18, 0.05, h - 0.16), (x, y - 0.025, z), material, bevel=0.035)]


def pull(x, y, z, span=0.28):
    """A brass bar handle on two posts, with round roses."""
    parts = [tube([(x - span / 2, y, z), (x - span / 2, y - 0.07, z), (x + span / 2, y - 0.07, z), (x + span / 2, y, z)], 0.018, BRASS)]
    for s_ in (-1, 1):
        parts.append(cyl(0.04, 0.02, (x + s_ * span / 2, y + 0.005, z), BRASS, rot=(math.pi / 2, 0, 0), verts=14))
    return parts


def cornice(w, z, material):
    """Stacked mouldings under the top board (the top stays at z)."""
    return [box((w + 0.02, 0.92, 0.06), (0, 0, z - 0.11), material, bevel=0.02),
            cyl(0.035, w - 0.02, (0, -0.44, z - 0.16), material, rot=(0, math.pi / 2, 0), verts=12)]


def carcass(w, h, material, open_from=0.0):
    """Plinth with bracket feet, the body, pilasters at the front corners and an overhanging top (top face at h).
    Above open_from (if given) the body is an open case: sides and a dark back."""
    parts = [box((w - 0.04, 0.86, 0.14), (0, 0, 0.2), material, bevel=0.02)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.2, 0.2, 0.16), (sx * (w / 2 - 0.12), sy * 0.33, 0.08), material, bevel=0.03))
    body_top = open_from if open_from else h - 0.09
    parts.append(box((w - 0.1, 0.84, body_top - 0.27), (0, 0.01, (0.27 + body_top) / 2), material, bevel=0.02))
    if open_from:
        for sx in (-1, 1):
            parts.append(box((0.08, 0.84, h - open_from), (sx * (w / 2 - 0.09), 0.01, (open_from + h) / 2), material, bevel=0.01))
        parts.append(box((w - 0.2, 0.05, h - open_from), (0, 0.4, (open_from + h) / 2), mat("case_back", (0.12, 0.07, 0.05), 0.8)))
    for sx in (-1, 1):
        parts.append(box((0.1, 0.05, h - 0.42), (sx * (w / 2 - 0.07), -0.43, 0.27 + (h - 0.42) / 2), material, bevel=0.015))
    parts.append(box((w + 0.1, 0.98, 0.09), (0, 0, h - 0.045), material, bevel=0.035))
    return parts


def furniture():
    """Walnut chests and cases with raised panels and brass pulls, turned legs, upholstered seats. The natural
    sizes are the ones the game scales from (width x height of the walkable top)."""
    fabric = mat("tablecloth", (0.78, 0.72, 0.62), 0.9)
    trim = mat("cloth_trim", (0.75, 0.2, 0.22), 0.8)
    for name, (w, h) in {"chair": (1.4, 1.8), "cabinet": (1.6, 3.4), "dresser": (1.6, 2.4), "table": (7.2, 1.0),
                         "stool": (1.6, 1.4), "shelf": (1.5, 2.8), "bookcase": (1.4, 3.0), "small_chair": (1.0, 1.2)}.items():
        parts = []
        if name in ("chair", "small_chair", "stool"):
            seat_z = h - 0.14
            parts.append(box((w, 0.9, 0.1), (0, 0, seat_z - 0.05), WOOD, bevel=0.025))  # seat frame
            parts.append(box((w - 0.12, 0.8, 0.16), (0, 0, h - 0.08), VELVET, bevel=0.06))  # cushion, top at h
            for sx in (-1, 1):
                parts.append(box((w - 0.2, 0.05, 0.12), (0, sx * 0.4, seat_z - 0.16), WOOD, bevel=0.01))  # apron
                parts.append(box((0.05, 0.75, 0.12), (sx * (w / 2 - 0.08), 0, seat_z - 0.16), WOOD, bevel=0.01))
                for sy in (-1, 1):
                    parts.append(turned(seat_z - 0.1, 0.07, (sx * (w / 2 - 0.1), sy * 0.35, 0), WOOD))
                parts.append(cyl(0.025, 0.7, (sx * (w / 2 - 0.1), 0, (seat_z - 0.1) * 0.3), WOOD, rot=(math.pi / 2, 0, 0), verts=8))  # stretcher
            if name != "stool":
                bh = 0.95 if name == "chair" else 0.75
                for sx in (-1, 1):
                    parts.append(cyl(0.05, bh + 0.1, (sx * (w / 2 - 0.1), 0.38, h + bh / 2 - 0.05), WOOD, verts=12))
                    parts.append(sphere(0.07, (sx * (w / 2 - 0.1), 0.38, h + bh), WOOD))
                parts.append(tube([(-w / 2 + 0.1, 0.38, h + bh - 0.1), (0, 0.44, h + bh + 0.02), (w / 2 - 0.1, 0.38, h + bh - 0.1)], 0.06, WOOD))
                parts.append(box((w * 0.3, 0.04, bh - 0.25), (0, 0.4, h + (bh - 0.25) / 2 + 0.05), WOOD, bevel=0.015))  # splat
                for sx in (-1, 1):
                    parts.append(cyl(0.022, bh - 0.2, (sx * w * 0.3, 0.4, h + (bh - 0.2) / 2 + 0.02), WOOD, verts=8))
        elif name == "table":
            parts.append(box((w, 1.8, 0.1), (0, 0, h - 0.07), WOOD, bevel=0.03))
            parts.append(box((w - 0.4, 1.5, 0.16), (0, 0, h - 0.2), WOOD, bevel=0.01))  # apron
            legs = (-1, -0.33, 0.33, 1) if w > 4 else (-1, 1)
            for sx in legs:
                for sy in (-1, 1):
                    parts.append(turned(h - 0.12, 0.08, (sx * (w / 2 - 0.25), sy * 0.68, 0), WOOD))
            # a runner down the middle with a trimmed hem hanging over the front (the walkable top stays at h)
            parts.append(box((w * 0.62, 1.84, 0.02), (0, 0, h - 0.01), fabric, bevel=0.005))
            parts.append(box((w * 0.62, 0.02, 0.3), (0, -0.92, h - 0.15), fabric, bevel=0.005))
            parts.append(box((w * 0.62 + 0.01, 0.025, 0.05), (0, -0.925, h - 0.28), trim))
            for i in range(int(w * 0.62 / 0.2)):
                parts.append(sphere(0.025, (-w * 0.31 + 0.1 + i * 0.2, -0.93, h - 0.33), trim, segs=8, rings=5))
        elif name == "bookcase":
            parts += carcass(w, h, WALNUT, 1.02) + cornice(w, h, WALNUT)
            for i, z in enumerate((1.05, 1.95)):
                parts.append(box((w - 0.16, 0.8, 0.06), (0, -0.04, z), WALNUT, bevel=0.01))
            for sx in (-1, 1):  # two doors below
                parts += panel((w - 0.26) / 2, 0.66, (sx * (w - 0.26) / 4, -0.45, 0.62), WALNUT)
                parts.append(sphere(0.045, (sx * 0.08, -0.5, 0.64), BRASS))
            rnd = random.Random(4)
            cols = [(0.55, 0.12, 0.12), (0.12, 0.25, 0.45), (0.15, 0.38, 0.22), (0.7, 0.52, 0.18), (0.35, 0.18, 0.32), (0.82, 0.78, 0.66)]
            for z in (1.08, 1.98):
                x = -w / 2 + 0.16
                while x < w / 2 - 0.3:
                    bw = rnd.uniform(0.07, 0.13)
                    bh = rnd.uniform(0.5, 0.78)
                    c = mat("book_%d" % rnd.randrange(len(cols)), cols[rnd.randrange(len(cols))], 0.7)
                    lean = 0.18 if rnd.random() < 0.12 else 0.0
                    parts.append(box((bw, 0.55, bh), (x + bw / 2, -0.12, z + bh / 2 * math.cos(lean)), c, rot=(0, lean, 0), bevel=0.012))
                    parts.append(box((bw + 0.004, 0.02, 0.03), (x + bw / 2, -0.4, z + bh * 0.8), mat("book_gilt", (1.0, 0.78, 0.35), 0.3, 1.0), rot=(0, lean, 0), bevel=0.0))
                    x += bw + 0.005 + (0.08 if lean else 0)
                parts.append(sphere(0.12, (w / 2 - 0.18, -0.15, z + 0.12), mat("globe", (0.25, 0.5, 0.65), 0.35, coat=0.6)))
        elif name == "shelf":  # an open kitchen dresser with jars and plates
            parts += carcass(w, h, WALNUT, 1.02) + cornice(w, h, WALNUT)
            parts += panel(w - 0.26, 0.66, (0, -0.45, 0.62), WALNUT)
            parts += pull(0, -0.5, 0.64)
            glass = mat("jar_glass", (0.75, 0.85, 0.8), 0.1, alpha=0.5)
            lid = mat("jar_lid", (0.75, 0.2, 0.15), 0.4)
            plate = mat("plate", (0.92, 0.93, 0.95), 0.25, coat=0.5)
            for z in (1.05, 1.95):
                parts.append(box((w - 0.16, 0.8, 0.06), (0, -0.04, z), WALNUT, bevel=0.01))
            for i, x in enumerate((-0.4, 0.0, 0.4)):
                jh = (0.42, 0.55, 0.36)[i]
                parts.append(lathe([(0.0, 0.0), (0.13, 0.0), (0.15, 0.04), (0.15, jh - 0.08), (0.1, jh - 0.02), (0.0, jh - 0.02)], glass, 20))
                active().location = (x, -0.15, 1.08)
                parts.append(cyl(0.11, 0.06, (x, -0.15, 1.08 + jh), lid, verts=20, bevel=0.01))
            for x in (-0.35, 0.0, 0.35):
                parts.append(cyl(0.3, 0.03, (x, -0.1, 2.3), plate, rot=(math.pi / 2 - 0.12, 0, 0), verts=28))
                parts.append(cyl(0.2, 0.035, (x, -0.11, 2.3), mat("plate_rim", (0.2, 0.35, 0.65), 0.3, coat=0.5), rot=(math.pi / 2 - 0.12, 0, 0), verts=24))
        else:  # cabinet, dresser: drawers (and doors up high on the tall cabinet)
            parts += carcass(w, h, WALNUT) + cornice(w, h, WALNUT)
            top = h - 0.25
            if name == "cabinet":
                for sx in (-1, 1):
                    parts += panel((w - 0.3) / 2, 1.35, (sx * (w - 0.3) / 4, -0.45, top - 0.72), WALNUT)
                    parts.append(sphere(0.045, (sx * 0.1, -0.5, top - 0.75), BRASS))
                    parts.append(box((0.04, 0.02, 0.1), (sx * 0.1, -0.49, top - 0.9), mat("keyhole", (0.05, 0.04, 0.03), 0.6)))
                top -= 1.47
            rows = max(2, round((top - 0.3) / 0.62))
            rh = (top - 0.3) / rows
            for k in range(rows):
                z = 0.3 + rh * (k + 0.5)
                parts += panel(w - 0.3, rh - 0.08, (0, -0.45, z), WALNUT)
                parts += pull(0, -0.5, z, 0.3 if w > 1.2 else 0.2)
        export(parts, name)


# ------------------------------------------------------------------ room dressing

def room_window():
    """The sash window the cat comes in through, seen from inside: opening 1.8 x 1.8 (bottom at z = 0, the wall face
    at y = 0), moulded architrave, a deep reveal, two sashes of six panes, a sill, and a brass curtain rod above.
    The glass and the night outside are drawn by the game."""
    paint = mat("window_paint", (0.93, 0.91, 0.86), 0.45)
    parts = []
    for s_ in (-1, 1):  # architrave
        parts.append(box((0.2, 0.08, 2.18), (s_ * 1.0, -0.04, 0.99), paint, bevel=0.025))
        parts.append(box((0.08, 0.1, 2.1), (s_ * 0.94, -0.06, 0.99), paint, bevel=0.02))
    parts.append(box((2.3, 0.1, 0.22), (0, -0.05, 1.99), paint, bevel=0.03))
    parts.append(box((2.45, 0.16, 0.08), (0, -0.08, 2.12), paint, bevel=0.03))  # head moulding
    for s_ in (-1, 1):  # reveal
        parts.append(box((0.04, 0.34, 1.8), (s_ * 0.9, 0.17, 0.9), paint))
    parts.append(box((1.8, 0.34, 0.04), (0, 0.17, 1.8), paint))
    for z0 in (0.0, 0.9):  # two sashes, 3 x 2 panes each
        y = 0.24 if z0 == 0 else 0.3
        for s_ in (-1, 1):
            parts.append(box((0.08, 0.06, 0.9), (s_ * 0.86, y, z0 + 0.45), paint, bevel=0.01))
        for z in (z0 + 0.04, z0 + 0.86):
            parts.append(box((1.8, 0.06, 0.08), (0, y, z), paint, bevel=0.01))
        for x in (-0.28, 0.28):
            parts.append(box((0.035, 0.05, 0.9), (x, y, z0 + 0.45), paint))
        parts.append(box((1.8, 0.05, 0.035), (0, y, z0 + 0.45), paint))
    parts.append(box((0.12, 0.03, 0.03), (0, 0.2, 0.93), BRASS, bevel=0.008))  # the sash lock
    parts.append(box((2.3, 0.4, 0.07), (0, -0.08, -0.035), paint, bevel=0.025))  # sill
    parts.append(box((1.9, 0.06, 0.25), (0, -0.03, -0.2), paint, bevel=0.02))  # apron
    parts.append(cyl(0.028, 3.3, (0, -0.2, 2.38), BRASS, rot=(0, math.pi / 2, 0), verts=12))  # curtain rod
    for s_ in (-1, 1):
        parts.append(sphere(0.07, (s_ * 1.7, -0.2, 2.38), BRASS))
        parts.append(tube([(s_ * 1.45, 0.0, 2.38), (s_ * 1.45, -0.2, 2.38)], 0.02, BRASS))
    for i in range(10):
        x = (-1.55 + i * 0.1) if i < 5 else (1.15 + (i - 5) * 0.1)
        parts.append(torus(0.05, 0.01, (x, -0.2, 2.38), BRASS, (0, math.pi / 2, 0)))
    export(parts, "room_window")


def curtain(name="curtain", W=1.0, H=3.0, folds=6.5, depth=1.0, mirror=False, rope_r=0.03, tassel=1.0):
    """A heavy curtain hanging from z = H to the floor, gathered by a tie-back and falling in folds. The gathered
    side is -x (+x for the mirrored one)."""
    cloth = mat("curtain", (0.5, 0.12, 0.14), 0.85)
    nu, nv = int(folds * 10), 40
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    grid = []
    for j in range(nv + 1):
        v = j / nv
        g = math.exp(-((v - 0.62) / 0.16) ** 2)  # the gather at the tie-back
        f = 1.0 - 0.55 * g
        row = []
        for i in range(nu + 1):
            u = i / nu
            x = (u - 0.5) * W * f - (1.0 - f) * W * 0.28 + 0.06 * W * v * v * (u - 0.5)
            y = depth * ((0.05 + 0.05 * g + 0.02 * v) * math.sin(u * 2 * math.pi * folds + v * 0.6) - 0.05)
            row.append(bm.verts.new((-x if mirror else x, y, H * (1.0 - v) + 0.02 * math.sin(u * 40) * v ** 4)))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            q = (grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1])
            bm.faces.new(tuple(reversed(q)) if mirror else q)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    sol = o.modifiers.new("s", "SOLIDIFY")
    sol.thickness = 0.02 * depth
    bpy.ops.object.modifier_apply(modifier=sol.name)
    parts = [put(o, cloth, True)]
    rope = mat("tassel", (0.95, 0.72, 0.3), 0.45, 0.6)
    z = H * (1.0 - 0.62)
    m = -1 if mirror else 1
    cx = m * -0.55 * W * 0.28  # the centre of the gathered cloth
    rx = 0.27 * W
    ring = [(cx + rx * math.cos(t), depth * (-0.05 + 0.14 * math.sin(t)), z + 0.03 * math.sin(2 * t)) for t in [2 * math.pi * k / 24 for k in range(25)]]
    parts.append(tube(ring, rope_r, rope))
    parts.append(sphere(0.06 * tassel, (cx, -0.2 * depth, z - 0.02), rope))  # the knot and its tassel
    parts.append(cyl(0.1 * tassel, 0.3 * tassel, (cx, -0.2 * depth, z - 0.2 * tassel), rope, r2=0.035 * tassel, verts=16))
    export(parts, name)


def curtains():
    curtain()
    curtain("curtain_r", mirror=True)
    curtain("drape", W=6.0, H=16.5, folds=13.0, depth=2.5, rope_r=0.07, tassel=2.5)
    curtain("drape_r", W=6.0, H=16.5, folds=13.0, depth=2.5, mirror=True, rope_r=0.07, tassel=2.5)


def sconce():
    """A wall light: a brass back plate, an arm curling up and a frosted tulip shade (origin on the wall)."""
    shade = mat("sconce_glass", (1.0, 0.86, 0.62), 0.3, emit=2.5)
    parts = [lathe([(0.0, -0.02), (0.1, -0.02), (0.12, 0.0), (0.1, 0.02), (0.0, 0.03)], BRASS, 20)]
    parts[-1].rotation_euler = (math.pi / 2, 0, 0)
    parts.append(tube([(0, -0.02, 0), (0, -0.2, -0.04), (0, -0.32, 0.06), (0, -0.33, 0.16)], 0.018, BRASS))
    parts.append(cyl(0.035, 0.06, (0, -0.33, 0.18), BRASS, verts=12))
    parts.append(lathe([(0.03, 0.2), (0.06, 0.22), (0.12, 0.3), (0.16, 0.42), (0.15, 0.44), (0.1, 0.34), (0.05, 0.26)], shade, 24))
    active().location = (0, -0.33, 0)
    export(parts, "sconce")


def pendant():
    """A ceiling light: a cord and a fabric drum shade with a glowing bulb (origin at the shade bottom)."""
    shade = mat("lamp_shade", (0.98, 0.86, 0.62), 0.8, emit=0.8)
    bulb = mat("bulb", (1.0, 0.9, 0.7), 0.2, emit=8.0)
    parts = [cyl(0.012, 4.0, (0, 0, 2.6), mat("cord", (0.08, 0.07, 0.06), 0.6), verts=6)]
    parts.append(lathe([(0.55, 0.0), (0.56, 0.02), (0.4, 0.55), (0.39, 0.57), (0.38, 0.55), (0.54, 0.02)], shade, 40))
    for z, r in ((0.02, 0.56), (0.55, 0.4)):
        parts.append(torus(r, 0.015, (0, 0, z), BRASS, segs=40))
    parts.append(cyl(0.06, 0.12, (0, 0, 0.6), BRASS, verts=12))
    parts.append(sphere(0.13, (0, 0, 0.3), bulb, (1, 1, 1.2)))
    export(parts, "pendant")


def frames():
    """Gilded picture frames with a canvas (material "canvas", painted by the game's shader; UV 0-1 over it)."""
    gilt = mat("gilt", (0.95, 0.72, 0.32), 0.32, 1.0)
    for name, (w, h) in {"frame_wide": (1.9, 1.3), "frame_tall": (1.1, 1.5)}.items():
        parts = []
        for s_ in (-1, 1):
            parts.append(box((0.14, 0.1, h + 0.14), (s_ * (w / 2), -0.05, 0), gilt, bevel=0.03))
            parts.append(box((w + 0.14, 0.1, 0.14), (0, -0.05, s_ * (h / 2)), gilt, bevel=0.03))
            parts.append(box((0.04, 0.12, h - 0.06), (s_ * (w / 2 - 0.09), -0.06, 0), gilt, bevel=0.012))
            parts.append(box((w - 0.14, 0.12, 0.04), (0, -0.06, s_ * (h / 2 - 0.09)), gilt, bevel=0.012))
            for t in (-1, 1):  # corner ornaments
                parts.append(sphere(0.07, (s_ * w / 2, -0.1, t * h / 2), gilt, (1, 0.6, 1), 12, 8))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.02, 0), rotation=(math.pi / 2, 0, 0))
        o = active()
        o.scale = (w - 0.16, h - 0.16, 1)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(put(o, mat("canvas", (0.5, 0.5, 0.5), 0.8)))
        export(parts, name)


def clock():
    """A round wall clock: a turned wooden rim, a cream face with hour marks and hands at ten past ten."""
    face = mat("clock_face", (0.95, 0.92, 0.82), 0.5)
    ink = mat("clock_ink", (0.08, 0.07, 0.06), 0.4)
    parts = [cyl(0.6, 0.08, (0, -0.04, 0), WALNUT, rot=(math.pi / 2, 0, 0), verts=48, bevel=0.03)]
    parts.append(torus(0.56, 0.05, (0, -0.09, 0), BRASS, (math.pi / 2, 0, 0), 48))
    parts.append(cyl(0.52, 0.02, (0, -0.09, 0), face, rot=(math.pi / 2, 0, 0), verts=48))
    for k in range(12):
        a = k * math.pi / 6
        big = k % 3 == 0
        parts.append(box((0.03 if big else 0.018, 0.01, 0.1 if big else 0.06), (0.43 * math.sin(a), -0.105, 0.43 * math.cos(a)), ink, rot=(0, a, 0), bevel=0.0))
    for a, l, t in ((math.radians(-60), 0.26, 0.035), (math.radians(60), 0.38, 0.022)):
        parts.append(box((t, 0.01, l), (0.5 * l * math.sin(a), -0.115, 0.5 * l * math.cos(a)), ink, rot=(0, a, 0), bevel=0.0))
    parts.append(cyl(0.035, 0.03, (0, -0.12, 0), BRASS, rot=(math.pi / 2, 0, 0), verts=12))
    export(parts, "clock")


def plant():
    """A potted plant: a terracotta pot and broad leaves on arching stems (about 1.7 m)."""
    pot = mat("terracotta", (0.72, 0.36, 0.22), 0.8)
    leaf = mat("leaf", (0.2, 0.45, 0.2), 0.5, coat=0.3)
    stem = mat("leaf_stem", (0.3, 0.45, 0.2), 0.7)
    parts = [lathe([(0.0, 0.0), (0.3, 0.0), (0.4, 0.62), (0.47, 0.64), (0.47, 0.76), (0.4, 0.78), (0.37, 0.7), (0.0, 0.7)], pot, 32)]
    parts.append(cyl(0.37, 0.02, (0, 0, 0.7), mat("potting_soil", (0.15, 0.1, 0.07), 0.95), verts=32))
    rnd = random.Random(11)
    for i in range(11):
        a = i * 2.4 + rnd.uniform(-0.3, 0.3)
        h = rnd.uniform(0.6, 1.1)
        reach = rnd.uniform(0.25, 0.6)
        tip = (reach * math.cos(a), reach * math.sin(a) * 0.6, 0.7 + h)
        parts.append(tube([(0.03 * math.cos(a), 0.03 * math.sin(a), 0.7), (tip[0] * 0.4, tip[1] * 0.4, 0.7 + h * 0.7), tip], 0.015, stem, 0.008))
        parts.append(sphere(0.22, (tip[0] * 1.15, tip[1] * 1.15, tip[2] + 0.1), leaf, (0.45, 1.0, 0.08), 16, 8,
                            (rnd.uniform(-0.6, 0.6), rnd.uniform(0.3, 1.0) * (1 if tip[0] > 0 else -1), a + math.pi / 2)))
    export(parts, "plant")


def milk_bowl():
    bowl_m = mat("dog_bowl", (0.75, 0.15, 0.12), 0.35, coat=0.4)
    # the milk is drawn by the game (it goes down as the cat drinks)
    export([lathe([(0.32, 0.0), (0.4, 0.02), (0.46, 0.22), (0.42, 0.24), (0.36, 0.08), (0.0, 0.08)], bowl_m)], "milk_bowl")


def heart():
    """A heart-shaped platform 1.8 m wide, flat top at z = 0 (the game stands the cat on it)."""
    pink = mat("heart", (0.95, 0.25, 0.45), 0.35, coat=0.5, emit=0.3)
    cu = bpy.data.curves.new("heart", "CURVE")
    cu.dimensions = "2D"
    sp = cu.splines.new("POLY")
    pts = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 18.0 * 0.9, y / 18.0 * 0.9))
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = (x, y, 0, 1)
    sp.use_cyclic_u = True
    cu.fill_mode = "BOTH"
    cu.extrude = 0.12
    cu.bevel_depth = 0.04
    o = bpy.data.objects.new("heart", cu)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.pi / 2, 0, 0)  # stand it up facing the camera
    o.location = (0, 0, -0.55)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=True, rotation=True)
    export([put(active(), pink, True)], "heart")


def arrow():
    gold = mat("arrow_gold", (1.0, 0.8, 0.35), 0.3, 1.0)
    feather = mat("arrow_feather", (0.95, 0.95, 1.0), 0.8)
    tip = mat("arrow_tip", (1.0, 0.3, 0.5), 0.3, emit=0.8)
    parts = [cyl(0.018, 1.0, (0, 0, 0), gold, rot=(0, math.pi / 2, 0), verts=8)]
    for s_ in (-1, 1):
        parts.append(box((0.18, 0.01, 0.07), (0.45, 0, 0.04 * s_), feather, rot=(0, 0.3 * s_, 0), bevel=0.0))
    parts.append(sphere(0.06, (-0.52, 0, 0), tip, (1.2, 0.5, 1.0)))
    export(parts, "arrow")


reset()
ALL = [milk_bowl, heart, arrow, trash_can, fence, washing, window, lamp, boot, bowl, goldfish, eel, cheese, mouse, canary,
       cage, broom, furniture, room_window, curtains, sconce, pendant, frames, clock, plant]
only = sys.argv[sys.argv.index("--") + 2].split(",") if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 2 else []
for build in ALL:  # optional second argument: a comma-separated list of builders to run
    if not only or build.__name__ in only:
        build()
