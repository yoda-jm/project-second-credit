"""Mossfolk (game 15) models: the mossling (a round moss sprite with big eyes, a sprout leaf on its head and a tiny
lantern on a stick strapped to its back), the entrance hatch, the exit burrow, two traps and the cavern dressing.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/mossfolk_models.py -- godot/games/mossfolk/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, ico, rod, tube, prism, join, export), the rig from
blastyard_bombers.py (Rig, mirror, merge, limb), prism_models.py (animate, export_anim) and nightbite_characters.py
(blob, about). 30 fps.

Axes: the level is seen from the side. Blender Z up, the camera side is -Y; in Godot +X stays +X, Blender +Z becomes
+Y (up) and Blender -Y becomes +Z (towards the camera). Walking right is +X: mirror the mossling (scale x = -1 on
its parent) to walk left. Origins sit on the ground unless noted.

mossling.glb  armature "mossling_rig" with the skinned mesh "mossling", 0.87 tall (0.6 to the top of the ball, the
              leaf and the lantern stand above it), 0.5 across, feet centred on the origin, facing +X, its right side
              (the side with the pick and the brick) towards the camera. Bone-attached nodes: "leaf" (the sprout on
              its head, bone "leaf": always visible; it becomes the parachute in float), "pick" (bone "pick", visible
              only in mine) and "brick" (bone "brick", visible only in build). The pick, brick and brows are hidden by
              bone scale 0 in every animation: in the bare rest pose (no animation playing) they show, so always play
              one. Materials: moss_body, moss_body_dark (tufts, arms, legs), moss_belly (the face and belly), moss_paw,
              moss_foot, moss_eye, moss_pupil, moss_shine, moss_cheek, moss_brow, moss_leaf, moss_leaf_under,
              moss_stick, moss_lantern (the brass frame), moss_lantern_glow (emissive), moss_pick_wood,
              moss_pick_head, moss_brick.
              Animations (loops unless noted): walk 1 s, fall 0.4 s, float 1 s, climb 0.67 s (a wall touching the
              front of the ball, x = +0.25), dig 0.53 s, bash 0.67 s, mine 0.8 s, build 1 s (the brick lands at
              x = +0.2 .. +0.4 on the ground at 0.47 s and pops back into the paws at 0.9 s), block 1 s,
              shrug (one-shot 1 s), panic 0.4 s, splat (one-shot 0.8 s: flattened, holds the last frame),
              exit (one-shot 1 s), drown (one-shot 1.5 s: sinks 1.1 below the origin).
hatch.glb     the entrance: root "hatch" (a hollow stump standing out of a mossy rock mass, 3.3 wide, 2.5 tall)
              with the children "door_front" and "door_back" (half-disc trapdoors under the stump's open bottom,
              hinged at y = -0.52 / +0.52). Origin at the centre of the opening on its underside: creatures drop out
              of it straight down; hang it in the air. Animation "open" (one-shot 1.5 s): the doors rattle, drop
              open and swing to rest hanging down (0.56 below the origin); the front door ends facing the camera.
              Depth y -0.75 .. +0.95.
burrow.glb    the exit: root "burrow" (a mossy mound with a round lit doorway, stone frame, an open door, a window,
              a chimney), child "flame" (the lantern's glowing core, right of the door). Origin at the bottom centre
              of the doorway. 3.1 wide, 3.0 tall; the mound's face stays behind y = +0.12 (behind the walking plane)
              except the threshold stone (from y = -0.1) and the door leaf (to y = -0.55 at x = -0.95). Animation
              "glow" (loop 2 s): the flame flickers.
trap_snapper  a snapping plant, 1.15 tall, facing +X: armature "trap_snapper_rig", mesh "trap_snapper".
              idle (loop 2 s), snap (one-shot 1 s: rears, bites the ground at about x = +0.55, lifts, chews, gulps,
              reopens; jaws shut at 0.37 s).
trap_crusher  root "trap_crusher" (the rock housing, 1.4 wide, from z = 2.0 to 3.4) with the child "stone" (the
              spiked block and its chains, rest bottom at z = 1.25). Origin on the ground under the block.
              Animation "crush" (one-shot 1.8 s): shivers, falls to the ground at 0.53 s, bounces, holds, winches up.
Decorations (one node each, named like the file, origin at the base, the front faces -Y):
              mushroom_big 1.25 tall, mushroom_small (a cluster, 0.5 tall), crystal_cluster 0.9 tall
              ("crystal_glow", "crystal_glow_pale"), root_hang (origin at the TOP, hangs 1.5 down),
              fern 0.75 tall, lantern_post 1.6 tall ("lantern_post_glow").
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90
from blastyard_bombers import Rig, merge, mirror, limb, FPS
from prism_models import animate, export_anim, new_obj
from nightbite_characters import blob, about

Q = Matrix.Rotation(R90, 4, "Z")       # the mossling is built facing -Y, then turned to face +X
Q3 = Q.to_3x3()


def turn(o):
    """Bakes an object's transform into its mesh, then turns it from facing -Y to facing +X."""
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    o.data.transform(Q)
    return o


class SideRig(Rig):
    """The blastyard Rig, written facing -Y (all poses and positions), built and exported facing +X.
    `hidden` bones default to scale 0 (props shown only in some actions)."""

    def __init__(self, bones, hidden=()):
        super().__init__({n: (tuple(Q3 @ Vector(h)), tuple(Q3 @ Vector(t)), p) for n, (h, t, p) in bones.items()})
        self.hidden = set(hidden)

    def weights(self, p, spec):
        if callable(spec):
            return spec(Q3.transposed() @ p)
        return super().weights(p, spec)

    def build(self, name):
        for o, _ in self.parts:
            turn(o)
        return super().build(name)

    def local_rot(self, bone, deg, prev):
        R = (Matrix.Rotation(math.radians(deg[2]), 3, "Z") @ Matrix.Rotation(math.radians(deg[1]), 3, "Y")
             @ Matrix.Rotation(math.radians(deg[0]), 3, "X"))
        R = Q3 @ R @ Q3.transposed()
        M = self.rest[bone]
        L = M.inverted() @ R @ M
        return L.to_euler("XYZ", prev) if prev is not None else L.to_euler("XYZ")

    def local_scale(self, bone, s):
        if not isinstance(s, (tuple, list)):
            s = (s, s, s)
        S = Q3 @ Matrix.Diagonal(Vector(s)) @ Q3.transposed()
        M = self.rest[bone]
        L = M.inverted() @ S @ M
        return Vector((abs(L[0][0]), abs(L[1][1]), abs(L[2][2])))

    def action(self, name, keys, loop=False):
        out = {}
        for f, p in keys.items():
            p = dict(p)
            for k in list(p):
                if k[0] == "@":
                    p[k] = tuple(Q3 @ Vector(p[k]))
            for b in self.hidden:
                p.setdefault("%" + b, 0.0)
            out[f] = p
        super().action(name, out, loop)

    def attach(self, bone, parts, name, pivot):
        """Joins parts (built facing -Y) into one node `name` parented to `bone`, origin at pivot (-Y coords)."""
        parts = K.flatten(parts)
        for o in parts:
            turn(o)
        o = join(parts, name, pivot=Q3 @ Vector(pivot))
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy()
        o.parent = self.arm
        o.parent_type = "BONE"
        o.parent_bone = bone
        bpy.context.view_layer.update()
        o.matrix_world = mw
        return o


def painted_ball(r, c, scale, mats, paint, segs=18, rings=12, name="ball"):
    """A UV sphere whose faces take mats[paint(normal)] (normal of the unscaled sphere)."""
    me = bpy.data.meshes.new(name)
    for m in mats:
        me.materials.append(m)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    for f in bm.faces:
        f.material_index = paint(f.calc_center_median().normalized())
        f.smooth = True
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal(Vector(scale)).to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def lumpy(r, loc, material, seed, amount=0.18, scale=(1, 1, 1), sub=1, smooth=0):
    """A flat-shaded icosphere with its vertices pushed in and out: a rock, a tuft, a clump."""
    o = ico(r, (0, 0, 0), material, scale=(1, 1, 1), sub=sub, smooth=smooth)
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co = v.co * (1 + rnd.uniform(-amount, amount))
    o.data.transform(Matrix.Diagonal(Vector(scale)).to_4x4())
    o.data.transform(Matrix.Translation(Vector(loc)))
    o.data.update()
    return o


