"""Frostpeak Games athletes: one humanoid rig with two outfits, the speed skater (skin suit, hood, blades) and the
ski jumper (suit, helmet, goggles, long skis on their own bones so they can open into a V). The material named
"suit" is recoloured per nation in the game. Rigid parts on bones, keyed animations, one glTF animation per action.
Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/frostpeak_athletes.py -- godot/games/frostpeak/art/models
About 1.8 m tall, feet at z = 0, facing -Y.
"""
import bpy, math, os, sys
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *  # mat, sphere, box, limb, BONES, clear, keys, rig_export

def body(kind):
    suit = mat("suit", (0.85, 0.15, 0.15), 0.35, coat=0.3)
    trim = mat("suit_trim", (0.95, 0.95, 0.95), 0.4)
    skin = mat("skin", (0.92, 0.7, 0.55), 0.6)
    boot = mat("athlete_boot", (0.1, 0.1, 0.12), 0.4, coat=0.4)
    visor = mat("goggles", (0.2, 0.6, 0.9), 0.05, 0.6, coat=1.0)
    sphere(0.16, (0, 0, 1.32), "spine", suit, (1.25, 0.72, 1.05))   # chest and shoulders
    sphere(0.13, (0, 0, 1.15), "spine", suit, (1.05, 0.72, 1.0))    # waist
    sphere(0.14, (0, 0, 0.99), "hips", suit, (1.12, 0.76, 0.75))    # pelvis
    limb(0.05, (0, 0, 1.45), (0, 0, 1.55), "head", skin)            # neck
    box((0.22, 0.012, 0.2), (0, -0.118, 1.28), "spine", trim)        # the race bib
    box((0.12, 0.014, 0.05), (0, -0.124, 1.3), "spine", mat("bib_number", (0.1, 0.1, 0.12), 0.5))
    sphere(0.11, (0, -0.01, 1.62), "head", skin, (0.95, 1.0, 1.1))
    if kind == "skater":
        sphere(0.118, (0, 0.01, 1.64), "head", suit, (0.98, 1.02, 1.08))  # the tight hood
        box((0.14, 0.03, 0.04), (0, -0.1, 1.64), "head", visor)
    else:
        sphere(0.13, (0, 0.0, 1.66), "head", mat("helmet", (0.95, 0.95, 0.95), 0.3, coat=0.8), (1.0, 1.05, 1.0))
        box((0.18, 0.04, 0.06), (0, -0.11, 1.63), "head", visor)
    for s, side in ((1, "L"), (-1, "R")):
        limb(0.055, (0.2 * s, 0, 1.42), (0.24 * s, 0, 1.12), "arm." + side, suit)
        limb(0.045, (0.24 * s, 0, 1.12), (0.26 * s, -0.02, 0.88), "forearm." + side, suit, 0.04)
        sphere(0.045, (0.265 * s, -0.025, 0.84), "forearm." + side, mat("gloves", (0.12, 0.12, 0.14), 0.6))
        limb(0.08, (0.1 * s, 0, 0.95), (0.1 * s, 0, 0.52), "thigh." + side, suit, 0.065)
        limb(0.06, (0.1 * s, 0, 0.52), (0.1 * s, 0, 0.12), "shin." + side, suit, 0.05)
        box((0.1, 0.24, 0.1), (0.1 * s, -0.04, 0.07), "shin." + side, boot)
        if kind == "skater":
            blade = mat("blade", (0.85, 0.87, 0.9), 0.15, 1.0)
            box((0.012, 0.44, 0.05), (0.1 * s, -0.06, 0.0), "shin." + side, blade)
        else:
            ski = mat("ski", (0.95, 0.8, 0.1), 0.3, coat=0.6)
            box((0.1, 2.3, 0.025), (0.1 * s, -0.5, 0.01), "ski." + side, ski)
            box((0.1, 0.12, 0.025), (0.1 * s, -1.66, 0.05), "ski." + side, ski, rot=(0.5, 0, 0))  # the tip


