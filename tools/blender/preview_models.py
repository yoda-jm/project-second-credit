"""Renders a contact sheet of the game-1 models (OBJ files) for review.
Run: blender -b --factory-startup -P tools/blender/preview_models.py -- <models_dir> <out.png>
"""
import bpy, sys, os, math
args = sys.argv[sys.argv.index("--") + 1:]
models_dir, out = args[0], args[1]
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
names = sorted(f[:-4] for f in os.listdir(models_dir) if f.endswith(".obj"))
cols = 4
for i, n in enumerate(names):
    bpy.ops.wm.obj_import(filepath=os.path.join(models_dir, n + ".obj"), forward_axis="NEGATIVE_Z", up_axis="Y")
    o = bpy.context.selected_objects[0]
    o.location = ((i % cols) * 1.4, 0, -(i // cols) * 1.4)
    o.rotation_euler = (math.radians(90), 0, math.radians(-25))
    mat = bpy.data.materials.new(n)
    mat.diffuse_color = (0.8, 0.75, 0.7, 1)
    o.data.materials.append(mat)
rows = (len(names) + cols - 1) // cols
bpy.ops.object.camera_add(location=((cols - 1) * 0.7, -9, -(rows - 1) * 0.7 + 2.5), rotation=(math.radians(76), 0, 0))
cam = bpy.context.active_object
cam.location = ((cols - 1) * 0.7, -12, -(rows - 1) * 0.7)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.type = "ORTHO"
cam.data.ortho_scale = max(cols, rows) * 1.5
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(20), math.radians(-30)))
bpy.context.active_object.data.energy = 3
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 24
sc.cycles.device = "CPU"
sc.render.resolution_x = 1000
sc.render.resolution_y = int(1000 * rows / cols)
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.12, 0.12, 0.14)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("names:", names)
