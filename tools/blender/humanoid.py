"""Shared humanoid builder for Blender scripts: a full biped skeleton, smooth skinning, a sculpted body made of dense
tubes and lofts, and an animation system (keyed poses with smooth auto-clamped interpolation, leg and arm IK, foot
roll, a gait generator for walk and run cycles). One glTF animation per action. Output CC BY-SA 4.0.
Users: knuckles_fighters.py, frostpeak_athletes.py, boots_models.py; flags_robots.py uses the legacy rigid path.
About 1.8 m tall at scale 1, feet at z = 0, facing -Y.

Skeleton (new rig): root > hips > spine > chest > neck > head; chest > clavicle.X > arm.X > forearm.X > hand.X;
hips > thigh.X > shin.X > foot.X > toe.X (> ski.X when asked). Every bone's local Z points forward (up for foot, toe
and ski), so rotations read the same on every bone and mirror between sides.

Skinning: a part is tagged with a rigid bone name ("head", "hand.L", "ski.R") or a smooth region: "~body" (pelvis,
torso, neck: blended down the spine and into the legs, clavicles and arms at the hips and shoulders), "~arm.L"
(clavicle, upper arm, forearm, wrist), "~leg.L" (hip, thigh, knee, shin, ankle) or "~foot.L" (shoe: shin collar,
foot, toes). Weights are a smooth function of the rest position, so overlapping parts (a sleeve over an arm, a knee
cap over a leg) move together and no gap opens at a bent joint.

Poses: {bone: (flex, twist, side)} in degrees. flex + bends forward (spine, neck, head: lean forward; clavicle: shoulder
forward; arm: swing forward and up; forearm: elbow bend; thigh: leg forward; shin: knee bend; foot and toe: toes up),
twist + turns left (spine chain) or rotates inward (limbs), side + leans right (spine chain), shrugs up (clavicle),
lifts out (arm, thigh; hand: back of the hand; foot: toe out). Right-side bones mirror the left, so one set of numbers
makes a symmetric pose. Special channels: "root": (left, forward, up) metres; "turn": (pitch forward, yaw left, roll
right) degrees about the floor under the hips; "ik_foot.L": (left, forward, up, pitch, yaw) ankle target on the ground
with the foot's pitch (toes up +) and yaw (toe out +); "ikw.L" its weight; "ik_hand.L": (left, forward, up) wrist
target; "ikh.L" its weight (the target can ride another bone, see Anim).
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Quaternion

MATS = {}


def mat(name, color, rough=0.5, metal=0.0, coat=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    MATS[name] = m
    return m


def active():
    return bpy.context.active_object


def _select_only(o):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)


def tag(o, bone, material, smooth=True):
    """Gives a part its material and its binding: a rigid bone name, or a smooth region ("~body", "~arm.L" ...)."""
    o.data.materials.clear()
    o.data.materials.append(material)
    o["bone"] = bone
    _select_only(o)
    if smooth:
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()
    return o


def smoothstep(e0, e1, x):
    if e0 == e1:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ primitives (legacy API kept)

def sphere(r, loc, bone, material, scale=(1, 1, 1), segs=24, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return tag(o, bone, material)


def box(size, loc, bone, material, rot=(0, 0, 0), bevel=None, segs=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    b = o.modifiers.new("b", "BEVEL")
    b.width = min(size) * 0.3 if bevel is None else bevel
    b.segments = segs
    bpy.ops.object.modifier_apply(modifier=b.name)
    return tag(o, bone, material)


def limb(r, a, b, bone, material, r2=None, verts=16):
    a, b = Vector(a), Vector(b)
    d = b - a
    r2 = r if r2 is None else r2
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = active()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    parts = [o]
    for p, rr in ((a, r), (b, r2)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=verts, ring_count=8, radius=rr, location=p)
        parts.append(active())
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for x in parts:
        x.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    return tag(active(), bone, material)


def _mesh_object(bm, name="part"):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    _select_only(o)
    return o


def _loft(ring_pts, material, bone, subsurf=1, caps=True):
    """A closed surface through rings of points (each ring the same count), bottom to top, capped with fans."""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in ring] for ring in ring_pts]
    n = len(rings[0])
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    if caps:
        for ring, rev in ((rings[0], True), (rings[-1], False)):
            c = sum((v.co for v in ring), Vector()) / n
            cv = bm.verts.new(c)
            for i in range(n):
                a, b = ring[i], ring[(i + 1) % n]
                bm.faces.new((a, cv, b) if rev else (a, b, cv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _mesh_object(bm, "loft")
    if subsurf:
        m = o.modifiers.new("s", "SUBSURF")
        m.levels = subsurf
        bpy.ops.object.modifier_apply(modifier=m.name)
    return tag(o, bone, material)


def _catmull(pts, t):
    """Catmull-Rom through a list of Vectors (or floats), t in [0, len - 1]."""
    n = len(pts)
    i = min(int(t), n - 2)
    u = t - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)


def _superellipse(rx, ry, cy, z, segs, n=2.0, x0=0.0):
    pts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        e = 2.0 / n
        pts.append((x0 + rx * math.copysign(abs(c) ** e, c), cy + ry * math.copysign(abs(s) ** e, s), z))
    return pts


def body_loft(rings, bone, material, segs=20, subsurf=1, step=None, x0=0.0):
    """A torso-like part through horizontal (super)ellipses [(z, half width, half depth, y offset[, squareness])],
    bottom to top. With `step`, the rings are resampled every `step` metres (dense rings bend smoothly)."""
    rings = [tuple(r) + (0.0,) * (4 - len(r)) + ((2.0,) if len(r) < 5 else ()) for r in rings]
    if step:
        zs = [r[0] for r in rings]
        n = max(2, int(round((zs[-1] - zs[0]) / step)) + 1)
        cols = [[r[k] for r in rings] for k in range(5)]
        dense = []
        for i in range(n):
            z = zs[0] + (zs[-1] - zs[0]) * i / (n - 1)
            # find the parameter whose z matches (z is monotonic)
            k = 0
            while k < len(zs) - 2 and zs[k + 1] < z:
                k += 1
            u = (z - zs[k]) / (zs[k + 1] - zs[k]) if zs[k + 1] != zs[k] else 0.0
            dense.append(tuple([z] + [_catmull(cols[c], k + u) for c in range(1, 5)]))
        rings = dense
    pts = [_superellipse(rx, ry, cy, z, segs, sq, x0) for z, rx, ry, cy, sq in rings]
    return _loft(pts, material, bone, subsurf)


def muscle_limb(points, bone, material, segs=14, subsurf=1):
    """A limb swept along [(x, y, z, radius)] with rings square to the path: bulges and tapers where you ask."""
    pts = [Vector(p[:3]) for p in points]
    rings = []
    for k, p in enumerate(pts):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        a = d.orthogonal().normalized()
        b = d.cross(a).normalized()
        r = points[k][3]
        rings.append([tuple(p + (a * math.cos(2 * math.pi * i / segs) + b * math.sin(2 * math.pi * i / segs)) * r) for i in range(segs)])
    return _loft(rings, material, bone, subsurf)


def tube(points, bone, material, segs=16, step=0.018, ell=(1.0, 1.0), caps=(True, True), lateral=(1, 0, 0), sq=2.0):
    """A smooth tube through control points [(x, y, z, radius)], resampled every `step` metres along a Catmull-Rom
    path, with rounded ends. `ell` squashes the section (across, front-back); `lateral` is the across direction at
    the start. Dense rings are what lets a skinned limb bend without creasing."""
    ctrl = [Vector(p[:3]) for p in points]
    rad = [p[3] for p in points]
    # arc length sampling
    fine = [(_catmull(ctrl, t), _catmull(rad, t)) for t in [i / 40.0 * (len(ctrl) - 1) for i in range(41)]]
    L = [0.0]
    for i in range(1, len(fine)):
        L.append(L[-1] + (fine[i][0] - fine[i - 1][0]).length)
    n = max(3, int(L[-1] / step) + 1)
    samples = []
    j = 0
    for i in range(n):
        s = L[-1] * i / (n - 1)
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        u = (s - L[j]) / max(1e-9, L[j + 1] - L[j])
        samples.append((fine[j][0].lerp(fine[j + 1][0], u), fine[j][1] + (fine[j + 1][1] - fine[j][1]) * u))
    # parallel-transport frames
    lat = Vector(lateral).normalized()
    rings = []
    prev_t = None
    for i, (p, r) in enumerate(samples):
        t = (samples[min(i + 1, n - 1)][0] - samples[max(i - 1, 0)][0]).normalized()
        if prev_t is not None:
            q = prev_t.rotation_difference(t)
            lat = q @ lat
        lat = (lat - t * lat.dot(t)).normalized()
        fwd = t.cross(lat).normalized()
        prev_t = t
        rings.append((p, r, t, lat, fwd))

    def ring(p, r, lat, fwd):
        out = []
        e = 2.0 / sq
        for k in range(segs):
            a = 2 * math.pi * k / segs
            c, s = math.cos(a), math.sin(a)
            c, s = math.copysign(abs(c) ** e, c), math.copysign(abs(s) ** e, s)
            out.append(tuple(p + lat * (c * r * ell[0]) + fwd * (s * r * ell[1])))
        return out
    body = [ring(p, r, lat, fwd) for p, r, t, lat, fwd in rings]
    # rounded caps
    for end, sign in ((0, -1), (-1, 1)):
        if not caps[0 if end == 0 else 1]:
            continue
        p, r, t, lat, fwd = rings[end]
        cap = [ring(p + t * sign * r * math.sin(a), r * math.cos(a), lat, fwd) for a in (0.5, 0.95, 1.3)]
        if end == 0:
            body = list(reversed(cap)) + body
        else:
            body = body + cap
    return _loft(body, material, bone, 0)


def shell(rings, a0, a1, bone, material, thick=0.006, segs=16, subsurf=1):
    """An open, curved panel over the body: arcs from angle a0 to a1 (degrees; -90 is the front, 0 the left side)
    through ellipses [(z, half width, half depth, y centre)], given a thickness. Bibs, jackets, hoods."""
    bm = bmesh.new()
    rows = []
    for z, rx, ry, cy in rings:
        row = []
        for i in range(segs + 1):
            a = math.radians(a0 + (a1 - a0) * i / segs)
            row.append(bm.verts.new((rx * math.cos(a), cy + ry * math.sin(a), z)))
        rows.append(row)
    for k in range(len(rows) - 1):
        for i in range(segs):
            bm.faces.new((rows[k][i], rows[k][i + 1], rows[k + 1][i + 1], rows[k + 1][i]))
    o = _mesh_object(bm, "shell")
    if subsurf:
        m = o.modifiers.new("s", "SUBSURF")
        m.levels = subsurf
        bpy.ops.object.modifier_apply(modifier=m.name)
    m = o.modifiers.new("t", "SOLIDIFY")
    m.thickness = thick
    m.offset = 1.0
    bpy.ops.object.modifier_apply(modifier=m.name)
    return tag(o, bone, material)


def head_detailed(skin, eye_white, iris, center=(0, 0, 1.66), hair=None, bone="head", brow=None, size=1.0, lips=None):
    """A head, rigid on the head bone: cranium, jaw and chin, nose, ears, eyes set into the face, eyebrows, a mouth
    and (optionally) a cap of hair."""
    cx, cy, cz = center
    s = size

    def P(x, y, z):
        return (cx + x * s, cy + y * s, cz + z * s)
    sphere(0.1 * s, P(0, 0.006, 0.004), bone, skin, (0.87, 1.0, 1.08), 32, 18)             # cranium
    sphere(0.072 * s, P(0, -0.02, -0.05), bone, skin, (0.95, 0.95, 0.85), 24, 14)          # jaw
    sphere(0.024 * s, P(0, -0.062, -0.094), bone, skin, (1.3, 0.9, 0.75), 16, 10)         # chin
    sphere(0.016 * s, P(0, -0.097, -0.012), bone, skin, (0.72, 1.0, 1.35), 14, 10)        # nose bridge
    sphere(0.012 * s, P(0, -0.104, -0.027), bone, skin, (1.1, 0.95, 0.85), 14, 10)        # nose tip
    sphere(0.012 * s, P(0, -0.088, -0.058), bone, lips or mat("lips", (0.55, 0.28, 0.24), 0.5), (1.7, 0.45, 0.4), 12, 8)
    for k in (-1, 1):
        sphere(0.023 * s, P(0.087 * k, 0.01, -0.006), bone, skin, (0.45, 0.85, 1.3), 14, 10)   # ears
        sphere(0.0125 * s, P(0.033 * k, -0.079, 0.016), bone, eye_white, (1.15, 0.8, 0.9), 14, 10)
        sphere(0.0068 * s, P(0.033 * k, -0.09, 0.016), bone, iris, (1, 0.6, 1), 10, 8)
        sphere(0.017 * s, P(0.034 * k, -0.086, 0.042), bone, brow or hair or iris, (1.45, 0.42, 0.34), 12, 8)   # eyebrow
    if hair:
        sphere(0.106 * s, P(0, 0.02, 0.04), bone, hair, (0.92, 1.0, 0.88), 32, 18)


# ------------------------------------------------------------------ the skeleton

def proportions(**k):
    """Joint positions for a 1.8 m adult (metres). Override any of them, e.g. a broader shoulder."""
    P = dict(hip_h=0.93, hip_w=0.095, knee_h=0.505, ankle_h=0.09, ball_y=-0.125, toe_y=-0.2, heel_y=0.065,
             waist_h=1.06, chest_h=1.25, neck_h=1.465, head_h=1.575, top=1.8,
             sh_w=0.185, sh_h=1.425, clav_w=0.025, upper=0.29, fore=0.255, handl=0.09,
             arm_out=9.0, elbow_fwd=10.0)
    P.update(k)
    return P


class Skeleton:
    """Rest joints built from proportions; knows each bone's head, tail, parent and roll axis."""

    def __init__(self, P=None, skis=False):
        P = P or proportions()
        self.P = P
        B = {}
        B["root"] = ((0, 0, 0), (0, 0, 0.12), None, "fwd")
        B["hips"] = ((0, 0, P["hip_h"] + 0.02), (0, 0, P["waist_h"]), "root", "fwd")
        B["spine"] = ((0, 0, P["waist_h"]), (0, 0.0, P["chest_h"]), "hips", "fwd")
        B["chest"] = ((0, 0.0, P["chest_h"]), (0, 0.0, P["neck_h"]), "spine", "fwd")
        B["neck"] = ((0, 0.0, P["neck_h"]), (0, -0.012, P["head_h"]), "chest", "fwd")
        B["head"] = ((0, -0.012, P["head_h"]), (0, -0.012, P["top"]), "neck", "fwd")
        for s, X in ((1, "L"), (-1, "R")):
            sh = Vector((P["sh_w"] * s, 0.0, P["sh_h"]))
            a = math.radians(P["arm_out"])
            el = sh + Vector((math.sin(a) * s, 0, -math.cos(a))) * P["upper"]
            f = math.radians(P["elbow_fwd"])
            wr = el + Vector((math.sin(a) * math.cos(f) * s, -math.sin(f), -math.cos(a) * math.cos(f))) * P["fore"]
            hd = (wr - el).normalized()
            B["clavicle." + X] = ((P["clav_w"] * s, -0.03, P["sh_h"] + 0.015), tuple(sh), "chest", "fwd")
            B["arm." + X] = (tuple(sh), tuple(el), "clavicle." + X, "fwd")
            B["forearm." + X] = (tuple(el), tuple(wr), "arm." + X, "fwd")
            B["hand." + X] = (tuple(wr), tuple(wr + hd * P["handl"]), "forearm." + X, "fwd")
            hip = (P["hip_w"] * s, 0.0, P["hip_h"])
            knee = (P["hip_w"] * s + 0.004 * s, -0.012, P["knee_h"])
            ank = (P["hip_w"] * s + 0.006 * s, 0.0, P["ankle_h"])
            ball = (ank[0] + 0.004 * s, P["ball_y"], 0.028)
            toe = (ank[0] + 0.004 * s, P["toe_y"], 0.024)
            B["thigh." + X] = (hip, knee, "hips", "fwd")
            B["shin." + X] = (knee, ank, "thigh." + X, "fwd")
            B["foot." + X] = (ank, ball, "shin." + X, "up")
            B["toe." + X] = (ball, toe, "foot." + X, "up")
            if skis:
                B["ski." + X] = ((ank[0], -0.09, 0.0), (ank[0], -0.4, 0.0), "foot." + X, "up")
        self.bones = B
        self.order = list(B.keys())

    def head(self, b):
        return Vector(self.bones[b][0])

    def tail(self, b):
        return Vector(self.bones[b][1])


