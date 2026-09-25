"""App icon: the Glimmerdeep gem over a dark rounded tile, rendered with Cycles (transparent corners).

blender -b --factory-startup -P tools/blender/app_icon.py -- godot/icon.png [size]
"""
import bpy, sys, math

args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
size = int(args[1]) if len(args) > 1 else 512

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 256
sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = size
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"


def mat(name, color, metal=0.0, rough=0.5, emit=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = emit
    return m


# Tile: a rounded slab seen from the front (orthographic camera looking down -Y)
bpy.ops.mesh.primitive_cube_add(size=2)
tile = bpy.context.object
tile.scale = (0.94, 0.1, 0.94)
bev = tile.modifiers.new("bevel", "BEVEL")
bev.width, bev.segments, bev.affect = 0.2, 12, "EDGES"
bpy.ops.object.transform_apply(scale=True)
tile.location.y = 0.25
tm = bpy.data.materials.new("tile")
nt = tm.node_tree
b = nt.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.45
grad = nt.nodes.new("ShaderNodeTexGradient")
grad.gradient_type = "SPHERICAL"
mapn = nt.nodes.new("ShaderNodeMapping")
mapn.inputs["Scale"].default_value = (0.75, 0.75, 0.75)
mapn.inputs["Location"].default_value = (0, 0, 0.15)
tc = nt.nodes.new("ShaderNodeTexCoord")
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.02, 0.015, 0.05, 1)
ramp.color_ramp.elements[1].color = (0.16, 0.07, 0.32, 1)
nt.links.new(tc.outputs["Object"], mapn.inputs["Vector"])
nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
tile.data.materials.append(tm)

# Gem: brilliant cut from the game's diamond model
bpy.ops.wm.obj_import(filepath="godot/games/glimmerdeep/art/models/diamond.obj", forward_axis="NEGATIVE_Z", up_axis="Y")
gem = bpy.context.selected_objects[0]
dims = max(gem.dimensions)
gem.scale = [1.25 / dims] * 3
gem.rotation_euler = (math.radians(95), math.radians(-12), math.radians(18))
bpy.ops.object.shade_flat()
bpy.context.view_layer.update()
gem.location = (0.02, -0.25, 0.05)
gem.data.materials.clear()
gem.data.materials.append(mat("gem", (0.3, 0.85, 1.0), rough=0.02, trans=1.0, ior=2.4, emit=0.35))

# A small glowing glint behind the gem
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.33, location=(0.0, 0.1, 0.05))
glow = bpy.context.object
glow.data.materials.append(mat("glow", (0.35, 0.8, 1.0), emit=6.0))
glow.visible_camera = False

cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.0
cam = bpy.data.objects.new("cam", cam_data)
cam.location = (0, -6, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.collection.objects.link(cam)
sc.camera = cam

for loc, energy, size_, col in [((-2.5, -4, 3), 900, 3, (1, 0.9, 0.8)), ((3, -3, -1), 400, 2, (0.5, 0.7, 1)),
                                ((0, -2, 4), 300, 1, (1, 1, 1))]:
    ld = bpy.data.lights.new("l", "AREA")
    ld.energy, ld.size, ld.color = energy, size_, col
    lo = bpy.data.objects.new("l", ld)
    lo.location = loc
    sc.collection.objects.link(lo)
    tr = lo.constraints.new("TRACK_TO")
    tr.target = gem
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.08, 1)
sc.world = w

sc.render.filepath = out
bpy.ops.render.render(write_still=True)
