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
hull = lambda: mat("hull", (0.22, 0.13, 0.07), 0.7)
paint = lambda: mat("paint", (0.7, 0.08, 0.06), 0.5)
lamp = lambda: mat("lamp", (1.0, 0.8, 0.35), 0.4, 0.0, 1.2)
enemy = lambda: mat("enemy", (0.75, 0.12, 0.12), 0.6)


def castle():
    """A 2x2-cell keep: body with windows, four round towers (arrow slits, crenellations, cone roofs and
    banners), a gatehouse with an arched door, and a central flag."""
    reset()
    parts = [box((1.3, 1.3, 1.0), (0, 0, 0.5), stone())]
    for sx in (-1, 1):
        for sy in (-1, 1):
            tx, ty = sx * 0.72, sy * 0.72
            parts.append(cyl(0.3, 1.5, (tx, ty, 0.75), stone(), 32))
            parts.append(cyl(0.34, 0.1, (tx, ty, 1.52), stone(), 32))
            for k in range(8):  # tower crenellations
                a = k * math.pi / 4
                parts.append(box((0.09, 0.09, 0.12), (tx + 0.3 * math.cos(a), ty + 0.3 * math.sin(a), 1.62), stone()))
            parts.append(cyl(0.33, 0.62, (tx, ty, 1.95), roof(), 32, r2=0.0))
            parts.append(cyl(0.012, 0.35, (tx, ty, 2.4), wood(), 6))
            parts.append(box((0.16, 0.01, 0.09), (tx + 0.08, ty, 2.5), flag()))
            for k in range(3):  # arrow slits facing out
                a = math.atan2(ty, tx) + (k - 1) * 0.6
                parts.append(box((0.03, 0.03, 0.16), (tx + 0.3 * math.cos(a), ty + 0.3 * math.sin(a), 0.9), dark_stone()))
    for i in range(6):
        t = -0.55 + i * 0.22
        for (x, y) in ((t, -0.62), (t, 0.62), (-0.62, t), (0.62, t)):
            parts.append(box((0.12, 0.12, 0.14), (x, y, 1.07), stone()))
    for (x, z) in ((-0.3, 0.72), (0.3, 0.72)):  # windows
        parts.append(box((0.1, 0.04, 0.16), (x, -0.66, z), dark_stone()))
    parts.append(box((0.62, 0.3, 0.7), (0, -0.68, 0.35), stone()))  # gatehouse
    parts.append(cyl(0.16, 0.34, (0, -0.84, 0.36), wood(), 24, rot=(math.radians(90), 0, 0)))
    parts.append(box((0.32, 0.34, 0.36), (0, -0.84, 0.18), wood()))
    parts.append(cyl(0.025, 0.9, (0, 0, 1.45), wood(), 8))
    parts.append(box((0.42, 0.02, 0.26), (0.22, 0, 1.75), flag()))
    join(parts, "castle")
    export_glb("castle")


def cannon():
    """A 2x2-cell cannon: tapered iron barrel with reinforcing rings and a flared muzzle, on a wooden carriage
    with spoked wheels, on a flagstone platform."""
    reset()
    parts = [cyl(0.78, 0.14, (0, 0, 0.07), dark_stone(), 40)]
    for k in range(8):
        a = k * math.pi / 4
        parts.append(box((0.3, 0.3, 0.04), (0.45 * math.cos(a), 0.45 * math.sin(a), 0.15), dark_stone(), rot=(0, 0, a)))
    parts.append(box((0.46, 0.8, 0.2), (0, 0.05, 0.36), wood()))
    parts.append(box((0.06, 0.8, 0.3), (-0.2, 0.05, 0.46), wood()))
    parts.append(box((0.06, 0.8, 0.3), (0.2, 0.05, 0.46), wood()))
    for sx in (-1, 1):
        parts.append(cyl(0.27, 0.07, (sx * 0.3, -0.18, 0.38), wood(), 24, rot=(0, math.radians(90), 0)))
        parts.append(cyl(0.06, 0.1, (sx * 0.3, -0.18, 0.38), iron(), 12, rot=(0, math.radians(90), 0)))
        for k in range(6):  # spokes
            a = k * math.pi / 3
            parts.append(box((0.02, 0.4, 0.035), (sx * 0.3, -0.18, 0.38), wood(), rot=(a, 0, 0)))
    tilt = math.radians(78)
    parts.append(cyl(0.15, 1.05, (0, -0.25, 0.62), iron(), 32, rot=(tilt, 0, 0), r2=0.11))
    for k, d in enumerate((-0.3, 0.05, 0.4)):  # rings
        parts.append(cyl(0.165 - k * 0.012, 0.05, (0, -0.25 - d * math.sin(tilt), 0.62 + d * math.cos(tilt) * 0.2), iron(), 32,
                         rot=(tilt, 0, 0)))
    parts.append(cyl(0.14, 0.1, (0, -0.76, 0.72), iron(), 32, rot=(tilt, 0, 0), r2=0.16))  # muzzle
    parts.append(cyl(0.17, 0.16, (0, 0.22, 0.55), iron(), 32, rot=(tilt, 0, 0)))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.1, location=(0, 0.32, 0.54))
    parts.append(bpy.context.active_object)
    parts[-1].data.materials.append(iron())
    join(parts, "cannon")
    export_glb("cannon")