BONES = {  # the legacy rigid rig (flags_robots.py replaces it with its own)
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, 0, 0.95), (0, 0, 1.1), "root"),
    "spine": ((0, 0, 1.1), (0, 0, 1.45), "hips"),
    "head": ((0, 0, 1.45), (0, 0, 1.8), "spine"),
    "arm.L": ((0.2, 0, 1.42), (0.24, 0, 1.12), "spine"),
    "forearm.L": ((0.24, 0, 1.12), (0.26, -0.02, 0.86), "arm.L"),
    "arm.R": ((-0.2, 0, 1.42), (-0.24, 0, 1.12), "spine"),
    "forearm.R": ((-0.24, 0, 1.12), (-0.26, -0.02, 0.86), "arm.R"),
    "thigh.L": ((0.1, 0, 0.95), (0.1, 0, 0.52), "hips"),
    "shin.L": ((0.1, 0, 0.52), (0.1, 0, 0.08), "thigh.L"),
    "thigh.R": ((-0.1, 0, 0.95), (-0.1, 0, 0.52), "hips"),
    "shin.R": ((-0.1, 0, 0.52), (-0.1, 0, 0.08), "thigh.R"),
    "ski.L": ((0.1, 0, 0.04), (0.1, -0.3, 0.04), "shin.L"),
    "ski.R": ((-0.1, 0, 0.04), (-0.1, -0.3, 0.04), "shin.R"),
}


