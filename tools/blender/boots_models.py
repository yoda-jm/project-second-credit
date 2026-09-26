"""Models for game 6 (Muddy Boots): the soldier (our squad and, recoloured, the enemy), the hostage, the hut, the
rescue tent, crates, the mine, jungle palms, bushes and boulders. Deterministic; output CC BY-SA 4.0; provenance:
this script. The soldier's material "uniform" is recoloured by the game (green for us, khaki for the enemy).
Run: blender -b --factory-startup -P tools/blender/boots_models.py -- godot/games/boots/art/models [palm bush ...]
One map tile = 1 unit. People are half the humanoid builder's size (about 0.9 units tall).
"""
import bpy, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)


SK = Skeleton(proportions())
FPS = 24


def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


def local_to_rest(bone, p):
    """A point given in a bone's rest frame, as (left, forward, up) for the pose channels."""
    q = bone_frame(SK, bone) @ Vector(p)
    return (q.x, -q.y, q.z)


def rifle(gun, stock):
    """An assault rifle in the right fist (hand.R's frame: the grip runs along +Z, the barrel along the hand, +Y)."""
    m = -0.012   # the palm's side
    parts = [box((0.028, 0.035, 0.1), (m, 0.078, 0.0), "hand.R", gun, bevel=0.008),
             box((0.045, 0.3, 0.066), (m, 0.1, 0.085), "hand.R", gun, bevel=0.01),
             box((0.052, 0.2, 0.06), (m, 0.33, 0.08), "hand.R", stock, bevel=0.012),
             box((0.03, 0.05, 0.13), (m, 0.17, 0.0), "hand.R", gun, rot=(0.2, 0, 0), bevel=0.006),
             box((0.04, 0.24, 0.075), (m, -0.16, 0.07), "hand.R", stock, bevel=0.012),
             box((0.012, 0.02, 0.03), (m, 0.5, 0.12), "hand.R", gun, bevel=0.003)]
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.011, depth=0.22, location=(m, 0.54, 0.09), rotation=(math.pi / 2, 0, 0))
    parts.append(tag(active(), "hand.R", gun))
    place(parts, bone_frame(SK, "hand.R"))


GRIP_L = local_to_rest("hand.R", (-0.012, 0.31, 0.02))   # the left hand under the handguard


def armed(pose, at, aim):
    """The rifle: the right hand at `at` (rest space, riding the chest), the barrel along `aim` (yaw, pitch, roll);
    the left hand on the handguard."""
    return P(pose, **{"ik_hand.R": at, "ikh.R": 1.0, "hand_dir.R": aim, "hdw.R": 1.0, "ik_hand.L": GRIP_L, "ikh.L": 1.0})


HANDS_ON = {"R": "chest", "L": "hand.R"}
POLES = {"R": (0.9, 0.5, -0.5), "L": (0.5, 0.3, -1.0)}
STAND = {"ik_foot.L": (0.12, 0.04, 0.09, 0, 10), "ik_foot.R": (-0.12, -0.04, 0.09, 0, 14), "ikw.L": 1.0, "ikw.R": 1.0}
PORT_AT, PORT_AIM = (-0.13, 0.26, 1.08), (32, 22, 0)
AIM_AT, AIM_AIM = (-0.1, 0.24, 1.33), (0, 0, 0)


