"""Fuseflight (game 28) models: the firework sprite (the hero), the firework rocket, the night imp (walking and
winged), the will-o'-wisp orb, the power star, the two bonus letters and the spark an enemy becomes during power.
Original designs for a firework festival at night: the sprite is our own character (a round red paper lantern with
big eyes, a glowing belly where its flame shows through, a crest of sparks on top, stubby arms and boots, and a little
midnight-blue cape clipped to a gold collar); the imp is a purple goblin with long ears, a pointed nose, a sly grin
and a ragged teal cloak, swinging a green lantern on a crooked stick (the flyer adds bat wings); the orb is a
grinning wisp of cold fire. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets
(the B and E glyphs are drawn with Blender's built-in, permissively licensed text font, then thickened).
Run: blender -b --factory-startup -P tools/blender/fuseflight_models.py -- godot/games/fuseflight/art/models [name ...]
Helpers come from blastyard_models.py (mat, sphere, rod, tube, join, export, ...), blastyard_bombers.py (merge,
mirror, smoothstep), hopline_models.py (TurnRig, ell), mossfolk_models.py (lathe_r, lumpy) and prism_models.py
(animate, export_anim, empty). 30 fps.

Axes: the arena is the Godot XY plane seen from +Z. Everything is built in Blender facing -Y, which exports as
facing Godot +Z (towards the camera); Godot +Y (Blender +Z) is up. Game size (node scale 1). Animations marked * are
seamless loops: set their loop mode in the game. Emissive materials all have "glow" in their names.

sprite.glb   armature "sprite_rig" (root, body, top, crest, eye.L/R, arm.L/R, leg.L/R, cape.L/R, cape.L2/R2),
             mesh "sprite": 0.91 tall to the crest's sparks (the lantern 0.14 .. 0.72), 0.69 wide across the mittens,
             origin at the feet, facing +Z. Materials sprite_paper (red lantern paper), sprite_rib (its ribs),
             sprite_belly_glow (the lit lower third of the lantern), sprite_brass (caps, collar), sprite_crest_glow and
             sprite_spark_glow (the spark crest), sprite_eye_white, sprite_iris, sprite_pupil, sprite_eye_glow (catch
             lights), sprite_mouth, sprite_cheek, sprite_limb, sprite_mitten, sprite_boot, sprite_cape (outside),
             sprite_cape_lining (inside: what shows when it spreads), sprite_hem_glow (its gold hem),
             sprite_brooch_glow (the star clasp).
             Animations:  idle*  2.0 s  breathing, the crest flickers, the cape stirs, one blink
                          run*   0.4 s  two strides (feet planted ~0.4 apart: 2 units/s at speed 1), lean, arms pump,
                                        cape streaming back
                          leap   0.3 s  crouch (f3), spring (f6), stretched up (f9, the rise pose)
                          rise*  0.5 s  stretched, arms up, legs together, cape trailing down
                          glide* 1.2 s  the cape spread like wings, arms out, a gentle sway and bob
                          fall*  0.5 s  the cape billowing up, arms flailing, legs kicking, eyes wide
                          land   0.2 s  squash (f2) and back to rest
                          die    1.2 s  a jolt, two spins slowing, the crest fizzles out, slumps (holds the last frame)
                          cheer* 1.0 s  two hops, arms up, the cape flapping, the crest flaring
rocket.glb   mesh "rocket" (0.45 tall, -0.225 .. +0.225, origin at the centre, upright): a paper tube 0.16 across with
             a spiral stripe (rocket_paper: tint it per variant; rocket_stripe white), four fins and a gold nose cone
             (rocket_trim), a guide stick below (rocket_stick), a twisted fuse curling from the nose (rocket_fuse).
             Child empty "fuse_tip" at the fuse's end (Godot x 0.048, y 0.215) for the lit spark.
walker.glb   armature "walker_rig" (root, body, head, ear.L/R, arm.L/R, lamp, leg.L/R, tail), mesh "walker": 0.52 tall
             to the ear tips (0.55 wide across the lantern), origin at the feet, facing +Z. walker_skin, walker_belly, walker_cloak, walker_ear,
             walker_eye_glow, walker_pupil, walker_mouth, walker_tooth, walker_horn, walker_stick, walker_lamp_frame,
             walker_lamp_glow (the green lantern held out on its left, Godot +X).
             Animation walk* 0.6 s: a sneaky tiptoe, the lantern swinging, the tail swishing.
flyer.glb    the same imp with bat wings (bones wing.L/R, wing.L2/R2), mesh "flyer": 0.84 across the wing tips;
             walker_wing (membrane), walker_wing_bone. Animation fly* 0.5 s: two-stroke flaps, legs dangling.
orb.glb      meshes under "orb_root" (origin at the core's centre, 0.50 across, the flame tips
             reaching 0.33 up): a grinning core (orb_core_glow, orb_face), a
             flame shell of wisps (orb_flame_glow), two crackling arc rings (orb_arc_glow) and four motes
             (orb_mote_glow). Animation spin* 1.0 s: the arcs counter-rotate, the motes orbit, the core pulses.
star.glb     mesh "star": a faceted five-pointed star 0.60 across, 0.57 tall (point up), 0.16 thick, origin at the centre,
             star_glow (gold) with a raised pale core (star_core_glow). No animation (the view spins it).
letter_b.glb, letter_e.glb   mesh "letter_b" / "letter_e": a coin 0.50 across, 0.10 thick (rim and letters), its face towards +Z
             (and the letter on the back too, reading right from behind): letter_b_face (magenta) / letter_e_face
             (teal), a gold rim (letter_rim_glow), the embossed letter (letter_b_glow / letter_e_glow). No animation.
spark.glb    meshes under "spark_root" (origin at the centre, 0.40 across the rays): a faceted gem (spark_gem_glow) and a
             star-burst of rays (spark_ray_glow). Animation spin* 1.0 s: the gem turns about Y, the rays wheel and
             pulse.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, sphere, ico, torus, rod, tube, join, export, reset, cyl
from blastyard_bombers import merge, mirror, smoothstep
from hopline_models import TurnRig, ell, hemi
from mossfolk_models import lathe_r
from prism_models import animate, export_anim, empty, new_obj

FPS = 30


def cone(base, tip, r, material, verts=8):
    return rod(base, tip, r, material, r2=0.0, verts=verts)


def fib_dirs(n):
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        yield Vector((r * math.cos(i * ga), r * math.sin(i * ga), z))


def sheet(grid, material, name="sheet", flip=False):
    """A quad surface through a grid of points (rows of columns); flip reverses the faces."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in grid]
    for i in range(len(vs) - 1):
        for j in range(len(vs[0]) - 1):
            f = (vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j])
            bm.faces.new(f[::-1] if flip else f)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=70)


def flame(base, tip, r, material, bend=(0, 0, 0), verts=8):
    """A teardrop wisp from base to tip, bulging near the base and bending by `bend` at the middle."""
    a, b = Vector(base), Vector(tip)
    pts = [a + (b - a) * t + Vector(bend) * math.sin(math.pi * t) for t in (0.0, 0.2, 0.45, 0.7, 0.88, 1.0)]
    rad = [r * k for k in (0.75, 1.0, 0.85, 0.5, 0.22, 0.04)]
    return tube(pts, rad, material, verts=verts, caps=True, name="flame")


def lsc(name, deg):
    """A left-side channel and its mirror."""
    return mirror({name: deg})


# ------------------------------------------------------------------ the sprite

LC = Vector((0, 0, 0.43))            # lantern centre
LR = Vector((0.25, 0.23, 0.29))      # lantern radii (0.14 .. 0.72)


def lantern_pt(d, k=1.0):
    d = Vector(d).normalized()
    s = 1.0 / math.sqrt((d.x / LR.x) ** 2 + (d.y / LR.y) ** 2 + (d.z / LR.z) ** 2)
    return LC + d * s * k


