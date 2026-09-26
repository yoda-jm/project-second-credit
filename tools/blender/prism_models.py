"""Prism Breaker (game 13) models: crystal bricks, the paddle-ship, the energy ball, power-up capsules, the laser bolt,
the sci-fi frame around the field (with the enemy gate and the warp gate), three drones and the backdrop.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/prism_models.py -- godot/games/prism/art/models [name ...]
Helpers (mat, box, cyl, sphere, tube, join, export, ...) come from blastyard_models.py.

Axes: the playfield stands in the Blender XZ plane and faces the camera at -Y (Godot: X right, Y up, the camera at
+Z). One brick = 1.0 (X) x 0.5 (Z) x 0.4 (Y deep); the field is 13 bricks wide. Every origin sits at the piece's
centre, in depth too (bricks span y -0.2..0.2), unless noted.

Bricks (one node each, named like the file):
  brick        glass slab (material "brick_glass", alpha-blended) around an emissive core ("brick_core") and a
               white glint ("brick_glint", keep it white). The game recolours brick_glass and brick_core per colour.
  brick_hard   the same crystal held in a metal frame ("brick_frame", "brick_glass", "brick_core", "brick_glint").
  brick_steel  indestructible dark riveted steel ("steel").
  brick_gold   indestructible gold bar ("gold").
  brick_crack_1, brick_crack_2   node "crack" (material "crack"): thin fracture lines floating just in front of a
               brick (y -0.23 .. -0.21), to overlay on a damaged hard brick.
Frame (T = 0.8 thick, reaching y -0.55 .. 0.35):
  frame_side   1 unit tall (z -0.5..0.5), T wide, built as the RIGHT wall: its inner (ball) face is at x = -T/2.
               Place its centre at x = field_right + T/2. It is symmetric top/bottom, so the LEFT wall is the same
               piece rotated 180 degrees about the depth axis (Godot: rotation.z = PI) at x = field_left - T/2.
  frame_top    1 unit wide (x -0.5..0.5), T tall; inner face at z = -T/2. Centre at y = field_top + T/2.
  frame_corner T x T, four-fold symmetric: the same piece fits all four corners.
  gate         replaces TWO top pieces (2 wide, T tall, inner face at z = -T/2). Child "door": a shutter whose origin
               is its top edge; open it by scaling door.scale.y (Godot) towards 0 (it rolls up into the frame).
  warp_gate    replaces TWO right-wall pieces (T wide, 2 tall, inner face at x = -T/2). Child "door", origin at its
               top edge, opens the same way.
Paddle: root "paddle" (an empty) with children "end_l", "mid", "end_r". mid spans exactly x -0.5..0.5 and has no end
  caps; end_l ends at its origin going left, end_r starts at its origin going right. For width w: mid.scale.x = w - 1,
  end_l.position.x = -(w - 1) / 2, end_r.position.x = (w - 1) / 2 (the default w = 2: ends at +-0.5).
  Materials "paddle_hull", "paddle_glow" (thrusters and trims), "paddle_accent" (thruster pods), "paddle_dark".
Ball: root "ball" (r = 0.15, "ball_glow") with child "ring" (a tilted halo, "ball_ring") pivoting on the centre.
Capsule: a 0.9 x 0.4 pill along X; "capsule_shell" (chrome ends), "capsule_band" (recolour per power),
  "capsule_rim" (white glow lines). Laser bolt: about 0.55 tall along Z (origin at its centre), "laser_glow" core in a "laser_halo" sheath.
Drones (about 0.6 across), each one node with a looping animation "spin" (2 s at 24 fps, set the loop in the game):
  drone_0 a spinning top-cone, drone_1 a pulsing crystal tetra, drone_2 a wobbling ring with an eye.
Backdrop: 16 x 20 panel (x -8..8, z -10..10), its front face at y = 0 and reliefs up to y = -0.08; "backdrop"
  (dark plates) and "backdrop_lines" (emissive circuit traces).
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90

FPS = 24
T = 0.8          # frame thickness
BW, BH, BD = 1.0, 0.5, 0.4


# ------------------------------------------------------------------ helpers

def edit(o, fn):
    """Runs fn(bm) on the object's mesh."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    fn(bm)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return o


def front_face(bm):
    bm.faces.ensure_lookup_table()
    return max((f for f in bm.faces if f.normal.y < -0.9), key=lambda f: f.calc_area())


def inset_front(o, thickness, depth, material=None, smooth=25):
    """Insets the largest front face: depth > 0 raises a faceted table, < 0 sinks a panel."""
    def fn(bm):
        f = front_face(bm)
        bmesh.ops.inset_region(bm, faces=[f], thickness=thickness, depth=depth, use_even_offset=True)
    edit(o, fn)
    return K.finish(o, material or o.data.materials[0], smooth=smooth)


def drop_faces(o, test):
    def fn(bm):
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if test(f)], context="FACES")
    return edit(o, fn)


