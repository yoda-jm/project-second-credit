"""DOCSTRING"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, export, reset, cyl, box, prism
from blastyard_bombers import merge, mirror, smoothstep, smooth_path
from hopline_models import TurnRig, ell, hemi
from mossfolk_models import lathe_r, lumpy, solid
from prism_models import animate, export_anim, empty, new_obj

FPS = 30


# ------------------------------------------------------------------ helpers

def cone(base, tip, r, material, verts=8):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


class Rig(TurnRig):
    """TurnRig facing -Y in Blender (Godot +Z), with bone-attached empties and a mesh named "body"."""

    def __init__(self, bones, hidden=()):
        super().__init__(bones, 0, fps=FPS, hidden=hidden)
        self.attached = []

    def build(self, name):
        mesh = super().build(name)
        mesh.name = mesh.data.name = "body"
        return mesh

    def pin(self, name, loc, bone):
        """An empty at loc carried by `bone`."""
        e = empty(name)
        e.empty_display_size = 0.05
        bpy.context.view_layer.update()
        e.matrix_world = Matrix.Translation(Vector(loc))
        mw = e.matrix_world.copy()
        e.parent = self.arm
        e.parent_type = "BONE"
        e.parent_bone = bone
        bpy.context.view_layer.update()
        e.matrix_world = mw
        self.attached.append(e)
        return e

    def save(self, name, extra=()):
        super().save(name, list(self.attached) + list(extra))


def sheet(grid, material, name="sheet", thick=0.0, smooth=70):
    """A quad surface through a grid of points (rows of columns), optionally solidified."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in grid]
    for i in range(len(vs) - 1):
        for j in range(len(vs[0]) - 1):
            bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if thick:
        solid(o, thick)
    return K.finish(o, material, smooth=smooth)


def xform(objs, M):
    """Transforms the objects' meshes by M (after baking any object transform into the mesh)."""
    for o in K.flatten([objs]):
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.transform(M)
    return objs


def flame(base, tip, r, material, bend=(0, 0, 0), verts=8):
    """A teardrop tongue of fire from base to tip, bulging near the base."""
    a, b = Vector(base), Vector(tip)
    pts = [a + (b - a) * t + Vector(bend) * math.sin(math.pi * t) for t in (0.0, 0.2, 0.45, 0.7, 0.88, 1.0)]
    rad = [r * k for k in (0.7, 1.0, 0.85, 0.5, 0.22, 0.04)]
    return tube(pts, rad, material, verts=verts, caps=True, name="flame")


def fire(c, size, outer, inner, seed=1):
    """A little fire: a few tongues of the outer colour around a brighter core, rising from c."""
    rnd = random.Random(seed)
    c = Vector(c)
    out = [flame(c, c + Vector((0, 0, 1.0 * size)), 0.32 * size, inner, verts=8)]
    for k in range(5):
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        out.append(flame(c + d * 0.12 * size, c + d * 0.2 * size + Vector((0, 0, rnd.uniform(0.6, 0.9) * size)),
                         0.24 * size, outer, bend=tuple(d * 0.05 * size), verts=7))
    out.append(flame(c, c + Vector((0, 0, 1.25 * size)), 0.38 * size, outer, verts=9))
    return out


def lathe_y(profile, material, segs=16, name="lathe", smooth=60):
    """A lathe about Z turned to lie along -Y (its +Z end forward)."""
    o = lathe_r(profile, material, segs=segs, name=name, smooth=smooth)
    o.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    return o


def place(objs, loc, rz=0.0, rx=0.0, ry=0.0):
    M = (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
         @ Matrix.Rotation(rx, 4, "X"))
    return xform(objs, M)


def rings_loft(rings, material, name="loft", smooth=60, cap_bottom=True, cap_top=True):
    """A loft through closed rings of points (each a list of Vector, same count)."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    for r0, r1 in zip(vs, vs[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    if cap_bottom:
        bm.faces.new(vs[0][::-1])
    if cap_top:
        bm.faces.new(vs[-1])
    return new_obj(name, bm, material, smooth)


# ------------------------------------------------------------------ heroes: shared body and rig

# Joints, built facing -Y (left = +X). Hand centres at (+-0.207, -0.045, 0.31).
HERO_BONES = {"root": ((0, 0, 0), (0, 0, 0.06), None),
              "hips": ((0, 0, 0.34), (0, 0, 0.45), "root"),
              "body": ((0, 0, 0.45), (0, 0, 0.64), "hips"),
              "head": ((0, 0, 0.66), (0, 0, 0.9), "body"),
              "arm.L": ((0.165, 0.0, 0.6), (0.195, 0.01, 0.45), "body"),
              "arm.R": ((-0.165, 0.0, 0.6), (-0.195, 0.01, 0.45), "body"),
              "fore.L": ((0.195, 0.01, 0.45), (0.205, -0.03, 0.33), "arm.L"),
              "fore.R": ((-0.195, 0.01, 0.45), (-0.205, -0.03, 0.33), "arm.R"),
              "hand.L": ((0.205, -0.03, 0.33), (0.208, -0.05, 0.27), "fore.L"),
              "hand.R": ((-0.205, -0.03, 0.33), (-0.208, -0.05, 0.27), "fore.R"),
              "leg.L": ((0.075, 0.0, 0.35), (0.08, 0.0, 0.2), "hips"),
              "leg.R": ((-0.075, 0.0, 0.35), (-0.08, 0.0, 0.2), "hips"),
              "shin.L": ((0.08, 0.0, 0.2), (0.08, 0.005, 0.075), "leg.L"),
              "shin.R": ((-0.08, 0.0, 0.2), (-0.08, 0.005, 0.075), "leg.R"),
              "foot.L": ((0.08, 0.005, 0.075), (0.08, -0.07, 0.03), "shin.L"),
              "foot.R": ((-0.08, 0.005, 0.075), (-0.08, -0.07, 0.03), "shin.R")}
HAND = {1: Vector((0.207, -0.045, 0.31)), -1: Vector((-0.207, -0.045, 0.31))}


def w_trunk(p):
    a = smoothstep(0.4, 0.5, p.z)
    return {"hips": 1 - a + 1e-4, "body": a + 1e-4}


def w_cape(z_top, z_len):
    """Cape weights: body at the collar, cape, then cape2 towards the hem."""
    def fn(p):
        v = (z_top - p.z) / z_len
        a = smoothstep(0.0, 0.25, v)
        b = smoothstep(0.35, 0.8, v)
        return {"body": 1 - a + 1e-4, "cape": a * (1 - b) + 1e-4, "cape2": a * b + 1e-4}
    return fn


def cape_grid(z_top, z_bot, w_top, w_bot, y_top, y_bot, curl=0.06, nu=12, nv=10, scallop=0.0):
    """A cape hanging behind the shoulders: rows from the collar down, curving round the back."""
    rows = []
    for i in range(nv + 1):
        v = i / nv
        z = z_top + (z_bot - z_top) * v
        w = w_top + (w_bot - w_top) * v ** 0.8
        yb = y_top + (y_bot - y_top) * v
        row = []
        for j in range(nu + 1):
            u = -1 + 2 * j / nu
            x = u * w
            y = yb - curl * (1 - u * u) * -1 - (0.07 + 0.05 * v) * u * u
            zz = z + (scallop * (0.5 + 0.5 * math.cos(u * math.pi * 5)) if i == nv else 0.0)
            row.append(Vector((x, y, zz)))
        rows.append(row)
    return rows


def belt_torch(rig, name, at, lean=(0.5, 0.6), seed=3):
    """A short torch tucked through the belt at `at` (hips bone), leaning out and back; returns its flame tip."""
    wood = mat(name + "_torch_wood", (0.32, 0.2, 0.1), 0.8)
    wrap = mat(name + "_torch_wrap", (0.16, 0.1, 0.07), 0.9)
    glow = mat(name + "_torch_glow", (1.0, 0.5, 0.12), 0.4, emit=3.5, emit_color=(1.0, 0.42, 0.08))
    core = mat(name + "_torch_core_glow", (1.0, 0.85, 0.45), 0.3, emit=6.0)
    at = Vector(at)
    d = Vector((lean[0] * (1 if at.x > 0 else -1), lean[1], 1.0)).normalized()
    a, b = at - d * 0.09, at + d * 0.1
    parts = [rod(a, b, 0.013, wood, verts=8),
             rod(b - d * 0.01, b + d * 0.04, 0.02, wrap, r2=0.024, verts=10),
             torus(0.022, 0.005, b + d * 0.005, wrap, verts=10, minor=4)]
    top = b + d * 0.035
    parts += fire(top, 0.07, glow, core, seed)
    rig.rigid("hips", parts)
    return top + Vector((0, 0, 0.04))


def eye_pair(rig, c, sep, white, pupil, shine, size=1.0, yaw=24):
    for s in (-1, 1):
        e = Vector((s * sep, c[1], c[2]))
        rig.rigid("head", [ell(e, (0.016 * size, 0.008 * size, 0.019 * size), white, yaw=-s * yaw, segs=10, rings=6),
                           ell(e + Vector((-s * 0.002, -0.006, -0.001)), (0.009 * size, 0.005 * size, 0.012 * size),
                               pupil, yaw=-s * yaw, segs=8, rings=6),
                           sphere(0.003 * size, e + Vector((s * 0.002, -0.01, 0.006)), shine, segs=6, rings=4)])


def limb_set(rig, s, side, upper, fore, hand, r_up=0.042, r_fore=0.037, elbow=None, cuff=None, hand_m=None,
             fist=True, hand_bone=None):
    """Arm: an upper arm, an elbow ball, a forearm and a fist (all rigid)."""
    sh, el = Vector(HERO_BONES["arm." + side][0]), Vector(HERO_BONES["arm." + side][1])
    wr = Vector(HERO_BONES["fore." + side][1])
    up = [rod(sh, el, r_up, upper, r2=r_up * 0.9, verts=12), sphere(r_up, sh, upper, segs=12, rings=8)]
    rig.rigid("arm." + side, up)
    fo = [rod(el, wr, r_fore, fore, r2=r_fore * 0.92, verts=12), sphere(r_up * 0.9, el, elbow or fore, segs=12,
                                                                         rings=8)]
    if cuff:
        fo.append(rod(el + (wr - el) * 0.45, wr + (wr - el) * 0.05, r_fore * 1.25, cuff, r2=r_fore * 1.32, verts=12))
    rig.rigid("fore." + side, fo)
    h = HAND[s]
    hd = [ell(h, (0.036, 0.042, 0.04), hand_m or hand, segs=12, rings=8)]
    if fist:   # knuckles
        hd.append(ell(h + Vector((-s * 0.01, -0.03, 0.0)), (0.026, 0.016, 0.03), hand_m or hand, segs=10, rings=6))
    rig.rigid(hand_bone or "hand." + side, hd)


def leg_set(rig, s, side, thigh, shin, boot, r_th=0.05, r_sh=0.043, knee=None, sole=None, boot_top=0.16,
            cuff=None, toe=0.0):
    hp = Vector(HERO_BONES["leg." + side][0])
    kn = Vector(HERO_BONES["leg." + side][1])
    an = Vector(HERO_BONES["shin." + side][1])
    rig.rigid("leg." + side, [rod(hp, kn, r_th, thigh, r2=r_th * 0.88, verts=12)])
    sh = [rod(kn, an, r_sh, shin, r2=r_sh * 0.85, verts=12), sphere(r_th * 0.86, kn, knee or shin, segs=12, rings=8)]
    if boot_top > 0.08:
        sh.append(rod(Vector((kn.x, 0.0, boot_top)), an, r_sh * 1.15, boot, r2=r_sh * 1.05, verts=12))
    if cuff:
        sh.append(torus(r_sh * 1.25, 0.014, (kn.x, 0.0, boot_top), cuff, verts=14, minor=6))
    rig.rigid("shin." + side, sh)
    ft = [ell((an.x, -0.03, 0.04), (0.05, 0.085, 0.042), boot, segs=14, rings=8)]
    for v in ft[0].data.vertices:
        v.co.z = max(v.co.z, 0.005)
    if toe:
        ft.append(tube([(an.x, -0.09, 0.03), (an.x, -0.125, 0.04), (an.x, -0.14, 0.065)], [0.03, 0.018, 0.006], boot,
                       verts=10, caps=True, name="toe"))
    if sole:
        ft.append(ell((an.x, -0.03, 0.01), (0.052, 0.088, 0.012), sole, segs=14, rings=6))
    rig.rigid("foot." + side, ft)


def trunk(rig, material, prof=None, ydepth=0.72, extra_mat=None, split=None):
    """The torso: a lathe from neck to crotch, flattened front to back."""
    prof = prof or [(0.0, 0.665), (0.06, 0.66), (0.115, 0.64), (0.148, 0.605), (0.15, 0.56), (0.137, 0.49),
                    (0.12, 0.43), (0.125, 0.37), (0.11, 0.33), (0.0, 0.315)]
    o = lathe_r(prof, material, segs=28, name="trunk", smooth=60)
    for v in o.data.vertices:
        v.co.y *= ydepth
    o.data.update()
    if extra_mat and split:
        o.data.materials.append(extra_mat)
        for f in o.data.polygons:
            if split(f.center):
                f.material_index = 1
    rig.custom(w_trunk, o)
    return o


def hero_anims(rig, style, base, cape=True, blink=None, phi0=None):
    """The shared hero actions. base: the hero's resting hold (added to every key). style: chop / slash / cast /
    draw (the attack). Returns nothing; keys the actions idle, run, attack, hurt, die, cheer."""
    has_cape = cape
    phi0 = phi0 or {}

    def conv(pose):
        """'phi.R' / 'phi.L': the weapon's angle from upright (degrees, + tips it forward) -> a hand rotation."""
        pose = dict(pose)
        for side in ("R", "L"):
            k = "phi." + side
            if k in pose:
                want = pose.pop(k)
                tot = sum(pose.get(b + "." + side, (0, 0, 0))[0] for b in ("arm", "fore"))
                h = pose.get("hand." + side, (0, 0, 0))
                pose["hand." + side] = (want - phi0.get(side, 0.0) - tot, h[1], h[2])
        return pose

    class _R:
        def action(self, name, keys, loop=False):
            rig_.action(name, {f: conv(p) for f, p in keys.items()}, loop=loop)
    rig_ = rig
    rig = _R()

    def B(*poses):
        return merge(base, *poses)

    def O(*poses):
        """The base hold, with the channels the poses name replaced (not added)."""
        out = dict(base)
        for p in poses:
            out.update(p)
        return out

    def capes(a, b=0.0, sway=0.0):
        return {"cape": (a, sway, 0), "cape2": (b, sway * 0.5, 0)} if has_cape else {}

    # idle*: 2 s, breathing, a glance, the cape stirring
    def idle_p(k, ex=None):
        a = 2 * math.pi * k
        return B({"%body": (1 + 0.018 * math.sin(a), 1 + 0.018 * math.sin(a), 1 + 0.012 * math.sin(a)),
                  "body": (1.5 * math.sin(a), 0, 0), "head": (-2 * math.sin(a), 0, 8 * math.sin(a) if k > 0.4 else 0),
                  "arm.L": (-2 * math.sin(a), -3 - 2 * math.sin(a), 0), "arm.R": (-2 * math.sin(a), 3 + 2 * math.sin(a), 0),
                  "@root": (0, 0, -0.004 * (1 - math.cos(a)))},
                 capes(3 + 2 * math.sin(a + 0.6), 3 * math.sin(a + 1.2), 2 * math.sin(a + 0.3)), ex or {})
    keys = {f: idle_p(f / 60) for f in (0, 10, 20, 30, 40, 50, 60)}
    if blink:
        keys[46] = idle_p(46 / 60)
        keys[48] = idle_p(48 / 60, blink)
        keys[50] = idle_p(50 / 60)
    rig.action("idle", keys, loop=True)

    # run*: 0.4 s, two strides; f0 left foot forward (contact), f3 the right knee passing high, f6 right forward
    swing_arm = {"chop": 0.35, "slash": 0.45, "cast": 0.4, "draw": 0.35}[style]

    def run_p(ph, up):
        L, R = ("L", "R") if ph == 0 else ("R", "L")
        sg = 1 if ph == 0 else -1
        if not up:   # contact: L forward, R behind
            legs = {"leg." + L: (-34, 0, 0), "shin." + L: (10, 0, 0), "foot." + L: (-8, 0, 0),
                    "leg." + R: (28, 0, 0), "shin." + R: (42, 0, 0), "foot." + R: (18, 0, 0)}
            lift = -0.005
        else:        # passing: R knee high coming through, L planted under the body
            legs = {"leg." + R: (-44, 0, 0), "shin." + R: (88, 0, 0), "foot." + R: (12, 0, 0),
                    "leg." + L: (10, 0, 0), "shin." + L: (8, 0, 0), "foot." + L: (-6, 0, 0)}
            lift = 0.035
        arm = 34 * (1 - 0.4 * up)
        fwd = 34 if not up else 44
        return B(legs, {"@root": (0, 0, lift), "hips": (0, 0, 7 * sg), "body": (12, 0, -9 * sg), "head": (-8, 0, 3 * sg),
                        "arm.L": (arm * sg * (1 if style != "draw" else 0.4), -6, 0),
                        "fore.L": (-30 - 10 * up, 0, 0),
                        "arm.R": (-arm * sg * swing_arm, 6, 0), "fore.R": (-10 * swing_arm, 0, 0),
                        "skirt.F": (-0.8 * fwd, 0, 0), "skirt.B": (0.5 * fwd, 0, 0)},
                 capes(34 + 6 * up, 18 - 8 * up, 5 * sg))
    rig.action("run", {0: run_p(0, 0), 3: run_p(0, 1), 6: run_p(1, 0), 9: run_p(1, 1), 12: run_p(0, 0)}, loop=True)

    # attack: 0.3 s (9 frames), repeatable: rest, wind-up (f3), the blow (f5), back to rest (f9)
    lunge = {"leg.L": (-30, 0, 0), "shin.L": (20, 0, 0), "leg.R": (24, 0, 0), "shin.R": (16, 0, 0),
             "skirt.F": (-24, 0, 0), "skirt.B": (14, 0, 0)}
    if style == "chop":   # an overhead chop: the axe behind the head, then down in front
        wind = {"arm.R": (-150, 18, 10), "fore.R": (-40, 0, 0), "phi.R": -125, "body": (-10, 0, 14),
                "hips": (0, 0, 6), "head": (-6, 0, -8), "arm.L": (-30, -14, 0), "fore.L": (-30, 0, 0),
                "leg.L": (-12, 0, 0), "leg.R": (10, 0, 0), "shin.R": (10, 0, 0)}
        blow = merge(lunge, {"arm.R": (-55, 0, -14), "fore.R": (-20, 0, 0), "phi.R": 100, "body": (22, 0, -14),
                             "hips": (4, 0, -6), "head": (-10, 0, 8), "@root": (0, -0.04, -0.03),
                             "arm.L": (20, -18, 0), "fore.L": (-30, 0, 0)})
        follow = merge(blow, {"arm.R": (8, 0, 0), "fore.R": (6, 0, 0)})
        follow["phi.R"] = 112
    elif style == "slash":   # a diagonal forehand cut from high right across to low left
        wind = {"arm.R": (-140, 30, 30), "fore.R": (-40, 0, 0), "phi.R": -95, "body": (-4, 0, 24), "hips": (0, 0, 8),
                "head": (0, 0, -14), "arm.L": (-40, -10, -20), "fore.L": (-30, 0, 0)}
        blow = merge(lunge, {"arm.R": (-60, 0, -55), "fore.R": (-15, 0, 0), "phi.R": 95, "body": (14, 0, -26),
                             "hips": (0, 0, -10), "head": (-6, 0, 14), "@root": (0, -0.04, -0.02),
                             "arm.L": (-20, -14, 10), "fore.L": (-30, 0, 0)})
        follow = merge(blow, {"arm.R": (0, 0, -12)})
        follow["phi.R"] = 105
    elif style == "cast":   # the staff raised, then thrust out, the free hand pushing the spell
        wind = {"arm.R": (-60, 10, 0), "fore.R": (-60, 0, 0), "phi.R": -25, "body": (-10, 0, 10), "head": (-8, 0, 0),
                "arm.L": (-40, -20, 0), "fore.L": (-60, 0, 0), "%body": (1.02, 1.02, 1.03)}
        blow = merge(lunge, {"arm.R": (-75, 0, -8), "fore.R": (-10, 0, 0), "phi.R": 62, "body": (16, 0, -6),
                             "head": (-8, 0, 0), "@root": (0, -0.04, -0.015), "arm.L": (-80, 0, -12),
                             "fore.L": (-12, 0, 0)})
        follow = merge(blow, {"arm.R": (4, 0, 0)})
        follow["phi.R"] = 66
    else:   # draw: the bow arm out in front, the string hand pulls to the cheek and lets go at f5
        wind = {"arm.L": (-82, -4, 0), "fore.L": (-4, 0, 0), "bow": (86, 0, 0), "arm.R": (-10, 80, 20),
                "fore.R": (-128, 0, 0), "body": (4, 0, -18), "hips": (0, 0, -8), "head": (0, 0, 14),
                "@nock": (-0.1, 0.2, 0.05), "leg.L": (-16, 0, 0), "leg.R": (12, 0, 0)}
        blow = merge(wind, {"arm.R": (0, 10, -10), "fore.R": (60, 0, 0), "@nock": (-0.1, 0.2, 0.05),
                            "@root": (0, 0.02, 0)})
        blow["@nock"] = (0, 0, 0)
        blow["fore.R"] = (-68, 0, 0)
        follow = merge(blow, {"arm.R": (0, 10, -8)})
    rig.action("attack", {0: B(), 3: O(wind), 5: O(blow), 6: O(follow), 9: B()})

    # hurt: 0.25 s, a recoil and back
    hit = {"body": (-16, 0, 6), "head": (-16, 0, -6), "@root": (0, 0.05, 0.0), "arm.L": (14, -24, 0),
           "arm.R": (14, 24, 0), "fore.L": (-20, 0, 0), "fore.R": (-20, 0, 0), "leg.L": (-10, 0, 0),
           "shin.L": (10, 0, 0), "%body": (1.04, 1.04, 0.96)}
    rig.action("hurt", {0: B(), 2: B(hit, capes(-10, 10)), 4: B(merge(hit, {"body": (6, 0, 0)}), capes(6, 0)),
                        8: B()})

    # die: 1.2 s, staggers, the knees go, falls back and lies still (holds the last frame)
    stag = B(hit, {"body": (-10, 0, 10), "@root": (0, 0.07, 0)}, capes(-10, 10))
    buckle = O({"@root": (0, 0.1, -0.14), "body": (18, 0, -10), "head": (14, 0, 0), "leg.L": (-60, 0, 4),
                "shin.L": (100, 0, 0), "foot.L": (-30, 0, 0), "leg.R": (-50, 0, -4), "shin.R": (95, 0, 0),
                "foot.R": (-30, 0, 0), "arm.L": (0, -20, 0), "arm.R": (0, 20, 0), "fore.L": (-30, 0, 0),
                "fore.R": (-30, 0, 0), "skirt.F": (-60, 0, 0)}, capes(10, 10))

    def lie(bounce):
        return O({"root": (-84, 0, 0), "@root": (0, 0.12, 0.09 + bounce), "body": (-6, 0, 0), "head": (-10, 0, 12),
                  "leg.L": (-24, 0, 6), "shin.L": (40, 0, 0), "leg.R": (-6, 0, -8), "shin.R": (14, 0, 0),
                  "foot.L": (-30, 0, 0), "foot.R": (-30, 0, 0),
                  "arm.L": (-10, -70, 0), "fore.L": (-40, 0, 0), "arm.R": (-20, 64, 0), "fore.R": (-20, 0, 0),
                  "skirt.F": (-20, 0, 0), "skirt.B": (30, 0, 0)},
                 capes(-60, 0))
    rig.action("die", {0: B(), 4: stag, 12: buckle, 22: lie(0.0), 26: lie(0.03), 30: lie(0.0), 36: lie(0.0)})

    # cheer*: 1 s, the weapon raised high, two hops
    def cheer_p(h, sq, wave):
        return O({"@root": (0, 0, h), "%body": (1 - sq, 1 - sq, 1 + sq), "head": (-14, 0, 0), "body": (-4, 0, 0),
                  "arm.R": (-165 + wave, 18, 0), "fore.R": (-10, 0, 0), "phi.R": -8, "arm.L": (-10, -40 - wave, 0),
                  "fore.L": (-60, 0, 0),
                  "leg.L": (-20 * h / 0.08, 0, 0), "shin.L": (40 * h / 0.08, 0, 0), "foot.L": (0, 0, 0),
                  "leg.R": (-20 * h / 0.08, 0, 0), "shin.R": (40 * h / 0.08, 0, 0)},
                 capes(10 + 120 * h, 20 * h / 0.08))
    rig.action("cheer", {0: cheer_p(0, -0.04, 0), 5: cheer_p(0.08, 0.03, 10), 9: cheer_p(0.09, 0.02, 14),
                         13: cheer_p(0.02, 0.0, 6), 15: cheer_p(0, -0.05, 0), 20: cheer_p(0.08, 0.03, 10),
                         24: cheer_p(0.09, 0.02, 14), 28: cheer_p(0.02, 0.0, 6), 30: cheer_p(0, -0.04, 0)}, loop=True)


