"""Hopline (game 16) models: the frog (and the lady frog), the traffic, the river riders (logs, turtles, a lily pad,
the crocodile), the home bays in the hedge, the ground tiles and the canal-town dressing.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/hopline_models.py -- godot/games/hopline/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, ico, rod, tube, prism, join, export), the rig from
blastyard_bombers.py (Rig, merge, mirror, limb), prism_models.py (loft_x, superellipse, animate, export_anim, new_obj),
nightbite_characters.py (blob) and mossfolk_models.py (lumpy, lathe_r).

Axes. One grid cell = 1 unit. Blender Z up; lanes run along X; the frog hops towards Blender +Y. In Godot +X stays +X,
Blender +Z becomes +Y (up) and Blender +Y becomes -Z (away from the camera, which sits at +Z). Origins sit on the
ground (or on the water surface for floating things) at the object's centre unless noted. Suggested water surface:
Godot y = -0.1 (the canal lies a little below the pavement: see water_edge); the river riders' origins go at that
level, the ground tiles' tops are at y = 0.

frog.glb      armature "frog_rig" and the skinned mesh "frog", facing Godot -Z, 0.7 long (nose to the folded heels),
              0.52 across, eyes 0.37 high. Materials: frog_skin (recolour it for player 2), frog_spot (the back spots,
              a darker skin: tint it with the skin), frog_belly, frog_throat (the croaking sac), frog_eye, frog_pupil,
              frog_shine, frog_mouth, frog_cheek, frog_bubble (the drowning bubbles, alpha-blended).
              Animations (50 fps): idle (loop 2 s: breathing, throat pumping, a blink at 1.2 s),
              hop (one-shot 0.18 s: crouch, launch with the legs thrown back, stretched mid-air, landing squash;
              it holds NO horizontal travel, the game moves the node one cell, but it DOES carry the vertical arc of
              the body: 0.17 at 0.1 s, back on the ground at 0.16 s; feet on the ground at both ends),
              splat (one-shot 0.8 s, pancake: holds the last frame), drown (one-shot 1.2 s: flails, sinks 0.75
              below the origin while four bubbles rise to the surface and pop; nothing shows at the end),
              home (one-shot 1.2 s: a happy hop in place, then two croaks with the throat sac puffed up, squinting).
              The bubbles sit inside the body unless drown plays.
lady_frog.glb the pink bonus frog: the same rig and animations ("lady_frog_rig", mesh "lady_frog"), materials lady_*
              (lady_skin, lady_spot, ...), plus a flower on her head (lady_petal, lady_flower_heart) and lashes.
Vehicles (one root node named like the file, facing Godot +X, origin at the centre on the road; about 0.7 wide):
              car_a 1.2 long (a round little city car), car_b 1.6 (a two-tone delivery van with crates on the roof),
              truck 2.6 (a lorry: cab and cargo box), bulldozer 1.4 (on tracks, blade in front), racecar 1.2 (open
              wheels, wings). Materials "<name>_paint" (recolour), "<name>_glow" (headlights, emissive), plus glass,
              tyre, hub, chrome, tail (rear lights) and trims. Children "wheel_0".. (all but the bulldozer): each
              wheel's origin is on its axle; spin them about the node's local Z (Godot), negative for forward travel
              (angle -= distance / radius; radii: car_a 0.13, car_b 0.15, truck 0.16, racecar 0.14 front / 0.16 rear).
River (origins at the water surface, at the centre; long axis along X):
              log_short 3, log_mid 4, log_long 6 long, 0.58 thick, top of the bark 0.2 above the water (the frog
              rides at y + 0.2); materials log_bark, log_wood (cut ends), log_ring, log_moss (+ log_cap / log_dot
              toadstools on the mid and long logs).
              turtle: one turtle 0.9 long (X), facing +X, shell top 0.23 above the water; armature "turtle_rig",
              mesh "turtle". Animations (30 fps): swim (loop 1 s: flippers rowing, head bob), dive (one-shot 1 s: noses
              down, fully under (0.45 below) from 0.4 s to 0.6 s, back up at 1 s). The game may also just lower it.
              lilypad: 0.86 across, top 0.02 above the water, a flower on its rim (lilypad_leaf, lilypad_vein,
              lilypad_petal, lilypad_heart).
              croc: 3.0 long, facing +X, armature "croc_rig", mesh "croc". The back from x = -0.75 to +0.7 is flat
              enough to ride (top 0.2 above the water); the head is x = +0.75 .. +1.5 (dangerous while the mouth
              opens). Animation snap (loop 1.6 s, 30 fps): tail sway, the jaws gape at 0.9 s and snap shut at 1.07 s.
Scenery (origin on the ground, front towards the camera, Godot +Z):
              home_bay: one alcove of the top hedge, 1 wide opening; origin at the bay centre on the ground. A stone
              basin with its own water (child node "pool", water at y = -0.1: hide it if the river plane already
              reaches under the hedge row), a big lily pad whose top is at y = 0.0 (the frog sits at the origin),
              reeds and cattails, a flowered arch over the back. Depth: z = +0.5 (front, open) .. -1.0 (back hedge).
              hedge_block: the hedge between bays, 1 wide (x -0.5..0.5), from z = +0.5 to -1.0, 0.72 tall.
              bank_tile, median_tile, road_tile, road_tile_line: 1 x 1 tiles, top at y = 0, sides down to -0.3.
              The bank has a kerb along its far edge (z = -0.5, the road side), the median a kerb along its near
              edge (z = +0.5); road_tile_line has one dash of the lane line along its far edge (z -0.46..-0.41):
              a row of them makes a dashed line between two lanes.
              water_edge: stone coping 1 long (x -0.5..0.5) on the edge line between pavement and water (origin on
              that line at y = 0), the canal wall dropping to y = -0.6 on the water side, Godot -Z (rotate by PI for
              the other side).
              lamp_post 1.9 tall (lamp_post_glow), tree 2.2 tall, house_a (2.0 wide, 1.8 deep, 3.7 tall, a stepped
              gable), house_b (2.4 wide, 1.8 deep, 3.6 tall, a bell gable and a shop front): houses face Godot +Z,
              with windows on every side ("house_a_glow", "house_b_glow": lit windows).
              fly: a firefly hovering 0.32 above its origin; the node "fly" with the children "wing_l", "wing_r";
              animation buzz (loop 1 s, 30 fps: bob and wing beats). fly_glow is the lantern.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90
from blastyard_bombers import Rig, merge, mirror, limb
from prism_models import loft_x, superellipse, animate, export_anim, new_obj, empty
from nightbite_characters import blob
from mossfolk_models import lumpy, lathe_r

WATER = -0.1  # suggested water surface (Godot y); only home_bay's pool uses it


# ------------------------------------------------------------------ helpers

class TurnRig(Rig):
    """The blastyard Rig, written facing -Y (poses and positions), built and exported turned by `deg` about Z
    (180: facing +Y, Godot -Z; 90: facing +X). Keys are in frames at `fps`."""

    def __init__(self, bones, deg, fps=30, hidden=()):
        self.Q = Matrix.Rotation(math.radians(deg), 4, "Z")
        self.Q3 = self.Q.to_3x3()
        super().__init__({n: (tuple(self.Q3 @ Vector(h)), tuple(self.Q3 @ Vector(t)), p) for n, (h, t, p) in bones.items()})
        self.hidden = set(hidden)
        self.fps = fps
        self.lengths = {}

    def turn(self, o):
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.transform(self.Q)
        return o

    def weights(self, p, spec):
        if callable(spec):
            return spec(self.Q3.transposed() @ p)
        return super().weights(p, spec)

    def build(self, name):
        for o, _ in self.parts:
            self.turn(o)
        return super().build(name)

    def local_rot(self, bone, deg, prev):
        R = (Matrix.Rotation(math.radians(deg[2]), 3, "Z") @ Matrix.Rotation(math.radians(deg[1]), 3, "Y")
             @ Matrix.Rotation(math.radians(deg[0]), 3, "X"))
        R = self.Q3 @ R @ self.Q3.transposed()
        M = self.rest[bone]
        L = M.inverted() @ R @ M
        return L.to_euler("XYZ", prev) if prev is not None else L.to_euler("XYZ")

    def local_scale(self, bone, s):
        if not isinstance(s, (tuple, list)):
            s = (s, s, s)
        S = self.Q3 @ Matrix.Diagonal(Vector(s)) @ self.Q3.transposed()
        M = self.rest[bone]
        L = M.inverted() @ S @ M
        return Vector((abs(L[0][0]), abs(L[1][1]), abs(L[2][2])))

    def action(self, name, keys, loop=False):
        out = {}
        for f, p in keys.items():
            p = dict(p)
            for k in list(p):
                if k[0] == "@":
                    p[k] = tuple(self.Q3 @ Vector(p[k]))
            for b in self.hidden:
                p.setdefault("%" + b, 0.0)
            out[f] = p
        super().action(name, out, loop)
        self.lengths[name] = (max(keys) - min(keys)) / self.fps

    def save(self, name, extra=()):
        """Exports the armature and the mesh (plus bone-parented nodes) with every NLA track, at the rest pose."""
        for t in self.arm.animation_data.nla_tracks:
            t.mute = True
        for b in self.arm.pose.bones:
            b.location = (0, 0, 0)
            b.rotation_euler = (0, 0, 0)
            b.scale = (1, 1, 1)
        bpy.context.view_layer.update()
        sc = bpy.context.scene
        sc.render.fps = self.fps
        sc.frame_start = 0
        K.deselect()
        for o in [self.arm, self.mesh] + list(extra):
            o.select_set(True)
        bpy.context.view_layer.objects.active = self.arm
        bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, name + ".glb"), use_selection=True,
                                  export_format="GLB", export_yup=True, export_apply=False, export_animations=True,
                                  export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_frame_step=1)
        print("exported %-10s %5d tris  anims: %s" % (name, K.tris(self.mesh), ", ".join(
            "%s %.2fs" % (k, v) for k, v in self.lengths.items())))
        sc.render.fps = 30
        reset()


def ell(c, r, material, pitch=0.0, segs=20, rings=12, yaw=0.0, roll=0.0):
    """An ellipsoid with semi-axes r = (rx, ry, rz) at c, pitched about X (degrees, + tips the -Y end down)."""
    o = sphere(1.0, (0, 0, 0), material, scale=r, segs=segs, rings=rings)
    o.data.transform(Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pitch), 4, "X")
                     @ Matrix.Rotation(math.radians(roll), 4, "Y"))
    o.data.transform(Matrix.Translation(Vector(c)))
    return o


def ell_point(c, r, d, pitch=0.0):
    """The point of an ellipsoid (as made by ell, without yaw or roll) in direction d from its centre."""
    R = Matrix.Rotation(math.radians(pitch), 3, "X")
    dl = R.transposed() @ Vector(d).normalized()
    # scale the local direction to the surface
    k = 1.0 / math.sqrt((dl.x / r[0]) ** 2 + (dl.y / r[1]) ** 2 + (dl.z / r[2]) ** 2)
    return Vector(c) + R @ (dl * k)


def hemi(r, c, pole, material, cut=0.0, segs=20, rings=12):
    """The part of a sphere (radius r at c) on the side of `pole` (dot > cut): an eyelid, a dome."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    p = Vector(pole).normalized()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.normalized().dot(p) < cut], context="VERTS")
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    o = new_obj("hemi", bm, material, smooth=80)
    return o


def soap(x0, x1, hw, hh, zc, material, r=0.12, p=3.0, n=24, ends=5, taper=None, name="soap"):
    """A rounded bar along X from x0 to x1: a superellipse section (half width hw, half height hh) centred at
    height zc, both ends rounded over r. taper(x) -> (sy, sz, dz) multiplies the section along the way."""
    prof = superellipse(hw, hh, n, p)
    cap = []  # (distance from the end, section scale): a quarter circle from a small cap to the full section
    for k in range(ends + 1):
        t = math.radians(14 + 76 * k / ends)
        cap.append((r * (1 - math.cos(t)), math.sin(t)))
    st = [(x0 + d, s) for d, s in cap]
    mids = max(1, int((x1 - x0 - 2 * r) / 0.15))
    for k in range(1, mids):
        st.append((x0 + r + (x1 - x0 - 2 * r) * k / mids, 1.0))
    st += [(x1 - d, s) for d, s in reversed(cap)]
    stations = []
    for x, s in st:
        sy, sz, dz = taper(x) if taper else (1.0, 1.0, 0.0)
        # the ends round off more across (y) than in height, like a pebble
        stations.append((x, sy * (0.2 + 0.8 * s), sz * (0.35 + 0.65 * s), zc + dz))
    return loft_x(prof, stations, material, cap_start=True, cap_end=True, name=name, smooth=55)


def wheel(r, width, loc, tyre, hub, name, cap=None):
    """A chubby toy wheel with its axle along Y: a torus tyre round a hub disc; origin on the axle."""
    loc = Vector(loc)
    R = r * 0.64
    t = r - R
    parts = [torus(R, t, loc, tyre, rot=(R90, 0, 0), verts=22, minor=8, scale=(1, 1, width / (2 * t)))]
    parts[0].data.transform(Matrix.Translation(-loc))
    parts[0].data.transform(Matrix.Diagonal((1, width / (2 * t), 1, 1)))  # squash the tyre across (the rot put Z on Y)
    parts[0].data.transform(Matrix.Translation(loc))
    parts.append(cyl(R * 1.02, width * 0.8, loc, hub, rot=(R90, 0, 0), verts=18, bevel=0.01, segs=2))
    parts.append(cyl(R * 0.45, width * 0.92, loc, cap or hub, rot=(R90, 0, 0), verts=12, bevel=0.008, segs=1))
    return join(parts, name, pivot=loc)


def loft_y(profile, stations, material, cap_start=False, cap_end=False, name="lofty", smooth=50):
    """Sweeps an (x, z) profile along Y. stations: (y, scale_x, scale_z, dz)."""
    bm = bmesh.new()
    rings = []
    for y, sx, sz, dz in stations:
        rings.append([bm.verts.new((x * sx, y, z * sz + dz)) for x, z in profile])
    n = len(profile)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    for flag, ring in ((cap_start, rings[0]), (cap_end, rings[-1])):
        if flag:
            bm.faces.new(ring)
    return new_obj(name, bm, material, smooth)


