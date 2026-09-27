"""Henhouse Heist (game 20) models: the farmhand (on the shared humanoid rig), the hens, the giant goose and its cage,
the eggs, grain and lifts, the brick platforms and ladders, and the golden-hour farmyard backdrop.
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/henhouse_models.py -- godot/games/henhouse/art/models [name ...]
Helpers come from humanoid.py (the 26-bone rig, smooth skin, IK poses, gait), relic_models.py (export_humanoid,
cycle, yawed, slim), blastyard_models.py (mat, box, cyl, ...), blastyard_bombers.py and hopline_models.py (Rig,
TurnRig for the birds), prism_models.py and mossfolk_models.py. 30 fps.

Axes: Blender Z up, the camera side is -Y; in Godot +X stays +X, Blender +Z is +Y (up), Blender -Y is +Z (towards the
camera). 1 tile = 0.5 units; the level pieces, items, hens, goose and cage are at game size (node scale 1); only the
farmhand is built at 1.7 and scaled by the game. Characters face Godot +X, turned towards the camera (farmhand 28
degrees, birds 20) so faces read; mirror with scale.x = -1. Origins at the feet / base centre unless noted.
Suggested depths (Godot z): bricks at 0 (front face +0.25), ladders +0.30 (in front of the bricks, so they cross
platforms), actors and items +0.5 (a climbing farmhand then stands 0.2 in front of the rungs), backdrop well behind.

farmhand.glb  armature "farmhand_rig" (26 bones, see humanoid.py) with the skinned mesh "farmhand": a young farmhand,
              ginger hair, green flat cap, yellow shirt with rolled sleeves, red polka-dot neckerchief, blue dungarees
              with brass buttons, green wellies. 1.70 tall at node scale 1: scale the node by 1.1 / 1.7 = 0.647 for 2.2
              tiles. Materials farmhand_skin, _cheek, _eye_white, _iris, _hair, _lips, _shirt, _shirt_dark, _denim,
              _denim_dark, _stitch, _welly, _welly_dark, _sole, _brass, _cap, _cap_dark, _scarf, _scarf_dot.
              Animations (loops marked *):
                idle*   2.4 s, breathing, a glance at the camera
                walk*   0.53 s (16 frames), a bouncy walk, one stride (two steps) per cycle, no root travel:
                        0.93 game units per cycle at 0.647 scale (1.75 units/s = 3.5 tiles/s at speed_scale 1)
                climb*  0.53 s, his back to the camera, hands and feet alternating on the rungs, in place: 0.50 game
                        units (one ladder segment) per cycle (0.94 units/s)
                jump    0.47 s, crouch, spring, knees tucked, arms up (holds the last frame; blend to fall)
                fall*   0.4 s, arms windmilling, legs pedalling
                die     1.4 s, a startled hop, a wobble, topples on his back, a bounce, lies spread out (holds; the body
                        lies from about x = -0.9 to +0.7 at scale 1)
                cheer*  1 s, two hops with both fists pumping
hen.glb       armature "hen_rig" (root, body, neck, head, tail, wing.L/R, thigh/shin/foot.L/R), mesh "hen": a plump
              hen 0.86 long (beak to tail), 0.81 tall to the comb. Materials hen_feather (recolour per stage: white by
              default, brown about (0.62, 0.32, 0.12)), hen_speckle (dots over the back, breast and wings: a slightly
              darker tint by default; set it near black on a grey or white feather for the speckled hen, or equal to
              the feather to hide it), hen_comb, hen_beak, hen_leg, hen_eye, hen_iris, hen_eye_shine (emissive).
              Animations, all loops: walk 0.6 s (a waddle with the head bob; 0.44 units per cycle = 0.73 units/s,
              1.5 tiles/s at speed_scale 1), climb 0.53 s (turns to face the camera and flaps hard, stepping up in place:
              any climb speed reads; put it on the ladder line), peck 1 s (three pecks at the ground in front, a
              scratch, a look round), idle 2 s (looks about, tail flicks).
goose.glb     armature "goose_rig" (root, body, neck1, neck2, head, jaw, tail, wing.L/R, tip.L/R, thigh/shin/foot.L/R),
              mesh "goose": a giant grumpy white goose, 1.80 tall standing (head top), heavy lids and low grey brows,
              a knobbed orange beak. The rest pose has the wings spread (2.7 span): every action poses them. Materials
              goose_feather, goose_wing, goose_primary, goose_beak, goose_knob, goose_nail, goose_mouth, goose_leg,
              goose_eye_white, goose_eye, goose_brow.
              Animations: idle (loop 2.4 s, in the cage: wings folded, shifts, mutters, turns a glare on the camera),
              fly (loop 0.67 s: neck stretched forward, feet trailing, big wing beats, turned a further 22 degrees
              to the camera; the body bobs 0.06), honk (one-shot 0.8 s: winds back, thrusts the neck out with the
              beak wide and the wings half raised, ends in the idle stance).
cage.glb      root "cage" (2 wide at the posts, 2.28 over the eaves, 2.59 tall to the ridge, 1.4 deep; origin at the
              bottom centre; floor with straw, top at 0.12) and child "door" (the whole front: frame, wire, a Z brace,
              hinges, a padlock) whose origin is on the hinge line of the right post (x 0.89, z +0.73 Godot).
              Animation "open" (0.7 s): a rattle, then it bursts open towards the camera, overshoots and settles at
              115 degrees. Put the goose at the cage origin + (-0.15, 0.12, 0) so its beak clears the right post.
              Materials cage_wood, _wood_dark, _roof, _wire, _iron, _brass, _straw, _straw_dark.
egg.glb       a brown egg (0.18 wide, top at 0.24) in a straw nest 0.3 across; origin at the base. egg_shell, egg_speck,
              nest_straw, nest_straw_dark.
grain.glb     a heap of golden corn 0.4 wide, 0.17 tall, a small heap beside it and strays; origin at the base centre of
              the big heap. grain_seed, grain_seed_dark.
lift.glb      root "lift": a wooden pallet 1.54 wide, 0.52 deep, origin at the TOP centre of the deck (the deck is
              y -0.035..0, runners below to -0.19). Two ropes rise at the back corners (Godot z -0.2, behind a rider)
              to a spreader bar 1.47 up and a ring at 1.72; child "rope" (origin at the ring top, 1.77 up; 1 unit long
              going up: scale its Y to reach the top of the shaft). lift_wood, _wood_dark, _rope, _iron.
brick.glb     root "brick": one 0.5 x 0.5 x 0.5 block, origin at the CENTRE: three staggered courses of warm red brick
              over cream mortar, running the full depth (the ends show at a platform's edge; halves meet the next
              block's halves). Child "brick_top": the grass on top (+0.25..+0.28, tufts to +0.35) rolling over the
              front edge, a daisy or two: hide it when another block sits on top. Materials brick_face (recolour per
              stage), brick_mortar, brick_top (the grass), brick_top_dark, brick_flower, brick_flower_heart.
ladder.glb    a 0.5 wide segment 0.5 tall: rails at x = +-0.2, two rungs (0.125, 0.375) lashed with rope; origin at the
              bottom centre, depth Godot z -0.03..+0.035. Stack every 0.5. ladder_wood, _wood_dark, _rope.
Backdrop (origin at the base centre, front towards the camera; warm golden-hour colours; lit windows are emissive):
  bg_barn      a red gambrel barn 4.4 wide over the eaves, 4.1 to the ridge (4.8 with the cockerel weather vane),
               2.4 deep: white trim, X-braced doors, a hay loft with hay, a round lit window. bg_barn_red, _red_dark,
               _trim, _roof, _dark, bg_hay, bg_barn_glow, bg_barn_iron.
  bg_silo      a grain silo 1.6 across, 5.1 tall, ribbed bands, red dome, a ladder. bg_silo_metal, _band, _roof, _base.
  bg_fence     a rail fence 2 long (x -1..1), 1.0 tall, posts at x = +-0.5: tile every 2. bg_fence_wood, _wood_dark,
               bg_grass.
  bg_haybale   a round bale 1.1 across, 1 wide, its rolled face to the camera. bg_hay, bg_hay_dark.
  bg_tree      an apple tree 4.2 tall, 3.5 wide. bg_tree_bark, _leaf, _leaf_light, _leaf_dark, _apple.
  bg_windmill  a white tower mill 5.5 tall to the cap; child "blades" (four lattice sails, 3 long; hub at (0, 4.9,
               +1.2) Godot) with the animation "turn" (loop 4 s, one turn anticlockwise seen from the camera).
               bg_mill_wall, _base, _cap, _wood, _sail, _window (emissive), _trim.
  bg_hill      a rolling hill panel 12 wide (x -6..6), up to 3.8 tall, bulging 1.3 towards the camera at its foot: a
               patchwork of fields (bg_hill_grass, bg_hill_field golden, bg_hill_field_light), hedgerows, little trees
               on the crest (bg_hill_hedge, bg_tree_bark).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90
from blastyard_bombers import merge, mirror, limb
from prism_models import animate, export_anim, empty, edit
from hopline_models import TurnRig, ell
from mossfolk_models import lumpy, lathe_r, solid
import humanoid as HU
from relic_models import P, clear_all, cycle, rot_c, yawed, export_humanoid, slim, air_legs

FPS = 30
TILE = 0.5
HERO_GAME = 1.1 / 1.7     # the game scales the farmhand (1.7 tall) to 1.1 units (2.2 tiles)


# ------------------------------------------------------------------ the farmhand

FH_YAW = 62            # facing +X, turned 28 degrees towards the camera
FSK = HU.Skeleton(HU.proportions(sh_w=0.18, hip_w=0.1))
FSHAPE = {"chest": 1.1, "waist": 1.12, "hips": 1.1, "arms": 1.2, "legs": 1.18, "neck": 1.15, "hand": 1.25}
FHEAD = 1.42
FH = (0, -0.02, 1.715)          # head centre
FH_SCALE = 0.88          # set so the cap top is 1.70 (printed at export)
RIG_TO_GAME = FH_SCALE * HERO_GAME


def f_stand(w=0.12):
    return {"ik_foot.L": (w, 0.03, 0.09, 0, 10), "ik_foot.R": (-w, -0.03, 0.09, 0, 12), "ikw.L": 1.0, "ikw.R": 1.0}


def f_arms(br=0.0):
    return {"clavicle.L": (2, 0, 2 + 1.5 * br), "clavicle.R": (2, 0, 2 + 1.5 * br),
            "arm.L": (4, 0, 12), "forearm.L": (20 + 2 * br, 0, 0), "hand.L": (0, 0, -4),
            "arm.R": (8, 0, 12), "forearm.R": (24 - 2 * br, 0, 0), "hand.R": (0, 0, -4)}


F_STAND = P(f_stand(), **{"root": (0, 0, -0.03), "spine": (1, 0, 0), "chest": (-1, 0, 0), "head": (-3, 0, 0)},
            **f_arms())


def f_idle():
    """2.4 s: breathing, a look round at the camera and back, a little weight shift."""
    def f(t):
        br = math.sin(2 * math.pi * t * 2)
        sway = math.sin(2 * math.pi * t)
        look = math.sin(2 * math.pi * t) ** 3
        p = P(F_STAND, **{"root": (0.012 * sway, 0, -0.03 - 0.006 * br), "hips": (0, 3 * sway, -2 * sway),
                          "spine": (1, -1 * sway, 0), "chest": (-1 + 1.5 * br, -2 * sway - 6 * look, 0),
                          "neck": (0, -16 * look, 0), "head": (-3 - 2 * br, -22 * look, -3 * look)})
        p.update(f_arms(br))
        return p
    return cycle(72, f, 3)


WALK_FRAMES, WALK_STRIDE = 16, 1.64


def f_walk():
    """A jaunty, bouncy walk: WALK_STRIDE rig metres per cycle (two steps)."""
    return HU.gait(FSK, WALK_FRAMES, WALK_STRIDE, 0.56, lift=0.14, lift_at=0.42, strike=16, push=34, bob=0.03,
                   drop=-0.035, lean=5, width=0.12, arm_swing=34, arm_out=12, elbow=34, elbow_swing=26,
                   pelvis_yaw=9, pelvis_roll=5, shoulder_yaw=9, reach=0.5, sway=0.014, step=1,
                   base={"head": (-4, 0, 0), "spine": (2, 0, 0)})


def f_jump():
    """0.47 s one-shot: crouch, spring, knees tucked with the arms flung up (holds the last frame; blend to fall)."""
    crouch = P(F_STAND, **{"root": (0, 0.02, -0.2), "hips": (18, 0, 0), "spine": (10, 0, 0), "chest": (6, 0, 0),
                           "head": (-16, 0, 0), "ik_foot.L": (0.12, 0.06, 0.09, 0, 10),
                           "ik_foot.R": (-0.12, -0.06, 0.09, 0, 12), "arm.L": (-30, 0, 16), "arm.R": (-26, 0, 16),
                           "forearm.L": (30, 0, 0), "forearm.R": (40, 0, 0)})
    push = P(F_STAND, **{"root": (0, 0.04, 0.06), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (6, 0, 4), "shin.L": (8, 0, 0),
                         "thigh.R": (-12, 0, 4), "shin.R": (16, 0, 0), "foot.L": (-45, 0, 0), "foot.R": (-50, 0, 0),
                         "spine": (-4, 0, 0), "chest": (-6, 0, 0), "head": (-10, 0, 0),
                         "arm.L": (150, 0, 24), "forearm.L": (20, 0, 0), "arm.R": (140, 0, 20), "forearm.R": (30, 0, 0)})
    up = P(push, **air_legs(0.85, 0.35), **{"root": (0, 0, 0.1), "spine": (8, 0, 0), "chest": (4, 0, 0),
                                            "head": (-12, 0, 0), "arm.L": (160, 0, 36), "forearm.L": (26, 0, 0),
                                            "arm.R": (150, 0, 34), "forearm.R": (30, 0, 0)})
    return HU.Anim({1: F_STAND, 4: crouch, 7: push, 11: up, 15: P(up, **{"arm.L": (156, 0, 40), "arm.R": (146, 0, 38)})})


def f_fall():
    """0.4 s loop: arms windmilling up, legs pedalling."""
    def f(t):
        a = 2 * math.pi * t
        p = P(F_STAND, **air_legs(0.25 + 0.1 * math.sin(a), 0.6 * math.sin(a)))
        p.update({"root": (0, 0, 0.04), "spine": (-4, 0, 0), "chest": (-6, 0, 0), "head": (-14, 0, 0),
                  "arm.L": (135 + 22 * math.sin(a), 0, 55), "forearm.L": (30 + 15 * math.cos(a), 0, 0),
                  "arm.R": (125 - 22 * math.sin(a), 0, 50), "forearm.R": (40 - 15 * math.cos(a), 0, 0),
                  "hand.L": (0, 0, 20), "hand.R": (0, 0, 20)})
        return p
    return cycle(12, f, 1)


# the climb: written facing the ladder (forward), then turned so the farmhand shows his back to the camera
LADDER_FWD = 0.3                 # the rungs' plane in front of the hips (rig metres)
CLIMB_FRAMES = 16
CLIMB_STEP = TILE / RIG_TO_GAME      # rig metres per cycle: one ladder segment (0.5 game units) per cycle
CLIMB_TURN = 180 - FH_YAW


def f_climb():
    D = CLIMB_STEP
    duty = 0.6

    def limb_z(ph, z0, lift):
        """In place: a gripping limb slides down at the climb speed, then reaches up to its next hold."""
        if ph < duty:
            u = ph / duty
            return z0 + D * duty * (0.5 - u), 0.0
        v = (ph - duty) / (1 - duty)
        return z0 - D * duty * 0.5 + D * duty * HU.smoothstep(0, 1, v), math.sin(math.pi * v) * lift

    def f(t):
        p = {}
        for X, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            zh, oh = limb_z((t + off) % 1.0, 1.56, 0.08)
            p["ik_hand." + X] = (0.17 * s, LADDER_FWD - 0.06 - oh, zh)
            p["ikh." + X] = 1.0
            p["hand_dir." + X] = (-20 * s, 70, 90)
            p["hdw." + X] = 0.8
            zf, of = limb_z((t + off + 0.5) % 1.0, 0.36, 0.1)
            p["ik_foot." + X] = (0.12 * s, LADDER_FWD - 0.12 - of, zf, 0, 8)
            p["ikw." + X] = 1.0
        b = math.sin(4 * math.pi * t)
        sw = math.sin(2 * math.pi * t)
        p.update({"root": (0.03 * sw, 0.0, -0.07 + 0.025 * b), "hips": (-4, 4 * sw, 3 * sw), "spine": (4, -3 * sw, 0),
                  "chest": (2, -3 * sw, -2 * sw), "neck": (-6, 0, 0), "head": (-14, 6 * sw, 0)})
        return p
    a = cycle(CLIMB_FRAMES, f, 1)
    a.arm_pole = {"L": (0.5, 0.2, -1.0), "R": (0.5, 0.2, -1.0)}
    return yawed(a, CLIMB_TURN)


F_LIE = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-90, 0, 0), "root": (0, 0, 0.13), "hips": (0, 0, 0), "spine": (-2, 0, 0),
         "chest": (-2, 0, 0), "neck": (4, 0, 0), "head": (6, 20, 0), "arm.L": (20, 0, 70), "forearm.L": (40, 0, 0),
         "arm.R": (30, 0, 64), "forearm.R": (30, 0, 0), "thigh.L": (22, 0, 12), "shin.L": (40, 0, 0),
         "thigh.R": (8, 0, 14), "shin.R": (14, 0, 0), "foot.L": (-30, 0, 0), "foot.R": (-35, 0, 0)}


def f_die():
    """1.4 s one-shot: a startled hop with the hands up, a dizzy wobble, then he topples backwards flat on his back,
    bounces once and lies spread out (holds)."""
    jolt = P(F_STAND, **{"root": (0, 0, 0.12), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (10, 0, 10), "shin.L": (14, 0, 0),
                         "thigh.R": (-4, 0, 10), "shin.R": (16, 0, 0), "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0),
                         "spine": (-8, 0, 0), "chest": (-10, 0, 0), "head": (-22, 0, 0),
                         "arm.L": (165, 0, 44), "forearm.L": (10, 0, 0), "arm.R": (165, 0, 40), "forearm.R": (14, 0, 0),
                         "hand.L": (0, 0, 30), "hand.R": (0, 0, 30)})
    wob1 = P(F_STAND, **{"turn": (-6, 0, 10), "root": (0, -0.02, -0.02), "spine": (-4, 12, 6), "head": (-8, 24, 12),
                         "arm.L": (70, 0, 80), "forearm.L": (40, 0, 0), "arm.R": (90, 0, 70), "forearm.R": (30, 0, 0)})
    wob2 = P(wob1, **{"turn": (-10, 0, -10), "spine": (-4, -12, -6), "head": (-10, -24, -12),
                      "arm.L": (100, 0, 70), "arm.R": (60, 0, 80)})
    tip = P(F_STAND, **{"turn": (-45, 0, 0), "root": (0, 0.3, 0.06), "ikw.L": 0.0, "ikw.R": 0.0,
                        "thigh.L": (14, 0, 6), "shin.L": (4, 0, 0), "thigh.R": (6, 0, 6), "shin.R": (4, 0, 0),
                        "foot.L": (-10, 0, 0), "foot.R": (-10, 0, 0), "spine": (6, 0, 0), "head": (14, 0, 0),
                        "arm.L": (100, 0, 50), "forearm.L": (10, 0, 0), "arm.R": (110, 0, 44), "forearm.R": (10, 0, 0)})
    flat = P(F_LIE, **{"root": (0, 0.6, 0.3), "thigh.L": (50, 0, 10), "shin.L": (10, 0, 0), "thigh.R": (40, 0, 12),
                       "shin.R": (8, 0, 0), "arm.L": (70, 0, 60), "arm.R": (80, 0, 50), "head": (-6, 0, 0)})
    bounce = P(F_LIE, **{"turn": (-84, 0, 0), "root": (0, 0.64, 0.36), "thigh.L": (70, 0, 12), "shin.L": (20, 0, 0),
                         "thigh.R": (60, 0, 14), "shin.R": (20, 0, 0), "head": (-10, 0, 0), "arm.L": (60, 0, 80),
                         "arm.R": (60, 0, 76)})
    rest = P(F_LIE, **{"root": (0, 0.66, 0.29), "head": (4, 34, 6)})
    return HU.Anim({1: F_STAND, 4: jolt, 10: wob1, 15: wob2, 19: tip, 24: flat, 28: bounce,
                    33: P(rest, **{"head": (0, 10, 0)}), 37: rest, 43: rest})


def f_cheer():
    """1 s loop: two hops, both fists up, the cap-hand waving."""
    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a * 2)) ** 1.5
        pump = math.sin(a)
        p = P(f_stand(0.13), **{
            "root": (0, 0, -0.05 + 0.1 * hop - 0.05 * max(0.0, -math.sin(a * 2))),
            "spine": (-4, 5 * pump, 0), "chest": (-6, 6 * pump, 0), "neck": (-6, 0, 0), "head": (-16, -8 * pump, 0),
            "clavicle.L": (0, 0, 18 + 8 * max(0, pump)), "clavicle.R": (0, 0, 18 + 8 * max(0, -pump)),
            "arm.L": (150 + 20 * max(0, pump), 0, 34), "forearm.L": (20 + 50 * max(0, -pump), 0, 0),
            "arm.R": (150 + 20 * max(0, -pump), 0, 34), "forearm.R": (20 + 50 * max(0, pump), 0, 0),
            "hand.L": (0, 0, 10), "hand.R": (0, 0, 10)})
        for X in "LR":
            v = p["ik_foot." + X]
            p["ik_foot." + X] = (v[0], v[1], v[2] + 0.09 * hop, -10 * hop, v[4])
        return p
    return cycle(30, f, 1)


def farmhand_actions():
    return {"idle": f_idle(), "walk": f_walk(), "climb": f_climb(), "jump": f_jump(), "fall": f_fall(),
            "die": f_die(), "cheer": f_cheer()}


def farmhand():
    sk = FSK
    sh = FSHAPE
    skin = mat("farmhand_skin", (0.94, 0.66, 0.5), 0.5)
    cheek = mat("farmhand_cheek", (0.95, 0.5, 0.42), 0.55)
    white = mat("farmhand_eye_white", (0.97, 0.96, 0.93), 0.3)
    iris = mat("farmhand_iris", (0.18, 0.28, 0.12), 0.2)
    hair = mat("farmhand_hair", (0.78, 0.36, 0.12), 0.6, coat=0.1)
    lips = mat("farmhand_lips", (0.7, 0.36, 0.3), 0.5)
    shirt = mat("farmhand_shirt", (1.0, 0.76, 0.18), 0.8)
    shirt_dk = mat("farmhand_shirt_dark", (0.85, 0.56, 0.1), 0.8)
    denim = mat("farmhand_denim", (0.18, 0.34, 0.66), 0.85)
    denim_dk = mat("farmhand_denim_dark", (0.12, 0.23, 0.46), 0.85)
    stitch = mat("farmhand_stitch", (0.95, 0.7, 0.3), 0.7)
    welly = mat("farmhand_welly", (0.18, 0.46, 0.2), 0.3, coat=0.6)
    welly_dk = mat("farmhand_welly_dark", (0.1, 0.3, 0.12), 0.35, coat=0.4)
    sole = mat("farmhand_sole", (0.1, 0.08, 0.06), 0.7)
    brass = mat("farmhand_brass", (0.95, 0.72, 0.32), 0.3, 0.9)
    cap = mat("farmhand_cap", (0.2, 0.42, 0.24), 0.9)
    cap_dk = mat("farmhand_cap_dark", (0.12, 0.28, 0.15), 0.9)
    scarf = mat("farmhand_scarf", (0.86, 0.16, 0.1), 0.75)
    scarf_dot = mat("farmhand_scarf_dot", (0.98, 0.92, 0.82), 0.75)

    HU.human_body(sk, skin, shirt, denim, white, iris, shoes=welly, sole=sole, glove=skin, sleeves="short",
                  hands="relaxed", shape=sh, head=False, shoe_height=0.42)
    slim(welly, 0.6)
    slim(denim, 0.6, bone="~body")
    slim(shirt, 0.55, bone="~body")
    for X in "LR":
        slim(denim, 0.7, bone="~leg." + X)
        slim(skin, 0.6, bone="hand." + X)
    # rolled sleeves above the elbow
    for X, s in (("L", 1), ("R", -1)):
        HU.tube(HU.arm_path(sk, X, 0.01, 0.0, 0.44, shape=sh["arms"]), "~arm." + X, shirt, 18, 0.016,
                lateral=(s, 0, 0), caps=(True, False))
        HU.tube(HU.arm_path(sk, X, 0.026, 0.34, 0.45, shape=sh["arms"]), "~arm." + X, shirt_dk, 14, 0.02,
                lateral=(s, 0, 0))
    # the head: big and young, freckles, rosy cheeks, a shock of ginger hair under the cap
    k = FHEAD
    HU.head_detailed(skin, white, iris, center=FH, hair=None, size=k, brow=hair, lips=lips)
    cx, cy, cz = FH
    HU.sphere(0.104 * k, (0, cy + 0.045, cz + 0.012 * k), "head", hair, (0.95, 0.9, 0.9), 20, 10)      # hair at the back
    for s in (-1, 1):
        HU.sphere(0.022 * k, (0.058 * k * s, cy - 0.07 * k, cz - 0.03 * k), "head", cheek, (1.0, 0.6, 0.8), 10, 6)
        HU.sphere(0.022 * k, (0.09 * k * s, cy - 0.0 * k, cz + 0.01 * k), "head", hair, (0.55, 0.9, 1.3), 10, 6)
    # tufts of hair sticking out from under the cap over the forehead
    for x, z, rx in ((-0.05, 0.07, 0.3), (-0.015, 0.078, 0.0), (0.03, 0.074, -0.3)):
        HU.sphere(0.028 * k, (x * k, cy - 0.07 * k, cz + z * k), "head", hair, (0.9, 0.6, 0.5), 10, 6)
    # the flat cap: a band, a soft crown pulled forward over a peak, a button on top
    HU.body_loft([(cz + 0.04 * k, 0.106 * k, 0.114 * k, cy + 0.005), (cz + 0.072 * k, 0.108 * k, 0.116 * k, cy + 0.005)],
                 "head", cap_dk, 24, 0)
    crown = HU.sphere(0.118 * k, (0, 0, 0), "head", cap, (1.0, 1.1, 0.46), 24, 12)
    crown.data.transform(Matrix.Rotation(0.16, 4, "X"))
    crown.data.transform(Matrix.Translation((0, cy - 0.012 * k, cz + 0.09 * k)))
    peak = HU.box((0.19 * k, 0.08 * k, 0.016), (0, cy - 0.125 * k, cz + 0.064 * k), "head", cap_dk, rot=(0.2, 0, 0),
                  bevel=0.007)
    HU.sphere(0.014 * k, (0, cy - 0.012 * k, cz + 0.145 * k), "head", cap_dk, (1, 1, 0.6), 10, 6)
    # the neckerchief: a knotted roll, a triangle at the front, white dots
    tube_pts = [(0.0, -0.085, 1.475, 0.026), (0.08, -0.05, 1.485, 0.028), (0.095, 0.02, 1.495, 0.028),
                (0.05, 0.08, 1.505, 0.026), (-0.02, 0.085, 1.505, 0.026), (-0.09, 0.03, 1.495, 0.028),
                (-0.08, -0.05, 1.485, 0.028), (0.0, -0.088, 1.475, 0.026)]
    HU.tube(tube_pts, "~body", scarf, 10, 0.03)
    HU.sphere(0.034, (0.0, -0.105, 1.465), "~body", scarf, (1.2, 0.7, 1.0), 12, 7)
    for s in (-1, 1):
        HU.sphere(0.028, (0.03 * s, -0.11, 1.45), "~body", scarf, (1.0, 0.45, 1.3), 10, 6)
        HU.sphere(0.006, (0.06 * s, -0.098, 1.49), "~body", scarf_dot, (1, 0.6, 1), 6, 4)
    # the dungarees: a bib over the chest (to the armpits), side buttons, a bib pocket, straps over the shoulders
    g = 0.014
    rings = [(z, rx + g, ry + g, cy_) for z, rx, ry, cy_, sq in HU.torso_rings(1.0, 1.36, 0.0, sh)]
    HU.shell(rings, -150, -30, "~body", denim, 0.012, 14, 0)
    HU.box((0.12, 0.014, 0.085), (0.0, -0.118 * sh["chest"] - 0.012, 1.25), "~body", denim_dk, rot=(-0.08, 0, 0),
           bevel=0.008)
    HU.box((0.1, 0.012, 0.006), (0.0, -0.118 * sh["chest"] - 0.02, 1.275), "~body", stitch, rot=(-0.08, 0, 0),
           bevel=0.002)
    for s in (-1, 1):
        pts = [(0.08 * s, -0.118, 1.35, 0.012), (0.11 * s, -0.08, 1.44, 0.012), (0.115 * s, 0.02, 1.47, 0.012),
               (0.1 * s, 0.11, 1.39, 0.012), (0.06 * s, 0.13, 1.22, 0.012), (0.02 * s, 0.13, 1.08, 0.012)]
        HU.tube(pts, "~body", denim, 6, 0.028, ell=(1.9, 0.5))
        HU.sphere(0.018, (0.085 * s, -0.132, 1.345), "~body", brass, (1, 0.55, 1), 10, 6)
        HU.sphere(0.014, (0.175 * s * sh["waist"], -0.02, 1.02), "~body", brass, (0.5, 1, 1), 8, 5)
    # wellies: a turned-down rim and a chunky tread
    for X, s in (("L", 1), ("R", -1)):
        x = sk.head("foot." + X).x
        HU.body_loft([(0.39, 0.058, 0.066, 0.006), (0.43, 0.066, 0.074, 0.006), (0.45, 0.064, 0.072, 0.006)],
                     "~foot." + X, welly_dk, 18, 0, x0=x)
        HU.box((0.1, 0.27, 0.03), (x, -0.045, 0.015), "~foot." + X, sole, bevel=0.012)
    export_humanoid("farmhand", farmhand_actions(), sk, FH_SCALE, FH_YAW)
    print("   walk: %.2f game units per %d-frame cycle (%.2f units/s = %.2f tiles/s at speed_scale 1)" % (
        WALK_STRIDE * RIG_TO_GAME, WALK_FRAMES, WALK_STRIDE * RIG_TO_GAME * FPS / WALK_FRAMES,
        WALK_STRIDE * RIG_TO_GAME * FPS / WALK_FRAMES / TILE))
    print("   climb: %.2f game units per cycle (%.2f units/s)" % (CLIMB_STEP * RIG_TO_GAME,
                                                               CLIMB_STEP * RIG_TO_GAME * FPS / CLIMB_FRAMES))


# ------------------------------------------------------------------ birds (TurnRig: built facing -Y, turned to +X)

def ell_at(c, r, u, v, out=0.0):
    """A point on an axis-aligned ellipsoid: u around (0 = +X, 90 = -Y front), v up (-90..90), pushed out by `out`."""
    a, b = math.radians(u), math.radians(v)
    n = Vector((math.cos(b) * math.cos(a), -math.cos(b) * math.sin(a), math.sin(b)))
    return Vector(c) + Vector((n.x * (r[0] + out), n.y * (r[1] + out), n.z * (r[2] + out))), n


def speckles(c, r, material, seed, n, vmin=-20, vmax=80, size=0.018, skip=None, pitch=0.0):
    """Little flattened dots on an ellipsoid (as made by ell with that pitch): the speckled hen's pattern."""
    rnd = random.Random(seed)
    parts = []
    R = Matrix.Rotation(math.radians(pitch), 3, "X")
    for i in range(n):
        u, v = rnd.uniform(0, 360), rnd.uniform(vmin, vmax)
        p, nrm = ell_at((0, 0, 0), r, u, v, 0.001)
        p, nrm = R @ p + Vector(c), R @ nrm
        if skip and skip(p):
            continue
        o = sphere(size * rnd.uniform(0.7, 1.2), (0, 0, 0), material, scale=(1, 1, 0.3), segs=8, rings=4)
        o.data.transform(Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4())
        o.data.transform(Matrix.Translation(p))
        parts.append(o)
    return parts


