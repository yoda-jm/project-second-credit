"""The Fruitburrow gardener: a stylised character on an armature, with keyed animations (idle, walk, dig, throw,
die, cheer). Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/fruitburrow_gardener.py -- godot/games/fruitburrow/art/models
The character is about 0.85 m tall, centred on the cell (feet at z = -0.45), facing -Y. Parts are rigidly bound to
their bones (a toy-like look, and robust skinning); each animation is a separate glTF animation.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
FPS = 30
MATS = {}


def mat(name, color, rough=0.6, coat=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    MATS[name] = m
    return m


def active():
    return bpy.context.active_object


def part(obj, bone, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["bone"] = bone
    bpy.ops.object.shade_smooth()
    return obj


def sphere(r, loc, bone, material, scale=(1, 1, 1), segs=24, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return part(o, bone, material)


def cyl(r, depth, loc, bone, material, rot=(0, 0, 0), r2=None, verts=20):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = active()
    bev = o.modifiers.new("b", "BEVEL")
    bev.width = min(r, depth) * 0.25
    bev.segments = 3
    bpy.ops.object.modifier_apply(modifier=bev.name)
    return part(o, bone, material)


def capsule(r, a, b, bone, material, verts=16):
    """A rounded limb from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(a + b) / 2)
    o = active()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    parts = [o]
    for p in (a, b):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=verts, ring_count=8, radius=r, location=p)
        parts.append(active())
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for x in parts:
        x.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    return part(active(), bone, material)


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
bpy.context.scene.render.fps = FPS

skin = mat("skin", (0.95, 0.68, 0.52), 0.55)
cheek = mat("cheek", (0.95, 0.45, 0.42), 0.6)
denim = mat("overalls", (0.16, 0.33, 0.7), 0.75)
shirt = mat("shirt", (0.85, 0.2, 0.18), 0.7)
straw = mat("straw", (0.93, 0.78, 0.4), 0.8)
band = mat("hat_band", (0.75, 0.15, 0.12), 0.6)
boot = mat("boots", (0.35, 0.2, 0.1), 0.6, coat=0.2)
dark = mat("eyes", (0.03, 0.03, 0.04), 0.1, coat=1.0)
white = mat("eye_shine", (1, 1, 1), 0.1)
metal = mat("spade", (0.7, 0.72, 0.75), 0.3)
wood = mat("handle", (0.55, 0.36, 0.18), 0.6)
brass = mat("buttons", (0.95, 0.75, 0.25), 0.3)
hair = mat("hair", (0.45, 0.25, 0.1), 0.8)

# ------------------------------------------------------------------ body parts (bone name in "bone")
torso = sphere(0.17, (0, 0, 0.06), "spine", denim, (1.0, 0.8, 1.05))
sphere(0.15, (0, 0, 0.12), "spine", shirt, (1.02, 0.82, 0.9))  # shirt under the bib
bib = cyl(0.1, 0.03, (0, -0.125, 0.1), "spine", denim, rot=(math.pi / 2, 0, 0), verts=4)
for s in (-1, 1):
    sphere(0.02, (0.07 * s, -0.14, 0.15), "spine", brass)
    capsule(0.02, (0.07 * s, -0.12, 0.16), (0.09 * s, 0.05, 0.22), "spine", denim, 8)  # straps
hips = sphere(0.16, (0, 0, -0.1), "hips", denim, (1.05, 0.85, 0.7))
head = sphere(0.15, (0, 0, 0.33), "head", skin, (1.0, 0.95, 1.0), 32, 20)
sphere(0.045, (0, -0.15, 0.31), "head", skin, (1.0, 0.9, 0.9))  # nose
for s in (-1, 1):
    sphere(0.028, (0.06 * s, -0.125, 0.36), "head", dark, (1, 0.6, 1.3))
    sphere(0.008, (0.066 * s, -0.142, 0.372), "head", white)
    sphere(0.03, (0.1 * s, -0.11, 0.3), "head", cheek, (1, 0.5, 0.8))
    sphere(0.035, (0.14 * s, 0, 0.33), "head", skin, (0.5, 0.8, 1.0))  # ears
