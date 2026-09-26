"""Whisker Alley's animals: the ginger tom (a tabby with a torn ear), the lady cat and the bulldog. Each is one
smooth skinned mesh (a metaball body with tube limbs, voxel-fused) on a real quadruped skeleton: a spine chain,
neck, head, jaw, ears, eyes, shoulder blade / upper / lower leg / paw at the front, thigh / shin / hock / paw at
the back, and a multi-bone tail. The legs are IK-driven with hinge knees, so paws plant on the ground; the
animations are procedural gait cycles and Bezier key poses, baked into one glTF animation per action.
Deterministic; output CC BY-SA 4.0; provenance: this script and creature_kit.py.
Run: blender -b --factory-startup -P tools/blender/whisker_animals.py -- godot/games/whisker/art/models
Feet at z = 0, facing -Y (the view turns them to face left or right).
Cat actions: idle, walk, run (a gallop), jump (take-off into a tuck, played once), fall, swim, catch, die, cheer
(the serenade: sitting up, singing), sit, hurt. The lady cat's idle is a seated idle.
Bulldog actions: idle (asleep, lying down), stand, walk (a heavy trot), run (a gallop), bark (brace and bark).
"""
import bpy, math, os, sys
from mathutils import Vector, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import creature_kit as K
from creature_kit import mat, sphere, cone, rod, tube, Blob, fuse, paint, Rig, smooth01, ss, mix

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
only = sys.argv[sys.argv.index("--") + 2].split(",") if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 2 else None
os.makedirs(out_dir, exist_ok=True)
S = math.sin
C = math.cos
TAU = 2 * math.pi


def side_exclude(rig):
    """Keeps each side's leg bones off the other side of the body."""
    ex = {}
    for b in rig.pb:
        n = b.name
        if n.endswith("L"):
            ex[n] = lambda co: co.x < -0.012
        elif n.endswith("R"):
            ex[n] = lambda co: co.x > 0.012
    return ex


# ====================================================================== the four-legged rig
class Quad:
    """Leg bookkeeping for a quadruped rig: IK targets and paw geometry."""

    LEGS = ("fL", "fR", "bL", "bR")

    def __init__(self, rig):
        self.rig = rig
        self.v = {}
        for leg in self.LEGS:
            h, t = rig.rest_head("paw_" + leg), rig.rest_tail("paw_" + leg)
            self.v[leg] = t - h

    def plant(self, pose, leg, fwd=0.0, up=0.0, pitch=0.0, side=0.0):
        """Places a paw: the TOES move by (side, fwd, up) from rest (fwd > 0 is backwards, +Y) and the paw pitches
        by `pitch` degrees about its toes (+ lifts the heel)."""
        v = self.v[leg]
        R = Euler((math.radians(pitch), 0, 0)).to_matrix()
        off = v - R @ v + Vector((side, fwd, up))
        pose["@ik_" + leg] = tuple(off)
        pose["ik_" + leg] = (pitch, 0, 0)


def quad_bones(P):
    """P: named joint positions (right-side x is mirrored). Returns the bone table for Rig()."""
    b = {
        "root": ((0, 0, 0), (0, 0, P["root_len"]), None, {"nodeform"}),
        "body": (P["cog"], P["cog"] + Vector((0, -0.06, 0)), "root", {"nodeform"}),
        "pelvis": (P["cog"], P["rump"], "body"),
        "spine1": (P["cog"], P["mid"], "body"),
        "spine2": (P["mid"], P["withers"], "spine1", {"connect"}),
        "neck": (P["withers"], P["skull"], "spine2", {"connect"}),
        "head": (P["skull"], P["snout"], "neck", {"connect"}),
        "jaw": (P["jaw"], P["chin"], "head", {"nodeform"}),
    }
    for s, sx in (("L", 1), ("R", -1)):
        m = lambda v: Vector((v[0] * sx, v[1], v[2]))
        b["ear_" + s] = (m(P["ear0"]), m(P["ear1"]), "head", {"nodeform"})
        b["eye_" + s] = (m(P["eye"]), m(P["eye"]) + Vector((0, -0.03, 0)), "head", {"nodeform"})
        b["shoulder_f" + s] = (m(P["scap"]), m(P["shoulder"]), "spine2")
        b["upper_f" + s] = (m(P["shoulder"]), m(P["elbow"]), "shoulder_f" + s, {"connect"})
        b["lower_f" + s] = (m(P["elbow"]), m(P["wrist"]), "upper_f" + s, {"connect"})
        b["paw_f" + s] = (m(P["wrist"]), m(P["ftoe"]), "lower_f" + s, {"connect"})
        b["upper_b" + s] = (m(P["hip"]), m(P["knee"]), "pelvis")
        b["lower_b" + s] = (m(P["knee"]), m(P["hock"]), "upper_b" + s, {"connect"})
        b["foot_b" + s] = (m(P["hock"]), m(P["ankle"]), "lower_b" + s, {"connect"})
        b["paw_b" + s] = (m(P["ankle"]), m(P["btoe"]), "foot_b" + s, {"connect"})
        b["ik_f" + s] = (m(P["wrist"]), m(P["ftoe"]), None, {"nodeform"})
        b["ik_b" + s] = (m(P["ankle"]), m(P["btoe"]), None, {"nodeform"})
    prev = "pelvis"
    for i in range(len(P["tail"]) - 1):
        b[f"tail{i}"] = (P["tail"][i], P["tail"][i + 1], prev, {"connect"} if i else set())
        prev = f"tail{i}"
    return b


def make_quad_rig(name, P):
    rig = Rig(name, quad_bones(P))
    for s in ("L", "R"):
        rig.ik("lower_f" + s, "ik_f" + s, 2, hinge=("upper_f" + s, "lower_f" + s), copy_rot="paw_f" + s, tag="f" + s)
        rig.ik("foot_b" + s, "ik_b" + s, 3, hinge=("upper_b" + s, "lower_b" + s, "foot_b" + s), copy_rot="paw_b" + s,
               stiff={"foot_b" + s: 0.5}, tag="b" + s)
    return rig


def tail_names(P):
    return [f"tail{i}" for i in range(len(P["tail"]) - 1)]


# ====================================================================== the cats
CAT = {
    "root_len": 0.1,
    "cog": Vector((0, 0.02, 0.275)), "rump": Vector((0, 0.15, 0.27)), "mid": Vector((0, -0.075, 0.285)),
    "withers": Vector((0, -0.15, 0.3)), "skull": Vector((0, -0.215, 0.375)), "snout": Vector((0, -0.34, 0.425)),
    "jaw": Vector((0, -0.25, 0.385)), "chin": Vector((0, -0.33, 0.375)),
    "ear0": Vector((0.055, -0.245, 0.49)), "ear1": Vector((0.078, -0.25, 0.575)),
    "eye": Vector((0.044, -0.34, 0.44)),
    "scap": Vector((0.045, -0.1, 0.33)), "shoulder": Vector((0.062, -0.15, 0.21)),
    "elbow": Vector((0.066, -0.108, 0.125)), "wrist": Vector((0.064, -0.13, 0.03)), "ftoe": Vector((0.064, -0.172, 0.012)),
    "hip": Vector((0.062, 0.125, 0.26)), "knee": Vector((0.07, 0.06, 0.15)), "hock": Vector((0.07, 0.14, 0.07)),
    "ankle": Vector((0.068, 0.115, 0.022)), "btoe": Vector((0.068, 0.075, 0.012)),
    "tail": [Vector(p) for p in ((0, 0.17, 0.3), (0, 0.225, 0.32), (0, 0.268, 0.37), (0, 0.284, 0.435), (0, 0.28, 0.5),
                                  (0, 0.262, 0.56), (0, 0.232, 0.6), (0, 0.198, 0.615))],
}


