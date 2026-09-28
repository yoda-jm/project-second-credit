"""Pop Voyage (game 23) models: the traveller (on the shared humanoid rig) with her harpoon launcher, the four balloons
and a rubber shard, the harpoon tip, the carved blocks (whole and cracked) and the five items.
Original designs (the traveller is our own globe-trotter: a young woman in a pinned-up bush hat, a teal safari shirt,
khaki shorts, striped socks and a big orange backpack with a bedroll and a pennant). Deterministic; output
CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/popvoyage_models.py -- godot/games/popvoyage/art/models [name ...]
Helpers come from humanoid.py (the 26-bone rig, smooth skin, IK poses, gait), relic_models.py (P, cycle, slim,
clear_all), deepbreath_models.py (export_rig, xf), blastyard_models.py (mat, box, cyl, ...), prism_models.py (edit)
and mossfolk_models.py (lumpy, solid). 30 fps.

Axes: Blender Z up, the camera side is -Y; in Godot +X stays +X, Blender +Z is +Y (up), Blender -Y is +Z (towards
the camera). Game size (node scale 1): the arena is 16 x 10 units, the floor at y = 0, the play plane at z = 0.
Animations marked * are seamless loops: set their loop mode in the game. Emissive materials have "glow" in their names.

traveller.glb  armature "traveller_rig" (26 bones: root, hips, spine, chest, neck, head, clavicle/arm/forearm/hand.L/R,
               thigh/shin/foot/toe.L/R), the skinned mesh "traveller", and on the bone hand.R the node "launcher" (the
               harpoon launcher, a mesh) and the empty "muzzle" (at the launcher's mouth; its local +Y runs out of the
               barrel). 1.30 tall (to the pinned-up hat brim) at node scale 1, feet at the origin, FACING GODOT +Z
               (the camera), left-right symmetric except the launcher in her right hand (at Godot -X). For facing,
               turn the node about Y (e.g. +-70 degrees while running, to keep the face readable) or mirror it with
               scale.x = -1.
               Materials: traveller_skin, _cheek, _freckle, _lips, _eye_white, _iris, _pupil, traveller_eye_glow (the
               catch lights), _hair, _hair_tie, _hat, _hat_band, _feather, _shirt, _shirt_dark, _button, _scarf,
               _shorts, _socks, _sock_stripe, _boots, _sole, _leather, _brass, _pack, _pack_dark, _bedroll, _mug,
               _pennant, and on the launcher launcher_body, launcher_brass, launcher_wood, launcher_steel,
               launcher_wire.
               Animations (loops marked *):
                 idle*   3.2 s, breathing, the launcher held upright at her right hip, a glance up and to each side
                 run*    0.4 s (12 frames), one stride (two steps) in place, running towards her facing: 2.2 units per
                         cycle = 5.5 units/s at speed_scale 1 (the engine's WALK); the launcher rides at the hip
                 shoot   0.3 s, both hands swing the launcher up to vertical in front of her chest, it fires at frame 3
                         (0.067 s) and kicks down, then lowers halfway; at the shot the muzzle is at about
                         (-0.08, 0.99, 0.15) from the origin, pointing straight up (at rest in idle it sits at
                         (-0.19, 1.08, 0.24), tilted forward)
                 die     1.5 s, a jolt (hat and arms up), flung up and sideways, lands on her back and bounces, flops
                         with the limbs spread (holds); she ends lying along X, head towards Godot +X (mirror with
                         scale.x = -1 for the other way), from about x = -0.4 to +1.1 (the launcher arm raised)
                 cheer*  1 s, two hops, the launcher raised high in the right hand, the left fist pumping
balloon_0..3.glb  one mesh each (balloon_0 .. balloon_3), radius 0.24 / 0.44 / 0.72 / 1.05 (the engine's RADIUS), origin
               at the centre of that circle; a slightly egg-shaped body (the bottom reaches 1.06 r) with a tied knot
               below it (to about -1.2 r). Materials "balloon" (glossy white rubber, including the knot: override or
               tint it per balloon) and "balloon_sheen" (a soft white window highlight on the camera side, upper left;
               leave it white). No animation (squash them in the view).
balloon_shard.glb  one mesh "balloon_shard": a torn rubber scrap about 0.16 across, origin at its centre, material
               "balloon" (tint it like the balloon it came from); spin and fling copies for a pop.
wire.glb       one mesh "wire": the harpoon tip pointing up (Godot +Y), 0.30 long, origin at its base (put it on the
               wire's top); a brass collar, a barbed steel arrowhead with a glowing edge. wire_steel, wire_brass,
               wire_glow.
block.glb      one mesh "block", 1 x 1 x 1, origin at the centre (scale it to the block's rect): dressed stone with a
               gilded frame round the front face and along the top edges, gold corner studs and a recessed panel
               with a small carved sun. block_stone, block_stone_dark, block_gold, block_carve.
block_cracked.glb  the same block, visibly cracked: a zigzag crack across the front and over the top, a chipped
               corner, a split gold frame, faint warm light in the deepest cracks. block_stone, block_stone_dark,
               block_gold, block_carve, block_crack, block_crack_glow.
Items (about 0.5 across and 0.5 tall, origin at the bottom centre, facing the camera; each stands in a halo ring in
its own colour, material item_<kind>_glow; one mesh named like the file):
  item_double    two harpoon arrows side by side, tied with a red ribbon (cyan halo)
  item_sticky    a steel hook dripping green goo (item_sticky_goo, slightly emissive), lime halo
  item_shield    a heater shield (blue enamel, gold rim and star) inside a clear bubble (item_shield_bubble, alpha),
                 sky-blue halo
  item_clock     a gold pocket watch with a glowing dial (item_clock_face_glow), hands at ten to two, the bow and
                 crown on top, amber halo
  item_charge    a firework rocket (red and gold stripes, fins) with a lit fuse (item_charge_spark_glow), orange halo
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, join, export, reset, R90
from prism_models import edit, empty
from mossfolk_models import lumpy, solid
from relic_models import P, cycle, slim, clear_all
from deepbreath_models import export_rig, xf
import humanoid as HU

FPS = 30
TALL = 1.3                       # the traveller's height in game units (the engine's TALL)
WALK = 5.5                       # the engine's walking speed, units/s


# ------------------------------------------------------------------ the traveller

TSK = HU.Skeleton(HU.proportions(sh_w=0.175, hip_w=0.098))
TSHAPE = {"chest": 1.02, "waist": 0.96, "hips": 1.08, "arms": 1.1, "legs": 1.12, "neck": 1.25, "hand": 1.3}
THEAD = 1.75
TH = (0, -0.02, 1.725)           # head centre
T_SCALE = 1.0                    # set from the built figure's height (TALL / height) before the actions are made
RUN_FRAMES = 12
LS = 1.2                         # the launcher's scale (it is built at the rig's size)


def t_stand(w=0.12):
    return {"ik_foot.L": (w, 0.02, 0.09, 0, 10), "ik_foot.R": (-w, -0.02, 0.09, 0, 12), "ikw.L": 1.0, "ikw.R": 1.0}


def hold_r(br=0.0, up=0.0):
    """The launcher held upright at the right hip (FK arm, the hand aimed)."""
    return {"clavicle.R": (2, 0, 2 + 1.5 * br), "arm.R": (8 + 2 * br, 0, 14), "forearm.R": (78 + up, 0, 0),
            "hand_dir.R": (-12, 72, 0), "hdw.R": 1.0}


def left_rest(br=0.0):
    return {"clavicle.L": (2, 0, 2 + 1.5 * br), "arm.L": (4, 0, 12), "forearm.L": (24 + 2 * br, 0, 0),
            "hand.L": (0, 0, -4)}


T_STAND = P(t_stand(), **{"root": (0, 0, -0.02), "spine": (1, 0, 0), "chest": (-1, 0, 0), "head": (-2, 0, 0)},
            **left_rest(), **hold_r())


def t_idle():
    """3.2 s: breathing, a weight shift, a glance up at the sky, then to each side."""
    def f(t):
        a = 2 * math.pi * t
        br = math.sin(a * 3)
        sway = math.sin(a)
        up = HU.smoothstep(0.08, 0.18, t) * (1 - HU.smoothstep(0.3, 0.4, t))
        look = HU.smoothstep(0.45, 0.55, t) * (1 - HU.smoothstep(0.62, 0.7, t)) \
            - HU.smoothstep(0.72, 0.8, t) * (1 - HU.smoothstep(0.88, 0.96, t))
        p = P(T_STAND, **{"root": (0.012 * sway, 0, -0.02 - 0.006 * br), "hips": (0, 3 * sway, -3 * sway),
                          "spine": (1, -1.5 * sway, 1.5 * sway), "chest": (-1 + 1.5 * br, -3 * sway + 6 * look, 0),
                          "neck": (-8 * up, 12 * look, 0), "head": (-2 - 2 * br - 16 * up, 22 * look, 4 * look)})
        p.update(left_rest(br))
        p.update(hold_r(br, 4 * br))
        return p
    return cycle(96, f, 3)


def t_run():
    """A quick, light run: the stride is set so 12 frames cover 2.2 game units (5.5 units/s)."""
    stride = WALK * RUN_FRAMES / FPS / T_SCALE

    def extra(ph, pose):
        b = math.sin(4 * math.pi * ph)
        return {"clavicle.R": (4, 0, 4), "arm.R": (14 + 4 * b, 0, 16), "forearm.R": (82 + 6 * b, 0, 0),
                "hand_dir.R": (-8, 62, 0), "hdw.R": 1.0}
    return HU.gait(TSK, RUN_FRAMES, stride, 0.36, lift=0.3, lift_at=0.45, strike=8, push=42, bob=-0.035,
                   drop=-0.07, lean=11, width=0.1, arm_swing=48, arm_out=12, elbow=74, elbow_swing=20,
                   pelvis_yaw=10, pelvis_roll=4, shoulder_yaw=10, reach=0.46, sway=0.012, step=1,
                   base={"head": (-7, 0, 0), "spine": (4, 0, 0)}, extra=extra)


FORE = None                      # the fore-grip in rest space (character space), set when the launcher is built


def aim(kick=0.0, lower=0.0):
    """Both hands hold the launcher upright in front of the chest; kick pushes it down, lower brings it down."""
    fx, ff, fu = FORE
    return P(T_STAND, **{"ik_hand.R": (-0.13, 0.3 - 0.05 * lower, 1.06 - 0.06 * kick - 0.2 * lower), "ikh.R": 1.0,
                         "hand_dir.R": (0, 86 - 30 * lower, 0), "hdw.R": 1.0,
                         "ik_hand.L": (fx + 0.035, ff + 0.03, fu - 0.02), "ikh.L": 1.0,
                         "hand_dir.L": (-10, 30, 90), "hdw.L": 0.6,
                         "clavicle.R": (8, 0, 6 + 4 * kick), "clavicle.L": (10, 0, 4),
                         "spine": (-2 + 3 * kick, 0, 0), "chest": (-4 + 2 * kick, 0, 0), "neck": (-6, 0, 0),
                         "head": (-14 + 4 * kick, 0, 0), "root": (0, 0, -0.04 - 0.035 * kick),
                         "ik_foot.L": (0.13, 0.04, 0.09, 0, 12), "ik_foot.R": (-0.13, -0.06, 0.09, 0, 14)})


def t_shoot():
    """0.3 s: swing up to vertical, fire at frame 3, kick, settle, lower halfway."""
    return HU.Anim({1: T_STAND, 3: aim(), 4: aim(1.0), 6: aim(0.3), 8: aim(0.0, 0.15), 10: aim(0.0, 0.45)},
                   hand_on={"L": "hand.R"}, arm_pole={"L": (0.9, 0.6, -0.6), "R": (0.9, 0.5, -0.6)})


def t_die():
    """1.5 s: a jolt, flung up and sideways (towards her left, Godot +X), lands on her back, bounces, flops (holds)."""
    jolt = P(T_STAND, **{"root": (0, 0.02, 0.1), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (8, 0, 10), "shin.L": (14, 0, 0),
                         "thigh.R": (-4, 0, 10), "shin.R": (16, 0, 0), "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0),
                         "spine": (-10, 0, 0), "chest": (-10, 0, 0), "head": (-22, 0, 0), "hdw.R": 0.0,
                         "arm.L": (160, 0, 44), "forearm.L": (10, 0, 0), "arm.R": (150, 0, 44), "forearm.R": (20, 0, 0),
                         "hand.L": (0, 0, 30), "hand.R": (0, 0, 30)})
    fly = P(jolt, **{"turn": (-30, -40, -40), "root": (0.05, 0.0, 0.3), "thigh.L": (40, 0, 30), "shin.L": (60, 0, 0),
                     "thigh.R": (20, 0, 24), "shin.R": (40, 0, 0), "arm.L": (120, 0, 80), "arm.R": (130, 0, 70),
                     "head": (-10, 0, 0), "spine": (-6, 0, 0)})
    lie = {"ikw.L": 0.0, "ikw.R": 0.0, "hdw.R": 0.0, "turn": (-90, -90, 0), "root": (0.0, 0.0, 0.14),
           "hips": (0, 0, 0), "spine": (-2, 0, 0), "chest": (-2, 0, 0), "neck": (4, 0, 0), "head": (6, -30, 0),
           "arm.L": (30, 0, 75), "forearm.L": (40, 0, 0), "arm.R": (40, 0, 70), "forearm.R": (30, 0, 0),
           "thigh.L": (24, 0, 16), "shin.L": (40, 0, 0), "thigh.R": (10, 0, 18), "shin.R": (14, 0, 0),
           "foot.L": (-30, 0, 0), "foot.R": (-35, 0, 0)}
    land = P(lie, **{"root": (-0.4, 0.0, 0.2), "thigh.L": (70, 0, 12), "shin.L": (30, 0, 0), "thigh.R": (60, 0, 14),
                     "shin.R": (24, 0, 0), "arm.L": (100, 0, 60), "arm.R": (110, 0, 56), "head": (-6, 0, 0)})
    bounce = P(lie, **{"turn": (-80, -90, 0), "root": (-0.34, 0.0, 0.3), "thigh.L": (80, 0, 14), "shin.L": (40, 0, 0),
                       "thigh.R": (70, 0, 16), "shin.R": (36, 0, 0), "head": (-12, 0, 0), "arm.L": (70, 0, 90),
                       "arm.R": (80, 0, 84)})
    rest = P(lie, **{"root": (-0.3, 0.0, 0.14)})
    return HU.Anim({1: T_STAND, 4: jolt, 10: fly, 17: land, 21: bounce, 26: P(rest, **{"head": (0, -10, 0)}),
                    32: P(rest, **{"thigh.L": (34, 0, 16), "arm.L": (36, 0, 80)}), 38: rest, 46: rest})


def t_cheer():
    """1 s loop: two hops, the launcher raised high in the right hand, the left fist pumping."""
    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a * 2)) ** 1.5
        pump = math.sin(a)
        p = P(t_stand(0.13), **{
            "root": (0, 0, -0.05 + 0.1 * hop - 0.05 * max(0.0, -math.sin(a * 2))),
            "spine": (-4, 5 * pump, 0), "chest": (-6, 6 * pump, 0), "neck": (-6, 0, 0), "head": (-16, -8 * pump, 0),
            "clavicle.L": (0, 0, 16 + 10 * max(0, pump)), "clavicle.R": (0, 0, 20),
            "arm.L": (120 + 40 * max(0, pump), 0, 34), "forearm.L": (30 + 60 * max(0, -pump), 0, 0),
            "arm.R": (165, 0, 24), "forearm.R": (12, 0, 0), "hand_dir.R": (-20, 80, 0), "hdw.R": 1.0,
            "hand.L": (0, 0, 10)})
        for X in "LR":
            v = p["ik_foot." + X]
            p["ik_foot." + X] = (v[0], v[1], v[2] + 0.09 * hop, -10 * hop, v[4])
        return p
    return cycle(30, f, 1)


def traveller_actions():
    return {"idle": t_idle(), "run": t_run(), "shoot": t_shoot(), "die": t_die(), "cheer": t_cheer()}


def traveller_head(k, skin, cheek, white, iris, pupil, shine, lips, hair, freckle):
    cx, cy, cz = TH

    def Q(x, y, z):
        return (cx + x * k, cy + y * k, cz + z * k)
    HU.sphere(0.1 * k, Q(0, 0.006, 0.004), "head", skin, (0.9, 1.0, 1.04), 32, 18)            # cranium
    HU.sphere(0.074 * k, Q(0, -0.016, -0.046), "head", skin, (0.94, 0.95, 0.84), 24, 14)      # jaw, cheeks
    HU.sphere(0.02 * k, Q(0, -0.058, -0.088), "head", skin, (1.4, 0.8, 0.7), 14, 8)           # chin
    HU.sphere(0.011 * k, Q(0, -0.1, -0.018), "head", skin, (1.1, 0.9, 0.85), 14, 10)          # button nose
    for s in (-1, 1):
        HU.sphere(0.022 * k, Q(0.088 * s, 0.01, -0.01), "head", skin, (0.45, 0.85, 1.3), 14, 10)   # ears
        # big, friendly eyes: white, iris, pupil, a catch light
        HU.sphere(0.022 * k, Q(0.037 * s, -0.075, 0.006), "head", white, (0.95, 0.55, 1.18), 18, 12)
        HU.sphere(0.0155 * k, Q(0.035 * s, -0.086, 0.002), "head", iris, (1.0, 0.45, 1.12), 16, 10)
        HU.sphere(0.0085 * k, Q(0.035 * s, -0.093, 0.002), "head", pupil, (1.0, 0.4, 1.1), 12, 8)
        HU.sphere(0.0045 * k, Q(0.035 * s + 0.006 * k / k, -0.0985, 0.012), "head", shine, (1, 0.5, 1), 8, 6)
        # an upper lash line, flicked out at the corner
        lash = [Q(0.037 * s + 0.021 * math.cos(u) * s, -0.086 + 0.012 * (1 - math.sin(u)), 0.006 + 0.026 * math.sin(u) * 0.9)
                for u in (math.radians(d) for d in (170, 140, 110, 80, 50, 20, 0))]
        lash = [(x, y, z, 0.0032 * k) for x, y, z in lash]
        lash.append((cx + (0.037 * s + 0.028 * s) * k, cy - 0.074 * k, cz + 0.014 * k, 0.002 * k))
        HU.tube(lash, "head", pupil, 6, 0.004)
        # brows: soft arcs, a little raised (curious)
        HU.tube([Q(0.018 * s, -0.093, 0.04) + (0.0045 * k,), Q(0.036 * s, -0.093, 0.048) + (0.005 * k,),
                 Q(0.055 * s, -0.083, 0.044) + (0.004 * k,)], "head", hair, 8, 0.005)
        HU.sphere(0.019 * k, Q(0.056 * s, -0.064, -0.03), "head", cheek, (1.0, 0.45, 0.72), 12, 8)   # blush
        for dx, dz in ((0.028, -0.018), (0.042, -0.024), (0.034, -0.03), (0.05, -0.016)):       # freckles
            HU.sphere(0.0032 * k, Q(dx * s, -0.094 + 0.03 * (dx - 0.028), dz), "head", freckle, (1, 0.5, 1), 6, 4)
    # a wide smile, the corners turned up, a hint of the lower lip
    sm = []
    for i in range(9):
        u = -1 + 2 * i / 8
        x = 0.026 * u
        z = -0.05 + 0.011 * u * u
        y = -0.016 - 0.0703 * math.sqrt(max(0.0, 1 - (x / 0.0695) ** 2 - ((z + 0.03) / 0.062) ** 2 * 0.3)) - 0.001
        sm.append(Q(x, y, z) + (0.0042 * k,))
    HU.tube(sm, "head", lips, 8, 0.004)
    HU.sphere(0.01 * k, Q(0, -0.085, -0.06), "head", lips, (1.6, 0.4, 0.5), 10, 6)


def brim_point(a, ring, k, hz, cx, cy):
    """A point of the hat's brim: ring 0 at the crown, 1 at the edge; her left side (+X) is pinned up."""
    rx = (0.113 + 0.085 * ring) * k
    ry = (0.118 + 0.087 * ring) * k
    x, y = rx * math.cos(a), ry * math.sin(a)
    z = hz + 0.002 - 0.02 * k * ring * (0.5 + 0.5 * abs(math.sin(a)))     # a soft droop front and back
    pin = HU.smoothstep(0.45, 0.95, math.cos(a)) * ring
    z += pin * 0.085 * k
    x -= pin * 0.045 * k
    return (cx + x, cy + 0.01 * k + y, z)


