"""Blastyard (game 9) props: the bomb (with a separate child "spark" at the fuse tip), arena blocks (pillar, two
breakable crates, border wall, floor tile in two shades), five power-up capsules, the solo-mode exit hatch and the
dressing for three arena themes (garden, factory, ice).
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/blastyard_models.py -- godot/games/blastyard/art/models [name ...]
One grid cell = 1 unit, the front faces -Y, the origin sits at the cell centre on the ground (z = 0 is the top of the
floor tiles). blastyard_bombers.py imports the helpers below (mat, box, cyl, sphere, ...).

Themes: every arena block exists once per theme, as its own file:
  pillar.glb, pillar_garden.glb, pillar_factory.glb, pillar_ice.glb       (indestructible block)
  crate.glb,  crate_garden.glb,  crate_factory.glb,  crate_ice.glb        (two nodes each: crate_0, crate_1)
  wall.glb,   wall_garden.glb,   wall_factory.glb,   wall_ice.glb         (border block)
  floor_tile.glb, floor_tile_garden.glb, ...                              (two nodes each: floor_a, floor_b)
The two nodes of a crate or floor file sit on top of each other at the origin: the game keeps one per cell.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

OUT = "."
MATS = {}
R90 = math.pi / 2


# ------------------------------------------------------------------ helpers

def mat(name, color, rough=0.5, metal=0.0, emit=0.0, coat=0.0, alpha=1.0, emit_color=None):
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
        b.inputs["Coat Roughness"].default_value = 0.08
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    m.use_backface_culling = True
    MATS[name] = m
    return m


def team():
    """Light grey team materials: the game recolours them per player (white, red, blue, yellow, green...)."""
    return (mat("team_main", (0.82, 0.82, 0.82), 0.32, 0.0, coat=0.6),
            mat("team_trim", (0.62, 0.62, 0.62), 0.4, 0.1, coat=0.4))


def active():
    return bpy.context.active_object


def deselect():
    for x in bpy.context.selected_objects:
        x.select_set(False)


def select(o):
    deselect()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.curves, bpy.data.materials):
        for d in list(coll):
            coll.remove(d)
    MATS.clear()


def finish(o, material, bevel=0.0, segs=2, smooth=35):
    select(o)
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = segs
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        b.harden_normals = False
        bpy.ops.object.modifier_apply(modifier=b.name)
    o.data.materials.clear()
    o.data.materials.append(material)
    if smooth:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth))
    else:
        bpy.ops.object.shade_flat()
    return o


def box(size, loc, material, rot=(0, 0, 0), bevel=None, segs=2, smooth=35):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    if bevel is None:
        bevel = min(0.03, min(size) * 0.2)
    return finish(o, material, bevel, segs, smooth)


def cyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=16, bevel=0.0, segs=1, scale=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = active()
    if scale:
        o.scale = scale
        bpy.ops.object.transform_apply(scale=True)
    return finish(o, material, bevel, segs)


def sphere(r, loc, material, scale=(1, 1, 1), segs=12, rings=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc, rotation=rot)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return finish(o, material, smooth=80)


def ico(r, loc, material, scale=(1, 1, 1), sub=1, rot=(0, 0, 0), smooth=80):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc, rotation=rot)
    o = active()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return finish(o, material, smooth=smooth)


def torus(r, thick, loc, material, rot=(0, 0, 0), verts=24, minor=6, scale=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=verts, minor_segments=minor, major_radius=r, minor_radius=thick,
                                     location=loc, rotation=rot)
    o = active()
    if scale:
        o.scale = scale
        bpy.ops.object.transform_apply(scale=True)
    return finish(o, material, smooth=80)


def rod(a, b, r, material, r2=None, verts=10):
    """A cylinder (or cone) from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    r2 = r if r2 is None else r2
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = active()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    return finish(o, material, smooth=60)


def prism(poly, depth, loc, material, rot=(0, 0, 0), bevel=0.01, segs=2, scale=1.0):
    """A 2D outline (x, z pairs, counter-clockwise seen from -Y) extruded `depth` along Y, centred on loc."""
    me = bpy.data.meshes.new("prism")
    bm = bmesh.new()
    front = [bm.verts.new((x * scale, -depth / 2, z * scale)) for x, z in poly]
    back = [bm.verts.new((x * scale, depth / 2, z * scale)) for x, z in poly]
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("prism", me)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = rot
    o.location = loc
    select(o)
    bpy.ops.object.transform_apply(location=False, rotation=True)
    o = finish(o, material, bevel, segs, smooth=30)
    return o


