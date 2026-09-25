"""Procedural models for game 3 (Fruitburrow). Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/fruitburrow_models.py -- godot/games/fruitburrow/art/models
One garden cell = 1 m. Z is up in Blender (Y up in the exported files); models face -Y (towards the camera).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
MATS = {}


def mat(name, color, rough=0.5, metal=0.0, emit=0.0, coat=0.0):
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
    MATS[name] = m
    return m


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def active():
    return bpy.context.active_object


def smooth(o, levels=2):
    s = o.modifiers.new("s", "SUBSURF")
    s.levels = levels
    s.render_levels = levels
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=s.name)
    bpy.ops.object.shade_smooth()
    return o


def sphere(r, loc, material, scale=(1, 1, 1), segs=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    return o


def lathe(profile, material, segs=32, loc=(0, 0, 0)):
    """Surface of revolution around Z from [(radius, z), ...], bottom to top."""
    me = bpy.data.meshes.new("lathe")
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        c = bm.verts.new((0, 0, profile[0][1] if flip else profile[-1][1]))
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((ring[j], ring[i], c) if flip else (ring[i], ring[j], c))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("lathe", me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    return o


def tube(points, r, material, r_end=None, segs=8):
    """A tapered tube along a polyline (stems, stalks)."""
    cu = bpy.data.curves.new("tube", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (*p, 1)
        k = i / max(1, len(points) - 1)
        sp.points[i].radius = 1.0 + ((r_end if r_end is not None else r) / r - 1.0) * k
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    o = bpy.data.objects.new("tube", cu)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects:
        x.select_set(False)
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = active()
    o.data.materials.clear()
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o


def leaf(loc, size, material, rot=(0, 0, 0)):
    """A curved leaf: a flattened, pointed, slightly bent sheet."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(0, 0, 0))
    o = active()
    for v in o.data.vertices:
        x, y, z = v.co
        taper = 1.0 - abs(x) ** 1.6
        v.co = Vector((x * size, y * size * 0.45 * max(taper, 0.05), z * size * 0.06 + (x * x) * size * 0.25))
    o.location = loc
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    return o


def join(parts, name):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = active()
    o.name = name
    return o


def export_glb(name):
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)


def finish(parts, name):
    o = join(parts, name)
    for x in bpy.context.scene.objects:
        x.select_set(x == o)
    export_glb(name)
    reset()


STEM = None
LEAF = None


def shared():
    global STEM, LEAF
    STEM = mat("stem", (0.33, 0.22, 0.1), 0.8)
    LEAF = mat("fruit_leaf", (0.2, 0.55, 0.12), 0.45)


# ------------------------------------------------------------------ fruit

def cherries():
    red = mat("cherry", (0.55, 0.01, 0.03), 0.12, coat=0.6)
    parts = []
    for sx, h in ((-0.12, 0.0), (0.12, 0.04)):
        b = sphere(0.13, (sx, 0, -0.1 + h), red, (1.0, 1.0, 0.92))
        parts.append(b)
        parts.append(tube([(sx, 0, 0.02 + h), (sx * 0.6, 0, 0.18), (0.0, 0, 0.3)], 0.012, STEM, 0.009))
    parts.append(leaf((0.12, 0, 0.3), 0.14, LEAF, (0.2, -0.3, 0.5)))
    finish(parts, "cherries")


def banana():
    yellow = mat("banana", (0.95, 0.75, 0.1), 0.4)
    tip = mat("banana_tip", (0.25, 0.18, 0.08), 0.6)
    # a tapered tube along an arc, pentagonal like a real banana
    pts = []
    for i in range(12):
        a = math.radians(-60 + 120 * i / 11)
        pts.append((math.sin(a) * 0.32, 0, -math.cos(a) * 0.32 + 0.12))
    body = tube(pts, 0.13, yellow, 0.07, segs=5)
    for v in body.data.vertices:  # fatter in the middle
        k = 1.0 - abs(v.co.x) / 0.32
        v.co.z -= 0.0
        v.co.y *= 0.8 + 0.5 * k
    parts = [body]
    parts.append(tube([(-0.28, 0, -0.05), (-0.33, 0, 0.0), (-0.36, 0, 0.06)], 0.022, yellow, 0.018))
    parts.append(sphere(0.025, (-0.36, 0, 0.07), tip))
    parts.append(sphere(0.02, (0.28, 0, -0.04), tip))
    finish(parts, "banana")


