"""Nova Wardens (game 25) models: the three invader kinds, the player's cannon, the mothership, three bombs and the
laser bolt. Original designs (our own creatures, not the arcade's pixel sprites: a hooded one-eyed squid-thing with
fins and curling tentacles, an armoured crab-thing with a spiked shell, a tri-eye visor and big pincers, and a bulky
dome-headed octopus-thing with a glowing core in its chest and eight stubby legs). Deterministic; output CC BY-SA
4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/novawardens_models.py -- godot/games/novawardens/art/models [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (merge,
mirror, smoothstep, limb), hopline_models.py (TurnRig, ell) and mossfolk_models.py (lathe_r).

Axes: the game's field is the Godot XY plane seen from +Z (1 field pixel = 0.05 units). Everything is built in
Blender facing -Y, which exports as facing Godot +Z (towards the camera); Godot +Y (Blender +Z) is up the screen.
Origins at the centre of each model. Emissive materials all have "glow" in their names.

squid.glb    (30 points, top row) armature "squid_rig" (root, body, eye, fin.L/R, tent.L1a/b, tent.L2a/b and .R),
             mesh "squid": 0.50 wide across the fins, 0.48 tall. A violet hooded mantle with swept fins, one big slit-pupilled eye over a small beak
             (squid_eye_glow), glowing freckles and fin edges (squid_spot_glow), four curling tentacles with glowing
             tips. Materials squid_skin, squid_beak, squid_fin, squid_brow, squid_pupil, squid_eye_glow,
             squid_spot_glow.
crab.glb     (20 points) armature "crab_rig" (root, body, arm.L/R, jaw.L/R, leg.L1..L3 and .R), mesh "crab":
             0.63 wide across the claws, 0.42 tall. A teal spiked shell, a dark visor band with three amber eyes
             (crab_eye_glow), pincers with glowing inner edges (crab_claw_glow), six short legs. Materials crab_shell,
             crab_plate, crab_spike, crab_visor, crab_claw, crab_leg, crab_eye_glow, crab_claw_glow.
octopus.glb  (10 points) armature "octopus_rig" (root, body, brow, leg0..leg7 left to right), mesh "octopus":
             0.58 wide, 0.45 tall. A bulky lime dome with warts, a heavy brow over two narrow red eyes
             (octopus_eye_glow), a ribbed porthole in the chest with a hot core (octopus_core_glow), eight stubby
             legs with glowing suckers (octopus_sucker_glow). Materials octopus_skin, octopus_belly, octopus_rim,
             octopus_brow, octopus_leg, octopus_eye_glow, octopus_core_glow, octopus_sucker_glow.
             Animations (all three invaders, keyed at 60 fps):
                          march* 0.5 s: two poses, A at 0.0 s and B at 0.25 s, each held and snapping to the other
                                 (a walk step). The view can also seek 0.0 / 0.25 to follow the engine's `frame`.
                          hit    0.3 s: a jolt, everything flares out, then shrinks (ends small: hide it then).
cannon.glb   one mesh "cannon", 0.70 wide (across the nacelle rings), 0.38 tall, 0.23 deep: origin at the centre
             of the hull, the barrel along Godot +Y (the muzzle glow at y = +0.26, the hover glow down to -0.12).
             A white angular hover tank with a cyan canopy (cannon_canopy_glow) looking at the camera, glowing barrel
             coils, muzzle and front stripes (cannon_coil_glow), hover pads and nacelle glows (cannon_hover_glow).
             Materials cannon_hull, cannon_trim, cannon_dark, cannon_canopy_glow, cannon_coil_glow, cannon_hover_glow.
mothership.glb  mesh "mothership": a crimson saucer 0.91 across (0.97 with the lamps), 0.36 tall (y -0.11 .. +0.245
             with the dome and its aerial), origin at the hull's centre on the rim plane. A child mesh "lights"
             (origin on the saucer's axis): fourteen rim lamps alternating mother_lamp_a_glow (red) and
             mother_lamp_b_glow (amber); spin it about its local Y. Hull materials mother_hull, mother_trim,
             mother_dome (tinted glass, alpha 0.6, over a glowing pilot: mother_pilot_glow, mother_pilot_eye),
             mother_band_glow (a rim band), mother_beam_glow (the underside emitter ring and lens).
bomb_rolling.glb   mesh "bomb_rolling": a twisted drill, 0.14 x 0.35 (two orange helices round a hot core):
             bomb_rolling_glow, bomb_rolling_core_glow. Spin it about Y.
bomb_plunger.glb   mesh "bomb_plunger": a finned dart pointing down, 0.12 x 0.36: bomb_plunger_shell,
             bomb_plunger_glow (red band and tip).
bomb_squiggly.glb  mesh "bomb_squiggly": a zigzag of plasma beads, 0.15 x 0.35: bomb_squiggly_glow,
             bomb_squiggly_core_glow.
shot.glb     mesh "shot": the laser bolt, 0.07 x 0.33, pointing up (Godot +Y), a white core in a cyan sheath:
             shot_core_glow, shot_glow (alpha 0.7).
"""
import bpy, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, torus, rod, tube, join, export, reset
from blastyard_bombers import merge, mirror, smoothstep, limb
from hopline_models import TurnRig, ell
from mossfolk_models import lathe_r

