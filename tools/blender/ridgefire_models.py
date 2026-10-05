"""Ridgefire (game 30) models: the artillery tank, five projectiles (shell, missile, nuke, roller, digger), the
parachute supply crate, the victory flag and the debris a destroyed tank scatters.
Original designs (our own shapes, nothing from any artillery game): a chunky, toy-like little tank with big road
wheels on toothed tracks, riveted side skirts in three panels, an egg-shaped turret with a commander's cupola, a
pill mantlet and a long gun with a fume extractor and a slotted muzzle brake, headlamps on the fenders, a wooden
stowage box, a rolled tarp, spare track links on the nose and a whip antenna with a pennant.
Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/ridgefire_models.py -- godot/games/ridgefire/art/models [name ...]
     (TRIS=1 also prints the triangles per material)
Helpers come from blastyard_models.py (mat, box, sphere, torus, rod, tube, join, ...), prism_models.py (export_anim,
empty, new_obj), mossfolk_models.py (lathe_r, solid), hopline_models.py (ell) and marbledrift_models.py (mesh_from,
dims).

Units: metres. Built in Blender with X forward/right, Z up and the camera side towards -Y, which exports as Godot
+X right, +Y up and +Z towards the camera. No animations: the view moves the nodes. Emissive materials all have "glow"
in their names.

tank.glb      root empty "tank", origin at the bottom centre (the tracks' contact line, y = 0), facing +X (the gun
              to the right), the camera side +Z. The tracks run x -1.61 .. +1.61 (exhausts and tow eyes to -1.76 /
              +1.71), 2.04 wide over the skirts (z -1.02 .. 1.02); the deck at y 0.94, the turret roof 1.36, the
              cupola 1.41; the gun reaches x = 2.22 when level; the antenna rises to 2.41 (on the far side, z -0.32).
              Children:
                hull          the body, both tracks, skirts, lamps, stowage (static)
                  wheel_0..4  road wheels, radius 0.20, axles at y = 0.285, x = -0.9, -0.45, 0, 0.45, 0.9 (the left
                              and right wheel of an axle are one node, its origin on the axle at z = 0)
                  wheel_front the toothed drive sprocket, radius 0.22 (to the track's inner face), at (1.30, 0.44)
                  wheel_rear  the idler, radius 0.22, at (-1.30, 0.44)
                              Spin them all about local Z: rotation.z -= distance_moved / radius (moving +X).
                turret        origin at the turret ring centre (x -0.15, y 0.94); fixed (no traverse)
                  barrel      origin on the trunnion (turret local (0.75, 0.21, 0), i.e. tank (0.60, 1.15, 0)); local
                              +X along the bore. rotation.z = aim angle: 0 = level to +X, PI/2 = straight up. For an
                              aim towards -X (angle a > PI/2) mirror the whole tank (tank.scale.x = -1) or turn it by
                              PI about Y, and set barrel.rotation.z = PI - a: the gun then stays clear of the antenna
                              and the stowage at any angle 0 .. PI/2. The mantlet (a pill across the turret face)
                              turns with the gun. For recoil, offset the barrel from its rest position (0.75, 0.21).
                    muzzle    empty at the muzzle (barrel local x 1.62): the shot's spawn point; its +X is the shot's
                              direction (use muzzle.global_transform)
                  pennant     origin at the antenna tip's hoist (turret local (-0.45, 1.36, -0.32), tank y 2.30): a
                              two-sided 0.46 x 0.24 pennant streaming towards -X, a player-colour stripe at the hoist,
                              subdivided 12 x 4 for waving (rotate it about Y to swing with the wind; mirror the
                              tank and it streams the other way)
              Materials: tank_paint (THE PLAYER COLOUR: recolour it per player; red in the file), tank_metal (steel
              trim, hub caps, brake, bands, exhausts), tank_track (dark track links), tank_tread (the grousers' worn
              faces), tank_rubber (tyres), tank_dark
              (grilles, bore, slots, vision blocks), tank_wood (the stowage box), tank_canvas (the tarp roll and
              straps), tank_pennant (near white: tint it with the player colour), tank_lamp_glow (the two headlamps
              and the turret's little searchlight), tank_tail_glow (red tail lamps). About 18.5k triangles:
              both sides are fully detailed, so a left-facing tank may also be turned by PI about Y.
shell.glb     mesh "shell": 0.50 long (x -0.25 .. 0.25), 0.16 across, origin at its centre, nose to +X. shell_body
              (olive steel), shell_tip (brass fuse), shell_band (copper driving band), shell_tracer_glow (the base).
missile.glb   mesh "missile": 0.78 long (x -0.39 .. 0.39), 0.24 across the fins, nose to +X, origin at its centre:
              missile_body (white), missile_nose (red), missile_fin (red), missile_band (dark), missile_glow (the
              nozzle). The MIRV and its warheads (scale it down for the children).
nuke.glb      mesh "nuke": a fat bomb 1.03 long (x -0.51 .. 0.52), 0.59 across, nose to +X, origin at its centre:
              nuke_body (charcoal), nuke_stripe_a / nuke_stripe_b (a yellow and black hazard band), nuke_metal (the
              box tail and its ring), nuke_glow (the glowing band round its waist).
roller.glb    mesh "roller": a spiked iron ball 0.60 across the spike tips (the ball 0.40), origin at its centre;
              roller_body, roller_spike, roller_glow (a glowing equator so its spin reads). Spin it about Z.
digger.glb    mesh "digger": 0.65 long (x -0.32 .. 0.33), nose (a fluted drill) to +X, origin at its centre;
              digger_body (yellow), digger_band (black), digger_drill (bright steel), digger_glow (an orange eye
              ring behind the drill). Spin it about X as it bores.
crate.glb     mesh "crate": a wooden supply crate 0.90 x 0.75 x 0.90 (0.94 over the brackets), origin at its bottom
              centre: crate_wood, crate_plank (darker boards), crate_metal (corner brackets), crate_mark (a white
              cross stencil on each side), crate_beacon_glow (a lamp on the lid). Child "chute" (origin at the lid's
              centre, y 0.75): the canopy 2.37 across, its rim 1.45 above the lid, its top 2.08 above the lid (2.83
              above the ground), eight gores (chute_a white, chute_b orange) and eight cords (chute_cord) to a ring
              on the lid. Scale the chute down (towards its origin) to collapse it on landing.
flag.glb      mesh "flag": origin at the base centre: a little stone plinth (flag_base), a 2.4 pole (flag_pole) with
              a gold finial (flag_finial). Child "cloth" (origin at the hoist top on the pole, y 2.25): a two-sided
              1.10 x 0.70 cloth towards +X, a 22 x 14 grid (cut along the star's edges) for waving; flag_cloth (near
              white: tint it with the winner's colour) with a five-pointed star emblem (flag_emblem, gold).
wreck_bits.glb root empty "wreck_bits" at the tank's origin; children bit_0 .. bit_5, each with its origin at its
              own centre and placed where it sat on the tank (near side, +Z), so the view can spawn the file at the
              wreck and fling each piece outwards: bit_0 a run of five track links (tank_track, tank_tread,
              tank_metal pins), bit_1 the cupola hatch, bit_2 a road wheel (tank_rubber, tank_metal), bit_3 a bent
              skirt panel with rivets, bit_4 a twisted fender plate, bit_5 a torn armour plate. Painted parts use
              tank_paint (recolour with the player colour, darkened), scorch marks wreck_char, torn edges
              wreck_ember_glow.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, torus, rod, tube, join, reset
from prism_models import export_anim, empty, new_obj
from mossfolk_models import lathe_r, solid
from hopline_models import ell
from marbledrift_models import mesh_from, dims

TAU = 2 * math.pi
FPS = 30


# ------------------------------------------------------------------ helpers

def paint_mats():
    return dict(
        paint=mat("tank_paint", (0.62, 0.08, 0.06), 0.38, 0.0, coat=0.55),
        metal=mat("tank_metal", (0.55, 0.56, 0.58), 0.32, 1.0),
        track=mat("tank_track", (0.16, 0.15, 0.15), 0.62, 0.75),
        tread=mat("tank_tread", (0.3, 0.3, 0.31), 0.42, 0.9),
        rubber=mat("tank_rubber", (0.05, 0.05, 0.055), 0.8),
        dark=mat("tank_dark", (0.03, 0.03, 0.035), 0.6, 0.3),
        wood=mat("tank_wood", (0.5, 0.31, 0.15), 0.7),
        canvas=mat("tank_canvas", (0.52, 0.47, 0.32), 0.85),
        pennant=mat("tank_pennant", (0.95, 0.93, 0.88), 0.7),
        lamp=mat("tank_lamp_glow", (1.0, 0.92, 0.7), 0.15, emit=6.0, emit_color=(1.0, 0.85, 0.55)),
        tail=mat("tank_tail_glow", (0.9, 0.08, 0.04), 0.2, emit=4.0, emit_color=(1.0, 0.1, 0.05)),
    )


def box(size, loc, material, rot=(0, 0, 0), bevel=None, segs=1):
    """K.box with a single chamfer by default (small parts: it keeps the triangle count down)."""
    return K.box(size, loc, material, rot=rot, bevel=bevel, segs=segs)


def set_mats(o, mats, fn):
    """Gives `o` the materials `mats` and picks one per face: fn(face centre, face normal) -> index."""
    o.data.materials.clear()
    for m in mats:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.material_index = fn(p.center, p.normal)
    return o


def lathe_axis(profile, material, axis, centre, segs=16, radial=None, smooth=40, name="lathe"):
    """lathe_r about an axis: 'x' (profile z runs along +X), '-y' (along -Y, towards the camera) or 'y'."""
    o = lathe_r(profile, material, segs=segs, radial=radial, name=name, smooth=smooth)
    rot = {"x": Matrix.Rotation(math.pi / 2, 4, "Y"), "-y": Matrix.Rotation(math.pi / 2, 4, "X"),
           "y": Matrix.Rotation(-math.pi / 2, 4, "X"), "z": Matrix.Identity(4)}[axis]
    o.data.transform(Matrix.Translation(Vector(centre)) @ rot)
    o.data.update()
    return o


def rivet(p, axis, material, r=0.022):
    """A low, domed rivet head at p (six facets round a raised centre, open underneath), its dome along axis."""
    d = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "-y": Vector((0, -1, 0)), "z": Vector((0, 0, 1))}[axis]
    bm = bmesh.new()
    ring = [bm.verts.new((r * math.cos(TAU * k / 6), r * math.sin(TAU * k / 6), 0.0)) for k in range(6)]
    mid = [bm.verts.new((0.6 * r * math.cos(TAU * (k + 0.5) / 6), 0.6 * r * math.sin(TAU * (k + 0.5) / 6), 0.3 * r))
           for k in range(6)]
    top = bm.verts.new((0, 0, 0.45 * r))
    for k in range(6):
        j = (k + 1) % 6
        bm.faces.new((ring[k], ring[j], mid[k]))
        bm.faces.new((mid[k], ring[j], mid[j]))
        bm.faces.new((mid[k], mid[j], top))
    o = new_obj("rivet", bm, material, smooth=80)
    o.data.transform(Matrix.Translation(Vector(p)) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
    o.data.update()
    return o


def convex_hull(pts):
    pts = sorted(set((round(x, 6), round(z, 6)) for x, z in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]          # counter-clockwise (x right, z up)


def resample_loop(poly, count):
    """count points evenly spaced round a closed polyline, with outward normals (for a CCW loop)."""
    P = [Vector((x, 0, z)) for x, z in poly]
    seg = [(P[i], P[(i + 1) % len(P)]) for i in range(len(P))]
    total = sum((b - a).length for a, b in seg)
    out = []
    step = total / count
    i, acc = 0, 0.0
    for k in range(count):
        d = k * step
        while acc + (seg[i][1] - seg[i][0]).length < d:
            acc += (seg[i][1] - seg[i][0]).length
            i += 1
        a, b = seg[i]
        u = (d - acc) / max(1e-9, (b - a).length)
        out.append(a.lerp(b, u))
    norms = []
    for k in range(count):
        t = (out[(k + 1) % count] - out[k - 1]).normalized()
        norms.append(Vector((t.z, 0, -t.x)))
    return out, norms, total


# ------------------------------------------------------------------ the tank

ROAD_X = (-0.9, -0.45, 0.0, 0.45, 0.9)
ROAD_Z, ROAD_R = 0.285, 0.20
SPR_X, SPR_Z, SPR_R = 1.30, 0.44, 0.22
TRACK_Y, TRACK_W, TRACK_T = 0.74, 0.44, 0.05
DECK = 0.94                              # the hull's top deck
GLACIS = (1.7, 0.78, 1.0, DECK)          # the glacis plate: from (x, z) at the nose up to (x, z) at the deck
TX, TZ = -0.15, DECK                     # turret ring centre
PIV = Vector((0.6, 0.0, 1.15))           # the gun's trunnion
ANT = (TX - 0.45, 0.32)                  # the antenna's foot (x, y)


def track(side, M):
    """One track loop round the wheels (side -1 near the camera, +1 far), grousers and worn tops."""
    circles = [(x, ROAD_Z, ROAD_R) for x in ROAD_X] + [(SPR_X, SPR_Z, SPR_R), (-SPR_X, SPR_Z, SPR_R)]
    pts = []
    for cx, cz, r in circles:
        for k in range(48):
            a = TAU * k / 48
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    hull = convex_hull(pts)
    _, _, total = resample_loop(hull, 400)
    links = int(round(total / 0.18))
    fr = (0.0, 0.12, 0.52, 0.64)         # stations within a link: plate, grouser rise, grouser top, fall
    th = (0.045, 0.085, 0.085, 0.045)
    P, N, _ = resample_loop(hull, links * 64)
    yc = side * TRACK_Y
    w = TRACK_W / 2
    prof = [(0.0, -w), (1.0, -w), (1.0, -w + 0.025), (1.0, w - 0.025), (1.0, w), (0.0, w)]   # (0 inner / 1 outer, y)
    verts, faces, fm = [], [], []
    st = []
    for k in range(links):
        for j in range(len(fr)):
            idx = int((k + fr[j]) * 64) % len(P)
            st.append((P[idx], N[idx], th[j], j))
    S = len(prof)
    for p, n, t, j in st:
        for i, (a, y) in enumerate(prof):
            off = t * a - (0.012 if a and i in (1, 4) else 0.0)
            q = p + n * off
            verts.append((q.x, yc + y, q.z))
    for k in range(len(st)):
        k2 = (k + 1) % len(st)
        top = st[k][3] in (1,)            # the grouser's top face
        for i in range(S):
            a, b = k * S + i, k * S + (i + 1) % S
            faces.append((a, b, k2 * S + (i + 1) % S, k2 * S + i))
            fm.append(1 if top and 0 < i < S - 2 else 0)
    return [mesh_from("track", verts, faces, [M["track"], M["tread"]], fm, smooth=30)]


def wheel_profile_road():
    """(r, z) tip-first: hub cap, dished disc, rim lip, tyre (outer face at +z)."""
    return [(0.0, 0.118), (0.035, 0.112), (0.05, 0.092), (0.11, 0.072), (0.145, 0.09), (0.17, 0.09), (0.195, 0.08),
            (0.2, 0.06), (0.2, -0.06), (0.0, -0.09)]


def road_wheel(x, z, side, M, segs):
    def pick(c, n):
        r = math.hypot(c.x - x, c.z - z)
        if r < 0.05:
            return 2
        if r > 0.158:
            return 1
        return 0
    o = lathe_axis(wheel_profile_road(), M["paint"], "-y" if side < 0 else "y", (x, side * TRACK_Y, z),
                   segs=segs, smooth=35, name="wheel")
    set_mats(o, [M["paint"], M["rubber"], M["metal"]], pick)
    parts = [o]
    for k in range(4):                    # lug nuts round the hub cap
        a = TAU * k / 4 + 0.4
        p = (x + 0.07 * math.cos(a), side * (TRACK_Y + 0.088), z + 0.07 * math.sin(a))
        parts.append(K.cyl(0.013, 0.016, p, M["metal"], rot=(math.pi / 2, 0, 0), verts=6))
    return parts


def sprocket(x, z, side, M, toothed, segs=36):
    """The drive sprocket (toothed ring) or the idler (a spoked disc), radius SPR_R to the track's inner face."""
    R = SPR_R

    def teeth(k, zz):
        if not toothed or zz > 0.06 or zz < -0.06:
            return 1.0
        return 1.0 if k % 3 else 0.86
    prof = [(0.0, 0.11), (0.04, 0.104), (0.06, 0.08), (0.12, 0.07), (R - 0.03, 0.078), (R, 0.05), (R, -0.05),
            (R - 0.03, -0.078), (0.0, -0.078)]
    o = lathe_axis(prof, M["paint"], "-y" if side < 0 else "y", (x, side * TRACK_Y, z), segs=segs, radial=teeth,
                   smooth=30, name="sprocket")

    def pick(c, n):
        r = math.hypot(c.x - x, c.z - z)
        if r < 0.065:
            return 1
        if r > R - 0.035:
            return 2
        return 0
    set_mats(o, [M["paint"], M["metal"], M["track"]], pick)
    parts = [o]
    for k in range(6):   # lightening holes (dark discs) or bolts round the hub
        a = TAU * k / 6
        p = (x + 0.115 * math.cos(a), side * (TRACK_Y + 0.072), z + 0.115 * math.sin(a))
        if toothed:
            parts.append(K.cyl(0.026, 0.006, p, M["dark"], rot=(math.pi / 2, 0, 0), verts=8))
        else:
            parts.append(K.cyl(0.013, 0.016, p, M["metal"], rot=(math.pi / 2, 0, 0), verts=6))
    return parts


