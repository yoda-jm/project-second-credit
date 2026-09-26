"""Nightbite (game 12) props: the neon maze pieces, the floor tile, pellets, the power orb (with a child "halo"),
four bonus fruits and the gate of the spook den. The characters are in nightbite_characters.py.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/nightbite_models.py -- godot/games/nightbite/art/models [name ...]
One maze cell = 1 unit, the front faces -Y, the origin sits at the cell centre on the ground (z = 0 is the top of the
floor tile). Helpers (mat, box, sphere, tube, join, export, ...) come from blastyard_models.py.

Maze pieces (one node each, named like the file): a dark glossy base (material "wall_base") outlined by two neon
tubes (material "wall_neon", emissive: the game recolours it per stage). Every piece meets the cell edge the same
way (base half-width 0.23, tubes at +-0.18 from the centre line), so neighbours join seamlessly:
  wall_straight  connects -X and +X            wall_corner  connects +X and +Y (rounded)
  wall_t         connects -X, +X and +Y        wall_cross   connects all four sides
  wall_end       connects +X (rounded dead end) wall_single  connects nothing (a round post)
Directions are Blender axes; in Godot +X stays +X and Blender +Y becomes -Z. Rotate about the up axis for the other
orientations. Height: base 0.3, the tubes reach 0.34.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90

HW = 0.23     # half-width of a wall base
D = 0.18      # neon tube offset from the centre line
H = 0.3       # base height
TR = 0.035    # neon tube radius
CH = 0.035    # chamfer of the base's top edge
ARC = 5       # segments per quarter arc


def wall_mats():
    return (mat("wall_base", (0.045, 0.06, 0.13), 0.2, 0.3, coat=1.0),
            mat("wall_neon", (0.15, 0.5, 1.0), 0.3, emit=3.5))


def arc(c, r, a0, a1, n=ARC):
    """Points on a circle around c from angle a0 to a1 (degrees), n segments."""
    return [Vector((c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                    c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)), 0)) for k in range(n + 1)]


def slab(poly, h, material, chamfer=CH, name="slab"):
    """A 2D outline (XY points) extruded up to height h, the top edge chamfered at 45 degrees, no bottom face."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    pts = []
    for p in poly:  # drop duplicates where arcs meet
        p = Vector((p[0], p[1], 0))
        if not pts or (p - pts[-1]).length > 1e-4:
            pts.append(p)
    if (pts[0] - pts[-1]).length < 1e-4:
        pts.pop()
    bot = [bm.verts.new((p.x, p.y, 0.0)) for p in pts]
    top = [bm.verts.new((p.x, p.y, h - chamfer)) for p in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    cap = bm.faces.new(top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if cap.normal.z < 0:
        cap.normal_flip()
    if chamfer:
        bmesh.ops.inset_region(bm, faces=[cap], thickness=chamfer, depth=chamfer, use_even_offset=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=30)


def neon(points, m, closed=False):
    pts = [Vector((p[0], p[1], H)) for p in points]
    return tube(pts, [TR] * len(pts), m, verts=6, caps=False)


def fillet(cx, cy, a0, a1, r):
    return arc((cx, cy), r, a0, a1)


def wall_straight():
    base, glow = wall_mats()
    parts = [slab([(-0.5, -HW), (0.5, -HW), (0.5, HW), (-0.5, HW)], H, base),
             neon([(-0.5, -D), (0.5, -D)], glow), neon([(-0.5, D), (0.5, D)], glow)]
    simple(parts, "wall_straight")


def wall_corner():
    base, glow = wall_mats()
    c = (0.5, 0.5)
    poly = arc(c, 0.5 + HW, -90, -180) + arc(c, 0.5 - HW, -180, -90)
    parts = [slab(poly, H, base), neon(arc(c, 0.5 - D, -90, -180), glow), neon(arc(c, 0.5 + D, -90, -180), glow)]
    simple(parts, "wall_corner")


def wall_t():
    base, glow = wall_mats()
    r = 0.5 - HW
    poly = ([(-0.5, -HW), (0.5, -HW)] + fillet(0.5, 0.5, -90, -180, r) + fillet(-0.5, 0.5, 0, -90, r))
    parts = [slab(poly, H, base), neon([(-0.5, -D), (0.5, -D)], glow),
             neon(fillet(0.5, 0.5, -90, -180, 0.5 - D), glow), neon(fillet(-0.5, 0.5, 0, -90, 0.5 - D), glow)]
    simple(parts, "wall_t")


def wall_cross():
    base, glow = wall_mats()
    r = 0.5 - HW
    poly = (fillet(0.5, -0.5, 180, 90, r) + fillet(0.5, 0.5, -90, -180, r) + fillet(-0.5, 0.5, 0, -90, r)
            + fillet(-0.5, -0.5, 90, 0, r))
    parts = [slab(poly, H, base)]
    for cx, cy, a0, a1 in ((0.5, -0.5, 180, 90), (0.5, 0.5, -90, -180), (-0.5, 0.5, 0, -90), (-0.5, -0.5, 90, 0)):
        parts.append(neon(fillet(cx, cy, a0, a1, 0.5 - D), glow))
    simple(parts, "wall_cross")


def wall_end():
    base, glow = wall_mats()
    poly = [(0.5, -HW), (0.5, HW)] + arc((0, 0), HW, 90, 270, 8)
    u = [(0.5, D)] + arc((0, 0), D, 90, 270, 8) + [(0.5, -D)]
    parts = [slab(poly, H, base), neon(u, glow)]
    simple(parts, "wall_end")


def wall_single():
    base, glow = wall_mats()
    poly = arc((0, 0), HW + 0.02, 0, 360, 16)[:-1]
    parts = [slab(poly, H, base), torus(D, TR, (0, 0, H), glow, verts=16, minor=6)]
    simple(parts, "wall_single")


# ------------------------------------------------------------------ floor, pellets, power, gate

def floor_tile():
    """A dark glossy tile, its top at z = 0, with faint glowing lines along its four edges (neighbours form a grid)."""
    floor = mat("floor", (0.018, 0.02, 0.04), 0.22, 0.1, coat=0.8)
    line = mat("floor_grid", (0.08, 0.12, 0.3), 0.4, emit=0.6)
    top = box((1.0, 1.0, 0.06), (0, 0, -0.03), floor, bevel=0.0)
    bm = bmesh.new()
    bm.from_mesh(top.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.5], context="FACES")
    bm.to_mesh(top.data)
    bm.free()
    w = 0.012
    parts = [top]
    for s in (-1, 1):
        parts.append(box((1.0, w, 0.004), (0, s * (0.5 - w / 2), 0.0), line, bevel=0.0))
        parts.append(box((w, 1.0 - 2 * w, 0.004), (s * (0.5 - w / 2), 0, 0.0), line, bevel=0.0))
    for o in parts[1:]:  # only the top faces of the lines matter
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < 0.5], context="FACES")
        bm.to_mesh(o.data)
        bm.free()
    simple(parts, "floor_tile")