def traveller_hair_and_hat(k, hair, tie, hat, band, feather_m):
    cx, cy, cz = TH

    def Q(x, y, z):
        return (cx + x * k, cy + y * k, cz + z * k)
    # a rounded auburn bob: a shell over the cranium with the face cut out under a side-swept fringe, down to the
    # jaw at the sides and the nape at the back
    hc = Vector(Q(0, 0.01, 0.012))
    R = Vector((0.104 * k, 0.114 * k, 0.114 * k))
    shell = HU.sphere(1.0, tuple(hc), "head", hair, tuple(R), 72, 40)

    def cut(bm):
        kill = []
        for v in bm.verts:
            d = v.co - hc
            d = Vector((d.x / R.x, d.y / R.y, d.z / R.z))
            fringe = 0.36 + 0.12 * d.x + 0.05 * math.sin(d.x * 16)     # swept up to her left, a little wavy
            if d.y < -0.18 and d.z < fringe:
                kill.append(v)
            elif d.z < -0.62 + 0.25 * max(0.0, -d.y):                  # the bob's hem, higher towards the face
                kill.append(v)
            elif d.z > 0.72:                                            # under the hat's crown
                kill.append(v)
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    edit(shell, cut)
    solid(shell, 0.012 * k)
    HU.tag(shell, "head", hair)
    # the hem curls in a little at the jaw: a soft roll along the bottom edge at each side
    for s in (-1, 1):
        HU.tube([Q(0.08 * s, -0.035, -0.05) + (0.009 * k,), Q(0.09 * s, 0.0, -0.062) + (0.012 * k,),
                 Q(0.082 * s, 0.05, -0.066) + (0.012 * k,), Q(0.05 * s, 0.088, -0.064) + (0.011 * k,)],
                "head", hair, 12, 0.008)
    # the ponytail: out from under the hat at the back, a coral tie, a bouncy curl down
    HU.tube([Q(0, 0.1, 0.02) + (0.03 * k,), Q(0, 0.13, 0.0) + (0.034 * k,), Q(0.0, 0.15, -0.05) + (0.032 * k,),
             Q(0.01, 0.152, -0.11) + (0.024 * k,), Q(0.03, 0.135, -0.155) + (0.014 * k,),
             Q(0.05, 0.11, -0.165) + (0.004 * k,)], "head", hair, 14, 0.008)
    HU.tube([Q(0, 0.104, 0.018) + (0.022 * k,), Q(0, 0.12, 0.01) + (0.022 * k,)], "head", tie, 12, 0.006)
    # the bush hat: a soft crown with a dent, a coral band, a brim pinned up on her left side, a feather
    n_before = set(bpy.context.scene.objects)
    hz = cz + 0.07 * k
    crown = HU.sphere(0.116 * k, (cx, cy + 0.01 * k, hz), "head", hat, (0.97, 1.02, 0.84), 28, 16)
    edit(crown, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < hz - 0.004], context="VERTS"))
    for v in crown.data.vertices:          # a lengthwise dent in the top of the crown
        d = abs(v.co.x - cx) / (0.05 * k)
        if v.co.z > hz + 0.06 * k and d < 1:
            v.co.z -= 0.01 * k * (1 - d * d) * HU.smoothstep(hz + 0.06 * k, hz + 0.095 * k, v.co.z)
    crown.data.update()
    HU.body_loft([(hz - 0.002, 0.116 * k, 0.121 * k, cy + 0.01 * k), (hz + 0.03 * k, 0.112 * k, 0.117 * k, cy + 0.01 * k)],
                 "head", band, 28, 0)
    bm = bmesh.new()
    n = 40
    rows = [[bm.verts.new(brim_point(2 * math.pi * i / n, ring, k, hz, cx, cy)) for i in range(n)]
            for ring in (0.0, 0.5, 1.0)]
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    brim = HU._mesh_object(bm, "brim")
    solid(brim, 0.011)
    sub = brim.modifiers.new("s", "SUBSURF")
    sub.levels = 1
    HU._select_only(brim)
    bpy.ops.object.modifier_apply(modifier=sub.name)
    HU.tag(brim, "head", hat)
    # a stitched binding round the brim's edge (the band colour)
    edge = [brim_point(2 * math.pi * i / n, 0.985, k, hz, cx, cy) + (0.005 * k,) for i in range(n + 1)]
    HU.tube(edge, "head", band, 6, 0.012, caps=(False, False))
    # a brass pin holding the brim up, and a small feather tucked in the band behind it
    px = brim_point(0.0, 0.62, k, hz, cx, cy)
    HU.sphere(0.012 * k, (px[0] - 0.004 * k, px[1] - 0.012 * k, px[2]), "head",
              mat("traveller_brass", (0.95, 0.72, 0.3), 0.3, 0.9), (0.6, 1, 1), 12, 8)
    fp = [(cx + 0.1 * k, cy + 0.05 * k, hz + 0.02 * k), (cx + 0.108 * k, cy + 0.07 * k, hz + 0.07 * k),
          (cx + 0.098 * k, cy + 0.095 * k, hz + 0.125 * k), (cx + 0.078 * k, cy + 0.115 * k, hz + 0.16 * k)]
    wid = [0.003, 0.013, 0.015, 0.004]
    HU.tube([p + (w * k,) for p, w in zip(fp, wid)], "head", feather_m, 10, 0.01, ell=(0.35, 1.0))
    HU.tube([p + (0.0025 * k,) for p in fp], "head", band, 6, 0.01)
    tilt = Matrix.Translation(Vector(TH)) @ Matrix.Rotation(math.radians(-10), 4, "X") \
        @ Matrix.Rotation(math.radians(-5), 4, "Y") @ Matrix.Translation(-Vector(TH))
    for o in set(bpy.context.scene.objects) - n_before:
        o.data.transform(tilt)


