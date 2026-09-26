"""Iron Flags (game 8) models: vehicles and cannons (each with a separate child object "turret" pivoting on its
rotation axis), buildings (fort, robot and vehicle factories, radar with a spinning child "dish", repair pad, hut,
flag pole with a separate "cloth"), terrain pieces (rock blocks, crates, bridge, crater) and planet decoration.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/flags_models.py -- godot/games/flags/art/models
One map tile = 1 unit, the front faces -Y, the origin sits at the footprint centre on the ground. Every material whose
name contains "team" is light grey: the game recolours it per team (red player, blue enemy, grey neutral).
flags_robots.py imports the helpers below (mat, box, cyl, sphere, rod, ...).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

OUT = "."
MATS = {}
R90 = math.pi / 2


def mat(name, color, rough=0.5, metal=0.0, emit=0.0, coat=0.0, double=False):
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
    m.use_backface_culling = not double
    MATS[name] = m
    return m


def team():
    """The two team materials: the main armour colour and a slightly darker trim (both recoloured by the game)."""
    return (mat("team_main", (0.8, 0.8, 0.8), 0.4, 0.15, coat=0.3), mat("team_trim", (0.66, 0.66, 0.66), 0.5, 0.25))


def common():
    """Shared non-team materials."""
    return {
        "gun": mat("gunmetal", (0.16, 0.17, 0.19), 0.35, 0.8),
        "dark": mat("dark_metal", (0.09, 0.09, 0.1), 0.5, 0.6),
        "rubber": mat("rubber", (0.05, 0.05, 0.055), 0.85),
        "steel": mat("steel", (0.55, 0.57, 0.6), 0.3, 0.9),
        "paint": mat("hull_paint", (0.4, 0.38, 0.24), 0.55, 0.2, coat=0.25),
        "concrete": mat("concrete", (0.6, 0.58, 0.54), 0.85),
        "concrete_dark": mat("concrete_dark", (0.36, 0.35, 0.33), 0.9),
        "lamp": mat("lamp_glow", (1.0, 0.82, 0.45), 0.3, emit=4.0),
        "glass": mat("glass", (0.08, 0.12, 0.16), 0.05, 0.3, coat=1.0),
        "hazard": mat("hazard_yellow", (0.95, 0.7, 0.08), 0.5),
        "red_light": mat("red_light", (1.0, 0.12, 0.05), 0.3, emit=5.0),
        "green_light": mat("green_light", (0.2, 1.0, 0.35), 0.3, emit=4.0),
    }


def active():
    return bpy.context.active_object


def deselect():
    for x in bpy.context.selected_objects:
        x.select_set(False)


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.curves):
        for d in list(coll):
            coll.remove(d)


def finish(o, material, bevel=0.0, segs=2, smooth=35):
    deselect()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = segs
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        bpy.ops.object.modifier_apply(modifier=b.name)
    o.data.materials.clear()
    o.data.materials.append(material)
    if smooth:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth))
    else:
        bpy.ops.object.shade_flat()
    return o


def box(size, loc, material, rot=(0, 0, 0), bevel=None, segs=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    if bevel is None:
        bevel = min(0.03, min(size) * 0.2)
    return finish(o, material, bevel, segs)


def cyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=16, bevel=0.0, segs=1):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return finish(active(), material, bevel, segs)


def sphere(r, loc, material, scale=(1, 1, 1), segs=12, rings=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc, rotation=rot)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return finish(o, material, smooth=80)


def ring(r, thick, loc, material, rot=(0, 0, 0), verts=24):
    """A torus of major radius r and minor radius thick."""
    bpy.ops.mesh.primitive_torus_add(major_segments=verts, minor_segments=6, major_radius=r, minor_radius=thick,
                                     location=loc, rotation=rot)
    return finish(active(), material, smooth=80)


def rod(a, b, r, material, r2=None, verts=10, caps=False):
    """A cylinder (or cone) from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    r2 = r if r2 is None else r2
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = active()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    finish(o, material)
    if caps:
        return [o, sphere(r, a, material, segs=verts, rings=6), sphere(r2, b, material, segs=verts, rings=6)]
    return o


def join(parts, name, pivot=(0, 0, 0)):
    """Joins parts into one object named `name` whose origin sits at `pivot` (world coordinates)."""
    parts = [p for p in parts if p is not None]
    deselect()
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    o = active()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.data.transform(Matrix.Translation(-Vector(pivot)))
    o.location = pivot
    o.name = name
    o.data.name = name
    assert o.name == name, o.name
    return o


def flatten(items):
    out = []
    for p in items:
        if isinstance(p, (list, tuple)):
            out += flatten(p)
        elif p is not None:
            out.append(p)
    return out


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def export(root, name, children=()):
    """Exports `root` and its children (each (object, parent)) as name.glb, keeping the hierarchy."""
    objs = [root]
    for c, parent in children:
        c.parent = parent
        c.matrix_parent_inverse = parent.matrix_world.inverted()
        objs.append(c)
    deselect()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True)
    print("exported %-18s %6d tris  nodes: %s" % (name, sum(tris(o) for o in objs), ", ".join(o.name for o in objs)))
    reset()


def simple(parts, name):
    export(join(flatten(parts), name), name)


# ------------------------------------------------------------------ vehicles

def track(x, length, tw, h, side, C):
    """A track run along Y at x: rubber belt with rounded ends, grousers on top, road wheels on the outer face."""
    p = [box((tw, length - h, h), (x, 0, h / 2), C["rubber"], bevel=0.02)]
    for s in (-1, 1):
        p.append(cyl(h / 2, tw, (x, s * (length - h) / 2, h / 2), C["rubber"], rot=(0, R90, 0), verts=14, bevel=0.012))
    n = int(length / 0.2)
    for k in range(n):
        y = -length / 2 + h / 2 + (length - h) * (k + 0.5) / n
        p.append(box((tw + 0.012, 0.035, 0.02), (x, y, h + 0.005), C["dark"], bevel=0.0))
    wheels = max(3, int((length - h) / 0.3) + 1)
    for k in range(wheels):
        y = -(length - h) / 2 + (length - h) * k / (wheels - 1)
        p.append(cyl(h * 0.36, 0.04, (x + side * (tw / 2 + 0.005), y, h * 0.46), C["gun"], rot=(0, R90, 0), verts=12))
        p.append(cyl(h * 0.14, 0.05, (x + side * (tw / 2 + 0.01), y, h * 0.46), C["steel"], rot=(0, R90, 0), verts=6))
    return p


def wheel(x, y, r, w, side, C):
    return [cyl(r, w, (x, y, r), C["rubber"], rot=(0, R90, 0), verts=16, bevel=0.03, segs=2),
            cyl(r * 0.55, w + 0.02, (x + side * 0.005, y, r), C["steel"], rot=(0, R90, 0), verts=10, bevel=0.01),
            cyl(r * 0.2, w + 0.05, (x + side * 0.01, y, r), C["gun"], rot=(0, R90, 0), verts=6)]


def headlights(y, z, xs, C, r=0.045):
    return [cyl(r, 0.04, (x, y, z), C["lamp"], rot=(R90, 0, 0), verts=10) for x in xs]


def tank(name, L, W, h, turret_fn, heavy=False):
    TM, TT = team()
    C = common()
    tw = W * 0.24
    x_t = W / 2 - tw / 2
    hull = []
    for s in (-1, 1):
        hull += track(s * x_t, L, tw, h, s, C)
        # fenders over the tracks, with a team stripe
        hull.append(box((tw + 0.04, L * 0.92, 0.04), (s * x_t, 0.0, h + 0.05), C["paint"], bevel=0.012))
        hull.append(box((0.03, L * 0.6, 0.05), (s * (W / 2 + 0.005), 0.0, h + 0.03), TT, bevel=0.01))
        if heavy:  # side skirts
            hull.append(box((0.04, L * 0.8, h * 0.55), (s * (W / 2 + 0.02), 0, h * 0.7), C["paint"], bevel=0.012))
    body_w = W - 2 * tw + 0.02
    hull.append(box((body_w, L * 0.9, h * 0.8), (0, 0, h * 0.55), C["gun"], bevel=0.02))
    deck_h = h * 0.55
    hull.append(box((W - 0.06, L * 0.72, deck_h), (0, 0.04 * L, h + deck_h / 2), C["paint"], bevel=0.04))
    # sloped glacis plate at the front, engine deck grille at the back
    hull.append(box((W - 0.1, L * 0.2, 0.06), (0, -L * 0.4, h + deck_h * 0.35), C["paint"], rot=(math.radians(-28), 0, 0), bevel=0.02))
    for k in range(4):
        hull.append(box((W * 0.5, 0.03, 0.02), (0, L * 0.28 + k * 0.05, h + deck_h + 0.005), C["dark"], bevel=0.0))
    hull.append(box((0.1, L * 0.5, 0.02), (0, 0.0, h + deck_h + 0.003), TT, bevel=0.005))
    hull += headlights(-L * 0.47, h + 0.06, (-W * 0.3, W * 0.3), C, 0.035)
    hull += [cyl(0.03, 0.03, (x, L * 0.44, h + deck_h * 0.6), C["red_light"], rot=(R90, 0, 0), verts=8) for x in (-W * 0.35, W * 0.35)]
    # exhausts
    for s in (-1, 1):
        hull.append(cyl(0.035, 0.1, (s * W * 0.28, L * 0.43, h + deck_h + 0.02), C["dark"], rot=(R90, 0, 0), verts=8))
    pivot = (0, 0.02 * L, h + deck_h)
    tur = turret_fn(pivot, TM, TT, C)
    root = join(flatten(hull), name)
    export(root, name, [(join(flatten(tur), "turret", pivot), root)])