def soldier_actions():
    idle = {}
    for i in range(0, 61, 6):
        t = i / 60.0
        br = math.sin(2 * math.pi * t * 2)
        look = math.sin(2 * math.pi * t)
        idle[i + 1] = armed(P(STAND, **{"root": (0.01 * look, 0, -0.03), "hips": (2, 4 * look, -2 * look),
                                        "chest": (3 + br, -4 * look, 0), "clavicle.L": (4, 0, br), "clavicle.R": (4, 0, br),
                                        "neck": (0, 16 * math.sin(2 * math.pi * (t - 0.1)), 0),
                                        "head": (-2, 22 * math.sin(2 * math.pi * (t - 0.12)), 0)}),
                            PORT_AT, (PORT_AIM[0], PORT_AIM[1] - 8, 0))
    run = gait(SK, 16, 3.14, 0.32, lift=0.3, lift_at=0.33, strike=8, push=45, bob=-0.04, drop=-0.08, lean=14,
               arm_swing=0, arm_out=0, elbow=0, elbow_swing=0, pelvis_yaw=10, pelvis_roll=4, shoulder_yaw=4, reach=0.4,
               base={"head": (-6, 0, 0)})
    for f, k in run.keys.items():
        run.keys[f] = armed(k, PORT_AT, PORT_AIM)
    run.hand_on, run.arm_pole = HANDS_ON, POLES
    stance = {"ik_foot.L": (0.13, 0.18, 0.09, 0, 12), "ik_foot.R": (-0.14, -0.2, 0.09, 0, 35), "ikw.L": 1.0, "ikw.R": 1.0,
              "root": (0, 0, -0.07), "hips": (4, -16, 0), "spine": (4, -4, 0), "chest": (4, 0, 0), "neck": (0, 8, 0),
              "head": (8, 6, 4)}
    aim = armed(stance, AIM_AT, AIM_AIM)
    kick = armed(P(stance, **{"chest": (-2, 3, 0), "spine": (1, -3, 0), "head": (4, 6, 4), "root": (0, -0.03, -0.07)}),
                 (AIM_AT[0], AIM_AT[1] - 0.04, AIM_AT[2] + 0.015), (0, 8, 3))
    shoot = Anim({1: aim, 2: kick, 4: P(aim, **{"chest": (2, 1, 0)}), 6: aim}, hand_on=HANDS_ON, arm_pole=POLES)
    # a grenade: the rifle drops to the right hand alone, the left arm lobs overhand
    one = P(STAND, **{"ik_hand.R": PORT_AT, "ikh.R": 1.0, "hand_dir.R": (10, -30, 0), "hdw.R": 1.0})
    throw = Anim({1: P(one, **{"arm.L": (30, 0, 20), "forearm.L": (60, 0, 0)}),
                  4: P(one, **{"arm.L": (140, 0, 40), "forearm.L": (110, 0, 0), "chest": (-6, -26, 0), "spine": (-4, -10, 0),
                               "root": (0, -0.08, -0.08), "head": (-10, 20, 0)}),
                  6: P(one, **{"arm.L": (150, 0, 20), "forearm.L": (40, 0, 0), "chest": (6, 10, 0), "spine": (4, 6, 0),
                               "root": (0, 0.06, -0.08), "head": (-6, -6, 0)}),
                  8: P(one, **{"arm.L": (90, 0, 10), "forearm.L": (10, 0, 0), "chest": (12, 24, 0), "spine": (6, 10, 0),
                               "root": (0, 0.1, -0.1), "head": (0, -16, 0)}),
                  12: P(one, **{"arm.L": (10, 0, 12), "forearm.L": (20, 0, 0)})},
                 hand_on={"R": "chest"}, arm_pole=POLES)
    fallen = {"ikw.L": 0.0, "ikw.R": 0.0, "ikh.L": 0.0, "ikh.R": 0.0, "hand_dir.R": (70, -4, 90), "hdw.R": 1.0, "turn": (-90, 0, 12),
              "root": (0, 0.55, 0.12), "spine": (-4, 0, 6), "chest": (-4, 0, 0), "neck": (4, 0, 0), "head": (6, 45, 8),
              "arm.L": (20, 0, 70), "forearm.L": (40, 0, 0), "arm.R": (-5, 0, 60), "forearm.R": (20, 0, 0),
              "thigh.L": (25, 0, 10), "shin.L": (40, 0, 0), "thigh.R": (8, 0, 14), "shin.R": (15, 0, 0),
              "foot.L": (-30, 0, 0), "foot.R": (-35, 0, 0)}
    die = Anim({1: aim,
                3: P(aim, **{"chest": (-18, 10, 6), "spine": (-8, 0, 0), "head": (-26, 10, 8), "root": (0, -0.06, -0.06)}),
                7: P(fallen, **{"ikw.L": 0.9, "ikw.R": 0.9, "turn": (-8, 0, 4), "root": (0, 0.0, -0.28), "hips": (30, 0, 0),
                                "spine": (10, 0, 0), "chest": (-10, 0, 0), "head": (-30, 0, 0), "arm.L": (40, 0, 40),
                                "arm.R": (50, 0, 30), "hand_dir.R": (20, -45, 30), "ik_foot.L": (0.13, 0.18, 0.09, 0, 12), "ik_foot.R": (-0.14, -0.2, 0.09, 0, 35)}),
                11: P(fallen, **{"turn": (-55, 0, 10), "root": (0, 0.3, 0.05), "thigh.L": (70, 0, 10), "shin.L": (100, 0, 0),
                                 "thigh.R": (50, 0, 14), "shin.R": (80, 0, 0), "arm.L": (70, 0, 60), "arm.R": (30, 0, 60), "hand_dir.R": (50, 10, 70)}),
                14: P(fallen, **{"root": (0, 0.55, 0.16), "turn": (-86, 0, 12)}),
                18: fallen}, hand_on=HANDS_ON, arm_pole=POLES)
    swim = {}
    for i in range(0, 21, 4):
        t = i / 20.0
        a = 2 * math.pi * t
        swim[i + 1] = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (48, 0, 4 * math.sin(a)), "root": (0, -0.62, -0.32 + 0.02 * math.sin(a * 2)),
                       "neck": (-30, 0, 0), "head": (-30, 6 * math.sin(a), 0),
                       "ik_hand.R": (-0.16, 0.36, 1.62), "ikh.R": 1.0, "hand_dir.R": (0, 20, 0), "hdw.R": 1.0,
                       "arm.L": (70 + 70 * math.cos(a), 0, 25 + 15 * math.sin(a)), "forearm.L": (30 + 25 * max(0, math.sin(a)), 0, 0),
                       "chest": (0, 8 * math.sin(a), 0),
                       "thigh.L": (12 * math.sin(a * 2), 0, 6), "thigh.R": (-12 * math.sin(a * 2), 0, 6),
                       "shin.L": (20 + 15 * max(0, math.cos(a * 2)), 0, 0), "shin.R": (20 + 15 * max(0, -math.cos(a * 2)), 0, 0),
                       "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0)}
    return {"idle": Anim(idle, loop=True, hand_on=HANDS_ON, arm_pole=POLES), "run": run, "shoot": shoot, "throw": throw,
            "die": die, "swim": Anim(swim, loop=True, hand_on={"R": "chest"}, arm_pole=POLES)}


