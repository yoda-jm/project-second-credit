"""Props for game 5 (Frostpeak Games): podium, flagpole, spectator (tinted per instance), snowy pine, torch
cauldron, floodlight tower, finish arch, start gate. Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/frostpeak_models.py -- godot/games/frostpeak/art/models
1 unit = 1 m, Z up in Blender, fronts face -Y. The ice oval and the jump hill are built by the game from the
events' own geometry, so what you see is what the physics uses.
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
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def box(size, loc, material, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
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


SNOW = mat("snow", (0.95, 0.97, 1.0), 0.6)
WOOD = mat("wood", (0.5, 0.35, 0.22), 0.8)
STEEL = mat("steel", (0.7, 0.72, 0.76), 0.35, 0.9)


def podium():
    white = mat("podium", (0.95, 0.95, 0.97), 0.4, coat=0.3)
    gold = mat("podium_gold", (1.0, 0.8, 0.3), 0.3, 1.0)
    silver = mat("podium_silver", (0.8, 0.82, 0.86), 0.3, 1.0)
    bronze = mat("podium_bronze", (0.8, 0.5, 0.3), 0.35, 1.0)
    parts = [box((1.4, 1.2, 1.2), (0, 0, 0.6), white), box((1.4, 1.2, 0.85), (-1.45, 0, 0.425), white),
             box((1.4, 1.2, 0.55), (1.45, 0, 0.275), white)]
    for x, z, m in ((0, 1.2, gold), (-1.45, 0.85, silver), (1.45, 0.55, bronze)):
        parts.append(box((1.3, 0.04, 0.3), (x, -0.61, z - 0.3), m, bevel=0.01))
    export(parts, "podium")


def flagpole():
    export([cyl(0.05, 8.0, (0, 0, 4.0), STEEL, verts=12), sphere(0.1, (0, 0, 8.05), mat("pole_ball", (1.0, 0.8, 0.3), 0.3, 1.0))],
           "flagpole")


def spectator():
    """One spectator; the game tints the coat per instance (material "coat" is white)."""
    coat = mat("coat", (1, 1, 1), 0.8)
    skin = mat("face", (0.92, 0.72, 0.58), 0.6)
    dark = mat("trousers", (0.15, 0.15, 0.2), 0.8)
    hat = mat("bobble_hat", (0.95, 0.95, 0.95), 0.9)
    parts = [cyl(0.2, 0.6, (0, 0, 1.0), coat, r2=0.16, verts=10), sphere(0.13, (0, 0, 1.42), skin),
             cyl(0.14, 0.12, (0, 0, 1.52), hat, verts=10), sphere(0.06, (0, 0, 1.62), hat),
             cyl(0.08, 0.7, (0.09, 0, 0.35), dark, verts=8), cyl(0.08, 0.7, (-0.09, 0, 0.35), dark, verts=8)]
    for s in (-1, 1):  # arms raised a little, cheering
        parts.append(cyl(0.06, 0.55, (0.26 * s, 0, 1.3), coat, rot=(0, 0.5 * s, 0), verts=8))
    export(parts, "spectator")


def snowy_pine():
    needles = mat("pine_needles", (0.12, 0.3, 0.18), 0.8)
    parts = [cyl(0.12, 1.2, (0, 0, 0.6), WOOD, verts=8)]
    for i, (r, z) in enumerate(((1.6, 1.6), (1.25, 2.6), (0.9, 3.5), (0.55, 4.3))):
        parts.append(cyl(r, 1.4, (0, 0, z), needles, r2=0.05, verts=12, smooth=False))
        parts.append(cyl(r * 0.8, 0.5, (0, 0, z + 0.05), SNOW, r2=r * 0.25, verts=12))  # snow caps
    export(parts, "snowy_pine")


def cauldron():
    bronze = mat("cauldron", (0.75, 0.5, 0.25), 0.35, 1.0)
    flame = mat("flame", (1.0, 0.55, 0.15), 0.5, emit=8.0)
    parts = [cyl(0.25, 2.5, (0, 0, 1.25), STEEL, r2=0.18, verts=16), cyl(1.0, 0.7, (0, 0, 2.8), bronze, r2=0.6, verts=24)]
    for i in range(5):
        a = i * 2 * math.pi / 5
        parts.append(cyl(0.35 - i * 0.03, 1.4 - i * 0.12, (0.25 * math.cos(a), 0.25 * math.sin(a), 3.6), flame, r2=0.02, verts=10))
    export(parts, "cauldron")


def floodlight():
    lamp = mat("flood_lamp", (1.0, 0.97, 0.9), 0.3, emit=5.0)
    parts = [cyl(0.2, 18.0, (0, 0, 9.0), STEEL, verts=10), box((3.0, 0.4, 1.6), (0, 0.1, 18.4), STEEL)]
    for i in range(4):
        for k in range(2):
            parts.append(box((0.6, 0.1, 0.6), (-1.05 + i * 0.7, -0.12, 18.05 + k * 0.7), lamp, bevel=0.01))
    export(parts, "floodlight")


def finish_arch():
    red = mat("arch_red", (0.85, 0.1, 0.12), 0.5)
    parts = [box((0.4, 0.4, 5.0), (-5.5, 0, 2.5), red), box((0.4, 0.4, 5.0), (5.5, 0, 2.5), red),
             box((11.4, 0.5, 1.0), (0, 0, 5.2), red), box((10.0, 0.52, 0.5), (0, 0, 5.2), mat("arch_white", (1, 1, 1), 0.5))]
    export(parts, "finish_arch")


def start_gate():
    parts = [box((3.0, 1.2, 0.2), (0, 0, 0.1), WOOD), box((0.15, 0.15, 1.6), (-1.4, 0, 0.8), STEEL),
             box((0.15, 0.15, 1.6), (1.4, 0, 0.8), STEEL), box((3.0, 0.2, 0.3), (0, 0, 1.5), mat("gate_blue", (0.1, 0.3, 0.8), 0.4))]
    export(parts, "start_gate")


reset()
podium()
flagpole()
spectator()
snowy_pine()
cauldron()
floodlight()
finish_arch()
start_gate()
