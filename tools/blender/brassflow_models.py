"""Brassflow (game 29) models: brass-and-glass pipe pieces, the glow boiler, a blocked cell, the cursor, the piece
dispenser, a spill splash and the steampunk workshop diorama round the board.
Our own designs (a pipe-laying race in a night workshop; nothing taken from any earlier pipe game). Deterministic;
output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/brassflow_models.py -- godot/games/brassflow/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, torus, rod, tube, prism, join, export, ...) and
lanternlinks_models.py (lathe, place, T, Rx, Ry, Rz); sweep, gear, gauge and wheel are this file's own.

Axes: built in Blender (Z up) and exported Y up, so Blender (x, y, z) is Godot (x, z, -y). Everything below is in
Godot axes: x right, y up, z down the rows (towards the camera). 1 unit = one board cell. The board's top is y = 0;
cell (col, row) is centred at (col + 0.5, 0, row + 0.5). Directions as in flow_engine.gd: up = -z, right = +x,
down = +z, left = -x. Emissive materials all have "glow" in their names.

PIPE PIECES (pipe_straight, pipe_corner, pipe_cross): origin at the cell centre on the board top. A square tile
  plate 0.94 x 0.94, 0.05 thick (tile_plate, brass edging tile_brass, four corner rivets), carrying a pipe whose
  centreline runs at y = 0.24: a copper cradle (pipe_copper, an open trough round the lower 244 degrees, outer radius
  0.16: the top 116 degrees are open) holding a glass tube (child "glass", radius 0.14, material pipe_glass, alpha
  0.12) round a glow tube (child "glow_path", radius 0.085, material glow_path_glow) on the centreline; brass collars (pipe_brass) and a flange
  (radius 0.19, 0.045 thick, six iron bolts: pipe_iron) at every opening, flush with the cell edge (|x| or |z| = 0.5),
  so the flanges of neighbouring pieces meet. Seen from above, the glow shows through the trough's open top.
  The glow_path UVs: U runs 0 -> 1 along the path (by length), V round the tube. Its direction is given below; a fill
  shader can reveal U < fill (or U > 1 - fill when the glow comes in from the other end).
  pipe_straight.glb  root "pipe_straight": openings right (+x) and left (-x) = the engine's "h". glow_path U = 0 at
                     x = -0.5, U = 1 at x = +0.5. A pressure gauge stands on the tile's front-right corner (+x, +z),
                     tilted towards +z (gauge_face, gauge_needle, pipe_brass), fed by a thin copper line.
                     For "v" rotate it by +90 degrees about Y (then U = 0 at z = +0.5, the bottom).
  pipe_corner.glb    root "pipe_corner": openings up (-z) and right (+x) = the engine's "ne". The path is a quarter
                     circle of radius 0.5 centred on the cell's corner (+0.5, -0.5). glow_path U = 0 at the up
                     opening (0, 0.24, -0.5), U = 1 at the right opening (0.5, 0.24, 0). A red valve wheel
                     (valve_red) on a brass stem sits in the free corner (-x, +z).
                     Rotations about Y (positive = counter-clockwise seen from above, Godot's convention):
                       ne = 0,  nw = +90 deg (openings up, left),  sw = 180 deg (down, left),  se = -90 deg (down,
                       right).  (Check: +90 deg about Y maps +x to -z and -z to -x.)
  pipe_cross.glb     root "pipe_cross": all four openings. The left-right run is a straight pipe at y = 0.24
                     (child "glow_path", U = 0 at x = -0.5, U = 1 at x = +0.5); the up-down run arches over it as a
                     little bridge (its centreline climbs to y = 0.58 over the cell centre, flat again for |z| > 0.42)
                     on two brass legs (child "glow_path_v", U = 0 at the up opening z = -0.5, U = 1 at the bottom
                     z = +0.5). One "glass" child covers both runs. Both glow children use glow_path_glow.
SOURCE (source.glb): root "source", origin at the cell centre on the board top, outlet facing +x (rotate about Y as
  for the corner: up = +90 deg, left = 180 deg, down = -90 deg). An iron plinth, a glass tank (child "glass",
  source_glass) radius 0.3 from y 0.18 to 0.86 holding the glow (child "tank_glow", material tank_glow, a cylinder of
  radius 0.28 from y 0.19 to 0.80 with its ORIGIN AT ITS BOTTOM (0, 0.19, 0): scale its Y to drain it), brass bands
  and straps, a domed brass cap up to y 1.06 with a whistle to y 1.22, a gauge on the dome facing +z, the outlet pipe
  along +x at y 0.24 ending in the same flange as the pieces at x = 0.5, a red valve wheel on the outlet. The outlet
  stub has a short glass window and a child "outlet_glow" (glow tube, glow_path_glow, U = 0 at the tank, 1 at x 0.5).
BLOCK (block.glb): root "block": a riveted cast-iron plate 0.94 square, 0.12 tall (block_iron, block_brass corner
  plates, block_bolt), with two meshing cogs lying on it: child "cog" (radius 0.33, 16 teeth, pivot at (0, 0.15, 0))
  and child "cog_small" (radius 0.15, 7 teeth, pivot at (0.31, 0.15, 0.31)); spin both about Y, cog_small at
  -16/7 of cog's rate. Top at y 0.27.
CURSOR (cursor.glb): root "cursor": a brass frame (cursor_brass) 1.04 square on y 0..0.04 round the cell, four corner
  posts up to y 0.52 with glowing corner brackets (cursor_glow) at the bottom and caps on top. Origin at the cell
  centre on the board top.
DISPENSER (dispenser.glb): root "dispenser", origin at its centre on the slot floor (y = 0, level with the board top),
  1.2 wide (x -0.6..0.6), five slots along z: empties "slot_0" .. "slot_4" at z = +2, +1, 0, -1, -2 (slot_0 is the
  FRONT, nearest the camera: the next piece; a piece put on a slot empty sits like a board piece). Brass rails and
  dividers (dispenser_brass), an iron bed (dispenser_iron, down to y -0.15 = the bench top in workshop.glb), a copper
  hopper at the back (z -2.6..-3.5, to y 1.0), a glowing arrow and lamp strip at the front (dispenser_glow) pointing
  +x (towards the board), and on its left side a feed gear: child "feed_gear" (pivot (-0.66, 0.2, 0.6), radius
  0.32), spin it about X when the queue moves. Overall it spans x -0.8..0.8 (the hopper), z -3.8 .. +3.2.
SPILL (spill.glb): root "spill", origin at its centre on the board top: a glowing puddle (~0.95 across, 0.04 thick,
  spill_glow) with droplets and a crown of splashes up to y 0.2. Scale it in from 0.
WORKSHOP (workshop.glb): root "workshop" (an empty at the origin) with these children, all in board space:
  bench        the workbench: top at y -0.15, x -6.5..16.5, z -4.4..10.5; bench_wood (planks along x), bench_brass
               trim and corner caps, turned legs down to the floor at y -9.5.
  board_bed    the board: a dark green leather inlay (board_leather), x 0..10, z 0..7, top at y = 0 (from -0.15).
  board_grid   thin brass grid lines at the cell edges, y 0..0.004 (board_grid). Hide it if the view draws its own.
  board_frame  a raised brass frame round the board (board_brass), x -0.32..10.32, z -0.32..7.32, top at y 0.07,
               with rivets.
  room         brick walls (brick): the back wall's face at z = -4.6, the side walls at x = -11 and x = 21, up to
               y 14; a plank floor (floor_wood) at y -9.5; three arched windows in the back wall (centres x = -2.5,
               5, 12.5; sill y 0.6, top y 7.6) with iron glazing bars (window_iron), sandstone surrounds
               (stone_trim) and night panes (window_night_glow; the middle one shows the moon: window_moon_glow).
  shelves      shelves between the windows with bottles (bottle_* glass), jars, books, tins.
  props        tools and clutter on the bench margins (wrenches, hammer, oil can, blueprints, mug, spare pipe,
               screws, a vice, a toolbox) and the steam pipe runs along the back wall with valves (steam_copper,
               valve_red), the vat (vat_glass, vat_brass) and the gear machine frames.
  vat_glow     the glow inside the big vat at (-4.2, -0.15, -2.9) (radius 0.85, 2.0 tall, origin at its bottom).
  gear_0 ..    gears to spin (gear_brass, gear_iron), each with its origin at its axle; each lies flat in the plane
               normal to its thinnest extent (spin about that local axis). gear_0..3 hang on the back wall (axis Z),
               gear_4..6 sit in the bench machine at the back right (axis Z), gear_7 on the left wall (axis X).
  piston_0, piston_1  the moving rods (with their crossheads) of two pistons beside gear_4: rest positions as
               exported, they slide along Y (amplitude ~0.35) driven by gear_4's crank.
  clock        the wall clock body above the middle window (centre (5, 9.3, -4.45), facing +z); children
               "clock_hour" and "clock_minute" (pivot at the centre, pointing up = 12 o'clock at rest, spin about Z;
               negative angles turn clockwise as seen from the room).
  lamp_0 ..    hanging lamps (lamp_brass shades, lamp_glow bulbs, cord); empties "lamp_light_0" .. at the bulbs.
  alarm_lamp   a red warning lamp on the steam pipe (alarm_glow), empty "alarm_light" at its bulb.
  vent_0 ..    empties at steam vents (the steam rises along +Y from them).
  bubbles_0    empty at the bottom centre of the vat's glow (bubble source).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, cyl, sphere, torus, rod, tube, prism, export, reset, finish, select
from lanternlinks_models import lathe, place, T, Rx, Ry, Rz, link
from prism_models import empty, export_anim

TAU = 2 * math.pi
H = 0.24          # pipe centreline height
R_CRADLE = 0.16
R_GLASS = 0.14
R_GLOW = 0.085
R_FLANGE = 0.19


def join(parts, name, pivot=(0, 0, 0)):
    """K.join that first moves aside an unrelated object already holding `name` (props reuse names)."""
    parts = K.flatten(parts)
    o = bpy.data.objects.get(name)
    if o is not None and o not in parts:
        o.name = name + "_part"
    return K.join(parts, name, pivot)


def B(x, y, z):
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return (x, -z, y)


def box(size, loc, material, rot=(0, 0, 0), bevel=None, segs=1, smooth=35):
    return K.box(size, loc, material, rot=rot, bevel=bevel, segs=segs, smooth=smooth)


def gbox(sx, sy, sz, x, y, z, material, bevel=None, segs=1):
    """A box given in Godot axes: sizes (x, y, z) and centre (x, y, z)."""
    return box((sx, sz, sy), B(x, y, z), material, bevel=bevel, segs=segs)


# ------------------------------------------------------------------ materials

def mats():
    return dict(
        brass=mat("pipe_brass", (0.8, 0.58, 0.26), 0.28, 1.0),
        copper=mat("pipe_copper", (0.78, 0.33, 0.2), 0.32, 1.0),
        iron=mat("pipe_iron", (0.13, 0.13, 0.14), 0.45, 0.85),
        glass=mat("pipe_glass", (0.78, 0.9, 0.92), 0.04, 0.0, alpha=0.12),
        glow=mat("glow_path_glow", (0.3, 1.0, 0.72), 0.3, emit=2.5),
        plate=mat("tile_plate", (0.21, 0.2, 0.2), 0.42, 0.65),
        trim=mat("tile_brass", (0.72, 0.52, 0.24), 0.35, 1.0),
        face=mat("gauge_face", (0.93, 0.89, 0.77), 0.4),
        needle=mat("gauge_needle", (0.7, 0.05, 0.03), 0.35),
        red=mat("valve_red", (0.62, 0.07, 0.04), 0.3, coat=0.6),
    )


# ------------------------------------------------------------------ sweep, gear, gauge, wheel

def sweep(path, profile, material, name="sweep", smooth=60, cap=True):
    """Sweeps a closed cross-section along a path (Blender points). profile: (s, u) offsets, s along the side
    (tangent x world Z) and u along the frame's up. UV U = length along the path / total, V = profile index."""
    pts = [Vector(p) for p in path]
    n = len(pts)
    acc = [0.0]
    for i in range(1, n):
        acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
    total = acc[-1] or 1.0
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-5 else Vector((1, 0, 0))
        up = side.cross(t).normalized()
        rings.append([bm.verts.new(p + s * side + u * up) for s, u in profile])
    m = len(profile)
    for i in range(n - 1):
        for k in range(m):
            k2 = (k + 1) % m
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp, (uu, vv) in zip(f.loops, ((acc[i], k), (acc[i], k + 1), (acc[i + 1], k + 1), (acc[i + 1], k))):
                lp[uvl].uv = (uu / total, vv / m)
    if cap:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return finish(link(me, name), material, smooth=smooth)


