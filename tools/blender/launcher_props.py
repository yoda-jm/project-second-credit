"""Props that float behind the launcher when a game is selected (each game has its own set).
Run: blender -b --factory-startup -P tools/blender/launcher_props.py -- godot/core/art/props
Deterministic; output licence CC BY-SA 4.0. Provenance: this script.
"""
import bpy, bmesh, math, os, sys

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def join(parts, name, bevel=0.0, smooth=False):
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    if bevel:
        m = obj.modifiers.new("b", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
        bpy.ops.object.modifier_apply(modifier=m.name)
    if smooth:
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()
    bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, name + ".obj"), export_selected_objects=True,
                          export_materials=False, forward_axis="NEGATIVE_Z", up_axis="Y")
    print("exported", name)


def cannonball():
    reset()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=0.35)
    ball = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.08, depth=0.12, location=(0, 0, 0.36))
    join([ball, bpy.context.active_object], "cannonball", smooth=True)


def wall_piece():
    """An L-shaped piece of four stone blocks, like Rampart's wall pieces."""
    reset()
    parts = []
    for (x, z) in [(-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5), (1.5, -0.5)]:
        bpy.ops.mesh.primitive_cube_add(size=0.92, location=(x * 0.5, 0, z * 0.5))
        o = bpy.context.active_object
        o.scale = (0.5, 0.5, 0.5)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(o)
    join(parts, "wall_piece", bevel=0.03)


def cone():
    """A traffic cone: square base, tapered body."""
    reset()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.42))
    base = bpy.context.active_object
    base.scale = (0.5, 0.5, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.22, radius2=0.05, depth=0.8, location=(0, 0, 0.0))
    join([base, bpy.context.active_object], "cone", bevel=0.01)


def gear():
    """A 10-tooth cog with a hole."""
    reset()
    bm = bmesh.new()
    teeth, r_in, r_out, depth = 10, 0.3, 0.42, 0.14
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        r = r_out if i % 4 in (1, 2) else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    hole = [(0.1 * math.cos(2 * math.pi * i / 16), 0.1 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    outer_top = [bm.verts.new((x, depth / 2, z)) for x, z in pts]
    outer_bot = [bm.verts.new((x, -depth / 2, z)) for x, z in pts]
    hole_top = [bm.verts.new((x, depth / 2, z)) for x, z in hole]
    hole_bot = [bm.verts.new((x, -depth / 2, z)) for x, z in hole]
    n, m = len(pts), len(hole)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([outer_top[i], outer_top[j], outer_bot[j], outer_bot[i]])
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new([hole_bot[i], hole_bot[j], hole_top[j], hole_top[i]])
    # caps: bridge outer ring to hole ring
    for ring_o, ring_h in ((outer_top, hole_top), (outer_bot, hole_bot)):
        for i in range(n):
            j = (i + 1) % n
            hi = int(i * m / n) % m
            hj = int(j * m / n) % m
            if hi == hj:
                bm.faces.new([ring_o[i], ring_o[j], ring_h[hi]])
            else:
                bm.faces.new([ring_o[i], ring_o[j], ring_h[hj], ring_h[hi]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("gear")
    bm.to_mesh(me)
    obj = bpy.data.objects.new("gear", me)
    bpy.context.collection.objects.link(obj)
    join([obj], "gear")


for f in (cannonball, wall_piece, cone, gear):
    f()