def soldier():
    clear()
    uni = mat("uniform", (0.25, 0.4, 0.2), 0.8)
    skin = mat("skin", (0.9, 0.7, 0.55), 0.6)
    helmet = mat("helmet", (0.22, 0.32, 0.18), 0.5, coat=0.3)
    boot = mat("boots", (0.12, 0.1, 0.08), 0.6, coat=0.2)
    gun = mat("rifle", (0.1, 0.1, 0.11), 0.4, 0.6)
    stock = mat("stock", (0.45, 0.28, 0.15), 0.6)
    pack = mat("pack", (0.35, 0.33, 0.22), 0.8)
    belt = mat("belt", (0.2, 0.18, 0.12), 0.7)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("iris", (0.2, 0.15, 0.1), 0.2)
    shape = {"chest": 1.05, "waist": 1.06, "arms": 1.05, "legs": 1.04, "neck": 1.1, "hand": 1.1}
    human_body(SK, skin, uni, uni, white, iris, shoes=boot, sole=boot, glove=skin, sleeves="long", hands="grip",
               shape=shape, shoe_height=0.21)
    cx, cy, cz = 0, -0.012, 1.665
    sphere(0.128, (0, cy + 0.008, cz + 0.035), "head", helmet, (1.0, 1.06, 0.74))   # the helmet, with its brim
    body_loft([(cz - 0.035, 0.132, 0.138, cy + 0.008), (cz - 0.015, 0.128, 0.134, cy + 0.008)], "head", helmet, 24, 0)
    for k in (-1, 1):   # chin strap
        tube([(0.092 * k, cy + 0.0, cz - 0.02, 0.005), (0.07 * k, cy - 0.05, cz - 0.09, 0.005), (0, cy - 0.065, cz - 0.115, 0.005)], "head", belt, 6, 0.015)
    # the webbing belt with pouches, braces, the pack and a bedroll
    body_loft([(z, rx + 0.01, ry + 0.01, cy_, sq) for z, rx, ry, cy_, sq in torso_rings(1.0, 1.06, 0.0, shape)], "~body", belt, 26, 0)
    for x in (-0.1, -0.04, 0.04, 0.1):
        box((0.05, 0.035, 0.055), (x, -0.112, 1.02), "~body", pack, bevel=0.01)
    for k in (-1, 1):
        rings = torso_rings(1.06, 1.43, 0.0, shape)
        tube([(0.085 * k, -(ry + 0.008) + cy_, z, 0.011) for z, rx, ry, cy_, sq in rings], "~body", belt, 6, 0.03, ell=(1.3, 0.4))
    box((0.27, 0.13, 0.3), (0, 0.17, 1.28), "~body", pack, bevel=0.035)
    box((0.2, 0.05, 0.12), (0, 0.25, 1.2), "~body", pack, bevel=0.02)
    body_loft([(1.43, 0.13, 0.05, 0.19), (1.47, 0.13, 0.05, 0.19)], "~body", mat("bedroll", (0.3, 0.25, 0.18), 0.9), 14, 1)
    rifle(gun, stock)
    rig_export("soldier", out_dir, soldier_actions(), 0.5, skeleton=SK, fps=FPS)