def build_cat(name, fur_c, stripe_c, eye_c, tabby=True, torn=True, bow=False, lady=False):
    K.clear_scene()
    K.MATS.clear()
    P = dict(CAT)
    fur = mat(name + "_fur", tuple(x * 0.93 for x in fur_c), 0.85, sheen=0.4)  # the ears: shaded like the fur
    dark = mat(name + "_stripes", stripe_c, 0.85, sheen=0.3)
    cream = mat(name + "_cream", (0.98, 0.92, 0.82) if not lady else (1.0, 0.98, 0.97), 0.85, sheen=0.4)
    pink = mat("cat_pink", (0.95, 0.52, 0.58), 0.45)
    eye = mat(name + "_eye", eye_c, 0.08, coat=1.0, emit=0.35)
    pupil = mat("cat_pupil", (0.01, 0.01, 0.01), 0.05, coat=1.0)
    shine = mat("cat_shine", (1, 1, 1), 0.1, emit=1.5)
    whisk = mat("cat_whisker", (0.96, 0.95, 0.9), 0.4)
    mouth = mat("cat_mouth", (0.35, 0.08, 0.1), 0.6)

    # ---------------------------------------------------------------- the body: torso, neck and head blobs
    body = Blob(name + "_torso", res=0.006)
    body.ell((0, -0.105, 0.265), 0.094, 0.105, 0.1, rot=(-8, 0, 0))  # chest
    body.ell((0, 0.0, 0.278), 0.097, 0.13, 0.092, rot=(-3, 0, 0))  # ribs and loin: a gentle arch
    body.ell((0, 0.115, 0.268), 0.09, 0.09, 0.09, rot=(10, 0, 0))  # rump
    body.ell((0, 0.04, 0.228), 0.07, 0.1, 0.05)  # belly
    head = Blob(name + "_head", res=0.005)
    head.ell((0, -0.265, 0.43), 0.104, 0.09, 0.086)  # skull
    head.ell((0, -0.278, 0.458), 0.084, 0.074, 0.062)  # brow and crown
    for s in (-1, 1):
        head.ell((0.052 * s, -0.298, 0.4), 0.058, 0.052, 0.048)  # cheeks
        head.ball((0.021 * s, -0.342, 0.398), 0.028)  # whisker pads
    head.ell((0, -0.33, 0.422), 0.026, 0.03, 0.024, rot=(-25, 0, 0))  # bridge of the nose
    neck = tube([(0, -0.1, 0.28), (0, -0.165, 0.32), (0, -0.215, 0.375), (0, -0.245, 0.41)], [0.08, 0.077, 0.072, 0.068], "neck")
    limbs = []
    for sx in (1, -1):
        m = lambda v: (v[0] * sx, v[1], v[2])
        # front leg: shoulder buried in the chest, elbow tucked in, slim forearm, a round paw
        limbs.append(tube([m((0.05, -0.12, 0.27)), m((0.062, -0.15, 0.21)), m((0.066, -0.108, 0.125)),
                           m((0.065, -0.12, 0.075)), m((0.064, -0.132, 0.034))], [0.052, 0.046, 0.034, 0.028, 0.025], "fleg"))
        limbs.append(Blob("fpaw", res=0.004).ell(m((0.064, -0.148, 0.02)), 0.031, 0.038, 0.021))
        # hind leg: a big haunch, the long shin and the hock
        limbs.append(Blob("haunch", res=0.006).ell(m((0.058, 0.1, 0.215)), 0.05, 0.075, 0.088, rot=(24, 0, 0)))
        limbs.append(tube([m((0.055, 0.1, 0.24)), m((0.07, 0.06, 0.15)), m((0.071, 0.105, 0.105)), m((0.07, 0.14, 0.07)),
                           m((0.069, 0.117, 0.026))], [0.05, 0.036, 0.029, 0.023, 0.021], "bleg"))
        limbs.append(Blob("bpaw", res=0.004).ell(m((0.068, 0.098, 0.019)), 0.03, 0.04, 0.02))
    tail = tube(P["tail"], [0.034, 0.031, 0.029, 0.027, 0.026, 0.025, 0.024, 0.021] if not lady else
                [0.035, 0.036, 0.037, 0.037, 0.036, 0.034, 0.031, 0.024], "tail")

    def is_tail(c):
        return ss(c.y, 0.17, 0.19) * ss(c.z, 0.28, 0.3)

    def cream_amount(c, n):
        paws = ss(c.z, 0.048, 0.03) * (1 - is_tail(c))
        belly = ss(-n.z, 0.3, 0.6) * ss(c.z, 0.26, 0.225) * ss(abs(c.y + 0.01), 0.13, 0.09)
        bib = ss(-c.y, 0.13, 0.17) * ss(c.z, 0.355, 0.31) * ss(-n.y, 0.0, 0.3) * ss(abs(c.x), 0.075, 0.045) * ss(-c.y, 0.31, 0.29)
        muzzle = ss(-c.y, 0.31, 0.325) * ss(c.z, 0.425, 0.41)
        chin = ss(-c.y, 0.25, 0.28) * ss(c.z, 0.39, 0.37)
        inner_leg = ss(abs(c.x), 0.055, 0.04) * ss(c.z, 0.2, 0.15)
        return max(paws, belly, bib, muzzle, chin, 0.7 * inner_leg)

    def stripe_amount(c, n):
        if not tabby:
            return 0.0
        tail = is_tail(c)
        if tail > 0.5:
            return max(ss(c.z, 0.57, 0.6), ss(S(TAU * (c.z * 11.0 + c.y * 2)), 0.15, 0.55))  # rings and a dark tip
        back = ss(c.y, -0.15, -0.12) * ss(c.y, 0.2, 0.17) * ss(c.z, 0.22, 0.26) * ss(n.z, -0.45, -0.2)
        band = S(TAU * (c.y * 9.0 + 0.25 * S(c.z * 30 + c.y * 10) + 0.15)) + 0.9 * max(0.0, c.z - 0.3)
        st = back * ss(band, 0.3, 0.6)
        spine = ss(c.z, 0.345, 0.37) * ss(abs(c.x), 0.03, 0.015) * ss(c.y, -0.15, -0.1) * ss(c.y, 0.2, 0.15)  # a dark line down the spine
        legs = ss(abs(c.x), 0.045, 0.055) * ss(c.z, 0.08, 0.1) * ss(c.z, 0.22, 0.2) * ss(S(TAU * c.z * 11.0 + 1.0), 0.45, 0.8)
        m_mark = ss(-c.y, 0.22, 0.24) * ss(c.z, 0.465, 0.48) * ss(abs(c.x), 0.06, 0.05) * ss(S(TAU * (c.x * 30.0 + 0.25)), 0.2, 0.55)
        cheek = ss(-c.y, 0.22, 0.24) * ss(abs(c.x), 0.08, 0.09) * ss(c.z, 0.4, 0.41) * ss(c.z, 0.465, 0.455) * ss(S(TAU * c.z * 36.0), 0.25, 0.6)
        return max(st, spine * 0.8, legs, m_mark, cheek)

    base_c, deep_c, cream_c = fur_c, stripe_c, ((0.98, 0.92, 0.82) if not lady else (1.0, 0.985, 0.975))

    def colour(c, n):
        shade = 0.9 + 0.1 * ss(n.z, -0.6, 0.6)  # a touch darker underneath, like the fur's own shadow
        col = mix(base_c, deep_c, stripe_amount(c, n))
        if lady:
            col = mix(col, (0.86, 0.84, 0.86), 0.5 * is_tail(c) * ss(c.z, 0.5, 0.62) + 0.25 * ss(c.z, 0.33, 0.37) * ss(abs(c.x), 0.05, 0.02))
        col = mix(col, cream_c, cream_amount(c, n))
        return tuple(x * shade for x in col)

    skin = fuse([body, head, neck, tail] + limbs, name, voxel=0.004, smooth=4, faces=8000)
    K.paint_vc(skin, colour, K.vc_mat(name + "_fur", 0.85, sheen=0.5))

    # ---------------------------------------------------------------- rigid parts, placed on the surface
    parts = []
    face_y = lambda x, z: K.surface(skin, (x, -1, z), (0, 1, 0))[0].y
    eyez = P["eye"].z
    eyey = face_y(P["eye"].x, eyez) + 0.013
    P["eye"] = Vector((P["eye"].x, eyey, eyez))
    for s, side in ((1, "L"), (-1, "R")):
        ex, ey, ez = P["eye"].x * s, P["eye"].y, P["eye"].z
        parts.append(sphere(0.03, (ex, ey, ez), "eye_" + side, eye, (1.0, 0.62, 1.12), rot=(0, 0, -16 * s)))
        parts.append(sphere(0.022, (ex + 0.002 * s, ey - 0.01, ez), "eye_" + side, pupil, (0.3 if not lady else 0.6, 0.45, 1.0)))
        parts.append(sphere(0.007, (ex + 0.01 * s, ey - 0.022, ez + 0.012), "eye_" + side, shine))
        if lady:  # lashes: three little flicks at the outer corner
            for k in range(3):
                parts.append(rod(0.0024, (ex + (0.016 + 0.006 * k) * s, ey - 0.006, ez + 0.02 - 0.005 * k),
                                 (ex + (0.036 + 0.008 * k) * s, ey - 0.002, ez + 0.034 - 0.008 * k), "eye_" + side, pupil, 0.0012, 5))
        # ears: flattened cones on their own bones, pink inside; the tom's left one torn
        top = K.surface(skin, (P["ear0"].x * s, P["ear0"].y, 1.0), (0, 0, -1))[0]
        e0 = Vector((P["ear0"].x * s, P["ear0"].y, top.z - 0.012))
        P["ear0"] = Vector((P["ear0"].x, P["ear0"].y, e0.z))
        P["ear1"] = Vector((P["ear1"].x, P["ear1"].y, e0.z + 0.085))
        ear = cone(0.048, 0.004, 0.105, e0 + Vector((0.012 * s, 0, 0.042)), "ear_" + side, fur, rot=(6, 16 * s, 0),
                   verts=16, scale=(1, 0.42, 1))
        inner = cone(0.033, 0.003, 0.072, e0 + Vector((0.011 * s, -0.01, 0.036)), "ear_" + side, pink, rot=(6, 16 * s, 0),
                     verts=12, scale=(1, 0.3, 1))
        if torn and s == 1:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.017, location=e0 + Vector((0.038, 0, 0.066)))
            cutter = K.active()
            for o in (ear, inner):
                bo = o.modifiers.new("notch", "BOOLEAN")
                bo.operation = "DIFFERENCE"
                bo.object = cutter
                K.select_only([o])
                bpy.ops.object.modifier_apply(modifier=bo.name)
            bpy.data.objects.remove(cutter)
        parts += [ear, inner]
        # whiskers from the pads
        pad = K.surface(skin, (0.03 * s, -1, 0.398), (0, 1, 0))[0]
        for k in (-1, 0, 1):
            parts.append(rod(0.0018, pad + Vector((0, 0.006, 0.007 * k)), pad + Vector((0.13 * s, 0.02 - 0.012 * k, 0.012 + 0.028 * k)),
                             "head", whisk, 0.0007, 5, caps=False))
        if not lady:  # brows: the tom's are a little stern
            b0 = K.surface(skin, (0.022 * s, -1, eyez + 0.035), (0, 1, 0))[0]
            b1 = K.surface(skin, (0.062 * s, -1, eyez + 0.03), (0, 1, 0))[0]
            parts.append(rod(0.0035, b0 + Vector((0, 0.002, 0)), b1 + Vector((0, 0.002, 0)), "head", dark, 0.0025, 6))
    nose = K.surface(skin, (0, -1, 0.414), (0, 1, 0))[0]
    parts.append(sphere(0.014, nose + Vector((0, 0.004, 0.0)), "head", pink, (1.3, 0.8, 0.85)))
    lip = K.surface(skin, (0, -1, 0.385), (0, 1, 0))[0]
    parts.append(sphere(0.02, lip + Vector((0, 0.03, -0.004)), "head", mouth, (1.1, 1.0, 0.8)))  # inside the mouth
    parts.append(sphere(0.024, lip + Vector((0, 0.016, -0.016)), "jaw", cream, (1.05, 1.1, 0.6)))  # chin
    P["chin"] = lip + Vector((0, 0.005, -0.012))
    if bow:
        ribbon = mat("bow", (1.0, 0.3, 0.55), 0.35, coat=0.6)
        bt = K.surface(skin, (0.05, -0.27, 1.0), (0, 0, -1))[0]
        for s in (-1, 1):
            parts.append(sphere(0.032, bt + Vector((0.032 * s, 0, 0.012 - 0.006 * s)), "head", ribbon, (1.45, 0.55, 0.9),
                                rot=(0, 25 * s, 0)))
        parts.append(sphere(0.015, bt + Vector((0, -0.004, 0.012)), "head", ribbon))
        collar = mat("lady_collar", (0.95, 0.3, 0.55), 0.35, coat=0.6)
        gold = mat("lady_bell", (1.0, 0.78, 0.3), 0.2, coat=0.8)
        ring, rad, R = K.collar(skin, (0, -0.19, 0.345), 42, 0.009, "neck", collar, snug=0.1)
        parts.append(ring)
        parts.append(sphere(0.014, Vector((0, -0.19, 0.345)) + R @ Vector((0, -rad - 0.01, 0)), "neck", gold))

    rig = make_quad_rig(name, P)
    ex = side_exclude(rig)
    for t in tail_names(P):
        ex[t] = lambda co: co.y < 0.15
    for b in ("head", "neck"):
        ex[b] = lambda co: co.y > -0.08
    ex["pelvis"] = lambda co: co.y < -0.08
    K.skin(skin, rig, smooth_iter=4, exclude=ex)
    body = K.assemble(name, skin, rig, parts)
    cat_actions(rig, P, lady)
    K.export(name, rig, body, out_dir)


