"""Inkstorm (game 14) models: the player's marker (a brass-and-glass quill nib), the two sparks, the diorama props that
rise on claimed land, the carved map frame around the board and an inkwell with a feather beside it.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/inkstorm_models.py -- godot/games/inkstorm/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, ico, rod, prism, join, ...), prism_models.py (animate,
export_anim, empty, new_obj, loft_x) and nightbite_models.py (lathe). Animations are 24 fps, set the loop in the game.

Axes: Blender Z up, the camera side is -Y. In Godot: +X stays +X, Blender +Z becomes +Y (up), Blender -Y becomes +Z
(towards the camera). Every origin sits on the ground (y = 0 in Godot) unless noted; the board's top face is y = 0.

marker       root "marker" (an empty at the nib's tip, the point that touches the board) with the child "nib" (the
             whole quill, pivot on the tip). About 0.5 tall and 0.2 wide; the quill leans back 22 degrees, away from
             the camera (towards Godot -Z), like a pen in a writing hand, so the nib's face looks at the viewer.
             Animation "hover" (2 s, on "nib"): bobs up to +0.035 and sways +-20 degrees about the vertical axis
             through the tip, so the tip lifts slightly off the board. Materials "marker_brass", "marker_brass_dark",
             "marker_glass" (alpha-blended bulb), "marker_glow" (the gem core in the bulb, the slit, the breather hole
             and the top gem: emissive cyan, recolour it for player 2).
spark        one node "spark", 0.36 across, origin at its CENTRE (lift it 0.18 to sit on the line). Animation
             "spin" (1 s): one turn about the vertical axis with a tumble. "spark_ember" (orange spikes), "spark_glow"
             (hot white-yellow core and spike tips).
spark_super  one node "spark_super", 0.52 across, origin at its centre (lift it 0.26), "spin" (1 s). Red-violet:
             "spark_super_ember", "spark_super_ring", "spark_glow_super" (contains "spark_glow").
Props (one node each, named like the file, origin at the centre of the base, flat-shaded painted colours, each under
400 triangles, materials prefixed with the prop name):
  tree_round 0.5 tall   tree_pine 0.56 tall   house 0.37 tall (front door faces -Y / Godot +Z)   rock 0.17 tall
  bush 0.22 tall   tower 0.66 tall (flag included)
  boat 0.42 tall, origin at the WATERLINE (the hull dips 0.045 below it), bow towards +X
  windmill 0.53 tall, 0.68 with a sail up: root "windmill" with the child "sail" (pivot on the hub, 0.44 up, on the
             -Y face / Godot +Z); animation "turn" (4 s, one full turn of "sail"). Rotate the whole windmill freely
             about the vertical axis.
  Windows ("house_window", "tower_window", "windmill_window") are slightly emissive, for dusk.
frame        one node "frame" for the whole 12.8 x 9.6 board: place it unrotated at the board's centre (0, 0, 0).
             Its inner edge is exactly the board's edge (x = +-6.4, Godot z = +-4.8) and it is 0.6 wide on every side
             (outer size 14.0 x 10.8; 14.07 x 10.87 with the dentils on its outer face). It reaches from y = -0.35
             (hiding the board's side) to y = 0.26 (0.41 on the corner bosses); the inner lip is
             only 0.04 high and the moulding climbs gently, so a camera 55 degrees down loses less than 0.05 of the
             near edge. Materials "frame_wood" (walnut), "frame_wood_light" (carved bands), "frame_gilt" (beads,
             corner bosses, compass medallions at the middle of each side), "frame_inlay" (dark grooves).
inkwell      one node "inkwell", origin at the centre of its base, 1.2 tall (the feather leans towards +X and away
             from the camera, its tip at Godot x = 0.42, z = -0.22). About 0.66 across the base. Place it beside the
             frame, e.g. at Godot (7.7, -0.35, -3.5) when the frame sits on a table at the frame's bottom.
             "inkwell_glass" (dark blue faceted body), "inkwell_brass", "inkwell_ink", "inkwell_feather",
             "inkwell_feather_tip", "inkwell_quill".
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, prism, join, export, simple, reset, R90
from prism_models import animate, export_anim, empty, new_obj, loft_x
from nightbite_models import lathe

FPS = 24
BX, BY = 6.4, 4.8      # board half sizes (Blender X, Y)


def flat(*objs):
    for o in objs:
        K.select(o)
        bpy.ops.object.shade_flat()
    return objs[0] if len(objs) == 1 else objs


def lumpy(r, loc, material, seed, amount=0.18, scale=(1, 1, 1), sub=1):
    """A flat-shaded icosphere with its vertices pushed in and out: a painted canopy, bush or rock."""
    o = ico(r, loc, material, scale=scale, sub=sub, smooth=0)
    rnd = random.Random(seed)
    c = Vector(loc)
    for v in o.data.vertices:
        d = v.co - c
        v.co = c + d * (1 + rnd.uniform(-amount, amount))
    o.data.update()
    return o


def ring_star(n, r1, r2):
    return [(math.cos(k * math.pi / n) * (r1 if k % 2 == 0 else r2),
             math.sin(k * math.pi / n) * (r1 if k % 2 == 0 else r2)) for k in range(2 * n)]


def flat_disc(poly, z0, z1, material, name="disc"):
    """A 2D outline in XY extruded from z0 to z1 (top and bottom faces)."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in poly]
    hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return new_obj(name, bm, material, smooth=0)


