"""Neon Knuckles props: weapons (bat, knife, crate), a burning oil barrel and trash bags. The buildings, cars, street
furniture, docks and rooftop kits are in knuckles_city.py. Deterministic; output CC BY-SA 4.0;
provenance: this script.
Run: blender -b --factory-startup -P tools/blender/knuckles_props.py -- godot/games/knuckles/art/models
"""
import bpy, math, os, sys, random

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
MATS = {}


def mat(name, color, rough=0.6, metal=0.0, emit=0.0, coat=0.0):
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
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def active():
    return bpy.context.active_object


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


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


def box(size, loc, material, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return put(o, material, bevel=bevel)


def cyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=20, smooth=True):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return put(active(), material, smooth)


def sphere(r, loc, material, scale=(1, 1, 1), segs=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active()
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
    active().name = name
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)
    reset()


def bat():
    wood = mat("bat_wood", (0.72, 0.5, 0.28), 0.45, coat=0.4)
    tape = mat("bat_tape", (0.1, 0.1, 0.1), 0.7)
    export([cyl(0.02, 0.3, (0, 0, 0.15), tape, verts=12), cyl(0.022, 0.6, (0, 0, 0.6), wood, r2=0.04, verts=16),
            sphere(0.04, (0, 0, 0.9), wood)], "bat")  # grip at the origin, along +Z


def knife():
    steel = mat("blade", (0.85, 0.87, 0.9), 0.15, 1.0)
    grip = mat("knife_grip", (0.15, 0.1, 0.08), 0.6)
    export([box((0.025, 0.02, 0.12), (0, 0, 0.06), grip), box((0.05, 0.02, 0.012), (0, 0, 0.125), steel),
            box((0.03, 0.004, 0.18), (0, 0, 0.22), steel, bevel=0.002)], "knife")


def crate():
    wood = mat("crate_wood", (0.6, 0.45, 0.25), 0.8)
    dark = mat("crate_dark", (0.35, 0.25, 0.14), 0.8)
    parts = [box((0.6, 0.6, 0.6), (0, 0, 0.3), wood, bevel=0.02)]
    for sx in (-1, 1):
        parts.append(box((0.62, 0.62, 0.06), (0, 0, 0.3 + sx * 0.25), dark))
    parts.append(box((0.06, 0.62, 0.62), (0, 0, 0.3), dark, rot=(0.78, 0, 0)))
    export(parts, "crate")


def barrel():
    steel = mat("barrel", (0.2, 0.3, 0.55), 0.5, 0.6)
    ring = mat("barrel_ring", (0.15, 0.2, 0.35), 0.5, 0.6)
    fire = mat("barrel_fire", (1.0, 0.5, 0.15), 0.5, emit=6.0)
    parts = [cyl(0.3, 0.9, (0, 0, 0.45), steel, verts=24)]
    for z in (0.2, 0.7):
        parts.append(cyl(0.31, 0.04, (0, 0, z), ring, verts=24))
    for k in range(4):  # a fire burning in the barrel
        a = k * math.pi / 2
        parts.append(cyl(0.12, 0.35, (0.1 * math.cos(a), 0.1 * math.sin(a), 1.0), fire, r2=0.0, verts=8))
    export(parts, "barrel")


def trash_bags():
    bag = mat("trash_bag", (0.05, 0.05, 0.06), 0.3, coat=0.6)
    rnd = random.Random(2)
    parts = [sphere(rnd.uniform(0.25, 0.35), (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.3, 0.3), 0.25), bag, (1, 1, 0.85)) for _ in range(4)]
    export(parts, "trash_bags")


reset()
bat()
knife()
crate()
barrel()
trash_bags()
