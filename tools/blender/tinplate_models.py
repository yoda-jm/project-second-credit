"""Tinplate Turbo (game 31) models: the tin wind-up racing car and the dressing of the miniature race-track dioramas.
Original designs in the spirit of old pressed-tin toys (no real toy, car or brand copied): the car is a chubby 1950s-
style racer of our own, its body one pressed shell with pontoon wings over the wheels, a cream lithographed belt line
and twin bonnet stripes, white number discs on both flanks and the bonnet, chrome bumpers and grille, a wrap-round
windscreen, a little driver in a leather cap with goggles and a trailing scarf, side exhausts, and a brass wind-up
key in the tail. The dressing is toy-box scenery: cones, tyre stacks, hay bales, a striped tin crash barrier, a
grandstand of peg spectators under a striped canopy, the start gantry with five lamps, block trees, a toy house, a
windmill, the wrench pickup, oil, a puddle, a jump ramp, a girder bridge, a trophy and a chequered flag.
Deterministic; output CC BY-SA 4.0; provenance: this script only, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/tinplate_models.py -- godot/games/tinplate/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, rod, tube, prism, join, export, ...), hopline_models.py
(ell, hemi), mossfolk_models.py (lathe_r) and prism_models.py (loft_x, new_obj).

Axes: Blender is built Z up and exported Y up: Blender +X = Godot +X, Blender +Z = Godot +Y (up), Blender +Y =
Godot -Z. Game units (1 = 1 m on the diorama, node scale 1). Every origin sits at the base centre on the ground
(Godot y = 0) unless noted. The lit materials (lamps, the wrench rim) have "glow" in their names; house_glass and
oil_sheen* only carry a faint emission.

car.glb          root mesh "car" facing Godot +X (the body from x -0.95 to +0.98, the bumpers reaching -1.0 / +1.05,
                 the key -1.12), 1.0 wide over the tyres (1.06 over the side exhausts), 0.71 tall to the top of the
                 driver's cap; origin on the ground midway between the axles; about 15k triangles in all.
                 Materials: car_paint (the body: recolour it per car), car_trim (cream belt line, bonnet stripes,
                 wheel-arch lips, whitewalls), car_chrome (bumpers, grille, exhausts, screen frame, headlight rims),
                 car_number (the white number discs, draped on the shell, for a digit decal: the bonnet disc 0.115
                 in radius centred at Godot (0.56, 0.441, 0), facing up (normal (0.08, 1, 0)); the flank discs 0.105
                 in radius at (-0.06, 0.27, -+0.442), facing -+Z), car_glow (headlights), car_tail_glow (rear
                 lamps), car_glass,
                 car_dark (wheel wells, cockpit, grille, the number discs' thin outlines), car_driver (overalls),
                 car_skin, car_cheek, car_cap (the leather cap), car_goggle (lenses), car_scarf, car_brass (the key),
                 car_tyre, car_hub (the pressed tin wheel faces; the whitewalls use car_trim).
                 Children (pivots at their centres, unrotated, so the view can spin and steer them):
                   wheel_fl (0.60, 0.21, -0.40), wheel_fr (0.60, 0.21, 0.40), wheel_rl (-0.58, 0.21, -0.40),
                   wheel_rr (-0.58, 0.21, 0.40)   [Godot coordinates; l = left = Godot -Z]: radius 0.21, 0.19 wide,
                   the axle along local Z (spin about Z: negative angles roll forwards; steer the front pair about Y);
                   key (-0.93, 0.31, 0): the wind-up key, its shaft along X: spin it about local X while driving.
cone.glb         0.52 tall traffic cone on a 0.36 square foot: cone_orange, cone_white (bands), cone_base.
tyre_stack.glb   three tyres stacked (0.51 tall, 0.72 across): tyre_rubber, tyre_paint (white), tyre_paint_red
                 (painted bands round the top and bottom tyres).
hay_bale.glb     1.1 (X) x 0.56 (Z) x 0.46 tall, straw tufts poking out: hay_straw, hay_straw_light, hay_straw_dark,
                 hay_twine.
barrier.glb      a 2.0 m tin crash-barrier segment along X (x -1 .. 1, tiles end to end), 0.58 tall: a W-section
                 rail 0.3 .. 0.54 up on the Godot +Z face (the track side, z +0.06 .. +0.1), posts behind it (z up to
                 -0.14): barrier_red, barrier_white (alternating 0.5 m panels), barrier_post, barrier_bolt.
grandstand.glb   8.3 m along X, 3.5 deep (z -1.8 .. 1.7), 3.75 tall to the canopy (the pennants to 4.6): four tiers of
                 peg spectators (some cheering, some waving flags) facing Godot +Z, a red-and-white striped canopy
                 over the back rows only (so the camera sees the crowd) with a scalloped valance, three pennants.
                 stand_wall, stand_trim, stand_seat, stand_post, stand_board_yellow/green, stand_roof_red,
                 stand_roof_white, stand_flag_yellow/blue/green, fan_0 .. fan_7 (shirts), fan_skin_0 .. 2, fan_hat.
start_gantry.glb an arch over the track, 0.8 deep (z -0.4 .. 0.4): banded towers at x = +-5.0 (inner faces at +-4.8,
                 a 9.6 m clear span, 5.0 tall to the finials), the beam 3.3 .. 4.1 up, chequered on both faces
                 (gantry_black, gantry_white), towers gantry_red/gantry_white, gantry_base, gantry_frame (the lamp
                 bar 2.7 .. 3.2 up, the lowest point over the track). Five lamp children "light_0" .. "light_4"
                 (left to right at x = -1.6, -0.8, 0, 0.8, 1.6, y 2.95; lenses on both faces), material gantry_glow
                 (red): give each its own material_override (dark, red, then green) for the countdown.
tree.glb         a toy fir (three stacked tiers, a gold bead on top), 3.1 tall, 1.9 across: tree_trunk, tree_green,
                 tree_green_dark, tree_star.
tree_round.glb   a lollipop tree, 2.85 tall, crown 1.95 across, a few red apples: tree_trunk, tree_leaf, tree_apple.
house.glb        a toy house 3.0 (X) x 2.6 (Z) (3.4 x 3.3 over the eaves and the step), 3.3 tall to the chimney, the
                 door facing Godot +Z: house_wall, house_roof, house_trim, house_door, house_knob, house_glass (a
                 faint warm glow), house_shutter, house_flower, house_chimney.
windmill_toy.glb a toy windmill facing +X: an octagonal tower 2 across, a dome cap to 4.3, the sails reaching 5.3;
                 child "sails" (four latticed sails, 2.0 radius, in the local YZ plane) with its pivot at the hub,
                 Godot (0.95, 3.3, 0): spin it about local X. windmill_body, windmill_band, windmill_roof,
                 windmill_door, windmill_frame, windmill_canvas, windmill_canvas_red, windmill_hub, windmill_glass.
wrench.glb       the pickup: a chrome combination spanner 0.67 long along X lying flat (open jaw at +X, ring at -X),
                 0.2 across the heads, 0.04 thick (y -0.02 .. 0.02), origin at its centre (the view floats and spins
                 it): wrench_metal, wrench_glow (a glowing rim all round, just under the steel).
oil.glb          a glossy oil slick about 2.4 x 1.8 with its droplets (the pool 2.0 x 1.6), 0.02 high, a purple and a
                 green sheen: oil, oil_sheen, oil_sheen_green.
puddle.glb       a rain puddle about 2.9 x 1.6 with two small ones (the main pool 2.3 x 1.6), 0.015 high: puddle_water
                 (blended), puddle_wet (the dark wet rim), puddle_ripple (rings).
ramp.glb         a tin jump ramp 3.0 long (x -1.5 .. 1.5), the deck rising along +X as 0.6 * u^1.35 (u = (x + 1.5) / 3,
                 a gentle kicker) to 0.6 at x = +1.5, the deck 2.2 wide (2.36 over the side panels): ramp_deck,
                 ramp_side, ramp_stripe (yellow chevrons and edges), ramp_black, ramp_bolt.
bridge.glb       a toy girder bridge: the deck 10 long along X (x -5 .. 5), 6 wide (z -3 .. 3), its plain asphalt top
                 at y = 2.2 (lay the track ribbon a hair above it; open at both ends for the approaches), red and
                 white kerbs 0.06 high along both edges (z +-2.6 .. +-2.9), truss railings to 2.96, four stone
                 pillars at x = +-4.55, z = +-2.2 (a lower track along Z passes between them: 8.3 clear across,
                 1.59 clear under the girders): bridge_deck, bridge_kerb_red, bridge_kerb_white, bridge_steel,
                 bridge_pillar, bridge_cap, bridge_bolt.
trophy.glb       a tin trophy cup 0.97 tall (0.64 across the handles, along X) on a block plinth, a star and a plaque
                 on its Godot +Z face: trophy_gold, trophy_inside, trophy_base, trophy_plaque.
flag_chequered.glb a chequered flag on a 1.74 m pole in a little stand: flag_pole, flag_knob, flag_stand; child "cloth"
                 (0.82 x 0.6, flying towards +X, pivot on the pole at Godot (0, 1.62, 0)) with flag_black and
                 flag_white (double sided): the view can flutter it about Y.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, reset, R90
from hopline_models import ell, hemi
from mossfolk_models import lathe_r
from prism_models import loft_x, new_obj


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1]:
            u = (x - xs[i]) / (xs[i + 1] - xs[i])
            u = u * u * (3 - 2 * u)
            return ys[i] + (ys[i + 1] - ys[i]) * u
    return ys[-1]


def two_sided(m):
    m.use_backface_culling = False
    return m


def grid_obj(grid, material, name="grid", smooth=60, mats=None):
    """A quad surface through rows of points; mats(i, j) -> material index for each quad."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in grid]
    for i in range(len(vs) - 1):
        for j in range(len(vs[0]) - 1):
            f = bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
            if mats:
                f.material_index = mats(i, j)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    K.select(o)
    if smooth:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth))
    return o


def raw_obj(name, bm, material, smooth=60):
    """Like new_obj, keeping the winding as built (no normal recalculation: open sheets keep their facing)."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=smooth)


def baked(o):
    """Applies an object's rotation and scale to its mesh, so data.transform() then works in world space."""
    K.select(o)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return o


def set_mats(o, materials):
    o.data.materials.clear()
    for m in materials:
        o.data.materials.append(m)
    return o


def slab(poly, z0, z1, material, name="slab", smooth=0, bevel=0.0):
    """A 2D outline (x, y, counter-clockwise seen from above) extruded from z0 up to z1."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in poly]
    hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    o = new_obj(name, bm, material, smooth=smooth)
    if bevel:
        K.finish(o, material, bevel, 2, smooth=smooth or 30)
    return o


def dome_blob(poly, h, z0, material, name="blob", rings=4):
    """A flat blob: the outline at z0 rising to a gently domed top of height h (oil, puddles)."""
    bm = bmesh.new()
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    n = len(poly)
    base = [bm.verts.new((x, y, z0)) for x, y in poly]
    rows = [base]
    for k in range(1, rings + 1):
        u = 1 - k / (rings + 1)          # radial fraction
        hz = z0 + h * math.sqrt(max(0.0, 1 - u ** 4)) if k > 0 else z0
        rows.append([bm.verts.new((cx + (x - cx) * u, cy + (y - cy) * u, hz)) for x, y in poly])
    top = bm.verts.new((cx, cy, z0 + h))
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(n):
            bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
    for i in range(n):
        bm.faces.new((rows[-1][i], rows[-1][(i + 1) % n], top))
    bm.faces.new(base[::-1])
    return new_obj(name, bm, material, smooth=80)


def blob_outline(r, seed, n=40, wob=((2, 0.12), (3, 0.14), (5, 0.06)), sx=1.0, sy=1.0):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in wob]
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1 + sum(amp * math.sin(f * a + p) for (f, amp), p in zip(wob, ph)))
        pts.append((rr * math.cos(a) * sx, rr * math.sin(a) * sy))
    return pts


def offset_poly(poly, d):
    """Offsets a counter-clockwise outline outwards by d (mitred, limited)."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        m = (n0 + n1)
        if m.length < 1e-6:
            m = n0
        m.normalize()
        k = d / max(0.35, m.dot(n0))
        q = p1 + m * k
        out.append((q.x, q.y))
    return out