def ship(name, length, masts, color):
    """A ship pointing along -Y: a curved planked hull (many sections), gun ports, railing, a raised stern,
    masts with yards, sails, rigging lines and an enemy pennant."""
    reset()
    bm = bmesh.new()
    sections = 14
    rings = []
    for k in range(sections + 1):
        v = k / sections
        y = -length / 2 + v * length
        width = length * 0.27 * math.sin(math.pi * min(1.0, 0.15 + v * 0.95)) ** 0.6
        deck = 0.08 + (0.14 if v > 0.78 else 0.0)
        ring = []
        for j in range(9):
            a = math.pi * j / 8
            ring.append(bm.verts.new((-width * math.cos(a), y, deck - 0.36 * math.sin(a) * (0.6 + 0.4 * math.sin(math.pi * v)))))
        rings.append(ring)
    for k in range(sections):
        for j in range(8):
            bm.faces.new([rings[k][j], rings[k][j + 1], rings[k + 1][j + 1], rings[k + 1][j]])
    for k in range(sections):
        bm.faces.new([rings[k][0], rings[k + 1][0], rings[k + 1][8], rings[k][8]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    body = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(body)
    body.data.materials.append(hull())
    bpy.context.view_layer.objects.active = body
    parts = [body]
    for side in (-1, 1):  # gun ports and railing
        for k in range(2 + masts):
            y = -length * 0.28 + k * length * 0.5 / (1 + masts)
            parts.append(box((0.03, 0.09, 0.07), (side * length * 0.26, y, 0.0), dark_stone()))
        parts.append(box((0.03, length * 0.8, 0.05), (side * length * 0.24, 0, 0.2), wood()))
    parts.append(box((length * 0.42, length * 0.2, 0.2), (0, length * 0.38, 0.28), hull()))
    for side in (-1, 1):  # painted band along the hull, stern windows, lanterns
        parts.append(box((0.02, length * 0.72, 0.05), (side * length * 0.262, -0.02, 0.08), paint()))
    for k in range(3):
        parts.append(box((0.07, 0.02, 0.07), ((k - 1) * 0.12, length * 0.48, 0.25), lamp()))
    for sx in (-1, 1):
        parts.append(cyl(0.035, 0.08, (sx * length * 0.18, length * 0.47, 0.46), lamp(), 8))
    for k in range(masts):
        y = -length * 0.22 + (k * length * 0.5 / max(1, masts - 1) if masts > 1 else length * 0.05)
        mh = 1.0 + 0.3 * length
        parts.append(cyl(0.035, mh, (0, y, mh / 2), wood(), 10))
        for yard in (0.45, 0.8):
            parts.append(cyl(0.018, length * 0.62, (0, y, mh * yard), wood(), 6, rot=(0, math.radians(90), 0)))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y + 0.05, mh * 0.62), rotation=(math.radians(90), 0, 0))
        sl = bpy.context.active_object
        sl.scale = (length * 0.3, mh * 0.2, 1)
        bpy.ops.object.transform_apply(scale=True)
        sm = sl.modifiers.new("s", "SIMPLE_DEFORM")
        sm.deform_method = "BEND"
        sm.angle = 0.5
        sm.deform_axis = "Z"
        bpy.ops.object.modifier_apply(modifier=sm.name)
        sd = sl.modifiers.new("t", "SOLIDIFY")
        sd.thickness = 0.015
        bpy.ops.object.modifier_apply(modifier=sd.name)
        sl.data.materials.append(sail())
        parts.append(sl)
        parts.append(box((length * 0.06, 0.03, mh * 0.28), (0, y + 0.02, mh * 0.62), paint()))  # sail emblem
        parts.append(box((length * 0.24, 0.03, mh * 0.05), (0, y + 0.02, mh * 0.66), paint()))
        parts.append(box((0.25, 0.01, 0.1), (0.13, y, mh + 0.05), color))
        for side in (-1, 1):  # shrouds
            top = (0, y, mh * 0.85)
            bot = (side * length * 0.24, y + 0.15, 0.2)
            mid = [(a + b) / 2 for a, b in zip(top, bot)]
            ln = math.dist(top, bot)
            ang = math.atan2(top[0] - bot[0], top[2] - bot[2])
            parts.append(cyl(0.006, ln, mid, wood(), 4, rot=(0, ang, 0)))
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


