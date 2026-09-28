"""Deep Breath (game 21) models: the miner (on the shared humanoid rig), six guardians, the cavern tiles and
hazards, the crystal key, the exit lift and a backdrop kit for themed caverns (a cosy-spooky mining diorama).
Original designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets (the belt
texture is generated here too).
Run: blender -b --factory-startup -P tools/blender/deepbreath_models.py -- godot/games/deepbreath/art/models [name ...]
Helpers come from humanoid.py (the 26-bone rig, smooth skin, IK poses, gait), relic_models.py (P, cycle, slim,
air_legs, gear), blastyard_models.py (mat, box, cyl, ...), blastyard_bombers.py and hopline_models.py (Rig,
TurnRig), prism_models.py (animate, empty, edit) and mossfolk_models.py (lumpy, lathe_r, solid). 30 fps.

Axes: Blender Z up, the camera side is -Y; in Godot +X stays +X, Blender +Z is +Y (up), Blender -Y is +Z (towards the
camera). 1 tile = 0.5 units; everything is at game size (node scale 1) except the miner, built 1.7 tall. Characters
face Godot +X (turned towards the camera where a face must read); mirror with scale.x = -1. Origins at the feet /
base centre unless noted. Animations marked * are seamless loops: set their loop mode in the game.
Emissive materials all have "glow" in their names.

miner.glb     armature "miner_rig" (26 bones, see humanoid.py), skinned mesh "miner", and "lamp" (an empty on the head
              bone, at the lamp's lens: (0.20, 1.63, 0.11) at rest, node scale 1). The lamp's local -Z points along
              +X, 8 degrees down, at rest and follows the head (idle sweeps it): add a SpotLight3D as its child with
              an identity transform. A stocky miner in an ochre hard hat with a brass lamp (miner_lamp_glow), walrus
              moustache, blue neckerchief, red shirt with rolled sleeves, green braces, patched moleskins, leather
              gloves, steel-capped boots, and an oxygen canister on his back with a valve wheel, a hose over the right
              shoulder and a gauge on its camera-side flank (miner_gauge_glow dial, red needle). Facing +X turned 28
              degrees to the camera. 1.70 tall at node scale 1: scale by 1 / 1.7 = 0.588 for 2 tiles. Materials
              miner_skin, _cheek, _eye_white, _iris, _hair, _moustache, _lips, _shirt, _shirt_dark, _braces,
              _trousers, _patch, _stitch, _glove, _leather, _boots, _sole, _steel, _brass, _helmet, _helmet_dark,
              _scarf, _scarf_dot, _tank (recolour to show air, e.g. towards red), _hose, _glass, _needle,
              miner_lamp_glow, miner_gauge_glow.
              Animations (loops marked *):
                idle*   3.2 s, slow breathing, peers one way then the other (the lamp sweeps), a shrug
                walk*   0.53 s (16 frames), one stride (two steps) per cycle, in place: 1.33 model units per cycle
                        at node scale 1 = 0.78 game units at 0.588 (1.46 units/s = 2.9 tiles/s at speed_scale 1)
                jump    0.5 s, crouch, spring, a tight tuck (the body rises 0.16 and the feet lift to 0.46 at node
                        scale 1); holds the last frame: blend to fall
                fall*   0.4 s, arms flailing in circles, legs cycling
                die     1.5 s, a jolt, a dizzy spin, a wobble, the knees give and he falls flat on his face (the
                        canister on top), a bounce, a boot twitches; holds (lies from x = -0.88 to +1.10 at scale 1)
                gasp*   1.2 s, out of air: hands clutch the collar, the chest heaves, the head jerks back, knees wobble
                cheer*  1 s, two hops, fists pumping
Guardians (game size; about 1 tile wide, 1-2 tall; a looping animation "move"):
  guardian_minecart  a haunted mine cart 0.7 long (bumpers), 0.62 tall (eyes), side view: a riveted rusty tub of coal
              with ghostly green embers (minecart_glow) and two glowing slit eyes peering out (minecart_eye_glow).
              Root "guardian_minecart" with children wheel_b, wheel_f (axles 0.085 up at x -+0.17, radius 0.085)
              and eyes. move* 0.8 s: the wheels turn once (2 pi r = 0.53 units rolled to +X; spin them about Godot Z
              by -distance / 0.085 yourself if the speed differs), the tub rattles, the eyes glance and blink.
              minecart_iron, _rust, _rim, _coal, _wood, _pupil.
  guardian_drill     a pogo-drill robot 0.9 tall (0.5 wide with its arms), facing +X turned 40 degrees to the camera:
              an orange riveted boiler with one glowing porthole eye (drill_glow), pincer arms and a stack, on a
              spring over a spinning bit. Root "guardian_drill" (an empty; origin at the bit's tip on the floor) with
              children body (stack, arm_l, arm_r), spring, bit. move* 0.8 s: lands and squashes the spring, springs
              0.26 up, drops; the bit spins twice, the arms flail. drill_paint, _dark, _steel, _brass, _glass, _soot,
              _dial, _pupil.
  guardian_bat       a round cave bat, 0.96 wingspan, 0.5 tall with ears; origin at the body centre (hover it, e.g.
              for a vertical patrol); it faces the camera, glancing 25 degrees to +X. Armature "guardian_bat_rig",
              mesh "guardian_bat". move* 0.5 s: wing beats, the body bobs 0.03. bat_fur, _fur_light, _wing,
              _finger, _ear, _nose, _fang, _pupil, bat_glow (eyes).
  guardian_crab      a lantern crab 0.66 wide (claws), 0.35 to the eye stalks, 0.52 to its lantern (a brass lamp
              hanging from a stalk on its back, crab_glow), glowing eye stalks (crab_eye_glow); it faces the camera
              turned 20 degrees to +X and walks sideways. Armature "guardian_crab_rig", mesh "guardian_crab".
              move* 0.6 s: two alternating sets of legs step, the body sways, claws clack, the lantern swings.
              crab_shell, _shell_dark, _belly, _spot, _mouth, _pupil, crab_lantern_brass.
  guardian_gear      a rolling cog 0.62 across with a bloodshot eye in its hub, side view. Root "guardian_gear" (the
              brass hub, the eye (gear_glow iris) and a little bracket; stays upright; origin on the floor under the
              axle) with children "cog" (pivot on the axle, 0.31 up) and "lids". move* 1.2 s: the cog turns once
              clockwise (rolling 2 pi 0.31 = 1.95 to +X; otherwise spin it about Godot Z by -distance / 0.31), the
              hub judders, one blink. gear_steel, _dark, _brass, _copper, _eye_white, _pupil, _lid.
  guardian_snowball  a grumpy snow blob 0.5 wide, 0.64 tall: glowing icy eyes (snowball_glow) under coal brows, a coal
              frown, an icicle beard, twig arms. Root "guardian_snowball" (an empty at the base centre, facing +X
              turned 35 degrees to the camera) with child "body" (arm_l, arm_r). move* 0.7 s: a squashy waddle-hop
              (0.07 high), arms waving. snow_body, _shade, _coal, _ice, _twig.
Tiles (0.5 cube, origin at the centre, front face at Godot z = +0.25 with relief up to +0.275; one node each):
  tile_rock_a, _b, _c  cave rock: a: four big rounded stones in dark grit; b: 3 x 3 smaller rubble; c: four stones
              split by a glowing crystal vein (tile_crystal_glow, tile_crystal). tile_rock, tile_rock_dark,
              tile_rock_light (recolour per cavern). Stones stay inside the cell and there are a few on top.
  tile_floor  a timber walkway: four planks front to back (their ends and nails show), deck +0.195 .. +0.25, two
              stringers under it to +0.10, an iron strap; open below. tile_wood, tile_wood_dark, tile_iron.
  tile_crumble the same footprint in pale rotten timber with cracks, two split planks sagging, splinters, a fungus
              bracket, mud drips (to about -0.02): shrink or sink it away as it crumbles. tile_crumble_wood,
              _dark, _crack, _fungus.
  tile_conveyor an iron frame with a yellow front plate (two roller windows, a chevron band), top +0.25. Child "belt"
              (the rubber top, UVs one texture repeat per tile, material "conveyor_belt" with a packed 64 x 16
              texture, nearest filtering): scroll it with uv1_offset.x -= d / 0.5 to move the ribs d towards +X
              (albedo texture repeat must be on). Children roller_a, roller_b (x -+0.125, 0.14 up, radius 0.07):
              spin them about Godot Z by -d / 0.07. conveyor_iron, _paint, _dark, _steel, conveyor_belt.
  tile_wall_brick sooty mine brick, four staggered courses over dark mortar, full depth. tile_brick, _brick_dark,
              tile_mortar.
  tile_ice    glacier ice (faceted chunks, frost cracks), a snow cap rolling over the front edge (to +0.25), three
              icicles under the front edge hanging to -0.36 (into the cell below). tile_ice, _ice_deep, _ice_crack,
              tile_snow.
Hazards (in their own cell, standing on its floor at -0.25, origin at the cell centre like the tiles):
  hazard_spikes four iron spikes with bright tips in a rusty plate, tips at +0.12. spikes_iron, _tip, _rust.
  hazard_plant a poisonous cave plant 0.5 tall (to +0.25 + bulb): swollen stem, barbed leaves with purple ribs,
              glowing seed pods (hazard_plant_glow). Armature "plant_rig", mesh "hazard_plant"; sway* 2 s.
              plant_stem, _leaf, _vein, _thorn.
  hazard_steam a cast-iron vent with a glowing-hot grate (hazard_steam_glow); children steam_0..2 (steam_puff,
              alpha) that rise from the grate to about +0.3 in the animation puff* (1 s), each swelling and shrinking
              away in turn; hide them when the vent is off. steam_iron, _brass.
Items:
  key         a crystal key 0.42 long, upright (bow at the top), tilted 15 degrees; origin at its centre (float it in
              the cell). key_glow (the faceted crystal bow and bit tips: pulse or recolour it to flash), key_gem
              (emissive), key_brass. spin* 2 s: one turn about the vertical and a 0.03 bob.
  portal      the exit: a mine lift 1.0 wide (2 tiles), 1.12 tall to its sheave, origin at the bottom centre (deck top
              +0.04): green riveted headframe, a lit cage behind (portal_glow), signal lamps on the posts
              (portal_signal_glow: red while locked, green when open). Child "door": a scissor gate 0.19 in front
              of the origin, its origin on the left post; open 0.8 s (a rattle, then it folds to the left: scale.x
              1 -> 0.12). portal_iron, _paint, _brass, _wood, _dark.
Backdrop (origin at the base centre, front towards the camera; place at Godot z -1 .. -4):
  bg_timber_frame mine shoring 3.1 wide, 2.85 tall: round props with bark, a cap beam on wedges, lagging boards, iron
              dogs, a coil of rope. bg_timber, _timber_dark, _timber_end, bg_iron, bg_rope.
  bg_lantern  a hanging lantern; origin at the hook (the TOP); child "lantern" (pivot at the hook, the flame 0.33
              below: bg_lantern_glow) with sway* 3 s. bg_lantern_iron, _brass, _glass (alpha). Add an OmniLight3D.
  bg_crystal_vein a rock slab 1.7 wide, 1.2 tall split by glowing crystals (bg_crystal_glow, recolour per cavern;
              bg_crystal). bg_rock, bg_rock_light.
  bg_pipe     a boiler-room pipe run 2.0 long (tile every 2), 1.4 up on brackets, flanges and bolts, a riser with a red
              valve wheel, a pressure gauge (bg_pipe_glow). bg_pipe_copper, _iron, _brass, _valve.
  bg_mushroom a clump of giant fungi 1.7 tall with glowing gills and spots (bg_mushroom_glow). bg_mushroom_cap, _stem.
  bg_cog      a factory cog 2.0 across on an iron stand; child "cog" (axle 1.3 up) with turn* 6 s (one turn
              clockwise seen from the camera). bg_cog_steel, _brass, _iron.
  bg_icicles  a frozen ledge 2.0 wide with a snowy lip and icicles up to 0.9 long; origin at the TOP (hang it under
              the ceiling). bg_ice, _ice_deep, bg_snow.
  bg_rockwall a back-wall panel 4 x 4 of dark cave rock (x -2..2, y 0..4), lumps up to 0.3 forward: tile it every 4
              behind the field. bg_rock, _rock_light, _rock_dark (recolour per cavern).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90
from blastyard_bombers import Rig, merge, mirror, limb
from prism_models import animate, export_anim, empty, edit, new_obj
from hopline_models import TurnRig, ell
from mossfolk_models import lumpy, lathe_r, solid
import humanoid as HU
from relic_models import P, clear_all, cycle, rot_c, slim, air_legs, gear

FPS = 30
TILE = 0.5
HERO_GAME = 1.0 / 1.7     # the game scales the miner (1.7 tall) to 1.0 unit (2 tiles)


# ------------------------------------------------------------------ the miner

M_YAW = 62             # facing +X, turned 28 degrees towards the camera
MSK = HU.Skeleton(HU.proportions(sh_w=0.2, hip_w=0.105))
MSHAPE = {"chest": 1.16, "waist": 1.2, "hips": 1.12, "arms": 1.26, "legs": 1.2, "neck": 1.3, "hand": 1.12}
MHEAD = 1.4
MH = (0, -0.02, 1.69)           # head centre
M_SCALE = 0.884         # set so the helmet top is 1.70 (printed at export)
RIG_TO_GAME = M_SCALE * HERO_GAME


def m_stand(w=0.13):
    return {"ik_foot.L": (w, 0.03, 0.09, 0, 12), "ik_foot.R": (-w, -0.03, 0.09, 0, 14), "ikw.L": 1.0, "ikw.R": 1.0}


def m_arms(br=0.0):
    return {"clavicle.L": (2, 0, 2 + 1.5 * br), "clavicle.R": (2, 0, 2 + 1.5 * br),
            "arm.L": (4, 0, 14), "forearm.L": (22 + 2 * br, 0, 0), "hand.L": (0, 0, -4),
            "arm.R": (8, 0, 14), "forearm.R": (26 - 2 * br, 0, 0), "hand.R": (0, 0, -4)}


M_STAND = P(m_stand(), **{"root": (0, 0, -0.03), "spine": (2, 0, 0), "chest": (-1, 0, 0), "head": (-3, 0, 0)},
            **m_arms())


def m_idle():
    """3.2 s: slow breathing; he peers one way, then the other (the lamp sweeps), a shrug of the canister."""
    def f(t):
        a = 2 * math.pi * t
        br = math.sin(a * 3)
        sway = math.sin(a)
        look = HU.smoothstep(0.1, 0.22, t) * (1 - HU.smoothstep(0.38, 0.5, t)) \
            - HU.smoothstep(0.55, 0.67, t) * (1 - HU.smoothstep(0.83, 0.95, t))
        up = HU.smoothstep(0.6, 0.7, t) * (1 - HU.smoothstep(0.8, 0.9, t))
        shrug = max(0.0, math.sin(a * 2 - 1.0)) ** 6
        p = P(M_STAND, **{"root": (0.012 * sway, 0, -0.03 - 0.007 * br), "hips": (0, 3 * sway, -2 * sway),
                          "spine": (2, -2 * look, 0), "chest": (-1 + 1.8 * br, -8 * look, 0),
                          "neck": (-6 * up, -22 * look, 0), "head": (-3 - 2 * br - 10 * up, -30 * look, -4 * look)})
        p.update(m_arms(br))
        p["clavicle.L"] = (2, 0, 2 + 1.5 * br + 9 * shrug)
        p["clavicle.R"] = (2, 0, 2 + 1.5 * br + 9 * shrug)
        return p
    return cycle(96, f, 3)


WALK_FRAMES, WALK_STRIDE = 16, 1.5


def m_walk():
    """A sturdy, purposeful walk with a little bounce: WALK_STRIDE rig metres per cycle (two steps)."""
    return HU.gait(MSK, WALK_FRAMES, WALK_STRIDE, 0.56, lift=0.13, lift_at=0.42, strike=14, push=30, bob=0.028,
                   drop=-0.04, lean=6, width=0.13, arm_swing=32, arm_out=14, elbow=34, elbow_swing=24,
                   pelvis_yaw=8, pelvis_roll=5, shoulder_yaw=8, reach=0.5, sway=0.016, step=1,
                   base={"head": (-5, 0, 0), "spine": (3, 0, 0)})


def m_jump():
    """0.5 s one-shot: a quick crouch, spring, a tight tuck with the knees up and the arms hugging them (holds the
    last frame; blend to fall)."""
    crouch = P(M_STAND, **{"root": (0, 0.02, -0.18), "hips": (18, 0, 0), "spine": (10, 0, 0), "chest": (6, 0, 0),
                           "head": (-16, 0, 0), "ik_foot.L": (0.13, 0.06, 0.09, 0, 12),
                           "ik_foot.R": (-0.13, -0.06, 0.09, 0, 14), "arm.L": (-34, 0, 18), "arm.R": (-30, 0, 18),
                           "forearm.L": (30, 0, 0), "forearm.R": (36, 0, 0)})
    push = P(M_STAND, **{"root": (0, 0.04, 0.06), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (8, 0, 4), "shin.L": (8, 0, 0),
                         "thigh.R": (-10, 0, 4), "shin.R": (16, 0, 0), "foot.L": (-45, 0, 0), "foot.R": (-50, 0, 0),
                         "spine": (-4, 0, 0), "chest": (-6, 0, 0), "head": (-10, 0, 0),
                         "arm.L": (120, 0, 22), "forearm.L": (26, 0, 0), "arm.R": (110, 0, 20), "forearm.R": (34, 0, 0)})
    tuck = P(push, **air_legs(1.0, 0.1), **{"root": (0, 0.02, 0.16), "hips": (8, 0, 0), "spine": (16, 0, 0),
                                            "chest": (12, 0, 0), "neck": (-4, 0, 0), "head": (-18, 0, 0),
                                            "arm.L": (55, 0, 18), "forearm.L": (82, 0, 0), "hand.L": (0, 0, 10),
                                            "arm.R": (50, 0, 18), "forearm.R": (86, 0, 0), "hand.R": (0, 0, 10)})
    tuck["thigh.L"] = (95, 0, 8)
    tuck["thigh.R"] = (88, 0, 8)
    tuck["shin.L"] = (125, 0, 0)
    tuck["shin.R"] = (120, 0, 0)
    return HU.Anim({1: M_STAND, 4: crouch, 7: push, 11: tuck, 16: P(tuck, **{"arm.L": (60, 0, 20), "arm.R": (54, 0, 20)})})


def m_fall():
    """0.4 s loop: arms flailing overhead in circles, legs cycling."""
    def f(t):
        a = 2 * math.pi * t
        p = P(M_STAND, **air_legs(0.3 + 0.12 * math.sin(a), 0.7 * math.sin(a)))
        p.update({"root": (0, 0, 0.04), "spine": (-6, 4 * math.sin(a), 0), "chest": (-6, 0, 0), "head": (-16, 0, 0),
                  "arm.L": (140 + 26 * math.sin(a), 0, 60 + 12 * math.cos(a)), "forearm.L": (30 + 20 * math.cos(a), 0, 0),
                  "arm.R": (130 - 26 * math.sin(a), 0, 55 - 12 * math.cos(a)), "forearm.R": (40 - 20 * math.cos(a), 0, 0),
                  "hand.L": (0, 0, 24), "hand.R": (0, 0, 24)})
        return p
    return cycle(12, f, 1)


def m_die():
    """1.5 s one-shot: a jolt with the hands flung up, a dizzy spin on one heel, a wobble, then his knees give and he
    falls flat on his face (the canister on top), bounces once, and a boot twitches (holds; the body lies from about
    x = -0.35 to +1.35 at node scale 1)."""
    jolt = P(M_STAND, **{"root": (0, 0, 0.12), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (10, 0, 10), "shin.L": (14, 0, 0),
                         "thigh.R": (-4, 0, 10), "shin.R": (16, 0, 0), "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0),
                         "spine": (-8, 0, 0), "chest": (-10, 0, 0), "head": (-22, 0, 0),
                         "arm.L": (165, 0, 44), "forearm.L": (10, 0, 0), "arm.R": (165, 0, 40), "forearm.R": (14, 0, 0),
                         "hand.L": (0, 0, 30), "hand.R": (0, 0, 30)})
    spin = P(M_STAND, **{"turn": (0, 70, 0), "root": (0, 0, 0.02), "spine": (-4, 16, 6), "head": (-8, 26, 12),
                         "arm.L": (80, 0, 80), "forearm.L": (40, 0, 0), "arm.R": (100, 0, 76), "forearm.R": (30, 0, 0)})
    wob = P(M_STAND, **{"turn": (-6, 10, -10), "root": (0, -0.02, -0.02), "spine": (-4, -12, -6), "head": (-10, -24, -12),
                        "arm.L": (100, 0, 70), "arm.R": (60, 0, 80)})
    sag = P(M_STAND, **{"turn": (20, 0, 0), "root": (0, -0.2, -0.25), "ikw.L": 0.0, "ikw.R": 0.0,
                        "thigh.L": (60, 0, 8), "shin.L": (80, 0, 0), "thigh.R": (55, 0, 8), "shin.R": (85, 0, 0),
                        "foot.L": (-10, 0, 0), "foot.R": (-10, 0, 0), "spine": (10, 0, 0), "chest": (6, 0, 0),
                        "head": (-10, 0, 0), "arm.L": (30, 0, 30), "forearm.L": (20, 0, 0), "arm.R": (40, 0, 26),
                        "forearm.R": (20, 0, 0)})
    lie = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (90, 0, 0), "root": (0, -0.95, 0.14), "hips": (0, 0, 0),
           "spine": (-4, 0, 0), "chest": (-4, 0, 0), "neck": (-10, 0, 0), "head": (-16, 60, 0),
           "arm.L": (150, 0, 40), "forearm.L": (20, 0, 0), "arm.R": (140, 0, 44), "forearm.R": (30, 0, 0),
           "hand.L": (0, 0, 20), "hand.R": (0, 0, 20),
           "thigh.L": (-4, 0, 10), "shin.L": (10, 0, 0), "thigh.R": (-2, 0, 12), "shin.R": (6, 0, 0),
           "foot.L": (40, 0, 0), "foot.R": (40, 0, 0)}
    flat = P(lie, **{"turn": (94, 0, 0), "root": (0, -0.95, 0.1), "arm.L": (160, 0, 30), "arm.R": (150, 0, 34)})
    bounce = P(lie, **{"turn": (84, 0, 0), "root": (0, -0.95, 0.2), "thigh.L": (-24, 0, 10), "shin.L": (50, 0, 0),
                       "thigh.R": (-20, 0, 12), "shin.R": (44, 0, 0), "head": (-26, 40, 0), "arm.L": (130, 0, 50),
                       "arm.R": (120, 0, 54)})
    twitch = P(lie, **{"thigh.L": (-14, 0, 10), "shin.L": (75, 0, 0), "foot.L": (10, 0, 0)})
    return HU.Anim({1: M_STAND, 4: jolt, 10: spin, 15: wob, 20: sag, 24: flat, 28: bounce,
                    32: lie, 37: lie, 40: twitch, 43: lie, 46: lie})


def m_gasp():
    """1.2 s loop, out of air: both hands clutch at his collar, the chest heaves, the head jerks back on each gulp,
    the knees sag and wobble."""
    def f(t):
        a = 2 * math.pi * t
        gulp = max(0.0, math.sin(a * 2)) ** 2
        wob = math.sin(a)
        p = P(m_stand(0.14), **{"root": (0.02 * wob, 0.02, -0.09 - 0.02 * gulp), "hips": (8, 4 * wob, 4 * wob),
                               "spine": (8 - 10 * gulp, 3 * wob, -3 * wob), "chest": (6 - 12 * gulp, 0, 0),
                               "neck": (4 - 14 * gulp, 0, 0), "head": (10 - 34 * gulp, 10 * wob, 6 * wob),
                               "ik_hand.L": (0.06, 0.14, 1.42 - 0.02 * gulp), "ik_hand.R": (-0.05, 0.15, 1.4),
                               "ikh.L": 1.0, "ikh.R": 1.0,
                               "hand_dir.L": (-40, 40, 90), "hand_dir.R": (40, 40, 90), "hdw.L": 0.7, "hdw.R": 0.7})
        for X, s in (("L", 1), ("R", -1)):
            v = p["ik_foot." + X]
            p["ik_foot." + X] = (v[0], v[1], v[2], 0, v[4] + 10 * s * wob)
        return p
    a = cycle(36, f, 2)
    a.arm_pole = {"L": (0.6, -0.2, -1.0), "R": (0.6, -0.2, -1.0)}
    return a


def m_cheer():
    """1 s loop: two hops, fists pumping, then a helmet-tapping salute with the right hand."""
    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a * 2)) ** 1.5
        pump = math.sin(a)
        p = P(m_stand(0.14), **{
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


def miner_actions():
    return {"idle": m_idle(), "walk": m_walk(), "jump": m_jump(), "fall": m_fall(), "die": m_die(),
            "gasp": m_gasp(), "cheer": m_cheer()}


def export_rig(name, actions, sk, scale, yaw, attach=()):
    """relic_models.export_humanoid with bone-parented nodes that keep their own orientation: attach = [(object,
    bone)] (a mesh or an empty placed in rest space)."""
    bpy.context.scene.render.fps = FPS
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and "bone" in o]
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = HU.active()
    arm.name = name + "_rig"
    arm.data.name = name + "_rig"
    eb = arm.data.edit_bones
    eb.remove(eb[0])
    for n, (h, t, p, axis) in sk.bones.items():
        b = eb.new(n)
        b.head, b.tail = h, t
        b.align_roll((0, -1, 0) if axis == "fwd" else (0, 0, 1))
        if p:
            b.parent = eb[p]
    bpy.ops.object.mode_set(mode="OBJECT")
    HU._bind(meshes, sk)
    K.deselect()
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    mesh = HU.active()
    mesh.name = name
    mesh.data.name = name
    mod = mesh.modifiers.new("rig", "ARMATURE")
    mod.object = arm
    mesh.parent = arm
    nodes = []
    rest_at = []
    for o, bone in attach:
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy()
        rest_at.append((bone, mw))
        o.parent = arm
        o.parent_type = "BONE"
        o.parent_bone = bone
        bpy.context.view_layer.update()
        o.matrix_world = mw
        nodes.append(o)
    arm.animation_data_create()
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
    poser = HU.Poser(arm, sk)
    lengths = {}
    for aname, anim in actions.items():
        HU.keys_new(arm, poser, aname, anim, FPS)
        fr = sorted(anim.keys)
        lengths[aname] = ((fr[-1] - fr[0]) / FPS, anim.loop)
    for b in arm.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    arm.scale = (scale, scale, scale)
    arm.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    K.deselect()
    for o in [arm, mesh] + nodes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=False, export_animations=True,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True)
    MW = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Scale(scale, 4)
    zs = [(MW @ v.co) for v in mesh.data.vertices]
    print("exported %-10s %6d tris  height %.3f  x %.2f..%.2f  nodes: %s" % (
        name, K.tris(mesh), max(v.z for v in zs), min(v.x for v in zs), max(v.x for v in zs),
        ", ".join([arm.name, mesh.name] + [o.name for o in nodes])))
    for o, (bone, mw) in zip(nodes, rest_at):
        w = MW @ mw.translation
        print("   node %s on %s at (%.3f, %.3f, %.3f) Godot, rest" % (o.name, bone, w.x, w.z, -w.y))
    print("   anims: " + ", ".join("%s %.2fs%s" % (k, v[0], " loop" if v[1] else "") for k, v in lengths.items()))
    clear_all()


def miner():
    sk = MSK
    sh = MSHAPE
    skin = HU.mat("miner_skin", (0.93, 0.64, 0.5), 0.5)
    cheek = HU.mat("miner_cheek", (0.95, 0.46, 0.4), 0.55)
    white = HU.mat("miner_eye_white", (0.97, 0.96, 0.93), 0.3)
    iris = HU.mat("miner_iris", (0.2, 0.3, 0.42), 0.2)
    hair = HU.mat("miner_hair", (0.42, 0.3, 0.22), 0.65, coat=0.1)
    tache = HU.mat("miner_moustache", (0.5, 0.36, 0.26), 0.7)
    lips = HU.mat("miner_lips", (0.7, 0.36, 0.3), 0.5)
    shirt = HU.mat("miner_shirt", (0.86, 0.3, 0.2), 0.85)
    shirt_dk = HU.mat("miner_shirt_dark", (0.62, 0.18, 0.12), 0.85)
    trousers = HU.mat("miner_trousers", (0.24, 0.27, 0.36), 0.9)
    patch = HU.mat("miner_patch", (0.55, 0.45, 0.3), 0.9)
    stitch = HU.mat("miner_stitch", (0.9, 0.8, 0.55), 0.7)
    braces = HU.mat("miner_braces", (0.2, 0.34, 0.24), 0.7)
    boots = HU.mat("miner_boots", (0.34, 0.2, 0.1), 0.45, coat=0.3)
    sole = HU.mat("miner_sole", (0.08, 0.06, 0.05), 0.7)
    steel = HU.mat("miner_steel", (0.62, 0.62, 0.64), 0.3)
    glove = HU.mat("miner_glove", (0.62, 0.44, 0.24), 0.75)
    leather = HU.mat("miner_leather", (0.3, 0.18, 0.1), 0.5, coat=0.2)
    brass = mat("miner_brass", (0.95, 0.7, 0.3), 0.3, 0.9)
    helmet = HU.mat("miner_helmet", (0.95, 0.66, 0.16), 0.4, coat=0.5)
    helmet_dk = HU.mat("miner_helmet_dark", (0.7, 0.44, 0.1), 0.5, coat=0.3)
    scarf = HU.mat("miner_scarf", (0.2, 0.42, 0.72), 0.75)
    scarf_dot = HU.mat("miner_scarf_dot", (0.95, 0.92, 0.84), 0.75)
    tank = mat("miner_tank", (0.3, 0.52, 0.44), 0.35, 0.6, coat=0.4)
    hose = HU.mat("miner_hose", (0.14, 0.12, 0.12), 0.6)
    lamp_glow = mat("miner_lamp_glow", (1.0, 0.92, 0.7), 0.2, emit=12.0)
    gauge_glow = mat("miner_gauge_glow", (0.95, 0.95, 0.82), 0.3, emit=1.2)
    needle = mat("miner_needle", (0.9, 0.12, 0.08), 0.4)
    glass = mat("miner_glass", (0.8, 0.9, 1.0), 0.05, coat=1.0)

    HU.human_body(sk, skin, shirt, trousers, white, iris, shoes=boots, sole=sole, glove=glove, sleeves="short",
                  hands="relaxed", shape=sh, head=False, shoe_height=0.36)
    slim(boots, 0.6)
    slim(trousers, 0.6, bone="~body")
    slim(shirt, 0.55, bone="~body")
    for X in "LR":
        slim(trousers, 0.7, bone="~leg." + X)
        slim(glove, 0.6, bone="hand." + X)
    # rolled sleeves above the elbow, glove cuffs
    for X, s in (("L", 1), ("R", -1)):
        HU.tube(HU.arm_path(sk, X, 0.012, 0.0, 0.45, shape=sh["arms"]), "~arm." + X, shirt, 18, 0.016,
                lateral=(s, 0, 0), caps=(True, False))
        HU.tube(HU.arm_path(sk, X, 0.028, 0.35, 0.46, shape=sh["arms"]), "~arm." + X, shirt_dk, 14, 0.02,
                lateral=(s, 0, 0))
        a0, a1 = HU._along(sk, "forearm." + X, 0.8), HU._along(sk, "forearm." + X, 0.97)
        HU.tube([(a0.x, a0.y, a0.z, 0.03 * sh["arms"] + 0.012), (a1.x, a1.y, a1.z, 0.027 * sh["arms"] + 0.016)],
                "~arm." + X, glove, 14, 0.012, lateral=(s, 0, 0))
    # the head: a round, kindly face, a big nose, a bushy moustache, a smudge of soot
    k = MHEAD
    HU.head_detailed(skin, white, iris, center=MH, hair=None, size=k, brow=tache, lips=lips)
    cx, cy, cz = MH
    HU.sphere(0.104 * k, (0, cy + 0.07, cz + 0.0 * k), "head", hair, (0.93, 0.8, 0.85), 20, 10)
    HU.sphere(0.02 * k, (0, cy - 0.108 * k, cz - 0.028 * k), "head", cheek, (1.15, 1.0, 1.0), 14, 10)      # nose
    for s in (-1, 1):
        HU.sphere(0.022 * k, (0.058 * k * s, cy - 0.07 * k, cz - 0.03 * k), "head", cheek, (1.0, 0.6, 0.8), 10, 6)
        HU.sphere(0.024 * k, (0.09 * k * s, cy - 0.002 * k, cz - 0.02 * k), "head", hair, (0.55, 0.9, 1.4), 10, 6)
        # the moustache: two drooping, curled bushes
        HU.tube([(0.004 * s * k, cy - 0.106 * k, cz - 0.048 * k, 0.014 * k),
                 (0.03 * s * k, cy - 0.1 * k, cz - 0.052 * k, 0.017 * k),
                 (0.052 * s * k, cy - 0.086 * k, cz - 0.066 * k, 0.012 * k),
                 (0.062 * s * k, cy - 0.074 * k, cz - 0.056 * k, 0.006 * k)], "head", tache, 10, 0.006)
    # the helmet: an enamelled hard hat with a crest ridge and a short brim, a brass lamp on the front
    hz = cz + 0.05 * k
    n_before = set(bpy.context.scene.objects)
    dome = HU.sphere(0.124 * k, (0, cy + 0.005, hz), "head", helmet, (0.96, 1.08, 0.94), 28, 16)
    edit(dome, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < hz - 0.005], context="VERTS"))
    HU.sphere(0.03 * k, (0, cy + 0.005, hz + 0.092 * k), "head", helmet, (0.5, 3.6, 0.5), 16, 8)
    HU.body_loft([(hz - 0.004, 0.121 * k, 0.133 * k, cy + 0.005), (hz + 0.022 * k, 0.12 * k, 0.132 * k, cy + 0.005)],
                 "head", helmet_dk, 28, 0)
    bm = bmesh.new()
    n = 32
    rows = []
    for ring, (rx, ry, dz) in enumerate(((0.118, 0.13, 0.0), (0.15, 0.175, -0.012), (0.162, 0.192, -0.022))):
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            back = max(0.0, math.sin(a))            # the brim flares a little longer at the back (+Y)
            row.append(bm.verts.new((rx * k * math.cos(a), cy + 0.005 + ry * k * math.sin(a) * (1 + 0.15 * back * ring / 2),
                                     hz + dz * k + 0.004)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    brim = HU._mesh_object(bm, "brim")
    solid(brim, 0.012)
    HU.tag(brim, "head", helmet)
    # the lamp: a bracket, a brass barrel, a bright lens and a reflector rim; a cable round to the back
    LY = cy - 0.128 * k
    LZ = hz + 0.045 * k
    HU.box((0.03 * k, 0.03 * k, 0.05 * k), (0, LY + 0.01 * k, LZ - 0.02 * k), "head", helmet_dk, bevel=0.004)
    barrel = cyl(0.028 * k, 0.05 * k, (0, LY - 0.02 * k, LZ), brass, rot=(R90, 0, 0), verts=18, bevel=0.003)
    rim = torus(0.03 * k, 0.006 * k, (0, LY - 0.046 * k, LZ), brass, rot=(R90, 0, 0), verts=20, minor=6)
    lens = sphere(0.025 * k, (0, LY - 0.046 * k, LZ), lamp_glow, scale=(1, 0.35, 1), segs=16, rings=8)
    back_cap = sphere(0.028 * k, (0, LY + 0.004 * k, LZ), brass, scale=(1, 0.5, 1), segs=14, rings=8)
    for o in (barrel, rim, lens, back_cap):
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o["bone"] = "head"
    HU.tube([(0.02 * k, LY + 0.01 * k, LZ, 0.006 * k), (0.07 * k, cy - 0.06 * k, hz + 0.075 * k, 0.006 * k),
             (0.105 * k, cy + 0.03 * k, hz + 0.045 * k, 0.006 * k), (0.085 * k, cy + 0.11 * k, hz + 0.005 * k, 0.006 * k)],
            "head", hose, 8, 0.006)
    tilt = Matrix.Translation(Vector(MH)) @ Matrix.Rotation(math.radians(-6), 4, "X") @ Matrix.Translation(-Vector(MH))
    for o in set(bpy.context.scene.objects) - n_before:
        o.data.transform(tilt)
    lamp_at = tilt @ Vector((0, LY - 0.05 * k, LZ))
    # the neckerchief
    tube_pts = [(0.0, -0.09, 1.475, 0.026), (0.085, -0.052, 1.485, 0.028), (0.1, 0.02, 1.495, 0.028),
                (0.05, 0.085, 1.505, 0.026), (-0.02, 0.09, 1.505, 0.026), (-0.095, 0.03, 1.495, 0.028),
                (-0.085, -0.052, 1.485, 0.028), (0.0, -0.092, 1.475, 0.026)]
    HU.tube(tube_pts, "~body", scarf, 10, 0.03)
    HU.sphere(0.034, (-0.03, -0.11, 1.465), "~body", scarf, (1.2, 0.7, 1.0), 12, 7)
    HU.tube([(-0.03, -0.115, 1.45, 0.028), (-0.04, -0.13, 1.4, 0.02), (-0.045, -0.132, 1.36, 0.006)], "~body", scarf,
            8, 0.02, ell=(1.9, 0.4))
    for s in (-1, 1):
        HU.sphere(0.006, (0.065 * s, -0.1, 1.49), "~body", scarf_dot, (1, 0.6, 1), 6, 4)
    # braces: two straps from the waistband over the shoulders, crossing at the back; brass clips
    ck = sh["chest"]
    for s in (-1, 1):
        pts = [(0.085 * s, -0.125 * sh["waist"], 1.05, 0.012), (0.09 * s, -0.128 * ck, 1.22, 0.012),
               (0.1 * s, -0.11 * ck, 1.38, 0.012), (0.11 * s, -0.05, 1.47, 0.012), (0.1 * s, 0.05, 1.47, 0.012),
               (0.06 * s, 0.13 * ck, 1.36, 0.012), (-0.02 * s, 0.14 * ck, 1.22, 0.012),
               (-0.08 * s, 0.13 * sh["waist"], 1.06, 0.012)]
        HU.tube(pts, "~body", braces, 6, 0.03, ell=(1.9, 0.5))
        HU.box((0.035, 0.012, 0.03), (0.085 * s, -0.133 * sh["waist"], 1.07), "~body", brass, bevel=0.005)
    # shirt buttons down the placket
    for z in (1.18, 1.26, 1.34):
        HU.sphere(0.008, (0.0, -0.118 * ck - 0.004, z), "~body", scarf_dot, (1, 0.5, 1), 8, 5)
    # the belt and buckle
    HU.body_loft([(z, rx + 0.012, ry + 0.012, cy_, sq) for z, rx, ry, cy_, sq in HU.torso_rings(0.98, 1.04, 0.0, sh)],
                 "~body", leather, 26, 0)
    HU.box((0.06, 0.02, 0.05), (0.0, -0.1 * sh["hips"] - 0.025, 1.01), "~body", brass, bevel=0.006)
    # a patch on the left knee
    kl = sk.head("shin.L")
    HU.box((0.09, 0.02, 0.1), (kl.x, kl.y - 0.062, kl.z + 0.02), "~leg.L", patch, rot=(0.1, 0, 0.1), bevel=0.01)
    HU.box((0.1, 0.01, 0.006), (kl.x, kl.y - 0.07, kl.z + 0.07), "~leg.L", stitch, rot=(0.1, 0, 0.1), bevel=0.002)
    # boots: turned-down cuffs, laces, steel toe caps
    for X, s in (("L", 1), ("R", -1)):
        x = sk.head("foot." + X).x
        HU.body_loft([(0.33, 0.058, 0.066, 0.006), (0.37, 0.064, 0.072, 0.006)], "~foot." + X, leather, 18, 0, x0=x)
        for z in (0.16, 0.21, 0.26):
            HU.box((0.05, 0.012, 0.01), (x, -0.058, z), "~foot." + X, sole, bevel=0.003)
        HU.sphere(0.052, (x, -0.135, 0.045), "~foot." + X, steel, (1.0, 1.0, 0.72), 18, 10)
        HU.box((0.11, 0.28, 0.03), (x, -0.045, 0.015), "~foot." + X, sole, bevel=0.012)
    # the oxygen canister on his back (rigid on the chest): a rounded bottle in a harness, a valve wheel on top,
    # a hose over the right shoulder to a clip on the braces, and a gauge on its right flank (the camera side)
    TX, TY, TR = -0.01, 0.23 * ck, 0.095
    tp = [cyl(TR, 0.4, (TX, TY, 1.2), tank, verts=24, bevel=0.01),
          sphere(TR, (TX, TY, 1.4), tank, scale=(1, 1, 0.7), segs=24, rings=12),
          sphere(TR, (TX, TY, 1.0), tank, scale=(1, 1, 0.6), segs=24, rings=12)]
    for z in (1.07, 1.33):
        tp.append(torus(TR + 0.004, 0.012, (TX, TY, z), leather, verts=24, minor=6))
        tp.append(box((0.03, 0.02, 0.03), (TX - TR - 0.004, TY, z), brass, bevel=0.005))
    tp.append(cyl(0.022, 0.06, (TX, TY, 1.49), brass, verts=12, bevel=0.004))
    tp.append(torus(0.036, 0.008, (TX, TY, 1.525), brass, verts=16, minor=5))
    for a in range(4):
        tp.append(rod((TX, TY, 1.525), (TX + 0.036 * math.cos(a * R90), TY + 0.036 * math.sin(a * R90), 1.525), 0.004,
                      brass, verts=5))
    tp.append(tube([(TX, TY - 0.02, 1.5), (-0.07, 0.12, 1.58), (-0.13, 0.0, 1.52), (-0.12, -0.1, 1.4),
                    (-0.1, -0.135 * ck, 1.3)], [0.014, 0.014, 0.014, 0.014, 0.014], hose, verts=8))
    tp.append(box((0.03, 0.02, 0.04), (-0.1, -0.14 * ck, 1.29), brass, bevel=0.005))
    # the gauge
    gd = Vector((-0.85, -0.25, 0.46)).normalized()
    gc = Vector((TX, TY, 1.36)) + gd * (TR + 0.004)
    q = Vector((0, 0, 1)).rotation_difference(gd)
    Rg = q.to_matrix().to_4x4()
    gp = [cyl(0.05, 0.03, (0, 0, 0), brass, verts=22, bevel=0.004),
          cyl(0.042, 0.01, (0, 0, 0.016), gauge_glow, verts=22),
          sphere(0.043, (0, 0, 0.02), glass, scale=(1, 1, 0.25), segs=18, rings=6)]
    for i in range(7):                   # ticks round the dial, the last two red
        a = math.radians(-120 + 40 * i)
        gp.append(box((0.004, 0.012, 0.004), (0.032 * math.sin(a), 0.032 * math.cos(a), 0.022),
                      needle if i >= 5 else hose, rot=(0, 0, -a), bevel=0.0))
    gp.append(box((0.005, 0.032, 0.004), (-0.008, 0.012, 0.025), needle, rot=(0, 0, math.radians(35)), bevel=0.0))
    gp.append(sphere(0.006, (0, 0, 0.026), brass, segs=8, rings=4))
    for o in gp:
        xf(o, Matrix.Translation(gc) @ Rg)
    tp += gp
    for o in tp:
        o["bone"] = "chest"
    # the straps of the harness over the shoulders (over the braces)
    for s in (-1, 1):
        HU.tube([(0.07 * s, TY - 0.06, 1.42, 0.012), (0.12 * s, 0.04, 1.5, 0.012), (0.13 * s, -0.08, 1.44, 0.012),
                 (0.14 * s, -0.12, 1.32, 0.012)], "~body", leather, 6, 0.028, ell=(1.9, 0.5))
    # the lamp node: an empty at the lens whose local -Z (Godot) points along world +X at rest, 8 degrees down
    d_world = Vector((math.cos(math.radians(8)), 0, -math.sin(math.radians(8))))
    d_build = Matrix.Rotation(math.radians(-M_YAW), 3, "Z") @ d_world
    lamp = empty("lamp")
    lamp.empty_display_size = 0.05
    lamp.rotation_mode = "QUATERNION"
    lamp.rotation_quaternion = d_build.to_track_quat("Y", "Z")
    lamp.location = lamp_at
    export_rig("miner", miner_actions(), sk, M_SCALE, M_YAW, attach=[(lamp, "head")])
    print("   walk: %.3f game units per %d-frame cycle (%.2f units/s = %.2f tiles/s at speed_scale 1)" % (
        WALK_STRIDE * RIG_TO_GAME, WALK_FRAMES, WALK_STRIDE * RIG_TO_GAME * FPS / WALK_FRAMES,
        WALK_STRIDE * RIG_TO_GAME * FPS / WALK_FRAMES / TILE))



# ------------------------------------------------------------------ node helpers

def export_tree(root, name, links=(), yaw=0.0, anim=True):
    """export_anim with (child, parent) links at any depth and the root turned `yaw` degrees about the vertical
    (children built facing -Y follow it). The root may be an empty."""
    objs = [root]
    for c, parent in links:
        c.parent = parent
        c.matrix_parent_inverse = parent.matrix_world.inverted()
        objs.append(c)
    root.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    K.deselect()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.context.scene.frame_start = 0
    bpy.ops.export_scene.gltf(filepath=os.path.join(K.OUT, name + ".glb"), use_selection=True, export_format="GLB",
                              export_yup=True, export_apply=True, export_animations=anim,
                              export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_frame_step=1)
    tr = {}
    for o in objs:
        if o.animation_data:
            for t in o.animation_data.nla_tracks:
                a = t.strips[0].action
                tr[t.name] = max(tr.get(t.name, 0), (a.frame_range[1] - a.frame_range[0]) / FPS)
    print("exported %-22s %6d tris  nodes: %s%s" % (name, sum(K.tris(o) for o in objs if o.type == "MESH"),
                                                    ", ".join(o.name for o in objs),
                                                    ("  anims: " + ", ".join("%s %.2fs" % kv for kv in tr.items()))
                                                    if tr and anim else ""))
    reset()


def xf(o, M):
    """Bakes the object's own transform into its mesh, then transforms the mesh by M (world space)."""
    o.data.transform(M @ o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    return o


def keys_fn(frames, fn, step=1):
    """{frame: fn(phase)} for a loop of `frames` frames (the last key repeats the first)."""
    return {f: fn((f % frames) / frames) for f in range(0, frames + 1, step)}


def rivets(pts, r, material, axis_y=True):
    return [sphere(r, p, material, scale=(1, 0.55, 1) if axis_y else (1, 1, 0.55), segs=8, rings=5) for p in pts]


# ------------------------------------------------------------------ guardians (game size, facing +X)

def guardian_minecart():
    """A haunted mine cart, 0.62 long, 0.52 tall, side view (long side to the camera): a riveted, rusty tub heaped
    with coal, two glowing eyes peering out of the coal, a ghostly glow over the rim; two axles (children wheel_f,
    wheel_b) and the eyes (child "eyes")."""
    iron = mat("minecart_iron", (0.3, 0.29, 0.3), 0.45, 0.7)
    rust = mat("minecart_rust", (0.52, 0.24, 0.12), 0.8, 0.2)
    rim_m = mat("minecart_rim", (0.2, 0.19, 0.2), 0.4, 0.8)
    coal = mat("minecart_coal", (0.06, 0.06, 0.07), 0.35, coat=0.4)
    wood = mat("minecart_wood", (0.42, 0.27, 0.14), 0.8)
    haze = mat("minecart_glow", (0.4, 1.0, 0.5), 0.5, emit=5.0)
    eye_m = mat("minecart_eye_glow", (0.85, 1.0, 0.35), 0.3, emit=5.0)
    pupil = mat("minecart_pupil", (0.02, 0.03, 0.02), 0.3)
    WR = 0.085
    Z0 = 0.13               # the tub's bottom
    # the tub: a trapezoid (wider at the top), made from a loft of rounded rectangles
    bm = bmesh.new()
    rings = []
    for z, hx, hy in ((Z0, 0.24, 0.16), (Z0 + 0.02, 0.25, 0.17), (0.46, 0.3, 0.2), (0.48, 0.305, 0.205)):
        ring = []
        for kk in range(24):
            a = 2 * math.pi * kk / 24
            c, s_ = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((hx * math.copysign(abs(c) ** 0.3, c), hy * math.copysign(abs(s_) ** 0.3, s_), z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for kk in range(24):
            bm.faces.new((r0[kk], r0[(kk + 1) % 24], r1[(kk + 1) % 24], r1[kk]))
    bm.faces.new(rings[0][::-1])
    tub = new_obj("tub", bm, rust, smooth=40)
    solid(tub, 0.02)
    parts = [tub]
    # iron bands, a thick rim, corner straps and rivets
    for z, hx, hy in ((0.47, 0.305, 0.205), (0.3, 0.275, 0.186)):
        o = torus(1.0, 0.018, (0, 0, z), iron, verts=32, minor=6, scale=(hx, hy, 1))
        parts.append(o)
    parts.append(torus(1.0, 0.026, (0, 0, 0.485), rim_m, verts=32, minor=8, scale=(0.305, 0.205, 1)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(rod((0.245 * sx, 0.165 * sy, Z0 + 0.01), (0.3 * sx, 0.2 * sy, 0.47), 0.018, iron, verts=6))
    rv = []
    for x in (-0.18, -0.06, 0.06, 0.18):
        for z in (0.3, 0.46):
            f = (z - Z0) / (0.48 - Z0)
            rv.append((x * (1 + 0.2 * f), -(0.16 + 0.045 * f) - 0.02, z))
    parts += rivets(rv, 0.012, rim_m)
    # a wooden plank bumper at each end, the chassis, axle boxes
    for sx in (-1, 1):
        parts.append(box((0.05, 0.3, 0.07), (0.3 * sx, 0, Z0 + 0.03), wood, bevel=0.012))
        parts.append(cyl(0.025, 0.04, (0.33 * sx, 0, Z0 + 0.03), iron, rot=(0, R90, 0), verts=10))
    parts.append(box((0.5, 0.26, 0.04), (0, 0, Z0 - 0.015), iron, bevel=0.01))
    for x in (-0.17, 0.17):
        for sy in (-1, 1):
            parts.append(box((0.08, 0.03, 0.06), (x, 0.15 * sy, WR), iron, bevel=0.01))
    # the coal heap, the ghostly haze over it
    rnd = random.Random(21)
    for kk in range(26):
        x, y = rnd.uniform(-0.24, 0.24), rnd.uniform(-0.15, 0.15)
        z = 0.44 + 0.07 * (1 - (x / 0.3) ** 2) * (1 - (y / 0.2) ** 2) + rnd.uniform(-0.02, 0.02)
        parts.append(lumpy(rnd.uniform(0.04, 0.065), (x, y, z), coal, 200 + kk, 0.25))
    for kk in range(7):              # ghostly green embers glowing between the lumps
        x, y = rnd.uniform(-0.22, 0.22), rnd.uniform(-0.14, 0.02)
        parts.append(sphere(0.022, (x, y, 0.47), haze, scale=(1.4, 1, 0.6), segs=10, rings=6))
    body = join(parts, "guardian_minecart")
    # the eyes: two glowing ovals with slit pupils among the coal, facing a little forward (+X) and to the camera
    ep = []
    for x in (0.03, 0.17):
        c = Vector((x, -0.13, 0.56))
        ep.append(ell(tuple(c), (0.052, 0.03, 0.058), eye_m, yaw=-15, segs=16, rings=10))
        ep.append(ell(tuple(c + Vector((0.016, -0.026, -0.004))), (0.012, 0.008, 0.04), pupil, yaw=-15, segs=8, rings=6))
        ep.append(box((0.1, 0.035, 0.024), (x - 0.004, -0.13, 0.622), coal,
                      rot=(0, math.radians(16 if x < 0.1 else -16), 0), bevel=0.008))
    eyes = join(ep, "eyes", pivot=(0.1, -0.13, 0.56))
    wheels = []
    for nm, x in (("wheel_b", -0.17), ("wheel_f", 0.17)):
        wp = []
        for sy in (-1, 1):
            wp.append(cyl(WR, 0.035, (x, 0.18 * sy, WR), iron, rot=(R90, 0, 0), verts=24, bevel=0.006))
            wp.append(torus(WR - 0.004, 0.012, (x, 0.2 * sy, WR), rim_m, rot=(R90, 0, 0), verts=24, minor=5))
            wp.append(cyl(0.025, 0.05, (x, 0.19 * sy, WR), rust, rot=(R90, 0, 0), verts=10))
            for kk in range(4):
                a = kk * R90 + 0.3
                wp.append(rod((x, 0.199 * sy, WR), (x + 0.06 * math.cos(a), 0.199 * sy, WR + 0.06 * math.sin(a)), 0.01,
                              rust, verts=5))
        wp.append(cyl(0.014, 0.36, (x, 0, WR), iron, rot=(R90, 0, 0), verts=8))
        wheels.append(join(wp, nm, pivot=(x, 0, WR)))
    # move (loop 0.8 s): the wheels turn once (rolling 2 pi r = 0.53 to +X), the tub rattles, the eyes glance about
    N = 24
    animate(body, "move", keys_fn(N, lambda t: {"loc": (0, 0, 0.008 * abs(math.sin(2 * math.pi * t * 2))),
                                                "rot": (0, math.radians(1.6 * math.sin(2 * math.pi * t * 2)), 0)}, 2),
            linear=False)
    for w in wheels:
        animate(w, "move", {f: {"rot": (0, 2 * math.pi * f / N, 0)} for f in range(0, N + 1, 2)}, linear=True)
    animate(eyes, "move", {0: {}, 6: {"loc": (0.02, 0, 0.005)}, 10: {"loc": (0.02, 0, 0.005), "scale": (1, 1, 0.15)},
                           12: {"loc": (0.02, 0, 0.005)}, 18: {"loc": (-0.015, 0, 0)}, 24: {}}, linear=False)
    export_tree(body, "guardian_minecart", [(w, body) for w in wheels] + [(eyes, body)])


DRILL_YAW = 50         # facing +X, turned 40 degrees towards the camera


def guardian_drill():
    """A pogo-drill robot 0.95 tall: a riveted boiler body with one glowing eye, little pincer arms and a smoking
    stack, bouncing on a spring over a spinning drill bit. Root "guardian_drill" (an empty at the bit's tip on the
    floor, turned 40 degrees towards the camera) with children body (arm_l, arm_r, stack), spring, bit."""
    paint = mat("drill_paint", (0.86, 0.5, 0.16), 0.45, 0.3, coat=0.5)
    dark = mat("drill_dark", (0.22, 0.22, 0.24), 0.4, 0.7)
    steel = mat("drill_steel", (0.72, 0.74, 0.78), 0.25, 1.0)
    brass = mat("drill_brass", (0.95, 0.72, 0.3), 0.3, 0.9)
    glow = mat("drill_glow", (1.0, 0.3, 0.15), 0.3, emit=8.0)
    glass = mat("drill_glass", (0.9, 0.95, 1.0), 0.05, coat=1.0, alpha=0.3)
    soot = mat("drill_soot", (0.12, 0.11, 0.1), 0.8)
    BZ0, BZ1, BR = 0.34, 0.66, 0.17
    bp = [cyl(BR, BZ1 - BZ0, (0, 0, (BZ0 + BZ1) / 2), paint, verts=28, bevel=0.02),
          sphere(BR, (0, 0, BZ1), paint, scale=(1, 1, 0.55), segs=28, rings=14),
          sphere(BR * 0.9, (0, 0, BZ0), dark, scale=(1, 1, 0.35), segs=24, rings=10)]
    for z in (BZ0 + 0.02, BZ1 - 0.02):
        bp.append(torus(BR + 0.004, 0.014, (0, 0, z), dark, verts=32, minor=6))
        for kk in range(12):
            a = 2 * math.pi * kk / 12
            bp.append(sphere(0.01, (BR * 1.03 * math.cos(a), BR * 1.03 * math.sin(a), z + (0.022 if z < 0.5 else -0.022)),
                             brass, segs=6, rings=4))
    # the eye: a brass porthole on the front (-Y) with a glowing lens and a visor lid
    E = Vector((0, -BR - 0.005, 0.54))
    bp.append(torus(0.07, 0.018, tuple(E), brass, rot=(R90, 0, 0), verts=24, minor=6))
    bp.append(sphere(0.062, tuple(E + Vector((0, 0.02, 0))), glow, scale=(1, 0.45, 1), segs=18, rings=10))
    bp.append(sphere(0.022, tuple(E + Vector((0, -0.012, 0.0))), mat("drill_pupil", (0.1, 0.02, 0.02), 0.3),
                     scale=(1, 0.4, 1), segs=10, rings=6))
    bp.append(sphere(0.066, tuple(E + Vector((0, -0.004, 0))), glass, scale=(1, 0.35, 1), segs=16, rings=8))
    lid = sphere(0.085, (0, 0, 0), dark, scale=(1.05, 0.6, 0.55), segs=18, rings=8)
    edit(lid, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.005], context="VERTS"))
    lid.data.transform(Matrix.Translation(E + Vector((0, -0.01, 0.035))) @ Matrix.Rotation(math.radians(-12), 4, "Y"))
    bp.append(lid)
    # side gauges, a pipe, a panel
    bp.append(cyl(0.035, 0.02, (-BR - 0.005, -0.06, 0.44), brass, rot=(0, R90, 0), verts=14))
    bp.append(cyl(0.028, 0.012, (-BR - 0.015, -0.06, 0.44), mat("drill_dial", (0.95, 0.93, 0.85), 0.4), rot=(0, R90, 0),
                  verts=14))
    bp.append(tube([(BR * 0.7, 0.1, 0.62), (BR + 0.05, 0.06, 0.55), (BR + 0.04, 0.0, 0.42), (BR * 0.8, -0.05, 0.38)],
                   [0.016] * 4, brass, verts=8))
    body = join(bp, "body", pivot=(0, 0, BZ0))
    stack = join([cyl(0.035, 0.14, (0.05, 0.07, BZ1 + 0.13), dark, verts=12, bevel=0.005),
                  cyl(0.05, 0.035, (0.05, 0.07, BZ1 + 0.2), dark, r2=0.04, verts=12),
                  torus(0.042, 0.008, (0.05, 0.07, BZ1 + 0.22), soot, verts=12, minor=4)], "stack",
                 pivot=(0.05, 0.07, BZ1 + 0.06))
    arms = []
    for nm, sx in (("arm_l", 1), ("arm_r", -1)):
        sh_ = Vector((sx * (BR + 0.01), -0.02, 0.5))
        ap = [sphere(0.035, tuple(sh_), dark, segs=12, rings=8),
              tube([sh_, sh_ + Vector((sx * 0.06, -0.03, -0.06)), sh_ + Vector((sx * 0.08, -0.07, -0.12))],
                   [0.016, 0.014, 0.013], steel, verts=8)]
        h = sh_ + Vector((sx * 0.08, -0.07, -0.12))
        for sp in (-1, 1):
            ap.append(rod(h, h + Vector((sx * 0.02, -0.02, -0.05 + 0.0)) + Vector((0.02 * sp, 0, 0)), 0.01, brass,
                          r2=0.003, verts=6))
        arms.append(join(ap, nm, pivot=tuple(sh_)))
    SZ0, SZ1 = 0.2, BZ0 + 0.02
    spp = []
    turns = 5
    pts = []
    for kk in range(turns * 16 + 1):
        a = 2 * math.pi * kk / 16
        pts.append((0.07 * math.cos(a), 0.07 * math.sin(a), SZ0 + (SZ1 - SZ0) * kk / (turns * 16)))
    spp.append(tube(pts, [0.012] * len(pts), steel, verts=6))
    spp.append(cyl(0.03, SZ1 - SZ0, (0, 0, (SZ0 + SZ1) / 2), dark, verts=10))
    spring = join(spp, "spring", pivot=(0, 0, SZ0))
    # the bit: a collar and a fluted steel cone to a point at the floor
    bt = [cyl(0.085, 0.05, (0, 0, SZ0 - 0.005), dark, verts=20, bevel=0.01),
          cyl(0.09, 0.012, (0, 0, SZ0 + 0.02), brass, verts=20)]
    cone = cyl(0.001, SZ0 - 0.03, (0, 0, (SZ0 - 0.03) / 2), steel, r2=0.075, verts=24)
    bt.append(cone)
    for kk in range(3):               # a helical flute ridge around the cone
        pts = []
        for j in range(25):
            u = j / 24
            a = 2 * math.pi * (kk / 3 + 1.2 * u)
            r = 0.075 * (1 - u) + 0.004
            pts.append((r * math.cos(a), r * math.sin(a), 0.005 + (SZ0 - 0.04) * u))
        bt.append(tube(pts, [0.011 * (1 - 0.7 * j / 24) for j in range(25)], steel, verts=6))
    bit = join(bt, "bit", pivot=(0, 0, 0))
    root = empty("guardian_drill")
    # move (loop 0.8 s): lands and squashes the spring, springs up 0.26, hangs, drops; the bit spins; arms flail
    N = 24

    def hop(t):
        """height of the body above rest, spring squash (1 = rest), bit height"""
        if t < 0.25:              # on the floor: squash and release
            sq = math.sin(math.pi * t / 0.25)
            return -0.07 * sq, 1 - 0.55 * sq, 0.0
        u = (t - 0.25) / 0.75     # airborne: a parabola 0.26 high
        h = 0.26 * 4 * u * (1 - u)
        return h, 1.08, h
    kb, ks, kt, ka, kl = {}, {}, {}, {}, {}
    for f in range(0, N + 1):
        t = (f % N) / N
        h, sq, hb = hop(t)
        kb[f] = {"loc": (0, 0, h), "rot": (math.radians(4 * math.sin(2 * math.pi * t)), 0, 0),
                 "scale": (1 + 0.05 * (1 - sq), 1 + 0.05 * (1 - sq), 1 - 0.04 * (1 - sq))}
        ks[f] = {"loc": (0, 0, hb), "scale": (1, 1, sq)}
        kt[f] = {"loc": (0, 0, hb), "rot": (0, 0, -2 * math.pi * 2 * f / N)}
        ka[f] = {"rot": (math.radians(30 * math.sin(2 * math.pi * t)), 0, 0)}
        kl[f] = {"rot": (0, 0, 0), "scale": (1, 1, 1 + 0.25 * max(0.0, math.sin(2 * math.pi * (t - 0.1))))}
    animate(body, "move", kb, linear=False)
    animate(spring, "move", ks, linear=False)
    animate(bit, "move", kt, linear=True)
    for a_, sx in zip(arms, (1, -1)):
        animate(a_, "move", {f: {"rot": (v["rot"][0] * sx, 0, 0)} for f, v in ka.items()}, linear=False)
    animate(stack, "move", kl, linear=False)
    export_tree(root, "guardian_drill", [(body, root), (spring, root), (bit, root), (stack, body)] +
                [(a_, body) for a_ in arms], yaw=DRILL_YAW)


def guardian_bat():
    """A round cave bat, 0.95 wingspan, origin at the body centre (hover it); it faces the camera, glancing 25 degrees towards +X.
    Armature "bat_rig", mesh "guardian_bat"; animation move (loop 0.5 s: wing beats, the body bobs 0.05)."""
    fur = mat("bat_fur", (0.3, 0.24, 0.36), 0.7, coat=0.1)
    fur2 = mat("bat_fur_light", (0.55, 0.46, 0.58), 0.75)
    wing_m = mat("bat_wing", (0.26, 0.16, 0.3), 0.5, coat=0.3)
    bone_m = mat("bat_finger", (0.16, 0.1, 0.18), 0.5)
    ear_in = mat("bat_ear", (0.86, 0.5, 0.56), 0.6)
    glow = mat("bat_glow", (1.0, 0.85, 0.2), 0.3, emit=9.0)
    fang = mat("bat_fang", (0.97, 0.96, 0.9), 0.3)
    nose = mat("bat_nose", (0.62, 0.36, 0.44), 0.5)
    B = {"root": ((0, 0, -0.25), (0, 0, -0.15), None), "body": ((0, 0, -0.14), (0, 0, 0.12), "root")}
    for s, side in ((1, "L"), (-1, "R")):
        B["wing." + side] = ((0.09 * s, 0.02, 0.04), (0.28 * s, 0.04, 0.08), "body")
        B["tip." + side] = ((0.28 * s, 0.04, 0.08), (0.48 * s, 0.07, 0.02), "wing." + side)
        B["ear." + side] = ((0.06 * s, 0.0, 0.1), (0.1 * s, 0.0, 0.24), "body")
        B["foot." + side] = ((0.04 * s, 0.02, -0.1), (0.04 * s, 0.03, -0.17), "body")
    rig = TurnRig(B, 25, fps=FPS)
    c = Vector((0, 0, 0))
    bodyp = [sphere(0.13, tuple(c), fur, scale=(1.0, 0.92, 1.0), segs=20, rings=14),
             sphere(0.09, tuple(c + Vector((0, -0.07, -0.035))), fur2, scale=(1.0, 0.55, 0.9), segs=16, rings=10)]
    rnd = random.Random(5)
    for kk in range(14):              # a shaggy ruff round the neck
        a = math.pi * (kk / 13) - math.pi / 2
        p = Vector((0.12 * math.sin(a), -0.02 + 0.07 * abs(math.cos(a)) * 0 + 0.03, 0.05 - 0.02 * abs(math.sin(a))))
        bodyp.append(ell(tuple(p), (0.04, 0.035, 0.05), fur, pitch=rnd.uniform(-20, 20), segs=10, rings=6))
    for kk in range(5):               # a tuft on the head
        bodyp.append(rod((0, -0.02, 0.1), (0.03 * (kk - 2), -0.04 + 0.01 * kk, 0.17 + 0.01 * (kk % 2)), 0.014, fur,
                         r2=0.002, verts=5))
    bodyp.append(sphere(0.028, tuple(c + Vector((0, -0.125, 0.0))), nose, scale=(1.3, 0.8, 0.9), segs=12, rings=8))
    for s in (1, -1):
        e = c + Vector((0.052 * s, -0.105, 0.035))
        bodyp.append(sphere(0.034, tuple(e), glow, scale=(1, 0.55, 1.1), segs=12, rings=8))
        bodyp.append(sphere(0.012, tuple(e + Vector((0, -0.017, 0))), mat("bat_pupil", (0.05, 0.02, 0.04), 0.3),
                            scale=(0.6, 0.5, 1.3), segs=8, rings=6))
        brow = sphere(1.0, (0, 0, 0), fur, scale=(0.045, 0.015, 0.012), segs=10, rings=6)
        brow.data.transform(Matrix.Rotation(math.radians(-22 * s), 4, "Y"))
        brow.data.transform(Matrix.Translation(e + Vector((0.004 * s, -0.012, 0.038))))
        bodyp.append(brow)
        bodyp.append(rod(c + Vector((0.022 * s, -0.12, -0.04)), c + Vector((0.024 * s, -0.122, -0.08)), 0.011, fang,
                         r2=0.0, verts=5))
    rig.rigid("body", *bodyp)
    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("ear." + side, rod(c + Vector((0.055 * s, 0, 0.08)), c + Vector((0.12 * s, 0.01, 0.27)), 0.065, fur,
                                     r2=0.0, verts=10),
                  rod(c + Vector((0.058 * s, -0.022, 0.09)), c + Vector((0.112 * s, -0.012, 0.24)), 0.04, ear_in,
                      r2=0.0, verts=8))
        rig.rigid("foot." + side, rod((0.04 * s, 0.02, -0.1), (0.04 * s, 0.03, -0.16), 0.016, bone_m, verts=6),
                  *[rod((0.04 * s, 0.03, -0.16), (0.04 * s + 0.012 * j, 0.0, -0.18), 0.006, bone_m, verts=4)
                    for j in (-1, 0, 1)])
        # the wing: a membrane with a scalloped trailing edge between three fingers
        bm = bmesh.new()
        N_, M_ = 12, 4
        grid = []
        for i in range(N_ + 1):
            u = i / N_
            x = 0.08 + u * 0.42
            lead_z = 0.05 + 0.07 * math.sin(u * math.pi) - 0.04 * u
            chord = 0.26 * (1 - u * 0.55) * (0.62 + 0.38 * abs(math.cos(u * math.pi * 1.5)))
            grid.append([bm.verts.new((s * x, 0.02 + 0.035 * u + 0.02 * j / M_, lead_z - chord * j / M_))
                         for j in range(M_ + 1)])
        for i in range(N_):
            for j in range(M_):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if s > 0 else f[::-1])
        me = bpy.data.meshes.new("wing")
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("wing", me)
        bpy.context.scene.collection.objects.link(o)
        solid(o, 0.014)
        K.finish(o, wing_m, smooth=50)
        bones = ["body", "wing." + side, "tip." + side]
        rig.smooth(bones, o)
        rig.smooth(bones, limb([(0.08 * s, 0.02, 0.05), (0.28 * s, 0.045, 0.1), (0.5 * s, 0.075, 0.01)],
                               [0.018, 0.013, 0.006], bone_m, verts=6, per=4, caps=True))
        for u in (0.38, 0.7):          # finger bones fanning down to the scallops
            x0 = 0.08 + u * 0.42
            lead = 0.05 + 0.07 * math.sin(u * math.pi) - 0.04 * u
            ch = 0.26 * (1 - u * 0.55) * (0.62 + 0.38 * abs(math.cos(u * math.pi * 1.5)))
            rig.smooth(bones, limb([(s * x0, 0.02 + 0.035 * u - 0.004, lead), (s * (x0 + 0.02), 0.03 + 0.035 * u, lead - ch)],
                                   [0.008, 0.004], bone_m, verts=5, per=2, caps=True))
        rig.smooth(bones, sphere(0.014, (0.29 * s, 0.03, 0.105), bone_m, segs=8, rings=5))
    rig.build("guardian_bat")
    up = mirror({"wing.L": (0, -55, 0), "tip.L": (0, -25, 0), "ear.L": (0, 5, 0)})
    mid_d = mirror({"wing.L": (0, 5, 0), "tip.L": (0, -16, 0)})
    down = mirror({"wing.L": (0, 50, 0), "tip.L": (0, 28, 0), "ear.L": (0, -8, 0)})
    mid_u = mirror({"wing.L": (0, 0, 0), "tip.L": (0, 30, 0)})
    feet = mirror({"foot.L": (20, 0, 0)})
    rig.action("move", {0: merge(up, feet, {"@root": (0, 0, -0.03), "body": (6, 0, 0)}),
                        4: merge(mid_d, feet, {"@root": (0, 0, 0.0)}),
                        8: merge(down, {"@root": (0, 0, 0.03), "body": (-4, 0, 0)}),
                        11: merge(mid_u, feet, {"@root": (0, 0, 0.01)}),
                        15: merge(up, feet, {"@root": (0, 0, -0.03), "body": (6, 0, 0)})}, loop=True)
    rig.save("guardian_bat")


def guardian_crab():
    """A lantern crab 0.62 wide (claws out), 0.36 tall to the eye stalks and 0.72 to its lantern; it faces the
    camera, turned 20 degrees towards +X (it walks sideways). Armature "crab_rig", mesh "guardian_crab"; animation
    move (loop 0.6 s: legs stepping in two alternating sets, the body swaying, claws clacking, the lantern swinging)."""
    shell = mat("crab_shell", (0.86, 0.32, 0.16), 0.35, coat=0.7)
    shell2 = mat("crab_shell_dark", (0.6, 0.18, 0.1), 0.4, coat=0.5)
    belly = mat("crab_belly", (0.98, 0.8, 0.6), 0.5)
    spot = mat("crab_spot", (0.98, 0.62, 0.3), 0.4, coat=0.5)
    eye = mat("crab_eye_glow", (0.4, 1.0, 0.9), 0.3, emit=8.0)
    pupil = mat("crab_pupil", (0.02, 0.05, 0.05), 0.3)
    lamp_b = mat("crab_lantern_brass", (0.95, 0.72, 0.3), 0.3, 0.9)
    lamp_g = mat("crab_glow", (1.0, 0.72, 0.3), 0.3, emit=10.0)
    Z = 0.15                          # shell centre height
    B = {"root": ((0, 0, 0.0), (0, 0, 0.1), None), "body": ((0, 0.02, Z - 0.06), (0, 0.02, Z + 0.08), "root"),
         "stalk": ((0, 0.06, Z + 0.08), (0, 0.02, Z + 0.34), "body"),
         "lantern": ((0, 0.0, Z + 0.34), (0, -0.04, Z + 0.24), "stalk")}
    for s, side in ((1, "L"), (-1, "R")):
        B["eye." + side] = ((0.05 * s, -0.08, Z + 0.06), (0.06 * s, -0.1, Z + 0.17), "body")
        B["arm." + side] = ((0.12 * s, -0.08, Z - 0.02), (0.2 * s, -0.16, Z + 0.0), "body")
        B["claw." + side] = ((0.2 * s, -0.16, Z + 0.0), (0.25 * s, -0.24, Z + 0.02), "arm." + side)
        B["pincer." + side] = ((0.235 * s, -0.24, Z - 0.005), (0.285 * s, -0.33, Z - 0.012), "claw." + side)
        for k in range(3):
            y = -0.03 + 0.06 * k
            B["leg%d.%s" % (k, side)] = ((0.13 * s, y, Z - 0.03), (0.21 * s, y + 0.01, Z + 0.04), "body")
            B["foot%d.%s" % (k, side)] = ((0.21 * s, y + 0.01, Z + 0.04), (0.26 * s, y + 0.02, 0.0), "leg%d.%s" % (k, side))
    rig = TurnRig(B, 20, fps=FPS)
    body = [ell((0, 0.02, Z), (0.17, 0.14, 0.09), shell, segs=26, rings=14),
            ell((0, 0.02, Z - 0.035), (0.15, 0.12, 0.05), belly, segs=22, rings=10)]
    rnd = random.Random(9)
    for kk in range(10):              # bumps and spots over the shell
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.2, 0.8)
        x, y = 0.15 * r * math.cos(a), 0.02 + 0.12 * r * math.sin(a)
        zt = Z + 0.09 * math.sqrt(max(0.0, 1 - r * r)) - 0.004
        body.append(sphere(rnd.uniform(0.012, 0.022), (x, y, zt), spot if kk % 2 else shell2, scale=(1, 1, 0.45),
                           segs=8, rings=5))
    for s in (-1, 1):                 # a serrated front rim
        for kk in range(4):
            a = math.radians(-90 + s * (20 + 16 * kk))
            body.append(rod((0.16 * math.cos(a), 0.02 + 0.13 * math.sin(a), Z + 0.01),
                            (0.19 * math.cos(a), 0.02 + 0.155 * math.sin(a), Z + 0.02), 0.014, shell, r2=0.002,
                            verts=5))
    body.append(ell((0, -0.1, Z - 0.03), (0.05, 0.02, 0.012), mat("crab_mouth", (0.3, 0.06, 0.05), 0.5), segs=10,
                    rings=6))
    rig.rigid("body", *body)
    rig.rigid("stalk", tube([(0, 0.08, Z + 0.07), (0, 0.1, Z + 0.22), (0, 0.06, Z + 0.33), (0, 0.0, Z + 0.35)],
                            [0.016, 0.012, 0.01, 0.009], shell2, verts=8))
    L0 = Vector((0, -0.005, Z + 0.33))
    rig.rigid("lantern", torus(0.012, 0.004, tuple(L0), lamp_b, rot=(R90, 0, 0), verts=10, minor=4),
              cyl(0.035, 0.012, tuple(L0 + Vector((0, 0, -0.03))), lamp_b, r2=0.02, verts=12),
              sphere(0.034, tuple(L0 + Vector((0, 0, -0.07))), lamp_g, scale=(1, 1, 1.2), segs=14, rings=10),
              *[rod(L0 + Vector((0.034 * math.cos(a), 0.034 * math.sin(a), -0.035)),
                    L0 + Vector((0.034 * math.cos(a), 0.034 * math.sin(a), -0.11)), 0.004, lamp_b, verts=4)
                for a in (0.4, 0.4 + R90, 0.4 + 2 * R90, 0.4 + 3 * R90)],
              cyl(0.038, 0.01, tuple(L0 + Vector((0, 0, -0.112))), lamp_b, verts=12))
    for s, side in ((1, "L"), (-1, "R")):
        e = Vector((0.065 * s, -0.1, Z + 0.17))
        rig.rigid("eye." + side, tube([Vector((0.05 * s, -0.08, Z + 0.05)), e + Vector((0, 0.005, -0.03))], [0.014, 0.011],
                                      shell2, verts=8),
                  sphere(0.03, tuple(e), eye, segs=12, rings=8),
                  sphere(0.012, tuple(e + Vector((0, -0.026, 0.004))), pupil, scale=(1, 0.5, 1), segs=8, rings=5))
        rig.rigid("arm." + side, tube([Vector((0.12 * s, -0.06, Z - 0.02)), Vector((0.2 * s, -0.16, Z))], [0.024, 0.022],
                                      shell, verts=10))
        # a big claw: the palm (fixed half) and the pincer (moving finger)
        rig.rigid("claw." + side, ell((0.235 * s, -0.2, Z + 0.02), (0.075, 0.09, 0.06), shell, yaw=30 * s, segs=18,
                                      rings=12),
                  sphere(0.012, (0.25 * s, -0.25, Z + 0.07), spot, scale=(1, 1, 0.5), segs=8, rings=5),
                  rod((0.25 * s, -0.26, Z + 0.045), (0.28 * s, -0.34, Z + 0.045), 0.03, shell2, r2=0.005, verts=10))
        rig.rigid("pincer." + side, rod((0.235 * s, -0.25, Z - 0.005), (0.285 * s, -0.33, Z - 0.012), 0.022, shell2,
                                        r2=0.005, verts=10))
        for k in range(3):
            y = -0.03 + 0.06 * k
            rig.rigid("leg%d.%s" % (k, side), tube([Vector((0.13 * s, y, Z - 0.03)), Vector((0.21 * s, y + 0.01, Z + 0.04))],
                                                   [0.024, 0.019], shell, verts=10),
                      sphere(0.021, (0.21 * s, y + 0.01, Z + 0.04), shell2, segs=10, rings=6))
            rig.rigid("foot%d.%s" % (k, side), tube([Vector((0.21 * s, y + 0.01, Z + 0.04)), Vector((0.245 * s, y + 0.015, 0.03)),
                                                     Vector((0.26 * s, y + 0.02, 0.0))],
                                                    [0.018, 0.012, 0.004], shell, verts=10))
    rig.build("guardian_crab")
    N = 18

    def walk(t):
        p = {}
        for side, s in (("L", 1), ("R", -1)):
            for k in range(3):
                ph = (t + (0.5 if (k + (side == "R")) % 2 else 0.0)) % 1.0
                lift = max(0.0, math.sin(2 * math.pi * ph))
                swing = math.cos(2 * math.pi * ph)
                p["leg%d.%s" % (k, side)] = (0, -s * 25 * lift, 10 * swing)
                p["foot%d.%s" % (k, side)] = (0, s * 15 * lift, 0)
        a = 2 * math.pi * t
        clack = max(0.0, math.sin(2 * a)) ** 3
        p.update({"@root": (0.012 * math.sin(a), 0, 0.01 * abs(math.sin(2 * a))), "body": (0, 5 * math.sin(a), 0),
                  "stalk": (6 * math.sin(a), -8 * math.sin(a + 0.8), 0), "lantern": (10 * math.sin(a + 1.4), 14 * math.sin(a + 1.8), 0),
                  "eye.L": (8 * math.sin(a), 0, 6), "eye.R": (8 * math.sin(a + 1), 0, -6),
                  "arm.L": (10 + 8 * math.sin(a), 0, 0), "arm.R": (10 + 8 * math.sin(a + math.pi), 0, 0),
                  "pincer.L": (-30 * clack, 0, 0), "pincer.R": (-30 * clack, 0, 0)})
        return p
    rig.action("move", keys_fn(N, walk, 2), loop=True)
    rig.save("guardian_crab")


def guardian_gear():
    """A rolling cog 0.62 across with an eye in its hub, side view (it rolls in the picture plane). Root
    "guardian_gear" (the brass hub with the eye and lids, stays upright; origin at the floor under the axle) with
    children "cog" (pivot on the axle 0.31 up) and "lids"."""
    steel = mat("gear_steel", (0.55, 0.57, 0.62), 0.3, 1.0)
    dark = mat("gear_dark", (0.2, 0.2, 0.23), 0.4, 0.8)
    brass = mat("gear_brass", (0.95, 0.7, 0.3), 0.3, 0.9)
    copper = mat("gear_copper", (0.85, 0.45, 0.28), 0.35, 0.9)
    white = mat("gear_eye_white", (0.96, 0.95, 0.9), 0.3)
    iris = mat("gear_glow", (1.0, 0.25, 0.2), 0.3, emit=7.0)
    pupil = mat("gear_pupil", (0.02, 0.02, 0.02), 0.2, coat=1.0)
    C = Vector((0, 0, 0.31))
    # the cog: a toothed rim, four curved spokes, rivets, a copper inner ring
    cp = [gear(0.25, 0.1, (0, 0, 0), steel, teeth=14, rot=(R90, 0, 0), tooth=0.07)]
    inner = cyl(0.2, 0.12, (0, 0, 0), dark, rot=(R90, 0, 0), verts=40)
    cp.append(inner)
    cp.append(torus(0.205, 0.014, (0, -0.062, 0), copper, rot=(R90, 0, 0), verts=40, minor=6))
    for kk in range(5):
        a = 2 * math.pi * kk / 5
        pts = [(0.09 * math.cos(a), -0.055, 0.09 * math.sin(a)), (0.15 * math.cos(a + 0.18), -0.055, 0.15 * math.sin(a + 0.18)),
               (0.2 * math.cos(a + 0.3), -0.055, 0.2 * math.sin(a + 0.3))]
        cp.append(tube(pts, [0.022, 0.02, 0.022], steel, verts=8))
        cp.append(sphere(0.012, (0.225 * math.cos(a + 0.6), -0.07, 0.225 * math.sin(a + 0.6)), brass, scale=(1, 0.5, 1),
                         segs=8, rings=5))
    for o in cp:
        xf(o, Matrix.Translation(C))
    # cut the dark inner disc's front so the hub reads as a hole: it's behind the spokes (y > -0.05)
    cog = join(cp, "cog", pivot=tuple(C))
    # the hub: a brass ring round an eyeball, facing the camera, glancing towards +X
    hp = [torus(0.085, 0.022, tuple(C + Vector((0, -0.075, 0))), brass, rot=(R90, 0, 0), verts=28, minor=8),
          cyl(0.09, 0.14, tuple(C + Vector((0, 0.0, 0))), dark, rot=(R90, 0, 0), verts=24),
          sphere(0.075, tuple(C + Vector((0, -0.05, 0))), white, segs=22, rings=14)]
    for kk in range(8):
        a = 2 * math.pi * kk / 8
        hp.append(sphere(0.008, tuple(C + Vector((0.085 * math.cos(a), -0.1, 0.085 * math.sin(a)))), dark, segs=6, rings=4))
    iris_o = cyl(0.036, 0.01, (0, 0, 0), iris, verts=20)
    pup = cyl(0.016, 0.012, (0, 0, 0.003), pupil, verts=14)
    look = Vector((0.45, -1, 0.1)).normalized()
    Rl = Vector((0, 0, 1)).rotation_difference(look).to_matrix().to_4x4()
    for o in (iris_o, pup):
        xf(o, Matrix.Translation(C + Vector((0, -0.05, 0)) + look * 0.071) @ Rl)
    hp += [iris_o, pup]
    # a bracket arm from the hub to a little rudder of a tail (so the hub reads as a creature), steam puffs vent
    hp.append(rod(C + Vector((-0.05, 0.07, 0.02)), C + Vector((-0.16, 0.08, 0.2)), 0.014, brass, verts=8))
    hp.append(sphere(0.03, tuple(C + Vector((-0.16, 0.08, 0.21))), copper, segs=10, rings=6))
    hub = join(hp, "guardian_gear")
    lp = []
    for sgn in (1, -1):               # upper and lower lids, closed by scaling
        l = sphere(0.079, (0, 0, 0), mat("gear_lid", (0.36, 0.36, 0.4), 0.35, 0.7), segs=22, rings=12)
        edit(l, lambda bm, sgn=sgn: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z * sgn < 0.03],
                                                     context="VERTS"))
        l.data.transform(Matrix.Translation(C + Vector((0, -0.05, 0))) @ Matrix.Rotation(math.radians(-14 * sgn), 4, "Y"))
        lp.append(l)
    lids = join(lp, "lids", pivot=tuple(C + Vector((0, -0.05, 0))))
    N = 36
    animate(cog, "move", {f: {"rot": (0, 2 * math.pi * f / N, 0)} for f in range(0, N + 1, 2)}, linear=True)
    animate(hub, "move", keys_fn(N, lambda t: {"loc": (0, 0, 0.012 * abs(math.sin(2 * math.pi * t * 14 / 2)))}, 1),
            linear=True)
    animate(lids, "move", {0: {"scale": (1, 1, 0.55)}, 20: {"scale": (1, 1, 0.55)}, 23: {"scale": (1, 1, 1.25)},
                           26: {"scale": (1, 1, 0.55)}, 36: {"scale": (1, 1, 0.55)}}, linear=False)
    export_tree(hub, "guardian_gear", [(cog, hub), (lids, hub)])


