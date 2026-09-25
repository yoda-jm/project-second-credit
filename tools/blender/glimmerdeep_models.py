"""Procedural models for game 1 (Glimmerdeep), built in Blender and exported as OBJ for Godot.

Run: blender -b --factory-startup -P tools/blender/glimmerdeep_models.py -- godot/games/glimmerdeep/art/models
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
    """A chiselled rock: convex hull of random points on a squashed ellipsoid, bevelled edges."""
    reset()
    random.seed(11)
    bm = bmesh.new()
    for i in range(90):
        z = random.uniform(-1, 1)
        a = random.uniform(0, 2 * math.pi)
        r = math.sqrt(1 - z * z)
        k = random.uniform(0.86, 1.0)
        bm.verts.new((0.44 * r * math.cos(a) * k, 0.4 * r * math.sin(a) * k, 0.38 * z * k))
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    obj = bm_to_obj(bm, "boulder")
    finish(obj, "boulder", bevel=0.02, segments=2)
    m = obj.modifiers.new("sub", "SUBSURF")
    m.levels = 1
    bpy.ops.object.modifier_apply(modifier=m.name)
    for v in obj.data.vertices:
        v.co += v.normal * (0.018 * noise.noise(v.co * 7.0) + 0.006 * noise.noise(v.co * 23.0))
    bpy.ops.object.shade_flat()
    export("boulder")


# ---------- diamond: a brilliant-cut gem ----------
def diamond():
    """A round brilliant: octagonal table, star and kite facets in the crown, pointed pavilion."""
    reset()
    bm = bmesh.new()
    n = 8
    table = [bm.verts.new((0.19 * math.cos(2 * math.pi * i / n), 0.19 * math.sin(2 * math.pi * i / n), 0.2)) for i in range(n)]
    crown = [bm.verts.new((0.3 * math.cos(2 * math.pi * (i + 0.5) / n), 0.3 * math.sin(2 * math.pi * (i + 0.5) / n), 0.13))
             for i in range(n)]
    girdle = [bm.verts.new((0.38 * math.cos(2 * math.pi * i / (2 * n)), 0.38 * math.sin(2 * math.pi * i / (2 * n)), 0.03))
              for i in range(2 * n)]
    mid = [bm.verts.new((0.2 * math.cos(2 * math.pi * i / n), 0.2 * math.sin(2 * math.pi * i / n), -0.2)) for i in range(n)]
    tip = bm.verts.new((0, 0, -0.4))
    bm.faces.new(table)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([table[i], crown[i], table[j]])                       # star facets
        bm.faces.new([table[i], girdle[2 * i], girdle[2 * i + 1], crown[i]])  # kite (bezel)
        bm.faces.new([crown[i], girdle[2 * i + 1], girdle[(2 * i + 2) % (2 * n)]])
        bm.faces.new([crown[i], girdle[(2 * i + 2) % (2 * n)], table[j]])
        bm.faces.new([girdle[2 * i], mid[i], girdle[2 * i + 1]])
        bm.faces.new([girdle[2 * i + 1], mid[i], mid[j], girdle[(2 * i + 2) % (2 * n)]])
        bm.faces.new([mid[i], tip, mid[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = bm_to_obj(bm, "diamond")
    finish(obj, "diamond")
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
    """A chunky little miner: round body, big head, helmet with a lamp, goggles, backpack and boots.
    Facing -Y in Blender (towards the camera in the game)."""
    reset()
    parts = []

    mats = {}

    def mat(name, color, emission=0.0, rough=0.5, metal=0.0):
        if name not in mats:
            m = bpy.data.materials.new(name)
            m.use_nodes = True
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (*color, 1)
            b.inputs["Roughness"].default_value = rough
            b.inputs["Metallic"].default_value = metal
            if emission > 0:
                b.inputs["Emission Color"].default_value = (*color, 1)
                b.inputs["Emission Strength"].default_value = emission
            mats[name] = m
        return mats[name]

    current = {"m": None}

    def add(obj, scale=None):
        if scale:
            obj.scale = scale
            bpy.ops.object.transform_apply(scale=True)
        obj.data.materials.append(current["m"])
        parts.append(obj)

    def use(name, color, **kw):
        current["m"] = mat(name, color, **kw)

    use("overalls", (0.85, 0.35, 0.08), rough=0.7)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.2, location=(0, 0, -0.15))
    add(bpy.context.active_object, (1.0, 0.85, 1.05))                       # body
    use("skin", (0.95, 0.7, 0.55), rough=0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.21, location=(0, -0.01, 0.16))
    add(bpy.context.active_object)                                           # head
    use("helmet", (1.0, 0.78, 0.1), rough=0.3, metal=0.1)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.225, location=(0, 0, 0.22))
    helmet = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(helmet.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.02], context="VERTS")
    bm.to_mesh(helmet.data)
    bm.free()
    add(helmet)                                                              # helmet dome
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.25, depth=0.03, location=(0, -0.02, 0.215))
    add(bpy.context.active_object)                                           # brim
    use("lamp", (1.0, 0.95, 0.7), emission=6.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.055, depth=0.07, location=(0, -0.22, 0.3),
                                        rotation=(math.radians(90), 0, 0))
    add(bpy.context.active_object)                                           # lamp
    for sx in (-1, 1):
        use("goggles", (0.15, 0.15, 0.18), rough=0.3, metal=0.6)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.018, location=(sx * 0.08, -0.19, 0.15),
                                         rotation=(math.radians(90), 0, 0), major_segments=16, minor_segments=6)
        add(bpy.context.active_object)                                       # goggles
        use("eyes", (0.05, 0.05, 0.08), rough=0.1)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.04, location=(sx * 0.08, -0.18, 0.15))
        add(bpy.context.active_object)                                       # eyes
        use("overalls", (0.85, 0.35, 0.08), rough=0.7)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.07, location=(sx * 0.2, -0.02, -0.12))
        add(bpy.context.active_object, (0.8, 0.8, 1.3))                     # arms
        use("boots", (0.3, 0.18, 0.1), rough=0.8)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 0.1, -0.05, -0.4))
        add(bpy.context.active_object, (0.13, 0.2, 0.09))                   # boots
    use("backpack", (0.4, 0.42, 0.45), rough=0.6, metal=0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.17, -0.1))
    add(bpy.context.active_object, (0.26, 0.12, 0.3))                       # backpack
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = 0.015
    m.segments = 2
    m.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=m.name)
    finish(obj, "hero", smooth=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "hero.glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True)
    print("exported hero.glb")


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
    """A stone archway: two pillars with bases and capitals, a round arch of voussoirs with a keystone."""
    reset()
    parts = []
    for sx in (-1, 1):
        for (z, sxz, sz) in ((-0.44, 0.2, 0.08), (-0.1, 0.14, 0.6), (0.22, 0.2, 0.06)):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 0.36, 0, z))
            o = bpy.context.active_object
            o.scale = (sxz, 0.7, sz)
            bpy.ops.object.transform_apply(scale=True)
            parts.append(o)
    stones = 7
    for i in range(stones):
        a = math.pi * (i + 0.5) / stones
        key = i == stones // 2
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.36 * math.cos(a), 0, 0.25 + 0.3 * math.sin(a)),
                                        rotation=(0, -(a - math.pi / 2), 0))
        o = bpy.context.active_object
        o.scale = (0.13 if not key else 0.16, 0.72 if not key else 0.8, 0.14 if not key else 0.2)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(o)
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