def bird_leg(rig, X, hip, knee, ankle, toe_len, r_shank, leg_m, claw_m=None, webbed=None, n_toes=3):
    """Shank (shin bone) and toes (foot bone): toes fan forward (-Y) from the ankle, a short back toe; webbed: a
    material for a web between the front toes."""
    s = 1 if X == "L" else -1
    ankle = Vector(ankle)
    rig.rigid("shin." + X, rod(knee, ankle + Vector((0, 0, 0.01)), r_shank, leg_m, r2=r_shank * 0.8, verts=10),
              sphere(r_shank * 1.15, tuple(knee), leg_m, segs=10, rings=6))
    toes = []
    tips = []
    for k in range(n_toes):
        a = math.radians((k - (n_toes - 1) / 2) * 28)
        tip = ankle + Vector((math.sin(a) * toe_len, -math.cos(a) * toe_len, -ankle.z + r_shank * 0.35))
        tips.append(tip)
        toes.append(rod(ankle + Vector((0, 0, -0.005)), tip, r_shank * 0.55, leg_m, r2=r_shank * 0.35, verts=8))
        if claw_m:
            toes.append(sphere(r_shank * 0.35, tuple(tip + Vector((0, -0.006, 0))), claw_m, scale=(1, 1.6, 0.8),
                               segs=8, rings=4))
    toes.append(rod(ankle, ankle + Vector((0, toe_len * 0.4, -ankle.z + r_shank * 0.35)), r_shank * 0.45, leg_m,
                    r2=r_shank * 0.3, verts=6))
    toes.append(sphere(r_shank * 0.9, tuple(ankle), leg_m, segs=10, rings=6))
    if webbed:
        bm = bmesh.new()
        c = bm.verts.new(ankle + Vector((0, -0.01, -ankle.z + r_shank * 0.3)))
        vs = [bm.verts.new(t + Vector((0, 0.01, -0.004))) for t in tips]
        for a_, b_ in zip(vs, vs[1:]):
            bm.faces.new((c, a_, b_))
        me = bpy.data.meshes.new("web")
        bm.to_mesh(me)
        bm.free()
        w = bpy.data.objects.new("web", me)
        bpy.context.scene.collection.objects.link(w)
        solid(w, r_shank * 0.35)
        K.finish(w, webbed, smooth=0)
        toes.append(w)
    rig.rigid("foot." + X, *toes)


