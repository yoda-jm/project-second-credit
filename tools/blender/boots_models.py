"""Models for game 6 (Muddy Boots): the soldier (our squad and, recoloured, the enemy), the hostage, the hut, the
rescue tent, crates, the mine, jungle palms, bushes and boulders. Deterministic; output CC BY-SA 4.0; provenance:
this script. The soldier's material "uniform" is recoloured by the game (green for us, khaki for the enemy).
Run: blender -b --factory-startup -P tools/blender/boots_models.py -- godot/games/boots/art/models [palm bush ...]
One map tile = 1 unit. People are half the humanoid builder's size (about 0.9 units tall).
"""
import bpy, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanoid import *  # mat, sphere, box, limb, BONES, clear, rig_export

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)


def soldier():
    clear()
    uni = mat("uniform", (0.25, 0.4, 0.2), 0.8)
    skin = mat("skin", (0.9, 0.7, 0.55), 0.6)
    helmet = mat("helmet", (0.22, 0.32, 0.18), 0.5, coat=0.3)
    boot = mat("boots", (0.12, 0.1, 0.08), 0.6, coat=0.2)
    gun = mat("rifle", (0.1, 0.1, 0.11), 0.4, 0.6)
    stock = mat("stock", (0.45, 0.28, 0.15), 0.6)
    pack = mat("pack", (0.35, 0.33, 0.22), 0.8)
    belt = mat("belt", (0.2, 0.18, 0.12), 0.7)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("iris", (0.2, 0.15, 0.1), 0.2)
    athletic_body(uni, skin, white, iris, glove=skin, boot=boot)
    sphere(0.125, (0, 0.005, 1.7), "head", helmet, (1.02, 1.08, 0.72))  # the helmet, with its brim
    body_loft([(1.62, 0.13, 0.135, 0.005), (1.64, 0.125, 0.13, 0.005)], "head", helmet, 20, 0)
    box((0.012, 0.012, 0.09), (0.09, -0.05, 1.6), "head", belt)  # chin strap
    box((0.012, 0.012, 0.09), (-0.09, -0.05, 1.6), "head", belt)
    body_loft([(1.05, 0.165, 0.11), (1.09, 0.165, 0.11)], "hips", belt, 20, 0)  # the belt, with pouches
    for x in (-0.1, 0.0, 0.1):
        box((0.05, 0.03, 0.05), (x, -0.115, 1.06), "hips", pack)
    box((0.26, 0.14, 0.3), (0, 0.16, 1.3), "spine", pack)
    body_loft([(1.43, 0.12, 0.05, 0.2), (1.46, 0.12, 0.05, 0.2)], "spine", mat("bedroll", (0.3, 0.25, 0.18), 0.9), 12, 1)
    # the rifle in the right hand, pointing forward
    box((0.045, 0.7, 0.055), (-0.27, -0.3, 0.86), "forearm.R", gun)
    box((0.055, 0.22, 0.09), (-0.27, 0.08, 0.84), "forearm.R", stock)
    box((0.03, 0.08, 0.12), (-0.27, -0.22, 0.79), "forearm.R", gun)
    box((0.025, 0.25, 0.03), (-0.27, -0.55, 0.88), "forearm.R", gun)
    run = {}
    for f, ph in ((1, 1), (6, 0), (11, -1), (16, 0), (21, 1)):
        run[f] = {"thigh.L": (40 * ph, 0, 0), "thigh.R": (-40 * ph, 0, 0), "shin.L": (-50 * max(0, -ph), 0, 0),
                  "shin.R": (-50 * max(0, ph), 0, 0), "arm.L": (-35 * ph, 0, 5), "arm.R": (-60, 0, -5),
                  "forearm.R": (-30, 0, 0), "spine": (12, 0, 0), "@root": (0, 0, 0.05 if ph == 0 else 0.0)}
    aim = {"arm.R": (-80, 0, 10), "forearm.R": (-15, 0, 0), "arm.L": (-75, 0, -25), "forearm.L": (-30, 0, 0), "spine": (5, 0, 0)}
    shoot = {1: aim, 3: dict(aim, **{"spine": (-3, 0, 0), "arm.R": (-88, 0, 10)}), 6: aim}
    throw = {1: {"arm.L": (60, 0, 20), "spine": (-10, 0, 0)}, 6: {"arm.L": (-150, 0, 0), "spine": (15, 0, 0)}, 12: {}}
    die = {1: {}, 8: {"hips": (-30, 0, 20), "@root": (0, 0, 0.15), "arm.L": (0, 0, 80), "arm.R": (0, 0, -60)},
           18: {"hips": (-88, 0, 30), "@root": (0, 0, 0.1), "arm.L": (0, 0, 120), "arm.R": (0, 0, -90), "thigh.L": (20, 0, 10)}}
    swim = {1: {"arm.L": (-150, 0, 20), "arm.R": (-40, 0, -20)}, 10: {"arm.L": (-40, 0, 20), "arm.R": (-150, 0, -20)},
            20: {"arm.L": (-150, 0, 20), "arm.R": (-40, 0, -20)}}
    idle = {1: {"arm.R": (-30, 0, 0)}, 30: {"arm.R": (-32, 0, 0), "head": (0, 0, 10), "spine": (2, 0, 0)}, 60: {"arm.R": (-30, 0, 0)}}
    rig_export("soldier", out_dir, {"idle": idle, "run": run, "shoot": shoot, "throw": throw, "die": die, "swim": swim}, 0.5)


