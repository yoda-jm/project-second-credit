"""Crate Keeper (game 11) props: the crate (plain, and lit when it sits on a goal), the goal marker, oak floor boards,
brick walls with a stone cap, and the harbour-warehouse dressing (barrel, rope coil, sacks, lamp post, anchor, net
pile, pallet, a stack of crates, a wall with a lit window).
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/crates_models.py -- godot/games/crates/art/models [name ...]

One grid cell = 1 unit, the front faces -Y, the origin sits at the cell centre on the floor (z = 0 is the top of the
floor boards). One node per file, named like the file, unless noted.
  crate.glb        0.86 x 0.86 x 0.74 pine crate: two painted steel straps over the top ("crate_band"), a stencilled
                   shipping mark on the top and the front, a brass latch with a dark lamp on the front
  crate_done.glb   the same crate, straps in green ("crate_band"), the latch lamp and a top lamp glowing ("crate_lamp")
  goal.glb         a brass plate with a glowing inset ring ("goal_glow"), a painted ring and four corner marks that stay
                   visible round a crate; flush with the floor (0 .. 0.012)
  floor_0/1.glb    1 x 1 oak board tiles, z -0.08 .. 0 (boards run along Y)
  wall_0/1.glb     1 x 1 x 1.1 brick blocks with a stone cap, z 0 .. 1.1 (wall_1: soot, a mooring ring, sea moss)
  window_wall.glb  a wall block with a lit window on its front (-Y) face ("window_glow")
  wall_corner.glb  a wall block with a stone quoin pilaster, for the outer corners
  dressing (outside the playfield): barrel, rope_coil, sack_pile, lamp_post (about 1.9 tall; its glass is
  "lamp_glow"; a child node "bulb" at the light's centre, z = 1.66: hang an OmniLight3D there), anchor, net_pile,
  pallet, crate_stack (3 crates, about 1.75 tall)
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, jitter, finish, R90


def glow(name, color, strength, base=None, rough=0.3):
    return mat(name, base or color, rough, emit=strength, emit_color=color)


def lathe(profile, material, segs=20, loc=(0, 0, 0), smooth=50):
    """A solid of revolution round Z through [(radius, z)] bottom to top, closed with flat caps."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((loc[0] + r * math.cos(2 * math.pi * i / segs), loc[1] + r * math.sin(2 * math.pi * i / segs),
                                    loc[2] + z)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("lathe")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("lathe", me)
    bpy.context.scene.collection.objects.link(o)
    return finish(o, material, smooth=smooth)


