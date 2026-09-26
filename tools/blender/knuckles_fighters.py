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


def ring(z, rx, ry, bone, material, h=0.03, y=0.0):
    """A band around the body (belts, hems, collars): a short loft, a touch bigger than what it wraps."""
    return body_loft([(z - h / 2, rx, ry, y), (z + h / 2, rx, ry, y)], bone, material, 20, 0)


def torus(R, r, loc, bone, material, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=24, minor_segments=6, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return tag(o, bone, material)


def fighter(name, jacket, shirt, pants, skin_c, hair_c=None, build=1.0, extras=None, leather=False, sole=(0.9, 0.9, 0.88)):
    clear()
    skin = mat(name + "_skin", skin_c, 0.5)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat(name + "_iris", (0.2, 0.15, 0.1), 0.2)
    top = mat(name + "_top", shirt, 0.75)
    legs = mat(name + "_pants", pants, 0.85)
    shoes = mat(name + "_shoes", (0.1, 0.1, 0.12) if name != "hero_a" else (0.9, 0.9, 0.92), 0.45)
    hair = mat(name + "_hair", hair_c, 0.6, coat=0.3) if hair_c else None
    belt = mat("belt", (0.06, 0.04, 0.03), 0.35, coat=0.4)
    metal = mat("buckle", (0.85, 0.7, 0.35), 0.2, 1.0)
    rubber = mat(name + "_sole", sole, 0.6)
    athletic_body(top, skin, white, iris, hair=hair, glove=skin, boot=shoes, legs=legs)
    # a belt with a buckle, soles under the shoes, a seam down each leg
    ring(1.0, 0.172, 0.112, "hips", belt, 0.045)
    box((0.06, 0.02, 0.04), (0, -0.114, 1.0), "hips", metal)
    for s_, side in ((1, "L"), (-1, "R")):
        box((0.112, 0.25, 0.035), (0.1 * s_, -0.045, 0.015), "shin." + side, rubber)
        box((0.1, 0.04, 0.05), (0.1 * s_, -0.155, 0.04), "shin." + side, rubber)  # toe cap
        box((0.006, 0.01, 0.4), (0.1 * s_ + 0.078 * s_, -0.005, 0.72), "thigh." + side, mat(name + "_seam", tuple(c * 0.7 for c in pants), 0.9))
    if jacket:
        jk = mat(name + "_jacket", jacket, 0.3 if leather else 0.42, coat=0.8 if leather else 0.45)
        dark = mat(name + "_jacket_trim", tuple(c * 0.45 for c in jacket), 0.5, coat=0.3)
        # an open jacket over the shirt: two front panels, the back and sleeves
        for s_ in (-1, 1):
            body_loft([(1.05, 0.08, 0.1, 0.0), (1.3, 0.1, 0.115, 0.0), (1.44, 0.1, 0.1, 0.0)], "spine", jk, 12, 1)
            bpy.context.active_object.location.x = 0.1 * s_
        for s_, side in ((1, "L"), (-1, "R")):
            muscle_limb([(0.195 * s_, 0, 1.46, 0.064), (0.225 * s_, 0, 1.3, 0.06), (0.252 * s_, 0, 1.1, 0.05)], "arm." + side, jk)
            muscle_limb([(0.249 * s_, 0, 1.17, 0.05), (0.26 * s_, -0.01, 1.03, 0.051), (0.268 * s_, -0.02, 0.92, 0.042)], "forearm." + side, jk)
            muscle_limb([(0.267 * s_, -0.019, 0.945, 0.047), (0.27 * s_, -0.022, 0.905, 0.046)], "forearm." + side, dark, 14, 0)  # cuff
            muscle_limb([(0.19 * s_, -0.005, 1.47, 0.068), (0.21 * s_, 0, 1.41, 0.07)], "spine", dark, 14, 0)  # shoulder seam
        ring(1.06, 0.19, 0.125, "spine", dark, 0.05)  # the hem
        # a collar standing up round the neck, and the zip's edges down the front
        body_loft([(1.43, 0.12, 0.1, 0.012), (1.49, 0.1, 0.09, 0.015), (1.54, 0.095, 0.088, 0.02)], "spine", dark, 16, 1)
        for s_ in (-1, 1):
            box((0.012, 0.01, 0.36), (0.07 * s_, -0.118, 1.25), "spine", dark)
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


def pompadour():
    brown = mat("hero_a_hair", (0.35, 0.22, 0.1), 0.6, coat=0.3)
    sphere(0.07, (0, -0.06, 1.78), "head", brown, (1.2, 0.9, 0.75))
    sphere(0.06, (0, 0.02, 1.8), "head", brown, (1.3, 1.2, 0.6))


def headband():
    red = mat("headband", (0.85, 0.1, 0.1), 0.6)
    torus(0.1, 0.014, (0, 0.008, 1.72), "head", red, scale=(0.95, 1.03, 1.0))
    for k in (-1, 1):  # the knot's tails at the back
        box((0.02, 0.012, 0.13), (0.02 * k, 0.11, 1.66), "head", red, (0.25 * k, 0, 0))
    black = mat("hero_b_hair", (0.1, 0.08, 0.06), 0.6, coat=0.3)
    for k in range(5):  # spikes over the band
        a = (k - 2) * 0.35
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.035, radius2=0.0, depth=0.1,
                                        location=(0.06 * math.sin(a), 0.01, 1.8), rotation=(0.3, a * 0.8, 0))
        tag(bpy.context.active_object, "head", black)