def hostage():
    clear()
    shirt = mat("shirt", (0.92, 0.9, 0.85), 0.8)
    trousers = mat("trousers", (0.45, 0.35, 0.25), 0.8)
    skin = mat("skin", (0.8, 0.6, 0.45), 0.6)
    hair = mat("hair", (0.15, 0.1, 0.08), 0.8)
    white = mat("eye_white", (0.95, 0.95, 0.92), 0.3)
    iris = mat("iris", (0.2, 0.12, 0.08), 0.2)
    athletic_body(shirt, skin, white, iris, hair=hair, boot=mat("sandals", (0.4, 0.25, 0.1), 0.7), legs=trousers)
    walk = {}
    for f, ph in ((1, 1), (8, 0), (15, -1), (22, 0), (29, 1)):
        walk[f] = {"thigh.L": (25 * ph, 0, 0), "thigh.R": (-25 * ph, 0, 0), "arm.L": (-20 * ph, 0, 5), "arm.R": (20 * ph, 0, -5)}
    wave = {1: {"arm.L": (0, 0, 150), "arm.R": (0, 0, -150)}, 8: {"arm.L": (0, 0, 165), "arm.R": (0, 0, -165), "@root": (0, 0, 0.1)},
            16: {"arm.L": (0, 0, 150), "arm.R": (0, 0, -150)}}
    rig_export("hostage", out_dir, {"idle": {1: {"head": (0, 0, 10)}, 30: {"head": (0, 0, -10)}, 60: {"head": (0, 0, 10)}},
                                    "walk": walk, "wave": wave}, 0.5)


# ------------------------------------------------------------------ props

def active_obj():
    return bpy.context.active_object


def put(o, material, smooth=False, bevel=0.0):
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 2
        b.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=b.name)
    o.data.materials.clear()
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth() if smooth else bpy.ops.object.shade_flat()
    return o