FPS = 60


def cone(base, tip, r, material, verts=8):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


def march(rig, a, b):
    """The 2-beat step: A held, snap to B, B held, snap back (60 fps, 0.5 s)."""
    rig.action("march", {0: a, 11: a, 15: b, 26: b, 30: a}, loop=True)


def hit(rig, flare, shrink):
    rig.action("hit", {0: {}, 4: flare, 10: merge(flare, {"%root": 1.1}), 18: shrink})


def dims(o):
    bb = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector([min(v[i] for v in bb) for i in range(3)])
    hi = Vector([max(v[i] for v in bb) for i in range(3)])
    print("  %s: width %.3f  depth %.3f  height %.3f  (z %.3f .. %.3f)" % (o.name, hi.x - lo.x, hi.y - lo.y,
                                                                          hi.z - lo.z, lo.z, hi.z))


# ------------------------------------------------------------------ squid (30 points)

def squid():
    skin = mat("squid_skin", (0.42, 0.08, 0.62), 0.22, coat=1.0)
    belly = mat("squid_beak", (0.12, 0.02, 0.1), 0.25, coat=1.0)
    fin = mat("squid_fin", (0.55, 0.12, 0.7), 0.3, coat=0.8, emit=0.35, emit_color=(0.7, 0.2, 1.0))
    brow = mat("squid_brow", (0.15, 0.02, 0.22), 0.3, coat=0.8)
    pupil = mat("squid_pupil", (0.01, 0.0, 0.02), 0.2, coat=1.0)
    eye = mat("squid_eye_glow", (0.7, 1.0, 0.15), 0.2, emit=3.0)
    spot = mat("squid_spot_glow", (1.0, 0.45, 0.95), 0.3, emit=4.0)

    bones = {"root": ((0, 0, -0.05), (0, 0, 0.0), None),
             "body": ((0, 0, -0.06), (0, 0, 0.16), "root"),
             "eye": ((0, -0.1, 0.03), (0, -0.2, 0.03), "body"),
             "fin.L": ((0.09, 0, 0.16), (0.24, 0, 0.08), "body"),
             "fin.R": ((-0.09, 0, 0.16), (-0.24, 0, 0.08), "body")}
    # tentacles: two per side, (base, mid, tip) as (x, z); the outer ones curl outwards, the inner ones inwards
    tents = {"L1": [(0.035, -0.06), (0.05, -0.14), (0.035, -0.2), (0.06, -0.225)],
             "L2": [(0.08, -0.05), (0.12, -0.12), (0.155, -0.17), (0.19, -0.16)]}
    for k, pts in list(tents.items()):
        tents[k.replace("L", "R")] = [(-x, z) for x, z in pts]
    for k, pts in tents.items():
        bones["tent.%sa" % k] = ((pts[0][0], 0, pts[0][1]), (pts[1][0], 0, pts[1][1]), "body")
        bones["tent.%sb" % k] = ((pts[1][0], 0, pts[1][1]), (pts[3][0], 0, pts[3][1]), "tent.%sa" % k)
    rig = TurnRig(bones, 0, fps=FPS)

    # the mantle: a hooded teardrop, flattened front to back, rising to a swept point
    def mantle_r(k, z):
        a = 2 * math.pi * k / 32
        return 1.0 - 0.18 * math.sin(a) ** 2   # a little flatter in Y than in X
    prof = [(0.0, 0.245), (0.02, 0.235), (0.05, 0.2), (0.085, 0.15), (0.115, 0.09), (0.13, 0.03), (0.128, -0.02),
            (0.11, -0.055), (0.07, -0.075), (0.0, -0.08)]
    body = lathe_r(prof, skin, segs=32, radial=mantle_r, name="mantle", smooth=70)
    beak = [cone((s * 0.012, -0.1, -0.035), (s * 0.004, -0.108, -0.068), 0.012, belly, verts=8) for s in (-1, 1)]
    rig.rigid("body", body, beak)
    # glowing freckles in two rows up the mantle's sides
    sp = []
    for s in (-1, 1):
        for i, (x, z) in enumerate(((0.1, 0.1), (0.075, 0.15), (0.05, 0.195), (0.117, 0.05))):
            yy = -math.sqrt(max(0.0, (0.13 * (1 - 0.18)) ** 2 - (x * 0.8) ** 2)) * 0.75
            sp.append(sphere(0.011 - 0.0015 * i, (s * x, yy, z), spot, segs=8, rings=6))
    rig.rigid("body", sp)
    # a brow: a V-shaped ridge over the eye, angled down to the middle (menace)
    for s in (-1, 1):
        b = ell((s * 0.045, -0.105, 0.085), (0.055, 0.02, 0.014), brow, roll=-s * 22, segs=12, rings=6)
        rig.rigid("body", b)
    # the eye: one big glowing eye with a vertical slit
    E = Vector((0, -0.09, 0.035))
    rig.rigid("eye", ell(E + Vector((0, -0.005, 0)), (0.062, 0.035, 0.05), brow, segs=20, rings=12),
              ell(E + Vector((0, -0.02, 0)), (0.052, 0.03, 0.042), eye, segs=20, rings=12),
              ell(E + Vector((0, -0.045, 0)), (0.009, 0.012, 0.034), pupil, segs=10, rings=8))
    # fins: flat leaves swept up and out from the hood, with glowing edges
    for s, side in ((1, "L"), (-1, "R")):
        outline = [(0.07, 0.205), (0.15, 0.165), (0.215, 0.115), (0.25, 0.07), (0.2, 0.08), (0.14, 0.095),
                   (0.085, 0.1)]
        poly = [(s * x, z) for x, z in outline]
        f = K.prism(poly if s > 0 else poly[::-1], 0.022, (0, 0.012, 0), fin, bevel=0.008, segs=2)
        edge = limb([(s * x, 0.0, z) for x, z in outline[:4]], [0.006, 0.006, 0.005, 0.003], spot, verts=6, per=3,
                    caps=True)
        rig.rigid("fin." + side, f, edge)
    # tentacles: tubes tapering to glowing tips, bent at the mid bone
    for k, pts in tents.items():
        P = [(x, -0.01, z) for x, z in pts]
        t = limb(P, [0.03, 0.022, 0.014, 0.008], skin, verts=10, per=4, caps=True)
        tip = sphere(0.013, P[-1], spot, segs=8, rings=6)
        mid_z = pts[1][1]

        def w(p, k=k, mid_z=mid_z):
            q = smoothstep(mid_z + 0.02, mid_z - 0.02, p.z)
            return {"tent.%sa" % k: 1 - q + 1e-4, "tent.%sb" % k: q + 1e-4}
        rig.custom(w, t)
        rig.rigid("tent.%sb" % k, tip)
    rig.build("squid")
    dims(rig.mesh)

    a = merge({"@body": (0, 0, 0.0), "%body": (1.03, 1.0, 0.97), "eye": (0, 0, 0)},
              {"tent.L1a": (0, -18, 0), "tent.L1b": (0, -25, 0), "tent.L2a": (0, 20, 0), "tent.L2b": (0, 30, 0),
               "tent.R1a": (0, -10, 0), "tent.R1b": (0, 20, 0), "tent.R2a": (0, -8, 0), "tent.R2b": (0, -25, 0),
               "fin.L": (0, 12, 0), "fin.R": (0, 4, 0)})
    b = merge({"@body": (0, 0, 0.015), "%body": (0.97, 1.0, 1.04)},
              {"tent.R1a": (0, 18, 0), "tent.R1b": (0, 25, 0), "tent.R2a": (0, -20, 0), "tent.R2b": (0, -30, 0),
               "tent.L1a": (0, 10, 0), "tent.L1b": (0, -20, 0), "tent.L2a": (0, 8, 0), "tent.L2b": (0, 25, 0),
               "fin.R": (0, -12, 0), "fin.L": (0, -4, 0)})
    march(rig, a, b)
    hit(rig, merge({"%root": 1.2, "%eye": (1.3, 1, 1.3), "tent.L2a": (0, 40, 0), "tent.R2a": (0, -40, 0),
                    "tent.L1a": (0, 25, 0), "tent.R1a": (0, -25, 0)}, mirror({"fin.L": (0, 30, 0)})),
        {"%root": 0.15})
    rig.save("squid")