def rot_parts(parts, R, t=(0, 0, 0)):
    """Rotates (a 3x3 matrix) then moves parts about the origin."""
    M4 = Matrix.Translation(t) @ R.to_4x4()
    for o in parts:
        o.data.transform(M4 @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    return parts


# ------------------------------------------------------------------ crate

CS, CH = 0.86, 0.74      # crate width and height


def crate_parts(done=False, detail=True, s=CS, h=CH, seed=0):
    wood = mat("crate_wood", (0.78, 0.56, 0.3), 0.62, coat=0.12)
    frame = mat("crate_frame", (0.55, 0.35, 0.16), 0.66, coat=0.1)
    seam = mat("crate_seam", (0.22, 0.13, 0.06), 0.9)
    band = (mat("crate_band", (0.2, 0.52, 0.34), 0.35, 0.55, coat=0.4) if done else
            mat("crate_band", (0.62, 0.16, 0.09), 0.4, 0.45, coat=0.35))
    bolt = mat("crate_bolt", (0.2, 0.19, 0.18), 0.4, 0.85)
    ink = mat("crate_stencil", (0.14, 0.09, 0.06), 0.85)
    brass = mat("crate_brass", (0.88, 0.64, 0.3), 0.28, 0.95)
    lamp = (glow("crate_lamp", (0.35, 1.0, 0.45), 7.0, base=(0.4, 1.0, 0.5)) if done else
            mat("crate_lamp", (0.08, 0.14, 0.1), 0.15, coat=1.0))
    J = jitter(11 + seed)
    t = 0.09                      # corner post size
    parts = [box((s - 0.04, s - 0.04, h - 0.04), (0, 0, h / 2), wood, bevel=0.012, segs=1)]
    # corner posts and the rims round the top and bottom
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((t, t, h), (sx * (s - t) / 2, sy * (s - t) / 2, h / 2), frame, bevel=0.022, segs=1))
    for z in ((h - 0.045,) if detail else ()):
        for ax in range(2):
            for sg in (-1, 1):
                size = (s - 2 * t + 0.01, t * 0.8, t) if ax == 0 else (t * 0.8, s - 2 * t + 0.01, t)
                loc = (0, sg * (s / 2 - t * 0.4), z) if ax == 0 else (sg * (s / 2 - t * 0.4), 0, z)
                parts.append(box(size, loc, frame, bevel=0.018, segs=1))
    # board seams on the sides and the top (the boards run across)
    for side in range(4 if detail else 0):
        R = Matrix.Rotation(side * R90, 3, "Z")
        for z in (0.3, 0.46):
            p = R @ Vector((0, -(s / 2 - 0.018), z))
            parts.append(box((s - 2 * t, 0.012, 0.012), p, seam, rot=(0, 0, side * R90), bevel=0.0))
    for k in ((-1, 0, 1) if detail else ()):
        parts.append(box((s - 2 * t, 0.012, 0.012), (0, k * 0.17, h - 0.018), seam, bevel=0.0))
    # two straps over the top, down the front and the back
    for x in (-0.22, 0.22):
        parts.append(box((0.07, s + 0.02, 0.016), (x, 0, h + 0.004), band, bevel=0.006 if detail else 0.0, segs=1))
        for sy in (-1, 1):
            parts.append(box((0.07, 0.016, h - 0.02), (x, sy * (s / 2 + 0.004), h / 2 + 0.01), band, bevel=0.006 if detail else 0.0, segs=1))
            if detail and sy < 0:
                parts.append(cyl(0.013, 0.012, (x, sy * (s / 2 + 0.013), h - 0.14), bolt, rot=(R90, 0, 0), verts=6))
    if detail:
        # the stencilled shipping mark: a diamond with a bar and a dot, on the top and the front
        def mark(M_, scale, dots=True):
            out = []
            d = 0.12 * scale
            for a in range(4):
                ang = a * R90 + math.pi / 4
                c = Vector((math.cos(ang - math.pi / 4) * d * 0.5, math.sin(ang - math.pi / 4) * d * 0.5, 0))
                c = Matrix.Rotation(math.pi / 4, 3, "Z") @ Vector((math.cos(a * R90), math.sin(a * R90), 0)) * d * 0.5
                out.append(box((0.018 * scale, d * 1.02, 0.004), c, ink, rot=(0, 0, a * R90 + math.pi / 4), bevel=0.0))
            out.append(box((d * 1.1, 0.02 * scale, 0.004), (0, 0, 0), ink, bevel=0.0))
            if dots:
                out.append(cyl(0.016 * scale, 0.004, (0, 0.03 * scale, 0), ink, verts=8))
                out.append(cyl(0.016 * scale, 0.004, (0, -0.03 * scale, 0), ink, verts=8))
            return rot_parts(out, M_[0], M_[1])
        parts += mark((Matrix.Identity(3), (0, 0.0, h + 0.002)), 1.2)
        parts += mark((Matrix.Rotation(R90, 3, "X"), (0, -s / 2 - 0.0, 0.52)), 1.0, False)
        # arrows "this side up" on the front's lower board
        for x in (-0.09, 0.09):
            parts.append(prism([(-0.025, 0.0), (0.025, 0.0), (0.0, 0.04)], 0.004, (x, -s / 2 - 0.001, 0.2), ink, bevel=0.0))
            parts.append(box((0.012, 0.004, 0.05), (x, -s / 2 - 0.001, 0.175), ink, bevel=0.0))
        # the latch on the front: a brass plate with a round lamp; a second lamp on the top
        parts.append(box((0.12, 0.02, 0.1), (0, -s / 2 - 0.01, h - 0.16), brass, bevel=0.008, segs=1))
        parts.append(cyl(0.03, 0.014, (0, -s / 2 - 0.022, h - 0.16), lamp, rot=(R90, 0, 0), verts=10))
        parts.append(cyl(0.05, 0.02, (0.33, -0.33, h + 0.01), brass, verts=12, bevel=0.005))
        parts.append(sphere(0.036, (0.33, -0.33, h + 0.02), lamp, scale=(1, 1, 0.7), segs=10, rings=5))
    return parts


