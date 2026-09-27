"""Relic Run (game 19) models: the explorer (on the shared humanoid rig), three enemies (a clockwork temple automaton,
a cartoon skeleton sentry, a bat), the traps, pickups and props, the temple tiles and the backdrop.
Original designs (no real deities or cultures: the glyphs, the idol and the stone face are made up). Deterministic;
output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/relic_models.py -- godot/games/relic/art/models [name ...]
Helpers come from humanoid.py (the 26-bone rig, smooth skin, IK poses, gait), blastyard_models.py (mat, box, cyl, ...),
blastyard_bombers.py and hopline_models.py (Rig, TurnRig for the bat), prism_models.py, mossfolk_models.py,
slipfloe_models.py. 30 fps. 1 tile = 1 unit.

Axes: Blender Z up, the camera side is -Y; in Godot +X stays +X, Blender +Z is +Y (up), Blender -Y is +Z (towards the
camera). Characters face Godot +X, turned towards the camera (explorer 28 degrees, automaton and skeleton 15, bat 55)
so faces read; mirror with scale.x = -1 to face -X. Origins at the feet / base centre unless noted.

explorer.glb   armature "explorer_rig" (26 bones: root, hips, spine, chest, neck, head, clavicle/arm/forearm/hand.L/R,
               thigh/shin/foot/toe.L/R) with the skinned mesh "explorer" and a bone-attached node "pistol" (bone hand.R,
               always visible). 1.70 tall at node scale 1 (helmet top); scale the node by about 0.88 for 1.5 tiles.
               Materials: explorer_skin, _cheek, _stubble, _lips, _eye_white, _iris, _hair, _shirt, _shirt_dark,
               _trousers, _boots, _sole, _leather, _leather_dark, _brass, _helmet, _helmet_band, _scarf, _pistol,
               _pistol_grip.
               Animations (loops marked *):
                 idle*   2.4 s, breathing, a glance round
                 walk*   0.47 s, a quick run: 2.34 tiles per cycle at 0.88 node scale (5.0 tiles/s at speed_scale 1;
                         the engine's WALK 5.2 -> speed_scale 1.04). One stride per cycle, no root travel.
                 jump    0.43 s, crouch, spring, knees tucked, arms up (holds the last frame)
                 fall*   0.4 s, arms up and flailing, legs kicking
                 climb*  0.53 s, turned to show his back (facing the ladder), hands and feet alternate on the rungs,
                         in place: 0.61 tiles per cycle at 0.88 scale (1.14 tiles/s; CLIMB 3.6 -> speed_scale 3.2, or
                         clamp it). Put the node 0.23 in front of the ladder (Godot +Z) so the hands reach the rungs.
                 crawl*  0.53 s, on hands and knees (top of the helmet 0.90 at scale 1, 0.79 at 0.88 scale), 0.55 tiles
                         per cycle (1.02 tiles/s; CRAWL 2.4 -> speed_scale 2.35)
                 shoot   0.3 s, the pistol snaps up to point along +X at chest height and fires at frame 4 (0.1 s),
                         kicks and holds the aim; muzzle at about (0.74, 1.24, 0.13) from the origin at scale 1
                         (x0.88 in game)
                 plant   0.5 s, squats and sets the dynamite down with both hands at about x = +0.4 (0.27 s), stands
                 die     1.3 s, a comic flop: a jolt with the hands up, a wobble, falls stiff on his back, bounces, lies
                         spread out (holds; the body lies from x = -1.0 to +0.7 at scale 1)
                 cheer*  1 s, two hops, the left fist pumping
automaton.glb  armature "automaton_rig" (the same 26 bones), mesh "automaton", 1.60 tall: a carved stone and bronze
               clockwork guardian with a cog waist, a glowing core, a visor slit and a wind-up key in its back.
               Materials automaton_stone, _stone_dark, _bronze, _verdigris, _moss, automaton_glow (the eyes and core,
               emissive cyan). idle* 2 s (a slow head scan), walk* 1 s (a heavy stomp, 1.5 rig m = 1.28 model units per
               cycle, 1.2 tiles/s at 0.94 scale: the engine's 1.6 -> speed_scale 1.33), hit 0.57 s (a jolt back, head
               knocked, recovers), die 1.3 s (extra: sags, topples forward face down, holds;
               lies from x = -0.7 to +1.1).
skeleton.glb   armature "skeleton_rig", mesh "skeleton", 1.60 tall: a cartoon skeleton sentry in a dented bronze helmet
               with a short bronze sword (in the mesh, on hand.R). Materials skeleton_bone, _bone_shade, _socket,
               skeleton_glow (eye embers, emissive), _helmet, _rust, _cloth, _blade. idle* 1.6 s, walk* 0.8 s (a jaunty
               bouncing stride, 1.9 rig m = 1.56 model units per cycle, 1.8 tiles/s at 0.94 scale: the engine's 2.2 ->
               speed_scale 1.2), hit 0.5 s (a rattle, ends standing), die 0.77 s (extra: buckles into a heap 0.5 tall, holds).
bat.glb        armature "bat_rig", mesh "bat": a round temple bat, 1.2 wingspan, origin at the body centre (hover it).
               Materials bat_fur, _face, _wing, _finger, _ear, _fang, bat_glow (eyes). fly* 0.5 s, die 0.73 s (extra:
               folds and tumbles 0.45 down).
Traps and objects (one node named like the file unless noted):
  spikes         a row of iron spikes 1 wide, 0.8 tall, rising from the origin (the floor) along +Y: raise the node
                 from y = -0.8 to 0. spikes_iron, spikes_tip, spikes_rust.
  dart_hole      a 1x1x1 wall block (origin at the centre) carved with a serpent's head, jaws open at the +X face:
                 darts leave from (0.5, 0.06, 0). Mirror it to shoot along -X. dart_hole_jade (the eye, slightly
                 emissive), dart_hole_dark, tile_* stone.
  dart           0.36 long pointing +X, origin at its middle. dart_wood, dart_tip, dart_feather.
  boulder        a carved stone ball 1.8 across, origin at the centre, grooved bands and a spiral on each face so the
                 roll reads: rotate it about Godot Z by -distance / 0.9 when rolling right. boulder_stone, _groove, _moss.
  crusher        a stone block 1 wide x 1.2 tall with a scowling face, bronze bands and iron spikes below reaching 1.5;
                 origin at the TOP centre. crusher_bronze, crusher_iron, tile_* stone.
  breakable      a cracked stone block 1x1x1, origin at the centre. rubble.glb: root "rubble" (empty, the block
                 centre) with children rubble_0..rubble_7 (chunks, each origin at its own centre, spread over the block).
  dynamite       a bundle of three sticks, 0.45 tall with its fuse, origin at the base; child "spark" (dynamite_fuse,
                 emissive) at the fuse tip (0.1, 0.42, 0): flicker or scale it while the fuse burns.
  ammo_box       an olive tin with brass cartridges on the lid, 0.5 wide, 0.46 tall. ammo_tin, _tin_dark, _brass, _lead.
  dynamite_box   a wooden crate with sticks poking out, 0.55 wide, 0.5 tall. dynbox_wood, _wood_dark, dynamite_*.
  treasure_idol  a chubby golden made-up idol, 0.6 tall; treasure_gem a cut ruby 0.3 tall; treasure_coin a standing
                 gold coin 0.3 across. Materials treasure_gold, _gold_dark, _ruby, _emerald, _shine (emissive glints);
                 the gold is slightly emissive so it reads in the dark. Origins at the base.
  exit_door      a carved doorway 2 wide, 3 tall (origin at the bottom centre, sill at y 0..0.1), a lintel with a
                 bronze sun, a warm glow deep inside (exit_glow). exit_dark, exit_bronze, tile_* stone, tile_moss.
  ladder         one tile: poles at x = +-0.32, four rungs (y 0.125 .. 0.875), rope lashings; origin at the bottom
                 centre, depth -0.1 .. +0.05. Stack every 1.0. ladder_wood, _wood_dark, _rope.
  torch          a wall torch: origin at the bronze mount (on the wall face); child "flame" (torch_flame,
                 torch_flame_core emissive; its origin at the flame base, 0.5 up and 0.2 in front of the mount) with an
                 animation "flicker" (loop 1 s). Add an OmniLight3D at the flame.
  vine           vine.glb: root "vine" with children vine_1, vine_2, vine_3 (1, 2, 3 tiles long) all hanging from the
                 origin (at the TOP): show one. vine_stem, vine_leaf, vine_leaf_dark.
Tiles (1x1x1, origin at the centre, front face at Godot z = +0.5; carvings stand up to 0.04 proud of it):
  tile_stone_a   a dressed block, pits and a hairline crack; tile_stone_b two courses of masonry; tile_stone_c a
                 carved spiral-sun glyph. Materials tile_stone, tile_stone_light, tile_stone_dark, tile_groove (recolour
                 per level for themes).
  tile_moss      tile_stone with a moss cushion on top (up to 0.07 above the top) rolling over the front edge, drips
                 and leaves: tile_moss, tile_moss_dark, tile_leaf.
  tile_brick     the darker inner wall (small staggered bricks, deep mortar; front at -0.5, bricks 0.2 deep):
                 tile_brick, tile_brick_light, tile_mortar. Use it for the back wall behind the play plane.
  tile_platform  a wooden plank bridge 1 wide, 0.2 thick, top at +0.5 (the tile's top), 0.9 deep, rope lashings:
                 platform_wood, _wood_dark, _rope, _iron.
Backdrop (origin at the base centre, front towards the camera; put them behind the play plane, e.g. Godot z = -1):
  bg_pillar 1.2 wide, 4.1 tall (with moss); bg_statue a big made-up stone face 3.2 wide, 3.4 tall with faintly glowing
  eyes (bg_statue_glow); bg_arch a corbelled arch 3.2 wide, 3.2 tall (opening 1.6); bg_jungle_plant 1.7 tall, 2 wide
  (bg_plant_leaf, _leaf_dark, _stem).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, simple, reset, R90
from blastyard_bombers import Rig, merge, mirror, limb
from prism_models import new_obj, animate, export_anim, empty, edit
from hopline_models import TurnRig, ell, hemi
from mossfolk_models import lumpy, lathe_r, solid
from nightbite_characters import blob
from slipfloe_models import star
import humanoid as HU

FPS = 30
GAME = 1.5 / 1.7          # the game scales the explorer to about 1.5 tiles: tiles per model unit


def P(base, **kw):
    """A pose: base with some channels replaced (bone names carry dots, so pass them as **{...})."""
    d = dict(base)
    d.update(kw)
    return d


def clear_all():
    reset()
    HU.MATS.clear()
    for a in list(bpy.data.armatures):
        bpy.data.armatures.remove(a)


# ------------------------------------------------------------------ humanoid helpers

def cycle(frames, fn, step=2):
    """A looping HU.Anim keyed every `step` frames from fn(phase in [0, 1))."""
    return HU.Anim({i + 1: fn(i / frames) for i in range(0, frames + 1, step)}, loop=True)


def rot_c(v, deg):
    """Turns a character-space point (left, forward, up) about the vertical by deg (to the left)."""
    a = math.radians(deg)
    x, y = v[0], -v[1]                       # armature space (the model faces -Y)
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (x, -y) + tuple(v[2:])


def yawed(anim, deg):
    """The same action with the whole figure turned deg to its left: the root, the turn, every IK target and aim."""
    keys = {}
    for f, p in anim.keys.items():
        p = dict(anim.base, **p)
        q = dict(p)
        r = p.get("root", (0, 0, 0))
        q["root"] = rot_c(r, deg)
        t = p.get("turn", (0, 0, 0))
        q["turn"] = (t[0], t[1] + deg, t[2])
        for X, s in (("L", 1), ("R", -1)):
            if "ik_foot." + X in p:
                v = p["ik_foot." + X]
                q["ik_foot." + X] = rot_c(v[:3], deg) + (v[3], v[4] + deg * s)
            if "ik_hand." + X in p:
                q["ik_hand." + X] = rot_c(p["ik_hand." + X], deg)
            if "hand_dir." + X in p:
                v = p["hand_dir." + X]
                q["hand_dir." + X] = (v[0] + deg,) + tuple(v[1:])
        keys[f] = q
    pole = anim.arm_pole
    new_pole = None
    if pole is not None:
        new_pole = {}
        for X, s in (("L", 1), ("R", -1)):
            v = pole.get(X) if isinstance(pole, dict) else pole
            w = Vector((v[0] * s, v[1], v[2]))                      # armature space
            w = Matrix.Rotation(math.radians(deg), 3, "Z") @ w
            new_pole[X] = (w.x * s, w.y, w.z)
    return HU.Anim(keys, loop=anim.loop, hand_on=anim.hand_on, arm_pole=new_pole)


def export_humanoid(name, actions, sk, scale, yaw, attach=(), out=None):
    """HU.rig_export with the figure turned `yaw` degrees about Z (from facing -Y), plus bone-parented nodes:
    attach = [(node name, parts, bone, pivot)] (parts built in rest space, joined into one node)."""
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
    for nname, parts, bone, pivot in attach:
        o = join(parts, nname, pivot=pivot)
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy()
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
    # the rest-pose bounds (model units)
    MW = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Scale(scale, 4)
    zs = [(MW @ v.co) for v in mesh.data.vertices]
    print("exported %-10s %6d tris  height %.2f  x %.2f..%.2f  nodes: %s" % (
        name, K.tris(mesh), max(v.z for v in zs), min(v.x for v in zs), max(v.x for v in zs),
        ", ".join([arm.name, mesh.name] + [o.name for o in nodes])))
    print("   anims: " + ", ".join("%s %.2fs%s" % (k, v[0], " loop" if v[1] else "") for k, v in lengths.items()))
    clear_all()


def slim(material, ratio, bone=None):
    """Decimates the humanoid builder's dense parts of one material (and binding)."""
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and "bone" in o]:
        if o.data.materials[0] is not material or (bone and o["bone"] != bone):
            continue
        HU._select_only(o)
        m = o.modifiers.new("d", "DECIMATE")
        m.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.ops.object.shade_smooth()


def drop_bone_parts(bone):
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and o.get("bone") == bone]:
        bpy.data.objects.remove(o, do_unlink=True)


def hu_part(o, bone, smooth=True):
    """Tags a blastyard-built part (already with its material) for the humanoid binder."""
    o["bone"] = bone
    return o


# ------------------------------------------------------------------ the explorer

EXP_SCALE = 0.885
EXP_YAW = 62            # facing +X, turned 28 degrees towards the camera
ESK = HU.Skeleton(HU.proportions(sh_w=0.19, hip_w=0.1))
ESHAPE = {"chest": 1.12, "waist": 1.08, "hips": 1.08, "arms": 1.22, "legs": 1.18, "neck": 1.2, "hand": 1.2}
EHEAD = 1.34
EH = (0, -0.018, 1.715)          # head centre


def e_stand(w=0.12):
    return {"ik_foot.L": (w, 0.03, 0.09, 0, 10), "ik_foot.R": (-w, -0.03, 0.09, 0, 12), "ikw.L": 1.0, "ikw.R": 1.0}


def e_arms(br=0.0):
    return {"clavicle.L": (2, 0, 2 + 1.5 * br), "clavicle.R": (2, 0, 2 + 1.5 * br),
            "arm.L": (4, 0, 12), "forearm.L": (22 + 2 * br, 0, 0), "hand.L": (0, 0, -4),
            "arm.R": (10, 0, 12), "forearm.R": (34 - 2 * br, 0, 0), "hand.R": (0, 0, -6)}


E_STAND = P(e_stand(), **{"root": (0, 0, -0.03), "spine": (1, 0, 0), "chest": (-1, 0, 0), "head": (-2, 0, 0)},
            **e_arms())


def e_idle():
    def f(t):
        br = math.sin(2 * math.pi * t * 2)
        sway = math.sin(2 * math.pi * t)
        look = math.sin(2 * math.pi * t) ** 3
        p = P(E_STAND, **{"root": (0.01 * sway, 0, -0.03 - 0.006 * br), "hips": (0, 3 * sway, -2 * sway),
                          "spine": (1, -1 * sway, 0), "chest": (-1 + 1.5 * br, -2 * sway + 5 * look, 0),
                          "neck": (0, 14 * look, 0), "head": (-2 - 2 * br, 20 * look, 3 * look)})
        p.update(e_arms(br))
        return p
    return cycle(72, f, 3)