def fan_feathers(base, n, spread, length, width, pitch0, material, x_spread=0.0, thick=0.35):
    """A fan of long feathers from `base`, rising from pitch0 (degrees above the -Y... +Y axis) over `spread`."""
    out = []
    for k in range(n):
        f = k / max(1, n - 1) - 0.5
        pitch = math.radians(pitch0 + spread * f)
        d = Vector((0, math.cos(pitch), math.sin(pitch)))
        o = sphere(1.0, (0, 0, 0), material, scale=(width * thick, length, width), segs=12, rings=8)
        o.data.transform(Matrix.Translation((0, length * 0.8, 0)))
        o.data.transform(Matrix.Rotation(pitch, 4, "X"))
        o.data.transform(Matrix.Rotation(f * 0.3, 4, "Y"))
        o.data.transform(Matrix.Translation(Vector(base) + Vector((x_spread * f, 0, 0))))
        out.append(o)
    return out


HEN_YAW = 70            # facing +X, turned 20 degrees towards the camera
HEN_STRIDE, HEN_WALK = 0.44, 18


def hen():
    feather = mat("hen_feather", (0.97, 0.94, 0.87), 0.85)
    speck = mat("hen_speckle", (0.86, 0.8, 0.7), 0.85)
    comb = mat("hen_comb", (0.9, 0.12, 0.1), 0.45, coat=0.3)
    beak = mat("hen_beak", (1.0, 0.72, 0.2), 0.4, coat=0.3)
    leg = mat("hen_leg", (1.0, 0.68, 0.18), 0.45, coat=0.2)
    eye = mat("hen_eye", (0.03, 0.02, 0.02), 0.15, coat=1.0)
    iris = mat("hen_iris", (1.0, 0.55, 0.1), 0.3)
    shine = mat("hen_eye_shine", (1.0, 1.0, 1.0), 0.2, emit=3.0)
    B = {"root": ((0, 0, 0), (0, 0, 0.1), None),
         "body": ((0, 0.06, 0.34), (0, -0.14, 0.4), "root"),
         "neck": ((0, -0.15, 0.47), (0, -0.23, 0.62), "body"),
         "head": ((0, -0.23, 0.62), (0, -0.33, 0.645), "neck"),
         "tail": ((0, 0.2, 0.46), (0, 0.32, 0.62), "body")}
    for X, s in (("L", 1), ("R", -1)):
        B["wing." + X] = ((0.15 * s, -0.1, 0.49), (0.17 * s, 0.2, 0.45), "body")
        B["thigh." + X] = ((0.075 * s, 0.02, 0.3), (0.075 * s, 0.035, 0.16), "root")
        B["shin." + X] = ((0.075 * s, 0.035, 0.16), (0.075 * s, 0.0, 0.035), "thigh." + X)
        B["foot." + X] = ((0.075 * s, 0.0, 0.035), (0.075 * s, -0.09, 0.02), "shin." + X)
    rig = TurnRig(B, HEN_YAW, fps=FPS)
    BODY_C, BODY_R = (0, 0.03, 0.37), (0.19, 0.28, 0.2)
    rig.rigid("body", ell(BODY_C, BODY_R, feather, pitch=8, segs=24, rings=16),
              ell((0, -0.14, 0.39), (0.17, 0.15, 0.18), feather, segs=20, rings=12),
              ell((0, 0.05, 0.27), (0.155, 0.21, 0.12), feather, segs=20, rings=10),
              ell((0, 0.2, 0.47), (0.13, 0.15, 0.13), feather, pitch=-30, segs=18, rings=10),
              speckles(BODY_C, BODY_R, speck, 11, 60, vmin=-10, vmax=80, size=0.022, pitch=8,
                       skip=lambda p: abs(p.x) > 0.12 and -0.14 < p.y < 0.22 and p.z < 0.5),
              speckles((0, -0.14, 0.39), (0.17, 0.15, 0.18), speck, 12, 30, vmin=-30, vmax=70, size=0.02),
              speckles((0, 0.2, 0.47), (0.13, 0.15, 0.13), speck, 13, 16, vmin=0, vmax=80, size=0.02, pitch=-30))
    # the neck: a feathery tube with a ruff of hackles at its base
    rig.smooth(["body", "neck", "head"],
               tube([(0, -0.1, 0.44), (0, -0.17, 0.52), (0, -0.215, 0.6), (0, -0.235, 0.66)], [0.12, 0.095, 0.075, 0.07],
                    feather, verts=16),
               ell((0, -0.16, 0.52), (0.115, 0.1, 0.1), feather, pitch=-20, segs=18, rings=10))
    for k in range(7):
        a = math.radians(-60 + 120 * k / 6)
        c = Vector((0.1 * math.sin(a), -0.16 - 0.08 * math.cos(a), 0.5))
        o = ell(tuple(c), (0.035, 0.03, 0.07), feather, segs=10, rings=6)
        rig.smooth(["body", "neck"], o)
    # the head
    H = Vector((0, -0.245, 0.665))
    parts = [ell(tuple(H), (0.078, 0.092, 0.084), feather, segs=20, rings=12),
             ell(tuple(H + Vector((0, -0.02, -0.03))), (0.07, 0.07, 0.06), feather, segs=16, rings=8)]
    parts.append(tube([H + Vector((0, -0.07, -0.005)), H + Vector((0, -0.12, -0.015)), H + Vector((0, -0.155, -0.035))],
                      [0.03, 0.018, 0.004], beak, verts=10))
    parts.append(tube([H + Vector((0, -0.07, -0.028)), H + Vector((0, -0.12, -0.034))], [0.018, 0.006], beak, verts=8))
    for k, (y, z, r) in enumerate(((-0.07, 0.075, 0.03), (-0.035, 0.1, 0.038), (0.0, 0.1, 0.036), (0.035, 0.085, 0.03),
                                   (0.06, 0.06, 0.024))):
        parts.append(sphere(r, tuple(H + Vector((0, y, z))), comb, scale=(0.5, 0.9, 1.25), segs=12, rings=8))
    parts.append(ell(tuple(H + Vector((0, -0.02, 0.05))), (0.028, 0.08, 0.035), comb, segs=12, rings=6))
    for s in (-1, 1):
        parts.append(sphere(0.028, tuple(H + Vector((0.016 * s, -0.075, -0.075))), comb, scale=(0.55, 0.8, 1.4),
                            segs=12, rings=8))
        e = H + Vector((0.064 * s, -0.03, 0.018))
        parts.append(sphere(0.024, tuple(e), iris, scale=(0.5, 1, 1), segs=12, rings=8))
        parts.append(sphere(0.016, tuple(e + Vector((0.009 * s, -0.003, 0))), eye, scale=(0.5, 1, 1), segs=10, rings=6))
        parts.append(sphere(0.006, tuple(e + Vector((0.014 * s, -0.008, 0.008))), shine, segs=6, rings=4))
    rig.rigid("head", *parts)
    # wings: a feathered paddle on each side with rows of scalloped feather tips at the back and bottom
    for X, s in (("L", 1), ("R", -1)):
        wp = [ell((0.175 * s, 0.03, 0.42), (0.05, 0.2, 0.12), feather, pitch=10, segs=18, rings=10)]
        for row, (y0, z0) in enumerate(((0.12, 0.36), (0.18, 0.4), (0.2, 0.46))):
            for k in range(3):
                wp.append(ell((0.19 * s, y0 + 0.02 * k - 0.07 * row * 0, z0 - 0.045 * k), (0.03, 0.08, 0.035),
                              feather, pitch=-25 + 12 * k, segs=12, rings=6))
        wp += speckles((0.175 * s, 0.03, 0.42), (0.05, 0.2, 0.12), speck, 14 + s, 40, vmin=-60, vmax=60, size=0.02,
                       pitch=10, skip=lambda p, s=s: p.x * s < 0.195)
        rig.rigid("wing." + X, *wp)
        rig.rigid("thigh." + X, ell((0.085 * s, 0.03, 0.24), (0.07, 0.085, 0.085), feather, segs=14, rings=8))
        bird_leg(rig, X, None, Vector((0.075 * s, 0.035, 0.17)), (0.075 * s, 0.0, 0.035), 0.085, 0.017, leg, leg)
    # the tail: a raised fan
    rig.rigid("tail", *fan_feathers((0, 0.22, 0.47), 5, 60, 0.12, 0.05, 50, feather, x_spread=0.06),
              *fan_feathers((0, 0.2, 0.46), 4, 50, 0.09, 0.045, 30, feather, x_spread=0.1))
    rig.build("hen")
    hen_actions(rig)
    rig.save("hen")


