"""Procedural models for game 1 (rocks and diamonds), built in Blender and exported as OBJ for Godot.

Run: blender -b --factory-startup -P tools/blender/rocks_models.py -- godot/games/rocks/art/models
Every model is one grid cell (1 x 1 m), centred on the origin, Z up in Blender (Y up in the OBJ files).
Deterministic: fixed random seeds, so the output only changes when this script does.
Licence of the generated models: CC BY-SA 4.0 (like all project assets). Provenance: this script.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, noise

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials):
        for b in list(block):
            block.remove(b)


def finish(obj, name, smooth=False, bevel=0.0, segments=2):
    obj.name = name
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if bevel > 0:
        m = obj.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = segments
        m.limit_method = "ANGLE"
        bpy.ops.object.modifier_apply(modifier=m.name)
    if smooth:
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()


def export(name):
    for o in bpy.context.scene.objects:
        o.select_set(o.name == name)
    bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, name + ".obj"), export_selected_objects=True,
                          export_materials=False, export_uv=True, export_normals=True,
                          forward_axis="NEGATIVE_Z", up_axis="Y", apply_modifiers=True)
    print("exported", name)


def bm_to_obj(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


# ---------- boulder: a lumpy, faceted rock ----------
def boulder():
    reset()
    random.seed(7)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.43)
    for v in bm.verts:
        n = noise.noise(v.co * 3.1 + Vector((1.3, 2.1, 0.7)))
        v.co *= 1.0 + 0.14 * n + random.uniform(-0.03, 0.03)
        v.co.z *= 0.92
    obj = bm_to_obj(bm, "boulder")
    finish(obj, "boulder", smooth=False)
    export("boulder")


# ---------- diamond: a brilliant-cut gem ----------
def diamond():
    reset()
    bm = bmesh.new()
    n = 8
    r_table, r_girdle = 0.2, 0.36
    top = [bm.verts.new((r_table * math.cos(a), r_table * math.sin(a), 0.2)) for a in
           [2 * math.pi * i / n + math.pi / n for i in range(n)]]
    gird = [bm.verts.new((r_girdle * math.cos(a), r_girdle * math.sin(a), 0.04)) for a in
            [2 * math.pi * i / n for i in range(n)]]
    tip = bm.verts.new((0, 0, -0.38))
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([gird[i], gird[j], top[i]])
        bm.faces.new([top[i], gird[j], top[j]])
        bm.faces.new([gird[j], gird[i], tip])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = bm_to_obj(bm, "diamond")
    obj.rotation_euler = (math.radians(0), 0, 0)
    finish(obj, "diamond", smooth=False)
    export("diamond")


# ---------- dirt: a soft block with a crumbly surface ----------
def dirt():
    reset()
    bpy.ops.mesh.primitive_cube_add(size=0.98)
    obj = bpy.context.active_object
    m = obj.modifiers.new("sub", "SUBSURF")
    m.levels = 3
    m.subdivision_type = "SIMPLE"
    bpy.ops.object.modifier_apply(modifier=m.name)
    for v in obj.data.vertices:
        d = noise.noise(v.co * 7.0) * 0.035 + noise.noise(v.co * 17.0) * 0.015
        v.co += v.normal * d
    finish(obj, "dirt", smooth=True, bevel=0.0)
    export("dirt")


# ---------- brick wall: six bricks with mortar gaps ----------
def brick():
    reset()
    objs = []
    rows = [(-0.25, [(-0.25, 0.47), (0.25, 0.47)]), (0.25, [(-0.375, 0.22), (0.125, 0.47), (0.435, 0.11)])]
    rows[1] = (0.25, [(-0.385, 0.2), (0.0, 0.52), (0.385, 0.2)])
    for z, bricks in rows:
        for x, width in bricks:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, z))
            b = bpy.context.active_object
            b.scale = (width, 0.96, 0.46)
            bpy.ops.object.transform_apply(scale=True)
            objs.append(b)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    finish(bpy.context.active_object, "brick", bevel=0.035, segments=2)
    export("brick")


# ---------- steel: riveted armour plate ----------
def steel():
    reset()
    bpy.ops.mesh.primitive_cube_add(size=0.99)
    base = bpy.context.active_object
    finish(base, "steel", bevel=0.06, segments=3)
    parts = [base]
    for sx in (-1, 1):
        for sz in (-1, 1):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.06, location=(sx * 0.32, -0.5, sz * 0.32))
            parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.5, 0))
    plate = bpy.context.active_object
    plate.scale = (0.46, 0.04, 0.46)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(plate)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    base.name = "steel"
    bpy.ops.object.shade_flat()
    export("steel")


# ---------- hero: a small round miner robot with a head lamp ----------
def hero():
    reset()
    parts = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=0.26, location=(0, 0, -0.1))
    body = bpy.context.active_object
    body.scale = (1.0, 0.9, 1.05)
    parts.append(body)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=0.2, location=(0, 0, 0.22))
    parts.append(bpy.context.active_object)
    # helmet brim and lamp
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.22, depth=0.05, location=(0, 0, 0.3))
    parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.06, depth=0.08, location=(0, -0.2, 0.33),
                                        rotation=(math.radians(90), 0, 0))
    parts.append(bpy.context.active_object)
    # eyes
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.045, location=(sx * 0.08, -0.18, 0.2))
        parts.append(bpy.context.active_object)
    # feet
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.09, location=(sx * 0.13, -0.03, -0.38))
        f = bpy.context.active_object
        f.scale = (1, 1.4, 0.6)
        parts.append(f)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    finish(bpy.context.active_object, "hero", smooth=True)
    export("hero")


# ---------- firefly: glowing core with four fins ----------
def firefly():
    reset()
    parts = []
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.2)
    core = bpy.context.active_object
    parts.append(core)
    for a in range(4):
        ang = a * math.pi / 2 + math.pi / 4
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.08, depth=0.28,
                                        location=(0.25 * math.cos(ang), 0, 0.25 * math.sin(ang)),
                                        rotation=(0, math.pi / 2 - ang, 0))
        parts.append(bpy.context.active_object)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = core
    bpy.ops.object.join()
    finish(bpy.context.active_object, "firefly")
    export("firefly")


# ---------- butterfly: body and two wings (wings flap in Godot by scaling X) ----------
def butterfly():
    reset()
    bm = bmesh.new()
    for side in (-1, 1):
        pts = [(0.02 * side, 0, 0.05), (0.42 * side, 0, 0.36), (0.44 * side, 0, -0.05), (0.3 * side, 0, -0.32),
               (0.03 * side, 0, -0.08)]
        vs = [bm.verts.new(p) for p in pts]
        f = bm.faces.new(vs if side > 0 else list(reversed(vs)))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
    obj = bm_to_obj(bm, "butterfly")
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.045, depth=0.5)
    body = bpy.context.active_object
    body.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    finish(obj, "butterfly")
    export("butterfly")


# ---------- amoeba: a wobbly blob ----------
def amoeba():
    reset()
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.5)
    for v in bm.verts:
        v.co *= 1.0 + 0.12 * noise.noise(v.co * 4.0 + Vector((3, 1, 2)))
    obj = bm_to_obj(bm, "amoeba")
    finish(obj, "amoeba", smooth=True)
    export("amoeba")


# ---------- exit: a stone arch around a portal ----------
def exit_gate():
    reset()
    parts = []
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 0.38, 0, -0.08))
        p = bpy.context.active_object
        p.scale = (0.2, 0.9, 0.84)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(p)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.38, minor_radius=0.1, location=(0, 0, 0.28),
                                     rotation=(math.radians(90), 0, 0), major_segments=24, minor_segments=8)
    parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.47))
    p = bpy.context.active_object
    p.scale = (0.96, 0.9, 0.06)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(p)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    finish(bpy.context.active_object, "exit", bevel=0.02)
    export("exit")


# ---------- portal: the glowing disc inside the exit ----------
def portal():
    reset()
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.3, fill_type="TRIFAN", location=(0, 0, 0.05),
                                      rotation=(math.radians(90), 0, 0))
    finish(bpy.context.active_object, "portal", smooth=True)
    export("portal")


for build in (boulder, diamond, dirt, brick, steel, hero, firefly, butterfly, amoeba, exit_gate, portal):
    build()
