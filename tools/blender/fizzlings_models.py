"""Fizzlings (game 18) models: the axolotl hero (one model, recoloured for player 2), the soap bubbles (plain, trap,
three element bubbles, the letter bubble), three wind-up tin toy enemies, six treats, the platform tiles and the
underwater-toybox backdrop.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/fizzlings_models.py -- godot/games/fizzlings/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export), the rig
from blastyard_bombers.py (merge, mirror, limb) and hopline_models.py (TurnRig, ell, ell_point, hemi),
mossfolk_models.py (lumpy, lathe_r, solid), nightbite_characters.py (blob, about), slipfloe_models.py (star, tiny),
prism_models.py (new_obj, animate, export_anim, empty). 30 fps.

Axes. The level is seen from the side: 1 tile = 0.5 units, the camera sits at Godot +Z looking straight on. Blender Z
up; everything is written facing Blender -Y (the camera side) and the characters are exported turned to face Godot +X
(right), with a 20 degree (hero) or 15 degree (toys) turn towards the camera so both eyes and the smile read; mirror
them with scale.x = -1 to face left (the turn towards the camera survives the mirror). Origins at the feet centre
unless noted.

axolotl.glb     armature "axolotl_rig", skinned mesh "axolotl", 0.9 tall (gill tips), about 0.33 tall to the chin; the
                snout reaches x = +0.24, the tail x = -0.47 (Godot). Mouth (bubble spawn) at about (+0.24, 0.52, +0.05)
                from the origin; spawn the bubble at x = +0.55 when it is full size.
                Materials: fizz_skin (pink: RECOLOUR it for player 2, blue-lilac), fizz_gill (the gill stalks, frills and
                the back and tail fin, slightly emissive: RECOLOUR with the skin), fizz_gill_tip (the glowing gill tips,
                emissive: recolour too), fizz_belly (cream belly, hand and toe tips), fizz_eye (glossy black),
                fizz_shine (emissive catchlights), fizz_mouth (smile line and the puffed mouth), fizz_blush,
                fizz_star (dizzy stars, emissive).
                Animations (30 fps; loops are marked, the rest are one-shots holding the last frame):
                idle (loop 2 s: breathing, gill ripple, a blink, tail sway), walk (loop 0.5 s: two steps, no travel),
                jump (one-shot 0.27 s: a spring off both feet into a rising pose it holds: arms up, gills streaming),
                fall (loop 0.4 s: arms paddling up, gills and tail floating up), blow (one-shot 0.27 s: cheeks
                puff, lunge, the mouth rounds into an "O" at 0.1 s: spawn the bubble then), die (one-shot 1.33 s: a
                shocked stretch, two spins in the air, flops on its back, dizzy stars; holds), ride (loop 1 s: feet
                together on a bubble, balancing with the arms and tail), cheer (loop 1 s: two hops with the arms up).
                The dizzy stars and the "O" mouth are scaled to nothing except in die and blow.
bubble.glb      node "bubble", 0.9 across, origin at the centre. Materials: bubble (the shell: pale aqua, alpha-blended,
                very clear), bubble_rim_pink, bubble_rim_cyan, bubble_rim_gold, bubble_rim_violet (a thin iridescent
                ring just inside the silhouette, facing the camera, emissive and alpha-blended: it reads as the
                thin-film rim), bubble_shine (the window glint and a dot, emissive white). Tint "bubble" and the rims
                to warn that a bubble is about to pop. For a real fresnel look the game may swap "bubble" for a
                shader; the rims already give the rim.
bubble_trap     node "bubble_trap": the same, 1.0 across. The trapped toy sits at its centre (see below).
special_bubble_water / _fire / _bolt   one node each, 0.9 across, shells bubble_water / bubble_fire / bubble_bolt
                (tinted), the element inside glowing: water_core (a drop and two droplets) + water_shine,
                fire_core + fire_core_hot (two flames), bolt_core + bolt_glow (a lightning bolt with a halo).
letter_bubble   node "letter_bubble": the plain bubble with a chubby star inside (letter_star, recolour per letter),
                set 0.06 behind the centre so a Label3D at the centre (z = +0.1) sits in front of it.
Enemies (armature "<name>_rig", skinned mesh "<name>", facing +X, 15 degrees towards the camera). Shared materials:
                toy_paint (the body paint: tint it red for the angry version), toy_stripe (bands, spots, fins), toy_metal
                (chrome), toy_brass (keys, rivets), toy_rubber (feet), toy_eye, toy_pupil, toy_shine, toy_glow
                (emissive bulbs). "trapped" (loop 0.5 s) curls the toy up (0.85 scale, upside down, struggling) CENTRED
                ON ITS ORIGIN: place the node at the bubble centre while trapped.
toy_beetle      a clockwork beetle 0.65 tall (the key), 0.8 long. walk (loop 0.5 s: tripod scuttle, the key turns once),
                trapped (legs flailing, the key whirring).
toy_spring      a tin-can robot on a coil spring with a pad foot, 0.82 tall (antenna bulb). walk (loop 0.5 s: one hop,
                0.2 high, on the spot), trapped (spring coiled up, arms waving).
toy_flyer       a tin bird with a propeller, 0.7 tall (hub), origin under its dangling feet (hover it). fly (loop 0.5 s:
                the propeller turns once, wings flap, bobbing), trapped.
Treats (one node each, origin at the base centre, facing the camera, 0.4-0.55 tall): treat_cherry, treat_melon,
                treat_cupcake, treat_icecream, treat_gem, treat_crown. Materials prefixed treat_; treat_shine is the
                emissive glint on each.
tile_block      node "tile_block": 0.5 cube, ORIGIN AT ITS CENTRE (put it at the tile centre), bevelled, a raised front
                panel with a ring and a pearl stud. Materials tile_face (RECOLOUR per level), tile_trim (the ring:
                recolour to a darker shade of tile_face), tile_pearl (white stud).
tile_top        node "tile_top": the same block with a scalloped foam lip over its top edge (tile_top_trim, recolour
                per level too): its top stays at +0.25; the scallops hang 0.11 down the front face, the lip sticks out 0.012
                at the front and back. Two scallops per tile, so a row reads as one continuous edge.
Backdrop (origin at the base centre, facing the camera; put them behind the play plane):
                bg_kelp (armature "bg_kelp_rig", mesh "bg_kelp": three kelp strands up to 3.3 tall, animation "sway",
                loop 3 s), bg_coral (1.5 tall, 1.6 wide: branching coral, a brain coral, a sea star on a rock),
                bg_shell (an open scallop with a glowing pearl, 1.2 wide, 1.0 tall), bg_toy_block (a big toy block, 1.1
                cube, turned 28 degrees, a star, a heart and a circle on its faces, half sunk in sand), bg_bubble_column
                (root "bg_bubble_column" with the vent rock child "vent" and 14 bubble children "b00".."b13";
                animation "rise", loop 2 s: bubbles leave the vent and rise 3.8, wobbling, popping at the top).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90
from blastyard_bombers import merge, mirror, limb
from prism_models import new_obj, animate, export_anim, empty
from nightbite_characters import blob, about
from mossfolk_models import lumpy, lathe_r, solid
from hopline_models import TurnRig, ell, ell_point, hemi
from slipfloe_models import star, tiny

FPS = 30


# ------------------------------------------------------------------ helpers

def fin_yz(outline, material, thick=0.02, x=0.0, name="fin"):
    """A thin fin: a polygon given as (y, z) points in the Y-Z plane at x, `thick` wide along X."""
    bm = bmesh.new()
    a = [bm.verts.new((x - thick / 2, y, z)) for y, z in outline]
    b = [bm.verts.new((x + thick / 2, y, z)) for y, z in outline]
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return new_obj(name, bm, material, smooth=50)


def centred(c, rot, k):
    """The root offset that puts point c (build coordinates) on the origin after the root is rotated by rot
    (degrees about X, Y, Z, as the rig applies them) and scaled by k."""
    R = (Matrix.Rotation(math.radians(rot[2]), 3, "Z") @ Matrix.Rotation(math.radians(rot[1]), 3, "Y")
         @ Matrix.Rotation(math.radians(rot[0]), 3, "X"))
    return tuple(-(R @ Vector(c)) * k)


def arc_on_sphere(R, a0, a1, lift, n=9):
    """Points on a sphere of radius R along an arc in front (towards -Y): angle a (degrees, 0 = +X, 90 = up)."""
    pts = []
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * k / (n - 1))
        d = Vector((math.cos(a) * lift, -math.sqrt(max(0.0, 1 - lift * lift)), math.sin(a) * lift))
        pts.append(d * R)
    return pts


def glint(c, r, material, face=(0, -1, 0), stretch=1.6):
    """A small flattened emissive highlight at c."""
    return blob(r, c, material, (1.0, 0.35, stretch), face, segs=10, rings=6)


# ------------------------------------------------------------------ the axolotl (written facing -Y)

H = Vector((0, -0.02, 0.6))        # head centre
HR = (0.205, 0.19, 0.162)
BC = Vector((0, 0.025, 0.3))       # body centre
BR = (0.15, 0.14, 0.2)
STARS = Vector((0, 0.0, 0.84))
GILLS = (  # base direction on the head, stalk direction, length
    ((0.5, 0.42, 0.72), (0.3, 0.62, 0.78), 0.17),
    ((0.82, 0.48, 0.22), (0.5, 0.82, 0.2), 0.185),
    ((0.78, 0.42, -0.28), (0.45, 0.8, -0.32), 0.15))


def gill_path(s, g):
    d, v, L = GILLS[g]
    base = ell_point(H, HR, (d[0] * s, d[1], d[2]))
    v = Vector((v[0] * s, v[1], v[2])).normalized()
    up = Vector((0, 0, 1))
    p0 = base - v * 0.02
    pts = [p0, p0 + v * L * 0.4, p0 + v * L * 0.75 + up * 0.015, p0 + v * L + up * 0.04]
    return pts, v


def axolotl():
    skin = mat("fizz_skin", (1.0, 0.42, 0.6), 0.32, coat=0.7)
    gill = mat("fizz_gill", (1.0, 0.24, 0.5), 0.35, coat=0.4, emit=0.35, emit_color=(1.0, 0.25, 0.5))
    tip = mat("fizz_gill_tip", (1.0, 0.6, 0.78), 0.3, emit=3.0, emit_color=(1.0, 0.45, 0.7))
    belly = mat("fizz_belly", (1.0, 0.88, 0.84), 0.45, coat=0.4)
    eye_m = mat("fizz_eye", (0.02, 0.02, 0.05), 0.08, coat=1.0)
    shine = mat("fizz_shine", (1, 1, 1), 0.2, emit=5.0)
    mouth = mat("fizz_mouth", (0.35, 0.05, 0.14), 0.5)
    blush = mat("fizz_blush", (1.0, 0.3, 0.42), 0.55)
    star_m = mat("fizz_star", (1.0, 0.88, 0.25), 0.3, emit=3.0)

    MOUTH = ell_point(H, HR, (0, -0.9, -0.36))
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0.01, 0.1), (0, 0.0, 0.46), "root"),
         "head": ((0, 0.0, 0.46), (0, -0.02, 0.76), "body"),
         "smile": (tuple(MOUTH), tuple(MOUTH + Vector((0, -0.05, 0))), "head"),
         "mouth_o": (tuple(MOUTH), tuple(MOUTH + Vector((0, -0.05, 0))), "head"),
         "tail1": ((0, 0.1, 0.2), (0, 0.26, 0.135), "root"),
         "tail2": ((0, 0.26, 0.135), (0, 0.46, 0.1), "tail1"),
         "stars": (tuple(STARS), tuple(STARS + Vector((0, 0, 0.1))), "head")}
    EYES = {}
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: (p[0] * s, p[1], p[2])
        d = Vector((0.6 * s, -0.72, 0.34)).normalized()
        e = ell_point(H, HR, d)
        EYES[side] = (d, e)
        B["eye." + side] = (tuple(e), tuple(e + d * 0.06), "head")
        B["arm." + side] = (m((0.13, -0.02, 0.41)), m((0.155, -0.12, 0.27)), "body")
        B["thigh." + side] = (m((0.085, 0.02, 0.17)), m((0.09, 0.0, 0.05)), "root")
        B["foot." + side] = (m((0.09, 0.0, 0.05)), m((0.09, -0.1, 0.02)), "thigh." + side)
        for g in range(3):
            pts, v = gill_path(s, g)
            B["gill%d.%s" % (g + 1, side)] = (tuple(pts[0]), tuple(pts[-1]), "head")
    rig = TurnRig(B, 70, fps=FPS, hidden=("mouth_o", "stars"))

    # body: a pear leaning a touch forward, the cream belly in front
    rig.rigid("body", ell(BC, BR, skin, pitch=-6, segs=24, rings=14),
              blob(0.13, (0, -0.075, 0.28), belly, (1.0, 0.45, 1.3), (0, -1, -0.1), segs=16, rings=10))
    # the back and tail fin: one frilly sheet from the nape to past the tail tip
    outer = [(0.08, 0.49), (0.14, 0.45), (0.18, 0.39), (0.21, 0.32), (0.27, 0.26), (0.33, 0.22), (0.4, 0.19),
             (0.46, 0.16), (0.5, 0.12)]
    under = [(0.48, 0.08), (0.42, 0.06), (0.35, 0.06), (0.28, 0.09)]
    inner = [(0.2, 0.17), (0.13, 0.28), (0.1, 0.38), (0.06, 0.46)]
    wob = [(y, z + (0.008 if k % 2 else -0.004)) for k, (y, z) in enumerate(outer)]
    fin = fin_yz(wob + under + inner, gill, thick=0.018)
    rig.smooth(["body", "tail1", "tail2"], fin, power=5)
    # tail: a flattened tapering tube
    t = limb([(0, 0.06, 0.25), (0, 0.16, 0.18), (0, 0.26, 0.135), (0, 0.36, 0.11), (0, 0.45, 0.1)],
             [0.1, 0.08, 0.058, 0.036, 0.012], skin, verts=12, per=3, caps=True)
    t.data.transform(Matrix.Diagonal((0.62, 1, 1, 1)).to_4x4())
    rig.smooth(["body", "tail1", "tail2"], t, power=5)
    # head: wide and round, the smile, eyes, blush, the gills
    rig.rigid("head", ell(H, HR, skin, segs=28, rings=16))
    rig.rigid("head", blob(0.11, ell_point(H, HR, (0, -0.8, -0.6)), belly, (1.35, 0.35, 0.75), (0, -0.8, -0.6),
                           segs=14, rings=8))     # a pale chin
    sm = []
    for k in range(11):
        f = -1 + 2 * k / 10
        phi = math.radians(78 * f)
        d = Vector((math.sin(phi), -math.cos(phi), -0.36 + 0.2 * f * f))
        sm.append(ell_point(H, HR, d) + d.normalized() * 0.004)
    rig.rigid("smile", tube(sm, [0.007, 0.01, 0.011, 0.012, 0.012, 0.012, 0.012, 0.012, 0.011, 0.01, 0.007], mouth,
                            verts=6))
    for s, side in ((1, "L"), (-1, "R")):
        d, e = EYES[side]
        rig.rigid("eye." + side, blob(0.052, e, eye_m, (1.0, 0.62, 1.1), d, segs=16, rings=10),
                  sphere(0.018, e + d * 0.03 + Vector((0.006 * s, -0.012, 0.022)), shine, segs=8, rings=5),
                  sphere(0.008, e + d * 0.03 + Vector((-0.012 * s, -0.012, -0.018)), shine, segs=6, rings=4))
        cd = Vector((0.74 * s, -0.56, -0.2)).normalized()
        rig.rigid("head", blob(0.042, ell_point(H, HR, cd), blush, (1.25, 0.3, 0.8), cd, segs=10, rings=6))
        for g in range(3):
            pts, v = gill_path(s, g)
            bone = "gill%d.%s" % (g + 1, side)
            parts = [limb(pts, [0.022, 0.018, 0.014, 0.011], gill, verts=8, per=2, caps=False)]
            perp = (Vector((0, 0, 1)) - v * v.z).normalized()
            for i, tt in enumerate((0.26, 0.42, 0.58, 0.74, 0.88)):
                p = pts[0].lerp(pts[-1], tt)
                for sg in (1, -1):
                    dd = (perp * sg * 0.8 + v * 0.7).normalized()
                    parts.append(blob(0.03 - 0.003 * i, p + dd * 0.024, gill, (0.5, 0.42, 1.25), dd, segs=8,
                                      rings=5))
            parts.append(sphere(0.026, pts[-1], tip, segs=10, rings=6))
            rig.rigid(bone, *parts)
    # the "O" mouth of blow (hidden otherwise): pursed lips round a dark hole
    rig.rigid("mouth_o", torus(0.032, 0.014, MOUTH + Vector((0, -0.012, 0.004)), skin, rot=(R90, 0, 0), verts=16,
                               minor=6),
              blob(0.03, MOUTH + Vector((0, -0.016, 0.004)), mouth, (1.0, 0.3, 1.0), (0, -1, 0), segs=10, rings=6))
    # arms with round hands and three fingers; stubby legs with round feet and toes
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: Vector((p[0] * s, p[1], p[2]))
        rig.rigid("arm." + side, limb([m((0.11, -0.01, 0.42)), m((0.13, -0.02, 0.41)), m((0.155, -0.07, 0.33)),
                                       m((0.155, -0.11, 0.28))], [0.035, 0.034, 0.03, 0.028], skin, verts=10, per=2,
                                      caps=True),
                  sphere(0.038, m((0.155, -0.125, 0.265)), skin, scale=(0.9, 1.0, 1.0), segs=12, rings=8))
        for k in range(3):
            a = math.radians(-35 + 35 * k)
            rig.rigid("arm." + side, sphere(0.015, m((0.155 + 0.028 * math.sin(a), -0.15 - 0.012 * math.cos(a),
                                                       0.24 + 0.01 * math.cos(a))), belly, segs=8, rings=5))
        rig.rigid("thigh." + side, limb([m((0.08, 0.02, 0.22)), m((0.085, 0.02, 0.17)), m((0.09, 0.0, 0.05))],
                                        [0.05, 0.047, 0.04], skin, verts=10, per=2, caps=True))
        rig.rigid("foot." + side, ell(m((0.092, -0.04, 0.03)), (0.052, 0.078, 0.03), skin, segs=14, rings=8))
        for k in range(4):
            a = math.radians(-45 + 30 * k)
            rig.rigid("foot." + side, sphere(0.016, m((0.092 + 0.05 * math.sin(a), -0.1 - 0.018 * math.cos(a), 0.02)),
                                             belly, scale=(1, 1, 0.8), segs=8, rings=5))
    # dizzy stars round the head (die only)
    st = []
    for k in range(3):
        a = 2 * math.pi * k / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        st.append(star(STARS + d * 0.17, 0.05, star_m, thick=0.022, face=d))
    rig.rigid("stars", *tiny(st, STARS))
    rig.build("axolotl")

    # ---------------------------------------------------------------- actions
    # written facing -Y: +X tips the body forward, swings a hanging arm back, lifts the tail; -X swings a gill back
    def eyes(k):
        return {"%eye.L": (1, 1, k), "%eye.R": (1, 1, k)}

    def gills(a, ph=0.0, amp=0.0, spread=0.0):
        """All gills rotated by a (about X, + forward-up) with a ripple of amp degrees at phase ph."""
        p = {}
        for g in range(3):
            w = a + amp * math.sin(ph + g * 1.3)
            p["gill%d.L" % (g + 1)] = (w, -spread, 0)
        return mirror(p)

    def arms(l, r, lo=0.0, ro=0.0):
        return {"arm.L": (l, -lo, 0), "arm.R": (r, ro, 0)}

    def legs(l, r, lf=0.0, rf=0.0):
        return {"thigh.L": (l, 0, 0), "thigh.R": (r, 0, 0), "foot.L": (lf, 0, 0), "foot.R": (rf, 0, 0)}

    def tail(a, b=0.0, side=0.0):
        return {"tail1": (a, 0, side), "tail2": (b, 0, side * 1.3)}

    def breathe(k, look=0.0, blink=1.0, ph=0.0):
        return merge({"%body": (1 + 0.015 * k, 1 + 0.015 * k, 1 + 0.03 * k), "head": (-3 * k, 0, look),
                      "@head": (0, 0, 0.004 * k)}, arms(-4 * k, -4 * k, 6, 6), gills(-4 * k, ph, 7),
                     tail(3 * math.sin(ph), 5 * math.sin(ph), 8 * math.sin(ph + 1)), eyes(blink))
    rig.action("idle", {0: breathe(0), 8: breathe(0.5, 0, 1, 1.0), 15: breathe(1, 8, 1, 2.0),
                        22: breathe(0.6, 12, 1, 3.0), 30: breathe(0, 12, 1, 4.0), 36: breathe(0.4, 4, 1, 4.8),
                        40: breathe(0.6, 0, 0.1, 5.3), 43: breathe(0.7, 0, 1, 5.7), 50: breathe(0.8, -6, 1, 6.5),
                        60: breathe(0, 0, 1, 2 * math.pi)}, loop=True)

    def step(p):
        a = 2 * math.pi * p
        s, c = math.sin(a), math.cos(a)
        return merge({"@root": (0, 0, 0.022 * (1 - math.cos(2 * a)) / 2), "body": (7, 6 * s, 0),
                      "head": (-5 + 3 * math.cos(2 * a), -4 * s, 3 * s)},
                     legs(-34 * s, 34 * s, 30 * s - 22 * max(0.0, -c) * (s < 0), -30 * s - 22 * max(0.0, c) * (s > 0)),
                     arms(28 * s, -28 * s, 8, 8), gills(-10, a * 2, 10), tail(-6 + 4 * math.cos(2 * a), -4, 14 * s))
    rig.action("walk", {f: step(f / 15) for f in range(16)}, loop=True)

    crouch = merge({"@root": (0, 0, -0.04), "%body": (1.1, 1.1, 0.86), "body": (10, 0, 0), "head": (-6, 0, 0)},
                   legs(-30, -30, 30, 30), arms(20, 20, 10, 10), gills(10), tail(10, 5), eyes(0.6))
    rise = merge({"@root": (0, 0, 0.0), "%body": (0.94, 0.94, 1.1), "body": (-4, 0, 0), "head": (-8, 0, 0)},
                 legs(-35, -10, 50, 25), arms(-150, -150, 20, 20), gills(-45), tail(-25, -20))
    rig.action("jump", {0: crouch, 3: merge(rise, {"%body": (0.9, 0.9, 1.16), "@root": (0, 0, 0.02)},
                                            legs(10, 10, -10, -10)), 8: rise})

    def paddle(i):
        a = 2 * math.pi * i / 4
        return merge({"%body": (1.02, 1.02, 0.98), "body": (-6, 0, 0), "head": (-10, 0, 0)},
                     arms(-130 - 30 * math.sin(a), -130 + 30 * math.sin(a), 30, 30),
                     legs(-20 + 20 * math.sin(a), -20 - 20 * math.sin(a), 20, 20),
                     gills(40, a, 14, 10), tail(35 + 8 * math.sin(a), 20), eyes(1.1))
    rig.action("fall", {0: paddle(0), 3: paddle(1), 6: paddle(2), 9: paddle(3), 12: paddle(4)}, loop=True)

    puff = merge({"%head": (1.1, 1.0, 1.08), "head": (-10, 0, 0), "body": (-6, 0, 0), "@root": (0, 0.015, 0)},
                 arms(-30, -30, 10, 10), gills(15), eyes(0.5))
    shot = merge({"%head": (0.96, 1.06, 0.96), "head": (8, 0, 0), "body": (12, 0, 0), "@root": (0, -0.035, 0),
                  "%smile": 0.0, "%mouth_o": 1.3}, arms(-75, -75, 12, 12), legs(-10, 20, 0, -10), gills(-30),
                 tail(8, 10), eyes(1.1))
    rig.action("blow", {0: {}, 2: puff, 3: merge(puff, {"%smile": 0.0, "%mouth_o": 0.6}), 4: shot,
                        6: merge(shot, {"head": (4, 0, 0), "body": (6, 0, 0), "%mouth_o": 0.8}), 8: {}})

    shock = merge({"%body": (0.9, 0.9, 1.15), "@root": (0, 0, 0.03), "head": (-12, 0, 0)},
                  arms(-160, -160, 40, 40), legs(-10, 10, 0, 0), gills(40, 0, 0, 15), tail(40, 20), eyes(1.4))
    die = {0: {}, 4: shock}
    for k in range(9):          # two turns, 90 degrees per key, a hop up and down
        f = 4 + 2 * (k + 1)
        h = 0.26 * math.sin(math.pi * (k + 1) / 9)
        die[f] = merge(shock, {"root": (0, 0, 90 * (k + 1)), "@root": (0, 0, 0.03 + h)}, eyes(0.3))
    flop = lambda ang, z, st: merge({"root": (ang, 0, 720), "@root": (0, 0, z), "%stars": 100 if st else 0.0,
                                     "stars": (0, 0, st)},
                                    arms(-120, -120, 60, 60), legs(-50, -50, 20, 20), gills(10, 0, 0, 25),
                                    tail(-20, -10), eyes(0.12))
    die.update({24: flop(-50, 0.12, 0), 28: flop(-88, 0.27, 0), 31: flop(-80, 0.25, 30),
                34: flop(-84, 0.26, 90), 37: flop(-84, 0.26, 160), 40: flop(-84, 0.26, 240)})
    rig.action("die", die)

    def balance(i):
        a = 2 * math.pi * i / 6
        s = math.sin(a)
        return merge({"body": (9 * s, 0, 0), "head": (-5 * s, 0, 0), "@root": (0, 0, 0.012 * math.cos(2 * a))},
                     arms(-80 - 45 * s, -80 + 45 * s, 35, 35), legs(-12, -12, 12, 12),
                     tail(-18 * s, -12 * s), gills(-6 * s, a, 8), eyes(1.0 if i != 3 else 0.2))
    rig.action("ride", {i * 5: balance(i) for i in range(7)}, loop=True)

    def hop(h, up, twist, sq):
        air = h > 0.05
        return merge({"@root": (0, 0, h), "%body": (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq), "body": (0, 0, twist),
                      "head": (-10 if air else 0, 0, -twist * 0.5)},
                     arms(-up, -up, 25, 25), legs(-25 if air else 0, -25 if air else 0, 20 if air else 0, 20 if air else 0),
                     gills(30 if air else 0, 0, 0, 20 if air else 5), tail(-15 if air else 5, -10 if air else 0, twist))
    rig.action("cheer", {0: hop(-0.02, 40, 0, 0.9), 5: hop(0.15, 165, 12, 1.08), 10: hop(-0.02, 60, 0, 0.9),
                         15: hop(0.0, 40, -12, 1.0), 20: hop(0.15, 165, -12, 1.08), 25: hop(-0.02, 60, 0, 0.9),
                         30: hop(-0.02, 40, 0, 0.9)}, loop=True)
    rig.save("axolotl")


# ------------------------------------------------------------------ bubbles (origin at the centre)

def rim_mats():
    return [mat("bubble_rim_pink", (1.0, 0.45, 0.8), 0.1, alpha=0.6, emit=1.4, emit_color=(1.0, 0.4, 0.8)),
            mat("bubble_rim_violet", (0.6, 0.45, 1.0), 0.1, alpha=0.6, emit=1.4, emit_color=(0.55, 0.4, 1.0)),
            mat("bubble_rim_cyan", (0.4, 0.95, 1.0), 0.1, alpha=0.6, emit=1.4, emit_color=(0.35, 0.95, 1.0)),
            mat("bubble_rim_gold", (1.0, 0.9, 0.45), 0.1, alpha=0.6, emit=1.4, emit_color=(1.0, 0.85, 0.4))]


def bubble_parts(R, shell_m):
    """A soap bubble of radius R at the origin: the clear shell, the iridescent rim ring (facing -Y) and glints."""
    shine = mat("bubble_shine", (1, 1, 1), 0.1, emit=4.0)
    rims = rim_mats()
    parts = [sphere(R, (0, 0, 0), shell_m, segs=36, rings=18)]
    # the rim: a thin torus just inside the silhouette, banded like a thin film (pink top, violet left, gold
    # bottom, cyan right), the bands blending through the sectors
    bm = bmesh.new()
    n, m = 64, 6
    Rr, r = R * 0.955, R * 0.03
    rings = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c = Vector((math.cos(a) * Rr, 0, math.sin(a) * Rr))
        out = Vector((math.cos(a), 0, math.sin(a)))
        rings.append([bm.verts.new(c + out * r * math.cos(2 * math.pi * j / m) * 1.0
                                   + Vector((0, r * 1.6 * math.sin(2 * math.pi * j / m), 0))) for j in range(m)])
    for i in range(n):
        for j in range(m):
            bm.faces.new((rings[i][j], rings[(i + 1) % n][j], rings[(i + 1) % n][(j + 1) % m], rings[i][(j + 1) % m]))
    rim = new_obj("rim", bm, rims[0], smooth=80)
    for mm in rims[1:]:
        rim.data.materials.append(mm)
    order = (2, 0, 1, 3)   # cyan (right), pink (top), violet (left), gold (bottom)
    for p in rim.data.polygons:
        a = math.degrees(math.atan2(p.center.z, p.center.x)) % 360
        p.material_index = order[int(((a + 45 + 10 * math.sin(math.radians(a * 3))) % 360) // 90)]
    parts.append(rim)
    # the window glint, upper left, and a small dot lower right, just inside the front of the shell
    arc = arc_on_sphere(R * 0.97, 118, 162, 0.72)
    parts.append(tube(arc, [0.006, 0.012, 0.017, 0.02, 0.021, 0.02, 0.017, 0.012, 0.006], shine, verts=6))
    arc2 = arc_on_sphere(R * 0.97, 128, 146, 0.52, n=5)
    parts.append(tube(arc2, [0.004, 0.008, 0.009, 0.008, 0.004], shine, verts=5))
    d = Vector((0.5, -0.72, -0.42)).normalized()
    parts.append(blob(0.028, d * R * 0.96, shine, (1.0, 0.3, 1.0), d, segs=8, rings=5))
    return parts


def bubble_shell(name, tint=(0.8, 0.95, 1.0), alpha=0.12):
    return mat(name, tint, 0.03, coat=1.0, alpha=alpha, emit=0.3, emit_color=tint)


def bubble():
    simple(bubble_parts(0.45, bubble_shell("bubble")), "bubble")


def bubble_trap():
    simple(bubble_parts(0.5, bubble_shell("bubble")), "bubble_trap")


def special_bubble_water():
    parts = bubble_parts(0.45, bubble_shell("bubble_water", (0.45, 0.8, 1.0), 0.2))
    core = mat("water_core", (0.15, 0.55, 1.0), 0.05, coat=1.0, emit=1.6, emit_color=(0.1, 0.5, 1.0))
    wsh = mat("water_shine", (0.85, 0.97, 1.0), 0.1, emit=4.0)
    drop = lathe_r([(0.0, 0.2), (0.025, 0.15), (0.06, 0.08), (0.1, 0.0), (0.118, -0.06), (0.105, -0.12),
                    (0.065, -0.162), (0.0, -0.175)], core, segs=24, smooth=80)
    parts.append(drop)
    parts.append(glint((-0.045, -0.105, -0.02), 0.03, wsh, stretch=2.0))
    parts.append(sphere(0.012, (0.05, -0.1, -0.1), wsh, segs=6, rings=4))
    for c, r in (((0.2, 0.0, 0.14), 0.04), ((-0.19, 0.02, -0.12), 0.032)):
        parts.append(lathe_r([(0.0, 0.07 * r / 0.04), (0.02 * r / 0.04, 0.03 * r / 0.04), (r, -0.01),
                              (r * 0.85, -0.035 * r / 0.04), (0.0, -r * 1.05)], core, segs=14, smooth=80,
                             center=(c[0], c[1], 0)))
        parts[-1].data.transform(Matrix.Translation((0, 0, c[2])))
    simple(parts, "special_bubble_water")


def flame(h, r, material, seed, lick=0.3):
    """A flame standing at the origin: a lathe tapering to a curled tip, with tongues."""
    prof = [(0.0, h)] + [(r * math.sin(math.pi * (1 - t) ** 0.8) * (0.25 + 0.75 * (1 - t)) ** 0.6 + 0.001, h * t)
                         for t in (0.85, 0.7, 0.55, 0.4, 0.25, 0.12, 0.04)] + [(0.0, -0.02)]
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    o = lathe_r(prof, material, segs=24, radial=lambda k, z: 1 + lick * max(0.0, z / h) * math.sin(
        5 * 2 * math.pi * k / 24 + ph[0] + 3 * z), smooth=70)
    for v in o.data.vertices:     # a lean and a curl near the top
        t = max(0.0, v.co.z / h)
        v.co.x += 0.05 * r * math.sin(3.0 * t + ph[1]) * t * 4
    o.data.update()
    return o


def special_bubble_fire():
    parts = bubble_parts(0.45, bubble_shell("bubble_fire", (1.0, 0.7, 0.45), 0.2))
    outer = mat("fire_core", (1.0, 0.35, 0.05), 0.4, emit=4.0, emit_color=(1.0, 0.3, 0.03))
    hot = mat("fire_core_hot", (1.0, 0.88, 0.4), 0.3, emit=6.0, emit_color=(1.0, 0.8, 0.3))
    f1 = flame(0.42, 0.15, outer, 3)
    f1.data.transform(Matrix.Translation((0, 0.02, -0.2)))
    f2 = flame(0.26, 0.09, hot, 7, lick=0.2)
    f2.data.transform(Matrix.Translation((0.0, -0.06, -0.2)))
    parts += [f1, f2]
    for x, z, s in ((-0.16, -0.08, 0.3), (0.15, -0.13, 0.25)):
        f = flame(0.12 * s / 0.3, 0.045, outer, 11 + int(x * 100))
        f.data.transform(Matrix.Translation((x, 0.0, z)))
        parts.append(f)
    simple(parts, "special_bubble_fire")


def special_bubble_bolt():
    parts = bubble_parts(0.45, bubble_shell("bubble_bolt", (1.0, 0.95, 0.55), 0.2))
    core = mat("bolt_core", (1.0, 0.92, 0.3), 0.3, emit=5.0, emit_color=(1.0, 0.88, 0.25))
    glow = mat("bolt_glow", (1.0, 0.55, 0.1), 0.3, alpha=0.8, emit=2.5, emit_color=(1.0, 0.5, 0.05))
    poly = [(0.07, 0.3), (-0.13, 0.0), (0.0, 0.0), (-0.09, -0.3), (0.14, 0.05), (0.02, 0.05), (0.13, 0.3)]
    poly = poly[::-1] if sum((b[0] - a[0]) * (b[1] + a[1]) for a, b in zip(poly, poly[1:] + poly[:1])) > 0 else poly
    parts.append(prism(poly, 0.07, (0, -0.01, 0), core, bevel=0.015, segs=2))
    big = [(x * 1.28 - 0.0, z * 1.18) for x, z in poly]
    parts.append(prism(big, 0.035, (0, 0.04, 0), glow, bevel=0.01, segs=1))
    simple(parts, "special_bubble_bolt")


def letter_bubble():
    parts = bubble_parts(0.45, bubble_shell("bubble"))
    st = mat("letter_star", (1.0, 0.86, 0.4), 0.25, coat=0.6, emit=0.8, emit_color=(1.0, 0.75, 0.3))
    parts.append(star((0, 0.06, -0.01), 0.3, st, thick=0.07))
    simple(parts, "letter_bubble")


# ------------------------------------------------------------------ tin toys (written facing -Y)

def toy_mats(paint, stripe):
    return dict(paint=mat("toy_paint", paint, 0.2, metal=0.25, coat=1.0),
                stripe=mat("toy_stripe", stripe, 0.22, metal=0.2, coat=1.0),
                metal=mat("toy_metal", (0.78, 0.8, 0.86), 0.2, metal=0.85, emit=0.08, emit_color=(0.7, 0.75, 0.85)),
                brass=mat("toy_brass", (1.0, 0.74, 0.28), 0.22, metal=0.85, emit=0.2, emit_color=(1.0, 0.65, 0.2)),
                rubber=mat("toy_rubber", (0.14, 0.12, 0.18), 0.55),
                eye=mat("toy_eye", (1.0, 1.0, 1.0), 0.15, coat=0.8, emit=0.2),
                pupil=mat("toy_pupil", (0.03, 0.03, 0.06), 0.1, coat=1.0),
                shine=mat("toy_shine", (1, 1, 1), 0.2, emit=4.0),
                glow=mat("toy_glow", (1.0, 0.9, 0.45), 0.3, emit=5.0, emit_color=(1.0, 0.8, 0.3)))


def googly(rig, M, side, c, d, r, pupil_r):
    """A googly eye at c looking along d: a white dome with a black pupil on bone pupil.<side> (rotates about c)."""
    d = Vector(d).normalized()
    rig.rigid("body", blob(r, c, M["eye"], (1.0, 0.7, 1.0), d, segs=16, rings=10),
              torus(r * 0.98, r * 0.12, c, M["brass"], rot=tuple(
                  Vector((0, 0, 1)).rotation_difference(d).to_euler()), verts=18, minor=5))
    pc = Vector(c) + d * r * 0.62 + Vector((0, 0, -r * 0.2))
    rig.rigid("pupil." + side, blob(pupil_r, pc, M["pupil"], (1.0, 0.45, 1.0), d, segs=12, rings=7),
              sphere(pupil_r * 0.32, pc + d * pupil_r * 0.4 + Vector((0.3 * pupil_r, -0.2 * pupil_r, 0.35 * pupil_r)),
                     M["shine"], segs=6, rings=4))


def toy_beetle():
    M = toy_mats((0.1, 0.72, 0.55), (1.0, 0.86, 0.3))
    SC = Vector((0, 0.05, 0.2))     # shell centre
    SR = (0.25, 0.31, 0.3)
    KEY0 = Vector((0, 0.2, 0.43))
    KD = Vector((0, 0.45, 1.0)).normalized()
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0.0, 0.1), (0, 0.0, 0.45), "root"),
         "head": ((0, -0.2, 0.2), (0, -0.36, 0.2), "body"),
         "key": (tuple(KEY0), tuple(KEY0 + KD * 0.2), "body")}
    legs = []
    for s, side in ((1, "L"), (-1, "R")):
        for i, y in enumerate((-0.14, 0.04, 0.2)):
            hip = (0.18 * s, y, 0.14)
            foot = (0.31 * s, y + (i - 1) * 0.03, 0.025)
            B["leg%d.%s" % (i + 1, side)] = (hip, foot, "body")
            legs.append((s, side, i, Vector(hip), Vector(foot)))
    for s, side in ((1, "L"), (-1, "R")):
        B["pupil." + side] = ((0.085 * s, -0.33, 0.33), (0.085 * s, -0.4, 0.34), "head")
    rig = TurnRig(B, 75, fps=FPS)
    # the shell: a domed tin body, a seam and spots, a band round its skirt, rivets
    sh = hemi(1.0, (0, 0, 0), (0, 0, 1), M["paint"], cut=-0.22, segs=32, rings=18)
    sh.data.transform(Matrix.Translation(SC) @ Matrix.Diagonal((*SR, 1)))
    rig.rigid("body", sh)
    seam = [ell_point(SC, SR, (0, -math.cos(math.radians(a)), math.sin(math.radians(a)))) for a in range(20, 161, 14)]
    rig.rigid("body", tube(seam, [0.014] * len(seam), M["stripe"], verts=6))
    for s in (1, -1):
        for d, r in (((0.5, -0.35, 0.75), 0.05), ((0.75, 0.2, 0.55), 0.058), ((0.45, 0.62, 0.62), 0.045)):
            dd = Vector((d[0] * s, d[1], d[2])).normalized()
            rig.rigid("body", blob(r, ell_point(SC, SR, dd), M["stripe"], (1.0, 0.25, 1.0), dd, segs=12, rings=7))
    band = torus(1.0, 0.05, (0, 0, 0), M["stripe"], verts=40, minor=6)
    band.data.transform(Matrix.Translation((SC.x, SC.y, 0.15)) @ Matrix.Diagonal((SR[0] * 0.985, SR[1] * 0.985, 0.6, 1)))
    rig.rigid("body", band)
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        p = Vector((math.cos(a) * SR[0] * 1.03, SC.y + math.sin(a) * SR[1] * 1.03, 0.15))
        rig.rigid("body", sphere(0.014, p, M["brass"], segs=6, rings=4))
    rig.rigid("body", ell((0, 0.05, 0.12), (0.2, 0.26, 0.035), M["metal"], segs=18, rings=6))
    # head: a round tin face in the stripe colour, googly eyes on top, a smile, antennae
    HC = Vector((0, -0.28, 0.22))
    rig.rigid("head", ell(HC, (0.15, 0.11, 0.12), M["stripe"], segs=20, rings=12))
    sm = [ell_point(HC, (0.15, 0.11, 0.12), (x, -1, -0.35 + 0.5 * x * x)) + Vector((0, -0.003, 0))
          for x in (-0.5, -0.25, 0, 0.25, 0.5)]
    rig.rigid("head", tube(sm, [0.007, 0.01, 0.011, 0.01, 0.007], M["rubber"], verts=5))
    for s, side in ((1, "L"), (-1, "R")):
        googly(rig, M, side, (0.085 * s, -0.31, 0.32), (0.35 * s, -0.8, 0.35), 0.075, 0.042)
        a0 = Vector((0.05 * s, -0.25, 0.32))
        rig.rigid("head", tube([a0, a0 + Vector((0.03 * s, -0.05, 0.1)), a0 + Vector((0.07 * s, -0.13, 0.16))],
                               [0.012, 0.01, 0.009], M["metal"], verts=6),
                  sphere(0.03, a0 + Vector((0.075 * s, -0.14, 0.17)), M["glow"], segs=10, rings=6))
    # the wind-up key on the back
    ax = KD
    side = Vector((1, 0, 0))
    kparts = [rod(KEY0 - ax * 0.04, KEY0 + ax * 0.13, 0.018, M["brass"], verts=8),
              cyl(0.035, 0.02, (0, 0, 0), M["brass"], verts=12)]
    kparts[-1].data.transform(Matrix.Translation(KEY0 + ax * 0.02) @ Vector((0, 0, 1)).rotation_difference(ax)
                              .to_matrix().to_4x4())
    for sg in (1, -1):
        c = KEY0 + ax * 0.17 + side * 0.065 * sg
        o = torus(0.058, 0.02, (0, 0, 0), M["brass"], verts=20, minor=6)
        o.data.transform(Matrix.Diagonal((1, 1.0, 0.85, 1)) @ Matrix.Rotation(R90, 4, "Y"))
        q = Vector((0, 0, 1)).rotation_difference(ax).to_matrix().to_4x4()
        o.data.transform(q)
        o.data.transform(Matrix.Translation(c))
        kparts.append(o)
    kparts.append(sphere(0.03, KEY0 + ax * 0.17, M["brass"], segs=10, rings=6))
    rig.rigid("key", *kparts)
    # six legs with brass feet
    for s, side, i, hip, foot in legs:
        knee = hip.lerp(foot, 0.45) + Vector((0.03 * s, 0, 0.08))
        rig.rigid("leg%d.%s" % (i + 1, side), limb([hip, knee, foot], [0.02, 0.018, 0.016], M["rubber"], verts=7,
                                                    per=3),
                  sphere(0.03, foot, M["brass"], scale=(1, 1.2, 0.8), segs=10, rings=6))
    rig.build("toy_beetle")

    def pupils(a, b):
        return {"pupil.L": (a, 0, b), "pupil.R": (a, 0, -b)}

    def scuttle(p):
        a = 2 * math.pi * p
        s = math.sin(a)
        pose = {"@root": (0, 0, 0.012 * abs(math.sin(2 * a))), "body": (2, 3 * math.sin(2 * a), 0),
                "head": (4 * math.sin(2 * a), 0, 5 * s), "key": about(tuple(KD), -360 * p)}
        for sd, side in ((1, "L"), (-1, "R")):
            for i in range(3):
                ph = a + (math.pi if (i + (sd < 0)) % 2 else 0)
                sw = 28 * math.sin(ph)
                lift = 25 * max(0.0, math.cos(ph))
                pose["leg%d.%s" % (i + 1, side)] = (0, -lift * sd, sw)
        return merge(pose, pupils(8 * math.sin(2 * a), 10 * s))
    rig.action("walk", {f: scuttle(f / 15) for f in range(16)}, loop=True)

    def kick(p):
        a = 2 * math.pi * p
        rot = (15 * math.sin(a), 180 + 18 * math.sin(2 * a), 0)
        pose = {"root": rot, "%root": 0.85, "@root": centred(SC + Vector((0, -0.05, 0.02)), rot, 0.85),
                "head": (-15 + 10 * math.sin(4 * a), 0, 0), "key": about(tuple(KD), -720 * p)}
        for sd, side in ((1, "L"), (-1, "R")):
            for i in range(3):
                ph = 4 * a + i * 2.1 + (sd < 0) * 1.0
                pose["leg%d.%s" % (i + 1, side)] = (0, -(25 + 25 * math.sin(ph)) * sd, 35 * math.cos(ph))
        return merge(pose, pupils(30 * math.sin(4 * a), 40 * math.cos(4 * a)))
    rig.action("trapped", {f: kick(f / 15) for f in range(16)}, loop=True)
    rig.save("toy_beetle")


def helix(r, z0, z1, turns, wire, material, per=14):
    pts = []
    n = int(turns * per)
    for k in range(n + 1):
        t = k / n
        a = 2 * math.pi * turns * t
        pts.append((r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * t))
    return tube(pts, [wire] * len(pts), material, verts=7, caps=True)


def toy_spring():
    M = toy_mats((0.95, 0.55, 0.12), (0.2, 0.55, 1.0))
    Z0, Z1 = 0.05, 0.3
    B = {"root": ((0, 0, 0), (0, 0, 0.05), None),
         "spring": ((0, 0, Z0), (0, 0, Z1), "root"),
         "body": ((0, 0, Z1), (0, 0, 0.62), "root"),
         "antenna": ((0, 0, 0.6), (0, 0, 0.72), "body")}
    for s, side in ((1, "L"), (-1, "R")):
        B["arm." + side] = ((0.19 * s, 0.0, 0.45), (0.25 * s, -0.02, 0.3), "body")
        B["pupil." + side] = ((0.08 * s, -0.19, 0.48), (0.08 * s, -0.25, 0.48), "body")
    rig = TurnRig(B, 75, fps=FPS)
    # the pad foot and the coil
    rig.rigid("root", cyl(0.13, 0.05, (0, 0, 0.025), M["rubber"], verts=24, bevel=0.015, segs=2),
              torus(0.125, 0.012, (0, 0, 0.05), M["brass"], verts=24, minor=5))
    rig.rigid("spring", helix(0.085, Z0 + 0.01, Z1 + 0.01, 4.5, 0.016, M["metal"]))
    # the tin-can body: rounded can, two bands, rivets, big lens eyes, a grille mouth, ear bolts
    can = lathe_r([(0.0, 0.62), (0.15, 0.62), (0.185, 0.605), (0.198, 0.57), (0.198, 0.34), (0.185, 0.305),
                   (0.15, 0.29), (0.0, 0.29)], M["paint"], segs=32, smooth=50)
    rig.rigid("body", can, cyl(0.1, 0.03, (0, 0, 0.285), M["metal"], verts=16))
    for z in (0.33, 0.585):
        rig.rigid("body", torus(0.2, 0.016, (0, 0, z), M["stripe"], verts=32, minor=6))
        for k in range(10):
            a = 2 * math.pi * (k + 0.5) / 10
            rig.rigid("body", sphere(0.012, (math.cos(a) * 0.215, math.sin(a) * 0.215, z), M["brass"], segs=6,
                                     rings=4))
    for s, side in ((1, "L"), (-1, "R")):
        c = Vector((0.08 * s, -0.185, 0.47))
        d = Vector((0.3 * s, -1, 0.05)).normalized()
        googly(rig, M, side, c, d, 0.066, 0.036)
        rig.rigid("body", cyl(0.035, 0.05, (0.2 * s, 0.0, 0.47), M["brass"], rot=(0, R90, 0), verts=12, bevel=0.01))
    rig.rigid("body", box((0.16, 0.03, 0.06), (0, -0.19, 0.375), M["metal"], bevel=0.012))
    for k in range(4):
        rig.rigid("body", box((0.012, 0.012, 0.042), (-0.045 + 0.03 * k, -0.206, 0.375), M["rubber"], bevel=0.004))
    rig.rigid("antenna", rod((0, 0, 0.6), (0, 0, 0.74), 0.012, M["metal"], verts=6),
              sphere(0.045, (0, 0, 0.77), M["glow"], segs=12, rings=8),
              torus(0.03, 0.01, (0, 0, 0.73), M["brass"], verts=12, minor=4))
    for s, side in ((1, "L"), (-1, "R")):
        m = lambda p: Vector((p[0] * s, p[1], p[2]))
        rig.rigid("arm." + side, limb([m((0.18, 0.0, 0.45)), m((0.23, 0.0, 0.42)), m((0.25, -0.02, 0.32))],
                                      [0.018, 0.017, 0.016], M["metal"], verts=7, per=3),
                  sphere(0.028, m((0.25, -0.02, 0.31)), M["brass"], segs=8, rings=6))
        for sg in (1, -1):
            rig.rigid("arm." + side, ell(m((0.25, -0.02 + 0.02 * sg, 0.27)), (0.012, 0.018, 0.04), M["stripe"],
                                         pitch=20 * sg, segs=8, rings=6))
    rig.build("toy_spring")
    L = Z1 - Z0

    def pupils(a, b):
        return {"pupil.L": (a, 0, b), "pupil.R": (a, 0, -b)}

    def pose(h, k, arm, lean=0.0, sq=1.0, ant=0.0):
        """h: root height, k: spring length factor (the body rides on the coil top)."""
        return merge({"@root": (0, 0, h), "%spring": (1, 1, k), "@body": (0, 0, -L * (1 - k)),
                      "%body": (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq), "body": (lean, 0, 0),
                      "antenna": (ant, 0, 0)},
                     mirror({"arm.L": (-arm, -20, 0)}), pupils(-ant * 0.5, 0))
    rig.action("walk", {0: pose(0.0, 0.5, 20, 8, 0.9, 25), 3: pose(0.02, 1.2, 60, -4, 1.08, -15),
                        6: pose(0.17, 1.05, 80, 0, 1.03, -30), 8: pose(0.2, 0.95, 70, 3, 1.0, 5),
                        11: pose(0.08, 1.15, 40, 6, 1.02, 20), 13: pose(0.0, 0.7, 25, 8, 0.94, 30),
                        15: pose(0.0, 0.5, 20, 8, 0.9, 25)}, loop=True)

    def curl(p):
        a = 2 * math.pi * p
        rot = (10 * math.sin(2 * a), 165 + 20 * math.sin(a), 0)
        k = 0.4
        c = Vector((0, 0, 0.3 - L * (1 - k) * 0.5))
        return merge({"root": rot, "%root": 0.85, "@root": centred(c, rot, 0.85), "%spring": (1, 1, k + 0.05 * math.sin(4 * a)),
                      "@body": (0, 0, -L * (1 - k)), "antenna": (30 * math.sin(3 * a), 0, 0)},
                     {"arm.L": (-120 + 50 * math.sin(4 * a), -40, 0), "arm.R": (-120 - 50 * math.sin(4 * a), 40, 0)},
                     pupils(30 * math.sin(4 * a), 40 * math.cos(4 * a)))
    rig.action("trapped", {f: curl(f / 15) for f in range(16)}, loop=True)
    rig.save("toy_spring")


def toy_flyer():
    M = toy_mats((0.62, 0.35, 1.0), (1.0, 0.82, 0.2))
    C = Vector((0, 0, 0.36))
    CR = (0.21, 0.23, 0.2)
    B = {"root": ((0, 0, 0), (0, 0, 0.08), None),
         "body": ((0, 0, 0.16), (0, 0, 0.56), "root"),
         "prop": ((0, 0, 0.6), (0, 0, 0.72), "body"),
         "legs": ((0, 0, 0.18), (0, 0, 0.04), "body"),
         "tail": ((0, 0.2, 0.4), (0, 0.34, 0.5), "body")}
    for s, side in ((1, "L"), (-1, "R")):
        B["wing." + side] = ((0.19 * s, 0.03, 0.37), (0.36 * s, 0.06, 0.4), "body")
        B["pupil." + side] = ((0.09 * s, -0.19, 0.44), (0.09 * s, -0.25, 0.44), "body")
    rig = TurnRig(B, 75, fps=FPS)
    rig.rigid("body", ell(C, CR, M["paint"], segs=28, rings=16))
    rig.rigid("body", blob(0.15, ell_point(C, CR, (0, -0.75, -0.66)), M["stripe"], (1.2, 0.3, 1.0),
                           (0, -0.75, -0.66), segs=14, rings=8))       # a cream belly patch
    band = torus(1.0, 0.035, (0, 0, 0), M["stripe"], verts=36, minor=6)
    band.data.transform(Matrix.Translation(C) @ Matrix.Diagonal((CR[0], 1, CR[2], 1)) @ Matrix.Rotation(R90, 4, "X"))
    band.data.transform(Matrix.Translation((0, 0.06, 0)))
    rig.rigid("body", band)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        rig.rigid("body", sphere(0.012, (C.x + math.cos(a) * CR[0] * 1.02, 0.06, C.z + math.sin(a) * CR[2] * 1.02),
                                 M["brass"], segs=6, rings=4))
    # the beak cone and the eyes
    rig.rigid("body", rod((0, -0.19, 0.35), (0, -0.33, 0.33), 0.055, M["brass"], r2=0.012, verts=14))
    for s, side in ((1, "L"), (-1, "R")):
        googly(rig, M, side, (0.09 * s, -0.175, 0.445), (0.4 * s, -0.8, 0.3), 0.07, 0.038)
    # the propeller: a mast, a brass hub, three blades
    rig.rigid("body", rod((0, 0, 0.54), (0, 0, 0.64), 0.015, M["metal"], verts=6),
              torus(0.035, 0.012, (0, 0, 0.555), M["brass"], verts=14, minor=4))
    blades = [sphere(0.035, (0, 0, 0.66), M["brass"], segs=12, rings=8)]
    for k in range(3):
        a = 2 * math.pi * k / 3
        o = ell((0.13, 0, 0), (0.12, 0.035, 0.008), M["stripe"], segs=12, rings=6)
        o.data.transform(Matrix.Rotation(math.radians(18), 4, "X"))
        o.data.transform(Matrix.Translation((0, 0, 0.66)) @ Matrix.Rotation(a, 4, "Z"))
        blades.append(o)
        tipc = Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, 0.66))
        blades.append(sphere(0.02, tipc, M["paint"], scale=(1.0, 1.0, 0.5), segs=8, rings=5))
    rig.rigid("prop", *blades)
    # stubby wings, a tail fin, dangling wire legs with ball feet
    for s, side in ((1, "L"), (-1, "R")):
        w = ell((0.3 * s, 0.05, 0.38), (0.12, 0.075, 0.018), M["stripe"], roll=-12 * s, segs=14, rings=8)
        rig.rigid("wing." + side, w, sphere(0.02, (0.2 * s, 0.03, 0.37), M["brass"], segs=6, rings=4))
    fin = fin_yz([(0.16, 0.38), (0.3, 0.44), (0.37, 0.58), (0.3, 0.57), (0.2, 0.5)], M["stripe"], thick=0.03)
    rig.rigid("tail", fin, sphere(0.02, (0, 0.36, 0.575), M["brass"], segs=8, rings=5))
    for s in (1, -1):
        rig.rigid("legs", tube([(0.07 * s, 0.0, 0.2), (0.075 * s, 0.0, 0.12), (0.08 * s, -0.01, 0.05)],
                               [0.01, 0.01, 0.01], M["metal"], verts=6),
                  sphere(0.035, (0.08 * s, -0.02, 0.035), M["rubber"], scale=(1, 1.3, 1), segs=10, rings=6))
    rig.build("toy_flyer")

    def pupils(a, b):
        return {"pupil.L": (a, 0, b), "pupil.R": (a, 0, -b)}

    def fly(p):
        a = 2 * math.pi * p
        return merge({"@root": (0, 0, 0.03 * math.sin(a)), "body": (8 + 3 * math.cos(a), 0, 0),
                      "prop": (0, 0, 360 * p), "legs": (15 + 12 * math.sin(a + 1), 0, 0),
                      "tail": (8 * math.sin(a), 0, 0)},
                     {"wing.L": (0, -32 * math.sin(2 * a), 0), "wing.R": (0, 32 * math.sin(2 * a), 0)},
                     pupils(4 * math.sin(a), 0))
    rig.action("fly", {f: fly(f / 15) for f in range(0, 16, 1)}, loop=True)

    def flail(p):
        a = 2 * math.pi * p
        rot = (12 * math.sin(a), 160 + 18 * math.sin(2 * a), 0)
        return merge({"root": rot, "%root": 0.85, "@root": centred(C, rot, 0.85),
                      "prop": (0, 0, 120 * p), "legs": (-40 + 30 * math.sin(4 * a), 0, 0),
                      "tail": (15 * math.sin(4 * a), 0, 0)},
                     {"wing.L": (0, -40 * math.sin(4 * a) - 20, 0), "wing.R": (0, 40 * math.sin(4 * a) + 20, 0)},
                     pupils(30 * math.sin(4 * a), 40 * math.cos(4 * a)))
    rig.action("trapped", {f: flail(f / 15) for f in range(16)}, loop=True)
    rig.save("toy_flyer")


# ------------------------------------------------------------------ treats (origin at the base, facing -Y)

def shine_m():
    return mat("treat_shine", (1, 1, 1), 0.1, emit=5.0)


def treat_cherry():
    red = mat("treat_cherry", (0.9, 0.02, 0.1), 0.15, coat=1.0, emit=0.2, emit_color=(1.0, 0.05, 0.15))
    stem = mat("treat_stem", (0.42, 0.55, 0.14), 0.55)
    leaf = mat("treat_leaf", (0.25, 0.75, 0.18), 0.4, coat=0.5, emit=0.1)
    sh = shine_m()
    parts = []
    prof = [(0.0, 0.205), (0.035, 0.225), (0.085, 0.218), (0.122, 0.17), (0.13, 0.11), (0.112, 0.045),
            (0.065, 0.008), (0.0, 0.0)]
    for x, y, k in ((-0.11, 0.02, 0.95), (0.1, -0.03, 1.0)):
        c = lathe_r([(r * k, z * k) for r, z in prof], red, segs=24, smooth=80, center=(x, y, 0))
        parts.append(c)
        top = Vector((x, y, 0.21 * k))
        parts.append(tube([top + Vector((0, 0, -0.015)), top + Vector((x * 0.1, 0, 0.1)),
                           Vector((x * 0.35 + 0.02, 0.0, 0.4)), Vector((0.02, 0.0, 0.47))],
                          [0.012, 0.011, 0.01, 0.01], stem, verts=6))
        parts.append(glint((x - 0.05 * k, y - 0.1 * k, 0.15 * k), 0.028 * k, sh, face=(-0.4, -1, 0.3), stretch=1.8))
        parts.append(sphere(0.01 * k, (x + 0.05, y - 0.115, 0.07), sh, segs=6, rings=4))
    lf = ell((0.0, 0, 0), (0.1, 0.012, 0.042), leaf, segs=14, rings=6)
    lf.data.transform(Matrix.Translation((0.1, 0.0, 0.5)) @ Matrix.Rotation(math.radians(-25), 4, "Y"))
    parts.append(lf)
    parts.append(rod((0.02, -0.013, 0.47), (0.18, -0.013, 0.54), 0.004, stem, verts=4))
    simple(parts, "treat_cherry")


def treat_melon():
    rind = mat("treat_melon_rind", (0.1, 0.45, 0.15), 0.35, coat=0.6)
    pale = mat("treat_melon_pale", (0.75, 0.95, 0.6), 0.5)
    flesh = mat("treat_melon", (1.0, 0.18, 0.28), 0.3, coat=0.6, emit=0.2, emit_color=(1.0, 0.2, 0.3))
    seed_m = mat("treat_seed", (0.08, 0.05, 0.05), 0.2, coat=1.0)
    sh = shine_m()
    R, apex, half = 0.5, 0.5, 34

    def sector(r, n=14):
        pts = [(0.0, apex)]
        for k in range(n + 1):
            a = math.radians(-90 - half + 2 * half * k / n)
            pts.append((r * math.cos(a), apex + r * math.sin(a)))
        return pts[::-1] if False else pts
    parts = [prism(sector(R), 0.13, (0, 0, 0), rind, bevel=0.02, segs=2),
             prism(sector(R - 0.04), 0.136, (0, 0, 0), pale, bevel=0.012, segs=2),
             prism(sector(R - 0.06), 0.142, (0, 0, 0), flesh, bevel=0.012, segs=2)]
    for p in parts:
        p.data.transform(Matrix.Translation((0, 0, 0)))
    rnd = random.Random(4)
    for k, (x, z) in enumerate(((-0.07, 0.18), (0.06, 0.2), (0.0, 0.3), (-0.1, 0.1), (0.1, 0.11), (0.0, 0.12),
                                (0.03, 0.4))):
        parts.append(blob(0.018, (x, -0.074, z), seed_m, (0.6, 0.3, 1.0), (0, -1, 0), segs=8, rings=5))
        parts[-1].data.transform(Matrix.Translation((x, 0, z)) @ Matrix.Rotation(math.radians(-x * 150), 4, "Y")
                                 @ Matrix.Translation((-x, 0, -z)))
    parts.append(glint((-0.1, -0.074, 0.3), 0.012, sh, stretch=2.4))
    for o in parts:
        o.data.transform(Matrix.Rotation(math.radians(-18), 4, "Z"))
    simple(parts, "treat_melon")


def treat_cupcake():
    wrap_m = mat("treat_wrapper", (0.3, 0.78, 0.8), 0.45, coat=0.3)
    cake = mat("treat_cake", (0.78, 0.5, 0.28), 0.7)
    icing = mat("treat_icing", (1.0, 0.55, 0.75), 0.25, coat=0.8, emit=0.15)
    red = mat("treat_cherry", (0.9, 0.02, 0.1), 0.15, coat=1.0, emit=0.2, emit_color=(1.0, 0.05, 0.15))
    stem = mat("treat_stem", (0.42, 0.55, 0.14), 0.55)
    sh = shine_m()
    spr = [mat("treat_sprinkle_%s" % n, c, 0.3, emit=0.3) for n, c in
           (("a", (1.0, 0.9, 0.2)), ("b", (0.3, 0.6, 1.0)), ("c", (1.0, 1.0, 1.0)), ("d", (0.4, 0.9, 0.3)))]
    parts = [lathe_r([(0.19, 0.2), (0.175, 0.14), (0.155, 0.06), (0.14, 0.0), (0.0, 0.0)], wrap_m, segs=32,
                     radial=lambda k, z: 1.0 + 0.06 * (k % 2), smooth=0),
             ell((0, 0, 0.2), (0.19, 0.19, 0.06), cake, segs=24, rings=10)]
    parts.append(torus(0.19, 0.012, (0, 0, 0.2), wrap_m, verts=32, minor=4))
    for r, th, z in ((0.155, 0.058, 0.26), (0.115, 0.052, 0.32), (0.07, 0.046, 0.375)):
        parts.append(torus(r, th, (0, 0, z), icing, verts=28, minor=10))
    parts.append(lathe_r([(0.0, 0.455), (0.02, 0.44), (0.045, 0.41), (0.05, 0.39), (0.0, 0.37)], icing, segs=16))
    parts.append(sphere(0.052, (0.0, -0.01, 0.47), red, segs=16, rings=10))
    parts.append(tube([(0, -0.01, 0.51), (0.01, 0.0, 0.56), (0.04, 0.02, 0.6)], [0.008, 0.007, 0.006], stem, verts=5))
    parts.append(glint((-0.018, -0.055, 0.49), 0.013, sh))
    rnd = random.Random(9)
    for k in range(16):
        a = rnd.uniform(math.pi * 1.05, math.pi * 1.95) if k < 11 else rnd.uniform(0, math.pi * 2)
        ring = rnd.choice(((0.155, 0.058, 0.26), (0.115, 0.052, 0.32), (0.07, 0.046, 0.375)))
        r, th, z = ring
        b = rnd.uniform(0.2, 1.3)
        p = Vector((math.cos(a) * (r + th * math.cos(b)), math.sin(a) * (r + th * math.cos(b)), z + th * math.sin(b)))
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3))).normalized() * 0.013
        parts.append(rod(p - d, p + d, 0.006, spr[k % 4], verts=5))
    parts.append(glint((-0.09, -0.12, 0.3), 0.02, sh, face=(-0.5, -1, 0.3)))
    simple(parts, "treat_cupcake")


def treat_icecream():
    cone = mat("treat_cone", (0.92, 0.66, 0.34), 0.6)
    grid = mat("treat_cone_grid", (0.7, 0.42, 0.18), 0.7)
    pink = mat("treat_scoop_pink", (1.0, 0.62, 0.72), 0.35, coat=0.5, emit=0.1)
    mint = mat("treat_scoop_mint", (0.55, 0.92, 0.72), 0.35, coat=0.5, emit=0.1)
    chip = mat("treat_choc", (0.28, 0.14, 0.08), 0.4, coat=0.5)
    red = mat("treat_cherry", (0.9, 0.02, 0.1), 0.15, coat=1.0, emit=0.2, emit_color=(1.0, 0.05, 0.15))
    stem = mat("treat_stem", (0.42, 0.55, 0.14), 0.55)
    sh = shine_m()
    TOP, RC = 0.26, 0.11
    parts = [lathe_r([(0.0, TOP), (RC, TOP), (0.0, 0.0)], cone, segs=24, smooth=40),
             torus(RC, 0.018, (0, 0, TOP), cone, verts=24, minor=6)]
    for sg in (1, -1):
        for k in range(8):
            pts = []
            for i in range(7):
                t = 0.08 + 0.9 * i / 6
                a = 2 * math.pi * k / 8 + sg * 1.4 * t
                pts.append((math.cos(a) * RC * t * 1.03, math.sin(a) * RC * t * 1.03, TOP * t))
            parts.append(tube(pts, [0.005] * 7, grid, verts=4))
    # two scoops with a wavy skirt, a drip, chips on the mint, a cherry
    parts.append(sphere(0.125, (0, 0, TOP + 0.08), pink, segs=24, rings=14))
    parts.append(torus(0.12, 0.03, (0, 0, TOP + 0.02), pink, verts=24, minor=6))
    for k in range(10):
        a = 2 * math.pi * k / 10
        parts.append(sphere(0.035, (math.cos(a) * 0.125, math.sin(a) * 0.125, TOP + 0.02), pink, segs=8, rings=6))
    parts.append(ell((-0.05, -0.105, TOP - 0.03), (0.025, 0.02, 0.05), pink, segs=10, rings=6))
    parts.append(sphere(0.02, (-0.05, -0.108, TOP - 0.08), pink, segs=8, rings=5))
    parts.append(sphere(0.1, (0.01, 0.0, TOP + 0.21), mint, segs=22, rings=12))
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.3
        b = 0.3 + 0.5 * (k % 3) / 2
        d = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
        parts.append(ico(0.014, Vector((0.01, 0, TOP + 0.21)) + d * 0.1, chip, sub=1, smooth=0))
    parts.append(sphere(0.045, (0.02, -0.01, TOP + 0.345), red, segs=14, rings=8))
    parts.append(tube([(0.02, -0.01, TOP + 0.38), (0.03, 0.0, TOP + 0.42), (0.06, 0.01, TOP + 0.45)],
                      [0.007, 0.006, 0.005], stem, verts=5))
    parts.append(glint((-0.05, -0.1, TOP + 0.13), 0.02, sh, face=(-0.4, -1, 0.3)))
    parts.append(glint((-0.03, -0.085, TOP + 0.26), 0.017, sh, face=(-0.4, -1, 0.3)))
    simple(parts, "treat_icecream")


def treat_gem():
    gem = mat("treat_gem", (0.1, 0.75, 1.0), 0.05, coat=1.0, emit=1.8, emit_color=(0.05, 0.6, 1.0))
    facet = mat("treat_gem_facet", (0.6, 0.95, 1.0), 0.05, coat=1.0, emit=4.0, emit_color=(0.5, 0.9, 1.0))
    sh = shine_m()
    n, R = 8, 0.21
    zg, zt, crown = 0.28, 0.4, 0.62
    bm = bmesh.new()
    table = [bm.verts.new((crown * R * math.cos(2 * math.pi * (k + 0.5) / n),
                           crown * R * math.sin(2 * math.pi * (k + 0.5) / n), zt)) for k in range(n)]
    gird = [bm.verts.new((R * math.cos(2 * math.pi * k / n), R * math.sin(2 * math.pi * k / n), zg)) for k in range(n)]
    gird2 = [bm.verts.new((R * math.cos(2 * math.pi * k / n), R * math.sin(2 * math.pi * k / n), zg - 0.025))
             for k in range(n)]
    tipv = bm.verts.new((0, 0, 0.0))
    bm.faces.new(table)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((gird[k], gird[j], table[k]))
        bm.faces.new((table[k], table[(k - 1) % n], gird[k]))
        bm.faces.new((gird2[k], gird2[j], gird[j], gird[k]))
        bm.faces.new((gird2[j], gird2[k], tipv))
    g = new_obj("gem", bm, gem, smooth=0)
    g.data.materials.append(facet)
    for p in g.data.polygons:
        if p.normal.z > 0.3:
            p.material_index = 1
    g.data.transform(Matrix.Translation((0, 0, 0.2)) @ Matrix.Rotation(math.radians(-16), 4, "X")
                     @ Matrix.Translation((0, 0, -0.2)))
    parts = [g]
    # a twinkle: a four-pointed sparkle at the upper left
    for ax in ((1, 0, 0), (0, 0, 1)):
        a = Vector(ax) * 0.07
        c = Vector((-0.13, -0.16, 0.4))
        parts.append(rod(c - a, c, 0.0005, sh, r2=0.012, verts=4))
        parts.append(rod(c, c + a, 0.012, sh, r2=0.0005, verts=4))
    simple(parts, "treat_gem")


def treat_crown():
    gold = mat("treat_gold", (1.0, 0.72, 0.18), 0.22, metal=1.0, emit=0.35, emit_color=(1.0, 0.6, 0.15))
    velvet = mat("treat_velvet", (0.75, 0.05, 0.2), 0.8)
    pearl = mat("treat_pearl", (1.0, 0.96, 0.92), 0.2, coat=1.0, emit=0.3)
    ruby = mat("treat_ruby", (1.0, 0.05, 0.2), 0.05, coat=1.0, emit=1.5, emit_color=(1.0, 0.05, 0.2))
    sapph = mat("treat_sapphire", (0.15, 0.35, 1.0), 0.05, coat=1.0, emit=1.5, emit_color=(0.1, 0.3, 1.0))
    sh = shine_m()
    R, n, spikes = 0.2, 60, 5
    bm = bmesh.new()
    bot, top = [], []
    for k in range(n):
        a = 2 * math.pi * k / n - R90       # k = 0 at the front (-Y), between two spikes
        t = (k * spikes / n) % 1.0
        h = 0.17 + 0.16 * (1 - abs(2 * t - 1)) ** 1.4
        c, s = math.cos(a), math.sin(a)
        rr = R * (1 + 0.1 * (h - 0.17))
        bot.append(bm.verts.new((c * R * 0.92, s * R * 0.92, 0.02)))
        top.append(bm.verts.new((c * rr, s * rr, h)))
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((bot[k], bot[j], top[j], top[k]))
    c = new_obj("crown", bm, gold, smooth=35)
    solid(c, 0.02)
    parts = [c, torus(R * 0.92, 0.022, (0, 0, 0.025), gold, verts=40, minor=6),
             torus(R * 0.975, 0.016, (0, 0, 0.165), gold, verts=40, minor=6),
             ell((0, 0, 0.12), (0.17, 0.17, 0.13), velvet, segs=20, rings=10)]
    for k in range(spikes):
        a = 2 * math.pi * (k + 0.5) / spikes - math.pi / 2
        rr = R * (1 + 0.1 * 0.16)
        parts.append(sphere(0.026, (math.cos(a) * rr, math.sin(a) * rr, 0.35), pearl, segs=12, rings=8))
    for k, (a, m, r) in enumerate(((-90, ruby, 0.035), (-90 - 42, sapph, 0.025), (-90 + 42, sapph, 0.025),
                                   (-90 - 84, ruby, 0.02), (-90 + 84, ruby, 0.02))):
        ar = math.radians(a)
        p = Vector((math.cos(ar) * R * 0.99, math.sin(ar) * R * 0.99, 0.095))
        o = ico(r, p, m, sub=1, smooth=0, scale=(1, 0.6, 1.2))
        o.data.transform(Matrix.Translation(p) @ Matrix.Rotation(ar + R90, 4, "Z") @ Matrix.Translation(-p))
        parts.append(o)
    parts.append(glint((-0.1, -0.19, 0.12), 0.018, sh, face=(-0.5, -1, 0), stretch=2.2))
    simple(parts, "treat_crown")


# ------------------------------------------------------------------ level tiles (origin at the centre)

T = 0.5


def tile_mats():
    return dict(face=mat("tile_face", (0.2, 0.52, 0.95), 0.3, coat=0.6),
                trim=mat("tile_trim", (0.1, 0.28, 0.62), 0.4, coat=0.3),
                pearl=mat("tile_pearl", (1.0, 0.97, 0.93), 0.15, coat=1.0, emit=0.25))


def block_parts(M):
    h = T / 2
    parts = [box((T, T, T), (0, 0, 0), M["face"], bevel=0.05, segs=3, smooth=40),
             box((0.36, 0.03, 0.36), (0, -h + 0.006, 0), M["face"], bevel=0.014, segs=2, smooth=40)]
    parts.append(torus(0.09, 0.013, (0, -h - 0.01, 0), M["trim"], rot=(R90, 0, 0), verts=20, minor=6))
    parts.append(sphere(0.032, (0, -h - 0.01, 0), M["pearl"], scale=(1, 0.7, 1), segs=12, rings=8))
    return parts


def tile_block():
    simple(block_parts(tile_mats()), "tile_block")


def tile_top():
    M = tile_mats()
    lip = mat("tile_top_trim", (1.0, 0.9, 0.62), 0.25, coat=0.8, emit=0.1)
    h = T / 2
    parts = block_parts(M)
    parts.append(box((T, T + 0.024, 0.06), (0, 0, h - 0.03), lip, bevel=0.022, segs=3, smooth=40))
    for x in (-0.125, 0.125):      # scallops on the camera side only
        parts.append(ell((x, -h - 0.006, h - 0.06), (0.108, 0.018, 0.05), lip, segs=14, rings=7))
    for x in (-0.19, 0.0, 0.19):   # little foam bubbles on the front of the lip
        parts.append(sphere(0.012, (x + 0.03, -h - 0.02, h - 0.035), M["pearl"], segs=6, rings=4))
    simple(parts, "tile_top")


# ------------------------------------------------------------------ backdrop (origin at the base, facing -Y)

def bg_mats():
    return dict(sand=mat("bg_sand", (0.95, 0.82, 0.55), 0.85),
                rock=mat("bg_rock", (0.35, 0.36, 0.5), 0.8))


def sand_mound(c, r, h, M, seed):
    o = lumpy(1.0, (0, 0, 0), M["sand"], seed, amount=0.06, sub=2, smooth=70)
    o.data.transform(Matrix.Translation(Vector(c)) @ Matrix.Diagonal((r, r * 0.7, h, 1)))
    return o


def bg_kelp():
    stem_m = mat("bg_kelp", (0.2, 0.5, 0.2), 0.6, coat=0.2)
    leaf_m = mat("bg_kelp_light", (0.42, 0.75, 0.25), 0.5, coat=0.3, emit=0.08)
    bl = mat("bg_kelp_bladder", (0.75, 0.68, 0.22), 0.4, coat=0.5)
    M = bg_mats()
    strands = ((-0.28, 0.0, 3.3, 0.0), (0.06, 0.08, 2.4, 1.6), (0.32, -0.05, 2.85, 3.1))
    NB = 4
    B = {}
    for i, (x, y, h, ph) in enumerate(strands):
        for j in range(NB):
            B["s%d_%d" % (i, j)] = ((x, y, h * j / NB), (x, y, h * (j + 1) / NB), "s%d_%d" % (i, j - 1) if j else None)
    rig = TurnRig(B, 0, fps=FPS)
    rnd = random.Random(21)
    for i, (x, y, h, ph) in enumerate(strands):
        bones = ["s%d_%d" % (i, j) for j in range(NB)]
        pts = [(x + 0.05 * math.sin(3 * t + ph), y, h * t) for t in (k / 10 for k in range(11))]
        rig.smooth(bones, limb(pts, [0.045 - 0.02 * k / 10 for k in range(11)], stem_m, verts=8, per=2), power=5)
        n = int(h / 0.24)
        for k in range(1, n):
            t = k / n
            z = h * t
            sx = 1 if k % 2 else -1
            p = Vector((x + 0.05 * math.sin(3 * t + ph), y, z))
            L = 0.4 * (1 - 0.35 * t) + rnd.uniform(-0.03, 0.03)
            lf = ell((0, 0, 0), (L / 2, 0.012, 0.075 * (1 - 0.3 * t)), leaf_m, segs=14, rings=6)
            lf.data.transform(Matrix.Translation(p + Vector((sx * (L / 2 + 0.03), 0, 0.05)))
                              @ Matrix.Rotation(math.radians(sx * 35), 4, "Y"))
            j = min(NB - 1, int(t * NB))
            rig.rigid(bones[j], lf, sphere(0.028, p + Vector((sx * 0.035, 0, 0.012)), bl, segs=8, rings=6))
        rig.rigid(bones[-1], ell((x + 0.05 * math.sin(3 + ph), y, h + 0.1), (0.05, 0.012, 0.14), leaf_m, segs=12,
                                 rings=6))
    rig.rigid("s0_0", lumpy(0.2, (-0.25, 0.02, 0.02), M["rock"], 3, amount=0.2, scale=(1.4, 0.9, 0.6), sub=2),
              lumpy(0.14, (0.2, 0.04, 0.0), M["rock"], 4, amount=0.2, scale=(1.3, 0.9, 0.6), sub=2),
              sand_mound((0, 0.02, 0), 0.6, 0.08, M, 5))
    rig.build("bg_kelp")

    def sway(t):
        pose = {}
        for i, (x, y, h, ph) in enumerate(strands):
            for j in range(NB):
                a = 2 * math.pi * t - j * 0.7 + ph
                pose["s%d_%d" % (i, j)] = (3 * math.sin(a + 1.0), (4 + 1.5 * j) * math.sin(a), 0)
        return pose
    rig.action("sway", {f: sway(f / 90) for f in range(0, 91, 15)}, loop=True)
    rig.save("bg_kelp")


def branch(parts, p, d, L, r, depth, rnd, M_b, M_t):
    d = d.normalized()
    q = p + d * L
    mid = p.lerp(q, 0.5) + Vector((rnd.uniform(-0.04, 0.04), 0, rnd.uniform(-0.02, 0.02)))
    parts.append(tube([p, mid, q], [r, r * 0.9, r * 0.8], M_b, verts=8, caps=False))
    if depth == 0:
        parts.append(sphere(r * 1.2, q, M_t, segs=10, rings=6))
        return
    parts.append(sphere(r * 0.82, q, M_b, segs=8, rings=5))
    for k in range(2):
        ang = math.radians((-1 if k == 0 else 1) * rnd.uniform(22, 38))
        nd = Matrix.Rotation(ang, 3, "Y") @ d
        nd = (nd + Vector((0, rnd.uniform(-0.25, 0.25), 0))).normalized()
        branch(parts, q, nd, L * rnd.uniform(0.62, 0.78), r * 0.78, depth - 1, rnd, M_b, M_t)


def bg_coral():
    M = bg_mats()
    cb = mat("bg_coral", (1.0, 0.42, 0.42), 0.5, coat=0.3, emit=0.05)
    ct = mat("bg_coral_tip", (1.0, 0.78, 0.6), 0.4, emit=0.5, emit_color=(1.0, 0.6, 0.45))
    brain = mat("bg_coral_brain", (0.62, 0.38, 0.85), 0.6, coat=0.2)
    groove = mat("bg_coral_groove", (0.42, 0.22, 0.62), 0.7)
    sstar = mat("bg_seastar", (1.0, 0.55, 0.15), 0.5, coat=0.3)
    dot = mat("bg_seastar_dot", (1.0, 0.9, 0.6), 0.5)
    rnd = random.Random(12)
    parts = [lumpy(0.35, (0.0, 0.05, 0.05), M["rock"], 1, amount=0.2, scale=(1.8, 1.0, 0.7), sub=2, smooth=0),
             sand_mound((0, 0.05, 0), 0.8, 0.08, M, 2)]
    for x, d, L in ((-0.25, (-0.25, 0, 1), 0.45), (-0.05, (0.08, 0, 1), 0.55), (0.18, (0.35, 0, 1), 0.42)):
        branch(parts, Vector((x, 0.05, 0.18)), Vector(d), L, 0.05, 3, rnd, cb, ct)
    # the brain coral on the right, with meandering grooves
    bc = Vector((0.52, -0.02, 0.12))
    parts.append(ell(bc, (0.26, 0.22, 0.2), brain, segs=24, rings=12))
    for k in range(5):
        pts = []
        for i in range(12):
            a = math.radians(-160 + 140 * i / 11)
            b = math.radians(10 + 14 * k + 8 * math.sin(i * 1.3 + k))
            d = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
            pts.append(ell_point(bc, (0.26, 0.22, 0.2), d) + d * 0.003)
        parts.append(tube(pts, [0.012] * 12, groove, verts=5))
    # a sea star on the rock
    st = star((-0.45, -0.25, 0.18), 0.13, sstar, thick=0.05, face=(0.0, -0.6, 0.8))
    parts.append(st)
    for k in range(5):
        a = math.pi / 2 + 2 * math.pi * k / 5
        parts.append(sphere(0.012, (-0.45 + 0.06 * math.cos(a), -0.27 - 0.03, 0.18 + 0.06 * math.sin(a) * 0.6 + 0.02),
                            dot, segs=6, rings=4))
    simple(parts, "bg_coral")


def fan_valve(R, ribs, spread, M_out, M_in, bulge=0.12, nr=10, na=40):
    """A scallop valve: hinge at the origin, opening upward (+Z) in the X-Z plane, bulging towards +Y, ribbed;
    the inside (faces towards -Y) takes M_in."""
    bm = bmesh.new()
    grid = []
    for i in range(nr + 1):
        r = R * (0.08 + 0.92 * i / nr)
        row = []
        for j in range(na + 1):
            a = math.radians(-spread + 2 * spread * j / na)
            rib = 0.018 * abs(math.cos(ribs * a * math.pi / math.radians(2 * spread) * 2)) * (r / R)
            edge = 1.0 + 0.035 * abs(math.sin(ribs * a * math.pi / math.radians(2 * spread) * 2)) * (i == nr)
            y = bulge * math.sin(math.pi * 0.5 * r / R) * math.cos(a * 0.8) + rib
            row.append(bm.verts.new((r * edge * math.sin(a), y, r * edge * math.cos(a))))
        grid.append(row)
    for i in range(nr):
        for j in range(na):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    o = new_obj("valve", bm, M_out, smooth=50)
    solid(o, 0.025)
    o.data.materials.append(M_in)
    for p in o.data.polygons:
        p.material_index = 1 if p.normal.y < -0.2 else 0
    return o


def bg_shell():
    M = bg_mats()
    out = mat("bg_shell", (1.0, 0.72, 0.62), 0.45, coat=0.4)
    inner = mat("bg_shell_inner", (1.0, 0.7, 0.78), 0.25, coat=0.8, emit=0.08)
    pearl = mat("bg_pearl", (1.0, 0.96, 0.95), 0.12, coat=1.0, emit=0.9, emit_color=(0.9, 0.85, 1.0))
    back = fan_valve(0.62, 9, 62, out, inner)
    back.data.transform(Matrix.Translation((0, 0.12, 0.08)) @ Matrix.Rotation(math.radians(-12), 4, "X"))
    front = fan_valve(0.56, 9, 60, out, inner, bulge=0.1)
    front.data.transform(Matrix.Diagonal((1, -1, 1, 1)))          # bulging towards the camera...
    front.data.flip_normals()
    front.data.transform(Matrix.Rotation(math.radians(76), 4, "X"))   # ...then laid forward: it bulges down
    front.data.transform(Matrix.Translation((0, 0.1, 0.12)))
    front.data.update()
    for p in front.data.polygons:
        p.material_index = 1 if p.normal.z > 0.2 else 0
    parts = [back, front,
             box((0.24, 0.12, 0.1), (0, 0.12, 0.08), out, bevel=0.03),
             sphere(0.13, (0, -0.2, 0.19), pearl, segs=24, rings=14),
             sand_mound((0, 0.0, 0), 0.75, 0.06, M, 7)]
    simple(parts, "bg_shell")


def bg_toy_block():
    M = bg_mats()
    paint = mat("bg_block_paint", (0.3, 0.72, 0.85), 0.35, coat=0.6)
    frame = mat("bg_block_frame", (1.0, 0.94, 0.78), 0.4, coat=0.5)
    sm = mat("bg_block_star", (1.0, 0.78, 0.15), 0.3, coat=0.6, emit=0.1)
    hm = mat("bg_block_heart", (1.0, 0.35, 0.45), 0.3, coat=0.6, emit=0.1)
    cm = mat("bg_block_circle", (0.45, 0.82, 0.3), 0.3, coat=0.6)
    S = 1.1
    h = S / 2
    parts = [box((S, S, S), (0, 0, h), paint, bevel=0.08, segs=3, smooth=40)]

    face = []
    w = 0.07
    for x, z, sx, sz in ((0, h - (h - 0.1), S - 0.2, w), (0, h + (h - 0.1), S - 0.2, w),
                         (-(h - 0.1), h, w, S - 0.2), ((h - 0.1), h, w, S - 0.2)):
        face.append(box((sx, 0.04, sz), (x, -h, z), frame, bevel=0.015))
    face.append(star((0, -h - 0.02, h), 0.3, sm, thick=0.06))
    parts += face
    # the right face (+X): the same frame, a heart
    side = [box((sx, 0.04, sz), (x, -h, z), frame, bevel=0.015) for x, z, sx, sz in
            ((0, 0.1, S - 0.2, w), (0, S - 0.1, S - 0.2, w), (-(h - 0.1), h, w, S - 0.2), ((h - 0.1), h, w, S - 0.2))]
    heart = []
    for k in range(40):
        t = 2 * math.pi * k / 40
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        heart.append((x * 0.017, z * 0.017))
    heart = heart[::-1]
    side.append(prism(heart, 0.05, (0, 0, 0), hm, bevel=0.015, segs=2))
    side[-1].data.transform(Matrix.Translation((0, -h - 0.01, h + 0.02)))
    for o in side:
        o.data.transform(Matrix.Translation((0, 0, 0)) @ Matrix.Rotation(R90, 4, "Z"))
    parts += side
    # the top: a frame and a circle
    top = [box((sx, sz, 0.04), (x, z, S), frame, bevel=0.015) for x, z, sx, sz in
           ((0, -(h - 0.1), S - 0.2, w), (0, (h - 0.1), S - 0.2, w), (-(h - 0.1), 0, w, S - 0.2), ((h - 0.1), 0, w, S - 0.2))]
    top.append(cyl(0.26, 0.05, (0, 0, S + 0.01), cm, verts=32, bevel=0.015, segs=2))
    parts += top
    for o in parts:
        o.data.transform(Matrix.Rotation(math.radians(-28), 4, "Z"))
        o.data.transform(Matrix.Translation((0, 0, -0.12)))
    parts.append(sand_mound((0, 0, 0), 0.95, 0.14, M, 3))
    simple(parts, "bg_toy_block")


def bg_bubble_column():
    M = bg_mats()
    bub = mat("bg_bubble", (0.8, 0.95, 1.0), 0.05, coat=1.0, alpha=0.4, emit=0.5, emit_color=(0.6, 0.9, 1.0))
    root = empty("bg_bubble_column")
    vent = join([lumpy(0.22, (-0.12, 0.0, 0.05), M["rock"], 1, amount=0.22, scale=(1.3, 1.0, 0.8), sub=2),
                 lumpy(0.18, (0.16, 0.03, 0.04), M["rock"], 2, amount=0.22, scale=(1.2, 1.0, 0.9), sub=2),
                 lumpy(0.1, (0.02, -0.12, 0.12), M["rock"], 3, amount=0.2, sub=2),
                 sand_mound((0, 0, 0), 0.5, 0.06, M, 4)], "vent")
    children = [(vent, root)]
    rnd = random.Random(33)
    N, Hh, F = 14, 3.8, 60
    for k in range(N):
        r = rnd.uniform(0.03, 0.075)
        o = sphere(r, (0, 0, 0), bub, segs=12, rings=8)
        o = join([o, sphere(r * 0.28, (-r * 0.4, -r * 0.8, r * 0.4), mat("bg_bubble_shine", (1, 1, 1), 0.1, emit=3.0),
                            segs=6, rings=4)], "b%02d" % k)
        ph = k / N + rnd.uniform(-0.02, 0.02)
        wob = rnd.uniform(0.04, 0.09)
        w0 = rnd.uniform(0, 6.28)
        y = rnd.uniform(-0.05, 0.05)
        wrap_f = int((1 - ph) % 1.0 * F)

        def at(u):
            x = wob * math.sin(2 * math.pi * 2.2 * u + w0) + 0.02
            sc = max(0.0, min(1.0, u / 0.06, (1 - u) / 0.05)) * (0.75 + 0.5 * u)
            return (x, y, 0.2 + Hh * u), sc
        keys = {}
        frames = set(range(0, F + 1, 3)) | {wrap_f, wrap_f + 1}
        for f in sorted(frames):
            if f > F:
                continue
            u = (f / F + ph) % 1.0
            loc, sc = at(u)
            if f == wrap_f:
                loc, sc = at(0.9999)
                sc = 0.0
            if f == wrap_f + 1:
                sc = 0.0
            keys[f] = {"loc": loc, "scale": (sc, sc, sc)}
        o.location = (0, 0, 0)
        animate(o, "rise", keys)
        children.append((o, root))
    export_anim(root, "bg_bubble_column", children)


# ------------------------------------------------------------------ main

JOBS = {"axolotl": axolotl, "bubble": bubble, "bubble_trap": bubble_trap,
        "special_bubble_water": special_bubble_water, "special_bubble_fire": special_bubble_fire,
        "special_bubble_bolt": special_bubble_bolt, "letter_bubble": letter_bubble,
        "toy_beetle": toy_beetle, "toy_spring": toy_spring, "toy_flyer": toy_flyer,
        "treat_cherry": treat_cherry, "treat_melon": treat_melon, "treat_cupcake": treat_cupcake,
        "treat_icecream": treat_icecream, "treat_gem": treat_gem, "treat_crown": treat_crown,
        "tile_block": tile_block, "tile_top": tile_top,
        "bg_kelp": bg_kelp, "bg_coral": bg_coral, "bg_shell": bg_shell, "bg_toy_block": bg_toy_block,
        "bg_bubble_column": bg_bubble_column}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