# ------------------------------------------------------------------ crab (20 points)

def crab():
    shell = mat("crab_shell", (0.03, 0.42, 0.48), 0.2, 0.3, coat=1.0)
    plate = mat("crab_plate", (0.02, 0.2, 0.26), 0.28, 0.4, coat=0.8)
    spike = mat("crab_spike", (0.8, 0.95, 0.9), 0.25, coat=0.6)
    visor = mat("crab_visor", (0.01, 0.02, 0.03), 0.15, coat=1.0)
    claw_m = mat("crab_claw", (0.05, 0.55, 0.55), 0.22, 0.3, coat=1.0)
    leg_m = mat("crab_leg", (0.02, 0.26, 0.3), 0.35, 0.3, coat=0.5)
    eye = mat("crab_eye_glow", (1.0, 0.4, 0.02), 0.2, emit=3.0)
    cglow = mat("crab_claw_glow", (0.3, 1.0, 0.95), 0.3, emit=3.5)

    bones = {"root": ((0, 0, -0.05), (0, 0, 0.0), None),
             "body": ((0, 0, -0.08), (0, 0, 0.12), "root"),
             "arm.L": ((0.14, 0, 0.0), (0.24, 0, 0.08), "body"),
             "jaw.L": ((0.24, 0, 0.08), (0.28, 0, 0.18), "arm.L"),
             "arm.R": ((-0.14, 0, 0.0), (-0.24, 0, 0.08), "body"),
             "jaw.R": ((-0.24, 0, 0.08), (-0.28, 0, 0.18), "arm.R")}
    LEGS = [(0.05, 0.075, -0.2), (0.1, 0.14, -0.19), (0.14, 0.2, -0.17)]   # hip x, foot x, foot z
    for i, (hx, fx, fz) in enumerate(LEGS):
        for s, side in ((1, "L"), (-1, "R")):
            bones["leg.%s%d" % (side, i + 1)] = ((s * hx, 0, -0.07), (s * fx, 0, fz), "body")
    rig = TurnRig(bones, 0, fps=FPS)

    # the shell: a wide dome, a darker belly plate, three ridged plates across the back and spikes on the rim
    body = [ell((0, 0, 0.0), (0.175, 0.13, 0.115), shell, segs=32, rings=16),
            ell((0, 0.01, -0.055), (0.15, 0.11, 0.05), plate, segs=24, rings=10)]
    for k in range(7):   # armour scales over the dome's front, a darker rim below each
        a = math.radians(-60 + 20 * k)
        p = Vector((0.15 * math.sin(a), -0.1 * math.cos(a), 0.06 - 0.01 * abs(k - 3)))
        body.append(ell(p, (0.032, 0.02, 0.022), plate, segs=12, rings=8))
        body.append(ell(p + Vector((0, -0.004, 0.006)), (0.028, 0.018, 0.018), shell, segs=12, rings=8))
    for k, (x, z, dx, dz) in enumerate(((0.0, 0.113, 0.0, 0.06), (0.075, 0.1, 0.03, 0.05), (0.135, 0.07, 0.05, 0.035),
                                         (0.17, 0.025, 0.05, 0.01))):
        for s in ((1,) if x == 0 else (1, -1)):
            base = Vector((s * x, 0.0, z))
            body.append(cone(base, base + Vector((s * dx, 0.0, dz)), 0.022 - 0.002 * k, spike, verts=8))
    # the face: a dark visor band across the front, three eyes in it (the middle one biggest), mandibles below
    body.append(ell((0, -0.098, -0.005), (0.12, 0.05, 0.034), visor, segs=24, rings=10))
    for x, r in ((-0.055, 0.017), (0.0, 0.023), (0.055, 0.017)):
        body.append(sphere(r, (x, -0.135, -0.003 + (0.004 if x == 0 else 0)), eye, segs=12, rings=8))
    for s in (-1, 1):
        body.append(ell((s * 0.09, -0.105, 0.035), (0.05, 0.02, 0.012), plate, roll=-s * 20, segs=12, rings=6))
        body.append(limb([(s * 0.03, -0.1, -0.06), (s * 0.028, -0.115, -0.09), (s * 0.01, -0.11, -0.11)],
                         [0.013, 0.009, 0.003], spike, verts=8, per=3, caps=True))
    rig.rigid("body", body)
    # arms and pincers: the upper blade fixed to the arm, the lower jaw on its own bone
    for s, side in ((1, "L"), (-1, "R")):
        arm = limb([(s * 0.13, 0, 0.0), (s * 0.2, -0.01, 0.02), (s * 0.24, -0.01, 0.07)], [0.035, 0.03, 0.035],
                   claw_m, verts=12, per=3, caps=True)
        palm = ell((s * 0.245, -0.01, 0.09), (0.045, 0.04, 0.04), claw_m, segs=16, rings=10)
        upper = limb([(s * 0.25, -0.01, 0.11), (s * 0.24, -0.01, 0.16), (s * 0.21, -0.01, 0.195),
                      (s * 0.175, -0.01, 0.2)], [0.032, 0.026, 0.016, 0.004], claw_m, verts=12, per=3, caps=True)
        teeth = [cone((s * (0.235 - 0.02 * i), -0.01, 0.16 + 0.012 * i), (s * (0.22 - 0.02 * i), -0.01, 0.15 + 0.01 * i),
                      0.007, cglow, verts=6) for i in range(3)]
        rig.rigid("arm." + side, arm, palm, upper, teeth)
        jaw = limb([(s * 0.27, -0.01, 0.1), (s * 0.3, -0.01, 0.15), (s * 0.29, -0.01, 0.19)],
                   [0.026, 0.018, 0.004], claw_m, verts=10, per=3, caps=True)
        edge = sphere(0.009, (s * 0.292, -0.01, 0.185), cglow, segs=8, rings=6)
        rig.rigid("jaw." + side, jaw, edge)
    # six short legs, bent at the knee, pointed feet
    for i, (hx, fx, fz) in enumerate(LEGS):
        for s, side in ((1, "L"), (-1, "R")):
            knee = (s * (hx + fx) * 0.5 + s * 0.03, 0.0, -0.1)
            lg = limb([(s * hx, 0.0, -0.06), knee, (s * fx, 0.0, fz)], [0.02, 0.016, 0.004], leg_m, verts=8,
                      per=3, caps=True)
            rig.rigid("leg.%s%d" % (side, i + 1), lg)
    rig.build("crab")
    dims(rig.mesh)

    a = merge({"arm.L": (0, -18, 0), "jaw.L": (0, -25, 0), "arm.R": (0, -4, 0), "jaw.R": (0, 5, 0),
               "@body": (0, 0, 0.0), "body": (0, 3, 0)},
              {"leg.L1": (0, -12, 0), "leg.L3": (0, -12, 0), "leg.R2": (0, 12, 0),
               "leg.L2": (0, 8, 0), "leg.R1": (0, -8, 0), "leg.R3": (0, -8, 0)})
    b = merge({"arm.R": (0, 18, 0), "jaw.R": (0, 25, 0), "arm.L": (0, 4, 0), "jaw.L": (0, -5, 0),
               "@body": (0, 0, 0.012), "body": (0, -3, 0)},
              {"leg.R1": (0, 12, 0), "leg.R3": (0, 12, 0), "leg.L2": (0, -12, 0),
               "leg.R2": (0, -8, 0), "leg.L1": (0, 8, 0), "leg.L3": (0, 8, 0)})
    march(rig, a, b)
    hit(rig, merge({"%root": 1.2}, mirror({"arm.L": (0, -35, 0), "jaw.L": (0, -40, 0), "leg.L1": (0, 20, 0),
                                          "leg.L2": (0, 25, 0), "leg.L3": (0, 30, 0)})), {"%root": 0.15})
    rig.save("crab")