# ------------------------------------------------------------------ skin weights

def _chain_weights(p, joints, bones, widths, before=None, after=None):
    """Weights along a chain of joints: each segment belongs to one bone, blended across each joint over
    +-width (metres, along the chain). `before`/`after` take points past the ends."""
    best, bk, bt = 1e9, 0, 0.0
    for k in range(len(joints) - 1):
        a, b = joints[k], joints[k + 1]
        d = b - a
        L2 = d.length_squared
        t = (p - a).dot(d) / L2
        tc = min(1.0, max(0.0, t))
        dist = (p - (a + d * tc)).length
        if dist < best - 1e-9:
            best, bk, bt = dist, k, t
    L = (joints[bk + 1] - joints[bk]).length
    w = {bones[bk]: 1.0}
    prev = bones[bk - 1] if bk > 0 else before
    if prev:
        b = smoothstep(-widths[bk], widths[bk], bt * L)
        w = {bones[bk]: b, prev: 1.0 - b}
    nxt = bones[bk + 1] if bk + 1 < len(bones) else after
    if nxt:
        c = smoothstep(-widths[bk + 1], widths[bk + 1], (bt - 1.0) * L)
        w = {k_: v * (1.0 - c) for k_, v in w.items()}
        w[nxt] = w.get(nxt, 0.0) + c
    return w


def _mix(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0.0) + v * t
    return out


