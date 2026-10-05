"""Bloomwand (game 33) models: the fairy (the heroine), four creatures (grub, bopper, snapper, cloudlet), the pickups
(a flower that pops open, cherries, a pear, grapes, a cake, a crystal, a bonus bomb, a letter bubble) and the level
pieces (three 1 m blocks, a wooden ladder, a rainbow ladder, the exit gate).
Original designs for a storybook garden, nothing taken from any arcade game: the fairy is our own character (a
round-faced girl with a honey bob and a high twisted ponytail tied with daisies, elf ears, a petal dress with puff
sleeves and a leaf collar, white stockings, curly leaf shoes, two pairs of glassy wings and a star wand with a blue
bow); the creatures are cute-grumpy garden pests (a fat green caterpillar standing on its tail, a red-capped mushroom
imp with pointed ears, a purple little crocodile on two legs with a huge underbite, a scowling storm cloud dangling
a lightning bolt). Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/bloomwand_models.py -- godot/games/bloomwand/art/models [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (Rig, merge,
mirror, limb), hopline_models.py (TurnRig, ell, hemi), mossfolk_models.py (lathe_r, lumpy, solid), prism_models.py
(animate, export_anim, empty) and nightbite_characters.py (blob). 30 fps.

Axes: Godot units = metres, y up, the camera at +Z looking at the play plane z = 0. Characters are built facing -Y
in Blender and exported facing Godot +X (their right side, the wand side, towards the camera); turn them 180 degrees
about Y (or mirror x) to face -X. They read in pure profile, but a turn of about 20-30 degrees towards the camera shows
more of the faces. Props face the camera (+Z). Animations marked * are seamless loops: set their loop mode in the
game. Emissive materials all have "glow" in their names; materials with alpha are alpha-blended.

fairy.glb    armature "fairy_rig" (root, hips, chest, head, tail, tail2 (the ponytail), eye.L/R, wing.L/R, arm.L/R,
             wand, thigh.L/R, shin.L/R), skinned mesh "body": 0.87 tall (the ponytail's arch; head top 0.80), origin
             at the feet, facing +X. Bone-attached node "wand" (bone "wand", in the right hand, camera side) with the
             child empty "wand_tip" at the star: rest (idle) about (0.40, 0.34, 0.14) from the origin; in hold about
             (0.03, 0.86, -0.07), straight above her head; cast f3+ about (0.47, 0.36, 0.25).
             Materials: fairy_dress (petals, bodice, sleeves: pink; recolour it per player, teal for player 2),
             fairy_trim (cuffs, stockings, pompoms), fairy_leaf (collar, sash), fairy_skin, fairy_hair,
             fairy_hair_light (strands), fairy_eye, fairy_iris, fairy_eye_shine, fairy_lash, fairy_mouth, fairy_cheek,
             fairy_shoe, fairy_flower, fairy_flower_heart (the daisies in her hair), fairy_wing_glow (alpha 0.42),
             fairy_wing_vein_glow, fairy_wand, fairy_star_glow, fairy_ribbon.
             Animations: idle*  2.0 s   breathing, the wings flutter, the ponytail sways, one blink at 1.33 s
                         walk*  0.5 s   a light skipping step, feet ~0.25 apart (about 1 m/s at speed 1)
                         climb* 0.6 s   on a ladder in front of her, seen side-on: hands reach up in turn
                         fall*  0.5 s   arms up and out, legs kicking, wings beating, eyes wide
                         cast   0.27 s  the wand thrust straight ahead from f3 (0.1 s), held to f5, easing back
                         hold*  1.0 s   both hands up, the wand pointing straight up (hang the creature on wand_tip)
                         slam   0.4 s   from hold: down in front (impact f3, 0.1 s, tip ~(0.28, 0.0)), over the head
                                        (f6) and down behind (impact f9, 0.3 s, tip ~(-0.30, 0.02)), back to hold (f12)
                         die    1.4 s   a jolt, a dizzy spin slowing (2.25 turns), sits down facing the camera, eyes
                                        shut (holds the last frame)
                         cheer* 1.0 s   two hops, the wand waved high, happy eyes
grub.glb     armature "grub_rig" (root, belly, tail, chest, head, ant.L/R, arm.L/R), mesh "body": 0.93 tall to the
             antenna tips (head top 0.78), 0.61 long, origin at the feet, facing +X. Materials grub_skin (green),
             grub_belly, grub_band, grub_spot (orange flank spots, antenna tips), grub_foot, grub_brow, grub_eye,
             grub_pupil, grub_shine, grub_mouth, grub_tooth.
             walk* 0.8 s (a ripple tail to head), climb* 0.8 s (reared up, the tail hanging, arms reaching),
             caught* 0.6 s (wriggling, curling and twisting).
bopper.glb   armature "bopper_rig" (root, body, cap, arm.L/R, leg.L/R), mesh "body": 0.88 tall, the cap 0.63 across,
             origin at the feet, facing +X. bopper_skin (the red cap), bopper_spot, bopper_gill, bopper_belly (the
             stem body, ears, arms), bopper_boot, bopper_brow, bopper_nose, eye/pupil/shine/mouth/tooth.
             walk* 0.6 s (one hop: crouch f0, spring f4, top f9 0.13 up, landing squash f15; move it on the hop),
             climb* 0.6 s, caught* 0.5 s (kicking, the cap wobbling).
snapper.glb  armature "snapper_rig" (root, hips, chest, head, jaw, tail, tail2, arm.L/R, leg.L/R), mesh "body": 0.78
             tall, 0.9 long (snout tip x +0.37, tail tip x -0.53), origin at the feet, facing +X. snapper_skin (purple),
             snapper_belly, snapper_scute, snapper_claw, snapper_brow, snapper_tongue, eye/pupil/shine/mouth/tooth.
             walk* 0.7 s (a stompy waddle, tail swishing), climb* 0.7 s, caught* 0.5 s (thrashing, jaw snapping),
             bite 0.5 s (rears back jaw wide f5, lunges and snaps shut f8 = 0.27 s, 0.06 forward, recovers).
cloudlet.glb armature "cloudlet_rig" (root, body, puff.T, puff.F, puff.B, arm.L/R, bolt), mesh "body": a storm cloud
             from y 0.22 to 0.85 (0.67 long), the bolt dangling to y 0.05, origin under it (on the tile floor), facing
             +X. cloudlet_skin, cloudlet_belly (the sunlit top), cloudlet_bolt_glow, cloudlet_drop (alpha), cloudlet_cheek,
             cloudlet_brow, eye/pupil/shine/mouth/tooth.
             float* 2.0 s (bobbing 0.035, puffs breathing, the bolt swaying), caught* 0.5 s (shaking with fury).
             The creatures' rest pose stands neutral; there is no idle: play walk (or float) at any speed.

Pickups (origin at the bottom centre, resting on the floor, unless noted; facing the camera):
flower.glb   node "flower" (stem, two leaves, a grass tuft; 0.47 tall) with the child "bloom" (the flower head, origin
             at its centre, (0, 0.44, 0.01)), whose children "petal_0" .. "petal_7" are the petals. flower_petal (pink:
             recolour it per variant), flower_heart, flower_heart_dots, flower_stem, flower_leaf. Animation "open"
             0.5 s (one-shot): a bud (bloom scaled 0.4, petals folded forward) pops open with an overshoot. At rest
             (no animation) the flower is open.
fruit_cherry.glb (0.44 tall), fruit_pear.glb (0.46), fruit_grapes.glb (0.47), cake.glb (0.42 across, 0.34 tall: a
             strawberry cake with pink icing), crystal.glb (0.40 tall, crystal_glow alpha, crystal_core_glow):
             one node each, named like the file. fruit_shine is a small emissive highlight; fruit_leaf, fruit_stem.
bomb_bonus.glb node "bomb_bonus" (a round navy bomb with a gold star and cap, 0.32 across, 0.46 to the fuse tip)
             with the child "spark" (origin at the fuse tip, bomb_spark_glow). Animation "fizz"* 0.4 s.
letter_bubble.glb node "letter_bubble": a glossy bubble 0.6 across, origin at its CENTRE; bubble_glass (alpha 0.32),
             bubble_rim_glow, bubble_shine_glow (highlights on the camera side, top left and bottom right). Write the
             letter at the origin, facing the camera.

Level pieces (1 x 1 x 1 m tiles, origin at the BOTTOM centre: x -0.5..0.5, y 0..1, z -0.5..0.5; place a tile's
origin at (cell x + 0.5, cell y)):
block.glb    carved stone in two staggered courses (block_stone, block_stone_dark), a moss cushion on top lipping over the
             front edge with tiny flowers (block_moss, block_flower, block_flower_heart): the moss rises to y 1.07 and
             shows as a mossy joint when another block sits on it.
block_b.glb  a wooden crate (crate_wood, crate_frame, crate_nail); the front and back frames reach z +-0.54.
block_c.glb  ice: a clear block (ice_glass, alpha) with shards frozen inside (ice_core_glow), a frosty top (ice_frost) and
             icicles along the front edge.
ladder.glb   one 1 m segment: rails at x +-0.32, four rungs at y 0.125, 0.375, 0.625, 0.875 (0.25 apart, so segments
             stack seamlessly), rope lashings; z -0.05..0.05. ladder_wood, ladder_rope.
magic_ladder.glb the same layout in light: each rail a ribbon of five rainbow bands (magic_band0_glow .. magic_band4_glow:
             red, gold, green, blue, violet), rungs of white light in a coloured sheath (magic_rung_glow), star sparks
             (magic_spark_glow); all alpha-blended.
door.glb     the exit gate: node "door" (a stone arch on two pillars, 1.54 wide, 1.95 tall, a gold star keystone, a
             flowering vine, a threshold, and door_portal_glow: the warm light filling the opening at z -0.1, behind
             the leaves) with the children "door_l" and "door_r": the two leaves (wood, gold straps, ring handles, a
             flower emblem), origins on their hinges at x -0.5 / +0.5 (y 0, z 0). Opening 1.0 wide, 1.7 tall (round
             top). Animation "open" 0.8 s (one-shot): a rattle, then both leaves swing out towards the camera to 100
             degrees (door_l rotation.y = -100 deg, door_r +100 deg in Godot) with a little bounce. Materials door_stone,
             door_stone_dark, door_wood, door_wood_dark, door_metal, door_vine, door_flower, door_flower_heart.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, export, reset, cyl, box, prism
from blastyard_bombers import merge, mirror, smoothstep, limb
from hopline_models import TurnRig, ell, hemi
from mossfolk_models import lathe_r, lumpy, solid
from prism_models import animate, export_anim, empty, new_obj
from nightbite_characters import blob

FPS = 30


# ------------------------------------------------------------------ helpers

class SideRig(TurnRig):
    """TurnRig turned 90 degrees: written facing -Y, exported facing +X. Adds bone-attached nodes."""

    def __init__(self, bones, hidden=()):
        super().__init__(bones, 90, fps=FPS, hidden=hidden)
        self.attached = []

    def attach(self, bone, parts, name, pivot):
        """Joins parts (built facing -Y) into one node `name` parented to `bone`, origin at pivot (-Y coords)."""
        parts = K.flatten(parts)
        for o in parts:
            self.turn(o)
        o = join(parts, name, pivot=self.Q3 @ Vector(pivot))
        self.parent_to_bone(o, bone)
        self.attached.append(o)
        return o

    def parent_to_bone(self, o, bone):
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy()
        o.parent = self.arm
        o.parent_type = "BONE"
        o.parent_bone = bone
        bpy.context.view_layer.update()
        o.matrix_world = mw

    def child_empty(self, parent, name, loc):
        """An empty `name` at loc (-Y coords) parented to the node `parent`."""
        e = empty(name)
        e.location = self.Q3 @ Vector(loc)
        bpy.context.view_layer.update()
        mw = e.matrix_world.copy()
        e.parent = parent
        bpy.context.view_layer.update()
        e.matrix_world = mw
        self.attached.append(e)
        return e

    def build(self, name):
        """Builds the skinned mesh "body" under the armature "<name>_rig"."""
        mesh = super().build(name)
        mesh.name = mesh.data.name = "body"
        return mesh

    def save(self, name, extra=()):
        super().save(name, list(self.attached) + list(extra))


def on_surface(o, p, n, spin=0.0):
    """Moves an object built at the origin facing -Y onto point p, facing along the normal n."""
    q = Vector((0, -1, 0)).rotation_difference(Vector(n).normalized())
    o.data.transform(Matrix.Translation(Vector(p)) @ q.to_matrix().to_4x4() @ Matrix.Rotation(spin, 4, "Y"))
    return o


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


def outline_plate(pts, thick, material, name="plate", smooth=0):
    """A flat plate from a closed outline of 3D points (a fan from their centroid), `thick` along its normal."""
    bm = bmesh.new()
    c = sum((Vector(p) for p in pts), Vector()) / len(pts)
    cv = bm.verts.new(c)
    vs = [bm.verts.new(p) for p in pts]
    for i in range(len(vs)):
        bm.faces.new((cv, vs[i], vs[(i + 1) % len(vs)]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if thick:
        solid(o, thick)
    return K.finish(o, material, smooth=smooth)


def star_mesh(r_out, r_in, depth, material, name="star", points=5):
    """A puffy faceted star in the XZ plane (point up), raised by `depth` on both faces (-Y front, +Y back)."""
    bm = bmesh.new()
    rim = []
    for k in range(points * 2):
        a = math.pi / 2 + math.pi * k / points
        r = r_out if k % 2 == 0 else r_in
        rim.append(bm.verts.new((r * math.cos(a), 0, r * math.sin(a))))
    f = bm.verts.new((0, -depth, 0))
    b = bm.verts.new((0, depth, 0))
    n = len(rim)
    for k in range(n):
        bm.faces.new((rim[k], rim[(k + 1) % n], f))
        bm.faces.new((rim[(k + 1) % n], rim[k], b))
    return new_obj(name, bm, material, smooth=0)


DAISY = [0]


def daisy(c, d, r, petal_m, heart_m, n=8, cup=0.25, name="daisy"):
    """A small flower facing d: n rounded petals around a domed heart."""
    parts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        p = ell((r * 0.55 * math.cos(a), 0, r * 0.55 * math.sin(a)), (r * 0.5, r * 0.12, r * 0.22), petal_m,
                segs=8, rings=5)
        p.data.transform(Matrix.Translation((r * 0.55 * math.cos(a), 0, r * 0.55 * math.sin(a)))
                         @ Matrix.Rotation(-a, 4, "Y") @ Matrix.Rotation(cup, 4, "Z")
                         @ Matrix.Translation((-r * 0.55 * math.cos(a), 0, -r * 0.55 * math.sin(a))))
        parts.append(p)
    parts.append(ell((0, -r * 0.08, 0), (r * 0.32, r * 0.2, r * 0.32), heart_m, segs=10, rings=6))
    DAISY[0] += 1
    o = join(parts, "%s_%d" % (name, DAISY[0]))
    q = Vector((0, -1, 0)).rotation_difference(Vector(d).normalized())
    o.data.transform(Matrix.Translation(Vector(c)) @ q.to_matrix().to_4x4())
    return o


def lsc(name, deg):
    return mirror({name: deg})


# ------------------------------------------------------------------ the fairy

HC = Vector((0, -0.005, 0.625))      # head centre
HR = Vector((0.158, 0.148, 0.146))   # head radii
EYE_YAW = 40.0
WAND0 = -120.0                        # the wand's rest direction (degrees about X from straight down: forward-up)


def flat(o, k=0.45, shell=1.07):
    """Presses a hair lock against the head: squashes its depth towards a shell `shell` x the head's radius."""
    for v in o.data.vertices:
        d = v.co - HC
        r0 = (head_pt(d) - HC).length * shell
        v.co = HC + d.normalized() * (r0 + (d.length - r0) * k)
    o.data.update()
    return o


def head_pt(d, k=1.0):
    d = Vector(d).normalized()
    s = 1.0 / math.sqrt((d.x / HR.x) ** 2 + (d.y / HR.y) ** 2 + (d.z / HR.z) ** 2)
    return HC + d * s * k


def head_dir(yaw, el):
    """Direction from the head centre: yaw degrees from the front (-Y) towards +X, el degrees up."""
    y, e = math.radians(yaw), math.radians(el)
    return Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))