def turret_light(p, TM, TT, C):
    x, y, z = p
    return [box((0.5, 0.56, 0.2), (x, y + 0.03, z + 0.1), TM, bevel=0.06, segs=2),
            box((0.36, 0.3, 0.06), (x, y + 0.06, z + 0.22), TT, bevel=0.02),
            cyl(0.08, 0.14, (x, y - 0.26, z + 0.1), C["gun"], rot=(R90, 0, 0), verts=12, bevel=0.01),
            cyl(0.035, 0.52, (x, y - 0.5, z + 0.1), C["gun"], rot=(R90, 0, 0), verts=10),
            cyl(0.05, 0.08, (x, y - 0.75, z + 0.1), C["dark"], rot=(R90, 0, 0), verts=10),
            cyl(0.06, 0.05, (x + 0.12, y + 0.1, z + 0.25), C["dark"], verts=10),
            rod((x - 0.18, y + 0.2, z + 0.2), (x - 0.18, y + 0.24, z + 0.55), 0.008, C["dark"], verts=4)]


def turret_medium(p, TM, TT, C):
    x, y, z = p
    return [cyl(0.36, 0.08, (x, y, z + 0.04), C["gun"], verts=20),
            box((0.64, 0.7, 0.24), (x, y + 0.02, z + 0.18), TM, bevel=0.08, segs=2),
            box((0.44, 0.24, 0.2), (x, y - 0.3, z + 0.16), TM, rot=(math.radians(12), 0, 0), bevel=0.06),
            box((0.3, 0.2, 0.06), (x - 0.08, y + 0.12, z + 0.32), TT, bevel=0.02),
            cyl(0.08, 0.06, (x + 0.17, y + 0.08, z + 0.33), C["dark"], verts=12),
            cyl(0.045, 0.75, (x, y - 0.72, z + 0.17), C["gun"], rot=(R90, 0, 0), verts=12),
            box((0.14, 0.1, 0.08), (x, y - 1.1, z + 0.17), C["dark"], bevel=0.02),
            box((0.1, 0.18, 0.1), (x, y + 0.42, z + 0.18), C["gun"], bevel=0.02),
            rod((x - 0.22, y + 0.25, z + 0.3), (x - 0.24, y + 0.3, z + 0.7), 0.008, C["dark"], verts=4)]


def turret_heavy(p, TM, TT, C):
    x, y, z = p
    t = [cyl(0.46, 0.1, (x, y, z + 0.05), C["gun"], verts=16),
         box((0.84, 0.9, 0.3), (x, y + 0.04, z + 0.23), TM, bevel=0.1, segs=2),
         box((0.62, 0.32, 0.26), (x, y - 0.4, z + 0.2), TM, rot=(math.radians(14), 0, 0), bevel=0.08),
         box((0.5, 0.26, 0.06), (x, y + 0.2, z + 0.41), TT, bevel=0.02),
         box((0.26, 0.24, 0.12), (x, y + 0.56, z + 0.24), C["gun"], bevel=0.03)]
    for s in (-1, 1):  # twin barrels
        t += [cyl(0.05, 0.9, (x + s * 0.13, y - 0.9, z + 0.22), C["gun"], rot=(R90, 0, 0), verts=10),
              cyl(0.065, 0.14, (x + s * 0.13, y - 1.36, z + 0.22), C["dark"], rot=(R90, 0, 0), verts=10, bevel=0.01),
              cyl(0.07, 0.14, (x + s * 0.13, y - 0.55, z + 0.22), C["dark"], rot=(R90, 0, 0), verts=10)]
    t += [cyl(0.09, 0.07, (x + 0.24, y + 0.18, z + 0.42), C["dark"], verts=10),
          box((0.05, 0.22, 0.05), (x + 0.24, y + 0.05, z + 0.48), C["gun"], bevel=0.01),
          rod((x - 0.3, y + 0.35, z + 0.38), (x - 0.34, y + 0.42, z + 0.85), 0.01, C["dark"], verts=4)]
    return t


def jeep():
    TM, TT = team()
    C = common()
    L, W = 1.6, 0.86
    r = 0.17
    hull = []
    for s in (-1, 1):
        for y in (-0.5, 0.48):
            hull += wheel(s * (W / 2 - 0.06), y, r, 0.14, s, C)
            hull.append(box((0.2, 0.36, 0.04), (s * (W / 2 - 0.06), y, 2 * r + 0.03), C["paint"], bevel=0.015))  # mudguards
    hull.append(box((W - 0.24, L * 0.9, 0.12), (0, 0, r + 0.02), C["gun"], bevel=0.02))
    hull.append(box((W - 0.06, L * 0.86, 0.16), (0, 0.02, r + 0.14), C["paint"], bevel=0.04))
    hull.append(box((W - 0.12, 0.42, 0.1), (0, -0.52, r + 0.26), C["paint"], bevel=0.04))  # bonnet
    hull.append(box((W - 0.2, 0.36, 0.015), (0, -0.52, r + 0.315), TM, bevel=0.005))       # team bonnet panel
    hull.append(box((0.26, 0.04, 0.1), (0, -0.74, r + 0.2), C["dark"], bevel=0.01))       # grille
    hull += headlights(-0.745, r + 0.22, (-0.28, 0.28), C, 0.04)
    hull.append(box((W - 0.1, 0.03, 0.2), (0, -0.3, r + 0.36), C["dark"], rot=(math.radians(-15), 0, 0), bevel=0.01))
    hull.append(box((W - 0.16, 0.02, 0.15), (0, -0.305, r + 0.36), C["glass"], rot=(math.radians(-15), 0, 0), bevel=0.005))
    for s in (-1, 1):  # seats, roll bar, side stripes
        hull.append(box((0.24, 0.2, 0.08), (s * 0.18, -0.1, r + 0.25), C["dark"], bevel=0.03))
        hull.append(box((0.24, 0.06, 0.18), (s * 0.18, 0.0, r + 0.33), C["dark"], bevel=0.025))
        hull.append(box((0.02, L * 0.6, 0.06), (s * (W / 2 - 0.02), 0.05, r + 0.15), TT, bevel=0.008))
        hull.append(rod((s * 0.36, 0.12, r + 0.22), (s * 0.34, 0.12, r + 0.62), 0.02, C["gun"], verts=8))
    hull.append(rod((-0.34, 0.12, r + 0.62), (0.34, 0.12, r + 0.62), 0.02, C["gun"], verts=8))
    hull.append(cyl(r * 0.9, 0.1, (0, 0.76, r + 0.2), C["rubber"], rot=(R90, 0, 0), verts=14, bevel=0.02))  # spare
    hull.append(cyl(0.05, 0.3, (0, 0.45, r + 0.37), C["gun"], verts=10))                                   # gun post
    pivot = (0, 0.45, r + 0.52)
    x, y, z = pivot
    tur = [cyl(0.06, 0.05, (x, y, z), C["gun"], verts=10),
           box((0.1, 0.4, 0.1), (x, y - 0.08, z + 0.07), C["gun"], bevel=0.02),
           cyl(0.02, 0.36, (x, y - 0.44, z + 0.08), C["dark"], rot=(R90, 0, 0), verts=8),
           cyl(0.03, 0.06, (x, y - 0.62, z + 0.08), C["dark"], rot=(R90, 0, 0), verts=8),
           box((0.08, 0.1, 0.1), (x + 0.1, y - 0.02, z + 0.04), TT, bevel=0.015),        # ammo box
           box((0.34, 0.03, 0.18), (x, y - 0.22, z + 0.12), TM, bevel=0.012),            # gun shield
           rod((x - 0.03, y + 0.1, z + 0.05), (x - 0.03, y + 0.2, z + 0.02), 0.012, C["dark"], verts=6)]
    root = join(flatten(hull), "jeep")
    export(root, "jeep", [(join(flatten(tur), "turret", pivot), root)])


def apc():
    TM, TT = team()
    C = common()
    L, W, r = 2.0, 1.1, 0.19
    hull = []
    for s in (-1, 1):
        for y in (-0.62, 0.0, 0.62):
            hull += wheel(s * (W / 2 - 0.08), y, r, 0.16, s, C)
    hull.append(box((W - 0.3, L * 0.9, 0.16), (0, 0, r), C["gun"], bevel=0.02))
    hull.append(box((W, L * 0.94, 0.3), (0, 0.02, 2 * r + 0.1), C["paint"], bevel=0.04))
    hull.append(box((W - 0.12, L * 0.62, 0.2), (0, 0.18, 2 * r + 0.34), C["paint"], bevel=0.05))
    hull.append(box((W - 0.08, 0.36, 0.08), (0, -0.78, 2 * r + 0.24), C["paint"], rot=(math.radians(-30), 0, 0), bevel=0.03))
    hull.append(box((W - 0.22, 0.2, 0.06), (0, -0.55, 2 * r + 0.3), C["glass"], rot=(math.radians(-18), 0, 0), bevel=0.02))
    for s in (-1, 1):
        hull.append(box((0.03, L * 0.8, 0.08), (s * (W / 2 + 0.005), 0.02, 2 * r + 0.1), TT, bevel=0.01))
        hull.append(box((0.04, 0.3, 0.14), (s * (W / 2 + 0.01), 0.55, 2 * r + 0.34), C["dark"], bevel=0.015))  # stowage
        for k in range(3):  # periscopes / vision blocks
            hull.append(box((0.04, 0.08, 0.05), (s * (W / 2 - 0.05), -0.1 + k * 0.28, 2 * r + 0.46), C["glass"], bevel=0.01))
    hull.append(box((W - 0.3, 0.05, 0.36), (0, 0.97, 2 * r + 0.14), C["gun"], bevel=0.02))  # rear ramp
    hull.append(box((W * 0.5, 0.5, 0.02), (0, 0.45, 2 * r + 0.445), TM, bevel=0.006))       # roof team panel
    hull += headlights(-0.95, 2 * r + 0.08, (-0.38, 0.38), C, 0.04)
    pivot = (0, -0.18, 2 * r + 0.44)
    x, y, z = pivot
    tur = [cyl(0.2, 0.08, (x, y, z + 0.04), C["gun"], verts=16),
           box((0.34, 0.36, 0.16), (x, y, z + 0.14), TM, bevel=0.05),
           box((0.12, 0.08, 0.06), (x + 0.08, y + 0.08, z + 0.24), C["dark"], bevel=0.015)]
    for s in (-1, 1):
        tur.append(cyl(0.022, 0.42, (x + s * 0.06, y - 0.36, z + 0.14), C["dark"], rot=(R90, 0, 0), verts=8))
    root = join(flatten(hull), "apc")
    export(root, "apc", [(join(flatten(tur), "turret", pivot), root)])