def sprite():
    reset()
    paper = mat("sprite_paper", (0.86, 0.12, 0.07), 0.55, coat=0.25)
    rib = mat("sprite_rib", (0.42, 0.04, 0.05), 0.5, coat=0.3)
    belly = mat("sprite_belly_glow", (1.0, 0.55, 0.12), 0.5, emit=1.0, emit_color=(1.0, 0.42, 0.05))
    brass = mat("sprite_brass", (0.95, 0.66, 0.2), 0.3, metal=0.85)
    crest_m = mat("sprite_crest_glow", (1.0, 0.55, 0.08), 0.4, emit=2.2, emit_color=(1.0, 0.45, 0.04))
    spark_m = mat("sprite_spark_glow", (1.0, 0.97, 0.8), 0.3, emit=9.0)
    white = mat("sprite_eye_white", (0.98, 0.97, 0.94), 0.25, coat=0.8)
    iris = mat("sprite_iris", (0.1, 0.22, 0.55), 0.3, coat=1.0)
    pupil = mat("sprite_pupil", (0.02, 0.02, 0.04), 0.2, coat=1.0)
    shine = mat("sprite_eye_glow", (1.0, 1.0, 1.0), 0.1, emit=4.0)
    mouth = mat("sprite_mouth", (0.25, 0.02, 0.03), 0.5)
    cheek = mat("sprite_cheek", (1.0, 0.45, 0.42), 0.6)
    limb = mat("sprite_limb", (0.16, 0.1, 0.22), 0.6)
    mitten = mat("sprite_mitten", (1.0, 0.86, 0.6), 0.6)
    boot = mat("sprite_boot", (0.1, 0.13, 0.48), 0.45, coat=0.4)
    cape_m = mat("sprite_cape", (0.08, 0.1, 0.42), 0.55, coat=0.2)
    lining = mat("sprite_cape_lining", (0.32, 0.36, 0.95), 0.5)
    hem = mat("sprite_hem_glow", (1.0, 0.75, 0.25), 0.3, metal=0.4, emit=1.2, emit_color=(1.0, 0.65, 0.2))
    brooch = mat("sprite_brooch_glow", (1.0, 0.9, 0.4), 0.2, emit=3.0)

    bones = {"root": ((0, 0, 0), (0, 0, 0.06), None),
             "body": ((0, 0, 0.15), (0, 0, 0.43), "root"),
             "top": ((0, 0, 0.43), (0, 0, 0.72), "body"),
             "crest": ((0, 0, 0.74), (0, 0, 0.86), "top"),
             "eye.L": ((0.09, -0.17, 0.52), (0.09, -0.27, 0.52), "top"),
             "eye.R": ((-0.09, -0.17, 0.52), (-0.09, -0.27, 0.52), "top"),
             "arm.L": ((0.22, 0.0, 0.42), (0.3, -0.03, 0.33), "body"),
             "arm.R": ((-0.22, 0.0, 0.42), (-0.3, -0.03, 0.33), "body"),
             "leg.L": ((0.075, 0.0, 0.17), (0.08, 0.0, 0.03), "root"),
             "leg.R": ((-0.075, 0.0, 0.17), (-0.08, 0.0, 0.03), "root"),
             "cape.L": ((0.05, 0.17, 0.66), (0.15, 0.26, 0.42), "top"),
             "cape.R": ((-0.05, 0.17, 0.66), (-0.15, 0.26, 0.42), "top"),
             "cape.L2": ((0.15, 0.26, 0.42), (0.24, 0.31, 0.17), "cape.L"),
             "cape.R2": ((-0.15, 0.26, 0.42), (-0.24, 0.31, 0.17), "cape.R")}
    rig = TurnRig(bones, 0, fps=FPS)

    def w_lantern(p):
        t = smoothstep(0.3, 0.56, p.z)
        return {"body": 1 - t + 1e-4, "top": t + 1e-4}

    # the lantern: an ellipsoid of red paper, its lower third lit gold from inside, ringed by dark ribs
    lan = ell(LC, LR, paper, segs=32, rings=20)
    lan.data.materials.append(belly)
    for f in lan.data.polygons:
        if f.center.z < 0.315:
            f.material_index = 1
    parts = [lan]
    for zr in (-0.82, -0.58, -0.3, 0.0, 0.3, 0.58, 0.82):
        k = math.sqrt(1 - zr * zr)
        pts = [LC + Vector((LR.x * k * math.cos(a) * 1.01, LR.y * k * math.sin(a) * 1.01, LR.z * zr))
               for a in (2 * math.pi * i / 40 for i in range(41))]
        parts.append(tube(pts, [0.0075] * len(pts), rib, verts=6, caps=False, name="rib"))
    # brass caps top and bottom
    parts += [cyl(0.095, 0.05, (0, 0, 0.725), brass, verts=20, bevel=0.01, segs=2),
              torus(0.095, 0.012, (0, 0, 0.75), brass, verts=20, minor=6),
              cyl(0.1, 0.045, (0, 0, 0.148), brass, verts=20, bevel=0.01, segs=2),
              torus(0.1, 0.012, (0, 0, 0.126), brass, verts=20, minor=6)]
    # the collar the cape clips to, with a star brooch at the front
    parts.append(torus(0.118, 0.016, (0, 0, 0.675), brass, verts=24, minor=6, scale=(1.0, 0.95, 1.0)))
    rig.custom(w_lantern, parts)
    bro = star_mesh(0.035, 0.016, 0.012, brooch, name="brooch")
    bro.data.transform(Matrix.Translation((0, -0.118, 0.672)))
    rig.rigid("top", bro)

    # the face: big eyes, cheeks and a small open smile on the upper front
    face = []
    for s, side in ((1, "L"), (-1, "R")):
        c = Vector((s * 0.09, -0.185, 0.52))
        eye = [ell(c, (0.066, 0.03, 0.085), white, yaw=-s * 20, segs=18, rings=12),
               ell(c + Vector((-s * 0.006, -0.022, -0.008)), (0.045, 0.016, 0.058), iris, yaw=-s * 20, segs=14, rings=8),
               ell(c + Vector((-s * 0.008, -0.031, -0.01)), (0.027, 0.01, 0.036), pupil, yaw=-s * 20, segs=10, rings=6),
               sphere(0.013, c + Vector((s * 0.008, -0.039, 0.022)), shine, segs=6, rings=4),
               sphere(0.006, c + Vector((-s * 0.018, -0.038, -0.03)), shine, segs=6, rings=4)]
        rig.rigid("eye." + side, eye)
        ch = ell((0, 0, 0), (0.04, 0.012, 0.024), cheek, segs=12, rings=6)
        pc = lantern_pt((s * 0.6, -1.0, -0.12), 1.0)
        ch.data.transform(Matrix.Translation(pc) @ (pc - LC).normalized().to_track_quat("Y", "Z").to_matrix().to_4x4()
                          @ Matrix.Rotation(math.pi, 4, "Z"))
        face.append(ch)
        brow = [lantern_pt((s * (0.22 + 0.2 * u), -1.0, 0.86 + 0.07 * math.sin(math.pi * u) - 0.05 * u), 1.012)
                for u in (0, 0.25, 0.5, 0.75, 1)]
        face.append(tube(brow, [0.007, 0.009, 0.01, 0.009, 0.006], rib, verts=6, caps=True, name="brow"))
    smile = [lantern_pt((0.3 * math.cos(a), -1.0, -0.2 + 0.1 * math.sin(a)), 1.006)
             for a in (math.pi * (1.15 + 0.7 * k / 8) for k in range(9))]
    face.append(tube(smile, [0.008, 0.011, 0.013, 0.014, 0.014, 0.014, 0.013, 0.011, 0.008], mouth, verts=6,
                     caps=True, name="smile"))
    rig.custom(w_lantern, face)

    # the spark crest: five wisps of fire and a few loose sparks
    crest = [flame((0, 0.0, 0.74), (0, 0.03, 0.9), 0.045, crest_m, bend=(0, -0.015, 0.0)),
             flame((0.03, 0.0, 0.74), (0.1, 0.02, 0.86), 0.034, crest_m, bend=(-0.01, 0, 0.02)),
             flame((-0.03, 0.0, 0.74), (-0.1, 0.02, 0.86), 0.034, crest_m, bend=(0.01, 0, 0.02)),
             flame((0.04, 0.02, 0.73), (0.15, 0.04, 0.79), 0.026, crest_m, bend=(0, 0, 0.025)),
             flame((-0.04, 0.02, 0.73), (-0.15, 0.04, 0.79), 0.026, crest_m, bend=(0, 0, 0.025)),
             flame((0, 0.0, 0.745), (0, 0.0, 0.84), 0.024, spark_m),
             flame((0.02, 0.0, 0.745), (0.06, 0.0, 0.81), 0.016, spark_m),
             flame((-0.02, 0.0, 0.745), (-0.06, 0.0, 0.81), 0.016, spark_m)]
    for p in ((0.13, -0.01, 0.89), (-0.12, 0.0, 0.9), (0.05, -0.02, 0.9), (-0.18, 0.02, 0.84), (0.19, 0.03, 0.83)):
        crest.append(ico(0.012, p, spark_m, sub=1))
    rig.rigid("crest", crest)

    # stubby arms with mittens
    for s, side in ((1, "L"), (-1, "R")):
        a = [rod((s * 0.2, 0.0, 0.43), (s * 0.285, -0.025, 0.35), 0.022, limb, verts=8),
             sphere(0.044, (s * 0.3, -0.03, 0.33), mitten, segs=14, rings=8),
             ell((s * 0.27, -0.045, 0.35), (0.016, 0.016, 0.024), mitten, roll=s * 30, segs=8, rings=6)]
        rig.rigid("arm." + side, a)
    # short legs and round boots with a turned-up toe
    for s, side in ((1, "L"), (-1, "R")):
        lg = [rod((s * 0.075, 0.0, 0.16), (s * 0.08, -0.005, 0.06), 0.024, limb, verts=8),
              ell((s * 0.08, -0.02, 0.04), (0.052, 0.075, 0.042), boot, segs=14, rings=8),
              sphere(0.022, (s * 0.08, -0.095, 0.06), boot, segs=8, rings=6),
              torus(0.032, 0.008, (s * 0.08, -0.005, 0.07), brass, verts=12, minor=4)]
        rig.rigid("leg." + side, lg)

    # the cape: two layers (lining in front, midnight blue behind) hanging from the collar, flaring to the hem
    nu, nv = 14, 10

    def cape_pt(u, v, off=0.0):
        z = 0.665 - 0.5 * v
        zr = max(-1.0, min(1.0, (z - LC.z) / LR.z))
        yb = max(0.06, LR.y * math.sqrt(max(0.0, 1 - zr * zr)))
        w = 0.105 + 0.19 * v ** 0.9
        x = u * w
        y = yb + 0.022 + 0.05 * v * v - 0.07 * u * u * (0.4 + 0.6 * v) + off
        z += 0.018 * math.sin(u * math.pi * 2.5) * v ** 3 + 0.02 * u * u * v
        return Vector((x, y, z))

    def grid(off):
        return [[cape_pt(-1 + 2 * j / nu, i / nv, off) for j in range(nu + 1)] for i in range(nv + 1)]

    front = sheet(grid(0.0), lining, "cape_in")
    back = sheet(grid(0.009), cape_m, "cape_out", flip=True)
    for o in (front, back):   # make sure the lining faces the body (-Y), the outside faces away
        o.data.update()
        n = sum((p.normal for p in o.data.polygons), Vector())
        want = -1 if o is front else 1
        if n.y * want < 0:
            o.data.flip_normals()
    hem_pts = [cape_pt(-1 + 2 * j / (nu * 2), 1.0, 0.0045) for j in range(nu * 2 + 1)]
    hem_t = tube(hem_pts, [0.009] * len(hem_pts), hem, verts=6, caps=True, name="hem")
    stars = []
    rnd = random.Random(28)
    for k in range(9):   # little gold stars on the outside
        u, v = rnd.uniform(-0.8, 0.8), rnd.uniform(0.25, 0.85)
        p = cape_pt(u, v, 0.0105)
        st = star_mesh(0.022, 0.009, 0.003, hem, name="cape_star")
        st.data.transform(Matrix.Translation(p) @ Matrix.Rotation(math.pi, 4, "Z")
                          @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, "Y"))
        stars.append(st)

    def w_cape(p):
        v = (0.665 - p.z) / 0.5
        a = smoothstep(0.0, 0.3, v)
        b = smoothstep(0.38, 0.8, v)
        t = smoothstep(-0.05, 0.05, p.x)
        w = {"top": 1 - a + 1e-4}
        for side, k in (("L", t), ("R", 1 - t)):
            w["cape." + side] = a * (1 - b) * k + 1e-4
            w["cape." + side + "2"] = a * b * k + 1e-4
        return w
    rig.custom(w_cape, front, back, hem_t, stars)
    rig.build("sprite")

    # ---- poses
    blink = {"%eye.L": (1, 1, 0.1), "%eye.R": (1, 1, 0.1)}
    wide = {"%eye.L": (1.1, 1, 1.15), "%eye.R": (1.1, 1, 1.15)}
    shut = {"%eye.L": (1.1, 1, 0.14), "%eye.R": (1.1, 1, 0.14)}
    happy = {"%eye.L": (1.05, 1, 0.45), "%eye.R": (1.05, 1, 0.45)}

    def capes(a, b=0.0, spread=0.0, a2=0.0, swing=0.0):
        """a: lift back (deg about X), spread: swing out sideways, a2/b: the lower halves, swing: sideways sway."""
        return {"cape.L": (a, -spread + swing, 0), "cape.R": (a, spread + swing, 0),
                "cape.L2": (a2, -b + swing * 0.5, 0), "cape.R2": (a2, b + swing * 0.5, 0)}

    def arms(lift, fwd=0.0, lift_r=None, fwd_r=None):
        """lift raises the arms out to the sides (deg), fwd swings them forward (-) / back (+)."""
        lift_r = lift if lift_r is None else lift_r
        fwd_r = fwd if fwd_r is None else fwd_r
        return {"arm.L": (fwd, -lift, 0), "arm.R": (fwd_r, lift_r, 0)}

    # idle: breathing, the crest flickers, the cape stirs, one blink
    def idle_p(k, extra=None):
        a = 2 * math.pi * k
        return merge({"%body": (1 + 0.025 * math.sin(a), 1 + 0.025 * math.sin(a), 1 - 0.02 * math.sin(a)),
                      "top": (0, 0, 3 * math.sin(a)),
                      "%crest": (1 + 0.06 * math.sin(3 * a), 1 + 0.06 * math.sin(3 * a), 1 - 0.1 * math.sin(3 * a)),
                      "crest": (4 * math.sin(2 * a), 5 * math.sin(3 * a + 1), 0)},
                     arms(8 + 4 * math.sin(a), -4), capes(4 + 3 * math.sin(a + 0.7), 4, 3, 4 * math.sin(a + 1.4)),
                     extra or {})
    rig.action("idle", {0: idle_p(0), 10: idle_p(1 / 6), 20: idle_p(2 / 6), 30: idle_p(3 / 6),
                        38: idle_p(38 / 60), 40: idle_p(40 / 60, blink), 42: idle_p(42 / 60),
                        50: idle_p(5 / 6), 60: idle_p(1)}, loop=True)

    # run: 0.4 s, two strides; f0 left foot forward and planted, f3 passing (up), f6 right forward, f9 passing
    def run_p(ph, up):
        sgn = 1 if ph == 0 else -1
        sw = 38 * sgn
        return merge({"@root": (0, 0, 0.045 * up), "body": (10, 0, 4 * sgn), "top": (-3, 0, -4 * sgn),
                      "%body": (1 + 0.05 * (1 - up), 1 + 0.05 * (1 - up), 1 - 0.07 * (1 - up) + 0.04 * up),
                      "crest": (-28, 0, 6 * sgn), "%crest": (0.95, 0.95, 1.12),
                      "leg.L": (-sw * (1 - up), 0, 0), "leg.R": (sw * (1 - up), 0, 0),
                      "@leg.L": (0, -0.1 * sgn * (1 - up), 0.06 * up * (sgn < 0)),
                      "@leg.R": (0, 0.1 * sgn * (1 - up), 0.06 * up * (sgn > 0))},
                     arms(18, 45 * sgn * (1 - up * 0.5), 18, -45 * sgn * (1 - up * 0.5)),
                     capes(38 + 8 * up, 6, 6, 14 - 10 * up, 6 * sgn))
    rig.action("run", {0: run_p(0, 0), 3: run_p(0, 1), 6: run_p(1, 0), 9: run_p(1, 1), 12: run_p(0, 0)}, loop=True)

    crouch = merge({"@root": (0, 0, -0.01), "%body": (1.18, 1.18, 0.78), "body": (6, 0, 0), "crest": (10, 0, 0),
                    "%crest": (1.1, 1.1, 0.8), "leg.L": (-10, 0, 0), "leg.R": (-10, 0, 0)},
                   arms(-6, 20), capes(-6, 0, 4, 6), {"%eye.L": (1.05, 1, 0.8), "%eye.R": (1.05, 1, 0.8)})
    spring = merge({"@root": (0, 0, 0.03), "%body": (0.86, 0.86, 1.2), "body": (-4, 0, 0), "crest": (-6, 0, 0),
                    "%crest": (0.9, 0.9, 1.35), "leg.L": (8, 0, 0), "leg.R": (8, 0, 0),
                    "@leg.L": (0, 0, -0.02), "@leg.R": (0, 0, -0.02)},
                   arms(120, -10), capes(-14, 4, 0, -8), wide)

    def rise_p(k):
        a = 2 * math.pi * k
        return merge({"%body": (0.9, 0.9, 1.12), "crest": (-12 + 4 * math.sin(a), 3 * math.sin(a), 0),
                      "%crest": (0.92, 0.92, 1.3 + 0.08 * math.sin(2 * a)),
                      "leg.L": (10 + 12 * math.sin(a), 0, 4), "leg.R": (10 - 12 * math.sin(a), 0, -4),
                      "@leg.L": (0.0, 0, 0.01), "@leg.R": (0.0, 0, 0.01)},
                     arms(135 + 6 * math.sin(a), -8), capes(-8 + 4 * math.sin(a), 6, 2, -10 + 8 * math.sin(a + 1)),
                     wide)
    rig.action("leap", {0: {}, 3: crouch, 6: spring, 9: rise_p(0)})
    rig.action("rise", {0: rise_p(0), 4: rise_p(0.25), 8: rise_p(0.5), 11: rise_p(0.75), 15: rise_p(1)}, loop=True)

    # glide: the cape spread like wings, arms out, a gentle sway; the hem ripples
    def glide_p(k):
        a = 2 * math.pi * k
        roll = 7 * math.sin(a)
        return merge({"root": (0, roll, 0), "@root": (0, 0, 0.025 * math.sin(2 * a + 0.5)),
                      "%body": (1.04, 1.04, 0.97), "body": (6, 0, 0), "crest": (-24, -roll * 0.6, 0),
                      "%crest": (1.0, 1.0, 1.05 + 0.08 * math.sin(4 * a)),
                      "leg.L": (24 + 6 * math.sin(a), 0, 0), "leg.R": (24 - 6 * math.sin(a), 0, 0),
                      "@leg.L": (0, 0, 0.012), "@leg.R": (0, 0, 0.012)},
                     arms(78 + 6 * math.sin(2 * a), 6),
                     {"cape.L": (22, -60 - 5 * math.sin(2 * a), 0), "cape.R": (22, 60 + 5 * math.sin(2 * a + 0.4), 0),
                      "cape.L2": (6 + 10 * math.sin(4 * a), 8 - 10 * math.sin(2 * a + 1), 0),
                      "cape.R2": (6 + 10 * math.sin(4 * a + 1), -8 + 10 * math.sin(2 * a + 1.4), 0)},
                     {"%eye.L": (1.05, 1, 0.82), "%eye.R": (1.05, 1, 0.82)})
    rig.action("glide", {f: glide_p(f / 36) for f in (0, 4, 9, 13, 18, 22, 27, 31, 36)}, loop=True)

    # fall: the cape billows up behind, arms flail, legs kick, eyes wide
    def fall_p(k):
        a = 2 * math.pi * k
        return merge({"%body": (0.96, 0.96, 1.06), "body": (-6, 0, 4 * math.sin(a)), "crest": (30, 0, 0),
                      "%crest": (1.1, 1.1, 0.75 + 0.1 * math.sin(2 * a)),
                      "leg.L": (-14 + 26 * math.sin(a), 0, 0), "leg.R": (-14 - 26 * math.sin(a), 0, 0),
                      "@leg.L": (0, 0, 0.015), "@leg.R": (0, 0, 0.015)},
                     arms(115 + 20 * math.sin(a), -15 * math.cos(a), 115 - 20 * math.sin(a), 15 * math.cos(a)),
                     capes(105 + 10 * math.sin(2 * a), 12, 24, 30 + 18 * math.sin(2 * a + 1)), wide)
    rig.action("fall", {0: fall_p(0), 4: fall_p(0.25), 8: fall_p(0.5), 11: fall_p(0.75), 15: fall_p(1)}, loop=True)

    squash = merge({"@root": (0, 0, -0.015), "%body": (1.24, 1.24, 0.72), "body": (4, 0, 0), "crest": (24, 0, 0),
                    "%crest": (1.15, 1.15, 0.7), "leg.L": (0, -18, 0), "leg.R": (0, 18, 0)},
                   arms(40, 0), capes(16, 0, 6, 18), {"%eye.L": (1.08, 1, 0.6), "%eye.R": (1.08, 1, 0.6)})
    rig.action("land", {0: merge(squash, {"%body": (1.12, 1.12, 0.86)}), 2: squash,
                        4: {"%body": (0.95, 0.95, 1.06), "crest": (-8, 0, 0)}, 6: {}})

    # die: a jolt, two spins slowing, the crest fizzles out, slumps
    def die_p(turn, crest_s, extra):
        return merge({"root": (0, 0, turn), "%crest": (crest_s, crest_s, crest_s)}, extra)
    jolt = merge({"%body": (0.85, 0.85, 1.25), "@root": (0, 0, 0.05), "crest": (-20, 0, 0)}, arms(120, 0), wide,
                 capes(40, 10, 10, 20))
    spin = merge({"%body": (0.95, 0.95, 1.05), "@root": (0, 0, 0.03)}, arms(70, 0), shut, capes(60, 20, 30, 20))
    keys = {0: {}, 3: die_p(0, 1.3, jolt)}
    for i, f in enumerate((6, 9, 12, 15, 18, 21, 24, 27)):
        keys[f] = die_p(90 * (i + 1) * (1 - 0.02 * i), max(0.05, 1.1 - 0.15 * i), spin)
    slump = merge({"%body": (1.2, 1.2, 0.72), "@root": (0, 0, -0.02), "body": (16, 0, 10), "top": (10, 0, 0)},
                  arms(-10, -10), shut, capes(-8, 0, 0, 0), {"leg.L": (-50, 0, 10), "leg.R": (-40, 0, -10),
                                                             "@leg.L": (0, -0.04, 0.03), "@leg.R": (0, -0.03, 0.02)})
    keys[31] = die_p(650, 0.02, slump)
    keys[34] = die_p(655, 0.01, merge(slump, {"%body": (1.14, 1.14, 0.78)}))
    keys[36] = die_p(655, 0.01, slump)
    rig.action("die", keys)

    # cheer: two hops, arms up, cape flapping, crest flaring
    def cheer_p(h, sq, arm, flap):
        return merge({"@root": (0, 0, h), "%body": (1 + sq, 1 + sq, 1 - 1.5 * sq), "crest": (-6, 0, 0),
                      "%crest": (1.1 + h * 3, 1.1 + h * 3, 1.2 + h * 6), "leg.L": (-12 * h / 0.1, 0, 0),
                      "leg.R": (-12 * h / 0.1, 0, 0)},
                     arms(arm, -10), capes(20 + flap, 30, 20, flap), happy)
    rig.action("cheer", {0: cheer_p(0, 0.1, 100, 0), 5: cheer_p(0.07, -0.06, 150, 25), 8: cheer_p(0.1, -0.02, 160, 10),
                         12: cheer_p(0.02, -0.04, 140, -10), 15: cheer_p(0, 0.12, 100, 0),
                         20: cheer_p(0.07, -0.06, 150, 25), 23: cheer_p(0.1, -0.02, 160, 10),
                         27: cheer_p(0.02, -0.04, 140, -10), 30: cheer_p(0, 0.1, 100, 0)}, loop=True)
    rig.save("sprite")