def launcher_parts(sk):
    """The harpoon launcher in the right hand's rest frame: the barrel along the hand (+Y), above the fist (+Z); a
    pistol grip through the fist, a fore-grip for the left hand, a wire reel on the side, the harpoon in the mouth."""
    body = mat("launcher_body", (0.1, 0.42, 0.36), 0.3, 0.2, coat=0.7)
    brass = mat("launcher_brass", (0.95, 0.7, 0.28), 0.28, 0.95)
    wood = mat("launcher_wood", (0.5, 0.26, 0.1), 0.45, coat=0.4)
    steel = mat("launcher_steel", (0.75, 0.78, 0.82), 0.22, 1.0)
    wire = mat("launcher_wire", (0.85, 0.42, 0.2), 0.35, 0.9)
    m = -1
    Z = 0.078                     # the barrel's axis above the fist
    parts = []

    def along(y0, y1, r, material, r2=None, verts=20):
        return rod((0, y0, Z), (0, y1, Z), r, material, r2=r2, verts=verts)
    parts.append(along(-0.17, 0.3, 0.05, body, verts=24))
    parts.append(sphere(0.05, (0, -0.17, Z), body, scale=(1, 0.6, 1), segs=20, rings=10))
    for y in (-0.12, 0.04, 0.26):
        parts.append(rod((0, y - 0.012, Z), (0, y + 0.012, Z), 0.056, brass, verts=24))
    parts.append(along(0.29, 0.35, 0.052, brass, r2=0.064, verts=24))              # the flared mouth
    parts.append(torus(0.062, 0.008, (0, 0.35, Z), brass, rot=(R90, 0, 0), verts=24, minor=6))
    parts.append(along(0.345, 0.352, 0.056, mat("launcher_dark", (0.05, 0.05, 0.06), 0.6), verts=24))
    # the harpoon's tip waiting in the mouth
    parts.append(along(0.3, 0.4, 0.014, steel, verts=10))
    ah = [(0, 0.39), (0.03, 0.4), (0.0, 0.47), (-0.03, 0.4)]
    parts.append(K.prism([(x, y) for x, y in ah], 0.012, (0, 0, 0), steel, rot=(0, 0, 0), bevel=0.003))
    last = parts[-1]
    last.data.transform(Matrix.Translation((0, 0, Z)) @ Matrix.Rotation(-R90, 4, "X"))
    # prism builds in x/z and extrudes along y: rotate its outline into x/y (the barrel's direction)
    # the pistol grip through the fist (along the hand's local Z), a trigger and its guard
    parts.append(box((0.03, 0.045, 0.13), (m * 0.004, 0.09, 0.0), wood, rot=(0.12, 0, 0), bevel=0.012))
    parts.append(torus(0.024, 0.005, (0, 0.14, 0.026), brass, rot=(0, R90, 0), verts=14, minor=4))
    parts.append(box((0.008, 0.012, 0.022), (0, 0.135, 0.03), steel, bevel=0.002))
    # the fore-grip under the front of the barrel
    parts.append(rod((0, 0.2, Z), (0, 0.2, Z - 0.1), 0.02, wood, verts=12))
    parts.append(sphere(0.022, (0, 0.2, Z - 0.1), wood, segs=12, rings=8))
    # the wire reel on the outer side: a brass drum wound with copper wire, a little crank
    rx = -m * 0.062
    parts.append(cyl(0.045, 0.04, (rx, 0.03, Z), brass, rot=(0, R90, 0), verts=22, bevel=0.004))
    parts.append(cyl(0.036, 0.046, (rx, 0.03, Z), wire, rot=(0, R90, 0), verts=22))
    parts.append(cyl(0.012, 0.06, (rx, 0.03, Z), steel, rot=(0, R90, 0), verts=10))
    parts.append(rod((rx - m * 0.03, 0.03, Z), (rx - m * 0.03, 0.03 + 0.04, Z - 0.02), 0.007, steel, verts=6))
    parts.append(sphere(0.012, (rx - m * 0.03, 0.07, Z - 0.02), wood, segs=8, rings=6))
    # a brass sight on top and a pressure gauge
    parts.append(box((0.012, 0.05, 0.03), (0, 0.22, Z + 0.058), brass, bevel=0.004))
    parts.append(cyl(0.022, 0.014, (0, -0.06, Z + 0.058), brass, verts=16, bevel=0.003))
    parts.append(cyl(0.017, 0.016, (0, -0.06, Z + 0.06), mat("launcher_dial", (0.95, 0.93, 0.85), 0.4), verts=16))
    M = HU.bone_frame(sk, "hand.R") @ Matrix.Scale(LS, 4)
    for o in parts:
        xf(o, M)
    muzzle = M @ Vector((0, 0.35, Z))
    fore = M @ Vector((0, 0.2, Z - 0.06))
    M = HU.bone_frame(sk, "hand.R")
    return parts, M, muzzle, fore