def hero_rig(extra=None):
    bones = dict(HERO_BONES)
    bones.update({"cape": ((0, 0.1, 0.62), (0, 0.15, 0.4), "body"),
                  "cape2": ((0, 0.15, 0.4), (0, 0.18, 0.14), "cape"),
                  "skirt.F": ((0, -0.08, 0.44), (0, -0.11, 0.2), "hips"),
                  "skirt.B": ((0, 0.08, 0.44), (0, 0.11, 0.2), "hips")})
    bones.update(extra or {})
    return Rig(bones)


def w_skirt(z_top, z_bot):
    """A skirt: front half on skirt.F, back half on skirt.B, the sides and the waist on the hips."""
    def fn(p):
        v = smoothstep(z_top, z_bot, p.z) if z_bot < z_top else 0.0
        v = smoothstep(0.0, 1.0, (z_top - p.z) / (z_top - z_bot))
        f = smoothstep(0.0, -0.06, p.y)
        b = smoothstep(0.0, 0.06, p.y)
        side = smoothstep(0.08, 0.15, abs(p.x)) * 0.5
        k = v * (1 - side)
        return {"hips": 1 - k + 1e-4, "skirt.F": k * f + 1e-4, "skirt.B": k * b + 1e-4}
    return fn


def skirt_mesh(material, z_top, z_bot, r_top, r_bot, ydepth=0.78, slit=0.0, segs=32, rows=6, name="skirt",
               hem=0.0):
    """A flared skirt lathe; slit > 0 removes the side faces (|x| > ... near the sides) leaving front/back panels."""
    prof = [(r_top + (r_bot - r_top) * (i / rows) ** 1.2, z_top + (z_bot - z_top) * i / rows) for i in range(rows + 1)]
    o = lathe_r(prof, material, segs=segs, name=name, smooth=60)
    for v in o.data.vertices:
        v.co.y *= ydepth
    o.data.update()
    if slit:
        def fn(bm):
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.calc_center_median().y) < slit
                                       and f.calc_center_median().z < z_top - 0.06], context="FACES")
        from prism_models import edit
        edit(o, fn)
    solid(o, 0.012)
    return K.finish(o, material, smooth=60)


# ------------------------------------------------------------------ the knight

def knight():
    reset()
    steel = mat("knight_steel", (0.6, 0.62, 0.66), 0.3, metal=0.9)
    dark = mat("knight_mail", (0.3, 0.31, 0.34), 0.5, metal=0.8)
    team = mat("knight_team", (0.72, 0.05, 0.04), 0.6, coat=0.1)
    lining = mat("knight_lining", (0.28, 0.03, 0.03), 0.7)
    gold = mat("knight_gold", (0.95, 0.68, 0.22), 0.3, metal=0.9)
    leather = mat("knight_leather", (0.24, 0.13, 0.07), 0.7)
    wood = mat("knight_wood", (0.34, 0.2, 0.1), 0.75)
    slit = mat("knight_slit", (0.01, 0.01, 0.01), 0.8)
    eye = mat("knight_eye_glow", (1.0, 0.75, 0.4), 0.4, emit=2.5)
    rig = hero_rig()

    # torso: a steel gorget and a red surcoat with a gold flame on the chest; the belt
    trunk(rig, team, extra_mat=steel, split=lambda c: c.z > 0.6)
    flame_poly = [(0.0, 0.07), (0.022, 0.03), (0.03, -0.005), (0.02, -0.03), (0.0, -0.04), (-0.02, -0.03),
                  (-0.03, -0.005), (-0.016, 0.02), (-0.006, 0.0), (-0.004, 0.035)]
    emb = prism(flame_poly, 0.01, (0, -0.104, 0.53), gold, bevel=0.003, scale=1.3)
    rig.rigid("body", emb)
    belt = torus(0.124, 0.016, (0, 0, 0.43), leather, verts=28, minor=6, scale=(1, 0.76, 1))
    buckle = box((0.05, 0.016, 0.04), (0, -0.098, 0.43), gold, bevel=0.006)
    rig.custom(w_trunk, belt, buckle)
    # the surcoat's skirt: front and back panels (split at the sides), a gold hem
    sk = skirt_mesh(team, 0.44, 0.17, 0.128, 0.17, slit=0.07, name="skirt")
    rig.custom(w_skirt(0.44, 0.17), sk)
    # mail under the skirt
    mail = skirt_mesh(dark, 0.4, 0.24, 0.12, 0.14, name="mail")
    rig.custom(w_skirt(0.42, 0.22), mail)

    # the great helm: a flat-topped steel bucket, a brow band and a cross in gold, the eye slits, a red crest
    helm = lathe_r([(0.0, 0.925), (0.06, 0.922), (0.1, 0.905), (0.118, 0.875), (0.122, 0.82), (0.12, 0.72),
                    (0.112, 0.668), (0.098, 0.655), (0.0, 0.655)], steel, segs=28, name="helm", smooth=50)
    for v in helm.data.vertices:   # a pointed snout at the front
        if v.co.y < 0:
            k = (-v.co.y / 0.12) ** 3 * (1 - abs(v.co.x) / 0.12)
            v.co.y -= 0.025 * max(0.0, k) * smoothstep(0.66, 0.78, v.co.z)
    helm.data.update()
    hp = [helm]
    for s in (-1, 1):
        sl = box((0.06, 0.03, 0.013), (s * 0.04, -0.118, 0.795), slit, bevel=0.004)
        sl.data.transform(Matrix.Translation((s * 0.04, -0.118, 0.795)) @ Matrix.Rotation(s * 0.38, 4, "Z")
                          @ Matrix.Translation((-s * 0.04, 0.118, -0.795)))
        hp.append(sl)
        hp.append(sphere(0.006, (s * 0.04, -0.13, 0.795), eye, segs=6, rings=4))
        for k in range(3):   # breathing holes
            hp.append(cyl(0.005, 0.02, (s * (0.03 + 0.017 * k), -0.122 + 0.006 * k, 0.725), slit,
                          rot=(math.pi / 2, 0, 0), verts=6))
    hp.append(torus(0.124, 0.011, (0, 0, 0.84), gold, verts=28, minor=6, scale=(1, 0.96, 1)))
    hp.append(tube([(0, -0.135, 0.84), (0, -0.142, 0.78), (0, -0.14, 0.72), (0, -0.125, 0.67)], [0.011] * 4, gold,
                   verts=6, caps=True, name="nasal"))
    # the crest: a gold comb along the top holding a red horsehair plume that sweeps back and down
    hp.append(prism([(-0.08, 0.0), (0.09, 0.0), (0.07, 0.035), (-0.06, 0.035)], 0.014, (0, 0, 0.92), gold,
                    rot=(0, 0, math.pi / 2), bevel=0.004))
    pl = [Vector(p) for p in ((0, -0.085, 0.95), (0, -0.03, 0.985), (0, 0.04, 0.99), (0, 0.11, 0.96),
                              (0, 0.17, 0.89), (0, 0.2, 0.8), (0, 0.205, 0.7))]
    plume = tube(smooth_path(pl, 3), [0.025, 0.03, 0.036, 0.04, 0.042, 0.042, 0.04, 0.038, 0.036, 0.034, 0.03, 0.028,
                                      0.024, 0.02, 0.016, 0.012, 0.006, 0.002, 0.001][:len(smooth_path(pl, 3))],
                 team, verts=10, caps=True, name="plume")
    for v in plume.data.vertices:
        v.co.x *= 0.55
    plume.data.update()
    hp.append(plume)
    rig.rigid("head", hp)

    # pauldrons: big rounded steel shells with two lames and gold rims
    for s, side in ((1, "L"), (-1, "R")):
        sh = []
        for k, (r, dz, dx) in enumerate(((0.105, 0.0, 0.0), (0.09, -0.045, 0.02), (0.075, -0.08, 0.035))):
            d = hemi(r, (0, 0, 0), (0, 0, 1), steel, cut=-0.15, segs=22, rings=10)
            d.data.transform(Matrix.Diagonal((1.0, 0.95, 0.7, 1.0)))
            solid(d, 0.008)
            K.finish(d, steel, smooth=50)
            rim = torus(r * 0.99, 0.007, (0, 0, -0.15 * r * 0.7), gold, verts=22, minor=4, scale=(1, 0.95, 1))
            for o in (d, rim):
                o.data.transform(Matrix.Translation((s * (0.175 + dx), 0.0, 0.625 + dz))
                                 @ Matrix.Rotation(-s * math.radians(28 + 10 * k), 4, "Y"))
            sh += [d, rim]
        rig.rigid("arm." + side, sh)
    limb_set(rig, 1, "L", dark, steel, steel, r_up=0.042, r_fore=0.04, cuff=steel)
    limb_set(rig, -1, "R", dark, steel, steel, r_up=0.042, r_fore=0.04, cuff=steel)
    for s, side in ((1, "L"), (-1, "R")):
        leg_set(rig, s, side, dark, steel, steel, r_th=0.052, r_sh=0.045, knee=steel, sole=leather, boot_top=0.13)
    belt_torch(rig, "knight", (0.11, 0.06, 0.4))

    # the cape: red outside, dark lining, gold clasps at the shoulders
    g = cape_grid(0.63, 0.12, 0.13, 0.24, 0.1, 0.17, curl=0.0, nu=12, nv=10)
    inner = sheet(g, lining, "cape_in")
    outer = sheet([[p + Vector((0, 0.008, 0)) for p in row] for row in g], team, "cape_out")
    outer.data.flip_normals()
    for o in (inner, outer):
        o.data.update()
    clasp = [sphere(0.022, (s * 0.12, 0.07, 0.625), gold, segs=10, rings=6) for s in (-1, 1)]
    rig.custom(w_cape(0.63, 0.51), inner, outer)
    rig.rigid("body", clasp)

    # the axe-hammer in the right fist: an ash haft with steel bands, a crescent blade forward, a hammer face behind
    grip = HAND[-1]
    d = Vector((0, -0.42, 1)).normalized()
    side = Vector((1, 0, 0))
    fwd = d.cross(side).normalized()   # perpendicular to the haft, pointing forward (-Y-ish)
    if fwd.y > 0:
        fwd = -fwd
    a, b = grip - d * 0.14, grip + d * 0.64
    wp = [rod(a, b, 0.016, wood, verts=10), sphere(0.024, a, steel, segs=10, rings=6)]
    for t in (0.05, 0.25, 0.5):
        c = a + (b - a) * t
        wp.append(rod(c - d * 0.012, c + d * 0.012, 0.02, steel, verts=10))
    wp.append(rod(grip - d * 0.06, grip + d * 0.06, 0.02, leather, verts=10))
    head_c = b - d * 0.08
    # the blade: a crescent in the plane of (d, fwd), 0.012 thick
    poly = [(0.0, -0.06), (0.06, -0.075), (0.13, -0.11), (0.155, -0.04), (0.16, 0.02), (0.15, 0.08), (0.12, 0.13),
            (0.06, 0.085), (0.0, 0.06)]
    bm = bmesh.new()
    fr = [bm.verts.new(head_c + fwd * x + d * y + side * -0.007) for x, y in poly]
    bk = [bm.verts.new(head_c + fwd * x + d * y + side * 0.007) for x, y in poly]
    bm.faces.new(fr)
    bm.faces.new(bk[::-1])
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        bm.faces.new((fr[i], bk[i], bk[j], fr[j]))
    blade = new_obj("blade", bm, steel, smooth=20)
    # thin the cutting edge
    for v in blade.data.vertices:
        u = (v.co - head_c).dot(fwd)
        if u > 0.1:
            k = 1 - 0.75 * smoothstep(0.1, 0.16, u)
            off = (v.co - head_c).dot(side)
            v.co -= side * off * (1 - k)
    blade.data.update()
    wp.append(blade)
    wp.append(rod(head_c - d * 0.07, head_c + d * 0.07, 0.03, steel, verts=12))   # the socket
    hm = rod(head_c, head_c - fwd * 0.11, 0.032, steel, r2=0.036, verts=8)        # the hammer behind
    wp.append(hm)
    wp.append(rod(head_c - fwd * 0.11, head_c - fwd * 0.125, 0.04, steel, verts=8))
    wp.append(cone(head_c + d * 0.07, head_c + d * 0.15, 0.022, steel, verts=8))   # the top spike
    wp.append(torus(0.032, 0.007, head_c - d * 0.07, gold, verts=12, minor=4,
                    rot=(math.acos(d.z), 0, 0)))
    rig.rigid("hand.R", wp)
    rig.build("knight")
    rig.pin("muzzle", head_c + d * 0.15, "hand.R")

    base = {"arm.R": (-12, 8, 0), "fore.R": (-50, 0, 0), "phi.R": 8, "arm.L": (0, -8, 0), "fore.L": (-14, 0, 0)}
    hero_anims(rig, "chop", base, phi0={"R": math.degrees(math.atan(0.42))})
    rig.save("knight")


# ------------------------------------------------------------------ the shieldmaiden

def face(rig, c, r, skin, white, pupil, shine, lip, nose=True, eyes_z=0.0, sep=0.036, size=1.0):
    """A plain round head (skin) with eyes, a nose and a small mouth, facing -Y."""
    c = Vector(c)
    rig.rigid("head", ell(c, (r, r * 0.95, r * 1.05), skin, segs=22, rings=14))
    eye_pair(rig, (0, c.y - r * 0.82, c.z + eyes_z), sep, white, pupil, shine, size=size)
    if nose:
        rig.rigid("head", ell((0, c.y - r * 0.98, c.z - 0.012 + eyes_z), (0.012, 0.014, 0.016), skin, segs=8, rings=6))
    if lip:
        m = [(0.018 * math.cos(a), c.y - r * 0.9 - 0.004 * math.sin(a), c.z - 0.045 + eyes_z + 0.005 * math.sin(a))
             for a in (math.pi * (1.15 + 0.7 * k / 4) for k in range(5))]
        rig.rigid("head", tube(m, [0.004] * 5, lip, verts=5, caps=True, name="mouth"))


