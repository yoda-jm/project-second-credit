"""Frostpeak Games athletes on the shared humanoid rig (smooth skin, IK feet): the speed skater (skin suit, hood,
glasses, clap skates) and the ski jumper (suit, helmet, goggles, long skis on their own bones under the feet, so they
open into a V). The materials "suit" and "suit_accent" are recoloured per nation in the game. One glTF animation per
action, 30 fps. Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/frostpeak_athletes.py -- godot/games/frostpeak/art/models
About 1.8 m tall, facing -Y; the skater's blades and the jumper's skis stand on z = 0 in every animation.
"""
import bpy, math, os, sys
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *

FPS = 30
SKATE_Z = 0.075   # the blade lifts the skater's boot off the ice
SKI_Z = 0.025     # the ski under the jumper's boot
H = (0, -0.012, 1.665)  # the head's centre


def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


def grown(rings, k=1.035, zlo=-1.0, zhi=9.0):
    return [(z, rx * k + 0.002, ry * k + 0.002, cy) for z, rx, ry, cy, sq in rings if zlo <= z <= zhi]


def arc(center, rx, ry, z, a0, a1, n=9):
    """Points round the head at height z, for visors and bands."""
    cx, cy = center
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))), z) for i in range(n)]


def stripe(path, s, off, r):
    """A stripe down the outside of a limb path [(x, y, z, radius)]."""
    return [(x + s * (rad + off), y, z, r) for x, y, z, rad in path]


