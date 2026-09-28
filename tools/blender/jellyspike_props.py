"""Jelly Spike props for the launcher and menus: a jelly blob (blue and red) with eyes, and a striped beach ball.
Our own simple designs, made from primitives here; CC BY-SA 4.0 like the other game assets. Materials are named so
a game could recolour them. Usage:
  .tools/bin/blender -b --factory-startup -P tools/blender/jellyspike_props.py -- godot/games/jellyspike/art/models"""
import sys, math, bpy

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "godot/games/jellyspike/art/models"


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, col, rough=0.2, alpha=1.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1.0)
    b.inputs["Roughness"].default_value = rough
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    if emit > 0.0:
        b.inputs["Emission Color"].default_value = (*col, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    return m


def sphere(r, loc=(0, 0, 0), segs=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    return o


def export(name):
    bpy.ops.export_scene.gltf(filepath=f"{out}/{name}.glb", export_format="GLB", use_selection=False,
                              export_apply=True)


for name, col in [("blob_blue", (0.1, 0.55, 1.0)), ("blob_red", (1.0, 0.28, 0.22))]:
    reset()
    body = sphere(0.62, (0, 0, 0.62), 48, 24)
    body.scale = (1.05, 0.95, 1.12)  # Blender z up: a slightly tall jelly dome
    body.data.materials.append(mat(name + "_jelly", col, 0.05, 0.9, 0.15))
    core = sphere(0.28, (0, 0, 0.55))
    core.data.materials.append(mat(name + "_core", tuple(c * 0.5 for c in col), 0.3))
    for ex in (-0.2, 0.2):
        eye = sphere(0.14, (ex, -0.46, 0.95), 16, 8)
        eye.data.materials.append(mat("eye_white", (1, 1, 1), 0.15))
        pupil = sphere(0.07, (ex, -0.58, 0.95), 12, 6)
        pupil.data.materials.append(mat("eye_pupil", (0.03, 0.03, 0.06), 0.1))
    export(name)

reset()
ball = sphere(0.36, (0, 0, 0), 36, 18)
cols = [(1.0, 0.2, 0.2), (0.97, 0.97, 0.97), (1.0, 0.85, 0.15), (0.97, 0.97, 0.97), (0.15, 0.5, 1.0), (0.97, 0.97, 0.97)]
for i, c in enumerate(cols):
    ball.data.materials.append(mat(f"ball_{i}", c, 0.25))
cap = len(cols)
ball.data.materials.append(mat("ball_cap", (0.97, 0.97, 0.97), 0.25))
for p in ball.data.polygons:
    x, y, z = p.center
    if abs(z) > 0.3:
        p.material_index = cap
    else:
        a = (math.atan2(y, x) / (2 * math.pi) + 0.5) * 6.0
        p.material_index = int(a) % 6
export("beach_ball")