WALK_FRAMES, WALK_STRIDE = 14, 3.0


def e_walk():
    """A quick run (the hero moves fast): WALK_STRIDE rig metres per cycle."""
    return HU.gait(ESK, WALK_FRAMES, WALK_STRIDE, 0.38, lift=0.34, lift_at=0.45, strike=8, push=42, bob=-0.035,
                   drop=-0.07, lean=12, width=0.11, arm_swing=46, arm_out=12, elbow=72, elbow_swing=20,
                   pelvis_yaw=10, pelvis_roll=4, shoulder_yaw=12, reach=0.46, sway=0.012, step=1,
                   base={"head": (-6, 0, 0), "hand.R": (0, 0, -6), "spine": (4, 0, 0)})


def air_legs(tuck=0.0, kick=0.0):
    """FK legs in the air: tuck 0..1 pulls the knees up; kick swings one leg forward and the other back."""
    return {"ikw.L": 0.0, "ikw.R": 0.0,
            "thigh.L": (25 + 55 * tuck + 18 * kick, 0, 5), "shin.L": (30 + 80 * tuck, 0, 0), "foot.L": (-10, 0, 0),
            "thigh.R": (-5 + 45 * tuck - 18 * kick, 0, 5), "shin.R": (45 + 70 * tuck, 0, 0), "foot.R": (-20, 0, 0)}


def e_jump():
    crouch = P(E_STAND, **{"root": (0, 0.02, -0.2), "hips": (18, 0, 0), "spine": (10, 0, 0), "chest": (6, 0, 0),
                           "head": (-16, 0, 0), "ik_foot.L": (0.12, 0.06, 0.09, 0, 10),
                           "ik_foot.R": (-0.12, -0.06, 0.09, 0, 12), "arm.L": (-30, 0, 16), "arm.R": (-26, 0, 16),
                           "forearm.L": (30, 0, 0), "forearm.R": (40, 0, 0)})
    push = P(E_STAND, **{"root": (0, 0.04, 0.06), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (6, 0, 4), "shin.L": (8, 0, 0),
                         "thigh.R": (-12, 0, 4), "shin.R": (16, 0, 0), "foot.L": (-45, 0, 0), "foot.R": (-50, 0, 0),
                         "spine": (-4, 0, 0), "chest": (-6, 0, 0), "head": (-10, 0, 0),
                         "arm.L": (150, 0, 24), "forearm.L": (20, 0, 0), "arm.R": (120, 0, 20), "forearm.R": (40, 0, 0)})
    up = P(push, **air_legs(0.9, 0.3), **{"root": (0, 0, 0.1), "spine": (8, 0, 0), "chest": (4, 0, 0),
                                          "head": (-12, 0, 0), "arm.L": (160, 0, 30), "forearm.L": (30, 0, 0),
                                          "arm.R": (110, 0, 28), "forearm.R": (60, 0, 0)})
    return HU.Anim({1: E_STAND, 4: crouch, 7: push, 11: up, 14: P(up, **{"arm.L": (155, 0, 34)})})


def e_fall():
    def f(t):
        a = 2 * math.pi * t
        p = P(E_STAND, **air_legs(0.25 + 0.1 * math.sin(a), 0.6 * math.sin(a)))
        p.update({"root": (0, 0, 0.04), "spine": (-4, 0, 0), "chest": (-6, 0, 0), "head": (-14, 0, 0),
                  "arm.L": (135 + 20 * math.sin(a), 0, 55), "forearm.L": (30 + 15 * math.cos(a), 0, 0),
                  "arm.R": (125 - 20 * math.sin(a), 0, 50), "forearm.R": (40 - 15 * math.cos(a), 0, 0),
                  "hand.L": (0, 0, 20), "hand.R": (0, 0, 20)})
        return p
    return cycle(12, f, 1)


# the climb: written facing the ladder (forward), then turned so the explorer shows his back to the camera
LADDER_FWD = 0.3                 # the rungs' plane in front of the hips (rig metres)
CLIMB_FRAMES, CLIMB_STEP = 16, 0.78
CLIMB_TURN = 180 - EXP_YAW       # from the export yaw to facing +Y (away from the camera)


def e_climb():
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


CRAWL_FRAMES, CRAWL_STRIDE = 16, 0.7


def e_crawl():
    """On hands and knees, a diagonal gait (left hand with the right knee): CRAWL_STRIDE rig metres per cycle."""
    S = CRAWL_STRIDE
    duty = 0.62

    def limb(ph, f0, lift):
        if ph < duty:
            u = ph / duty
            return f0 + S * duty * (0.5 - u), 0.0
        v = (ph - duty) / (1 - duty)
        return f0 - S * duty * 0.5 + S * duty * HU.smoothstep(0, 1, v), math.sin(math.pi * v) * lift

    def f(t):
        p = {}
        for X, s, off in (("L", 1, 0.0), ("R", -1, 0.5)):
            fh, lh = limb((t + off) % 1.0, 0.5, 0.09)
            p["ik_hand." + X] = (0.15 * s, fh, 0.11 + lh)
            p["ikh." + X] = 1.0
            p["hand_dir." + X] = (8 * s, -8, 90)
            p["hdw." + X] = 0.85
            fk, lk = limb((t + off + 0.5) % 1.0, -0.3, 0.07)
            p["ik_foot." + X] = (0.12 * s, fk, 0.15 + lk, -95, 0)
            p["ikw." + X] = 1.0
        b = math.sin(4 * math.pi * t)
        sw = math.sin(2 * math.pi * t)
        p.update({"root": (0.02 * sw, 0.06, -0.45 + 0.012 * b), "hips": (72, 6 * sw, 4 * sw), "spine": (8, -4 * sw, 0),
                  "chest": (2, -4 * sw, -3 * sw), "neck": (-38, 3 * sw, 0), "head": (-36, 5 * sw, 0)})
        return p
    a = cycle(CRAWL_FRAMES, f, 1)
    a.arm_pole = {"L": (0.6, 1.0, 0.2), "R": (0.6, 1.0, 0.2)}
    return a


AIM = rot_c((0.0, 0.62), 90 - EXP_YAW)    # 0.62 rig metres along world +X from the shoulder, character space


def aim_pose(recoil=0.0, lift=0.0):
    sh = ESK.head("arm.R")
    tgt = (sh.x + AIM[0] * (1 - recoil * 0.12), -sh.y + AIM[1] * (1 - recoil * 0.12), 1.34 + lift + recoil * 0.05)
    tw = 90 - EXP_YAW
    return P(E_STAND, **{"ik_hand.R": tgt, "ikh.R": 1.0, "hand_dir.R": (tw, 4 + 26 * recoil, 0), "hdw.R": 1.0,
                         "spine": (0, tw * 0.3, 0), "chest": (-2 - 4 * recoil, tw * 0.4, 0), "neck": (0, tw * 0.1, 0),
                         "head": (-2, tw * 0.2, 0), "clavicle.R": (10, 0, 4),
                         "arm.L": (-10, 0, 14), "forearm.L": (30, 0, 0),
                         "root": (0, -0.02 * recoil, -0.04), "ik_foot.L": (0.12, 0.1, 0.09, 0, 10),
                         "ik_foot.R": (-0.12, -0.1, 0.09, 0, 14)})


def e_shoot():
    """0.3 s: the pistol snaps up to point along +X at chest height, fires at frame 4 (0.1 s), kicks, holds the aim."""
    return HU.Anim({1: E_STAND, 3: aim_pose(0.0, 0.03), 4: aim_pose(0.0), 5: aim_pose(1.0), 7: aim_pose(0.25),
                    10: aim_pose(0.0)}, arm_pole={"L": (0.35, 1.0, -0.4), "R": (0.6, 0.2, -1.0)})


def e_plant():
    """0.5 s: squats, both hands set the dynamite on the floor in front (at 0.27 s), stands back up."""
    down = P(E_STAND, **{"root": (0, -0.02, -0.46), "hips": (34, 0, 0), "spine": (18, 0, 0), "chest": (10, 0, 0),
                         "neck": (-14, 0, 0), "head": (-24, 0, 0),
                         "ik_foot.L": (0.14, 0.08, 0.09, 0, 14), "ik_foot.R": (-0.14, -0.14, 0.12, -30, 16),
                         "ik_hand.L": (0.07, 0.5, 0.1), "ik_hand.R": (-0.07, 0.5, 0.12), "ikh.L": 1.0, "ikh.R": 1.0,
                         "hand_dir.L": (-10, -60, 90), "hand_dir.R": (10, -60, 90), "hdw.L": 1.0, "hdw.R": 1.0})
    place = P(down, **{"ik_hand.L": (0.07, 0.5, 0.06), "ik_hand.R": (-0.07, 0.5, 0.08)})
    off = P(down, **{"ik_hand.L": (0.1, 0.36, 0.3), "ik_hand.R": (-0.1, 0.36, 0.32), "root": (0, -0.03, -0.36),
                     "hand_dir.L": (-10, -20, 90), "hand_dir.R": (10, -20, 90)})
    up = P(E_STAND, **{"ikh.L": 0.0, "ikh.R": 0.0, "hdw.L": 0.0, "hdw.R": 0.0})
    for k in (down, place, off):
        k.setdefault("ikh.L", 1.0)
    return HU.Anim({1: P(up, **{"ikh.L": 0.0, "ikh.R": 0.0}), 5: down, 9: place, 11: place, 13: off, 16: up},
                   arm_pole={"L": (0.6, 0.6, -0.8), "R": (0.6, 0.6, -0.8)})


E_LIE = {"ikw.L": 0.0, "ikw.R": 0.0, "turn": (-90, 0, 0), "root": (0, 0, 0.13), "hips": (0, 0, 0), "spine": (-2, 0, 0),
         "chest": (-2, 0, 0), "neck": (4, 0, 0), "head": (6, 20, 0), "arm.L": (20, 0, 70), "forearm.L": (40, 0, 0),
         "arm.R": (30, 0, 64), "forearm.R": (30, 0, 0), "thigh.L": (22, 0, 12), "shin.L": (40, 0, 0),
         "thigh.R": (8, 0, 14), "shin.R": (14, 0, 0), "foot.L": (-30, 0, 0), "foot.R": (-35, 0, 0)}


def e_die():
    """1.3 s comic flop: a jolt (hands up, eyes to the sky), a wobble on his heels, a stiff fall backwards, a bounce,
    lies spread out on his back (holds)."""
    jolt = P(E_STAND, **{"root": (0, 0, 0.1), "ikw.L": 0.0, "ikw.R": 0.0, "thigh.L": (8, 0, 8), "shin.L": (10, 0, 0),
                         "thigh.R": (-6, 0, 8), "shin.R": (12, 0, 0), "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0),
                         "spine": (-8, 0, 0), "chest": (-10, 0, 0), "head": (-20, 0, 0),
                         "arm.L": (160, 0, 40), "forearm.L": (10, 0, 0), "arm.R": (160, 0, 36), "forearm.R": (14, 0, 0),
                         "hand.L": (0, 0, 30), "hand.R": (0, 0, 30)})
    wob1 = P(E_STAND, **{"turn": (-6, 0, 8), "root": (0, -0.02, -0.02), "spine": (-4, 10, 4), "head": (-8, 20, 10),
                         "arm.L": (70, 0, 80), "forearm.L": (40, 0, 0), "arm.R": (90, 0, 70), "forearm.R": (30, 0, 0)})
    wob2 = P(wob1, **{"turn": (-10, 0, -8), "spine": (-4, -10, -4), "head": (-10, -20, -10),
                      "arm.L": (100, 0, 70), "arm.R": (60, 0, 80)})
    tip = P(E_STAND, **{"turn": (-45, 0, 0), "root": (0, 0.3, 0.06), "ikw.L": 0.0, "ikw.R": 0.0,
                        "thigh.L": (14, 0, 6), "shin.L": (4, 0, 0), "thigh.R": (6, 0, 6), "shin.R": (4, 0, 0),
                        "foot.L": (-10, 0, 0), "foot.R": (-10, 0, 0), "spine": (6, 0, 0), "head": (14, 0, 0),
                        "arm.L": (100, 0, 50), "forearm.L": (10, 0, 0), "arm.R": (110, 0, 44), "forearm.R": (10, 0, 0)})
    flat = P(E_LIE, **{"root": (0, 0.6, 0.3), "thigh.L": (50, 0, 10), "shin.L": (10, 0, 0), "thigh.R": (40, 0, 12),
                       "shin.R": (8, 0, 0), "arm.L": (70, 0, 60), "arm.R": (80, 0, 50), "head": (-6, 0, 0)})
    bounce = P(E_LIE, **{"turn": (-84, 0, 0), "root": (0, 0.64, 0.36), "thigh.L": (70, 0, 12), "shin.L": (20, 0, 0),
                         "thigh.R": (60, 0, 14), "shin.R": (20, 0, 0), "head": (-10, 0, 0), "arm.L": (60, 0, 80),
                         "arm.R": (60, 0, 76)})
    rest = P(E_LIE, **{"root": (0, 0.66, 0.29), "head": (4, 34, 6)})
    return HU.Anim({1: E_STAND, 4: jolt, 9: wob1, 13: wob2, 17: tip, 22: flat, 26: bounce, 31: P(rest, **{"head": (0, 10, 0)}),
                    35: rest, 40: rest})


def e_cheer():
    def f(t):
        a = 2 * math.pi * t
        hop = max(0.0, math.sin(a * 2)) ** 1.5
        pump = math.sin(a)
        p = P(e_stand(0.13), **{
            "root": (0, 0, -0.05 + 0.1 * hop - 0.05 * max(0.0, -math.sin(a * 2))),
            "spine": (-4, 5 * pump, 0), "chest": (-6, 6 * pump, 0), "neck": (-6, 0, 0), "head": (-14, -8 * pump, 0),
            "clavicle.L": (0, 0, 18 + 8 * max(0, pump)), "clavicle.R": (0, 0, 14),
            "arm.L": (155 + 18 * max(0, pump), 0, 30), "forearm.L": (20 + 60 * max(0, -pump), 0, 0),
            "arm.R": (120 + 30 * max(0, -pump), 0, 40), "forearm.R": (40 + 30 * max(0, pump), 0, 0),
            "hand.L": (0, 0, 10), "hand.R": (0, 0, 10)})
        for X in "LR":
            v = p["ik_foot." + X]
            p["ik_foot." + X] = (v[0], v[1], v[2] + 0.09 * hop, -10 * hop, v[4])
        return p
    return cycle(30, f, 1)


def explorer_actions():
    return {"idle": e_idle(), "walk": e_walk(), "jump": e_jump(), "fall": e_fall(), "climb": e_climb(),
            "crawl": e_crawl(), "shoot": e_shoot(), "plant": e_plant(), "die": e_die(), "cheer": e_cheer()}