def new_obj(name, bm, material, smooth=40):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=smooth)


def superellipse(a, b, n=16, p=3.0):
    """Points (y, z) of a rounded-rectangle outline with half sizes a (depth) and b (height)."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(c) ** (2 / p), c), b * math.copysign(abs(s) ** (2 / p), s)))
    return pts


def loft_x(profile, stations, material, cap_start=False, cap_end=False, name="loft", smooth=50):
    """Sweeps a (y, z) profile along X. stations: (x, scale_y, scale_z, dz). Optional fan caps at the ends."""
    bm = bmesh.new()
    rings = []
    for x, sy, sz, dz in stations:
        rings.append([bm.verts.new((x, y * sy, z * sz + dz)) for y, z in profile])
    n = len(profile)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    for flag, ring, st in ((cap_start, rings[0], stations[0]), (cap_end, rings[-1], stations[-1])):
        if flag:
            bm.faces.new(ring)
    return new_obj(name, bm, material, smooth)


def mirror_x(o):
    o.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    o.data.flip_normals()
    o.data.update()
    return o


def empty(name):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    return e


def export_anim(root, name, children=(), anim=True):
    """Like K.export, with an empty allowed as the root and the NLA tracks exported as animations."""
    objs = [root]
    for c, parent in children:
        c.parent = parent
        c.matrix_parent_inverse = parent.matrix_world.inverted()
        objs.append(c)
    K.deselect()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.context.scene.frame_start = 0
    bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True, export_animations=anim,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_frame_step=1)
    print("exported %-22s %6d tris  nodes: %s%s" % (name, sum(K.tris(o) for o in objs if o.type == "MESH"),
                                                        ", ".join(o.name for o in objs), "  (anim)" if anim else ""))
    reset()


def animate(o, name, keys, linear=True):
    """keys: {frame: {"rot": (x, y, z), "scale": (x, y, z), "loc": (x, y, z)}} -> an NLA track `name`."""
    o.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    o.animation_data.action = act
    o.rotation_mode = "XYZ"
    base_loc = o.location.copy()
    for f in sorted(keys):
        k = keys[f]
        o.rotation_euler = k.get("rot", (0, 0, 0))
        o.scale = k.get("scale", (1, 1, 1))
        o.location = base_loc + Vector(k.get("loc", (0, 0, 0)))
        for path in ("rotation_euler", "scale", "location"):
            o.keyframe_insert(path, frame=f)
    curves = []
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves += list(bag.fcurves)
    except AttributeError:
        curves = list(act.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR" if linear else "BEZIER"
            if not linear:
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()
    tr = o.animation_data.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, int(act.frame_range[0]), act)
    o.animation_data.action = None
    o.rotation_euler = (0, 0, 0)
    o.scale = (1, 1, 1)
    o.location = base_loc


# ------------------------------------------------------------------ bricks

def glass_mats():
    return (mat("brick_glass", (0.1, 0.4, 0.9), 0.04, 0.0, emit=0.25, coat=1.0, alpha=0.5,
                emit_color=(0.15, 0.5, 1.0)),
            mat("brick_core", (0.15, 0.55, 1.0), 0.3, emit=2.5),
            mat("brick_glint", (1.0, 1.0, 1.0), 0.1, emit=6.0))


def crystal(w, h, d, glass, core, glint, segs=2):
    """A faceted glass slab with a glowing core inside and a glint streak on its upper-left facet."""
    g = box((w, d, h), (0, 0, 0), glass, bevel=0.035, segs=segs)
    g = inset_front(g, min(w, h) * 0.22, 0.05, smooth=0)
    c = box((w * 0.7, d * 0.45, h * 0.5), (0, 0.01, 0), core, bevel=0.05, segs=segs)
    c = inset_front(c, 0.05, 0.03, smooth=0)
    fy = -d / 2 - 0.05
    s = box((w * 0.22, 0.01, 0.022), (-w * 0.2, fy - 0.004, h * 0.26), glint, bevel=0.0)
    s2 = box((0.035, 0.01, 0.035), (-w * 0.38, fy + 0.012, h * 0.3), glint, rot=(0, 0.785, 0), bevel=0.0)
    for o in (s, s2):
        drop_faces(o, lambda f: f.normal.y > 0.5)
    return [g, c, s, s2]


def brick():
    glass, core, glint = glass_mats()
    simple(crystal(0.96, 0.46, 0.34, glass, core, glint), "brick")


def brick_hard():
    glass, core, glint = glass_mats()
    frame = mat("brick_frame", (0.62, 0.66, 0.72), 0.28, 0.9, coat=0.4)
    parts = crystal(0.76, 0.3, 0.3, glass, core, glint, segs=1)[:3]   # one glint is enough here
    w, h, d, t = 0.96, 0.46, 0.38, 0.085
    for s in (-1, 1):
        parts.append(box((w, d, t), (0, 0, s * (h - t) / 2), frame, bevel=0.025, segs=1))
        parts.append(box((t, d, h - 2 * t + 0.01), (s * (w - t) / 2, 0, 0), frame, bevel=0.02, segs=1))
    simple(parts, "brick_hard")


def brick_steel():
    steel = mat("steel", (0.2, 0.22, 0.26), 0.38, 0.9, coat=0.25)
    w, h, d = 0.96, 0.46, 0.38
    body = box((w, d, h), (0, 0, 0), steel, bevel=0.03, segs=2)
    body = inset_front(body, 0.075, -0.025, smooth=0)
    parts = [body]
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(cyl(0.026, 0.03, (sx * (w / 2 - 0.042), -d / 2 - 0.005, sz * (h / 2 - 0.042)), steel,
                             r2=0.016, rot=(R90, 0, 0), verts=6))
    # a raised diagonal cross brace inside the sunken panel
    for s in (-1, 1):
        a = math.atan2(h - 0.18, w - 0.18)
        parts.append(box((math.hypot(w - 0.18, h - 0.18) - 0.04, 0.03, 0.045), (0, -d / 2 + 0.03, 0), steel,
                         rot=(0, s * a, 0), bevel=0.012, segs=1))
    simple(parts, "brick_steel")


def brick_gold():
    gold = mat("gold", (1.0, 0.72, 0.22), 0.28, 1.0, coat=0.5, emit=0.25, emit_color=(1.0, 0.6, 0.15))
    w, h, d = 0.96, 0.46, 0.38
    body = box((w, d, h), (0, 0, 0), gold, bevel=0.03, segs=2)
    body = inset_front(body, 0.1, 0.05, smooth=0)
    gem = [(0, 0.1), (0.1, 0), (0, -0.1), (-0.1, 0)]
    emblem = prism(gem, 0.03, (0, -d / 2 - 0.06, 0), gold, bevel=0.012, segs=1)
    simple([body, emblem], "brick_gold")


def crack(level):
    """Fracture lines (thin flat strips) on the front of a brick; level 2 adds more branches."""
    m = mat("crack", (0.95, 0.97, 1.0), 0.2, emit=2.5)
    paths = [[(-0.05, 0.23), (0.02, 0.1), (-0.06, 0.02), (0.05, -0.08), (0.0, -0.23)],
             [(0.02, 0.1), (0.16, 0.13), (0.26, 0.05)],
             [(-0.06, 0.02), (-0.2, -0.04)]]
    if level == 2:
        paths += [[(0.05, -0.08), (0.2, -0.12), (0.33, -0.08), (0.44, -0.17)],
                  [(-0.2, -0.04), (-0.3, 0.08), (-0.42, 0.12)],
                  [(-0.2, -0.04), (-0.3, -0.16), (-0.36, -0.23)],
                  [(0.16, 0.13), (0.22, 0.23)]]
    bm = bmesh.new()
    y = -0.225
    for p in paths:
        for i, ((x0, z0), (x1, z1)) in enumerate(zip(p, p[1:])):
            d = Vector((x1 - x0, z1 - z0)).normalized()
            n = Vector((-d.y, d.x)) * (0.011 if i == 0 else 0.008)
            vs = [bm.verts.new((x0 + n.x, y, z0 + n.y)), bm.verts.new((x0 - n.x, y, z0 - n.y)),
                  bm.verts.new((x1 - n.x * 0.6, y, z1 - n.y * 0.6)), bm.verts.new((x1 + n.x * 0.6, y, z1 + n.y * 0.6))]
            f = bm.faces.new(vs)
            f.normal_update()
            if f.normal.y > 0:
                f.normal_flip()
    me = bpy.data.meshes.new("crack")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("crack", me)
    bpy.context.scene.collection.objects.link(o)
    K.finish(o, m, smooth=0)
    export(o, "brick_crack_%d" % level)


# ------------------------------------------------------------------ paddle, ball, capsule, laser

HULL = superellipse(0.24, 0.155, n=16, p=2.6)


def paddle():
    hull = mat("paddle_hull", (0.62, 0.66, 0.74), 0.25, 0.8, coat=1.0)
    glow = mat("paddle_glow", (0.25, 0.85, 1.0), 0.3, emit=3.0)
    accent = mat("paddle_accent", (0.9, 0.12, 0.2), 0.25, 0.3, coat=1.0)
    dark = mat("paddle_dark", (0.03, 0.04, 0.07), 0.12, 0.2, coat=1.0)
    stripe = [(-0.012, 0.009), (-0.012, -0.009), (0.0, -0.012), (0.0, 0.012)]
    visor = [(-0.08, 0.02), (0.1, 0.02), (0.06, 0.03), (-0.05, 0.03)]
    # mid: exactly x -0.5..0.5, open ends
    mid = [loft_x(HULL, [(-0.5, 1, 1, 0), (0.5, 1, 1, 0)], hull, name="mid_hull"),
           loft_x([(y - 0.246, z * 1.6) for y, z in stripe], [(-0.5, 1, 1, 0), (0.5, 1, 1, 0)], glow, name="stripe"),
           loft_x([(y, z + 0.132) for y, z in visor], [(-0.5, 1, 1, 0), (0.5, 1, 1, 0)], dark, name="visor")]
    mid = join(mid, "mid")
    # end_r: x 0..0.5 from its origin, tapering hull into a thruster pod
    parts = [loft_x(HULL, [(0.0, 1, 1, 0), (0.12, 1, 1, 0), (0.24, 0.92, 0.9, 0), (0.33, 0.7, 0.62, 0)], hull,
                    name="end_hull"),
             loft_x([(y - 0.246, z * 1.6) for y, z in stripe], [(0.0, 1, 1, 0), (0.12, 1, 1, 0), (0.2, 0.98, 0.8, 0)],
                    glow, name="stripe"),
             loft_x([(y, z + 0.132) for y, z in visor], [(0.0, 1, 1, 0), (0.1, 1, 1, 0), (0.18, 0.6, 1.0, -0.012)],
                    dark, name="visor"),
             rod((0.16, 0, 0), (0.42, 0, 0), 0.175, accent, r2=0.165, verts=16),
             torus(0.175, 0.014, (0.22, 0, 0), glow, rot=(0, R90, 0), verts=16, minor=4),
             rod((0.42, 0, 0), (0.48, 0, 0), 0.155, hull, r2=0.12, verts=16),
             cyl(0.1, 0.03, (0.483, 0, 0), glow, rot=(0, R90, 0), verts=14),
             cyl(0.06, 0.04, (0.49, 0, 0), mat("paddle_core", (1.0, 1.0, 1.0), 0.2, emit=10.0, emit_color=(0.7, 0.95, 1.0)),
                 rot=(0, R90, 0), verts=10)]
    # a small fin on the top of the pod
    fin = prism([(-0.08, 0.0), (0.08, 0.0), (0.03, 0.09), (-0.05, 0.09)], 0.03, (0.29, 0.02, 0.155), hull, bevel=0.008,
                segs=1)
    parts.append(fin)
    end_r = join(parts, "end_r")
    # end_l: a mirrored copy
    end_l = end_r.copy()
    end_l.data = end_r.data.copy()
    bpy.context.scene.collection.objects.link(end_l)
    mirror_x(end_l)
    end_l.name = "end_l"
    end_l.data.name = "end_l"
    root = empty("paddle")
    end_l.location = (-0.5, 0, 0)
    end_r.location = (0.5, 0, 0)
    export_anim(root, "paddle", [(end_l, root), (mid, root), (end_r, root)], anim=False)


def ball():
    core = mat("ball_glow", (0.85, 0.97, 1.0), 0.15, emit=9.0)
    ring_m = mat("ball_ring", (0.35, 0.85, 1.0), 0.3, emit=5.0)
    root = join([ico(0.15, (0, 0, 0), core, sub=2)], "ball")
    ring = join([torus(0.22, 0.012, (0, 0, 0), ring_m, rot=(1.1, 0.35, 0), verts=24, minor=4)], "ring")
    export(root, "ball", [(ring, root)])


def capsule():
    shell = mat("capsule_shell", (0.86, 0.88, 0.92), 0.16, 0.9, coat=1.0)
    band = mat("capsule_band", (0.2, 0.8, 1.0), 0.18, 0.0, coat=1.0, emit=1.6)
    rim = mat("capsule_rim", (1.0, 1.0, 1.0), 0.2, emit=5.0)
    r = 0.19
    parts = [tube([(-0.26, 0, 0), (-0.13, 0, 0)], [r, r], shell, verts=16, caps=True),
             tube([(0.13, 0, 0), (0.26, 0, 0)], [r, r], shell, verts=16, caps=True)]
    # the band: slightly fatter, with a double chevron embossed on the front
    parts.append(cyl(r + 0.012, 0.3, (0, 0, 0), band, rot=(0, R90, 0), verts=16))
    for x in (-0.155, 0.155):
        parts.append(torus(r + 0.004, 0.012, (x, 0, 0), rim, rot=(0, R90, 0), verts=16, minor=4))
    for dx in (-0.045, 0.045):
        chev = [(-0.035, 0.08), (0.0, 0.08), (0.05, 0.0), (0.0, -0.08), (-0.035, -0.08), (0.015, 0.0)]
        parts.append(prism(chev, 0.02, (dx, -r - 0.012, 0), rim, bevel=0.0))
    simple(parts, "capsule")


def laser_bolt():
    core = mat("laser_glow", (1.0, 0.95, 0.85), 0.2, emit=10.0, emit_color=(1.0, 0.6, 0.35))
    halo = mat("laser_halo", (1.0, 0.35, 0.2), 0.3, emit=4.0, alpha=0.5)
    simple([tube([(0, 0, -0.18), (0, 0, 0.18)], [0.035, 0.035], core, verts=8),
            tube([(0, 0, -0.2), (0, 0, 0.2)], [0.07, 0.07], halo, verts=8)], "laser_bolt")


# ------------------------------------------------------------------ frame

def frame_mats():
    return dict(metal=mat("frame_metal", (0.13, 0.15, 0.2), 0.32, 0.85, coat=0.3),
                plate=mat("frame_plate", (0.42, 0.47, 0.56), 0.28, 0.75, coat=0.6),
                chrome=mat("frame_chrome", (0.85, 0.88, 0.92), 0.12, 1.0),
                glow=mat("frame_glow", (0.2, 0.75, 1.0), 0.3, emit=5.0),
                accent=mat("frame_accent", (1.0, 0.55, 0.12), 0.3, 0.2, coat=0.5, emit=0.6))


def side_parts(h=1.0, plate=True):
    """The right wall, h tall (z -h/2..h/2), inner face at x = -T/2."""
    M = frame_mats()
    parts = [box((T, 0.8, h), (0, -0.05, 0), M["metal"], bevel=0.02, segs=1)]
    if plate:
        parts.append(box((T - 0.26, 0.1, h - 0.012), (0.05, -0.47, 0), M["plate"], bevel=0.02, segs=1))
        parts.append(cyl(0.035, h, (T / 2 - 0.035, -0.46, 0), M["chrome"], verts=8))
    # the chrome rail along the inner edge, with the light strip behind it facing the field
    parts.append(cyl(0.085, h, (-T / 2 + 0.06, -0.42, 0), M["chrome"], verts=12))
    parts.append(box((0.03, 0.08, h), (-T / 2 - 0.005, -0.25, 0), M["glow"], bevel=0.0))
    parts.append(box((0.03, 0.02, h), (0.05, -0.525, 0), M["glow"], bevel=0.0))
    return parts, M


def side_details(parts, M):
    for z in (-0.4, 0.4):
        for x in (-0.07, 0.17):
            parts.append(cyl(0.022, 0.02, (x, -0.525, z), M["chrome"], rot=(R90, 0, 0), verts=6))


def frame_side():
    parts, M = side_parts()
    side_details(parts, M)
    simple(parts, "frame_side")


def rot_top(parts):
    """Turns right-wall parts into top-wall parts (inner face from -X to -Z)."""
    o = join(parts, "tmp")
    o.data.transform(Matrix.Rotation(-R90, 4, "Y"))
    return o


def frame_top():
    parts, M = side_parts()
    side_details(parts, M)
    o = rot_top(parts)
    o.name = o.data.name = "frame_top"
    export(o, "frame_top")


def frame_corner():
    M = frame_mats()
    parts = [box((T, 0.85, T), (0, -0.075, 0), M["metal"], bevel=0.05, segs=2),
             cyl(0.33, 0.14, (0, -0.52, 0), M["plate"], rot=(R90, 0, 0), verts=8, bevel=0.03, segs=2),
             torus(0.24, 0.022, (0, -0.595, 0), M["glow"], rot=(R90, 0, 0), verts=16, minor=4),
             cyl(0.14, 0.07, (0, -0.6, 0), M["chrome"], rot=(R90, 0, 0), verts=8, bevel=0.02, segs=1),
             cyl(0.05, 0.03, (0, -0.64, 0), M["accent"], rot=(R90, 0, 0), verts=8)]
    for k in range(4):
        a = k * R90 + math.pi / 4
        parts.append(cyl(0.035, 0.03, (math.cos(a) * 0.33, -0.51, math.sin(a) * 0.33), M["chrome"],
                         rot=(R90, 0, 0), verts=6))
    o = join(parts, "frame_corner")
    export(o, "frame_corner")


def shutter(w, h, M, name):
    """A hazard-striped roller door, origin at its top edge (z = 0), hanging down to z = -h."""
    dark = mat("door_dark", (0.06, 0.06, 0.08), 0.4, 0.5)
    parts = [box((w, 0.06, h), (0, 0, -h / 2), M["plate"], bevel=0.01, segs=1)]
    for k in range(int(h / 0.1)):
        parts.append(box((w, 0.02, 0.015), (0, -0.035, -0.05 - k * 0.1), M["metal"], bevel=0.0))
    for k in range(5):
        x = -w / 2 + (k + 0.5) * w / 5
        parts.append(box((0.07, 0.02, 0.18), (x, -0.045, -h + 0.12), M["accent"], rot=(0, 0.6, 0), bevel=0.0))
    parts.append(box((w, 0.03, 0.05), (0, -0.04, -h + 0.025), dark, bevel=0.0))
    return join(parts, name)


def gate():
    """Two top pieces wide: an alcove opening down into the field, closed by a roller door."""
    M = frame_mats()
    inner = mat("gate_inside", (0.02, 0.02, 0.04), 0.5, emit=1.0, emit_color=(0.35, 0.1, 0.6))
    lamp = mat("gate_light", (1.0, 0.25, 0.3), 0.3, emit=6.0)
    ow, oh = 1.2, 0.5          # opening
    z0 = -T / 2                # inner edge (field side)
    parts = [box((2.0, 0.8, T - oh), (0, -0.05, z0 + oh + (T - oh) / 2), M["metal"], bevel=0.02, segs=1),
             box((2.0, 0.2, oh), (0, 0.25, z0 + oh / 2), M["metal"], bevel=0.0),
             box((ow, 0.05, oh), (0, 0.13, z0 + oh / 2), inner, bevel=0.0)]
    for s in (-1, 1):  # jambs
        x = s * (ow / 2 + (1.0 - ow / 2) / 2)
        jw = 1.0 - ow / 2
        parts.append(box((jw, 0.8, oh), (x, -0.05, z0 + oh / 2), M["metal"], bevel=0.02, segs=1))
        parts.append(box((jw - 0.12, 0.1, oh + 0.05), (x, -0.47, z0 + oh / 2 + 0.02), M["plate"], bevel=0.03, segs=2))
        parts.append(sphere(0.05, (s * (ow / 2 + 0.12), -0.53, z0 + oh + 0.1), lamp, segs=10, rings=6))
    # lintel over the opening: chrome rail, light strip, plate with an arrow
    parts.append(box((2.0 - 0.1, 0.1, T - oh - 0.08), (0, -0.47, z0 + oh + (T - oh) / 2), M["plate"], bevel=0.03,
                     segs=2))
    parts.append(cyl(0.085, 2.0, (0, -0.42, z0 + 0.06), M["chrome"], rot=(0, R90, 0), verts=12))
    parts.append(box((2.0, 0.08, 0.03), (0, -0.25, z0 - 0.005), M["glow"], bevel=0.0))
    for s in (-1, 1):
        parts.append(box((0.3, 0.02, 0.04), (s * 0.35, -0.525, z0 + oh + 0.14), M["accent"], bevel=0.006, segs=1))
    arrow = [(-0.09, 0.05), (0.09, 0.05), (0.0, -0.05)]
    parts.append(prism(arrow, 0.02, (0, -0.53, z0 + oh + 0.14), M["glow"], bevel=0.0))
    root = join(parts, "gate")
    door = shutter(ow, oh, M, "door")
    door.location = (0, -0.3, z0 + oh)
    export(root, "gate", [(door, root)])


def warp_gate():
    """Two right-wall pieces tall: a glowing warp tunnel through the wall, closed by a roller door."""
    M = frame_mats()
    portal = mat("warp_glow", (0.9, 0.3, 1.0), 0.3, emit=5.0)
    swirl = mat("warp_swirl", (1.0, 0.85, 1.0), 0.2, emit=8.0)
    lamp = mat("gate_light", (1.0, 0.25, 0.3), 0.3, emit=6.0)
    oh = 1.2
    parts = []
    for s in (-1, 1):  # the wall above and below the tunnel
        hh = (2.0 - oh) / 2
        zc = s * (oh / 2 + hh / 2)
        sp, _ = side_parts(hh, plate=True)
        o = join(sp, "seg_%d" % (s + 1))
        o.location = (0, 0, zc)
        parts.append(o)
        parts.append(sphere(0.05, (0.05, -0.53, s * (oh / 2 + 0.12)), lamp, segs=10, rings=6))
    # tunnel: a glowing back wall with a spiral, lit sides
    parts.append(box((T - 0.1, 0.05, oh), (0.05, 0.3, 0), portal, bevel=0.0))
    for s in (-1, 1):
        parts.append(box((T, 0.8, 0.04), (0, -0.05, s * (oh / 2 - 0.02)), M["glow"], bevel=0.0))
    for k in range(3):
        pts = []
        for j in range(7):
            t = j / 6
            a = k * 2 * math.pi / 3 + t * 2.6
            r = 0.05 + t * 0.3
            pts.append((0.05 + math.cos(a) * r * 0.9, 0.26, math.sin(a) * r * 1.3))
        parts.append(tube(pts, [0.02] * 7, swirl, verts=5, caps=False))
    parts.append(box((0.03, 0.08, 2.0), (-T / 2 - 0.005, -0.25, 0), M["glow"], bevel=0.0))
    root = join(parts, "warp_gate")
    door = shutter(T, oh, M, "door")
    door.location = (0.0, -0.3, oh / 2)
    export(root, "warp_gate", [(door, root)])


# ------------------------------------------------------------------ drones

def drone_0():
    """A spinning top: a faceted double cone with a glowing band and a crown gem."""
    body = mat("drone_0_body", (1.0, 0.45, 0.1), 0.25, 0.3, coat=1.0, emit=0.5)
    glow = mat("drone_0_glow", (1.0, 0.85, 0.3), 0.3, emit=6.0)
    dark = mat("drone_dark", (0.05, 0.05, 0.07), 0.3, 0.6, coat=0.8)
    parts = [cyl(0.26, 0.3, (0, 0, -0.15), body, r2=0.0, rot=(math.pi, 0, 0), verts=8),
             cyl(0.26, 0.14, (0, 0, 0.07), body, r2=0.16, verts=8),
             cyl(0.275, 0.05, (0, 0, 0.0), glow, verts=8),
             cyl(0.16, 0.06, (0, 0, 0.17), dark, r2=0.1, verts=8),
             ico(0.07, (0, 0, 0.25), glow, sub=1, smooth=0)]
    for k in range(4):
        a = k * R90
        parts.append(box((0.14, 0.03, 0.05), (math.cos(a) * 0.31, math.sin(a) * 0.31, 0.02), dark,
                         rot=(0, 0, a), bevel=0.01, segs=1))
    for o in parts[:4]:
        K.select(o)
        bpy.ops.object.shade_flat()
    root = join(parts, "drone_0")
    animate(root, "spin", {0: {"rot": (0.25, 0, 0)}, 24: {"rot": (0.25, 0, math.pi)},
                           48: {"rot": (0.25, 0, 2 * math.pi)}})
    export_anim(root, "drone_0")


def drone_1():
    """A pulsing crystal tetrahedron in a cage of four glowing nodes."""
    body = mat("drone_1_body", (0.1, 0.7, 0.25), 0.08, 0.0, coat=1.0, emit=0.8, emit_color=(0.2, 1.0, 0.4))
    glow = mat("drone_1_glow", (0.8, 1.0, 0.6), 0.3, emit=7.0)
    dark = mat("drone_dark", (0.05, 0.05, 0.07), 0.3, 0.6, coat=0.8)
    s = 0.24
    v = [Vector((1, 1, 1)), Vector((1, -1, -1)), Vector((-1, 1, -1)), Vector((-1, -1, 1))]
    bm = bmesh.new()
    vs = [bm.verts.new(p * s) for p in v]
    for f in ((0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)):
        bm.faces.new([vs[i] for i in f])
    tet = new_obj("tet", bm, body, smooth=0)
    parts = [tet, ico(0.09, (0, 0, 0), glow, sub=1)]
    for p in v:
        parts.append(ico(0.04, p * s * 1.25, glow, sub=1))
        parts.append(rod(p * s * 0.9, p * s * 1.2, 0.015, dark, verts=5))
    root = join(parts, "drone_1")
    keys = {}
    for i in range(9):
        f = i * 6
        a = 2 * math.pi * i / 8
        sc = 1.0 + 0.12 * math.sin(2 * a)
        keys[f] = {"rot": (a * 0.5, a, 0), "scale": (sc, sc, sc)}
    keys[48] = {"rot": (math.pi, 2 * math.pi, 0), "scale": (1, 1, 1)}
    animate(root, "spin", keys)
    export_anim(root, "drone_1")


def drone_2():
    """A wobbling ring with a watching eye at its centre, held on three spokes."""
    ring_m = mat("drone_2_body", (0.6, 0.35, 1.0), 0.2, 0.4, coat=1.0, emit=0.5)
    glow = mat("drone_2_glow", (0.4, 0.9, 1.0), 0.3, emit=6.0)
    eye = mat("drone_2_eye", (1.0, 0.3, 0.45), 0.2, emit=5.0)
    dark = mat("drone_dark", (0.05, 0.05, 0.07), 0.3, 0.6, coat=0.8)
    parts = [torus(0.24, 0.06, (0, 0, 0), ring_m, rot=(R90, 0, 0), verts=20, minor=6),
             torus(0.24, 0.018, (0, -0.055, 0), glow, rot=(R90, 0, 0), verts=20, minor=4),
             sphere(0.1, (0, 0, 0), dark, segs=12, rings=8),
             sphere(0.05, (0, -0.07, 0), eye, scale=(1, 0.5, 1), segs=10, rings=6)]
    for k in range(3):
        a = k * 2 * math.pi / 3 + R90
        parts.append(rod((math.cos(a) * 0.09, 0, math.sin(a) * 0.09), (math.cos(a) * 0.2, 0, math.sin(a) * 0.2),
                         0.018, dark, verts=5))
    root = join(parts, "drone_2")
    keys = {}
    for i in range(9):
        a = 2 * math.pi * i / 8
        keys[i * 6] = {"rot": (0.35 * math.sin(a), a, 0.3 * math.cos(a)), "loc": (0, 0, 0.04 * math.sin(2 * a))}
    animate(root, "spin", keys)
    export_anim(root, "drone_2")


# ------------------------------------------------------------------ backdrop

def backdrop():
    base = mat("backdrop", (0.035, 0.04, 0.075), 0.35, 0.6, coat=0.4)
    lines = mat("backdrop_lines", (0.1, 0.18, 0.55), 0.4, emit=0.25)
    W, H = 16.0, 20.0
    plate = box((W, 0.1, H), (0, 0.05, 0), base, bevel=0.0)
    drop_faces(plate, lambda f: f.normal.y > -0.5)
    parts = [plate]
    J = K.jitter(1313)

    def relief(w, h, x, z, depth=0.05):
        o = box((w, depth, h), (x, -depth / 2, z), base, bevel=min(0.03, depth * 0.5), segs=1)
        drop_faces(o, lambda f: f.normal.y > 0.5)
        parts.append(o)

    # chip-like raised plates, mirrored left/right so the field sits on a balanced board
    chips = [(2.2, 1.6, 5.4, 7.2), (1.4, 2.4, 6.4, 2.6), (2.6, 1.2, 5.0, -3.4), (1.6, 1.6, 6.2, -7.6),
             (3.0, 0.9, 2.2, 8.6), (1.2, 1.2, 1.4, -8.8)]
    for w, h, x, z in chips:
        for s in (-1, 1):
            relief(w, h, s * x, z)
            relief(w - 0.5, h - 0.5, s * x, z, 0.08)
    # traces: 45-degree circuit runs with pads at their ends
    bm = bmesh.new()
    y = -0.012

    def seg(a, b, wd=0.03):
        d = (b - a).normalized()
        n = Vector((-d.y, d.x)) * wd / 2
        vs = [bm.verts.new((p.x, y, p.y)) for p in (a + n, a - n, b - n, b + n)]
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()

    def pad(c, r=0.055):
        vs = [bm.verts.new((c.x + r * math.cos(k * math.pi / 3), y - 0.002, c.y + r * math.sin(k * math.pi / 3)))
              for k in range(6)]
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()

    dirs = [Vector((1, 0)), Vector((1, 1)).normalized(), Vector((0, 1)), Vector((-1, 1)).normalized(),
            Vector((-1, 0)), Vector((-1, -1)).normalized(), Vector((0, -1)), Vector((1, -1)).normalized()]
    def offset(pts, d):
        """The polyline shifted sideways by d (mitred corners)."""
        out = []
        for i, p in enumerate(pts):
            ns = []
            for a, b in ((pts[i - 1], p) if i > 0 else (None, None), (p, pts[i + 1]) if i < len(pts) - 1 else (None, None)):
                if a is not None:
                    t = (b - a).normalized()
                    ns.append(Vector((-t.y, t.x)))
            n = (ns[0] + ns[-1]).normalized()
            out.append(p + n * (d / max(0.5, n.dot(ns[0]))))
        return out

    # bundles of three parallel traces leaving the chips' outer edges, turning at 45 degrees
    for ci, (w, h, x, z) in enumerate(chips):
        for s in (-1, 1):
            for side in range(2):
                J2 = K.jitter(ci * 7 + side)          # the same run on both halves (mirrored)
                if side == 0:
                    p, di = Vector((x - w / 2, z + J2(-0.3, 0.3) * h)), 4          # from the inner edge
                else:
                    p, di = Vector((x + J2(-0.3, 0.3) * w, z + h / 2 * (1 if z < 0 else -1))), (2 if z < 0 else 6)
                pts = [p]
                for k in range(int(J2(2, 4.99))):
                    ln = J2(0.7, 2.0)
                    q = pts[-1] + dirs[di] * ln
                    if abs(q.x) > 7.6 or abs(q.y) > 9.6:
                        break
                    pts.append(q)
                    di = (di + (1 if J2(0, 1) > 0.5 else -1)) % 8
                if len(pts) < 2:
                    continue
                pts = [Vector((q.x * s, q.y)) for q in pts]
                for d in (-0.13, 0.0, 0.13):
                    run = offset(pts, d)
                    for a, b in zip(run, run[1:]):
                        seg(a, b)
                    pad(run[-1])
    me = bpy.data.meshes.new("traces")
    bm.to_mesh(me)
    bm.free()
    tr = bpy.data.objects.new("traces", me)
    bpy.context.scene.collection.objects.link(tr)
    parts.append(K.finish(tr, lines, smooth=0))
    # a row of small lights along the bottom, like a bus
    for k in range(-7, 8):
        parts.append(box((0.3, 0.02, 0.06), (k * 1.0, -0.01, -9.6), lines, bevel=0.0))
    simple(parts, "backdrop")


# ------------------------------------------------------------------ main

JOBS = {"brick": brick, "brick_hard": brick_hard, "brick_steel": brick_steel, "brick_gold": brick_gold,
        "brick_crack_1": lambda: crack(1), "brick_crack_2": lambda: crack(2), "paddle": paddle, "ball": ball,
        "capsule": capsule, "laser_bolt": laser_bolt, "frame_side": frame_side, "frame_top": frame_top,
        "frame_corner": frame_corner, "gate": gate, "warp_gate": warp_gate, "drone_0": drone_0, "drone_1": drone_1,
        "drone_2": drone_2, "backdrop": backdrop}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
