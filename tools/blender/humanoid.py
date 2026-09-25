"""Shared humanoid builder for Blender scripts: materials, rigidly bound parts (each part follows one bone), a
standard biped armature (with ski bones under the feet), keyed actions and glTF export with one animation per
action. Used by frostpeak_athletes.py and boots_models.py. Output CC BY-SA 4.0.
About 1.8 m tall at scale 1, feet at z = 0, facing -Y.
"""
import bpy, math, os
from mathutils import Vector

MATS = {}


def mat(name, color, rough=0.5, metal=0.0, coat=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
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


def box(size, loc, bone, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    b = o.modifiers.new("b", "BEVEL")
    b.width = min(size) * 0.3
    b.segments = 2
    bpy.ops.object.modifier_apply(modifier=b.name)
    return tag(o, bone, material)


def limb(r, a, b, bone, material, r2=None, verts=16):
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


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, 0, 0.95), (0, 0, 1.1), "root"),
    "spine": ((0, 0, 1.1), (0, 0, 1.45), "hips"),
    "head": ((0, 0, 1.45), (0, 0, 1.8), "spine"),
    "arm.L": ((0.2, 0, 1.42), (0.24, 0, 1.12), "spine"),
    "forearm.L": ((0.24, 0, 1.12), (0.26, -0.02, 0.86), "arm.L"),
    "arm.R": ((-0.2, 0, 1.42), (-0.24, 0, 1.12), "spine"),
    "forearm.R": ((-0.24, 0, 1.12), (-0.26, -0.02, 0.86), "arm.R"),
    "thigh.L": ((0.1, 0, 0.95), (0.1, 0, 0.52), "hips"),
    "shin.L": ((0.1, 0, 0.52), (0.1, 0, 0.08), "thigh.L"),
    "thigh.R": ((-0.1, 0, 0.95), (-0.1, 0, 0.52), "hips"),
    "shin.R": ((-0.1, 0, 0.52), (-0.1, 0, 0.08), "thigh.R"),
    "ski.L": ((0.1, 0, 0.04), (0.1, -0.3, 0.04), "shin.L"),
    "ski.R": ((-0.1, 0, 0.04), (-0.1, -0.3, 0.04), "shin.R"),
}




def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for a in list(bpy.data.armatures):
        bpy.data.armatures.remove(a)


def keys(arm_obj, name, frames):
    pb = arm_obj.pose.bones
    act = bpy.data.actions.new(name)
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
    tr.name = name
    tr.strips.new(name, 1, act)
    arm_obj.animation_data.action = None



def rig_export(name, out_dir, actions, scale=1.0):
    """Binds every mesh in the scene (each tagged with its bone) to a new biped armature, keys `actions`
    ({name: {frame: {bone: (rx, ry, rz) degrees, or "@bone": location}}}) and exports name.glb."""
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm_obj = active()
    arm_obj.name = name + "_rig"
    eb = arm_obj.data.edit_bones
    eb.remove(eb[0])
    for n, (h, t, p) in BONES.items():
        b = eb.new(n)
        b.head, b.tail = h, t
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
    mesh = active()
    mesh.name = name
    mod = mesh.modifiers.new("rig", "ARMATURE")
    mod.object = arm_obj
    mesh.parent = arm_obj
    for b in arm_obj.pose.bones:
        b.rotation_mode = "XYZ"
    arm_obj.animation_data_create()
    for aname, frames in actions.items():
        keys(arm_obj, aname, frames)
    arm_obj.scale = (scale, scale, scale)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    arm_obj.select_set(True)
    mesh.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True)
    print("exported", name)