def pear():
    skin = mat("pear", (0.62, 0.75, 0.15), 0.35)
    prof = [(0.0, -0.3), (0.15, -0.29), (0.24, -0.22), (0.27, -0.12), (0.24, -0.02), (0.17, 0.06), (0.12, 0.14),
            (0.1, 0.2), (0.06, 0.25), (0.0, 0.26)]
    body = lathe(prof, skin)
    smooth(body, 1)
    body.rotation_euler = (0, math.radians(8), 0)
    parts = [body, tube([(0, 0, 0.24), (0.02, 0, 0.32), (0.05, 0, 0.36)], 0.014, STEM, 0.01)]
    parts.append(leaf((0.13, 0, 0.33), 0.12, LEAF, (0.1, -0.4, 0.3)))
    finish(parts, "pear")


def grapes():
    purple = mat("grape", (0.25, 0.05, 0.35), 0.18, coat=0.4)
    rnd = random.Random(3)
    parts = []
    rows = [(0.2, 4), (0.1, 4), (0.0, 3), (-0.1, 3), (-0.2, 2), (-0.28, 1)]
    for z, n in rows:
        w = n * 0.075
        for i in range(n):
            x = -w / 2 + 0.075 * (i + 0.5) + rnd.uniform(-0.01, 0.01)
            for y in ((-0.04, 0.04) if n > 1 else (0.0,)):
                parts.append(sphere(0.062, (x, y + rnd.uniform(-0.01, 0.01), z), purple, segs=16, rings=10))
    parts.append(tube([(0, 0, 0.22), (0.0, 0, 0.32), (0.04, 0, 0.36)], 0.016, STEM, 0.012))
    parts.append(leaf((-0.12, 0, 0.3), 0.15, LEAF, (0.1, 0.3, -0.4)))
    finish(parts, "grapes")


def strawberry():
    red = mat("strawberry", (0.8, 0.05, 0.06), 0.3, coat=0.3)
    seed = mat("seed", (0.95, 0.85, 0.3), 0.4)
    prof = [(0.0, -0.26), (0.06, -0.24), (0.13, -0.16), (0.19, -0.05), (0.21, 0.05), (0.19, 0.13), (0.12, 0.18),
            (0.0, 0.19)]
    body = lathe(prof, red, segs=24)
    smooth(body, 1)
    parts = [body]
    rnd = random.Random(5)
    for i in range(36):  # seeds on the surface
        z = rnd.uniform(-0.2, 0.14)
        # radius of the profile at height z (linear between the points)
        for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
            if z0 <= z <= z1:
                r = r0 + (r1 - r0) * (z - z0) / (z1 - z0)
                break
        a = rnd.uniform(0, 2 * math.pi)
        parts.append(sphere(0.012, (math.cos(a) * r * 0.98, math.sin(a) * r * 0.98, z), seed, (1, 1, 1.6), 8, 6))
    for k in range(6):  # green calyx
        a = k * math.pi / 3
        parts.append(leaf((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.19), 0.09, LEAF, (0, -0.25, a)))
    parts.append(tube([(0, 0, 0.18), (0, 0, 0.26)], 0.012, LEAF, 0.01))
    finish(parts, "strawberry")


def apple():
    red = mat("apple", (0.72, 0.05, 0.04), 0.25, coat=0.5)
    prof = [(0.0, -0.3), (0.08, -0.32), (0.2, -0.29), (0.31, -0.18), (0.36, -0.03), (0.35, 0.1), (0.3, 0.2),
            (0.2, 0.26), (0.08, 0.24), (0.0, 0.18)]  # a dimple at the top
    body = lathe(prof, red)
    smooth(body, 1)
    parts = [body, tube([(0, 0, 0.19), (0.02, 0, 0.3), (0.06, 0, 0.36)], 0.018, STEM, 0.012)]
    parts.append(leaf((0.16, 0, 0.32), 0.15, LEAF, (0.3, -0.3, 0.2)))
    finish(parts, "apple")