def star_mesh(r_out, r_in, depth, material, name="star", points=5, core=None):
    """A faceted star in the XZ plane (point up), its front (centre raised by `depth`) towards -Y, back to +Y."""
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
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return K.finish(o, material, smooth=0)


# ------------------------------------------------------------------ the rocket

def rocket():
    reset()
    paper = mat("rocket_paper", (0.9, 0.12, 0.1), 0.45, coat=0.4)
    stripe = mat("rocket_stripe", (0.97, 0.95, 0.9), 0.45, coat=0.4)
    trim = mat("rocket_trim", (0.95, 0.7, 0.22), 0.3, metal=0.85)
    stick = mat("rocket_stick", (0.6, 0.4, 0.22), 0.75)
    fuse = mat("rocket_fuse", (0.32, 0.22, 0.12), 0.85)
    R = 0.08
    z0, z1 = -0.075, 0.115            # the tube
    parts = []
    tube_o = lathe_r([(0.0, z1), (R * 0.9, z1), (R, z1 - 0.008), (R, z0 + 0.008), (R * 0.9, z0), (0.0, z0)], paper,
                     segs=24, name="tube", smooth=50)
    parts.append(tube_o)
    # a spiral stripe wound round the tube
    for ph in (0.0, math.pi):
        pts = []
        for k in range(41):
            u = k / 40
            a = ph + u * 2 * math.pi * 1.25
            pts.append(Vector((R * 1.005 * math.cos(a), R * 1.005 * math.sin(a), z0 + 0.02 + u * (z1 - z0 - 0.04))))
        rib = tube(pts, [0.013] * len(pts), stripe, verts=6, caps=True, name="stripe")
        for v in rib.data.vertices:   # flatten the stripe onto the tube
            p = Vector((v.co.x, v.co.y, 0))
            d = p.length
            if d > 1e-6:
                nd = R + (d - R) * 0.35
                v.co.x, v.co.y = v.co.x / d * nd, v.co.y / d * nd
        rib.data.update()
        parts.append(rib)
    # gold bands, the nose cone and fins
    parts += [torus(R * 1.02, 0.008, (0, 0, z1 - 0.006), trim, verts=24, minor=6),
              torus(R * 1.02, 0.008, (0, 0, z0 + 0.006), trim, verts=24, minor=6)]
    parts.append(lathe_r([(0.0, 0.19), (0.012, 0.185), (0.035, 0.165), (0.058, 0.137), (R * 1.02, z1 + 0.002),
                          (0.0, z1)], trim, segs=24, name="nose", smooth=50))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        fin = K.prism([(0.0, 0.0), (0.05, -0.03), (0.05, -0.05), (0.0, -0.03)], 0.01, (0, 0, 0), trim, bevel=0.003)
        fin.data.transform(Matrix.Translation(d * (R - 0.004) + Vector((0, 0, z0 + 0.03)))
                           @ Matrix.Rotation(a, 4, "Z"))
        parts.append(fin)
    # the stick behind, down to the bottom
    parts.append(rod((0, 0.075, z1 - 0.02), (0, 0.075, -0.225), 0.011, stick, verts=8))
    parts.append(torus(0.016, 0.005, (0, 0.075, z0 + 0.02), fuse, verts=10, minor=4))
    parts.append(torus(0.016, 0.005, (0, 0.075, z1 - 0.04), fuse, verts=10, minor=4))
    # the fuse: a twisted cord curling up out of the nose
    fp = [Vector((0, 0, 0.183)), Vector((0.002, 0, 0.198)), Vector((0.012, 0.0, 0.212)), Vector((0.028, 0.0, 0.219)),
          Vector((0.042, 0.0, 0.216))]
    parts.append(tube(fp, [0.009, 0.0085, 0.008, 0.0075, 0.007], fuse, verts=8, caps=True, name="fuse"))
    for k in range(9):   # the twist of the cord
        u = (k + 0.5) / 9
        i = min(3, int(u * 4))
        p = fp[i].lerp(fp[i + 1], u * 4 - i)
        parts.append(sphere(0.0062, p + Vector((0, -0.006 * (1 if k % 2 else -1), 0.003)), fuse, segs=6, rings=4))
    tip = empty("fuse_tip")
    tip.location = (0.048, 0.0, 0.215)
    root = join(parts, "rocket")
    export_anim(root, "rocket", [(tip, root)], anim=False)