def guardian_snowball():
    """A grumpy snow blob 0.5 wide, 0.56 tall: packed snow, glowing icy eyes under coal brows, a coal frown,
    twig arms, an icicle beard, a tuft of frost. Root "guardian_snowball" (an empty at the base centre, turned 30
    degrees towards the camera) with child "body" (arm_l, arm_r); animation move (loop 0.7 s: a squashy waddle-hop)."""
    snow = mat("snow_body", (0.93, 0.96, 1.0), 0.6, coat=0.2)
    snow2 = mat("snow_shade", (0.78, 0.86, 0.98), 0.7)
    coal = mat("snow_coal", (0.06, 0.06, 0.07), 0.35, coat=0.4)
    glow = mat("snowball_glow", (0.4, 0.85, 1.0), 0.3, emit=8.0)
    ice = mat("snow_ice", (0.7, 0.88, 1.0), 0.05, coat=1.0, alpha=0.7)
    twig = mat("snow_twig", (0.36, 0.22, 0.12), 0.8)
    body = [lumpy(0.25, (0, 0, 0.25), snow, 31, 0.06, scale=(1.0, 0.92, 1.05), sub=3, smooth=60),
            lumpy(0.17, (0, 0.02, 0.43), snow, 32, 0.05, scale=(1.0, 0.95, 0.85), sub=3, smooth=60)]
    rnd = random.Random(33)
    for kk in range(9):               # clumps round the base
        a = rnd.uniform(0, 2 * math.pi)
        body.append(lumpy(rnd.uniform(0.05, 0.08), (0.22 * math.cos(a), 0.2 * math.sin(a), 0.05), snow2, 40 + kk, 0.2,
                          sub=2, smooth=60))
    for s in (-1, 1):
        e = Vector((0.08 * s, -0.19, 0.38))
        body.append(sphere(0.045, tuple(e), glow, scale=(1, 0.5, 0.8), segs=14, rings=8))
        body.append(sphere(0.016, tuple(e + Vector((0.0, -0.02, -0.005))), coal, scale=(1, 0.5, 1), segs=8, rings=5))
        b = box((0.11, 0.035, 0.03), (0, 0, 0), coal, bevel=0.01)
        b.data.transform(Matrix.Translation(e + Vector((0.01 * s, -0.012, 0.055))) @ Matrix.Rotation(math.radians(-20 * s), 4, "Y"))
        body.append(b)
    for kk in range(5):               # a coal frown
        u = (kk - 2) / 2
        body.append(sphere(0.017, (0.07 * u, -0.225 + 0.02 * abs(u), 0.27 - 0.025 * (1 - u * u)), coal, segs=8, rings=5))
    for kk in range(6):               # icicle beard
        x = -0.1 + 0.04 * kk
        L = 0.05 + 0.03 * ((kk * 7) % 3)
        body.append(cyl(0.014, L, (x, -0.2 + 0.03 * abs(x) * 3, 0.2 - L / 2), ice, r2=0.0, verts=6))
    for kk in range(4):               # frost tuft on top
        body.append(rod((0, 0.02, 0.56), (0.03 * (kk - 1.5), 0.02 + 0.01 * kk, 0.63 + 0.01 * (kk % 2)), 0.02, snow,
                        r2=0.003, verts=6))
    B = join(body, "body")
    arms = []
    for nm, s in (("arm_l", 1), ("arm_r", -1)):
        sh_ = Vector((0.22 * s, 0.0, 0.3))
        ap = [rod(sh_, sh_ + Vector((0.14 * s, -0.02, 0.1)), 0.013, twig, r2=0.008, verts=6),
              rod(sh_ + Vector((0.09 * s, -0.01, 0.06)), sh_ + Vector((0.13 * s, -0.03, 0.14)), 0.007, twig, r2=0.003,
                  verts=5),
              rod(sh_ + Vector((0.14 * s, -0.02, 0.1)), sh_ + Vector((0.2 * s, -0.02, 0.11)), 0.006, twig, r2=0.003,
                  verts=5),
              rod(sh_ + Vector((0.14 * s, -0.02, 0.1)), sh_ + Vector((0.17 * s, -0.02, 0.17)), 0.006, twig, r2=0.003,
                  verts=5)]
        arms.append(join(ap, nm, pivot=tuple(sh_)))
    root = empty("guardian_snowball")
    N = 21

    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a)) ** 0.8
        land = max(0.0, -math.sin(a))
        return {"loc": (0, 0, 0.07 * hop), "rot": (math.radians(-6 * math.cos(a)), math.radians(8 * math.sin(a * 0.5 + 0.3)) * 0, 0),
                "scale": (1 + 0.12 * land - 0.04 * hop, 1 + 0.12 * land - 0.04 * hop, 1 - 0.16 * land + 0.06 * hop)}
    animate(B, "move", keys_fn(N, f, 1), linear=False)
    for a_, s in zip(arms, (1, -1)):
        animate(a_, "move", keys_fn(N, lambda t, s=s: {"rot": (0, math.radians(s * (25 * math.sin(2 * math.pi * t) - 10)), 0)}, 1),
                linear=False)
    export_tree(root, "guardian_snowball", [(B, root)] + [(a_, B) for a_ in arms], yaw=55)