def flower(c, petal, heart, r=0.05, n=5, tilt=0.35, seg=6):
    """A small flower facing up at c: n flattened petals and a heart."""
    c = Vector(c)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Vector((math.cos(a), math.sin(a), 0))
        o = sphere(r, (0, 0, 0), petal, scale=(1.0, 0.62, 0.3), segs=seg, rings=4)
        o.data.transform(Matrix.Rotation(-tilt, 4, "Y"))
        o.data.transform(Matrix.Translation((r * 0.9, 0, 0)))
        o.data.transform(Matrix.Rotation(a, 4, "Z"))
        o.data.transform(Matrix.Translation(c))
        out.append(o)
    out.append(sphere(r * 0.5, c + Vector((0, 0, r * 0.15)), heart, segs=8, rings=5))
    return out


def ang(v):
    """Angle of a direction in the Y-Z plane (degrees, measured like a rotation about +X from +Y)."""
    return math.degrees(math.atan2(v[2], v[1]))


def wrap(a):
    while a > 180:
        a -= 360
    while a <= -180:
        a += 360
    return a


# ------------------------------------------------------------------ the frog

HIP = (0.13, 0.13, 0.13)
KNEE = (0.275, 0.0, 0.1)
ANKLE = (0.255, 0.2, 0.045)
TOE = (0.27, -0.03, 0.02)
SHOULDER = (0.12, -0.13, 0.135)
WRIST = (0.165, -0.235, 0.03)
FINGER = (0.17, -0.3, 0.012)
EYE = Vector((0.108, -0.165, 0.3))
EYE_R = 0.066
LID_POLE = Vector((0, 0.86, 0.5))


def frog_bones():
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0.1, 0.12), (0, -0.14, 0.2), "root"),
         "throat": ((0, -0.2, 0.12), (0, -0.25, 0.1), "body"),
         "bubbles": ((0, 0.02, 0.1), (0, 0.02, 0.2), None)}
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: (p[0] * s, p[1], p[2])
        e = (EYE.x * s, EYE.y, EYE.z)
        B["lid." + side] = (e, (e[0], e[1], e[2] + 0.05), "body")
        B["arm." + side] = (m(SHOULDER), m(WRIST), "body")
        B["hand." + side] = (m(WRIST), m(FINGER), "arm." + side)
        B["thigh." + side] = (m(HIP), m(KNEE), "body")
        B["shin." + side] = (m(KNEE), m(ANKLE), "thigh." + side)
        B["foot." + side] = (m(ANKLE), m(TOE), "shin." + side)
    return B


REST_ANG = {"thigh": ang(Vector(KNEE) - Vector(HIP)), "shin": ang(Vector(ANKLE) - Vector(KNEE)),
            "foot": ang(Vector(TOE) - Vector(ANKLE)), "arm": ang(Vector(WRIST) - Vector(SHOULDER)),
            "hand": ang(Vector(FINGER) - Vector(WRIST))}


def leg_pose(thigh=None, shin=None, foot=None, body=0.0, spread=0.0):
    """World directions (angles in the Y-Z plane, see ang) for the back leg segments, both sides; None keeps the
    segment's rest angle relative to its parent. body: the body's pitch (degrees about X) they hang from."""
    p = {}
    acc = body
    for bone, phi in (("thigh", thigh), ("shin", shin), ("foot", foot)):
        rel = 0.0 if phi is None else wrap(phi - REST_ANG[bone] - acc)
        acc += rel
        p[bone + ".L"] = (rel, 0, spread if bone == "thigh" else 0)
    return mirror(p)


def arm_pose(arm=None, hand=None, body=0.0, spread=0.0):
    p = {}
    acc = body
    for bone, phi in (("arm", arm), ("hand", hand)):
        rel = 0.0 if phi is None else wrap(phi - REST_ANG[bone] - acc)
        acc += rel
        p[bone + ".L"] = (rel, 0, spread if bone == "arm" else 0)
    return mirror(p)


def lids(deg):
    return {"lid.L": (deg, 0, 0), "lid.R": (deg, 0, 0)}


def frog_model(name, pre, colors, lady=False):
    reset()
    skin = mat(pre + "_skin", colors["skin"], 0.42, coat=0.45)
    spot = mat(pre + "_spot", colors["spot"], 0.5, coat=0.3)
    belly = mat(pre + "_belly", colors["belly"], 0.55, coat=0.2)
    throat_m = mat(pre + "_throat", colors["throat"], 0.35, coat=0.6)
    eye_m = mat(pre + "_eye", (1.0, 0.99, 0.95), 0.2, coat=0.8, emit=0.12)
    pupil_m = mat(pre + "_pupil", (0.015, 0.018, 0.025), 0.12, coat=1.0)
    shine_m = mat(pre + "_shine", (1.0, 1.0, 1.0), 0.2, emit=4.0)
    mouth_m = mat(pre + "_mouth", colors["mouth"], 0.6)
    cheek_m = mat(pre + "_cheek", colors["cheek"], 0.6)
    bubble_m = mat(pre + "_bubble", (0.75, 0.92, 1.0), 0.05, coat=1.0, alpha=0.5, emit=0.3)

    rig = TurnRig(frog_bones(), 180, fps=50, hidden=("bubbles",))

    # body and head: two ellipsoids that overlap into one smooth toy shape
    BODY_C, BODY_R, BODY_P = (0, 0.05, 0.155), (0.2, 0.22, 0.125), -18
    HEAD_C, HEAD_R, HEAD_P = (0, -0.15, 0.2), (0.21, 0.16, 0.12), -6
    rig.rigid("body",
              ell(BODY_C, BODY_R, skin, BODY_P, segs=24, rings=14),
              ell(HEAD_C, HEAD_R, skin, HEAD_P, segs=24, rings=14),
              ell((0, -0.08, 0.1), (0.165, 0.2, 0.075), belly, -6, segs=20, rings=10),
              ell((0, -0.2, 0.132), (0.15, 0.1, 0.075), belly, -10, segs=18, rings=10))
    # spots on the back
    for k, (dx, dy, dz, r, sx) in enumerate(((0.12, 0.3, 1.0, 0.045, 1.3), (0.62, 0.05, 0.8, 0.032, 1.0),
                                             (-0.5, 0.42, 0.85, 0.038, 1.4), (0.3, 0.85, 0.6, 0.03, 1.2),
                                             (-0.2, 0.8, 0.65, 0.024, 1.0), (-0.12, -0.05, 1.0, 0.022, 1.1),
                                             (0.75, 0.5, 0.45, 0.026, 1.3), (-0.72, -0.05, 0.6, 0.022, 1.0))):
        d = Vector((dx, dy, dz)).normalized()
        p = ell_point(BODY_C, BODY_R, d, BODY_P) - d * 0.004
        rig.rigid("body", blob(r, p, spot, (sx, 0.12, 0.85), d, segs=12, rings=6))
    # mouth: a smile along the head's front, a bit below its equator
    pts = []
    for k in range(13):
        a = math.radians(18 + 144 * k / 12)
        d = Vector((math.cos(a), -math.sin(a), -0.1 + 0.16 * abs(math.cos(a)) ** 2))
        pts.append(ell_point(HEAD_C, HEAD_R, d, HEAD_P) + Vector((0, 0, 0.0)) + d.normalized() * 0.002)
    rig.rigid("body", tube(pts, [0.006] + [0.0085] * 11 + [0.006], mouth_m, verts=6))
    # nostrils, cheeks
    for s in (1, -1):
        n = ell_point(HEAD_C, HEAD_R, (0.2 * s, -1.0, 0.55), HEAD_P)
        rig.rigid("body", sphere(0.011, n, mouth_m, segs=6, rings=4))
        cd = Vector((0.75 * s, -0.62, -0.05))
        rig.rigid("body", blob(0.036, ell_point(HEAD_C, HEAD_R, cd, HEAD_P), cheek_m, (1.2, 0.25, 0.8), cd, segs=10,
                               rings=6))
    # throat sac: tucked under the chin, puffs out when the "throat" bone scales up
    rig.rigid("throat", ell((0, -0.225, 0.118), (0.08, 0.06, 0.05), throat_m, -15, segs=16, rings=10))
    # eyes on their bumps, lids (open: resting on the back of the eye), pupils looking ahead
    for s, side in ((1, "L"), (-1, "R")):
        e = Vector((EYE.x * s, EYE.y, EYE.z))
        d = Vector((0.42 * s, -0.86, 0.22)).normalized()
        rig.rigid("body", ell(e + Vector((0.004 * s, 0.018, -0.035)), (0.078, 0.078, 0.062), skin, segs=16, rings=10))
        rig.rigid("body", sphere(EYE_R, e, eye_m, segs=18, rings=12))
        pp = e + d * (EYE_R * 0.8)
        rig.rigid("body", blob(0.043, pp, pupil_m, (1.25, 0.42, 0.95), d, segs=14, rings=8))
        rig.rigid("body", sphere(0.013, pp + d * 0.018 + Vector((0.012 * s, 0.004, 0.021)), shine_m, segs=6, rings=4))
        lid = hemi(EYE_R + 0.006, e, LID_POLE, skin, cut=-0.12, segs=18, rings=12)
        rig.rigid("lid." + side, lid)
        if lady:
            lash = mat(pre + "_lash", (0.05, 0.03, 0.05), 0.5)
            # lashes on the lid's front rim (open lid: the rim faces up-forward)
            # three lashes on the outer side of each eye, curling out and up
            for k, (dy, dz) in enumerate(((-0.35, 0.35), (0.0, 0.5), (0.35, 0.45))):
                out = Vector((s, dy, dz)).normalized()
                q = e + out * (EYE_R + 0.004)
                rig.rigid("lid." + side, tube([q, q + out * 0.02 + Vector((0, 0, 0.004)),
                                               q + out * 0.032 + Vector((0, 0, 0.014))], [0.0045, 0.004, 0.002], lash,
                                              verts=4))
    # front legs and hands (three fingers with round pads)
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: Vector((p[0] * s, p[1], p[2]))
        rig.rigid("arm." + side, limb([m((0.1, -0.12, 0.15)), m(SHOULDER), m((0.16, -0.19, 0.085)), m(WRIST)],
                                      [0.038, 0.037, 0.03, 0.026], skin, verts=10, per=3, caps=True))
        w = m(WRIST)
        for k, a in enumerate((-35, 0, 35)):
            d = Vector((math.sin(math.radians(a)) * s * 0.9 + 0.25 * s, -math.cos(math.radians(a)), -0.1)).normalized()
            tip = w + d * 0.06 + Vector((0, 0, -0.015))
            rig.rigid("hand." + side, rod(w + Vector((0, 0, -0.008)), tip, 0.013, skin, r2=0.011, verts=6),
                      sphere(0.016, tip, belly, scale=(1, 1, 0.7), segs=8, rings=5))
    # back legs: a big haunch, the shin folded back, a long webbed foot pointing forward
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: Vector((p[0] * s, p[1], p[2]))
        rig.rigid("thigh." + side, limb([m((0.07, 0.15, 0.15)), m(HIP), m((0.23, 0.06, 0.12)), m(KNEE)],
                                        [0.065, 0.085, 0.068, 0.046], skin, verts=12, per=3, caps=True))
        rig.rigid("shin." + side, limb([m(KNEE), m((0.275, 0.1, 0.075)), m(ANKLE)], [0.046, 0.04, 0.028], skin,
                                       verts=10, per=3, caps=True),
                  sphere(0.047, m(KNEE), skin, segs=12, rings=8))
        a0 = m(ANKLE)
        heel = m((0.262, 0.06, 0.03))
        rig.rigid("foot." + side, limb([a0, heel, m((0.268, 0.0, 0.021))], [0.028, 0.023, 0.019], skin, verts=8,
                                       per=2, caps=True))
        base = m((0.268, -0.005, 0.018))
        tips = []
        for k, a in enumerate((-32, -8, 16)):
            aa = math.radians(a)
            d = Vector((math.sin(aa) * s + 0.12 * s, -math.cos(aa), 0)).normalized()
            tip = base + d * 0.085 + Vector((0, 0, -0.004))
            tips.append(tip)
            rig.rigid("foot." + side, rod(base, tip, 0.011, skin, r2=0.009, verts=6),
                      sphere(0.017, tip, belly, scale=(1, 1, 0.65), segs=8, rings=5))
        # webbing between the toes: a thin fan
        bm = bmesh.new()
        c = bm.verts.new(base + Vector((0, 0, 0.004)))
        vs = []
        for i in range(len(tips)):
            vs.append(bm.verts.new(tips[i] + (base - tips[i]) * 0.18 + Vector((0, 0, 0.004))))
            if i < len(tips) - 1:
                mid = (tips[i] + tips[i + 1]) / 2
                vs.append(bm.verts.new(base + (mid - base) * 0.62 + Vector((0, 0, 0.004))))
        for i in range(len(vs) - 1):
            bm.faces.new((c, vs[i], vs[i + 1]))
        web = new_obj("web", bm, skin, smooth=0)
        mod = web.modifiers.new("s", "SOLIDIFY")
        mod.thickness = 0.006
        mod.offset = 0
        K.select(web)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        rig.rigid("foot." + side, web)
    # the drowning bubbles, hidden inside the body until drown lifts them out
    for k, (x, y, z, r) in enumerate(((0.03, 0.0, 0.14, 0.035), (-0.05, 0.05, 0.16, 0.025), (0.0, 0.08, 0.2, 0.03),
                                      (0.06, 0.08, 0.12, 0.02))):
        rig.rigid("bubbles", sphere(r, (x, y, z), bubble_m, segs=12, rings=8))
    extra = []
    if lady:
        petal = mat(pre + "_petal", (1.0, 0.97, 0.98), 0.4, coat=0.3, emit=0.15)
        heart = mat(pre + "_flower_heart", (1.0, 0.78, 0.15), 0.4, emit=0.8)
        c = ell_point(HEAD_C, HEAD_R, (0.55, 0.3, 1.0), HEAD_P) + Vector((0, 0, 0.03))
        fl = flower(c, petal, heart, r=0.045, n=6, tilt=0.45, seg=8)
        leafm = mat(pre + "_leaf", (0.3, 0.62, 0.15), 0.5)
        fl.append(sphere(0.05, c + Vector((0.035, 0.03, -0.02)), leafm, scale=(1, 0.5, 0.2), segs=8, rings=4,
                         rot=(0, 0.3, 0.6)))
        rig.rigid("body", *fl)
    rig.build(name)

    # ---------------------------------------------------------------- actions (facing -Y while writing them)
    REST = {}
    # idle: breathing, throat pumping twice, a blink
    def breathe(k, throat=1.0, lid=0.0):
        return merge({"%body": (1 + 0.012 * k, 1 + 0.008 * k, 1 + 0.03 * k), "%throat": throat}, lids(lid))
    rig.action("idle", {0: breathe(0), 25: breathe(1, 1.18), 50: breathe(0, 1.0), 58: breathe(0.3, 1.0),
                        61: breathe(0.4, 1.0, 108), 64: breathe(0.5, 1.0, 0), 75: breathe(1, 1.18),
                        100: breathe(0)}, loop=True)

    # hop: 9 frames at 50 fps
    crouch = merge({"@root": (0, 0, -0.025), "body": (-6, 0, 0), "%body": (1.06, 0.95, 0.88)},
                   leg_pose(thigh=REST_ANG["thigh"] + 6, shin=None, foot=None, body=-6),
                   arm_pose(body=-6), lids(20))
    launch = merge({"@root": (0, 0, 0.1), "body": (-16, 0, 0), "%body": (0.92, 1.16, 0.95)},
                   leg_pose(thigh=-48, shin=-45, foot=-35, body=-16),
                   arm_pose(arm=-150, hand=-165, body=-16))
    apex = merge({"@root": (0, 0, 0.17), "body": (-2, 0, 0), "%body": (0.94, 1.14, 0.96)},
                 leg_pose(thigh=-38, shin=-55, foot=-25, body=-2, spread=-6),
                 arm_pose(arm=-160, hand=-175, body=-2))
    reach = merge({"@root": (0, 0, 0.08), "body": (6, 0, 0), "%body": (1.0, 1.04, 1.0)},
                  leg_pose(thigh=-140, shin=-35, foot=-172, body=6),
                  arm_pose(arm=-120, hand=-160, body=6))
    land = merge({"@root": (0, 0, -0.02), "body": (4, 0, 0), "%body": (1.1, 0.96, 0.84)},
                 leg_pose(body=4), arm_pose(body=4), lids(15))
    rig.action("hop", {0: {}, 2: crouch, 4: launch, 5: apex, 7: reach, 8: land, 9: {}})

    # splat: squashed flat, limbs splayed, eyes shut
    flat = merge({"%root": (1.55, 1.4, 0.14)}, leg_pose(thigh=-150, shin=-20, foot=-170, spread=35),
                 arm_pose(arm=-175, spread=40), lids(115))
    rig.action("splat", {0: {}, 3: merge(flat, {"%root": (1.75, 1.55, 0.08)}), 7: merge(flat, {"%root": (1.4, 1.3, 0.2)}),
                         12: merge(flat, {"%root": (1.6, 1.45, 0.12)}), 18: flat, 40: flat})

    # drown: flailing, sinking; the bubbles rise to the surface and pop
    def sink(z, j, bz, bs):
        return merge({"@root": (0, 0, z), "body": (-20 + 8 * j, 0, 6 * j), "@bubbles": (0, 0, bz), "%bubbles": bs},
                     arm_pose(arm=75 + 20 * j, hand=90), leg_pose(thigh=-60 - 20 * j, shin=-40, foot=-30),
                     lids(40))
    rig.action("drown", {0: {}, 6: sink(-0.08, 1, 0.0, 0.0), 14: sink(-0.2, -1, 0.05, 0.6),
                         22: sink(-0.34, 1, 0.12, 1.0), 32: sink(-0.52, -1, 0.2, 1.1), 42: sink(-0.66, 1, 0.26, 1.2),
                         50: sink(-0.75, -1, 0.3, 1.3), 54: sink(-0.75, 0, 0.32, 0.0), 60: sink(-0.75, 0, 0.32, 0.0)})

    # home: a happy hop in place, then two croaks
    croak = lambda t: merge({"%throat": 1.0 + 1.1 * t, "body": (-10 * t, 0, 0), "%body": (1, 1, 1 + 0.04 * t)},
                            lids(62 * t), arm_pose(body=-10 * t))
    rig.action("home", {0: {}, 4: crouch, 8: merge(apex, leg_pose(thigh=-120, shin=-50, foot=-160, body=-2), {"@root": (0, 0, 0.14)}), 12: land, 16: {},
                        22: croak(1), 27: croak(0.2), 32: croak(1), 38: croak(0.1), 44: croak(1), 52: croak(0.3),
                        60: {}})
    rig.save(name)