def hen_actions(rig):
    S = HEN_STRIDE
    duty = 0.62

    def legs(t, lift=0.06):
        p = {}
        for X, off in (("L", 0.0), ("R", 0.5)):
            q = (t + off) % 1.0
            if q < duty:
                u = q / duty
                y, z, fp = -S * duty / 2 + S * duty * u, 0.0, 0.0
            else:
                v = (q - duty) / (1 - duty)
                y = S * duty / 2 - S * duty * HU.smoothstep(0, 1, v)
                z = lift * math.sin(math.pi * v)
                fp = 40 * math.sin(math.pi * v)
            p["@thigh." + X] = (0, y, z)
            p["thigh." + X] = (-10 * math.sin(math.pi * max(0, (q - duty) / (1 - duty))) if q >= duty else 0, 0, 0)
            p["foot." + X] = (fp, 0, 0)
        return p

    def walk(t):
        p = legs(t)
        a = 2 * math.pi * t
        ph = (2 * t) % 1.0
        hy = -0.03 + 0.06 * ph / 0.7 if ph < 0.7 else 0.03 - 0.06 * HU.smoothstep(0, 1, (ph - 0.7) / 0.3)
        p.update({"@body": (0, 0, 0.012 * math.cos(2 * a)), "body": (2, 0, 0), "@root": (0, 0, 0),
                  "root": (0, 6 * math.sin(a), 0),
                  "@neck": (0, hy, 0.005 * math.cos(2 * a)), "neck": (4, 0, 0), "head": (-4, 0, 0),
                  "tail": (0, 0, 8 * math.sin(a)),
                  "wing.L": (0, -6 - 5 * math.sin(2 * a), 0), "wing.R": (0, 6 + 5 * math.sin(2 * a), 0)})
        return p
    rig.action("walk", {i: walk(i / HEN_WALK) for i in range(HEN_WALK + 1)}, loop=True)

    def climb(t):
        """Facing the camera, flapping hard and stepping up the rungs (in place)."""
        a = 2 * math.pi * t
        p = {}
        for X, off in (("L", 0.0), ("R", 0.5)):
            st = max(0.0, math.sin(a + off * 2 * math.pi))
            p["@thigh." + X] = (0, -0.02, 0.09 * st)
            p["thigh." + X] = (-25 * st, 0, 0)
            p["foot." + X] = (30 * st, 0, 0)
        flap = math.sin(2 * a)
        p.update({"root": (0, 0, -HEN_YAW), "@root": (0, 0, 0.03 + 0.03 * math.sin(2 * a + 1.2)),
                  "body": (-28, 0, 0), "neck": (22, 0, 0), "head": (10, 6 * math.sin(a), 0),
                  "tail": (-10, 0, 0),
                  "wing.L": (0, -70 - 45 * flap, -20), "wing.R": (0, 70 + 45 * flap, 20)})
        return p
    rig.action("climb", {i: climb(i / 16) for i in range(17)}, loop=True)

    up = {"body": (0, 0, 0), "neck": (0, 0, 0), "head": (0, 0, 0)}
    down = {"body": (32, 0, 0), "@body": (0, 0, -0.035), "neck": (68, 0, 0), "head": (8, 0, 0), "tail": (-12, 0, 0),
            "wing.L": (0, -8, 0), "wing.R": (0, 8, 0)}
    half = {"body": (20, 0, 0), "neck": (35, 0, 0), "head": (-5, 0, 0), "tail": (-8, 0, 0)}
    look = {"body": (6, 0, 0), "neck": (-4, 0, -22), "head": (-6, 0, -10), "tail": (0, 0, 10)}
    scratch = merge(half, {"@thigh.R": (0, 0.09, 0.05), "foot.R": (40, 0, 0)})
    rig.action("peck", {0: up, 4: down, 7: half, 10: down, 13: half, 16: down, 20: scratch, 23: half, 27: look,
                        30: up}, loop=True)

    def idle(t):
        a = 2 * math.pi * t
        turn = math.sin(a) ** 3
        return {"@body": (0, 0, 0.006 * math.sin(3 * a)), "neck": (-2, 0, 26 * turn), "head": (0, 14 * math.sin(2 * a), 12 * turn),
                "tail": (0, 0, 10 * math.sin(4 * a) * max(0, math.sin(a))),
                "wing.L": (0, -3 * max(0, math.sin(2 * a)), 0), "wing.R": (0, 3 * max(0, math.sin(2 * a)), 0)}
    rig.action("idle", {i: idle(i / 60) for i in range(0, 61, 3)}, loop=True)


GOOSE_YAW = 70
GOOSE_HEAD = 1.35