# ------------------------------------------------------------------ monsters

def eyes(parts, y, z, sx, r, look=(0.0, 0.0)):
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.15, coat=0.8)
    black = mat("pupil", (0.02, 0.02, 0.03), 0.1, coat=1.0)
    shine = mat("eye_shine", (1, 1, 1), 0.1, emit=2.0)
    for s in (-1, 1):
        parts.append(sphere(r, (sx * s, y, z), white, (1, 0.7, 1.15), 20, 12))
        parts.append(sphere(r * 0.5, (sx * s + look[0] * r, y - r * 0.6, z + look[1] * r), black, (1, 0.6, 1.2), 16, 10))
        parts.append(sphere(r * 0.14, (sx * s + r * 0.2, y - r * 0.9, z + r * 0.35), shine, segs=8, rings=6))


def plum():
    skin = mat("plum", (0.3, 0.06, 0.4), 0.3, coat=0.7)
    dark = mat("plum_dark", (0.12, 0.02, 0.15), 0.5)
    body = sphere(0.36, (0, 0, 0.0), skin, (1.0, 0.95, 1.05), 32, 20)
    for v in body.data.vertices:  # a plum's groove down the front
        if v.co.y < 0:
            v.co.y *= 1.0 - 0.1 * math.exp(-(v.co.x / 0.06) ** 2)
    parts = [body]
    eyes(parts, -0.26, 0.1, 0.11, 0.1, look=(0.0, -0.1))
    # frowning brows and a small grin
    for s in (-1, 1):
        parts.append(tube([(0.2 * s, -0.33, 0.25), (0.05 * s, -0.36, 0.2)], 0.02, dark))
    parts.append(tube([(-0.1, -0.35, -0.08), (0.0, -0.36, -0.12), (0.1, -0.35, -0.08)], 0.018, dark))
    for s in (-1, 1):  # little feet
        parts.append(sphere(0.09, (0.15 * s, -0.05, -0.36), dark, (1.2, 1.4, 0.6)))
    parts.append(tube([(0, 0, 0.36), (0.03, 0, 0.45), (0.07, 0, 0.5)], 0.02, STEM, 0.014))
    parts.append(leaf((0.15, 0, 0.48), 0.14, LEAF, (0.2, -0.3, 0.3)))
    finish(parts, "plum")


def digger():
    fur = mat("digger_fur", (0.28, 0.2, 0.15), 0.85)
    nose = mat("digger_nose", (0.95, 0.45, 0.55), 0.35, coat=0.4)
    claw = mat("digger_claw", (0.9, 0.85, 0.75), 0.3)
    tooth = mat("digger_tooth", (1.0, 0.98, 0.9), 0.2)
    body = sphere(0.36, (0, 0.02, -0.02), fur, (1.05, 1.0, 0.95), 32, 20)
    parts = [body]
    snout = sphere(0.14, (0, -0.32, -0.02), fur, (1.0, 1.1, 0.8))
    parts.append(snout)
    parts.append(sphere(0.07, (0, -0.47, 0.0), nose))
    eyes(parts, -0.24, 0.14, 0.13, 0.075, look=(0.0, 0.0))
    for s in (-1, 1):  # buck teeth and big digging claws
        parts.append(sphere(0.035, (0.025 * s, -0.42, -0.1), tooth, (0.8, 0.5, 1.4)))
        paw = sphere(0.1, (0.3 * s, -0.2, -0.22), fur, (1.3, 1.0, 0.7))
        parts.append(paw)
        for k in range(3):
            parts.append(tube([(0.3 * s + (k - 1) * 0.05, -0.28, -0.24), (0.3 * s + (k - 1) * 0.06, -0.36, -0.3)], 0.02, claw, 0.006))
    for s in (-1, 1):  # ears
        parts.append(sphere(0.06, (0.24 * s, 0.05, 0.28), fur, (1.0, 0.5, 1.0)))
    finish(parts, "digger")


reset()
shared()
cherries()
banana()
pear()
grapes()
strawberry()
apple()
plum()
digger()