class Skinner:
    def __init__(self, sk):
        self.sk = sk
        h, t = sk.head, sk.tail
        self.spine = ([h("hips") - Vector((0, 0, 0.3)), h("spine"), h("chest"), h("neck"), h("head"), t("head")],
                      ["hips", "spine", "chest", "neck", "head"], [0.0, 0.055, 0.075, 0.035, 0.03, 0.0])
        self.arm, self.leg = {}, {}
        for X in "LR":
            self.arm[X] = ([h("clavicle." + X), h("arm." + X), h("forearm." + X), h("hand." + X), t("hand." + X)],
                           ["clavicle." + X, "arm." + X, "forearm." + X, "hand." + X], [0.03, 0.055, 0.045, 0.025, 0.0])
            self.leg[X] = ([h("thigh." + X) + Vector((0, 0, 0.25)), h("thigh." + X), h("shin." + X), h("foot." + X), h("foot." + X) - Vector((0, 0, 0.2))],
                           ["hips", "thigh." + X, "shin." + X, "foot." + X], [0.0, 0.075, 0.05, 0.03, 0.0])

    def arm_w(self, p, X):
        j, b, w = self.arm[X]
        return _chain_weights(p, j, b, w, before="chest")

    def leg_w(self, p, X):
        j, b, w = self.leg[X]
        return _chain_weights(p, j, b, w)

    def foot_w(self, p, X):
        sk = self.sk
        ank, ball = sk.head("foot." + X), sk.head("toe." + X)
        w_shin = smoothstep(ank.z + 0.015, ank.z + 0.075, p.z)
        w_toe = smoothstep(ball.y + 0.018, ball.y - 0.018, p.y) * (1 - w_shin)
        return {"shin." + X: w_shin, "toe." + X: w_toe, "foot." + X: 1 - w_shin - w_toe}

    def body_w(self, p):
        sk = self.sk
        j, b, wd = self.spine
        w = _chain_weights(p, j, b, wd)
        # the shoulders' top follows the clavicles
        for X, s in (("L", 1), ("R", -1)):
            if p.x * s > 0:
                c = smoothstep(0.05, 0.15, abs(p.x)) * smoothstep(sk.head("chest").z + 0.06, sk.P["sh_h"] - 0.02, p.z) \
                    * (1 - smoothstep(sk.P["sh_h"] + 0.07, sk.P["sh_h"] + 0.12, p.z)) * 0.85
                if c > 0:
                    w = _mix(w, {"clavicle." + X: 1.0}, c)
        # junctions: near a shoulder the torso takes the arm's weights, near a hip joint the leg's
        for X, s in (("L", 1), ("R", -1)):
            sh = sk.head("arm." + X)
            a = 1 - smoothstep(0.045, 0.12, (p - sh).length)
            if a > 0:
                w = _mix(w, self.arm_w(p, X), a)
            hip = sk.head("thigh." + X)
            d = (p - hip)
            a = (1 - smoothstep(0.05, 0.17, d.length)) * (1 - smoothstep(-0.02, 0.06, d.z))
            if a > 0:
                w = _mix(w, self.leg_w(p, X), a)
        return w

    def weights(self, p, region):
        if region == "~body":
            return self.body_w(p)
        kind, X = region[1:].split(".")
        return {"arm": self.arm_w, "leg": self.leg_w, "foot": self.foot_w}[kind](p, X)


# ------------------------------------------------------------------ the body

def bone_frame(sk, b):
    """The rest frame of a bone (columns: across, along, forward/up) as a 4x4 at its head."""
    h, t, p, axis = sk.bones[b]
    y = (Vector(t) - Vector(h)).normalized()
    z = Vector((0, -1, 0)) if axis == "fwd" else Vector((0, 0, 1))
    z = (z - y * z.dot(y)).normalized()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(h)
    return M


def place(objs, M):
    """Moves parts built around the origin (in a bone's local axes) into place."""
    for o in objs:
        o.matrix_world = M @ o.matrix_world
        _select_only(o)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objs


def hand_parts(sk, X, material, style="fist", size=1.0, bone=None):
    """A hand, rigid on hand.X: "fist" (fighters), "relaxed" (open, fingers together, a little curled) or "grip"
    (curled round a handle that runs forward, for a rifle or ski pole)."""
    m = 1 if X == "L" else -1       # the palm's side in the bone's local x
    bone = bone or "hand." + X
    k = size
    parts = [sphere(0.02 * k, (0, 0.045 * k, 0), bone, material, (1.0, 2.35, 2.1), 16, 10)]
    parts.append(sphere(0.017 * k, (m * 0.002 * k, 0.012 * k, 0), bone, material, (1.2, 1.3, 1.6), 12, 8))   # wrist heel
    if style == "fist":
        parts.append(tube([(m * 0.014 * k, 0.088 * k, -0.04 * k, 0.021 * k), (m * 0.016 * k, 0.091 * k, 0.0, 0.023 * k),
                           (m * 0.014 * k, 0.088 * k, 0.038 * k, 0.021 * k)], bone, material, 12, 0.012, lateral=(1, 0, 0)))
        parts.append(tube([(m * 0.032 * k, 0.075 * k, -0.036 * k, 0.016 * k), (m * 0.034 * k, 0.074 * k, 0.03 * k, 0.017 * k)],
                          bone, material, 10, 0.012, lateral=(1, 0, 0)))
        parts.append(tube([(m * 0.008 * k, 0.03 * k, 0.034 * k, 0.013 * k), (m * 0.024 * k, 0.058 * k, 0.046 * k, 0.012 * k),
                           (m * 0.036 * k, 0.074 * k, 0.04 * k, 0.011 * k)], bone, material, 10, 0.01))
    elif style == "grip":
        parts.append(tube([(m * 0.01 * k, 0.085 * k, -0.038 * k, 0.02 * k), (m * 0.012 * k, 0.09 * k, 0.034 * k, 0.021 * k)],
                          bone, material, 12, 0.012, lateral=(1, 0, 0)))
        parts.append(tube([(m * 0.03 * k, 0.098 * k, -0.034 * k, 0.015 * k), (m * 0.034 * k, 0.1 * k, 0.03 * k, 0.016 * k)],
                          bone, material, 10, 0.012, lateral=(1, 0, 0)))
        parts.append(tube([(m * 0.008 * k, 0.03 * k, 0.034 * k, 0.013 * k), (m * 0.03 * k, 0.062 * k, 0.05 * k, 0.012 * k),
                           (m * 0.042 * k, 0.085 * k, 0.045 * k, 0.011 * k)], bone, material, 10, 0.01))
    else:
        parts.append(tube([(0, 0.078 * k, 0.0, 0.04 * k), (m * 0.006 * k, 0.115 * k, -0.004 * k, 0.036 * k),
                           (m * 0.022 * k, 0.15 * k, -0.01 * k, 0.026 * k), (m * 0.034 * k, 0.168 * k, -0.012 * k, 0.014 * k)],
                          bone, material, 12, 0.012, ell=(0.42, 1.0), lateral=(1, 0, 0)))
        parts.append(tube([(m * 0.006 * k, 0.03 * k, 0.034 * k, 0.013 * k), (m * 0.02 * k, 0.062 * k, 0.05 * k, 0.012 * k),
                           (m * 0.03 * k, 0.088 * k, 0.05 * k, 0.01 * k)], bone, material, 10, 0.01))
    return place(parts, bone_frame(sk, "hand." + X))


def _along(sk, b, t, off=(0, 0, 0)):
    return sk.head(b).lerp(sk.tail(b), t) + Vector(off)


def arm_path(sk, X, grow=0.0, t0=0.0, t1=1.0, shape=1.0):
    """Control points of an arm from the shoulder to the wrist (upper arm then forearm), radius grown by `grow`,
    cut to the fraction [t0, t1] of its length (a short sleeve)."""
    s = 1 if X == "L" else -1
    A, F = "arm." + X, "forearm." + X
    g = grow
    k = shape
    pts = [(_along(sk, A, 0.0, (-0.012 * s, 0.0, 0.006)), 0.046 * k), (_along(sk, A, 0.12, (0.004 * s, 0, 0)), 0.054 * k),
           (_along(sk, A, 0.4, (0, -0.006, 0)), 0.05 * k), (_along(sk, A, 0.7, (0, -0.004, 0)), 0.046 * k),
           (_along(sk, A, 0.95), 0.04 * k), (_along(sk, F, 0.06), 0.039 * k), (_along(sk, F, 0.25, (0, 0.0, 0)), 0.043 * k),
           (_along(sk, F, 0.5), 0.038 * k), (_along(sk, F, 0.8), 0.03 * k), (_along(sk, F, 1.0), 0.026 * k)]
    n = len(pts) - 1
    out = []
    for i, (p, r) in enumerate(pts):
        u = i / n
        if t0 - 1e-6 <= u <= t1 + 1e-6:
            out.append((p.x, p.y, p.z, r + g))
    return out