PELLET_Z = 0.2


def pellet():
    simple([ico(0.07, (0, 0, PELLET_Z), mat("pellet", (1.0, 0.86, 0.72), 0.3, emit=5.0), sub=2)], "pellet")


def power():
    """The power orb (root "power", centre 0.25 above the ground) and its child "halo", a ring pivoting on the orb's
    centre: the game pulses the orb and spins or scales the halo."""
    core = mat("power_glow", (1.0, 0.92, 0.8), 0.2, emit=8.0)
    shell = mat("power_shell", (1.0, 0.55, 0.85), 0.1, coat=1.0, emit=2.0)
    ring = mat("power_halo", (1.0, 0.5, 0.85), 0.3, emit=5.0)
    c = Vector((0, 0, 0.25))
    parts = [ico(0.2, c, shell, sub=2), ico(0.12, c + Vector((-0.07, -0.07, 0.1)), core, sub=1)]
    root = join(parts, "power")
    halo = join([torus(0.29, 0.018, c, ring, rot=(0.35, 0.2, 0), verts=24, minor=4)], "halo", pivot=c)
    export(root, "power", [(halo, root)])


def gate():
    """The door of the spook den: a thin glowing bar across the cell along X, on two small posts at the cell edges."""
    bar = mat("gate", (1.0, 0.45, 0.8), 0.3, emit=5.0)
    post = mat("wall_base", (0.045, 0.06, 0.13), 0.2, 0.3, coat=1.0)
    z = 0.18
    parts = [rod((-0.5, 0, z), (0.5, 0, z), 0.035, bar, verts=6),
             box((1.0, 0.03, 0.02), (0, 0, z - 0.07), bar, bevel=0.0)]
    for s in (-1, 1):
        parts.append(cyl(0.06, 0.26, (s * 0.46, 0, 0.13), post, verts=8, bevel=0.015))
        parts.append(cyl(0.045, 0.02, (s * 0.46, 0, 0.265), bar, verts=8))
    simple(parts, "gate")