def feather(base, length, width, d, up, material, thick=0.006):
    """A flat feather from base along d, its broad face facing `up`."""
    d = Vector(d).normalized()
    side = d.cross(Vector(up)).normalized()
    n = Vector(up).normalized()
    pts = [(0.0, 0.0), (0.25, 0.55), (0.6, 0.62), (0.88, 0.45), (1.0, 0.0), (0.88, -0.3), (0.6, -0.42), (0.25, -0.4)]
    bm = bmesh.new()
    top = [bm.verts.new(Vector(base) + d * u * length + side * v * width + n * thick / 2) for u, v in pts]
    bot = [bm.verts.new(Vector(base) + d * u * length + side * v * width - n * thick / 2) for u, v in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    return new_obj("feather", bm, material, smooth=30)


def shieldmaiden():
    reset()
    team = mat("shieldmaiden_team", (0.07, 0.24, 0.78), 0.55, coat=0.15)
    steel = mat("shieldmaiden_steel", (0.7, 0.72, 0.76), 0.28, metal=0.9)
    mail = mat("shieldmaiden_mail", (0.34, 0.35, 0.38), 0.5, metal=0.8)
    fur = mat("shieldmaiden_fur", (0.86, 0.8, 0.68), 0.95)
    skin = mat("shieldmaiden_skin", (0.92, 0.68, 0.54), 0.55)
    hair = mat("shieldmaiden_hair", (0.95, 0.68, 0.22), 0.5, coat=0.2)
    leather = mat("shieldmaiden_leather", (0.33, 0.19, 0.1), 0.7)
    legging = mat("shieldmaiden_legging", (0.16, 0.18, 0.28), 0.75)
    white = mat("shieldmaiden_white", (0.95, 0.94, 0.9), 0.5)
    gold = mat("shieldmaiden_gold", (0.95, 0.72, 0.25), 0.3, metal=0.9)
    eye_w = mat("shieldmaiden_eye", (0.97, 0.96, 0.94), 0.3)
    iris = mat("shieldmaiden_iris", (0.08, 0.22, 0.5), 0.3, coat=0.8)
    shine = mat("shieldmaiden_eye_glow", (1, 1, 1), 0.2, emit=3.0)
    lip = mat("shieldmaiden_lip", (0.62, 0.25, 0.22), 0.5)
    wood = mat("shieldmaiden_wood", (0.36, 0.22, 0.12), 0.75)
    rig = hero_rig()

    # torso: a blue tunic, a leather girdle over the waist, a fur mantle round the shoulders
    trunk(rig, team, extra_mat=leather, split=lambda c: 0.39 < c.z < 0.48,
          prof=[(0.0, 0.665), (0.055, 0.66), (0.105, 0.64), (0.135, 0.605), (0.14, 0.56), (0.125, 0.5),
                (0.11, 0.44), (0.12, 0.38), (0.11, 0.33), (0.0, 0.315)])
    belt = torus(0.116, 0.014, (0, 0, 0.43), leather, verts=28, minor=6, scale=(1, 0.76, 1))
    buckle = torus(0.018, 0.006, (0, -0.09, 0.43), gold, rot=(math.pi / 2, 0, 0), verts=12, minor=4)
    rig.custom(w_trunk, belt, buckle)
    mant = lumpy(1.0, (0, 0, 0), fur, 11, amount=0.1, sub=3, smooth=60)
    for v in mant.data.vertices:
        p = v.co.copy()
        a = math.atan2(p.y, p.x)
        rr = 0.125 + 0.05 * math.sqrt(p.x * p.x + p.y * p.y)
        v.co = Vector((math.cos(a) * rr * 1.18, math.sin(a) * rr * 0.92, 0.63 + 0.045 * p.z))
    mant.data.update()
    rig.custom(lambda p: {"body": 1.0}, mant)
    sk = skirt_mesh(team, 0.44, 0.22, 0.118, 0.16, slit=0.075, name="skirt")
    hem = torus(0.16, 0.008, (0, 0, 0.225), gold, verts=32, minor=4, scale=(1, 0.78, 1))
    rig.custom(w_skirt(0.44, 0.22), sk, hem)
    ml = skirt_mesh(mail, 0.4, 0.2, 0.115, 0.145, name="mail")
    rig.custom(w_skirt(0.42, 0.2), ml)

    # head: a fair face, the winged helm (a steel cap, a gold brow band, a nasal, two white wings)
    face(rig, (0, 0.0, 0.765), 0.094, skin, eye_w, iris, shine, lip, eyes_z=0.005)
    cap = hemi(0.108, (0, 0, 0), (0, 0, 1), steel, cut=-0.05, segs=26, rings=12)
    cap.data.transform(Matrix.Translation((0, 0.008, 0.79)) @ Matrix.Diagonal((1, 1.05, 1.05, 1)))
    hp = [cap, torus(0.108, 0.01, (0, 0.008, 0.787), gold, verts=26, minor=5, scale=(1, 1.05, 1)),
          tube([(0, -0.113, 0.8), (0, -0.112, 0.765), (0, -0.104, 0.735)], [0.009, 0.008, 0.006], steel, verts=6,
               caps=True, name="nasal"),
          tube([(0, -0.1, 0.8), (0, -0.04, 0.9), (0, 0.06, 0.895), (0, 0.11, 0.8)], [0.008] * 4, gold, verts=6,
               caps=True, name="ridge")]
    for s in (-1, 1):
        root = Vector((s * 0.1, 0.02, 0.81))
        nrm = Vector((s * 0.8, 0.0, 0.6))
        for k in range(7):
            th = math.radians(8 + 13 * k)
            d = Vector((s * 0.3, math.sin(th), math.cos(th)))
            ln = (0.11 + 0.08 * math.sin(math.pi * (k + 1) / 8)) * (1.15 if k < 3 else 1.0)
            hp.append(feather(root + Vector((s * 0.004 * k, 0.006 * k, -0.005 * k)), ln, 0.026,
                              d, nrm + Vector((0, 0, 0.0)), white if k % 2 == 0 else fur, thick=0.008))
        hp.append(sphere(0.024, root, gold, segs=10, rings=6))
    # hair: a golden mass behind and two thick braids over the shoulders onto the chest
    hp.append(ell((0, 0.05, 0.72), (0.09, 0.07, 0.08), hair, segs=16, rings=10))
    rig.rigid("head", hp)
    for s in (-1, 1):
        pts = [Vector(p) for p in ((s * 0.075, 0.03, 0.73), (s * 0.11, 0.0, 0.66), (s * 0.115, -0.07, 0.6),
                                   (s * 0.1, -0.11, 0.52), (s * 0.095, -0.115, 0.46))]
        path = smooth_path(pts, 3)
        br = [tube(path, [0.026] * len(path), hair, verts=8, caps=True, name="braid")]
        for k in range(1, len(path) - 1):
            br.append(sphere(0.028 - 0.0008 * k, path[k], hair, segs=10, rings=6, scale=(1, 1, 0.8)))
        br.append(torus(0.024, 0.008, path[-2], leather, verts=10, minor=4))
        br.append(cone(path[-1], path[-1] + Vector((0, -0.01, -0.05)), 0.024, hair, verts=8))

        def w_braid(p):
            t = smoothstep(0.7, 0.62, p.z)
            return {"head": 1 - t + 1e-4, "body": t + 1e-4}
        rig.custom(w_braid, br)

    # arms: bare upper arms with silver rings, leather bracers; legs: leggings, fur-topped boots
    limb_set(rig, 1, "L", skin, skin, skin, r_up=0.038, r_fore=0.034, cuff=leather)
    limb_set(rig, -1, "R", skin, skin, skin, r_up=0.038, r_fore=0.034, cuff=leather)
    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("arm." + side, torus(0.04, 0.007, (s * 0.18, 0.004, 0.52), steel, verts=12, minor=4))
        rig.rigid("arm." + side, ell((s * 0.16, 0.0, 0.6), (0.06, 0.06, 0.045), team, segs=12, rings=8))
        leg_set(rig, s, side, legging, legging, leather, r_th=0.046, r_sh=0.04, sole=leather, boot_top=0.17,
                cuff=fur)
    belt_torch(rig, "shieldmaiden", (-0.1, 0.07, 0.4), lean=(0.45, 0.6))

    # the round shield on the left forearm: blue face, a white sunwheel, a steel rim and boss
    n = Vector((0.85, -0.5, 0.0)).normalized()
    c = HAND[1] + Vector((0.055, -0.02, 0.07))
    sh = [lathe_r([(0.0, 0.03), (0.06, 0.026), (0.12, 0.016), (0.16, 0.004), (0.165, -0.004), (0.15, -0.01),
                   (0.0, -0.004)], team, segs=36, name="shield", smooth=40),
          torus(0.163, 0.011, (0, 0, 0.0), steel, verts=36, minor=6),
          lathe_r([(0.0, 0.058), (0.025, 0.054), (0.04, 0.035), (0.045, 0.026)], steel, segs=20, name="boss")]
    for k in range(8):   # a white sunwheel: rays between a ring and the boss
        a = 2 * math.pi * k / 8
        p0 = Vector((0.05 * math.cos(a), 0.05 * math.sin(a), 0.03))
        p1 = Vector((0.135 * math.cos(a + 0.35), 0.135 * math.sin(a + 0.35), 0.012))
        sh.append(tube([p0, (p0 + p1) / 2 + Vector((0, 0, 0.004)), p1], [0.009, 0.012, 0.007], white, verts=5,
                       caps=True, name="ray"))
    ring = [Vector((0.138 * math.cos(a), 0.138 * math.sin(a), 0.011)) for a in (2 * math.pi * k / 40 for k in range(41))]
    sh.append(tube(ring, [0.006] * 41, white, verts=5, caps=False, name="ring"))
    for k in range(10):
        a = 2 * math.pi * k / 10
        sh.append(sphere(0.008, (0.163 * math.cos(a), 0.163 * math.sin(a), 0.012), gold, segs=6, rings=4))
    q = Vector((0, 0, 1)).rotation_difference(n)
    xform(sh, Matrix.Translation(c) @ q.to_matrix().to_4x4())
    rig.rigid("fore.L", sh)

    # the sword in the right fist, point up and a little forward
    grip = HAND[-1]
    d = Vector((0, -0.4, 1)).normalized()
    side = Vector((1, 0, 0))
    fl = d.cross(side).normalized()
    sw = [rod(grip - d * 0.06, grip + d * 0.05, 0.015, leather, verts=8),
          sphere(0.022, grip - d * 0.075, gold, segs=10, rings=6),
          rod(grip + d * 0.055 - side * 0.075, grip + d * 0.055 + side * 0.075, 0.011, gold, verts=8)]
    for s in (-1, 1):
        sw.append(sphere(0.015, grip + d * 0.055 + side * s * 0.078, gold, segs=8, rings=6))
    L = 0.42
    bm = bmesh.new()
    prof = [(0.0, 0.022), (0.8, 0.019), (0.93, 0.012), (1.0, 0.0)]
    vs = []
    for u, w in prof:
        b = grip + d * (0.065 + u * L)
        vs.append([bm.verts.new(b + side * w), bm.verts.new(b + fl * 0.006), bm.verts.new(b - side * w),
                   bm.verts.new(b - fl * 0.006)])
    for r0, r1 in zip(vs, vs[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
    bm.faces.new(vs[0][::-1])
    sw.append(new_obj("blade", bm, steel, smooth=0))
    rig.rigid("hand.R", sw)
    rig.build("shieldmaiden")
    rig.pin("muzzle", grip + d * (0.065 + L), "hand.R")
    base = {"arm.R": (-10, 8, 0), "fore.R": (-50, 0, 0), "phi.R": 30, "arm.L": (-8, -6, 0), "fore.L": (-40, 0, 10)}
    hero_anims(rig, "slash", base, cape=False, phi0={"R": math.degrees(math.atan(0.4))})
    rig.save("shieldmaiden")


# ------------------------------------------------------------------ the mage

def star_prism(c, r, material, n_axis=(0, -1, 0), depth=0.006, points=5):
    poly = []
    for k in range(points * 2):
        a = math.pi / 2 + math.pi * k / points
        rr = r if k % 2 == 0 else r * 0.45
        poly.append((rr * math.cos(a), rr * math.sin(a)))
    o = prism(poly, depth, (0, 0, 0), material, bevel=0.0)
    q = Vector((0, -1, 0)).rotation_difference(Vector(n_axis).normalized())
    o.data.transform(Matrix.Translation(Vector(c)) @ q.to_matrix().to_4x4())
    return o


def mage():
    reset()
    team = mat("mage_team", (0.95, 0.72, 0.08), 0.6, coat=0.1)
    trim = mat("mage_trim", (0.32, 0.08, 0.3), 0.6)
    gold = mat("mage_gold", (1.0, 0.8, 0.3), 0.3, metal=0.9)
    skin = mat("mage_skin", (0.9, 0.7, 0.58), 0.55)
    beard = mat("mage_beard", (0.9, 0.9, 0.92), 0.8)
    eye_w = mat("mage_eye", (0.97, 0.96, 0.94), 0.3)
    iris = mat("mage_iris", (0.1, 0.3, 0.25), 0.3, coat=0.8)
    shine = mat("mage_eye_glow", (1, 1, 1), 0.2, emit=3.0)
    wood = mat("mage_wood", (0.28, 0.17, 0.09), 0.8)
    orb = mat("mage_staff_glow", (1.0, 0.85, 0.4), 0.2, emit=6.0, emit_color=(1.0, 0.75, 0.3))
    orb_core = mat("mage_staff_core_glow", (1.0, 1.0, 0.9), 0.2, emit=12.0)
    slipper = mat("mage_slipper", (0.3, 0.07, 0.28), 0.5)
    rig = hero_rig()

    # the robe: one lathe from the collar to the floor, its skirt following the legs; a plum band down the front,
    # a hem band, a sash; gold stars sewn on the skirt
    robe = lathe_r([(0.0, 0.665), (0.055, 0.66), (0.11, 0.64), (0.14, 0.6), (0.14, 0.55), (0.127, 0.49),
                    (0.118, 0.44), (0.13, 0.38), (0.15, 0.3), (0.17, 0.2), (0.19, 0.1), (0.2, 0.03), (0.19, 0.018),
                    (0.0, 0.02)], team, segs=36, name="robe", smooth=60)
    for v in robe.data.vertices:
        v.co.y *= 0.78
    robe.data.update()
    sk = w_skirt(0.44, 0.02)

    def w_robe(p):
        return w_trunk(p) if p.z > 0.44 else sk(p)
    rig.custom(w_robe, robe)
    band = [tube([(0, -0.103, 0.6), (0, -0.098, 0.5), (0, -0.095, 0.44)], [0.016] * 3, trim, verts=6, caps=True)]
    rig.custom(w_trunk, band)
    fb = []
    for k in range(9):
        z = 0.42 - 0.4 * k / 8
        r = 0.118 + (0.2 - 0.118) * min(1, (0.44 - z) / 0.42) ** 0.9
        fb.append(Vector((0, -r * 0.78 - 0.004, z)))
    lower = [tube(fb, [0.017] * len(fb), trim, verts=6, caps=True, name="band"),
             torus(0.199, 0.014, (0, 0, 0.035), trim, verts=40, minor=5, scale=(1, 0.78, 1))]
    rnd = random.Random(7)
    for k in range(9):
        a = math.radians(-60 + 120 * rnd.random()) + (math.pi if k % 3 == 2 else 0)
        z = rnd.uniform(0.08, 0.36)
        r = 0.118 + (0.2 - 0.118) * min(1, (0.44 - z) / 0.42) ** 0.9 + 0.002
        p = Vector((r * math.sin(a), -r * 0.78 * math.cos(a), z))
        if abs(p.x) < 0.03:
            continue
        lower.append(star_prism(p, 0.016, gold, n_axis=(math.sin(a), -math.cos(a) * 0.78, 0)))
    rig.custom(sk, lower)
    sash = [torus(0.122, 0.018, (0, 0, 0.44), trim, verts=28, minor=6, scale=(1, 0.8, 1)),
            tube([(0.05, -0.095, 0.44), (0.06, -0.11, 0.38), (0.065, -0.12, 0.31)], [0.016, 0.014, 0.012], trim,
                 verts=6, caps=True), tube([(0.04, -0.095, 0.44), (0.03, -0.112, 0.37), (0.025, -0.12, 0.33)],
                                         [0.014, 0.012, 0.01], trim, verts=6, caps=True)]
    rig.custom(w_trunk, sash)
    # a plum shoulder mantle with a high collar behind the head and a gold clasp
    mant = hemi(0.17, (0, 0, 0), (0, 0, 1), trim, cut=0.2, segs=30, rings=12)
    mant.data.transform(Matrix.Translation((0, 0.0, 0.53)) @ Matrix.Diagonal((1.02, 0.85, 0.75, 1)))
    solid(mant, 0.01)
    K.finish(mant, trim, smooth=50)
    collar = sheet([[Vector((0.1 * math.cos(a), 0.06 + 0.055 * math.sin(a) * -1 + 0.11, z)) for a in
                     (math.radians(200 + 140 * j / 10) for j in range(11))] for z in (0.62, 0.7, 0.77)], trim, "collar",
                   thick=0.008)
    for v in collar.data.vertices:
        v.co.y = v.co.y - 0.11 + 0.02 * (v.co.z - 0.62) / 0.15 * 1.5
    collar.data.update()
    rig.custom(lambda p: {"body": 1.0}, mant, collar, sphere(0.022, (0, -0.1, 0.63), gold, segs=10, rings=6))

    # the head: an old face, bushy white brows, a long beard and moustache; the tall hat bending back
    face(rig, (0, 0.0, 0.75), 0.088, skin, eye_w, iris, shine, None, eyes_z=0.01, sep=0.034)
    rig.rigid("head", ell((0, -0.094, 0.745), (0.018, 0.028, 0.028), skin, pitch=20, segs=10, rings=8))
    hp = []
    for s in (-1, 1):
        hp.append(ell((s * 0.036, -0.078, 0.784), (0.026, 0.014, 0.011), beard, roll=s * 14, segs=10, rings=6))
        hp.append(tube([(s * 0.008, -0.093, 0.722), (s * 0.04, -0.09, 0.715), (s * 0.06, -0.08, 0.69)],
                       [0.012, 0.012, 0.004], beard, verts=7, caps=True, name="moustache"))
    bp = [Vector(p) for p in ((0, -0.06, 0.72), (0, -0.095, 0.66), (0, -0.115, 0.58), (0, -0.12, 0.5),
                              (0, -0.115, 0.44))]
    path = smooth_path(bp, 3)
    bd = tube(path, [0.06, 0.062, 0.06, 0.057, 0.052, 0.046, 0.04, 0.034, 0.028, 0.02, 0.014, 0.008, 0.002][:len(path)],
              beard, verts=12, caps=True, name="beard")
    for v in bd.data.vertices:
        v.co.y = -0.06 + (v.co.y + 0.06) * 1.0
        if v.co.y > -0.05:
            v.co.y = -0.05 + (v.co.y + 0.05) * 0.4
    bd.data.update()
    hp.append(bd)
    # the hat: a wide brim and a tall cone whose tip bends back
    brim = lathe_r([(0.105, 0.835), (0.17, 0.83), (0.215, 0.818), (0.222, 0.81), (0.17, 0.818), (0.1, 0.822)],
                   team, segs=40, name="brim", smooth=40)
    cpts = [Vector((0, 0.0, 0.82)), Vector((0, 0.01, 0.92)), Vector((0, 0.025, 1.0)), Vector((0, 0.055, 1.07)),
            Vector((0, 0.11, 1.11)), Vector((0, 0.17, 1.1))]
    cp = smooth_path(cpts, 3)
    rads = [0.112 * (1 - i / (len(cp) - 1)) ** 1.1 + 0.004 for i in range(len(cp))]
    cone_o = tube(cp, rads, team, verts=24, caps=True, name="hatcone")
    hp += [brim, cone_o, torus(0.108, 0.016, (0, 0.004, 0.845), trim, verts=28, minor=6),
           star_prism((0, -0.122, 0.848), 0.026, gold, depth=0.01)]
    rig.rigid("head", hp)

    # sleeves: wide yellow sleeves flaring to a plum cuff; hands; pointed plum slippers
    for s, side in ((1, "L"), (-1, "R")):
        sh, el = Vector(HERO_BONES["arm." + side][0]), Vector(HERO_BONES["arm." + side][1])
        wr = Vector(HERO_BONES["fore." + side][1])
        rig.rigid("arm." + side, [rod(sh, el, 0.046, team, r2=0.05, verts=14), sphere(0.05, sh, team, segs=14, rings=8)])
        rig.rigid("fore." + side, [rod(el, wr + (wr - el) * 0.05, 0.05, team, r2=0.075, verts=16),
                                   torus(0.074, 0.012, wr + (wr - el) * 0.05, trim, verts=16, minor=5,
                                         rot=(math.radians(-17), 0, 0))])
        rig.rigid("hand." + side, ell(HAND[s], (0.032, 0.038, 0.036), skin, segs=12, rings=8))
        an = Vector(HERO_BONES["shin." + side][1])
        ft = [ell((an.x, -0.05, 0.03), (0.045, 0.08, 0.032), slipper, segs=14, rings=8),
              tube([(an.x, -0.11, 0.025), (an.x, -0.15, 0.035), (an.x, -0.16, 0.065)], [0.026, 0.014, 0.004],
                   slipper, verts=10, caps=True, name="toe")]
        for v in ft[0].data.vertices:
            v.co.z = max(v.co.z, 0.004)
        rig.rigid("foot." + side, ft)
        rig.rigid("shin." + side, rod((an.x, 0, 0.2), an, 0.035, slipper, verts=8))
    belt_torch(rig, "mage", (0.1, 0.07, 0.43), lean=(0.4, 0.6))

    # the staff: a gnarled stave whose head curls round a glowing orb
    grip = HAND[-1]
    d = Vector((0, -0.18, 1)).normalized()
    a, b = grip - d * 0.29, grip + d * 0.6
    st = [tube([a, a + (b - a) * 0.3 + Vector((0.008, 0, 0)), a + (b - a) * 0.6 + Vector((-0.01, 0, 0)), b],
               [0.016, 0.018, 0.017, 0.02], wood, verts=10, caps=True, name="staff")]
    for t in (0.42, 0.66):
        st.append(sphere(0.022, a + (b - a) * t, wood, segs=8, rings=6))
    oc = b + d * 0.08 + Vector((0, -0.01, 0))
    curl = []
    for k in range(15):
        u = k / 14
        ang = math.radians(-100 + 300 * u)
        r = 0.065 - 0.03 * u
        curl.append(oc + Vector((0, r * math.cos(ang) * 1.0, r * math.sin(ang))))
    curl[0] = b
    st.append(tube(curl, [0.02 - 0.012 * k / 14 for k in range(15)], wood, verts=8, caps=True, name="curl"))
    st.append(torus(0.022, 0.006, b - d * 0.01, gold, verts=12, minor=4))
    st += [sphere(0.042, oc, orb, segs=18, rings=12), sphere(0.022, oc, orb_core, segs=10, rings=6)]
    rig.rigid("hand.R", st)
    rig.build("mage")
    rig.pin("muzzle", oc, "hand.R")
    base = {"arm.R": (-12, 8, 0), "fore.R": (-50, 0, 0), "phi.R": 4, "arm.L": (-4, -8, 0), "fore.L": (-24, 0, 0)}
    hero_anims(rig, "cast", base, cape=False, phi0={"R": math.degrees(math.atan(0.18))})
    rig.save("mage")


# ------------------------------------------------------------------ the ranger

def ranger():
    reset()
    team = mat("ranger_team", (0.12, 0.48, 0.14), 0.7)
    lining = mat("ranger_lining", (0.07, 0.2, 0.07), 0.8)
    leather = mat("ranger_leather", (0.42, 0.25, 0.12), 0.65)
    dark = mat("ranger_cloth", (0.17, 0.15, 0.12), 0.85)
    skin = mat("ranger_skin", (0.86, 0.64, 0.5), 0.55)
    mask = mat("ranger_mask", (0.24, 0.27, 0.22), 0.85)
    eye_w = mat("ranger_eye", (0.97, 0.96, 0.94), 0.3)
    iris = mat("ranger_iris", (0.3, 0.45, 0.12), 0.3, coat=0.8)
    shine = mat("ranger_eye_glow", (1, 1, 1), 0.2, emit=3.0)
    wood = mat("ranger_wood", (0.45, 0.27, 0.12), 0.55, coat=0.3)
    string = mat("ranger_string", (0.9, 0.88, 0.8), 0.6)
    fletch = mat("ranger_fletch", (0.85, 0.15, 0.08), 0.6)
    brass = mat("ranger_brass", (0.85, 0.65, 0.3), 0.35, metal=0.9)
    rig = hero_rig({"bow": ((0.207, -0.045, 0.31), (0.207, -0.045, 0.45), "fore.L"),
                    "nock": ((0.207, 0.02, 0.31), (0.207, 0.06, 0.31), "bow")})

    # torso: a leather jerkin over a dark shirt, a belt with pouches, the jerkin's tails
    trunk(rig, leather, extra_mat=team, split=lambda c: c.z > 0.6,
          prof=[(0.0, 0.665), (0.055, 0.66), (0.105, 0.64), (0.135, 0.605), (0.138, 0.56), (0.124, 0.5),
                (0.11, 0.44), (0.118, 0.38), (0.108, 0.33), (0.0, 0.315)])
    for k in range(4):   # lacing on the jerkin
        z = 0.47 + 0.035 * k
        rig.rigid("body", tube([(-0.02, -0.1, z), (0.02, -0.1, z + 0.02)], [0.004, 0.004], dark, verts=4))
    belt = [torus(0.114, 0.014, (0, 0, 0.42), dark, verts=28, minor=6, scale=(1, 0.76, 1)),
            box((0.035, 0.012, 0.03), (0, -0.088, 0.42), brass, bevel=0.005)]
    for s in (-1, 1):
        belt.append(box((0.05, 0.035, 0.055), (s * 0.085, -0.055, 0.39), leather, bevel=0.012))
    rig.custom(w_trunk, belt)
    sk = skirt_mesh(leather, 0.43, 0.27, 0.112, 0.145, slit=0.07, name="tails")
    rig.custom(w_skirt(0.43, 0.27), sk)

    # head: face with a scarf mask over the nose and mouth; the green hood with a point down the back
    face(rig, (0, 0.0, 0.76), 0.088, skin, eye_w, iris, shine, None, eyes_z=0.012, sep=0.033)
    mk = hemi(0.093, (0, 0, 0), (0, -1, -1.1), mask, cut=0.62, segs=22, rings=12)
    mk.data.transform(Matrix.Translation((0, 0.0, 0.755)))
    hood = lathe_r([(0.0, 0.88), (0.06, 0.875), (0.1, 0.85), (0.118, 0.8), (0.12, 0.74), (0.112, 0.69),
                    (0.1, 0.66)], team, segs=30, name="hood", smooth=60)
    solid(hood, 0.012)

    def open_face(bm):
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < -0.04
                                   and 0.67 < f.calc_center_median().z < 0.83
                                   and abs(f.calc_center_median().x) < 0.085], context="FACES")
    from prism_models import edit
    edit(hood, open_face)
    K.finish(hood, team, smooth=60)
    for v in hood.data.vertices:   # a peak over the brow, drawn forward
        if v.co.y < 0 and v.co.z > 0.8:
            v.co.y -= 0.025 * smoothstep(0.8, 0.86, v.co.z) * (1 - abs(v.co.x) / 0.12)
    hood.data.update()
    tip = tube([(0, 0.08, 0.84), (0, 0.13, 0.78), (0, 0.16, 0.7), (0, 0.17, 0.64)], [0.05, 0.035, 0.018, 0.004],
               team, verts=10, caps=True, name="liripipe")
    rig.rigid("head", [mk, hood, tip])
    # a short shoulder cape of the hood, then the cloak
    sc = hemi(0.16, (0, 0, 0), (0, 0, 1), team, cut=0.25, segs=30, rings=10)
    sc.data.transform(Matrix.Translation((0, 0.0, 0.535)) @ Matrix.Diagonal((1.0, 0.85, 0.75, 1)))
    solid(sc, 0.01)
    K.finish(sc, team, smooth=50)
    rig.custom(lambda p: {"body": 1.0}, sc)
    g = cape_grid(0.6, 0.2, 0.13, 0.22, 0.1, 0.16, nu=12, nv=10, scallop=0.02)
    inner = sheet(g, lining, "cloak_in")
    outer = sheet([[p + Vector((0, 0.008, 0)) for p in row] for row in g], team, "cloak_out")
    outer.data.flip_normals()
    rig.custom(w_cape(0.6, 0.4), inner, outer)

    # the quiver across the back, full of red-fletched arrows, on a strap over the chest
    qa, qb = Vector((0.07, 0.15, 0.32)), Vector((-0.05, 0.17, 0.62))
    qd = (qb - qa).normalized()
    qv = [rod(qa, qb, 0.042, leather, r2=0.046, verts=14), torus(0.046, 0.008, qb - qd * 0.01, brass, verts=14, minor=4,
                                                                  rot=(0, math.atan2(qd.x, qd.z), 0)),
          torus(0.043, 0.007, qa + qd * 0.04, dark, verts=14, minor=4, rot=(0, math.atan2(qd.x, qd.z), 0))]
    for k in range(6):
        off = Vector((0.022 * math.cos(k * 2.1), 0.018 * math.sin(k * 2.1), 0))
        s0 = qb - qd * 0.03 + off
        s1 = s0 + qd * (0.09 + 0.012 * (k % 3)) + Vector((0, 0.01 * (k % 2), 0))
        qv.append(rod(s0, s1, 0.005, wood, verts=5))
        sd = (s1 - s0).normalized()
        for j in range(3):
            a = 2 * math.pi * j / 3 + k
            pr = Vector((math.cos(a), math.sin(a), 0))
            pr = (pr - sd * pr.dot(sd)).normalized()
            qv.append(prism([(0.0, 0.0), (0.0, 0.05), (0.018, 0.035), (0.016, 0.0)], 0.003, (0, 0, 0), fletch,
                            bevel=0.0))
            o = qv[-1]
            M = Matrix.Translation(s1 - sd * 0.055) @ Matrix(((pr.x, sd.cross(pr).x, sd.x, 0),
                                                              (pr.y, sd.cross(pr).y, sd.y, 0),
                                                              (pr.z, sd.cross(pr).z, sd.z, 0), (0, 0, 0, 1)))
            # prism lies in XZ: X -> pr (out), Z -> sd (along)
            o.data.transform(Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
            o.data.transform(M)
    strap = [Vector(p) for p in ((-0.05, 0.13, 0.62), (-0.1, 0.0, 0.63), (-0.08, -0.1, 0.56), (0.0, -0.11, 0.48),
                                 (0.09, -0.08, 0.4), (0.1, 0.05, 0.36))]
    qv.append(tube(smooth_path(strap, 3), [0.011] * len(smooth_path(strap, 3)), dark, verts=6, caps=True, name="strap"))
    rig.custom(w_trunk, qv)

    # arms in dark sleeves, leather bracers and gloves; legs in dark breeches, tall boots
    limb_set(rig, 1, "L", team, team, leather, r_up=0.037, r_fore=0.033, cuff=leather, hand_bone="bow")
    limb_set(rig, -1, "R", team, team, leather, r_up=0.037, r_fore=0.033, cuff=leather)
    for s, side in ((1, "L"), (-1, "R")):
        leg_set(rig, s, side, dark, dark, leather, r_th=0.044, r_sh=0.038, sole=dark, boot_top=0.2)
        rig.rigid("shin." + side, torus(0.05, 0.01, (s * 0.08, 0.0, 0.2), leather, verts=12, minor=4))
    belt_torch(rig, "ranger", (-0.1, 0.06, 0.4), lean=(0.45, 0.65))

    # the bow in the left fist: a recurve stave in the YZ plane, its belly forward, the string behind
    g0 = HAND[1]
    L = 0.33
    pts_up, pts_dn = [], []
    for k in range(9):
        u = k / 8
        y = -0.06 * math.sin(math.pi * 0.85 * u) + 0.03 * smoothstep(0.82, 1.0, u)
        pts_up.append(g0 + Vector((0, y, L * u)))
        pts_dn.append(g0 + Vector((0, y, -L * u)))
    bw = [tube(pts_up, [0.014 - 0.008 * k / 8 for k in range(9)], wood, verts=8, caps=True, name="limb"),
          tube(pts_dn, [0.014 - 0.008 * k / 8 for k in range(9)], wood, verts=8, caps=True, name="limb"),
          rod(g0 - Vector((0, 0, 0.05)), g0 + Vector((0, 0, 0.05)), 0.018, dark, verts=10)]
    for p in (pts_up[-1], pts_dn[-1]):
        bw.append(sphere(0.008, p, brass, segs=6, rings=4))
    rig.rigid("bow", bw)
    nockp = Vector((0.207, 0.02, 0.31))
    s_pts = [pts_up[-1] + (nockp - pts_up[-1]) * (k / 6) for k in range(7)] + \
            [nockp + (pts_dn[-1] - nockp) * (k / 6) for k in range(1, 7)]
    sto = tube(s_pts, [0.0035] * len(s_pts), string, verts=4, caps=False, name="string")

    def w_string(p):
        t = 1 - min(1.0, abs(p.z - nockp.z) / L)
        t = t ** 2
        return {"bow": 1 - t + 1e-4, "nock": t + 1e-4}
    rig.custom(w_string, sto)
    rig.build("ranger")
    rig.pin("muzzle", g0 + Vector((0, -0.07, 0.0)), "bow")
    base = {"arm.L": (-8, -6, 0), "fore.L": (-46, 0, 0), "bow": (26, 0, 0), "arm.R": (0, 8, 0), "fore.R": (-16, 0, 0)}
    hero_anims(rig, "draw", base, cape=True)
    rig.save("ranger")


# ------------------------------------------------------------------ monsters

def glow_eyes(c, sep, r, material, yaw=20, slant=0.0, squash=0.6):
    out = []
    for s in (-1, 1):
        out.append(ell((s * sep, c[1], c[2]), (r, r * 0.5, r * squash), material, yaw=-s * yaw, roll=s * slant,
                       segs=10, rings=6))
    return out


def ghost():
    reset()
    body_m = mat("ghost_glow", (0.62, 0.9, 1.0), 0.3, emit=1.4, alpha=0.62, emit_color=(0.45, 0.85, 1.0))
    wisp_m = mat("ghost_wisp_glow", (0.5, 0.8, 1.0), 0.3, emit=1.0, alpha=0.4, emit_color=(0.35, 0.7, 1.0))
    hole = mat("ghost_hollow", (0.01, 0.03, 0.08), 0.6)
    eye = mat("ghost_eye_glow", (0.8, 1.0, 1.0), 0.2, emit=8.0)
    rig = Rig({"root": ((0, 0, 0), (0, 0, 0.06), None),
               "body": ((0, 0.0, 0.3), (0, 0, 0.62), "root"),
               "head": ((0, 0, 0.62), (0, -0.02, 0.92), "body"),
               "arm.L": ((0.14, -0.02, 0.6), (0.27, -0.16, 0.48), "body"),
               "arm.R": ((-0.14, -0.02, 0.6), (-0.27, -0.16, 0.48), "body"),
               "tail": ((0, 0.07, 0.45), (0, 0.2, 0.28), "body"),
               "tail2": ((0, 0.2, 0.28), (0, 0.46, 0.2), "tail")})
    # the shroud: a hooded head flowing into a body that thins to a wisp trailing behind and below
    path = [Vector(p) for p in ((0, -0.03, 0.9), (0, -0.01, 0.78), (0, 0.02, 0.62), (0, 0.07, 0.47), (0, 0.15, 0.35),
                                (0, 0.26, 0.26), (0, 0.38, 0.21), (0, 0.5, 0.2))]
    pp = smooth_path(path, 3)
    rads = [0.09, 0.125, 0.15, 0.16, 0.165, 0.165, 0.16, 0.15, 0.14, 0.13, 0.115, 0.1, 0.085, 0.07, 0.055, 0.04,
            0.028, 0.018, 0.01, 0.004, 0.002, 0.001]
    sh = tube(pp, (rads + [0.001] * 40)[:len(pp)], body_m, verts=20, caps=True, name="shroud")
    rnd = random.Random(5)
    for v in sh.data.vertices:   # ripples down the body
        z = v.co.z
        a = math.atan2(v.co.x, -v.co.y + 0.1)
        v.co.x *= 1.0 + 0.08 * math.sin(a * 5 + z * 20) * smoothstep(0.6, 0.3, z)
    sh.data.update()

    def w_sh(p):
        h = smoothstep(0.6, 0.7, p.z)
        t1 = smoothstep(0.08, 0.2, p.y) * (1 - h)
        t2 = smoothstep(0.22, 0.34, p.y)
        return {"head": h + 1e-4, "body": (1 - h) * (1 - t1) + 1e-4, "tail": t1 * (1 - t2) + 1e-4, "tail2": t2 + 1e-4}
    rig.custom(w_sh, sh)
    # ragged streamers hanging from the body
    st = []
    for k in range(7):
        a = math.radians(-150 + 300 * k / 6)
        b0 = Vector((0.15 * math.sin(a), 0.05 - 0.13 * math.cos(a), 0.47))
        pts = [b0, b0 + Vector((0.03 * math.sin(a), 0.1, -0.08)), b0 + Vector((0.05 * math.sin(a), 0.22 + 0.04 * (k % 2), -0.14))]
        st.append(tube(pts, [0.032, 0.02, 0.003], wisp_m, verts=6, caps=True, name="streamer"))
    rig.custom(w_sh, st)
    # the face: hollow eye pits with glowing points, a long wailing mouth
    fc = []
    for s in (-1, 1):
        fc.append(ell((s * 0.048, -0.122, 0.8), (0.034, 0.02, 0.045), hole, yaw=-s * 20, roll=s * 18, segs=12, rings=8))
        fc.append(sphere(0.016, (s * 0.048, -0.138, 0.8), eye, segs=8, rings=6))
    fc.append(ell((0, -0.13, 0.7), (0.035, 0.02, 0.058), hole, segs=12, rings=8))
    rig.rigid("head", fc)
    # arms: wisps ending in long clawed hands
    for s, side in ((1, "L"), (-1, "R")):
        a = [tube([(s * 0.12, -0.02, 0.62), (s * 0.2, -0.08, 0.56), (s * 0.27, -0.16, 0.48)], [0.05, 0.035, 0.025],
                  body_m, verts=10, caps=True, name="arm")]
        for k in range(3):
            base = Vector((s * 0.27, -0.16, 0.48))
            a.append(cone(base, base + Vector((s * (0.02 + 0.02 * (k - 1)), -0.08, -0.03 + 0.03 * (k - 1))), 0.012,
                          body_m, verts=6))
        rig.rigid("arm." + side, a)
    rig.build("ghost")

    def float_p(k, reach=0.0, extra=None):
        a = 2 * math.pi * k
        return merge({"@root": (0, 0, 0.06 + 0.05 * math.sin(a)), "body": (10 + 4 * math.sin(a), 0, 4 * math.sin(a)),
                      "head": (-6 * math.sin(a + 1), 0, 6 * math.sin(a)),
                      "tail": (14 + 12 * math.sin(a + 1.2), 0, 18 * math.sin(a + 0.5)),
                      "tail2": (16 + 14 * math.sin(a + 2), 0, 26 * math.sin(a + 1.4)),
                      "arm.L": (-20 - 15 * math.sin(a) - reach, -10, 0), "arm.R": (-20 + 15 * math.sin(a) - reach, 10, 0)},
                     extra or {})
    rig.action("walk", {f: float_p(f / 30) for f in (0, 5, 10, 15, 20, 25, 30)}, loop=True)
    lunge = {"@root": (0, -0.12, 0.06), "body": (26, 0, 0), "head": (-10, 0, 0), "%head": (1.05, 1.05, 1.15),
             "arm.L": (-70, -20, 0), "arm.R": (-70, 20, 0), "tail": (30, 0, 0), "tail2": (30, 0, 0)}
    rig.action("attack", {0: float_p(0), 4: merge(float_p(0.1), {"body": (-14, 0, 0), "arm.L": (-60, -50, 0),
                                                              "arm.R": (-60, 50, 0), "@root": (0, 0.04, 0.1)}),
                          7: lunge, 12: float_p(0)})
    rig.action("die", {0: float_p(0), 4: merge(float_p(0), {"%root": (1.15, 1.15, 0.85), "head": (-30, 0, 0),
                                                            "arm.L": (-10, -80, 0), "arm.R": (-10, 80, 0)}),
                       14: {"@root": (0, 0, 0.25), "%root": (1.3, 1.3, 1.6), "head": (-40, 0, 0), "tail": (-30, 0, 0),
                            "arm.L": (0, -120, 0), "arm.R": (0, 120, 0)},
                       24: {"@root": (0, 0, 0.4), "%root": (0.01, 0.01, 0.01)}})
    rig.save("ghost")


def biped_bones(h=1.0, w=1.0, extra=None):
    """A stocky biped (facing -Y), scaled by height h and width w."""
    def P(x, y, z):
        return (x * w, y, z * h)
    b = {"root": ((0, 0, 0), (0, 0, 0.06), None),
         "hips": (P(0, 0, 0.36), P(0, 0, 0.45), "root"),
         "body": (P(0, 0, 0.45), P(0, 0, 0.66), "hips"),
         "head": (P(0, 0, 0.66), P(0, 0, 0.9), "body"),
         "arm.L": (P(0.17, 0, 0.6), P(0.21, 0.0, 0.45), "body"),
         "arm.R": (P(-0.17, 0, 0.6), P(-0.21, 0.0, 0.45), "body"),
         "fore.L": (P(0.21, 0, 0.45), P(0.22, -0.04, 0.32), "arm.L"),
         "fore.R": (P(-0.21, 0, 0.45), P(-0.22, -0.04, 0.32), "arm.R"),
         "leg.L": (P(0.08, 0, 0.36), P(0.085, 0, 0.2), "hips"),
         "leg.R": (P(-0.08, 0, 0.36), P(-0.085, 0, 0.2), "hips"),
         "shin.L": (P(0.085, 0, 0.2), P(0.085, 0.005, 0.07), "leg.L"),
         "shin.R": (P(-0.085, 0, 0.2), P(-0.085, 0.005, 0.07), "leg.R")}
    b.update(extra or {})
    return b


def walk_cycle(rig, frames, stride=26, bob=0.03, lean=8, twist=6, arm=24, extra=None, arm_r=None):
    """A plain two-step walk: f0 left forward, f/4 passing, f/2 right forward."""
    def p(ph, up):
        L, R = ("L", "R") if ph == 0 else ("R", "L")
        sg = 1 if ph == 0 else -1
        if not up:
            legs = {"leg." + L: (-stride, 0, 0), "shin." + L: (6, 0, 0), "leg." + R: (stride * 0.8, 0, 0),
                    "shin." + R: (stride, 0, 0)}
        else:
            legs = {"leg." + R: (-stride, 0, 0), "shin." + R: (stride * 2, 0, 0), "leg." + L: (6, 0, 0),
                    "shin." + L: (4, 0, 0)}
        ar = arm if arm_r is None else arm_r
        return merge(legs, {"@root": (0, 0, bob * up), "hips": (0, 0, twist * sg), "body": (lean, 0, -twist * sg),
                            "arm.L": (arm * sg, 0, 0), "arm.R": (-ar * sg, 0, 0)},
                     extra(ph, up) if extra else {})
    q = frames // 4
    rig.action("walk", {0: p(0, 0), q: p(0, 1), 2 * q: p(1, 0), 3 * q: p(1, 1), 4 * q: p(0, 0)}, loop=True)


def topple(rig, base=None, n=30, back=False):
    """die: a reel, then down flat on the face (or the back), holding the last frame."""
    base = base or {}
    s = -1 if back else 1
    reel = merge(base, {"body": (-14 * s, 0, 12), "head": (-20 * s, 0, 0), "@root": (0, 0.04 * s, 0),
                        "arm.L": (0, -40, 0), "arm.R": (0, 40, 0)})
    knees = merge(base, {"@root": (0, -0.06 * s, -0.12), "body": (20 * s, 0, 0), "leg.L": (-50, 0, 0),
                         "shin.L": (90, 0, 0), "leg.R": (-40, 0, 0), "shin.R": (80, 0, 0)})
    flat = merge(base, {"root": (84 * s, 0, 0), "@root": (0, -0.04 * s, 0.1), "head": (-10 * s, 0, 15),
                        "arm.L": (-150 * s if not back else 0, -30, 0), "arm.R": (-150 * s if not back else 0, 30, 0),
                        "leg.L": (10, 0, 4), "leg.R": (-6, 0, -4)})
    bump = merge(flat, {"@root": (0, -0.04 * s, 0.13)})
    rig.action("die", {0: base, 5: reel, 12: knees, 20: flat, 24: bump, 27: flat, n: flat})


def grunt():
    reset()
    skin = mat("grunt_skin", (0.42, 0.48, 0.24), 0.65)
    belly = mat("grunt_belly", (0.58, 0.6, 0.36), 0.7)
    hide = mat("grunt_hide", (0.36, 0.22, 0.12), 0.8)
    cloth = mat("grunt_cloth", (0.55, 0.12, 0.08), 0.8)
    iron = mat("grunt_iron", (0.32, 0.31, 0.3), 0.45, metal=0.8)
    tusk = mat("grunt_tusk", (0.92, 0.88, 0.74), 0.4)
    wood = mat("grunt_wood", (0.35, 0.22, 0.12), 0.8)
    eye = mat("grunt_eye_glow", (1.0, 0.55, 0.1), 0.3, emit=4.0)
    mouth = mat("grunt_mouth", (0.15, 0.03, 0.03), 0.6)
    W = 1.25
    rig = Rig(biped_bones(0.95, W, {"hand.R": ((-0.22 * W, -0.04, 0.3), (-0.22 * W, -0.06, 0.22), "fore.R")}))
    # a hunched barrel body, a belly, a hide harness and a red loincloth
    tr = lathe_r([(0.0, 0.66), (0.09, 0.66), (0.17, 0.63), (0.205, 0.57), (0.2, 0.49), (0.18, 0.42), (0.16, 0.37),
                  (0.13, 0.33), (0.0, 0.32)], skin, segs=28, name="trunk", smooth=60)
    for v in tr.data.vertices:
        v.co.y *= 0.82
        if v.co.y > 0:   # a humped back
            v.co.y += 0.05 * smoothstep(0.45, 0.62, v.co.z)
            v.co.z += 0.03 * smoothstep(0.5, 0.63, v.co.z) * (v.co.y / 0.2)
    tr.data.update()
    parts = [tr, ell((0, -0.1, 0.44), (0.13, 0.08, 0.1), belly, segs=18, rings=10)]
    parts.append(torus(0.17, 0.02, (0, 0, 0.37), hide, verts=28, minor=6, scale=(1, 0.82, 1)))
    parts.append(box((0.05, 0.02, 0.05), (0, -0.14, 0.37), iron, bevel=0.008))
    for s in (-1, 1):   # a crossed harness
        st = [Vector(p) for p in ((s * 0.14, -0.12, 0.62), (0, -0.165, 0.5), (-s * 0.14, -0.13, 0.4))]
        parts.append(tube(smooth_path(st, 3), [0.017] * 7, hide, verts=6, caps=True, name="strap"))
    parts.append(cyl(0.035, 0.012, (0, -0.168, 0.5), iron, rot=(math.pi / 2, 0, 0), verts=12))
    rig.custom(w_trunk, parts)
    lc = [prism([(-0.09, 0.0), (0.09, 0.0), (0.07, -0.16), (0.0, -0.18), (-0.07, -0.16)], 0.014, (0, -0.135, 0.37),
                cloth, bevel=0.004),
          prism([(-0.1, 0.0), (0.1, 0.0), (0.08, -0.15), (-0.08, -0.15)], 0.014, (0, 0.13, 0.37), cloth, bevel=0.004)]
    rig.custom(lambda p: {"hips": 1.0}, lc)
    # the head: small, low between the shoulders; a heavy brow, small glaring eyes, a wide jaw with two tusks,
    # pointed ears, a dented iron cap
    HC = Vector((0, -0.07, 0.69))
    head = ell(HC, (0.105, 0.1, 0.095), skin, segs=22, rings=14)
    hp = [head, ell(HC + Vector((0, -0.05, -0.04)), (0.1, 0.07, 0.055), skin, segs=18, rings=10),
          ell(HC + Vector((0, -0.08, 0.035)), (0.09, 0.03, 0.022), skin, segs=14, rings=8),
          ell(HC + Vector((0, -0.11, -0.005)), (0.028, 0.022, 0.022), belly, segs=10, rings=6),
          tube([HC + Vector((-0.05, -0.115, -0.055)), HC + Vector((0, -0.122, -0.06)), HC + Vector((0.05, -0.115, -0.055))],
               [0.006, 0.008, 0.006], mouth, verts=5, caps=True, name="mouth")]
    hp += glow_eyes(HC + Vector((0, -0.093, 0.018)), 0.038, 0.014, eye, slant=-14)
    for s in (-1, 1):
        hp.append(cone(HC + Vector((s * 0.04, -0.105, -0.06)), HC + Vector((s * 0.05, -0.12, 0.0)), 0.014, tusk, verts=8))
        hp.append(cone(HC + Vector((s * 0.09, 0.0, 0.01)), HC + Vector((s * 0.17, 0.03, 0.05)), 0.03, skin, verts=8))
    cap = hemi(0.1, (0, 0, 0), (0, 0, 1), iron, cut=0.15, segs=20, rings=8)
    cap.data.transform(Matrix.Translation(HC + Vector((0, 0.01, 0.0))) @ Matrix.Diagonal((1.05, 1.05, 1.0, 1)))
    hp.append(cap)
    hp.append(cone(HC + Vector((0, 0.0, 0.09)), HC + Vector((0, 0.01, 0.15)), 0.02, iron, verts=8))
    rig.rigid("head", hp)
    # long thick arms, hide bracers, big fists
    for s, side in ((1, "L"), (-1, "R")):
        sh = Vector((s * 0.17 * W, 0, 0.57))
        el = Vector((s * 0.21 * W, 0, 0.43))
        wr = Vector((s * 0.22 * W, -0.04, 0.3))
        rig.rigid("arm." + side, [rod(sh, el, 0.06, skin, r2=0.05, verts=12), sphere(0.07, sh, skin, segs=14, rings=8),
                                  ell(sh + Vector((s * 0.01, 0, 0.03)), (0.08, 0.075, 0.05), hide, segs=12, rings=8)])
        rig.rigid("fore." + side, [rod(el, wr, 0.052, skin, r2=0.045, verts=12),
                                   rod(el + (wr - el) * 0.5, wr, 0.058, hide, verts=12),
                                   sphere(0.055, wr + Vector((0, -0.01, -0.03)), skin, segs=12, rings=8)])
        hip = Vector((s * 0.08 * W, 0, 0.34))
        kn = Vector((s * 0.085 * W, 0, 0.19))
        an = Vector((s * 0.085 * W, 0.005, 0.066))
        rig.rigid("leg." + side, [rod(hip, kn, 0.062, skin, r2=0.055, verts=12)])
        ft = ell((an.x, -0.04, 0.035), (0.06, 0.09, 0.04), hide, segs=12, rings=8)
        for v in ft.data.vertices:
            v.co.z = max(v.co.z, 0.004)
        rig.rigid("shin." + side, [rod(kn, an, 0.05, skin, r2=0.045, verts=12), sphere(0.055, kn, skin, segs=10, rings=6),
                                   ft, torus(0.052, 0.012, an + Vector((0, 0, 0.03)), hide, verts=12, minor=4)])
    # the spiked club in the right fist
    g = Vector((-0.22 * W, -0.05, 0.27))
    d = Vector((0, -0.75, 0.66)).normalized()
    club = [rod(g - d * 0.06, g + d * 0.2, 0.022, wood, r2=0.03, verts=10),
            tube([g + d * 0.18, g + d * 0.3, g + d * 0.42], [0.04, 0.058, 0.05], wood, verts=12, caps=True, name="clubhead")]
    for k in range(9):
        a = k * 2.4
        t = 0.23 + 0.17 * (k / 8)
        side = Vector((math.cos(a), 0, 0)) + d.cross(Vector((1, 0, 0))).normalized() * math.sin(a)
        p0 = g + d * t + side.normalized() * 0.045
        club.append(cone(p0, p0 + side.normalized() * 0.045, 0.012, iron, verts=6))
    rig.rigid("hand.R", club)
    rig.build("grunt")
    walk_cycle(rig, 24, stride=24, bob=0.035, lean=14, twist=9, arm=26, arm_r=12)
    wind = {"arm.R": (-150, 20, 0), "fore.R": (-40, 0, 0), "hand.R": (-15, 0, 0), "body": (-12, 0, 14),
            "head": (-6, 0, 0), "arm.L": (-20, -20, 0), "@root": (0, 0.03, 0.02)}
    smash = {"arm.R": (-60, 0, -10), "fore.R": (-10, 0, 0), "hand.R": (125, 0, 0), "body": (28, 0, -12), "head": (-14, 0, 0),
             "arm.L": (10, -30, 0), "@root": (0, -0.05, -0.04), "leg.L": (-30, 0, 0), "shin.L": (30, 0, 0),
             "leg.R": (20, 0, 0)}
    rig.action("attack", {0: {}, 5: wind, 8: smash, 10: merge(smash, {"body": (3, 0, 0)}), 15: {}})
    topple(rig)
    rig.save("grunt")



def imp():
    reset()
    skin = mat("imp_skin", (0.72, 0.1, 0.05), 0.5, coat=0.2)
    belly = mat("imp_belly", (0.95, 0.45, 0.12), 0.55)
    horn = mat("imp_horn", (0.12, 0.08, 0.06), 0.35, coat=0.5)
    wing_m = mat("imp_wing", (0.3, 0.04, 0.05), 0.6)
    eye = mat("imp_eye_glow", (1.0, 0.9, 0.2), 0.2, emit=6.0)
    mouth = mat("imp_mouth", (0.12, 0.01, 0.02), 0.5)
    tooth = mat("imp_tooth", (1.0, 0.96, 0.85), 0.3)
    fire_m = mat("imp_fire_glow", (1.0, 0.45, 0.08), 0.4, emit=6.0, emit_color=(1.0, 0.35, 0.05))
    core = mat("imp_fire_core_glow", (1.0, 0.92, 0.5), 0.3, emit=12.0)
    rig = Rig(biped_bones(0.78, 0.95, {"tail": ((0, 0.08, 0.3), (0, 0.22, 0.25), "hips"),
                                       "wing.L": ((0.06, 0.08, 0.48), (0.2, 0.14, 0.58), "body"),
                                       "wing.R": ((-0.06, 0.08, 0.48), (-0.2, 0.14, 0.58), "body")}))
    tr = lathe_r([(0.0, 0.52), (0.07, 0.515), (0.12, 0.49), (0.135, 0.44), (0.12, 0.38), (0.1, 0.33), (0.09, 0.29),
                  (0.0, 0.27)], skin, segs=24, name="trunk", smooth=60)
    for v in tr.data.vertices:
        v.co.y *= 0.85
    tr.data.update()
    rig.custom(w_trunk, [tr, ell((0, -0.08, 0.38), (0.08, 0.04, 0.09), belly, segs=14, rings=8)])
    # a big head: a wide grin, slanted glowing eyes, long swept horns and pointed ears
    HC = Vector((0, -0.02, 0.62))
    hp = [ell(HC, (0.12, 0.11, 0.105), skin, segs=24, rings=14),
          ell(HC + Vector((0, -0.07, -0.04)), (0.08, 0.06, 0.05), skin, segs=16, rings=10)]
    hp += glow_eyes(HC + Vector((0, -0.095, 0.02)), 0.045, 0.024, eye, slant=-22)
    for s in (-1, 1):
        hp.append(ell(HC + Vector((s * 0.045, -0.1, 0.045)), (0.035, 0.012, 0.01), skin, roll=-s * 25, segs=8, rings=4))
        hp.append(tube([HC + Vector((s * 0.06, -0.02, 0.08)), HC + Vector((s * 0.11, 0.02, 0.15)),
                        HC + Vector((s * 0.14, 0.09, 0.19)), HC + Vector((s * 0.15, 0.16, 0.17))],
                       [0.03, 0.022, 0.012, 0.002], horn, verts=10, caps=True, name="horn"))
        hp.append(cone(HC + Vector((s * 0.1, 0.0, 0.0)), HC + Vector((s * 0.2, 0.04, 0.03)), 0.035, skin, verts=8))
    grin = []
    for k in range(11):
        a = math.pi * (1.08 + 0.84 * k / 10)
        grin.append(HC + Vector((0.075 * math.cos(a), -0.115 + 0.02 * (1 - abs(math.cos(a))), -0.03 + 0.03 * math.sin(a))))
    hp.append(tube(grin, [0.008] + [0.013] * 9 + [0.008], mouth, verts=6, caps=True, name="grin"))
    for k in range(4):
        x = -0.045 + 0.03 * k
        hp.append(cone(HC + Vector((x, -0.122, -0.04)), HC + Vector((x, -0.125, -0.06)), 0.007, tooth, verts=5))
    rig.rigid("head", hp)
    # arms and clawed hands; the right one cups a ball of fire
    for s, side in ((1, "L"), (-1, "R")):
        sh, el = Vector((s * 0.15, 0, 0.47)), Vector((s * 0.19, 0, 0.36))
        wr = Vector((s * 0.2, -0.03, 0.26))
        rig.rigid("arm." + side, [rod(sh, el, 0.03, skin, r2=0.026, verts=10), sphere(0.035, sh, skin, segs=10, rings=6)])
        hand = [rod(el, wr, 0.025, skin, r2=0.022, verts=10), sphere(0.03, wr, skin, segs=10, rings=6)]
        for k in range(3):
            hand.append(cone(wr + Vector((s * 0.01 * (k - 1), -0.02, -0.01)),
                             wr + Vector((s * 0.015 * (k - 1), -0.05, -0.04)), 0.008, horn, verts=5))
        rig.rigid("fore." + side, hand)
        hip, kn = Vector((s * 0.075, 0, 0.28)), Vector((s * 0.085, -0.04, 0.16))
        an = Vector((s * 0.08, 0.03, 0.06))
        rig.rigid("leg." + side, [rod(hip, kn, 0.04, skin, r2=0.033, verts=10)])
        rig.rigid("shin." + side, [rod(kn, an, 0.028, skin, r2=0.022, verts=10), sphere(0.033, kn, skin, segs=8, rings=6),
                                   ell((an.x, -0.01, 0.025), (0.035, 0.06, 0.025), horn, segs=10, rings=6)])
        # bat wings
        poly = [(0.0, 0.0), (0.12, 0.08), (0.24, 0.13), (0.3, 0.1), (0.25, 0.04), (0.2, 0.05), (0.16, -0.02),
                (0.1, 0.0), (0.06, -0.06)]
        if s < 0:
            poly = [(-x, z) for x, z in poly][::-1]
        w = prism(poly, 0.006, (s * 0.05, 0.1, 0.47), wing_m, bevel=0.002)
        w.data.transform(Matrix.Translation((s * 0.05, 0.1, 0.47)) @ Matrix.Rotation(math.radians(-25), 4, "X")
                         @ Matrix.Translation((-s * 0.05, -0.1, -0.47)))
        rig.rigid("wing." + side, w)
    tl = [tube([(0, 0.07, 0.3), (0, 0.16, 0.24), (0, 0.24, 0.27), (0, 0.27, 0.34)], [0.022, 0.016, 0.01, 0.007], skin,
               verts=8, caps=True, name="tail"),
          prism([(-0.035, 0.0), (0.035, 0.0), (0.0, 0.06)], 0.01, (0, 0.272, 0.33), horn, bevel=0.003)]
    rig.rigid("tail", tl)
    fc = Vector((-0.2, -0.08, 0.22))
    ball = [sphere(0.045, fc, core, segs=12, rings=8)] + fire(fc + Vector((0, 0, -0.03)), 0.08, fire_m, core, 4)
    rig.rigid("fore.R", ball)
    rig.build("imp")
    rig.pin("muzzle", fc, "fore.R")
    walk_cycle(rig, 15, stride=30, bob=0.05, lean=12, twist=8, arm=20, arm_r=10,
               extra=lambda ph, up: {"tail": (0, 0, 25 * (1 if ph == 0 else -1)), "wing.L": (0, -15 * up, 0),
                                     "wing.R": (0, 15 * up, 0)})
    wind = {"arm.R": (60, 30, 0), "fore.R": (-60, 0, 0), "body": (-12, 0, 24), "head": (-8, 0, -10), "tail": (0, 0, -30),
            "arm.L": (-50, -20, 0), "wing.L": (0, -30, 0), "wing.R": (0, 30, 0)}
    fling = {"arm.R": (-110, 0, -10), "fore.R": (-10, 0, 0), "body": (18, 0, -20), "head": (-6, 0, 10),
             "arm.L": (20, -20, 0), "@root": (0, -0.03, 0.02), "leg.L": (-20, 0, 0), "leg.R": (16, 0, 0)}
    rig.action("attack", {0: {}, 4: wind, 7: fling, 11: {}})
    rig.action("die", {0: {}, 4: {"body": (-20, 0, 0), "head": (-25, 0, 0), "arm.L": (0, -90, 0), "arm.R": (0, 90, 0),
                                  "@root": (0, 0, 0.08), "%root": (1.1, 1.1, 1.1)},
                       10: {"root": (0, 0, 200), "@root": (0, 0, 0.12), "%root": (1.0, 1.0, 1.0), "body": (-10, 0, 0),
                            "arm.L": (0, -100, 0), "arm.R": (0, 100, 0), "wing.L": (0, -40, 0), "wing.R": (0, 40, 0)},
                       16: {"root": (0, 0, 400), "@root": (0, 0, 0.05), "%root": (0.6, 0.6, 0.6)},
                       22: {"root": (0, 0, 520), "@root": (0, 0, 0.0), "%root": (0.01, 0.01, 0.01)}})
    rig.save("imp")


def sorcerer():
    reset()
    robe = mat("sorcerer_robe", (0.2, 0.06, 0.3), 0.7)
    trim = mat("sorcerer_trim", (0.6, 0.45, 0.15), 0.35, metal=0.8)
    dark = mat("sorcerer_hood_dark", (0.0, 0.0, 0.0), 1.0)
    hand = mat("sorcerer_skin", (0.55, 0.6, 0.58), 0.6)
    eye = mat("sorcerer_eye_glow", (0.85, 0.4, 1.0), 0.2, emit=8.0)
    rune = mat("sorcerer_rune_glow", (0.7, 0.35, 1.0), 0.3, emit=5.0, emit_color=(0.6, 0.25, 1.0))
    wood = mat("sorcerer_wood", (0.12, 0.08, 0.07), 0.7)
    rig = Rig(biped_bones(1.0, 1.0, {"skirt.F": ((0, -0.08, 0.44), (0, -0.12, 0.2), "hips"),
                                     "skirt.B": ((0, 0.08, 0.44), (0, 0.12, 0.2), "hips")}))
    ro = lathe_r([(0.0, 0.67), (0.06, 0.66), (0.12, 0.64), (0.15, 0.6), (0.145, 0.53), (0.13, 0.46), (0.135, 0.38),
                  (0.16, 0.26), (0.19, 0.12), (0.21, 0.02), (0.0, 0.03)], robe, segs=36, name="robe", smooth=60)
    for v in ro.data.vertices:
        v.co.y *= 0.8
        if v.co.z < 0.05:
            a = math.atan2(v.co.y, v.co.x)
            v.co.z += 0.03 * (1 if int((a + math.pi) / (2 * math.pi) * 14) % 2 else 0)
    ro.data.update()
    sk = w_skirt(0.44, 0.02)
    rig.custom(lambda p: w_trunk(p) if p.z > 0.44 else sk(p), ro)
    belt = [torus(0.132, 0.014, (0, 0, 0.45), trim, verts=28, minor=5, scale=(1, 0.8, 1))]
    for k in range(5):   # glowing runes down the front
        z = 0.38 - 0.07 * k
        r = 0.135 + (0.21 - 0.135) * (0.44 - z) / 0.42
        belt.append(prism([(-0.018, 0.0), (0.0, 0.025), (0.018, 0.0), (0.0, -0.025)], 0.005,
                          (0, -r * 0.8 - 0.004, z), rune, bevel=0.0))
    rig.custom(sk, belt[1:])
    rig.custom(w_trunk, belt[:1])
    mant = hemi(0.18, (0, 0, 0), (0, 0, 1), robe, cut=0.25, segs=30, rings=10)
    mant.data.transform(Matrix.Translation((0, 0.0, 0.52)) @ Matrix.Diagonal((1.0, 0.86, 0.8, 1)))
    solid(mant, 0.01)
    K.finish(mant, robe, smooth=50)
    rig.custom(lambda p: {"body": 1.0}, mant, torus(0.16, 0.008, (0, 0, 0.56), trim, verts=30, minor=4,
                                                    scale=(1, 0.86, 1)))
    # the deep, pointed hood: darkness inside, two violet eyes
    hood = lathe_r([(0.0, 0.98), (0.03, 0.95), (0.08, 0.88), (0.115, 0.8), (0.125, 0.72), (0.115, 0.66),
                    (0.1, 0.64)], robe, segs=30, name="hood", smooth=60)
    for v in hood.data.vertices:   # pull the point back
        v.co.y += 0.08 * smoothstep(0.85, 0.98, v.co.z)
    hood.data.update()
    solid(hood, 0.012)

    def open_face(bm):
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < -0.05
                                   and 0.66 < f.calc_center_median().z < 0.86
                                   and abs(f.calc_center_median().x) < 0.08], context="FACES")
    from prism_models import edit
    edit(hood, open_face)
    K.finish(hood, robe, smooth=60)
    hp = [hood, ell((0, -0.01, 0.76), (0.1, 0.1, 0.1), dark, segs=16, rings=10),
          torus(0.085, 0.008, (0, -0.075, 0.77), trim, rot=(math.radians(80), 0, 0), verts=24, minor=4,
                scale=(0.95, 1.2, 1))]
    hp += glow_eyes((0, -0.1, 0.77), 0.03, 0.016, eye, slant=-10, squash=0.45)
    rig.rigid("head", hp)
    for s, side in ((1, "L"), (-1, "R")):
        sh, el = Vector((s * 0.16, 0, 0.6)), Vector((s * 0.2, 0, 0.45))
        wr = Vector((s * 0.21, -0.04, 0.32))
        rig.rigid("arm." + side, [rod(sh, el, 0.045, robe, r2=0.05, verts=12), sphere(0.05, sh, robe, segs=12, rings=8)])
        fo = [rod(el, wr, 0.05, robe, r2=0.07, verts=14), torus(0.068, 0.008, wr, trim, verts=14, minor=4),
              sphere(0.026, wr + Vector((0, -0.02, -0.02)), hand, segs=10, rings=6)]
        for k in range(4):
            fo.append(rod(wr + Vector((s * 0.012 * (k - 1.5), -0.03, -0.03)),
                          wr + Vector((s * 0.016 * (k - 1.5), -0.07, -0.06)), 0.006, hand, r2=0.003, verts=5))
        rig.rigid("fore." + side, fo)
    # a crooked wand topped by a violet crystal, in the right hand
    g = Vector((-0.21, -0.07, 0.29))
    wand = [tube([g + Vector((0, 0.03, -0.12)), g, g + Vector((0.01, -0.03, 0.12)), g + Vector((-0.005, -0.05, 0.25))],
                 [0.012, 0.014, 0.012, 0.01], wood, verts=8, caps=True, name="wand")]
    tip = g + Vector((-0.005, -0.06, 0.3))
    wand.append(lathe_r([(0.0, 0.05), (0.022, 0.0), (0.0, -0.035)], rune, segs=6, name="crystal", smooth=0,
                        center=(0, 0, 0)))
    wand[-1].data.transform(Matrix.Translation(tip))
    rig.rigid("fore.R", wand)
    rig.build("sorcerer")
    rig.pin("muzzle", tip, "fore.R")

    def glide(k, extra=None):
        a = 2 * math.pi * k
        return merge({"@root": (0, 0, 0.012 * math.sin(2 * a)), "body": (8, 0, 3 * math.sin(a)), "head": (-4, 0, 0),
                      "skirt.F": (-10 - 6 * math.sin(a), 0, 0), "skirt.B": (14 + 6 * math.sin(a), 0, 0),
                      "leg.L": (-20 * math.sin(a), 0, 0), "leg.R": (20 * math.sin(a), 0, 0),
                      "arm.L": (-20, -10, 0), "fore.L": (-40, 0, 0), "arm.R": (-30, 10, 0), "fore.R": (-50, 0, 0)},
                     extra or {})
    rig.action("walk", {f: glide(f / 24) for f in (0, 6, 12, 18, 24)}, loop=True)
    raise_ = merge(glide(0), {"arm.R": (-150, 20, 0), "fore.R": (-20, 0, 0), "arm.L": (-120, -30, 0),
                              "body": (-12, 0, 0), "head": (-14, 0, 0), "%body": (1.04, 1.04, 1.06)})
    cast = merge(glide(0), {"arm.R": (-90, 0, -10), "fore.R": (-10, 0, 0), "arm.L": (-80, 0, 10), "fore.L": (-10, 0, 0),
                            "body": (20, 0, 0), "@root": (0, -0.04, 0)})
    rig.action("attack", {0: glide(0), 6: raise_, 9: cast, 12: cast, 18: glide(0)})
    rig.action("die", {0: glide(0), 5: merge(glide(0), {"body": (-20, 0, 0), "head": (-30, 0, 0), "arm.L": (0, -80, 0),
                                                         "arm.R": (0, 80, 0)}),
                       14: {"%root": (1.2, 1.2, 0.5), "@root": (0, 0, -0.02), "head": (30, 0, 0), "skirt.F": (-40, 0, 0),
                            "skirt.B": (40, 0, 0)},
                       24: {"%root": (1.4, 1.4, 0.08), "skirt.F": (-70, 0, 0), "skirt.B": (70, 0, 0)},
                       30: {"%root": (1.4, 1.4, 0.06), "skirt.F": (-70, 0, 0), "skirt.B": (70, 0, 0)}})
    # fade / appear: the hint for blinking out: a twist that thins him to a thread, gone at the end (and back)
    fk = {0: glide(0), 4: merge(glide(0), {"root": (0, 0, 90), "%root": (0.7, 0.7, 1.1)}),
          8: {"root": (0, 0, 220), "%root": (0.25, 0.25, 1.3), "@root": (0, 0, 0.05)},
          12: {"root": (0, 0, 360), "%root": (0.01, 0.01, 1.5), "@root": (0, 0, 0.1)}}
    rig.action("fade", fk)
    rig.action("appear", {12 - f: p for f, p in fk.items()})
    rig.save("sorcerer")


