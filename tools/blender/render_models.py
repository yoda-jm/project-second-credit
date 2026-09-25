"""Studio renders of a folder of models (OBJ or GLB), coloured roughly like in the game.

Contact sheet:  blender -b --factory-startup -P tools/blender/render_models.py -- <dir> <out.png> [title]
Turntable:      blender -b --factory-startup -P tools/blender/render_models.py -- <dir> <out_prefix> [title] --turntable 48
The turntable writes <out_prefix>0001.png ... (all models spinning together).
"""
import bpy, sys, os, math

args = sys.argv[sys.argv.index("--") + 1:]
turn = 0
if "--turntable" in args:
    turn = int(args[args.index("--turntable") + 1])
    args = args[:args.index("--turntable")]
models_dir, out = args[0], args[1]
title = args[2] if len(args) > 2 else ""

COLORS = {  # name: (base color, metallic, roughness, emission strength)
    "boulder": ((0.45, 0.43, 0.41), 0.0, 0.8, 0), "diamond": ((0.25, 0.8, 1.0), 0.2, 0.05, 2.0),
    "dirt": ((0.32, 0.22, 0.13), 0.0, 0.95, 0), "brick": ((0.55, 0.25, 0.16), 0.0, 0.8, 0),
    "steel": ((0.55, 0.62, 0.72), 0.9, 0.3, 0), "firefly": ((1.0, 0.45, 0.05), 0.0, 0.5, 4.0),
    "butterfly": ((0.9, 0.25, 1.0), 0.0, 0.5, 3.0), "amoeba": ((0.2, 0.8, 0.25), 0.0, 0.3, 0.6),
    "exit": ((0.5, 0.48, 0.52), 0.0, 0.8, 0), "portal": ((0.3, 1.0, 0.5), 0.0, 0.5, 3.0),
    "hero": ((1.0, 0.72, 0.15), 0.1, 0.4, 0), "cannonball": ((0.25, 0.25, 0.27), 0.8, 0.35, 0),
    "wall_piece": ((0.62, 0.58, 0.5), 0.0, 0.9, 0), "cone": ((1.0, 0.45, 0.05), 0.0, 0.6, 0.5),
    "gear": ((0.6, 0.65, 0.72), 1.0, 0.3, 0),
}

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
files = sorted(f for f in os.listdir(models_dir) if f.endswith((".obj", ".glb")))
names = []
pivots = []
cols = min(4, max(1, len(files)))
for i, f in enumerate(files):
    name = f.rsplit(".", 1)[0]
    before = set(bpy.data.objects)
    path = os.path.join(models_dir, f)
    if f.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    pivot = bpy.data.objects.new(name + "_pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = ((i % cols) * 1.5, 0, -(i // cols) * 1.5)
    for o in new:
        if o.parent is None:
            o.parent = pivot
            o.location = (0, 0, 0)
        if o.type == "MESH" and f.endswith(".obj"):
            o.rotation_euler = (math.radians(90), 0, 0)
            c, metal, rough, emit = COLORS.get(name, ((0.7, 0.7, 0.7), 0, 0.6, 0))
            m = bpy.data.materials.new(name)
            m.use_nodes = True
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (*c, 1)
            b.inputs["Metallic"].default_value = metal
            b.inputs["Roughness"].default_value = rough
            if emit:
                b.inputs["Emission Color"].default_value = (*c, 1)
                b.inputs["Emission Strength"].default_value = emit * 0.35
            o.data.materials.clear()
            o.data.materials.append(m)
    pivot.rotation_euler = (math.radians(12), 0, math.radians(-25))
    pivots.append(pivot)
    names.append(name)

rows = (len(files) + cols - 1) // cols
cx, cz = (cols - 1) * 0.75, -(rows - 1) * 0.75
bpy.ops.object.camera_add(location=(cx, -14, cz + 1.2), rotation=(math.radians(85), 0, 0))
cam = bpy.context.active_object
cam.data.type = "ORTHO"
cam.data.ortho_scale = max(cols * 1.55, (rows + 0.6) * 1.55 * 16 / 9) + 0.4
cam.location.z += 0.45
bpy.context.scene.camera = cam
for loc, energy, color in [((-4, -6, 5), 900, (1, 0.92, 0.85)), ((6, -4, 2), 350, (0.6, 0.75, 1)), ((0, 5, 4), 500, (1, 1, 1))]:
    bpy.ops.object.light_add(type="AREA", location=(cx + loc[0], loc[1], cz + loc[2]))
    l = bpy.context.active_object
    l.data.energy = energy
    l.data.size = 4
    l.data.color = color
    l.rotation_euler = (math.radians(55), 0, math.atan2(-loc[0], loc[1]) if loc[1] else 0)
    constraint = l.constraints.new("TRACK_TO")
    constraint.target = cam
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.target = pivots[0]
sc = bpy.context.scene
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)
sc.render.engine = "CYCLES"
sc.cycles.samples = 32
sc.cycles.use_denoising = True
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.view_settings.view_transform = "AgX"
if title:
    bpy.ops.object.text_add(location=(cam.location.x - cam.data.ortho_scale * 0.47, -3,
                                      cam.location.z + cam.data.ortho_scale * 9 / 16 * 0.5 - cam.data.ortho_scale * 0.06),
                            rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object
    t.data.body = title
    t.data.size = cam.data.ortho_scale * 0.035
    tm = bpy.data.materials.new("title")
    tm.use_nodes = True
    tm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 0.83, 0.35, 1)
    tm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2
    t.data.materials.append(tm)
if turn:
    sc.frame_start, sc.frame_end = 1, turn
    for p in pivots:
        p.rotation_euler = (math.radians(12), 0, 0)
        p.keyframe_insert("rotation_euler", frame=1)
        p.rotation_euler = (math.radians(12), 0, 2 * math.pi * (turn - 1) / turn)
        p.keyframe_insert("rotation_euler", frame=turn)
        for fc in p.animation_data.action.fcurves if hasattr(p.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    sc.cycles.samples = 16
    sc.render.filepath = out
    bpy.ops.render.render(animation=True)
else:
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
print("rendered", names)