def hostage_actions():
    idle = {}
    for i in range(0, 61, 6):
        t = i / 60.0
        br = math.sin(2 * math.pi * t * 3)   # quick, nervous breaths
        look = math.sin(2 * math.pi * t)
        idle[i + 1] = P(STAND, **{"root": (0.015 * look, 0, -0.02), "hips": (0, 3 * look, -3 * look), "spine": (6, 0, 0),
                                  "chest": (8 + 1.5 * br, 0, 0), "clavicle.L": (8, 0, 6 + 2 * br), "clavicle.R": (8, 0, 6 + 2 * br),
                                  "arm.L": (30, 30, 10), "forearm.L": (80, 0, 0), "arm.R": (30, 30, 10), "forearm.R": (85, 0, 0),
                                  "hand.L": (0, 0, -10), "hand.R": (0, 0, -10), "neck": (6, 25 * look, 0),
                                  "head": (4, 20 * math.sin(2 * math.pi * (t - 0.05)), 0)})
    run = gait(SK, 16, 3.14, 0.34, lift=0.26, lift_at=0.35, strike=10, push=40, bob=-0.04, drop=-0.08, lean=12,
               arm_swing=45, arm_out=14, elbow=55, elbow_swing=15, pelvis_yaw=10, pelvis_roll=5, shoulder_yaw=12, reach=0.4)
    wave = {}
    for i in range(0, 17, 2):
        t = i / 16.0
        s_ = math.sin(2 * math.pi * t)
        wave[i + 1] = P(STAND, **{"root": (0, 0, -0.02 - 0.03 * max(0, s_)), "arm.L": (40, -20, 120 + 18 * s_),
                                  "arm.R": (40, -20, 120 - 18 * s_), "forearm.L": (25 - 15 * s_, 0, 0), "forearm.R": (25 + 15 * s_, 0, 0),
                                  "clavicle.L": (0, 0, 14), "clavicle.R": (0, 0, 14), "chest": (-4, 6 * s_, 0), "head": (-12, -6 * s_, 0),
                                  "hand.L": (0, 0, 10), "hand.R": (0, 0, 10)})
    return {"idle": Anim(idle, loop=True), "walk": run, "wave": Anim(wave, loop=True)}


def hostage():
    clear()
    shirt = mat("shirt", (0.92, 0.9, 0.85), 0.8)
    trousers = mat("trousers", (0.45, 0.35, 0.25), 0.8)
    skin = mat("skin", (0.8, 0.6, 0.45), 0.6)
    hair = mat("hair", (0.15, 0.1, 0.08), 0.8)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("iris", (0.2, 0.12, 0.08), 0.2)
    human_body(SK, skin, shirt, trousers, white, iris, hair=hair, shoes=mat("sandals", (0.4, 0.25, 0.1), 0.7),
               sleeves="short", hands="relaxed", shape={"chest": 0.95, "arms": 0.92, "waist": 1.02}, shoe_height=0.13)
    rig_export("hostage", out_dir, hostage_actions(), 0.5, skeleton=SK, fps=FPS)


# ------------------------------------------------------------------ props

def active_obj():
    return bpy.context.active_object


def put(o, material, smooth=False, bevel=0.0):
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 2
        b.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=b.name)
    o.data.materials.clear()
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth() if smooth else bpy.ops.object.shade_flat()
    return o


def pbox(size, loc, material, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active_obj()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return put(o, material, bevel=bevel)


def pcyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=12, smooth=True):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return put(active_obj(), material, smooth)


def psphere(r, loc, material, scale=(1, 1, 1), segs=14, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active_obj()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, True)


