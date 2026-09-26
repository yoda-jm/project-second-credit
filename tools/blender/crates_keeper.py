"""Crate Keeper (game 11) character on the shared humanoid rig: the warehouse keeper, a friendly stocky dock worker in
a flat cap, a chambray shirt with rolled sleeves, a red neckerchief, a canvas apron and work boots, with a bushy
moustache. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/crates_keeper.py -- godot/games/crates/art/models

Scale: one grid cell = 1 unit; the keeper is about 0.9 units tall (the humanoid at SCALE = 0.48). Origin at the feet,
on the floor at the centre of his cell. The model faces -Y: turn the node (yaw) to face the move direction.
24 fps. Animations (loops marked *):
  idle*   breathing, a look left and right (3 s)
  walk*   a brisk trot: WALK_CELLS cells per 10-frame cycle at speed_scale 1 (printed at export); one step per cell
  push*   leaning into a crate with both hands, stepping: PUSH_CELLS per 12-frame cycle. The palms rest on the face of a
          crate in the next cell (0.86 wide, its face 0.57 cells ahead of the keeper's origin): keep the keeper at his
          own cell's centre and the crate at the next one's while both slide
  bump    one-shot (1 s): shoves a crate that won't move, strains, gives up with a shake of the head; ends in the idle
          stance (blend to idle)
  cheer*  fist pumps and hops (1 s)
  undo    one-shot (0.42 s): a quick shrug, palms up, a glance back over the shoulder
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import humanoid
from humanoid import *

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
FPS = 24
SCALE = 0.48
SK = Skeleton(proportions(sh_w=0.205, hip_w=0.108))
SHAPE = {"chest": 1.34, "waist": 1.42, "hips": 1.26, "arms": 1.42, "legs": 1.3, "neck": 1.4, "hand": 1.3}
HEAD = 1.32             # a slightly big, friendly head
H = (0, -0.018, 1.71)   # head centre


def M(w):
    """World units (cells) to the rig's metres."""
    return w / SCALE


def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


# ------------------------------------------------------------------ an apron panel that follows both thighs

_weights = humanoid.Skinner.weights


def _skirt_weights(self, p, region):
    """"~skirt": hangs from the hips and follows each thigh by its side (the middle splits between both), more
    so toward the hem, so a stride swings the apron instead of poking through it."""
    if region != "~skirt":
        return _weights(self, p, region)
    P_ = self.sk.P
    t = smoothstep(P_["hip_h"] + 0.06, P_["hip_h"] - 0.2, p.z)
    side = smoothstep(-0.08, 0.08, p.x)
    w = {"hips": 1.0 - t}
    if t > 0:
        w["thigh.L"] = t * side
        w["thigh.R"] = t * (1 - side)
    return {k: v for k, v in w.items() if v > 0}


humanoid.Skinner.weights = _skirt_weights


# ------------------------------------------------------------------ poses

def cycle(frames, fn, step=2):
    """A looping Anim keyed every `step` frames from fn(phase in [0, 1))."""
    return {i + 1: fn(i / frames) for i in range(0, frames + 1, step)}


def stand(w=0.13):
    return {"ik_foot.L": (w, 0.02, 0.09, 0, 12), "ik_foot.R": (-w, -0.02, 0.09, 0, 14), "ikw.L": 1.0, "ikw.R": 1.0}


def arms_rest(br=0.0):
    """Stocky arms hang a little out, clear of the belly."""
    return {"clavicle.L": (2, 0, 2 + 1.5 * br), "clavicle.R": (2, 0, 2 + 1.5 * br),
            "arm.L": (4, 0, 14), "forearm.L": (24 + 2 * br, 0, 0), "hand.L": (0, 0, -4),
            "arm.R": (6, 0, 14), "forearm.R": (28 - 2 * br, 0, 0), "hand.R": (0, 0, -4)}


STAND = P(stand(), **{"root": (0, 0, -0.03), "spine": (2, 0, 0), "chest": (1, 0, 0), "head": (-2, 0, 0)}, **arms_rest())


def idle():
    def f(t):
        br = math.sin(2 * math.pi * t * 3)           # three breaths a loop
        sway = math.sin(2 * math.pi * t)
        # a look to his left, back, a look to his right, back
        look = math.sin(2 * math.pi * t) ** 3
        tilt = math.sin(4 * math.pi * t)
        p = P(STAND, **{"root": (0.012 * sway, 0, -0.03 - 0.006 * br), "hips": (0, 3 * sway, -2 * sway),
                        "spine": (2, -1 * sway, 0), "chest": (1 + 1.5 * br, -2 * sway + 4 * look, 0),
                        "neck": (0, 12 * look, 0), "head": (-2 - 2 * br, 22 * look, 4 * tilt * abs(look))})
        p.update(arms_rest(br))
        return p
    return Anim(cycle(72, f, 3), loop=True)


