"""Ingot Run (game 10) characters on the shared humanoid rig: the runner (a nimble explorer in a canvas cap with a
headlamp, a red scarf, a leather vest, a satchel, tall boots and a zapper bracer on each wrist) and the temple guard
(stocky, bronze crested helmet and pauldrons, a knee-length robe in material "team_main" that the game recolours).
Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/ingot_characters.py -- godot/games/ingot/art/models [runner guard]

Scale: one grid cell = 1 unit; both characters are about 0.92 units tall (the humanoid at SCALE = 0.48). Origin at
the feet: put it on the floor of the character's cell (cell centre - 0.5 in Z). The model faces -Y (the camera).
24 fps. Facing: turn the node to face +X / -X for run, bar and (optionally) hang and fall; keep it facing the camera
(yaw 0) for everything else: climb already shows the back (the rig turns itself round), dig_left / dig_right turn the
body toward the side they dig (screen left = -X, screen right = +X).

Animations (loops marked *):
  both:   idle*, run*, climb*, bar*, hang*, fall*, die, cheer*
  runner: dig_left, dig_right (the zap fires at frame 7 = 0.25 s; the wrist emitter points at the brick below-left /
          below-right, i.e. the top of the brick one cell over)
  guard:  trapped* (stuck in a hole: the legs stay still, the upper body flails), climb_out (hands on the rims, pulls
          up; the root rises exactly one cell during the clip: snap the node one cell up when it ends)
Speeds at speed_scale 1: run = RUN_CELLS cells per cycle (printed at export), climb and bar = 0.5 cell per cycle.
Ladder rungs are 0.25 apart (ingot_models.py), the ladder sits 0.15 behind the cell centre; a bar is gripped at
0.9 above the character's origin (the bar's axis at cell centre + 0.4).
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import humanoid
from humanoid import *

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
FPS = 24
SCALE = 0.48
SK = Skeleton(proportions())


def M(w):
    """World units (cells) to the rig's metres."""
    return w / SCALE


def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


# ------------------------------------------------------------------ a robe skirt that follows both thighs

_weights = humanoid.Skinner.weights


def _skirt_weights(self, p, region):
    """"~skirt": hangs from the hips and follows each thigh by its side (the middle splits between both), more
    so toward the hem, so a stride swings the robe instead of poking through it."""
    if region != "~skirt":
        return _weights(self, p, region)
    P_ = self.sk.P
    t = smoothstep(P_["hip_h"] + 0.06, P_["hip_h"] - 0.16, p.z)
    side = smoothstep(-0.07, 0.07, p.x)
    w = {"hips": 1.0 - t}
    if t > 0:
        w["thigh.L"] = t * side
        w["thigh.R"] = t * (1 - side)
    return {k: v for k, v in w.items() if v > 0}


humanoid.Skinner.weights = _skirt_weights


# ------------------------------------------------------------------ pose tools

SPINE = ("hips", "spine", "chest", "neck", "head")


def mirror(pose):
    """The same pose, left for right."""
    out = {}
    for k, v in pose.items():
        sw = k.replace(".L", ".#").replace(".R", ".L").replace(".#", ".R")
        if k in SPINE:
            out[k] = (v[0], -v[1], -v[2]) + tuple(v[3:])
        elif k == "root":
            out[k] = (-v[0], v[1], v[2])
        elif k == "turn":
            out[k] = (v[0], -v[1], -v[2])
        elif k.startswith("ik_foot") or k.startswith("ik_hand"):
            out[sw] = (-v[0],) + tuple(v[1:])
        elif k.startswith("hand_dir"):
            out[sw] = (-v[0], v[1], v[2])
        else:
            out[sw] = v
    return out


def mirror_anim(a):
    pole = a.arm_pole
    if isinstance(pole, dict):
        pole = {("R" if X == "L" else "L"): v for X, v in pole.items()}
    return Anim({f: mirror(k) for f, k in a.keys.items()}, loop=a.loop, arm_pole=pole)


def face_away(pose):
    """A pose written facing the camera (-Y), turned round to face +Y: the targets live in the armature's space,
    so they turn with the body."""
    out = dict(pose)
    t = pose.get("turn", (0, 0, 0))
    out["turn"] = (t[0], t[1] + 180, t[2])
    for k, v in pose.items():
        if k == "root":
            out[k] = (-v[0], -v[1], v[2])
        elif k.startswith("ik_foot"):
            out[k] = (-v[0], -v[1], v[2], v[3], v[4] + 180)
        elif k.startswith("ik_hand"):
            out[k] = (-v[0], -v[1], v[2])
        elif k.startswith("hand_dir"):
            out[k] = (v[0] + 180, v[1], v[2])
    return out


def cycle(frames, fn, step=2):
    """A looping Anim keyed every `step` frames from fn(phase in [0, 1))."""
    return {i + 1: fn(i / frames) for i in range(0, frames + 1, step)}


def ease(x):
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ actions