def pbox(size, loc, material, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active_obj()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    return put(o, material, bevel=bevel)


def pcyl(r, depth, loc, material, rot=(0, 0, 0), r2=None, verts=12, smooth=True):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return put(active_obj(), material, smooth)


def psphere(r, loc, material, scale=(1, 1, 1), segs=14, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = active_obj()
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return put(o, material, True)


def export(parts, name):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    active_obj().name = name
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name)
    clear()


def hut():
    """A 2 x 2 tile jungle hut, centred on its footprint; the door faces +Z in the game (-Y here, the map's south)."""
    bamboo = mat("bamboo", (0.72, 0.58, 0.32), 0.7)
    dark = mat("hut_dark", (0.08, 0.06, 0.05), 0.9)
    straw = mat("thatch", (0.78, 0.66, 0.35), 0.95)
    parts = []
    for i in range(14):  # walls of upright canes
        a = i / 14.0
        parts.append(pcyl(0.06, 1.0, (-0.8 + a * 1.6, 0.8, 0.5), bamboo, verts=6))
        parts.append(pcyl(0.06, 1.0, (-0.8 + a * 1.6, -0.8, 0.5), bamboo, verts=6) if abs(-0.8 + a * 1.6) > 0.3 else None)
        parts.append(pcyl(0.06, 1.0, (0.8, -0.8 + a * 1.6, 0.5), bamboo, verts=6))
        parts.append(pcyl(0.06, 1.0, (-0.8, -0.8 + a * 1.6, 0.5), bamboo, verts=6))
    parts = [p for p in parts if p is not None]
    parts.append(pbox((0.55, 0.05, 0.8), (0, -0.78, 0.4), dark, bevel=0.0))  # the dark doorway
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.55, radius2=0.05, depth=1.1, location=(0, 0, 1.5), rotation=(0, 0, math.pi / 4))
    parts.append(put(active_obj(), straw))
    for i in range(3):  # straw fringes
        parts.append(pcyl(1.5 - i * 0.02, 0.06, (0, 0, 1.0 + i * 0.04), straw, rot=(0, 0, math.pi / 4), verts=4, r2=1.45, smooth=False))
    export(parts, "hut")