def body(kind, sk):
    suit = mat("suit", (0.85, 0.15, 0.15), 0.3, coat=0.5)
    trim = mat("suit_trim", (0.96, 0.96, 0.96), 0.35, coat=0.3)
    accent = mat("suit_accent", (0.1, 0.2, 0.6), 0.3, coat=0.5)
    skin = mat("skin", (0.9, 0.68, 0.54), 0.55)
    white = mat("eye_white", (0.95, 0.95, 0.93), 0.2)
    iris = mat("iris", (0.15, 0.25, 0.4), 0.1, coat=1.0)
    glove = mat("gloves", (0.1, 0.1, 0.12), 0.5)
    boot = mat("athlete_boot", (0.08, 0.08, 0.1), 0.35, coat=0.5)
    visor = mat("goggles", (0.25, 0.55, 0.85), 0.03, 0.8, coat=1.0)
    frame = mat("goggle_frame", (0.06, 0.06, 0.07), 0.4)
    number = mat("bib_number", (0.08, 0.08, 0.1), 0.4)
    seam = mat("seam", (0.05, 0.05, 0.07), 0.6)
    shape = {"chest": 0.98, "waist": 0.95, "hips": 0.98, "legs": 1.06, "arms": 0.96}
    human_body(sk, skin, suit, suit, white, iris, hair=mat("hair", (0.25, 0.17, 0.1), 0.6), shoes=boot, sole=boot,
               glove=glove, sleeves="long", hands="relaxed", shape=shape, shoe_height=0.16 if kind == "skater" else 0.24,
               neck_mat=suit if kind == "skater" else None)
    torso = torso_rings(0.8, 1.51, 0.0, shape)
    # accent panels down both sides of the body, from the armpit to the hip
    for a0, a1 in ((-26, 26), (154, 206)):
        shell(grown(torso, zlo=0.9, zhi=1.38), a0, a1, "~body", accent, segs=8)
    # the zip
    tube([(0, -0.1, 1.44, 0.004), (0, -0.112, 1.3, 0.004), (0, -0.1, 1.12, 0.004)], "~body", seam, 6, 0.03)
    for X, s in (("L", 1), ("R", -1)):
        lp = leg_path(sk, X, 0.0, shape=shape["legs"])
        tube(stripe(lp[1:-1], s, 0.0, 0.012), "~leg." + X, accent, 8, 0.02)
        tube(arm_path(sk, X, 0.004, 0.86, 1.0, shape=shape["arms"]), "~arm." + X, accent, 14, 0.01)   # cuff
    if kind == "skater":
        for y, sgn in ((-0.108, 1), (0.1, -1)):   # the race bib, front and back
            box((0.15, 0.008, 0.13), (0, y, 1.25), "~body", trim, bevel=0.004)
            box((0.085, 0.01, 0.048), (0, y - 0.003 * sgn, 1.26), "~body", number, bevel=0.003)
        # the aero hood: open at the face, a seam over the crown
        cx, cy, cz = H
        hood = [(cz - 0.11, 0.07, 0.07, cy + 0.022), (cz - 0.065, 0.098, 0.102, cy + 0.02), (cz - 0.005, 0.103, 0.11, cy + 0.02),
                (cz + 0.055, 0.098, 0.106, cy + 0.02), (cz + 0.105, 0.075, 0.082, cy + 0.02), (cz + 0.13, 0.03, 0.035, cy + 0.02)]
        shell(hood, -48, 228, "head", suit, thick=0.008, segs=18)
        tube([(0, cy + 0.125, cz - 0.045, 0.006), (0, cy + 0.118, cz + 0.075, 0.006), (0, cy + 0.05, cz + 0.135, 0.006),
              (0, cy - 0.03, cz + 0.118, 0.006)], "head", accent, 6, 0.02)
        # wraparound glasses: a mirrored band across the eyes, a thin frame over it
        tube([(p[0], p[1], p[2], 0.017) for p in arc((0, cy + 0.004), 0.1, 0.106, cz + 0.017, -160, -20)], "head", visor, 8, 0.012)
        tube([(p[0], p[1], p[2], 0.005) for p in arc((0, cy + 0.004), 0.103, 0.11, cz + 0.036, -160, -20)], "head", frame, 6, 0.012)
        # clap skates: a long blade on a tube under each boot, the hinge under the toe (rigid on the foot)
        blade = mat("blade", (0.88, 0.9, 0.93), 0.1, 1.0)
        holder = mat("blade_holder", (0.2, 0.2, 0.22), 0.3, 0.6)
        for X in "LR":
            x = sk.head("foot." + X).x
            f = "foot." + X
            box((0.006, 0.46, 0.03), (x, -0.08, -SKATE_Z + 0.015), f, blade, bevel=0.002)
            sphere(0.015, (x, -0.31, -SKATE_Z + 0.022), f, blade, (0.35, 1.0, 1.0), 10, 8)
            tube([(x, -0.28, -SKATE_Z + 0.04, 0.011), (x, 0.13, -SKATE_Z + 0.04, 0.011)], f, holder, 8, 0.04)
            box((0.034, 0.05, 0.05), (x, -0.13, -0.012), f, holder, bevel=0.008)   # the clap hinge
            box((0.03, 0.04, 0.05), (x, 0.06, -0.012), f, holder, bevel=0.008)    # the heel post
    else:
        for a0, a1 in ((-145, -35), (35, 145)):   # the big bib, front and back
            shell(grown(torso, 1.06, 1.1, 1.39), a0, a1, "~body", trim, segs=10)
        box((0.11, 0.01, 0.065), (0, -0.118, 1.28), "~body", number, bevel=0.004)
        box((0.11, 0.01, 0.065), (0, 0.116, 1.28), "~body", number, bevel=0.004)
        shell(grown(torso, 1.04, 1.38, 1.43), -180, 180, "~body", accent, segs=24)
        # helmet: a shell with a raised ridge, large goggles on a strap, a chin strap
        cx, cy, cz = H
        shell_m = mat("helmet", (0.96, 0.96, 0.97), 0.2, coat=1.0)
        strap = mat("strap", (0.1, 0.1, 0.1), 0.5)
        sphere(0.117, (0, cy + 0.012, cz + 0.032), "head", shell_m, (0.97, 1.05, 0.93))
        tube([(0, cy - 0.1, cz + 0.095, 0.011), (0, cy - 0.02, cz + 0.135, 0.013), (0, cy + 0.08, cz + 0.117, 0.011), (0, cy + 0.125, cz + 0.035, 0.01)], "head", accent, 8, 0.015)
        tube([(p[0], p[1], p[2], 0.008) for p in arc((0, cy + 0.012), 0.116, 0.123, cz - 0.04, -200, 20, 12)], "head", accent, 8, 0.015)
        tube([(p[0], p[1], p[2], 0.026) for p in arc((0, cy), 0.098, 0.104, cz + 0.018, -158, -22)], "head", visor, 10, 0.012)
        tube([(p[0], p[1], p[2], 0.008) for p in arc((0, cy), 0.103, 0.11, cz + 0.018, -20, 200, 11)], "head", strap, 6, 0.015)
        tube([(0.082, cy - 0.02, cz - 0.02, 0.005), (0.06, cy - 0.055, cz - 0.1, 0.005), (0, cy - 0.07, cz - 0.115, 0.005),
              (-0.06, cy - 0.055, cz - 0.1, 0.005), (-0.082, cy - 0.02, cz - 0.02, 0.005)], "head", strap, 6, 0.012)
        for X in "LR":   # laces up the tall boots
            x = sk.head("foot." + X).x
            for i in range(4):
                box((0.045, 0.008, 0.009), (x, -0.052 + 0.004 * i, 0.12 + i * 0.03), "~foot." + X, trim, bevel=0.003)
        ski = mat("ski", (0.95, 0.78, 0.1), 0.25, coat=0.8)
        ski_edge = mat("ski_edge", (0.1, 0.1, 0.12), 0.3)
        stripe_m = mat("ski_stripe", (0.85, 0.12, 0.1), 0.3, coat=0.8)
        binding = mat("binding", (0.2, 0.2, 0.22), 0.3, 0.6)
        for X in "LR":
            x = sk.head("foot." + X).x
            b = "ski." + X
            box((0.11, 2.2, 0.018), (x, -0.45, -0.012), b, ski, bevel=0.005)
            box((0.112, 2.2, 0.005), (x, -0.45, -0.022), b, ski_edge, bevel=0.002)
            box((0.03, 2.1, 0.004), (x, -0.45, -0.002), b, stripe_m, bevel=0.001)
            py, pz = -1.53, -0.012   # the tip turns up in steps
            for i, th in enumerate((0.15, 0.4, 0.7, 1.0)):
                dy, dz = -math.cos(th) * 0.09, math.sin(th) * 0.09
                box((0.11 - i * 0.006, 0.1, 0.018), (x, py + dy * 0.5, pz + dz * 0.5), b, ski, rot=(-th, 0, 0), bevel=0.004)
                py, pz = py + dy, pz + dz
            box((0.07, 0.1, 0.02), (x, -0.15, 0.004), b, binding, bevel=0.005)    # toe piece
            box((0.075, 0.08, 0.012), (x, 0.13, 0.0), b, binding, bevel=0.004)   # heel plate