def hair_cap(material, cols=120, rows=16):
    """The fairy's bob: one shell over the crown, its hem scalloped into pointed locks, a fringe at the brow,
    falling to the cheeks at the sides and to the nape at the back, flicked out at the back."""
    base = [(0, 19), (40, 17), (62, 4), (85, -20), (110, -32), (145, -42), (180, -44)]
    front_locks = [-40, -22, -5, 12, 30, 47]
    side_locks = [62, 82, 104, 128, 154, 180]
    centres = front_locks + side_locks + [-c for c in side_locks]

    def lock(th):
        best = (1.0, 0)
        for c in centres:
            d = abs((th - c + 180) % 360 - 180)
            w = 9.0 if abs(c) < 55 else 12.0
            best = min(best, (d / w, c))
        return best

    def hem(th):
        a = abs(th)
        h = float(numpy_interp(a, base))
        t, c = lock(th)
        dip = (15.0 if abs(c) < 55 else 13.0) * (c == -5 and 1.2 or 1.0)
        return h - dip * max(0.0, 1 - t) ** 1.7, t

    bm = bmesh.new()
    grid = []
    for i in range(rows + 1):
        v = i / rows
        row = []
        for j in range(cols):
            th = -180 + 360 * j / cols
            h, t = hem(th)
            el = 88 - v * (88 - h)
            d = head_dir(th, el)
            flick = -0.03 if abs(th) < 60 else (0.05 * smoothstep(80, 150, abs(th)))
            k = 1.075 + 0.03 * max(0.0, 1 - t * t) ** 2 * v + flick * smoothstep(0.7, 1.0, v)
            p = head_pt(d, k)
            if abs(th) < 60:    # the fringe hugs the brow
                p += Vector((0, 0, -0.004)) * v
            row.append(bm.verts.new(p))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            a, b = grid[i][j], grid[i][(j + 1) % cols]
            c, d = grid[i + 1][(j + 1) % cols], grid[i + 1][j]
            bm.faces.new((a, d, c, b))
    top = bm.verts.new(head_pt(Vector((0, 0, 1)), 1.075))
    for j in range(cols):
        bm.faces.new((top, grid[0][j], grid[0][(j + 1) % cols])[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = new_obj("hair_cap", bm, material, smooth=0)
    o.data.update()
    n = sum((p.normal for p in o.data.polygons if p.center.z > HC.z + 0.1), Vector())
    if n.z < 0:
        o.data.flip_normals()
    solid(o, 0.012)
    return K.finish(o, material, smooth=80)


def numpy_interp(x, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def fairy():
    reset()
    dress = mat("fairy_dress", (0.96, 0.4, 0.62), 0.5, coat=0.35)
    trim = mat("fairy_trim", (1.0, 0.95, 0.88), 0.55, coat=0.2)
    leaf = mat("fairy_leaf", (0.36, 0.7, 0.28), 0.55, coat=0.3)
    skin = mat("fairy_skin", (1.0, 0.72, 0.58), 0.55, coat=0.15)
    hair = mat("fairy_hair", (0.98, 0.52, 0.17), 0.45, coat=0.45)
    hair_hi = mat("fairy_hair_light", (1.0, 0.68, 0.24), 0.4, coat=0.45)
    eye = mat("fairy_eye", (0.12, 0.06, 0.16), 0.2, coat=1.0)
    iris = mat("fairy_iris", (0.42, 0.22, 0.7), 0.25, coat=1.0)
    shine = mat("fairy_eye_shine", (1.0, 1.0, 1.0), 0.1, emit=3.0)
    lash = mat("fairy_lash", (0.18, 0.08, 0.1), 0.6)
    mouth = mat("fairy_mouth", (0.62, 0.16, 0.24), 0.5)
    cheek = mat("fairy_cheek", (1.0, 0.48, 0.5), 0.7)
    shoe = mat("fairy_shoe", (0.28, 0.58, 0.3), 0.45, coat=0.4)
    wing = mat("fairy_wing_glow", (0.72, 0.92, 1.0), 0.15, emit=0.7, alpha=0.42, emit_color=(0.55, 0.85, 1.0))
    vein = mat("fairy_wing_vein_glow", (0.85, 0.95, 1.0), 0.2, emit=1.6, alpha=0.8, emit_color=(0.7, 0.9, 1.0))
    petal_m = mat("fairy_flower", (1.0, 0.97, 0.9), 0.5)
    heart_m = mat("fairy_flower_heart", (1.0, 0.78, 0.2), 0.5)
    wood = mat("fairy_wand", (0.98, 0.93, 0.82), 0.35, coat=0.6)
    star_m = mat("fairy_star_glow", (1.0, 0.85, 0.3), 0.25, metal=0.2, emit=2.2, emit_color=(1.0, 0.78, 0.25))
    ribbon = mat("fairy_ribbon", (0.55, 0.75, 1.0), 0.5, coat=0.2)

    B = {"root": ((0, 0, 0), (0, 0, 0.06), None),
         "hips": ((0, 0, 0.26), (0, 0, 0.36), "root"),
         "chest": ((0, 0, 0.36), (0, 0, 0.47), "hips"),
         "head": ((0, 0, 0.48), (0, 0, 0.78), "chest"),
         "tail": ((0, 0.1, 0.77), (0, 0.24, 0.66), "head"),
         "tail2": ((0, 0.24, 0.66), (0, 0.27, 0.5), "tail"),
         "eye.L": (tuple(head_pt(head_dir(EYE_YAW, -10))), tuple(head_pt(head_dir(EYE_YAW, -10), 1.3)), "head"),
         "eye.R": (tuple(head_pt(head_dir(-EYE_YAW, -10))), tuple(head_pt(head_dir(-EYE_YAW, -10), 1.3)), "head"),
         "wing.L": ((0.025, 0.07, 0.44), (0.12, 0.2, 0.6), "chest"),
         "wing.R": ((-0.025, 0.07, 0.44), (-0.12, 0.2, 0.6), "chest"),
         "arm.L": ((0.085, 0.0, 0.44), (0.115, -0.01, 0.29), "chest"),
         "arm.R": ((-0.085, 0.0, 0.44), (-0.115, -0.01, 0.29), "chest"),
         "wand": ((-0.118, -0.02, 0.29), (-0.118, -0.02 - 0.34 * 0.866, 0.29 + 0.34 * 0.5), "arm.R"),
         "thigh.L": ((0.045, 0.0, 0.27), (0.05, 0.0, 0.155), "root"),
         "thigh.R": ((-0.045, 0.0, 0.27), (-0.05, 0.0, 0.155), "root"),
         "shin.L": ((0.05, 0.0, 0.155), (0.052, 0.0, 0.045), "thigh.L"),
         "shin.R": ((-0.05, 0.0, 0.155), (-0.052, 0.0, 0.045), "thigh.R")}
    rig = SideRig(B)

    def w_body(p):
        t1 = smoothstep(0.33, 0.39, p.z)
        t2 = smoothstep(0.455, 0.5, p.z)
        return {"hips": 1 - t1 + 1e-4, "chest": t1 * (1 - t2) + 1e-4, "head": t1 * t2 + 1e-4}

    # ---- the head: a big round face, pointed ears
    head = ell(HC, HR, skin, segs=32, rings=20)
    for v in head.data.vertices:    # a softer, rounder cheek and a slightly narrower chin
        t = (v.co.z - HC.z) / HR.z
        if t < 0:
            v.co.x = HC.x + (v.co.x - HC.x) * (1 - 0.1 * t * t)
            v.co.y = HC.y + (v.co.y - HC.y) * (1 - 0.06 * t * t)
    head.data.update()
    neck = rod((0, 0, 0.44), (0, 0, 0.52), 0.035, skin, verts=12)
    rig.custom(w_body, head, neck)
    hp = []
    for s in (-1, 1):   # elf ears sweeping back and up
        base = head_pt(head_dir(90 * s, -2), 0.96)
        ear = tube([base, base + Vector((0.035 * s, 0.03, 0.02)), base + Vector((0.06 * s, 0.07, 0.055)),
                    base + Vector((0.07 * s, 0.1, 0.09))], [0.032, 0.026, 0.014, 0.003], skin, verts=10, caps=True,
                   name="ear")
        for v in ear.data.vertices:   # flatten into a leaf shape
            rel = v.co - base
            v.co.x = base.x + rel.x * 0.45 + rel.y * 0.12 * s
        ear.data.update()
        hp.append(ear)
        # cheeks, a touch below and outside the eyes
        cd = head_dir(48 * s, -30)
        hp.append(blob(0.028, head_pt(cd, 0.99), cheek, (1.25, 0.3, 0.8), cd, segs=12, rings=6))
    # a tiny button nose and a small open smile (the silhouette carries them in profile)
    hp.append(sphere(0.014, head_pt(head_dir(0, -16), 0.99), skin, scale=(1.0, 0.9, 0.8), segs=10, rings=6))
    smile = [head_pt(head_dir(a, -33 - 4 * math.cos(math.radians(a * 4))), 1.004) for a in (-16, -8, 0, 8, 16)]
    hp.append(tube(smile, [0.004, 0.007, 0.008, 0.007, 0.004], mouth, verts=6, caps=True, name="smile"))
    rig.rigid("head", hp)
    # the eyes: tall dark ovals with a violet lower iris and two catch lights (bones scale them for blinks)
    for s, side in ((1, "L"), (-1, "R")):
        d = head_dir(EYE_YAW * s, -10)
        p = head_pt(d, 0.985)
        up = (Vector((0, 0, 1)) - d * d.z).normalized()
        side_v = d.cross(up).normalized()
        parts = [blob(0.036, p, eye, (0.82, 0.32, 1.22), d, segs=16, rings=10),
                 blob(0.026, p + d * 0.007 - up * 0.014, iris, (0.8, 0.25, 0.75), d, segs=12, rings=8),
                 sphere(0.011, p + d * 0.014 + up * 0.016 + side_v * 0.009 * s, shine, segs=8, rings=6),
                 sphere(0.005, p + d * 0.013 - up * 0.02 - side_v * 0.008 * s, shine, segs=6, rings=4)]
        # lashes: a little flick at the outer top corner
        lp = [p + up * 0.04 - side_v * 0.012 * s + d * 0.004, p + up * 0.038 + side_v * 0.016 * s + d * 0.004,
              p + up * 0.03 + side_v * 0.036 * s + d * 0.002]
        parts.append(tube(lp, [0.004, 0.005, 0.002], lash, verts=5, caps=True, name="lash"))
        rig.rigid("eye." + side, parts)

    # ---- the hair: a bob cap open at the face, a sweeping fringe, side locks, a high ponytail
    cap = hair_cap(hair)
    locks = []
    for s_ in (-1, 1):   # side locks in front of the ears, curling in at the cheek
        a = head_pt(head_dir(74 * s_, 10), 1.06)
        b = head_pt(head_dir(73 * s_, -22), 1.08)
        c = head_pt(head_dir(66 * s_, -46), 1.05)
        d = c + Vector((-0.008 * s_, -0.014, 0.012))
        locks.append(flat(tube([a, b, c, d], [0.026, 0.024, 0.015, 0.004], hair, verts=10, caps=True,
                               name="sidelock"), k=0.6, shell=1.06))
    rig.rigid("head", cap, locks)
    # the ponytail, tied high at the back of the crown with a little flower, falling in a fountain
    tie = HC + Vector((0, 0.11, 0.15))
    rig.rigid("head", sphere(0.045, tie, hair, scale=(1.0, 0.9, 0.8), segs=14, rings=8),
              torus(0.033, 0.011, tie + Vector((0, 0.014, 0.012)), leaf, rot=(math.radians(-40), 0, 0), verts=16,
                    minor=6),
              daisy(tie + Vector((-0.045, 0.0, 0.03)), (-0.7, -0.3, 0.5), 0.05, petal_m, heart_m, name="tie_flower"),
              daisy(tie + Vector((0.045, 0.0, 0.03)), (0.7, -0.3, 0.5), 0.042, petal_m, heart_m, n=7,
                    name="tie_flower2"))
    pt = [tie + Vector((0, 0.01, 0.01)), tie + Vector((0, 0.06, 0.05)), Vector((0, 0.24, 0.82)),
          Vector((0, 0.29, 0.73)), Vector((0, 0.29, 0.63)), Vector((0, 0.265, 0.56)), Vector((0, 0.225, 0.545)),
          Vector((0, 0.205, 0.575))]
    pr = [0.03, 0.036, 0.036, 0.031, 0.026, 0.02, 0.013, 0.004]

    def w_tail(p):
        t = smoothstep(0.1, 0.2, p.y)
        u = smoothstep(0.62, 0.72, p.z)
        return {"head": 1 - t + 1e-4, "tail": t * u + 1e-4, "tail2": t * (1 - u) + 1e-4}
    from blastyard_bombers import smooth_path, smooth_radii
    sp, sr = smooth_path(pt, 4), smooth_radii(pr, 4)
    strands = []
    for k in range(3):   # three soft twisted strands make the tail read as hair
        pts, rad = [], []
        for i, (q, r) in enumerate(zip(sp, sr)):
            u = i / (len(sp) - 1)
            tng = (sp[min(i + 1, len(sp) - 1)] - sp[max(i - 1, 0)]).normalized()
            n1 = tng.cross(Vector((1, 0, 0))).normalized()
            n2 = tng.cross(n1).normalized()
            a_ = 2 * math.pi * k / 3 + u * 2.4 * math.pi
            off = (n1 * math.cos(a_) + n2 * math.sin(a_)) * r * 0.45
            pts.append(q + off)
            rad.append(r * 0.62 + 0.002)
        strands.append(tube(pts, rad, hair if k else hair_hi, verts=10, caps=True, name="strand"))
    tail = join(strands, "tail")
    rig.custom(w_tail, tail)

    # ---- the body: a petal dress (bodice, two rings of petals), puff sleeves, a leaf collar
    bod = ell((0, 0.0, 0.4), (0.082, 0.07, 0.085), dress, segs=20, rings=12)
    rig.custom(w_body, bod)
    for k in range(7):   # leaf collar
        a = math.pi * (0.15 + 0.7 * k / 6) + math.pi
        dvec = Vector((math.cos(a), math.sin(a) * 0.9, 0))
        lf = ell((0, 0, 0), (0.026, 0.006, 0.042), leaf, segs=8, rings=6)
        lf.data.transform(Matrix.Translation(Vector((0, 0, 0.462)) + dvec * 0.05)
                          @ Vector((0, -1, 0)).rotation_difference(dvec + Vector((0, 0, -0.9))).to_matrix().to_4x4()
                          @ Matrix.Translation((0, 0, -0.02)))
        rig.rigid("chest", lf)
    rig.rigid("chest", torus(0.04, 0.008, (0, 0, 0.462), trim, verts=16, minor=5))

    def petal(a, z0, ln, w, flare, cup, lift, thick=0.006):
        rows = []
        for i in range(9):
            v = i / 8
            width = w * (math.sin(math.pi * min(1.0, 0.12 + v * 0.95)) ** 0.7) * (1 - 0.15 * v)
            if v > 0.82:
                width *= (1 - v) / 0.18
            r = 0.07 + flare * v ** 0.85
            z = z0 - ln * v + lift * v ** 3
            row = []
            for j in range(7):
                u = -1 + 2 * j / 6
                ang = a + u * width / max(r, 0.05)
                rr = r - cup * (1 - u * u) * 0.0 - cup * u * u
                row.append(Vector((rr * math.cos(ang), rr * math.sin(ang), z + 0.01 * u * u)))
            rows.append(row)
        return sheet(rows, dress, "petal", thick=thick, smooth=70)

    skirt = []
    for k in range(6):
        skirt.append(petal(2 * math.pi * k / 6, 0.37, 0.18, 0.085, 0.085, 0.01, 0.02))
    for k in range(6):
        skirt.append(petal(2 * math.pi * (k + 0.5) / 6, 0.375, 0.155, 0.075, 0.095, 0.012, 0.035))
    rig.custom(lambda p: {"hips": 1.0}, skirt)
    rig.rigid("hips", torus(0.074, 0.012, (0, 0, 0.36), leaf, verts=20, minor=6))   # the leaf sash
    for s, side in ((1, "L"), (-1, "R")):
        sh = Vector((0.085 * s, 0.0, 0.44))
        hand = Vector((0.118 * s, -0.012, 0.29))
        rig.smooth(["chest", "arm." + side], limb([sh + Vector((-0.02 * s, 0, 0.0)), sh, hand + Vector((0, 0, 0.02))],
                                                  [0.027, 0.025, 0.021], skin, verts=8, per=3), power=6)
        rig.rigid("arm." + side, sphere(0.042, sh + Vector((0.008 * s, 0, -0.012)), dress, scale=(1.0, 1.0, 0.85),
                                        segs=14, rings=8),
                  torus(0.03, 0.008, sh + Vector((0.016 * s, -0.003, -0.045)), trim,
                        rot=(0, math.radians(-12 * s), 0), verts=14, minor=5),
                  sphere(0.027, hand, skin, scale=(0.9, 1.0, 1.0), segs=10, rings=6))
        # legs: slim, into pointed leaf shoes that curl up at the toe, a white pompom on the tip
        rig.smooth(["root", "thigh." + side, "shin." + side],
                   limb([(0.045 * s, 0, 0.28), (0.05 * s, 0, 0.155), (0.052 * s, 0, 0.05)], [0.03, 0.025, 0.021],
                        skin, verts=8, per=3), power=6)
        rig.smooth(["thigh." + side, "shin." + side],
                   limb([(0.05 * s, 0, 0.17), (0.052 * s, 0, 0.1), (0.052 * s, 0, 0.04)], [0.0265, 0.024, 0.023],
                        trim, verts=10, per=2), power=6)
        rig.smooth(["thigh." + side, "shin." + side], torus(0.026, 0.008, (0.05 * s, 0, 0.17), trim, verts=12,
                                                            minor=5))
        sole = Vector((0.052 * s, 0, 0.0))
        shoe_parts = [ell(sole + Vector((0, -0.015, 0.03)), (0.034, 0.055, 0.03), shoe, segs=12, rings=8),
                      tube([sole + Vector((0, -0.045, 0.03)), sole + Vector((0, -0.08, 0.026)),
                            sole + Vector((0, -0.105, 0.04)), sole + Vector((0, -0.11, 0.06))],
                           [0.026, 0.016, 0.009, 0.003], shoe, verts=10, caps=True, name="toe"),
                      sphere(0.012, sole + Vector((0, -0.108, 0.066)), trim, segs=8, rings=6),
                      torus(0.027, 0.006, sole + Vector((0, -0.004, 0.058)), shoe, verts=12, minor=4)]
        rig.rigid("shin." + side, shoe_parts)

    # ---- the wings: two pairs on each side, angled back so they read in profile, faint veins
    def wing_outline(L, W, n=22, droop=0.0):
        """Outline of a rounded teardrop wing in its own plane: (along, across) from the root."""
        pts = []
        for k in range(n):
            t = 2 * math.pi * k / n
            x = 0.5 * L * (1 - math.cos(t))
            y = W * math.sin(t) * (0.35 + 0.65 * (x / L) ** 0.7) * (1 - 0.25 * (x / L) ** 3)
            pts.append((x, y + droop * (x / L) ** 2))
        return pts

    def place(pts2, s, along, across, root, bulge=0.0):
        al, ac = Vector(along).normalized(), Vector(across).normalized()
        out = []
        for x, y in pts2:
            out.append(root + al * x + ac * y + Vector((s * bulge * math.sin(math.pi * min(1, x / 0.3)), 0, 0)))
        return out

    for s, side in ((1, "L"), (-1, "R")):
        root = Vector((0.02 * s, 0.07, 0.445))
        up_al = Vector((0.42 * s, 0.55, 0.72))
        up_ac = Vector((0.0, 0.8, -0.6))
        lo_al = Vector((0.38 * s, 0.82, -0.42))
        lo_ac = Vector((0.0, 0.5, 0.86))
        parts = []
        for al, ac, L, W, rr in ((up_al, up_ac, 0.33, 0.095, root + Vector((0, 0, 0.01))),
                                 (lo_al, lo_ac, 0.21, 0.065, root + Vector((0, 0.005, -0.035)))):
            ol = place(wing_outline(L, W), s, al, ac, rr, 0.02)
            parts.append(outline_plate(ol, 0.004, wing, "wing"))
            rim = ol + [ol[0]]
            parts.append(tube(rim, [0.0035] * len(rim), vein, verts=4, caps=False, name="wing_rim"))
            for f in (0.35, 0.65):
                c = Vector(rr) + Vector(al).normalized() * L * 0.95
                mid = Vector(rr) + Vector(al).normalized() * L * f + Vector(ac).normalized() * W * 0.45 * (1 if f > 0.5 else -1)
                parts.append(tube([rr, mid, c], [0.0025, 0.002, 0.0012], vein, verts=4, caps=False, name="vein"))
            # a few sparkles
            for f, g in ((0.6, 0.3), (0.8, -0.2), (0.45, -0.45)):
                p = Vector(rr) + Vector(al).normalized() * L * f + Vector(ac).normalized() * W * g
                parts.append(ico(0.006, p + Vector((0.003 * s, 0, 0)), vein, sub=1))
        rig.rigid("wing." + side, parts)

    rig.build("fairy")

    # ---- the wand (a bone-attached node): a pale stick, a gold star at the tip, a ribbon bow
    H = Vector(B["wand"][0])
    D = (Vector(B["wand"][1]) - H).normalized()
    tip = H + D * 0.34
    wparts = [rod(H - D * 0.035, H + D * 0.275, 0.009, wood, r2=0.006, verts=8),
              sphere(0.011, H - D * 0.037, star_m, segs=8, rings=6),
              torus(0.0095, 0.004, H + D * 0.035, star_m, rot=(math.radians(-30), 0, 0), verts=10, minor=4)]
    st = star_mesh(0.058, 0.026, 0.02, star_m, name="wand_star")
    st.data.transform(Matrix.Translation(tip) @ Matrix.Rotation(math.radians(-30) * 0, 4, "X")
                      @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    wparts.append(st)
    for s in (-1, 1):   # a little ribbon bow under the star
        b0 = H + D * 0.27
        wparts.append(tube([b0, b0 + Vector((0, 0.02 * s, -0.012)) + D * 0.01, b0 + Vector((0, 0.03 * s, 0.006))],
                           [0.006, 0.009, 0.003], ribbon, verts=6, caps=True, name="bow"))
        wparts.append(tube([b0, b0 + Vector((0.004, 0.012 * s, -0.04)), b0 + Vector((0.0, 0.02 * s, -0.07))],
                           [0.004, 0.004, 0.002], ribbon, verts=5, caps=True, name="tail"))
    wn = rig.attach("wand", wparts, "wand", H)
    rig.child_empty(wn, "wand_tip", tip)

    # ---- poses (world axes, written facing -Y: +X about X tips an upright bone forward)
    blink = {"%eye.L": (1, 1, 0.12), "%eye.R": (1, 1, 0.12)}
    happy = {"%eye.L": (1.1, 1, 0.35), "%eye.R": (1.1, 1, 0.35)}
    wide = {"%eye.L": (1.08, 1, 1.12), "%eye.R": (1.08, 1, 1.12)}

    def wings(open_, flap=0.0):
        """open_: swing the wings apart (deg about Z), flap: about their length."""
        return {"wing.L": (flap, 0, open_), "wing.R": (flap, 0, -open_)}

    def wand(arm, d):
        """The wand's channel so that it points along d (degrees about X from straight down) given the arm's."""
        return {"wand": (d - arm - WAND0, 0, 0)}

    def arms(l, r, out_l=8, out_r=8, wd=None):
        p = {"arm.L": (l, -out_l, 0), "arm.R": (r, out_r, 0)}
        if wd is not None:
            p.update(wand(r, wd))
        return p

    def legs(tl, sl, tr, sr):
        return {"thigh.L": (tl, 0, 0), "shin.L": (sl, 0, 0), "thigh.R": (tr, 0, 0), "shin.R": (sr, 0, 0)}

    def tailp(a, b=0.0, side=0.0):
        return {"tail": (a, 0, side), "tail2": (b, 0, side * 0.6)}

    # idle: 2 s; breathing, the wings flutter in little bursts, the ponytail sways, the wand bobs, one blink
    def idle_p(k, extra=None):
        a = 2 * math.pi * k
        return merge({"chest": (2 * math.sin(a), 0, 0), "head": (-2 * math.sin(a), 0, 3 * math.sin(a)),
                      "%chest": (1 + 0.02 * math.sin(a), 1 + 0.02 * math.sin(a), 1 + 0.015 * math.sin(a)),
                      "@root": (0, 0, 0.004 * math.sin(2 * a))},
                     arms(-4 + 3 * math.sin(a), -16 + 4 * math.sin(a), 10, 12, -95 + 6 * math.sin(a)),
                     tailp(6 * math.sin(a - 0.6), 8 * math.sin(a - 1.2), 4 * math.sin(a)),
                     wings(14 + 10 * math.sin(4 * a), 6 * math.sin(4 * a + 0.5)), extra or {})
    rig.action("idle", {0: idle_p(0), 8: idle_p(8 / 60), 15: idle_p(0.25), 23: idle_p(23 / 60), 30: idle_p(0.5),
                        38: idle_p(38 / 60), 40: idle_p(40 / 60, blink), 42: idle_p(42 / 60), 45: idle_p(0.75),
                        53: idle_p(53 / 60), 60: idle_p(1)}, loop=True)

    # walk: 0.5 s, a light skipping step; f0 left foot forward and planted, f7.5 right foot forward
    def walk_p(ph, up):
        sg = 1 if ph == 0 else -1
        sw = 30 * sg * (1 - up)
        lift = 0.035 * up
        return merge({"@root": (0, 0, 0.02 * up), "hips": (4, 0, 5 * sg), "chest": (2, 0, -6 * sg),
                      "head": (-3, 0, 2 * sg)},
                     legs(-sw - (28 if (up and sg < 0) else 0), (40 if (up and sg < 0) else 4),
                          sw - (28 if (up and sg > 0) else 0), (40 if (up and sg > 0) else 4)),
                     arms(24 * sg * (1 - up * 0.4), -20 * sg * (1 - up * 0.4) - 10, 14, 12,
                          -100 - 10 * sg * (1 - up)),
                     tailp(-10 + 8 * up, 10 - 12 * up, 6 * sg), wings(12 + 14 * up, 8 * up))
    rig.action("walk", {0: walk_p(0, 0), 4: walk_p(0, 1), 8: walk_p(1, 0), 11: walk_p(1, 1), 15: walk_p(0, 0)},
               loop=True)

    # climb: 0.6 s on a ladder in front of her (rungs at x +0.15 .. +0.2 in the game): hands reach up in turn
    def climb_p(ph):
        sg = 1 if ph == 0 else -1
        return merge({"hips": (-8, 0, 0), "chest": (-4, 0, 4 * sg), "head": (-6, 0, 0)},
                     {"arm.L": (-150 + 35 * sg, -6, 0), "arm.R": (-150 - 35 * sg, 6, 0)},
                     wand(-150 - 35 * sg, -150), legs(-62 + 30 * sg, 88 - 34 * sg, -62 - 30 * sg, 88 + 34 * sg),
                     tailp(-12, 10), wings(10, 4))
    rig.action("climb", {0: climb_p(0), 9: climb_p(1), 18: climb_p(0)}, loop=True)

    # fall: 0.5 s; arms up, legs kicking, the wings beating hard, eyes wide
    def fall_p(k):
        a = 2 * math.pi * k
        return merge({"hips": (-4, 0, 0), "chest": (-6, 0, 3 * math.sin(a)), "head": (-8, 0, 0)},
                     arms(-140 + 15 * math.sin(a), -140 - 15 * math.sin(a), -62, -62, -170),
                     legs(-20 + 22 * math.sin(a), 30 - 20 * math.sin(a), -20 - 22 * math.sin(a), 30 + 20 * math.sin(a)),
                     tailp(-40 + 8 * math.sin(2 * a), -20 + 10 * math.sin(2 * a)),
                     wings(30 + 20 * math.sin(2 * a), 14 * math.sin(2 * a + 1)), wide)
    rig.action("fall", {f: fall_p(f / 15) for f in (0, 4, 8, 11, 15)}, loop=True)

    # cast: 0.25 s; a quick forward thrust of the wand (pointing straight ahead from f3), then easing back
    rest_arms = arms(-4, -16, 10, 12, -95)
    thrust = merge({"hips": (4, 0, -6), "chest": (10, 0, -10), "head": (-6, 0, 4), "@root": (0, -0.01, 0)},
                   arms(30, -92, 14, 4, -90), legs(-14, 10, 16, 6), tailp(22, 10), wings(26, 10), wide)
    rig.action("cast", {0: rest_arms, 3: thrust, 5: merge(thrust, {"arm.R": (-4, 0, 0)}), 8: merge(
        {"chest": (4, 0, -4)}, arms(10, -60, 12, 8, -88))})

    # hold: 1 s loop; arms up, both hands on the wand, which points straight up (wand_tip above her head)
    def hold_p(k):
        a = 2 * math.pi * k
        return merge({"hips": (-3, 0, 0), "chest": (-6 + 2 * math.sin(2 * a), 0, 0), "head": (-10, 0, 0),
                      "@root": (0, 0, -0.008 + 0.006 * math.sin(2 * a)),
                      "%hips": (1.02, 1.02, 0.98 + 0.015 * math.sin(2 * a))},
                     {"arm.L": (-126, -26, 0), "arm.R": (-130, 24, 0)}, wand(-130, -178),
                     legs(-8, 14, 6, 8), tailp(-6, 6 * math.sin(a)), wings(18 + 10 * math.sin(2 * a), 6), wide)
    rig.action("hold", {0: hold_p(0), 8: hold_p(0.25), 15: hold_p(0.5), 23: hold_p(0.75), 30: hold_p(1)}, loop=True)

    # slam: 0.4 s; from hold, the wand swings down in front (impact f3, 0.1 s), back up over the head (f6) and
    # down behind her (impact f9, 0.3 s), then back up to the hold pose (f12)
    def slam_p(arm, lean, sq=0.0):
        return merge({"hips": (lean * 0.4, 0, 0), "chest": (lean, 0, 0), "head": (-lean * 0.5, 0, 0),
                      "@root": (0, 0, -sq), "%hips": (1 + sq * 2, 1 + sq * 2, 1 - sq * 3)},
                     {"arm.L": (arm + 8, -14, 0), "arm.R": (arm, 12, 0)}, wand(arm, arm),
                     legs(-14 - lean * 0.4, 20, 10 - lean * 0.2, 10), tailp(lean * 0.8, lean * 0.5),
                     wings(18, 6), wide)
    rig.action("slam", {0: hold_p(0), 3: slam_p(-50, 18, 0.012), 4: slam_p(-60, 14, 0.008),
                        6: slam_p(-175, -6), 9: slam_p(-305, -16, 0.012), 10: slam_p(-292, -12, 0.006),
                        12: hold_p(0)})

    # die: 1.4 s; a jolt, a dizzy spin slowing down, then she sits down with a bump, legs out, eyes shut
    def spin_p(turn, wob):
        return merge({"root": (0, 0, turn), "chest": (wob, wob * 0.5, 0), "head": (wob, -wob, 0)},
                     arms(-60, -70, 50, 50, -150), legs(-10, 20, 10, 10), tailp(-30, -10, 20), wings(40, 10),
                     blink)
    sit = merge({"@root": (0, 0, -0.16), "hips": (-10, 0, 0), "chest": (6, 8, 0), "head": (14, -12, 0)},
                arms(10, -10, 40, 40, -60), legs(-80, 20, -86, 26), tailp(10, 20), wings(4, -10), blink)
    keys = {0: {}, 3: merge({"@root": (0, 0, 0.05)}, arms(-130, -130, -60, -60, -170), wide, wings(40, 20))}
    for i, f in enumerate((6, 10, 14, 18, 23, 28)):   # spins one way (-Z), slowing, to face the camera
        keys[f] = spin_p(-(135 * (i + 1) - 4 * i * i), 10 * (-1) ** i)
    keys[33] = merge(sit, {"root": (0, 0, -820), "@root": (0, 0, -0.1)})
    keys[36] = merge(sit, {"root": (0, 0, -810), "%hips": (1.08, 1.08, 0.9)})
    keys[40] = merge(sit, {"root": (0, 0, -810)})
    keys[42] = merge(sit, {"root": (0, 0, -810), "head": (8, 8, 0)})
    rig.action("die", keys)

    # cheer: 1 s loop; two hops, the wand waved high, the wings buzzing, happy eyes
    def cheer_p(h, sq, wave):
        return merge({"@root": (0, 0, h), "%hips": (1 + sq, 1 + sq, 1 - sq), "chest": (-4, 0, 0), "head": (-6, 0, wave * 0.1)},
                     arms(-140 + wave * 0.3, -140 - wave * 0.5, -55, -48, -145 - wave * 0.8), legs(-10 * h / 0.08, 30 * h / 0.08, -10 * h / 0.08, 30 * h / 0.08),
                     tailp(-20 * h / 0.08, 20 * h / 0.08), wings(30 + 200 * h, 10), happy)
    rig.action("cheer", {0: cheer_p(0, 0.06, 0), 4: cheer_p(0.07, -0.03, 25), 7: cheer_p(0.08, 0, 10),
                         11: cheer_p(0.02, -0.02, -20), 15: cheer_p(0, 0.06, 0), 19: cheer_p(0.07, -0.03, 25),
                         22: cheer_p(0.08, 0, 10), 26: cheer_p(0.02, -0.02, -20), 30: cheer_p(0, 0.06, 0)}, loop=True)
    rig.save("fairy")


# ------------------------------------------------------------------ enemies: shared face parts

def grumpy_eye(c, d, r, white, pupil, lid_m, shine, s, slant=22.0, cut=0.12, aspect=(1.0, 0.55, 1.15),
               look=(0, -1, 0), lid_drop=0.0):
    """A round eye facing d at c (radius r), its pupil looking along `look`, under a heavy lid slanting down
    towards the nose (s = +1 for the left eye, -1 for the right): the cute-grumpy look."""
    d = Vector(d).normalized()
    q = Vector((0, -1, 0)).rotation_difference(d).to_matrix().to_4x4()
    parts = [blob(r, c, white, aspect, d, segs=16, rings=10)]
    lk = Vector(look).normalized()
    lat = (lk - d * lk.dot(d))
    pp = Vector(c) + d * r * aspect[1] * 0.62 + lat * r * 0.38 + Vector((0, 0, -0.18 * r))
    parts.append(blob(r * 0.5, pp, pupil, (1.0, 0.45, 1.15), d, segs=12, rings=8))
    parts.append(sphere(r * 0.16, pp + d * r * 0.18 + Vector((0, 0, r * 0.22)) - lat.normalized() * r * 0.1, shine,
                        segs=6, rings=4))
    lid = hemi(r * 1.12, (0, 0, 0), (0, 0, 1), lid_m, cut=cut, segs=18, rings=10)
    lid.data.transform(Matrix.Translation(Vector(c)) @ q @ Matrix.Rotation(math.radians(slant * s), 4, "Y")
                       @ Matrix.Translation((0, 0, -lid_drop * r)) @ Matrix.Scale(1.0, 4) @
                       Matrix.Diagonal((aspect[0] * 1.02, max(aspect[1], 0.62) * 1.05, aspect[2] * 1.0, 1.0)))
    parts.append(lid)
    return parts


def brow(c, d, w, r, material, s, slant=-24.0):
    """A thick brow above an eye at c (facing d); a negative slant slopes it down towards the nose."""
    d = Vector(d).normalized()
    up = (Vector((0, 0, 1)) - d * d.z).normalized()
    across = d.cross(up).normalized() * s    # points towards the nose
    a = math.radians(slant)
    pts = []
    for k in (-1, -0.3, 0.4, 1):
        pts.append(Vector(c) + across * (w * k) + up * (w * k * math.tan(a) * 0.5 + 0.004 * (1 - k * k)))
    return limb(pts, [r * 0.7, r, r, r * 0.6], material, verts=6, per=2, caps=True)


def seg_ball(c, r, axis, material, squash=0.86, segs=20, rings=12):
    """A body segment: a sphere squashed along `axis` (the spine direction)."""
    o = sphere(r, (0, 0, 0), material, scale=(1.0, squash, 1.0), segs=segs, rings=rings)
    q = Vector((0, 1, 0)).rotation_difference(Vector(axis).normalized())
    o.data.transform(Matrix.Translation(Vector(c)) @ q.to_matrix().to_4x4())
    return o


def enemy_mats(name, skin, belly):
    return (mat(name + "_skin", skin, 0.5, coat=0.35), mat(name + "_belly", belly, 0.6, coat=0.15),
            mat(name + "_eye", (1.0, 0.99, 0.95), 0.25, coat=0.7), mat(name + "_pupil", (0.05, 0.03, 0.06), 0.2, coat=1.0),
            mat(name + "_shine", (1.0, 1.0, 1.0), 0.1, emit=3.0), mat(name + "_mouth", (0.35, 0.05, 0.1), 0.5),
            mat(name + "_tooth", (1.0, 0.98, 0.92), 0.3, coat=0.5))


def finish_rig(rig, name):
    rig.arm.name = rig.arm.data.name = name + "_rig"


# ------------------------------------------------------------------ the grub

GRUB = [(Vector((0, 0.3, 0.085)), 0.085), (Vector((0, 0.195, 0.112)), 0.112), (Vector((0, 0.065, 0.16)), 0.158),
        (Vector((0, -0.02, 0.31)), 0.142), (Vector((0, -0.04, 0.45)), 0.122)]
GRUB_HC = Vector((0, -0.05, 0.615))
GRUB_HR = 0.165


def grub():
    reset()
    skin, belly, white, pupil, shine, mouth, tooth = enemy_mats("grub", (0.36, 0.72, 0.06), (1.0, 0.86, 0.36))
    band = mat("grub_band", (0.16, 0.38, 0.04), 0.6, coat=0.2)
    spot = mat("grub_spot", (1.0, 0.55, 0.12), 0.45, coat=0.4)
    foot = mat("grub_foot", (0.32, 0.24, 0.14), 0.6)
    brow_m = mat("grub_brow", (0.2, 0.3, 0.06), 0.6)
    B = {"root": ((0, 0, 0), (0, 0, 0.05), None),
         "belly": ((0, 0.13, 0.12), (0, -0.01, 0.25), "root"),
         "tail": ((0, 0.13, 0.12), (0, 0.33, 0.08), "belly"),
         "chest": ((0, -0.01, 0.25), (0, -0.045, 0.52), "belly"),
         "head": ((0, -0.045, 0.52), (0, -0.05, 0.8), "chest"),
         "ant.L": ((0.06, -0.02, 0.76), (0.13, 0.06, 0.9), "head"),
         "ant.R": ((-0.06, -0.02, 0.76), (-0.13, 0.06, 0.9), "head"),
         "arm.L": ((0.1, -0.08, 0.44), (0.17, -0.14, 0.37), "chest"),
         "arm.R": ((-0.1, -0.08, 0.44), (-0.17, -0.14, 0.37), "chest")}
    rig = SideRig(B)
    spine = ["tail", "belly", "chest", "head"]   # tail and chest both hang off the belly
    body = []
    for i, (c, r) in enumerate(GRUB):
        nxt = GRUB[min(i + 1, len(GRUB) - 1)][0]
        prv = GRUB[max(i - 1, 0)][0]
        axis = (nxt - prv).normalized()
        body.append(seg_ball(c, r, axis, skin, squash=0.88))
        # a darker band ring where each segment meets the next
        if i < len(GRUB) - 1:
            m = c.lerp(nxt, 0.5)
            rr = (r + GRUB[i + 1][1]) * 0.36
            t = torus(rr, 0.009, (0, 0, 0), band, verts=24, minor=6)
            t.data.transform(Matrix.Translation(m) @ Vector((0, 0, 1)).rotation_difference(nxt - c).to_matrix().to_4x4())
            body.append(t)
        # a pale belly plate on the front/underside, two orange eye-spots on each flank
        bd = Vector((0, -1, -0.6 if i < 3 else -0.1)).normalized()
        if i < 3:
            bd = Vector((0, -0.25, -1)).normalized() if i < 2 else Vector((0, -0.8, -0.6)).normalized()
        body.append(blob(r * 0.62, c + bd * r * 0.62, belly, (1.0, 0.45, 0.9), bd, segs=12, rings=8))
        for sd in (-1, 1):
            sdv = Vector((sd, 0.1, 0.35)).normalized()
            body.append(blob(r * 0.3, c + sdv * r * 0.86, spot, (1.0, 0.4, 1.0), sdv, segs=12, rings=8))
            body.append(blob(r * 0.13, c + sdv * r * 0.97, band, (1.0, 0.4, 1.0), sdv, segs=8, rings=6))
    rig.smooth(spine, body, power=5)
    # little prolegs under the back segments
    for i in (0, 1, 2):
        c, r = GRUB[i]
        for sd in (-1, 1):
            p = c + Vector((sd * r * 0.55, 0, -r * 0.75))
            rig.smooth(spine, ell(p + Vector((0, 0, -0.01)), (0.032, 0.04, 0.03), foot, segs=10, rings=6), power=5)
    # the head: big and round, a pale muzzle, grumpy eyes under a heavy brow, a buck tooth, antennae
    head = [sphere(GRUB_HR, GRUB_HC, skin, scale=(1.05, 0.95, 0.95), segs=28, rings=16)]
    md = Vector((0, -1, -0.45)).normalized()
    mc = GRUB_HC + md * GRUB_HR * 0.78
    head.append(blob(0.085, mc, belly, (1.25, 0.6, 0.75), md, segs=16, rings=10))
    for s_ in (-1, 1):
        d = Vector((math.sin(math.radians(44)) * s_, -math.cos(math.radians(44)), 0.22)).normalized()
        ec = GRUB_HC + d * GRUB_HR * 0.86
        head += grumpy_eye(ec, d, 0.045, white, pupil, skin, shine, s_, slant=24, cut=0.1)
        head.append(brow(ec + d * 0.02 + Vector((0, 0, 0.05)), d, 0.04, 0.013, brow_m, s_, slant=-30))
        cd = Vector((0.85 * s_, -0.5, -0.25)).normalized()
        head.append(blob(0.03, GRUB_HC + cd * GRUB_HR * 0.95, spot, (1.2, 0.3, 0.8), cd, segs=10, rings=6))
    # a pouty frown and one buck tooth
    fr = [mc + Vector((x, -0.045 - 0.25 * x * x, -0.028 + 1.6 * x * x)) for x in (-0.045, -0.022, 0.0, 0.022, 0.045)]
    head.append(tube(fr, [0.006, 0.009, 0.01, 0.009, 0.006], mouth, verts=6, caps=True, name="frown"))
    head.append(box((0.02, 0.008, 0.022), mc + Vector((0.008, -0.063, -0.04)), tooth, bevel=0.004))
    rig.rigid("head", head)
    for s_, side in ((1, "L"), (-1, "R")):
        a = [Vector((0.05 * s_, -0.03, 0.76)), Vector((0.09 * s_, 0.0, 0.84)), Vector((0.13 * s_, 0.05, 0.89)),
             Vector((0.16 * s_, 0.1, 0.9))]
        rig.rigid("ant." + side, limb(a, [0.012, 0.01, 0.008, 0.007], band, verts=6, per=2),
                  sphere(0.026, a[-1] + Vector((0.006 * s_, 0.008, 0.008)), spot, segs=10, rings=6))
        arm = limb([(0.08 * s_, -0.06, 0.45), (0.13 * s_, -0.11, 0.41), (0.165 * s_, -0.14, 0.37)],
                   [0.024, 0.021, 0.019], skin, verts=8, per=2)
        rig.smooth(["chest", "arm." + side], arm, power=6)
        rig.rigid("arm." + side, sphere(0.03, (0.17 * s_, -0.15, 0.36), belly, segs=10, rings=6))
    rig.build("grub")
    finish_rig(rig, "grub")

    def ants(a, b=0.0):
        return {"ant.L": (a, -b, 0), "ant.R": (a, b, 0)}

    def arms(l, r, out=0.0):
        return {"arm.L": (l, -out, 0), "arm.R": (r, out, 0)}

    # walk: 0.8 s; a ripple runs from the tail to the head (the segments hump up in turn), the arms swing
    def walk_p(k):
        a = 2 * math.pi * k
        return merge({"tail": (10 * max(0.0, math.sin(a)) - 4, 0, 0),
                      "belly": (8 * math.sin(a - 1.2), 0, 3 * math.sin(a)),
                      "%belly": (1 + 0.04 * math.sin(a - 1.2), 1 + 0.04 * math.sin(a - 1.2),
                                 1 - 0.05 * math.sin(a - 1.2)),
                      "chest": (6 * math.sin(a - 2.2), 0, -3 * math.sin(a)), "head": (-6 * math.sin(a - 2.8), 0, 4 * math.sin(a)),
                      "@root": (0, 0, 0.012 * math.sin(2 * a))},
                     ants(10 * math.sin(a - 3.2), 8 * math.sin(2 * a)), arms(25 * math.sin(a), -25 * math.sin(a), 10))
    rig.action("walk", {f: walk_p(f / 24) for f in (0, 3, 6, 9, 12, 15, 18, 21, 24)}, loop=True)

    # climb: 0.8 s; reared up straight against the ladder in front, arms reaching up in turn, the tail curled
    def climb_p(k):
        a = 2 * math.pi * k
        sg = math.sin(a)
        return merge({"tail": (-55 + 6 * sg, 0, 4 * sg), "belly": (-6, 0, 0), "chest": (-6, 0, 4 * sg), "head": (-4, 0, 0),
                      "@root": (0, 0, 0.015 * math.sin(2 * a))},
                     arms(-125 + 35 * sg, -125 - 35 * sg, 0), ants(-10, 6 * sg))
    rig.action("climb", {f: climb_p(f / 24) for f in (0, 6, 12, 18, 24)}, loop=True)

    # caught: 0.6 s; wriggling in the air, curling and twisting, arms flailing, squinting
    def caught_p(k):
        a = 2 * math.pi * k
        sg = math.sin(a)
        return merge({"tail": (-30 + 30 * math.sin(a + 1.5), 0, 25 * sg), "belly": (-14 * math.sin(a + 0.8), 10 * sg, -20 * sg),
                      "chest": (10 * math.sin(a + 0.2), -10 * sg, 18 * sg), "head": (-8 * sg, 10 * sg, -12 * sg)},
                     arms(-110 + 50 * sg, -110 - 50 * sg, 30), ants(20 * sg, 20 * math.cos(a)))
    rig.action("caught", {f: caught_p(f / 18) for f in (0, 3, 6, 9, 12, 15, 18)}, loop=True)
    rig.save("grub")


# ------------------------------------------------------------------ the bopper

def bopper():
    reset()
    skin, belly, white, pupil, shine, mouth, tooth = enemy_mats("bopper", (0.95, 0.2, 0.08), (1.0, 0.9, 0.72))
    spot = mat("bopper_spot", (1.0, 0.96, 0.84), 0.5, coat=0.3)
    gill = mat("bopper_gill", (0.9, 0.66, 0.55), 0.7)
    boot = mat("bopper_boot", (0.42, 0.26, 0.5), 0.45, coat=0.4)
    brow_m = mat("bopper_brow", (0.35, 0.22, 0.14), 0.6)
    nose_m = mat("bopper_nose", (1.0, 0.6, 0.5), 0.5, coat=0.3)
    B = {"root": ((0, 0, 0), (0, 0, 0.05), None),
         "body": ((0, 0, 0.1), (0, 0, 0.42), "root"),
         "cap": ((0, 0, 0.42), (0, 0, 0.8), "body"),
         "arm.L": ((0.12, -0.02, 0.3), (0.2, -0.04, 0.22), "body"),
         "arm.R": ((-0.12, -0.02, 0.3), (-0.2, -0.04, 0.22), "body"),
         "leg.L": ((0.07, 0, 0.12), (0.075, -0.01, 0.03), "root"),
         "leg.R": ((-0.07, 0, 0.12), (-0.075, -0.01, 0.03), "root")}
    rig = SideRig(B)
    # the stem: a plump cream body with the face, tapering under the cap
    prof = [(0.12, 0.5), (0.14, 0.46), (0.158, 0.38), (0.172, 0.28), (0.168, 0.18), (0.145, 0.11), (0.1, 0.07)]
    from blastyard_bombers import smooth_path
    prof = [(0.0, 0.505)] + [(v.x, v.y) for v in smooth_path([Vector((r_, z_, 0)) for r_, z_ in prof], 3)] + [(0.0, 0.062)]
    stem = lathe_r(prof, belly, segs=32, name="stem", smooth=60)

    def w_body(p):
        t = smoothstep(0.42, 0.5, p.z)
        return {"body": 1 - t + 1e-4, "cap": t + 1e-4}
    rig.custom(w_body, stem)
    fc = Vector((0, 0, 0.3))
    face = []
    for s_ in (-1, 1):
        d = Vector((math.sin(math.radians(40)) * s_, -math.cos(math.radians(40)), 0.12)).normalized()
        ec = fc + Vector((d.x * 0.155, d.y * 0.155, 0.045))
        face += grumpy_eye(ec, d, 0.054, white, pupil, belly, shine, s_, slant=26, cut=0.05)
        face.append(brow(ec + d * 0.024 + Vector((0, 0, 0.056)), d, 0.042, 0.014, brow_m, s_, slant=-34))
        cd = Vector((0.75 * s_, -0.6, -0.2)).normalized()
        face.append(blob(0.03, fc + cd * 0.17 + Vector((0, 0, -0.025)), nose_m, (1.2, 0.3, 0.8), cd, segs=10, rings=6))
        # little pointed imp ears poking out under the brim
        e0 = Vector((0.15 * s_, 0.0, 0.4))
        ear = tube([e0, e0 + Vector((0.07 * s_, 0.01, -0.005)), e0 + Vector((0.14 * s_, 0.035, 0.03))],
                   [0.036, 0.024, 0.003], belly, verts=8, caps=True, name="ear")
        for v in ear.data.vertices:
            v.co.y = e0.y + (v.co.y - e0.y) * 0.45
        ear.data.update()
        face.append(ear)
        face.append(blob(0.016, e0 + Vector((0.07 * s_, -0.008, 0.002)), nose_m, (1.8, 0.4, 0.8), (0, -1, 0), segs=8, rings=5))
    face.append(sphere(0.036, (0, -0.18, 0.3), nose_m, scale=(1.0, 0.8, 0.85), segs=12, rings=8))   # a round nose
    fr = [Vector((x, -0.17 + 1.2 * x * x, 0.24 - 2.4 * x * x)) for x in (-0.05, -0.025, 0.0, 0.025, 0.05)]
    face.append(tube(fr, [0.005, 0.008, 0.009, 0.008, 0.005], mouth, verts=6, caps=True, name="frown"))
    rig.rigid("body", face)
    # the cap: a wide dome with a rolled rim, cream spots, gills underneath
    cap_o = lathe_r([(0.0, 0.88), (0.1, 0.87), (0.19, 0.83), (0.26, 0.76), (0.3, 0.67), (0.315, 0.58),
                     (0.3, 0.535), (0.26, 0.52), (0.0, 0.515)], skin, segs=36, name="cap", smooth=60)
    caps = [cap_o]
    rnd = random.Random(33)
    for k, (yaw, el, r) in enumerate(((0, 50, 0.055), (60, 30, 0.045), (-60, 30, 0.045), (130, 40, 0.05),
                                      (-130, 40, 0.05), (180, 20, 0.04), (30, 12, 0.032), (-30, 12, 0.032),
                                      (95, 8, 0.035), (-95, 8, 0.035), (155, 70, 0.04), (-90, 72, 0.035))):
        d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(el)),
                    -math.cos(math.radians(yaw)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        # a point on the cap: scale to the dome
        k = 1.0 / math.sqrt((d.x / 0.312) ** 2 + (d.y / 0.312) ** 2 + (d.z / 0.3) ** 2)
        p = Vector((0, 0, 0.58)) + d * k
        caps.append(blob(r * 1.35, p, spot, (1.0, 0.3, 1.0), Vector((d.x, d.y, d.z * 1.4)), segs=14, rings=8))
    gl = lathe_r([(0.0, 0.52), (0.28, 0.52), (0.25, 0.505), (0.12, 0.485), (0.0, 0.485)], gill, segs=36,
                 radial=lambda k, z: 1.0 + (0.03 if k % 2 else 0.0), name="gills", smooth=0)
    caps.append(gl)
    rig.rigid("cap", caps)
    # tiny arms with mitts, round boots
    for s_, side in ((1, "L"), (-1, "R")):
        rig.smooth(["body", "arm." + side], limb([(0.11 * s_, -0.02, 0.31), (0.16 * s_, -0.03, 0.26),
                                                  (0.195 * s_, -0.04, 0.22)], [0.022, 0.02, 0.018], belly,
                                                 verts=8, per=2), power=6)
        rig.rigid("arm." + side, sphere(0.032, (0.2 * s_, -0.045, 0.215), boot, segs=10, rings=6))
        rig.smooth(["root", "leg." + side], limb([(0.07 * s_, 0, 0.13), (0.075 * s_, -0.005, 0.06)], [0.026, 0.024],
                                                 belly, verts=8, per=2), power=6)
        rig.rigid("leg." + side, ell((0.075 * s_, -0.03, 0.04), (0.055, 0.075, 0.045), boot, segs=14, rings=8),
                  torus(0.03, 0.008, (0.075 * s_, -0.005, 0.075), boot, verts=12, minor=4))
    rig.build("bopper")
    finish_rig(rig, "bopper")

    def legs(l, r, lz=0.0, rz=0.0):
        return {"leg.L": (l, 0, 0), "leg.R": (r, 0, 0), "@leg.L": (0, 0, lz), "@leg.R": (0, 0, rz)}

    def arms(l, r, out=10):
        return {"arm.L": (l, -out, 0), "arm.R": (r, out, 0)}

    # walk: 0.6 s, one hop: crouch (f0), spring (f4), the top of the hop (f9), landing squash (f15), recover (f18)
    crouch = merge({"%body": (1.14, 1.14, 0.82), "@body": (0, 0, -0.02), "cap": (6, 0, 0), "%cap": (1.06, 1.06, 0.9)},
                   legs(-10, -10), arms(10, 10, 20))
    spring = merge({"@root": (0, 0, 0.08), "%body": (0.9, 0.9, 1.14), "cap": (-6, 0, 0), "%cap": (0.95, 0.95, 1.08)},
                   legs(18, 22, 0.0, 0.0), arms(-30, -30, 40))
    top = merge({"@root": (0, 0, 0.13), "%body": (0.96, 0.96, 1.05), "cap": (-10, 0, 0)},
                legs(-14, 8, 0.01, 0.0), arms(-50, -40, 50))
    land = merge({"@root": (0, 0, 0.0), "%body": (1.18, 1.18, 0.78), "@body": (0, 0, -0.02), "cap": (12, 0, 0),
                  "%cap": (1.1, 1.1, 0.86)}, legs(-6, -4), arms(20, 20, 30))
    rig.action("walk", {0: crouch, 4: spring, 9: top, 13: merge(top, {"@root": (0, 0, 0.05)}), 15: land, 18: crouch},
               loop=True)

    # climb: 0.6 s; hop-stepping up the rungs in front, mitts reaching up in turn
    def climb_p(sg):
        return merge({"body": (-6, 0, 4 * sg), "cap": (-6, 0, -4 * sg), "%body": (1 - 0.03 * sg, 1 - 0.03 * sg, 1 + 0.04 * sg)},
                     arms(-150 + 30 * sg, -150 - 30 * sg, 20), legs(-50 + 40 * sg, -50 - 40 * sg, 0.03 * (sg > 0), 0.03 * (sg < 0)))
    rig.action("climb", {0: climb_p(1), 9: climb_p(-1), 18: climb_p(1)}, loop=True)

    # caught: 0.5 s; kicking and squirming, the cap wobbling
    def caught_p(k):
        a = 2 * math.pi * k
        sg = math.sin(a)
        return merge({"body": (6 * math.cos(a), 12 * sg, 0), "cap": (10 * math.sin(2 * a), -18 * sg, 0),
                      "%body": (1 + 0.05 * math.sin(2 * a), 1 + 0.05 * math.sin(2 * a), 1 - 0.06 * math.sin(2 * a))},
                     arms(-120 + 50 * sg, -120 - 50 * sg, 40), legs(-30 * sg - 10, 30 * sg - 10))
    rig.action("caught", {f: caught_p(f / 15) for f in (0, 3, 6, 9, 12, 15)}, loop=True)
    rig.save("bopper")


# ------------------------------------------------------------------ the snapper

def snapper():
    reset()
    skin, belly, white, pupil, shine, mouth, tooth = enemy_mats("snapper", (0.45, 0.22, 0.8), (1.0, 0.86, 0.42))
    scute = mat("snapper_scute", (0.32, 0.16, 0.55), 0.5, coat=0.3)
    claw = mat("snapper_claw", (1.0, 0.95, 0.85), 0.4, coat=0.4)
    brow_m = mat("snapper_brow", (0.22, 0.1, 0.36), 0.6)
    HCs = Vector((0, -0.04, 0.6))
    B = {"root": ((0, 0, 0), (0, 0, 0.05), None),
         "hips": ((0, 0.02, 0.17), (0, 0.0, 0.32), "root"),
         "chest": ((0, 0.0, 0.32), (0, -0.03, 0.5), "hips"),
         "head": ((0, -0.03, 0.5), (0, -0.06, 0.74), "chest"),
         "jaw": ((0, -0.02, 0.53), (0, -0.3, 0.5), "head"),
         "tail": ((0, 0.1, 0.2), (0, 0.27, 0.1), "hips"),
         "tail2": ((0, 0.27, 0.1), (0, 0.45, 0.06), "tail"),
         "arm.L": ((0.12, -0.04, 0.42), (0.17, -0.1, 0.33), "chest"),
         "arm.R": ((-0.12, -0.04, 0.42), (-0.17, -0.1, 0.33), "chest"),
         "leg.L": ((0.08, 0.01, 0.17), (0.085, -0.01, 0.04), "root"),
         "leg.R": ((-0.08, 0.01, 0.17), (-0.085, -0.01, 0.04), "root")}
    rig = SideRig(B)
    torso = ell((0, 0.01, 0.31), (0.15, 0.14, 0.19), skin, segs=24, rings=14)
    for v in torso.data.vertices:   # pear-shaped: wider low down
        t = (v.co.z - 0.31) / 0.19
        k = 1.0 + 0.12 * max(0.0, -t) - 0.12 * max(0.0, t)
        v.co.x *= k
        v.co.y = 0.01 + (v.co.y - 0.01) * k
    torso.data.update()
    bel = ell((0, -0.07, 0.3), (0.105, 0.09, 0.15), belly, segs=18, rings=12)
    bands = []
    for z in (0.2, 0.26, 0.32, 0.38):   # belly plate lines
        w = 0.1 * math.sqrt(max(0.0, 1 - ((z - 0.3) / 0.15) ** 2))
        pts = [Vector((x, -0.07 - 0.09 * math.sqrt(max(0.0, 1 - (x / 0.105) ** 2 - ((z - 0.3) / 0.15) ** 2)) - 0.003, z))
               for x in (-w * 0.9, -w * 0.45, 0.0, w * 0.45, w * 0.9)]
        bands.append(tube(pts, [0.003] * 5, scute, verts=4, caps=False, name="bandline"))

    def w_body(p):
        t = smoothstep(0.28, 0.4, p.z)
        return {"hips": 1 - t + 1e-4, "chest": t + 1e-4}
    rig.custom(w_body, torso, bel, bands)
    # the head: a round skull with bulging eye-turrets on top, a long broad snout (upper jaw), nostrils
    head = [ell(HCs, (0.14, 0.13, 0.12), skin, segs=24, rings=14)]
    snout = ell((0, -0.2, 0.575), (0.115, 0.17, 0.07), skin, segs=22, rings=12)
    for v in snout.data.vertices:   # flat underside (the bite line), a rounded tip
        if v.co.z < 0.56:
            v.co.z = 0.56 - (0.56 - v.co.z) * 0.25
    snout.data.update()
    head.append(snout)
    for s_ in (-1, 1):
        head.append(sphere(0.016, (0.04 * s_, -0.35, 0.615), scute, segs=8, rings=6))   # nostril bumps
        ec = Vector((0.075 * s_, -0.06, 0.7))
        head.append(sphere(0.062, ec, skin, segs=16, rings=10))     # the eye turret
        d = Vector((0.55 * s_, -0.8, 0.2)).normalized()
        head += grumpy_eye(ec + d * 0.012, d, 0.052, white, pupil, skin, shine, s_, slant=28, cut=0.02,
                           aspect=(1.0, 0.7, 1.0))
        head.append(brow(ec + d * 0.035 + Vector((0, 0, 0.05)), d, 0.04, 0.014, brow_m, s_, slant=-36))
    for k in range(5):   # upper teeth along the bite line (pointing down)
        for s_ in (-1, 1):
            u = k / 4
            y = -0.08 - 0.25 * u
            x = s_ * (0.1 - 0.055 * u * u)
            head.append(rod((x, y, 0.565), (x * 1.02, y, 0.528), 0.014, tooth, r2=0.0, verts=6))
    for k, y in enumerate((-0.02, 0.06, 0.13)):   # scutes on the crown and neck
        head.append(rod((0, y, 0.7 - 0.05 * k), (0, y + 0.02, 0.76 - 0.05 * k), 0.028, scute, r2=0.004, verts=6))
    rig.rigid("head", head)
    # the lower jaw: a big underbite scoop, pale inside, teeth pointing up
    jaw = [ell((0, -0.17, 0.535), (0.12, 0.17, 0.045), skin, segs=22, rings=10)]
    for v in jaw[0].data.vertices:
        if v.co.z > 0.545:
            v.co.z = 0.545 + (v.co.z - 0.545) * 0.2
    jaw[0].data.update()
    jaw.append(ell((0, -0.16, 0.548), (0.095, 0.14, 0.012), mouth, segs=18, rings=6))   # the inside of the mouth
    jaw.append(ell((0, -0.13, 0.55), (0.05, 0.08, 0.012), mat("snapper_tongue", (1.0, 0.45, 0.55), 0.5), segs=12, rings=6))
    for k in range(4):
        for s_ in (-1, 1):
            u = (k + 0.5) / 4
            y = -0.06 - 0.24 * u
            x = s_ * (0.1 - 0.05 * u * u)
            jaw.append(rod((x, y, 0.545), (x * 1.02, y, 0.58), 0.013, tooth, r2=0.0, verts=6))
    rig.rigid("jaw", jaw)
    # the tail: thick, tapering along the ground, a row of scutes
    tl = limb([(0, 0.08, 0.24), (0, 0.2, 0.15), (0, 0.32, 0.09), (0, 0.44, 0.07), (0, 0.52, 0.09)],
              [0.11, 0.085, 0.06, 0.035, 0.01], skin, verts=14, per=3, caps=True)
    rig.smooth(["hips", "tail", "tail2"], tl, power=5)
    for k in range(6):
        u = k / 5
        p = Vector((0, 0.12 + 0.33 * u, 0.28 - 0.17 * u - 0.03 * u * u + 0.01))
        r = 0.03 * (1 - 0.6 * u)
        rig.smooth(["hips", "tail", "tail2"], rod(p, p + Vector((0, 0.02, 0.05 * (1 - 0.4 * u))), r, scute, r2=0.003, verts=6), power=8)
    for k in range(3):   # back scutes
        p = Vector((0, 0.13 - 0.01 * k, 0.33 + 0.07 * k))
        rig.smooth(["hips", "chest"], rod(p, p + Vector((0, 0.05, 0.02)), 0.028, scute, r2=0.004, verts=6), power=6)
    # stubby arms with three claws; big flat feet
    for s_, side in ((1, "L"), (-1, "R")):
        rig.smooth(["chest", "arm." + side], limb([(0.1 * s_, -0.03, 0.43), (0.145 * s_, -0.07, 0.38),
                                                   (0.17 * s_, -0.1, 0.33)], [0.032, 0.028, 0.026], skin, verts=8,
                                                  per=2), power=6)
        hand = [sphere(0.034, (0.175 * s_, -0.105, 0.325), skin, segs=10, rings=6)]
        for dx in (-0.016, 0.0, 0.016):
            hand.append(rod((0.175 * s_ + dx, -0.13, 0.315), (0.175 * s_ + dx * 1.3, -0.15, 0.3), 0.007, claw, r2=0.0,
                            verts=5))
        rig.rigid("arm." + side, hand)
        rig.smooth(["hips", "leg." + side], limb([(0.075 * s_, 0.01, 0.18), (0.085 * s_, -0.0, 0.1),
                                                  (0.085 * s_, -0.01, 0.05)], [0.05, 0.045, 0.04], skin, verts=10,
                                                 per=2), power=6)
        foot = [ell((0.085 * s_, -0.04, 0.03), (0.06, 0.09, 0.032), skin, segs=14, rings=8)]
        for dx in (-0.025, 0.0, 0.025):
            foot.append(rod((0.085 * s_ + dx, -0.115, 0.025), (0.085 * s_ + dx * 1.2, -0.14, 0.012), 0.009, claw,
                            r2=0.0, verts=5))
        rig.rigid("leg." + side, foot)
    rig.build("snapper")
    finish_rig(rig, "snapper")

    def legs(l, r, lz=0.0, rz=0.0):
        return {"leg.L": (l, 0, 0), "leg.R": (r, 0, 0), "@leg.L": (0, 0, lz), "@leg.R": (0, 0, rz)}

    def arms(l, r, out=10):
        return {"arm.L": (l, -out, 0), "arm.R": (r, out, 0)}

    # walk: 0.7 s; a stompy waddle, rocking side to side, the tail swishing, the jaw chattering a little
    def walk_p(ph, up):
        sg = 1 if ph == 0 else -1
        sw = 26 * sg * (1 - up)
        return merge({"@root": (0, 0, 0.018 * up), "hips": (4, 6 * sg, 6 * sg), "chest": (2, -4 * sg, -4 * sg),
                      "head": (-3, -2 * sg, 3 * sg), "jaw": (-6 * up, 0, 0),
                      "tail": (0, 0, -14 * sg), "tail2": (0, 0, -16 * sg)},
                     legs(-sw, sw, 0.03 * up * (sg < 0), 0.03 * up * (sg > 0)),
                     arms(20 * sg, -20 * sg, 14))
    rig.action("walk", {0: walk_p(0, 0), 5: walk_p(0, 1), 10: walk_p(1, 0), 16: walk_p(1, 1), 21: walk_p(0, 0)},
               loop=True)

    # climb: 0.7 s; hauling up the rungs in front, the tail hanging
    def climb_p(sg):
        return merge({"hips": (-8, 0, 0), "chest": (-6, 0, 5 * sg), "head": (-6, 0, 0), "tail": (-40, 0, 6 * sg),
                      "tail2": (-20, 0, 8 * sg)},
                     arms(-140 + 35 * sg, -140 - 35 * sg, 10), legs(-50 + 35 * sg, -50 - 35 * sg))
    rig.action("climb", {0: climb_p(1), 10: climb_p(-1), 21: climb_p(1)}, loop=True)

    # caught: 0.5 s; thrashing, the jaw snapping, the tail lashing
    def caught_p(k):
        a = 2 * math.pi * k
        sg = math.sin(a)
        return merge({"hips": (8 * math.cos(a), 10 * sg, 0), "chest": (0, -8 * sg, 10 * sg), "head": (-10, 0, -8 * sg),
                      "jaw": (-28 * max(0.0, math.sin(2 * a)), 0, 0), "tail": (-30, 0, 30 * sg),
                      "tail2": (-10, 0, 30 * math.sin(a - 1))},
                     arms(-110 + 45 * sg, -110 - 45 * sg, 35), legs(-30 * sg - 10, 30 * sg - 10))
    rig.action("caught", {f: caught_p(f / 15) for f in (0, 2, 4, 6, 8, 10, 12, 15)}, loop=True)

    # bite: 0.5 s; rears back with the jaw wide (f5), lunges and snaps shut (f8), holds, recovers
    rear = merge({"hips": (-6, 0, 0), "chest": (-10, 0, 0), "head": (-14, 0, 0), "jaw": (-42, 0, 0),
                  "@root": (0, 0.03, 0)}, arms(-40, -40, 30), legs(-6, 8))
    snap = merge({"hips": (10, 0, 0), "chest": (14, 0, 0), "head": (6, 0, 0), "jaw": (4, 0, 0),
                  "@root": (0, -0.06, 0)}, arms(-70, -70, 10), legs(-24, 18), {"tail": (14, 0, 0)})
    rig.action("bite", {0: {}, 5: rear, 8: snap, 10: merge(snap, {"jaw": (0, 0, 0)}), 15: {}})
    rig.save("snapper")


# ------------------------------------------------------------------ the cloudlet

def cloudlet():
    reset()
    skin, belly, white, pupil, shine, mouth, tooth = enemy_mats("cloudlet", (0.3, 0.32, 0.46), (0.62, 0.66, 0.8))
    bolt_m = mat("cloudlet_bolt_glow", (1.0, 0.9, 0.3), 0.3, emit=4.0, emit_color=(1.0, 0.85, 0.2))
    drop_m = mat("cloudlet_drop", (0.55, 0.78, 1.0), 0.1, coat=1.0, alpha=0.7)
    brow_m = mat("cloudlet_brow", (0.2, 0.2, 0.32), 0.6)
    cheek = mat("cloudlet_cheek", (0.85, 0.55, 0.75), 0.7)
    C = Vector((0, 0, 0.52))
    B = {"root": ((0, 0, 0), (0, 0, 0.05), None),
         "body": ((0, 0, 0.3), (0, 0, 0.62), "root"),
         "puff.T": ((0, 0.02, 0.62), (0, 0.02, 0.84), "body"),
         "puff.F": ((0, -0.1, 0.48), (0, -0.3, 0.48), "body"),
         "puff.B": ((0, 0.12, 0.48), (0, 0.34, 0.48), "body"),
         "arm.L": ((0.17, -0.06, 0.42), (0.24, -0.1, 0.34), "body"),
         "arm.R": ((-0.17, -0.06, 0.42), (-0.24, -0.1, 0.34), "body"),
         "bolt": ((0.0, 0.0, 0.3), (0.0, 0.0, 0.08), "body")}
    rig = SideRig(B)
    core = [sphere(0.22, C, skin, scale=(0.82, 1.02, 0.92), segs=26, rings=16)]
    rig.rigid("body", core)
    puffs = {"puff.T": [((0.0, -0.03, 0.71), 0.15), ((0.0, 0.13, 0.67), 0.14), ((0.0, -0.09, 0.66), 0.1)],
             "puff.F": [((0.0, -0.15, 0.34), 0.1), ((0.0, -0.08, 0.31), 0.1)],
             "puff.B": [((0.0, 0.25, 0.5), 0.15), ((0.0, 0.34, 0.41), 0.1), ((0.04, 0.2, 0.62), 0.1)],
             "body": [((0.08, 0.08, 0.38), 0.14), ((-0.08, 0.08, 0.38), 0.14), ((0.07, -0.08, 0.37), 0.12),
                      ((-0.07, -0.08, 0.37), 0.12), ((0.0, 0.22, 0.36), 0.11)]}
    for b, lst in puffs.items():
        for c, r in lst:
            o = sphere(r, c, skin, scale=(1.0, 0.92, 0.9), segs=20, rings=12)
            rig.rigid(b, o)
    # a paler top lit by the sun: soft highlight puffs
    for c, r in (((0.0, -0.04, 0.76), 0.08), ((0.0, 0.12, 0.72), 0.07), ((0.03, -0.17, 0.67), 0.05)):
        rig.rigid("puff.T", sphere(r, c, belly, scale=(1.0, 0.8, 0.55), segs=14, rings=8))
    # the face: scowling eyes, a wobbly frown, puffed cheeks
    face = []
    for s_ in (-1, 1):
        d = Vector((math.sin(math.radians(52)) * s_, -math.cos(math.radians(52)), 0.1)).normalized()
        ec = C + Vector((d.x * 0.18 * 0.82, d.y * 0.22, 0.04)) + d * 0.01
        face += grumpy_eye(ec, d, 0.054, white, pupil, skin, shine, s_, slant=34, cut=0.2)
        face.append(brow(ec + d * 0.02 + Vector((0, 0, 0.055)), d, 0.04, 0.013, brow_m, s_, slant=-38))
        cd = Vector((0.7 * s_, -0.66, -0.25)).normalized()
        cd = Vector((0.78 * s_, -0.58, -0.25)).normalized()
        face.append(blob(0.034, C + Vector((cd.x * 0.17, cd.y * 0.21, cd.z * 0.2 - 0.03)), cheek, (1.2, 0.3, 0.8),
                         cd, segs=10, rings=6))
    fr = [Vector((x, -0.212 + 3.0 * x * x, 0.45 + 0.012 * math.cos(x * 140) - 3.0 * x * x)) for x in
          (-0.05, -0.025, 0.0, 0.025, 0.05)]
    face.append(tube(fr, [0.006, 0.009, 0.01, 0.009, 0.006], mouth, verts=6, caps=True, name="frown"))
    rig.rigid("body", face)
    # little puff-hands
    for s_, side in ((1, "L"), (-1, "R")):
        rig.rigid("arm." + side, sphere(0.055, (0.24 * s_, -0.1, 0.34), skin, scale=(0.9, 0.9, 1.0), segs=14, rings=8),
                  sphere(0.025, (0.26 * s_, -0.15, 0.35), skin, segs=8, rings=6))
    # the lightning bolt dangling below and two raindrops
    zig = [(0.02, 0.33), (0.07, 0.23), (0.02, 0.21), (0.06, 0.05), (-0.055, 0.2), (-0.005, 0.22), (-0.04, 0.32)]
    bolt = prism([(x, z) for x, z in zig], 0.035, (0, 0, 0), bolt_m, bevel=0.008)
    bolt.data.transform(Matrix.Rotation(math.pi / 2, 4, "Z"))   # flat side to the camera (built facing -Y)
    rig.rigid("bolt", bolt)
    for p in ((0.0, -0.13, 0.25), (0.02, 0.15, 0.22)):
        drop = lathe_r([(0.0, 0.05), (0.01, 0.035), (0.022, 0.012), (0.02, -0.004), (0.0, -0.01)], drop_m, segs=12,
                       name="drop")
        drop.data.transform(Matrix.Translation(p))
        rig.rigid("body", drop)
    rig.build("cloudlet")
    finish_rig(rig, "cloudlet")

    def puff(t, l, r):
        return {"%puff.T": (t, t, t), "%puff.F": (l, l, l), "%puff.B": (r, r, r)}

    # float: 2 s; bobbing and drifting, the puffs breathing out of step, the hands paddling, the bolt swaying
    def float_p(k):
        a = 2 * math.pi * k
        return merge({"@root": (0, 0, 0.035 * math.sin(a)), "body": (3 * math.sin(a + 0.5), 0, 4 * math.sin(a)),
                      "bolt": (12 * math.sin(2 * a), 0, 10 * math.sin(a)),
                      "%bolt": (1, 1, 1 + 0.15 * math.sin(4 * a)),
                      "arm.L": (25 * math.sin(2 * a), 0, 0), "arm.R": (-25 * math.sin(2 * a), 0, 0)},
                     puff(1 + 0.05 * math.sin(a), 1 + 0.06 * math.sin(a + 2.1), 1 + 0.06 * math.sin(a + 4.2)))
    rig.action("float", {f: float_p(f / 60) for f in range(0, 61, 6)}, loop=True)

    # caught: 0.5 s; shaking with fury, the puffs squashing, fists waving, the bolt crackling
    def caught_p(k):
        a = 2 * math.pi * k
        sg = math.sin(a)
        return merge({"body": (6 * math.sin(2 * a), 10 * sg, 0), "%body": (1 + 0.05 * math.sin(2 * a), 1, 1 - 0.05 * math.sin(2 * a)),
                      "bolt": (30 * math.sin(3 * a), 0, 20 * sg), "%bolt": (1.2, 1.2, 1.2 + 0.2 * math.sin(4 * a)),
                      "arm.L": (-100 + 40 * sg, -20, 0), "arm.R": (-100 - 40 * sg, 20, 0)},
                     puff(1 + 0.08 * math.sin(2 * a), 1 + 0.1 * math.sin(2 * a + 1), 1 + 0.1 * math.sin(2 * a + 2)))
    rig.action("caught", {f: caught_p(f / 15) for f in (0, 3, 6, 9, 12, 15)}, loop=True)
    rig.save("cloudlet")


JOBS_ENEMIES = {"grub": grub, "bopper": bopper, "snapper": snapper, "cloudlet": cloudlet}


# ------------------------------------------------------------------ pickups (static props face the camera: -Y)

def flower():
    reset()
    petal_m = mat("flower_petal", (1.0, 0.42, 0.62), 0.45, coat=0.4)
    heart = mat("flower_heart", (1.0, 0.72, 0.05), 0.45, coat=0.3)
    dots = mat("flower_heart_dots", (0.85, 0.5, 0.08), 0.5)
    stem_m = mat("flower_stem", (0.3, 0.62, 0.18), 0.5, coat=0.2)
    leaf_m = mat("flower_leaf", (0.36, 0.72, 0.22), 0.5, coat=0.25)
    HC_ = Vector((0, -0.01, 0.44))
    tilt = Matrix.Rotation(math.radians(-18), 4, "X")
    # the stem, a gentle S, two leaves and a little tuft of grass at the foot
    stem = limb([(0, 0.0, 0.0), (0.02, 0.0, 0.12), (-0.015, 0.0, 0.26), (0.0, -0.005, 0.38), (0, -0.01, 0.43)],
                [0.018, 0.016, 0.015, 0.014, 0.014], stem_m, verts=8, per=3, caps=True)
    parts = [stem]
    for s_, z, ln in ((1, 0.1, 0.17), (-1, 0.18, 0.14)):
        pts, rad = [], []
        for k in range(7):
            u = k / 6
            pts.append(Vector((s_ * (0.01 + ln * u), -0.02 * math.sin(math.pi * u), z + 0.09 * u - 0.07 * u * u)))
            rad.append(0.004 + 0.032 * math.sin(math.pi * min(1.0, u * 1.1)) ** 0.8)
        lf = tube(pts, rad, leaf_m, verts=10, caps=True, name="leaf")
        for v in lf.data.vertices:   # flatten into a blade
            c = pts[min(range(7), key=lambda i: (pts[i] - v.co).length)]
            v.co.y = c.y + (v.co.y - c.y) * 0.25
        lf.data.update()
        parts.append(lf)
    for k in range(7):
        a = -0.9 + 1.8 * k / 6
        parts.append(rod((0.03 * math.sin(a), 0.0, 0.0), (0.09 * math.sin(a), -0.02 + 0.03 * (k % 2), 0.07 + 0.03 * (k % 3)),
                         0.01, leaf_m, r2=0.0, verts=5))
    root = join(parts, "flower")
    # the bloom: a domed heart with freckles; eight petals as nodes so "open" can unfold them
    hb = [ell((0, 0, 0), (0.05, 0.03, 0.05), heart, segs=18, rings=10)]
    rnd = random.Random(7)
    for k in range(9):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.0, 0.035)
        hb.append(sphere(0.0055, (r * math.cos(a), -0.028 * math.sqrt(max(0.0, 1 - (r / 0.05) ** 2)) - 0.002,
                                  r * math.sin(a)), dots, segs=6, rings=4))
    hb.append(ell((0, 0.02, 0), (0.045, 0.02, 0.045), stem_m, segs=14, rings=8))   # the green calyx behind
    for o in hb:
        o.data.transform(tilt)
    bloom = join(hb, "bloom")
    bloom.data.transform(Matrix.Translation(-HC_)) if False else None
    bloom.data.transform(Matrix.Translation((0, 0, 0)))
    bloom.location = HC_
    petals = []
    n = 8
    opens = []
    for k in range(n):
        a = 2 * math.pi * k / n + math.pi / 2
        pts = []
        for i in range(6):
            u = i / 5
            pts.append(Vector((0, -0.012 * math.sin(math.pi * u) + 0.01 * u, 0.012 + 0.12 * u)))
        pt = tube(pts, [0.016, 0.034, 0.042, 0.04, 0.03, 0.012], petal_m, verts=12, caps=True, name="petal")
        for v in pt.data.vertices:   # flat and slightly cupped
            c = Vector((0, 0, v.co.z))
            v.co.y = -0.012 * math.sin(math.pi * min(1, max(0, (v.co.z - 0.012) / 0.12))) + (v.co.y + 0.012 * math.sin(math.pi * min(1, max(0, (v.co.z - 0.012) / 0.12)))) * 0.22 + 0.4 * v.co.x ** 2
        pt.data.update()
        pt.name = pt.data.name = "petal_%d" % k
        phi = math.pi / 2 - a
        R_open = tilt.to_3x3() @ Matrix.Rotation(phi, 3, "Y")
        pt.location = HC_ + R_open @ Vector((0, 0.004, 0.02))
        pt.rotation_mode = "XYZ"

        def eul(fold, phi=phi):
            return (tilt.to_3x3() @ Matrix.Rotation(phi, 3, "Y") @ Matrix.Rotation(math.radians(fold), 3, "X")).to_euler("XYZ")
        opens.append(eul(0.0))
        keys = {}
        for f, fold, sc in ((0, 88, 0.55), (4, 60, 0.85), (7, -22, 1.08), (10, 10, 0.98), (13, -4, 1.0), (15, 0, 1.0)):
            e = eul(fold + (k % 2) * (6 if f < 8 else 0))
            keys[f] = {"rot": tuple(e), "scale": (sc, sc, sc)}
        animate(pt, "open", keys, linear=False)
        petals.append(pt)
    for pt, e in zip(petals, opens):   # the rest pose: open
        pt.rotation_euler = e
    sc = {0: {"scale": (0.4, 0.4, 0.4)}, 5: {"scale": (1.15, 1.15, 1.15)}, 9: {"scale": (0.95, 0.95, 0.95)},
          15: {"scale": (1, 1, 1)}}
    animate(bloom, "open", sc, linear=False)
    export_rest(root, "flower", [(bloom, root)] + [(p, bloom) for p in petals], rest_anim="open")


def fruit_cherry():
    reset()
    skin = mat("fruit_cherry_skin", (0.82, 0.04, 0.1), 0.18, coat=1.0)
    stem_m = mat("fruit_stem", (0.42, 0.55, 0.16), 0.6)
    leaf_m = mat("fruit_leaf", (0.3, 0.68, 0.2), 0.45, coat=0.3)
    shine = mat("fruit_shine", (1.0, 1.0, 1.0), 0.1, emit=1.5)
    parts = []
    for x, z, r in ((-0.085, 0.1, 0.1), (0.08, 0.092, 0.092)):
        c = Vector((x, 0, z))
        b = sphere(r, c, skin, scale=(1.05, 1.0, 0.95), segs=24, rings=16)
        for v in b.data.vertices:   # the dimple where the stem goes in
            d = v.co - c
            if d.z > 0:
                k = math.exp(-((d.x ** 2 + d.y ** 2) / (r * 0.25) ** 2))
                v.co.z -= 0.25 * r * k
        b.data.update()
        parts.append(b)
        parts.append(ell(c + Vector((-0.035, -r * 0.82, 0.04)), (0.022, 0.006, 0.03), shine, segs=8, rings=6,
                         roll=-30))
        top = Vector((0.0, 0.01, 0.34))
        parts.append(limb([c + Vector((0, 0, r * 0.7)), c + Vector((x * 0.3, 0, 0.14)), top], [0.008, 0.007, 0.007],
                          stem_m, verts=6, per=4, caps=True))
    lf = []
    for k in range(7):
        u = k / 6
        lf.append(Vector((0.0 + 0.16 * u, 0.0, 0.34 + 0.06 * math.sin(math.pi * u * 0.9))))
    leaf = tube(lf, [0.004 + 0.04 * math.sin(math.pi * min(1.0, u * 1.05)) ** 0.8 for u in (k / 6 for k in range(7))],
                leaf_m, verts=10, caps=True, name="leaf")
    for v in leaf.data.vertices:
        v.co.y *= 0.25
    leaf.data.update()
    parts.append(leaf)
    simple_export(parts, "fruit_cherry")


def export_rest(root, name, children, rest_anim=None):
    """export_anim, then (rest_anim given) sets every node that animation moves to the animation's last frame, so
    that pose is the one shown when nothing plays (the exporter writes the first frame's pose)."""
    export_anim(root, name, children)
    if rest_anim:
        rest_to_last(os.path.join(K.OUT, name + ".glb"), rest_anim)


def rest_to_last(path, anim):
    """Rewrites a .glb's node transforms to the last keyframe of the animation `anim`."""
    import json, struct
    data = open(path, "rb").read()
    jlen = struct.unpack("<I", data[12:16])[0]
    j = json.loads(data[20:20 + jlen])
    rest = data[20 + jlen:]
    blen = struct.unpack("<I", rest[:4])[0]
    binc = rest[8:8 + blen]
    size = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}
    for a in j["animations"]:
        if a["name"] != anim:
            continue
        for ch in a["channels"]:
            acc = j["accessors"][a["samplers"][ch["sampler"]]["output"]]
            bv = j["bufferViews"][acc["bufferView"]]
            n = size[acc["type"]]
            off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0) + (acc["count"] - 1) * 4 * n
            last = list(struct.unpack("<%df" % n, binc[off:off + 4 * n]))
            j["nodes"][ch["target"]["node"]][ch["target"]["path"]] = last
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = data[:12] + struct.pack("<I", len(js)) + b"JSON" + js + rest
    out = out[:8] + struct.pack("<I", len(out)) + out[12:]
    open(path, "wb").write(out)


def simple_export(parts, name):
    export(join(parts, name), name)


def fruit_pear():
    reset()
    skin = mat("fruit_pear_skin", (0.78, 0.82, 0.16), 0.4, coat=0.5)
    stem_m = mat("fruit_stem", (0.42, 0.3, 0.14), 0.6)
    leaf_m = mat("fruit_leaf", (0.3, 0.68, 0.2), 0.45, coat=0.3)
    shine = mat("fruit_shine", (1.0, 1.0, 1.0), 0.1, emit=1.5)
    prof = [(0.0, 0.33), (0.03, 0.325), (0.05, 0.3), (0.062, 0.26), (0.08, 0.21), (0.12, 0.15), (0.145, 0.1),
            (0.14, 0.05), (0.11, 0.015), (0.06, 0.0), (0.0, 0.0)]
    from blastyard_bombers import smooth_path
    sp = [(v.x, v.y) for v in smooth_path([Vector((r, z, 0)) for r, z in prof[1:-1]], 3)]
    body = lathe_r([(0.0, 0.335)] + sp + [(0.0, -0.002)], skin, segs=28, name="pear", smooth=60)
    parts = [body, ell((-0.06, -0.12, 0.17), (0.02, 0.006, 0.035), shine, segs=8, rings=6, roll=20),
             limb([(0, 0, 0.32), (0.01, 0, 0.37), (0.035, 0.0, 0.4)], [0.01, 0.009, 0.008], stem_m, verts=6, per=3,
                  caps=True)]
    lf = [Vector((0.02 + 0.13 * k / 6, 0.0, 0.37 + 0.05 * math.sin(math.pi * k / 6))) for k in range(7)]
    leaf = tube(lf, [0.004 + 0.035 * math.sin(math.pi * min(1.0, u * 1.05)) ** 0.8 for u in (k / 6 for k in range(7))],
                leaf_m, verts=10, caps=True, name="leaf")
    for v in leaf.data.vertices:
        v.co.y *= 0.25
    leaf.data.update()
    parts.append(leaf)
    simple_export(parts, "fruit_pear")


def fruit_grapes():
    reset()
    skin = mat("fruit_grape_skin", (0.42, 0.14, 0.62), 0.25, coat=0.8)
    skin2 = mat("fruit_grape_skin_dark", (0.3, 0.08, 0.48), 0.25, coat=0.8)
    stem_m = mat("fruit_stem", (0.42, 0.3, 0.14), 0.6)
    leaf_m = mat("fruit_leaf", (0.3, 0.68, 0.2), 0.45, coat=0.3)
    shine = mat("fruit_shine", (1.0, 1.0, 1.0), 0.1, emit=1.5)
    parts = []
    rnd = random.Random(5)
    rows = [(0.29, 4, 0.11), (0.23, 5, 0.1), (0.17, 4, 0.08), (0.115, 3, 0.06), (0.065, 2, 0.035), (0.03, 1, 0.0)]
    for i, (z, n, r) in enumerate(rows):
        for k in range(n):
            a = 2 * math.pi * k / n + i * 0.6
            c = Vector((r * math.cos(a), r * math.sin(a) * 0.8, z))
            parts.append(sphere(0.045, c, skin if (k + i) % 3 else skin2, scale=(1, 1, 1.08), segs=14, rings=10))
            if c.y < 0:
                parts.append(sphere(0.009, c + Vector((-0.016, -0.04, 0.018)), shine, segs=6, rings=4))
    parts.append(limb([(0, 0, 0.3), (0.01, 0, 0.36), (0.03, 0, 0.4)], [0.012, 0.011, 0.01], stem_m, verts=6, per=3,
                      caps=True))
    # a vine leaf with three lobes and a curly tendril
    for k, ang in enumerate((-40, 0, 40)):
        a = math.radians(ang)
        d = Vector((math.sin(a) * 0.6 + 0.6, 0.0, math.cos(a) * 0.6))
        pts = [Vector((0.03, 0.01, 0.37)) + d * 0.15 * u for u in (0, 0.33, 0.66, 1.0)]
        lob = tube(pts, [0.006, 0.04, 0.035, 0.006], leaf_m, verts=10, caps=True, name="lobe")
        for v in lob.data.vertices:
            v.co.y = 0.01 + (v.co.y - 0.01) * 0.25
        lob.data.update()
        parts.append(lob)
    tend = [Vector((-0.01, 0.0, 0.36)) + Vector((-0.03 * u - 0.025 * math.sin(6 * u), 0, 0.04 * u + 0.025 * math.cos(6 * u) - 0.025))
            for u in (k / 10 for k in range(11))]
    parts.append(tube(tend, [0.004] * 11, stem_m, verts=5, caps=True, name="tendril"))
    simple_export(parts, "fruit_grapes")


def cake():
    reset()
    sponge = mat("cake_sponge", (0.98, 0.78, 0.45), 0.7)
    cream = mat("cake_cream", (1.0, 0.97, 0.92), 0.35, coat=0.3)
    icing = mat("cake_icing", (1.0, 0.62, 0.75), 0.3, coat=0.6)
    berry = mat("cake_berry", (0.9, 0.08, 0.14), 0.25, coat=0.8)
    seed = mat("cake_berry_seed", (1.0, 0.9, 0.4), 0.5)
    leaf_m = mat("fruit_leaf", (0.3, 0.68, 0.2), 0.45, coat=0.3)
    plate = mat("cake_plate", (0.85, 0.92, 1.0), 0.2, coat=0.8)
    parts = [cyl(0.21, 0.02, (0, 0, 0.01), plate, verts=40, bevel=0.006, segs=2),
             cyl(0.17, 0.1, (0, 0, 0.07), sponge, verts=40, bevel=0.01, segs=2),
             cyl(0.172, 0.022, (0, 0, 0.13), cream, verts=40, bevel=0.008, segs=2),
             cyl(0.17, 0.08, (0, 0, 0.18), sponge, verts=40, bevel=0.01, segs=2)]
    # the pink icing on top, dripping over the edge
    ice = lathe_r([(0.0, 0.245), (0.15, 0.243), (0.175, 0.232), (0.178, 0.218), (0.0, 0.218)], icing, segs=48,
                  name="icing", smooth=60)
    parts.append(ice)
    for k in range(14):
        a = 2 * math.pi * k / 14 + 0.1
        ln = 0.03 + 0.03 * ((k * 7) % 5) / 4
        p0 = Vector((0.176 * math.cos(a), 0.176 * math.sin(a), 0.225))
        parts.append(tube([p0, p0 + Vector((0, 0, -ln * 0.6)), p0 + Vector((0, 0, -ln))], [0.016, 0.014, 0.012], icing,
                          verts=8, caps=True, name="drip"))
    # cream swirls round the top and three strawberries
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((0.13 * math.cos(a), 0.13 * math.sin(a), 0.255))
        parts.append(lathe_r([(0.0, 0.05), (0.012, 0.04), (0.026, 0.02), (0.03, 0.005), (0.0, 0.0)], cream, segs=10,
                             radial=lambda kk, z: 1.0 + 0.12 * (kk % 2), name="swirl", smooth=30, center=(c.x, c.y, 0)))
        parts[-1].data.transform(Matrix.Translation((0, 0, c.z - 0.005)))
    for p in ((0.0, -0.02, 0.3), (-0.06, 0.04, 0.29), (0.065, 0.035, 0.29)):
        b = lathe_r([(0.0, 0.0), (0.026, 0.012), (0.034, 0.035), (0.026, 0.055), (0.0, 0.06)], berry, segs=14,
                    name="berry", smooth=60)
        b.data.transform(Matrix.Translation(Vector(p) + Vector((0, 0, -0.03))) @ Matrix.Rotation(math.pi, 4, "X")
                         @ Matrix.Translation((0, 0, -0.06)))
        parts.append(b)
        for k in range(6):
            a = 2 * math.pi * k / 6
            parts.append(sphere(0.0035, Vector(p) + Vector((0.026 * math.cos(a), 0.026 * math.sin(a), -0.005)), seed,
                                segs=4, rings=3))
        for k in range(4):
            a = 2 * math.pi * k / 4
            parts.append(rod(Vector(p) + Vector((0, 0, 0.028)), Vector(p) + Vector((0.025 * math.cos(a), 0.025 * math.sin(a), 0.04)),
                             0.008, leaf_m, r2=0.002, verts=4))
    simple_export(parts, "cake")


def crystal():
    reset()
    glow = mat("crystal_glow", (0.85, 0.35, 1.0), 0.08, coat=1.0, emit=1.4, alpha=0.82, emit_color=(0.8, 0.3, 1.0))
    core = mat("crystal_core_glow", (1.0, 0.85, 1.0), 0.1, emit=3.5)
    rock = mat("crystal_rock", (0.45, 0.4, 0.5), 0.8)
    parts = [lumpy(0.09, (0, 0, 0.03), rock, 11, amount=0.25, scale=(1.4, 1.0, 0.5), smooth=0)]

    def gem(base, axis, r, h, m, n=6):
        g = lathe_r([(0.0, h), (r * 0.6, h * 0.86), (r, h * 0.65), (r, 0.0), (0.0, -0.01)], m, segs=n, name="gem",
                    smooth=0)
        q = Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized())
        g.data.transform(Matrix.Translation(Vector(base)) @ q.to_matrix().to_4x4())
        return g
    parts += [gem((0, 0, 0.02), (0, 0, 1), 0.075, 0.38, glow), gem((0.07, 0.0, 0.02), (0.5, -0.1, 1), 0.045, 0.22, glow),
              gem((-0.07, 0.01, 0.02), (-0.55, 0.1, 1), 0.04, 0.18, glow),
              gem((0, -0.0, 0.05), (0, 0, 1), 0.03, 0.27, core, n=6)]
    simple_export(parts, "crystal")


