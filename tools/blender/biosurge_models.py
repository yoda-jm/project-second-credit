"""Biosurge (game 34) models: the player's craft and its add-ons, the shots, nine cavern creatures, five bosses, the
pickups and the trader of the shop screen.
Original designs (our own shapes, nothing from any shooter): a chrome-and-teal bio-tech fighter with curved blade
wings, glowing veins and claw tips; a violet jellyfish, an arrow-headed fish, a pinwheel spore, an eye-stalk turret,
an armoured burrowing worm, an egg-sac spawner and a wall crab; an ivory-and-oxblood coiled shell creature with one
great eye, an indigo crustacean colossus, a brain-flower with eyes on its petals, a hooded bio-mechanical serpent
head and a heart bound in a ring of chitin and steel; a lavender trader with a monocle, a third eye on a stalk and a
tiny top hat. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/biosurge_models.py -- godot/games/biosurge/art/models [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (Rig,
merge, smooth_path), hopline_models.py (ell, hemi, loft_y), mossfolk_models.py (lathe_r, lumpy) and prism_models.py
(animate, export_anim, empty, new_obj, superellipse). 30 fps.

Axes. Built in Blender with Z up and the craft's nose towards +Y, which exports as Godot +X right, +Y up and
Blender +Y = Godot -Z: the play plane is Godot XZ at y = 0, seen from above, up the screen is -Z. The craft, its
add-ons and its shots face -Z; every enemy and boss faces +Z (down the screen, towards the player). Sizes in metres
(node scale 1). Animations marked * are seamless loops: set their loop mode in the game. Emissive materials all have
"glow" in their names. Rotations below are Godot's: rotation.y > 0 turns a part's +Z end towards +X.

THE CRAFT AND ITS ADD-ONS (materials ship_chrome, ship_teal, ship_dark, ship_canopy_glow, ship_vein_glow,
ship_engine_glow; the add-ons share them)
ship.glb      mesh "ship", origin at its centre on the play plane: 1.16 across the wing claws (x -0.58 .. 0.58), 1.35
              long (nose z -0.70, exhaust cones +0.65), 0.27 tall (y -0.12 .. 0.15). Child empties: engine_l / engine_r
              at (-+0.22, 0, 0.66) (the exhausts: trails and flames go there, pointing +Z), gun (0, -0.03, -0.70) at
              the nose, mount_l / mount_r (-+0.47, 0, 0.10) on the wings for pod_side, mount_rear (0, 0, 0.57) between
              the engines for pod_rear. One mesh: the view banks it by rolling about Z.
pod_side.glb  mesh "pod_side": a side cannon for the RIGHT wing, origin at its clamp (put it on mount_r); the pod
              runs x 0 .. 0.34, z -0.44 .. 0.26; child "gun" (0.17, 0, -0.44) at the muzzle. For the left wing set
              scale.x = -1 on mount_l.
pod_rear.glb  mesh "pod_rear": a twin rear gun, origin at its front mount (put it on mount_rear), twin barrels pointing
              +Z (z -0.02 .. 0.38, 0.34 across the fins); child "gun" (0, 0, 0.38).
drone.glb     root "drone_root": "drone" (a chrome saucer 0.4 across the fins, a glowing teal eye on top) and "ring"
              (a chrome ring 0.33 across with four glowing nubs); child "gun" (0, 0, -0.15). spin* 1.0 s: the ring
              turns once about Y. Orbit the root round the craft; face it with the craft.

SHOTS
shot_pulse.glb  mesh "shot_pulse": a teal bolt 0.44 long (z -0.22 .. 0.22), 0.12 across, its white core on top;
                shot_pulse_glow, shot_pulse_core_glow. Moves towards -Z.
shot_laser.glb  mesh "shot_laser": a beam segment from the origin 1.0 forward (z 0 .. -1), 0.12 across, flat ends;
                scale.z = length. shot_laser_glow, shot_laser_core_glow.
shot_homing.glb mesh "shot_homing": a small missile 0.43 long (nose z -0.17, the exhaust flame +0.26), four teal fins,
                origin near its centre; shot_homing_body, shot_homing_tip_glow (nose), shot_homing_glow (flame).
                Turn it about Y to steer (at rotation.y = 0 it flies -Z).
shot_enemy.glb  root "shot_enemy_root": "core" (yellow-orange), "shell" (two rings of flame), "spikes" (red barbs);
                0.32 across. pulse* 0.5 s: the core throbs, the rings spin, the barbs breathe.

ENEMIES (facing +Z; materials prefixed with the file name)
drifter.glb   armature "drifter_rig" (root, bell, tendril_0_0 .. tendril_5_2, arm_0_0 .. arm_3_1), mesh "drifter": a
              jellyfish bell 0.86 across (front z +0.43), six tendrils trailing behind it to z -1.08 (up the
              screen), 0.42 tall; origin at the bell's rim centre. pulse* 1.2 s: the bell contracts and relaxes, the
              tendrils and frilled arms wave. drifter_bell, drifter_under, drifter_glow (ribs, rim beads),
              drifter_heart_glow, drifter_arm, drifter_tendril_glow.
dart.glb      root "dart" > "body" > "tail" (pivot at the tail root, z -0.42): an arrow-headed fish 1.55 long (the
              chitin arrowhead's tip z +0.85, the forked tail -0.70), 0.9 across the fins. swim* 0.6 s: the tail
              beats, the body counter-sways. dart_body, dart_belly, dart_plate (the head), dart_fin, dart_spine,
              dart_glow (eyes, lateral line, fin edges), dart_pupil.
spinner.glb   mesh "spinner": a spore 1.38 across the spike tips, origin at its core; eight curled spikes in the plane
              (a pinwheel: spin it about Y), six short ones up; spinner_core, spinner_spike, spinner_glow (pores),
              spinner_tip_glow.
turret.glb    root "turret_root": "turret" (a fleshy mound 1.0 across with bone teeth and glowing veins, origin at its
              base centre: put it on the floor or a ledge) and "head" (origin on the vertical axis at y 0.20: the
              stalk, the eye and its chitin lid); rotation.y = atan2(dx, dz) aims the eye at (dx, dz) (at 0 it looks
              +Z, tilted up 55 degrees so the camera sees the iris). Child of head: "muzzle" at the pupil (0, 0.79,
              0.36 at rest). turret_flesh, turret_bone, turret_dark, turret_vein_glow, turret_eye, turret_iris_glow,
              turret_pupil, turret_lid.
worm_head.glb mesh "worm_head": 1.52 across the side spikes, z -0.54 .. +0.93 (the mandibles reach forward), a domed
              skull, eye cluster, glowing toothed maw. Chain behind it:
worm_seg.glb  mesh "worm_seg": 1.48 across the spikes, 0.84 long (z -0.42 .. 0.42), 0.75 tall: a broad chitin shell
              crossed by two glowing grooves, a bone crest, flank spikes and pores, over a glowing seam of flesh;
              space the links about 0.62 apart (head to first segment too), so each shell overlaps the next.
worm_tail.glb mesh "worm_tail": the last link, z -0.75 (the stinger, behind) .. +0.39.
              The worm shares worm_plate (dark crimson chitin), worm_ridge, worm_tooth, worm_seam_glow, worm_glow,
              worm_eye_glow, worm_maw_glow (flash worm_plate or the seams on hits).
pod.glb       root "pod_root": "sac" (the central sac and its roots, 2.0 across the roots, 0.95 tall), "mouth" (the
              spawning mouth on top, origin at its centre y 0.93: spawn from there), "egg_0".."egg_4" (glowing eggs
              round the base, origins on the floor under them). Origin at the floor. pulse* 2.0 s: the sac breathes,
              the mouth gapes, the eggs throb in turn. pod_sac, pod_vein, pod_root, pod_lip, pod_egg_glow,
              pod_mouth_glow.
crab.glb      armature "crab_rig" (root, body, eyes, leg0..2.L/R, shin0..2.L/R, claw.L/R, pincer.L/R, finger.L/R),
              mesh "crab": 1.75 across the legs, z -0.41 .. +0.81 (the claws forward), 0.54 tall, origin under its
              middle on the ground (on a wall, turn the node so its +Y points out of the wall). walk* 0.8 s: a
              tripod gait, about 0.25 a step, the claws and eye stalks bob. crab_shell, crab_under, crab_joint,
              crab_claw, crab_tip, crab_glow (back gem, eyes).

BOSSES (facing +Z; root empty named like the file, every part a child node with its origin at its hinge, the whole
boss centred on the origin across, along and in height; static: the view animates and flashes the parts; materials
bossN_*, the weak point's is bossN_core_glow)
boss_1.glb    the coiled shell creature, 6.2 across, 7.5 long, 2.3 tall. body (the shell, spiked keel with glowing
              vents, the spotted hood and a fan of small tentacles), core (the glowing siphon under the hood's lip,
              at (-1.14, 0.07, 0.40)), eye (one great eye on the hood, origin at its centre: turn it to track),
              arm_l, arm_r (two long tentacles, origins at their roots: swing them about Y). The shell coils to the
              right and behind; the head is left of centre (x -1.14).
boss_2.glb    the crustacean colossus, 6.7 across the claws and legs, 8.6 long (the tail fan behind), 1.8 tall. body,
              core (a glowing organ in a socket on its back, (0, 0.47, -0.71)), eye (a three-eyed turret at the
              front), jaw_l, jaw_r (hooked mandibles; closing: jaw_l rotation.y > 0, jaw_r < 0), arm_l, arm_r (the
              claws, origins at the shoulders (-+1.65, -0.28, 0.04); swinging inwards: arm_l rotation.y > 0), with
              children pinch_l, pinch_r (the moving fingers on the claws' outer sides; closing: pinch_l rotation.y
              > 0, pinch_r < 0).
boss_3.glb    the brain-flower, 6.6 across, 8.3 long (with its vines), 2.9 tall; the flower's centre at (0.02, 0,
              -0.89), the vines reaching forward to z +4.15. body (sepals, base, glowing
              stamens), petals (eight petals with sixteen eyes, one node: breathe it with scale or turn it slowly
              about Y), core (the folded glowing brain in the middle), eye (a great eye on a stalk at the front,
              origin at the stalk's foot (0.02, -0.29, 0.46)), arm_l, arm_r (thorny vines curling forward with a
              glowing spore bulb at the tip; origins at their roots).
boss_4.glb    the hooded serpent head, 7.0 across the hood, 7.1 long, 2.1 tall. body (the plated skull, horns, chrome
              fins, the cobra hood with glowing eyespots, two neck vertebrae behind), eye (six visor lenses and two
              brow slits: flash it), jaw_l, jaw_r (side mandibles with steel teeth hinged at (-+1.45, -0.47, -0.23);
              opening: jaw_l rotation.y < 0, jaw_r > 0; their tips meet in front of the snout), core (a glowing
              reactor between the jaw tips at the front, (0, -0.37, 3.07)).
boss_5.glb    the hive heart, 8.9 across (shutters open), 8.9 long, 2.9 tall. body (the fleshy bed, the chitin and
              steel ring with six clamps, pipes and arteries out to the edges, pump bladders behind), core (the
              heart, origin at its centre), jaw_l, jaw_r (armoured shutters hinged along Z at (-+1.85, -0.28, 0),
              modelled OPEN, flipped out 115 degrees; closing over the heart: jaw_r rotation.z = +115 degrees,
              jaw_l rotation.z = -115 degrees), arm_l, arm_r (tentacle cannons at the front, glowing mouths,
              origins at their roots), eye (a cluster eye on a stalk at the front).

PICKUPS (lying flat, faces up; the view may spin them about Y)
credit.glb    root "credit": "coin" (an amber coin 0.38 across stamped with a cell: credit_glow, credit_mark_glow)
              inside "bubble" (a clear bubble 0.58 across: credit_bubble is alpha-blended, credit_shine_glow).
power_gun.glb, power_speed.glb, power_shield.glb, power_life.glb
              mesh named like the file: a chrome hexagon 0.6 across (point to point, along z), 0.15 thick, teal studs
              (ship_chrome, ship_vein_glow), a coloured glowing disc (<name>_glow) and a raised emblem
              (<name>_mark_glow): gun orange with three arrows, speed yellow with two chevrons, shield blue with a
              shield (power_shield_inner), life green with a little craft.

THE SHOP
shop_keeper.glb armature "shop_keeper_rig" (root, chest, head, jaw, eye.L/R, ear.L/R, hat, arm.L/R, hand.L/R,
              stalk0..1, stache.L0..1, stache.R0..1), mesh "shop_keeper": a bust 2.1 tall (y 0 .. 2.11, the bust cut
              flat at y 0), 1.6 across the ears, facing +Z (the shop camera). keeper_skin, keeper_skin_light,
              keeper_eye, keeper_iris_glow, keeper_pupil, keeper_mouth, keeper_tooth, keeper_gold, keeper_monocle
              (alpha), keeper_vest, keeper_vest_trim, keeper_shirt, keeper_hat, keeper_gem_glow.
              Animations: idle* 3.0 s (breathing, the head sways, the third eye looks about, ears and moustache
              twitch, hands rub, one blink at 1.47 s), talk* 1.0 s (the jaw flaps three times, the head nods),
              blink 0.23 s (one-shot).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, export, reset, cyl, box
from blastyard_bombers import Rig, merge, smoothstep, smooth_path
from hopline_models import ell, hemi, loft_y
from mossfolk_models import lathe_r, lumpy
from prism_models import animate, empty, new_obj, superellipse
from prism_models import export_anim as _export_anim

FPS = 30
R90 = math.pi / 2


# ------------------------------------------------------------------ helpers

def export_anim(root, name, children=(), anim=True):
    """prism_models.export_anim, after refreshing the world matrices (join() moves origins without an update, and
    the parenting reads matrix_world)."""
    bpy.context.view_layer.update()
    _export_anim(root, name, children, anim)


def cone(base, tip, r, material, verts=8):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


def fib_dirs(n):
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        yield Vector((r * math.cos(i * ga), r * math.sin(i * ga), z))


def curve_pts(ctrl, per=4, closed=False):
    """A Catmull-Rom curve through 2D or 3D control points (closed: wraps round)."""
    P = [Vector(p) for p in ctrl]
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
        out = []
        for i in range(1, len(P) - 2):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            for s in range(per):
                t = s / per
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        return out
    return smooth_path(P, per)


def plate(poly, thick, z, material, bevel=0.012, segs=2, smooth=30, name="plate", taper=0.0):
    """A flat outline (x, y points, any winding) extruded `thick` along Z, centred on height z.
    taper shrinks the top face towards the outline's centre (a bevelled, blade-like plate)."""
    bm = bmesh.new()
    c = sum((Vector((p[0], p[1], 0)) for p in poly), Vector()) / len(poly)
    bot = [bm.verts.new((p[0], p[1], z - thick / 2)) for p in poly]
    top = []
    for p in poly:
        v = Vector((p[0], p[1], 0))
        v = v + (c - v) * taper
        top.append(bm.verts.new((v.x, v.y, z + thick / 2)))
    bm.faces.new(bot)
    bm.faces.new(top[::-1])
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, bevel, segs, smooth)


def xmirror_pts(half):
    """A symmetric outline from its right half (x >= 0, listed from the front tip round to the back)."""
    left = [(-x, y) for x, y in reversed(half) if x > 1e-6]
    return list(half) + left


def lathe_y(profile, material, segs=16, name="lathe", smooth=60, radial=None):
    """A surface of revolution about the Y axis from (r, y) pairs listed front (+y) to back."""
    o = lathe_r([(r, -y) for r, y in profile], material, segs=segs, name=name, smooth=smooth, radial=radial)
    o.data.transform(Matrix.Rotation(R90, 4, "X"))   # Z -> -Y ... so -(-y) = y
    o.data.update()
    return o


