"""Whisker Alley's animals: the cat (a ginger tabby with a torn ear) and the bulldog, built by one four-legged
builder, rigidly bound to an armature, with keyed animations. Deterministic; output CC BY-SA 4.0; provenance:
this script.
Run: blender -b --factory-startup -P tools/blender/whisker_animals.py -- godot/games/whisker/art/models
Feet at z = 0, facing -Y (the view turns them to face left or right). One glTF animation per action.
"""
import bpy, math, os, sys
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
FPS = 30
MATS = {}


def mat(name, color, rough=0.6, coat=0.0, emit=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def active():
    return bpy.context.active_object


def tag(o, bone, material):
    o.data.materials.clear()
    o.data.materials.append(material)
    o["bone"] = bone
    bpy.ops.object.shade_smooth()
    return o


def sphere(r, loc, bone, material, scale=(1, 1, 1), segs=24, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return tag(o, bone, material)


def cone(r1, r2, depth, loc, bone, material, rot=(0, 0, 0), verts=12):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    return tag(active(), bone, material)


def capsule(r, a, b, bone, material, r2=None, verts=14):
    a, b = Vector(a), Vector(b)
    d = b - a
    r2 = r if r2 is None else r2
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = active()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    parts = [o]
    for p, rr in ((a, r), (b, r2)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=verts, ring_count=8, radius=rr, location=p)
        parts.append(active())
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for x in parts:
        x.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    return tag(active(), bone, material)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for a in list(bpy.data.armatures):
        bpy.data.armatures.remove(a)


def rig_and_export(name, bones, actions):
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm_obj = active()
    arm_obj.name = name + "_rig"
    eb = arm_obj.data.edit_bones
    eb.remove(eb[0])
    for bname, (h, t, p) in bones.items():
        b = eb.new(bname)
        b.head, b.tail = h, t
        b.roll = 0.0
        if p:
            b.parent = eb[p]
    bpy.ops.object.mode_set(mode="OBJECT")
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
    body.name = name
    mod = body.modifiers.new("rig", "ARMATURE")
    mod.object = arm_obj
    body.parent = arm_obj
    pb = arm_obj.pose.bones
    for b in pb:
        b.rotation_mode = "XYZ"
    arm_obj.animation_data_create()
    for aname, frames in actions.items():
        act = bpy.data.actions.new(aname)
        act.use_fake_user = True
        arm_obj.animation_data.action = act
        for f in sorted(frames):
            for b in pb:
                b.rotation_euler = (0, 0, 0)
                b.location = (0, 0, 0)
            for bone, v in frames[f].items():
                if bone.startswith("@"):
                    pb[bone[1:]].location = v
                else:
                    pb[bone].rotation_euler = tuple(math.radians(a) for a in v)
            for b in pb:
                b.keyframe_insert("rotation_euler", frame=f)
                b.keyframe_insert("location", frame=f)
        tr = arm_obj.animation_data.nla_tracks.new()
        tr.name = aname
        tr.strips.new(aname, 1, act)
        arm_obj.animation_data.action = None
    for x in bpy.context.selected_objects:
        x.select_set(False)
    arm_obj.select_set(True)
    body.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True)
    print("exported", name)


def quad_bones(hip_z, leg_x, front_y, back_y, shoulder_z, head_y, head_z, tail_y, tail_z, tail_n, tail_seg, tail_rise):
    b = {
        "root": ((0, 0, 0), (0, 0, 0.1), None),
        "body": ((0, back_y, hip_z), (0, front_y, shoulder_z), "root"),
        "head": ((0, front_y, shoulder_z), (0, head_y, head_z), "body"),
    }
    for side, sx in (("L", 1), ("R", -1)):
        for end, y, z0 in (("f", front_y, shoulder_z), ("b", back_y, hip_z)):
            b[f"leg_{end}{side}"] = ((sx * leg_x, y, z0), (sx * leg_x, y, z0 * 0.45), "body")
            b[f"paw_{end}{side}"] = ((sx * leg_x, y, z0 * 0.45), (sx * leg_x, y, 0.0), f"leg_{end}{side}")
    prev = "body"
    y, z = tail_y, tail_z
    for i in range(tail_n):
        ny, nz = y + tail_seg, z + tail_rise * (1 - i / tail_n)
        b[f"tail{i}"] = ((0, y, z), (0, ny, nz), prev)
        prev = f"tail{i}"
        y, z = ny, nz
    return b


def gait(amp, lift, body_bob, tail_n, frames=(1, 5, 9, 13, 17)):
    """A four-legged walk: diagonal pairs swing together."""
    out = {}
    for f, ph in zip(frames, (1, 0, -1, 0, 1)):
        k = {
            "leg_fL": (amp * ph, 0, 0), "leg_bR": (amp * ph, 0, 0),
            "leg_fR": (-amp * ph, 0, 0), "leg_bL": (-amp * ph, 0, 0),
            "paw_fL": (-lift * max(0, -ph), 0, 0), "paw_fR": (-lift * max(0, ph), 0, 0),
            "paw_bL": (lift * max(0, ph), 0, 0), "paw_bR": (lift * max(0, -ph), 0, 0),
            "head": (-3 * ph, 0, 0), "@root": (0, 0, body_bob if ph == 0 else 0.0),
        }
        for i in range(tail_n):
            k[f"tail{i}"] = (0, 0, 8 * ph * (i + 1) / tail_n)
        out[f] = k
    return out


# ================================================================== the cat
clear_scene()
fur = mat("cat_fur", (0.86, 0.46, 0.16), 0.8)
dark = mat("cat_stripes", (0.55, 0.24, 0.08), 0.85)
cream = mat("cat_cream", (0.98, 0.9, 0.78), 0.8)
pink = mat("cat_pink", (0.95, 0.55, 0.6), 0.5)
eye = mat("cat_eye", (0.45, 0.85, 0.2), 0.1, coat=1.0, emit=0.4)
pupil = mat("cat_pupil", (0.02, 0.02, 0.02), 0.1, coat=1.0)
whisk = mat("cat_whisker", (0.95, 0.95, 0.9), 0.4)
HZ, SZ, FY, BY = 0.3, 0.32, -0.22, 0.2
sphere(0.2, (0, -0.02, 0.31), "body", fur, (0.95, 1.55, 0.92))
sphere(0.16, (0, -0.2, 0.33), "body", cream, (0.9, 1.0, 0.9))  # chest
for k, y in enumerate((-0.1, 0.02, 0.14, 0.24)):  # tabby stripes over the back
    sphere(0.1, (0, y, 0.41 - abs(y) * 0.1), "body", dark, (1.75, 0.35, 0.72))
sphere(0.15, (0, -0.38, 0.5), "head", fur, (1.05, 0.95, 0.92), 32, 18)
sphere(0.075, (0, -0.5, 0.45), "head", cream, (1.2, 0.9, 0.8))  # muzzle
sphere(0.022, (0, -0.57, 0.48), "head", pink, (1.3, 0.8, 0.9))  # nose
for s in (-1, 1):
    sphere(0.042, (0.06 * s, -0.5, 0.54), "head", eye, (1, 0.6, 1.1))
    sphere(0.02, (0.064 * s, -0.525, 0.54), "head", pupil, (0.45, 0.5, 1.4))
    ear = cone(0.06, 0.005, 0.12, (0.09 * s, -0.36, 0.64), "head", fur, rot=(0.25, 0.3 * s, 0))
    cone(0.035, 0.004, 0.08, (0.09 * s, -0.385, 0.635), "head", pink, rot=(0.25, 0.3 * s, 0))
    for k in (-1, 0, 1):
        capsule(0.004, (0.05 * s, -0.54, 0.45 + 0.012 * k), (0.2 * s, -0.56, 0.44 + 0.04 * k), "head", whisk, 0.002, 6)
# the torn ear: a notch of stripe colour on the left ear
sphere(0.018, (0.1, -0.38, 0.67), "head", dark)
for side, sx in (("L", 1), ("R", -1)):
    for end, y in (("f", FY), ("b", BY)):
        capsule(0.05, (sx * 0.09, y, 0.27), (sx * 0.09, y, 0.12), f"leg_{end}{side}", fur, 0.042)
        capsule(0.04, (sx * 0.09, y, 0.12), (sx * 0.09, y - 0.02, 0.03), f"paw_{end}{side}", fur, 0.035)
        sphere(0.045, (sx * 0.09, y - 0.035, 0.025), f"paw_{end}{side}", cream, (1, 1.3, 0.6))
TN, TS = 5, 0.09
y, z = 0.3, 0.36
for i in range(TN):
    ny, nz = y + TS, z + 0.07 * (1 - i / TN)
    capsule(0.04 - i * 0.005, (0, y, z), (0, ny, nz), f"tail{i}", dark if i == TN - 1 else fur, 0.035 - i * 0.005, 10)
    y, z = ny, nz
bones = quad_bones(HZ, 0.09, FY, BY, SZ, -0.5, 0.55, 0.3, 0.36, TN, TS, 0.07)
idle = {}
for f, ph in ((1, 0), (20, 1), (40, 0), (60, -1), (80, 0)):
    k = {"head": (4 * ph, 0, 6 * ph), "@root": (0, 0, 0.004 * abs(ph))}
    for i in range(TN):
        k[f"tail{i}"] = (6 * ph, 0, 14 * ph * (i + 1) / TN)
    idle[f] = k
walk = gait(28, 30, 0.02, TN)
run = gait(45, 50, 0.04, TN, frames=(1, 3, 5, 7, 9))
jump = {1: {"leg_fL": (-50, 0, 0), "leg_fR": (-50, 0, 0), "leg_bL": (40, 0, 0), "leg_bR": (40, 0, 0), "head": (-12, 0, 0),
            "body": (-10, 0, 0), "tail0": (25, 0, 0), "tail1": (15, 0, 0)},
        10: {"leg_fL": (-60, 0, 0), "leg_fR": (-60, 0, 0), "leg_bL": (50, 0, 0), "leg_bR": (50, 0, 0), "head": (-15, 0, 0),
             "body": (-12, 0, 0), "tail0": (30, 0, 0), "tail1": (20, 0, 0)}}
fall = {1: {"leg_fL": (-25, 0, 10), "leg_fR": (-25, 0, -10), "leg_bL": (20, 0, 10), "leg_bR": (20, 0, -10), "head": (10, 0, 0),
            "body": (8, 0, 0), "tail0": (-20, 0, 0), "tail1": (-20, 0, 0)},
        10: {"leg_fL": (-30, 0, 14), "leg_fR": (-30, 0, -14), "leg_bL": (25, 0, 14), "leg_bR": (25, 0, -14), "head": (12, 0, 0),
             "body": (8, 0, 0), "tail0": (-25, 0, 5), "tail1": (-25, 0, -5)}}
swim = {}
for f, ph in ((1, 1), (6, -1), (11, 1)):
    swim[f] = {"leg_fL": (-40 * ph - 30, 0, 0), "leg_fR": (40 * ph - 30, 0, 0), "leg_bL": (30 * ph + 20, 0, 0),
               "leg_bR": (-30 * ph + 20, 0, 0), "head": (-20, 0, 0), "body": (-15, 0, 0), "tail0": (10, 0, 8 * ph)}
catch = {1: {}, 5: {"head": (30, 0, 0), "body": (15, 0, 0), "leg_fL": (-60, 0, 0), "leg_fR": (-60, 0, 0), "@root": (0, 0, 0.05)},
         12: {"head": (10, 0, 0), "leg_fL": (-10, 0, 0), "leg_fR": (-10, 0, 0)}, 18: {}}
die = {1: {}, 10: {"body": (0, 70, 0), "@root": (0, 0, 0.25), "leg_fL": (-40, 0, 30), "leg_bL": (40, 0, 30)},
       20: {"body": (0, 170, 0), "@root": (0, 0, 0.3), "leg_fL": (-60, 0, 40), "leg_fR": (-60, 0, -40), "leg_bL": (60, 0, 40),
            "leg_bR": (60, 0, -40), "head": (-20, 0, 0)},
       30: {"body": (0, 180, 0), "@root": (0, 0, 0.32), "leg_fL": (-70, 0, 45), "leg_fR": (-70, 0, -45), "leg_bL": (70, 0, 45),
            "leg_bR": (70, 0, -45), "head": (-25, 0, 20)}}
cheer = {}
for f, ph in ((1, 0), (6, 1), (11, 0), (16, 1), (21, 0)):
    k = {"leg_fL": (-70 * ph, 0, 0), "body": (-25 * ph, 0, 0), "head": (-15 * ph, 0, 10 * ph), "@root": (0, 0, 0.12 * ph)}
    for i in range(TN):
        k[f"tail{i}"] = (-15, 0, 20 * (1 if ph else -1) * (i + 1) / TN)
    cheer[f] = k
rig_and_export("cat", bones, {"idle": idle, "walk": walk, "run": run, "jump": jump, "fall": fall, "swim": swim,
                              "catch": catch, "die": die, "cheer": cheer})

# ================================================================== the bulldog
clear_scene()
coat_c = mat("dog_coat", (0.6, 0.42, 0.28), 0.8)
white = mat("dog_white", (0.95, 0.92, 0.86), 0.8)
black = mat("dog_nose", (0.05, 0.04, 0.04), 0.3, coat=0.8)
jowl = mat("dog_jowl", (0.6, 0.45, 0.35), 0.8)
collar = mat("dog_collar", (0.8, 0.1, 0.1), 0.4)
stud = mat("dog_studs", (0.85, 0.85, 0.8), 0.2)
tooth = mat("dog_teeth", (1, 0.97, 0.9), 0.3)
dog_eye = mat("dog_eye", (0.1, 0.06, 0.03), 0.1, coat=1.0)
HZ, SZ, FY, BY = 0.42, 0.46, -0.3, 0.3
sphere(0.3, (0, 0.0, 0.46), "body", coat_c, (1.1, 1.4, 0.85))
sphere(0.24, (0, -0.28, 0.46), "body", white, (1.1, 0.8, 0.9))  # broad chest
capsule(0.13, (-0.0, -0.36, 0.62), (0, -0.36, 0.62), "body", collar, 0.13)
for s in range(-3, 4):
    sphere(0.02, (0.13 * math.sin(s * 0.45), -0.48 + 0.02 * abs(s), 0.62 + 0.13 * math.cos(s * 0.45) * 0.2), "body", stud)
sphere(0.24, (0, -0.55, 0.66), "head", coat_c, (1.15, 0.9, 0.85), 32, 18)
sphere(0.16, (0, -0.72, 0.58), "head", jowl, (1.5, 0.8, 0.8))  # jowls
sphere(0.05, (0, -0.84, 0.66), "head", black, (1.3, 0.8, 0.8))
for s in (-1, 1):
    sphere(0.035, (0.1 * s, -0.74, 0.74), "head", dog_eye)
    sphere(0.08, (0.2 * s, -0.5, 0.82), "head", jowl, (0.6, 1.0, 1.1))  # ears
    cone(0.02, 0.003, 0.05, (0.07 * s, -0.84, 0.53), "head", tooth, rot=(0, 0, 0))
    capsule(0.03, (0.16 * s, -0.75, 0.73), (0.05 * s, -0.8, 0.76), "head", jowl, 0.02, 8)  # frowning brow
for side, sx in (("L", 1), ("R", -1)):
    for end, y in (("f", FY), ("b", BY)):
        capsule(0.08, (sx * 0.16, y, 0.4), (sx * 0.17, y, 0.18), f"leg_{end}{side}", coat_c, 0.07)
        capsule(0.065, (sx * 0.17, y, 0.18), (sx * 0.17, y - 0.03, 0.05), f"paw_{end}{side}", coat_c, 0.06)
        sphere(0.07, (sx * 0.17, y - 0.05, 0.04), f"paw_{end}{side}", white, (1, 1.2, 0.6))
capsule(0.035, (0, 0.4, 0.55), (0, 0.46, 0.66), "tail0", coat_c, 0.02, 8)
bones = quad_bones(HZ, 0.17, FY, BY, SZ, -0.8, 0.7, 0.4, 0.55, 1, 0.1, 0.1)
walk = gait(24, 25, 0.02, 1)
run = gait(38, 40, 0.05, 1, frames=(1, 3, 5, 7, 9))
bark = {1: {}, 4: {"head": (-25, 0, 0), "body": (-6, 0, 0), "@root": (0, 0, 0.03)}, 8: {"head": (5, 0, 0)}, 12: {}}
idle = {1: {"tail0": (0, 0, 20)}, 8: {"tail0": (0, 0, -20), "head": (3, 0, 5)}, 16: {"tail0": (0, 0, 20)}}
rig_and_export("bulldog", bones, {"idle": idle, "walk": walk, "run": run, "bark": bark})