def leg_path(sk, X, grow=0.0, t1=1.0, shape=1.0):
    s = 1 if X == "L" else -1
    T, S = "thigh." + X, "shin." + X
    k = shape
    g = grow
    pts = [(_along(sk, T, 0.0, (0.0, 0.0, 0.07)), 0.078 * k), (_along(sk, T, 0.08, (0.004 * s, 0.0, 0)), 0.088 * k),
           (_along(sk, T, 0.35, (0.004 * s, -0.004, 0)), 0.08 * k), (_along(sk, T, 0.65, (0.0, -0.004, 0)), 0.066 * k),
           (_along(sk, T, 0.9), 0.054 * k), (_along(sk, S, 0.04), 0.05 * k), (_along(sk, S, 0.2, (0, 0.012, 0)), 0.055 * k),
           (_along(sk, S, 0.38, (0, 0.016, 0)), 0.057 * k), (_along(sk, S, 0.62, (0, 0.008, 0)), 0.045 * k),
           (_along(sk, S, 0.85), 0.036 * k), (_along(sk, S, 1.0), 0.034 * k)]
    n = len(pts) - 1
    return [(p.x, p.y, p.z, r + g) for i, (p, r) in enumerate(pts) if i / n <= t1 + 1e-6]


TORSO = [(0.82, 0.125, 0.075, 0.004, 2.4), (0.85, 0.15, 0.09, 0.008, 2.3), (0.9, 0.162, 0.1, 0.012, 2.3),
         (0.95, 0.172, 0.105, 0.012, 2.3), (1.0, 0.166, 0.1, 0.006, 2.3), (1.06, 0.152, 0.094, 0.0, 2.3),
         (1.12, 0.146, 0.092, -0.004, 2.3), (1.19, 0.152, 0.097, -0.008, 2.4), (1.26, 0.166, 0.104, -0.012, 2.5),
         (1.32, 0.18, 0.108, -0.012, 2.6), (1.38, 0.19, 0.104, -0.008, 2.6), (1.425, 0.184, 0.094, 0.0, 2.4),
         (1.455, 0.14, 0.078, 0.006, 2.3), (1.485, 0.085, 0.062, 0.008, 2.0), (1.505, 0.05, 0.045, 0.008, 2.0)]


def torso_rings(z0=0.0, z1=9.0, grow=0.0, shape=None):
    """The torso's rings between two heights, grown outward (clothes), shaped by {"chest", "waist", "hips"} factors."""
    sh = shape or {}
    out = []
    for z, rx, ry, cy, sq in TORSO:
        if not z0 - 1e-6 <= z <= z1 + 1e-6:
            continue
        f = 1.0
        if z >= 1.2:
            f = sh.get("chest", 1.0)
        elif z >= 1.03:
            f = sh.get("waist", 1.0)
        else:
            f = sh.get("hips", 1.0)
        fy = 1.0 + (f - 1.0) * 0.8
        out.append((z, rx * f + grow, ry * fy + grow, cy, sq))
    return out


def shoe(sk, X, material, sole=None, height=0.155, bulk=1.0, toe_cap=None):
    """A shoe or boot on the foot (the sole on the ground), skinned to shin, foot and toes."""
    x = sk.head("foot." + X).x
    k = bulk
    rings = [(0.012, 0.048 * k, 0.125 * k, -0.047), (0.03, 0.052 * k, 0.13 * k, -0.048), (0.06, 0.052 * k, 0.122 * k, -0.045),
             (0.09, 0.047 * k, 0.098 * k, -0.026), (0.12, 0.044 * k, 0.064, -0.002), (height, 0.043 * k, 0.052, 0.006)]
    if height > 0.17:
        rings.append((height + 0.01, 0.042 * k, 0.05, 0.006))
    parts = [body_loft(rings, "~foot." + X, material, 22, 0, step=0.012, x0=x)]
    if sole:
        parts.append(body_loft([(0.0, 0.051 * k, 0.131 * k, -0.047, 2.6), (0.018, 0.054 * k, 0.134 * k, -0.047, 2.6)],
                               "~foot." + X, sole, 22, 0, x0=x))
    if toe_cap:
        parts.append(sphere(0.05 * k, (x, -0.13 * k, 0.035), "~foot." + X, toe_cap, (1.0, 1.0, 0.72)))
    return parts


def human_body(sk, skin, top, legs, eye_white, iris, hair=None, shoes=None, sole=None, glove=None, sleeves="long",
               hands="fist", shape=None, head=True, shoe_height=0.155, neck_mat=None):
    """A proportioned figure on a Skeleton: a torso in two lofts (trousers up to the belt line, the top above),
    arms and legs as single dense tubes, deltoids, knee caps, a neck, a head, hands and shoes.
    sleeves: "long", "short" (to mid upper arm, skin below) or "none". shape: {"chest", "waist", "hips", "arms",
    "legs", "neck", "hand"} factors."""
    sh = shape or {}
    body_loft(torso_rings(0.8, 1.07, 0.0, sh), "~body", legs, 26, 0, step=0.016)
    body_loft(torso_rings(1.03, 1.51, 0.0, sh), "~body", top, 26, 0, step=0.016)
    nk = sh.get("neck", 1.0)
    tube([(0, 0.012, 1.43, 0.058 * nk), (0, -0.002, 1.5, 0.051 * nk), (0, -0.01, 1.57, 0.049 * nk), (0, -0.012, 1.62, 0.046 * nk)],
         "~body", neck_mat or skin, 18, 0.016)
    if head:
        head_detailed(skin, eye_white, iris, center=(0, -0.012, 1.665), hair=hair)
    ak, lk = sh.get("arms", 1.0), sh.get("legs", 1.0)
    for X, s in (("L", 1), ("R", -1)):
        shp = sk.head("arm." + X)
        arm_top = top if sleeves != "none" else skin
        sphere(0.054 * ak, tuple(shp + Vector((0.006 * s, 0.002, -0.03))), "~arm." + X, arm_top, (1.0, 1.1, 1.2), 20, 12)
        if sleeves == "long":
            tube(arm_path(sk, X, 0.0, shape=ak), "~arm." + X, top, 18, 0.016, lateral=(s, 0, 0))
        else:
            tube(arm_path(sk, X, 0.0, shape=ak), "~arm." + X, skin, 18, 0.016, lateral=(s, 0, 0))
            if sleeves == "short":
                tube(arm_path(sk, X, 0.007, 0.0, 0.34, shape=ak), "~arm." + X, top, 18, 0.016, lateral=(s, 0, 0), caps=(True, False))
        tube(leg_path(sk, X, 0.0, shape=lk), "~leg." + X, legs, 18, 0.016, lateral=(s, 0, 0))
        hand_parts(sk, X, glove or skin, hands, sh.get("hand", 1.0))
        if shoes:
            shoe(sk, X, shoes, sole, shoe_height)


# ------------------------------------------------------------------ animation