def move(o, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    """Transforms an object's mesh data in place (rotation in degrees, XYZ), after baking its own transform."""
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    M = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    if scale is not None:
        M = M @ Matrix.Diagonal(Vector(scale)).to_4x4()
    o.data.transform(M)
    o.data.update()
    return o


def displace(o, fn):
    for v in o.data.vertices:
        v.co = fn(Vector(v.co))
    o.data.update()
    return o


def noise3(p, seed=0, freq=1.0):
    """A cheap smooth pseudo-noise (sum of sines), -1 .. 1."""
    x, y, z = p.x * freq, p.y * freq, p.z * freq
    s = seed * 1.7
    return (math.sin(x * 1.7 + s + math.sin(y * 1.3 - s)) * 0.5 + math.sin(y * 2.1 - s * 0.7 + math.sin(z * 1.9))
            * 0.3 + math.sin(z * 2.7 + s * 1.3 + math.sin(x * 2.3)) * 0.2)


def node(parts, name, pivot=(0, 0, 0)):
    return join(parts, name, pivot)


def place(name, loc):
    e = empty(name)
    e.location = loc
    return e


def flat_disc(r, z, material, verts=24, center=(0, 0)):
    bm = bmesh.new()
    vs = [bm.verts.new((center[0] + r * math.cos(2 * math.pi * k / verts),
                        center[1] + r * math.sin(2 * math.pi * k / verts), z)) for k in range(verts)]
    bm.faces.new(vs)
    return new_obj("disc", bm, material, smooth=0)


def tube_pts(pts, r0, r1, material, verts=8, caps=True, per=3, name="tube", shape=None):
    """A smooth tube through control points, the radius going from r0 to r1 (or shape(u) * r0)."""
    P = smooth_path(pts, per)
    n = len(P)
    rad = [(shape(i / (n - 1)) * r0) if shape else r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    return tube(P, rad, material, verts=verts, caps=caps, name=name)


# ------------------------------------------------------------------ the player's craft and add-ons

def ship_mats():
    return dict(
        chrome=mat("ship_chrome", (0.78, 0.82, 0.88), 0.2, metal=0.9, coat=0.3),
        teal=mat("ship_teal", (0.02, 0.45, 0.47), 0.32, coat=1.0),
        dark=mat("ship_dark", (0.03, 0.04, 0.05), 0.45, metal=0.5),
        canopy=mat("ship_canopy_glow", (0.02, 0.12, 0.16), 0.05, coat=1.0, emit=0.35, emit_color=(0.1, 0.7, 0.9)),
        vein=mat("ship_vein_glow", (0.3, 1.0, 0.85), 0.3, emit=2.2, emit_color=(0.15, 1.0, 0.8)),
        engine=mat("ship_engine_glow", (0.6, 1.0, 1.0), 0.2, emit=4.0, emit_color=(0.3, 0.9, 1.0)))


def wing_outline():
    ctrl = [(0.1, 0.3), (0.26, 0.1), (0.44, -0.08), (0.56, -0.23), (0.545, -0.31), (0.44, -0.27), (0.32, -0.3),
            (0.14, -0.42)]
    return [(p.x, p.y) for p in curve_pts(ctrl, 4)]


def ship():
    reset()
    M = ship_mats()
    parts = []
    PX = 0.215                         # the engine pods' axis (x = +-PX)
    # the fuselage: a lofted superellipse from the tail to a needle nose
    prof = [(x, z) for x, z in superellipse(1.0, 1.0, 22, 2.6)]
    st = [(-0.56, 0.08, 0.055, 0.0), (-0.5, 0.12, 0.085, 0.0), (-0.3, 0.15, 0.11, 0.0), (0.0, 0.15, 0.12, 0.0),
          (0.25, 0.125, 0.11, 0.0), (0.42, 0.088, 0.083, -0.005), (0.55, 0.05, 0.055, -0.012),
          (0.63, 0.022, 0.03, -0.018), (0.665, 0.004, 0.008, -0.02)]
    parts.append(loft_y(prof, st, M["chrome"], cap_start=True, cap_end=True, name="hull", smooth=60))
    # a teal saddle over the back of the hull behind the canopy, a glowing spine ridge down its middle
    st2 = [(y, sx * 1.03, sz * 1.03, dz) for y, sx, sz, dz in st[1:4]] + [(0.05, 0.15 * 1.03, 0.12 * 1.03, 0.0)]
    parts.append(loft_y([(x, z) for x, z in superellipse(1.0, 1.0, 22, 2.6) if z > 0.1], st2, M["teal"],
                        name="saddle"))
    spine = [(0, -0.47, 0.095), (0, -0.3, 0.118), (0, -0.12, 0.126), (0, 0.0, 0.124)]
    parts.append(tube_pts(spine, 0.011, 0.011, M["vein"], verts=6))
    for s in (1, -1):   # ribs across the saddle, like a carapace
        for y in (-0.36, -0.25, -0.14):
            k = 1.0 - 0.15 * abs(y + 0.25) / 0.11
            pts = [(s * 0.025, y, 0.118 * k + 0.002), (s * 0.08, y - 0.01, 0.1 * k), (s * 0.13, y - 0.025, 0.06 * k)]
            parts.append(tube_pts(pts, 0.008, 0.005, M["chrome"], verts=5))
    # the canopy: a dark glass teardrop with a chrome rim
    parts.append(ell((0, 0.2, 0.08), (0.062, 0.18, 0.072), M["canopy"], segs=24, rings=14))
    rim = [Vector((0.066 * math.sin(a), 0.2 + 0.186 * math.cos(a), 0.083)) for a in
           (2 * math.pi * k / 40 for k in range(41))]
    parts.append(tube(rim, [0.008] * len(rim), M["chrome"], verts=6, caps=False, name="rim"))
    # the wings: curved blades, chrome with a teal leading-edge band and glowing veins, swept back to claw tips
    wo = wing_outline()
    lead = wo[:len(wo) // 2 + 1]
    for s in (1, -1):
        parts.append(plate([(s * x, y) for x, y in wo], 0.045, 0.0, M["chrome"], bevel=0.014, taper=0.05))
        band = [(x, y) for x, y in lead[1:-2]]
        band = [(s * x, y + 0.005) for x, y in band] + [(s * (x - 0.01), y - 0.075 + 0.03 * (x - 0.2))
                                                         for x, y in reversed(band)]
        parts.append(plate(band, 0.016, 0.025, M["teal"], bevel=0.005, taper=0.0))
        vein = [(s * 0.17, 0.08, 0.03), (s * 0.3, -0.06, 0.03), (s * 0.42, -0.17, 0.028), (s * 0.5, -0.25, 0.026)]
        parts.append(tube_pts(vein, 0.009, 0.005, M["vein"], verts=6))
        for a, b in (((0.3, -0.06), (0.33, -0.22)), ((0.41, -0.16), (0.43, -0.25))):
            parts.append(tube_pts([(s * a[0], a[1], 0.029), (s * (a[0] + b[0]) / 2 + s * 0.012, (a[1] + b[1]) / 2,
                                                             0.029), (s * b[0], b[1], 0.026)], 0.006, 0.004, M["vein"],
                                  verts=5))
        # the wing tip: a glowing claw curling back
        parts.append(tube_pts([(s * 0.51, -0.18, 0.0), (s * 0.565, -0.25, 0.0), (s * 0.575, -0.34, -0.004)],
                              0.02, 0.006, M["vein"], verts=8))
        # canards by the nose
        cp = [(s * 0.04, 0.52), (s * 0.15, 0.4), (s * 0.165, 0.355), (s * 0.04, 0.37)]
        parts.append(plate(cp, 0.022, 0.0, M["chrome"], bevel=0.007, taper=0.05))
        parts.append(tube_pts([(s * 0.06, 0.46, 0.013), (s * 0.15, 0.38, 0.012)], 0.005, 0.005, M["vein"], verts=5))
        # intakes on the hull's flanks
        parts.append(ell((s * 0.125, 0.06, 0.045), (0.03, 0.1, 0.028), M["dark"], segs=12, rings=8))
    # engine pods at the wing roots, glowing exhausts at the back
    for s in (1, -1):
        prof = [(0.0, 0.0), (0.035, -0.01), (0.058, -0.04), (0.074, -0.09), (0.08, -0.2), (0.078, -0.38),
                (0.085, -0.44), (0.088, -0.5), (0.08, -0.52), (0.0, -0.52)]
        pod = lathe_y(prof, M["chrome"], segs=24, name="pod", smooth=50)
        move(pod, (s * PX, -0.06, 0.0))
        parts.append(pod)
        for y, r, th in ((-0.43, 0.082, 0.011), (-0.2, 0.08, 0.009)):
            parts.append(torus(r, th, (s * PX, y, 0), M["teal"], rot=(R90, 0, 0), verts=24, minor=6))
        parts.append(torus(0.064, 0.014, (s * PX, -0.585, 0), M["engine"], rot=(R90, 0, 0), verts=24, minor=6))
        d = flat_disc(0.06, 0, M["engine"], verts=24)
        move(d, (s * PX, -0.57, 0), rot=(90, 0, 0))
        parts.append(d)
        parts.append(cone((s * PX, -0.565, 0), (s * PX, -0.65, 0), 0.042, M["engine"], verts=12))
        parts.append(tube_pts([(s * PX, -0.1, 0.07), (s * PX, -0.25, 0.082), (s * PX, -0.38, 0.08)],
                              0.007, 0.007, M["vein"], verts=5))
    # the nose gun: a short dark barrel with a glowing tip under the needle
    parts.append(rod((0, 0.5, -0.03), (0, 0.69, -0.03), 0.016, M["dark"], verts=8))
    parts.append(sphere(0.014, (0, 0.69, -0.03), M["vein"], segs=8, rings=6))
    root = join(parts, "ship")
    E = [place("engine_l", (-PX, -0.66, 0.0)), place("engine_r", (PX, -0.66, 0.0)),
         place("gun", (0.0, 0.7, -0.03)),
         place("mount_l", (-0.47, -0.1, 0.0)), place("mount_r", (0.47, -0.1, 0.0)),
         place("mount_rear", (0.0, -0.57, 0.0))]
    export_anim(root, "ship", [(e, root) for e in E], anim=False)


def pod_side():
    """A side cannon pod for the right flank: its clamp at the origin, the pod out to +X, the barrel forward."""
    reset()
    M = ship_mats()
    parts = []
    prof = [(0.0, 0.3), (0.03, 0.28), (0.06, 0.22), (0.075, 0.12), (0.078, -0.1), (0.07, -0.2), (0.05, -0.25),
            (0.0, -0.26)]
    b = lathe_y(prof, M["chrome"], segs=20, name="pod")
    move(b, (0.17, 0, 0))
    parts.append(b)
    parts.append(torus(0.078, 0.012, (0.17, 0.0, 0), M["teal"], rot=(R90, 0, 0), verts=20, minor=6))
    parts.append(torus(0.074, 0.01, (0.17, 0.14, 0), M["teal"], rot=(R90, 0, 0), verts=20, minor=6))
    parts.append(rod((0.17, 0.27, 0), (0.17, 0.42, 0), 0.022, M["dark"], verts=10))
    parts.append(torus(0.026, 0.008, (0.17, 0.41, 0), M["chrome"], rot=(R90, 0, 0), verts=12, minor=4))
    parts.append(sphere(0.018, (0.17, 0.425, 0), M["vein"], segs=8, rings=6))
    # the clamp arm back to the hull
    parts.append(plate([(0.0, 0.06), (0.11, 0.08), (0.12, -0.1), (0.0, -0.08)], 0.04, 0.0, M["dark"], bevel=0.01))
    parts.append(tube_pts([(0.17, -0.2, 0.06), (0.17, 0.0, 0.08), (0.17, 0.2, 0.06)], 0.008, 0.008, M["vein"], verts=5))
    # stabiliser fin outboard
    parts.append(plate([(0.24, 0.05), (0.33, -0.14), (0.33, -0.22), (0.24, -0.18)], 0.02, 0.0, M["teal"], bevel=0.006))
    parts.append(tube_pts([(0.3, -0.1, 0.0), (0.335, -0.18, 0.0)], 0.01, 0.01, M["vein"], verts=6))
    root = join(parts, "pod_side")
    g = place("gun", (0.17, 0.44, 0.0))
    export_anim(root, "pod_side", [(g, root)], anim=False)


def pod_rear():
    """A rear gun: its mount at the origin (front), the twin barrels pointing back (Blender -Y, Godot +Z)."""
    reset()
    M = ship_mats()
    parts = []
    prof = [(0.0, 0.02), (0.05, 0.0), (0.085, -0.05), (0.09, -0.16), (0.07, -0.24), (0.0, -0.26)]
    parts.append(lathe_y(prof, M["chrome"], segs=20, name="body"))
    parts.append(torus(0.088, 0.012, (0, -0.1, 0), M["teal"], rot=(R90, 0, 0), verts=20, minor=6))
    for s in (1, -1):
        parts.append(rod((s * 0.045, -0.15, 0), (s * 0.045, -0.36, 0), 0.018, M["dark"], verts=8))
        parts.append(sphere(0.016, (s * 0.045, -0.365, 0), M["vein"], segs=8, rings=6))
        parts.append(plate([(s * 0.06, -0.05), (s * 0.17, -0.17), (s * 0.17, -0.22), (s * 0.07, -0.18)], 0.02, 0.0,
                           M["teal"], bevel=0.006))
    parts.append(ell((0, -0.08, 0.07), (0.03, 0.06, 0.025), M["vein"], segs=10, rings=6))
    root = join(parts, "pod_rear")
    g = place("gun", (0.0, -0.38, 0.0))
    export_anim(root, "pod_rear", [(g, root)], anim=False)


def drone():
    """A small helper drone: a chrome saucer with a glowing teal eye on top and two fins; the outer ring spins."""
    reset()
    M = ship_mats()
    shell = [ell((0, 0, 0), (0.11, 0.11, 0.06), M["chrome"], segs=24, rings=12),
             torus(0.105, 0.012, (0, 0, -0.005), M["teal"], verts=24, minor=6),
             torus(0.052, 0.01, (0, 0.0, 0.05), M["teal"], verts=20, minor=6),
             sphere(0.045, (0, 0.0, 0.05), M["engine"], segs=16, rings=10),
             ell((0, 0.01, 0.088), (0.012, 0.03, 0.008), M["dark"], segs=10, rings=6)]
    for s in (1, -1):
        shell.append(plate([(s * 0.09, 0.03), (s * 0.2, -0.07), (s * 0.2, -0.13), (s * 0.09, -0.07)], 0.02, 0.0,
                           M["chrome"], bevel=0.006, taper=0.05))
        shell.append(tube_pts([(s * 0.12, -0.03, 0.012), (s * 0.19, -0.1, 0.012)], 0.007, 0.007, M["vein"], verts=5))
    shell.append(cone((0, 0.1, 0), (0, 0.15, 0), 0.02, M["vein"], verts=8))
    body = join(shell, "drone")
    ring = torus(0.16, 0.01, (0, 0, 0), M["chrome"], verts=36, minor=6)
    nubs = [ell((0.16 * math.cos(a), 0.16 * math.sin(a), 0), (0.022, 0.022, 0.016), M["vein"], segs=8, rings=6)
            for a in (k * math.pi / 2 + math.pi / 4 for k in range(4))]
    ring = join([ring] + nubs, "ring")
    n = 30
    animate(ring, "spin", {f: {"rot": (0, 0, 2 * math.pi * f / n)} for f in range(0, n + 1, 5)})
    root = empty("drone_root")
    g = place("gun", (0, 0.15, 0))
    export_anim(root, "drone", [(body, root), (ring, root), (g, root)])


# ------------------------------------------------------------------ shots

def shot_pulse():
    """A teal bolt; its white-hot core rides on top so it shows from the camera above."""
    reset()
    outer = mat("shot_pulse_glow", (0.15, 1.0, 0.85), 0.3, emit=3.0, emit_color=(0.05, 1.0, 0.8))
    core = mat("shot_pulse_core_glow", (0.9, 1.0, 1.0), 0.2, emit=6.0, emit_color=(0.8, 1.0, 1.0))
    a = tube_pts([(0, -0.2, 0), (0, -0.05, 0), (0, 0.12, 0), (0, 0.2, 0)], 0.07, 0, outer, verts=12,
                 shape=lambda u: 0.25 + 0.75 * math.sin(math.pi * min(1.0, u * 1.25)) ** 0.7 * (1 - u * 0.25))
    move(a, scale=(1.0, 1.0, 0.6))
    b = tube_pts([(0, -0.13, 0.02), (0, 0.0, 0.025), (0, 0.13, 0.022), (0, 0.18, 0.018)], 0.032, 0, core, verts=10,
                 shape=lambda u: 0.3 + 0.7 * math.sin(math.pi * min(1.0, u * 1.2)) ** 0.6)
    export(join([a, b], "shot_pulse"), "shot_pulse")


def shot_laser():
    """A beam segment from the origin 1 m forward (Godot -Z); flat ends so segments butt together."""
    reset()
    outer = mat("shot_laser_glow", (0.2, 1.0, 0.95), 0.3, emit=3.0, emit_color=(0.1, 0.95, 1.0))
    core = mat("shot_laser_core_glow", (0.9, 1.0, 1.0), 0.2, emit=6.0, emit_color=(0.85, 1.0, 1.0))
    a = cyl(0.06, 1.0, (0, 0.5, 0), outer, rot=(R90, 0, 0), verts=12)
    move(a, scale=(1.0, 1.0, 0.55))
    b = cyl(0.024, 1.0, (0, 0.5, 0.018), core, rot=(R90, 0, 0), verts=8)
    export(join([a, b], "shot_laser"), "shot_laser")


def shot_homing():
    reset()
    M = ship_mats()
    body = mat("shot_homing_body", (0.85, 0.88, 0.92), 0.25, metal=0.8)
    glow = mat("shot_homing_glow", (0.5, 1.0, 0.9), 0.3, emit=6.0, emit_color=(0.3, 1.0, 0.8))
    tipm = mat("shot_homing_tip_glow", (1.0, 0.5, 0.9), 0.3, emit=3.0, emit_color=(1.0, 0.35, 0.85))
    prof = [(0.0, 0.17), (0.02, 0.15), (0.032, 0.1), (0.035, 0.0), (0.035, -0.12), (0.03, -0.15), (0.0, -0.15)]
    parts = [lathe_y(prof, body, segs=14, name="body")]
    parts.append(lathe_y([(0.0, 0.175), (0.02, 0.152), (0.033, 0.11), (0.0, 0.11)], tipm, segs=14, name="tip"))
    parts.append(torus(0.036, 0.006, (0, 0.02, 0), M["teal"], rot=(R90, 0, 0), verts=14, minor=4))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), 0, math.sin(a)))
        fin = plate([(0.0, -0.06), (0.06, -0.13), (0.06, -0.16), (0.0, -0.15)], 0.01, 0.0, M["teal"], bevel=0.003)
        fin.data.transform(Matrix.Rotation(-a, 4, "Y"))
        fin.data.transform(Matrix.Translation(d * 0.025))
        fin.data.update()
        parts.append(fin)
    parts.append(cone((0, -0.15, 0), (0, -0.26, 0), 0.026, glow, verts=10))
    export(join(parts, "shot_homing"), "shot_homing")


def shot_enemy():
    """A spore of fire: a yellow-white core, two orange rings of flame round it, red barbs; pulse* 0.5 s."""
    reset()
    core = mat("shot_enemy_core_glow", (1.0, 0.7, 0.2), 0.3, emit=2.6, emit_color=(1.0, 0.5, 0.08))
    shell = mat("shot_enemy_glow", (0.9, 0.18, 0.02), 0.3, emit=1.5, emit_color=(1.0, 0.18, 0.02))
    spike = mat("shot_enemy_spike_glow", (0.7, 0.04, 0.03), 0.35, emit=1.1, emit_color=(1.0, 0.06, 0.03))
    c = join([ico(0.085, (0, 0, 0), core, sub=2)], "core")
    rings = [torus(0.11, 0.018, (0, 0, 0), shell, rot=(0, 0, 0), verts=24, minor=6),
             torus(0.11, 0.018, (0, 0, 0), shell, rot=(R90, 0, 0.6), verts=24, minor=6)]
    sh = join(rings, "shell")
    sp = []
    for d in fib_dirs(12):
        sp.append(cone(d * 0.1, d * 0.16, 0.028, spike, verts=5))
    sp = join(sp, "spikes")
    n = 15
    animate(c, "pulse", {f: {"scale": (s, s, s)} for f, s in ((0, 1.0), (4, 1.22), (8, 0.92), (15, 1.0))}, False)
    animate(sh, "pulse", {f: {"rot": (0, 0, 2 * math.pi * f / n), "scale": (s, s, s)}
                          for f, s in ((0, 1.0), (5, 0.9), (10, 1.08), (15, 1.0))})
    animate(sp, "pulse", {f: {"rot": (0, 0, -2 * math.pi * f / n / 3), "scale": (s, s, s)}
                          for f, s in ((0, 1.0), (5, 1.15), (10, 0.92), (15, 1.0))})
    root = empty("shot_enemy_root")
    export_anim(root, "shot_enemy", [(c, root), (sh, root), (sp, root)])


# ------------------------------------------------------------------ enemies (facing -Y: Godot +Z, down the screen)

def chain(rig_bones, prefix, pts, count, parent):
    """Adds `count` bones along a smooth path (prefix0, prefix1, ...); returns their names."""
    P = smooth_path(pts, 8)
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + (b - a).length)

    def at(d):
        for i in range(len(P) - 1):
            if L[i + 1] >= d:
                u = (d - L[i]) / max(1e-9, L[i + 1] - L[i])
                return P[i].lerp(P[i + 1], u)
        return P[-1]
    names = []
    for k in range(count):
        h, t = at(L[-1] * k / count), at(L[-1] * (k + 1) / count)
        nm = "%s%d" % (prefix, k)
        rig_bones[nm] = (tuple(h), tuple(t), parent if k == 0 else names[-1])
        names.append(nm)
    return names