# ------------------------------------------------------------------ marker

NIB_H, NIB_W, NIB_A = 0.29, 0.1, math.radians(72)
LEAN = math.radians(22)


def nib_half_width(z):
    """Half width of the nib outline at height z: a point at the tip, round shoulders, a waist into the collar."""
    u = z / NIB_H
    if u < 0.7:
        return max(0.003, NIB_W * math.sin(u / 0.7 * R90) ** 0.8)
    return NIB_W * (1 - 0.3 * ((u - 0.7) / 0.3) ** 1.6)


def nib_point(x_frac, z, lift=0.0):
    """A point on the nib's front face: x_frac in -1..1 across the width, lifted `lift` off the surface."""
    hw = nib_half_width(z)
    R = hw / math.sin(NIB_A)
    th = x_frac * NIB_A
    return Vector((R * math.sin(th), -(R * math.cos(th) - R * math.cos(NIB_A)) - 0.004 - lift, z))


def nib_blade(material, t=0.014):
    """The pointed, curved blade of a pen nib: tip at the origin, bulging towards -Y, open at the top."""
    bm = bmesh.new()
    rows = []
    n = 11
    for s in range(15):
        z = NIB_H * s / 14
        row = [nib_point(-1 + 2 * k / (n - 1), z) for k in range(n)]
        outer = [bm.verts.new(p) for p in row]
        inner = [bm.verts.new((p.x * 0.88, p.y + t, p.z)) for p in reversed(row)]
        rows.append(outer + inner)
    m = len(rows[0])
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(m):
            bm.faces.new((r0[k], r0[(k + 1) % m], r1[(k + 1) % m], r1[k]))
    bm.faces.new(rows[0])
    bm.faces.new(rows[-1][::-1])
    return new_obj("blade", bm, material, smooth=45)


def marker():
    brass = mat("marker_brass", (0.95, 0.66, 0.26), 0.32, 0.65, coat=0.5)
    dark = mat("marker_brass_dark", (0.3, 0.16, 0.06), 0.4, 0.6)
    glass = mat("marker_glass", (0.75, 0.92, 1.0), 0.03, 0.0, coat=1.0, alpha=0.3, emit=0.3,
                emit_color=(0.3, 0.9, 1.0))
    glow = mat("marker_glow", (0.3, 0.95, 1.0), 0.2, emit=7.0)
    parts = [nib_blade(brass)]
    # the glowing slit from the tip up to the breather hole, the hole a glowing teardrop gem in a dark ring
    parts.append(K.tube([nib_point(0, z, 0.001) for z in (0.012, 0.06, 0.1, 0.14)], [0.0035, 0.005, 0.006, 0.006],
                        glow, verts=5))
    hole = nib_point(0, 0.162, 0.0)
    parts.append(ico(0.026, hole + Vector((0, -0.004, 0)), glow, scale=(1, 0.5, 1.25), sub=2, smooth=0))
    parts.append(torus(0.03, 0.006, hole + Vector((0, 0.0, 0)), dark, rot=(R90, 0, 0), verts=12, minor=4,
                       scale=(1, 1, 1.25)))
    # engraved scrolls on the shoulders and a band where the nib meets the collar
    for sgn in (1, -1):
        pts = [nib_point(sgn * f, z, 0.002) for f, z in ((0.3, 0.17), (0.55, 0.19), (0.7, 0.215), (0.62, 0.24),
                                                         (0.45, 0.235), (0.42, 0.215))]
        parts.append(K.tube(pts, [0.004] * len(pts), dark, verts=4))
    parts.append(K.tube([nib_point(-0.95 + 1.9 * k / 10, 0.262, 0.002) for k in range(11)], [0.005] * 11, dark,
                        verts=4))
    # collar, glass bulb with the gem core inside, a cage of ribs, top collar
    parts += [cyl(0.08, 0.03, (0, 0, 0.3), dark, r2=0.075, verts=16, bevel=0.006, segs=1),
              torus(0.078, 0.008, (0, 0, 0.29), brass, verts=16, minor=4),
              cyl(0.075, 0.02, (0, 0, 0.322), brass, r2=0.06, verts=16, bevel=0.005, segs=1)]
    gem = ico(0.04, (0, 0, 0.37), glow, scale=(1, 1, 1.35), sub=1, smooth=0)
    parts.append(gem)
    parts.append(sphere(0.06, (0, 0, 0.37), glass, scale=(1, 1, 1.1), segs=16, rings=10))
    for k in range(6):
        a = k * math.pi / 3
        pts = [(math.cos(a) * r, math.sin(a) * r, z) for r, z in ((0.055, 0.327), (0.064, 0.35), (0.066, 0.37),
                                                                    (0.063, 0.39), (0.05, 0.413))]
        parts.append(K.tube(pts, [0.005] * 5, brass, verts=5, caps=False))
    parts += [cyl(0.06, 0.018, (0, 0, 0.415), brass, r2=0.045, verts=16, bevel=0.004, segs=1),
              cyl(0.035, 0.02, (0, 0, 0.43), dark, r2=0.028, verts=12)]
    # finial: three brass feather vanes fanning up, a small gem on top
    for k in range(3):
        a = k * 2 * math.pi / 3 + R90
        vane = prism([(0.0, 0.0), (0.028, 0.012), (0.042, 0.045), (0.03, 0.068), (0.008, 0.05)], 0.01, (0, 0, 0),
                     brass, bevel=0.003, segs=1)
        vane.location = (0, 0, 0.43)
        vane.rotation_euler = (0, 0, a - R90 + math.pi)
        K.select(vane)
        bpy.ops.object.transform_apply(location=True, rotation=True)
        parts.append(vane)
    parts.append(rod((0, 0, 0.43), (0, 0, 0.48), 0.01, dark, r2=0.005, verts=6))
    parts.append(ico(0.022, (0, 0, 0.49), glow, sub=1, smooth=0))
    nib = join(parts, "nib")
    # lean the quill back, away from the camera, like a pen in a writing hand: the nib's face turns to the viewer
    nib.data.transform(Matrix.Rotation(-LEAN, 4, "X"))
    root = empty("marker")
    keys = {}
    for i in range(9):
        a = 2 * math.pi * i / 8
        keys[i * 6] = {"loc": (0, 0, 0.0175 * (1 - math.cos(a))), "rot": (0, 0, 0.35 * math.sin(a))}
    animate(nib, "hover", keys, linear=False)
    export_anim(root, "marker", [(nib, root)])