WALK_FRAMES, WALK_STRIDE = 10, 3.2
PUSH_FRAMES, PUSH_STRIDE = 12, 1.6


def walk():
    return gait(SK, WALK_FRAMES, WALK_STRIDE, 0.4, lift=0.24, lift_at=0.38, strike=12, push=38, bob=-0.03, drop=-0.06,
                lean=9, width=0.14, arm_swing=34, arm_out=16, elbow=0, elbow_swing=18, pelvis_yaw=9, pelvis_roll=5,
                shoulder_yaw=9, reach=0.45, sway=0.02, step=1,
                base={"arm.L": (4, 0, 4), "arm.R": (4, 0, 4), "forearm.L": (70, 0, 0), "forearm.R": (70, 0, 0),
                      "head": (-4, 0, 0)})


CRATE_FACE = M(0.57)    # the near face of a crate in the next cell
HAND_H = M(0.44)        # where the palms press


PUSH_FWD = 0.3          # the hips ride this far ahead of the origin (rig metres)


def push_hands(pose, shove=0.0, spread=0.2):
    p = dict(pose)
    p.update({"ikh.L": 1.0, "ikh.R": 1.0, "hdw.L": 1.0, "hdw.R": 1.0,
              "ik_hand.L": (spread, CRATE_FACE - 0.07 + shove, HAND_H), "ik_hand.R": (-spread, CRATE_FACE - 0.07 + shove, HAND_H),
              "hand_dir.L": (-10, 62, 90), "hand_dir.R": (10, 62, 90)})
    return p


PUSH_POLE = {"L": (1.0, 0.2, -0.9), "R": (1.0, 0.2, -0.9)}


def push():
    base = {"turn": (14, 0, 0), "hips": (12, 0, 0), "spine": (14, 0, 0), "chest": (8, 0, 0), "neck": (-14, 0, 0),
            "head": (-20, 0, 0), "clavicle.L": (14, 0, 6), "clavicle.R": (14, 0, 6)}

    def extra(ph, pose):
        return push_hands(pose)
    a = gait(SK, PUSH_FRAMES, PUSH_STRIDE, 0.62, lift=0.12, lift_at=0.45, strike=8, push=40, bob=0.012, drop=-0.06,
             lean=10, width=0.15, arm_swing=0, arm_out=0, elbow=0, elbow_swing=0, pelvis_yaw=7, pelvis_roll=5,
             shoulder_yaw=-4, reach=0.3, sway=0.02, step=1, base=base, extra=extra)
    for k in a.keys.values():
        r = k["root"]
        k["root"] = (r[0], r[1] + PUSH_FWD, r[2])
        for X in "LR":
            v = k["ik_foot." + X]
            k["ik_foot." + X] = (v[0], v[1] + PUSH_FWD) + tuple(v[2:])
    a.arm_pole = PUSH_POLE
    return a


def push_pose(shove=0.0, crouch=0.0, lean=0.0):
    """A standing push (both feet down, the right one back) for the bump."""
    p = {"ik_foot.L": (0.15, PUSH_FWD + 0.12, 0.09, 0, 8), "ik_foot.R": (-0.15, PUSH_FWD - 0.42, 0.09 + 0.02, -18, 10),
         "ikw.L": 1.0, "ikw.R": 1.0, "toe.R": (18, 0, 0),
         "root": (0, PUSH_FWD + shove, -0.1 - crouch), "turn": (14 + lean, 0, 0), "hips": (12, 0, 0),
         "spine": (14 + lean * 0.5, 0, 0), "chest": (8, 0, 0), "neck": (-14 - lean, 0, 0), "head": (-20, 0, 0),
         "clavicle.L": (14, 0, 6), "clavicle.R": (14, 0, 6)}
    return push_hands(p, shove * 0.4)