def export(parts, name):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    active_obj().name = name
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)
    clear()


def hut():
    """A 2 x 2 tile jungle hut, centred on its footprint; the door faces +Z in the game (-Y here, the map's south)."""
    bamboo = mat("bamboo", (0.72, 0.58, 0.32), 0.7)
    dark = mat("hut_dark", (0.08, 0.06, 0.05), 0.9)
    straw = mat("thatch", (0.78, 0.66, 0.35), 0.95)
    parts = []
    for i in range(14):  # walls of upright canes
        a = i / 14.0
        parts.append(pcyl(0.06, 1.0, (-0.8 + a * 1.6, 0.8, 0.5), bamboo, verts=6))
        parts.append(pcyl(0.06, 1.0, (-0.8 + a * 1.6, -0.8, 0.5), bamboo, verts=6) if abs(-0.8 + a * 1.6) > 0.3 else None)
        parts.append(pcyl(0.06, 1.0, (0.8, -0.8 + a * 1.6, 0.5), bamboo, verts=6))
        parts.append(pcyl(0.06, 1.0, (-0.8, -0.8 + a * 1.6, 0.5), bamboo, verts=6))
    parts = [p for p in parts if p is not None]
    parts.append(pbox((0.55, 0.05, 0.8), (0, -0.78, 0.4), dark, bevel=0.0))  # the dark doorway
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.55, radius2=0.05, depth=1.1, location=(0, 0, 1.5), rotation=(0, 0, math.pi / 4))
    parts.append(put(active_obj(), straw))
    for i in range(3):  # straw fringes
        parts.append(pcyl(1.5 - i * 0.02, 0.06, (0, 0, 1.0 + i * 0.04), straw, rot=(0, 0, math.pi / 4), verts=4, r2=1.45, smooth=False))
    export(parts, "hut")