def crate(done=False):
    simple(crate_parts(done), "crate_done" if done else "crate")


# ------------------------------------------------------------------ goal

def goal():
    paint = mat("goal_paint", (0.92, 0.8, 0.5), 0.7)
    brass = mat("goal_brass", (0.86, 0.62, 0.28), 0.25, 1.0)
    dark = mat("goal_recess", (0.12, 0.08, 0.05), 0.6, 0.5)
    lamp = glow("goal_glow", (1.0, 0.62, 0.18), 2.2, base=(0.9, 0.55, 0.2))
    parts = [cyl(0.3, 0.012, (0, 0, 0.006), brass, verts=32, bevel=0.004, segs=1),
             cyl(0.22, 0.004, (0, 0, 0.014), dark, verts=32),
             cyl(0.2, 0.006, (0, 0, 0.014), lamp, verts=32),
             cyl(0.15, 0.008, (0, 0, 0.016), brass, verts=32, bevel=0.003, segs=1),
             cyl(0.045, 0.004, (0, 0, 0.021), lamp, verts=16)]
    for a in range(4):   # four rivets on the plate
        ang = a * R90 + math.pi / 4
        parts.append(sphere(0.014, (math.cos(ang) * 0.26, math.sin(ang) * 0.26, 0.012), brass, scale=(1, 1, 0.5), segs=8, rings=4))
    # a painted ring round the plate and corner marks at the cell's corners (outside a crate's footprint)
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=0.37, fill_type="NOTHING")
    o = K.active()
    K.select(o)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0)})
    bpy.ops.transform.resize(value=(0.9, 0.9, 1))
    bpy.ops.object.mode_set(mode="OBJECT")
    o.location = (0, 0, 0.002)
    parts.append(finish(o, paint, smooth=0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = Vector((sx * 0.44, sy * 0.44, 0.002))
            parts.append(box((0.14, 0.035, 0.004), c + Vector((-sx * 0.052, 0, 0)), paint, bevel=0.0))
            parts.append(box((0.035, 0.14, 0.004), c + Vector((0, -sy * 0.052, 0)), paint, bevel=0.0))
    simple(parts, "goal")


# ------------------------------------------------------------------ floor

OAK = [(0.46, 0.27, 0.13), (0.52, 0.31, 0.15), (0.41, 0.23, 0.11), (0.56, 0.34, 0.17), (0.48, 0.29, 0.14)]


def floor(v):
    J = jitter(100 + v)
    under = mat("floor_gap", (0.08, 0.05, 0.03), 0.95)
    nail = mat("floor_nail", (0.16, 0.15, 0.14), 0.4, 0.8)
    tones = [mat("oak_%d" % i, c, 0.58 + 0.04 * (i % 2), coat=0.18) for i, c in enumerate(OAK)]
    parts = [box((1.0, 1.0, 0.04), (0, 0, -0.06), under, bevel=0.0)]
    n = 4
    w = 1.0 / n
    g = 0.006
    for i in range(n):
        x = -0.5 + w * (i + 0.5)
        # one board in two meets a butt joint inside the tile, at a different place per variant
        cuts = [-0.5, 0.5]
        if (i + v) % 2 == 0:
            cuts = [-0.5, round(J(-0.3, 0.3), 3), 0.5]
        for k, (y0, y1) in enumerate(zip(cuts, cuts[1:])):
            m = tones[(i * 2 + k * 3 + v * 3) % len(tones)]
            dz = J(-0.003, 0.002)
            parts.append(box((w - 2 * g, y1 - y0 - 2 * g, 0.05 + dz), (x, (y0 + y1) / 2, -0.025 + dz / 2), m,
                             rot=(0, 0, J(-0.004, 0.004)), bevel=0.01, segs=1))
            for yy in (y0 + 0.04, y1 - 0.04):
                for xx in (x - w * 0.28, x + w * 0.28):
                    parts.append(cyl(0.008, 0.002, (xx, yy, 0.0), nail, verts=5))
    # a knot and a worn streak on one board
    kx = -0.5 + w * (0.5 + (v * 3 + 1) % n)
    parts.append(sphere(0.025, (kx + 0.02, J(-0.3, 0.3), -0.001), mat("oak_knot", (0.24, 0.13, 0.06), 0.7),
                        scale=(0.7, 1.4, 0.1), segs=10, rings=4))
    simple(parts, "floor_%d" % v)


# ------------------------------------------------------------------ walls

BRICK = [(0.55, 0.22, 0.14), (0.62, 0.27, 0.16), (0.5, 0.2, 0.13), (0.6, 0.3, 0.2), (0.46, 0.19, 0.13)]
WALL_H, CAP_Z = 1.1, 0.96


def wall_parts(v, window=False):
    J = jitter(200 + v)
    mortar = mat("mortar", (0.52, 0.48, 0.42), 0.95)
    tones = [mat("brick_%d" % i, c, 0.8, coat=0.05) for i, c in enumerate(BRICK)]
    soot = mat("brick_soot", (0.24, 0.13, 0.1), 0.85)
    stone = mat("cap_stone", (0.4, 0.37, 0.34), 0.75, coat=0.1)
    stone_d = mat("cap_stone_dark", (0.26, 0.24, 0.22), 0.8)
    stone_m = mat("cap_stone_2", (0.36, 0.34, 0.32), 0.8, coat=0.05)
    parts = [box((0.97, 0.97, CAP_Z), (0, 0, CAP_Z / 2), mortar, bevel=0.0)]
    courses = 6
    ch = CAP_Z / courses
    g = 0.011
    for c in range(courses):
        z = ch * (c + 0.5)
        spans = [(-0.5, 0.0), (0.0, 0.5)] if (c + v) % 2 == 0 else [(-0.5, -0.25), (-0.25, 0.25), (0.25, 0.5)]
        for k, (x0, x1) in enumerate(spans):
            if window and 1 <= c <= 4 and x0 < 0.25 and x1 > -0.25 and (x1 - x0) < 0.9:
                # the window's opening: only the brick's ends stay (the frame covers the rest)
                pass
            m = tones[(c * 3 + k * 2 + v) % len(tones)]
            if v == 1 and ((c, k) in ((1, 1), (2, 0), (4, 2), (5, 1))):
                m = soot
            dz = J(-0.004, 0.004)
            parts.append(box((x1 - x0 - 2 * g, 0.985 + J(-0.006, 0.0), ch - 2 * g + dz), ((x0 + x1) / 2, J(-0.003, 0.003), z),
                             m, bevel=0.018, segs=1))
    # the stone cap, a little proud of the bricks, and a drip line under it
    for k, y in enumerate((-0.25, 0.25)):   # two coping slabs, a hairline apart, a touch uneven
        dz = J(-0.006, 0.004)
        parts.append(box((1.0, 0.494, WALL_H - CAP_Z + dz), (0, y, (CAP_Z + WALL_H + dz) / 2),
                         stone if (k + v) % 2 == 0 else stone_m, bevel=0.022, segs=2))
    parts.append(box((0.99, 0.99, 0.025), (0, 0, CAP_Z + 0.004), stone_d, bevel=0.006, segs=1))
    if v == 1:
        iron = mat("ring_iron", (0.16, 0.14, 0.13), 0.45, 0.8)
        rust = mat("ring_rust", (0.36, 0.16, 0.07), 0.8, 0.3)
        moss = mat("sea_moss", (0.18, 0.28, 0.12), 0.9)
        parts.append(cyl(0.05, 0.03, (0.18, -0.5, 0.5), iron, rot=(R90, 0, 0), verts=12, bevel=0.008))
        parts.append(torus(0.075, 0.014, (0.18, -0.525, 0.43), rust, rot=(R90 * 0.8, 0, 0), verts=16, minor=6))
        for x in (-0.36, -0.2, 0.3):
            parts.append(ico(J(0.05, 0.08), (x, -0.49, 0.02), moss, scale=(1.6, 0.35, 0.8), sub=1))
    return parts


def wall(v):
    simple(wall_parts(v), "wall_%d" % v)


def window_wall():
    frame = mat("window_frame", (0.2, 0.3, 0.32), 0.5, coat=0.3)
    sill = mat("cap_stone", (0.4, 0.37, 0.34), 0.75, coat=0.1)
    glass = glow("window_glow", (1.0, 0.6, 0.25), 1.8, base=(1.0, 0.7, 0.4))
    shade = mat("window_dark", (0.1, 0.07, 0.05), 0.8)
    parts = wall_parts(0, window=True)
    y = -0.5
    zc, wd, ht = 0.5, 0.46, 0.5
    parts.append(box((wd + 0.08, 0.06, ht + 0.08), (0, y - 0.005, zc), frame, bevel=0.015, segs=1))
    parts.append(box((wd - 0.02, 0.02, ht - 0.02), (0, y - 0.03, zc), glass, bevel=0.0))
    parts.append(box((wd - 0.02, 0.022, 0.11), (0, y - 0.031, zc + ht / 2 - 0.07), shade, bevel=0.0))  # a blind half down
    for x in (-wd / 6, wd / 6):
        parts.append(box((0.025, 0.03, ht - 0.02), (x, y - 0.04, zc), frame, bevel=0.006, segs=1))
    parts.append(box((wd - 0.02, 0.03, 0.025), (0, y - 0.04, zc), frame, bevel=0.006, segs=1))
    parts.append(box((wd + 0.16, 0.12, 0.05), (0, y - 0.04, zc - ht / 2 - 0.06), sill, bevel=0.012, segs=1))
    parts.append(box((wd + 0.12, 0.1, 0.06), (0, y - 0.03, zc + ht / 2 + 0.06), sill, bevel=0.012, segs=1))  # lintel
    simple(parts, "window_wall")


def wall_corner():
    stone = mat("cap_stone", (0.4, 0.37, 0.34), 0.75, coat=0.1)
    stone_d = mat("cap_stone_dark", (0.26, 0.24, 0.22), 0.8)
    parts = wall_parts(0)
    ch = CAP_Z / 3
    for c in range(3):   # quoin blocks, alternately long and short, proud on every side
        w = 1.03 if c % 2 == 0 else 0.99
        parts.append(box((w, w, ch - 0.02), (0, 0, ch * (c + 0.5)), stone if c % 2 == 0 else stone_d, bevel=0.03, segs=2))
    parts.append(box((1.05, 1.05, WALL_H - CAP_Z + 0.03), (0, 0, (CAP_Z + WALL_H) / 2 + 0.015), stone, bevel=0.03, segs=2))
    parts.append(sphere(0.12, (0, 0, WALL_H + 0.03), stone, scale=(1, 1, 0.55), segs=12, rings=5))
    simple(parts, "wall_corner")


# ------------------------------------------------------------------ dressing

def barrel():
    wood = mat("barrel_wood", (0.5, 0.3, 0.15), 0.6, coat=0.2)
    lid = mat("barrel_lid", (0.42, 0.25, 0.12), 0.7)
    iron = mat("barrel_hoop", (0.2, 0.18, 0.17), 0.4, 0.8)
    stave = mat("barrel_stave", (0.28, 0.16, 0.08), 0.8)
    h, r0, r1 = 0.66, 0.22, 0.27
    prof = [(r0, 0.0)]
    for i in range(1, 8):
        z = h * i / 8
        prof.append((r0 + (r1 - r0) * math.sin(math.pi * z / h), z))
    prof.append((r0, h))
    parts = [lathe(prof, wood, 20)]
    parts.append(cyl(r0 - 0.02, 0.02, (0, 0, h - 0.005), lid, verts=20))
    for z in (0.05, 0.2, h - 0.2, h - 0.05):
        rr = r0 + (r1 - r0) * math.sin(math.pi * z / h) + 0.006
        parts.append(torus(rr, 0.012, (0, 0, z), iron, verts=20, minor=4))
    for i in range(10):   # stave lines
        a = 2 * math.pi * (i + 0.5) / 10
        pts = []
        for zz in (0.08, h / 2, h - 0.08):
            rr = r0 + (r1 - r0) * math.sin(math.pi * zz / h) + 0.001
            pts.append((math.cos(a) * rr, math.sin(a) * rr, zz))
        parts.append(tube(pts, [0.004] * 3, stave, verts=3, caps=False))
    parts.append(cyl(0.03, 0.02, (0.1, -0.05, h), iron, verts=8))   # the bung
    simple(parts, "barrel")


def rope_coil():
    rope = mat("rope", (0.72, 0.58, 0.36), 0.9)
    rope_d = mat("rope_end", (0.55, 0.42, 0.24), 0.9)
    pts, radii = [], []
    turns, n = 3.4, 68
    for i in range(n + 1):
        u = i / n
        a = 2 * math.pi * turns * u
        r = 0.1 + 0.17 * u
        z = 0.032 + 0.02 * math.sin(a * 0.5) * 0.3
        pts.append((math.cos(a) * r, math.sin(a) * r, z))
        radii.append(0.03)
    parts = [tube(pts, radii, rope, verts=6)]
    # a second, smaller coil on top and the loose end trailing out
    pts2 = []
    for i in range(29):
        u = i / 28
        a = 2 * math.pi * 1.6 * u + 1.0
        r = 0.12 + 0.06 * u
        pts2.append((math.cos(a) * r, math.sin(a) * r, 0.088))
    parts.append(tube(pts2, [0.028] * len(pts2), rope, verts=6))
    end = pts[-1]
    parts.append(tube([end, (end[0] + 0.1, end[1] - 0.12, 0.03), (end[0] + 0.14, end[1] - 0.28, 0.03)], [0.03, 0.03, 0.028],
                      rope_d, verts=7))
    simple(parts, "rope_coil")


def sack_pile():
    burlap = [mat("burlap", (0.66, 0.54, 0.36), 0.95), mat("burlap_dark", (0.55, 0.44, 0.28), 0.95)]
    twine = mat("sack_twine", (0.38, 0.28, 0.16), 0.9)
    stamp = mat("sack_stamp", (0.45, 0.14, 0.08), 0.9)
    parts = []
    spec = [((-0.18, 0.08, 0.1), 0.15, 0), ((0.2, 0.1, 0.1), -0.1, 1), ((0.0, -0.2, 0.1), 1.45, 0), ((0.02, 0.05, 0.27), 0.25, 1)]
    for (x, y, z), yaw, t in spec:
        b = box((0.46, 0.3, 0.2), (0, 0, 0), burlap[t], bevel=0.09, segs=3)
        ear = sphere(0.05, (0.25, 0, 0.0), twine, scale=(1.0, 1.1, 0.8), segs=8, rings=5)
        tip = sphere(0.06, (0.3, 0, 0.0), burlap[t], scale=(0.8, 1.2, 0.9), segs=8, rings=5)
        mark = box((0.12, 0.004, 0.08), (-0.04, -0.15, 0.02), stamp, bevel=0.0)
        rot_parts([b, ear, tip, mark], Matrix.Rotation(yaw, 3, "Z"), (x, y, z))
        parts += [b, ear, tip, mark]
    simple(parts, "sack_pile")


def lamp_post():
    iron = mat("post_iron", (0.1, 0.12, 0.12), 0.4, 0.75)
    trim = mat("post_brass", (0.8, 0.58, 0.28), 0.3, 0.95)
    glass = glow("lamp_glow", (1.0, 0.72, 0.36), 6.0, base=(1.0, 0.85, 0.6), rough=0.15)
    parts = [lathe([(0.17, 0.0), (0.17, 0.05), (0.13, 0.08), (0.12, 0.2), (0.07, 0.3), (0.05, 0.36)], iron, 16),
             cyl(0.04, 1.2, (0, 0, 0.94), iron, r2=0.03, verts=12),
             torus(0.05, 0.012, (0, 0, 0.42), trim, verts=14, minor=4),
             torus(0.042, 0.01, (0, 0, 1.4), trim, verts=14, minor=4),
             lathe([(0.05, 1.48), (0.1, 1.53), (0.11, 1.56)], iron, 12)]
    # the lantern: glass panes between four posts, a roof and a finial
    zc, hw, hh = 1.67, 0.1, 0.13
    for a in range(4):
        R = Matrix.Rotation(a * R90, 3, "Z")
        parts.append(box((0.17, 0.008, 0.21), R @ Vector((0, -hw + 0.004, zc)), glass, rot=(0, 0, a * R90), bevel=0.0))
        c = R @ Vector((hw, hw, zc))
        parts.append(box((0.022, 0.022, 0.25), c, iron, bevel=0.004, segs=1))
    parts.append(box((0.23, 0.23, 0.03), (0, 0, zc - hh), iron, bevel=0.008, segs=1))
    parts.append(cyl(0.18, 0.1, (0, 0, zc + hh + 0.05), iron, r2=0.03, verts=4, rot=(0, 0, math.pi / 4)))
    parts.append(sphere(0.03, (0, 0, zc + hh + 0.12), trim, segs=10, rings=6))
    # a crossbar arm (for a ladder or a rope)
    parts.append(rod((-0.18, 0, 1.44), (0.18, 0, 1.44), 0.014, iron, verts=8))
    for x in (-0.18, 0.18):
        parts.append(sphere(0.022, (x, 0, 1.44), trim, segs=8, rings=5))
    root = join(parts, "lamp_post")
    bulb = join([ico(0.045, (0, 0, zc), glass, sub=2), cyl(0.012, 0.06, (0, 0, zc - 0.07), trim, verts=8)],
                "bulb", pivot=(0, 0, zc))
    export(root, "lamp_post", [(bulb, root)])


def anchor():
    iron = mat("anchor_iron", (0.13, 0.13, 0.14), 0.5, 0.7)
    rust = mat("anchor_rust", (0.42, 0.19, 0.08), 0.85, 0.2)
    parts = []
    # built standing (shank along +Y on the floor plane), then laid flat
    parts.append(rod((0, -0.4, 0), (0, 0.36, 0), 0.035, iron, verts=10))
    parts.append(torus(0.07, 0.018, (0, 0.45, 0), rust, rot=(0, R90, 0), verts=16, minor=6))
    parts.append(rod((-0.24, 0.28, 0), (0.24, 0.28, 0), 0.022, rust, verts=8))     # the stock
    for x in (-0.24, 0.24):
        parts.append(sphere(0.032, (x, 0.28, 0), rust, segs=8, rings=5))
    pts = []
    for i in range(13):
        a = math.pi * (0.1 + 0.8 * i / 12)
        pts.append((math.cos(a) * 0.3, -0.36 - math.sin(a) * 0.12 + 0.12, 0))
    parts.append(tube(pts, [0.03] * len(pts), iron, verts=8))
    for sx in (-1, 1):
        tip = Vector(pts[0] if sx > 0 else pts[-1])
        fl = prism([(-0.05, -0.02), (0.05, -0.02), (0.0, 0.1)], 0.02, (0, 0, 0), iron, bevel=0.005)
        rot_parts([fl], Matrix.Rotation(R90, 3, "X") @ Matrix.Identity(3), (0, 0, 0))
        rot_parts([fl], Matrix.Rotation(-sx * 0.9, 3, "Z"), tuple(tip + Vector((sx * -0.01, 0.0, 0))))
        parts.append(fl)
    parts.append(sphere(0.045, (0, -0.4, 0), iron, segs=10, rings=6))
    rot_parts(parts, Matrix.Rotation(0.5, 3, "Z"), (0, 0, 0.036))
    simple(parts, "anchor")


def net_pile():
    net = mat("fishing_net", (0.24, 0.32, 0.26), 0.9)
    net_d = mat("fishing_net_dark", (0.16, 0.22, 0.18), 0.95)
    cork = mat("net_float", (0.86, 0.44, 0.16), 0.6, coat=0.2)
    cream = mat("net_float_cream", (0.9, 0.84, 0.7), 0.6)
    J = jitter(77)
    parts = []
    for i in range(6):
        a = i * 1.1
        r = 0.18 if i else 0.0
        parts.append(ico(J(0.18, 0.26), (math.cos(a) * r, math.sin(a) * r, 0.05), net if i % 2 else net_d,
                         scale=(1.3, 1.0, 0.55), sub=2, smooth=60))
    for i in range(6):
        a = i * 1.05 + 0.3
        r = J(0.16, 0.3)
        m = cork if i % 2 == 0 else cream
        parts.append(cyl(0.035, 0.07, (math.cos(a) * r, math.sin(a) * r, J(0.12, 0.2)), m, verts=10, bevel=0.01,
                         rot=(J(0.4, 1.2), 0, a)))
    rope = mat("rope", (0.72, 0.58, 0.36), 0.9)
    parts.append(tube([(-0.3, -0.25, 0.02), (-0.1, -0.2, 0.14), (0.15, -0.12, 0.2), (0.32, 0.05, 0.1), (0.42, 0.1, 0.02)],
                      [0.014] * 5, rope, verts=6))
    simple(parts, "net_pile")


def pallet():
    wood = mat("pallet_wood", (0.68, 0.52, 0.32), 0.8)
    wood_d = mat("pallet_wood_dark", (0.52, 0.38, 0.22), 0.85)
    J = jitter(5)
    parts = []
    for x in (-0.38, 0.0, 0.38):
        for y in (-0.38, 0.0, 0.38):
            parts.append(box((0.12, 0.12, 0.07), (x, y, 0.035), wood_d, bevel=0.01, segs=1))
    for y in (-0.38, 0.0, 0.38):
        parts.append(box((0.9, 0.12, 0.025), (0, y, 0.0825), wood, bevel=0.006, segs=1))
    for i in range(6):
        x = -0.39 + i * 0.156
        parts.append(box((0.11, 0.9, 0.022), (x, 0, 0.106), wood if i % 2 else wood_d, rot=(0, 0, J(-0.01, 0.01)),
                         bevel=0.006, segs=1))
    simple(parts, "pallet")


def crate_stack():
    a = crate_parts(detail=False, seed=1)
    b = rot_parts(crate_parts(detail=False, s=0.7, h=0.6, seed=2), Matrix.Rotation(0.3, 3, "Z"), (0.04, 0.02, CH))
    c = rot_parts(crate_parts(detail=False, s=0.46, h=0.4, seed=3), Matrix.Rotation(-0.25, 3, "Z"), (-0.02, 0.0, CH + 0.6))
    simple(a + b + c, "crate_stack")


# ------------------------------------------------------------------ main

def build_all(only):
    jobs = {"crate": lambda: crate(False), "crate_done": lambda: crate(True), "goal": goal,
            "floor_0": lambda: floor(0), "floor_1": lambda: floor(1), "wall_0": lambda: wall(0), "wall_1": lambda: wall(1),
            "window_wall": window_wall, "wall_corner": wall_corner, "barrel": barrel, "rope_coil": rope_coil,
            "sack_pile": sack_pile, "lamp_post": lamp_post, "anchor": anchor, "net_pile": net_pile, "pallet": pallet,
            "crate_stack": crate_stack}
    for k, fn in jobs.items():
        if not only or k in only:
            reset()
            fn()


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    reset()
    build_all(args[1:])