def traveller():
    global T_SCALE, FORE
    sk = TSK
    sh = TSHAPE
    skin = HU.mat("traveller_skin", (0.9, 0.55, 0.39), 0.5)
    cheek = HU.mat("traveller_cheek", (0.98, 0.5, 0.45), 0.55)
    freckle = HU.mat("traveller_freckle", (0.72, 0.4, 0.26), 0.6)
    lips = HU.mat("traveller_lips", (0.62, 0.16, 0.16), 0.45)
    white = HU.mat("traveller_eye_white", (0.98, 0.97, 0.95), 0.25, coat=0.6)
    iris = HU.mat("traveller_iris", (0.22, 0.52, 0.3), 0.25, coat=0.8)
    pupil = HU.mat("traveller_pupil", (0.03, 0.02, 0.02), 0.3, coat=0.8)
    shine = mat("traveller_eye_glow", (1.0, 1.0, 1.0), 0.1, emit=3.0)
    hair = HU.mat("traveller_hair", (0.55, 0.19, 0.07), 0.55, coat=0.2)
    tie = HU.mat("traveller_hair_tie", (0.95, 0.35, 0.3), 0.5)
    hat = HU.mat("traveller_hat", (0.86, 0.74, 0.5), 0.8)
    band = HU.mat("traveller_hat_band", (0.9, 0.3, 0.22), 0.6)
    feather_m = HU.mat("traveller_feather", (0.2, 0.55, 0.85), 0.5)
    shirt = HU.mat("traveller_shirt", (0.14, 0.55, 0.56), 0.8)
    shirt_dk = HU.mat("traveller_shirt_dark", (0.08, 0.4, 0.42), 0.8)
    button = HU.mat("traveller_button", (0.96, 0.9, 0.76), 0.4, coat=0.5)
    scarf = HU.mat("traveller_scarf", (1.0, 0.74, 0.16), 0.7)
    shorts = HU.mat("traveller_shorts", (0.74, 0.6, 0.38), 0.85)
    socks = HU.mat("traveller_socks", (0.97, 0.94, 0.86), 0.85)
    stripe = HU.mat("traveller_sock_stripe", (0.9, 0.3, 0.22), 0.8)
    boots = HU.mat("traveller_boots", (0.44, 0.25, 0.12), 0.45, coat=0.35)
    sole = HU.mat("traveller_sole", (0.12, 0.08, 0.05), 0.7)
    leather = HU.mat("traveller_leather", (0.4, 0.22, 0.1), 0.5, coat=0.25)
    brass = mat("traveller_brass", (0.95, 0.72, 0.3), 0.3, 0.9)
    pack = HU.mat("traveller_pack", (0.95, 0.42, 0.12), 0.75)
    pack_dk = HU.mat("traveller_pack_dark", (0.7, 0.26, 0.08), 0.75)
    bedroll = HU.mat("traveller_bedroll", (0.25, 0.36, 0.62), 0.85)
    mug = mat("traveller_mug", (0.85, 0.87, 0.9), 0.35, 0.6)
    pennant = HU.mat("traveller_pennant", (0.98, 0.86, 0.3), 0.6)

    HU.human_body(sk, skin, shirt, shorts, white, iris, shoes=boots, sole=sole, glove=skin, sleeves="short",
                  hands="grip", shape=sh, head=False, shoe_height=0.28)
    # bare legs under the shorts
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.get("bone", "").startswith("~leg") and o.data.materials[0] is shorts:
            o.data.materials.clear()
            o.data.materials.append(skin)
    slim(boots, 0.6)
    slim(shorts, 0.6, bone="~body")
    slim(shirt, 0.55, bone="~body")
    for X in "LR":
        slim(skin, 0.7, bone="~leg." + X)
        slim(skin, 0.6, bone="hand." + X)
    for X, s in (("L", 1), ("R", -1)):
        # the shorts: flared legs to mid-thigh with turned-up cuffs
        pts = HU.leg_path(sk, X, 0.0, t1=0.22, shape=sh["legs"])
        fl = [0.012, 0.018, 0.024]
        pts = [(x + s * f * 0.3, y, z, r + f) for (x, y, z, r), f in zip(pts, fl)]
        HU.tube(pts, "~leg." + X, shorts, 18, 0.016, lateral=(s, 0, 0))
        e = pts[-1]
        a = HU._along(sk, "thigh." + X, 0.42)
        HU.tube([(e[0], e[1], e[2] + 0.03, e[3] + 0.004), (a.x + s * 0.008, a.y - 0.002, a.z, e[3] + 0.005)],
                "~leg." + X, shorts, 18, 0.012, lateral=(s, 0, 0))
        # knee socks with a stripe
        lp = HU.leg_path(sk, X, 0.006, shape=sh["legs"])
        HU.tube(lp[6:], "~leg." + X, socks, 16, 0.016, lateral=(s, 0, 0), caps=(True, False))
        HU.tube([lp[6][:3] + (lp[6][3] + 0.006,), lp[7][:3] + (lp[7][3] + 0.006,)], "~leg." + X, socks, 16, 0.012,
                lateral=(s, 0, 0))
        b0, b1 = HU._along(sk, "shin." + X, 0.3), HU._along(sk, "shin." + X, 0.36)
        HU.tube([(b0.x, b0.y + 0.012, b0.z, 0.056 * sh["legs"] + 0.012), (b1.x, b1.y + 0.012, b1.z, 0.055 * sh["legs"] + 0.012)],
                "~leg." + X, stripe, 16, 0.01, lateral=(s, 0, 0))
        # boot cuffs, laces and toe caps
        x = sk.head("foot." + X).x
        HU.body_loft([(0.25, 0.056, 0.064, 0.006), (0.3, 0.062, 0.07, 0.006)], "~foot." + X, leather, 18, 0, x0=x)
        for z in (0.14, 0.18, 0.22):
            HU.box((0.05, 0.012, 0.01), (x, -0.058, z), "~foot." + X, sole, bevel=0.003)
        HU.box((0.11, 0.27, 0.035), (x, -0.045, 0.017), "~foot." + X, sole, bevel=0.012)
        # sleeves: rolled cuffs
        HU.tube(HU.arm_path(sk, X, 0.024, 0.28, 0.36, shape=sh["arms"]), "~arm." + X, shirt_dk, 14, 0.02, lateral=(s, 0, 0))
        # epaulettes with a button
        shp = sk.head("arm." + X)
        HU.box((0.07, 0.05, 0.014), (shp.x - s * 0.04, shp.y, shp.z + 0.05), "~body", shirt_dk, rot=(0, s * 0.3, 0), bevel=0.006)
        HU.sphere(0.008, (shp.x - s * 0.02, shp.y - 0.01, shp.z + 0.06), "~body", button, (1, 1, 0.6), 8, 5)

    k = THEAD
    traveller_head(k, skin, cheek, white, iris, pupil, shine, lips, hair, freckle)
    traveller_hair_and_hat(k, hair, tie, hat, band, feather_m)

    ck = sh["chest"]
    # the shirt: an open collar, two chest pockets with flaps and buttons, a placket
    for s in (-1, 1):
        HU.box((0.075, 0.016, 0.075), (0.07 * s, -0.106 * ck, 1.29), "~body", shirt_dk, rot=(-0.14, 0, 0), bevel=0.008)
        HU.box((0.082, 0.02, 0.026), (0.07 * s, -0.112 * ck, 1.33), "~body", shirt_dk, rot=(-0.14, 0, 0), bevel=0.008)
        HU.sphere(0.008, (0.07 * s, -0.126 * ck, 1.325), "~body", button, (1, 0.6, 1), 8, 5)
        HU.box((0.06, 0.014, 0.07), (0.045 * s, -0.09, 1.44), "~body", shirt, rot=(-0.5, s * 0.5, s * 0.6), bevel=0.006)
    for z in (1.12, 1.19, 1.26):
        HU.sphere(0.008, (0.0, -0.112 * sh["waist"] - 0.004, z), "~body", button, (1, 0.6, 1), 8, 5)
    HU.box((0.022, 0.012, 0.28), (0.0, -0.106 * sh["waist"], 1.2), "~body", shirt_dk, rot=(-0.1, 0, 0), bevel=0.005)
    # a sunflower neckerchief knotted at the front
    HU.tube([(0.0, -0.085, 1.472, 0.024), (0.08, -0.05, 1.482, 0.026), (0.095, 0.02, 1.492, 0.026),
             (0.05, 0.08, 1.502, 0.024), (-0.02, 0.085, 1.502, 0.024), (-0.09, 0.03, 1.492, 0.026),
             (-0.08, -0.05, 1.482, 0.026), (0.0, -0.088, 1.472, 0.024)], "~body", scarf, 10, 0.03)
    HU.sphere(0.03, (0.0, -0.104, 1.46), "~body", scarf, (1.2, 0.7, 1.0), 12, 7)
    for s in (-1, 1):
        HU.tube([(0.01 * s, -0.11, 1.445, 0.022), (0.035 * s, -0.12, 1.4, 0.016), (0.04 * s, -0.118, 1.37, 0.005)],
                "~body", scarf, 8, 0.02, ell=(1.9, 0.4))
    # the belt, a brass buckle, a canteen on the left hip
    HU.body_loft([(z, rx + 0.012, ry + 0.012, cy_, sq) for z, rx, ry, cy_, sq in HU.torso_rings(0.98, 1.04, 0.0, sh)],
                 "~body", leather, 26, 0)
    HU.box((0.055, 0.02, 0.045), (0.0, -0.1 * sh["hips"] - 0.024, 1.01), "~body", brass, bevel=0.006)
    cx_ = 0.2 * sh["hips"]
    HU.sphere(0.07, (cx_, 0.0, 0.9), "hips", mat("traveller_canteen", (0.35, 0.5, 0.3), 0.6), (0.55, 1.0, 1.0), 20, 12)
    HU.sphere(0.074, (cx_, 0.0, 0.9), "hips", leather, (0.4, 1.02, 0.35), 20, 8)
    cap = cyl(0.016, 0.03, (cx_, 0.0, 0.975), brass, verts=10)
    cap["bone"] = "hips"
    # the backpack (rigid on the chest): a canvas pack with a flap, a front pocket, a bedroll on top, a tin mug,
    # and a pennant on a stick
    ch = "chest"
    PY = 0.21 * ck
    bp = [box((0.3, 0.19, 0.38), (0, PY, 1.2), pack, bevel=0.05, segs=3),
          box((0.31, 0.2, 0.11), (0, PY - 0.004, 1.35), pack_dk, bevel=0.04, segs=3),
          box((0.2, 0.06, 0.15), (0, PY + 0.11, 1.12), pack_dk, bevel=0.03, segs=2),
          box((0.2, 0.065, 0.04), (0, PY + 0.115, 1.2), pack, bevel=0.015),
          box((0.03, 0.012, 0.04), (0, PY + 0.148, 1.185), brass, bevel=0.004)]
    for s in (-1, 1):
        bp.append(box((0.04, 0.21, 0.018), (0.08 * s, PY, 1.36), leather, bevel=0.005))
        bp.append(box((0.07, 0.12, 0.16), (0.175 * s, PY + 0.01, 1.14), pack_dk, bevel=0.03, segs=2))   # side pockets
    bp.append(cyl(0.065, 0.42, (0, PY + 0.005, 1.47), bedroll, rot=(0, R90, 0), verts=22, bevel=0.012))
    bp.append(cyl(0.04, 0.425, (0, PY + 0.005, 1.47), mat("traveller_bedroll_end", (0.9, 0.85, 0.72), 0.8),
                  rot=(0, R90, 0), verts=18))
    for s in (-1, 1):
        bp.append(torus(0.068, 0.01, (0.13 * s, PY + 0.005, 1.47), leather, rot=(0, R90, 0), verts=22, minor=5))
    # the tin mug hanging on the right side, the pennant on a stick poking up on the left
    bp.append(cyl(0.035, 0.06, (-0.215, PY + 0.03, 1.05), mug, verts=16, bevel=0.004))
    bp.append(torus(0.02, 0.006, (-0.215, PY + 0.07, 1.05), mug, rot=(R90, 0, 0), verts=12, minor=4))
    bp.append(rod((0.19, PY + 0.04, 1.08), (0.24, PY + 0.07, 1.72), 0.008, mat("traveller_stick", (0.6, 0.38, 0.18), 0.5),
                  verts=8))
    bp.append(sphere(0.014, (0.242, PY + 0.071, 1.735), brass, segs=8, rings=6))
    fl = K.prism([(0.0, 0.0), (0.16, -0.045), (0.0, -0.1)], 0.008, (0, 0, 0), pennant, bevel=0.002)
    fl.data.transform(Matrix.Translation((0.238, PY + 0.068, 1.71)) @ Matrix.Rotation(math.radians(30), 4, "Z"))
    bp.append(fl)
    dot = K.prism([(0.0, 0.0), (0.05, -0.014), (0.0, -0.03)], 0.012, (0, 0, 0), band, bevel=0.001)
    dot.data.transform(Matrix.Translation((0.238, PY + 0.068, 1.675)) @ Matrix.Rotation(math.radians(30), 4, "Z"))
    bp.append(dot)
    for o in bp:
        if o.matrix_world != Matrix.Identity(4):
            xf(o, Matrix.Identity(4))
        o["bone"] = ch
    # the shoulder straps, over the shirt, front and back
    for s in (-1, 1):
        HU.tube([(0.09 * s, 0.12, 1.4, 0.013), (0.11 * s, 0.03, 1.49, 0.013), (0.12 * s, -0.07, 1.45, 0.013),
                 (0.125 * s, -0.12 * ck, 1.33, 0.013), (0.12 * s, -0.115 * ck, 1.2, 0.013), (0.13 * s, -0.06, 1.1, 0.012),
                 (0.13 * s, 0.1, 1.05, 0.012)], "~body", leather, 6, 0.028, ell=(1.9, 0.5))
        HU.box((0.03, 0.012, 0.03), (0.123 * s, -0.126 * ck, 1.28), "~body", brass, bevel=0.004)

    # the height sets the node scale, and with it the run's stride
    zs = [o.matrix_world @ v.co for o in bpy.context.scene.objects if o.type == "MESH" and "bone" in o
          for v in o.data.vertices]
    height = max(v.z for v in zs)
    T_SCALE = TALL / height
    print("   rig height %.3f -> scale %.4f" % (height, T_SCALE))

    parts, M, muzzle, fore = launcher_parts(sk)
    FORE = (fore.x, -fore.y, fore.z)
    launcher = join(parts, "launcher", pivot=tuple(M.translation))
    mz = empty("muzzle")
    mz.empty_display_size = 0.05
    mz.matrix_world = M.to_3x3().to_4x4()
    mz.location = muzzle
    export_rig("traveller", traveller_actions(), sk, T_SCALE, 0.0, attach=[(launcher, "hand.R"), (mz, "hand.R")])
    print("   run: %.3f units per %d-frame cycle (%.2f units/s at speed_scale 1)" % (
        WALK * RUN_FRAMES / FPS, RUN_FRAMES, WALK))