def ring_profile(r, segs=20):
    return [(r * math.cos(TAU * k / segs), r * math.sin(TAU * k / segs)) for k in range(segs)]


def trough_profile(r_out, r_in, open_deg=100, segs=18):
    """An annulus sector round the bottom: the top open_deg degrees are left open."""
    a0 = math.radians(90 + open_deg / 2)
    a1 = math.radians(90 - open_deg / 2) + TAU
    outer = [(r_out * math.cos(a0 + (a1 - a0) * k / segs), r_out * math.sin(a0 + (a1 - a0) * k / segs))
             for k in range(segs + 1)]
    inner = [(r_in * math.cos(a0 + (a1 - a0) * k / segs), r_in * math.sin(a0 + (a1 - a0) * k / segs))
             for k in range(segs, -1, -1)]
    return outer + inner


def gear(r, teeth, thick, material, hub=None, spokes=5, name="gear", rim=None, depth=None, hole=True):
    """A spur gear in the Blender XY plane (axis Z, z -thick/2..thick/2), centred on the origin: trapezoid teeth
    (tip radius r), a rim, spokes and a hub (hub material)."""
    depth = depth or r * 0.13
    rim = rim or max(r * 0.16, 0.02)
    r_root = r - depth
    r_in = r_root - rim
    bm = bmesh.new()
    n = teeth * 4
    pitch = TAU / teeth
    outer_t, outer_b, inner_t, inner_b = [], [], [], []
    for i in range(teeth):
        for frac, rr in ((0.0, r_root), (0.18, r), (0.45, r), (0.63, r_root)):
            a = i * pitch + frac * pitch
            outer_t.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), thick / 2)))
            outer_b.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), -thick / 2)))
            if hole:
                inner_t.append(bm.verts.new((r_in * math.cos(a), r_in * math.sin(a), thick / 2)))
                inner_b.append(bm.verts.new((r_in * math.cos(a), r_in * math.sin(a), -thick / 2)))
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((outer_b[k], outer_b[k2], outer_t[k2], outer_t[k]))
        if hole:
            bm.faces.new((outer_t[k], outer_t[k2], inner_t[k2], inner_t[k]))
            bm.faces.new((outer_b[k2], outer_b[k], inner_b[k], inner_b[k2]))
            bm.faces.new((inner_t[k], inner_t[k2], inner_b[k2], inner_b[k]))
    if not hole:
        bm.faces.new(outer_t)
        bm.faces.new(outer_b[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    parts = [finish(link(me, name), material, smooth=0)]
    if hole:
        hm = hub or material
        rh = max(r * 0.17, 0.02)
        parts.append(cyl(rh, thick * 1.5, (0, 0, 0), hm, verts=16))
        parts.append(cyl(rh * 0.45, thick * 1.9, (0, 0, 0), K.mat("gear_axle", (0.1, 0.1, 0.11), 0.4, 0.9), verts=8))
        for s in range(spokes):
            a = TAU * s / spokes
            mid = (rh + r_in) / 2 + 0.002
            ln = r_in - rh + rim * 0.5
            o = box((ln, max(r * 0.09, 0.012), thick * 0.7), (mid * math.cos(a), mid * math.sin(a), 0), material,
                    rot=(0, 0, a), bevel=0)
            parts.append(o)
    return join(parts, name)


def gauge(r, face, brass, needle, iron=None, ticks=9, depth=0.03):
    """A round pressure gauge facing Blender +Z, centred on the origin: bezel, face, ticks, needle, glass dome."""
    parts = [cyl(r, depth, (0, 0, 0), brass, verts=20),
             torus(r * 0.93, r * 0.12, (0, 0, depth / 2), brass, verts=20, minor=5),
             cyl(r * 0.86, 0.004, (0, 0, depth / 2 + 0.001), face, verts=20)]
    tick_m = iron or needle
    for k in range(ticks):
        a = math.radians(225 - 270 * k / (ticks - 1))
        rr = r * 0.68
        parts.append(box((r * 0.18, r * 0.05, 0.004), (rr * math.cos(a), rr * math.sin(a), depth / 2 + 0.004),
                         tick_m, rot=(0, 0, a), bevel=0))
    a = math.radians(60)
    parts.append(box((r * 0.75, r * 0.07, 0.005), (r * 0.3 * math.cos(a), r * 0.3 * math.sin(a), depth / 2 + 0.008),
                     needle, rot=(0, 0, a), bevel=0))
    parts.append(cyl(r * 0.1, 0.01, (0, 0, depth / 2 + 0.009), brass, verts=8))
    return join(parts, "gauge")


def wheel(r, material, hub_m, spokes=4, thick=None):
    """A valve hand-wheel facing Blender +Z, centred on the origin."""
    thick = thick or r * 0.14
    parts = [torus(r, thick, (0, 0, 0), material, verts=20, minor=6),
             cyl(r * 0.2, thick * 2.6, (0, 0, 0), hub_m, verts=10)]
    for s in range(spokes):
        a = TAU * s / spokes + 0.4
        parts.append(rod((0, 0, 0), (r * math.cos(a), r * math.sin(a), 0), thick * 0.7, material, verts=6))
    for s in range(spokes * 2):  # knurls on the rim
        a = TAU * (s + 0.5) / (spokes * 2) + 0.4
        parts.append(sphere(thick * 1.25, (r * math.cos(a), r * math.sin(a), 0), material, segs=6, rings=4))
    return join(parts, "wheel")


def placed(obj, M):
    obj.matrix_world = M @ obj.matrix_world
    return obj


def rivet(loc, r, material):
    return sphere(r, loc, material, scale=(1, 1, 0.55), segs=8, rings=4)


# ------------------------------------------------------------------ pipe pieces

def tile(M):
    parts = [box((0.94, 0.94, 0.05), (0, 0, 0.025), M["plate"], bevel=0.008)]
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if sx:
            parts.append(box((0.04, 0.94, 0.056), (sx * 0.45, 0, 0.028), M["trim"], bevel=0.006))
        else:
            parts.append(box((0.86, 0.04, 0.056), (0, sy * 0.45, 0.028), M["trim"], bevel=0.006))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(rivet((sx * 0.4, sy * 0.4, 0.05), 0.022, M["trim"]))
    # a faint engraved diagonal line pattern: two thin brass inlays on the plate
    parts.append(box((0.8, 0.012, 0.004), (0, -0.3, 0.051), M["trim"], bevel=0))
    parts.append(box((0.8, 0.012, 0.004), (0, 0.3, 0.051), M["trim"], bevel=0))
    return parts


def run(path, M, collars=(0.25, 0.75), flanges=(True, True)):
    """The brass/copper/glass parts of one pipe run along `path` (Blender points at the centreline).
    Returns (metal parts, glass object, glow object)."""
    pts = [Vector(p) for p in path]
    parts = [sweep(pts, trough_profile(R_CRADLE, R_CRADLE - 0.016, 116), M["copper"], "cradle", smooth=50)]
    glass = sweep(pts, ring_profile(R_GLASS, 20), M["glass"], "glass", smooth=80, cap=False)
    glow = sweep(pts, ring_profile(R_GLOW, 12), M["glow"], "glow_path", smooth=80)
    acc = [0.0]
    for i in range(1, len(pts)):
        acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)

    def at(f):
        d = f * acc[-1]
        for i in range(1, len(pts)):
            if acc[i] >= d:
                k = (d - acc[i - 1]) / max(acc[i] - acc[i - 1], 1e-6)
                return pts[i - 1].lerp(pts[i], k), (pts[i] - pts[i - 1]).normalized()
        return pts[-1], (pts[-1] - pts[-2]).normalized()

    for f in collars:
        p, t = at(f)
        parts.append(rod(p - t * 0.022, p + t * 0.022, 0.172, M["brass"], verts=20))
        parts.append(rod(p - t * 0.008, p + t * 0.008, 0.18, M["brass"], verts=20))
    for end, use in zip((0, 1), flanges):
        if not use:
            continue
        p, t = (pts[0], (pts[1] - pts[0]).normalized()) if end == 0 else (pts[-1], (pts[-1] - pts[-2]).normalized())
        inward = t if end == 0 else -t
        parts.append(rod(p, p + inward * 0.045, R_FLANGE, M["brass"], verts=24))
        parts.append(rod(p + inward * 0.045, p + inward * 0.075, 0.172, M["brass"], r2=0.165, verts=20))
        side = t.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-5 else Vector((1, 0, 0))
        up = side.cross(t).normalized()
        for k in range(6):
            a = TAU * k / 6 + math.pi / 6
            q = p + inward * 0.045 + 0.155 * (math.cos(a) * side + math.sin(a) * up)
            parts.append(rod(q, q + inward * 0.018, 0.016, M["iron"], verts=6))
    return parts, glass, glow


def saddle(p, t, M, bottom=0.05):
    """A brass saddle bracket under the pipe at p (Blender), across the tangent t."""
    p = Vector(p)
    side = t.cross(Vector((0, 0, 1))).normalized()
    h = p.z - R_CRADLE + 0.02 - bottom
    out = [box((0.07, 0.07, 0.02), (p.x, p.y, bottom + 0.01), M["trim"], bevel=0.005)]
    o = box((0.05, 0.05, h), (p.x, p.y, bottom + h / 2), M["brass"], bevel=0.006)
    out.append(o)
    return out


def straight_path(n=12):
    return [(-0.5 + i / n, 0, H) for i in range(n + 1)]


def corner_path(n=16):
    pts = []
    for i in range(n + 1):
        a = (math.pi / 2) * i / n
        pts.append((0.5 - 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a), H))
    return pts