class Anim:
    """An action: keys {frame: pose} over a base pose (channels a key leaves out take the base's value), smooth
    auto-clamped interpolation per channel; `loop` makes the curve periodic (the last key is set to the first).
    `hand_on` = {"L": "hand.R"} makes ik_hand.L a point in rest space carried by hand.R (a two-handed grip)."""

    def __init__(self, keys, base=None, loop=False, hand_on=None, arm_pole=None):
        self.keys = keys
        self.base = base or {}
        self.loop = loop
        self.hand_on = hand_on or {}
        self.arm_pole = arm_pole


def _flatten(pose):
    out = {}
    for k, v in pose.items():
        if isinstance(v, (int, float)):
            out[(k, 0)] = float(v)
        else:
            for i, x in enumerate(v):
                out[(k, i)] = float(x)
    return out


def _tangents(ts, vs, loop):
    n = len(ts)
    d = [(vs[i + 1] - vs[i]) / (ts[i + 1] - ts[i]) for i in range(n - 1)]
    m = [0.0] * n
    for i in range(n):
        if 0 < i < n - 1:
            dl, dr, hl, hr = d[i - 1], d[i], ts[i] - ts[i - 1], ts[i + 1] - ts[i]
        elif loop and n > 2:
            dl, dr, hl, hr = d[-1], d[0], ts[-1] - ts[-2], ts[1] - ts[0]
        else:
            continue
        if dl * dr <= 0:
            m[i] = 0.0
        else:
            m[i] = 3 * (hl + hr) / ((2 * hr + hl) / dl + (hr + 2 * hl) / dr)
    return m


def _interp(ts, vs, ms, t):
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    i = 0
    while ts[i + 1] < t:
        i += 1
    h = ts[i + 1] - ts[i]
    u = (t - ts[i]) / h
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return h00 * vs[i] + h10 * h * ms[i] + h01 * vs[i + 1] + h11 * h * ms[i + 1]


def cpos(left, fwd, up):
    """Character space (left, forward, up) to armature space (the model faces -Y)."""
    return Vector((left, -fwd, up))


class Poser:
    """Turns channel values into bone rotations, solving the IK."""

    def __init__(self, arm_obj, sk):
        self.sk = sk
        self.rest, self.rel, self.len, self.parent = {}, {}, {}, {}
        bones = arm_obj.data.bones
        for n in sk.order:
            b = bones[n]
            self.rest[n] = b.matrix_local.copy()
            self.parent[n] = b.parent.name if b.parent else None
            self.len[n] = b.length
        for n in sk.order:
            p = self.parent[n]
            self.rel[n] = self.rest[p].inverted() @ self.rest[n] if p else self.rest[n]

    def fk(self, basis):
        W = {}
        for n in self.sk.order:
            p = self.parent[n]
            W[n] = (W[p] @ self.rel[n] if p else self.rel[n]) @ basis[n]
        return W

    @staticmethod
    def rot(bone, v):
        flex, twist, side = v[:3]
        swing = v[3] if len(v) > 3 else 0.0
        s = -1.0 if bone.endswith(".R") else 1.0
        if bone.startswith("shin"):
            flex = -flex
        m = (Matrix.Rotation(math.radians(flex), 4, "X") @ Matrix.Rotation(math.radians(side * s), 4, "Z")
             @ Matrix.Rotation(math.radians(twist * s), 4, "Y"))
        if swing:
            m = Matrix.Rotation(math.radians(swing * s), 4, "Y") @ m
        return m

    def _parent_world(self, W, b):
        p = self.parent[b]
        return (W[p] @ self.rel[b]) if p else self.rel[b]

    def _set_world_rot(self, W, basis, b, R, weight):
        pw = self._parent_world(W, b).to_3x3()
        q_ik = (pw.inverted() @ R).to_quaternion()
        q_fk = basis[b].to_quaternion()
        if q_fk.dot(q_ik) < 0:
            q_ik.negate()
        q = q_fk.slerp(q_ik, weight) if weight < 1 else q_ik
        basis[b] = q.to_matrix().to_4x4()

    def ik2(self, basis, up, lo, target, pole, weight):
        W = self.fk(basis)
        A = W[up].translation.copy()
        lu, ll = self.len[up], self.len[lo]
        v = target - A
        d = max(abs(lu - ll) + 1e-4, min(v.length, (lu + ll) * 0.9995))
        dr = v.normalized()
        pp = (pole - dr * pole.dot(dr))
        if pp.length < 1e-6:
            pp = dr.orthogonal()
        pp.normalize()
        ca = (lu * lu + d * d - ll * ll) / (2 * lu * d)
        sa = math.sqrt(max(0.0, 1 - ca * ca))
        M = A + (dr * ca + pp * sa) * lu
        T = A + dr * d
        yU, yL = (M - A).normalized(), (T - M).normalized()
        n = dr.cross(pp).normalized()
        if n.dot(W[up].col[0].xyz) < 0:
            n.negate()

        def frame(y):
            x = (n - y * n.dot(y)).normalized()
            return Matrix((x, y, x.cross(y))).transposed()
        self._set_world_rot(W, basis, up, frame(yU), weight)
        W = self.fk(basis)
        self._set_world_rot(W, basis, lo, frame(yL), weight)

    def pose(self, vals, anim):
        sk = self.sk
        basis = {}
        for n in sk.order:
            if n == "root":
                continue
            v = (vals.get((n, 0), 0.0), vals.get((n, 1), 0.0), vals.get((n, 2), 0.0), vals.get((n, 3), 0.0))
            basis[n] = self.rot(n, v) if any(v) else Matrix.Identity(4)
        rp = [vals.get(("root", i), 0.0) for i in range(3)]
        tr = [vals.get(("turn", i), 0.0) for i in range(3)]
        basis["root"] = (Matrix.Translation((rp[0], rp[2], rp[1])) @ Matrix.Rotation(math.radians(tr[1]), 4, "Y")
                         @ Matrix.Rotation(math.radians(tr[0]), 4, "X") @ Matrix.Rotation(math.radians(tr[2]), 4, "Z"))
        # legs
        for X, s in (("L", 1), ("R", -1)):
            w = vals.get(("ikw." + X, 0), 0.0)
            if w <= 1e-4 or ("ik_foot." + X, 0) not in vals:
                continue
            f = [vals.get(("ik_foot." + X, i), 0.0) for i in range(5)]
            ank = cpos(f[0], f[1], f[2])
            yaw = math.radians(f[4]) * s
            pole = Matrix.Rotation(yaw, 3, "Z") @ Vector((0.12 * s, -1.0, 0.0))
            self.ik2(basis, "thigh." + X, "shin." + X, ank, pole, w)
            W = self.fk(basis)
            R = (Matrix.Rotation(yaw, 3, "Z") @ Matrix.Rotation(math.radians(-f[3]), 3, "X")
                 @ self.rest["foot." + X].to_3x3())
            fk_foot = basis["foot." + X].copy()
            self._set_world_rot(W, basis, "foot." + X, R, w)
            # the channel's own foot rotation is added on top (ankle roll, extra flex)
            basis["foot." + X] = basis["foot." + X] @ fk_foot
        # arms, the right first (a left hand may ride the right hand); then the hand's aim
        for X, s in (("R", -1), ("L", 1)):
            w = vals.get(("ikh." + X, 0), 0.0)
            if w > 1e-4 and ("ik_hand." + X, 0) in vals:
                h = [vals.get(("ik_hand." + X, i), 0.0) for i in range(3)]
                W = self.fk(basis)
                if X in anim.hand_on:
                    b = anim.hand_on[X]
                    tgt = W[b] @ self.rest[b].inverted() @ cpos(*h)
                else:
                    tgt = cpos(*h)
                ap = anim.arm_pole.get(X) if isinstance(anim.arm_pole, dict) else anim.arm_pole
                pole = Vector(ap or (0.35, 1.0, -0.4))   # elbows (lateral +, back +, up +)
                pole = Vector((pole.x * s, pole.y, pole.z))
                hand_world = W["hand." + X].to_3x3()
                self.ik2(basis, "arm." + X, "forearm." + X, tgt, pole, w)
                if X in anim.hand_on and anim.hand_on[X].startswith("hand"):
                    W = self.fk(basis)
                    self._set_world_rot(W, basis, "hand." + X, hand_world, w)
            w = vals.get(("hdw." + X, 0), 0.0)
            if w > 1e-4 and ("hand_dir." + X, 0) in vals:
                # the hand's length along a direction (yaw left +, pitch up +, in ground space), thumb up, rolled
                yaw, pitch, roll = [math.radians(vals.get(("hand_dir." + X, i), 0.0)) for i in range(3)]
                y = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
                z = Vector((0, 0, 1))
                z = (z - y * z.dot(y)).normalized()
                z = Matrix.Rotation(roll * -s, 3, y) @ z
                R = Matrix((y.cross(z), y, z)).transposed()
                W = self.fk(basis)
                self._set_world_rot(W, basis, "hand." + X, R, w)
        return basis