def lathe_r(profile, material, segs=16, radial=None, name="lathe", smooth=60, center=(0, 0, 0)):
    """Surface of revolution about Z from (r, z) pairs, top to bottom; radial(k, z) multiplies the radius."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-4:
            rings.append([bm.verts.new((center[0], center[1], z))])
        else:
            ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                rr = r * (radial(k, z) if radial else 1.0)
                ring.append(bm.verts.new((center[0] + rr * math.cos(a), center[1] + rr * math.sin(a), z)))
            rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segs):
            q = [r0[k % len(r0)], r1[k % len(r1)], r1[(k + 1) % len(r1)], r0[(k + 1) % len(r0)]]
            q = [v for i, v in enumerate(q) if v not in q[:i]]
            if len(q) >= 3:
                bm.faces.new(q)
    return new_obj(name, bm, material, smooth)


def solid(o, t):
    K.select(o)
    s = o.modifiers.new("s", "SOLIDIFY")
    s.thickness = t
    s.offset = 0
    bpy.ops.object.modifier_apply(modifier=s.name)
    return o


# ------------------------------------------------------------------ the mossling

C = Vector((0, 0, 0.36))       # ball centre (built facing -Y)
BR = 0.245
BSC = (1.0, 0.97, 0.98)
LEAF0 = Vector((0, 0.0, 0.575))  # leaf bone head (stem base)
TIP = Vector((0, 0.34, 0.775))   # stick tip: the lantern hangs here


def over(*poses):
    """Like merge, but later poses replace earlier channels instead of adding to them."""
    out = {}
    for p in poses:
        out.update(p)
    return out


def ball_point(d, k=1.0):
    d = Vector(d).normalized()
    return C + Vector((d.x * BR * BSC[0], d.y * BR * BSC[1], d.z * BR * BSC[2])) * k


def mossling():
    reset()
    body = mat("moss_body", (0.3, 0.56, 0.2), 0.85)
    dark = mat("moss_body_dark", (0.16, 0.36, 0.13), 0.9)
    belly = mat("moss_belly", (0.8, 0.86, 0.52), 0.8)
    paw = mat("moss_paw", (0.93, 0.8, 0.58), 0.6)
    foot = mat("moss_foot", (0.34, 0.2, 0.1), 0.7)
    eye = mat("moss_eye", (1.0, 0.99, 0.95), 0.25, coat=0.6, emit=0.15)
    pupil = mat("moss_pupil", (0.03, 0.04, 0.06), 0.15, coat=1.0)
    shine = mat("moss_shine", (1.0, 1.0, 1.0), 0.2, emit=4.0)
    cheek = mat("moss_cheek", (1.0, 0.5, 0.45), 0.6)
    brow_m = mat("moss_brow", (0.1, 0.18, 0.06), 0.8)
    leaf_m = mat("moss_leaf", (0.55, 0.85, 0.16), 0.55, coat=0.3)
    leaf_u = mat("moss_leaf_under", (0.72, 0.9, 0.4), 0.7)
    stick_m = mat("moss_stick", (0.42, 0.26, 0.13), 0.8)
    brass = mat("moss_lantern", (0.62, 0.42, 0.18), 0.4, 0.7)
    glow = mat("moss_lantern_glow", (1.0, 0.72, 0.3), 0.4, emit=7.0, emit_color=(1.0, 0.62, 0.2))
    pwood = mat("moss_pick_wood", (0.6, 0.42, 0.24), 0.7)
    phead = mat("moss_pick_head", (0.55, 0.58, 0.62), 0.35, 0.8)
    brick_m = mat("moss_brick", (0.78, 0.52, 0.32), 0.85)

    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0, 0.14), (0, 0, 0.5), "root"),
         "leaf": (tuple(LEAF0), tuple(LEAF0 + Vector((0, 0, 0.1))), "body"),
         "stick": ((0, 0.17, 0.3), tuple(TIP), "body"),
         "lantern": (tuple(TIP), tuple(TIP + Vector((0, 0, -0.12))), "stick")}
    for s, side in ((1, "L"), (-1, "R")):
        B["arm." + side] = ((0.2 * s, 0, 0.37), (0.235 * s, -0.005, 0.25), "body")
        B["forearm." + side] = ((0.235 * s, -0.005, 0.25), (0.242 * s, -0.012, 0.13), "arm." + side)
        B["thigh." + side] = ((0.09 * s, 0, 0.17), (0.095 * s, 0, 0.075), "root")
        B["foot." + side] = ((0.095 * s, 0, 0.075), (0.095 * s, -0.08, 0.02), "thigh." + side)
    # the eyes, looking forward from the front-sides of the ball (the camera sees the right one in profile)
    eyes = {}
    for s, side in ((1, "L"), (-1, "R")):
        d = Vector((0.72 * s, -0.6, 0.28)).normalized()
        eyes[side] = (d, ball_point(d, 0.93))
        # frame on the eye: t across (towards the ball's front), u up
        t = d.cross(Vector((0, 0, 1))).normalized()
        u = t.cross(d).normalized()
        if u.z < 0:
            u = -u
        bc = eyes[side][1] + d * 0.035 + u * 0.115
        B["brow." + side] = (tuple(bc), tuple(bc + d * 0.03), "body")
    B["pick"] = ((-0.242, -0.012, 0.13), (-0.242, -0.012, 0.0), "forearm.R")
    B["brick"] = ((-0.242, -0.012, 0.13), (-0.242, -0.012, 0.05), "forearm.R")
    rig = SideRig(B, hidden=("pick", "brick", "brow.L", "brow.R"))

    # the ball: moss on top and back, a pale face and belly patch in front
    ball = painted_ball(BR, C, BSC, [body], lambda n: 0, segs=16, rings=11)
    bd = Vector((0, -1, -0.35)).normalized()
    rig.rigid("body", ball, blob(0.17, ball_point(bd, 0.8), belly, (1.15, 0.3, 1.05), bd, segs=12, rings=7))
    # moss tufts: flattened lumps over the crown and back (a shaggy silhouette)
    rnd = random.Random(15)
    for k, (dx, dy, dz, r) in enumerate(((0.0, 0.2, 1.0, 0.075), (0.45, 0.35, 0.85, 0.065), (-0.45, 0.35, 0.85, 0.065),
                                         (0.2, 0.9, 0.5, 0.07), (-0.2, 0.9, 0.5, 0.07), (0.0, 0.85, -0.1, 0.07),
                                         (0.7, 0.55, 0.2, 0.06), (-0.7, 0.55, 0.2, 0.06), (0.0, -0.45, 0.9, 0.06))):
        d = Vector((dx, dy, dz)).normalized()
        o = lumpy(r, (0, 0, 0), dark, 100 + k, amount=0.2, scale=(1.0, 1.0, 0.6), smooth=70)
        o.data.transform(Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
        o.data.transform(Matrix.Translation(ball_point(d, 0.97)))
        rig.rigid("body", o)
    # eyes: big whites with the pupils toward the front, a shine; cheeks under them
    for s, side in ((1, "L"), (-1, "R")):
        d, p = eyes[side]
        fwd = Vector((0, -1, 0))
        pp = p + d * 0.045 + (fwd - d * fwd.dot(d)).normalized() * 0.022 + Vector((0, 0, -0.004))
        rig.rigid("body",
                  blob(0.098, p, eye, (1.0, 0.62, 1.22), d, segs=12, rings=7),
                  blob(0.058, pp, pupil, (0.95, 0.5, 1.12), d, segs=10, rings=6),
                  sphere(0.019, pp + d * 0.03 + Vector((0, -0.012, 0.028)), shine, segs=6, rings=4))
        cd = Vector((0.78 * s, -0.5, -0.1)).normalized()
        rig.rigid("body", blob(0.04, ball_point(cd, 0.985), cheek, (1.2, 0.3, 0.8), cd, segs=8, rings=5))
        # brows (hidden unless an action shows them)
        t = d.cross(Vector((0, 0, 1))).normalized()
        u = t.cross(d).normalized()
        if u.z < 0:
            u = -u
        bc = p + d * 0.035 + u * 0.115
        pts = [bc + t * k * 0.055 + u * (0.012 * (1 - k * k)) for k in (-1, 0, 1)]
        rig.rigid("brow." + side, limb(pts, [0.011, 0.018, 0.011], brow_m, verts=5, per=2, caps=True))
    # arms (dark moss noodles), cream paws; stubby legs, bark-brown feet
    for s, side in ((1, "L"), (-1, "R")):
        rig.smooth(["body", "arm." + side, "forearm." + side],
                   limb([(0.16 * s, 0, 0.38), (0.2 * s, 0, 0.37), (0.235 * s, -0.005, 0.25),
                         (0.242 * s, -0.012, 0.15)], [0.034, 0.033, 0.03, 0.029], dark, verts=8, per=2), power=6)
        rig.rigid("forearm." + side, sphere(0.048, (0.243 * s, -0.014, 0.13), paw, scale=(0.9, 1.0, 1.05), segs=10,
                                            rings=6))
        rig.smooth(["root", "thigh." + side, "foot." + side],
                   limb([(0.085 * s, 0, 0.21), (0.09 * s, 0, 0.17), (0.095 * s, 0, 0.075)], [0.038, 0.037, 0.034],
                        dark, verts=8, per=2), power=6)
        rig.rigid("foot." + side, sphere(0.06, (0.095 * s, -0.028, 0.036), foot, scale=(0.85, 1.35, 0.6), segs=10,
                                         rings=6))
    # the lantern stick, strapped to the back, and the lantern hanging from its hook
    rig.smooth(["body", "stick"], limb([(0, 0.16, 0.28), (0, 0.29, 0.42), (0, 0.36, 0.6), (0, 0.375, 0.74),
                                        (0, 0.35, 0.79), (0, 0.335, 0.775)],
                                       [0.016, 0.016, 0.015, 0.014, 0.012, 0.01], stick_m, verts=6, per=2), power=6)
    rig.rigid("body", torus(0.2, 0.012, (0, 0.03, 0.33), stick_m, rot=(0.5, 0, 0), verts=14, minor=3,
                            scale=(1.02, 0.95, 1.0)))
    lx, ly = 0.0, TIP.y
    lan = [lathe_r([(0.0, 0.74), (0.022, 0.735), (0.05, 0.705), (0.046, 0.695), (0.0, 0.695)], brass, segs=8,
                   smooth=0),
           lathe_r([(0.0, 0.697), (0.036, 0.695), (0.044, 0.655), (0.036, 0.615), (0.0, 0.613)], glow, segs=8),
           lathe_r([(0.0, 0.617), (0.048, 0.615), (0.04, 0.598), (0.0, 0.596)], brass, segs=8, smooth=0),
           torus(0.014, 0.004, (0, 0, 0), brass, rot=(0, R90, 0), verts=8, minor=3)]
    lan[-1].location = (0, ly, 0.752)
    for o in lan[:3]:
        o.location = (lx, ly, 0)
    for k in range(4):
        a = math.pi / 4 + k * R90
        lan.append(rod((0.043 * math.cos(a), ly + 0.043 * math.sin(a), 0.698),
                       (0.04 * math.cos(a), ly + 0.04 * math.sin(a), 0.616), 0.005, brass, verts=4))
    rig.rigid("lantern", *lan)
    rig.build("mossling")

    # ---- bone-attached nodes: the leaf (always), the pick and the brick (hidden unless used)
    # leaf: a round cupped sprout leaf on a short stem (a peltate leaf: the stem meets the blade's centre)
    stem = limb([(0, 0, 0.56), (0, 0.004, 0.62), (0, 0.02, 0.68), (0, 0.03, 0.705)], [0.013, 0.012, 0.011, 0.01],
                leaf_m, verts=6, per=2)
    bm = bmesh.new()
    lc = Vector((0, 0.03, 0.71))
    N = 12
    cen = bm.verts.new(lc + Vector((0, 0, 0.012)))
    mid = []
    out = []
    for k in range(N):
        a = 2 * math.pi * k / N
        wob = 0.006 * (1 if k % 2 else -1)
        rr = 0.092 * (0.84 if k == N // 4 else 1.0)          # a small notch at the back
        mid.append(bm.verts.new(lc + Vector((0.052 * math.cos(a), 0.052 * math.sin(a), 0.004))))
        out.append(bm.verts.new(lc + Vector((rr * math.cos(a), rr * math.sin(a), -0.018 + wob))))
    for k in range(N):
        j = (k + 1) % N
        bm.faces.new((cen, mid[k], mid[j]))
        bm.faces.new((mid[k], out[k], out[j], mid[j]))
    blade = new_obj("blade", bm, leaf_m, smooth=60)
    solid(blade, 0.012)
    blade.data.materials.append(leaf_u)
    for p in blade.data.polygons:
        p.material_index = 1 if p.normal.z < -0.2 else 0
    # tilt the blade back a little, jauntily
    blade.data.transform(Matrix.Translation(lc) @ Matrix.Rotation(math.radians(14), 4, "X")
                         @ Matrix.Translation(-lc))
    vein = rod(lc + Vector((0, -0.005, 0.014)), lc + Vector((0, -0.085, -0.006)), 0.004, leaf_u, verts=4)
    rig.attach("leaf", [stem, blade, vein], "leaf", LEAF0)

    # pick: handle through the right paw, a two-pointed head in the swing plane (Y-Z)
    hx = -0.242
    handle = rod((hx, -0.012, 0.2), (hx, -0.012, -0.2), 0.013, pwood, verts=6)
    head = limb([(hx, -0.17, -0.175), (hx, -0.09, -0.205), (hx, -0.012, -0.215), (hx, 0.07, -0.205),
                 (hx, 0.13, -0.18)], [0.006, 0.02, 0.028, 0.02, 0.006], phead, verts=5, per=1, caps=True)
    band = cyl(0.02, 0.03, (hx, -0.012, -0.19), phead, verts=6)
    rig.attach("pick", [handle, head, band], "pick", (hx, -0.012, 0.13))
    # brick: held between both paws
    brick = box((0.36, 0.26, 0.085), (0, -0.07, 0.13), brick_m, bevel=0.012, segs=1)
    rig.attach("brick", [brick], "brick", (hx, -0.012, 0.13))
    attached = [o for o in bpy.data.objects if o.name in ("leaf", "pick", "brick")]

    # ---- actions (written facing -Y: +X tips the body forward, swings a hanging arm back; -X swings it forward)
    L = mirror

    def arms(l, r, lo=0.0, ro=0.0, lb=0.0, rb=0.0):
        """Arm swings about X (negative: forward/up), outward spread, forearm bends (negative: forward)."""
        return {"arm.L": (l, -lo, 0), "arm.R": (r, ro, 0), "forearm.L": (lb, 0, 0), "forearm.R": (rb, 0, 0)}

    def brows(front_down=0.0, lift=0.0):
        """Shows the brows: front_down > 0 tilts their front ends down (stern), < 0 up (worried)."""
        d, p = eyes["L"]
        # rotation about the eye's axis that lowers the front end of the left brow
        t = d.cross(Vector((0, 0, 1))).normalized()
        front = t if t.y < 0 else -t
        e = about(d, front_down)
        test = Matrix.Rotation(math.radians(front_down), 3, d) @ front
        if front_down and (test.z > front.z) == (front_down > 0):
            e = about(d, -front_down)
        return L({"brow.L": e, "%brow.L": 1.0, "@brow.L": (0, 0, lift)})

    def legs(l, r, lf=0.0, rf=0.0):
        return {"thigh.L": (l, 0, 0), "thigh.R": (r, 0, 0), "foot.L": (lf, 0, 0), "foot.R": (rf, 0, 0)}

    # walk: a lively waddle, two steps a second
    def step(ph, passing):
        if not passing:
            p = merge(legs(-30 * ph, 30 * ph, 18 * ph if ph > 0 else -5, -18 * ph if ph < 0 else -5),
                      arms(28 * ph, -28 * ph, 6, 6, -12, -12),
                      {"body": (4, 9 * ph, 0), "%body": (1.03, 1.03, 0.96), "@root": (0, 0, 0.0),
                       "leaf": (10, -6 * ph, 0), "lantern": (-10, 0, 8 * ph), "stick": (0, 0, 0)})
        else:
            sw = "R" if ph > 0 else "L"
            p = merge({"thigh." + sw: (-32, 0, 0), "foot." + sw: (-15, 0, 0)},
                      arms(0, 0, 10, 10, -18, -18),
                      {"body": (2, 0, 0), "%body": (0.97, 0.97, 1.04), "@root": (0, 0, 0.045),
                       "leaf": (-8, 0, 0), "lantern": (14, 0, 0), "stick": (-3, 0, 0)})
        return p
    rig.action("walk", {0: step(1, False), 8: step(1, True), 15: step(-1, False), 23: step(-1, True),
                        30: step(1, False)}, loop=True)

    # fall: arms up flailing (the near arm up-forward, the far one up-back), legs kicking, lantern flying up
    def flail(i):
        a = i * math.pi / 2
        return merge(arms(165 + 18 * math.sin(a), -160 - 18 * math.cos(a), 25, 25, -25 * math.cos(a), 25 * math.sin(a)),
                     legs(-25 * math.sin(a), 25 * math.sin(a), 20, 20),
                     {"%body": (0.95, 0.95, 1.07), "leaf": (-25 + 15 * math.cos(a), 10 * math.sin(a), 0),
                      "lantern": (150 + 20 * math.sin(a), 0, 0), "stick": (-6, 0, 0), "body": (-4, 0, 0)},
                     brows(-18, 0.012))
    rig.action("fall", {i * 3: flail(i) for i in range(5)}, loop=True)

    # float: the leaf grown into a parasol, held up with both paws; a gentle pendulum sway
    def drift(i):
        a = 2 * math.pi * i / 4
        return merge(arms(-172 + 4 * math.sin(a), -172 + 4 * math.sin(a), 8, 8, -10, -10),
                     legs(12 * math.sin(a + 1), -12 * math.sin(a + 1), 10, 10),
                     {"@leaf": (0, 0, 0.06), "%leaf": 2.8, "leaf": (-14 + 5 * math.sin(a), 0, 0),
                      "body": (5 * math.sin(a - 0.8), 0, 0), "@root": (0, 0, 0.02 * math.cos(a)),
                      "lantern": (-12 * math.sin(a - 1.5), 0, 0)})
    rig.action("float", {0: drift(0), 8: drift(1), 15: drift(2), 23: drift(3), 30: drift(0)}, loop=True)

    # climb: paws reaching up the wall in turns, knees pushing, the ball leaning into the wall
    def haul(ph):
        return merge(arms(-110 - 55 * ph, -110 + 55 * ph, 5, 5, -35 + 25 * ph, -35 - 25 * ph),
                     legs(-55 * max(0, -ph) - 20, -55 * max(0, ph) - 20, 30, 30),
                     {"body": (14, 0, 4 * ph), "@root": (0, 0.0, 0.025 * abs(ph)), "leaf": (-10, 0, 0),
                      "lantern": (-18, 0, 0)})
    rig.action("climb", {0: haul(1), 5: haul(0), 10: haul(-1), 15: haul(0), 20: haul(1)}, loop=True)

    # dig: bent over, scooping the ground away with both paws in turns
    def scoop(ph):
        return merge(arms(-68 + 50 * ph, -68 - 50 * ph, 12, 12, -30, -30),
                     legs(-25, -25, 25, 25),
                     {"body": (30, 0, 5 * ph), "@root": (0, 0, -0.015), "%body": (1.02, 1.02, 0.97),
                      "leaf": (18 + 8 * ph, 0, 0), "lantern": (-30 + 8 * ph, 0, 0), "stick": (-4, 0, 0)})
    rig.action("dig", {0: scoop(1), 4: scoop(0), 8: scoop(-1), 12: scoop(0), 16: scoop(1)}, loop=True)

    # bash: one-two punches straight ahead
    guard = {"arm.L": (-55, -8, 0), "forearm.L": (-70, 0, 0), "arm.R": (-55, 8, 0), "forearm.R": (-70, 0, 0)}

    def punch(side):
        o = "L" if side == "R" else "R"
        return merge({"arm." + side: (-104, 0, 0), "forearm." + side: (-4, 0, 0),
                      "arm." + o: (-40, 8 if o == "R" else -8, 0), "forearm." + o: (-80, 0, 0)},
                     legs(-20, 20, 10, -10) if side == "R" else legs(20, -20, -10, 10),
                     {"body": (14, 0, 8 if side == "R" else -8), "@root": (0, -0.035, 0),
                      "leaf": (-14, 0, 0), "lantern": (25, 0, 0)}, brows(14))

    def wind(side):
        return over(guard, {"arm." + side: (15, 0, 0), "forearm." + side: (-95, 0, 0), "body": (-4, 0, 0),
                             "leaf": (8, 0, 0), "lantern": (-10, 0, 0)}, brows(14))
    rig.action("bash", {0: wind("R"), 4: punch("R"), 7: punch("R"), 10: wind("L"), 14: punch("L"), 17: punch("L"),
                        20: wind("R")}, loop=True)

    # mine: the pick swung from over the head (behind) down-forward into the ground
    up = merge(arms(-195, -195, 8, 8, -25, -25), legs(-8, 10, 5, -5),
               {"body": (-10, 0, 0), "@root": (0, 0, 0.01), "%pick": 1.0, "leaf": (10, 0, 0), "lantern": (-12, 0, 0)},
               brows(10))
    hit = merge(arms(-84, -84, 8, 8, -5, -5), legs(-20, 15, 12, -8),
                {"body": (24, 0, 0), "@root": (0, 0, -0.02), "%pick": 1.0, "%body": (1.03, 1.03, 0.96),
                 "leaf": (-20, 0, 0), "lantern": (30, 0, 0)}, brows(10))
    rig.action("mine", {0: up, 6: over(up, arms(-150, -150, 8, 8, -10, -10), {"body": (6, 0, 0)}), 9: hit,
                        12: over(hit, {"@root": (0, 0, -0.012), "leaf": (-8, 0, 0)}),
                        17: over(up, arms(-120, -120, 8, 8, -20, -20), {"body": (5, 0, 0)}), 24: up}, loop=True)

    # build: brick at the chest, bend and lay it in front, fetch the next one from the back
    carry = merge(arms(-58, -58, 6, 6, -58, -58), {"%brick": 1.0, "body": (-4, 0, 0), "lantern": (-6, 0, 0)})
    lay = merge(arms(-92, -92, 6, 6, 35, 35), legs(-30, -30, 30, 30),
                {"%brick": 1.0, "body": (32, 0, 0), "@root": (0, 0, -0.03), "leaf": (15, 0, 0), "lantern": (-30, 0, 0)})
    rig.action("build", {0: carry, 9: lay, 14: lay, 15: over(lay, {"%brick": 0.0}),
                         20: merge(arms(-20, 30, 6, 10, -20, -60), {"%brick": 0.0, "body": (0, 0, 0)}),
                         26: merge(arms(-40, 45, 6, 15, -40, -80), {"%brick": 0.0, "body": (-6, 0, 0)}),
                         27: over(carry, {"%brick": 1.0}), 30: carry}, loop=True)

    # block: arms flung out front and back, stern brows, a tapping foot
    def stand(i):
        a = 2 * math.pi * i / 4
        tap = -18 if i in (1,) else 0
        return merge(arms(92, -92, 20, 20, -18, -18), legs(0, tap, 0, -tap * 0.6),
                     {"%body": (1 + 0.02 * math.sin(a), 1 + 0.02 * math.sin(a), 1 - 0.02 * math.sin(a)),
                      "leaf": (3 * math.sin(a), 0, 0), "body": (-3, 0, 0)}, brows(20))
    rig.action("block", {0: stand(0), 8: stand(1), 15: stand(2), 23: stand(3), 30: stand(0)}, loop=True)

    # shrug: palms up, shoulders up, head tipped - "no more bricks"
    shrug = merge(arms(-38, -38, 55, 55, -75, -75), {"@body": (0, 0, 0.025), "%body": (0.97, 0.97, 1.04),
                                                     "body": (-8, 0, 0), "leaf": (-10, 0, 0), "lantern": (8, 0, 0)},
                  brows(-10, 0.02))
    rig.action("shrug", {0: {}, 7: shrug, 12: over(shrug, {"body": (-6, 12, 0)}), 20: over(shrug, {"body": (-6, 12, 0)}),
                         30: {}})

    # panic: paws clutching the head, shaking, hopping from foot to foot
    def fret(j):
        return merge(arms(-165, -165, -5, -5, -40, -40), legs(-25 if j > 0 else 0, -25 if j < 0 else 0, 15, 15),
                     {"body": (0, 0, 14 * j), "@root": (0.012 * j, 0.0, 0.02), "%body": (1.02, 1.02, 0.98),
                      "leaf": (10, 25 * j, 0), "lantern": (0, 0, 30 * j)}, brows(-22, 0.012))
    rig.action("panic", {0: fret(1), 3: fret(-1), 6: fret(1), 9: fret(-1), 12: fret(1)}, loop=True)

    # splat: flattened like a pancake (the feet stay on the ground)
    flat = merge(arms(0, 0, 80, 80), legs(-40, 40, 0, 0), {"leaf": (70, 0, 0), "lantern": (80, 0, 0)})
    rig.action("splat", {0: {"%root": (0.85, 0.85, 1.2)},
                         3: merge(flat, {"%root": (1.7, 1.7, 0.18)}),
                         7: merge(flat, {"%root": (1.4, 1.4, 0.34)}),
                         11: merge(flat, {"%root": (1.66, 1.66, 0.19)}),
                         24: merge(flat, {"%root": (1.62, 1.62, 0.2)})})

    # exit: squat, a happy hop with both arms up, land and wave
    crouch = merge(legs(-35, -35, 35, 35), arms(20, 20, 10, 10, -20, -20),
                   {"@root": (0, 0, -0.02), "%body": (1.08, 1.08, 0.88), "body": (6, 0, 0)})
    wave = lambda k: merge(arms(10, -160 + 22 * k, 10, 20, -10, -30 * k), {"body": (-6, 0, 0), "leaf": (-6 * k, 0, 0)})
    rig.action("exit", {0: {}, 5: crouch,
                        10: merge(arms(-165, -165, 20, 20), legs(-40, -40, 30, 30),
                                  {"@root": (0, 0, 0.24), "%body": (0.94, 0.94, 1.08), "leaf": (-25, 0, 0),
                                   "lantern": (40, 0, 0)}),
                        14: merge(arms(-160, -160, 25, 25), legs(-20, -20, 10, 10), {"@root": (0, 0, 0.26)}),
                        19: over(crouch, arms(-150, -150, 20, 20), {"@root": (0, 0, -0.01)}),
                        22: wave(1), 25: wave(-1), 28: wave(1), 30: wave(0)})

    # drown: arms up, bobbing, sinking out of sight
    def sink(z, j):
        return merge(arms(-160 + 20 * j, -160 - 20 * j, 20, 20, -20 * j, 20 * j), legs(-30 * j, 30 * j, 10, 10),
                     {"@root": (0, 0, z), "body": (8 * j, 0, 0), "leaf": (-20, 15 * j, 0), "lantern": (60, 0, 0)},
                     brows(-22, 0.012))
    rig.action("drown", {0: {}, 5: sink(-0.12, 1), 12: sink(-0.2, -1), 19: sink(-0.34, 1), 26: sink(-0.5, -1),
                         34: sink(-0.75, 1), 45: sink(-1.1, -1)})

    for t in rig.arm.animation_data.nla_tracks:   # back to the rest pose (the NLA stack would pose it), so the
        t.mute = True                               # attached nodes export at their rest places
    for b in rig.arm.pose.bones:
        b.location = (0, 0, 0)
        b.rotation_euler = (0, 0, 0)
        b.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    K.deselect()
    for o in [rig.arm, rig.mesh] + attached:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig.arm
    bpy.context.scene.frame_start = 0
    bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, "mossling.glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_frame_step=1)
    print("exported mossling  %5d tris (+ %s)  anims: %s" % (
        K.tris(rig.mesh), ", ".join("%s %d" % (o.name, K.tris(o)) for o in attached),
        ", ".join("%s %.2fs" % (k, v) for k, v in rig.lengths.items())))
    reset()



# ------------------------------------------------------------------ shared prop helpers

def disc_xy(poly, z0, z1, material, name="disc", smooth=0):
    """A 2D outline in XY extruded from z0 to z1."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in poly]
    hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return new_obj(name, bm, material, smooth=smooth)