def pipe_straight():
    M = mats()
    parts, glass, glow = run(straight_path(), M)
    parts += tile(M)
    parts += saddle((-0.25, 0, H), Vector((1, 0, 0)), M) + saddle((0.25, 0, H), Vector((1, 0, 0)), M)
    # a pressure gauge on the front-right corner (Godot +x, +z = Blender +x, -y), tilted to face the camera
    g = gauge(0.085, M["face"], M["brass"], M["needle"], M["iron"])
    placed(g, T((0.3, -0.33, 0.25)) @ Rx(math.radians(60)))
    parts.append(g)
    parts.append(rod((0.3, -0.28, 0.05), (0.3, -0.29, 0.2), 0.018, M["brass"], verts=8))
    parts.append(cyl(0.035, 0.03, (0.3, -0.28, 0.065), M["brass"], verts=10))
    parts.append(tube([(0.3, -0.24, 0.17), (0.3, -0.16, 0.2), (0.24, -0.1, 0.24), (0.18, -0.06, 0.25)],
                      [0.011] * 4, M["copper"], verts=6))
    root = join(parts, "pipe_straight")
    export(root, "pipe_straight", [(glass, root), (glow, root)])


def pipe_corner():
    M = mats()
    parts, glass, glow = run(corner_path(), M, collars=(0.3, 0.7))
    parts += tile(M)
    a = math.radians(45)
    mid = (0.5 - 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a), H)
    parts += saddle(mid, Vector((1, -1, 0)).normalized(), M)
    # the valve wheel in the free corner (Godot -x, +z = Blender -x, -y)
    parts.append(rod((-0.28, -0.28, 0.05), (-0.28, -0.28, 0.24), 0.022, M["brass"], verts=8))
    parts.append(cyl(0.05, 0.05, (-0.28, -0.28, 0.075), M["brass"], verts=12))
    w = wheel(0.1, M["red"], M["brass"])
    placed(w, T((-0.28, -0.28, 0.25)))
    parts.append(w)
    parts.append(tube([(-0.28, -0.22, 0.12), (-0.2, -0.12, 0.13), (-0.1, -0.02, 0.18)], [0.014] * 3, M["copper"],
                      verts=6))
    root = join(parts, "pipe_corner")
    export(root, "pipe_corner", [(glass, root), (glow, root)])


def bridge_z(y, top=0.34, span=0.42):
    if abs(y) >= span:
        return H
    return H + top * math.cos(math.pi * y / (2 * span)) ** 2


def pipe_cross():
    M = mats()
    parts, glass_h, glow_h = run(straight_path(), M, collars=(0.2, 0.8))
    vpath = [(0, 0.5 - i / 40, bridge_z(0.5 - i / 40)) for i in range(41)]
    p2, glass_v, glow_v = run(vpath, M, collars=(0.5,))
    parts += p2 + tile(M)
    for y in (0.3, -0.3):
        z = bridge_z(y)
        parts.append(box((0.05, 0.05, z - R_CRADLE - 0.03), (0.0, y, 0.05 + (z - R_CRADLE - 0.03) / 2), M["brass"]))
    for x in (-0.3, 0.3):
        parts += saddle((x, 0, H), Vector((1, 0, 0)), M)
    # a riveted brass plate on the bridge's crown
    parts.append(box((0.2, 0.1, 0.012), (0, 0, bridge_z(0) + R_CRADLE * 0.2), M["trim"], bevel=0.004))
    glass = join([glass_h, glass_v], "glass")
    glow_v.name = "glow_path_v"
    glow_v.data.name = "glow_path_v"
    root = join(parts, "pipe_cross")
    export(root, "pipe_cross", [(glass, root), (glow_h, root), (glow_v, root)])


# ------------------------------------------------------------------ source, block, cursor, dispenser, spill

def source():
    M = mats()
    sglass = mat("source_glass", (0.8, 0.92, 0.95), 0.03, alpha=0.2)
    tglow = mat("tank_glow", (0.3, 1.0, 0.72), 0.2, emit=3.0)
    parts = [box((0.94, 0.94, 0.09), (0, 0, 0.045), M["iron"], bevel=0.012)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(rivet((sx * 0.4, sy * 0.4, 0.09), 0.024, M["brass"]))
    parts.append(lathe([(0.0, 0.2), (0.33, 0.2), (0.37, 0.17), (0.39, 0.12), (0.39, 0.09), (0.0, 0.09)][::-1][::-1],
                       M["brass"], segs=28, name="foot"))
    for z in (0.32, 0.6):
        parts.append(torus(0.305, 0.014, (0, 0, z), M["brass"], verts=28, minor=5))
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        parts.append(box((0.04, 0.025, 0.66), (0.31 * math.cos(a), 0.31 * math.sin(a), 0.53), M["brass"],
                         rot=(0, 0, a + math.pi / 2), bevel=0.006))
        for z in (0.26, 0.46, 0.66, 0.82):
            parts.append(rivet((0.325 * math.cos(a), 0.325 * math.sin(a), z), 0.012, M["iron"]))
    parts.append(lathe([(0.0, 1.06), (0.08, 1.05), (0.2, 1.01), (0.3, 0.94), (0.37, 0.88), (0.37, 0.85),
                        (0.33, 0.85), (0.0, 0.85)], M["brass"], segs=28, name="dome"))
    parts.append(torus(0.36, 0.018, (0, 0, 0.87), M["copper"], verts=28, minor=5))
    for k in range(12):
        a = TAU * k / 12
        parts.append(rivet((0.365 * math.cos(a), 0.365 * math.sin(a), 0.9), 0.012, M["iron"]))
    # the whistle and a safety valve
    parts.append(cyl(0.035, 0.12, (0.0, 0.05, 1.1), M["brass"], verts=12))
    parts.append(cyl(0.05, 0.06, (0.0, 0.05, 1.19), M["brass"], r2=0.03, verts=12))
    parts.append(sphere(0.022, (0.0, 0.05, 1.23), M["brass"]))
    parts.append(cyl(0.022, 0.1, (-0.16, 0.14, 1.02), M["brass"], verts=8))
    parts.append(rod((-0.16, 0.14, 1.07), (0.05, 0.2, 1.1), 0.01, M["iron"], verts=6))
    parts.append(sphere(0.03, (0.06, 0.2, 1.1), M["red"]))
    g = gauge(0.1, M["face"], M["brass"], M["needle"], M["iron"])
    placed(g, T((0.0, -0.26, 0.98)) @ Rx(math.radians(58)))
    parts.append(g)
    # the outlet: copper stub along +x with a glass window, a flange at the cell edge and a valve wheel on top
    stub = [(0.28 + 0.22 * i / 6, 0, H) for i in range(7)]
    p2, oglass, oglow = run(stub, M, collars=(0.35,), flanges=(False, True))
    parts += p2
    parts.append(rod((0.26, 0, H), (0.33, 0, H), 0.2, M["brass"], verts=24))
    parts.append(rod((0.4, 0, H + 0.12), (0.4, 0, H + 0.2), 0.02, M["brass"], verts=8))
    w = wheel(0.075, M["red"], M["brass"])
    placed(w, T((0.4, 0, H + 0.21)))
    parts.append(w)
    parts += saddle((0.42, 0, H), Vector((1, 0, 0)), M, bottom=0.09)
    # a copper feed pipe down the back
    parts.append(tube([(0.0, 0.3, 0.95), (0.0, 0.42, 0.88), (0.0, 0.43, 0.6), (0.0, 0.43, 0.2), (0.0, 0.35, 0.12)],
                      [0.03] * 5, M["copper"], verts=10, caps=True))
    tank = cyl(0.3, 0.68, (0, 0, 0.52), sglass, verts=28)
    tank.name = "glass"
    tank.data.name = "glass"
    glass = join([tank, oglass], "glass")
    tg = cyl(0.28, 0.61, (0, 0, 0.19 + 0.305), tglow, verts=24)
    tg = join([tg], "tank_glow", pivot=(0, 0, 0.19))
    oglow.name = "outlet_glow"
    oglow.data.name = "outlet_glow"
    root = join(parts, "source")
    export(root, "source", [(glass, root), (tg, root), (oglow, root)])


def block():
    M = mats()
    biron = mat("block_iron", (0.11, 0.11, 0.12), 0.55, 0.8)
    bbrass = mat("block_brass", (0.7, 0.5, 0.22), 0.35, 1.0)
    bolt = mat("block_bolt", (0.25, 0.24, 0.23), 0.4, 0.9)
    cogm = mat("cog_brass", (0.8, 0.58, 0.26), 0.3, 1.0)
    parts = [box((0.94, 0.94, 0.12), (0, 0, 0.06), biron, bevel=0.02, segs=2)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.22, 0.05, 0.13), (sx * 0.36, sy * 0.445, 0.065), bbrass, bevel=0.01))
            parts.append(box((0.05, 0.22, 0.13), (sx * 0.445, sy * 0.36, 0.065), bbrass, bevel=0.01))
            parts.append(cyl(0.028, 0.03, (sx * 0.4, sy * 0.4, 0.13), bolt, verts=6))
    for k in range(8):  # a ring of rivets
        a = TAU * k / 8 + 0.2
        parts.append(rivet((0.39 * math.cos(a) * 0.6, 0.39 * math.sin(a) * 0.6, 0.12), 0.016, bolt))
    # warning stripes on the plate's front and back edges (painted red and black)
    paint = mat("block_paint", (0.62, 0.1, 0.05), 0.4, coat=0.4)
    for sy in (-1, 1):
        for k in range(5):
            parts.append(box((0.07, 0.012, 0.07), (-0.24 + k * 0.12, sy * 0.472, 0.06), paint, rot=(0, math.radians(35), 0),
                             bevel=0))
    parts.append(cyl(0.05, 0.08, (0, 0, 0.18), bolt, verts=10))
    cog = gear(0.33, 16, 0.05, cogm, hub=bbrass, spokes=5, name="cog")
    placed(cog, T((0, 0, 0.15)))
    cog = join([cog], "cog", pivot=(0, 0, 0.15))
    small = gear(0.15, 7, 0.045, cogm, hub=bbrass, spokes=3, name="cog_small")
    placed(small, T((0.31, -0.31, 0.15)) @ Rz(math.radians(10)))
    small = join([small], "cog_small", pivot=(0.31, -0.31, 0.15))
    parts.append(cyl(0.035, 0.12, (0.31, -0.31, 0.12), bolt, verts=8))
    root = join(parts, "block")
    export(root, "block", [(cog, root), (small, root)])