def pine():
    reset()
    parts = [cyl(0.05, 0.3, (0, 0, 0.15), wood(), 8)]
    for k, (r, z) in enumerate(((0.32, 0.4), (0.26, 0.62), (0.19, 0.82), (0.11, 0.98))):
        parts.append(cyl(r, 0.34, (0, 0, z), mat("pine", (0.12, 0.3, 0.14), 0.8), 10, r2=0.0))
    join(parts, "pine")
    export_glb("pine")


def tree():
    reset()
    random.seed(3)
    parts = [cyl(0.06, 0.5, (0, 0, 0.25), wood(), 8)]
    for k in range(5):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=random.uniform(0.18, 0.26),
                                              location=(random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), 0.6 + random.uniform(0, 0.2)))
        o = bpy.context.active_object
        o.data.materials.append(mat("leaves", (0.22, 0.45, 0.16), 0.8))
        parts.append(o)
    join(parts, "tree")
    export_glb("tree")


def bush():
    reset()
    random.seed(4)
    parts = []
    for k in range(4):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=random.uniform(0.1, 0.16),
                                              location=(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0.1))
        o = bpy.context.active_object
        o.data.materials.append(mat("bush", (0.18, 0.38, 0.12), 0.8))
        parts.append(o)
    for k in range(5):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=0.025,
                                             location=(random.uniform(-0.18, 0.18), random.uniform(-0.18, 0.18), random.uniform(0.12, 0.2)))
        o = bpy.context.active_object
        o.data.materials.append(mat("berry", (0.8, 0.15, 0.2), 0.4))
        parts.append(o)
    join(parts, "bush")
    export_glb("bush")


def stones():
    reset()
    random.seed(8)
    parts = []
    for k in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.08, 0.16),
                                              location=(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 0.04))
        o = bpy.context.active_object
        o.scale = (1, 0.8, 0.6)
        o.data.materials.append(dark_stone())
        parts.append(o)
    join(parts, "stones")
    export_glb("stones")


def grass_tuft():
    reset()
    random.seed(6)
    parts = []
    for k in range(9):
        a = random.uniform(0, math.pi * 2)
        r = random.uniform(0, 0.25)
        parts.append(cyl(0.02, random.uniform(0.12, 0.22), (r * math.cos(a), r * math.sin(a), 0.08),
                         mat("blade", (0.3, 0.55, 0.18), 0.8), 3, rot=(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0), r2=0.0))
    for k in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=0.03,
                                             location=(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 0.16))
        o = bpy.context.active_object
        o.data.materials.append(mat(random.choice(["flower_y", "flower_w", "flower_p"]),
                                    random.choice([(1, 0.85, 0.2), (0.95, 0.95, 0.95), (0.8, 0.4, 0.9)]), 0.5))
        parts.append(o)
    join(parts, "grass_tuft")
    export_glb("grass_tuft")


castle()
cannon()
pine()
tree()
bush()
stones()
grass_tuft()
ship("ship_small", 1.2, 1, enemy())
ship("ship_medium", 1.7, 2, enemy())
ship("ship_large", 2.3, 3, enemy())
wall()
rubble()
cannonball()