# ------------------------------------------------------------------ tiles (0.5 cube, origin at the centre, front at -Y)

H = TILE / 2       # 0.25


def rock_mats():
    return (mat("tile_rock", (0.36, 0.27, 0.21), 0.8), mat("tile_rock_dark", (0.13, 0.1, 0.085), 0.9),
            mat("tile_rock_light", (0.47, 0.38, 0.3), 0.75))


def stone(c, size, material, seed, amount=0.14, sub=2, rot=0.0, smooth=0):
    """A chunky cobble: an icosphere pushed about, squashed flat front to back (smooth: auto-smooth angle)."""
    o = lumpy(1.0, (0, 0, 0), material, seed, amount, sub=sub, smooth=smooth)
    xf(o, Matrix.Translation(c) @ Matrix.Rotation(rot, 4, "Y") @ Matrix.Diagonal(Vector(size)).to_4x4())
    return o


def clamp_tile(o, lim=H, front=-H - 0.03, back=H):
    """Keeps every vertex inside the cell (so neighbours never overlap) and no further forward than `front`."""
    for v in o.data.vertices:
        v.co.x = max(-lim, min(lim, v.co.x))
        v.co.z = max(-lim, min(lim, v.co.z))
        v.co.y = max(front, min(back, v.co.y))
    o.data.update()
    return o