def tent():
    canvas = mat("canvas", (0.4, 0.5, 0.3), 0.85)
    flag = mat("tent_flag", (0.95, 0.85, 0.2), 0.6)
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=0.9, depth=1.8, location=(0, 0, 0.45), rotation=(math.pi / 2, 0, math.pi / 2))
    o = active_obj()
    o.scale = (1.0, 0.75, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(put(o, canvas))
    parts.append(pcyl(0.02, 1.6, (0.9, 0, 0.8), mat("pole", (0.4, 0.3, 0.2), 0.7), verts=6))
    parts.append(pbox((0.4, 0.02, 0.26), (1.1, 0, 1.45), flag, bevel=0.0))
    export(parts, "tent")


def crates():
    wood = mat("crate_wood", (0.55, 0.42, 0.22), 0.8)
    band = mat("crate_band", (0.2, 0.25, 0.15), 0.6)
    g = [pbox((0.5, 0.35, 0.3), (0, 0, 0.15), wood, bevel=0.02), pbox((0.52, 0.37, 0.05), (0, 0, 0.2), band, bevel=0.0)]
    for i in range(3):
        g.append(psphere(0.05, (-0.12 + i * 0.12, 0, 0.33), mat("grenade", (0.25, 0.3, 0.2), 0.5), (1, 1, 1.3)))
    export(g, "grenade_crate")
    r = [pbox((0.8, 0.3, 0.25), (0, 0, 0.125), wood, bevel=0.02), pbox((0.82, 0.32, 0.05), (0.2, 0, 0.13), band, bevel=0.0)]
    r.append(pcyl(0.04, 0.6, (0, 0, 0.3), mat("rocket_body", (0.6, 0.6, 0.55), 0.4, 0.5), rot=(0, math.pi / 2, 0), verts=10))
    r.append(pcyl(0.04, 0.1, (0.35, 0, 0.3), mat("rocket_tip", (0.8, 0.2, 0.1), 0.4), rot=(0, math.pi / 2, 0), r2=0.0, verts=10))
    export(r, "rocket_crate")


def mine():
    metal = mat("mine_metal", (0.3, 0.32, 0.28), 0.5, 0.6)
    parts = [pcyl(0.18, 0.07, (0, 0, 0.035), metal, verts=16), pcyl(0.04, 0.05, (0, 0, 0.09), mat("mine_pin", (0.7, 0.2, 0.1), 0.4), verts=8)]
    export(parts, "mine")


class Builder:
    """One mesh built by hand: faces carry a material slot and a smooth flag, so a whole plant is one object."""

    def __init__(self):
        self.verts, self.faces, self.mats, self.smooth, self.slots = [], [], [], [], []

    def slot(self, material):
        if material not in self.slots:
            self.slots.append(material)
        return self.slots.index(material)

    def face(self, pts, material, smooth=True):
        i = len(self.verts)
        self.verts.extend(tuple(p) for p in pts)
        self.faces.append(tuple(range(i, i + len(pts))))
        self.mats.append(self.slot(material))
        self.smooth.append(smooth)

    def grid(self, rings, material, smooth=True, cap=False):
        """Faces between consecutive closed rings of points (a tube); materials may be one per band."""
        i0 = len(self.verts)
        n = len(rings[0])
        for r in rings:
            self.verts.extend(tuple(p) for p in r)
        for k in range(len(rings) - 1):
            m = material[k] if isinstance(material, list) else material
            for j in range(n):
                a, b = i0 + k * n + j, i0 + k * n + (j + 1) % n
                self.faces.append((a, b, b + n, a + n))
                self.mats.append(self.slot(m))
                self.smooth.append(smooth)
        if cap:
            top = i0 + (len(rings) - 1) * n
            self.faces.append(tuple(range(top, top + n)))
            self.mats.append(self.slot(material[-1] if isinstance(material, list) else material))
            self.smooth.append(smooth)

    def add_object(self, o):
        """Merges an existing primitive object (its material slots and smoothing) and deletes it."""
        me = o.data
        mw = o.matrix_world
        i0 = len(self.verts)
        self.verts.extend(tuple(mw @ v.co) for v in me.vertices)
        for f in me.polygons:
            self.faces.append(tuple(i0 + v for v in f.vertices))
            self.mats.append(self.slot(me.materials[f.material_index]))
            self.smooth.append(f.use_smooth)
        bpy.data.objects.remove(o)

    def build(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        for m in self.slots:
            me.materials.append(m)
        for f, mi, sm in zip(me.polygons, self.mats, self.smooth):
            f.material_index = mi
            f.use_smooth = sm
        me.update()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        return o


def ring(c, t, r, n, phase=0.0, wobble=None):
    """n points around centre c, in the plane normal to direction t."""
    t = t.normalized()
    u = t.cross(Vector((0, 1, 0)))
    if u.length < 1e-4:
        u = Vector((1, 0, 0))
    u.normalize()
    v = t.cross(u)
    pts = []
    for j in range(n):
        a = phase + j * math.tau / n
        rr = r * (wobble[j] if wobble else 1.0)
        pts.append(c + (u * math.cos(a) + v * math.sin(a)) * rr)
    return pts


def bezier(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t


def palm():
    rnd = random.Random(11)
    trunk = mat("palm_trunk", (0.27, 0.19, 0.12), 0.85)
    band = mat("palm_ring", (0.13, 0.09, 0.06), 0.9)
    crown = mat("palm_crown", (0.24, 0.26, 0.1), 0.8)
    nut = mat("coconut", (0.2, 0.16, 0.07), 0.6)
    rib = mat("palm_rib", (0.16, 0.2, 0.06), 0.7)
    shades = [mat("palm_leaf_dark", (0.045, 0.13, 0.04), 0.6), mat("palm_leaf", (0.07, 0.19, 0.05), 0.55),
              mat("palm_leaf_light", (0.13, 0.27, 0.07), 0.5), mat("palm_leaf_sun", (0.24, 0.34, 0.09), 0.5)]
    dry = mat("palm_leaf_dry", (0.42, 0.3, 0.1), 0.75)
    bld = Builder()
    # a leaning trunk that curves back up, in ring segments (a lip at each old leaf scar)
    p0, p1, top = Vector((0, 0, 0)), Vector((0.05, 0, 1.3)), Vector((0.42, 0, 2.55))
    segs, sides = 11, 9
    rings, bands = [], []
    for k in range(segs):
        for f, rs, m in ((0.0, 1.08, band), (0.12, 0.95, trunk), (0.92, 1.0, band)):
            t = (k + f) / segs
            c = bezier(p0, p1, top, t)
            d = bezier(p0, p1, top, min(t + 0.01, 1)) - bezier(p0, p1, top, max(t - 0.01, 0))
            r = 0.085 - 0.03 * t + 0.09 * max(0.0, 0.18 - t) ** 1.3 * 4  # flared foot
            rings.append(ring(c, d, r * rs, sides, phase=k * 0.35))
            bands.append(m)
    rings.append(ring(top, top - bezier(p0, p1, top, 0.98), 0.07, sides, phase=segs * 0.35))
    bld.grid(rings, bands[:len(rings) - 1], smooth=True)
    # crownshaft bulb
    tdir = (top - bezier(p0, p1, top, 0.97)).normalized()
    cr = [ring(top + tdir * h, tdir, r, sides) for h, r in ((0.0, 0.075), (0.08, 0.1), (0.18, 0.085), (0.26, 0.03))]
    bld.grid(cr, crown, cap=True)
    head = top + tdir * 0.2
    # coconuts under the crown
    for k in range(5):
        a = k * math.tau / 5 + rnd.uniform(-0.3, 0.3)
        c = top + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, rnd.uniform(-0.05, 0.06)))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.07, location=c)
        o = active_obj()
        o.scale = (1, 1, 1.15)
        put(o, nut, True)
        bpy.ops.object.transform_apply(scale=True)
        bld.add_object(o)
    # fronds: a rib that arches up and droops, with folded leaflets on both sides
    fronds = []
    for k in range(6):   # upper, shorter, sunlit
        fronds.append((k * math.tau / 6 + 0.25, rnd.uniform(0.6, 0.8), rnd.uniform(1.15, 1.3), 1.6, rnd.choice((1, 2, 2))))
    for k in range(7):   # lower, longer, drooping, darker; one of them yellowing at the tip
        fronds.append((k * math.tau / 7 + rnd.uniform(-0.15, 0.15), rnd.uniform(0.2, 0.4), rnd.uniform(1.35, 1.5), 1.9,
                       -2 if k == 3 else rnd.choice((0, 1, 1))))
    fronds.append((1.2, -0.5, 1.0, 1.2, -1))  # an old dead frond hanging against the trunk
    for a, pitch0, length, bend, shade in fronds:
        curl = rnd.uniform(-0.35, 0.35)  # fronds sweep sideways a little, not straight spokes
        n = 15
        p = head + Vector((math.cos(a), math.sin(a), 0)) * 0.05
        pts, tans = [p.copy()], []
        for i in range(n):
            u = (i + 0.5) / n
            pitch = pitch0 - bend * u ** 1.4
            dirh = Vector((math.cos(a + curl * u * u), math.sin(a + curl * u * u), 0))
            t = dirh * math.cos(pitch) + Vector((0, 0, math.sin(pitch)))
            tans.append(t)
            p = p + t * (length / n)
            pts.append(p.copy())
        tans.append(tans[-1])
        # rib: a thin flat strip, widest at the base
        for i in range(n):
            side = Vector((-tans[i].y, tans[i].x, 0)).normalized()
            w0, w1 = 0.018 * (1 - i / n) + 0.004, 0.018 * (1 - (i + 1) / n) + 0.004
            bld.face([pts[i] - side * w0, pts[i] + side * w0, pts[i + 1] + side * w1, pts[i + 1] - side * w1],
                     rib if shade >= 0 else dry, smooth=False)
        for i in range(1, n):
            u = i / n
            ll = 0.5 * length * (u ** 0.45) * ((1 - u) ** 0.7)
            if shade == -1:
                m = dry
            elif shade == -2:
                m = dry if u > 0.55 else shades[0]
            else:
                m = shades[min(3, shade + (1 if u > 0.6 else 0))]
            t = tans[i]
            side = Vector((-t.y, t.x, 0)).normalized()
            for sgn in (-1, 1):
                d = side * sgn * 0.8 + t * 0.55
                d.z -= 0.35 + 0.35 * u
                d.normalize()
                ln = ll * rnd.uniform(0.85, 1.1)
                b = pts[i]
                tip = b + d * ln
                wv = t - d * t.dot(d)
                wv.normalize()
                w = ln * 0.13
                mid = b + d * (ln * 0.4)
                fold = Vector((0, 0, -w * 0.9))
                bld.face([b, mid + wv * w + fold, tip], m)
                bld.face([b, tip, mid - wv * w + fold], m)
    export([bld.build("palm")], "palm")