def taper(o, z0, k):
    """Leans a part's sides in above z0: y shrinks by k per metre of height (a softer, toy-like body)."""
    for v in o.data.vertices:
        if v.co.z > z0:
            v.co.y *= 1 - k * (v.co.z - z0)
    o.data.update()
    return o


def on_glacis(x, y, lift=0.0):
    """A matrix placing a part on the glacis at (x, y): local Z along the plate's normal."""
    gx0, gz0, gx1, gz1 = GLACIS
    z = gz0 + (gz1 - gz0) * (x - gx0) / (gx1 - gx0)
    a = math.atan2(gz1 - gz0, gx0 - gx1)            # the plate's lean back from vertical
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((0, 0, lift))


def hull_parts(M):
    P = []
    paint, metal, dark = M["paint"], M["metal"], M["dark"]
    # lower hull between the tracks, with a sloped nose and a sloped tail
    P.append(K.prism([(-1.45, 0.3), (1.3, 0.3), (1.62, 0.72), (-1.6, 0.72)], 1.0, (0, 0, 0), paint, bevel=0.03))
    # the upper hull over the full width: fenders over the tracks, a long glacis, a rounded rear, sides leaning in
    gx0, gz0, gx1, gz1 = GLACIS
    up = [(-1.6, 0.7), (1.56, 0.7), (gx0, 0.74), (gx0, gz0), (gx1, gz1), (-1.32, DECK), (-1.62, 0.86)]
    P.append(taper(K.prism(up, 1.96, (0, 0, 0), paint, bevel=0.045, segs=3), 0.74, 0.35))
    # a steel strip along the fender's lower edge, and a lip at the glacis' top edge
    for s in (-1, 1):
        P.append(box((2.9, 0.04, 0.035), (0.0, s * 0.985, 0.715), metal, bevel=0.012))
    # the driver's hatch on the glacis, a vision block in front of it and a handle
    hm = on_glacis(1.22, -0.36, 0.0)
    hatch = K.cyl(0.17, 0.05, (0, 0, 0), paint, verts=24, bevel=0.012, segs=2)
    hatch.data.transform(hm)
    P.append(hatch)
    for part in (tube([(-0.06, 0, 0.026), (-0.06, 0, 0.055), (0.06, 0, 0.055), (0.06, 0, 0.026)], [0.011] * 4, metal,
                      verts=6),
                 rod((-0.17, -0.07, 0.02), (-0.17, 0.07, 0.02), 0.016, metal, verts=8)):
        part.data.transform(hm)
        P.append(part)
    vb = box((0.07, 0.24, 0.07), (0, 0, 0), dark, bevel=0.012)
    vb.data.transform(on_glacis(1.43, -0.36, 0.02))
    P.append(vb)
    vh = box((0.1, 0.3, 0.05), (0, 0, 0), paint, bevel=0.015)
    vh.data.transform(on_glacis(1.4, -0.36, 0.035))
    P.append(vh)
    # a bolted inspection plate on the far side of the glacis
    pl = box((0.3, 0.42, 0.025), (0, 0, 0), paint, bevel=0.01)
    pl.data.transform(on_glacis(1.2, 0.36, 0.0))
    P.append(pl)
    for dx in (-0.12, 0.12):
        for dy in (-0.18, 0.18):
            r = rivet((0, 0, 0), "z", metal, 0.018)
            r.data.transform(on_glacis(1.2 + dx, 0.36 + dy, 0.014))
            P.append(r)
    # spare track links clipped across the lower nose
    for k in range(3):
        y = -0.42 + 0.21 * k
        lk = box((0.06, 0.19, 0.17), (0, 0, 0), M["track"], bevel=0.012)
        lk.data.transform(Matrix.Translation((1.48, y, 0.52)) @ Matrix.Rotation(-0.92, 4, "Y"))
        P.append(lk)
        P.append(rod((1.505, y - 0.1, 0.53), (1.505, y + 0.1, 0.53), 0.012, metal, verts=6))
    # tow hooks at the nose and the tail
    for s in (-1, 1):
        P.append(torus(0.05, 0.016, (1.66, s * 0.36, 0.48), metal, rot=(0, math.pi / 2 - 0.9, 0), verts=10, minor=4))
        P.append(torus(0.05, 0.016, (-1.55, s * 0.36, 0.5), metal, rot=(0, math.pi / 2 + 0.6, 0), verts=10, minor=4))
    # headlamps on the front fenders: a bracket, a steel bucket, a glowing lens, a little wire guard
    for s in (-1, 1):
        y = s * 0.74
        zc = 0.9
        P.append(box((0.08, 0.06, 0.1), (1.5, y, 0.81), metal, bevel=0.01))
        P.append(lathe_axis([(0.0, 0.0), (0.075, 0.0), (0.085, 0.03), (0.085, 0.08), (0.0, 0.08)], metal, "x",
                            (1.45, y, zc), segs=16, smooth=40, name="lamp"))
        P.append(K.cyl(0.072, 0.012, (1.532, y, zc), M["lamp"], rot=(0, math.pi / 2, 0), verts=16))
        P.append(torus(0.08, 0.01, (1.535, y, zc), metal, rot=(0, math.pi / 2, 0), verts=16, minor=3))
        for dz in (-0.035, 0.035):
            P.append(rod((1.545, y - 0.07, zc + dz), (1.545, y + 0.07, zc + dz), 0.006, metal, verts=4))
    # tail lamps
    for s in (-1, 1):
        P.append(box((0.04, 0.12, 0.07), (-1.6, s * 0.78, 0.82), M["tail"], bevel=0.012))
        P.append(box((0.03, 0.15, 0.1), (-1.585, s * 0.78, 0.82), metal, bevel=0.01))
    # engine deck: a raised grille with slats behind the turret, two lifting eyes
    P.append(box((0.5, 0.96, 0.05), (-1.08, 0.0, DECK + 0.02), metal, bevel=0.015))
    for k in range(5):
        P.append(box((0.05, 0.86, 0.03), (-1.28 + k * 0.1, 0.0, DECK + 0.05), dark, bevel=0.008))
    for s in (-1, 1):
        P.append(torus(0.04, 0.012, (0.75, s * 0.62, DECK + 0.02), metal, rot=(math.pi / 2, 0, 0), verts=10,
                       minor=4))
    # exhausts: two stubby pipes out of the rear plate
    for s in (-1, 1):
        P.append(rod((-1.55, s * 0.45, 0.8), (-1.75, s * 0.45, 0.8), 0.055, metal, verts=12))
        P.append(K.cyl(0.04, 0.012, (-1.755, s * 0.45, 0.8), dark, rot=(0, math.pi / 2, 0), verts=12))
        P.append(torus(0.058, 0.01, (-1.7, s * 0.45, 0.8), metal, rot=(0, math.pi / 2, 0), verts=12, minor=3))
    # the wooden stowage box on the near rear fender, steel straps and a latch
    bx_y = -0.7
    P.append(box((0.5, 0.36, 0.26), (-1.1, bx_y, DECK + 0.13), M["wood"], bevel=0.02))
    for x in (-1.28, -0.92):
        P.append(box((0.04, 0.38, 0.28), (x, bx_y, DECK + 0.13), metal, bevel=0.008))
    for k in range(2):   # board seams
        P.append(box((0.32, 0.006, 0.01), (-1.1, bx_y - 0.181, DECK + 0.08 + 0.1 * k), M["dark"], bevel=0.0))
    P.append(box((0.06, 0.02, 0.05), (-1.1, bx_y - 0.19, DECK + 0.21), metal, bevel=0.006))
    # a jerrycan in a rack on the far rear fender
    P.append(box((0.22, 0.3, 0.32), (-1.2, 0.7, DECK + 0.16), M["canvas"], bevel=0.03))
    P.append(box((0.24, 0.035, 0.34), (-1.2, 0.7, DECK + 0.16), metal, bevel=0.01))
    P.append(tube([(-1.24, 0.7, DECK + 0.32), (-1.24, 0.7, DECK + 0.36), (-1.16, 0.7, DECK + 0.36),
                   (-1.16, 0.7, DECK + 0.32)], [0.012] * 4, metal, verts=5))
    # a shovel and a tow cable on the near side, above the skirts
    y = -0.97
    P.append(rod((0.15, y, 0.835), (0.95, y, 0.835), 0.018, M["wood"], verts=8))
    P.append(K.prism([(0.95, 0.79), (1.17, 0.8), (1.2, 0.835), (1.17, 0.87), (0.95, 0.88)], 0.012, (0, y, 0), metal,
                     bevel=0.003))
    for x in (0.35, 0.8):
        P.append(box((0.04, 0.03, 0.07), (x, y + 0.005, 0.835), metal, bevel=0.006))
    cable = []
    for k in range(17):
        u = k / 16
        cable.append((-1.1 + 1.0 * u, y, 0.8 + 0.03 * math.sin(math.pi * u) - 0.015 * math.sin(3 * math.pi * u)))
    P.append(tube(cable, [0.016] * len(cable), M["dark"], verts=5, name="cable"))
    for e in (cable[0], cable[-1]):
        P.append(torus(0.035, 0.01, e, metal, rot=(math.pi / 2, 0, 0), verts=10, minor=4))
    # skirts: three riveted panels a side, the end corners swept up
    for s in (-1, 1):
        y = s * 1.0
        panels = ((-1.2, -0.42), (-0.39, 0.39), (0.42, 1.2))
        for i, (x0, x1) in enumerate(panels):
            poly = [(x0, 0.42), (x1, 0.42), (x1, 0.735), (x0, 0.735)]
            if i == 2:
                poly = [(x0, 0.42), (x1 - 0.12, 0.42), (x1, 0.56), (x1, 0.735), (x0, 0.735)]
            if i == 0:
                poly = [(x0 + 0.1, 0.42), (x1, 0.42), (x1, 0.735), (x0, 0.735), (x0, 0.53)]
            P.append(K.prism(poly, 0.035, (0, y, 0), paint, bevel=0.012))
            for zr in (0.46, 0.69):
                for k in range(4):
                    x = x0 + 0.08 + (x1 - x0 - 0.16) * k / 3
                    P.append(rivet((x, y + s * 0.02, zr), "-y" if s < 0 else "y", metal))
        P.append(box((0.22, 0.03, 0.08), (0.0, y + s * 0.025, 0.58), metal, bevel=0.008))
    # a rivet row along the glacis' top edge
    for k in range(7):
        r = rivet((0, 0, 0), "z", metal, 0.018)
        r.data.transform(on_glacis(gx1 + 0.06, -0.72 + 0.24 * k, 0.012))
        P.append(r)
    return P