def goose():
    feather = mat("goose_feather", (0.97, 0.96, 0.92), 0.85)
    wing_m = mat("goose_wing", (0.84, 0.84, 0.82), 0.85)
    prim = mat("goose_primary", (0.5, 0.52, 0.56), 0.8)
    beak = mat("goose_beak", (1.0, 0.5, 0.1), 0.4, coat=0.4)
    knob = mat("goose_knob", (0.9, 0.36, 0.06), 0.4, coat=0.3)
    nail = mat("goose_nail", (0.18, 0.12, 0.1), 0.4)
    mouth = mat("goose_mouth", (0.8, 0.3, 0.32), 0.5)
    leg = mat("goose_leg", (1.0, 0.52, 0.12), 0.45, coat=0.2)
    eye_w = mat("goose_eye_white", (0.98, 0.97, 0.9), 0.3)
    eye = mat("goose_eye", (0.03, 0.03, 0.05), 0.15, coat=1.0)
    brow = mat("goose_brow", (0.32, 0.32, 0.36), 0.8)
    B = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "body": ((0, 0.15, 0.72), (0, -0.3, 0.8), "root"),
         "neck1": ((0, -0.42, 0.95), (0, -0.53, 1.25), "body"),
         "neck2": ((0, -0.53, 1.25), (0, -0.52, 1.56), "neck1"),
         "head": ((0, -0.52, 1.56), (0, -0.78, 1.6), "neck2"),
         "jaw": ((0, -0.66, 1.555), (0, -0.88, 1.54), "head"),
         "tail": ((0, 0.5, 0.82), (0, 0.72, 0.92), "body")}
    for X, s in (("L", 1), ("R", -1)):
        B["wing." + X] = ((0.28 * s, -0.25, 1.0), (0.78 * s, -0.2, 1.02), "body")
        B["tip." + X] = ((0.78 * s, -0.2, 1.02), (1.35 * s, -0.08, 1.0), "wing." + X)
        B["thigh." + X] = ((0.17 * s, 0.1, 0.56), (0.17 * s, 0.13, 0.32), "root")
        B["shin." + X] = ((0.17 * s, 0.13, 0.32), (0.17 * s, 0.08, 0.06), "thigh." + X)
        B["foot." + X] = ((0.17 * s, 0.08, 0.06), (0.17 * s, -0.12, 0.03), "shin." + X)
    rig = TurnRig(B, GOOSE_YAW, fps=FPS)
    rig.rigid("body", ell((0, 0.05, 0.8), (0.36, 0.6, 0.34), feather, pitch=6, segs=28, rings=18),
              ell((0, -0.33, 0.82), (0.32, 0.3, 0.33), feather, segs=24, rings=14),
              ell((0, 0.1, 0.62), (0.3, 0.44, 0.2), feather, segs=24, rings=12))
    rig.rigid("tail", ell((0, 0.55, 0.88), (0.2, 0.2, 0.13), feather, pitch=-25, segs=18, rings=10),
              *fan_feathers((0, 0.6, 0.88), 5, 40, 0.14, 0.07, 25, feather, x_spread=0.2))
    # the neck: long and thick, weighted along its two bones
    rig.smooth(["body", "neck1", "neck2", "head"],
               tube([(0, -0.36, 0.9), (0, -0.47, 1.05), (0, -0.53, 1.25), (0, -0.53, 1.42), (0, -0.53, 1.6)],
                    [0.22, 0.16, 0.135, 0.125, 0.125], feather, verts=18))
    H = Vector((0, -0.57, 1.63))
    hp = [ell(tuple(H), (0.12, 0.17, 0.125), feather, pitch=-8, segs=22, rings=14),
          ell(tuple(H + Vector((0, -0.07, -0.04))), (0.105, 0.11, 0.09), feather, segs=18, rings=10),
          # the upper beak with its knob and nail
          ell(tuple(H + Vector((0, -0.22, -0.035))), (0.058, 0.15, 0.042), beak, pitch=6, segs=18, rings=10),
          sphere(0.055, tuple(H + Vector((0, -0.12, 0.02))), knob, scale=(0.8, 1.0, 0.9), segs=14, rings=8),
          ell(tuple(H + Vector((0, -0.355, -0.05))), (0.03, 0.025, 0.02), nail, segs=10, rings=6),
          ell(tuple(H + Vector((0, -0.2, -0.06))), (0.045, 0.12, 0.012), mouth, pitch=6, segs=12, rings=6)]
    for s in (-1, 1):
        e = H + Vector((0.095 * s, -0.07, 0.03))
        hp.append(sphere(0.042, tuple(e), eye_w, scale=(0.55, 1.0, 1.0), segs=14, rings=10))
        hp.append(sphere(0.02, tuple(e + Vector((0.018 * s, -0.012, -0.006))), eye, scale=(0.5, 1, 1), segs=10, rings=6))
        # a heavy lid over the top half of the eye (grumpy) and a low, angled brow
        lid = sphere(0.046, (0, 0, 0), feather, scale=(0.6, 1.05, 0.6), segs=14, rings=8)
        lid.data.transform(Matrix.Rotation(math.radians(-18 * s), 4, "Y") @ Matrix.Rotation(math.radians(20), 4, "X"))
        lid.data.transform(Matrix.Translation(e + Vector((0.004 * s, 0.0, 0.03))))
        hp.append(lid)
        b = sphere(1.0, (0, 0, 0), brow, scale=(0.02, 0.075, 0.018), segs=12, rings=6)
        b.data.transform(Matrix.Rotation(math.radians(28), 4, "X"))
        b.data.transform(Matrix.Translation(e + Vector((0.01 * s, -0.01, 0.06))))
        hp.append(b)
    jaw = ell(tuple(H + Vector((0, -0.2, -0.075))), (0.048, 0.13, 0.022), beak, pitch=8, segs=16, rings=8)
    HS = Matrix.Translation(H) @ Matrix.Scale(GOOSE_HEAD, 4) @ Matrix.Translation(-H)      # a big cartoon head
    for o in hp + [jaw]:
        o.data.transform(HS)
    rig.rigid("head", *hp)
    rig.rigid("jaw", jaw)
    # wings, built spread (the rest pose): a padded arm, a long hand, grey primaries fanned at the tip
    for X, s in (("L", 1), ("R", -1)):
        bm = bmesh.new()
        N, M_ = 12, 3
        grid = []
        for i in range(N + 1):
            u = i / N
            x = 0.24 + u * 1.1
            lead_y = -0.3 + 0.18 * u
            chord = 0.5 * (1 - 0.55 * u)
            grid.append([bm.verts.new((s * x, lead_y + chord * j / M_, 1.02 + 0.03 * math.sin(math.pi * u) - 0.02 * j / M_))
                         for j in range(M_ + 1)])
        for i in range(N):
            for j in range(M_):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if s < 0 else f[::-1])
        me = bpy.data.meshes.new("wing")
        bm.to_mesh(me)
        bm.free()
        w = bpy.data.objects.new("wing", me)
        bpy.context.scene.collection.objects.link(w)
        solid(w, 0.05)
        K.finish(w, wing_m, smooth=50)
        rig.smooth(["body", "wing." + X, "tip." + X], w,
                   limb([(0.22 * s, -0.28, 1.03), (0.78 * s, -0.2, 1.05), (1.3 * s, -0.1, 1.02)], [0.07, 0.05, 0.025],
                        wing_m, verts=10, per=4, caps=True))
        # secondaries along the arm's trailing edge, primaries at the hand
        sec = []
        for k in range(8):
            x = 0.3 + 0.075 * k
            o = sphere(1.0, (0, 0, 0), wing_m, scale=(0.07, 0.1, 0.02), segs=12, rings=6)
            o.data.transform(Matrix.Translation((s * x, -0.3 + 0.18 * (x - 0.24) / 1.1 + 0.5 * (1 - 0.55 * (x - 0.24) / 1.1),
                                                 1.0)))
            sec.append(o)
        rig.rigid("wing." + X, *sec)
        pri = []
        for k in range(6):
            a = math.radians(-8 + 17 * k)
            L = 0.42 - 0.03 * k
            o = sphere(1.0, (0, 0, 0), prim, scale=(0.05, L / 2, 0.018), segs=12, rings=6)
            o.data.transform(Matrix.Translation((0, L / 2, 0)))
            o.data.transform(Matrix.Rotation(-s * (math.pi / 2 - a), 4, "Z"))
            o.data.transform(Matrix.Translation((s * (0.95 + 0.04 * k), -0.2 + 0.05 * k, 1.01 - 0.004 * k)))
            pri.append(o)
        rig.rigid("tip." + X, *pri)
        rig.rigid("thigh." + X, ell((0.19 * s, 0.1, 0.48), (0.12, 0.15, 0.13), feather, segs=16, rings=10))
        bird_leg(rig, X, None, Vector((0.17 * s, 0.13, 0.33)), (0.17 * s, 0.08, 0.06), 0.2, 0.04, leg, None, webbed=leg)
    rig.build("goose")
    goose_actions(rig)
    rig.save("goose")


G_FOLD = mirror({"wing.L": (-90, 0, 78), "tip.L": (0, 0, 6)})


def goose_actions(rig):
    def idle(t):
        """In the cage: shifts its weight, mutters, turns a glare on the camera, fluffs the wings."""
        a = 2 * math.pi * t
        glare = HU.smoothstep(0.3, 0.45, t) * (1 - HU.smoothstep(0.75, 0.9, t))
        mutter = max(0.0, math.sin(6 * a)) * (1 - glare)
        p = merge(G_FOLD, {"root": (0, 3 * math.sin(a), 0), "@body": (0, 0, 0.012 * math.sin(2 * a)),
                           "body": (2 * math.sin(2 * a), 0, 0),
                           "neck1": (6 + 4 * math.sin(a), 0, -8 * glare), "neck2": (-4, 0, -34 * glare + 6 * math.sin(a)),
                           "head": (-4 + 6 * glare, 0, -10 * glare), "jaw": (-10 * mutter, 0, 0),
                           "tail": (0, 0, 14 * math.sin(3 * a)),
                           "@thigh.L": (0, 0, 0.03 * max(0, math.sin(a))), "@thigh.R": (0, 0, 0.03 * max(0, -math.sin(a)))})
        return p
    rig.action("idle", {i: idle(i / 72) for i in range(0, 73, 3)}, loop=True)

    def fly(t):
        a = 2 * math.pi * t
        beat = math.cos(a)                     # +1 wings up, -1 down
        lag = math.cos(a - 0.9)
        return {"root": (0, 0, -22), "body": (-4, 0, 0), "@root": (0, 0, 0.06 * math.sin(a - 0.4)),
                "neck1": (58, 0, 0), "neck2": (18, 0, 0), "head": (-66, 0, 0), "jaw": (-4, 0, 0),
                "tail": (-10, 0, 0),
                "wing.L": (0, -48 * beat + 4, 0), "tip.L": (0, -26 * lag, 0),
                "wing.R": (0, 48 * beat - 4, 0), "tip.R": (0, 26 * lag, 0),
                "thigh.L": (70, 0, 0), "shin.L": (30, 0, 0), "foot.L": (70, 0, 0),
                "thigh.R": (74, 0, 0), "shin.R": (26, 0, 0), "foot.R": (66, 0, 0)}
    rig.action("fly", {i: fly(i / 20) for i in range(21)}, loop=True)

    rest = merge(G_FOLD, {"neck1": (6, 0, 0), "neck2": (-4, 0, 0), "head": (-4, 0, 0)})
    wind = merge(mirror({"wing.L": (-80, -20, 70), "tip.L": (0, 0, 6)}),
                 {"body": (-12, 0, 0), "neck1": (-18, 0, 0), "neck2": (-10, 0, 0), "head": (10, 0, 0), "@body": (0, 0.03, 0)})
    honk = merge(mirror({"wing.L": (-75, -40, 55), "tip.L": (0, -20, 10)}),
                 {"body": (10, 0, 0), "neck1": (40, 0, 0), "neck2": (8, 0, 0), "head": (-40, 0, 0), "jaw": (-32, 0, 0),
                  "@body": (0, -0.03, 0), "tail": (-10, 0, 0)})
    honk2 = merge(honk, {"jaw": (-24, 0, 0), "head": (-36, 0, 0)})
    rig.action("honk", {0: rest, 5: wind, 9: honk, 14: honk2, 18: honk, 24: rest})



# ------------------------------------------------------------------ the goose's cage