# ------------------------------------------------------------------ balloons

RADII = [0.24, 0.44, 0.72, 1.05]


def balloon_mats():
    return (mat("balloon", (0.93, 0.93, 0.92), 0.22, coat=1.0),
            mat("balloon_sheen", (1.0, 1.0, 1.0), 0.15, coat=0.5))


def balloon(size):
    body_m, sheen_m = balloon_mats()
    r = RADII[size]
    segs = [32, 40, 48, 56][size]
    rings = [18, 24, 28, 32][size]
    b = sphere(r, (0, 0, 0), body_m, segs=segs, rings=rings)
    for v in b.data.vertices:            # an egg: the bottom drawn down a little towards the knot
        z = v.co.z / r
        if z < 0:
            v.co.z *= 1 + 0.06 * z * z
            k = 1 - 0.05 * z * z
            v.co.x *= k
            v.co.y *= k
    b.data.update()
    parts = [b]
    # the knot: a pinched neck, a tied lump, a rolled lip
    zb = -r * 1.06
    kr = max(0.03, r * 0.075)
    parts.append(rod((0, 0, zb + kr * 0.8), (0, 0, zb - kr * 0.6), kr * 0.55, body_m, r2=kr * 0.35, verts=14))
    parts.append(sphere(kr * 0.7, (0, 0, zb - kr * 0.9), body_m, scale=(1.1, 0.9, 0.85), segs=14, rings=8))
    parts.append(torus(kr * 0.55, kr * 0.28, (0, 0, zb - kr * 1.5), body_m, verts=16, minor=6, scale=(1, 1, 0.8)))
    # a painted highlight on the camera side, upper left: a soft oval and a small dot, lying on the skin
    for az, el, a_, b_, rot in ((-38, 36, 0.3, 0.16, 35), (-52, 16, 0.07, 0.06, 0)):
        d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)),
                    math.sin(math.radians(el))))
        t1 = Vector((0, 0, 1)).cross(d).normalized()
        t2 = d.cross(t1)
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        t1, t2 = t1 * cr + t2 * sr, t2 * cr - t1 * sr
        bm = bmesh.new()
        nr, na = 4, 24
        centre = bm.verts.new(d * r * 1.003)
        rings_ = []
        for i in range(1, nr + 1):
            u = i / nr
            rings_.append([bm.verts.new((d + (t1 * a_ * math.cos(2 * math.pi * j / na) + t2 * b_ * math.sin(2 * math.pi * j / na)) * u)
                                        .normalized() * r * 1.003) for j in range(na)])
        for j in range(na):
            bm.faces.new((centre, rings_[0][j], rings_[0][(j + 1) % na]))
        for r0, r1 in zip(rings_, rings_[1:]):
            for j in range(na):
                bm.faces.new((r0[j], r1[j], r1[(j + 1) % na], r0[(j + 1) % na]))
        me = bpy.data.meshes.new("sheen")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("sheen", me)
        bpy.context.scene.collection.objects.link(ob)
        for p_ in ob.data.polygons:
            if p_.normal.dot(p_.center) < 0:
                p_.flip()
        ob.data.update()
        parts.append(K.finish(ob, sheen_m, smooth=80))
    export(join(parts, "balloon_%d" % size), "balloon_%d" % size)