def build(kind):
    clear()
    body(kind)
    acts = {}
    crouch = {"spine": (55, 0, 0), "head": (-40, 0, 0), "thigh.L": (-60, 0, 0), "thigh.R": (-60, 0, 0),
              "shin.L": (80, 0, 0), "shin.R": (80, 0, 0), "@root": (0, 0, -0.28)}
    acts["idle"] = ({1: {"head": (0, 0, 5)}, 30: {"head": (4, 0, -5), "spine": (3, 0, 0)}, 60: {"head": (0, 0, 5)}})
    acts["wave"] = ({1: {"arm.R": (0, 0, -150), "forearm.R": (0, 0, -20)}, 10: {"arm.R": (0, 0, -165), "forearm.R": (0, 0, 20)},
                           20: {"arm.R": (0, 0, -150), "forearm.R": (0, 0, -20)}})
    acts["celebrate"] = ({1: {"arm.L": (0, 0, 160), "arm.R": (0, 0, -160), "@root": (0, 0, 0.0)},
                                8: {"arm.L": (0, 0, 170), "arm.R": (0, 0, -170), "@root": (0, 0, 0.25), "thigh.L": (-30, 0, 0), "shin.L": (40, 0, 0)},
                                16: {"arm.L": (0, 0, 160), "arm.R": (0, 0, -160), "@root": (0, 0, 0.0)}})
    if kind == "skater":
        # the skating stride: crouched, one leg pushing out sideways, the other arm swinging
        stride = {}
        for f, s in ((1, 1), (11, -1), (21, 1)):
            k = dict(crouch)
            k["thigh.L" if s > 0 else "thigh.R"] = (-60, 0, 35 * s)
            k["shin.L" if s > 0 else "shin.R"] = (40, 0, 0)
            k["arm.R" if s > 0 else "arm.L"] = (-50, 0, -20 * s)
            k["arm.L" if s > 0 else "arm.R"] = (30, 0, 10 * s)
            k["hips"] = (0, 0, -8 * s)
            stride[f] = k
        acts["skate"] = (stride)
        glide = dict(crouch)
        glide["arm.L"] = (40, 0, 0)
        glide["arm.R"] = (40, 0, 0)
        acts["glide"] = ({1: glide, 20: glide})
        acts["ready"] = ({1: crouch, 20: crouch})
    else:
        tuck = {"spine": (75, 0, 0), "head": (-60, 0, 0), "thigh.L": (-70, 0, 0), "thigh.R": (-70, 0, 0),
                "shin.L": (100, 0, 0), "shin.R": (100, 0, 0), "arm.L": (60, 0, 5), "arm.R": (60, 0, -5), "@root": (0, 0, -0.35),
                "ski.L": (-30, 0, 0), "ski.R": (-30, 0, 0)}
        acts["tuck"] = ({1: tuck, 20: tuck})
        # the flight: body leaning far forward over V-shaped skis, arms back
        fly = {"hips": (70, 0, 0), "head": (-60, 0, 0), "arm.L": (20, 0, 12), "arm.R": (20, 0, -12),
               "ski.L": (-72, 0, 18), "ski.R": (-72, 0, -18), "thigh.L": (5, 0, 0), "thigh.R": (5, 0, 0)}
        fly2 = dict(fly)
        fly2["hips"] = (73, 0, 2)
        acts["flight"] = ({1: fly, 30: fly2, 60: fly})
        tele = {"spine": (20, 0, 0), "thigh.L": (-40, 0, 0), "shin.L": (60, 0, 0), "thigh.R": (20, 0, 0), "shin.R": (50, 0, 0),
                "arm.L": (0, 0, 70), "arm.R": (0, 0, -70), "@root": (0, 0, -0.2)}
        acts["telemark"] = ({1: tele, 20: tele})
        acts["fall"] = ({1: {}, 10: {"hips": (-80, 0, 30), "@root": (0, 0, 0.3), "arm.L": (0, 0, 120), "arm.R": (0, 0, -60)},
                               20: {"hips": (-95, 0, 60), "@root": (0, 0, 0.2), "arm.L": (0, 0, 150), "arm.R": (0, 0, -100),
                                    "ski.L": (0, 40, 0)}})
    rig_export(kind, out_dir, acts)


bpy.context.scene.render.fps = 30
build("skater")
build("jumper")