# ------------------------------------------------------------------ the car

AX_F, AX_R = 0.60, -0.58      # axles
WR, WW, WY = 0.21, 0.19, 0.40  # wheel radius, width, centre |y|
X_NOSE, X_TAIL = 0.98, -0.95
ZM = 0.29                     # the widest line of the body
P_EXP = 3.0                   # superellipse exponent of the body section
ARCH_R = 0.262
SIDE_DISC = (-0.06, 0.27)      # (x, z) of the flank number discs


def plan_w(x):
    return interp([-0.95, -0.78, -0.58, -0.36, -0.08, 0.2, 0.42, 0.6, 0.8, 0.98],
                  [0.40, 0.465, 0.478, 0.455, 0.44, 0.44, 0.458, 0.475, 0.455, 0.37], x)


def end_round(x):
    rn, rt = 0.26, 0.2
    if x > X_NOSE - rn:
        u = (x - (X_NOSE - rn)) / rn
    elif x < X_TAIL + rt:
        u = ((X_TAIL + rt) - x) / rt
    else:
        return 1.0
    return math.sqrt(max(0.0, 1 - min(1.0, u) ** 2))


def z_bottom(x):
    return 0.125


def top_centre(x):
    return interp([-0.95, -0.7, -0.4, -0.15, 0.15, 0.45, 0.75, 0.98],
                  [0.385, 0.43, 0.45, 0.452, 0.45, 0.432, 0.41, 0.355], x)


def top_fender(x):
    b = 0.0
    for ax in (AX_F, AX_R):
        d = (x - ax) / 0.46
        if abs(d) < 1:
            b = max(b, math.cos(d * math.pi / 2) ** 2)
    return interp([-0.95, -0.6, 0.6, 0.98], [0.40, 0.455, 0.455, 0.37], x) + 0.085 * b


def top_at(x, t):
    """Top height at lateral fraction t = |y| / W."""
    hump = smoothstep(0.18, 0.74, t)
    return top_centre(x) + (top_fender(x) - top_centre(x)) * hump


def section(x, n=32):
    """The ring of body points at station x (a superellipse whose top follows the fender humps)."""
    e = end_round(x)
    W = plan_w(x) * max(e, 0.02)
    ev = max(e, 0.02) ** 0.6
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        y = W * math.copysign(abs(c) ** (2 / P_EXP), c)
        if s >= 0:
            T = top_at(x, min(1.0, abs(y) / max(W, 1e-6)))
            z = ZM + (T - ZM) * ev * abs(s) ** (2 / P_EXP)
        else:
            z = ZM - (ZM - z_bottom(x)) * ev * abs(s) ** (2 / P_EXP)
        pts.append(Vector((x, y, z)))
    return pts


SHELL = [None]   # a BVH tree of the finished body shell: decals and trim are draped on the real mesh


def surf_top(x, y):
    """The top surface height at (x, y)."""
    if SHELL[0]:
        hit = SHELL[0].ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)))
        if hit[0] is not None:
            return hit[0].z
    e = end_round(x)
    W = plan_w(x) * max(e, 0.02)
    ev = max(e, 0.02) ** 0.6
    t = min(1.0, abs(y) / W)
    c = t ** (P_EXP / 2)
    s = math.sqrt(max(0.0, 1 - c * c))
    return ZM + (top_at(x, t) - ZM) * ev * s ** (2 / P_EXP)


def surf_side(x, z):
    """|y| of the body side at (x, z)."""
    if SHELL[0]:
        hit = SHELL[0].ray_cast(Vector((x, 2.0, z)), Vector((0, -1, 0)))
        if hit[0] is not None:
            return hit[0].y
    e = end_round(x)
    W = plan_w(x) * max(e, 0.02)
    ev = max(e, 0.02) ** 0.6
    if z >= ZM:
        t = 1.0
        for _ in range(8):
            T = top_at(x, t)
            q = min(1.0, max(0.0, (z - ZM) / max(1e-4, (T - ZM) * ev)))
            s = q ** (P_EXP / 2)
            t = math.sqrt(max(0.0, 1 - s * s)) ** (2 / P_EXP)
        return W * t
    q = min(1.0, (ZM - z) / max(1e-4, (ZM - z_bottom(x)) * ev))
    s = q ** (P_EXP / 2)
    return W * math.sqrt(max(0.0, 1 - s * s)) ** (2 / P_EXP)


def frame_at(x, y):
    """Point and normal on the top surface at (x, y)."""
    h = 0.004
    p = Vector((x, y, surf_top(x, y)))
    dx = (surf_top(x + h, y) - surf_top(x - h, y)) / (2 * h)
    dy = (surf_top(x, y + h) - surf_top(x, y - h)) / (2 * h)
    return p, Vector((-dx, -dy, 1)).normalized()


def decal_top(poly, material, lift=0.004, name="decal", sub=1):
    """A flat 2D outline (x, y) draped on the top surface (fan-triangulated round its centre)."""
    bm = bmesh.new()
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    rings = []
    for k in range(sub + 1):
        u = (k + 1) / (sub + 1)
        rings.append([bm.verts.new((cx + (x - cx) * u, cy + (y - cy) * u, 0)) for x, y in poly])
    c = bm.verts.new((cx, cy, 0))
    n = len(poly)
    for i in range(n):
        bm.faces.new((c, rings[0][i], rings[0][(i + 1) % n]))
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((r0[i], r1[i], r1[(i + 1) % n], r0[(i + 1) % n]))
    for v in bm.verts:
        v.co.z = surf_top(v.co.x, v.co.y) + lift
    return raw_obj(name, bm, material, smooth=60)


def decal_side(poly, side, material, lift=0.004, name="decal", sub=1):
    """A flat 2D outline (x, z) draped on the body flank (side = +1 left / -1 right)."""
    bm = bmesh.new()
    cx = sum(p[0] for p in poly) / len(poly)
    cz = sum(p[1] for p in poly) / len(poly)
    rings = []
    for k in range(sub + 1):
        u = (k + 1) / (sub + 1)
        rings.append([bm.verts.new((cx + (x - cx) * u, 0, cz + (z - cz) * u)) for x, z in poly])
    c = bm.verts.new((cx, 0, cz))
    n = len(poly)
    for i in range(n):
        f = (c, rings[0][(i + 1) % n], rings[0][i])
        bm.faces.new(f if side > 0 else f[::-1])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            f = (r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i])
            bm.faces.new(f if side > 0 else f[::-1])
    for v in bm.verts:
        v.co.y = side * (surf_side(v.co.x, v.co.z) + lift)
    return raw_obj(name, bm, material, smooth=60)


def ring_decal(c, r0, r1, material, side=0, lift=0.006, n=28, name="ring"):
    """An annulus decal (radii r0 .. r1) on the top (side 0) or on a flank (side +-1)."""
    bm = bmesh.new()
    a_ = [bm.verts.new((c[0] + r0 * math.cos(2 * math.pi * k / n), c[1] + r0 * math.sin(2 * math.pi * k / n), 0))
          for k in range(n)]
    b_ = [bm.verts.new((c[0] + r1 * math.cos(2 * math.pi * k / n), c[1] + r1 * math.sin(2 * math.pi * k / n), 0))
          for k in range(n)]
    for k in range(n):
        f = (a_[k], b_[k], b_[(k + 1) % n], a_[(k + 1) % n])
        bm.faces.new(f[::-1] if side > 0 else f)
    for v in bm.verts:
        u, w = v.co.x, v.co.y
        if side == 0:
            v.co = Vector((u, w, surf_top(u, w) + lift))
        else:
            v.co = Vector((u, side * (surf_side(u, w) + lift), w))
    return raw_obj(name, bm, material, smooth=60)


