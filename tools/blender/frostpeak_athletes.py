"""Frostpeak Games athletes on the shared humanoid rig (smooth skin, IK feet): the speed skater (skin suit, hood,
glasses, clap skates), the ski jumper (suit, helmet, goggles, long skis on their own bones under the feet, so they
open into a V) and the biathlete (race suit and bib, a knitted hat, sports glasses, narrow skating skis; the rifle
and the poles are props of their own, "rifle" and "ski_pole", which the game puts in the hands or on the back) and the
bobsledder (a speed suit, a bob helmet with its visor, spiked sprint shoes; pushing, jumping in, seated in the sled).
The materials "suit" and "suit_accent" are recoloured per nation in the game. One glTF animation per action, 30 fps.
Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/frostpeak_athletes.py -- godot/games/frostpeak/art/models [names]
(names: skater, jumper, biathlete, bobber, rifle, ski_pole; all when none are given)
About 1.8 m tall, facing -Y; the skater's blades and the skis stand on z = 0 in every animation.
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
    if kind == "biathlete":
        shape = {"chest": 1.0, "waist": 0.95, "hips": 0.97, "legs": 1.04, "arms": 0.98}
    if kind == "bobber":  # sprinters' build: broad, powerful thighs
        shape = {"chest": 1.07, "waist": 1.0, "hips": 1.03, "legs": 1.12, "arms": 1.06}
    human_body(sk, skin, suit, suit, white, iris, hair=mat("hair", (0.25, 0.17, 0.1), 0.6), shoes=boot, sole=boot,
               glove=glove, sleeves="long", hands="fist" if kind == "biathlete" else ("grip" if kind == "bobber" else "relaxed"), shape=shape,
               shoe_height={"skater": 0.16, "jumper": 0.24, "bobber": 0.13}.get(kind, 0.2), neck_mat=suit if kind != "jumper" else None)
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
    elif kind == "bobber":
        # the start number on the chest and back, a white yoke across the shoulders
        for a0, a1 in ((-40, 40), (140, 220)):
            shell(grown(torso, 1.04, 1.36, 1.46), a0, a1, "~body", trim, segs=10)
        box((0.1, 0.01, 0.06), (0, -0.117, 1.24), "~body", number, bevel=0.004)
        box((0.1, 0.01, 0.06), (0, 0.115, 1.24), "~body", number, bevel=0.004)
        # the helmet: a round shell over the ears, a tinted visor across the face, a ridge and a chin guard
        cx, cy, cz = H
        shell_m = mat("helmet", (0.96, 0.96, 0.97), 0.18, coat=1.0)
        strap = mat("strap", (0.1, 0.1, 0.1), 0.5)
        sphere(0.128, (0, cy + 0.01, cz + 0.02), "head", shell_m, (0.97, 1.08, 0.98))
        tube([(0, cy - 0.11, cz + 0.1, 0.012), (0, cy - 0.02, cz + 0.145, 0.014), (0, cy + 0.08, cz + 0.13, 0.012),
              (0, cy + 0.135, cz + 0.03, 0.011)], "head", accent, 8, 0.015)
        tube([(p[0], p[1], p[2], 0.01) for p in arc((0, cy + 0.01), 0.125, 0.135, cz - 0.05, -205, 25, 13)], "head", accent, 8, 0.015)
        tube([(p[0], p[1], p[2], 0.03) for p in arc((0, cy - 0.005), 0.112, 0.12, cz + 0.005, -150, -30)], "head", visor, 10, 0.012)
        tube([(0.09, cy - 0.04, cz - 0.07, 0.012), (0.05, cy - 0.1, cz - 0.1, 0.013), (0, cy - 0.115, cz - 0.105, 0.013),
              (-0.05, cy - 0.1, cz - 0.1, 0.013), (-0.09, cy - 0.04, cz - 0.07, 0.012)], "head", shell_m, 8, 0.012)
        # the spiked sprint shoes: a spike plate under the ball of the foot
        spikes = mat("spikes", (0.7, 0.72, 0.75), 0.3, 0.9)
        for X in "LR":
            x = sk.head("foot." + X).x
            box((0.085, 0.13, 0.012), (x, -0.13, 0.004), "~foot." + X, spikes, bevel=0.003)
            for i in range(3):
                box((0.07, 0.012, 0.02), (x, -0.08 - i * 0.05, 0.034 + 0.004 * i), "~foot." + X, trim, bevel=0.003)
    elif kind == "biathlete":
        torso2 = torso_rings(0.8, 1.51, 0.0, shape)
        for a0, a1 in ((-150, -30), (30, 150)):   # the bib, front and back, with its number
            shell(grown(torso2, 1.05, 1.02, 1.4), a0, a1, "~body", trim, segs=10)
        box((0.12, 0.01, 0.07), (0, -0.117, 1.25), "~body", number, bevel=0.004)
        box((0.12, 0.01, 0.07), (0, 0.115, 1.25), "~body", number, bevel=0.004)
        # the rifle harness: two straps over the shoulders to a pad between the shoulder blades
        strap = mat("strap", (0.1, 0.1, 0.1), 0.5)
        for s in (1, -1):
            tube([(s * 0.1, -0.1, 1.2, 0.008), (s * 0.13, -0.08, 1.42, 0.008), (s * 0.1, 0.03, 1.47, 0.008),
                  (s * 0.07, 0.12, 1.36, 0.008), (s * 0.04, 0.115, 1.22, 0.008)], "~body", strap, 6, 0.02, ell=(1.6, 0.5))
        box((0.1, 0.02, 0.12), (0, 0.125, 1.3), "~body", strap, bevel=0.008)
        # a knitted hat with a folded brim and a pompom, and wraparound sports glasses
        cx, cy, cz = H
        knit = mat("hat", (0.95, 0.95, 0.96), 0.85)
        hat = [(cz + 0.02, 0.1, 0.108, cy + 0.012), (cz + 0.06, 0.1, 0.108, cy + 0.012), (cz + 0.1, 0.086, 0.094, cy + 0.012),
               (cz + 0.13, 0.055, 0.06, cy + 0.012), (cz + 0.145, 0.02, 0.02, cy + 0.012)]
        shell(hat, -180, 180, "head", knit, thick=0.01, segs=24)
        tube([(p[0], p[1], p[2], 0.016) for p in arc((0, cy + 0.012), 0.104, 0.112, cz + 0.035, -180, 180, 25)], "head", accent, 8, 0.012)
        sphere(0.03, (0, cy + 0.012, cz + 0.16), "head", accent, (1, 1, 0.9), 12, 8)
        tube([(p[0], p[1], p[2], 0.015) for p in arc((0, cy + 0.004), 0.1, 0.106, cz + 0.012, -160, -20)], "head", visor, 8, 0.012)
        tube([(p[0], p[1], p[2], 0.004) for p in arc((0, cy + 0.004), 0.103, 0.11, cz + 0.03, -165, -15)], "head", frame, 6, 0.012)
        # narrow skating skis: a thin ski, its edge, a stripe, a gently turned-up tip, a small binding
        ski = mat("ski", (0.08, 0.1, 0.14), 0.25, coat=0.8)
        ski_edge = mat("ski_edge", (0.75, 0.77, 0.8), 0.3, 0.8)
        stripe_m = mat("ski_stripe", (0.95, 0.45, 0.08), 0.3, coat=0.8)
        binding = mat("binding", (0.2, 0.2, 0.22), 0.3, 0.6)
        for X in "LR":
            x = sk.head("foot." + X).x
            b = "ski." + X
            box((0.046, 1.62, 0.014), (x, -0.08, -0.01), b, ski, bevel=0.004)
            box((0.047, 1.62, 0.004), (x, -0.08, -0.018), b, ski_edge, bevel=0.0015)
            box((0.014, 1.5, 0.003), (x, -0.1, -0.002), b, stripe_m, bevel=0.001)
            py, pz = -0.89, -0.01
            for i, th in enumerate((0.12, 0.3, 0.5, 0.7)):
                dy, dz = -math.cos(th) * 0.06, math.sin(th) * 0.06
                box((0.046 - i * 0.004, 0.066, 0.014), (x, py + dy * 0.5, pz + dz * 0.5), b, ski, rot=(-th, 0, 0), bevel=0.003)
                py, pz = py + dy, pz + dz
            box((0.05, 0.16, 0.02), (x, -0.08, 0.006), b, binding, bevel=0.006)
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


def biathlete_actions(sk):
    z0 = SKI_Z
    ank = 0.09 + z0
    # skating on skis with a double push of both poles on every stride (the V2): the skis angle out in a V, each
    # pushes out and back and lifts to come round; the arms swing up together, plant and push through behind
    crouch = {"hips": (26, 0, 0), "spine": (10, 0, 0), "chest": (6, 0, 0), "neck": (-18, 0, 0), "head": (-16, 0, 0),
              "ikw.L": 1.0, "ikw.R": 1.0, "hand.L": (0, 0, 0), "hand.R": (0, 0, 0)}
    path = [(0.0, (0.3, 0.08, 0.0, 14, 16)), (0.18, (0.38, -0.05, 0.0, 10, 16)), (0.34, (0.46, -0.2, 0.05, 0, 14)),
            (0.44, (0.3, -0.12, 0.09, -2, 10)), (0.56, (0.14, 0.12, 0.03, -4, 6)), (0.7, (0.14, 0.2, 0.0, -2, 8)),
            (0.86, (0.22, 0.16, 0.0, 6, 12)), (1.0, (0.3, 0.08, 0.0, 14, 16))]

    def foot_at(ph):
        ph %= 1.0
        for (a, pa), (b, pb) in zip(path, path[1:]):
            if a <= ph <= b:
                u = smoothstep(0, 1, (ph - a) / (b - a))
                return tuple(pa[i] + (pb[i] - pa[i]) * u for i in range(5))
    # the poles, twice a leg cycle: [phase, (arm flex, arm out, forearm bend, trunk crunch)]
    pole = [(0.0, (62, 12, 58, 0)), (0.16, (40, 10, 44, 10)), (0.32, (-4, 8, 22, 18)), (0.46, (-42, 12, 8, 8)),
            (0.66, (-18, 12, 30, 0)), (0.84, (38, 12, 60, -2)), (1.0, (62, 12, 58, 0))]

    def pole_at(ph):
        ph %= 1.0
        for (a, pa), (b, pb) in zip(pole, pole[1:]):
            if a <= ph <= b:
                u = smoothstep(0, 1, (ph - a) / (b - a))
                return tuple(pa[i] + (pb[i] - pa[i]) * u for i in range(4))
    skate = {}
    for i in range(0, 31, 2):
        t = i / 30.0
        k = dict(crouch)
        for X, sgn, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            x, y, z, roll, yaw = foot_at(t + off)
            k["ik_foot." + X] = (x * sgn, y, ank + z, 0, yaw)
            k["foot." + X] = (0, roll, 0)
        sw = math.sin(2 * math.pi * (t - 0.3))      # +1 with the weight over the left ski
        a, w, fa, crunch = pole_at(2.0 * t)
        k["root"] = (0.1 * sw, 0.0, -0.16 - 0.035 * crunch / 18.0 + 0.012 * math.cos(4 * math.pi * t))
        k["hips"] = (26 + crunch * 0.9, 3 * sw, -4 * sw)
        k["spine"] = (10 + crunch * 0.5, -2 * sw, 3 * sw)
        k["chest"] = (6 + crunch * 0.3, -3 * sw, 2 * sw)
        k["head"] = (-16 - crunch * 0.9, 4 * sw, -3 * sw)
        for X in "LR":
            k["arm." + X] = (a, -6, w)
            k["forearm." + X] = (fa, 0, 0)
            k["clavicle." + X] = (4 + a * 0.08, 0, 2)
        skate[i + 1] = k
    tuck = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        s = math.sin(2 * math.pi * t)
        tuck[i + 1] = {"ik_foot.L": (0.13, 0.02, ank, 0, 0), "ik_foot.R": (-0.13, -0.02, ank, 0, 0), "ikw.L": 1.0, "ikw.R": 1.0,
                       "root": (0, -0.04, -0.46 - 0.006 * s), "hips": (68, 0, 0), "spine": (14 + s, 0, 0), "chest": (8, 0, 0),
                       "neck": (-34, 0, 0), "head": (-30, 0, 0), "arm.L": (52, -20, 12), "arm.R": (52, -20, 12),
                       "forearm.L": (92, 0, 0), "forearm.R": (92, 0, 0), "clavicle.L": (8, 0, 0), "clavicle.R": (8, 0, 0)}
    ready = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        br = math.sin(2 * math.pi * t)
        ready[i + 1] = {"ik_foot.L": (0.13, 0.05, ank, 0, 4), "ik_foot.R": (-0.13, -0.05, ank, 0, 4), "ikw.L": 1.0, "ikw.R": 1.0,
                        "root": (0, 0.0, -0.12 - 0.006 * br), "hips": (22, 0, 0), "spine": (8, 0, 0), "chest": (4 + 1.5 * br, 0, 0),
                        "neck": (-14, 0, 0), "head": (-12, 0, 0), "arm.L": (48, -6, 12), "arm.R": (48, -6, 12),
                        "forearm.L": (56, 0, 0), "forearm.R": (56, 0, 0), "clavicle.L": (6, 0, 2), "clavicle.R": (6, 0, 2)}
    # prone at the range: lying along the mat on the elbows, the left hand forward under the rifle, the right at the
    # grip, cheek down on the stock; the legs apart, the skis flat behind
    prone = {}
    for i in range(0, 41, 10):
        t = i / 40.0
        br = math.sin(2 * math.pi * t)
        prone[i + 1] = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (84, 0, 0), "root": (0, 0.0, 0.2 + 0.004 * br),
                        "hips": (-4, 0, 0), "spine": (-12 - 0.8 * br, 0, 0), "chest": (-14 - 0.8 * br, 0, 0),
                        "neck": (-26, 0, 0), "head": (-22, -4, 0), "thigh.L": (-2, 0, 9), "thigh.R": (-2, 0, 9),
                        "shin.L": (4, 0, 0), "shin.R": (4, 0, 0), "foot.L": (-96, 0, 6), "foot.R": (-96, 0, 6),
                        "clavicle.L": (14, 0, 10), "clavicle.R": (10, 0, 6), "arm.L": (150, -10, 4), "forearm.L": (38, 0, 0),
                        "arm.R": (128, 10, -6), "forearm.R": (96, 0, 0), "hand.L": (0, 0, 0), "hand.R": (-10, 0, 0)}
    return {"idle": idle(z0), "wave": wave(z0), "celebrate": celebrate(z0), "skate": Anim(skate, loop=True),
            "tuck": Anim(tuck, loop=True), "ready": Anim(ready, loop=True), "prone": Anim(prone, loop=True)}


def bobber_actions(sk):
    z0 = 0.0
    ank = 0.09
    # where the hands grip, by where the runner pushes from (character space: left, forward, up): at the rear bar
    # straight ahead; on a side handle (the sled to the runner's right when they run on its left) one hand behind
    # the other on the grip that points back along the sled
    grips = {"": ((0.19, 0.8, 0.5), (-0.19, 0.8, 0.5)),
             "_l": ((-0.19, 0.38, 0.48), (-0.27, 0.56, 0.48)),
             "_r": ((0.27, 0.56, 0.48), (0.19, 0.38, 0.48))}
    acts = {}
    for suffix, (hl, hr) in grips.items():
        lean = 3 if suffix else 0
        twist = {"": 0, "_l": -8, "_r": 8}[suffix]
        # the set position at the sled: crouched, one foot forward, both hands on the grip, looking down the track
        ready = {}
        for i in range(0, 21, 5):
            t = i / 20.0
            br = math.sin(2 * math.pi * t)
            ready[i + 1] = {"ik_foot.L": (0.14, 0.28, ank, 0, 6), "ik_foot.R": (-0.14, -0.3, ank, -20, 6), "ikw.L": 1.0, "ikw.R": 1.0,
                            "root": (0.0, 0.1, -0.3 - 0.01 * br), "hips": (48, twist * 0.5, 0), "spine": (20, twist, lean),
                            "chest": (12 + 1.5 * br, twist * 0.5, 0), "neck": (-34, -twist, 0), "head": (-30, -twist, 0),
                            "ik_hand.L": hl, "ik_hand.R": hr, "ikh.L": 1.0, "ikh.R": 1.0, "hand.L": (0, 0, 0), "hand.R": (0, 0, 0)}
        # the push: sprinting bent low beside or behind the sled, the hands staying on the grip as the body drives
        base = {"hips": (46, twist * 0.5, 0), "spine": (20, twist, lean), "chest": (12, twist * 0.5, 0), "neck": (-36, -twist, 0),
                "head": (-30, -twist, 0), "ik_hand.L": hl, "ik_hand.R": hr, "ikh.L": 1.0, "ikh.R": 1.0, "root": (0, 0.16, 0)}
        push = gait(sk, 16, 2.6, 0.36, lift=0.18, lift_at=0.4, strike=6.0, push=40.0, bob=-0.05, drop=-0.2, toe_out=2.0,
                    pelvis_yaw=5.0, pelvis_roll=3.0, sway=0.006, shoulder_yaw=3.0, lean=6.0, arm_swing=0.0, arm_out=0.0,
                    elbow=0.0, elbow_swing=0.0, base=base, step=2)
        acts["ready" + suffix] = Anim(ready, loop=True)
        acts["push" + suffix] = push
    # seated in the sled: on its floor, knees up, feet forward; the pilot upright with the hands on the steering
    # rings at the sides, the crew behind tucked down with their heads between their shoulders
    seat = {"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0, 0.2 - 0.93), "hips": (0, 0, 0), "thigh.L": (104, 0, 8),
            "thigh.R": (104, 0, 8), "shin.L": (122, 0, 0), "shin.R": (122, 0, 0), "foot.L": (10, 0, 0), "foot.R": (10, 0, 0)}

    def seated(n, fn):
        keys = {}
        for i in range(0, n + 1, max(1, n // 4)):
            keys[i + 1] = P(seat, **fn(i / n))
        return Anim(keys, loop=True)
    br = lambda t: math.sin(2 * math.pi * t)
    acts["sit"] = seated(20, lambda t: {"spine": (14 + br(t), 0, 0), "chest": (10, 0, 0), "neck": (-18, 0, 0), "head": (-14, 0, 0),
                                        "arm.L": (40, 0, 14), "arm.R": (40, 0, 14), "forearm.L": (58, 0, 0), "forearm.R": (58, 0, 0),
                                        "hand.L": (0, 0, 0), "hand.R": (0, 0, 0)})
    acts["tuck"] = seated(20, lambda t: {"spine": (40 + br(t), 0, 0), "chest": (30, 0, 0), "neck": (18, 0, 0), "head": (16, 0, 0),
                                         "arm.L": (44, 0, 30), "arm.R": (44, 0, 30), "forearm.L": (96, 0, 0), "forearm.R": (96, 0, 0),
                                         "clavicle.L": (10, 0, -4), "clavicle.R": (10, 0, -4)})
    # the brakeman past the line: sitting up, leaning back, both hands hauling the lever at his side
    acts["brake"] = seated(20, lambda t: {"spine": (-12 + 2 * br(t), 0, 0), "chest": (-6, 0, 0), "neck": (-4, 0, 0), "head": (-8, 0, 0),
                                          "arm.L": (-20, 0, 18), "arm.R": (-20, 0, 18), "forearm.L": (70 + 6 * br(t), 0, 0),
                                          "forearm.R": (70 + 6 * br(t), 0, 0), "clavicle.L": (-6, 0, 0), "clavicle.R": (-6, 0, 0)})
    # the joy at the bottom, each their own way: both arms up, a fist pumped, a hug for the one in front, a wave
    acts["cheer"] = seated(16, lambda t: {"spine": (-4, 0, 3 * br(t)), "chest": (-6, 0, 0), "head": (-16, 10 * br(t), 0),
                                          "arm.L": (160, -20, 30 + 8 * br(t)), "arm.R": (160, -20, 30 - 8 * br(t)), "forearm.L": (20, 0, 0),
                                          "forearm.R": (20, 0, 0), "clavicle.L": (0, 0, 14), "clavicle.R": (0, 0, 14)})
    acts["pump"] = seated(12, lambda t: {"spine": (4 + 6 * max(0.0, br(t)), 8, 0), "chest": (2, 6, 0), "head": (-10 - 8 * max(0.0, br(t)), -6, 0),
                                         "arm.R": (120 + 40 * max(0.0, br(t)), -10, 20), "forearm.R": (70 - 50 * max(0.0, br(t)), 0, 0),
                                         "arm.L": (30, 0, 14), "forearm.L": (60, 0, 0), "clavicle.R": (0, 0, 10 + 8 * max(0.0, br(t)))})
    acts["hug"] = seated(20, lambda t: {"spine": (32 + 4 * br(t), 4 * br(t * 2), 0), "chest": (20, 0, 3 * br(t)), "neck": (4, 0, 0),
                                        "head": (-6, 10, 0), "arm.L": (80, 20, 40), "arm.R": (80, 20, 40), "forearm.L": (80, 0, 0),
                                        "forearm.R": (80, 0, 0), "clavicle.L": (14, 0, 0), "clavicle.R": (14, 0, 0)})
    acts["wave_seat"] = seated(16, lambda t: {"spine": (2, 24, -4), "chest": (0, 16, 0), "head": (-14, 20, 0),
                                              "arm.L": (150, -30, 40), "forearm.L": (30, 0, 26 * br(t)), "hand.L": (0, 0, 14 * br(t)),
                                              "arm.R": (30, 0, 14), "forearm.R": (60, 0, 0)})
    acts.update({"idle": idle(z0), "wave": wave(z0), "celebrate": celebrate(z0)})
    return acts


def build(kind):
    clear()
    sk = Skeleton(proportions(), skis=(kind not in ("skater", "bobber")))
    body(kind, sk)
    acts = {"skater": skater_actions, "jumper": jumper_actions, "biathlete": biathlete_actions, "bobber": bobber_actions}[kind](sk)
    rig_export(kind, out_dir, acts, skeleton=sk, fps=FPS)


def export_static(name):
    """Joins the scene's meshes and exports them as a plain model (no rig)."""
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    o = active()
    o.name = name
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True)
    print("exported", name, "tris", sum(len(p.vertices) - 2 for p in o.data.polygons))