# ---------------------------------------------------------------------- cat animation
def tail_pose(p, names, t, sway=0.0, lift=0.0, curl=0.0, lag=0.12, freq=1.0, flick=0.0, wave_up=0.0):
    """An S-wave down the tail: `sway` degrees side to side and `wave_up` degrees up and down (what the side-on
    game camera sees), both travelling towards the tip; `lift` pitches the root (negative lays the tail back),
    `curl` bends the tip over (negative curls it back)."""
    n = len(names)
    for i, b in enumerate(names):
        k = (i + 1) / n
        ph = TAU * (freq * t - lag * i)
        z = sway * (0.5 + 0.7 * k) * S(ph) / n * 2.2
        x = (lift if i == 0 else lift * 0.15) + curl * k * k / n * 3 + wave_up * (0.4 + 0.8 * k) * S(ph + 0.8) / n * 2.2
        if flick and i >= n - 2:
            x -= flick
        p[b] = (x, 0, z)
    return p


def seat(p, P, pitch, hip_to):
    """Pitches the whole body by `pitch` degrees and moves it so the hip joint lands at hip_to (y, z)."""
    R = Euler((math.radians(pitch), 0, 0)).to_matrix()
    cog, hip = P["cog"], Vector((0, P["hip"].y, P["hip"].z))
    t = Vector((0, hip_to[0], hip_to[1])) - cog - R @ (hip - cog)
    p["body"] = (pitch, 0, 0)
    p["@body"] = tuple(t)
    return p


