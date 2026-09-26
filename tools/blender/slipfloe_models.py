"""Slipfloe (game 17) models: the sea otter hero, the frost mite, the ice blocks (plain, with an egg, the gem block),
the break shard, the arena wall and floor, and the snowfield dressing.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/slipfloe_models.py -- godot/games/slipfloe/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, ico, torus, rod, tube, join, export), the rig from
blastyard_bombers.py (merge, mirror, limb) and hopline_models.py (TurnRig, ell, hemi), mossfolk_models.py (lumpy,
lathe_r), nightbite_characters.py (blob).

Axes. One grid cell = 1 unit. Blender Z up; the characters are written facing Blender -Y and exported turned to face
Blender +Y, which is Godot -Z (away from the camera, which sits at +Z looking down about 60 degrees). Godot +X stays
+X. Origins sit at the base centre (the floor top is Godot y = 0).

otter.glb       armature "otter_rig", skinned mesh "otter", facing Godot -Z, 0.75 tall (crown), 0.5 wide, nose at
                z = -0.28, the flat tail reaching z = +0.45 behind. Materials: otter_fur (brown body, arms, tail),
                otter_face (the pale sea-otter head), otter_muzzle, otter_belly, otter_paw (paws and feet), otter_nose,
                otter_eye, otter_shine (emissive catchlights), otter_whisker, otter_cheek, otter_ear_in, otter_scarf
                (red: RECOLOUR it for player 2), otter_scarf_stripe (cream stripes and fringe), otter_star (dizzy stars,
                emissive). Rest pose: paws held together in front of the chest.
                Animations (30 fps): idle (loop 2 s: breathing, a look around, a blink, the scarf tail sways),
                walk (loop 0.5 s: a waddle of two steps; no travel, the game moves the node),
                push (one-shot 0.3 s: wind-up, both paws shove forward at 0.13 s, recover),
                kick_wall (one-shot 0.4 s: a little hop and a hip-bump stomp, lands at 0.2 s: shake the wall then),
                die (one-shot 1.2 s: squashed flat at 0.1 s, springs back up dizzy with stars circling his head,
                wobbles; holds the last frame), cheer (loop 1 s: hops with both paws up, a wiggle).
                The dizzy stars are scaled to nothing except in die.
mite.glb        armature "mite_rig", skinned mesh "mite", facing Godot -Z, 0.6 tall (antenna bulbs), the fuzzy body
                0.5 across (0.57 with the tufts), 0.46 tall.
                Materials: mite_body (the fuzz: pale frost blue, RECOLOUR per level), mite_belly, mite_glow (antenna
                bulbs and the heart spot, emissive), mite_eye, mite_pupil, mite_shine, mite_tooth, mite_mouth,
                mite_foot, mite_star (emissive), mite_egg (the egg shell, only in hatch).
                Animations (30 fps): walk (loop 0.5 s: a bouncy scuttle), chew (loop 0.5 s: leaning forward, gnawing
                with the buck teeth), stunned (loop 1 s: wobbling, eyes shut, stars circling), squash (one-shot
                0.5 s: flattened to a pancake, holds), hatch (one-shot 0.8 s: the egg shell rocks, its top pops off
                at 0.33 s, the mite springs out, the shell shrinks away by 0.8 s). The egg and the stars are scaled to
                nothing outside their actions.
ice_block.glb   one node "ice_block": 0.96 x 0.96 footprint, 0.9 tall, bevelled. Materials: ice (the translucent
                shell, alpha-blended, a little emissive so it reads at night; tint it to flash a block), ice_core (the
                cloudy opaque heart), ice_crack (emissive crack lines under the surface), ice_frost (the frosted top
                panel: the top reads brighter than the sides from above), ice_shine (two emissive streaks on the top),
                ice_bubble (tiny trapped bubbles). Only the shell is transparent, so the block sorts as one object.
ice_block_egg   node "ice_block_egg": the same block with a mite egg frozen inside instead of the cloudy heart
                (ice_egg: pale lilac, faint spots ice_egg_spot). The game can pulse the "ice_egg" emission to reveal it.
gem_block.glb   node "gem_block": the same shell tinted violet (gem_ice; gem_crack, gem_bubble) with a clear top, round a
                big brilliant-cut gem seen through it (gem: emissive rose, gem_facet: the lighter crown facets), gold
                studs on the eight corners (gem_gold, a little emissive).
ice_shard.glb   node "ice_shard": a 0.2 splinter (material ice_shard, alpha-blended), origin at its centre.
wall_segment    node "wall_segment": the arena border, 1 long along X (x -0.5..0.5), three courses of ice bricks 0.54
                tall under snow drifts (0.6 at the drifts), 0.5 thick: the inner face (towards the play field) is at
                Godot local z = +0.25, the outer at z = -0.25. Rotation about Godot Y: the far (top, -Z) edge takes it
                unrotated, the near (bottom) edge PI, the left edge +PI/2, the right edge -PI/2. Place its origin 0.75
                outside the last cell centre (the play-field edge is 0.5 from that centre, the inner face sits on it).
                Segments butt end to end (the brick courses and joints continue). Shake it (it is one node).
                Materials: wall_ice (bricks), wall_mortar (the joints), wall_snow (drifts and drips), wall_glow (two
                small emissive crystals frozen into the inner face).
wall_corner     node "wall_corner": a 0.5 x 0.5 brick post (x, z -0.25..0.25), 0.6 tall with a glowing crystal finial
                (to 0.88); put it at the arena corners (+-(W/2 + 0.25), +-(H/2 + 0.25)) from the field centre.
floor_tile_a/b/c one node each, 1 x 1, top at y = 0, slab down to y = -0.12: packed snow (a: plain with sparkles,
                b: a glossy ice patch, c: a few cracks and pebbles). Materials floor_snow, floor_snow_dark (the
                bevel, darker so the grid reads), floor_ice, floor_sparkle (emissive), floor_crack, floor_pebble.
Dressing (one node each, origin at the base centre, the front faces the camera, Godot +Z):
                igloo (dome 1.5 across, 0.95 tall, 1.9 with its drifts; the porch and its glowing doorway reach
                z = +1.1 towards the camera; igloo_glow: the warm light in the door and a side window), pine_snowy (2.0
                tall, 1.45 across), snowman (1.24 tall to the bobble, stick arms 1.04 across, knitted scarf and hat),
                ice_rock (0.58 tall, a glowing crystal among ice spikes, ice_rock_glow), lantern_ice (1.23 tall: a post,
                the lantern hanging at x = +0.22, 0.9 high, lantern_ice_glow). All opaque except lantern_ice_glass.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, join, export, simple, reset, R90
from blastyard_bombers import merge, mirror, limb
from prism_models import new_obj
from nightbite_characters import blob
from mossfolk_models import lumpy, lathe_r
from hopline_models import TurnRig, ell, hemi

BH = 0.9     # block height
BS = 0.96    # block footprint


# ------------------------------------------------------------------ helpers

def tiny(objs, pivot, k=0.01):
    """Shrinks parts towards pivot: bone-carried props that stay invisible in the rest pose; an action shows them
    with the bone scaled by 1 / k."""
    P = Vector(pivot)
    for o in K.flatten(objs):
        o.data.transform(Matrix.Translation(P) @ Matrix.Scale(k, 4) @ Matrix.Translation(-P))
    return objs


def star(c, r, material, thick=0.02, face=(0, -1, 0)):
    """A chubby five-pointed star at c, facing `face`."""
    bm = bmesh.new()
    ring = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.48
        ring.append((rr * math.cos(a), rr * math.sin(a)))
    front = [bm.verts.new((x, -thick / 2, z)) for x, z in ring]
    back = [bm.verts.new((x, thick / 2, z)) for x, z in ring]
    cf = bm.verts.new((0, -thick * 1.2, 0))
    cb = bm.verts.new((0, thick * 1.2, 0))
    for i in range(10):
        j = (i + 1) % 10
        bm.faces.new((cf, front[j], front[i]))
        bm.faces.new((cb, back[i], back[j]))
        bm.faces.new((front[i], front[j], back[j], back[i]))
    o = new_obj("star", bm, material, smooth=0)
    q = Vector((0, -1, 0)).rotation_difference(Vector(face).normalized())
    o.data.transform(Matrix.Translation(Vector(c)) @ q.to_matrix().to_4x4())
    return o


def ribbon(points, widths, material, thick=0.012, up=(0, 0, 1), name="ribbon"):
    """A flat strip through points (a scarf end), width across `up` x tangent, solidified."""
    bm = bmesh.new()
    P = [Vector(p) for p in points]
    rows = []
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        side = t.cross(Vector(up)).normalized()
        rows.append((bm.verts.new(p - side * widths[i] / 2), bm.verts.new(p + side * widths[i] / 2)))
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    o = new_obj(name, bm, material, smooth=60)
    K.select(o)
    s = o.modifiers.new("s", "SOLIDIFY")
    s.thickness = thick
    s.offset = 0
    bpy.ops.object.modifier_apply(modifier=s.name)
    return o


def crack_line(pts, material, w=0.012, normal=(0, -1, 0)):
    """Thin flat quads along a polyline lying in a plane with the given normal (a crack under the ice)."""
    bm = bmesh.new()
    n = Vector(normal).normalized()
    P = [Vector(p) for p in pts]
    for a, b in zip(P, P[1:]):
        t = (b - a).normalized()
        s = t.cross(n).normalized() * w / 2
        vs = [bm.verts.new(v) for v in (a - s, a + s, b + s, b - s)]
        bm.faces.new(vs)
    return new_obj("crack", bm, material, smooth=0)


def zig(rnd, a, b, n, amp):
    """A jagged polyline from a to b with n kinks (random offsets up to amp, perpendicular-ish)."""
    a, b = Vector(a), Vector(b)
    out = [a]
    for k in range(1, n):
        t = k / n
        p = a.lerp(b, t) + Vector((rnd.uniform(-amp, amp), rnd.uniform(-amp, amp), rnd.uniform(-amp, amp)))
        out.append(p)
    out.append(b)
    return out


# ------------------------------------------------------------------ ice blocks

def ice_mats(pre="ice", tint=(0.18, 0.62, 1.0), glow=(0.1, 0.45, 1.0)):
    return dict(
        shell=mat(pre if pre == "ice" else pre + "_ice", tint, 0.04, coat=1.0, alpha=0.62, emit=0.55,
                  emit_color=glow),
        core=mat(pre + "_core", (0.45, 0.85, 1.0), 0.3, emit=0.5, emit_color=(0.3, 0.75, 1.0)),
        crack=mat(pre + "_crack", (0.9, 0.97, 1.0), 0.3, emit=1.2, emit_color=(0.75, 0.93, 1.0)),
        frost=mat(pre + "_frost", (0.62, 0.9, 1.0), 0.25, coat=1.0, emit=0.6, emit_color=(0.35, 0.75, 1.0)),
        shine=mat(pre + "_shine", (1.0, 1.0, 1.0), 0.2, emit=2.5),
        bubble=mat(pre + "_bubble", (0.95, 1.0, 1.0), 0.2, emit=0.8),
        snow=mat(pre + "_snow", (0.95, 0.97, 1.0), 0.7, emit=0.1, emit_color=(0.8, 0.9, 1.0)))


def block_shell(M, seed, core=True, cracks=True, panel=True):
    """The shared ice block: a bevelled translucent shell, frost on the top, cracks and bubbles inside."""
    rnd = random.Random(seed)
    parts = [box((BS, BS, BH), (0, 0, BH / 2), M["shell"], bevel=0.085, segs=3, smooth=40)]
    # the top: a frosted inset panel (brighter than the sides, so the block reads from above) with two shine
    # streaks, and a little snow drift in its back-left corner
    if panel:
        parts.append(box((BS - 0.2, BS - 0.2, 0.02), (0, 0, BH - 0.004), M["frost"], bevel=0.008, segs=2))
        for k, (off, ln, w) in enumerate(((0.0, 0.34, 0.045), (0.1, 0.16, 0.03))):
            o = box((ln, w, 0.006), (0, 0, 0), M["shine"], bevel=0.0)
            o.data.transform(Matrix.Translation((0.14 + off, -0.12 + off, BH + 0.008)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
            parts.append(o)
    if core:
        c = lumpy(1.0, (0, 0, 0), M["core"], seed + 3, amount=0.14, sub=3, smooth=70)
        c.data.transform(Matrix.Translation((0.0, 0.0, BH * 0.46)) @ Matrix.Diagonal((0.3, 0.3, 0.28, 1)))
        parts.append(c)
    if cracks:
        # cracks 0.02 under the front (-Y) and top faces, and one down the right side
        h = BS / 2 - 0.022
        parts.append(crack_line(zig(rnd, (-0.36, -h, 0.72), (0.1, -h, 0.38), 5, 0.04), M["crack"], 0.014, (0, -1, 0)))
        parts.append(crack_line(zig(rnd, (-0.08, -h, 0.54), (-0.3, -h, 0.2), 3, 0.03), M["crack"], 0.01, (0, -1, 0)))
        parts.append(crack_line(zig(rnd, (0.2, -h, 0.8), (0.36, -h, 0.58), 3, 0.02), M["crack"], 0.009, (0, -1, 0)))
        parts.append(crack_line(zig(rnd, (h, -0.35, 0.7), (h, 0.25, 0.3), 5, 0.04), M["crack"], 0.012, (1, 0, 0)))
        top = BH - 0.025
        parts.append(crack_line(zig(rnd, (-0.38, 0.3, top), (-0.05, -0.2, top), 4, 0.04), M["crack"], 0.012,
                                (0, 0, 1)))
        parts.append(crack_line(zig(rnd, (0.36, -0.36, top), (0.15, -0.1, top), 3, 0.03), M["crack"], 0.009,
                                (0, 0, 1)))
    for k in range(9):
        p = (rnd.uniform(-0.36, 0.36), rnd.uniform(-0.38, 0.0), rnd.uniform(0.12, 0.8))
        parts.append(sphere(rnd.uniform(0.01, 0.022), p, M["bubble"], segs=6, rings=4))
    return parts


def ice_block():
    simple(block_shell(ice_mats(), 17), "ice_block")


def ice_block_egg():
    M = ice_mats()
    parts = block_shell(M, 23, core=False)
    egg = mat("ice_egg", (0.78, 0.74, 0.98), 0.35, emit=0.3, emit_color=(0.6, 0.5, 1.0))
    spot = mat("ice_egg_spot", (0.5, 0.45, 0.85), 0.4, emit=0.2, emit_color=(0.5, 0.4, 1.0))
    parts.append(egg_shape((0, 0.02, 0.2), 0.2, 0.29, egg, tilt=12))
    rnd = random.Random(5)
    for k in range(6):
        a = rnd.uniform(-2.2, -0.9)
        z = rnd.uniform(0.3, 0.6)
        rr = 0.2 * egg_prof((z - 0.2) / 0.29) * 0.985
        parts.append(blob(0.028, (math.cos(a) * rr, 0.02 + math.sin(a) * rr, z), spot, (1.0, 0.3, 1.2),
                          (math.cos(a), math.sin(a), 0), segs=8, rings=5))
    simple(parts, "ice_block_egg")


def egg_prof(t):
    """Egg radius factor at height t (0 at the bottom, 1 at the top)."""
    t = min(max(t, 0.0), 1.0)
    return math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)) * (1.0 - 0.18 * t)


def egg_shape(base, r, h, material, tilt=0.0, segs=20, rings=14):
    """An egg standing on `base`, radius r, height h, pointier at the top."""
    prof = [(0.0, h)] + [(r * egg_prof(1 - k / rings), h * (1 - k / rings)) for k in range(1, rings)] + [(0.0, 0.0)]
    o = lathe_r(prof, material, segs=segs, smooth=80)
    o.data.transform(Matrix.Translation(Vector(base)) @ Matrix.Rotation(math.radians(tilt), 4, "Y"))
    return o


def gem_block():
    M = ice_mats("gem", (0.55, 0.45, 1.0), (0.45, 0.25, 1.0))
    parts = block_shell(M, 31, core=False, panel=False)
    gem = mat("gem", (1.0, 0.15, 0.4), 0.1, coat=1.0, emit=2.2, emit_color=(0.9, 0.08, 0.32))
    facet = mat("gem_facet", (1.0, 0.55, 0.7), 0.05, coat=1.0, emit=5.0, emit_color=(1.0, 0.45, 0.62))
    gold = mat("gem_gold", (1.0, 0.72, 0.25), 0.3, metal=0.4, emit=0.6, emit_color=(1.0, 0.65, 0.2))
    # a brilliant cut: table on top, crown, girdle, pavilion down to a point; stood facing the camera a bit
    n = 8
    R, zc = 0.33, 0.52
    bm = bmesh.new()
    table = [bm.verts.new((0.55 * R * math.cos(2 * math.pi * (k + 0.5) / n), 0.55 * R * math.sin(2 * math.pi * (k + 0.5) / n), zc + 0.13)) for k in range(n)]
    gird = [bm.verts.new((R * math.cos(2 * math.pi * k / n), R * math.sin(2 * math.pi * k / n), zc)) for k in range(n)]
    tip = bm.verts.new((0, 0, zc - 0.3))
    bm.faces.new(table)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((gird[k], gird[j], table[k]))
        bm.faces.new((table[k], table[(k - 1) % n], gird[k]))
        bm.faces.new((gird[j], gird[k], tip))
    g = new_obj("gem", bm, gem, smooth=0)
    # the crown facets in the lighter material
    for p in g.data.polygons:
        if p.normal.z > 0.2:
            p.material_index = 1
    g.data.materials.append(facet)
    g.data.transform(Matrix.Translation((0, 0, zc)) @ Matrix.Rotation(math.radians(-12), 4, "X")
                     @ Matrix.Translation((0, 0, -zc)))
    g.data.transform(Matrix.Translation((0, 0, -0.04)))
    parts.append(g)
    # gold studs on the four top corners and the four bottom corners' fronts
    for x in (-1, 1):
        for y in (-1, 1):
            parts.append(ico(0.045, (x * 0.44, y * 0.44, BH - 0.02), gold, sub=1, smooth=0))
            parts.append(ico(0.04, (x * 0.44, y * 0.44, 0.06), gold, sub=1, smooth=0))
    simple(parts, "gem_block")


def ice_shard():
    m = mat("ice_shard", (0.6, 0.88, 1.0), 0.05, coat=1.0, alpha=0.7, emit=0.6, emit_color=(0.4, 0.75, 1.0))
    bm = bmesh.new()
    rnd = random.Random(3)
    pts = [(0, 0, 0.1), (0, 0, -0.1)]
    ring = []
    for k in range(5):
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.3, 0.3)
        ring.append(bm.verts.new((math.cos(a) * rnd.uniform(0.035, 0.055), math.sin(a) * rnd.uniform(0.03, 0.05),
                                  rnd.uniform(-0.03, 0.02))))
    top = bm.verts.new((0.02, 0.01, 0.1))
    bot = bm.verts.new((-0.01, 0.0, -0.07))
    for k in range(5):
        j = (k + 1) % 5
        bm.faces.new((ring[k], ring[j], top))
        bm.faces.new((ring[j], ring[k], bot))
    simple([new_obj("ice_shard", bm, m, smooth=0)], "ice_shard")


# ------------------------------------------------------------------ arena wall and floor

def wall_mats():
    return dict(ice=mat("wall_ice", (0.16, 0.36, 0.72), 0.2, coat=0.8, emit=0.12, emit_color=(0.2, 0.45, 1.0)),
                mortar=mat("wall_mortar", (0.7, 0.8, 0.95), 0.8),
                snow=mat("wall_snow", (0.95, 0.97, 1.0), 0.7, emit=0.2, emit_color=(0.75, 0.88, 1.0)),
                glow=mat("wall_glow", (0.4, 0.9, 1.0), 0.2, emit=4.0))


def bricks(x0, x1, y0, y1, z0, z1, M, rows, seed, stagger=0.0, blen=0.34):
    """Rows of rounded ice bricks filling the slab x0..x1 (along X), y0..y1 thick, z0..z1, over a mortar core."""
    rnd = random.Random(seed)
    parts = [box((x1 - x0 - 0.02, y1 - y0 - 0.04, z1 - z0 - 0.01), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                 M["mortar"], bevel=0.01)]
    hr = (z1 - z0) / rows
    for r in range(rows):
        off = (stagger + (0.5 if r % 2 else 0.0)) * blen
        x = x0 - off
        while x < x1 - 0.02:
            a, b = max(x, x0), min(x + blen, x1)
            if b - a > 0.06:
                d = rnd.uniform(-0.006, 0.006)
                parts.append(box((b - a - 0.026, y1 - y0 + d, hr - 0.026),
                                 ((a + b) / 2, (y0 + y1) / 2 + rnd.uniform(-0.004, 0.004), z0 + hr * (r + 0.5)),
                                 M["ice"], bevel=0.03, segs=2, smooth=40))
            x += blen
    return parts


def snow_cap(x0, x1, y0, y1, z, M, seed, drips=True):
    """A soft snow cap over a wall top, with a few drips down the faces."""
    rnd = random.Random(seed)
    L, W = x1 - x0, y1 - y0
    parts = []
    n = max(2, int(L / 0.2))
    m = max(2, int(L / 0.3))
    for k in range(m):    # irregular drifts of different sizes, not a row of pillows
        o = lumpy(1.0, (0, 0, 0), M["snow"], seed + 40 + k, amount=0.12, sub=2, smooth=70)
        x = x0 + L * (k + 0.5) / m + rnd.uniform(-0.08, 0.08)
        sx = min(rnd.uniform(0.1, 0.22), L * 0.4)
        o.data.transform(Matrix.Translation((x, (y0 + y1) / 2 + rnd.uniform(-0.06, 0.06), z))
                         @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, "Z")
                         @ Matrix.Diagonal((sx, W * rnd.uniform(0.2, 0.36), rnd.uniform(0.03, 0.05), 1)))
        parts.append(o)
    for k in range(n):
        x = x0 + L * (k + 0.5) / n + rnd.uniform(-0.04, 0.04)
        if drips and rnd.random() < 0.55:
            y = y0 + 0.01 if rnd.random() < 0.6 else y1 - 0.01
            parts.append(ell((x + rnd.uniform(-0.05, 0.05), y, z - 0.005), (0.045, 0.022, 0.04), M["snow"], segs=10,
                             rings=6))
    return parts


def wall_segment():
    M = wall_mats()
    parts = bricks(-0.5, 0.5, -0.25, 0.25, 0.0, 0.54, M, 3, 4)
    parts += snow_cap(-0.5, 0.5, -0.25, 0.25, 0.54, M, 9)
    # two small glowing crystals frozen into the inner face (Godot +Z side)
    for x, z in ((-0.3, 0.3), (0.22, 0.12)):
        parts.append(ico(0.03, (x, -0.255, z), M["glow"], sub=1, smooth=0, scale=(1.0, 0.6, 1.3)))
    simple(parts, "wall_segment")


def wall_corner():
    M = wall_mats()
    parts = bricks(-0.25, 0.25, -0.25, 0.25, 0.0, 0.6, M, 3, 6, blen=0.5)
    # side faces: rotate a second brick skin by 90 degrees so every face shows bricks
    side = bricks(-0.25, 0.25, -0.25, 0.25, 0.0, 0.6, M, 3, 7, stagger=0.25, blen=0.5)
    for o in side:
        o.data.transform(Matrix.Rotation(R90, 4, "Z"))
    parts += side
    parts += snow_cap(-0.26, 0.26, -0.26, 0.26, 0.6, M, 11, drips=False)
    # a crystal finial
    parts.append(ico(0.09, (0, 0, 0.75), M["glow"], sub=1, smooth=0, scale=(0.75, 0.75, 1.5)))
    for a in range(3):
        ang = a * 2 * math.pi / 3 + 0.4
        parts.append(ico(0.045, (0.06 * math.cos(ang), 0.06 * math.sin(ang), 0.7), M["glow"], sub=1, smooth=0,
                         scale=(0.7, 0.7, 1.4)))
    simple(parts, "wall_corner")


def floor_mats():
    return dict(snow=mat("floor_snow", (0.5, 0.6, 0.82), 0.85),
                dark=mat("floor_snow_dark", (0.2, 0.26, 0.48), 0.8),
                ice=mat("floor_ice", (0.3, 0.55, 0.85), 0.05, coat=1.0, emit=0.12, emit_color=(0.3, 0.6, 1.0)),
                sparkle=mat("floor_sparkle", (0.9, 0.97, 1.0), 0.2, emit=3.0),
                crack=mat("floor_crack", (0.45, 0.58, 0.8), 0.6),
                pebble=mat("floor_pebble", (0.35, 0.38, 0.48), 0.7))


def floor_base(M, seed):
    """The slab: a darker bevelled base with a slightly smaller, gently lumpy snow top."""
    rnd = random.Random(seed)
    parts = [box((1.0, 1.0, 0.1), (0, 0, -0.07), M["dark"], bevel=0.02)]
    top = box((0.95, 0.95, 0.045), (0, 0, -0.0225), M["snow"], bevel=0.018, segs=2)
    parts.append(top)
    return parts, rnd


def sparkles(parts, M, rnd, n):
    for k in range(n):
        p = (rnd.uniform(-0.43, 0.43), rnd.uniform(-0.43, 0.43), 0.004)
        parts.append(ico(0.009, p, M["sparkle"], sub=1, smooth=0, scale=(1, 1, 0.5)))


def floor_tile_a():
    M = floor_mats()
    parts, rnd = floor_base(M, 1)
    sparkles(parts, M, rnd, 7)
    simple(parts, "floor_tile_a")


def floor_tile_b():
    M = floor_mats()
    parts, rnd = floor_base(M, 2)
    ice = lumpy(1.0, (0, 0, 0), M["ice"], 77, amount=0.06, sub=3, smooth=60)
    ice.data.transform(Matrix.Translation((0.08, 0.05, -0.004)) @ Matrix.Diagonal((0.3, 0.24, 0.012, 1)))
    parts.append(ice)
    ice2 = lumpy(1.0, (0, 0, 0), M["ice"], 78, amount=0.06, sub=2, smooth=60)
    ice2.data.transform(Matrix.Translation((-0.28, -0.25, -0.004)) @ Matrix.Diagonal((0.1, 0.08, 0.01, 1)))
    parts.append(ice2)
    sparkles(parts, M, rnd, 4)
    simple(parts, "floor_tile_b")


def floor_tile_c():
    M = floor_mats()
    parts, rnd = floor_base(M, 3)
    for k in range(2):
        a = (rnd.uniform(-0.4, 0.0), rnd.uniform(-0.35, 0.35), 0.003)
        b = (a[0] + rnd.uniform(0.3, 0.45), a[1] + rnd.uniform(-0.2, 0.2), 0.003)
        parts.append(crack_line(zig(rnd, a, b, 4, 0.04), M["crack"], 0.012, (0, 0, 1)))
    for k in range(3):
        p = (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0.0)
        parts.append(lumpy(0.025, p, M["pebble"], 300 + k, amount=0.2, scale=(1.2, 1.0, 0.55), sub=1))
    sparkles(parts, M, rnd, 3)
    simple(parts, "floor_tile_c")



# ------------------------------------------------------------------ the otter (written facing -Y)

OH = Vector((0, -0.02, 0.6))        # head centre
OHR = (0.205, 0.175, 0.15)
OB = Vector((0, 0.01, 0.28))        # body centre
OBR = (0.22, 0.2, 0.26)
SHOULDER = (0.185, -0.04, 0.42)
PAW = (0.1, -0.215, 0.3)
HIP = (0.1, 0.0, 0.14)
ANKLE = (0.11, -0.02, 0.05)
TOE = (0.11, -0.14, 0.03)
STARS = Vector((0, -0.02, 0.87))


def knit_ring(c, R, r, scale, M, stripes, n=40, m=10, rib=24):
    """A knitted collar: a torus (major R, minor r) with ribs across it; faces in `stripes(angle)` take M[1]."""
    bm = bmesh.new()
    rings = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        ring = []
        for j in range(m):
            b = 2 * math.pi * j / m
            rr = r * (1 + 0.09 * math.cos(rib * a) ** 2)
            p = d * (R + rr * math.cos(b)) + Vector((0, 0, rr * math.sin(b)))
            ring.append(bm.verts.new(Vector((p.x * scale[0], p.y * scale[1], p.z * scale[2])) + Vector(c)))
        rings.append(ring)
    for i in range(n):
        for j in range(m):
            f = bm.faces.new((rings[i][j], rings[(i + 1) % n][j], rings[(i + 1) % n][(j + 1) % m],
                              rings[i][(j + 1) % m]))
            f.material_index = 1 if stripes(2 * math.pi * (i + 0.5) / n) else 0
    o = new_obj("knit", bm, M[0], smooth=70)
    o.data.materials.append(M[1])
    return o


def scarf_tail(points, width, M, n_stripes=2, fringe=True):
    """A hanging scarf end: a ribbon with cross stripes near the end and a fringe."""
    from blastyard_bombers import smooth_path
    P = smooth_path(points, 4)
    parts = [ribbon(P, [width] * len(P), M[0], thick=0.022)]
    L = len(P)
    for k in range(n_stripes):
        i = L - 3 - 3 * k
        a, b = P[i], P[i + 1]
        parts.append(ribbon([a + (b - a) * 0.15, a + (b - a) * 0.75], [width * 1.02] * 2, M[1], thick=0.028))
    if fringe:
        end, t = P[-1], (P[-1] - P[-2]).normalized()
        side = t.cross(Vector((0, 0, 1))).normalized()
        if side.length < 0.5:
            side = Vector((1, 0, 0))
        for k in range(4):
            q = end + side * (width * (-0.36 + 0.24 * k))
            parts.append(tube([q - t * 0.01, q + t * 0.045], [0.009, 0.007], M[1], verts=5))
    return parts


def otter():
    fur = mat("otter_fur", (0.36, 0.2, 0.1), 0.85)
    face = mat("otter_face", (1.0, 0.8, 0.55), 0.75)
    muzzle = mat("otter_muzzle", (1.0, 0.96, 0.88), 0.75)
    belly = mat("otter_belly", (0.62, 0.43, 0.27), 0.75)
    paw_m = mat("otter_paw", (0.2, 0.12, 0.07), 0.6, coat=0.2)
    nose_m = mat("otter_nose", (0.06, 0.04, 0.04), 0.2, coat=1.0)
    eye_m = mat("otter_eye", (0.02, 0.02, 0.03), 0.1, coat=1.0)
    shine = mat("otter_shine", (1, 1, 1), 0.2, emit=4.0)
    whisk = mat("otter_whisker", (0.98, 0.96, 0.9), 0.5)
    cheek = mat("otter_cheek", (1.0, 0.5, 0.45), 0.6)
    ear_in = mat("otter_ear_in", (0.55, 0.32, 0.25), 0.7)
    scarf = mat("otter_scarf", (0.9, 0.12, 0.1), 0.85, emit=0.0)
    stripe = mat("otter_scarf_stripe", (0.98, 0.92, 0.78), 0.85)
    star_m = mat("otter_star", (1.0, 0.85, 0.2), 0.3, emit=3.0)

    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0, 0.1), (0, 0, 0.44), "root"),
         "head": ((0, 0, 0.46), (0, 0, 0.74), "body"),
         "tail": ((0, 0.15, 0.1), (0, 0.42, 0.05), "root"),
         "scarf": ((0.05, 0.13, 0.46), (0.08, 0.21, 0.26), "body"),
         "stars": (tuple(STARS), tuple(STARS + Vector((0, 0, 0.1))), "head")}
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: (p[0] * s, p[1], p[2])
        B["eye." + side] = (m((0.083, -0.14, 0.64)), m((0.083, -0.2, 0.64)), "head")
        B["arm." + side] = (m(SHOULDER), m(PAW), "body")
        B["thigh." + side] = (m(HIP), m(ANKLE), "root")
        B["foot." + side] = (m(ANKLE), m(TOE), "thigh." + side)
    rig = TurnRig(B, 180, fps=30, hidden=("stars",))

    # body: a pear, a lighter belly, the tail behind
    rig.rigid("body", ell(OB, OBR, fur, segs=24, rings=14),
              ell((0, -0.075, 0.26), (0.16, 0.14, 0.2), belly, -4, segs=20, rings=12))
    tail = limb([(0, 0.12, 0.13), (0, 0.22, 0.08), (0, 0.33, 0.05), (0, 0.42, 0.04)], [0.075, 0.07, 0.06, 0.035],
                fur, verts=12, per=3, caps=True)
    tail.data.transform(Matrix.Translation((0, 0, 0.06)) @ Matrix.Diagonal((1.15, 1, 0.5, 1))
                        @ Matrix.Translation((0, 0, -0.06)))
    rig.rigid("tail", tail)
    # head: the pale sea-otter face, muzzle puffs, nose, smile, eyes, cheeks, ears, whiskers
    rig.rigid("head", ell(OH, OHR, face, segs=24, rings=14))
    for s in (1, -1):
        rig.rigid("head", ell((0.05 * s, -0.162, 0.552), (0.064, 0.05, 0.047), muzzle, segs=14, rings=8))
    rig.rigid("head", ell((0, -0.207, 0.585), (0.042, 0.026, 0.028), nose_m, segs=14, rings=8),
              sphere(0.008, (0.012, -0.228, 0.596), shine, segs=6, rings=4))
    rig.rigid("head", tube([(-0.04, -0.187, 0.527), (-0.02, -0.2, 0.513), (0, -0.203, 0.522), (0.02, -0.2, 0.513),
                            (0.04, -0.187, 0.527)], [0.005, 0.006, 0.006, 0.006, 0.005], nose_m, verts=5))
    for s, side in ((1, "L"), (-1, "R")):
        e = Vector((0.083 * s, -0.138, 0.64))
        rig.rigid("eye." + side, ell(e, (0.04, 0.028, 0.045), eye_m, segs=14, rings=8),
                  sphere(0.013, e + Vector((0.013 * s, -0.024, 0.018)), shine, segs=6, rings=4),
                  sphere(0.006, e + Vector((-0.014 * s, -0.026, -0.014)), shine, segs=5, rings=3))
        rig.rigid("head", blob(0.034, (0.12 * s, -0.13, 0.565), cheek, (1.2, 0.3, 0.8), (0.7 * s, -0.7, -0.1),
                               segs=10, rings=6))
        ear = ell((0.175 * s, 0.01, 0.685), (0.038, 0.026, 0.034), fur, segs=12, rings=8)
        rig.rigid("head", ear, blob(0.022, (0.18 * s, -0.012, 0.685), ear_in, (1.0, 0.3, 0.9), (0.3 * s, -1, 0.1),
                                    segs=8, rings=5))
        for k, (dz, dx) in enumerate(((0.02, 0.0), (0.0, 0.01), (-0.02, 0.0))):
            a = Vector((0.07 * s, -0.19, 0.553 + dz * 0.5))
            b = a + Vector((0.11 * s, -0.01, dz * 1.6 + 0.004))
            rig.rigid("head", tube([a, (a + b) / 2 + Vector((0, 0, 0.006)), b], [0.0035, 0.003, 0.002], whisk,
                                   verts=4))
    # the scarf: a knitted collar round the neck, one end down the front, one trailing down the back
    SM = (scarf, stripe)
    rig.rigid("body", knit_ring((0, -0.01, 0.455), 0.15, 0.052, (1.06, 1.0, 0.85), SM,
                                lambda a: (a % (2 * math.pi / 3)) < 0.25))
    rig.rigid("body", *scarf_tail([(-0.07, -0.17, 0.46), (-0.085, -0.2, 0.4), (-0.09, -0.205, 0.33),
                                   (-0.1, -0.2, 0.27)], 0.085, SM))
    rig.rigid("scarf", *scarf_tail([(0.05, 0.13, 0.47), (0.065, 0.2, 0.42), (0.075, 0.23, 0.35),
                                    (0.08, 0.235, 0.28)], 0.08, SM))
    # arms with dark paws; stubby legs with big webbed feet
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: Vector((p[0] * s, p[1], p[2]))
        rig.rigid("arm." + side, limb([m((0.15, -0.02, 0.44)), m(SHOULDER), m((0.2, -0.12, 0.36)), m(PAW)],
                                      [0.05, 0.05, 0.046, 0.042], fur, verts=10, per=2, caps=True),
                  sphere(0.047, m((0.085, -0.235, 0.29)), paw_m, scale=(1.0, 0.9, 0.95), segs=12, rings=8))
        rig.rigid("thigh." + side, limb([m((0.09, 0.0, 0.2)), m(HIP), m(ANKLE)], [0.06, 0.058, 0.045], fur,
                                        verts=10, per=2, caps=True))
        rig.rigid("foot." + side, ell(m((0.112, -0.065, 0.032)), (0.068, 0.1, 0.032), paw_m, segs=14, rings=8))
        for k in range(3):
            rig.rigid("foot." + side, sphere(0.022, m((0.112 + 0.037 * (k - 1), -0.155, 0.028)), paw_m,
                                             scale=(1, 1, 0.7), segs=8, rings=5))
    # dizzy stars round the head (shown only in die)
    st = []
    for k in range(3):
        a = 2 * math.pi * k / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        st.append(star(STARS + d * 0.16, 0.05, star_m, thick=0.022, face=d))
    rig.rigid("stars", *tiny(st, STARS))
    rig.build("otter")

    # ---------------------------------------------------------------- actions
    def blink(k):
        return {"%eye.L": (1, 1, k), "%eye.R": (1, 1, k)}

    def breathe(k, look=0.0, eyes=1.0, sway=0.0):
        return merge({"%body": (1 + 0.012 * k, 1 + 0.012 * k, 1 + 0.025 * k), "head": (-3 * k, 0, look),
                      "arm.L": (0, 0, 0), "scarf": (6 * sway, 0, 8 * sway), "tail": (0, 0, 6 * sway)},
                     blink(eyes), mirror({"arm.L": (0, 3 * k, 0)}))
    rig.action("idle", {0: breathe(0), 15: breathe(1, 0, 1, 1), 22: breathe(0.6, 18, 1, 0.3),
                        30: breathe(0, 18, 1, -1), 38: breathe(0.5, -14, 1, 0), 46: breathe(1, -14, 1, 1),
                        48: breathe(1, -8, 0.1, 1), 50: breathe(0.9, -4, 1, 0.8), 60: breathe(0)}, loop=True)

    def waddle(p):
        a = 2 * math.pi * p
        s, c = math.sin(a), math.cos(a)
        return merge({"@root": (0, 0, 0.022 * (1 + math.cos(2 * a)) / 2), "body": (4, 9 * s, 0),
                      "head": (0, -6 * s, 3 * s), "tail": (0, 0, 16 * s), "scarf": (8 + 6 * c, 0, 14 * s),
                      "thigh.L": (-30 * s, 0, 0), "thigh.R": (30 * s, 0, 0),
                      "foot.L": (30 * s - 18 * max(0, -c) * (s < 0), 0, 0),
                      "foot.R": (-30 * s - 18 * max(0, c) * (s > 0), 0, 0),
                      "arm.L": (18 * s, 0, 0), "arm.R": (-18 * s, 0, 0)})
    rig.action("walk", {f: waddle(f / 15) for f in range(16)}, loop=True)

    windup = merge({"body": (-10, 0, 0), "@root": (0, 0.02, -0.01), "head": (6, 0, 0), "%body": (1.03, 1.03, 0.96)},
                   mirror({"arm.L": (15, 0, -10)}), blink(0.7))
    shove = merge({"body": (20, 0, 0), "@root": (0, -0.06, -0.02), "head": (-12, 0, 0),
                   "thigh.L": (-10, 0, 0), "thigh.R": (25, 0, 0), "foot.R": (-15, 0, 0)},
                  mirror({"arm.L": (-38, -4, -14), "@arm.L": (0, -0.06, 0.01)}), blink(0.3))
    rig.action("push", {0: {}, 2: windup, 4: shove, 6: merge(shove, {"body": (16, 0, 0)}), 9: {}})

    crouch = merge({"@root": (0, 0, -0.03), "%body": (1.08, 1.08, 0.9), "body": (6, 0, 0)},
                   mirror({"arm.L": (0, -25, 0)}), {"thigh.L": (-20, 0, 0), "thigh.R": (-20, 0, 0),
                                                     "foot.L": (20, 0, 0), "foot.R": (20, 0, 0)})
    up = merge({"@root": (0, 0, 0.1), "%body": (0.95, 0.95, 1.08), "body": (0, -10, 0), "tail": (-25, 0, 0)},
               mirror({"arm.L": (0, -70, 0)}), {"thigh.L": (-35, 0, 0), "thigh.R": (5, 0, 0)})
    stomp = merge({"@root": (0, 0, -0.035), "%root": (1.14, 1.14, 0.82), "body": (0, 16, 0), "head": (0, -8, 0),
                   "tail": (10, 0, 0)}, mirror({"arm.L": (0, -55, 0)}), blink(0.2),
                  {"thigh.L": (-15, 0, 0), "foot.L": (15, 0, 0)})
    rig.action("kick_wall", {0: {}, 2: crouch, 4: up, 6: stomp, 8: merge(stomp, {"%root": (1.05, 1.05, 0.95),
                                                                                  "@root": (0, 0, -0.01)}), 12: {}})

    flat = merge({"%root": (1.5, 1.5, 0.16)}, mirror({"arm.L": (0, -80, 0), "thigh.L": (0, -40, 0)}), blink(0.1))

    def dizzy(k, ang):
        a = math.radians(ang * 2)
        return merge({"%stars": 100, "stars": (0, 0, ang), "head": (7 * math.sin(a), 7 * math.cos(a), 0),
                      "body": (3 * math.sin(a + 1), 5 * math.cos(a + 1), 0)},
                     blink(0.25), mirror({"arm.L": (0, -18, 10)}))
    die = {0: {}, 3: flat, 8: merge(flat, {"%root": (1.45, 1.45, 0.2)}), 12: flat,
           15: merge({"%root": (0.9, 0.9, 1.15), "@root": (0, 0, 0.04)}, dizzy(0, 0)),
           18: merge({"%root": (1.06, 1.06, 0.94)}, dizzy(0, 40))}
    for k, f in enumerate(range(21, 37, 3)):
        die[f] = dizzy(0, 40 + 50 * (k + 1))
    rig.action("die", die)

    def hop(h, arms, twist, sq):
        return merge({"@root": (0, 0, h), "%body": (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq), "body": (0, 0, twist),
                      "head": (-8 if h > 0.05 else 0, 0, -twist * 0.5), "tail": (-20 if h > 0.05 else 0, 0, twist)},
                     mirror({"arm.L": (-arms, 0, arms * 0.75)}),
                     {"thigh.L": (-25 if h > 0.05 else 0, 0, 0), "thigh.R": (-25 if h > 0.05 else 0, 0, 0)})
    rig.action("cheer", {0: hop(-0.02, 25, 0, 0.9), 5: hop(0.14, 85, 12, 1.08), 10: hop(-0.02, 35, 0, 0.9),
                         15: hop(0.0, 25, -14, 1.0), 20: hop(0.14, 85, -12, 1.08), 25: hop(-0.02, 35, 0, 0.9),
                         30: hop(-0.02, 25, 0, 0.9)}, loop=True)
    rig.save("otter")


# ------------------------------------------------------------------ the frost mite (written facing -Y)

MC = Vector((0, 0, 0.25))
MR = 0.2
MSC = (1.1, 1.0, 0.95)
MSTARS = Vector((0, 0, 0.56))


def mpoint(d, k=1.0):
    d = Vector(d).normalized()
    return MC + Vector((d.x * MR * MSC[0], d.y * MR * MSC[1], d.z * MR * MSC[2])) * k


def egg_half(r, h, material, upper, cut, teeth=9, amp=0.03, segs=27, rings=16):
    """Half of an egg shell (radius r, height h, standing at the origin) split along a zigzag at height cut;
    solidified."""
    bm = bmesh.new()
    rows = []
    for i in range(rings + 1):
        t = i / rings
        rows.append([(r * egg_prof(t) * math.cos(2 * math.pi * j / segs),
                      r * egg_prof(t) * math.sin(2 * math.pi * j / segs), h * t) for j in range(segs)])
    zz = lambda j: cut + (amp if j % 3 == 0 else -amp if j % 3 == 2 else amp * 0.2)
    # clamp each column's vertices to the zigzag, so the edge follows it
    verts = []
    for i, row in enumerate(rows):
        vrow = []
        for j, (x, y, z) in enumerate(row):
            c = zz(j)
            if upper and z < c:
                t = c / h
                x, y, z = r * egg_prof(t) * math.cos(2 * math.pi * j / segs), r * egg_prof(t) * math.sin(2 * math.pi * j / segs), c
            if not upper and z > c:
                t = c / h
                x, y, z = r * egg_prof(t) * math.cos(2 * math.pi * j / segs), r * egg_prof(t) * math.sin(2 * math.pi * j / segs), c
            vrow.append(bm.verts.new((x, y, z)))
        verts.append(vrow)
    for i in range(rings):
        for j in range(segs):
            q = (verts[i][j], verts[i][(j + 1) % segs], verts[i + 1][(j + 1) % segs], verts[i + 1][j])
            if len({v.co.to_tuple(5) for v in q}) >= 3:
                try:
                    bm.faces.new(q)
                except ValueError:
                    pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = new_obj("egg", bm, material, smooth=70)
    K.select(o)
    sm = o.modifiers.new("s", "SOLIDIFY")
    sm.thickness = 0.015
    bpy.ops.object.modifier_apply(modifier=sm.name)
    return o


def mite():
    body = mat("mite_body", (0.55, 0.72, 1.0), 0.9)
    belly = mat("mite_belly", (0.93, 0.97, 1.0), 0.8, emit=0.45, emit_color=(0.55, 0.85, 1.0))
    glow = mat("mite_glow", (0.55, 1.0, 0.95), 0.3, emit=6.0)
    eye = mat("mite_eye", (1.0, 1.0, 1.0), 0.2, coat=0.6, emit=0.1)
    pupil = mat("mite_pupil", (0.05, 0.05, 0.14), 0.12, coat=1.0)
    shine = mat("mite_shine", (1, 1, 1), 0.2, emit=4.0)
    tooth = mat("mite_tooth", (1.0, 1.0, 0.97), 0.3, coat=0.5)
    mouth = mat("mite_mouth", (0.2, 0.06, 0.2), 0.6)
    foot = mat("mite_foot", (0.3, 0.36, 0.7), 0.6)
    brow = mat("mite_brow", (0.25, 0.3, 0.6), 0.7)
    star_m = mat("mite_star", (1.0, 0.9, 0.3), 0.3, emit=3.0)
    egg_m = mat("mite_egg", (0.88, 0.86, 1.0), 0.45, coat=0.4, emit=0.15, emit_color=(0.6, 0.55, 1.0))
    egg_spot = mat("mite_egg_spot", (0.58, 0.5, 0.95), 0.5)

    MOUTH = mpoint((0, -1, -0.4), 1.0)
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0, 0.08), (0, 0, 0.44), "root"),
         "jaw": (tuple(MOUTH + Vector((0, 0, 0.02))), tuple(MOUTH + Vector((0, -0.06, 0.02))), "body"),
         "stars": (tuple(MSTARS), tuple(MSTARS + Vector((0, 0, 0.1))), "body"),
         "egg_bot": ((0, 0, 0), (0, 0, 0.1), None),
         "egg_top": ((0, 0, 0.34), (0, 0, 0.45), None)}
    ANT0 = {}
    for s, side in ((1, "L"), (-1, "R")):
        a0 = mpoint((0.35 * s, -0.1, 1.0), 0.9)
        ANT0[side] = a0
        B["antenna." + side] = (tuple(a0), (0.13 * s, 0.0, 0.54), "body")
        d = Vector((0.42 * s, -0.84, 0.28)).normalized()
        e = mpoint(d, 0.96)
        B["eye." + side] = (tuple(e), tuple(e + d * 0.06), "body")
        B["foot." + side] = ((0.09 * s, 0.0, 0.1), (0.095 * s, -0.08, 0.02), "root")
        B["arm." + side] = (tuple(mpoint((1.0 * s, -0.25, -0.1), 0.9)), tuple(mpoint((1.0 * s, -0.4, -0.5), 1.15)),
                            "body")
    rig = TurnRig(B, 180, fps=30, hidden=("stars", "egg_bot", "egg_top"))

    # the fuzzy ball: a round core bristling with soft tufts (the face left clear)
    rig.rigid("body", sphere(MR, MC, body, scale=MSC, segs=24, rings=14))
    n = 150
    rnd = random.Random(8)
    ga = math.pi * (3 - math.sqrt(5))
    for k in range(n):
        z = 1 - 2 * (k + 0.5) / n
        rr = math.sqrt(1 - z * z)
        d = Vector((math.cos(ga * k) * rr, math.sin(ga * k) * rr, z))
        if d.y < -0.35 and -0.75 < d.z < 0.62 or d.z < -0.8:
            continue
        dd = (d + Vector((rnd.uniform(-0.3, 0.3), 0.35 + rnd.uniform(-0.3, 0.3), 0.5))).normalized()  # combed back
        o = ell((0, 0, 0), (1, 1, 1), body, segs=7, rings=5)
        h = rnd.uniform(0.05, 0.07)
        w = rnd.uniform(0.036, 0.044)
        for v in o.data.vertices:     # a soft teardrop: full at the base, tapering to a blunt tip
            t = (v.co.z + 1) / 2
            v.co.x *= w * (1 - 0.5 * t ** 2)
            v.co.y *= w * (1 - 0.5 * t ** 2)
            v.co.z = (v.co.z + 0.45) * h
        o.data.update()
        o.data.transform(Vector((0, 0, 1)).rotation_difference(dd).to_matrix().to_4x4())
        o.data.transform(Matrix.Translation(mpoint(d, 0.93)))
        rig.rigid("body", o)
    fd = Vector((0, -1, -0.05)).normalized()
    rig.rigid("body", blob(0.165, mpoint(fd, 0.78), belly, (1.15, 0.3, 1.1), fd, segs=14, rings=9))
    # eyes: big whites, pupils, shines; slanted cheeky brows above
    for s, side in ((1, "L"), (-1, "R")):
        d = Vector((0.42 * s, -0.84, 0.28)).normalized()
        e = mpoint(d, 0.96)
        pp = e + d * 0.036 + Vector((-0.012 * s, -0.004, -0.006))
        rig.rigid("eye." + side, blob(0.07, e, eye, (1.0, 0.55, 1.15), d, segs=14, rings=8),
                  blob(0.042, pp, pupil, (0.9, 0.5, 1.05), d, segs=12, rings=7),
                  sphere(0.013, pp + d * 0.022 + Vector((0.008 * s, -0.01, 0.018)), shine, segs=6, rings=4))
        bc = e + Vector((0.0, -0.02, 0.1))
        rig.rigid("body", limb([bc + Vector((0.045 * s, 0.01, 0.018)), bc, bc + Vector((-0.045 * s, -0.012, -0.012))],
                               [0.01, 0.014, 0.011], brow, verts=5, per=2, caps=True))
    # the mouth and two buck teeth
    rig.rigid("jaw", blob(0.048, MOUTH + Vector((0, -0.028, -0.012)), mouth, (1.1, 0.4, 0.6),
                          (0, -1, -0.3), segs=12, rings=7))
    for s in (1, -1):
        rig.rigid("body", box((0.028, 0.014, 0.034), MOUTH + Vector((0.016 * s, -0.045, -0.002)), tooth, bevel=0.006))
    # antennae with glowing bulbs
    for s, side in ((1, "L"), (-1, "R")):
        a0 = ANT0[side]
        tip = Vector((0.13 * s, 0.0, 0.54))
        rig.rigid("antenna." + side, tube([a0, a0 + Vector((0.01 * s, -0.01, 0.06)), tip], [0.011, 0.009, 0.008],
                                          foot, verts=6),
                  ico(0.036, tip + Vector((0.005 * s, 0, 0.018)), glow, sub=2, smooth=80))
    # stubby arms and feet
    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("arm." + side, sphere(0.045, mpoint((1.0 * s, -0.4, -0.5), 1.1), belly, scale=(0.8, 0.9, 1.0),
                                        segs=10, rings=6))
        rig.rigid("foot." + side, ell((0.095 * s, -0.035, 0.032), (0.05, 0.07, 0.033), foot, segs=12, rings=7))
    # stars (stunned)
    st = []
    for k in range(3):
        a = 2 * math.pi * k / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        st.append(star(MSTARS + d * 0.15, 0.045, star_m, thick=0.02, face=d))
    rig.rigid("stars", *tiny(st, MSTARS))
    # the egg shell (hatch only): two halves split along a zigzag at 0.34
    bot = egg_half(0.25, 0.54, egg_m, False, 0.34)
    top = egg_half(0.25, 0.54, egg_m, True, 0.34)
    spots = []
    rnd = random.Random(12)
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(0.08, 0.5)
        rr = 0.25 * egg_prof(z / 0.54) + 0.004
        spots.append((blob(rnd.uniform(0.018, 0.03), (math.cos(a) * rr, math.sin(a) * rr, z), egg_spot,
                           (1.0, 0.25, 1.0), (math.cos(a), math.sin(a), 0), segs=8, rings=5), z))
    rig.rigid("egg_bot", *tiny([bot] + [o for o, z in spots if z < 0.31], (0, 0, 0)))
    rig.rigid("egg_top", *tiny([top] + [o for o, z in spots if z >= 0.31], (0, 0, 0.34)))
    rig.build("mite")

    # ---------------------------------------------------------------- actions
    def eyes(k):
        return {"%eye.L": (1, 1, k), "%eye.R": (1, 1, k)}

    def scuttle(p):
        a = 2 * math.pi * p
        s = math.sin(a)
        h = abs(math.sin(a))
        sq = 1 + 0.08 * (h - 0.5)
        return {"@root": (0, 0, 0.05 * h), "%body": (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq),
                "body": (6, 6 * s, 0), "foot.L": (-35 * s, 0, 0), "foot.R": (35 * s, 0, 0),
                "antenna.L": (-18 * h + 8, 0, 6 * s), "antenna.R": (-18 * h + 8, 0, 6 * s),
                "arm.L": (25 * s, 0, 0), "arm.R": (-25 * s, 0, 0)}
    rig.action("walk", {f: scuttle(f / 15) for f in range(16)}, loop=True)

    def gnaw(k, w):
        return merge({"body": (16 + 4 * k, 3 * w, 0), "@root": (0, -0.03, -0.01 * k), "%jaw": (1.0, 1, 0.5 + 1.2 * k),
                      "%body": (1 + 0.03 * k, 1, 1 - 0.04 * k), "antenna.L": (10 * k, 0, 0),
                      "antenna.R": (10 * (1 - k), 0, 0), "arm.L": (-50, -10, 0), "arm.R": (-50, 10, 0)}, eyes(1 - 0.35 * k))
    rig.action("chew", {0: gnaw(0, 0), 3: gnaw(1, 1), 6: gnaw(0.1, 0), 8: gnaw(0.9, -1), 11: gnaw(0.2, 0),
                        13: gnaw(0.8, 0.5), 15: gnaw(0, 0)}, loop=True)

    def daze(t):
        a = 2 * math.pi * t
        return merge({"%stars": 100, "stars": (0, 0, 360 * t), "body": (8 * math.sin(a), 8 * math.cos(a), 0),
                      "antenna.L": (35, 0, 20 * math.sin(a)), "antenna.R": (35, 0, 20 * math.sin(a + 1)),
                      "%jaw": (1, 1, 1.3), "@root": (0, 0, -0.01)}, eyes(0.12))
    rig.action("stunned", {f: daze(f / 30) for f in range(0, 31, 3)}, loop=True)

    flat = merge({"%root": (1.55, 1.55, 0.13)}, eyes(0.2), {"antenna.L": (0, -60, 0), "antenna.R": (0, 60, 0)})
    rig.action("squash", {0: {}, 3: flat, 6: merge(flat, {"%root": (1.45, 1.45, 0.19)}), 9: flat, 15: flat})

    def egg(k, rock=0.0, top=(0, 0, 0), top_rot=0.0, top_s=100, bot_s=100):
        a = math.radians(rock)
        off = (0.34 * math.sin(a), 0, 0.34 * (math.cos(a) - 1))
        return {"%egg_bot": bot_s, "%egg_top": top_s, "egg_bot": (0, rock, 0),
                "egg_top": (top_rot, rock + top_rot * 0.6, 0),
                "@egg_top": tuple(o + t for o, t in zip(off, top))}
    inside = {"%root": 0.55, "@root": (0, 0, 0.02)}
    rig.action("hatch", {0: merge(inside, egg(0)), 2: merge(inside, egg(0, 9)), 4: merge(inside, egg(0, -9)),
                         6: merge(inside, egg(0, 7)), 8: merge(inside, egg(0, -5)),
                         10: merge({"%root": (0.9, 0.9, 1.25), "@root": (0, 0, 0.12)}, eyes(0.3),
                                   egg(0, 0, (0.05, 0.02, 0.22), -35)),
                         14: merge({"%root": (1.08, 1.08, 1.05), "@root": (0, 0, 0.14)}, eyes(1.1),
                                   {"antenna.L": (-25, 0, 0), "antenna.R": (-25, 0, 0)},
                                   egg(0, 0, (0.14, 0.05, 0.3), -80, 60)),
                         18: merge({"%root": (1.15, 1.15, 0.85), "@root": (0, 0, 0.0)},
                                   {"antenna.L": (25, 0, 0), "antenna.R": (25, 0, 0)},
                                   egg(0, 0, (0.22, 0.08, 0.2), -120, 0, 45)),
                         21: merge({"%root": (0.96, 0.96, 1.05)}, egg(0, 0, (0.22, 0.08, 0.2), -120, 0, 8)),
                         24: merge({}, egg(0, 0, (0.22, 0.08, 0.2), -120, 0, 0))})
    rig.save("mite")


# ------------------------------------------------------------------ dressing (built facing -Y = Godot +Z)

def snow_mound(c, r, h, material, seed, sub=2):
    o = lumpy(1.0, (0, 0, 0), material, seed, amount=0.08, sub=sub, smooth=70)
    o.data.transform(Matrix.Translation(Vector(c)) @ Matrix.Diagonal((r, r * 0.9, h, 1)))
    return o


def igloo():
    snow = mat("igloo_snow", (0.9, 0.95, 1.0), 0.6, emit=0.12, emit_color=(0.7, 0.85, 1.0))
    seam = mat("igloo_seam", (0.55, 0.7, 0.9), 0.7)
    glow = mat("igloo_glow", (1.0, 0.62, 0.25), 0.4, emit=6.0, emit_color=(1.0, 0.55, 0.2))
    ice = mat("igloo_icicle", (0.55, 0.85, 1.0), 0.05, coat=1.0, emit=0.6, emit_color=(0.3, 0.7, 1.0))
    R, Hs = 0.75, 0.95 / 0.75
    parts = []
    dome = hemi(R, (0, 0, 0), (0, 0, 1), snow, cut=-0.01, segs=32, rings=18)
    dome.data.transform(Matrix.Diagonal((1, 1, Hs, 1)))
    parts.append(dome)
    rows = 5
    for r in range(1, rows):
        el = math.radians(90 * r / rows)
        rr, z = R * math.cos(el), R * math.sin(el) * Hs
        parts.append(torus(rr + 0.004, 0.012, (0, 0, z), seam, verts=40, minor=4))
        n = max(4, int(12 * math.cos(el)))
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (r % 2)) / n
            el0 = math.radians(90 * (r - 1) / rows)
            p0 = Vector((R * math.cos(el0) * math.cos(a), R * math.cos(el0) * math.sin(a), R * math.sin(el0) * Hs))
            p1 = Vector((rr * math.cos(a), rr * math.sin(a), z))
            parts.append(rod(p0 * 1.006, p1 * 1.006, 0.01, seam, verts=4))
    # the tunnel porch towards the camera, its round doorway glowing
    tun = hemi(0.36, (0, 0, 0), (0, 0, 1), snow, cut=-0.01, segs=20, rings=8)
    tun.data.transform(Matrix.Diagonal((1, 1, 1.25, 1)))
    tun.data.transform(Matrix.Translation((0, -0.7, 0)) @ Matrix.Diagonal((1, 1.0, 1, 1)))
    parts.append(tun)
    parts.append(ell((0, -0.72, 0.0), (0.37, 0.4, 0.46), snow, segs=20, rings=10))
    door = ell((0, -1.05, 0.0), (0.2, 0.05, 0.3), glow, segs=18, rings=10)
    parts.append(door)
    parts.append(torus(0.215, 0.035, (0, -1.07, 0.0), snow, rot=(R90, 0, 0), verts=24, minor=6,
                       scale=(1, 1.45, 1)))
    for k in range(5):
        x = -0.2 + 0.1 * k
        z = 0.3 * math.sqrt(max(0.0, 1 - (x / 0.24) ** 2)) + 0.02
        parts.append(rod((x, -1.08, z), (x, -1.08, z - 0.06 - 0.03 * (k % 2)), 0.012, ice, r2=0.001, verts=5))
    rnd = random.Random(4)
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.3
        if abs(math.cos(a + R90)) > 0.85 and math.sin(a) < 0:
            continue
        parts.append(snow_mound((math.cos(a) * 0.78, math.sin(a) * 0.78, 0.0), rnd.uniform(0.14, 0.22),
                                rnd.uniform(0.06, 0.1), snow, 60 + k))
    # a window of clear ice on the side, lit from inside
    parts.append(blob(0.1, (0.62, -0.28, 0.42), glow, (1.0, 0.3, 0.8), (0.9, -0.4, 0.45), segs=12, rings=6))
    simple(parts, "igloo")


def pine_snowy():
    bark = mat("pine_bark", (0.28, 0.16, 0.09), 0.85)
    needle = mat("pine_needles", (0.05, 0.25, 0.2), 0.8)
    snow = mat("pine_snow", (0.93, 0.96, 1.0), 0.6, emit=0.12, emit_color=(0.7, 0.85, 1.0))
    parts = [cyl(0.085, 0.45, (0, 0, 0.22), bark, verts=10, r2=0.06)]
    rnd = random.Random(7)
    tiers = ((0.3, 0.66, 0.78), (0.68, 0.52, 0.7), (1.03, 0.4, 0.62), (1.36, 0.27, 0.62))
    n = 16
    for k, (z, r, h) in enumerate(tiers):
        # a steep cone with a scalloped hem (every other rim vertex droops and sticks out)
        jag = lambda kk, zz, z=z: (1.1 if kk % 2 == 0 else 0.92) if zz < z + 0.06 else 1.0
        parts.append(lathe_r([(0.0, z + h), (r * 0.35, z + h * 0.62), (r * 0.75, z + h * 0.22), (r, z + 0.04),
                              (r * 0.8, z - 0.01), (0.0, z + 0.1)], needle, segs=n, radial=jag, smooth=50))
        # snow on the upper slope: a thin shell following the cone, ending in soft clumps
        # snow on the exposed lower slope (the next tier hides the upper one), the top tier gets a cap
        if k == len(tiers) - 1:
            prof = [(0.0, z + h + 0.02), (r * 0.3 + 0.02, z + h * 0.7), (r * 0.36 + 0.02, z + h * 0.6),
                    (r * 0.25, z + h * 0.64)]
            cz = z + h * 0.6
        else:
            prof = [(r * 0.68, z + h * 0.19), (r * 0.8 + 0.018, z + h * 0.17 + 0.012), (r * 0.9 + 0.012, z + h * 0.12),
                    (r * 0.78, z + h * 0.13)]
            cz = z + h * 0.13
        parts.append(lathe_r(prof, snow, segs=n, radial=lambda kk, zz: 1.0 + (0.1 if kk % 4 == 0 else 0.0),
                             smooth=50))
        for jj in range(5 + k % 2):
            a = 2 * math.pi * (jj + rnd.random() * 0.5) / (5 + k % 2)
            rr = r * (0.36 if k == len(tiers) - 1 else 0.88)
            q = (math.cos(a) * rr, math.sin(a) * rr, cz)
            parts.append(ell(q, (0.065, 0.065, 0.04), snow, segs=8, rings=5))
        # a snowy hem here and there
        for jj in range(3):
            a = 2 * math.pi * (jj + 0.3 + rnd.random() * 0.3) / 3 + k
            q = (math.cos(a) * r * 1.0, math.sin(a) * r * 1.0, z + 0.06)
            parts.append(ell(q, (0.07, 0.05, 0.03), snow, yaw=math.degrees(a) + 90, segs=8, rings=5))
    parts.append(snow_mound((0, 0, 0), 0.34, 0.07, snow, 5))
    simple(parts, "pine_snowy")


def snowman():
    snow = mat("snowman_snow", (0.95, 0.97, 1.0), 0.55, emit=0.12, emit_color=(0.7, 0.85, 1.0))
    coal = mat("snowman_coal", (0.05, 0.05, 0.07), 0.4, coat=0.5)
    carrot = mat("snowman_carrot", (1.0, 0.42, 0.08), 0.5)
    stick = mat("snowman_stick", (0.3, 0.18, 0.1), 0.85)
    scarf = mat("snowman_scarf", (0.1, 0.62, 0.55), 0.85)
    stripe = mat("snowman_scarf_stripe", (0.98, 0.9, 0.5), 0.85)
    hat = mat("snowman_hat", (0.85, 0.15, 0.25), 0.85)
    shine = mat("snowman_shine", (1, 1, 1), 0.2, emit=3.0)
    parts = [sphere(0.3, (0, 0, 0.27), snow, scale=(1, 1, 0.92), segs=24, rings=14),
             sphere(0.22, (0, 0, 0.66), snow, segs=22, rings=12),
             sphere(0.165, (0, 0, 0.95), snow, segs=20, rings=12)]
    H = Vector((0, 0, 0.95))
    for s in (1, -1):
        e = H + Vector((0.06 * s, -0.145, 0.04))
        parts.append(sphere(0.022, e, coal, segs=8, rings=6))
        parts.append(sphere(0.007, e + Vector((0.006, -0.018, 0.008)), shine, segs=5, rings=3))
    for k in range(5):
        a = math.radians(-60 + 30 * k)
        parts.append(sphere(0.012, H + Vector((0.07 * math.sin(a), -0.15, -0.055 - 0.02 * math.cos(a))), coal, segs=6,
                            rings=4))
    parts.append(rod(H + Vector((0, -0.14, 0.0)), H + Vector((0.015, -0.32, -0.02)), 0.028, carrot, r2=0.004, verts=10))
    for z in (0.58, 0.7, 0.3, 0.44):
        parts.append(sphere(0.025, (0, -0.21 if z > 0.5 else -0.285, z), coal, segs=8, rings=6))
    for s in (1, -1):
        a = Vector((0.18 * s, 0, 0.72))
        b = a + Vector((0.28 * s, 0.02, 0.2))
        parts.append(tube([a, (a + b) / 2, b], [0.017, 0.014, 0.01], stick, verts=6))
        parts.append(tube([(a + b) / 2 + Vector((0.04 * s, 0, 0.02)), (a + b) / 2 + Vector((0.08 * s, 0.0, 0.1))],
                          [0.01, 0.007], stick, verts=5))
        for t in (-1, 1):
            parts.append(tube([b, b + Vector((0.06 * s, 0.0, 0.05 * t + 0.03))], [0.008, 0.006], stick, verts=5))
    SM = (scarf, stripe)
    parts.append(knit_ring((0, 0, 0.82), 0.14, 0.045, (1.05, 1.0, 0.8), SM, lambda a: (a % (math.pi / 3)) < 0.2))
    parts += scarf_tail([(0.08, -0.13, 0.82), (0.12, -0.2, 0.74), (0.14, -0.21, 0.64), (0.15, -0.2, 0.56)], 0.07, SM)
    # a knitted bobble hat
    parts.append(lathe_r([(0.0, 1.17), (0.08, 1.16), (0.13, 1.11), (0.155, 1.04), (0.16, 1.03), (0.0, 1.03)], hat,
                         segs=20, smooth=60))
    parts.append(torus(0.158, 0.028, (0, 0, 1.035), stripe, verts=24, minor=6))
    parts.append(ico(0.045, (0, 0, 1.19), stripe, sub=2, smooth=0))
    parts.append(snow_mound((0, 0, 0), 0.36, 0.06, snow, 8))
    root = join(parts, "snowman")
    root.data.transform(Matrix.Rotation(math.radians(-8), 4, "Z"))
    export(root, "snowman")


def ice_rock():
    ice = mat("ice_rock", (0.3, 0.7, 1.0), 0.08, coat=1.0, emit=0.4, emit_color=(0.2, 0.6, 1.0))
    glow = mat("ice_rock_glow", (0.6, 1.0, 1.0), 0.2, emit=5.0, emit_color=(0.4, 0.95, 1.0))
    snow = mat("ice_rock_snow", (0.93, 0.96, 1.0), 0.6, emit=0.12, emit_color=(0.7, 0.85, 1.0))
    parts = []
    rnd = random.Random(9)

    def crystal(base, d, r, h, material):
        bm = bmesh.new()
        ring0 = [bm.verts.new((r * math.cos(k * math.pi / 3), r * math.sin(k * math.pi / 3), 0)) for k in range(6)]
        ring1 = [bm.verts.new((r * 0.9 * math.cos(k * math.pi / 3), r * 0.9 * math.sin(k * math.pi / 3), h * 0.7))
                 for k in range(6)]
        tip = bm.verts.new((0, 0, h))
        for k in range(6):
            j = (k + 1) % 6
            bm.faces.new((ring0[k], ring0[j], ring1[j], ring1[k]))
            bm.faces.new((ring1[k], ring1[j], tip))
        bm.faces.new(ring0[::-1])
        o = new_obj("crystal", bm, material, smooth=0)
        o.data.transform(Matrix.Translation(Vector(base)) @ Vector((0, 0, 1)).rotation_difference(
            Vector(d).normalized()).to_matrix().to_4x4())
        return o
    parts.append(crystal((0, 0, -0.02), (0, 0, 1), 0.11, 0.6, glow))
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.2, 0.2)
        d = (math.cos(a) * 0.55, math.sin(a) * 0.55, 1.0)
        parts.append(crystal((math.cos(a) * 0.08, math.sin(a) * 0.08, -0.02), d, rnd.uniform(0.06, 0.1),
                             rnd.uniform(0.25, 0.45), ice))
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.5
        parts.append(snow_mound((math.cos(a) * 0.2, math.sin(a) * 0.2, 0), rnd.uniform(0.1, 0.16), 0.06, snow, 20 + k))
    simple(parts, "ice_rock")


def lantern_ice():
    wood = mat("lantern_ice_post", (0.3, 0.18, 0.1), 0.8)
    metal = mat("lantern_ice_frame", (0.2, 0.22, 0.28), 0.4, metal=0.8)
    glass = mat("lantern_ice_glass", (0.6, 0.9, 1.0), 0.05, coat=1.0, alpha=0.45, emit=0.6, emit_color=(0.4, 0.8, 1.0))
    glow = mat("lantern_ice_glow", (1.0, 0.8, 0.45), 0.3, emit=8.0, emit_color=(1.0, 0.7, 0.35))
    snow = mat("lantern_ice_snow", (0.93, 0.96, 1.0), 0.6, emit=0.12, emit_color=(0.7, 0.85, 1.0))
    parts = [box((0.08, 0.08, 1.2), (0, 0, 0.6), wood, bevel=0.015),
             box((0.3, 0.06, 0.06), (0.11, 0, 1.13), wood, bevel=0.012),
             rod((0.03, 0, 0.95), (0.2, 0, 1.12), 0.018, wood, verts=6),
             box((0.1, 0.1, 0.035), (0, 0, 1.215), snow, bevel=0.015),
             ell((0.12, 0, 1.17), (0.16, 0.045, 0.025), snow, segs=12, rings=6),
             snow_mound((0, 0, 0), 0.22, 0.08, snow, 3)]
    L = Vector((0.22, 0, 0.9))   # lantern centre, hanging from the arm
    parts.append(rod(L + Vector((0, 0, 0.14)), Vector((0.22, 0, 1.11)), 0.006, metal, verts=4))
    parts.append(torus(0.018, 0.005, L + Vector((0, 0, 0.145)), metal, rot=(R90, 0, 0), verts=10, minor=4))
    parts.append(lathe_r([(r, L.z + z) for r, z in ((0.0, 0.14), (0.05, 0.135), (0.1, 0.1), (0.09, 0.09),
                                                    (0.0, 0.09))], metal, segs=6, smooth=0, center=(L.x, L.y, 0)))
    parts.append(lathe_r([(r, L.z + z) for r, z in ((0.0, -0.1), (0.075, -0.1), (0.085, -0.115), (0.0, -0.125))],
                         metal, segs=6, smooth=0, center=(L.x, L.y, 0)))
    parts.append(cyl(0.075, 0.19, L, glass, verts=6))
    parts.append(ell(L + Vector((0, 0, -0.01)), (0.035, 0.035, 0.055), glow, segs=10, rings=6))
    for k in range(6):
        a = k * math.pi / 3
        parts.append(rod(L + Vector((0.077 * math.cos(a), 0.077 * math.sin(a), -0.1)),
                         L + Vector((0.077 * math.cos(a), 0.077 * math.sin(a), 0.095)), 0.006, metal, verts=4))
    for s in (-1, 1):
        parts.append(rod((0.3 * 0.5 + 0.11 + 0.0, 0.0, 1.1), (0.26, 0.0, 1.03 + 0.02 * s), 0.008, glass, r2=0.001,
                         verts=4))
    simple(parts, "lantern_ice")


# ------------------------------------------------------------------ main

JOBS = {"otter": otter, "mite": mite, "ice_block": ice_block, "ice_block_egg": ice_block_egg, "gem_block": gem_block, "ice_shard": ice_shard,
        "wall_segment": wall_segment, "wall_corner": wall_corner, "floor_tile_a": floor_tile_a,
        "floor_tile_b": floor_tile_b, "floor_tile_c": floor_tile_c, "igloo": igloo, "pine_snowy": pine_snowy,
        "snowman": snowman, "ice_rock": ice_rock, "lantern_ice": lantern_ice}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = 30
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