def rock_base(dark, front=-H + 0.004):
    """The dark grit the stones sit in, from `front` back to the tile's back face."""
    return box((TILE - 0.004, H - front, TILE - 0.004), (0, (H + front) / 2, 0), dark, bevel=0.012)


def cobbles(rows, rnd, mats, seed, y=-0.18, skip=(), n=3):
    """Cobbles packed over the front face in a jittered grid (rows x n), bulging to about -0.27."""
    out = []
    for j in range(rows):
        for i in range(n):
            if (i, j) in skip:
                continue
            w, h = TILE / n, TILE / rows
            x = -H + w * (i + 0.5) + rnd.uniform(-0.02, 0.02) + (0.09 / n if j % 2 else -0.09 / n)
            z = -H + h * (j + 0.5) + rnd.uniform(-0.015, 0.015)
            sz = (w * rnd.uniform(0.52, 0.64), rnd.uniform(0.07, 0.085), h * rnd.uniform(0.5, 0.62))
            m = mats[rnd.randrange(len(mats))]
            out.append(clamp_tile(stone((x, y, z), sz, m, seed + 10 * j + i, amount=0.22, sub=2,
                                        rot=rnd.uniform(-0.4, 0.4), smooth=32), front=-H - 0.025))
    for i in range(3):                # a few on the top face, so an exposed top reads as rock too
        x = -H + TILE / 3 * (i + 0.5) + rnd.uniform(-0.02, 0.02)
        out.append(clamp_tile(stone((x, rnd.uniform(-0.05, 0.1), H - 0.06), (0.1, 0.13, 0.07), mats[i % len(mats)],
                                    seed + 90 + i, amount=0.22, sub=2, smooth=32), front=-H - 0.02))
    return out