def missile_launcher():
    TM, TT = team()
    C = common()
    L, W, r = 2.2, 1.06, 0.18
    red = mat("missile_red", (0.85, 0.16, 0.1), 0.4, coat=0.3)
    white = mat("missile_white", (0.9, 0.9, 0.86), 0.45)
    hull = []
    for s in (-1, 1):
        for y in (-0.72, 0.28, 0.72):
            hull += wheel(s * (W / 2 - 0.08), y, r, 0.16, s, C)
    hull.append(box((W - 0.3, L * 0.92, 0.14), (0, 0, r + 0.02), C["gun"], bevel=0.02))
    hull.append(box((W, L * 0.94, 0.12), (0, 0.02, 2 * r + 0.06), C["paint"], bevel=0.03))  # flatbed
    hull.append(box((W - 0.04, 0.6, 0.4), (0, -0.74, 2 * r + 0.3), C["paint"], bevel=0.06))  # cab
    hull.append(box((W - 0.14, 0.04, 0.2), (0, -1.045, 2 * r + 0.36), C["glass"], bevel=0.02))
    for s in (-1, 1):
        hull.append(box((0.03, 0.34, 0.16), (s * (W / 2 - 0.005), -0.74, 2 * r + 0.36), C["glass"], bevel=0.01))
        hull.append(box((0.03, L * 0.6, 0.06), (s * (W / 2 + 0.005), 0.3, 2 * r + 0.07), TT, bevel=0.01))
        hull.append(box((0.12, 0.3, 0.14), (s * (W / 2 - 0.1), 0.95, 2 * r + 0.18), C["gun"], bevel=0.02))  # stabiliser legs
    hull.append(box((W - 0.2, 0.44, 0.02), (0, -0.74, 2 * r + 0.505), TM, bevel=0.006))
    hull += headlights(-1.05, 2 * r + 0.14, (-0.36, 0.36), C, 0.04)
    hull.append(cyl(0.035, 0.03, (0, -0.74, 2 * r + 0.53), C["lamp"], verts=8))
    pivot = (0, 0.32, 2 * r + 0.12)
    x, y, z = pivot
    tur = [cyl(0.36, 0.1, (x, y, z + 0.05), C["gun"], verts=20),
           box((0.2, 0.3, 0.24), (x, y, z + 0.2), C["gun"], bevel=0.03)]
    tilt = math.radians(22)
    cz = z + 0.44
    tur.append(box((0.8, 0.95, 0.36), (x, y + 0.05, cz), TM, rot=(tilt, 0, 0), bevel=0.05))
    tur.append(box((0.82, 0.3, 0.38), (x, y + 0.35, cz + 0.12), TT, rot=(tilt, 0, 0), bevel=0.03))
    fwd = Vector((0, -math.cos(tilt), math.sin(tilt)))
    face = Vector((x, y + 0.05, cz)) + fwd * 0.476
    for i in range(3):
        for j in range(2):
            off = Vector(((i - 1) * 0.24, 0, 0)) + Vector((0, math.sin(tilt), math.cos(tilt))) * ((j - 0.5) * 0.16)
            c = face + off
            tur.append(cyl(0.07, 0.02, tuple(c), C["dark"], rot=(R90 - tilt, 0, 0), verts=12))
            tur.append(cyl(0.05, 0.12, tuple(c + fwd * 0.04), red if (i + j) % 2 == 0 else white, rot=(-R90 - tilt, 0, 0), r2=0.0, verts=10))
    root = join(flatten(hull), "missile_launcher")
    export(root, "missile_launcher", [(join(flatten(tur), "turret", pivot), root)])


# ------------------------------------------------------------------ cannons

def cannon_base(C, TT):
    return [cyl(0.95, 0.12, (0, 0, 0.06), C["concrete_dark"], verts=8, bevel=0.02),
            cyl(0.8, 0.22, (0, 0, 0.22), C["concrete"], verts=8, bevel=0.03, segs=2),
            cyl(0.82, 0.06, (0, 0, 0.26), TT, verts=8, bevel=0.01),
            cyl(0.56, 0.08, (0, 0, 0.36), C["gun"], verts=24, bevel=0.01)] + \
           [box((0.12, 0.04, 0.05), (0.84 * math.cos(a), 0.84 * math.sin(a), 0.14), C["hazard"], rot=(0, 0, a + R90), bevel=0.01)
            for a in [k * math.pi / 4 + math.pi / 8 for k in range(8)]]


def cannon(name, tur_fn):
    TM, TT = team()
    C = common()
    pivot = (0, 0, 0.4)
    root = join(flatten(cannon_base(C, TT)), name)
    export(root, name, [(join(flatten(tur_fn(pivot, TM, TT, C)), "turret", pivot), root)])


def tur_gatling(p, TM, TT, C):
    x, y, z = p
    t = [cyl(0.42, 0.12, (x, y, z + 0.06), C["gun"], verts=20),
         sphere(0.4, (x, y + 0.05, z + 0.28), TM, scale=(1, 1.05, 0.7), segs=16, rings=10),
         box((0.5, 0.2, 0.12), (x, y + 0.1, z + 0.5), TT, bevel=0.04),
         box((0.2, 0.3, 0.2), (x + 0.38, y + 0.05, z + 0.26), C["dark"], bevel=0.04),
         cyl(0.16, 0.2, (x, y - 0.36, z + 0.28), C["gun"], rot=(R90, 0, 0), verts=12, bevel=0.02)]
    for k in range(6):
        a = k * math.pi / 3
        t.append(cyl(0.028, 0.6, (x + 0.08 * math.cos(a), y - 0.72, z + 0.28 + 0.08 * math.sin(a)), C["dark"], rot=(R90, 0, 0), verts=8))
    for yy in (-0.6, -1.0):
        t.append(cyl(0.13, 0.04, (x, y + yy, z + 0.28), C["gun"], rot=(R90, 0, 0), verts=12))
    t.append(cyl(0.04, 0.03, (x - 0.2, y - 0.25, z + 0.44), C["red_light"], verts=8))
    return t


def tur_gun(p, TM, TT, C):
    x, y, z = p
    return [cyl(0.5, 0.1, (x, y, z + 0.05), C["gun"], verts=20),
            box((0.8, 0.72, 0.36), (x, y + 0.08, z + 0.27), TM, bevel=0.1, segs=2),
            box((0.7, 0.3, 0.32), (x, y - 0.3, z + 0.26), TM, rot=(math.radians(20), 0, 0), bevel=0.08),
            box((0.6, 0.3, 0.06), (x, y + 0.2, z + 0.47), TT, bevel=0.02),
            cyl(0.13, 0.2, (x, y - 0.46, z + 0.26), C["gun"], rot=(R90, 0, 0), verts=14, bevel=0.02),
            cyl(0.06, 0.95, (x, y - 0.95, z + 0.26), C["gun"], rot=(R90, 0, 0), verts=12),
            box((0.18, 0.14, 0.1), (x, y - 1.44, z + 0.26), C["dark"], bevel=0.02),
            cyl(0.07, 0.04, (x - 0.22, y + 0.3, z + 0.5), C["dark"], verts=10)]


def tur_howitzer(p, TM, TT, C):
    x, y, z = p
    el = math.radians(32)
    d = Vector((0, -math.cos(el), math.sin(el)))
    o = Vector((x, y + 0.05, z + 0.42))
    t = [cyl(0.55, 0.1, (x, y, z + 0.05), C["gun"], verts=20),
         box((0.9, 0.8, 0.22), (x, y + 0.1, z + 0.2), C["gun"], bevel=0.05)]
    for s in (-1, 1):  # trunnion cheeks
        t.append(box((0.12, 0.5, 0.42), (x + s * 0.3, y + 0.05, z + 0.4), TM, bevel=0.05))
        t.append(cyl(0.1, 0.06, (x + s * 0.37, y + 0.05, z + 0.42), TT, rot=(0, R90, 0), verts=12))
        t.append(rod(tuple(o + Vector((s * 0.12, 0, -0.06)) + d * 0.1), tuple(o + Vector((s * 0.12, 0, -0.06)) + d * 0.6), 0.04, C["steel"], verts=10))
    t.append(rod(tuple(o - d * 0.35), tuple(o + d * 0.3), 0.16, TM, verts=14))
    t.append(rod(tuple(o + d * 0.3), tuple(o + d * 1.25), 0.085, C["gun"], r2=0.075, verts=14))
    t.append(rod(tuple(o + d * 1.2), tuple(o + d * 1.4), 0.11, C["dark"], verts=14))
    t.append(box((0.6, 0.3, 0.2), (x, y + 0.45, z + 0.3), TT, bevel=0.04))
    return t