def stand(k=1.0):
    w = 0.11 * k
    return {"ik_foot.L": (w, 0.03, 0.09, 0, 10), "ik_foot.R": (-w, -0.03, 0.09, 0, 12), "ikw.L": 1.0, "ikw.R": 1.0}


def idle(st):
    heavy = st["heavy"]
    arms = st["arms"]

    def f(t):
        br = math.sin(2 * math.pi * t * 2)
        sway = math.sin(2 * math.pi * t)
        look = math.sin(2 * math.pi * (t - 0.1))
        p = P(stand(1.25 if heavy else 1.0), **{
            "root": (0.012 * sway, 0, -0.02 - (0.03 if heavy else 0) - 0.006 * br),
            "hips": (0, 3 * sway, -2 * sway), "spine": (2, 0, 0), "chest": (2 + 1.5 * br, -2 * sway, 0),
            "clavicle.L": (2, 0, 2 + 1.5 * br), "clavicle.R": (2, 0, 2 + 1.5 * br),
            "neck": (0, 10 * look, 0), "head": (-2 + (8 if heavy else 0), 16 * look, 2 * sway)})
        p.update(arms(br))
        return p
    return Anim(cycle(48, f, 4), loop=True)


def run(st):
    heavy = st["heavy"]
    if heavy:
        return gait(SK, 16, 2.1, 0.38, lift=0.2, lift_at=0.4, strike=10, push=35, bob=-0.035, drop=-0.08, lean=12,
                    arm_swing=34, arm_out=14, elbow=0, elbow_swing=16, pelvis_yaw=10, pelvis_roll=5, shoulder_yaw=10,
                    reach=0.42, width=0.13, base={"arm.L": (6, 0, 6), "arm.R": (6, 0, 6), "forearm.L": (78, 0, 0),
                                                   "forearm.R": (78, 0, 0), "head": (-8, 0, 0)})
    return gait(SK, 14, 2.3, 0.34, lift=0.3, lift_at=0.36, strike=10, push=45, bob=-0.035, drop=-0.07, lean=14,
                arm_swing=46, arm_out=8, elbow=0, elbow_swing=22, pelvis_yaw=11, pelvis_roll=4, shoulder_yaw=12,
                reach=0.42, base={"arm.L": (4, 0, 4), "arm.R": (4, 0, 4), "forearm.L": (82, 0, 0),
                                  "forearm.R": (82, 0, 0), "head": (-6, 0, 0)})


RUNG = M(0.25)          # rung spacing in rig metres
CLIMB_V = 2 * RUNG      # rise per cycle
LADDER_FWD = M(0.15)    # the rungs' distance in front of the climber


def limb_cycle(u, hold, v, top):
    """A hand or foot that grips at height `top` at u = 0, rides down with the body at speed v until u = hold,
    then lifts back to `top` (with a hump away from the ladder). Returns (height, clearance 0..1)."""
    if u < hold:
        return top - v * u, 0.0
    w = (u - hold) / (1 - hold)
    e = ease(w)
    return top - v * hold * (1 - e), math.sin(math.pi * w)


def climb(st):
    heavy = st["heavy"]

    def f(t):
        p = {"ikw.L": 1.0, "ikw.R": 1.0, "ikh.L": 1.0, "ikh.R": 1.0, "hdw.L": 1.0, "hdw.R": 1.0}
        for X, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            h, c = limb_cycle((t + off) % 1.0, 0.55, CLIMB_V, 1.72)
            p["ik_hand." + X] = (0.17 * s + 0.03 * c * s, LADDER_FWD - 0.03 - 0.12 * c, h + 0.03 * c)
            p["hand_dir." + X] = (-8 * s, 55 + 25 * c, 0)
            fh, fc = limb_cycle((t + off + 0.5) % 1.0, 0.45, CLIMB_V, 0.66)   # the other side's foot moves with this hand
            p["ik_foot." + X] = (0.13 * s, LADDER_FWD - 0.14 - 0.08 * fc, fh + 0.04 * fc, -10 + 25 * fc, 18)
        sw = math.sin(2 * math.pi * t)
        p.update({"root": (0.035 * sw, 0.02, 0.1 + 0.015 * math.cos(4 * math.pi * t)), "hips": (4, 4 * sw, -4 * sw),
                  "spine": (4, -2 * sw, 3 * sw), "chest": (4, -3 * sw, 2 * sw), "neck": (-6, 0, 0),
                  "head": (-10, 6 * sw, 0), "clavicle.L": (6, 0, 8 + 6 * sw), "clavicle.R": (6, 0, 8 - 6 * sw)})
        return face_away(p)
    return Anim(cycle(20, f, 1), loop=True, arm_pole={"L": (-1.0, -0.4, -0.5), "R": (-1.0, -0.4, -0.5)})


BAR_H = M(0.9)          # the bar's axis above the origin
BAR_V = M(0.5)          # travel per cycle