def cage():
    """2 wide, 2.5 tall, 1.4 deep; origin at the bottom centre; the floor (straw) top at 0.12. Child "door" (the whole
    front, wire in a frame) hinged on the right post, animation "open" (0.7 s): it bursts open towards the camera."""
    wood = mat("cage_wood", (0.62, 0.4, 0.2), 0.75)
    dark = mat("cage_wood_dark", (0.42, 0.25, 0.12), 0.8)
    roof_m = mat("cage_roof", (0.78, 0.2, 0.14), 0.7)
    wire = mat("cage_wire", (0.62, 0.62, 0.64), 0.55, 0.4)
    iron = mat("cage_iron", (0.2, 0.2, 0.22), 0.45, 0.7)
    brass = mat("cage_brass", (0.95, 0.72, 0.3), 0.3, 0.9)
    straw = mat("cage_straw", (0.95, 0.78, 0.36), 0.85)
    straw2 = mat("cage_straw_dark", (0.8, 0.6, 0.24), 0.85)
    parts = [box((2.0, 1.4, 0.1), (0, 0, 0.05), dark, bevel=0.02)]
    for x in (-0.95, 0.95):
        for y in (-0.65, 0.65):
            parts.append(box((0.12, 0.12, 2.1), (x, y, 1.1), wood, bevel=0.02))
    for y in (-0.65, 0.65):
        parts.append(box((2.02, 0.13, 0.12), (0, y, 2.1), wood, bevel=0.02))
        parts.append(box((2.02, 0.13, 0.1), (0, y, 0.15), wood, bevel=0.02))
    for x in (-0.95, 0.95):
        parts.append(box((0.13, 1.42, 0.12), (x, 0, 2.1), wood, bevel=0.02))
    # the back wall of boards
    for k in range(9):
        x = -0.84 + 0.21 * k
        parts.append(box((0.2, 0.04, 1.9), (x, 0.66, 1.1), dark if k % 3 == 1 else wood, bevel=0.012))
    # side walls of wire
    for x in (-0.965, 0.965):
        for k in range(8):
            y = -0.52 + 0.15 * k
            parts.append(cyl(0.01, 1.9, (x, y, 1.12), wire, verts=6))
        for k in range(12):
            z = 0.25 + 0.155 * k
            parts.append(cyl(0.01, 1.3, (x, 0, z), wire, rot=(R90, 0, 0), verts=6))
    # the roof: a red gable over the top, a ridge beam, the eaves overhanging
    for s_ in (-1, 1):
        a = math.atan2(0.36, 1.12)
        parts.append(box((1.2, 1.6, 0.07), (s_ * 0.56, 0, 2.34), roof_m, rot=(0, s_ * a, 0), bevel=0.02))
        for k in range(5):
            parts.append(box((0.04, 1.62, 0.02), (s_ * (0.12 + 0.21 * k), 0, 2.2 + 0.36 * (1 - (0.12 + 0.21 * k) / 1.12) + 0.03),
                             dark, rot=(0, s_ * a, 0), bevel=0.006))
    parts.append(cyl(0.06, 1.66, (0, 0, 2.53), dark, rot=(R90, 0, 0), verts=10))
    # the gable's front triangle (boards)
    parts.append(prism([(-1.0, 2.16), (1.0, 2.16), (0.0, 2.48)], 0.05, (0, -0.72, 0), wood, bevel=0.01))
    # straw on the floor
    rnd = random.Random(40)
    for k in range(60):
        x, y = rnd.uniform(-0.85, 0.85), rnd.uniform(-0.55, 0.55)
        a = rnd.uniform(0, math.pi)
        L = rnd.uniform(0.12, 0.25)
        parts.append(rod((x - math.cos(a) * L / 2, y - math.sin(a) * L / 2, 0.11 + rnd.uniform(0, 0.02)),
                         (x + math.cos(a) * L / 2, y + math.sin(a) * L / 2, 0.11 + rnd.uniform(0, 0.03)), 0.008,
                         straw if k % 3 else straw2, verts=5))
    for x, y in ((-0.7, 0.4), (0.72, 0.45), (-0.2, 0.52)):
        parts.append(lumpy(0.16, (x, y, 0.12), straw, int(x * 100 + 300), 0.25, scale=(1.3, 0.8, 0.5)))
    body = join(parts, "cage")
    # the door: the front frame with wire, a Z brace, hinges and a padlock; origin on the hinge (right post)
    HX, HY = 0.89, -0.73
    dp = [box((1.78, 0.06, 0.1), (0, HY, 0.24), wood, bevel=0.015), box((1.78, 0.06, 0.1), (0, HY, 2.0), wood, bevel=0.015),
          box((0.1, 0.06, 1.86), (-0.84, HY, 1.12), wood, bevel=0.015), box((0.1, 0.06, 1.86), (0.84, HY, 1.12), wood, bevel=0.015),
          box((0.08, 0.05, 2.1), (0, HY - 0.01, 1.12), wood, rot=(0, math.atan2(1.6, 1.7), 0), bevel=0.012)]
    for k in range(11):
        x = -0.75 + 0.15 * k
        dp.append(cyl(0.011, 1.72, (x, HY + 0.01, 1.12), wire, verts=6))
    for k in range(11):
        z = 0.36 + 0.155 * k
        dp.append(cyl(0.011, 1.62, (0, HY + 0.01, z), wire, rot=(0, R90, 0), verts=6))
    for z in (0.5, 1.75):
        dp.append(box((0.28, 0.07, 0.06), (0.72, HY - 0.02, z), iron, bevel=0.01))
        dp.append(cyl(0.03, 0.14, (HX, HY, z), iron, verts=10))
    dp.append(box((0.12, 0.05, 0.1), (-0.82, HY - 0.05, 1.12), brass, bevel=0.015))
    dp.append(torus(0.04, 0.012, (-0.82, HY - 0.05, 1.19), iron, rot=(R90, 0, 0), verts=12, minor=4))
    door = join(dp, "door", pivot=(HX, HY, 0.0))
    animate(door, "open", {0: {"rot": (0, 0, 0)}, 3: {"rot": (0, 0, math.radians(-4))},
                           10: {"rot": (0, 0, math.radians(128))}, 15: {"rot": (0, 0, math.radians(104))},
                           21: {"rot": (0, 0, math.radians(115))}}, linear=False)
    export_anim(body, "cage", [(door, body)])


# ------------------------------------------------------------------ items

def egg():
    """A brown egg in a little straw nest, 0.3 across, origin at the base; the egg's top is 0.2 up."""
    shell = mat("egg_shell", (0.9, 0.6, 0.36), 0.3, coat=0.6)
    speck = mat("egg_speck", (0.6, 0.32, 0.16), 0.4)
    straw = mat("nest_straw", (0.95, 0.78, 0.36), 0.85)
    straw2 = mat("nest_straw_dark", (0.74, 0.54, 0.22), 0.85)
    parts = [torus(0.1, 0.045, (0, 0, 0.045), straw2, verts=20, minor=8, scale=(1, 1, 0.8)),
             cyl(0.1, 0.03, (0, 0, 0.02), straw2, verts=16)]
    rnd = random.Random(7)
    for k in range(34):
        a = 2 * math.pi * k / 34 + rnd.uniform(-0.1, 0.1)
        r = 0.1 + rnd.uniform(-0.02, 0.03)
        t = a + math.pi / 2 + rnd.uniform(-0.5, 0.5)
        L = rnd.uniform(0.06, 0.1)
        c = Vector((r * math.cos(a), r * math.sin(a), 0.04 + rnd.uniform(0.0, 0.05)))
        d = Vector((math.cos(t), math.sin(t), rnd.uniform(-0.3, 0.3))) * L / 2
        parts.append(rod(c - d, c + d, 0.007, straw if k % 3 else straw2, verts=5))
    o = sphere(0.088, (0, 0, 0), shell, scale=(1, 1, 1.3), segs=20, rings=14)
    for v in o.data.vertices:            # egg-shaped: fuller at the bottom
        if v.co.z < 0:
            v.co.x *= 1.06
            v.co.y *= 1.06
    o.data.transform(Matrix.Rotation(0.18, 4, "Y"))
    o.data.transform(Matrix.Translation((0, 0, 0.125)))
    parts.append(o)
    for k in range(9):
        a = rnd.uniform(-1.8, 0.8)
        b = rnd.uniform(-0.3, 1.0)
        p = Vector((0.09 * math.cos(b) * math.sin(a), -0.09 * math.cos(b) * math.cos(a), 0.125 + 0.11 * math.sin(b)))
        parts.append(sphere(0.008, tuple(p), speck, scale=(1, 1, 0.5), segs=6, rings=4))
    simple(parts, "egg")


def grain():
    """A heap of golden corn, 0.4 wide and 0.17 tall, with a smaller heap beside it and strays; origin at the base
    centre of the big heap."""
    seed = mat("grain_seed", (1.0, 0.76, 0.2), 0.5, coat=0.2)
    seed2 = mat("grain_seed_dark", (0.9, 0.55, 0.12), 0.5)
    parts = [lumpy(0.13, (0.0, 0.0, 0.0), seed, 71, 0.08, scale=(1.35, 0.95, 1.3), sub=2, smooth=60),
             lumpy(0.08, (0.14, 0.04, 0.0), seed, 72, 0.1, scale=(1.1, 1.0, 0.8), sub=2, smooth=60)]
    for o in parts:              # heaps sit on the ground: nothing below it
        edit(o, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context="VERTS"))
    rnd = random.Random(8)
    for k in range(70):          # kernels over the heap's surface
        a = rnd.uniform(0, 2 * math.pi)
        b = rnd.uniform(0.0, 1.3)
        p = Vector((0.175 * math.cos(b) * math.cos(a), 0.123 * math.cos(b) * math.sin(a), 0.17 * math.sin(b)))
        if p.y > 0.08 and p.x > 0.05:
            continue
        parts.append(sphere(0.016, tuple(p), seed if k % 3 else seed2, scale=(1, 0.8, 0.7), segs=6, rings=4))
    for k in range(10):          # a few strays on the ground
        a = rnd.uniform(-2.6, -0.5)
        r = rnd.uniform(0.19, 0.24)
        parts.append(sphere(0.014, (r * math.cos(a), 0.7 * r * math.sin(a), 0.008), seed2, scale=(1, 0.8, 0.6), segs=6,
                            rings=4))
    simple(parts, "grain")


def lift():
    """A wooden pallet 1.5 wide, 0.5 deep hung on ropes; origin at the TOP centre of the deck (stand things at y = 0).
    Two ropes rise at the back corners to a spreader bar 1.45 up and a ring at 1.7; child "rope" (origin at the ring,
    1 unit long going up: scale its Y to the length needed)."""
    wood = mat("lift_wood", (0.78, 0.56, 0.3), 0.75)
    dark = mat("lift_wood_dark", (0.55, 0.36, 0.17), 0.8)
    rope_m = mat("lift_rope", (0.88, 0.76, 0.5), 0.9)
    iron = mat("lift_iron", (0.25, 0.25, 0.27), 0.4, 0.7)
    parts = []
    for k in range(5):
        x = -0.6 + 0.3 * k
        parts.append(box((0.27, 0.52, 0.035), (x, 0, -0.0175), wood if k % 2 else dark, bevel=0.008))
    for y in (-0.2, 0.2):
        parts.append(box((1.5, 0.08, 0.1), (0, y, -0.085), dark, bevel=0.012))
    for x in (-0.66, 0, 0.66):
        parts.append(box((0.12, 0.5, 0.05), (x, 0, -0.16), wood, bevel=0.01))
        for y in (-0.2, 0.2):
            parts.append(sphere(0.012, (x, y - 0.045, -0.085), iron, segs=6, rings=4))
    for s_ in (-1, 1):
        parts.append(torus(0.04, 0.014, (s_ * 0.7, 0.2, 0.03), rope_m, rot=(R90, 0, 0), verts=12, minor=5))
        parts.append(cyl(0.018, 1.4, (s_ * 0.7, 0.2, 0.75), rope_m, verts=8))
        parts.append(rod((s_ * 0.7, 0.2, 1.47), (0, 0.2, 1.68), 0.016, rope_m, verts=8))
    parts.append(cyl(0.035, 1.55, (0, 0.2, 1.47), dark, rot=(0, R90, 0), verts=10))
    parts.append(torus(0.045, 0.014, (0, 0.2, 1.72), iron, rot=(R90, 0, 0), verts=14, minor=5))
    body = join(parts, "lift")
    r = join([cyl(0.018, 1.0, (0, 0.2, 1.77 + 0.5), rope_m, verts=8)], "rope", pivot=(0, 0.2, 1.77))
    export_anim(body, "lift", [(r, body)], anim=False)


# ------------------------------------------------------------------ level pieces (1 tile = 0.5)

def brick():
    """A 0.5 x 0.5 x 0.5 block (origin at the centre) of warm red farm brick: three courses, staggered, full depth
    (the ends show at a platform's edge), mortar behind; child "brick_top" (the grass on top and tufts over the front
    edge, top at +0.28): hide it when another block sits above."""
    face = mat("brick_face", (0.74, 0.3, 0.19), 0.8)
    mortar = mat("brick_mortar", (0.86, 0.76, 0.6), 0.95)
    grass = mat("brick_top", (0.42, 0.66, 0.2), 0.8)
    grass2 = mat("brick_top_dark", (0.28, 0.5, 0.14), 0.8)
    flower = mat("brick_flower", (1.0, 0.95, 0.8), 0.6)
    heart = mat("brick_flower_heart", (1.0, 0.75, 0.15), 0.5)
    h = 0.5 / 3
    g = 0.014
    parts = [box((0.49, 0.48, 0.49), (0, 0.005, 0), mortar, bevel=0.01)]
    rnd = random.Random(3)
    for row in range(3):
        z0 = -0.25 + row * h
        edges = [-0.25, 0.0, 0.25] if row % 2 == 0 else [-0.25, -0.125, 0.125, 0.25]
        for a, b in zip(edges, edges[1:]):
            x0 = a + (g / 2 if a > -0.25 else 0.0)
            x1 = b - (g / 2 if b < 0.25 else 0.0)
            o = box((x1 - x0, 0.5, h - g), ((x0 + x1) / 2, 0.0, z0 + h / 2), face, bevel=0.012)
            for v in o.data.vertices:
                if v.co.y < 0:
                    v.co.y += rnd.uniform(-0.004, 0.004)
                    v.co.z += rnd.uniform(-0.002, 0.002)
            parts.append(o)
    body = join(parts, "brick")
    tp = [box((0.5, 0.5, 0.03), (0, 0, 0.26), grass, bevel=0.01)]
    for k in range(10):
        x = -0.25 + (k + 0.5) * 0.05 + rnd.uniform(-0.008, 0.008)
        # a rounded clump of grass rolling over the front edge, a few thin blades poking up
        tp.append(sphere(rnd.uniform(0.03, 0.038), (x, -0.235, 0.265), grass2 if k % 2 else grass,
                         scale=(1.0, 0.75, 0.75), segs=10, rings=6))
        if k % 3 == 0:
            for j in (-1, 1):
                hgt = rnd.uniform(0.05, 0.08)
                tp.append(rod((x + 0.01 * j, -0.22, 0.27), (x + 0.03 * j, -0.24, 0.27 + hgt), 0.008, grass, r2=0.001,
                              verts=4))
    for x in (-0.12, 0.15):
        if rnd.random() < 0.9:
            for k in range(5):
                a = 2 * math.pi * k / 5
                tp.append(sphere(0.012, (x + 0.014 * math.cos(a), -0.2, 0.3 + 0.014 * math.sin(a)), flower,
                                 scale=(1, 0.4, 1), segs=6, rings=4))
            tp.append(sphere(0.009, (x, -0.207, 0.3), heart, segs=6, rings=4))
            tp.append(rod((x, -0.2, 0.27), (x, -0.2, 0.3), 0.004, grass2, verts=4))
    top = join(tp, "brick_top")
    export_anim(body, "brick", [(top, body)], anim=False)