def cat_actions(rig, P, lady):
    q = Quad(rig)
    tails = tail_names(P)

    def base():
        return {"ik": 1.0}

    # ---------------------------------------------------------------- walk: lateral sequence LH, LF, RH, RF
    def walk(t):
        p = base()
        duty, stride = 0.64, 0.2
        for leg, ph, lift in (("bL", 0.0, 0.05), ("fL", 0.25, 0.055), ("bR", 0.5, 0.05), ("fR", 0.75, 0.055)):
            u = (t - ph) % 1.0
            if u < duty:
                s = u / duty
                fwd = -stride / 2 + stride * s
                up = 0.0
                pitch = 45 * smooth01((s - 0.7) / 0.3)  # heel rises before toe-off
            else:
                s = (u - duty) / (1 - duty)
                fwd = stride / 2 - stride * smooth01(s)
                up = lift * S(math.pi * s) ** 1.3
                pitch = 45 + 40 * S(math.pi * min(1, s * 1.6)) - 45 * smooth01(s * 1.3)
                pitch = max(-12, pitch - 20 * smooth01((s - 0.7) / 0.3))
            q.plant(p, leg, fwd=fwd + (0.012 if leg[0] == "f" else 0.0), up=up, pitch=pitch)
        bob = 0.006 * C(TAU * 2 * t)
        p["@body"] = (0.004 * S(TAU * t), 0, bob - 0.004)
        p["body"] = (0, 2.5 * S(TAU * t), 2 * S(TAU * t + 0.6))
        p["pelvis"] = (0, 4 * S(TAU * t), 3 * S(TAU * t))
        p["spine1"] = (1.5, 0, -2.5 * S(TAU * t + 0.25))
        p["spine2"] = (1.5, -3 * S(TAU * (t + 0.25)), -2 * S(TAU * t + 0.25))
        p["neck"] = (-6 + 3 * C(TAU * 2 * t + 0.4), 0, 3 * S(TAU * t))
        p["head"] = (3 - 2.5 * C(TAU * 2 * t + 0.4), 0, -3 * S(TAU * t))
        for s in ("L", "R"):
            ph = 0.25 if s == "L" else 0.75
            p["shoulder_f" + s] = (-10 * C(TAU * (t - ph + 0.32)), 0, 0)
        tail_pose(p, tails, t, sway=26, lift=-8, curl=-20, lag=0.1, wave_up=16)
        return p

    rig.cycle("walk", 30, walk)

    # ---------------------------------------------------------------- run: a gallop with gathered and extended flights
    def run(t):
        p = base()
        flex = C(TAU * (t - 0.93))  # +1 gathered (back arched, hind legs under), -1 stretched
        legs = (("bL", 0.0, 0.33, 0.3, -0.05, 0.08), ("bR", 0.07, 0.33, 0.3, -0.05, 0.08),
                ("fL", 0.42, 0.3, 0.28, -0.09, 0.09), ("fR", 0.5, 0.3, 0.28, -0.09, 0.09))
        for leg, ph, duty, stride, centre, lift in legs:
            u = (t - ph) % 1.0
            if u < duty:
                s = u / duty
                fwd = centre - stride / 2 + stride * s
                up = 0.0
                pitch = 70 * smooth01((s - 0.55) / 0.45)
            else:
                s = (u - duty) / (1 - duty)
                fwd = centre + stride / 2 - stride * smooth01(s)
                up = lift * S(math.pi * s) ** 0.9 + 0.03 * S(math.pi * s)
                pitch = 70 + 30 * S(math.pi * min(1, s * 1.5)) - 90 * smooth01((s - 0.2) / 0.75)
            q.plant(p, leg, fwd=fwd, up=up, pitch=pitch)
        h = 0.02 + 0.03 * S(TAU * (t - 0.8))
        p["@body"] = (0, 0.02 * flex, h)
        p["body"] = (-6 * S(TAU * (t - 0.12)), 0, 0)
        p["pelvis"] = (-18 * flex, 0, 0)
        p["spine1"] = (10 * flex, 0, 0)
        p["spine2"] = (8 * flex, 0, 0)
        p["neck"] = (-10 + 6 * S(TAU * (t - 0.12)) - 8 * flex, 0, 0)
        p["head"] = (6 + 4 * S(TAU * (t - 0.2)), 0, 0)
        for s in ("L", "R"):
            p["shoulder_f" + s] = (-28 * C(TAU * (t - 0.62)), 0, 0)
            p["ear_" + s] = (22, 0, -10 if s == "L" else 10)  # ears back into the wind
        tail_pose(p, tails, t, sway=10, lift=-55 + 10 * flex, curl=-40 + 20 * S(TAU * (t - 0.3)), lag=0.14)
        return p

    rig.cycle("run", 10, run)

    # ---------------------------------------------------------------- idle: breathing, a look around, an ear flick,
    # a blink and a slow tail swish
    def idle(t):
        p = base()
        br = S(TAU * 2 * t)
        p["@body"] = (0, 0, 0.002 * br - 0.003)
        p["spine1"] = (-1 + 1.2 * br, 0, 0)
        p["spine2"] = (-1.5 + 1.5 * br, 0, 0)
        look = S(TAU * t) * smooth01(abs(S(TAU * t)) * 1.4)
        p["neck"] = (-4 - 2 * br, 0, 10 * look)
        p["head"] = (2, 6 * S(TAU * t + 0.5), 8 * look)
        flick = math.exp(-((t - 0.33) * 60) ** 2) + 0.6 * math.exp(-((t - 0.37) * 60) ** 2)
        p["ear_L"] = (-35 * flick, 0, 30 * flick)
        p["ear_R"] = (0, 0, -6 * math.exp(-((t - 0.8) * 30) ** 2))
        blink = max(math.exp(-((t - 0.6) * 55) ** 2), math.exp(-((t - 0.1) * 55) ** 2))
        for s in ("L", "R"):
            p["%eye_" + s] = (1, 1, 1 - 0.9 * blink)
        tail_pose(p, tails, t, sway=30, lift=-4, curl=-20 + 25 * S(TAU * 2 * t), lag=0.08, wave_up=18,
                  flick=25 * math.exp(-((t - 0.8) * 25) ** 2))
        for leg in q.LEGS:
            q.plant(p, leg)
        return p

    # ---------------------------------------------------------------- sitting (the lady's idle, and a plain sit)
    def sit_pose(p, t, pitch=-36):
        br = S(TAU * 2 * t)
        seat(p, P, pitch, (P["hip"].y - 0.02, 0.1 + 0.0015 * br))
        p["pelvis"] = (8, 0, 0)
        p["spine1"] = (-2 + br, 0, 0)
        p["spine2"] = (-3 + br, 0, 0)
        p["neck"] = (-pitch * 0.35 - 4, 0, 0)
        p["head"] = (-pitch * 0.55 + 6, 0, 0)
        # front legs straight columns under the shoulders, paws together; hind legs folded, hocks on the ground
        for s, sx in (("L", 1), ("R", -1)):
            p["shoulder_f" + s] = (-4, 0, 0)
            sh = rig.head_of(p, "upper_f" + s)
            q.plant(p, "f" + s, fwd=sh.y - 0.012 - rig.rest_head("paw_f" + s).y, up=0.0, side=-0.008 * sx)
            q.plant(p, "b" + s, fwd=-0.1, up=0.0, pitch=0, side=0.02 * sx)
        tail_pose(p, tails, t, sway=0, lift=0, curl=0)
        # the tail wrapped round the feet, its tip tapping
        p["tail0"] = (95, 0, 30)
        p["tail1"] = (25, 0, 35)
        p["tail2"] = (8, 0, 40 + 3 * S(TAU * t))
        p["tail3"] = (0, 0, 38 + 4 * S(TAU * t - 0.5))
        p["tail4"] = (0, 0, 30 + 6 * S(TAU * t - 1.0))
        p["tail5"] = (-10 - 8 * S(TAU * 2 * t - 1.5), 0, 14 + 10 * S(TAU * t - 1.5))
        p["tail6"] = (-10 - 14 * S(TAU * 2 * t - 2.0) - 30 * math.exp(-((t - 0.7) * 25) ** 2), 0, 10 + 14 * S(TAU * t - 2.0))
        return p

    def sit(t):
        p = sit_pose(base(), t)
        tilt = S(TAU * t)
        p["head"] = (p["head"][0] - 3 * tilt, 10 * smooth01(0.5 + 0.5 * tilt) - 5, 6 * tilt)
        blink = max(math.exp(-((t - 0.3) * 50) ** 2), math.exp(-((t - 0.78) * 50) ** 2))
        if lady:  # slow, contented blinks
            blink = max(blink, 0.8 * smooth01(1 - abs(t - 0.55) * 14))
        for s in ("L", "R"):
            p["%eye_" + s] = (1, 1, 1 - 0.9 * blink)
        p["ear_R"] = (-25 * math.exp(-((t - 0.45) * 50) ** 2), 0, 0)
        return p

    if lady:  # the lady waits on her balcony, seated
        rig.cycle("idle", 120, sit, step=2)
        rig.cycle("stand", 120, idle, step=2)
    else:
        rig.cycle("idle", 120, idle, step=2)
        rig.cycle("sit", 120, sit, step=2)

    # ---------------------------------------------------------------- the serenade: sits up and sings
    def cheer(t):
        p = sit_pose(base(), t, pitch=-40)
        beat = S(TAU * 2 * t)
        sing = max(0.0, S(TAU * 2 * t + 0.4)) ** 0.7
        p["body"] = (-40, 0, 5 * S(TAU * t))
        p["neck"] = (4, 0, 0)
        p["head"] = (22 - 12 * sing, 12 * S(TAU * t), 8 * S(TAU * t))
        p["jaw"] = (-38 * sing, 0, 0)
        for s in ("L", "R"):
            p["%eye_" + s] = (1, 1, 0.12)
            p["ear_" + s] = (-10, 0, 0)
        # one paw on the heart
        p["ik"] = {"fL": 0.0}
        p["shoulder_fL"] = (-35, 0, 0)
        p["upper_fL"] = (-60, 0, -12)
        p["lower_fL"] = (-70, 0, -20)
        p["paw_fL"] = (-10, 0, 0)
        return p

    rig.cycle("cheer", 40, cheer, step=2)

    # ---------------------------------------------------------------- jump: take-off stretch into a tuck (held)
    def fk_air(p, reach, tuck):
        """Legs in the air (no IK): reach > 0 stretches the fore legs forward and the hind legs back."""
        p["ik"] = 0.0
        for s in ("L", "R"):
            p["shoulder_f" + s] = (-20 * reach - 5 * tuck, 0, 0)
            p["upper_f" + s] = (-40 * reach + 20 * tuck, 0, 0)
            p["lower_f" + s] = (-10 * reach - 70 * tuck, 0, 0)
            p["paw_f" + s] = (-20 * reach + 60 * tuck, 0, 0)
            p["upper_b" + s] = (30 * reach - 40 * tuck, 0, 0)
            p["lower_b" + s] = (35 * reach + 40 * tuck, 0, 0)
            p["foot_b" + s] = (25 * reach - 50 * tuck, 0, 0)
            p["paw_b" + s] = (30 * reach + 30 * tuck, 0, 0)
        return p

    def jump(t):
        p = base()
        r = 1 - smooth01(t * 1.4)  # the take-off stretch fades into a tuck
        k = smooth01((t - 0.25) / 0.6)
        fk_air(p, r, k)
        p["body"] = (-24 * r - 6 * k, 0, 0)
        p["@body"] = (0, 0, 0.01 * r)
        p["spine1"] = (-6 * r + 8 * k, 0, 0)
        p["spine2"] = (-4 * r + 6 * k, 0, 0)
        p["pelvis"] = (8 * r - 14 * k, 0, 0)
        p["neck"] = (8 * r - 4 * k, 0, 0)
        p["head"] = (-4 * r + 6 * k, 0, 0)
        tail_pose(p, tails, t, sway=0, lift=-50 * r - 20 * k, curl=-30 + 40 * k, lag=0)
        for s in ("L", "R"):
            p["ear_" + s] = (15 * r, 0, 0)
        return p

    rig.cycle("jump", 14, jump, loop=False)

    # ---------------------------------------------------------------- fall: reaching down for the landing
    def fall(t):
        """Dropping: fore legs reach down and forward for the landing, hind legs trail, the back arches, the tail
        rises for balance; a slight paddle and the ears blown back."""
        p = base()
        w = S(TAU * t)
        p["ik"] = 0.0
        for s_, sg in (("L", 1), ("R", -1)):
            p["shoulder_f" + s_] = (-24 + 5 * w * sg, 0, 0)
            p["upper_f" + s_] = (-38 + 8 * w * sg, 0, -8 * sg)
            p["lower_f" + s_] = (-6 - 6 * w * sg, 0, 0)
            p["paw_f" + s_] = (-28, 0, 0)
            p["upper_b" + s_] = (18 - 6 * w * sg, 0, 8 * sg)
            p["lower_b" + s_] = (-10, 0, 0)
            p["foot_b" + s_] = (20, 0, 0)
            p["paw_b" + s_] = (20, 0, 0)
            p["ear_" + s_] = (28, 0, 20 * sg)
        p["body"] = (10 + 2 * w, 0, 0)
        p["spine1"] = (6, 0, 0)
        p["spine2"] = (4, 0, 0)
        p["pelvis"] = (-10, 0, 0)
        p["neck"] = (-20, 0, 0)
        p["head"] = (6, 0, 0)
        p["jaw"] = (-10 - 6 * max(0, w), 0, 0)
        for e in ("L", "R"):
            p["%eye_" + e] = (1.15, 1, 1.2)  # wide-eyed
        tail_pose(p, tails, t, sway=16, lift=10, curl=-50, lag=0.12, wave_up=24)
        return p

    rig.cycle("fall", 20, fall)

    # ---------------------------------------------------------------- swim: a frantic paddle, head held high
    def swim(t):
        p = base()
        p["ik"] = 0.0
        for s, ph in (("L", 0.0), ("R", 0.5)):
            a = TAU * (t + ph)
            p["shoulder_f" + s] = (-25 + 15 * S(a), 0, 0)
            p["upper_f" + s] = (-40 + 35 * S(a), 0, 0)
            p["lower_f" + s] = (-40 - 30 * C(a), 0, 0)
            p["paw_f" + s] = (30 + 20 * C(a), 0, 0)
            p["upper_b" + s] = (10 - 30 * S(a + 1.2), 0, 0)
            p["lower_b" + s] = (20 + 25 * C(a + 1.2), 0, 0)
            p["foot_b" + s] = (-20 - 20 * S(a + 1.2), 0, 0)
            p["paw_b" + s] = (20, 0, 0)
            p["ear_" + s] = (30, 0, 30 if s == "L" else -30)  # flattened, unhappy
        p["body"] = (-22 + 2 * S(TAU * 2 * t), 0, 3 * S(TAU * t))
        p["@body"] = (0, 0, 0.006 * S(TAU * 2 * t))
        p["neck"] = (-8, 0, 0)
        p["head"] = (22, 0, -4 * S(TAU * t))
        p["jaw"] = (-12 - 8 * max(0, S(TAU * 2 * t)), 0, 0)
        tail_pose(p, tails, t, sway=18, lift=-45, curl=-30, lag=0.1, freq=2, wave_up=10)
        return p

    rig.cycle("swim", 16, swim)

    # ---------------------------------------------------------------- catch: crouch, pounce, pin, look up pleased
    def catch_pose(stage):
        p = base()
        if stage == "crouch":
            p["@body"] = (0, 0.02, -0.06)
            p["body"] = (6, 0, 0)
            p["pelvis"] = (-10, 0, 0)
            p["neck"] = (-12, 0, 0)
            p["head"] = (18, 0, 0)
            for s in ("L", "R"):
                q.plant(p, "f" + s, fwd=-0.02)
                q.plant(p, "b" + s, fwd=-0.04, pitch=10)
                p["ear_" + s] = (-10, 0, 0)
            tail_pose(p, tails, 0, lift=-60, curl=-20)
        elif stage == "pounce":
            p["@body"] = (0, -0.06, 0.04)
            p["body"] = (-10, 0, 0)
            p["spine1"] = (-6, 0, 0)
            p["neck"] = (-6, 0, 0)
            p["head"] = (-4, 0, 0)
            p["jaw"] = (-25, 0, 0)
            for s in ("L", "R"):
                q.plant(p, "f" + s, fwd=-0.16, up=0.09, pitch=-30)
                q.plant(p, "b" + s, fwd=0.07, pitch=60)
            tail_pose(p, tails, 0, lift=-70, curl=-30)
        elif stage == "pin":
            p["@body"] = (0, -0.06, -0.04)
            p["body"] = (10, 0, 0)
            p["neck"] = (8, 0, 0)
            p["head"] = (22, 0, 0)
            for s in ("L", "R"):
                q.plant(p, "f" + s, fwd=-0.17, pitch=20)
                q.plant(p, "b" + s, fwd=-0.02)
            tail_pose(p, tails, 0, lift=-20, curl=-10)
        else:  # pleased
            p["@body"] = (0, -0.02, 0.0)
            p["neck"] = (-14, 0, 0)
            p["head"] = (-6, 0, 10)
            for s in ("L", "R"):
                q.plant(p, "f" + s, fwd=-0.06)
                q.plant(p, "b" + s)
                p["%eye_" + s] = (1, 1, 0.3)
            tail_pose(p, tails, 0, lift=10, curl=-30)
        return p

    rig.poses("catch", {1: catch_pose("crouch"), 5: catch_pose("pounce"), 8: catch_pose("pin"), 15: catch_pose("pleased")})

    # ---------------------------------------------------------------- die: a jolt, a spin and flat on the back
    def die_pose(stage):
        p = base()
        p["ik"] = 0.0
        if stage == "jolt":
            p["@body"] = (0, 0, 0.14)
            p["body"] = (-18, 0, 0)
            for s, sg in (("L", 1), ("R", -1)):
                p["upper_f" + s] = (-50, 0, -30 * sg)
                p["upper_b" + s] = (50, 0, -30 * sg)
                p["lower_b" + s] = (-20, 0, 0)
                p["ear_" + s] = (-20, 0, 40 * sg)
                p["%eye_" + s] = (1.3, 1, 1.3)
            p["jaw"] = (-35, 0, 0)
            tail_pose(p, tails, 0, lift=-30, curl=40)
        elif stage == "roll":
            p["@body"] = (0, 0, 0.02)
            p["body"] = (-6, 95, 0)
            for s, sg in (("L", 1), ("R", -1)):
                p["upper_f" + s] = (-40, 0, 20 * sg)
                p["upper_b" + s] = (40, 0, 20 * sg)
                p["%eye_" + s] = (1, 1, 0.12)
            tail_pose(p, tails, 0, lift=-60, curl=-10)
        else:  # flat out on the back, paws up, a last twitch at "twitch"
            p["@body"] = (0, 0, -0.165 if stage != "twitch" else -0.16)
            p["body"] = (0, 178, 0)
            p["spine1"] = (-4, 0, 0)
            p["neck"] = (40, 0, 0)  # upside down: bending the neck this way lays the head on the floor
            p["head"] = (30, 0, 25)
            p["jaw"] = (-18, 0, 0)
            tw = 8 if stage == "twitch" else 0
            for s, sg in (("L", 1), ("R", -1)):
                p["shoulder_f" + s] = (-20, 0, 0)
                p["upper_f" + s] = (-50 - tw, 0, 18 * sg)
                p["lower_f" + s] = (60 + tw, 0, 0)
                p["paw_f" + s] = (50, 0, 0)
                p["upper_b" + s] = (-60, 0, 25 * sg)
                p["lower_b" + s] = (40 + tw, 0, 0)
                p["foot_b" + s] = (-20, 0, 0)
                p["paw_b" + s] = (10, 0, 0)
                p["%eye_" + s] = (1, 1, 0.1)
                p["ear_" + s] = (10, 0, 0)
            p["tail0"] = (-70, 0, 20)
            for i, tn in enumerate(tails[1:]):
                p[tn] = (-10, 0, 8)
        return p

    rig.poses("die", {1: base() | {"ik": 0.0}, 5: die_pose("jolt"), 13: die_pose("roll"), 20: die_pose("down"),
                      25: die_pose("twitch"), 30: die_pose("down")})

    # ---------------------------------------------------------------- hurt: a flinch from a flying boot
    rig.poses("hurt", {1: base(), 4: {"ik": 1.0, "@body": (0, 0.03, -0.03), "body": (8, 0, 0), "neck": (14, 0, 0),
                                      "head": (10, -10, 0), "ear_L": (40, 0, 30), "ear_R": (40, 0, -30),
                                      "%eye_L": (1, 1, 0.1), "%eye_R": (1, 1, 0.1), "tail0": (-40, 0, 0)},
                      12: base()})