# ------------------------------------------------------------------ animation

def stand(z0, spread=0.11):
    return {"ik_foot.L": (spread, 0.0, 0.09 + z0, 0, 6), "ik_foot.R": (-spread, 0.0, 0.09 + z0, 0, 6), "ikw.L": 1.0, "ikw.R": 1.0}


def idle(z0):
    k = {}
    base = P(stand(z0), **{"arm.L": (4, 0, 8), "arm.R": (4, 0, 8), "forearm.L": (14, 0, 0), "forearm.R": (14, 0, 0),
                           "hand.L": (0, 0, -6), "hand.R": (0, 0, -6), "clavicle.L": (0, 0, -3), "clavicle.R": (0, 0, -3)})
    for i in range(0, 61, 5):
        t = i / 60.0
        br = math.sin(2 * math.pi * t * 2)          # two breaths
        w = math.sin(2 * math.pi * t)                # the weight drifts from foot to foot
        k[i + 1] = P(base, **{"root": (0.03 * w, 0, z0 - 0.012 - 0.006 * abs(w)), "hips": (0, 3 * w, -3 * w),
                              "spine": (1, -1 * w, 1.5 * w), "chest": (1.5 + 1.2 * br, -1 * w, 1.2 * w),
                              "clavicle.L": (0, 0, -3 + 1.5 * br), "clavicle.R": (0, 0, -3 + 1.5 * br),
                              "neck": (0, 4 * math.sin(2 * math.pi * (t - 0.2)), 0), "head": (-2, 6 * math.sin(2 * math.pi * (t - 0.25)), 0.5 * w)})
    return Anim(k, loop=True)


def wave(z0):
    k = {}
    base = P(stand(z0), **{"arm.L": (4, 0, 8), "forearm.L": (14, 0, 0), "arm.R": (20, -30, 128), "clavicle.R": (0, 0, 12),
                           "chest": (0, -6, -3), "head": (-4, -8, 0), "root": (-0.02, 0, z0 - 0.01), "hand.R": (0, 0, 0)})
    for i in range(0, 21, 5):
        t = i / 20.0
        s = math.sin(2 * math.pi * t)
        k[i + 1] = P(base, **{"forearm.R": (25, 0, 28 * s), "hand.R": (0, 0, 12 * s), "arm.R": (20, -30, 128 + 4 * s)})
    return Anim(k, loop=True)


