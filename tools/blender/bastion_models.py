"""Procedural models for game 2 (Bastion Coast). Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/bastion_models.py -- godot/games/bastion/art/models
One map cell = 1 m. Z is up in Blender (Y up in the exported files). Multi-material objects are GLB.
"""
import bpy, bmesh, math, os, sys, random

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
MATS = {}


def mat(name, color, rough=0.7, metal=0.0, emit=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def box(size, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=False)
    o.data.materials.append(material)
    return o


def cyl(r, depth, loc, material, verts=16, rot=(0, 0, 0), r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.data.materials.append(material)
    return o


def join(parts, name):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    m = o.modifiers.new("b", "BEVEL")
    m.width = 0.015
    m.segments = 1
    m.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.shade_flat()
    return o


def export_glb(name):
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)


def export_obj(name):
    bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, name + ".obj"), export_selected_objects=True,
                          export_materials=False, forward_axis="NEGATIVE_Z", up_axis="Y")
    print("exported", name)


stone = lambda: mat("stone", (0.62, 0.58, 0.52), 0.85)
dark_stone = lambda: mat("dark_stone", (0.42, 0.4, 0.37), 0.9)
roof = lambda: mat("roof", (0.55, 0.16, 0.12), 0.6)
wood = lambda: mat("wood", (0.4, 0.25, 0.13), 0.8)
iron = lambda: mat("iron", (0.18, 0.18, 0.2), 0.35, 0.8)
sail = lambda: mat("sail", (0.93, 0.9, 0.82), 0.9)
flag = lambda: mat("flag", (1.0, 0.75, 0.15), 0.5, 0.0, 0.4)
hull = lambda: mat("hull", (0.3, 0.18, 0.1), 0.7)
enemy = lambda: mat("enemy", (0.75, 0.12, 0.12), 0.6)


def castle():
    """A 2x2-cell keep: square body, four corner towers with cones, crenellations and a flag."""
    reset()
    parts = [box((1.3, 1.3, 1.0), (0, 0, 0.5), stone())]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(0.3, 1.5, (sx * 0.72, sy * 0.72, 0.75), stone(), 12))
            parts.append(cyl(0.36, 0.55, (sx * 0.72, sy * 0.72, 1.77), roof(), 12, r2=0.0))
    for i in range(6):
        t = -0.55 + i * 0.22
        for (x, y) in ((t, -0.62), (t, 0.62), (-0.62, t), (0.62, t)):
            parts.append(box((0.12, 0.12, 0.14), (x, y, 1.07), stone()))
    parts.append(box((0.5, 0.06, 0.55), (0, -0.66, 0.28), wood()))  # gate
    parts.append(cyl(0.025, 0.9, (0, 0, 1.45), wood(), 6))
    parts.append(box((0.42, 0.02, 0.26), (0.22, 0, 1.75), flag()))
    join(parts, "castle")
    export_glb("castle")


def cannon():
    """A 2x2-cell cannon: iron barrel on a wooden carriage with two wheels, on a stone platform."""
    reset()
    parts = [box((1.5, 1.5, 0.16), (0, 0, 0.08), dark_stone())]
    parts.append(box((0.5, 0.8, 0.22), (0, 0, 0.35), wood()))
    for sx in (-1, 1):
        parts.append(cyl(0.26, 0.08, (sx * 0.3, -0.15, 0.4), wood(), 14, rot=(0, math.radians(90), 0)))
    parts.append(cyl(0.14, 1.0, (0, -0.25, 0.62), iron(), 16, rot=(math.radians(80), 0, 0), r2=0.11))
    parts.append(cyl(0.17, 0.14, (0, 0.2, 0.55), iron(), 16, rot=(math.radians(80), 0, 0)))
    join(parts, "cannon")
    export_glb("cannon")


def ship(name, length, masts, color):
    """A ship pointing along -Y: hull with a raised stern, masts with sails and an enemy pennant."""
    reset()
    bm = bmesh.new()
    w, h = length * 0.28, 0.34
    profile = [(0, -length / 2, 0.05), (w, -length * 0.25, 0), (w, length * 0.4, 0), (w * 0.7, length / 2, 0.1),
               (-w * 0.7, length / 2, 0.1), (-w, length * 0.4, 0), (-w, -length * 0.25, 0)]
    bottom = [bm.verts.new((x * 0.6, y * 0.92, z - h)) for x, y, z in profile]
    top = [bm.verts.new((x, y, z + (0.12 if y > length * 0.3 else 0))) for x, y, z in profile]
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bottom[i], bottom[j], top[j], top[i]])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    body = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(body)
    body.data.materials.append(hull())
    parts = [body]
    parts.append(box((w * 1.6, length * 0.2, 0.18), (0, length * 0.36, 0.2), hull()))
    for k in range(masts):
        y = -length * 0.25 + k * (length * 0.55 / max(1, masts - 1) if masts > 1 else 0) + (0.1 if masts == 1 else 0)
        mh = 1.0 + 0.25 * length
        parts.append(cyl(0.035, mh, (0, y, mh / 2), wood(), 6))
        parts.append(box((w * 2.4, 0.03, mh * 0.5), (0, y + 0.04, mh * 0.55), sail()))
        parts.append(box((0.25, 0.02, 0.1), (0.13, y, mh - 0.02), color))
    join(parts, name)
    export_glb(name)


def wall():
    """One wall cell: stone blocks with crenellations on top (instanced, so a single OBJ mesh)."""
    reset()
    random.seed(5)
    parts = [box((0.98, 0.98, 0.55), (0, 0, 0.275), stone())]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.3, 0.3, 0.22), (sx * 0.3, sy * 0.3, 0.66), stone()))
    o = join(parts, "wall")
    export_obj("wall")


def rubble():
    """Broken stones (instanced OBJ)."""
    reset()
    random.seed(9)
    parts = []
    for i in range(7):
        s = random.uniform(0.15, 0.3)
        parts.append(box((s, s * 0.8, s * 0.6), (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), s * 0.3),
                         dark_stone(), rot=(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 3))))
    join(parts, "rubble")
    export_obj("rubble")


def cannonball():
    reset()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.16)
    o = bpy.context.active_object
    o.data.materials.append(iron())
    bpy.ops.object.shade_smooth()
    o.name = "ball"
    export_obj("ball")


castle()
cannon()
ship("ship_small", 1.2, 1, enemy())
ship("ship_medium", 1.7, 2, enemy())
ship("ship_large", 2.3, 3, enemy())
wall()
rubble()
cannonball()