def balloon_shard():
    body_m, _ = balloon_mats()
    rnd = random.Random(9)
    bm = bmesh.new()
    n = 18
    ring = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 0.075 * (0.8 + 0.2 * math.sin(3 * a + 1)) * (1.0 if i % 3 else 0.72 + 0.1 * rnd.random())   # torn edge
        ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a) * 0.8, 0)))
    c = bm.verts.new((0, 0, 0))
    for i in range(n):
        bm.faces.new((c, ring[i], ring[(i + 1) % n]))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
    for v in bm.verts:                    # curled like a scrap of rubber
        x, y = v.co.x, v.co.y
        v.co.z = 0.35 * (x * x) / 0.08 - 0.25 * (y * y) / 0.08 + 0.02 * math.sin(x * 60 + y * 30)
    o = bpy.data.meshes.new("balloon_shard")
    bm.to_mesh(o)
    bm.free()
    ob = bpy.data.objects.new("balloon_shard", o)
    bpy.context.scene.collection.objects.link(ob)
    solid(ob, 0.006)
    K.finish(ob, body_m, smooth=60)
    ob.rotation_euler = (math.radians(70), 0, 0)
    export(join([ob], "balloon_shard"), "balloon_shard")


# ------------------------------------------------------------------ the harpoon tip

def wire():
    steel = mat("wire_steel", (0.78, 0.82, 0.88), 0.2, 1.0)
    brass = mat("wire_brass", (0.95, 0.7, 0.28), 0.28, 0.95)
    glow = mat("wire_glow", (0.7, 0.95, 1.0), 0.2, emit=3.0)
    parts = [cyl(0.03, 0.05, (0, 0, 0.025), brass, verts=16, bevel=0.006),
             torus(0.03, 0.006, (0, 0, 0.052), brass, verts=16, minor=5),
             rod((0, 0, 0.05), (0, 0, 0.14), 0.014, steel, verts=12)]
    # a barbed arrowhead, flat to the camera (faces +-Y), with a raised glowing ridge
    head = [(0.0, 0.3), (0.035, 0.2), (0.07, 0.12), (0.024, 0.155), (0.018, 0.12), (-0.018, 0.12), (-0.024, 0.155),
            (-0.07, 0.12), (-0.035, 0.2)]
    parts.append(K.prism(head, 0.022, (0, 0, 0), steel, bevel=0.006, segs=2))
    parts.append(K.prism([(0.0, 0.292), (0.012, 0.2), (0.0, 0.13), (-0.012, 0.2)], 0.03, (0, 0, 0), glow, bevel=0.002))
    parts.append(ico(0.022, (0, 0, 0.128), steel, sub=1))
    export(join(parts, "wire"), "wire")


# ------------------------------------------------------------------ blocks

def block_mats():
    return (mat("block_stone", (0.66, 0.6, 0.52), 0.8),
            mat("block_stone_dark", (0.45, 0.4, 0.34), 0.85),
            mat("block_gold", (1.0, 0.76, 0.3), 0.28, 0.95),
            mat("block_carve", (0.36, 0.31, 0.26), 0.9))


def block_parts(cracked=False):
    stone, dark, gold, carve = block_mats()
    parts = [box((0.98, 0.98, 0.98), (0, 0, 0), stone, bevel=0.06, segs=3)]
    # gilded frame round the front face, bars along the top front and back edges
    F = -0.5
    t = 0.06
    frame = [((0, F, 0.44), (0.9, 0.03, t)), ((0, F, -0.44), (0.9, 0.03, t)),
             ((0.44, F, 0), (t, 0.03, 0.82)), ((-0.44, F, 0), (t, 0.03, 0.82))]
    for loc, size in frame:
        parts.append(box(size, loc, gold, bevel=0.012))
    parts.append(box((0.9, 0.9, 0.03), (0, 0, 0.495), dark, bevel=0.012))           # the top's inlaid slab
    for y in (-0.44, 0.44):
        parts.append(box((0.9, t, 0.03), (0, y, 0.5), gold, bevel=0.01))
    for x in (-0.44, 0.44):
        for z in (-0.44, 0.44):
            parts.append(sphere(0.045, (x, F - 0.015, z), gold, scale=(1, 0.6, 1), segs=14, rings=8))
    # a recessed panel with a carved sun: a disc, rays, an inner ring
    parts.append(box((0.68, 0.03, 0.68), (0, F + 0.004, 0), dark, bevel=0.02))
    parts.append(cyl(0.13, 0.03, (0, F - 0.005, 0), stone, rot=(R90, 0, 0), verts=24, bevel=0.01))
    parts.append(torus(0.17, 0.014, (0, F - 0.004, 0), carve, rot=(R90, 0, 0), verts=28, minor=5))
    for i in range(12):
        a = 2 * math.pi * i / 12
        l = 0.3 if i % 2 == 0 else 0.25
        parts.append(K.prism([(-0.022, 0.0), (0.022, 0.0), (0.0, l - 0.2)], 0.024, (0, 0, 0), carve, bevel=0.003))
        parts[-1].data.transform(Matrix.Translation((0, F - 0.004, 0)) @ Matrix.Rotation(-a, 4, "Y")
                                 @ Matrix.Translation((0, 0, 0.2)))
    parts.append(cyl(0.05, 0.036, (0, F - 0.008, 0), gold, rot=(R90, 0, 0), verts=18, bevel=0.008))
    return parts