def frog():
    frog_model("frog", "frog", {"skin": (0.16, 0.52, 0.03), "spot": (0.05, 0.24, 0.02), "belly": (0.98, 0.9, 0.6),
                                "throat": (1.0, 0.92, 0.62), "mouth": (0.07, 0.14, 0.04), "cheek": (1.0, 0.42, 0.3)})


def lady_frog():
    frog_model("lady_frog", "lady", {"skin": (0.95, 0.28, 0.48), "spot": (0.7, 0.1, 0.3),
                                     "belly": (1.0, 0.9, 0.86), "throat": (1.0, 0.85, 0.88),
                                     "mouth": (0.35, 0.05, 0.12), "cheek": (1.0, 0.25, 0.35)}, lady=True)


# ------------------------------------------------------------------ vehicles (built facing +X)

def vmats(n, paint, glass=(0.05, 0.11, 0.16)):
    return dict(paint=mat(n + "_paint", paint, 0.3, coat=0.8),
                glass=mat(n + "_glass", glass, 0.06, coat=1.0, emit=0.05),
                tyre=mat(n + "_tyre", (0.06, 0.055, 0.06), 0.75),
                hub=mat(n + "_hub", (0.85, 0.84, 0.8), 0.3, 0.6),
                chrome=mat(n + "_chrome", (0.9, 0.9, 0.92), 0.15, 1.0),
                glow=mat(n + "_glow", (1.0, 0.92, 0.65), 0.2, emit=6.0),
                tail=mat(n + "_tail", (0.9, 0.08, 0.05), 0.3, emit=2.0),
                dark=mat(n + "_dark", (0.08, 0.08, 0.1), 0.6))


def headlight(loc, M, r=0.05, rim=True):
    loc = Vector(loc)
    out = [sphere(r, loc, M["glow"], scale=(0.5, 1, 1), segs=12, rings=8)]
    if rim:
        out.append(torus(r, r * 0.22, loc - Vector((0.005, 0, 0)), M["chrome"], rot=(0, R90, 0), verts=14, minor=5))
    return out


def export_vehicle(parts, wheels, name):
    root = join(parts, name)
    export(root, name, [(w, root) for w in wheels])


def car_a():
    M = vmats("car_a", (0.92, 0.1, 0.04))
    cream = mat("car_a_trim", (0.98, 0.9, 0.75), 0.4, coat=0.5)
    parts = [soap(-0.6, 0.6, 0.33, 0.15, 0.27, M["paint"], r=0.22, p=3.2,
                  taper=lambda x: (1.0, 1.0 - 0.1 * (x / 0.6) ** 2, 0.0)),
             soap(-0.36, 0.2, 0.285, 0.13, 0.44, M["glass"], r=0.15, p=2.6),
             soap(-0.34, 0.16, 0.295, 0.045, 0.565, M["paint"], r=0.13, p=2.6),
             # a cream belt line and bumpers
             soap(-0.62, 0.62, 0.34, 0.022, 0.3, cream, r=0.2, p=4)]
    for x in (0.6, -0.6):
        parts.append(rod((x, -0.26, 0.16), (x, 0.26, 0.16), 0.03, M["chrome"], verts=10))
    for s in (1, -1):
        parts += headlight((0.56, 0.2 * s, 0.34), M, 0.055)
        parts.append(sphere(0.035, (-0.59, 0.22 * s, 0.34), M["tail"], scale=(0.5, 1, 1.2), segs=10, rings=6))
        parts.append(rod((0.1, 0.33 * s, 0.34), (0.03, 0.33 * s, 0.34), 0.012, M["chrome"], verts=6))  # door handle
    # a spare wheel on the tail
    sp = torus(0.075, 0.035, (-0.64, 0, 0.33), M["tyre"], rot=(0, R90, 0), verts=16, minor=6)
    parts += [sp, cyl(0.07, 0.05, (-0.64, 0, 0.33), cream, rot=(0, R90, 0), verts=12)]
    # wheel arches: dark shadows behind the wheels
    wheels = []
    for i, (x, y) in enumerate(((0.37, 0.29), (0.37, -0.29), (-0.37, 0.29), (-0.37, -0.29))):
        parts.append(ell((x, y * 0.97, 0.16), (0.16, 0.05, 0.12), M["dark"], segs=14, rings=8))
        wheels.append(wheel(0.13, 0.11, (x, y, 0.13), M["tyre"], M["hub"], "wheel_%d" % i, cap=cream))
    export_vehicle(parts, wheels, "car_a")


def car_b():
    M = vmats("car_b", (0.02, 0.42, 0.48))
    cream = mat("car_b_trim", (0.98, 0.93, 0.8), 0.4, coat=0.5)
    wood = mat("car_b_crate", (0.78, 0.55, 0.3), 0.7)
    fruit = [mat("car_b_fruit_a", (1.0, 0.45, 0.05), 0.4, coat=0.5), mat("car_b_fruit_b", (0.55, 0.85, 0.15), 0.4,
                                                                          coat=0.5)]
    parts = [soap(-0.8, 0.8, 0.35, 0.18, 0.33, M["paint"], r=0.16, p=3.5),
             soap(-0.78, 0.48, 0.34, 0.17, 0.63, cream, r=0.14, p=3.5,
                  taper=lambda x: (1.0, 1.0, 0.0)),
             soap(-0.74, 0.52, 0.345, 0.075, 0.62, M["glass"], r=0.15, p=3.5)]
    # windscreen: a sloped glass slab between the hood and the roof
    parts.append(prism([(0.44, 0.5), (0.62, 0.5), (0.5, 0.78), (0.4, 0.78)], 0.62, (0, 0, 0), M["glass"], bevel=0.03))
    parts.append(soap(-0.8, 0.52, 0.355, 0.035, 0.8, M["paint"], r=0.12, p=4))  # roof
    for x in (0.8, -0.8):
        parts.append(rod((x, -0.28, 0.17), (x, 0.28, 0.17), 0.035, M["chrome"], verts=10))
    for s in (1, -1):
        parts += headlight((0.77, 0.22 * s, 0.36), M, 0.06)
        parts.append(box((0.03, 0.08, 0.1), (-0.8, 0.25 * s, 0.38), M["tail"], bevel=0.012))
        parts.append(box((0.02, 0.012, 0.3), (0.05, 0.355 * s, 0.33), M["dark"], bevel=0.004))  # sliding door line
    # grille
    parts.append(box((0.03, 0.26, 0.1), (0.8, 0, 0.3), M["chrome"], bevel=0.015))
    # roof rack with two crates of fruit
    for x in (-0.55, 0.25):
        parts.append(rod((x, -0.3, 0.86), (x, 0.3, 0.86), 0.012, M["chrome"], verts=6))
    for y in (-0.3, 0.3):
        parts.append(rod((-0.65, y, 0.86), (0.35, y, 0.86), 0.012, M["chrome"], verts=6))
    rnd = random.Random(7)
    for cx, fm in ((-0.37, fruit[0]), (0.07, fruit[1])):
        parts.append(box((0.36, 0.42, 0.14), (cx, 0, 0.94), wood, bevel=0.015))
        for i in range(3):
            for j in range(3):
                parts.append(sphere(0.055, (cx - 0.11 + 0.11 * i + rnd.uniform(-0.01, 0.01),
                                            -0.13 + 0.13 * j + rnd.uniform(-0.01, 0.01), 1.02), fm, segs=10, rings=6))
    wheels = []
    for i, (x, y) in enumerate(((0.52, 0.3), (0.52, -0.3), (-0.52, 0.3), (-0.52, -0.3))):
        parts.append(ell((x, y * 0.97, 0.17), (0.18, 0.05, 0.13), M["dark"], segs=14, rings=8))
        wheels.append(wheel(0.15, 0.12, (x, y, 0.15), M["tyre"], M["hub"], "wheel_%d" % i, cap=cream))
    export_vehicle(parts, wheels, "car_b")


def truck():
    M = vmats("truck", (0.04, 0.2, 0.8))
    boxm = mat("truck_box", (0.97, 0.9, 0.75), 0.5, coat=0.3)
    panel = mat("truck_panel", (0.95, 0.55, 0.12), 0.45, coat=0.4)
    emb = mat("truck_emblem", (1.0, 0.95, 0.85), 0.4, coat=0.3)
    parts = [box((2.3, 0.62, 0.12), (-0.1, 0, 0.22), M["dark"], bevel=0.02),        # chassis
             soap(0.62, 1.3, 0.37, 0.19, 0.35, M["paint"], r=0.14, p=3.5),         # hood
             soap(0.6, 1.08, 0.365, 0.24, 0.72, M["paint"], r=0.12, p=3.5),        # cab
             soap(0.595, 1.09, 0.373, 0.09, 0.75, M["glass"], r=0.125, p=3.5),
             soap(0.58, 1.05, 0.375, 0.04, 0.96, M["paint"], r=0.1, p=4),
             box((1.86, 0.78, 0.84), (-0.36, 0, 0.72), boxm, bevel=0.06, segs=3)]  # cargo box
    for s in (1, -1):
        parts.append(box((1.4, 0.02, 0.5), (-0.36, 0.39 * s, 0.74), panel, bevel=0.01))
        # emblem: a round sun of dots on the panel
        for k in range(8):
            a = 2 * math.pi * k / 8
            parts.append(cyl(0.035, 0.02, (-0.36 + 0.16 * math.cos(a), 0.4 * s, 0.74 + 0.16 * math.sin(a)), emb,
                             rot=(R90, 0, 0), verts=10))
        parts.append(cyl(0.1, 0.02, (-0.36, 0.4 * s, 0.74), emb, rot=(R90, 0, 0), verts=16))
        parts += headlight((1.28, 0.24 * s, 0.4), M, 0.06)
        parts.append(box((0.03, 0.08, 0.12), (-1.3, 0.3 * s, 0.4), M["tail"], bevel=0.012))
        parts.append(rod((1.1, 0.37 * s, 0.82), (1.1, 0.46 * s, 0.84), 0.012, M["chrome"], verts=6))  # mirror arm
        parts.append(box((0.04, 0.05, 0.1), (1.1, 0.47 * s, 0.84), M["chrome"], bevel=0.012))
        parts.append(box((0.3, 0.06, 0.035), (0.84, 0.36 * s, 0.2), M["chrome"], bevel=0.01))  # step
    # back doors, grille, bumpers
    parts.append(box((0.02, 0.01, 0.76), (-1.3, 0, 0.72), M["dark"], bevel=0.0))
    for z in (0.5, 0.95):
        parts.append(box((0.03, 0.7, 0.03), (-1.3, 0, z), M["chrome"], bevel=0.01))
    parts.append(box((0.03, 0.34, 0.14), (1.3, 0, 0.31), M["chrome"], bevel=0.015))
    parts.append(rod((1.32, -0.33, 0.17), (1.32, 0.33, 0.17), 0.035, M["chrome"], verts=10))
    parts.append(box((0.06, 0.7, 0.06), (-1.3, 0, 0.2), M["dark"], bevel=0.01))
    parts.append(cyl(0.035, 0.28, (0.58, 0.33, 1.0), M["chrome"], verts=10))  # exhaust stack
    wheels = []
    for i, (x, y) in enumerate(((0.92, 0.3), (0.92, -0.3), (-0.58, 0.3), (-0.58, -0.3), (-0.92, 0.3), (-0.92, -0.3))):
        wheels.append(wheel(0.16, 0.13, (x, y, 0.16), M["tyre"], M["hub"], "wheel_%d" % i))
    export_vehicle(parts, wheels, "truck")