def celebrate(z0):
    low = P(stand(z0, 0.13), **{"root": (0, 0, z0 - 0.1), "arm.L": (150, -20, 35), "arm.R": (150, -20, 35), "forearm.L": (40, 0, 0),
                                "forearm.R": (40, 0, 0), "clavicle.L": (0, 0, 14), "clavicle.R": (0, 0, 14), "chest": (-6, 0, 0),
                                "head": (-18, 0, 0), "hips": (6, 0, 0)})
    high = P(low, **{"root": (0, 0, z0), "arm.L": (165, -20, 25), "arm.R": (165, -20, 25), "forearm.L": (8, 0, 0),
                     "forearm.R": (8, 0, 0), "chest": (-10, 0, 0), "head": (-25, 0, 0), "hips": (0, 0, 0)})
    return Anim({1: low, 5: high, 8: P(high, **{"root": (0, 0, z0 - 0.02)}), 12: P(low, **{"root": (0, 0, z0 - 0.07)}), 17: low}, loop=True)


def skater_actions(sk):
    z0 = SKATE_Z
    ank = 0.09 + z0
    crouch = {"hips": (40, 0, 0), "spine": (14, 0, 0), "chest": (10, 0, 0), "neck": (-26, 0, 0), "head": (-26, 0, 0),
              "clavicle.L": (6, 0, 0), "clavicle.R": (6, 0, 0), "ikw.L": 1.0, "ikw.R": 1.0,
              "hand.L": (0, 0, -10), "hand.R": (0, 0, -10)}
    # the stride: a foot's path through one cycle (phase: position left/fwd/up, blade roll), mirrored for the right
    path = [(0.0, (0.55, -0.1, 0.0, 22)), (0.12, (0.4, -0.3, 0.1, 10)), (0.25, (0.2, -0.22, 0.12, 0)),
            (0.36, (0.07, 0.08, 0.0, -4)), (0.5, (0.05, 0.06, 0.0, -6)), (0.7, (0.06, 0.0, 0.0, -2)),
            (0.86, (0.14, -0.04, 0.0, 8)), (1.0, (0.55, -0.1, 0.0, 22))]

    def foot_at(ph):
        ph %= 1.0
        for (a, pa), (b, pb) in zip(path, path[1:]):
            if a <= ph <= b:
                u = smoothstep(0, 1, (ph - a) / (b - a))
                return tuple(pa[i] + (pb[i] - pa[i]) * u for i in range(4))
    skate = {}
    for i in range(0, 21, 2):
        t = i / 20.0
        k = dict(crouch)
        for X, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            x, y, z, roll = foot_at(t + off)
            k["ik_foot." + X] = (x * s, y, ank + z, 0, 4)
            k["foot." + X] = (0, roll, 0)
        sw = math.sin(2 * math.pi * (t - 0.4))        # +1 when the weight is over the left blade
        k["root"] = (0.11 * sw, 0.0, -0.3 + 0.02 * math.cos(4 * math.pi * (t - 0.1)))
        k["hips"] = (40, 4 * sw, -5 * sw)
        k["spine"] = (14, -3 * sw, 4 * sw)
        k["chest"] = (10, -4 * sw, 2 * sw)
        k["head"] = (-26, 5 * sw, -4 * sw)
        a = math.cos(2 * math.pi * (t + 0.02))       # the left arm swings back as the left leg pushes
        k["arm.L"] = (8 - 48 * a, -10, 16 + 10 * max(0, a), 18 * max(0, -a))
        k["arm.R"] = (8 + 48 * a, -10, 16 + 10 * max(0, -a), 18 * max(0, a))
        k["forearm.L"] = (20 + 25 * max(0, -a), 0, 0)
        k["forearm.R"] = (20 + 25 * max(0, a), 0, 0)
        skate[i + 1] = k
    glide = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        s = math.sin(2 * math.pi * t)
        glide[i + 1] = P(crouch, **{"ik_foot.L": (0.12, 0.03, ank, 0, 4), "ik_foot.R": (-0.12, -0.03, ank, 0, 4),
                                    "root": (0.03 * s, 0, -0.29), "hips": (42, 2 * s, -2 * s), "spine": (14, 0, 0),
                                    "arm.L": (-30, 92, 4), "arm.R": (-30, 92, 4), "forearm.L": (108, 0, 0),
                                    "forearm.R": (108, 0, 0), "hand.L": (0, 0, 0), "hand.R": (0, 0, 0),
                                    "head": (-26, -3 * s, 0)})
    ready = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        br = math.sin(2 * math.pi * t)
        ready[i + 1] = P(crouch, **{"ik_foot.L": (0.12, 0.22, ank, 0, 12), "ik_foot.R": (-0.2, -0.22, ank, 0, 50),
                                    "root": (0.0, 0.06, -0.3 - 0.006 * br), "hips": (46, -10, 0), "spine": (12, -4, 0),
                                    "chest": (8 + 1.5 * br, 0, 0), "arm.L": (30, 0, 10), "forearm.L": (40, 0, 0),
                                    "arm.R": (-45, 0, 14), "forearm.R": (20, 0, 0), "head": (-30, 10, 0)})
    return {"idle": idle(z0), "wave": wave(z0), "celebrate": celebrate(z0), "skate": Anim(skate, loop=True),
            "glide": Anim(glide, loop=True), "ready": Anim(ready, loop=True)}