def bomb_bonus():
    reset()
    shell = mat("bomb_shell", (0.1, 0.1, 0.16), 0.25, coat=0.9)
    cap = mat("bomb_cap", (0.95, 0.72, 0.25), 0.3, metal=0.8)
    fuse = mat("bomb_fuse", (0.85, 0.75, 0.55), 0.8)
    star_m = mat("bomb_star", (1.0, 0.85, 0.2), 0.35, coat=0.4)
    spark = mat("bomb_spark_glow", (1.0, 0.8, 0.3), 0.3, emit=6.0, emit_color=(1.0, 0.6, 0.15))
    shine = mat("fruit_shine", (1.0, 1.0, 1.0), 0.1, emit=1.5)
    C_ = Vector((0, 0, 0.16))
    parts = [sphere(0.16, C_, shell, segs=28, rings=18),
             ell(C_ + Vector((-0.06, -0.135, 0.07)), (0.03, 0.008, 0.05), shine, segs=8, rings=6, roll=35),
             cyl(0.055, 0.05, C_ + Vector((0, 0, 0.16)), cap, verts=20, bevel=0.008, segs=2),
             torus(0.057, 0.01, C_ + Vector((0, 0, 0.14)), cap, verts=20, minor=6)]
    st = star_mesh(0.07, 0.032, 0.012, star_m, name="emblem")
    st.data.transform(Matrix.Translation(C_ + Vector((0.0, -0.162, 0.0))))
    parts.append(st)
    fp = [C_ + Vector((0, 0, 0.18)), C_ + Vector((0.02, 0, 0.23)), C_ + Vector((0.06, 0, 0.255)), C_ + Vector((0.1, 0, 0.25))]
    parts.append(limb(fp, [0.012, 0.011, 0.01, 0.009], fuse, verts=8, per=3, caps=True))
    body = join(parts, "bomb_bonus")
    sp = [ico(0.022, fp[-1] + Vector((0.008, 0, 0.004)), spark, sub=1)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = Vector((math.cos(a), 0, math.sin(a)))
        sp.append(rod(fp[-1] + d * 0.02, fp[-1] + d * 0.05, 0.005, spark, r2=0.0, verts=4))
    spk = join(sp, "spark", pivot=fp[-1])
    animate(spk, "fizz", {0: {"scale": (1, 1, 1), "rot": (0, 0.0, 0)}, 3: {"scale": (1.35, 1.35, 1.35), "rot": (0, 0.5, 0)},
                          6: {"scale": (0.8, 0.8, 0.8), "rot": (0, 1.0, 0)}, 9: {"scale": (1.2, 1.2, 1.2), "rot": (0, 1.5, 0)},
                          12: {"scale": (1, 1, 1), "rot": (0, 2.0944, 0)}})
    export_rest(body, "bomb_bonus", [(spk, body)])


def letter_bubble():
    reset()
    glass = mat("bubble_glass", (0.75, 0.9, 1.0), 0.04, coat=1.0, emit=0.25, alpha=0.32, emit_color=(0.6, 0.8, 1.0))
    rim = mat("bubble_rim_glow", (1.0, 0.75, 0.95), 0.1, emit=1.2, alpha=0.55, emit_color=(0.9, 0.6, 1.0))
    shine = mat("bubble_shine_glow", (1.0, 1.0, 1.0), 0.05, emit=3.0)
    R_ = 0.3
    parts = [sphere(R_, (0, 0, 0), glass, segs=36, rings=24)]
    # a thin iridescent band round the silhouette (as seen from the camera)
    parts.append(torus(R_ * 0.985, 0.012, (0, 0.0, 0), rim, rot=(math.pi / 2, 0, 0), verts=48, minor=6))
    # a big curved window highlight top-left, a small one bottom-right
    arc = [Vector((R_ * 0.8 * math.cos(a), -R_ * 0.55, R_ * 0.8 * math.sin(a))) for a in
           (math.radians(d) for d in (110, 120, 130, 140, 150, 160))]
    for v in arc:
        v.y = -math.sqrt(max(0.0, R_ ** 2 - v.x ** 2 - v.z ** 2)) - 0.004
    parts.append(tube(arc, [0.006, 0.014, 0.018, 0.018, 0.014, 0.006], shine, verts=6, caps=True, name="glint"))
    parts.append(sphere(0.022, (-R_ * 0.35, -R_ * 0.86, R_ * 0.33), shine, segs=8, rings=6))
    arc2 = [Vector((R_ * 0.78 * math.cos(a), 0, R_ * 0.78 * math.sin(a))) for a in
            (math.radians(d) for d in (-60, -50, -40, -30))]
    for v in arc2:
        v.y = -math.sqrt(max(0.0, R_ ** 2 - v.x ** 2 - v.z ** 2)) - 0.004
    parts.append(tube(arc2, [0.004, 0.008, 0.008, 0.004], shine, verts=6, caps=True, name="glint2"))
    simple_export(parts, "letter_bubble")


# ------------------------------------------------------------------ level pieces (1 m tiles, origin bottom centre)

def block_moss(parts, seed, moss, flower_m, heart_m, w=1.0, top=1.0):
    """A moss cushion over the top of a block, lipping over the front edge, with a few tiny flowers."""
    rnd = random.Random(seed)
    nx, ny = 22, 10
    grid = []
    for i in range(ny + 1):
        y = -0.5 + i / ny
        row = []
        for j in range(nx + 1):
            x = -w / 2 + w * j / nx
            h = 0.035 + 0.02 * math.sin(x * 9 + seed) * math.sin(y * 7 + seed * 2) + rnd.uniform(-0.006, 0.006)
            row.append(Vector((x, y, top + h)))
        grid.append(row)
    cushion = sheet(grid, moss, "moss", thick=0.0, smooth=70)
    parts.append(cushion)
    # the lip draping over the front edge: lumps along the edge, some hanging lower
    for k in range(13):
        x = -w / 2 + 0.04 + (w - 0.08) * k / 12
        drop = 0.03 + 0.05 * rnd.random() ** 2
        parts.append(lumpy(0.05, (x, -0.49, top - drop * 0.5 + 0.01), moss, seed * 31 + k, amount=0.3,
                           scale=(1.1, 0.6, 0.8 + drop * 6), smooth=40))
    for k in range(3):   # tiny flowers
        x = rnd.uniform(-0.38, 0.38)
        y = rnd.uniform(-0.42, 0.0)
        parts.append(daisy(Vector((x, y, top + 0.06)), (0, -0.4, 1), 0.04 + 0.01 * rnd.random(), flower_m, heart_m,
                           n=6, name="mossflower"))
        parts.append(rod((x, y + 0.01, top + 0.02), (x, y + 0.01, top + 0.06), 0.005, moss, verts=4))


def block():
    reset()
    stone = mat("block_stone", (0.72, 0.64, 0.56), 0.85)
    dark = mat("block_stone_dark", (0.5, 0.43, 0.38), 0.9)
    moss = mat("block_moss", (0.33, 0.58, 0.16), 0.9)
    fl = mat("block_flower", (1.0, 0.96, 0.98), 0.5)
    he = mat("block_flower_heart", (1.0, 0.8, 0.2), 0.5)
    parts = []
    # two courses of carved blocks on the front, staggered, with recessed joints behind them
    parts.append(box((0.98, 0.98, 0.98), (0, 0, 0.5), dark, bevel=0.02))
    rnd = random.Random(3)
    courses = [(0.0, 0.5, [(-0.5, 0.1), (0.1, 0.5)]), (0.5, 1.0, [(-0.5, -0.2), (-0.2, 0.5)])]
    for z0, z1, spans in courses:
        for x0, x1 in spans:
            c = ((x0 + x1) / 2, -0.005, (z0 + z1) / 2)
            sz = (x1 - x0 - 0.035, 1.0, z1 - z0 - 0.035)
            b = box(sz, c, stone, bevel=0.035, segs=3)
            for v in b.data.vertices:   # hand-cut: a slight random bulge on the front
                if v.co.y < -0.4:
                    v.co.y -= 0.008 * math.sin(v.co.x * 11 + z0 * 5) * math.sin(v.co.z * 9)
            b.data.update()
            parts.append(b)
    # a carved spiral rosette on the lower-left stone
    sp = [Vector((-0.2 + 0.11 * (t / 12) * math.cos(t), -0.507, 0.25 + 0.11 * (t / 12) * math.sin(t))) for t in
          (k * 0.5 for k in range(25))]
    parts.append(tube(sp, [0.008] * len(sp), dark, verts=6, caps=True, name="spiral"))
    block_moss(parts, 4, moss, fl, he)
    simple_export(parts, "block")


def block_b():
    reset()
    wood = mat("crate_wood", (0.78, 0.52, 0.28), 0.75)
    frame = mat("crate_frame", (0.52, 0.32, 0.16), 0.7)
    nail = mat("crate_nail", (0.75, 0.72, 0.68), 0.3, metal=0.9)
    parts = [box((0.96, 0.96, 0.96), (0, 0, 0.5), wood, bevel=0.01)]
    for k in range(4):   # planks on the front and back
        z = 0.125 + 0.25 * k
        for y in (-0.485, 0.485):
            b = box((0.86, 0.04, 0.225), (0, y, z), wood, bevel=0.015, segs=2)
            parts.append(b)
    # the frame: a border and a diagonal brace on the front and back, nail heads
    for y in (-0.5, 0.5):
        for (x, z, sx, sz) in ((0, 0.04, 1.0, 0.08), (0, 0.96, 1.0, 0.08), (-0.46, 0.5, 0.08, 1.0), (0.46, 0.5, 0.08, 1.0)):
            parts.append(box((sx, 0.06, sz), (x, y, z), frame, bevel=0.012))
        br = box((1.12, 0.05, 0.1), (0, y, 0.5), frame, rot=(0, math.radians(-40 if y < 0 else 40), 0), bevel=0.012)
        parts.append(br)
        for (x, z) in ((-0.46, 0.04), (0.46, 0.04), (-0.46, 0.96), (0.46, 0.96)):
            parts.append(sphere(0.014, (x, y * 1.065, z), nail, scale=(1, 0.5, 1), segs=8, rings=4))
    for x in (-0.47, 0.47):   # side frames (inside the tile, so neighbours never overlap)
        for (y, z, sy, sz) in ((0, 0.04, 0.94, 0.08), (0, 0.96, 0.94, 0.08)):
            parts.append(box((0.06, sy, sz), (x, y, z), frame, bevel=0.012))
    simple_export(parts, "block_b")


def block_c():
    reset()
    ice = mat("ice_glass", (0.62, 0.86, 1.0), 0.05, coat=1.0, emit=0.15, alpha=0.62, emit_color=(0.5, 0.8, 1.0))
    core = mat("ice_core_glow", (0.75, 0.92, 1.0), 0.2, emit=0.9, alpha=0.5)
    frost = mat("ice_frost", (0.94, 0.98, 1.0), 0.6)
    parts = [box((0.98, 0.98, 0.98), (0, 0, 0.5), ice, bevel=0.05, segs=2, smooth=0)]
    # crystal shards frozen inside, catching the light
    rnd = random.Random(9)
    for k in range(5):
        c = Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.25, 0.25), rnd.uniform(0.2, 0.75)))
        g = lathe_r([(0.0, 0.16), (0.05, 0.08), (0.05, -0.08), (0.0, -0.16)], core, segs=6, name="shard", smooth=0)
        g.data.transform(Matrix.Translation(c) @ Matrix.Rotation(rnd.uniform(-1, 1), 4, "Y")
                         @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, "X"))
        parts.append(g)
    # frost and icicles along the top front edge, a snowy cap
    nx, ny = 20, 8
    grid = [[Vector((-0.5 + j / nx, -0.5 + i / ny, 1.0 + 0.02 + 0.012 * math.sin(j * 1.7 + i))) for j in range(nx + 1)]
            for i in range(ny + 1)]
    parts.append(sheet(grid, frost, "snow", smooth=70))
    for k in range(9):
        x = -0.44 + 0.88 * k / 8 + rnd.uniform(-0.03, 0.03)
        ln = rnd.uniform(0.06, 0.16)
        parts.append(rod((x, -0.5, 1.0), (x, -0.505, 1.0 - ln), 0.022, ice, r2=0.0, verts=6))
    simple_export(parts, "block_c")