def arch(r, cz, n=12, bottom=0.0):
    """Outline (x, z) of a round-topped doorway: a half circle of radius r centred at height cz, straight sides
    down to `bottom`; counter-clockwise seen from -Y."""
    pts = [(r, bottom)]
    for k in range(n + 1):
        a = math.pi * k / n
        pts.append((r * math.cos(a), cz + r * math.sin(a)))
    pts.append((-r, bottom))
    return pts


def mushroom(base, h, cap_r, cap_m, stem_m, gill_m=None, lean=(0, 0), segs=10, spots=None, seed=0):
    """A mushroom: a lathed stem leaning by `lean` (dx, dy at the top) and a domed cap; spots on the cap."""
    bx, by, bz = base
    tx, ty = bx + lean[0], by + lean[1]
    parts = [limb([(bx, by, bz - 0.02), (bx + lean[0] * 0.3, by + lean[1] * 0.3, bz + h * 0.4),
                   (tx, ty, bz + h * 0.95)], [cap_r * 0.28, cap_r * 0.22, cap_r * 0.2], stem_m, verts=segs, per=2)]
    top = bz + h
    prof = [(0.0, top + cap_r * 0.55), (cap_r * 0.45, top + cap_r * 0.5), (cap_r * 0.8, top + cap_r * 0.3),
            (cap_r, top + cap_r * 0.02), (cap_r * 0.96, top - cap_r * 0.08)]
    cap = lathe_r(prof, cap_m, segs=segs + 4, smooth=50)
    under = lathe_r([(cap_r * 0.96, top - cap_r * 0.08), (cap_r * 0.6, top - cap_r * 0.02),
                     (cap_r * 0.2, top + cap_r * 0.02), (0.0, top + cap_r * 0.03)], gill_m or stem_m, segs=segs + 4,
                    smooth=50)
    for o in (cap, under):
        o.data.transform(Matrix.Translation((tx, ty, 0)))
    parts += [cap, under]
    if spots:
        rnd = random.Random(seed)
        for k in range(5):
            a = 2 * math.pi * k / 5 + rnd.uniform(-0.3, 0.3)
            el = rnd.uniform(0.35, 0.75)
            d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el) * 0.55)).normalized()
            p = Vector((tx, ty, top)) + Vector((d.x * cap_r * 0.9, d.y * cap_r * 0.9, d.z * cap_r * 0.95))
            parts.append(blob(cap_r * 0.13, p, spots, (1, 0.35, 1), d, segs=5, rings=3))
    return parts