def hang_pose(t=0.0):
    sw = math.sin(2 * math.pi * t)
    return {"ikw.L": 0.0, "ikw.R": 0.0, "ikh.L": 1.0, "ikh.R": 1.0, "hdw.L": 1.0, "hdw.R": 1.0,
            "root": (0, 0.0, -0.3), "hips": (-2, 0, 0), "spine": (-3, 0, 0), "chest": (-4, 0, 0), "neck": (4, 0, 0),
            "head": (2, 0, 0), "clavicle.L": (0, 0, 24), "clavicle.R": (0, 0, 24),
            "thigh.L": (14 + 4 * sw, 0, 4), "shin.L": (48 + 6 * sw, 0, 0), "foot.L": (-30, 0, 0),
            "thigh.R": (6 - 4 * sw, 0, 4), "shin.R": (58 - 6 * sw, 0, 0), "foot.R": (-30, 0, 0)}


def bar(st):
    def f(t):
        p = hang_pose()
        sw = math.sin(2 * math.pi * t)
        for X, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            u = (t + off) % 1.0
            h, c = limb_cycle(u, 0.6, BAR_V, 0.34)      # here "height" is the reach along the bar
            p["ik_hand." + X] = (0.04 * s + 0.07 * c * s, h, BAR_H - 0.07 - 0.1 * c)
            p["hand_dir." + X] = (0, 78 - 30 * c, 0)
        p.update({"turn": (-6 * math.cos(4 * math.pi * t), 0, 0), "root": (0.02 * sw, 0.0, -0.3 + 0.015 * math.cos(4 * math.pi * t)),
                  "hips": (-2, 10 * sw, 0), "chest": (-4, -6 * sw, 0),
                  "thigh.L": (26 * sw + 12, 0, 4), "shin.L": (50 - 16 * sw, 0, 0),
                  "thigh.R": (-26 * sw + 12, 0, 4), "shin.R": (50 + 16 * sw, 0, 0),
                  "head": (4, -4 * sw, 0)})
        return p
    return Anim(cycle(16, f, 1), loop=True, arm_pole={"L": (1.0, 0.3, 0.2), "R": (1.0, 0.3, 0.2)})


def hang(st):
    def f(t):
        p = hang_pose(t)
        br = math.sin(2 * math.pi * t)
        look = math.sin(2 * math.pi * (t - 0.15))
        for X, s, fw in (("L", 1, 0.08), ("R", -1, -0.08)):
            p["ik_hand." + X] = (0.045 * s, fw, BAR_H - 0.07)
            p["hand_dir." + X] = (0, 80, 0)
        p.update({"root": (0, 0.0, -0.3 + 0.01 * br), "turn": (2 * br, 0, 0), "chest": (-4 + 2 * br, 0, 0),
                  "neck": (4, 14 * look, 0), "head": (2, 18 * look, 0)})
        return p
    return Anim(cycle(40, f, 4), loop=True, arm_pole={"L": (1.0, 0.3, 0.2), "R": (1.0, 0.3, 0.2)})


def fall(st):
    def f(t):
        a = 2 * math.pi * t
        s1, c1 = math.sin(a), math.cos(a)
        return {"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0, 0.05), "turn": (-4, 0, 3 * s1),
                "hips": (-4, 0, 0), "spine": (-8, 0, 0), "chest": (-8, 6 * s1, 0), "neck": (-6, 0, 0), "head": (-14, 8 * s1, 0),
                "clavicle.L": (0, 0, 22), "clavicle.R": (0, 0, 22),
                "arm.L": (150 + 14 * s1, 0, 36 + 12 * c1), "forearm.L": (30 - 15 * c1, 0, 0), "hand.L": (0, 0, 20),
                "arm.R": (150 - 14 * s1, 0, 36 - 12 * c1), "forearm.R": (30 + 15 * c1, 0, 0), "hand.R": (0, 0, 20),
                "thigh.L": (30 + 18 * s1, 0, 8), "shin.L": (60 - 20 * s1, 0, 0), "foot.L": (-25, 0, 0),
                "thigh.R": (22 - 18 * s1, 0, 8), "shin.R": (66 + 20 * s1, 0, 0), "foot.R": (-25, 0, 0)}
    return Anim(cycle(12, f, 1), loop=True)