def bump():
    """Shoves a stuck crate twice, strains (a tremble), gives up: steps back, shakes his head, back to the stance."""
    a0 = push_pose()
    shove = push_pose(0.1, 0.02, 4)
    strain = push_pose(0.12, 0.05, 6)
    strain2 = P(strain, **{"root": (0.012, PUSH_FWD + 0.12, -0.15), "head": (-26, 4, 3)})
    strain3 = P(strain, **{"root": (-0.012, PUSH_FWD + 0.11, -0.15), "head": (-24, -4, -3)})
    slip = P(push_pose(-0.02, 0.0, -2), **{"head": (-10, 0, 0)})
    back = P(STAND, **{"root": (0, 0.04, -0.06), "spine": (6, 0, 0), "chest": (4, 0, 0), "neck": (4, 0, 0),
                       "head": (10, 0, 0), "ik_foot.L": (0.13, 0.06, 0.09, 0, 12)})
    shake = P(back, **{"head": (12, 20, 4), "neck": (6, 8, 0), "arm.L": (8, 0, 22), "arm.R": (8, 0, 22),
                       "forearm.L": (40, 0, 0), "forearm.R": (40, 0, 0), "hand.L": (0, 0, 20), "hand.R": (0, 0, 20)})
    shake2 = P(shake, **{"head": (12, -20, -4), "neck": (6, -8, 0)})
    keys = {1: a0, 4: shove, 7: strain2, 9: strain3, 11: strain2, 13: slip, 16: strain, 18: strain3,
            21: P(STAND, **{"root": (0, 0.12, -0.08), "spine": (8, 0, 0), "head": (6, 0, 0)}),
            24: back, 26: shake, 28: shake2, 30: shake, 32: P(back, **{"head": (6, 0, 0)}), 36: STAND}
    # the hands drop off the crate after the second strain
    for f in (21, 24, 26, 28, 30, 32, 36):
        keys[f] = P(keys[f], **{"ikh.L": 0.0, "ikh.R": 0.0, "hdw.L": 0.0, "hdw.R": 0.0})
    return Anim(keys, arm_pole=PUSH_POLE)


def cheer():
    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a * 2)) ** 1.5
        pump = math.sin(a)
        up = 0.09
        p = P(stand(0.14), **{
            "root": (0, 0, -0.06 + up * hop - 0.05 * max(0.0, -math.sin(a * 2))),
            "spine": (-4, 6 * pump, 0), "chest": (-6, 8 * pump, 0), "neck": (-6, 0, 0), "head": (-14, -6 * pump, 0),
            "clavicle.L": (0, 0, 16 + 8 * max(0, pump)), "clavicle.R": (0, 0, 16 + 8 * max(0, -pump)),
            "arm.L": (150 + 20 * max(0, pump), 0, 34), "forearm.L": (20 + 60 * max(0, -pump), 0, 0),
            "arm.R": (150 + 20 * max(0, -pump), 0, 34), "forearm.R": (20 + 60 * max(0, pump), 0, 0),
            "hand.L": (0, 0, 10), "hand.R": (0, 0, 10)})
        for X in "LR":
            v = p["ik_foot." + X]
            p["ik_foot." + X] = (v[0], v[1], v[2] + up * hop * 0.8, -10 * hop, v[4])
        return p
    return Anim(cycle(24, f, 1), loop=True)


def undo():
    """A quick shrug: shoulders up, forearms out with the palms up, a glance back over the shoulder."""
    shrug = P(STAND, **{"root": (0, 0.02, -0.02), "clavicle.L": (0, 0, 22), "clavicle.R": (0, 0, 22),
                        "arm.L": (10, -30, 26), "arm.R": (10, -30, 26), "forearm.L": (80, 0, 0), "forearm.R": (80, 0, 0),
                        "hand.L": (0, 0, -30), "hand.R": (0, 0, -30), "chest": (-2, 10, 0), "neck": (0, 16, 0),
                        "head": (-4, 30, 10), "spine": (0, 6, 0)})
    return Anim({1: STAND, 4: shrug, 7: P(shrug, **{"head": (-2, 26, 8)}), 11: STAND})


def actions():
    return {"idle": idle(), "walk": walk(), "push": push(), "bump": bump(), "cheer": cheer(), "undo": undo()}


# ------------------------------------------------------------------ the keeper

def slim(material, ratio=None, bone=None, delete=False):
    """Decimates the builder's parts of one material (and binding), or deletes them where the outfit hides them."""
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


def rotated(o, rot):
    o.rotation_euler = rot
    humanoid._select_only(o)
    bpy.ops.object.transform_apply(rotation=True)
    return o


