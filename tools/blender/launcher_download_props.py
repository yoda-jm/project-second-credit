"""Props that float behind the launcher while the selected game isn't downloaded yet: 3.5-inch floppy disks (two
colours), small clouds and a download arrow over its tray.
Run: blender -b --factory-startup -P tools/blender/launcher_download_props.py -- godot/core/art/props
Deterministic; output licence CC BY-SA 4.0. Provenance: this script. Z is up in Blender (Y up in the files).
"""
import bpy, bmesh, math, os, sys

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
MATS = {}


def mat(name, color, rough=0.5, metal=0.0, emit=0.0):
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
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def box(size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    return o


def bevel(o, width, segments=2):
    m = o.modifiers.new("b", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)


def join(parts, name, smooth=False):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    if smooth:
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()
    return o


def export_glb(name):
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)


def floppy(name, body_color):
    """A 3.5-inch disk, 9 cm square: the body with its clipped corner, the sliding metal shutter with its window,
    the paper label, the write-protect tab."""
    reset()
    body_m = mat(name + "_body", body_color, rough=0.45)
    s = 0.9
    t = 0.033
    # body: a square with the top-right corner cut, extruded
    bm = bmesh.new()
    pts = [(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2 - 0.05), (s / 2 - 0.05, s / 2), (-s / 2, s / 2)]
    top = [bm.verts.new((x, y, t / 2)) for x, y in pts]
    bot = [bm.verts.new((x, y, -t / 2)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new([top[i], bot[i], bot[j], top[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    body = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(body)
    body.data.materials.append(body_m)
    bevel(body, 0.008)
    parts = [body]
    metal = mat("shutter", (0.78, 0.8, 0.84), rough=0.25, metal=1.0)
    dark = mat("window", (0.05, 0.05, 0.07), rough=0.6)
    # shutter across the top edge, both faces, with the window showing the dark disk
    for z in (1, -1):
        parts.append(box((0.42, 0.3, 0.006), (0.0, s / 2 - 0.15, z * (t / 2 + 0.002)), metal))
        parts.append(box((0.12, 0.2, 0.004), (0.06, s / 2 - 0.14, z * (t / 2 + 0.006)), dark))
    # label on the front, a strip on top
    paper = mat("label", (0.95, 0.94, 0.88), rough=0.85)
    parts.append(box((0.64, 0.46, 0.004), (0.0, -0.17, t / 2 + 0.002), paper))
    parts.append(box((0.64, 0.05, 0.005), (0.0, 0.02, t / 2 + 0.003), mat(name + "_stripe", body_color, rough=0.5, emit=0.6)))
    # hub on the back, write-protect tab
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=0.006, location=(0, 0.02, -t / 2 - 0.003))
    hub = bpy.context.active_object
    hub.data.materials.append(metal)
    parts.append(hub)
    parts.append(box((0.06, 0.05, 0.006), (-s / 2 + 0.07, -s / 2 + 0.07, -t / 2 - 0.002), dark))
    o = join(parts, name)
    o.rotation_euler = (math.radians(90), 0, 0)  # stands up, faces the camera
    bpy.ops.object.transform_apply(rotation=True)
    export_glb(name)


def cloud():
    """A small cartoon cloud: overlapping spheres on a flat underside."""
    reset()
    white = mat("cloud", (0.92, 0.95, 1.0), rough=0.9, emit=0.25)
    balls = [(0.0, 0.0, 0.28, 0.36), (-0.36, 0.0, 0.14, 0.26), (0.38, 0.02, 0.16, 0.28), (-0.15, 0.08, 0.36, 0.25),
             (0.2, -0.06, 0.34, 0.24), (-0.6, 0.0, 0.06, 0.16), (0.65, 0.0, 0.07, 0.17)]
    parts = []
    for x, y, z, r in balls:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=(x, y, z))
        o = bpy.context.active_object
        o.scale = (1.0, 0.75, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(white)
        parts.append(o)
    o = join(parts, "cloud", smooth=True)
    # flatten what hangs below the base
    for v in o.data.vertices:
        if v.co.z < 0.0:
            v.co.z *= 0.25
    o.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    export_glb("cloud")


def arrow():
    """A download arrow over its tray, glowing gold."""
    reset()
    gold = mat("arrow", (1.0, 0.78, 0.25), rough=0.35, metal=0.3, emit=1.6)
    shaft = box((0.16, 0.12, 0.42), (0, 0, 0.24), gold)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.3, radius2=0.0, depth=0.3, location=(0, 0, -0.1),
                                    rotation=(math.pi, 0, math.radians(45)))
    head = bpy.context.active_object
    head.scale = (1.0, 0.45, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(gold)
    tray_m = mat("tray", (0.3, 0.85, 1.0), rough=0.4, emit=0.8)
    tray = [box((0.7, 0.12, 0.07), (0, 0, -0.38), tray_m), box((0.07, 0.12, 0.2), (-0.35, 0, -0.3), tray_m),
            box((0.07, 0.12, 0.2), (0.35, 0, -0.3), tray_m)]
    for p in [shaft, head] + tray:
        bevel(p, 0.012, 1)
    o = join([shaft, head] + tray, "download_arrow")
    o.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    export_glb("download_arrow")


floppy("floppy_teal", (0.12, 0.62, 0.72))
floppy("floppy_pink", (0.85, 0.25, 0.55))
cloud()
arrow()
