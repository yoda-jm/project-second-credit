"""Biosurge (game 34) world kit: the small living things that dress the cavern walls and the abyss below the play
plane. Original designs (polyps, tube corals, egg clusters, crystals, tendrils, ribs, bio-machinery pipes, glowing
plants, spore pods, vents, anemones, fan corals, chitin spines, pustules), made to be instanced many times.
Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/biosurge_world.py -- godot/games/biosurge/art/world [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, ...), mossfolk_models.py (lathe_r, lumpy).

Each file holds ONE mesh named like the file, origin at the base centre, growing up (Godot +Y), about 1 unit tall
(scale it in the game). The materials are ROLES, not colours: the game (view3d/bio_world.gd) swaps each one for its
theme's shader by name: flesh (the soft body), dark (the darker underside, mouths, seams), shell (bone, chitin,
coral skeleton), metal (bio-machinery), crystal (faceted, glassy), egg (translucent, lit from inside), glow (the
emissive accent: mouths, tips, bulbs, rims; "glow" is in its name). Base colours here are neutral greys only for the
Blender preview.

polyp         a curved stalk, a bulb head with a glowing mouth ring and six little tentacles (1.0 tall)
tube_coral    five open tubes of different heights with glowing rims and throats (1.1)
egg_cluster   seven eggs on a lumpy sac (0.7)
crystal       a cluster of seven hexagonal crystals (1.2)
tendril       a tapered, curling tentacle with a glowing tip (2.0): the game sways it
rib           a bone rib arching over (1.6 tall, 2.2 across X)
pipe          a bio-machinery pipe: an arch with flanges, a valve wheel and a glowing gauge (1.2)
glow_plant    a stalk with five drooping branches ending in glowing bulbs, and leaves (1.3)
spore_pod     an open pod full of glowing spores (0.8)
vent          a chimney with a glowing throat (1.2)
anemone       a ring of fourteen tentacles with glowing tips (0.7)
fan_coral     a branching flat fan (1.4 tall, its face towards Godot +Z) with glowing tips
spine         a curved chitin thorn with a glowing ring at its base (1.3)
pustule       a blister mound with a glowing heart and veins (0.45)
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, reset, cyl
from mossfolk_models import lathe_r, lumpy

ROLE = {}


def roles():
    ROLE["flesh"] = mat("flesh", (0.55, 0.5, 0.5), rough=0.45)
    ROLE["dark"] = mat("dark", (0.2, 0.18, 0.18), rough=0.6)
    ROLE["shell"] = mat("shell", (0.8, 0.78, 0.72), rough=0.5)
    ROLE["metal"] = mat("metal", (0.45, 0.45, 0.48), rough=0.35, metal=0.8)
    ROLE["crystal"] = mat("crystal", (0.85, 0.85, 0.9), rough=0.1)
    ROLE["egg"] = mat("egg", (0.8, 0.8, 0.7), rough=0.25)
    ROLE["glow"] = mat("glow", (1.0, 1.0, 1.0), emit=4.0)


def F(name):
    return ROLE[name]


def export_one(parts, name):
    o = join(parts, name)
    K.deselect()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True, export_animations=False)
    print("exported %-12s %6d tris" % (name, K.tris(o)))


def curve_pts(a, b, bend, n=8, wobble=0.0, seed=0):
    """Points from a to b bowed sideways by the vector `bend` (a quadratic arc), with optional wobble."""
    a, b, bend = Vector(a), Vector(b), Vector(bend)
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        p = a.lerp(b, t) + bend * (4 * t * (1 - t))
        if wobble and 0 < i < n - 1:
            p += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3))) * wobble
        pts.append(p)
    return pts


def taper(n, r0, r1, power=1.0):
    return [r0 + (r1 - r0) * (i / (n - 1)) ** power for i in range(n)]


# ------------------------------------------------------------------ the kit

def polyp():
    stalk = curve_pts((0, 0, 0), (0.12, 0.05, 0.62), (0.12, -0.05, 0.0), n=7)
    parts = [tube(stalk, taper(7, 0.12, 0.08), F("flesh"), verts=10, caps=False)]
    parts.append(lumpy(0.17, (0, 0, 0.02), F("flesh"), 3, amount=0.15, scale=(1.3, 1.3, 0.6), sub=2, smooth=60))
    head = Vector((0.12, 0.05, 0.74))
    parts.append(sphere(0.2, head, F("flesh"), scale=(1, 1, 0.85), segs=14, rings=10))
    parts.append(torus(0.13, 0.04, head + Vector((0, 0, 0.15)), F("glow"), verts=16, minor=6))
    parts.append(cyl(0.11, 0.03, head + Vector((0, 0, 0.16)), F("dark"), verts=12))
    for k in range(6):
        a = k * math.tau / 6
        base = head + Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, 0.13))
        tip = base + Vector((math.cos(a) * 0.17, math.sin(a) * 0.17, 0.14))
        parts.append(rod(base, tip, 0.028, F("flesh"), r2=0.006, verts=6))
        parts.append(ico(0.022, tip, F("glow"), sub=1))
    # a ridge of dark spots down the head
    for k in range(5):
        a = k * 1.3
        parts.append(ico(0.03, head + Vector((math.cos(a) * 0.19, math.sin(a) * 0.19, -0.04 + 0.02 * k)), F("dark"),
                         scale=(1, 1, 0.5), sub=1))
    export_one(parts, "polyp")


def open_tube(r, h, loc, rim_glow=True):
    """A tube open at the top with a thickness, a flared lip and a glowing throat."""
    x, y, z = loc
    prof = [(r * 0.78, h - 0.02), (r * 1.08, h + 0.01), (r * 1.15, h - 0.04), (r, h - 0.15), (r * 0.92, h * 0.5),
            (r * 1.05, 0.06), (r * 1.25, 0.0)]
    o = lathe_r(prof, F("shell"), segs=14, center=(x, y, z), name="tube")
    inner = lathe_r([(r * 0.78, h - 0.02), (r * 0.74, h - 0.25), (0.0, h - 0.27)], F("dark"), segs=14,
                    center=(x, y, z), name="throat")
    # lathe_r faces point outward: flip the inside of the tube
    K.select(inner)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    out = [o, inner, cyl(r * 0.6, 0.02, (x, y, z + h - 0.24), F("glow"), verts=12)]
    if rim_glow:
        out.append(torus(r * 0.98, 0.022, (x, y, z + h + 0.005), F("glow"), verts=16, minor=5))
    return out


def tube_coral():
    parts = [lumpy(0.3, (0, 0, 0.0), F("flesh"), 11, amount=0.2, scale=(1.3, 1.1, 0.35), sub=2, smooth=50)]
    for (x, y, r, h) in [(0, 0, 0.13, 1.1), (0.2, 0.1, 0.1, 0.8), (-0.18, 0.12, 0.09, 0.65), (0.08, -0.22, 0.1, 0.55),
                         (-0.15, -0.15, 0.07, 0.4)]:
        parts += open_tube(r, h, (x, y, 0))
    export_one(parts, "tube_coral")


def egg_cluster():
    parts = [lumpy(0.3, (0, 0, 0.02), F("flesh"), 21, amount=0.22, scale=(1.3, 1.2, 0.45), sub=2, smooth=60)]
    rnd = random.Random(5)
    eggs = [(0, 0, 0.32, 0.17), (0.22, 0.06, 0.22, 0.13), (-0.2, 0.1, 0.22, 0.14), (0.05, 0.24, 0.2, 0.12),
            (-0.04, -0.23, 0.2, 0.13), (0.24, -0.16, 0.14, 0.1), (-0.25, -0.12, 0.15, 0.1)]
    for x, y, z, r in eggs:
        tilt = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)
        parts.append(sphere(r, (x, y, z), F("egg"), scale=(1, 1, 1.35), segs=14, rings=10, rot=tilt))
        parts.append(ico(r * 0.45, (x, y, z + r * 0.1), F("glow"), sub=1))  # the yolk (seen through the shell)
    for k in range(9):  # strands of slime between the eggs
        a = k * 0.7
        parts.append(rod((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.12), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.04),
                         0.018, F("dark"), r2=0.01, verts=5))
    export_one(parts, "egg_cluster")


def crystal_prism(base, axis, r, h, name="c"):
    """A hexagonal crystal from base along axis: a prism with a pointed six-faced tip, flat shaded."""
    axis = Vector(axis).normalized()
    prof = [(0.0, h), (r, h * 0.78), (r * 1.02, h * 0.15), (r * 0.9, 0.0), (0.0, 0.0)]
    o = lathe_r(prof, F("crystal"), segs=6, name=name, smooth=0)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)
    o.location = base
    K.select(o)
    bpy.ops.object.transform_apply(location=True, rotation=True)
    return o


def crystal():
    parts = [lumpy(0.28, (0, 0, 0.0), F("shell"), 31, amount=0.25, scale=(1.2, 1.2, 0.4), sub=1, smooth=0)]
    spec = [((0, 0, 0), (0, 0, 1), 0.12, 1.2), ((0.12, 0.05, 0), (0.45, 0.2, 1), 0.08, 0.8),
            ((-0.1, 0.08, 0), (-0.5, 0.3, 1), 0.09, 0.85), ((0.02, -0.12, 0), (0.1, -0.6, 1), 0.07, 0.6),
            ((-0.12, -0.06, 0), (-0.6, -0.4, 1), 0.06, 0.5), ((0.15, -0.1, 0), (0.7, -0.4, 1), 0.05, 0.4),
            ((0.05, 0.15, 0), (0.2, 0.8, 1), 0.06, 0.5)]
    for i, (b, a, r, h) in enumerate(spec):
        parts.append(crystal_prism(b, a, r, h, "c%d" % i))
    for k in range(5):  # glowing shards at the foot
        a = k * 1.25 + 0.4
        parts.append(crystal_prism((math.cos(a) * 0.24, math.sin(a) * 0.24, 0.0), (math.cos(a), math.sin(a), 1.4),
                                   0.03, 0.18, "g%d" % k))
        parts[-1].data.materials[0] = F("glow")
    export_one(parts, "crystal")


def tendril():
    pts = [Vector((0.0, 0.0, 0.0))]
    for i in range(1, 14):
        t = i / 13
        a = t * 4.2
        pts.append(Vector((0.35 * math.sin(a) * t, 0.18 * math.sin(a * 0.7) * t, 2.0 * t)))
    rad = taper(len(pts), 0.13, 0.015, 0.8)
    parts = [tube(pts, rad, F("flesh"), verts=9, caps=True)]
    for i in range(2, 12):  # suckers down the inner side
        p, r = pts[i], rad[i]
        parts.append(ico(r * 0.35, p + Vector((0, -r * 0.95, 0)), F("dark"), scale=(1, 0.5, 1), sub=1))
    parts.append(ico(0.04, pts[-1] + Vector((0, 0, 0.02)), F("glow"), sub=1))
    for i in (4, 7, 10):  # glowing bands
        parts.append(torus(rad[i] * 1.02, rad[i] * 0.18, pts[i], F("glow"), verts=10, minor=4))
    parts.append(lumpy(0.16, (0, 0, 0.0), F("dark"), 41, amount=0.2, scale=(1.2, 1.2, 0.4), sub=1, smooth=50))
    export_one(parts, "tendril")


def rib():
    pts = []
    for i in range(13):
        t = i / 12
        a = math.pi * t
        pts.append(Vector((-1.1 * math.cos(a), 0.15 * math.sin(2 * a), 1.55 * math.sin(a) ** 0.8)))
    rad = [0.12 - 0.05 * math.sin(math.pi * i / 12) for i in range(13)]
    parts = [tube(pts, rad, F("shell"), verts=10, caps=True)]
    for end in (pts[0], pts[-1]):  # knuckles where it meets the wall
        parts.append(lumpy(0.17, end, F("shell"), 7, amount=0.12, scale=(1, 1, 0.8), sub=2, smooth=60))
        parts.append(lumpy(0.22, end - Vector((0, 0, 0.05)), F("flesh"), 8, amount=0.25, scale=(1.3, 1.3, 0.5), sub=1,
                           smooth=50))
    for i in (3, 6, 9):  # sinew bands
        parts.append(torus(rad[i] * 1.05, 0.025, pts[i], F("dark"), verts=10, minor=4,
                           rot=(0, math.atan2(pts[i + 1].x - pts[i - 1].x, pts[i + 1].z - pts[i - 1].z), 0)))
    export_one(parts, "rib")


def pipe():
    pts = [Vector((-0.5, 0, 0)), Vector((-0.5, 0, 0.6)), Vector((-0.42, 0, 0.95)), Vector((-0.2, 0, 1.12)),
           Vector((0.2, 0, 1.12)), Vector((0.42, 0, 0.95)), Vector((0.5, 0, 0.6)), Vector((0.5, 0, 0))]
    smooth = []
    for i in range(len(pts) - 1):  # resample for a rounder arch
        for k in range(4):
            smooth.append(pts[i].lerp(pts[i + 1], k / 4))
    smooth.append(pts[-1])
    parts = [tube(smooth, [0.11] * len(smooth), F("metal"), verts=12, caps=False)]
    for p in (smooth[2], smooth[8], smooth[14], smooth[20], smooth[26]):
        parts.append(cyl(0.15, 0.07, p, F("dark"), verts=12,
                         rot=(0, 0, 0) if abs(p.x) > 0.45 else (0, math.pi / 2, 0)))
    for x in (-0.5, 0.5):
        parts.append(cyl(0.2, 0.12, (x, 0, 0.06), F("metal"), verts=12, bevel=0.02))
        parts.append(lumpy(0.25, (x, 0, 0.0), F("flesh"), 9 + int(x * 10), amount=0.25, scale=(1.2, 1.2, 0.5), sub=1,
                           smooth=50))
    # a valve wheel and a glowing gauge on the arch
    parts.append(torus(0.12, 0.02, (0, -0.16, 1.12), F("metal"), rot=(math.pi / 2, 0, 0), verts=14, minor=5))
    parts.append(rod((0, -0.08, 1.12), (0, -0.17, 1.12), 0.02, F("metal"), verts=6))
    parts.append(cyl(0.08, 0.08, (-0.5, -0.12, 0.45), F("metal"), rot=(math.pi / 2, 0, 0), verts=12))
    parts.append(cyl(0.06, 0.02, (-0.5, -0.165, 0.45), F("glow"), rot=(math.pi / 2, 0, 0), verts=12))
    # glowing seams of fluid inside
    for p in (smooth[5], smooth[17], smooth[23]):
        parts.append(torus(0.115, 0.018, p, F("glow"), verts=12, minor=4,
                           rot=(0, math.pi / 2, 0) if abs(p.x) < 0.45 else (0, 0, 0)))
    export_one(parts, "pipe")


def glow_plant():
    parts = []
    stalk = curve_pts((0, 0, 0), (0.05, 0.0, 0.95), (0.1, 0.05, 0), n=7)
    parts.append(tube(stalk, taper(7, 0.06, 0.03), F("flesh"), verts=8, caps=True))
    top = stalk[-1]
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        start = stalk[3 + k % 3]
        mid = start + d * 0.25 + Vector((0, 0, 0.25))
        end = start + d * 0.42 + Vector((0, 0, 0.05 + 0.05 * k))
        br = [start, start.lerp(mid, 0.5) + Vector((0, 0, 0.05)), mid, mid.lerp(end, 0.6) + Vector((0, 0, 0.04)), end]
        parts.append(tube(br, taper(5, 0.025, 0.012), F("flesh"), verts=6, caps=False))
        parts.append(sphere(0.07, end - Vector((0, 0, 0.05)), F("glow"), scale=(1, 1, 1.25), segs=10, rings=7))
        parts.append(cyl(0.035, 0.03, end, F("dark"), verts=8))
    parts.append(sphere(0.09, top + Vector((0, 0, 0.05)), F("glow"), scale=(1, 1, 1.3), segs=12, rings=8))
    for k in range(4):  # leaves at the foot
        a = k * math.tau / 4 + 0.7
        d = Vector((math.cos(a), math.sin(a), 0))
        leaf = [Vector((0, 0, 0.02)), d * 0.18 + Vector((0, 0, 0.12)), d * 0.34 + Vector((0, 0, 0.1)),
                d * 0.45 + Vector((0, 0, 0.0))]
        o = tube(leaf, [0.02, 0.07, 0.05, 0.005], F("dark"), verts=8, caps=False)
        o.data.transform(Matrix.Translation(-Vector((0, 0, 0))))
        parts.append(o)
    export_one(parts, "glow_plant")


def spore_pod():
    prof = [(0.12, 0.72), (0.2, 0.78), (0.26, 0.7), (0.32, 0.45), (0.3, 0.2), (0.18, 0.04), (0.0, 0.0)]
    rnd = random.Random(3)
    pod = lathe_r(prof, F("flesh"), segs=16, radial=lambda k, z: 1.0 + 0.12 * math.sin(k * 1.9) * (z / 0.8),
                  name="pod")
    inner = lathe_r([(0.12, 0.72), (0.1, 0.6), (0.0, 0.55)], F("dark"), segs=16, name="inner")
    K.select(inner)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [pod, inner]
    for k in range(5):  # petals peeling open
        a = k * math.tau / 5
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(tube([d * 0.18 + Vector((0, 0, 0.72)), d * 0.28 + Vector((0, 0, 0.86)),
                           d * 0.4 + Vector((0, 0, 0.88))], [0.05, 0.04, 0.01], F("flesh"), verts=6, caps=True))
    for k in range(9):  # spores crowding the mouth
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.0, 0.09)
        parts.append(ico(rnd.uniform(0.03, 0.05), (math.cos(a) * r, math.sin(a) * r, 0.66 + rnd.uniform(0, 0.08)),
                         F("glow"), sub=1))
    for k in range(6):  # ribs
        a = k * math.tau / 6
        pts = [Vector((math.cos(a) * rr * 1.04, math.sin(a) * rr * 1.04, z)) for rr, z in prof[1:6]]
        parts.append(tube(pts, [0.015] * len(pts), F("dark"), verts=5, caps=False))
    export_one(parts, "spore_pod")


def vent():
    prof = [(0.16, 1.2), (0.22, 1.18), (0.2, 1.0), (0.17, 0.75), (0.22, 0.4), (0.4, 0.1), (0.5, 0.0)]
    o = lathe_r(prof, F("shell"), segs=12, radial=lambda k, z: 1.0 + 0.1 * math.sin(k * 2.3 + z * 6), name="vent")
    inner = lathe_r([(0.16, 1.2), (0.13, 1.0), (0.0, 0.95)], F("glow"), segs=12, name="throat")
    K.select(inner)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o, inner]
    for z in (0.35, 0.62, 0.88):  # crusted bands with glowing cracks
        parts.append(torus(0.2 - 0.02 * z, 0.035, (0, 0, z), F("dark"), verts=12, minor=5))
    for k in range(7):
        a = k * 0.9
        z = 0.15 + 0.13 * k
        r = 0.19 if z > 0.4 else 0.3
        parts.append(rod((math.cos(a) * r, math.sin(a) * r, z), (math.cos(a + 0.3) * r, math.sin(a + 0.3) * r, z + 0.12),
                         0.012, F("glow"), verts=4))
    export_one(parts, "vent")


def anemone():
    parts = [lathe_r([(0.0, 0.22), (0.18, 0.22), (0.2, 0.15), (0.17, 0.06), (0.25, 0.0), (0.0, 0.0)], F("flesh"),
                     segs=16, name="foot")]
    parts.append(cyl(0.12, 0.02, (0, 0, 0.225), F("dark"), verts=14))
    for k in range(14):
        a = k * math.tau / 14
        ring = 0.15 if k % 2 == 0 else 0.11
        d = Vector((math.cos(a), math.sin(a), 0))
        h = 0.45 if k % 2 == 0 else 0.38
        pts = [d * ring + Vector((0, 0, 0.2)), d * (ring + 0.06) + Vector((0, 0, 0.32)),
               d * (ring + 0.14) + Vector((0, 0, h)), d * (ring + 0.26) + Vector((0, 0, h + 0.06))]
        parts.append(tube(pts, [0.035, 0.03, 0.022, 0.012], F("flesh"), verts=6, caps=False))
        parts.append(ico(0.022, pts[-1], F("glow"), sub=1))
    export_one(parts, "anemone")


def fan_coral():
    rnd = random.Random(12)
    parts = []

    def branch(p, d, length, r, depth):
        end = p + d * length
        mid = p.lerp(end, 0.5) + Vector((0, rnd.uniform(-0.03, 0.03), 0))
        parts.append(tube([p, mid, end], [r, r * 0.85, r * 0.7], F("shell"), verts=5, caps=False))
        if depth == 0:
            parts.append(ico(r * 1.6, end, F("glow"), sub=1))
            return
        for s in (-1, 1):
            a = math.atan2(d.x, d.z) + s * rnd.uniform(0.3, 0.55)
            nd = Vector((math.sin(a), 0, math.cos(a)))
            branch(end, nd, length * rnd.uniform(0.62, 0.78), r * 0.72, depth - 1)

    branch(Vector((0, 0, 0)), Vector((0, 0, 1)), 0.42, 0.05, 4)
    parts.append(lumpy(0.14, (0, 0, 0.0), F("flesh"), 13, amount=0.2, scale=(1.3, 1.0, 0.5), sub=1, smooth=50))
    export_one(parts, "fan_coral")


def spine():
    pts = curve_pts((0, 0, 0), (0.35, 0, 1.3), (0.12, 0, 0.1), n=9)
    parts = [tube(pts, taper(9, 0.16, 0.004, 0.9), F("shell"), verts=8, caps=True)]
    for i in (1, 3, 5):  # growth rings
        parts.append(torus(taper(9, 0.16, 0.004, 0.9)[i] * 1.02, 0.012, pts[i], F("dark"), verts=10, minor=4,
                           rot=(0, math.atan2(pts[i + 1].x - pts[i].x, pts[i + 1].z - pts[i].z), 0)))
    parts.append(torus(0.18, 0.03, (0, 0, 0.04), F("glow"), verts=14, minor=5))
    parts.append(lumpy(0.24, (0, 0, -0.02), F("flesh"), 17, amount=0.2, scale=(1.2, 1.2, 0.35), sub=1, smooth=50))
    export_one(parts, "spine")


def pustule():
    parts = [sphere(0.3, (0, 0, 0), F("flesh"), scale=(1, 1, 0.75), segs=16, rings=10)]
    parts.append(sphere(0.12, (0, 0, 0.18), F("glow"), scale=(1, 1, 0.8), segs=12, rings=8))
    for k in range(7):  # veins running from the heart
        a = k * math.tau / 7
        pts = [Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.2)), Vector((math.cos(a + 0.2) * 0.2, math.sin(a + 0.2) * 0.2, 0.17)),
               Vector((math.cos(a + 0.1) * 0.29, math.sin(a + 0.1) * 0.29, 0.08)),
               Vector((math.cos(a + 0.3) * 0.35, math.sin(a + 0.3) * 0.35, -0.02))]
        parts.append(tube(pts, [0.022, 0.018, 0.014, 0.008], F("glow"), verts=5, caps=False))
    for k in range(4):  # little blisters
        a = k * 1.6 + 0.5
        parts.append(sphere(0.07, (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.02), F("flesh"), scale=(1, 1, 0.7), segs=10,
                            rings=6))
    export_one(parts, "pustule")


JOBS = {"polyp": polyp, "tube_coral": tube_coral, "egg_cluster": egg_cluster, "crystal": crystal, "tendril": tendril,
        "rib": rib, "pipe": pipe, "glow_plant": glow_plant, "spore_pod": spore_pod, "vent": vent, "anemone": anemone,
        "fan_coral": fan_coral, "spine": spine, "pustule": pustule}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    for name, fn in JOBS.items():
        if len(args) > 1 and name not in args[1:]:
            continue
        reset()
        roles()
        fn()