def dig_left(st):
    """Dig to screen left (-X): turn right, lunge, the right bracer points down at the brick one cell over."""
    base = stand()
    ready = P(base, **{"root": (0, 0, -0.03), "arm.L": (6, 0, 10), "forearm.L": (40, 0, 0),
                       "arm.R": (6, 0, 10), "forearm.R": (40, 0, 0)})
    coil = P(base, **{"turn": (0, -30, 0), "root": (-0.06, 0.0, -0.14),
                      "ik_foot.L": (0.13, 0.08, 0.09, 0, 10), "ik_foot.R": (-0.24, -0.02, 0.09, 0, 40),
                      "hips": (10, -10, 0), "spine": (8, -8, -6), "chest": (6, -8, -6), "neck": (0, -10, 0), "head": (14, -14, 0),
                      "arm.R": (40, 0, 60), "forearm.R": (110, 0, 0), "hand.R": (-20, 0, 0),
                      "arm.L": (20, 0, 30), "forearm.L": (70, 0, 0)})
    zap = P(coil, **{"turn": (0, -44, 0), "root": (-0.14, 0.02, -0.26),
                     "ik_foot.R": (-0.34, -0.04, 0.09, 0, 50),
                     "hips": (22, -8, -4), "spine": (12, -6, -10), "chest": (8, -6, -8), "neck": (6, -6, 0), "head": (24, -10, 0),
                     "ikh.R": 1.0, "ik_hand.R": (-0.78, 0.12, 0.72), "hdw.R": 1.0, "hand_dir.R": (-82, -40, 0),
                     "arm.L": (-30, 0, 56), "forearm.L": (40, 0, 0), "clavicle.R": (14, 0, 4)})
    kick = P(zap, **{"root": (-0.1, 0.0, -0.22), "ik_hand.R": (-0.74, 0.1, 0.84), "hand_dir.R": (-82, -22, 0),
                     "chest": (2, -8, -6), "head": (14, -12, 0)})
    hold = P(zap, **{"root": (-0.12, 0.01, -0.24), "ik_hand.R": (-0.76, 0.11, 0.76), "hand_dir.R": (-82, -34, 0)})
    back = P(ready, **{"turn": (0, -10, 0), "root": (-0.03, 0, -0.06), "ik_foot.R": (-0.16, -0.03, 0.09, 0, 18),
                       "arm.R": (20, 0, 26), "forearm.R": (60, 0, 0)})
    return Anim({1: ready, 4: coil, 7: zap, 9: kick, 13: hold, 18: back, 22: ready},
                arm_pole={"R": (0.6, 0.6, -0.8), "L": (0.35, 1.0, -0.4)})


def die(st):
    heavy = st["heavy"]
    base = stand(1.25 if heavy else 1.0)
    jolt = P(base, **{"root": (0, -0.03, -0.02), "turn": (-6, 0, 0), "spine": (-8, 0, 0), "chest": (-12, 0, 0),
                      "neck": (-8, 0, 0), "head": (-22, 0, 0), "clavicle.L": (0, 0, 20), "clavicle.R": (0, 0, 20),
                      "arm.L": (40, 0, 60), "forearm.L": (70, 0, 0), "arm.R": (40, 0, 60), "forearm.R": (70, 0, 0)})
    kneel = {"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0.05, -0.5), "turn": (0, 0, 0), "hips": (-6, 0, 0),
             "thigh.L": (8, 0, 8), "shin.L": (110, 0, 0), "foot.L": (-50, 0, 0),
             "thigh.R": (4, 0, 8), "shin.R": (104, 0, 0), "foot.R": (-50, 0, 0),
             "spine": (18, 0, 0), "chest": (16, 0, 0), "neck": (14, 0, 0), "head": (16, 0, 0),
             "arm.L": (30, 0, 10), "forearm.L": (40, 0, 0), "arm.R": (26, 0, 10), "forearm.R": (40, 0, 0)}
    slump = P(kneel, **{"turn": (8, 0, 50), "root": (0.45, 0.05, -0.3), "spine": (24, 0, 6), "chest": (18, 0, 8),
                        "head": (10, 30, 10), "arm.L": (70, 0, 40), "forearm.L": (60, 0, 0),
                        "arm.R": (100, 0, 20), "forearm.R": (30, 0, 0),
                        "thigh.L": (60, 0, 6), "shin.L": (110, 0, 0), "thigh.R": (40, 0, 4), "shin.R": (100, 0, 0)})
    down = P(slump, **{"turn": (6, 0, 88), "root": (1.15, 0.05, 0.14), "spine": (22, 0, 6), "chest": (14, 0, 6),
                       "neck": (6, 0, 6), "head": (0, 40, 14), "arm.L": (80, 0, 30), "forearm.L": (50, 0, 0),
                       "arm.R": (110, 0, 20), "forearm.R": (20, 0, 0), "thigh.L": (70, 0, 4), "shin.L": (100, 0, 0),
                       "thigh.R": (50, 0, 0), "shin.R": (90, 0, 0), "foot.L": (-30, 0, 0), "foot.R": (-30, 0, 0)})
    settle = P(down, **{"turn": (6, 0, 90), "root": (1.18, 0.05, 0.12), "head": (0, 44, 16)})
    return Anim({1: base, 3: jolt, 6: P(jolt, **{"head": (-10, 0, 0), "chest": (-6, 0, 0)}),
                 11: P(kneel, **{"root": (0, 0.05, -0.46)}), 14: kneel, 19: slump, 23: down, 26: settle, 32: settle})