def bulldozer():
    M = vmats("bulldozer", (1.0, 0.52, 0.0))
    steel = mat("bulldozer_blade", (0.22, 0.22, 0.24), 0.4, 0.7)
    track = mat("bulldozer_track", (0.08, 0.075, 0.07), 0.8)
    beacon = mat("bulldozer_beacon", (1.0, 0.45, 0.05), 0.3, emit=5.0)
    stripe = mat("bulldozer_stripe", (0.08, 0.08, 0.09), 0.5)
    parts = []
    for s in (1, -1):
        y = 0.27 * s
        parts.append(soap(-0.62, 0.45, 0.1, 0.13, 0.14, track, r=0.13, p=4))
        parts[-1].data.transform(Matrix.Translation((0, y, 0)))
        for k in range(13):  # treads over the top and along the outer side
            x = -0.52 + 0.08 * k
            parts.append(box((0.03, 0.2, 0.02), (x, y, 0.275), track, bevel=0.006))
        for x in (-0.45, -0.18, 0.1, 0.33):
            parts.append(cyl(0.075, 0.03, (x, y + 0.095 * s, 0.13), M["hub"], rot=(R90, 0, 0), verts=14, bevel=0.01))
        parts.append(box((1.05, 0.06, 0.03), (-0.085, y, 0.28), M["paint"], bevel=0.01))  # track guard
    parts += [box((0.9, 0.46, 0.3), (-0.12, 0, 0.42), M["paint"], bevel=0.06, segs=3),   # body
              box((0.36, 0.44, 0.2), (0.2, 0, 0.62), M["paint"], bevel=0.05, segs=3),     # engine hood
              box((0.02, 0.3, 0.12), (0.39, 0, 0.6), M["dark"], bevel=0.01)]            # grille
    for k in range(3):
        parts.append(box((0.025, 0.3, 0.015), (0.4, 0, 0.56 + 0.04 * k), M["chrome"], bevel=0.004))
    parts.append(box((0.9, 0.47, 0.04), (-0.12, 0, 0.36), stripe, bevel=0.01))
    # cab: glass box with pillars and a roof
    parts.append(box((0.4, 0.4, 0.36), (-0.28, 0, 0.75), M["glass"], bevel=0.03))
    for x in (-0.47, -0.09):
        for s in (1, -1):
            parts.append(box((0.04, 0.04, 0.38), (x, 0.2 * s, 0.75), M["paint"], bevel=0.012))
    parts.append(box((0.5, 0.48, 0.06), (-0.28, 0, 0.96), M["paint"], bevel=0.025))
    parts += [cyl(0.05, 0.08, (-0.28, 0, 1.02), M["dark"], verts=12),
              sphere(0.055, (-0.28, 0, 1.09), beacon, scale=(1, 1, 0.9), segs=12, rings=8)]
    parts.append(cyl(0.03, 0.34, (0.3, 0.14, 0.85), M["dark"], verts=10))  # exhaust
    parts.append(cyl(0.036, 0.04, (0.3, 0.14, 1.02), M["dark"], verts=10))
    for s in (1, -1):
        parts += headlight((-0.07, 0.17 * s, 0.9), M, 0.035)
        parts.append(box((0.03, 0.06, 0.05), (-0.58, 0.18 * s, 0.5), M["tail"], bevel=0.01))
    # the blade: a curved plate across the front on two push arms
    prof = []
    for k in range(9):
        a = math.radians(-60 + 120 * k / 8)
        prof.append((0.62 - 0.1 * math.cos(a) + 0.1, 0.2 + 0.17 * math.sin(a)))
    pts = prof + [(p[0] + 0.035, p[1]) for p in reversed(prof)]
    blade = prism([(x, z) for x, z in pts], 0.78, (0, 0, 0), steel, bevel=0.012)
    parts.append(blade)
    parts.append(box((0.03, 0.8, 0.035), (0.58, 0, 0.035), M["chrome"], bevel=0.008))  # cutting edge
    for s in (1, -1):
        parts.append(rod((0.1, 0.27 * s, 0.3), (0.58, 0.27 * s, 0.22), 0.028, M["paint"], verts=8))
        parts.append(rod((0.25, 0.2 * s, 0.55), (0.58, 0.25 * s, 0.33), 0.018, M["chrome"], verts=8))  # ram
    root = join(parts, "bulldozer")
    export(root, "bulldozer")


def racecar():
    M = vmats("racecar", (0.55, 0.05, 0.85))
    stripe = mat("racecar_stripe", (1.0, 0.97, 0.9), 0.35, coat=0.6)
    wing = mat("racecar_wing", (0.1, 0.1, 0.13), 0.4, coat=0.5)
    helmet = mat("racecar_helmet", (1.0, 0.85, 0.1), 0.25, coat=1.0)
    visor = mat("racecar_visor", (0.05, 0.08, 0.15), 0.05, coat=1.0, emit=0.2)
    taper = lambda x: (0.6 + 0.4 * (1 - max(0, x) / 0.6) if x > 0 else 1.0, 1.0 - 0.45 * max(0, x) / 0.6, -0.03 * max(0, x) / 0.6)
    parts = [soap(-0.5, 0.6, 0.17, 0.1, 0.19, M["paint"], r=0.1, p=3, taper=taper),                  # nose and tub
             soap(-0.45, 0.12, 0.28, 0.08, 0.17, M["paint"], r=0.1, p=3.5),                             # sidepods
             soap(-0.48, 0.55, 0.05, 0.103, 0.195, stripe, r=0.08, p=3, taper=taper),                   # centre stripe
             soap(-0.45, -0.12, 0.13, 0.12, 0.3, M["paint"], r=0.1, p=3),                                # engine cover
             sphere(0.085, (-0.02, 0, 0.35), helmet, segs=16, rings=10),
             sphere(0.07, (0.03, 0, 0.36), visor, scale=(0.75, 0.9, 0.5), segs=12, rings=8),
             ell((-0.02, 0, 0.27), (0.13, 0.13, 0.05), M["dark"], segs=14, rings=8)]                    # cockpit rim
    # roundel with a dot on each sidepod
    for s in (1, -1):
        parts.append(cyl(0.075, 0.02, (-0.17, 0.28 * s, 0.18), stripe, rot=(R90, 0, 0), verts=16))
        parts.append(cyl(0.035, 0.025, (-0.17, 0.28 * s, 0.18), M["dark"], rot=(R90, 0, 0), verts=12))
    # wings
    parts.append(box((0.14, 0.66, 0.025), (0.58, 0, 0.08), wing, bevel=0.008))
    for s in (1, -1):
        parts.append(box((0.16, 0.02, 0.08), (0.58, 0.33 * s, 0.09), M["paint"], bevel=0.006))
    parts.append(box((0.16, 0.62, 0.03), (-0.56, 0, 0.44), wing, bevel=0.008))
    for s in (1, -1):
        parts.append(box((0.18, 0.02, 0.16), (-0.56, 0.31 * s, 0.4), M["paint"], bevel=0.006))
        parts.append(rod((-0.5, 0.08 * s, 0.3), (-0.54, 0.08 * s, 0.43), 0.012, wing, verts=6))
        parts += headlight((0.6, 0.07 * s, 0.14), M, 0.028, rim=False)
    parts.append(box((0.03, 0.08, 0.05), (-0.62, 0, 0.18), M["tail"], bevel=0.008))
    # suspension arms
    wheels = []
    for i, (x, y, r, w) in enumerate(((0.38, 0.31, 0.12, 0.11), (0.38, -0.31, 0.12, 0.11),
                                      (-0.36, 0.3, 0.155, 0.15), (-0.36, -0.3, 0.155, 0.15))):
        parts.append(rod((x, 0.1 * (1 if y > 0 else -1), 0.17), (x, y * 0.8, r), 0.012, wing, verts=6))
        wheels.append(wheel(r, w, (x, y, r), M["tyre"], M["hub"], "wheel_%d" % i, cap=stripe))
    export_vehicle(parts, wheels, "racecar")


# ------------------------------------------------------------------ river riders

LOG_R = 0.29
LOG_Z = -0.09


def log(name, L, seed, shrooms=0):
    bark = mat("log_bark", (0.34, 0.2, 0.1), 0.85)
    wood = mat("log_wood", (0.92, 0.72, 0.45), 0.7)
    ring = mat("log_ring", (0.66, 0.44, 0.24), 0.75)
    moss = mat("log_moss", (0.35, 0.62, 0.14), 0.8, coat=0.1)
    cap = mat("log_cap", (0.92, 0.18, 0.1), 0.45, coat=0.5)
    dot = mat("log_dot", (1.0, 0.97, 0.9), 0.5)
    stem = mat("log_stem", (0.97, 0.93, 0.82), 0.6)
    rnd = random.Random(seed)
    n = 16
    x0, x1 = -L / 2 + 0.06, L / 2 - 0.06
    ns = max(4, int(L / 0.25))
    phase = [rnd.uniform(0, 6.28) for _ in range(4)]
    stations = []
    prof = []
    for k in range(n):
        a = 2 * math.pi * k / n
        prof.append((math.cos(a), math.sin(a)))
    bm = bmesh.new()
    rings = []
    for i in range(ns + 1):
        x = x0 + (x1 - x0) * i / ns
        bulge = 1.0 + 0.04 * math.sin(x * 1.7 + phase[0]) + 0.025 * math.sin(x * 4.1 + phase[1])
        ring_v = []
        for k, (c, s) in enumerate(prof):
            ridge = 1.0 + (0.045 if k % 2 == 0 else -0.01) + rnd.uniform(-0.012, 0.012)
            rr = LOG_R * bulge * ridge
            ring_v.append(bm.verts.new((x, c * rr, LOG_Z + s * rr)))
        rings.append(ring_v)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    # bark lips at the ends, then the cut faces
    ends = []
    for ring_v, sgn in ((rings[0], -1), (rings[-1], 1)):
        lip = [bm.verts.new(v.co + Vector((sgn * 0.05, 0, 0)) + (v.co - Vector((v.co.x, 0, LOG_Z))) * -0.08)
               for v in ring_v]
        for k in range(n):
            f = (ring_v[k], ring_v[(k + 1) % n], lip[(k + 1) % n], lip[k])
            bm.faces.new(f if sgn > 0 else f[::-1])
        ends.append((lip[0].co.x, sgn))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    body = new_obj("bark", bm, bark, smooth=0)
    K.select(body)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
    parts = [body]
    for x, sgn in ends:
        parts.append(cyl(LOG_R * 0.9, 0.02, (x - sgn * 0.005, 0, LOG_Z), wood, rot=(0, R90, 0), verts=n))
        for rr in (0.2, 0.42, 0.64):
            parts.append(torus(LOG_R * rr, 0.008, (x + sgn * 0.006, 0, LOG_Z), ring, rot=(0, R90, 0), verts=16, minor=3))
        parts.append(cyl(0.02, 0.012, (x + sgn * 0.006, 0, LOG_Z), ring, rot=(0, R90, 0), verts=8))
    # moss on top, knots on the sides
    for i in range(int(L * 2.2)):
        x = rnd.uniform(x0 + 0.15, x1 - 0.15)
        a = math.radians(rnd.uniform(40, 140))
        p = Vector((x, math.cos(a) * LOG_R * 1.0, LOG_Z + math.sin(a) * LOG_R * 1.0))
        o = lumpy(rnd.uniform(0.09, 0.16), (0, 0, 0), moss, seed * 100 + i, amount=0.2, scale=(1.4, 1.0, 0.28),
                  smooth=70)
        o.data.transform(Matrix.Rotation(a - R90, 4, "X"))
        o.data.transform(Matrix.Translation(p))
        parts.append(o)
    for i in range(int(L)):
        x = rnd.uniform(x0 + 0.3, x1 - 0.3)
        s = rnd.choice((-1, 1))
        a = math.radians(rnd.uniform(-10, 25))
        p = Vector((x, s * math.cos(a) * LOG_R, LOG_Z + math.sin(a) * LOG_R))
        parts.append(ell(p, (0.05, 0.03, 0.04), bark, segs=10, rings=6))
        parts.append(ell(p + Vector((0, s * 0.02, 0)), (0.028, 0.02, 0.022), ring, segs=8, rings=5))
    # a broken branch stub
    x = rnd.uniform(-L / 4, L / 4)
    parts.append(rod((x, 0.2, LOG_Z + 0.2), (x + 0.12, 0.36, LOG_Z + 0.3), 0.04, bark, r2=0.03, verts=8))
    parts.append(cyl(0.028, 0.01, (x + 0.12, 0.36, LOG_Z + 0.3), wood, rot=(-0.9, 0.5, 0), verts=8))
    # toadstools near one end (on the far side, so the frog's path stays clear)
    for i in range(shrooms):
        x = x1 - 0.35 - 0.16 * i
        a = math.radians(115 + 12 * i)
        base = Vector((x, math.cos(a) * LOG_R, LOG_Z + math.sin(a) * LOG_R))
        h = 0.08 - 0.02 * i
        top = base + Vector((0, -0.03, h))
        parts.append(rod(base, top, 0.016, stem, r2=0.013, verts=8))
        parts.append(hemi(0.05 - 0.01 * i, top, (0, 0, 1), cap, cut=-0.1, segs=14, rings=8))
        for k in range(4):
            aa = 2 * math.pi * k / 4 + 0.4
            parts.append(sphere(0.008, top + Vector((math.cos(aa) * 0.03, math.sin(aa) * 0.03, 0.03 - 0.008 * i)), dot,
                                segs=6, rings=4))
    simple(parts, name)


