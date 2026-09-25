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
    suit = mat("suit", (0.85, 0.15, 0.15), 0.3, coat=0.5)
    trim = mat("suit_trim", (0.96, 0.96, 0.96), 0.35, coat=0.3)
    skin = mat("skin", (0.9, 0.68, 0.54), 0.55)
    white = mat("eye_white", (0.95, 0.95, 0.93), 0.2)
    iris = mat("iris", (0.15, 0.25, 0.4), 0.1, coat=1.0)
    glove = mat("gloves", (0.1, 0.1, 0.12), 0.5)
    boot = mat("athlete_boot", (0.08, 0.08, 0.1), 0.35, coat=0.5)
    visor = mat("goggles", (0.25, 0.55, 0.85), 0.03, 0.8, coat=1.0)
    athletic_body(suit, skin, white, iris, hair=None, glove=glove, boot=boot)
    # the race bib, front and back, with a dark number panel
    for y, sgn in ((-0.108, 1), (0.1, -1)):
        box((0.2, 0.012, 0.19), (0, y, 1.27), "spine", trim)
        box((0.11, 0.014, 0.06), (0, y - 0.004 * sgn, 1.29), "spine", mat("bib_number", (0.08, 0.08, 0.1), 0.4))
    # white stripes down the outside of the legs and arms
    for s_, side in ((1, "L"), (-1, "R")):
        muscle_limb([(0.178 * s_, 0, 0.92, 0.012), (0.172 * s_, -0.01, 0.75, 0.012), (0.152 * s_, 0, 0.55, 0.01)], "thigh." + side, trim, 8, 0)
        muscle_limb([(0.25 * s_, 0, 1.4, 0.01), (0.272 * s_, 0, 1.28, 0.01), (0.29 * s_, 0, 1.15, 0.009)], "arm." + side, trim, 8, 0)
    if kind == "skater":
        sphere(0.108, (0, 0.008, 1.665), "head", suit, (0.95, 1.02, 1.13))  # the tight hood over the head
        sphere(0.095, (0, -0.02, 1.672), "head", visor, (1.02, 0.95, 0.35))  # wraparound visor
        blade = mat("blade", (0.88, 0.9, 0.93), 0.1, 1.0)
        holder = mat("blade_holder", (0.2, 0.2, 0.22), 0.3, 0.6)
        for s_, side in ((1, "L"), (-1, "R")):
            box((0.03, 0.2, 0.03), (0.1 * s_, -0.04, 0.0), "shin." + side, holder)
            box((0.006, 0.44, 0.035), (0.1 * s_, -0.06, -0.03), "shin." + side, blade)
    else:
        shell = mat("helmet", (0.96, 0.96, 0.97), 0.2, coat=1.0)
        sphere(0.118, (0, 0.005, 1.69), "head", shell, (0.98, 1.05, 0.95))
        sphere(0.1, (0, -0.035, 1.665), "head", visor, (1.0, 0.9, 0.38))
        box((0.23, 0.02, 0.02), (0, 0.0, 1.665), "head", mat("strap", (0.1, 0.1, 0.1), 0.5))
        ski = mat("ski", (0.95, 0.78, 0.1), 0.25, coat=0.8)
        ski_edge = mat("ski_edge", (0.1, 0.1, 0.12), 0.3)
        for s_, side in ((1, "L"), (-1, "R")):
            box((0.11, 2.35, 0.022), (0.1 * s_, -0.52, -0.005), "ski." + side, ski)
            box((0.112, 2.35, 0.006), (0.1 * s_, -0.52, -0.018), "ski." + side, ski_edge)
            box((0.11, 0.16, 0.022), (0.1 * s_, -1.72, 0.035), "ski." + side, ski, rot=(0.45, 0, 0))  # the tip, turned up
            box((0.07, 0.16, 0.05), (0.1 * s_, -0.03, 0.03), "ski." + side, mat("binding", (0.2, 0.2, 0.22), 0.3, 0.6))


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
                "ski.L": (30, 0, 0), "ski.R": (30, 0, 0)}  # the ski bone's axis is flipped: +(thigh + shin) keeps the skis flat
        acts["tuck"] = ({1: tuck, 20: tuck})
        # the flight: body leaning far forward over V-shaped skis, arms back
        fly = {"hips": (70, 0, 0), "head": (-60, 0, 0), "arm.L": (20, 0, 12), "arm.R": (20, 0, -12),
               "ski.L": (62, 0, 18), "ski.R": (62, 0, -18), "thigh.L": (5, 0, 0), "thigh.R": (5, 0, 0)}  # skis along the body, in a V
        fly2 = dict(fly)
        fly2["hips"] = (73, 0, 2)
        acts["flight"] = ({1: fly, 30: fly2, 60: fly})
        tele = {"spine": (20, 0, 0), "thigh.L": (-40, 0, 0), "shin.L": (60, 0, 0), "thigh.R": (20, 0, 0), "shin.R": (50, 0, 0),
                "arm.L": (0, 0, 70), "arm.R": (0, 0, -70), "@root": (0, 0, -0.2), "ski.L": (20, 0, 0), "ski.R": (70, 0, 0)}
        acts["telemark"] = ({1: tele, 20: tele})
        acts["fall"] = ({1: {}, 10: {"hips": (-80, 0, 30), "@root": (0, 0, 0.3), "arm.L": (0, 0, 120), "arm.R": (0, 0, -60)},
                               20: {"hips": (-95, 0, 60), "@root": (0, 0, 0.2), "arm.L": (0, 0, 150), "arm.R": (0, 0, -100),
                                    "ski.L": (-65, 40, 0), "ski.R": (-95, 0, 0)}})
    rig_export(kind, out_dir, acts)


bpy.context.scene.render.fps = 30
build("skater")
build("jumper")