def leaf(bld, base, dirh, pitch0, bend, length, width, inner, outer):
    """A broad pointed leaf folded along its midrib; the base half dark, the tip half light."""
    side = Vector((-dirh.y, dirh.x, 0))
    n = 4
    prof = [0.35, 0.9, 1.0, 0.75, 0.0]
    p = base.copy()
    mids, lefts, rights = [p.copy()], [], []
    pts = [p.copy()]
    for i in range(n):
        u = (i + 0.5) / n
        pitch = pitch0 - bend * u
        p = p + (dirh * math.cos(pitch) + Vector((0, 0, math.sin(pitch)))) * (length / n)
        pts.append(p.copy())
    for i, c in enumerate(pts):
        w = width * prof[i] * 0.5
        drop = Vector((0, 0, -w * 0.55))
        lefts.append(c - side * w + drop)
        rights.append(c + side * w + drop)
    for i in range(n):
        m = inner if i < 2 else outer
        if i < n - 1:
            bld.face([pts[i], pts[i + 1], lefts[i + 1], lefts[i]], m)
            bld.face([pts[i], rights[i], rights[i + 1], pts[i + 1]], m)
        else:
            bld.face([pts[i], pts[i + 1], lefts[i]], m)
            bld.face([pts[i], rights[i], pts[i + 1]], m)