def log_short():
    log("log_short", 3.0, 3)


def log_mid():
    log("log_mid", 4.0, 4, shrooms=2)


def log_long():
    log("log_long", 6.0, 6, shrooms=3)


def turtle():
    shell = mat("turtle_shell", (0.2, 0.42, 0.25), 0.4, coat=0.6)
    scute = mat("turtle_scute", (0.55, 0.62, 0.22), 0.45, coat=0.5)
    rim = mat("turtle_rim", (0.95, 0.72, 0.3), 0.5, coat=0.3)
    skin = mat("turtle_skin", (0.45, 0.72, 0.4), 0.5, coat=0.2)
    eye_m = mat("turtle_eye", (0.02, 0.02, 0.03), 0.1, coat=1.0)
    shine = mat("turtle_shine", (1, 1, 1), 0.2, emit=4.0)
    cheek = mat("turtle_cheek", (1.0, 0.5, 0.4), 0.6)
    # built facing -Y; the rig turns it to face +X
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "shell": ((0, 0.05, 0.05), (0, -0.2, 0.05), "root"),
         "head": ((0, -0.26, 0.04), (0, -0.44, 0.07), "shell")}
    for s, side in ((1, "L"), (-1, "R")):
        B["fin." + side] = ((0.2 * s, -0.16, 0.0), (0.4 * s, -0.2, -0.02), "shell")
        B["back." + side] = ((0.18 * s, 0.18, -0.01), (0.28 * s, 0.3, -0.02), "shell")
    rig = TurnRig(B, 90, fps=30)
    C = Vector((0, 0.0, 0.02))
    dome = hemi(1.0, (0, 0, 0), (0, 0, 1), shell, cut=-0.02, segs=28, rings=16)
    dome.data.transform(Matrix.Diagonal((0.3, 0.34, 0.21, 1)))
    dome.data.transform(Matrix.Translation(C))
    rig.rigid("shell", dome,
              torus(1.0, 0.07, C + Vector((0, 0, 0.0)), rim, verts=28, minor=6, scale=(0.305, 0.345, 0.3)),
              ell(C + Vector((0, 0, -0.02)), (0.28, 0.32, 0.06), skin, segs=20, rings=8))
    # scutes: a spine row and a ring of plates, slightly raised
    def on_dome(dx, dy):
        z = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
        return C + Vector((dx * 0.3, dy * 0.34, z * 0.21)), Vector((dx / 0.3, dy / 0.34, z / 0.21)).normalized()
    for dx, dy, r in ((0, 0, 0.085), (0, -0.55, 0.06), (0, 0.55, 0.06)) + tuple(
            (0.62 * math.cos(a), 0.62 * math.sin(a), 0.055) for a in [2 * math.pi * k / 8 + math.pi / 8 for k in range(8)]):
        p, nrm = on_dome(dx, dy)
        o = cyl(r, 0.02, (0, 0, 0), scute, verts=6, bevel=0.006, segs=1)
        o.data.transform(Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4())
        o.data.transform(Matrix.Translation(p))
        rig.rigid("shell", o)
    # head: round, smiling, two big eyes
    hc = Vector((0, -0.4, 0.075))
    rig.rigid("head", limb([(0, -0.2, 0.02), (0, -0.3, 0.04), hc], [0.06, 0.055, 0.05], skin, verts=10, per=2),
              ell(hc, (0.085, 0.095, 0.075), skin, -10, segs=16, rings=10))
    for s in (1, -1):
        e = hc + Vector((0.055 * s, -0.045, 0.03))
        rig.rigid("head", sphere(0.022, e, eye_m, segs=10, rings=6),
                  sphere(0.007, e + Vector((0.006 * s, -0.016, 0.012)), shine, segs=6, rings=4),
                  blob(0.018, hc + Vector((0.07 * s, -0.05, -0.012)), cheek, (1.2, 0.3, 0.8),
                       (0.8 * s, -0.6, 0), segs=8, rings=5))
    rig.rigid("head", tube([hc + Vector((-0.03, -0.085, -0.02)), hc + Vector((0, -0.094, -0.028)),
                            hc + Vector((0.03, -0.085, -0.02))], [0.005, 0.006, 0.005], eye_m, verts=5))
    for s, side in ((1, "L"), (-1, "R")):
        f = ell((0.3 * s, -0.19, -0.01), (0.13, 0.055, 0.02), skin, yaw=-20 * s, segs=14, rings=6)
        rig.rigid("fin." + side, f)
        b = ell((0.22 * s, 0.24, -0.015), (0.07, 0.045, 0.018), skin, yaw=35 * s, segs=12, rings=6)
        rig.rigid("back." + side, b)
    rig.rigid("shell", ell((0, 0.35, -0.01), (0.03, 0.06, 0.02), skin, segs=8, rings=5))  # tail
    rig.build("turtle")

    def paddle(t):
        a = 2 * math.pi * t
        return merge({"fin.L": (0, 18 * math.cos(a), 30 * math.sin(a)), "back.L": (0, 0, -20 * math.sin(a))},
                     {"head": (6 * math.sin(2 * a), 0, 5 * math.sin(a)), "@root": (0, 0, 0.012 * math.sin(2 * a)),
                      "shell": (1.5 * math.sin(2 * a + 1), 2.5 * math.sin(a), 0)})

    def mp(p):
        return mirror(p)
    rig.action("swim", {int(30 * k / 6): mp(paddle(k / 6)) for k in range(7)}, loop=True)
    down = lambda z, pitch, tuck: mirror({"@root": (0, 0, z), "shell": (pitch, 0, 0), "head": (tuck, 0, 0),
                                          "fin.L": (0, -30, -35), "back.L": (0, 0, 20)})
    rig.action("dive", {0: mp(paddle(0)), 5: down(-0.05, 12, 20), 12: down(-0.45, 6, 15), 18: down(-0.45, -4, 10),
                        25: down(-0.1, -8, -5), 30: mp(paddle(0))})
    rig.save("turtle")


def lilypad():
    leaf = mat("lilypad_leaf", (0.24, 0.55, 0.14), 0.45, coat=0.5)
    vein = mat("lilypad_vein", (0.45, 0.72, 0.25), 0.5, coat=0.3)
    under = mat("lilypad_under", (0.55, 0.2, 0.25), 0.6)
    petal = mat("lilypad_petal", (1.0, 0.72, 0.82), 0.4, coat=0.3, emit=0.2)
    petal_in = mat("lilypad_petal_in", (1.0, 0.9, 0.93), 0.4, coat=0.3, emit=0.2)
    heart = mat("lilypad_heart", (1.0, 0.8, 0.15), 0.4, emit=1.2)
    R, n = 0.43, 40
    notch = math.radians(16)
    bm = bmesh.new()
    cen = bm.verts.new((0, 0, 0.012))
    rim_i, rim_o = [], []
    for k in range(n + 1):
        a = notch + (2 * math.pi - 2 * notch) * k / n - R90   # the notch points to -Y
        wob = 1 + 0.02 * math.sin(k * 1.7)
        rim_i.append(bm.verts.new((0.6 * R * math.cos(a), 0.6 * R * math.sin(a), 0.016)))
        rim_o.append(bm.verts.new((R * wob * math.cos(a), R * wob * math.sin(a), 0.024)))
    for k in range(n):
        bm.faces.new((cen, rim_i[k], rim_i[k + 1]))
        bm.faces.new((rim_i[k], rim_o[k], rim_o[k + 1], rim_i[k + 1]))
    bm.faces.new((cen, rim_o[0], rim_i[0]))
    bm.faces.new((cen, rim_i[n], rim_o[n]))
    pad = new_obj("pad", bm, leaf, smooth=70)
    mod = pad.modifiers.new("s", "SOLIDIFY")
    mod.thickness = 0.02
    K.select(pad)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    pad.data.materials.append(under)
    for p in pad.data.polygons:
        p.material_index = 1 if p.normal.z < -0.3 else 0
    parts = [pad]
    for k in range(9):
        a = notch + (2 * math.pi - 2 * notch) * (k + 0.5) / 9 - R90
        parts.append(rod((0.02 * math.cos(a), 0.02 * math.sin(a), 0.027), (0.37 * math.cos(a), 0.37 * math.sin(a), 0.03),
                         0.007, vein, r2=0.003, verts=4))
    # the flower on the rim (back-left), two rings of pointed petals
    c = Vector((-0.2, 0.18, 0.03))
    for ring_i, (cnt, ln, tilt, pm) in enumerate(((8, 0.1, 0.35, petal), (6, 0.075, 0.9, petal_in))):
        for k in range(cnt):
            a = 2 * math.pi * k / cnt + ring_i * 0.4
            o = sphere(1.0, (0, 0, 0), pm, scale=(ln, ln * 0.38, 0.02), segs=10, rings=6)
            o.data.transform(Matrix.Translation((ln * 0.9, 0, 0)))
            o.data.transform(Matrix.Rotation(-tilt, 4, "Y"))
            o.data.transform(Matrix.Rotation(a, 4, "Z"))
            o.data.transform(Matrix.Translation(c + Vector((0, 0, 0.01 + 0.015 * ring_i))))
            parts.append(o)
    parts.append(sphere(0.03, c + Vector((0, 0, 0.05)), heart, scale=(1, 1, 0.7), segs=10, rings=6))
    simple(parts, "lilypad")


def croc():
    skin = mat("croc_skin", (0.25, 0.5, 0.2), 0.5, coat=0.35)
    belly = mat("croc_belly", (0.8, 0.82, 0.5), 0.55)
    scute = mat("croc_scute", (0.15, 0.34, 0.12), 0.6, coat=0.2)
    tooth = mat("croc_tooth", (1.0, 0.98, 0.9), 0.3, coat=0.4)
    mouth = mat("croc_mouth", (0.85, 0.3, 0.3), 0.5)
    eye_m = mat("croc_eye", (1.0, 0.82, 0.15), 0.2, coat=0.8, emit=0.6)
    pupil = mat("croc_pupil", (0.02, 0.02, 0.02), 0.2)
    # built facing -Y (snout at y = -1.5, tail tip at +1.5), turned to face +X
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0.7, 0.02), (0, -0.7, 0.02), "root"),
         "head": ((0, -0.72, 0.06), (0, -1.5, 0.06), "body"),
         "jaw": ((0, -0.72, -0.0), (0, -1.45, -0.02), "body"),
         "tail1": ((0, 0.65, 0.02), (0, 1.0, 0.01), "body"),
         "tail2": ((0, 1.0, 0.01), (0, 1.28, 0.0), "tail1"),
         "tail3": ((0, 1.28, 0.0), (0, 1.5, 0.0), "tail2")}
    for s, side in ((1, "L"), (-1, "R")):
        B["leg." + side] = ((0.2 * s, -0.42, 0.0), (0.38 * s, -0.5, -0.06), "body")
        B["hind." + side] = ((0.2 * s, 0.45, 0.0), (0.38 * s, 0.38, -0.06), "body")
    rig = TurnRig(B, 90, fps=30)
    # body: a flat oval section lofted along Y, tapering into the tail
    prof = superellipse(1.0, 1.0, 20, 2.6)
    prof = [(x, z) for x, z in prof]
    def sec(y):
        # half width, half height, centre z along the body
        if y < -0.7:
            return 0.2, 0.1, 0.02
        if y < 0.6:
            t = (y + 0.7) / 1.3
            return 0.27 - 0.05 * (2 * t - 1) ** 2 - 0.02 * t, 0.13, 0.03
        t = (y - 0.6) / 0.9
        return 0.2 * (1 - t) + 0.02, 0.1 * (1 - t) + 0.02, 0.02 - 0.015 * t
    ys = [-0.78, -0.7, -0.55, -0.35, -0.1, 0.15, 0.4, 0.6, 0.8, 1.0, 1.15, 1.3, 1.42, 1.5]
    bodies = {"body": [], "tail1": [], "tail2": [], "tail3": []}
    st = [(y, sec(y)[0], sec(y)[1], sec(y)[2]) for y in ys]
    trunk = loft_y(prof, st, skin, cap_start=True, cap_end=True, name="trunk", smooth=60)
    trunk.data.materials.append(belly)
    for p in trunk.data.polygons:
        p.material_index = 1 if p.normal.z < -0.55 else 0
    def tail_w(p):
        y = p.y
        pts = [("body", 0.5), ("tail1", 0.85), ("tail2", 1.15), ("tail3", 1.42)]
        w = {}
        for b, yc in pts:
            w[b] = math.exp(-((y - yc) / 0.14) ** 2) + 1e-6
        if y < 0.5:
            return {"body": 1.0}
        return w
    rig.custom(tail_w, trunk)
    # back scutes: two rows of bumps and a tail crest
    for i in range(12):
        y = -0.55 + 0.1 * i
        for s in (1, -1):
            hw, hh, zc = sec(y)
            rig.custom(tail_w, ell((0.09 * s, y, zc + hh * 0.92), (0.035, 0.04, 0.03), scute, segs=8, rings=5))
    for i in range(9):
        y = 0.7 + 0.09 * i
        hw, hh, zc = sec(y)
        o = prism([(-0.035, 0), (0.035, 0), (0, 0.06 - 0.004 * i)], 0.012, (0, 0, 0), scute, rot=(0, 0, R90),
                  bevel=0.004)
        o.data.transform(Matrix.Translation((0, y, zc + hh * 0.9)))
        rig.custom(tail_w, o)
    # head: upper jaw (skull and snout), lower jaw; teeth along both
    snout = [(-0.72, 0.19, 0.1, 0.07), (-0.82, 0.19, 0.11, 0.07), (-0.95, 0.15, 0.08, 0.06), (-1.15, 0.12, 0.06, 0.05),
             (-1.35, 0.11, 0.055, 0.05), (-1.46, 0.1, 0.05, 0.05), (-1.5, 0.07, 0.035, 0.05)]
    up = loft_y(superellipse(1.0, 1.0, 18, 2.6), snout, skin, cap_start=True, cap_end=True, name="snout", smooth=60)
    rig.rigid("head", up)
    jawst = [(-0.72, 0.18, 0.05, 0.0), (-0.9, 0.14, 0.045, -0.005), (-1.2, 0.11, 0.035, -0.01),
             (-1.42, 0.095, 0.03, -0.01), (-1.46, 0.07, 0.022, -0.01)]
    jaw = loft_y(superellipse(1.0, 1.0, 16, 2.6), jawst, skin, cap_start=True, cap_end=True, name="jaw", smooth=60)
    jaw.data.materials.append(mouth)
    for p in jaw.data.polygons:
        p.material_index = 1 if p.normal.z > 0.6 else 0
    rig.rigid("jaw", jaw)
    for i in range(7):
        y = -0.88 - 0.085 * i
        w = 0.105 if y < -1.0 else 0.13
        for s in (1, -1):
            rig.rigid("head", rod((w * s, y, 0.03), (w * s, y, -0.012), 0.011, tooth, r2=0.001, verts=5))
            if i % 2 == 0:
                rig.rigid("jaw", rod((w * 0.9 * s, y - 0.04, 0.01), (w * 0.9 * s, y - 0.04, 0.05), 0.01, tooth,
                                     r2=0.001, verts=5))
    for s in (1, -1):
        e = Vector((0.1 * s, -0.8, 0.17))
        rig.rigid("head", sphere(0.06, e + Vector((0, 0.01, -0.02)), skin, segs=12, rings=8),
                  sphere(0.045, e, eye_m, segs=12, rings=8),
                  sphere(0.02, e + Vector((0.006 * s, -0.032, 0.012)), pupil, scale=(0.4, 0.6, 1.4), segs=8, rings=5),
                  hemi(0.049, e, (0, 0.5, 0.9), skin, cut=0.1, segs=12, rings=8),
                  sphere(0.02, (0.04 * s, -1.44, 0.1), scute, segs=8, rings=5))
    # stubby legs, sprawled
    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("leg." + side, limb([(0.18 * s, -0.42, 0.02), (0.3 * s, -0.46, -0.02), (0.36 * s, -0.5, -0.07)],
                                      [0.06, 0.05, 0.045], skin, verts=10, per=2, caps=True),
                  ell((0.39 * s, -0.53, -0.09), (0.06, 0.07, 0.02), skin, segs=10, rings=5))
        rig.rigid("hind." + side, limb([(0.18 * s, 0.45, 0.02), (0.3 * s, 0.42, -0.02), (0.36 * s, 0.38, -0.07)],
                                       [0.07, 0.055, 0.045], skin, verts=10, per=2, caps=True),
                  ell((0.39 * s, 0.35, -0.09), (0.06, 0.07, 0.02), skin, segs=10, rings=5))
    rig.build("croc")

    def sway(t, head=0.0, jaw=0.0):
        a = 2 * math.pi * t
        return {"tail1": (0, 0, 10 * math.sin(a)), "tail2": (0, 0, 14 * math.sin(a - 0.8)),
                "tail3": (0, 0, 18 * math.sin(a - 1.6)), "body": (0, 0, -2 * math.sin(a)),
                "head": (-head, 0, 2 * math.sin(a)), "jaw": (jaw, 0, 2 * math.sin(a)),
                "leg.L": (0, 0, 10 * math.sin(a)), "leg.R": (0, 0, 10 * math.sin(a)),
                "hind.L": (0, 0, -10 * math.sin(a)), "hind.R": (0, 0, -10 * math.sin(a)),
                "@root": (0, 0, 0.01 * math.sin(2 * a))}
    N = 48
    keys = {0: sway(0), 12: sway(0.25), 20: sway(20 / N, 4, 2), 27: sway(27 / N, 30, 10), 32: sway(32 / N, -2, -1),
            34: sway(34 / N, 0, 0), 38: sway(38 / N, 8, 3), 42: sway(42 / N, 0, 0), 48: sway(1.0)}
    rig.action("snap", keys, loop=True)
    rig.save("croc")