def cursor():
    brass = mat("cursor_brass", (0.9, 0.68, 0.32), 0.25, 1.0)
    glow = mat("cursor_glow", (1.0, 0.75, 0.35), 0.3, emit=6.0)
    parts = []
    s = 0.52
    w = 0.05
    for sx in (-1, 1):
        parts.append(box((w, 2 * s, 0.04), (sx * (s - w / 2), 0, 0.02), brass, bevel=0.008))
        parts.append(box((2 * s, w, 0.04), (0, sx * (s - w / 2), 0.02), brass, bevel=0.008))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (s - 0.035), sy * (s - 0.035)
            parts.append(box((0.06, 0.06, 0.5), (cx, cy, 0.25), brass, bevel=0.01))
            parts.append(sphere(0.045, (cx, cy, 0.52), glow, segs=10, rings=6))
            parts.append(cyl(0.05, 0.03, (cx, cy, 0.48), brass, verts=10))
            # glowing L brackets on the frame corners
            parts.append(box((0.2, 0.03, 0.02), (cx - sx * 0.1, cy - sy * 0.03, 0.045), glow, bevel=0))
            parts.append(box((0.03, 0.2, 0.02), (cx - sx * 0.03, cy - sy * 0.1, 0.045), glow, bevel=0))
    simple = join(parts, "cursor")
    export(simple, "cursor")


def dispenser():
    brass = mat("dispenser_brass", (0.83, 0.6, 0.27), 0.28, 1.0)
    iron = mat("dispenser_iron", (0.14, 0.13, 0.13), 0.5, 0.8)
    copper = mat("dispenser_copper", (0.86, 0.45, 0.28), 0.32, 1.0)
    glow = mat("dispenser_glow", (1.0, 0.72, 0.3), 0.3, emit=5.0)
    red = mat("valve_red", (0.62, 0.07, 0.04), 0.3, coat=0.6)
    parts = [gbox(1.2, 0.15, 6.3, 0, -0.075, -0.35, iron, bevel=0.02)]
    for z in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5):  # slot dividers
        parts.append(gbox(1.14, 0.03, 0.04, 0, 0.015, z, brass, bevel=0.006))
    for sx in (-1, 1):
        parts.append(gbox(0.06, 0.12, 6.1, sx * 0.57, 0.06, -0.35, brass, bevel=0.01))
        parts.append(rod(B(sx * 0.6, 0.32, -3.3), B(sx * 0.6, 0.32, 2.75), 0.025, brass, verts=10))
        for z in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5):
            parts.append(rod(B(sx * 0.6, 0.0, z), B(sx * 0.6, 0.32, z), 0.018, brass, verts=8))
            parts.append(sphere(0.032, B(sx * 0.6, 0.32, z), brass, segs=8, rings=5))
        for z in [-3.2 + 0.4 * i for i in range(15)]:
            parts.append(rivet(B(sx * 0.6, 0.0, z), 0.012, iron))
    # the hopper at the back (pieces drop in from above)
    bm = bmesh.new()
    lo = [bm.verts.new(B(x, 0.0, z)) for x, z in ((-0.6, -3.5), (0.6, -3.5), (0.6, -2.55), (-0.6, -2.55))]
    hi = [bm.verts.new(B(x, 1.0, z)) for x, z in ((-0.8, -3.75), (0.8, -3.75), (0.8, -2.3), (-0.8, -2.3))]
    for k in range(4):
        k2 = (k + 1) % 4
        bm.faces.new((lo[k], lo[k2], hi[k2], hi[k]))
    bm.faces.new(lo[::-1])
    me = bpy.data.meshes.new("hopper")
    bm.to_mesh(me)
    bm.free()
    hopper = finish(link(me, "hopper"), copper, smooth=0)
    select(hopper)
    sol = hopper.modifiers.new("s", "SOLIDIFY")
    sol.thickness = 0.04
    bpy.ops.object.modifier_apply(modifier=sol.name)
    parts.append(hopper)
    for y in (0.35, 0.7):
        f = y / 1.0
        hw = 0.6 + 0.2 * f + 0.02
        z0, z1 = -3.5 - 0.25 * f - 0.02, -2.55 + 0.25 * f + 0.02
        parts.append(gbox(2 * hw, 0.05, 0.04, 0, y, z0, brass, bevel=0.008))
        parts.append(gbox(2 * hw, 0.05, 0.04, 0, y, z1, brass, bevel=0.008))
        parts.append(gbox(0.04, 0.05, z1 - z0, -hw, y, (z0 + z1) / 2, brass, bevel=0.008))
        parts.append(gbox(0.04, 0.05, z1 - z0, hw, y, (z0 + z1) / 2, brass, bevel=0.008))
    parts.append(gbox(1.7, 0.06, 0.06, 0, 1.0, -3.77, brass))
    parts.append(gbox(1.7, 0.06, 0.06, 0, 1.0, -2.28, brass))
    # the front: a brass lip, a lamp strip and an arrow pointing +x towards the board
    parts.append(gbox(1.26, 0.18, 0.08, 0, 0.0, 2.78, brass, bevel=0.015))
    parts.append(gbox(0.9, 0.04, 0.03, 0, 0.06, 2.83, glow, bevel=0))
    arrow = prism([(-0.2, -0.06), (0.05, -0.06), (0.05, -0.13), (0.22, 0.0), (0.05, 0.13), (0.05, 0.06), (-0.2, 0.06)],
                  0.02, (0, 0, 0), glow, bevel=0)
    placed(arrow, T(B(0, 0.045, 3.0)) @ Rx(math.radians(90)))
    parts.append(gbox(0.6, 0.06, 0.4, 0, 0.0, 3.0, iron, bevel=0.01))
    parts.append(arrow)
    # a lamp post at the front-left corner
    parts.append(rod(B(-0.62, 0.0, 2.7), B(-0.62, 0.7, 2.7), 0.02, brass, verts=8))
    parts.append(sphere(0.06, B(-0.62, 0.76, 2.7), glow, segs=10, rings=6))
    parts.append(cyl(0.07, 0.04, B(-0.62, 0.84, 2.7), brass, r2=0.03, verts=10))
    parts.append(torus(0.065, 0.008, B(-0.62, 0.76, 2.7), brass, verts=12, minor=4))
    # the feed gear on the left side
    fg = gear(0.32, 12, 0.05, brass, hub=red, spokes=4, name="feed_gear")
    placed(fg, T(B(-0.66, 0.2, 0.6)) @ Ry(math.radians(90)))
    fg = join([fg], "feed_gear", pivot=B(-0.66, 0.2, 0.6))
    parts.append(gear(0.2, 8, 0.05, brass, hub=red, spokes=3, name="g2"))
    placed(parts[-1], T(B(-0.69, 0.08, 0.13)) @ Ry(math.radians(90)))
    root = join(parts, "dispenser")
    slots = []
    for i in range(5):
        e = empty("slot_%d" % i)
        e.location = B(0, 0, 2 - i)
        slots.append((e, root))
    export_anim(root, "dispenser", [(fg, root)] + slots, anim=False)