# ------------------------------------------------------------------ octopus (10 points)

def octopus():
    skin = mat("octopus_skin", (0.22, 0.6, 0.04), 0.25, coat=1.0)
    bel = mat("octopus_belly", (0.5, 0.75, 0.25), 0.4, coat=0.5)
    rim = mat("octopus_rim", (0.05, 0.12, 0.03), 0.3, 0.5, coat=0.8)
    brow_m = mat("octopus_brow", (0.08, 0.25, 0.02), 0.3, coat=0.8)
    leg_m = mat("octopus_leg", (0.16, 0.45, 0.04), 0.3, coat=0.9)
    eye = mat("octopus_eye_glow", (1.0, 0.05, 0.02), 0.2, emit=3.5)
    core = mat("octopus_core_glow", (1.0, 0.4, 0.03), 0.2, emit=2.5)
    suck = mat("octopus_sucker_glow", (0.85, 1.0, 0.4), 0.3, emit=2.5)

    # eight legs along the bottom rim, (hip x, foot x, foot z), left (x < 0) to right
    LEGS = [(-0.16, -0.25, -0.16), (-0.12, -0.2, -0.195), (-0.07, -0.105, -0.215), (-0.025, -0.03, -0.21)]
    LEGS += [(-hx, -fx, fz) for hx, fx, fz in reversed(LEGS)]
    bones = {"root": ((0, 0, -0.05), (0, 0, 0.0), None),
             "body": ((0, 0, -0.08), (0, 0, 0.18), "root"),
             "brow": ((0, -0.12, 0.09), (0, -0.2, 0.09), "body")}
    for i, (hx, fx, fz) in enumerate(LEGS):
        bones["leg%d" % i] = ((hx, 0, -0.08), (fx, 0, fz), "body")
    rig = TurnRig(bones, 0, fps=FPS)

    # the dome: bulky, wider than tall, with a flat-ish bottom; warts over the top
    def lobes(k, z):
        a = 2 * math.pi * k / 40
        return (1.0 - 0.2 * math.sin(a) ** 2) * (1 + 0.035 * math.cos(6 * a) * smoothstep(0.1, -0.05, z))
    prof = [(0.0, 0.215), (0.07, 0.205), (0.13, 0.175), (0.18, 0.125), (0.21, 0.06), (0.22, 0.0), (0.21, -0.05),
            (0.18, -0.085), (0.1, -0.1), (0.0, -0.1)]
    head = lathe_r(prof, skin, segs=40, radial=lobes, name="dome", smooth=70)
    parts = [head]
    rnd = random.Random(25)
    for k in range(22):
        a = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(0.03, 0.19)
        rr = 0.22 * math.sqrt(max(0.0, 1 - ((z - 0.0) / 0.215) ** 2))
        p = Vector((rr * math.cos(a), rr * math.sin(a) * 0.8, z))
        if p.y < -0.1 and abs(p.x) < 0.13 and z < 0.14:
            continue   # keep the face clear
        parts.append(sphere(rnd.uniform(0.01, 0.018), p, bel if k % 3 else suck, segs=8, rings=6))
    # the chest porthole: a ribbed rim round a hot core
    C = Vector((0, -0.155, -0.02))
    ring = torus(0.055, 0.016, (0, 0, 0), rim, verts=24, minor=8)
    ring.data.transform(Matrix.Translation(C) @ Matrix.Rotation(math.radians(90), 4, "X"))
    parts += [ring, sphere(0.047, C + Vector((0, 0.012, 0)), core, segs=16, rings=10)]
    for k in range(8):   # rivets on the rim
        a = 2 * math.pi * k / 8
        parts.append(sphere(0.008, C + Vector((0.055 * math.cos(a), -0.014, 0.055 * math.sin(a))), bel, segs=6, rings=4))
    rig.rigid("body", parts)
    # the eyes and the heavy brow: narrow glowing slits under a V ridge
    br = []
    for s in (-1, 1):
        br.append(ell((s * 0.065, -0.155, 0.075), (0.042, 0.02, 0.018), rim, roll=-s * 14, segs=14, rings=8))
        br.append(ell((s * 0.065, -0.172, 0.075), (0.034, 0.012, 0.012), eye, roll=-s * 14, segs=14, rings=8))
        br.append(ell((s * 0.068, -0.162, 0.103), (0.072, 0.032, 0.02), brow_m, roll=-s * 24, segs=16, rings=8))
    rig.rigid("brow", br)
    # legs: thick stubby tentacles curling at the tip, a row of glowing suckers underneath
    for i, (hx, fx, fz) in enumerate(LEGS):
        s = 1 if hx > 0 else -1
        mid = ((hx + fx) * 0.5 + s * 0.01, -0.01, -0.1 + (fz + 0.1) * 0.55)
        curl = (fx + s * 0.03, -0.02, fz + 0.02)
        lg = limb([(hx, 0.0, -0.06), mid, (fx, -0.01, fz), curl], [0.042, 0.034, 0.02, 0.008], leg_m, verts=12,
                  per=3, caps=True)
        su = [sphere(0.008, Vector(mid).lerp(Vector((fx, -0.01, fz)), t) + Vector((0, -0.028 + 0.012 * t, 0)), suck,
                     segs=6, rings=4) for t in (0.1, 0.55)]
        rig.rigid("leg%d" % i, lg, su)
    rig.build("octopus")
    dims(rig.mesh)

    def legs(sign):
        return {"leg%d" % i: (0, sign * (14 if i % 2 == 0 else -10) * (1 if i < 4 else -1), 0) for i in range(8)}
    a = merge({"%body": (1.03, 1.0, 0.96), "@body": (0, 0, -0.005), "brow": (0, 0, 0)}, legs(1))
    b = merge({"%body": (0.97, 1.0, 1.04), "@body": (0, 0, 0.01), "%brow": (1.0, 1.0, 0.85)}, legs(-1))
    march(rig, a, b)
    hit(rig, merge({"%root": 1.2, "%brow": (1.2, 1, 1.4)},
                   {"leg%d" % i: (0, (35 if i < 4 else -35), 0) for i in range(8)}), {"%root": 0.15})
    rig.save("octopus")