def circle(c, r, n=24):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def body_shell(paint, dark):
    n_st = 40
    xs = []
    for k in range(n_st + 1):   # stations bunched towards the rounded ends
        u = k / n_st
        u = 0.5 * u + 0.5 * (0.5 - 0.5 * math.cos(math.pi * u))
        xs.append(X_TAIL + (X_NOSE - X_TAIL) * u)
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in section(x)] for x in xs]
    n = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    for ring, x in ((rings[0], xs[0]), (rings[-1], xs[-1])):
        c = bm.verts.new((x, 0, sum(v.co.z for v in ring) / n))
        for k in range(n):
            bm.faces.new((ring[k], ring[(k + 1) % n], c))
    shell = new_obj("shell", bm, paint, smooth=50)
    # cut the four wheel arches: cylinders across the flanks, their inner caps making the wheel wells
    cutters = []
    for ax in (AX_F, AX_R):
        for s in (1, -1):
            cutters.append(cyl(ARCH_R, 0.5, (ax, s * (0.27 + 0.25), WR), dark, rot=(R90, 0, 0), verts=40))
    cut = join(cutters, "cutter")
    m = shell.modifiers.new("arch", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = cut
    K.select(shell)
    bpy.ops.object.modifier_apply(modifier="arch")
    bpy.data.objects.remove(cut, do_unlink=True)
    set_mats(shell, [paint, dark])
    for f in shell.data.polygons:
        c = f.center
        for ax in (AX_F, AX_R):
            if math.hypot(c.x - ax, c.z - WR) < ARCH_R + 0.004 and abs(c.y) > 0.265:
                f.material_index = 1
    K.select(shell)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
    dg = bpy.context.evaluated_depsgraph_get()
    SHELL[0] = BVHTree.FromObject(shell, dg)
    return shell


def arch_lip(ax, side, material):
    pts = []
    for k in range(17):
        a = math.radians(-8 + 196 * k / 16)
        x = ax + ARCH_R * math.cos(a)
        z = WR + ARCH_R * math.sin(a)
        if z < z_bottom(x) + 0.03:
            continue
        pts.append((x, side * (surf_side(x, z) - 0.003), z))
    return tube(pts, [0.014] * len(pts), material, verts=5, caps=True, name="lip")


def car_wheel(x, side, tyre_m, hub_m, trim_m, chrome_m, name):
    """A chubby toy wheel, its axle along Y, the stamped tin face outwards (side +1: +Y)."""
    c = Vector((x, side * WY, WR))
    R = WR - 0.075
    parts = []
    ty = baked(torus(R, 0.075, (0, 0, 0), tyre_m, rot=(R90, 0, 0), verts=20, minor=6))
    ty.data.transform(Matrix.Diagonal((1, WW / 0.15, 1, 1)))
    ty.data.transform(Matrix.Translation(c))
    parts.append(ty)
    # a cream whitewall on the outer sidewall
    ww = baked(torus(R + 0.03, 0.022, (0, 0, 0), trim_m, rot=(R90, 0, 0), verts=22, minor=4))
    ww.data.transform(Matrix.Translation(c + Vector((0, side * (WW * 0.5 - 0.012), 0)))
                      @ Matrix.Diagonal((1, 0.5, 1, 1)))
    parts.append(ww)
    # the pressed tin hub: a dished disc, a raised ring, six stamped spokes and a domed cap
    o = side
    hub = lathe_r([(0.0, 0.0), (R * 0.98, 0.0), (R * 0.98, 0.012), (R * 0.82, 0.028), (R * 0.55, 0.03), (0.0, 0.03)],
                  hub_m, segs=18, name="hub", smooth=40)
    ring = torus(R * 0.72, 0.011, (0, 0, 0.03), trim_m, verts=16, minor=4)
    cap = lathe_r([(0.0, 0.075), (0.02, 0.072), (0.04, 0.06), (0.05, 0.04), (0.05, 0.028), (0.0, 0.028)],
                  chrome_m, segs=12, name="cap", smooth=50)
    spokes = []
    for k in range(6):
        a = 2 * math.pi * k / 6
        spokes.append(rod((0.055 * math.cos(a), 0.055 * math.sin(a), 0.033),
                          (R * 0.66 * math.cos(a), R * 0.66 * math.sin(a), 0.033), 0.011, chrome_m, verts=5))
    face = join([hub, ring, cap] + spokes, "hubface")
    # local +Z of the face points outwards (side * Y)
    face.data.transform(Matrix.Translation(c + Vector((0, o * (WW * 0.5 - 0.045), 0)))
                        @ Matrix.Rotation(-o * R90, 4, "X"))
    parts.append(face)
    return join(parts, name, pivot=c)


def car():
    paint = mat("car_paint", (0.86, 0.1, 0.07), 0.26, metal=0.25, coat=0.9)
    trim = mat("car_trim", (0.97, 0.9, 0.72), 0.35, coat=0.6)
    chrome = mat("car_chrome", (0.92, 0.92, 0.95), 0.12, metal=1.0)
    number = mat("car_number", (0.97, 0.96, 0.92), 0.4, coat=0.6)
    glow = mat("car_glow", (1.0, 0.95, 0.75), 0.2, emit=5.0)
    tail = mat("car_tail_glow", (1.0, 0.12, 0.06), 0.3, emit=2.5)
    glass = mat("car_glass", (0.55, 0.75, 0.85), 0.05, coat=1.0, alpha=0.45)
    dark = mat("car_dark", (0.05, 0.05, 0.06), 0.7)
    driver_m = mat("car_driver", (0.95, 0.95, 0.92), 0.6)
    skin = mat("car_skin", (0.96, 0.72, 0.56), 0.6)
    cap_m = mat("car_cap", (0.42, 0.22, 0.1), 0.5, coat=0.5)
    goggle = mat("car_goggle", (0.3, 0.6, 0.75), 0.05, metal=0.3, coat=1.0)
    scarf = mat("car_scarf", (1.0, 0.82, 0.1), 0.6)
    brass = mat("car_brass", (0.95, 0.72, 0.28), 0.22, metal=1.0)
    tyre_m = mat("car_tyre", (0.05, 0.05, 0.055), 0.8)
    hub_m = mat("car_hub", (0.82, 0.83, 0.86), 0.25, metal=0.9)

    parts = [body_shell(paint, dark)]
    # the lithographed belt line along each flank, broken by the wheel arches
    for s in (1, -1):
        seg = []
        xs = [X_TAIL + 0.16 + k * 0.045 for k in range(int((X_NOSE - 0.2 - X_TAIL - 0.16) / 0.045) + 1)]
        for x in xs:
            z = ZM + 0.075
            inside = any(math.hypot(x - ax, z - WR) < ARCH_R + 0.03 for ax in (AX_F, AX_R)) or \
                math.hypot(x - SIDE_DISC[0], z - SIDE_DISC[1]) < 0.142
            if inside:
                if len(seg) > 1:
                    parts.append(tube(seg, [0.012] * len(seg), trim, verts=6, caps=True, name="belt"))
                seg = []
                continue
            seg.append((x, s * (surf_side(x, z) + 0.002), z))
        if len(seg) > 1:
            parts.append(tube(seg, [0.012] * len(seg), trim, verts=6, caps=True, name="belt"))
        for ax in (AX_F, AX_R):
            parts.append(arch_lip(ax, s, trim))
    # twin bonnet and tail stripes, the bonnet number disc
    for y in (-0.075, 0.075):
        for x0, x1 in ((0.7, 0.93), (0.13, 0.42), (-0.9, -0.62)):
            n = max(2, int((x1 - x0) / 0.04))
            poly = [(x0 + (x1 - x0) * k / n, y - 0.022) for k in range(n + 1)] + \
                   [(x1 - (x1 - x0) * k / n, y + 0.022) for k in range(n + 1)]
            parts.append(decal_top(poly, trim, 0.005, "stripe", sub=1))
    bon = Vector((0.56, 0.0))
    parts.append(ring_decal(bon, 0.112, 0.132, dark, 0, 0.012))
    parts.append(decal_top(circle(bon, 0.115, 28), number, 0.011, "disc", sub=2))
    # the flank number discs
    for s in (1, -1):
        c = SIDE_DISC
        parts.append(ring_decal(c, 0.102, 0.122, dark, s, 0.012))
        parts.append(decal_side(circle(c, 0.105, 28), s, number, 0.01, "disc", sub=2))
        # pressed louvres behind the front wheel
        for k in range(4):
            x = 0.2 - k * 0.055
            poly = [(x - 0.012, 0.25), (x + 0.012, 0.25), (x + 0.012, 0.36), (x - 0.012, 0.36)]
            parts.append(decal_side(poly, s, dark, 0.003, "louvre"))
    # the cockpit: a dark opening with a padded chrome-edged rim
    cp = Vector((-0.2, 0.0))
    opening = [(cp.x + 0.24 * math.cos(a) * (1.0 if math.cos(a) < 0 else 0.85), cp.y + 0.2 * math.sin(a))
               for a in (2 * math.pi * k / 24 for k in range(24))]
    parts.append(decal_top(opening, dark, 0.004, "cockpit", sub=1))
    rim = [Vector((x, y, surf_top(x, y) + 0.012)) for x, y in opening + opening[:1]]
    parts.append(tube(rim, [0.014] * len(rim), cap_m, verts=5, caps=False, name="rim"))
    # the headrest fairing behind the driver
    fair = []
    for k in range(10):
        u = k / 9
        x = -0.45 - 0.42 * u
        w = 0.1 * (1 - 0.5 * u)
        hgt = 0.13 * (1 - u ** 1.8)
        base = surf_top(x, 0)
        fair.append([(x, w * math.cos(a), base - 0.02 + max(0.0, math.sin(a)) * hgt + 0.0 * math.sin(a))
                     for a in (2 * math.pi * j / 14 for j in range(14))])
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in r] for r in fair]
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(14):
            bm.faces.new((r0[j], r0[(j + 1) % 14], r1[(j + 1) % 14], r1[j]))
    c0 = bm.verts.new(Vector(fair[0][0]) * 0 + Vector((fair[0][0][0] + 0.01, 0, surf_top(-0.45, 0) + 0.06)))
    for j in range(14):
        bm.faces.new((rings[0][(j + 1) % 14], rings[0][j], c0))
    parts.append(new_obj("fairing", bm, paint, smooth=60))
    # the wrap-round windscreen with a chrome frame
    gl = []
    nv, nu = 4, 12
    for i in range(nv + 1):
        v = i / nv
        row = []
        for j in range(nu + 1):
            u = -1 + 2 * j / nu
            y = 0.22 * u
            x = 0.06 - 0.09 * u * u - 0.07 * v
            z = surf_top(x, y) - 0.012 + 0.15 * v - 0.025 * u * u * v
            row.append((x, y, z))
        gl.append(row)
    g = grid_obj(gl, glass, "screen", smooth=70)
    set_mats(g, [two_sided(glass)])
    parts.append(g)
    parts.append(tube(gl[-1], [0.011] * len(gl[-1]), chrome, verts=6, caps=True, name="frame"))
    for j in (0, nu):
        col = [gl[i][j] for i in range(nv + 1)]
        parts.append(tube(col, [0.011] * len(col), chrome, verts=6, caps=True, name="frame"))
    # the driver: shoulders in white overalls, a cheery face, leather cap with ear flaps, goggles, a flying scarf
    hx, hz = -0.2, 0.615
    parts.append(ell((-0.22, 0, 0.47), (0.12, 0.16, 0.09), driver_m, segs=14, rings=8))
    for s in (1, -1):   # arms reaching to the wheel
        parts.append(tube([(-0.2, s * 0.13, 0.5), (-0.1, s * 0.15, 0.47), (-0.02, s * 0.08, 0.5)],
                          [0.04, 0.035, 0.03], driver_m, verts=8, caps=True, name="arm"))
        parts.append(sphere(0.03, (-0.01, s * 0.075, 0.505), cap_m, segs=8, rings=5))   # gloves
    parts.append(torus(0.075, 0.012, (0.0, 0, 0.51), dark, rot=(0, math.radians(-60), 0), verts=18, minor=5))
    parts.append(cyl(0.05, 0.05, (hx, 0, 0.535), skin, verts=12))   # neck
    parts.append(sphere(0.085, (hx, 0, hz), skin, segs=14, rings=9))
    parts.append(sphere(0.018, (hx + 0.085, 0, hz - 0.01), skin, segs=8, rings=5))   # nose
    for s in (1, -1):
        parts.append(sphere(0.016, (hx + 0.07, s * 0.045, hz - 0.03), mat("car_cheek", (1.0, 0.5, 0.45), 0.6),
                            scale=(0.6, 1, 0.8), segs=6, rings=4))
    smile = [(hx + 0.083 * math.cos(math.radians(a * 0.8)) , 0.085 * math.sin(math.radians(a)) * 0.45,
              hz - 0.042 - 0.012 * math.cos(math.radians(a * 1.5))) for a in (-60, -30, 0, 30, 60)]
    parts.append(tube(smile, [0.005, 0.006, 0.0065, 0.006, 0.005], dark, verts=5, caps=True, name="smile"))
    capo = hemi(0.093, (hx - 0.004, 0, hz + 0.005), (0.25, 0, 1), cap_m, cut=-0.15, segs=16, rings=10)
    parts.append(capo)
    for s in (1, -1):   # ear flaps and the buckle strap
        parts.append(ell((hx - 0.01, s * 0.082, hz - 0.03), (0.04, 0.018, 0.055), cap_m, segs=8, rings=5))
    parts.append(tube([(hx - 0.09 * math.cos(a), 0.09 * math.sin(a) * 1.02, hz + 0.035) for a in
                       (math.radians(d) for d in range(-120, 121, 40))], [0.009] * 7, dark, verts=5, caps=True,
                      name="strap"))
    for s in (1, -1):   # goggles pushed up on the cap's brow
        gc = Vector((hx + 0.07, s * 0.036, hz + 0.045))
        rg = torus(0.026, 0.008, gc, chrome, rot=(0, math.radians(70), 0), verts=14, minor=5)
        lens = sphere(0.025, gc + Vector((0.004, 0, 0.0)), goggle, scale=(0.45, 1, 1), segs=10, rings=6)
        lens.data.transform(Matrix.Translation(gc) @ Matrix.Rotation(math.radians(-20), 4, "Y")
                            @ Matrix.Translation(-gc))
        parts += [rg, lens]
    sc = [(hx - 0.04, 0.0, 0.54), (hx - 0.14, 0.03, 0.55), (hx - 0.26, -0.02, 0.57), (hx - 0.38, 0.05, 0.58),
          (hx - 0.48, 0.02, 0.6)]
    parts.append(tube(sc, [0.03, 0.028, 0.026, 0.022, 0.018], scarf, verts=8, caps=True, name="scarf"))
    parts.append(torus(0.06, 0.024, (hx, 0, 0.55), scarf, verts=12, minor=5))
    # the nose: an oval chrome grille with bars, chrome bumpers front and back
    gx = X_NOSE - 0.035
    parts.append(ell((gx, 0, 0.265), (0.05, 0.13, 0.075), dark, segs=14, rings=6))
    gr = baked(torus(0.1, 0.014, (0, 0, 0), chrome, rot=(0, R90, 0), verts=20, minor=5))
    gr.data.transform(Matrix.Translation((gx + 0.03, 0, 0.265)) @ Matrix.Diagonal((1, 1.3, 0.75, 1)))
    parts.append(gr)
    for k in range(-3, 4):
        y = k * 0.034
        hgt = 0.072 * math.sqrt(max(0.0, 1 - (y / 0.13) ** 2))
        parts.append(rod((gx + 0.035, y, 0.265 - hgt), (gx + 0.035, y, 0.265 + hgt), 0.008, chrome, verts=6))

    def plan_x(y, front):
        lo, hi = (0.5, X_NOSE) if front else (X_TAIL, -0.5)
        for _ in range(30):
            mid = (lo + hi) / 2
            inside = plan_w(mid) * end_round(mid) > abs(y)
            if front:
                lo, hi = (mid, hi) if inside else (lo, mid)
            else:
                lo, hi = (lo, mid) if inside else (mid, hi)
        return (lo + hi) / 2

    for front in (True, False):
        pts = []
        for k in range(11):
            y = -0.31 + 0.62 * k / 10
            x = plan_x(y, front)
            pts.append((x + (0.045 if front else -0.045), y * 1.04, 0.17))
        parts.append(tube(pts, [0.026] * len(pts), chrome, verts=8, caps=True, name="bumper"))
        for s in (1, -1):   # overriders and their brackets
            y = 0.22 * s
            x = plan_x(y, front) + (0.05 if front else -0.05)
            parts.append(rod((x, y, 0.13), (x, y, 0.235), 0.022, chrome, r2=0.016, verts=10))
            parts.append(sphere(0.017, (x, y, 0.235), chrome, segs=8, rings=4))
    # headlights in the fronts of the wings, tail lamps behind
    for s in (1, -1):
        y = 0.3 * s
        x = plan_x(y, True)
        z = 0.38
        lp = Vector((x - 0.035, y, z - 0.02))
        parts.append(sphere(0.052, lp + Vector((0.025, 0, 0)), glow, scale=(0.55, 1, 1), segs=12, rings=7))
        parts.append(torus(0.052, 0.012, lp + Vector((0.026, 0, 0)), chrome, rot=(0, R90, 0), verts=12, minor=4))
        y = 0.3 * s
        x = plan_x(y, False)
        parts.append(sphere(0.035, (x + 0.02, y, 0.32), tail, scale=(0.5, 1, 1.25), segs=10, rings=6))
    # side exhausts with fishtails
    for s in (1, -1):
        pts = []
        for k in range(9):
            x = 0.3 - 0.62 * k / 8
            pts.append((x, s * (surf_side(x, 0.17) + 0.035), 0.165))
        pts.insert(0, (0.36, s * (surf_side(0.33, 0.2) - 0.01), 0.2))
        parts.append(tube(pts, [0.026] * len(pts), chrome, verts=10, caps=False, name="exhaust"))
        x = pts[-1][0]
        parts.append(cyl(0.032, 0.05, (x - 0.02, pts[-1][1], 0.165), chrome, rot=(0, R90, 0), r2=0.04, verts=12))
        parts.append(cyl(0.022, 0.052, (x - 0.02, pts[-1][1], 0.165), dark, rot=(0, R90, 0), verts=10))
    # the tin tabs that hold the shell to its base plate (folded through slots, unpainted)
    for s in (1, -1):
        for x in (-0.25, 0.1):
            parts.append(box((0.05, 0.012, 0.035), (x, s * (surf_side(x, 0.15) + 0.004), 0.15), chrome, bevel=0.0))
    parts.append(box((1.5, 0.6, 0.02), (0.0, 0, 0.115), dark, bevel=0.0))   # the base plate
    # filler cap on the tail
    fx = -0.66
    fp, fn = frame_at(fx, 0.2)
    parts.append(cyl(0.035, 0.02, fp + fn * 0.008, chrome, verts=14))

    # the wind-up key: a brass shaft out of the tail and a two-lobed bow (pivot on the shaft's axis)
    kx, kz = -0.93, 0.31
    kp = []
    kp.append(rod((kx + 0.02, 0, kz), (kx - 0.13, 0, kz), 0.018, brass, verts=10))
    kp.append(cyl(0.032, 0.02, (kx - 0.02, 0, kz), brass, rot=(0, R90, 0), verts=14, bevel=0.005))
    for s in (1, -1):
        c = (kx - 0.17, 0, kz + s * 0.075)
        kp.append(torus(0.056, 0.016, c, brass, rot=(0, R90, 0), verts=16, minor=5))
        kp.append(cyl(0.05, 0.012, c, brass, rot=(0, R90, 0), verts=16))
    kp.append(box((0.03, 0.03, 0.1), (kx - 0.17, 0, kz), brass, bevel=0.008))
    key = join(kp, "key", pivot=(kx, 0, kz))

    wheels = [car_wheel(AX_F, 1, tyre_m, hub_m, trim, chrome, "wheel_fl"),
              car_wheel(AX_F, -1, tyre_m, hub_m, trim, chrome, "wheel_fr"),
              car_wheel(AX_R, 1, tyre_m, hub_m, trim, chrome, "wheel_rl"),
              car_wheel(AX_R, -1, tyre_m, hub_m, trim, chrome, "wheel_rr")]
    SHELL[0] = None
    root = join(parts, "car")
    export(root, "car", [(w, root) for w in wheels] + [(key, root)])