def tent():
    canvas = mat("canvas", (0.4, 0.5, 0.3), 0.85)
    flag = mat("tent_flag", (0.95, 0.85, 0.2), 0.6)
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=0.9, depth=1.8, location=(0, 0, 0.45), rotation=(math.pi / 2, 0, math.pi / 2))
    o = active_obj()
    o.scale = (1.0, 0.75, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(put(o, canvas))
    parts.append(pcyl(0.02, 1.6, (0.9, 0, 0.8), mat("pole", (0.4, 0.3, 0.2), 0.7), verts=6))
    parts.append(pbox((0.4, 0.02, 0.26), (1.1, 0, 1.45), flag, bevel=0.0))
    export(parts, "tent")


def crates():
    wood = mat("crate_wood", (0.55, 0.42, 0.22), 0.8)
    band = mat("crate_band", (0.2, 0.25, 0.15), 0.6)
    g = [pbox((0.5, 0.35, 0.3), (0, 0, 0.15), wood, bevel=0.02), pbox((0.52, 0.37, 0.05), (0, 0, 0.2), band, bevel=0.0)]
    for i in range(3):
        g.append(psphere(0.05, (-0.12 + i * 0.12, 0, 0.33), mat("grenade", (0.25, 0.3, 0.2), 0.5), (1, 1, 1.3)))
    export(g, "grenade_crate")
    r = [pbox((0.8, 0.3, 0.25), (0, 0, 0.125), wood, bevel=0.02), pbox((0.82, 0.32, 0.05), (0.2, 0, 0.13), band, bevel=0.0)]
    r.append(pcyl(0.04, 0.6, (0, 0, 0.3), mat("rocket_body", (0.6, 0.6, 0.55), 0.4, 0.5), rot=(0, math.pi / 2, 0), verts=10))
    r.append(pcyl(0.04, 0.1, (0.35, 0, 0.3), mat("rocket_tip", (0.8, 0.2, 0.1), 0.4), rot=(0, math.pi / 2, 0), r2=0.0, verts=10))
    export(r, "rocket_crate")


def mine():
    metal = mat("mine_metal", (0.3, 0.32, 0.28), 0.5, 0.6)
    parts = [pcyl(0.18, 0.07, (0, 0, 0.035), metal, verts=16), pcyl(0.04, 0.05, (0, 0, 0.09), mat("mine_pin", (0.7, 0.2, 0.1), 0.4), verts=8)]
    export(parts, "mine")


class Builder:
    """One mesh built by hand: faces carry a material slot and a smooth flag, so a whole plant is one object."""

    def __init__(self):
        self.verts, self.faces, self.mats, self.smooth, self.slots = [], [], [], [], []

    def slot(self, material):
        if material not in self.slots:
            self.slots.append(material)
        return self.slots.index(material)

    def face(self, pts, material, smooth=True):
        i = len(self.verts)
        self.verts.extend(tuple(p) for p in pts)
        self.faces.append(tuple(range(i, i + len(pts))))
        self.mats.append(self.slot(material))
        self.smooth.append(smooth)

    def grid(self, rings, material, smooth=True, cap=False):
        """Faces between consecutive closed rings of points (a tube); materials may be one per band."""
        i0 = len(self.verts)
        n = len(rings[0])
        for r in rings:
            self.verts.extend(tuple(p) for p in r)
        for k in range(len(rings) - 1):
            m = material[k] if isinstance(material, list) else material
            for j in range(n):
                a, b = i0 + k * n + j, i0 + k * n + (j + 1) % n
                self.faces.append((a, b, b + n, a + n))
                self.mats.append(self.slot(m))
                self.smooth.append(smooth)
        if cap:
            top = i0 + (len(rings) - 1) * n
            self.faces.append(tuple(range(top, top + n)))
            self.mats.append(self.slot(material[-1] if isinstance(material, list) else material))
            self.smooth.append(smooth)

    def add_object(self, o):
        """Merges an existing primitive object (its material slots and smoothing) and deletes it."""
        me = o.data
        mw = o.matrix_world
        i0 = len(self.verts)
        self.verts.extend(tuple(mw @ v.co) for v in me.vertices)
        for f in me.polygons:
            self.faces.append(tuple(i0 + v for v in f.vertices))
            self.mats.append(self.slot(me.materials[f.material_index]))
            self.smooth.append(f.use_smooth)
        bpy.data.objects.remove(o)

    def build(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        for m in self.slots:
            me.materials.append(m)
        for f, mi, sm in zip(me.polygons, self.mats, self.smooth):
            f.material_index = mi
            f.use_smooth = sm
        me.update()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        return o


def ring(c, t, r, n, phase=0.0, wobble=None):
    """n points around centre c, in the plane normal to direction t."""
    t = t.normalized()
    u = t.cross(Vector((0, 1, 0)))
    if u.length < 1e-4:
        u = Vector((1, 0, 0))
    u.normalize()
    v = t.cross(u)
    pts = []
    for j in range(n):
        a = phase + j * math.tau / n
        rr = r * (wobble[j] if wobble else 1.0)
        pts.append(c + (u * math.cos(a) + v * math.sin(a)) * rr)
    return pts


def bezier(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t


def palm():
    rnd = random.Random(11)
    trunk = mat("palm_trunk", (0.27, 0.19, 0.12), 0.85)
    band = mat("palm_ring", (0.13, 0.09, 0.06), 0.9)
    crown = mat("palm_crown", (0.24, 0.26, 0.1), 0.8)
    nut = mat("coconut", (0.2, 0.16, 0.07), 0.6)
    rib = mat("palm_rib", (0.16, 0.2, 0.06), 0.7)
    shades = [mat("palm_leaf_dark", (0.045, 0.13, 0.04), 0.6), mat("palm_leaf", (0.07, 0.19, 0.05), 0.55),
              mat("palm_leaf_light", (0.13, 0.27, 0.07), 0.5), mat("palm_leaf_sun", (0.24, 0.34, 0.09), 0.5)]
    dry = mat("palm_leaf_dry", (0.42, 0.3, 0.1), 0.75)
    bld = Builder()
    # a leaning trunk that curves back up, in ring segments (a lip at each old leaf scar)
    p0, p1, top = Vector((0, 0, 0)), Vector((0.05, 0, 1.3)), Vector((0.42, 0, 2.55))
    segs, sides = 11, 9
    rings, bands = [], []
    for k in range(segs):
        for f, rs, m in ((0.0, 1.08, band), (0.12, 0.95, trunk), (0.92, 1.0, band)):
            t = (k + f) / segs
            c = bezier(p0, p1, top, t)
            d = bezier(p0, p1, top, min(t + 0.01, 1)) - bezier(p0, p1, top, max(t - 0.01, 0))
            r = 0.085 - 0.03 * t + 0.09 * max(0.0, 0.18 - t) ** 1.3 * 4  # flared foot
            rings.append(ring(c, d, r * rs, sides, phase=k * 0.35))
            bands.append(m)
    rings.append(ring(top, top - bezier(p0, p1, top, 0.98), 0.07, sides, phase=segs * 0.35))
    bld.grid(rings, bands[:len(rings) - 1], smooth=True)
    # crownshaft bulb
    tdir = (top - bezier(p0, p1, top, 0.97)).normalized()
    cr = [ring(top + tdir * h, tdir, r, sides) for h, r in ((0.0, 0.075), (0.08, 0.1), (0.18, 0.085), (0.26, 0.03))]
    bld.grid(cr, crown, cap=True)
    head = top + tdir * 0.2
    # coconuts under the crown
    for k in range(5):
        a = k * math.tau / 5 + rnd.uniform(-0.3, 0.3)
        c = top + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, rnd.uniform(-0.05, 0.06)))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.07, location=c)
        o = active_obj()
        o.scale = (1, 1, 1.15)
        put(o, nut, True)
        bpy.ops.object.transform_apply(scale=True)
        bld.add_object(o)
    # fronds: a rib that arches up and droops, with folded leaflets on both sides
    fronds = []
    for k in range(6):   # upper, shorter, sunlit
        fronds.append((k * math.tau / 6 + 0.25, rnd.uniform(0.6, 0.8), rnd.uniform(1.15, 1.3), 1.6, rnd.choice((1, 2, 2))))
    for k in range(7):   # lower, longer, drooping, darker; one of them yellowing at the tip
        fronds.append((k * math.tau / 7 + rnd.uniform(-0.15, 0.15), rnd.uniform(0.2, 0.4), rnd.uniform(1.35, 1.5), 1.9,
                       -2 if k == 3 else rnd.choice((0, 1, 1))))
    fronds.append((1.2, -0.5, 1.0, 1.2, -1))  # an old dead frond hanging against the trunk
    for a, pitch0, length, bend, shade in fronds:
        curl = rnd.uniform(-0.35, 0.35)  # fronds sweep sideways a little, not straight spokes
        n = 15
        p = head + Vector((math.cos(a), math.sin(a), 0)) * 0.05
        pts, tans = [p.copy()], []
        for i in range(n):
            u = (i + 0.5) / n
            pitch = pitch0 - bend * u ** 1.4
            dirh = Vector((math.cos(a + curl * u * u), math.sin(a + curl * u * u), 0))
            t = dirh * math.cos(pitch) + Vector((0, 0, math.sin(pitch)))
            tans.append(t)
            p = p + t * (length / n)
            pts.append(p.copy())
        tans.append(tans[-1])
        # rib: a thin flat strip, widest at the base
        for i in range(n):
            side = Vector((-tans[i].y, tans[i].x, 0)).normalized()
            w0, w1 = 0.018 * (1 - i / n) + 0.004, 0.018 * (1 - (i + 1) / n) + 0.004
            bld.face([pts[i] - side * w0, pts[i] + side * w0, pts[i + 1] + side * w1, pts[i + 1] - side * w1],
                     rib if shade >= 0 else dry, smooth=False)
        for i in range(1, n):
            u = i / n
            ll = 0.5 * length * (u ** 0.45) * ((1 - u) ** 0.7)
            if shade == -1:
                m = dry
            elif shade == -2:
                m = dry if u > 0.55 else shades[0]
            else:
                m = shades[min(3, shade + (1 if u > 0.6 else 0))]
            t = tans[i]
            side = Vector((-t.y, t.x, 0)).normalized()
            for sgn in (-1, 1):
                d = side * sgn * 0.8 + t * 0.55
                d.z -= 0.35 + 0.35 * u
                d.normalize()
                ln = ll * rnd.uniform(0.85, 1.1)
                b = pts[i]
                tip = b + d * ln
                wv = t - d * t.dot(d)
                wv.normalize()
                w = ln * 0.13
                mid = b + d * (ln * 0.4)
                fold = Vector((0, 0, -w * 0.9))
                bld.face([b, mid + wv * w + fold, tip], m)
                bld.face([b, tip, mid - wv * w + fold], m)
    export([bld.build("palm")], "palm")