def tur_missile(p, TM, TT, C):
    x, y, z = p
    red = mat("missile_red", (0.85, 0.16, 0.1), 0.4, coat=0.3)
    el = math.radians(28)
    t = [cyl(0.45, 0.1, (x, y, z + 0.05), C["gun"], verts=20),
         box((0.24, 0.3, 0.34), (x, y + 0.05, z + 0.25), C["gun"], bevel=0.04)]
    fwd = Vector((0, -math.cos(el), math.sin(el)))
    up = Vector((0, math.sin(el), math.cos(el)))
    for s in (-1, 1):  # two pods of two missiles
        c = Vector((x + s * 0.3, y, z + 0.48))
        t.append(box((0.36, 0.9, 0.36), tuple(c), TM, rot=(el, 0, 0), bevel=0.06))
        t.append(box((0.38, 0.12, 0.38), tuple(c - fwd * 0.3), TT, rot=(el, 0, 0), bevel=0.02))
        for i in (-1, 1):
            for j in (-1, 1):
                m = c + fwd * 0.45 + Vector((i * 0.085, 0, 0)) + up * (j * 0.085)
                t.append(cyl(0.065, 0.02, tuple(m), C["dark"], rot=(R90 - el, 0, 0), verts=10))
                t.append(cyl(0.05, 0.14, tuple(m + fwd * 0.05), red, rot=(-R90 - el, 0, 0), r2=0.0, verts=10))
    t.append(cyl(0.06, 0.3, (x, y + 0.2, z + 0.55), C["gun"], verts=8))
    t.append(box((0.3, 0.02, 0.18), (x, y + 0.2, z + 0.72), C["steel"], bevel=0.005))
    return t


# ------------------------------------------------------------------ buildings

def crenels(x0, y0, x1, y1, z, m, size=0.22, step=0.5, thick=0.18):
    """A row of merlons from (x0, y0) to (x1, y1) on top of a wall at height z."""
    d = Vector((x1 - x0, y1 - y0, 0))
    n = max(1, int(d.length / step))
    p = []
    for k in range(n + 1):
        c = Vector((x0, y0, 0)) + d * (k / n)
        rot = (0, 0, math.atan2(d.y, d.x))
        p.append(box((size, thick, size * 0.9), (c.x, c.y, z + size * 0.45), m, rot=rot, bevel=0.0))
    return p


def fort():
    TM, TT = team()
    C = common()
    wall = mat("fort_wall", (0.62, 0.6, 0.55), 0.8)
    cap = mat("fort_cap", (0.42, 0.41, 0.4), 0.7, 0.2)
    floor = mat("fort_floor", (0.5, 0.48, 0.44), 0.9)
    WX, WY, T, H = 10.0, 12.0, 0.6, 1.3
    ex, ey = WX / 2 - T / 2 - 0.25, WY / 2 - T / 2 - 0.25  # buttresses, towers and banners stay inside the footprint
    gy = -(WY / 2 - 0.65)
    p = [box((WX - 0.2, WY - 0.2, 0.08), (0, 0, 0.04), floor, bevel=0.02)]
    # courtyard paving lines
    for k in range(-4, 5):
        p.append(box((WX - 1.6, 0.03, 0.012), (0, k * 1.2, 0.083), C["concrete_dark"], bevel=0.0))
    gate = 1.1
    segs = [((-ex, ey), (ex, ey)), ((-ex, -ey), (-ex, ey)), ((ex, -ey), (ex, ey)),
            ((-ex, -ey), (-gate - 0.4, -ey)), ((gate + 0.4, -ey), (ex, -ey))]
    for (x0, y0), (x1, y1) in segs:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        lx, ly = abs(x1 - x0) + T, abs(y1 - y0) + T
        p.append(box((lx, ly, H), (cx, cy, H / 2), wall, bevel=0.05))
        p.append(box((lx + 0.06, ly + 0.06, 0.1), (cx, cy, H + 0.02), cap, bevel=0.02))
        p.append(box((lx + 0.03, ly + 0.03, 0.12), (cx, cy, H * 0.55), TT, bevel=0.01))  # team band
        # buttresses on the outer face
        n = int(max(lx, ly) / 2.2)
        for k in range(1, n):
            t = k / n
            bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            ox = (T / 2 + 0.1) * (1 if bx > 0 else -1) if ly > lx else 0
            oy = (T / 2 + 0.1) * (1 if by > 0 else -1) if lx > ly else 0
            p.append(box((0.3 if ly <= lx else 0.2, 0.2 if ly <= lx else 0.3, H * 0.85), (bx + ox, by + oy, H * 0.42), wall, bevel=0.04))
        # merlons along the outer edge
        if lx > ly:
            oy = (T / 2 - 0.09) * (1 if cy > 0 else -1)
            p += crenels(x0, y0 + oy, x1, y1 + oy, H + 0.07, cap)
        else:
            ox = (T / 2 - 0.09) * (1 if cx > 0 else -1)
            p += crenels(x0 + ox, y0, x1 + ox, y1, H + 0.07, cap)
    # corner towers with team roofs
    for sx in (-1, 1):
        for sy in (-1, 1):
            tx, ty = sx * (WX / 2 - 1.05), sy * (WY / 2 - 1.05)
            p.append(cyl(0.95, 2.2, (tx, ty, 1.1), wall, verts=12, bevel=0.04))
            p.append(cyl(1.05, 0.14, (tx, ty, 2.2), cap, verts=12, bevel=0.02))
            p.append(cyl(1.0, 0.1, (tx, ty, 1.5), TT, verts=12, bevel=0.01))
            p.append(cyl(0.98, 0.9, (tx, ty, 2.72), TM, r2=0.12, verts=12, bevel=0.02))
            p.append(sphere(0.12, (tx, ty, 3.2), C["lamp"], segs=8, rings=6))
            a = math.atan2(sy, sx)
            p.append(box((0.08, 0.3, 0.12), (tx + 0.96 * math.cos(a), ty + 0.96 * math.sin(a), 1.9), C["lamp"], rot=(0, 0, a), bevel=0.01))
            p.append(box((0.5, 0.05, 0.8), (tx + 0.98 * math.cos(a), ty + 0.98 * math.sin(a), 1.0), TM, rot=(0, 0, a + R90), bevel=0.01))
    # gatehouse: two squat towers, a lintel and the gate door
    for s in (-1, 1):
        gx = s * (gate + 0.55)
        p.append(box((1.1, 1.2, 1.9), (gx, gy, 0.95), wall, bevel=0.06))
        p.append(box((1.2, 1.2, 0.1), (gx, gy, 1.92), cap, bevel=0.02))
        p += crenels(gx - 0.45, gy - 0.5, gx + 0.45, gy - 0.5, 1.97, cap, step=0.45)
        p.append(box((0.5, 0.05, 0.9), (gx, gy - 0.62, 1.1), TM, bevel=0.01))  # banners
        p.append(box((0.5, 0.06, 0.08), (gx, gy - 0.62, 1.56), C["gun"], bevel=0.01))
        p.append(box((0.12, 0.08, 0.3), (gx, gy - 0.61, 0.4), C["lamp"], bevel=0.01))
    p.append(box((2 * gate + 0.2, 1.0, 0.45), (0, gy, 1.6), wall, bevel=0.05))
    p.append(box((2 * gate, 0.14, 1.35), (0, -ey - 0.05, 0.675), C["gun"], bevel=0.02))
    for k in range(-3, 4):
        p.append(box((0.06, 0.18, 1.3), (k * 0.3, -ey - 0.07, 0.65), C["dark"], bevel=0.0))
    p.append(box((2 * gate, 0.2, 0.12), (0, -ey - 0.08, 1.2), TT, bevel=0.02))
    p.append(box((1.0, 0.1, 0.24), (0, gy - 0.5, 1.6), C["hazard"], bevel=0.02))
    # the keep: two stories, team roof, glowing windows, antenna and a helipad-style roof mark
    ky = 1.0
    p.append(box((4.4, 4.6, 2.2), (0, ky, 1.1), wall, bevel=0.08))
    p.append(box((4.6, 4.8, 0.14), (0, ky, 2.2), cap, bevel=0.03))
    p.append(box((4.44, 4.64, 0.14), (0, ky, 1.4), TT, bevel=0.01))
    p.append(box((3.2, 3.2, 1.0), (0, ky + 0.3, 2.75), wall, bevel=0.08))
    p.append(box((3.4, 3.4, 0.14), (0, ky + 0.3, 3.3), TM, bevel=0.04))
    p.append(cyl(0.9, 0.04, (0, ky + 0.3, 3.39), cap, verts=20))
    p.append(cyl(0.7, 0.045, (0, ky + 0.3, 3.395), C["hazard"], verts=20))
    p.append(cyl(0.55, 0.05, (0, ky + 0.3, 3.4), cap, verts=20))
    for x0, y0, x1, y1 in ((-2.2, ky - 2.25, 2.2, ky - 2.25), (-2.2, ky + 2.25, 2.2, ky + 2.25),
                           (-2.25, ky - 2.2, -2.25, ky + 2.2), (2.25, ky - 2.2, 2.25, ky + 2.2)):
        p += crenels(x0, y0, x1, y1, 2.27, cap, step=0.55)
    for k in range(-2, 3):  # windows on the front and sides
        p.append(box((0.3, 0.06, 0.2), (k * 0.8, ky - 2.31, 1.85), C["lamp"], bevel=0.01))
        p.append(box((0.3, 0.06, 0.16), (k * 0.6, ky + 0.3 - 1.61, 2.8), C["lamp"], bevel=0.01))
        for s in (-1, 1):
            p.append(box((0.06, 0.3, 0.2), (s * 2.21, ky + k * 0.8, 1.85), C["lamp"], bevel=0.01))
    p.append(box((1.2, 0.2, 1.1), (0, ky - 2.3, 0.55), C["gun"], bevel=0.03))
    p.append(box((1.4, 0.3, 0.12), (0, ky - 2.35, 1.16), TT, bevel=0.02))
    for s in (-1, 1):
        p.append(box((0.7, 0.05, 1.4), (s * 1.4, ky - 2.33, 1.2), TM, bevel=0.01))  # keep banners
        p.append(box((0.8, 0.08, 0.08), (s * 1.4, ky - 2.34, 1.92), C["gun"], bevel=0.01))
    p.append(rod((1.3, ky + 1.3, 3.3), (1.3, ky + 1.3, 4.6), 0.04, C["steel"], verts=8))
    p.append(sphere(0.08, (1.3, ky + 1.3, 4.62), C["red_light"], segs=8, rings=6))
    for z in (3.8, 4.2):
        p.append(rod((1.1, ky + 1.3, z), (1.5, ky + 1.3, z), 0.015, C["steel"], verts=6))
    # courtyard clutter: crates, fuel drums, a flag spot
    rnd = random.Random(8)
    crate = mat("crate_olive", (0.34, 0.38, 0.22), 0.8)
    for cx, cy in ((-3.4, -3.6), (-3.0, -3.9), (3.3, -3.8), (-3.5, 4.2), (3.4, 4.5)):
        s = rnd.uniform(0.35, 0.5)
        p.append(box((s, s, s), (cx, cy, 0.08 + s / 2), crate, rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.03))
    drum = mat("drum_red", (0.6, 0.14, 0.1), 0.5, 0.4)
    for cx, cy in ((3.0, 3.8), (3.3, 3.5), (2.8, 3.3)):
        p.append(cyl(0.18, 0.42, (cx, cy, 0.29), drum, verts=12, bevel=0.02))
    simple(p, "fort")