def explorer():
    sk = ESK
    sh = ESHAPE
    skin = mat("explorer_skin", (0.9, 0.62, 0.45), 0.5)
    cheek = mat("explorer_cheek", (0.9, 0.48, 0.38), 0.55)
    white = mat("explorer_eye_white", (0.96, 0.95, 0.92), 0.3)
    iris = mat("explorer_iris", (0.16, 0.1, 0.05), 0.2)
    hair = mat("explorer_hair", (0.34, 0.2, 0.1), 0.6, coat=0.1)
    lips = mat("explorer_lips", (0.62, 0.32, 0.26), 0.5)
    shirt = mat("explorer_shirt", (0.8, 0.66, 0.4), 0.8)
    shirt_dk = mat("explorer_shirt_dark", (0.62, 0.48, 0.27), 0.8)
    trousers = mat("explorer_trousers", (0.3, 0.33, 0.18), 0.85)
    boots = mat("explorer_boots", (0.3, 0.16, 0.07), 0.4, coat=0.35)
    sole = mat("explorer_sole", (0.08, 0.05, 0.03), 0.7)
    leather = mat("explorer_leather", (0.45, 0.24, 0.1), 0.45, coat=0.25)
    brass = mat("explorer_brass", (0.95, 0.7, 0.3), 0.3, 0.9)
    helmet = mat("explorer_helmet", (0.93, 0.86, 0.68), 0.6, coat=0.15)
    band = mat("explorer_helmet_band", (0.42, 0.24, 0.12), 0.6)
    scarf = mat("explorer_scarf", (0.85, 0.18, 0.1), 0.75)
    gun = mat("explorer_pistol", (0.16, 0.17, 0.2), 0.3, 0.8)
    grip_m = mat("explorer_pistol_grip", (0.4, 0.2, 0.08), 0.5, coat=0.3)

    HU.human_body(sk, skin, shirt, trousers, white, iris, shoes=boots, sole=sole, glove=skin, sleeves="short",
                  hands="relaxed", shape=sh, head=False, shoe_height=0.34)
    slim(boots, 0.6)
    slim(trousers, 0.6, bone="~body")
    slim(shirt, 0.55, bone="~body")
    for X in "LR":
        slim(trousers, 0.7, bone="~leg." + X)
        slim(skin, 0.6, bone="hand." + X)
    # the right hand grips the pistol
    drop_bone_parts("hand.R")
    HU.hand_parts(sk, "R", skin, "grip", sh["hand"])
    slim(skin, 0.6, bone="hand.R")
    # rolled sleeves above the elbow
    for X, s in (("L", 1), ("R", -1)):
        HU.tube(HU.arm_path(sk, X, 0.01, 0.0, 0.44, shape=sh["arms"]), "~arm." + X, shirt, 18, 0.016, lateral=(s, 0, 0),
                caps=(True, False))
        HU.tube(HU.arm_path(sk, X, 0.024, 0.34, 0.45, shape=sh["arms"]), "~arm." + X, shirt_dk, 14, 0.02,
                lateral=(s, 0, 0))
    # the head: big and friendly, rosy cheeks, brown hair under the helmet, a confident brow
    k = EHEAD
    HU.head_detailed(skin, white, iris, center=EH, hair=None, size=k, brow=hair, lips=lips)
    cx, cy, cz = EH
    HU.sphere(0.104 * k, (0, cy + 0.035, cz + 0.0), "head", hair, (0.95, 0.95, 0.9), 20, 10)      # hair at the back
    for s in (-1, 1):
        HU.sphere(0.02 * k, (0.058 * k * s, cy - 0.07 * k, cz - 0.03 * k), "head", cheek, (1.0, 0.6, 0.8), 10, 6)
        HU.sphere(0.02 * k, (0.09 * k * s, cy - 0.005 * k, cz - 0.0 * k), "head", hair, (0.5, 0.9, 1.4), 10, 6)   # sideburns
    # a stubbly chin line (darker skin), to read as a rugged adventurer
    HU.sphere(0.05 * k, (0, cy - 0.052 * k, cz - 0.07 * k), "head", mat("explorer_stubble", (0.62, 0.42, 0.3), 0.7),
              (1.2, 0.7, 0.55), 14, 8)
    # the pith helmet: a dome, a band, a wide brim sloping down front and back, a vent knob
    hz = cz + 0.04 * k
    n_before = set(bpy.context.scene.objects)
    dome = HU.sphere(0.122 * k, (0, cy + 0.01, hz), "head", helmet, (0.98, 1.08, 0.9), 26, 14)
    edit(dome, lambda bm: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < hz - 0.005], context="VERTS"))
    HU.body_loft([(hz - 0.002, 0.121 * k, 0.131 * k, cy + 0.01), (hz + 0.03 * k, 0.118 * k, 0.128 * k, cy + 0.01)],
                 "head", band, 26, 0)
    HU.sphere(0.018 * k, (0, cy + 0.01, hz + 0.106 * k), "head", helmet, (1, 1, 0.55), 12, 6)
    HU.sphere(0.024 * k, (0, cy + 0.01, hz + 0.1 * k), "head", band, (1, 1, 0.3), 12, 6)
    bm = bmesh.new()
    n = 32
    rows = []
    for ring, (rx, ry, dz) in enumerate(((0.118, 0.128, 0.0), (0.17, 0.2, -0.028), (0.2, 0.235, -0.05))):
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            fb = abs(math.sin(a))              # the brim droops more at the front and back
            row.append(bm.verts.new((rx * k * math.cos(a), cy + 0.01 + ry * k * math.sin(a),
                                     hz + dz * k * (0.5 + 0.8 * fb) + 0.004)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    brim = HU._mesh_object(bm, "brim")
    solid(brim, 0.012)
    HU.tag(brim, "head", helmet)
    tilt = Matrix.Translation(Vector(EH)) @ Matrix.Rotation(math.radians(-9), 4, "X") @ Matrix.Translation(-Vector(EH))
    for o in set(bpy.context.scene.objects) - n_before:
        o.data.transform(tilt)
    # the neckerchief: a knotted roll and a triangle at the front
    tube_pts = [(0.0, -0.085, 1.475, 0.026), (0.08, -0.05, 1.485, 0.028), (0.095, 0.02, 1.495, 0.028),
                (0.05, 0.08, 1.505, 0.026), (-0.02, 0.085, 1.505, 0.026), (-0.09, 0.03, 1.495, 0.028),
                (-0.08, -0.05, 1.485, 0.028), (0.0, -0.088, 1.475, 0.026)]
    HU.tube(tube_pts, "~body", scarf, 10, 0.03)
    HU.sphere(0.032, (0.03, -0.105, 1.465), "~body", scarf, (1.2, 0.7, 1.0), 12, 7)
    HU.tube([(0.03, -0.11, 1.45, 0.03), (0.04, -0.125, 1.39, 0.02), (0.045, -0.128, 1.34, 0.006)], "~body", scarf, 8,
            0.02, ell=(1.9, 0.4))
    # shirt: an open collar, two chest pockets with flaps and buttons, a placket
    ck = sh["chest"]
    for s in (-1, 1):
        HU.box((0.075, 0.016, 0.07), (0.075 * s, -0.112 * ck, 1.3), "~body", shirt_dk, rot=(-0.12, 0, 0), bevel=0.008)
        HU.box((0.082, 0.02, 0.026), (0.075 * s, -0.118 * ck, 1.34), "~body", shirt_dk, rot=(-0.12, 0, 0), bevel=0.008)
        HU.sphere(0.008, (0.075 * s, -0.13 * ck, 1.335), "~body", brass, (1, 0.6, 1), 8, 5)
    for z in (1.18, 1.25):
        HU.sphere(0.008, (0.0, -0.115 * sh["waist"] - 0.004, z), "~body", brass, (1, 0.6, 1), 8, 5)
    HU.box((0.022, 0.012, 0.3), (0.0, -0.108 * sh["waist"], 1.24), "~body", shirt_dk, rot=(-0.1, 0, 0), bevel=0.005)
    # the belt, a brass buckle; the satchel strap from the left shoulder to the satchel on the right hip
    HU.body_loft([(z, rx + 0.012, ry + 0.012, cy_, sq) for z, rx, ry, cy_, sq in HU.torso_rings(0.98, 1.05, 0.0, sh)],
                 "~body", leather, 26, 0)
    HU.box((0.06, 0.02, 0.05), (0.0, -0.1 * sh["hips"] - 0.02, 1.01), "~body", brass, bevel=0.006)
    def surf(a, z, grow=0.016):
        rings = HU.torso_rings(0.8, 1.51, grow, sh)
        for r0, r1 in zip(rings, rings[1:]):
            if r0[0] <= z <= r1[0]:
                u = (z - r0[0]) / (r1[0] - r0[0])
                rx, ry, cy_, sq = [r0[i] + (r1[i] - r0[i]) * u for i in (1, 2, 3, 4)]
                c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
                e = 2.0 / sq
                return (rx * math.copysign(abs(c) ** e, c), cy_ + ry * math.copysign(abs(s_) ** e, s_), z, 0.012)
        raise ValueError(z)
    front = [surf(-60 - 105 * u, 1.43 - 0.45 * u) for u in (0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0)]
    back = [surf(60 + 115 * u, 1.43 - 0.43 * u) for u in (0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0)]
    top = (0.13, 0.0, 1.475, 0.012)
    HU.tube(list(reversed(back)) + [top] + front, "~body", leather, 6, 0.02, ell=(1.8, 0.5))
    # jodhpurs: the breeches flare over the thighs
    for X, s in (("L", 1), ("R", -1)):
        pts = HU.leg_path(sk, X, 0.0, t1=0.55, shape=sh["legs"])
        fl = [0.012, 0.026, 0.046, 0.042, 0.02, 0.008]
        pts = [(x + s * f * 0.4, y, z, r + f) for (x, y, z, r), f in zip(pts, fl)]
        HU.tube(pts, "~leg." + X, trousers, 18, 0.016, lateral=(s, 0, 0))
    # the satchel (rigid on the hips): a leather bag with a flap and a brass clasp, on the right hip
    sx = -0.215 * sh["hips"]
    HU.box((0.075, 0.2, 0.17), (sx, -0.01, 0.9), "hips", leather, bevel=0.025)
    HU.box((0.085, 0.21, 0.08), (sx - 0.006, -0.01, 0.955), "hips", mat("explorer_leather_dark", (0.3, 0.15, 0.06), 0.5),
           bevel=0.02)
    HU.box((0.02, 0.035, 0.04), (sx - 0.05, -0.01, 0.925), "hips", brass, bevel=0.006)
    # boot cuffs and laces
    for X, s in (("L", 1), ("R", -1)):
        x = sk.head("foot." + X).x
        HU.body_loft([(0.31, 0.058, 0.068, 0.006), (0.36, 0.062, 0.072, 0.006)], "~foot." + X, leather, 18, 0, x0=x)
        for z in (0.16, 0.21, 0.26):
            HU.box((0.05, 0.012, 0.01), (x, -0.058, z), "~foot." + X, sole, bevel=0.003)
    # the pistol, in the right hand's rest frame: grip along the hand's local +Z, barrel along its length (+Y)
    M = HU.bone_frame(sk, "hand.R")
    m = -1
    k2 = 1.25
    parts = [box((0.028 * k2, 0.036 * k2, 0.075 * k2), (m * 0.02, 0.088, -0.005), grip_m, rot=(0.25, 0, 0), bevel=0.008),
             box((0.03 * k2, 0.17 * k2, 0.04 * k2), (m * 0.02, 0.12, 0.052), gun, bevel=0.008),
             cyl(0.013 * k2, 0.08, (m * 0.02, 0.24, 0.058), gun, rot=(R90, 0, 0), verts=10),
             box((0.012, 0.02, 0.02), (m * 0.02, 0.07, 0.085), gun, bevel=0.004),
             torus(0.018, 0.005, (m * 0.02, 0.1, 0.012), gun, rot=(0, R90, 0), verts=12, minor=4)]
    for o in parts:
        o.matrix_world = M @ o.matrix_world
        K.select(o)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    muzzle = M @ Vector((m * 0.02, 0.28, 0.058))
    export_humanoid("explorer", explorer_actions(), sk, EXP_SCALE, EXP_YAW,
                    attach=[("pistol", parts, "hand.R", tuple(M.translation))])
    print("   walk: %.2f tiles per %d-frame cycle at game scale (%.2f tiles/s at speed_scale 1)" % (
        WALK_STRIDE * EXP_SCALE * GAME, WALK_FRAMES, WALK_STRIDE * EXP_SCALE * GAME * FPS / WALK_FRAMES))
    print("   crawl: %.2f tiles per cycle (%.2f tiles/s)" % (CRAWL_STRIDE * EXP_SCALE * GAME,
                                                          CRAWL_STRIDE * EXP_SCALE * GAME * FPS / CRAWL_FRAMES))
    print("   climb: %.2f tiles per cycle (%.2f tiles/s)" % (CLIMB_STEP * EXP_SCALE * GAME,
                                                          CLIMB_STEP * EXP_SCALE * GAME * FPS / CLIMB_FRAMES))


# ------------------------------------------------------------------ enemies on the humanoid rig (rigid parts)

ENEMY_YAW = 75          # facing +X, turned 15 degrees towards the camera


def on(bone, *objs):
    """Binds blastyard-built parts rigidly to a humanoid bone."""
    for o in K.flatten(objs):
        o["bone"] = bone
    return objs


def along(sk, b, t, off=(0, 0, 0)):
    return HU._along(sk, b, t, off)


def taper_box(x0, y0, x1, y1, z0, z1, material, cy=0.0, bevel=0.03, cz=0.0):
    """A box from half sizes (x0, y0) at z0 to (x1, y1) at z1 (a tapered torso or block)."""
    bm = bmesh.new()
    vs = []
    for z, hx, hy in ((z0, x0, y0), (z1, x1, y1)):
        vs.append([bm.verts.new((sx * hx, cy + sy * hy, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    a, b = vs
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    o = new_obj("tbox", bm, material, smooth=0)
    return K.finish(o, material, bevel, 3, smooth=35)


_uid = [0]


def gear(r, depth, loc, material, teeth=12, rot=(0, 0, 0), tooth=None):
    """A chunky cog: a disc with square teeth, axis along Z (rotate it with rot)."""
    t = tooth or r * 0.28
    parts = [cyl(r, depth, (0, 0, 0), material, verts=24, bevel=0.006)]
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        parts.append(box((t, t * 0.9, depth * 0.9), (math.cos(a) * (r + t * 0.35), math.sin(a) * (r + t * 0.35), 0),
                         material, rot=(0, 0, a), bevel=0.004))
    _uid[0] += 1
    o = join(parts, "gear_%d" % _uid[0])
    o.data.transform(Matrix.Translation(Vector(loc)) @ mathutils_euler(rot))
    return o


def mathutils_euler(rot):
    from mathutils import Euler
    return Euler(rot).to_matrix().to_4x4()


# ---- the automaton: a clockwork temple guardian of carved stone and bronze

ASK = HU.Skeleton(HU.proportions(sh_w=0.24, hip_w=0.11))
AUTO_SCALE = 0.855


def automaton():
    sk = ASK
    stone = mat("automaton_stone", (0.66, 0.58, 0.46), 0.85)
    dark = mat("automaton_stone_dark", (0.36, 0.32, 0.28), 0.9)
    bronze = mat("automaton_bronze", (0.82, 0.52, 0.22), 0.32, 0.9)
    verd = mat("automaton_verdigris", (0.28, 0.6, 0.5), 0.6, 0.3)
    glow = mat("automaton_glow", (0.35, 0.95, 1.0), 0.3, emit=6.0)
    moss = mat("automaton_moss", (0.3, 0.5, 0.16), 0.9)
    # hips: a bronze pelvis drum and a skirt of stone plates
    on("hips", cyl(0.15, 0.12, (0, 0.0, 0.95), bronze, verts=20, bevel=0.01, scale=(1.15, 0.9, 1)))
    for a in (-90, -50, -130, 0, 180):
        r = math.radians(a)
        x, y = math.cos(r) * 0.17, math.sin(r) * 0.13
        on("hips", box((0.1, 0.035, 0.17), (x, y, 0.86), stone, rot=(0.12 * -math.sin(r), 0.12 * math.cos(r), r + R90),
                       bevel=0.012))
    # waist: a turning cog
    on("spine", gear(0.12, 0.1, (0, 0, 1.1), bronze, 12))
    on("spine", cyl(0.09, 0.2, (0, 0, 1.12), dark, verts=16))
    # chest: a tapered stone block, a bronze plate with the glowing core, rivets, a wind-up key at the back
    on("chest", taper_box(0.17, 0.12, 0.27, 0.16, 1.17, 1.5, stone, bevel=0.04))
    on("chest", taper_box(0.13, 0.02, 0.17, 0.02, 1.22, 1.44, bronze, cy=-0.15, bevel=0.012))
    on("chest", ico(0.05, (0, -0.175, 1.33), glow, sub=2), torus(0.058, 0.012, (0, -0.172, 1.33), bronze, rot=(R90, 0, 0)))
    for x in (-0.12, 0.12):
        for z in (1.25, 1.41):
            on("chest", sphere(0.014, (x, -0.172, z), bronze, segs=8, rings=5))
    for i in range(3):   # carved grooves on the chest sides
        on("chest", box((0.3 + i * 0.03, 0.3, 0.012), (0, 0.0, 1.21 + i * 0.1), dark, bevel=0.004))
    on("chest", rod((0, 0.14, 1.36), (0, 0.29, 1.36), 0.02, bronze, verts=10))
    for s in (-1, 1):
        o = torus(0.05, 0.014, (0, 0.33, 1.36 + 0.05 * s), bronze, rot=(0, R90, 0), verts=16, minor=6, scale=(1, 1, 0.8))
        on("chest", o)
    on("chest", sphere(0.022, (0, 0.3, 1.36), bronze, segs=10, rings=6))
    # shoulders: stone pauldrons with moss, bronze ball joints
    for X, s in (("L", 1), ("R", -1)):
        c = sk.head("arm." + X)
        on("clavicle." + X, sphere(0.12, (c.x + 0.02 * s, 0.0, c.z + 0.03), stone, scale=(1.0, 1.0, 0.8), segs=16, rings=10))
        on("clavicle." + X, lumpy(0.05, (c.x + 0.03 * s, -0.02, c.z + 0.11), moss, 7 + s, 0.25, scale=(1.3, 1.1, 0.5)))
        on("clavicle." + X, torus(0.1, 0.014, (c.x + 0.02 * s, 0.0, c.z - 0.0), bronze, verts=20, scale=(1, 1, 1)))
        on("arm." + X, sphere(0.07, tuple(c), bronze, segs=14, rings=8))
        on("arm." + X, rod(along(sk, "arm." + X, 0.15), along(sk, "arm." + X, 0.95), 0.06, dark, r2=0.055, verts=12))
        on("arm." + X, torus(0.064, 0.012, tuple(along(sk, "arm." + X, 0.55)), bronze, verts=16))
        on("forearm." + X, sphere(0.06, tuple(sk.head("forearm." + X)), bronze, segs=12, rings=8))
        g = rod(along(sk, "forearm." + X, 0.12), along(sk, "forearm." + X, 0.98), 0.07, stone, r2=0.088, verts=12)
        on("forearm." + X, K.finish(g, stone, 0.01, 2, 40))
        a, b = sk.head("forearm." + X), sk.tail("forearm." + X)
        d = (b - a).normalized()
        q = Vector((0, 0, 1)).rotation_difference(d).to_euler()
        on("forearm." + X, cyl(0.093, 0.04, tuple(along(sk, "forearm." + X, 0.85)), bronze, rot=q, verts=16, bevel=0.006))
        on("forearm." + X, cyl(0.078, 0.03, tuple(along(sk, "forearm." + X, 0.3)), bronze, rot=q, verts=16, bevel=0.006))
        # a blocky fist
        h = along(sk, "hand." + X, 0.55)
        on("hand." + X, box((0.1, 0.11, 0.12), tuple(h), stone, rot=q, bevel=0.02))
        for k in range(3):
            on("hand." + X, box((0.028, 0.03, 0.03), tuple(h + Vector((0.035 * s * 0, -0.055, -0.04 + 0.04 * k))),
                                 bronze, bevel=0.006))
        # legs: bronze piston thighs, stone greaves, block boots
        on("thigh." + X, sphere(0.07, tuple(sk.head("thigh." + X)), bronze, segs=12, rings=8))
        on("thigh." + X, rod(along(sk, "thigh." + X, 0.05), along(sk, "thigh." + X, 0.95), 0.05, bronze, verts=12))
        on("thigh." + X, rod(along(sk, "thigh." + X, 0.15), along(sk, "thigh." + X, 0.7), 0.075, dark, r2=0.06, verts=12))
        on("shin." + X, sphere(0.065, tuple(sk.head("shin." + X)), bronze, segs=12, rings=8))
        on("shin." + X, taper_box(0.07, 0.07, 0.085, 0.085, 0.14, 0.44, stone, cy=0.0, bevel=0.02))
        o = K.active()
        o.data.transform(Matrix.Translation((sk.head("shin." + X).x, -0.01, 0)))
        on("shin." + X, box((0.19, 0.2, 0.03), (sk.head("shin." + X).x, -0.01, 0.43), bronze, bevel=0.01))
        f = sk.head("foot." + X)
        on("foot." + X, box((0.16, 0.3, 0.12), (f.x, -0.06, 0.06), stone, bevel=0.03))
        on("foot." + X, box((0.17, 0.08, 0.05), (f.x, -0.19, 0.03), bronze, bevel=0.012))
    # neck and head: a stone helm-head with a glowing visor slit, a bronze crest and cheek plates
    on("neck", rod((0, 0, 1.44), (0, -0.01, 1.58), 0.055, bronze, verts=12))
    on("neck", torus(0.06, 0.012, (0, -0.005, 1.51), dark, verts=14))
    hc = Vector((0, -0.02, 1.66))
    on("head", taper_box(0.1, 0.11, 0.115, 0.12, 1.55, 1.78, stone, cy=hc.y, bevel=0.035))
    on("head", box((0.19, 0.03, 0.055), (0, hc.y - 0.12, 1.665), dark, bevel=0.012))
    for s in (-1, 1):
        on("head", box((0.06, 0.02, 0.034), (0.045 * s, hc.y - 0.135, 1.665), glow, bevel=0.01))
        on("head", cyl(0.035, 0.03, (0.12 * s, hc.y, 1.66), bronze, rot=(0, R90, 0), verts=14, bevel=0.005))
        on("head", box((0.02, 0.07, 0.1), (0.1 * s, hc.y - 0.07, 1.6), bronze, bevel=0.008))
    on("head", box((0.16, 0.03, 0.05), (0, hc.y - 0.125, 1.585), bronze, bevel=0.01))
    for k in range(4):
        on("head", box((0.012, 0.01, 0.03), (-0.045 + 0.03 * k, hc.y - 0.142, 1.585), dark, bevel=0.003))
    crest = prism([(-0.13, 0.0), (0.12, 0.0), (0.1, 0.07), (0.0, 0.1), (-0.14, 0.06)], 0.035, (0, 0, 0), bronze,
                  bevel=0.008)
    crest.data.transform(Matrix.Translation((0, hc.y + 0.0, 1.77)) @ Matrix.Rotation(-R90, 4, "Z"))
    on("head", crest)
    on("head", lumpy(0.04, (0.05, hc.y + 0.06, 1.78), moss, 3, 0.3, scale=(1.4, 1.2, 0.5)))
    export_humanoid("automaton", automaton_actions(), sk, AUTO_SCALE, ENEMY_YAW)


A_STAND = {"ik_foot.L": (0.14, 0.02, 0.09, 0, 6), "ik_foot.R": (-0.14, -0.02, 0.09, 0, 6), "ikw.L": 1.0, "ikw.R": 1.0,
           "root": (0, 0, -0.05), "spine": (2, 0, 0), "chest": (2, 0, 0), "head": (-2, 0, 0),
           "clavicle.L": (0, 0, 0), "clavicle.R": (0, 0, 0), "arm.L": (8, 0, 14), "arm.R": (8, 0, 14),
           "forearm.L": (26, 0, 0), "forearm.R": (26, 0, 0)}
A_WALK_FRAMES, A_WALK_STRIDE = 30, 1.5


def automaton_actions():
    def idle(t):
        a = 2 * math.pi * t
        look = math.sin(a)
        return P(A_STAND, **{"root": (0, 0, -0.05 - 0.008 * math.sin(2 * a)), "chest": (2 + 1.5 * math.sin(2 * a), 0, 0),
                             "head": (-2, 34 * math.sin(a) ** 3, 0), "neck": (0, 10 * look ** 3, 0),
                             "arm.L": (8 + 3 * math.sin(2 * a), 0, 14), "arm.R": (8 + 3 * math.sin(2 * a + 1), 0, 14)})
    walk = HU.gait(ASK, A_WALK_FRAMES, A_WALK_STRIDE, 0.6, lift=0.14, lift_at=0.45, strike=6, push=18, bob=0.02,
                   drop=-0.06, lean=4, width=0.15, arm_swing=18, arm_out=14, elbow=26, elbow_swing=10, pelvis_yaw=6,
                   pelvis_roll=7, shoulder_yaw=4, reach=0.5, sway=0.04, step=2,
                   base={"head": (-2, 0, 0), "clavicle.L": (0, 0, 0), "clavicle.R": (0, 0, 0)})
    jolt = P(A_STAND, **{"root": (0, -0.08, -0.04), "turn": (-8, 0, 0), "chest": (-14, 8, 0), "spine": (-6, 0, 0),
                         "head": (-24, -20, 12), "neck": (-8, 0, 0), "arm.L": (50, 0, 40), "forearm.L": (50, 0, 0),
                         "arm.R": (60, 0, 34), "forearm.R": (40, 0, 0), "ik_foot.L": (0.14, -0.06, 0.09, 0, 6)})
    shake = P(jolt, **{"head": (-18, 20, -10), "chest": (-10, -6, 0), "turn": (-5, 0, 0)})
    hit = HU.Anim({1: A_STAND, 3: jolt, 6: shake, 9: P(jolt, **{"head": (-14, -10, 6), "turn": (-3, 0, 0)}),
                   13: P(A_STAND, **{"head": (4, 0, 0), "chest": (6, 0, 0)}), 18: A_STAND})
    # die: sparks out, sags, topples forward face down with a clunk (holds)
    sag = P(A_STAND, **{"root": (0, 0.02, -0.2), "hips": (10, 0, 0), "spine": (14, 0, 0), "chest": (10, 0, 0),
                        "head": (30, 0, 12), "arm.L": (0, 0, 8), "arm.R": (0, 0, 8), "forearm.L": (6, 0, 0),
                        "forearm.R": (6, 0, 0)})
    fall = P(sag, **{"ikw.L": 0.0, "ikw.R": 0.0, "turn": (50, 0, 0), "root": (0, -0.3, -0.1), "thigh.L": (-4, 0, 4),
                     "thigh.R": (-4, 0, 4), "shin.L": (10, 0, 0), "shin.R": (10, 0, 0)})
    flat = P(fall, **{"turn": (88, 0, 0), "root": (0, -0.7, 0.26), "head": (-20, 40, 0), "hips": (0, 0, 0),
                      "spine": (0, 0, 0), "chest": (0, 0, 0), "neck": (-10, 0, 0), "arm.L": (120, 0, 60),
                      "arm.R": (110, 0, 60), "forearm.L": (10, 0, 0), "forearm.R": (10, 0, 0),
                      "thigh.L": (-6, 0, 6), "thigh.R": (-6, 0, 6), "foot.L": (-40, 0, 0), "foot.R": (-40, 0, 0)})
    die = HU.Anim({1: A_STAND, 4: jolt, 10: sag, 16: sag, 22: fall, 27: flat, 30: P(flat, **{"turn": (84, 0, 0),
                   "root": (0, -0.7, 0.32)}), 34: flat, 40: flat})
    return {"idle": cycle(60, idle, 3), "walk": walk, "hit": hit, "die": die}


# ---- the skeleton sentry: a cartoon skeleton in a dented bronze helmet, with a short sword

SSK = HU.Skeleton(HU.proportions(sh_w=0.17, hip_w=0.09))
SKEL_SCALE = 0.823


def bone_rod(a, b, r, material, knob=1.35):
    """A cartoon bone from a to b: a shaft with a pair of knobs at each end."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    side = d.cross(Vector((0, -1, 0)))
    if side.length < 0.1:
        side = d.cross(Vector((1, 0, 0)))
    side = side.normalized() * r * 0.55
    parts = [rod(a, b, r, material, verts=10)]
    for p in (a, b):
        for s in (-1, 1):
            parts.append(sphere(r * knob, tuple(p + side * s), material, segs=10, rings=6))
    _uid[0] += 1
    return join(parts, "bone_rod_%d" % _uid[0])


def skeleton():
    sk = SSK
    bone = mat("skeleton_bone", (0.93, 0.89, 0.76), 0.6, coat=0.2)
    shade = mat("skeleton_bone_shade", (0.7, 0.64, 0.5), 0.7)
    hole = mat("skeleton_socket", (0.07, 0.04, 0.05), 0.8)
    glow = mat("skeleton_glow", (0.75, 1.0, 0.3), 0.3, emit=6.0)
    helm = mat("skeleton_helmet", (0.62, 0.42, 0.2), 0.45, 0.8)
    rust = mat("skeleton_rust", (0.4, 0.22, 0.12), 0.8, 0.3)
    cloth = mat("skeleton_cloth", (0.55, 0.16, 0.14), 0.85)
    blade = mat("skeleton_blade", (0.78, 0.6, 0.35), 0.3, 0.9)
    # skull: a big round cranium, deep sockets with glowing pupils, a nose hole, a toothy grin
    hc = Vector((0, -0.01, 1.68))
    on("head", sphere(0.135, tuple(hc), bone, scale=(0.95, 1.02, 0.98), segs=24, rings=14))
    on("head", sphere(0.1, tuple(hc + Vector((0, -0.045, -0.085))), bone, scale=(0.95, 0.95, 0.7), segs=18, rings=10))
    for s in (-1, 1):
        on("head", sphere(0.042, tuple(hc + Vector((0.052 * s, -0.112, -0.005))), hole, scale=(1.0, 0.55, 1.1), segs=14,
                          rings=8))
        on("head", sphere(0.017, tuple(hc + Vector((0.05 * s, -0.132, -0.005))), glow, segs=10, rings=6))
        on("head", sphere(0.03, tuple(hc + Vector((0.075 * s, -0.09, -0.06))), bone, segs=10, rings=6))   # cheekbones
    on("head", sphere(0.02, tuple(hc + Vector((0, -0.14, -0.055))), hole, scale=(0.8, 0.5, 1.1), segs=10, rings=6))
    on("head", box((0.12, 0.03, 0.04), tuple(hc + Vector((0, -0.12, -0.105))), hole, bevel=0.01))
    for k in range(5):
        on("head", box((0.019, 0.022, 0.03), tuple(hc + Vector((-0.044 + 0.022 * k, -0.135, -0.095))), bone,
                       bevel=0.005))
        on("head", box((0.019, 0.022, 0.026), tuple(hc + Vector((-0.044 + 0.022 * k, -0.13, -0.122))), bone,
                       bevel=0.005))
    on("head", box((0.14, 0.05, 0.03), tuple(hc + Vector((0, -0.1, -0.145))), bone, bevel=0.012))     # the jaw
    # the dented bronze helmet: a dome, a rim, a crest ridge, a nasal guard
    dome = hemi(0.145, tuple(hc + Vector((0, 0.005, 0.02))), (0, 0, 1), helm, cut=-0.05, segs=24, rings=14)
    dome.data.transform(Matrix.Translation(hc) @ Matrix.Diagonal((1.0, 1.05, 1.0, 1)) @ Matrix.Rotation(0.12, 4, "X")
                        @ Matrix.Translation(-hc))
    on("head", dome)
    on("head", torus(0.145, 0.014, tuple(hc + Vector((0, 0.01, 0.0))), rust, rot=(0.12, 0, 0), verts=24, scale=(1, 1.05, 1)))
    ridge = [hc + Vector((0, 0.01 + 0.15 * math.sin(math.radians(a)), 0.02 + 0.15 * math.cos(math.radians(a))))
             for a in range(-70, 101, 17)]
    on("head", tube([tuple(p) for p in ridge], [0.018] * len(ridge), helm, verts=8))
    on("head", box((0.02, 0.012, 0.08), tuple(hc + Vector((0, -0.145, 0.0))), helm, rot=(0.15, 0, 0), bevel=0.005))
    on("head", sphere(0.025, tuple(hc + Vector((0.07, -0.08, 0.1))), rust, scale=(1, 1, 0.4), segs=8, rings=5))
    big = Matrix.Translation((0, 0, 1.56)) @ Matrix.Scale(1.25, 4) @ Matrix.Translation((0, 0, -1.56))
    for o in bpy.context.scene.objects:
        if o.get("bone") == "head":
            o.data.transform(big)
    # neck and spine: vertebrae
    for z in (1.47, 1.52, 1.56):
        on("neck", sphere(0.028, (0, 0.0, z), bone, scale=(1, 1, 0.7), segs=10, rings=6))
    for z in (1.08, 1.13, 1.18, 1.23):
        on("spine", sphere(0.03, (0, 0.035, z), bone, scale=(1.1, 1, 0.7), segs=10, rings=6))
    # chest: a rib cage (four hoops), a sternum, the upper spine, collarbones
    for i, z in enumerate((1.4, 1.335, 1.27, 1.205)):
        w = (0.125, 0.13, 0.125, 0.11)[i]
        o = torus(w, 0.018, (0, 0.0, z), bone, rot=(-0.18, 0, 0), verts=24, minor=6, scale=(1, 0.72, 1))
        on("chest", o)
    on("chest", box((0.04, 0.03, 0.2), (0, -0.098, 1.31), bone, rot=(-0.1, 0, 0), bevel=0.012))
    for z in (1.28, 1.33, 1.38, 1.43):
        on("chest", sphere(0.028, (0, 0.085, z), bone, scale=(1.1, 1, 0.7), segs=10, rings=6))
    for X, s in (("L", 1), ("R", -1)):
        c = sk.head("arm." + X)
        on("clavicle." + X, bone_rod((0.02 * s, -0.06, 1.44), (c.x, 0.0, c.z + 0.02), 0.014, bone))
        on("arm." + X, sphere(0.04, tuple(c), bone, segs=12, rings=8))
        on("arm." + X, bone_rod(along(sk, "arm." + X, 0.1), along(sk, "arm." + X, 0.95), 0.028, bone))
        a, b = along(sk, "forearm." + X, 0.08), along(sk, "forearm." + X, 0.95)
        for dy in (-0.012, 0.012):
            on("forearm." + X, rod(a + Vector((0, dy, 0)), b + Vector((0, dy, 0)), 0.017, bone, verts=8))
        on("forearm." + X, sphere(0.03, tuple(a), bone, segs=10, rings=6), sphere(0.026, tuple(b), bone, segs=10, rings=6))
        # a bony hand: a palm and three fingers
        h0, h1 = sk.head("hand." + X), sk.tail("hand." + X)
        on("hand." + X, sphere(0.03, tuple(h0.lerp(h1, 0.35)), bone, scale=(0.7, 1, 1.1), segs=10, rings=6))
        for k in (-1, 0, 1):
            p0 = h0.lerp(h1, 0.5) + Vector((0, -0.018 * k, 0))
            on("hand." + X, rod(p0, p0 + (h1 - h0).normalized() * 0.06 + Vector((0, -0.02, 0)), 0.009, bone, verts=6))
        # pelvis side, legs, feet
        on("hips", sphere(0.07, (0.075 * s, 0.01, 0.98), bone, scale=(1.0, 0.55, 1.1), segs=14, rings=8))
        on("thigh." + X, sphere(0.04, tuple(sk.head("thigh." + X)), bone, segs=12, rings=8))
        on("thigh." + X, bone_rod(along(sk, "thigh." + X, 0.08), along(sk, "thigh." + X, 0.94), 0.034, bone))
        on("shin." + X, sphere(0.036, tuple(along(sk, "shin." + X, 0.0, (0, -0.03, 0))), bone, segs=12, rings=8))
        a, b = along(sk, "shin." + X, 0.08), along(sk, "shin." + X, 0.92)
        on("shin." + X, rod(a + Vector((0.01 * s, 0, 0)), b + Vector((0.008 * s, 0, 0)), 0.024, bone, verts=8),
           rod(a + Vector((-0.012 * s, 0.005, 0)), b + Vector((-0.01 * s, 0.005, 0)), 0.012, bone, verts=8))
        f = sk.head("foot." + X)
        on("foot." + X, sphere(0.035, tuple(f), bone, segs=10, rings=6))
        on("foot." + X, box((0.07, 0.16, 0.035), (f.x, -0.07, 0.03), bone, bevel=0.015))
        for k in (-1, 0, 1):
            on("toe." + X, rod((f.x + 0.022 * k, -0.14, 0.022), (f.x + 0.022 * k, -0.2, 0.018), 0.011, bone, verts=6))
    on("hips", sphere(0.045, (0, 0.03, 0.96), bone, scale=(1, 0.8, 1.2), segs=12, rings=6))
    on("hips", torus(0.095, 0.014, (0, 0.0, 1.02), rust, verts=20, scale=(1.1, 0.85, 1)))
    # a tattered loincloth hanging from the rusty belt
    for x, h in ((-0.035, 0.18), (0.035, 0.15)):
        o = box((0.07, 0.012, h), (x, -0.085, 1.0 - h / 2), cloth, rot=(0.12, 0, 0.04 * (1 if x > 0 else -1)), bevel=0.004)
        on("hips", o)
    # the short sword in the right hand: grip along the hand's local +Z, the blade continuing past the thumb
    M = HU.bone_frame(sk, "hand.R")
    g = (-0.02, 0.075)
    blade_o = prism([(-0.03, 0.0), (0.03, 0.0), (0.028, 0.3), (0.0, 0.4), (-0.026, 0.3)], 0.014, (0, 0, 0), blade,
                    bevel=0.004)
    blade_o.data.transform(Matrix.Translation((g[0], g[1], 0.075)) @ Matrix.Rotation(R90, 4, "Z"))
    parts = [rod((g[0], g[1], -0.07), (g[0], g[1], 0.06), 0.016, rust, verts=8),
             box((0.03, 0.15, 0.028), (g[0], g[1], 0.065), rust, bevel=0.006),
             sphere(0.022, (g[0], g[1], -0.08), rust, segs=8, rings=5), blade_o]
    for o in parts:
        o.data.transform(M)
        on("hand.R", o)
    export_humanoid("skeleton", skeleton_actions(), sk, SKEL_SCALE, ENEMY_YAW)


S_STAND = {"ik_foot.L": (0.11, 0.03, 0.09, 0, 10), "ik_foot.R": (-0.11, -0.03, 0.09, 0, 10), "ikw.L": 1.0, "ikw.R": 1.0,
           "root": (0, 0, -0.06), "spine": (6, 0, 0), "chest": (6, 0, 0), "neck": (-4, 0, 0), "head": (-8, 0, 6),
           "arm.L": (6, 0, 12), "arm.R": (30, 0, 12), "forearm.L": (30, 0, 0), "forearm.R": (60, 0, 0)}
S_WALK_FRAMES, S_WALK_STRIDE = 24, 1.9


def skeleton_actions():
    def extra(ph, pose):
        a = 2 * math.pi * ph
        return {"head": (-8 + 6 * math.sin(2 * a), 8 * math.sin(a), 10 * math.sin(a)),
                "arm.R": (30 + 12 * math.sin(a), 0, 14), "forearm.R": (64, 0, 0)}
    walk = HU.gait(SSK, S_WALK_FRAMES, S_WALK_STRIDE, 0.55, lift=0.2, lift_at=0.4, strike=16, push=30, bob=0.05,
                   drop=-0.05, lean=6, width=0.12, arm_swing=34, arm_out=12, elbow=26, elbow_swing=30, pelvis_yaw=12,
                   pelvis_roll=10, shoulder_yaw=12, reach=0.5, sway=0.03, step=2, base={}, extra=extra)
    rattle = P(S_STAND, **{"root": (0, -0.06, 0.02), "turn": (-6, 0, 0), "chest": (-12, 0, 8), "spine": (-4, 0, 0),
                           "head": (-26, 40, -14), "arm.L": (70, 0, 60), "forearm.L": (20, 0, 0), "arm.R": (90, 0, 50),
                           "forearm.R": (30, 0, 0), "ik_foot.L": (0.11, -0.05, 0.12, -20, 10)})
    r2 = P(rattle, **{"head": (-20, -30, 14), "chest": (-8, 0, -8), "arm.L": (40, 0, 70), "arm.R": (110, 0, 40)})
    hit = HU.Anim({1: S_STAND, 3: rattle, 5: r2, 7: rattle, 9: r2, 12: P(S_STAND, **{"head": (4, 0, 14)}), 16: S_STAND})
    # die: the bones buckle and the skeleton slumps into a heap, the skull lolling (holds)
    buckle = P(S_STAND, **{"root": (0, 0.0, -0.3), "hips": (10, 0, 6), "spine": (20, 0, 8), "chest": (16, 0, -6),
                           "head": (20, 30, 20), "arm.L": (-10, 0, 30), "arm.R": (0, 0, 30), "forearm.L": (10, 0, 0),
                           "forearm.R": (20, 0, 0), "ik_foot.L": (0.16, 0.08, 0.09, 0, 30),
                           "ik_foot.R": (-0.16, -0.02, 0.09, 0, 30)})
    heap = {"ikw.L": 0.0, "ikw.R": 0.0, "root": (0, 0.1, -0.84), "hips": (-8, 0, 0), "spine": (40, 0, 10),
            "chest": (30, 10, 0), "neck": (20, 0, 0), "head": (30, 50, 40), "thigh.L": (88, 0, 20), "shin.L": (12, 0, 0),
            "thigh.R": (84, 0, 28), "shin.R": (24, 0, 0), "foot.L": (-20, 0, 0), "foot.R": (-20, 0, 0),
            "arm.L": (10, 0, 60), "forearm.L": (40, 0, 0), "arm.R": (20, 0, 56), "forearm.R": (30, 0, 0)}
    die = HU.Anim({1: S_STAND, 3: rattle, 6: buckle, 11: P(heap, **{"root": (0, 0.08, -0.78), "head": (0, 20, 10)}),
                   14: P(heap, **{"root": (0, 0.1, -0.86)}), 18: P(heap, **{"head": (36, 60, 30)}), 24: heap})
    idle = cycle(48, lambda t: P(S_STAND, **{"root": (0, 0, -0.06 - 0.01 * math.sin(4 * math.pi * t)),
                                             "head": (-8, 16 * math.sin(2 * math.pi * t), 6 + 4 * math.sin(4 * math.pi * t)),
                                             "chest": (6 + 2 * math.sin(4 * math.pi * t), 0, 0)}), 3)
    return {"idle": idle, "walk": walk, "hit": hit, "die": die}


# ---- the bat: a round temple bat with big ears and glowing eyes (built facing -Y, turned towards +X)

def bat():
    fur = mat("bat_fur", (0.36, 0.22, 0.2), 0.6, coat=0.2)
    face = mat("bat_face", (0.72, 0.5, 0.42), 0.6)
    wing = mat("bat_wing", (0.44, 0.24, 0.26), 0.5, coat=0.2)
    finger = mat("bat_finger", (0.22, 0.12, 0.12), 0.5)
    ear_in = mat("bat_ear", (0.85, 0.52, 0.5), 0.6)
    glow = mat("bat_glow", (1.0, 0.72, 0.2), 0.3, emit=6.0)
    fang = mat("bat_fang", (0.97, 0.96, 0.9), 0.3)
    c = Vector((0, 0, 0))
    B = {"root": ((0, 0, -0.2), (0, 0, -0.1), None), "body": ((0, 0, -0.12), (0, 0, 0.12), "root")}
    for s, side in ((1, "L"), (-1, "R")):
        B["wing." + side] = ((0.1 * s, 0.01, 0.03), (0.32 * s, 0.03, 0.06), "body")
        B["tip." + side] = ((0.32 * s, 0.03, 0.06), (0.58 * s, 0.06, 0.02), "wing." + side)
        B["ear." + side] = ((0.06 * s, 0.0, 0.1), (0.1 * s, 0.0, 0.22), "body")
    rig = TurnRig(B, 35, fps=FPS)
    rig.rigid("body", sphere(0.14, tuple(c), fur, scale=(1.0, 0.95, 1.0), segs=18, rings=12),
              sphere(0.1, tuple(c + Vector((0, -0.07, -0.02))), face, scale=(1.05, 0.6, 0.95), segs=14, rings=8),
              sphere(0.03, tuple(c + Vector((0, -0.145, -0.02))), face, scale=(1.3, 0.8, 0.8), segs=10, rings=6))
    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("body", sphere(0.03, tuple(c + Vector((0.05 * s, -0.12, 0.03))), glow, scale=(1, 0.5, 1.1), segs=10,
                                 rings=6),
                  rod(c + Vector((0.025 * s, -0.13, -0.05)), c + Vector((0.027 * s, -0.132, -0.09)), 0.011, fang, r2=0.0,
                      verts=5),
                  sphere(0.028, tuple(c + Vector((0.055 * s, 0.0, -0.13))), finger, segs=8, rings=5))
        rig.rigid("ear." + side, rod(c + Vector((0.06 * s, 0, 0.09)), c + Vector((0.12 * s, 0.01, 0.27)), 0.06, fur,
                                     r2=0.0, verts=10),
                  rod(c + Vector((0.063 * s, -0.02, 0.1)), c + Vector((0.11 * s, -0.012, 0.23)), 0.035, ear_in, r2=0.0,
                      verts=8))
        me = bpy.data.meshes.new("wing")
        bm = bmesh.new()
        N, M_ = 10, 3
        grid = []
        for i in range(N + 1):
            u = i / N
            x = 0.09 + u * 0.5
            lead_z = 0.03 + 0.06 * math.sin(u * math.pi) - 0.03 * u
            chord = 0.24 * (1 - u * 0.5) * (0.7 + 0.3 * abs(math.cos(u * math.pi * 2.5)))
            grid.append([bm.verts.new((s * x, 0.02 + 0.03 * u + 0.02 * j / M_, lead_z - chord * j / M_))
                         for j in range(M_ + 1)])
        for i in range(N):
            for j in range(M_):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                bm.faces.new(f if s > 0 else f[::-1])
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("wing", me)
        bpy.context.scene.collection.objects.link(o)
        solid(o, 0.016)
        K.finish(o, wing, smooth=50)
        bones = ["body", "wing." + side, "tip." + side]
        rig.smooth(bones, o)
        rig.smooth(bones, limb([(0.09 * s, 0.02, 0.03), (0.32 * s, 0.04, 0.075), (0.6 * s, 0.07, 0.01)],
                               [0.02, 0.015, 0.008], finger, verts=6, per=4, caps=True))
    rig.build("bat")
    up = mirror({"wing.L": (0, -50, 0), "tip.L": (0, -22, 0), "ear.L": (0, 6, 0)})
    mid_d = mirror({"wing.L": (0, 5, 0), "tip.L": (0, -14, 0)})
    down = mirror({"wing.L": (0, 46, 0), "tip.L": (0, 26, 0), "ear.L": (0, -8, 0)})
    mid_u = mirror({"wing.L": (0, 0, 0), "tip.L": (0, 30, 0)})
    rig.action("fly", {0: merge(up, {"@root": (0, 0, -0.03), "body": (6, 0, 0)}),
                       4: merge(mid_d, {"@root": (0, 0, 0.0)}),
                       8: merge(down, {"@root": (0, 0, 0.04), "body": (-4, 0, 0)}),
                       11: merge(mid_u, {"@root": (0, 0, 0.01)}),
                       15: merge(up, {"@root": (0, 0, -0.03), "body": (6, 0, 0)})}, loop=True)
    fold = mirror({"wing.L": (0, 70, 0), "tip.L": (0, 95, 0)})
    rig.action("die", {0: {}, 4: merge(up, {"@root": (0, 0, 0.05), "body": (-20, 0, 0)}),
                       10: merge(fold, {"root": (0, 0, 200), "@root": (0, 0, -0.15), "body": (30, 0, 0)}),
                       16: merge(fold, {"root": (0, 0, 360), "@root": (0, 0, -0.4), "body": (60, 0, 0)}),
                       22: merge(fold, {"root": (0, 0, 380), "@root": (0, 0, -0.45), "body": (70, 20, 0)})})
    rig.save("bat")


# ------------------------------------------------------------------ temple materials and helpers

def stone_mats():
    return {"stone": mat("tile_stone", (0.74, 0.55, 0.35), 0.85),
            "light": mat("tile_stone_light", (0.85, 0.68, 0.45), 0.85),
            "dark": mat("tile_stone_dark", (0.42, 0.28, 0.17), 0.9),
            "groove": mat("tile_groove", (0.2, 0.12, 0.07), 0.95)}


def chip(o, seed, amount=0.012):
    """Jitters the vertices of a bevelled block a little: hand-cut stone."""
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co += Vector((rnd.uniform(-amount, amount), rnd.uniform(-amount, amount) * 0.5, rnd.uniform(-amount, amount)))
    o.data.update()
    return o


def slab(x0, x1, z0, z1, material, seed, y0=-0.5, y1=0.5, bevel=0.035, amount=0.01):
    """A stone between x0..x1, z0..z1 (a masonry block inside a tile), bevelled and chipped."""
    o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), material, bevel=bevel, segs=2)
    return chip(o, seed, amount)


def groove_line(pts, material, w=0.018, y=-0.505):
    """A carved line on a front face (a thin dark strip just proud of it)."""
    parts = []
    for a, b in zip(pts, pts[1:]):
        a, b = Vector((a[0], y, a[1])), Vector((b[0], y, b[1]))
        d = b - a
        o = box((d.length + w, 0.012, w), tuple((a + b) / 2), material, rot=(0, -math.atan2(d.z, d.x), 0), bevel=0.003)
        parts.append(o)
    return parts


def spiral_glyph(c, r, material, y=-0.505, turns=1.6, w=0.022, n=26):
    pts = []
    for k in range(n):
        t = k / (n - 1)
        a = 2 * math.pi * turns * t
        rr = r * (0.15 + 0.85 * t)
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return groove_line(pts, material, w, y)


# ------------------------------------------------------------------ tiles (1 x 1 x 1, origin at the centre)

def tile_stone_a():
    """A single dressed block: soft chipped edges, a few pits and a hairline crack."""
    m = stone_mats()
    o = slab(-0.5, 0.5, -0.5, 0.5, m["stone"], 1, bevel=0.07, amount=0.018)
    parts = [o]
    rnd = random.Random(2)
    for k in range(5):
        parts.append(ico(rnd.uniform(0.02, 0.04), (rnd.uniform(-0.38, 0.38), -0.5, rnd.uniform(-0.38, 0.38)), m["dark"],
                         scale=(1, 0.4, 1), sub=1, smooth=0))
    parts += groove_line([(0.44, -0.44), (0.3, -0.33), (0.33, -0.18), (0.24, -0.1)], m["groove"], 0.014, y=-0.505)
    parts.append(box((0.3, 0.02, 0.012), (-0.2, -0.505, 0.44), m["light"], bevel=0.004))
    simple(parts, "tile_stone_a")


def tile_stone_b():
    m = stone_mats()
    parts = [slab(-0.5, 0.5, 0.0, 0.5, m["stone"], 3), slab(-0.5, 0.02, -0.5, 0.0, m["light"], 4),
             slab(0.02, 0.5, -0.5, 0.0, m["stone"], 5)]
    parts.append(slab(-0.5, 0.5, -0.5, 0.5, m["groove"], 6, y0=-0.44, y1=0.44, bevel=0.01, amount=0.0))
    simple(parts, "tile_stone_b")


def tile_stone_c():
    """A carved block: a sun-and-spiral glyph (a made-up motif) in a sunken frame."""
    m = stone_mats()
    parts = [slab(-0.5, 0.5, -0.5, 0.5, m["stone"], 7, bevel=0.05)]
    parts.append(box((0.82, 0.03, 0.82), (0, -0.505, 0), m["dark"], bevel=0.015))
    parts.append(chip(box((0.72, 0.04, 0.72), (0, -0.51, 0), m["light"], bevel=0.02), 8, 0.004))
    parts += spiral_glyph((0, 0), 0.18, m["groove"], y=-0.532)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        parts += groove_line([(0.24 * math.cos(a), 0.24 * math.sin(a)), (0.31 * math.cos(a), 0.31 * math.sin(a))],
                             m["groove"], 0.022, y=-0.532)
    simple(parts, "tile_stone_c")


def moss_mats():
    return (mat("tile_moss", (0.36, 0.56, 0.18), 0.9), mat("tile_moss_dark", (0.2, 0.38, 0.12), 0.9),
            mat("tile_leaf", (0.3, 0.62, 0.2), 0.6, coat=0.2))


def moss_cap(x0, x1, z, seed, drips=True, depth=(-0.52, 0.5)):
    """A mossy cushion over a top edge (x0..x1 at height z): a lumpy mat, clumps rolling over the front edge, fat
    drips and a few leaves."""
    moss, moss_dk, leaf = moss_mats()
    rnd = random.Random(seed)
    parts = [box((x1 - x0, depth[1] - depth[0] - 0.02, 0.05), ((x0 + x1) / 2, (depth[0] + depth[1]) / 2 + 0.01, z + 0.015),
                 moss, bevel=0.02)]
    n = int((x1 - x0) / 0.11) + 1
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n + rnd.uniform(-0.025, 0.025)
        r = rnd.uniform(0.06, 0.085)
        parts.append(lumpy(r, (x, depth[0] + 0.04, z + 0.015), moss if k % 3 else moss_dk, seed * 10 + k, 0.22,
                           scale=(1.25, 0.9, 0.75), sub=2))
        if rnd.random() < 0.5:
            parts.append(lumpy(r * 0.9, (x, depth[1] - 0.2 - rnd.uniform(0, 0.4), z + 0.02), moss, seed * 20 + k, 0.2,
                               scale=(1.3, 1.3, 0.6), sub=1))
        if drips and rnd.random() < 0.45:
            L = rnd.uniform(0.06, 0.2)
            parts.append(lumpy(0.05, (x, depth[0] + 0.005, z - 0.03), moss_dk, seed * 30 + k, 0.2, scale=(1.0, 0.7, 1.2)))
            parts.append(lumpy(0.035, (x + rnd.uniform(-0.02, 0.02), depth[0] + 0.0, z - 0.04 - L), moss_dk,
                               seed * 40 + k, 0.2, scale=(0.9, 0.7, 1.3)))
            parts.append(tube([(x, depth[0] + 0.005, z - 0.03), (x, depth[0] + 0.0, z - 0.04 - L)], [0.028, 0.022],
                              moss_dk, verts=8))
    for k in range(3):
        x = x0 + (x1 - x0) * rnd.uniform(0.1, 0.9)
        parts.append(leaf_mesh(0.18, 0.07, (x, depth[0] + 0.08, z + 0.03), rnd.uniform(-1.2, 1.2), leaf, droop=0.3))
    return parts


def leaf_mesh(length, width, base, angle, material, droop=0.4, fold=0.25, n=8, face=(0, -1, 0)):
    """A pointed leaf from `base`, leaning `angle` radians from vertical (+ to the right, seen from the front),
    folded along its midrib and drooping towards its tip."""
    bm = bmesh.new()
    rows = []
    for k in range(n + 1):
        t = k / n
        w = width * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.8 * (1 - 0.25 * t)
        y = length * t
        rows.append([bm.verts.new((-w, -fold * w, y)), bm.verts.new((0, 0, y)), bm.verts.new((w, -fold * w, y))])
    for r0, r1 in zip(rows, rows[1:]):
        bm.faces.new((r0[0], r0[1], r1[1], r1[0]))
        bm.faces.new((r0[1], r0[2], r1[2], r1[1]))
    o = new_obj("leaf", bm, material, smooth=60)
    solid(o, 0.008)
    # the leaf stands up along +Z facing the camera: curl the tip outwards (it droops once leaned), then lean it
    sg = 1 if angle >= 0 else -1
    for v in o.data.vertices:
        t = max(0.0, v.co.z / length)
        v.co.x += sg * droop * length * t * t
        v.co.y -= 0.15 * length * t * t
    o.data.transform(Matrix.Translation(Vector(base)) @ Matrix.Rotation(angle, 4, "Y"))
    return o


def tile_moss():
    m = stone_mats()
    parts = [slab(-0.5, 0.5, -0.5, 0.5, m["stone"], 11, bevel=0.05)]
    parts.append(chip(box((0.8, 0.04, 0.7), (0, -0.5, -0.05), m["light"], bevel=0.02), 12, 0.006))
    parts += moss_cap(-0.5, 0.5, 0.5, 13)
    simple(parts, "tile_moss")


def tile_brick():
    """The darker inner wall: small bricks in staggered rows, deep mortar."""
    br = mat("tile_brick", (0.42, 0.29, 0.2), 0.85)
    br2 = mat("tile_brick_light", (0.5, 0.36, 0.25), 0.85)
    mortar = mat("tile_mortar", (0.14, 0.09, 0.06), 0.95)
    parts = [box((1.0, 0.96, 1.0), (0, 0.02, 0), mortar, bevel=0.01)]
    rows = 4
    for r in range(rows):
        z0 = -0.5 + r / rows
        off = 0.25 if r % 2 else 0.0
        for c in range(-1, 3):
            x0 = -0.5 + c * 0.5 + off
            a, b = max(-0.5, x0 + 0.012), min(0.5, x0 + 0.5 - 0.012)
            if b - a < 0.05:
                continue
            parts.append(slab(a, b, z0 + 0.012, z0 + 1 / rows - 0.012, br if (r + c) % 3 else br2, 20 + r * 5 + c,
                              y0=-0.5, y1=-0.3, bevel=0.02, amount=0.006))
    simple(parts, "tile_brick")


def tile_platform():
    """A wooden plank bridge: 1 wide, 0.2 thick, top at +0.5 (the tile's top), lashed with rope at both ends."""
    wood = mat("platform_wood", (0.55, 0.34, 0.16), 0.7)
    dark = mat("platform_wood_dark", (0.32, 0.18, 0.08), 0.8)
    rope = mat("platform_rope", (0.78, 0.66, 0.42), 0.9)
    iron = mat("platform_iron", (0.3, 0.3, 0.32), 0.4, 0.8)
    parts = []
    for k, (y0, y1) in enumerate(((-0.45, -0.16), (-0.14, 0.14), (0.16, 0.45))):
        o = box((1.0, y1 - y0, 0.2), (0, (y0 + y1) / 2, 0.4), wood if k != 1 else dark, bevel=0.03)
        parts.append(chip(o, 30 + k, 0.006))
    parts += groove_line([(-0.45, 0.42), (-0.1, 0.43), (0.2, 0.41), (0.45, 0.42)], dark, 0.01, y=-0.456)
    parts += groove_line([(-0.4, 0.36), (0.0, 0.35), (0.35, 0.36)], dark, 0.01, y=-0.456)
    for x in (-0.4, 0.4):
        for k in range(3):
            parts.append(torus(0.115, 0.018, (x + (k - 1) * 0.035, -0.0, 0.4), rope, rot=(0, R90, 0), verts=16,
                               minor=6, scale=(1, 4.1, 1)))
        parts.append(cyl(0.02, 0.01, (x * 0.62, -0.458, 0.4), iron, rot=(R90, 0, 0), verts=8))
    simple(parts, "tile_platform")


# ------------------------------------------------------------------ traps

def spikes():
    """A row of spikes, 1 wide, 0.8 tall, rising from the origin (the floor) along +Y (Godot)."""
    iron = mat("spikes_iron", (0.42, 0.4, 0.4), 0.35, 0.85)
    tip = mat("spikes_tip", (0.85, 0.83, 0.8), 0.2, 0.95)
    rust = mat("spikes_rust", (0.45, 0.22, 0.1), 0.8, 0.3)
    parts = [box((0.96, 0.7, 0.08), (0, 0, 0.04), rust, bevel=0.02)]
    for row, (y, n, h) in enumerate(((-0.16, 5, 0.8), (0.16, 4, 0.7))):
        for k in range(n):
            x = -0.4 + 0.2 * k + 0.1 * row
            parts.append(cyl(0.075, h - 0.2, (x, y, 0.06 + (h - 0.2) / 2), iron, r2=0.03, verts=8))
            parts.append(cyl(0.03, 0.2, (x, y, h - 0.1), tip, r2=0.0, verts=8))
            parts.append(cyl(0.085, 0.04, (x, y, 0.09), rust, verts=8))
    simple(parts, "spikes")


def dart_hole():
    """A 1x1x1 wall block carved with a serpent's head in profile on its front, jaws open at the +X face around a dark
    bore: darts fly out along +X from (0.5, 0.06, 0) (Godot, from the origin at the centre). Mirror (scale.x = -1) to
    shoot along -X."""
    m = stone_mats()
    jade = mat("dart_hole_jade", (0.25, 0.7, 0.5), 0.35, 0.1, emit=0.6, emit_color=(0.2, 0.8, 0.5))
    hole = mat("dart_hole_dark", (0.03, 0.02, 0.02), 0.9)
    parts = [slab(-0.5, 0.5, -0.5, 0.5, m["stone"], 40, bevel=0.05)]
    parts.append(box((0.9, 0.03, 0.9), (0, -0.505, 0), m["dark"], bevel=0.015))
    parts.append(chip(box((0.84, 0.04, 0.84), (0, -0.51, 0), m["stone"], bevel=0.02), 41, 0.004))
    upper = [(-0.36, 0.02), (-0.3, 0.2), (-0.1, 0.3), (0.2, 0.3), (0.42, 0.22), (0.5, 0.14), (0.5, 0.1), (0.2, 0.08),
             (-0.1, 0.04)]
    lower = [(-0.3, -0.02), (0.1, 0.0), (0.5, -0.0), (0.5, -0.06), (0.36, -0.14), (0.0, -0.2), (-0.26, -0.16)]
    for poly in (upper, lower):
        parts.append(prism(poly, 0.12, (0, -0.55, 0.0), m["light"], bevel=0.035))
    parts.append(box((0.5, 0.1, 0.08), (0.26, -0.52, 0.05), hole, bevel=0.02))
    for x in (0.44, 0.3):   # fangs
        parts.append(cyl(0.022, 0.07, (x, -0.58, 0.06), m["light"], r2=0.0, rot=(math.pi, 0, 0), verts=6))
    parts.append(sphere(0.06, (0.1, -0.61, 0.19), jade, scale=(1.2, 0.5, 0.9), segs=14, rings=8))
    parts.append(box((0.014, 0.02, 0.07), (0.11, -0.64, 0.19), hole, bevel=0.004))
    parts.append(box((0.24, 0.04, 0.05), (0.08, -0.62, 0.27), m["dark"], rot=(0, 0.2, 0), bevel=0.015))
    parts.append(sphere(0.02, (0.42, -0.62, 0.19), hole, segs=8, rings=5))
    for k in range(3):    # scales
        x = -0.22 + 0.11 * k
        parts += groove_line([(x, 0.2), (x + 0.05, 0.13), (x, 0.06)], m["groove"], 0.015, y=-0.615)
    # the coiled body
    parts += spiral_glyph((-0.2, -0.28), 0.17, m["groove"], y=-0.535, w=0.03)
    # the bore in the +X face
    parts.append(cyl(0.075, 0.08, (0.48, 0.0, 0.06), hole, rot=(0, R90, 0), verts=14))
    parts.append(torus(0.085, 0.022, (0.505, 0.0, 0.06), m["dark"], rot=(0, R90, 0), verts=16))
    simple(parts, "dart_hole")


def dart():
    """A dart 0.36 long pointing +X, origin at its middle."""
    wood = mat("dart_wood", (0.6, 0.42, 0.22), 0.6)
    tip = mat("dart_tip", (0.8, 0.8, 0.82), 0.25, 0.9)
    feather = mat("dart_feather", (0.9, 0.22, 0.14), 0.7)
    parts = [rod((-0.14, 0, 0), (0.1, 0, 0), 0.012, wood, verts=8), rod((0.1, 0, 0), (0.18, 0, 0), 0.02, tip, r2=0.0, verts=8)]
    for a in range(3):
        r = a * 2 * math.pi / 3
        o = prism([(-0.18, 0.0), (-0.08, 0.0), (-0.11, 0.045), (-0.18, 0.05)], 0.004, (0, 0, 0), feather, bevel=0.0)
        o.data.transform(Matrix.Rotation(r, 4, "X"))
        parts.append(o)
    simple(parts, "dart")


def boulder():
    """A round carved stone ball 1.8 across, origin at the centre: grooved bands and a spiral on each face, so the roll
    reads. It rolls about Godot Z (the view axis)."""
    st = mat("boulder_stone", (0.6, 0.47, 0.34), 0.8)
    gr = mat("boulder_groove", (0.24, 0.15, 0.09), 0.95)
    moss = mat("boulder_moss", (0.34, 0.52, 0.18), 0.9)
    R = 0.9
    ball = lumpy(R, (0, 0, 0), st, 5, 0.02, sub=4, smooth=80)
    K.finish(ball, st, smooth=80)
    parts = [ball]
    # bands round the equator of the face, and across it
    for rot in ((R90, 0, 0), (0, 0, 0), (0, R90 * 0.5, 0), (0, -R90 * 0.5, 0)):
        if rot == (R90, 0, 0):
            parts.append(torus(R * 0.72, 0.035, (0, -R * 0.69, 0), gr, rot=rot, verts=40, minor=6))
            parts.append(torus(R * 0.72, 0.035, (0, R * 0.69, 0), gr, rot=rot, verts=40, minor=6))
        else:
            parts.append(torus(R * 1.0, 0.035, (0, 0, 0), gr, rot=rot, verts=48, minor=6))
    # spirals on both faces and small studs between the bands
    for sy in (-1, 1):
        pts = []
        for k in range(30):
            t = k / 29
            a = 2 * math.pi * 1.8 * t
            rr = R * 0.55 * (0.12 + 0.88 * t)
            p = Vector((rr * math.cos(a), 0, rr * math.sin(a)))
            p.y = sy * math.sqrt(max(0.0, (R + 0.012) ** 2 - p.x ** 2 - p.z ** 2))
            pts.append(tuple(p))
        parts.append(tube(pts, [0.03] * len(pts), gr, verts=6))
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        d = Vector((math.cos(a), 0.35, math.sin(a))).normalized()
        parts.append(lumpy(0.12, tuple(d * R * 0.97), moss, 60 + k, 0.3, scale=(1, 1, 0.5)) if k % 3 == 0 else
                     sphere(0.05, tuple(d * R * 1.0), gr, segs=8, rings=5))
    simple(parts, "boulder")


def crusher():
    """A heavy stone block 1 wide, 1.5 tall with iron spikes underneath; origin at the TOP centre (hang it from the
    ceiling: the block spans y 0 .. -1.2, the spikes reach -1.5)."""
    m = stone_mats()
    bronze = mat("crusher_bronze", (0.8, 0.52, 0.24), 0.35, 0.9)
    iron = mat("crusher_iron", (0.4, 0.4, 0.42), 0.35, 0.85)
    parts = [slab(-0.48, 0.48, -1.2, 0.0, m["stone"], 70, y0=-0.45, y1=0.45, bevel=0.05)]
    for z in (-0.12, -1.08):
        parts.append(box((1.0, 0.94, 0.08), (0, 0, z), bronze, bevel=0.02))
    # a scowling face in relief
    parts.append(box((0.7, 0.05, 0.12), (0, -0.46, -0.42), m["dark"], rot=(0, 0.0, 0), bevel=0.03))
    for s in (-1, 1):
        parts.append(box((0.3, 0.05, 0.08), (0.18 * s, -0.47, -0.36), m["light"], rot=(0, -0.3 * s, 0), bevel=0.02))
        parts.append(sphere(0.06, (0.18 * s, -0.47, -0.5), m["groove"], scale=(1.2, 0.4, 0.8), segs=10, rings=6))
    parts.append(box((0.5, 0.05, 0.1), (0, -0.47, -0.82), m["groove"], bevel=0.03))
    for k in range(5):
        parts.append(box((0.06, 0.03, 0.08), (-0.2 + 0.1 * k, -0.49, -0.79), m["light"], bevel=0.01))
    for x in (-0.36, -0.12, 0.12, 0.36):
        for y in (-0.2, 0.2):
            parts.append(cyl(0.07, 0.3, (x + (0.06 if y > 0 else 0), y, -1.35), iron, r2=0.0, rot=(math.pi, 0, 0), verts=8))
    for x in (-0.3, 0.3):
        parts.append(torus(0.07, 0.02, (x, 0, 0.02), iron, rot=(0, R90, 0), verts=12))
    simple(parts, "crusher")


def breakable():
    """A cracked stone block 1x1x1 (origin at the centre)."""
    m = stone_mats()
    parts = [slab(-0.5, 0.5, -0.5, 0.5, m["stone"], 80, bevel=0.05)]
    parts.append(chip(box((0.8, 0.04, 0.8), (0, -0.5, 0.0), m["light"], bevel=0.02), 81, 0.008))
    rnd = random.Random(82)
    for start, n in (((0.0, 0.42), 6), ((-0.42, -0.1), 5), ((0.42, -0.2), 4)):
        pts = [start]
        p = Vector(start)
        for k in range(n):
            p = p + Vector((-p.x * 0.25 + rnd.uniform(-0.08, 0.08), -p.y * 0.25 + rnd.uniform(-0.08, 0.08)))
            pts.append((p.x, p.y))
        parts += groove_line(pts, m["groove"], 0.04, y=-0.525)
    for k in range(4):
        parts.append(ico(0.045, (rnd.uniform(-0.3, 0.3), -0.53, rnd.uniform(-0.3, 0.3)), m["groove"], sub=1, smooth=0))
    parts.append(ico(0.06, (0.45, -0.45, 0.45), m["dark"], sub=1, smooth=0))
    parts.append(ico(0.05, (-0.46, -0.45, -0.3), m["dark"], sub=1, smooth=0))
    simple(parts, "breakable")


def rubble():
    """rubble.glb: root "rubble" (an empty at the block centre) with children rubble_0 .. rubble_7, stone chunks
    scattered over the block's volume, each with its origin at its own centre: throw them outwards when a
    breakable block blows up."""
    m = stone_mats()
    root = empty("rubble")
    rnd = random.Random(90)
    children = []
    for k in range(8):
        x, z = (-0.25 + 0.5 * (k % 2), -0.3 + 0.2 * (k // 2))
        c = (x + rnd.uniform(-0.08, 0.08), rnd.uniform(-0.2, 0.2), z + rnd.uniform(-0.05, 0.05))
        o = lumpy(rnd.uniform(0.12, 0.18), (0, 0, 0), m["stone"] if k % 3 else m["light"], 91 + k, 0.3,
                  scale=(1.0, 0.9, 0.8))
        o.location = c
        o.name = o.data.name = "rubble_%d" % k
        children.append((o, root))
    export_anim(root, "rubble", children, anim=False)


def dynamite():
    """A bundle of three sticks 0.4 tall with a fuse, origin at the base; child "spark" (dynamite_fuse, emissive) at
    the fuse tip: flicker or scale it while the fuse burns."""
    red = mat("dynamite_stick", (0.85, 0.16, 0.1), 0.55, coat=0.3)
    paper = mat("dynamite_paper", (0.92, 0.86, 0.7), 0.8)
    band = mat("dynamite_band", (0.25, 0.18, 0.12), 0.7)
    cord = mat("dynamite_cord", (0.2, 0.18, 0.16), 0.8)
    fuse_m = mat("dynamite_fuse", (1.0, 0.75, 0.25), 0.3, emit=12.0)
    parts = []
    for x, y in ((-0.065, 0.0), (0.065, 0.0), (0.0, 0.07)):
        parts.append(cyl(0.065, 0.36, (x, y, 0.18), red, verts=16, bevel=0.01))
        parts.append(cyl(0.05, 0.012, (x, y, 0.362), paper, verts=16))
    for z in (0.09, 0.27):
        parts.append(torus(0.14, 0.018, (0, 0.025, z), band, verts=20, scale=(1.05, 0.8, 1)))
    fuse = [(0.0, 0.07, 0.36), (0.02, 0.06, 0.42), (0.07, 0.03, 0.45), (0.1, 0.0, 0.42)]
    parts.append(tube(fuse, [0.012] * 4, cord, verts=6))
    body = join(parts, "dynamite")
    spark = star((0, 0, 0), 0.05, fuse_m, thick=0.02)
    spark2 = sphere(0.025, (0, 0, 0), fuse_m, segs=8, rings=5)
    sp = join([spark, spark2], "spark")
    sp.location = (0.1, -0.0, 0.42)
    export(body, "dynamite", [(sp, body)])


def ammo_box():
    """An olive ammunition tin with brass cartridges on its lid; 0.5 wide, 0.36 tall, origin at the base."""
    tin = mat("ammo_tin", (0.35, 0.4, 0.22), 0.45, 0.5)
    dark = mat("ammo_tin_dark", (0.2, 0.24, 0.12), 0.5, 0.5)
    brass = mat("ammo_brass", (0.95, 0.72, 0.3), 0.25, 0.95)
    lead = mat("ammo_lead", (0.55, 0.52, 0.5), 0.35, 0.7)
    parts = [box((0.5, 0.3, 0.28), (0, 0, 0.14), tin, bevel=0.03), box((0.52, 0.32, 0.05), (0, 0, 0.28), dark, bevel=0.015)]
    parts.append(box((0.1, 0.03, 0.04), (0, -0.165, 0.24), dark, bevel=0.01))
    for k in range(5):
        x = -0.16 + 0.08 * k
        parts.append(cyl(0.025, 0.12, (x, 0.0, 0.365), brass, verts=10))
        parts.append(cyl(0.022, 0.035, (x, 0.0, 0.44), lead, r2=0.012, verts=10))
    parts.append(box((0.3, 0.015, 0.1), (0, -0.155, 0.13), brass, bevel=0.005))
    for k in range(3):
        parts.append(cyl(0.012, 0.018, (-0.08 + 0.08 * k, -0.165, 0.13), dark, rot=(R90, 0, 0), verts=8))
    simple(parts, "ammo_box")


def dynamite_box():
    """A wooden crate of dynamite (sticks poking out, a red stick painted on the front); 0.55 wide, origin at the
    base."""
    wood = mat("dynbox_wood", (0.6, 0.4, 0.2), 0.7)
    dark = mat("dynbox_wood_dark", (0.36, 0.22, 0.1), 0.8)
    red = mat("dynamite_stick", (0.85, 0.16, 0.1), 0.55, coat=0.3)
    paper = mat("dynamite_paper", (0.92, 0.86, 0.7), 0.8)
    parts = [box((0.55, 0.36, 0.34), (0, 0, 0.17), wood, bevel=0.02)]
    for z in (0.04, 0.3):
        parts.append(box((0.57, 0.38, 0.06), (0, 0, z), dark, bevel=0.012))
    for x in (-0.26, 0.26):
        parts.append(box((0.05, 0.38, 0.34), (x, 0, 0.17), dark, bevel=0.012))
    parts.append(box((0.3, 0.02, 0.09), (0, -0.185, 0.17), red, bevel=0.01))
    parts.append(box((0.03, 0.02, 0.09), (-0.12, -0.19, 0.17), paper, bevel=0.005))
    for k, (x, y, tilt) in enumerate(((-0.12, 0.0, 0.15), (0.0, 0.04, -0.05), (0.11, -0.03, -0.2))):
        o = cyl(0.045, 0.3, (x, y, 0.36), red, rot=(0, tilt, 0), verts=12)
        parts.append(o)
    simple(parts, "dynamite_box")


def treasure_mats():
    return (mat("treasure_gold", (1.0, 0.74, 0.25), 0.28, 0.7, emit=0.35, emit_color=(1.0, 0.6, 0.15)),
            mat("treasure_gold_dark", (0.75, 0.46, 0.12), 0.35, 0.7, emit=0.15, emit_color=(0.8, 0.4, 0.1)),
            mat("treasure_ruby", (0.95, 0.1, 0.18), 0.05, 0.0, emit=0.6, coat=1.0),
            mat("treasure_emerald", (0.1, 0.85, 0.4), 0.05, 0.0, emit=0.6, coat=1.0),
            mat("treasure_shine", (1, 1, 1), 0.2, emit=6.0))


def treasure_idol():
    """A chubby golden idol (a made-up round-bellied guardian, not any real deity), 0.55 tall, ruby eyes."""
    gold, dark, ruby, emer, shine = treasure_mats()
    parts = [box((0.34, 0.26, 0.08), (0, 0, 0.04), dark, bevel=0.02),
             sphere(0.15, (0, 0, 0.2), gold, scale=(1.0, 0.9, 1.0), segs=20, rings=12),
             sphere(0.13, (0, -0.01, 0.4), gold, scale=(1.05, 0.95, 0.95), segs=20, rings=12)]
    for s in (-1, 1):
        parts.append(sphere(0.022, (0.045 * s, -0.12, 0.42), ruby, scale=(1, 0.5, 1), segs=10, rings=6))
        parts.append(sphere(0.05, (0.12 * s, -0.02, 0.4), gold, scale=(0.4, 0.8, 1.1), segs=10, rings=6))   # ears
        parts.append(sphere(0.055, (0.11 * s, -0.06, 0.22), gold, scale=(0.9, 0.9, 1.3), segs=10, rings=6))  # hands
        parts.append(sphere(0.06, (0.08 * s, -0.08, 0.1), gold, scale=(1.1, 1.3, 0.6), segs=10, rings=6))   # feet
    parts.append(box((0.08, 0.02, 0.012), (0, -0.125, 0.365), dark, bevel=0.004))
    parts.append(sphere(0.04, (0, -0.13, 0.2), emer, segs=10, rings=6))
    for k in range(5):   # a crown of rays
        a = math.radians(-60 + 30 * k)
        parts.append(cyl(0.025, 0.12, (0.11 * math.sin(a), 0.0, 0.5 + 0.08 * math.cos(a)), gold, r2=0.005,
                         rot=(0, a, 0), verts=8))
    parts.append(glint_obj((-0.07, -0.14, 0.47), 0.02, shine))
    simple(parts, "treasure_idol")


def glint_obj(c, r, material):
    return star(c, r, material, thick=0.01)


def treasure_gem():
    """A cut ruby 0.35 tall, origin at the base."""
    gold, dark, ruby, emer, shine = treasure_mats()
    bm = bmesh.new()
    n = 8
    top = [bm.verts.new((0.1 * math.cos(2 * math.pi * k / n), 0.1 * math.sin(2 * math.pi * k / n) * 0.8, 0.3)) for k in range(n)]
    mid = [bm.verts.new((0.17 * math.cos(2 * math.pi * (k + 0.5) / n), 0.17 * math.sin(2 * math.pi * (k + 0.5) / n) * 0.8, 0.22))
           for k in range(n)]
    tip = bm.verts.new((0, 0, 0.0))
    bm.faces.new(top[::-1])
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((top[k], top[j], mid[k]))
        bm.faces.new((mid[k], top[j], mid[j]))
        bm.faces.new((mid[k], mid[j], tip))
    g = new_obj("treasure_gem", bm, ruby, smooth=0)
    simple([g, glint_obj((-0.05, -0.15, 0.25), 0.03, shine)], "treasure_gem")


def treasure_coin():
    """A gold coin 0.3 across, standing, a star struck on it; origin at the base."""
    gold, dark, ruby, emer, shine = treasure_mats()
    parts = [cyl(0.15, 0.04, (0, 0, 0.15), gold, rot=(R90, 0, 0), verts=28, bevel=0.01),
             torus(0.13, 0.012, (0, -0.02, 0.15), dark, rot=(R90, 0, 0), verts=28),
             star((0, -0.025, 0.15), 0.075, dark, thick=0.012), glint_obj((-0.06, -0.035, 0.22), 0.02, shine)]
    simple(parts, "treasure_coin")


def exit_door():
    """A carved temple doorway 2 wide, 3 tall, origin at the bottom centre; a warm glow inside (exit_glow)."""
    m = stone_mats()
    dark = mat("exit_dark", (0.03, 0.02, 0.02), 0.9)
    glow = mat("exit_glow", (1.0, 0.7, 0.3), 0.5, emit=1.6)
    bronze = mat("exit_bronze", (0.85, 0.58, 0.25), 0.3, 0.9)
    parts = [box((1.1, 0.12, 2.4), (0, 0.3, 1.2), dark, bevel=0.01)]
    parts.append(box((0.84, 0.03, 2.2), (0, 0.23, 1.1), glow, bevel=0.01))
    parts.append(box((1.1, 0.4, 0.06), (0, 0.05, 0.03), m["dark"], bevel=0.01))
    for s in (-1, 1):
        parts.append(box((0.06, 0.5, 2.4), (0.53 * s, 0.0, 1.2), dark, bevel=0.005))
    for s in (-1, 1):   # jambs of stacked stones
        for k in range(4):
            z0 = k * 0.6
            parts.append(slab(min(0.55 * s, 1.0 * s), max(0.55 * s, 1.0 * s), z0 + 0.01, z0 + 0.59,
                              m["stone"] if k % 2 else m["light"], 100 + k + 10 * s, y0=-0.3, y1=0.3, bevel=0.04))
    # lintel with a sun glyph, a stepped crown
    parts.append(slab(-1.0, 1.0, 2.4, 2.8, m["stone"], 120, y0=-0.35, y1=0.35, bevel=0.05))
    parts.append(slab(-0.7, 0.7, 2.8, 3.0, m["light"], 121, y0=-0.3, y1=0.3, bevel=0.04))
    parts.append(cyl(0.16, 0.06, (0, -0.37, 2.6), bronze, rot=(R90, 0, 0), verts=20, bevel=0.01))
    for k in range(12):
        a = 2 * math.pi * k / 12
        parts.append(box((0.1, 0.03, 0.03), (0.24 * math.cos(a), -0.37, 2.6 + 0.24 * math.sin(a) * 0.6), bronze,
                         rot=(0, -a, 0), bevel=0.008))
    for s in (-1, 1):
        parts += spiral_glyph((0.62 * s, 2.6), 0.1, m["groove"], y=-0.36)
    # a step
    parts.append(slab(-0.9, 0.9, 0.0, 0.1, m["stone"], 122, y0=-0.4, y1=0.3, bevel=0.03))
    parts += moss_cap(-1.0, -0.2, 2.8, 123, drips=True, depth=(-0.37, 0.3))
    simple(parts, "exit_door")


def ladder():
    """One tile of ladder: two poles at x = +-0.32, four rungs, rope lashings; origin at the bottom centre, front
    towards the camera (y from -0.12 to 0.06). Stack segments every 1.0."""
    wood = mat("ladder_wood", (0.58, 0.38, 0.18), 0.7)
    dark = mat("ladder_wood_dark", (0.4, 0.24, 0.1), 0.75)
    rope = mat("ladder_rope", (0.78, 0.66, 0.42), 0.9)
    parts = []
    for x in (-0.32, 0.32):
        parts.append(cyl(0.045, 1.0, (x, 0.0, 0.5), wood, verts=10))
    for k in range(4):
        z = 0.125 + 0.25 * k
        parts.append(cyl(0.032, 0.72, (0, -0.045, z), dark, rot=(0, R90, 0), verts=8))
        for x in (-0.32, 0.32):
            parts.append(torus(0.05, 0.012, (x, -0.02, z), rope, rot=(0.6, 0, 0), verts=12, minor=4))
    simple(parts, "ladder")


def torch():
    """A wall torch: a bronze bracket (the origin, on the wall face), a wooden handle tilted up and out, a cup; child
    "flame" (torch_flame, torch_flame_core emissive; origin at the flame's base) with an animation "flicker"
    (loop 1 s). The flame's base sits 0.5 above the mount, 0.2 in front."""
    bronze = mat("torch_bronze", (0.8, 0.52, 0.24), 0.35, 0.9)
    wood = mat("torch_wood", (0.45, 0.28, 0.12), 0.7)
    cloth = mat("torch_cloth", (0.3, 0.22, 0.15), 0.9)
    flame_m = mat("torch_flame", (1.0, 0.45, 0.1), 0.5, emit=8.0)
    core_m = mat("torch_flame_core", (1.0, 0.9, 0.5), 0.5, emit=14.0)
    parts = [box((0.16, 0.04, 0.24), (0, 0.0, 0.0), bronze, bevel=0.015),
             rod((0, -0.02, -0.02), (0, -0.14, 0.12), 0.025, bronze, verts=8),
             torus(0.05, 0.015, (0, -0.14, 0.12), bronze, verts=12),
             rod((0, -0.1, -0.08), (0, -0.2, 0.44), 0.035, wood, r2=0.045, verts=10),
             cyl(0.075, 0.1, (0, -0.2, 0.46), bronze, r2=0.095, verts=14, bevel=0.01),
             sphere(0.075, (0, -0.2, 0.49), cloth, scale=(1, 1, 0.5), segs=12, rings=6)]
    body = join(parts, "torch")
    fl = [sphere(0.1, (0, 0, 0.1), flame_m, scale=(1, 1, 1.6), segs=14, rings=10),
          cyl(0.07, 0.2, (0.01, 0, 0.3), flame_m, r2=0.0, verts=10),
          sphere(0.055, (0, -0.03, 0.08), core_m, scale=(1, 1, 1.5), segs=12, rings=8)]
    flame = join(fl, "flame")
    flame.location = (0, -0.2, 0.5)
    animate(flame, "flicker", {0: {"scale": (1, 1, 1)}, 5: {"scale": (0.92, 0.92, 1.12), "rot": (0, 0.08, 0)},
                               10: {"scale": (1.06, 1.06, 0.9), "rot": (0, -0.05, 0)},
                               16: {"scale": (0.96, 0.96, 1.08), "rot": (0, 0.04, 0)},
                               22: {"scale": (1.04, 1.04, 0.95), "rot": (0, -0.06, 0)}, 30: {"scale": (1, 1, 1)}},
            linear=False)
    export_anim(body, "torch", [(flame, body)])


def vine():
    """vine.glb: three hanging vines side by side at the origin, "vine_1", "vine_2", "vine_3" (1, 2 and 3 tiles long),
    origin at the TOP (hang it under a ceiling tile); show one."""
    stem = mat("vine_stem", (0.3, 0.42, 0.14), 0.8)
    leaf = mat("vine_leaf", (0.32, 0.62, 0.2), 0.6, coat=0.2)
    leaf2 = mat("vine_leaf_dark", (0.2, 0.44, 0.14), 0.7)
    root = empty("vine")
    kids = []
    for L in (1, 2, 3):
        rnd = random.Random(200 + L)
        n = 6 * L
        pts = [(0.06 * math.sin(k * 0.9 + L), -0.05 + 0.02 * math.sin(k * 0.5), -L * k / n) for k in range(n + 1)]
        parts = [tube(pts, [0.03 - 0.015 * k / n for k in range(n + 1)], stem, verts=6)]
        for k in range(1, n + 1):
            p = Vector(pts[k])
            s = 1 if k % 2 else -1
            o = sphere(0.075, (0, 0, 0), leaf if k % 3 else leaf2, scale=(1.0, 0.25, 0.5), segs=10, rings=6)
            o.data.transform(Matrix.Translation(p + Vector((0.07 * s, -0.02, 0.02)))
                             @ Matrix.Rotation(0.6 * s + rnd.uniform(-0.2, 0.2), 4, "Y"))
            parts.append(o)
        v = join(parts, "vine_%d" % L)
        kids.append((v, root))
    export_anim(root, "vine", kids, anim=False)


# ------------------------------------------------------------------ backdrop (behind the play plane; origin at the
# base centre, front towards the camera)

def bg_pillar():
    """A carved pillar 1.1 wide, 4 tall: plinth, a banded shaft with a chevron frieze, a capital, a crack, moss."""
    m = stone_mats()
    parts = [slab(-0.55, 0.55, 0.0, 0.3, m["stone"], 300, y0=-0.4, y1=0.4, bevel=0.04),
             slab(-0.48, 0.48, 0.3, 0.42, m["light"], 301, y0=-0.34, y1=0.34, bevel=0.03)]
    for k in range(5):
        z0 = 0.42 + k * 0.62
        parts.append(chip(cyl(0.34, 0.6, (0, 0, z0 + 0.3), m["stone"] if k % 2 else m["light"], verts=16, bevel=0.03), 302 + k,
                          0.01))
    parts.append(cyl(0.37, 0.06, (0, 0, 1.66), m["dark"], verts=16))
    for k in range(6):  # chevrons on the frieze band
        x = -0.25 + 0.1 * k
        parts += groove_line([(x - 0.04, 1.73), (x, 1.79), (x + 0.04, 1.73)], m["groove"], 0.016, y=-0.345)
    parts.append(slab(-0.5, 0.5, 3.52, 3.72, m["light"], 310, y0=-0.4, y1=0.4, bevel=0.04))
    parts.append(slab(-0.6, 0.6, 3.72, 4.0, m["stone"], 311, y0=-0.45, y1=0.45, bevel=0.05))
    parts += groove_line([(0.1, 3.3), (0.05, 3.05), (0.14, 2.8), (0.08, 2.55)], m["groove"], 0.022, y=-0.34)
    parts += moss_cap(-0.6, 0.6, 4.0, 312, drips=True, depth=(-0.46, 0.45))
    parts += moss_cap(-0.55, 0.1, 0.3, 313, drips=False, depth=(-0.41, 0.4))
    simple(parts, "bg_pillar")


def bg_statue():
    """A big carved stone face (a made-up temple guardian, 3 wide, 3.4 tall): heavy brow, round staring eyes with
    faintly glowing gems (bg_statue_glow), a broad nose, a grim mouth, ear discs, a stepped headdress, moss."""
    m = stone_mats()
    glow = mat("bg_statue_glow", (0.3, 0.95, 0.8), 0.3, emit=2.5)
    parts = [slab(-1.3, 1.3, 0.0, 2.6, m["stone"], 400, y0=-0.3, y1=0.5, bevel=0.12, amount=0.03)]
    # headdress: stepped blocks
    parts.append(slab(-1.5, 1.5, 2.55, 2.9, m["light"], 401, y0=-0.4, y1=0.5, bevel=0.06))
    parts.append(slab(-1.1, 1.1, 2.9, 3.15, m["stone"], 402, y0=-0.35, y1=0.45, bevel=0.05))
    parts.append(slab(-0.5, 0.5, 3.15, 3.4, m["light"], 403, y0=-0.3, y1=0.4, bevel=0.05))
    for k in range(7):
        parts.append(box((0.16, 0.08, 0.16), (-0.9 + 0.3 * k, -0.43, 2.72), m["dark"], rot=(0, math.pi / 4, 0), bevel=0.02))
    # brow, eyes, nose, mouth
    parts.append(slab(-1.1, 1.1, 1.8, 2.05, m["light"], 404, y0=-0.42, y1=0.0, bevel=0.08))
    for s in (-1, 1):
        parts.append(sphere(0.3, (0.52 * s, -0.3, 1.55), m["light"], scale=(1.0, 0.4, 0.8), segs=20, rings=12))
        parts.append(sphere(0.2, (0.52 * s, -0.38, 1.55), m["groove"], scale=(1.0, 0.4, 0.8), segs=18, rings=10))
        parts.append(ico(0.09, (0.52 * s, -0.46, 1.55), glow, sub=1, smooth=0))
        parts.append(cyl(0.3, 0.2, (1.38 * s, -0.1, 1.4), m["light"], rot=(R90, 0, 0), verts=20, bevel=0.03))
        parts.append(cyl(0.14, 0.22, (1.38 * s, -0.12, 1.4), m["groove"], rot=(R90, 0, 0), verts=16))
        parts.append(sphere(0.16, (0.2 * s, -0.42, 0.98), m["light"], scale=(1, 0.7, 0.8), segs=12, rings=8))   # nostrils
    parts.append(prism([(-0.2, 0.9), (0.2, 0.9), (0.12, 1.5), (-0.12, 1.5)], 0.3, (0, -0.4, 0), m["light"], bevel=0.05))
    parts.append(slab(-0.7, 0.7, 0.4, 0.72, m["light"], 405, y0=-0.4, y1=0.0, bevel=0.07))
    parts.append(slab(-0.55, 0.55, 0.5, 0.62, m["groove"], 406, y0=-0.44, y1=-0.2, bevel=0.03))
    for k in range(6):
        parts.append(box((0.12, 0.06, 0.1), (-0.4 + 0.16 * k, -0.43, 0.6), m["stone"], bevel=0.02))
    parts += groove_line([(-0.4, 0.2), (0.0, 0.1), (0.4, 0.2)], m["groove"], 0.03, y=-0.32)
    parts += groove_line([(-0.9, 1.1), (-0.95, 0.7), (-0.8, 0.4)], m["groove"], 0.025, y=-0.32)
    parts += moss_cap(-1.5, 0.3, 2.9, 407, drips=True, depth=(-0.41, 0.5))
    parts += moss_cap(0.4, 1.3, 2.05, 408, drips=True, depth=(-0.43, 0.0))
    simple(parts, "bg_statue")


def bg_arch():
    """A corbelled stone arch 3.2 wide, 3.2 tall (opening 1.6 wide), origin at the base centre."""
    m = stone_mats()
    parts = []
    for s in (-1, 1):
        for k in range(5):
            z0 = k * 0.5
            w = 0.8 - (0.12 * (k - 2) if k > 2 else 0)
            x_in = 0.8 - max(0, k - 2) * 0.22
            parts.append(slab(min(s * x_in, s * 1.6), max(s * x_in, s * 1.6), z0 + 0.01, z0 + 0.49,
                              m["stone"] if (k + (s > 0)) % 2 else m["light"], 500 + k + 20 * s, y0=-0.3, y1=0.3))
    parts.append(slab(-0.5, 0.5, 2.5, 2.9, m["light"], 540, y0=-0.32, y1=0.32, bevel=0.05))
    parts.append(slab(-1.6, 1.6, 2.9, 3.2, m["stone"], 541, y0=-0.35, y1=0.35, bevel=0.05))
    parts += spiral_glyph((0, 2.7), 0.12, m["groove"], y=-0.33)
    parts += moss_cap(-1.6, -0.2, 3.2, 542, drips=True, depth=(-0.36, 0.35))
    simple(parts, "bg_arch")


def bg_jungle_plant():
    """A jungle plant 1.7 tall, 2 wide: broad pointed leaves on arching stems, a few young curled shoots and a fern
    skirt (bg_plant_leaf, bg_plant_leaf_dark, bg_plant_stem), origin at the base."""
    lf = mat("bg_plant_leaf", (0.28, 0.6, 0.18), 0.5, coat=0.3)
    lf2 = mat("bg_plant_leaf_dark", (0.15, 0.42, 0.14), 0.55, coat=0.3)
    st = mat("bg_plant_stem", (0.34, 0.46, 0.14), 0.7)
    rnd = random.Random(600)
    parts = []
    for k in range(11):
        a = math.radians(-75 + 150 * k / 10 + rnd.uniform(-6, 6))
        L = rnd.uniform(0.55, 0.95) * (1.1 - 0.3 * abs(math.sin(a)))
        tipv = Vector((math.sin(a) * L, rnd.uniform(-0.35, 0.25), math.cos(a) * L + 0.1))
        mid = tipv * 0.5 + Vector((0, 0, 0.18))
        parts.append(tube([(0, 0, 0.02), tuple(mid), tuple(tipv)], [0.03, 0.022, 0.014], st, verts=6))
        parts.append(leaf_mesh(rnd.uniform(0.6, 0.8), rnd.uniform(0.2, 0.26), tuple(tipv), a * 1.25,
                               lf if k % 2 else lf2, droop=0.35, fold=0.3))
    for k in range(9):
        a = math.radians(-80 + 160 * k / 8)
        parts.append(leaf_mesh(0.42, 0.07, (0.05 * math.sin(a), -0.3, 0.0), a * 1.1, lf2 if k % 2 else lf, droop=0.5,
                               fold=0.2))
    simple(parts, "bg_jungle_plant")


# ------------------------------------------------------------------ main

JOBS = {"explorer": explorer, "automaton": automaton, "skeleton": skeleton, "bat": bat,
        "spikes": spikes, "dart_hole": dart_hole, "dart": dart, "boulder": boulder, "crusher": crusher,
        "breakable": breakable, "rubble": rubble, "dynamite": dynamite, "ammo_box": ammo_box,
        "dynamite_box": dynamite_box, "treasure_idol": treasure_idol, "treasure_gem": treasure_gem,
        "treasure_coin": treasure_coin, "exit_door": exit_door, "ladder": ladder, "torch": torch, "vine": vine,
        "tile_stone_a": tile_stone_a, "tile_stone_b": tile_stone_b, "tile_stone_c": tile_stone_c,
        "tile_moss": tile_moss, "tile_brick": tile_brick, "tile_platform": tile_platform,
        "bg_pillar": bg_pillar, "bg_statue": bg_statue, "bg_arch": bg_arch, "bg_jungle_plant": bg_jungle_plant}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            clear_all()
            fn()
