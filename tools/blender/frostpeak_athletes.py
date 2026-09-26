"""Frostpeak Games athletes: one humanoid rig with two outfits, the speed skater (skin suit, hood, blades) and the
ski jumper (suit, helmet, goggles, long skis on their own bones so they can open into a V). The material named
"suit" is recoloured per nation in the game. Rigid parts on bones, keyed animations, one glTF animation per action.
Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/frostpeak_athletes.py -- godot/games/frostpeak/art/models
About 1.8 m tall, feet at z = 0, facing -Y.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *  # mat, sphere, box, limb, BONES, clear, keys, rig_export

def shell(rings, a0, a1, bone, material, thick=0.006, segs=16, subsurf=1):
    """An open, curved panel over the body: arcs from angle a0 to a1 (degrees; -90 is the front, 0 the left side)
    through ellipses [(z, half width, half depth, y centre)], given a thickness. Bibs, side panels, the hood."""
    me = bpy.data.meshes.new("shell")
    bm = bmesh.new()
    rows = []
    for z, rx, ry, cy in rings:
        row = []
        for i in range(segs + 1):
            a = math.radians(a0 + (a1 - a0) * i / segs)
            row.append(bm.verts.new((rx * math.cos(a), cy + ry * math.sin(a), z)))
        rows.append(row)
    for k in range(len(rows) - 1):
        for i in range(segs):
            bm.faces.new((rows[k][i], rows[k][i + 1], rows[k + 1][i + 1], rows[k + 1][i]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("shell", me)
    bpy.context.collection.objects.link(o)
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    if subsurf:
        m = o.modifiers.new("s", "SUBSURF")
        m.levels = subsurf
        bpy.ops.object.modifier_apply(modifier=m.name)
    m = o.modifiers.new("t", "SOLIDIFY")
    m.thickness = thick
    m.offset = 1.0
    bpy.ops.object.modifier_apply(modifier=m.name)
    return tag(o, bone, material)


# the torso's own ellipses (see humanoid.athletic_body), grown a little so panels sit on the suit
TORSO = [(1.04, 0.155, 0.1, 0.0), (1.12, 0.143, 0.095, 0.0), (1.2, 0.156, 0.102, 0.0), (1.29, 0.178, 0.112, -0.005),
         (1.37, 0.196, 0.108, 0.0), (1.42, 0.2, 0.096, 0.0)]
PELVIS = [(0.86, 0.12, 0.085, 0.0), (0.9, 0.16, 0.1, 0.0), (0.98, 0.175, 0.108, 0.0), (1.06, 0.162, 0.104, 0.0)]


def grown(rings, k=1.035, zlo=-1.0, zhi=9.0):
    return [(z, rx * k + 0.002, ry * k + 0.002, cy) for z, rx, ry, cy in rings if zlo <= z <= zhi]


def arc(center, rx, ry, z, a0, a1, n=9):
    """Points round the head at height z, for visors and bands."""
    cx, cy = center
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))), z) for i in range(n)]


def body(kind):
    suit = mat("suit", (0.85, 0.15, 0.15), 0.3, coat=0.5)
    trim = mat("suit_trim", (0.96, 0.96, 0.96), 0.35, coat=0.3)
    accent = mat("suit_accent", (0.1, 0.2, 0.6), 0.3, coat=0.5)  # recoloured per nation (its flag's other colour)
    skin = mat("skin", (0.9, 0.68, 0.54), 0.55)
    white = mat("eye_white", (0.95, 0.95, 0.93), 0.2)
    iris = mat("iris", (0.15, 0.25, 0.4), 0.1, coat=1.0)
    glove = mat("gloves", (0.1, 0.1, 0.12), 0.5)
    boot = mat("athlete_boot", (0.08, 0.08, 0.1), 0.35, coat=0.5)
    visor = mat("goggles", (0.25, 0.55, 0.85), 0.03, 0.8, coat=1.0)
    frame = mat("goggle_frame", (0.06, 0.06, 0.07), 0.4)
    number = mat("bib_number", (0.08, 0.08, 0.1), 0.4)
    seam = mat("seam", (0.05, 0.05, 0.07), 0.6)
    athletic_body(suit, skin, white, iris, hair=None, glove=glove, boot=boot)
    # accent panels down both sides of the body, from the armpit to the hip
    for a0, a1 in ((-28, 28), (152, 208)):
        shell(grown(TORSO, zhi=1.38), a0, a1, "spine", accent, segs=8)
        shell(grown(PELVIS, zlo=0.89), a0, a1, "hips", accent, segs=8)
    # the zip and the seams under the chest
    muscle_limb([(0, -0.114, 1.44, 0.004), (0, -0.121, 1.3, 0.004), (0, -0.112, 1.12, 0.004)], "spine", seam, 6, 0)
    # stripes down the outside of the legs and arms, in the accent colour with a white piping
    for s_, side in ((1, "L"), (-1, "R")):
        muscle_limb([(0.178 * s_, 0, 0.92, 0.014), (0.172 * s_, -0.01, 0.75, 0.014), (0.152 * s_, 0, 0.55, 0.011)], "thigh." + side, accent, 8, 0)
        muscle_limb([(0.153 * s_, 0, 0.56, 0.01), (0.157 * s_, 0.01, 0.4, 0.012), (0.137 * s_, 0, 0.22, 0.008)], "shin." + side, accent, 8, 0)
        muscle_limb([(0.25 * s_, 0, 1.4, 0.012), (0.272 * s_, 0, 1.28, 0.012), (0.29 * s_, 0, 1.15, 0.01)], "arm." + side, trim, 8, 0)
        muscle_limb([(0.296 * s_, -0.004, 1.12, 0.009), (0.307 * s_, -0.01, 1.0, 0.01), (0.3 * s_, -0.02, 0.9, 0.007)], "forearm." + side, trim, 8, 0)
        # a cuff at each wrist and a knee seam
        muscle_limb([(0.268 * s_, -0.02, 0.92, 0.036), (0.269 * s_, -0.021, 0.9, 0.036)], "forearm." + side, accent, 12, 0)
        muscle_limb([(0.1 * s_, -0.05, 0.53, 0.006), (0.1 * s_ + 0.03 * s_, -0.035, 0.52, 0.006)], "shin." + side, seam, 6, 0)
    if kind == "skater":
        # the race bib (small, front and back) with a dark number panel
        for y, sgn in ((-0.117, 1), (0.11, -1)):
            box((0.16, 0.01, 0.14), (0, y, 1.25), "spine", trim)
            box((0.09, 0.012, 0.05), (0, y - 0.003 * sgn, 1.26), "spine", number)
        # the aero hood: open at the face, a seam over the crown
        hood = [(1.55, 0.07, 0.07, 0.01), (1.6, 0.098, 0.102, 0.008), (1.66, 0.103, 0.11, 0.008), (1.72, 0.098, 0.106, 0.008),
                (1.77, 0.075, 0.082, 0.008), (1.795, 0.03, 0.035, 0.008)]
        shell(hood, -45, 225, "head", suit, thick=0.008, segs=18)
        muscle_limb([(0, 0.11, 1.62, 0.006), (0, 0.105, 1.74, 0.006), (0, 0.04, 1.8, 0.006), (0, -0.04, 1.78, 0.006)], "head", accent, 6, 0)
        sphere(0.07, (0, 0.03, 1.575), "head", suit, (1.1, 1.0, 0.6))  # the collar of the hood
        # wraparound glasses: a mirrored band across the eyes, a thin frame over it
        muscle_limb([(p[0], p[1], p[2], 0.018) for p in arc((0, 0.004), 0.1, 0.108, 1.683, -165, -15)], "head", visor, 8, 1)
        muscle_limb([(p[0], p[1], p[2], 0.005) for p in arc((0, 0.004), 0.103, 0.112, 1.703, -165, -15)], "head", frame, 6, 0)
        # clap skates: a low boot, a long blade on a tube, the hinge under the toe
        blade = mat("blade", (0.88, 0.9, 0.93), 0.1, 1.0)
        holder = mat("blade_holder", (0.2, 0.2, 0.22), 0.3, 0.6)
        for s_, side in ((1, "L"), (-1, "R")):
            x = 0.1 * s_
            box((0.006, 0.47, 0.032), (x, -0.07, -0.035), "shin." + side, blade)
            sphere(0.016, (x, -0.305, -0.028), "shin." + side, blade, (0.35, 1.0, 1.0))  # the rounded nose
            muscle_limb([(x, -0.27, -0.015, 0.011), (x, 0.13, -0.015, 0.011)], "shin." + side, holder, 8, 0)
            box((0.035, 0.05, 0.035), (x, -0.14, 0.0), "shin." + side, holder)  # the clap hinge
            box((0.03, 0.04, 0.03), (x, 0.06, 0.0), "shin." + side, holder)  # the heel post
            box((0.106, 0.1, 0.02), (x, 0.03, 0.155), "shin." + side, accent)  # a collar at the ankle
    else:
        # the big bib, front and back, and a band of the accent colour across the shoulders
        for a0, a1 in ((-145, -35), (35, 145)):
            shell(grown(TORSO, 1.06, 1.1, 1.39), a0, a1, "spine", trim, segs=10)
        box((0.12, 0.012, 0.07), (0, -0.125, 1.28), "spine", number)
        box((0.12, 0.012, 0.07), (0, 0.12, 1.28), "spine", number)
        shell(grown(TORSO, 1.04, 1.39, 1.43), -180, 180, "spine", accent, segs=24)
        # helmet: a shell with a raised ridge, large goggles on a strap, a chin strap
        shell_m = mat("helmet", (0.96, 0.96, 0.97), 0.2, coat=1.0)
        sphere(0.118, (0, 0.012, 1.695), "head", shell_m, (0.98, 1.06, 0.93))
        muscle_limb([(0, -0.1, 1.76, 0.012), (0, -0.02, 1.8, 0.014), (0, 0.08, 1.78, 0.012), (0, 0.125, 1.7, 0.01)], "head", accent, 8, 1)
        muscle_limb([(p[0], p[1], p[2], 0.009) for p in arc((0, 0.012), 0.117, 0.124, 1.62, -200, 20, 12)], "head", accent, 8, 0)
        muscle_limb([(p[0], p[1], p[2], 0.028) for p in arc((0, 0.0), 0.1, 0.108, 1.668, -160, -20)], "head", visor, 10, 1)
        muscle_limb([(p[0], p[1], p[2], 0.009) for p in arc((0, 0.0), 0.103, 0.112, 1.668, -20, 200, 11)], "head", mat("strap", (0.1, 0.1, 0.1), 0.5), 6, 0)
        muscle_limb([(0.085, -0.02, 1.64, 0.005), (0.06, -0.06, 1.56, 0.005), (0, -0.075, 1.55, 0.005), (-0.06, -0.06, 1.56, 0.005), (-0.085, -0.02, 1.64, 0.005)], "head", mat("strap", (0.1, 0.1, 0.1), 0.5), 6, 0)
        # tall jumping boots, laced up the shin
        for s_, side in ((1, "L"), (-1, "R")):
            muscle_limb([(0.1 * s_, 0.0, 0.1, 0.052), (0.1 * s_, 0.005, 0.22, 0.05), (0.1 * s_, 0.01, 0.3, 0.052)], "shin." + side, boot, 12, 1)
            for i in range(4):
                box((0.05, 0.008, 0.01), (0.1 * s_, -0.05, 0.14 + i * 0.045), "shin." + side, trim)
        ski = mat("ski", (0.95, 0.78, 0.1), 0.25, coat=0.8)
        ski_edge = mat("ski_edge", (0.1, 0.1, 0.12), 0.3)
        stripe = mat("ski_stripe", (0.85, 0.12, 0.1), 0.3, coat=0.8)
        binding = mat("binding", (0.2, 0.2, 0.22), 0.3, 0.6)
        for s_, side in ((1, "L"), (-1, "R")):
            x = 0.1 * s_
            box((0.11, 2.2, 0.022), (x, -0.45, -0.005), "ski." + side, ski)
            box((0.112, 2.2, 0.006), (x, -0.45, -0.018), "ski." + side, ski_edge)
            box((0.03, 2.1, 0.004), (x, -0.45, 0.007), "ski." + side, stripe)
            # the tip turns up in three steps
            py, pz = -1.53, -0.005
            for i, th in enumerate((0.15, 0.4, 0.7, 1.0)):
                dy, dz = -math.cos(th) * 0.09, math.sin(th) * 0.09
                box((0.11 - i * 0.006, 0.1, 0.02), (x, py + dy * 0.5, pz + dz * 0.5), "ski." + side, ski, rot=(-th, 0, 0))
                py, pz = py + dy, pz + dz
            box((0.07, 0.12, 0.04), (x, -0.13, 0.03), "ski." + side, binding)  # toe piece
            box((0.075, 0.08, 0.035), (x, 0.13, 0.03), "ski." + side, binding)   # heel plate
            muscle_limb([(x - 0.04, -0.12, 0.04, 0.004), (x - 0.045, 0.08, 0.1, 0.004)], "ski." + side, binding, 4, 0)  # the heel cable
            muscle_limb([(x + 0.04, -0.12, 0.04, 0.004), (x + 0.045, 0.08, 0.1, 0.004)], "ski." + side, binding, 4, 0)


def build(kind):
    clear()
    body(kind)
    acts = {}
    crouch = {"spine": (55, 0, 0), "head": (-40, 0, 0), "thigh.L": (-60, 0, 0), "thigh.R": (-60, 0, 0),
              "shin.L": (80, 0, 0), "shin.R": (80, 0, 0), "@root": (0, 0, -0.28)}
    acts["idle"] = ({1: {"head": (0, 0, 5)}, 30: {"head": (4, 0, -5), "spine": (3, 0, 0)}, 60: {"head": (0, 0, 5)}})
    acts["wave"] = ({1: {"arm.R": (0, 0, -150), "forearm.R": (0, 0, -20)}, 10: {"arm.R": (0, 0, -165), "forearm.R": (0, 0, 20)},
                           20: {"arm.R": (0, 0, -150), "forearm.R": (0, 0, -20)}})
    acts["celebrate"] = ({1: {"arm.L": (0, 0, 160), "arm.R": (0, 0, -160), "@root": (0, 0, 0.0)},
                                8: {"arm.L": (0, 0, 170), "arm.R": (0, 0, -170), "@root": (0, 0, 0.25), "thigh.L": (-30, 0, 0), "shin.L": (40, 0, 0)},
                                16: {"arm.L": (0, 0, 160), "arm.R": (0, 0, -160), "@root": (0, 0, 0.0)}})
    if kind == "skater":
        # the skating stride: crouched, one leg pushing out sideways, the other arm swinging
        stride = {}
        for f, s in ((1, 1), (11, -1), (21, 1)):
            k = dict(crouch)
            k["thigh.L" if s > 0 else "thigh.R"] = (-60, 0, 35 * s)
            k["shin.L" if s > 0 else "shin.R"] = (40, 0, 0)
            k["arm.R" if s > 0 else "arm.L"] = (-50, 0, -20 * s)
            k["arm.L" if s > 0 else "arm.R"] = (30, 0, 10 * s)
            k["hips"] = (0, 0, -8 * s)
            stride[f] = k
        acts["skate"] = (stride)
        glide = dict(crouch)
        glide["arm.L"] = (40, 0, 0)
        glide["arm.R"] = (40, 0, 0)
        acts["glide"] = ({1: glide, 20: glide})
        acts["ready"] = ({1: crouch, 20: crouch})
    else:
        tuck = {"spine": (75, 0, 0), "head": (-60, 0, 0), "thigh.L": (-70, 0, 0), "thigh.R": (-70, 0, 0),
                "shin.L": (100, 0, 0), "shin.R": (100, 0, 0), "arm.L": (8, 0, 8), "arm.R": (8, 0, -8), "@root": (0, 0, -0.35),
                "ski.L": (30, 0, 0), "ski.R": (30, 0, 0)}  # the ski bone's axis is flipped: +(thigh + shin) keeps the skis flat
        acts["tuck"] = ({1: tuck, 20: tuck})
        # the flight: body leaning far forward over V-shaped skis, arms back
        fly = {"hips": (70, 0, 0), "head": (-60, 0, 0), "arm.L": (20, 0, 12), "arm.R": (20, 0, -12),
               "ski.L": (62, 0, 18), "ski.R": (62, 0, -18), "thigh.L": (5, 0, 0), "thigh.R": (5, 0, 0)}  # skis along the body, in a V
        fly2 = dict(fly)
        fly2["hips"] = (73, 0, 2)
        acts["flight"] = ({1: fly, 30: fly2, 60: fly})
        tele = {"spine": (20, 0, 0), "thigh.L": (-40, 0, 0), "shin.L": (60, 0, 0), "thigh.R": (20, 0, 0), "shin.R": (50, 0, 0),
                "arm.L": (0, 0, 70), "arm.R": (0, 0, -70), "@root": (0, 0, -0.2), "ski.L": (20, 0, 0), "ski.R": (70, 0, 0)}
        acts["telemark"] = ({1: tele, 20: tele})
        acts["fall"] = ({1: {}, 10: {"hips": (-80, 0, 30), "@root": (0, 0, 0.3), "arm.L": (0, 0, 120), "arm.R": (0, 0, -60)},
                               20: {"hips": (-95, 0, 60), "@root": (0, 0, 0.2), "arm.L": (0, 0, 150), "arm.R": (0, 0, -100),
                                    "ski.L": (-65, 40, 0), "ski.R": (-95, 0, 0)}})
    rig_export(kind, out_dir, acts)


bpy.context.scene.render.fps = 30
build("skater")
build("jumper")