# ------------------------------------------------------------------ scenery

def hedge_mats():
    return (mat("hedge_leaf", (0.16, 0.4, 0.12), 0.7, coat=0.2),
            mat("hedge_leaf_light", (0.3, 0.56, 0.16), 0.65, coat=0.2),
            mat("hedge_flower", (1.0, 0.6, 0.72), 0.5, emit=0.3),
            mat("hedge_flower_heart", (1.0, 0.85, 0.3), 0.4, emit=0.8),
            mat("hedge_stone", (0.72, 0.64, 0.54), 0.8))


def hedge_mass(x0, x1, y0, y1, h, seed, flowers=5):
    """A trimmed hedge from x0..x1, y0..y1: a rounded core with leafy lumps on the top and the faces."""
    leaf, leaf2, fl, fh, stone = hedge_mats()
    J = random.Random(seed)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    parts = [box((x1 - x0, y1 - y0, h - 0.12), (cx, cy, 0.12 + (h - 0.12) / 2), leaf, bevel=0.1, segs=2),
             box((x1 - x0, y1 - y0 + 0.04, 0.14), (cx, cy - 0.02, 0.07), stone, bevel=0.025, segs=1),
             box((x1 - x0, y1 - y0, 0.6), (cx, cy, -0.3), stone, bevel=0.0)]   # footing, down into the water
    nx = max(2, int((x1 - x0) / 0.24) + 1)
    ny = max(2, int((y1 - y0) / 0.28) + 1)
    for i in range(nx):
        for j in range(ny):
            x = x0 + 0.1 + (x1 - x0 - 0.2) * i / (nx - 1) + J.uniform(-0.03, 0.03)
            y = y0 + 0.12 + (y1 - y0 - 0.24) * j / (ny - 1) + J.uniform(-0.03, 0.03)
            parts.append(lumpy(J.uniform(0.1, 0.14), (x, y, h - 0.03), leaf2 if (i + j) % 2 else leaf, seed * 50 + i * 7 + j,
                               amount=0.16, scale=(1, 1, 0.55), sub=1, smooth=70))
    # the front face: a row of lumps
    for i in range(nx):
        x = x0 + 0.1 + (x1 - x0 - 0.2) * i / (nx - 1)
        for z in (0.3, 0.52):
            parts.append(lumpy(J.uniform(0.09, 0.12), (x + J.uniform(-0.04, 0.04), y0 + 0.02, z + J.uniform(-0.04, 0.04)),
                               leaf2 if J.random() < 0.4 else leaf, seed * 90 + i * 3 + int(z * 10), amount=0.16,
                               scale=(1, 0.5, 1), sub=1, smooth=70))
    for k in range(flowers):
        x = J.uniform(x0 + 0.08, x1 - 0.08)
        z = J.uniform(0.28, h - 0.08)
        parts += flower((x, y0 - 0.035, z), fl, fh, r=0.03, n=5, tilt=0.2, seg=6)
        for o in parts[-6:]:  # turn the flower to face -Y
            c = Vector((x, y0 - 0.035, z))
            o.data.transform(Matrix.Translation(-c))
            o.data.transform(Matrix.Rotation(R90, 4, "X"))
            o.data.transform(Matrix.Translation(c))
    return parts


HEDGE_H = 0.72


def hedge_block():
    simple(hedge_mass(-0.5, 0.5, -0.5, 1.0, HEDGE_H, 12, flowers=3), "hedge_block")


def home_bay():
    leaf, leaf2, fl, fh, stone = hedge_mats()
    water = mat("home_bay_water", (0.1, 0.35, 0.45), 0.05, coat=1.0, emit=0.05)
    pad = mat("home_bay_pad", (0.26, 0.58, 0.16), 0.45, coat=0.5)
    vein = mat("home_bay_vein", (0.45, 0.72, 0.25), 0.5)
    reed = mat("home_bay_reed", (0.4, 0.62, 0.18), 0.6)
    cattail = mat("home_bay_cattail", (0.42, 0.24, 0.1), 0.8)
    wood = mat("home_bay_arch", (0.95, 0.9, 0.8), 0.5, coat=0.3)
    glow = mat("home_bay_glow", (1.0, 0.8, 0.4), 0.3, emit=4.0)
    parts = hedge_mass(-0.5, 0.5, 0.5, 1.0, HEDGE_H, 21, flowers=2)
    # stone basin: a rim on the sides and at the back; the front stays open to the river
    for x in (-0.47, 0.47):
        parts.append(box((0.08, 1.0, 0.12), (x, 0.0, 0.0), stone, bevel=0.02, segs=1))
    parts.append(box((1.0, 0.08, 0.12), (0, 0.46, 0.0), stone, bevel=0.02, segs=1))
    for x in (-0.47, 0.47):  # the basin walls drop into the water
        parts.append(box((0.06, 1.0, 0.5), (x, 0.0, -0.3), stone, bevel=0.01, segs=1))
    parts.append(box((1.0, 0.06, 0.5), (0, 0.47, -0.3), stone, bevel=0.01, segs=1))
    # the big lily pad (the frog's seat: top at z = 0)
    bm = bmesh.new()
    n = 32
    cen = bm.verts.new((0, 0, -0.005))
    rim = []
    notch = math.radians(14)
    for k in range(n + 1):
        a = notch + (2 * math.pi - 2 * notch) * k / n + R90   # the notch points back (+Y)
        rim.append(bm.verts.new((0.4 * math.cos(a), 0.38 * math.sin(a), -0.002 + 0.006 * math.sin(k * 1.3))))
    for k in range(n):
        bm.faces.new((cen, rim[k], rim[k + 1]))
    bm.faces.new((cen, rim[n], rim[0]))
    p = new_obj("pad", bm, pad, smooth=70)
    m = p.modifiers.new("s", "SOLIDIFY")
    m.thickness = 0.03
    K.select(p)
    bpy.ops.object.modifier_apply(modifier=m.name)
    parts.append(p)
    for k in range(8):
        a = notch + (2 * math.pi - 2 * notch) * (k + 0.5) / 8 + R90
        parts.append(rod((0.02 * math.cos(a), 0.02 * math.sin(a), 0.0), (0.34 * math.cos(a), 0.32 * math.sin(a), 0.002),
                         0.006, vein, r2=0.003, verts=4))
    # reeds and cattails in the back corners
    J = random.Random(5)
    for cx in (-0.36, 0.36):
        for k in range(6):
            b = Vector((cx + J.uniform(-0.06, 0.06), 0.36 + J.uniform(-0.05, 0.05), -0.05))
            h = J.uniform(0.45, 0.75)
            lean = Vector((J.uniform(-0.08, 0.08) - 0.08 * math.copysign(1, cx), J.uniform(-0.1, 0.0), h))
            parts.append(rod(b, b + lean, 0.012, reed, r2=0.002, verts=5))
        for k in range(2):
            b = Vector((cx + 0.04 * (k * 2 - 1), 0.4, -0.05))
            top = b + Vector((0.03 * (k * 2 - 1), -0.04, 0.62 + 0.1 * k))
            parts.append(rod(b, top, 0.008, reed, verts=5))
            parts.append(cyl(0.025, 0.13, top - Vector((0, 0, 0.1)), cattail, verts=8, bevel=0.01, segs=2))
    # the arch over the back of the nook, woven with flowers, a little lantern hanging from it
    pts = []
    for k in range(13):
        a = math.pi * k / 12
        pts.append(Vector((0.43 * math.cos(a), 0.5, 0.1 + 0.95 * math.sin(a) ** 0.8)))
    parts.append(tube(pts, [0.028] * len(pts), wood, verts=8))
    for k in range(1, 12):
        a = math.pi * k / 12
        c = Vector((0.43 * math.cos(a), 0.47, 0.1 + 0.95 * math.sin(a) ** 0.8))
        if k % 2 == 0:
            parts += flower(c + Vector((0, -0.02, 0)), fl, fh, r=0.035, n=5, tilt=0.2, seg=6)
            for o in parts[-6:]:
                o.data.transform(Matrix.Translation(-c))
                o.data.transform(Matrix.Rotation(R90, 4, "X"))
                o.data.transform(Matrix.Translation(c))
        else:
            parts.append(lumpy(0.05, c, leaf2, 300 + k, amount=0.2, scale=(1, 0.7, 1), smooth=70))
    lc = Vector((0, 0.5, 0.82))
    parts += [rod(lc + Vector((0, 0, 0.23)), lc + Vector((0, 0, 0.07)), 0.006, cattail, verts=4),
              cyl(0.04, 0.02, lc + Vector((0, 0, 0.065)), cattail, verts=8),
              sphere(0.035, lc, glow, scale=(1, 1, 1.3), segs=10, rings=6),
              cyl(0.03, 0.015, lc - Vector((0, 0, 0.05)), cattail, verts=8)]
    root = join(parts, "home_bay")
    pool = join([box((0.88, 0.94, 0.02), (0, -0.03, WATER - 0.01), water, bevel=0.0)], "pool")
    export(root, "home_bay", [(pool, root)])


def tile_base(top_m, side_m, h=0.3):
    """A 1 x 1 block, top at z = 0, sides down to -h; the top face is `top_m`, the rest `side_m`."""
    o = box((1.0, 1.0, h), (0, 0, -h / 2), side_m, bevel=0.0)
    o.data.materials.append(top_m)
    for p in o.data.polygons:
        p.material_index = 1 if p.normal.z > 0.5 else 0
    return o