def drifter():
    """A jellyfish: a scalloped violet bell with glowing ribs and a four-lobed glowing heart, frilled oral arms and
    long tendrils trailing behind it (up the screen)."""
    reset()
    bell_m = mat("drifter_bell", (0.5, 0.12, 0.62), 0.25, coat=1.0, emit=0.25, emit_color=(0.6, 0.1, 0.8))
    under = mat("drifter_under", (0.85, 0.35, 0.75), 0.35, coat=0.5)
    rib = mat("drifter_glow", (1.0, 0.45, 0.9), 0.3, emit=2.5, emit_color=(1.0, 0.25, 0.8))
    heart = mat("drifter_heart_glow", (1.0, 0.8, 0.3), 0.3, emit=3.0, emit_color=(1.0, 0.6, 0.15))
    arm_m = mat("drifter_arm", (0.95, 0.5, 0.85), 0.3, coat=0.6, emit=0.4, emit_color=(1.0, 0.3, 0.8))
    tend = mat("drifter_tendril_glow", (0.9, 0.4, 1.0), 0.3, emit=1.4, emit_color=(0.7, 0.25, 1.0))
    R = 0.4
    bones = {"root": ((0, 0, -0.1), (0, 0, 0.0), None), "bell": ((0, 0, 0.0), (0, 0, 0.3), "root")}
    tend_paths, arm_paths = [], []
    for i, a in enumerate((-50, -25, -8, 8, 25, 50)):
        ang = math.radians(90 + a)            # round the back half of the rim (+Y)
        p0 = Vector((R * 0.9 * math.cos(ang), R * 0.9 * math.sin(ang), -0.01))
        ln = 0.62 + 0.12 * (1 - abs(a) / 50)
        side = math.cos(ang)
        pts = [p0 + Vector((side * 0.05 * u + 0.05 * math.sin(u * 5 + i), u * ln, -0.04 * u)) for u in
               (0.0, 0.25, 0.5, 0.75, 1.0)]
        tend_paths.append(pts)
    for i, a in enumerate((-30, -10, 10, 30)):
        ang = math.radians(90 + a)
        p0 = Vector((0.08 * math.cos(ang), 0.05 * math.sin(ang), -0.02))
        pts = [p0 + Vector((math.cos(ang) * 0.12 * u + 0.03 * math.sin(u * 7 + i), 0.4 * u, -0.05 * u)) for u in
               (0.0, 0.33, 0.66, 1.0)]
        arm_paths.append(pts)
    tchains = [chain(bones, "tendril_%d_" % i, p, 3, "root") for i, p in enumerate(tend_paths)]
    achains = [chain(bones, "arm_%d_" % i, p, 2, "root") for i, p in enumerate(arm_paths)]
    rig = Rig(bones)

    def scallop(k, z):
        a = 2 * math.pi * k / 48
        return 1.0 + (0.045 * math.cos(8 * a) if z < 0.08 else 0.0)
    bell = lathe_r([(0.0, 0.3), (0.12, 0.29), (0.24, 0.25), (0.33, 0.18), (0.38, 0.1), (0.4, 0.04), (R, 0.0),
                    (0.38, -0.02), (0.3, 0.02), (0.15, 0.05), (0.0, 0.06)], bell_m, segs=48, radial=scallop,
                   name="bell", smooth=60)
    bell.data.materials.append(under)
    for f in bell.data.polygons:
        if f.normal.z < -0.3:
            f.material_index = 1
    parts = [bell]
    # eight glowing ribs over the dome, beads round the rim
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        prof = [(0.13, 0.29), (0.24, 0.255), (0.33, 0.185), (0.38, 0.105), (0.395, 0.05)]
        pts = [(r * 1.015 * math.cos(a), r * 1.015 * math.sin(a), z + 0.004) for r, z in prof]
        parts.append(tube_pts(pts, 0.012, 0.007, rib, verts=6))
    for k in range(16):
        a = 2 * math.pi * k / 16
        parts.append(sphere(0.018, (0.415 * math.cos(a), 0.415 * math.sin(a), 0.01), rib, segs=8, rings=6))
    # the four-lobed heart showing through the crown
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        parts.append(ell((0.1 * math.cos(a), 0.1 * math.sin(a), 0.27), (0.075, 0.045, 0.03), heart,
                         yaw=math.degrees(a), segs=12, rings=8))
    parts.append(sphere(0.045, (0, 0, 0.29), heart, segs=12, rings=8))
    rig.rigid("bell", parts)
    for pts, names in zip(arm_paths, achains):   # frilled oral arms: a wavy ribbon with a crinkled edge
        P = smooth_path(pts, 6)
        rad = [0.05 * (1 - 0.75 * i / (len(P) - 1)) for i in range(len(P))]
        o = tube(P, rad, arm_m, verts=8, caps=True, name="arm")
        displace(o, lambda c: c + Vector((0, 0, 0.012 * math.sin(c.y * 60))))
        rig.smooth(names, o)
    for pts, names in zip(tend_paths, tchains):
        P = smooth_path(pts, 6)
        rad = [0.022 * (1 - 0.8 * i / (len(P) - 1)) for i in range(len(P))]
        o = tube(P, rad, tend, verts=6, caps=True, name="tendril")
        beads = [sphere(0.016 * (1 - 0.5 * u), P[int(u * (len(P) - 1))], rib, segs=6, rings=4) for u in (0.3, 0.6, 0.9)]
        rig.smooth(names, o, beads)
    rig.build("drifter")
    # pulse: 1.2 s: the bell contracts (thrust) and relaxes; tendrils and arms wave in travelling S-curves
    keys = {}
    for f in range(0, 37, 4):
        u = f / 36
        a = 2 * math.pi * u
        c = math.sin(a)
        pose = {"%bell": (1 - 0.07 * c, 1 - 0.07 * c, 1 + 0.12 * c), "@root": (0, 0, 0.02 * c)}
        for i, names in enumerate(tchains):
            for j, nm in enumerate(names):
                pose[nm] = (6 * math.sin(a - 0.9 * j - 0.4 * i), 0, 14 * math.sin(a - 1.1 * j + 0.6 * i))
        for i, names in enumerate(achains):
            for j, nm in enumerate(names):
                pose[nm] = (8 * math.sin(a - 0.8 * j + i), 0, 10 * math.sin(a - 1.2 * j + 0.9 * i))
        keys[f] = pose
    rig.action("pulse", keys, loop=True)
    rig.export("drifter")


def dart():
    """A fast arrow-headed bio-fish: a wine-red chitin arrowhead, glowing eyes, swept fins, a forked tail."""
    reset()
    body_m = mat("dart_body", (0.12, 0.1, 0.38), 0.3, coat=0.8)
    belly = mat("dart_belly", (0.3, 0.22, 0.6), 0.4, coat=0.4)
    plate_m = mat("dart_plate", (0.6, 0.07, 0.14), 0.25, coat=1.0)
    fin_m = mat("dart_fin", (0.35, 0.15, 0.6), 0.35, coat=0.5)
    glow = mat("dart_glow", (0.75, 1.0, 0.2), 0.3, emit=3.0, emit_color=(0.6, 1.0, 0.1))
    bone = mat("dart_spine", (0.92, 0.85, 0.7), 0.35, coat=0.4)
    prof = [(x, z) for x, z in superellipse(1.0, 1.0, 20, 2.4)]
    st = [(-0.62, 0.02, 0.02, 0.0), (-0.52, 0.1, 0.07, 0.0), (-0.32, 0.19, 0.12, 0.0), (-0.08, 0.21, 0.13, 0.0),
          (0.15, 0.16, 0.11, 0.0), (0.33, 0.09, 0.075, 0.0), (0.45, 0.05, 0.05, 0.0)]
    parts = [loft_y(prof, st, body_m, cap_start=True, cap_end=True, name="body")]
    parts.append(loft_y([(x, z) for x, z in superellipse(1.0, 1.0, 20, 2.4) if z < -0.2],
                        [(y, sx * 1.02, sz * 1.02, dz) for y, sx, sz, dz in st[1:-1]], belly, name="belly"))
    head = xmirror_pts([(0.0, -0.72), (0.31, -0.24), (0.27, -0.15), (0.14, -0.2), (0.0, -0.12)])
    parts.append(plate(head, 0.05, 0.1, plate_m, bevel=0.012, taper=0.3))
    for s in (1, -1):
        parts.append(sphere(0.045, (s * 0.15, -0.3, 0.12), glow, segs=12, rings=8))
        parts.append(ell((s * 0.16, -0.31, 0.15), (0.012, 0.028, 0.01), mat("dart_pupil", (0.02, 0.02, 0.02), 0.2),
                         segs=8, rings=4))
        fin = [(s * 0.17, -0.06), (s * 0.45, 0.2), (s * 0.43, 0.29), (s * 0.3, 0.22), (s * 0.13, 0.14)]
        parts.append(plate(fin, 0.025, 0.0, fin_m, bevel=0.008, taper=0.05))
        parts.append(tube_pts([(s * 0.18, -0.05, 0.016), (s * 0.32, 0.08, 0.016), (s * 0.44, 0.24, 0.014)], 0.01,
                              0.004, glow, verts=5))
        for k in range(4):   # lateral line lamps
            y = -0.05 + 0.11 * k
            r = 0.2 - 0.03 * k
            parts.append(sphere(0.016, (s * r * 0.92, y, 0.06), glow, segs=6, rings=4))
    for k, y in enumerate((-0.05, 0.08, 0.2, 0.31)):   # spines down the back
        h = 0.13 - 0.02 * k
        parts.append(cone((0, y, 0.1), (0, y + 0.1, 0.1 + h), 0.03, bone, verts=6))
    body = join(parts, "body")
    tail = [loft_y(prof, [(0.4, 0.06, 0.055, 0.0), (0.55, 0.035, 0.035, 0.0), (0.62, 0.02, 0.02, 0.0)], body_m,
                   cap_end=True, name="stem")]
    fork = xmirror_pts([(0.0, 0.52), (0.08, 0.6), (0.23, 0.82), (0.15, 0.84), (0.0, 0.66)])
    tail.append(plate(fork, 0.022, 0.0, fin_m, bevel=0.007, taper=0.05))
    for s in (1, -1):
        tail.append(tube_pts([(s * 0.02, 0.6, 0.013), (s * 0.12, 0.72, 0.013), (s * 0.2, 0.82, 0.012)], 0.008, 0.004,
                             glow, verts=5))
    tail = join(tail, "tail", pivot=(0, 0.42, 0))
    n = 18
    animate(tail, "swim", {f: {"rot": (0, 0, math.radians(24) * math.sin(2 * math.pi * f / n))}
                           for f in range(0, n + 1, 3)}, linear=False)
    animate(body, "swim", {f: {"rot": (0, 0, math.radians(-5) * math.sin(2 * math.pi * f / n))}
                           for f in range(0, n + 1, 3)}, linear=False)
    root = empty("dart")
    tail.parent = body
    tail.matrix_parent_inverse = body.matrix_world.inverted()
    export_anim(root, "dart", [(body, root), (tail, body)])


def spinner():
    """A spiky spore: a lumpy purple core with glowing pores, eight long bone spikes in the plane, six short ones
    up and down, red glowing tips. The view spins it about Godot Y."""
    reset()
    core_m = mat("spinner_core", (0.32, 0.05, 0.36), 0.3, coat=0.8)
    pore = mat("spinner_glow", (0.85, 1.0, 0.2), 0.3, emit=3.0, emit_color=(0.7, 1.0, 0.1))
    spike = mat("spinner_spike", (0.9, 0.84, 0.68), 0.35, coat=0.5)
    tip = mat("spinner_tip_glow", (1.0, 0.25, 0.1), 0.3, emit=3.0, emit_color=(1.0, 0.15, 0.05))
    core = lumpy(0.31, (0, 0, 0), core_m, 7, amount=0.08, scale=(1, 1, 0.8), sub=3, smooth=60)
    parts = [core]
    dirs = [Vector((math.cos(a), math.sin(a), 0)) for a in (k * math.pi / 4 for k in range(8))]
    for k, d in enumerate(dirs):
        ln = 0.44 if k % 2 == 0 else 0.33
        bend = Vector((-d.y, d.x, 0)) * 0.06   # a slight curl, so the spin reads as a pinwheel
        pts = [d * 0.24, d * (0.24 + ln * 0.45) + bend * 0.5, d * (0.24 + ln * 0.8) + bend,
               d * (0.24 + ln) + bend * 1.6]
        parts.append(tube_pts(pts, 0.09, 0, spike, verts=8, shape=lambda u: max(0.04, 1 - u) ** 0.8))
        parts.append(sphere(0.03, pts[-1] - d * 0.02, tip, segs=8, rings=6))
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        for zs in (1,):
            d = Vector((0.55 * math.cos(a), 0.55 * math.sin(a), zs * 0.84)).normalized()
            parts.append(tube_pts([d * 0.22, d * 0.34, d * 0.46], 0.055, 0, spike, verts=6,
                                  shape=lambda u: 1 - u * 0.95))
            parts.append(sphere(0.022, d * 0.45, tip, segs=6, rings=4))
    for d in fib_dirs(22):   # glowing pores
        if abs(d.z) < 0.92:
            p = Vector((d.x * 0.3, d.y * 0.3, d.z * 0.24))
            if min((p.normalized() - dd).length for dd in dirs) > 0.3:
                parts.append(ell(p, (0.03, 0.03, 0.03), pore, segs=8, rings=6))
    export(join(parts, "spinner"), "spinner")


def turret():
    """A wall-mounted eye-stalk: a fleshy mound ringed with bone teeth; the stalk and its eye (node "head") turn
    about the vertical axis through the origin. The eye looks along -Y (Godot +Z), tilted up so the camera sees
    the iris."""
    reset()
    flesh = mat("turret_flesh", (0.45, 0.1, 0.16), 0.4, coat=0.6)
    dark = mat("turret_dark", (0.12, 0.02, 0.05), 0.5)
    bone_m = mat("turret_bone", (0.9, 0.84, 0.7), 0.35, coat=0.4)
    vein = mat("turret_vein_glow", (1.0, 0.4, 0.1), 0.3, emit=1.6, emit_color=(1.0, 0.3, 0.05))
    white = mat("turret_eye", (0.95, 0.9, 0.82), 0.15, coat=1.0)
    iris = mat("turret_iris_glow", (1.0, 0.3, 0.05), 0.2, emit=3.0, emit_color=(1.0, 0.25, 0.02))
    pupil = mat("turret_pupil", (0.01, 0.0, 0.0), 0.1, coat=1.0)
    lid_m = mat("turret_lid", (0.3, 0.05, 0.1), 0.3, coat=1.0)
    base = lathe_r([(0.0, 0.2), (0.15, 0.19), (0.3, 0.14), (0.42, 0.07), (0.5, 0.0), (0.0, 0.0)], flesh, segs=28,
                   name="mound", smooth=60)
    displace(base, lambda c: c + Vector((0, 0, 0.02 * noise3(c, 3, 9) * min(1, c.z * 8))))
    parts = [base, cyl(0.13, 0.04, (0, 0, 0.195), dark, verts=20)]
    for k in range(10):   # a ring of teeth round the socket
        a = 2 * math.pi * k / 10
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(cone(d * 0.28 + Vector((0, 0, 0.14)), d * 0.38 + Vector((0, 0, 0.25)), 0.05, bone_m, verts=6))
    for k in range(6):   # glowing veins over the mound
        a = 2 * math.pi * (k + 0.3) / 6
        pts = [(r * math.cos(a + 0.4 * r), r * math.sin(a + 0.4 * r), z) for r, z in
               ((0.16, 0.195), (0.28, 0.15), (0.38, 0.1), (0.48, 0.03))]
        parts.append(tube_pts(pts, 0.016, 0.01, vein, verts=5))
    mound = join(parts, "turret")
    # the stalk: rises, curls forward; the eye at its tip
    sp = [(0, 0.02, 0.18), (0, 0.0, 0.36), (0, -0.06, 0.5), (0, -0.16, 0.56)]
    head = [tube_pts(sp, 0.085, 0.065, flesh, verts=12, caps=False)]
    for k, u in enumerate((0.15, 0.4, 0.65)):   # rings of muscle on the stalk
        P = smooth_path(sp, 6)
        i = int(u * (len(P) - 1))
        tng = (P[i + 1] - P[i]).normalized()
        tr = torus(0.08, 0.016, (0, 0, 0), lid_m, verts=16, minor=5)
        tr.data.transform(Matrix.Translation(P[i]) @ tng.to_track_quat("Z", "Y").to_matrix().to_4x4())
        head.append(tr)
    E = Vector((0, -0.24, 0.62))
    look = Vector((0, -math.cos(math.radians(55)), math.sin(math.radians(55))))
    rot = look.to_track_quat("Z", "Y").to_matrix().to_4x4()   # local +Z along the look direction
    eye = [sphere(0.19, (0, 0, 0), white, segs=28, rings=18),
           hemi(0.192, (0, 0, 0), (0, 0, 1), iris, cut=0.8, segs=28, rings=14),
           ell((0, 0, 0.19), (0.03, 0.08, 0.012), pupil, segs=12, rings=6)]
    # the chitin lid behind and over the eyeball, a crest of spikes
    lid = hemi(0.21, (0, 0, 0), (0, 0, -1), lid_m, cut=-0.1, segs=28, rings=12)
    eye.append(lid)
    for k in (-1, 0, 1):
        eye.append(cone((k * 0.08, 0.1, -0.15), (k * 0.13, 0.12, -0.3), 0.04, bone_m, verts=6))
    for o in eye:
        o.data.transform(Matrix.Translation(E) @ rot)
        o.data.update()
    head += eye
    head = join(head, "head", pivot=(0, 0, 0.2))
    muzzle = place("muzzle", E + look * 0.21)
    root = empty("turret_root")
    export_anim(root, "turret", [(mound, root), (head, root), (muzzle, head)], anim=False)


def worm_mats():
    return dict(plate=mat("worm_plate", (0.36, 0.05, 0.09), 0.22, coat=1.0),
                ridge=mat("worm_ridge", (0.9, 0.82, 0.66), 0.35, coat=0.5),
                seam=mat("worm_seam_glow", (1.0, 0.45, 0.1), 0.4, emit=1.8, emit_color=(1.0, 0.35, 0.04)),
                glow=mat("worm_glow", (1.0, 0.6, 0.15), 0.3, emit=2.6, emit_color=(1.0, 0.5, 0.06)),
                bone=mat("worm_tooth", (0.95, 0.9, 0.78), 0.3, coat=0.5),
                maw=mat("worm_maw_glow", (1.0, 0.3, 0.1), 0.4, emit=2.5, emit_color=(1.0, 0.2, 0.04)),
                eye=mat("worm_eye_glow", (0.8, 1.0, 0.25), 0.2, emit=3.0, emit_color=(0.6, 1.0, 0.1)))