def _eval_anim(anim):
    keys = {f: dict(anim.base, **p) for f, p in anim.keys.items()}
    fr = sorted(keys)
    if anim.loop:
        keys[fr[-1]] = dict(keys[fr[0]])
    flat = {f: _flatten(keys[f]) for f in fr}
    chans = set()
    for f in fr:
        chans |= set(flat[f])
    base = _flatten(anim.base)
    curves = {}
    for c in chans:
        vs = []
        for f in fr:
            if c in flat[f]:
                vs.append(flat[f][c])
            elif c in base:
                vs.append(base[c])
            elif c[0].startswith("ikw") or c[0].startswith("ikh"):
                vs.append(0.0)
            elif c[0].startswith("ik_"):
                # a target missing from a key: hold the nearest key that has it
                near = min((g for g in fr if c in flat[g]), key=lambda g: abs(g - f))
                vs.append(flat[near][c])
            else:
                vs.append(0.0)   # a rotation left out: the rest pose
        curves[c] = (fr, vs, _tangents(fr, vs, anim.loop))
    return fr, curves


def keys_new(arm_obj, poser, name, anim, fps):
    """Samples an Anim at every frame, solves the IK and keys quaternions (and the root's location)."""
    fr, curves = _eval_anim(anim)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm_obj.animation_data.action = act
    pb = arm_obj.pose.bones
    prev = {}
    data = {n: [] for n in poser.sk.order}
    for f in range(fr[0], fr[-1] + 1):
        vals = {c: _interp(ts, vs, ms, f) for c, (ts, vs, ms) in curves.items()}
        basis = poser.pose(vals, anim)
        for n in poser.sk.order:
            q = basis[n].to_quaternion()
            if n in prev and prev[n].dot(q) < 0:
                q.negate()
            prev[n] = q
            data[n].append((f, q, basis[n].translation.copy()))
    for n in poser.sk.order:
        b = pb[n]
        for f, q, t in data[n]:
            b.rotation_quaternion = q
            b.keyframe_insert("rotation_quaternion", frame=f)
            if n == "root":
                b.location = t
                b.keyframe_insert("location", frame=f)
    tr = arm_obj.animation_data.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, 1, act)
    arm_obj.animation_data.action = None


# ------------------------------------------------------------------ locomotion

def foot_ground(left, fwd, pitch, sk, pivot=None):
    """The ankle target for a foot whose sole touches the ground at `fwd` (the ankle's flat position), rolled
    by `pitch` (+: on the heel, toes up; -: on the ball, heel up)."""
    P = sk.P
    a0 = Vector((0.0, 0.0, P["ankle_h"]))
    if pitch >= 0:
        piv = Vector((0.0, -P["heel_y"] + 0.005, 0.0))   # heel (behind the ankle), forward = +y here
    else:
        piv = Vector((0.0, -P["ball_y"], 0.0))
    R = Matrix.Rotation(math.radians(pitch), 3, "X")  # in (lateral, fwd, up) space: toes up = +pitch
    rel = R @ (a0 - Vector((0, piv.y, 0)))
    return (left, fwd + piv.y + rel.y, rel.z)