def boss_extras():
    shades()
    gold = mat("buckle", (0.85, 0.7, 0.35), 0.2, 1.0)
    torus(0.085, 0.008, (0, -0.02, 1.43), "spine", gold, rot=(0.35, 0, 0), scale=(1.0, 1.1, 1.0))  # a chain


def thug_extras():
    cap()
    vest = mat("thug_vest", (0.08, 0.08, 0.09), 0.4, coat=0.5)
    for s_ in (-1, 1):
        box((0.02, 0.012, 0.3), (0.075 * s_, -0.118, 1.26), "spine", vest)  # the vest's zip edges


def bruiser_extras():
    strap = mat("bruiser_strap", (0.06, 0.05, 0.04), 0.4)
    for s_ in (-1, 1):  # braces over the tank top
        box((0.035, 0.01, 0.42), (0.085 * s_, -0.108, 1.25), "spine", strap)
        box((0.035, 0.01, 0.42), (0.085 * s_, 0.1, 1.25), "spine", strap)
    torus(0.05, 0.01, (0.265, -0.02, 0.93), "forearm.L", strap)  # wrist wraps
    torus(0.05, 0.01, (-0.265, -0.02, 0.93), "forearm.R", strap)


def hood():
    green = mat("hood", (0.25, 0.35, 0.2), 0.8)
    sphere(0.118, (0, 0.02, 1.68), "head", green, (1.02, 1.1, 1.08))




fighter("hero_a", (0.12, 0.3, 0.8), (0.95, 0.95, 0.95), (0.16, 0.22, 0.42), (0.9, 0.7, 0.55), (0.35, 0.22, 0.1), extras=pompadour)
fighter("hero_b", (0.78, 0.12, 0.12), (0.95, 0.95, 0.95), (0.18, 0.18, 0.24), (0.85, 0.65, 0.5), (0.1, 0.08, 0.06), extras=headband)
fighter("thug", (0.3, 0.3, 0.32), (0.85, 0.8, 0.7), (0.3, 0.28, 0.25), (0.88, 0.68, 0.52), None, 1.0, thug_extras, sole=(0.3, 0.25, 0.2))
fighter("knifer", None, (0.25, 0.35, 0.2), (0.2, 0.2, 0.22), (0.7, 0.5, 0.38), None, 0.95, hood, sole=(0.85, 0.85, 0.8))
fighter("bruiser", None, (0.9, 0.9, 0.85), (0.25, 0.3, 0.4), (0.8, 0.6, 0.45), None, 1.25, bruiser_extras, sole=(0.15, 0.12, 0.1))
fighter("boss", (0.12, 0.1, 0.1), (0.5, 0.1, 0.1), (0.1, 0.1, 0.12), (0.85, 0.66, 0.5), (0.05, 0.05, 0.05), 1.12, boss_extras, leather=True,
        sole=(0.1, 0.1, 0.1))