capsule(0.012, (-0.05, -0.135, 0.27), (0.05, -0.135, 0.27), "head", dark, 8)  # smile
sphere(0.13, (0, 0.03, 0.4), "head", hair, (1.05, 1.0, 0.7))
cyl(0.27, 0.02, (0, 0, 0.44), "head", straw, verts=40)  # hat brim
cyl(0.14, 0.12, (0, 0, 0.5), "head", straw, r2=0.12, verts=32)  # crown
cyl(0.143, 0.035, (0, 0, 0.465), "head", band, verts=32)
for s, side in ((1, "L"), (-1, "R")):
    capsule(0.05, (0.17 * s, 0, 0.14), (0.27 * s, 0, 0.0), "arm." + side, shirt)
    capsule(0.042, (0.27 * s, 0, 0.0), (0.31 * s, -0.04, -0.11), "forearm." + side, skin)
    sphere(0.055, (0.32 * s, -0.05, -0.15), "forearm." + side, skin)
    capsule(0.065, (0.08 * s, 0, -0.14), (0.085 * s, 0, -0.27), "leg." + side, denim)
    capsule(0.055, (0.085 * s, 0, -0.27), (0.085 * s, 0, -0.38), "shin." + side, denim)
    sphere(0.075, (0.085 * s, -0.035, -0.41), "shin." + side, boot, (0.85, 1.35, 0.6))
# the little spade in the right hand
capsule(0.014, (-0.33, -0.05, -0.1), (-0.33, -0.08, -0.36), "forearm.R", wood, 8)
spade = cyl(0.07, 0.012, (-0.33, -0.09, -0.4), "forearm.R", metal, rot=(math.pi / 2 - 0.1, 0, 0), verts=6)
spade.scale = (0.8, 1.2, 1.0)
bpy.ops.object.transform_apply(scale=True)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]

# ------------------------------------------------------------------ armature
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm_obj = active()
arm_obj.name = "gardener_rig"
arm = arm_obj.data
eb = arm.edit_bones
eb.remove(eb[0])
BONES = {  # name: (head, tail, parent)
    "root": ((0, 0, -0.45), (0, 0, -0.3), None),
    "hips": ((0, 0, -0.14), (0, 0, 0.0), "root"),
    "spine": ((0, 0, 0.0), (0, 0, 0.2), "hips"),
    "head": ((0, 0, 0.2), (0, 0, 0.5), "spine"),
    "arm.L": ((0.17, 0, 0.14), (0.27, 0, 0.0), "spine"),
    "forearm.L": ((0.27, 0, 0.0), (0.32, -0.05, -0.15), "arm.L"),
    "arm.R": ((-0.17, 0, 0.14), (-0.27, 0, 0.0), "spine"),
    "forearm.R": ((-0.27, 0, 0.0), (-0.32, -0.05, -0.15), "arm.R"),
    "leg.L": ((0.08, 0, -0.14), (0.085, 0, -0.27), "hips"),
    "shin.L": ((0.085, 0, -0.27), (0.085, 0, -0.42), "leg.L"),
    "leg.R": ((-0.08, 0, -0.14), (-0.085, 0, -0.27), "hips"),
    "shin.R": ((-0.085, 0, -0.27), (-0.085, 0, -0.42), "leg.R"),
}
for name, (h, t, p) in BONES.items():
    b = eb.new(name)
    b.head, b.tail = h, t
    b.roll = 0.0
    if p:
        b.parent = eb[p]
        b.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

# rigid skinning: each part fully weighted to its bone, all parts joined into one skinned mesh
for o in meshes:
    vg = o.vertex_groups.new(name=o["bone"])
    vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
for x in bpy.context.selected_objects:
    x.select_set(False)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
body = active()
body.name = "gardener"
mod = body.modifiers.new("rig", "ARMATURE")
mod.object = arm_obj
body.parent = arm_obj

# ------------------------------------------------------------------ animations
pb = arm_obj.pose.bones
for b in pb:
    b.rotation_mode = "XYZ"


def key(action_name, frames):
    """frames: {frame: {bone: (rx, ry, rz) degrees, or ("loc", (x, y, z))}}. Unlisted bones rest."""
    act = bpy.data.actions.new(action_name)
    act.use_fake_user = True
    arm_obj.animation_data_create()
    arm_obj.animation_data.action = act
    for f in sorted(frames):
        for b in pb:
            b.rotation_euler = (0, 0, 0)
            b.location = (0, 0, 0)
        for bone, v in frames[f].items():
            if isinstance(v, tuple) and len(v) == 2 and v[0] == "loc":
                pb[bone].location = v[1]
            else:
                pb[bone].rotation_euler = tuple(math.radians(a) for a in v)
        for b in pb:
            b.keyframe_insert("rotation_euler", frame=f)
            b.keyframe_insert("location", frame=f)
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = action_name
    track.strips.new(action_name, 1, act)
    arm_obj.animation_data.action = None