def skeleton():
    reset()
    bone_m = mat("skeleton_bone", (0.88, 0.84, 0.72), 0.55)
    dark = mat("skeleton_dark", (0.03, 0.02, 0.02), 0.8)
    eye = mat("skeleton_eye_glow", (1.0, 0.25, 0.12), 0.2, emit=8.0)
    rust = mat("skeleton_rust", (0.38, 0.33, 0.29), 0.55, metal=0.8)
    rag = mat("skeleton_rag", (0.3, 0.27, 0.22), 0.9)
    wood = mat("skeleton_wood", (0.3, 0.2, 0.12), 0.7)
    string = mat("skeleton_string", (0.8, 0.78, 0.7), 0.6)
    rig = hero_rig({"bow": ((0.207, -0.045, 0.31), (0.207, -0.045, 0.45), "fore.L"),
                    "nock": ((0.207, 0.02, 0.31), (0.207, 0.06, 0.31), "bow")})
    # spine, ribs, pelvis
    parts = [rod((0, 0.03, 0.36), (0, 0.04, 0.64), 0.016, bone_m, verts=8)]
    for k in range(5):
        z = 0.47 + 0.035 * k
        w = 0.085 + 0.025 * math.sin(math.pi * (k + 1) / 6)
        rib = [Vector((w * math.cos(a), 0.03 - 0.075 * math.sin(a) * (0.8 + 0.2 * math.sin(math.pi * (k + 1) / 6)),
                       z - 0.02 * math.sin(a))) for a in (math.radians(x) for x in range(-30, 211, 15))]
        parts.append(tube(rib, [0.009] * len(rib), bone_m, verts=6, caps=True, name="rib"))
    parts.append(rod((0, -0.07, 0.6), (0, -0.075, 0.48), 0.012, bone_m, verts=6))   # sternum
    parts.append(rod((-0.15, 0.02, 0.62), (0.15, 0.02, 0.62), 0.014, bone_m, verts=8))   # collarbones
    rig.custom(w_trunk, parts)
    pel = [ell((0, 0.01, 0.37), (0.1, 0.06, 0.05), bone_m, segs=14, rings=8),
           torus(0.11, 0.012, (0, 0.0, 0.42), rag, verts=24, minor=4, scale=(1, 0.8, 1))]
    rig.custom(lambda p: {"hips": 1.0}, pel)
    rg = skirt_mesh(rag, 0.42, 0.24, 0.115, 0.15, slit=0.06, name="rag")
    for v in rg.data.vertices:
        if v.co.z < 0.27:
            v.co.z += 0.03 * math.sin(math.atan2(v.co.y, v.co.x) * 7)
    rg.data.update()
    rig.custom(w_skirt(0.42, 0.24), rg)
    # the skull: dark sockets with red pin-points, a gaping jaw, a dented rusty kettle helm
    HC = Vector((0, -0.005, 0.76))
    hp = [ell(HC, (0.085, 0.095, 0.09), bone_m, segs=20, rings=12),
          ell(HC + Vector((0, -0.04, -0.07)), (0.06, 0.05, 0.03), bone_m, segs=14, rings=8)]
    for s in (-1, 1):
        hp.append(ell(HC + Vector((s * 0.032, -0.075, 0.0)), (0.025, 0.02, 0.026), dark, segs=10, rings=6))
        hp.append(sphere(0.008, HC + Vector((s * 0.032, -0.093, 0.0)), eye, segs=6, rings=4))
    hp.append(cone(HC + Vector((0, -0.09, -0.03)), HC + Vector((0, -0.088, -0.005)), 0.01, dark, verts=3))
    for k in range(6):
        hp.append(box((0.009, 0.006, 0.012), HC + Vector((-0.027 + 0.011 * k, -0.088, -0.055)), bone_m, bevel=0.002))
    helm = lathe_r([(0.0, 0.875), (0.06, 0.87), (0.095, 0.84), (0.1, 0.8), (0.135, 0.78), (0.138, 0.77),
                    (0.1, 0.787), (0.0, 0.79)], rust, segs=24, name="kettle", smooth=40)
    helm.data.transform(Matrix.Translation((0, 0, 0.8)) @ Matrix.Rotation(math.radians(-10), 4, "Y")
                        @ Matrix.Translation((0, 0, -0.8)))
    hp.append(helm)
    rig.rigid("head", hp)
    for s, side in ((1, "L"), (-1, "R")):
        sh, el = Vector(HERO_BONES["arm." + side][0]), Vector(HERO_BONES["arm." + side][1])
        wr = Vector(HERO_BONES["fore." + side][1])
        rig.rigid("arm." + side, [rod(sh, el, 0.014, bone_m, verts=8), sphere(0.025, sh, bone_m, segs=10, rings=6)])
        rig.rigid("fore." + side, [rod(el, wr, 0.012, bone_m, verts=8), rod(el + Vector((s * 0.01, 0, 0)), wr, 0.008,
                                                                             bone_m, verts=6),
                                   sphere(0.02, el, bone_m, segs=8, rings=6)])
        h = HAND[s]
        hd = [ell(h, (0.02, 0.025, 0.022), bone_m, segs=8, rings=6)]
        for k in range(4):
            hd.append(rod(h + Vector((s * 0.006 * (k - 1.5), -0.015, -0.005)),
                          h + Vector((-s * 0.008, -0.03, 0.01 * (k - 1.5))), 0.005, bone_m, verts=4))
        rig.rigid("bow" if s > 0 else "hand.R", hd)
        hp_, kn = Vector(HERO_BONES["leg." + side][0]), Vector(HERO_BONES["leg." + side][1])
        an = Vector(HERO_BONES["shin." + side][1])
        rig.rigid("leg." + side, [rod(hp_, kn, 0.016, bone_m, verts=8)])
        rig.rigid("shin." + side, [rod(kn, an, 0.014, bone_m, verts=8), sphere(0.024, kn, bone_m, segs=8, rings=6)])
        ft = [ell((an.x, -0.03, 0.02), (0.025, 0.06, 0.018), bone_m, segs=10, rings=6)]
        rig.rigid("foot." + side, ft)
    # a rough bow in the bony left hand
    g0 = HAND[1]
    L = 0.31
    up_, dn_ = [], []
    for k in range(7):
        u = k / 6
        y = -0.05 * math.sin(math.pi * u)
        up_.append(g0 + Vector((0, y, L * u)))
        dn_.append(g0 + Vector((0, y, -L * u)))
    rig.rigid("bow", [tube(up_, [0.012 - 0.006 * k / 6 for k in range(7)], wood, verts=6, caps=True),
                      tube(dn_, [0.012 - 0.006 * k / 6 for k in range(7)], wood, verts=6, caps=True)])
    nockp = Vector((0.207, 0.02, 0.31))
    s_pts = [up_[-1] + (nockp - up_[-1]) * (k / 6) for k in range(7)] + \
            [nockp + (dn_[-1] - nockp) * (k / 6) for k in range(1, 7)]
    rig.custom(lambda p: {"bow": 1 - (1 - min(1.0, abs(p.z - nockp.z) / L)) ** 2 + 1e-4,
                          "nock": (1 - min(1.0, abs(p.z - nockp.z) / L)) ** 2 + 1e-4},
               tube(s_pts, [0.003] * len(s_pts), string, verts=4, caps=False, name="string"))
    rig.build("skeleton")
    rig.pin("muzzle", g0 + Vector((0, -0.07, 0)), "bow")
    base = {"arm.L": (-8, -6, 0), "fore.L": (-46, 0, 0), "bow": (26, 0, 0), "arm.R": (0, 8, 0), "fore.R": (-16, 0, 0)}
    jitter = lambda ph, up: merge(base, {"head": (6 * up, 0, 10 * (1 if ph == 0 else -1)), "foot.L": (0, 0, 0)})
    walk_cycle(rig, 20, stride=26, bob=0.02, lean=6, twist=10, arm=14, arm_r=22, extra=jitter)
    wind = merge(base, {"arm.L": (-82, -4, 0), "fore.L": (-4, 0, 0), "bow": (86, 0, 0), "arm.R": (-10, 80, 20),
                        "fore.R": (-128, 0, 0), "body": (4, 0, -18), "head": (0, 0, 14), "@nock": (-0.1, 0.2, 0.05)})
    wind["arm.L"], wind["fore.L"], wind["bow"], wind["arm.R"], wind["fore.R"] = (-82, -4, 0), (-4, 0, 0), (86, 0, 0), \
        (-10, 80, 20), (-128, 0, 0)
    shot = dict(wind)
    shot.update({"@nock": (0, 0, 0), "fore.R": (-68, 0, 0), "arm.R": (0, 10, -10)})
    rig.action("attack", {0: base, 7: wind, 10: wind, 12: shot, 18: base})
    # die: the bones give way: the knees fold, the skull drops and rolls off, the rest collapses into a heap
    fold = merge(base, {"@root": (0, 0, -0.16), "leg.L": (-70, 0, 10), "shin.L": (120, 0, 0), "leg.R": (-60, 0, -10),
                        "shin.R": (110, 0, 0), "body": (25, 0, 0), "arm.L": (0, -30, 0), "arm.R": (0, 30, 0)})
    heap = {"@root": (0, 0, -0.2), "leg.L": (-88, 0, 30), "shin.L": (160, 0, 0),
            "leg.R": (-88, 0, -30), "shin.R": (160, 0, 0), "body": (62, 0, 20), "arm.L": (-20, -80, 0),
            "arm.R": (-10, 80, 0), "fore.L": (-40, 0, 0), "head": (60, 40, 0), "@head": (0.12, -0.15, -0.3),
            "bow": (90, 0, 0)}
    rig.action("die", {0: base, 6: fold, 14: heap, 18: merge(heap, {"@head": (0.18, -0.2, -0.22)}),
                       24: merge(heap, {"@head": (0.22, -0.22, -0.26)}), 30: merge(heap, {"@head": (0.22, -0.22, -0.26)})})
    rig.save("skeleton")