# ------------------------------------------------------------------ fruits (bonus items, about 0.5 across)

FZ = 0.3  # the fruits float: their centre sits 0.3 above the ground


def lathe(profile, material, segs=12, name="lathe"):
    """A surface of revolution about Z from (r, z) pairs, top to bottom; the ends close on the axis."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-4:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z))
                          for k in range(segs)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segs):
            q = [r0[k % len(r0)], r1[k % len(r1)], r1[(k + 1) % len(r1)], r0[(k + 1) % len(r0)]]
            q = [v for i, v in enumerate(q) if v not in q[:i]]
            if len(q) >= 3:
                bm.faces.new(q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=60)


def leaf(base, direction, length, width, material, lift=0.3):
    """A flat pointed leaf from base along direction (XY), tilted up by lift radians."""
    shape = [(0.0, 0.0), (0.35, 0.5), (1.0, 0.0), (0.35, -0.5)]
    o = prism([(x * length, y * width) for x, y in shape], 0.012, (0, 0, 0), material, rot=(R90, 0, 0), bevel=0.0)
    o.rotation_euler = (0, -lift, math.atan2(direction[1], direction[0]))
    o.location = base
    K.select(o)
    bpy.ops.object.transform_apply(location=True, rotation=True)
    return o


def fruit_0():
    """Crystal berry: a cluster of faceted magenta drupelets under a crown of green crystal leaves."""
    berry = mat("fruit_berry", (0.95, 0.2, 0.55), 0.1, coat=1.0, emit=1.6)
    shine = mat("fruit_berry_shine", (1.0, 0.75, 0.9), 0.1, emit=4.0)
    green = mat("fruit_leaf", (0.3, 1.0, 0.45), 0.3, emit=1.5)
    parts = []
    c = Vector((0, 0, FZ - 0.02))
    for k, (a, e, r) in enumerate([(0, 90, 0.0), (0, 30, 0.11), (72, 30, 0.11), (144, 30, 0.11), (216, 30, 0.11),
                                   (288, 30, 0.11), (36, -20, 0.1), (108, -20, 0.1), (180, -20, 0.1), (252, -20, 0.1),
                                   (324, -20, 0.1), (0, -90, 0.12)]):
        d = Vector((math.cos(math.radians(a)) * math.cos(math.radians(e)),
                    math.sin(math.radians(a)) * math.cos(math.radians(e)), math.sin(math.radians(e))))
        p = c + d * r * 1.05 + Vector((0, 0, 0.1 if e == 90 else 0))
        parts.append(ico(0.072, p, berry, sub=1, smooth=0))
    parts.append(ico(0.03, c + Vector((-0.07, -0.1, 0.1)), shine, sub=1))
    top = c + Vector((0, 0, 0.17))
    for k in range(5):
        a = math.radians(k * 72 + 18)
        parts.append(leaf(top, (math.cos(a), math.sin(a)), 0.14, 0.07, green, lift=-0.35))
    parts.append(rod(top, top + Vector((0.02, 0.0, 0.08)), 0.014, green, verts=5))
    simple(parts, "fruit_0")


def star_points(r1, r2, n=5, rot=R90):
    return [(math.cos(rot + k * math.pi / n) * (r1 if k % 2 == 0 else r2),
             math.sin(rot + k * math.pi / n) * (r1 if k % 2 == 0 else r2)) for k in range(2 * n)]


def fruit_1():
    """Star plum: a violet plum with a golden star glowing on its crown."""
    plum = mat("fruit_plum", (0.42, 0.14, 0.9), 0.15, coat=1.0, emit=0.9)
    gold = mat("fruit_gold", (1.0, 0.8, 0.25), 0.25, emit=4.0)
    green = mat("fruit_leaf", (0.3, 1.0, 0.45), 0.3, emit=1.5)
    shine = mat("fruit_plum_shine", (0.85, 0.75, 1.0), 0.1, emit=3.0)
    c = Vector((0, 0, FZ - 0.02))
    body = sphere(0.2, c, plum, scale=(1.0, 0.95, 0.92), segs=16, rings=10)
    for v in body.data.vertices:  # a dimple on top
        if v.co.z > c.z + 0.16:
            v.co.z -= 0.03
    star = prism(star_points(0.13, 0.055), 0.04, (0, 0, 0), gold, rot=(R90, 0, 0), bevel=0.01, segs=1)
    star.location = c + Vector((0, 0, 0.175))
    star.rotation_euler = (-0.25, 0, 0)
    parts = [body, star, sphere(0.04, c + Vector((-0.09, -0.12, 0.08)), shine, scale=(1, 0.5, 0.8), segs=8, rings=5),
             rod(c + Vector((0, 0.02, 0.18)), c + Vector((0.03, 0.05, 0.28)), 0.015, green, verts=5),
             leaf(c + Vector((0.03, 0.05, 0.26)), (1, 0.4), 0.13, 0.07, green, lift=0.3)]
    simple(parts, "fruit_1")


def fruit_2():
    """Moon pear: a pale silver-blue pear with a crescent moon for a leaf."""
    pear = mat("fruit_pear", (0.62, 0.82, 1.0), 0.15, coat=1.0, emit=1.1)
    moon = mat("fruit_moon", (1.0, 0.95, 0.7), 0.25, emit=4.0)
    stem = mat("fruit_stem", (0.35, 0.25, 0.2), 0.6)
    b = FZ - 0.21
    prof = [(0.0, b + 0.46), (0.035, b + 0.455), (0.065, b + 0.42), (0.085, b + 0.37), (0.1, b + 0.31),
            (0.135, b + 0.24), (0.175, b + 0.17), (0.19, b + 0.1), (0.17, b + 0.04), (0.11, b + 0.005), (0.0, b)]
    parts = [lathe(prof, pear, segs=14)]
    top = Vector((0, 0, b + 0.455))
    parts.append(rod(top - Vector((0, 0, 0.02)), top + Vector((0.03, 0.01, 0.07)), 0.014, stem, verts=5))
    cres = arc((0, 0), 0.1, 40, 320, 10) + arc((0.05, 0), 0.075, 320, 40, 8)[1:-1]
    m = prism([(p.x, p.y) for p in cres], 0.025, (0, 0, 0), moon, rot=(R90, 0, 0), bevel=0.006, segs=1)
    m.rotation_euler = (-0.3, 0.0, 0.5)
    m.location = top + Vector((0.1, -0.02, 0.02))
    parts.append(m)
    simple(parts, "fruit_2")


def fruit_3():
    """Sun gem: a faceted orange-red gem ringed by eight golden rays."""
    gem = mat("fruit_sun", (1.0, 0.38, 0.08), 0.1, coat=1.0, emit=2.0)
    gold = mat("fruit_gold", (1.0, 0.8, 0.25), 0.25, emit=4.0)
    table = mat("fruit_sun_table", (1.0, 0.85, 0.5), 0.1, emit=5.0)
    c = Vector((0, 0, FZ - 0.03))
    crown = cyl(0.19, 0.08, c + Vector((0, 0, 0.04)), gem, r2=0.11, verts=8)
    pav = cyl(0.19, 0.17, c + Vector((0, 0, -0.085)), gem, r2=0.0, verts=8, rot=(math.pi, 0, 0))
    tab = cyl(0.105, 0.01, c + Vector((0, 0, 0.084)), table, verts=8)
    for o in (crown, pav, tab):
        K.select(o)
        bpy.ops.object.shade_flat()
    parts = [crown, pav, tab]
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        ln = 0.07 if k % 2 else 0.05
        parts.append(rod(c + d * 0.2, c + d * (0.2 + ln), 0.026, gold, r2=0.0, verts=4))
    simple(parts, "fruit_3")


# ------------------------------------------------------------------ main

JOBS = {"wall_straight": wall_straight, "wall_corner": wall_corner, "wall_t": wall_t, "wall_cross": wall_cross,
        "wall_end": wall_end, "wall_single": wall_single, "floor_tile": floor_tile, "pellet": pellet,
        "power": power, "gate": gate, "fruit_0": fruit_0, "fruit_1": fruit_1, "fruit_2": fruit_2, "fruit_3": fruit_3}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