R = lambda *a: tuple(a)
key("idle", {
    1: {"spine": R(0, 0, 0), "head": R(0, 0, 0), "arm.L": R(0, 0, 4), "arm.R": R(0, 0, -4)},
    30: {"spine": R(4, 0, 0), "head": R(-4, 0, 3), "arm.L": R(0, 0, 8), "arm.R": R(0, 0, -8), "root": ("loc", (0, 0, 0.01))},
    60: {"spine": R(0, 0, 0), "head": R(0, 0, 0), "arm.L": R(0, 0, 4), "arm.R": R(0, 0, -4)},
})
walk = {}
for f, ph in ((1, 1), (6, 0), (11, -1), (16, 0), (21, 1)):
    walk[f] = {
        "leg.L": R(35 * ph, 0, 0), "leg.R": R(-35 * ph, 0, 0),
        "shin.L": R(-30 * max(0, -ph), 0, 0), "shin.R": R(-30 * max(0, ph), 0, 0),
        "arm.L": R(-30 * ph, 0, 6), "arm.R": R(30 * ph, 0, -6),
        "forearm.L": R(-20, 0, 0), "forearm.R": R(-20, 0, 0),
        "spine": R(6, 0, 4 * ph), "head": R(-4, 0, -3 * ph),
        "root": ("loc", (0, 0, 0.035 if ph == 0 else 0.0)),
    }
key("walk", walk)
key("dig", {
    1: {"arm.R": R(-40, 0, 0), "arm.L": R(-40, 0, 0), "forearm.R": R(-30, 0, 0), "forearm.L": R(-30, 0, 0), "spine": R(10, 0, 0)},
    6: {"arm.R": R(-95, 0, 0), "arm.L": R(-80, 0, 0), "forearm.R": R(-10, 0, 0), "forearm.L": R(-20, 0, 0), "spine": R(25, 0, 0),
        "leg.L": R(20, 0, 0), "leg.R": R(-15, 0, 0)},
    11: {"arm.R": R(-20, 0, 0), "arm.L": R(-25, 0, 0), "forearm.R": R(-60, 0, 0), "forearm.L": R(-50, 0, 0), "spine": R(-8, 0, 0)},
    16: {"arm.R": R(-40, 0, 0), "arm.L": R(-40, 0, 0), "forearm.R": R(-30, 0, 0), "forearm.L": R(-30, 0, 0), "spine": R(10, 0, 0)},
})
key("throw", {
    1: {"arm.R": R(0, 0, 0)},
    5: {"arm.R": R(60, 0, -30), "forearm.R": R(-60, 0, 0), "spine": R(-10, 0, -15)},
    9: {"arm.R": R(-120, 0, 10), "forearm.R": R(-10, 0, 0), "spine": R(15, 0, 15), "leg.R": R(-20, 0, 0)},
    14: {"arm.R": R(0, 0, 0)},
})
key("die", {
    1: {},
    8: {"root": ("loc", (0, 0, 0.2)), "arm.L": R(0, 0, 70), "arm.R": R(0, 0, -70), "head": R(-20, 0, 0)},
    16: {"root": ("loc", (0, 0, 0.0)), "spine": R(-30, 0, 0), "arm.L": R(0, 0, 100), "arm.R": R(0, 0, -100),
         "leg.L": R(40, 0, 20), "leg.R": R(40, 0, -20), "head": R(-30, 0, 20)},
    30: {"root": ("loc", (0, 0, -0.05)), "spine": R(-45, 0, 0), "arm.L": R(0, 0, 110), "arm.R": R(0, 0, -110),
         "leg.L": R(60, 0, 25), "leg.R": R(60, 0, -25), "head": R(-35, 0, 25)},
})
key("cheer", {
    1: {},
    6: {"root": ("loc", (0, 0, 0.18)), "arm.L": R(0, 0, 150), "arm.R": R(0, 0, -150), "leg.L": R(-20, 0, 0), "leg.R": R(-20, 0, 0)},
    11: {"root": ("loc", (0, 0, 0.0)), "arm.L": R(0, 0, 135), "arm.R": R(0, 0, -135), "head": R(-10, 0, 0)},
    16: {"root": ("loc", (0, 0, 0.18)), "arm.L": R(0, 0, 150), "arm.R": R(0, 0, -150), "leg.L": R(-20, 0, 0), "leg.R": R(-20, 0, 0)},
    21: {"root": ("loc", (0, 0, 0.0)), "arm.L": R(0, 0, 135), "arm.R": R(0, 0, -135)},
})

for x in bpy.context.selected_objects:
    x.select_set(False)
arm_obj.select_set(True)
body.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "gardener.glb"), use_selection=True, export_format="GLB",
                          export_yup=True, export_apply=False, export_animations=True,
                          export_animation_mode="NLA_TRACKS", export_force_sampling=True)
print("exported gardener")
