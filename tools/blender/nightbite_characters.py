"""Nightbite (game 12) characters: the hero (a round glowing firefly with a clamshell mouth) and the spook (a floating
lantern-jellyfish, recoloured per chaser). Each has a small armature; actions are keyed with the Rig of
blastyard_bombers.py and exported as one glTF animation per action.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/nightbite_characters.py -- godot/games/nightbite/art/models [name ...]
One maze cell = 1 unit, the front faces -Y (the game turns the models toward their movement), origin on the ground
at the cell centre, 30 fps.

hero.glb   armature "hero_rig", skinned mesh "hero". Materials: "hero_glow" (the amber body, emissive), "hero_back",
           "hero_tail" (the lantern tail), "hero_wing", "hero_mouth", "hero_eye", "hero_pupil", "hero_spark" ...
           Animations: chomp (loop, 0.27 s), idle (loop, 1.6 s), die (one-shot, 1.1 s: spins, swells, pops into
           eight sparks; the last frame shows nothing).
spook.glb  armature "spook_rig" with the skinned mesh "body" (material "team_main", light grey: the game recolours
           it per chaser and deep blue when scared; set the emission colour too, it glows) and, on the bone "face",
           the nodes "eye_l" and "eye_r" (the whites, "spook_eye"), each with a child "pupil_l" / "pupil_r"
           ("spook_pupil"). The eyes do not belong to the body: hide "body" and the eyes stay (eaten spooks).
           Shift the pupils within about 0.035 of their rest position to look around.
           Animations: float (loop, 1.33 s), scared (loop, 0.4 s), eaten (one-shot, 0.43 s: the body swells, flattens
           and vanishes; the eyes stay).
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, prism, reset, flatten, R90
from blastyard_bombers import Rig, merge, mirror, limb, FPS


def aim(o, d, up_axis=(0, -1, 0)):
    """Turns an object (built facing -Y around its location) so its -Y axis points along d."""
    q = Vector(up_axis).rotation_difference(Vector(d).normalized())
    loc = o.location.copy()
    o.data.transform(Matrix.Translation(-loc))
    o.data.transform(q.to_matrix().to_4x4())
    o.data.transform(Matrix.Translation(loc))
    return o


def blob(r, loc, material, scale, d, segs=12, rings=8):
    """A sphere squashed by `scale` (y is the depth) and turned to face d."""
    o = sphere(r, (0, 0, 0), material, scale=scale, segs=segs, rings=rings)
    q = Vector((0, -1, 0)).rotation_difference(Vector(d).normalized())
    o.data.transform(q.to_matrix().to_4x4())
    o.data.transform(Matrix.Translation(Vector(loc)))
    return o


def shell_half(c, r, scale, zcut, upper, shell, cap, segs=24, rings=16, paint=None):
    """Half of a squashed sphere cut at z = zcut; the cut is closed with a `cap` face (the inside of the mouth).
    paint(normal) -> material index (0 shell, 1 cap, 2.. extra) for the shell faces."""
    me = bpy.data.meshes.new("half")
    me.materials.append(shell)
    me.materials.append(cap)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal(Vector(scale)).to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zcut), plane_no=(0, 0, 1),
                           clear_inner=upper, clear_outer=not upper)
    edges = [e for e in bm.edges if e.is_boundary]
    res = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    capf = res["faces"]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.material_index = 0
        if paint:
            f.material_index = paint(f.normal, f.calc_center_median())
    for f in capf:
        f.material_index = 1
        f.smooth = False
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("half", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def spark_shape(loc, material):
    """A small four-pointed star (three crossed spindles)."""
    parts = []
    for ax in ((0.05, 0, 0), (0, 0.05, 0), (0, 0, 0.05)):
        a = Vector(loc) - Vector(ax)
        b = Vector(loc) + Vector(ax)
        parts.append(rod(a, Vector(loc), 0.0, material, r2=0.022, verts=4))
        parts.append(rod(Vector(loc), b, 0.022, material, r2=0.0, verts=4))
    return parts


# ------------------------------------------------------------------ hero

C = Vector((0, 0, 0.34))   # body centre
R = 0.29
SC = (1.0, 1.02, 0.95)
ZCUT = 0.315               # the mouth line
HINGE = Vector((0, 0.2, ZCUT))
SPARK_C = Vector((0, 0, 0.19))
SPARKS = 8


def hero():
    reset()
    glow = mat("hero_glow", (1.0, 0.6, 0.16), 0.35, coat=0.8, emit=2.8, emit_color=(1.0, 0.46, 0.06))
    back = mat("hero_back", (0.9, 0.3, 0.05), 0.25, coat=1.0, emit=1.6, emit_color=(1.0, 0.28, 0.04))
    mouth = mat("hero_mouth", (0.3, 0.02, 0.05), 0.5, emit=0.3, emit_color=(0.6, 0.05, 0.1))
    tongue = mat("hero_tongue", (1.0, 0.35, 0.42), 0.4, emit=0.6)
    tooth = mat("hero_tooth", (1.0, 0.97, 0.9), 0.3, emit=0.4)
    eye = mat("hero_eye", (1.0, 0.98, 0.94), 0.25, coat=0.8, emit=0.5)
    pupil = mat("hero_pupil", (0.03, 0.02, 0.06), 0.15, coat=1.0)
    shine = mat("hero_shine", (1.0, 1.0, 1.0), 0.2, emit=4.0)
    dark = mat("hero_dark", (0.16, 0.07, 0.03), 0.4, coat=0.6)
    tail = mat("hero_tail", (1.0, 0.86, 0.35), 0.3, emit=6.0)
    wing = mat("hero_wing", (0.55, 0.9, 1.0), 0.2, coat=0.6, emit=2.2, emit_color=(0.35, 0.8, 1.0))
    spark = mat("hero_spark", (1.0, 0.8, 0.4), 0.3, emit=10.0)

    B = {"root": ((0, 0, 0), (0, 0, 0.1), None),
         "body": ((0, 0, 0.1), (0, 0, ZCUT), "root"),
         "head": (tuple(HINGE), (0, -0.1, ZCUT), "body"),
         "tail": ((0, 0.24, 0.3), (0, 0.5, 0.33), "body")}
    for s, side in ((1, "L"), (-1, "R")):
        B["wing." + side] = ((0.08 * s, 0.12, 0.56), (0.4 * s, 0.3, 0.62), "head")
        B["antenna." + side] = ((0.07 * s, -0.14, 0.58), (0.19 * s, -0.3, 0.8), "head")
    for k in range(SPARKS):
        a = 2 * math.pi * k / SPARKS
        B["spark%d" % k] = (tuple(SPARK_C), tuple(SPARK_C + Vector((math.cos(a), math.sin(a), 0.3)) * 0.05), "root")
    rig = Rig(B)

    # the body: two halves of a glowing ball; the upper one (the head) hinges open at the back
    def paint_top(n, p):
        return 2 if (n.y > 0.25 and n.z > -0.1) else 0   # a darker back plate: the front and face stay bright
    top = shell_half(C, R, SC, ZCUT, True, glow, mouth, paint=paint_top)
    top.data.materials.append(back)
    bot = shell_half(C, R, SC, ZCUT, False, glow, mouth)
    for o in (top, bot):
        K.select(o)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
    rig.rigid("body", bot,
              sphere(0.1, (0, -0.1, ZCUT + 0.005), tongue, scale=(1.0, 1.2, 0.18), segs=12, rings=6))
    rig.rigid("head", top)
    for s in (-1, 1):
        rig.rigid("head", rod((s * 0.09, -0.235, ZCUT + 0.002), (s * 0.085, -0.225, ZCUT - 0.05), 0.024, tooth,
                              r2=0.0, verts=6))
    # big eyes high on the front of the head (they must read from above whatever the heading)
    for s in (-1, 1):
        d = Vector((0.42 * s, -0.74, 0.52)).normalized()
        p = C + Vector((d.x * R * SC[0], d.y * R * SC[1], d.z * R * SC[2])) * 0.97
        rig.rigid("head",
                  blob(0.118, p, eye, (1.0, 0.6, 1.1), d, segs=16, rings=10),
                  blob(0.064, p + d * 0.058 + Vector((0, -0.01, -0.012)), pupil, (1.0, 0.5, 1.15), d, segs=12,
                       rings=8),
                  sphere(0.021, p + d * 0.09 + Vector((-0.02 * s + 0.02, 0, 0.03)), shine, segs=8, rings=5))
    # antennae with glowing bulbs
    for s, side in ((1, "L"), (-1, "R")):
        pts = [(0.06 * s, -0.12, 0.56), (0.1 * s, -0.17, 0.68), (0.15 * s, -0.24, 0.76), (0.19 * s, -0.31, 0.8)]
        rig.smooth(["head", "antenna." + side], limb(pts, [0.018, 0.016, 0.014, 0.012], dark, verts=6, per=2),
                   power=6)
        rig.rigid("antenna." + side, sphere(0.045, (0.2 * s, -0.33, 0.81), tail, segs=10, rings=6))
    # wings: a pair per side, pale cyan against the amber
    for s, side in ((1, "L"), (-1, "R")):
        for (dx, dy, dz), ln, wd in (((0.86, 0.46, 0.2), 0.34, 0.15), ((0.55, 0.83, 0.1), 0.24, 0.11)):
            me = bpy.data.meshes.new("wing")
            bm = bmesh.new()
            N = 14
            ring = [bm.verts.new((ln / 2 + math.cos(2 * math.pi * k / N) * ln / 2,
                                  math.sin(2 * math.pi * k / N) * wd / 2 * (1 - 0.25 * math.cos(2 * math.pi * k / N)),
                                  0)) for k in range(N)]
            bm.faces.new(ring)
            bm.to_mesh(me)
            bm.free()
            o = bpy.data.objects.new("wing", me)
            bpy.context.scene.collection.objects.link(o)
            d = Vector((dx * s, dy, dz)).normalized()
            q = Vector((1, 0, 0)).rotation_difference(d)
            o.data.transform(q.to_matrix().to_4x4())
            o.data.transform(Matrix.Translation(Vector((0.07 * s, 0.1, 0.57))))
            K.select(o)
            sol = o.modifiers.new("s", "SOLIDIFY")
            sol.thickness = 0.014
            sol.offset = 0
            bpy.ops.object.modifier_apply(modifier=sol.name)
            K.finish(o, wing, smooth=50)
            rig.rigid("wing." + side, o)
            rig.rigid("wing." + side, rod(Vector((0.07 * s, 0.1, 0.575)), Vector((0.07 * s, 0.1, 0.575)) + d * ln * 0.85,
                                          0.008, dark, verts=4))
    # the lantern tail
    rig.rigid("tail", sphere(0.14, (0, 0.34, 0.31), tail, scale=(0.9, 1.15, 0.85), segs=16, rings=10),
              torus(0.1, 0.022, (0, 0.235, 0.32), dark, rot=(R90 - 0.2, 0, 0), verts=14, minor=4))
    # sparks for the death pop, hidden inside the lower half until then
    for k in range(SPARKS):
        rig.rigid("spark%d" % k, *spark_shape(SPARK_C, spark))
    rig.build("hero")

    # ---- actions
    L = mirror

    def flutter(t, amp=28):
        return L({"wing.L": (0, -amp * t, 0)})

    idle = {}
    for i in range(13):
        f = i * 4
        a = 2 * math.pi * f / 48
        idle[f] = merge(flutter(1 if i % 2 == 0 else -0.4, 22),
                        L({"antenna.L": (8 * math.sin(a), 0, 4 * math.cos(a))}),
                        {"@root": (0, 0, 0.03 * math.sin(a)), "head": (-4 - 3 * math.sin(a), 0, 0),
                         "tail": (6 * math.sin(a + 1), 0, 5 * math.cos(a))})
    rig.action("idle", idle, loop=True)

    closed = merge(flutter(1), L({"antenna.L": (10, 0, 0)}),
                   {"head": (3, 0, 0), "%body": (1.04, 1.04, 0.95), "tail": (-6, 0, 0)})
    opened = merge(flutter(-0.6), L({"antenna.L": (-14, 0, 0)}),
                   {"head": (-40, 0, 0), "body": (8, 0, 0), "%body": (0.98, 0.98, 1.04), "tail": (8, 0, 0),
                    "@root": (0, 0, 0.02)})
    rig.action("chomp", {0: closed, 4: opened, 8: closed}, loop=True)

    def sparks(r, s, lift=0.0):
        p = {}
        for k in range(SPARKS):
            a = 2 * math.pi * k / SPARKS
            p["@spark%d" % k] = (math.cos(a) * r, math.sin(a) * r, lift + (0.12 if k % 2 else 0.0) * r)
            p["%%spark%d" % k] = s
        return p
    rig.action("die", {
        0: {},
        5: merge(flutter(1, 40), {"head": (-45, 0, 0), "@root": (0, 0, 0.08), "%body": (1.08, 1.08, 1.0)}),
        10: merge(flutter(-1, 40), {"root": (0, 0, 200), "head": (-20, 0, 0), "@root": (0, 0, 0.16)}),
        15: merge(flutter(1, 40), {"root": (0, 0, 430), "head": (-8, 0, 0), "@root": (0, 0, 0.2),
                                   "%body": (1.22, 1.22, 1.22)}),
        19: merge({"root": (0, 0, 560), "@root": (0, 0, 0.2), "%body": (1.4, 1.4, 1.4)}, sparks(0.02, 1.0, 0.15)),
        22: merge({"root": (0, 0, 600), "@root": (0, 0, 0.2), "%body": (0.02, 0.02, 0.02)}, sparks(0.4, 2.4, 0.15)),
        27: merge({"root": (0, 0, 630), "@root": (0, 0, 0.2), "%body": (0.0, 0.0, 0.0)}, sparks(0.72, 1.6, 0.1)),
        33: merge({"root": (0, 0, 645), "@root": (0, 0, 0.2), "%body": (0.0, 0.0, 0.0)}, sparks(0.9, 0.0, 0.0)),
    })
    rig.export("hero")


# ------------------------------------------------------------------ spook

BELL_C = Vector((0, 0, 0.46))
TENT = 6


def tent_dir(k):
    a = 2 * math.pi * k / TENT          # 0, 60, ... : the front (-Y, 270) falls between two tentacles
    return Vector((math.cos(a), math.sin(a), 0))


def about(axis, deg):
    """World-axis Euler (degrees, XYZ) of a rotation of `deg` about `axis`."""
    e = Matrix.Rotation(math.radians(deg), 3, Vector(axis)).to_euler("XYZ")
    return tuple(math.degrees(x) for x in e)


def flare(k, deg):
    """Rotates tentacle k outward and up by deg (negative: down and under)."""
    d = tent_dir(k)
    return about((-d.y, d.x, 0), -deg)


def spook():
    reset()
    TM = mat("team_main", (0.82, 0.82, 0.84), 0.3, coat=0.8, emit=0.9, emit_color=(0.82, 0.82, 0.84))
    dots = mat("spook_glow", (1.0, 1.0, 1.0), 0.3, emit=3.0)
    white = mat("spook_eye", (1.0, 1.0, 1.0), 0.25, coat=0.8, emit=0.6)
    pupil_m = mat("spook_pupil", (0.02, 0.03, 0.12), 0.15, coat=1.0)
    shine = mat("spook_shine", (1.0, 1.0, 1.0), 0.2, emit=4.0)

    B = {"root": ((0, 0, 0), (0, 0, 0.1), None),
         "bell": ((0, 0, 0.26), (0, 0, 0.72), "root"),
         "wisp": ((0, 0.02, 0.72), (0, 0.14, 0.86), "bell"),
         "face": ((0, -0.1, 0.5), (0, -0.3, 0.5), "root")}
    for k in range(TENT):
        d = tent_dir(k)
        mid = d * 0.33 + Vector((0, 0, 0.14))
        B["ten%d" % k] = (tuple(d * 0.2 + Vector((0, 0, 0.26))), tuple(mid), "bell")
        B["tip%d" % k] = (tuple(mid), tuple(d * 0.42 + Vector((0, 0, 0.17))), "ten%d" % k)
    rig = Rig(B)

    # the bell: a lathe with a flared, scalloped hem and a closed underside
    me = bpy.data.meshes.new("bell")
    bm = bmesh.new()
    S = 24
    prof = [(0.1, 0.705), (0.18, 0.68), (0.24, 0.63), (0.28, 0.56), (0.3, 0.48), (0.305, 0.4), (0.31, 0.33),
            (0.33, 0.28), (0.36, 0.24)]
    rings = []
    for r, z in prof:
        ring = []
        for k in range(S):
            a = 2 * math.pi * k / S
            lobe = math.cos(TENT * a + math.pi) if z < 0.3 else 0.0   # scallops between the tentacles
            rr = r + (0.02 * lobe if z < 0.26 else 0.0)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z + (0.035 * lobe if z < 0.26 else 0))))
        rings.append(ring)
    topv = bm.verts.new((0, 0, 0.715))
    for k in range(S):
        bm.faces.new((topv, rings[0][k], rings[0][(k + 1) % S]))
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(S):
            bm.faces.new((r0[k], r1[k], r1[(k + 1) % S], r0[(k + 1) % S]))
    inner = [bm.verts.new((v.co.x * 0.8, v.co.y * 0.8, v.co.z + 0.03)) for v in rings[-1]]
    for k in range(S):
        bm.faces.new((rings[-1][k], inner[k], inner[(k + 1) % S], rings[-1][(k + 1) % S]))
    under = bm.verts.new((0, 0, 0.3))
    for k in range(S):
        bm.faces.new((inner[k], under, inner[(k + 1) % S]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    bell = bpy.data.objects.new("bell", me)
    bpy.context.scene.collection.objects.link(bell)
    K.finish(bell, TM, smooth=80)

    def bell_w(p):
        out = {"bell": 1.0}
        hem = max(0.0, min(1.0, (0.31 - p.z) / 0.08))
        if hem > 0:
            ang = math.atan2(p.y, p.x)
            ws = {}
            for k in range(TENT):
                c = max(0.0, math.cos(ang - 2 * math.pi * k / TENT))
                ws["ten%d" % k] = c ** 4
            tot = sum(ws.values()) + 1e-6
            out["bell"] = 1 - hem + 1e-4
            for n, w in ws.items():
                out[n] = hem * w / tot + 1e-4
        return out
    body = [bell]
    # glowing spots around the back and sides of the bell (lantern windows)
    for k in range(5):
        a = math.radians(-20 + k * 55)   # from front-right round the back to front-left, avoiding the face
        d = Vector((math.cos(a), math.sin(a), 0.25)).normalized()
        body.append(blob(0.04, BELL_C + Vector((d.x * 0.3, d.y * 0.3, 0.02)), dots, (1, 0.35, 1), d, segs=8, rings=5))
    rig.custom(bell_w, *body)
    # the wisp: a curled flame on the crown
    rig.smooth(["bell", "wisp"], limb([(0, 0.0, 0.69), (0, 0.03, 0.78), (0, 0.1, 0.84), (0, 0.16, 0.82),
                                       (0, 0.17, 0.77)], [0.05, 0.04, 0.028, 0.018, 0.01], TM, verts=8, per=3,
                                      caps=True), power=6)
    # tentacles: out, down and curling back up
    for k in range(TENT):
        d = tent_dir(k)
        pts = [d * 0.17 + Vector((0, 0, 0.3)), d * 0.26 + Vector((0, 0, 0.2)), d * 0.34 + Vector((0, 0, 0.13)),
               d * 0.41 + Vector((0, 0, 0.13)), d * 0.43 + Vector((0, 0, 0.19))]
        rig.smooth(["bell", "ten%d" % k, "tip%d" % k],
                   limb(pts, [0.05, 0.042, 0.032, 0.022, 0.012], TM, verts=8, per=2, caps=True))
    rig.build("body")
    rig.arm.name = "spook_rig"
    rig.arm.data.name = "spook_rig"

    # eyes: separate nodes on the bone "face" (they survive when the body is hidden)
    eyes = []
    for s, side in ((1, "l"), (-1, "r")):
        d = Vector((0.36 * s, -0.8, 0.45)).normalized()
        p = Vector((0.12 * s, -0.235, 0.53))
        white_o = blob(0.112, (0, 0, 0), white, (1.0, 0.6, 1.2), d, segs=16, rings=10)
        pp = d * 0.056 + Vector((0, 0, -0.01))
        pup = [blob(0.06, pp, pupil_m, (1.0, 0.5, 1.15), d, segs=12, rings=8),
               sphere(0.016, pp + d * 0.025 + Vector((0.018, 0, 0.022)), shine, segs=8, rings=5)]
        pup = K.join(pup, "pupil_" + side, pivot=pp)
        white_o.name = "eye_" + side
        white_o.data.name = "eye_" + side
        for o in (white_o, pup):
            o.location += p
        pup.location = p + pp
        K.select(white_o)
        pup.parent = white_o
        pup.matrix_parent_inverse = white_o.matrix_world.inverted()
        eyes += [white_o, pup]
        mw = white_o.matrix_world.copy()
        white_o.parent = rig.arm
        white_o.parent_type = "BONE"
        white_o.parent_bone = "face"
        bpy.context.view_layer.update()
        white_o.matrix_world = mw

    L = mirror

    def ten_pose(ph, amp, curl, base=0.0):
        p = {}
        for k in range(TENT):
            w = math.sin(ph + k * math.pi / 3)
            p["ten%d" % k] = flare(k, base + amp * w)
            p["tip%d" % k] = flare(k, curl * math.sin(ph + k * math.pi / 3 - 1.0) + base * 0.8)
        return p

    fl = {}
    for i in range(9):
        a = 2 * math.pi * i / 8
        fl[i * 5] = merge(ten_pose(a, 16, 26),
                          {"@root": (0, 0, 0.035 * math.sin(a)), "%bell": (1 + 0.045 * math.cos(a), 1 + 0.045 *
                                                                            math.cos(a), 1 - 0.05 * math.cos(a)),
                           "wisp": (14 * math.sin(a - 0.8), 0, 8 * math.cos(a)),
                           "@face": (0, 0, -0.012 * math.cos(a))})
    rig.action("float", fl, loop=True)

    sc = {}
    for i in range(7):
        j = 1 if i % 2 == 0 else -1
        sc[i * 2] = merge(ten_pose(i * 2.1, 8, 14, base=-18),
                          {"bell": (0, 0, 5 * j), "@root": (0.012 * j, 0, 0.01 * (i % 3)),
                           "%bell": (1.06, 1.06, 0.9), "wisp": (35, 0, 12 * j), "@face": (0.012 * j, 0.0, -0.02)})
    sc[12] = sc[0]
    rig.action("scared", sc, loop=True)

    rig.action("eaten", {0: {}, 4: merge(ten_pose(0, 0, 0, base=25), {"%bell": (1.25, 1.25, 1.2), "@face": (0, 0, 0.04)}),
                         8: merge(ten_pose(0, 0, 0, base=40), {"%bell": (1.6, 1.6, 0.12), "@face": (0, 0, 0.06)}),
                         13: {"%bell": (0.0, 0.0, 0.0), "@face": (0, 0, 0.05)}})

    # export: the armature, the skinned body and the eye nodes
    K.deselect()
    for o in [rig.arm, rig.mesh] + eyes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig.arm
    bpy.context.scene.frame_start = 0
    bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, "spook.glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_frame_step=1)
    print("exported spook      %5d tris (+ eyes %d)  anims: %s" % (K.tris(rig.mesh), sum(K.tris(o) for o in eyes),
          ", ".join("%s %.2fs" % (k, v) for k, v in rig.lengths.items())))
    reset()


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for n, fn in (("hero", hero), ("spook", spook)):
        if not args[1:] or n in args[1:]:
            fn()