def deathshade():
    reset()
    robe = mat("deathshade_robe", (0.035, 0.03, 0.05), 0.85)
    hem = mat("deathshade_hem_glow", (0.45, 0.15, 0.85), 0.4, emit=3.0, emit_color=(0.45, 0.1, 0.95))
    bone_m = mat("deathshade_bone", (0.7, 0.7, 0.66), 0.5)
    dark = mat("deathshade_dark", (0.0, 0.0, 0.0), 1.0)
    eye = mat("deathshade_eye_glow", (0.5, 1.0, 0.45), 0.2, emit=10.0)
    iron = mat("deathshade_iron", (0.2, 0.2, 0.22), 0.4, metal=0.9)
    mist = mat("deathshade_mist_glow", (0.4, 0.15, 0.7), 0.4, emit=1.5, alpha=0.45, emit_color=(0.35, 0.1, 0.8))
    rig = Rig({"root": ((0, 0, 0), (0, 0, 0.06), None),
               "body": ((0, 0, 0.3), (0, 0, 0.75), "root"),
               "head": ((0, 0, 0.75), (0, -0.02, 1.05), "body"),
               "arm.L": ((0.17, 0, 0.72), (0.25, -0.06, 0.55), "body"),
               "arm.R": ((-0.17, 0, 0.72), (-0.25, -0.06, 0.55), "body"),
               "fore.L": ((0.25, -0.06, 0.55), (0.3, -0.24, 0.48), "arm.L"),
               "fore.R": ((-0.25, -0.06, 0.55), (-0.3, -0.24, 0.48), "arm.R"),
               "tail": ((0, 0.05, 0.3), (0, 0.18, 0.14), "body"),
               "tail2": ((0, 0.18, 0.14), (0, 0.32, 0.06), "tail")})
    # a tall tattered robe hovering above the floor, its hem burning with a violet glow
    ro = lathe_r([(0.0, 0.8), (0.08, 0.79), (0.16, 0.76), (0.19, 0.7), (0.18, 0.6), (0.17, 0.48), (0.19, 0.34),
                  (0.22, 0.2), (0.24, 0.1)], robe, segs=40, name="robe", smooth=60)
    for v in ro.data.vertices:
        v.co.y *= 0.82
        if v.co.z < 0.12:   # ragged tatters
            a = math.atan2(v.co.y, v.co.x)
            v.co.z += 0.06 * abs(math.sin(a * 7)) - 0.03 + 0.02 * math.sin(a * 13)
    ro.data.update()
    solid(ro, 0.01)
    K.finish(ro, robe, smooth=60)
    hem_pts = []
    for k in range(81):
        a = 2 * math.pi * k / 80
        hem_pts.append(Vector((0.243 * math.cos(a), 0.243 * 0.82 * math.sin(a),
                               0.1 + 0.06 * abs(math.sin(a * 7)) - 0.03 + 0.02 * math.sin(a * 13))))
    hm = tube(hem_pts, [0.008] * 81, hem, verts=5, caps=False, name="hem")
    mist_o = lathe_r([(0.2, 0.12), (0.26, 0.04), (0.2, -0.02), (0.0, -0.01)], mist, segs=24, name="mist")

    def w_robe(p):
        a = smoothstep(0.35, 0.18, p.z)
        b = smoothstep(0.16, 0.05, p.z)
        k = smoothstep(-0.05, 0.12, p.y)
        return {"body": 1 - a * k + 1e-4, "tail": a * k * (1 - b) + 1e-4, "tail2": a * k * b + 1e-4}
    rig.custom(w_robe, ro, hm)
    bpy.data.objects.remove(mist_o)
    # a tall hood over a pale skull with green burning eyes, an iron crown of spikes
    hood = lathe_r([(0.0, 1.06), (0.05, 1.04), (0.1, 0.98), (0.13, 0.9), (0.135, 0.8), (0.12, 0.75)], robe, segs=30,
                   name="hood", smooth=60)
    for v in hood.data.vertices:
        v.co.y += 0.06 * smoothstep(0.95, 1.06, v.co.z)
    hood.data.update()
    solid(hood, 0.012)

    def open_face(bm):
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < -0.05
                                   and 0.76 < f.calc_center_median().z < 0.97
                                   and abs(f.calc_center_median().x) < 0.085], context="FACES")
    from prism_models import edit
    edit(hood, open_face)
    K.finish(hood, robe, smooth=60)
    HC = Vector((0, -0.02, 0.87))
    hp = [hood, ell(HC + Vector((0, 0.03, 0)), (0.11, 0.1, 0.11), dark, segs=14, rings=8),
          ell(HC, (0.07, 0.075, 0.08), bone_m, segs=18, rings=10),
          ell(HC + Vector((0, -0.03, -0.065)), (0.05, 0.045, 0.025), bone_m, segs=12, rings=6)]
    for s in (-1, 1):
        hp.append(ell(HC + Vector((s * 0.027, -0.06, 0.008)), (0.022, 0.018, 0.024), dark, segs=10, rings=6))
        hp.append(ell(HC + Vector((s * 0.027, -0.075, 0.008)), (0.012, 0.006, 0.016), eye, segs=8, rings=6))
    hp.append(torus(0.125, 0.012, (0, 0.0, 0.97), iron, verts=24, minor=5))
    for k in range(9):
        a = 2 * math.pi * k / 9
        b = Vector((0.125 * math.cos(a), 0.125 * math.sin(a), 0.97))
        hp.append(cone(b, b + Vector((0.02 * math.cos(a), 0.02 * math.sin(a), 0.09 + 0.03 * (k % 2))), 0.014, iron,
                       verts=6))
    rig.rigid("head", hp)
    # long sleeves and skeletal claws reaching out
    for s, side in ((1, "L"), (-1, "R")):
        sh, el = Vector((s * 0.17, 0, 0.72)), Vector((s * 0.25, -0.06, 0.55))
        wr = Vector((s * 0.3, -0.24, 0.48))
        rig.rigid("arm." + side, [rod(sh, el, 0.05, robe, r2=0.055, verts=12), sphere(0.06, sh, robe, segs=12, rings=8)])
        fo = [rod(el, el + (wr - el) * 0.55, 0.055, robe, r2=0.085, verts=14),
              rod(el + (wr - el) * 0.5, wr, 0.013, bone_m, verts=6),
              ell(wr, (0.025, 0.03, 0.02), bone_m, segs=8, rings=6)]
        d = (wr - el).normalized()
        for k in range(4):
            off = Vector((s * 0.02 * (k - 1.5), 0, 0.01 * (k - 1.5)))
            a = wr + off * 0.6
            b = wr + d * 0.07 + off * 1.4
            c = b + d * 0.04 + Vector((0, 0, -0.035))
            fo.append(tube([a, b, c], [0.007, 0.006, 0.002], bone_m, verts=5, caps=True, name="claw"))
        rig.rigid("fore." + side, fo)
    rig.build("deathshade")

    def drift(k, extra=None):
        a = 2 * math.pi * k
        return merge({"@root": (0, 0, 0.07 + 0.04 * math.sin(a)), "body": (8, 0, 3 * math.sin(a)),
                      "head": (-6, 0, -5 * math.sin(a)), "tail": (16 + 10 * math.sin(a + 1), 0, 10 * math.sin(a)),
                      "tail2": (16 + 12 * math.sin(a + 2), 0, 14 * math.sin(a + 1)),
                      "arm.L": (-12 - 8 * math.sin(a), -6, 0), "arm.R": (-12 + 8 * math.sin(a), 6, 0),
                      "fore.L": (-10, 0, 0), "fore.R": (-10, 0, 0)}, extra or {})
    rig.action("walk", {f: drift(f / 40) for f in (0, 10, 20, 30, 40)}, loop=True)
    reach = drift(0, {"body": (22, 0, 0), "head": (6, 0, 0), "@root": (0, -0.12, 0.05), "arm.L": (-60, 10, -20),
                      "arm.R": (-60, -10, 20), "fore.L": (-10, 0, 0), "fore.R": (-10, 0, 0), "%head": (1.08, 1.08, 1.08)})
    rig.action("attack", {0: drift(0), 6: drift(0, {"body": (-14, 0, 0), "arm.L": (-90, -40, 0), "arm.R": (-90, 40, 0),
                                                   "fore.L": (-30, 0, 0), "fore.R": (-30, 0, 0)}),
                          10: reach, 13: merge(reach, {"fore.L": (-25, 0, 0), "fore.R": (-25, 0, 0)}), 18: drift(0)})
    rig.action("die", {0: drift(0), 5: drift(0, {"body": (-25, 0, 0), "head": (-30, 0, 0), "arm.L": (-20, -90, 0),
                                                 "arm.R": (-20, 90, 0)}),
                       16: {"%root": (1.2, 1.2, 0.5), "@root": (0, 0, -0.05), "head": (40, 0, 0), "arm.L": (0, -60, 0),
                            "arm.R": (0, 60, 0)},
                       28: {"%root": (1.5, 1.5, 0.06), "@root": (0, 0, -0.04)},
                       36: {"%root": (1.5, 1.5, 0.04), "@root": (0, 0, -0.04)}})
    rig.save("deathshade")