def spill():
    glow = mat("spill_glow", (0.3, 1.0, 0.72), 0.15, emit=2.0)
    bm = bmesh.new()
    segs, rings = 40, 5
    centre = bm.verts.new((0, 0, 0.04))
    prev = None
    rows = []
    for j in range(1, rings + 1):
        f = j / rings
        row = []
        for k in range(segs):
            a = TAU * k / segs
            r = 0.44 * f * (1 + 0.22 * noise.noise(Vector((math.cos(a) * 1.7, math.sin(a) * 1.7, 0.3)))
                            + 0.08 * math.sin(5 * a + 1))
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0.04 * (1 - f ** 3) + 0.004)))
        rows.append(row)
    for k in range(segs):
        bm.faces.new((centre, rows[0][k], rows[0][(k + 1) % segs]))
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r1[k], r1[(k + 1) % segs], r0[(k + 1) % segs]))
    me = bpy.data.meshes.new("pool")
    bm.to_mesh(me)
    bm.free()
    parts = [finish(link(me, "pool"), glow, smooth=80)]
    rnd = random.Random(29)
    for k in range(9):  # droplets
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(0.42, 0.56)
        parts.append(sphere(rnd.uniform(0.025, 0.045), (r * math.cos(a), r * math.sin(a), 0.02), glow,
                            scale=(1, 1, 0.6), segs=8, rings=5))
    for k in range(7):  # a crown of splashes
        a = TAU * k / 7 + rnd.uniform(-0.2, 0.2)
        r = 0.3
        base = Vector((r * math.cos(a), r * math.sin(a), 0.02))
        tip = base + Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, rnd.uniform(0.12, 0.2)))
        parts.append(rod(base, tip, 0.03, glow, r2=0.008, verts=6))
        parts.append(sphere(0.022, tip + Vector((math.cos(a) * 0.02, math.sin(a) * 0.02, 0.03)), glow, segs=6, rings=4))
    export(join(parts, "spill"), "spill")


# ------------------------------------------------------------------ workshop

def arch_poly(w, spring, segs=14):
    """An arched opening outline (x, z) for K.prism: from the sill (z 0) up to the spring line, then a half circle."""
    r = w / 2
    pts = [(-r, 0), (r, 0)]
    for k in range(segs + 1):
        a = math.pi * k / segs
        pts.append((r * math.cos(a), spring + r * math.sin(a)))
    return pts