def turret_parts(M):
    paint, metal, dark = M["paint"], M["metal"], M["dark"]
    P = []
    top = 1.36
    prof = [(0.0, top), (0.34, top), (0.47, top - 0.02), (0.565, top - 0.07), (0.62, top - 0.15), (0.64, top - 0.25),
            (0.63, top - 0.35), (0.6, TZ), (0.0, TZ)]

    def plan(x, y):
        """The egg-shaped plan: longer to the front, narrower at the back."""
        x2 = x * (1.14 if x > 0 else 1.06)
        y2 = y * (0.9 - (0.06 * min(1.0, -x / 0.5) if x < 0 else 0))
        return x2, y2
    t = lathe_r(prof, paint, segs=32, smooth=35, name="turret_body")
    for v in t.data.vertices:
        v.co.x, v.co.y = plan(v.co.x, v.co.y)
        v.co.x += TX
    t.data.update()
    P.append(t)
    # the turret ring collar and a row of rivets round the skirt of the turret
    ring = lathe_r([(0.0, TZ + 0.035), (0.6, TZ + 0.035), (0.645, TZ + 0.015), (0.645, TZ), (0.0, TZ)], metal, segs=32,
                   smooth=35, name="ring")
    for v in ring.data.vertices:
        v.co.x, v.co.y = plan(v.co.x, v.co.y)
        v.co.x += TX
    ring.data.update()
    P.append(ring)
    for k in range(20):
        a = TAU * k / 20
        if math.cos(a) > 0.8:
            continue   # not behind the mantlet
        x, y = plan(0.645 * math.cos(a), 0.645 * math.sin(a))
        P.append(rivet((TX + x, y, TZ + 0.11), "x" if abs(x) > abs(y) else "y", metal, 0.02))
    # the commander's cupola: a raised ring with vision blocks and a domed hatch with a handle and a hinge
    cx, cy = TX - 0.14, 0.2
    P.append(lathe_r([(0.0, top + 0.05), (0.12, top + 0.05), (0.17, top + 0.04), (0.19, top + 0.02), (0.2, top - 0.02),
                      (0.0, top - 0.02)], paint, segs=24, smooth=35, name="cupola", center=(cx, cy, 0)))
    for k in range(6):
        a = TAU * k / 6 + 0.25
        P.append(box((0.04, 0.08, 0.03), (cx + 0.2 * math.cos(a), cy + 0.2 * math.sin(a), top + 0.01), dark,
                     bevel=0.006, rot=(0, 0, a)))
    P.append(tube([(cx - 0.06, cy, top + 0.045), (cx - 0.06, cy, top + 0.07), (cx + 0.06, cy, top + 0.07),
                   (cx + 0.06, cy, top + 0.045)], [0.01] * 4, metal, verts=6))
    P.append(rod((cx - 0.16, cy - 0.08, top + 0.04), (cx - 0.16, cy + 0.08, top + 0.04), 0.018, metal, verts=8))
    # the loader's periscope and a little searchlight on the near cheek
    P.append(box((0.12, 0.1, 0.07), (TX + 0.2, -0.24, top + 0.01), dark, bevel=0.012))
    P.append(box((0.15, 0.13, 0.03), (TX + 0.2, -0.24, top - 0.01), paint, bevel=0.01))
    sx, sy, sz = TX + 0.35, -0.5, 1.28
    P.append(rod((sx - 0.02, sy + 0.06, sz - 0.1), (sx, sy, sz - 0.03), 0.02, metal, verts=6))
    P.append(lathe_axis([(0.0, 0.0), (0.05, 0.0), (0.058, 0.03), (0.058, 0.07), (0.0, 0.07)], metal, "x",
                        (sx - 0.02, sy, sz), segs=14, smooth=40, name="spot"))
    P.append(K.cyl(0.05, 0.012, (sx + 0.052, sy, sz), M["lamp"], rot=(0, math.pi / 2, 0), verts=14))
    # side grab bars
    for s in (-1, 1):
        y = s * 0.56
        P.append(tube([(TX - 0.32, y * 0.97, 1.16), (TX - 0.32, y * 1.07, 1.17), (TX + 0.18, y * 1.07, 1.17),
                       (TX + 0.18, y * 0.99, 1.16)], [0.013] * 4, metal, verts=6))
    # the tarp roll strapped across the turret's back, on a bustle rack
    bx = TX - 0.7
    P.append(box((0.14, 0.86, 0.04), (bx + 0.04, 0, 1.06), metal, bevel=0.012))
    roll = rod((bx, -0.44, 1.17), (bx, 0.44, 1.17), 0.11, M["canvas"], verts=14)
    for v in roll.data.vertices:          # a soft, slightly saggy roll
        v.co.z += 0.015 * math.cos(math.pi * v.co.y / 0.44)
    roll.data.update()
    P.append(roll)
    for e in (-0.44, 0.44):
        P.append(K.cyl(0.11, 0.01, (bx, e, 1.17), M["canvas"], rot=(math.pi / 2, 0, 0), verts=14))
    for y in (-0.25, 0.25):
        P.append(torus(0.118, 0.014, (bx, y, 1.18), M["dark"], rot=(math.pi / 2, 0, 0), verts=14, minor=3))
    # the antenna: a base on the far rear of the turret, a thin whip, a ball at the tip
    ax, ay = ANT
    P.append(K.cyl(0.04, 0.08, (ax, ay, top - 0.02), metal, verts=10))
    P.append(sphere(0.03, (ax, ay, top + 0.03), metal, segs=10, rings=6))
    P.append(rod((ax, ay, top + 0.03), (ax, ay, 2.38), 0.012, M["dark"], r2=0.006, verts=6))
    P.append(sphere(0.02, (ax, ay, 2.39), metal, segs=8, rings=6))
    return P