def gait(sk, frames, stride, duty, lift=0.12, lift_at=0.45, strike=18.0, push=35.0, bob=0.025, drop=-0.03,
         width=None, toe_out=6.0, pelvis_yaw=6.0, pelvis_roll=4.0, sway=0.012, shoulder_yaw=6.0, lean=4.0,
         arm_swing=25.0, arm_out=8.0, elbow=30.0, elbow_swing=20.0, arm_lag=0.04, head_hold=1.0, base=None,
         extra=None, step=1, reach=0.5):
    """A walk or run cycle in place (the stance foot slides back at ground speed = stride / cycle) as a looping Anim
    with a key every `step` frames: heel strike, foot flat, heel off, toe off, swing with the knee raised; pelvis bob,
    sway and rotation, chest counter-rotation, arm swing, a steady head. Frame 1 = the left heel strikes.
    stride: metres per cycle (two steps); duty: the share of the cycle a foot is on the ground (walk > 0.5, run
    < 0.5); bob > 0 lifts the hips over the stance leg (walk), < 0 drops them into it (run). `base` gives the
    posture (arms, spine) the cycle rides on; extra(phase, pose) may return more channels for each key."""
    P = sk.P
    b = base or {}
    width = P["hip_w"] + 0.01 if width is None else width
    S = stride * duty
    L = P["hip_h"] - P["ankle_h"]
    keys = {}

    def add(k, v):
        o = b.get(k, (0, 0, 0))
        return tuple(o[i] + v[i] for i in range(3))
    for i in range(0, frames + 1, step):
        ph = i / frames
        pose = dict(b)
        feet = {}
        for X, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            q = (ph + off) % 1.0                    # 0 = this foot's heel strike
            if q < duty:
                u = q / duty
                fwd = S * reach - S * u
                if u < 0.15:
                    pitch = strike * (1 - smoothstep(0.0, 0.15, u))
                elif u > 0.6:
                    pitch = -push * smoothstep(0.6, 1.0, u)
                else:
                    pitch = 0.0
                a = foot_ground(width * s, fwd, pitch, sk)
                toe = max(0.0, -pitch)
            else:
                v = (q - duty) / (1 - duty)
                a0 = foot_ground(width * s, -S * (1 - reach), -push, sk)
                a1 = foot_ground(width * s, S * reach, strike, sk)
                h00, h10, h01, h11 = 2 * v ** 3 - 3 * v ** 2 + 1, v ** 3 - 2 * v ** 2 + v, -2 * v ** 3 + 3 * v ** 2, v ** 3 - v ** 2
                vg = -stride * (1 - duty)
                fwd = h00 * a0[1] + h10 * vg * 0.5 + h01 * a1[1] + h11 * vg * 0.15
                z = a0[2] + (a1[2] - a0[2]) * smoothstep(0.0, 1.0, v)
                z += lift * math.sin(math.pi * min(1.0, v ** (math.log(0.5) / math.log(lift_at))))
                pitch = -push * (1 - smoothstep(0.0, 0.4, v)) + (strike + 5) * smoothstep(0.3, 0.85, v) - 5 * smoothstep(0.85, 1.0, v)
                a = (width * s, fwd, z)
                toe = push * 0.7 * (1 - smoothstep(0.0, 0.35, v))
            feet[X] = a
            pose["ik_foot." + X] = (a[0], a[1], a[2], pitch, toe_out)
            pose["ikw." + X] = 1.0
            pose["toe." + X] = add("toe." + X, (toe, 0, 0))
        c1 = math.cos(2 * math.pi * ph)                      # +1 when the left leg is forward
        mid = math.cos(2 * math.pi * (ph - duty / 2))        # +1 at the left foot's mid-stance
        # the hips: bob, and never ask a leg for more than it has (a smooth minimum lowers them)
        z = drop + bob * math.cos(4 * math.pi * (ph - duty / 2))
        lim = 1e9
        for X, a in feet.items():
            dx = a[0] - (P["hip_w"] if X == "L" else -P["hip_w"])
            lim = min(lim, math.sqrt(max(0.0, (0.98 * L) ** 2 - dx * dx - a[1] * a[1])) + a[2] - P["ankle_h"] - L)
        k = 0.02
        z = -k * math.log(math.exp(-z / k) + math.exp(-lim / k))
        r = b.get("root", (0, 0, 0))
        pose["root"] = (r[0] + sway * mid, r[1], r[2] + z)
        pose["hips"] = add("hips", (0.0, -pelvis_yaw * c1, pelvis_roll * mid))
        pose["spine"] = add("spine", (lean * 0.5, pelvis_yaw * 0.5 * c1, -pelvis_roll * 0.6 * mid))
        pose["chest"] = add("chest", (lean * 0.5, (pelvis_yaw * 0.5 + shoulder_yaw) * c1, -pelvis_roll * 0.3 * mid))
        pose["neck"] = add("neck", (-lean * 0.4, -shoulder_yaw * 0.5 * head_hold * c1, -pelvis_roll * 0.1 * mid))
        pose["head"] = add("head", (-lean * 0.5, -shoulder_yaw * 0.5 * head_hold * c1, 0.0))
        for X, sgn in (("L", -1), ("R", 1)):
            sw_ = sgn * math.cos(2 * math.pi * (ph - arm_lag))   # the arm swings against its own side's leg
            pose["arm." + X] = add("arm." + X, (arm_swing * sw_, 0.0, arm_out))
            pose["forearm." + X] = add("forearm." + X, (elbow + elbow_swing * max(0.0, sw_) - elbow_swing * 0.25 * max(0.0, -sw_), 0.0, 0.0))
        if extra:
            pose.update(extra(ph, pose))
        keys[i + 1] = pose
    return Anim(keys, loop=True)


# ------------------------------------------------------------------ rig and export

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for a in list(bpy.data.armatures):
        bpy.data.armatures.remove(a)


def keys(arm_obj, name, frames):
    """Legacy: linear Euler keys per bone (the robots' rig)."""
    pb = arm_obj.pose.bones
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm_obj.animation_data.action = act
    for f in sorted(frames):
        for b in pb:
            b.rotation_euler = (0, 0, 0)
            b.location = (0, 0, 0)
        for bone, v in frames[f].items():
            if bone.startswith("@"):
                pb[bone[1:]].location = v
            else:
                pb[bone].rotation_euler = tuple(math.radians(a) for a in v)
        for b in pb:
            b.keyframe_insert("rotation_euler", frame=f)
            b.keyframe_insert("location", frame=f)
    tr = arm_obj.animation_data.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, 1, act)
    arm_obj.animation_data.action = None


def _bind(meshes, sk):
    """Vertex groups: rigid parts get one bone, smooth regions the Skinner's weights."""
    skin = Skinner(sk) if sk else None
    for o in meshes:
        tagv = o["bone"]
        mw = o.matrix_world
        if not tagv.startswith("~"):
            vg = o.vertex_groups.new(name=tagv)
            vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
            continue
        groups = {}
        for v in o.data.vertices:
            w = skin.weights(mw @ v.co, tagv)
            tot = sum(w.values())
            for b, x in w.items():
                if x / tot < 0.004:
                    continue
                if b not in groups:
                    groups[b] = o.vertex_groups.new(name=b)
                groups[b].add([v.index], x / tot, "REPLACE")


def rig_export(name, out_dir, actions, scale=1.0, skeleton=None, fps=None):
    """Binds every mesh in the scene to a new armature, keys `actions` and exports name.glb.
    With a Skeleton: smooth skinning and Anim actions ({name: Anim}). Without: the legacy rigid rig from BONES
    with Euler actions ({name: {frame: {bone: (rx, ry, rz) degrees, or "@bone": location}}})."""
    if fps:
        bpy.context.scene.render.fps = fps
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm_obj = active()
    arm_obj.name = name + "_rig"
    eb = arm_obj.data.edit_bones
    eb.remove(eb[0])
    if skeleton:
        for n, (h, t, p, axis) in skeleton.bones.items():
            b = eb.new(n)
            b.head, b.tail = h, t
            b.align_roll((0, -1, 0) if axis == "fwd" else (0, 0, 1))
            if p:
                b.parent = eb[p]
    else:
        for n, (h, t, p) in BONES.items():
            b = eb.new(n)
            b.head, b.tail = h, t
            if p:
                b.parent = eb[p]
    bpy.ops.object.mode_set(mode="OBJECT")
    _bind(meshes, skeleton)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    mesh = active()
    mesh.name = name
    mod = mesh.modifiers.new("rig", "ARMATURE")
    mod.object = arm_obj
    mesh.parent = arm_obj
    arm_obj.animation_data_create()
    if skeleton:
        for b in arm_obj.pose.bones:
            b.rotation_mode = "QUATERNION"
        poser = Poser(arm_obj, skeleton)
        for aname, anim in actions.items():
            keys_new(arm_obj, poser, aname, anim, fps)
    else:
        for b in arm_obj.pose.bones:
            b.rotation_mode = "XYZ"
        for aname, frames in actions.items():
            keys(arm_obj, aname, frames)
    arm_obj.scale = (scale, scale, scale)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    arm_obj.select_set(True)
    mesh.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True)
    tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    print("exported", name, "tris", tris)