def jumper_actions(sk):
    z0 = SKI_Z
    ank = 0.09 + z0
    tuck = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        s = math.sin(2 * math.pi * t)
        tuck[i + 1] = {"ik_foot.L": (0.1, 0.0, ank, 0, 0), "ik_foot.R": (-0.1, 0.0, ank, 0, 0), "ikw.L": 1.0, "ikw.R": 1.0,
                       "root": (0, -0.06, -0.47 - 0.005 * s), "hips": (70, 0, 0), "spine": (12 + s, 0, 0), "chest": (6, 0, 0),
                       "neck": (-32, 0, 0), "head": (-34, 0, 0), "arm.L": (6, -30, 8), "arm.R": (6, -30, 8),
                       "forearm.L": (6, 0, 0), "forearm.R": (6, 0, 0), "hand.L": (0, 0, 10), "hand.R": (0, 0, 10)}
    fly = {"ikw.L": 0.0, "ikw.R": 0.0, "hips": (60, 0, 0), "spine": (4, 0, 0), "chest": (2, 0, 0), "neck": (-24, 0, 0),
           "head": (-32, 0, 0), "arm.L": (-16, -40, 16), "arm.R": (-16, -40, 16), "forearm.L": (4, 0, 0), "forearm.R": (4, 0, 0),
           "hand.L": (0, 0, 12), "hand.R": (0, 0, 12), "thigh.L": (0, -8, 6), "thigh.R": (0, -8, 6), "shin.L": (4, 0, 0),
           "shin.R": (4, 0, 0), "foot.L": (28, 0, 0), "foot.R": (28, 0, 0), "ski.L": (40, 0, 20), "ski.R": (40, 0, 20),
           "root": (0, 0, -0.1)}
    flight = {}
    for i in range(0, 61, 10):
        t = i / 60.0
        s, c = math.sin(2 * math.pi * t), math.sin(2 * math.pi * (t * 2 + 0.3))
        flight[i + 1] = P(fly, **{"hips": (60 + 1.5 * s, 0, 0), "arm.L": (-16 + 2 * c, -40, 16 + 2 * s), "arm.R": (-16 - 2 * c, -40, 16 - 2 * s),
                                  "ski.L": (40 + c, 0, 20 + s), "ski.R": (40 - c, 0, 20 - s), "head": (-32 + s, 0, 0)})
    tele_base = {"ikw.L": 1.0, "ikw.R": 1.0, "spine": (10, 0, 0), "chest": (6, 0, 0), "neck": (-8, 0, 0), "head": (-10, 0, 0),
                 "arm.L": (14, -20, 62), "arm.R": (14, -20, 62), "forearm.L": (18, 0, 0), "forearm.R": (18, 0, 0),
                 "hand.L": (0, 0, 20), "hand.R": (0, 0, 20), "clavicle.L": (0, 0, 6), "clavicle.R": (0, 0, 6)}
    back = foot_ground(-0.1, -0.34, -32, sk)
    tele = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        s = math.sin(2 * math.pi * t)
        tele[i + 1] = P(tele_base, **{"ik_foot.L": (0.1, 0.34, ank, 0, 0), "ik_foot.R": (back[0], back[1], back[2] + z0, -32, 0),
                                      "ski.R": (32, 0, 0), "toe.R": (32, 0, 0), "root": (0, 0.0, -0.3 - 0.015 * s),
                                      "arm.L": (14, -20, 62 + 3 * s), "arm.R": (14, -20, 62 - 3 * s), "hips": (8, 0, 2 * s)})
    stand_ = stand(z0)
    fall = {1: P(tele[1]),
            5: P(tele_base, **{"ik_foot.L": (0.1, 0.34, ank, 0, 0), "ik_foot.R": (back[0], back[1], back[2] + z0, -32, 0),
                               "ski.R": (32, 0, 0), "root": (0.04, -0.05, -0.22), "turn": (-14, 0, 8), "spine": (-12, 0, 0),
                               "arm.L": (150, 0, 50), "arm.R": (40, 0, 90), "forearm.L": (30, 0, 0), "head": (-10, 0, 10)}),
            9: {"ikw.L": 0.5, "ikw.R": 0.3, "ik_foot.L": (0.1, 0.34, ank, 0, 0), "ik_foot.R": (back[0], back[1], back[2] + z0, -32, 0),
                "turn": (-40, 0, 25), "root": (0.1, -0.1, 0.0), "spine": (-10, 0, 10), "chest": (-6, 0, 0),
                "arm.L": (160, 0, 40), "arm.R": (90, 0, 80), "forearm.L": (40, 0, 0), "forearm.R": (30, 0, 0),
                "thigh.L": (40, 0, 10), "shin.L": (60, 0, 0), "thigh.R": (10, 0, 5), "shin.R": (50, 0, 0), "ski.L": (0, 0, -15),
                "ski.R": (10, 0, 15), "head": (10, 0, 20)},
            14: {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-82, 0, 30), "root": (0.2, -0.3, 0.14), "spine": (-6, 0, 12), "chest": (-4, 0, 6),
                 "arm.L": (120, 0, 60), "arm.R": (40, 0, 80), "forearm.L": (40, 0, 0), "forearm.R": (30, 0, 0),
                 "thigh.L": (22, 0, 12), "shin.L": (35, 0, 0), "thigh.R": (12, 0, 8), "shin.R": (20, 0, 0), "foot.L": (-25, 0, 0),
                 "foot.R": (-25, 0, 0), "ski.L": (-55, 0, -25), "ski.R": (-60, 0, 22), "head": (20, 20, 10)},
            17: {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-88, 0, 34), "root": (0.2, -0.32, 0.18), "spine": (-4, 0, 12), "chest": (-2, 0, 6),
                 "arm.L": (110, 0, 70), "arm.R": (30, 0, 70), "forearm.L": (30, 0, 0), "forearm.R": (20, 0, 0),
                 "thigh.L": (18, 0, 12), "shin.L": (30, 0, 0), "thigh.R": (10, 0, 8), "shin.R": (16, 0, 0), "foot.L": (-25, 0, 0),
                 "foot.R": (-25, 0, 0), "ski.L": (-58, 0, -28), "ski.R": (-62, 0, 24), "head": (14, 25, 10)},
            20: {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-86, 0, 32), "root": (0.2, -0.32, 0.15), "spine": (-4, 0, 12), "chest": (-2, 0, 6),
                 "arm.L": (110, 0, 72), "arm.R": (28, 0, 72), "forearm.L": (30, 0, 0), "forearm.R": (20, 0, 0),
                 "thigh.L": (16, 0, 12), "shin.L": (28, 0, 0), "thigh.R": (9, 0, 8), "shin.R": (15, 0, 0), "foot.L": (-25, 0, 0),
                 "foot.R": (-25, 0, 0), "ski.L": (-58, 0, -28), "ski.R": (-62, 0, 24), "head": (10, 30, 10)}}
    return {"idle": idle(z0), "wave": wave(z0), "celebrate": celebrate(z0), "tuck": Anim(tuck, loop=True),
            "flight": Anim(flight, loop=True), "telemark": Anim(tele, loop=True), "fall": Anim(fall)}


def build(kind):
    clear()
    sk = Skeleton(proportions(), skis=(kind == "jumper"))
    body(kind, sk)
    acts = skater_actions(sk) if kind == "skater" else jumper_actions(sk)
    rig_export(kind, out_dir, acts, skeleton=sk, fps=FPS)


only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
for k in ("skater", "jumper"):
    if not only or k in only:
        build(k)