def tile_rock(variant):
    """A block of cave rock: a: four big rounded stones packed in dark grit; b: smaller rubble (3 x 3); c: four
    stones split by a glowing crystal vein (tile_crystal_glow, tile_crystal)."""
    rock, dark, light = rock_mats()
    parts = [rock_base(dark, -0.19)]
    rnd = random.Random({"a": 11, "b": 12, "c": 13}[variant])
    if variant == "a":
        parts += cobbles(2, rnd, (rock, rock, light, rock), 100, n=2, y=-0.17)
    elif variant == "b":
        parts += cobbles(3, rnd, (rock, light, rock), 150, y=-0.18)
    else:
        parts += cobbles(3, rnd, (rock, light, rock), 200, skip=((0, 1), (1, 1)), n=2, y=-0.18)
        glow = mat("tile_crystal_glow", (0.35, 0.85, 1.0), 0.15, emit=2.5)
        core = mat("tile_crystal", (0.55, 0.9, 1.0), 0.05, coat=1.0)
        pts = [(-H, -0.03), (-0.1, 0.0), (0.0, 0.03), (0.1, -0.01), (H, 0.03)]
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            parts.append(clamp_tile(rod((x0, -0.19, z0), (x1, -0.19, z1), 0.04, dark, verts=6)))
            parts.append(clamp_tile(rod((x0, -0.215, z0), (x1, -0.215, z1), 0.024, glow, verts=6)))
        for kk, (x, z, ang, L) in enumerate(((-0.17, -0.02, 0.5, 0.12), (-0.07, 0.01, -0.35, 0.15),
                                             (0.03, 0.03, 0.2, 0.1), (0.15, 0.0, -0.5, 0.13), (0.2, 0.04, 0.6, 0.08))):
            d = Vector((math.sin(ang) * 0.6, -1.0, math.cos(ang) * 0.5)).normalized()
            c0 = Vector((x, -0.19, z))
            parts.append(clamp_tile(rod(c0, c0 + d * L * 0.6, 0.026, core if kk % 2 else glow, r2=0.0, verts=6),
                                    front=-H - 0.05))
    simple(parts, "tile_rock_" + variant)


