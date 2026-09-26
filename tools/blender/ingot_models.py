"""Ingot Run (game 10) props: the grid tiles (two sandstone bricks, the trap brick, granite stone, ladder, bar, the
golden exit ladder), gold, the rubble of a refilling hole, and the temple-mine dressing (carved back wall in three
variants, hanging lantern, wall torch, pillar, arch, mine cart, crate).
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/ingot_models.py -- godot/games/ingot/art/models [name ...]

One grid cell = 1 unit, seen from the front (the camera looks along +Y, slightly from above). The origin is at the
cell centre: a cell spans -0.5..0.5 in X and Z and a block is about 1 deep along Y (-0.5..0.5), its face toward -Y.
  brick_0.glb, brick_1.glb  diggable sandstone blocks (two variants, one node each: brick_0 / brick_1)
  trap_brick.glb            a false brick: the same block with hairline cracks and a slightly paler, worn face
  stone.glb                 undiggable granite block with bronze studs
  ladder.glb                wooden ladder filling the cell height (tiles vertically), rungs every 0.25 at z = -0.375,
                            -0.125, 0.125, 0.375, its plane 0.15 behind the cell centre (y = +0.15)
  exit_ladder.glb           the same ladder in glowing gold (emissive) for the escape route
  bar.glb                   a twisted hemp rope across the top of the cell (axis at z = +0.4, y = 0, about 0.1 thick; tiles along X)
  gold.glb                  a pile of ingots and coins on the cell floor (z = -0.5 up), with emissive glints
  rubble.glb                a few sandstone chunks on the cell floor: the hole refilling (scale it up in Z)
  back_wall_0..2.glb        1x1 carved panels behind the grid: front face at y = +0.5, 0.12 thick
  lantern.glb               a hanging lantern: its chain reaches the top of the cell, the glass glows ("lantern")
  torch.glb                 a wall torch on a bracket against the back of the cell; child node "flame" at the tip
                            (the flame's origin at its base: flicker it by scaling)
  pillar.glb                three nodes stacked at the origin, one cell each: pillar_base, pillar_shaft (tiles in Z),
                            pillar_capital
  arch.glb                  a stone arch 3 cells wide (x -1.5..1.5) and about 2.6 tall (z -0.5..2.07); origin at the
                            centre of its bottom-middle cell; the opening is 2 cells wide
  mine_cart.glb, crate.glb  background dressing standing on the cell floor
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, jitter, R90

FLOOR = -0.5


def glow(name, color, strength, base=None, rough=0.3):
    return mat(name, base or color, rough, emit=strength, emit_color=color)


# ------------------------------------------------------------------ bricks

SAND = [(0.6, 0.35, 0.16), (0.53, 0.3, 0.13), (0.66, 0.41, 0.2), (0.49, 0.27, 0.12)]


def brick_block(name, seed, cracked=False):
    """Two courses of sandstone bricks in running bond over a recessed mortar core, full depth, so the top reads
    too. The bricks stop 0.012 short of the cell edge: neighbours meet with a mortar line."""
    J = jitter(seed)
    mortar = mat("mortar", (0.17, 0.11, 0.065), 0.95)
    tones = [mat("sandstone_%d" % i, c, 0.82, coat=0.05) for i, c in enumerate(SAND)]
    if cracked:
        tones = [mat("sandstone_worn_%d" % i, tuple(min(1.0, x * 1.08 + 0.025) for x in c), 0.9) for i, c in enumerate(SAND)]
    parts = [box((0.97, 0.97, 0.97), (0, 0, 0), mortar, bevel=0.02, segs=1)]
    g = 0.012   # half the mortar gap
    courses = [(0.25, [(-0.5, 0.0), (0.0, 0.5)]), (-0.25, [(-0.5, -0.25), (-0.25, 0.25), (0.25, 0.5)])]
    if seed % 2:
        courses = [(0.25, [(-0.5, -0.25), (-0.25, 0.25), (0.25, 0.5)]), (-0.25, [(-0.5, 0.0), (0.0, 0.5)])]
    k = 0
    for zc, spans in courses:
        for x0, x1 in spans:
            w = x1 - x0 - 2 * g
            h = 0.5 - 2 * g
            m = tones[(k * 3 + seed) % len(tones)]
            k += 1
            dz = J(-0.006, 0.006)
            parts.append(box((w, 0.985, h + dz), ((x0 + x1) / 2, J(-0.006, 0.0), zc + dz / 2), m,
                             rot=(0, J(-0.006, 0.006), 0), bevel=0.028, segs=2))
    if cracked:
        dark = mat("crack", (0.12, 0.07, 0.035), 0.95)
        # hairline cracks zig-zagging across the face (dark slivers, barely proud)
        for pts in ([(-0.3, 0.42), (-0.18, 0.28), (-0.22, 0.12), (-0.08, -0.02), (-0.12, -0.2), (0.02, -0.34)],
                    [(0.18, 0.1), (0.3, -0.02), (0.26, -0.18)]):
            for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
                d = Vector((x1 - x0, 0, z1 - z0))
                a = math.atan2(d.z, d.x)
                parts.append(box((d.length + 0.01, 0.01, 0.008), ((x0 + x1) / 2, -0.4975, (z0 + z1) / 2), dark,
                                 rot=(0, -a, 0), bevel=0.0))
        parts.append(box((0.3, 0.012, 0.012), (0.05, -0.2, 0.4975), dark, rot=(0, 0, 0.5), bevel=0.0))
    simple(parts, name)


def stone():
    granite = mat("granite", (0.13, 0.13, 0.145), 0.7, coat=0.1)
    granite_d = mat("granite_dark", (0.07, 0.07, 0.08), 0.75)
    fleck = mat("granite_fleck", (0.35, 0.34, 0.33), 0.5)
    bronze = mat("stud_bronze", (0.7, 0.45, 0.2), 0.3, 0.9)
    parts = [box((0.985, 0.985, 0.985), (0, 0, 0), granite, bevel=0.06, segs=3),
             box((0.78, 0.02, 0.78), (0, -0.49, 0), granite_d, bevel=0.03, segs=2),
             box((0.64, 0.02, 0.64), (0, -0.5, 0), granite, bevel=0.03, segs=2),
             box((0.78, 0.78, 0.02), (0, 0, 0.49), granite_d, bevel=0.03, segs=2)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = (sx * 0.39, -0.505, sz * 0.39)
            parts.append(cyl(0.045, 0.03, p, bronze, rot=(R90, 0, 0), verts=12, bevel=0.012, segs=1))
            parts.append(sphere(0.028, (p[0], -0.515, p[2]), bronze, scale=(1, 0.6, 1), segs=10, rings=5))
    J = jitter(9)
    for i in range(7):
        parts.append(ico(0.012, (J(-0.3, 0.3), -0.51, J(-0.3, 0.3)), fleck, scale=(1.4, 0.4, 1), sub=1, smooth=0))
    simple(parts, "stone")


# ------------------------------------------------------------------ ladders, bar

RUNGS = (-0.375, -0.125, 0.125, 0.375)
LADDER_Y = 0.15


def ladder_parts(rail, rung, band, glowing=False):
    parts = []
    for x in (-0.22, 0.22):
        parts.append(box((0.055, 0.06, 1.0), (x, LADDER_Y, 0), rail, bevel=0.018, segs=2))
    for z in RUNGS:
        parts.append(cyl(0.024, 0.46, (0, LADDER_Y, z), rung, rot=(0, R90, 0), verts=10, bevel=0.0))
        for x in (-0.22, 0.22):
            parts.append(box((0.07, 0.075, 0.035), (x, LADDER_Y, z), band, bevel=0.01, segs=1))
    return parts


def ladder():
    wood = mat("ladder_wood", (0.3, 0.16, 0.07), 0.7, coat=0.1)
    rung = mat("ladder_rung", (0.38, 0.21, 0.09), 0.65)
    band = mat("ladder_iron", (0.22, 0.2, 0.19), 0.45, 0.7)
    simple(ladder_parts(wood, rung, band), "ladder")


def exit_ladder():
    gold = glow("exit_gold", (1.0, 0.7, 0.25), 2.5, base=(1.0, 0.78, 0.35), rough=0.25)
    gold_m = mat("exit_gold_metal", (1.0, 0.8, 0.4), 0.2, 1.0, emit=1.2, emit_color=(1.0, 0.65, 0.2))
    bright = glow("exit_bright", (1.0, 0.9, 0.6), 6.0)
    parts = ladder_parts(gold_m, gold, gold_m, True)
    for z in RUNGS:   # little sparks on the bindings
        parts.append(ico(0.018, (0.22, LADDER_Y - 0.05, z + 0.04), bright, sub=1, smooth=0))
        parts.append(ico(0.014, (-0.22, LADDER_Y - 0.05, z - 0.03), bright, sub=1, smooth=0))
    simple(parts, "exit_ladder")


def bar():
    """Three hemp strands twisted round each other along X; a whole number of twists per cell so it tiles."""
    hemp = mat("rope_hemp", (0.5, 0.36, 0.18), 0.9)
    hemp_d = mat("rope_hemp_dark", (0.36, 0.24, 0.11), 0.9)
    parts = []
    n = 24
    for k in range(3):
        pts, radii = [], []
        for i in range(n + 1):
            x = -0.5 + i / n
            a = 2 * math.pi * (2 * (x + 0.5) + k / 3)
            pts.append((x, 0.022 * math.cos(a), 0.4 + 0.022 * math.sin(a)))
            radii.append(0.025)
        parts.append(tube(pts, radii, hemp if k else hemp_d, verts=6, caps=False))
    simple(parts, "bar")


# ------------------------------------------------------------------ gold, rubble

def gold():
    au = mat("gold", (1.0, 0.74, 0.3), 0.22, 1.0, emit=0.35, emit_color=(1.0, 0.6, 0.15))
    au2 = mat("gold_pale", (1.0, 0.84, 0.46), 0.18, 1.0, emit=0.35, emit_color=(1.0, 0.7, 0.25))
    glint = glow("gold_glint", (1.0, 0.92, 0.7), 8.0)
    ingot = [(-0.16, -0.075), (0.16, -0.075), (0.12, 0.075), (-0.12, 0.075)]   # a trapezoid section, x (along Y) z
    parts = []

    def bar_at(x, y, z, yaw, m):
        o = prism([(p[0], p[1]) for p in ingot], 0.15, (0, 0, 0), m, bevel=0.012, segs=1)
        # prism extrudes along Y; the section lies in XZ: an ingot 0.26 long, 0.13 wide, 0.13 tall
        o.rotation_euler = (0, 0, yaw)
        o.location = (x, y, z)
        return o
    parts.append(bar_at(-0.17, 0.0, FLOOR + 0.076, 0.08, au))
    parts.append(bar_at(0.17, 0.02, FLOOR + 0.076, -0.1, au2))
    parts.append(bar_at(0.0, 0.14, FLOOR + 0.076, R90 + 0.1, au))
    parts.append(bar_at(-0.06, 0.03, FLOOR + 0.226, 0.12, au2))
    parts.append(bar_at(0.1, 0.06, FLOOR + 0.226, -0.2, au))
    parts.append(bar_at(0.02, 0.05, FLOOR + 0.376, 0.02, au2))
    J = jitter(21)
    for i in range(7):
        a = J(0, 6.28)
        r = J(0.2, 0.3)
        parts.append(cyl(0.045, 0.014, (math.cos(a) * r, math.sin(a) * r * 0.6 - 0.05, FLOOR + 0.008 + (i % 2) * 0.012),
                         au2 if i % 2 else au, rot=(J(-0.2, 0.2), J(-0.2, 0.2), 0), verts=12, bevel=0.004, segs=1))
    for p in ((-0.04, -0.09, FLOOR + 0.42), (0.24, -0.08, FLOOR + 0.17), (-0.26, -0.09, FLOOR + 0.14)):
        for ax in ((0.07, 0.006, 0.006), (0.006, 0.006, 0.07)):
            parts.append(box(ax, p, glint, bevel=0.0))
    for o in parts:
        K.select(o)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    simple(parts, "gold")


def rubble():
    sand = [mat("sandstone_%d" % i, c, 0.82, coat=0.05) for i, c in enumerate(SAND)]
    dust = mat("rubble_dust", (0.4, 0.26, 0.14), 0.95)
    J = jitter(33)
    parts = [ico(0.42, (0, 0, FLOOR), dust, scale=(1.1, 1.0, 0.35), sub=2)]
    for i in range(9):
        x, y = J(-0.36, 0.36), J(-0.3, 0.3)
        r = J(0.08, 0.15)
        parts.append(ico(r, (x, y, FLOOR + r * 0.6 + J(0, 0.06)), sand[i % 4], scale=(J(1.0, 1.5), J(0.9, 1.3), J(0.6, 0.9)),
                         sub=1, rot=(J(0, 3), J(0, 3), J(0, 3)), smooth=0))
    simple(parts, "rubble")


# ------------------------------------------------------------------ back wall

def back_wall(v):
    """A carved panel behind the grid: front face at y = +0.5."""
    stone_m = mat("wall_stone", (0.2, 0.13, 0.08), 0.88)
    stone_l = mat("wall_stone_light", (0.26, 0.17, 0.1), 0.85)
    seam = mat("wall_seam", (0.07, 0.045, 0.03), 0.95)
    carve = mat("wall_carving", (0.14, 0.09, 0.05), 0.9)
    paint = mat("wall_paint", (0.07, 0.2, 0.21), 0.8)
    y0 = 0.5
    T = 0.12
    parts = [box((1.0, T, 1.0), (0, y0 + T / 2 + 0.01, 0), seam, bevel=0.0)]
    J = jitter(60 + v)
    if v == 0:   # dressed blocks, three courses in bond
        for r, zc in enumerate((-0.333, 0.0, 0.333)):
            xs = (-0.5, 0.0, 0.5) if r % 2 == 0 else (-0.5, -0.25, 0.25, 0.5)
            for x0, x1 in zip(xs, xs[1:]):
                m = stone_m if (r + int(x0 * 4)) % 2 else stone_l
                parts.append(box((x1 - x0 - 0.02, T, 0.313), ((x0 + x1) / 2, y0 + T / 2 + J(-0.008, 0.004), zc), m,
                                 bevel=0.02, segs=1))
    elif v == 1:   # a carved sun disc on one slab
        parts.append(box((0.98, T, 0.98), (0, y0 + T / 2, 0), stone_m, bevel=0.025, segs=1))
        parts.append(cyl(0.2, 0.03, (0, y0 - 0.005, 0.02), stone_l, rot=(R90, 0, 0), verts=24, bevel=0.012, segs=1))
        parts.append(cyl(0.09, 0.03, (0, y0 - 0.02, 0.02), carve, rot=(R90, 0, 0), verts=16, bevel=0.01, segs=1))
        for i in range(12):
            a = i * math.pi / 6
            d = Vector((math.cos(a), 0, math.sin(a)))
            parts.append(box((0.1, 0.02, 0.03), tuple(Vector((0, y0 - 0.004, 0.02)) + d * 0.29), stone_l,
                             rot=(0, -a, 0), bevel=0.008, segs=1))
        parts.append(box((0.9, 0.02, 0.04), (0, y0 - 0.004, -0.4), carve, bevel=0.01, segs=1))
    else:   # a glyph frieze with a faded teal band
        parts.append(box((0.98, T, 0.98), (0, y0 + T / 2, 0), stone_l, bevel=0.025, segs=1))
        parts.append(box((0.98, 0.02, 0.26), (0, y0 - 0.002, 0.08), paint, bevel=0.008, segs=1))
        for i in range(3):
            x = -0.3 + i * 0.3
            glyph = [(-0.07, -0.08), (0.07, -0.08), (0.07, 0.0), (0.02, 0.0), (0.02, 0.08), (-0.07, 0.08)]
            if i == 1:
                glyph = [(-0.08, -0.08), (0.08, -0.08), (0.0, 0.09)]
            if i == 2:
                glyph = [(-0.05, -0.08), (0.05, -0.08), (0.08, 0.0), (0.05, 0.08), (-0.05, 0.08), (-0.08, 0.0)]
            parts.append(prism(glyph, 0.02, (x, y0 - 0.012, 0.08), carve, bevel=0.005, segs=1))
        parts.append(box((0.98, 0.03, 0.03), (0, y0 - 0.006, -0.08), carve, bevel=0.01, segs=1))
        parts.append(box((0.98, 0.03, 0.03), (0, y0 - 0.006, 0.24), carve, bevel=0.01, segs=1))
        parts.append(box((0.98, 0.012, 0.012), (0, y0 - 0.001, -0.3), seam, bevel=0.0))
    simple(parts, "back_wall_%d" % v)


# ------------------------------------------------------------------ light sources

def lantern():
    iron = mat("lantern_iron", (0.16, 0.14, 0.13), 0.45, 0.8)
    brass = mat("brass", (0.86, 0.62, 0.28), 0.3, 0.9)
    glass = glow("lantern", (1.0, 0.68, 0.3), 5.0, base=(1.0, 0.8, 0.5), rough=0.15)
    parts = [cyl(0.1, 0.035, (0, 0, -0.16), iron, verts=8, bevel=0.01, segs=1),
             cyl(0.085, 0.24, (0, 0, -0.02), glass, verts=8, bevel=0.0),
             cyl(0.11, 0.06, (0, 0, 0.12), iron, r2=0.05, verts=8, bevel=0.01, segs=1),
             cyl(0.04, 0.04, (0, 0, 0.17), brass, verts=8, bevel=0.008, segs=1),
             torus(0.035, 0.009, (0, 0, 0.21), iron, rot=(R90, 0, 0), verts=12, minor=4)]
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        parts.append(box((0.016, 0.016, 0.26), (math.cos(a) * 0.088, math.sin(a) * 0.088, -0.02), iron, bevel=0.004, segs=1))
    for z in range(5):   # the chain to the top of the cell
        zc = 0.25 + z * 0.052
        parts.append(torus(0.018, 0.005, (0, 0, zc), iron, rot=(R90, 0, (z % 2) * R90), verts=8, minor=4, scale=(1, 1, 1.5)))
    simple(parts, "lantern")


def torch():
    iron = mat("torch_iron", (0.16, 0.14, 0.13), 0.45, 0.8)
    wood = mat("torch_wood", (0.3, 0.18, 0.09), 0.8)
    wrap = mat("torch_wrap", (0.35, 0.25, 0.15), 0.95)
    ember = glow("torch_ember", (1.0, 0.35, 0.08), 3.0, base=(0.3, 0.1, 0.05))
    core = glow("flame_core", (1.0, 0.85, 0.45), 9.0)
    outer = glow("flame_outer", (1.0, 0.45, 0.1), 6.0)
    # the bracket on the back wall, the torch leaning out toward the camera
    parts = [box((0.14, 0.03, 0.2), (0, 0.49, 0.0), iron, bevel=0.01, segs=1),
             rod((0, 0.48, -0.02), (0, 0.33, -0.02), 0.018, iron, verts=8),
             torus(0.045, 0.012, (0, 0.3, -0.02), iron, verts=12, minor=4)]
    tilt = Vector((0, -0.35, 1)).normalized()
    base = Vector((0, 0.35, -0.2))
    top = base + tilt * 0.36
    parts.append(rod(base, top, 0.028, wood, r2=0.036, verts=10))
    parts.append(rod(top - tilt * 0.08, top + tilt * 0.01, 0.045, wrap, verts=10))
    parts.append(ico(0.04, top + tilt * 0.01, ember, scale=(1, 1, 0.5), sub=1))
    root = join(parts, "torch")
    fl = [ico(0.06, top + tilt * 0.07, outer, scale=(1, 1, 1.5), sub=2),
          rod(top + tilt * 0.1, top + tilt * 0.26 + Vector((0.01, 0, 0)), 0.05, outer, r2=0.0, verts=10),
          ico(0.035, top + tilt * 0.07, core, scale=(1, 1, 1.6), sub=2),
          rod(top + tilt * 0.08, top + Vector((0, -0.02, 0.2)), 0.03, core, r2=0.0, verts=8)]
    flame = join(fl, "flame", pivot=tuple(top + tilt * 0.02))
    export(root, "torch", [(flame, root)])


# ------------------------------------------------------------------ framing decor

def pillar():
    st = mat("pillar_stone", (0.36, 0.24, 0.13), 0.8, coat=0.05)
    st_d = mat("pillar_stone_dark", (0.22, 0.14, 0.08), 0.85)
    bronze = mat("stud_bronze", (0.7, 0.45, 0.2), 0.3, 0.9)
    nodes = []
    # shaft: a fluted drum, tiles vertically
    parts = [cyl(0.3, 1.0, (0, 0, 0), st, verts=16)]
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 16
        parts.append(box((0.05, 0.03, 0.98), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0), st_d, rot=(0, 0, a + R90), bevel=0.01, segs=1))
    parts.append(torus(0.305, 0.02, (0, 0, 0.47), st_d, verts=16, minor=4))
    nodes.append(join(parts, "pillar_shaft"))
    parts = [box((0.9, 0.9, 0.2), (0, 0, -0.4), st_d, bevel=0.04, segs=2),
             box((0.78, 0.78, 0.16), (0, 0, -0.22), st, bevel=0.04, segs=2),
             cyl(0.36, 0.14, (0, 0, -0.08), st, r2=0.31, verts=16, bevel=0.03, segs=1),
             cyl(0.3, 0.44, (0, 0, 0.28), st, verts=16)]
    for sx in (-1, 1):
        parts.append(cyl(0.03, 0.02, (sx * 0.3, -0.45, -0.4), bronze, rot=(R90, 0, 0), verts=10, bevel=0.006))
    nodes.append(join(parts, "pillar_base"))
    parts = [cyl(0.3, 0.44, (0, 0, -0.28), st, verts=16),
             cyl(0.31, 0.14, (0, 0, 0.0), st, r2=0.4, verts=16, bevel=0.03, segs=1),
             box((0.9, 0.9, 0.16), (0, 0, 0.15), st, bevel=0.04, segs=2),
             box((1.0, 1.0, 0.18), (0, 0, 0.39), st_d, bevel=0.04, segs=2),
             box((0.5, 0.02, 0.08), (0, -0.451, 0.15), bronze, bevel=0.01, segs=1)]
    nodes.append(join(parts, "pillar_capital"))
    export(nodes, "pillar")


def arch():
    """Three cells wide, about 2.6 tall: two piers and a round arch of voussoirs with a keystone."""
    st = mat("pillar_stone", (0.36, 0.24, 0.13), 0.8, coat=0.05)
    st_d = mat("pillar_stone_dark", (0.22, 0.14, 0.08), 0.85)
    key = mat("arch_key", (0.45, 0.3, 0.16), 0.75, coat=0.05)
    bronze = mat("stud_bronze", (0.7, 0.45, 0.2), 0.3, 0.9)
    parts = []
    for sx in (-1, 1):
        parts.append(box((0.5, 0.6, 1.0), (sx * 1.25, 0, 0.0), st, bevel=0.03, segs=1))
        parts.append(box((0.6, 0.66, 0.14), (sx * 1.25, 0, -0.43), st_d, bevel=0.03, segs=1))
        parts.append(box((0.6, 0.66, 0.1), (sx * 1.25, 0, 0.52), st_d, bevel=0.03, segs=1))
    c = Vector((0, 0, 0.57))
    R0, R1 = 1.0, 1.5
    n = 9
    for i in range(n):
        a0 = math.pi * i / n + 0.012
        a1 = math.pi * (i + 1) / n - 0.012
        poly = [(math.cos(a0) * R0, math.sin(a0) * R0), (math.cos(a0) * R1, math.sin(a0) * R1),
                (math.cos(a1) * R1, math.sin(a1) * R1), (math.cos(a1) * R0, math.sin(a1) * R0)]
        poly = poly[::-1]
        m = key if i == n // 2 else (st if i % 2 else st_d)
        depth = 0.66 if i == n // 2 else 0.6
        parts.append(prism(poly, depth, (c.x, 0, c.z), m, bevel=0.02, segs=1))
    parts.append(cyl(0.06, 0.03, (0, -0.34, c.z + 1.25), bronze, rot=(R90, 0, 0), verts=12, bevel=0.008))
    simple(parts, "arch")


def mine_cart():
    iron = mat("cart_iron", (0.2, 0.18, 0.17), 0.45, 0.8)
    rust = mat("cart_rust", (0.3, 0.11, 0.045), 0.7, 0.4)
    wood = mat("cart_wood", (0.27, 0.15, 0.06), 0.75)
    ore = mat("cart_ore", (0.12, 0.1, 0.09), 0.9)
    au = mat("gold", (1.0, 0.74, 0.3), 0.22, 1.0, emit=0.35, emit_color=(1.0, 0.6, 0.15))
    rail = mat("rail_steel", (0.4, 0.4, 0.42), 0.35, 0.9)
    z0 = FLOOR
    parts = []
    for y in (-0.16, 0.16):   # a short stretch of track
        parts.append(box((1.0, 0.035, 0.04), (0, y, z0 + 0.06), rail, bevel=0.008, segs=1))
    for x in (-0.33, 0.0, 0.33):
        parts.append(box((0.1, 0.5, 0.04), (x, 0, z0 + 0.02), wood, bevel=0.01, segs=1))
    body = [(-0.36, 0.0), (0.36, 0.0), (0.42, 0.34), (-0.42, 0.34)]
    parts.append(prism(body, 0.44, (0, 0, z0 + 0.14), rust, bevel=0.02, segs=1))
    for x in (-0.39, 0.39):
        parts.append(box((0.03, 0.46, 0.36), (x * 0.96, 0, z0 + 0.31), iron, rot=(0, math.copysign(0.17, x), 0), bevel=0.008, segs=1))
    parts.append(box((0.86, 0.47, 0.035), (0, 0, z0 + 0.48), iron, bevel=0.01, segs=1))
    for x in (-0.24, 0.24):
        parts.append(cyl(0.08, 0.03, (x, -0.2, z0 + 0.12), iron, rot=(R90, 0, 0), verts=14, bevel=0.008, segs=1))
        parts.append(cyl(0.08, 0.03, (x, 0.2, z0 + 0.12), iron, rot=(R90, 0, 0), verts=14, bevel=0.008, segs=1))
    parts.append(ico(0.3, (0, 0, z0 + 0.46), ore, scale=(1.25, 0.65, 0.35), sub=2, smooth=0))
    for p in ((-0.12, -0.08, z0 + 0.53), (0.12, 0.02, z0 + 0.54), (0.02, -0.12, z0 + 0.55)):
        parts.append(ico(0.045, p, au, sub=1, smooth=0))
    simple(parts, "mine_cart")


def crate():
    wood = mat("crate_wood", (0.36, 0.2, 0.08), 0.75)
    plank = mat("crate_plank", (0.27, 0.15, 0.06), 0.8)
    iron = mat("crate_iron", (0.2, 0.18, 0.17), 0.45, 0.8)
    s = 0.62
    zc = FLOOR + s / 2
    parts = [box((s, s, s), (0, 0.05, zc), wood, bevel=0.03, segs=2)]
    for y in (-s / 2 + 0.05 - 0.005, s / 2 + 0.05 + 0.005):
        for z in (-0.22, 0.22):
            parts.append(box((s, 0.03, 0.07), (0, y, zc + z), plank, bevel=0.01, segs=1))
        parts.append(box((0.75 * s * 1.41, 0.025, 0.07), (0, y, zc), plank, rot=(0, math.pi / 4, 0), bevel=0.01, segs=1))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(box((0.08, 0.04, 0.08), (sx * (s / 2 - 0.02), -s / 2 + 0.03, zc + sz * (s / 2 - 0.02)), iron,
                             bevel=0.01, segs=1))
    simple(parts, "crate")


def build_all(only):
    jobs = {"brick_0": lambda: brick_block("brick_0", 0), "brick_1": lambda: brick_block("brick_1", 1),
            "trap_brick": lambda: brick_block("trap_brick", 0, True), "stone": stone, "ladder": ladder,
            "exit_ladder": exit_ladder, "bar": bar, "gold": gold, "rubble": rubble, "lantern": lantern, "torch": torch,
            "pillar": pillar, "arch": arch, "mine_cart": mine_cart, "crate": crate}
    for v in range(3):
        jobs["back_wall_%d" % v] = (lambda v_: lambda: back_wall(v_))(v)
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