# ====================================================================== the bulldog
DOG = {
    "root_len": 0.15,
    "cog": Vector((0, -0.02, 0.4)), "rump": Vector((0, 0.19, 0.43)), "mid": Vector((0, -0.14, 0.41)),
    "withers": Vector((0, -0.27, 0.45)), "skull": Vector((0, -0.37, 0.53)), "snout": Vector((0, -0.64, 0.6)),
    "jaw": Vector((0, -0.46, 0.5)), "chin": Vector((0, -0.68, 0.45)),
    "ear0": Vector((0.15, -0.43, 0.72)), "ear1": Vector((0.22, -0.45, 0.74)),
    "eye": Vector((0.1, -0.6, 0.645)),
    "scap": Vector((0.13, -0.2, 0.5)), "shoulder": Vector((0.17, -0.29, 0.34)),
    "elbow": Vector((0.225, -0.24, 0.21)), "wrist": Vector((0.18, -0.28, 0.062)), "ftoe": Vector((0.2, -0.35, 0.02)),
    "hip": Vector((0.1, 0.17, 0.42)), "knee": Vector((0.12, 0.09, 0.25)), "hock": Vector((0.12, 0.21, 0.12)),
    "ankle": Vector((0.12, 0.19, 0.035)), "btoe": Vector((0.12, 0.13, 0.02)),
    "tail": [Vector(p) for p in ((0, 0.26, 0.49), (0, 0.31, 0.53), (0, 0.34, 0.5))],
}