def cheer(st):
    heavy = st["heavy"]

    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a * 2)) ** 1.5
        pump = math.sin(a)
        up = 0.06 if heavy else 0.1
        p = P(stand(1.25 if heavy else 1.0), **{
            "root": (0, 0, -0.06 + up * hop - 0.05 * max(0.0, -math.sin(a * 2))),
            "spine": (-4, 6 * pump, 0), "chest": (-6, 8 * pump, 0), "neck": (-6, 0, 0), "head": (-12, -6 * pump, 0),
            "clavicle.L": (0, 0, 16 + 8 * max(0, pump)), "clavicle.R": (0, 0, 16 + 8 * max(0, -pump)),
            "arm.L": (150 + 20 * max(0, pump), 0, 30), "forearm.L": (20 + 60 * max(0, -pump), 0, 0),
            "arm.R": (150 + 20 * max(0, -pump), 0, 30), "forearm.R": (20 + 60 * max(0, pump), 0, 0),
            "hand.L": (0, 0, 10), "hand.R": (0, 0, 10)})
        for X in "LR":
            v = p["ik_foot." + X]
            p["ik_foot." + X] = (v[0], v[1], v[2] + up * hop * 0.8, -10 * hop, v[4])
        return p
    return Anim(cycle(24, f, 1), loop=True)


def trapped(st):
    """Stuck in a hole: legs still (the rim hides them), the upper body struggles and the arms flail overhead."""
    def f(t):
        a = 2 * math.pi * t
        s1, s2 = math.sin(a), math.sin(2 * a)
        p = P(stand(1.25), **{"root": (0.03 * s1, 0, -0.1 + 0.02 * s2), "hips": (6, 8 * s1, 0),
                              "spine": (4, 10 * s1, 4 * s1), "chest": (-6, 14 * s1, 6 * s1), "neck": (-6, -10 * s1, 0),
                              "head": (-14, -16 * s1, 6 * s1), "clavicle.L": (0, 0, 20 + 10 * s2), "clavicle.R": (0, 0, 20 - 10 * s2),
                              "arm.L": (120 + 40 * s1, 0, 50 + 20 * math.cos(a)), "forearm.L": (50 + 30 * s2, 0, 0),
                              "arm.R": (120 - 40 * s1, 0, 50 - 20 * math.cos(a)), "forearm.R": (50 - 30 * s2, 0, 0),
                              "hand.L": (0, 0, 20 * s2), "hand.R": (0, 0, -20 * s2)})
        return p
    return Anim(cycle(16, f, 1), loop=True)


def climb_out(st):
    """From the hole to the floor above: grab both rims, heave, a knee up, stand one cell higher."""
    rise = M(1.0)
    rim = rise + 0.06
    trap = trapped(st).keys[1]
    grab = P(stand(1.25), **{"root": (0, 0, -0.14), "ikh.L": 1.0, "ikh.R": 1.0, "hdw.L": 1.0, "hdw.R": 1.0,
                             "ik_hand.L": (0.62, 0.0, rim), "ik_hand.R": (-0.62, 0.0, rim),
                             "hand_dir.L": (90, 10, 0), "hand_dir.R": (-90, 10, 0), "spine": (-2, 0, 0),
                             "chest": (-6, 0, 0), "head": (-18, 0, 0), "clavicle.L": (0, 0, 24), "clavicle.R": (0, 0, 24)})
    heave = P(grab, **{"root": (0, 0.0, 0.62), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (30, 0, 10), "shin.L": (70, 0, 0),
                       "thigh.R": (20, 0, 10), "shin.R": (60, 0, 0), "foot.L": (-30, 0, 0), "foot.R": (-30, 0, 0),
                       "chest": (10, 0, 0), "head": (-6, 0, 0), "hand_dir.L": (90, -30, 0), "hand_dir.R": (-90, -30, 0)})
    knee = P(heave, **{"root": (0, -0.06, 1.3), "hips": (20, 0, 0), "spine": (24, 0, 0), "chest": (16, 0, 0),
                       "thigh.L": (100, 0, 16), "shin.L": (120, 0, 0), "thigh.R": (10, 0, 6), "shin.R": (40, 0, 0),
                       "ik_hand.L": (0.5, 0.0, rim - 0.04), "ik_hand.R": (-0.5, 0.0, rim - 0.04),
                       "hand_dir.L": (90, -60, 0), "hand_dir.R": (-90, -60, 0)})
    top = stand(1.25)
    top = {k: ((v[0], v[1], v[2] + rise) + tuple(v[3:]) if k.startswith("ik_foot") else v) for k, v in top.items()}
    push = P(top, **{"root": (0, 0.0, rise - 0.3), "hips": (26, 0, 0), "spine": (20, 0, 0), "chest": (10, 0, 0),
                     "head": (-10, 0, 0), "ikh.L": 0.6, "ikh.R": 0.6, "ik_hand.L": (0.36, -0.1, rise + 0.3),
                     "ik_hand.R": (-0.36, -0.1, rise + 0.3), "arm.L": (20, 0, 20), "arm.R": (20, 0, 20),
                     "forearm.L": (60, 0, 0), "forearm.R": (60, 0, 0)})
    done = P(top, **{"root": (0, 0, rise - 0.03), "arm.L": (4, 0, 10), "arm.R": (4, 0, 10), "forearm.L": (40, 0, 0),
                     "forearm.R": (40, 0, 0), "head": (6, 0, 0)})
    pole = {"L": (0.8, 0.4, -0.3), "R": (0.8, 0.4, -0.3)}
    return Anim({1: trap, 4: grab, 9: heave, 13: knee, 17: push, 22: done}, arm_pole=pole)


