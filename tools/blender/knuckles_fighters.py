"""Neon Knuckles fighters on the shared humanoid rig: the two brothers (blue and red jackets), the thug (vest and
cap), the knifer (hoodie), the bruiser (big, bald, tank top) and the boss (leather jacket, sunglasses), with the
fighting animations. Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/knuckles_fighters.py -- godot/games/knuckles/art/models
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *  # mat, sphere, box, muscle_limb, body_loft, athletic_body, clear, rig_export

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)

GUARD = {"arm.L": (-60, 0, 25), "forearm.L": (-80, 0, 0), "arm.R": (-45, 0, -25), "forearm.R": (-90, 0, 0),
         "spine": (8, 0, 10), "thigh.L": (-12, 0, 0), "thigh.R": (10, 0, 0), "shin.L": (15, 0, 0), "shin.R": (10, 0, 0)}


def pose(**over):
    k = dict(GUARD)
    k.update(over)
    return k


def actions():
    a = {}
    a["idle"] = {1: GUARD, 20: pose(**{"@root": (0, 0, -0.02), "spine": (10, 0, 12)}), 40: GUARD}
    walk = {}
    for f, ph in ((1, 1), (8, 0), (15, -1), (22, 0), (29, 1)):
        walk[f] = pose(**{"thigh.L": (-12 + 28 * ph, 0, 0), "thigh.R": (10 - 28 * ph, 0, 0), "shin.L": (15 + 20 * max(0, -ph), 0, 0),
                          "shin.R": (10 + 20 * max(0, ph), 0, 0), "@root": (0, 0, 0.03 if ph == 0 else 0.0)})
    a["walk"] = walk
    a["jab"] = {1: GUARD, 3: pose(**{"arm.L": (-92, 0, 5), "forearm.L": (-5, 0, 0), "spine": (4, 0, 25)}), 8: GUARD}
    a["punch"] = {1: GUARD, 4: pose(**{"arm.R": (-92, 0, -5), "forearm.R": (-5, 0, 0), "spine": (4, 0, -25), "thigh.R": (-10, 0, 0)}), 10: GUARD}
    a["hook"] = {1: GUARD, 4: pose(**{"arm.L": (-80, 0, 60), "forearm.L": (-60, 0, 0), "spine": (0, 0, 35)}),
                 8: pose(**{"arm.L": (-85, 0, -30), "forearm.L": (-50, 0, 0), "spine": (6, 0, -30), "@root": (0, 0, 0.04)}), 16: GUARD}
    a["kick"] = {1: GUARD, 5: pose(**{"thigh.R": (-95, 0, 0), "shin.R": (5, 0, 0), "spine": (-15, 0, 0)}), 12: GUARD}
    a["jump"] = {1: pose(**{"thigh.L": (-60, 0, 0), "shin.L": (90, 0, 0), "thigh.R": (-40, 0, 0), "shin.R": (80, 0, 0)}),
                 10: pose(**{"thigh.L": (-60, 0, 0), "shin.L": (90, 0, 0), "thigh.R": (-40, 0, 0), "shin.R": (80, 0, 0)})}
    a["jump_kick"] = {1: pose(**{"thigh.L": (-70, 0, 0), "shin.L": (100, 0, 0)}),
                      4: pose(**{"thigh.R": (-90, 0, 0), "shin.R": (0, 0, 0), "thigh.L": (-60, 0, 0), "shin.L": (110, 0, 0), "spine": (-20, 0, 0)}),
                      14: pose(**{"thigh.R": (-90, 0, 0), "shin.R": (0, 0, 0), "thigh.L": (-60, 0, 0), "shin.L": (110, 0, 0), "spine": (-20, 0, 0)})}
    a["knee"] = {1: pose(**{"arm.L": (-80, 0, 20), "arm.R": (-80, 0, -20)}),
                 4: pose(**{"thigh.R": (-100, 0, 0), "shin.R": (110, 0, 0), "arm.L": (-60, 0, 20), "arm.R": (-60, 0, -20), "spine": (15, 0, 0)}),
                 9: pose(**{"arm.L": (-80, 0, 20), "arm.R": (-80, 0, -20)})}
    a["elbow"] = {1: GUARD, 5: pose(**{"arm.R": (40, 0, -20), "forearm.R": (-120, 0, 0), "spine": (0, 0, -40)}), 12: GUARD}
    a["bat"] = {1: pose(**{"arm.R": (-150, 0, -20), "forearm.R": (-40, 0, 0), "spine": (-5, 0, -20)}),
                7: pose(**{"arm.R": (-70, 0, 30), "forearm.R": (-10, 0, 0), "spine": (15, 0, 30)}), 16: GUARD}
    a["grab"] = {1: pose(**{"arm.L": (-80, 0, 20), "arm.R": (-80, 0, -20), "forearm.L": (-30, 0, 0), "forearm.R": (-30, 0, 0)}),
                 20: pose(**{"arm.L": (-82, 0, 20), "arm.R": (-82, 0, -20), "forearm.L": (-30, 0, 0), "forearm.R": (-30, 0, 0)})}
    a["held"] = {1: {"spine": (25, 0, 0), "head": (20, 0, 0), "arm.L": (0, 0, 30), "arm.R": (0, 0, -30)},
                 15: {"spine": (30, 0, 5), "head": (25, 0, 0), "arm.L": (0, 0, 35), "arm.R": (0, 0, -35)}}
    a["hit"] = {1: GUARD, 3: pose(**{"spine": (-25, 0, 0), "head": (-25, 0, 0), "arm.L": (-20, 0, 40), "arm.R": (-20, 0, -40)}), 12: GUARD}
    a["down"] = {1: pose(**{"spine": (-30, 0, 0)}),
                 8: {"hips": (-80, 0, 0), "@root": (0, 0, 0.1), "arm.L": (0, 0, 90), "arm.R": (0, 0, -90), "head": (-20, 0, 0)},
                 16: {"hips": (-90, 0, 0), "@root": (0, 0, -0.75), "arm.L": (0, 0, 110), "arm.R": (0, 0, -100), "thigh.L": (10, 0, 10)}}
    a["getup"] = {1: {"hips": (-90, 0, 0), "@root": (0, 0, -0.75), "arm.L": (0, 0, 110), "arm.R": (0, 0, -100)},
                  8: {"hips": (-40, 0, 0), "@root": (0, 0, -0.5), "thigh.L": (-80, 0, 0), "shin.L": (120, 0, 0)}, 16: GUARD}
    a["thrown"] = {1: {"hips": (-40, 0, 20), "arm.L": (0, 0, 120), "arm.R": (0, 0, -120)},
                   10: {"hips": (-140, 0, 40), "arm.L": (0, 0, 150), "arm.R": (0, 0, -150), "thigh.L": (-40, 0, 0)}}
    a["ko"] = {1: pose(**{"spine": (-30, 0, 0)}), 10: {"hips": (-90, 0, 0), "@root": (0, 0, -0.75), "arm.L": (0, 0, 120), "arm.R": (0, 0, -120),
                                                         "head": (-10, 0, 30)}}
    a["victory"] = {1: pose(**{"arm.R": (0, 0, -165), "forearm.R": (0, 0, 0)}),
                    10: pose(**{"arm.R": (0, 0, -175), "forearm.R": (0, 0, 10), "@root": (0, 0, 0.15)}),
                    20: pose(**{"arm.R": (0, 0, -165), "forearm.R": (0, 0, 0)})}
    return a


def fighter(name, jacket, shirt, pants, skin_c, hair_c=None, build=1.0, extras=None):
    clear()
    skin = mat(name + "_skin", skin_c, 0.55)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat(name + "_iris", (0.2, 0.15, 0.1), 0.2)
    top = mat(name + "_top", shirt, 0.7)
    legs = mat(name + "_pants", pants, 0.8)
    shoes = mat(name + "_shoes", (0.1, 0.1, 0.12) if name != "hero_a" else (0.9, 0.9, 0.92), 0.5)
    hair = mat(name + "_hair", hair_c, 0.8) if hair_c else None
    athletic_body(top, skin, white, iris, hair=hair, glove=skin, boot=shoes, legs=legs)
    if jacket:
        jk = mat(name + "_jacket", jacket, 0.5, coat=0.2)
        # an open jacket over the shirt: two front panels, the back and sleeves
        for s_ in (-1, 1):
            body_loft([(1.05, 0.08, 0.1, 0.0), (1.3, 0.1, 0.115, 0.0), (1.44, 0.1, 0.1, 0.0)], "spine", jk, 12, 1)
            bpy.context.active_object.location.x = 0.1 * s_
        for s_, side in ((1, "L"), (-1, "R")):
            muscle_limb([(0.195 * s_, 0, 1.46, 0.064), (0.225 * s_, 0, 1.3, 0.06), (0.252 * s_, 0, 1.1, 0.05)], "arm." + side, jk)
            muscle_limb([(0.249 * s_, 0, 1.17, 0.05), (0.26 * s_, -0.01, 1.03, 0.051), (0.268 * s_, -0.02, 0.92, 0.042)], "forearm." + side, jk)
    if extras:
        extras()
    rig_export(name, out_dir, actions(), build)


def cap():
    red = mat("cap", (0.75, 0.15, 0.12), 0.6)
    sphere(0.108, (0, 0.005, 1.7), "head", red, (1.0, 1.05, 0.7))
    box((0.16, 0.11, 0.015), (0, -0.12, 1.69), "head", red)


def shades():
    dark = mat("shades", (0.02, 0.02, 0.03), 0.05, 0.6, coat=1.0)
    box((0.15, 0.02, 0.035), (0, -0.098, 1.685), "head", dark)


def hood():
    green = mat("hood", (0.25, 0.35, 0.2), 0.8)
    sphere(0.118, (0, 0.02, 1.68), "head", green, (1.02, 1.1, 1.08))


fighter("hero_a", (0.15, 0.35, 0.8), (0.95, 0.95, 0.95), (0.2, 0.25, 0.45), (0.9, 0.7, 0.55), (0.35, 0.22, 0.1))
fighter("hero_b", (0.8, 0.15, 0.15), (0.95, 0.95, 0.95), (0.2, 0.2, 0.25), (0.85, 0.65, 0.5), (0.1, 0.08, 0.06))
fighter("thug", (0.3, 0.3, 0.32), (0.85, 0.8, 0.7), (0.3, 0.28, 0.25), (0.88, 0.68, 0.52), None, 1.0, cap)
fighter("knifer", None, (0.25, 0.35, 0.2), (0.2, 0.2, 0.22), (0.7, 0.5, 0.38), None, 0.95, hood)
fighter("bruiser", None, (0.9, 0.9, 0.85), (0.25, 0.3, 0.4), (0.8, 0.6, 0.45), None, 1.25)
fighter("boss", (0.12, 0.1, 0.1), (0.5, 0.1, 0.1), (0.1, 0.1, 0.12), (0.85, 0.66, 0.5), (0.05, 0.05, 0.05), 1.12, shades)