def bank_tile():
    grass = mat("bank_grass", (0.3, 0.58, 0.14), 0.8)
    grass2 = mat("bank_grass_light", (0.46, 0.7, 0.2), 0.8)
    soil = mat("bank_soil", (0.4, 0.26, 0.14), 0.9)
    pebble = mat("bank_pebble", (0.78, 0.72, 0.64), 0.7)
    pebble2 = mat("bank_pebble_dark", (0.5, 0.48, 0.46), 0.7)
    kerb = mat("bank_kerb", (0.8, 0.77, 0.72), 0.7)
    fl = mat("bank_flower", (1.0, 0.95, 0.4), 0.5, emit=0.3)
    fh = mat("bank_flower_heart", (1.0, 0.6, 0.1), 0.5, emit=0.5)
    parts = [tile_base(grass, soil)]
    J = random.Random(11)
    # soft lighter patches
    for k in range(3):
        parts.append(ell((J.uniform(-0.35, 0.35), J.uniform(-0.35, 0.3), 0.0), (J.uniform(0.1, 0.16), J.uniform(0.08, 0.13), 0.012),
                         grass2, segs=12, rings=6))
    for k in range(7):
        p = (J.uniform(-0.42, 0.42), J.uniform(-0.42, 0.35), 0.0)
        parts.append(lumpy(J.uniform(0.022, 0.045), p, pebble if k % 3 else pebble2, 40 + k, amount=0.25,
                           scale=(1.2, 1, 0.55), smooth=0))
    for k in range(6):  # grass tufts
        c = Vector((J.uniform(-0.44, 0.44), J.uniform(-0.44, 0.36), 0))
        for b in range(4):
            a = 2 * math.pi * b / 4 + J.uniform(0, 1)
            parts.append(rod(c, c + Vector((0.025 * math.cos(a), 0.025 * math.sin(a), J.uniform(0.05, 0.08))), 0.009,
                             grass2 if b % 2 else grass, r2=0.001, verts=4))
    parts += flower((0.3, -0.25, 0.02), fl, fh, r=0.022, n=5, tilt=0.2, seg=6)
    parts += flower((-0.28, 0.12, 0.02), fl, fh, r=0.02, n=5, tilt=0.2, seg=6)
    parts.append(box((1.0, 0.1, 0.06), (0, 0.45, 0.01), kerb, bevel=0.015, segs=2))  # kerb along the road
    simple(parts, "bank_tile")


def median_tile():
    paver = mat("median_paver", (0.86, 0.72, 0.55), 0.75)
    paver2 = mat("median_paver_b", (0.76, 0.58, 0.44), 0.75)
    grout = mat("median_joint", (0.36, 0.3, 0.25), 0.9)
    kerb = mat("median_kerb", (0.8, 0.77, 0.72), 0.7)
    moss = mat("median_moss", (0.35, 0.58, 0.16), 0.8)
    parts = [tile_base(grout, grout)]
    parts[0].data.transform(Matrix.Translation((0, 0, -0.01)))
    J = random.Random(8)
    # herringbone-ish bricks: rows of 0.25 x 0.125 pavers, rows offset
    rows = 7
    y0 = -0.4
    h = (0.5 - y0) / rows
    for r in range(rows):
        y = y0 + h * (r + 0.5)
        off = 0.125 if r % 2 else 0.0
        x = -0.5 - off
        while x < 0.5:
            xa, xb = max(-0.5, x), min(0.5, x + 0.25)
            if xb - xa > 0.03:
                parts.append(box((xb - xa - 0.014, h - 0.014, 0.03), ((xa + xb) / 2, y, -0.012 + J.uniform(-0.002, 0.003)),
                                 paver2 if J.random() < 0.3 else paver, bevel=0.006, segs=1))
            x += 0.25
    parts.append(box((1.0, 0.1, 0.07), (0, -0.45, 0.0), kerb, bevel=0.015, segs=2))  # kerb along the road
    for k in range(4):  # moss in a few joints
        parts.append(ell((J.uniform(-0.45, 0.45), J.uniform(-0.35, 0.45), -0.004), (0.03, 0.012, 0.01), moss, segs=6,
                         rings=4))
    simple(parts, "median_tile")


def road_mats():
    return (mat("road_asphalt", (0.14, 0.14, 0.17), 0.85),
            mat("road_patch", (0.11, 0.11, 0.135), 0.9),
            mat("road_side", (0.1, 0.1, 0.12), 0.9),
            mat("road_line", (0.98, 0.9, 0.7), 0.6, emit=0.05))


def road_base(seed):
    asphalt, patch, side, line = road_mats()
    parts = [tile_base(asphalt, side)]
    J = random.Random(seed)
    for k in range(2):
        parts.append(ell((J.uniform(-0.3, 0.3), J.uniform(-0.3, 0.3), -0.004), (J.uniform(0.08, 0.14), J.uniform(0.05, 0.1), 0.006),
                         patch, segs=10, rings=5))
    for k in range(10):  # gravel specks
        parts.append(sphere(0.008, (J.uniform(-0.47, 0.47), J.uniform(-0.47, 0.47), -0.004), patch, segs=5, rings=3))
    return parts


def road_tile():
    simple(road_base(3), "road_tile")


def road_tile_line():
    asphalt, patch, side, line = road_mats()
    parts = road_base(4)
    parts.append(box((0.5, 0.05, 0.01), (0, 0.435, 0.0), line, bevel=0.004, segs=1))
    simple(parts, "road_tile_line")


def water_edge():
    stone = mat("water_edge_stone", (0.78, 0.7, 0.6), 0.75)
    stone2 = mat("water_edge_stone_b", (0.7, 0.62, 0.53), 0.75)
    brick = mat("water_edge_brick", (0.62, 0.32, 0.22), 0.85)
    joint = mat("water_edge_joint", (0.4, 0.33, 0.28), 0.9)
    algae = mat("water_edge_algae", (0.2, 0.4, 0.16), 0.8)
    parts = []
    # coping stones: two per metre, overhanging the water side (+Y)
    for i, x in enumerate((-0.25, 0.25)):
        parts.append(box((0.49, 0.26, 0.08), (x, 0.03, -0.02), stone if i == 0 else stone2, bevel=0.02, segs=2))
    # the wall: brick courses on a joint backing, facing +Y, down to -0.6
    parts.append(box((1.0, 0.06, 0.6), (0, 0.1, -0.35), joint, bevel=0.0))
    for r in range(6):
        z = -0.1 - 0.085 * (r + 0.5)
        off = 0.1 if r % 2 else 0.0
        x = -0.5 - off
        while x < 0.5:
            xa, xb = max(-0.5, x), min(0.5, x + 0.2)
            if xb - xa > 0.03:
                parts.append(box((xb - xa - 0.012, 0.03, 0.072), ((xa + xb) / 2, 0.138, z), brick, bevel=0.006, segs=1))
            x += 0.2
    # a band of algae near the waterline
    parts.append(box((1.0, 0.012, 0.06), (0, 0.157, WATER - 0.02), algae, bevel=0.0))
    simple(parts, "water_edge")


def lamp_post():
    iron = mat("lamp_post_iron", (0.08, 0.2, 0.16), 0.4, 0.5, coat=0.4)
    brass = mat("lamp_post_brass", (0.85, 0.62, 0.28), 0.3, 0.9)
    glow = mat("lamp_post_glow", (1.0, 0.78, 0.4), 0.3, emit=7.0)
    glass = mat("lamp_post_glass", (1.0, 0.92, 0.75), 0.1, emit=1.5, alpha=0.5)
    basket = mat("lamp_post_basket", (0.55, 0.36, 0.2), 0.8)
    fl = [mat("lamp_post_flower_a", (1.0, 0.3, 0.4), 0.5, emit=0.2), mat("lamp_post_flower_b", (1.0, 0.85, 0.3), 0.5,
                                                                          emit=0.2)]
    leaf = mat("lamp_post_leaf", (0.25, 0.52, 0.15), 0.7)
    parts = [lathe_r([(0.0, 0.3), (0.06, 0.3), (0.09, 0.22), (0.12, 0.1), (0.13, 0.04), (0.14, 0.0), (0.0, 0.0)], iron,
                     segs=12, smooth=40),
             cyl(0.035, 1.25, (0, 0, 0.9), iron, verts=10),
             torus(0.045, 0.012, (0, 0, 0.4), brass, verts=12, minor=4),
             torus(0.045, 0.012, (0, 0, 1.45), brass, verts=12, minor=4)]
    # lantern on top: base, four glass panes round the flame, a cap and a finial
    z0 = 1.55
    parts += [cyl(0.09, 0.04, (0, 0, z0), iron, verts=8, bevel=0.01),
              cyl(0.07, 0.24, (0, 0, z0 + 0.14), glass, r2=0.1, verts=4, bevel=0.0),
              sphere(0.045, (0, 0, z0 + 0.13), glow, scale=(1, 1, 1.3), segs=10, rings=6),
              cyl(0.13, 0.08, (0, 0, z0 + 0.3), iron, r2=0.02, verts=4, bevel=0.008),
              sphere(0.025, (0, 0, z0 + 0.36), brass, segs=8, rings=5)]
    parts[-4].data.transform(Matrix.Rotation(math.pi / 4, 4, "Z"))
    parts[-2].data.transform(Matrix.Rotation(math.pi / 4, 4, "Z"))
    for k in range(4):
        a = math.pi / 4 + k * R90
        parts.append(rod((0.07 * math.cos(a), 0.07 * math.sin(a), z0 + 0.02), (0.1 * math.cos(a), 0.1 * math.sin(a), z0 + 0.26),
                         0.008, iron, verts=4))
    # a curly arm with a hanging flower basket
    arm = [Vector((0, 0, 1.3)), Vector((0.12, 0, 1.36)), Vector((0.25, 0, 1.33)), Vector((0.3, 0, 1.28))]
    parts.append(tube(arm, [0.015] * 4, iron, verts=6))
    parts.append(rod((0.3, 0, 1.28), (0.3, 0, 1.12), 0.004, iron, verts=4))
    bc = Vector((0.3, 0, 1.06))
    parts.append(hemi(0.09, bc + Vector((0, 0, 0.04)), (0, 0, -1), basket, cut=-0.05, segs=12, rings=8))
    J = random.Random(2)
    for k in range(9):
        a = 2 * math.pi * k / 9
        c = bc + Vector((0.07 * math.cos(a), 0.07 * math.sin(a), 0.06 + J.uniform(-0.02, 0.02)))
        parts.append(sphere(0.03, c, fl[k % 2], segs=8, rings=5))
    parts.append(lumpy(0.075, bc + Vector((0, 0, 0.05)), leaf, 9, amount=0.2, scale=(1, 1, 0.6), smooth=70))
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.3
        s = bc + Vector((0.08 * math.cos(a), 0.08 * math.sin(a), 0.03))
        parts.append(tube([s, s + Vector((0.03 * math.cos(a), 0.03 * math.sin(a), -0.1)),
                           s + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.2))], [0.01, 0.008, 0.005], leaf, verts=4))
    simple(parts, "lamp_post")


def tree():
    bark = mat("tree_bark", (0.38, 0.24, 0.14), 0.85)
    leaf = mat("tree_leaf", (0.2, 0.5, 0.15), 0.7, coat=0.15)
    leaf2 = mat("tree_leaf_light", (0.42, 0.66, 0.2), 0.65, coat=0.15)
    blossom = mat("tree_blossom", (1.0, 0.8, 0.85), 0.5, emit=0.15)
    parts = [limb([(0, 0, -0.02), (0.0, 0, 0.4), (0.04, 0, 0.8), (0.02, 0.02, 1.1)], [0.11, 0.08, 0.07, 0.05], bark,
                  verts=10, per=3, caps=True)]
    for a, h in ((0.3, 0.02), (2.4, 0.02), (4.3, 0.02)):  # root flares
        parts.append(rod((0, 0, 0.16), (0.2 * math.cos(a), 0.2 * math.sin(a), h), 0.05, bark, r2=0.02, verts=6))
    parts.append(rod((0.03, 0, 0.85), (0.3, 0.1, 1.25), 0.04, bark, r2=0.025, verts=6))
    parts.append(rod((0.03, 0, 0.9), (-0.25, -0.1, 1.3), 0.04, bark, r2=0.025, verts=6))
    J = random.Random(4)
    for k, (x, y, z, r) in enumerate(((0, 0, 1.55, 0.5), (0.35, 0.1, 1.35, 0.36), (-0.35, -0.08, 1.4, 0.36),
                                      (0.1, -0.3, 1.35, 0.32), (-0.08, 0.3, 1.45, 0.34), (0.12, 0.05, 1.9, 0.32))):
        parts.append(lumpy(r, (x, y, z), leaf if k % 2 == 0 else leaf2, 70 + k, amount=0.1, scale=(1, 1, 0.9), sub=2,
                           smooth=70))
    for k in range(14):
        a = J.uniform(0, 6.28)
        e = J.uniform(-0.2, 1.0)
        d = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        parts.append(sphere(0.035, Vector((0, 0, 1.6)) + d * Vector((0.62, 0.55, 0.52)) * 1.0, blossom, segs=6, rings=4))
    simple(parts, "tree")


def window(x, z, w, h, y, face, frame_m, glass_m, shutter=None, box_m=None, flowers=None, depth=0.05):
    """A window on a wall whose outer face is at y (face = -1: the wall faces -Y). Built on the XZ plane."""
    parts = [box((w + 0.08, depth, h + 0.08), (x, y + face * depth / 2, z), frame_m, bevel=0.012, segs=1),
             box((w, depth, h), (x, y + face * (depth / 2 + 0.01), z), glass_m, bevel=0.0),
             box((0.03, depth, h), (x, y + face * (depth / 2 + 0.015), z), frame_m, bevel=0.004),
             box((w, depth, 0.03), (x, y + face * (depth / 2 + 0.015), z + h * 0.12), frame_m, bevel=0.004),
             box((w + 0.16, depth + 0.05, 0.04), (x, y + face * (depth / 2 + 0.02), z - h / 2 - 0.05), frame_m, bevel=0.01)]
    if shutter is not None:
        for s in (-1, 1):
            parts.append(box((w * 0.5, 0.025, h + 0.04), (x + s * (w * 0.75 + 0.06), y + face * 0.02, z), shutter,
                             bevel=0.008))
    if box_m is not None:
        parts.append(box((w + 0.1, 0.12, 0.08), (x, y + face * 0.08, z - h / 2 - 0.1), box_m, bevel=0.015))
        J = random.Random(int(x * 100 + z * 10))
        for k in range(5):
            parts.append(sphere(0.04, (x - w / 2 + w * k / 4, y + face * 0.09, z - h / 2 - 0.04 + J.uniform(0, 0.03)),
                                flowers[k % len(flowers)], segs=8, rings=5))
    return parts


def rotate_parts(parts, angle, c=(0, 0, 0)):
    M = Matrix.Translation(Vector(c)) @ Matrix.Rotation(angle, 4, "Z") @ Matrix.Translation(-Vector(c))
    for o in parts:
        o.data.transform(M)
    return parts