def wood_mats():
    return (mat("tile_wood", (0.6, 0.4, 0.22), 0.75), mat("tile_wood_dark", (0.4, 0.25, 0.13), 0.8),
            mat("tile_iron", (0.26, 0.26, 0.28), 0.4, 0.7))


def plank_deck(material_a, material_b, iron, seed, broken=False):
    """A deck of planks running front to back, top at +0.25, 0.06 thick; stringers underneath."""
    rnd = random.Random(seed)
    parts = []
    n = 4
    w = TILE / n
    for kk in range(n):
        x = -H + w * (kk + 0.5)
        m = material_a if kk % 2 == 0 else material_b
        dz = rnd.uniform(-0.006, 0.0)
        if broken and kk in (1, 2):
            # split in two along its length with a gap, one half sagging
            for half, (y0, y1) in enumerate(((-H, -0.02), (0.02, H))):
                o = box((w - 0.008, y1 - y0, 0.055), (x + (0.006 if half else -0.004), (y0 + y1) / 2, H - 0.0275 + dz),
                        m, rot=(math.radians(6 if half == 0 and kk == 1 else 0), 0, 0), bevel=0.008)
                parts.append(o)
            continue
        o = box((w - 0.008, TILE - 0.004, 0.055), (x, 0, H - 0.0275 + dz), m,
                rot=(0, math.radians(rnd.uniform(-1.2, 1.2)), 0), bevel=0.01)
        for v in o.data.vertices:
            v.co.z += rnd.uniform(-0.002, 0.002)
        parts.append(o)
        if not broken:
            for x_ in (x - w * 0.25, x + w * 0.25):     # nail heads on the plank ends
                parts.append(sphere(0.007, (x_, -H + 0.02, H + 0.001), iron, scale=(1, 1, 0.4), segs=8, rings=4))
    for y in (-0.19, 0.19):
        parts.append(box((TILE, 0.06, 0.08), (0, y, H - 0.055 - 0.04), material_b, bevel=0.012))
    return parts


def tile_floor():
    """A timber walkway: four planks front to back (their ends and nail heads show at the front edge), top at +0.25,
    0.055 thick, two stringers under it to +0.10; open below (the cavern shows through)."""
    wood, dark, iron = wood_mats()
    parts = plank_deck(wood, dark, iron, 50)
    parts.append(box((TILE, 0.012, 0.028), (0, -0.2 - 0.036, H - 0.075), iron, bevel=0.004))     # an iron strap
    for x in (-0.2, 0.0, 0.2):
        parts.append(sphere(0.008, (x, -0.245, H - 0.075), iron, scale=(1, 0.5, 1), segs=8, rings=4))
    simple(parts, "tile_floor")


def tile_crumble():
    """A rotten walkway (same footprint as tile_floor, deck +0.14 .. +0.25): pale wet timber, two planks split
    with one half sagging, cracks, splinters, a fungus bracket and drips of mud."""
    wood = mat("tile_crumble_wood", (0.55, 0.47, 0.34), 0.9)
    dark = mat("tile_crumble_dark", (0.33, 0.27, 0.18), 0.9)
    crack = mat("tile_crumble_crack", (0.08, 0.06, 0.04), 0.9)
    fungus = mat("tile_crumble_fungus", (0.86, 0.72, 0.5), 0.7)
    parts = plank_deck(wood, dark, mat("tile_iron", (0.26, 0.26, 0.28), 0.4, 0.7), 51, broken=True)
    rnd = random.Random(52)
    for kk in range(6):               # dark cracks along the planks' tops and front ends
        x = rnd.uniform(-0.22, 0.22)
        y = rnd.uniform(-0.2, 0.15)
        L = rnd.uniform(0.06, 0.12)
        parts.append(box((0.006, L, 0.004), (x, y, H + 0.001), crack, rot=(0, 0, rnd.uniform(-0.2, 0.2)), bevel=0.0))
    for kk in range(5):
        x = rnd.uniform(-0.22, 0.22)
        parts.append(box((0.004, 0.004, 0.035), (x, -H - 0.001, H - 0.03), crack, rot=(0, rnd.uniform(-0.5, 0.5), 0),
                         bevel=0.0))
    for kk in range(5):               # splinters sticking out of the broken ends
        x = -0.09 + 0.045 * kk
        parts.append(rod((x, -0.01, H - 0.02), (x + rnd.uniform(-0.02, 0.02), -0.0, H - 0.07 - rnd.uniform(0, 0.04)), 0.006,
                         wood, r2=0.001, verts=4))
    parts.append(sphere(0.045, (0.17, -H - 0.005, H - 0.085), fungus, scale=(1.2, 0.6, 0.35), segs=12, rings=6))
    parts.append(sphere(0.03, (0.12, -H - 0.004, H - 0.1), fungus, scale=(1.2, 0.6, 0.35), segs=10, rings=6))
    for x, L in ((-0.15, 0.05), (-0.02, 0.035), (0.08, 0.06)):
        parts.append(cyl(0.01, L, (x, -0.2, H - 0.13 - L / 2), dark, r2=0.002, verts=6))
    simple(parts, "tile_crumble")


def belt_texture():
    """A 64 x 16 rubber belt texture: four raised ribs per repeat (one repeat per tile), packed into the file."""
    W, Hh = 64, 16
    img = bpy.data.images.new("conveyor_belt", W, Hh)
    px = []
    for y in range(Hh):
        for x in range(W):
            u = (x % 16) / 16
            v = 0.14 + 0.03 * math.sin(y * 1.3)
            if u < 0.25:
                v = 0.34 + 0.12 * math.sin(math.pi * u / 0.25)       # a rib, lit on its top
            elif u < 0.32:
                v = 0.05
            edge = min(y, Hh - 1 - y)
            if edge < 2:
                v *= 0.6
            px += [v * 1.0, v * 0.97, v * 0.92, 1.0]
    img.pixels = px
    img.pack()
    return img


def tile_conveyor():
    """A conveyor segment 0.5 wide: an iron frame (front plate with two roller windows), top +0.25. Child "belt"
    (the rubber top, one texture repeat per tile) whose material "conveyor_belt" the game scrolls: uv1_offset.x -=
    d / 0.5 moves the ribs d units towards +X. Children "roller_a", "roller_b" (x = -0.125 / +0.125, radius 0.07,
    axle at +0.14 up): spin them about Godot Z by -d / 0.07 for a belt moving d towards +X."""
    iron = mat("conveyor_iron", (0.3, 0.3, 0.33), 0.4, 0.7)
    paint = mat("conveyor_paint", (0.85, 0.62, 0.12), 0.45, 0.3, coat=0.4)
    dark = mat("conveyor_dark", (0.08, 0.08, 0.09), 0.5)
    steel = mat("conveyor_steel", (0.7, 0.72, 0.76), 0.25, 1.0)
    AZ = H - 0.11
    parts = [box((TILE, 0.4, 0.12), (0, 0.02, AZ), dark, bevel=0.005)]
    # the front plate: yellow paint with black hazard stripes along its bottom edge, two round windows
    fp = box((TILE, 0.03, 0.2), (0, -0.215, H - 0.12), paint, bevel=0.008)
    parts.append(fp)
    parts.append(box((TILE, 0.012, 0.05), (0, -0.232, H - 0.19), dark, bevel=0.0))
    for kk in range(5):               # yellow chevrons on a black band along the bottom
        x = -0.2 + 0.1 * kk
        parts.append(box((0.022, 0.006, 0.062), (x, -0.24, H - 0.19), paint, rot=(0, math.radians(35), 0), bevel=0.0))
    for x in (-0.125, 0.125):
        parts.append(torus(0.078, 0.012, (x, -0.235, AZ), iron, rot=(R90, 0, 0), verts=24, minor=6))
        parts.append(cyl(0.07, 0.01, (x, -0.226, AZ), dark, rot=(R90, 0, 0), verts=24))
    for x in (-0.24, 0.0, 0.24):
        parts.append(sphere(0.009, (x, -0.232, H - 0.04), iron, scale=(1, 0.5, 1), segs=8, rings=4))
    parts.append(box((TILE, 0.02, 0.02), (0, 0.21, H - 0.03), iron, bevel=0.004))      # the back rail
    body = join(parts, "tile_conveyor")
    # the belt with UVs: u runs along X (one repeat per tile), v across
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    y0, y1, zt, zb = -0.2, 0.2, H + 0.002, H - 0.02
    quads = [((-H, y0, zt), (H, y0, zt), (H, y1, zt), (-H, y1, zt)),
             ((-H, y0, zb), (H, y0, zb), (H, y0, zt), (-H, y0, zt))]
    for q in quads:
        vs = [bm.verts.new(p) for p in q]
        f = bm.faces.new(vs)
        for l in f.loops:
            l[uv].uv = (l.vert.co.x / TILE + 0.5, (l.vert.co.y - y0) / (y1 - y0) if l.vert.co.z > zt - 1e-4 else 0.0)
    me = bpy.data.meshes.new("belt")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    belt = bpy.data.objects.new("belt", me)
    bpy.context.scene.collection.objects.link(belt)
    for poly in me.polygons:          # the top faces up, the front faces the camera
        if poly.normal.z < -0.5 or poly.normal.y > 0.5:
            poly.flip()
    bm_ = mat("conveyor_belt", (1, 1, 1), 0.7)
    nt = bm_.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = belt_texture()
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    belt.data.materials.append(bm_)
    rollers = []
    for nm, x in (("roller_a", -0.125), ("roller_b", 0.125)):
        rp = [cyl(0.062, 0.38, (x, 0.0, AZ), iron, rot=(R90, 0, 0), verts=20),
              cyl(0.03, 0.02, (x, -0.22, AZ), steel, rot=(R90, 0, 0), verts=14)]
        for kk in range(3):
            a = 2 * math.pi * kk / 3
            rp.append(box((0.1, 0.012, 0.016), (x + 0.03 * math.cos(a), -0.225, AZ + 0.03 * math.sin(a)), steel,
                          rot=(0, -a, 0), bevel=0.003))
        rollers.append(join(rp, nm, pivot=(x, 0, AZ)))
    export_tree(body, "tile_conveyor", [(belt, body)] + [(r, body) for r in rollers], anim=False)


def tile_wall_brick():
    """A block of sooty mine brick: four staggered courses over dark mortar, the full depth."""
    brick = mat("tile_brick", (0.55, 0.26, 0.17), 0.85)
    brick2 = mat("tile_brick_dark", (0.38, 0.17, 0.11), 0.85)
    mortar = mat("tile_mortar", (0.2, 0.17, 0.15), 0.95)
    parts = [box((TILE - 0.01, TILE - 0.02, TILE - 0.01), (0, 0.01, 0), mortar, bevel=0.01)]
    h = TILE / 4
    g = 0.012
    rnd = random.Random(61)
    for row in range(4):
        z0 = -H + row * h
        edges = [-H, 0.0, H] if row % 2 == 0 else [-H, -0.125, 0.125, H]
        for a, b in zip(edges, edges[1:]):
            x0 = a + (g / 2 if a > -H else 0.0)
            x1 = b - (g / 2 if b < H else 0.0)
            o = box((x1 - x0, TILE, h - g), ((x0 + x1) / 2, 0.0, z0 + h / 2), brick if rnd.random() < 0.7 else brick2,
                    bevel=0.01)
            for v in o.data.vertices:
                if v.co.y < 0:
                    v.co.y += rnd.uniform(-0.004, 0.004)
            parts.append(o)
    simple(parts, "tile_wall_brick")


def tile_ice():
    """A block of glacier ice (tile_ice, tile_ice_deep, cracks in tile_ice_crack), a cap of snow on top rolling
    over the front edge (tile_snow) and three short icicles under the front edge (down to -0.36: they hang into
    the cell below)."""
    ice = mat("tile_ice", (0.62, 0.84, 0.98), 0.06, coat=1.0)
    deep = mat("tile_ice_deep", (0.3, 0.56, 0.86), 0.1, coat=1.0)
    crack = mat("tile_ice_crack", (0.92, 0.97, 1.0), 0.3)
    snow = mat("tile_snow", (0.95, 0.97, 1.0), 0.6)
    parts = [box((TILE - 0.004, TILE - 0.01, TILE - 0.004), (0, 0.004, 0), deep, bevel=0.02)]
    rnd = random.Random(71)
    for kk, (x, z, sx, sz) in enumerate(((-0.12, -0.1, 0.12, 0.13), (0.12, -0.12, 0.12, 0.12), (0.0, 0.11, 0.2, 0.1))):
        o = ico(1.0, (0, 0, 0), ice, sub=1, smooth=0)
        for v in o.data.vertices:
            v.co *= 1 + rnd.uniform(-0.1, 0.1)
        xf(o, Matrix.Translation((x, -0.18, z)) @ Matrix.Diagonal(Vector((sx, 0.08, sz))).to_4x4())
        parts.append(clamp_tile(o))
    for kk in range(4):
        x0, z0 = rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.15)
        parts.append(clamp_tile(rod((x0, -0.255, z0), (x0 + rnd.uniform(-0.08, 0.08), -0.255, z0 + rnd.uniform(0.03, 0.08)),
                                    0.004, crack, verts=4)))
    parts.append(box((TILE, TILE - 0.01, 0.04), (0, 0.004, H - 0.005), snow, bevel=0.015))
    for kk in range(7):
        x = -H + 0.035 + 0.072 * kk
        parts.append(sphere(0.04, (x, -0.24, H - 0.012), snow, scale=(1.0, 0.7, 0.65), segs=10, rings=6))
    for x, L in ((-0.17, 0.09), (0.02, 0.06), (0.15, 0.11)):
        parts.append(cyl(0.022, L, (x, -0.21, -H - L / 2 + 0.01), ice, r2=0.0, verts=7))
    simple(parts, "tile_ice")


# ------------------------------------------------------------------ hazards (in their own cell, standing on its floor)

def hazard_spikes():
    """Four iron spikes in a rusty plate on the cell's floor (-0.25), tips up to +0.12."""
    iron = mat("spikes_iron", (0.3, 0.3, 0.33), 0.35, 0.8)
    tip = mat("spikes_tip", (0.85, 0.87, 0.9), 0.2, 1.0)
    rust = mat("spikes_rust", (0.5, 0.22, 0.1), 0.8, 0.2)
    parts = [box((TILE - 0.02, 0.36, 0.035), (0, 0, -H + 0.0175), rust, bevel=0.01)]
    for kk, (x, h) in enumerate(((-0.18, 0.3), (-0.06, 0.37), (0.06, 0.33), (0.18, 0.36))):
        b = Vector((x, -0.04 * (kk % 2), -H + 0.035))
        parts.append(cyl(0.035, h * 0.72, tuple(b + Vector((0, 0, h * 0.36))), iron, r2=0.012, verts=8))
        parts.append(cyl(0.012, h * 0.28, tuple(b + Vector((0, 0, h * 0.72 + h * 0.14))), tip, r2=0.0, verts=8))
        parts.append(torus(0.036, 0.008, tuple(b + Vector((0, 0, 0.012))), iron, verts=12, minor=4))
    for x in (-0.22, 0.22):
        parts.append(sphere(0.01, (x, -0.17, -H + 0.035), iron, scale=(1, 1, 0.5), segs=8, rings=4))
    simple(parts, "hazard_spikes")