def slab(w, d, C, h=0.1):
    return box((w - 0.04, d - 0.04, h), (0, 0, h / 2), C["concrete_dark"], bevel=0.03)


def robot_factory():
    TM, TT = team()
    C = common()
    wall = mat("factory_wall", (0.58, 0.58, 0.6), 0.6, 0.3)
    roof = mat("factory_roof", (0.3, 0.31, 0.33), 0.6, 0.5)
    p = [slab(4, 5, C)]
    p.append(box((3.4, 3.0, 1.5), (0, 0.6, 0.85), wall, bevel=0.06))
    p.append(box((3.5, 3.1, 0.12), (0, 0.6, 1.62), roof, bevel=0.03))
    p.append(box((3.52, 3.12, 0.12), (0, 0.6, 1.2), TT, bevel=0.01))
    # sawtooth skylights on the roof
    for k in range(3):
        y = -0.4 + k * 0.85
        p.append(box((3.0, 0.55, 0.22), (0, y + 0.15, 1.78), TM, rot=(math.radians(-25), 0, 0), bevel=0.02))
        p.append(box((2.9, 0.04, 0.22), (0, y - 0.1, 1.76), C["lamp"], bevel=0.005))
    # front annex with the robot exit and a big robot-head sign
    p.append(box((2.4, 1.2, 1.0), (0, -1.3, 0.6), wall, bevel=0.05))
    p.append(box((2.5, 1.3, 0.1), (0, -1.3, 1.12), roof, bevel=0.02))
    p.append(box((1.1, 0.1, 0.8), (0, -1.9, 0.5), C["dark"], bevel=0.02))
    for k in range(4):
        p.append(box((1.0, 0.12, 0.03), (0, -1.91, 0.2 + k * 0.18), C["gun"], bevel=0.0))
    p.append(box((1.3, 0.14, 0.1), (0, -1.93, 0.95), C["hazard"], bevel=0.02))
    p.append(box((0.08, 0.14, 0.8), (-0.62, -1.93, 0.5), C["hazard"], bevel=0.02))
    p.append(box((0.08, 0.14, 0.8), (0.62, -1.93, 0.5), C["hazard"], bevel=0.02))
    p.append(box((4.0 - 0.3, 0.8, 0.02), (0, -2.1, 0.105), C["concrete"], bevel=0.0))  # apron
    for k in range(-3, 4):
        p.append(box((0.24, 0.12, 0.01), (k * 0.45, -2.2, 0.12), C["hazard"], rot=(0, 0, 0.6), bevel=0.0))
    head = [box((0.8, 0.6, 0.55), (0, -1.2, 1.5), TM, bevel=0.16, segs=3),
            box((0.6, 0.06, 0.14), (0, -1.51, 1.52), mat("sign_visor", (0.3, 0.9, 1.0), 0.2, emit=5.0), bevel=0.03),
            rod((0, -1.2, 1.75), (0, -1.2, 2.05), 0.02, C["steel"], verts=6),
            sphere(0.05, (0, -1.2, 2.07), C["red_light"], segs=8, rings=6)]
    for s in (-1, 1):
        head.append(cyl(0.1, 0.1, (s * 0.44, -1.2, 1.5), C["gun"], rot=(0, R90, 0), verts=12))
    p += head
    # chimneys and pipes at the back
    for x in (-1.1, 1.1):
        p.append(cyl(0.22, 1.4, (x, 1.6, 2.2), C["steel"], verts=14, bevel=0.02))
        p.append(cyl(0.26, 0.12, (x, 1.6, 2.85), TT, verts=14))
        p.append(cyl(0.16, 0.04, (x, 1.6, 2.91), mat("ember", (1.0, 0.45, 0.1), 0.4, emit=6.0), verts=14))
    for s in (-1, 1):
        p.append(rod((s * 1.72, -0.5, 0.35), (s * 1.72, 1.8, 0.35), 0.08, C["steel"], verts=10))
        p.append(box((0.3, 0.6, 0.5), (s * 1.78, -0.9, 0.35), C["gun"], bevel=0.04))
        p.append(box((0.06, 0.3, 0.12), (s * 1.94, -0.9, 0.45), C["green_light"], bevel=0.01))
    simple(p, "robot_factory")


def vehicle_factory():
    TM, TT = team()
    C = common()
    wall = mat("factory_wall", (0.58, 0.58, 0.6), 0.6, 0.3)
    roof = mat("hangar_roof", (0.44, 0.45, 0.47), 0.45, 0.6)
    p = [slab(4, 5, C)]
    p.append(box((3.6, 4.2, 1.0), (0, 0.2, 0.6), wall, bevel=0.05))
    p.append(cyl(1.85, 4.3, (0, 0.2, 1.05), roof, rot=(R90, 0, 0), verts=24, bevel=0.02))
    for k in range(6):  # roof ribs in team trim
        y = -1.8 + k * 0.8
        p.append(cyl(1.88, 0.08, (0, y, 1.05), TT, rot=(R90, 0, 0), verts=24))
    p.append(box((3.64, 4.24, 0.9), (0, 0.2, 0.55), wall, bevel=0.05))
    # the big door on -Y with hazard chevrons and a glowing header
    p.append(box((2.8, 0.1, 1.9), (0, -1.9, 1.0), C["gun"], bevel=0.03))
    for k in range(7):
        p.append(box((2.7, 0.12, 0.04), (0, -1.92, 0.2 + k * 0.24), C["dark"], bevel=0.0))
    for s in (-1, 1):
        p.append(box((0.2, 0.3, 2.3), (s * 1.55, -1.95, 1.15), TM, bevel=0.04))
        for k in range(5):
            p.append(box((0.22, 0.02, 0.1), (s * 1.55, -2.11, 0.3 + k * 0.42), C["hazard"], rot=(0, 0.6 * s, 0), bevel=0.0))
    p.append(box((3.3, 0.3, 0.3), (0, -1.95, 2.15), TM, bevel=0.05))
    p.append(box((2.4, 0.04, 0.1), (0, -2.1, 2.15), C["lamp"], bevel=0.01))
    p.append(box((3.8, 0.4, 0.02), (0, -2.28, 0.105), C["concrete"], bevel=0.0))
    for x in (-0.6, 0.6):
        p.append(box((0.08, 0.36, 0.01), (x, -2.28, 0.12), C["hazard"], bevel=0.0))
    # side crane and exhaust stacks
    p.append(rod((1.9, 1.8, 0.1), (1.9, 1.8, 2.4), 0.06, C["hazard"], verts=8))
    p.append(rod((1.9, 1.8, 2.35), (1.9, 0.0, 2.35), 0.05, C["hazard"], verts=8))
    p.append(rod((1.9, 0.2, 2.33), (1.9, 0.2, 1.9), 0.01, C["dark"], verts=4))
    p.append(box((0.1, 0.12, 0.08), (1.9, 0.2, 1.86), C["dark"], bevel=0.01))
    for y in (1.2, 1.7):
        p.append(cyl(0.12, 0.8, (-1.6, y, 2.1), C["steel"], verts=12))
        p.append(cyl(0.14, 0.08, (-1.6, y, 2.5), TT, verts=12))
    p.append(cyl(0.06, 0.04, (0, 1.8, 2.92), C["red_light"], verts=8))
    simple(p, "vehicle_factory")