def worm_shell(yc, hw, hl, hh, M, spikes=True, lamps=True, grooves=(-0.35, 0.35)):
    """One armoured body shell: a broad dome of dark chitin with glowing grooves across it (it reads as three
    fused plates), a bone crest with spines down its middle, bone spikes at its flanks and a row of glowing pores."""
    parts = [ell((0, yc, 0.0), (hw, hl, hh), M["plate"], segs=32, rings=16)]

    def surf(x, y, lift=0.0):
        u = 1 - (x / hw) ** 2 - ((y - yc) / hl) ** 2
        return hh * math.sqrt(max(0.0, u)) + lift
    for g in grooves:
        y = yc + g * hl
        pts = [(x, y + 0.02 * (x / hw) ** 2, surf(x, y) - 0.008) for x in
               (hw * (-0.9 + 1.8 * k / 14) for k in range(15))]
        parts.append(tube_pts(pts, 0.026, 0.026, M["seam"], verts=6, per=2,
                              shape=lambda u: 0.45 + 0.55 * math.sin(math.pi * u)))
    crest = [(0, yc + hl * t, surf(0, yc + hl * t) - 0.01) for t in (-0.8, -0.4, 0.0, 0.4, 0.8)]
    parts.append(tube_pts(crest, 0.035, 0.035, M["ridge"], verts=8, shape=lambda u: 0.4 + 0.6 * math.sin(math.pi * u)))
    for t in (-0.55, 0.0, 0.55):
        b = Vector((0, yc + hl * t, surf(0, yc + hl * t) + 0.01))
        parts.append(cone(b, b + Vector((0, 0.06, 0.1)), 0.03, M["bone"], verts=6))
    if spikes:
        for s in (1, -1):
            for t in ((-0.4, 0.0, 0.4) if hl > 0.3 else (0.0,)):
                y = yc + hl * t
                parts.append(cone((s * hw * 0.9, y, 0.02), (s * (hw + 0.22), y + 0.12, -0.03), 0.05, M["bone"],
                                  verts=6))
    if lamps:
        for s in (1, -1):
            for t in (-0.6, 0.0, 0.6):
                x, y = s * hw * 0.62, yc + hl * t * 0.8
                parts.append(sphere(0.028, (x, y, surf(x, y) - 0.005), M["glow"], segs=8, rings=6))
    return parts


def worm_seg():
    """One body segment: a glowing seam of flesh under a broad armoured shell (0.80 long: chain the links about
    0.62 apart, so each shell overlaps the next)."""
    reset()
    M = worm_mats()
    parts = [ell((0, 0, -0.04), (0.47, 0.42, 0.2), M["seam"], segs=24, rings=12)]
    parts += worm_shell(0.0, 0.52, 0.38, 0.32, M)
    export(join(parts, "worm_seg"), "worm_seg")


def worm_head():
    """The worm's head: a domed skull with an eye cluster, a glowing toothed maw and four hooked mandibles at the
    front (-Y, Godot +Z)."""
    reset()
    M = worm_mats()
    parts = [ell((0, 0.12, -0.04), (0.48, 0.42, 0.2), M["seam"], segs=24, rings=12)]
    skull = ell((0, 0.0, 0.0), (0.58, 0.44, 0.38), M["plate"], pitch=-8, segs=32, rings=16)
    parts.append(skull)
    parts.append(tube_pts([(0, -0.38, 0.22), (0, -0.2, 0.37), (0, 0.05, 0.39), (0, 0.3, 0.3)], 0.04, 0.02,
                          M["ridge"], verts=8))
    parts.append(tube_pts([(x, 0.18 + 0.03 * (x / 0.5) ** 2, 0.34 * math.sqrt(max(0, 1 - (x / 0.58) ** 2)) - 0.0)
                           for x in (-0.48, -0.3, -0.12, 0.0, 0.12, 0.3, 0.48)], 0.026, 0.026, M["seam"], verts=6,
                          per=2, shape=lambda u: 0.45 + 0.55 * math.sin(math.pi * u)))
    for s in (1, -1):
        parts.append(tube_pts([(s * 0.12, -0.35, 0.25), (s * 0.3, -0.2, 0.31), (s * 0.48, 0.05, 0.2),
                               (s * 0.56, 0.2, 0.06)], 0.025, 0.015, M["ridge"], verts=6))
        for k in range(3):   # eye cluster on the brow
            parts.append(sphere(0.05 - 0.01 * k, (s * (0.16 + 0.09 * k), -0.29 + 0.07 * k, 0.29 - 0.015 * k),
                                M["eye"], segs=10, rings=6))
        for y in (-0.05, 0.25):
            parts.append(cone((s * 0.52, y, 0.05), (s * 0.76, y + 0.12, 0.0), 0.06, M["bone"], verts=6))
    # the maw at the front: a glowing throat ringed by teeth, four hooked mandibles
    parts.append(ell((0, -0.42, 0.02), (0.27, 0.1, 0.2), M["maw"], segs=20, rings=10))
    for k in range(12):
        a = 2 * math.pi * k / 12
        b = Vector((0.26 * math.cos(a), -0.44, 0.02 + 0.19 * math.sin(a)))
        parts.append(cone(b, b + Vector((-0.08 * math.cos(a), -0.05, -0.08 * math.sin(a))), 0.035, M["bone"], verts=6))
    for s in (1, -1):
        for zz, r in ((0.12, 0.07), (-0.06, 0.06)):
            pts = [(s * 0.28, -0.34, zz), (s * 0.46, -0.6, zz), (s * 0.36, -0.84, zz), (s * 0.14, -0.92, zz)]
            parts.append(tube_pts(pts, r, 0.008, M["bone"] if zz > 0 else M["plate"], verts=8,
                                  shape=lambda u: 1 - 0.88 * u))
    export(join(parts, "worm_head"), "worm_head")


def worm_tail():
    """The last segment: a smaller shell and a curled stinger with a glowing tip."""
    reset()
    M = worm_mats()
    parts = [ell((0, -0.05, -0.04), (0.34, 0.34, 0.16), M["seam"], segs=20, rings=10)]
    parts += worm_shell(-0.08, 0.4, 0.3, 0.25, M, grooves=(0.0,))
    parts.append(tube_pts([(0, 0.1, 0.05), (0, 0.42, 0.08), (0, 0.62, 0.16), (0, 0.7, 0.28)], 0.14, 0.0,
                          M["plate"], verts=10, shape=lambda u: (1 - u) ** 0.8 + 0.04))
    for k, u in enumerate((0.25, 0.5)):
        y = 0.15 + 0.5 * u
        parts.append(torus(0.12 * (1 - u) + 0.02, 0.016, (0, y, 0.07 + 0.08 * u * u), M["seam"],
                           rot=(R90 - 0.3 * u, 0, 0), verts=14, minor=5))
    parts.append(cone((0, 0.69, 0.26), (0, 0.66, 0.4), 0.03, M["bone"], verts=6))
    parts.append(sphere(0.045, (0, 0.7, 0.28), M["glow"], segs=10, rings=6))
    export(join(parts, "worm_tail"), "worm_tail")


def pod():
    """A fleshy egg-sac spawner rooted to the floor: a veined central sac with a puckered spawning mouth on top,
    ringed by five glowing eggs. pulse* 2.0 s: the sac breathes, the eggs throb in turn, the mouth gapes."""
    reset()
    sac_m = mat("pod_sac", (0.6, 0.2, 0.28), 0.35, coat=0.8)
    vein_m = mat("pod_vein", (0.35, 0.04, 0.12), 0.4, coat=0.6)
    egg_m = mat("pod_egg_glow", (0.75, 0.95, 0.3), 0.15, coat=1.0, emit=1.2, emit_color=(0.55, 1.0, 0.15))
    lip_m = mat("pod_lip", (0.85, 0.35, 0.4), 0.35, coat=0.5)
    hole = mat("pod_mouth_glow", (1.0, 0.75, 0.25), 0.4, emit=2.5, emit_color=(1.0, 0.6, 0.1))
    root_m = mat("pod_root", (0.3, 0.08, 0.1), 0.5)
    sac = lathe_r([(0.0, 0.95), (0.18, 0.93), (0.42, 0.85), (0.62, 0.68), (0.72, 0.45), (0.7, 0.22), (0.6, 0.06),
                   (0.5, 0.0), (0.0, 0.0)], sac_m, segs=36, name="sac", smooth=60)
    displace(sac, lambda c: c * (1 + 0.04 * noise3(c, 5, 6)))
    parts = [sac]
    rnd = random.Random(5)
    for k in range(9):   # veins snaking up the sac
        a = 2 * math.pi * k / 9 + rnd.uniform(-0.2, 0.2)
        pts = []
        for r, z in ((0.62, 0.06), (0.72, 0.3), (0.7, 0.5), (0.58, 0.72), (0.38, 0.87)):
            aa = a + 0.25 * math.sin(z * 9 + k)
            pts.append((r * 1.03 * math.cos(aa), r * 1.03 * math.sin(aa), z))
        parts.append(tube_pts(pts, 0.03, 0.014, vein_m, verts=6))
    for k in range(7):   # roots gripping the floor
        a = 2 * math.pi * (k + 0.5) / 7
        pts = [(0.55 * math.cos(a), 0.55 * math.sin(a), 0.05),
               (0.85 * math.cos(a + 0.1), 0.85 * math.sin(a + 0.1), 0.0),
               (1.0 * math.cos(a + 0.25), 1.0 * math.sin(a + 0.25), -0.02)]
        parts.append(tube_pts(pts, 0.07, 0.01, root_m, verts=7))
    sac = join(parts, "sac")
    mouth = [torus(0.17, 0.06, (0, 0, 0.93), lip_m, verts=24, minor=8),
             ell((0, 0, 0.92), (0.15, 0.15, 0.05), hole, segs=20, rings=8)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        mouth.append(ell((0.2 * math.cos(a), 0.2 * math.sin(a), 0.97), (0.09, 0.05, 0.035), lip_m,
                         yaw=math.degrees(a) + 90, segs=10, rings=6))
    mouth = join(mouth, "mouth", pivot=(0, 0, 0.93))
    eggs = []
    for k in range(5):
        a = 2 * math.pi * k / 5 - math.pi / 2
        c = Vector((0.82 * math.cos(a), 0.82 * math.sin(a), 0.2))
        e = [ell(c, (0.24, 0.24, 0.22), egg_m, segs=18, rings=12)]
        for j in range(3):
            aa = a + (j - 1) * 0.9
            pts = [c + Vector((0.23 * math.cos(aa + u), 0.23 * math.sin(aa + u), -0.15 + 0.3 * u))
                   for u in (0, 0.5, 1.0)]
            e.append(tube_pts(pts, 0.016, 0.01, vein_m, verts=5))
        eggs.append(join(e, "egg_%d" % k, pivot=c - Vector((0, 0, 0.2))))
    n = 60
    animate(sac, "pulse", {f: {"scale": (1 + 0.04 * math.sin(2 * math.pi * f / n),) * 2
                                        + (1 - 0.03 * math.sin(2 * math.pi * f / n),)}
                           for f in range(0, n + 1, 6)}, False)
    animate(mouth, "pulse", {f: {"scale": (1 + 0.18 * max(0, math.sin(2 * math.pi * f / n)),) * 2 + (1.0,),
                                 "loc": (0, 0, 0.035 * math.sin(2 * math.pi * f / n))} for f in range(0, n + 1, 6)},
            False)
    for k, e in enumerate(eggs):
        ph = k / 5
        animate(e, "pulse", {f: {"scale": (1 + 0.08 * math.sin(2 * math.pi * (f / n * 2 - ph)),) * 3}
                             for f in range(0, n + 1, 3)}, False)
    root = empty("pod_root")
    export_anim(root, "pod", [(sac, root), (mouth, root)] + [(e, root) for e in eggs])


def crab():
    """A wall crab: a broad spiked carapace with a glowing back-gem, eyes on stalks, two claws forward, six jointed
    legs. walk* 0.8 s: a tripod gait (the view moves the node; the step length is about 0.25)."""
    reset()
    shell_m = mat("crab_shell", (0.75, 0.25, 0.08), 0.3, coat=1.0)
    under = mat("crab_under", (0.95, 0.75, 0.55), 0.4, coat=0.4)
    dark = mat("crab_joint", (0.25, 0.06, 0.04), 0.45, coat=0.4)
    glow = mat("crab_glow", (0.4, 1.0, 0.8), 0.3, emit=2.6, emit_color=(0.2, 1.0, 0.7))
    claw_m = mat("crab_claw", (0.85, 0.32, 0.1), 0.25, coat=1.0)
    tipm = mat("crab_tip", (0.15, 0.04, 0.03), 0.3, coat=1.0)
    BZ = 0.25
    bones = {"root": ((0, 0, 0), (0, 0, 0.1), None), "body": ((0, 0.1, BZ), (0, -0.2, BZ), "root"),
             "eyes": ((0, -0.25, BZ + 0.05), (0, -0.35, BZ + 0.2), "body")}
    legs = []
    for s, side in ((1, "L"), (-1, "R")):
        for i, y in enumerate((-0.08, 0.08, 0.24)):
            hip = Vector((s * 0.3, y, BZ))
            knee = Vector((s * 0.55, y + 0.05 * (i - 1), BZ + 0.15))
            foot = Vector((s * 0.86, y + 0.16 * (i - 1), 0.0))
            a, b = "leg%d.%s" % (i, side), "shin%d.%s" % (i, side)
            bones[a] = (tuple(hip), tuple(knee), "body")
            bones[b] = (tuple(knee), tuple(foot), a)
            legs.append((a, b, hip, knee, foot, s, i))
        bones["claw." + side] = ((s * 0.22, -0.25, BZ), (s * 0.35, -0.5, BZ + 0.02), "body")
        bones["pincer." + side] = ((s * 0.35, -0.5, BZ + 0.02), (s * 0.28, -0.75, BZ + 0.02), "claw." + side)
        bones["finger." + side] = ((s * 0.3, -0.62, BZ + 0.02), (s * 0.22, -0.74, BZ + 0.02), "pincer." + side)
    rig = Rig(bones)
    # carapace: a broad flattened dome with a serrated rim
    cara = lathe_r([(0.0, BZ + 0.2), (0.15, BZ + 0.19), (0.3, BZ + 0.14), (0.4, BZ + 0.06), (0.43, BZ),
                    (0.38, BZ - 0.06), (0.0, BZ - 0.08)], shell_m, segs=36, name="carapace",
                   radial=lambda k, z: 1.0 + (0.06 * (k % 2) if z > BZ - 0.02 and z < BZ + 0.1 else 0))
    move(cara, scale=(1.15, 0.85, 1.0))
    cara.data.materials.append(under)
    for f in cara.data.polygons:
        if f.normal.z < -0.2:
            f.material_index = 1
    body = [cara]
    for s in (1, -1):   # rim spikes and back ridges
        for k, (x, y) in enumerate(((0.47, -0.08), (0.44, 0.1), (0.36, 0.24))):
            body.append(cone((s * x * 0.95, y, BZ + 0.03), (s * (x + 0.12), y + 0.06, BZ + 0.05), 0.04, dark, verts=6))
        body.append(tube_pts([(s * 0.08, -0.25, BZ + 0.17), (s * 0.22, -0.05, BZ + 0.17), (s * 0.18, 0.2, BZ + 0.13)],
                             0.02, 0.012, dark, verts=6))
    body.append(ell((0, 0.02, BZ + 0.19), (0.09, 0.12, 0.04), glow, segs=16, rings=8))
    body.append(torus(0.1, 0.018, (0, 0.02, BZ + 0.185), dark, verts=20, minor=5, scale=(1, 1.3, 1)))
    body.append(ell((0, -0.28, BZ - 0.02), (0.12, 0.06, 0.05), dark, segs=12, rings=6))   # mouthparts
    rig.rigid("body", body)
    eyes = []
    for s in (1, -1):
        eyes.append(rod((s * 0.08, -0.26, BZ + 0.08), (s * 0.12, -0.33, BZ + 0.24), 0.018, under, verts=6))
        eyes.append(sphere(0.04, (s * 0.12, -0.335, BZ + 0.25), glow, segs=10, rings=6))
    rig.rigid("eyes", eyes)
    for a, b, hip, knee, foot, s, i in legs:
        rig.rigid(a, rod(hip, knee, 0.062, shell_m, r2=0.05, verts=8), sphere(0.045, knee, dark, segs=8, rings=6))
        rig.rigid(b, rod(knee, foot + Vector((0, 0, 0.02)), 0.05, shell_m, r2=0.014, verts=8),
                  cone(foot + Vector((0, 0, 0.04)), foot, 0.015, tipm, verts=5))
    for s, side in ((1, "L"), (-1, "R")):
        rig.rigid("claw." + side, rod((s * 0.22, -0.25, BZ), (s * 0.35, -0.5, BZ + 0.02), 0.055, claw_m, r2=0.07,
                                      verts=10))
        rig.rigid("pincer." + side, ell((s * 0.34, -0.56, BZ + 0.02), (0.14, 0.16, 0.1), claw_m, segs=14, rings=8),
                  tube_pts([(s * 0.38, -0.6, BZ + 0.02), (s * 0.36, -0.72, BZ + 0.02), (s * 0.3, -0.8, BZ + 0.02)],
                           0.045, 0.008, tipm, verts=8, shape=lambda u: 1 - 0.85 * u))
        rig.rigid("finger." + side, tube_pts([(s * 0.29, -0.6, BZ + 0.02), (s * 0.25, -0.7, BZ + 0.02),
                                              (s * 0.25, -0.78, BZ + 0.02)], 0.032, 0.006, tipm, verts=8,
                                             shape=lambda u: 1 - 0.85 * u))
    rig.build("crab")
    # walk: tripod A = L0, R1, L2; tripod B = R0, L1, R2. f0: A down, B lifted; f12: swap; 24 = 0.8 s
    def walk_p(ph):
        a = 2 * math.pi * ph
        p = {"@root": (0, 0, 0.012 * abs(math.sin(2 * a))), "body": (0, 3 * math.sin(a), 0),
             "eyes": (6 * math.sin(2 * a), 0, 8 * math.sin(a)),
             "claw.L": (0, 0, 6 * math.sin(a)), "claw.R": (0, 0, 6 * math.sin(a)),
             "finger.L": (0, 0, -12 * max(0, math.sin(2 * a))), "finger.R": (0, 0, 12 * max(0, math.sin(2 * a)))}
        for _a, _b, hip, knee, foot, s, i in legs:
            grp = (i % 2 == 0) == (s > 0)        # tripod A
            q = a + (0 if grp else math.pi)
            swing = 16 * math.cos(q)              # about Z: forward/back
            lift = max(0.0, math.sin(q))           # lifting while swinging forward
            p[_a] = (0, -s * 22 * lift, -s * swing)
            p[_b] = (0, s * 10 * lift, 0)
        return p
    rig.action("walk", {f: walk_p(f / 24) for f in range(0, 25, 3)}, loop=True)
    rig.export("crab")


# ------------------------------------------------------------------ bosses (facing -Y: Godot +Z; 6-9 m across)

def sweep(pts, rx, rz, materials, verts=24, mat_fn=None, radial=None, cap_end=None, name="sweep", up=(0, 0, 1),
          smooth=50):
    """An elliptical tube along `pts` (rx, rz: lists of half widths across and up), its sections kept level (the
    `up` axis). mat_fn(i, k) -> material index per face (ring i, around k); radial(i, a) multiplies the radius;
    cap_end closes the last ring with that material index (an aperture)."""
    P = [Vector(p) for p in pts]
    bm = bmesh.new()
    rings = []
    U = Vector(up)
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        side = t.cross(U).normalized()
        upv = side.cross(t).normalized()
        ring = []
        for k in range(verts):
            a = 2 * math.pi * k / verts
            m = radial(i, a) if radial else 1.0
            ring.append(bm.verts.new(p + side * rx[i] * math.cos(a) * m + upv * rz[i] * math.sin(a) * m))
        rings.append(ring)
    for i, (r0, r1) in enumerate(zip(rings, rings[1:])):
        for k in range(verts):
            f = bm.faces.new((r0[k], r0[(k + 1) % verts], r1[(k + 1) % verts], r1[k]))
            f.material_index = mat_fn(i, k) if mat_fn else 0
    first = bm.faces.new(rings[0][::-1])
    first.material_index = 0
    if cap_end is not None:
        c = bm.faces.new(rings[-1])
        c.material_index = cap_end
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    K.select(o)
    for m in materials:
        o.data.materials.append(m)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth))
    return o