def hazard_plant():
    """A poisonous cave plant rooted on the cell's floor (-0.25), 0.5 tall: a swollen stem, barbed leaves, a
    nodding bulb and glowing seed pods (hazard_plant_glow). Armature "plant_rig" (stem1..3, leaf bones), mesh
    "hazard_plant"; animation sway (loop 2 s)."""
    stem_m = mat("plant_stem", (0.3, 0.42, 0.2), 0.6, coat=0.3)
    leaf_m = mat("plant_leaf", (0.22, 0.36, 0.2), 0.55, coat=0.3)
    vein = mat("plant_vein", (0.7, 0.2, 0.55), 0.5)
    glow = mat("hazard_plant_glow", (0.85, 1.0, 0.2), 0.3, emit=7.0)
    thorn = mat("plant_thorn", (0.95, 0.85, 0.7), 0.4)
    Z0 = -H
    B = {"root": ((0, 0, Z0), (0, 0, Z0 + 0.05), None),
         "stem1": ((0, 0, Z0 + 0.02), (0.01, 0, Z0 + 0.16), "root"),
         "stem2": ((0.01, 0, Z0 + 0.16), (0.0, 0, Z0 + 0.3), "stem1"),
         "stem3": ((0.0, 0, Z0 + 0.3), (0.04, -0.01, Z0 + 0.42), "stem2")}
    leaves = [("leaf0", "stem1", Z0 + 0.06, 1, 0.16, 20), ("leaf1", "stem1", Z0 + 0.1, -1, 0.14, 35),
              ("leaf2", "stem2", Z0 + 0.2, 1, 0.12, 40), ("leaf3", "stem2", Z0 + 0.24, -1, 0.11, 50)]
    for nm, par, z, s, L, up in leaves:
        B[nm] = ((0.01 * s, 0, z), (s * L * math.cos(math.radians(up)), -0.02, z + L * math.sin(math.radians(up))), par)
    rig = Rig(B)
    rig.smooth(["stem1", "stem2", "stem3"],
               limb([(0, 0, Z0), (0.012, 0, Z0 + 0.1), (0.008, 0, Z0 + 0.22), (0.0, 0, Z0 + 0.32), (0.04, -0.01, Z0 + 0.4)],
                    [0.03, 0.022, 0.02, 0.016, 0.014], stem_m, verts=10, per=3, caps=True))
    rnd = random.Random(81)
    for nm, par, z, s, L, up in leaves:
        # a barbed leaf: a flattened, pointed lozenge with a purple midrib and white thorns along its edge
        a = math.radians(up)
        d = Vector((s * math.cos(a), -0.15, math.sin(a))).normalized()
        base = Vector((0.01 * s, 0, z))
        lf = sphere(1.0, (0, 0, 0), leaf_m, scale=(L / 2, 0.035, 0.008), segs=14, rings=6)
        for v in lf.data.vertices:
            u = (v.co.x + L / 2) / L
            v.co.y *= 0.3 + 1.2 * math.sin(math.pi * min(1.0, u * 1.1))
            v.co.z += 0.04 * u * u
        M = Matrix.Translation(base) @ Vector((1, 0, 0)).rotation_difference(d).to_matrix().to_4x4() @ \
            Matrix.Rotation(math.radians(70), 4, "X") @ Matrix.Translation((L / 2, 0, 0))
        xf(lf, M)
        rib = rod(base, base + d * L * 0.9, 0.004, vein, verts=4)
        th = []
        for k in range(4):
            p = base + d * L * (0.25 + 0.18 * k)
            th.append(rod(p, p + Vector((0, 0, 0.025)) + d * 0.01, 0.004, thorn, r2=0.0, verts=4))
        rig.rigid(nm, lf, rib, *th)
    # the nodding bulb with glowing pods
    Bc = Vector((0.05, -0.012, Z0 + 0.43))
    bulb = [sphere(0.05, tuple(Bc), stem_m, scale=(1.0, 1.0, 0.85), segs=16, rings=10)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        bulb.append(sphere(0.024, tuple(Bc + Vector((0.045 * math.cos(a), 0.045 * math.sin(a) * 0.8, 0.015 + 0.01 * (k % 2)))),
                           glow, segs=10, rings=6))
    bulb.append(sphere(0.03, tuple(Bc + Vector((0, 0, 0.04))), glow, segs=12, rings=8))
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        bulb.append(rod(Bc + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.02)),
                        Bc + Vector((0.07 * math.cos(a), 0.07 * math.sin(a), -0.05)), 0.006, thorn, r2=0.0, verts=4))
    rig.rigid("stem3", *bulb)
    for k in range(3):                # two more pods on short stalks from the stem
        p = Vector((0.03 * (1 if k % 2 else -1), -0.01, Z0 + 0.14 + 0.08 * k))
        q = p + Vector((0.04 * (1 if k % 2 else -1), -0.01, 0.03))
        rig.rigid("stem1" if k == 0 else "stem2", rod(p, q, 0.006, stem_m, verts=5),
                  sphere(0.018, tuple(q), glow, segs=8, rings=6))
    rig.build("hazard_plant")
    rig.arm.name = "plant_rig"
    N = 60

    def sway(t):
        a = 2 * math.pi * t
        return {"stem1": (0, 4 * math.sin(a), 3 * math.sin(a + 0.5)), "stem2": (0, 6 * math.sin(a - 0.6), 4 * math.sin(a)),
                "stem3": (6 * math.sin(2 * a), 10 * math.sin(a - 1.2), 0),
                "leaf0": (0, 8 * math.sin(a + 1), 0), "leaf1": (0, -8 * math.sin(a + 2), 0),
                "leaf2": (0, 10 * math.sin(a + 2.5), 0), "leaf3": (0, -10 * math.sin(a + 0.5), 0),
                "%stem3": 1 + 0.04 * math.sin(4 * a)}
    rig.action("sway", keys_fn(N, sway, 4), loop=True)
    rig.export("hazard_plant")


def hazard_steam():
    """A steam vent in the cell's floor: a cast-iron collar with a grate, glowing hot inside (hazard_steam_glow),
    rivets and a little valve. Children steam_0..2 (translucent puffs, material steam_puff) rise from the grate in
    the animation "puff" (loop 1 s): each swells from nothing at the grate to 0.2 across near the cell's top, and
    shrinks away; hide them (or play your own particles) when the vent is off."""
    iron = mat("steam_iron", (0.24, 0.23, 0.24), 0.4, 0.7)
    brass = mat("steam_brass", (0.9, 0.66, 0.3), 0.3, 0.9)
    hot = mat("hazard_steam_glow", (1.0, 0.4, 0.12), 0.4, emit=6.0)
    puff = mat("steam_puff", (0.95, 0.97, 1.0), 0.8, emit=0.3, alpha=0.55)
    Z0 = -H
    parts = [cyl(0.16, 0.06, (0, 0, Z0 + 0.03), iron, verts=24, bevel=0.012),
             cyl(0.12, 0.08, (0, 0, Z0 + 0.07), iron, r2=0.1, verts=24, bevel=0.01),
             cyl(0.085, 0.02, (0, 0, Z0 + 0.1), hot, verts=20)]
    for k in range(4):
        parts.append(box((0.17, 0.018, 0.02), (0, -0.06 + 0.04 * k, Z0 + 0.115), iron, bevel=0.004))
    for k in range(8):
        a = 2 * math.pi * k / 8
        parts.append(sphere(0.012, (0.14 * math.cos(a), 0.14 * math.sin(a), Z0 + 0.062), brass, segs=8, rings=4))
    parts.append(rod((0.13, 0.05, Z0 + 0.05), (0.2, 0.05, Z0 + 0.08), 0.014, iron, verts=8))
    parts.append(torus(0.03, 0.007, (0.2, 0.05, Z0 + 0.1), brass, verts=12, minor=4))
    body = join(parts, "hazard_steam")
    puffs = []
    N = 30
    for k in range(3):
        rnd = random.Random(90 + k)
        pp = [sphere(0.05, (rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0.0), puff, segs=12, rings=8)]
        for j in range(3):
            a = 2 * math.pi * j / 3 + k
            pp.append(sphere(0.035, (0.04 * math.cos(a), 0.04 * math.sin(a), 0.01), puff, segs=10, rings=6))
        o = join(pp, "steam_%d" % k, pivot=(0, 0, 0))
        o.location = (0, 0, Z0 + 0.1)
        keys = {}
        for f in range(0, N + 1, 2):
            t = ((f / N) + k / 3) % 1.0
            sz = math.sin(math.pi * t) ** 0.7 * (0.5 + 1.5 * t)
            keys[f] = {"loc": (0.02 * math.sin(6 * t + k), 0, 0.38 * t), "scale": (sz, sz, sz * 0.9),
                       "rot": (0, 0, t * 2)}
        # the wrap at t = 1 -> 0 happens where the scale is 0, so the loop is seamless
        animate(o, "puff", keys, linear=True)
        puffs.append(o)
    export_tree(body, "hazard_steam", [(p_, body) for p_ in puffs])


# ------------------------------------------------------------------ items

def key():
    """A crystal key 0.42 long standing upright (bow at the top), tilted 15 degrees, origin at its centre (float
    it in the cell): a faceted crystal bow (key_glow, emissive: recolour or pulse it to flash), a brass collar,
    shaft and teeth tipped with crystal. Animation spin (loop 2 s): a full turn about the vertical and a 0.03 bob."""
    glow = mat("key_glow", (0.4, 0.95, 1.0), 0.1, emit=2.5)
    brass = mat("key_brass", (1.0, 0.76, 0.32), 0.25, 1.0)
    gem = mat("key_gem", (1.0, 0.35, 0.6), 0.1, emit=3.0)
    parts = []
    # the bow: a faceted hexagonal ring of crystal round a pink gem
    ring = torus(0.085, 0.03, (0, 0, 0), glow, rot=(R90, 0, 0), verts=6, minor=4)
    xf(ring, Matrix.Translation((0, 0, 0.12)) @ Matrix.Rotation(math.radians(30), 4, "Y"))
    K.finish(ring, glow, smooth=0)
    parts.append(ring)
    parts.append(sphere(0.03, (0, 0, 0.12), gem, scale=(1, 0.6, 1), segs=8, rings=4))
    parts.append(torus(0.034, 0.012, (0, 0, 0.12), brass, rot=(R90, 0, 0), verts=14, minor=5))
    parts.append(cyl(0.028, 0.04, (0, 0, 0.03), brass, verts=12, bevel=0.005))
    parts.append(torus(0.03, 0.008, (0, 0, 0.018), brass, verts=14, minor=4))
    parts.append(cyl(0.017, 0.2, (0, 0, -0.08), brass, verts=10))
    for z, w in ((-0.14, 0.07), (-0.175, 0.05)):
        parts.append(box((w, 0.026, 0.024), (w / 2 + 0.01, 0, z), brass, bevel=0.006))
        parts.append(ico(0.02, (w + 0.015, 0, z), glow, sub=1, smooth=0))
    parts.append(ico(0.022, (0, 0, -0.19), glow, sub=1, smooth=0))
    for o in parts:
        xf(o, Matrix.Rotation(math.radians(15), 4, "Y"))
    root = join(parts, "key")
    N = 60
    animate(root, "spin", {f: {"rot": (0, 0, 2 * math.pi * f / N), "loc": (0, 0, 0.03 * math.sin(2 * math.pi * f / N))}
                           for f in range(0, N + 1, 3)}, linear=True)
    export_tree(root, "key", [])


def portal():
    """The exit: a mine lift 1.0 wide (2 tiles), 1.12 tall to the sheave wheel, origin at the bottom centre, deck
    top at 0.04. An iron headframe with a sheave, a lit cage behind (portal_glow, warm), signal lamps on the posts
    (portal_signal_glow: recolour red while locked, green when open). Child "door": a scissor gate across the front
    (0.19 towards the camera) whose origin is on its left post; animation "open" (0.8 s): a rattle, then the gate
    folds to the left (scale.x 1 -> 0.12)."""
    iron = mat("portal_iron", (0.24, 0.24, 0.27), 0.4, 0.8)
    paint = mat("portal_paint", (0.22, 0.38, 0.32), 0.5, 0.3, coat=0.3)
    brass = mat("portal_brass", (0.95, 0.72, 0.32), 0.3, 0.9)
    wood = mat("portal_wood", (0.5, 0.32, 0.17), 0.75)
    glow = mat("portal_glow", (1.0, 0.72, 0.36), 0.5, emit=2.2)
    sig = mat("portal_signal_glow", (1.0, 0.2, 0.1), 0.3, emit=8.0)
    dark = mat("portal_dark", (0.06, 0.05, 0.05), 0.9)
    W, T = 1.0, 0.07
    parts = []
    for s in (-1, 1):                 # the posts: riveted girders
        parts.append(box((T, 0.12, 0.95), (s * (W / 2 - T / 2), -0.1, 0.475), paint, bevel=0.012))
        for z in (0.1, 0.3, 0.5, 0.7, 0.9):
            parts.append(sphere(0.009, (s * (W / 2 - T / 2), -0.162, z), brass, scale=(1, 0.5, 1), segs=8, rings=4))
        parts.append(box((0.12, 0.14, 0.04), (s * (W / 2 - T / 2), -0.1, 0.02), iron, bevel=0.01))
        # the signal lamp: a caged bulb on a bracket at the top of the post
        L = Vector((s * (W / 2 - T / 2), -0.17, 0.84))
        parts.append(cyl(0.03, 0.02, tuple(L + Vector((0, 0.015, 0))), iron, rot=(R90, 0, 0), verts=12))
        parts.append(sphere(0.03, tuple(L + Vector((0, -0.01, 0))), sig, segs=12, rings=8))
        for k in range(3):
            a = math.pi * k / 3
            parts.append(torus(0.034, 0.004, tuple(L + Vector((0, -0.01, 0))), iron,
                               rot=(0, 0, a), verts=12, minor=3))
    # the crosshead, the sheave on top, cable into the cage
    parts.append(box((W + 0.04, 0.14, 0.1), (0, -0.1, 0.99), paint, bevel=0.015))
    for x in (-0.3, 0.0, 0.3):
        parts.append(sphere(0.01, (x, -0.172, 0.99), brass, scale=(1, 0.5, 1), segs=8, rings=4))
    parts.append(torus(0.1, 0.02, (0, -0.02, 1.02), iron, rot=(R90, 0, 0), verts=24, minor=6))
    for k in range(6):
        a = math.pi * k / 3
        parts.append(rod((0, -0.02, 1.02), (0.09 * math.cos(a), -0.02, 1.02 + 0.09 * math.sin(a)), 0.008, iron, verts=5))
    parts.append(cyl(0.02, 0.1, (0, -0.02, 1.02), brass, rot=(R90, 0, 0), verts=10))
    parts.append(cyl(0.008, 0.1, (0.1, -0.02, 0.97), iron, verts=6))
    # the cage behind: a back wall of planks lit by a lamp, side bars, a deck; the dark shaft above and below
    parts.append(box((W - 2 * T, 0.03, 0.9), (0, 0.3, 0.47), dark, bevel=0.005))
    for k in range(6):
        x = -0.36 + 0.144 * k
        parts.append(box((0.13, 0.02, 0.8), (x, 0.28, 0.46), wood, bevel=0.01))
    parts.append(box((0.5, 0.01, 0.5), (0, 0.265, 0.5), glow, bevel=0.0))
    parts.append(cyl(0.05, 0.05, (0, 0.24, 0.8), brass, r2=0.08, verts=14))
    parts.append(sphere(0.04, (0, 0.23, 0.76), glow, segs=12, rings=8))
    for s in (-1, 1):
        for y in (0.0, 0.14):
            parts.append(cyl(0.01, 0.84, (s * 0.4, y, 0.46), iron, verts=6))
        parts.append(box((0.02, 0.36, 0.02), (s * 0.4, 0.1, 0.86), iron, bevel=0.004))
    parts.append(box((W - 2 * T, 0.42, 0.04), (0, 0.08, 0.02), iron, bevel=0.01))
    for k in range(6):
        parts.append(box((0.14, 0.4, 0.008), (-0.36 + 0.144 * k, 0.08, 0.044), wood if k % 2 else paint, bevel=0.003))
    body = join(parts, "portal")
    # the scissor gate: crossing lattice bars between vertical bars, from x = -0.42 to +0.42
    GX0, GX1, GY = -0.43, 0.43, -0.19
    gp = []
    n = 8
    w = (GX1 - GX0) / n
    for k in range(n + 1):
        x = GX0 + w * k
        gp.append(box((0.018, 0.02, 0.82), (x, GY, 0.46), brass if k in (0, n) else iron, bevel=0.004))
    for k in range(n):
        x = GX0 + w * k
        for zc in (0.2, 0.46, 0.72):
            gp.append(rod((x, GY - 0.012, zc - 0.13), (x + w, GY - 0.012, zc + 0.13), 0.006, iron, verts=5))
            gp.append(rod((x, GY - 0.012, zc + 0.13), (x + w, GY - 0.012, zc - 0.13), 0.006, iron, verts=5))
    gp.append(box((0.04, 0.04, 0.12), (GX1 - 0.02, GY - 0.02, 0.46), brass, bevel=0.008))       # a handle
    door = join(gp, "door", pivot=(GX0, GY, 0.0))
    animate(door, "open", {0: {}, 3: {"loc": (0.008, 0, 0)}, 5: {"loc": (-0.006, 0, 0)}, 7: {},
                           18: {"scale": (0.1, 1, 1)}, 21: {"scale": (0.14, 1, 1)}, 24: {"scale": (0.12, 1, 1)}},
            linear=False)
    export_tree(body, "portal", [(door, body)])


# ------------------------------------------------------------------ backdrop (origin at the base centre)

def bg_timber_frame():
    """A set of mine shoring 3.0 wide, 2.8 tall: two round props with bark, a cap beam on wedges, lagging boards
    on top, iron dogs, a rope coil hanging from a peg. bg_timber, bg_timber_dark, bg_timber_end, bg_iron, bg_rope."""
    wood = mat("bg_timber", (0.46, 0.3, 0.17), 0.85)
    dark = mat("bg_timber_dark", (0.3, 0.19, 0.1), 0.9)
    end = mat("bg_timber_end", (0.72, 0.56, 0.36), 0.8)
    iron = mat("bg_iron", (0.22, 0.22, 0.24), 0.4, 0.7)
    rope = mat("bg_rope", (0.78, 0.66, 0.44), 0.9)
    parts = []
    rnd = random.Random(101)
    for s in (-1, 1):
        x = s * 1.3
        post = cyl(0.13, 2.5, (x, 0, 1.25), wood, verts=12)
        for v in post.data.vertices:
            v.co.x += 0.012 * math.sin(v.co.z * 5 + s) + rnd.uniform(-0.01, 0.01)
            v.co.y += rnd.uniform(-0.01, 0.01)
        parts.append(post)
        for k in range(6):             # bark strips
            a = rnd.uniform(-2.6, -0.5)
            z0 = rnd.uniform(0.2, 2.0)
            parts.append(box((0.05, 0.02, rnd.uniform(0.2, 0.5)), (x + 0.13 * math.cos(a), 0.13 * math.sin(a), z0), dark,
                             rot=(0, 0, a), bevel=0.006))
        parts.append(box((0.3, 0.06, 0.12), (x, -0.02, 2.46), dark, rot=(0, s * 0.12, 0), bevel=0.01))      # wedge
        parts.append(box((0.3, 0.3, 0.05), (x, 0, 0.025), dark, bevel=0.01))                               # sill
    cap = box((3.1, 0.3, 0.28), (0, 0, 2.64), wood, bevel=0.03)
    for v in cap.data.vertices:
        v.co.z += 0.02 * math.sin(v.co.x * 2.1)
    parts.append(cap)
    for s in (-1, 1):
        parts.append(box((0.03, 0.31, 0.27), (s * 1.55, 0, 2.64), end, bevel=0.008))
        parts.append(box((0.2, 0.02, 0.04), (s * 1.3, -0.16, 2.5), iron, rot=(0, s * 0.6, 0), bevel=0.005))
    for k in range(9):                # lagging boards over the cap
        x = -1.45 + 0.36 * k
        parts.append(box((0.3, 0.6, 0.05), (x + rnd.uniform(-0.03, 0.03), 0.1, 2.8 + rnd.uniform(0, 0.02)),
                         wood if k % 2 else dark, rot=(0, rnd.uniform(-0.05, 0.05), 0), bevel=0.01))
    parts.append(cyl(0.02, 0.12, (1.3, -0.17, 1.6), iron, rot=(R90, 0, 0), verts=8))
    for k in range(4):
        parts.append(torus(0.1 - 0.004 * k, 0.018, (1.3, -0.2 - 0.01 * k, 1.5), rope, rot=(R90, 0, 0.1 * k), verts=18,
                           minor=5))
    simple(parts, "bg_timber_frame")