def radar():
    TM, TT = team()
    C = common()
    wall = mat("factory_wall", (0.58, 0.58, 0.6), 0.6, 0.3)
    dish_w = mat("dish_white", (0.88, 0.88, 0.86), 0.35, 0.1)
    p = [slab(4, 3, C)]
    # control hut
    p.append(box((1.6, 1.8, 0.9), (-1.0, 0.1, 0.55), wall, bevel=0.05))
    p.append(box((1.7, 1.9, 0.1), (-1.0, 0.1, 1.03), TT, bevel=0.02))
    p.append(box((1.2, 0.05, 0.2), (-1.0, -0.82, 0.75), C["glass"], bevel=0.01))
    p.append(box((1.1, 0.03, 0.12), (-1.0, -0.84, 0.75), mat("screen_glow", (0.35, 1.0, 0.6), 0.3, emit=3.0), bevel=0.0))
    p.append(box((0.4, 0.06, 0.6), (-0.5, -0.82, 0.4), C["gun"], bevel=0.02))
    for k in range(3):
        p.append(box((0.36, 0.3, 0.2), (-1.5 + k * 0.5, 0.5, 1.18), C["gun"], bevel=0.03))
    p.append(rod((-1.6, 0.8, 1.08), (-1.6, 0.8, 1.9), 0.015, C["steel"], verts=6))
    p.append(sphere(0.04, (-1.6, 0.8, 1.92), C["red_light"], segs=8, rings=6))
    # lattice mast
    mx, my = 0.85, 0.0
    top = 1.6
    legs = [(mx + sx * 0.55, my + sy * 0.55) for sx in (-1, 1) for sy in (-1, 1)]
    for (lx, ly) in legs:
        p.append(rod((lx, ly, 0.1), (mx + (lx - mx) * 0.35, my + (ly - my) * 0.35, top), 0.04, C["steel"], verts=6))
        p.append(box((0.18, 0.18, 0.08), (lx, ly, 0.14), C["concrete"], bevel=0.02))
    for z0, z1 in ((0.15, 0.85), (0.85, 1.55)):
        f0, f1 = 1 - 0.65 * (z0 - 0.1) / (top - 0.1), 1 - 0.65 * (z1 - 0.1) / (top - 0.1)
        loop = [legs[0], legs[1], legs[3], legs[2]]
        for i in range(4):
            a, b = loop[i], loop[(i + 1) % 4]
            pa = (mx + (a[0] - mx) * f0, my + (a[1] - my) * f0, z0)
            pb = (mx + (b[0] - mx) * f1, my + (b[1] - my) * f1, z1)
            p.append(rod(pa, pb, 0.018, C["steel"], verts=5))
    p.append(cyl(0.35, 0.1, (mx, my, top), C["gun"], verts=12, bevel=0.02))
    p.append(cyl(0.12, 0.2, (mx, my, top + 0.12), TT, verts=12))
    root = join(flatten(p), "radar")
    # the dish, spinning about the vertical axis through the mast top
    pv = (mx, my, top + 0.2)
    x, y, z = pv
    tilt = math.radians(35)
    n = Vector((0, -math.cos(tilt), math.sin(tilt)))
    c = Vector((x, y + 0.1, z + 0.55))
    d = [cyl(0.1, 0.12, (x, y, z + 0.06), C["gun"], verts=10),
         rod((x, y, z + 0.1), tuple(c - n * 0.05), 0.05, C["gun"], verts=8),
         cyl(0.95, 0.28, tuple(c - n * 0.02), dish_w, rot=(R90 - tilt, 0, 0), r2=0.28, verts=24, bevel=0.01),
         ring(0.95, 0.05, tuple(c + n * 0.12), TM, rot=(R90 - tilt, 0, 0)),
         cyl(0.28, 0.05, tuple(c - n * 0.14), TT, rot=(R90 - tilt, 0, 0), verts=16),
         box((0.3, 0.25, 0.3), tuple(c - n * 0.35), C["gun"], rot=(tilt, 0, 0), bevel=0.04)]
    for a in (0, 2 * math.pi / 3, 4 * math.pi / 3):
        rim = c + n * 0.12 + Vector((0.9 * math.cos(a), 0, 0)) + Vector((0, math.sin(tilt), math.cos(tilt))) * (0.9 * math.sin(a))
        d.append(rod(tuple(rim), tuple(c + n * 0.7), 0.012, C["steel"], verts=5))
    d.append(sphere(0.07, tuple(c + n * 0.72), C["red_light"], segs=8, rings=6))
    dish = join(flatten(d), "dish", pv)
    export(root, "radar", [(dish, root)])


def repair():
    TM, TT = team()
    C = common()
    pad = mat("pad_concrete", (0.52, 0.52, 0.5), 0.8)
    p = [slab(5, 4, C)]
    p.append(box((3.2, 3.2, 0.06), (-0.6, -0.1, 0.13), pad, bevel=0.02))
    for s in (-1, 1):  # hazard border and a team edge on the pad
        p.append(box((3.2, 0.12, 0.012), (-0.6, -0.1 + s * 1.5, 0.165), C["hazard"], bevel=0.0))
        p.append(box((0.12, 3.2, 0.012), (-0.6 + s * 1.5, -0.1, 0.165), C["hazard"], bevel=0.0))
        p.append(box((4.9, 0.08, 0.12), (0, s * 1.93, 0.12), TT, bevel=0.02))
    # a green glowing wrench-and-cross mark at the centre
    cross = mat("repair_glow", (0.3, 1.0, 0.4), 0.3, emit=3.5)
    p.append(box((1.1, 0.3, 0.012), (-0.6, -0.1, 0.165), cross, bevel=0.0))
    p.append(box((0.3, 1.1, 0.012), (-0.6, -0.1, 0.165), cross, bevel=0.0))
    for a in range(8):  # landing lights around the pad
        t = a * math.pi / 4
        p.append(cyl(0.05, 0.04, (-0.6 + 1.35 * math.cos(t), -0.1 + 1.35 * math.sin(t), 0.18), C["lamp"], verts=8))
    # the crane: a pillar with a boom reaching over the pad, a cable and a claw
    bx, by = 1.7, 1.2
    p.append(cyl(0.4, 0.2, (bx, by, 0.2), C["gun"], verts=12, bevel=0.02))
    p.append(cyl(0.2, 1.8, (bx, by, 1.2), C["hazard"], verts=12, bevel=0.02))
    p.append(box((0.5, 0.5, 0.4), (bx, by, 2.2), TM, bevel=0.06))
    p.append(box((0.3, 0.5, 0.25), (bx + 0.35, by + 0.2, 2.2), C["gun"], bevel=0.04))  # counterweight
    tip = Vector((-0.6, -0.1, 2.5))
    base = Vector((bx, by, 2.3))
    p.append(rod(tuple(base), tuple(tip), 0.08, C["hazard"], r2=0.06, verts=8))
    p.append(rod(tuple(base + Vector((0, 0, 0.1))), tuple(tip + Vector((0, 0, 0.08))), 0.02, C["dark"], verts=5))
    p.append(rod(tuple(tip), tuple(tip - Vector((0, 0, 1.2))), 0.012, C["dark"], verts=4))
    claw = tip - Vector((0, 0, 1.25))
    p.append(box((0.24, 0.24, 0.1), tuple(claw), C["gun"], bevel=0.02))
    for a in range(3):
        t = a * 2 * math.pi / 3
        p.append(rod(tuple(claw), tuple(claw + Vector((0.18 * math.cos(t), 0.18 * math.sin(t), -0.18))), 0.025, C["steel"], verts=5))
    # tool cabinets and a fuel pump on the side
    for k in range(3):
        p.append(box((0.5, 0.35, 0.7), (1.8, -1.4 + k * 0.55, 0.45), C["gun"] if k != 1 else TM, bevel=0.03))
        p.append(box((0.4, 0.02, 0.05), (1.8, -1.58 + k * 0.55, 0.6), C["steel"], bevel=0.0))
    p.append(box((0.35, 0.35, 0.8), (1.4, 0.4, 0.5), mat("pump_red", (0.7, 0.15, 0.1), 0.45, 0.2), bevel=0.05))
    p.append(box((0.2, 0.03, 0.15), (1.4, 0.22, 0.7), C["lamp"], bevel=0.01))
    simple(p, "repair")


def hut():
    TM, TT = team()
    C = common()
    wall = mat("hut_wall", (0.55, 0.5, 0.42), 0.85)
    p = [cyl(0.95, 0.1, (0, 0, 0.05), C["concrete_dark"], verts=10, bevel=0.02)]
    p.append(cyl(0.78, 0.5, (0, 0, 0.35), wall, verts=10, bevel=0.03))
    p.append(cyl(0.82, 0.08, (0, 0, 0.6), TT, verts=10))
    dome = sphere(0.78, (0, 0, 0.6), TM, scale=(1, 1, 0.7), segs=16, rings=10)
    p.append(dome)
    for k in range(4):  # roof straps
        p.append(box((0.04, 1.6, 0.04), (0, 0, 0.62), C["gun"], rot=(0, 0, k * math.pi / 4), bevel=0.0))
    # doorway on -Y with a glowing frame, a vent on top and a lamp
    p.append(box((0.5, 0.4, 0.62), (0, -0.7, 0.36), wall, bevel=0.04))
    p.append(box((0.34, 0.06, 0.46), (0, -0.9, 0.3), C["dark"], bevel=0.02))
    p.append(box((0.42, 0.05, 0.05), (0, -0.92, 0.56), C["red_light"], bevel=0.01))
    p.append(cyl(0.14, 0.2, (0.2, 0.2, 1.1), C["gun"], verts=10))
    p.append(cyl(0.18, 0.04, (0.2, 0.2, 1.21), C["gun"], verts=10))
    p.append(rod((-0.35, 0.25, 0.9), (-0.35, 0.25, 1.35), 0.012, C["steel"], verts=5))
    p.append(sphere(0.04, (-0.35, 0.25, 1.37), C["red_light"], segs=8, rings=6))
    for a in (0.8, 2.3, 4.0):  # sandbags around
        p.append(sphere(0.14, (0.9 * math.cos(a), 0.9 * math.sin(a), 0.12), mat("sandbag", (0.62, 0.55, 0.38), 0.9), scale=(1.4, 0.9, 0.6)))
    simple(p, "hut")


def flag_pole():
    TM, TT = team()
    C = common()
    gold = mat("gold", (0.9, 0.7, 0.25), 0.3, 1.0)
    p = [cyl(0.42, 0.08, (0, 0, 0.04), C["concrete_dark"], verts=8, bevel=0.02),
         cyl(0.3, 0.08, (0, 0, 0.12), C["gun"], verts=8, bevel=0.02),
         cyl(0.32, 0.03, (0, 0, 0.17), TT, verts=8),
         cyl(0.08, 0.2, (0, 0, 0.26), C["steel"], verts=10),
         cyl(0.035, 2.1, (0, 0, 1.2), C["steel"], verts=10),
         sphere(0.07, (0, 0, 2.28), gold, segs=10, rings=6)]
    for a in (0, 2 * math.pi / 3, 4 * math.pi / 3):
        p.append(cyl(0.03, 0.02, (0.23 * math.cos(a), 0.23 * math.sin(a), 0.165), C["lamp"], verts=6))
    root = join(flatten(p), "flag_pole")
    # the cloth: a vertical 0.9 x 0.55 plane, 12 x 8 quads, its origin on the pole edge; UV.x = 0 at the pole, 1 at the tip
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=13, y_subdivisions=9, size=1, calc_uvs=True)
    cl = active()
    cl.data.transform(Matrix.Translation((0.5, 0, 0)))
    cl.data.transform(Matrix.Diagonal((0.9, 0.55, 1, 1)))
    cl.data.transform(Matrix.Rotation(R90, 4, "X"))
    cl.location = (0.035, 0, 1.95)
    cl.name = "cloth"
    cl.data.name = "cloth"
    finish(cl, mat("team_cloth", (0.8, 0.8, 0.8), 0.85, double=True), smooth=180)
    export(root, "flag_pole", [(cl, root)])