def build_bulldog():
    K.clear_scene()
    K.MATS.clear()
    P = dict(DOG)
    fawn, white_c, mask_c = (0.74, 0.47, 0.27), (0.95, 0.92, 0.85), (0.22, 0.14, 0.1)
    mask = mat("dog_mask", mask_c, 0.75, sheen=0.3)
    coat = mat("dog_coat", fawn, 0.8, sheen=0.3)
    black = mat("dog_nose", (0.03, 0.03, 0.03), 0.25, coat=0.8)
    collar_m = mat("dog_collar", (0.8, 0.1, 0.08), 0.4, coat=0.3)
    stud = mat("dog_studs", (0.85, 0.85, 0.8), 0.2, coat=0.6)
    tooth = mat("dog_teeth", (1, 0.97, 0.9), 0.3)
    eye_m = mat("dog_eye", (0.14, 0.07, 0.03), 0.05, coat=1.0)
    eye_white = mat("dog_eye_white", (0.95, 0.93, 0.88), 0.2, coat=0.6)
    shine = mat("dog_shine", (1, 1, 1), 0.1, emit=1.2)
    mouth = mat("dog_mouth", (0.3, 0.07, 0.08), 0.6)
    tongue = mat("dog_tongue", (0.9, 0.4, 0.45), 0.4)

    body = Blob("dog_torso", res=0.01)
    body.ell((0, -0.21, 0.37), 0.21, 0.17, 0.2, rot=(-10, 0, 0))  # deep, wide chest slung low
    body.ell((0, -0.04, 0.4), 0.16, 0.17, 0.15, rot=(-4, 0, 0))  # a short barrel
    body.ell((0, 0.14, 0.43), 0.12, 0.11, 0.12, rot=(12, 0, 0))  # narrow hips, a little higher: the roach back
    for s in (-1, 1):
        body.ell((0.14 * s, -0.25, 0.4), 0.08, 0.11, 0.13, rot=(-15, 0, 0))  # shoulders
    head = Blob("dog_head", res=0.008)
    head.ell((0, -0.47, 0.62), 0.2, 0.16, 0.15)  # a big wide skull
    for s in (-1, 1):
        head.ell((0.12 * s, -0.54, 0.57), 0.1, 0.1, 0.1)  # cheeks
        head.ell((0.09 * s, -0.6, 0.475), 0.085, 0.07, 0.085, rot=(0, 8 * s, 0))  # hanging flews
    head.ell((0, -0.6, 0.575), 0.14, 0.075, 0.085)  # short, pushed-in muzzle
    head.ell((0, -0.55, 0.69), 0.15, 0.07, 0.05)  # heavy brow
    neck = tube([(0, -0.22, 0.44), (0, -0.3, 0.5), (0, -0.4, 0.56)], [0.175, 0.17, 0.155], "neck")
    limbs = []
    for sx in (1, -1):
        m = lambda v: (v[0] * sx, v[1], v[2])
        # bowed front legs set wide: elbows out, paws turned a touch outwards
        limbs.append(tube([m((0.14, -0.24, 0.4)), m((0.17, -0.29, 0.33)), m((0.225, -0.24, 0.21)), m((0.2, -0.265, 0.12)),
                           m((0.18, -0.28, 0.065))], [0.092, 0.088, 0.068, 0.056, 0.05], "fleg"))
        limbs.append(Blob("fpaw", res=0.006).ell(m((0.195, -0.31, 0.035)), 0.06, 0.07, 0.036, rot=(0, 0, -18 * sx)))
        limbs.append(Blob("haunch", res=0.008).ell(m((0.095, 0.15, 0.33)), 0.07, 0.1, 0.12, rot=(22, 0, 0)))
        limbs.append(tube([m((0.09, 0.15, 0.42)), m((0.115, 0.13, 0.33)), m((0.12, 0.09, 0.25)), m((0.12, 0.15, 0.18)),
                           m((0.12, 0.21, 0.12)), m((0.12, 0.19, 0.05))], [0.085, 0.08, 0.058, 0.048, 0.042, 0.04], "bleg"))
        limbs.append(Blob("bpaw", res=0.006).ell(m((0.12, 0.172, 0.03)), 0.05, 0.065, 0.032))
    tail = tube(P["tail"], [0.042, 0.036, 0.024], "tail")

    def white_amount(c, n):
        socks = ss(c.z, 0.1, 0.065)
        chest = ss(-c.y, 0.27, 0.33) * ss(c.z, 0.52, 0.45) * ss(-n.y, -0.1, 0.25) * ss(abs(c.x), 0.16, 0.1)
        belly = ss(-n.z, 0.3, 0.6) * ss(c.z, 0.34, 0.28)
        blaze = ss(abs(c.x), 0.05 + 0.08 * ss(c.z, 0.64, 0.58), 0.03 + 0.08 * ss(c.z, 0.64, 0.58)) * ss(-c.y, 0.5, 0.56) * ss(c.z, 0.78, 0.74) * ss(c.z, 0.5, 0.53)
        return max(socks, chest, belly, blaze)

    def mask_amount(c, n):
        muzzle = ss(-c.y, 0.56, 0.6) * ss(c.z, 0.64, 0.6) * (1 - ss(abs(c.x), 0.03, 0.02) * ss(c.z, 0.56, 0.6))
        wrinkles = ss(-c.y, 0.5, 0.56) * ss(c.z, 0.68, 0.7) * ss(abs(c.x), 0.14, 0.1) * ss(S(TAU * c.z * 32.0), 0.6, 0.9) * 0.45
        return max(muzzle, wrinkles)

    def colour(c, n):
        shade = 0.88 + 0.12 * ss(n.z, -0.6, 0.6)
        col = mix(fawn, (0.62, 0.38, 0.21), 0.5 * ss(c.z, 0.5, 0.6) * ss(n.z, 0.2, 0.8))  # a darker saddle
        col = mix(col, white_c, white_amount(c, n))
        col = mix(col, mask_c, mask_amount(c, n))
        return tuple(x * shade for x in col)

    skin = fuse([body, head, neck, tail] + limbs, "bulldog", voxel=0.006, smooth=4, faces=8500)
    K.paint_vc(skin, colour, K.vc_mat("dog_coat", 0.85, sheen=0.4))

    parts = []
    front = lambda x, z: K.surface(skin, (x, -2, z), (0, 1, 0))[0]
    ey = front(P["eye"].x, P["eye"].z).y + 0.012
    P["eye"] = Vector((P["eye"].x, ey, P["eye"].z))
    for s, side in ((1, "L"), (-1, "R")):
        ex, ez = P["eye"].x * s, P["eye"].z
        parts.append(sphere(0.032, (ex, ey + 0.004, ez), "eye_" + side, eye_white, (1, 0.6, 0.9)))
        parts.append(sphere(0.024, (ex + 0.002 * s, ey - 0.006, ez - 0.002), "eye_" + side, eye_m, (1, 0.6, 1)))
        parts.append(sphere(0.008, (ex + 0.008 * s, ey - 0.02, ez + 0.01), "eye_" + side, shine))
        # a frowning brow over each eye, and a wrinkle
        b0, b1 = front(0.04 * s, ez + 0.05), front(0.14 * s, ez + 0.035)
        parts.append(rod(0.022, b0 + Vector((0, 0.012, 0)), b1 + Vector((0, 0.012, 0)), "head", coat, 0.016, 10))
        # rose ears: small folded flaps at the back corners of the skull
        top = K.surface(skin, (P["ear0"].x * s, P["ear0"].y, 2), (0, 0, -1))[0]
        P["ear0"] = Vector((P["ear0"].x, P["ear0"].y, top.z - 0.02))
        P["ear1"] = Vector((P["ear1"].x, P["ear1"].y + 0.02, top.z + 0.02))
        # a folded triangular flap tipping outwards and down from the top corner of the skull
        ear = cone(0.052, 0.006, 0.085, (P["ear0"].x * s + 0.045 * s, P["ear0"].y + 0.01, top.z - 0.01), "ear_" + side, mask,
                   rot=(-15, 115 * s, 0), verts=12, scale=(1, 0.32, 1))
        ear["bone"] = "ear_" + side
        parts.append(ear)
    nose = front(0, 0.61)
    parts.append(sphere(0.05, nose + Vector((0, 0.012, 0)), "head", black, (1.35, 0.7, 0.75)))
    for s in (-1, 1):  # nostrils
        parts.append(sphere(0.012, nose + Vector((0.025 * s, -0.018, -0.005)), "head", mask, (1.2, 0.6, 0.8)))
    lip = front(0, 0.49)
    parts.append(sphere(0.07, lip + Vector((0, 0.06, 0.01)), "head", mouth, (1.3, 1.0, 0.7)))  # inside the mouth
    # the lower jaw: an underbite, with a row of small teeth, two canines and a tongue
    jaw = Blob("jaw", res=0.005).ell(tuple(lip + Vector((0, 0.035, -0.035))), 0.1, 0.055, 0.035, rot=(-6, 0, 0))
    jm = jaw.mesh("jaw", smooth=1)
    paint(jm, [(mask, None)])
    jm["bone"] = "jaw"
    parts.append(jm)
    P["chin"] = lip + Vector((0, 0.0, -0.04))
    parts.append(sphere(0.05, lip + Vector((0, 0.05, -0.012)), "jaw", tongue, (1.1, 1.0, 0.35)))
    for k in range(-2, 3):
        parts.append(sphere(0.011, lip + Vector((0.022 * k, 0.0 + 0.004 * abs(k), -0.01)), "jaw", tooth, (1, 0.7, 1.3)))
    for s in (-1, 1):
        parts.append(cone(0.013, 0.003, 0.045, lip + Vector((0.065 * s, 0.01, 0.005)), "jaw", tooth, rot=(-10, 0, 0)))
    # the studded collar, fitted to the neck
    ring, rad, R = K.collar(skin, (0, -0.31, 0.49), 56, 0.026, "neck", collar_m, snug=0.2)
    parts.append(ring)
    for k in range(12):
        a = TAU * k / 12
        v = R @ Vector((C(a), S(a), 0))
        parts.append(cone(0.014, 0.003, 0.026, Vector((0, -0.31, 0.49)) + v * (rad + 0.022), "neck", stud,
                          rot=tuple(math.degrees(x) for x in Vector((0, 0, 1)).rotation_difference(v).to_euler())))

    rig = make_quad_rig("bulldog", P)
    ex = side_exclude(rig)
    for t in tail_names(P):
        ex[t] = lambda co: co.y < 0.2
    for b in ("head", "neck"):
        ex[b] = lambda co: co.y > -0.2
    ex["pelvis"] = lambda co: co.y < -0.14
    K.skin(skin, rig, smooth_iter=4, exclude=ex)
    body = K.assemble("bulldog", skin, rig, parts)
    dog_actions(rig, P)
    K.export("bulldog", rig, body, out_dir)