def barrel_parts(M):
    """The gun along +X from the trunnion PIV; the mantlet pill and its cast collar go with it."""
    paint, metal, dark = M["paint"], M["metal"], M["dark"]
    prof = [(0.0, 1.5), (0.032, 1.5), (0.032, 1.62), (0.082, 1.62), (0.094, 1.605), (0.094, 1.445), (0.082, 1.43),
            (0.06, 1.425), (0.058, 1.06), (0.066, 1.05), (0.082, 1.01), (0.086, 0.93), (0.082, 0.85), (0.066, 0.81),
            (0.06, 0.8), (0.062, 0.57), (0.08, 0.56), (0.08, 0.53), (0.076, 0.52), (0.076, 0.26),
            (0.115, 0.22), (0.115, 0.1), (0.0, 0.1)]

    def pick(c, n):
        r = math.hypot(c.y, c.z - PIV.z)
        x = c.x - PIV.x
        if r < 0.036 and x > 1.45:
            return 2
        if x > 1.42 or 0.515 < x < 0.57:
            return 1
        return 0
    g = lathe_axis(prof, paint, "x", PIV, segs=18, smooth=40, name="gun")
    set_mats(g, [paint, metal, dark], pick)
    P = [g]
    for s in (-1, 1):                     # muzzle brake slots
        for dx in (1.475, 1.56):
            P.append(box((0.05, 0.02, 0.065), (PIV.x + dx, s * 0.089, PIV.z), dark, bevel=0.006))
    # the mantlet: a flattened pill across the turret face (it turns with the gun, so it reads the same at any angle)
    m = tube([(PIV.x, -0.24, PIV.z), (PIV.x, 0.24, PIV.z)], [0.14, 0.14], paint, verts=18, name="mantlet")
    for v in m.data.vertices:
        v.co.x = PIV.x + (v.co.x - PIV.x) * 0.75
    m.data.update()
    P.append(m)
    for s in (-1, 1):
        for dz in (-0.1, 0.1):
            P.append(rivet((PIV.x + 0.07, s * 0.17, PIV.z + dz), "x", metal, 0.018))
    # a coaxial gun port and a sight with a little lens on top of the pill
    P.append(rod((PIV.x + 0.08, 0.15, PIV.z - 0.05), (PIV.x + 0.22, 0.15, PIV.z - 0.05), 0.018, metal, verts=8))
    P.append(box((0.12, 0.07, 0.06), (PIV.x + 0.0, -0.13, PIV.z + 0.16), dark, bevel=0.012))
    P.append(box((0.02, 0.05, 0.04), (PIV.x + 0.065, -0.13, PIV.z + 0.16), M["lamp"], bevel=0.006))
    # the breech block behind the trunnion (inside the turret at most angles)
    P.append(box((0.3, 0.18, 0.18), (PIV.x - 0.2, 0, PIV.z), metal, bevel=0.02))
    return P