def keeper():
    clear()
    sh = SHAPE
    skin = mat("keeper_skin", (0.84, 0.58, 0.44), 0.5)
    cheek = mat("keeper_cheek", (0.86, 0.46, 0.38), 0.5)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("keeper_iris", (0.18, 0.12, 0.07), 0.2)
    hair = mat("keeper_hair", (0.3, 0.18, 0.1), 0.6, coat=0.1)
    shirt = mat("keeper_shirt", (0.22, 0.38, 0.6), 0.8)
    trousers = mat("keeper_trousers", (0.2, 0.19, 0.18), 0.85)
    boots = mat("keeper_boots", (0.26, 0.14, 0.07), 0.45, coat=0.3)
    sole = mat("keeper_sole", (0.07, 0.05, 0.04), 0.7)
    apron = mat("keeper_apron", (0.78, 0.55, 0.22), 0.8)
    strap = mat("keeper_strap", (0.32, 0.18, 0.08), 0.55, coat=0.2)
    brass = mat("keeper_brass", (0.9, 0.66, 0.3), 0.3, 0.9)
    cap = mat("keeper_cap", (0.2, 0.22, 0.28), 0.85)
    cap_band = mat("keeper_cap_band", (0.13, 0.13, 0.16), 0.7)
    scarf = mat("keeper_scarf", (0.8, 0.16, 0.1), 0.75)
    human_body(SK, skin, shirt, trousers, white, iris, shoes=boots, sole=sole, glove=skin, sleeves="short",
               hands="relaxed", shape=sh, head=False, shoe_height=0.26)
    slim(boots, 0.55)
    slim(trousers, 0.6, bone="~body")
    slim(shirt, 0.55, bone="~body")
    for X in "LR":
        slim(trousers, 0.7, bone="~leg." + X)
        slim(skin, 0.6, bone="hand." + X)
    # rolled sleeves: the shirt to above the elbow, a thick rolled cuff
    for X, s in (("L", 1), ("R", -1)):
        tube(arm_path(SK, X, 0.008, 0.0, 0.45, shape=sh["arms"]), "~arm." + X, shirt, 18, 0.016, lateral=(s, 0, 0),
             caps=(True, False))
        tube(arm_path(SK, X, 0.022, 0.33, 0.45, shape=sh["arms"]), "~arm." + X, shirt, 14, 0.02, lateral=(s, 0, 0))
    # the head: big and friendly, rosy cheeks, a bushy moustache, hair under the cap
    k = HEAD
    head_detailed(skin, white, iris, center=H, hair=None, size=k, brow=hair)
    cx, cy, cz = H
    sphere(0.106 * k, (0, cy + 0.03, cz + 0.02), "head", hair, (0.95, 1.0, 0.85), 20, 10)      # hair round the back
    for s in (-1, 1):
        sphere(0.02 * k, (0.058 * k * s, cy - 0.07 * k, cz - 0.03 * k), "head", cheek, (1.0, 0.6, 0.8), 10, 6)
        sphere(0.024 * k, (0.024 * k * s, cy - 0.1 * k, cz - 0.047 * k), "head", hair, (1.5, 0.75, 0.7), 12, 7)  # moustache
        sphere(0.016 * k, (0.05 * k * s, cy - 0.094 * k, cz - 0.058 * k), "head", hair, (1.2, 0.8, 1.0), 10, 6)
        sphere(0.02 * k, (0.092 * k * s, cy - 0.01 * k, cz - 0.02 * k), "head", hair, (0.5, 0.9, 1.3), 10, 6)    # sideburns
    # the flat cap: a band, a soft crown pulled forward over a short drooping brim, a button on top
    body_loft([(cz + 0.035 * k, 0.106 * k, 0.112 * k, cy + 0.005), (cz + 0.07 * k, 0.108 * k, 0.114 * k, cy + 0.005)],
              "head", cap_band, 24, 0)
    rotated(sphere(0.114 * k, (0, 0, 0), "head", cap, (1.0, 1.08, 0.45), 24, 12), (0.14, 0, 0))
    o = active()
    o.location = (0, cy - 0.01 * k, cz + 0.085 * k)
    humanoid._select_only(o)
    bpy.ops.object.transform_apply(location=True)
    b = box((0.18 * k, 0.07 * k, 0.014), (0, cy - 0.12 * k, cz + 0.056 * k), "head", cap, rot=(0.16, 0, 0), bevel=0.006)
    sphere(0.013 * k, (0, cy - 0.01 * k, cz + 0.137 * k), "head", cap_band, (1, 1, 0.6), 10, 6)
    # the neckerchief: a knotted roll and a small triangle at the front
    tube([(0.0, -0.08, 1.475, 0.026), (0.075, -0.05, 1.485, 0.028), (0.09, 0.02, 1.495, 0.028), (0.05, 0.075, 1.505, 0.026),
          (-0.02, 0.08, 1.505, 0.026), (-0.085, 0.03, 1.495, 0.028), (-0.075, -0.05, 1.485, 0.028), (0.0, -0.083, 1.475, 0.026)],
         "~body", scarf, 10, 0.03)
    sphere(0.03, (0.0, -0.1, 1.465), "~body", scarf, (1.2, 0.7, 1.0), 12, 7)
    tube([(0.0, -0.105, 1.45, 0.03), (0.0, -0.115, 1.4, 0.018), (0.0, -0.118, 1.36, 0.006)], "~body", scarf, 8, 0.02,
         ell=(1.9, 0.4))
    # the apron: a bib over the chest, a waist band and a long panel to the knees (it swings with the thighs)
    g = 0.016
    rings = [(z, rx + g, ry + g, cy_) for z, rx, ry, cy_, sq in torso_rings(1.0, 1.33, 0.0, sh)]
    shell(rings, -140, -40, "~body", apron, 0.012, 14, 0)
    body_loft([(z, rx + 0.02, ry + 0.02, cy_, sq) for z, rx, ry, cy_, sq in torso_rings(0.99, 1.06, 0.0, sh)],
              "~body", strap, 26, 0)
    box((0.05, 0.02, 0.04), (0.0, -0.132 * sh["waist"] - 0.01, 1.025), "~body", brass, bevel=0.006)
    panel = []
    for z, rx, ry in ((1.0, 0.19, 0.13), (0.9, 0.19, 0.12), (0.8, 0.18, 0.1), (0.68, 0.175, 0.09), (0.58, 0.17, 0.088)):
        panel.append((z, rx * sh["hips"], ry * sh["hips"], -0.01))
    shell(list(reversed(panel)), -145, -35, "~skirt", apron, 0.012, 14, 0)
    # a pocket on the panel, stitched with a brass rivet at each corner
    for s in (-1, 1):
        box((0.018, 0.012, 0.018), (0.085 * s, -0.12 * sh["hips"] - 0.03, 0.855), "~skirt", brass, bevel=0.004)
    box((0.2, 0.014, 0.1), (0.0, -0.12 * sh["hips"] - 0.02, 0.815), "~skirt", mat("keeper_pocket", (0.66, 0.45, 0.17), 0.85),
        rot=(-0.2, 0, 0), bevel=0.006)
    # the straps from the bib's corners over the shoulders to the waist band at the back
    for s in (-1, 1):
        pts = [(0.075 * s, -0.12, 1.33, 0.012), (0.11 * s, -0.08, 1.43, 0.012), (0.12 * s, 0.02, 1.46, 0.012),
               (0.1 * s, 0.11, 1.38, 0.012), (0.04 * s, 0.135, 1.2, 0.012), (-0.06 * s, 0.14, 1.05, 0.012)]
        tube(pts, "~body", strap, 6, 0.03, ell=(1.7, 0.5))
        box((0.024, 0.012, 0.024), (0.075 * s, -0.135, 1.33), "~body", brass, bevel=0.004)
    # a bow at the back of the waist band
    for s in (-1, 1):
        sphere(0.03, (0.035 * s, 0.138, 1.03), "~body", apron, (1.3, 0.5, 0.8), 10, 6)
    # rolled trouser cuffs over the boots
    for X, s in (("L", 1), ("R", -1)):
        x = SK.head("foot." + X).x
        body_loft([(0.25, 0.058, 0.066, 0.004), (0.29, 0.06, 0.068, 0.004)], "~foot." + X, trousers, 18, 0, x0=x)
    rig_export("keeper", out_dir, actions(), SCALE, skeleton=SK, fps=FPS)


if __name__ == "__main__":
    keeper()
    cyc = lambda n: n / FPS
    print("WALK_CELLS %.3f per %d frames (%.2f cells/s at speed_scale 1)" %
          (WALK_STRIDE * SCALE, WALK_FRAMES, WALK_STRIDE * SCALE / cyc(WALK_FRAMES)))
    print("PUSH_CELLS %.3f per %d frames (%.2f cells/s at speed_scale 1)" %
          (PUSH_STRIDE * SCALE, PUSH_FRAMES, PUSH_STRIDE * SCALE / cyc(PUSH_FRAMES)))