def dog_actions(rig, P):
    q = Quad(rig)
    tails = tail_names(P)

    def base():
        return {"ik": 1.0}

    # ---------------------------------------------------------------- walk: a heavy, rolling trot
    def walk(t):
        p = base()
        duty, stride = 0.52, 0.26
        for leg, ph, lift in (("fL", 0.0, 0.07), ("bR", 0.02, 0.06), ("fR", 0.5, 0.07), ("bL", 0.52, 0.06)):
            u = (t - ph) % 1.0
            if u < duty:
                s = u / duty
                fwd, up = -stride / 2 + stride * s, 0.0
                pitch = 40 * smooth01((s - 0.65) / 0.35)
            else:
                s = (u - duty) / (1 - duty)
                fwd = stride / 2 - stride * smooth01(s)
                up = lift * S(math.pi * s)
                pitch = 40 + 30 * S(math.pi * min(1, s * 1.6)) - 70 * smooth01((s - 0.3) / 0.6)
            q.plant(p, leg, fwd=fwd, up=up, pitch=pitch, side=0.012 * S(math.pi * max(0, s if u >= duty else 0)) * (1 if leg[1] == "L" else -1))
        p["@body"] = (0, 0, -0.012 + 0.012 * C(TAU * 2 * t + 0.6))
        p["body"] = (1.5 * S(TAU * 2 * t), 6 * S(TAU * t + 0.3), 3 * S(TAU * t))  # the waddle: a roll with each diagonal
        p["pelvis"] = (0, -4 * S(TAU * t + 0.3), -4 * S(TAU * t))
        p["spine2"] = (0, -3 * S(TAU * t + 0.3), 0)
        p["neck"] = (-2 - 3 * C(TAU * 2 * t + 1.2), 0, 4 * S(TAU * t))
        p["head"] = (2 + 4 * C(TAU * 2 * t + 1.6), -3 * S(TAU * t), 0)
        p["jaw"] = (-4 - 3 * max(0, C(TAU * 2 * t + 2.0)), 0, 0)
        for s in ("L", "R"):
            p["shoulder_f" + s] = (-10 * C(TAU * (t - (0 if s == "L" else 0.5) + 0.25)), 0, 0)
            p["ear_" + s] = (-6 * C(TAU * 2 * t + 2.2), 0, 0)
        p["tail0"] = (0, 0, 20 * S(TAU * 2 * t))
        p["tail1"] = (0, 0, 25 * S(TAU * 2 * t - 0.8))
        return p

    rig.cycle("walk", 14, walk)

    # ---------------------------------------------------------------- run: a thundering gallop
    def run(t):
        p = base()
        flex = C(TAU * (t - 0.9))
        legs = (("bL", 0.0, 0.36, 0.34, -0.06, 0.1), ("bR", 0.08, 0.36, 0.34, -0.06, 0.1),
                ("fL", 0.45, 0.34, 0.32, -0.1, 0.12), ("fR", 0.55, 0.34, 0.32, -0.1, 0.12))
        for leg, ph, duty, stride, centre, lift in legs:
            u = (t - ph) % 1.0
            if u < duty:
                s = u / duty
                fwd, up = centre - stride / 2 + stride * s, 0.0
                pitch = 60 * smooth01((s - 0.55) / 0.45)
            else:
                s = (u - duty) / (1 - duty)
                fwd = centre + stride / 2 - stride * smooth01(s)
                up = lift * S(math.pi * s)
                pitch = 60 + 25 * S(math.pi * min(1, s * 1.5)) - 85 * smooth01((s - 0.2) / 0.75)
            q.plant(p, leg, fwd=fwd, up=up, pitch=pitch)
        p["@body"] = (0, 0.02 * flex, 0.0 + 0.035 * S(TAU * (t - 0.8)))
        p["body"] = (-6 * S(TAU * (t - 0.12)), 0, 0)
        p["pelvis"] = (-12 * flex, 0, 0)
        p["spine1"] = (6 * flex, 0, 0)
        p["spine2"] = (5 * flex, 0, 0)
        p["neck"] = (-6 + 5 * S(TAU * (t - 0.1)), 0, 0)
        p["head"] = (4 + 5 * S(TAU * (t - 0.2)), 0, 0)
        p["jaw"] = (-14 - 6 * S(TAU * (t - 0.3)), 0, 0)  # panting, jowls flapping
        for s in ("L", "R"):
            p["shoulder_f" + s] = (-22 * C(TAU * (t - 0.65)), 0, 0)
            p["ear_" + s] = (18 + 10 * S(TAU * (t - 0.35)), 0, 0)
        p["tail0"] = (-20, 0, 12 * S(TAU * t))
        p["tail1"] = (-10, 0, 16 * S(TAU * t - 0.8))
        return p

    rig.cycle("run", 12, run)

    # ---------------------------------------------------------------- bark: brace, then bark, recoiling
    def bark_pose(stage):
        p = base()
        brace = {"@body": (0, 0.05, -0.05), "body": (8, 0, 0), "pelvis": (-4, 0, 0), "neck": (10, 0, 0), "head": (6, 0, 0)}
        if stage in ("brace", "bark", "bark2", "after"):
            p.update(brace)
            for s, sg in (("L", 1), ("R", -1)):
                q.plant(p, "f" + s, fwd=-0.08, side=0.03 * sg)
                q.plant(p, "b" + s, fwd=0.04, side=0.01 * sg)
                p["ear_" + s] = (20, 0, 0)
            p["tail0"] = (-30, 0, 0)
            p["jaw"] = (-4, 0, 0)
        if stage in ("bark", "bark2"):
            k = 1.0 if stage == "bark" else 0.7
            p["@body"] = (0, 0.02, -0.02 + 0.03 * k)
            p["body"] = (-6 * k, 0, 0)
            p["neck"] = (-16 * k, 0, 0)
            p["head"] = (-14 * k, 0, 0)
            p["jaw"] = (-38 * k, 0, 0)
            for s in ("L", "R"):
                p["ear_" + s] = (-25 * k, 0, 0)
                p["%eye_" + s] = (1.1, 1, 1.15)
        return p

    rig.poses("bark", {1: bark_pose("stand"), 4: bark_pose("brace"), 6: bark_pose("bark"), 8: bark_pose("brace"),
                       10: bark_pose("bark2"), 13: bark_pose("after")})

    # ---------------------------------------------------------------- stand: a patient idle with a wagging stub
    def stand(t):
        p = base()
        br = S(TAU * 2 * t)
        p["@body"] = (0, 0, -0.004 + 0.002 * br)
        p["spine2"] = (br, 0, 0)
        p["neck"] = (-2 * br, 0, 6 * S(TAU * t))
        p["head"] = (3, 4 * S(TAU * t + 1), 4 * S(TAU * t))
        p["jaw"] = (-6 - 5 * max(0, br), 0, 0)  # panting
        p["tail0"] = (0, 0, 28 * S(TAU * 6 * t))
        p["tail1"] = (0, 0, 20 * S(TAU * 6 * t - 1))
        blink = math.exp(-((t - 0.4) * 50) ** 2)
        for s in ("L", "R"):
            p["%eye_" + s] = (1, 1, 1 - 0.9 * blink)
        for leg in q.LEGS:
            q.plant(p, leg)
        return p

    rig.cycle("stand", 60, stand, step=2)

    # ---------------------------------------------------------------- idle: asleep, lying down, snoring
    def idle(t):
        p = base()
        br = S(TAU * t)
        p["@body"] = (0, 0.02, -0.25 + 0.006 * br)
        p["body"] = (-2, 0, 0)
        p["spine1"] = (0.8 * br, 0, 0)
        p["spine2"] = (-1 + 1.5 * br, 0, 0)
        p["neck"] = (10, 0, 6)
        p["head"] = (14 - 1.5 * br, -6, 4)
        p["jaw"] = (-3 - 3 * max(0, br), 0, 0)
        for s, sg in (("L", 1), ("R", -1)):
            q.plant(p, "f" + s, fwd=-0.2, up=0.0, pitch=-20, side=-0.02 * sg)  # front legs stretched out
            # hind legs folded flat under the belly (FK: the thigh forward, shin and hock tucked back)
            p["upper_b" + s] = (-70, 0, 12 * sg)
            p["lower_b" + s] = (120, 0, 0)
            p["foot_b" + s] = (-75, 0, 0)
            p["paw_b" + s] = (20, 0, 0)
            p["%eye_" + s] = (1, 1, 0.1)
            p["shoulder_f" + s] = (-30, 0, 0)
            p["ear_" + s] = (10, 0, 0)
        p["ear_L"] = (10 - 25 * math.exp(-((t - 0.6) * 30) ** 2), 0, 0)  # a twitch in a dream
        p["ik"] = {"bL": 0.0, "bR": 0.0}
        p["tail0"] = (-40, 0, 25)
        p["tail1"] = (-10, 0, 10)
        return p

    rig.cycle("idle", 30, idle)


# ======================================================================
if only is None or "cat" in only:
    build_cat("cat", (0.88, 0.47, 0.16), (0.5, 0.2, 0.06), (0.5, 0.85, 0.2))
if only is None or "lady_cat" in only:
    build_cat("lady_cat", (0.97, 0.96, 0.95), (0.8, 0.8, 0.84), (0.3, 0.6, 1.0), tabby=False, torn=False, bow=True, lady=True)
if only is None or "bulldog" in only:
    build_bulldog()