def ladder():
    """A 0.5 wide ladder segment, 0.5 tall (two rungs), origin at the bottom centre, front towards the camera (depth
    -0.035 .. +0.03). Stack segments every 0.5."""
    wood = mat("ladder_wood", (0.82, 0.6, 0.32), 0.7)
    dark = mat("ladder_wood_dark", (0.6, 0.4, 0.18), 0.75)
    rope = mat("ladder_rope", (0.9, 0.8, 0.55), 0.9)
    parts = []
    for x in (-0.2, 0.2):
        parts.append(box((0.055, 0.06, 0.5), (x, 0.0, 0.25), wood, bevel=0.012))
    for z in (0.125, 0.375):
        parts.append(cyl(0.022, 0.46, (0, -0.012, z), dark, rot=(0, R90, 0), verts=10))
        for x in (-0.2, 0.2):
            parts.append(torus(0.036, 0.009, (x, -0.012, z), rope, rot=(0.6, 0, 0), verts=10, minor=4))
    simple(parts, "ladder")



# ------------------------------------------------------------------ farmyard backdrop (origin at the base centre,
# front towards the camera; put them behind the play plane)

def bg_barn():
    """A big red barn, 4.0 wide, 4.1 tall to the ridge (4.6 with the weather vane), 2.4 deep: a gambrel roof, white
    trim, X-braced doors, a hay loft with hay poking out, a lit window (bg_barn_glow)."""
    red = mat("bg_barn_red", (0.72, 0.16, 0.1), 0.8)
    red2 = mat("bg_barn_red_dark", (0.55, 0.11, 0.07), 0.8)
    trim = mat("bg_barn_trim", (0.97, 0.94, 0.86), 0.7)
    roof = mat("bg_barn_roof", (0.36, 0.3, 0.3), 0.75)
    dark = mat("bg_barn_dark", (0.16, 0.08, 0.05), 0.9)
    hay = mat("bg_hay", (0.97, 0.8, 0.38), 0.85)
    glow = mat("bg_barn_glow", (1.0, 0.72, 0.35), 0.5, emit=2.5)
    iron = mat("bg_barn_iron", (0.2, 0.2, 0.22), 0.4, 0.7)
    W, D, Hw = 4.0, 2.4, 2.3
    prof = [(-2.0, 0.0), (2.0, 0.0), (2.0, Hw), (1.45, 3.35), (0.0, 4.1), (-1.45, 3.35), (-2.0, Hw)]
    parts = [prism(prof, D, (0, 0.2, 0), red, bevel=0.02)]
    # boards: vertical grooves on the front
    for k in range(19):
        x = -1.8 + 0.2 * k
        top = Hw if abs(x) > 1.45 else (Hw + (3.35 - Hw) * (2.0 - abs(x)) / 0.55 if abs(x) > 1.45 else
                                        3.35 + (4.1 - 3.35) * (1.45 - abs(x)) / 1.45)
        parts.append(box((0.025, 0.02, top - 0.1), (x, -1.0, (top - 0.1) / 2 + 0.05), red2, bevel=0.005))
    # the gambrel roof: four slabs over the profile, overhanging
    for (x0, z0), (x1, z1) in (((-2.15, Hw - 0.1), (-1.45, 3.37)), ((-1.45, 3.37), (0.0, 4.12)),
                               ((0.0, 4.12), (1.45, 3.37)), ((1.45, 3.37), (2.15, Hw - 0.1))):
        L = math.hypot(x1 - x0, z1 - z0)
        a = math.atan2(z1 - z0, x1 - x0)
        parts.append(box((L + 0.08, D + 0.4, 0.12), ((x0 + x1) / 2, 0.2, (z0 + z1) / 2 + 0.06), roof,
                         rot=(0, -a, 0), bevel=0.03))
    # white trim round the gable edge and the corners
    edge = [(-2.0, Hw), (-1.45, 3.35), (0.0, 4.1), (1.45, 3.35), (2.0, Hw)]
    for (x0, z0), (x1, z1) in zip(edge, edge[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        a = math.atan2(z1 - z0, x1 - x0)
        parts.append(box((L + 0.1, 0.06, 0.12), ((x0 + x1) / 2, -1.02, (z0 + z1) / 2 - 0.02), trim, rot=(0, -a, 0),
                         bevel=0.015))
    for x in (-1.98, 1.98):
        parts.append(box((0.14, 0.06, Hw), (x, -1.02, Hw / 2), trim, bevel=0.015))
    # the big doors, with white frames and X braces, one ajar showing the dark inside
    parts.append(box((1.9, 0.05, 1.75), (0, -1.0, 0.875), dark, bevel=0.01))
    for x in (-0.48, 0.52):
        cx = x
        parts.append(box((0.9, 0.08, 1.7), (cx, -1.05 if x < 0 else -1.12, 0.85), red, bevel=0.015))
        fr = [((0.9, 0.1, 0.1), (cx, 0.0, 0.05 + 1.6)), ((0.9, 0.1, 0.1), (cx, 0.0, 0.1)),
              ((0.1, 0.1, 1.7), (cx - 0.4, 0.0, 0.85)), ((0.1, 0.1, 1.7), (cx + 0.4, 0.0, 0.85)),
              ((0.9, 0.1, 0.08), (cx, 0.0, 0.85))]
        y = -1.1 if x < 0 else -1.17
        for sz, (px, _, pz) in fr:
            parts.append(box(sz, (px, y, pz), trim, bevel=0.012))
        for z0, z1 in ((0.12, 0.85), (0.85, 1.6)):
            L = math.hypot(0.8, z1 - z0)
            for sgn in (-1, 1):
                parts.append(box((L, 0.1, 0.07), (cx, y, (z0 + z1) / 2), trim, rot=(0, sgn * math.atan2(z1 - z0, 0.8), 0),
                                 bevel=0.01))
    parts.append(cyl(0.04, 2.1, (0, -1.2, 1.82), iron, rot=(0, R90, 0), verts=8))
    # the hay loft: a door frame, hay spilling out, a hoist beam
    parts.append(box((0.9, 0.06, 0.8), (0, -1.02, 2.95), dark, bevel=0.01))
    for sz, pos in (((1.05, 0.1, 0.12), (0, -1.06, 3.38)), ((1.05, 0.1, 0.12), (0, -1.06, 2.52)),
                    ((0.12, 0.1, 0.96), (-0.48, -1.06, 2.95)), ((0.12, 0.1, 0.96), (0.48, -1.06, 2.95))):
        parts.append(box(sz, pos, trim, bevel=0.012))
    for k in range(6):
        parts.append(lumpy(0.2, (-0.3 + 0.12 * k, -1.02, 2.62 + 0.05 * (k % 2)), hay, 50 + k, 0.2, scale=(1.2, 0.8, 0.8)))
    parts.append(box((0.12, 0.9, 0.12), (0, -1.3, 3.6), dark, bevel=0.02))
    # a round window up in the gable end, warmly lit
    parts.append(torus(0.2, 0.05, (0, -1.03, 3.72), trim, rot=(R90, 0, 0), verts=20, minor=6))
    parts.append(cyl(0.19, 0.04, (0, -1.0, 3.72), glow, rot=(R90, 0, 0), verts=20))
    for a in (0, R90):
        parts.append(box((0.38, 0.05, 0.03), (0, -1.04, 3.72), trim, rot=(0, a, 0), bevel=0.005))
    # side windows (visible when the barn is turned)
    for y in (-0.3, 0.7):
        parts.append(box((0.06, 0.5, 0.5), (2.0, y, 1.5), glow, bevel=0.01))
        parts.append(box((0.08, 0.62, 0.1), (2.02, y, 1.78), trim, bevel=0.01))
    # the weather vane: a little cockerel on an arrow
    parts.append(cyl(0.02, 0.5, (0, 0.2, 4.35), iron, verts=6))
    parts.append(box((0.6, 0.02, 0.03), (0, 0.2, 4.45), iron, bevel=0.0))
    parts.append(prism([(-0.14, 0.0), (0.12, 0.0), (0.16, 0.12), (0.1, 0.2), (0.12, 0.28), (0.06, 0.24), (-0.02, 0.1),
                        (-0.16, 0.2)], 0.02, (0, 0.2, 4.5), iron, bevel=0.0))
    simple(parts, "bg_barn")


def bg_silo():
    """A grain silo 1.5 across, 5.2 tall with its dome: ribbed metal bands, a ladder cage, a little vent."""
    metal = mat("bg_silo_metal", (0.78, 0.8, 0.82), 0.4, 0.6)
    band = mat("bg_silo_band", (0.6, 0.62, 0.66), 0.4, 0.7)
    roof = mat("bg_silo_roof", (0.72, 0.2, 0.12), 0.6)
    base = mat("bg_silo_base", (0.62, 0.56, 0.5), 0.9)
    parts = [cyl(0.8, 0.3, (0, 0, 0.15), base, verts=28, bevel=0.03),
             cyl(0.72, 4.0, (0, 0, 2.3), metal, verts=32)]
    for k in range(9):
        parts.append(torus(0.725, 0.02, (0, 0, 0.5 + 0.45 * k), band, verts=32, minor=4))
    dome = sphere(0.76, (0, 0, 4.3), roof, scale=(1, 1, 0.6), segs=32, rings=16)
    edit(dome, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 4.28], context="VERTS"))
    parts.append(dome)
    parts.append(cyl(0.12, 0.3, (0, 0, 4.85), band, r2=0.08, verts=12))
    parts.append(sphere(0.14, (0, 0, 5.05), roof, scale=(1, 1, 0.5), segs=12, rings=6))
    # the ladder up the front, slightly to one side
    for x in (0.18, 0.4):
        parts.append(cyl(0.02, 4.0, (x, -0.72, 2.3), band, verts=6))
    for k in range(18):
        parts.append(cyl(0.012, 0.22, (0.29, -0.73, 0.5 + 0.22 * k), band, rot=(0, R90, 0), verts=5))
    simple(parts, "bg_silo")


def bg_fence():
    """A rail fence 2 long (x -1 .. 1), 0.95 tall: posts at x = -0.5 and +0.5, three rails; tiles every 2.0."""
    wood = mat("bg_fence_wood", (0.72, 0.5, 0.28), 0.8)
    dark = mat("bg_fence_wood_dark", (0.52, 0.34, 0.17), 0.85)
    rnd = random.Random(12)
    parts = []
    for x in (-0.5, 0.5):
        parts.append(box((0.13, 0.13, 0.95), (x, 0, 0.475), dark, rot=(0, rnd.uniform(-0.03, 0.03), 0), bevel=0.02))
        parts.append(cyl(0.075, 0.08, (x, 0, 0.98), dark, r2=0.02, verts=4, rot=(0, 0, math.pi / 4)))
    for z in (0.3, 0.58, 0.84):
        parts.append(box((2.0, 0.06, 0.1), (0, -0.1, z + rnd.uniform(-0.02, 0.02)), wood,
                         rot=(0, rnd.uniform(-0.02, 0.02), 0), bevel=0.015))
    # grass at the post feet
    for x in (-0.5, 0.5):
        for k in range(5):
            a = rnd.uniform(-0.5, 0.5)
            parts.append(rod((x + 0.05 * math.sin(k), -0.08, 0.0), (x + 0.05 * math.sin(k) + a * 0.15, -0.1, 0.18),
                             0.02, mat("bg_grass", (0.4, 0.62, 0.2), 0.8), r2=0.002, verts=4))
    simple(parts, "bg_fence")