# ------------------------------------------------------------------ hatch (entrance)

def hatch():
    rock = mat("hatch_rock", (0.23, 0.21, 0.26), 0.92)
    rock_l = mat("hatch_rock_light", (0.32, 0.29, 0.33), 0.9)
    moss_m = mat("hatch_moss", (0.3, 0.54, 0.18), 0.9)
    bark = mat("hatch_bark", (0.36, 0.23, 0.13), 0.9)
    bark_d = mat("hatch_bark_dark", (0.2, 0.12, 0.07), 0.9)
    cut = mat("hatch_wood_cut", (0.8, 0.62, 0.4), 0.8)
    inside = mat("hatch_inside", (0.05, 0.03, 0.02), 1.0)
    inside.use_backface_culling = False
    door_m = mat("hatch_door", (0.66, 0.43, 0.22), 0.8)
    iron = mat("hatch_iron", (0.22, 0.22, 0.25), 0.45, 0.8)
    glow = mat("hatch_glow", (1.0, 0.72, 0.32), 0.5, emit=5.0, emit_color=(1.0, 0.6, 0.2))
    sglow = mat("hatch_mushroom_glow", (0.45, 0.95, 1.0), 0.4, emit=3.0, emit_color=(0.3, 0.9, 1.0))
    stem_m = mat("hatch_mushroom_stem", (0.85, 0.85, 0.78), 0.7)
    parts = []
    # the stump: ridged bark from the opening up into the rock, a cut-wood lip, the dark hollow
    parts.append(lathe_r([(0.5, 1.6), (0.53, 1.1), (0.56, 0.6), (0.6, 0.25), (0.66, 0.08), (0.66, 0.03)], bark,
                         segs=20, radial=lambda k, z: 1.0 + (0.05 if k % 2 else -0.02) * min(1.0, 1.4 - z * 0.5),
                         smooth=25))
    parts.append(lathe_r([(0.66, 0.035), (0.63, 0.0), (0.52, 0.0), (0.49, 0.035)], cut, segs=20, smooth=40))
    parts.append(lathe_r([(0.49, 0.035), (0.49, 1.2), (0.0, 1.2)], inside, segs=20, smooth=40))
    # growth rings on the lip: one dark ring
    parts.append(torus(0.575, 0.012, (0, 0, 0.004), bark_d, verts=20, minor=3))
    # the rock mass it hangs from
    # one rock mass round the stump's top (the stump stands in front of it), lumps for a broken outline
    parts.append(lumpy(1.0, (0, 0.3, 1.42), rock, 200, amount=0.1, scale=(1.5, 0.62, 0.82), sub=2))
    for k, (x, y, z, r, sx, sz) in enumerate(((-1.05, 0.0, 0.95, 0.45, 1.1, 0.75), (1.1, 0.02, 1.0, 0.42, 1.1, 0.75),
                                              (-0.55, -0.05, 2.0, 0.42, 1.3, 0.6), (0.55, 0.0, 2.02, 0.44, 1.3, 0.6),
                                              (0.0, -0.02, 2.2, 0.36, 1.2, 0.5), (-1.45, 0.1, 1.45, 0.3, 1.0, 0.9),
                                              (1.47, 0.1, 1.5, 0.3, 1.0, 0.9))):
        parts.append(lumpy(r, (x, y, z), rock_l if k % 2 else rock, 201 + k, amount=0.14, scale=(sx, 0.8, sz), sub=2))
    for k, (x, z, r) in enumerate(((-0.55, 2.2, 0.4), (0.55, 2.22, 0.42), (0.0, 2.36, 0.32), (-1.15, 1.25, 0.28),
                                   (1.2, 1.3, 0.26))):
        parts.append(lumpy(r, (x, -0.05, z), moss_m, 220 + k, amount=0.2, scale=(1.3, 0.8, 0.3), sub=1))
    # moss drips and a few roots hanging off the rock
    rnd = random.Random(7)
    for k, (x, z) in enumerate(((-1.4, 0.75), (-0.85, 0.62), (0.85, 0.66), (1.4, 0.8), (-1.15, 0.7))):
        ln = rnd.uniform(0.25, 0.5)
        parts.append(limb([(x, -0.3, z + 0.1), (x + 0.03, -0.33, z - ln * 0.5), (x - 0.02, -0.35, z - ln)],
                          [0.03, 0.022, 0.01], moss_m if k % 2 else bark_d, verts=5, per=2, caps=True))
    # a glowing round window in the stump's front
    wc = Vector((0, -0.6, 0.62))
    parts += [cyl(0.13, 0.04, wc, glow, rot=(R90, 0, 0), verts=14),
              torus(0.14, 0.03, wc + Vector((0, -0.02, 0)), bark_d, rot=(R90, 0, 0), verts=14, minor=4),
              box((0.02, 0.02, 0.26), wc + Vector((0, -0.03, 0)), bark_d, bevel=0.0),
              box((0.26, 0.02, 0.02), wc + Vector((0, -0.03, 0)), bark_d, bevel=0.0)]
    # glowing mushrooms on the left ledge
    for (x, z, h, r) in ((-1.2, 1.28, 0.2, 0.09), (-1.05, 1.3, 0.13, 0.06), (-1.35, 1.25, 0.1, 0.05)):
        parts += mushroom((x, -0.3, z), h, r, sglow, stem_m, segs=6)
    root = join(parts, "hatch")
    # the trapdoors: two half discs under the lip, hinged front (y = -0.52) and back (y = +0.52); the front one
    # drops towards the camera and hangs facing it
    doors = []
    for s_, name in ((-1, "door_front"), (1, "door_back")):
        pts = [(-0.52 * math.cos(math.pi * k / 12), s_ * 0.52 * math.sin(math.pi * k / 12)) for k in range(13)]
        if s_ > 0:
            pts = pts[::-1]
        d = disc_xy(pts, -0.07, 0.0, door_m)
        d.data.transform(Matrix.Translation((0, -s_ * 0.005, 0)))
        bands = [box((0.06, 0.42, 0.02), (x, s_ * 0.24, -0.075), iron, bevel=0.005, segs=1) for x in (-0.26, 0.26)]
        ring = torus(0.05, 0.012, (0, s_ * 0.14, -0.085), iron, rot=(0, 0, R90), verts=10, minor=3)
        hinge = cyl(0.03, 1.0, (0, s_ * 0.52, -0.035), iron, rot=(0, R90, 0), verts=8)
        groove = [box((0.9, 0.012, 0.012), (0, s_ * y, -0.074), bark_d, bevel=0.0) for y in (0.17, 0.34)]
        o = join([d, ring, hinge] + bands + groove, name, pivot=(0, s_ * 0.52, -0.035))
        ang = s_ * R90   # both swing down: the front one about -X (towards the camera), the back one about +X
        animate(o, "open", {0: {}, 6: {"rot": (ang * 0.04, 0, 0)}, 8: {"rot": (-ang * 0.02, 0, 0)},
                            10: {"rot": (ang * 0.05, 0, 0)}, 13: {"rot": (0, 0, 0)},
                            23: {"rot": (ang * 1.12, 0, 0)}, 29: {"rot": (ang * 0.9, 0, 0)},
                            35: {"rot": (ang * 1.05, 0, 0)}, 40: {"rot": (ang * 0.98, 0, 0)},
                            45: {"rot": (ang * 1.0, 0, 0)}}, linear=False)
        doors.append(o)
    export_anim(root, "hatch", [(d, root) for d in doors])


