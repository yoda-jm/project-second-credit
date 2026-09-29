"""Nova Wardens (game 25) models: the three invader kinds, the player's cannon, the mothership, three bombs and the
laser bolt. Original designs (our own creatures, not the arcade's pixel sprites): a hooded one-eyed squid-thing in
banded chitin with membrane fins and four jointed tentacles, an armoured crab-thing with a plated shell, three
slit-pupilled eyes, antennae, mandibles and big serrated pincers, and a bulky octopus-thing whose ridged cranium sits
over two angry eyes and a fanged porthole round a glowing core, on eight jointed legs. Their chitin plates are raised
panels with rounded rims over a glowing under-skin, so the seams between plates read as bioluminescent panel lines.
Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/novawardens_models.py -- godot/games/novawardens/art/models [name ...]
     (TRIS=1 also prints the triangles per material)
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (merge,
mirror, smoothstep, limb, smooth_path), hopline_models.py (TurnRig, ell) and mossfolk_models.py (lathe_r); the
shape helpers below (Lathe bodies, plate, vein, eye, tentacle) are this file's own.

Axes: the game's field is the Godot XY plane seen from +Z (1 field pixel = 0.05 units). Everything is built in
Blender facing -Y, which exports as facing Godot +Z (towards the camera); Godot +Y (Blender +Z) is up the screen.
Origins at the centre of each model. Emissive materials all have "glow" in their names.

squid.glb    (30 points, top row) armature "squid_rig" (root, body, crown, eye, lid, mand.L/R, fin.L/R, ant.L/L2 and
             .R, tent.L1a/b/c, tent.L2a/b/c and .R), mesh "squid": 0.52 wide across the fins, 0.50 tall, about 12k
             triangles. A violet mantle in four bands of chitin plates (squid_skin, squid_plate) with keels, over a
             magenta glowing membrane (squid_membrane_glow); one big eye (squid_eye_glow iris with a slit pupil,
             squid_glint_glow) under a lid and a V brow; a hooked beak (squid_beak); scalloped membrane fins
             (squid_fin) on chitin rays; antennae and four jointed, fluted tentacles with glowing suckers, bulbs and
             hooks (squid_spot_glow); squid_brow (dark chitin), squid_pupil.
crab.glb     (20 points) armature "crab_rig" (root, body, eyes, arm.L/R, jaw.L/R, ant.L/L2 and .R, mand.L/R,
             leg.L1..L3 and .R, each with a lower segment leg.L1b..), mesh "crab": 0.64 wide across the claws, 0.41 tall,
             about 11k triangles. A teal shell of radial and flank plates (crab_shell, crab_plate) with pale spikes
             (crab_spike) over a cyan glowing skin (crab_membrane_glow); a black visor band (crab_visor) with three
             amber slit eyes under lids (crab_eye_glow, crab_glint_glow); antennae, mandibles, jointed arms and pincers
             (crab_claw) with glowing serrated edges (crab_claw_glow); six two-segment legs (crab_leg).
octopus.glb  (10 points) armature "octopus_rig" (root, body, brow, core, leg0..leg7 left to right, each with a lower
             segment leg0b..leg7b), mesh "octopus": 0.57 wide, 0.46 tall, about 11k triangles. A bulky lime dome
             whose cranium is ridged plates (octopus_skin, octopus_plate) glowing at the seams
             (octopus_membrane_glow) over soft skin (octopus_belly); two red eyes with horizontal slit pupils under
             heavy lids and brows (octopus_eye_glow, octopus_brow), gill slits, a ribbed porthole with fangs
             (octopus_rim) round a caged hot core (octopus_core_glow) that pulses on its own bone; eight jointed legs
             (octopus_leg) with glowing suckers and tips (octopus_sucker_glow).
             Animations (all three invaders, keyed at 60 fps):
                          march* 0.5 s: two poses, A at 0.0 s and B at 0.25 s, each held and snapping to the other
                                 (a walk step). The view can also seek 0.0 / 0.25 to follow the engine's `frame`.
                                 Secondary motion only between those instants: tentacle and leg tips, antennae and
                                 pincer jaws lag through each snap, overshoot and settle; the squid's crown breathes
                                 and its lid half-blinks, the crab's mandibles chatter, the octopus's core pulses.
                          hit    0.3 s: a jolt, everything flares out, then shrinks (ends small: hide it then).
cannon.glb   one mesh "cannon", 0.70 wide (across the nacelle rings), 0.39 tall, 0.23 deep: origin at the centre
             of the hull, the barrel along Godot +Y (the muzzle glow at y = +0.26, the hover glow down to -0.12).
             A white angular hover tank: hull panels (cannon_hull, cannon_panel) on a dark frame (cannon_dark) with
             slatted vents glowing blue, a cyan canopy (cannon_canopy_glow) in a steel frame (cannon_trim), a bolted
             collar, heat-sink fins, a glowing charging coil wound round the barrel, a pronged muzzle and front
             stripes (cannon_coil_glow), nacelles with intake fans and thruster bells glowing underneath
             (cannon_hover_glow).
mothership.glb  mesh "mothership": a crimson saucer 0.91 across (0.97 with the lamps), 0.36 tall (y -0.12 .. +0.245
             with the dome and its aerial), origin at the hull's centre on the rim plane. A child mesh "lights"
             (origin on the saucer's axis): fourteen rim lamps in steel cups alternating mother_lamp_a_glow (red) and
             mother_lamp_b_glow (amber); spin it about its local Y. Hull: plated decks (mother_hull, mother_panel)
             over a dark body (mother_dark), mother_trim, a ring of windows (mother_window_glow), mother_dome (tinted
             glass, alpha 0.6, in a steel frame, over a glowing pilot at its controls: mother_pilot_glow,
             mother_pilot_eye), mother_band_glow (a rim band, landing pods), mother_beam_glow (the underside emitter
             rings and a ridged tractor lens among dark vanes).
bomb_rolling.glb   mesh "bomb_rolling": a twisted drill, 0.14 x 0.36 (three orange flutes round a hot core, dark bands,
             a capped head): bomb_rolling_glow, bomb_rolling_core_glow, bomb_rolling_shell. Spin it about Y.
bomb_plunger.glb   mesh "bomb_plunger": a finned dart pointing down, 0.12 x 0.36: bomb_plunger_shell,
             bomb_plunger_trim, bomb_plunger_glow (bands, nose grooves, fin edges and tip).
bomb_squiggly.glb  mesh "bomb_squiggly": a zigzag of plasma beads with a hot filament and orbiting sparks, 0.15 x
             0.35: bomb_squiggly_glow, bomb_squiggly_core_glow.
shot.glb     mesh "shot": the laser bolt, 0.07 x 0.33, pointing up (Godot +Y), a white core in a cyan sheath with
             pulse rings and a flared tip: shot_core_glow, shot_glow (alpha 0.7).
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, torus, rod, tube, join, export, reset, finish
from blastyard_bombers import merge, mirror, smoothstep, limb, smooth_path, smooth_radii
from hopline_models import TurnRig, ell
from mossfolk_models import lathe_r

FPS = 60
TAU = 2 * math.pi


# ------------------------------------------------------------------ shape helpers

def cone(base, tip, r, material, verts=8):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


def cs(x):
    """Cosine spacing of 0..1 (samples bunch up at both ends, where plate rims and joints need them)."""
    return 0.5 - 0.5 * math.cos(math.pi * x)


def link(me, name):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def grid(rows, mats, closed=False, inside=None, name="grid", smooth=80, mat_fn=None):
    """A quad grid through rows of points (a row whose points all coincide becomes a pole). `closed` wraps the
    columns; normals are turned away from `inside`; mat_fn(row, col) picks a material index into `mats`."""
    mats = list(mats) if isinstance(mats, (list, tuple)) else [mats]
    bm = bmesh.new()
    V = []
    for row in rows:
        row = [Vector(p) for p in row]
        if max((p - row[0]).length for p in row) < 1e-7:
            v = bm.verts.new(row[0])
            V.append([v] * len(row))
        else:
            V.append([bm.verts.new(p) for p in row])
    n = len(rows[0])
    for i in range(len(rows) - 1):
        for j in range(n if closed else n - 1):
            k = (j + 1) % n
            f = []
            for v in (V[i][j], V[i][k], V[i + 1][k], V[i + 1][j]):
                if v not in f:
                    f.append(v)
            if len(f) < 3:
                continue
            try:
                face = bm.faces.new(f)
            except ValueError:
                continue
            face.material_index = mat_fn(i, j) if mat_fn else 0
    if inside is not None:
        bm.normal_update()
        c = Vector(inside)
        s = sum(f.normal.dot(f.calc_center_median() - c) * f.calc_area() for f in bm.faces)
        if s < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = finish(link(me, name), mats[0], smooth=smooth)
    for m in mats[1:]:
        o.data.materials.append(m)
    return o


def tube2(points, radii, mats, seg_mat=None, verts=10, caps=True, name="tube", rmod=None, smooth=80):
    """K.tube with a material per ring gap (seg_mat(i) indexes `mats`) and a radius modulation rmod(i, k) (ridges,
    flutes). Rounded caps take the material of their end."""
    mats = list(mats) if isinstance(mats, (list, tuple)) else [mats]
    pts = [Vector(p) for p in points]
    bm = bmesh.new()
    rings = []
    prev_n = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            ref = Vector((0, -1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
            n = t.cross(ref).normalized()
        else:
            n = (prev_n - t * prev_n.dot(t)).normalized()
        prev_n = n
        b = t.cross(n)
        ring = []
        for k in range(verts):
            a = TAU * k / verts
            r = radii[i] * (rmod(i, k) if rmod else 1.0)
            ring.append(bm.verts.new(p + r * (math.cos(a) * n + math.sin(a) * b)))
        rings.append(ring)
    last = len(rings) - 2
    for i, (r0, r1) in enumerate(zip(rings, rings[1:])):
        for k in range(verts):
            f = bm.faces.new((r0[k], r0[(k + 1) % verts], r1[(k + 1) % verts], r1[k]))
            f.material_index = seg_mat(i) if seg_mat else 0
    if caps:
        for end, ring, sgn, mi in ((pts[0], rings[0], -1, 0), (pts[-1], rings[-1], 1, last)):
            t = ((pts[1] - pts[0]) if sgn < 0 else (pts[-1] - pts[-2])).normalized() * sgn
            r = radii[0] if sgn < 0 else radii[-1]
            m = seg_mat(mi) if seg_mat else 0
            prev = ring
            for s in (1, 2):
                a = s * math.pi / 6
                c = end + t * r * math.sin(a)
                cur = [bm.verts.new(c + (v.co - end) * math.cos(a)) for v in ring]
                for k in range(verts):
                    f = (prev[k], prev[(k + 1) % verts], cur[(k + 1) % verts], cur[k])
                    bm.faces.new(f if sgn > 0 else f[::-1]).material_index = m
                prev = cur
            tip = bm.verts.new(end + t * r)
            for k in range(verts):
                f = (prev[k], prev[(k + 1) % verts], tip)
                bm.faces.new(f if sgn > 0 else f[::-1]).material_index = m
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = finish(link(me, name), mats[0], smooth=smooth)
    for m in mats[1:]:
        o.data.materials.append(m)
    return o


def resample(points, n):
    """n points evenly spaced by arc length along a polyline."""
    P = [Vector(p) for p in points]
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + (b - a).length)
    out = []
    j = 0
    for i in range(n):
        s = L[-1] * i / (n - 1)
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        f = (s - L[j]) / max(1e-9, L[j + 1] - L[j])
        out.append(P[j].lerp(P[j + 1], min(1.0, max(0.0, f))))
    return out


def along(points, t):
    """The point at fraction t of the arc length of a polyline, and the unit tangent there."""
    P = resample(points, 64)
    i = min(62, int(t * 63))
    f = t * 63 - i
    return P[i].lerp(P[i + 1], f), (P[i + 1] - P[i]).normalized()


def orient(o, axis_from, axis_to, at):
    """Turns a part built about the origin so axis_from points along axis_to, then moves it to `at`."""
    q = Vector(axis_from).rotation_difference(Vector(axis_to).normalized())
    o.data.transform(Matrix.Translation(Vector(at)) @ q.to_matrix().to_4x4())
    return o


def ring(r, thick, center, normal, material, verts=24, minor=6, scale=None):
    """A torus of radius r centred on `center` facing `normal`."""
    o = torus(r, thick, (0, 0, 0), material, verts=verts, minor=minor, scale=scale)
    return orient(o, (0, 0, 1), normal, center)


class Lathe:
    """A body of revolution about Z from (r, z) pairs top to bottom (smoothed), squashed by sx, sy and shaped by
    k(u, v) (a radius factor). u runs round from the front (-Y, u = 0) through +X (u = 0.25); v from the top pole (0)
    to the bottom pole (1) by arc length. p(u, v) is a surface point, n(u, v) its outward normal."""

    def __init__(self, prof, sx=1.0, sy=1.0, k=None, center=(0, 0, 0), per=6):
        pts = smooth_path([(r, 0, z) for r, z in prof], per)
        self.pr = [(max(0.0, p.x), p.z) for p in pts]
        self.pr[0] = (0.0, prof[0][1])
        self.pr[-1] = (0.0, prof[-1][1])
        L = [0.0]
        for a, b in zip(self.pr, self.pr[1:]):
            L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.L = [x / L[-1] for x in L]
        self.sx, self.sy, self.k, self.c = sx, sy, k, Vector(center)

    def rz(self, v):
        v = min(1.0, max(0.0, v))
        L = self.L
        lo, hi = 0, len(L) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if L[m] <= v:
                lo = m
            else:
                hi = m
        f = (v - L[lo]) / max(1e-9, L[hi] - L[lo])
        (r0, z0), (r1, z1) = self.pr[lo], self.pr[hi]
        return r0 + (r1 - r0) * f, z0 + (z1 - z0) * f

    def v_at(self, z):
        """The v where the profile first comes down to height z."""
        for i in range(len(self.pr) - 1):
            z0, z1 = self.pr[i][1], self.pr[i + 1][1]
            if (z0 - z) * (z1 - z) <= 0 and z0 != z1:
                f = (z0 - z) / (z0 - z1)
                return self.L[i] + (self.L[i + 1] - self.L[i]) * f
        return 0.0 if z > self.pr[0][1] else 1.0

    def p(self, u, v):
        r, z = self.rz(v)
        a = TAU * u
        kk = self.k(u, v) if self.k else 1.0
        return Vector((self.c.x + r * kk * self.sx * math.sin(a), self.c.y - r * kk * self.sy * math.cos(a),
                       self.c.z + z))

    def n(self, u, v):
        e = 1e-3
        du = self.p(u + e, v) - self.p(u - e, v)
        dv = self.p(u, min(1.0, v + e)) - self.p(u, max(0.0, v - e))
        nn = dv.cross(du)
        if nn.length < 1e-10:
            q = self.p(u, v) - self.c
            return q.normalized() if q.length > 1e-9 else Vector((0, 0, 1))
        return nn.normalized()

    def at(self, u, z, h=0.0):
        """The surface point at azimuth u and height z (lifted h along the normal), and the normal."""
        v = self.v_at(z)
        return self.p(u, v) + self.n(u, v) * h, self.n(u, v)

    def mesh(self, nu, nv, material, name="body", mat_fn=None, smooth=80):
        rows = [[self.p(j / nu, i / nv) for j in range(nu)] for i in range(nv + 1)]
        return grid(rows, material, closed=True, inside=self.c + Vector((0, 0, self.rz(0.5)[1])), name=name,
                    mat_fn=mat_fn, smooth=smooth)


def edge(s, r0, r1):
    a = smoothstep(0.0, r0, s) if r0 > 0 else 1.0
    b = smoothstep(0.0, r1, 1.0 - s) if r1 > 0 else 1.0
    return a * b


def plate(B, u0, u1, z0, z1, material, nu=10, nv=8, thick=0.008, rim=(0.12, 0.12, 0.16, 0.16), tuck=0.0025,
          crown=None, name="plate"):
    """An armour plate over the body B between azimuths u0..u1 and heights z0 (top) .. z1: raised `thick` with rounded
    rims that tuck under the surface at the edges, so the body shows in the seams between plates as panel lines.
    crown(s, t) adds height inside the plate (ridges, keels); s runs across (u), t down (z), both 0..1."""
    v0, v1 = B.v_at(z0), B.v_at(z1)
    closed = (u1 - u0) >= 0.999
    rows = []
    for i in range(nv + 1):
        t = cs(i / nv)
        v = v0 + (v1 - v0) * t
        et = edge(t, rim[2], rim[3])
        row = []
        for j in range(nu if closed else nu + 1):
            s = j / nu if closed else cs(j / nu)
            u = u0 + (u1 - u0) * s
            es = 1.0 if closed else edge(s, rim[0], rim[1])
            h = -tuck + (thick + tuck) * es * et
            if crown:
                h += crown(s, t) * es * et
            row.append(B.p(u, v) + B.n(u, v) * h)
        rows.append(row)
    return grid(rows, material, closed=closed, inside=B.c + Vector((0, 0, B.rz(0.5)[1])), name=name, smooth=50)


def vein(B, uz, radius, material, lift=0.003, per=3, verts=6, taper=0.5, caps=True):
    """A glowing thread lying on body B through (u, z) points."""
    q = smooth_path([(u, z, 0) for u, z in uz], per)
    pts = []
    for p in q:
        v = B.v_at(p.y)
        pts.append(B.p(p.x, v) + B.n(p.x, v) * lift)
    n = len(pts)
    return tube(pts, [radius * (1 - taper * i / (n - 1)) for i in range(n)], material, verts=verts, caps=caps,
                name="vein")


def cap(r, axis, th0, th1, material, nth=6, nph=24, center=(0, 0, 0), name="cap", smooth=80):
    """A band of a sphere (radius r) round `axis` between polar angles th0..th1 (degrees)."""
    a = Vector(axis).normalized()
    e1 = a.orthogonal().normalized()
    e2 = a.cross(e1)
    c = Vector(center)
    rows = []
    for i in range(nth + 1):
        th = math.radians(th0 + (th1 - th0) * i / nth)
        rows.append([c + r * (math.cos(th) * a + math.sin(th) * (math.cos(TAU * j / nph) * e1
                                                                  + math.sin(TAU * j / nph) * e2))
                     for j in range(nph)])
    return grid(rows, material, closed=True, inside=c, name=name, smooth=smooth)


def eye(c, r, m, look=(0, -1, 0), iris=48, slit=(0.2, 0.75), lid_up=62, lid_tilt=0.0, lid_low=48, segs=20,
        lids=True):
    """A detailed eye of radius r at c looking along `look`: a glossy ball (m["ball"]), a domed glowing iris with
    fine radial ridges (m["iris"]) inside a dark limbal ring and a brighter inner ring (m["ring"]), a slit or round
    pupil (m["pupil"], slit = (width, height) as fractions of r), a glint (m["glint"]) and chitin lids (m["lid"]):
    the upper one covers lid_up degrees from its pole, tilted lid_tilt degrees (+: lower towards +X), the lower
    one lid_low. Returns (eye parts, upper lid parts, lower lid parts)."""
    th_i = math.radians(iris)
    rows = []
    for i in range(6):
        th = th_i * (i / 5) ** 0.8
        row = []
        for j in range(segs * 3 // 2):
            ph = TAU * j / (segs * 3 // 2)
            rr = r * (1.0 + 0.07 * math.cos(0.5 * math.pi * th / th_i)) * (1 + 0.012 * (j % 2) * (i > 1))
            row.append(Vector((rr * math.sin(th) * math.cos(ph), -rr * math.cos(th), rr * math.sin(th) * math.sin(ph))))
        rows.append(row)
    ball = [sphere(r, (0, 0, 0), m["ball"], segs=segs, rings=segs // 2 - 2),
            grid(rows, m["iris"], closed=True, inside=(0, 0, 0), name="iris")]
    lr = r * math.sin(th_i)
    ball.append(ring(lr * 1.01, r * 0.06, (0, -r * math.cos(th_i) * 1.005, 0), (0, -1, 0), m["pupil"], verts=segs,
                     minor=4))
    if m.get("ring"):
        ball.append(ring(lr * 0.52, r * 0.035, (0, -r * 1.045, 0), (0, -1, 0), m["ring"], verts=segs, minor=4))
    # the pupil: an ellipse (a slit when narrow) lying on the iris dome
    prow = []
    for i in range(9):
        z = slit[1] * (-1 + 2 * cs(i / 8))
        hw = slit[0] * math.sqrt(max(0.0, 1 - (z / slit[1]) ** 2))
        row = []
        for j in range(7):
            x = hw * (-1 + 2 * j / 6)
            d = Vector((x, -math.sqrt(max(0.0, 1 - x * x - z * z)), z))
            th = math.acos(min(1.0, -d.y))
            row.append(d * r * (1.0 + 0.07 * math.cos(0.5 * math.pi * min(1.0, th / th_i)) + 0.022))
        prow.append(row)
    ball.append(grid(prow, m["pupil"], inside=(0, 0, 0), name="pupil"))
    ball.append(sphere(r * 0.1, (-r * 0.3, -r * 1.02, r * 0.34), m["glint"], segs=8, rings=5))
    up, low = [], []
    if lids:
        R = Matrix.Rotation(math.radians(lid_tilt), 3, "Y")
        ax = R @ Vector((0, 0.18, 1)).normalized()
        up.append(cap(r * 1.12, ax, 0, lid_up, m["lid"], nth=4, nph=segs, name="lid"))
        e = math.radians(lid_up)
        up.append(ring(r * 1.12 * math.sin(e), r * 0.09, ax * r * 1.12 * math.cos(e), ax, m["lid"], verts=segs,
                       minor=4))
        ax2 = R @ Vector((0, 0.25, -1)).normalized()
        low.append(cap(r * 1.1, ax2, 0, lid_low, m["lid"], nth=3, nph=segs, name="lid"))
        e = math.radians(lid_low)
        low.append(ring(r * 1.1 * math.sin(e), r * 0.07, ax2 * r * 1.1 * math.cos(e), ax2, m["lid"], verts=segs,
                        minor=3))
    M = Matrix.Translation(Vector(c)) @ Vector((0, -1, 0)).rotation_difference(Vector(look).normalized()).to_matrix().to_4x4()
    for o in ball + up + low:
        o.data.transform(M)
    return ball, up, low


def tentacle(pts, radii, mats, n_seg, verts=10, per=4, pinch=0.22, band=0.14, ridges=0, rings=None):
    """A jointed tentacle through pts: n_seg segments pinched at the joints, the joints in mats[1] (a darker band),
    optional ridges (flutes) along it."""
    P = smooth_path(pts, per)
    R = smooth_radii(radii, per)
    N = rings or n_seg * 4 + 1
    Q = resample(P, N)
    rs = []
    for i in range(N):
        x = i / (N - 1) * (len(R) - 1)
        j = min(len(R) - 2, int(x))
        rs.append(R[j] + (R[j + 1] - R[j]) * (x - j))
    radii2, segm = [], []
    for i in range(N):
        f = (i / (N - 1) * n_seg) % 1.0
        radii2.append(rs[i] * (1 - pinch + pinch * math.sin(math.pi * f) ** 0.5))
    for i in range(N - 1):
        f = ((i + 0.5) / (N - 1) * n_seg) % 1.0
        segm.append(1 if (f < band or f > 1 - band) and len(mats) > 1 else 0)
    rm = (lambda i, k: 1.0 + 0.08 * math.cos(ridges * TAU * k / verts)) if ridges else None
    return tube2(Q, radii2, mats, seg_mat=lambda i: segm[i], verts=verts, caps=True, rmod=rm, name="tentacle")


def lerp_pose(P, Q, k, names):
    return {n: tuple(a + (b - a) * k for a, b in zip(P.get(n, (0, 0, 0)), Q.get(n, (0, 0, 0)))) for n in names}


def march(rig, a, b, tips=(), over=0.4, back=0.12, extra=None):
    """The 2-beat step (60 fps, 0.5 s): pose A from 0.0 s, snap to B, B from 0.25 s, snap back. The `tips` (tentacle
    ends, antennae) lag through each snap, overshoot and settle while the pose is held (follow-through); the exact
    poses sit at frames 0 and 15 so the view can seek 0.0 / 0.25. extra: {frame: pose} merged in (breathing)."""
    def at(base, other, k):
        o = dict(base)
        o.update(lerp_pose(other, base, k, tips))
        return o
    keys = {0: a, 4: at(a, b, 1 + over), 8: at(a, b, 1 - back), 11: a, 13: at(b, a, 0.0), 15: b,
            19: at(b, a, 1 + over), 23: at(b, a, 1 - back), 26: b, 28: at(a, b, 0.0), 30: a}
    for f, p in (extra or {}).items():
        keys[f] = merge(keys[f], p)
    rig.action("march", keys, loop=True)


def hit(rig, flare, shrink):
    rig.action("hit", {0: {}, 4: flare, 10: merge(flare, {"%root": 1.1}), 18: shrink})


def dims(o):
    bb = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector([min(v[i] for v in bb) for i in range(3)])
    hi = Vector([max(v[i] for v in bb) for i in range(3)])
    print("  %s: width %.3f  depth %.3f  height %.3f  (x %.3f .. %.3f, z %.3f .. %.3f)  %d tris, %d materials" % (
        o.name, hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo.x, hi.x, lo.z, hi.z, K.tris(o), len(o.data.materials)))
    if os.environ.get("TRIS"):
        per = {}
        for p in o.data.polygons:
            n = o.data.materials[p.material_index].name
            per[n] = per.get(n, 0) + len(p.vertices) - 2
        print("   ", sorted(per.items(), key=lambda x: -x[1]))


def lr(fn):
    """Calls fn(s, side) for the left (+X, "L") and right (-X, "R") sides and returns the parts."""
    return [fn(1, "L"), fn(-1, "R")]


# ------------------------------------------------------------------ squid (30 points)

def squid():
    chitin = mat("squid_skin", (0.4, 0.07, 0.8), 0.3, coat=1.0)
    plate2 = mat("squid_plate", (0.3, 0.04, 0.62), 0.42, coat=0.6)
    dark = mat("squid_brow", (0.1, 0.015, 0.17), 0.3, coat=0.9)
    beak = mat("squid_beak", (0.04, 0.01, 0.04), 0.18, coat=1.0)
    pupil = mat("squid_pupil", (0.005, 0.0, 0.01), 0.2, coat=1.0)
    memb = mat("squid_membrane_glow", (0.1, 0.0, 0.12), 0.35, emit=1.6, emit_color=(0.95, 0.05, 0.75))
    fin = mat("squid_fin", (0.42, 0.03, 0.7), 0.3, coat=0.8, emit=0.45, emit_color=(0.75, 0.05, 1.0))
    eye_g = mat("squid_eye_glow", (0.75, 1.0, 0.15), 0.2, emit=3.0)
    spot = mat("squid_spot_glow", (1.0, 0.4, 0.95), 0.3, emit=4.0)
    glint = mat("squid_glint_glow", (1.0, 1.0, 1.0), 0.2, emit=6.0)
    EM = {"ball": beak, "iris": eye_g, "ring": spot, "pupil": pupil, "glint": glint, "lid": plate2}

    E = Vector((0, -0.08, 0.026))
    bones = {"root": ((0, 0, -0.05), (0, 0, 0.0), None),
             "body": ((0, 0, -0.06), (0, 0, 0.16), "root"),
             "crown": ((0, 0, 0.12), (0, 0, 0.24), "body"),
             "eye": (tuple(E), tuple(E + Vector((0, -0.1, 0))), "body"),
             "lid": (tuple(E), tuple(E + Vector((0.06, 0, 0))), "eye"),
             "mand.L": ((0.012, -0.095, -0.03), (0.01, -0.11, -0.075), "body"),
             "mand.R": ((-0.012, -0.095, -0.03), (-0.01, -0.11, -0.075), "body"),
             "fin.L": ((0.09, 0, 0.16), (0.24, 0, 0.08), "body"),
             "fin.R": ((-0.09, 0, 0.16), (-0.24, 0, 0.08), "body"),
             "ant.L": ((0.03, -0.03, 0.215), (0.08, -0.03, 0.245), "crown"),
             "ant.L2": ((0.08, -0.03, 0.245), (0.14, -0.03, 0.24), "ant.L"),
             "ant.R": ((-0.03, -0.03, 0.215), (-0.08, -0.03, 0.245), "crown"),
             "ant.R2": ((-0.08, -0.03, 0.245), (-0.14, -0.03, 0.24), "ant.R")}
    # tentacles: two per side as (x, z) points; the outer ones curl outwards, the inner ones hang and hook in
    tents = {"L1": [(0.035, -0.06), (0.05, -0.12), (0.042, -0.175), (0.058, -0.212), (0.078, -0.212)],
             "L2": [(0.078, -0.05), (0.118, -0.105), (0.152, -0.15), (0.19, -0.162), (0.205, -0.14)]}
    for k, pts in list(tents.items()):
        tents[k.replace("L", "R")] = [(-x, z) for x, z in pts]
    for k, pts in tents.items():
        p = [(x, 0, z) for x, z in pts]
        bones["tent.%sa" % k] = (p[0], p[1], "body")
        bones["tent.%sb" % k] = (p[1], p[2], "tent.%sa" % k)
        bones["tent.%sc" % k] = (p[2], p[4], "tent.%sb" % k)
    rig = TurnRig(bones, 0, fps=FPS)

    # the mantle: a hooded teardrop rising to a swept crown, flatter front to back; it glows through the seams
    B = Lathe([(0.0, 0.25), (0.03, 0.236), (0.06, 0.2), (0.09, 0.15), (0.115, 0.09), (0.128, 0.03), (0.125, -0.02),
               (0.105, -0.055), (0.065, -0.075), (0.0, -0.08)], sx=1.0, sy=0.8)
    body = [B.mesh(30, 20, memb, name="mantle")]
    # chitin plates: a crown cap, then bands split front, back and at the sides (the seams glow), the lower bands
    # parted round the eye; a keel ridge up the front of each band
    keel = lambda s, t: 0.006 * math.exp(-((s - 0.5) / 0.12) ** 2)
    ridge = lambda s, t: 0.004 * math.exp(-((t - 0.45) / 0.14) ** 2)
    body.append(plate(B, 0, 1, 0.25, 0.167, chitin, nu=24, nv=5, thick=0.009, rim=(0, 0, 0, 0.3),
                      crown=lambda s, t: 0.004 * math.cos(6 * TAU * s) ** 8 * t))
    bands = [(0.16, 0.108, [(-0.12, 0.12), (0.13, 0.37), (0.38, 0.62), (0.63, 0.87)]),
             (0.101, 0.052, [(-0.2, -0.1), (0.1, 0.2), (0.21, 0.39), (0.4, 0.6), (0.61, 0.79)]),
             (0.045, -0.012, [(0.095, 0.24), (0.25, 0.45), (0.55, 0.75), (0.76, 0.905)]),
             (-0.019, -0.074, [(-0.085, 0.085), (0.095, 0.24), (0.25, 0.45), (0.55, 0.75), (0.76, 0.905)])]
    for bi, (z0, z1, us) in enumerate(bands):
        for pi, (u0, u1) in enumerate(us):
            m = chitin if (bi + pi) % 2 == 0 else plate2
            body.append(plate(B, u0, u1, z0, z1, m, nu=8, nv=5, thick=0.008 - 0.001 * bi,
                              crown=(keel if abs(u0 + u1) < 0.05 else ridge)))
    # a V brow over the eye (the membrane glows round it)
    def front(x, z, h):
        r = B.rz(B.v_at(z))[0]
        return B.at(math.asin(max(-1.0, min(1.0, x / r))) / TAU, z, h)[0]
    brow = [(-0.092, 0.084), (-0.06, 0.1), (-0.028, 0.096), (0, 0.084), (0.028, 0.096), (0.06, 0.1), (0.092, 0.084)]
    line = resample(smooth_path([(x, z, 0) for x, z in brow], 3), 19)
    body.append(tube([front(q.x, q.y, 0.006) for q in line], [0.006 + 0.005 * math.sin(math.pi * i / 18)
                                                               for i in range(19)], chitin, verts=8, name="brow"))
    body.append(tube([front(q.x, q.y - 0.011, 0.003) for q in line[2:-2]], [0.0028] * 15, spot, verts=5,
                     name="brow_glow"))
    # bioluminescent freckles down the sides of the plates, a glowing vein fork on each flank
    for s in (-1, 1):
        for i, (u, z) in enumerate(((0.19, 0.135), (0.17, 0.08), (0.2, 0.025), (0.18, -0.045), (0.12, 0.183))):
            p, n = B.at(u if s > 0 else 1 - u, z, 0.009)
            body.append(sphere(0.0065 - 0.0005 * (i % 3), p, spot, segs=6, rings=4))
        body.append(vein(B, [(u if s > 0 else 1 - u, z) for u, z in
                             ((0.245, 0.2), (0.25, 0.14), (0.248, 0.08), (0.25, 0.02), (0.247, -0.05))],
                         0.0045, spot, lift=0.002, verts=4))
    rig.rigid("body", body)
    # the hood's crest: three short glowing spines along the top plate
    rig.rigid("crown", [cone((0, -0.005 + 0.015 * i, 0.245 - 0.012 * i), (0, 0.01 + 0.02 * i, 0.272 - 0.018 * i),
                             0.009 - 0.002 * i, dark, verts=8) for i in range(3)])
    # the eye
    ball, up, low = eye(E, 0.054, EM, slit=(0.16, 0.72), iris=50, lid_up=72, lid_low=52, segs=18)
    rig.rigid("eye", ball, low)
    rig.rigid("lid", up)
    # the beak: two hooked mandibles with glowing inner edges, feeding cirri beside it
    for s, side in ((1, "L"), (-1, "R")):
        m = limb([(s * 0.004, -0.098, -0.028), (s * 0.02, -0.112, -0.05), (s * 0.016, -0.12, -0.07),
                  (s * 0.002, -0.118, -0.083)], [0.011, 0.01, 0.006, 0.002], beak, verts=8, per=3, caps=True)
        g = limb([(s * 0.006, -0.108, -0.035), (s * 0.013, -0.12, -0.055), (s * 0.006, -0.124, -0.072)],
                 [0.003, 0.003, 0.0015], spot, verts=5, per=3, caps=True)
        rig.rigid("mand." + side, m, g)
    # fins: membranes on chitin rays (a scalloped trailing edge between the ray tips), glowing edge beads
    tips = [(0.15, 0.23), (0.215, 0.18), (0.255, 0.115), (0.245, 0.07), (0.19, 0.075)]

    def fin_side(s, side):
        outline = [(0.07, 0.2)]
        for i, t in enumerate(tips):
            outline.append(t)
            if i + 1 < len(tips):
                a, b = Vector((*t, 0)), Vector((*tips[i + 1], 0))
                mid = (a + b) / 2
                outline.append((mid.x - 0.012 * (0.6 if i == 3 else 1), mid.y - 0.01 * (0.2 if i == 3 else 1)))
        outline += [(0.12, 0.085), (0.095, 0.1)]
        poly = [(s * x, z) for x, z in outline]
        parts = [K.prism(poly if s > 0 else poly[::-1], 0.012, (0, 0.012, 0), fin, bevel=0.004, segs=2)]
        roots = [(0.085, 0.19), (0.09, 0.16), (0.095, 0.13), (0.1, 0.11), (0.1, 0.1)]
        for (bx, bz), (tx, tz) in zip(roots, tips):
            mid = ((bx + tx) / 2, (bz + tz) / 2 + 0.006)
            parts.append(limb([(s * bx, 0.005, bz), (s * mid[0], 0.005, mid[1]), (s * tx, 0.005, tz)],
                              [0.007, 0.005, 0.0025], chitin, verts=6, per=3, caps=True))
            parts.append(sphere(0.007, (s * tx, 0.01, tz), spot, segs=6, rings=4))
        parts.append(limb([(s * 0.07, 0.012, 0.2), (s * 0.085, 0.012, 0.15), (s * 0.1, 0.012, 0.1)],
                          [0.011, 0.012, 0.01], dark, verts=8, per=3, caps=True))
        rig.rigid("fin." + side, parts)
    lr(fin_side)
    # antennae: thin whips with a joint and a glowing bulb
    for s, side in ((1, "L"), (-1, "R")):
        a = limb([(s * 0.025, -0.03, 0.205), (s * 0.055, -0.035, 0.235), (s * 0.08, -0.03, 0.245)],
                 [0.006, 0.005, 0.004], dark, verts=6, per=3, caps=True)
        b = limb([(s * 0.08, -0.03, 0.245), (s * 0.11, -0.03, 0.25), (s * 0.135, -0.03, 0.238)],
                 [0.004, 0.0032, 0.0022], dark, verts=6, per=3, caps=True)
        rig.rigid("ant." + side, a, sphere(0.0065, (s * 0.08, -0.03, 0.245), plate2, segs=8, rings=5))
        rig.rigid("ant.%s2" % side, b, sphere(0.01, (s * 0.139, -0.03, 0.236), spot, segs=10, rings=6))
    # tentacles: jointed, fluted, a row of glowing suckers down the front, a hooked claw round a glowing bulb
    for k, pts in tents.items():
        s = 1 if k[0] == "L" else -1
        P = [(x, -0.01, z) for x, z in pts]
        names = ["tent.%s%s" % (k, c) for c in "abc"]
        t = tentacle(P, [0.03, 0.022, 0.016, 0.011, 0.007], [chitin, dark], 6, verts=8, ridges=4, rings=19)
        su = []
        path = resample(smooth_path(P, 4), 40)
        for i in range(1, 5):
            q, d = along(path, 0.1 + 0.17 * i)
            rr = 0.03 * (1 - 0.13 * i)
            su.append(sphere(0.0045 + 0.0006 * (5 - i), q + Vector((0, -rr * 0.8, 0)), memb, segs=6, rings=3,
                             scale=(1, 0.6, 1)))
        tip = Vector(P[-1])
        d = (Vector(P[-1]) - Vector(P[-2])).normalized()
        hook = limb([tip, tip + d * 0.014 + Vector((0, 0, -0.004)), tip + d * 0.02 + Vector((0, 0, 0.008))],
                    [0.005, 0.003, 0.0008], beak, verts=6, per=3, caps=True)
        bulb = sphere(0.011, tip - d * 0.004, spot, segs=8, rings=5)
        rig.smooth(names, t, power=6)
        rig.smooth(names, su, power=6)
        rig.rigid(names[2], hook, bulb)
    rig.build("squid")
    dims(rig.mesh)

    tips = [n for n in rig.bones if n.startswith("tent.") and n[-1] in "bc"] + ["ant.L2", "ant.R2"]
    a = merge({"@body": (0, 0, 0.0), "%body": (1.03, 1.0, 0.97)},
              {"tent.L1a": (0, -18, 0), "tent.L1b": (0, -22, 0), "tent.L1c": (0, -20, 0),
               "tent.L2a": (0, 20, 0), "tent.L2b": (0, 24, 0), "tent.L2c": (0, 28, 0),
               "tent.R1a": (0, -10, 0), "tent.R1b": (0, 16, 0), "tent.R1c": (0, 18, 0),
               "tent.R2a": (0, -8, 0), "tent.R2b": (0, -20, 0), "tent.R2c": (0, -24, 0),
               "fin.L": (0, 12, 0), "fin.R": (0, 4, 0), "ant.L": (0, -8, 0), "ant.L2": (0, -14, 0),
               "ant.R": (0, 4, 0), "ant.R2": (0, 10, 0), "mand.L": (0, -8, 0), "mand.R": (0, 8, 0)})
    b = merge({"@body": (0, 0, 0.015), "%body": (0.97, 1.0, 1.04)},
              {"tent.R1a": (0, 18, 0), "tent.R1b": (0, 22, 0), "tent.R1c": (0, 20, 0),
               "tent.R2a": (0, -20, 0), "tent.R2b": (0, -24, 0), "tent.R2c": (0, -28, 0),
               "tent.L1a": (0, 10, 0), "tent.L1b": (0, -16, 0), "tent.L1c": (0, -18, 0),
               "tent.L2a": (0, 8, 0), "tent.L2b": (0, 20, 0), "tent.L2c": (0, 24, 0),
               "fin.R": (0, -12, 0), "fin.L": (0, -4, 0), "ant.R": (0, 8, 0), "ant.R2": (0, 14, 0),
               "ant.L": (0, -4, 0), "ant.L2": (0, -10, 0), "mand.L": (0, 6, 0), "mand.R": (0, -6, 0)})
    march(rig, a, b, tips, extra={4: {"%crown": (1.02, 1.02, 1.03), "lid": (20, 0, 0)}, 8: {"%crown": (1.03, 1.03, 1.05)},
                                  19: {"%crown": (1.02, 1.02, 1.03)}, 23: {"%crown": (1.03, 1.03, 1.05)}})
    hit(rig, merge({"%root": 1.2, "%eye": (1.3, 1, 1.3), "lid": (-25, 0, 0), "tent.L2a": (0, 40, 0),
                    "tent.R2a": (0, -40, 0), "tent.L2c": (0, 40, 0), "tent.R2c": (0, -40, 0),
                    "tent.L1a": (0, 25, 0), "tent.R1a": (0, -25, 0), "mand.L": (0, -25, 0), "mand.R": (0, 25, 0)},
                   mirror({"fin.L": (0, 30, 0), "ant.L": (0, -30, 0), "ant.L2": (0, -30, 0)})),
        {"%root": 0.15})
    rig.save("squid")


# ------------------------------------------------------------------ crab (20 points)

def crab():
    shell = mat("crab_shell", (0.02, 0.5, 0.58), 0.25, 0.2, coat=1.0)
    plate_m = mat("crab_plate", (0.02, 0.26, 0.4), 0.4, 0.3, coat=0.7)
    spike = mat("crab_spike", (0.75, 0.95, 0.92), 0.3, coat=0.6)
    visor = mat("crab_visor", (0.005, 0.015, 0.025), 0.15, 0.2, coat=1.0)
    claw_m = mat("crab_claw", (0.05, 0.68, 0.68), 0.22, 0.25, coat=1.0)
    leg_m = mat("crab_leg", (0.015, 0.2, 0.26), 0.35, 0.3, coat=0.6)
    memb = mat("crab_membrane_glow", (0.0, 0.08, 0.1), 0.35, emit=1.5, emit_color=(0.05, 1.0, 0.85))
    eye_g = mat("crab_eye_glow", (1.0, 0.45, 0.02), 0.2, emit=3.0)
    cglow = mat("crab_claw_glow", (0.3, 1.0, 0.95), 0.3, emit=3.5)
    glint = mat("crab_glint_glow", (1.0, 1.0, 0.95), 0.2, emit=6.0)
    EM = {"ball": visor, "iris": eye_g, "ring": None, "pupil": visor, "glint": glint, "lid": plate_m}

    LEGS = [(0.06, 0.1, 0.075, -0.2), (0.1, 0.16, 0.14, -0.19), (0.135, 0.215, 0.2, -0.17)]  # hip, knee, foot x, z
    bones = {"root": ((0, 0, -0.05), (0, 0, 0.0), None),
             "body": ((0, 0, -0.08), (0, 0, 0.12), "root"),
             "eyes": ((0, -0.1, 0.0), (0, -0.2, 0.0), "body"),
             "arm.L": ((0.14, 0, 0.0), (0.24, 0, 0.08), "body"),
             "jaw.L": ((0.24, 0, 0.08), (0.28, 0, 0.18), "arm.L"),
             "arm.R": ((-0.14, 0, 0.0), (-0.24, 0, 0.08), "body"),
             "jaw.R": ((-0.24, 0, 0.08), (-0.28, 0, 0.18), "arm.R")}
    for s, side in ((1, "L"), (-1, "R")):
        bones["ant.%s" % side] = ((s * 0.035, -0.1, 0.06), (s * 0.08, -0.1, 0.13), "body")
        bones["ant.%s2" % side] = ((s * 0.08, -0.1, 0.13), (s * 0.15, -0.1, 0.2), "ant." + side)
        bones["mand.%s" % side] = ((s * 0.02, -0.11, -0.04), (s * 0.015, -0.13, -0.09), "body")
        for i, (hx, kx, fx, fz) in enumerate(LEGS):
            bones["leg.%s%d" % (side, i + 1)] = ((s * hx, 0, -0.07), (s * kx, 0, -0.1), "body")
            bones["leg.%s%db" % (side, i + 1)] = ((s * kx, 0, -0.1), (s * fx, 0, fz), "leg.%s%d" % (side, i + 1))
    rig = TurnRig(bones, 0, fps=FPS)

    # the carapace: a wide low shell, glowing cyan through the seams between its plates
    B = Lathe([(0.0, 0.118), (0.08, 0.11), (0.14, 0.083), (0.172, 0.04), (0.18, 0.0), (0.168, -0.035), (0.13, -0.06),
               (0.07, -0.075), (0.0, -0.078)], sx=1.0, sy=0.74, k=lambda u, v: 1.0 + 0.035 * math.cos(2 * TAU * u))
    body = [B.mesh(36, 18, memb, name="carapace")]
    keel = lambda s, t: 0.007 * math.exp(-((s - 0.5) / 0.1) ** 2) * (1 - 0.5 * t)
    ribs = lambda s, t: 0.003 * math.exp(-((t - 0.5) / 0.1) ** 2)
    body.append(plate(B, 0, 1, 0.118, 0.095, shell, nu=24, nv=4, thick=0.009, rim=(0, 0, 0, 0.35)))
    for k in range(7):   # radial plates round the crown, the front one on the keel
        u0 = (k - 0.5) / 7 + 0.005
        body.append(plate(B, u0, u0 + 1 / 7 - 0.01, 0.092, 0.028, shell if k % 2 == 0 else plate_m, nu=8, nv=5,
                          thick=0.009, crown=keel))
    for k in range(10):   # the flank band, a spike on each plate
        u0 = (k - 0.5) / 10 + 0.004
        if k == 0:
            continue   # the face
        body.append(plate(B, u0, u0 + 0.1 - 0.008, 0.024, -0.03, plate_m if k % 2 else shell, nu=6, nv=5,
                          thick=0.008, crown=ribs))
        p, n = B.at(u0 + 0.046, 0.0, 0.006)
        side = Vector((math.sin(TAU * (u0 + 0.046)), 0, 0))
        tipd = (n + side * 0.8 + Vector((0, 0, 0.3))).normalized()
        body.append(cone(p, p + tipd * (0.03 if k in (2, 3, 7, 8) else 0.022), 0.012, spike, verts=8))
    body.append(plate(B, 0, 1, -0.036, -0.078, plate_m, nu=24, nv=4, thick=0.006, rim=(0, 0, 0.3, 0)))
    # the face: a black visor band, a toothed mouth plate below it
    body.append(ell((0, -0.092, -0.003), (0.105, 0.04, 0.036), visor, segs=18, rings=7))
    body.append(ell((0, -0.1, -0.045), (0.05, 0.03, 0.02), plate_m, segs=12, rings=6))
    for i in range(5):
        x = -0.03 + 0.015 * i
        body.append(cone((x, -0.126, -0.04), (x * 0.9, -0.13, -0.056), 0.0045, spike, verts=6))
    # glowing vein pairs over the crown plates
    for s in (-1, 1):
        body.append(vein(B, [(s * 0.02 % 1, 0.1), (s * 0.05 % 1, 0.075), (s * 0.06 % 1, 0.045)], 0.003, cglow,
                         verts=5))
    rig.rigid("body", body)
    # three eyes in the visor, the middle one biggest, each with lids
    ey = []
    for x, r, z, look in ((-0.062, 0.024, 0.0, (-0.3, -1, 0.05)), (0.0, 0.031, 0.004, (0, -1, 0.05)),
                          (0.062, 0.024, 0.0, (0.3, -1, 0.05))):
        ball, up, low = eye((x, -0.122 + abs(x) * 0.2, z), r, EM, look=look, iris=52, slit=(0.13, 0.5),
                            lid_up=76, lid_low=58, lid_tilt=-26 * (x / 0.062) if x else 0, segs=14)
        ey += ball + up + low
    rig.rigid("eyes", ey)
    # antennae: long whips from above the visor with a joint and a glowing bulb
    for s, side in ((1, "L"), (-1, "R")):
        a = limb([(s * 0.03, -0.105, 0.045), (s * 0.055, -0.108, 0.1), (s * 0.08, -0.105, 0.13)],
                 [0.007, 0.006, 0.0045], leg_m, verts=6, per=2, caps=True)
        b = limb([(s * 0.08, -0.105, 0.13), (s * 0.12, -0.1, 0.175), (s * 0.155, -0.1, 0.19)],
                 [0.0045, 0.0035, 0.002], leg_m, verts=5, per=2, caps=True)
        rig.rigid("ant." + side, a, sphere(0.0075, (s * 0.08, -0.105, 0.13), shell, segs=8, rings=5))
        rig.rigid("ant.%s2" % side, b, sphere(0.009, (s * 0.157, -0.1, 0.19), cglow, segs=8, rings=5))
        # mandibles: jointed hooks with glowing inner edges
        m = limb([(s * 0.018, -0.118, -0.04), (s * 0.027, -0.126, -0.06), (s * 0.018, -0.13, -0.078),
                  (s * 0.004, -0.127, -0.086)], [0.009, 0.008, 0.005, 0.002], claw_m, verts=6, per=3, caps=True)
        g = limb([(s * 0.017, -0.13, -0.05), (s * 0.02, -0.135, -0.066), (s * 0.01, -0.134, -0.08)],
                 [0.0025, 0.0025, 0.0012], cglow, verts=5, per=3, caps=True)
        rig.rigid("mand." + side, m, g)

    # arms and pincers: jointed arm, a ridged palm with knuckle spikes, a serrated fixed finger (on the arm) and a
    # moving finger (the jaw), both with glowing cutting edges
    for s, side in ((1, "L"), (-1, "R")):
        arm = [sphere(0.03, (s * 0.14, -0.005, 0.0), leg_m, segs=10, rings=6),
               limb([(s * 0.14, -0.005, 0.0), (s * 0.18, -0.01, 0.005), (s * 0.205, -0.012, 0.025)],
                    [0.026, 0.024, 0.022], claw_m, verts=8, per=2),
               sphere(0.022, (s * 0.207, -0.012, 0.028), leg_m, segs=8, rings=5),
               limb([(s * 0.207, -0.012, 0.028), (s * 0.225, -0.012, 0.05), (s * 0.238, -0.012, 0.07)],
                    [0.022, 0.024, 0.026], claw_m, verts=8, per=2),
               ]
        palm = ell((s * 0.245, -0.012, 0.1), (0.047, 0.04, 0.045), claw_m, roll=-s * 12, segs=12, rings=7)
        ridge = [ell((s * 0.248, -0.036, 0.1), (0.032, 0.02, 0.03), shell, roll=-s * 12, segs=12, rings=6),
                 limb([(s * 0.222, -0.05, 0.08), (s * 0.24, -0.056, 0.1), (s * 0.262, -0.052, 0.122)],
                      [0.003, 0.003, 0.002], cglow, verts=5, per=3, caps=True)]
        knuck = [cone((s * 0.285, -0.012, 0.09 + 0.02 * i), (s * 0.305, -0.012, 0.095 + 0.024 * i), 0.008, spike,
                      verts=6) for i in range(2)]
        finger = limb([(s * 0.245, -0.012, 0.12), (s * 0.24, -0.012, 0.16), (s * 0.215, -0.012, 0.192),
                       (s * 0.175, -0.012, 0.203)], [0.03, 0.025, 0.016, 0.004], claw_m, verts=8, per=3, caps=True)
        teeth = [cone((s * (0.24 - 0.016 * i), -0.012, 0.155 + 0.012 * i),
                      (s * (0.228 - 0.016 * i), -0.012, 0.143 + 0.012 * i), 0.006, cglow, verts=6) for i in range(4)]
        rig.rigid("arm." + side, arm, palm, ridge, knuck, finger, teeth)
        jaw = limb([(s * 0.272, -0.012, 0.11), (s * 0.3, -0.012, 0.15), (s * 0.294, -0.012, 0.188),
                    (s * 0.278, -0.012, 0.2)], [0.024, 0.018, 0.009, 0.003], claw_m, verts=8, per=3, caps=True)
        jt = [cone((s * (0.285 - 0.002 * i), -0.012, 0.14 + 0.016 * i), (s * (0.272 - 0.002 * i), -0.012, 0.134 + 0.016 * i),
                   0.005, cglow, verts=6) for i in range(3)]
        rig.rigid("jaw." + side, jaw, jt)
    # six legs in two segments, knee balls, glowing claw tips
    for i, (hx, kx, fx, fz) in enumerate(LEGS):
        for s, side in ((1, "L"), (-1, "R")):
            n = "leg.%s%d" % (side, i + 1)
            th = limb([(s * hx, 0.0, -0.06), (s * (hx + kx) * 0.5, -0.004, -0.09), (s * kx, 0.0, -0.1)],
                      [0.018, 0.017, 0.014], leg_m, verts=6, per=2)
            kb = sphere(0.014, (s * kx, -0.002, -0.1), cglow, segs=6, rings=4)
            sh = limb([(s * kx, 0.0, -0.1), (s * (kx + fx) * 0.5 + s * 0.008, -0.004, (fz - 0.1) * 0.5),
                       (s * fx, 0.0, fz)], [0.013, 0.01, 0.004], leg_m, verts=6, per=3)
            tip = sphere(0.005, (s * fx, 0.0, fz), cglow, segs=6, rings=4)
            rig.rigid(n, th, kb)
            rig.rigid(n + "b", sh, tip)
    rig.build("crab")
    dims(rig.mesh)

    tips = ["ant.L2", "ant.R2"] + ["leg.%s%db" % (sd, i) for sd in "LR" for i in (1, 2, 3)] + ["jaw.L", "jaw.R"]
    a = merge({"arm.L": (0, -18, 0), "jaw.L": (0, -25, 0), "arm.R": (0, -4, 0), "jaw.R": (0, 5, 0),
               "@body": (0, 0, 0.0), "body": (0, 3, 0), "ant.L": (0, -6, 0), "ant.L2": (0, -12, 0),
               "ant.R": (0, 4, 0), "ant.R2": (0, 10, 0), "mand.L": (0, -12, 0), "mand.R": (0, 12, 0)},
              {"leg.L1": (0, -12, 0), "leg.L3": (0, -12, 0), "leg.R2": (0, 12, 0),
               "leg.L2": (0, 8, 0), "leg.R1": (0, -8, 0), "leg.R3": (0, -8, 0),
               "leg.L1b": (0, 10, 0), "leg.L3b": (0, 10, 0), "leg.R2b": (0, -10, 0)})
    b = merge({"arm.R": (0, 18, 0), "jaw.R": (0, 25, 0), "arm.L": (0, 4, 0), "jaw.L": (0, -5, 0),
               "@body": (0, 0, 0.012), "body": (0, -3, 0), "ant.R": (0, 6, 0), "ant.R2": (0, 12, 0),
               "ant.L": (0, -4, 0), "ant.L2": (0, -10, 0), "mand.L": (0, 4, 0), "mand.R": (0, -4, 0)},
              {"leg.R1": (0, 12, 0), "leg.R3": (0, 12, 0), "leg.L2": (0, -12, 0),
               "leg.R2": (0, -8, 0), "leg.L1": (0, 8, 0), "leg.L3": (0, 8, 0),
               "leg.R1b": (0, -10, 0), "leg.R3b": (0, -10, 0), "leg.L2b": (0, 10, 0)})
    chatter = {"mand.L": (0, 10, 0), "mand.R": (0, -10, 0)}
    march(rig, a, b, tips, extra={4: chatter, 19: chatter, 8: {"%body": (1.02, 1.02, 1.03)},
                                  23: {"%body": (1.02, 1.02, 1.03)}})
    hit(rig, merge({"%root": 1.2, "%eyes": 1.25}, mirror({"arm.L": (0, -35, 0), "jaw.L": (0, -40, 0),
                                                          "leg.L1": (0, 20, 0), "leg.L2": (0, 25, 0),
                                                          "leg.L3": (0, 30, 0), "ant.L": (0, -30, 0),
                                                          "ant.L2": (0, -30, 0), "mand.L": (0, -30, 0)})),
        {"%root": 0.15})
    rig.save("crab")


# ------------------------------------------------------------------ octopus (10 points)

def octopus():
    skin = mat("octopus_skin", (0.32, 0.95, 0.02), 0.25, coat=1.0)
    plate_m = mat("octopus_plate", (0.14, 0.62, 0.01), 0.4, coat=0.6)
    bel = mat("octopus_belly", (0.3, 0.7, 0.04), 0.4, coat=0.5)
    rim = mat("octopus_rim", (0.03, 0.08, 0.02), 0.25, 0.6, coat=0.8)
    brow_m = mat("octopus_brow", (0.04, 0.2, 0.02), 0.3, coat=0.9)
    leg_m = mat("octopus_leg", (0.22, 0.75, 0.02), 0.28, coat=0.9)
    memb = mat("octopus_membrane_glow", (0.05, 0.12, 0.0), 0.35, emit=1.5, emit_color=(0.55, 1.0, 0.05))
    eye_g = mat("octopus_eye_glow", (1.0, 0.06, 0.02), 0.2, emit=4.0)
    core = mat("octopus_core_glow", (1.0, 0.3, 0.0), 0.2, emit=3.0)
    suck = mat("octopus_sucker_glow", (0.85, 1.0, 0.4), 0.3, emit=2.5)
    EM = {"ball": rim, "iris": eye_g, "ring": core, "pupil": rim, "glint": suck, "lid": brow_m}

    # eight legs along the bottom rim, (hip x, knee x, knee z, foot x, foot z), left (x < 0) to right
    LEGS = [(-0.16, -0.215, -0.1, -0.25, -0.16), (-0.115, -0.16, -0.13, -0.195, -0.197),
            (-0.07, -0.092, -0.14, -0.105, -0.215), (-0.024, -0.03, -0.14, -0.034, -0.212)]
    LEGS += [(-hx, -kx, kz, -fx, fz) for hx, kx, kz, fx, fz in reversed(LEGS)]
    C = Vector((0, -0.158, -0.022))   # the chest porthole
    bones = {"root": ((0, 0, -0.05), (0, 0, 0.0), None),
             "body": ((0, 0, -0.08), (0, 0, 0.18), "root"),
             "brow": ((0, -0.12, 0.09), (0, -0.2, 0.09), "body"),
             "core": (tuple(C), tuple(C + Vector((0, -0.08, 0))), "body")}
    for i, (hx, kx, kz, fx, fz) in enumerate(LEGS):
        bones["leg%d" % i] = ((hx, 0, -0.07), (kx, 0, kz), "body")
        bones["leg%db" % i] = ((kx, 0, kz), (fx, 0, fz), "leg%d" % i)
    rig = TurnRig(bones, 0, fps=FPS)

    # the head: a bulky lobed dome; the cranium is armoured in ridged plates that glow lime at the seams, the face
    # and chest below are soft skin
    def lobes(u, v):
        return 1 + 0.03 * math.cos(8 * TAU * u) * smoothstep(0.62, 0.8, v)
    B = Lathe([(0.0, 0.218), (0.07, 0.208), (0.13, 0.178), (0.18, 0.128), (0.21, 0.062), (0.22, 0.0), (0.21, -0.05),
               (0.18, -0.085), (0.1, -0.1), (0.0, -0.1)], sx=1.0, sy=0.8, k=lobes)
    nv = 18
    split = B.v_at(0.05)
    head = B.mesh(36, nv, [bel, memb], name="dome", mat_fn=lambda i, j: 1 if (i + 0.5) / nv < split else 0)
    parts = [head]
    fold = lambda s, t: 0.005 * math.sin(math.pi * s) * (1 - t) + 0.003 * math.exp(-((s - 0.5) / 0.08) ** 2)
    parts.append(plate(B, 0, 1, 0.218, 0.19, skin, nu=24, nv=4, thick=0.01, rim=(0, 0, 0, 0.35)))
    for k in range(8):
        u0 = (k - 0.5) / 8 + 0.006
        parts.append(plate(B, u0, u0 + 0.125 - 0.012, 0.184, 0.1, skin if k % 2 == 0 else plate_m, nu=8, nv=6,
                           thick=0.011, crown=fold))
    for k in range(12):
        u0 = (k - 0.5) / 12 + 0.005
        if k in (0, 1, 2, 10, 11):
            continue   # the brow sits there
        parts.append(plate(B, u0, u0 + 1 / 12 - 0.01, 0.093, 0.05, plate_m if k % 2 == 0 else skin, nu=6, nv=4,
                           thick=0.008))
    # glowing freckles on the crown plates, gill slits on the cheeks, veins round the chest
    for k in (0, 1, 2, 6, 7):
        p, _ = B.at((k + 0.25) / 8, 0.15 - 0.02 * (k % 2), 0.013)
        parts.append(sphere(0.008, p, suck, segs=6, rings=4))
    for s in (-1, 1):
        for g in range(3):
            u = 0.13 + 0.03 * g
            parts.append(vein(B, [(u if s > 0 else 1 - u, 0.035), ((u + 0.006) if s > 0 else 1 - u - 0.006, 0.0),
                                  (u if s > 0 else 1 - u, -0.035)], 0.005, memb, lift=0.0, taper=0.3, verts=5, per=2,
                              caps=False))
            parts.append(vein(B, [((u - 0.012) if s > 0 else 1 - u + 0.012, 0.03),
                                  ((u - 0.006) if s > 0 else 1 - u + 0.006, 0.0),
                                  ((u - 0.012) if s > 0 else 1 - u + 0.012, -0.03)], 0.004, brow_m, lift=0.003,
                              taper=0.3, verts=5, per=2))
        parts.append(vein(B, [(s * 0.05 % 1, -0.075), (s * 0.075 % 1, -0.04), (s * 0.1 % 1, -0.005),
                              (s * 0.11 % 1, 0.03)], 0.0032, memb, lift=0.002))
    # the chest porthole: a ribbed rim with inward fangs round a hot, caged core
    ringo = ring(0.058, 0.016, C + Vector((0, -0.012, 0)), (0, -1, 0), rim, verts=28, minor=6)
    parts.append(ringo)
    for k in range(12):
        a = TAU * k / 12
        d = Vector((math.cos(a), 0, math.sin(a)))
        parts.append(ell(C + d * 0.058 + Vector((0, -0.026, 0)), (0.007, 0.006, 0.007), bel, segs=6, rings=3))
        if k % 2 == 0:
            parts.append(cone(C + d * 0.05 + Vector((0, -0.02, 0)), C + d * 0.033 + Vector((0, -0.02, 0)), 0.007, bel,
                              verts=6))
    rig.rigid("body", parts)
    cr = [sphere(0.046, C + Vector((0, 0.01, 0)), core, segs=16, rings=10),
          sphere(0.02, C + Vector((0, -0.03, 0)), suck, segs=10, rings=6)]
    for k in range(3):
        a = math.radians(-50 + 50 * k)
        d = Vector((math.cos(a + math.pi / 2), 0, math.sin(a + math.pi / 2)))
        cr.append(rod(C - d * 0.047 + Vector((0, -0.03, 0)), C + d * 0.047 + Vector((0, -0.03, 0)), 0.0035, rim,
                      verts=6))
    rig.rigid("core", cr)
    # the eyes: horizontal slit pupils under heavy angry lids, a ridged brow over each
    br = []
    for s in (-1, 1):
        ball, up, low = eye((s * 0.068, -0.152, 0.074), 0.032, EM, look=(s * 0.15, -1, 0.05), iris=50,
                            slit=(0.55, 0.13), lid_up=74, lid_low=56, lid_tilt=-s * 24, segs=16)
        br += ball + up + low
        line = [(s * 0.02, -0.19, 0.098), (s * 0.06, -0.188, 0.118), (s * 0.1, -0.175, 0.112),
                (s * 0.125, -0.155, 0.095)]
        br.append(limb(line, [0.012, 0.016, 0.014, 0.008], brow_m, verts=8, per=3, caps=True))
        br.append(limb([Vector(p) + Vector((0, -0.012, -0.012)) for p in line[:3]], [0.003, 0.003, 0.002], suck,
                       verts=5, per=3, caps=True))
    rig.rigid("brow", br)
    # legs: thick jointed tentacles curling at the tip, glowing suckers down the front, a glowing tip
    for i, (hx, kx, kz, fx, fz) in enumerate(LEGS):
        s = 1 if hx > 0 else -1
        P = [(hx, -0.005, -0.06), (kx, -0.01, kz), (fx, -0.01, fz), (fx + s * 0.028, -0.02, fz + 0.02)]
        names = ["leg%d" % i, "leg%db" % i]
        t = tentacle(P, [0.042, 0.03, 0.017, 0.008], [leg_m, brow_m], 4, verts=8, per=4, pinch=0.1, band=0.1,
                     rings=13)
        path = resample(smooth_path(P, 4), 40)
        su = []
        for j, f in enumerate((0.36, 0.62)):
            q, d = along(path, f)
            rr = 0.036 * (1 - 0.75 * f)
            su.append(sphere(0.0065 - 0.0015 * j, q + Vector((0, -rr, 0)), suck, segs=6, rings=4, scale=(1, 0.6, 1)))
        rig.smooth(names, t, su, power=6)
        rig.rigid(names[1], sphere(0.009, P[-1], suck, segs=6, rings=4))
    rig.build("octopus")
    dims(rig.mesh)

    def legs(sign):
        out = {}
        for i in range(8):
            w = sign * (14 if i % 2 == 0 else -10) * (1 if i < 4 else -1)
            out["leg%d" % i] = (0, w, 0)
            out["leg%db" % i] = (0, w * 1.2, 0)
        return out
    tips = ["leg%db" % i for i in range(8)]
    a = merge({"%body": (1.03, 1.0, 0.96), "@body": (0, 0, -0.005), "brow": (0, 0, 0)}, legs(1))
    b = merge({"%body": (0.97, 1.0, 1.04), "@body": (0, 0, 0.01), "%brow": (1.0, 1.0, 0.85)}, legs(-1))
    pulse = {"%core": 1.12}
    march(rig, a, b, tips, extra={4: pulse, 8: {"%core": 1.05}, 19: pulse, 23: {"%core": 1.05}})
    hit(rig, merge({"%root": 1.2, "%brow": (1.2, 1, 1.4), "%core": 1.4},
                   {"leg%d" % i: (0, (35 if i < 4 else -35), 0) for i in range(8)},
                   {"leg%db" % i: (0, (30 if i < 4 else -30), 0) for i in range(8)}), {"%root": 0.15})
    rig.save("octopus")


# ------------------------------------------------------------------ cannon

def helix(z0, z1, r, turns, thick, material, verts=6, per_turn=16, phase=0.0):
    n = max(4, int(turns * per_turn)) + 1
    pts = [(r * math.cos(phase + TAU * turns * i / (n - 1)), r * math.sin(phase + TAU * turns * i / (n - 1)),
            z0 + (z1 - z0) * i / (n - 1)) for i in range(n)]
    return tube(pts, [thick] * n, material, verts=verts, caps=True, name="helix")


def cannon():
    hull = mat("cannon_hull", (0.88, 0.9, 0.95), 0.2, 0.1, coat=1.0)
    panel = mat("cannon_panel", (0.62, 0.66, 0.74), 0.45, 0.3, coat=0.4)
    trim = mat("cannon_trim", (0.45, 0.5, 0.58), 0.25, 0.9)
    dark = mat("cannon_dark", (0.04, 0.05, 0.08), 0.3, 0.6, coat=0.6)
    canopy = mat("cannon_canopy_glow", (0.1, 0.7, 1.0), 0.05, coat=1.0, emit=1.8)
    coil = mat("cannon_coil_glow", (0.2, 0.95, 1.0), 0.2, emit=3.5)
    hover = mat("cannon_hover_glow", (0.2, 0.6, 1.0), 0.3, emit=3.0)
    parts = []
    # the hull: a low angular wedge on a dark keel, split into panels (dark seams between), a cheek plate each side
    outline = [(-0.25, -0.075), (0.25, -0.075), (0.3, -0.035), (0.23, 0.035), (0.1, 0.06), (-0.1, 0.06),
               (-0.23, 0.035), (-0.3, -0.035)]
    parts.append(K.prism(outline, 0.2, (0, 0, 0), dark, bevel=0.01, segs=2))
    parts.append(K.prism([(-0.22, -0.11), (0.22, -0.11), (0.26, -0.07), (-0.26, -0.07)], 0.2, (0, 0, 0), dark,
                         bevel=0.012, segs=2))
    front = [((-0.245, -0.07), (-0.07, -0.07), (-0.07, 0.055), (-0.1, 0.055), (-0.225, 0.032), (-0.292, -0.035)),
             ((-0.06, -0.07), (0.06, -0.07), (0.06, 0.055), (-0.06, 0.055)),
             ((0.07, -0.07), (0.245, -0.07), (0.292, -0.035), (0.225, 0.032), (0.1, 0.055), (0.07, 0.055))]
    for k, poly in enumerate(front):   # three front panels and matching back ones, a gap between them
        for y, d in ((-0.105, 0.03), (0.105, 0.03)):
            parts.append(K.prism(list(poly), d, (0, y - (0.004 if y < 0 else -0.004), 0), hull if k != 1 else panel,
                                 bevel=0.008, segs=2))
    parts.append(K.prism([(-0.23, 0.03), (0.23, 0.03), (0.1, 0.064), (-0.1, 0.064)], 0.2, (0, 0, 0), hull,
                         bevel=0.01, segs=2))   # the deck
    for k in range(2):   # two glowing chevrons on the middle panel
        z = -0.045 + 0.028 * k
        parts.append(limb([(-0.032, -0.126, z), (0, -0.126, z + 0.02), (0.032, -0.126, z)], [0.0045] * 3, coil,
                          verts=5, per=1, caps=True))
    # vents on the cheeks: dark slots with steel slats and a blue glow behind
    for sgn in (-1, 1):
        parts.append(K.prism([(sgn * 0.14, -0.055), (sgn * 0.215, -0.055), (sgn * 0.215, -0.02), (sgn * 0.14, -0.02)][::sgn],
                             0.01, (0, -0.121, 0), hover, bevel=0.002, segs=1))
        for i in range(4):
            x = sgn * (0.15 + 0.018 * i)
            parts.append(K.box((0.006, 0.012, 0.04), (x, -0.126, -0.0375), trim, bevel=0.002, segs=1))
        # a glowing stripe along the front chamfer, a row of rivets
        parts.append(limb([(sgn * 0.285, -0.123, -0.03), (sgn * 0.225, -0.123, 0.024), (sgn * 0.11, -0.123, 0.047)],
                          [0.006, 0.006, 0.005], coil, verts=6, per=3, caps=True))
        for i in range(3):
            parts.append(sphere(0.005, (sgn * (0.09 + 0.04 * i), -0.123, -0.063), trim, segs=6, rings=4))
    # hover nacelles at both ends: steel capsules, an intake fan facing out, a thruster bell glowing underneath
    for sgn in (-1, 1):
        parts.append(limb([(sgn * 0.24, 0, -0.07), (sgn * 0.3, 0, -0.07), (sgn * 0.34, 0, -0.065)],
                          [0.055, 0.056, 0.047], trim, verts=16, per=2, caps=True))
        parts.append(ring(0.057, 0.006, (sgn * 0.27, 0, -0.07), (1, 0, 0), dark, verts=16, minor=4))
        parts.append(ring(0.036, 0.009, (sgn * 0.345, 0, -0.065), (1, 0, 0), coil, verts=16, minor=6))
        parts.append(orient(K.cyl(0.03, 0.01, (0, 0, 0), dark, verts=16), (0, 0, 1), (1, 0, 0),
                            (sgn * 0.346, 0, -0.065)))
        for b in range(6):   # fan blades
            a = TAU * b / 6
            d = Vector((0, math.cos(a), math.sin(a)))
            parts.append(rod(Vector((sgn * 0.35, 0, -0.065)) + d * 0.006, Vector((sgn * 0.35, 0, -0.065)) + d * 0.027,
                             0.004, trim, verts=4))
        parts.append(sphere(0.008, (sgn * 0.352, 0, -0.065), coil, segs=8, rings=5))
        parts.append(K.cyl(0.036, 0.03, (sgn * 0.3, 0, -0.118), dark, r2=0.026, verts=16))   # the bell
        parts.append(ell((sgn * 0.3, 0, -0.132), (0.034, 0.034, 0.008), hover, segs=16, rings=5))
        parts.append(K.prism([(sgn * 0.26, -0.03), (sgn * 0.33, -0.03), (sgn * 0.3, 0.0)][::sgn], 0.008,
                             (0, 0.0, -0.01), trim, bevel=0.003, segs=1))   # a small top fin
    parts.append(ell((0, 0, -0.113), (0.17, 0.08, 0.01), hover, segs=24, rings=5))
    # the turret: a dome, a canopy with a steel frame looking at the camera, a bolted collar
    parts.append(ell((0, 0.0, 0.065), (0.14, 0.11, 0.075), hull, segs=28, rings=12))
    parts.append(ell((0, -0.075, 0.07), (0.08, 0.04, 0.042), canopy, segs=20, rings=10))
    for x in (-0.03, 0.03):
        parts.append(limb([(x * 1.4, -0.112, 0.05), (x, -0.119, 0.075), (x * 0.6, -0.1, 0.105)], [0.004] * 3, trim,
                          verts=5, per=3))
    parts.append(limb([(-0.075, -0.09, 0.065), (0, -0.121, 0.072), (0.075, -0.09, 0.065)], [0.004] * 3, trim,
                      verts=5, per=4))
    parts.append(torus(0.1, 0.013, (0, 0, 0.06), trim, verts=32, minor=6, scale=(1.35, 1.05, 1.0)))
    for k in range(10):
        a = TAU * (k + 0.5) / 10
        parts.append(sphere(0.006, (0.135 * math.cos(a), 0.105 * math.sin(a), 0.066), dark, segs=6, rings=4))
    # the barrel: a dark mantlet, heat-sink fins, a glowing charging coil wound round a steel sleeve, a muzzle
    # with three prongs round the emitter
    parts.append(rod((0, 0, 0.1), (0, 0, 0.155), 0.05, dark, r2=0.042, verts=20))
    parts.append(rod((0, 0, 0.15), (0, 0, 0.25), 0.026, trim, r2=0.024, verts=16))
    for i in range(3):
        parts.append(K.cyl(0.042 - 0.003 * i, 0.005, (0, 0, 0.128 + 0.012 * i), dark, verts=18))
    parts.append(helix(0.165, 0.228, 0.033, 3.5, 0.0065, coil, verts=6))
    for z in (0.162, 0.232):
        parts.append(torus(0.035, 0.007, (0, 0, z), trim, verts=18, minor=5))
    parts.append(torus(0.032, 0.011, (0, 0, 0.258), trim, verts=18, minor=6))
    for k in range(3):
        a = TAU * k / 3 + math.pi / 2
        c, s = math.cos(a), math.sin(a)
        parts.append(rod((0.03 * c, 0.03 * s, 0.25), (0.024 * c, 0.024 * s, 0.278), 0.0055, dark, r2=0.003, verts=5))
    parts.append(sphere(0.022, (0, 0, 0.262), coil, segs=12, rings=8))
    # fins behind the turret, an aerial with a glowing tip
    for sgn in (-1, 1):
        parts.append(K.prism([(sgn * 0.12, 0.04), (sgn * 0.2, 0.035), (sgn * 0.14, 0.11)][::sgn], 0.012,
                             (0, 0.07, 0), trim, bevel=0.004, segs=1))
        parts.append(limb([(sgn * 0.13, 0.07, 0.05), (sgn * 0.19, 0.07, 0.04)], [0.003, 0.002], coil, verts=4, per=1))
    parts.append(rod((-0.09, 0.05, 0.1), (-0.11, 0.05, 0.19), 0.003, trim, verts=5))
    parts.append(sphere(0.007, (-0.11, 0.05, 0.19), coil, segs=8, rings=5))
    o = join(parts, "cannon")
    o.data.transform(Matrix.Scale(0.91, 4))   # built a little large: 0.70 across the nacelle rings
    dims(o)
    export(o, "cannon")


# ------------------------------------------------------------------ mothership

def mothership():
    hullm = mat("mother_hull", (0.55, 0.04, 0.09), 0.25, 0.5, coat=1.0)
    panel = mat("mother_panel", (0.32, 0.02, 0.06), 0.4, 0.6, coat=0.6)
    trim = mat("mother_trim", (0.9, 0.7, 0.3), 0.25, 0.95)
    dark = mat("mother_dark", (0.03, 0.01, 0.02), 0.3, 0.6)
    dome = mat("mother_dome", (0.1, 0.04, 0.16), 0.02, 0.1, coat=1.0, alpha=0.6)
    pilot = mat("mother_pilot_glow", (1.0, 0.3, 0.85), 0.3, emit=3.0)
    peye = mat("mother_pilot_eye", (0.02, 0, 0.03), 0.2)
    beam = mat("mother_beam_glow", (1.0, 0.2, 0.5), 0.3, emit=3.0)
    band = mat("mother_band_glow", (1.0, 0.45, 0.1), 0.3, emit=2.5)
    win = mat("mother_window_glow", (1.0, 0.75, 0.35), 0.3, emit=3.0)
    la = mat("mother_lamp_a_glow", (1.0, 0.08, 0.12), 0.2, emit=4.0)
    lb = mat("mother_lamp_b_glow", (1.0, 0.6, 0.05), 0.2, emit=4.0)
    # the hull: a stepped saucer; the dark body shows between the plates of the upper and lower decks
    H = Lathe([(0.0, 0.062), (0.2, 0.054), (0.3, 0.036), (0.37, 0.02), (0.45, -0.005), (0.44, -0.03), (0.33, -0.062),
               (0.16, -0.085), (0.0, -0.09)], per=8)
    parts = [H.mesh(64, 16, dark, name="hull")]
    for k in range(16):   # upper deck: two rings of plates, staggered
        u0 = k / 16 + 0.003
        parts.append(plate(H, u0, u0 + 1 / 16 - 0.006, 0.056, 0.036, hullm if k % 2 else panel, nu=5, nv=3,
                           thick=0.006))
        u1 = (k + 0.5) / 16 + 0.003
        parts.append(plate(H, u1, u1 + 1 / 16 - 0.006, 0.032, 0.0, hullm, nu=5, nv=3, thick=0.006))
    for k in range(12):   # lower deck
        u0 = k / 12 + 0.004
        parts.append(plate(H, u0, u0 + 1 / 12 - 0.008, -0.03, -0.075, panel if k % 2 else hullm, nu=5, nv=3,
                           thick=0.005))
    parts.append(torus(0.445, 0.012, (0, 0, -0.012), trim, verts=64, minor=6))
    parts.append(torus(0.4, 0.005, (0, 0, 0.012), band, verts=64, minor=4))
    parts.append(torus(0.19, 0.015, (0, 0, 0.055), trim, verts=48, minor=6))
    # a ring of windows round the upper deck, each in a steel rim
    for k in range(16):
        a = TAU * (k + 0.5) / 16
        p, n = H.at((k + 0.5) / 16 + 0.25, 0.034, 0.004)
        parts.append(orient(ell((0, 0, 0), (0.014, 0.014, 0.004), win, segs=10, rings=4), (0, 0, 1), n, p))
        parts.append(ring(0.015, 0.003, p, n, trim, verts=10, minor=3))
    # the dome with the pilot inside: a glowing hooded blob with two dark eyes and little arms on the controls
    parts.append(lathe_r([(0.0, 0.215), (0.07, 0.205), (0.12, 0.17), (0.16, 0.115), (0.18, 0.055)], dome, segs=40,
                         name="dome", smooth=70))
    for k in range(6):   # the dome's frame
        a = TAU * k / 6
        c, s = math.cos(a), math.sin(a)
        parts.append(limb([(0.18 * c, 0.18 * s, 0.056), (0.16 * c, 0.16 * s, 0.116), (0.12 * c, 0.12 * s, 0.171),
                           (0.07 * c, 0.07 * s, 0.206)], [0.004] * 4, trim, verts=5, per=3))
    parts.append(ell((0, 0, 0.115), (0.06, 0.05, 0.06), pilot, segs=16, rings=10))
    parts.append(ell((0, 0, 0.16), (0.035, 0.03, 0.03), pilot, segs=12, rings=6))
    for s in (-1, 1):
        parts.append(ell((s * 0.022, -0.05, 0.125), (0.014, 0.008, 0.02), peye, roll=s * 20, segs=10, rings=6))
        parts.append(limb([(s * 0.04, -0.03, 0.09), (s * 0.06, -0.06, 0.075), (s * 0.05, -0.085, 0.07)],
                          [0.01, 0.008, 0.005], pilot, verts=6, per=3, caps=True))
    parts.append(K.box((0.12, 0.03, 0.02), (0, -0.1, 0.07), dark, bevel=0.005, segs=1))
    for i in range(3):
        parts.append(sphere(0.006, (-0.03 + 0.03 * i, -0.116, 0.074), (la, lb, win)[i], segs=6, rings=4))
    parts.append(sphere(0.012, (0, 0, 0.23), trim, segs=8, rings=6))
    parts.append(rod((0, 0, 0.21), (0, 0, 0.245), 0.005, trim, verts=6))
    # underneath: a stepped emitter with vanes round a ridged tractor lens, three landing pods
    for r, z, t in ((0.15, -0.084, 0.01), (0.125, -0.089, 0.02)):
        parts.append(torus(r, t, (0, 0, z), trim if r > 0.13 else beam, verts=40, minor=6))
    for k in range(12):
        a = TAU * k / 12
        c, s = math.cos(a), math.sin(a)
        parts.append(K.prism([(0.075, 0.0), (0.14, 0.0), (0.13, -0.022), (0.08, -0.018)], 0.008, (0, 0, -0.085),
                             dark, bevel=0.002, segs=1))
        parts[-1].data.transform(Matrix.Rotation(a, 4, "Z"))
    for k, r in enumerate((0.075, 0.058, 0.04, 0.022)):
        parts.append(torus(r, 0.005, (0, 0, -0.1 - 0.003 * k), beam if k % 2 else trim, verts=32, minor=4))
    parts.append(ell((0, 0, -0.1), (0.07, 0.07, 0.016), beam, segs=24, rings=6))
    for k in range(3):
        a = TAU * k / 3 + math.pi / 6
        c, s = math.cos(a), math.sin(a)
        parts.append(ell((0.27 * c, 0.27 * s, -0.064), (0.04, 0.04, 0.018), panel, segs=12, rings=6))
        parts.append(sphere(0.01, (0.27 * c, 0.27 * s, -0.08), band, segs=8, rings=5))
    hull = join(parts, "mothership")
    lamps = []
    for k in range(14):
        a = TAU * k / 14
        c, s = math.cos(a), math.sin(a)
        lamps.append(sphere(0.024, (0.458 * c, 0.458 * s, -0.012), la if k % 2 == 0 else lb, segs=12, rings=8))
        lamps.append(orient(K.cyl(0.02, 0.012, (0, 0, 0), trim, r2=0.026, verts=12), (0, 0, 1), (c, s, 0),
                            (0.44 * c, 0.44 * s, -0.012)))
    lights = join(lamps, "lights")
    dims(hull)
    export(hull, "mothership", children=[(lights, hull)])


# ------------------------------------------------------------------ bombs and the shot

def bomb_rolling():
    g = mat("bomb_rolling_glow", (1.0, 0.3, 0.02), 0.3, emit=1.8)
    core = mat("bomb_rolling_core_glow", (1.0, 0.8, 0.4), 0.3, emit=4.0)
    shell = mat("bomb_rolling_shell", (0.2, 0.06, 0.02), 0.3, 0.8)
    parts = [rod((0, 0, 0.14), (0, 0, -0.16), 0.022, core, r2=0.006, verts=12)]
    for ph in (0, TAU / 3, 2 * TAU / 3):   # three twisted flutes round the hot core
        pts, rad = [], []
        for i in range(43):
            t = i / 42
            z = 0.15 - 0.31 * t
            r = 0.052 * (1 - 0.65 * t)
            a = ph + t * 4.5 * math.pi
            pts.append((r * math.cos(a), r * math.sin(a), z))
            rad.append(0.017 * (1 - 0.6 * t))
        parts.append(tube(pts, rad, g, verts=8, caps=True, name="helix"))
    for z in (0.12, 0.06, 0.0, -0.06):   # spinning bands
        parts.append(torus(0.05 * (1 - 0.65 * (0.15 - z) / 0.31), 0.005, (0, 0, z), shell, verts=16, minor=4))
    parts.append(sphere(0.036, (0, 0, 0.15), shell, segs=14, rings=8))
    parts.append(torus(0.036, 0.007, (0, 0, 0.15), g, verts=16, minor=5))
    parts.append(sphere(0.02, (0, 0, 0.175), core, segs=10, rings=6))
    o = join(parts, "bomb_rolling")
    dims(o)
    export(o, "bomb_rolling")


def bomb_plunger():
    shell = mat("bomb_plunger_shell", (0.2, 0.05, 0.06), 0.25, 0.8, coat=0.8)
    trim = mat("bomb_plunger_trim", (0.55, 0.5, 0.5), 0.3, 0.9)
    g = mat("bomb_plunger_glow", (1.0, 0.05, 0.1), 0.3, emit=3.0)
    parts = [lathe_r([(0.0, 0.14), (0.03, 0.135), (0.04, 0.1), (0.042, 0.0), (0.035, -0.07), (0.018, -0.13),
                      (0.0, -0.175)], shell, segs=20, name="dart", smooth=50)]
    parts.append(torus(0.043, 0.01, (0, 0, 0.03), g, verts=20, minor=6))
    parts.append(torus(0.038, 0.008, (0, 0, -0.03), g, verts=20, minor=6))
    parts.append(torus(0.043, 0.005, (0, 0, 0.075), trim, verts=20, minor=4))
    parts.append(torus(0.03, 0.005, (0, 0, -0.09), trim, verts=16, minor=4))
    for k in range(6):   # grooves down the nose
        a = TAU * k / 6
        c, s = math.cos(a), math.sin(a)
        parts.append(limb([(0.037 * c, 0.037 * s, -0.04), (0.03 * c, 0.03 * s, -0.09), (0.018 * c, 0.018 * s, -0.128)],
                          [0.003, 0.0025, 0.002], g, verts=4, per=2, caps=True))
    parts.append(cone((0, 0, -0.12), (0, 0, -0.178), 0.014, g, verts=10))
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        f = K.prism([(0.0, 0.0), (0.035, 0.03), (0.035, 0.1), (0.0, 0.07)], 0.01, (0, 0, 0), shell, bevel=0.003)
        f.data.transform(Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0.035, 0, 0.07)))
        parts.append(f)
        e = limb([(0.07, 0, 0.1), (0.07, 0, 0.17)], [0.004, 0.004], g, verts=5, per=1, caps=True)
        e.data.transform(Matrix.Rotation(a, 4, "Z"))
        parts.append(e)
        parts.append(sphere(0.009, (0.072 * c, 0.072 * s, 0.17), g, segs=8, rings=6))
    parts.append(ell((0, 0, 0.14), (0.028, 0.028, 0.012), g, segs=12, rings=5))
    o = join(parts, "bomb_plunger")
    dims(o)
    export(o, "bomb_plunger")


def bomb_squiggly():
    g = mat("bomb_squiggly_glow", (0.35, 1.0, 0.03), 0.3, emit=1.8)
    core = mat("bomb_squiggly_core_glow", (0.85, 1.0, 0.5), 0.3, emit=4.0)
    pts = [(0.05 * (1 if i % 2 else -1) * (1 - 0.3 * i / 6), 0, 0.15 - 0.3 * i / 6) for i in range(7)]
    parts = [limb(pts, [0.02, 0.02, 0.018, 0.016, 0.014, 0.012, 0.01], g, verts=10, per=5, caps=True),
             limb(pts, [0.008, 0.008, 0.007, 0.006, 0.005, 0.004, 0.003], core, verts=6, per=5, caps=True)]
    parts[1].data.transform(Matrix.Translation((0, -0.014, 0)))
    for i, p in enumerate(pts):
        parts.append(sphere(0.03 - 0.0025 * i, p, core if i % 2 == 0 else g, segs=14, rings=8))
        for k in range(3):   # sparks orbiting each bead
            a = TAU * k / 3 + i
            q = Vector(p) + Vector((math.cos(a), math.sin(a) * 0.6, math.sin(a) * 0.5)) * (0.04 - 0.003 * i)
            parts.append(sphere(0.005, q, core, segs=6, rings=4))
    o = join(parts, "bomb_squiggly")
    dims(o)
    export(o, "bomb_squiggly")


def shot():
    core = mat("shot_core_glow", (0.9, 1.0, 1.0), 0.2, emit=10.0)
    g = mat("shot_glow", (0.2, 0.9, 1.0), 0.2, emit=5.0, alpha=0.7)
    parts = [tube([(0, 0, 0.14), (0, 0, 0.1), (0, 0, -0.05), (0, 0, -0.14)], [0.018, 0.016, 0.01, 0.003], core,
                  verts=12, caps=True, name="core"),
             tube([(0, 0, 0.13), (0, 0, 0.1), (0, 0, -0.05), (0, 0, -0.16)], [0.035, 0.03, 0.018, 0.004], g,
                  verts=14, caps=True, name="sheath")]
    for k, z in enumerate((0.07, 0.01, -0.05)):   # pulse rings trailing down the bolt
        parts.append(torus(0.03 - 0.006 * k, 0.004, (0, 0, z), core, verts=14, minor=4))
    for k in range(4):   # a flared tip: four short spikes of light
        a = TAU * k / 4 + math.pi / 4
        parts.append(cone((0, 0, 0.13), (0.02 * math.cos(a), 0.02 * math.sin(a), 0.165), 0.006, core, verts=5))
    o = join(parts, "shot")
    dims(o)
    export(o, "shot")


JOBS = {"squid": squid, "crab": crab, "octopus": octopus, "cannon": cannon, "mothership": mothership,
        "bomb_rolling": bomb_rolling, "bomb_plunger": bomb_plunger, "bomb_squiggly": bomb_squiggly, "shot": shot}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = 30
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