def rifle():
    """The small-bore biathlon rifle, about 1.1 m: the butt plate at the origin, the muzzle along -Y (so +Z in the
    game), the sights on top. A dark composite stock with a big cheek piece, spare magazines in the fore-end, a
    diopter sight at the back and a hooded front sight, the sling and the hand stop under the fore-end."""
    clear()
    stock = mat("rifle_stock", (0.1, 0.11, 0.13), 0.45, coat=0.4)
    wood = mat("rifle_wood", (0.42, 0.24, 0.12), 0.5, coat=0.5)
    steel = mat("rifle_steel", (0.2, 0.21, 0.23), 0.3, 0.9)
    bright = mat("rifle_bright", (0.75, 0.77, 0.8), 0.25, 1.0)
    mag = mat("rifle_mag", (0.85, 0.12, 0.1), 0.4)
    box((0.04, 0.03, 0.14), (0, -0.015, -0.01), "", stock, bevel=0.01)               # the butt plate
    box((0.036, 0.36, 0.1), (0, -0.19, 0.0), "", wood, bevel=0.012)                  # the butt
    box((0.034, 0.2, 0.05), (0, -0.2, 0.07), "", wood, bevel=0.012)                  # the cheek piece
    box((0.034, 0.12, 0.09), (0, -0.39, -0.04), "", wood, rot=(0.5, 0, 0), bevel=0.012)   # the pistol grip
    box((0.04, 0.38, 0.06), (0, -0.56, 0.02), "", stock, bevel=0.01)                 # the fore-end
    for i in range(4):                                                               # spare magazines
        box((0.012, 0.022, 0.05), (0.024 - (i % 2) * 0.048, -0.48 - (i // 2) * 0.05, 0.0), "", mag, bevel=0.003)
    box((0.03, 0.2, 0.035), (0, -0.44, 0.07), "", steel, bevel=0.005)                # the action
    box((0.018, 0.03, 0.05), (0, -0.37, 0.11), "", steel, bevel=0.004)               # the diopter
    sphere(0.012, (0, -0.35, 0.125), "", steel, (1, 0.6, 1), 12, 8)
    tube([(0, -0.54, 0.075, 0.009), (0, -1.06, 0.075, 0.008)], "", steel, 12, 0.02)  # the barrel
    tube([(0, -1.02, 0.1, 0.012), (0, -1.08, 0.1, 0.012)], "", steel, 12, 0.01)      # the front sight's hood
    box((0.008, 0.02, 0.025), (0, -1.05, 0.085), "", steel, bevel=0.002)
    box((0.004, 0.04, 0.006), (0, -0.42, 0.095), "", bright, bevel=0.001)            # the bolt handle
    box((0.02, 0.03, 0.04), (0, -0.64, -0.03), "", steel, bevel=0.004)               # the hand stop
    tube([(0, -0.64, -0.05, 0.004), (0, -0.4, -0.12, 0.004), (0, -0.12, -0.08, 0.004)], "", steel, 6, 0.02)
    export_static("rifle")


def ski_pole():
    """A skating pole, 1.6 m: the grip at the origin, the shaft down -Z, a strap, a small basket and a steel tip."""
    clear()
    shaft = mat("pole_shaft", (0.12, 0.13, 0.16), 0.3, 0.2, coat=0.8)
    grip = mat("pole_grip", (0.1, 0.1, 0.1), 0.6)
    accent = mat("pole_accent", (0.95, 0.45, 0.08), 0.4)
    steel = mat("pole_tip", (0.7, 0.72, 0.75), 0.3, 1.0)
    tube([(0, 0, 0.06, 0.016), (0, 0, -0.05, 0.015), (0, 0, -0.1, 0.012)], "", grip, 12, 0.01)
    tube([(0, 0, -0.1, 0.009), (0, 0, -1.55, 0.006)], "", shaft, 10, 0.05)
    tube([(0, 0, -0.12, 0.0095), (0, 0, -0.22, 0.0095)], "", accent, 10, 0.02)
    tube([(0.015, 0, 0.04, 0.004), (0.04, -0.02, -0.03, 0.004), (0.02, -0.01, -0.08, 0.004)], "", grip, 6, 0.01)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.035, radius2=0.012, depth=0.025, location=(0, 0, -1.48))
    tag(active(), "", accent)
    tube([(0, 0, -1.55, 0.006), (0, 0, -1.6, 0.002)], "", steel, 8, 0.01)
    export_static("ski_pole")


only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
for k in ("skater", "jumper", "biathlete", "bobber"):
    if not only or k in only:
        build(k)
if not only or "rifle" in only:
    rifle()
if not only or "ski_pole" in only:
    ski_pole()