def ladder():
    reset()
    wood = mat("ladder_wood", (0.66, 0.44, 0.24), 0.75)
    rope = mat("ladder_rope", (0.86, 0.76, 0.52), 0.85)
    parts = []
    for s_ in (-1, 1):
        x = 0.32 * s_
        pts = [Vector((x + 0.006 * math.sin(z * 9 + s_), 0.0, z)) for z in (0.0, 0.25, 0.5, 0.75, 1.0)]
        parts.append(tube(pts, [0.034] * 5, wood, verts=10, caps=False, name="rail"))
    for k in range(4):
        z = 0.125 + 0.25 * k
        parts.append(rod((-0.35, -0.0, z), (0.35, 0.0, z + 0.004 * (k % 2)), 0.024, wood, verts=8))
        for s_ in (-1, 1):   # rope lashings
            parts.append(torus(0.037, 0.008, (0.32 * s_, 0, z + 0.016), rope, verts=12, minor=4))
            parts.append(torus(0.037, 0.008, (0.32 * s_, 0, z - 0.016), rope, verts=12, minor=4))
    simple_export(parts, "ladder")


def magic_ladder():
    reset()
    cols = [(1.0, 0.12, 0.35), (1.0, 0.7, 0.05), (0.1, 0.95, 0.35), (0.1, 0.55, 1.0), (0.6, 0.2, 1.0)]
    mats = [mat("magic_band%d_glow" % i, c, 0.2, emit=2.6, alpha=0.75, emit_color=c) for i, c in enumerate(cols)]
    rung_m = mat("magic_rung_glow", (1.0, 0.97, 0.9), 0.2, emit=3.0, alpha=0.75)
    spark_m = mat("magic_spark_glow", (1.0, 1.0, 1.0), 0.1, emit=6.0)
    parts = []
    for s_ in (-1, 1):   # each rail a ribbon of five rainbow bands
        for i, m in enumerate(mats):
            x = 0.32 * s_ + (i - 2) * 0.014 * s_
            pts = [Vector((x + 0.004 * math.sin(z * 2 * math.pi + i), 0.0, z)) for z in (0.0, 0.25, 0.5, 0.75, 1.0)]
            parts.append(tube(pts, [0.009] * 5, m, verts=6, caps=False, name="band"))
    for k in range(4):
        z = 0.125 + 0.25 * k
        parts.append(rod((-0.3, 0.0, z), (0.3, 0.0, z), 0.018, rung_m, verts=8))
        parts.append(rod((-0.3, 0.0, z), (0.3, 0.0, z), 0.03, mats[k % 5], verts=8))
    rnd = random.Random(12)
    for k in range(6):
        p = Vector((rnd.uniform(-0.28, 0.28), rnd.uniform(-0.04, 0.04), rnd.uniform(0.05, 0.95)))
        st = star_mesh(0.022, 0.009, 0.006, spark_m, name="spark")
        st.data.transform(Matrix.Translation(p))
        parts.append(st)
    simple_export(parts, "magic_ladder")