def leaf(bld, base, dirh, pitch0, bend, length, width, inner, outer):
    """A broad pointed leaf folded along its midrib; the base half dark, the tip half light."""
    side = Vector((-dirh.y, dirh.x, 0))
    n = 4
    prof = [0.35, 0.9, 1.0, 0.75, 0.0]
    p = base.copy()
    mids, lefts, rights = [p.copy()], [], []
    pts = [p.copy()]
    for i in range(n):
        u = (i + 0.5) / n
        pitch = pitch0 - bend * u
        p = p + (dirh * math.cos(pitch) + Vector((0, 0, math.sin(pitch)))) * (length / n)
        pts.append(p.copy())
    for i, c in enumerate(pts):
        w = width * prof[i] * 0.5
        drop = Vector((0, 0, -w * 0.55))
        lefts.append(c - side * w + drop)
        rights.append(c + side * w + drop)
    for i in range(n):
        m = inner if i < 2 else outer
        if i < n - 1:
            bld.face([pts[i], pts[i + 1], lefts[i + 1], lefts[i]], m)
            bld.face([pts[i], rights[i], rights[i + 1], pts[i + 1]], m)
        else:
            bld.face([pts[i], pts[i + 1], lefts[i]], m)
            bld.face([pts[i], rights[i], pts[i + 1]], m)