def tube(points, radii, material, verts=10, caps=True, name="tube"):
    """A smooth tube through `points` (world) with per-point radii; rounded caps (hemispheres) when `caps`."""
    pts = [Vector(p) for p in points]
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    prev_n = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            n = t.cross(ref).normalized()
        else:
            n = (prev_n - t * prev_n.dot(t)).normalized()
        prev_n = n
        bnorm = t.cross(n)
        rings.append([bm.verts.new(p + radii[i] * (math.cos(a) * n + math.sin(a) * bnorm))
                      for a in (2 * math.pi * k / verts for k in range(verts))])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(verts):
            bm.faces.new((r0[k], r0[(k + 1) % verts], r1[(k + 1) % verts], r1[k]))
    if caps:
        for end, ring, sgn in ((pts[0], rings[0], -1), (pts[-1], rings[-1], 1)):
            t = ((pts[1] - pts[0]) if sgn < 0 else (pts[-1] - pts[-2])).normalized() * sgn
            r = radii[0] if sgn < 0 else radii[-1]
            prev = ring
            for s in (1, 2):
                a = s * math.pi / 6
                c = end + t * r * math.sin(a)
                cur = [bm.verts.new(c + (v.co - end) * math.cos(a)) for v in ring]
                for k in range(verts):
                    f = (prev[k], prev[(k + 1) % verts], cur[(k + 1) % verts], cur[k])
                    bm.faces.new(f if sgn > 0 else f[::-1])
                prev = cur
            tip = bm.verts.new(end + t * r)
            for k in range(verts):
                f = (prev[k], prev[(k + 1) % verts], tip)
                bm.faces.new(f if sgn > 0 else f[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return finish(o, material, smooth=80)


def join(parts, name, pivot=(0, 0, 0)):
    """Joins parts into one object named `name` whose origin sits at `pivot` (world coordinates)."""
    parts = flatten(parts)
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


def export(roots, name, children=()):
    """Exports the root objects (one or several) and their children ((object, parent) pairs) as name.glb."""
    roots = flatten([roots])
    objs = list(roots)
    for c, parent in children:
        c.parent = parent
        c.matrix_parent_inverse = parent.matrix_world.inverted()
        objs.append(c)
    deselect()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = roots[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True, export_animations=False)
    total = sum(tris(o) for o in objs)
    print("exported %-22s %6d tris  nodes: %s" % (name, total, ", ".join(o.name for o in objs)))
    reset()
    return total


def simple(parts, name):
    return export(join(parts, name), name)


def jitter(seed):
    rnd = random.Random(seed)
    return lambda a, b: rnd.uniform(a, b)


# ------------------------------------------------------------------ bomb

def bomb():
    body = mat("bomb_body", (0.05, 0.06, 0.09), 0.18, 0.1, coat=1.0)
    brass = mat("bomb_cap", (0.85, 0.62, 0.25), 0.28, 0.9)
    fuse = mat("fuse", (0.78, 0.66, 0.46), 0.8)
    shine = mat("bomb_shine", (0.55, 0.62, 0.8), 0.15, emit=0.25, coat=1.0)
    spark_m = mat("spark", (1.0, 0.72, 0.25), 0.3, emit=12.0)
    c = Vector((0, 0, 0.3))
    parts = [sphere(0.3, c, body, segs=24, rings=14)]
    tilt = (-0.35, 0, 0.25)  # the cap leans back-right, toward the upper right of the screen
    top = Vector((0.07, 0.1, 0.57))
    parts.append(cyl(0.085, 0.1, top, brass, rot=tilt, verts=18, bevel=0.012, segs=2))
    parts.append(torus(0.085, 0.014, top + Vector((0.004, 0.017, 0.047)), brass, rot=tilt, verts=18, minor=6))
    # a soft highlight patch: reads as gloss even in flat lighting
    parts.append(sphere(0.07, (-0.12, -0.22, 0.45), shine, scale=(1.0, 0.35, 0.6), segs=10, rings=6, rot=(0.5, 0, -0.5)))
    # the fuse: a rope curling up and out of the cap
    pts = [top + Vector((0.008, 0.03, 0.03)), Vector((0.1, 0.16, 0.66)), Vector((0.16, 0.17, 0.72)),
           Vector((0.22, 0.13, 0.75)), Vector((0.26, 0.08, 0.74))]
    parts.append(tube(pts, [0.02, 0.019, 0.018, 0.017, 0.016], fuse, verts=8))
    root = join(parts, "bomb")
    tip = pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.02
    spark = [ico(0.035, tip, spark_m, sub=1)]
    for k in range(6):
        a = k * math.pi / 3
        d = Vector((math.cos(a), math.sin(a) * 0.4, math.sin(a) * 0.9 + 0.2)).normalized()
        spark.append(rod(tip, tip + d * 0.08, 0.014, spark_m, r2=0.0, verts=5))
    spark = join(spark, "spark", pivot=tip)
    export(root, "bomb", [(spark, root)])


# ------------------------------------------------------------------ themes

THEMES = {
    "": dict(  # the classic toy arena: warm sand floor, slate-blue blocks, orange wooden crates
        floor=((0.72, 0.64, 0.5), (0.64, 0.56, 0.43)), grout=(0.42, 0.36, 0.3)),
    "garden": dict(floor=((0.3, 0.58, 0.2), (0.24, 0.49, 0.16)), grout=(0.28, 0.22, 0.14)),
    "factory": dict(floor=((0.21, 0.22, 0.25), (0.16, 0.17, 0.2)), grout=(0.07, 0.07, 0.08)),
    "ice": dict(floor=((0.72, 0.86, 0.95), (0.62, 0.78, 0.9)), grout=(0.45, 0.6, 0.75)),
}


def suffix(theme):
    return "_" + theme if theme else ""


def floor_tile(theme):
    T = THEMES[theme]
    nodes = []
    for k, col in (("a", T["floor"][0]), ("b", T["floor"][1])):
        rough, metal, coat = {"": (0.7, 0, 0.1), "garden": (0.85, 0, 0), "factory": (0.45, 0.6, 0),
                              "ice": (0.12, 0, 0.8)}[theme]
        m = mat("floor_" + k, col, rough, metal, coat=coat)
        g = mat("floor_grout_" + (theme or "classic"), T["grout"], 0.9)
        parts = [box((0.97, 0.97, 0.1), (0, 0, -0.05), m, bevel=0.025, segs=2),
                 box((1.0, 1.0, 0.06), (0, 0, -0.085), g, bevel=0.0)]
        if theme == "factory":   # tread plate: a few raised studs
            for i in range(3):
                for j in range(3):
                    rot = (0, 0, 0.6 if (i + j) % 2 else -0.6)
                    parts.append(box((0.16, 0.035, 0.012), ((i - 1) * 0.28, (j - 1) * 0.28, 0.004), m, rot=rot,
                                     bevel=0.0))
        elif theme == "garden" and k == "a":  # a few grass blades
            J = jitter(3)
            for i in range(5):
                x, y = J(-0.4, 0.4), J(-0.4, 0.4)
                parts.append(cyl(0.02, 0.05, (x, y, 0.02), m, r2=0.0, verts=4))
        elif theme == "ice":  # a sheen streak
            parts.append(box((0.5, 0.05, 0.004), (0.05, -0.05, 0.001), mat("ice_sheen", (0.9, 0.97, 1.0), 0.05,
                                                                             coat=1.0), rot=(0, 0, 0.7), bevel=0.0))
        nodes.append(join(parts, "floor_" + k))
    export(nodes, "floor_tile" + suffix(theme))


def pillar(theme):
    """Indestructible blocks: each theme's pillar contrasts with its floor (value) and its crates (hue)."""
    parts = []
    if theme == "":
        body = mat("pillar_body", (0.3, 0.4, 0.58), 0.35, 0.0, coat=0.5)
        top = mat("pillar_top", (0.55, 0.66, 0.8), 0.3, coat=0.6)
        bolt = mat("pillar_bolt", (0.85, 0.72, 0.4), 0.25, 0.9)
        glow = mat("pillar_glow", (0.4, 0.85, 1.0), 0.3, emit=2.5)
        parts += [box((0.94, 0.94, 0.78), (0, 0, 0.39), body, bevel=0.07, segs=3),
                  box((0.8, 0.8, 0.12), (0, 0, 0.8), top, bevel=0.05, segs=3),
                  box((0.4, 0.4, 0.06), (0, 0, 0.87), body, bevel=0.025, segs=2)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(cyl(0.035, 0.03, (sx * 0.3, sy * 0.3, 0.87), bolt, verts=10, bevel=0.01))
        for s in (-1, 1):  # a thin light slot on the front and back faces
            parts.append(box((0.5, 0.02, 0.045), (0, s * 0.471, 0.55), glow, bevel=0.01, segs=1))
    elif theme == "garden":   # beige cut stone on a darker plinth: nothing green, it must not melt into the lawn
        stone = mat("garden_stone", (0.78, 0.72, 0.6), 0.75, coat=0.15)
        stone2 = mat("garden_stone_dark", (0.5, 0.47, 0.42), 0.85)
        cap = mat("garden_stone_cap", (0.88, 0.84, 0.74), 0.7, coat=0.2)
        parts += [box((0.95, 0.95, 0.2), (0, 0, 0.1), stone2, bevel=0.05, segs=2),
                  box((0.9, 0.9, 0.58), (0, 0, 0.48), stone, bevel=0.06, segs=2),
                  box((0.95, 0.95, 0.13), (0, 0, 0.83), cap, bevel=0.05, segs=2)]
        for s in (-1, 1):  # a mortar course on the front and back
            parts.append(box((0.9, 0.012, 0.025), (0, s * 0.451, 0.48), stone2, bevel=0.0))
            parts.append(box((0.012, 0.9, 0.025), (s * 0.451, 0, 0.48), stone2, bevel=0.0))
    elif theme == "factory":  # riveted light steel on the dark floor plates
        steel = mat("factory_steel", (0.66, 0.69, 0.74), 0.35, 0.35)
        edge = mat("factory_steel_edge", (0.44, 0.47, 0.52), 0.4, 0.4)
        lamp = mat("factory_status", (0.3, 0.9, 1.0), 0.3, emit=3.0)
        parts += [box((0.94, 0.94, 0.86), (0, 0, 0.43), steel, bevel=0.05, segs=2),
                  box((0.96, 0.96, 0.08), (0, 0, 0.06), edge, bevel=0.025, segs=1),
                  box((0.96, 0.96, 0.08), (0, 0, 0.82), edge, bevel=0.025, segs=1),
                  box((0.6, 0.6, 0.04), (0, 0, 0.87), edge, bevel=0.015, segs=1)]
        for side in range(4):  # rivet rows under the top band
            R = Matrix.Rotation(side * R90, 3, "Z")
            for k in range(4):
                parts.append(sphere(0.022, R @ Vector((-0.3 + k * 0.2, -0.472, 0.72)), edge, segs=6, rings=3))
        parts.append(box((0.2, 0.02, 0.035), (0, -0.476, 0.35), lamp, bevel=0.008, segs=1))
    elif theme == "ice":      # blue-grey stone under a thick snow cap
        stone = mat("ice_stone", (0.36, 0.42, 0.54), 0.6, coat=0.2)
        snow = mat("snow", (0.95, 0.97, 1.0), 0.6)
        frost = mat("frost_glint", (0.7, 0.9, 1.0), 0.1, emit=1.0)
        parts += [box((0.94, 0.94, 0.78), (0, 0, 0.39), stone, bevel=0.07, segs=2),
                  box((0.97, 0.97, 0.12), (0, 0, 0.8), snow, bevel=0.06, segs=2)]
        J = jitter(5)
        for i in range(6):
            a = i * 2 * math.pi / 6 + 0.3
            parts.append(ico(J(0.16, 0.22), (math.cos(a) * 0.24, math.sin(a) * 0.24, 0.86), snow,
                             scale=(1.2, 1.2, 0.4), sub=1))
        for x in (-0.3, 0.05, 0.28):  # snow drips down the front
            parts.append(sphere(0.06, (x, -0.475, 0.73 - abs(x) * 0.2), snow, scale=(1, 0.4, 1.4), segs=8, rings=5))
        parts.append(box((0.3, 0.012, 0.02), (-0.1, -0.471, 0.4), frost, rot=(0, 0.5, 0), bevel=0.0))
    simple(parts, "pillar" + suffix(theme))


def crate_classic(v):
    wood = mat("crate_wood", (0.85, 0.5, 0.22), 0.55, coat=0.35)
    frame = mat("crate_frame", (0.62, 0.32, 0.14), 0.6, coat=0.25)
    metal = mat("crate_metal", (0.4, 0.42, 0.45), 0.35, 0.85)
    paint = mat("crate_paint", (0.95, 0.9, 0.78), 0.6)
    s, h = 0.86, 0.8
    parts = [box((s - 0.08, s - 0.08, h - 0.08), (0, 0, h / 2), wood, bevel=0.02, segs=1)]
    # frame edges
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.1, 0.1, h), (sx * (s / 2 - 0.05), sy * (s / 2 - 0.05), h / 2), frame, bevel=0.025, segs=1))
    for z in (0.05, h - 0.05):
        for ax in range(2):
            for sg in (-1, 1):
                size = (s - 0.12, 0.1, 0.1) if ax == 0 else (0.1, s - 0.12, 0.1)
                loc = (0, sg * (s / 2 - 0.05), z) if ax == 0 else (sg * (s / 2 - 0.05), 0, z)
                parts.append(box(size, loc, frame, bevel=0.025, segs=1))
    faces = [(0, -1), (0, 1), (1, 0), (-1, 0)]
    for fx, fy in faces:
        ang = math.atan2(fx, -fy)
        R = Matrix.Rotation(ang, 3, "Z")
        if v == 0:  # X brace
            for sg in (-1, 1):
                p = R @ Vector((0, -s / 2 + 0.03, h / 2))
                parts.append(box((0.08, 0.04, 0.8), p, frame, rot=(0, sg * 0.78, ang), bevel=0.015, segs=1))
        else:       # horizontal slats and a painted star
            for z in (0.28, 0.52):
                p = R @ Vector((0, -s / 2 + 0.025, z))
                parts.append(box((s - 0.16, 0.03, 0.06), p, frame, rot=(0, 0, ang), bevel=0.012, segs=1))
    if v == 1:
        star = [(math.cos(R90 + k * math.pi / 5) * (0.1 if k % 2 == 0 else 0.045),
                 math.sin(R90 + k * math.pi / 5) * (0.1 if k % 2 == 0 else 0.045)) for k in range(10)]
        parts.append(prism(star, 0.01, (0, 0, h + 0.002), paint, rot=(R90, 0, 0), bevel=0.0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box((0.13, 0.13, 0.13), (sx * (s / 2 - 0.05), sy * (s / 2 - 0.05), h - 0.05), metal,
                                 bevel=0.03, segs=1))
    return parts


def crate_garden(v):
    """Warm wooden boxes, like the classic ones (the player reads crates first: no green on them)."""
    return crate_classic(v)


def hazard_crate(v):
    """Yellow steel crates with black hazard stripes."""
    yel = mat("hazard_crate", (0.98, 0.74, 0.1), 0.35, 0.2, coat=0.5)
    blk = mat("hazard_black", (0.06, 0.06, 0.07), 0.45)
    frame = mat("hazard_frame", (0.2, 0.2, 0.22), 0.4, 0.6)
    s, h = 0.86, 0.78
    parts = [box((s - 0.04, s - 0.04, h - 0.04), (0, 0, h / 2), yel, bevel=0.03, segs=2)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.09, 0.09, h), (sx * (s / 2 - 0.045), sy * (s / 2 - 0.045), h / 2), frame,
                             bevel=0.02, segs=1))
    for side in range(4):
        ang = side * R90
        R = Matrix.Rotation(ang, 3, "Z")
        if v == 0:   # a band of diagonal stripes
            for k in range(4):
                u = -0.24 + k * 0.16
                parts.append(box((0.06, 0.012, 0.3), R @ Vector((u, -s / 2 + 0.014, h / 2)), blk,
                                 rot=(0, 0.7, ang), bevel=0.0))
            parts.append(box((s - 0.1, 0.014, 0.03), R @ Vector((0, -s / 2 + 0.012, h / 2 + 0.17)), frame,
                             rot=(0, 0, ang), bevel=0.0))
            parts.append(box((s - 0.1, 0.014, 0.03), R @ Vector((0, -s / 2 + 0.012, h / 2 - 0.17)), frame,
                             rot=(0, 0, ang), bevel=0.0))
        else:        # a black X
            for sg in (-1, 1):
                parts.append(box((0.07, 0.014, 0.82), R @ Vector((0, -s / 2 + 0.014, h / 2)), blk,
                                 rot=(0, sg * 0.78, ang), bevel=0.0))
    tri = [(0.0, 0.1), (-0.09, -0.06), (0.09, -0.06)]
    parts.append(prism(tri, 0.012, (0, 0, h + 0.004), blk, rot=(R90, 0, 0), bevel=0.0))
    return parts