def boss_root(name, nodes):
    """Exports a root empty `name` with child nodes [(object, parent or None)] (None: the root), every node shifted
    so the boss's bounding box is centred on the origin (across, along and in height)."""
    bpy.context.view_layer.update()
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for o, _ in nodes:
        if o.type == "MESH":
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
    c = (lo + hi) / 2
    for o, p in nodes:
        if p is None:
            o.location -= c
    for o, p in nodes:
        if p is not None:
            o.location -= c
    print("  %s: %.2f across (x), %.2f long (y), %.2f tall (z)" % (name, hi.x - lo.x, hi.y - lo.y, hi.z - lo.z))
    root = empty(name)
    export_anim(root, name, [(o, p or root) for o, p in nodes], anim=False)


def boss_1():
    """The armoured nautilus: a coiled ivory shell striped in oxblood, ribbed with septa and spiked along its keel,
    lying flat; from its aperture (facing -Y) a leathery hood with a single great eye, a fan of tentacles and two
    long arms; the core is the glowing siphon under the hood's lip."""
    reset()
    ivory = mat("boss1_shell", (0.86, 0.78, 0.62), 0.3, coat=1.0)
    stripe = mat("boss1_stripe", (0.42, 0.07, 0.06), 0.3, coat=1.0)
    lip = mat("boss1_lip", (0.25, 0.04, 0.05), 0.35, coat=0.8)
    hood_m = mat("boss1_hood", (0.42, 0.13, 0.22), 0.4, coat=0.5)
    hood_spot = mat("boss1_hood_spot", (0.7, 0.3, 0.35), 0.4, coat=0.5)
    tent = mat("boss1_tentacle", (0.6, 0.22, 0.3), 0.4, coat=0.5)
    sucker = mat("boss1_sucker", (0.95, 0.75, 0.65), 0.35, coat=0.4)
    spike_m = mat("boss1_spike", (0.2, 0.05, 0.06), 0.3, coat=1.0)
    vent = mat("boss1_vent_glow", (1.0, 0.5, 0.1), 0.3, emit=2.5, emit_color=(1.0, 0.4, 0.05))
    core_m = mat("boss1_core_glow", (1.0, 0.45, 0.2), 0.3, emit=4.0, emit_color=(1.0, 0.35, 0.08))
    white = mat("boss1_eye", (0.95, 0.9, 0.8), 0.15, coat=1.0)
    iris = mat("boss1_iris_glow", (1.0, 0.8, 0.1), 0.2, emit=3.0, emit_color=(1.0, 0.7, 0.05))
    pupil = mat("boss1_pupil", (0.01, 0.0, 0.0), 0.1, coat=1.0)
    # the coil: a logarithmic spiral about Z; turned so the aperture's end runs towards -Y
    b = math.log(3.0) / (2 * math.pi)
    th0, th1 = -2.2 * math.pi, 0.0
    N = 150
    pts, rx, rz = [], [], []
    for i in range(N + 1):
        th = th0 + (th1 - th0) * i / N
        r = 2.25 * math.exp(b * th)
        pts.append(Vector((r * math.cos(th), r * math.sin(th), 0)))
        rx.append(0.58 * r)
        rz.append(0.42 * r)
    tdir = (pts[-1] - pts[-2]).normalized()
    rot = tdir.to_2d().angle_signed(Vector((0, -1)))
    R = Matrix.Rotation(-rot, 4, "Z")
    pts = [R @ p for p in pts]
    off = Vector((-pts[-1].x, 0.0 - pts[-1].y, 0))
    pts = [p + off for p in pts]
    # where is the centre? keep the aperture at y = 0, the coil behind it (+Y)
    if sum(p.y for p in pts) < 0:
        pts = [Vector((p.x, -p.y, p.z)) for p in pts]

    def ribs(i, a):
        u = i / N
        th = th0 + (th1 - th0) * u
        k = (th * 2.6) % (2 * math.pi)
        return 1.0 + 0.035 * max(0.0, math.cos(k)) ** 6 - 0.012

    def stripes(i, k):
        u = i / N
        th = th0 + (th1 - th0) * u
        a = 2 * math.pi * k / 32
        wav = math.sin(th * 7.5 + 2.0 * math.sin(a * 1.0))
        return 1 if (wav > 0.45 and math.sin(a) > -0.2 and u < 0.93) else 0
    shell = sweep(pts, rx, rz, [ivory, stripe, lip], verts=32, mat_fn=stripes, radial=ribs, cap_end=2, name="shell")
    parts = [shell]
    # the keel: spikes along the outer edge of the coil's top, glowing vents between them
    for j in range(14, N - 6, 9):
        p = pts[j]
        t = (pts[j + 1] - pts[j - 1]).normalized()
        side = t.cross(Vector((0, 0, 1))).normalized()
        cen = sum(pts, Vector()) / len(pts)
        if side.dot(p - cen) < 0:
            side = -side
        base = p + side * rx[j] * 0.55 + Vector((0, 0, rz[j] * 0.8))
        parts.append(cone(base, base + side * rx[j] * 0.35 + Vector((0, 0, rz[j] * 0.45)) - t * rx[j] * 0.2,
                          rx[j] * 0.12, spike_m, verts=7))
        vb = p + side * rx[j] * 0.15 + Vector((0, 0, rz[j] * 0.99))
        parts.append(ell(vb, (rx[j] * 0.07, rx[j] * 0.07, rx[j] * 0.03), vent, segs=10, rings=6))
    body = join(parts, "body")
    ap = pts[-1]
    W = rx[-1]
    # the hood: a leathery dome filling the aperture, spotted
    hood = [ell(ap + Vector((0, -0.2, 0.1)), (W * 0.85, 0.9, rz[-1] * 0.85), hood_m, segs=32, rings=16)]
    rnd = random.Random(11)
    for k in range(18):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.2, 0.85)
        p = ap + Vector((0, -0.2, 0.1)) + Vector((W * 0.85 * rr * math.cos(a), 0.9 * rr * math.sin(a) * 0.6,
                                                  rz[-1] * 0.85 * math.sqrt(max(0, 1 - rr * rr)) + 0.01))
        hood.append(ell(p, (0.12, 0.09, 0.03), hood_spot, yaw=math.degrees(a), segs=10, rings=6))
    # a fan of small tentacles under the hood's lip, curling forward
    fan = []
    for k in range(9):
        a = math.radians(-60 + 120 * k / 8)
        d = Vector((math.sin(a), -math.cos(a), 0))
        base = ap + Vector((0, -0.6, -0.15)) + d * 0.4
        ln = 1.6 + 0.4 * math.cos(a * 2)
        curl = Vector((math.cos(a), math.sin(a), 0)) * 0.25 * (1 if k % 2 else -1)
        ptsT = [base, base + d * ln * 0.4 + curl * 0.5, base + d * ln * 0.75 + curl, base + d * ln + curl * 0.4]
        fan.append(tube_pts(ptsT, 0.2, 0.0, tent, verts=10, shape=lambda u: 1 - 0.85 * u))
        for u in (0.3, 0.5, 0.7):
            P = smooth_path(ptsT, 3)
            q = P[int(u * (len(P) - 1))]
            fan.append(sphere(0.07 * (1.1 - u), q + Vector((0, 0, 0.13 * (1.1 - u))), sucker, segs=8, rings=5))
    body2 = join(hood + fan, "hood")
    body = join([body, body2], "body")
    # the arms: two long tentacles from the hood's sides (origin at the root; swing them about Godot Y)
    arms = []
    for s, nm in ((-1, "arm_l"), (1, "arm_r")):
        root = ap + Vector((s * W * 0.6, -0.6, 0.0))
        P = [root, root + Vector((s * 0.9, -1.4, 0.05)), root + Vector((s * 0.6, -2.8, 0.1)),
             root + Vector((s * -0.2, -3.6, 0.1)), root + Vector((s * -0.5, -3.4, 0.12))]
        parts = [tube_pts(P, 0.32, 0.0, tent, verts=12, shape=lambda u: 1 - 0.7 * u + (0.25 if u > 0.75 else 0)
                          * math.sin(math.pi * (u - 0.75) / 0.25))]
        PP = smooth_path(P, 6)
        for j in range(3, len(PP) - 1, 2):
            u = j / (len(PP) - 1)
            q = PP[j]
            t = (PP[j + 1] - PP[j - 1]).normalized()
            side = t.cross(Vector((0, 0, 1))).normalized()
            rr = 0.32 * (1 - 0.7 * u)
            for sg in (1, -1):
                parts.append(sphere(rr * 0.32, q + side * sg * rr * 0.55 + Vector((0, 0, rr * 0.7)), sucker, segs=8,
                                    rings=5))
        parts.append(ell(PP[-1] + Vector((0, 0, 0.1)), (0.18, 0.18, 0.12), vent, segs=12, rings=8))
        arms.append(join(parts, nm, pivot=root))
    # the eye: one great eye set in the top of the hood, looking forward and up
    E = ap + Vector((0, -0.55, rz[-1] * 0.75))
    look = Vector((0, -math.cos(math.radians(50)), math.sin(math.radians(50))))
    M4 = Matrix.Translation(E) @ look.to_track_quat("Z", "Y").to_matrix().to_4x4()
    eye = [sphere(0.6, (0, 0, 0), white, segs=32, rings=18),
           hemi(0.605, (0, 0, 0), (0, 0, 1), iris, cut=0.75, segs=32, rings=12),
           ell((0, 0, 0.6), (0.08, 0.26, 0.03), pupil, segs=14, rings=8),
           torus(0.6, 0.09, (0, 0, -0.05), lip, verts=36, minor=8)]
    for o in eye:
        o.data.transform(M4)
        o.data.update()
    eye = join(eye, "eye", pivot=E)
    # the core: the glowing siphon under the hood's lip, between the tentacles
    core = join([ell(ap + Vector((0, -1.05, 0.25)), (0.42, 0.34, 0.3), core_m, segs=20, rings=12),
                 torus(0.42, 0.08, ap + Vector((0, -1.05, 0.2)), lip, verts=28, minor=8)], "core",
                pivot=ap + Vector((0, -1.05, 0.25)))
    boss_root("boss_1", [(body, None), (core, None), (eye, None), (arms[0], None), (arms[1], None)])


def boss_2():
    """The crustacean colossus: an indigo carapace studded with bone tubercles, three tail plates and a fan, four
    legs a side, two great claws (arm_l, arm_r; their moving fingers pinch_l, pinch_r), hooked mandibles (jaw_l,
    jaw_r) under a three-eyed turret (eye); the core is a glowing organ bared in a socket on its back."""
    reset()
    shell = mat("boss2_shell", (0.2, 0.1, 0.32), 0.25, coat=1.0)
    shell2 = mat("boss2_shell_edge", (0.45, 0.2, 0.5), 0.3, coat=1.0)
    bone = mat("boss2_bone", (0.92, 0.86, 0.72), 0.3, coat=0.5)
    claw_m = mat("boss2_claw", (0.32, 0.14, 0.42), 0.22, coat=1.0)
    tipm = mat("boss2_claw_tip", (0.08, 0.03, 0.06), 0.25, coat=1.0)
    glow = mat("boss2_glow", (1.0, 0.55, 0.1), 0.3, emit=2.5, emit_color=(1.0, 0.45, 0.05))
    core_m = mat("boss2_core_glow", (1.0, 0.3, 0.6), 0.3, emit=4.0, emit_color=(1.0, 0.2, 0.55))
    eye_m = mat("boss2_eye_glow", (0.7, 1.0, 0.2), 0.2, emit=3.5, emit_color=(0.55, 1.0, 0.1))
    socket = mat("boss2_socket", (0.1, 0.03, 0.06), 0.4, coat=0.5)
    prof = [(x, z) for x, z in superellipse(1.0, 1.0, 32, 2.4) if z > -0.6]
    parts = []

    def shield(y0, y1, hw, hh, m, bulge=0.25):
        st = []
        for k in range(11):
            u = k / 10
            y = y0 + (y1 - y0) * u
            b = math.sin(math.pi * (0.05 + 0.9 * u)) ** bulge
            st.append((y, hw * b, hh * b, 0.0))
        return loft_y(prof, st, m, cap_start=True, cap_end=True, name="plate")
    # the cephalothorax shield, then three tail plates and the fan
    parts.append(shield(-1.75, 0.45, 1.9, 0.95, shell, 0.3))
    for k, (y0, y1, hw, hh) in enumerate(((0.25, 1.05, 1.55, 0.72), (0.9, 1.65, 1.3, 0.6), (1.5, 2.2, 1.05, 0.48))):
        parts.append(shield(y0, y1, hw, hh, shell if k % 2 else shell2, 0.2))
        for s in (1, -1):
            parts.append(cone((s * hw * 0.92, (y0 + y1) / 2, 0.0), (s * (hw + 0.45), (y0 + y1) / 2 + 0.25, -0.05),
                              0.12, bone, verts=7))
        parts.append(tube_pts([(-hw * 0.7, y0 + 0.08, hh * 0.72), (0, y0 + 0.02, hh * 1.0), (hw * 0.7, y0 + 0.08,
                                                                                            hh * 0.72)],
                              0.05, 0.05, glow, verts=6))
    for s in (1, 0, -1):   # the tail fan
        poly = [(0, 2.0), (0.42, 2.2), (0.55, 3.1), (0.0, 3.35), (-0.55, 3.1), (-0.42, 2.2)]
        fan = plate([(x + s * 0.75, y - abs(s) * 0.12) for x, y in poly], 0.12, 0.0, shell2 if s else shell,
                    bevel=0.04, taper=0.15)
        if s:
            fan.data.transform(Matrix.Translation((s * 0.75, 2.0, 0)) @ Matrix.Rotation(-s * 0.35, 4, "Z")
                               @ Matrix.Translation((-s * 0.75, -2.0, 0)))
        parts.append(fan)
    # tubercles and ridges on the shield, a rostrum spike
    rnd = random.Random(22)
    for k in range(40):
        x, y = rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 0.2)
        u = (y + 1.75) / 2.2
        b = math.sin(math.pi * (0.05 + 0.9 * u)) ** 0.3
        if abs(x) > 1.8 * b or (abs(x) < 0.5 and -0.6 < y < 0.15) or (abs(x) < 0.55 and y < -1.15):
            continue
        z = 0.95 * b * (1 - (abs(x) / (1.9 * b)) ** 2.4) ** (1 / 2.4)
        parts.append(ell((x, y, z), (0.07, 0.07, 0.06), bone, segs=8, rings=5))
    for s in (1, -1):
        parts.append(tube_pts([(s * 0.65, -1.55, 0.55), (s * 1.1, -0.8, 0.82), (s * 1.0, 0.0, 0.85),
                               (s * 0.75, 0.35, 0.82)], 0.06, 0.05, glow, verts=6))
    parts.append(cone((0, -1.6, 0.45), (0, -2.4, 0.4), 0.18, bone, verts=8))
    # the socket on the back where the core shows
    parts.append(torus(0.5, 0.13, (0, -0.25, 0.86), socket, verts=32, minor=8))
    for k in range(8):
        a = 2 * math.pi * k / 8
        parts.append(cone((0.55 * math.cos(a), -0.25 + 0.55 * math.sin(a), 0.86),
                          (0.82 * math.cos(a), -0.25 + 0.82 * math.sin(a), 1.1), 0.08, bone, verts=6))
    # four legs a side
    for s in (1, -1):
        for k, y in enumerate((-0.9, -0.3, 0.3, 0.9)):
            hip = Vector((s * 1.6, y, -0.1))
            knee = Vector((s * 2.35, y + 0.1 * (k - 1.5), 0.45))
            foot = Vector((s * 2.85, y + 0.3 * (k - 1.5), -0.5))
            parts.append(tube_pts([hip, knee], 0.15, 0.12, shell2, verts=10))
            parts.append(tube_pts([knee, foot], 0.12, 0.03, claw_m, verts=10))
            parts.append(sphere(0.13, knee, bone, segs=10, rings=6))
    body = join(parts, "body")
    # the eye turret: three glowing eyes on a short dome
    E0 = Vector((0, -1.35, 0.72))
    eye = [ell(E0, (0.42, 0.32, 0.25), shell2, segs=20, rings=10)]
    for k, x in enumerate((-0.2, 0.0, 0.2)):
        r = 0.13 if k == 1 else 0.1
        eye.append(sphere(r, E0 + Vector((x, -0.22 + 0.04 * abs(x) * 5, 0.12 + (0.06 if k == 1 else 0))), eye_m,
                          segs=12, rings=8))
    eye = join(eye, "eye", pivot=E0)
    # mandibles: hooks that close towards the middle (swing about Godot Y)
    jaws = []
    for s, nm in ((-1, "jaw_l"), (1, "jaw_r")):
        h = Vector((s * 0.55, -1.65, 0.1))
        P = [h, h + Vector((s * 0.15, -0.45, 0)), h + Vector((-s * 0.15, -0.85, 0)), h + Vector((-s * 0.45, -0.95, 0))]
        j = [tube_pts(P, 0.16, 0.0, claw_m, verts=10, shape=lambda u: 1 - 0.85 * u)]
        for u in (0.45, 0.65):
            PP = smooth_path(P, 4)
            q = PP[int(u * (len(PP) - 1))]
            j.append(cone(q, q + Vector((-s * 0.18, -0.02, 0)), 0.05, bone, verts=5))
        jaws.append(join(j, nm, pivot=h))
    # the claws: shoulder, upper arm, forearm, the pincer with a fixed finger; the moving finger is its child
    arms, pinches = [], []
    for s, nm in ((-1, "arm_l"), (1, "arm_r")):
        sh = Vector((s * 1.65, -1.0, 0.1))
        el = Vector((s * 2.8, -1.55, 0.35))
        wr = Vector((s * 2.75, -2.75, 0.3))
        a = [sphere(0.32, sh, shell2, segs=16, rings=10),
             tube_pts([sh, (sh + el) / 2 + Vector((0, 0, 0.15)), el], 0.3, 0.26, claw_m, verts=14),
             sphere(0.3, el, bone, segs=14, rings=8),
             tube_pts([el, (el + wr) / 2 + Vector((s * 0.1, 0, 0.1)), wr], 0.28, 0.3, claw_m, verts=14)]
        for u in (0.3, 0.7):
            q = el.lerp(wr, u)
            a.append(cone(q + Vector((s * 0.2, 0, 0.15)), q + Vector((s * 0.55, 0.15, 0.3)), 0.09, bone, verts=6))
        # the pincer's palm and fixed (inner) finger
        palm_c = wr + Vector((-s * 0.1, -0.55, 0.0))
        a.append(ell(palm_c, (0.62, 0.75, 0.42), claw_m, segs=24, rings=12))
        a.append(tube_pts([palm_c + Vector((-s * 0.3, -0.5, 0)), palm_c + Vector((-s * 0.4, -1.2, 0)),
                           palm_c + Vector((-s * 0.15, -1.75, 0))], 0.3, 0.0, claw_m, verts=12,
                          shape=lambda u: 1 - 0.9 * u))
        for k in range(4):
            q = palm_c + Vector((-s * (0.25 + 0.05 * k), -0.6 - 0.25 * k, 0.0))
            a.append(cone(q, q + Vector((s * 0.22, -0.05, 0)), 0.07, bone, verts=5))
        a.append(tube_pts([palm_c + Vector((-s * 0.5, -0.3, 0.3)), palm_c + Vector((0, 0.2, 0.42)),
                           palm_c + Vector((s * 0.5, -0.1, 0.3))], 0.05, 0.05, glow, verts=6))
        for k in range(5):
            q = palm_c + Vector((s * (0.1 + 0.08 * k), -0.2 + 0.12 * k, 0.38 - 0.03 * k))
            a.append(ell(q, (0.06, 0.06, 0.05), bone, segs=8, rings=5))
        hinge = palm_c + Vector((s * 0.35, -0.55, 0.0))
        f = [tube_pts([hinge, hinge + Vector((s * 0.05, -0.75, 0)), hinge + Vector((-s * 0.35, -1.3, 0))], 0.26, 0.0,
                      claw_m, verts=12, shape=lambda u: 1 - 0.9 * u),
             cone(hinge + Vector((-s * 0.3, -1.22, 0)), hinge + Vector((-s * 0.45, -1.4, 0)), 0.06, tipm, verts=6)]
        for k in range(3):
            q = hinge + Vector((s * 0.0, -0.35 - 0.25 * k, 0.0))
            f.append(cone(q, q + Vector((-s * 0.2, -0.04, 0)), 0.06, bone, verts=5))
        pinches.append(join(f, "pinch_" + nm[-1], pivot=hinge))
        arms.append(join(a, nm, pivot=sh))
    core = join([sphere(0.42, (0, -0.25, 0.85), core_m, segs=24, rings=14)] +
                [tube_pts([(0.42 * math.cos(a), -0.25 + 0.42 * math.sin(a), 0.85),
                           (0.25 * math.cos(a + 0.4), -0.25 + 0.25 * math.sin(a + 0.4), 1.18),
                           (0.0, -0.25, 1.26)], 0.04, 0.03, socket, verts=5) for a in
                 (k * math.pi / 3 for k in range(6))], "core", pivot=(0, -0.25, 0.85))
    boss_root("boss_2", [(body, None), (core, None), (eye, None), (jaws[0], None), (jaws[1], None),
                         (arms[0], None), (arms[1], None), (pinches[0], arms[0]), (pinches[1], arms[1])])


