"""Tunnel Pop (game 32) models: the digger (the hero), the two burrowing enemies (the puffer and the drake), the rock
and its shard, eight bonus vegetables and the dressing for the grassy strip above ground.
Original designs for a garden underground: the digger is our own character (a mole kid in teal overalls with a
velvet-brown face, a pink snout and whiskers, big spade paws, a yellow miner's helmet with a lamp, a red neckerchief
and a brass hand pump strapped to the back, its red hose running to a flared brass nozzle held in the right paw);
the puffer is a fuzzy lilac dumpling critter (a pleated, pinched top with a curl, a cream tummy, big round eyes,
blushing cheeks, a buck tooth and tiny orange feet); the drake is a chubby, stubby green dragonling (a big round
snout with nostrils, cream belly plates, a crest of soft orange spines, little orange bat wings, a curled tail).
Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/tunnelpop_models.py -- godot/games/tunnelpop/art/models [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (merge,
mirror, smoothstep, limb), hopline_models.py (TurnRig, ell, hemi), mossfolk_models.py (lathe_r, lumpy) and
prism_models.py (export_anim, empty, new_obj). 30 fps.

Axes: the world is a cross-section of earth in the Godot XY plane seen from +Z (cells of 1, tunnels 1 tall, the play
plane at z = 0). Characters are built in Blender facing -Y and turned to face Godot +X (their right side towards
the camera); Godot +Y (Blender +Z) is up. Game size (node scale 1). To face left, turn the node by PI about Y (the
other side shows: the models are finished all round) or mirror it with scale.x = -1. Animations marked * are
seamless loops: set their loop mode in the game. Emissive materials all have "glow" in their names.

digger.glb   armature "digger_rig" (root, hips, body, head, eye.L/R, glint, plunger, arm.L/R, fore.L/R, leg.L/R,
             foot.L/R), skinned mesh "digger": 0.86 tall to the helmet top, origin at the feet, facing +X, 0.60 long
             from the pump at the back (Godot x -0.27) to the nozzle's bell (x +0.33), 0.45 deep. Child empty
             "nozzle" (on the bone fore.R) at the mouth of the brass nozzle (rest: Godot x 0.325, y 0.29, z 0.17):
             start the hose line there. Materials digger_fur, digger_muzzle, digger_nose, digger_cheek,
             digger_whisker, digger_eye_white, digger_iris, digger_pupil, digger_eye_glow (catch lights), digger_paw,
             digger_claw, digger_shirt, digger_scarf, digger_overalls, digger_stitch, digger_button, digger_boot,
             digger_sole, digger_helmet, digger_brass (pump, lamp housing, nozzle), digger_lamp_glow (the lamp lens),
             digger_glint_glow (a star glint on the lamp, tiny at rest, flashing in idle and dig), digger_hose,
             digger_handle (the plunger's T-handle and the nozzle grip), digger_gauge (its dial face), digger_strap.
             Animations:  idle*  2.0 s  breathing, a look round, one blink, the lamp glints once
                          walk*  0.5 s  two strides (feet planted ~0.24 apart: about 1 unit/s at speed 1), a bob
                          dig*   0.5 s  leaning in, paws clawing at the earth in turn, steps, the lamp glints
                          pump   0.3 s  a squat and heave: the plunger rams down (repeatable; starts and ends at rest)
                          shoot  0.4 s  wind back (f3), the nozzle thrust forward and level (f6, held to f8), back
                          die    1.4 s  a jolt, dizzy wobbles, the knees go (f28), then splat: squashed flat as a
                                        pancake (f31, settles by f42, holds the last frame); it suits a rock as well
                          cheer* 1.0 s  two hops, the left paw and the nozzle waved up, eyes happy
                          climb* 0.5 s  scrabbling up a shaft: paws reaching overhead in turn, feet kicking
puffer.glb   armature "puffer_rig" (root, body, top, eyes, foot.L/R), skinned mesh "body" (0.78 tall to the curl,
             0.61 long, origin at the feet, facing +X) and the separate mesh "eyes" (both goggling eyes, on the bone
             "eyes"): hide "body" in ghost mode and the eyes drift alone. Materials puffer_fur, puffer_tummy,
             puffer_cheek, puffer_mouth, puffer_tooth, puffer_feet, puffer_eye_white, puffer_pupil, puffer_eye_glow.
             Animations:  walk*    0.6 s  a bouncy waddle
                          ghost*   1.0 s  the eyes drift and bob, looking about, a slow blink (hide "body")
                          inflate  1.0 s  four puffs, each held: the body bone scales 1.18 (held f4-f7), 1.36
                                          (f11-f15), 1.55 (f19-f22), 1.75 (f26-f30); feet splay, eyes bulge. Seek to
                                          0.23, 0.5, 0.73 or 1.0 s to show step 1..4, or scale the node by the same
                                          steps instead (the origin stays on the ground).
                          pop      0.3 s  a last over-swell and a shudder, gone at f7 (eyes too); optional
                          stunned* 1.0 s  a dizzy sway, eyes squeezed shut
drake.glb    armature "drake_rig" (root, body, neck, head, jaw, eyes, wing.L/R, tail, tail2, leg.L/R), skinned mesh
             "body" (0.79 tall to the crest, 0.83 long from the tail at Godot x -0.45 to the snout at +0.38, origin at
             the feet, facing +X) and the separate mesh "eyes" (eyes and lids, on the bone "eyes"). Child empty
             "mouth" (on the bone "head", rest Godot x 0.36, y 0.47, z 0) just in front of the jaws: start the flame
             there. Materials drake_scale, drake_belly, drake_spine (crest, cheek frills, tail spade), drake_wing,
             drake_nostril, drake_mouth, drake_tongue, drake_tooth, drake_claw, drake_eye_white, drake_pupil,
             drake_eye_glow.
             Animations:  walk*    0.6 s  a stubby waddle, the wings fluttering, the tail swinging
                          ghost*   1.0 s  as the puffer's (hide "body")
                          breathe  0.6 s  rears back (f8), then lunges with the jaw wide and the head level (f12 ..
                                          f15: the moment to start the flame), back to rest at f18
                          stunned* 1.0 s  a dizzy sway, eyes squeezed, jaw hanging, wings drooping
Both enemies (and the digger) read best turned a little towards the camera: a yaw of about 30 degrees off the pure
profile shows both eyes.
rock.glb     mesh "rock": a boulder 0.95 across, about 0.85 tall, origin at its bottom centre, with a child mesh "crack"
             (dark fissures pressed into its front face): HIDE "crack" when the scene loads (glTF has no hidden flag)
             and show it while the rock wobbles. Materials rock_stone, rock_light (the worn top, pebbles, a fossil
             swirl), rock_crack.
rock_shard.glb  mesh "rock_shard": a chipped fragment 0.24 across, origin at its centre; rock_stone, rock_light.
veg_*.glb    one mesh named like the file, 0.57-0.65 tall, origin at the bottom centre, glossy (clear-coated)
             materials veg_<name>_...: veg_carrot, veg_turnip, veg_mushroom, veg_pepper (green), veg_pumpkin,
             veg_eggplant, veg_pineapple, veg_melon (a striped watermelon).
Surface (one mesh each, named like the file; origin on the ground, the front towards the camera, Godot +Z):
             flower_a (0.5 tall, a pink daisy), flower_b (0.35, two arching stems of bluebells), bush (1.1 wide,
             0.62 tall, red berries), fence (2.0 along X from x -1 to +1, 0.7 tall, white pickets, posts at x -0.5 and
             +0.5: tile it every 2), signpost (1.1 tall, a blank cream arrow board pointing +X), wheelbarrow (1.34
             long, 0.56 tall, wheel at +X, a heap of soil in the tray), shed (a garden shed 2.54 tall, 2.0 wide with
             its corner posts, 1.4 deep plus the roof's overhang; door, a lit window (shed_glow) with a flower box),
             level_flower (a sunflower 1.2 tall facing the camera: one per level, like a counter).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, export, reset, cyl, box, prism
from blastyard_bombers import merge, mirror, smoothstep, limb
from hopline_models import TurnRig, ell, hemi
from mossfolk_models import lathe_r, lumpy
from prism_models import export_anim, empty, new_obj

FPS = 30


def cone(base, tip, r, material, verts=8):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


def pin(rig, name, loc, bone):
    """An empty at loc (build frame, facing -Y) carried by `bone` of a built TurnRig."""
    e = empty(name)
    e.empty_display_size = 0.05
    bpy.context.view_layer.update()
    e.matrix_world = Matrix.Translation(rig.Q3 @ Vector(loc))
    attach(rig, e, bone)
    return e


def attach(rig, o, bone):
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = rig.arm
    o.parent_type = "BONE"
    o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = mw
    return o


def poly_param(p, pts):
    """The arc-length fraction along a polyline of the point closest to p."""
    best, bd, acc = 0.0, 1e9, 0.0
    lens = [(b - a).length for a, b in zip(pts, pts[1:])]
    tot = sum(lens)
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
        d = (p - (a + ab * t)).length
        if d < bd:
            bd, best = d, (acc + t * L) / tot
        acc += L
    return best


def glint_star(c, r, material, name="glint"):
    """A flat four-point sparkle facing -Y."""
    bm = bmesh.new()
    rim = []
    for k in range(8):
        a = math.pi / 2 + k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.22
        rim.append(bm.verts.new((c[0] + rr * math.cos(a), c[1], c[2] + rr * math.sin(a))))
    f = bm.verts.new((c[0], c[1] - r * 0.15, c[2]))
    b = bm.verts.new((c[0], c[1] + r * 0.15, c[2]))
    for k in range(8):
        bm.faces.new((rim[k], rim[(k + 1) % 8], f))
        bm.faces.new((rim[(k + 1) % 8], rim[k], b))
    return new_obj(name, bm, material, smooth=0)


# ------------------------------------------------------------------ the digger

def digger():
    reset()
    fur = mat("digger_fur", (0.36, 0.22, 0.14), 0.75, coat=0.1)
    muzzle = mat("digger_muzzle", (0.9, 0.66, 0.46), 0.7)
    nose = mat("digger_nose", (0.95, 0.42, 0.52), 0.3, coat=0.8)
    cheek = mat("digger_cheek", (1.0, 0.5, 0.5), 0.6)
    whisk = mat("digger_whisker", (0.2, 0.13, 0.1), 0.5)
    white = mat("digger_eye_white", (0.98, 0.97, 0.94), 0.25, coat=0.8)
    iris = mat("digger_iris", (0.35, 0.2, 0.08), 0.3, coat=1.0)
    pupil = mat("digger_pupil", (0.02, 0.02, 0.03), 0.2, coat=1.0)
    shine = mat("digger_eye_glow", (1.0, 1.0, 1.0), 0.1, emit=4.0)
    paw = mat("digger_paw", (0.97, 0.66, 0.64), 0.55)
    claw = mat("digger_claw", (0.98, 0.94, 0.84), 0.35, coat=0.5)
    shirt = mat("digger_shirt", (0.96, 0.92, 0.8), 0.7)
    scarf = mat("digger_scarf", (0.86, 0.16, 0.12), 0.6)
    over = mat("digger_overalls", (0.12, 0.46, 0.56), 0.7)
    stitch = mat("digger_stitch", (0.98, 0.78, 0.3), 0.6)
    button = mat("digger_button", (0.95, 0.68, 0.22), 0.3, metal=0.8)
    boot = mat("digger_boot", (0.42, 0.22, 0.1), 0.45, coat=0.3)
    sole = mat("digger_sole", (0.16, 0.1, 0.07), 0.8)
    helmet = mat("digger_helmet", (1.0, 0.74, 0.1), 0.35, coat=0.7)
    brass = mat("digger_brass", (0.92, 0.64, 0.24), 0.28, metal=0.9)
    lamp = mat("digger_lamp_glow", (1.0, 0.95, 0.75), 0.1, emit=5.0, emit_color=(1.0, 0.88, 0.55))
    glint_m = mat("digger_glint_glow", (1.0, 1.0, 0.9), 0.1, emit=12.0)
    hose = mat("digger_hose", (0.78, 0.1, 0.08), 0.45, coat=0.3)
    handle = mat("digger_handle", (0.75, 0.16, 0.1), 0.45, coat=0.5)
    gauge = mat("digger_gauge", (0.97, 0.95, 0.88), 0.4)
    strap = mat("digger_strap", (0.33, 0.2, 0.1), 0.7)

    HC = Vector((0, -0.01, 0.6))       # head centre
    # the helmet is modelled sitting at 0.665 and then lifted and tipped back a little by HT
    HT = (Matrix.Translation((0, 0.004, 0.66 + 0.014)) @ Matrix.Rotation(math.radians(-6), 4, "X")
          @ Matrix.Translation((0, 0, -0.66)))
    HR = Vector((0.155, 0.145, 0.145))
    bones = {"root": ((0, 0, 0), (0, 0, 0.06), None),
             "hips": ((0, 0, 0.17), (0, 0, 0.3), "root"),
             "body": ((0, 0, 0.3), (0, 0, 0.46), "hips"),
             "head": ((0, 0, 0.47), (0, 0, 0.74), "body"),
             "eye.L": ((0.072, -0.104, 0.628), (0.072, -0.16, 0.628), "head"),
             "eye.R": ((-0.072, -0.104, 0.628), (-0.072, -0.16, 0.628), "head"),
             "glint": (tuple(HT @ Vector((0, -0.214, 0.735))), tuple(HT @ Vector((0, -0.26, 0.735))), "head"),
             "plunger": ((0, 0.19, 0.5), (0, 0.19, 0.6), "body"),
             "arm.L": ((0.125, 0.0, 0.42), (0.16, -0.02, 0.33), "body"),
             "arm.R": ((-0.125, 0.0, 0.42), (-0.16, -0.03, 0.33), "body"),
             "fore.L": ((0.16, -0.02, 0.33), (0.165, -0.07, 0.26), "arm.L"),
             "fore.R": ((-0.16, -0.03, 0.33), (-0.17, -0.1, 0.27), "arm.R"),
             "leg.L": ((0.07, 0.0, 0.19), (0.072, 0.0, 0.065), "hips"),
             "leg.R": ((-0.07, 0.0, 0.19), (-0.072, 0.0, 0.065), "hips"),
             "foot.L": ((0.072, 0.0, 0.065), (0.072, -0.09, 0.03), "leg.L"),
             "foot.R": ((-0.072, 0.0, 0.065), (-0.072, -0.09, 0.03), "leg.R")}
    rig = TurnRig(bones, 90, fps=FPS)

    def w_trunk(p):
        a = smoothstep(0.2, 0.3, p.z)
        b = smoothstep(0.44, 0.5, p.z)
        return {"hips": (1 - a) + 1e-4, "body": a * (1 - b) + 1e-4, "head": b + 1e-4}

    # the overalls: a pear-shaped trunk, the bib and the straps; the shirt above, the neckerchief at the neck
    trunk = lathe_r([(0.0, 0.47), (0.07, 0.468), (0.11, 0.45), (0.13, 0.41), (0.145, 0.35), (0.155, 0.29),
                     (0.15, 0.23), (0.13, 0.185), (0.09, 0.16), (0.0, 0.155)], shirt, segs=28, name="trunk",
                    smooth=60)
    for v in trunk.data.vertices:   # a little deeper than wide at the tummy, flatter at the back
        v.co.y *= 0.9 if v.co.y < 0 else 0.82
    trunk.data.update()
    trunk.data.materials.append(over)
    for f in trunk.data.polygons:
        if f.center.z < 0.33:
            f.material_index = 1
    parts = [trunk]
    # the bib: a rounded panel on the tummy, with a pocket, two buttons and stitched edges
    bib_pts = [-1 + 2 * k / 8 for k in range(9)]
    bib = []
    for i in range(7):
        z = 0.3 + 0.12 * i / 6
        row = []
        for u in bib_pts:
            x = u * (0.1 - 0.015 * i / 6)
            r = 0.156 if z < 0.33 else 0.15 - 0.06 * ((z - 0.33) / 0.1) ** 2
            y = -math.sqrt(max(0.0, (r * 0.9) ** 2 - x * x)) - 0.006
            row.append(Vector((x, y, z)))
        bib.append(row)
    from fuseflight_models import sheet
    bib_o = sheet(bib, over, "bib")
    K.select(bib_o)
    sm = bib_o.modifiers.new("s", "SOLIDIFY")
    sm.thickness = 0.008
    bpy.ops.object.modifier_apply(modifier=sm.name)
    parts.append(bib_o)
    edge = [bib[-1][j] + Vector((0, -0.007, 0)) for j in range(len(bib_pts))]
    parts.append(tube(edge, [0.004] * len(edge), stitch, verts=5, caps=True, name="stitch"))
    pocket = K.prism([(-0.035, 0.0), (0.035, 0.0), (0.03, -0.045), (-0.03, -0.045)], 0.006, (0, -0.148, 0.37),
                     over, bevel=0.002)
    parts.append(pocket)
    parts.append(tube([(-0.033, -0.152, 0.372), (0.033, -0.152, 0.372)], [0.003, 0.003], stitch, verts=4))
    for s in (-1, 1):
        parts.append(cyl(0.014, 0.008, (s * 0.075, -0.142, 0.41), button, rot=(math.pi / 2 - s * 0.35, 0, 0),
                         verts=12, bevel=0.002))
        # straps over the shoulders to the back
        sp = [(s * 0.08, -0.13, 0.415), (s * 0.085, -0.1, 0.45), (s * 0.08, -0.03, 0.475), (s * 0.075, 0.06, 0.465),
              (s * 0.07, 0.11, 0.42), (s * 0.06, 0.125, 0.33)]
        parts.append(tube(sp, [0.014] * len(sp), over, verts=6, caps=True, name="strap"))
    # the neckerchief: a knotted red scarf, its point at the front
    parts.append(torus(0.085, 0.022, (0, 0, 0.47), scarf, verts=24, minor=8, scale=(1.0, 0.92, 0.85)))
    parts.append(K.prism([(-0.045, 0.0), (0.045, 0.0), (0.0, -0.06)], 0.012, (0, -0.088, 0.465), scarf,
                         rot=(math.radians(-18), 0, 0), bevel=0.004))
    parts.append(sphere(0.02, (0.0, -0.088, 0.458), scarf, segs=10, rings=6))
    rig.custom(w_trunk, parts)

    # the head: velvet brown, a cream muzzle pushing forward into a pink snout, whiskers, small round ears
    head = ell(HC, HR, fur, segs=28, rings=18)
    for v in head.data.vertices:   # a fuller lower face, the crown a touch narrower
        t = (v.co.z - HC.z) / HR.z
        v.co.x *= 1.0 - 0.06 * max(0.0, t) + 0.04 * max(0.0, -t)
    head.data.update()
    hp = [head, ell((0, -0.098, 0.565), (0.1, 0.06, 0.07), muzzle, segs=22, rings=14)]   # the lighter face
    hp.append(tube([(0, -0.11, 0.568), (0, -0.16, 0.572), (0, -0.2, 0.58)], [0.052, 0.044, 0.034], muzzle,
                   verts=18, caps=False, name="snout"))
    hp.append(ell((0, -0.214, 0.586), (0.041, 0.031, 0.034), nose, segs=18, rings=12))
    hp.append(sphere(0.009, (0.014, -0.24, 0.601), shine, segs=6, rings=4))
    for s in (-1, 1):
        hp.append(ell((s * 0.011, -0.24, 0.578), (0.006, 0.004, 0.008), whisk, segs=6, rings=4))   # nostrils
    # buck teeth under the snout
    for s in (-1, 1):
        hp.append(K.box((0.014, 0.008, 0.018), (s * 0.008, -0.162, 0.522), claw, bevel=0.003))
    # a small happy mouth under the snout
    sm_pts = [(0.03 * math.cos(a), -0.158 + 0.014 * abs(math.cos(a)), 0.534 + 0.01 * math.sin(a))
              for a in (math.pi * (1.1 + 0.8 * k / 6) for k in range(7))]
    hp.append(tube(sm_pts, [0.004, 0.005, 0.006, 0.006, 0.006, 0.005, 0.004], whisk, verts=5, caps=True, name="mouth"))
    for s in (-1, 1):
        # cheeks, ears, whiskers
        hp.append(ell((s * 0.098, -0.105, 0.55), (0.03, 0.012, 0.02), cheek, yaw=-s * 40, segs=10, rings=6))
        hp.append(ell((s * 0.14, 0.02, 0.66), (0.022, 0.04, 0.04), fur, roll=s * 20, segs=12, rings=8))
        hp.append(ell((s * 0.146, 0.012, 0.66), (0.012, 0.026, 0.026), paw, roll=s * 20, segs=10, rings=6))
        for k, (dz, dy) in enumerate(((0.012, 0.0), (-0.004, 0.006), (-0.02, 0.012))):
            a = Vector((s * 0.035, -0.18, 0.574 + dz * 0.4))
            b = Vector((s * 0.125, -0.165 + dy, 0.576 + dz * 2.4))
            hp.append(rod(a, b, 0.0035, whisk, r2=0.0012, verts=4))
    rig.custom(lambda p: {"head": 1.0}, hp)

    # the eyes: big, bright and friendly, just above the muzzle
    for s, side in ((1, "L"), (-1, "R")):
        c = Vector((s * 0.072, -0.104, 0.628))
        eye = [ell(c, (0.04, 0.026, 0.052), white, yaw=-s * 36, segs=18, rings=12),
               ell(c + Vector((-s * 0.005, -0.02, -0.006)), (0.028, 0.014, 0.036), iris, yaw=-s * 36, segs=14, rings=8),
               ell(c + Vector((-s * 0.006, -0.028, -0.007)), (0.017, 0.009, 0.023), pupil, yaw=-s * 36, segs=10, rings=6),
               sphere(0.0095, c + Vector((s * 0.004, -0.036, 0.013)), shine, segs=6, rings=4),
               sphere(0.0045, c + Vector((-s * 0.013, -0.034, -0.019)), shine, segs=6, rings=4)]
        rig.rigid("eye." + side, eye)
        brow = [(s * (0.035 + 0.05 * u), -0.13 + 0.02 * u, 0.7 + 0.01 * math.sin(math.pi * u)) for u in (0, 0.5, 1)]
        rig.rigid("head", tube(brow, [0.006, 0.008, 0.005], whisk, verts=5, caps=True, name="brow"))

    # the miner's helmet: a yellow dome with a ridge, a brim, a brass lamp at the front
    dome = hemi(0.163, (0, 0, 0), (0, 0, 1), helmet, cut=-0.05, segs=28, rings=16)
    dome.data.transform(Matrix.Translation((0, 0.0, 0.665)) @ Matrix.Diagonal((1.0, 1.06, 0.98, 1.0))
                        @ Matrix.Rotation(math.radians(-8), 4, "X"))
    brim = lathe_r([(0.17, 0.668), (0.2, 0.664), (0.208, 0.656), (0.2, 0.65), (0.165, 0.652)], helmet, segs=32,
                   name="brim", smooth=50)
    for v in brim.data.vertices:   # a longer peak at the front
        if v.co.y < 0:
            k = -v.co.y / 0.2
            v.co.y -= 0.03 * k * k
            v.co.z -= 0.012 * k * k
    brim.data.transform(Matrix.Translation((0, 0, 0.665)) @ Matrix.Rotation(math.radians(-8), 4, "X")
                        @ Matrix.Translation((0, 0, -0.665)))
    ridge = [(0, 0.17 * math.cos(a) * 1.06, 0.665 + 0.165 * math.sin(a) * 0.98) for a in
             (math.radians(x) for x in (30, 55, 80, 105, 130, 155))]
    ridge = [Matrix.Rotation(math.radians(-8), 3, "X") @ (Vector(p) - Vector((0, 0, 0.665))) + Vector((0, 0, 0.665))
             for p in ridge]
    hel = [dome, brim, tube(ridge, [0.016] * 6, helmet, verts=8, caps=True, name="ridge")]
    # the lamp: a brass can on a bracket, the lens glowing
    lc = Vector((0, -0.18, 0.735))
    hel += [rod(lc + Vector((0, 0.04, 0)), lc + Vector((0, -0.01, 0)), 0.038, brass, verts=20),
            torus(0.036, 0.008, lc + Vector((0, -0.012, 0)), brass, rot=(math.pi / 2, 0, 0), verts=20, minor=6),
            ell(lc + Vector((0, -0.014, 0)), (0.03, 0.012, 0.03), lamp, segs=16, rings=8),
            K.box((0.03, 0.03, 0.04), (0, -0.15, 0.71), brass, bevel=0.006)]
    gl = glint_star((0, -0.216, 0.735), 0.006, glint_m)
    for o in hel + [gl]:
        o.data.transform(HT @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    rig.rigid("head", hel)
    rig.rigid("glint", gl)

    # the brass pump on the back: a tank on leather straps, a gauge, the plunger and its red T-handle
    tc = Vector((0, 0.19, 0.36))
    pump = [lathe_r([(0.0, 0.5), (0.03, 0.497), (0.055, 0.485), (0.065, 0.465), (0.066, 0.26), (0.06, 0.24),
                     (0.035, 0.228), (0.0, 0.225)], brass, segs=24, name="tank", smooth=60, center=(0, 0.19, 0)),
            torus(0.068, 0.007, (0, 0.19, 0.44), brass, verts=24, minor=6),
            torus(0.068, 0.007, (0, 0.19, 0.29), brass, verts=24, minor=6)]
    for s in (-1, 1):   # shoulder straps holding the tank
        pump.append(tube([(s * 0.045, 0.14, 0.46), (s * 0.06, 0.1, 0.47), (s * 0.08, 0.06, 0.47)], [0.012] * 3,
                         strap, verts=6, caps=True, name="strap"))
        pump.append(tube([(s * 0.05, 0.14, 0.27), (s * 0.09, 0.09, 0.26), (s * 0.12, 0.04, 0.27)], [0.012] * 3,
                         strap, verts=6, caps=True, name="strap"))
    # the gauge on the camera side (Blender -X) and its twin on the other side
    for s in (-1, 1):
        gc = Vector((s * 0.068, 0.19, 0.38))
        pump.append(rod(gc, gc + Vector((s * 0.012, 0, 0)), 0.026, brass, verts=16))
        pump.append(rod(gc + Vector((s * 0.012, 0, 0)), gc + Vector((s * 0.015, 0, 0)), 0.021, gauge, verts=16))
        pump.append(rod(gc + Vector((s * 0.016, 0, 0)), gc + Vector((s * 0.016, -0.004, 0.015)), 0.003, scarf, verts=4))
    pump.append(cyl(0.022, 0.03, (0, 0.19, 0.51), brass, verts=14))
    pump.append(rod((0.0, 0.215, 0.24), (0.0, 0.215, 0.215), 0.016, brass, verts=10))   # the hose outlet
    rig.rigid("body", pump)
    plunger = [rod((0, 0.19, 0.5), (0, 0.19, 0.6), 0.011, brass, verts=10),
               rod((-0.07, 0.19, 0.6), (0.07, 0.19, 0.6), 0.02, handle, verts=12),
               sphere(0.024, (0.075, 0.19, 0.6), handle, segs=12, rings=8),
               sphere(0.024, (-0.075, 0.19, 0.6), handle, segs=12, rings=8)]
    rig.rigid("plunger", plunger)

    # arms: shirt sleeves (rolled up), big pink spade paws with cream claws
    def arm_parts(s):
        up = [rod((s * 0.11, 0.0, 0.43), (s * 0.16, -0.02, 0.33), 0.036, shirt, r2=0.032, verts=12),
              sphere(0.04, (s * 0.115, 0.0, 0.425), shirt, segs=12, rings=8),
              sphere(0.033, (s * 0.16, -0.02, 0.33), shirt, segs=12, rings=8)]
        return up

    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("arm." + side, arm_parts(s))
        e, w = Vector((s * 0.16, -0.02 if s > 0 else -0.03, 0.33)), Vector((s * 0.165, -0.07, 0.26)) if s > 0 else \
            Vector((-0.17, -0.1, 0.27))
        d = (w - e).normalized()
        fp = [rod(e, w, 0.026, fur, r2=0.024, verts=10),
              torus(0.033, 0.011, e + d * 0.012, shirt, verts=14, minor=5)]
        # the paw: a broad spade, palm towards the body, four claws
        pc = w + d * 0.035
        pw = ell(pc, (0.03, 0.046, 0.05), paw, segs=14, rings=10)
        q = Vector((0, 0, -1)).rotation_difference(d)
        pw.data.transform(Matrix.Translation(pc) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pc))
        fp.append(pw)
        for k in range(4):
            off = Vector((0, -0.03 + 0.02 * k, 0))
            base = pc + q @ (off + Vector((0, 0, -0.035)))
            tip = pc + q @ (off * 1.1 + Vector((0, -0.008, -0.058)))
            fp.append(rod(base, tip, 0.0095, claw, r2=0.003, verts=6))
        rig.rigid("fore." + side, fp)

    # the nozzle in the right paw: a grip, a brass barrel and a flared bell, pointing forward
    nz = [rod((-0.17, -0.07, 0.27), (-0.17, -0.12, 0.275), 0.022, handle, verts=12),
          rod((-0.17, -0.12, 0.275), (-0.17, -0.27, 0.29), 0.014, brass, verts=12),
          torus(0.016, 0.005, (-0.17, -0.15, 0.278), brass, rot=(math.pi / 2, 0, 0), verts=12, minor=4),
          lathe_r([(0.016, 0.0), (0.02, -0.02), (0.032, -0.045), (0.034, -0.05), (0.028, -0.05), (0.012, -0.03)],
                  brass, segs=16, name="bell", smooth=40)]
    bell = nz[-1]
    bell.data.transform(Matrix.Translation((-0.17, -0.27, 0.29)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    rig.rigid("fore.R", nz)

    # the hose: from the tank's outlet round the right hip to the grip
    hose_pts = [Vector(p) for p in ((0.0, 0.215, 0.215), (-0.02, 0.21, 0.19), (-0.09, 0.15, 0.18),
                                    (-0.165, 0.06, 0.2), (-0.2, -0.02, 0.23), (-0.19, -0.06, 0.26),
                                    (-0.17, -0.07, 0.27))]
    from blastyard_bombers import smooth_path
    hp_s = smooth_path(hose_pts, 4)
    hose_o = tube(hp_s, [0.017] * len(hp_s), hose, verts=10, caps=False, name="hose")

    def w_hose(p):
        t = poly_param(p, hp_s)
        a = smoothstep(0.35, 0.9, t)
        b = smoothstep(0.0, 0.25, t)
        return {"body": (1 - b) + 1e-4, "hips": b * (1 - a) + 1e-4, "fore.R": a + 1e-4}
    rig.custom(w_hose, hose_o)

    # legs: overall legs with a rolled cuff, chunky brown boots
    for s, side in ((1, "L"), (-1, "R")):
        lg = [rod((s * 0.07, 0.0, 0.2), (s * 0.072, 0.0, 0.08), 0.042, over, r2=0.046, verts=12),
              torus(0.046, 0.012, (s * 0.072, 0.0, 0.088), over, verts=14, minor=5)]
        rig.rigid("leg." + side, lg)
        ft = [ell((s * 0.072, -0.03, 0.04), (0.05, 0.08, 0.042), boot, segs=16, rings=10),
              ell((s * 0.072, -0.085, 0.045), (0.04, 0.035, 0.035), boot, segs=12, rings=8),
              ell((s * 0.072, -0.03, 0.012), (0.053, 0.085, 0.014), sole, segs=16, rings=6),
              torus(0.04, 0.008, (s * 0.072, 0.0, 0.075), boot, verts=14, minor=4)]
        for v in ft[0].data.vertices:   # flat soles
            v.co.z = max(v.co.z, 0.004)
        rig.rigid("foot." + side, ft)
    rig.build("digger")
    nozzle = pin(rig, "nozzle", (-0.17, -0.325, 0.29), "fore.R")

    # ---- poses
    blink = {"%eye.L": (1, 1, 0.1), "%eye.R": (1, 1, 0.1)}
    happy = {"%eye.L": (1.05, 1, 0.4), "%eye.R": (1.05, 1, 0.4)}
    shut = {"%eye.L": (1.1, 1, 0.12), "%eye.R": (1.1, 1, 0.12)}
    wide = {"%eye.L": (1.12, 1, 1.18), "%eye.R": (1.12, 1, 1.18)}
    GL = 8.0   # glint scale while it flashes

    def glint(s):
        return {"%glint": (s * GL, 1, s * GL)} if s else {}

    # idle: breathing, a look round, one blink, a glint
    def idle_p(k, extra=None):
        a = 2 * math.pi * k
        return merge({"%body": (1 + 0.02 * math.sin(a), 1 + 0.02 * math.sin(a), 1 + 0.015 * math.sin(a)),
                      "head": (2 * math.sin(a), 0, 10 * math.sin(a) if 0.25 < k < 0.75 else 0),
                      "arm.L": (-2, -6 - 2 * math.sin(a), 0), "arm.R": (-4, 4, 0),
                      "plunger": (0, 0, 0), "@plunger": (0, 0, 0.004 * math.sin(a))},
                     extra or {})
    rig.action("idle", {0: idle_p(0), 10: idle_p(1 / 6), 20: idle_p(1 / 3), 24: idle_p(0.4, glint(1)),
                        27: idle_p(0.45), 30: idle_p(0.5), 40: idle_p(2 / 3), 46: idle_p(46 / 60),
                        48: idle_p(0.8, blink), 50: idle_p(50 / 60), 60: idle_p(1)}, loop=True)

    # walk: 0.5 s; f0 left foot forward and planted, f4 passing (up), f8 right forward, f11 passing
    def walk_p(ph, up):
        sgn = 1 if ph == 0 else -1
        sw = 26 * sgn * (1 - up)
        return merge({"@root": (0, 0, 0.025 * up), "hips": (0, 0, 5 * sgn), "body": (6, 0, -4 * sgn),
                      "head": (-3 + 3 * up, 0, -2 * sgn),
                      "leg.L": (-sw, 0, 0), "leg.R": (sw, 0, 0),
                      "foot.L": (sw * 0.4 if sgn > 0 else 0, 0, 0), "foot.R": (-sw * 0.4 if sgn < 0 else 0, 0, 0),
                      "@leg.L": (0, 0, 0.03 * up * (sgn < 0)), "@leg.R": (0, 0, 0.03 * up * (sgn > 0)),
                      "arm.L": (34 * sgn * (1 - up), -6, 0), "fore.L": (-10, 0, 0),
                      "arm.R": (-8 * sgn * (1 - up), 4, 0), "@plunger": (0, 0, 0.01 * up)})
    rig.action("walk", {0: walk_p(0, 0), 4: walk_p(0, 1), 8: walk_p(1, 0), 11: walk_p(1, 1), 15: walk_p(0, 0)},
               loop=True)

    # dig: 0.5 s; leaning in, the paws claw in turn (reach forward and up, rake down and back), steps, the lamp
    # glints; the right forearm turns against the arm so the nozzle stays roughly level
    def dig_p(k, gl=0.0):
        a = 2 * math.pi * k
        reachL = math.sin(a)          # 1: left paw forward and up, -1: raked back
        reachR = -reachL
        armL, armR = -70 - 32 * reachL, -70 - 32 * reachR
        return merge({"@root": (0, 0, 0.015 * abs(math.sin(a))), "hips": (6, 0, 4 * math.sin(a)),
                      "body": (14, 0, -8 * math.sin(a)), "head": (-12, 0, 5 * math.sin(a)),
                      "arm.L": (armL, -10, 0), "fore.L": (-20 - 25 * reachL, 0, 0),
                      "arm.R": (armR, 10, 0), "fore.R": (-0.55 * (armR + 40), 0, 0),
                      "leg.L": (-18 * math.sin(a), 0, 0), "leg.R": (18 * math.sin(a), 0, 0),
                      "@leg.L": (0, 0, 0.02 * max(0.0, -math.cos(a))),
                      "@leg.R": (0, 0, 0.02 * max(0.0, math.cos(a)))},
                     glint(gl), {"%eye.L": (1.05, 1, 0.85), "%eye.R": (1.05, 1, 0.85)})
    rig.action("dig", {0: dig_p(0), 2: dig_p(2 / 15), 4: dig_p(4 / 15, 0.6), 5: dig_p(5 / 15, 1.0),
                       6: dig_p(6 / 15, 0.3), 8: dig_p(8 / 15), 10: dig_p(10 / 15), 12: dig_p(12 / 15),
                       15: dig_p(1)}, loop=True)

    # pump: 0.3 s, a squat and heave; the plunger rams down
    heave = merge({"@root": (0, 0, -0.03), "hips": (0, 0, 0), "body": (12, 0, 0), "head": (-6, 0, 0),
                   "leg.L": (-25, 0, 0), "leg.R": (-25, 0, 0), "foot.L": (25, 0, 0), "foot.R": (25, 0, 0),
                   "@plunger": (0, 0, -0.075), "%body": (1.04, 1.04, 0.96),
                   "arm.L": (-25, -8, 0), "fore.L": (-25, 0, 0), "arm.R": (-12, 4, 0), "fore.R": (8, 0, 0)},
                  {"%eye.L": (1.08, 1, 0.55), "%eye.R": (1.08, 1, 0.55)})
    rig.action("pump", {0: {}, 3: heave, 4: merge(heave, {"@plunger": (0, 0, -0.08)}), 7: {"@plunger": (0, 0, 0.01)},
                        9: {}})

    # shoot: wind back, then the nozzle thrust forward with a lunge (the forearm keeps it level)
    wind = merge({"body": (-6, 0, 8), "head": (4, 0, 0), "arm.R": (25, 10, 0), "fore.R": (-20, 0, 0),
                  "arm.L": (20, -10, 0), "@root": (0, 0.0, -0.01)})
    thrust = merge({"body": (12, 0, -6), "hips": (4, 0, 0), "head": (-8, 0, 0), "@root": (0, -0.03, 0.0),
                    "arm.R": (-72, 4, 0), "fore.R": (66, 0, 0), "arm.L": (30, -14, 0), "fore.L": (-20, 0, 0),
                    "leg.L": (-25, 0, 0), "leg.R": (18, 0, 0)}, wide)
    rig.action("shoot", {0: {}, 3: wind, 6: thrust, 8: merge(thrust, {"arm.R": (-68, 4, 0), "fore.R": (62, 0, 0)}),
                         12: {}})

    # die: a jolt, dizzy wobbles, the knees go, then a splat: squashed flat as a pancake (holds the last frame)
    jolt = merge({"@root": (0, 0, 0.06), "%body": (0.95, 0.95, 1.08), "arm.L": (-10, -70, 0),
                  "arm.R": (-10, 70, 0), "head": (8, 0, 0)}, wide)

    def dizzy(k, sag=0.0):
        a = 2 * math.pi * k
        return merge({"hips": (6 * math.sin(a), 8 * math.cos(a), 0), "head": (10 * math.cos(a), 14 * math.sin(a), 0),
                      "body": (10 * sag, 0, 0), "@root": (0, 0, -0.03 * sag),
                      "arm.L": (0, -30 + 25 * sag, 0), "arm.R": (0, 30 - 25 * sag, 0),
                      "leg.L": (-30 * sag, -6, 0), "leg.R": (-30 * sag, 6, 0),
                      "foot.L": (30 * sag, 0, 0), "foot.R": (30 * sag, 0, 0)}, shut)

    def splat(sx, sz):
        return merge({"%root": (sx, sx, sz), "arm.L": (0, -85, 0), "arm.R": (0, 85, 0), "head": (6, 0, 0),
                      "leg.L": (0, -30, 0), "leg.R": (0, 30, 0), "foot.L": (-20, 0, 0), "foot.R": (-20, 0, 0)}, shut)
    rig.action("die", {0: {}, 3: jolt, 8: dizzy(0), 13: dizzy(0.25), 18: dizzy(0.5), 23: dizzy(0.75),
                       28: dizzy(1.0, 1.0), 31: splat(1.4, 0.28), 34: splat(1.22, 0.44), 37: splat(1.32, 0.34),
                       42: splat(1.3, 0.36)})

    # cheer: two hops, the left paw and the nozzle waved up
    def cheer_p(h, sq, wave):
        return merge({"@root": (0, 0, h), "%body": (1 + sq, 1 + sq, 1 - sq), "head": (-10, 0, 0),
                      "arm.L": (-15, -150 + wave, 0), "fore.L": (0, 0, 0), "arm.R": (-15, 150 - wave, 0),
                      "fore.R": (-10, 0, 0), "leg.L": (-15 * h / 0.08, 0, 0), "leg.R": (-15 * h / 0.08, 0, 0),
                      "foot.L": (20 * h / 0.08, 0, 0), "foot.R": (20 * h / 0.08, 0, 0)}, happy)
    rig.action("cheer", {0: cheer_p(0, 0.05, 0), 4: cheer_p(0.07, -0.03, 15), 8: cheer_p(0.08, 0, 25),
                         12: cheer_p(0.02, -0.02, 10), 15: cheer_p(0, 0.06, 0), 19: cheer_p(0.07, -0.03, 15),
                         23: cheer_p(0.08, 0, 25), 27: cheer_p(0.02, -0.02, 10), 30: cheer_p(0, 0.05, 0)}, loop=True)

    # climb: scrabbling up a shaft; the paws reach overhead in turn, the feet kick
    def climb_p(k):
        a = 2 * math.pi * k
        r = math.sin(a)
        return merge({"@root": (0, 0, 0.02 * math.sin(2 * a)), "body": (-4, 0, 6 * r), "head": (-14, 0, -4 * r),
                      "arm.L": (-150 + 28 * r, -22, 0), "fore.L": (-25 * max(0.0, r), 0, 0),
                      "arm.R": (-150 - 28 * r, 22, 0), "fore.R": (70 - 25 * max(0.0, -r), 0, 0),
                      "leg.L": (-40 * max(0.0, r) + 10, 0, 0), "leg.R": (-40 * max(0.0, -r) + 10, 0, 0),
                      "foot.L": (30 * max(0.0, r), 0, 0), "foot.R": (30 * max(0.0, -r), 0, 0),
                      "@leg.L": (0, 0, 0.04 * max(0.0, r)), "@leg.R": (0, 0, 0.04 * max(0.0, -r))})
    rig.action("climb", {f: climb_p(f / 15) for f in (0, 2, 4, 6, 8, 10, 12, 15)}, loop=True)
    rig.save("digger", extra=[nozzle])


# ------------------------------------------------------------------ enemies: shared bits

def eyes_node(rig, parts, bone):
    """Joins the eye parts (build frame) into the separate mesh "eyes", turned with the rig, carried by `bone`."""
    o = join(parts, "eyes")
    rig.turn(o)
    return attach(rig, o, bone)


def critter_eyes(c, r, yaw, white, pupil, shine, lid=None, look=(0.0, 0.0)):
    """One big round eye at c (radii r) turned by yaw: the white, a big pupil, two catch lights."""
    out = [ell(c, r, white, yaw=yaw, segs=20, rings=14)]
    R = Matrix.Rotation(math.radians(yaw), 3, "Z")
    pc = Vector(c) + R @ Vector((look[0] * r[0], -r[1] * 0.78, look[1] * r[2] - 0.08 * r[2]))
    out.append(ell(pc, (r[0] * 0.56, r[1] * 0.32, r[2] * 0.58), pupil, yaw=yaw, segs=16, rings=10))
    out.append(sphere(r[0] * 0.2, pc + R @ Vector((r[0] * 0.2, -r[1] * 0.3, r[2] * 0.24)), shine, segs=8, rings=6))
    out.append(sphere(r[0] * 0.09, pc + R @ Vector((-r[0] * 0.22, -r[1] * 0.28, -r[2] * 0.22)), shine, segs=6,
                      rings=4))
    return out


# ------------------------------------------------------------------ the puffer

def puffer():
    reset()
    fur = mat("puffer_fur", (0.6, 0.42, 0.86), 0.7, coat=0.15)
    tummy = mat("puffer_tummy", (1.0, 0.84, 0.64), 0.65)
    cheek = mat("puffer_cheek", (1.0, 0.48, 0.62), 0.6)
    mouth = mat("puffer_mouth", (0.32, 0.05, 0.12), 0.5)
    tooth = mat("puffer_tooth", (1.0, 0.98, 0.92), 0.3, coat=0.5)
    feet = mat("puffer_feet", (1.0, 0.56, 0.16), 0.45, coat=0.4)
    white = mat("puffer_eye_white", (0.99, 0.98, 0.95), 0.2, coat=0.9)
    pupil = mat("puffer_pupil", (0.05, 0.03, 0.12), 0.15, coat=1.0)
    shine = mat("puffer_eye_glow", (1.0, 1.0, 1.0), 0.1, emit=4.0)

    bones = {"root": ((0, 0, 0), (0, 0, 0.04), None),
             "body": ((0, 0, 0.05), (0, 0, 0.38), "root"),
             "top": ((0, 0, 0.38), (0, 0, 0.68), "body"),
             "eyes": ((0, -0.2, 0.44), (0, -0.3, 0.44), "body"),
             "foot.L": ((0.12, -0.02, 0.07), (0.13, -0.1, 0.02), "root"),
             "foot.R": ((-0.12, -0.02, 0.07), (-0.13, -0.1, 0.02), "root")}
    rig = TurnRig(bones, 90, fps=FPS)

    # the dumpling: a soft round body, pleated and pinched to a twisted knot at the top, with a curl
    NP = 9   # pleats

    def radial(k, z):
        t = smoothstep(0.36, 0.66, z)
        return 1.0 + 0.07 * t * math.cos(NP * 2 * math.pi * k / 36)
    prof = [(0.0, 0.69), (0.03, 0.688), (0.07, 0.675), (0.13, 0.64), (0.2, 0.58), (0.26, 0.5), (0.297, 0.41),
            (0.31, 0.32), (0.305, 0.23), (0.285, 0.15), (0.245, 0.085), (0.17, 0.05), (0.08, 0.04), (0.0, 0.04)]
    body = lathe_r(prof, fur, segs=36, radial=radial, name="dumpling", smooth=70)
    for v in body.data.vertices:   # the pleats twist a little as they rise
        t = smoothstep(0.36, 0.69, v.co.z)
        a = 0.35 * t
        x, y = v.co.x, v.co.y
        v.co.x, v.co.y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        v.co.y *= 0.93
    body.data.update()
    parts = [body]
    # a cream tummy patch on the front
    tm = ell((0, -0.2, 0.2), (0.17, 0.11, 0.15), tummy, segs=22, rings=14)
    parts.append(tm)
    # blushing cheeks, a small open smile with a buck tooth
    for s in (-1, 1):
        ch = ell((s * 0.17, -0.235, 0.33), (0.05, 0.02, 0.032), cheek, yaw=-s * 38, segs=12, rings=8)
        parts.append(ch)
    sm = []
    for k in range(9):
        a = math.pi * (1.12 + 0.76 * k / 8)
        x = 0.06 * math.cos(a)
        z = 0.33 + 0.035 * math.sin(a)
        sm.append((x, -0.29 + 0.25 * x * x, z))
    parts.append(tube(sm, [0.008, 0.011, 0.014, 0.016, 0.017, 0.016, 0.014, 0.011, 0.008], mouth, verts=6,
                      caps=True, name="smile"))
    parts.append(K.box((0.026, 0.012, 0.026), (0.0, -0.288, 0.298), tooth, bevel=0.005))
    # little nub arms
    for s in (-1, 1):
        parts.append(ell((s * 0.29, -0.08, 0.22), (0.038, 0.035, 0.05), fur, roll=s * 30, segs=12, rings=8))
    def w_body(p):
        t = smoothstep(0.3, 0.55, p.z)
        return {"body": 1 - t + 1e-4, "top": t + 1e-4}
    rig.custom(w_body, parts)
    # the twisted knot and the curl on top
    curl = [tube([(0, 0.0, 0.66), (0.0, 0.0, 0.72), (0.03, -0.01, 0.77), (0.065, 0.0, 0.79), (0.08, 0.02, 0.76),
                  (0.065, 0.03, 0.735)], [0.04, 0.034, 0.028, 0.022, 0.017, 0.012], fur, verts=12, caps=True,
                 name="curl")]
    rig.rigid("top", curl)
    # tiny orange feet
    for s, side in ((1, "L"), (-1, "R")):
        ft = ell((s * 0.12, -0.06, 0.035), (0.06, 0.085, 0.04), feet, segs=14, rings=8)
        for v in ft.data.vertices:
            v.co.z = max(v.co.z, 0.003)
        toes = [sphere(0.018, (s * 0.12 + dx, -0.135, 0.03), feet, segs=8, rings=6) for dx in (-0.03, 0.0, 0.03)]
        rig.rigid("foot." + side, ft, toes)
    rig.build("body")
    rig.arm.name = rig.arm.data.name = "puffer_rig"

    eyes = []
    for s in (-1, 1):
        th = math.radians(46)
        eyes += critter_eyes((s * 0.255 * math.sin(th), -0.255 * math.cos(th) * 0.95, 0.45), (0.085, 0.055, 0.095),
                             s * 46, white, pupil, shine, look=(-s * 0.3, 0.0))
    eyes = eyes_node(rig, eyes, "eyes")

    # ---- animations
    def eyes_s(sx, sz=None):
        return {"%eyes": (sx, 1, sz if sz is not None else sx)}

    # walk: a bouncy waddle, 0.6 s; f0 left foot forward
    def walk_p(ph, up):
        sgn = 1 if ph == 0 else -1
        return merge({"@root": (0, 0, 0.035 * up), "body": (6, 7 * sgn * (1 - up), 0),
                      "top": (-6 * up, -6 * sgn * (1 - up), 0),
                      "%body": (1 + 0.05 * (1 - up), 1 + 0.05 * (1 - up), 1 - 0.06 * (1 - up) + 0.03 * up),
                      "foot.L": (-30 * sgn * (1 - up), 0, 0), "foot.R": (30 * sgn * (1 - up), 0, 0),
                      "@foot.L": (0, -0.04 * sgn * (1 - up), 0.03 * up * (sgn < 0)),
                      "@foot.R": (0, 0.04 * sgn * (1 - up), 0.03 * up * (sgn > 0))})
    rig.action("walk", {0: walk_p(0, 0), 4: walk_p(0, 1), 9: walk_p(1, 0), 13: walk_p(1, 1), 18: walk_p(0, 0)},
               loop=True)

    # ghost: the eyes drift and bob, look about, a slow blink (the body is hidden by the game)
    def ghost_p(k, blink=1.0):
        a = 2 * math.pi * k
        return merge({"@eyes": (0.03 * math.sin(a), 0, 0.03 * math.sin(2 * a)),
                      "eyes": (8 * math.sin(2 * a), 0, 18 * math.sin(a))}, eyes_s(1.0, blink))
    rig.action("ghost", {0: ghost_p(0), 5: ghost_p(1 / 6), 10: ghost_p(1 / 3), 15: ghost_p(0.5),
                         19: ghost_p(19 / 30), 21: ghost_p(0.7, 0.1), 23: ghost_p(23 / 30), 25: ghost_p(5 / 6),
                         30: ghost_p(1)}, loop=True)

    # inflate: four puffs (f1-4, f8-11, f16-19, f23-26), each held; the feet splay, the eyes bulge
    def infl(sc, k):
        return merge({"%body": (sc, sc, sc), "foot.L": (0, -12 * k, 0), "foot.R": (0, 12 * k, 0),
                      "@foot.L": (0.02 * k, 0, 0), "@foot.R": (-0.02 * k, 0, 0)},
                     eyes_s(1 + 0.07 * k))
    steps = [1.0, 1.18, 1.36, 1.55, 1.75]
    ik = {0: infl(1.0, 0)}
    for i in range(1, 5):
        f0 = [1, 8, 16, 23][i - 1]
        ik[f0 + 2] = infl(steps[i] + 0.04, i)
        ik[f0 + 3] = infl(steps[i], i)
        hold = [7, 15, 22, 30][i - 1]
        ik[hold] = infl(steps[i], i)
    rig.action("inflate", ik)

    # pop: a last over-swell, a shudder and gone
    rig.action("pop", {0: infl(1.75, 4), 3: merge(infl(2.0, 4), {"body": (0, 6, 0)}),
                       5: merge(infl(2.1, 4), {"body": (0, -6, 0)}), 7: {"%root": (0.0, 0.0, 0.0)},
                       9: {"%root": (0.0, 0.0, 0.0)}})

    # stunned: a dizzy sway, eyes squeezed shut
    def stun_p(k):
        a = 2 * math.pi * k
        return merge({"body": (6 * math.cos(a), 10 * math.sin(a), 0), "top": (8 * math.cos(a), 8 * math.sin(a), 0),
                      "%body": (1.04, 1.04, 0.95), "eyes": (0, 0, 10 * math.sin(2 * a))},
                     eyes_s(1.05, 0.22))
    rig.action("stunned", {f: stun_p(f / 30) for f in (0, 5, 10, 15, 20, 25, 30)}, loop=True)
    rig.save("puffer", extra=[eyes])


# ------------------------------------------------------------------ the drake

def drake():
    reset()
    scale_m = mat("drake_scale", (0.28, 0.66, 0.24), 0.5, coat=0.35)
    belly = mat("drake_belly", (0.99, 0.88, 0.58), 0.55, coat=0.2)
    spine = mat("drake_spine", (1.0, 0.5, 0.12), 0.45, coat=0.4)
    wing = mat("drake_wing", (1.0, 0.62, 0.2), 0.55)
    nostril = mat("drake_nostril", (0.08, 0.2, 0.06), 0.6)
    mouth = mat("drake_mouth", (0.45, 0.06, 0.08), 0.5)
    tooth = mat("drake_tooth", (1.0, 0.98, 0.9), 0.3, coat=0.5)
    claw = mat("drake_claw", (0.98, 0.94, 0.84), 0.35, coat=0.5)
    white = mat("drake_eye_white", (0.99, 0.98, 0.93), 0.2, coat=0.9)
    pupil = mat("drake_pupil", (0.06, 0.03, 0.02), 0.15, coat=1.0)
    shine = mat("drake_eye_glow", (1.0, 1.0, 1.0), 0.1, emit=4.0)

    HC = Vector((0, -0.1, 0.53))
    bones = {"root": ((0, 0, 0), (0, 0, 0.04), None),
             "body": ((0, 0.04, 0.1), (0, 0.0, 0.38), "root"),
             "neck": ((0, 0.0, 0.38), (0, -0.06, 0.46), "body"),
             "head": ((0, -0.06, 0.46), (0, -0.1, 0.7), "neck"),
             "jaw": ((0, -0.12, 0.47), (0, -0.33, 0.44), "head"),
             "eyes": ((0, -0.18, 0.62), (0, -0.28, 0.62), "head"),
             "wing.L": ((0.08, 0.16, 0.4), (0.24, 0.24, 0.5), "body"),
             "wing.R": ((-0.08, 0.16, 0.4), (-0.24, 0.24, 0.5), "body"),
             "tail": ((0, 0.18, 0.14), (0, 0.32, 0.12), "body"),
             "tail2": ((0, 0.32, 0.12), (0, 0.42, 0.24), "tail"),
             "leg.L": ((0.1, 0.02, 0.15), (0.11, -0.01, 0.03), "root"),
             "leg.R": ((-0.1, 0.02, 0.15), (-0.11, -0.01, 0.03), "root")}
    rig = TurnRig(bones, 90, fps=FPS)

    # a chubby pear body leaning a touch forward, a cream belly with plates
    bd = ell((0, 0.04, 0.27), (0.19, 0.2, 0.21), scale_m, segs=28, rings=18)
    bl = ell((0, -0.07, 0.25), (0.14, 0.12, 0.17), belly, segs=22, rings=14)
    plates = []
    for k, z in enumerate((0.13, 0.19, 0.25, 0.31, 0.37)):
        w = 0.13 * math.sqrt(max(0.0, 1 - ((z - 0.25) / 0.18) ** 2))
        pts = []
        for j in range(9):
            x = -w + 2 * w * j / 8
            y = -0.07 - 0.12 * math.sqrt(max(0.0, 1 - (x / 0.14) ** 2 - ((z - 0.25) / 0.17) ** 2)) - 0.003
            pts.append((x, y, z))
        plates.append(tube(pts, [0.006] * 9, belly, verts=5, caps=True, name="plate"))
    # tiny arms with three claws
    arms = []
    for s in (-1, 1):
        a0, a1 = Vector((s * 0.15, -0.06, 0.33)), Vector((s * 0.17, -0.15, 0.27))
        arms += [rod(a0, a1, 0.03, scale_m, r2=0.026, verts=10), sphere(0.032, a1, scale_m, segs=10, rings=8)]
        for dx in (-0.015, 0.0, 0.015):
            arms.append(cone(a1 + Vector((dx, -0.015, -0.01)), a1 + Vector((dx * 1.5, -0.04, -0.03)), 0.008, claw,
                             verts=6))

    def w_body(p):
        t = smoothstep(0.36, 0.46, p.z)
        return {"body": 1 - t + 1e-4, "neck": t + 1e-4}
    rig.custom(w_body, bd, bl, plates, arms)

    # the head: round, a big friendly snout with nostrils, a lower jaw that opens, cheek frills
    hd = ell(HC, (0.155, 0.15, 0.14), scale_m, segs=26, rings=16)
    sn = ell((0, -0.235, 0.51), (0.112, 0.125, 0.066), scale_m, segs=22, rings=14)
    hp = [hd, sn]
    for s in (-1, 1):
        hp.append(ell((s * 0.04, -0.345, 0.53), (0.016, 0.01, 0.011), nostril, segs=8, rings=6))
        hp.append(ell((s * 0.04, -0.333, 0.535), (0.024, 0.02, 0.02), scale_m, segs=10, rings=6))   # nostril rims
        # cheek frills: three soft spikes
        for k in range(3):
            a = math.radians(-30 + 30 * k)
            base = Vector((s * 0.13, -0.05 + 0.03 * k, 0.5 + 0.03 * k))
            tip = base + Vector((s * 0.09 * math.cos(a), 0.06, 0.07 * math.sin(a) + 0.02))
            hp.append(cone(base, tip, 0.028, spine, verts=8))
    # two little fangs peeping down from the upper snout
    for s in (-1, 1):
        hp.append(cone((s * 0.055, -0.3, 0.462), (s * 0.055, -0.305, 0.43), 0.012, tooth, verts=6))
    # the crest of soft orange spines over the head and down the back
    crest = []
    for k, (y, z, h) in enumerate(((-0.14, 0.68, 0.09), (-0.06, 0.69, 0.1), (0.03, 0.66, 0.085))):
        crest.append(cone((0, y, z - 0.03), (0, y + 0.04, z + h), 0.038, spine, verts=10))
    hp += crest
    # little horns
    for s in (-1, 1):
        hp.append(tube([(s * 0.08, -0.04, 0.64), (s * 0.11, 0.0, 0.7), (s * 0.12, 0.05, 0.72)], [0.022, 0.014, 0.004],
                       belly, verts=8, caps=True, name="horn"))
    rig.rigid("head", hp)
    back = []
    for k, (y, z, h) in enumerate(((0.12, 0.44, 0.07), (0.19, 0.36, 0.065), (0.23, 0.27, 0.055),
                                   (0.24, 0.18, 0.045))):
        d = Vector((0, 0.7, 0.7 - 0.25 * k)).normalized()
        crest_b = cone((0, y - 0.02, z), Vector((0, y, z)) + d * h, 0.032 - 0.004 * k, spine, verts=10)
        back.append(crest_b)
    rig.rigid("body", back)
    # the jaw: a rounded lower jaw, its inside dark red, a pink tongue
    jw = ell((0, -0.215, 0.44), (0.098, 0.115, 0.042), scale_m, segs=20, rings=10)
    inside = ell((0, -0.215, 0.462), (0.085, 0.1, 0.014), mouth, segs=16, rings=6)
    tongue = ell((0, -0.235, 0.47), (0.045, 0.065, 0.012), mat("drake_tongue", (1.0, 0.45, 0.5), 0.4), segs=12, rings=6)
    for s in (-1, 1):   # two lower teeth
        jw = [jw] if not isinstance(jw, list) else jw
        jw.append(cone((s * 0.035, -0.3, 0.462), (s * 0.035, -0.302, 0.485), 0.01, tooth, verts=6))
    rig.rigid("jaw", jw, inside, tongue)
    # the mouth's dark inside on the upper side too (seen when it opens)
    rig.rigid("head", ell((0, -0.22, 0.47), (0.095, 0.105, 0.014), mouth, segs=16, rings=6))

    # wings: little bat wings, orange membranes on green fingers
    for s, side in ((1, "L"), (-1, "R")):
        poly = [(0.0, 0.0), (0.1, 0.07), (0.2, 0.14), (0.24, 0.12), (0.2, 0.06), (0.16, 0.07), (0.13, 0.01),
                (0.09, 0.03), (0.05, -0.04)]
        pts = []
        for x, z in poly:
            pts.append(Vector((s * (0.08 + x), 0.17 + x * 0.45, 0.39 + z)))
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in pts]
        bm.faces.new(vs if s > 0 else vs[::-1])
        mem = new_obj("wing", bm, wing, smooth=0)
        K.select(mem)
        sm_ = mem.modifiers.new("s", "SOLIDIFY")
        sm_.thickness = 0.008
        bpy.ops.object.modifier_apply(modifier=sm_.name)
        fingers = [tube([pts[0], pts[1], pts[2], pts[3]], [0.012, 0.01, 0.008, 0.004], scale_m, verts=6, caps=True,
                        name="finger")]
        for i in (5, 7):
            fingers.append(rod(pts[2] if i == 5 else pts[1], pts[i - 1], 0.006, scale_m, r2=0.003, verts=5))
        rig.rigid("wing." + side, mem, fingers)

    # the tail: thick, curling up, with a spade tip
    tp = [Vector(p) for p in ((0, 0.16, 0.16), (0, 0.26, 0.11), (0, 0.34, 0.11), (0, 0.41, 0.16), (0, 0.43, 0.23),
                              (0, 0.41, 0.28))]
    from blastyard_bombers import smooth_path
    tps = smooth_path(tp, 4)
    rad = [0.085 - 0.07 * (i / (len(tps) - 1)) for i in range(len(tps))]
    tail = tube(tps, rad, scale_m, verts=14, caps=True, name="tail")
    tip = K.prism([(-0.05, 0.0), (0.0, -0.03), (0.05, 0.0), (0.0, 0.07)], 0.02, (0, 0.0, 0.0), spine, bevel=0.008)
    tip.data.transform(Matrix.Translation((0, 0.405, 0.29)) @ Matrix.Rotation(math.pi / 2, 4, "Z")
                       @ Matrix.Rotation(math.radians(-20), 4, "Y"))

    def w_tail(p):
        t = poly_param(p, tps)
        a = smoothstep(0.0, 0.2, t)
        b = smoothstep(0.4, 0.7, t)
        return {"body": 1 - a + 1e-4, "tail": a * (1 - b) + 1e-4, "tail2": b + 1e-4}
    rig.custom(w_tail, tail)
    rig.rigid("tail2", tip)

    # stubby legs and three-toed feet
    for s, side in ((1, "L"), (-1, "R")):
        lg = [ell((s * 0.11, 0.02, 0.12), (0.07, 0.08, 0.08), scale_m, segs=14, rings=10),
              ell((s * 0.11, -0.04, 0.035), (0.065, 0.09, 0.04), scale_m, segs=14, rings=8)]
        for v in lg[1].data.vertices:
            v.co.z = max(v.co.z, 0.003)
        for dx in (-0.03, 0.0, 0.03):
            lg.append(cone((s * 0.11 + dx, -0.11, 0.03), (s * 0.11 + dx * 1.2, -0.15, 0.015), 0.013, claw, verts=6))
        rig.rigid("leg." + side, lg)
    rig.build("body")
    rig.arm.name = rig.arm.data.name = "drake_rig"

    eyes = []
    for s in (-1, 1):
        eyes += critter_eyes((s * 0.075, -0.2, 0.615), (0.06, 0.04, 0.072), -s * 24, white, pupil, shine)
        # a heavy lid line gives a cheeky look
        lid = hemi(0.068, (0, 0, 0), (0, 0, 1), scale_m, cut=0.5, segs=16, rings=10)
        lid.data.transform(Matrix.Translation((s * 0.075, -0.198, 0.62)) @ Matrix.Rotation(math.radians(-s * 24), 4, "Z")
                           @ Matrix.Diagonal((0.95, 0.7, 1.15, 1)) @ Matrix.Rotation(math.radians(-s * 22), 4, "Y"))
        eyes.append(lid)
    eyes = eyes_node(rig, eyes, "eyes")
    mouth_e = pin(rig, "mouth", (0, -0.36, 0.47), "head")

    def eyes_s(sx, sz=None):
        return {"%eyes": (sx, 1, sz if sz is not None else sx)}

    # walk: a stubby waddle, 0.6 s, wings fluttering, tail swinging
    def walk_p(ph, up, k):
        sgn = 1 if ph == 0 else -1
        a = 2 * math.pi * k
        return merge({"@root": (0, 0, 0.03 * up), "body": (4, 6 * sgn * (1 - up), 0), "neck": (-4, 0, 0),
                      "head": (3 * up, -4 * sgn * (1 - up), 0),
                      "leg.L": (-30 * sgn * (1 - up), 0, 0), "leg.R": (30 * sgn * (1 - up), 0, 0),
                      "@leg.L": (0, 0, 0.03 * up * (sgn < 0)), "@leg.R": (0, 0, 0.03 * up * (sgn > 0)),
                      "tail": (0, 0, 14 * sgn * (1 - up)), "tail2": (0, 0, -10 * sgn * (1 - up)),
                      "jaw": (0, 0, 0)},
                     mirror({"wing.L": (0, -25 * math.sin(2 * a), 15 * math.sin(2 * a))}))
    rig.action("walk", {0: walk_p(0, 0, 0), 4: walk_p(0, 1, 4 / 18), 9: walk_p(1, 0, 0.5), 13: walk_p(1, 1, 13 / 18),
                        18: walk_p(0, 0, 1)}, loop=True)

    def ghost_p(k, blink=1.0):
        a = 2 * math.pi * k
        return merge({"@eyes": (0.03 * math.sin(a), 0, 0.03 * math.sin(2 * a)),
                      "eyes": (8 * math.sin(2 * a), 0, 18 * math.sin(a))}, eyes_s(1.0, blink))
    rig.action("ghost", {0: ghost_p(0), 5: ghost_p(1 / 6), 10: ghost_p(1 / 3), 15: ghost_p(0.5),
                         19: ghost_p(19 / 30), 21: ghost_p(0.7, 0.1), 23: ghost_p(23 / 30), 25: ghost_p(5 / 6),
                         30: ghost_p(1)}, loop=True)

    # breathe: rears back, then lunges with the jaw wide
    rear = merge({"body": (-14, 0, 0), "neck": (-10, 0, 0), "head": (-16, 0, 0), "jaw": (-4, 0, 0),
                  "tail": (12, 0, 0), "@root": (0, 0.02, 0.02), "%body": (0.96, 0.96, 1.06)},
                 mirror({"wing.L": (0, -40, 20)}), eyes_s(1.1, 1.15))
    lunge = merge({"body": (10, 0, 0), "neck": (4, 0, 0), "head": (-16, 0, 0), "jaw": (40, 0, 0),
                   "tail": (-10, 0, 0), "@root": (0, -0.03, 0.0), "%body": (1.05, 1.05, 0.95)},
                  mirror({"wing.L": (0, 25, -10)}), eyes_s(1.08, 0.5))
    rig.action("breathe", {0: {}, 8: rear, 12: lunge, 15: merge(lunge, {"jaw": (36, 0, 0)}), 18: {}})

    def stun_p(k):
        a = 2 * math.pi * k
        return merge({"body": (4 * math.cos(a), 8 * math.sin(a), 0), "head": (10 * math.cos(a), 10 * math.sin(a), 0),
                      "jaw": (10, 0, 0), "tail": (-10, 0, 0)},
                     mirror({"wing.L": (20, 30, 0)}), eyes_s(1.05, 0.22))
    rig.action("stunned", {f: stun_p(f / 30) for f in (0, 5, 10, 15, 20, 25, 30)}, loop=True)
    rig.save("drake", extra=[eyes, mouth_e])


# ------------------------------------------------------------------ the rock

def two_tone(o, top_mat, test=lambda n, c: n.z > 0.55):
    """Gives the faces that pass test(normal, centre) a second material."""
    o.data.materials.append(top_mat)
    for f in o.data.polygons:
        if test(f.normal, f.center):
            f.material_index = len(o.data.materials) - 1
    return o


def boulder(r, scale, seed, amount, stone, light, sub=3, smooth=32, flat=0.12):
    """A lumpy boulder (low-frequency bumps, flattened underneath) resting on z = 0."""
    o = ico(r, (0, 0, 0), stone, sub=sub, smooth=smooth)
    rnd = random.Random(seed)
    bumps = [(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized(),
              rnd.uniform(-amount, amount), rnd.uniform(0.35, 0.7)) for _ in range(14)]
    for v in o.data.vertices:
        d = v.co.normalized()
        k = 1.0 + sum(a * max(0.0, d.dot(b) - (1 - w)) / w for b, a, w in bumps)
        v.co = v.co * k
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    zmin = min(v.co.z for v in o.data.vertices)
    for v in o.data.vertices:
        if v.co.z < zmin + flat * r:
            v.co.z = zmin + flat * r
    zmin = min(v.co.z for v in o.data.vertices)
    for v in o.data.vertices:
        v.co.z -= zmin
    o.data.update()
    K.select(o)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth))
    return two_tone(o, light)


def rock():
    reset()
    stone = mat("rock_stone", (0.34, 0.29, 0.26), 0.75)
    light = mat("rock_light", (0.5, 0.44, 0.37), 0.7)
    crack_m = mat("rock_crack", (0.1, 0.07, 0.06), 0.9)
    body = boulder(0.5, (0.95, 0.82, 1.04), 32, 0.2, stone, light, smooth=24)
    # fit it to 0.95 across
    xs = [v.co.x for v in body.data.vertices]
    k = 0.95 / (max(xs) - min(xs))
    cx = (max(xs) + min(xs)) / 2
    for v in body.data.vertices:
        v.co.x = (v.co.x - cx) * k
        v.co.y *= k
        v.co.z *= k
    body.data.update()
    # a few embedded pebbles and a fossil swirl for character
    rnd = random.Random(7)
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())

    def surf(x, z, off=0.0):
        hit = bvh.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
        return None if hit[0] is None else hit[0] + hit[1] * off

    parts = [body]
    for x, z, r in ((0.22, 0.2, 0.035), (-0.28, 0.42, 0.028), (0.05, 0.62, 0.025), (-0.12, 0.13, 0.03)):
        p = surf(x, z, -0.01)
        if p:
            parts.append(lumpy(r, p, light, rnd.randint(0, 999), amount=0.2, sub=1))
    sw = []
    for i in range(14):
        a = i * 0.55
        rr = 0.012 + 0.0045 * i
        p = surf(-0.15 + rr * math.cos(a), 0.36 + rr * math.sin(a), 0.002)
        if p:
            sw.append(p)
    parts.append(tube(sw, [0.007] * len(sw), light, verts=5, caps=True, name="fossil"))
    root = join(parts, "rock")
    # the cracks: dark fissures branching down the face, shown while it wobbles
    lines = [[(0.02, 0.86), (-0.04, 0.74), (0.03, 0.62), (-0.03, 0.5), (0.04, 0.38), (0.0, 0.27)],
             [(0.03, 0.62), (0.13, 0.56), (0.17, 0.46), (0.27, 0.41)],
             [(-0.03, 0.5), (-0.14, 0.45), (-0.2, 0.34)],
             [(0.04, 0.38), (0.1, 0.3), (0.09, 0.2)]]
    cr = []
    for ln in lines:
        pts = []
        for a, b in zip(ln, ln[1:]):
            for t in (0.0, 0.25, 0.5, 0.75):
                x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                p = surf(x, z * 0.98, 0.004)
                if p:
                    pts.append(p)
        p = surf(ln[-1][0], ln[-1][1] * 0.98, 0.004)
        if p:
            pts.append(p)
        n = len(pts)
        ln_o = tube(pts, [0.01 * (1 - 0.5 * i / max(1, n - 1)) for i in range(n)], crack_m, verts=6, caps=True,
                    name="crack_line")
        for v in ln_o.data.vertices:   # pressed into the face: flat, dark grooves
            v.co.y = -1.0 + (v.co.y + 1.0)
            hit = bvh.find_nearest(v.co)
            if hit[0] is not None:
                v.co = hit[0] + (v.co - hit[0]) * 0.35 + hit[1] * 0.002
        ln_o.data.update()
        cr.append(ln_o)
    crack = join(cr, "crack")
    export(root, "rock", children=[(crack, root)])


def rock_shard():
    reset()
    stone = mat("rock_stone", (0.34, 0.29, 0.26), 0.75)
    light = mat("rock_light", (0.5, 0.44, 0.37), 0.7)
    o = lumpy(0.13, (0, 0, 0), stone, 11, amount=0.28, scale=(1.1, 0.75, 0.7), sub=1, smooth=0)
    two_tone(o, light)
    o.name = o.data.name = "rock_shard"
    export(o, "rock_shard")


# ------------------------------------------------------------------ bonus vegetables (glossy, ~0.6 tall)

def leaf(base, tip, w, material, bend=0.0, twist=0.0, n=7, name="leaf"):
    """A pointed, slightly cupped leaf from base to tip, `w` wide, bent by `bend` (towards -Y)."""
    a, b = Vector(base), Vector(tip)
    d = (b - a)
    L = d.length
    d.normalize()
    side = d.cross(Vector((0, -1, 0)))
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    side = Matrix.Rotation(twist, 3, d) @ side
    nrm = side.cross(d)
    rows = []
    for i in range(n + 1):
        t = i / n
        c = a + d * L * t + nrm * bend * math.sin(math.pi * t)
        hw = w * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.8 * (1 - 0.15 * t)
        rows.append([c - side * hw + nrm * 0.25 * hw, c, c + side * hw + nrm * 0.25 * hw])
    from fuseflight_models import sheet
    o = sheet(rows, material, name)
    K.select(o)
    m = o.modifiers.new("s", "SOLIDIFY")
    m.thickness = 0.006
    m.offset = 0
    bpy.ops.object.modifier_apply(modifier=m.name)
    return o


def gloss(name, color, rough=0.25):
    return mat(name, color, rough, coat=0.9)


def veg_carrot():
    reset()
    root_m = gloss("veg_carrot_root", (1.0, 0.42, 0.06))
    ring = gloss("veg_carrot_ring", (0.92, 0.34, 0.05))
    green = gloss("veg_carrot_leaf", (0.25, 0.7, 0.2), 0.35)
    prof = [(0.0, 0.43), (0.06, 0.428), (0.09, 0.415), (0.1, 0.39), (0.098, 0.33), (0.088, 0.25), (0.07, 0.17),
            (0.05, 0.1), (0.028, 0.045), (0.01, 0.01), (0.0, 0.0)]
    body = lathe_r(prof, root_m, segs=24, name="carrot", smooth=60)
    parts = [body]
    for z in (0.33, 0.26, 0.19, 0.12):   # the little growth rings
        r = 0.1 * (z / 0.39) ** 0.75 * 0.98
        pts = [(r * math.cos(a), r * math.sin(a), z + 0.004 * math.sin(3 * a)) for a in
               (math.radians(x) for x in range(-60, 61, 15))]
        parts.append(tube(pts, [0.005] * len(pts), ring, verts=5, caps=True, name="ring"))
    for k in range(5):   # a feathery top
        a = math.radians(-50 + 25 * k)
        tip = Vector((0.16 * math.sin(a), 0.02 * math.cos(3 * a), 0.43 + 0.17 * math.cos(a)))
        parts.append(rod((0, 0, 0.42), tip * 0.6 + Vector((0, 0, 0.17)), 0.01, green, verts=6))
        parts.append(leaf(tip * 0.45 + Vector((0, 0, 0.235)), tip + Vector((0, 0, 0.0)), 0.045, green, bend=0.02,
                          twist=0.4 * k))
    o = join(parts, "veg_carrot")
    o.data.transform(Matrix.Rotation(math.radians(-14), 4, "Y"))
    settle(o)
    export(o, "veg_carrot")


def settle(o):
    """Puts the lowest point on z = 0, centred on x and y."""
    vs = [v.co for v in o.data.vertices]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2
    o.data.transform(Matrix.Translation((-cx, -cy, -min(v.z for v in vs))))
    o.data.update()


def veg_turnip():
    reset()
    white = gloss("veg_turnip_white", (0.97, 0.94, 0.9))
    purple = gloss("veg_turnip_purple", (0.62, 0.16, 0.5))
    green = gloss("veg_turnip_leaf", (0.3, 0.68, 0.22), 0.35)
    stem = gloss("veg_turnip_stem", (0.55, 0.78, 0.35), 0.35)
    prof = [(0.0, 0.34), (0.05, 0.335), (0.11, 0.315), (0.15, 0.27), (0.165, 0.21), (0.155, 0.14), (0.12, 0.08),
            (0.06, 0.04), (0.02, 0.025), (0.0, 0.0)]
    body = lathe_r(prof, white, segs=28, name="turnip", smooth=60)
    two_tone(body, purple, lambda n, c: c.z > 0.2 + 0.015 * math.sin(6 * math.atan2(c.y, c.x)))
    parts = [body]
    for k in range(4):
        a = math.radians(-45 + 30 * k)
        tip = Vector((0.2 * math.sin(a), 0.04 * math.cos(2 * a) - 0.02, 0.6 - 0.04 * abs(k - 1.5)))
        parts.append(rod((0, 0, 0.33), Vector((tip.x * 0.4, tip.y * 0.4, 0.42)), 0.012, stem, verts=6))
        parts.append(leaf((tip.x * 0.35, tip.y * 0.35, 0.41), tip, 0.075, green, bend=0.025, twist=0.3 * (k - 1.5)))
    o = join(parts, "veg_turnip")
    settle(o)
    export(o, "veg_turnip")


def veg_mushroom():
    reset()
    cap_m = gloss("veg_mushroom_cap", (0.9, 0.12, 0.1))
    dot = gloss("veg_mushroom_spot", (1.0, 0.97, 0.9))
    stem = gloss("veg_mushroom_stem", (0.98, 0.93, 0.82), 0.35)
    gill = mat("veg_mushroom_gill", (0.85, 0.72, 0.6), 0.6)
    parts = [lathe_r([(0.0, 0.3), (0.08, 0.3), (0.095, 0.24), (0.1, 0.15), (0.11, 0.06), (0.13, 0.02), (0.11, 0.0),
                      (0.0, 0.0)], stem, segs=24, name="stem", smooth=60)]
    cap = lathe_r([(0.0, 0.6), (0.08, 0.595), (0.16, 0.57), (0.22, 0.52), (0.26, 0.45), (0.27, 0.4), (0.25, 0.37),
                   (0.0, 0.37)], cap_m, segs=32, name="cap", smooth=60)
    parts.append(cap)
    parts.append(lathe_r([(0.25, 0.372), (0.12, 0.36), (0.08, 0.33), (0.0, 0.33)], gill, segs=32, name="gills",
                         smooth=60))
    for d in ((0, -1, 0.35), (0.7, -0.6, 0.15), (-0.75, -0.55, 0.2), (0.3, -0.4, 0.85), (-0.35, -0.3, 0.8),
              (0.9, 0.1, 0.3), (-0.9, 0.2, 0.25), (0.0, 0.6, 0.7), (0.5, 0.75, 0.3), (-0.5, 0.8, 0.35)):
        dv = Vector(d).normalized()
        # the cap point in direction dv from (0, 0, 0.37)
        best = None
        for v in cap.data.vertices:
            w = (v.co - Vector((0, 0, 0.37))).normalized()
            sc = w.dot(dv)
            if best is None or sc > best[0]:
                best = (sc, v.co.copy(), w)
        sp = ell(best[1], (0.045, 0.045, 0.012), dot, segs=12, rings=6)
        q = Vector((0, 0, 1)).rotation_difference(best[2])
        sp.data.transform(Matrix.Translation(best[1]) @ q.to_matrix().to_4x4() @ Matrix.Translation(-best[1]))
        parts.append(sp)
    o = join(parts, "veg_mushroom")
    settle(o)
    export(o, "veg_mushroom")


def veg_pepper():
    reset()
    skin = gloss("veg_pepper_skin", (0.18, 0.62, 0.12), 0.18)
    stem = gloss("veg_pepper_stem", (0.3, 0.45, 0.15), 0.4)

    def lobes(k, z):
        return 1.0 + 0.1 * math.cos(4 * 2 * math.pi * k / 32)
    prof = [(0.0, 0.48), (0.06, 0.478), (0.13, 0.46), (0.19, 0.42), (0.215, 0.36), (0.215, 0.27), (0.2, 0.18),
            (0.17, 0.09), (0.12, 0.03), (0.06, 0.005), (0.0, 0.02)]
    body = lathe_r(prof, skin, segs=32, radial=lobes, name="pepper", smooth=60)
    for v in body.data.vertices:   # four bumps on the bottom
        a = math.atan2(v.co.y, v.co.x)
        if v.co.z < 0.08:
            v.co.z -= 0.025 * max(0.0, math.cos(4 * a)) * (1 - v.co.z / 0.08)
    body.data.update()
    parts = [body,
             lathe_r([(0.0, 0.5), (0.07, 0.49), (0.09, 0.47), (0.06, 0.46), (0.0, 0.46)], stem, segs=16, name="calyx"),
             tube([(0, 0, 0.48), (0, 0, 0.54), (0.02, 0, 0.58), (0.05, 0, 0.6)], [0.022, 0.02, 0.018, 0.016], stem,
                  verts=10, caps=True, name="stalk")]
    o = join(parts, "veg_pepper")
    settle(o)
    export(o, "veg_pepper")


def veg_pumpkin():
    reset()
    skin = gloss("veg_pumpkin_skin", (1.0, 0.48, 0.06), 0.3)
    stem = mat("veg_pumpkin_stem", (0.45, 0.35, 0.15), 0.6)
    green = gloss("veg_pumpkin_leaf", (0.28, 0.6, 0.18), 0.35)

    def ribs(k, z):
        return 1.0 - 0.07 * (0.5 + 0.5 * math.cos(9 * 2 * math.pi * k / 54)) ** 2
    prof = [(0.0, 0.4), (0.06, 0.39), (0.16, 0.37), (0.25, 0.32), (0.3, 0.24), (0.3, 0.15), (0.26, 0.07),
            (0.17, 0.015), (0.06, 0.0), (0.0, 0.01)]
    body = lathe_r(prof, skin, segs=54, radial=ribs, name="pumpkin", smooth=60)
    for v in body.data.vertices:
        v.co.y *= 0.92
    body.data.update()
    parts = [body,
             tube([(0, 0, 0.36), (0, 0, 0.45), (0.03, 0, 0.52), (0.07, 0, 0.55)], [0.035, 0.03, 0.026, 0.022], stem,
                  verts=8, caps=True, name="stem")]
    cur = [(0.0 + 0.06 * math.cos(a) * (1 - a / 12), 0.03 + 0.06 * math.sin(a) * (1 - a / 12), 0.42 + a * 0.008)
           for a in [x * 0.5 for x in range(14)]]
    parts.append(tube(cur, [0.008] * len(cur), green, verts=5, caps=True, name="tendril"))
    parts.append(leaf((0.03, 0.0, 0.4), (0.24, 0.05, 0.47), 0.09, green, bend=-0.03, twist=0.5))
    o = join(parts, "veg_pumpkin")
    settle(o)
    export(o, "veg_pumpkin")


def veg_eggplant():
    reset()
    skin = gloss("veg_eggplant_skin", (0.3, 0.08, 0.38), 0.15)
    cal = gloss("veg_eggplant_calyx", (0.3, 0.55, 0.2), 0.4)
    pts = [Vector(p) for p in ((0, 0, 0.58), (0, 0, 0.5), (0.02, 0, 0.4), (0.06, 0, 0.27), (0.08, 0, 0.14),
                               (0.06, 0, 0.04))]
    from blastyard_bombers import smooth_path
    sp = smooth_path(pts, 4)
    rad = []
    for i, p in enumerate(sp):
        t = i / (len(sp) - 1)
        rad.append(0.02 + 0.15 * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.7 * (0.45 + 0.55 * t))
    body = tube(sp, rad, skin, verts=24, caps=True, name="eggplant")
    parts = [body]
    for k in range(5):   # the star-shaped calyx
        a = 2 * math.pi * k / 5
        parts.append(leaf((0.0, 0.0, 0.55), (0.13 * math.cos(a), 0.13 * math.sin(a), 0.43), 0.055, cal, bend=0.015))
    parts.append(lathe_r([(0.0, 0.575), (0.05, 0.56), (0.075, 0.52), (0.07, 0.49), (0.0, 0.49)], cal, segs=16,
                         name="cap", smooth=50))
    parts.append(tube([(0, 0, 0.55), (0, 0, 0.62), (0.03, 0, 0.66)], [0.025, 0.02, 0.016], cal, verts=8, caps=True,
                      name="stem"))
    o = join(parts, "veg_eggplant")
    o.data.transform(Matrix.Rotation(math.radians(-12), 4, "Y"))
    settle(o)
    export(o, "veg_eggplant")


def veg_pineapple():
    reset()
    skin = gloss("veg_pineapple_skin", (0.95, 0.66, 0.12), 0.35)
    scale_m = gloss("veg_pineapple_eye", (0.7, 0.42, 0.08), 0.4)
    green = gloss("veg_pineapple_leaf", (0.25, 0.6, 0.25), 0.35)
    prof = [(0.0, 0.38), (0.06, 0.375), (0.11, 0.355), (0.14, 0.31), (0.155, 0.24), (0.15, 0.15), (0.13, 0.07),
            (0.08, 0.015), (0.0, 0.0)]
    body = lathe_r(prof, skin, segs=24, name="pineapple", smooth=60)
    parts = [body]
    # the diamond pattern: little pyramids in offset rows
    for row in range(7):
        z = 0.05 + row * 0.047
        r = None
        for (r0, z0), (r1, z1) in zip(prof[::-1], prof[::-1][1:]):
            if z0 <= z <= z1:
                r = r0 + (r1 - r0) * (z - z0) / max(1e-6, z1 - z0)
        if r is None or r < 0.05:
            continue
        n = 11
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (row % 2)) / n
            d = Vector((math.cos(a), math.sin(a), 0))
            pyr = cone(d * r * 0.985 + Vector((0, 0, z)), d * (r + 0.012) + Vector((0, 0, z + 0.004)), 0.024,
                       scale_m, verts=4)
            pyr.data.transform(Matrix.Translation(d * r + Vector((0, 0, z))) @ Matrix.Rotation(math.pi / 4, 4, d)
                               @ Matrix.Translation(-(d * r + Vector((0, 0, z)))))
            parts.append(pyr)
    for k in range(9):   # a crown of stiff leaves
        a = 2 * math.pi * k / 9
        tilt = 0.25 + 0.2 * (k % 2)
        tip = Vector((0.12 * math.cos(a) * tilt * 2.6, 0.12 * math.sin(a) * tilt * 2.6, 0.6 - 0.06 * (k % 2)))
        parts.append(leaf((0.02 * math.cos(a), 0.02 * math.sin(a), 0.36), tip, 0.035, green, bend=0.01))
    parts.append(leaf((0, 0, 0.36), (0, 0.0, 0.64), 0.03, green, bend=0.0))
    o = join(parts, "veg_pineapple")
    settle(o)
    export(o, "veg_pineapple")


def veg_melon():
    reset()
    rind = gloss("veg_melon_rind", (0.22, 0.6, 0.18), 0.2)
    stripe = gloss("veg_melon_stripe", (0.1, 0.33, 0.1), 0.2)
    stem = mat("veg_melon_stem", (0.45, 0.4, 0.18), 0.6)
    C, R = Vector((0, 0, 0.28)), Vector((0.3, 0.27, 0.28))
    body = ell(C, R, rind, segs=40, rings=24)
    stripes = []
    for k in range(10):   # wavy dark stripes from pole to pole, pressed flat onto the rind
        a0 = 2 * math.pi * k / 10
        pts, rad = [], []
        for i in range(25):
            v = math.pi * (0.04 + 0.92 * i / 24)
            az = a0 + 0.12 * math.sin(v * 9 + k)
            d = Vector((math.sin(v) * math.cos(az), math.sin(v) * math.sin(az), math.cos(v)))
            pts.append(C + Vector((d.x * R.x, d.y * R.y, d.z * R.z)) * 1.004)
            rad.append(0.034 * math.sin(v) ** 0.6)
        st = tube(pts, rad, stripe, verts=10, caps=True, name="stripe")
        for vv in st.data.vertices:
            q = vv.co - C
            dn = Vector((q.x / R.x, q.y / R.y, q.z / R.z))
            ln = dn.length
            vv.co = C + q * ((1.0 + (ln - 1.0) * 0.25) / ln)
        st.data.update()
        stripes.append(st)
    parts = [body] + stripes + [tube([(0, 0, 0.55), (0, 0, 0.6), (0.03, 0, 0.62)], [0.02, 0.017, 0.014], stem,
                                     verts=8, caps=True, name="stem")]
    cur = [(0.02 + 0.05 * math.cos(a) * (1 - a / 12), 0.05 * math.sin(a) * (1 - a / 12), 0.6 + a * 0.006)
           for a in [x * 0.5 for x in range(14)]]
    parts.append(tube(cur, [0.007] * len(cur), stem, verts=5, caps=True, name="tendril"))
    o = join(parts, "veg_melon")
    settle(o)
    export(o, "veg_melon")


# ------------------------------------------------------------------ the surface strip

def petal_ring(c, n, r_in, r_out, w, material, tilt=0.25, phase=0.0, face=(0, -1, 0)):
    """A ring of petals round c in the plane facing `face`."""
    f = Vector(face).normalized()
    q = Vector((0, 0, 1)).rotation_difference(f)
    out = []
    for k in range(n):
        a = phase + 2 * math.pi * k / n
        d = q @ Vector((math.cos(a), math.sin(a), 0))
        out.append(leaf(Vector(c) + d * r_in, Vector(c) + d * r_out + f * tilt * (r_out - r_in), w, material,
                        bend=-0.01))
    return out


def flower_a():
    reset()
    stem = gloss("flower_stem", (0.25, 0.6, 0.2), 0.4)
    petal = gloss("flower_a_petal", (1.0, 0.55, 0.72), 0.4)
    heart = gloss("flower_a_heart", (1.0, 0.8, 0.15), 0.4)
    parts = [tube([(0, 0, 0), (0.02, 0, 0.15), (-0.01, 0, 0.3), (0.0, -0.02, 0.4)], [0.012, 0.011, 0.01, 0.009], stem,
                  verts=8, caps=True, name="stem"),
             leaf((0.01, 0, 0.08), (0.14, -0.02, 0.18), 0.04, stem, bend=0.02),
             leaf((0.0, 0, 0.16), (-0.12, -0.01, 0.25), 0.035, stem, bend=0.02)]
    c = Vector((0.0, -0.03, 0.41))
    parts += petal_ring(c, 10, 0.02, 0.1, 0.022, petal, tilt=0.15, face=(0, -1, 0.35))
    parts.append(ell(c + Vector((0, -0.01, 0.004)), (0.035, 0.022, 0.035), heart, segs=14, rings=8))
    export(join(parts, "flower_a"), "flower_a")


def flower_b():
    reset()
    stem = gloss("flower_stem", (0.25, 0.6, 0.2), 0.4)
    bell = gloss("flower_b_bell", (0.35, 0.45, 1.0), 0.35)
    parts = []
    for j, (x, h, lean) in enumerate(((-0.05, 0.36, -0.06), (0.04, 0.3, 0.07))):
        pts = [Vector((x, 0, 0)), Vector((x, 0, h * 0.5)), Vector((x + lean * 0.6, 0, h * 0.9)),
               Vector((x + lean * 1.6, 0, h * 0.95))]
        parts.append(tube(pts, [0.01, 0.009, 0.008, 0.006], stem, verts=6, caps=True, name="stem"))
        for k in range(4):   # bells hanging along the arch
            p = Vector((x + lean * (0.4 + k * 0.4), 0, h * (0.62 + 0.1 * k)))
            b = lathe_r([(0.0, 0.0), (0.012, -0.004), (0.026, -0.03), (0.03, -0.05), (0.036, -0.056),
                         (0.028, -0.052), (0.0, -0.03)], bell, segs=12, name="bell", smooth=50)
            b.data.transform(Matrix.Translation(p + Vector((math.copysign(0.025, lean), 0, -0.005))))
            parts.append(b)
            parts.append(rod(p, p + Vector((math.copysign(0.025, lean), 0, -0.005)), 0.004, stem, verts=4))
    parts.append(leaf((0, 0, 0.0), (0.12, -0.03, 0.22), 0.03, stem, bend=0.02))
    parts.append(leaf((0, 0, 0.0), (-0.13, 0.02, 0.2), 0.03, stem, bend=0.02))
    export(join(parts, "flower_b"), "flower_b")


def bush():
    reset()
    leaf_m = mat("bush_leaf", (0.2, 0.52, 0.17), 0.55, coat=0.2)
    light = mat("bush_light", (0.36, 0.68, 0.24), 0.55, coat=0.2)
    berry = gloss("bush_berry", (0.9, 0.12, 0.2), 0.2)
    parts = []
    rnd = random.Random(5)
    for (x, z, r) in ((-0.3, 0.2, 0.22), (0.0, 0.3, 0.28), (0.3, 0.21, 0.22), (-0.14, 0.42, 0.18), (0.16, 0.43, 0.17),
                      (0.42, 0.12, 0.13), (-0.43, 0.11, 0.13)):
        o = boulder(r, (1.0, 0.85, 0.95), rnd.randint(0, 999), 0.12, leaf_m, light, sub=3, smooth=80, flat=0.0)
        o.data.transform(Matrix.Translation((x, 0.0, z - r * 0.9)))
        parts.append(o)
    for k in range(9):
        x = rnd.uniform(-0.4, 0.4)
        z = rnd.uniform(0.12, 0.45)
        parts.append(sphere(0.025, (x, -0.23 - 0.02 * rnd.random(), z), berry, segs=10, rings=6))
    o = join(parts, "bush")
    vs = o.data.vertices
    for v in vs:
        v.co.z = max(v.co.z, 0.0)
    o.data.update()
    export(o, "bush")


def fence():
    reset()
    wood = mat("fence_paint", (0.96, 0.94, 0.88), 0.55, coat=0.2)
    post_m = mat("fence_post", (0.88, 0.85, 0.78), 0.6)
    parts = []
    for x in (-0.5, 0.5):
        parts.append(K.box((0.08, 0.08, 0.66), (x, 0.02, 0.33), post_m, bevel=0.012))
        parts.append(K.prism([(-0.045, 0.0), (0.045, 0.0), (0.0, 0.05)], 0.09, (x, 0.02, 0.66), post_m, bevel=0.006))
    for z in (0.17, 0.44):
        parts.append(K.box((2.0, 0.035, 0.06), (0, 0.06, z), wood, bevel=0.01))
    rnd = random.Random(3)
    for k in range(10):
        x = -0.9 + 0.2 * k
        if abs(abs(x) - 0.5) < 0.05:
            continue
        h = 0.5 + 0.02 * rnd.uniform(-1, 1)
        parts.append(K.prism([(-0.04, 0.0), (0.04, 0.0), (0.04, h), (0.0, h + 0.05), (-0.04, h)], 0.02,
                             (x, 0.03, 0.02), wood, bevel=0.005))
    export(join(parts, "fence"), "fence")


def signpost():
    reset()
    wood = mat("signpost_wood", (0.55, 0.36, 0.2), 0.7)
    board = mat("signpost_board", (0.95, 0.85, 0.6), 0.6)
    trim = mat("signpost_trim", (0.75, 0.25, 0.15), 0.55)
    nail = mat("signpost_nail", (0.6, 0.6, 0.62), 0.3, metal=0.9)
    parts = [K.box((0.08, 0.08, 1.1), (0, 0.02, 0.55), wood, bevel=0.012)]
    arrow = [(-0.32, -0.1), (0.22, -0.1), (0.36, 0.0), (0.22, 0.1), (-0.32, 0.1)]
    parts.append(K.prism([(x, z + 0.86) for x, z in arrow], 0.04, (0.04, -0.03, 0.0), board, bevel=0.012))
    edge = [(x * 1.0, z + 0.86) for x, z in arrow] + [(arrow[0][0], arrow[0][1] + 0.86)]
    parts.append(tube([(x + 0.04, -0.054, z) for x, z in edge], [0.008] * len(edge), trim, verts=5, caps=True,
                      name="trim"))
    for x in (-0.03, 0.03):
        parts.append(cyl(0.01, 0.01, (0.0, -0.055, 0.86 + x), nail, rot=(math.pi / 2, 0, 0), verts=8))
    parts.append(K.box((0.12, 0.12, 0.05), (0, 0.02, 0.025), wood, bevel=0.01))
    export(join(parts, "signpost"), "signpost")


def wheelbarrow():
    reset()
    tray = gloss("wheelbarrow_tray", (0.85, 0.2, 0.12), 0.35)
    metal = mat("wheelbarrow_metal", (0.3, 0.3, 0.32), 0.4, metal=0.7)
    wood = mat("wheelbarrow_handle", (0.6, 0.4, 0.22), 0.6)
    tyre = mat("wheelbarrow_tyre", (0.1, 0.1, 0.1), 0.7)
    soil = mat("wheelbarrow_soil", (0.36, 0.24, 0.15), 0.9)
    # the tray: a tapered tub, deeper at the front (+X)
    bm = bmesh.new()
    top = [(-0.32, -0.24), (0.36, -0.22), (0.36, 0.22), (-0.32, 0.24)]
    bot = [(-0.18, -0.15), (0.2, -0.13), (0.2, 0.13), (-0.18, 0.15)]
    vt = [bm.verts.new((x, y, 0.5)) for x, y in top]
    vb = [bm.verts.new((x, y, 0.27)) for x, y in bot]
    bm.faces.new(vb[::-1])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    o = new_obj("tray", bm, tray, smooth=0)
    K.select(o)
    m = o.modifiers.new("s", "SOLIDIFY")
    m.thickness = 0.02
    bpy.ops.object.modifier_apply(modifier=m.name)
    b = o.modifiers.new("b", "BEVEL")
    b.width = 0.01
    b.segments = 2
    bpy.ops.object.modifier_apply(modifier=b.name)
    parts = [o]
    parts.append(lumpy(0.2, (0.02, 0, 0.47), soil, 4, amount=0.15, scale=(1.4, 1.0, 0.45), sub=2))
    for s in (-1, 1):
        parts.append(rod((0.42, s * 0.05, 0.16), (-0.6, s * 0.2, 0.36), 0.022, wood, verts=8))
        parts.append(tube([(-0.6, s * 0.2, 0.36), (-0.72, s * 0.22, 0.4)], [0.03, 0.03], tyre, verts=8, caps=True,
                          name="grip"))
        parts.append(rod((-0.2, s * 0.13, 0.26), (-0.24, s * 0.15, 0.0), 0.016, metal, verts=8))   # the legs
        parts.append(K.box((0.06, 0.04, 0.02), (-0.24, s * 0.15, 0.01), metal, bevel=0.005))
    # the wheel at the front
    parts.append(torus(0.13, 0.04, (0.42, 0, 0.17), tyre, rot=(math.pi / 2, 0, 0), verts=28, minor=10))
    parts.append(cyl(0.1, 0.05, (0.42, 0, 0.17), tray, rot=(math.pi / 2, 0, 0), verts=24))
    parts.append(cyl(0.025, 0.09, (0.42, 0, 0.17), metal, rot=(math.pi / 2, 0, 0), verts=12))
    o = join(parts, "wheelbarrow")
    settle(o)
    export(o, "wheelbarrow")


def shed():
    reset()
    plank = mat("shed_plank", (0.38, 0.6, 0.48), 0.65)
    plank2 = mat("shed_plank_dark", (0.3, 0.5, 0.4), 0.65)
    trim = mat("shed_trim", (0.96, 0.94, 0.86), 0.55)
    roof = mat("shed_roof", (0.62, 0.2, 0.15), 0.6)
    door = mat("shed_door", (0.86, 0.6, 0.25), 0.55)
    glow = mat("shed_glow", (1.0, 0.82, 0.45), 0.3, emit=2.0, emit_color=(1.0, 0.7, 0.3))
    metal = mat("shed_metal", (0.35, 0.33, 0.3), 0.4, metal=0.8)
    pot = mat("shed_box", (0.7, 0.35, 0.2), 0.6)
    petal = gloss("flower_a_petal", (1.0, 0.55, 0.72), 0.4)
    heart = gloss("flower_a_heart", (1.0, 0.8, 0.15), 0.4)
    W, D, H = 1.8, 1.4, 1.75    # walls; the roof ridge reaches 2.5
    parts = [K.box((W, D, H), (0, 0, H / 2), plank, bevel=0.02)]
    # vertical planks on the front and the sides
    for k in range(13):
        x = -W / 2 + 0.07 + k * (W - 0.14) / 12
        parts.append(K.box((0.012, 0.012, H - 0.04), (x, -D / 2 - 0.002, H / 2), plank2, bevel=0.0))
    for k in range(9):
        y = -D / 2 + 0.08 + k * (D - 0.16) / 8
        for s in (-1, 1):
            parts.append(K.box((0.012, 0.012, H - 0.04), (s * (W / 2 + 0.002), y, H / 2), plank2, bevel=0.0))
    for k in range(13):
        x = -W / 2 + 0.07 + k * (W - 0.14) / 12
        parts.append(K.box((0.012, 0.012, H - 0.04), (x, D / 2 + 0.002, H / 2), plank2, bevel=0.0))
    # the gables and the roof (two pitched slabs with an overhang)
    gz = 2.42
    for y in (-D / 2, D / 2):
        parts.append(K.prism([(-W / 2, H), (W / 2, H), (0.0, gz)], 0.04, (0, y, 0), plank, bevel=0.01))
    pitch = math.atan2(gz - H, W / 2)
    L = math.hypot(W / 2, gz - H) + 0.18
    for s in (-1, 1):
        slab = K.box((L, D + 0.3, 0.07), (0, 0, 0), roof, bevel=0.015)
        slab.data.transform(Matrix.Translation((s * (L / 2 - 0.06) * math.cos(pitch), 0, gz + 0.03
                                                - (L / 2 - 0.06) * math.sin(pitch)))
                            @ Matrix.Rotation(s * pitch, 4, "Y"))
        parts.append(slab)
        for k in range(5):   # shingle rows
            t = 0.12 + k * 0.19
            strip = K.box((0.05, D + 0.32, 0.02), (0, 0, 0), roof, bevel=0.006)
            px = s * t * L * math.cos(pitch) - s * 0.0
            pz = gz + 0.07 - t * L * math.sin(pitch)
            strip.data.transform(Matrix.Translation((px, 0, pz)) @ Matrix.Rotation(s * pitch, 4, "Y"))
            parts.append(strip)
    parts.append(rod((0, -D / 2 - 0.16, gz + 0.07), (0, D / 2 + 0.16, gz + 0.07), 0.05, trim, verts=10))
    # corner trims
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(K.box((0.07, 0.07, H), (sx * W / 2, sy * D / 2, H / 2), trim, bevel=0.01))
    # the door with a Z brace, a latch; the window with a glow and cross bars, a flower box
    dx = -0.35
    parts.append(K.box((0.62, 0.04, 1.45), (dx, -D / 2 - 0.02, 0.74), door, bevel=0.012))
    for z in (0.25, 1.25):
        parts.append(K.box((0.62, 0.03, 0.08), (dx, -D / 2 - 0.05, z), trim, bevel=0.008))
    brace = K.box((0.08, 0.03, 1.12), (dx, -D / 2 - 0.05, 0.75), trim, bevel=0.008)
    brace.data.transform(Matrix.Translation((dx, 0, 0.75)) @ Matrix.Rotation(math.atan2(0.5, 1.0), 4, "Y")
                         @ Matrix.Translation((-dx, 0, -0.75)))
    parts.append(brace)
    parts.append(sphere(0.03, (dx + 0.24, -D / 2 - 0.07, 0.74), metal, segs=10, rings=6))
    wx, wz = 0.45, 1.15
    parts.append(K.box((0.5, 0.03, 0.46), (wx, -D / 2 - 0.005, wz), glow, bevel=0.0))
    for (sx, sz, x, z) in ((0.6, 0.06, wx, wz + 0.26), (0.6, 0.06, wx, wz - 0.26), (0.06, 0.52, wx - 0.27, wz),
                           (0.06, 0.52, wx + 0.27, wz), (0.03, 0.46, wx, wz), (0.5, 0.03, wx, wz)):
        parts.append(K.box((sx, 0.05, sz), (x, -D / 2 - 0.03, z), trim, bevel=0.006))
    parts.append(K.box((0.62, 0.16, 0.13), (wx, -D / 2 - 0.1, wz - 0.36), pot, bevel=0.015))
    for k in range(5):
        c = Vector((wx - 0.24 + 0.12 * k, -D / 2 - 0.16, wz - 0.22 + 0.03 * (k % 2)))
        parts += petal_ring(c, 6, 0.012, 0.05, 0.016, petal if k % 2 == 0 else heart, tilt=0.1)
        parts.append(sphere(0.016, c + Vector((0, -0.006, 0)), heart if k % 2 == 0 else petal, segs=8, rings=6))
    o = join(parts, "shed")
    export(o, "shed")


def level_flower():
    reset()
    stem = gloss("level_flower_stem", (0.28, 0.6, 0.2), 0.4)
    petal = gloss("level_flower_petal", (1.0, 0.78, 0.08), 0.35)
    disk = mat("level_flower_disk", (0.36, 0.2, 0.08), 0.6)
    seed = mat("level_flower_seed", (0.22, 0.12, 0.05), 0.5)
    parts = [tube([(0, 0, 0), (0.02, 0, 0.35), (-0.02, 0, 0.7), (0.0, -0.03, 0.92)], [0.03, 0.028, 0.025, 0.022], stem,
                  verts=10, caps=True, name="stem"),
             leaf((0.01, -0.01, 0.3), (0.3, -0.06, 0.45), 0.09, stem, bend=0.04, twist=0.3),
             leaf((0.0, -0.01, 0.52), (-0.28, -0.05, 0.66), 0.08, stem, bend=0.04, twist=-0.3)]
    c = Vector((0.0, -0.06, 0.96))
    face = Vector((0, -1, 0.15)).normalized()
    parts += petal_ring(c, 16, 0.1, 0.25, 0.045, petal, tilt=0.15, face=face)
    parts += petal_ring(c + face * -0.01, 16, 0.09, 0.22, 0.04, petal, tilt=0.1, face=face, phase=math.pi / 16)
    dk = ell(c, (0.12, 0.04, 0.12), disk, segs=24, rings=12)
    q = Vector((0, -1, 0)).rotation_difference(face)
    dk.data.transform(Matrix.Translation(c) @ q.to_matrix().to_4x4() @ Matrix.Translation(-c))
    parts.append(dk)
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(60):   # seeds in a golden spiral
        r = 0.105 * math.sqrt((i + 0.5) / 60)
        a = i * ga
        p = c + q @ Vector((r * math.cos(a), -0.035 * (1 - (r / 0.13) ** 2) - 0.004, r * math.sin(a)))
        parts.append(sphere(0.009, p, seed, segs=6, rings=4))
    export(join(parts, "level_flower"), "level_flower")


JOBS = {"digger": digger, "puffer": puffer, "drake": drake, "rock": rock, "rock_shard": rock_shard,
        "veg_carrot": veg_carrot, "veg_turnip": veg_turnip, "veg_mushroom": veg_mushroom, "veg_pepper": veg_pepper,
        "veg_pumpkin": veg_pumpkin, "veg_eggplant": veg_eggplant, "veg_pineapple": veg_pineapple,
        "veg_melon": veg_melon, "flower_a": flower_a, "flower_b": flower_b, "bush": bush, "fence": fence,
        "signpost": signpost, "wheelbarrow": wheelbarrow, "shed": shed, "level_flower": level_flower}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
