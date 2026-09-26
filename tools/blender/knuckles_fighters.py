"""Neon Knuckles fighters on the shared humanoid rig: the two brothers (blue and red jackets), the thug (jacket and
cap), the knifer (hoodie), the bruiser (big, bald, tank top) and the boss (leather jacket, sunglasses), smoothly
skinned, with the fighting animations. Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/knuckles_fighters.py -- godot/games/knuckles/art/models [names]
Timing: 24 fps; the game plays attacks at 1.3x, so a move's hit lands at frame 1 + startup * 31.2 (brawl_engine.gd
ATTACKS). The walk is a guarded jog of 2.0 m per 16-frame cycle (3.0 m/s at 1x; the view scales it by speed).
The weapon rides bone hand.R (the grip runs along the hand's local +Z).
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
FPS = 24
SK = Skeleton(proportions())


def P(base, **kw):
    """A pose: `base` with some channels replaced (bone names use dots, so pass them as **{...})."""
    d = dict(base)
    d.update(kw)
    return d


# ------------------------------------------------------------------ poses

FEET = {"ik_foot.L": (0.11, 0.16, 0.09, 0, 12), "ik_foot.R": (-0.15, -0.2, 0.09, 0, 38), "ikw.L": 1.0, "ikw.R": 1.0}
GUARD = dict(FEET, **{
    "root": (0.0, -0.02, -0.075), "hips": (6, -18, 0), "spine": (6, -6, 0), "chest": (6, -6, 0), "neck": (-4, 10, 0),
    "head": (-6, 16, 0), "clavicle.L": (6, 0, 4), "clavicle.R": (4, 0, 6),
    "arm.L": (44, -10, 16), "forearm.L": (98, 0, 0), "hand.L": (0, 0, -8),
    "arm.R": (32, -8, 22), "forearm.R": (116, 0, 0), "hand.R": (0, 0, -10),
    "toe.L": (0, 0, 0), "toe.R": (0, 0, 0)})


def with_feet(pose, **feet):
    """Moves the stance feet: L=(left, fwd, up, pitch, yaw)."""
    p = dict(pose)
    for X, v in feet.items():
        p["ik_foot." + X] = v
    return p


def idle():
    k = {}
    for i in range(0, 41, 4):
        t = i / 40.0
        b = math.sin(2 * math.pi * t * 2)           # a light bounce, twice a loop
        br = math.sin(2 * math.pi * t)              # one breath
        sway = math.sin(2 * math.pi * t)
        k[i + 1] = P(GUARD, **{"root": (0.012 * sway, -0.02, -0.075 - 0.012 * (0.5 + 0.5 * b)),
                               "chest": (6 + 1.5 * br, -6 + 1.5 * sway, 0), "clavicle.L": (6, 0, 4 + 2 * br),
                               "clavicle.R": (4, 0, 6 + 2 * br), "neck": (-4 - 1 * br, 10, 0),
                               "arm.L": (44 + 3 * b, -10, 16), "arm.R": (32 + 2 * math.sin(2 * math.pi * (t * 2 - 0.15)), -8, 22),
                               "forearm.L": (98 - 3 * b, 0, 0), "head": (-6, 16 - 2 * sway, 1.5 * sway)})
    return Anim(k, loop=True)


def walk():
    base = {"arm.L": (30, -10, 8), "forearm.L": (96, 0, 0), "arm.R": (26, -8, 8), "forearm.R": (104, 0, 0),
            "hand.L": (0, 0, -8), "hand.R": (0, 0, -10), "clavicle.L": (4, 0, 3), "clavicle.R": (4, 0, 3),
            "spine": (4, 0, 0), "chest": (4, 0, 0)}
    return gait(SK, 16, 2.0, 0.4, lift=0.2, lift_at=0.4, strike=10, push=38, bob=-0.03, drop=-0.05, lean=8,
                arm_swing=16, arm_out=6, elbow=0, elbow_swing=18, pelvis_yaw=9, pelvis_roll=4, shoulder_yaw=9,
                reach=0.38, base=base, toe_out=5, step=1)


def jab():
    ext = P(GUARD, **{"arm.L": (88, -30, 6, 0), "forearm.L": (6, 0, 0), "hand.L": (0, 0, 0), "clavicle.L": (18, 0, 0),
                      "chest": (8, -20, 0), "spine": (6, -10, 0), "hips": (6, -22, 0), "head": (-6, 30, 0),
                      "root": (0, 0.03, -0.085), "arm.R": (38, -8, 16)})
    return Anim({1: GUARD,
                 2: P(GUARD, **{"arm.L": (44, -12, 12), "forearm.L": (118, 0, 0), "chest": (6, -3, 0)}),
                 3: P(ext, **{"arm.L": (86, -28, 6, 0), "forearm.L": (14, 0, 0)}),
                 4: ext,
                 5: P(ext, **{"arm.L": (86, -26, 6, 0), "forearm.L": (10, 0, 0)}),
                 7: P(GUARD, **{"arm.L": (60, -14, 10), "forearm.L": (80, 0, 0)}),
                 9: GUARD})


def punch():
    load = P(GUARD, **{"chest": (6, -14, 0), "hips": (6, -22, 0), "arm.R": (30, -8, 20), "forearm.R": (132, 0, 0),
                       "root": (0, -0.03, -0.085)})
    ext = P(GUARD, **{"arm.R": (94, -40, 2, -4), "forearm.R": (4, 0, 0), "hand.R": (0, 0, 0), "clavicle.R": (20, 0, -2),
                      "chest": (8, 8, 0), "spine": (8, 4, 0), "hips": (8, 6, 0), "head": (-8, -12, 0),
                      "arm.L": (40, -8, 20), "forearm.L": (125, 0, 0), "root": (0, 0.07, -0.1),
                      "ik_foot.R": (-0.15, -0.2, 0.09, -28, 20)})
    return Anim({1: GUARD, 3: load,
                 4: P(ext, **{"arm.R": (86, -30, 8, 0), "forearm.R": (30, 0, 0), "chest": (8, 2, 0)}),
                 5: ext, 7: P(ext, **{"forearm.R": (10, 0, 0)}),
                 9: P(GUARD, **{"arm.R": (50, -10, 16), "forearm.R": (95, 0, 0), "chest": (6, 6, 0)}),
                 11: GUARD})


def hook():
    wind = P(GUARD, **{"chest": (4, -28, 4), "spine": (6, -12, 0), "hips": (6, -26, 0), "arm.L": (40, 0, 62, 20),
                       "forearm.L": (96, 0, 0), "root": (0.03, -0.04, -0.11), "head": (-8, 30, 0),
                       "ik_foot.L": (0.11, 0.16, 0.09, 0, 20)})
    hit = P(GUARD, **{"chest": (10, 16, -6), "spine": (8, 8, 0), "hips": (6, 4, 0), "arm.L": (14, 0, 84, 34),
                      "forearm.L": (82, 0, 0), "hand.L": (0, 0, 0), "clavicle.L": (18, 0, 6), "root": (-0.02, 0.04, -0.11),
                      "head": (-8, -14, 0), "arm.R": (40, -6, 16), "ik_foot.L": (0.11, 0.16, 0.09, 0, -10),
                      "ik_foot.R": (-0.15, -0.2, 0.09, -20, 30)})
    return Anim({1: GUARD, 4: wind, 5: P(wind, **{"chest": (6, -18, 2)}),
                 7: hit, 9: P(hit, **{"chest": (12, 26, -6), "arm.L": (10, 0, 80, 48), "forearm.L": (98, 0, 0)}),
                 12: P(hit, **{"chest": (10, 12, -4), "arm.L": (24, 0, 60, 36), "forearm.L": (106, 0, 0)}),
                 17: GUARD})


def kick():
    fk = {"ikw.R": 0.0}
    chamber = P(GUARD, **fk, **{"thigh.R": (85, 10, 6), "shin.R": (110, 0, 0), "foot.R": (-10, 0, 0),
                                "hips": (0, 0, 0), "spine": (2, -2, 0), "chest": (2, -4, 0), "root": (-0.02, 0.0, -0.05),
                                "arm.L": (46, -10, 20), "arm.R": (20, -8, 30), "forearm.R": (105, 0, 0)})
    ext = P(chamber, **{"thigh.R": (90, 0, 0), "shin.R": (4, 0, 0), "foot.R": (-35, 0, 0), "hips": (-8, 2, 0),
                        "spine": (-1, 0, 0), "chest": (2, -4, 0), "head": (2, 10, 0), "root": (-0.02, -0.02, -0.03),
                        "arm.R": (6, -8, 34), "forearm.R": (90, 0, 0), "arm.L": (50, -10, 20), "forearm.L": (100, 0, 0)})
    return Anim({1: GUARD, 3: P(GUARD, **{"root": (0, -0.03, -0.1), "ikw.R": 1.0}), 5: chamber,
                 6: P(ext, **{"shin.R": (40, 0, 0)}), 7: ext, 9: ext, 11: chamber,
                 14: P(GUARD, **{"ik_foot.R": (-0.15, -0.16, 0.14, 0, 38), "ikw.R": 0.7}), 16: GUARD})


def knee():
    hold = P(GUARD, **{"arm.L": (70, -10, 10, 10), "forearm.L": (60, 0, 0), "arm.R": (70, -10, 10, 10),
                       "forearm.R": (60, 0, 0), "hand.L": (10, 0, 0), "hand.R": (10, 0, 0), "chest": (14, 0, 0),
                       "spine": (10, 0, 0), "hips": (4, -6, 0), "head": (-14, 6, 0)})
    up = P(hold, **{"ikw.R": 0.0, "thigh.R": (105, 4, 0), "shin.R": (120, 0, 0), "foot.R": (-20, 0, 0), "hips": (-8, -4, 0),
                    "root": (0, 0.06, -0.02), "arm.L": (60, -10, 10, 10), "forearm.L": (80, 0, 0), "arm.R": (60, -10, 10, 10),
                    "forearm.R": (80, 0, 0), "chest": (22, 0, 0), "spine": (14, 0, 0)})
    return Anim({1: hold, 2: P(hold, **{"root": (0, -0.03, -0.1)}), 4: up, 6: P(up, **{"thigh.R": (98, 4, 0)}),
                 8: P(hold, **{"ikw.R": 0.5, "thigh.R": (40, 0, 0), "shin.R": (60, 0, 0)}), 11: hold})


def elbow():
    # a back elbow at whoever is behind: look back, drive the right elbow back
    look = P(GUARD, **{"head": (-6, -50, 0), "neck": (-4, -20, 0), "chest": (6, 10, 0)})
    hit = P(GUARD, **{"arm.R": (-45, -10, 55), "forearm.R": (135, 0, 0), "clavicle.R": (-14, 0, 4), "chest": (2, -36, 0),
                      "spine": (4, -16, 0), "hips": (4, -10, 0), "head": (-4, -70, 0), "neck": (-2, -30, 0),
                      "arm.L": (60, -10, 20, 20), "forearm.L": (100, 0, 0), "root": (0, -0.06, -0.1),
                      "ik_foot.R": (-0.15, -0.2, 0.09, 0, 20)})
    return Anim({1: GUARD, 3: look, 5: P(hit, **{"arm.R": (-40, -10, 24), "chest": (4, -20, 0)}), 6: hit, 8: hit,
                 11: P(GUARD, **{"head": (-6, -10, 0)}), 15: GUARD})


def bat():
    up = P(GUARD, **{"arm.R": (150, -20, 20), "forearm.R": (70, 0, 0), "hand.R": (0, 0, -20), "chest": (-4, -34, 4),
                     "spine": (0, -14, 0), "hips": (4, -26, 0), "arm.L": (60, -6, 30), "forearm.L": (80, 0, 0),
                     "root": (0.02, -0.06, -0.08), "head": (-6, 30, 0)})
    hit = P(GUARD, **{"arm.R": (80, -30, 10, 24), "forearm.R": (12, 0, 0), "hand.R": (-20, 0, 20), "chest": (14, 34, -4),
                      "spine": (10, 14, 0), "hips": (8, 12, 0), "arm.L": (30, -6, 40), "forearm.L": (60, 0, 0),
                      "root": (0, 0.1, -0.12), "head": (-10, -20, 0), "ik_foot.L": (0.13, 0.26, 0.09, 0, 8),
                      "ik_foot.R": (-0.15, -0.2, 0.09, -30, 25)})
    return Anim({1: GUARD, 4: P(up, **{"arm.R": (120, -16, 22), "forearm.R": (90, 0, 0)}), 6: up,
                 8: P(hit, **{"arm.R": (120, -30, 14, 10), "forearm.R": (30, 0, 0), "chest": (8, 10, 0)}),
                 9: hit, 11: P(hit, **{"arm.R": (40, -30, 10, 60), "forearm.R": (20, 0, 0), "chest": (16, 48, -6)}),
                 14: P(hit, **{"arm.R": (30, -20, 16, 40), "forearm.R": (60, 0, 0), "chest": (12, 30, -4)}),
                 19: GUARD})


def grab():
    k = {}
    for i in range(0, 21, 5):
        t = i / 20.0
        b = math.sin(2 * math.pi * t)
        k[i + 1] = P(GUARD, **{"arm.L": (66, -10, 8, 18), "forearm.L": (58 + 3 * b, 0, 0), "arm.R": (66, -10, 8, 18),
                               "forearm.R": (58 - 3 * b, 0, 0), "hand.L": (10, 0, 10), "hand.R": (10, 0, 10),
                               "chest": (12 + b, 0, 0), "spine": (8, 0, 0), "hips": (4, -8, 0), "head": (-12, 8, 0),
                               "root": (0, -0.02, -0.09 + 0.006 * b)})
    return Anim(k, loop=True)


def held():
    k = {}
    for i in range(0, 17, 4):
        t = i / 16.0
        b = math.sin(2 * math.pi * t)
        k[i + 1] = P(FEET, **{"root": (0.01 * b, 0.02, -0.14), "hips": (18, 0, 0), "spine": (22 + 2 * b, 0, 2 * b),
                              "chest": (16, 0, 0), "neck": (14, 0, 0), "head": (10, 0, 4 * b),
                              "arm.L": (20 + 4 * b, 0, 14), "forearm.L": (30, 0, 0), "arm.R": (20 - 4 * b, 0, 14),
                              "forearm.R": (34, 0, 0), "hand.L": (0, 0, -20), "hand.R": (0, 0, -20),
                              "ik_foot.L": (0.13, 0.08, 0.09, 0, 10), "ik_foot.R": (-0.13, -0.08, 0.09, 0, 10)})
    return Anim(k, loop=True)


def hit():
    snap = P(GUARD, **{"head": (-30, 30, 10), "neck": (-18, 0, 0), "chest": (-16, -10, 6), "spine": (-8, 0, 0),
                       "hips": (-4, -18, 0), "arm.L": (20, -10, 40), "forearm.L": (70, 0, 0), "arm.R": (10, -8, 44),
                       "forearm.R": (60, 0, 0), "root": (0, -0.07, -0.08), "clavicle.L": (-6, 0, 12), "clavicle.R": (-6, 0, 12)})
    return Anim({1: GUARD, 2: P(snap, **{"head": (-18, 24, 6), "chest": (-8, -8, 3)}), 3: snap,
                 5: P(snap, **{"head": (-14, 22, 4), "chest": (-6, -8, 2), "root": (0, -0.1, -0.11),
                               "ik_foot.L": (0.11, 0.06, 0.09, 0, 12)}),
                 8: P(GUARD, **{"head": (0, 16, 0), "chest": (10, -6, 0), "root": (0, -0.06, -0.1),
                                "ik_foot.L": (0.11, 0.08, 0.09, 0, 12)}),
                 12: GUARD})


LIE = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-90, 0, 0), "root": (0, 0, 0.11), "hips": (0, 0, 0), "spine": (-4, 0, 0),
       "chest": (-4, 0, 0), "neck": (6, 0, 0), "head": (4, 30, 0), "arm.L": (10, 0, 70), "forearm.L": (40, 0, 0),
       "arm.R": (20, 0, 60), "forearm.R": (25, 0, 0), "thigh.L": (18, 0, 8), "shin.L": (30, 0, 0), "thigh.R": (6, 0, 12),
       "shin.R": (10, 0, 0), "foot.L": (-30, 0, 0), "foot.R": (-35, 0, 0)}


def down(ko=False):
    fly = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-35, 0, 0), "root": (0, 0.2, 0.12), "hips": (-10, 0, 0), "spine": (-14, 0, 0),
           "chest": (-10, 0, 0), "neck": (-10, 0, 0), "head": (-20, 10, 0), "arm.L": (70, 0, 50), "forearm.L": (40, 0, 0),
           "arm.R": (80, 0, 40), "forearm.R": (30, 0, 0), "thigh.L": (30, 0, 6), "shin.L": (50, 0, 0),
           "thigh.R": (10, 0, 6), "shin.R": (20, 0, 0), "foot.L": (-20, 0, 0), "foot.R": (-20, 0, 0)}
    k = {1: P(GUARD, **{"head": (-26, 20, 8), "chest": (-14, -10, 4), "root": (0, -0.06, -0.08)}),
         3: P(fly, **{"turn": (-20, 0, 0), "root": (0, 0.08, 0.08)}),
         6: fly,
         9: P(fly, **{"turn": (-70, 0, 0), "root": (0, 0.45, 0.2), "arm.L": (100, 0, 60), "arm.R": (100, 0, 50),
                      "thigh.L": (40, 0, 6), "shin.L": (40, 0, 0)}),
         11: P(LIE, **{"root": (0, 0.6, 0.11), "head": (-10, 10, 0), "arm.L": (40, 0, 80), "arm.R": (40, 0, 70),
                       "thigh.L": (35, 0, 8), "shin.L": (40, 0, 0), "thigh.R": (25, 0, 12), "shin.R": (30, 0, 0)}),
         13: P(LIE, **{"turn": (-84, 0, 0), "root": (0, 0.6, 0.15), "head": (10, 20, 0), "thigh.L": (28, 0, 8),
                       "thigh.R": (18, 0, 12), "arm.L": (20, 0, 76)}),
         16: P(LIE, **{"root": (0, 0.6, 0.11)})}
    if ko:
        k[16] = P(LIE, **{"root": (0, 0.6, 0.11), "turn": (-90, 0, 4)})
        k[22] = P(LIE, **{"root": (0, 0.6, 0.1), "turn": (-91, 0, 6), "head": (8, 60, 10), "arm.L": (6, 0, 88),
                          "forearm.L": (20, 0, 0), "arm.R": (10, 0, 80), "forearm.R": (15, 0, 0), "thigh.L": (8, 0, 10),
                          "shin.L": (12, 0, 0), "thigh.R": (4, 0, 14), "shin.R": (6, 0, 0)})
    return Anim(k)


def getup():
    lie = P(LIE, **{"root": (0, 0.6, 0.11)})
    sit = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-62, 0, 0), "root": (0, 0.45, 0.1), "hips": (0, 0, 0), "spine": (34, 0, 0),
           "chest": (16, 0, 0), "neck": (0, 0, 0), "head": (-10, 0, 0), "arm.L": (-45, 0, 25), "forearm.L": (15, 0, 0),
           "arm.R": (-45, 0, 25), "forearm.R": (15, 0, 0), "thigh.L": (55, 0, 6), "shin.L": (115, 0, 0),
           "thigh.R": (40, 0, 12), "shin.R": (80, 0, 0), "foot.L": (10, 0, 0), "foot.R": (0, 0, 0)}
    crouch = P(GUARD, **{"root": (0, -0.12, -0.42), "hips": (30, -10, 0), "spine": (20, 0, 0), "chest": (10, 0, 0),
                         "head": (-30, 10, 0), "neck": (-10, 0, 0), "arm.L": (40, -10, 20), "forearm.L": (90, 0, 0),
                         "arm.R": (30, -8, 24), "forearm.R": (100, 0, 0), "ik_foot.L": (0.13, 0.1, 0.09, 0, 12),
                         "ik_foot.R": (-0.15, -0.14, 0.09, 0, 30)})
    return Anim({1: lie, 4: sit, 7: P(crouch, **{"ikw.L": 0.8, "ikw.R": 0.8}), 10: P(crouch, **{"root": (0, -0.06, -0.2), "hips": (14, -14, 0)}),
                 13: GUARD})


def thrown():
    base = {"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0, 0.1), "spine": (-10, 0, 0), "chest": (-10, 0, 0), "head": (-20, 0, 0),
            "arm.L": (120, 0, 60), "forearm.L": (40, 0, 0), "arm.R": (140, 0, 50), "forearm.R": (30, 0, 0),
            "thigh.L": (40, 0, 10), "shin.L": (70, 0, 0), "thigh.R": (10, 0, 10), "shin.R": (30, 0, 0)}
    return Anim({1: P(base, **{"hips": (-30, 0, 10), "root": (0, 0, 0.0)}),
                 5: P(base, **{"hips": (-80, 0, 20), "root": (0, 0, 0.3)}),
                 10: P(base, **{"hips": (-125, 0, 25), "root": (0, 0, 0.55), "arm.L": (160, 0, 70), "thigh.L": (60, 0, 10)}),
                 16: P(base, **{"hips": (-100, 0, 15), "root": (0, 0, 0.45), "arm.L": (120, 0, 80), "arm.R": (110, 0, 70)})})


def jump():
    push = P(GUARD, **{"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0, 0.05), "hips": (4, -10, 0), "thigh.L": (10, 0, 4),
                       "shin.L": (10, 0, 0), "thigh.R": (-10, 0, 4), "shin.R": (20, 0, 0), "foot.L": (-40, 0, 0),
                       "foot.R": (-40, 0, 0), "arm.L": (60, -10, 20), "arm.R": (50, -8, 24)})
    tuck = P(push, **{"thigh.L": (80, 0, 8), "shin.L": (110, 0, 0), "thigh.R": (50, 0, 8), "shin.R": (100, 0, 0),
                      "foot.L": (-10, 0, 0), "foot.R": (-20, 0, 0), "root": (0, 0, 0.12), "spine": (12, -6, 0),
                      "chest": (8, -6, 0), "arm.L": (52, -10, 18), "arm.R": (40, -8, 22)})
    land = P(tuck, **{"thigh.L": (40, 0, 6), "shin.L": (50, 0, 0), "thigh.R": (20, 0, 6), "shin.R": (50, 0, 0),
                      "foot.L": (0, 0, 0), "foot.R": (-5, 0, 0), "root": (0, 0, 0.04), "spine": (8, -6, 0)})
    return Anim({1: P(GUARD, **{"root": (0, -0.02, -0.16)}), 3: push, 7: tuck, 12: tuck, 17: land})


def jump_kick():
    tuck = P(GUARD, **{"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0, 0.12), "thigh.L": (80, 0, 8), "shin.L": (110, 0, 0),
                       "thigh.R": (60, 0, 8), "shin.R": (110, 0, 0), "spine": (10, -6, 0)})
    kick = P(tuck, **{"hips": (-26, 30, 0), "spine": (-6, 10, 0), "chest": (-4, 6, 0), "head": (6, -30, 0),
                      "thigh.R": (96, 0, 4), "shin.R": (0, 0, 0), "foot.R": (-30, 0, 0), "thigh.L": (70, 0, 10),
                      "shin.L": (125, 0, 0), "arm.L": (10, 0, 50), "forearm.L": (60, 0, 0), "arm.R": (-10, 0, 40),
                      "forearm.R": (50, 0, 0), "root": (0, 0, 0.2)})
    return Anim({1: tuck, 3: P(kick, **{"shin.R": (50, 0, 0)}), 4: kick, 11: P(kick, **{"thigh.R": (90, 0, 4)}),
                 15: tuck})


def victory():
    up = P(GUARD, **{"arm.R": (165, -30, 20), "forearm.R": (20, 0, 0), "hand.R": (0, 0, 0), "clavicle.R": (0, 0, 20),
                     "chest": (-4, 10, 0), "spine": (-2, 6, 0), "head": (-16, 10, 0), "arm.L": (20, -10, 20),
                     "forearm.L": (90, 0, 0), "root": (0, -0.02, -0.03)})
    return Anim({1: GUARD, 4: P(GUARD, **{"root": (0, -0.02, -0.14), "arm.R": (60, -10, 30), "forearm.R": (130, 0, 0)}),
                 8: P(up, **{"root": (0, -0.02, 0.0)}), 11: P(up, **{"arm.R": (170, -30, 16), "forearm.R": (10, 0, 0)}),
                 15: up, 20: P(up, **{"arm.R": (160, -30, 22), "forearm.R": (30, 0, 0), "root": (0, -0.02, -0.05)})})


def actions():
    return {"idle": idle(), "walk": walk(), "jab": jab(), "punch": punch(), "hook": hook(), "kick": kick(),
            "jump": jump(), "jump_kick": jump_kick(), "knee": knee(), "elbow": elbow(), "bat": bat(), "grab": grab(),
            "held": held(), "hit": hit(), "down": down(), "getup": getup(), "thrown": thrown(), "ko": down(True),
            "victory": victory()}


# ------------------------------------------------------------------ outfits

def jacket(jk, dark, sh):
    """An open jacket: a shell round the torso (open at the front), sleeves, cuffs, a collar and the hem."""
    g = 0.014
    rings = [(z, rx + g, ry + g, cy) for z, rx, ry, cy, sq in torso_rings(1.0, 1.43, 0.0, sh)]
    rings.append((1.46, 0.15, 0.085, 0.006))
    shell(rings, -66, 246, "~body", jk, 0.008, 28, 1)
    shell([(1.0, rings[0][1] + 0.004, rings[0][2] + 0.004, 0.0), (1.035, rings[0][1] + 0.002, rings[0][2] + 0.002, 0.0)],
          -66, 246, "~body", dark, 0.01, 28, 0)   # the hem
    shell([(1.43, 0.13, 0.086, 0.008), (1.47, 0.108, 0.08, 0.012), (1.51, 0.098, 0.078, 0.016)], -62, 242, "~body", dark, 0.01, 24, 1)
    ak = sh.get("arms", 1.0)
    for X, s in (("L", 1), ("R", -1)):
        shp = SK.head("arm." + X)
        sphere(0.054 * ak + 0.013, tuple(shp + Vector((0.006 * s, 0.002, -0.03))), "~arm." + X, jk, (1.0, 1.1, 1.2), 20, 12)
        tube(arm_path(SK, X, 0.012, 0.0, 0.9, shape=ak), "~arm." + X, jk, 18, 0.016, lateral=(s, 0, 0))
        tube(arm_path(SK, X, 0.016, 0.8, 0.92, shape=ak), "~arm." + X, dark, 18, 0.012, lateral=(s, 0, 0))


def fighter(name, jacket_c, shirt, pants, skin_c, hair_c=None, build=1.0, extras=None, leather=False, sole=(0.9, 0.9, 0.88),
            shape=None, sleeves="long"):
    clear()
    sh = shape or {}
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
    human_body(SK, skin, top, legs, white, iris, hair=hair, shoes=shoes, sole=rubber, glove=skin, sleeves=sleeves,
               hands="fist", shape=sh)
    # a belt with a buckle
    hk = sh.get("hips", 1.0)
    body_loft([(z, rx + 0.006, ry + 0.006, cy, sq) for z, rx, ry, cy, sq in torso_rings(1.0, 1.06, 0.0, sh)], "~body", belt, 26, 0)
    box((0.06, 0.02, 0.045), (0, -0.1 * hk - 0.004, 1.03), "~body", metal, bevel=0.006)
    if jacket_c:
        jk = mat(name + "_jacket", jacket_c, 0.3 if leather else 0.42, coat=0.8 if leather else 0.45)
        dark = mat(name + "_jacket_trim", tuple(c * 0.45 for c in jacket_c), 0.5, coat=0.3)
        jacket(jk, dark, sh)
    if extras:
        extras()
    rig_export(name, out_dir, actions(), build, skeleton=SK, fps=FPS)


def torus(R, r, loc, bone, material, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=24, minor_segments=6, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return tag(o, bone, material)


H = (0, -0.012, 1.665)  # the head's centre


def cap():
    red = mat("cap", (0.75, 0.15, 0.12), 0.6)
    sphere(0.108, (0, H[1] + 0.012, H[2] + 0.042), "head", red, (0.98, 1.04, 0.72))
    box((0.15, 0.1, 0.014), (0, H[1] - 0.12, H[2] + 0.03), "head", red, rot=(-0.12, 0, 0), bevel=0.006)


def shades():
    dark = mat("shades", (0.02, 0.02, 0.03), 0.05, 0.6, coat=1.0)
    box((0.13, 0.02, 0.032), (0, H[1] - 0.088, H[2] + 0.018), "head", dark, bevel=0.008)
    for k in (-1, 1):
        box((0.008, 0.08, 0.008), (0.066 * k, H[1] - 0.045, H[2] + 0.022), "head", dark, bevel=0.003)


def pompadour():
    brown = mat("hero_a_hair", (0.35, 0.22, 0.1), 0.6, coat=0.3)
    sphere(0.068, (0, H[1] - 0.05, H[2] + 0.1), "head", brown, (1.2, 0.9, 0.72))
    sphere(0.06, (0, H[1] + 0.02, H[2] + 0.115), "head", brown, (1.35, 1.25, 0.6))


def headband():
    red = mat("headband", (0.85, 0.1, 0.1), 0.6)
    torus(0.1, 0.013, (0, H[1] + 0.012, H[2] + 0.055), "head", red, scale=(0.92, 1.02, 1.0))
    for k in (-1, 1):  # the knot's tails at the back
        box((0.02, 0.012, 0.13), (0.02 * k, H[1] + 0.115, H[2] - 0.005), "head", red, (0.25 * k, 0, 0))
    black = mat("hero_b_hair", (0.1, 0.08, 0.06), 0.6, coat=0.3)
    for k in range(5):  # spikes over the band
        a = (k - 2) * 0.35
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.035, radius2=0.0, depth=0.1,
                                        location=(0.06 * math.sin(a), H[1] + 0.022, H[2] + 0.13), rotation=(0.3, a * 0.8, 0))
        tag(bpy.context.active_object, "head", black)


def boss_extras():
    shades()
    gold = mat("buckle", (0.85, 0.7, 0.35), 0.2, 1.0)
    torus(0.078, 0.007, (0, -0.03, 1.43), "~body", gold, rot=(0.4, 0, 0), scale=(1.0, 1.15, 1.0))  # a chain


def thug_extras():
    cap()


def bruiser_extras():
    strap = mat("bruiser_strap", (0.06, 0.05, 0.04), 0.4)
    sh = BRUISER
    for s_ in (-1, 1):  # braces over the tank top, front and back
        for y, sgn in ((-1, -1), (1, 1)):
            rings = torso_rings(1.05, 1.43, 0.0, sh)
            pts = [(0.085 * s_ * (1.05 if z > 1.38 else 1.0), (ry + 0.006) * sgn + cy, z, 0.012) for z, rx, ry, cy, sq in rings]
            tube(pts, "~body", strap, 6, 0.03, ell=(1.4, 0.35))
    for X in "LR":  # wrist wraps
        tube(arm_path(SK, X, 0.008, 0.86, 1.0, shape=sh["arms"]), "~arm." + X, strap, 16, 0.01)


def hood():
    green = mat("knifer_top", (0.25, 0.35, 0.2), 0.75)
    cx, cy, cz = H   # open at the face, peaked over the brow
    shell([(cz - 0.1, 0.085, 0.09, cy + 0.03), (cz - 0.05, 0.112, 0.118, cy + 0.03), (cz + 0.02, 0.118, 0.126, cy + 0.028),
           (cz + 0.08, 0.108, 0.118, cy + 0.024), (cz + 0.125, 0.07, 0.085, cy + 0.02), (cz + 0.15, 0.02, 0.03, cy + 0.02)],
          -58, 238, "head", green, 0.012, 20, 1)
    shell([(1.46, 0.11, 0.09, 0.02), (1.52, 0.12, 0.1, 0.03), (1.58, 0.12, 0.1, 0.035)], 30, 150, "~body", green, 0.01, 12, 1)


BRUISER = {"chest": 1.14, "waist": 1.18, "hips": 1.06, "arms": 1.22, "legs": 1.1, "neck": 1.25, "hand": 1.12}
FIGHTERS = {
    "hero_a": lambda: fighter("hero_a", (0.12, 0.3, 0.8), (0.95, 0.95, 0.95), (0.16, 0.22, 0.42), (0.9, 0.7, 0.55), (0.35, 0.22, 0.1),
                              extras=pompadour, shape={"chest": 1.04, "arms": 1.06, "waist": 0.97}),
    "hero_b": lambda: fighter("hero_b", (0.78, 0.12, 0.12), (0.95, 0.95, 0.95), (0.18, 0.18, 0.24), (0.85, 0.65, 0.5), (0.1, 0.08, 0.06),
                              extras=headband, shape={"chest": 1.05, "arms": 1.08, "waist": 0.97}),
    "thug": lambda: fighter("thug", (0.3, 0.3, 0.32), (0.85, 0.8, 0.7), (0.3, 0.28, 0.25), (0.88, 0.68, 0.52), (0.2, 0.15, 0.1),
                            1.0, thug_extras, sole=(0.3, 0.25, 0.2), shape={"waist": 1.06}),
    "knifer": lambda: fighter("knifer", None, (0.25, 0.35, 0.2), (0.2, 0.2, 0.22), (0.7, 0.5, 0.38), None, 0.95, hood,
                              sole=(0.85, 0.85, 0.8), shape={"chest": 0.95, "arms": 0.94, "legs": 0.95}),
    "bruiser": lambda: fighter("bruiser", None, (0.9, 0.9, 0.85), (0.25, 0.3, 0.4), (0.8, 0.6, 0.45), None, 1.25, bruiser_extras,
                               sole=(0.15, 0.12, 0.1), shape=BRUISER, sleeves="none"),
    "boss": lambda: fighter("boss", (0.12, 0.1, 0.1), (0.5, 0.1, 0.1), (0.1, 0.1, 0.12), (0.85, 0.66, 0.5), (0.05, 0.05, 0.05),
                            1.12, boss_extras, leather=True, sole=(0.1, 0.1, 0.1), shape={"chest": 1.1, "arms": 1.1, "waist": 1.08}),
}

only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
for k, f in FIGHTERS.items():
    if not only or k in only:
        f()