# ------------------------------------------------------------------ projectiles (built along -Y = Godot +Z)

def trail(length, r0, material, name="trail", z=0.0, y0=0.06):
    """A tapering ghost ribbon streaming back (+Y) behind a projectile."""
    pts = [Vector((0, y0 + length * u, z)) for u in (0, 0.25, 0.5, 0.75, 1.0)]
    return tube(pts, [r0, r0 * 0.85, r0 * 0.6, r0 * 0.3, r0 * 0.05], material, verts=12, caps=True, name=name)


def throw_axe():
    reset()
    steel = mat("throw_axe_steel", (0.7, 0.72, 0.76), 0.28, metal=0.9)
    wood = mat("throw_axe_wood", (0.36, 0.21, 0.1), 0.7)
    edge = mat("throw_axe_glow", (1.0, 0.5, 0.25), 0.3, emit=4.0, emit_color=(1.0, 0.35, 0.15))
    tr_m = mat("throw_axe_trail_glow", (1.0, 0.45, 0.2), 0.4, emit=2.0, alpha=0.35, emit_color=(1.0, 0.3, 0.1))
    # a short double-bitted axe lying in the YZ plane (it tumbles end over end about X), 0.46 from bit to bit
    parts = [rod((0, 0, -0.17), (0, 0, 0.17), 0.016, wood, verts=8), sphere(0.022, (0, 0, -0.17), steel, segs=8, rings=6),
             rod((0, 0, 0.12), (0, 0, 0.2), 0.026, steel, verts=10)]
    for sgn in (-1, 1):
        poly = [(0.0, -0.035), (0.09, -0.07), (0.15, -0.09), (0.17, 0.0), (0.15, 0.09), (0.09, 0.07), (0.0, 0.035)]
        bm = bmesh.new()
        f = [bm.verts.new((-0.008, sgn * x, 0.16 + z)) for x, z in poly]
        b = [bm.verts.new((0.008, sgn * x, 0.16 + z)) for x, z in poly]
        bm.faces.new(f)
        bm.faces.new(b[::-1])
        for i in range(len(poly) - 1):
            bm.faces.new((f[i], b[i], b[i + 1], f[i + 1]))
        bm.faces.new((f[-1], b[-1], b[0], f[0]))
        parts.append(new_obj("bit", bm, steel, smooth=20))
        arc = [Vector((0, sgn * (0.16 + 0.012 * math.cos(a)), 0.16 + 0.09 * math.sin(a))) for a in
               (math.radians(x) for x in range(-80, 81, 20))]
        parts.append(tube(arc, [0.007] * len(arc), edge, verts=5, caps=True, name="edge"))
    for o in parts:
        o.data.transform(Matrix.Translation((0, 0, -0.03)))
    axe = join(parts, "axe")
    tr = join([trail(0.35, 0.09, tr_m)], "trail")
    for v in tr.data.vertices:
        v.co.x *= 0.15
    n = 9
    animate(axe, "spin", {f: {"rot": (2 * math.pi * f / n, 0, 0)} for f in range(0, n + 1, 1)})
    root = empty("throw_axe")
    export_anim(root, "throw_axe", [(axe, root), (tr, root)])


def throw_sword():
    reset()
    steel = mat("throw_sword_steel", (0.78, 0.82, 0.9), 0.2, metal=0.9)
    gold = mat("throw_sword_gold", (0.95, 0.72, 0.25), 0.3, metal=0.9)
    grip = mat("throw_sword_grip", (0.3, 0.18, 0.1), 0.7)
    edge = mat("throw_sword_glow", (0.5, 0.75, 1.0), 0.3, emit=4.0, emit_color=(0.35, 0.6, 1.0))
    tr_m = mat("throw_sword_trail_glow", (0.4, 0.65, 1.0), 0.4, emit=2.0, alpha=0.35, emit_color=(0.3, 0.55, 1.0))
    # a sword flying point first (-Y), 0.52 long, blade flat in XY; it rolls about its length
    parts = [sphere(0.022, (0, 0.25, 0), gold, segs=10, rings=6), rod((0, 0.24, 0), (0, 0.15, 0), 0.014, grip, verts=8),
             rod((-0.07, 0.145, 0), (0.07, 0.145, 0), 0.011, gold, verts=8)]
    bm = bmesh.new()
    prof = [(0.14, 0.024), (-0.15, 0.02), (-0.22, 0.012), (-0.27, 0.0)]
    rings = []
    for y, w in prof:
        rings.append([bm.verts.new((w, y, 0)), bm.verts.new((0, y, 0.007)), bm.verts.new((-w, y, 0)),
                      bm.verts.new((0, y, -0.007))])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
    bm.faces.new(rings[0])
    parts.append(new_obj("blade", bm, steel, smooth=0))
    for sgn in (-1, 1):
        parts.append(tube([(sgn * 0.024, 0.13, 0), (sgn * 0.02, -0.15, 0), (sgn * 0.012, -0.22, 0), (0, -0.268, 0)],
                          [0.004] * 4, edge, verts=4, caps=True, name="edge"))
    sw = join(parts, "sword")
    tr = join([trail(0.32, 0.05, tr_m, y0=0.2)], "trail")
    for v in tr.data.vertices:
        v.co.z *= 0.2
    n = 12
    animate(sw, "spin", {f: {"rot": (0, 2 * math.pi * f / n, 0)} for f in range(0, n + 1)})
    root = empty("throw_sword")
    export_anim(root, "throw_sword", [(sw, root), (tr, root)])


def fireball_model(name, r, outer_c, inner_c, smoke=None, seed=1):
    reset()
    core = mat(name + "_core_glow", inner_c, 0.3, emit=10.0)
    fl = mat(name + "_glow", outer_c, 0.4, emit=5.0, emit_color=outer_c)
    tr_m = mat(name + "_trail_glow", outer_c, 0.4, emit=2.5, alpha=0.4, emit_color=outer_c)
    c = [sphere(r * 0.55, (0, 0, 0), core, segs=16, rings=10)]
    rnd = random.Random(seed)
    shell = []
    for k in range(16):   # licking tongues swept back (+Y)
        a = 2 * math.pi * k / 16
        d = Vector((math.cos(a), 0, math.sin(a)))
        base = d * r * 0.55 + Vector((0, -r * 0.3 * rnd.random(), 0))
        tip = d * r * (0.7 + 0.3 * rnd.random()) + Vector((0, r * (1.6 + 1.2 * rnd.random()), 0))
        shell.append(flame(base, tip, r * 0.35, fl, bend=tuple(d * r * 0.2), verts=7))
    shell.append(ell((0, -0.0, 0), (r * 0.85, r * 0.9, r * 0.85), fl, segs=14, rings=10))
    if smoke:
        sm = mat(name + "_smoke", smoke, 0.9, alpha=0.6)
        for k in range(5):
            shell.append(ico(r * 0.25, (rnd.uniform(-r, r) * 0.5, r * (2.2 + 0.4 * k), rnd.uniform(-r, r) * 0.5), sm, sub=1))
    core_o = join(c, "core")
    flames = join(shell, "flames")
    tr = join([trail(r * 4.0, r * 0.9, tr_m, y0=r * 0.4)], "trail")
    n = 12
    animate(flames, "spin", {f: {"rot": (0, 2 * math.pi * f / n, 0),
                                 "scale": (1 + 0.08 * math.sin(4 * math.pi * f / n),) * 3} for f in range(0, n + 1, 2)})
    animate(core_o, "spin", {f: {"scale": (1 + 0.12 * math.sin(2 * math.pi * f / n * 3),) * 3} for f in range(0, n + 1, 2)},
            linear=False)
    root = empty(name)
    export_anim(root, name, [(core_o, root), (flames, root), (tr, root)])


def fireball():
    fireball_model("fireball", 0.11, (1.0, 0.55, 0.12), (1.0, 0.95, 0.7), seed=3)


def imp_fire():
    fireball_model("imp_fire", 0.085, (1.0, 0.22, 0.05), (1.0, 0.75, 0.3), smoke=(0.12, 0.05, 0.05), seed=8)


def arrow():
    reset()
    wood = mat("arrow_shaft", (0.62, 0.45, 0.25), 0.6)
    steel = mat("arrow_head", (0.6, 0.62, 0.66), 0.3, metal=0.9)
    fl = mat("arrow_fletch", (0.85, 0.15, 0.08), 0.6)
    glint = mat("arrow_glow", (1.0, 0.95, 0.8), 0.2, emit=4.0)
    tr_m = mat("arrow_trail_glow", (1.0, 0.95, 0.85), 0.4, emit=1.5, alpha=0.3)
    parts = [rod((0, 0.24, 0), (0, -0.2, 0), 0.008, wood, verts=8)]
    head = lathe_r([(0.0, 0.07), (0.026, 0.0), (0.012, -0.004), (0.01, -0.02), (0.0, -0.02)], steel, segs=4,
                   name="head", smooth=0)
    head.data.transform(Matrix.Translation((0, -0.2, 0)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    parts.append(head)
    parts.append(sphere(0.006, (0, -0.268, 0), glint, segs=6, rings=4))
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        f = prism([(0.0, 0.0), (0.0, 0.09), (0.028, 0.07), (0.026, 0.0)], 0.003, (0, 0, 0), fl, bevel=0.0)
        f.data.transform(Matrix.Rotation(a, 4, "Y") @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
        f.data.transform(Matrix.Translation((0, 0.13, 0)))
        parts.append(f)
    parts.append(rod((0, 0.235, 0), (0, 0.25, 0), 0.011, fl, verts=8))
    a = join(parts, "arrow")
    tr = join([trail(0.3, 0.02, tr_m, y0=0.25)], "trail")
    export_anim(a, "arrow", [(tr, a)], anim=False)



# ------------------------------------------------------------------ generators (three damage states)

def states(name, build):
    """build(k) -> parts for damage state k (0 whole .. 2 nearly broken); exported as children state_0..2."""
    kids = []
    for k in range(3):
        kids.append(join(build(k), "state_%d" % k))
    root = empty(name)
    export_anim(root, name, [(o, root) for o in kids], anim=False)


def bone_piece(a, b, r, material):
    a, b = Vector(a), Vector(b)
    return [rod(a, b, r, material, verts=6), sphere(r * 1.7, a, material, segs=6, rings=4),
            sphere(r * 1.7, b, material, segs=6, rings=4)]


def skull(c, r, bone_m, dark, eye=None, yaw=0.0, horns=None, jaw=True, broken=False):
    c = Vector(c)
    R = Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, "Z")
    out = [ell((0, 0, 0), (r, r * 1.1, r * 0.95), bone_m, segs=16, rings=10)]
    if jaw:
        out.append(ell((0, -r * 0.45, -r * 0.75), (r * 0.7, r * 0.55, r * 0.35), bone_m, segs=12, rings=6))
    for s in (-1, 1):
        out.append(ell((s * r * 0.38, -r * 0.88, r * 0.05), (r * 0.27, r * 0.2, r * 0.3), dark, segs=10, rings=6))
        if eye:
            out.append(sphere(r * 0.12, (s * r * 0.38, -r * 1.02, r * 0.05), eye, segs=6, rings=4))
        if horns and not (broken and s > 0):
            out.append(tube([(s * r * 0.6, -r * 0.2, r * 0.6), (s * r * 1.2, 0, r * 1.0), (s * r * 1.5, r * 0.3, r * 1.6),
                             (s * r * 1.4, r * 0.4, r * 2.1)], [r * 0.25, r * 0.18, r * 0.1, r * 0.01], horns,
                            verts=8, caps=True, name="horn"))
    out.append(cone((0, -r * 1.0, -r * 0.25), (0, -r * 0.95, -r * 0.05), r * 0.12, dark, verts=3))
    if broken:   # a chunk missing from the crown
        out.append(ell((r * 0.4, -r * 0.2, r * 0.6), (r * 0.45, r * 0.5, r * 0.35), dark, segs=10, rings=6))
    xform(out, R)
    return out


def gen_bones():
    stone = mat("gen_bones_stone", (0.3, 0.29, 0.31), 0.85)
    stone2 = mat("gen_bones_stone_dark", (0.18, 0.17, 0.19), 0.9)
    bone_m = mat("gen_bones_bone", (0.86, 0.81, 0.68), 0.6)
    dark = mat("gen_bones_dark", (0.02, 0.01, 0.01), 0.8)
    horn = mat("gen_bones_horn", (0.12, 0.08, 0.07), 0.4, coat=0.4)
    eye = mat("gen_bones_glow", (0.5, 1.0, 0.4), 0.3, emit=8.0)
    wax = mat("gen_bones_wax", (0.9, 0.85, 0.7), 0.6)
    flame_m = mat("gen_bones_flame_glow", (1.0, 0.7, 0.3), 0.3, emit=8.0)

    def build(k):
        rnd = random.Random(31 + k)
        parts = []
        # the altar: a stepped stone block (split in two at state 2)
        if k < 2:
            parts += [box((0.72, 0.56, 0.12), (0, 0, 0.06), stone2, bevel=0.03),
                      box((0.56, 0.42, 0.3), (0, 0, 0.27), stone, bevel=0.03),
                      box((0.62, 0.48, 0.06), (0, 0, 0.44), stone2, bevel=0.02)]
            if k == 1:
                parts.append(lumpy(0.07, (0.26, -0.2, 0.42), stone2, 5, amount=0.3))
        else:
            parts += [box((0.72, 0.56, 0.12), (0, 0, 0.06), stone2, bevel=0.03)]
            for sgn in (-1, 1):
                b = box((0.27, 0.42, 0.24), (0, 0, 0), stone, bevel=0.03)
                b.data.transform(Matrix.Translation((sgn * 0.16, 0.02, 0.22)) @ Matrix.Rotation(sgn * 0.25, 4, "Y"))
                parts.append(b)
        # runes on the altar's face
        if k < 2:
            for j in range(3):
                parts.append(prism([(-0.02, 0.0), (0.0, 0.035), (0.02, 0.0), (0.0, -0.035)], 0.006,
                                   (-0.14 + 0.14 * j, -0.213, 0.27), eye, bevel=0.0))
        # the great horned skull on top (fallen and broken at state 2)
        if k < 2:
            parts += skull((0, 0.02, 0.6), 0.14, bone_m, dark, eye, horns=horn, broken=k == 1)
        else:
            parts += skull((0.22, -0.3, 0.12), 0.13, bone_m, dark, None, yaw=0.8, horns=horn, broken=True, jaw=False)
        # candles on the corners
        for j, (x, y) in enumerate(((-0.25, -0.18), (0.25, -0.18), (-0.25, 0.18), (0.25, 0.18))):
            if k == 2 and j % 2:
                continue
            z0 = 0.47 if k < 2 else 0.12
            if k == 2:
                x, y = x * 1.25, y * 1.3
            h = 0.08 + 0.04 * ((j * 7) % 3) / 2
            parts.append(cyl(0.022, h, (x, y, z0 + h / 2), wax, verts=10))
            if not (k == 1 and j == 0) and k < 2:
                parts.append(flame((x, y, z0 + h), (x, y, z0 + h + 0.06), 0.016, flame_m, verts=6))
        # the heap of bones round the base
        n = (26, 18, 30)[k]
        for j in range(n):
            a = rnd.uniform(0, 2 * math.pi)
            rr = rnd.uniform(0.35, 0.55) if k < 2 else rnd.uniform(0.1, 0.55)
            c = Vector((rr * math.cos(a), rr * math.sin(a) * 0.9, 0.03 + rnd.uniform(0, 0.06)))
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.6))).normalized()
            L = rnd.uniform(0.08, 0.17)
            parts += bone_piece(c - d * L / 2, c + d * L / 2, 0.012, bone_m)
        for j in range(3 - k + (1 if k == 2 else 0)):
            a = 1.3 + 2.1 * j
            parts += skull((0.42 * math.cos(a), 0.4 * math.sin(a), 0.06), 0.06, bone_m, dark, None, yaw=a + 1.5)
        return parts
    states("gen_bones", build)