def crate_factory(v):
    return hazard_crate(v)


def crate_ice(v):
    """Wooden crates with a light dusting of snow on one corner (the wood must stay visible: crates are read first)
    and icicles on the front."""
    parts = crate_classic(v)
    snow = mat("snow", (0.95, 0.97, 1.0), 0.6)
    icicle = mat("icicle", (0.7, 0.9, 1.0), 0.05, emit=0.5, coat=1.0)
    J = jitter(9 + v)
    corner = (-0.22, 0.2) if v == 0 else (0.22, 0.18)
    for i in range(3):
        parts.append(ico(J(0.07, 0.11), (corner[0] + J(-0.1, 0.1), corner[1] + J(-0.08, 0.08), 0.81), snow,
                         scale=(1.3, 1.2, 0.35), sub=1))
    J = jitter(4 + v)
    for i in range(4):
        x = -0.28 + i * 0.18
        parts.append(cyl(0.022, J(0.07, 0.13), (x, -0.44, 0.74), icicle, r2=0.0, rot=(math.pi, 0, 0), verts=6))
    return parts


def crate(theme):
    fn = {"": crate_classic, "garden": crate_garden, "factory": crate_factory, "ice": crate_ice}[theme]
    nodes = [join(fn(v), "crate_%d" % v) for v in (0, 1)]
    export(nodes, "crate" + suffix(theme))