def pennant_mesh(M, root):
    """A two-sided triangular pennant from the hoist point `root` streaming towards -X, 12 x 4 cells."""
    L, H = 0.46, 0.24
    nx, nz = 12, 4
    verts, faces = [], []
    for i in range(nx + 1):
        u = i / nx
        for j in range(nz + 1):
            v = j / nz
            h = H * (1 - 0.92 * u)
            x = -0.02 - L * u
            z = -(1 - v) * h - 0.0                 # hangs below the hoist point
            z -= 0.04 * u * u                      # droops a little
            y = 0.02 * math.sin(math.pi * 2 * u) * u
            verts.append((root.x + x, root.y + y, root.z + z))
    for i in range(nx):
        for j in range(nz):
            a = i * (nz + 1) + j
            faces.append((a, a + nz + 1, a + nz + 2, a + 1))
    p = mesh_from("pennant", verts, faces, [M["pennant"]], smooth=60)
    bm = bmesh.new()
    bm.from_mesh(p.data)
    back = bmesh.ops.duplicate(bm, geom=list(bm.faces))["geom"]
    bmesh.ops.reverse_faces(bm, faces=[g for g in back if isinstance(g, bmesh.types.BMFace)])
    for g in back:
        if isinstance(g, bmesh.types.BMVert):
            g.co.y += 0.003
    bm.to_mesh(p.data)
    bm.free()
    # a stripe in the player colour along the hoist edge
    p.data.materials.append(M["paint"])
    for f in p.data.polygons:
        if f.center.x > root.x - 0.08:
            f.material_index = 1
    return p


def tank():
    M = paint_mats()
    hull = hull_parts(M)
    for s in (-1, 1):
        hull += track(s, M)
    hull = join(hull, "hull")
    wheels = []
    for i, x in enumerate(ROAD_X):
        parts = []
        for s in (-1, 1):
            parts += road_wheel(x, ROAD_Z, s, M, 13)
        wheels.append(join(parts, "wheel_%d" % i, pivot=(x, 0, ROAD_Z)))
    for name, x, toothed in (("wheel_front", SPR_X, True), ("wheel_rear", -SPR_X, False)):
        parts = []
        for s in (-1, 1):
            parts += sprocket(x, SPR_Z, s, M, toothed, 27)
        wheels.append(join(parts, name, pivot=(x, 0, SPR_Z)))
    tur = join(turret_parts(M), "turret", pivot=(TX, 0, TZ))
    bar = join(barrel_parts(M), "barrel", pivot=tuple(PIV))
    muzzle = empty("muzzle")
    muzzle.location = (PIV.x + 1.62, 0, PIV.z)
    tip = Vector((ANT[0], ANT[1], 2.3))
    pen = join([pennant_mesh(M, tip)], "pennant", pivot=tuple(tip))
    root = empty("tank")
    for o in [hull, tur, bar, pen] + wheels:
        dims(o)
    print("  tank total %d tris" % sum(K.tris(o) for o in [hull, tur, bar, pen] + wheels))
    export_anim(root, "tank", [(hull, root), (tur, root), (bar, tur), (muzzle, bar), (pen, tur)]
                + [(w, hull) for w in wheels], anim=False)


# ------------------------------------------------------------------ projectiles

def shell():
    body = mat("shell_body", (0.36, 0.4, 0.22), 0.4, 0.5, coat=0.3)
    tip = mat("shell_tip", (0.9, 0.66, 0.25), 0.25, 1.0)
    band = mat("shell_band", (0.85, 0.42, 0.22), 0.3, 1.0)
    tracer = mat("shell_tracer_glow", (1.0, 0.6, 0.2), 0.3, emit=8.0, emit_color=(1.0, 0.5, 0.15))
    prof = [(0.0, 0.25), (0.012, 0.247), (0.024, 0.236), (0.034, 0.222), (0.05, 0.19), (0.062, 0.155),
            (0.071, 0.11), (0.075, 0.06), (0.075, -0.12), (0.08, -0.13), (0.08, -0.165), (0.075, -0.175),
            (0.075, -0.22), (0.07, -0.235), (0.058, -0.25), (0.035, -0.252), (0.0, -0.252)]

    def pick(c, n):
        if c.x > 0.2:
            return 1
        if -0.17 < c.x < -0.125:
            return 2
        if c.x < -0.249 and math.hypot(c.y, c.z) < 0.04:
            return 3
        if 0.15 < c.x <= 0.2:
            return 1 if c.x > 0.205 else 0
        return 0
    o = lathe_axis(prof, body, "x", (0, 0, 0), segs=24, smooth=40, name="shell")
    set_mats(o, [body, tip, band, tracer], pick)
    o = join([o, torus(0.0725, 0.004, (0.02, 0, 0), tip, rot=(0, math.pi / 2, 0), verts=24, minor=4)], "shell")
    dims(o)
    K.export(o, "shell")