def slim(material, ratio=None, bone=None, delete=False):
    """Trims the builder's parts of one material (and binding): decimates them, or deletes them where the outfit
    hides them."""
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        if o.data.materials[0] is not material or (bone and o["bone"] != bone):
            continue
        if delete:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        humanoid._select_only(o)
        m = o.modifiers.new("d", "DECIMATE")
        m.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.ops.object.shade_smooth()


def actions(st, kind):
    a = {"idle": idle(st), "run": run(st), "climb": climb(st), "bar": bar(st), "hang": hang(st), "fall": fall(st),
         "die": die(st), "cheer": cheer(st)}
    if kind == "runner":
        dl = dig_left(st)
        a["dig_left"] = dl
        a["dig_right"] = mirror_anim(dl)
    else:
        a["trapped"] = trapped(st)
        a["climb_out"] = climb_out(st)
    return a


# ------------------------------------------------------------------ the runner

H = (0, -0.012, 1.675)   # head centre


def runner_arms(br):
    return {"arm.L": (4, 0, 8), "forearm.L": (26 + 2 * br, 0, 0), "hand.L": (0, 0, -6),
            "arm.R": (6, 0, 8), "forearm.R": (30 - 2 * br, 0, 0), "hand.R": (0, 0, -6)}


def bracer(X, brass, leather, lens):
    s = 1 if X == "L" else -1
    tube(arm_path(SK, X, 0.012, 0.72, 0.98), "~arm." + X, leather, 12, 0.016, lateral=(s, 0, 0))
    # the zapper: a brass barrel along the back of the wrist, the glowing lens at its muzzle
    fr = bone_frame(SK, "forearm." + X)
    L = SK.tail("forearm." + X) - SK.head("forearm." + X)
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.022, depth=0.11, location=(0, L.length * 0.82, 0.042),
                                        rotation=(math.pi / 2, 0, 0))
    parts.append(tag(active(), "forearm." + X, brass))
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.027, depth=0.018, location=(0, L.length * 0.92, 0.042),
                                        rotation=(math.pi / 2, 0, 0))
    parts.append(tag(active(), "forearm." + X, brass))
    parts.append(sphere(0.017, (0, L.length * 0.93, 0.042), "forearm." + X, lens, (1, 0.7, 1), 12, 8))
    parts.append(box((0.05, 0.05, 0.02), (0, L.length * 0.78, 0.022), "forearm." + X, brass, bevel=0.006))
    place(parts, fr)