# ------------------------------------------------------------------ the imp (walker, flyer)

def imp(wings):
    reset()
    name = "flyer" if wings else "walker"
    skin = mat("walker_skin", (0.42, 0.24, 0.72), 0.55, coat=0.2)
    bel = mat("walker_belly", (0.68, 0.52, 0.92), 0.6)
    cloak = mat("walker_cloak", (0.05, 0.38, 0.4), 0.7)
    ear_m = mat("walker_ear", (0.95, 0.5, 0.75), 0.55)
    eye_m = mat("walker_eye_glow", (1.0, 0.9, 0.2), 0.2, emit=3.0)
    pupil = mat("walker_pupil", (0.02, 0.01, 0.03), 0.2, coat=1.0)
    mouth = mat("walker_mouth", (0.2, 0.02, 0.08), 0.5)
    tooth = mat("walker_tooth", (1.0, 0.98, 0.9), 0.3)
    horn = mat("walker_horn", (0.95, 0.85, 0.6), 0.35, coat=0.5)
    stick = mat("walker_stick", (0.35, 0.22, 0.12), 0.8)
    frame = mat("walker_lamp_frame", (0.18, 0.18, 0.2), 0.4, metal=0.8)
    lamp = mat("walker_lamp_glow", (0.4, 1.0, 0.5), 0.3, emit=4.0, emit_color=(0.35, 1.0, 0.45))
    HC = Vector((0, -0.01, 0.37))
    bones = {"root": ((0, 0, 0), (0, 0, 0.04), None),
             "body": ((0, 0, 0.1), (0, 0, 0.29), "root"),
             "head": ((0, 0, 0.29), (0, 0, 0.48), "body"),
             "ear.L": ((0.11, 0.0, 0.4), (0.25, 0.02, 0.5), "head"),
             "ear.R": ((-0.11, 0.0, 0.4), (-0.25, 0.02, 0.5), "head"),
             "arm.L": ((0.08, -0.01, 0.25), (0.17, -0.07, 0.2), "body"),
             "arm.R": ((-0.08, -0.01, 0.25), (-0.16, -0.05, 0.16), "body"),
             "lamp": ((0.25, -0.13, 0.33), (0.25, -0.13, 0.25), "arm.L"),
             "leg.L": ((0.05, 0.0, 0.12), (0.055, -0.01, 0.02), "root"),
             "leg.R": ((-0.05, 0.0, 0.12), (-0.055, -0.01, 0.02), "root"),
             "tail": ((0, 0.09, 0.14), (0, 0.2, 0.18), "body")}
    if wings:
        bones.update({"wing.L": ((0.05, 0.08, 0.27), (0.19, 0.12, 0.33), "body"),
                      "wing.R": ((-0.05, 0.08, 0.27), (-0.19, 0.12, 0.33), "body"),
                      "wing.L2": ((0.19, 0.12, 0.33), (0.42, 0.12, 0.36), "wing.L"),
                      "wing.R2": ((-0.19, 0.12, 0.33), (-0.42, 0.12, 0.36), "wing.R")})
    rig = TurnRig(bones, 0, fps=FPS)

    # the cloak: a ragged bell from the shoulders to the shins, a lighter belly peeping out
    def ragged(k, z):
        return 1.0 + (0.08 * math.sin(k * 2.1) if z < 0.12 else 0.0)
    clo = lathe_r([(0.0, 0.305), (0.05, 0.3), (0.08, 0.27), (0.1, 0.22), (0.12, 0.15), (0.14, 0.09), (0.13, 0.085)],
                  cloak, segs=18, radial=ragged, name="cloak", smooth=50)
    for v in clo.data.vertices:   # a ragged, zigzag hem
        if v.co.z < 0.1:
            a = math.atan2(v.co.y, v.co.x)
            v.co.z += 0.02 * (1 if int((a + math.pi) / (2 * math.pi) * 9) % 2 else -1)
    clo.data.update()
    belly = ell((0, -0.07, 0.2), (0.06, 0.04, 0.07), bel, segs=12, rings=8)
    head = ell(HC, (0.14, 0.12, 0.115), skin, segs=24, rings=14)
    for v in head.data.vertices:   # a broad jaw, a narrower crown
        t = (v.co.z - HC.z) / 0.115
        k = 1.0 - 0.12 * max(0.0, t)
        v.co.x *= k
    head.data.update()

    def w_bh(p):
        t = smoothstep(0.27, 0.32, p.z)
        return {"body": 1 - t + 1e-4, "head": t + 1e-4}
    rig.custom(w_bh, clo, belly, head)

    hp = []
    for s in (-1, 1):
        ec = Vector((s * 0.052, -0.095, 0.4))
        hp.append(ell(ec, (0.04, 0.025, 0.036), eye_m, yaw=-s * 18, roll=s * 12, segs=12, rings=8))
        hp.append(ell(ec + Vector((-s * 0.006, -0.022, -0.004)), (0.013, 0.006, 0.024), pupil, yaw=-s * 18,
                      segs=8, rings=6))
        lid = hemi(0.047, (0, 0, 0), (0, 0, 1), skin, cut=0.25, segs=14, rings=8)   # sly lids slanting down inward
        lid.data.transform(Matrix.Translation(ec + Vector((0, 0.004, 0.0))) @ Matrix.Rotation(math.radians(-s * 24), 4, "Y")
                           @ Matrix.Rotation(math.radians(-14), 4, "X"))
        hp.append(lid)
        hp.append(cone((s * 0.05, -0.04, 0.46), (s * 0.075, -0.01, 0.52), 0.02, horn, verts=8))
        hp.append(sphere(0.012, (s * 0.1, -0.075, 0.36), ear_m, segs=8, rings=6))   # blush spots
    # a long pointed nose, drooping a touch
    hp.append(tube([(0, -0.1, 0.375), (0, -0.14, 0.365), (0, -0.175, 0.35), (0, -0.19, 0.335)],
                   [0.026, 0.02, 0.012, 0.004], skin, verts=10, caps=True, name="nose"))
    # a wide sly grin with two little fangs
    grin = []
    for k in range(11):
        a = math.pi * (1.1 + 0.8 * k / 10)
        x = 0.085 * math.cos(a)
        z = 0.322 + 0.025 * math.sin(a) + 0.012 * (x / 0.085) ** 2
        y = HC.y - 0.12 * math.sqrt(max(0.0, 1 - (x / 0.14) ** 2 - ((z - HC.z) / 0.115) ** 2)) - 0.003
        grin.append((x, y, z))
    hp.append(tube(grin, [0.007] + [0.01] * 9 + [0.007], mouth, verts=6, caps=True, name="grin"))
    for s in (-1, 1):
        hp.append(cone((s * 0.03, -0.112, 0.305), (s * 0.03, -0.112, 0.288), 0.009, tooth, verts=6))
    rig.rigid("head", hp)

    # long pointed ears
    for s, side in ((1, "L"), (-1, "R")):
        e = cone((s * 0.1, 0.0, 0.39), (s * 0.27, 0.03, 0.51), 0.05, skin, verts=10)
        for v in e.data.vertices:
            v.co.y = v.co.y * 0.45 + (v.co.x * s - 0.1) * 0.1
        inner = cone((s * 0.11, -0.014, 0.395), (s * 0.245, 0.012, 0.49), 0.028, ear_m, verts=8)
        for v in inner.data.vertices:
            v.co.y = -0.014 + (v.co.y + 0.014) * 0.3 + (v.co.x * s - 0.1) * 0.1 - 0.006
        rig.rigid("ear." + side, e, inner)

    # arms: the left holds a crooked stick out front with the lamp hanging from its tip; the right has claws
    armL = [rod((0.07, -0.01, 0.26), (0.165, -0.07, 0.2), 0.022, skin, verts=8),
            sphere(0.028, (0.17, -0.075, 0.2), skin, segs=10, rings=6),
            tube([(0.15, -0.07, 0.16), (0.18, -0.09, 0.22), (0.21, -0.11, 0.3), (0.235, -0.125, 0.345),
                  (0.252, -0.13, 0.34)], [0.01, 0.011, 0.01, 0.009, 0.008], stick, verts=6, caps=True, name="stick")]
    rig.rigid("arm.L", armL)
    lp = [tube([(0.252, -0.13, 0.335), (0.25, -0.13, 0.3)], [0.003, 0.003], frame, verts=4, caps=False),
          cyl(0.03, 0.05, (0.25, -0.13, 0.255), lamp, verts=10),
          cyl(0.036, 0.012, (0.25, -0.13, 0.285), frame, verts=10),
          cyl(0.016, 0.012, (0.25, -0.13, 0.296), frame, r2=0.004, verts=10),
          cyl(0.036, 0.012, (0.25, -0.13, 0.226), frame, verts=10),
          torus(0.012, 0.003, (0.25, -0.13, 0.305), frame, verts=8, minor=4, rot=(math.pi / 2, 0, 0))]
    for k in range(4):   # the cage bars
        a = math.pi / 4 + k * math.pi / 2
        lp.append(rod((0.25 + 0.032 * math.cos(a), -0.13 + 0.032 * math.sin(a), 0.23),
                      (0.25 + 0.032 * math.cos(a), -0.13 + 0.032 * math.sin(a), 0.282), 0.004, frame, verts=4))
    rig.rigid("lamp", lp)
    armR = [rod((-0.07, -0.01, 0.26), (-0.155, -0.05, 0.165), 0.022, skin, verts=8),
            sphere(0.028, (-0.16, -0.052, 0.158), skin, segs=10, rings=6)]
    armR += [cone((-0.16 + dx, -0.07, 0.15), (-0.16 + dx * 1.5, -0.085, 0.125), 0.007, horn, verts=5)
             for dx in (-0.014, 0.0, 0.014)]
    rig.rigid("arm.R", armR)

    # thin legs and pointed shoes curling up at the toe
    for s, side in ((1, "L"), (-1, "R")):
        lg = [rod((s * 0.05, 0.0, 0.12), (s * 0.055, -0.005, 0.03), 0.017, skin, verts=8),
              ell((s * 0.055, -0.03, 0.022), (0.03, 0.05, 0.022), cloak, segs=12, rings=6),
              tube([(s * 0.055, -0.06, 0.02), (s * 0.055, -0.09, 0.025), (s * 0.055, -0.105, 0.045)],
                   [0.016, 0.009, 0.003], cloak, verts=8, caps=True, name="toe")]
        rig.rigid("leg." + side, lg)
    # a thin tail with an arrow tip
    tl = [tube([(0, 0.08, 0.14), (0, 0.15, 0.12), (0, 0.2, 0.16), (0, 0.21, 0.22)], [0.012, 0.01, 0.008, 0.007],
               skin, verts=8, caps=False, name="tail"),
          K.prism([(-0.025, 0.0), (0.025, 0.0), (0.0, 0.045)], 0.01, (0, 0.21, 0.215), ear_m, bevel=0.003)]
    rig.rigid("tail", tl)

    if wings:
        membrane = mat("walker_wing", (0.25, 0.1, 0.38), 0.6)
        wbone = mat("walker_wing_bone", (0.42, 0.24, 0.72), 0.55)
        for s, side in ((1, "L"), (-1, "R")):
            poly = [(0.05, 0.3), (0.19, 0.345), (0.32, 0.37), (0.44, 0.375), (0.4, 0.31), (0.36, 0.26),
                    (0.32, 0.27), (0.27, 0.22), (0.22, 0.235), (0.16, 0.19), (0.1, 0.21), (0.05, 0.22)]
            poly = [(s * x, z) for x, z in poly]
            if s < 0:
                poly = poly[::-1]
            w = K.prism(poly, 0.008, (0, 0.11, 0), membrane, bevel=0.002)
            ribs = [tube([(s * 0.05, 0.11, 0.3), (s * 0.19, 0.11, 0.345), (s * 0.32, 0.11, 0.37), (s * 0.44, 0.11, 0.378)],
                         [0.012, 0.011, 0.008, 0.003], wbone, verts=6, caps=True, name="wingarm")]
            for tip in ((0.36, 0.26), (0.27, 0.22), (0.16, 0.19)):
                ribs.append(rod((s * 0.19 + s * 0.06 * (tip[0] > 0.3), 0.11, 0.345), (s * tip[0], 0.11, tip[1]),
                                0.005, wbone, r2=0.002, verts=5))
            ribs.append(cone((s * 0.19, 0.11, 0.35), (s * 0.2, 0.11, 0.385), 0.01, horn, verts=5))   # the thumb claw

            def w_wing(p, side=side, s=s):
                t = smoothstep(0.15, 0.24, p.x * s)
                return {"wing." + side: 1 - t + 1e-4, "wing." + side + "2": t + 1e-4}
            rig.custom(w_wing, w, ribs)
    rig.build(name)

    if not wings:
        # walk: a sneaky tiptoe, 0.6 s; f0 left foot forward, f9 right foot forward
        def walk_p(ph, up):
            sgn = 1 if ph == 0 else -1
            sw = 28 * sgn * (1 - up)
            return merge({"@root": (0, 0, 0.03 * up), "body": (8, 0, 6 * sgn), "head": (-6, 0, -8 * sgn),
                          "%body": (1 + 0.04 * (1 - up), 1 + 0.04 * (1 - up), 1 - 0.05 * (1 - up)),
                          "leg.L": (-sw, 0, 0), "leg.R": (sw, 0, 0),
                          "@leg.L": (0, 0, 0.035 * up * (sgn < 0)), "@leg.R": (0, 0, 0.035 * up * (sgn > 0)),
                          "arm.L": (-10 + 8 * sgn, 0, 0), "arm.R": (30 * sgn, 10, 0),
                          "lamp": (22 * sgn * (1 - up) - 6, 0, 8 * sgn), "tail": (10 * up, 0, 30 * sgn),
                          "ear.L": (0, -8 * up, 0), "ear.R": (0, 8 * up, 0)})
        rig.action("walk", {0: walk_p(0, 0), 4: walk_p(0, 1), 9: walk_p(1, 0), 13: walk_p(1, 1), 18: walk_p(0, 0)},
                   loop=True)
        rig.save(name)
        return

    # fly: two-stroke flaps, 0.5 s; downstroke f0 -> f7 (wings high to low), upstroke back
    def fly_p(k):
        a = 2 * math.pi * k
        flap = math.cos(a)          # 1: wings up, -1: wings down
        return merge({"@root": (0, 0, 0.03 * -math.sin(a)), "body": (10, 0, 0), "head": (-8 + 4 * flap, 0, 0),
                      "leg.L": (16 + 12 * math.sin(a), 0, 0), "leg.R": (16 + 12 * math.sin(a + 0.6), 0, 0),
                      "arm.L": (-8, 0, 0), "arm.R": (20 + 8 * math.sin(a), 20, 0),
                      "lamp": (-12 + 14 * math.sin(a + 1), 0, 0), "tail": (20 + 10 * flap, 0, 20 * math.sin(a)),
                      "ear.L": (0, 10 * flap, 0), "ear.R": (0, -10 * flap, 0)},
                     lsc("wing.L", (6, -42 * flap, 10 + 6 * flap)), lsc("wing.L2", (0, -24 * flap + 8, 0)))
    rig.action("fly", {f: fly_p(f / 15) for f in (0, 2, 4, 6, 8, 10, 12, 15)}, loop=True)
    rig.save(name)