def fins(n, x0, x1, r0, span, chord_tip, thick, material, sweep=0.05, phase=math.pi / 4):
    """n swept fins on a body of radius r0 along X: root chord x0..x1, span outwards."""
    out = []
    for k in range(n):
        a = phase + TAU * k / n
        f = K.prism([(x0, 0.0), (x1, 0.0), (x1 - sweep - chord_tip * 0.3, span), (x1 - sweep - chord_tip, span)],
                    thick, (0, 0, 0), material, bevel=0.004, segs=1)
        f.data.transform(Matrix.Rotation(a, 4, "X") @ Matrix.Translation((0, 0, r0 - 0.005)))
        out.append(f)
    return out


def missile():
    body = mat("missile_body", (0.9, 0.9, 0.88), 0.35, coat=0.6)
    nose = mat("missile_nose", (0.8, 0.12, 0.08), 0.35, coat=0.6)
    fin = mat("missile_fin", (0.8, 0.12, 0.08), 0.4, coat=0.4)
    band = mat("missile_band", (0.1, 0.1, 0.12), 0.5, 0.4)
    glow = mat("missile_glow", (1.0, 0.65, 0.25), 0.3, emit=7.0, emit_color=(1.0, 0.5, 0.15))
    prof = [(0.0, 0.39), (0.02, 0.38), (0.04, 0.35), (0.056, 0.3), (0.066, 0.24), (0.07, 0.18), (0.07, -0.3),
            (0.066, -0.32), (0.05, -0.34), (0.05, -0.37), (0.0, -0.37)]

    def pick(c, n):
        if c.x > 0.175:
            return 1
        if 0.12 < c.x < 0.15 or -0.16 < c.x < -0.13:
            return 2
        if c.x < -0.31:
            return 2
        return 0
    o = lathe_axis(prof, body, "x", (0, 0, 0), segs=24, smooth=40, name="missile")
    set_mats(o, [body, nose, band], pick)
    parts = [o, K.cyl(0.04, 0.03, (-0.375, 0, 0), glow, rot=(0, math.pi / 2, 0), r2=0.046, verts=16)]
    parts += fins(4, -0.33, -0.16, 0.07, 0.1, 0.08, 0.012, fin, sweep=0.04)
    parts += fins(4, 0.06, 0.12, 0.07, 0.035, 0.04, 0.008, fin, sweep=0.01)
    # three little warhead seams round the nose cone
    for k in range(3):
        a = TAU * k / 3
        parts.append(rod((0.19, 0.071 * math.cos(a), 0.071 * math.sin(a)),
                         (0.33, 0.054 * math.cos(a), 0.054 * math.sin(a)), 0.005, band, verts=4))
    o = join(parts, "missile")
    dims(o)
    K.export(o, "missile")