def door():
    reset()
    stone = mat("door_stone", (0.7, 0.64, 0.58), 0.85)
    dark = mat("door_stone_dark", (0.5, 0.44, 0.4), 0.9)
    wood = mat("door_wood", (0.62, 0.36, 0.2), 0.7, coat=0.2)
    plank = mat("door_wood_dark", (0.46, 0.25, 0.13), 0.75)
    metal = mat("door_metal", (0.95, 0.75, 0.3), 0.3, metal=0.85)
    vine = mat("door_vine", (0.3, 0.6, 0.2), 0.6)
    fl = mat("door_flower", (1.0, 0.55, 0.75), 0.5)
    he = mat("door_flower_heart", (1.0, 0.85, 0.25), 0.5)
    portal = mat("door_portal_glow", (1.0, 0.86, 0.55), 0.3, emit=1.6, emit_color=(1.0, 0.78, 0.4))
    W, H0 = 0.5, 1.2           # opening half width, height of the straight sides (arch above, top 1.7)
    parts = []
    # the frame: two pillars and a round arch of voussoirs, a keystone with a star
    for s_ in (-1, 1):
        for k in range(4):
            z = 0.15 + 0.3 * k
            parts.append(box((0.22, 0.34, 0.28), (s_ * (W + 0.11), 0.0, z), stone if k % 2 == 0 else dark, bevel=0.03))
    n = 9
    for k in range(n):
        a0 = math.pi * k / n
        a1 = math.pi * (k + 1) / n
        poly = [((W) * math.cos(a0), H0 + W * math.sin(a0)), ((W + 0.22) * math.cos(a0), H0 + (W + 0.22) * math.sin(a0)),
                ((W + 0.22) * math.cos(a1), H0 + (W + 0.22) * math.sin(a1)), (W * math.cos(a1), H0 + W * math.sin(a1))]
        poly = poly[::-1] if True else poly
        parts.append(prism(poly, 0.34, (0, 0, 0), stone if k % 2 else dark, bevel=0.02))
    ks = star_mesh(0.07, 0.03, 0.02, metal, name="keystar")
    ks.data.transform(Matrix.Translation((0, -0.18, H0 + W + 0.11)))
    parts.append(ks)
    parts.append(box((1.5, 0.4, 0.06), (0, 0.0, 0.03), dark, bevel=0.02))   # the threshold
    # vines up the pillars and round the arch, with flowers
    rnd = random.Random(21)
    vp = []
    for k in range(25):
        u = k / 24
        a = math.pi * (1 - u)
        if u < 0.25:
            p = Vector((-(W + 0.2), -0.18, 0.1 + (H0 - 0.1) * u / 0.25))
        elif u > 0.75:
            p = Vector(((W + 0.2), -0.18, 0.1 + (H0 - 0.1) * (1 - u) / 0.25))
        else:
            t = (u - 0.25) / 0.5
            a = math.pi * (1 - t)
            p = Vector(((W + 0.2) * math.cos(a), -0.18, H0 + (W + 0.2) * math.sin(a)))
        p += Vector((0.02 * math.sin(k * 1.3), 0, 0.02 * math.cos(k * 1.7)))
        vp.append(p)
    parts.append(tube(vp, [0.014] * len(vp), vine, verts=6, caps=True, name="vine"))
    for k in range(1, 24, 2):
        p = vp[k]
        lf = ell((0, 0, 0), (0.04, 0.008, 0.022), vine, segs=8, rings=5)
        lf.data.transform(Matrix.Translation(p + Vector((0, -0.01, 0))) @ Matrix.Rotation(rnd.uniform(0, math.pi), 4, "Y"))
        parts.append(lf)
    for k in (3, 8, 12, 16, 21):
        parts.append(daisy(vp[k] + Vector((0, -0.03, 0)), (0, -1, 0.2), 0.055, fl, he, n=6, name="vineflower"))
    # the warm glow beyond the doors (seen when they open)
    glow = []
    for k in range(17):
        a = math.pi * k / 16
        glow.append((W * math.cos(a), H0 + W * math.sin(a)))
    glow = [(W, 0.06)] + glow + [(-W, 0.06)]
    parts.append(prism(glow[::-1], 0.02, (0, 0.1, 0), portal, bevel=0.0))
    frame = join(parts, "door")
    # the two leaves: planks with a rounded top, metal straps, a ring handle and a flower emblem
    leaves = []
    for s_, name in ((-1, "door_l"), (1, "door_r")):
        lp = []
        out = []
        for k in range(9):   # the leaf outline: from the hinge edge up and round to the middle
            a = math.pi / 2 * k / 8
            out.append((s_ * (W - 0.005) * math.sin(a) if False else s_ * W * math.cos(a) * 0.99, H0 + W * math.sin(a) * 0.99))
        poly = [(0.0 * s_, 0.07), (s_ * W * 0.99, 0.07)] + out
        if s_ < 0:
            poly = poly[::-1]
        leaf_o = prism(poly, 0.06, (0, -0.0, 0), wood, bevel=0.01)
        lp.append(leaf_o)
        for k in range(1, 4):   # plank grooves
            x = s_ * W * k / 4
            ztop = H0 + math.sqrt(max(0.0, W ** 2 - x ** 2)) - 0.03
            lp.append(box((0.012, 0.01, ztop - 0.1), (x, -0.032, 0.07 + (ztop - 0.1) / 2 + 0.01), plank, bevel=0.003))
        for z in (0.3, 0.95):   # metal straps
            lp.append(box((W * 0.9, 0.014, 0.05), (s_ * W * 0.5, -0.036, z), metal, bevel=0.006))
            for x in (0.12, 0.28, 0.42):
                lp.append(sphere(0.011, (s_ * x, -0.045, z), metal, segs=6, rings=4))
        lp.append(torus(0.04, 0.008, (s_ * 0.09, -0.05, 0.68), metal, rot=(math.pi / 2, 0, 0), verts=14, minor=4))
        lp.append(sphere(0.016, (s_ * 0.09, -0.04, 0.72), metal, segs=8, rings=6))
        lp.append(daisy(Vector((s_ * 0.22, -0.045, 1.35)), (0, -1, 0), 0.08, fl, he, n=8, name="emblem"))
        hinge_x = s_ * W
        leaf = join(lp, name, pivot=(hinge_x, 0, 0))
        leaves.append(leaf)
    # open: 0.8 s; a rattle, then both leaves swing out towards the camera (100 degrees), a small bounce
    for leaf, s_ in zip(leaves, (-1, 1)):
        ang = lambda d, s_=s_: (0, 0, math.radians(d) * s_)   # both leaves swing out towards the camera
        animate(leaf, "open", {0: {"rot": ang(0)}, 3: {"rot": ang(-3)}, 5: {"rot": ang(2)}, 7: {"rot": ang(0)},
                               16: {"rot": ang(85)}, 20: {"rot": ang(108)}, 22: {"rot": ang(100)}, 24: {"rot": ang(102)}},
                linear=False)
    export_rest(frame, "door", [(l, frame) for l in leaves])


JOBS_PROPS = {"flower": flower, "fruit_cherry": fruit_cherry, "fruit_pear": fruit_pear, "fruit_grapes": fruit_grapes,
              "cake": cake, "crystal": crystal, "bomb_bonus": bomb_bonus, "letter_bubble": letter_bubble,
              "block": block, "block_b": block_b, "block_c": block_c, "ladder": ladder, "magic_ladder": magic_ladder,
              "door": door}


JOBS = {"fairy": fairy}
JOBS.update(JOBS_ENEMIES)
JOBS.update(JOBS_PROPS)

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