def gen_hut():
    wood = mat("gen_hut_wood", (0.36, 0.23, 0.13), 0.8)
    wood2 = mat("gen_hut_wood_dark", (0.2, 0.13, 0.08), 0.85)
    thatch = mat("gen_hut_thatch", (0.55, 0.42, 0.2), 0.95)
    hide = mat("gen_hut_hide", (0.5, 0.33, 0.2), 0.85)
    rope = mat("gen_hut_rope", (0.6, 0.5, 0.32), 0.9)
    bone_m = mat("gen_hut_bone", (0.86, 0.81, 0.68), 0.6)
    dark = mat("gen_hut_dark", (0.03, 0.02, 0.01), 0.9)
    glow = mat("gen_hut_glow", (1.0, 0.45, 0.12), 0.4, emit=5.0, emit_color=(1.0, 0.35, 0.08))

    def build(k):
        rnd = random.Random(70 + k)
        parts = []
        R = 0.4
        # a ring of rough stakes, with a doorway at the front (-Y)
        for j in range(20):
            a = 2 * math.pi * j / 20
            if abs(math.atan2(math.cos(a), -math.sin(a))) < 0.0:
                pass
            x, y = R * math.cos(a), R * math.sin(a)
            door = y < -0.3 and abs(x) < 0.14
            if door:
                continue
            h = 0.52 + rnd.uniform(-0.04, 0.05)
            if k >= 1 and rnd.random() < (0.25 if k == 1 else 0.6):
                h *= rnd.uniform(0.3, 0.7)
            lean = Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0))
            parts.append(rod((x, y, 0.0), Vector((x, y, h)) + lean, 0.04, wood if j % 3 else wood2, verts=7))
            parts.append(cone(Vector((x, y, h)) + lean, Vector((x, y, h + 0.06)) + lean, 0.04, wood2, verts=7))
        for z in (0.15, 0.4):   # rope lashings
            if k == 2 and z > 0.3:
                continue
            ring = [Vector((0.415 * math.cos(a), 0.415 * math.sin(a), z)) for a in
                    (math.radians(x) for x in range(-62, 243, 8))]
            parts.append(tube(ring, [0.008] * len(ring), rope, verts=4, caps=True, name="rope"))
        # the dark doorway glowing from inside; a hide flap
        parts.append(cyl(0.36, 0.02, (0, 0, 0.01), dark, verts=24))
        parts.append(box((0.24, 0.02, 0.4), (0, -0.36, 0.2), glow, bevel=0.0))
        parts.append(box((0.26, 0.05, 0.05), (0, -0.4, 0.43), wood2, bevel=0.01))
        flap = prism([(-0.12, 0.0), (0.0, 0.0), (-0.02, -0.3), (-0.12, -0.34)], 0.012, (0.12, -0.42, 0.42), hide,
                     bevel=0.003)
        parts.append(flap)
        # the conical roof of thatch (torn at 1, collapsed and tilted at 2)
        if k < 2:
            roof = lathe_r([(0.0, 1.18), (0.12, 1.02), (0.3, 0.78), (0.55, 0.5), (0.58, 0.47), (0.5, 0.5),
                            (0.0, 0.62)], thatch, segs=28, name="roof", smooth=30, radial=lambda j, z: 1.0 + (
                                0.04 * math.sin(j * 2.3) if z < 0.52 else 0.0))
            if k == 1:
                def hole(bm):
                    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x > 0.1
                                               and f.calc_center_median().y < 0.0 and 0.7 < f.calc_center_median().z
                                               < 0.95], context="FACES")
                from prism_models import edit
                edit(roof, hole)
                K.finish(roof, thatch, smooth=30)
            parts.append(roof)
            for j in range(8):   # bundled ridges
                a = 2 * math.pi * j / 8 + 0.2
                parts.append(tube([(0.04 * math.cos(a), 0.04 * math.sin(a), 1.12), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.8),
                                   (0.57 * math.cos(a), 0.57 * math.sin(a), 0.49)], [0.022, 0.024, 0.02], thatch,
                                  verts=6, caps=True, name="ridge"))
            for z, r in ((0.6, 0.47), (0.8, 0.31), (0.98, 0.16)):   # rope bands holding the thatch
                parts.append(torus(r, 0.012, (0, 0, z), rope, verts=28, minor=4))
            parts.append(rod((0, 0, 1.1), (0.02, 0.0, 1.3), 0.02, wood2, verts=6))
            parts += skull((0.02, 0.0, 1.32), 0.05, bone_m, dark, None)
        else:
            roof = lathe_r([(0.0, 0.66), (0.16, 0.56), (0.32, 0.4), (0.44, 0.26), (0.46, 0.24), (0.0, 0.34)], thatch,
                           segs=24, name="roof", smooth=30, radial=lambda j, z: 1.0 + 0.12 * math.sin(j * 1.7))
            for v in roof.data.vertices:   # sagging, caved in on one side
                v.co.z -= 0.18 * max(0.0, v.co.x / 0.46) * (1 - abs(v.co.y) / 0.5) * smoothstep(0.2, 0.6, v.co.z)
            roof.data.update()
            roof.data.transform(Matrix.Translation((0.0, 0.04, -0.04)) @ Matrix.Rotation(0.18, 4, "X"))
            parts.append(roof)
            for j in range(5):
                a = 0.6 + 1.25 * j
                parts.append(tube([(0.08 * math.cos(a), 0.08 * math.sin(a), 0.5), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.3),
                                   (0.46 * math.cos(a), 0.46 * math.sin(a), 0.14)], [0.022, 0.024, 0.02], thatch,
                                  verts=6, caps=True, name="ridge"))
            for j in range(10):
                a = rnd.uniform(0, 6.3)
                parts.append(rod((0.6 * math.cos(a), 0.6 * math.sin(a), 0.03),
                                 (0.6 * math.cos(a) + 0.15 * math.cos(a + 1), 0.6 * math.sin(a) + 0.15 * math.sin(a + 1),
                                  0.03), 0.02, wood2, verts=6))
        # two skull totems beside the door
        if k < 2:
            for sgn in (-1, 1):
                x = sgn * 0.3
                parts.append(rod((x, -0.5, 0.0), (x, -0.5, 0.62 - 0.1 * k * (sgn > 0)), 0.02, wood2, verts=6))
                parts += skull((x, -0.5, 0.67 - 0.1 * k * (sgn > 0)), 0.055, bone_m, dark, None)
        return parts
    states("gen_hut", build)


def gen_brazier():
    iron = mat("gen_brazier_iron", (0.2, 0.19, 0.2), 0.45, metal=0.85)
    rust = mat("gen_brazier_rust", (0.42, 0.18, 0.08), 0.7, metal=0.5)
    horn = mat("gen_brazier_horn", (0.75, 0.68, 0.55), 0.4)
    coal = mat("gen_brazier_coal", (0.06, 0.04, 0.04), 0.9)
    ember = mat("gen_brazier_ember_glow", (1.0, 0.3, 0.05), 0.5, emit=4.0)
    fire_m = mat("gen_brazier_glow", (1.0, 0.35, 0.06), 0.4, emit=3.0, emit_color=(1.0, 0.28, 0.04))
    core = mat("gen_brazier_core_glow", (1.0, 0.75, 0.3), 0.3, emit=5.0)
    eye = mat("gen_brazier_eye_glow", (1.0, 0.2, 0.05), 0.3, emit=8.0)
    stone = mat("gen_brazier_stone", (0.24, 0.21, 0.22), 0.85)

    def bowl(k):
        p = [lathe_r([(0.0, 0.0), (0.18, 0.02), (0.3, 0.12), (0.34, 0.22), (0.36, 0.24), (0.33, 0.24), (0.29, 0.14),
                      (0.17, 0.05), (0.0, 0.04)], iron, segs=32, name="bowl", smooth=50),
             torus(0.35, 0.02, (0, 0, 0.235), rust, verts=32, minor=6)]
        for j in range(8):   # spikes round the rim
            a = 2 * math.pi * j / 8 + 0.2
            b = Vector((0.36 * math.cos(a), 0.36 * math.sin(a), 0.24))
            p.append(cone(b, b + Vector((0.06 * math.cos(a), 0.06 * math.sin(a), 0.1)), 0.022, iron, verts=6))
        # a demon face on the front: brows, two glowing eye slits, fangs, curled horns
        fc = Vector((0, -0.32, 0.14))
        p.append(ell(fc, (0.12, 0.04, 0.09), rust, segs=14, rings=8))
        for sgn in (-1, 1):
            p.append(ell(fc + Vector((sgn * 0.045, -0.035, 0.02)), (0.03, 0.01, 0.012), eye, roll=sgn * 20, segs=8, rings=4))
            p.append(cone(fc + Vector((sgn * 0.03, -0.035, -0.04)), fc + Vector((sgn * 0.03, -0.04, -0.08)), 0.012, horn,
                          verts=5))
            p.append(tube([fc + Vector((sgn * 0.09, 0.0, 0.05)), fc + Vector((sgn * 0.18, -0.02, 0.12)),
                           fc + Vector((sgn * 0.2, -0.06, 0.2)), fc + Vector((sgn * 0.16, -0.08, 0.24))],
                          [0.03, 0.022, 0.013, 0.003], horn, verts=8, caps=True, name="horn"))
        # coals and fire
        p.append(cyl(0.29, 0.03, (0, 0, 0.19), coal, verts=24))
        rnd = random.Random(4)
        for j in range(14):
            a = rnd.uniform(0, 6.3)
            rr = rnd.uniform(0, 0.25)
            p.append(lumpy(0.04, (rr * math.cos(a), rr * math.sin(a), 0.21), ember if j % 3 == 0 else coal, j, amount=0.3))
        if k < 2:
            sz = 0.35 if k == 0 else 0.22
            p += fire((0, 0, 0.2), sz, fire_m, core, 7 + k)
            for j in range(4):
                a = 2 * math.pi * j / 4 + 0.6
                p += fire((0.15 * math.cos(a), 0.15 * math.sin(a), 0.2), sz * 0.55, fire_m, core, 20 + j)
        return p

    def build(k):
        parts = [cyl(0.42, 0.06, (0, 0, 0.03), stone, verts=8, bevel=0.015)]
        if k < 2:
            tilt = Matrix.Translation((0, 0, 0.55)) @ (Matrix.Rotation(0.12, 4, "X") if k == 1 else Matrix.Identity(4))
            b = bowl(k)
            xform(b, tilt)
            parts += b
            for j in range(3):   # three clawed legs
                a = 2 * math.pi * j / 3 + math.pi / 2
                d = Vector((math.cos(a), math.sin(a), 0))
                bent = k == 1 and j == 0
                top = d * 0.18 + Vector((0, 0, 0.58))
                mid = d * (0.32 if not bent else 0.26) + Vector((0, 0, 0.3 if not bent else 0.22))
                foot = d * 0.36 + Vector((0, 0, 0.07))
                parts.append(tube([top, mid, foot], [0.03, 0.026, 0.024], iron, verts=8, caps=True, name="leg"))
                for c in (-1, 0, 1):
                    side = Vector((-d.y, d.x, 0))
                    parts.append(cone(foot, foot + d * 0.07 + side * c * 0.05 + Vector((0, 0, -0.03)), 0.014, horn, verts=5))
            parts.append(torus(0.24, 0.018, (0, 0, 0.4), rust, verts=24, minor=5))
        else:
            b = bowl(2)
            xform(b, Matrix.Translation((0.1, -0.05, 0.18)) @ Matrix.Rotation(1.2, 4, "X") @ Matrix.Rotation(0.4, 4, "Z"))
            parts += b
            for j in range(3):
                a = 2 * math.pi * j / 3 + 0.4
                d = Vector((math.cos(a), math.sin(a), 0))
                parts.append(tube([d * 0.2 + Vector((0, 0, 0.08)), d * 0.38 + Vector((0, 0, 0.1)), d * 0.5 + Vector((0, 0, 0.04))],
                                  [0.03, 0.026, 0.024], iron, verts=8, caps=True, name="leg"))
            rnd = random.Random(9)
            for j in range(12):   # spilt embers
                a = rnd.uniform(-1.0, 1.0) - math.pi / 2
                rr = rnd.uniform(0.25, 0.55)
                parts.append(lumpy(0.035, (rr * math.cos(a), rr * math.sin(a), 0.07), ember if j % 2 else coal, j + 50,
                                   amount=0.3))
        return parts
    states("gen_brazier", build)



# ------------------------------------------------------------------ dungeon props (origin at the base centre)

def plank_box(x0, x1, y0, y1, z0, z1, wood, wood2, n, axis="x", gap=0.006, bevel=0.008):
    """A slab of n planks running along `axis`."""
    out = []
    if axis == "x":
        h = (z1 - z0) / n
        for i in range(n):
            out.append(box((x1 - x0, y1 - y0, h - gap), ((x0 + x1) / 2, (y0 + y1) / 2, z0 + h * (i + 0.5)),
                           wood if i % 2 else wood2, bevel=bevel))
    else:
        w = (x1 - x0) / n
        for i in range(n):
            out.append(box((w - gap, y1 - y0, z1 - z0), (x0 + w * (i + 0.5), (y0 + y1) / 2, (z0 + z1) / 2),
                           wood if i % 2 else wood2, bevel=bevel))
    return out


def door():
    reset()
    wood = mat("door_wood", (0.38, 0.24, 0.13), 0.75)
    wood2 = mat("door_wood_dark", (0.3, 0.18, 0.1), 0.8)
    iron = mat("door_iron", (0.22, 0.22, 0.24), 0.4, metal=0.85)
    stone = mat("door_stone", (0.34, 0.32, 0.33), 0.85)
    glow = mat("door_lock_glow", (1.0, 0.75, 0.3), 0.3, emit=3.0)
    # the frame: two iron-capped stone jambs and a lintel (the leaf lifts up between them); a threshold
    fr = [box((0.12, 0.3, 1.3), (s * 0.56, 0, 0.65), stone, bevel=0.02) for s in (-1, 1)]
    fr += [box((1.24, 0.3, 0.16), (0, 0, 1.38), stone, bevel=0.02), box((1.0, 0.24, 0.025), (0, 0, 0.0125), stone, bevel=0.008)]
    for s in (-1, 1):
        fr.append(box((0.03, 0.16, 1.28), (s * 0.505, 0, 0.64), iron, bevel=0.006))
        for z in (0.3, 0.9):
            fr.append(cyl(0.02, 0.02, (s * 0.56, -0.155, z), iron, rot=(math.pi / 2, 0, 0), verts=8))
    frame = join(fr, "door")
    # the leaf: vertical planks, three iron bands with studs, a ring pull, a lock plate with a glowing keyhole
    lf = plank_box(-0.49, 0.49, -0.05, 0.05, 0.02, 1.27, wood, wood2, 6, axis="z")
    for z in (0.2, 0.65, 1.1):
        lf.append(box((0.99, 0.12, 0.07), (0, 0, z), iron, bevel=0.01))
        for k in range(7):
            for sgn in (-1, 1):
                lf.append(sphere(0.014, (-0.42 + 0.14 * k, sgn * 0.062, z), iron, segs=6, rings=4))
    lf.append(box((0.14, 0.12, 0.2), (0.28, 0, 0.62), iron, bevel=0.01))
    for sgn in (-1, 1):
        lf.append(box((0.03, 0.01, 0.06), (0.28, sgn * 0.062, 0.63), glow, bevel=0.0))
        lf.append(torus(0.05, 0.01, (-0.25, sgn * 0.075, 0.6), iron, rot=(math.pi / 2, 0, 0), verts=14, minor=4))
    leaf = join(lf, "leaf")
    export_anim(frame, "door", [(leaf, frame)], anim=False)


def key():
    reset()
    gold = mat("key_glow", (1.0, 0.78, 0.25), 0.25, metal=0.6, emit=1.5, emit_color=(1.0, 0.65, 0.15))
    gem = mat("key_gem_glow", (0.3, 0.9, 1.0), 0.1, emit=4.0)
    # a big ornate key lying on the floor at a slant, its bow (a ring with a gem) towards the camera
    parts = [torus(0.07, 0.016, (0, -0.13, 0), gold, rot=(0, 0, 0), verts=20, minor=6),
             sphere(0.028, (0, -0.13, 0), gem, segs=10, rings=6),
             rod((0, -0.06, 0), (0, 0.19, 0), 0.014, gold, verts=10),
             box((0.02, 0.05, 0.02), (0.035, 0.155, 0), gold, bevel=0.004),
             box((0.02, 0.025, 0.02), (0.035, 0.105, 0), gold, bevel=0.004),
             torus(0.02, 0.006, (0, -0.055, 0), gold, rot=(math.pi / 2, 0, 0), verts=12, minor=4)]
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        parts.append(sphere(0.012, (0.088 * math.cos(a), -0.13 + 0.088 * math.sin(a), 0), gold, segs=6, rings=4))
    xform(parts, Matrix.Translation((0, 0, 0.12)) @ Matrix.Rotation(math.radians(35), 4, "X") @ Matrix.Scale(1.3, 4))
    k_o = join(parts, "key")
    export(k_o, "key")


def chest():
    reset()
    wood = mat("chest_wood", (0.45, 0.24, 0.1), 0.65)
    wood2 = mat("chest_wood_dark", (0.33, 0.17, 0.08), 0.7)
    iron = mat("chest_iron", (0.24, 0.23, 0.25), 0.4, metal=0.85)
    gold = mat("chest_gold", (1.0, 0.75, 0.25), 0.25, metal=0.95)
    glow = mat("chest_gold_glow", (1.0, 0.8, 0.35), 0.3, metal=0.5, emit=1.5, emit_color=(1.0, 0.7, 0.2))
    W, D, H = 0.62, 0.42, 0.3
    body = plank_box(-W / 2, W / 2, -D / 2, D / 2, 0.0, H, wood, wood2, 3)
    for x in (-W / 2 + 0.06, W / 2 - 0.06):
        body.append(box((0.045, D + 0.02, H + 0.01), (x, 0, H / 2), iron, bevel=0.006))
    for x, y in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        body.append(box((0.06, 0.06, 0.06), (x * (W / 2 - 0.005), y * (D / 2 - 0.005), 0.03), iron, bevel=0.008))
    body.append(box((0.09, 0.03, 0.1), (0, -D / 2 - 0.01, H - 0.06), gold, bevel=0.008))
    body.append(box((0.015, 0.01, 0.03), (0, -D / 2 - 0.028, H - 0.07), iron, bevel=0.0))
    # treasure inside, heaped above the rim (seen when the lid opens)
    rnd = random.Random(12)
    body.append(box((W - 0.04, D - 0.04, 0.02), (0, 0, H - 0.03), glow, bevel=0.0))
    for k in range(26):
        body.append(cyl(0.028, 0.008, (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.16, 0.16), H - 0.015 + rnd.uniform(0, 0.03)),
                        glow, rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0), verts=12))
    base = join(body, "chest")
    # the lid: a barrel-vault, hinged along the back top edge (its origin on the hinge)
    lid_parts = []
    prof = [(-D / 2 + D * (1 - math.cos(math.pi * t / 2 * 2)) / 2, H + 0.12 * math.sin(math.pi * t)) for t in
            (k / 10 for k in range(11))]
    rings = [[Vector((x, y, z)) for (y, z) in prof] for x in (-W / 2, W / 2)]
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    for i in range(len(prof) - 1):
        bm.faces.new((vs[0][i], vs[0][i + 1], vs[1][i + 1], vs[1][i]))
    bm.faces.new([v for v in vs[0]][::-1])
    bm.faces.new([v for v in vs[1]])
    lid = new_obj("lid", bm, wood, smooth=40)
    solid(lid, 0.02)
    lid_parts.append(K.finish(lid, wood, smooth=40))
    for x in (-W / 2 + 0.06, W / 2 - 0.06):
        band = [Vector((x, y, z + 0.008)) for (y, z) in prof]
        lid_parts.append(tube(band, [0.016] * len(band), iron, verts=6, caps=True, name="band"))
    lid_parts.append(box((0.09, 0.03, 0.06), (0, -D / 2 - 0.012, H + 0.02), gold, bevel=0.008))
    lid_o = join(lid_parts, "lid", pivot=(0, D / 2, H))
    export_anim(base, "chest", [(lid_o, base)], anim=False)


def coin_heap(c, r, h, gold, n, seed, gems=()):
    rnd = random.Random(seed)
    out = [lathe_r([(0.0, h), (r * 0.5, h * 0.7), (r * 0.85, h * 0.3), (r, 0.0), (0.0, 0.0)], gold, segs=20, name="heap",
                   center=(c[0], c[1], 0))]
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rnd.random())
        z = h * (1 - (rr / r) ** 1.6) + 0.004
        out.append(cyl(0.026, 0.007, (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), z), gold,
                       rot=(rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 0), verts=12))
    for g, p in gems:
        out.append(ico(0.03, p, g, sub=1, smooth=0))
    return out


def gold_pile():
    reset()
    gold = mat("gold_pile_gold", (1.0, 0.74, 0.22), 0.25, metal=0.95)
    glint = mat("gold_pile_glow", (1.0, 0.85, 0.45), 0.3, metal=0.5, emit=1.2, emit_color=(1.0, 0.7, 0.2))
    ruby = mat("gold_pile_ruby_glow", (1.0, 0.1, 0.15), 0.1, emit=2.0)
    sapph = mat("gold_pile_sapphire_glow", (0.2, 0.4, 1.0), 0.1, emit=2.0)
    parts = coin_heap((0, 0), 0.22, 0.12, gold, 40, 3, gems=((ruby, (0.05, -0.08, 0.09)), (sapph, (-0.08, 0.02, 0.08))))
    parts += coin_heap((0.17, -0.12), 0.09, 0.05, glint, 10, 4)
    parts += coin_heap((-0.16, -0.13), 0.07, 0.04, gold, 6, 5)
    parts.append(lathe_r([(0.0, 0.2), (0.04, 0.2), (0.05, 0.12), (0.03, 0.04), (0.035, 0.0), (0.0, 0.0)], gold, segs=16,
                         name="goblet", center=(0.12, 0.1, 0)))
    parts.append(torus(0.05, 0.008, (0.12, 0.1, 0.2), gold, verts=16, minor=4))
    export(join(parts, "gold_pile"), "gold_pile")


def food_ham():
    reset()
    meat = mat("food_ham_meat", (0.62, 0.24, 0.12), 0.45, coat=0.4)
    crust = mat("food_ham_crust", (0.45, 0.17, 0.07), 0.5, coat=0.3)
    fat = mat("food_ham_fat", (0.95, 0.82, 0.7), 0.5)
    bone_m = mat("food_ham_bone", (0.93, 0.9, 0.8), 0.5)
    plate = mat("food_ham_plate", (0.55, 0.5, 0.45), 0.4, metal=0.6)
    green = mat("food_ham_herb", (0.25, 0.55, 0.15), 0.6)
    parts = [lathe_r([(0.0, 0.03), (0.2, 0.03), (0.24, 0.05), (0.25, 0.04), (0.22, 0.0), (0.0, 0.0)], plate, segs=28,
                     name="plate")]
    h = ell((0.0, 0.03, 0.12), (0.15, 0.12, 0.1), crust, pitch=-15, segs=22, rings=14)
    parts.append(h)
    parts.append(ell((0.0, -0.08, 0.13), (0.11, 0.035, 0.08), meat, pitch=-15, segs=18, rings=10))
    parts.append(torus(0.1, 0.012, (0.0, -0.09, 0.13), fat, rot=(math.radians(75), 0, 0), verts=20, minor=5,
                       scale=(1.05, 0.8, 1)))
    parts += [rod((0, 0.1, 0.16), (0.02, 0.22, 0.22), 0.022, bone_m, verts=10),
              sphere(0.028, (0.0, 0.225, 0.225), bone_m, segs=10, rings=6), sphere(0.026, (0.035, 0.22, 0.23), bone_m,
                                                                                    segs=10, rings=6)]
    for k in range(5):
        a = 2.4 * k
        parts.append(ell((0.17 * math.cos(a), 0.16 * math.sin(a), 0.045), (0.03, 0.015, 0.008), green, yaw=math.degrees(a),
                         segs=8, rings=4))
    export(join(parts, "food_ham"), "food_ham")