def eyeball(c, r, look, white, iris, pupil, lid=None, iris_cut=0.72, slit=True):
    """An eyeball at c looking along `look`: white, a glowing iris cap, a slit pupil, an optional lid ring."""
    M4 = Matrix.Translation(Vector(c)) @ Vector(look).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    parts = [sphere(r, (0, 0, 0), white, segs=20, rings=12),
             hemi(r * 1.01, (0, 0, 0), (0, 0, 1), iris, cut=iris_cut, segs=20, rings=8),
             ell((0, 0, r * 1.0), (r * 0.12, r * 0.42, r * 0.05), pupil, segs=10, rings=6) if slit else
             ell((0, 0, r * 0.99), (r * 0.25, r * 0.25, r * 0.05), pupil, segs=12, rings=6)]
    if lid is not None:
        parts.append(torus(r * 0.98, r * 0.16, (0, 0, -r * 0.05), lid, verts=24, minor=6))
    for o in parts:
        o.data.transform(M4)
        o.data.update()
    return parts


def petal_mesh(L, W, r0, z0, material, rise=0.7, droop=1.0, cup=0.35, thick=0.09, nu=16, nv=9, name="petal"):
    """A cupped petal along +X from radius r0: rises, then droops to its tip; its edges curl up."""
    grid = []
    for i in range(nu + 1):
        u = i / nu
        w = W * 0.5 * math.sin(math.pi * min(1.0, 0.08 + u * 0.95)) ** 0.65 * (1 - 0.2 * u)
        row = []
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            x = r0 + L * u
            y = v * w
            z = z0 + rise * u - droop * u * u + cup * v * v * w / (W * 0.5)
            row.append((x, y, z))
        grid.append(row)
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in grid]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    o = new_obj(name, bm, material, smooth=60)
    K.select(o)
    sm = o.modifiers.new("s", "SOLIDIFY")
    sm.thickness = thick
    sm.offset = 0
    bpy.ops.object.modifier_apply(modifier=sm.name)
    return o


def boss_3():
    """The brain-flower: eight fleshy magenta petals spread round a glowing brain (the core), each petal watching
    with its own eyes; a great eye on a stalk at the front (eye); two thorny vines whipping forward with spore
    bulbs (arm_l, arm_r); the petals are one node (petals) the view may breathe or turn."""
    reset()
    petal_m = mat("boss3_petal", (0.55, 0.08, 0.32), 0.35, coat=0.6)
    petal_in = mat("boss3_petal_inner", (0.95, 0.55, 0.65), 0.4, coat=0.4)
    vein = mat("boss3_vein_glow", (1.0, 0.4, 0.7), 0.3, emit=2.0, emit_color=(1.0, 0.25, 0.6))
    brain = mat("boss3_brain_glow", (0.95, 0.3, 0.48), 0.3, coat=0.6, emit=0.9, emit_color=(1.0, 0.2, 0.4))
    base_m = mat("boss3_stem", (0.12, 0.18, 0.08), 0.4, coat=0.5)
    thorn = mat("boss3_thorn", (0.9, 0.85, 0.65), 0.3, coat=0.4)
    white = mat("boss3_eye", (0.96, 0.93, 0.85), 0.15, coat=1.0)
    iris = mat("boss3_iris_glow", (0.5, 1.0, 0.25), 0.2, emit=3.0, emit_color=(0.4, 1.0, 0.1))
    pupil = mat("boss3_pupil", (0.01, 0.0, 0.02), 0.1, coat=1.0)
    bulb = mat("boss3_bulb_glow", (0.9, 1.0, 0.3), 0.25, emit=2.4, emit_color=(0.7, 1.0, 0.15))
    # the base: dark green sepals under the petals, with thorns
    base = [ell((0, 0, -0.35), (1.9, 1.9, 0.5), base_m, segs=32, rings=12)]
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        pm = petal_mesh(1.2, 1.1, 1.0, -0.3, base_m, rise=0.0, droop=0.3, cup=0.15, thick=0.1, name="sepal")
        move(pm, rot=(0, 0, math.degrees(a)))
        base.append(pm)
        d = Vector((math.cos(a), math.sin(a), 0))
        base.append(cone(d * 1.7 + Vector((0, 0, -0.2)), d * 2.3 + Vector((0, 0, 0.1)), 0.09, thorn, verts=6))
    body = join(base, "body")
    # the petals with their eyes and glowing veins
    pet = []
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        L = 2.5 if k % 2 == 0 else 2.15
        p = petal_mesh(L, 1.75, 1.0, 0.0, petal_m, rise=0.9, droop=1.4, cup=0.45, name="petal")
        p.data.materials.append(petal_in)
        for f in p.data.polygons:
            if f.normal.z > 0.35 and f.center.z > 0.05 and abs(f.center.y) < 0.55 * (1.2 - (f.center.x - 1.0) / L):
                f.material_index = 1
        parts = [p]
        mid = [(1.0 + L * u, 0, 0.0 + 0.9 * u - 1.4 * u * u + 0.05) for u in (0.05, 0.3, 0.55, 0.8)]
        parts.append(tube_pts(mid, 0.05, 0.02, vein, verts=6))
        for sg in (1, -1):
            side = [(1.0 + L * u, sg * (0.25 + 0.35 * u), 0.9 * u - 1.4 * u * u + 0.1 + 0.08 * u) for u in
                    (0.15, 0.35, 0.6)]
            parts.append(tube_pts(side, 0.03, 0.012, vein, verts=5))
        for u, r in ((0.42, 0.2), (0.7, 0.15)):
            x = 1.0 + L * u
            z = 0.9 * u - 1.4 * u * u + 0.1
            parts += eyeball((x, 0.0, z + r * 0.5), r, (0.25, 0, 1), white, iris, pupil, lid=petal_m)
        for o in parts:
            move(o, rot=(0, 0, math.degrees(a)))
        pet += parts
    petals = join(pet, "petals")
    # the brain: a domed mass folded into gyri
    br = sphere(1.25, (0, 0, 0.0), brain, segs=48, rings=28)
    move(br, scale=(1.0, 1.05, 0.72))

    def fold(c):
        n = c.normalized()
        g = math.sin(9 * n.x + 4 * math.sin(7 * n.y)) * math.sin(8 * n.y + 3 * math.sin(6 * n.x + 2 * n.z))
        k = 1.0 + 0.1 * g - (0.1 if abs(c.x) < 0.07 and c.z > 0 else 0.0)
        return Vector((c.x * k, c.y * k, max(c.z * k, -0.3)))
    displace(br, fold)
    move(br, (0, 0.1, 0.62))
    core = join([br], "core", pivot=(0, 0.1, 0.7))
    # stamens round the brain: glowing tips
    st = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        d = Vector((math.cos(a), math.sin(a), 0))
        if d.y < -0.8:
            continue
        P = [d * 1.15 + Vector((0, 0, 0.1)), d * 1.4 + Vector((0, 0, 0.7)), d * 1.55 + Vector((0, 0, 0.95))]
        st.append(tube_pts(P, 0.05, 0.03, base_m, verts=6))
        st.append(sphere(0.1, P[-1], bulb, segs=10, rings=6))
    body = join([body] + st, "body")
    # the great eye on a stalk at the front
    S = Vector((0, -1.35, 0.3))
    eye = [tube_pts([S, S + Vector((0, -0.25, 0.6)), S + Vector((0, -0.55, 0.95))], 0.22, 0.16, base_m, verts=12)]
    eye += eyeball(S + Vector((0, -0.62, 1.2)), 0.5, (0, -0.7, 1.0), white, iris, pupil, lid=petal_m)
    eye = join(eye, "eye", pivot=S)
    # the vines: thorny whips curling forward with a spore bulb at the tip
    arms = []
    for s, nm in ((-1, "arm_l"), (1, "arm_r")):
        r0 = Vector((s * 1.4, -1.0, -0.1))
        P = [r0, r0 + Vector((s * 1.2, -0.9, 0.2)), r0 + Vector((s * 1.5, -2.2, 0.3)),
             r0 + Vector((s * 0.9, -3.1, 0.3)),
             r0 + Vector((s * 0.2, -3.4, 0.35))]
        v = [tube_pts(P, 0.2, 0.08, base_m, verts=10)]
        PP = smooth_path(P, 6)
        for j in range(2, len(PP) - 2, 2):
            t = (PP[j + 1] - PP[j - 1]).normalized()
            side = t.cross(Vector((0, 0, 1))).normalized() * (1 if j % 4 else -1)
            rr = 0.2 - 0.12 * j / len(PP)
            v.append(cone(PP[j] + side * rr * 0.8, PP[j] + side * (rr + 0.25) + t * 0.12 + Vector((0, 0, 0.05)), 0.06,
                          thorn, verts=5))
        v.append(ell(PP[-1] + Vector((0, -0.15, 0.05)), (0.32, 0.36, 0.3), bulb, segs=16, rings=10))
        for k in range(5):
            a = 2 * math.pi * k / 5
            v.append(petal_mesh(0.35, 0.3, 0.15, 0.0, petal_m, rise=0.25, droop=0.0, cup=0.1, thick=0.05,
                                nu=6, nv=4, name="bract"))
            move(v[-1], PP[-1] + Vector((0, -0.15, -0.05)), rot=(0, 0, math.degrees(a)))
        arms.append(join(v, nm, pivot=r0))
    boss_root("boss_3", [(body, None), (petals, None), (core, None), (eye, None), (arms[0], None), (arms[1], None)])


def boss_4():
    """The bio-mechanical serpent head: a gunmetal skull of overlapping plates over red flesh, chrome blade fins
    down its back and swept horns, a cobra hood of chrome ribs and dark flesh with glowing eyespots, a visor of six
    glowing lenses and two angry brow slits (eye), two side mandibles with steel teeth that swing open sideways
    (jaw_l, jaw_r), a glowing reactor throat between them (core), two vertebrae of its neck trailing behind (+Y)."""
    reset()
    metal = mat("boss4_metal", (0.28, 0.3, 0.34), 0.3, metal=0.85)
    metal2 = mat("boss4_metal_dark", (0.1, 0.11, 0.13), 0.35, metal=0.7)
    chrome = mat("boss4_chrome", (0.8, 0.82, 0.86), 0.18, metal=1.0)
    flesh = mat("boss4_flesh", (0.5, 0.06, 0.1), 0.35, coat=0.7)
    tooth = mat("boss4_tooth", (0.85, 0.85, 0.88), 0.2, metal=0.9)
    glow = mat("boss4_glow", (1.0, 0.25, 0.1), 0.3, emit=2.6, emit_color=(1.0, 0.15, 0.04))
    lens = mat("boss4_eye_glow", (1.0, 0.85, 0.2), 0.2, emit=4.0, emit_color=(1.0, 0.7, 0.05))
    core_m = mat("boss4_core_glow", (0.5, 1.0, 1.0), 0.2, emit=4.0, emit_color=(0.2, 0.95, 1.0))
    prof = [(x, z) for x, z in superellipse(1.0, 1.0, 32, 2.3) if z > -0.5]
    parts = []
    # the flesh under the skull
    parts.append(ell((0, -0.6, -0.1), (1.4, 2.0, 0.55), flesh, segs=28, rings=14))

    def plate_y(y0, y1, hw0, hw1, hh0, hh1, m, z=0.0):
        st = []
        for k in range(9):
            u = k / 8
            b = math.sin(math.pi * (0.04 + 0.92 * u)) ** 0.18
            st.append((y0 + (y1 - y0) * u, (hw0 + (hw1 - hw0) * u) * b, (hh0 + (hh1 - hh0) * u) * b, z))
        return loft_y(prof, st, m, cap_start=True, cap_end=True, name="skull")
    # the skull: four overlapping plates from the snout back, each stepped up over the last
    for k, (y0, y1, w0, w1, h0, h1, z) in enumerate(((-2.75, -1.7, 0.55, 0.95, 0.4, 0.62, 0.0),
                                                     (-1.95, -0.85, 0.95, 1.4, 0.6, 0.8, 0.04),
                                                     (-1.05, 0.05, 1.4, 1.5, 0.8, 0.9, 0.08),
                                                     (-0.15, 0.85, 1.45, 1.1, 0.9, 0.7, 0.04))):
        parts.append(plate_y(y0, y1, w0, w1, h0, h1, metal if k % 2 == 0 else metal2, z))
    # the visor slot (the eye node sits in it)
    parts.append(ell((0, -1.55, 0.58), (0.95, 0.22, 0.12), metal2, segs=24, rings=8))
    # blade fins down the back, glowing seams, rivets
    for k, y in enumerate((-1.2, -0.6, 0.0, 0.6)):
        h = 0.6 - 0.08 * k
        fin = plate([(0.0, y - 0.25), (0.0, y + 0.35), (h, y + 0.5)], 0.08, 0.0, chrome, bevel=0.02, taper=0.0)
        fin.data.transform(Matrix.Translation((0, 0, 0.9 - 0.04 * k)) @ Matrix.Rotation(-R90, 4, "Y"))
        fin.data.update()
        parts.append(fin)
    for s in (1, -1):
        parts.append(tube_pts([(s * 0.5, -2.6, 0.32), (s * 0.95, -1.7, 0.55), (s * 1.35, -0.6, 0.7),
                               (s * 1.3, 0.4, 0.6)], 0.045, 0.045, glow, verts=6))
        for k in range(5):
            y = -2.3 + 0.6 * k
            w = min(1.4, 0.6 + 0.45 * k)
            parts.append(sphere(0.06, (s * w * 0.8, y, 0.5 + 0.08 * k if k < 4 else 0.75), chrome, segs=8, rings=5))
        # cheek pistons running back to the jaw hinges
        parts.append(rod((s * 1.25, -1.2, 0.1), (s * 1.55, 0.2, 0.15), 0.1, chrome, verts=10))
        parts.append(rod((s * 1.55, 0.2, 0.15), (s * 1.6, 0.6, 0.15), 0.16, metal2, verts=10))
    # the hood: a cobra fan of chrome ribs behind the skull, dark flesh between them with glowing eyespots
    hood_m = mat("boss4_hood", (0.32, 0.03, 0.07), 0.4, coat=0.6)
    spot = mat("boss4_spot_glow", (1.0, 0.45, 0.05), 0.3, emit=2.2, emit_color=(1.0, 0.35, 0.02))
    for s in (1, -1):
        half = [(0.9, -0.5), (1.9, -0.45), (2.75, 0.0), (3.2, 0.7), (3.15, 1.45), (2.65, 2.05), (1.75, 2.4),
                (0.8, 2.35), (0.45, 1.2)]
        outline = curve_pts(half, 3, closed=True)
        mem = plate([(s * x, y) for x, y in outline], 0.06, 0.0, hood_m, bevel=0.02, taper=0.0)
        displace(mem, lambda c, s=s: c + Vector((0, 0, 0.12 * math.sin(abs(c.x) * 2.2) - 0.08 * abs(c.x) + 0.25)))
        parts.append(mem)
        hub = Vector((s * 0.6, 0.9, 0.38))
        for k, (x, y) in enumerate(half[1:8]):
            tip = Vector((s * x * 0.98, y * 0.98 + 0.02, 0.0))
            tip.z = 0.12 * math.sin(abs(tip.x) * 2.2) - 0.08 * abs(tip.x) + 0.25 + 0.06
            mid = hub.lerp(tip, 0.5) + Vector((0, 0, 0.12))
            parts.append(tube_pts([hub, mid, tip], 0.085, 0.03, chrome, verts=8))
            parts.append(cone(tip, tip + (tip - hub).normalized() * 0.35 + Vector((0, 0, -0.05)), 0.05, chrome,
                              verts=6))
            if 1 <= k <= 5:
                c = hub.lerp(tip, 0.68)
                parts.append(ell(c + Vector((0, 0, 0.05)), (0.17, 0.17, 0.04), spot, segs=12, rings=6))
        # swept-back horns from the skull's rear corners
        parts.append(tube_pts([(s * 1.25, -0.6, 0.75), (s * 1.75, -0.1, 0.95), (s * 2.0, 0.6, 1.05)], 0.2, 0.0,
                              chrome, verts=10, shape=lambda u: 1 - 0.95 * u))
    # the neck behind the hood: two vertebrae with cables
    for k in range(2):
        y = 2.35 + 0.85 * k
        r = 0.85 - 0.18 * k
        parts.append(ell((0, y, -0.05), (r * 0.95, 0.42, r * 0.6), flesh, segs=24, rings=12))
        parts.append(plate_y(y - 0.45, y + 0.3, r * 1.15, r * 1.0, r * 0.72, r * 0.62, metal if k % 2 else metal2))
        parts.append(tube_pts([(-r * 0.7, y - 0.4, r * 0.45), (0, y - 0.45, r * 0.75), (r * 0.7, y - 0.4, r * 0.45)],
                              0.04, 0.04, glow, verts=6))
    body = join(parts, "body")
    # the visor: six lenses in a row (the eye node)
    eye = []
    for k in range(6):
        x = -0.75 + 0.3 * k
        eye.append(ell((x, -1.62, 0.66 - 0.05 * abs(x)), (0.11, 0.1, 0.07), lens, segs=12, rings=8))
    for s in (1, -1):   # two angry slits on the brow
        eye.append(ell((s * 1.05, -1.25, 0.7), (0.32, 0.12, 0.08), lens, yaw=-s * 28, segs=16, rings=8))
    eye = join(eye, "eye", pivot=(0, -1.6, 0.6))
    # the jaws: side mandibles hinged at the back of the cheeks, closing along the snout
    jaws = []
    for s, nm in ((-1, "jaw_l"), (1, "jaw_r")):
        h = Vector((s * 1.45, 0.3, -0.05))
        P = [h, h + Vector((s * 0.1, -1.2, 0.0)), h + Vector((-s * 0.3, -2.5, 0.0)),
             h + Vector((-s * 0.95, -3.45, 0.0))]
        j = [sweep(smooth_path(P, 5), [0.42 * (1 - 0.7 * i / 15) for i in range(16)],
                   [0.3 * (1 - 0.6 * i / 15) for i in range(16)], [metal2], verts=16, name="jaw")]
        j.append(sweep(smooth_path(P[:3], 4), [0.3] * 9, [0.12] * 9, [metal], verts=12, name="jawplate"))
        move(j[-1], (0, 0, 0.2))
        PP = smooth_path(P, 5)
        for i in range(3, len(PP) - 1):
            t = (PP[i + 1] - PP[i - 1]).normalized()
            inward = Vector((0, 0, 1)).cross(t).normalized() * (-s if t.y < 0 else s)
            if inward.x * s > 0:
                inward = -inward
            rr = 0.42 * (1 - 0.7 * i / 15)
            j.append(cone(PP[i] + inward * rr * 0.7, PP[i] + inward * (rr + 0.28) - t * 0.05, 0.07, tooth, verts=6))
        j.append(cone(PP[-1], PP[-1] + (PP[-1] - PP[-2]).normalized() * 0.4, 0.13, tooth, verts=8))
        j.append(tube_pts([PP[1] + Vector((0, 0, 0.27)), PP[6] + Vector((0, 0, 0.25)), PP[10] + Vector((0, 0, 0.18))],
                          0.035, 0.03, glow, verts=6))
        jaws.append(join(j, nm, pivot=h))
    # the reactor throat between the jaws, in front of the snout
    C = Vector((0, -3.0, 0.05))
    core = [sphere(0.45, C, core_m, segs=24, rings=14),
            torus(0.48, 0.08, C + Vector((0, 0.05, 0)), chrome, rot=(R90, 0, 0), verts=28, minor=8),
            torus(0.42, 0.06, C, metal2, verts=28, minor=6)]
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        core.append(rod(C + Vector((0.5 * math.cos(a), 0.35, 0.5 * math.sin(a))),
                        C + Vector((0.3 * math.cos(a), 0.9, 0.3 * math.sin(a))), 0.06, chrome, verts=8))
    core = join(core, "core", pivot=C)
    boss_root("boss_4", [(body, None), (core, None), (eye, None), (jaws[0], None), (jaws[1], None)])