def bush():
    rnd = random.Random(3)
    core = mat("bush_core", (0.025, 0.07, 0.025), 0.9)
    dark = mat("bush_leaf_dark", (0.04, 0.12, 0.035), 0.7)
    mid = mat("bush_leaf", (0.07, 0.19, 0.05), 0.6)
    light = mat("bush_leaf_light", (0.15, 0.28, 0.07), 0.55)
    bld = Builder()
    clumps = [(Vector((-0.17, -0.12, 0)), 1.0), (Vector((0.2, -0.05, 0)), 0.85), (Vector((0.0, 0.22, 0)), 0.9)]
    for c, s in clumps:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22 * s, location=c + Vector((0, 0, 0.12 * s)))
        o = active_obj()
        o.scale = (1, 1, 0.8)
        put(o, core, True)
        bpy.ops.object.transform_apply(scale=True)
        bld.add_object(o)
        # three tiers: low leaves splay and droop, the top ones stand up
        for count, pitch, bend, ln, wd, h, inner, outer in ((8, 0.35, 1.1, 0.42, 0.2, 0.08, core, dark),
                                                           (7, 0.85, 1.2, 0.36, 0.19, 0.14, dark, mid),
                                                           (5, 1.25, 1.1, 0.28, 0.17, 0.2, mid, light)):
            ph = rnd.uniform(0, math.tau)
            for k in range(count):
                a = ph + k * math.tau / count + rnd.uniform(-0.2, 0.2)
                dirh = Vector((math.cos(a), math.sin(a), 0))
                leaf(bld, c + dirh * 0.03 + Vector((0, 0, h * s)), dirh, pitch + rnd.uniform(-0.15, 0.15), bend,
                     ln * s * rnd.uniform(0.9, 1.1), wd * s, inner, outer)
    export([bld.build("bush")], "bush")


def boulder():
    from mathutils import noise
    rock = mat("rock", (0.2, 0.185, 0.17), 0.9)
    moss = mat("rock_moss", (0.06, 0.11, 0.03), 0.95)
    bld = Builder()
    for loc, r, sc, sub, seed in (((0, 0, 0.26), 0.5, (1.0, 0.86, 0.74), 3, 8), ((0.44, -0.3, 0.07), 0.19, (1.0, 0.85, 0.75), 2, 9)):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(0, 0, 0))
        o = active_obj()
        off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
        for v in o.data.vertices:
            n = v.co.normalized()
            k = 1.0 + 0.3 * noise.noise(n * 1.4 + off) + 0.08 * noise.noise(n * 3.5 + off)
            v.co = Vector((n.x * sc[0], n.y * sc[1], n.z * sc[2])) * r * k + Vector(loc)
            v.co.z = max(v.co.z, -0.03)  # sits on the ground
        o.data.materials.append(rock)
        o.data.materials.append(moss)
        o.data.update()
        for f in o.data.polygons:
            f.material_index = 1 if f.normal.z + 0.35 * noise.noise(f.center * 6 + off) > 0.8 else 0
            f.use_smooth = False
        bld.add_object(o)
    export([bld.build("boulder")], "boulder")


only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []  # optional: build only these models
for build in (soldier, hostage, hut, tent, crates, mine, palm, bush, boulder):
    if not only or build.__name__ in only:
        build()
