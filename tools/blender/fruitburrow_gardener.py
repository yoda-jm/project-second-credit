"""The Fruitburrow gardener: a small, round, friendly farmer (straw hat, moustache, red shirt, blue dungarees, boots,
a little spade). One smooth skinned body (metaballs and tubes, voxel-fused, clothes painted as vertex colours) on
a real biped skeleton: hips, spine, chest, neck, head, clavicles, upper arms, forearms, hands, thighs, shins and
feet, with IK legs so the boots plant. Hard bits (hat, boots, eyes, moustache, buttons, spade) are rigid.
Deterministic; output CC BY-SA 4.0; provenance: this script and creature_kit.py.
Run: blender -b --factory-startup -P tools/blender/fruitburrow_gardener.py -- godot/games/fruitburrow/art/models
About 0.85 m tall, centred on the cell (feet at z = -0.45), facing -Y. Actions (one glTF animation each): idle,
walk (a bouncy jog), dig (wind up, strike, lever and toss; one stroke per loop), throw (played once), cheer, die.
"""
import bpy, math, os, sys
from mathutils import Vector, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import creature_kit as K
from creature_kit import mat, sphere, cyl, rod, tube, Blob, fuse, Rig, smooth01, ss, mix

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
S, C, TAU = math.sin, math.cos, 2 * math.pi
FZ = -0.45  # the soles

K.clear_scene()
SKIN, SHIRT, DENIM = (0.93, 0.62, 0.46), (0.8, 0.13, 0.1), (0.13, 0.27, 0.62)
HAIR, CUFF, STITCH = (0.36, 0.2, 0.08), (0.92, 0.3, 0.24), (0.85, 0.6, 0.2)
straw = mat("straw", (0.93, 0.76, 0.38), 0.8)
band = mat("hat_band", (0.75, 0.12, 0.1), 0.6)
boot = mat("boots", (0.3, 0.17, 0.08), 0.5, coat=0.3)
sole = mat("soles", (0.12, 0.08, 0.05), 0.8)
dark = mat("eyes", (0.03, 0.03, 0.04), 0.1, coat=1.0)
white = mat("eye_shine", (1, 1, 1), 0.1, emit=1.0)
metal = mat("spade", (0.72, 0.74, 0.78), 0.28)
handle = mat("handle", (0.55, 0.35, 0.17), 0.6)
brass = mat("buttons", (0.95, 0.75, 0.25), 0.3, coat=0.5)
hair_m = mat("hair", HAIR, 0.8)
nose_m = mat("nose", (0.95, 0.55, 0.45), 0.5)

# ------------------------------------------------------------------ joints (left side; the right is mirrored)
J = {
    "pelvis": Vector((0, 0, -0.12)), "spine": Vector((0, 0.0, -0.02)), "chest": Vector((0, 0.0, 0.09)),
    "neck": Vector((0, 0.0, 0.2)), "head": Vector((0, 0.0, 0.245)), "top": Vector((0, 0, 0.5)),
    "clav": Vector((0.03, 0.0, 0.175)), "shoulder": Vector((0.135, 0.0, 0.165)), "elbow": Vector((0.2, 0.012, 0.03)),
    "wrist": Vector((0.235, -0.01, -0.09)), "hand": Vector((0.25, -0.02, -0.15)),
    "hip": Vector((0.072, 0.0, -0.135)), "knee": Vector((0.078, -0.012, -0.28)), "ankle": Vector((0.078, 0.01, -0.405)),
    "toe": Vector((0.078, -0.075, -0.435)),
}


def L(v, s=1):
    return Vector((v.x * s, v.y, v.z))


# ------------------------------------------------------------------ the body
body = Blob("gardener_body", res=0.006)
body.ell((0, 0.005, 0.03), 0.16, 0.135, 0.15)  # a round tummy in dungarees
body.ell((0, 0.01, 0.125), 0.15, 0.115, 0.09)  # chest and shoulders
body.ell((0, 0.01, -0.095), 0.145, 0.115, 0.085)  # seat
head = Blob("gardener_head", res=0.005)
head.ell((0, 0.0, 0.345), 0.145, 0.135, 0.14)  # a big round head
for s in (-1, 1):
    head.ell((0.07 * s, -0.06, 0.3), 0.06, 0.06, 0.05)  # round cheeks
    head.ell((0.14 * s, 0.01, 0.335), 0.028, 0.02, 0.04)  # ears