# ------------------------------------------------------------------ terrain

def rock(i):
    rnd = random.Random(100 + i)
    body = mat("rock", (0.4, 0.35, 0.3), 0.9)
    top = mat("rock_top", (0.62, 0.5, 0.3), 0.95)
    band = mat("rock_band", (0.29, 0.25, 0.22), 0.9)
    cut = rnd.uniform(0.3, 0.55)
    H = 1.1 * rnd.uniform(0.9, 1.08)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    for v in sorted(bm.verts, key=lambda v: (round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3))):
        x, y, z = v.co
        zt = z + 0.5
        # sides pushed in by a random facet depth (never out, so a row of blocks joins into one cliff face), the
        # upper third rounded inwards, the top a lumpy crown
        taper = 1.0 - 0.28 * max(0.0, zt - 0.55) ** 1.5 / 0.45 ** 1.5
        dx = rnd.uniform(0.0, 0.09) if abs(x) > 0.49 else rnd.uniform(-0.04, 0.04)
        dy = rnd.uniform(0.0, 0.09) if abs(y) > 0.49 else rnd.uniform(-0.04, 0.04)
        nx = (x - math.copysign(dx, x) if abs(x) > 0.49 else x + dx) * taper
        ny = (y - math.copysign(dy, y) if abs(y) > 0.49 else y + dy) * taper
        if zt > 0.99:
            nz = H + rnd.uniform(-0.18, 0.1) - 0.25 * (abs(x) + abs(y) > 0.8)
        elif zt > 0.01:
            nz = zt * H + rnd.uniform(-0.07, 0.07)
        else:
            nz = 0.0
        v.co = (nx, ny, max(0.0, nz))
    me = bpy.data.meshes.new("rock")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("rock", me)
    bpy.context.collection.objects.link(o)
    finish(o, body, smooth=0)
    o.data.materials.append(top)
    o.data.materials.append(band)
    for poly in o.data.polygons:
        if poly.normal.z > 0.55:
            poly.material_index = 1
        elif poly.center.z < cut * H:
            poly.material_index = 2  # a darker stratum at the foot, so a row of blocks reads as one cliff
    parts = [o]
    for k in range(rnd.randint(1, 3)):  # a few boulders leaning on the block
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.2, 0.32)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r,
                                              location=(0.25 * math.cos(a), 0.25 * math.sin(a), H - rnd.uniform(0.0, 0.12)))
        b = active()
        b.scale = (rnd.uniform(0.9, 1.3), rnd.uniform(0.9, 1.3), rnd.uniform(0.7, 1.0))
        b.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        finish(b, top, smooth=0)
        parts.append(b)
    simple(parts, "rock_%d" % i)


def crate_grenades():
    C = common()
    wood = mat("crate_olive", (0.34, 0.38, 0.22), 0.8)
    green = mat("grenade_green", (0.25, 0.4, 0.18), 0.5, coat=0.3)
    p = [box((0.6, 0.5, 0.32), (0, 0, 0.16), wood, bevel=0.03),
         box((0.62, 0.52, 0.05), (0, 0, 0.31), C["gun"], bevel=0.015),
         box((0.5, 0.4, 0.02), (0, 0, 0.33), C["dark"], bevel=0.0)]
    for s in (-1, 1):
        p.append(box((0.04, 0.52, 0.06), (s * 0.24, 0, 0.16), C["gun"], bevel=0.01))
        p.append(box((0.3, 0.02, 0.08), (0, s * 0.255, 0.16), C["hazard"], bevel=0.005))
    for i in range(3):
        for j in range(2):
            x, y = -0.16 + i * 0.16, -0.08 + j * 0.16
            p.append(sphere(0.07, (x, y, 0.4), green, scale=(1, 1, 1.15), segs=10, rings=6))
            p.append(cyl(0.025, 0.04, (x, y, 0.49), C["steel"], verts=6))
            p.append(rod((x + 0.02, y, 0.5), (x + 0.06, y, 0.43), 0.008, C["steel"], verts=4))
    simple(p, "crate_grenades")


def crate_rockets():
    C = common()
    wood = mat("crate_olive", (0.34, 0.38, 0.22), 0.8)
    red = mat("missile_red", (0.85, 0.16, 0.1), 0.4, coat=0.3)
    white = mat("missile_white", (0.9, 0.9, 0.86), 0.45)
    p = [box((0.7, 0.44, 0.26), (0, 0, 0.13), wood, bevel=0.03),
         box((0.72, 0.46, 0.04), (0, 0, 0.24), C["gun"], bevel=0.012)]
    for s in (-1, 1):
        p.append(box((0.04, 0.46, 0.28), (s * 0.3, 0, 0.14), C["gun"], bevel=0.01))
        p.append(box((0.3, 0.02, 0.08), (0, s * 0.225, 0.13), C["hazard"], bevel=0.005))
    for k in range(3):
        y = -0.13 + k * 0.13
        p.append(cyl(0.045, 0.62, (0.02, y, 0.31), white, rot=(0, R90, 0), verts=10))
        p.append(cyl(0.045, 0.14, (-0.36, y, 0.31), red, rot=(0, -R90, 0), r2=0.0, verts=10))
        for a in (0, R90):
            p.append(box((0.08, 0.12, 0.012), (0.3, y, 0.31), red, rot=(a, 0, 0), bevel=0.0))
    simple(p, "crate_rockets")


def bridge():
    C = common()
    deck = mat("bridge_deck", (0.42, 0.33, 0.24), 0.8)
    steel = mat("bridge_steel", (0.35, 0.38, 0.42), 0.45, 0.7)
    p = [box((4.0, 1.0, 0.1), (0, 0, 0.25), steel, bevel=0.0)]
    for k in range(4):  # planks across the whole width
        p.append(box((3.7, 0.23, 0.04), (0, -0.375 + k * 0.25, 0.32), deck, bevel=0.01, segs=1))
    for x in (-0.9, 0.9):  # tyre tracks of steel plate
        p.append(box((0.5, 1.0, 0.02), (x, 0, 0.345), steel, bevel=0.0))
    for s in (-1, 1):
        p.append(box((0.3, 1.0, 0.36), (s * 1.9, 0, 0.18), steel, bevel=0.0))   # girders
        p.append(box((0.08, 1.0, 0.05), (s * 1.93, 0, 0.8), C["hazard"], bevel=0.01))  # top rail
        p.append(box((0.05, 1.0, 0.04), (s * 1.93, 0, 0.58), steel, bevel=0.0))
        p.append(box((0.1, 0.1, 0.46), (s * 1.93, 0, 0.58), steel, bevel=0.01))  # post
        p.append(box((0.05, 0.9, 0.04), (s * 1.9, 0, 0.1), steel, rot=(math.radians(20), 0, 0), bevel=0.0))
    p.append(box((3.6, 0.2, 0.2), (0, 0, 0.1), steel, bevel=0.0))  # cross beam
    simple(p, "bridge")


def crater():
    scorch = mat("crater_scorch", (0.07, 0.06, 0.055), 1.0)
    rim = mat("crater_rim", (0.33, 0.27, 0.2), 0.95)
    rnd = random.Random(5)
    n = 20
    prof = [(0.0, 0.004), (0.18, 0.006), (0.34, 0.02), (0.46, 0.07), (0.56, 0.05), (0.66, 0.004)]
    jit = [rnd.uniform(0.9, 1.12) for _ in range(n)]
    bm = bmesh.new()
    rings = []
    for k, (r, z) in enumerate(prof):
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        rings.append([bm.verts.new((r * jit[i] * math.cos(2 * math.pi * i / n), r * jit[i] * math.sin(2 * math.pi * i / n),
                                     z * (jit[(i + k) % n] if k in (3, 4) else 1))) for i in range(n)])
    for i in range(n):
        f = bm.faces.new((rings[0][0], rings[1][i], rings[1][(i + 1) % n]))
        f.material_index = 0
    for k in range(1, len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((rings[k][i], rings[k + 1][i], rings[k + 1][j], rings[k][j]))
            f.material_index = 0 if k < 2 else 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("crater")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("crater", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(scorch)
    o.data.materials.append(rim)
    deselect()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    parts = [o]
    for k in range(6):  # debris chunks on the rim
        a = rnd.uniform(0, 2 * math.pi)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.03, 0.06),
                                              location=(0.55 * math.cos(a), 0.55 * math.sin(a), 0.04))
        finish(active(), rim, smooth=0)
        parts.append(active())
    simple(parts, "crater")


# ------------------------------------------------------------------ decoration