def wall(theme):
    parts = []
    if theme == "":
        body = mat("wall_body", (0.2, 0.24, 0.36), 0.45, coat=0.3)
        top = mat("wall_top", (0.36, 0.42, 0.58), 0.35, coat=0.5)
        glow = mat("wall_glow", (1.0, 0.7, 0.3), 0.3, emit=2.0)
        parts += [box((1.0, 1.0, 0.95), (0, 0, 0.475), body, bevel=0.05, segs=2),
                  box((0.9, 0.9, 0.1), (0, 0, 0.98), top, bevel=0.04, segs=2),
                  box((0.3, 0.3, 0.03), (0, 0, 1.04), glow, bevel=0.012, segs=1)]
    elif theme == "garden":  # dark weathered stone courses under a pale cap
        dark = mat("garden_wall", (0.36, 0.32, 0.28), 0.85, coat=0.1)
        mortar = mat("garden_mortar", (0.22, 0.2, 0.18), 0.9)
        cap = mat("garden_stone_cap", (0.88, 0.84, 0.74), 0.7, coat=0.2)
        for k, z in enumerate((0.16, 0.47, 0.78)):
            parts.append(box((1.0 - 0.02 * (k % 2), 1.0 - 0.02 * (k % 2), 0.29), (0, 0, z), dark, bevel=0.05, segs=2))
        parts += [box((0.96, 0.96, 0.3), (0, 0, 0.47), mortar, bevel=0.0),
                  box((1.02, 1.02, 0.1), (0, 0, 0.97), cap, bevel=0.04, segs=2)]
    elif theme == "factory":  # painted blue-grey steel with a cyan light strip
        paint = mat("factory_wall", (0.28, 0.34, 0.44), 0.4, 0.5, coat=0.3)
        steel = mat("factory_steel", (0.66, 0.69, 0.74), 0.35, 0.35)
        parts += [box((1.0, 1.0, 0.95), (0, 0, 0.475), paint, bevel=0.04, segs=2),
                  box((0.9, 0.9, 0.05), (0, 0, 0.97), steel, bevel=0.02, segs=1),
                  box((1.01, 1.01, 0.04), (0, 0, 0.8), mat("factory_status", (0.3, 0.9, 1.0), 0.3, emit=3.0),
                      bevel=0.012, segs=1)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(sphere(0.03, (sx * 0.38, sy * 0.38, 0.99), steel, segs=8, rings=4))
    elif theme == "ice":      # dark blue stone bricks under snow
        stone = mat("ice_wall", (0.28, 0.34, 0.46), 0.55, coat=0.3)
        snow = mat("snow", (0.95, 0.97, 1.0), 0.6)
        for k, z in enumerate((0.16, 0.48, 0.8)):
            off = 0.0 if k % 2 == 0 else 0.03
            parts.append(box((1.0 - off, 1.0 - off, 0.3), (0, 0, z), stone, bevel=0.05, segs=2))
        parts.append(box((0.98, 0.98, 0.1), (0, 0, 0.97), snow, bevel=0.05, segs=2))
    simple(parts, "wall" + suffix(theme))


# ------------------------------------------------------------------ power-ups

def capsule(color, glow_color, name):
    """The floating pill: its underside sits 0.1 above the ground (the game can bob it); origin on the ground."""
    shell = mat("pu_shell_" + name, color, 0.18, 0.0, coat=1.0)
    rim = mat("pu_glow_" + name, glow_color, 0.3, emit=4.0)
    face = mat("pu_face_" + name, tuple(0.55 + 0.45 * c for c in color), 0.3, coat=0.8)
    z = 0.22
    return [box((0.58, 0.58, 0.24), (0, 0, z), shell, bevel=0.11, segs=4),
            box((0.62, 0.62, 0.035), (0, 0, z - 0.01), rim, bevel=0.016, segs=2),
            box((0.42, 0.42, 0.03), (0, 0, z + 0.115), face, bevel=0.012, segs=2)]


def icon(parts, scale=1.35):
    """Joins an icon and scales it up about its foot on the pill."""
    o = join(parts, "icon", pivot=(0, 0.02, ICON_Z))
    o.scale = (scale, scale, scale)
    return o


ICON_Z = 0.36     # the icons stand on the pill, leaning back toward the camera
ICON_TILT = -0.35


def icon_rot():
    return (ICON_TILT, 0, 0)


def pu_bomb():
    cap = capsule((0.15, 0.38, 0.95), (0.4, 0.75, 1.0), "bomb")
    body = mat("bomb_body", (0.05, 0.06, 0.09), 0.18, 0.1, coat=1.0)
    spark = mat("spark", (1.0, 0.72, 0.25), 0.3, emit=12.0)
    brass = mat("bomb_cap", (0.85, 0.62, 0.25), 0.28, 0.9)
    parts = [sphere(0.13, (0, 0.02, ICON_Z + 0.13), body, segs=16, rings=10),
              cyl(0.045, 0.05, (0.04, 0.04, ICON_Z + 0.26), brass, rot=(0, 0.35, 0), verts=12, bevel=0.008),
              rod((0.05, 0.04, ICON_Z + 0.27), (0.1, 0.04, ICON_Z + 0.33), 0.012, mat("fuse", (0.78, 0.66, 0.46), 0.8), verts=6),
              ico(0.025, (0.11, 0.04, ICON_Z + 0.345), spark, sub=1)]
    simple([cap, icon(parts)], "pu_bomb")


def pu_fire():
    cap = capsule((0.95, 0.3, 0.12), (1.0, 0.6, 0.2), "fire")
    outer = mat("flame_outer", (1.0, 0.35, 0.05), 0.4, emit=3.0)
    inner = mat("flame_inner", (1.0, 0.85, 0.3), 0.3, emit=5.0)
    flame = [(0.0, 0.0), (0.1, 0.02), (0.15, 0.1), (0.13, 0.2), (0.07, 0.27), (0.08, 0.36), (0.02, 0.29),
             (-0.03, 0.4), (-0.07, 0.26), (-0.12, 0.3), (-0.14, 0.17), (-0.15, 0.08), (-0.1, 0.02)]
    small = [(0.0, 0.0), (0.06, 0.02), (0.08, 0.09), (0.04, 0.17), (0.0, 0.22), (-0.04, 0.15), (-0.08, 0.08),
             (-0.06, 0.02)]
    parts = [prism(flame, 0.08, (0, 0.02, ICON_Z), outer, rot=icon_rot(), bevel=0.015),
              prism(small, 0.1, (0, 0.0, ICON_Z + 0.01), inner, rot=icon_rot(), bevel=0.012)]
    simple([cap, icon(parts)], "pu_fire")


def pu_speed():
    cap = capsule((0.15, 0.78, 0.45), (0.5, 1.0, 0.6), "speed")
    skate = mat("skate_boot", (0.96, 0.95, 0.92), 0.35, coat=0.6)
    wheel = mat("skate_wheel", (1.0, 0.85, 0.2), 0.3, emit=1.5)
    dark = mat("skate_sole", (0.12, 0.12, 0.14), 0.5)
    boot = [(-0.14, 0.05), (0.16, 0.05), (0.17, 0.1), (0.1, 0.14), (0.02, 0.15), (0.0, 0.3), (-0.12, 0.3),
            (-0.14, 0.2)]
    parts = [prism(boot, 0.1, (0, 0.02, ICON_Z), skate, rot=icon_rot(), bevel=0.018),
              prism([(-0.15, 0.03), (0.17, 0.03), (0.17, 0.06), (-0.15, 0.06)], 0.11, (0, 0.02, ICON_Z), dark,
                    rot=icon_rot(), bevel=0.008)]
    for x in (-0.09, 0.1):
        c = Matrix.Rotation(ICON_TILT, 3, "X") @ Vector((x, 0, 0.0))
        parts.append(cyl(0.035, 0.1, (c.x, c.y + 0.02, ICON_Z + c.z + 0.01), wheel, rot=(R90, 0, 0), verts=12, bevel=0.008))
    # motion streaks
    for k, z in enumerate((0.12, 0.2)):
        c = Matrix.Rotation(ICON_TILT, 3, "X") @ Vector((0.24 + 0.02 * k, 0, z))
        parts.append(box((0.1 - 0.03 * k, 0.03, 0.025), (c.x, c.y + 0.02, ICON_Z + c.z), wheel, rot=icon_rot(),
                         bevel=0.01, segs=1))
    simple([cap, icon(parts)], "pu_speed")


def pu_kick():
    cap = capsule((0.6, 0.25, 0.9), (0.85, 0.5, 1.0), "kick")
    boot = mat("kick_boot", (0.96, 0.95, 0.92), 0.35, coat=0.6)
    sole = mat("kick_sole", (0.95, 0.35, 0.1), 0.45, coat=0.5)
    burst = mat("kick_burst", (1.0, 0.9, 0.3), 0.3, emit=3.0)
    shape = [(-0.1, 0.06), (0.16, 0.06), (0.19, 0.1), (0.17, 0.15), (0.05, 0.17), (0.03, 0.34), (-0.11, 0.34)]
    parts = [prism(shape, 0.11, (-0.03, 0.02, ICON_Z), boot, rot=icon_rot(), bevel=0.02),
              prism([(-0.11, 0.02), (0.2, 0.02), (0.2, 0.07), (-0.11, 0.07)], 0.12, (-0.03, 0.02, ICON_Z), sole,
                    rot=icon_rot(), bevel=0.01)]
    star = [(math.cos(k * math.pi / 4) * (0.08 if k % 2 == 0 else 0.035),
             math.sin(k * math.pi / 4) * (0.08 if k % 2 == 0 else 0.035)) for k in range(8)]
    c = Matrix.Rotation(ICON_TILT, 3, "X") @ Vector((0.21, 0, 0.12))
    parts.append(prism(star, 0.04, (c.x, c.y + 0.02, ICON_Z + c.z), burst, rot=icon_rot(), bevel=0.006))
    simple([cap, icon(parts)], "pu_kick")


def pu_skull():
    cap = capsule((0.2, 0.12, 0.26), (0.55, 1.0, 0.25), "skull")
    bone = mat("skull_bone", (0.93, 0.9, 0.82), 0.4, coat=0.4)
    eye = mat("skull_eye", (0.5, 1.0, 0.2), 0.3, emit=4.0)
    R = Matrix.Rotation(ICON_TILT, 3, "X")
    c = Vector((0, 0.02, ICON_Z))
    parts = [sphere(0.14, c + R @ Vector((0, 0, 0.2)), bone, scale=(1, 0.9, 0.95), segs=16, rings=10),
              box((0.15, 0.13, 0.08), c + R @ Vector((0, -0.01, 0.07)), bone, rot=icon_rot(), bevel=0.03, segs=2)]
    for sx in (-1, 1):
        parts.append(sphere(0.04, c + R @ Vector((sx * 0.055, -0.128, 0.19)), eye, scale=(1.1, 0.5, 1.2), segs=10, rings=6))
    for k in (-1, 0, 1):
        parts.append(box((0.018, 0.02, 0.05), c + R @ Vector((k * 0.035, -0.075, 0.06)),
                         mat("skull_gap", (0.1, 0.06, 0.12), 0.6), rot=icon_rot(), bevel=0.0))
    simple([cap, icon(parts)], "pu_skull")


# ------------------------------------------------------------------ exit hatch (solo mode)

def exit_door():
    """Frame (root), child "portal" (spins about its centre) and child "lid" (hinged at the back edge: rotate it
    about its local X to open)."""
    frame = mat("exit_frame", (0.35, 0.37, 0.42), 0.35, 0.8)
    trim = mat("exit_trim", (0.95, 0.72, 0.15), 0.35, coat=0.4)
    light = mat("exit_light", (0.3, 1.0, 0.6), 0.3, emit=5.0)
    portal_m = mat("exit_portal", (0.25, 0.9, 1.0), 0.2, emit=4.0)
    swirl_m = mat("exit_swirl", (0.85, 1.0, 1.0), 0.2, emit=7.0)
    lid_m = mat("exit_lid", (0.5, 0.52, 0.58), 0.3, 0.85, coat=0.3)
    parts = []
    for i in range(4):
        R = Matrix.Rotation(i * R90, 3, "Z")
        parts.append(box((0.92, 0.14, 0.1), R @ Vector((0, -0.39, 0.05)), frame, rot=(0, 0, i * R90), bevel=0.03, segs=2))
        parts.append(box((0.5, 0.03, 0.015), R @ Vector((0, -0.4, 0.105)), trim, rot=(0, 0, i * R90), bevel=0.0))
        parts.append(sphere(0.035, R @ Vector((-0.39, -0.39, 0.11)), light, segs=8, rings=4))
    root = join(parts, "exit_door")
    disc = [cyl(0.33, 0.02, (0, 0, 0.03), portal_m, verts=24)]
    for k in range(3):  # three spiral arms
        pts = []
        for j in range(7):
            t = j / 6
            a = k * 2 * math.pi / 3 + t * 2.4
            r = 0.04 + t * 0.26
            pts.append((math.cos(a) * r, math.sin(a) * r, 0.045))
        disc.append(tube(pts, [0.012 + 0.012 * (1 - abs(j / 3 - 1)) for j in range(7)], swirl_m, verts=5, caps=False))
    portal = join(disc, "portal")
    hinge = Vector((0, 0.33, 0.1))
    lid = [box((0.66, 0.66, 0.05), (0, 0, 0.1), lid_m, bevel=0.02, segs=2),
           box((0.5, 0.06, 0.04), (0, 0, 0.14), trim, bevel=0.015, segs=1),
           box((0.06, 0.5, 0.04), (0, 0, 0.14), trim, bevel=0.015, segs=1),
           cyl(0.03, 0.2, hinge + Vector((0, 0, 0)), frame, rot=(0, R90, 0), verts=10, bevel=0.005)]
    lid = join(lid, "lid", pivot=hinge)
    export(root, "exit_door", [(portal, root), (lid, root)])


# ------------------------------------------------------------------ theme dressing

def hedge():
    leaf = mat("hedge_leaf", (0.2, 0.46, 0.17), 0.7, coat=0.2)
    leaf2 = mat("hedge_leaf_light", (0.32, 0.6, 0.22), 0.65, coat=0.2)
    flower = mat("hedge_flower", (1.0, 0.95, 0.95), 0.5, emit=0.4)
    heart = mat("hedge_flower_heart", (1.0, 0.8, 0.2), 0.4, emit=1.0)
    parts = [box((0.94, 0.94, 0.75), (0, 0, 0.375), leaf, bevel=0.14, segs=2)]
    J = jitter(41)
    for i in range(9):
        a = J(0, 6.28)
        r = J(0.1, 0.36)
        parts.append(ico(J(0.1, 0.16), (math.cos(a) * r, math.sin(a) * r, 0.74), leaf2, scale=(1, 1, 0.6), sub=1))
    for i in range(6):
        a = J(0, 6.28)
        x, y = math.cos(a) * 0.47, math.sin(a) * 0.47
        z = J(0.25, 0.6)
        parts.append(ico(0.035, (max(-0.47, min(0.47, x)), max(-0.47, min(0.47, y)), z), flower, sub=1))
        parts.append(ico(0.015, (max(-0.49, min(0.49, x * 1.04)), max(-0.49, min(0.49, y * 1.04)), z), heart, sub=1))
    simple(parts, "hedge")


def flowerpot():
    pot = mat("terracotta", (0.8, 0.42, 0.26), 0.6, coat=0.3)
    soil = mat("soil", (0.25, 0.16, 0.1), 0.95)
    stem = mat("stem", (0.25, 0.55, 0.18), 0.6)
    petals = [mat("petal_red", (0.95, 0.25, 0.3), 0.45, coat=0.4), mat("petal_yellow", (1.0, 0.8, 0.2), 0.45, coat=0.4),
              mat("petal_violet", (0.6, 0.35, 0.95), 0.45, coat=0.4)]
    heart = mat("flower_heart", (1.0, 0.9, 0.5), 0.4, emit=1.2)
    parts = [cyl(0.2, 0.32, (0, 0, 0.16), pot, r2=0.27, verts=16, bevel=0.02, segs=2),
             cyl(0.3, 0.07, (0, 0, 0.34), pot, verts=16, bevel=0.025, segs=2),
             cyl(0.25, 0.02, (0, 0, 0.365), soil, verts=16)]
    heads = [(0.0, 0.0, 0.72), (0.14, -0.08, 0.6), (-0.13, 0.05, 0.64)]
    for k, h in enumerate(heads):
        parts.append(rod((h[0] * 0.3, h[1] * 0.3, 0.36), h, 0.015, stem, verts=6))
        for p in range(5):
            a = p * 2 * math.pi / 5
            parts.append(sphere(0.05, (h[0] + math.cos(a) * 0.055, h[1] + math.sin(a) * 0.055, h[2]), petals[k],
                                scale=(1, 1, 0.35), segs=6, rings=3))
        parts.append(sphere(0.03, (h[0], h[1], h[2] + 0.01), heart, segs=8, rings=4))
    for a in (0.5, 2.6, 4.4):
        parts.append(sphere(0.07, (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.42), stem, scale=(1.4, 0.6, 0.25),
                            segs=8, rings=4, rot=(0, 0.4, a)))
    simple(parts, "flowerpot")


def pipe():
    """A pipe run along X across the whole cell (tiles with its neighbours), on a stand; a red valve wheel."""
    steel = mat("pipe_steel", (0.55, 0.6, 0.62), 0.3, 0.9)
    paint = mat("pipe_paint", (0.2, 0.5, 0.35), 0.4, 0.3, coat=0.5)
    dark = mat("factory_dark", (0.14, 0.15, 0.17), 0.5, 0.6)
    valve = mat("valve_red", (0.85, 0.15, 0.1), 0.35, coat=0.5)
    lamp = mat("pipe_gauge", (0.4, 1.0, 0.5), 0.3, emit=3.0)
    z = 0.42
    parts = [cyl(0.17, 1.0, (0, 0, z), paint, rot=(0, R90, 0), verts=16)]
    for x in (-0.46, 0.46):
        parts.append(cyl(0.22, 0.07, (x, 0, z), steel, rot=(0, R90, 0), verts=16, bevel=0.015, segs=1))
    parts += [box((0.16, 0.5, 0.06), (0, 0, 0.03), dark, bevel=0.02),
              box((0.08, 0.08, z - 0.1), (0, 0, (z - 0.1) / 2 + 0.03), dark, bevel=0.02),
              torus(0.2, 0.03, (0, 0, z), steel, rot=(0, R90, 0), verts=16, minor=6),
              cyl(0.035, 0.14, (0.18, 0, z + 0.2), steel, verts=8),
              torus(0.1, 0.018, (0.18, 0, z + 0.27), valve, verts=16, minor=6),
              box((0.2, 0.025, 0.025), (0.18, 0, z + 0.27), valve, bevel=0.0),
              box((0.025, 0.2, 0.025), (0.18, 0, z + 0.27), valve, bevel=0.0),
              cyl(0.06, 0.04, (-0.2, -0.17, z + 0.05), steel, rot=(R90, 0, 0), verts=12, bevel=0.01),
              cyl(0.045, 0.01, (-0.2, -0.195, z + 0.05), lamp, rot=(R90, 0, 0), verts=12)]
    simple(parts, "pipe")


def barrel():
    paint = mat("barrel_paint", (0.15, 0.35, 0.75), 0.35, 0.4, coat=0.5)
    steel = mat("barrel_rim", (0.55, 0.58, 0.62), 0.3, 0.9)
    haz = mat("hazard_yellow", (0.98, 0.72, 0.08), 0.4, coat=0.4)
    goo = mat("toxic_goo", (0.45, 1.0, 0.2), 0.2, emit=3.0)
    parts = [cyl(0.27, 0.7, (0, 0, 0.35), paint, verts=18, bevel=0.03, segs=2)]
    for z in (0.02, 0.25, 0.47, 0.69):
        parts.append(torus(0.275, 0.018, (0, 0, z), steel, verts=18, minor=5))
    parts.append(cyl(0.278, 0.1, (0, 0, 0.36), haz, verts=18))
    parts += [cyl(0.045, 0.03, (0.13, 0.05, 0.71), steel, verts=10, bevel=0.008),
              sphere(0.09, (-0.07, -0.08, 0.705), goo, scale=(1.3, 1.0, 0.2), segs=12, rings=5),
              sphere(0.04, (-0.2, -0.18, 0.62), goo, scale=(0.6, 0.6, 1.4), segs=8, rings=5)]
    simple(parts, "barrel")


def snowdrift():
    snow = mat("snow", (0.95, 0.97, 1.0), 0.6)
    blue = mat("snow_shadow", (0.78, 0.86, 0.97), 0.65)
    sparkle = mat("snow_sparkle", (0.8, 0.95, 1.0), 0.1, emit=3.0)
    J = jitter(51)
    parts = [ico(0.42, (0, 0, 0.0), snow, scale=(1.1, 0.95, 0.55), sub=2),
             ico(0.25, (0.25, 0.15, 0.1), snow, scale=(1.0, 1.0, 0.8), sub=2),
             ico(0.2, (-0.28, -0.12, 0.05), blue, scale=(1.1, 1.0, 0.6), sub=1)]
    for i in range(3):
        parts.append(ico(J(0.06, 0.09), (J(-0.3, 0.3), -0.4 + J(0, 0.1), 0.05), snow, sub=1))
    for i in range(5):
        a = J(0, 6.28)
        parts.append(ico(0.012, (math.cos(a) * 0.25, math.sin(a) * 0.2, J(0.2, 0.3)), sparkle, sub=1, smooth=0))
    simple(parts, "snowdrift")


def ice_crystal():
    crystal = mat("crystal", (0.45, 0.8, 1.0), 0.05, coat=1.0, emit=1.2, emit_color=(0.3, 0.7, 1.0))
    bright = mat("crystal_bright", (0.8, 0.95, 1.0), 0.05, emit=3.0)
    snow = mat("snow", (0.95, 0.97, 1.0), 0.6)
    parts = [ico(0.3, (0, 0, 0), snow, scale=(1.2, 1.1, 0.35), sub=2)]
    spec = [((0, 0), 0.0, 0.0, 0.62, 0.09, crystal), ((0.14, 0.05), 0.45, 0.5, 0.4, 0.07, crystal),
            ((-0.12, 0.08), -0.5, 2.0, 0.45, 0.07, crystal), ((0.02, -0.14), 0.4, 4.0, 0.3, 0.06, bright),
            ((-0.18, -0.1), 0.6, 3.5, 0.25, 0.05, crystal)]
    for (x, y), tilt, yaw, h, r, m in spec:
        base = Vector((x, y, 0.05))
        d = Matrix.Rotation(yaw, 3, "Z") @ Matrix.Rotation(tilt, 3, "X") @ Vector((0, 0, 1))
        top = base + d * h
        parts.append(rod(base, top, r, m, verts=6))
        parts.append(rod(top, top + d * r * 1.8, r, m, r2=0.0, verts=6))
    simple(parts, "ice_crystal")


# ------------------------------------------------------------------ main

def build_all(only):
    jobs = {"bomb": bomb, "exit_door": exit_door, "pu_bomb": pu_bomb, "pu_fire": pu_fire, "pu_speed": pu_speed,
            "pu_kick": pu_kick, "pu_skull": pu_skull, "hedge": hedge, "flowerpot": flowerpot, "pipe": pipe,
            "barrel": barrel, "snowdrift": snowdrift, "ice_crystal": ice_crystal}
    for th in THEMES:
        jobs["pillar" + suffix(th)] = (lambda t: lambda: pillar(t))(th)
        jobs["crate" + suffix(th)] = (lambda t: lambda: crate(t))(th)
        jobs["wall" + suffix(th)] = (lambda t: lambda: wall(t))(th)
        jobs["floor_tile" + suffix(th)] = (lambda t: lambda: floor_tile(t))(th)
    for k, fn in jobs.items():
        if not only or k in only:
            reset()
            fn()


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    OUT = args[0]
    os.makedirs(OUT, exist_ok=True)
    reset()
    build_all(args[1:])
