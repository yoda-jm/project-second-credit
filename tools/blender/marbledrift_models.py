"""Marble Drift (game 27) models: the steelie (the enemy marble), the hopper (a patrolling spring creature), the goal
arch, the checkpoint beacon, the support pylon under the floating course, a glass shard for the shatter effect and a
pennant flag. Original designs (our own shapes, nothing from any arcade marble game): a dark polished steel ball with
engraved bands and a red slit that glows like a narrowed eye; a coral spring-creature on a coiled copper spring with
big eyes and a feeler; a slim elliptical gate of white ceramic and brass with a chequered banner and lamps; a crystal
beacon on a fluted post; a tapering ceramic-and-steel pylon with light seams.
Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/marbledrift_models.py -- godot/games/marbledrift/art/models [name ...]
     (TRIS=1 also prints the triangles per material)
Helpers come from blastyard_models.py (mat, sphere, torus, rod, tube, join, export, ...), prism_models.py (animate,
export_anim, empty), hopline_models.py (ell) and mossfolk_models.py (lathe_r).

Units: 1 unit = one course cell; the marble's radius is 0.3, walls rise 1.5. Built in Blender facing -Y with Z up,
which exports as facing Godot +Z with Godot +Y up. Emissive materials all have "glow" in their names.

steelie.glb   mesh "steelie": a sphere of radius 0.3, origin at its centre, about 24k triangles. Dark polished steel
              (steelie_steel) with engraved bands (steelie_groove: the equator, two tropics and two polar rings); the
              equator groove opens at the front (Godot +Z) into an almond socket holding a red eye (steelie_eye_glow)
              with a hot slit pupil (steelie_pupil_glow), and carries a faint red seam round the back
              (steelie_seam_glow). Spin it as it rolls.
hopper.glb    root empty "hopper" (origin at its feet, facing Godot +Z; 0.63 tall to the head, 0.73 with its feeler,
              0.52 wide across the fin ears, the foot pad 0.27 across) with four
              animated child meshes: "foot" (a rubber pad: hopper_foot, hopper_trim), "spring" (a coiled copper
              spring: hopper_spring), "head" (a coral round head, hopper_skin, hopper_belly; big eyes hopper_eye,
              hopper_pupil, hopper_glint_glow; cheeks hopper_cheek; fin ears; a collar hopper_trim) and "feeler" (a
              curled feeler with a glowing tip, hopper_bulb_glow).
              Animation "hop" (1.0 s, 30 fps, set it to loop in the game): it lands at 0.0 s, squashes (to 0.12 s),
              springs up (leaves the ground at 0.24 s), flies to a 0.32 apex at 0.62 s and lands again at 1.0 s,
              the spring stretching and squashing, the head squashing the other way, the feeler lagging.
goal_arch.glb mesh "goal_arch": 3.0 wide, 2.5 tall, 0.5 deep, origin at the base centre, facing Godot +Z. Two
              plinths and an arch of white ceramic (goal_body: straight legs, a flattened elliptical top) with brass
              edges (goal_trim) and blue light seams (goal_glow), a row of warm lamps along the inner edge
              (goal_lamp_glow) and a diamond crest in a ring at the top (goal_crest_glow, up to y = 2.63). The opening
              is 2.14 wide, 1.5 high under the banner. Child mesh "banner" (origin at the middle of its top edge,
              y = 1.9, on the gate's plane): a chequered cloth 1.8 x 0.4 in 10 x 2 squares (goal_check_a,
              goal_check_b, two-sided) on a brass bar (goal_trim), subdivided 40 x 8 so the view may wave it.
beacon.glb    mesh "beacon": 1.2 tall, origin at the base centre: a hexagonal foot, a fluted post (beacon_body,
              beacon_trim) and a three-pronged claw holding a long crystal and a ring round the claw (beacon_glow:
              the view lights it up when passed; it is dimly emissive in the file).
pylon.glb     mesh "pylon": origin at the TOP centre (the course's underside), extending 12 units down Godot -Y; a
              1.0 x 1.0 head plate tapering through octagonal sections to a point; pale ceramic (pylon_body), steel
              collars (pylon_trim), a halo ring 1.1 across just below the head, light seams down four faces and a
              beacon near the tip (pylon_glow). About 2k tris.
shard.glb     mesh "shard": a curved triangular piece of glass shell, about 0.12 across, 0.01 thick, origin at its
              centre (shard_glass, alpha 0.45; the view may recolour it to the marble's tint).
flag.glb      mesh "flag": 1.0 tall, origin at the base centre: a steel pole (flag_pole) on a little foot with a
              glowing knob (flag_tip_glow). Child mesh "pennant" (origin on the pole at y = 0.83, the middle of its
              hoist): a triangular pennant 0.24 high and 0.42 long towards Godot +X, two-sided, subdivided 10 x 6 for
              waving (flag_cloth, near white so the view can tint it, with a darker hem flag_hem).
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, torus, rod, tube, join, export, reset
from prism_models import animate, export_anim, empty
from hopline_models import ell
from mossfolk_models import lathe_r

TAU = 2 * math.pi
FPS = 30


def link(me, name):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def mesh_from(name, verts, faces, mats, face_mat=None, smooth=60):
    """A mesh from raw verts and faces, with a material index per face."""
    bm = bmesh.new()
    V = [bm.verts.new(v) for v in verts]
    for i, f in enumerate(faces):
        try:
            face = bm.faces.new([V[k] for k in f])
        except ValueError:
            continue
        face.material_index = face_mat[i] if face_mat else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    keep = [p.material_index for p in me.polygons]
    o = K.finish(link(me, name), mats[0], smooth=smooth)   # (finish clears the slots, and with them the indices)
    for m in mats[1:]:
        o.data.materials.append(m)
    for p, k in zip(o.data.polygons, keep):
        p.material_index = k
    return o


def dims(o):
    objs = [o] + [c for c in o.children_recursive]
    bb = [c.matrix_world @ v.co for c in objs if c.type == "MESH" for v in c.data.vertices]
    lo = Vector([min(v[i] for v in bb) for i in range(3)])
    hi = Vector([max(v[i] for v in bb) for i in range(3)])
    print("  %s: width %.3f  depth %.3f  height %.3f  (x %.3f .. %.3f, z %.3f .. %.3f)  %d tris" % (
        o.name, hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo.x, hi.x, lo.z, hi.z,
        sum(K.tris(c) for c in objs if c.type == "MESH")))
    if os.environ.get("TRIS"):
        per = {}
        for c in objs:
            if c.type != "MESH":
                continue
            for p in c.data.polygons:
                n = c.data.materials[p.material_index].name
                per[n] = per.get(n, 0) + len(p.vertices) - 2
        print("   ", sorted(per.items(), key=lambda x: -x[1]))


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ the steelie

def steelie():
    steel = mat("steelie_steel", (0.16, 0.17, 0.19), 0.17, 1.0, coat=0.5)
    groove = mat("steelie_groove", (0.025, 0.025, 0.03), 0.45, 0.9)
    eye = mat("steelie_eye_glow", (0.6, 0.03, 0.02), 0.25, emit=1.5, emit_color=(1.0, 0.05, 0.02))
    pupil = mat("steelie_pupil_glow", (1.0, 0.35, 0.1), 0.2, emit=5.0)
    seam = mat("steelie_seam_glow", (0.55, 0.02, 0.01), 0.4, emit=0.6)
    R = 0.3
    D = 0.007                                   # engraving depth
    bands = (55.0, 125.0, 20.0, 160.0)          # polar angles (degrees) of the plain grooves
    HW = 1.6                                    # their half-width
    front = -math.pi / 2                        # longitude of -Y (Godot +Z)
    SA, SB = 30.0, 8.6                          # the eye socket: half-length and half-height (degrees)

    def almond(x, a, b):
        """Half-height at x of a pointed almond of half-length a and half-height b (both in degrees)."""
        return b * max(0.0, 1 - (x / a) ** 2) ** 0.85

    def depth(th, phi):
        """(inward depth, material) at polar angle th (degrees) and longitude phi: 0 steel, 1 groove, 2 seam."""
        for b in bands:
            g = 1 - smoothstep(HW - 0.5, HW, abs(th - b))
            if g > 0:
                return D * g, (1 if g > 0.5 else 0)
        x = math.degrees(abs((phi - front + math.pi) % TAU - math.pi))
        sock = almond(x, SA, SB)
        hw = max(1.8, sock)
        g = 1 - smoothstep(hw - 0.7, hw, abs(th - 90))
        if g > 0:
            if sock > 1.8:                      # the socket: a flat floor deeper than the grooves
                return (D + 0.007) * g, (1 if g > 0.5 else 0)
            return D * g, (2 if g > 0.5 else 0)
        return 0.0, 0

    rows = set(k * 3.0 for k in range(61))
    for b in bands:
        rows |= {b - HW - 0.5, b - HW, b - HW + 0.5, b + HW - 0.5, b + HW, b + HW + 0.5}
    rows |= {90 + 0.75 * k for k in range(-13, 14)}
    rows = sorted(r for r in rows if 0 <= r <= 180)
    cols = 112

    verts, faces, fm = [], [], []
    idx = []
    for th in rows:
        t = math.radians(th)
        if th in (0, 180):
            verts.append((0, 0, R * math.cos(t)))
            idx.append([len(verts) - 1] * cols)
            continue
        row = []
        for j in range(cols):
            phi = TAU * j / cols
            d, _ = depth(th, phi)
            r = R - d
            verts.append((r * math.sin(t) * math.cos(phi), r * math.sin(t) * math.sin(phi), r * math.cos(t)))
            row.append(len(verts) - 1)
        idx.append(row)
    for i in range(len(rows) - 1):
        thc = (rows[i] + rows[i + 1]) / 2
        for j in range(cols):
            k = (j + 1) % cols
            f = []
            for v in (idx[i][j], idx[i][k], idx[i + 1][k], idx[i + 1][j]):
                if v not in f:
                    f.append(v)
            faces.append(f)
            fm.append(depth(thc, TAU * (j + 0.5) / cols)[1])
    ball = mesh_from("ball", verts, faces, [steel, groove, seam], fm, smooth=50)

    def lens(a, b, r, material, vertical=False, nx=40, ny=8):
        """A smooth almond patch on the sphere of radius r round the front: a long (degrees), b high."""
        vs, fs = [], []
        for i in range(nx + 1):
            x = -a + 2 * a * (0.5 - 0.5 * math.cos(math.pi * i / nx))
            h = max(0.05, almond(x, a, b))
            for j in range(ny + 1):
                y = -h + 2 * h * j / ny
                lon, lat = (y, x) if vertical else (x, y)
                lo, la = front + math.radians(lon), math.radians(lat)
                vs.append((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))
        for i in range(nx):
            for j in range(ny):
                q = i * (ny + 1) + j
                fs.append((q, q + ny + 1, q + ny + 2, q + 1))
        return mesh_from("lens", vs, fs, [material], smooth=60)

    parts = [ball, lens(SA - 3.0, SB - 1.6, R - 0.01, eye),     # the red eye, a little inside its socket
             lens(5.6, 1.5, R - 0.0085, pupil, vertical=True, nx=16, ny=4)]   # a hot slit pupil
    o = join(parts, "steelie")
    dims(o)
    export(o, "steelie")


# ------------------------------------------------------------------ the hopper

FOOT_TOP, SPRING_TOP, HEAD_C = 0.06, 0.32, 0.46


def hop_pose(t):
    """The hop at time t (0..1 s): (foot height, spring stretch, feeler swing in radians)."""
    H = 0.32
    if t < 0.12:                                    # landing: the spring squashes
        u = t / 0.12
        s = 1.1 + (0.58 - 1.1) * math.sin(u * math.pi / 2)
        return 0.0, s, 0.35 * math.sin(u * math.pi)
    if t < 0.24:                                    # the push: the spring shoots out, the foot still down
        u = (t - 0.12) / 0.12
        s = 0.58 + (1.28 - 0.58) * (1 - math.cos(u * math.pi)) / 2
        return 0.0, s, 0.2 - 0.6 * u
    u = (t - 0.24) / 0.76                           # in the air: a parabola, the apex at 0.62 s
    y = 4 * H * u * (1 - u)
    s = 1.28 + (0.92 - 1.28) * math.sin(min(u, 0.5) * math.pi) if u < 0.5 else 0.92 + (1.1 - 0.92) * (u - 0.5) / 0.5
    return y, s, -0.4 * math.cos(u * math.pi * 1.5) * (1 - u) + 0.1 * u


def hopper():
    skin = mat("hopper_skin", (0.95, 0.36, 0.26), 0.35, coat=0.7)
    belly = mat("hopper_belly", (1.0, 0.82, 0.62), 0.45, coat=0.4)
    cheek = mat("hopper_cheek", (1.0, 0.45, 0.5), 0.5)
    white = mat("hopper_eye", (0.97, 0.97, 0.95), 0.15, coat=1.0)
    pupil = mat("hopper_pupil", (0.03, 0.03, 0.05), 0.1, coat=1.0)
    glint = mat("hopper_glint_glow", (1, 1, 1), 0.2, emit=4.0)
    spring_m = mat("hopper_spring", (0.85, 0.45, 0.2), 0.22, 1.0)
    rubber = mat("hopper_foot", (0.12, 0.13, 0.17), 0.7)
    trim = mat("hopper_trim", (0.95, 0.75, 0.25), 0.25, 1.0)
    bulb = mat("hopper_bulb_glow", (0.45, 1.0, 0.75), 0.3, emit=5.0)

    # the foot: a rounded rubber pad with a brass ring
    foot = [lathe_r([(0.0, FOOT_TOP), (0.09, FOOT_TOP), (0.12, FOOT_TOP - 0.008), (0.135, 0.03), (0.13, 0.008),
                     (0.115, 0.0), (0.0, 0.0)], rubber, segs=32, smooth=50, name="foot_pad"),
            torus(0.082, 0.012, (0, 0, FOOT_TOP), trim, verts=28, minor=6)]
    foot = join(foot, "foot", pivot=(0, 0, 0))

    # the spring: five coils of copper wire, flattened end turns
    pts = []
    turns, n = 5.0, 220
    for i in range(n + 1):
        u = i / n
        a = TAU * turns * u
        h = u + 0.04 * math.sin(TAU * u)  # slightly closer coils at the ends
        z = FOOT_TOP + 0.005 + (SPRING_TOP - FOOT_TOP - 0.01) * min(1.0, max(0.0, h))
        r = 0.072 + 0.01 * math.sin(math.pi * u)
        pts.append((r * math.cos(a), r * math.sin(a), z))
    spring = tube(pts, [0.014] * len(pts), spring_m, verts=8, name="spring")
    spring = join([spring], "spring", pivot=(0, 0, FOOT_TOP))

    # the head: a round coral head, a pale face, huge eyes, fin ears, a collar on top of the spring
    hz = HEAD_C
    head = [ell((0, 0, hz), (0.175, 0.16, 0.145), skin, segs=40, rings=24),
            ell((0, -0.055, hz - 0.035), (0.13, 0.12, 0.09), belly, segs=32, rings=18),
            lathe_r([(0.0, SPRING_TOP + 0.03), (0.06, SPRING_TOP + 0.03), (0.085, SPRING_TOP + 0.01),
                     (0.088, SPRING_TOP - 0.01), (0.07, SPRING_TOP - 0.02), (0.0, SPRING_TOP - 0.02)], trim,
                    segs=28, smooth=50, name="collar")]
    for s in (1, -1):
        c = Vector((0.07 * s, -0.115, hz + 0.045))
        head.append(ell(c, (0.06, 0.05, 0.068), white, segs=24, rings=14))
        head.append(ell(c + Vector((-0.008 * s, -0.04, -0.004)), (0.03, 0.016, 0.038), pupil, segs=16, rings=10))
        head.append(sphere(0.011, c + Vector((0.006 * s, -0.056, 0.022)), glint, segs=8, rings=6))
        head.append(ell(c + Vector((0.0, 0.008, 0.06)), (0.05, 0.03, 0.012), skin, segs=14, rings=8, roll=-14 * s))
        head.append(ell((0.12 * s, -0.11, hz - 0.03), (0.026, 0.01, 0.018), cheek, segs=12, rings=6, yaw=30 * s))
        # fin ears: thin swept leaves to the sides
        ear = ell((0, 0, 0), (0.07, 0.016, 0.035), skin, segs=16, rings=8)
        ear.data.transform(Matrix.Translation((0.2 * s, 0.02, hz + 0.05)) @ Matrix.Rotation(-0.5 * s, 4, "Y")
                           @ Matrix.Rotation(0.3 * s, 4, "Z"))
        head.append(ear)
    mouth = []  # a little smile: a curved tube under the eyes
    for i in range(9):
        u = i / 8 - 0.5
        mouth.append((0.05 * u * 2, -0.168 + 0.012 * abs(u), hz - 0.045 + 0.03 * u * u))
    head.append(tube(mouth, [0.005] * len(mouth), pupil, verts=6, name="mouth"))
    head = join(head, "head", pivot=(0, 0, SPRING_TOP))

    # the feeler: a curled stalk with a glowing bulb
    top = hz + 0.14
    stalk = [(0, 0.02, top - 0.02), (0, 0.03, top + 0.04), (0, 0.0, top + 0.09), (0, -0.04, top + 0.11),
             (0, -0.07, top + 0.1)]
    from blastyard_bombers import smooth_path
    stalk = smooth_path(stalk, 4)
    feeler = [tube(stalk, [0.012 - 0.005 * i / (len(stalk) - 1) for i in range(len(stalk))], skin, verts=8,
                   name="stalk"),
              sphere(0.024, stalk[-1], bulb, segs=14, rings=10)]
    feeler = join(feeler, "feeler", pivot=(0, 0.02, top - 0.02))

    keys = {k: {} for k in ("foot", "spring", "head", "feeler")}
    for f in range(FPS + 1):
        y, s, sw = hop_pose(f / FPS)
        hs = 1 + 0.18 * (1 - s)               # the head squashes the other way: wide when the spring is short
        wide = 1 / math.sqrt(hs)
        keys["foot"][f] = {"loc": (0, 0, y), "scale": (1 + 0.15 * max(0, 1 - s), 1 + 0.15 * max(0, 1 - s), 1)}
        xy = 1 / math.sqrt(max(0.5, s)) ** 0.5
        keys["spring"][f] = {"loc": (0, 0, y), "scale": (xy, xy, s)}
        dz = y + (SPRING_TOP - FOOT_TOP) * (s - 1)
        keys["head"][f] = {"loc": (0, 0, dz), "scale": (hs, hs, wide)}
        fz = dz + (top - 0.02 - SPRING_TOP) * (wide - 1)
        keys["feeler"][f] = {"loc": (0, 0, fz), "rot": (sw, 0, 0)}
    for o, name in ((foot, "foot"), (spring, "spring"), (head, "head"), (feeler, "feeler")):
        animate(o, "hop", keys[name], linear=True)
    root = empty("hopper")
    dims_parts = [foot, spring, head, feeler]
    for p in dims_parts:
        print("  part %-7s %5d tris" % (p.name, K.tris(p)))
    export_anim(root, "hopper", [(p, root) for p in dims_parts])


# ------------------------------------------------------------------ the goal arch

def goal_arch():
    body = mat("goal_body", (0.9, 0.9, 0.92), 0.3, coat=0.5)
    trim = mat("goal_trim", (0.95, 0.72, 0.3), 0.25, 1.0)
    glow = mat("goal_glow", (0.25, 0.75, 1.0), 0.3, emit=4.0)
    lamp = mat("goal_lamp_glow", (1.0, 0.85, 0.5), 0.3, emit=6.0)
    crest = mat("goal_crest_glow", (1.0, 0.8, 0.3), 0.3, emit=5.0)
    ca = mat("goal_check_a", (0.95, 0.95, 0.95), 0.6)
    cb = mat("goal_check_b", (0.04, 0.04, 0.05), 0.6)
    W, DEP = 0.32, 0.42          # the arch's beam: width across the gate, depth along the course
    X0 = 1.5 - 0.27              # the beam's centre line at the base (the plinths reach x = +-1.5)
    Z0, RZ = 1.8, 0.7            # the legs rise straight to Z0, then an elliptical top to 2.5 (outer edge)
    rz = RZ - W / 2              # the centre line's vertical semi-axis
    L1 = Z0
    L2 = math.pi * (3 * (X0 + rz) - math.sqrt((3 * X0 + rz) * (X0 + 3 * rz))) / 2   # half the ellipse (Ramanujan)
    tot = 2 * L1 + L2

    def centre(u):
        """The beam's centre line, u from 0 (left foot) to 1 (right foot)."""
        s = u * tot
        if s < L1:
            return Vector((-X0, 0, s)), Vector((1, 0, 0))
        if s > L1 + L2:
            return Vector((X0, 0, tot - s)), Vector((-1, 0, 0))
        a = math.pi * (1 - (s - L1) / L2)
        p = Vector((X0 * math.cos(a), 0, Z0 + rz * math.sin(a)))
        n = Vector((math.cos(a) / X0, 0, math.sin(a) / rz)).normalized()   # outward normal of the ellipse
        return p, -n

    # the beam: a rounded rectangle cross-section swept along the centre line (inward normal n, depth along Y)
    prof = []
    for k in range(16):
        a = TAU * k / 16
        ex, ey = math.cos(a), math.sin(a)
        p = 3.0
        sx = math.copysign(abs(ex) ** (2 / p), ex)
        sy = math.copysign(abs(ey) ** (2 / p), ey)
        prof.append((sx * W / 2, sy * DEP / 2))
    N = 90
    verts, faces, fm = [], [], []
    for i in range(N + 1):
        c, n = centre(i / N)
        for px, py in prof:
            verts.append(tuple(c + n * px + Vector((0, py, 0))))
    for i in range(N):
        for k in range(16):
            a, b = i * 16 + k, i * 16 + (k + 1) % 16
            faces.append((a, b, b + 16, a + 16))
            # light seams on the front and back faces (the middle of the y = +-DEP/2 sides)
            fm.append(2 if k in (4, 12) else (1 if k in (3, 5, 11, 13) else 0))
    for end in (0, N):
        faces.append(tuple(end * 16 + k for k in range(16)))
        fm.append(0)
    parts = [mesh_from("arch", verts, faces, [body, trim, glow], fm, smooth=40)]
    # plinths and feet
    for s in (1, -1):
        parts.append(K.box((0.5, 0.62, 0.3), (s * X0, 0, 0.15), body, bevel=0.04))
        parts.append(K.box((0.54, 0.66, 0.05), (s * X0, 0, 0.3), trim, bevel=0.015))
        parts.append(K.box((0.36, 0.5, 0.04), (s * X0, 0, 0.025), trim, bevel=0.01))
        for y in (-0.315, 0.315):
            parts.append(K.box((0.3, 0.02, 0.08), (s * X0, y, 0.15), glow, bevel=0.005))
    # lamps along the inner edge of the arch
    for i in range(1, 22):
        u = 0.08 + 0.84 * i / 22
        c, n = centre(u)
        p = c + n * (W / 2 + 0.005)
        parts.append(sphere(0.035, p, lamp, segs=10, rings=6))
        parts.append(torus(0.04, 0.008, (0, 0, 0), trim, verts=12, minor=4))
        parts[-1].data.transform(Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4())
    # the crest: a diamond in a ring on top
    top = Vector((0, 0, 2.43))
    parts.append(torus(0.17, 0.025, top + Vector((0, 0, 0.0)), trim, rot=(math.pi / 2, 0, 0), verts=28, minor=6))
    d = K.ico(0.12, top, crest, scale=(0.8, 0.5, 1.2), sub=0, smooth=0)
    parts.append(d)
    arch = join(parts, "goal_arch")
    # the banner: a bar and a chequered cloth, 10 x 2 squares, each square split 2 x 2 for waving
    BW, BH, BZ = 1.8, 0.4, 1.9
    bar = [rod((-1.02, 0, BZ + 0.03), (1.02, 0, BZ + 0.03), 0.025, trim, verts=10)]
    for s in (1, -1):
        bar.append(sphere(0.04, (s * 0.97, 0, BZ + 0.03), trim, segs=10, rings=8))
    nx, nz = 40, 8
    verts, faces, fm = [], [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            x = -BW / 2 + BW * i / nx
            z = BZ - BH * j / nz
            verts.append((x, -0.012 * math.sin(math.pi * i / nx * 5) * (j / nz), z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
            fm.append(((i // 4) + (j // 4)) % 2)
    cloth = mesh_from("cloth", verts, faces, [ca, cb], fm, smooth=40)
    # the cloth is one-sided in the file: give it a back by duplicating the faces flipped
    bm = bmesh.new()
    bm.from_mesh(cloth.data)
    back = bmesh.ops.duplicate(bm, geom=list(bm.faces))["geom"]
    bf = [g for g in back if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=bf)
    for g in back:
        if isinstance(g, bmesh.types.BMVert):
            g.co.y += 0.004
    bm.to_mesh(cloth.data)
    bm.free()
    banner = join(bar + [cloth], "banner", pivot=(0, 0, BZ))
    dims(arch)
    export(arch, "goal_arch", [(banner, arch)])


# ------------------------------------------------------------------ the beacon

def beacon():
    body = mat("beacon_body", (0.88, 0.89, 0.92), 0.3, coat=0.5)
    trim = mat("beacon_trim", (0.3, 0.33, 0.38), 0.25, 1.0)
    glow = mat("beacon_glow", (0.4, 0.95, 1.0), 0.15, emit=1.2)
    parts = [lathe_r([(0.0, 0.07), (0.17, 0.07), (0.2, 0.05), (0.21, 0.0), (0.0, 0.0)], trim, segs=6, smooth=0,
                     name="foot"),
             lathe_r([(0.0, 0.1), (0.12, 0.1), (0.15, 0.08), (0.15, 0.07), (0.0, 0.07)], body, segs=6, smooth=0,
                     name="foot2")]
    # the fluted post, tapering
    prof = [(0.0, 0.8), (0.035, 0.8), (0.045, 0.75), (0.05, 0.4), (0.065, 0.14), (0.09, 0.1), (0.0, 0.1)]
    parts.append(lathe_r(prof, body, segs=24, radial=lambda k, z: 1.0 - 0.12 * (k % 2), smooth=40, name="post"))
    for z, r in ((0.32, 0.058), (0.6, 0.05)):
        parts.append(torus(r, 0.008, (0, 0, z), trim, verts=20, minor=5))
    # the claw: a collar and three prongs curling up round the crystal
    parts.append(lathe_r([(0.0, 0.86), (0.07, 0.86), (0.085, 0.83), (0.06, 0.78), (0.0, 0.78)], trim, segs=18,
                         smooth=40, name="collar"))
    for k in range(3):
        a = TAU * k / 3 + math.pi / 6
        c, s = math.cos(a), math.sin(a)
        pts = [(0.06 * c, 0.06 * s, 0.84), (0.11 * c, 0.11 * s, 0.92), (0.1 * c, 0.1 * s, 1.03),
               (0.055 * c, 0.055 * s, 1.1)]
        parts.append(tube(pts, [0.016, 0.014, 0.012, 0.008], trim, verts=8, name="prong"))
    parts.append(torus(0.105, 0.01, (0, 0, 0.94), glow, verts=28, minor=6))
    # the crystal: a long hexagonal bipyramid, faceted
    parts.append(lathe_r([(0.0, 1.2), (0.05, 1.12), (0.07, 1.02), (0.065, 0.92), (0.0, 0.86)], glow, segs=6,
                         smooth=0, name="crystal"))
    o = join(parts, "beacon")
    dims(o)
    export(o, "beacon")


# ------------------------------------------------------------------ the pylon

def pylon():
    body = mat("pylon_body", (0.8, 0.82, 0.86), 0.35, coat=0.3)
    trim = mat("pylon_trim", (0.32, 0.35, 0.4), 0.3, 1.0)
    glow = mat("pylon_glow", (0.3, 0.85, 1.0), 0.3, emit=3.0)
    parts = []
    # the head plate: 1 x 1, chamfered, flush with the course's underside
    parts.append(K.box((1.0, 1.0, 0.16), (0, 0, -0.08), trim, bevel=0.05))
    parts.append(K.box((0.86, 0.86, 0.22), (0, 0, -0.25), body, bevel=0.06))
    # the shaft: octagonal sections tapering to a point, light seams on four faces
    prof = [(0.44, -0.36), (0.4, -0.7), (0.33, -2.0), (0.27, -4.5), (0.21, -7.0), (0.16, -9.0), (0.11, -10.6),
            (0.06, -11.5), (0.0, -12.0)]
    S = 8
    verts, faces, fm = [], [], []
    for r, z in prof:
        for k in range(S):
            a = TAU * (k + 0.5) / S
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(len(prof) - 1):
        for k in range(S):
            a, b = i * S + k, i * S + (k + 1) % S
            faces.append((a, b, b + S, a + S))
            fm.append(0)
    shaft = mesh_from("shaft", verts, faces, [body], fm, smooth=0)
    parts.append(shaft)
    # light seams: thin glowing strips standing just proud of four faces, from z -0.6 to -10.4
    for k in range(4):
        a = TAU * k / 4
        pts = []
        for z in (-0.6, -10.4):
            r = None
            for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
                if z1 <= z <= z0:
                    r = r0 + (r1 - r0) * (z - z0) / (z1 - z0)
            r *= math.cos(math.pi / S)     # the octagon's face, not its corner
            pts.append((r * math.cos(a), r * math.sin(a), z))
        parts.append(rod(pts[0], pts[1], 0.03, glow, r2=0.02, verts=6))
    # collars every few units, and a beacon at the tip
    for z in (-0.7, -2.0, -4.5, -7.0, -9.0):
        rr = next(r0 for r0, z0 in prof if abs(z0 - z) < 1e-6)
        parts.append(lathe_r([(0.0, z + 0.07), (rr + 0.03, z + 0.07), (rr + 0.05, z + 0.03), (rr + 0.05, z - 0.03),
                              (rr + 0.03, z - 0.07), (0.0, z - 0.07)], trim, segs=8, smooth=0, name="collar"))
        parts[-1].data.transform(Matrix.Rotation(TAU / 16, 4, "Z"))
    parts.append(sphere(0.06, (0, 0, -11.25), glow, segs=12, rings=8))
    # a halo: a glowing ring floating round the shaft below the head, held by four struts
    parts.append(torus(0.5, 0.03, (0, 0, -1.3), glow, verts=40, minor=6))
    parts.append(torus(0.5, 0.05, (0, 0, -1.3), trim, verts=40, minor=6, scale=(1, 1, 0.35)))
    for k in range(4):
        a = TAU * k / 4 + TAU / 8
        c, sn = math.cos(a), math.sin(a)
        parts.append(rod((0.3 * c, 0.3 * sn, -0.9), (0.5 * c, 0.5 * sn, -1.3), 0.025, trim, verts=6))
    o = join(parts, "pylon")
    dims(o)
    export(o, "pylon")


# ------------------------------------------------------------------ the shard

def shard():
    glass = mat("shard_glass", (0.75, 0.9, 1.0), 0.05, coat=1.0, alpha=0.45)
    R, T = 0.3, 0.01
    # a triangle on the marble's shell (a patch of the sphere of radius 0.3), with a bevelled rim
    corners = [Vector((0.0, -1.0, 0.13)), Vector((0.2, -1.0, -0.12)), Vector((-0.17, -1.0, -0.07))]
    corners = [c.normalized() for c in corners]
    n = 8
    verts, faces = [], []
    idx = {}
    for side, r in ((0, R), (1, R - T)):
        for i in range(n + 1):
            for j in range(n + 1 - i):
                k = n - i - j
                d = (corners[0] * i + corners[1] * j + corners[2] * k).normalized()
                idx[side, i, j] = len(verts)
                verts.append(tuple(d * r))
    for side in (0, 1):
        for i in range(n):
            for j in range(n - i):
                a, b, c = idx[side, i, j], idx[side, i + 1, j], idx[side, i, j + 1]
                faces.append((a, b, c) if side == 0 else (a, c, b))
                if i + j < n - 1:
                    d = idx[side, i + 1, j + 1]
                    faces.append((b, d, c) if side == 0 else (b, c, d))
    rim = ([(n - t, t) for t in range(n + 1)] + [(0, n - t) for t in range(1, n + 1)] +
           [(t, 0) for t in range(1, n)])
    for (i0, j0), (i1, j1) in zip(rim, rim[1:] + rim[:1]):
        faces.append((idx[0, i0, j0], idx[0, i1, j1], idx[1, i1, j1], idx[1, i0, j0]))
    o = mesh_from("shard", verts, faces, [glass], smooth=30)
    c = sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
    o.data.transform(Matrix.Translation(-c))
    dims(o)
    export(o, "shard")


# ------------------------------------------------------------------ the flag

def flag():
    pole_m = mat("flag_pole", (0.7, 0.72, 0.76), 0.25, 1.0)
    cloth_m = mat("flag_cloth", (0.92, 0.92, 0.9), 0.6)
    hem = mat("flag_hem", (0.25, 0.27, 0.32), 0.5)
    tip = mat("flag_tip_glow", (1.0, 0.8, 0.35), 0.3, emit=5.0)
    parts = [lathe_r([(0.0, 0.05), (0.05, 0.05), (0.07, 0.03), (0.075, 0.0), (0.0, 0.0)], pole_m, segs=12,
                     smooth=40, name="foot"),
             rod((0, 0, 0.04), (0, 0, 0.97), 0.014, pole_m, verts=10),
             sphere(0.028, (0, 0, 0.985), tip, segs=12, rings=8)]
    pole = join(parts, "flag")
    # the pennant: a triangle from the pole out along +X, subdivided 8 x 6 (rows shrink to the point)
    L, H, Z = 0.42, 0.24, 0.83
    nx, nz = 10, 6
    verts, faces, fm = [], [], []
    for i in range(nx + 1):
        u = i / nx
        for j in range(nz + 1):
            v = j / nz
            h = H * (1 - u)
            verts.append((0.016 + L * u, 0.0, Z + (0.5 - v) * h))
    for i in range(nx):
        for j in range(nz):
            a = i * (nz + 1) + j
            q = (a, a + nz + 1, a + nz + 2, a + 1)
            faces.append(q)
            fm.append(1 if i == 0 or j in (0, nz - 1) else 0)
    p = mesh_from("pennant", verts, faces, [cloth_m, hem], fm, smooth=40)
    bm = bmesh.new()
    bm.from_mesh(p.data)
    back = bmesh.ops.duplicate(bm, geom=list(bm.faces))["geom"]
    bmesh.ops.reverse_faces(bm, faces=[g for g in back if isinstance(g, bmesh.types.BMFace)])
    for g in back:
        if isinstance(g, bmesh.types.BMVert):
            g.co.y += 0.003
    bm.to_mesh(p.data)
    bm.free()
    p = join([p], "pennant", pivot=(0, 0, Z))
    dims(pole)
    export(pole, "flag", [(p, pole)])


JOBS = {"steelie": steelie, "hopper": hopper, "goal_arch": goal_arch, "beacon": beacon, "pylon": pylon,
        "shard": shard, "flag": flag}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