def bg_haybale():
    """A round bale 1.1 across, 1.0 wide, lying with a rolled face towards the camera; origin at the base."""
    hay = mat("bg_hay", (0.97, 0.8, 0.38), 0.85)
    hay2 = mat("bg_hay_dark", (0.82, 0.62, 0.26), 0.85)
    parts = [cyl(0.55, 1.0, (0, 0, 0.55), hay, rot=(R90, 0, 0), verts=32, bevel=0.08, segs=3)]
    # the spiral on the face
    pts = []
    for k in range(80):
        t = k / 79
        a = t * 2 * math.pi * 3.2
        r = 0.05 + 0.44 * t
        pts.append((r * math.cos(a), -0.5, 0.55 + r * math.sin(a)))
    parts.append(tube(pts, [0.012] * len(pts), hay2, verts=5))
    rnd = random.Random(21)
    for k in range(40):       # loose strands
        a = rnd.uniform(0, 2 * math.pi)
        y = rnd.uniform(-0.45, 0.45)
        c = Vector((0.56 * math.cos(a), y, 0.55 + 0.56 * math.sin(a)))
        d = Vector((-math.sin(a), rnd.uniform(-0.4, 0.4), math.cos(a))) * rnd.uniform(0.08, 0.16)
        parts.append(rod(c, c + d, 0.007, hay2 if k % 2 else hay, verts=4))
    for k in range(3):        # twine bands
        parts.append(torus(0.56, 0.008, (0, -0.3 + 0.3 * k, 0.55), hay2, rot=(R90, 0, 0), verts=32, minor=4))
    simple(parts, "bg_haybale")


def bg_tree():
    """A round apple tree 4.2 tall, 3.2 wide: a crooked trunk, a lumpy canopy, red apples."""
    bark = mat("bg_tree_bark", (0.42, 0.28, 0.17), 0.9)
    leaf = mat("bg_tree_leaf", (0.36, 0.6, 0.2), 0.8)
    leaf2 = mat("bg_tree_leaf_light", (0.55, 0.74, 0.26), 0.8)
    leaf3 = mat("bg_tree_leaf_dark", (0.22, 0.42, 0.14), 0.85)
    apple = mat("bg_tree_apple", (0.85, 0.12, 0.08), 0.4, coat=0.5)
    parts = [tube([(0, 0, 0), (0.05, 0, 0.8), (-0.05, 0, 1.6), (0.05, 0, 2.3)], [0.26, 0.2, 0.17, 0.12], bark, verts=12)]
    for a, L in ((0.8, 0.9), (-0.9, 0.8), (0.1, 0.8)):
        parts.append(rod((0, 0, 1.8), (math.sin(a) * L, 0, 1.8 + math.cos(a) * L), 0.09, bark, r2=0.05, verts=8))
    parts += [lumpy(0.3, (0.15 * s_, -0.05, 0.05), bark, 30 + s_, 0.2, scale=(1.4, 1.0, 0.4)) for s_ in (-1, 1)]
    rnd = random.Random(33)
    blobs = [((0, 0, 3.0), 1.2), ((-0.9, 0.1, 2.6), 0.85), ((0.95, 0.1, 2.65), 0.85), ((-0.4, -0.3, 3.5), 0.75),
             ((0.5, -0.25, 3.45), 0.75), ((0.0, -0.4, 2.5), 0.8)]
    for k, (c, r) in enumerate(blobs):
        parts.append(lumpy(r, c, leaf, 60 + k, 0.1, sub=2, smooth=60, scale=(1.0, 0.8, 0.9)))
        # a lighter cap on top of each blob (the sun) and a darker belly
        parts.append(lumpy(r * 0.7, (c[0] - 0.1, c[1] - 0.15, c[2] + r * 0.35), leaf2, 70 + k, 0.1, sub=2, smooth=60,
                           scale=(1.0, 0.8, 0.7)))
        parts.append(lumpy(r * 0.8, (c[0], c[1] + 0.1, c[2] - r * 0.3), leaf3, 80 + k, 0.1, sub=2, smooth=60,
                           scale=(1.0, 0.8, 0.7)))
    for k in range(12):
        c, r = blobs[k % len(blobs)]
        a, b = rnd.uniform(-1.4, 1.4), rnd.uniform(-0.6, 0.5)
        p = Vector(c) + Vector((r * math.sin(a) * math.cos(b), -r * 0.8 * math.cos(a) * math.cos(b), r * 0.9 * math.sin(b)))
        parts.append(sphere(0.09, tuple(p + Vector((0, -0.04, 0))), apple, segs=10, rings=6))
    simple(parts, "bg_tree")


def bg_windmill():
    """A little white tower mill, 5.4 tall to the cap (6.9 to the top sail tip): a tapered tower with a door and
    windows, a brown cap; child "blades" (four lattice sails 3 long, hub at (0, 4.9, +0.8) in Godot, facing the
    camera) with an animation "turn" (loop 4 s, one turn anticlockwise as seen from the camera)."""
    wall = mat("bg_mill_wall", (0.96, 0.92, 0.84), 0.85)
    base = mat("bg_mill_base", (0.62, 0.56, 0.5), 0.9)
    cap = mat("bg_mill_cap", (0.5, 0.3, 0.16), 0.75)
    wood = mat("bg_mill_wood", (0.45, 0.3, 0.18), 0.75)
    sail = mat("bg_mill_sail", (0.98, 0.93, 0.8), 0.9)
    win = mat("bg_mill_window", (1.0, 0.75, 0.38), 0.5, emit=2.0)
    trim = mat("bg_mill_trim", (0.2, 0.36, 0.5), 0.7)
    parts = [lathe_r([(0.0, 4.6), (0.92, 4.6), (1.1, 0.45), (1.12, 0.0), (0.0, 0.0)], wall, segs=28),
             cyl(1.2, 0.45, (0, 0, 0.22), base, verts=28, bevel=0.03),
             torus(0.95, 0.06, (0, 0, 4.6), wood, verts=28, minor=5)]
    capo = sphere(1.05, (0, 0.05, 4.6), cap, scale=(1, 1.1, 0.85), segs=28, rings=14)
    edit(capo, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 4.58], context="VERTS"))
    parts.append(capo)
    parts.append(sphere(0.12, (0, 0.05, 5.5), wood, segs=10, rings=6))
    # a door and two windows on the front, with blue trim and a little balcony rail
    parts.append(box((0.6, 0.1, 1.0), (0, -1.1, 0.95), wood, bevel=0.02))
    parts.append(box((0.74, 0.08, 0.1), (0, -1.12, 1.5), trim, bevel=0.015))
    for z in (2.3, 3.5):
        parts.append(box((0.36, 0.1, 0.44), (0, -1.06 + (z - 0.45) * 0.045, z), win, bevel=0.02))
        parts.append(box((0.48, 0.1, 0.07), (0, -1.08 + (z - 0.45) * 0.045, z - 0.26), trim, bevel=0.01))
    parts.append(box((0.3, 0.9, 0.3), (0, -0.6, 4.9), cap, bevel=0.05))       # the windshaft housing
    body = join(parts, "bg_windmill")
    # the sails
    sp = [cyl(0.2, 0.3, (0, -1.15, 4.9), wood, rot=(R90, 0, 0), verts=16, bevel=0.03),
          sphere(0.14, (0, -1.32, 4.9), cap, segs=12, rings=8)]
    for k in range(4):
        a = k * R90 + 0.3
        M = Matrix.Translation((0, -1.2, 4.9)) @ Matrix.Rotation(a, 4, "Y")
        loc = [box((0.1, 0.06, 3.0), (0, 0, 1.55), wood, bevel=0.015)]
        for j in range(8):
            loc.append(box((0.62, 0.04, 0.04), (0.28, 0.02, 0.5 + 0.34 * j), wood, bevel=0.006))
        loc.append(box((0.04, 0.04, 2.5), (0.58, 0.02, 1.75), wood, bevel=0.006))
        loc.append(box((0.5, 0.02, 2.4), (0.3, 0.035, 1.78), sail, bevel=0.004))
        for o in loc:
            o.data.transform(M)
        sp += loc
    blades = join(sp, "blades", pivot=(0, -1.2, 4.9))
    animate(blades, "turn", {0: {"rot": (0, 0, 0)}, 60: {"rot": (0, -math.pi, 0)}, 120: {"rot": (0, -2 * math.pi, 0)}},
            linear=True)
    export_anim(body, "bg_windmill", [(blades, body)])


def bg_hill():
    """A rolling hill panel 12 wide (x -6 .. 6), up to 3.2 tall, bulging 1.0 towards the camera: a patchwork of
    fields (bg_hill_grass, bg_hill_field golden wheat, bg_hill_field_light), hedgerows and little trees."""
    grass = mat("bg_hill_grass", (0.42, 0.64, 0.22), 0.9)
    field = mat("bg_hill_field", (0.95, 0.76, 0.32), 0.9)
    field2 = mat("bg_hill_field_light", (0.62, 0.78, 0.3), 0.9)
    hedge = mat("bg_hill_hedge", (0.22, 0.42, 0.14), 0.85)
    trunk = mat("bg_tree_bark", (0.42, 0.28, 0.17), 0.9)

    def top(x):
        return 2.2 + 0.7 * math.cos(x * 0.55 + 0.4) + 0.3 * math.cos(x * 1.3 + 1.0)

    NX, NZ = 150, 40
    bm = bmesh.new()
    rows = []
    for j in range(NZ + 1):
        v = j / NZ
        row = []
        for i in range(NX + 1):
            x = -6 + 12 * i / NX
            h = top(x)
            z = h * v
            y = -1.0 * math.sin(math.pi * min(1.0, v * 1.0)) * (1 - v) * 1.6 - 0.2 * math.sin(v * math.pi)
            row.append(bm.verts.new((x, y, z)))
        rows.append(row)
    for j in range(NZ):
        for i in range(NX):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            c = f.calc_center_median()
            u = c.x + 0.5 * c.z                  # slanted strips of fields
            band = int(math.floor(u / 1.6)) + int(math.floor(c.z / 0.9)) * 3
            f.material_index = [0, 1, 0, 2, 0, 2, 1][band % 7]
    me = bpy.data.meshes.new("bg_hill")
    for m_ in (grass, field, field2):
        me.materials.append(m_)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.normal_update()
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    hill = bpy.data.objects.new("bg_hill", me)
    bpy.context.scene.collection.objects.link(hill)
    K.select(hill)
    bpy.ops.object.shade_smooth()
    parts = [hill]
    # hedgerows along some field edges and a crown of little trees on the crest
    rnd = random.Random(90)
    for k in range(-4, 5):
        x0 = k * 1.6
        pts = []
        for j in range(8):
            v = j / 7 * 0.85
            z = v * top(x0 - 0.5 * v * 2.4)
            x = x0 - 0.5 * z
            if abs(x) > 5.8:
                continue
            vv = z / top(x)
            y = -1.0 * math.sin(math.pi * vv) * (1 - vv) * 1.6 - 0.2 * math.sin(vv * math.pi) - 0.05
            pts.append((x, y, z))
        for p in pts[1:]:
            parts.append(lumpy(0.13, p, hedge, rnd.randint(0, 999), 0.2, scale=(1.3, 0.8, 0.8)))
    for k in range(9):
        x = -5.2 + k * 1.3 + rnd.uniform(-0.3, 0.3)
        z = top(x) - 0.05
        parts.append(rod((x, -0.05, z - 0.1), (x, -0.05, z + 0.25), 0.04, trunk, verts=6))
        parts.append(lumpy(rnd.uniform(0.25, 0.35), (x, -0.05, z + 0.4), hedge, 400 + k, 0.15, sub=2, smooth=60))
    simple(parts, "bg_hill")


JOBS = {"farmhand": farmhand, "hen": hen, "goose": goose, "cage": cage, "egg": egg, "grain": grain,
        "lift": lift, "brick": brick, "ladder": ladder, "bg_barn": bg_barn, "bg_silo": bg_silo, "bg_fence": bg_fence,
        "bg_haybale": bg_haybale, "bg_tree": bg_tree, "bg_windmill": bg_windmill, "bg_hill": bg_hill}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            clear_all()
            fn()