def bg_lantern():
    """A hanging miner's lantern: origin at the hook (the top); child "lantern" (the lamp, its pivot at the hook)
    hangs 0.1 .. 0.55 below with a glass chimney round an emissive flame (bg_lantern_glow) and an animation sway
    (loop 3 s, a gentle swing of 6 degrees). Put an OmniLight3D 0.33 below the hook."""
    iron = mat("bg_lantern_iron", (0.18, 0.18, 0.2), 0.45, 0.7)
    brass = mat("bg_lantern_brass", (0.9, 0.62, 0.28), 0.3, 0.9)
    glass = mat("bg_lantern_glass", (1.0, 0.85, 0.6), 0.1, emit=0.8, alpha=0.4)
    flame = mat("bg_lantern_glow", (1.0, 0.6, 0.2), 0.4, emit=16.0)
    hook = join([torus(0.03, 0.008, (0, 0, -0.01), iron, rot=(R90, 0, 0), verts=12, minor=4),
                 box((0.12, 0.04, 0.02), (0, 0.0, 0.02), iron, bevel=0.004)], "bg_lantern")
    lp = [rod((0, 0, -0.03), (0, 0, -0.1), 0.006, iron, verts=5),
          torus(0.04, 0.007, (0, 0, -0.11), iron, rot=(R90, 0, 0), verts=12, minor=4),
          cyl(0.07, 0.06, (0, 0, -0.18), brass, r2=0.03, verts=16, bevel=0.005),
          cyl(0.06, 0.2, (0, 0, -0.32), glass, verts=16),
          cyl(0.09, 0.05, (0, 0, -0.44), brass, r2=0.075, verts=16, bevel=0.006),
          cyl(0.1, 0.02, (0, 0, -0.47), iron, verts=16)]
    for k in range(4):
        a = math.pi / 4 + k * R90
        lp.append(rod((0.065 * math.cos(a), 0.065 * math.sin(a), -0.21), (0.065 * math.cos(a), 0.065 * math.sin(a), -0.42),
                      0.006, iron, verts=5))
    f = sphere(0.025, (0, 0, -0.33), flame, scale=(1, 1, 1.9), segs=12, rings=8)
    lp.append(f)
    lp.append(cyl(0.012, 0.05, (0, 0, -0.39), brass, verts=8))
    lantern = join(lp, "lantern", pivot=(0, 0, 0))
    N = 90
    animate(lantern, "sway", keys_fn(N, lambda t: {"rot": (math.radians(2 * math.sin(2 * math.pi * t + 1)),
                                                           math.radians(6 * math.sin(2 * math.pi * t)), 0)}, 3),
            linear=False)
    export_tree(hook, "bg_lantern", [(lantern, hook)])


def bg_crystal_vein():
    """A slab of dark rock 1.6 wide, 1.2 tall, split by a vein of glowing crystals (bg_crystal_glow, recolour per
    cavern) with clusters bursting out of it; origin at the base centre."""
    rock = mat("bg_rock", (0.2, 0.165, 0.15), 0.9)
    rock2 = mat("bg_rock_light", (0.28, 0.235, 0.2), 0.85)
    glow = mat("bg_crystal_glow", (0.55, 0.4, 1.0), 0.1, emit=2.2)
    core = mat("bg_crystal", (0.4, 0.3, 0.7), 0.1, coat=1.0)
    parts = [lumpy(1.0, (0, 0, 0.6), rock, 111, 0.12, scale=(0.85, 0.35, 0.62), sub=2)]
    edit(parts[0], lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.0], context="VERTS"))
    parts.append(lumpy(0.3, (-0.55, -0.1, 0.2), rock2, 112, 0.2, scale=(1.2, 0.8, 0.8)))
    parts.append(lumpy(0.25, (0.6, -0.08, 0.3), rock2, 113, 0.2, scale=(1.0, 0.8, 1.2)))
    rnd = random.Random(114)
    pts = [(-0.8, 0.15), (-0.4, 0.45), (-0.05, 0.55), (0.3, 0.8), (0.75, 1.0)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        parts.append(rod((x0, -0.36, z0), (x1, -0.36, z1), 0.06, glow, verts=6))
    for c, n in (((-0.4, -0.38, 0.45), 6), ((0.3, -0.36, 0.8), 7), ((-0.05, -0.4, 0.55), 4), ((-0.7, -0.3, 0.22), 3)):
        for k in range(n):
            a = rnd.uniform(-1.2, 1.2)
            L = rnd.uniform(0.2, 0.42)
            d = Vector((math.sin(a), -0.6, math.cos(a))).normalized()
            base = Vector(c)
            parts.append(cyl(0.05, L * 0.8, (0, 0, L * 0.4), core if k % 2 else glow, verts=6))
            parts.append(cyl(0.05, L * 0.2, (0, 0, L * 0.9), core if k % 2 else glow, r2=0.0, verts=6))
            Mc = Matrix.Translation(base) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
            xf(parts[-2], Mc)
            xf(parts[-1], Mc)
    simple(parts, "bg_crystal_vein")


def bg_pipe():
    """A boiler-room pipe run 2.0 long (x -1..1, tile it every 2) 1.4 up, on brackets from the floor, flanged
    joints with bolts, a riser with a big red valve wheel, a pressure gauge (bg_pipe_glow, faintly lit), a steam
    leak's scorch. bg_pipe_copper, bg_pipe_iron, bg_pipe_brass, bg_pipe_valve, bg_pipe_glow."""
    copper = mat("bg_pipe_copper", (0.78, 0.42, 0.26), 0.35, 0.9)
    iron = mat("bg_pipe_iron", (0.22, 0.22, 0.24), 0.45, 0.7)
    brass = mat("bg_pipe_brass", (0.92, 0.68, 0.3), 0.3, 0.9)
    valve = mat("bg_pipe_valve", (0.75, 0.12, 0.08), 0.4, 0.3, coat=0.4)
    glow = mat("bg_pipe_glow", (1.0, 0.95, 0.8), 0.3, emit=1.5)
    Z = 1.4
    parts = [cyl(0.1, 2.0, (0, 0, Z), copper, rot=(0, R90, 0), verts=20)]
    for x in (-1.0, 0.0, 1.0):
        parts.append(cyl(0.14, 0.05, (x, 0, Z), iron, rot=(0, R90, 0), verts=20, bevel=0.01))
        for k in range(6):
            a = 2 * math.pi * k / 6
            parts.append(cyl(0.015, 0.07, (x, 0.12 * math.cos(a), Z + 0.12 * math.sin(a)), brass, rot=(0, R90, 0), verts=6))
    for x in (-0.5, 0.5):              # brackets down to the floor
        parts.append(torus(0.11, 0.015, (x, 0, Z), iron, rot=(0, R90, 0), verts=20, minor=5))
        parts.append(box((0.06, 0.06, Z - 0.1), (x, 0.05, (Z - 0.1) / 2), iron, bevel=0.01))
        parts.append(box((0.2, 0.2, 0.04), (x, 0.05, 0.02), iron, bevel=0.01))
    # a riser at x = 0.3 with the valve wheel facing the camera
    parts.append(cyl(0.07, 0.6, (0.3, -0.05, Z + 0.3), copper, verts=16))
    parts.append(cyl(0.1, 0.12, (0.3, -0.05, Z + 0.4), iron, verts=16, bevel=0.01))
    parts.append(torus(0.13, 0.018, (0.3, -0.2, Z + 0.4), valve, rot=(R90, 0, 0), verts=24, minor=6))
    for k in range(5):
        a = 2 * math.pi * k / 5
        parts.append(rod((0.3, -0.2, Z + 0.4), (0.3 + 0.13 * math.cos(a), -0.2, Z + 0.4 + 0.13 * math.sin(a)), 0.012, valve,
                         verts=5))
    parts.append(rod((0.3, -0.05, Z + 0.4), (0.3, -0.21, Z + 0.4), 0.02, brass, verts=8))
    # the gauge on a stalk at x = -0.4
    parts.append(rod((-0.4, 0, Z + 0.08), (-0.4, -0.05, Z + 0.35), 0.015, brass, verts=6))
    parts.append(cyl(0.1, 0.05, (-0.4, -0.08, Z + 0.42), brass, rot=(R90, 0, 0), verts=24, bevel=0.01))
    parts.append(cyl(0.085, 0.01, (-0.4, -0.108, Z + 0.42), glow, rot=(R90, 0, 0), verts=24))
    parts.append(box((0.012, 0.005, 0.08), (-0.4 + 0.02, -0.116, Z + 0.44), valve, rot=(0, -0.6, 0), bevel=0.0))
    simple(parts, "bg_pipe")


def bg_mushroom():
    """A clump of giant cave fungi 1.7 tall: three toadstools with glowing gills and spots (bg_mushroom_glow) on
    pale stems, small ones round the foot. bg_mushroom_cap, bg_mushroom_stem, bg_mushroom_glow."""
    cap_m = mat("bg_mushroom_cap", (0.42, 0.22, 0.5), 0.5, coat=0.4)
    stem_m = mat("bg_mushroom_stem", (0.86, 0.8, 0.7), 0.7)
    glow = mat("bg_mushroom_glow", (0.3, 1.0, 0.8), 0.3, emit=5.0)
    parts = []
    for (x, y, h, r, lean, seed) in ((0.0, 0.1, 1.5, 0.5, 0.05, 1), (-0.55, -0.05, 0.9, 0.34, -0.2, 2),
                                     (0.5, -0.1, 0.65, 0.28, 0.25, 3), (0.25, -0.3, 0.3, 0.14, 0.1, 4),
                                     (-0.3, -0.35, 0.22, 0.1, -0.2, 5), (-0.8, -0.2, 0.25, 0.12, -0.3, 6)):
        top = Vector((x + lean * h, y, h))
        parts.append(limb([(x, y, 0), (x + lean * h * 0.3, y, h * 0.45), tuple(top - Vector((0, 0, 0.05)))],
                          [r * 0.32, r * 0.22, r * 0.2], stem_m, verts=12, per=4, caps=False))
        parts.append(torus(r * 0.23, r * 0.05, tuple(top - Vector((0, 0, h * 0.3))), stem_m, verts=14, minor=5))
        cap = sphere(r, (0, 0, 0), cap_m, scale=(1, 1, 0.55), segs=24, rings=12)
        edit(cap, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.02 * r], context="VERTS"))
        xf(cap, Matrix.Translation(top) @ Matrix.Rotation(lean * 0.8, 4, "Y"))
        parts.append(cap)
        g = cyl(r * 0.95, 0.01, (0, 0, 0), glow, verts=24)
        xf(g, Matrix.Translation(top + Vector((0, 0, 0.005))) @ Matrix.Rotation(lean * 0.8, 4, "Y"))
        parts.append(g)
        rnd = random.Random(seed)
        for k in range(int(4 + r * 10)):
            a = rnd.uniform(0, 2 * math.pi)
            b = rnd.uniform(0.35, 1.3)
            p = Vector((r * math.cos(b) * math.cos(a), r * math.cos(b) * math.sin(a), r * 0.55 * math.sin(b)))
            if p.y > 0.3 * r:
                continue
            sp = sphere(r * 0.08, (0, 0, 0), glow, scale=(1, 1, 0.4), segs=8, rings=4)
            xf(sp, Matrix.Translation(top) @ Matrix.Rotation(lean * 0.8, 4, "Y") @ Matrix.Translation(p * 1.01)
               @ Vector((0, 0, 1)).rotation_difference(p.normalized()).to_matrix().to_4x4())
            parts.append(sp)
    simple(parts, "bg_mushroom")


def bg_cog():
    """A factory cog 2.0 across on an iron stand: origin at the base centre; child "cog" (its axle 1.3 up, facing
    the camera) with an animation turn (loop 6 s, one turn clockwise as seen from the camera). bg_cog_steel,
    bg_cog_brass, bg_cog_iron."""
    steel = mat("bg_cog_steel", (0.5, 0.52, 0.56), 0.35, 1.0)
    brass = mat("bg_cog_brass", (0.85, 0.62, 0.28), 0.3, 0.9)
    iron = mat("bg_cog_iron", (0.2, 0.2, 0.22), 0.45, 0.7)
    C = Vector((0, 0, 1.3))
    stand = [box((0.16, 0.2, 1.3), (0, 0.2, 0.65), iron, bevel=0.02), box((0.7, 0.4, 0.08), (0, 0.2, 0.04), iron, bevel=0.02),
             cyl(0.14, 0.24, (0, 0.2, 1.3), iron, rot=(R90, 0, 0), verts=18, bevel=0.02)]
    for s in (-1, 1):
        stand.append(rod((0.3 * s, 0.2, 0.08), (0.05 * s, 0.2, 0.9), 0.04, iron, verts=8))
    body = join(stand, "bg_cog")
    cp = [gear(0.86, 0.12, (0, 0, 0), steel, teeth=22, rot=(R90, 0, 0), tooth=0.16)]
    cp.append(torus(0.62, 0.05, (0, -0.07, 0), brass, rot=(R90, 0, 0), verts=40, minor=8))
    cp.append(torus(0.2, 0.05, (0, -0.07, 0), brass, rot=(R90, 0, 0), verts=24, minor=8))
    for k in range(6):
        a = 2 * math.pi * k / 6
        cp.append(box((0.1, 0.06, 0.44), (0.4 * math.cos(a), -0.07, 0.4 * math.sin(a)), steel, rot=(0, R90 - a, 0),
                      bevel=0.02))
        cp.append(sphere(0.03, (0.62 * math.cos(a + 0.5), -0.12, 0.62 * math.sin(a + 0.5)), brass, scale=(1, 0.5, 1),
                         segs=8, rings=5))
    cp.append(cyl(0.08, 0.1, (0, -0.1, 0), brass, rot=(R90, 0, 0), verts=14))
    for o in cp:
        xf(o, Matrix.Translation(C))
    cog = join(cp, "cog", pivot=tuple(C))
    N = 180
    animate(cog, "turn", {f: {"rot": (0, 2 * math.pi * f / N, 0)} for f in range(0, N + 1, 10)}, linear=True)
    export_tree(body, "bg_cog", [(cog, body)])


def bg_icicles():
    """A frozen ledge 2.0 wide (x -1..1) with a snowy lip and a fringe of icicles up to 0.9 long; origin at the TOP
    centre (hang it under a ceiling). bg_ice, bg_ice_deep, bg_snow."""
    ice = mat("bg_ice", (0.7, 0.88, 1.0), 0.05, coat=1.0)
    deep = mat("bg_ice_deep", (0.36, 0.6, 0.9), 0.1, coat=1.0)
    snow = mat("bg_snow", (0.94, 0.97, 1.0), 0.6)
    parts = [box((2.0, 0.4, 0.14), (0, 0.05, -0.07), deep, bevel=0.03)]
    rnd = random.Random(131)
    for k in range(14):
        x = -0.95 + 1.9 * k / 13
        parts.append(sphere(0.1, (x, -0.13, -0.02), snow, scale=(1.1, 0.8, 0.6), segs=12, rings=6))
    for k in range(22):
        x = -0.95 + 1.9 * k / 21 + rnd.uniform(-0.03, 0.03)
        L = rnd.uniform(0.15, 0.9) * (1 - 0.5 * abs(x))
        r = 0.02 + L * 0.05
        y = rnd.uniform(-0.12, 0.05)
        o = cyl(r, L, (x, y, -0.12 - L / 2), ice if k % 3 else deep, r2=0.0, verts=7)
        for v in o.data.vertices:
            v.co.x += 0.01 * math.sin(v.co.z * 30 + k)
        parts.append(o)
        parts.append(sphere(r * 1.3, (x, y, -0.12), ice, segs=8, rings=5))
    simple(parts, "bg_icicles")


def bg_rockwall():
    """A back-wall panel of cave rock 4.0 wide, 4.0 tall (x -2..2, z 0..4), its face at y 0 with lumps up to 0.3
    towards the camera: bg_rock, bg_rock_light, bg_rock_dark (recolour per cavern). Tile it every 4 behind the
    play field."""
    rock = mat("bg_rock", (0.2, 0.165, 0.15), 0.9)
    light = mat("bg_rock_light", (0.28, 0.235, 0.2), 0.85)
    dark = mat("bg_rock_dark", (0.07, 0.06, 0.055), 0.95)
    parts = [box((4.0, 0.2, 4.0), (0, 0.1, 2.0), dark, bevel=0.0)]
    rnd = random.Random(141)
    for k in range(70):
        x, z = rnd.uniform(-1.9, 1.9), rnd.uniform(0.1, 3.9)
        r = rnd.uniform(0.18, 0.38)
        o = lumpy(1.0, (0, 0, 0), rock if k % 3 else light, 500 + k, 0.22, sub=2, smooth=32)
        xf(o, Matrix.Translation((x, 0.05, z)) @ Matrix.Diagonal(Vector((r, r * 0.45, r * 0.8))).to_4x4())
        for v in o.data.vertices:
            v.co.x = max(-2.0, min(2.0, v.co.x))
            v.co.z = max(0.0, min(4.0, v.co.z))
            v.co.y = max(-0.3, v.co.y)
        parts.append(o)
    simple(parts, "bg_rockwall")


JOBS = {"miner": miner, "guardian_minecart": guardian_minecart, "guardian_drill": guardian_drill,
        "guardian_bat": guardian_bat, "guardian_crab": guardian_crab, "guardian_gear": guardian_gear,
        "guardian_snowball": guardian_snowball,
        "tile_rock_a": lambda: tile_rock("a"), "tile_rock_b": lambda: tile_rock("b"), "tile_rock_c": lambda: tile_rock("c"),
        "tile_floor": tile_floor, "tile_crumble": tile_crumble, "tile_conveyor": tile_conveyor,
        "tile_wall_brick": tile_wall_brick, "tile_ice": tile_ice, "hazard_spikes": hazard_spikes,
        "hazard_plant": hazard_plant, "hazard_steam": hazard_steam, "key": key, "portal": portal,
        "bg_timber_frame": bg_timber_frame, "bg_lantern": bg_lantern, "bg_crystal_vein": bg_crystal_vein,
        "bg_pipe": bg_pipe, "bg_mushroom": bg_mushroom, "bg_cog": bg_cog, "bg_icicles": bg_icicles,
        "bg_rockwall": bg_rockwall}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            clear_all()
            fn()