def bush():
    rnd = random.Random(3)
    core = mat("bush_core", (0.025, 0.07, 0.025), 0.9)
    dark = mat("bush_leaf_dark", (0.04, 0.12, 0.035), 0.7)
    mid = mat("bush_leaf", (0.07, 0.19, 0.05), 0.6)
    light = mat("bush_leaf_light", (0.15, 0.28, 0.07), 0.55)
    bld = Builder()
    clumps = [(Vector((-0.17, -0.12, 0)), 1.0), (Vector((0.2, -0.05, 0)), 0.85), (Vector((0.0, 0.22, 0)), 0.9)]
    for c, s in clumps:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22 * s, location=c + Vector((0, 0, 0.12 * s)))
        o = active_obj()
        o.scale = (1, 1, 0.8)
        put(o, core, True)
        bpy.ops.object.transform_apply(scale=True)
        bld.add_object(o)
        # three tiers: low leaves splay and droop, the top ones stand up
        for count, pitch, bend, ln, wd, h, inner, outer in ((8, 0.35, 1.1, 0.42, 0.2, 0.08, core, dark),
                                                           (7, 0.85, 1.2, 0.36, 0.19, 0.14, dark, mid),
                                                           (5, 1.25, 1.1, 0.28, 0.17, 0.2, mid, light)):
            ph = rnd.uniform(0, math.tau)
            for k in range(count):
                a = ph + k * math.tau / count + rnd.uniform(-0.2, 0.2)
                dirh = Vector((math.cos(a), math.sin(a), 0))
                leaf(bld, c + dirh * 0.03 + Vector((0, 0, h * s)), dirh, pitch + rnd.uniform(-0.15, 0.15), bend,
                     ln * s * rnd.uniform(0.9, 1.1), wd * s, inner, outer)
    export([bld.build("bush")], "bush")


def boulder():
    from mathutils import noise
    rock = mat("rock", (0.2, 0.185, 0.17), 0.9)
    moss = mat("rock_moss", (0.06, 0.11, 0.03), 0.95)
    bld = Builder()
    for loc, r, sc, sub, seed in (((0, 0, 0.26), 0.5, (1.0, 0.86, 0.74), 3, 8), ((0.44, -0.3, 0.07), 0.19, (1.0, 0.85, 0.75), 2, 9)):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(0, 0, 0))
        o = active_obj()
        off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
        for v in o.data.vertices:
            n = v.co.normalized()
            k = 1.0 + 0.3 * noise.noise(n * 1.4 + off) + 0.08 * noise.noise(n * 3.5 + off)
            v.co = Vector((n.x * sc[0], n.y * sc[1], n.z * sc[2])) * r * k + Vector(loc)
            v.co.z = max(v.co.z, -0.03)  # sits on the ground
        o.data.materials.append(rock)
        o.data.materials.append(moss)
        o.data.update()
        for f in o.data.polygons:
            f.material_index = 1 if f.normal.z + 0.35 * noise.noise(f.center * 6 + off) > 0.8 else 0
            f.use_smooth = False
        bld.add_object(o)
    export([bld.build("boulder")], "boulder")


only = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []  # optional: build only these models
for build in (soldier, hostage, hut, tent, crates, mine, palm, bush, boulder):
    if not only or build.__name__ in only:
        build()