def block():
    export(join(block_parts(), "block"), "block")


def block_cracked():
    stone, dark, gold, carve = block_mats()
    crack = mat("block_crack", (0.12, 0.08, 0.06), 0.9)
    glow = mat("block_crack_glow", (1.0, 0.55, 0.2), 0.5, emit=2.5)
    parts = block_parts(True)
    # a chipped corner (top right front) and a notch knocked out of the bottom frame: each part is cut on its own
    # (they are closed meshes; the joined block is not)
    for loc, rot, size in (((0.5, -0.5, 0.5), (0.5, 0.4, 0.7), 0.34), ((-0.3, -0.52, -0.46), (0.3, 0.2, 0.9), 0.14)):
        bpy.ops.mesh.primitive_cube_add(size=size, location=loc, rotation=rot)
        cutter = K.active()
        c = Vector(loc)
        keep = []
        for o in parts:
            bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
            lo = Vector(map(min, *bb))
            hi = Vector(map(max, *bb))
            q = Vector((min(max(c.x, lo.x), hi.x), min(max(c.y, lo.y), hi.y), min(max(c.z, lo.z), hi.z)))
            if (q - c).length > size * 0.87:
                keep.append(o)
                continue
            mod = o.modifiers.new("chip", "BOOLEAN")
            mod.object = cutter
            mod.operation = "DIFFERENCE"
            mod.solver = "EXACT"
            K.select(o)
            bpy.ops.object.modifier_apply(modifier=mod.name)
            if len(o.data.vertices) > 0:
                keep.append(o)
            else:
                bpy.data.objects.remove(o, do_unlink=True)
        parts = keep
        bpy.data.objects.remove(cutter, do_unlink=True)
    o = join(parts, "block_cracked")
    parts = [o]
    rnd = random.Random(23)
    # the crack: a zigzag across the front from the chipped corner down to the bottom left, branching,
    # then over the top towards the back
    main = [(0.34, 0.3), (0.2, 0.2), (0.16, 0.06), (0.02, -0.02), (-0.06, -0.16), (-0.2, -0.22), (-0.26, -0.34),
            (-0.37, -0.45)]
    branch = [(0.02, -0.02), (0.14, -0.14), (0.2, -0.3), (0.34, -0.36)]
    branch2 = [(0.16, 0.06), (-0.04, 0.16), (-0.14, 0.32), (-0.2, 0.5)]
    for line, w in ((main, 0.026), (branch, 0.016), (branch2, 0.014)):
        pts = [(x, -0.5, z) for x, z in line]
        ct = tube(pts, [w * (1.0 if i < len(pts) - 1 else 0.4) for i in range(len(pts))], crack, verts=8, name="crack")
        ct.data.transform(Matrix.Translation((0, -0.512, 0)) @ Matrix.Diagonal((1, 0.5, 1, 1))
                          @ Matrix.Translation((0, 0.5, 0)))
        parts.append(ct)
        # glowing embers deep in the widest part of the crack
        pts2 = [(x, -0.5, z) for x, z in line[1:-1]]
        if w > 0.02:
            et = tube(pts2, [0.007] * len(pts2), glow, verts=6, name="ember")
            et.data.transform(Matrix.Translation((0, -0.5235, 0)) @ Matrix.Diagonal((1, 0.6, 1, 1))
                              @ Matrix.Translation((0, 0.5, 0)))
            parts.append(et)
    top = [(-0.2, -0.5), (-0.16, -0.3), (-0.04, -0.2), (0.0, 0.0), (0.12, 0.12), (0.1, 0.3)]
    ct = tube([(x, y, 0.5) for x, y in top], [0.02, 0.02, 0.018, 0.016, 0.012, 0.006], crack, verts=8, name="crack_top")
    ct.data.transform(Matrix.Translation((0, 0, 0.51)) @ Matrix.Diagonal((1, 1, 0.35, 1)) @ Matrix.Translation((0, 0, -0.5)))
    parts.append(ct)
    # a few chips of stone scattered in the crack's mouth
    for i in range(5):
        x, z = main[1 + i]
        parts.append(lumpy(0.018 + 0.008 * rnd.random(), (x + 0.03, -0.505, z - 0.02), dark, 50 + i, 0.25))
    export(join(parts, "block_cracked"), "block_cracked")


# ------------------------------------------------------------------ items

def halo(kind, color):
    g = mat("item_%s_glow" % kind, color, 0.3, emit=2.2)
    return [torus(0.225, 0.016, (0, 0.07, 0.25), g, rot=(R90, 0, 0), verts=40, minor=6),
            torus(0.2, 0.006, (0, 0.075, 0.25), g, rot=(R90, 0, 0), verts=40, minor=4)]


def arrow(x, tilt, steel, brass, wood):
    """A stubby harpoon arrow, 0.44 long, rising from (x, 0.03), tilted `tilt` degrees about the view axis."""
    ps = [rod((0, 0, 0.04), (0, 0, 0.3), 0.018, wood, verts=10),
          cyl(0.026, 0.04, (0, 0, 0.06), brass, verts=12, bevel=0.005),
          cyl(0.024, 0.03, (0, 0, 0.3), brass, verts=12, bevel=0.005)]
    ps.append(K.prism([(0.0, 0.47), (0.05, 0.36), (0.09, 0.28), (0.03, 0.32), (0.022, 0.3), (-0.022, 0.3),
                       (-0.03, 0.32), (-0.09, 0.28), (-0.05, 0.36)], 0.03, (0, 0, 0), steel, bevel=0.008))
    for s in (-1, 1):   # fletching
        ps.append(K.prism([(0.0, 0.0), (0.05 * s, -0.02), (0.05 * s, 0.07), (0.0, 0.12)], 0.01, (0, 0, 0),
                          mat("item_fletch", (0.95, 0.95, 0.9), 0.6), bevel=0.002))
        ps[-1].data.transform(Matrix.Translation((0, 0, 0.04)))
    M = Matrix.Translation((x, 0, 0.03)) @ Matrix.Rotation(math.radians(tilt), 4, "Y")
    for o in ps:
        xf(o, M)
    return ps


def item_double():
    steel = mat("item_steel", (0.8, 0.84, 0.9), 0.2, 1.0)
    brass = mat("item_brass", (0.98, 0.74, 0.3), 0.28, 0.95)
    wood = mat("item_wood", (0.55, 0.3, 0.12), 0.5, coat=0.3)
    ribbon = mat("item_ribbon", (0.9, 0.12, 0.15), 0.5, coat=0.3)
    parts = halo("double", (0.25, 0.9, 1.0))
    parts += arrow(-0.06, -15, steel, brass, wood)
    parts += arrow(0.06, 15, steel, brass, wood)
    parts.append(torus(0.085, 0.018, (0, 0, 0.17), ribbon, verts=24, minor=6, scale=(1.0, 0.45, 0.55)))
    for s in (-1, 1):
        parts.append(sphere(0.04, (0.05 * s, -0.035, 0.17), ribbon, scale=(1.2, 0.5, 0.8), segs=12, rings=8))
        parts.append(K.prism([(0, 0), (0.05 * s, -0.08), (0.02 * s, -0.09)], 0.01, (0, -0.035, 0.16), ribbon, bevel=0.002))
    parts.append(sphere(0.025, (0, -0.045, 0.17), ribbon, segs=12, rings=8))
    export(join(parts, "item_double"), "item_double")


def item_sticky():
    steel = mat("item_steel", (0.8, 0.84, 0.9), 0.2, 1.0)
    brass = mat("item_brass", (0.98, 0.74, 0.3), 0.28, 0.95)
    goo = mat("item_sticky_goo", (0.35, 0.95, 0.2), 0.08, coat=1.0, emit=0.5, emit_color=(0.4, 1.0, 0.2))
    parts = halo("sticky", (0.55, 1.0, 0.25))
    # a hook: an eye at the top, a shank, a J bend with a barbed point
    parts.append(torus(0.04, 0.014, (0, 0, 0.44), steel, rot=(R90, 0, 0), verts=18, minor=6))
    pts = [(0, 0, 0.4), (0, 0, 0.3), (0, 0, 0.2), (0.01, 0, 0.14)]
    for i in range(9):
        a = math.pi * (1.0 + i / 8)
        pts.append((0.075 + 0.075 * math.cos(a), 0, 0.14 + 0.075 * math.sin(a)))
    pts.append((0.15, 0, 0.2))
    parts.append(tube(pts, [0.018] * (len(pts) - 1) + [0.006], steel, verts=10, name="hook"))
    parts.append(K.prism([(0.15, 0.2), (0.12, 0.17), (0.155, 0.16)], 0.02, (0, 0, 0), steel, bevel=0.003))
    parts.append(cyl(0.024, 0.03, (0, 0, 0.38), brass, verts=12, bevel=0.004))
    # green goo coating the bend in a glossy, lumpy sleeve, a blob on the point, two drips hanging from the bottom
    rnd = random.Random(12)
    bend = pts[3:-1]
    parts.append(tube(bend, [0.028 + 0.005 * math.sin(i * 1.9) ** 2 for i in range(len(bend))], goo, verts=14,
                      name="goo"))
    parts.append(lumpy(0.036, (0.148, 0, 0.19), goo, 4, 0.06, scale=(1, 0.9, 1.15), sub=2, smooth=80))
    for x, l in ((0.05, 0.05), (0.1, 0.028)):
        z0 = 0.045
        parts.append(rod((x, 0, z0 + 0.01), (x, 0, z0 - l), 0.013, goo, r2=0.009, verts=10))
        parts.append(sphere(0.018, (x, 0, z0 - l - 0.01), goo, scale=(1, 1, 1.3), segs=12, rings=8))
    for i in range(3):                     # glossy glints on the coat
        t = bend[2 + i * 2]
        parts.append(sphere(0.007, (t[0], -0.027, t[2] + 0.012), mat("item_sticky_shine", (0.9, 1.0, 0.8), 0.05),
                            scale=(1.6, 0.5, 1), segs=8, rings=6))
    o = join(parts, "item_sticky")
    o.data.transform(Matrix.Translation((-0.075, 0, 0)))
    for v in o.data.vertices:
        pass
    export(o, "item_sticky")