def boss_5():
    """The hive heart: a pulsing organic reactor. A great glowing heart (core) bound in a ring of chitin and steel
    with clamps, arteries and pipes spreading to the cavern; two armoured shutters hinged at the ring's sides
    (jaw_l, jaw_r: modelled open, lying outward; swing them about Godot Z to close over the heart); two tentacle
    cannons at the front (arm_l, arm_r); a cluster eye on a stalk (eye)."""
    reset()
    flesh = mat("boss5_flesh", (0.5, 0.1, 0.15), 0.35, coat=0.6)
    flesh2 = mat("boss5_flesh_dark", (0.22, 0.04, 0.07), 0.45, coat=0.4)
    chitin = mat("boss5_chitin", (0.18, 0.08, 0.2), 0.22, coat=1.0)
    steel = mat("boss5_steel", (0.55, 0.58, 0.62), 0.25, metal=0.9)
    vein = mat("boss5_vein_glow", (1.0, 0.35, 0.15), 0.3, emit=2.2, emit_color=(1.0, 0.25, 0.08))
    heart_m = mat("boss5_core_glow", (0.72, 0.06, 0.1), 0.3, coat=0.7, emit=0.55, emit_color=(1.0, 0.12, 0.08))
    artery = mat("boss5_artery", (0.6, 0.06, 0.1), 0.3, coat=0.8)
    white = mat("boss5_eye", (0.95, 0.92, 0.85), 0.15, coat=1.0)
    iris = mat("boss5_iris_glow", (0.3, 1.0, 0.9), 0.2, emit=3.0, emit_color=(0.15, 1.0, 0.8))
    pupil = mat("boss5_pupil", (0.01, 0.0, 0.0), 0.1, coat=1.0)
    muzzle = mat("boss5_muzzle_glow", (1.0, 0.8, 0.3), 0.3, emit=3.5, emit_color=(1.0, 0.6, 0.1))
    parts = []
    # a fleshy bed, the chitin-and-steel ring round the heart with six clamps
    bed = lathe_r([(0.0, -0.2), (2.4, -0.25), (3.3, -0.45), (3.6, -0.7), (0.0, -0.7)], flesh2, segs=48, name="bed",
                  radial=lambda k, z: 1 + 0.05 * math.sin(k * 0.9) * (z < -0.3))
    parts.append(bed)
    parts.append(torus(2.2, 0.38, (0, 0, 0.0), chitin, verts=64, minor=12))
    parts.append(torus(2.2, 0.2, (0, 0, 0.3), steel, verts=64, minor=8))
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        cl = box((0.55, 0.85, 0.5), (0, 0, 0), steel, bevel=0.08, segs=2)
        move(cl, d * 2.2 + Vector((0, 0, 0.25)), rot=(0, 0, math.degrees(a)))
        parts.append(cl)
        parts.append(sphere(0.14, d * 2.2 + Vector((0, 0, 0.55)), vein, segs=10, rings=6))
        # a pipe and an artery out to the walls
        parts.append(tube_pts([d * 2.5 + Vector((0, 0, 0.2)), d * 3.1 + Vector((0, 0, 0.1)),
                               d * 3.8 + Vector((0, 0, -0.3)),
                               d * 4.3 + Vector((0, 0, -0.55))], 0.16, 0.16, steel, verts=10))
        for sg in (1, -1):
            dd = Vector((math.cos(a + sg * 0.32), math.sin(a + sg * 0.32), 0))
            parts.append(tube_pts([dd * 2.0 + Vector((0, 0, -0.1)), dd * 2.9 + Vector((0, 0, -0.2)),
                                   dd * 3.7 + Vector((0, 0, -0.45)), dd * 4.2 + Vector((0, 0, -0.65))], 0.2, 0.08,
                                  artery, verts=9))
    # pump bladders behind, between the clamps
    for k in range(3):
        a = math.pi / 2 + (k - 1) * 0.62
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(ell(d * 3.0 + Vector((0, 0, 0.0)), (0.55, 0.55, 0.45), flesh, segs=18, rings=10))
        parts.append(tube_pts([d * 2.55 + Vector((0, 0, 0.35)), d * 3.0 + Vector((0, 0, 0.5)),
                               d * 3.45 + Vector((0, 0, 0.3))],
                              0.05, 0.04, vein, verts=6))
    body = join(parts, "body")
    # the heart: lumpy, veined, glowing
    h = sphere(1.55, (0, 0, 0), heart_m, segs=40, rings=24)
    displace(h, lambda c: c * (1 + 0.1 * noise3(c, 2, 2.2) + 0.03 * noise3(c, 7, 6.0)))
    move(h, (0, 0.0, 0.35), scale=(1.0, 1.0, 0.75))
    hp = [h]
    rnd = random.Random(55)
    for k in range(12):
        a = 2 * math.pi * k / 12 + rnd.uniform(-0.2, 0.2)
        pts = []
        for j in range(5):
            el = math.radians(80 - 18 * j)
            aa = a + 0.25 * math.sin(j * 1.7 + k)
            pts.append((1.6 * math.cos(el) * math.cos(aa), 1.6 * math.cos(el) * math.sin(aa), 0.35 + 1.2 * math.sin(el)
                        * 0.75 * (1 - 0.02 * j)))
        hp.append(tube_pts(pts[::-1], 0.08, 0.03, artery, verts=7))
        hp.append(tube_pts([Vector(q) * 1.015 for q in pts[::-1][:3]], 0.035, 0.02, vein, verts=5))
    for k in range(3):   # the great vessels leaving the top towards the back, open and dark
        a = math.pi / 2 + (k - 1) * 0.55
        d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((0, 0, 1.25)) + d * 0.65
        top = base + d * 0.45 + Vector((0, 0, 0.35))
        hp.append(tube_pts([base, base + d * 0.15 + Vector((0, 0, 0.3)), top], 0.22 - 0.04 * k, 0.18 - 0.03 * k,
                           artery, verts=12, caps=False))
        m4 = Matrix.Translation(top) @ (top - base).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        rim = torus(0.17 - 0.03 * k, 0.04, (0, 0, 0), artery, verts=16, minor=6)
        hole = flat_disc(0.15 - 0.03 * k, -0.02, flesh2, verts=16)
        for o in (rim, hole):
            o.data.transform(m4)
            o.data.update()
        hp += [rim, hole]
    core = join(hp, "core", pivot=(0, 0, 0.35))
    # the shutters: two armoured quarter-domes over the heart (closed they meet over its top along the middle),
    # hinged along Y on the ring's sides; modelled open, flipped outward by OPEN degrees
    OPEN = 115
    RS = 1.85
    jaws = []
    for s, nm in ((-1, "jaw_l"), (1, "jaw_r")):
        sh = hemi(RS, (0, 0, 0), (0, 0, 1), chitin, cut=0.0, segs=40, rings=16)
        bm = bmesh.new()
        bm.from_mesh(sh.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x * s < -1e-4], context="VERTS")
        bm.to_mesh(sh.data)
        bm.free()
        K.select(sh)
        sm = sh.modifiers.new("s", "SOLIDIFY")
        sm.thickness = 0.14
        bpy.ops.object.modifier_apply(modifier=sm.name)
        sh = K.finish(sh, chitin, smooth=50)
        parts = [sh]
        for y in (-1.0, 0.0, 1.0):   # steel ribs over the shell, hinge to seam
            r = math.sqrt(RS * RS - y * y) + 0.05
            parts.append(tube([(s * r * math.cos(math.radians(e)), y, r * math.sin(math.radians(e)))
                               for e in range(0, 91, 10)], [0.07] * 10, steel, verts=8, caps=True, name="rib"))
        parts.append(tube([(s * 0.03, (RS + 0.04) * math.cos(math.radians(t)), (RS + 0.04) * math.sin(math.radians(t)))
                           for t in range(0, 181, 10)], [0.08] * 19, steel, verts=8, caps=True, name="seam"))
        for y, e in ((-0.5, 40), (0.5, 40), (-1.2, 25), (1.2, 25), (0.0, 62)):   # spikes between the ribs
            r = math.sqrt(RS * RS - y * y)
            q = Vector((s * r * math.cos(math.radians(e)), y, r * math.sin(math.radians(e))))
            n = q.normalized()
            parts.append(cone(q, q + n * 0.5, 0.13, steel, verts=6))
        for y in (-0.5, 0.5):
            r = math.sqrt(RS * RS - y * y)
            q = Vector((s * r * math.cos(math.radians(70)), y, r * math.sin(math.radians(70))))
            parts.append(ell(q + q.normalized() * 0.05, (0.12, 0.12, 0.05), vein, segs=10, rings=6))
        o = join(parts, nm)
        hinge = Vector((s * RS, 0, 0.35))
        o.data.transform(Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(s * OPEN), 4, "Y")
                         @ Matrix.Translation((-s * RS, 0, 0)))
        o.data.update()
        jaws.append(join([o], nm, pivot=hinge))
    # the cannons: two tentacle guns at the front, mouths glowing
    arms = []
    for s, nm in ((-1, "arm_l"), (1, "arm_r")):
        r0 = Vector((s * 2.1, -1.4, 0.2))
        P = [r0, r0 + Vector((s * 0.4, -0.8, 0.1)), r0 + Vector((s * 0.2, -1.8, 0.15)), r0 + Vector((0, -2.5, 0.15))]
        a = [tube_pts(P, 0.42, 0.3, flesh, verts=14)]
        PP = smooth_path(P, 4)
        for j in range(1, len(PP) - 1, 2):
            t = (PP[j + 1] - PP[j - 1]).normalized()
            tr = torus(0.4 - 0.015 * j, 0.07, (0, 0, 0), chitin, verts=20, minor=6)
            tr.data.transform(Matrix.Translation(PP[j]) @ t.to_track_quat("Z", "Y").to_matrix().to_4x4())
            a.append(tr)
        t = (PP[-1] - PP[-2]).normalized()
        m4 = Matrix.Translation(PP[-1]) @ t.to_track_quat("Z", "Y").to_matrix().to_4x4()
        for o in (torus(0.3, 0.1, (0, 0, 0), flesh2, verts=20, minor=8), sphere(0.24, (0, 0, -0.05), muzzle, segs=14,
                                                                                    rings=8)):
            o.data.transform(m4)
            o.data.update()
            a.append(o)
        arms.append(join(a, nm, pivot=r0))
    # the eye cluster on a stalk at the front of the ring
    S = Vector((0, -2.25, 0.2))
    eye = [tube_pts([S, S + Vector((0, -0.3, 0.5)), S + Vector((0, -0.55, 0.85))], 0.28, 0.2, flesh, verts=12)]
    eye += eyeball(S + Vector((0, -0.62, 1.05)), 0.4, (0, -0.8, 1.0), white, iris, pupil, lid=chitin)
    for s in (1, -1):
        eye += eyeball(S + Vector((s * 0.42, -0.45, 0.8)), 0.2, (s * 0.4, -0.8, 1.0), white, iris, pupil, lid=chitin)
    eye = join(eye, "eye", pivot=S)
    boss_root("boss_5", [(body, None), (core, None), (jaws[0], None), (jaws[1], None), (arms[0], None),
                         (arms[1], None), (eye, None)])


# ------------------------------------------------------------------ pickups (lying flat, their faces up: Godot +Y)

def credit():
    """A bubble-coin: an amber coin stamped with a cell (a ring and its nucleus), floating inside a clear bubble."""
    reset()
    coin_m = mat("credit_glow", (1.0, 0.55, 0.05), 0.25, metal=0.6, emit=0.9, emit_color=(1.0, 0.45, 0.02))
    mark = mat("credit_mark_glow", (1.0, 0.95, 0.7), 0.2, emit=4.0, emit_color=(1.0, 0.85, 0.45))
    bub = mat("credit_bubble", (0.6, 0.9, 1.0), 0.03, coat=1.0, alpha=0.14, emit=0.15,
              emit_color=(0.3, 0.8, 1.0))
    shine = mat("credit_shine_glow", (1.0, 1.0, 1.0), 0.1, emit=3.0)
    parts = [cyl(0.19, 0.07, (0, 0, 0), coin_m, verts=36, bevel=0.02, segs=3),
             torus(0.19, 0.022, (0, 0, 0), coin_m, verts=36, minor=8)]
    for zs in (1, -1):
        parts += [torus(0.105, 0.016, (0, 0, zs * 0.036), mark, verts=28, minor=6),
                  sphere(0.042, (0.012, 0.01, zs * 0.034), mark, scale=(1, 1, 0.45), segs=12, rings=6)]
        for k in range(3):   # tiny organelles
            a = 2 * math.pi * k / 3 + 0.5
            parts.append(sphere(0.014, (0.065 * math.cos(a), 0.065 * math.sin(a), zs * 0.036), mark,
                                scale=(1, 1, 0.5), segs=8, rings=4))
    coin = join(parts, "coin")
    bubble = join([sphere(0.29, (0, 0, 0), bub, segs=28, rings=16),
                   ell((-0.12, 0.1, 0.22), (0.07, 0.035, 0.02), shine, yaw=40, segs=10, rings=6)], "bubble")
    root = empty("credit")
    export_anim(root, "credit", [(coin, root), (bubble, root)], anim=False)


def power(name, col, emblem):
    """A power-up seed: a chrome hexagon framing a glowing coloured disc with a raised emblem."""
    reset()
    M = ship_mats()
    disc = mat("%s_glow" % name, tuple(0.5 * c for c in col), 0.25, coat=1.0, emit=0.45, emit_color=col)
    em = mat("%s_mark_glow" % name, tuple(0.55 + 0.45 * c for c in col), 0.2, emit=4.0,
             emit_color=tuple(0.5 + 0.5 * c for c in col))
    hexo = [(0.3 * math.cos(math.pi / 6 + k * math.pi / 3), 0.3 * math.sin(math.pi / 6 + k * math.pi / 3)) for k in
            range(6)]
    hexi = [(x * 0.78, y * 0.78) for x, y in hexo]
    frame = plate(hexo, 0.1, 0.0, M["chrome"], bevel=0.025, taper=0.04)
    parts = [frame, plate(hexi, 0.104, 0.002, disc, bevel=0.01)]
    for x, y in hexo:   # teal studs at the corners
        parts.append(sphere(0.025, (x * 0.9, y * 0.9, 0.05), M["vein"], segs=8, rings=6))
    for o in emblem(em):
        parts.append(o)
    export(join(parts, name), name)


