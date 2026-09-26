"""Blastyard (game 9) characters: the bomber (a chibi in a round helmet, about 0.85 units tall) and the four solo-mode
enemies (blob, bat, ghost, stomper beetle). Each has its own armature with smooth skin weights; the actions are keyed
with Bezier curves (cyclic handles on the loops) and exported as one glTF animation per action.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/blastyard_bombers.py -- godot/games/blastyard/art/models [name ...]
One grid cell = 1 unit, the front faces -Y, feet at z = 0. 30 fps.
Bomber: the materials "team_main" (helmet, body) and "team_trim" (legs, ears, belt, cuffs) are light grey: the game
recolours them per player. Animations: idle, walk, win, lose (loops); place, kick, hurt, die (one-shots).
Enemies: move (loop) and die (one-shot).

Rig code (self-contained): parts are tagged with a bone (rigid), a list of bones (smooth: weights fall off with the
distance to each bone's segment) or a weight function. Poses are written in world axes (degrees about X, Y, Z,
applied X then Y then Z, "@bone" = location offset, "%bone" = scale) and converted to each bone's local frame, so a
key reads the same whatever the bone's direction: +X tips an upright bone forward (toward -Y) and swings a hanging
limb backward; about Y, -Y raises a left (+X side) arm outward. `mirror` builds the right side from the left.
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, team, box, cyl, sphere, ico, torus, rod, tube, reset, flatten, R90

FPS = 30


# ------------------------------------------------------------------ rig

def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Rig:
    def __init__(self, bones):
        """bones: {name: (head, tail, parent)} in armature space (= world, the rig sits at the origin)."""
        self.bones = {n: (Vector(h), Vector(t), p) for n, (h, t, p) in bones.items()}
        self.parts = []

    def rigid(self, bone, *objs):
        for o in flatten(objs):
            self.parts.append((o, bone))
        return objs

    def smooth(self, bones, *objs, power=4.0):
        for o in flatten(objs):
            self.parts.append((o, (list(bones), power)))
        return objs

    def custom(self, fn, *objs):
        for o in flatten(objs):
            self.parts.append((o, fn))
        return objs

    def weights(self, p, spec):
        if isinstance(spec, str):
            return {spec: 1.0}
        if callable(spec):
            return spec(p)
        names, power = spec
        return {n: 1.0 / (seg_dist(p, *self.bones[n][:2]) ** 2 + 1e-5) ** (power / 2) for n in names}

    def bind(self):
        for o, spec in self.parts:
            mw = o.matrix_world
            groups = {}
            for v in o.data.vertices:
                w = self.weights(mw @ v.co, spec)
                tot = sum(w.values())
                w = {b: x / tot for b, x in w.items() if x / tot > 0.015}
                tot = sum(w.values())
                for b, x in w.items():
                    if b not in groups:
                        groups[b] = o.vertex_groups.new(name=b)
                    groups[b].add([v.index], x / tot, "REPLACE")

    def build(self, name):
        """Creates the armature, binds and joins the parts into one skinned mesh named `name`."""
        meshes = [o for o, _ in self.parts]
        if os.environ.get("TRIS"):
            print("  parts:", sorted(((K.tris(o), o.data.materials[0].name) for o in meshes), reverse=True)[:14])
        self.bind()
        bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
        arm = K.active()
        arm.name = name + "_rig"
        arm.data.name = name + "_rig"
        eb = arm.data.edit_bones
        eb.remove(eb[0])
        for n, (h, t, p) in self.bones.items():
            b = eb.new(n)
            b.head, b.tail = h, t
            d = (t - h).normalized()
            b.align_roll(Vector((0, 0, 1)) if abs(d.z) < 0.7 else Vector((0, -1, 0)))
            if p:
                b.parent = eb[p]
        bpy.ops.object.mode_set(mode="OBJECT")
        K.deselect()
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
        mesh = K.active()
        mesh.name = name
        mesh.data.name = name
        mod = mesh.modifiers.new("rig", "ARMATURE")
        mod.object = arm
        mesh.parent = arm
        self.arm, self.mesh = arm, mesh
        for b in arm.pose.bones:
            b.rotation_mode = "XYZ"
        arm.animation_data_create()
        self.rest = {b.name: b.matrix_local.to_3x3() for b in arm.data.bones}
        return mesh

    def local_rot(self, bone, deg, prev):
        R = (Matrix.Rotation(math.radians(deg[2]), 3, "Z") @ Matrix.Rotation(math.radians(deg[1]), 3, "Y")
             @ Matrix.Rotation(math.radians(deg[0]), 3, "X"))
        M = self.rest[bone]
        L = M.inverted() @ R @ M
        return L.to_euler("XYZ", prev) if prev is not None else L.to_euler("XYZ")

    def local_scale(self, bone, s):
        if not isinstance(s, (tuple, list)):
            s = (s, s, s)
        M = self.rest[bone]
        L = M.inverted() @ Matrix.Diagonal(Vector(s)) @ M
        return Vector((abs(L[0][0]), abs(L[1][1]), abs(L[2][2])))

    def action(self, name, keys, loop=False):
        """keys: {frame: pose}; pose: {bone: (x, y, z) degrees, "@bone": (x, y, z), "%bone": s or (sx, sy, sz)}.
        Every bone is keyed at every key frame (a bone a pose leaves out returns to rest)."""
        arm = self.arm
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        arm.animation_data.action = act
        pb = arm.pose.bones
        prev = {}
        f0 = min(keys)   # keys start at frame 0, so the glTF clip starts at t = 0 (no hitch when Godot loops it)
        keys = {f - f0: p for f, p in keys.items()}
        frames = sorted(keys)
        for f in frames:
            pose = keys[f]
            for b in pb:
                n = b.name
                e = self.local_rot(n, pose.get(n, (0, 0, 0)), prev.get(n))
                prev[n] = e
                b.rotation_euler = e
                b.location = self.rest[n].inverted() @ Vector(pose.get("@" + n, (0, 0, 0)))
                b.scale = self.local_scale(n, pose.get("%" + n, 1.0))
                for path in ("rotation_euler", "location", "scale"):
                    b.keyframe_insert(path, frame=f)
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, act.slots[0])
        for fc in cb.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
                k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
            if loop:
                fc.modifiers.new("CYCLES")
            fc.update()
        act.use_frame_range = True
        act.frame_start, act.frame_end = frames[0], frames[-1]
        act.use_cyclic = loop
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, frames[0], act)
        arm.animation_data.action = None
        self.lengths = getattr(self, "lengths", {})
        self.lengths[name] = (frames[-1] - frames[0]) / FPS

    def export(self, name):
        K.deselect()
        self.arm.select_set(True)
        self.mesh.select_set(True)
        bpy.context.view_layer.objects.active = self.arm
        bpy.context.scene.frame_start = 0
        bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, name + ".glb"), use_selection=True,
                                  export_format="GLB", export_yup=True, export_apply=False, export_animations=True,
                                  export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                                  export_frame_step=1)
        print("exported %-10s %5d tris  anims: %s" % (name, K.tris(self.mesh), ", ".join(
            "%s %.2fs" % (k, v) for k, v in self.lengths.items())))
        reset()


def mirror(pose):
    """Adds the right-side (.R) counterpart of every left-side (.L) channel."""
    out = dict(pose)
    for k, v in pose.items():
        if ".L" in k:
            r = k.replace(".L", ".R")
            if k[0] == "@":
                out[r] = (-v[0], v[1], v[2])
            elif k[0] == "%":
                out[r] = v
            else:
                out[r] = (v[0], -v[1], -v[2])
    return out


def smooth_path(pts, per=3):
    """Catmull-Rom resampling: `per` samples per segment."""
    P = [Vector(p) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(per):
            t = s / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def smooth_radii(rs, per=3):
    out = []
    for a, b in zip(rs, rs[1:]):
        out += [a + (b - a) * s / per for s in range(per)]
    return out + [rs[-1]]


def limb(points, radii, material, verts=10, per=3, caps=False):
    """A resampled tube; open ends by default (they sit inside the body, a mitten or a boot)."""
    return tube(smooth_path(points, per), smooth_radii(radii, per), material, verts=verts, caps=caps)


# ------------------------------------------------------------------ bomber

LEG = 0.145  # hip (0.2) to ankle (0.055)


def squat(d, legs=("L", "R")):
    """Lowers the hips by d with both feet planted: thighs forward, shins back, feet level."""
    th = math.degrees(math.acos(max(-1.0, min(1.0, 1 - d / LEG))))
    p = {"@hips": (0, 0, -d)}
    for s in legs:
        p["thigh." + s] = (-th, 0, 0)
        p["shin." + s] = (2 * th, 0, 0)
        p["foot." + s] = (-th, 0, 0)
    return p


def merge(*poses):
    out = {}
    for p in poses:
        for k, v in p.items():
            if k in out and k[0] not in "@%":
                out[k] = tuple(a + b for a, b in zip(out[k], v))
            else:
                out[k] = v
    return out


def helmet(c, r, scale, shell, glass, trim, window=4, tilt=10, segs=22, rings=16):
    """A round helmet whose visor is a clean circular window of the shell (the first `window` rings around a pole
    pointing forward, tilted `tilt` degrees up toward the camera), framed by a rim torus. Returns the parts."""
    d = Vector((0, -math.cos(math.radians(tilt)), math.sin(math.radians(tilt))))
    q = Vector((0, 0, 1)).rotation_difference(d)
    S = Matrix.Diagonal(Vector(scale)).to_4x4()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r)
    o = K.active()
    o.data.transform(S @ q.to_matrix().to_4x4())
    o.data.materials.append(shell)
    o.data.materials.append(glass)
    lim = math.cos(math.radians(180.0 / rings * window))
    for p in o.data.polygons:
        n = (q.to_matrix().inverted() @ (S.to_3x3().inverted() @ p.center)).normalized()
        if n.z > lim:
            p.material_index = 1
    o.location = c
    K.select(o)
    bpy.ops.object.transform_apply(location=True)
    bpy.ops.object.shade_smooth()
    a = math.radians(180.0 / rings * window)
    bpy.ops.mesh.primitive_torus_add(major_segments=segs, minor_segments=5, major_radius=r * math.sin(a) + 0.004,
                                     minor_radius=0.021)
    rim = K.active()
    rim.data.transform(S @ Matrix.Translation(d * r * math.cos(a)) @ q.to_matrix().to_4x4())
    rim.location = c
    K.select(rim)
    bpy.ops.object.transform_apply(location=True)
    K.finish(rim, trim, smooth=80)
    return o, rim, d, q


def bomber():
    reset()
    TM, TT = team()
    visor = mat("visor", (0.03, 0.05, 0.1), 0.06, 0.2, coat=1.0)
    eye = mat("eye_glow", (0.3, 0.85, 1.0), 0.3, emit=1.6)
    mitten = mat("mitten", (0.97, 0.95, 0.9), 0.45, coat=0.4)
    boot = mat("boot", (0.12, 0.12, 0.15), 0.3, 0.0, coat=0.8)
    sole = mat("sole", (0.32, 0.3, 0.3), 0.7)
    metal = mat("antenna_metal", (0.7, 0.72, 0.76), 0.25, 0.9)
    bobble = mat("bobble_glow", (1.0, 0.4, 0.5), 0.3, emit=1.6)
    gold = mat("buckle", (1.0, 0.78, 0.3), 0.25, 0.9)
    light = mat("pack_light", (0.4, 1.0, 0.5), 0.3, emit=3.0)

    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "hips": ((0, 0, 0.2), (0, 0, 0.31), "root"),
         "spine": ((0, 0, 0.31), (0, 0, 0.46), "hips"),
         "head": ((0, 0, 0.46), (0, 0, 0.74), "spine"),
         "antenna": ((0, 0, 0.9), (0, 0, 0.98), "head")}
    for s, side in ((1, "L"), (-1, "R")):
        B["arm." + side] = ((0.13 * s, 0, 0.4), (0.2 * s, -0.005, 0.32), "spine")
        B["forearm." + side] = ((0.2 * s, -0.005, 0.32), (0.235 * s, -0.02, 0.25), "arm." + side)
        B["hand." + side] = ((0.235 * s, -0.02, 0.25), (0.25 * s, -0.03, 0.19), "forearm." + side)
        B["thigh." + side] = ((0.07 * s, 0, 0.2), (0.075 * s, 0, 0.125), "hips")
        B["shin." + side] = ((0.075 * s, 0, 0.125), (0.075 * s, 0, 0.055), "thigh." + side)
        B["foot." + side] = ((0.075 * s, 0, 0.055), (0.075 * s, -0.09, 0.03), "shin." + side)
    rig = Rig(B)

    # body: a round suit, smooth between hips and spine (the belt and backpack follow the same weights)
    def body_w(p):
        t = smoothstep(0.2, 0.42, p.z)
        return {"hips": 1 - t + 1e-4, "spine": t + 1e-4}
    rig.custom(body_w,
               sphere(0.175, (0, 0, 0.33), TM, scale=(1.0, 0.92, 1.0), segs=16, rings=10),
               torus(0.165, 0.02, (0, 0, 0.27), TT, verts=16, minor=4, scale=(1, 0.93, 1)),
               box((0.08, 0.03, 0.055), (0, -0.155, 0.27), gold, bevel=0.012, segs=2),
               box((0.16, 0.07, 0.14), (0, 0.17, 0.35), TT, bevel=0.03, segs=2),
               sphere(0.018, (0.04, 0.207, 0.38), light, segs=8, rings=4))
    # helmet (rigid): big round shell with a circular visor window, rim, glowing eyes, ear discs, antenna
    hc = Vector((0, 0, 0.66))
    shell, rim, d, q = helmet(hc, 0.29, (1.06, 1.0, 0.93), TM, visor, TT)
    rig.rigid("head", shell, rim)
    for s in (-1, 1):
        dir_ = Matrix.Rotation(math.radians(-19 * s), 3, "Z") @ Matrix.Rotation(math.radians(4), 3, "X") @ d
        p = hc + Vector((dir_.x * 0.29 * 1.06, dir_.y * 0.29, dir_.z * 0.29 * 0.93)) * 0.99
        e = sphere(0.043, (0, 0, 0), eye, scale=(0.75, 0.3, 1.25), segs=12, rings=7)
        e.rotation_euler = (math.radians(-10), 0, math.radians(-19 * s))
        e.location = p
        rig.rigid("head", e,
                  cyl(0.075, 0.06, hc + Vector((s * 0.3, 0.02, -0.02)), TT, rot=(0, R90, 0), verts=14,
                      bevel=0.015, segs=1),
                  cyl(0.036, 0.03, hc + Vector((s * 0.332, 0.02, -0.02)), metal, rot=(0, R90, 0), verts=10))
    rig.smooth(["head", "antenna"], rod((0, 0, 0.88), (0, 0, 0.98), 0.013, metal, verts=6), power=6)
    rig.rigid("antenna", sphere(0.042, (0, 0, 0.99), bobble, segs=12, rings=7))
    for s, side in ((1, "L"), (-1, "R")):
        # arm: one open tube from inside the shoulder to inside the mitten, smooth over spine/arm/forearm/hand
        rig.smooth(["spine", "arm." + side, "forearm." + side, "hand." + side],
                   limb([(0.1 * s, 0, 0.41), (0.2 * s, -0.005, 0.32), (0.235 * s, -0.02, 0.25),
                         (0.245 * s, -0.027, 0.215)], [0.047, 0.042, 0.038, 0.036], TM, verts=10))
        hand = Vector((0.252 * s, -0.035, 0.187))
        rig.rigid("hand." + side,
                  sphere(0.058, hand, mitten, scale=(0.9, 1.0, 1.1), segs=10, rings=6),
                  sphere(0.025, hand + Vector((-0.032 * s, -0.04, 0.014)), mitten, segs=8, rings=5),
                  torus(0.042, 0.014, (0.245 * s, -0.028, 0.228), TT, rot=(0.15, -0.25 * s, 0), verts=12, minor=4))
        # leg: open tube from inside the body to inside the boot, smooth over hips/thigh/shin/foot
        rig.smooth(["hips", "thigh." + side, "shin." + side, "foot." + side],
                   limb([(0.065 * s, 0, 0.28), (0.07 * s, 0, 0.2), (0.075 * s, 0, 0.125), (0.075 * s, 0, 0.06)],
                        [0.05, 0.05, 0.046, 0.044], TT, verts=10, per=2))
        x = 0.075 * s
        rig.rigid("foot." + side,
                  box((0.115, 0.17, 0.075), (x, -0.028, 0.043), boot, bevel=0.034, segs=2),
                  box((0.1, 0.15, 0.02), (x, -0.028, 0.008), sole, bevel=0.008, segs=1),
                  cyl(0.058, 0.04, (x, 0.0, 0.088), boot, verts=12, bevel=0.012, segs=1))
    rig.build("bomber")

    # ---- actions
    L = lambda d: mirror(d)
    rest_arms = L({"arm.L": (0, -6, 0)})
    idle = {}
    for f, t in ((1, 0.0), (13, 1.0), (25, 0.0), (37, 0.6), (49, 0.0)):
        idle[f] = merge(squat(0.012 * t), L({"arm.L": (-3 * t, -6 - 8 * t, 0), "forearm.L": (-6 * t, 0, 0)}),
                        {"spine": (-3 * t, 0, 0), "head": (4 * t, 0, 0),
                         "antenna": (10 * t - 4, 0, 0)})
    idle[25]["head"] = (-1, 0, 3)
    idle[37]["head"] = (2, 0, -3)
    rig.action("idle", idle, loop=True)

    def walk_pose(ph, passing):
        """ph = +1: left foot forward at contact; passing: the swinging leg lifts, the body rises."""
        if not passing:
            p = merge(squat(0.018), {"thigh.L": (-28 * ph, 0, 0), "thigh.R": (28 * ph, 0, 0),
                                     "foot.L": (12 * ph if ph < 0 else -8, 0, 0),
                                     "foot.R": (-12 * ph if ph > 0 else -8, 0, 0)})
            p["@root"] = (0, 0, 0)
        else:
            sw = "R" if ph > 0 else "L"   # the leg now swinging forward
            st = "L" if ph > 0 else "R"
            p = {"thigh." + sw: (-30, 0, 0), "shin." + sw: (55, 0, 0), "foot." + sw: (-15, 0, 0),
                 "thigh." + st: (5, 0, 0), "@root": (0, 0, 0.035)}
        p.update({"arm.L": (32 * ph if not passing else 0, -8, 0), "arm.R": (-32 * ph if not passing else 0, 8, 0),
                  "forearm.L": (-20, 0, 0), "forearm.R": (-20, 0, 0),
                  "hips": (0, 0, 8 * ph if not passing else 0), "spine": (7, 0, -6 * ph if not passing else 0),
                  "head": (-4 if not passing else 2, 0, 0), "antenna": (-12 if passing else 14, 0, 0)})
        return p
    rig.action("walk", {1: walk_pose(1, False), 6: walk_pose(1, True), 11: walk_pose(-1, False),
                        16: walk_pose(-1, True), 21: walk_pose(1, False)}, loop=True)

    down = merge(squat(0.06), L({"arm.L": (-55, -10, 0), "forearm.L": (-25, 0, 0), "hand.L": (-10, 0, 0)}),
                 {"spine": (28, 0, 0), "head": (-12, 0, 0), "antenna": (25, 0, 0)})
    rig.action("place", {1: {}, 5: down, 8: merge(down, {"spine": (-4, 0, 0)}),
                         13: merge(squat(0.01), {"spine": (-5, 0, 0), "antenna": (-18, 0, 0)}), 17: {}})

    wind = merge(squat(0.02, ("L",)), {"thigh.R": (35, 0, 0), "shin.R": (45, 0, 0), "foot.R": (10, 0, 0),
                                       "spine": (6, 0, 0), "arm.L": (-30, -10, 0), "arm.R": (25, 10, 0),
                                       "antenna": (-10, 0, 0)})
    strike = merge(squat(0.025, ("L",)), {"thigh.R": (-75, 0, 0), "shin.R": (5, 0, 0), "foot.R": (-15, 0, 0),
                                          "spine": (-12, 0, 0), "head": (6, 0, 0), "arm.L": (10, -45, 0),
                                          "arm.R": (-10, 45, 0), "antenna": (20, 0, 0)})
    rig.action("kick", {1: {}, 5: wind, 8: strike, 11: merge(strike, {"thigh.R": (-60, 0, 0)}), 17: {}})

    rig.action("hurt", {1: {},
                        4: merge(L({"arm.L": (0, -65, 0), "forearm.L": (-30, 0, 0)}),
                                 {"spine": (-18, 0, 0), "head": (-20, 0, 0), "@root": (0, 0.03, 0.03),
                                  "antenna": (40, 0, 0)}),
                        9: merge(L({"arm.L": (0, -40, 0)}), {"spine": (-5, 12, 0), "head": (5, -18, 0),
                                                              "antenna": (-30, 20, 0)}),
                        14: merge(L({"arm.L": (0, -20, 0)}), {"spine": (0, -8, 0), "head": (0, 12, 0),
                                                              "antenna": (15, -15, 0)}),
                        19: {}})

    # die: hop and spin twice, then flop on the back, limbs splayed (the last pose holds)
    flop_arms = L({"arm.L": (0, -75, 0), "forearm.L": (0, -20, 0)})
    flop_legs = L({"thigh.L": (-20, -18, 0), "shin.L": (10, 0, 0)})
    lying = {"@root": (0, -0.3, 0.19)}
    rig.action("die", {
        1: {},
        4: merge(squat(0.04), {"spine": (10, 0, 0)}),
        9: merge(L({"arm.L": (0, -80, 0)}), {"root": (0, 0, 150), "@root": (0, 0, 0.16), "antenna": (-30, 0, 0)}),
        14: merge(L({"arm.L": (0, -100, 0)}), {"root": (0, 0, 330), "@root": (0, 0, 0.2), "head": (-10, 0, 0)}),
        19: merge(L({"arm.L": (0, -80, 0)}), flop_legs, {"root": (-35, 0, 500), "@root": (0, -0.08, 0.14),
                                                          "antenna": (40, 0, 0)}),
        24: merge(flop_arms, flop_legs, {"root": (-92, 0, 700), **lying, "head": (-8, 0, 20), "antenna": (-40, 0, 0)}),
        28: merge(flop_arms, flop_legs, {"root": (-84, 0, 710), "@root": (0, -0.29, 0.23), "head": (-5, 0, 25),
                                         "antenna": (35, 0, 0)}),
        32: merge(flop_arms, flop_legs, {"root": (-90, 0, 718), **lying, "head": (-8, 0, 28), "antenna": (-15, 0, 0)}),
        40: merge(flop_arms, flop_legs, {"root": (-90, 0, 720), **lying, "head": (-8, 0, 30), "antenna": (8, 0, 0)}),
    })

    up = L({"arm.L": (-15, -82, 0), "forearm.L": (0, -25, 0)})  # the helmet hides arms raised higher
    ready = L({"arm.L": (-40, -75, 0), "forearm.L": (-10, -30, 0)})
    rig.action("win", {
        1: merge(squat(0.045), ready, {"head": (-8, 0, 0), "antenna": (15, 0, 0)}),
        8: merge(up, L({"thigh.L": (-35, 0, 0), "shin.L": (60, 0, 0), "foot.L": (-10, 0, 0)}),
                 {"@root": (0, 0, 0.2), "spine": (-8, 0, 0), "head": (-12, 0, 0), "antenna": (-25, 0, 0)}),
        12: merge(up, L({"thigh.L": (-20, 0, 0), "shin.L": (35, 0, 0)}),
                  L({"forearm.L": (0, -55, 0)}), {"@root": (0, 0, 0.22), "head": (-12, 0, 8)}),
        18: merge(L({"arm.L": (-50, -95, 0)}), {"@root": (0, 0, 0.02), "head": (-6, 0, -6), "antenna": (30, 0, 0)}),
        22: merge(squat(0.06), ready, {"head": (-4, 0, 0), "antenna": (-10, 0, 0)}),
        31: merge(squat(0.045), ready, {"head": (-8, 0, 0), "antenna": (15, 0, 0)}),
    }, loop=True)

    # lose: a slump (kept light: the big helmet makes any forward tilt read strongly from above) and sobs
    slump = merge(squat(0.03), L({"arm.L": (-12, 4, 0), "forearm.L": (-10, 0, 0)}),
                  {"spine": (9, 0, 0), "head": (5, 0, 0), "antenna": (60, 0, 0)})
    rig.action("lose", {
        1: slump,
        11: merge(slump, {"spine": (3, 0, 3), "head": (3, 0, -5), "antenna": (12, 0, 5)}),
        21: merge(slump, {"spine": (-2, 0, 0), "head": (-2, 0, 0), "antenna": (-6, 0, 0), "@hips": (0, 0, -0.022)}),
        31: merge(slump, {"spine": (3, 0, -3), "head": (3, 0, 5), "antenna": (12, 0, -5)}),
        41: slump,
    }, loop=True)
    rig.export("bomber")


# ------------------------------------------------------------------ enemies

def blob():
    reset()
    jelly = mat("blob_jelly", (0.2, 0.75, 0.15), 0.08, coat=1.0, emit=0.15, emit_color=(0.3, 0.9, 0.35))
    shine = mat("blob_shine", (0.9, 1.0, 0.9), 0.1, emit=1.5)
    white = mat("eye_white", (0.97, 0.97, 0.95), 0.3, coat=0.6)
    pupil = mat("pupil", (0.03, 0.03, 0.05), 0.2, coat=1.0)
    mouth = mat("blob_mouth", (0.1, 0.25, 0.08), 0.5)
    rig = Rig({"root": ((0, 0, 0), (0, 0, 0.06), None),
               "body": ((0, 0, 0.02), (0, 0, 0.2), "root"),
               "top": ((0, 0, 0.2), (0, 0, 0.44), "body")})
    body = sphere(0.3, (0, 0, 0.23), jelly, scale=(1, 1, 0.78), segs=22, rings=13)
    for v in body.data.vertices:  # a gummy drop: flat bottom, a soft peak on top
        if v.co.z < 0.02:
            v.co.z = 0.02 + (v.co.z - 0.02) * 0.15
        if v.co.z > 0.3:
            v.co.z += (v.co.z - 0.3) * 0.7
            v.co.x *= 1 - (v.co.z - 0.3) * 0.6
            v.co.y *= 1 - (v.co.z - 0.3) * 0.6

    def w(p):
        t = smoothstep(0.1, 0.36, p.z)
        return {"body": 1 - t + 1e-4, "top": t + 1e-4}
    parts = [body, sphere(0.05, (-0.12, -0.19, 0.36), shine, scale=(1, 0.4, 0.7), segs=10, rings=6, rot=(0.6, 0, -0.5))]
    for s in (-1, 1):
        parts += [sphere(0.072, (s * 0.1, -0.255, 0.31), white, scale=(1, 0.6, 1.15), segs=14, rings=8),
                  sphere(0.036, (s * 0.095, -0.293, 0.3), pupil, scale=(1, 0.5, 1.2), segs=10, rings=6),
                  sphere(0.011, (s * 0.083, -0.31, 0.325), shine, segs=6, rings=4)]
    parts.append(torus(0.045, 0.012, (0, -0.29, 0.2), mouth, rot=(R90 + 0.3, 0, 0), verts=12, minor=4,
                       scale=(1.3, 1, 0.6)))
    rig.custom(w, *parts)
    rig.build("blob")
    rig.action("move", {
        1: {"%body": (1.14, 1.14, 0.82), "top": (-4, 0, 0)},
        7: {"%body": (0.9, 0.9, 1.16), "@root": (0, 0, 0.05), "top": (6, 0, 0)},
        13: {"%body": (0.97, 0.97, 1.05), "@root": (0, 0, 0.08), "top": (8, 5, 0)},
        19: {"%body": (1.2, 1.2, 0.74), "top": (-10, -3, 0)},
        25: {"%body": (1.14, 1.14, 0.82), "top": (-4, 0, 0)},
    }, loop=True)
    rig.action("die", {1: {}, 5: {"%body": (0.8, 0.8, 1.3), "@root": (0, 0, 0.04)},
                       11: {"%body": (1.4, 1.4, 0.25), "top": (0, 0, 20)},
                       20: {"%body": (1.55, 1.55, 0.08), "top": (0, 0, 25)}})
    rig.export("blob")


def bat():
    reset()
    fur = mat("bat_fur", (0.3, 0.18, 0.42), 0.55, coat=0.3)
    belly = mat("bat_belly", (0.55, 0.4, 0.62), 0.6)
    wing = mat("bat_wing", (0.42, 0.2, 0.5), 0.45, coat=0.2)
    bone_m = mat("bat_finger", (0.2, 0.1, 0.26), 0.5)
    eye = mat("bat_eye", (1.0, 0.8, 0.2), 0.3, emit=5.0)
    fang = mat("fang", (0.97, 0.96, 0.9), 0.3)
    c = Vector((0, 0, 0.47))
    B = {"root": ((0, 0, 0), (0, 0, 0.1), None), "body": ((0, 0, 0.38), (0, 0, 0.56), "root")}
    for s, side in ((1, "L"), (-1, "R")):
        B["wing." + side] = ((0.09 * s, 0.01, 0.49), (0.29 * s, 0.03, 0.52), "body")
        B["tip." + side] = ((0.29 * s, 0.03, 0.52), (0.52 * s, 0.06, 0.49), "wing." + side)
    rig = Rig(B)
    rig.rigid("body", sphere(0.13, c, fur, scale=(1.0, 0.95, 1.05), segs=16, rings=10),
              sphere(0.08, c + Vector((0, -0.08, -0.03)), belly, scale=(1, 0.6, 1.1), segs=12, rings=7))
    for s in (-1, 1):
        rig.rigid("body",
                  rod(c + Vector((s * 0.06, 0, 0.09)), c + Vector((s * 0.12, 0.01, 0.22)), 0.05, fur, r2=0.0, verts=8),
                  rod(c + Vector((s * 0.063, -0.012, 0.1)), c + Vector((s * 0.11, -0.005, 0.19)), 0.03, belly, r2=0.0,
                      verts=6),
                  sphere(0.028, c + Vector((s * 0.05, -0.115, 0.03)), eye, scale=(1, 0.5, 1.1), segs=10, rings=6),
                  rod(c + Vector((s * 0.025, -0.115, -0.04)), c + Vector((s * 0.025, -0.12, -0.075)), 0.01, fang,
                      r2=0.0, verts=5),
                  sphere(0.025, c + Vector((s * 0.05, 0.0, -0.13)), bone_m, segs=8, rings=5))
    # wings: a membrane with a scalloped trailing edge, smooth over body / wing / tip
    import bmesh
    for s, side in ((1, "L"), (-1, "R")):
        me = bpy.data.meshes.new("wing")
        bm = bmesh.new()
        N, M = 10, 3
        grid = []
        for i in range(N + 1):
            u = i / N
            x = 0.08 + u * 0.46
            lead_z = 0.5 + 0.05 * math.sin(u * math.pi) - 0.02 * u
            chord = 0.22 * (1 - u * 0.55) * (0.72 + 0.28 * abs(math.cos(u * math.pi * 2.5)))
            row = []
            for j in range(M + 1):
                v = j / M
                row.append(bm.verts.new((s * x, 0.03 + 0.03 * u + 0.02 * v, lead_z - chord * v)))
            grid.append(row)
        for i in range(N):
            for j in range(M):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if s > 0 else f[::-1])
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("wing", me)
        bpy.context.scene.collection.objects.link(o)
        K.select(o)
        sol = o.modifiers.new("s", "SOLIDIFY")
        sol.thickness = 0.014
        sol.offset = 0
        bpy.ops.object.modifier_apply(modifier=sol.name)
        K.finish(o, wing, smooth=50)
        bones = ["body", "wing." + side, "tip." + side]
        rig.smooth(bones, o)
        rig.smooth(bones, limb([(0.08 * s, 0.03, 0.5), (0.29 * s, 0.045, 0.535), (0.54 * s, 0.07, 0.48)],
                               [0.018, 0.014, 0.008], bone_m, verts=6, per=4, caps=True))
    rig.build("bat")
    up = mirror({"wing.L": (0, -48, 0), "tip.L": (0, -20, 0)})
    mid_d = mirror({"wing.L": (0, 5, 0), "tip.L": (0, -12, 0)})
    down = mirror({"wing.L": (0, 42, 0), "tip.L": (0, 22, 0)})
    mid_u = mirror({"wing.L": (0, 0, 0), "tip.L": (0, 28, 0)})
    rig.action("move", {1: merge(up, {"@root": (0, 0, -0.02), "body": (4, 0, 0)}),
                        4: merge(mid_d, {"@root": (0, 0, 0.0)}),
                        7: merge(down, {"@root": (0, 0, 0.03), "body": (-4, 0, 0)}),
                        10: merge(mid_u, {"@root": (0, 0, 0.01)}),
                        13: merge(up, {"@root": (0, 0, -0.02), "body": (4, 0, 0)})}, loop=True)
    fold = mirror({"wing.L": (0, 70, 0), "tip.L": (0, 95, 0)})
    rig.action("die", {1: {}, 5: merge(up, {"@root": (0, 0, 0.05), "body": (-20, 0, 0)}),
                       12: merge(fold, {"root": (0, 0, 200), "@root": (0, 0, -0.15), "body": (30, 0, 0)}),
                       18: merge(fold, {"root": (0, 0, 360), "@root": (0, 0, -0.34), "body": (60, 0, 0)}),
                       24: merge(fold, {"root": (0, 0, 380), "@root": (0, 0, -0.34), "body": (70, 20, 0)})})
    rig.export("bat")


def ghost():
    reset()
    import bmesh
    sheet = mat("ghost_sheet", (0.9, 0.96, 1.0), 0.3, coat=0.5, emit=0.6, emit_color=(0.6, 0.85, 1.0), alpha=0.86)
    dark = mat("ghost_face", (0.05, 0.06, 0.12), 0.2, coat=1.0)
    blush = mat("ghost_blush", (1.0, 0.55, 0.7), 0.5, emit=0.6)
    hems = {"hem.F": (0, -1), "hem.B": (0, 1), "hem.L": (1, 0), "hem.R": (-1, 0)}
    B = {"root": ((0, 0, 0), (0, 0, 0.1), None), "body": ((0, 0, 0.18), (0, 0, 0.45), "root"),
         "head": ((0, 0, 0.45), (0, 0, 0.72), "body")}
    for n, (dx, dy) in hems.items():
        B[n] = ((dx * 0.05, dy * 0.05, 0.32), (dx * 0.28, dy * 0.28, 0.08), "body")
    for s, side in ((1, "L"), (-1, "R")):
        B["arm." + side] = ((0.2 * s, -0.02, 0.4), (0.33 * s, -0.07, 0.34), "body")
    rig = Rig(B)
    # lathe: dome, body and a wavy flared hem
    me = bpy.data.meshes.new("ghost")
    bm = bmesh.new()
    S = 22
    prof = [(0.0, 0.8), (0.1, 0.785), (0.18, 0.74), (0.235, 0.66), (0.26, 0.55), (0.265, 0.44), (0.27, 0.33),
            (0.285, 0.23), (0.31, 0.14), (0.33, 0.09)]
    rings = []
    for r, z in prof[1:]:
        ring = []
        for k in range(S):
            a = 2 * math.pi * k / S
            zz = z + (0.045 * math.cos(6 * a) if z < 0.1 else 0.0)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), zz)))
        rings.append(ring)
    top = bm.verts.new((0, 0, prof[0][1]))
    for k in range(S):
        bm.faces.new((top, rings[0][k], rings[0][(k + 1) % S]))
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(S):
            bm.faces.new((r0[k], r1[k], r1[(k + 1) % S], r0[(k + 1) % S]))
    inner = [bm.verts.new((v.co.x * 0.85, v.co.y * 0.85, v.co.z + 0.04)) for v in rings[-1]]
    for k in range(S):  # a short inward lip and an underside so the sheet reads as closed
        bm.faces.new((rings[-1][k], inner[k], inner[(k + 1) % S], rings[-1][(k + 1) % S]))
    under = bm.verts.new((0, 0, 0.26))
    for k in range(S):
        bm.faces.new((inner[k], under, inner[(k + 1) % S]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    body = bpy.data.objects.new("ghost", me)
    bpy.context.scene.collection.objects.link(body)
    K.finish(body, sheet, smooth=80)

    def w(p):
        out = {}
        th = smoothstep(0.45, 0.62, p.z)
        hem = smoothstep(0.34, 0.12, p.z)
        out["head"] = th + 1e-4
        out["body"] = (1 - th) * (1 - hem) + 1e-4
        ang = math.atan2(p.y, p.x)
        tot = 0
        ws = {}
        for n, (dx, dy) in hems.items():
            c = max(0.0, math.cos(ang - math.atan2(dy, dx)))
            ws[n] = c ** 2
            tot += c ** 2
        for n in hems:
            out[n] = hem * ws[n] / tot + 1e-4
        return out
    face = [body]
    for s in (-1, 1):
        face += [sphere(0.035, (s * 0.075, -0.235, 0.56), dark, scale=(0.9, 0.5, 1.3), segs=10, rings=6),
                 sphere(0.01, (s * 0.068, -0.252, 0.585), blush, segs=6, rings=4),
                 sphere(0.03, (s * 0.14, -0.2, 0.49), blush, scale=(1.2, 0.4, 0.7), segs=8, rings=5)]
    face.append(sphere(0.028, (0, -0.25, 0.47), dark, scale=(0.9, 0.4, 1.1), segs=10, rings=6))
    rig.custom(w, *face)
    for s, side in ((1, "L"), (-1, "R")):
        rig.smooth(["body", "arm." + side], limb([(0.19 * s, -0.02, 0.42), (0.27 * s, -0.05, 0.37),
                                                  (0.33 * s, -0.07, 0.34)], [0.06, 0.05, 0.04], sheet, verts=10, caps=True))
    rig.build("ghost")

    def flare(ph):
        """Hem ripple: the four flaps flare out in turn."""
        f = lambda k: 14 * math.sin(ph + k * math.pi / 2)
        return {"hem.F": (f(0), 0, 0), "hem.L": (0, -f(1), 0), "hem.B": (-f(2), 0, 0), "hem.R": (0, f(3), 0)}
    keys = {}
    for i in range(5):
        a = i * math.pi / 2
        keys[1 + i * 10] = merge(flare(a), {"@root": (0, 0, 0.04 * math.sin(a)), "body": (0, 6 * math.cos(a), 0),
                                            "head": (3 * math.sin(a), -4 * math.cos(a), 0),
                                            "arm.L": (0, -15 * math.sin(a), 0), "arm.R": (0, -15 * math.sin(a), 0)})
    rig.action("move", keys, loop=True)
    rig.action("die", {1: {}, 6: merge(flare(1), {"@root": (0, 0, 0.08), "%root": 1.1, "arm.L": (0, -60, 0),
                                                 "arm.R": (0, 60, 0)}),
                       14: merge(flare(2), {"root": (0, 0, 200), "@root": (0, 0, 0.3), "%root": 0.7}),
                       24: {"root": (0, 0, 400), "@root": (0, 0, 0.55), "%root": 0.05}})
    rig.export("ghost")


def stomper():
    reset()
    shell = mat("stomper_shell", (0.55, 0.12, 0.1), 0.22, 0.35, coat=1.0)
    spot = mat("stomper_spot", (0.1, 0.08, 0.08), 0.3, coat=0.8)
    chitin = mat("stomper_chitin", (0.12, 0.11, 0.13), 0.35, 0.3, coat=0.6)
    horn = mat("stomper_horn", (0.85, 0.78, 0.6), 0.35, coat=0.5)
    eye = mat("stomper_eye", (1.0, 0.55, 0.1), 0.3, emit=5.0)
    B = {"root": ((0, 0, 0), (0, 0, 0.1), None), "body": ((0, 0.16, 0.3), (0, -0.14, 0.3), "root"),
         "head": ((0, -0.14, 0.28), (0, -0.32, 0.28), "body")}
    legs = {}
    for i, y in enumerate((-0.1, 0.04, 0.17)):
        for s, side in ((1, "L"), (-1, "R")):
            n = "leg%d.%s" % (i + 1, side)
            knee = (0.33 * s, y + (i - 1) * 0.07, 0.3)
            foot = (0.38 * s, y + (i - 1) * 0.12, 0.0)
            B[n] = ((0.13 * s, y, 0.22), knee, "body")
            B["low" + n[3:]] = (knee, foot, n)
            legs[n] = ((0.13 * s, y, 0.22), knee, foot)
    rig = Rig(B)
    rig.rigid("body",
              sphere(0.3, (0, 0.04, 0.3), shell, scale=(0.82, 1.0, 0.62), segs=20, rings=11),
              box((0.012, 0.52, 0.02), (0, 0.05, 0.485), chitin, rot=(0.0, 0, 0), bevel=0.0),
              sphere(0.26, (0, 0.04, 0.2), chitin, scale=(0.85, 1.0, 0.45), segs=14, rings=7))
    for s in (-1, 1):
        for p in ((0.1, -0.05), (0.14, 0.12), (0.07, 0.2)):
            rig.rigid("body", sphere(0.04, (s * p[0], p[1], 0.45 - p[0] * 0.5), spot, scale=(1, 1, 0.35), segs=10,
                                     rings=5, rot=(0, s * 0.35, 0)))
    rig.rigid("head",
              sphere(0.13, (0, -0.26, 0.25), chitin, scale=(1.1, 0.9, 0.85), segs=14, rings=8),
              limb([(0, -0.34, 0.3), (0, -0.42, 0.38), (0, -0.43, 0.5), (0, -0.38, 0.56)],
                   [0.05, 0.04, 0.03, 0.012], horn, verts=8, per=3, caps=True))
    for s in (-1, 1):
        rig.rigid("head",
                  sphere(0.03, (s * 0.08, -0.35, 0.28), eye, scale=(1, 0.6, 1), segs=10, rings=6),
                  limb([(s * 0.07, -0.34, 0.2), (s * 0.08, -0.42, 0.18), (s * 0.03, -0.46, 0.17)],
                       [0.025, 0.02, 0.008], horn, verts=6, per=2, caps=True))
    for n, (hip, knee, foot) in legs.items():
        side = n[-1]
        rig.rigid(n, limb([hip, knee], [0.035, 0.03], chitin, verts=8, per=2),
                  sphere(0.035, knee, chitin, segs=8, rings=5))
        rig.rigid("low" + n[3:], limb([knee, foot], [0.028, 0.02], chitin, verts=8, per=2),
                  sphere(0.03, Vector(foot) + Vector((0, 0, 0.02)), shell, segs=8, rings=5))
    rig.build("stomper")

    A = ("leg1.L", "leg2.R", "leg3.L")
    Bt = ("leg1.R", "leg2.L", "leg3.R")

    def leg(n, swing, lift):
        s = 1 if n.endswith("L") else -1
        return {n: (0, -lift * s, -swing * 22 * s), "low" + n[3:]: (0, lift * 0.5 * s, 0)}

    def pose(sa, la, sb, lb, bob, roll):
        p = {"@root": (0, 0, bob), "body": (0, roll, 0), "head": (0, -roll * 0.5, roll * 2)}
        for n in A:
            p.update(leg(n, sa, la))
        for n in Bt:
            p.update(leg(n, sb, lb))
        return p
    rig.action("move", {1: pose(-1, 0, 1, 0, -0.02, 4), 7: pose(0, 28, 0, 0, 0.012, 0),
                        13: pose(1, 0, -1, 0, -0.02, -4), 19: pose(0, 0, 0, 28, 0.012, 0),
                        25: pose(-1, 0, 1, 0, -0.02, 4)}, loop=True)
    curl = {}
    for n in A + Bt:
        s = 1 if n.endswith("L") else -1
        curl[n] = (0, -40 * s, 0)
        curl["low" + n[3:]] = (0, -30 * s, 0)
    twitch = {k: (v[0], v[1] * 0.6, 15) for k, v in curl.items()}
    rig.action("die", {1: {}, 6: {"root": (0, 90, 0), "@root": (0, 0, 0.35)},
                       12: merge(curl, {"root": (0, 180, 0), "@root": (0, 0, 0.5)}),
                       16: merge(twitch, {"root": (0, 176, 0), "@root": (0, 0, 0.52)}),
                       20: merge(curl, {"root": (0, 180, 0), "@root": (0, 0, 0.5)}),
                       24: merge(twitch, {"root": (0, 180, 0), "@root": (0, 0, 0.5)}),
                       30: merge(curl, {"root": (0, 180, 0), "@root": (0, 0, 0.5)})})
    rig.export("stomper")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    only = args[1:]
    for n, fn in (("bomber", bomber), ("blob", blob), ("bat", bat), ("ghost", ghost), ("stomper", stomper)):
        if not only or n in only:
            fn()