def walker():
    imp(False)


def flyer():
    imp(True)


# ------------------------------------------------------------------ the orb

def orb():
    reset()
    core_m = mat("orb_core_glow", (0.6, 0.95, 1.0), 0.3, emit=2.2, emit_color=(0.4, 0.9, 1.0))
    face_m = mat("orb_face", (0.04, 0.02, 0.15), 0.4)
    flame_m = mat("orb_flame_glow", (0.15, 0.4, 1.0), 0.4, emit=1.4, emit_color=(0.1, 0.35, 1.0))
    arc_m = mat("orb_arc_glow", (0.85, 0.6, 1.0), 0.3, emit=4.0, emit_color=(0.8, 0.45, 1.0))
    mote_m = mat("orb_mote_glow", (0.85, 0.95, 1.0), 0.3, emit=5.0)
    parts = [sphere(0.13, (0, 0, 0), core_m, segs=24, rings=14)]
    for s in (-1, 1):   # hollow, mischievous eyes and a jagged grin
        e = ell((s * 0.045, -0.118, 0.025), (0.026, 0.012, 0.036), face_m, yaw=-s * 20, roll=-s * 25, segs=10, rings=6)
        parts.append(e)
    grin = []
    for k in range(9):
        a = math.pi * (1.15 + 0.7 * k / 8)
        x, z = 0.07 * math.cos(a), -0.02 + 0.04 * math.sin(a) + (0.008 if k % 2 else -0.004)
        y = -math.sqrt(max(0.0, 0.13 ** 2 - x * x - z * z)) - 0.002
        grin.append((x, y, z))
    parts.append(tube(grin, [0.008] * len(grin), face_m, verts=5, caps=True, name="grin"))
    rnd = random.Random(9)
    for d in fib_dirs(46):   # a shell of cold-fire wisps, swept up, longer on top (a tail of flame)
        if d.y < -0.55 and abs(d.z) < 0.6:
            continue   # keep the face clear
        base = d * 0.11
        ln = 0.07 + 0.05 * max(0.0, d.z) + rnd.uniform(0, 0.03)
        tip = d * (0.11 + ln) + Vector((0, 0, 0.04 + 0.05 * max(0.0, d.z)))
        parts.append(flame(base, tip, 0.045, flame_m, bend=(rnd.uniform(-0.01, 0.01), 0, 0.01), verts=6))
    core = join(parts, "orb")
    arcs = []
    tilts = ((-65, 20), (60, -35))   # each ring spins about its own axis (local X), then is tilted by Y and Z
    for i, r in enumerate((0.225, 0.235)):
        pts = []
        for k in range(49):
            a = 2 * math.pi * k / 48
            rr = r + (0.022 if k % 2 else -0.012) * (1 if (k // 3) % 2 else 0.6)
            pts.append(Vector((rr * math.cos(a), rr * math.sin(a), (0.018 if k % 3 == 0 else -0.01))))
        arc = tube(pts, [0.006] * len(pts), arc_m, verts=4, caps=False, name="arc")
        arc.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))   # into the YZ plane: its axis along X
        arcs.append(join([arc], "arcs_%d" % i))
    motes = join([ico(0.016, (0.24 * math.cos(a), 0.24 * math.sin(a), 0.06 * math.sin(3 * a)), mote_m, sub=1)
                  for a in (k * math.pi / 2 + 0.3 for k in range(4))], "motes")
    # spin: 1 s; the arc rings counter-rotate in their own planes, the motes orbit, the core pulses
    n = 30
    for i, a in enumerate(arcs):
        ty, tz = (math.radians(x) for x in tilts[i])
        sgn = 1 if i == 0 else -1
        animate(a, "spin", {f: {"rot": (sgn * 2 * math.pi * f / n, ty, tz)} for f in range(0, n + 1, 5)})
    animate(motes, "spin", {f: {"rot": (0, 0, -2 * math.pi * f / n)} for f in range(0, n + 1, 5)})
    pk = {}
    for f in range(0, n + 1, 5):
        s = 1 + 0.06 * math.sin(2 * math.pi * 2 * f / n)
        pk[f] = {"scale": (s, s, 1 + 0.08 * math.sin(2 * math.pi * 2 * f / n + 0.6))}
    animate(core, "spin", pk, linear=False)
    root = empty("orb_root")
    export_anim(root, "orb", [(core, root)] + [(a, root) for a in arcs] + [(motes, root)])


