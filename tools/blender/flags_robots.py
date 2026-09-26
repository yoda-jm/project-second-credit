"""Iron Flags (game 8) robots: six chunky, stubby combat robots (about 0.8 units tall, one map tile = 1 unit) on a small
robot armature, each with its weapon rigidly bound to the hand bones: grunt (rifle), psycho (twin SMGs, headband and
fin), sniper (long rifle, scope, antenna, round eye), tough (bigger, shoulder rocket launcher), pyro (flamethrower,
fuel tanks) and laser (sleek, glowing laser rifle). Animations: idle, walk, run, shoot, die, cheer.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/flags_robots.py -- godot/games/flags/art/models
Faces -Y, feet at z = 0. Materials whose name contains "team" are light grey and recoloured per team by the game.
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import humanoid
import flags_models as K
from flags_models import mat, team, common, cyl, sphere, rod, flatten, reset, R90


def box(size, loc, material, rot=(0, 0, 0), bevel=None, segs=1):
    """Single-segment bevels by default on the robots: they are small on screen and a map holds many of them."""
    return K.box(size, loc, material, rot, bevel, segs)

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)


def on(bone, *parts):
    for o in flatten(parts):
        o["bone"] = bone
    return parts


def bones(layout):
    """The robot armature. Rest pose: arms bent, forearms pointing forward holding the weapon."""
    b = {
        "root": ((0, 0, 0), (0, 0, 0.1), None),
        "hips": ((0, 0, 0.3), (0, 0, 0.38), "root"),
        "torso": ((0, 0, 0.38), (0, 0, 0.58), "hips"),
        "head": ((0, 0, 0.58), (0, 0, 0.78), "torso"),
        "thigh.L": ((0.09, 0, 0.3), (0.09, 0, 0.19), "hips"),
        "shin.L": ((0.09, 0, 0.19), (0.09, 0, 0.04), "thigh.L"),
        "thigh.R": ((-0.09, 0, 0.3), (-0.09, 0, 0.19), "hips"),
        "shin.R": ((-0.09, 0, 0.19), (-0.09, 0, 0.04), "thigh.R"),
    }
    for s, side in ((1, "L"), (-1, "R")):
        if layout == "two_hand":
            elbow = (0.21 * s, -0.06 if s > 0 else -0.02, 0.43)
            hand = (0.03, -0.3, 0.42) if s > 0 else (-0.12, -0.17, 0.42)
        else:
            elbow = (0.23 * s, -0.02, 0.43)
            hand = (0.22 * s, -0.2, 0.42)
        b["arm." + side] = ((0.23 * s, 0, 0.54), elbow, "torso")
        b["forearm." + side] = (elbow, hand, "arm." + side)
    return b


def body(B, M, v):
    """Legs, pelvis, torso, arms and head (shape depends on the variant)."""
    TM, TT, metal, joint, visor = M["team"], M["trim"], M["metal"], M["joint"], M["visor"]
    w = v.get("width", 1.0)
    for s, side in ((1, "L"), (-1, "R")):
        x = 0.09 * s
        on("shin." + side,
           box((0.13, 0.2, 0.075), (x, -0.025, 0.0375), joint, bevel=0.025),
           box((0.11, 0.07, 0.05), (x, -0.1, 0.06), TT, bevel=0.02),
           cyl(0.042, 0.13, (x, 0, 0.14), metal, verts=10),
           box((0.09, 0.05, 0.1), (x, -0.045, 0.15), TM, bevel=0.02))
        on("thigh." + side, sphere(0.05, (x, 0, 0.2), joint, segs=10, rings=6),
           cyl(0.048, 0.12, (x, 0, 0.26), metal, verts=10))
        # arm: shoulder pad, upper arm, elbow, forearm, fist
        sh = (0.23 * s * w, 0, 0.54)
        elbow, hand = B["forearm." + side][0], B["forearm." + side][1]
        on("arm." + side, sphere(0.085 * v.get("pad", 1.0), (sh[0], 0, 0.56), TM, scale=(1.1, 1.0, 0.85), segs=12, rings=7),
           rod(sh, elbow, 0.035, metal, verts=8), sphere(0.042, elbow, joint, segs=10, rings=6))
        on("forearm." + side, rod(elbow, hand, 0.042, metal, r2=0.048, verts=10),
           sphere(0.05 * v.get("fist", 1.0), hand, joint, segs=10, rings=6))
    on("hips", box((0.26 * w, 0.17, 0.1), (0, 0, 0.32), joint, bevel=0.03),
       box((0.14, 0.04, 0.06), (0, -0.09, 0.31), TT, bevel=0.015))
    on("torso",
       box((0.34 * w, 0.24, 0.21), (0, 0, 0.47), metal, bevel=0.05, segs=2),
       box((0.26 * w, 0.04, 0.13), (0, -0.12, 0.48), TM, bevel=0.018),
       cyl(0.025, 0.02, (0.07, -0.143, 0.5), visor, rot=(R90, 0, 0), verts=8),
       cyl(0.07, 0.05, (0, 0, 0.585), joint, verts=10))
    if v.get("pack", True):
        on("torso", box((0.24, 0.12, 0.18), (0, 0.16, 0.48), joint, bevel=0.03),
           box((0.2, 0.02, 0.05), (0, 0.225, 0.52), TT, bevel=0.008),
           cyl(0.025, 0.08, (0.08, 0.17, 0.6), metal, verts=8))
    # head
    hs = v.get("head", "box")
    if hs == "round":
        on("head", sphere(0.15, (0, 0, 0.69), TM, scale=(1.05, 1.0, 0.82), segs=16, rings=10),
           box((0.24, 0.08, 0.06), (0, -0.115, 0.685), visor, bevel=0.025),
           box((0.08, 0.06, 0.04), (0, -0.12, 0.61), metal, bevel=0.015))
    else:
        on("head", box((0.3, 0.27, 0.21), (0, 0, 0.69), TM, bevel=0.075, segs=3),
           box((0.26, 0.2, 0.05), (0, 0.01, 0.6), metal, bevel=0.02))
        if hs == "cyclops":
            on("head", cyl(0.075, 0.04, (0, -0.135, 0.69), joint, rot=(R90, 0, 0), verts=14, bevel=0.01),
               cyl(0.052, 0.04, (0, -0.15, 0.69), visor, rot=(R90, 0, 0), verts=14))
        else:
            on("head", box((0.25, 0.05, 0.075), (0, -0.125, 0.695), visor, bevel=0.022))
        on("head", box((0.14, 0.03, 0.035), (0, -0.13, 0.625), joint, bevel=0.01))  # mouth grille
    for s in (-1, 1):
        on("head", cyl(0.045, 0.03, (s * 0.155, 0, 0.69), metal, rot=(0, R90, 0), verts=10))


# ------------------------------------------------------------------ variants

def grunt(M, C):
    gx = -0.08
    on("forearm.R",
       box((0.06, 0.26, 0.08), (gx, -0.28, 0.45), C["gun"], bevel=0.015),
       box((0.062, 0.12, 0.02), (gx, -0.28, 0.495), M["trim"], bevel=0.006),
       cyl(0.018, 0.16, (gx, -0.48, 0.455), C["dark"], rot=(R90, 0, 0), verts=8),
       box((0.04, 0.05, 0.1), (gx, -0.25, 0.38), C["dark"], bevel=0.01),
       box((0.05, 0.11, 0.06), (gx, -0.11, 0.44), C["dark"], bevel=0.015),
       box((0.02, 0.04, 0.03), (gx, -0.34, 0.505), C["dark"], bevel=0.006))
    on("head", rod((0.1, 0.06, 0.78), (0.12, 0.08, 0.88), 0.008, C["dark"], verts=4))


def psycho(M, C):
    band = mat("headband_red", (0.8, 0.12, 0.1), 0.7)
    for s, side in ((1, "L"), (-1, "R")):
        x = 0.22 * s
        on("forearm." + side,
           box((0.055, 0.18, 0.07), (x, -0.27, 0.45), C["gun"], bevel=0.015),
           cyl(0.016, 0.08, (x, -0.4, 0.455), C["dark"], rot=(R90, 0, 0), verts=8),
           box((0.035, 0.04, 0.1), (x, -0.3, 0.37), C["dark"], bevel=0.008))
    on("head", box((0.32, 0.29, 0.045), (0, 0, 0.735), band, bevel=0.015),
       box((0.03, 0.22, 0.11), (0, 0.01, 0.82), M["trim"], bevel=0.012),
       box((0.02, 0.1, 0.03), (0.05, 0.19, 0.72), band, rot=(0.5, 0, 0.3), bevel=0.006),
       box((0.02, 0.1, 0.03), (-0.05, 0.19, 0.71), band, rot=(0.7, 0, -0.3), bevel=0.006))


def sniper(M, C):
    gx = -0.08
    on("forearm.R",
       box((0.05, 0.3, 0.07), (gx, -0.24, 0.45), C["gun"], bevel=0.012),
       cyl(0.014, 0.42, (gx, -0.58, 0.455), C["dark"], rot=(R90, 0, 0), verts=8),
       cyl(0.024, 0.05, (gx, -0.8, 0.455), C["dark"], rot=(R90, 0, 0), verts=8),
       cyl(0.025, 0.2, (gx, -0.28, 0.515), C["dark"], rot=(R90, 0, 0), verts=10),
       cyl(0.02, 0.01, (gx, -0.385, 0.515), M["visor"], rot=(R90, 0, 0), verts=10),
       box((0.05, 0.12, 0.08), (gx, -0.05, 0.44), M["trim"], bevel=0.015))
    on("head", rod((-0.1, 0.06, 0.78), (-0.12, 0.08, 1.0), 0.008, C["dark"], verts=4),
       sphere(0.02, (-0.12, 0.08, 1.0), C["red_light"], segs=8, rings=5),
       box((0.34, 0.2, 0.03), (0, 0.04, 0.8), mat("hood_green", (0.32, 0.38, 0.22), 0.8), bevel=0.012))


def tough(M, C):
    on("torso",
       cyl(0.075, 0.44, (-0.31, -0.02, 0.7), M["team"], rot=(R90, 0, 0), verts=12, bevel=0.01),
       cyl(0.082, 0.05, (-0.31, -0.25, 0.7), C["dark"], rot=(R90, 0, 0), verts=12),
       cyl(0.05, 0.02, (-0.31, -0.27, 0.7), mat("missile_red", (0.85, 0.16, 0.1), 0.4, coat=0.3), rot=(R90, 0, 0), verts=10),
       box((0.1, 0.12, 0.1), (-0.29, 0.1, 0.63), C["gun"], bevel=0.02),
       box((0.1, 0.04, 0.05), (-0.31, -0.1, 0.78), C["dark"], bevel=0.01),
       box((0.4, 0.06, 0.08), (0, -0.14, 0.4), M["trim"], bevel=0.02))
    for s, side in ((1, "L"), (-1, "R")):
        on("forearm." + side, box((0.1, 0.12, 0.1), (0.22 * s, -0.19, 0.42), M["trim"], bevel=0.03))  # knuckle plates


def pyro(M, C):
    fuel = mat("fuel_red", (0.75, 0.2, 0.08), 0.35, 0.3, coat=0.5)
    flame = mat("pilot_flame", (1.0, 0.5, 0.1), 0.4, emit=8.0)
    gx = -0.08
    on("forearm.R",
       box((0.07, 0.2, 0.09), (gx, -0.24, 0.45), C["gun"], bevel=0.02),
       cyl(0.03, 0.2, (gx, -0.44, 0.46), C["steel"], rot=(R90, 0, 0), verts=10),
       cyl(0.042, 0.06, (gx, -0.56, 0.46), C["dark"], rot=(R90, 0, 0), r2=0.03, verts=10),
       sphere(0.022, (gx, -0.6, 0.43), flame, segs=8, rings=5),
       cyl(0.03, 0.1, (gx, -0.26, 0.37), fuel, verts=10))
    for s in (-1, 1):
        on("torso", cyl(0.065, 0.3, (s * 0.075, 0.18, 0.5), fuel, verts=12, bevel=0.02),
           sphere(0.064, (s * 0.075, 0.18, 0.65), fuel, segs=12, rings=6),
           cyl(0.02, 0.04, (s * 0.075, 0.18, 0.72), C["steel"], verts=8))
    on("torso", rod((-0.075, 0.2, 0.36), (-0.2, 0.0, 0.34), 0.016, C["rubber"], verts=6),
       box((0.2, 0.02, 0.04), (0, 0.25, 0.5), M["trim"], bevel=0.008))
    on("head", cyl(0.04, 0.05, (0, -0.15, 0.62), C["dark"], rot=(R90, 0, 0), verts=10))  # gas-mask filter


def laser(M, C):
    white = mat("laser_white", (0.9, 0.91, 0.93), 0.25, 0.1, coat=0.6)
    glow = mat("laser_glow", (0.2, 0.9, 1.0), 0.2, emit=6.0)
    gx = -0.07
    on("forearm.R",
       box((0.06, 0.3, 0.075), (gx, -0.28, 0.45), white, bevel=0.03),
       cyl(0.02, 0.2, (gx, -0.5, 0.455), C["gun"], rot=(R90, 0, 0), verts=10),
       sphere(0.026, (gx, -0.61, 0.455), glow, segs=8, rings=5),
       box((0.04, 0.05, 0.08), (gx, -0.18, 0.39), C["gun"], bevel=0.01),
       box((0.063, 0.1, 0.02), (gx, -0.3, 0.49), M["trim"], bevel=0.006))
    for k in range(3):
        on("forearm.R", cyl(0.03, 0.012, (gx, -0.42 - k * 0.04, 0.455), glow, rot=(R90, 0, 0), verts=10))
    for s, side in ((1, "L"), (-1, "R")):
        on("arm." + side, box((0.02, 0.12, 0.08), (0.28 * s, 0.02, 0.6), M["trim"], rot=(0, 0.4 * s, 0), bevel=0.008))
    on("head", box((0.02, 0.14, 0.06), (0, 0.05, 0.815), M["trim"], bevel=0.008))


VARIANTS = {
    "grunt": dict(fn=grunt, layout="two_hand", visor=(0.3, 0.85, 1.0)),
    "psycho": dict(fn=psycho, layout="dual", visor=(1.0, 0.35, 0.15)),
    "sniper": dict(fn=sniper, layout="two_hand", visor=(0.4, 1.0, 0.3), head="cyclops"),
    "tough": dict(fn=tough, layout="dual", visor=(1.0, 0.7, 0.15), scale=1.18, width=1.15, pad=1.3, fist=1.3),
    "pyro": dict(fn=pyro, layout="two_hand", visor=(1.0, 0.55, 0.1), pack=False),
    "laser": dict(fn=laser, layout="two_hand", visor=(0.9, 0.3, 1.0), head="round", width=0.92),
}


# ------------------------------------------------------------------ animations (degrees, bone-local; "@bone" = location)

def actions():
    UP = lambda z: (0, z, 0)  # root location: bone-local Y is world up
    a = {}
    a["idle"] = {1: {}, 16: {"head": (0, 0, 14), "torso": (2, 0, 0), "@root": UP(-0.006)},
                 32: {"head": (0, 0, -12), "torso": (2, 0, 0), "@root": UP(-0.006)}, 48: {}}
    walk = {}
    for f, ph in ((1, 1), (7, 0), (13, -1), (19, 0), (25, 1)):
        walk[f] = {"thigh.L": (-25 * ph, 0, 0), "thigh.R": (25 * ph, 0, 0),
                   "shin.L": (30 * max(0, -ph) if ph else 20, 0, 0) if ph <= 0 else (0, 0, 0),
                   "shin.R": (30 * max(0, ph), 0, 0), "torso": (3, 0, 5 * ph), "head": (0, 0, -3 * ph),
                   "@root": UP(0.02 if ph == 0 else 0.0)}
    a["walk"] = walk
    run = {}
    for f, ph in ((1, 1), (5, 0), (9, -1), (13, 0), (17, 1)):
        run[f] = {"thigh.L": (-42 * ph, 0, 0), "thigh.R": (42 * ph, 0, 0),
                  "shin.L": (55 * max(0, -ph), 0, 0), "shin.R": (55 * max(0, ph), 0, 0),
                  "hips": (8, 0, 0), "torso": (8, 0, 8 * ph), "head": (-8, 0, -6 * ph),
                  "@root": UP(0.04 if ph == 0 else -0.01)}
    a["run"] = run
    kick = {"torso": (-7, 0, 3), "head": (-5, 0, 0), "arm.R": (9, 0, 0), "arm.L": (7, 0, 0), "@root": (0, 0, -0.012)}
    a["shoot"] = {1: {}, 2: kick, 4: {"torso": (-3, 0, 1), "arm.R": (4, 0, 0), "arm.L": (3, 0, 0)}, 8: {}}
    a["die"] = {1: {},
                5: {"torso": (-18, 0, 10), "head": (-25, 0, 20), "arm.L": (20, 0, 40), "arm.R": (20, 0, -40), "@root": UP(0.05)},
                12: {"hips": (-60, 0, 8), "torso": (-15, 0, 8), "head": (-20, 0, 30), "arm.L": (10, 0, 70), "arm.R": (10, 0, -70),
                     "thigh.L": (-20, 0, 0), "@root": UP(-0.06)},
                18: {"hips": (-88, 0, 10), "torso": (-6, 0, 5), "head": (-10, 0, 40), "arm.L": (0, 0, 80), "arm.R": (0, 0, -75), "forearm.L": (-80, 0, 0), "forearm.R": (-80, 0, 0),
                     "thigh.L": (-15, 0, 0), "thigh.R": (10, 0, 0), "shin.R": (30, 0, 0), "@root": UP(-0.19)},
                22: {"hips": (-86, 0, 10), "torso": (-6, 0, 5), "head": (-10, 0, 45), "arm.L": (0, 0, 80), "arm.R": (0, 0, -75), "forearm.L": (-80, 0, 0), "forearm.R": (-80, 0, 0),
                     "thigh.L": (-18, 0, 0), "thigh.R": (10, 0, 0), "shin.R": (30, 0, 0), "@root": UP(-0.185)},
                26: {"hips": (-88, 0, 10), "torso": (-6, 0, 5), "head": (-10, 0, 40), "arm.L": (0, 0, 80), "arm.R": (0, 0, -75), "forearm.L": (-80, 0, 0), "forearm.R": (-80, 0, 0),
                     "thigh.L": (-15, 0, 0), "thigh.R": (10, 0, 0), "shin.R": (30, 0, 0), "@root": UP(-0.19)}}
    up = {"arm.L": (-150, 0, 10), "arm.R": (-150, 0, -10), "head": (-15, 0, 0), "torso": (-6, 0, 0)}
    a["cheer"] = {1: {"thigh.L": (-20, 0, 0), "thigh.R": (-20, 0, 0), "shin.L": (40, 0, 0), "shin.R": (40, 0, 0), "@root": UP(-0.04),
                      "arm.L": (-60, 0, 10), "arm.R": (-60, 0, -10)},
                  7: dict(up, **{"@root": UP(0.14), "thigh.L": (-10, 0, 0), "thigh.R": (5, 0, 0)}),
                  11: dict(up, **{"@root": UP(0.1), "head": (-15, 0, 15)}),
                  16: {"thigh.L": (-20, 0, 0), "thigh.R": (-20, 0, 0), "shin.L": (40, 0, 0), "shin.R": (40, 0, 0), "@root": UP(-0.04),
                       "arm.L": (-120, 0, 10), "arm.R": (-120, 0, -10)},
                  24: {"thigh.L": (-20, 0, 0), "thigh.R": (-20, 0, 0), "shin.L": (40, 0, 0), "shin.R": (40, 0, 0), "@root": UP(-0.04),
                       "arm.L": (-60, 0, 10), "arm.R": (-60, 0, -10)}}
    return a


def robot(name, v):
    reset()
    humanoid.BONES = bones(v["layout"])
    TM, TT = team()
    C = common()
    M = {"team": TM, "trim": TT, "metal": mat("robot_metal", (0.42, 0.44, 0.47), 0.35, 0.7),
         "joint": mat("robot_joint", (0.12, 0.12, 0.13), 0.55, 0.4),
         "visor": mat("visor_" + name, v["visor"], 0.2, emit=3.0)}
    body(humanoid.BONES, M, v)
    v["fn"](M, C)
    n = "robot_" + name
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print("%s: %d tris" % (n, sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)))
    humanoid.rig_export(n, out_dir, actions(), v.get("scale", 1.0))


only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
for k, v in VARIANTS.items():
    if not only or k in only:
        robot(k, v)