# ------------------------------------------------------------------ burrow (exit)

def burrow():
    earth = mat("burrow_earth", (0.36, 0.25, 0.15), 0.95)
    moss_m = mat("burrow_moss", (0.32, 0.56, 0.2), 0.9)
    moss_d = mat("burrow_moss_dark", (0.2, 0.4, 0.14), 0.9)
    tunnel = mat("burrow_tunnel", (0.22, 0.13, 0.07), 1.0)
    stone = mat("burrow_stone", (0.55, 0.52, 0.48), 0.9)
    wood = mat("burrow_door", (0.3, 0.52, 0.28), 0.6)      # a green-painted round door
    wood_d = mat("burrow_wood", (0.4, 0.25, 0.13), 0.8)
    brass = mat("burrow_brass", (0.9, 0.68, 0.3), 0.3, 0.9)
    metal = mat("burrow_metal", (0.2, 0.2, 0.22), 0.5, 0.7)
    glow = mat("burrow_glow", (1.0, 0.66, 0.3), 0.5, emit=3.5, emit_color=(1.0, 0.55, 0.2))
    wglow = mat("burrow_window_glow", (1.0, 0.8, 0.45), 0.5, emit=4.0, emit_color=(1.0, 0.62, 0.25))
    lglow = mat("burrow_lantern_glow", (1.0, 0.85, 0.5), 0.4, emit=9.0, emit_color=(1.0, 0.65, 0.25))
    cap_m = mat("burrow_mushroom_cap", (0.85, 0.3, 0.15), 0.6)
    stem_m = mat("burrow_mushroom_stem", (0.92, 0.88, 0.8), 0.7)
    spot = mat("burrow_mushroom_spot", (1.0, 0.97, 0.9), 0.6)
    parts = []
    # the mound: a squashed dome, mossy on top, earthy on the sides; the doorway cut through it
    MC = Vector((0, 1.25, -0.05))
    mound = painted_ball(1.0, MC, (1.55, 1.05, 2.5), [earth, moss_m, moss_d],
                         lambda n: 1 if n.z > 0.32 + 0.08 * math.sin(n.x * 9) else (2 if n.z > 0.18 else 0),
                         segs=32, rings=20, name="mound")
    bm = bmesh.new()
    bm.from_mesh(mound.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, -0.08),
                           plane_no=(0, 0, 1), clear_inner=True)
    for v in bm.verts:   # a gentle lumpy surface
        v.co += Vector((0, 0, 0)) + (v.co - MC).normalized() * 0.035 * math.sin(v.co.x * 5.1 + v.co.z * 3.7)
    bm.to_mesh(mound.data)
    bm.free()
    cutter = prism(arch(0.6, 0.66, n=14, bottom=-0.2), 1.6, (0, 0.8, 0), tunnel, rot=(0, 0, 0), bevel=0.0)
    K.select(mound)
    mound.data.materials.append(tunnel)
    bo = mound.modifiers.new("cut", "BOOLEAN")
    bo.operation = "DIFFERENCE"
    bo.object = cutter
    bo.solver = "EXACT"
    bo.material_mode = "TRANSFER"
    bpy.ops.object.modifier_apply(modifier=bo.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    K.select(mound)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    parts.append(mound)
    # warm light at the end of the tunnel and a floor
    parts.append(prism(arch(0.6, 0.66, n=14, bottom=0.0), 0.04, (0, 1.55, 0), glow, bevel=0.0))
    parts.append(box((1.18, 1.5, 0.04), (0, 0.85, -0.02), tunnel, bevel=0.0))
    # stone frame round the doorway and a threshold slab
    n = 11
    for k in range(n):
        a = math.pi * k / (n - 1)
        p = Vector((0.74 * math.cos(a), 0.2, 0.66 + 0.74 * math.sin(a)))
        parts.append(lumpy(0.15, p, stone, 300 + k, amount=0.12, scale=(1.0, 0.7, 0.85), sub=2, smooth=60))
    for k, z in enumerate((0.1, 0.36)):
        for s in (-1, 1):
            parts.append(lumpy(0.14, (s * 0.76, 0.2, z), stone, 320 + k * 2 + (s > 0), amount=0.12,
                               scale=(0.9, 0.7, 0.95), sub=2, smooth=60))
    parts.append(box((1.45, 0.4, 0.06), (0, 0.12, 0.0), stone, bevel=0.02, segs=1))
    # the round green door, open inwards against the tunnel's left wall
    door = prism(arch(0.56, 0.64, n=14, bottom=0.03), 0.07, (0, 0, 0), wood, bevel=0.015, segs=1)
    door_parts = [door, sphere(0.06, (0, -0.05, 0.64), brass, segs=10, rings=6)]
    for x in (-0.28, 0.0, 0.28):
        door_parts.append(box((0.015, 0.02, 1.0 if x == 0 else 0.85), (x, -0.036, 0.62 if x == 0 else 0.55),
                              wood_d, bevel=0.0))
    for z in (0.28, 0.95):
        door_parts.append(box((0.62, 0.02, 0.05), (-0.22, -0.04, z), metal, bevel=0.0))
    dd = join(door_parts, "door_tmp", pivot=(-0.56, 0, 0))
    dd.rotation_euler = (0, 0, math.radians(62))
    dd.location = (-0.58, 0.32, 0)
    parts.append(dd)
    # the round window up to the left, the lantern bracket to the right of the doorway
    wc = Vector((-0.98, 0.52, 1.42))
    parts += [cyl(0.2, 0.12, wc, wglow, rot=(R90 - 0.25, 0, 0.35), verts=16),
              torus(0.21, 0.04, wc + Vector((0, -0.05, 0)), wood_d, rot=(R90 - 0.25, 0, 0.35), verts=16, minor=5)]
    for rot in (0.0, R90):
        b = box((0.4, 0.02, 0.025), wc + Vector((0, -0.07, 0)), wood_d, bevel=0.0)
        b.data.transform(Matrix.Translation(wc) @ Matrix.Rotation(0.35, 4, "Z") @
                         Matrix.Rotation(R90 - 0.25 - R90, 4, "X") @ Matrix.Rotation(rot, 4, "Y") @
                         Matrix.Translation(-wc))
        parts.append(b)
    lc = Vector((1.0, 0.14, 1.12))
    parts += [rod((1.0, 0.55, 1.5), (1.0, 0.12, 1.5), 0.025, metal, verts=6),
              rod((1.0, 0.12, 1.5), (1.0, 0.12, 1.42), 0.012, metal, verts=4),
              lathe_r([(0.0, 1.27), (0.05, 1.26), (0.11, 1.21), (0.1, 1.19), (0.0, 1.19)], metal, segs=8, smooth=0),
              lathe_r([(0.0, 1.05), (0.1, 1.05), (0.085, 1.0), (0.0, 0.99)], metal, segs=8, smooth=0),
              torus(0.03, 0.008, (1.0, 0.14, 1.4), metal, rot=(0, R90, 0), verts=8, minor=3)]
    for o in parts[-3:-1]:
        o.data.transform(Matrix.Translation((lc.x, lc.y, 0)))
    parts.append(rod((1.0, 0.14, 1.28), (1.0, 0.14, 1.36), 0.01, metal, verts=4))
    parts.append(lathe_r([(0.0, 1.19), (0.075, 1.18), (0.085, 1.12), (0.075, 1.06), (0.0, 1.05)], lglow, segs=8))
    parts[-1].data.transform(Matrix.Translation((lc.x, lc.y, 0)))
    for k in range(4):
        a = math.pi / 4 + k * R90
        parts.append(rod((lc.x + 0.095 * math.cos(a), lc.y + 0.095 * math.sin(a), 1.2),
                         (lc.x + 0.09 * math.cos(a), lc.y + 0.09 * math.sin(a), 1.05), 0.01, metal, verts=4))
    # chimney pipe, a sprout on top, mushrooms and moss clumps
    parts += [cyl(0.13, 0.5, (0.62, 1.1, 2.3), stone, verts=10, bevel=0.02, segs=1),
              cyl(0.16, 0.08, (0.62, 1.1, 2.56), stone, verts=10, bevel=0.02, segs=1),
              cyl(0.1, 0.05, (0.62, 1.1, 2.58), tunnel, verts=10)]
    parts.append(limb([(-0.3, 1.25, 2.38), (-0.32, 1.2, 2.55), (-0.28, 1.15, 2.7)], [0.03, 0.025, 0.02], moss_m,
                      verts=6, per=2))
    for rot, sc in ((0.6, 1.0), (-2.4, 0.8)):
        lf = sphere(0.14, (0, 0, 0), moss_m, scale=(1.0, 0.5, 0.12), segs=10, rings=6)
        lf.data.transform(Matrix.Translation((-0.28, 1.15, 2.7)) @ Matrix.Rotation(rot, 4, "Z") @
                          Matrix.Rotation(-0.35, 4, "Y") @ Matrix.Translation((0.13, 0, 0)) @
                          Matrix.Diagonal((sc, sc, sc, 1)))
        parts.append(lf)
    parts += mushroom((1.25, 0.35, 0.0), 0.32, 0.17, cap_m, stem_m, spots=spot, seed=3, lean=(0.05, 0))
    parts += mushroom((1.45, 0.4, 0.0), 0.2, 0.11, cap_m, stem_m, spots=spot, seed=4, lean=(0.04, 0))
    parts += mushroom((-1.35, 0.4, 0.0), 0.24, 0.13, cap_m, stem_m, spots=spot, seed=5, lean=(-0.05, 0))
    for k, (x, z) in enumerate(((-1.2, 0.05), (1.05, 0.05), (-0.95, 0.06))):
        parts.append(lumpy(0.16, (x, 0.35, z), moss_d, 340 + k, amount=0.2, scale=(1.3, 0.8, 0.6), sub=1))
    root = join(parts, "burrow")
    # the lantern's flame: its own node, flickering
    flame = ico(0.05, (0, 0, 0), lglow, scale=(1, 1, 1.4), sub=2)
    flame.location = (lc.x, lc.y, 1.12)
    fl = {}
    rnd = random.Random(11)
    for f in range(0, 61, 6):
        s_ = 1.0 if f in (0, 60) else rnd.uniform(0.8, 1.12)
        fl[f] = {"scale": (s_, s_, s_ * rnd.uniform(0.95, 1.1) if f not in (0, 60) else 1.0)}
    animate(flame, "glow", fl, linear=False)
    flame.name = "flame"
    flame.data.name = "flame"
    export_anim(root, "burrow", [(flame, root)])

# ------------------------------------------------------------------ traps

def trap_snapper():
    reset()
    stem_m = mat("trap_snapper_stem", (0.22, 0.44, 0.16), 0.7)
    lobe = mat("trap_snapper_lobe", (0.4, 0.66, 0.2), 0.5, coat=0.3)
    inner = mat("trap_snapper_mouth", (0.9, 0.2, 0.28), 0.5, emit=0.5, emit_color=(0.9, 0.1, 0.25))
    tooth = mat("trap_snapper_tooth", (0.96, 0.93, 0.78), 0.5)
    leaf_m = mat("trap_snapper_leaf", (0.18, 0.38, 0.13), 0.8)
    spot = mat("trap_snapper_spot", (0.72, 0.16, 0.2), 0.6)
    H = Vector((0.1, 0, 0.94))    # the jaw hinge
    B = {"root": ((0, 0, 0), (0, 0, 0.1), None),
         "s1": ((0, 0, 0.02), (-0.05, 0, 0.36), "root"),
         "s2": ((-0.05, 0, 0.36), (-0.03, 0, 0.64), "s1"),
         "s3": ((-0.03, 0, 0.64), tuple(H), "s2"),
         "head": (tuple(H), tuple(H + Vector((0.2, 0, 0.02))), "s3"),
         "jaw_top": (tuple(H), tuple(H + Vector((0.4, 0, 0.0))), "head"),
         "jaw_bot": (tuple(H), tuple(H + Vector((0.4, 0, -0.001))), "head")}
    rig = Rig(B)
    rig.smooth(["s1", "s2", "s3"], limb([(0, 0, -0.02), (-0.05, 0, 0.3), (-0.04, 0, 0.6), (0.03, 0, 0.84),
                                          tuple(H)], [0.07, 0.06, 0.052, 0.048, 0.045], stem_m, verts=8, per=2))
    rig.rigid("head", sphere(0.075, H + Vector((-0.02, 0, 0)), stem_m, segs=10, rings=6))
    # basal leaves
    for k, a in enumerate((0.3, 2.2, 3.6, 5.2)):
        lf = sphere(0.2, (0, 0, 0), leaf_m, scale=(1.0, 0.36, 0.06), segs=10, rings=5)
        lf.data.transform(Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(-0.35, 4, "Y") @
                          Matrix.Translation((0.17, 0, 0.0)))
        lf.data.transform(Matrix.Translation((0, 0, 0.04)))
        rig.rigid("root", lf)
    # the jaws: the two halves of a pod split along the hinge line, pink inside, teeth round the rim
    from nightbite_characters import shell_half
    c = H + Vector((0.2, 0, 0))
    rx, ry, rz = 0.22, 0.17, 0.12
    for upper, bone in ((True, "jaw_top"), (False, "jaw_bot")):
        half = shell_half(c, 1.0, (rx, ry, rz), H.z, upper, lobe, inner, segs=18, rings=10)
        K.select(half)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
        rig.rigid(bone, half)
        sg = -1 if upper else 1
        for k in range(7):
            a = math.radians(-105 + 210 * k / 6)
            for side in (1, -1) if abs(k - 3) < 3 else (1,):
                p = c + Vector((rx * math.cos(a), side * ry * math.sin(a), 0)) * 0.98
                if side < 0 and k in (0, 6):
                    continue
                base = Vector((p.x, p.y if k != 3 else 0.0, H.z - sg * 0.005))
                rig.rigid(bone, rod(base, base + Vector((math.cos(a) * 0.012, 0, sg * 0.065)), 0.019, tooth, r2=0.0,
                                    verts=5))
        for (dx, dy) in ((0.08, -0.1), (0.17, -0.06), (0.0, -0.14)):
            d = Vector((dx, dy, -sg * 0.06)).normalized()
            p = c + Vector((dx, dy, -sg * rz * 0.6))
            rig.rigid(bone, blob(0.03, (p.x, dy * 1.05 - 0.02, H.z - sg * 0.07), spot, (1, 0.3, 1),
                                 (0, -1, -sg * 0.5), segs=6, rings=4))
    rig.build("trap_snapper")

    def jaws(o):
        return {"jaw_top": (0, -o, 0), "jaw_bot": (0, o, 0)}

    idle = {}
    for i in range(5):
        a = 2 * math.pi * i / 4
        idle[i * 15] = merge(jaws(34 + 5 * math.sin(a)),
                             {"s1": (0, 3 * math.sin(a), 0), "s2": (0, -4 * math.sin(a + 1), 0),
                              "s3": (0, 5 * math.sin(a + 2), 0), "head": (0, -6 * math.sin(a), 0),
                              "%s2": (1.0, 1.0, 1.0)})
    rig.action("idle", idle, loop=True)
    lunge = {"s1": (0, 20, 0), "s2": (0, 32, 0), "s3": (0, 36, 0), "head": (0, 26, 0)}
    rig.action("snap", {0: idle[0],
                        5: merge(jaws(52), {"s1": (0, -8, 0), "s2": (0, -14, 0), "s3": (0, -18, 0),
                                            "head": (0, -15, 0)}),
                        9: merge(jaws(58), lunge),
                        11: merge(jaws(-2), lunge),
                        15: merge(jaws(0), {"s1": (0, 8, 0), "s2": (0, 12, 0), "s3": (0, 12, 0), "head": (0, 4, 0)}),
                        19: merge(jaws(7), {"head": (0, -6, 0)}),
                        21: merge(jaws(0), {"head": (0, -3, 0)}),
                        23: merge(jaws(7), {"head": (0, -6, 0)}),
                        26: merge(jaws(0), {"%s2": (1.25, 1.25, 1.0), "%s3": (0.9, 0.9, 1.0)}),
                        30: idle[0]})
    rig.export("trap_snapper")


def trap_crusher():
    rock = mat("trap_crusher_rock", (0.23, 0.21, 0.26), 0.92)
    rock_l = mat("trap_crusher_rock_light", (0.32, 0.29, 0.33), 0.9)
    moss_m = mat("trap_crusher_moss", (0.3, 0.52, 0.18), 0.9)
    iron = mat("trap_crusher_iron", (0.24, 0.24, 0.27), 0.45, 0.8)
    stone = mat("trap_crusher_stone", (0.52, 0.48, 0.44), 0.85)
    stone_d = mat("trap_crusher_stone_dark", (0.34, 0.31, 0.29), 0.9)
    rune = mat("trap_crusher_glow", (1.0, 0.4, 0.15), 0.5, emit=4.0, emit_color=(1.0, 0.3, 0.1))
    wood = mat("trap_crusher_wood", (0.4, 0.26, 0.14), 0.85)
    # the housing: a rock block in the ceiling with a timber frame and two pulleys
    parts = [box((1.1, 0.8, 1.3), (0, 0.05, 2.72), rock, bevel=0.1, segs=2)]
    for k, (x, y, z, r) in enumerate(((-0.6, -0.12, 2.3, 0.3), (0.62, -0.1, 2.34, 0.3), (0.0, -0.18, 3.1, 0.4),
                                      (-0.58, -0.08, 3.05, 0.34), (0.6, -0.05, 3.1, 0.32), (-0.2, -0.2, 2.62, 0.26),
                                      (0.3, -0.2, 2.75, 0.24))):
        parts.append(lumpy(r, (x, y, z), rock_l if k % 2 else rock, 400 + k, amount=0.14, scale=(1.2, 0.8, 0.75),
                           sub=2))
    parts.append(lumpy(0.3, (-0.6, -0.2, 2.62), moss_m, 410, amount=0.2, scale=(1.1, 0.6, 0.35)))
    parts += [box((1.36, 0.14, 0.14), (0, -0.4, 2.06), wood, bevel=0.02, segs=1),
              box((0.14, 0.14, 0.7), (-0.62, -0.4, 2.4), wood, bevel=0.02, segs=1),
              box((0.14, 0.14, 0.7), (0.62, -0.4, 2.4), wood, bevel=0.02, segs=1)]
    for x in (-0.3, 0.3):
        parts += [cyl(0.1, 0.06, (x, -0.43, 2.2), iron, rot=(R90, 0, 0), verts=12),
                  cyl(0.03, 0.08, (x, -0.43, 2.2), wood, rot=(R90, 0, 0), verts=8)]
    for x in (-0.62, 0.62):
        parts.append(cyl(0.035, 0.03, (x, -0.48, 2.06), iron, rot=(R90, 0, 0), verts=6))
    root = join(parts, "trap_crusher")
    # the stone: a heavy block with iron bands, a glowing rune, spikes underneath; chains up into the housing
    Z0 = 1.25
    sp = [box((0.9, 0.62, 0.62), (0, 0, Z0 + 0.1 + 0.31), stone, bevel=0.06, segs=2),
          box((0.96, 0.66, 0.08), (0, 0, Z0 + 0.2), iron, bevel=0.015, segs=1),
          box((0.96, 0.66, 0.08), (0, 0, Z0 + 0.62), iron, bevel=0.015, segs=1),
          box((0.7, 0.5, 0.1), (0, 0, Z0 + 0.77), stone_d, bevel=0.03, segs=1)]
    for x in (-0.44, 0.44):
        for z in (0.2, 0.62):
            sp.append(ico(0.022, (x, -0.33, Z0 + z), iron, sub=1))
    # rune: a glowing eye-like mark on the front
    sp += [prism([(-0.14, 0), (0, 0.09), (0.14, 0), (0, -0.09)], 0.02, (0, -0.315, Z0 + 0.41), rune, bevel=0.0),
           cyl(0.035, 0.02, (0, -0.325, Z0 + 0.41), stone_d, rot=(R90, 0, 0), verts=8)]
    for i in range(5):
        for y in (-0.16, 0.16):
            x = -0.34 + 0.17 * i
            sp.append(cyl(0.06, 0.1, (x, y, Z0 + 0.05), iron, r2=0.0, rot=(math.pi, 0, 0), verts=6))
    for x in (-0.3, 0.3):
        sp.append(torus(0.05, 0.015, (x, 0, Z0 + 0.84), iron, rot=(R90, 0, 0), verts=8, minor=3))
        z = Z0 + 0.9
        k = 0
        while z < 3.35:
            sp.append(torus(0.04, 0.011, (x, 0.0, z), iron, rot=(R90, 0, 0) if k % 2 == 0 else (R90, 0, R90),
                            verts=6, minor=3))
            z += 0.065
            k += 1
    stone_o = join(sp, "stone", pivot=(0, 0, Z0))
    animate(stone_o, "crush", {0: {}, 4: {"loc": (0, 0, 0.06)}, 6: {"loc": (0.01, 0, 0.03)},
                               8: {"loc": (-0.01, 0, 0.07)}, 10: {"loc": (0, 0, 0.05)}, 12: {"loc": (0, 0, 0.09)},
                               14: {"loc": (0, 0, -0.3)}, 16: {"loc": (0, 0, -Z0)}, 18: {"loc": (0, 0, -Z0 + 0.07)},
                               20: {"loc": (0, 0, -Z0)}, 36: {"loc": (0, 0, -Z0)}, 54: {"loc": (0, 0, 0)}},
            linear=True)
    export_anim(root, "trap_crusher", [(stone_o, root)])


# ------------------------------------------------------------------ cavern dressing

def mushroom_big():
    cap = mat("mushroom_big_cap", (0.32, 0.22, 0.62), 0.5, coat=0.4)
    stem_m = mat("mushroom_big_stem", (0.86, 0.84, 0.76), 0.7)
    gill = mat("mushroom_big_glow", (0.5, 0.95, 1.0), 0.5, emit=2.5, emit_color=(0.3, 0.85, 1.0))
    spots = mat("mushroom_big_spot_glow", (0.7, 1.0, 1.0), 0.5, emit=3.5, emit_color=(0.45, 0.95, 1.0))
    moss_m = mat("mushroom_big_moss", (0.26, 0.48, 0.17), 0.9)
    parts = mushroom((0, 0, 0), 0.82, 0.46, cap, stem_m, gill, lean=(0.08, 0.02), segs=14, spots=spots, seed=21)
    parts += mushroom((0.3, -0.12, 0), 0.22, 0.13, cap, stem_m, gill, lean=(0.04, 0), segs=8, spots=spots, seed=22)
    parts += [lumpy(0.2, (0, 0, 0.02), moss_m, 23, amount=0.2, scale=(1.4, 1.0, 0.35))]
    simple(parts, "mushroom_big")


def ring_of_skirt(c, r, material):
    """A little frilly ring round a mushroom stem."""
    return lathe_r([(r * 0.9, c[2] + 0.03), (r * 1.35, c[2] - 0.02), (r * 1.25, c[2] - 0.05), (r * 0.9, c[2])],
                   material, segs=12, smooth=40, center=(c[0], c[1], 0))


def mushroom_small():
    cap = mat("mushroom_small_cap", (0.95, 0.45, 0.14), 0.5)
    stem_m = mat("mushroom_small_stem", (0.92, 0.88, 0.78), 0.7)
    spots = mat("mushroom_small_glow", (1.0, 0.85, 0.5), 0.5, emit=2.5, emit_color=(1.0, 0.7, 0.3))
    moss_m = mat("mushroom_small_moss", (0.26, 0.48, 0.17), 0.9)
    parts = []
    for (x, y, h, r, lx, seed) in ((0.0, 0.0, 0.4, 0.14, 0.04, 31), (0.2, -0.05, 0.26, 0.1, 0.05, 32),
                                   (-0.16, 0.03, 0.22, 0.09, -0.05, 33), (0.08, -0.12, 0.12, 0.06, 0.02, 34)):
        parts += mushroom((x, y, 0), h, r, cap, stem_m, None, lean=(lx, 0), segs=8, spots=spots, seed=seed)
    parts.append(lumpy(0.16, (0.02, 0, 0.01), moss_m, 35, amount=0.2, scale=(1.8, 1.0, 0.3)))
    simple(parts, "mushroom_small")


def crystal_cluster():
    glow = mat("crystal_glow", (0.35, 0.8, 1.0), 0.15, emit=3.0, emit_color=(0.25, 0.7, 1.0), coat=1.0)
    pale = mat("crystal_glow_pale", (0.75, 0.6, 1.0), 0.15, emit=2.2, emit_color=(0.6, 0.4, 1.0), coat=1.0)
    rock = mat("crystal_rock", (0.3, 0.28, 0.32), 0.9)
    parts = [lumpy(0.3, (0, 0.02, 0.02), rock, 41, amount=0.2, scale=(1.3, 0.9, 0.45), sub=2)]
    for k, (x, y, h, r, tx, ty) in enumerate(((0.0, 0.0, 0.88, 0.1, 0.05, 0.0), (-0.18, 0.02, 0.58, 0.08, -0.3, 0.05),
                                              (0.2, -0.03, 0.52, 0.075, 0.28, -0.05), (-0.08, -0.12, 0.36, 0.06, -0.1, -0.35),
                                              (0.12, 0.12, 0.42, 0.065, 0.15, 0.3), (0.32, 0.06, 0.28, 0.05, 0.45, 0.1),
                                              (-0.32, -0.02, 0.3, 0.05, -0.5, 0.0))):
        m = pale if k in (1, 5) else glow
        prof = [(0.0, h), (r * 0.8, h - r * 1.6), (r, h - r * 2.0), (r, 0.0), (0.0, -0.05)]
        c = lathe_r(prof, m, segs=6, smooth=0)
        d = Vector((tx, ty, 1.0)).normalized()
        c.data.transform(Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
        c.data.transform(Matrix.Translation((x, y, 0.02)))
        parts.append(c)
    simple(parts, "crystal_cluster")


def root_hang():
    bark = mat("root_bark", (0.32, 0.21, 0.12), 0.9)
    soil = mat("root_soil", (0.25, 0.17, 0.1), 0.95)
    moss_m = mat("root_moss", (0.28, 0.5, 0.18), 0.9)
    glow = mat("root_glow", (0.6, 1.0, 0.75), 0.5, emit=4.0, emit_color=(0.4, 1.0, 0.6))
    parts = [lumpy(0.35, (0, 0.05, 0.05), soil, 51, amount=0.2, scale=(1.6, 0.9, 0.5), sub=2),
             lumpy(0.25, (-0.2, -0.05, -0.05), moss_m, 52, amount=0.25, scale=(1.3, 0.8, 0.45))]
    rnd = random.Random(53)
    for k, (x, ln) in enumerate(((-0.4, 1.1), (-0.15, 1.5), (0.1, 1.25), (0.35, 0.9), (0.02, 0.7))):
        pts = []
        n = 6
        for i in range(n):
            t = i / (n - 1)
            pts.append((x + 0.08 * math.sin(t * 5 + k) + rnd.uniform(-0.03, 0.03), -0.05 + 0.03 * math.cos(t * 4 + k),
                        -ln * t))
        rad = [0.05 * (1 - t * 0.8) for t in (i / (n - 1) for i in range(n))]
        parts.append(limb(pts, rad, bark, verts=6, per=2, caps=True))
        # a side rootlet and a glowing bead at the tip
        m = pts[2]
        parts.append(limb([m, (m[0] + 0.12, m[1] - 0.02, m[2] - 0.12), (m[0] + 0.16, m[1], m[2] - 0.3)],
                          [0.02, 0.014, 0.006], bark, verts=5, per=2, caps=True))
        if k in (1, 2, 4):
            tip = pts[-1]
            parts.append(rod(tip, (tip[0], tip[1], tip[2] - 0.12), 0.004, glow, verts=3))
            parts.append(ico(0.03, (tip[0], tip[1], tip[2] - 0.14), glow, sub=1))
    simple(parts, "root_hang")


def fern():
    leaf_m = mat("fern_leaf", (0.2, 0.5, 0.16), 0.75)
    tip_m = mat("fern_leaf_light", (0.42, 0.72, 0.24), 0.7)
    parts = []
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        d = Vector((math.cos(a), math.sin(a) * 0.6, 0))
        ln = 0.7 if k % 2 == 0 else 0.55
        pts = [Vector((0, 0, 0.02)) + d * ln * 0.75 * t + Vector((0, 0, ln * (1.7 * t - 1.2 * t * t)))
               for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        parts.append(limb(pts, [0.014, 0.012, 0.01, 0.007, 0.004], leaf_m, verts=4, per=2))
        # leaflets in pairs along the frond
        for i in range(1, 7):
            t = i / 7
            p = Vector((0, 0, 0.02)) + d * ln * 0.75 * t + Vector((0, 0, ln * (1.7 * t - 1.2 * t * t)))
            tan = (d * ln * 0.75 + Vector((0, 0, ln * (1.7 - 2.4 * t)))).normalized()
            side = tan.cross(Vector((0, 0, 1))).normalized()
            size = 0.17 * (1 - t * 0.6)
            for sgn in (1, -1):
                lf = prism([(0, 0), (size * 0.5, size * 0.22), (size, 0), (size * 0.5, -size * 0.12)], 0.008, (0, 0, 0),
                           tip_m if t > 0.7 else leaf_m, rot=(R90, 0, 0), bevel=0.0)
                dirv = (side * sgn + tan * 0.35 + Vector((0, 0, -0.25))).normalized()
                lf.data.transform(Vector((1, 0, 0)).rotation_difference(dirv).to_matrix().to_4x4())
                lf.data.transform(Matrix.Translation(p))
                parts.append(lf)
    simple(parts, "fern")


def lantern_post():
    wood = mat("lantern_post_wood", (0.38, 0.24, 0.13), 0.85)
    metal = mat("lantern_post_metal", (0.2, 0.2, 0.22), 0.5, 0.7)
    glow = mat("lantern_post_glow", (1.0, 0.8, 0.45), 0.4, emit=8.0, emit_color=(1.0, 0.62, 0.22))
    stone = mat("lantern_post_stone", (0.46, 0.43, 0.4), 0.9)
    moss_m = mat("lantern_post_moss", (0.28, 0.5, 0.18), 0.9)
    parts = [lumpy(0.2, (0, 0, 0.06), stone, 61, amount=0.15, scale=(1.3, 1.0, 0.55), sub=2),
             lumpy(0.14, (-0.08, -0.05, 0.14), moss_m, 62, amount=0.2, scale=(1.4, 1.0, 0.4)),
             limb([(0, 0, 0.0), (0.01, 0, 0.7), (-0.01, 0, 1.45), (0.0, 0, 1.52)], [0.055, 0.05, 0.045, 0.04],
                  wood, verts=6, per=2, caps=True),
             limb([(0.0, 0, 1.42), (0.18, 0, 1.47), (0.34, 0, 1.44), (0.38, 0, 1.38)], [0.03, 0.028, 0.024, 0.02],
                  wood, verts=6, per=2, caps=True),
             rod((0.03, 0, 1.3), (0.2, 0, 1.45), 0.015, wood, verts=5)]
    lx = 0.38
    parts += [rod((lx, 0, 1.38), (lx, 0, 1.3), 0.008, metal, verts=4),
              lathe_r([(0.0, 1.31), (0.05, 1.3), (0.11, 1.24), (0.1, 1.22), (0.0, 1.22)], metal, segs=8, smooth=0),
              lathe_r([(0.0, 1.23), (0.075, 1.22), (0.085, 1.15), (0.075, 1.08), (0.0, 1.07)], glow, segs=8),
              lathe_r([(0.0, 1.085), (0.095, 1.08), (0.08, 1.05), (0.0, 1.04)], metal, segs=8, smooth=0)]
    for o in parts[-3:]:
        o.data.transform(Matrix.Translation((lx, 0, 0)))
    for k in range(4):
        a = math.pi / 4 + k * R90
        parts.append(rod((lx + 0.095 * math.cos(a), 0.095 * math.sin(a), 1.235),
                         (lx + 0.09 * math.cos(a), 0.09 * math.sin(a), 1.075), 0.009, metal, verts=4))
    simple(parts, "lantern_post")


# ------------------------------------------------------------------ main

JOBS = {"mossling": mossling, "hatch": hatch, "burrow": burrow, "trap_snapper": trap_snapper,
        "trap_crusher": trap_crusher, "mushroom_big": mushroom_big, "mushroom_small": mushroom_small,
        "crystal_cluster": crystal_cluster, "root_hang": root_hang, "fern": fern, "lantern_post": lantern_post}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