def boolean(o, cutters):
    for c in cutters:
        m = o.modifiers.new("cut", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = c
        m.solver = "EXACT"
        select(o)
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(c, do_unlink=True)
    return o


WALL_Z = -4.6
WIN_X = (-2.5, 5.0, 12.5)
WIN_W = 4.2
WIN_SILL = 0.6
WIN_SPRING = 5.5   # sill + spring height; the top is at WIN_SILL + WIN_SPRING + WIN_W / 2 = 8.2


def bottle(x, y, z, kind, rnd, glass_mats, cork, label):
    """A bottle or jar standing at Godot (x, y, z)."""
    g = glass_mats[kind % len(glass_mats)]
    h = rnd.uniform(0.5, 0.95)
    r = rnd.uniform(0.11, 0.17)
    if kind % 3 == 0:  # tall bottle with a neck
        prof = [(0.0, h + 0.12), (0.035, h + 0.12), (0.04, h), (0.045, h * 0.72), (r, h * 0.55), (r, 0.03),
                (r * 0.9, 0.0), (0.0, 0.0)]
    elif kind % 3 == 1:  # round flask
        prof = [(0.0, h * 0.8 + 0.1), (0.03, h * 0.8 + 0.1), (0.035, h * 0.55), (r * 1.3, h * 0.35), (r * 1.25, h * 0.12),
                (r * 0.9, 0.0), (0.0, 0.0)]
    else:  # jar
        prof = [(0.0, h * 0.6), (r * 0.9, h * 0.6), (r, h * 0.55), (r, 0.02), (r * 0.95, 0.0), (0.0, 0.0)]
    o = lathe(prof, g, segs=12, name="bottle")
    out = [o]
    top = prof[0][1]
    if kind % 3 == 2:
        out.append(cyl(r * 0.95, 0.06, (0, 0, top + 0.02), cork, verts=12))
        out.append(cyl(r * 1.01, h * 0.25, (0, 0, h * 0.3), label, verts=12))
    else:
        out.append(cyl(0.04, 0.07, (0, 0, top + 0.02), cork, verts=8))
        if rnd.random() < 0.6:
            out.append(cyl(r * 1.01 if kind % 3 == 0 else r * 1.25, 0.14, (0, 0, h * 0.3), label, verts=12))
    j = join(out, "bottle")
    placed(j, T(B(x, y, z)) @ Rz(rnd.uniform(0, TAU)))
    return j


def lamp(x, y_bulb, z, M, cord_top=14.0):
    """A hanging lamp: cord from the ceiling, a brass conical shade with a cage, a glowing bulb at (x, y_bulb, z)."""
    parts = [rod(B(x, y_bulb + 0.55, z), B(x, cord_top, z), 0.025, M["cord"], verts=6)]
    shade = lathe([(0.0, 0.75), (0.1, 0.75), (0.14, 0.7), (0.2, 0.6), (0.6, 0.12), (0.72, 0.0), (0.7, -0.02),
                   (0.58, 0.1), (0.18, 0.56), (0.12, 0.64), (0.0, 0.64)], M["lamp_brass"], segs=24, name="shade")
    placed(shade, T(B(x, y_bulb - 0.1, z)))
    parts.append(shade)
    parts.append(torus(0.71, 0.03, B(x, y_bulb - 0.1, z), M["lamp_brass"], verts=24, minor=5))
    bulb = sphere(0.2, B(x, y_bulb - 0.05, z), M["lamp_glow"], scale=(1, 1, 1.25), segs=14, rings=8)
    parts.append(bulb)
    parts.append(cyl(0.11, 0.18, B(x, y_bulb + 0.2, z), M["lamp_brass"], verts=12))
    for k in range(6):  # a wire cage under the shade
        a = TAU * k / 6
        parts.append(tube([B(x + 0.62 * math.cos(a), y_bulb - 0.08, z + 0.62 * math.sin(a)),
                           B(x + 0.4 * math.cos(a), y_bulb - 0.36, z + 0.4 * math.sin(a)),
                           B(x, y_bulb - 0.45, z)], [0.012] * 3, M["lamp_brass"], verts=5, caps=False))
    return parts


def steam_pipe(points, r, M, flanges=True):
    out = [tube([B(*p) for p in points], [r] * len(points), M["steam"], verts=12, caps=False)]
    for p in points[1:-1]:
        out.append(sphere(r * 1.25, B(*p), M["brass"], segs=12, rings=8))
    if flanges:
        for a, b in zip(points, points[1:]):
            av, bv = Vector(B(*a)), Vector(B(*b))
            d = (bv - av)
            ln = d.length
            if ln < 1.2:
                continue
            t = d.normalized()
            for f in (0.25, 0.75) if ln > 4 else (0.5,):
                c = av + d * f
                out.append(rod(c - t * 0.05, c + t * 0.05, r * 1.45, M["brass"], verts=14))
    return out


def workshop():
    rnd = random.Random(2929)
    M = dict(
        wood=mat("bench_wood", (0.42, 0.24, 0.12), 0.55),
        bench_brass=mat("bench_brass", (0.8, 0.58, 0.27), 0.3, 1.0),
        leather=mat("board_leather", (0.035, 0.1, 0.07), 0.7),
        grid=mat("board_grid", (0.62, 0.46, 0.22), 0.4, 1.0),
        board_brass=mat("board_brass", (0.84, 0.62, 0.28), 0.25, 1.0),
        brick=mat("brick", (0.45, 0.2, 0.13), 0.85),
        stone=mat("stone_trim", (0.46, 0.38, 0.3), 0.85),
        night=mat("window_night_glow", (0.05, 0.08, 0.2), 0.3, emit=1.0, emit_color=(0.06, 0.1, 0.25)),
        moon=mat("window_moon_glow", (0.05, 0.08, 0.2), 0.3, emit=1.0, emit_color=(0.08, 0.12, 0.3)),
        win_iron=mat("window_iron", (0.07, 0.07, 0.08), 0.5, 0.7),
        floor=mat("floor_wood", (0.3, 0.18, 0.1), 0.7),
        shelf=mat("shelf_wood", (0.36, 0.21, 0.11), 0.6),
        iron=mat("workshop_iron", (0.13, 0.13, 0.14), 0.5, 0.8),
        brass=mat("workshop_brass", (0.8, 0.58, 0.26), 0.3, 1.0),
        steam=mat("steam_copper", (0.78, 0.36, 0.22), 0.35, 1.0),
        red=mat("valve_red", (0.62, 0.07, 0.04), 0.3, coat=0.6),
        gear_brass=mat("gear_brass", (0.78, 0.56, 0.25), 0.32, 1.0),
        gear_iron=mat("gear_iron", (0.2, 0.19, 0.19), 0.45, 0.85),
        piston=mat("piston_steel", (0.62, 0.64, 0.66), 0.2, 1.0),
        lamp_brass=mat("lamp_brass", (0.72, 0.5, 0.22), 0.35, 1.0),
        lamp_glow=mat("lamp_glow", (1.0, 0.78, 0.45), 0.3, emit=9.0, emit_color=(1.0, 0.7, 0.38)),
        cord=mat("lamp_cord", (0.06, 0.05, 0.05), 0.8),
        vat_glass=mat("vat_glass", (0.8, 0.92, 0.95), 0.03, alpha=0.2),
        vat_glow=mat("vat_glow", (0.3, 1.0, 0.72), 0.2, emit=2.5),
        face=mat("clock_face", (0.93, 0.88, 0.74), 0.45),
        hand=mat("clock_hand", (0.08, 0.07, 0.07), 0.4, 0.6),
        alarm=mat("alarm_glow", (0.9, 0.12, 0.06), 0.3, emit=0.6, emit_color=(1.0, 0.15, 0.05)),
        paper=mat("blueprint", (0.12, 0.25, 0.55), 0.8),
        paper_line=mat("blueprint_line", (0.8, 0.88, 0.95), 0.8),
        cork=mat("cork", (0.5, 0.36, 0.22), 0.8),
        label=mat("label_paper", (0.85, 0.78, 0.6), 0.8),
        book_a=mat("book_red", (0.42, 0.08, 0.06), 0.7),
        book_b=mat("book_green", (0.1, 0.25, 0.15), 0.7),
        book_c=mat("book_blue", (0.1, 0.13, 0.3), 0.7),
        steel=mat("tool_steel", (0.55, 0.57, 0.6), 0.3, 1.0),
        handle=mat("tool_handle", (0.5, 0.3, 0.15), 0.6),
        mug=mat("mug_enamel", (0.85, 0.85, 0.8), 0.3, coat=0.5),
        coffee=mat("coffee", (0.08, 0.04, 0.02), 0.1),
    )
    glass_mats = [mat("bottle_green", (0.2, 0.6, 0.3), 0.05, alpha=0.6),
                  mat("bottle_amber", (0.8, 0.45, 0.1), 0.05, alpha=0.6),
                  mat("bottle_blue", (0.15, 0.3, 0.75), 0.05, alpha=0.6),
                  mat("bottle_clear", (0.85, 0.9, 0.9), 0.05, alpha=0.35)]
    children = []
    root = empty("workshop")

    def child(o):
        children.append((o, root))
        return o

    # ---- the bench
    bench = [gbox(23.0, 0.6, 14.9, 5.0, -0.45, 3.05, M["wood"], bevel=0.06, segs=2)]
    for z in (-4.43, 10.53):
        bench.append(gbox(23.1, 0.14, 0.06, 5.0, -0.2, z, M["bench_brass"], bevel=0.01))
    for x in (-6.53, 16.53):
        bench.append(gbox(0.06, 0.14, 15.0, x, -0.2, 3.05, M["bench_brass"], bevel=0.01))
    for x in (-6.5, 16.5):
        for z in (-4.4, 10.5):
            bench.append(gbox(0.5, 0.66, 0.5, x, -0.45, z, M["bench_brass"], bevel=0.04))
    for x in (-5.6, 15.6):
        for z in (-3.6, 9.6):
            bench.append(lathe([(0.0, -0.75), (0.5, -0.75), (0.55, -1.0), (0.38, -1.4), (0.42, -2.0), (0.32, -2.4),
                                (0.32, -7.5), (0.42, -8.0), (0.36, -9.5), (0.0, -9.5)], M["wood"], segs=14,
                               name="leg"))
            placed(bench[-1], T((x, -z, 0)))
    bench.append(gbox(22.0, 0.5, 0.3, 5.0, -7.5, -3.6, M["wood"]))
    bench.append(gbox(22.0, 0.5, 0.3, 5.0, -7.5, 9.6, M["wood"]))
    child(join(bench, "bench"))

    # ---- the board
    child(join([gbox(10.0, 0.15, 7.0, 5.0, -0.075, 3.5, M["leather"], bevel=0.005)], "board_bed"))
    grid = []
    for c in range(11):
        grid.append(gbox(0.03, 0.006, 7.0, float(c), 0.001, 3.5, M["grid"], bevel=0))
    for r in range(8):
        grid.append(gbox(10.0, 0.006, 0.03, 5.0, 0.001, float(r), M["grid"], bevel=0))
    child(join(grid, "board_grid"))
    frame = []
    for z in (-0.17, 7.17):
        frame.append(gbox(10.64, 0.22, 0.3, 5.0, -0.04, z, M["board_brass"], bevel=0.03, segs=2))
    for x in (-0.17, 10.17):
        frame.append(gbox(0.3, 0.22, 7.04, x, -0.04, 3.5, M["board_brass"], bevel=0.03, segs=2))
    for x in [-0.17 + 10.34 * i / 10 for i in range(11)]:
        for z in (-0.17, 7.17):
            frame.append(rivet(B(x, 0.07, z), 0.04, M["iron"]))
    for z in [-0.17 + 7.34 * i / 7 for i in range(8)]:
        for x in (-0.17, 10.17):
            frame.append(rivet(B(x, 0.07, z), 0.04, M["iron"]))
    for x in (-0.17, 10.17):
        for z in (-0.17, 7.17):
            frame.append(cyl(0.24, 0.08, B(x, 0.1, z), M["board_brass"], verts=16, bevel=0.02))
    child(join(frame, "board_frame"))

    # ---- the room: walls with arched windows, floor
    room = []
    back = gbox(34.0, 24.0, 0.6, 5.0, 2.5, WALL_Z - 0.3, M["brick"], bevel=0)
    cutters = []
    for x in WIN_X:
        c = prism(arch_poly(WIN_W, WIN_SPRING), 2.0, (0, 0, 0), M["brick"], bevel=0)
        placed(c, T(B(x, WIN_SILL, WALL_Z)))
        cutters.append(c)
    boolean(back, cutters)
    room.append(back)
    for x in (-11.3, 21.3):
        room.append(gbox(0.6, 24.0, 22.0, x, 2.5, 4.0, M["brick"], bevel=0))
    room.append(gbox(34.0, 0.3, 22.0, 5.0, -9.65, 4.0, M["floor"], bevel=0))
    # brick piers' plinth and a cornice
    room.append(gbox(34.0, 0.5, 0.25, 5.0, 13.0, WALL_Z + 0.1, M["stone"], bevel=0.04))
    for x in WIN_X:
        # night pane (recessed), sill, voussoirs, glazing bars
        pane = prism(arch_poly(WIN_W, WIN_SPRING), 0.04, (0, 0, 0), M["moon"] if x == WIN_X[1] else M["night"],
                     bevel=0)
        placed(pane, T(B(x, WIN_SILL, WALL_Z - 0.5)))
        room.append(pane)
        room.append(gbox(WIN_W + 0.7, 0.22, 0.95, x, WIN_SILL - 0.08, WALL_Z - 0.05, M["stone"], bevel=0.04))
        r = WIN_W / 2
        n = 13
        for k in range(n):
            a0 = math.pi * k / n
            a1 = math.pi * (k + 1) / n
            am = (a0 + a1) / 2
            rr = r + 0.3
            cx, cy = x + rr * math.cos(am), WIN_SILL + WIN_SPRING + rr * math.sin(am)
            o = box((0.6 if k != n // 2 else 0.75, 0.3, r * (a1 - a0) + 0.1 - 0.06), (0, 0, 0), M["stone"], bevel=0.03)
            placed(o, T(B(cx, cy, WALL_Z + 0.08)) @ Ry(-am))
            room.append(o)
        for sx in (-1, 1):
            for j in range(4):
                y0 = WIN_SILL + 0.3 + j * 1.35
                room.append(gbox(0.55 if j % 2 else 0.4, 1.2, 0.3, x + sx * (r + 0.25 + (0.06 if j % 2 else 0)),
                                 y0 + 0.6, WALL_Z + 0.08, M["stone"], bevel=0.03))
        # glazing bars: mullions, transoms and the arch's radial bars
        z = WALL_Z - 0.45
        for bx in (-r * 0.5, 0.0, r * 0.5):
            hgt = WIN_SPRING + math.sqrt(max(r * r - bx * bx, 0))
            room.append(gbox(0.08, hgt, 0.08, x + bx, WIN_SILL + hgt / 2, z, M["win_iron"], bevel=0.01))
        for by in (1.4, 2.8, 4.2, WIN_SPRING):
            room.append(gbox(WIN_W, 0.08, 0.08, x, WIN_SILL + by, z, M["win_iron"], bevel=0.01))
        for k in (1, 2, 3):
            a = math.pi * k / 4
            p0 = Vector(B(x, WIN_SILL + WIN_SPRING, z))
            p1 = Vector(B(x + r * math.cos(a), WIN_SILL + WIN_SPRING + r * math.sin(a), z))
            room.append(rod(p0, p1, 0.04, M["win_iron"], verts=6))
        arc = [B(x + (r - 0.04) * math.cos(math.pi * k / 16), WIN_SILL + WIN_SPRING + (r - 0.04) * math.sin(math.pi * k / 16),
                 z) for k in range(17)]
        room.append(tube(arc, [0.045] * 17, M["win_iron"], verts=6, caps=False))
        rr2 = r * 0.55
        arc2 = [B(x + rr2 * math.cos(math.pi * k / 12), WIN_SILL + WIN_SPRING + rr2 * math.sin(math.pi * k / 12), z)
                for k in range(13)]
        room.append(tube(arc2, [0.04] * 13, M["win_iron"], verts=6, caps=False))
    child(join(room, "room"))

    # ---- shelves between the windows, with bottles, jars, books, tins
    shelves = []
    for x0, x1, levels in ((0.25, 2.25, 3), (7.75, 9.75, 3), (-9.8, -6.0, 2), (15.6, 19.6, 2)):
        cx = (x0 + x1) / 2
        w = x1 - x0
        for k, y in enumerate((1.2, 3.0, 4.8)[:levels]):
            shelves.append(gbox(w, 0.12, 0.9, cx, y, WALL_Z + 0.45, M["shelf"], bevel=0.02))
            for sx in (x0 + 0.25, x1 - 0.25):
                shelves.append(gbox(0.08, 0.5, 0.08, sx, y - 0.3, WALL_Z + 0.08, M["iron"], bevel=0))
                shelves.append(rod(B(sx, y - 0.5, WALL_Z + 0.05), B(sx, y - 0.06, WALL_Z + 0.8), 0.03, M["iron"],
                                   verts=5))
            x = x0 + 0.25
            while x < x1 - 0.3:
                kind = rnd.randrange(9)
                if kind < 6:
                    shelves.append(bottle(x, y + 0.06, WALL_Z + 0.45 + rnd.uniform(-0.15, 0.15), kind, rnd,
                                          glass_mats, M["cork"], M["label"]))
                    x += rnd.uniform(0.38, 0.55)
                elif kind < 8:
                    nb = rnd.randrange(3, 6)
                    for b in range(nb):
                        hb = rnd.uniform(0.55, 0.8)
                        shelves.append(gbox(0.1, hb, rnd.uniform(0.5, 0.65), x + b * 0.11, y + 0.06 + hb / 2,
                                            WALL_Z + 0.42, [M["book_a"], M["book_b"], M["book_c"]][rnd.randrange(3)],
                                            bevel=0.01))
                    x += nb * 0.11 + 0.15
                else:
                    shelves.append(cyl(0.16, 0.3, B(x + 0.1, y + 0.21, WALL_Z + 0.45), M["brass"], verts=14,
                                       bevel=0.01))
                    x += 0.45
    child(join(shelves, "shelves"))

    # ---- steam pipes along the back wall and the walls
    pipes = []
    py = 0.55
    pz = WALL_Z + 0.35
    pipes += steam_pipe([(-11.0, py, pz), (21.0, py, pz)], 0.16, M)
    pipes += steam_pipe([(-11.0, 12.0, pz), (21.0, 12.0, pz)], 0.13, M)
    for x in (-5.6, 3.0, 7.0):
        pipes += steam_pipe([(x, py, pz + 0.0), (x, 12.0, pz)], 0.11, M)
        pipes.append(sphere(0.2, B(x, py, pz), M["brass"], segs=12, rings=8))
        pipes.append(sphere(0.17, B(x, 12.0, pz), M["brass"], segs=12, rings=8))
    pipes += steam_pipe([(-10.7, -9.5, 0.0), (-10.7, 12.0, 0.0), (-10.7, 12.0, pz)], 0.13, M)
    pipes += steam_pipe([(20.7, -9.5, 2.0), (20.7, py, 2.0), (20.7, py, pz)], 0.16, M)
    # valve wheels and vent stubs along the low pipe
    for x in (-8.5, -1.2, 10.8, 18.5):
        pipes.append(cyl(0.13, 0.4, B(x, py + 0.3, pz), M["brass"], verts=12))
        w = wheel(0.32, M["red"], M["brass"])
        placed(w, T(B(x, py + 0.55, pz)))
        pipes.append(w)
    vents = [(-7.0, py, pz), (4.0, py, pz), (8.6, py, pz), (3.0, 7.5, pz), (-5.6, 7.5, pz)]
    for i, (x, y, z) in enumerate(vents):
        if y == py:
            pipes.append(rod(B(x, y, z), B(x, y + 0.55, z), 0.07, M["steam"], verts=10))
            pipes.append(cyl(0.11, 0.08, B(x, y + 0.55, z), M["brass"], r2=0.07, verts=12))
            e = empty("vent_%d" % i)
            e.location = B(x, y + 0.62, z)
        else:
            pipes.append(rod(B(x, y, z), B(x, y, z + 0.4), 0.06, M["steam"], verts=10))
            pipes.append(cyl(0.1, 0.08, B(x, y, z + 0.42), M["brass"], verts=12, rot=(math.pi / 2, 0, 0)))
            e = empty("vent_%d" % i)
            e.location = B(x, y, z + 0.5)
        children.append((e, root))
    # gauges on the pipes
    for x, y in ((-3.9, 12.0), (10.2, 12.0)):
        g = gauge(0.4, M["face"], M["brass"], mat("gauge_needle", (0.7, 0.05, 0.03), 0.35), M["iron"])
        placed(g, T(B(x, y + (0.62 if y == py else -0.62), pz + 0.12)) @ Rx(math.radians(90)))
        pipes.append(g)
        pipes.append(rod(B(x, y, pz), B(x, y + (0.25 if y == py else -0.25), pz), 0.05, M["brass"], verts=8))
    # the alarm lamp on the low pipe
    pipes.append(cyl(0.16, 0.18, B(6.0, py + 0.24, pz), M["brass"], verts=14))
    al = sphere(0.22, B(6.0, py + 0.48, pz), M["alarm"], scale=(1, 1, 1.15), segs=14, rings=8)
    alarm = child(join([al], "alarm_lamp"))
    for k in range(4):
        a = TAU * k / 4
        pipes.append(tube([B(6.0 + 0.21 * math.cos(a), py + 0.3, pz + 0.21 * math.sin(a)),
                           B(6.0 + 0.26 * math.cos(a), py + 0.5, pz + 0.26 * math.sin(a)),
                           B(6.0, py + 0.78, pz)], [0.018] * 3, M["brass"], verts=5, caps=False))
    e = empty("alarm_light")
    e.location = B(6.0, py + 0.5, pz + 0.3)
    children.append((e, root))
    child(join(pipes, "pipes"))

    # ---- gears on the back wall and the left wall; the bench machine at the back right
    def add_gear(name, r, teeth, loc, axis, thick=0.12, m=None, spokes=5):
        g = gear(r, teeth, thick, m or M["gear_brass"], hub=M["gear_iron"], spokes=spokes, name=name)
        rot = Rx(math.radians(90)) if axis == "z" else Ry(math.radians(90))
        placed(g, T(B(*loc)) @ rot)
        g = join([g], name, pivot=B(*loc))
        child(g)
        return g

    gz = WALL_Z + 0.25
    add_gear("gear_0", 1.7, 28, (-7.6, 6.8, gz), "z", m=M["gear_brass"], spokes=6)
    add_gear("gear_1", 0.9, 15, (-7.6 - 2.18, 6.8 - 1.0, gz + 0.14), "z", m=M["gear_iron"])
    add_gear("gear_2", 1.4, 23, (17.2, 6.0, gz), "z", spokes=6)
    add_gear("gear_3", 0.75, 12, (17.2 + 1.8, 6.0 - 0.9, gz + 0.14), "z", m=M["gear_iron"])
    # wall gear backing plates
    plates = []
    for x, y, r in ((-7.6, 6.8, 1.9), (17.2, 6.0, 1.6)):
        plates.append(cyl(r * 0.25, 0.3, B(x, y, WALL_Z + 0.1), M["iron"], verts=16, rot=(math.pi / 2, 0, 0)))
    # the bench machine: a brass frame at the back right with three gears and two pistons
    mx, mz = 13.4, -3.0
    frame = [gbox(3.6, 0.2, 1.3, mx, -0.05, mz, M["iron"], bevel=0.03)]
    for sx in (-1.65, 1.65):
        frame.append(gbox(0.16, 3.0, 0.16, mx + sx, 1.5, mz - 0.4, M["brass"], bevel=0.02))
        frame.append(gbox(0.16, 3.0, 0.16, mx + sx, 1.5, mz + 0.4, M["brass"], bevel=0.02))
    frame.append(gbox(3.5, 0.16, 0.16, mx, 3.0, mz - 0.4, M["brass"], bevel=0.02))
    frame.append(gbox(3.5, 0.16, 0.16, mx, 3.0, mz + 0.4, M["brass"], bevel=0.02))
    frame.append(gbox(3.5, 0.12, 0.9, mx, 3.1, mz, M["brass"], bevel=0.02))
    frame.append(gbox(3.3, 2.6, 0.08, mx, 1.5, mz - 0.45, M["iron"], bevel=0.01))
    add_gear("gear_4", 0.95, 16, (mx - 0.55, 1.45, mz + 0.05), "z", thick=0.1)
    add_gear("gear_5", 0.55, 9, (mx - 0.55 + 0.95 + 0.55 - 0.13, 1.45 + 0.35, mz + 0.18), "z", thick=0.1,
             m=M["gear_iron"])
    add_gear("gear_6", 0.38, 7, (mx + 1.27, 1.04, mz + 0.05), "z", thick=0.1)
    # two pistons: cylinders on the frame, rods (children) driven by gear_4's crank
    for i, px in enumerate((mx - 1.25, mx + 0.5)):
        frame.append(cyl(0.2, 0.9, B(px, 2.45, mz + 0.35), M["brass"], verts=16))
        frame.append(cyl(0.24, 0.08, B(px, 2.0, mz + 0.35), M["brass"], verts=16))
        frame.append(cyl(0.24, 0.08, B(px, 2.9, mz + 0.35), M["brass"], verts=16))
        rod_parts = [cyl(0.06, 1.2, B(px, 1.4, mz + 0.35), M["piston"], verts=10),
                     gbox(0.3, 0.14, 0.18, px, 0.8, mz + 0.35, M["brass"], bevel=0.02)]
        p = join(rod_parts, "piston_%d" % i, pivot=B(px, 0.8, mz + 0.35))
        child(p)
    child(join(frame + plates, "machine"))

    # ---- the clock above the middle window
    cx, cy, cz = 5.0, 10.1, WALL_Z + 0.15
    cl = [cyl(1.15, 0.25, (0, 0, 0), M["brass"], verts=40, bevel=0.03),
          torus(1.08, 0.07, (0, 0, 0.13), M["brass"], verts=40, minor=6),
          cyl(1.0, 0.02, (0, 0, 0.13), M["face"], verts=40)]
    for k in range(12):
        a = TAU * k / 12
        big = k % 3 == 0
        cl.append(box((0.07 if big else 0.04, 0.2 if big else 0.12, 0.01),
                      (0.84 * math.sin(a), 0.84 * math.cos(a), 0.145), M["hand"], rot=(0, 0, -a), bevel=0))
    for k in range(8):
        a = TAU * k / 8
        cl.append(rivet((1.17 * math.cos(a), 1.17 * math.sin(a), 0.1), 0.05, M["iron"]))
    clock = join(cl, "clock")
    placed(clock, T(B(cx, cy, cz)) @ Rx(math.radians(90)))
    clock = join([clock], "clock", pivot=B(cx, cy, cz))
    child(clock)
    hh = join([box((0.08, 0.55, 0.015), (0, 0.22, 0.17), M["hand"], bevel=0),
               cyl(0.07, 0.03, (0, 0, 0.17), M["brass"], verts=10)], "clock_hour")
    mh = join([box((0.05, 0.85, 0.015), (0, 0.36, 0.19), M["hand"], bevel=0)], "clock_minute")
    for hnd in (hh, mh):
        placed(hnd, T(B(cx, cy, cz)) @ Rx(math.radians(90)))
    hh = join([hh], "clock_hour", pivot=B(cx, cy, cz))
    mh = join([mh], "clock_minute", pivot=B(cx, cy, cz))
    children.append((hh, clock))
    children.append((mh, clock))

    # ---- hanging lamps over the back of the bench and the sides
    for i, (x, y, z) in enumerate(((-1.0, 3.0, -2.6), (5.0, 3.3, -2.9), (10.0, 3.0, -2.6), (-5.0, 3.6, 4.0),
                                   (15.2, 3.6, 4.5))):
        lp = lamp(x, y, z, M)
        child(join(lp, "lamp_%d" % i))
        e = empty("lamp_light_%d" % i)
        e.location = B(x, y - 0.1, z)
        children.append((e, root))

    # ---- the vat of glow at the back left
    vx, vz = -4.2, -2.9
    vat = [lathe([(0.0, 0.25), (1.0, 0.25), (1.05, 0.15), (1.05, -0.15), (0.0, -0.15)][::-1][::-1], M["brass"], segs=28,
                 name="vbase")]
    vat.append(lathe([(0.0, 2.75), (0.25, 2.72), (0.7, 2.55), (1.0, 2.38), (1.02, 2.3), (0.95, 2.3), (0.0, 2.3)],
                     M["brass"], segs=28, name="vlid"))
    for y in (0.95, 1.65):
        vat.append(torus(0.93, 0.04, (0, 0, y), M["brass"], verts=28, minor=5))
    for k in range(6):
        a = TAU * k / 6
        vat.append(box((0.08, 0.05, 2.1), (0.92 * math.cos(a), 0.92 * math.sin(a), 1.27), M["brass"], rot=(0, 0, a),
                       bevel=0.01))
    vat.append(cyl(0.08, 0.5, (0, 0, 2.95), M["brass"], verts=10))
    g = gauge(0.25, M["face"], M["brass"], mat("gauge_needle", (0.7, 0.05, 0.03), 0.35), M["iron"])
    placed(g, T((0.0, -0.75, 2.6)) @ Rx(math.radians(55)))
    vat.append(g)
    vat_glass = cyl(0.9, 2.05, (0, 0, 1.27), M["vat_glass"], verts=28)
    vat.append(tube([(0.0, 0.0, 2.7), (0.0, 0.5, 3.4), (0.0, 1.3, 3.6), (0.0, 1.65, 3.0), (0.0, 1.65, 0.7)],
                    [0.1] * 5, M["steam"], verts=10, caps=False))
    vat.append(tube([(0.85, 0.0, 0.6), (1.4, 0.0, 0.6), (1.6, 0.0, 0.4), (1.6, 0.0, -0.1)], [0.08] * 4, M["steam"],
                    verts=10, caps=False))
    w = wheel(0.22, M["red"], M["brass"])
    placed(w, T((1.25, -0.14, 0.6)) @ Rx(math.radians(90)))
    vat.append(w)
    for o in vat + [vat_glass]:
        placed(o, T(B(vx, -0.15, vz)))
    child(join(vat, "vat"))
    child(join([vat_glass], "vat_glass"))
    vg = cyl(0.85, 1.95, B(vx, -0.15 + 0.27 + 0.975, vz), M["vat_glow"], verts=24)
    child(join([vg], "vat_glow", pivot=B(vx, -0.15 + 0.27, vz)))
    e = empty("bubbles_0")
    e.location = B(vx, 0.15, vz)
    children.append((e, root))

    # ---- props on the bench margins
    props = []
    y0 = -0.15

    def lay(o, x, z, yaw=0.0, y=y0):
        placed(o, T(B(x, y, z)) @ Rz(yaw))
        return o

    def wrench(size):
        p = [box((1.0 * size, 0.12 * size, 0.04 * size), (0, 0, 0.02 * size), M["steel"], bevel=0.01)]
        for sx in (-1, 1):
            p.append(cyl(0.12 * size, 0.045 * size, (sx * 0.5 * size, 0, 0.022 * size), M["steel"], verts=14))
        p.append(box((0.12 * size, 0.09 * size, 0.05 * size), (0.58 * size, 0, 0.025 * size), M["wood"], bevel=0))
        return join(p, "wrench")

    # blueprints on the right margin, a wrench and a hammer on them
    bp = gbox(4.0, 0.01, 3.0, 13.4, y0 + 0.005, 3.0, M["paper"], bevel=0)
    props.append(bp)
    for k in range(9):
        props.append(gbox(3.6 if k % 3 else 2.2, 0.004, 0.03, 13.3 + (0.6 if k % 3 == 0 else 0), y0 + 0.012,
                          1.8 + k * 0.28, M["paper_line"], bevel=0))
    for rr in (0.7, 0.45):
        props.append(torus(rr, 0.016, (0, 0, 0), M["paper_line"], verts=32, minor=3, scale=(1, 1, 0.25)))
        lay(props[-1], 14.4, 3.4, y=y0 + 0.012)
    props.append(lay(wrench(1.6), 12.4, 5.3, 0.4))
    props.append(lay(wrench(1.1), 15.3, 1.5, -1.2))
    ham = [box((0.22, 0.6, 0.22), (0, 0.0, 0.11), M["iron"], bevel=0.02),
           rod((0, 0, 0.11), (1.5, 0.0, 0.11), 0.06, M["handle"], verts=8)]
    props.append(lay(join(ham, "hammer"), 13.0, 6.9, 2.6))
    # an oil can
    can = lathe([(0.0, 0.62), (0.08, 0.62), (0.1, 0.5), (0.35, 0.32), (0.4, 0.25), (0.4, 0.02), (0.38, 0.0),
                 (0.0, 0.0)], M["brass"], segs=16, name="can")
    spout = rod((0.0, 0.0, 0.55), (0.75, 0.0, 1.15), 0.03, M["brass"], r2=0.012, verts=8)
    props.append(lay(join([can, spout], "oilcan"), 15.4, 5.6, 2.2))
    # a mug of coffee
    mugp = [lathe([(0.0, 0.0), (0.26, 0.0), (0.27, 0.6), (0.24, 0.6), (0.24, 0.05), (0.0, 0.05)][::-1], M["mug"],
                  segs=18, name="mug"),
            cyl(0.235, 0.02, (0, 0, 0.5), M["coffee"], verts=18),
            torus(0.15, 0.04, (0.3, 0, 0.3), M["mug"], rot=(math.pi / 2, 0, 0), verts=12, minor=5)]
    props.append(lay(join(mugp, "mug"), 11.4, 8.4, 0.8))
    # a bench vice at the front right corner
    vice = [box((0.9, 0.7, 0.35), (0, 0, 0.17), M["iron"], bevel=0.03),
            box((0.9, 0.22, 0.5), (0, 0.3, 0.6), M["iron"], bevel=0.03),
            box((0.9, 0.22, 0.5), (0, -0.3, 0.6), M["iron"], bevel=0.03),
            rod((0, -1.0, 0.55), (0, 0.4, 0.55), 0.05, M["steel"], verts=8),
            rod((-0.4, -1.0, 0.55), (0.4, -1.0, 0.55), 0.035, M["steel"], verts=8)]
    for sx in (-1, 1):
        vice.append(sphere(0.07, (sx * 0.42, -1.0, 0.55), M["steel"]))
    props.append(lay(join(vice, "vice"), 15.2, 8.6, math.radians(90)))
    # spare pipe pieces and screws on the left margin, a toolbox
    for k, (x, z, yaw) in enumerate(((-4.7, 1.6, 0.3), (-3.4, 2.4, 1.2), (-4.6, 6.2, -0.4), (-3.2, 7.6, 2.0))):
        p = [rod((-0.5, 0, 0.17), (0.5, 0, 0.17), 0.16, M["steam"], verts=14),
             rod((-0.5, 0, 0.17), (-0.45, 0, 0.17), 0.19, M["brass"], verts=14),
             rod((0.45, 0, 0.17), (0.5, 0, 0.17), 0.19, M["brass"], verts=14)]
        props.append(lay(join(p, "spare"), x, z, yaw))
    for k in range(22):
        x, z = -4.2 + rnd.uniform(-1.6, 1.6), 4.4 + rnd.uniform(-0.9, 0.9)
        props.append(lay(join([cyl(0.06, 0.03, (0, 0, 0.015), M["brass"], verts=6),
                               rod((0, 0, 0.02), (0.22, 0, 0.03), 0.022, M["steel"], verts=5)], "screw"), x, z,
                         rnd.uniform(0, TAU)))
    tb = [box((2.2, 1.0, 0.7), (0, 0, 0.35), M["red"], bevel=0.04),
          box((2.26, 1.06, 0.08), (0, 0, 0.7), M["iron"], bevel=0.02),
          rod((-0.7, 0, 0.75), (-0.7, 0, 1.05), 0.04, M["iron"], verts=6),
          rod((0.7, 0, 0.75), (0.7, 0, 1.05), 0.04, M["iron"], verts=6),
          rod((-0.7, 0, 1.05), (0.7, 0, 1.05), 0.05, M["iron"], verts=8)]
    props.append(lay(join(tb, "toolbox"), -4.3, 8.9, 0.15))
    # a candle-less brass oil lamp... a pressure-gauge panel standing at the back left of the board
    panel = [box((2.4, 0.3, 1.6), (0, 0, 0.8), M["iron"], bevel=0.04)]
    for k, (gx, gzz, gr) in enumerate(((-0.65, 0.95, 0.42), (0.6, 1.0, 0.36), (0.0, 0.42, 0.24))):
        gg = gauge(gr, M["face"], M["brass"], mat("gauge_needle", (0.7, 0.05, 0.03), 0.35), M["iron"])
        placed(gg, T((gx, -0.16, gzz)) @ Rx(math.radians(90)))
        panel.append(gg)
    panel.append(box((2.5, 0.36, 0.1), (0, 0, 1.62), M["brass"], bevel=0.02))
    props.append(lay(join(panel, "panel"), 1.6, -2.7, 0.0))
    # coiled copper tube and a crate of glass tubes at the back centre
    coil = [B(8.0 + 0.45 * math.cos(a), y0 + 0.12 + 0.05 * a, -2.4 + 0.45 * math.sin(a)) for a in
            [k * 0.35 for k in range(72)]]
    props.append(tube(coil, [0.055] * len(coil), M["steam"], verts=8))
    crate = [box((1.4, 1.0, 0.6), (0, 0, 0.3), M["shelf"], bevel=0.03)]
    for k in range(7):
        crate.append(rod((-0.5 + k * 0.16, -0.2, 0.3), (-0.5 + k * 0.16, 0.6, 1.0), 0.06, glass_mats[3], verts=8))
    props.append(lay(join(crate, "crate"), 9.8, -2.6, 0.1))
    child(join(props, "props"))

    export_anim(root, "workshop", children, anim=False)


JOBS = {"pipe_straight": pipe_straight, "pipe_corner": pipe_corner, "pipe_cross": pipe_cross, "source": source,
        "block": block, "cursor": cursor, "dispenser": dispenser, "spill": spill, "workshop": workshop}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