# ------------------------------------------------------------------ cannon

def cannon():
    hull = mat("cannon_hull", (0.88, 0.9, 0.95), 0.2, 0.1, coat=1.0)
    trim = mat("cannon_trim", (0.45, 0.5, 0.58), 0.25, 0.9)
    dark = mat("cannon_dark", (0.05, 0.06, 0.09), 0.3, 0.6, coat=0.6)
    canopy = mat("cannon_canopy_glow", (0.1, 0.7, 1.0), 0.05, coat=1.0, emit=1.8)
    coil = mat("cannon_coil_glow", (0.2, 0.95, 1.0), 0.2, emit=3.5)
    hover = mat("cannon_hover_glow", (0.2, 0.6, 1.0), 0.3, emit=3.0)
    parts = []
    # the hull: a low angular wedge (a chamfered trapezoid in the screen plane), a dark keel under it
    outline = [(-0.25, -0.075), (0.25, -0.075), (0.3, -0.035), (0.23, 0.035), (0.1, 0.06), (-0.1, 0.06),
               (-0.23, 0.035), (-0.3, -0.035)]
    parts.append(K.prism(outline, 0.24, (0, 0, 0), hull, bevel=0.022, segs=3))
    parts.append(K.prism([(-0.22, -0.11), (0.22, -0.11), (0.26, -0.07), (-0.26, -0.07)], 0.2, (0, 0, 0), dark,
                         bevel=0.012, segs=2))
    # a glowing stripe along the front chamfers, steel panel lines
    for sgn in (-1, 1):
        parts.append(limb([(sgn * 0.285, -0.121, -0.03), (sgn * 0.22, -0.121, 0.028), (sgn * 0.1, -0.121, 0.05)],
                          [0.008, 0.008, 0.006], coil, verts=6, per=3, caps=True))
        parts.append(rod((sgn * 0.06, -0.122, -0.06), (sgn * 0.2, -0.122, -0.06), 0.006, trim, verts=6))
    # hover nacelles at both ends: steel capsules with glowing intake rings facing out, a glow pad underneath
    for sgn in (-1, 1):
        parts.append(limb([(sgn * 0.24, 0, -0.07), (sgn * 0.3, 0, -0.07), (sgn * 0.34, 0, -0.065)],
                          [0.055, 0.055, 0.045], trim, verts=16, per=2, caps=True))
        ring = torus(0.036, 0.009, (0, 0, 0), coil, verts=16, minor=6)
        ring.data.transform(Matrix.Translation((sgn * 0.345, 0, -0.065)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        parts.append(ring)
        parts.append(ell((sgn * 0.3, 0, -0.118), (0.05, 0.045, 0.01), hover, segs=16, rings=6))
    parts.append(ell((0, 0, -0.113), (0.17, 0.08, 0.01), hover, segs=24, rings=6))
    # the turret: a dome with a cyan canopy looking at the camera, a steel collar
    parts.append(ell((0, 0.0, 0.065), (0.14, 0.11, 0.075), hull, segs=28, rings=14))
    parts.append(ell((0, -0.075, 0.07), (0.08, 0.04, 0.042), canopy, segs=20, rings=10))
    parts.append(torus(0.1, 0.013, (0, 0, 0.06), trim, verts=32, minor=6, scale=(1.35, 1.05, 1.0)))
    # the barrel: a dark mantlet, a steel sleeve with three glowing coils, a muzzle ring and a glowing emitter
    parts.append(rod((0, 0, 0.1), (0, 0, 0.155), 0.05, dark, r2=0.042, verts=20))
    parts.append(rod((0, 0, 0.15), (0, 0, 0.255), 0.032, trim, r2=0.028, verts=18))
    for i, z in enumerate((0.17, 0.195, 0.22)):
        parts.append(torus(0.034 - 0.002 * i, 0.008, (0, 0, z), coil, verts=18, minor=6))
    parts.append(torus(0.032, 0.011, (0, 0, 0.26), trim, verts=18, minor=6))
    parts.append(sphere(0.022, (0, 0, 0.262), coil, segs=12, rings=8))
    # small fins behind the turret
    for sgn in (-1, 1):
        parts.append(K.prism([(sgn * 0.12, 0.04), (sgn * 0.2, 0.035), (sgn * 0.14, 0.11)][::sgn], 0.012,
                             (0, 0.07, 0), trim, bevel=0.004, segs=1))
    o = join(parts, "cannon")
    o.data.transform(Matrix.Scale(0.91, 4))   # built a little large: 0.70 across the nacelle rings
    dims(o)
    export(o, "cannon")


# ------------------------------------------------------------------ mothership

def mothership():
    hullm = mat("mother_hull", (0.55, 0.05, 0.1), 0.25, 0.5, coat=1.0)
    trim = mat("mother_trim", (0.9, 0.7, 0.3), 0.25, 0.95)
    dome = mat("mother_dome", (0.1, 0.04, 0.16), 0.02, 0.1, coat=1.0, alpha=0.6)
    pilot = mat("mother_pilot_glow", (1.0, 0.3, 0.85), 0.3, emit=3.0)
    beam = mat("mother_beam_glow", (1.0, 0.2, 0.5), 0.3, emit=3.0)
    band = mat("mother_band_glow", (1.0, 0.45, 0.1), 0.3, emit=2.5)
    la = mat("mother_lamp_a_glow", (1.0, 0.08, 0.12), 0.2, emit=4.0)
    lb = mat("mother_lamp_b_glow", (1.0, 0.6, 0.05), 0.2, emit=4.0)
    parts = [lathe_r([(0.0, 0.06), (0.2, 0.052), (0.34, 0.025), (0.45, -0.005), (0.44, -0.03), (0.32, -0.065),
                      (0.16, -0.085), (0.0, -0.09)], hullm, segs=64, name="hull", smooth=50)]
    parts.append(torus(0.445, 0.012, (0, 0, -0.012), trim, verts=64, minor=6))
    parts.append(torus(0.4, 0.005, (0, 0, 0.012), band, verts=64, minor=5))
    parts.append(torus(0.19, 0.015, (0, 0, 0.055), trim, verts=48, minor=6))
    # panel ribs on top, radiating from the dome
    for k in range(16):
        a = 2 * math.pi * k / 16
        c, s = math.cos(a), math.sin(a)
        parts.append(rod((0.21 * c, 0.21 * s, 0.055), (0.36 * c, 0.36 * s, 0.024), 0.006, trim, verts=6))
    # the dome with the pilot inside: a glowing blob with two dark eyes
    parts.append(lathe_r([(0.0, 0.215), (0.07, 0.205), (0.12, 0.17), (0.16, 0.115), (0.18, 0.055)], dome, segs=40,
                         name="dome", smooth=70))
    parts.append(ell((0, 0, 0.115), (0.06, 0.05, 0.06), pilot, segs=16, rings=10))
    for s in (-1, 1):
        parts.append(ell((s * 0.022, -0.05, 0.125), (0.014, 0.008, 0.02), mat("mother_pilot_eye", (0.02, 0, 0.03), 0.2),
                         roll=s * 20, segs=10, rings=6))
    parts.append(sphere(0.012, (0, 0, 0.23), trim, segs=8, rings=6))
    parts.append(rod((0, 0, 0.21), (0, 0, 0.245), 0.005, trim, verts=6))
    # underneath: an emitter ring and a glowing lens
    parts.append(torus(0.13, 0.02, (0, 0, -0.08), beam, verts=40, minor=8))
    parts.append(ell((0, 0, -0.09), (0.07, 0.07, 0.02), beam, segs=20, rings=8))
    hull = join(parts, "mothership")
    lamps = []
    for k in range(14):
        a = 2 * math.pi * k / 14
        lamps.append(sphere(0.026, (0.458 * math.cos(a), 0.458 * math.sin(a), -0.012), la if k % 2 == 0 else lb,
                            segs=10, rings=6))
    lights = join(lamps, "lights")
    dims(hull)
    export(hull, "mothership", children=[(lights, hull)])


# ------------------------------------------------------------------ bombs and the shot

def bomb_rolling():
    g = mat("bomb_rolling_glow", (1.0, 0.3, 0.02), 0.3, emit=1.8)
    core = mat("bomb_rolling_core_glow", (1.0, 0.8, 0.4), 0.3, emit=4.0)
    parts = [rod((0, 0, 0.14), (0, 0, -0.16), 0.022, core, r2=0.006, verts=10)]
    for ph in (0, math.pi):
        pts, rad = [], []
        for i in range(37):
            t = i / 36
            z = 0.15 - 0.31 * t
            r = 0.055 * (1 - 0.65 * t)
            a = ph + t * 4.5 * math.pi
            pts.append((r * math.cos(a), r * math.sin(a), z))
            rad.append(0.02 * (1 - 0.6 * t))
        parts.append(tube(pts, rad, g, verts=8, caps=True, name="helix"))
    parts.append(sphere(0.035, (0, 0, 0.15), g, segs=12, rings=8))
    o = join(parts, "bomb_rolling")
    dims(o)
    export(o, "bomb_rolling")


def bomb_plunger():
    shell = mat("bomb_plunger_shell", (0.2, 0.05, 0.06), 0.25, 0.8, coat=0.8)
    g = mat("bomb_plunger_glow", (1.0, 0.05, 0.1), 0.3, emit=3.0)
    parts = [lathe_r([(0.0, 0.14), (0.03, 0.135), (0.04, 0.1), (0.042, 0.0), (0.035, -0.07), (0.018, -0.13),
                      (0.0, -0.175)], shell, segs=16, name="dart", smooth=50)]
    parts.append(torus(0.043, 0.01, (0, 0, 0.03), g, verts=16, minor=6))
    parts.append(torus(0.038, 0.008, (0, 0, -0.03), g, verts=16, minor=6))
    parts.append(cone((0, 0, -0.12), (0, 0, -0.178), 0.014, g, verts=8))
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        f = K.prism([(0.0, 0.0), (0.035, 0.03), (0.035, 0.1), (0.0, 0.07)], 0.01, (0, 0, 0), shell, bevel=0.003)
        f.data.transform(Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0.035, 0, 0.07)))
        parts.append(f)
        parts.append(sphere(0.009, (0.072 * c, 0.072 * s, 0.17), g, segs=8, rings=6))
    o = join(parts, "bomb_plunger")
    dims(o)
    export(o, "bomb_plunger")