def palm():
    bark = mat("palm_bark", (0.45, 0.33, 0.2), 0.85)
    leaf = mat("palm_leaf", (0.22, 0.52, 0.16), 0.6, double=True)
    nut = mat("coconut", (0.3, 0.2, 0.1), 0.6)
    p = []
    pts = [Vector((0.25 * (t ** 2), 0, 1.7 * t)) for t in [k / 7 for k in range(8)]]
    for k in range(7):
        p.append(rod(tuple(pts[k]), tuple(pts[k + 1] + Vector((0, 0, 0.03))), 0.09 - 0.006 * k, bark, r2=0.08 - 0.006 * k, verts=8))
    top = pts[-1]
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        d = Vector((math.cos(a), math.sin(a), 0))
        m1 = top + d * 0.35 + Vector((0, 0, 0.12))
        m2 = top + d * 0.75 + Vector((0, 0, -0.18))
        for a0, a1, w0, w1 in ((top, m1, 0.1, 0.16), (m1, m2, 0.16, 0.04)):
            seg = a1 - a0
            bpy.ops.mesh.primitive_plane_add(size=1, location=tuple((a0 + a1) / 2))
            o = active()
            o.data.transform(Matrix.Diagonal((seg.length, 1, 1, 1)))
            for v in o.data.vertices:
                v.co.y *= (w0 if v.co.x < 0 else w1)
                v.co.z += -0.04 * abs(v.co.y) / 0.08
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(seg.normalized())
            bpy.ops.object.transform_apply(rotation=True)
            p.append(finish(o, leaf, smooth=60))
    for k in range(3):
        a = k * 2.1
        p.append(sphere(0.06, tuple(top + Vector((0.08 * math.cos(a), 0.08 * math.sin(a), -0.06))), nut, segs=8, rings=6))
    simple(p, "palm")


def pine():
    bark = mat("pine_bark", (0.35, 0.24, 0.15), 0.85)
    needles = mat("pine_needles", (0.14, 0.33, 0.2), 0.8)
    p = [cyl(0.07, 0.5, (0, 0, 0.25), bark, verts=8)]
    for k, (r, z, h) in enumerate(((0.55, 0.35, 0.6), (0.44, 0.72, 0.55), (0.32, 1.05, 0.5), (0.2, 1.33, 0.4))):
        p.append(cyl(r, h, (0, 0, z + h / 2), needles, r2=0.02, verts=9, bevel=0.02))
    simple(p, "pine")


def dead_tree():
    bark = mat("dead_bark", (0.36, 0.31, 0.27), 0.9)
    p = [rod((0, 0, 0), (0.05, 0, 0.8), 0.1, bark, r2=0.07, verts=8),
         rod((0.05, 0, 0.78), (-0.05, 0.03, 1.35), 0.07, bark, r2=0.03, verts=7)]
    for a, b, r in (((0.04, 0, 0.55), (0.45, 0.1, 0.95), 0.045), ((0.45, 0.1, 0.95), (0.55, 0.05, 1.15), 0.025),
                    ((0.03, 0, 0.8), (-0.4, -0.15, 1.1), 0.04), ((-0.4, -0.15, 1.1), (-0.45, -0.3, 1.25), 0.02),
                    ((0, 0.02, 1.05), (0.2, 0.3, 1.3), 0.025), ((0.0, 0, 0.1), (0.3, -0.1, -0.02), 0.05),
                    ((0.0, 0, 0.1), (-0.25, 0.2, -0.02), 0.05)):
        p.append(rod(a, b, r, bark, r2=r * 0.5, verts=6))
    simple(p, "dead_tree")


def cactus():
    green = mat("cactus_green", (0.25, 0.48, 0.24), 0.6)
    flower = mat("cactus_flower", (1.0, 0.4, 0.6), 0.5)
    p = [cyl(0.14, 1.0, (0, 0, 0.5), green, verts=10, bevel=0.0), sphere(0.14, (0, 0, 1.0), green, segs=10, rings=6)]
    for s, z0, h in ((1, 0.4, 0.4), (-1, 0.55, 0.3)):
        p.append(rod((0, 0, z0), (s * 0.3, 0, z0), 0.08, green, verts=8))
        p.append(sphere(0.08, (s * 0.3, 0, z0), green, segs=8, rings=6))
        p.append(cyl(0.08, h, (s * 0.3, 0, z0 + h / 2), green, verts=8))
        p.append(sphere(0.08, (s * 0.3, 0, z0 + h), green, segs=8, rings=6))
    p.append(sphere(0.05, (0.03, -0.02, 1.13), flower, segs=8, rings=6))
    p.append(sphere(0.04, (0.3, 0, 0.88), flower, segs=8, rings=6))
    simple(p, "cactus")


def crystal():
    glow = mat("crystal_glow", (0.45, 0.15, 1.0), 0.15, 0.1, emit=1.2)
    base = mat("rock", (0.4, 0.35, 0.3), 0.9)
    rnd = random.Random(3)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.32, location=(0, 0, 0.08))
    o = active()
    o.scale = (1.2, 1.0, 0.5)
    bpy.ops.object.transform_apply(scale=True)
    p = [finish(o, base, smooth=0)]
    for k in range(6):
        a = k * 1.1
        tilt = rnd.uniform(0.1, 0.5) if k else 0.0
        h = rnd.uniform(0.4, 0.7) if k else 1.0
        r = rnd.uniform(0.08, 0.12) if k else 0.15
        base_p = Vector((0.15 * math.cos(a), 0.15 * math.sin(a), 0.1)) if k else Vector((0, 0, 0.1))
        d = Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt)))
        body = rod(tuple(base_p), tuple(base_p + d * h * 0.75), r, glow, verts=6)
        tip = rod(tuple(base_p + d * h * 0.75), tuple(base_p + d * h), r, glow, r2=0.0, verts=6)
        finish(body, glow, smooth=0)
        finish(tip, glow, smooth=0)
        p += [body, tip]
    simple(p, "crystal")


def bush():
    leaf = mat("bush_leaf", (0.2, 0.42, 0.15), 0.75)
    leaf2 = mat("bush_leaf_light", (0.32, 0.55, 0.2), 0.75)
    rnd = random.Random(4)
    p = []
    for k in range(6):
        a = k * 1.05
        r = rnd.uniform(0.16, 0.24)
        d = 0.18 if k else 0.0
        p.append(sphere(r, (d * math.cos(a), d * math.sin(a), r * 0.85 + (0.1 if k == 0 else 0)), leaf if k % 2 else leaf2, segs=10, rings=6))
    simple(p, "bush")


def ruin_pillar():
    stone = mat("ruin_stone", (0.66, 0.62, 0.54), 0.85)
    moss = mat("ruin_moss", (0.3, 0.42, 0.2), 0.9)
    p = [box((0.55, 0.55, 0.16), (0, 0, 0.08), stone, bevel=0.03),
         box((0.46, 0.46, 0.1), (0, 0, 0.2), stone, bevel=0.02),
         cyl(0.18, 1.1, (0, 0, 0.8), stone, verts=12, bevel=0.0)]
    for k in range(12):  # fluting
        a = k * math.pi / 6 + math.pi / 12
        p.append(box((0.03, 0.03, 1.0), (0.18 * math.cos(a), 0.18 * math.sin(a), 0.78), stone, rot=(0, 0, a), bevel=0.0))
    p.append(cyl(0.2, 0.16, (0, 0, 1.38), stone, rot=(0.25, 0.1, 0), verts=12, bevel=0.02))  # broken, tilted top drum
    p.append(box((0.3, 0.22, 0.16), (0.36, -0.2, 0.08), stone, rot=(0.2, 0.1, 0.7), bevel=0.03))  # fallen chunk
    p.append(sphere(0.12, (0.1, -0.12, 0.3), moss, scale=(1.4, 1.0, 0.5), segs=8, rings=5))
    p.append(sphere(0.1, (-0.1, 0.15, 1.44), moss, scale=(1.3, 1.1, 0.4), segs=8, rings=5))
    simple(p, "ruin_pillar")


def street_lamp():
    C = common()
    p = [cyl(0.14, 0.12, (0, 0, 0.06), C["gun"], verts=8, bevel=0.02),
         cyl(0.04, 1.5, (0, 0, 0.8), C["gun"], verts=8),
         rod((0, 0, 1.5), (0, -0.35, 1.62), 0.03, C["gun"], verts=8),
         box((0.18, 0.3, 0.08), (0, -0.42, 1.6), C["gun"], bevel=0.02),
         box((0.13, 0.24, 0.02), (0, -0.42, 1.555), C["lamp"], bevel=0.0),
         box((0.12, 0.03, 0.3), (0.06, 0, 1.0), mat("sign_blue", (0.15, 0.35, 0.75), 0.5), bevel=0.01)]
    simple(p, "street_lamp")


if __name__ == "__main__":
    OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
    builds = {
        "jeep": jeep,
        "tank_light": lambda: tank("tank_light", 1.6, 1.0, 0.28, turret_light),
        "tank_medium": lambda: tank("tank_medium", 1.9, 1.2, 0.3, turret_medium),
        "tank_heavy": lambda: tank("tank_heavy", 2.35, 1.45, 0.34, turret_heavy, heavy=True),
        "apc": apc, "missile_launcher": missile_launcher,
        "cannon_gatling": lambda: cannon("cannon_gatling", tur_gatling),
        "cannon_gun": lambda: cannon("cannon_gun", tur_gun),
        "cannon_howitzer": lambda: cannon("cannon_howitzer", tur_howitzer),
        "cannon_missile": lambda: cannon("cannon_missile", tur_missile),
        "fort": fort, "robot_factory": robot_factory, "vehicle_factory": vehicle_factory, "radar": radar,
        "repair": repair, "hut": hut, "flag_pole": flag_pole,
        "rock_0": lambda: rock(0), "rock_1": lambda: rock(1), "rock_2": lambda: rock(2), "rock_3": lambda: rock(3),
        "crate_grenades": crate_grenades, "crate_rockets": crate_rockets, "bridge": bridge, "crater": crater,
        "palm": palm, "pine": pine, "dead_tree": dead_tree, "cactus": cactus, "crystal": crystal, "bush": bush,
        "ruin_pillar": ruin_pillar, "street_lamp": street_lamp,
    }
    reset()
    for n, fn in builds.items():
        if not only or n in only:
            fn()