def runner():
    clear()
    skin = mat("runner_skin", (0.86, 0.62, 0.46), 0.5)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("runner_iris", (0.25, 0.16, 0.08), 0.2)
    shirt = mat("runner_shirt", (0.08, 0.36, 0.42), 0.75)
    trousers = mat("runner_trousers", (0.5, 0.42, 0.28), 0.85)
    boots = mat("runner_boots", (0.22, 0.12, 0.06), 0.5, coat=0.3)
    sole = mat("runner_sole", (0.08, 0.06, 0.05), 0.7)
    glove = mat("runner_gloves", (0.36, 0.22, 0.12), 0.55)
    vest = mat("runner_vest", (0.4, 0.23, 0.1), 0.45, coat=0.35)
    scarf = mat("runner_scarf", (0.78, 0.14, 0.08), 0.8)
    canvas = mat("runner_cap", (0.44, 0.36, 0.2), 0.85)
    hair = mat("runner_hair", (0.22, 0.12, 0.06), 0.6, coat=0.2)
    brass = mat("brass", (0.86, 0.62, 0.28), 0.3, 0.9)
    strap = mat("runner_strap", (0.2, 0.12, 0.06), 0.6)
    lamp = mat("headlamp", (1.0, 0.86, 0.55), 0.2)
    lamp.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.8, 0.45, 1)
    lamp.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 6.0
    lens = mat("zapper_lens", (0.4, 0.95, 1.0), 0.2)
    lens.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.35, 0.9, 1.0, 1)
    lens.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 5.0
    sh = {"chest": 0.98, "waist": 0.94, "hips": 0.96, "arms": 0.96, "legs": 1.0, "neck": 1.0, "hand": 1.08}
    human_body(SK, skin, shirt, trousers, white, iris, shoes=boots, sole=sole, glove=glove, sleeves="long",
               hands="grip", shape=sh, head=False, shoe_height=0.3)
    slim(boots, 0.55)
    slim(trousers, 0.6, bone="~body")
    head_detailed(skin, white, iris, center=H, hair=None, size=1.1)
    cx, cy, cz = H
    k = 1.1
    sphere(0.106 * k, (0, cy + 0.024, cz + 0.035), "head", hair, (0.93, 1.0, 0.86), 20, 10)   # short hair
    # the cap: a soft canvas crown, a band and a short brim, the brass headlamp on the front
    sphere(0.108 * k, (0, cy + 0.012, cz + 0.07), "head", canvas, (1.0, 1.04, 0.66), 24, 12)
    body_loft([(cz + 0.045, 0.108 * k, 0.114 * k, cy + 0.01), (cz + 0.078, 0.106 * k, 0.112 * k, cy + 0.01)],
              "head", strap, 24, 0)
    box((0.19, 0.11, 0.016), (0, cy - 0.15, cz + 0.05), "head", canvas, rot=(-0.22, 0, 0), bevel=0.007)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.034, depth=0.045, location=(0, cy - 0.13, cz + 0.1),
                                        rotation=(math.pi / 2 - 0.25, 0, 0))
    tag(active(), "head", brass)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.027, depth=0.01, location=(0, cy - 0.154, cz + 0.094),
                                        rotation=(math.pi / 2 - 0.25, 0, 0))
    tag(active(), "head", lamp)
    # the scarf: a knotted roll round the neck and a tail over the left shoulder, down the back
    tube([(0.0, -0.075, 1.475, 0.03), (0.07, -0.05, 1.48, 0.032), (0.085, 0.02, 1.49, 0.032), (0.05, 0.07, 1.5, 0.03),
          (-0.02, 0.075, 1.5, 0.03), (-0.08, 0.03, 1.49, 0.032), (-0.07, -0.05, 1.48, 0.032), (0.0, -0.078, 1.475, 0.03)],
         "~body", scarf, 10, 0.03)
    sphere(0.035, (0.02, -0.085, 1.465), "~body", scarf, (1.2, 0.8, 1.0), 12, 7)
    tube([(0.03, -0.09, 1.45, 0.024), (0.045, -0.11, 1.38, 0.022), (0.05, -0.115, 1.3, 0.02)], "~body", scarf, 10, 0.02,
         ell=(1.6, 0.5))
    tube([(-0.02, 0.09, 1.47, 0.024), (-0.06, 0.12, 1.4, 0.024), (-0.09, 0.14, 1.31, 0.022)], "~body", scarf, 10, 0.02,
         ell=(1.6, 0.5))
    # the vest: an open shell over the shirt, with a collar
    g = 0.012
    rings = [(z, rx + g, ry + g, cy_) for z, rx, ry, cy_, sq in torso_rings(1.0, 1.43, 0.0, sh)]
    shell(rings, -70, 250, "~body", vest, 0.009, 20, 0)
    # a belt with a brass buckle; the satchel on the right hip on a strap from the left shoulder
    body_loft([(z, rx + 0.008, ry + 0.008, cy_, sq) for z, rx, ry, cy_, sq in torso_rings(0.99, 1.05, 0.0, sh)],
              "~body", strap, 26, 0)
    box((0.05, 0.02, 0.04), (0, -0.1, 1.02), "~body", brass, bevel=0.006)
    box((0.07, 0.19, 0.16), (-0.2, 0.0, 0.93), "~body", canvas, bevel=0.03)
    box((0.075, 0.2, 0.07), (-0.2, 0.0, 1.0), "~body", vest, rot=(0, 0, 0), bevel=0.02)
    box((0.02, 0.02, 0.03), (-0.24, 0.0, 0.97), "~body", brass, bevel=0.005)
    rings = torso_rings(1.0, 1.43, 0.0, sh)
    pts_f, pts_b = [], []
    for z, rx, ry, cy_, sq in rings:
        u = (z - 1.0) / 0.43
        x = -0.17 + 0.28 * u
        pts_f.append((x, -(ry + 0.02) + cy_, z, 0.014))
        pts_b.append((x, (ry + 0.02) + cy_, z, 0.014))
    tube(pts_f, "~body", strap, 6, 0.03, ell=(1.5, 0.45))
    tube(pts_b, "~body", strap, 6, 0.03, ell=(1.5, 0.45))
    # boot cuffs and knee patches
    for X, s in (("L", 1), ("R", -1)):
        x = SK.head("foot." + X).x
        body_loft([(0.29, 0.056, 0.064, 0.004), (0.33, 0.058, 0.066, 0.004)], "~foot." + X, boots, 20, 0, x0=x)
        bracer(X, brass, glove, lens)
    rig_export("runner", out_dir, actions({"heavy": False, "arms": runner_arms}, "runner"), SCALE, skeleton=SK, fps=FPS)


# ------------------------------------------------------------------ the guard

GUARD_SHAPE = {"chest": 1.12, "waist": 1.2, "hips": 1.1, "arms": 1.16, "legs": 1.1, "neck": 1.25, "hand": 1.12}


def guard_arms(br):
    return {"arm.L": (6, 0, 16), "forearm.L": (30 + 2 * br, 0, 0), "arm.R": (6, 0, 16), "forearm.R": (30 - 2 * br, 0, 0)}