# ------------------------------------------------------------------ sparks

def dirs(kind):
    """Unit directions of the icosahedron's vertices (12) or faces (20)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    if kind == "v":
        out = [v.co.normalized() for v in bm.verts]
    else:
        bm.faces.ensure_lookup_table()
        out = [f.calc_center_median().normalized() for f in bm.faces]
    bm.free()
    return out


def spiky(core_r, long_r, short_r, ember, glow, base_r, rot=(0.3, 0.2, 0.0)):
    m = Matrix.Rotation(rot[0], 3, "X") @ Matrix.Rotation(rot[1], 3, "Y")
    parts = [ico(core_r, (0, 0, 0), glow, sub=2, smooth=0)]
    for d in dirs("v"):
        d = m @ d
        parts.append(rod(d * core_r * 0.6, d * long_r * 0.8, base_r, ember, r2=base_r * 0.35, verts=5))
        parts.append(rod(d * long_r * 0.8, d * long_r, base_r * 0.35, glow, r2=0.0, verts=5))
    for d in dirs("f"):
        d = m @ d
        parts.append(rod(d * core_r * 0.7, d * short_r, base_r * 0.7, ember, r2=0.0, verts=4))
    flat(*parts)
    return parts


def fit_radius(o, r):
    """Scales the mesh about its origin so its farthest vertex sits r away."""
    far = max(v.co.length for v in o.data.vertices)
    o.data.transform(Matrix.Scale(r / far, 4))
    o.data.update()
    return o


def spin_keys(tilt=0.35):
    keys = {}
    for i in range(5):
        a = 2 * math.pi * i / 4
        keys[i * 6] = {"rot": (tilt * math.sin(a), tilt * math.cos(a), a)}
    return keys


def spark():
    ember = mat("spark_ember", (0.7, 0.14, 0.02), 0.4, emit=0.7, emit_color=(1.0, 0.28, 0.02))
    glow = mat("spark_glow", (1.0, 0.85, 0.4), 0.2, emit=8.0)
    root = fit_radius(join(spiky(0.07, 0.18, 0.11, ember, glow, 0.032), "spark"), 0.18)
    animate(root, "spin", spin_keys())
    export_anim(root, "spark")


def spark_super():
    ember = mat("spark_super_ember", (0.55, 0.02, 0.22), 0.4, emit=0.7, emit_color=(0.95, 0.05, 0.35))
    ring_m = mat("spark_super_ring", (0.35, 0.06, 0.9), 0.3, emit=2.0)
    glow = mat("spark_glow_super", (1.0, 0.55, 0.9), 0.2, emit=9.0)
    parts = spiky(0.1, 0.26, 0.17, ember, glow, 0.045, rot=(0.5, 0.1, 0))
    # a jagged crown ring around the waist with its own small thorns
    parts.append(torus(0.19, 0.016, (0, 0, 0), ring_m, verts=18, minor=4))
    for k in range(9):
        a = k * 2 * math.pi / 9
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(rod(d * 0.19, d * 0.25 + Vector((0, 0, 0.03)), 0.02, ring_m, r2=0.0, verts=4))
    flat(*parts[-10:])
    root = fit_radius(join(parts, "spark_super"), 0.26)
    animate(root, "spin", spin_keys(0.45))
    export_anim(root, "spark_super")


# ------------------------------------------------------------------ props

def tree_round():
    trunk = mat("tree_round_trunk", (0.42, 0.26, 0.14), 0.9)
    leaf = mat("tree_round_leaves", (0.36, 0.62, 0.24), 0.85)
    light = mat("tree_round_leaves_light", (0.56, 0.78, 0.3), 0.85)
    parts = [rod((0, 0, 0), (0.01, 0, 0.24), 0.035, trunk, r2=0.022, verts=6),
             rod((0.005, 0, 0.16), (0.07, 0.02, 0.24), 0.014, trunk, verts=4),
             lumpy(0.16, (0, 0, 0.32), leaf, 1, scale=(1, 1, 0.9)),
             lumpy(0.1, (0.1, -0.05, 0.27), leaf, 2),
             lumpy(0.1, (-0.1, 0.03, 0.29), leaf, 3),
             lumpy(0.09, (-0.02, -0.06, 0.41), light, 4)]
    flat(*parts[:2])
    simple(parts, "tree_round")


def tree_pine():
    trunk = mat("tree_pine_trunk", (0.38, 0.23, 0.13), 0.9)
    dark = mat("tree_pine_needles", (0.14, 0.38, 0.26), 0.85)
    light = mat("tree_pine_needles_light", (0.22, 0.5, 0.32), 0.85)
    parts = [cyl(0.03, 0.12, (0, 0, 0.06), trunk, verts=6)]
    for k, (r, z0, h) in enumerate(((0.17, 0.08, 0.2), (0.135, 0.2, 0.18), (0.1, 0.31, 0.16), (0.06, 0.41, 0.17))):
        c = cyl(r, h, (0, 0, z0 + h / 2), dark if k % 2 == 0 else light, r2=0.0, verts=7,
                rot=(0, 0, k * 0.45))
        for v in c.data.vertices:   # a drooping, uneven skirt
            if v.co.z < z0 + 0.001:
                v.co.z -= 0.015 * (1 + math.sin(math.atan2(v.co.y, v.co.x) * 3 + k))
        parts.append(c)
    flat(*parts)
    simple(parts, "tree_pine")


def house():
    wall = mat("house_wall", (0.93, 0.84, 0.66), 0.9)
    beam = mat("house_beam", (0.4, 0.25, 0.15), 0.9)
    roof = mat("house_roof", (0.72, 0.24, 0.15), 0.8)
    tile = mat("house_roof_tile", (0.55, 0.16, 0.1), 0.8)
    door = mat("house_door", (0.35, 0.2, 0.12), 0.8)
    win = mat("house_window", (1.0, 0.8, 0.4), 0.5, emit=0.6)
    chim = mat("house_chimney", (0.6, 0.45, 0.38), 0.9)
    W, D, H = 0.32, 0.24, 0.2
    parts = [box((W, D, H), (0, 0, H / 2), wall, bevel=0.0),
             box((W + 0.01, D + 0.01, 0.02), (0, 0, 0.01), beam, bevel=0.0)]
    rh = 0.14
    # gable roof: a triangular prism along X
    roof_o = prism([(-D / 2 - 0.04, H - 0.01), (D / 2 + 0.04, H - 0.01), (0, H + rh)], W + 0.07, (0, 0, 0), roof,
                   rot=(0, 0, R90), bevel=0.0)
    gable = prism([(-D / 2, H), (D / 2, H), (0, H + rh - 0.02)], W - 0.005, (0, 0, 0), wall, rot=(0, 0, R90),
                  bevel=0.0)
    parts += [roof_o, gable,
              box((0.07, 0.02, 0.12), (0.06, -D / 2 - 0.005, 0.06), door, bevel=0.0),
              box((0.06, 0.02, 0.055), (-0.08, -D / 2 - 0.005, 0.12), win, bevel=0.0),
              box((0.07, 0.024, 0.012), (-0.08, -D / 2 - 0.006, 0.09), beam, bevel=0.0),
              box((0.02, 0.06, 0.055), (W / 2 + 0.005, 0.0, 0.12), win, bevel=0.0),
              box((0.02, 0.06, 0.055), (-W / 2 - 0.005, 0.0, 0.12), win, bevel=0.0),
              box((0.05, 0.05, 0.12), (0.09, 0.05, H + 0.1), chim, bevel=0.0),
              box((0.06, 0.06, 0.02), (0.09, 0.05, H + 0.16), beam, bevel=0.0),
              box((W + 0.08, 0.025, 0.02), (0, 0, H + rh + 0.002), tile, bevel=0.0)]
    run = D / 2 + 0.04
    slope = math.atan2(rh, run)
    for sgn in (1, -1):   # rows of tiles: darker strips down each slope
        for f in (0.3, 0.62, 0.92):
            parts.append(box((W + 0.075, 0.018, 0.008), (0, sgn * run * f, H - 0.01 + rh * (1 - f) + 0.005), tile,
                             rot=(sgn * slope, 0, 0), bevel=0.0))
    flat(*parts)
    simple(parts, "house")


def windmill():
    wall = mat("windmill_wall", (0.95, 0.9, 0.8), 0.9)
    roof = mat("windmill_roof", (0.35, 0.42, 0.62), 0.8)
    wood = mat("windmill_wood", (0.45, 0.28, 0.16), 0.9)
    sail = mat("windmill_sail", (0.96, 0.93, 0.85), 0.9)
    win = mat("windmill_window", (1.0, 0.8, 0.4), 0.5, emit=0.6)
    parts = [cyl(0.13, 0.38, (0, 0, 0.19), wall, r2=0.085, verts=8),
             cyl(0.14, 0.03, (0, 0, 0.015), wood, verts=8),
             cyl(0.1, 0.02, (0, 0, 0.385), wood, verts=8),
             cyl(0.105, 0.13, (0, 0, 0.46), roof, r2=0.0, verts=8),
             box((0.06, 0.03, 0.1), (0, -0.118, 0.05), wood, rot=(0.3, 0, 0), bevel=0.0),
             box((0.04, 0.03, 0.045), (0, -0.098, 0.22), win, rot=(0.19, 0, 0), bevel=0.0)]
    flat(*parts)
    root = join(parts, "windmill")
    hub = Vector((0, -0.1, 0.44))
    sp = [cyl(0.03, 0.05, hub + Vector((0, -0.01, 0)), wood, rot=(R90, 0, 0), verts=8)]
    for k in range(4):
        a = k * R90 + math.pi / 4
        d = Vector((math.cos(a), 0, math.sin(a)))
        sd = Vector((-d.z, 0, d.x))
        sp.append(rod(hub + d * 0.02 + Vector((0, -0.025, 0)), hub + d * 0.29 + Vector((0, -0.025, 0)), 0.008, wood,
                      verts=4))
        # the sail cloth on one side of the arm, as a thin quad slab
        c = hub + d * 0.17 + sd * 0.035 + Vector((0, -0.02, 0))
        cloth = box((0.21, 0.008, 0.06), c, sail, rot=(0, -a, 0), bevel=0.0)
        sp.append(cloth)
        for t in (0.09, 0.17, 0.25):
            sp.append(box((0.006, 0.012, 0.075), hub + d * t + sd * 0.035 + Vector((0, -0.025, 0)), wood,
                          rot=(0, -a, 0), bevel=0.0))
    flat(*sp)
    sail_o = join(sp, "sail", pivot=hub)
    animate(sail_o, "turn", {0: {"rot": (0, 0, 0)}, 48: {"rot": (0, -math.pi, 0)}, 96: {"rot": (0, -2 * math.pi, 0)}})
    export_anim(root, "windmill", [(sail_o, root)])


def rock():
    stone = mat("rock_stone", (0.58, 0.55, 0.5), 0.95)
    light = mat("rock_stone_light", (0.72, 0.69, 0.62), 0.95)
    moss = mat("rock_moss", (0.45, 0.6, 0.28), 0.95)
    parts = [lumpy(0.12, (0, 0, 0.07), stone, 11, 0.25, scale=(1.2, 1.0, 0.9)),
             lumpy(0.07, (0.13, -0.05, 0.035), light, 12, 0.25),
             lumpy(0.05, (-0.12, -0.07, 0.025), stone, 13, 0.25),
             lumpy(0.06, (-0.02, 0.0, 0.14), moss, 14, 0.2, scale=(1.4, 1.2, 0.45))]
    root = join(parts, "rock")
    for v in root.data.vertices:  # sit flat on the ground
        v.co.z = max(v.co.z, 0.0)
    simple([root], "rock")


def bush():
    leaf = mat("bush_leaves", (0.3, 0.55, 0.22), 0.9)
    light = mat("bush_leaves_light", (0.48, 0.72, 0.28), 0.9)
    flower = mat("bush_flower", (1.0, 0.55, 0.7), 0.7)
    parts = [lumpy(0.1, (0, 0, 0.08), leaf, 21, scale=(1.2, 1.1, 0.9)),
             lumpy(0.075, (0.1, -0.03, 0.06), light, 22),
             lumpy(0.07, (-0.1, 0.02, 0.06), leaf, 23),
             lumpy(0.06, (0.0, -0.05, 0.15), light, 24)]
    for k, p in enumerate(((0.05, -0.1, 0.12), (-0.08, -0.07, 0.1), (0.13, -0.08, 0.09), (-0.02, -0.02, 0.2),
                           (0.07, 0.06, 0.15))):
        parts.append(ico(0.018, p, flower, sub=1, smooth=0))
    root = join(parts, "bush")
    for v in root.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    simple([root], "bush")


def tower():
    stone = mat("tower_stone", (0.72, 0.68, 0.6), 0.95)
    dark = mat("tower_stone_dark", (0.55, 0.5, 0.45), 0.95)
    roof = mat("tower_roof", (0.3, 0.38, 0.6), 0.8)
    flag = mat("tower_flag", (0.85, 0.2, 0.18), 0.8)
    win = mat("tower_window", (1.0, 0.78, 0.35), 0.5, emit=0.6)
    wood = mat("tower_wood", (0.4, 0.25, 0.14), 0.9)
    parts = [cyl(0.13, 0.36, (0, 0, 0.18), stone, r2=0.11, verts=8),
             cyl(0.14, 0.04, (0, 0, 0.02), dark, verts=8),
             cyl(0.135, 0.05, (0, 0, 0.385), dark, verts=8)]
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        parts.append(box((0.045, 0.04, 0.045), (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.43), stone,
                         rot=(0, 0, a), bevel=0.0))
    parts += [cyl(0.1, 0.17, (0, 0, 0.495), roof, r2=0.0, verts=8),
              rod((0, 0, 0.55), (0, 0, 0.66), 0.005, wood, verts=4),
              prism([(0, 0.0), (0.08, -0.02), (0, -0.045)], 0.006, (0.0, 0, 0.655), flag, bevel=0.0),
              box((0.03, 0.02, 0.06), (0, -0.117, 0.25), win, rot=(0.06, 0, 0), bevel=0.0),
              box((0.06, 0.02, 0.09), (0, -0.126, 0.045), wood, rot=(0.06, 0, 0), bevel=0.0),
              box((0.02, 0.03, 0.05), (0.113, 0.0, 0.3), win, rot=(0, -0.06, 0), bevel=0.0)]
    flat(*parts)
    simple(parts, "tower")


def boat():
    hull = mat("boat_hull", (0.62, 0.3, 0.18), 0.85)
    trim = mat("boat_trim", (0.95, 0.9, 0.78), 0.85)
    wood = mat("boat_wood", (0.4, 0.25, 0.14), 0.9)
    sail = mat("boat_sail", (0.98, 0.94, 0.84), 0.9)
    pennant = mat("boat_pennant", (0.25, 0.45, 0.85), 0.8)
    prof = [(-0.075, 0.06), (-0.07, 0.01), (-0.045, -0.03), (0.0, -0.045), (0.045, -0.03), (0.07, 0.01), (0.075, 0.06)]
    st = [(-0.19, 0.75, 0.75, 0.01), (-0.12, 0.95, 0.95, 0.0), (0.0, 1.0, 1.0, 0.0), (0.1, 0.85, 0.9, 0.005),
          (0.18, 0.45, 0.75, 0.02), (0.22, 0.05, 0.6, 0.035)]
    h = loft_x(prof, st, hull, cap_start=True, cap_end=True, name="hull", smooth=0)
    bands = [loft_x([(sg * 0.074, 0.058), (sg * 0.079, 0.058), (sg * 0.079, 0.04), (sg * 0.074, 0.04)],
                    [(x, sy, 1, dz) for x, sy, _, dz in st[:-1]], trim, name="band", smooth=0) for sg in (1, -1)]
    deck = box((0.3, 0.12, 0.012), (-0.03, 0, 0.061), wood, bevel=0.0)
    parts = [h, deck] + bands + [
             rod((0.0, 0, 0.05), (0.0, 0, 0.42), 0.008, wood, verts=5),
             rod((-0.005, 0, 0.11), (-0.17, 0, 0.11), 0.006, wood, verts=4)]
    main = prism([(-0.16, 0.115), (-0.01, 0.115), (-0.01, 0.4)], 0.008, (0, 0, 0), sail, bevel=0.0)
    for v in main.data.vertices:   # a belly in the sail
        v.co.y += -0.03 * math.sin(max(0.0, min(1.0, (v.co.z - 0.115) / 0.285)) * math.pi) * (1 - abs(v.co.x) / 0.16)
    jib = prism([(0.01, 0.1), (0.2, 0.06), (0.01, 0.36)], 0.008, (0, 0, 0), sail, bevel=0.0)
    parts += [main, jib, prism([(0, 0.0), (0.06, -0.012), (0, -0.025)], 0.004, (0, 0, 0.42), pennant, bevel=0.0)]
    flat(*parts)
    simple(parts, "boat")


# ------------------------------------------------------------------ frame

def sweep_rect(profile, material, ox=BX, oy=BY, name="sweep", closed=True):
    """Sweeps a (d, z) profile around the board rectangle, d measured outwards from its edge, with mitred corners."""
    bm = bmesh.new()
    rows = []
    for d, z in profile:
        rows.append([bm.verts.new((sx * (ox + d), sy * (oy + d), z))
                     for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    n = len(rows)
    last = n if closed else n - 1
    for i in range(last):
        r0, r1 = rows[i], rows[(i + 1) % n]
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
    if closed:
        return new_obj(name, bm, material, smooth=30)
    # an open strip: face it upwards (recalc_face_normals cannot tell the side of an open surface)
    bm.normal_update()
    if sum(f.normal.z * f.calc_area() for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=30)


def frame():
    wood = mat("frame_wood", (0.26, 0.13, 0.06), 0.55, coat=0.5)
    light = mat("frame_wood_light", (0.55, 0.34, 0.17), 0.6, coat=0.4)
    gilt = mat("frame_gilt", (1.0, 0.74, 0.32), 0.35, 0.6, coat=0.3)
    inlay = mat("frame_inlay", (0.12, 0.06, 0.03), 0.6)
    B = -0.35
    body = [(0.0, B), (0.0, 0.04), (0.05, 0.05), (0.09, 0.09), (0.13, 0.11)]   # inner lip, rising gently
    body += [(0.3, 0.2), (0.36, 0.24), (0.44, 0.26), (0.5, 0.24), (0.55, 0.19), (0.58, 0.16), (0.6, 0.12),
             (0.6, B)]
    parts = [sweep_rect(body[::-1], wood, name="body", closed=True)]
    # carved lighter cove between the lip and the crown, a dark groove, gilt beads
    parts.append(sweep_rect([(0.13, 0.112), (0.2, 0.162), (0.29, 0.202)][::-1], light, name="cove", closed=False))
    parts.append(sweep_rect([(0.535, 0.205), (0.545, 0.196), (0.555, 0.19)][::-1], inlay, name="groove",
                            closed=False))
    for d, z, r in ((0.03, 0.05, 0.022), (0.4, 0.262, 0.018), (0.6, 0.12, 0.02)):
        bead = [(d - r, z), (d - r * 0.7, z + r * 0.7), (d, z + r), (d + r * 0.7, z + r * 0.7), (d + r, z)]
        parts.append(sweep_rect(bead[::-1], gilt, name="bead", closed=False))
    # corner bosses: a gilt rosette on a square wooden block
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        c = Vector((sx * (BX + 0.3), sy * (BY + 0.3), 0))
        parts.append(box((0.5, 0.5, 0.08), c + Vector((0, 0, 0.27)), wood, bevel=0.03, segs=2))
        parts.append(flat_disc(ring_star(8, 0.19, 0.11), 0.31, 0.34, gilt))
        parts[-1].location = c
        parts.append(cyl(0.09, 0.05, c + Vector((0, 0, 0.35)), light, r2=0.06, verts=16))
        parts.append(ico(0.05, c + Vector((0, 0, 0.38)), gilt, sub=2, scale=(1, 1, 0.6)))
    # compass medallions at the middle of each side, their star pointing at the board
    M = 0.36   # medallion centre, from the board edge
    for c in (Vector((0, BY + M, 0)), Vector((0, -BY - M, 0)), Vector((BX + M, 0, 0)), Vector((-BX - M, 0, 0))):
        parts.append(cyl(0.2, 0.05, c + Vector((0, 0, 0.255)), wood, r2=0.185, verts=20, bevel=0.012, segs=1))
        parts.append(torus(0.19, 0.013, c + Vector((0, 0, 0.283)), gilt, verts=20, minor=4))
        s = flat_disc(ring_star(4, 0.17, 0.045), 0.28, 0.303, gilt)
        s.location = c
        s2 = flat_disc(ring_star(4, 0.11, 0.035), 0.28, 0.298, light)
        s2.location = c
        s2.rotation_euler = (0, 0, math.pi / 4)
        parts += [s, s2, ico(0.03, c + Vector((0, 0, 0.305)), gilt, sub=1)]
    # dentils: a row of small carved blocks on the outer face, under the crown
    for k in range(-31, 32):
        x = k * 0.2
        if abs(x) > BX + 0.1:
            continue
        for sy in (1, -1):
            parts.append(box((0.1, 0.04, 0.09), (x, sy * (BY + 0.615), 0.02), light, bevel=0.0))
    for k in range(-23, 24):
        y = k * 0.2
        if abs(y) > BY + 0.1:
            continue
        for sx in (1, -1):
            parts.append(box((0.04, 0.1, 0.09), (sx * (BX + 0.615), y, 0.02), light, bevel=0.0))
    # small gilt studs along the crown
    for k in range(-5, 6):
        if k == 0:
            continue
        x = k * BX / 6.0 * 1.0
        for sy in (1, -1):
            parts.append(ico(0.022, (x, sy * (BY + 0.44), 0.275), gilt, sub=1))
    for k in range(-3, 4):
        if k == 0:
            continue
        y = k * BY / 4.0
        for sx in (1, -1):
            parts.append(ico(0.022, (sx * (BX + 0.44), y, 0.275), gilt, sub=1))
    simple(parts, "frame")


# ------------------------------------------------------------------ inkwell

def feather(base, tip, material, tipm, quill):
    """A feather along base->tip, vane in the plane facing -Y, with a few split barbs."""
    base, tip = Vector(base), Vector(tip)
    ax = tip - base
    L = ax.length
    t = ax.normalized()
    side = t.cross(Vector((0, 1, 0))).normalized()   # in the XZ-ish plane
    bend = Vector((0, -1, 0))
    parts = []
    shaft = []
    for i in range(9):
        u = i / 8
        shaft.append(base + ax * u + bend * 0.06 * math.sin(u * math.pi) * u)
    parts.append(K.tube(shaft, [0.012 - 0.009 * i / 8 for i in range(9)], quill, verts=6, caps=False))
    # vane: two surfaces (left and right of the shaft) from u = 0.22 to 1
    for sgn, seed in ((1, 5), (-1, 6)):
        for piece, (u0, u1, m) in enumerate(((0.22, 0.8, material), (0.8, 1.0, tipm))):
            bm = bmesh.new()
            rnd = random.Random(seed * 10 + piece)
            prev = None
            N = 10 if piece == 0 else 4
            for i in range(N + 1):
                u = u0 + (u1 - u0) * i / N
                p = base + ax * u + bend * 0.06 * math.sin(u * math.pi) * u
                w = 0.15 * math.sin(min(1.0, (u - 0.2) / 0.8) * math.pi) ** 0.6 * (1.0 if sgn > 0 else 0.8)
                if 0 < i < N and rnd.random() < 0.35:
                    w *= 0.7    # a split in the vane
                back = -0.05   # barbs sweep back towards the base
                q = p + side * sgn * w + t * back * w / 0.15
                cur = (bm.verts.new(p + side * sgn * 0.008), bm.verts.new(q))
                if prev:
                    f = (prev[0], prev[1], cur[1], cur[0])
                    bm.faces.new(f if sgn > 0 else f[::-1])
                prev = cur
            o = new_obj("vane", bm, m, smooth=0)
            s = o.modifiers.new("s", "SOLIDIFY")
            s.thickness = 0.006
            K.select(o)
            bpy.ops.object.modifier_apply(modifier="s")
            parts.append(o)
    return parts


def inkwell():
    glass = mat("inkwell_glass", (0.05, 0.08, 0.24), 0.08, coat=1.0)
    brass = mat("inkwell_brass", (0.92, 0.66, 0.3), 0.3, 1.0)
    ink = mat("inkwell_ink", (0.02, 0.02, 0.06), 0.05, coat=1.0)
    fea = mat("inkwell_feather", (0.96, 0.93, 0.86), 0.8)
    tipm = mat("inkwell_feather_tip", (0.2, 0.5, 0.6), 0.7)
    quill = mat("inkwell_quill", (0.85, 0.78, 0.6), 0.5)
    body = lathe([(0.0, 0.36), (0.16, 0.36), (0.24, 0.33), (0.29, 0.26), (0.3, 0.12), (0.27, 0.06), (0.0, 0.06)],
                 glass, segs=8, name="body")
    flat(body)
    parts = [body,
             cyl(0.33, 0.04, (0, 0, 0.02), brass, verts=24, bevel=0.012, segs=1),
             cyl(0.3, 0.025, (0, 0, 0.05), brass, r2=0.28, verts=24),
             torus(0.3, 0.012, (0, 0, 0.12), brass, verts=8, minor=4),
             cyl(0.13, 0.08, (0, 0, 0.39), brass, r2=0.12, verts=16, bevel=0.01, segs=1),
             torus(0.125, 0.018, (0, 0, 0.43), brass, verts=16, minor=5),
             cyl(0.11, 0.01, (0, 0, 0.425), ink, verts=16)]
    # hinged lid, flipped open behind the neck
    lid = cyl(0.14, 0.03, (0, 0, 0), brass, r2=0.11, verts=16, bevel=0.008, segs=1)
    knob = ico(0.03, (0, 0, 0.03), brass, sub=1)
    lid = join([lid, knob], "lid")
    lid.rotation_euler = (-1.9, 0, 0)
    lid.location = (0, 0.17, 0.5)
    parts.append(lid)
    parts.append(cyl(0.02, 0.06, (0, 0.13, 0.44), brass, rot=(0, R90, 0), verts=8))
    parts += feather((0.02, 0.0, 0.3), (0.42, 0.22, 1.16), fea, tipm, quill)
    simple(parts, "inkwell")


# ------------------------------------------------------------------ main

JOBS = {"marker": marker, "spark": spark, "spark_super": spark_super, "tree_round": tree_round,
        "tree_pine": tree_pine, "house": house, "windmill": windmill, "rock": rock, "bush": bush, "tower": tower,
        "boat": boat, "frame": frame, "inkwell": inkwell}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