# ------------------------------------------------------------------ the star, the letters, the spark

def star():
    reset()
    gold = mat("star_glow", (1.0, 0.72, 0.12), 0.25, metal=0.3, emit=1.1, emit_color=(1.0, 0.62, 0.08))
    pale = mat("star_core_glow", (1.0, 0.92, 0.6), 0.2, emit=2.2)
    body = star_mesh(0.315, 0.142, 0.08, gold, name="star_body")
    front = star_mesh(0.15, 0.068, 0.04, pale, name="star_front")
    back = star_mesh(0.15, 0.068, 0.04, pale, name="star_back")
    front.data.transform(Matrix.Translation((0, -0.042, 0)))
    back.data.transform(Matrix.Translation((0, 0.042, 0)))
    export(join([body, front, back], "star"), "star")


def letter(ch):
    reset()
    key = ch.lower()
    col = {"b": (0.85, 0.1, 0.55), "e": (0.05, 0.6, 0.6)}[key]
    glow = {"b": (1.0, 0.85, 0.95), "e": (0.85, 1.0, 0.95)}[key]
    face = mat("letter_%s_face" % key, col, 0.35, coat=0.6)
    rim = mat("letter_rim_glow", (1.0, 0.75, 0.25), 0.25, metal=0.6, emit=1.6, emit_color=(1.0, 0.65, 0.15))
    let = mat("letter_%s_glow" % key, glow, 0.3, emit=3.0)
    R, T = 0.215, 0.05
    parts = [cyl(R, T, (0, 0, 0), face, rot=(math.pi / 2, 0, 0), verts=40, bevel=0.008, segs=2),
             torus(R, 0.032, (0, 0, 0), rim, rot=(math.pi / 2, 0, 0), verts=40, minor=10, scale=None)]
    for k in range(24):   # milled studs round the rim
        a = 2 * math.pi * k / 24
        for sgn in (-1, 1):
            parts.append(sphere(0.008, (0.245 * math.cos(a), sgn * 0.017, 0.245 * math.sin(a)), rim, segs=6, rings=4))
    for sgn in (-1, 1):
        cu = bpy.data.curves.new("glyph", "FONT")
        cu.body = ch.upper()
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.size = 0.3
        cu.extrude = 0.012
        cu.offset = 0.008
        cu.bevel_depth = 0.004
        cu.bevel_resolution = 1
        o = bpy.data.objects.new("glyph", cu)
        bpy.context.scene.collection.objects.link(o)
        K.select(o)
        bpy.ops.object.convert(target="MESH")
        o = K.active()
        o.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
        if sgn > 0:
            o.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
        cz = (min(v.z for v in bb) + max(v.z for v in bb)) / 2
        o.data.transform(Matrix.Translation((-cx, sgn * (T / 2 + 0.008), -cz)))
        K.finish(o, let, smooth=30)
        parts.append(o)
    export(join(parts, "letter_" + key), "letter_" + key)