def bomb_squiggly():
    g = mat("bomb_squiggly_glow", (0.35, 1.0, 0.03), 0.3, emit=1.8)
    core = mat("bomb_squiggly_core_glow", (0.85, 1.0, 0.5), 0.3, emit=4.0)
    pts = [(0.05 * (1 if i % 2 else -1) * (1 - 0.3 * i / 6), 0, 0.15 - 0.3 * i / 6) for i in range(7)]
    parts = [limb(pts, [0.02, 0.02, 0.018, 0.016, 0.014, 0.012, 0.01], g, verts=10, per=5, caps=True)]
    for i, p in enumerate(pts):
        parts.append(sphere(0.03 - 0.0025 * i, p, core if i % 2 == 0 else g, segs=12, rings=8))
    o = join(parts, "bomb_squiggly")
    dims(o)
    export(o, "bomb_squiggly")


def shot():
    core = mat("shot_core_glow", (0.9, 1.0, 1.0), 0.2, emit=10.0)
    g = mat("shot_glow", (0.2, 0.9, 1.0), 0.2, emit=5.0, alpha=0.7)
    parts = [tube([(0, 0, 0.14), (0, 0, 0.1), (0, 0, -0.05), (0, 0, -0.14)], [0.018, 0.016, 0.01, 0.003], core,
                  verts=10, caps=True, name="core"),
             tube([(0, 0, 0.13), (0, 0, 0.1), (0, 0, -0.05), (0, 0, -0.16)], [0.035, 0.03, 0.018, 0.004], g,
                  verts=12, caps=True, name="sheath")]
    o = join(parts, "shot")
    dims(o)
    export(o, "shot")


JOBS = {"squid": squid, "crab": crab, "octopus": octopus, "cannon": cannon, "mothership": mothership,
        "bomb_rolling": bomb_rolling, "bomb_plunger": bomb_plunger, "bomb_squiggly": bomb_squiggly, "shot": shot}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = 30
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