def house_a():
    wall = mat("house_a_wall", (0.62, 0.2, 0.12), 0.85)
    trim = mat("house_a_trim", (0.97, 0.95, 0.9), 0.5)
    glow = mat("house_a_glow", (1.0, 0.72, 0.35), 0.3, emit=1.6)
    roof = mat("house_a_roof", (0.2, 0.22, 0.28), 0.6)
    door = mat("house_a_door", (0.1, 0.32, 0.22), 0.4, coat=0.5)
    brass = mat("house_a_brass", (0.9, 0.7, 0.3), 0.3, 0.9)
    pot = mat("house_a_flowerbox", (0.3, 0.45, 0.2), 0.6)
    fls = [mat("house_a_flower_a", (1.0, 0.25, 0.3), 0.5), mat("house_a_flower_b", (1.0, 0.95, 0.9), 0.5)]
    W, D, H = 2.0, 1.8, 2.7
    parts = [box((W, D, H), (0, 0, H / 2), wall, bevel=0.02),
             box((W + 0.06, D + 0.06, 0.22), (0, 0, 0.11), trim, bevel=0.02)]
    # stepped gables front and back
    steps = [(-1.0, 0), (-1.0, 0.3), (-0.75, 0.3), (-0.75, 0.6), (-0.5, 0.6), (-0.5, 0.85), (-0.25, 0.85),
             (-0.25, 1.05), (0.25, 1.05), (0.25, 0.85), (0.5, 0.85), (0.5, 0.6), (0.75, 0.6), (0.75, 0.3), (1.0, 0.3),
             (1.0, 0)]
    for y in (-D / 2 + 0.1, D / 2 - 0.1):
        g = prism([(x, z + H) for x, z in steps], 0.2, (0, y, 0), wall, bevel=0.015)
        parts.append(g)
        for i in range(0, len(steps) - 1, 2):  # white copings on the steps
            (xa, za), (xb, zb) = steps[i + 1], steps[i + 2] if i + 2 < len(steps) else steps[i + 1]
            if abs(za - zb) < 1e-6 and abs(xa - xb) > 1e-6:
                parts.append(box((abs(xb - xa) + 0.06, 0.26, 0.05), ((xa + xb) / 2, y, H + za + 0.02), trim, bevel=0.01))
    # the roof between the gables
    rz = H + 0.95
    for s in (1, -1):
        ln = math.hypot(W / 2, rz - H)
        a = math.atan2(rz - H, W / 2)
        o = box((ln + 0.02, D - 0.35, 0.07), (s * W / 4, 0, (H + rz) / 2), roof, bevel=0.015)
        o.data.transform(Matrix.Translation((-s * W / 4, 0, -(H + rz) / 2)))
        o.data.transform(Matrix.Rotation(-s * a, 4, "Y"))
        o.data.transform(Matrix.Translation((s * W / 4, 0, (H + rz) / 2)))
        parts.append(o)
    parts.append(box((0.3, 0.3, 0.6), (0.55, 0.3, rz), wall, bevel=0.02))     # chimney
    parts.append(box((0.36, 0.36, 0.06), (0.55, 0.3, rz + 0.3), trim, bevel=0.01))
    # the front: door with a fanlight and steps, windows on three floors, the hoist beam
    fy = -D / 2
    parts += [box((0.42, 0.06, 0.8), (-0.5, fy - 0.01, 0.62), door, bevel=0.015),
              box((0.52, 0.08, 0.06), (-0.5, fy - 0.02, 1.05), trim, bevel=0.01),
              box((0.4, 0.05, 0.14), (-0.5, fy - 0.03, 1.15), glow, bevel=0.0),
              box((0.56, 0.2, 0.08), (-0.5, fy - 0.1, 0.18), trim, bevel=0.015),
              sphere(0.025, (-0.36, fy - 0.05, 0.62), brass, segs=8, rings=5)]
    parts += window(0.45, 0.72, 0.62, 0.62, fy, -1, trim, glow)
    for z in (1.55, 2.3):
        for x in (-0.5, 0.45):
            parts += window(x, z, 0.44, 0.56, fy, -1, trim, glow, box_m=pot if z < 2 else None, flowers=fls)
    parts += window(0, H + 0.45, 0.3, 0.36, fy, -1, trim, glow)
    parts.append(box((0.08, 0.35, 0.08), (0, fy - 0.15, H + 0.82), trim, bevel=0.01))   # hoist beam
    parts.append(rod((0, fy - 0.3, H + 0.78), (0, fy - 0.3, H + 0.62), 0.008, brass, verts=4))
    # back and side windows
    for z in (0.8, 1.55, 2.3):
        for x in (-0.45, 0.45):
            parts += window(x, z, 0.4, 0.5, D / 2, 1, trim, glow)
    for side in (-1, 1):
        for z in (0.8, 1.55, 2.3):
            for yy in (-0.4, 0.4):
                ws = window(yy, z, 0.36, 0.5, W / 2, 1, trim, glow)
                rotate_parts(ws, side * R90 if side > 0 else -R90)
                parts += ws
    simple(parts, "house_a")


def house_b():
    wall = mat("house_b_wall", (0.95, 0.7, 0.3), 0.85)
    trim = mat("house_b_trim", (0.98, 0.96, 0.92), 0.5)
    glow = mat("house_b_glow", (1.0, 0.75, 0.4), 0.3, emit=1.6)
    roof = mat("house_b_roof", (0.62, 0.2, 0.12), 0.6)
    shutter = mat("house_b_shutter", (0.15, 0.35, 0.65), 0.45, coat=0.4)
    awn_a = mat("house_b_awning", (0.85, 0.15, 0.15), 0.6)
    awn_b = mat("house_b_awning_b", (0.98, 0.95, 0.9), 0.6)
    door = mat("house_b_door", (0.45, 0.22, 0.12), 0.5, coat=0.4)
    W, D, H = 2.4, 1.8, 2.75
    parts = [box((W, D, H), (0, 0, H / 2), wall, bevel=0.02),
             box((W + 0.06, D + 0.06, 0.2), (0, 0, 0.1), trim, bevel=0.02),
             box((W + 0.1, D + 0.1, 0.1), (0, 0, H), trim, bevel=0.02)]
    # bell gable front and back: curved shoulders, a neck, a round pediment
    pts = []
    for k in range(9):
        t = k / 8
        pts.append((-0.95 + 0.45 * t, 0.55 * math.sin(t * R90) ** 1.5))
    pts += [(-0.4, 0.62), (-0.4, 0.8)]
    for k in range(9):
        a = math.pi - math.pi * k / 8
        pts.append((0.4 * math.cos(a), 0.8 + 0.3 * math.sin(a)))
    pts += [(0.4, 0.62)]
    for k in range(9):
        t = 1 - k / 8
        pts.append((0.95 - 0.45 * t, 0.55 * math.sin(t * R90) ** 1.5))
    gable = [(x, z + H) for x, z in pts]
    gable = [(-0.95, H)] + gable[1:-1] + [(0.95, H)]
    for y in (-D / 2 + 0.1, D / 2 - 0.1):
        parts.append(prism(gable, 0.2, (0, y, 0), wall, bevel=0.012))
        parts.append(tube([Vector((x, y - (0.11 if y < 0 else -0.11), z)) for x, z in gable[1:-1]],
                          [0.03] * (len(gable) - 2), trim, verts=6))
    rz = H + 0.72
    for s in (1, -1):
        ln = math.hypot(W / 2 + 0.1, rz - H)
        a = math.atan2(rz - H, W / 2 + 0.1)
        o = box((ln, D - 0.35, 0.07), (s * (W / 4 + 0.05), 0, (H + rz) / 2), roof, bevel=0.015)
        o.data.transform(Matrix.Translation((-s * (W / 4 + 0.05), 0, -(H + rz) / 2)))
        o.data.transform(Matrix.Rotation(-s * a, 4, "Y"))
        o.data.transform(Matrix.Translation((s * (W / 4 + 0.05), 0, (H + rz) / 2)))
        parts.append(o)
    parts.append(box((0.26, 0.26, 0.55), (-0.7, 0.2, rz - 0.05), roof, bevel=0.02))
    parts.append(box((0.32, 0.32, 0.06), (-0.7, 0.2, rz + 0.24), trim, bevel=0.01))
    fy = -D / 2
    # shop front: a big window, a door, a striped awning
    parts += [box((1.3, 0.05, 0.8), (0.35, fy - 0.02, 0.72), glow, bevel=0.0),
              box((1.4, 0.08, 0.06), (0.35, fy - 0.03, 1.14), trim, bevel=0.01),
              box((1.4, 0.08, 0.06), (0.35, fy - 0.03, 0.3), trim, bevel=0.01),
              box((0.05, 0.07, 0.8), (0.35, fy - 0.03, 0.72), trim, bevel=0.005),
              box((0.46, 0.06, 0.95), (-0.72, fy - 0.01, 0.68), door, bevel=0.015),
              box((0.3, 0.05, 0.3), (-0.72, fy - 0.03, 0.85), glow, bevel=0.0)]
    n = 10
    for k in range(n):
        x0 = -1.1 + 2.2 * k / n
        o = box((2.2 / n, 0.5, 0.04), (x0 + 1.1 / n, fy - 0.25, 1.35), awn_a if k % 2 == 0 else awn_b, bevel=0.0)
        o.data.transform(Matrix.Translation((0, -(fy - 0.25), -1.35)))
        o.data.transform(Matrix.Rotation(-0.45, 4, "X"))
        o.data.transform(Matrix.Translation((0, fy - 0.23, 1.33)))
        parts.append(o)
        # scalloped valance
        parts.append(sphere(2.2 / n / 2, (x0 + 1.1 / n, fy - 0.46, 1.2), awn_a if k % 2 == 0 else awn_b,
                            scale=(1, 0.15, 0.7), segs=10, rings=5))
    for z in (1.75, 2.4):
        for x in (-0.65, 0.0, 0.65):
            parts += window(x, z, 0.36, 0.48, fy, -1, trim, glow, shutter=shutter)
    parts += window(0, H + 0.55, 0.26, 0.3, fy, -1, trim, glow)
    for z in (0.8, 1.75, 2.4):
        for x in (-0.6, 0.6):
            parts += window(x, z, 0.4, 0.5, D / 2, 1, trim, glow, shutter=shutter)
    for side in (-1, 1):
        for z in (0.8, 1.75, 2.4):
            ws = window(0.0, z, 0.36, 0.5, W / 2, 1, trim, glow, shutter=shutter)
            rotate_parts(ws, -R90 if side > 0 else R90)
            parts += ws
    simple(parts, "house_b")


def fly():
    body = mat("fly_body", (0.12, 0.1, 0.1), 0.4, coat=0.5)
    glow = mat("fly_glow", (0.8, 1.0, 0.3), 0.3, emit=8.0)
    wing_m = mat("fly_wing", (0.85, 0.95, 1.0), 0.1, coat=1.0, alpha=0.45, emit=0.4)
    eye = mat("fly_eye", (0.8, 0.15, 0.1), 0.2, coat=1.0)
    shine = mat("fly_shine", (1, 1, 1), 0.2, emit=4.0)
    Z = 0.32
    # facing -Y (towards the camera): head forward
    parts = [ell((0, 0.0, Z), (0.055, 0.07, 0.05), body, segs=14, rings=8),
             ell((0, 0.1, Z - 0.02), (0.06, 0.08, 0.055), glow, pitch=15, segs=14, rings=8),
             sphere(0.045, (0, -0.08, Z + 0.01), body, segs=12, rings=8)]
    for s in (1, -1):
        parts.append(sphere(0.026, (0.03 * s, -0.1, Z + 0.025), eye, segs=10, rings=6))
        parts.append(sphere(0.007, (0.036 * s, -0.12, Z + 0.038), shine, segs=6, rings=4))
        parts.append(tube([Vector((0.015 * s, -0.11, Z + 0.05)), Vector((0.04 * s, -0.14, Z + 0.1)),
                           Vector((0.06 * s, -0.13, Z + 0.12))], [0.004, 0.003, 0.003], body, verts=4))
        parts.append(sphere(0.008, (0.06 * s, -0.13, Z + 0.12), glow, segs=6, rings=4))
        for k in range(3):
            y = -0.03 + 0.04 * k
            parts.append(tube([Vector((0.03 * s, y, Z - 0.03)), Vector((0.07 * s, y, Z - 0.05)),
                               Vector((0.08 * s, y + 0.01, Z - 0.1))], [0.005, 0.004, 0.003], body, verts=4))
    root = join(parts, "fly")
    wings = []
    for s, nm in ((1, "wing_l"), (-1, "wing_r")):
        hinge = Vector((0.03 * s, -0.01, Z + 0.04))
        w = ell(hinge + Vector((0.09 * s, 0.03, 0.0)), (0.1, 0.045, 0.006), wing_m, yaw=-20 * s, segs=12, rings=6)
        w = join([w], nm, pivot=hinge)
        wings.append(w)
    # buzz: the whole fly bobs and sways; the wings beat (every frame alternates up and down)
    animate(root, "buzz", {f: {"loc": (0.02 * math.sin(2 * math.pi * f / 30), 0.0, 0.03 * math.sin(4 * math.pi * f / 30)),
                                "rot": (0, 0.1 * math.sin(2 * math.pi * f / 30), 0)} for f in range(0, 31, 3)})
    for w, s in zip(wings, (1, -1)):
        animate(w, "buzz", {f: {"rot": (0, -s * (0.7 if f % 2 == 0 else -0.35), 0)} for f in range(0, 31)})
    export_anim(root, "fly", [(w, root) for w in wings])


# ------------------------------------------------------------------ main

JOBS = {"frog": frog, "lady_frog": lady_frog, "car_a": car_a, "car_b": car_b, "truck": truck, "bulldozer": bulldozer,
        "racecar": racecar, "log_short": log_short, "log_mid": log_mid, "log_long": log_long, "turtle": turtle,
        "lilypad": lilypad, "croc": croc, "home_bay": home_bay, "hedge_block": hedge_block, "bank_tile": bank_tile,
        "median_tile": median_tile, "road_tile": road_tile, "road_tile_line": road_tile_line,
        "water_edge": water_edge, "lamp_post": lamp_post, "tree": tree, "house_a": house_a, "house_b": house_b,
        "fly": fly}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = 30
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
