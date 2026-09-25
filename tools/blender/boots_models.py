"""Models for game 6 (Muddy Boots): the soldier (our squad and, recoloured, the enemy), the hostage, the hut, the
rescue tent, crates, the mine, jungle palms, bushes and boulders. Deterministic; output CC BY-SA 4.0; provenance:
this script. The soldier's material "uniform" is recoloured by the game (green for us, khaki for the enemy).
Run: blender -b --factory-startup -P tools/blender/boots_models.py -- godot/games/boots/art/models
One map tile = 1 unit. People are half the humanoid builder's size (about 0.9 units tall).
"""
import bpy, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *  # mat, sphere, box, limb, BONES, clear, rig_export

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)


def soldier():
    clear()
    uni = mat("uniform", (0.25, 0.4, 0.2), 0.8)
    skin = mat("skin", (0.9, 0.7, 0.55), 0.6)
    helmet = mat("helmet", (0.22, 0.32, 0.18), 0.5, coat=0.3)
    boot = mat("boots", (0.12, 0.1, 0.08), 0.6)
    gun = mat("rifle", (0.1, 0.1, 0.11), 0.4, 0.6)
    stock = mat("stock", (0.45, 0.28, 0.15), 0.6)
    pack = mat("pack", (0.35, 0.33, 0.22), 0.8)
    sphere(0.17, (0, 0, 1.3), "spine", uni, (1.15, 0.8, 1.1))
    sphere(0.15, (0, 0, 1.0), "hips", uni, (1.1, 0.8, 0.8))
    box((0.26, 0.14, 0.3), (0, 0.16, 1.3), "spine", pack)
    limb(0.05, (0, 0, 1.45), (0, 0, 1.55), "head", skin)
    sphere(0.12, (0, 0, 1.63), "head", skin)
    sphere(0.155, (0, 0.0, 1.7), "head", helmet, (1.0, 1.05, 0.72))  # the helmet, with a brim
    sphere(0.02, (0.045, -0.115, 1.64), "head", mat("eyes", (0.05, 0.05, 0.05), 0.2))
    sphere(0.02, (-0.045, -0.115, 1.64), "head", mat("eyes", (0.05, 0.05, 0.05), 0.2))
    for s, side in ((1, "L"), (-1, "R")):
        limb(0.055, (0.2 * s, 0, 1.42), (0.24 * s, 0, 1.12), "arm." + side, uni)
        limb(0.045, (0.24 * s, 0, 1.12), (0.26 * s, -0.02, 0.88), "forearm." + side, uni, 0.04)
        sphere(0.045, (0.265 * s, -0.025, 0.84), "forearm." + side, skin)
        limb(0.08, (0.1 * s, 0, 0.95), (0.1 * s, 0, 0.52), "thigh." + side, uni, 0.065)
        limb(0.06, (0.1 * s, 0, 0.52), (0.1 * s, 0, 0.12), "shin." + side, uni, 0.05)
        box((0.11, 0.24, 0.12), (0.1 * s, -0.04, 0.07), "shin." + side, boot)
    # the rifle in the right hand, pointing forward
    box((0.05, 0.7, 0.06), (-0.26, -0.3, 0.86), "forearm.R", gun)
    box((0.06, 0.2, 0.1), (-0.26, 0.08, 0.84), "forearm.R", stock)
    box((0.03, 0.08, 0.12), (-0.26, -0.22, 0.78), "forearm.R", gun)
    run = {}
    for f, ph in ((1, 1), (6, 0), (11, -1), (16, 0), (21, 1)):
        run[f] = {"thigh.L": (40 * ph, 0, 0), "thigh.R": (-40 * ph, 0, 0), "shin.L": (-50 * max(0, -ph), 0, 0),
                  "shin.R": (-50 * max(0, ph), 0, 0), "arm.L": (-35 * ph, 0, 5), "arm.R": (-60, 0, -5),
                  "forearm.R": (-30, 0, 0), "spine": (12, 0, 0), "@root": (0, 0, 0.05 if ph == 0 else 0.0)}
    aim = {"arm.R": (-80, 0, 10), "forearm.R": (-15, 0, 0), "arm.L": (-75, 0, -25), "forearm.L": (-30, 0, 0), "spine": (5, 0, 0)}
    shoot = {1: aim, 3: dict(aim, **{"spine": (-3, 0, 0), "arm.R": (-88, 0, 10)}), 6: aim}
    throw = {1: {"arm.L": (60, 0, 20), "spine": (-10, 0, 0)}, 6: {"arm.L": (-150, 0, 0), "spine": (15, 0, 0)}, 12: {}}
    die = {1: {}, 8: {"hips": (-30, 0, 20), "@root": (0, 0, 0.15), "arm.L": (0, 0, 80), "arm.R": (0, 0, -60)},
           18: {"hips": (-88, 0, 30), "@root": (0, 0, 0.1), "arm.L": (0, 0, 120), "arm.R": (0, 0, -90), "thigh.L": (20, 0, 10)}}
    swim = {1: {"arm.L": (-150, 0, 20), "arm.R": (-40, 0, -20)}, 10: {"arm.L": (-40, 0, 20), "arm.R": (-150, 0, -20)},
            20: {"arm.L": (-150, 0, 20), "arm.R": (-40, 0, -20)}}
    idle = {1: {"arm.R": (-30, 0, 0)}, 30: {"arm.R": (-32, 0, 0), "head": (0, 0, 10), "spine": (2, 0, 0)}, 60: {"arm.R": (-30, 0, 0)}}
    rig_export("soldier", out_dir, {"idle": idle, "run": run, "shoot": shoot, "throw": throw, "die": die, "swim": swim}, 0.5)