def food_bowl():
    reset()
    clay = mat("food_bowl_clay", (0.55, 0.3, 0.16), 0.7)
    stew = mat("food_bowl_stew", (0.5, 0.25, 0.08), 0.35, coat=0.5)
    carrot = mat("food_bowl_carrot", (1.0, 0.45, 0.1), 0.5)
    pea = mat("food_bowl_pea", (0.4, 0.7, 0.2), 0.5)
    bread = mat("food_bowl_bread", (0.85, 0.6, 0.3), 0.7)
    steam = mat("food_bowl_steam_glow", (1.0, 1.0, 1.0), 0.5, emit=0.6, alpha=0.3)
    parts = [lathe_r([(0.0, 0.0), (0.09, 0.0), (0.1, 0.015), (0.17, 0.08), (0.2, 0.15), (0.19, 0.16), (0.16, 0.09),
                      (0.0, 0.07)], clay, segs=28, name="bowl"),
             cyl(0.175, 0.01, (0, 0, 0.13), stew, verts=28)]
    rnd = random.Random(2)
    for k in range(9):
        a, rr = rnd.uniform(0, 6.3), rnd.uniform(0, 0.13)
        parts.append(ico(0.018, (rr * math.cos(a), rr * math.sin(a), 0.14), carrot if k % 2 else pea, sub=1))
    parts.append(ell((0.12, 0.05, 0.16), (0.07, 0.04, 0.03), bread, yaw=30, segs=12, rings=8))
    for k in range(3):
        b = Vector((-0.06 + 0.06 * k, 0.0, 0.16))
        parts.append(tube([b, b + Vector((0.02, 0, 0.08)), b + Vector((-0.015, 0, 0.16)), b + Vector((0.01, 0, 0.23))],
                          [0.012, 0.018, 0.014, 0.003], steam, verts=8, caps=True, name="steam"))
    export(join(parts, "food_bowl"), "food_bowl")


def food_cider():
    reset()
    clay = mat("food_cider_clay", (0.72, 0.55, 0.38), 0.6, coat=0.3)
    glaze = mat("food_cider_glaze", (0.35, 0.18, 0.1), 0.35, coat=0.6)
    cork = mat("food_cider_cork", (0.7, 0.55, 0.35), 0.8)
    apple = mat("food_cider_apple", (0.8, 0.12, 0.08), 0.4, coat=0.4)
    leaf = mat("food_cider_leaf", (0.25, 0.55, 0.15), 0.6)
    jug = lathe_r([(0.0, 0.0), (0.09, 0.0), (0.13, 0.06), (0.14, 0.14), (0.12, 0.22), (0.06, 0.28), (0.045, 0.32),
                   (0.05, 0.34), (0.0, 0.34)], clay, segs=28, name="jug")
    jug.data.materials.append(glaze)
    for f in jug.data.polygons:
        if f.center.z > 0.2:
            f.material_index = 1
    parts = [jug, torus(0.135, 0.008, (0, 0, 0.12), glaze, verts=28, minor=4),
             tube([(0.05, 0.0, 0.29), (0.13, 0.0, 0.3), (0.17, 0.0, 0.22), (0.13, 0.0, 0.12)], [0.016] * 4, glaze,
                  verts=8, caps=True, name="handle"),
             cyl(0.04, 0.05, (0, 0, 0.355), cork, verts=12, r2=0.045)]
    parts += [sphere(0.05, (-0.12, -0.12, 0.05), apple, segs=14, rings=10),
              rod((-0.12, -0.12, 0.095), (-0.11, -0.12, 0.12), 0.005, glaze, verts=4),
              ell((-0.1, -0.12, 0.115), (0.02, 0.008, 0.01), leaf, segs=8, rings=4)]
    export(join(parts, "food_cider"), "food_cider")


def potion():
    reset()
    glass = mat("potion_glass", (0.75, 0.85, 0.95), 0.05, coat=1.0, alpha=0.35)
    liquid = mat("potion_glow", (0.25, 0.55, 1.0), 0.2, emit=3.5, emit_color=(0.2, 0.5, 1.0))
    cork = mat("potion_cork", (0.65, 0.5, 0.3), 0.8)
    gold = mat("potion_gold", (1.0, 0.76, 0.28), 0.3, metal=0.9)
    star = mat("potion_star_glow", (1.0, 1.0, 0.9), 0.2, emit=6.0)
    parts = [lathe_r([(0.0, 0.0), (0.07, 0.005), (0.12, 0.06), (0.13, 0.13), (0.1, 0.2), (0.045, 0.24), (0.04, 0.3),
                      (0.05, 0.31), (0.0, 0.31)], glass, segs=28, name="flask"),
             lathe_r([(0.0, 0.17), (0.115, 0.17), (0.125, 0.12), (0.11, 0.05), (0.065, 0.012), (0.0, 0.01)], liquid,
                     segs=24, name="liquid"),
             cyl(0.036, 0.06, (0, 0, 0.32), cork, verts=12), torus(0.045, 0.008, (0, 0, 0.27), gold, verts=16, minor=4)]
    for k in range(4):
        parts.append(ico(0.012, (0.04 * math.cos(k * 1.7), 0.04 * math.sin(k * 1.7), 0.06 + 0.025 * k), star, sub=1))
    export(join(parts, "potion"), "potion")


def amulet():
    reset()
    gold = mat("amulet_gold", (1.0, 0.76, 0.28), 0.25, metal=0.95)
    gem = mat("amulet_glow", (0.9, 0.25, 1.0), 0.1, emit=5.0, emit_color=(0.85, 0.2, 1.0))
    halo = mat("amulet_halo_glow", (0.85, 0.5, 1.0), 0.3, emit=2.0, alpha=0.35)
    cushion = mat("amulet_cushion", (0.45, 0.06, 0.12), 0.8)
    tassel = mat("amulet_tassel", (1.0, 0.76, 0.28), 0.6)
    # a gold disc with an eye-shaped gem, standing tilted back on a small red cushion, its chain coiled round it
    c = Vector((0, 0.0, 0.25))
    disc = [cyl(0.11, 0.02, (0, 0, 0), gold, rot=(math.pi / 2, 0, 0), verts=32, bevel=0.005),
            torus(0.11, 0.012, (0, 0, 0), gold, rot=(math.pi / 2, 0, 0), verts=32, minor=6)]
    for k in range(8):
        a = 2 * math.pi * k / 8
        disc.append(cone((0.11 * math.cos(a), 0, 0.11 * math.sin(a)), (0.15 * math.cos(a), 0, 0.15 * math.sin(a)), 0.018,
                         gold, verts=6))
    g = ell((0, -0.02, 0), (0.05, 0.03, 0.065), gem, segs=16, rings=10)
    disc += [g, torus(0.07, 0.008, (0, -0.012, 0), gold, rot=(math.pi / 2, 0, 0), verts=24, minor=4,
                      scale=(0.85, 1, 1.1)), torus(0.17, 0.005, (0, 0.0, 0), halo, rot=(math.pi / 2, 0, 0), verts=40,
                                                   minor=4)]
    xform(disc, Matrix.Translation(c) @ Matrix.Rotation(math.radians(-25), 4, "X"))
    parts = disc + [ell((0, 0.03, 0.04), (0.16, 0.13, 0.045), cushion, segs=20, rings=10)]
    for s_ in (-1, 1):
        for x, y in ((0.14, 0.11), (0.14, -0.05)):
            parts.append(cone((s_ * x, y, 0.05), (s_ * (x + 0.02), y, 0.0), 0.012, tassel, verts=6))
    ch = [Vector((0.13 * math.cos(a), 0.03 + 0.1 * math.sin(a), 0.085 + 0.01 * math.sin(3 * a))) for a in
          (2 * math.pi * k / 40 for k in range(41))]
    for k in range(0, 40, 2):
        parts.append(torus(0.008, 0.002, ch[k], gold, verts=8, minor=3, rot=(0, math.pi / 2 * (k % 4 == 0), 0)))
    export(join(parts, "amulet"), "amulet")


def exit_tile():
    reset()
    stone = mat("exit_stone", (0.36, 0.34, 0.36), 0.85)
    stone2 = mat("exit_stone_dark", (0.2, 0.19, 0.21), 0.9)
    rune = mat("exit_rune_glow", (0.4, 0.9, 1.0), 0.3, emit=4.0)
    glow = mat("exit_glow", (0.35, 0.8, 1.0), 0.3, emit=3.0, emit_color=(0.3, 0.75, 1.0))
    # a 1 x 1 stairwell: a rim flush with the floor (top at y 0.03); the steps go down away from the camera (from
    # the front edge, Godot +Z, towards the back) into a glowing doorway in the shaft's back wall
    parts = []
    T = 0.09
    for x0, x1, y0, y1 in ((-0.5, 0.5, -0.5, -0.5 + T), (-0.5, 0.5, 0.5 - T, 0.5), (-0.5, -0.5 + T, -0.5, 0.5),
                           (0.5 - T, 0.5, -0.5, 0.5)):
        parts.append(box((x1 - x0, y1 - y0, 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, 0.0), stone, bevel=0.012))
    inner = 0.5 - T
    for sgn in (-1, 1):
        parts.append(box((0.04, 2 * inner, 0.75), (sgn * (inner - 0.02), 0, -0.375), stone2, bevel=0.0))
    parts.append(box((2 * inner, 0.04, 0.75), (0, inner - 0.02, -0.375), stone2, bevel=0.0))
    n = 6
    depth = (2 * inner - 0.04) / (n + 1)
    for k in range(n):
        y0 = -inner + depth * k
        zt = -0.07 - 0.095 * k
        parts.append(box((2 * inner - 0.08, depth, 0.75 + zt), (0, y0 + depth / 2, (zt - 0.75) / 2), stone if k % 2 else
                         stone2, bevel=0.008))
    parts.append(box((2 * inner - 0.16, 0.02, 0.5), (0, inner - 0.045, -0.5), glow, bevel=0.0))
    parts.append(box((2 * inner - 0.08, depth + 0.02, 0.02), (0, inner - 0.04 - depth / 2, -0.7), glow, bevel=0.0))
    # runes round the rim and a faint glowing veil over the opening
    for k in range(12):
        t = k / 12
        side = int(t * 4)
        u = (t * 4 - side) * 0.8 - 0.4
        p = [(u, -0.5 + T / 2), (0.5 - T / 2, u), (-u, 0.5 - T / 2), (-0.5 + T / 2, -u)][side]
        parts.append(prism([(-0.015, 0.0), (0.0, 0.025), (0.015, 0.0), (0.0, -0.025)], 0.006, (p[0], p[1], 0.031), rune,
                           rot=(math.pi / 2, 0, 0), bevel=0.0))
    export(join(parts, "exit"), "exit")


def torch_wall():
    reset()
    iron = mat("torch_wall_iron", (0.22, 0.21, 0.22), 0.45, metal=0.85)
    wood = mat("torch_wall_wood", (0.32, 0.2, 0.1), 0.8)
    wrap = mat("torch_wall_wrap", (0.16, 0.1, 0.07), 0.9)
    fl = mat("torch_wall_glow", (1.0, 0.5, 0.12), 0.4, emit=3.5, emit_color=(1.0, 0.42, 0.08))
    core = mat("torch_wall_core_glow", (1.0, 0.85, 0.45), 0.3, emit=6.0)
    # a wall sconce: the back plate on the wall (y = 0, the wall face; the room is towards -Y = Godot +Z),
    # a bracket holding a torch leaning out; mounted 1.1 above the floor
    Z = 1.1
    parts = [box((0.12, 0.025, 0.2), (0, -0.0125, Z), iron, bevel=0.006),
             tube([(0, -0.02, Z - 0.05), (0, -0.09, Z - 0.03), (0, -0.13, Z + 0.02)], [0.012] * 3, iron, verts=6,
                  caps=True, name="arm"),
             torus(0.035, 0.008, (0, -0.13, Z + 0.03), iron, verts=14, minor=4)]
    for z in (Z - 0.07, Z + 0.07):
        parts.append(sphere(0.012, (0, -0.028, z), iron, segs=6, rings=4))
    d = Vector((0, -0.35, 1)).normalized()
    a = Vector((0, -0.13, Z + 0.03)) - d * 0.12
    b = a + d * 0.3
    parts += [rod(a, b, 0.016, wood, r2=0.02, verts=8), rod(b - d * 0.02, b + d * 0.05, 0.026, wrap, r2=0.03, verts=10),
              torus(0.03, 0.005, b + d * 0.01, iron, verts=10, minor=4)]
    base = join(parts, "torch_wall")
    top = b + d * 0.045
    flame_o = join(fire(top, 0.11, fl, core, 11), "flame", pivot=top)
    light = empty("light")
    light.location = top + Vector((0, -0.03, 0.08))
    animate(flame_o, "flicker", {0: {"scale": (1.0, 1.0, 1.0)}, 3: {"scale": (0.92, 0.95, 1.12), "rot": (0.05, 0.08, 0.3)},
                                 6: {"scale": (1.06, 1.04, 0.9), "rot": (-0.04, -0.05, 0.7)},
                                 9: {"scale": (0.95, 0.98, 1.08), "rot": (0.03, 0.06, 1.1)},
                                 12: {"scale": (1.0, 1.0, 1.0), "rot": (0, 0, 0)}}, linear=False)
    export_anim(base, "torch_wall", [(flame_o, base), (light, base)])


def pillar():
    reset()
    stone = mat("pillar_stone", (0.4, 0.38, 0.39), 0.85)
    stone2 = mat("pillar_stone_dark", (0.26, 0.25, 0.27), 0.9)
    moss = mat("pillar_moss", (0.22, 0.32, 0.12), 0.9)
    H = 1.6
    parts = [box((1.0, 1.0, 0.14), (0, 0, 0.07), stone2, bevel=0.03), box((0.86, 0.86, 0.1), (0, 0, 0.19), stone, bevel=0.025),
             box((1.0, 1.0, 0.14), (0, 0, H - 0.07), stone2, bevel=0.03), box((0.86, 0.86, 0.1), (0, 0, H - 0.19), stone,
                                                                                bevel=0.025)]
    shaft = lathe_r([(0.0, H - 0.24), (0.33, H - 0.24), (0.3, H - 0.3), (0.3, 0.3), (0.33, 0.24), (0.0, 0.24)], stone,
                    segs=16, name="shaft", smooth=0)
    parts.append(shaft)
    for k in range(16):   # fluting
        a = 2 * math.pi * (k + 0.5) / 16
        parts.append(rod((0.3 * math.cos(a), 0.3 * math.sin(a), 0.32), (0.3 * math.cos(a), 0.3 * math.sin(a), H - 0.32),
                         0.018, stone2, verts=5))
    rnd = random.Random(3)
    for k in range(6):
        a = rnd.uniform(0, 6.3)
        parts.append(lumpy(0.06, (0.33 * math.cos(a), 0.33 * math.sin(a), 0.26), moss, k, amount=0.3, scale=(1.4, 1.4, 0.5)))
    for k in range(4):   # chips on the plinth
        parts.append(lumpy(0.04, (rnd.uniform(-0.45, 0.45), -0.48, 0.12), stone2, k + 10, amount=0.3))
    export(join(parts, "pillar"), "pillar")


def rubble():
    reset()
    stone = mat("rubble_stone", (0.4, 0.38, 0.39), 0.85)
    stone2 = mat("rubble_stone_dark", (0.27, 0.26, 0.28), 0.9)
    dust = mat("rubble_dust", (0.32, 0.29, 0.27), 1.0)
    rnd = random.Random(8)
    parts = [lathe_r([(0.0, 0.08), (0.25, 0.05), (0.4, 0.0), (0.0, 0.0)], dust, segs=20, name="dust",
                     radial=lambda k, z: 1 + 0.15 * math.sin(k * 1.9))]
    for k in range(18):
        a = rnd.uniform(0, 6.3)
        rr = rnd.uniform(0, 0.36)
        sz = rnd.uniform(0.05, 0.12) * (1.3 - rr)
        parts.append(lumpy(sz, (rr * math.cos(a), rr * math.sin(a), sz * 0.6 + 0.08 * (1 - rr / 0.36)),
                           stone if k % 3 else stone2, k, amount=0.25, scale=(1.2, 1.0, 0.8)))
    b = box((0.3, 0.16, 0.14), (0.05, -0.05, 0.16), stone, bevel=0.02)
    b.data.transform(Matrix.Translation((0.05, -0.05, 0.16)) @ Matrix.Rotation(0.4, 4, "Y") @ Matrix.Translation((-0.05, 0.05, -0.16)))
    parts.append(b)
    export(join(parts, "rubble"), "rubble")


def barrel():
    reset()
    wood = mat("barrel_wood", (0.45, 0.28, 0.14), 0.7)
    wood2 = mat("barrel_wood_dark", (0.36, 0.21, 0.1), 0.75)
    iron = mat("barrel_iron", (0.24, 0.23, 0.25), 0.4, metal=0.85)
    H, R = 0.62, 0.22
    parts = []
    n = 14
    for k in range(n):   # bulging staves
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 0.92) / n
        bm = bmesh.new()
        rows = []
        for j in range(7):
            z = H * j / 6
            r = R * (0.86 + 0.14 * math.sin(math.pi * j / 6))
            rows.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in (a0, (a0 + a1) / 2, a1)])
        for r0, r1 in zip(rows, rows[1:]):
            for i in range(2):
                bm.faces.new((r0[i], r0[i + 1], r1[i + 1], r1[i]))
        o = new_obj("stave", bm, wood if k % 2 else wood2, smooth=30)
        solid(o, 0.02)
        parts.append(K.finish(o, wood if k % 2 else wood2, smooth=30))
    for z in (0.08, 0.2, H - 0.2, H - 0.08):
        r = R * (0.86 + 0.14 * math.sin(math.pi * z / H)) + 0.006
        parts.append(torus(r, 0.01, (0, 0, z), iron, verts=28, minor=4, scale=(1, 1, 1.5)))
    parts.append(cyl(R * 0.85, 0.02, (0, 0, H - 0.03), wood2, verts=24))
    parts.append(cyl(0.03, 0.02, (0.08, -0.05, H - 0.012), wood, verts=10))
    export(join(parts, "barrel"), "barrel")


def bones_decor():
    reset()
    bone_m = mat("bones_decor_bone", (0.86, 0.81, 0.68), 0.6)
    dark = mat("bones_decor_dark", (0.03, 0.02, 0.02), 0.8)
    rust = mat("bones_decor_rust", (0.4, 0.22, 0.12), 0.6, metal=0.6)
    rnd = random.Random(44)
    parts = skull((0.06, -0.05, 0.06), 0.06, bone_m, dark, None, yaw=0.5)
    for k in range(9):
        a = rnd.uniform(0, 6.3)
        rr = rnd.uniform(0.08, 0.38)
        c = Vector((rr * math.cos(a), rr * math.sin(a), 0.015))
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
        parts += bone_piece(c - d * 0.08, c + d * 0.08, 0.011, bone_m)
    for k in range(5):   # ribs
        c = Vector((-0.15 + 0.035 * k, 0.14, 0.01))
        arc = [c + Vector((0.07 * math.cos(t) * 0.4, 0.07 * math.sin(t), 0.02 * math.sin(t))) for t in
               (math.radians(x) for x in range(-80, 81, 20))]
        parts.append(tube(arc, [0.006] * len(arc), bone_m, verts=5, caps=True, name="rib"))
    parts.append(rod((0.2, 0.2, 0.01), (0.38, -0.05, 0.01), 0.01, rust, verts=6))   # a rusted blade
    parts.append(rod((0.19, 0.22, 0.012), (0.23, 0.18, 0.012), 0.014, rust, verts=6))
    export(join(parts, "bones_decor"), "bones_decor")


def cobweb():
    reset()
    web = mat("cobweb_silk", (0.85, 0.85, 0.88), 0.6, alpha=0.55)
    # a web in a corner: its origin is the corner where two walls meet the ceiling line (anchor it at the top
    # corner of a wall); it spans 0.6 along +X and 0.6 down, in the plane of the wall face (y = 0) facing -Y.
    parts = []
    spokes = 7
    for k in range(spokes):
        a = math.radians(-90 * k / (spokes - 1))
        parts.append(rod((0, 0, 0), (0.62 * math.cos(a), -0.002, 0.62 * math.sin(a)), 0.003, web, verts=4))
    for ring in range(1, 7):
        r = 0.09 * ring
        pts = []
        for k in range(spokes):
            a = math.radians(-90 * k / (spokes - 1))
            pts.append(Vector((r * math.cos(a), -0.004, r * math.sin(a))))
        for p0, p1 in zip(pts, pts[1:]):
            m = (p0 + p1) / 2 * 0.93   # sagging threads
            parts.append(tube([p0, m, p1], [0.002] * 3, web, verts=4, caps=False, name="thread"))
    parts.append(tube([(0.35, -0.004, -0.2), (0.33, -0.01, -0.33), (0.34, -0.012, -0.45)], [0.002] * 3, web, verts=4))
    parts.append(ell((0.34, -0.015, -0.46), (0.012, 0.01, 0.015), mat("cobweb_spider", (0.05, 0.04, 0.04), 0.4), segs=8,
                     rings=6))
    export(join(parts, "cobweb"), "cobweb")


def banner():
    reset()
    cloth = mat("banner_team", (0.5, 0.06, 0.08), 0.8)
    trim = mat("banner_trim", (0.95, 0.72, 0.25), 0.4, metal=0.6)
    iron = mat("banner_iron", (0.22, 0.21, 0.22), 0.45, metal=0.85)
    emb = mat("banner_emblem", (0.95, 0.8, 0.4), 0.5)
    # a wall banner: origin at the middle of its rod, which sits against the wall (y = 0) and the cloth hangs down
    # 0.9 in front of it, facing -Y (Godot +Z)
    W, L = 0.46, 0.9
    nu, nv = 8, 12
    grid = []
    for i in range(nv + 1):
        v = i / nv
        row = []
        for j in range(nu + 1):
            u = -1 + 2 * j / nu
            z = -v * L
            if v > 0.82:   # a swallowtail
                z = -L * 0.82 - (L * 0.18) * (abs(u) ** 0.7) * (v - 0.82) / 0.18 / max(0.3, 1.0)
                z = -(0.82 + 0.18 * (v - 0.82) / 0.18 * abs(u)) * L
            row.append(Vector((u * W / 2, -0.03 - 0.012 * math.sin(u * math.pi * 1.5 + v * 3), z)))
        grid.append(row)
    cl = sheet(grid, cloth, "cloth", thick=0.008)
    parts = [cl, rod((-W / 2 - 0.06, -0.03, 0.02), (W / 2 + 0.06, -0.03, 0.02), 0.014, iron, verts=8)]
    for s in (-1, 1):
        parts.append(sphere(0.022, (s * (W / 2 + 0.07), -0.03, 0.02), trim, segs=8, rings=6))
        parts.append(rod((s * W / 2 * 0.97, -0.04, -0.01), (s * W / 2 * 0.97, -0.04, -0.8 * L), 0.007, trim, verts=5))
    parts.append(rod((-W / 2, -0.04, -0.03), (W / 2, -0.04, -0.03), 0.008, trim, verts=5))
    flame_poly = [(0.0, 0.07), (0.022, 0.03), (0.03, -0.005), (0.02, -0.03), (0.0, -0.04), (-0.02, -0.03),
                  (-0.03, -0.005), (-0.016, 0.02), (-0.006, 0.0), (-0.004, 0.035)]
    parts.append(prism(flame_poly, 0.006, (0, -0.042, -0.33), emb, bevel=0.0, scale=2.4))
    parts.append(rod((0, -0.042, -0.42), (0, -0.042, -0.55), 0.016, emb, verts=6))
    parts.append(torus(0.13, 0.008, (0, -0.042, -0.38), emb, rot=(math.pi / 2, 0, 0), verts=28, minor=4))
    export(join(parts, "banner"), "banner")


JOBS = {"knight": knight, "shieldmaiden": shieldmaiden, "mage": mage, "ranger": ranger, "ghost": ghost, "grunt": grunt, "imp": imp, "sorcerer": sorcerer, "skeleton": skeleton, "deathshade": deathshade,
        "throw_axe": throw_axe, "throw_sword": throw_sword, "fireball": fireball, "imp_fire": imp_fire, "arrow": arrow,
        "gen_bones": gen_bones, "gen_hut": gen_hut, "gen_brazier": gen_brazier,
        "door": door, "key": key, "chest": chest, "gold_pile": gold_pile, "food_ham": food_ham, "food_bowl": food_bowl,
        "food_cider": food_cider, "potion": potion, "amulet": amulet, "exit": exit_tile, "torch_wall": torch_wall,
        "pillar": pillar, "rubble": rubble, "barrel": barrel, "bones_decor": bones_decor, "cobweb": cobweb,
        "banner": banner}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