def letter_b():
    letter("B")


def letter_e():
    letter("E")


def spark():
    reset()
    gem_m = mat("spark_gem_glow", (1.0, 0.8, 0.3), 0.15, metal=0.2, emit=1.8, emit_color=(1.0, 0.72, 0.2))
    ray_m = mat("spark_ray_glow", (1.0, 0.95, 0.75), 0.2, emit=3.5)
    # a brilliant-cut gem, point down, its axis along Y (towards the camera): flat-shaded facets
    gem = lathe_r([(0.0, 0.09), (0.06, 0.09), (0.11, 0.045), (0.12, 0.03), (0.0, -0.11)], gem_m, segs=8,
                  name="gem", smooth=0)
    gem.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))   # the table towards -Y (the camera)
    gem = join([gem], "spark")
    rays = []
    for k in range(8):
        a = k * math.pi / 4
        ln = 0.2 if k % 2 == 0 else 0.13
        w = 0.03 if k % 2 == 0 else 0.022
        d = Vector((math.cos(a), 0, math.sin(a)))
        side = Vector((-math.sin(a), 0, math.cos(a)))
        bm = bmesh.new()
        p0, p1 = d * 0.06, d * ln
        mid = d * (0.06 + (ln - 0.06) * 0.3)
        vs = [bm.verts.new(p0), bm.verts.new(mid + side * w), bm.verts.new(p1), bm.verts.new(mid - side * w),
              bm.verts.new(mid + Vector((0, -0.012, 0))), bm.verts.new(mid + Vector((0, 0.012, 0)))]
        for f in ((vs[0], vs[1], vs[4]), (vs[1], vs[2], vs[4]), (vs[2], vs[3], vs[4]), (vs[3], vs[0], vs[4]),
                  (vs[1], vs[0], vs[5]), (vs[2], vs[1], vs[5]), (vs[3], vs[2], vs[5]), (vs[0], vs[3], vs[5])):
            bm.faces.new(f)
        rays.append(new_obj("ray", bm, ray_m, smooth=0))
    rays = join(rays, "rays")
    n = 30
    animate(gem, "spin", {f: {"rot": (0, 0, 2 * math.pi * f / n)} for f in range(0, n + 1, 5)})
    rk = {}
    for f in range(0, n + 1, 5):
        s = 1 + 0.18 * math.sin(2 * math.pi * 2 * f / n)
        rk[f] = {"rot": (0, -0.5 * math.pi * f / n, 0), "scale": (s, s, s)}
    animate(rays, "spin", rk, linear=True)
    root = empty("spark_root")
    export_anim(root, "spark", [(gem, root), (rays, root)])


JOBS = {"sprite": sprite, "rocket": rocket, "walker": walker, "flyer": flyer, "orb": orb, "star": star,
        "letter_b": letter_b, "letter_e": letter_e, "spark": spark}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    bpy.context.scene.render.fps = FPS
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