def guard():
    clear()
    sh = GUARD_SHAPE
    skin = mat("guard_skin", (0.66, 0.44, 0.3), 0.55)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("guard_iris", (0.12, 0.08, 0.05), 0.2)
    robe = mat("team_main", (0.62, 0.11, 0.08), 0.7)
    under = mat("guard_trousers", (0.3, 0.24, 0.17), 0.9)
    boots = mat("guard_boots", (0.16, 0.1, 0.06), 0.55, coat=0.2)
    bronze = mat("bronze", (0.72, 0.46, 0.2), 0.32, 0.9)
    dark_bronze = mat("bronze_dark", (0.36, 0.22, 0.1), 0.4, 0.85)
    sash = mat("guard_sash", (0.12, 0.08, 0.06), 0.6)
    gold = mat("guard_gold", (0.95, 0.74, 0.3), 0.25, 1.0)
    plume = mat("guard_plume", (0.1, 0.07, 0.06), 0.8)
    brow = mat("guard_brow", (0.08, 0.05, 0.04), 0.7)
    human_body(SK, skin, robe, under, white, iris, shoes=boots, sole=boots, glove=skin, sleeves="long", hands="fist",
               shape=sh, head=False, shoe_height=0.24)
    slim(under, bone="~body", delete=True)     # the hips under the skirt
    k = 1.08
    head_detailed(skin, white, iris, center=H, hair=None, size=k, brow=brow)
    cx, cy, cz = H
    # the helmet: a bronze dome, a band, cheek guards, a nose guard, a crest with a dark plume
    sphere(0.116 * k, (0, cy + 0.012, cz + 0.06), "head", bronze, (0.98, 1.05, 0.84), 24, 12)
    body_loft([(cz + 0.04, 0.119 * k, 0.126 * k, cy + 0.012), (cz + 0.075, 0.119 * k, 0.126 * k, cy + 0.012)], "head",
              dark_bronze, 24, 0)
    for s in (-1, 1):
        box((0.02, 0.07, 0.1), (0.108 * k * s, cy - 0.025, cz - 0.045), "head", bronze, rot=(0.1, 0, -0.12 * s), bevel=0.008)
    box((0.02, 0.018, 0.07), (0, cy - 0.136, cz + 0.02), "head", bronze, bevel=0.006)
    box((0.03, 0.2, 0.05), (0, cy + 0.012, cz + 0.16), "head", dark_bronze, bevel=0.012)
    for i in range(5):
        a = -0.6 + i * 0.3
        y = cy + 0.03 + math.sin(a) * 0.12
        z = cz + 0.15 + math.cos(a) * 0.06
        sphere(0.04, (0, y, z), "head", plume, (0.5, 1.1, 1.3 - abs(a) * 0.3), 10, 7)
    # the robe: the skirt from the hips to the knee, flaring; a hem band; a sash with a gold disc
    rings = []
    for z, rx, ry in ((0.99, 0.18, 0.115), (0.9, 0.2, 0.13), (0.8, 0.215, 0.145), (0.68, 0.23, 0.165), (0.56, 0.245, 0.18)):
        rings.append((z, rx * sh["hips"], ry * sh["hips"], 0.0, 2.3))
    body_loft(list(reversed(rings)), "~skirt", robe, 24, 0, step=0.03)
    z0, rx0, ry0 = rings[-1][0], rings[-1][1], rings[-1][2]
    body_loft([(z0 - 0.005, rx0 + 0.008, ry0 + 0.008, 0.0, 2.3), (z0 + 0.04, rx0 - 0.006, ry0 - 0.004, 0.0, 2.3)],
              "~skirt", gold, 24, 0)
    body_loft([(z, rx + 0.014, ry + 0.014, cy_, sq) for z, rx, ry, cy_, sq in torso_rings(0.98, 1.08, 0.0, sh)], "~body", sash, 26, 0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.05, depth=0.02, location=(0, -0.135, 1.03), rotation=(math.pi / 2, 0, 0))
    tag(active(), "~body", gold)
    # a gold-trimmed collar, pauldrons and bracers
    shell([(1.43, 0.15, 0.1, 0.008), (1.47, 0.12, 0.09, 0.012), (1.5, 0.1, 0.085, 0.014)], -90, 270, "~body", gold, 0.01, 22, 0)
    for X, s in (("L", 1), ("R", -1)):
        shp = SK.head("arm." + X)
        sphere(0.085, tuple(shp + Vector((0.03 * s, 0.0, 0.0))), "arm." + X, bronze, (1.05, 1.15, 0.75), 20, 10)
        sphere(0.07, tuple(shp + Vector((0.045 * s, 0.0, -0.05))), "arm." + X, dark_bronze, (1.0, 1.1, 0.7), 18, 9)
        tube(arm_path(SK, X, 0.014, 0.7, 0.98, shape=sh["arms"]), "~arm." + X, bronze, 12, 0.016, lateral=(s, 0, 0))
    rig_export("guard", out_dir, actions({"heavy": True, "arms": guard_arms}, "guard"), SCALE, skeleton=SK, fps=FPS)


CHARS = {"runner": runner, "guard": guard}
if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
    for k_, f_ in CHARS.items():
        if not only or k_ in only:
            f_()
    print("RUN_CELLS runner %.3f per 14 frames, guard %.3f per 16 frames" % (2.3 * SCALE, 2.1 * SCALE))