def hostage():
    clear()
    shirt = mat("shirt", (0.92, 0.9, 0.85), 0.8)
    trousers = mat("trousers", (0.45, 0.35, 0.25), 0.8)
    skin = mat("skin", (0.8, 0.6, 0.45), 0.6)
    hair = mat("hair", (0.15, 0.1, 0.08), 0.8)
    sphere(0.16, (0, 0, 1.3), "spine", shirt, (1.1, 0.8, 1.1))
    sphere(0.15, (0, 0, 1.0), "hips", trousers, (1.1, 0.8, 0.8))
    limb(0.05, (0, 0, 1.45), (0, 0, 1.55), "head", skin)
    sphere(0.12, (0, 0, 1.63), "head", skin)
    sphere(0.125, (0, 0.02, 1.68), "head", hair, (1.0, 1.0, 0.7))
    for s, side in ((1, "L"), (-1, "R")):
        limb(0.05, (0.2 * s, 0, 1.42), (0.24 * s, 0, 1.12), "arm." + side, shirt)
        limb(0.042, (0.24 * s, 0, 1.12), (0.26 * s, -0.02, 0.88), "forearm." + side, skin, 0.038)
        limb(0.075, (0.1 * s, 0, 0.95), (0.1 * s, 0, 0.52), "thigh." + side, trousers, 0.06)
        limb(0.055, (0.1 * s, 0, 0.52), (0.1 * s, 0, 0.1), "shin." + side, trousers, 0.045)
        box((0.1, 0.2, 0.08), (0.1 * s, -0.03, 0.05), "shin." + side, mat("sandals", (0.4, 0.25, 0.1), 0.7))
    walk = {}
    for f, ph in ((1, 1), (8, 0), (15, -1), (22, 0), (29, 1)):
        walk[f] = {"thigh.L": (25 * ph, 0, 0), "thigh.R": (-25 * ph, 0, 0), "arm.L": (-20 * ph, 0, 5), "arm.R": (20 * ph, 0, -5)}
    wave = {1: {"arm.L": (0, 0, 150), "arm.R": (0, 0, -150)}, 8: {"arm.L": (0, 0, 165), "arm.R": (0, 0, -165), "@root": (0, 0, 0.1)},
            16: {"arm.L": (0, 0, 150), "arm.R": (0, 0, -150)}}
    rig_export("hostage", out_dir, {"idle": {1: {"head": (0, 0, 10)}, 30: {"head": (0, 0, -10)}, 60: {"head": (0, 0, 10)}},
                                    "walk": walk, "wave": wave}, 0.5)


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


def palm():
    trunk = mat("palm_trunk", (0.5, 0.38, 0.25), 0.8)
    leaf = mat("palm_leaf", (0.25, 0.55, 0.2), 0.6)
    parts = []
    pts = [(0.0, 0.0, z * 0.35) for z in range(8)]
    for i, (x, y, z) in enumerate(pts):
        parts.append(pcyl(0.09 - i * 0.006, 0.36, (0.02 * i * i * 0.3, 0, z + 0.18), trunk, verts=8))
    top = Vector((0.02 * 49 * 0.3, 0, 2.7))
    for k in range(8):
        a = k * math.pi / 4
        for j in range(4):
            d = 0.25 + j * 0.28
            p = top + Vector((math.cos(a) * d, math.sin(a) * d, 0.1 - 0.12 * j * j))  # fronds arch, then droop
            parts.append(psphere(0.2, p, leaf, (1.4, 0.45, 0.08) if j else (1.0, 0.5, 0.1)))
            parts[-1].rotation_euler = (0, 0, a)
    export(parts, "palm")


def bush():
    leaf = mat("bush_leaf", (0.2, 0.45, 0.18), 0.7)
    rnd = random.Random(3)
    parts = [psphere(rnd.uniform(0.2, 0.32), (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(0.15, 0.3)), leaf) for _ in range(6)]
    export(parts, "bush")


def boulder():
    rock = mat("rock", (0.5, 0.48, 0.45), 0.9)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5, location=(0, 0, 0.35))
    o = active_obj()
    rnd = random.Random(8)
    for v in o.data.vertices:
        v.co *= rnd.uniform(0.8, 1.15)
    o.scale = (1.0, 0.9, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    export([put(o, rock)], "boulder")


soldier()
hostage()
hut()
tent()
crates()
mine()
palm()
bush()
boulder()