def emblem_gun(m):
    out = []
    for dx, ln in ((-0.075, 0.12), (0.0, 0.17), (0.075, 0.12)):
        out.append(tube_pts([(dx, -0.09, 0.07), (dx, -0.09 + ln, 0.07)], 0.022, 0.022, m, verts=8))
        out.append(cone((dx, -0.09 + ln, 0.07), (dx, -0.09 + ln + 0.06, 0.07), 0.034, m, verts=8))
    return out


def emblem_speed(m):
    out = []
    for dy in (-0.07, 0.02):
        poly = [(0.0, dy + 0.1), (0.12, dy - 0.0), (0.12, dy - 0.05), (0.0, dy + 0.045), (-0.12, dy - 0.05),
                (-0.12, dy - 0.0)]
        out.append(plate(poly, 0.03, 0.065, m, bevel=0.008))
    return out


def emblem_shield(m):
    poly = xmirror_pts([(0.0, 0.13), (0.11, 0.1), (0.11, 0.0), (0.06, -0.09), (0.0, -0.13)])
    inner = [(x * 0.62, y * 0.62 + 0.005) for x, y in poly]
    o = plate(poly, 0.03, 0.065, m, bevel=0.008)
    hole = plate(inner, 0.05, 0.08, mat("power_shield_inner", (0.15, 0.2, 0.6), 0.3, coat=0.8), bevel=0.0)
    return [o, hole]


def emblem_life(m):
    """A little ship: the extra life."""
    half = [(0.0, 0.14), (0.028, 0.06), (0.05, 0.0), (0.13, -0.07), (0.13, -0.11), (0.05, -0.08), (0.04, -0.12),
            (0.0, -0.1)]
    return [plate(xmirror_pts(half), 0.03, 0.065, m, bevel=0.006)]


def power_gun():
    power("power_gun", (1.0, 0.4, 0.06), emblem_gun)


def power_speed():
    power("power_speed", (1.0, 0.85, 0.1), emblem_speed)


def power_shield():
    power("power_shield", (0.35, 0.45, 1.0), emblem_shield)


def power_life():
    power("power_life", (0.3, 1.0, 0.35), emblem_life)


# ------------------------------------------------------------------ the shop keeper

def shop_keeper():
    """The trader: a lavender alien with a bulbous head, two big amber eyes and a third on a stalk, a monocle,
    floppy fin ears with gold rings, a tentacle moustache, a tiny top hat, a magenta waistcoat with gold buttons and
    a coin necklace, three-fingered hands rubbing together. Facing -Y (Godot +Z, the shop camera)."""
    reset()
    skin = mat("keeper_skin", (0.62, 0.45, 0.78), 0.45, coat=0.3)
    skin2 = mat("keeper_skin_light", (0.85, 0.72, 0.9), 0.5, coat=0.2)
    white = mat("keeper_eye", (0.98, 0.96, 0.9), 0.15, coat=1.0)
    iris = mat("keeper_iris_glow", (1.0, 0.65, 0.1), 0.2, emit=1.2, emit_color=(1.0, 0.5, 0.05))
    pupil = mat("keeper_pupil", (0.02, 0.01, 0.03), 0.1, coat=1.0)
    mouth = mat("keeper_mouth", (0.3, 0.05, 0.12), 0.5)
    tooth = mat("keeper_tooth", (1.0, 0.97, 0.88), 0.3, coat=0.5)
    gold = mat("keeper_gold", (1.0, 0.75, 0.25), 0.22, metal=0.95)
    glass = mat("keeper_monocle", (0.8, 0.95, 1.0), 0.02, coat=1.0, alpha=0.3)
    vest = mat("keeper_vest", (0.62, 0.06, 0.38), 0.4, coat=0.4)
    vest2 = mat("keeper_vest_trim", (0.2, 0.03, 0.15), 0.4, coat=0.4)
    shirt = mat("keeper_shirt", (0.95, 0.92, 0.85), 0.6)
    hat_m = mat("keeper_hat", (0.06, 0.05, 0.08), 0.35, coat=0.6)
    gem = mat("keeper_gem_glow", (0.2, 1.0, 0.85), 0.15, emit=2.0, emit_color=(0.1, 1.0, 0.8))
    HC = Vector((0, 0, 1.3))
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "chest": ((0, 0, 0.2), (0, 0, 0.85), "root"),
             "head": ((0, 0, 0.9), (0, 0, 1.6), "chest"),
             "jaw": ((0, -0.08, 1.12), (0, -0.4, 1.02), "head"),
             "eye.L": ((0.17, -0.3, 1.36), (0.17, -0.45, 1.36), "head"),
             "eye.R": ((-0.17, -0.3, 1.36), (-0.17, -0.45, 1.36), "head"),
             "ear.L": ((0.42, 0.0, 1.35), (0.75, 0.05, 1.18), "head"),
             "ear.R": ((-0.42, 0.0, 1.35), (-0.75, 0.05, 1.18), "head"),
             "hat": ((-0.1, 0.04, 1.74), (-0.1, 0.04, 2.08), "head"),
             "arm.L": ((0.5, 0.0, 0.7), (0.42, -0.3, 0.35), "chest"),
             "arm.R": ((-0.5, 0.0, 0.7), (-0.42, -0.3, 0.35), "chest"),
             "hand.L": ((0.42, -0.3, 0.35), (0.15, -0.45, 0.33), "arm.L"),
             "hand.R": ((-0.42, -0.3, 0.35), (-0.15, -0.45, 0.33), "arm.R")}
    stalk = chain(bones, "stalk", [(0.2, -0.12, 1.6), (0.25, -0.17, 1.76), (0.31, -0.26, 1.84)], 2, "head")
    stache = {}
    for s, side in ((1, "L"), (-1, "R")):
        stache[side] = chain(bones, "stache.%s" % side, [(s * 0.06, -0.47, 1.2), (s * 0.2, -0.5, 1.16),
                                                         (s * 0.33, -0.45, 1.06), (s * 0.36, -0.4, 0.97)], 2, "head")
    rig = Rig(bones)
    # the head: a bulbous cranium over a broad muzzle
    head = ell(HC + Vector((0, 0.02, 0.08)), (0.46, 0.44, 0.48), skin, segs=32, rings=18)
    muzzle = ell(HC + Vector((0, -0.24, -0.16)), (0.3, 0.24, 0.17), skin2, segs=24, rings=12)
    rig.rigid("head", head, muzzle)
    # eyes: big amber eyes under heavy brows; the monocle on the right
    for s, side in ((1, "L"), (-1, "R")):
        c = Vector((s * 0.17, -0.33, 1.36))
        e = [ell(c, (0.12, 0.1, 0.13), white, segs=18, rings=12),
             ell(c + Vector((0, -0.07, 0.0)), (0.075, 0.04, 0.085), iris, segs=14, rings=8),
             ell(c + Vector((0, -0.1, 0.0)), (0.025, 0.02, 0.06), pupil, segs=10, rings=6),
             sphere(0.022, c + Vector((s * 0.03, -0.11, 0.045)), tooth, segs=6, rings=4)]
        rig.rigid("eye." + side, e)
        brow = [c + Vector((s * dx, -0.06 - 0.02 * (1 - abs(dx) * 6),
                            0.15 + 0.03 * math.sin(math.pi * (dx + 0.08) / 0.2)))
                for dx in (-0.08, -0.02, 0.04, 0.1)]
        rig.rigid("head", tube_pts(brow, 0.032, 0.022, skin, verts=8))
    mono = [torus(0.13, 0.016, (0, 0, 0), gold, rot=(R90, 0, 0), verts=28, minor=6),
            cyl(0.125, 0.008, (0, 0, 0), glass, rot=(R90, 0, 0), verts=28)]
    for o in mono:
        move(o, (-0.17, -0.45, 1.36))
    chainp = [(-0.3, -0.45, 1.33), (-0.36, -0.4, 1.15), (-0.32, -0.33, 0.95), (-0.25, -0.38, 0.8)]
    mono.append(tube_pts(chainp, 0.007, 0.007, gold, verts=5))
    rig.rigid("head", mono)
    # the third eye on its stalk
    stalk_mesh = tube_pts([(0.19, -0.1, 1.53), (0.25, -0.17, 1.76), (0.31, -0.26, 1.84)], 0.04, 0.03, skin, verts=10)
    rig.smooth(stalk, stalk_mesh)
    se = Vector((0.32, -0.29, 1.88))
    rig.rigid(stalk[-1], [sphere(0.07, se, white, segs=14, rings=8),
                          ell(se + Vector((0, -0.05, 0)), (0.04, 0.03, 0.045), iris, segs=10, rings=6),
                          ell(se + Vector((0, -0.07, 0)), (0.015, 0.012, 0.03), pupil, segs=8, rings=4)])
    # the mouth: a wide grin in the jaw, a few teeth
    jaw = [ell(HC + Vector((0, -0.2, -0.27)), (0.26, 0.2, 0.09), skin2, segs=22, rings=10),
           ell(HC + Vector((0, -0.36, -0.2)), (0.2, 0.06, 0.035), mouth, segs=18, rings=8)]
    for k, x in enumerate((-0.12, -0.04, 0.05, 0.13)):
        jaw.append(cone((x, -0.4, -0.185 + HC.z), (x, -0.41, -0.15 + HC.z), 0.022 if k % 3 else 0.028, tooth, verts=6))
    rig.rigid("jaw", jaw)
    upper = [ell(HC + Vector((0, -0.37, -0.165)), (0.21, 0.05, 0.03), mouth, segs=18, rings=8)]
    upper.append(cone((0.08, -0.42, HC.z - 0.15), (0.08, -0.43, HC.z - 0.21), 0.025, tooth, verts=6))   # a snaggle
    rig.rigid("head", upper)
    # the moustache: two tentacle whiskers
    for s, side in ((1, "L"), (-1, "R")):
        pts = [(s * 0.04, -0.47, 1.2), (s * 0.2, -0.5, 1.16), (s * 0.33, -0.45, 1.06), (s * 0.36, -0.4, 0.97)]
        rig.smooth(stache[side], tube_pts(pts, 0.03, 0.008, skin, verts=8))
    # the ears: floppy fins with gold rings
    for s, side in ((1, "L"), (-1, "R")):
        poly = [(0.0, 0.0), (0.18, 0.09), (0.36, 0.06), (0.42, -0.08), (0.3, -0.16), (0.12, -0.12)]
        ear = plate([(s * x, z) for x, z in curve_pts(poly, 3, closed=True)], 0.07, 0.0, skin, bevel=0.025,
                    taper=0.15)
        ear.data.transform(Matrix.Translation((s * 0.4, 0.0, 1.38)) @ Matrix.Rotation(R90, 4, "X")
                           @ Matrix.Rotation(-s * 0.2, 4, "Y"))
        ear.data.update()
        rings = [torus(0.04, 0.009, (s * 0.67, -0.02, 1.25 + 0.05 * k), gold, rot=(0, R90, 0), verts=14, minor=4)
                 for k in range(2)]
        rig.rigid("ear." + side, ear, rings)
    # the hat: a tiny top hat with a glowing gem in its band
    hat = [cyl(0.22, 0.035, (-0.1, 0.04, 1.76), hat_m, verts=32, bevel=0.012),
           cyl(0.14, 0.32, (-0.1, 0.04, 1.93), hat_m, verts=28, bevel=0.012, r2=0.155),
           cyl(0.143, 0.06, (-0.1, 0.04, 1.81), vest, verts=28),
           ell((-0.1, -0.1, 1.81), (0.035, 0.015, 0.035), gem, segs=10, rings=6)]
    hc = Vector((-0.1, 0.04, 1.74))
    tilt = Matrix.Translation(hc) @ Euler((math.radians(-6), math.radians(-12), 0)).to_matrix().to_4x4() \
        @ Matrix.Translation(-hc)
    for o in hat:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.transform(tilt)
        o.data.update()
    move(hat[1], rot=(0, 0, 0))
    rig.rigid("hat", hat)
    # the bust: chest, shoulders, waistcoat, collar, buttons, necklace
    chest = lathe_r([(0.0, 0.95), (0.18, 0.95), (0.35, 0.88), (0.5, 0.75), (0.55, 0.5), (0.5, 0.2), (0.45, 0.0),
                     (0.0, 0.0)], vest, segs=32, name="chest", smooth=50)
    move(chest, scale=(1.0, 0.62, 1.0))
    neck = [tube_pts([(0, 0.0, 0.85), (0, -0.02, 1.0), (0, -0.04, 1.1)], 0.17, 0.16, skin, verts=14, caps=False)]
    shirtf = ell((0, -0.25, 0.68), (0.15, 0.1, 0.25), shirt, segs=14, rings=10)
    collar = []
    for s in (1, -1):
        collar.append(plate([(0.0, 0.0), (s * 0.24, 0.04), (s * 0.26, 0.2), (s * 0.08, 0.1)], 0.03, 0.0, vest2,
                            bevel=0.01))
        collar[-1].data.transform(Matrix.Translation((0, -0.2, 0.86)) @ Matrix.Rotation(R90 - 0.3, 4, "X"))
        collar[-1].data.update()
    buttons = [sphere(0.035, (0.11 * (1 if k % 2 else -1) * 0.0 + 0.0, -0.33, 0.6 - 0.16 * k), gold, segs=10, rings=6)
               for k in range(3)]
    for k, s in enumerate((1, -1)):
        buttons.append(sphere(0.03, (s * 0.12, -0.32, 0.55 - 0.1 * k), gold, segs=8, rings=6))
    neck_c = [Vector((0.3 * math.sin(a), -0.17 - 0.12 * math.cos(a), 0.86 - 0.18 * math.cos(a) ** 2))
              for a in (math.pi * (-0.45 + 0.9 * k / 12) for k in range(13))]
    necklace = [tube(neck_c, [0.01] * 13, gold, verts=5, caps=True, name="chain")]
    for k in (2, 4, 6, 8, 10):
        p = neck_c[k]
        necklace.append(cyl(0.04 if k == 6 else 0.03, 0.012, p + Vector((0, -0.02, -0.03)), gold,
                            rot=(R90 - 0.3, 0, 0), verts=16))
    necklace.append(ell(neck_c[6] + Vector((0, -0.035, -0.03)), (0.018, 0.008, 0.018), gem, segs=8, rings=6))
    rig.rigid("chest", chest, shirtf, collar, buttons, necklace)
    rig.custom(lambda p: {"chest": 1 - smoothstep(0.9, 1.05, p.z) + 1e-4, "head": smoothstep(0.9, 1.05, p.z) + 1e-4},
               neck)
    # arms and three-fingered hands held together in front
    for s, side in ((1, "L"), (-1, "R")):
        sl = tube_pts([(s * 0.5, 0.0, 0.72), (s * 0.5, -0.15, 0.5), (s * 0.42, -0.3, 0.35)], 0.11, 0.08, vest, verts=12)
        cuff = torus(0.085, 0.025, (s * 0.41, -0.31, 0.34), shirt, rot=(R90 - 0.6, 0, s * 0.8), verts=16, minor=6)
        rig.rigid("arm." + side, sl, cuff)
        hand = [ell((s * 0.3, -0.38, 0.34), (0.1, 0.08, 0.07), skin, segs=14, rings=8)]
        for k in range(3):
            base = Vector((s * 0.23, -0.4 + 0.03 * (k - 1), 0.36 - 0.03 * k))
            hand.append(tube_pts([base, base + Vector((-s * 0.09, -0.04, -0.01)),
                                  base + Vector((-s * 0.14, -0.02, -0.03))], 0.025, 0.018, skin, verts=7))
        rig.rigid("hand." + side, hand)
    rig.build("shop_keeper")
    blink = {"%eye.L": (1, 1, 0.08), "%eye.R": (1, 1, 0.08)}

    def idle_p(k, extra=None):
        a = 2 * math.pi * k
        return merge({"%chest": (1 + 0.012 * math.sin(a), 1 + 0.012 * math.sin(a), 1 + 0.01 * math.sin(a)),
                      "head": (2 * math.sin(a), 0, 5 * math.sin(a + 0.6)),
                      "stalk0": (8 * math.sin(2 * a), 0, 14 * math.sin(a + 1)), "stalk1": (10 * math.sin(2 * a + 1), 0,
                                                                                          18 * math.sin(a + 1.6)),
                      "ear.L": (0, -6 * math.sin(2 * a), 0), "ear.R": (0, 6 * math.sin(2 * a + 0.5), 0),
                      "stache.L0": (0, 5 * math.sin(2 * a), 4 * math.sin(a)),
                      "stache.L1": (0, 9 * math.sin(2 * a - 0.8), 0),
                      "stache.R0": (0, -5 * math.sin(2 * a + 0.3), 4 * math.sin(a)),
                      "stache.R1": (0, -9 * math.sin(2 * a - 0.5), 0),
                      "hat": (0, 3 * math.sin(a + 1.2), 0),
                      "arm.L": (0, 0, 4 * math.sin(4 * a)), "arm.R": (0, 0, -4 * math.sin(4 * a)),
                      "hand.L": (12 * math.sin(4 * a), 0, 6 * math.sin(4 * a)),
                      "hand.R": (-12 * math.sin(4 * a), 0, -6 * math.sin(4 * a)),
                      "jaw": (-3 - 2 * math.sin(a), 0, 0)}, extra or {})
    rig.action("idle", {0: idle_p(0), 10: idle_p(10 / 90), 20: idle_p(20 / 90), 30: idle_p(30 / 90),
                        40: idle_p(40 / 90), 42: idle_p(42 / 90), 44: idle_p(44 / 90, blink), 46: idle_p(46 / 90),
                        55: idle_p(55 / 90), 65: idle_p(65 / 90), 75: idle_p(75 / 90), 90: idle_p(1)}, loop=True)

    def talk_p(k, open_):
        return merge(idle_p(k), {"jaw": (-6 - 22 * open_, 0, 0), "head": (-4 * open_, 0, 0),
                                 "stache.L1": (0, 14 * open_, 0), "stache.R1": (0, -14 * open_, 0)})
    rig.action("talk", {0: talk_p(0, 0), 4: talk_p(4 / 30, 1), 8: talk_p(8 / 30, 0.2), 12: talk_p(12 / 30, 0.8),
                        16: talk_p(16 / 30, 0.1), 21: talk_p(21 / 30, 1), 26: talk_p(26 / 30, 0.3),
                        30: talk_p(1, 0)}, loop=True)
    rig.action("blink", {0: {}, 3: blink, 7: {}})
    rig.export("shop_keeper")


JOBS = {"ship": ship, "pod_side": pod_side, "pod_rear": pod_rear, "drone": drone,
        "shot_pulse": shot_pulse, "shot_laser": shot_laser, "shot_homing": shot_homing, "shot_enemy": shot_enemy,
        "drifter": drifter, "dart": dart, "spinner": spinner, "turret": turret, "worm_head": worm_head,
        "worm_seg": worm_seg, "worm_tail": worm_tail, "pod": pod, "crab": crab,
        "boss_1": boss_1, "boss_2": boss_2, "boss_3": boss_3, "boss_4": boss_4, "boss_5": boss_5,
        "credit": credit, "power_gun": power_gun, "power_speed": power_speed, "power_shield": power_shield,
        "power_life": power_life, "shop_keeper": shop_keeper}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