def nuke():
    body = mat("nuke_body", (0.15, 0.16, 0.17), 0.35, 0.4, coat=0.5)
    sa = mat("nuke_stripe_a", (0.95, 0.75, 0.08), 0.4, coat=0.4)
    sb = mat("nuke_stripe_b", (0.04, 0.04, 0.04), 0.45, coat=0.4)
    metal = mat("nuke_metal", (0.5, 0.52, 0.55), 0.3, 1.0)
    glow = mat("nuke_glow", (0.55, 1.0, 0.25), 0.3, emit=6.0, emit_color=(0.45, 1.0, 0.15))
    prof = [(0.0, 0.5), (0.06, 0.49), (0.13, 0.46), (0.19, 0.41), (0.235, 0.33), (0.26, 0.22), (0.268, 0.1),
            (0.268, 0.03), (0.272, 0.025), (0.272, -0.025), (0.268, -0.03), (0.265, -0.1), (0.25, -0.18),
            (0.22, -0.25), (0.17, -0.3), (0.11, -0.34), (0.07, -0.37), (0.06, -0.44), (0.0, -0.44)]
    segs = 32

    o = lathe_axis(prof, body, "x", (0, 0, 0), segs=segs, smooth=40, name="nuke")
    parts = [o, torus(0.272, 0.022, (0, 0, 0), glow, rot=(0, math.pi / 2, 0), verts=40, minor=6)]
    # the hazard band: a sleeve just proud of the body, its grid twisted so the stripes run cleanly on the diagonal
    X0, X1, NS, NR = 0.11, 0.25, 24, 4

    def body_r(x):
        pts = sorted((z, r) for r, z in prof)
        for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
            if z0 <= x <= z1:
                return r0 + (r1 - r0) * (x - z0) / (z1 - z0)
        return 0.0
    verts, faces, fm = [], [], []
    cols = NS * 2
    for i in range(NR + 1):
        x = X0 + (X1 - X0) * i / NR
        r = body_r(x) + 0.004
        tw = (x - X0) / (X1 - X0) * TAU / NS * 2.2
        for k in range(cols):
            a = TAU * k / cols + tw
            verts.append((x, r * math.cos(a), r * math.sin(a)))
    for i in range(NR):
        for k in range(cols):
            a, b = i * cols + k, i * cols + (k + 1) % cols
            faces.append((a, b, b + cols, a + cols))
            fm.append((k // 2) % 2)
    parts.append(mesh_from("hazard", verts, faces, [sa, sb], fm, smooth=50))
    for x in (X0, X1):
        parts.append(torus(body_r(x) + 0.005, 0.007, (x, 0, 0), metal, rot=(0, math.pi / 2, 0), verts=40, minor=4))
    for x in (-0.06, 0.06):
        parts.append(torus(0.268, 0.008, (x, 0, 0), metal, rot=(0, math.pi / 2, 0), verts=40, minor=4))
    # the box tail: four plates in a square ring held by four fins
    for k in range(4):
        a = TAU * k / 4
        f = K.prism([(-0.5, 0.0), (-0.3, 0.0), (-0.38, 0.17), (-0.5, 0.17)], 0.014, (0, 0, 0), metal, bevel=0.004,
                    segs=1)
        f.data.transform(Matrix.Rotation(a, 4, "X") @ Matrix.Translation((0, 0, 0.05)))
        parts.append(f)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        pl = box((0.13, 0.25, 0.012), (0, 0, 0), metal, bevel=0.004, segs=1)
        pl.data.transform(Matrix.Rotation(a, 4, "X") @ Matrix.Translation((-0.445, 0, 0.165)))
        parts.append(pl)
    parts.append(sphere(0.03, (0.49, 0, 0), metal, segs=10, rings=6))   # the nose fuse
    parts.append(torus(0.06, 0.012, (0.0, 0, 0.275), metal, rot=(math.pi / 2, 0, 0), verts=12, minor=4))   # lug
    o = join(parts, "nuke")
    dims(o)
    K.export(o, "nuke")


def fib_dirs(n):
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        yield Vector((r * math.cos(i * ga), r * math.sin(i * ga), z))


def roller():
    body = mat("roller_body", (0.2, 0.19, 0.2), 0.45, 0.8)
    spike = mat("roller_spike", (0.75, 0.75, 0.78), 0.25, 1.0)
    glow = mat("roller_glow", (1.0, 0.55, 0.15), 0.3, emit=5.0, emit_color=(1.0, 0.45, 0.08))
    parts = [sphere(0.2, (0, 0, 0), body, segs=24, rings=14)]
    # a raised glowing equator in the XY plane (Godot: facing the camera, so the spin about Z reads)
    parts.append(torus(0.2, 0.018, (0, 0, 0), glow, rot=(math.pi / 2, 0, 0), verts=36, minor=5))
    parts.append(torus(0.2, 0.03, (0, 0, 0), body, rot=(0, 0, 0), verts=36, minor=5))
    for d in fib_dirs(22):
        base = d * 0.17
        tipp = d * 0.31
        parts.append(rod(base, tipp, 0.045, spike, r2=0.004, verts=7))
        c = torus(0.048, 0.01, (0, 0, 0), body, verts=8, minor=3)
        c.data.transform(Matrix.Translation(d * 0.2) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
        parts.append(c)
    o = join(parts, "roller")
    dims(o)
    K.export(o, "roller")


def digger():
    body = mat("digger_body", (0.95, 0.68, 0.08), 0.35, coat=0.6)
    band = mat("digger_band", (0.06, 0.06, 0.07), 0.45, 0.3)
    drill = mat("digger_drill", (0.82, 0.84, 0.88), 0.18, 1.0)
    glow = mat("digger_glow", (1.0, 0.5, 0.1), 0.3, emit=6.0)
    prof = [(0.07, 0.12), (0.076, 0.11), (0.078, 0.09), (0.078, 0.0), (0.08, -0.005), (0.08, -0.035),
            (0.078, -0.04), (0.078, -0.165), (0.08, -0.17), (0.08, -0.2), (0.078, -0.205), (0.078, -0.24),
            (0.07, -0.26), (0.055, -0.27), (0.055, -0.32), (0.0, -0.32)]

    def pick(c, n):
        if -0.04 < c.x < 0.0 or -0.205 < c.x < -0.165:
            return 1
        if c.x < -0.262:
            return 1
        return 0
    o = lathe_axis(prof, body, "x", (0, 0, 0), segs=24, smooth=40, name="digger")
    # chevron stripes: mark faces between two bands
    set_mats(o, [body, band], pick)
    parts = [o, torus(0.073, 0.012, (0.115, 0, 0), glow, rot=(0, math.pi / 2, 0), verts=24, minor=5)]
    # the drill: a cone with three spiral flutes winding to the tip
    parts.append(lathe_axis([(0.0, 0.33), (0.012, 0.315), (0.04, 0.24), (0.062, 0.16), (0.068, 0.12), (0.0, 0.12)],
                            drill, "x", (0, 0, 0), segs=24, smooth=40, name="cone"))
    for k in range(3):
        pts, rad = [], []
        for i in range(25):
            u = i / 24
            x = 0.125 + u * 0.2
            r = 0.068 * (1 - u) + 0.008 * u
            a = TAU * k / 3 + u * TAU * 1.3
            pts.append((x, (r + 0.004) * math.cos(a), (r + 0.004) * math.sin(a)))
            rad.append(0.014 * (1 - 0.7 * u))
        parts.append(tube(pts, rad, drill, verts=5, name="flute"))
    parts += fins(4, -0.32, -0.2, 0.06, 0.07, 0.06, 0.012, band, sweep=0.02, phase=0.0)
    o = join(parts, "digger")
    dims(o)
    K.export(o, "digger")


# ------------------------------------------------------------------ the crate, the flag

def crate():
    wood = mat("crate_wood", (0.62, 0.42, 0.22), 0.7)
    plank = mat("crate_plank", (0.42, 0.27, 0.13), 0.75)
    metal = mat("crate_metal", (0.45, 0.47, 0.5), 0.35, 1.0)
    mark = mat("crate_mark", (0.95, 0.93, 0.86), 0.6)
    beacon = mat("crate_beacon_glow", (1.0, 0.75, 0.2), 0.3, emit=7.0, emit_color=(1.0, 0.6, 0.1))
    ca = mat("chute_a", (0.95, 0.94, 0.9), 0.75)
    cb = mat("chute_b", (0.95, 0.42, 0.1), 0.75)
    cord = mat("chute_cord", (0.85, 0.82, 0.74), 0.8)
    W, H = 0.9, 0.75
    parts = [box((W - 0.06, W - 0.06, H - 0.04), (0, 0, H / 2), wood, bevel=0.01)]
    # edge boards round every face, and diagonal braces on the four sides
    b = 0.09
    for s in (-1, 1):
        for zz in (b / 2 + 0.005, H - b / 2 - 0.005):
            parts.append(box((W, b * 0.4, b), (0, s * (W / 2 - b * 0.2), zz), plank, bevel=0.012))
            parts.append(box((b * 0.4, W, b), (s * (W / 2 - b * 0.2), 0, zz), plank, bevel=0.012))
        for t in (-1, 1):
            parts.append(box((b * 0.4, b, H), (s * (W / 2 - b * 0.2), t * (W / 2 - b / 2), H / 2), plank,
                             bevel=0.012))
    # the white cross stencil on each side
    for k in range(4):
        a = k * math.pi / 2
        n = Vector((math.cos(a), math.sin(a), 0))
        for sz in ((0.36, 0.1), (0.1, 0.36)):
            m = box((0.004, sz[0], sz[1]), (0, 0, 0), mark, bevel=0.0)
            m.data.transform(Matrix.Translation(n * (W / 2 - 0.026) + Vector((0, 0, H / 2)))
                             @ Matrix.Rotation(a, 4, "Z"))
            parts.append(m)
    # corner brackets
    for sx in (-1, 1):
        for sy in (-1, 1):
            for zz in (0.03, H - 0.03):
                parts.append(box((0.14, 0.14, 0.06), (sx * (W / 2 - 0.05), sy * (W / 2 - 0.05), zz), metal,
                                 bevel=0.012))
                parts.append(rivet((sx * (W / 2 + 0.002), sy * (W / 2 - 0.05), zz), "x", metal, 0.014))
    # lid: two boards, a harness ring and the beacon lamp in a cage
    for k in (-1, 1):
        parts.append(box((W - 0.12, 0.36, 0.03), (0, k * 0.2, H + 0.005), plank, bevel=0.008))
    parts.append(torus(0.1, 0.014, (0, 0, H + 0.03), metal, verts=16, minor=5))
    parts.append(K.cyl(0.05, 0.03, (0.28, -0.28, H + 0.035), metal, verts=12))
    parts.append(sphere(0.045, (0.28, -0.28, H + 0.075), beacon, segs=12, rings=8))
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        parts.append(rod((0.28 + 0.05 * math.cos(a), -0.28 + 0.05 * math.sin(a), H + 0.04),
                         (0.28 + 0.03 * math.cos(a), -0.28 + 0.03 * math.sin(a), H + 0.13), 0.006, metal, verts=4))
    cr = join(parts, "crate")
    # the parachute: eight gores, scalloped rim, a vent at the top, cords to the harness ring
    RIM, RH = 1.15, H + 1.45
    nseg, nring = 64, 10
    verts, faces, fm = [], [], []
    for i in range(nring + 1):
        v = i / nring
        th = v * math.radians(78)
        for k in range(nseg):
            a = TAU * k / nseg
            g = (k % 8) / 8                     # position within a gore: billow outwards in the middle
            bill = 1 + 0.07 * math.sin(math.pi * g) * math.sin(th)
            r = RIM * math.sin(th) / math.sin(math.radians(78)) * bill
            z = RH + 0.8 * math.cos(th) - 0.8 * math.cos(math.radians(78))
            if i == nring:
                z += 0.08 * math.sin(math.pi * g)    # scallops between the cords
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(nring):
        for k in range(nseg):
            a, b2 = i * nseg + k, i * nseg + (k + 1) % nseg
            if i == 0:
                continue                         # the vent
            faces.append((a, b2, b2 + nseg, a + nseg))
            fm.append((k // 8) % 2)
    canopy = mesh_from("canopy", verts, faces, [ca, cb], fm, smooth=50)
    bm = bmesh.new()
    bm.from_mesh(canopy.data)
    back = bmesh.ops.duplicate(bm, geom=list(bm.faces))["geom"]
    bmesh.ops.reverse_faces(bm, faces=[g for g in back if isinstance(g, bmesh.types.BMFace)])
    for g in back:
        if isinstance(g, bmesh.types.BMVert):
            g.co *= 0.995
            g.co.z += 0.004
    bm.to_mesh(canopy.data)
    bm.free()
    chute = [canopy]
    for k in range(8):
        a = TAU * k / 8
        p = Vector((RIM * math.cos(a), RIM * math.sin(a), RH))
        chute.append(rod(p, (0.1 * math.cos(a), 0.1 * math.sin(a), H + 0.03), 0.006, cord, verts=4))
    ch = join(chute, "chute", pivot=(0, 0, H))
    dims(cr)
    dims(ch)
    export_anim(cr, "crate", [(ch, cr)], anim=False)


def star_faces(cx, cz, ro, ri):
    """A point-in-star test for a five-pointed star centred at (cx, cz) (point up)."""
    pts = []
    for k in range(10):
        a = math.pi / 2 + math.pi * k / 5
        r = ro if k % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))

    def inside(x, z):
        c = False
        for i in range(10):
            (x1, z1), (x2, z2) = pts[i], pts[(i + 1) % 10]
            if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
                c = not c
        return c
    return inside, pts


def flag():
    base = mat("flag_base", (0.55, 0.52, 0.48), 0.85)
    pole = mat("flag_pole", (0.75, 0.76, 0.78), 0.25, 1.0)
    fin = mat("flag_finial", (0.95, 0.72, 0.25), 0.25, 1.0)
    cloth_m = mat("flag_cloth", (0.94, 0.93, 0.9), 0.7)
    emb = mat("flag_emblem", (1.0, 0.8, 0.25), 0.4, 0.3)
    parts = [box((0.5, 0.5, 0.16), (0, 0, 0.08), base, bevel=0.03),
             box((0.36, 0.36, 0.1), (0, 0, 0.21), base, bevel=0.025),
             lathe_r([(0.0, 0.32), (0.06, 0.32), (0.08, 0.29), (0.08, 0.26), (0.0, 0.26)], pole, segs=16, smooth=40),
             rod((0, 0, 0.3), (0, 0, 2.38), 0.028, pole, r2=0.022, verts=12),
             torus(0.03, 0.01, (0, 0, 2.25), pole, verts=12, minor=4),
             torus(0.03, 0.01, (0, 0, 1.57), pole, verts=12, minor=4),
             sphere(0.055, (0, 0, 2.43), fin, segs=14, rings=10),
             K.cyl(0.035, 0.03, (0, 0, 2.375), fin, verts=12)]
    pl = join(parts, "flag")
    L, Hh, Z = 1.1, 0.7, 2.25
    nx, nz = 22, 14
    inside, star = star_faces(0.035 + 0.55, Z - 0.35, 0.22, 0.09)
    verts, faces = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / nz
            x = 0.035 + L * u
            y = 0.03 * math.sin(u * math.pi * 1.5) * u
            verts.append((x, y, Z - Hh * v))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    c = mesh_from("cloth", verts, faces, [cloth_m, emb], smooth=50)
    # cut the cloth along the star's ten edges, so the emblem's outline is crisp (not stepped by the grid)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    for k in range(10):
        (x1, z1), (x2, z2) = star[k], star[(k + 1) % 10]
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-5,
                               plane_co=(x1, 0, z1), plane_no=(z2 - z1, 0, -(x2 - x1)))
    for f in bm.faces:
        cc = f.calc_center_median()
        f.material_index = 1 if inside(cc.x, cc.z) else 0
    bm.to_mesh(c.data)
    bm.free()
    bm = bmesh.new()
    bm.from_mesh(c.data)
    back = bmesh.ops.duplicate(bm, geom=list(bm.faces))["geom"]
    bmesh.ops.reverse_faces(bm, faces=[g for g in back if isinstance(g, bmesh.types.BMFace)])
    for g in back:
        if isinstance(g, bmesh.types.BMVert):
            g.co.y += 0.004
    bm.to_mesh(c.data)
    bm.free()
    c = join([c, rod((0.02, 0, Z + 0.01), (0.02, 0, Z - Hh - 0.01), 0.012, cloth_m, verts=6)], "cloth",
             pivot=(0, 0, Z))
    dims(pl)
    export_anim(pl, "flag", [(c, pl)], anim=False)


# ------------------------------------------------------------------ wreck bits

def bent_plate(w, h, t, bend, twist, jag, seed, M, rivets=True):
    """A plate w (x) by h (z) bent about Z, twisted, one torn edge (top) glowing; centred on the origin."""
    rnd = random.Random(seed)
    nx, nz = 16, 9
    ph = rnd.uniform(0, TAU)

    def zb(x):
        """The scorch line: a wavy boundary below the torn edge (the grid row nz - 2 follows it exactly)."""
        return h * (0.26 + 0.05 * math.sin(11.0 * x / w + ph) + 0.02 * math.sin(23.0 * x / w + 2 * ph))
    verts, faces = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            u, v = i / nx - 0.5, j / nz - 0.5
            x, z = u * w, v * h
            if j == nz:
                z += rnd.uniform(-jag, jag * 0.4)
            if j == nz - 2:
                z = zb(x)
            y = bend * (u * 2) ** 2 + twist * u * v * 2
            verts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    o = mesh_from("plate", verts, faces, [M["paint"]], smooth=40)
    solid(o, t)
    char = M["char"]
    ember = M["ember"]
    zt = h / 2 - jag * 1.5

    def pick(c, n):
        if c.z > zt and abs(n.z) > 0.3:
            return 2
        return 1 if c.z > zb(c.x) else 0
    set_mats(o, [M["paint"], char, ember], pick)
    parts = [o]
    if rivets:
        for k in range(4):
            u = -0.38 + 0.25 * k
            for v in (-0.35,):
                y = bend * (u * 2) ** 2 + twist * u * v * 2
                parts.append(rivet((u * w, y - t / 2 - 0.004, v * h), "-y", M["metal"], 0.02))
    return parts


def wreck_bits():
    M = paint_mats()
    M["char"] = mat("wreck_char", (0.06, 0.05, 0.05), 0.9)
    M["ember"] = mat("wreck_ember_glow", (1.0, 0.3, 0.04), 0.5, emit=3.0, emit_color=(1.0, 0.28, 0.02))
    bits = []
    # bit_0: five track links, still pinned together, in a loose curve
    parts = []
    for k in range(5):
        a = (k - 2) * 0.24
        c = Vector((math.sin(a) * 0.68, 0, (1 - math.cos(a)) * 0.68))
        lk = box((0.158, 0.42, 0.045), (0, 0, 0), M["track"], bevel=0.01, segs=1)
        gr = box((0.06, 0.42, 0.035), (0, 0, -0.035), M["tread"], bevel=0.008, segs=1)
        hn = box((0.05, 0.05, 0.06), (0, 0, 0.045), M["track"], bevel=0.008, segs=1)
        for o in (lk, gr, hn):
            o.data.transform(Matrix.Translation(c) @ Matrix.Rotation(a, 4, "Y"))
        parts += [lk, gr, hn]
        pc = c + Vector((math.cos(a) * 0.08, 0, -math.sin(a) * 0.08))
        parts.append(rod((pc.x, -0.23, pc.z), (pc.x, 0.23, pc.z), 0.014, M["metal"], verts=6))
    b0 = join(parts, "bit_0")
    b0.data.transform(Matrix.Translation((0, 0, -0.1)))
    b0.data.update()
    bits.append((b0, (-0.3, -0.74, 0.1)))
    # bit_1: the cupola hatch, dented, with its handle
    parts = [K.cyl(0.17, 0.035, (0, 0, 0), M["paint"], verts=24, bevel=0.01, segs=2),
             tube([(-0.07, 0, 0.018), (-0.07, 0, 0.045), (0.07, 0, 0.045), (0.07, 0, 0.018)], [0.01] * 4, M["metal"],
                  verts=6),
             rod((-0.17, -0.08, 0.0), (-0.17, 0.08, 0.0), 0.016, M["metal"], verts=8)]
    for v in parts[0].data.vertices:
        v.co.z -= 0.025 * max(0.0, 1 - ((v.co.x - 0.05) ** 2 + (v.co.y + 0.04) ** 2) / 0.01) * (v.co.z > 0)
    parts[0].data.update()
    set_mats(parts[0], [M["paint"], M["char"]], lambda c, n: 1 if c.x > 0.08 and c.z > 0 else 0)
    bits.append((join(parts, "bit_1"), (-0.27, 0.18, 1.39)))
    # bit_2: a road wheel
    o = lathe_axis(wheel_profile_road(), M["paint"], "-y", (0, 0, 0), segs=20, smooth=35, name="wheel")
    set_mats(o, [M["paint"], M["rubber"], M["metal"]],
             lambda c, n: 2 if math.hypot(c.x, c.z) < 0.05 else (1 if math.hypot(c.x, c.z) > 0.158 else 0))
    bits.append((join([o], "bit_2"), (0.45, -0.74, 0.26)))
    # bit_3: a skirt panel, bent, riveted, torn on top
    bits.append((join(bent_plate(0.78, 0.32, 0.035, 0.06, 0.05, 0.03, 3, M), "bit_3"), (0.0, -1.0, 0.58)))
    # bit_4: a twisted fender plate
    p4 = bent_plate(0.6, 0.4, 0.03, -0.05, 0.12, 0.05, 4, M, rivets=False)
    for o in p4:
        o.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    bits.append((join(p4, "bit_4"), (1.2, -0.8, 0.92)))
    # bit_5: a torn armour plate from the turret, jagged, smoking
    p5 = bent_plate(0.5, 0.5, 0.05, 0.08, -0.06, 0.08, 5, M)
    bits.append((join(p5, "bit_5"), (-0.1, -0.5, 1.2)))
    root = empty("wreck_bits")
    for o, pos in bits:
        o.location = pos
        dims(o)
    export_anim(root, "wreck_bits", [(o, root) for o, _ in bits], anim=False)


JOBS = {"tank": tank, "shell": shell, "missile": missile, "nuke": nuke, "roller": roller, "digger": digger,
        "crate": crate, "flag": flag, "wreck_bits": wreck_bits}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
