"""Tumbletop (game 22) models: Pip the hero, the three bouncing balls, the serpent (head and neck, plus a body
segment), the imp and the rainbow cloud-disc. Original designs (Pip is our own creature: an orange fuzzball with a
trumpet snout, a curl on top, freckles, stubby arms and a pom-pom tail). Deterministic; output CC BY-SA 4.0;
provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/tumbletop_models.py -- godot/games/tumbletop/art/models [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (Rig, merge,
mirror), hopline_models.py (TurnRig, ell, hemi) and mossfolk_models.py (lumpy). 30 fps.

Axes: built in Blender facing -Y and exported turned 180 degrees, so every character faces Godot -Z (forward);
+Y is up. Game size (node scale 1). Origins at the feet / the bottom unless noted. Animations marked * are seamless
loops: set their loop mode in the game. Emissive materials all have "glow" in their names.

pip.glb      armature "pip_rig" (root, body, top, snout, eye.L/R, tuft, arm.L/R, foot.L/R, tail), mesh "pip":
             0.60 tall to the curl (0.53 to the crown), 0.49 long (tail to snout tip, the snout reaching z = -0.46).
             Materials pip_fur, pip_fur_light, pip_snout, pip_rim, pip_nostril, pip_freckle, pip_cheek, pip_feet,
             pip_eye_white, pip_iris, pip_pupil, pip_eye_glow (the catch lights).
             Animations:  idle* 2 s (breathing, a snout wiggle, one blink, the curl sways)
                          hop   0.4 s: crouch (f2), stretch (f4), tuck (f6-7), feet down (f8), land squash at 0.32 s
                                (f10), recovered (f12). Play it on the hop event; it ends at rest.
                          fall* 0.5 s: arms flailing, feet kicking, eyes wide
                          cheer* 1 s: two little hops, arms up
                          die   1.5 s: a jolt, a dizzy wobble, eyes shut to slits, slumps (holds the last frame)
red.glb, green.glb, purple.glb   one mesh each (named like the file), no animation, origin at the bottom; the game
             does not turn the balls, so their faces look along Godot (+X, +Z), towards the camera's diagonal:
             red    0.44 across: glossy candy red, a scowl (two slanted eye slits and a brow), red_body, red_eye,
                    red_brow, red_shine
             green  0.44 across: glowing lime (green_glow) with a tennis-ball seam (green_seam_glow) and a sleepy
                    smile (green_face)
             purple 0.46 wide, 0.50 tall (an egg): purple_shell with purple_speckle spots and a glowing zigzag crack
                    (purple_crack_glow) with two eyes peeking out (purple_eye_glow)
serpent.glb  armature "serpent_rig" (root, neck1, neck2, head, jaw, tongue), mesh "serpent": an S-shaped neck rising
             from behind (its base centre (0, 0.2, +0.17), radius 0.14, where the first body segment goes) to the
             head, whose centre is 0.62 up. Big glowing yellow slit eyes (serpent_eye_glow) under heavy lids, a
             magenta crest, fangs, a forked tongue (hidden unless hissing). serpent_skin, serpent_belly,
             serpent_spot, serpent_crest, serpent_mouth, serpent_fang, serpent_tongue, serpent_pupil.
             Animation hiss* 1.2 s: the neck sways, the jaw opens, the tongue flicks twice.
serpent_segment.glb  one mesh "serpent_segment": a body ball of radius 0.17 with its origin at the CENTRE (the view
             places it on the trail point): serpent_skin with serpent_spot patches on top and a serpent_belly band.
imp.glb      armature "imp_rig" (root, body, head, ear.L/R, arm.L/R, foot.L/R, tail), mesh "imp": a green gremlin
             0.40 tall (to the ear tips 0.42), 0.46 wide across the ears. imp_skin, imp_belly, imp_ear, imp_horn,
             imp_eye_glow (yellow eyes), imp_pupil, imp_mouth, imp_tooth, imp_claw.
             Animation bounce* 0.6 s: squash, stretch, a tuck with the arms and ears up, stretch, squash.
disc.glb     one mesh "disc", 0.80 across, origin at the centre: a cushion of cloud puffs (disc_cloud_glow, top at
             +0.10) inside six concentric rainbow rings (disc_band_0_glow red outside .. disc_band_5_glow violet
             inside, at about 0) over a pale underside plate (disc_under_glow, down to -0.045). No animation (the
             game spins it).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, export, reset, R90
from blastyard_bombers import merge, mirror, smoothstep
from hopline_models import TurnRig, ell, hemi
from mossfolk_models import lumpy

FPS = 30


def cone(base, tip, r, material, verts=5):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


def fib_dirs(n):
    """n directions spread evenly over the sphere (a Fibonacci lattice)."""
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        yield Vector((r * math.cos(i * ga), r * math.sin(i * ga), z))


# ------------------------------------------------------------------ Pip

PC = Vector((0, 0, 0.29))       # body centre
PR = Vector((0.225, 0.215, 0.22))  # body radii


def body_point(d):
    d = d.normalized()
    k = 1.0 / math.sqrt((d.x / PR.x) ** 2 + (d.y / PR.y) ** 2 + (d.z / PR.z) ** 2)
    return PC + d * k


def pip():
    reset()
    fur = mat("pip_fur", (1.0, 0.3, 0.02), 0.72, coat=0.15)
    fur_l = mat("pip_fur_light", (1.0, 0.66, 0.36), 0.8)
    snout_m = mat("pip_snout", (1.0, 0.55, 0.24), 0.45, coat=0.4)
    rim = mat("pip_rim", (0.55, 0.16, 0.05), 0.5, coat=0.3)
    nostril = mat("pip_nostril", (0.08, 0.02, 0.02), 0.6)
    freckle = mat("pip_freckle", (0.72, 0.25, 0.06), 0.7)
    cheek = mat("pip_cheek", (1.0, 0.45, 0.45), 0.6)
    feet_m = mat("pip_feet", (0.62, 0.22, 0.05), 0.55, coat=0.3)
    white = mat("pip_eye_white", (0.98, 0.97, 0.95), 0.25, coat=0.8)
    iris = mat("pip_iris", (0.12, 0.32, 0.55), 0.3, coat=1.0)
    pupil = mat("pip_pupil", (0.02, 0.02, 0.03), 0.2, coat=1.0)
    shine = mat("pip_eye_glow", (1.0, 1.0, 1.0), 0.1, emit=4.0)

    bones = {"root": ((0, 0, 0), (0, 0, 0.05), None),
             "body": ((0, 0, 0.07), (0, 0, 0.25), "root"),
             "top": ((0, 0, 0.25), (0, 0, 0.48), "body"),
             "snout": ((0, -0.18, 0.27), (0, -0.44, 0.245), "top"),
             "eye.L": ((0.088, -0.17, 0.365), (0.088, -0.26, 0.365), "top"),
             "eye.R": ((-0.088, -0.17, 0.365), (-0.088, -0.26, 0.365), "top"),
             "tuft": ((0, 0.0, 0.5), (0, 0.02, 0.6), "top"),
             "arm.L": ((0.19, -0.02, 0.25), (0.26, -0.05, 0.2), "body"),
             "arm.R": ((-0.19, -0.02, 0.25), (-0.26, -0.05, 0.2), "body"),
             "foot.L": ((0.095, -0.01, 0.04), (0.095, -0.12, 0.03), "root"),
             "foot.R": ((-0.095, -0.01, 0.04), (-0.095, -0.12, 0.03), "root"),
             "tail": ((0, 0.19, 0.19), (0, 0.27, 0.23), "body")}
    rig = TurnRig(bones, 180)

    def w_body(p):
        t = smoothstep(0.2, 0.38, p.z)
        return {"body": 1 - t + 1e-4, "top": t + 1e-4}

    # the body: an egg of fur with tufts all over (combed back and down), a cream belly and muzzle
    body = ell(PC, PR, fur, segs=28, rings=18)
    rnd = random.Random(7)
    tufts = []
    for d in fib_dirs(420):
        face = d.y < -0.55 and d.z > -0.15 and abs(d.x) < 0.75   # keep the eyes and the snout root clear
        if face or d.z < -0.8:
            continue
        p = body_point(d) - d * 0.01
        flow = (d * 0.55 + Vector((0, 0.5, -0.3))).normalized()   # combed back and down, lying on the body
        ln = rnd.uniform(0.03, 0.045) * (0.7 if d.z < -0.3 else 1.0)
        tip = p + flow * ln + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.008
        tufts.append(cone(p, tip, rnd.uniform(0.022, 0.03), fur if d.y > -0.45 or d.z > 0.1 else fur_l, verts=5))
    belly = ell((0, -0.145, 0.2), (0.13, 0.08, 0.12), fur_l, segs=18, rings=10)
    for d in fib_dirs(60):  # tufts on the belly patch too, so its edge is soft
        if d.y > -0.3:
            continue
        p = Vector((0, -0.145, 0.2)) + Vector((d.x * 0.13, d.y * 0.08, d.z * 0.12))
        if p.z < 0.1:
            continue
        tufts.append(cone(p, p + (d + Vector((0, 0.2, -0.4))).normalized() * 0.02, 0.022, fur_l, verts=5))
    rig.custom(w_body, body, belly, tufts)
    # cheeks and brows
    for s in (-1, 1):
        rig.rigid("top", ell((s * 0.145, -0.165, 0.275), (0.045, 0.02, 0.03), cheek, yaw=-s * 38, segs=12, rings=6))
        rig.rigid("top", ell((s * 0.09, -0.19, 0.455), (0.05, 0.016, 0.016), feet_m, roll=-s * 14, yaw=-s * 18,
                             segs=10, rings=6))

    # eyes: big, set close above the snout, looking forward
    for s, side in ((1, "L"), (-1, "R")):
        c = Vector((s * 0.088, -0.17, 0.365))
        parts = [ell(c, (0.072, 0.06, 0.085), white, yaw=-s * 12, segs=18, rings=12),
                 ell(c + Vector((-s * 0.004, -0.052, -0.004)), (0.042, 0.018, 0.05), iris, yaw=-s * 12, segs=14, rings=8),
                 ell(c + Vector((-s * 0.005, -0.064, -0.006)), (0.024, 0.01, 0.03), pupil, yaw=-s * 12, segs=10, rings=6),
                 sphere(0.011, c + Vector((s * 0.012, -0.072, 0.022)), shine, segs=6, rings=4)]
        rig.rigid("eye." + side, parts)

    # the trumpet snout: a tube curving forward and a little down, flaring into a rimmed bell
    pts = [(0, -0.12, 0.29), (0, -0.2, 0.268), (0, -0.28, 0.248), (0, -0.35, 0.238), (0, -0.405, 0.244),
           (0, -0.435, 0.254)]
    rad = [0.085, 0.066, 0.052, 0.048, 0.054, 0.066]
    sn = tube(pts, rad, snout_m, verts=16, caps=False, name="snout")
    end = Vector(pts[-1])
    axis = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
    ring = torus(0.064, 0.016, (0, 0, 0), rim, verts=20, minor=8)
    ring.data.transform(Matrix.Translation(end) @ axis.to_track_quat("Z", "Y").to_matrix().to_4x4())
    hole = ell((0, 0, 0), (0.052, 0.052, 0.012), nostril, segs=16, rings=6)
    hole.data.transform(Matrix.Translation(end - axis * 0.004) @ axis.to_track_quat("Z", "Y").to_matrix().to_4x4())
    frk = [sphere(0.008, (x, y, z), freckle, segs=6, rings=4)
           for x, y, z in ((-0.022, -0.25, 0.3), (0.018, -0.29, 0.29), (-0.006, -0.32, 0.285), (0.03, -0.235, 0.296))]

    def w_snout(p):
        t = smoothstep(-0.17, -0.3, p.y)
        return {"top": 1 - t + 1e-4, "snout": t + 1e-4}
    rig.custom(w_snout, sn, ring, hole, frk)

    # the curl on top: three flame tufts
    curl = [tube([(0, 0.02, 0.49), (0, 0.0, 0.55), (0, -0.04, 0.59), (0, -0.07, 0.585), (0, -0.07, 0.56)],
                 [0.03, 0.026, 0.02, 0.012, 0.006], fur, verts=8, caps=True, name="curl"),
            tube([(0.02, 0.03, 0.48), (0.045, 0.04, 0.53), (0.07, 0.03, 0.55)], [0.022, 0.014, 0.004], fur, verts=6),
            tube([(-0.02, 0.03, 0.48), (-0.05, 0.045, 0.52), (-0.07, 0.04, 0.535)], [0.02, 0.012, 0.004], fur, verts=6)]
    rig.rigid("tuft", curl)

    # stubby arms: fuzzy mitts at the sides
    for s, side in ((1, "L"), (-1, "R")):
        a = ell((s * 0.235, -0.04, 0.215), (0.045, 0.05, 0.06), fur, roll=-s * 30, segs=12, rings=8)
        at = [cone(Vector((s * 0.235, -0.04, 0.215)) + d * 0.04, Vector((s * 0.235, -0.04, 0.215)) + d * 0.07, 0.016,
                   fur, verts=5) for d in fib_dirs(14) if d.x * s > -0.2]
        rig.rigid("arm." + side, a, at)

    # little feet with three toes, on short legs hidden in the fur
    for s, side in ((1, "L"), (-1, "R")):
        f = [ell((s * 0.095, -0.05, 0.035), (0.058, 0.085, 0.035), feet_m, segs=14, rings=8)]
        f += [sphere(0.022, (s * 0.095 + dx, -0.125, 0.03), feet_m, segs=8, rings=6) for dx in (-0.03, 0.0, 0.03)]
        leg = rod((s * 0.095, -0.01, 0.13), (s * 0.095, -0.02, 0.04), 0.04, fur, verts=10)
        rig.rigid("foot." + side, f)

        def w_leg(p, side=side):
            t = smoothstep(0.06, 0.12, p.z)
            return {"foot." + side: 1 - t + 1e-4, "body": t + 1e-4}
        rig.custom(w_leg, leg)

    # a pom-pom tail
    tl = [ell((0, 0.225, 0.2), (0.045, 0.045, 0.045), fur_l, segs=10, rings=6)]
    tl += [cone(Vector((0, 0.225, 0.2)) + d * 0.035, Vector((0, 0.225, 0.2)) + d * 0.068, 0.018, fur_l, verts=5)
           for d in fib_dirs(22) if d.y > -0.3]
    rig.rigid("tail", tl)

    rig.build("pip")

    def pose(**kw):
        return {k.replace("_L", ".L").replace("_R", ".R"): v for k, v in kw.items()}

    rest = {}
    blink = {"%eye.L": (1, 1, 0.08), "%eye.R": (1, 1, 0.08)}
    wide = {"%eye.L": (1.12, 1, 1.18), "%eye.R": (1.12, 1, 1.18)}

    # idle: breathing, a snout wiggle, a blink, the curl sways
    breathe_in = {"%body": (1.03, 1.03, 0.98), "top": (-2, 0, 0), "snout": (-4, 0, 3), "tuft": (0, -8, 0),
                  "tail": (0, 0, 10), **mirror({"arm.L": (0, 6, 0)})}
    breathe_out = {"%body": (0.99, 0.99, 1.02), "top": (1, 0, 0), "snout": (3, 0, -3), "tuft": (0, 8, 0),
                   "tail": (0, 0, -10), **mirror({"arm.L": (0, -4, 0)})}
    rig.action("idle", {0: rest, 15: breathe_in, 30: breathe_out, 38: merge(breathe_out, {"top": (0, 0, 6)}),
                        41: merge(breathe_out, blink, {"top": (0, 0, 6)}),
                        44: merge(breathe_out, {"top": (0, 0, 4)}), 52: breathe_in, 60: rest}, loop=True)

    # hop (0.4 s): crouch, stretch, tuck, feet down, land squash at 0.32 s, recover
    crouch = merge({"@body": (0, 0, -0.045), "%body": (1.16, 1.16, 0.8), "top": (8, 0, 0), "snout": (10, 0, 0)},
                   mirror({"arm.L": (0, -35, 0)}))
    stretch = merge({"@body": (0, 0, 0.03), "%body": (0.86, 0.86, 1.2), "top": (-8, 0, 0), "snout": (-14, 0, 0),
                     "tuft": (25, 0, 0), "tail": (30, 0, 0)},
                    mirror({"arm.L": (0, 40, 0), "foot.L": (-40, 0, 0), "@foot.L": (0, 0.02, -0.01)}), wide)
    tuck = merge({"@body": (0, 0, 0.0), "%body": (1.04, 1.04, 0.97), "top": (-4, 0, 0), "snout": (-8, 0, 0),
                  "tuft": (-15, 0, 0), "tail": (-20, 0, 0)},
                 mirror({"arm.L": (0, 55, 0), "foot.L": (35, 0, 0), "@foot.L": (0, -0.02, 0.07)}), wide)
    reach = merge({"%body": (0.95, 0.95, 1.06), "top": (4, 0, 0), "snout": (2, 0, 0), "tuft": (-20, 0, 0)},
                  mirror({"arm.L": (0, 30, 0), "foot.L": (-10, 0, 0), "@foot.L": (0, 0, 0.015)}))
    land = merge({"@body": (0, 0, -0.05), "%body": (1.2, 1.2, 0.76), "top": (6, 0, 0), "snout": (12, 0, 0),
                  "tuft": (30, 0, 0), "tail": (25, 0, 0)}, mirror({"arm.L": (0, -20, 0)}))
    rig.action("hop", {0: rest, 2: crouch, 4: stretch, 6: tuck, 7: tuck, 8: reach, 10: land, 12: rest})

    # fall: flailing arms, kicking feet, wide eyes, snout up
    def flail(k):
        a = k * math.pi / 2
        return merge({"%body": (0.94, 0.94, 1.1), "top": (-10, 0, 6 * math.sin(a)), "snout": (-22 + 6 * math.cos(a), 0, 0),
                      "tuft": (-30, 10 * math.sin(a), 0), "tail": (40, 0, 0)},
                     {"arm.L": (30 * math.sin(a), 70 + 25 * math.cos(a), 0),
                      "arm.R": (-30 * math.sin(a), -70 - 25 * math.cos(a), 0),
                      "foot.L": (-30 + 40 * math.sin(a), 0, 0), "foot.R": (-30 - 40 * math.sin(a), 0, 0),
                      "@foot.L": (0, 0, 0.03), "@foot.R": (0, 0, 0.03)}, wide)
    rig.action("fall", {0: flail(0), 4: flail(1), 8: flail(2), 11: flail(3), 15: flail(0)}, loop=True)

    # cheer: two little hops with the arms up
    def cheer_pose(h, sq, arm):
        return merge({"@root": (0, 0, h), "%body": (1 + sq, 1 + sq, 1 - 1.6 * sq), "top": (-6, 0, 0),
                      "snout": (-18, 0, 0), "tuft": (-10 + 60 * sq, 0, 0), "tail": (0, 0, 30 * h / 0.08)},
                     mirror({"arm.L": (0, arm, 0)}), {"%eye.L": (1, 1, 0.35), "%eye.R": (1, 1, 0.35)})
    rig.action("cheer", {0: cheer_pose(0, 0.1, 60), 5: cheer_pose(0.06, -0.06, 110), 8: cheer_pose(0.08, -0.02, 120),
                         12: cheer_pose(0.02, -0.04, 100), 15: cheer_pose(0, 0.12, 70), 20: cheer_pose(0.06, -0.06, 110),
                         23: cheer_pose(0.08, -0.02, 120), 27: cheer_pose(0.02, -0.04, 100), 30: cheer_pose(0, 0.1, 60)},
               loop=True)

    # die: a jolt, a dizzy wobble, eyes to slits, slumps
    shut = {"%eye.L": (1.1, 1, 0.2), "%eye.R": (1.1, 1, 0.2)}
    rig.action("die", {
        0: rest,
        3: merge({"%body": (0.85, 0.85, 1.25), "@body": (0, 0, 0.02), "snout": (-30, 0, 0), "tuft": (-40, 0, 0)},
                 mirror({"arm.L": (0, 80, 0)}), wide),
        8: merge({"%body": (1.15, 1.15, 0.85), "top": (0, 18, 10), "snout": (10, 0, 20)}, mirror({"arm.L": (0, 20, 0)}),
                 shut),
        14: merge({"top": (0, -20, -12), "snout": (8, 0, -25), "tuft": (0, -30, 0)}, mirror({"arm.L": (0, 10, 0)}), shut),
        20: merge({"top": (0, 16, 10), "snout": (10, 0, 20), "tuft": (0, 30, 0)}, shut),
        26: merge({"top": (0, -12, -8), "snout": (12, 0, -15), "tuft": (0, -20, 0)}, shut),
        34: merge({"@body": (0, 0, -0.07), "%body": (1.22, 1.22, 0.74), "top": (12, 8, 4),
                   "snout": (22, 0, 5), "tuft": (40, 0, 0)}, mirror({"arm.L": (0, -40, 0), "foot.L": (0, 20, 0)}), shut),
        39: merge({"@body": (0, 0, -0.055), "%body": (1.16, 1.16, 0.8), "top": (10, 6, 3),
                   "snout": (18, 0, 5), "tuft": (30, 0, 0)}, mirror({"arm.L": (0, -35, 0), "foot.L": (0, 20, 0)}), shut),
        45: merge({"@body": (0, 0, -0.065), "%body": (1.2, 1.2, 0.76), "top": (12, 7, 4),
                   "snout": (22, 0, 5), "tuft": (45, 0, 0)}, mirror({"arm.L": (0, -40, 0), "foot.L": (0, 20, 0)}), shut)})
    rig.save("pip")


# ------------------------------------------------------------------ the balls

def red():
    reset()
    body = mat("red_body", (0.85, 0.05, 0.04), 0.14, coat=1.0)
    eye = mat("red_eye", (0.12, 0.0, 0.02), 0.25, coat=1.0)
    brow = mat("red_brow", (0.45, 0.0, 0.02), 0.3, coat=0.8)
    shine = mat("red_shine", (1.0, 0.85, 0.8), 0.1, coat=1.0)
    c = Vector((0, 0, 0.22))
    parts = [sphere(0.22, c, body, segs=28, rings=16)]
    for s in (-1, 1):  # a scowl: slanted eye slits under a heavy brow ridge, set into the front of the ball
        e = ell((0, 0, 0), (0.042, 0.02, 0.026), eye, segs=12, rings=8, roll=-s * 18)
        e.data.transform(Matrix.Translation(c) @ Matrix.Rotation(math.radians(-s * 20), 4, "Z")
                         @ Matrix.Rotation(math.radians(-12), 4, "X") @ Matrix.Translation((0, -0.212, 0)))
        parts.append(e)
        g = sphere(0.007, (0, 0, 0), shine, segs=6, rings=4)
        g.data.transform(Matrix.Translation(c) @ Matrix.Rotation(math.radians(-s * 17), 4, "Z")
                         @ Matrix.Rotation(math.radians(-15), 4, "X") @ Matrix.Translation((0, -0.226, 0)))
        parts.append(g)
        b = ell((0, 0, 0), (0.058, 0.022, 0.016), brow, segs=12, rings=6, roll=s * 26)
        b.data.transform(Matrix.Translation(c) @ Matrix.Rotation(math.radians(-s * 22), 4, "Z")
                         @ Matrix.Rotation(math.radians(-27), 4, "X") @ Matrix.Translation((0, -0.212, 0)))
        parts.append(b)
    export(face_camera(join(parts, "red")), "red")


def green():
    reset()
    glow = mat("green_glow", (0.12, 0.8, 0.2), 0.2, coat=1.0, emit=1.4, emit_color=(0.15, 1.0, 0.25))
    seam = mat("green_seam_glow", (0.85, 1.0, 0.7), 0.3, emit=3.0)
    face = mat("green_face", (0.03, 0.25, 0.06), 0.4)
    c = Vector((0, 0, 0.22))
    parts = [sphere(0.22, c, glow, segs=28, rings=16)]
    # a tennis-ball seam: a closed curve winding round the ball
    pts = []
    for k in range(65):
        a = 2 * math.pi * k / 64
        d = Vector((math.cos(a), math.sin(a), 0.62 * math.sin(2 * a)))
        pts.append(c + d.normalized() * 0.222)
    parts.append(tube(pts, [0.009] * len(pts), seam, verts=6, caps=False, name="seam"))
    # a sleepy smile: two closed-eye arcs and a small grin
    for s in (-1, 1):
        arc = [ball_pt(c, 0.221, Vector((s * 0.065 + 0.03 * math.cos(a), -0.2, 0.06 + 0.02 * math.sin(a))))
               for a in (math.pi * k / 6 for k in range(7))]
        parts.append(tube(arc, [0.007] * len(arc), face, verts=6, caps=True, name="lid"))
    grin = []
    for k in range(9):
        a = math.pi * (1 + k / 8)
        grin.append(ball_pt(c, 0.221, Vector((0.05 * math.cos(a), -0.2, -0.03 + 0.03 * math.sin(a)))))
    parts.append(tube(grin, [0.008] * len(grin), face, verts=6, caps=True, name="grin"))
    export(face_camera(join(parts, "green")), "green")


def face_camera(o):
    """Turns a ball's face (built at -Y) towards the game camera's diagonal: Godot +X+Z."""
    o.data.transform(Matrix.Rotation(math.radians(45), 4, "Z"))
    return o


def ball_pt(c, r, p):
    """The point of the sphere (centre c, radius r) along the direction of p (a direction from c)."""
    return c + p.normalized() * r


def purple():
    reset()
    shell = mat("purple_shell", (0.42, 0.12, 0.72), 0.2, coat=1.0)
    speck = mat("purple_speckle", (0.78, 0.6, 1.0), 0.35, coat=0.6)
    crack = mat("purple_crack_glow", (1.0, 0.6, 1.0), 0.3, emit=4.0, emit_color=(1.0, 0.5, 0.95))
    eye = mat("purple_eye_glow", (1.0, 0.95, 0.3), 0.2, emit=5.0)
    c = Vector((0, 0, 0.245))
    egg = sphere(0.23, c, shell, segs=28, rings=16)
    for v in egg.data.vertices:  # an egg: taller, narrower at the top
        z = (v.co.z - c.z) / 0.23
        v.co.z = c.z + (v.co.z - c.z) * 1.08
        k = 1 - 0.1 * max(0.0, z)
        v.co.x *= k
        v.co.y *= k
    egg.data.update()

    def surf(d):
        d = Vector(d).normalized()
        x, y, z = d
        k = 1 - 0.1 * max(0.0, z)
        return Vector((c.x + x * 0.23 * k, c.y + y * 0.23 * k, c.z + z * 0.23 * 1.08))

    parts = [egg]
    rnd = random.Random(31)
    for d in fib_dirs(46):
        if abs(d.z - 0.3) < 0.18:  # keep the crack's band clear
            continue
        p = surf(d)
        sp = ell((0, 0, 0), (rnd.uniform(0.018, 0.03), rnd.uniform(0.018, 0.03), 0.006), speck, segs=8, rings=4)
        sp.data.transform(Matrix.Translation(p) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4())
        parts.append(sp)
    # a zigzag crack round the upper third, glowing from inside
    pts = []
    for k in range(29):
        a = 2 * math.pi * k / 28
        z = 0.3 + (0.09 if k % 2 else -0.05)
        d = Vector((math.cos(a), math.sin(a), z))
        pts.append(surf(d) + d.normalized() * 0.002)
    parts.append(tube(pts, [0.011] * len(pts), crack, verts=6, caps=False, name="crack"))
    for s in (-1, 1):  # two eyes peeking out through the crack
        d = Vector((s * 0.32, -1.0, 0.3))
        e = ell((0, 0, 0), (0.028, 0.034, 0.008), eye, segs=10, rings=6)
        e.data.transform(Matrix.Translation(surf(d)) @ d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4())
        parts.append(e)
    export(face_camera(join(parts, "purple")), "purple")


# ------------------------------------------------------------------ the serpent

def serpent_mats():
    return (mat("serpent_skin", (0.46, 0.14, 0.72), 0.3, coat=0.7),
            mat("serpent_belly", (0.95, 0.78, 0.55), 0.45, coat=0.3),
            mat("serpent_spot", (0.24, 0.06, 0.42), 0.35, coat=0.6))


def serpent():
    reset()
    skin, belly, spot = serpent_mats()
    crest = mat("serpent_crest", (1.0, 0.25, 0.6), 0.35, coat=0.5)
    mouth = mat("serpent_mouth", (0.45, 0.04, 0.1), 0.5)
    fang = mat("serpent_fang", (1.0, 0.98, 0.9), 0.2, coat=1.0)
    tongue_m = mat("serpent_tongue", (0.95, 0.12, 0.25), 0.4)
    eye_m = mat("serpent_eye_glow", (1.0, 0.85, 0.1), 0.2, emit=2.2)
    pupil = mat("serpent_pupil", (0.02, 0.01, 0.02), 0.2, coat=1.0)
    H = Vector((0, -0.02, 0.62))  # head centre
    bones = {"root": ((0, 0, 0), (0, 0, 0.06), None),
             "neck1": ((0, 0.2, 0.17), (0, 0.13, 0.4), "root"),
             "neck2": ((0, 0.13, 0.4), (0, 0.04, 0.56), "neck1"),
             "head": ((0, 0.04, 0.56), (0, -0.2, 0.62), "neck2"),
             "jaw": ((0, 0.02, 0.56), (0, -0.2, 0.52), "head"),
             "tongue": ((0, -0.14, 0.55), (0, -0.3, 0.55), "jaw")}
    rig = TurnRig(bones, 180, hidden=("tongue",))

    # the neck: an S rising from the body behind to the back of the head, a belly strip up its front
    npts = [(0, 0.2, 0.17), (0, 0.19, 0.27), (0, 0.13, 0.4), (0, 0.06, 0.5), (0, 0.02, 0.57)]
    nrad = [0.14, 0.135, 0.12, 0.11, 0.1]
    neck = tube(npts, nrad, skin, verts=18, caps=False, name="neck")
    plates, spots = [], []
    from blastyard_bombers import smooth_path, smooth_radii
    path, radii = smooth_path(npts, 3), smooth_radii(nrad, 3)
    for i in range(1, len(path) - 1):
        p, r = path[i], radii[i]
        t = (path[i + 1] - path[i - 1]).normalized()
        fwd = (Vector((0, -1, 0)) - t * t.y * -1).normalized()   # the front of the neck
        q = p + fwd * (r * 0.9)
        pl = ell((0, 0, 0), (r * 0.72, 0.03, 0.035), belly, segs=12, rings=6)
        pl.data.transform(Matrix.Translation(q) @ fwd.to_track_quat("Y", "Z").to_matrix().to_4x4())
        plates.append(pl)
        if i % 2 == 0:
            back = -fwd
            for s in (-1, 1):
                side = t.cross(fwd).normalized() * s
                d = (back * 0.8 + side * 0.6).normalized()
                sp = ell((0, 0, 0), (0.03, 0.03, 0.008), spot, segs=8, rings=4)
                sp.data.transform(Matrix.Translation(p + d * r * 0.98) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4())
                spots.append(sp)

    def w_neck(p):
        a = smoothstep(0.24, 0.42, p.z)
        b = smoothstep(0.46, 0.58, p.z)
        return {"neck1": (1 - a) + 1e-4, "neck2": a * (1 - b) + 1e-4, "head": b + 1e-4}
    rig.custom(w_neck, neck, plates, spots)

    # the head: a broad, rounded wedge with a snout; upper jaw on the head bone
    head = ell(H, (0.165, 0.2, 0.12), skin, segs=24, rings=14)
    for v in head.data.vertices:  # flatter underneath, a little snub at the front
        if v.co.z < H.z - 0.02:
            v.co.z = H.z - 0.02 + (v.co.z - (H.z - 0.02)) * 0.55
        if v.co.y < H.y - 0.1:
            v.co.x *= 1 - (H.y - 0.1 - v.co.y) * 1.2
    head.data.update()
    hparts = [head]
    # eyes up on the brow, slit pupils, heavy lids
    for s in (-1, 1):
        ec = Vector((s * 0.085, -0.08, 0.7))
        hparts.append(ell(ec, (0.055, 0.05, 0.058), eye_m, yaw=-s * 20, segs=16, rings=10))
        hparts.append(ell(ec + Vector((-s * 0.006, -0.046, 0.0)), (0.009, 0.012, 0.04), pupil, yaw=-s * 20, segs=8,
                          rings=6))
        lid = hemi(0.064, (0, 0, 0), (0, 0, 1), skin, cut=0.05, segs=16, rings=10)
        lid.data.transform(Matrix.Translation(ec) @ Matrix.Rotation(math.radians(s * 18), 4, "Y")
                           @ Matrix.Rotation(math.radians(-14), 4, "X"))
        hparts.append(lid)
        hparts.append(sphere(0.012, (s * 0.04, -0.215, 0.64), pupil, segs=6, rings=4))   # nostril
        hparts.append(cone((s * 0.05, -0.165, 0.565), (s * 0.048, -0.172, 0.5), 0.017, fang, verts=8))
        hparts.append(ell((s * 0.13, 0.02, 0.62), (0.012, 0.05, 0.02), spot, segs=8, rings=4))
    # a magenta crest down the top of the head
    for k, (y, z, h) in enumerate(((-0.04, 0.73, 0.07), (0.03, 0.72, 0.085), (0.1, 0.69, 0.07), (0.15, 0.64, 0.05))):
        fin = ell((0, y, z + h * 0.4), (0.012, 0.035, h * 0.6), crest, pitch=-20, segs=10, rings=6)
        hparts.append(fin)
    hparts.append(ell((0, -0.08, 0.575), (0.13, 0.13, 0.03), mouth, segs=16, rings=6))   # the mouth's roof
    rig.rigid("head", hparts)
    jaw = ell((0, -0.08, 0.545), (0.13, 0.15, 0.04), belly, segs=18, rings=8)
    rig.rigid("jaw", jaw, ell((0, -0.08, 0.565), (0.11, 0.12, 0.012), mouth, segs=14, rings=4))
    tg = [rod((0, -0.1, 0.56), (0, -0.25, 0.55), 0.011, tongue_m, verts=6),
          rod((0, -0.25, 0.55), (0.025, -0.3, 0.555), 0.008, tongue_m, r2=0.002, verts=6),
          rod((0, -0.25, 0.55), (-0.025, -0.3, 0.555), 0.008, tongue_m, r2=0.002, verts=6)]
    rig.rigid("tongue", tg)
    rig.build("serpent")

    def hp(sway, open_, tongue=0.0, flick=0.0):
        p = {"neck1": (4 * sway, 0, 10 * sway), "neck2": (-6 * sway, 6 * sway, 8 * sway),
             "head": (-8 * open_ + 3 * sway, 0, -6 * sway), "jaw": (26 * open_, 0, 0)}
        if tongue:
            p["%tongue"] = (1, tongue, 1)
            p["tongue"] = (0, 0, 14 * flick)
        return p
    rig.action("hiss", {0: hp(0, 0), 6: hp(0.6, 0.1), 12: hp(1, 0.9), 14: hp(1, 1, 1, 1), 16: hp(1, 1, 1, -1),
                        18: hp(0.9, 1, 1, 1), 20: hp(0.8, 0.9, 0.2), 24: hp(0.0, 0.2), 30: hp(-0.8, 0.5, 1, 1),
                        32: hp(-0.9, 0.5, 1, -1), 34: hp(-0.5, 0.3, 0.2), 36: hp(0, 0)}, loop=True)
    rig.save("serpent")


def serpent_segment():
    reset()
    skin, belly, spot = serpent_mats()
    r = 0.17
    parts = [sphere(r, (0, 0, 0), skin, segs=22, rings=12)]
    band = ell((0, 0, -0.07), (r * 0.93, r * 0.93, 0.08), belly, segs=22, rings=8)
    parts.append(band)
    rnd = random.Random(5)
    for d in fib_dirs(26):
        if d.z < 0.1:
            continue
        sp = ell((0, 0, 0), (rnd.uniform(0.03, 0.045), rnd.uniform(0.03, 0.045), 0.008), spot, segs=8, rings=4)
        sp.data.transform(Matrix.Translation(d * r * 0.99) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4())
        parts.append(sp)
    export(join(parts, "serpent_segment"), "serpent_segment")


# ------------------------------------------------------------------ the imp

def imp():
    reset()
    skin = mat("imp_skin", (0.3, 0.72, 0.18), 0.5, coat=0.3)
    belly = mat("imp_belly", (0.7, 0.92, 0.45), 0.6)
    ear_m = mat("imp_ear", (1.0, 0.55, 0.6), 0.55)
    horn = mat("imp_horn", (1.0, 0.9, 0.6), 0.35, coat=0.6)
    eye_m = mat("imp_eye_glow", (1.0, 0.8, 0.1), 0.2, emit=1.8)
    pupil = mat("imp_pupil", (0.02, 0.02, 0.02), 0.2, coat=1.0)
    mouth = mat("imp_mouth", (0.25, 0.02, 0.05), 0.5)
    tooth = mat("imp_tooth", (1.0, 0.98, 0.9), 0.3)
    claw = mat("imp_claw", (0.2, 0.3, 0.1), 0.4)
    bones = {"root": ((0, 0, 0), (0, 0, 0.04), None),
             "body": ((0, 0, 0.06), (0, 0, 0.2), "root"),
             "head": ((0, 0, 0.2), (0, 0, 0.36), "body"),
             "ear.L": ((0.12, 0.0, 0.3), (0.23, 0.03, 0.39), "head"),
             "ear.R": ((-0.12, 0.0, 0.3), (-0.23, 0.03, 0.39), "head"),
             "arm.L": ((0.1, -0.01, 0.17), (0.17, -0.04, 0.1), "body"),
             "arm.R": ((-0.1, -0.01, 0.17), (-0.17, -0.04, 0.1), "body"),
             "foot.L": ((0.06, 0.0, 0.03), (0.06, -0.07, 0.02), "root"),
             "foot.R": ((-0.06, 0.0, 0.03), (-0.06, -0.07, 0.02), "root"),
             "tail": ((0, 0.1, 0.1), (0, 0.2, 0.16), "body")}
    rig = TurnRig(bones, 180)
    body = ell((0, 0, 0.14), (0.11, 0.1, 0.1), skin, segs=18, rings=10)
    bel = ell((0, -0.06, 0.13), (0.075, 0.05, 0.07), belly, segs=14, rings=8)
    head = ell((0, -0.01, 0.275), (0.13, 0.115, 0.1), skin, segs=22, rings=12)

    def w_bh(p):
        t = smoothstep(0.17, 0.23, p.z)
        return {"body": 1 - t + 1e-4, "head": t + 1e-4}
    rig.custom(w_bh, body, bel, head)
    hp = []
    for s in (-1, 1):
        ec = Vector((s * 0.05, -0.095, 0.3))
        hp.append(ell(ec, (0.038, 0.03, 0.04), eye_m, yaw=-s * 15, segs=12, rings=8))
        hp.append(ell(ec + Vector((0, -0.028, -0.004)), (0.016, 0.008, 0.02), pupil, segs=8, rings=6))
        lid = hemi(0.044, (0, 0, 0), (0, 0, 1), skin, cut=0.15, segs=14, rings=8)   # sly half-lids slanting in
        lid.data.transform(Matrix.Translation(ec) @ Matrix.Rotation(math.radians(s * 22), 4, "Y")
                           @ Matrix.Rotation(math.radians(-10), 4, "X"))
        hp.append(lid)
        hp.append(cone((s * 0.045, -0.02, 0.36), (s * 0.06, 0.0, 0.42), 0.022, horn, verts=8))
    # a wide grin with two teeth
    grin = [Vector((0.075 * math.cos(a), -0.1 - 0.018 * math.sin(a) * 0, 0.235 - 0.03 * math.sin(a)))
            for a in (math.pi * (0.1 + 0.8 * k / 8) for k in range(9))]
    grin = [Vector((g.x, -math.sqrt(max(0.0, 1 - (g.x / 0.13) ** 2 - ((g.z - 0.275) / 0.1) ** 2)) * 0.115 - 0.01, g.z))
            for g in grin]
    hp.append(tube(grin, [0.012] * len(grin), mouth, verts=6, caps=True, name="grin"))
    for s in (-1, 1):
        hp.append(cone((s * 0.025, -0.108, 0.212), (s * 0.025, -0.106, 0.19), 0.011, tooth, verts=6))
    rig.rigid("head", hp)
    for s, side in ((1, "L"), (-1, "R")):
        e = cone((s * 0.1, 0.0, 0.29), (s * 0.24, 0.035, 0.4), 0.05, skin, verts=10)
        e.data.transform(Matrix.Translation((0, 0, 0)))
        for v in e.data.vertices:   # flatten the ear into a leaf
            v.co.y = 0.0 + (v.co.y - 0.0) * 0.45 + (v.co.x * s - 0.1) * 0.12
        inner = cone((s * 0.11, -0.012, 0.295), (s * 0.215, 0.02, 0.385), 0.03, ear_m, verts=8)
        for v in inner.data.vertices:
            v.co.y = -0.012 + (v.co.y + 0.012) * 0.3 + (v.co.x * s - 0.1) * 0.12 - 0.008
        rig.rigid("ear." + side, e, inner)
        arm = [rod((s * 0.09, -0.01, 0.17), (s * 0.15, -0.04, 0.11), 0.022, skin, verts=8),
               sphere(0.03, (s * 0.155, -0.045, 0.1), skin, segs=10, rings=6)]
        arm += [cone((s * 0.155 + dx, -0.06, 0.09), (s * 0.155 + dx * 1.4, -0.08, 0.07), 0.008, claw, verts=5)
                for dx in (-0.012, 0.012)]
        rig.rigid("arm." + side, arm)
        ft = [ell((s * 0.06, -0.025, 0.025), (0.04, 0.06, 0.025), skin, segs=12, rings=6)]
        ft += [cone((s * 0.06 + dx, -0.075, 0.02), (s * 0.06 + dx, -0.1, 0.012), 0.009, claw, verts=5)
               for dx in (-0.015, 0.015)]
        leg = rod((s * 0.06, 0.0, 0.1), (s * 0.06, -0.01, 0.03), 0.028, skin, verts=8)
        rig.rigid("foot." + side, ft)

        def w_leg(p, side=side):
            t = smoothstep(0.04, 0.09, p.z)
            return {"foot." + side: 1 - t + 1e-4, "body": t + 1e-4}
        rig.custom(w_leg, leg)
    tl = [tube([(0, 0.08, 0.1), (0, 0.15, 0.09), (0, 0.2, 0.13), (0, 0.2, 0.18)], [0.018, 0.013, 0.01, 0.008], skin,
               verts=8, caps=False, name="tail"), sphere(0.024, (0, 0.2, 0.19), skin, segs=8, rings=6)]
    rig.rigid("tail", tl)
    rig.build("imp")

    def bp(h, sq, arm, ear, feet=0.0):
        return merge({"@root": (0, 0, h), "%body": (1 + sq, 1 + sq, 1 - 1.5 * sq), "head": (-4 * sq * 10, 0, 0),
                      "tail": (40 * h / 0.1, 0, 0)},
                     mirror({"arm.L": (0, arm, 0), "ear.L": (0, ear, 0), "foot.L": (feet * 40, 0, 0),
                             "@foot.L": (0, 0, feet * 0.04)}))
    rig.action("bounce", {0: bp(0, 0.14, -10, -15), 4: bp(0.03, -0.1, 30, 20), 9: bp(0.08, 0.0, 70, 35, 1.0),
                          13: bp(0.03, -0.08, 40, 10), 18: bp(0, 0.14, -10, -15)}, loop=True)
    rig.save("imp")


# ------------------------------------------------------------------ the disc

BANDS = [(1.0, 0.2, 0.25), (1.0, 0.55, 0.15), (1.0, 0.92, 0.25), (0.3, 0.95, 0.4), (0.25, 0.6, 1.0), (0.65, 0.35, 1.0)]


def disc():
    reset()
    cloud = mat("disc_cloud_glow", (0.93, 0.93, 1.0), 0.9, emit=0.08)
    under = mat("disc_under_glow", (0.6, 0.85, 1.0), 0.5, emit=0.8)
    parts = []
    for i, col in enumerate(BANDS):
        m = mat("disc_band_%d_glow" % i, col, 0.3, emit=1.1)
        z = 0.0 + i * 0.008   # concentric rainbow rings round the cushion: red outside, violet inside
        parts.append(torus(0.385 - i * 0.021, 0.013, (0, 0, z), m, verts=40, minor=6))
    parts.append(K.cyl(0.39, 0.03, (0, 0, -0.03), under, verts=40))
    rnd = random.Random(11)
    for k in range(10):  # a ring of cloud puffs round the rim, a smaller ring inside, one in the middle
        a = 2 * math.pi * k / 10 + rnd.uniform(-0.1, 0.1)
        parts.append(lumpy(rnd.uniform(0.08, 0.09), (0.18 * math.cos(a), 0.18 * math.sin(a), 0.04), cloud, 100 + k,
                           0.1, scale=(0.95, 0.95, 0.65), sub=2, smooth=70))
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        parts.append(lumpy(0.085, (0.08 * math.cos(a), 0.08 * math.sin(a), 0.05), cloud, 200 + k, 0.08,
                           scale=(1, 1, 0.55), sub=2, smooth=70))
    parts.append(lumpy(0.09, (0, 0, 0.06), cloud, 300, 0.06, scale=(1, 1, 0.5), sub=2, smooth=70))
    export(join(parts, "disc"), "disc")


JOBS = {"pip": pip, "red": red, "green": green, "purple": purple, "serpent": serpent,
        "serpent_segment": serpent_segment, "imp": imp, "disc": disc}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