# ------------------------------------------------------------------ dressing helpers

def paint_by(o, materials, pick):
    """Gives each face of o a material index from pick(face_centre) into materials."""
    set_mats(o, materials)
    for f in o.data.polygons:
        f.material_index = pick(f.center)
    return o


def extrude_x(poly, x0, x1, material, name="ex", smooth=0):
    """A 2D outline (y, z) extruded along X from x0 to x1 (any winding)."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in poly]
    b = [bm.verts.new((x1, y, z)) for y, z in poly]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return new_obj(name, bm, material, smooth=smooth)


def ring_slab(outer, inner, z0, z1, material, name="ringslab"):
    """A flat slab with a hole: outer and inner outlines (x, y), the same number of points, counter-clockwise."""
    bm = bmesh.new()
    n = len(outer)
    ot = [bm.verts.new((x, y, z1)) for x, y in outer]
    ob = [bm.verts.new((x, y, z0)) for x, y in outer]
    it = [bm.verts.new((x, y, z1)) for x, y in inner]
    ib = [bm.verts.new((x, y, z0)) for x, y in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((it[i], ot[i], ot[j], it[j]))
        bm.faces.new((ib[j], ob[j], ob[i], ib[i]))
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
    return raw_obj(name, bm, material, smooth=30)


def wave_flag(x0, x1, z0, z1, nx, nz, mats, pick, amp=0.05, waves=1.2, droop=0.04, name="flag"):
    """A cloth hanging off a pole at x0: a grid in the XZ plane rippling in Y, its quads coloured by pick(i, j)."""
    grid = []
    for i in range(nz + 1):
        z = z1 - (z1 - z0) * i / nz
        row = []
        for j in range(nx + 1):
            u = j / nx
            x = x0 + (x1 - x0) * u
            y = amp * math.sin(2 * math.pi * waves * u - 0.4 + 0.6 * i / nz) * u ** 0.8
            row.append((x, y, z - droop * u * u * (0.5 + i / nz)))
        grid.append(row)
    o = grid_obj(grid, mats[0], name, smooth=80)
    set_mats(o, [two_sided(m) for m in mats])
    k = 0
    for i in range(nz):
        for j in range(nx):
            o.data.polygons[k].material_index = pick(i, j)
            k += 1
    return o


# ------------------------------------------------------------------ small track-side props

def cone():
    orange = mat("cone_orange", (1.0, 0.36, 0.04), 0.35, coat=0.6)
    white = mat("cone_white", (0.97, 0.96, 0.92), 0.3, coat=0.6)
    base_m = mat("cone_base", (0.14, 0.13, 0.14), 0.6)
    parts = [box((0.36, 0.36, 0.045), (0, 0, 0.0225), base_m, bevel=0.014)]
    hs = [0.52, 0.505, 0.4, 0.34, 0.24, 0.18, 0.06, 0.045]

    def r(h):
        return 0.028 + (0.128 - 0.028) * (0.505 - h) / (0.505 - 0.06)
    prof = [(0.0, 0.52), (0.02, 0.518)] + [(r(h), h) for h in hs[1:-1]] + [(0.134, 0.045), (0.0, 0.045)]
    body = lathe_r(prof, orange, segs=20, name="cone", smooth=50)
    paint_by(body, [orange, white], lambda c: 1 if (0.34 < c.z < 0.4 or 0.18 < c.z < 0.24) else 0)
    parts.append(body)
    K.simple(parts, "cone")


def tyre_stack():
    rubber = mat("tyre_rubber", (0.06, 0.06, 0.065), 0.8)
    paint = mat("tyre_paint", (0.96, 0.95, 0.9), 0.5)
    red = mat("tyre_paint_red", (0.88, 0.12, 0.08), 0.5)
    rnd = random.Random(31)
    parts = []
    for k in range(3):
        zc = 0.085 + 0.17 * k
        c = Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), zc))
        t = torus(0.245, 0.11, (0, 0, 0), rubber, verts=24, minor=8)
        t.data.transform(Matrix.Translation(c) @ Matrix.Diagonal((1, 1, 0.78, 1)))
        paint_by(t, [rubber, paint, red], lambda p, c=c, k=k: (0 if k == 1 else (1 if k == 0 else 2)) if (
            Vector((p.x - c.x, p.y - c.y)).length > 0.32 and abs(p.z - c.z) < 0.04) else 0)
        parts.append(t)
        # a painted white sidewall ring on the middle tyre
        if k == 1:
            parts.append(torus(0.245, 0.035, (c.x, c.y, zc + 0.075), paint, verts=24, minor=4, scale=(1, 1, 0.3)))
    K.simple(parts, "tyre_stack")


def hay_bale():
    straw = mat("hay_straw", (0.9, 0.66, 0.2), 0.85)
    straw2 = mat("hay_straw_light", (1.0, 0.82, 0.38), 0.8)
    straw3 = mat("hay_straw_dark", (0.72, 0.5, 0.15), 0.9)
    twine = mat("hay_twine", (0.55, 0.22, 0.1), 0.7)
    L, W, H = 1.1, 0.56, 0.46
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=5, use_grid_fill=True)
    rnd = random.Random(7)
    for v in bm.verts:
        p = v.co
        q = Vector((math.copysign(min(1, abs(p.x) * 2) ** 6, p.x), math.copysign(min(1, abs(p.y) * 2) ** 6, p.y),
                    math.copysign(min(1, abs(p.z) * 2) ** 6, p.z)))
        p.x *= L
        p.y *= W
        p.z = (p.z + 0.5) * H
        # round the edges a little and rough up the straw
        p.x -= 0.03 * q.x * (abs(q.y) + abs(q.z) > 1.2)
        p += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.012
        p.z = max(0.0, p.z)
    o = new_obj("bale", bm, straw, smooth=25)
    K.finish(o, straw, bevel=0.03, segs=2, smooth=40)
    # speckle the faces in three straw tones, in streaks along the bale
    set_mats(o, [straw, straw2, straw3])
    for f in o.data.polygons:
        h = math.sin(f.center.z * 61.0 + math.sin(f.center.x * 7.0) * 2.0) + math.sin(f.center.y * 43.0) * 0.6
        f.material_index = 1 if h > 0.7 else (2 if h < -0.9 else 0)
    parts = [o]
    for x in (-0.28, 0.28):
        pts = [(x, -W / 2 - 0.008, 0.02), (x, -W / 2 - 0.008, H + 0.008), (x, W / 2 + 0.008, H + 0.008),
               (x, W / 2 + 0.008, 0.02)]
        dense = []
        for a, b in zip(pts, pts[1:]):
            for k in range(6):
                dense.append(Vector(a).lerp(Vector(b), k / 6))
        dense.append(Vector(pts[-1]))
        parts.append(tube(dense, [0.012] * len(dense), twine, verts=5, caps=True, name="twine"))
    for k in range(18):   # loose tufts poking out
        side = rnd.choice(("top", "front", "back", "end"))
        if side == "top":
            p = Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.25, 0.25), H))
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.6))
        elif side == "end":
            sx = rnd.choice((-1, 1))
            p = Vector((sx * L / 2, rnd.uniform(-0.24, 0.24), rnd.uniform(0.08, H - 0.05)))
            d = Vector((sx, rnd.uniform(-0.6, 0.6), rnd.uniform(-0.3, 0.6)))
        else:
            sy = 1 if side == "back" else -1
            p = Vector((rnd.uniform(-0.5, 0.5), sy * W / 2, rnd.uniform(0.08, H - 0.05)))
            d = Vector((rnd.uniform(-0.7, 0.7), sy, rnd.uniform(-0.3, 0.6)))
        d.normalize()
        parts.append(rod(p - d * 0.02, p + d * rnd.uniform(0.06, 0.11), 0.012, rnd.choice((straw, straw2)), r2=0.0,
                         verts=4))
    K.simple(parts, "hay_bale")


def barrier():
    red = mat("barrier_red", (0.86, 0.08, 0.06), 0.3, metal=0.3, coat=0.7)
    white = mat("barrier_white", (0.96, 0.95, 0.92), 0.3, metal=0.2, coat=0.7)
    post = mat("barrier_post", (0.62, 0.64, 0.68), 0.35, metal=0.8)
    bolt = mat("barrier_bolt", (0.85, 0.85, 0.88), 0.2, metal=1.0)
    zc = 0.42
    ys = [0, -0.028, -0.04, -0.028, 0.0, -0.028, -0.04, -0.028, 0.0]
    zs = [-0.12 + 0.03 * k for k in range(9)]
    prof = [(y - 0.06, z) for y, z in zip(ys, zs)] + [(y - 0.06 + 0.022, z) for y, z in reversed(list(zip(ys, zs)))]
    parts = []
    for k in range(4):
        x0, x1 = -1.0 + 0.5 * k, -0.5 + 0.5 * k
        st = [(x0 + (x1 - x0) * j / 4, 1, 1, zc) for j in range(5)]
        parts.append(loft_x(prof, st, red if k % 2 == 0 else white, cap_start=True, cap_end=True, name="rail",
                            smooth=0))
    for x in (-0.5, 0.5):
        parts.append(box((0.07, 0.07, 0.58), (x, 0.06, 0.29), post, bevel=0.01))
        parts.append(box((0.05, 0.08, 0.14), (x, -0.005, zc), post, bevel=0.01))   # spacer block
        parts.append(box((0.16, 0.16, 0.02), (x, 0.06, 0.01), post, bevel=0.005))   # foot plate
        for dz in (-0.06, 0.06):
            parts.append(sphere(0.014, (x, -0.1, zc + dz), bolt, scale=(1, 0.6, 1), segs=8, rings=4))
    K.simple(parts, "barrier")


# ------------------------------------------------------------------ grandstand

def grandstand():
    wall = mat("stand_wall", (0.95, 0.93, 0.86), 0.5, coat=0.3)
    trim = mat("stand_trim", (0.12, 0.32, 0.72), 0.4, coat=0.4)
    seat = mat("stand_seat", (0.2, 0.55, 0.9), 0.4, coat=0.4)
    postm = mat("stand_post", (0.85, 0.86, 0.9), 0.3, metal=0.8)
    roof_r = mat("stand_roof_red", (0.88, 0.12, 0.1), 0.45, coat=0.4)
    roof_w = mat("stand_roof_white", (0.97, 0.96, 0.92), 0.45, coat=0.4)
    board = [mat("stand_board_yellow", (1.0, 0.8, 0.12), 0.4, coat=0.5),
             mat("stand_board_green", (0.15, 0.6, 0.3), 0.4, coat=0.5)]
    flags = [two_sided(mat("stand_flag_%s" % n, c, 0.6)) for n, c in
             (("yellow", (1.0, 0.82, 0.1)), ("blue", (0.15, 0.4, 0.95)), ("green", (0.2, 0.75, 0.3)))]
    shirts = [mat("fan_%d" % k, c, 0.6) for k, c in enumerate(
        ((0.9, 0.15, 0.12), (0.15, 0.4, 0.9), (1.0, 0.8, 0.15), (0.2, 0.7, 0.35), (0.95, 0.5, 0.1),
         (0.6, 0.25, 0.75), (0.95, 0.95, 0.92), (0.1, 0.65, 0.75)))]
    skins = [mat("fan_skin_%d" % k, c, 0.6) for k, c in enumerate(
        ((0.98, 0.78, 0.62), (0.82, 0.58, 0.4), (0.52, 0.34, 0.22)))]
    hat = mat("fan_hat", (0.95, 0.9, 0.7), 0.6)
    X = 4.0
    parts = []
    tiers = 4
    tz = [0.42 + 0.44 * i for i in range(tiers)]
    ty = [-1.42 + 0.7 * i for i in range(tiers)]
    for i in range(tiers):
        parts.append(box((2 * X - 0.2, 1.68 - (ty[i] + 1.42) + 1.42 - 0.0, tz[i]),
                         (0, (ty[i] + 1.62) / 2, tz[i] / 2), wall, bevel=0.02))
        parts.append(box((2 * X - 0.24, 0.3, 0.06), (0, ty[i] + 0.2, tz[i] + 0.03), seat, bevel=0.015))
        parts.append(box((2 * X - 0.22, 0.03, 0.05), (0, ty[i] - 0.005, tz[i] - 0.06), trim, bevel=0.0))
    # stepped side walls and the back wall
    top = 2.6
    step = [(-1.62, 0.0), (1.62, 0.0), (1.62, top), (ty[3] + 0.3, top), (ty[3] + 0.3, tz[3] + 0.3)]
    for i in range(tiers - 1, 0, -1):
        step += [(ty[i], tz[i] + 0.3), (ty[i], tz[i - 1] + 0.3)]
    step += [(-1.62, tz[0] + 0.3)]
    for sx in (-1, 1):
        parts.append(extrude_x(step, sx * X - 0.06, sx * X + 0.06, wall, "side"))
    parts.append(box((2 * X, 0.12, top), (0, 1.62, top / 2), wall, bevel=0.02))
    parts.append(box((2 * X + 0.02, 0.14, 0.14), (0, 1.62, top - 0.05), trim, bevel=0.02))
    # the front wall with coloured boards
    n_b = 8
    for k in range(n_b):
        x = -X + (k + 0.5) * 2 * X / n_b
        parts.append(box((2 * X / n_b - 0.06, 0.08, 0.36), (x, -1.66, 0.3), board[k % 2], bevel=0.015))
    parts.append(box((2 * X, 0.1, 0.12), (0, -1.64, 0.06), trim, bevel=0.01))
    # the spectators, peg people with round heads, some cheering
    rnd = random.Random(2031)
    for i in range(tiers):
        x = -X + 0.3
        while x < X - 0.25:
            if rnd.random() > 0.14:
                sh = rnd.choice(shirts)
                sk = rnd.choice(skins)
                y = ty[i] + 0.3 + rnd.uniform(-0.03, 0.03)
                z = tz[i] + 0.06
                parts.append(ell((x, y, z + 0.2), (0.13, 0.1, 0.21), sh, segs=8, rings=5))
                parts.append(sphere(0.1, (x, y - 0.01, z + 0.5), sk, segs=8, rings=5))
                r = rnd.random()
                if r < 0.3:
                    parts.append(cyl(0.105, 0.05, (x, y - 0.01, z + 0.58), hat, verts=8, r2=0.08))
                if r > 0.62:   # cheering: arms up
                    for s in (-1, 1):
                        parts.append(rod((x + s * 0.09, y, z + 0.32), (x + s * 0.17, y - 0.05, z + 0.6), 0.032, sh,
                                         verts=5))
                elif r > 0.45:   # waving a little flag
                    parts.append(rod((x + 0.1, y, z + 0.3), (x + 0.16, y - 0.06, z + 0.68), 0.01, postm, verts=4))
                    parts.append(K.prism([(0, 0), (0.16, -0.05), (0, -0.1)], 0.012, (x + 0.16, y - 0.06, z + 0.68),
                                         rnd.choice(flags), bevel=0.0))
            x += 0.47 + rnd.uniform(-0.04, 0.05)
    # the canopy: posts at the back, a striped roof leaning forward, a scalloped valance
    for x in (-3.85, -1.3, 1.3, 3.85):
        parts.append(box((0.1, 0.1, 3.6), (x, 1.62, 1.8), postm, bevel=0.01))
        parts.append(rod((x, 1.6, 2.7), (x, 0.8, 3.48), 0.035, postm, verts=6))   # brace
    y0, y1, z0, z1 = 0.6, 1.8, 3.45, 3.7
    n_s = 16
    for k in range(n_s):
        x0 = -X - 0.15 + (2 * X + 0.3) * k / n_s
        x1 = -X - 0.15 + (2 * X + 0.3) * (k + 1) / n_s
        m = roof_r if k % 2 == 0 else roof_w
        parts.append(extrude_x([(y0, z0), (y1, z1), (y1, z1 + 0.06), (y0, z0 + 0.06)], x0, x1, m, "roof"))
        # the scallop under the front edge
        sc = K.prism([(-0.5, 0), (0.5, 0)] + [(0.5 * math.cos(a), -0.22 * math.sin(a)) for a in
                                              (math.pi * j / 8 for j in range(1, 8))], 0.03,
                     ((x0 + x1) / 2, y0 + 0.01, z0 + 0.01), m, bevel=0.0, scale=(x1 - x0))
        parts.append(sc)
    # pennants on top of the canopy
    for k, x in enumerate((-3.0, 0.0, 3.0)):
        parts.append(rod((x, 1.3, z1 - 0.05), (x, 1.3, z1 + 0.85), 0.025, postm, verts=6))
        parts.append(sphere(0.04, (x, 1.3, z1 + 0.87), roof_r, segs=8, rings=5))
        pen = wave_flag(x + 0.02, x + 0.62, z1 + 0.5, z1 + 0.82, 6, 2, [flags[k]], lambda i, j: 0, amp=0.04,
                        waves=1.0, droop=0.0, name="pennant")
        for v in pen.data.vertices:   # taper to a point
            u = (v.co.x - x - 0.02) / 0.6
            zc = z1 + 0.66
            v.co.z = zc + (v.co.z - zc) * (1 - 0.92 * u)
            v.co.y += 1.3
        parts.append(pen)
    K.simple(parts, "grandstand")


# ------------------------------------------------------------------ start gantry

def start_gantry():
    red = mat("gantry_red", (0.88, 0.1, 0.08), 0.35, metal=0.2, coat=0.6)
    white = mat("gantry_white", (0.96, 0.96, 0.94), 0.35, coat=0.6)
    black = mat("gantry_black", (0.05, 0.05, 0.06), 0.4, coat=0.5)
    frame = mat("gantry_frame", (0.16, 0.17, 0.2), 0.4, metal=0.6)
    base_m = mat("gantry_base", (0.5, 0.52, 0.56), 0.6)
    glow = mat("gantry_glow", (1.0, 0.15, 0.08), 0.25, emit=4.0)
    parts = []
    for sx in (-1, 1):
        x = sx * 5.0
        parts.append(box((0.7, 0.8, 0.2), (x, 0, 0.1), base_m, bevel=0.03))
        for k in range(9):
            parts.append(box((0.4, 0.5, 0.5), (x, 0, 0.2 + 0.25 + 0.5 * k), red if k % 2 == 0 else white,
                             bevel=0.012))
        parts.append(box((0.5, 0.6, 0.08), (x, 0, 4.72), frame, bevel=0.02))
        parts.append(sphere(0.12, (x, 0, 4.86), red, segs=10, rings=6))
    # the beam: chequered on both faces
    bx0, bx1, bz0, bz1, bd = -4.8, 4.8, 3.3, 4.1, 0.24
    parts.append(box((bx1 - bx0, 2 * bd - 0.02, bz1 - bz0), (0, 0, (bz0 + bz1) / 2), black, bevel=0.0))
    nx, nz = 48, 4
    for sy in (-1, 1):
        grid = [[(bx0 + (bx1 - bx0) * j / nx, sy * bd, bz1 - (bz1 - bz0) * i / nz) for j in range(nx + 1)]
                for i in range(nz + 1)]
        g = grid_obj(grid, white, "chequer", smooth=0)
        set_mats(g, [white, black])
        for k, f in enumerate(g.data.polygons):
            i, j = divmod(k, nx)
            f.material_index = (i + j) % 2
        if sy < 0:
            g.data.flip_normals()
        parts.append(g)
    for z in (bz0, bz1):
        parts.append(box((bx1 - bx0 + 0.1, 2 * bd + 0.08, 0.08), (0, 0, z), white, bevel=0.02))
    # the lamp bar under the beam, five lamps lit from both faces
    parts.append(box((4.3, 0.36, 0.5), (0, 0, 2.95), frame, bevel=0.04))
    for x in (-1.9, 1.9):
        parts.append(rod((x, 0, 3.2), (x, 0, 3.3), 0.05, frame, verts=8))
    lights = []
    for k in range(5):
        x = -1.6 + 0.8 * k
        c = Vector((x, 0, 2.95))
        lens = []
        for sy in (-1, 1):
            parts.append(cyl(0.2, 0.06, (x, sy * 0.19, 2.95), frame, rot=(R90, 0, 0), verts=18))
            parts.append(box((0.46, 0.16, 0.03), (x, sy * 0.28, 3.17), frame, bevel=0.008))   # a visor
            lens.append(sphere(0.165, (x, sy * 0.225, 2.95), glow, scale=(1, 0.35, 1), segs=16, rings=8))
        lights.append(join(lens, "light_%d" % k, pivot=c))
    root = join(parts, "start_gantry")
    export(root, "start_gantry", [(l, root) for l in lights])


# ------------------------------------------------------------------ scenery

def tree():
    trunk = mat("tree_trunk", (0.5, 0.3, 0.15), 0.7)
    greens = [mat("tree_green", (0.18, 0.55, 0.22), 0.55, coat=0.3),
              mat("tree_green_dark", (0.1, 0.42, 0.2), 0.55, coat=0.3)]
    parts = [cyl(0.15, 0.7, (0, 0, 0.35), trunk, verts=12, r2=0.12, bevel=0.0)]
    for k in range(3):
        r = 0.95 - 0.24 * k
        zb = 0.5 + 0.78 * k
        h = 1.05 - 0.08 * k
        prof = [(0.0, zb + h), (r * 0.12, zb + h - 0.04), (r * 0.55, zb + h * 0.5), (r, zb + 0.12),
                (r * 0.98, zb + 0.04), (r * 0.85, zb), (r * 0.4, zb - 0.02), (0.0, zb - 0.02)]
        parts.append(lathe_r(prof, greens[k % 2], segs=18, name="tier", smooth=50))
    parts.append(sphere(0.07, (0, 0, 0.5 + 1.56 + 0.97), mat("tree_star", (1.0, 0.85, 0.2), 0.3, metal=0.5),
                        segs=8, rings=5))
    K.simple(parts, "tree")


def tree_round():
    trunk = mat("tree_trunk", (0.5, 0.3, 0.15), 0.7)
    leaf = mat("tree_leaf", (0.32, 0.66, 0.2), 0.55, coat=0.3)
    apple = mat("tree_apple", (0.9, 0.12, 0.08), 0.3, coat=0.8)
    parts = [cyl(0.14, 1.3, (0, 0, 0.65), trunk, verts=12, r2=0.09)]
    for s in (-1, 1):   # two little branches into the crown
        parts.append(rod((0, 0, 0.95), (s * 0.3, 0.05, 1.35), 0.05, trunk, r2=0.03, verts=6))
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.95)
    for v in bm.verts:
        d = v.co.normalized()
        bump = 0.06 * math.sin(5 * d.x + 1) * math.sin(4 * d.y + 2) * math.sin(5 * d.z) + \
            0.04 * math.sin(9 * d.x + 3 * d.z)
        v.co = d * 0.95 * (1 + bump)
        v.co.z *= 0.92
        v.co.z += 1.97
    crown = new_obj("crown", bm, leaf, smooth=80)
    parts.append(crown)
    rnd = random.Random(5)
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        e = rnd.uniform(-0.2, 0.7)
        d = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        p = Vector((0, 0, 1.97)) + Vector((d.x * 0.93, d.y * 0.93, d.z * 0.87))
        parts.append(sphere(0.075, p, apple, segs=8, rings=6))
        parts.append(rod(p + Vector((0, 0, 0.06)), p + Vector((0.02, 0, 0.11)), 0.008, trunk, verts=4))
    K.simple(parts, "tree_round")


def house():
    wall = mat("house_wall", (0.98, 0.9, 0.72), 0.55, coat=0.3)
    roof = mat("house_roof", (0.82, 0.2, 0.12), 0.45, coat=0.5)
    trim = mat("house_trim", (0.98, 0.98, 0.95), 0.4, coat=0.4)
    door = mat("house_door", (0.15, 0.38, 0.75), 0.4, coat=0.6)
    glass = mat("house_glass", (0.25, 0.45, 0.65), 0.08, coat=1.0, emit=0.08, emit_color=(1.0, 0.85, 0.5))
    shutter = mat("house_shutter", (0.2, 0.6, 0.35), 0.45, coat=0.5)
    chim = mat("house_chimney", (0.65, 0.3, 0.2), 0.7)
    flower = mat("house_flower", (1.0, 0.4, 0.6), 0.5)
    W, D, H = 3.0, 2.6, 1.8
    parts = [box((W, D, H), (0, 0, H / 2), wall, bevel=0.04),
             box((W + 0.06, D + 0.06, 0.12), (0, 0, 0.06), trim, bevel=0.02)]
    # gables (wall colour) and two roof planks
    ridge = H + 1.1
    parts.append(extrude_x([(-D / 2, H), (D / 2, H), (0, ridge)], -W / 2, W / 2, wall, "gable"))
    for sy in (-1, 1):
        a = Vector((0, sy * (D / 2 + 0.3), H - 0.24))
        b = Vector((0, 0, ridge + 0.06))
        d = (b - a)
        ang = math.atan2(b.z - a.z, abs(b.y - a.y))
        L = d.length + 0.04
        pl = box((W + 0.4, L, 0.12), (0, 0, 0), roof, bevel=0.03)
        pl.data.transform(Matrix.Translation((a + b) / 2 + Vector((0, 0, 0.06)))
                          @ Matrix.Rotation(-sy * ang, 4, "X"))
        parts.append(pl)
    parts.append(box((W + 0.44, 0.16, 0.12), (0, 0, ridge + 0.1), trim, bevel=0.04))
    # the chimney
    parts.append(box((0.36, 0.36, 1.2), (0.8, 0.45, ridge - 0.25), chim, bevel=0.02))
    parts.append(box((0.44, 0.44, 0.1), (0.8, 0.45, ridge + 0.38), trim, bevel=0.02))

    def window(x, y, z, face, w=0.5, h=0.56, shutters=True):
        """face: the outward axis ('-y', '+y', '-x', '+x')."""
        out = []
        ax, sgn = face[1], (1 if face[0] == "+" else -1)

        def at(u, v, d):
            return (u, sgn * (y + d), v) if ax == "y" else (sgn * (x + d), u, v)
        u0 = x if ax == "y" else y
        sz = (w, 0.04, h) if ax == "y" else (0.04, w, h)
        out.append(box(sz, at(u0, z, 0.0), glass, bevel=0.0))
        fr = (w + 0.1, 0.05, 0.08) if ax == "y" else (0.05, w + 0.1, 0.08)
        out.append(box(fr, at(u0, z - h / 2 - 0.02, 0.02), trim, bevel=0.01))
        out.append(box(fr, at(u0, z + h / 2 + 0.02, 0.02), trim, bevel=0.01))
        bar_v = (0.04, 0.05, h) if ax == "y" else (0.05, 0.04, h)
        bar_h = (w, 0.05, 0.04) if ax == "y" else (0.05, w, 0.04)
        out.append(box(bar_v, at(u0, z, 0.02), trim, bevel=0.0))
        out.append(box(bar_h, at(u0, z, 0.02), trim, bevel=0.0))
        for s in (-1, 1):
            out.append(box(bar_v, at(u0 + s * w / 2, z, 0.02), trim, bevel=0.0))
            if shutters:
                sh = (0.22, 0.04, h + 0.04) if ax == "y" else (0.04, 0.22, h + 0.04)
                out.append(box(sh, at(u0 + s * (w / 2 + 0.17), z, 0.02), shutter, bevel=0.01))
        # a flower box under it
        fb = (w + 0.08, 0.14, 0.1) if ax == "y" else (0.14, w + 0.08, 0.1)
        out.append(box(fb, at(u0, z - h / 2 - 0.1, 0.06), shutter, bevel=0.01))
        for k in range(4):
            uu = u0 - w / 2 + 0.06 + k * (w - 0.12) / 3
            out.append(sphere(0.05, at(uu, z - h / 2 - 0.02, 0.06), flower, segs=6, rings=4))
        return out
    for x in (-0.85, 0.85):
        parts += window(x, D / 2, 1.0, "-y")
        parts += window(x, D / 2, 1.0, "+y")
    for sx in ("-x", "+x"):
        parts += window(W / 2, 0, 1.0, sx, shutters=False)
        parts.append(cyl(0.2, 0.05, ((1 if sx[0] == "+" else -1) * (W / 2 + 0.01), 0, H + 0.42), glass,
                         rot=(0, R90, 0), verts=14))
        parts.append(torus(0.2, 0.035, ((1 if sx[0] == "+" else -1) * (W / 2 + 0.03), 0, H + 0.42), trim,
                           rot=(0, R90, 0), verts=16, minor=4))
    # the door in the middle of the front, a step and a little porch roof
    parts.append(box((0.56, 0.06, 1.0), (0, -D / 2 - 0.01, 0.62), door, bevel=0.02))
    parts.append(box((0.66, 0.08, 0.06), (0, -D / 2 - 0.02, 1.15), trim, bevel=0.01))
    parts.append(sphere(0.035, (0.17, -D / 2 - 0.06, 0.62), mat("house_knob", (1.0, 0.8, 0.3), 0.2, metal=1.0),
                        segs=8, rings=5))
    parts.append(box((0.8, 0.3, 0.1), (0, -D / 2 - 0.15, 0.05), trim, bevel=0.02))
    porch = box((0.9, 0.42, 0.06), (0, -D / 2 - 0.18, 1.3), roof, bevel=0.02)
    porch.data.transform(Matrix.Translation((0, -D / 2 - 0.18, 1.3)) @ Matrix.Rotation(math.radians(-18), 4, "X")
                         @ Matrix.Translation((0, D / 2 + 0.18, -1.3)))
    parts.append(porch)
    K.simple(parts, "house")


def windmill_toy():
    body = mat("windmill_body", (0.97, 0.95, 0.9), 0.45, coat=0.4)
    band = mat("windmill_band", (0.2, 0.42, 0.85), 0.4, coat=0.5)
    roof = mat("windmill_roof", (0.85, 0.18, 0.12), 0.45, coat=0.5)
    door = mat("windmill_door", (0.55, 0.32, 0.16), 0.6)
    frame = mat("windmill_frame", (0.55, 0.3, 0.14), 0.6)
    canvas = two_sided(mat("windmill_canvas", (0.98, 0.94, 0.84), 0.7))
    canvas2 = two_sided(mat("windmill_canvas_red", (0.9, 0.22, 0.15), 0.7))
    hub_m = mat("windmill_hub", (0.25, 0.25, 0.28), 0.4, metal=0.7)
    glass = mat("windmill_glass", (0.25, 0.45, 0.65), 0.08, coat=1.0)
    parts = []
    prof = [(1.02, 0.0)] + [(1.0 - 0.3 * z / 3.0, z) for z in (0.02, 0.5, 0.62, 1.4, 1.52, 2.3, 2.42, 3.0)]
    prof = [(0.0, 3.0)] + list(reversed(prof)) + [(0.0, 0.0)]
    tower = lathe_r(prof, body, segs=8, name="tower", smooth=0)
    paint_by(tower, [body, band], lambda c: 1 if any(a < c.z < b for a, b in ((0.5, 0.62), (1.4, 1.52),
                                                                                  (2.3, 2.42))) else 0)
    tower.data.transform(Matrix.Rotation(math.pi / 8, 4, "Z"))
    parts.append(tower)
    parts.append(lathe_r([(0.0, 3.0), (0.82, 3.0), (0.82, 3.12), (0.0, 3.12)], band, segs=16, name="gallery",
                         smooth=0))
    cap = lathe_r([(0.0, 4.25), (0.12, 4.2), (0.45, 3.9), (0.74, 3.35), (0.8, 3.12), (0.0, 3.12)], roof, segs=16,
                  name="cap", smooth=40)
    parts.append(cap)
    parts.append(sphere(0.1, (0, 0, 4.28), band, segs=8, rings=5))
    # the door on the front (+X) and two little round windows
    parts.append(box((0.1, 0.5, 0.8), (0.97, 0, 0.42), door, bevel=0.02))
    parts.append(sphere(0.25, (0.95, 0, 0.82), door, scale=(0.4, 1, 0.5), segs=10, rings=6))
    for z in (1.85, 2.65):
        r = 1.0 - 0.3 * z / 3.0
        parts.append(cyl(0.14, 0.06, (r * math.cos(math.pi / 8) * 0.98, 0, z), glass, rot=(0, R90, 0), verts=12))
        parts.append(torus(0.14, 0.03, (r * math.cos(math.pi / 8) * 0.98 + 0.02, 0, z), body, rot=(0, R90, 0),
                           verts=12, minor=4))
    hx, hz = 0.95, 3.3
    parts.append(rod((0.4, 0, hz), (hx, 0, hz), 0.09, hub_m, verts=10))
    # the sails: a hub cap and four latticed arms with canvas, in the YZ plane
    sp = [sphere(0.16, (hx, 0, hz), roof, scale=(0.8, 1, 1), segs=12, rings=8)]
    for k in range(4):
        rot = Matrix.Translation((hx, 0, hz)) @ Matrix.Rotation(k * math.pi / 2, 4, "X")
        arm = [box((0.06, 0.08, 2.0), (0, 0, 1.0), frame, bevel=0.01)]
        for j in range(7):   # rungs
            r = 0.45 + 1.45 * j / 6
            arm.append(box((0.04, 0.5, 0.035), (0.0, 0.25, r), frame, bevel=0.0))
        arm.append(box((0.04, 0.035, 1.5), (0.0, 0.5, 1.2), frame, bevel=0.0))
        cv = grid_obj([[(0.03, 0.03 + 0.44 * j / 2, 0.45 + 1.45 * i / 3) for j in range(3)] for i in range(4)],
                      canvas, "canvas", smooth=0)
        set_mats(cv, [canvas if k % 2 == 0 else canvas2])
        arm.append(cv)
        for o in arm:
            K.select(o)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            o.data.transform(rot)
        sp += arm
    sails = join(sp, "sails", pivot=(hx, 0, hz))
    root = join(parts, "windmill_toy")
    export(root, "windmill_toy", [(sails, root)])


# ------------------------------------------------------------------ pickups and hazards

def wrench():
    metal = mat("wrench_metal", (0.9, 0.9, 0.93), 0.14, metal=1.0)
    glow = mat("wrench_glow", (1.0, 0.75, 0.15), 0.3, emit=4.0, emit_color=(1.0, 0.7, 0.1))
    T = 0.02
    G = 0.017
    parts = []
    # the open end (right): a C-shaped jaw angled 15 degrees
    R, w = 0.085, 0.034
    a0 = math.asin(w / R)
    jaw = []
    for k in range(25):
        a = a0 + (2 * math.pi - 2 * a0) * k / 24
        jaw.append((R * math.cos(a), R * math.sin(a)))
    jaw += [(0.0, -w)] + [(-0.012 * math.sin(math.pi * j / 6) + 0.0, -w * math.cos(math.pi * j / 6))
                          for j in range(1, 6)] + [(0.0, w)]
    rot = Matrix.Rotation(math.radians(15), 2)

    def place(poly, dx, rm=None):
        out = []
        for x, y in poly:
            v = Vector((x, y))
            if rm:
                v = rm @ v
            out.append((v.x + dx, v.y))
        return out
    jaw_r = place(jaw, 0.235, rot)
    # ccw check: shoelace
    def ccw(poly):
        return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly))) > 0
    if not ccw(jaw_r):
        jaw_r = jaw_r[::-1]
    parts.append(slab(jaw_r, -T, T, metal, "jaw", smooth=0, bevel=0.006))
    parts.append(slab(offset_poly(jaw_r, G), -T * 0.6, T * 0.6, glow, "jaw_glow", smooth=0))
    # the ring end (left): a round eye with a twelve-point hole
    n = 24
    outer = [(-0.235 + 0.078 * math.cos(2 * math.pi * k / n), 0.078 * math.sin(2 * math.pi * k / n)) for k in range(n)]
    inner = [(-0.235 + (0.042 if k % 2 == 0 else 0.036) * math.cos(2 * math.pi * k / n),
              (0.042 if k % 2 == 0 else 0.036) * math.sin(2 * math.pi * k / n)) for k in range(n)]
    parts.append(ring_slab(outer, inner, -T, T, metal, "eye"))
    parts.append(ring_slab(offset_poly(outer, G), inner, -T * 0.6, T * 0.6, glow, "eye_glow"))
    # the handle: a waisted bar with a raised spine
    hl = []
    for k in range(13):
        x = -0.17 + 0.32 * k / 12
        hl.append((x, -(0.026 + 0.008 * (abs(x - 0.0) / 0.17) ** 2)))
    hu = [(x, -y) for x, y in reversed(hl)]
    handle = hl + hu
    parts.append(slab(handle, -T * 0.8, T * 0.8, metal, "handle", smooth=0, bevel=0.006))
    parts.append(slab(offset_poly(handle, G), -T * 0.5, T * 0.5, glow, "handle_glow", smooth=0))
    parts.append(box((0.24, 0.016, 0.012), (0.0, 0, T * 0.8 + 0.003), metal, bevel=0.004))
    parts.append(box((0.24, 0.016, 0.012), (0.0, 0, -T * 0.8 - 0.003), metal, bevel=0.004))
    K.simple(parts, "wrench")


def oil():
    oil_m = mat("oil", (0.015, 0.015, 0.025), 0.04, coat=1.0)
    sheen = mat("oil_sheen", (0.12, 0.05, 0.22), 0.05, coat=1.0, emit=0.12, emit_color=(0.3, 0.1, 0.6))
    sheen2 = mat("oil_sheen_green", (0.03, 0.16, 0.14), 0.05, coat=1.0, emit=0.1, emit_color=(0.1, 0.5, 0.4))
    parts = [dome_blob(blob_outline(0.85, 11, 48, sx=1.2, sy=0.95), 0.02, 0.0, oil_m, "slick")]
    parts.append(dome_blob(blob_outline(0.32, 4, 28, sx=1.5, sy=0.7), 0.0025, 0.0195, sheen, "sheen"))
    parts[-1].data.transform(Matrix.Translation((-0.15, 0.08, 0)) @ Matrix.Rotation(0.4, 4, "Z"))
    parts.append(dome_blob(blob_outline(0.2, 9, 24, sx=1.4, sy=0.6), 0.0025, 0.0195, sheen2, "sheen"))
    parts[-1].data.transform(Matrix.Translation((0.25, -0.12, 0)) @ Matrix.Rotation(-0.3, 4, "Z"))
    for (x, y, r, sd) in ((1.08, 0.35, 0.1, 1), (-1.05, -0.4, 0.13, 2), (0.6, -0.8, 0.07, 3), (-0.5, 0.82, 0.08, 6)):
        b = dome_blob(blob_outline(r, sd, 16), 0.016, 0.0, oil_m, "drop")
        b.data.transform(Matrix.Translation((x, y, 0)))
        parts.append(b)
    K.simple(parts, "oil")


def puddle():
    water = mat("puddle_water", (0.3, 0.42, 0.52), 0.02, coat=1.0, alpha=0.72)
    wet = mat("puddle_wet", (0.08, 0.08, 0.09), 0.25, coat=0.5)
    ripple = mat("puddle_ripple", (0.85, 0.92, 1.0), 0.05, coat=1.0, alpha=0.6)
    out = blob_outline(0.9, 21, 48, sx=1.2, sy=0.85)
    parts = [dome_blob(offset_poly(out, 0.07), 0.004, 0.0, wet, "wet"),
             dome_blob(out, 0.012, 0.002, water, "water")]
    for (x, y, r, sd) in ((1.15, -0.45, 0.18, 2), (-1.1, 0.5, 0.14, 5)):
        o2 = blob_outline(r, sd, 20)
        a = dome_blob(offset_poly(o2, 0.04), 0.004, 0.0, wet, "wet")
        b = dome_blob(o2, 0.01, 0.002, water, "water")
        for o in (a, b):
            o.data.transform(Matrix.Translation((x, y, 0)))
        parts += [a, b]
    for (x, y, r) in ((0.2, 0.1, 0.22), (0.2, 0.1, 0.4), (-0.45, -0.2, 0.15)):
        parts.append(torus(r, 0.008, (x, y, 0.014), ripple, verts=28, minor=4, scale=(1, 1, 0.35)))
    K.simple(parts, "puddle")


def ramp():
    deck = mat("ramp_deck", (0.55, 0.58, 0.62), 0.35, metal=0.6)
    side = mat("ramp_side", (0.15, 0.4, 0.85), 0.35, metal=0.2, coat=0.6)
    stripe = mat("ramp_stripe", (1.0, 0.8, 0.08), 0.4, coat=0.5)
    blk = mat("ramp_black", (0.06, 0.06, 0.07), 0.5)
    bolt = mat("ramp_bolt", (0.85, 0.85, 0.88), 0.2, metal=1.0)
    L, Wd, Hh = 1.5, 1.1, 0.6

    def ztop(x):
        u = (x + L) / (2 * L)
        return Hh * u ** 1.35
    prof = [(-Wd, -1.0), (Wd, -1.0), (Wd, 0.0), (-Wd, 0.0)]
    st = []
    for k in range(21):
        x = -L + 2 * L * k / 20
        z = ztop(x)
        st.append((x, 1.0, max(0.004, min(0.05, z)), z))
    parts = [loft_x(prof, st, deck, cap_start=True, cap_end=True, name="deck", smooth=20)]
    sidep = [(-L, 0.0), (L, 0.0)] + [(L - 2 * L * k / 20, ztop(L - 2 * L * k / 20) - 0.01) for k in range(21)]
    for sy in (-1, 1):
        sp = prism(sidep[:-1], 0.07, (0, sy * (Wd + 0.035), 0), side, bevel=0.012)
        parts.append(sp)
        # a yellow edge band along the top of each side and rivets
        pts = [(x, sy * (Wd + 0.035), ztop(x) + 0.012) for x in (-L + 2 * L * k / 20 for k in range(1, 21))]
        parts.append(tube(pts, [0.02] * len(pts), stripe, verts=6, caps=True, name="edge"))
        for k in range(1, 8):
            x = -L + 0.35 * k + 0.1
            parts.append(sphere(0.018, (x, sy * (Wd + 0.072), ztop(x) * 0.5 + 0.03), bolt, scale=(1, 0.5, 1),
                                segs=8, rings=4))
    parts.append(box((0.07, 2 * Wd + 0.14, Hh), (L - 0.035, 0, Hh / 2), side, bevel=0.012))

    def drape(poly, m, lift=0.004):
        bm = bmesh.new()
        vs = [bm.verts.new((x, y, ztop(x) + lift)) for x, y in poly]
        bm.faces.new(vs)
        return raw_obj("chev", bm, m, smooth=0)
    # chevrons pointing up the ramp
    for k in range(4):
        x0 = -1.15 + 0.62 * k
        for sy in (-1, 1):
            poly = [(x0, sy * 0.0), (x0 + 0.17, 0.0), (x0 + 0.17 - 0.32, sy * 0.78), (x0 - 0.32, sy * 0.78)]
            if sy < 0:
                poly = poly[::-1]
            # subdivide along for the curve
            dense = []
            for a, b in zip(poly, poly[1:] + poly[:1]):
                for j in range(4):
                    dense.append((a[0] + (b[0] - a[0]) * j / 4, a[1] + (b[1] - a[1]) * j / 4))
            parts.append(drape(dense, stripe))
    # a hazard band at the lip
    for k in range(11):
        y0 = -Wd + 2 * Wd * k / 11
        y1 = y0 + 2 * Wd / 11
        m = stripe if k % 2 == 0 else blk
        parts.append(drape([(L - 0.2, y0), (L - 0.04, y0), (L - 0.04, y1), (L - 0.2, y1)], m, 0.005))
    K.simple(parts, "ramp")


def bridge():
    deck_m = mat("bridge_deck", (0.3, 0.3, 0.33), 0.75)
    kr = mat("bridge_kerb_red", (0.88, 0.12, 0.1), 0.45, coat=0.4)
    kw = mat("bridge_kerb_white", (0.96, 0.95, 0.92), 0.45, coat=0.4)
    steel = mat("bridge_steel", (0.15, 0.55, 0.42), 0.35, metal=0.4, coat=0.5)
    pillar = mat("bridge_pillar", (0.92, 0.85, 0.72), 0.7)
    cap_m = mat("bridge_cap", (0.7, 0.62, 0.52), 0.7)
    bolt = mat("bridge_bolt", (0.85, 0.85, 0.88), 0.2, metal=1.0)
    L, Wd, top = 5.0, 3.0, 2.2
    parts = [box((2 * L, 2 * Wd - 0.2, 0.3), (0, 0, top - 0.15), deck_m, bevel=0.0)]
    # kerbs along both edges
    n = 20
    for sy in (-1, 1):
        for k in range(n):
            x = -L + (k + 0.5) * 2 * L / n
            parts.append(box((2 * L / n, 0.3, 0.06), (x, sy * (Wd - 0.25), top + 0.03), kr if k % 2 == 0 else kw,
                             bevel=0.008))
        # the girder fascia with rivets
        parts.append(box((2 * L, 0.14, 0.62), (0, sy * (Wd - 0.03), top - 0.3), steel, bevel=0.02))
        for z in (top - 0.12, top - 0.5):
            for k in range(15):
                x = -L + 0.3 + (2 * L - 0.6) * k / 14
                parts.append(sphere(0.024, (x, sy * (Wd + 0.045), z), bolt, scale=(1, 0.5, 1), segs=6, rings=3))
        # the railing: top and bottom rails, posts and X bracing
        y = sy * (Wd - 0.04)
        parts.append(box((2 * L, 0.08, 0.08), (0, y, top + 0.72), steel, bevel=0.02))
        parts.append(box((2 * L, 0.06, 0.06), (0, y, top + 0.1), steel, bevel=0.015))
        for k in range(11):
            x = -L + 0.04 + (2 * L - 0.08) * k / 10
            parts.append(box((0.08, 0.08, 0.66), (x, y, top + 0.41), steel, bevel=0.015))
            if k < 10:
                xn = -L + 0.04 + (2 * L - 0.08) * (k + 1) / 10
                parts.append(rod((x, y, top + 0.12), (xn, y, top + 0.7), 0.018, steel, verts=5))
                parts.append(rod((x, y, top + 0.7), (xn, y, top + 0.12), 0.018, steel, verts=5))
    # cross beams under the deck
    for x in (-3.0, 0.0, 3.0):
        parts.append(box((0.22, 2 * Wd - 0.2, 0.25), (x, 0, top - 0.42), steel, bevel=0.02))
    # four pillars at the ends, the clear span along Y between them
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 4.55, sy * 2.2
            parts.append(box((0.8, 0.8, 0.14), (x, y, 0.07), cap_m, bevel=0.02))
            parts.append(box((0.62, 0.62, top - 0.6 - 0.14), (x, y, 0.14 + (top - 0.74) / 2), pillar, bevel=0.03))
            for z in (0.55, 1.0, 1.45):   # block courses
                parts.append(box((0.64, 0.64, 0.035), (x, y, z), cap_m, bevel=0.0))
            parts.append(box((0.78, 0.78, 0.12), (x, y, top - 0.6 + 0.06 - 0.06), cap_m, bevel=0.02))
    K.simple(parts, "bridge")


def trophy():
    gold = mat("trophy_gold", (1.0, 0.76, 0.3), 0.18, metal=1.0)
    base_m = mat("trophy_base", (0.2, 0.12, 0.08), 0.35, coat=0.8)
    plaque = mat("trophy_plaque", (0.95, 0.93, 0.88), 0.3, metal=0.6)
    parts = [box((0.42, 0.42, 0.16), (0, 0, 0.08), base_m, bevel=0.02),
             box((0.32, 0.32, 0.08), (0, 0, 0.2), base_m, bevel=0.015),
             box((0.22, 0.02, 0.08), (0, -0.215, 0.085), plaque, bevel=0.005)]
    cup = lathe_r([(0.0, 0.96), (0.19, 0.96), (0.205, 0.95), (0.2, 0.86), (0.18, 0.72), (0.14, 0.6), (0.08, 0.53),
                   (0.045, 0.5), (0.035, 0.46), (0.04, 0.43), (0.06, 0.41), (0.04, 0.39), (0.035, 0.33),
                   (0.07, 0.28), (0.13, 0.25), (0.13, 0.24), (0.0, 0.24)], gold, segs=28, name="cup", smooth=50)
    parts.append(cup)
    parts.append(lathe_r([(0.0, 0.62), (0.15, 0.7), (0.175, 0.95), (0.0, 0.95)], mat("trophy_inside",
                                                                                     (0.75, 0.5, 0.18), 0.3,
                                                                                     metal=1.0), segs=28,
                         name="inside", smooth=50))
    parts.append(torus(0.2, 0.015, (0, 0, 0.958), gold, verts=28, minor=6))
    parts.append(torus(0.185, 0.012, (0, 0, 0.74), gold, verts=28, minor=5))
    for s in (-1, 1):   # two looping handles on the sides
        pts = [(s * (0.16 + 0.13 * math.sin(math.pi * u) + 0.02 * u), 0, 0.89 - 0.28 * u + 0.05 * math.sin(math.pi * u))
               for u in (k / 10 for k in range(11))]
        parts.append(tube(pts, [0.02] * len(pts), gold, verts=8, caps=True, name="handle"))
    # a little star on the front of the cup
    star = []
    for k in range(10):
        a = math.pi / 2 + math.pi * k / 5
        r = 0.065 if k % 2 == 0 else 0.028
        star.append((r * math.cos(a), r * math.sin(a)))
    st = K.prism(star, 0.02, (0, 0, 0), plaque, bevel=0.004)
    st.data.transform(Matrix.Translation((0, -0.2, 0.79)) @ Matrix.Rotation(math.radians(-8), 4, "X"))
    parts.append(st)
    K.simple(parts, "trophy")


def flag_chequered():
    pole_m = mat("flag_pole", (0.92, 0.92, 0.95), 0.2, metal=0.9)
    knob = mat("flag_knob", (1.0, 0.75, 0.25), 0.2, metal=1.0)
    blk = mat("flag_black", (0.04, 0.04, 0.05), 0.6)
    wht = mat("flag_white", (0.97, 0.97, 0.95), 0.6)
    parts = [cyl(0.13, 0.05, (0, 0, 0.025), mat("flag_stand", (0.15, 0.15, 0.17), 0.5), verts=16, bevel=0.01),
             rod((0, 0, 0.0), (0, 0, 1.68), 0.022, pole_m, verts=8),
             sphere(0.04, (0, 0, 1.7), knob, segs=10, rings=6)]
    cloth = wave_flag(0.02, 0.84, 1.03, 1.62, 8, 5, [blk, wht], lambda i, j: (i + j) % 2, amp=0.06, waves=1.1,
                      droop=0.05, name="cloth")
    cl = join([cloth], "cloth", pivot=(0, 0, 1.62))
    root = join(parts, "flag_chequered")
    export(root, "flag_chequered", [(cl, root)])


JOBS = {"car": car, "cone": cone, "tyre_stack": tyre_stack, "hay_bale": hay_bale, "barrier": barrier,
        "grandstand": grandstand, "start_gantry": start_gantry, "tree": tree, "tree_round": tree_round,
        "house": house, "windmill_toy": windmill_toy, "wrench": wrench, "oil": oil, "puddle": puddle, "ramp": ramp,
        "bridge": bridge, "trophy": trophy, "flag_chequered": flag_chequered}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