def item_shield():
    enamel = mat("item_shield_enamel", (0.15, 0.35, 0.9), 0.25, coat=0.8)
    gold = mat("item_brass", (0.98, 0.74, 0.3), 0.28, 0.95)
    bubble = mat("item_shield_bubble", (0.75, 0.92, 1.0), 0.03, coat=1.0, alpha=0.3)
    parts = halo("shield", (0.4, 0.8, 1.0))
    # a heater shield outline
    out = []
    for i in range(13):
        a = math.pi * i / 12
        out.append((0.12 * math.cos(math.pi - a) , 0.0))
    shape = [(-0.12, 0.34), (0.12, 0.34), (0.12, 0.22)]
    for i in range(1, 9):
        u = i / 9
        shape.append((0.12 * (1 - u) ** 0.8 * math.cos(u * 0.6), 0.22 - 0.16 * math.sin(u * math.pi / 2)))
    shape.append((0.0, 0.06))
    for x, z in reversed(shape[3:-1]):
        shape.append((-x, z))
    shape.append((-0.12, 0.22))
    rim = K.prism([(x * 1.18, 0.2 + (z - 0.2) * 1.14) for x, z in shape], 0.03, (0, 0, 0), gold, bevel=0.008)
    face = K.prism(shape, 0.04, (0, -0.004, 0), enamel, bevel=0.01)
    parts += [rim, face]
    star = []
    for i in range(10):
        a = math.pi / 2 + math.pi * i / 5
        rr = 0.06 if i % 2 == 0 else 0.025
        star.append((rr * math.cos(a), 0.215 + rr * math.sin(a)))
    parts.append(K.prism(star, 0.05, (0, -0.006, 0), gold, bevel=0.004))
    parts.append(sphere(0.2, (0, 0, 0.21), bubble, segs=32, rings=16))
    parts.append(sphere(0.03, (-0.09, -0.16, 0.3), mat("item_shield_glint", (1, 1, 1), 0.1), scale=(1.4, 0.4, 0.8),
                        segs=10, rings=6))
    export(join(parts, "item_shield"), "item_shield")


def item_clock():
    gold = mat("item_brass", (0.98, 0.74, 0.3), 0.28, 0.95)
    face_m = mat("item_clock_face_glow", (1.0, 0.97, 0.88), 0.4, emit=0.9)
    ink = mat("item_clock_ink", (0.1, 0.08, 0.1), 0.5)
    red = mat("item_ribbon", (0.9, 0.12, 0.15), 0.5, coat=0.3)
    glass = mat("item_glass", (0.9, 0.95, 1.0), 0.02, coat=1.0, alpha=0.25)
    parts = halo("clock", (1.0, 0.72, 0.2))
    C = Vector((0, 0, 0.21))
    parts.append(cyl(0.17, 0.07, C, gold, rot=(R90, 0, 0), verts=40, bevel=0.025, segs=3))
    parts.append(torus(0.155, 0.014, C + Vector((0, -0.036, 0)), gold, rot=(R90, 0, 0), verts=40, minor=6))
    parts.append(cyl(0.145, 0.01, C + Vector((0, -0.033, 0)), face_m, rot=(R90, 0, 0), verts=40))
    for i in range(12):
        a = 2 * math.pi * i / 12
        big = i % 3 == 0
        parts.append(box((0.012 if big else 0.007, 0.006, 0.03 if big else 0.018),
                         (0.118 * math.sin(a), -0.04, C.z + 0.118 * math.cos(a)), ink, rot=(0, a, 0), bevel=0.0))
    for ang, l, w in ((-60, 0.07, 0.012), (60, 0.1, 0.008)):       # ten to two
        a = math.radians(ang)
        parts.append(box((w, 0.006, l), (l / 2 * math.sin(a), -0.044, C.z + l / 2 * math.cos(a)), ink, rot=(0, a, 0),
                         bevel=0.0))
    parts.append(cyl(0.012, 0.012, C + Vector((0, -0.046, 0)), red, rot=(R90, 0, 0), verts=12))
    parts.append(sphere(0.15, C + Vector((0, -0.03, 0)), glass, scale=(1, 0.22, 1), segs=28, rings=12))
    # the crown and the bow on top
    parts.append(cyl(0.022, 0.03, (0, 0, 0.395), gold, verts=14, bevel=0.004))
    parts.append(cyl(0.028, 0.025, (0, 0, 0.42), gold, verts=16, bevel=0.006))
    parts.append(torus(0.045, 0.011, (0, 0, 0.47), gold, rot=(R90, 0, 0), verts=24, minor=6))
    export(join(parts, "item_clock"), "item_clock")


def item_charge():
    red = mat("item_charge_red", (0.9, 0.12, 0.1), 0.35, coat=0.7)
    gold = mat("item_brass", (0.98, 0.74, 0.3), 0.28, 0.95)
    paper = mat("item_charge_paper", (0.98, 0.92, 0.78), 0.7)
    fuse = mat("item_charge_fuse", (0.3, 0.2, 0.1), 0.8)
    spark = mat("item_charge_spark_glow", (1.0, 0.8, 0.3), 0.3, emit=6.0)
    parts = halo("charge", (1.0, 0.45, 0.12))
    parts.append(cyl(0.075, 0.26, (0, 0, 0.2), red, verts=24, bevel=0.01))
    parts.append(cyl(0.078, 0.03, (0, 0, 0.1), paper, verts=24, bevel=0.005))
    for z0 in (0.13, 0.19, 0.25):           # a gold spiral band
        pts = [(0.079 * math.cos(a), 0.079 * math.sin(a), z0 + 0.05 * a / (2 * math.pi))
               for a in (2 * math.pi * i / 16 for i in range(17))]
        parts.append(tube(pts, [0.008] * len(pts), gold, verts=6, name="spiral"))
    parts.append(cyl(0.08, 0.13, (0, 0, 0.395), red, r2=0.0, verts=24))           # the nose cone
    parts.append(cyl(0.083, 0.02, (0, 0, 0.34), gold, verts=24, bevel=0.004))
    parts.append(sphere(0.018, (0, 0, 0.462), gold, segs=10, rings=6))
    for i in range(3):                      # fins, one towards the camera
        a = math.radians(-90 + 120 * i)
        fin = K.prism([(0.0, 0.0), (0.09, -0.05), (0.09, 0.02), (0.0, 0.12)], 0.014, (0, 0, 0), gold, bevel=0.003)
        fin.data.transform(Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0.06, 0, 0.1)))
        parts.append(fin)
    # a star on the camera side, the fuse from the bottom with a spark
    star = []
    for i in range(10):
        a = math.pi / 2 + math.pi * i / 5
        rr = 0.04 if i % 2 == 0 else 0.017
        star.append((rr * math.cos(a), 0.22 + rr * math.sin(a)))
    st = K.prism(star, 0.01, (0, -0.076, 0), paper, bevel=0.002)
    parts.append(st)
    parts.append(tube([(0.02, -0.02, 0.07), (0.07, -0.04, 0.04), (0.12, -0.03, 0.05), (0.14, -0.02, 0.09)],
                      [0.008] * 4, fuse, verts=6, name="fuse"))
    parts.append(ico(0.025, (0.145, -0.02, 0.1), spark, sub=2))
    for i in range(7):
        d = Vector((math.cos(i * 0.9), -0.6, math.sin(i * 1.7) + 0.4)).normalized()
        parts.append(rod((0.145, -0.02, 0.1), Vector((0.145, -0.02, 0.1)) + d * 0.05, 0.004, spark, r2=0.0, verts=4))
    export(join(parts, "item_charge"), "item_charge")


JOBS = {"traveller": traveller,
        "balloon_0": lambda: balloon(0), "balloon_1": lambda: balloon(1), "balloon_2": lambda: balloon(2),
        "balloon_3": lambda: balloon(3), "balloon_shard": balloon_shard, "wire": wire, "block": block,
        "block_cracked": block_cracked, "item_double": item_double, "item_sticky": item_sticky,
        "item_shield": item_shield, "item_clock": item_clock, "item_charge": item_charge}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            clear_all()
            fn()
