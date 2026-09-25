"""Shared humanoid builder for Blender scripts: materials, rigidly bound parts (each part follows one bone), a
standard biped armature (with ski bones under the feet), keyed actions and glTF export with one animation per
action. Used by frostpeak_athletes.py and boots_models.py. Output CC BY-SA 4.0.
About 1.8 m tall at scale 1, feet at z = 0, facing -Y.
"""
import bpy, bmesh, math, os
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


def _loft(ring_pts, material, bone, subsurf=1):
    """A closed, capped surface through rings of points (each ring the same count), bottom to top."""
    me = bpy.data.meshes.new("loft")
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in ring] for ring in ring_pts]
    n = len(rings[0])
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("loft", me)
    bpy.context.collection.objects.link(o)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    if subsurf:
        m = o.modifiers.new("s", "SUBSURF")
        m.levels = subsurf
        bpy.ops.object.modifier_apply(modifier=m.name)
    return tag(o, bone, material)


def body_loft(rings, bone, material, segs=20, subsurf=1):
    """A torso-like part through horizontal ellipses [(z, half width, half depth, y offset)], bottom to top."""
    pts = []
    for z, rx, ry, *rest in rings:
        cy = rest[0] if rest else 0.0
        pts.append([(rx * math.cos(2 * math.pi * i / segs), cy + ry * math.sin(2 * math.pi * i / segs), z) for i in range(segs)])
    return _loft(pts, material, bone, subsurf)


def muscle_limb(points, bone, material, segs=14, subsurf=1):
    """A limb swept along [(x, y, z, radius)] with rings square to the path: bulges and tapers where you ask."""
    pts = [Vector(p[:3]) for p in points]
    rings = []
    for k, p in enumerate(pts):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        a = d.orthogonal().normalized()
        b = d.cross(a).normalized()
        r = points[k][3]
        rings.append([tuple(p + (a * math.cos(2 * math.pi * i / segs) + b * math.sin(2 * math.pi * i / segs)) * r) for i in range(segs)])
    return _loft(rings, material, bone, subsurf)


def head_detailed(skin, eye_white, iris, center=(0, 0, 1.66), hair=None):
    """A head with a jaw, nose, ears, eyes and (optionally) hair, on the "head" bone."""
    cx, cy, cz = center
    sphere(0.1, (cx, cy + 0.005, cz), "head", skin, (0.92, 1.0, 1.12), 32, 18)
    sphere(0.075, (cx, cy - 0.03, cz - 0.06), "head", skin, (1.0, 0.95, 0.8))  # jaw and chin
    sphere(0.02, (cx, cy - 0.1, cz - 0.01), "head", skin, (0.8, 1.2, 1.1))     # nose
    for s in (-1, 1):
        sphere(0.025, (cx + 0.09 * s, cy + 0.005, cz), "head", skin, (0.5, 0.9, 1.3))  # ears
        sphere(0.016, (cx + 0.035 * s, cy - 0.085, cz + 0.02), "head", eye_white, (1.2, 0.7, 0.9))
        sphere(0.008, (cx + 0.035 * s, cy - 0.097, cz + 0.02), "head", iris)
    if hair:
        sphere(0.104, (cx, cy + 0.02, cz + 0.035), "head", hair, (0.95, 1.02, 0.9))


def hand(center, side, bone, material):
    """A relaxed hand: palm, a mitten of fingers and a thumb."""
    x, y, z = center
    sphere(0.035, (x, y, z), bone, material, (0.8, 1.1, 1.2))
    muscle_limb([(x, y - 0.005, z - 0.02, 0.028), (x, y - 0.01, z - 0.06, 0.026), (x, y - 0.02, z - 0.085, 0.018)], bone, material, 10, 1)
    muscle_limb([(x - 0.025 * side, y - 0.02, z, 0.013), (x - 0.035 * side, y - 0.04, z - 0.03, 0.011)], bone, material, 8, 0)


def athletic_body(suit, skin, eye_white, iris, hair=None, glove=None, boot=None, legs=None):
    """A proportioned 1.8 m figure bound to BONES: pelvis, chest, neck, head, arms with hands, legs with feet.
    Parts overlap at the joints, and a rounded cap sits on each joint, so no gap opens when the rig bends."""
    legs = legs or suit
    body_loft([(0.84, 0.12, 0.085), (0.9, 0.16, 0.1), (0.98, 0.175, 0.108), (1.06, 0.162, 0.104), (1.14, 0.146, 0.098)], "hips", legs)
    body_loft([(1.02, 0.155, 0.1), (1.12, 0.143, 0.095), (1.2, 0.156, 0.102), (1.29, 0.178, 0.112, -0.005),
               (1.37, 0.196, 0.108), (1.42, 0.2, 0.096), (1.47, 0.14, 0.08), (1.5, 0.07, 0.055)], "spine", suit)
    muscle_limb([(0, 0, 1.42, 0.054), (0, -0.005, 1.5, 0.048), (0, -0.01, 1.6, 0.046)], "head", skin, 12, 1)
    head_detailed(skin, eye_white, iris, hair=hair)
    for s, side in ((1, "L"), (-1, "R")):
        sphere(0.064, (0.19 * s, 0, 1.415), "spine", suit, (1.1, 1.0, 0.95))      # shoulder
        muscle_limb([(0.195 * s, 0, 1.46, 0.056), (0.225 * s, 0, 1.3, 0.053), (0.252 * s, 0, 1.1, 0.043)], "arm." + side, suit)
        sphere(0.044, (0.25 * s, 0, 1.13), "forearm." + side, suit)              # elbow
        muscle_limb([(0.249 * s, 0, 1.17, 0.042), (0.26 * s, -0.01, 1.03, 0.045), (0.27 * s, -0.022, 0.87, 0.031)], "forearm." + side, suit)
        sphere(0.032, (0.269 * s, -0.021, 0.885), "forearm." + side, glove or skin)  # wrist
        hand((0.27 * s, -0.022, 0.86), s, "forearm." + side, glove or skin)
        sphere(0.085, (0.1 * s, 0, 0.93), "thigh." + side, legs)                 # hip joint
        muscle_limb([(0.1 * s, 0, 0.98, 0.084), (0.1 * s, -0.01, 0.75, 0.075), (0.1 * s, 0, 0.49, 0.054)], "thigh." + side, legs)
        sphere(0.056, (0.1 * s, -0.006, 0.52), "shin." + side, legs)             # knee
        muscle_limb([(0.1 * s, 0, 0.56, 0.053), (0.1 * s, 0.012, 0.4, 0.059), (0.1 * s, 0, 0.2, 0.038), (0.1 * s, 0, 0.08, 0.034)], "shin." + side, legs)
        if boot:
            body_loft([(0.0, 0.052, 0.11, -0.04), (0.07, 0.054, 0.115, -0.04), (0.12, 0.046, 0.065, 0.0), (0.17, 0.04, 0.045)], "shin." + side, boot)
            active().location.x = 0.1 * s  # body_loft is centred on x = 0: move the boot under this leg


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