neck = tube([(0, 0.0, 0.17), (0, 0.0, 0.26)], [0.062, 0.058], "neck")
limbs = []
for s in (1, -1):
    limbs.append(tube([L(J["shoulder"], s) + Vector((-0.02 * s, 0, 0)), L(J["elbow"], s), L(J["wrist"], s)], [0.05, 0.042, 0.036], "arm"))
    hb = Blob("hand", res=0.004)
    hb.ell(tuple(L(J["hand"], s) + Vector((0, 0, 0.012))), 0.042, 0.04, 0.05)  # a mitten of a hand
    hb.ell(tuple(L(J["hand"], s) + Vector((-0.02 * s, -0.03, 0.02))), 0.017, 0.017, 0.028, rot=(20, 0, 0))  # thumb
    limbs.append(hb)
    limbs.append(tube([L(J["hip"], s) + Vector((0, 0, 0.03)), L(J["knee"], s), L(J["ankle"], s) + Vector((0, 0, 0.02))],
                      [0.068, 0.06, 0.056], "leg"))


def seg_d(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def on_arm(c):
    s = 1 if c.x >= 0 else -1
    sh, el, wr = L(J["shoulder"], s), L(J["elbow"], s), L(J["wrist"], s)
    return abs(c.x) > 0.13 and min(seg_d(c, sh + Vector((0.02 * s, 0, 0)), el), seg_d(c, el, wr),
                                   (c - L(J["hand"], s)).length - 0.02) < 0.058


def is_head(c):
    return c.z > 0.235 or (c.z > 0.2 and math.hypot(c.x, c.y) < 0.09)


def colour(c, n):
    s = 1 if c.x >= 0 else -1
    if on_arm(c):
        el, wr = L(J["elbow"], s), L(J["wrist"], s)
        along = (c - el).dot((wr - el).normalized())  # past the elbow: rolled-up sleeves
        if along > 0.03:
            return SKIN
        if along > -0.005:
            return CUFF
        return SHIRT
    if is_head(c):  # head and neck, with hair below the hat at the back and sides, and rosy cheeks
        hair = max(ss(c.y, -0.01, 0.03) * ss(c.z, 0.28, 0.3), ss(abs(c.x), 0.118, 0.13) * ss(c.z, 0.35, 0.37) * ss(c.y, -0.03, 0.0))
        col = mix(SKIN, HAIR, hair)
        blush = ss((Vector((abs(c.x), c.y, c.z)) - Vector((0.08, -0.1, 0.3))).length, 0.04, 0.015)
        return mix(col, (0.97, 0.45, 0.42), 0.55 * blush)
    if c.z < -0.02:  # dungarees: seat and legs, with turn-ups at the bottom
        return mix(DENIM, (0.3, 0.45, 0.8), 0.5) if c.z < -0.375 else DENIM
    bib = abs(c.x) < 0.095 and c.y < 0.0 and c.z < 0.155
    strap = 0.055 < abs(c.x) < 0.095
    if c.z < 0.045 or bib or strap:
        return DENIM
    return SHIRT


skin = fuse([body, head, neck] + limbs, "gardener", voxel=0.0045, smooth=4, faces=9000)
# cut the garment seams into the mesh, then paint: sharp seams on the clothes, soft blends on the face
torso = lambda c: abs(c.x) < 0.17 and -0.05 < c.z < 0.26 and not on_arm(c)
planes = [((0, 0, 0.045), (0, 0, 1), torso), ((0, 0, 0.155), (0, 0, 1), lambda c: torso(c) and c.y < 0.01 and abs(c.x) < 0.11),
          ((0, 0, 0.2), (0, 0, 1), lambda c: math.hypot(c.x, c.y) < 0.11 and 0.15 < c.z < 0.25),
          ((0, 0, -0.375), (0, 0, 1), lambda c: c.z < -0.3)]
for x in (0.055, 0.095):
    for s_ in (1, -1):
        planes.append(((x * s_, 0, 0), (1, 0, 0), lambda c: torso(c) and c.z > 0.03))
for s_ in (1, -1):
    el, wr = L(J["elbow"], s_), L(J["wrist"], s_)
    d = (wr - el).normalized()
    for k in (-0.005, 0.03):
        planes.append((el + d * k, d, lambda c, s_=s_: on_arm(c) and c.x * s_ > 0))
K.cut(skin, planes)
K.paint_faces(skin, colour, K.vc_mat("gardener_clothes", 0.75, sheen=0.25), smooth=is_head)

# ------------------------------------------------------------------ rigid parts
parts = []
front = lambda x, z: K.surface(skin, (x, -2, z), (0, 1, 0))[0]
EYE_Z = 0.365
for s, side in ((1, "L"), (-1, "R")):
    e = front(0.052 * s, EYE_Z)
    parts.append(sphere(0.024, e + Vector((0, 0.008, 0)), "eye_" + side, dark, (0.9, 0.55, 1.3)))
    parts.append(sphere(0.007, e + Vector((0.006 * s, -0.008, 0.012)), "eye_" + side, white))
    b0, b1 = front(0.03 * s, EYE_Z + 0.05), front(0.085 * s, EYE_Z + 0.045)
    parts.append(rod(0.008, b0 + Vector((0, 0.004, 0)), b1 + Vector((0, 0.004, 0)), "head", hair_m, 0.006, 8))  # brows
    # a bushy moustache: two soft rolls under the nose
    m0 = front(0.0, 0.305)
    mb = Blob("moustache", res=0.004)
    mb.ell(tuple(m0 + Vector((0.04 * s, 0.0, -0.008))), 0.05, 0.022, 0.022, rot=(0, -18 * s, 0))
    mo = mb.mesh("moustache", smooth=1)
    K.paint(mo, [(hair_m, None)])
    mo["bone"] = "head"
    parts.append(mo)
nose = front(0, 0.33)
parts.append(sphere(0.042, nose + Vector((0, 0.012, 0)), "head", nose_m, (1.0, 0.9, 0.9)))
# the straw hat, tipped back a little
HAT = Vector((0, 0.015, 0.44))
parts.append(cyl(0.27, 0.018, HAT, "head", straw, rot=(-8, 0, 0), verts=48, bevel=0.4))
parts.append(cyl(0.145, 0.13, HAT + Vector((0, 0.008, 0.065)), "head", straw, rot=(-8, 0, 0), r2=0.125, verts=36))
parts.append(cyl(0.148, 0.036, HAT + Vector((0, 0.003, 0.022)), "head", band, rot=(-8, 0, 0), verts=36, bevel=0.2))
parts.append(sphere(0.03, HAT + Vector((0.13, -0.03, 0.03)), "head", band, (0.6, 1.0, 1.0)))  # a bow on the band
# buttons on the bib straps
for s in (-1, 1):
    b = front(0.075 * s, 0.14)
    parts.append(cyl(0.017, 0.01, b + Vector((0, -0.002, 0)), "chest", brass, rot=(90, 0, 0), verts=16))
# boots: round toes and a sole, on the feet
for s, side in ((1, "L"), (-1, "R")):
    a, t = L(J["ankle"], s), L(J["toe"], s)
    parts.append(sphere(0.064, (a.x, (a.y + t.y) / 2 - 0.005, FZ + 0.042), "foot_" + side, boot, (0.85, 1.4, 0.72)))
    parts.append(cyl(0.05, 0.05, (a.x, a.y + 0.005, FZ + 0.06), "foot_" + side, boot, verts=20))
    parts.append(cyl(0.056, 0.014, (a.x, (a.y + t.y) / 2 - 0.005, FZ + 0.008), "foot_" + side, sole, verts=24, scale=(0.95, 1.55, 1)))
# the little spade, held in the right hand
hR = L(J["hand"], -1)
grip_top = hR + Vector((0, -0.005, 0.1))
blade = hR + Vector((0, -0.03, -0.235))
parts.append(rod(0.013, grip_top, blade + Vector((0, 0.002, 0.07)), "hand_R", handle, verts=10))
parts.append(rod(0.016, grip_top + Vector((-0.03, 0, 0)), grip_top + Vector((0.03, 0, 0)), "hand_R", handle, verts=10))  # T grip
# the blade, turned a little on the handle so it reads from the side (as the game mostly sees him) and the front
parts.append(cyl(0.068, 0.012, blade, "hand_R", metal, rot=(80, 0, 50), verts=24, scale=(0.85, 1.2, 1), bevel=0.3))
parts.append(cyl(0.02, 0.05, blade + Vector((0, 0.001, 0.07)), "hand_R", metal, rot=(-8, 0, 0), verts=12))

# ------------------------------------------------------------------ skeleton
B = {
    "root": ((0, 0, FZ), (0, 0, FZ + 0.12), None, {"nodeform"}),
    "hips": (J["pelvis"], J["spine"], "root"),
    "spine": (J["spine"], J["chest"], "hips", {"connect"}),
    "chest": (J["chest"], J["neck"], "spine", {"connect"}),
    "neck": (J["neck"], J["head"], "chest", {"connect"}),
    "head": (J["head"], J["top"], "neck", {"connect"}),
}
for s, side in ((1, "L"), (-1, "R")):
    B["eye_" + side] = (front(0.052 * s, EYE_Z) + Vector((0, 0.008, 0)), front(0.052 * s, EYE_Z) + Vector((0, -0.02, 0)), "head", {"nodeform"})
    B["clavicle_" + side] = (L(J["clav"], s), L(J["shoulder"], s), "chest")
    B["upper_arm_" + side] = (L(J["shoulder"], s), L(J["elbow"], s), "clavicle_" + side, {"connect"})
    B["forearm_" + side] = (L(J["elbow"], s), L(J["wrist"], s), "upper_arm_" + side, {"connect"})
    B["hand_" + side] = (L(J["wrist"], s), L(J["hand"], s) + Vector((0, -0.005, -0.03)), "forearm_" + side, {"connect"})
    B["thigh_" + side] = (L(J["hip"], s), L(J["knee"], s), "hips")
    B["shin_" + side] = (L(J["knee"], s), L(J["ankle"], s), "thigh_" + side, {"connect"})
    B["foot_" + side] = (L(J["ankle"], s), L(J["toe"], s), "shin_" + side, {"connect"})
    B["ik_foot_" + side] = (L(J["ankle"], s), L(J["toe"], s), None, {"nodeform"})
rig = Rig("gardener", B)
for side in ("L", "R"):
    rig.ik("shin_" + side, "ik_foot_" + side, 2, hinge=("thigh_" + side, "shin_" + side), copy_rot="foot_" + side, tag=side)
ex = {}
for b in rig.pb:
    if b.name.endswith("_L"):
        ex[b.name] = lambda co: co.x < -0.02
    elif b.name.endswith("_R"):
        ex[b.name] = lambda co: co.x > 0.02
for b in ("head", "neck"):
    ex[b] = lambda co: co.z < 0.13
for b in ("thigh_L", "thigh_R", "shin_L", "shin_R"):
    ex[b] = (lambda f: (lambda co: f(co) or co.z > -0.05))(ex[b])
for b in ("upper_arm_L", "upper_arm_R", "clavicle_L", "clavicle_R", "forearm_L", "forearm_R", "hand_L", "hand_R"):
    ex[b] = (lambda f: (lambda co: f(co) or abs(co.x) < 0.09 or co.z > 0.24))(ex[b])
K.skin(skin, rig, smooth_iter=4, exclude=ex)
body = K.assemble("gardener", skin, rig, parts)


# ------------------------------------------------------------------ animation
def feet(p, l=(0, 0, 0), r=(0, 0, 0), lp=0.0, rp=0.0):
    """Places the boots: offsets of the toes (side, forward (+ is backwards), up) and a pitch (+ lifts the heel)."""
    for side, off, pitch in (("L", l, lp), ("R", r, rp)):
        h, t = rig.rest_head("foot_" + side), rig.rest_tail("foot_" + side)
        v = t - h
        R = Euler((math.radians(pitch), 0, 0)).to_matrix()
        p["@ik_foot_" + side] = tuple(v - R @ v + Vector(off))
        p["ik_foot_" + side] = (pitch, 0, 0)
    return p


def arms_down(p, l=0.0, r=0.0):
    """Relaxed arms: `l`, `r` swing them (+ backwards)."""
    p["upper_arm_L"] = (l, 0, 0)
    p["upper_arm_R"] = (r, 0, 0)
    p["forearm_L"] = (-12, 0, 0)
    p["forearm_R"] = (-12, 0, 0)
    return p


def idle(t):
    p = {}
    br = S(TAU * 2 * t)
    sway = S(TAU * t)
    p["@hips"] = (0.006 * sway, 0, -0.004 + 0.003 * br)
    p["hips"] = (0, 2 * sway, 0)
    p["spine"] = (-1 + 1.5 * br, -1.5 * sway, 0)
    p["chest"] = (-1.5 * br, -1 * sway, 0)
    p["neck"] = (0, 0, 8 * S(TAU * t + 0.4))
    p["head"] = (3 * S(TAU * 2 * t + 1), 4 * S(TAU * t + 1.3), 10 * S(TAU * t + 0.4) * ss(abs(S(TAU * t + 0.4)), 0.2, 0.8))
    arms_down(p, 3 * br, -3 * br)
    p["upper_arm_R"] = (-8 - 3 * br, 0, 0)  # the spade held a little forward
    p["forearm_R"] = (-30, 0, 0)
    p["clavicle_L"] = (0, 2 * br, 0)
    p["clavicle_R"] = (0, -2 * br, 0)
    blink = math.exp(-((t - 0.55) * 40) ** 2)
    for s in ("L", "R"):
        p["%eye_" + s] = (1, 1, 1 - 0.9 * blink)
    feet(p)
    return p


rig.cycle("idle", 60, idle, step=2)


def walk(t):
    """A bouncy jog: a flight phase, knees up, arms pumping, the hat bobbing a beat behind."""
    p = {}
    stride, lift = 0.2, 0.09
    offs = {}
    for side, ph in (("L", 0.0), ("R", 0.5)):
        u = (t - ph) % 1.0
        duty = 0.42
        if u < duty:
            s = u / duty
            fwd, up = -stride / 2 + stride * s, 0.0
            pitch = 50 * ss(s, 0.55, 1.0)
        else:
            s = (u - duty) / (1 - duty)
            fwd = stride / 2 - stride * smooth01(s)
            up = lift * S(math.pi * s) ** 0.8
            pitch = 50 - 60 * ss(s, 0.1, 0.8)
        offs[side] = ((0, fwd, up), pitch)
    feet(p, l=offs["L"][0], lp=offs["L"][1], r=offs["R"][0], rp=offs["R"][1])
    bounce = abs(S(TAU * t))
    p["@hips"] = (0.01 * S(TAU * t), 0, -0.012 + 0.03 * (1 - bounce) ** 0.6 * 0.8 - 0.01 * bounce)
    p["hips"] = (6, 5 * S(TAU * t), 10 * S(TAU * t))
    p["spine"] = (4, 0, -8 * S(TAU * t))
    p["chest"] = (2, -4 * S(TAU * t), -8 * S(TAU * t))
    p["neck"] = (-6, 0, 3 * S(TAU * t))
    p["head"] = (-4 + 4 * S(TAU * 2 * t - 1.2), 0, 3 * S(TAU * t))
    a = S(TAU * t)
    p["upper_arm_L"] = (-40 * a, -8, 0)
    p["upper_arm_R"] = (40 * a, 8, 0)
    p["forearm_L"] = (-50 - 20 * max(0, -a), 0, 0)
    p["forearm_R"] = (-50 - 20 * max(0, a), 0, 0)
    p["hand_R"] = (10, 0, 0)
    return p


rig.cycle("walk", 20, walk)


def dig_pose(stage):
    """Both hands on the spade: the right at the handle's middle, the left gripping the top."""
    p = {}
    if stage == "ready":
        p.update({"hips": (10, 0, 0), "spine": (8, 0, 6), "chest": (4, 0, 6), "neck": (-8, 0, 0), "head": (-6, 0, -6),
                  "upper_arm_R": (-35, 0, 0), "forearm_R": (-40, 0, 0), "hand_R": (20, 0, 0),
                  "upper_arm_L": (-45, 0, 15), "forearm_L": (-60, 0, -20), "@hips": (0, 0, -0.02)})
        feet(p, l=(0, -0.05, 0), r=(0, 0.05, 0), rp=15)
    elif stage == "raise":  # anticipation: the spade up and back, weight on the back foot, rising on the toes
        p.update({"hips": (-6, 0, 0), "spine": (-8, 0, -10), "chest": (-8, 0, -8), "neck": (6, 0, 0), "head": (4, 0, 4),
                  "upper_arm_R": (-110, 0, 10), "forearm_R": (-50, 0, 0), "hand_R": (30, 0, 0),
                  "upper_arm_L": (-120, 0, 20), "forearm_L": (-40, 0, -20), "@hips": (0, 0.02, 0.01)})
        feet(p, l=(0, -0.05, 0), r=(0, 0.05, 0), lp=10, rp=35)
    elif stage == "strike":  # the spade driven down and forward into the soil
        p.update({"hips": (18, 0, 0), "spine": (16, 0, 10), "chest": (10, 0, 8), "neck": (-12, 0, 0), "head": (-10, 0, -4),
                  "upper_arm_R": (-20, 0, 0), "forearm_R": (-10, 0, 0), "hand_R": (-10, 0, 0),
                  "upper_arm_L": (-50, 0, 20), "forearm_L": (-30, 0, -20), "@hips": (0, -0.03, -0.04)})
        feet(p, l=(0, -0.06, 0), r=(0, 0.06, 0), rp=25)
    elif stage == "lever":  # lever back and toss the soil over the shoulder
        p.update({"hips": (-2, 0, 0), "spine": (-6, 0, -12), "chest": (-10, 0, -14), "neck": (4, 0, 8), "head": (6, 0, 8),
                  "upper_arm_R": (-70, 0, -10), "forearm_R": (-80, 0, 0), "hand_R": (60, 0, 0),
                  "upper_arm_L": (-80, 0, 30), "forearm_L": (-60, 0, -20), "@hips": (0, 0.01, -0.01)})
        feet(p, l=(0, -0.05, 0), r=(0, 0.05, 0), rp=10)
    return p


rig.poses("dig", {1: dig_pose("ready"), 6: dig_pose("raise"), 10: dig_pose("strike"), 15: dig_pose("lever"),
                  20: dig_pose("ready")}, loop=True)


def throw_pose(stage):
    p = {}
    if stage == "rest":
        p = idle(0.0)
    elif stage == "wind":  # wind up: weight back, left arm back and high, the body turned away
        p.update({"hips": (-4, 0, 20), "spine": (-6, 0, 15), "chest": (-4, 0, 10), "neck": (0, 0, -20), "head": (4, 0, -15),
                  "upper_arm_L": (60, -60, 0), "forearm_L": (-90, 0, 0), "hand_L": (-30, 0, 0),
                  "upper_arm_R": (-20, 0, 0), "forearm_R": (-30, 0, 0), "@hips": (0, 0.02, -0.01)})
        feet(p, l=(0, 0.06, 0), r=(0, -0.06, 0), lp=20)
    elif stage == "release":  # the arm whips over, the body uncoils forward
        p.update({"hips": (10, 0, -15), "spine": (10, 0, -15), "chest": (8, 0, -10), "neck": (-6, 0, 10), "head": (-6, 0, 8),
                  "upper_arm_L": (-150, -20, 0), "forearm_L": (-10, 0, 0), "hand_L": (10, 0, 0),
                  "upper_arm_R": (20, 10, 0), "forearm_R": (-40, 0, 0), "@hips": (0, -0.03, -0.02)})
        feet(p, l=(0, -0.08, 0), r=(0, 0.06, 0), rp=40)
    elif stage == "follow":  # follow-through: the arm down across, leaning in
        p.update({"hips": (16, 0, -20), "spine": (14, 0, -15), "chest": (8, 0, -8), "neck": (-10, 0, 10), "head": (-6, 0, 6),
                  "upper_arm_L": (-50, 30, 0), "forearm_L": (-30, 0, 0), "hand_L": (20, 0, 0),
                  "upper_arm_R": (30, 10, 0), "forearm_R": (-40, 0, 0), "@hips": (0, -0.04, -0.035)})
        feet(p, l=(0, -0.08, 0), r=(0, 0.06, 0.03), rp=60)
    return p


rig.poses("throw", {1: throw_pose("rest"), 5: throw_pose("wind"), 9: throw_pose("release"), 13: throw_pose("follow"),
                    20: throw_pose("rest")})


def cheer(t):
    """Jumps for joy: crouch, spring up with both arms (and the spade) high, tuck, land."""
    p = {}
    up = max(0.0, S(TAU * t)) ** 0.8
    crouch = max(0.0, -S(TAU * t)) ** 0.8
    p["@hips"] = (0, 0, 0.14 * up - 0.06 * crouch)
    p["hips"] = (8 * crouch - 4 * up, 0, 0)
    p["spine"] = (4 * crouch - 6 * up, 0, 0)
    p["chest"] = (-6 * up, 0, 0)
    p["neck"] = (0, 0, 0)
    p["head"] = (-15 * up + 8 * crouch, 0, 6 * S(TAU * 2 * t))
    for s, sg in (("L", 1), ("R", -1)):
        p["clavicle_" + s] = (0, -12 * sg * up, 0)
        p["upper_arm_" + s] = (-20 * up, -sg * (40 + 110 * up), 0)
        p["forearm_" + s] = (-20 - 20 * crouch, 0, 0)
        p["hand_" + s] = (0, 0, 20 * S(TAU * 2 * t) * sg)
        p["%eye_" + s] = (1, 1, 0.25 + 0.75 * crouch)  # squeezed shut with joy at the top
    tuck = up * 0.07
    feet(p, l=(0, 0.02, tuck + 0.14 * up), r=(0, 0.02, tuck + 0.14 * up), lp=40 * up + 20 * crouch, rp=40 * up + 20 * crouch)
    return p


rig.cycle("cheer", 24, cheer, step=1)


def die_pose(stage):
    p = {"ik": 0.0}
    if stage == "stand":
        p = idle(0.0)
    elif stage == "shock":  # jumps out of his boots, arms flung up, eyes wide
        p.update({"@hips": (0, 0, 0.12), "hips": (-8, 0, 0), "spine": (-8, 0, 0), "head": (-10, 0, 0),
                  "upper_arm_L": (0, -150, 0), "upper_arm_R": (0, 150, 0), "forearm_L": (-20, 0, 0), "forearm_R": (-20, 0, 0),
                  "thigh_L": (-10, 0, 10), "thigh_R": (-10, 0, -10), "shin_L": (30, 0, 0), "shin_R": (30, 0, 0),
                  "%eye_L": (1.2, 1, 1.3), "%eye_R": (1.2, 1, 1.3)})
    elif stage in ("fall", "flat", "bounce"):  # flat on his back, arms and legs out like a starfish
        h = {"fall": 0.0, "flat": -0.2, "bounce": -0.16}[stage]
        rot = {"fall": -50, "flat": -88, "bounce": -84}[stage]
        p.update({"@hips": (0, 0.2 if stage != "fall" else 0.1, h), "hips": (rot, 0, 0), "spine": (-4, 0, 0), "neck": (10, 0, 0),
                  "head": (10, 0, 20), "upper_arm_L": (-20, -80, 0), "upper_arm_R": (-20, 80, 0), "forearm_L": (-20, 0, 0),
                  "forearm_R": (-20, 0, 0), "thigh_L": (-40, 0, 20), "thigh_R": (-40, 0, -20), "shin_L": (30, 0, 0),
                  "shin_R": (30, 0, 0), "foot_L": (-20, 0, 0), "foot_R": (-20, 0, 0),
                  "%eye_L": (1, 1, 0.12), "%eye_R": (1, 1, 0.12)})
    return p


rig.poses("die", {1: die_pose("stand"), 6: die_pose("shock"), 13: die_pose("fall"), 18: die_pose("flat"),
                  22: die_pose("bounce"), 26: die_pose("flat"), 30: die_pose("flat")})

K.export("gardener", rig, body, out_dir)
