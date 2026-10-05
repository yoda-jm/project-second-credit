"""Ridgefire (game 30) backdrops: five deep landscapes that stand behind the artillery field, one per theme
(0 Mesa Dusk, 1 Alpine Front, 2 Moonfall, 3 Ember Isle, 4 Frozen Wastes). Original designs: every place is an
invented, generic one (red-rock mesas with a dry wash and a railway trestle, an alpine valley with a castle on a crag
and a waterfall, a lunar plain with a domed base, a volcanic island at night, an arctic shore with a research
station); none copies a real place or building. Deterministic (fixed seeds); output CC BY-SA 4.0; provenance: this
script only (written by Claude Code for the project), no third-party assets, no textures (vertex colours).
Run: .tools/bin/blender -b --factory-startup -P tools/blender/ridgefire_backdrops.py -- \
         godot/games/ridgefire/art/backdrops [n ...]

Coordinates: everything is authored in Godot space (x right, y up, z towards the camera) and converted on export.
The field is x 0..96 on the plane z = 0 (the game's terrain slab fills z -5..+3, heights 0..40); the camera sits
near (48, 26, 72), fov 38, looking at (48, 18, 0). Everything here lies behind the slab (z < -6) and no further
than z -1000 (the sky dome's radius is 1150, centred on the camera). Each backdrop_<n>.glb holds
  near_*    the ground just behind the field (z -6 .. -160): what shows over the slab where its terrain is low
  mid_*     the middle distance (landforms, water, props)
  lm_*      the landmarks (the trestle, the castle, the base, the volcano, the station)
  far_*     the far ranges
and named nodes the game animates, each with its origin at its pivot:
  0 train (slides along +x; its origin is the locomotive's nose), hawk_<i> (circles about local Y),
    rotor_<i> (turns about local Z)
  1 hawk_<i>, gondola (the cable car: slides from its origin along the cable to the empty cable_end)
  2 rover (drives along +x and back), lander (rises from its pad and settles again), radar (turns about Y)
  3 -
  4 rotor_<i> (turns about local Z), radar (turns about Y)
and empties: light_warm_<i> / light_cool_<i> / light_lava_<i> / light_red_<i> (an omni light there),
smoke_<i> (a plume of smoke rises there), ember_<i> (a fountain of embers), steam_<i> (steam where lava meets the
sea), snow_<i> (blowing snow round it), glow_<i> (a source of light the water mirrors: the crater, the lava's mouth).
Material names carry the game's hints: "*glow*" emissive (window_glow, lamp_glow, beacon_glow (blinks), dome_glow
(the lit glass of a dome), lava_glow (flowing lava: UV.x across, UV.y along the flow, in metres), crater_glow
(a lava lake), crack_glow (glowing cracks in the ash), headlight_glow), "water" (waves; vertex colour R marks the
shallows), "seaice" (the frozen sea), "waterfall" (UV.y down the fall in metres), "mist" (soft haze cards; vertex
colour alpha is their opacity), "*sway*" (bent by the wind by UV.y, the height above the plant's foot), "ice"
(glossy, a little translucent), "snow", "glass", "metal". All other colour is in the vertex colours (COLOR_0, linear),
over white materials; on the land the vertex colour's alpha is the sun's visibility, baked by marching towards the
sun over the landforms (long shadows), which the game's land shader applies to the sunlight alone.
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/ridgefire/art/backdrops")
ONLY = [int(a) for a in argv[1:]]

CAM = Vector((48.0, 26.0, 72.0))
CX = 48.0
TAN_W = 0.612  # half-width per unit of distance for fov 38 at 16:9


# ------------------------------------------------------------------ colour and noise

def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c[:3])


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def mul(a, k):
    return tuple(min(1.0, x * k) for x in a)


def desat(c, k):
    g = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    return mix(c, (g, g, g), k)


def smooth(a, b, x):
    if a == b:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def n2(x, z, s=1.0, seed=0.0):
    return noise.noise(Vector((x * s + seed * 17.3, z * s - seed * 9.1, seed * 3.7)))


def fbm(x, z, s=1.0, oct=4, seed=0.0):
    v, a, f = 0.0, 1.0, s
    for i in range(oct):
        v += a * n2(x, z, f, seed + i * 5.1)
        a *= 0.5
        f *= 2.03
    return v


def n3(p, s=1.0, seed=0.0):
    return noise.noise(Vector((p[0] * s + seed * 13.1, p[1] * s + seed * 3.3, p[2] * s - seed * 7.7)))



def half_w(z, margin=1.5):
    """Half the visible width at depth z (plus a margin for camera drift and wide screens)."""
    return TAN_W * (CAM.z - z) * margin + 20.0


def clamp01(v):
    return max(0.0, min(1.0, v))


def lerp(a, b, t):
    return a + (b - a) * t


def wa(c, a):
    """A colour with an alpha (the land's sun visibility)."""
    return (c[0], c[1], c[2], a)


# ------------------------------------------------------------------ materials

MATS = {}
MAT_DEFS = {
    # name: (base colour, roughness, metallic, emission strength, alpha)
    "ground": ((1, 1, 1), 0.95, 0, 0, 1),
    "rock": ((1, 1, 1), 0.85, 0, 0, 1),
    "snow": ((1, 1, 1), 0.7, 0, 0, 1),
    "ice": ((1, 1, 1), 0.25, 0, 0, 1),
    "paint": ((1, 1, 1), 0.6, 0, 0, 1),
    "roof": ((1, 1, 1), 0.5, 0, 0, 1),
    "wood": ((1, 1, 1), 0.8, 0, 0, 1),
    "metal": ((1, 1, 1), 0.35, 0.7, 0, 1),
    "glass": ((1, 1, 1), 0.1, 0.2, 0, 1),
    "water": ((1, 1, 1), 0.1, 0, 0, 1),
    "seaice": ((1, 1, 1), 0.3, 0, 0, 1),
    "waterfall": ((1, 1, 1), 0.3, 0, 0, 1),
    "mist": ((1, 1, 1), 1, 0, 0, 1),
    "foliage_sway": ((1, 1, 1), 0.85, 0, 0, 1),
    "flag_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "window_glow": ((1.0, 0.72, 0.4), 0.4, 0, 2.5, 1),
    "lamp_glow": ((1.0, 0.82, 0.55), 0.4, 0, 4.0, 1),
    "beacon_glow": ((1.0, 0.2, 0.15), 0.4, 0, 5.0, 1),
    "dome_glow": ((1.0, 0.8, 0.55), 0.3, 0, 1.5, 1),
    "headlight_glow": ((1.0, 0.95, 0.8), 0.4, 0, 6.0, 1),
    "lava_glow": ((1.0, 0.4, 0.1), 0.6, 0, 4.0, 1),
    "crater_glow": ((1.0, 0.45, 0.12), 0.6, 0, 5.0, 1),
    "crack_glow": ((1.0, 0.35, 0.08), 0.6, 0, 3.0, 1),
}
def mat(name):
    if name in MATS:
        return MATS[name]
    col, rough, metal, emit, alpha = MAT_DEFS[name]
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"] if m.node_tree else None
    if b is None:
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(col), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(col), 1)
        b.inputs["Emission Strength"].default_value = emit
    m.use_backface_culling = False
    MATS[name] = m
    return m


# ------------------------------------------------------------------ geometry accumulator

class Acc:
    """Collects faces (Godot coordinates, sRGB corner colours, optional UVs) and builds one Blender object."""

    def __init__(self, name, origin=(0, 0, 0)):
        self.name = name
        self.o = Vector(origin)
        self.v = []
        self.f = []
        self.sway_base = None  # plants set their foot height: sway materials get UV.y = height above it

    def vert(self, p):
        self.v.append(Vector(p))
        return len(self.v) - 1

    def face(self, ids, material, col, uvs=None, sm=False, out=None):
        ids = list(ids)
        cols = list(col) if isinstance(col, list) else [col] * len(ids)
        if uvs is None and "sway" in material:
            b = self.sway_base if self.sway_base is not None else 1e9
            uvs = [(0.0, max(0.0, self.v[i].y - b)) for i in ids]
        if out is not None:
            n = Vector((0, 0, 0))
            for i in range(len(ids)):
                a, b = self.v[ids[i]], self.v[ids[(i + 1) % len(ids)]]
                n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
            c = sum((self.v[i] for i in ids), Vector()) / len(ids)
            if n.dot(c - Vector(out)) < 0:
                ids.reverse()
                cols.reverse()
                if uvs:
                    uvs = list(reversed(uvs))
        self.f.append((ids, material, cols, uvs, sm))

    def poly(self, pts, material, col, uvs=None, sm=False, out=None):
        self.face([self.vert(p) for p in pts], material, col, uvs, sm, out)

    def tris(self):
        return sum(len(f[0]) - 2 for f in self.f)

    # -------- primitives

    def box(self, c, size, material, col, ry=0.0, taper=1.0, cols=None):
        """An axis box (turned by ry about Y); `taper` shrinks the top face; cols: (top, sides) colours."""
        cx, cy, cz = c
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        cr, sr = math.cos(ry), math.sin(ry)
        pts = []
        for yy in (-1, 1):
            k = taper if yy > 0 else 1.0
            for xx, zz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                x, z = xx * sx * k, zz * sz * k
                pts.append(self.vert((cx + x * cr + z * sr, cy + yy * sy, cz - x * sr + z * cr)))
        top, side = (cols if cols else (col, col))
        C = (cx, cy, cz)
        self.face([pts[4], pts[5], pts[6], pts[7]], material, top, out=C)
        self.face([pts[0], pts[1], pts[2], pts[3]], material, side, out=C)
        for i in range(4):
            j = (i + 1) % 4
            self.face([pts[i], pts[j], pts[4 + j], pts[4 + i]], material, side, out=C)

    def prism(self, outline, y0, y1, material, col, top=None, sm=False):
        """A vertical extrusion of a star-shaped outline [(x, z)] from y0 to y1 (col may be fn(y) -> colour)."""
        n = len(outline)
        cx = sum(p[0] for p in outline) / n
        cz = sum(p[1] for p in outline) / n
        C = (cx, (y0 + y1) / 2, cz)
        cf = col if callable(col) else (lambda y: col)
        lo = [self.vert((x, y0, z)) for x, z in outline]
        hi = [self.vert((x, y1, z)) for x, z in outline]
        for i in range(n):
            j = (i + 1) % n
            self.face([lo[i], lo[j], hi[j], hi[i]], material, [cf(y0), cf(y0), cf(y1), cf(y1)], sm=sm, out=C)
        t = self.vert((cx, y1, cz))
        for i in range(n):
            self.face([hi[i], hi[(i + 1) % n], t], material, top or cf(y1), out=(cx, y0, cz))

    def lathe(self, c, prof, segs, material, col, sm=True, rough=0.0, nscale=0.5, seed=0.0, sx=1.0, sz=1.0,
              cap=True, phase=0.0):
        """Revolves prof [(r, y)] (bottom to top) about a vertical axis at c. col: colour or fn(x, y, z) -> colour.
        rough: noise amplitude (fraction of r)."""
        cx, cy, cz = c
        cf = col if callable(col) else (lambda x, y, z: col)
        rings = []
        for r, y in prof:
            ring = []
            for j in range(segs):
                a = phase + 2 * math.pi * j / segs
                ux, uz = math.cos(a), math.sin(a)
                rr = r
                if rough:
                    rr *= 1.0 + rough * n3((ux * 3, y * 0.7, uz * 3), nscale * 3, seed)
                ring.append(self.vert((cx + ux * rr * sx, cy + y, cz + uz * rr * sz)))
            rings.append(ring)
        for i in range(len(rings) - 1):
            ym = cy + (prof[i][1] + prof[i + 1][1]) / 2
            for j in range(segs):
                k = (j + 1) % segs
                ids = [rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]]
                self.face(ids, material, [cf(*self.v[q]) for q in ids], sm=sm, out=(cx, ym, cz))
        if cap and prof[-1][0] > 1e-4:
            t = self.vert((cx, cy + prof[-1][1], cz))
            for j in range(segs):
                ids = [rings[-1][j], rings[-1][(j + 1) % segs], t]
                self.face(ids, material, [cf(*self.v[q]) for q in ids], sm=sm, out=(cx, cy - 1e3, cz))

    def blob(self, c, r, material, col, segs=9, rings=6, rough=0.25, nscale=0.6, seed=0.0, sm=True, cut=-1.0):
        """A noisy ellipsoid. r = (rx, ry, rz). cut: lowest normalised height (-1 full; 0 a dome).
        col: colour or fn(nx, ny, nz, p) -> colour, where n* is the unit direction."""
        cx, cy, cz = c
        rx, ry, rz = r
        cf = col if callable(col) else (lambda a, b, d, p: col)
        grid = []
        for i in range(rings + 1):
            t = i / rings
            lat = math.asin(cut) + (math.pi / 2 - math.asin(cut)) * t
            row = []
            for j in range(segs if i < rings else 1):
                lon = 2 * math.pi * j / segs + seed
                d = Vector((math.cos(lat) * math.cos(lon), math.sin(lat), math.cos(lat) * math.sin(lon)))
                k = 1.0 + rough * n3(d * 2.0, nscale, seed)
                p = (cx + d.x * rx * k, cy + d.y * ry * k, cz + d.z * rz * k)
                row.append((self.vert(p), d))
            grid.append(row)
        C = (cx, cy + ry * cut * 0.5, cz)

        def colr(e):
            q, d = e
            return cf(d.x, d.y, d.z, self.v[q])
        for i in range(rings):
            for j in range(segs):
                k = (j + 1) % segs
                if i + 1 == rings:
                    es = [grid[i][j], grid[i][k], grid[i + 1][0]]
                else:
                    es = [grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]]
                self.face([e[0] for e in es], material, [colr(e) for e in es], sm=sm, out=C)
        if cut > -1.0:
            b = self.vert((cx, cy + ry * cut, cz))
            for j in range(segs):
                es = [grid[0][j], grid[0][(j + 1) % segs]]
                self.face([es[0][0], es[1][0], b], material, [colr(es[0]), colr(es[1]), colr(es[0])], sm=sm,
                          out=(cx, cy + 1e3, cz))

    def tube(self, pts, radii, material, col, segs=6, sm=True, cap=False, rough=0.0, seed=0.0, nscale=0.3):
        """A tube along pts (Godot points) with per-point radii. col: colour or fn(i, point) -> colour, or
        fn(i, point, vertex) when it takes three arguments (per-vertex colour). rough: radial noise (fraction)."""
        cf0 = col if callable(col) else (lambda i, p: col)
        per_vertex = callable(col) and col.__code__.co_argcount == 3
        pts = [Vector(p) for p in pts]
        rings = []
        prev_n = None
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            if prev_n is None:
                ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
                nrm = t.cross(ref).normalized()
            else:
                nrm = (prev_n - t * prev_n.dot(t)).normalized()
            prev_n = nrm
            bn = t.cross(nrm)
            r = radii[i] if isinstance(radii, (list, tuple)) else radii
            ring = []
            for j in range(segs):
                a = 2 * math.pi * j / segs
                d = nrm * math.cos(a) + bn * math.sin(a)
                rr = r
                if rough:
                    rr *= 1.0 + rough * n3(p + d * r, nscale, seed)
                ring.append(self.vert(p + d * rr))
            rings.append(ring)

        def cf(i, p, q=None):
            return col(i, p, self.v[q]) if per_vertex else cf0(i, p)
        for i in range(len(pts) - 1):
            c = (pts[i] + pts[i + 1]) / 2
            for j in range(segs):
                k = (j + 1) % segs
                ids = [rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]]
                cs = [cf(i, pts[i], ids[0]), cf(i, pts[i], ids[1]), cf(i + 1, pts[i + 1], ids[2]),
                      cf(i + 1, pts[i + 1], ids[3])]
                self.face(ids, material, cs, sm=sm, out=c)
        if cap:
            for i, s in ((0, -1), (len(pts) - 1, 1)):
                t = self.vert(pts[i])
                far = pts[i] - (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized() * s * 100
                for j in range(segs):
                    self.face([rings[i][j], rings[i][(j + 1) % segs], t], material, cf0(i, pts[i]) if not per_vertex
                              else col(i, pts[i], pts[i]), out=far)

    def terrain(self, z_near, z_far, rows, cols, h, col, material="ground", sm=True, xl=None, xr=None, margin=1.5):
        """A height field whose rows widen with distance (so it always fills the view). h(x, z) -> y;
        col(x, y, z, ny) -> colour, ny the up component of the normal."""
        dn, df = CAM.z - z_near, CAM.z - z_far
        grid = []
        for i in range(rows + 1):
            t = i / rows
            d = dn * (df / dn) ** t
            z = CAM.z - d
            a = CX - half_w(z, margin) if xl is None else xl(z)
            b = CX + half_w(z, margin) if xr is None else xr(z)
            row = []
            for j in range(cols + 1):
                x = a + (b - a) * j / cols
                y = h(x, z)
                e = 0.02 * d + 0.05
                gx = (h(x + e, z) - h(x - e, z)) / (2 * e)
                gz = (h(x, z + e) - h(x, z - e)) / (2 * e)
                ny = 1.0 / math.sqrt(1 + gx * gx + gz * gz)
                row.append((self.vert((x, y, z)), col(x, y, z, ny)))
            grid.append(row)
        for i in range(rows):
            for j in range(cols):
                es = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
                c = sum((self.v[e[0]] for e in es), Vector()) / 4
                self.face([e[0] for e in es], material, [e[1] for e in es], sm=sm,
                          out=(c.x, c.y - 100, c.z))

    def ridge(self, xs, z, base, top_fn, col, material="rock", depth=0.0, sm=True):
        """A vertical silhouette sheet (for far ranges): top_fn(x) -> y, from y=base; tilted back by depth."""
        prev = None
        for x in xs:
            y = top_fn(x)
            a = self.vert((x, base, z))
            b = self.vert((x, y, z - depth * (y - base)))
            if prev:
                pa, pb, py = prev
                self.face([pa, a, b, pb], material, [col(x, base), col(x, base), col(x, y), col(x, py)], sm=sm,
                          out=(x, (base + y) / 2, z - 100))
            prev = (a, b, y)

    # -------- build

    def build(self):
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        o = self.o
        verts = [(p.x - o.x, -(p.z - o.z), p.y - o.y) for p in self.v]
        me.from_pydata(verts, [], [f[0] for f in self.f])
        names = []
        for f in self.f:
            if f[1] not in names:
                names.append(f[1])
        for n in names:
            me.materials.append(mat(n))
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        uv = me.uv_layers.new(name="UVMap") if any(f[3] for f in self.f) else None  # only where a shader reads it
        for poly, f in zip(me.polygons, self.f):
            poly.material_index = names.index(f[1])
            poly.use_smooth = f[4]
            for k in range(poly.loop_total):
                c = lin(f[2][k])
                ca.data[poly.loop_start + k].color = (*c, f[2][k][3] if len(f[2][k]) > 3 else 1.0)
                if f[3] and uv:
                    # the glTF exporter flips V (and Godot keeps glTF's top-left origin): pre-flip so the
                    # game's shaders read UV.y as written here
                    uv.data[poly.loop_start + k].uv = (f[3][k][0], 1.0 - f[3][k][1])
        me.color_attributes.active_color = ca
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (o.x, -o.z, o.y)
        return ob


class Scene:
    """The objects of one backdrop, built and exported together."""

    def __init__(self, n):
        self.n = n
        self.accs = []
        self.empties = []

    def acc(self, name, origin=(0, 0, 0), ry=0.0):
        a = Acc(name, origin)
        a.ry = ry
        self.accs.append(a)
        return a

    def empty(self, name, p):
        self.empties.append((name, p))

    def export(self):
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        objs = []
        total = 0
        for a in self.accs:
            ob = a.build()
            if ob is None:
                continue
            if a.ry:
                ob.rotation_euler = (0, 0, a.ry)
            total += a.tris()
            objs.append(ob)
        for name, p in self.empties:
            e = bpy.data.objects.new(name, None)
            bpy.context.scene.collection.objects.link(e)
            e.location = (p[0], -p[2], p[1])
            objs.append(e)
        bpy.ops.object.select_all(action="DESELECT")
        for ob in objs:
            ob.select_set(True)
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, "backdrop_%d.glb" % self.n)
        bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB", export_yup=True,
                                  export_apply=True, export_animations=False, export_vertex_color="ACTIVE",
                                  export_extras=False)
        print("exported backdrop_%d  %6d tris  %d nodes" % (self.n, total, len(objs)))
        for a in sorted(self.accs, key=lambda a: -a.tris())[:6]:
            print("    %-20s %6d" % (a.name, a.tris()))
        for m in list(bpy.data.meshes):
            bpy.data.meshes.remove(m)
        for m in list(bpy.data.materials):
            bpy.data.materials.remove(m)
        MATS.clear()
        return total




# ------------------------------------------------------------------ screen helpers

UV4 = [(0, 0), (1, 0), (1, 1), (0, 1)]


def sx(xs, z):
    """The world x that shows at field x `xs` for depth z (the field plane is z = 0)."""
    return CAM.x + (xs - CAM.x) * (CAM.z - z) / CAM.z


def sy(ys, z):
    """The world y that shows at field height `ys` for depth z (the horizon is at ys = 26, the camera's height)."""
    return CAM.y + (ys - CAM.y) * (CAM.z - z) / CAM.z


def xs_of(x, z):
    return CAM.x + (x - CAM.x) * CAM.z / (CAM.z - z)


def ys_of(y, z):
    return CAM.y + (y - CAM.y) * CAM.z / (CAM.z - z)


def dist(p):
    return (Vector(p) - CAM).length


def px_size(p, px=1.2):
    """A size that shows as about `px` pixels at 720p (so thin things never vanish)."""
    return 0.00066 * px * dist(p)


def catenary(A, B, sag, n):
    A, B = Vector(A), Vector(B)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = A.lerp(B, t)
        p.y -= sag * 4 * t * (1 - t)
        pts.append(p)
    return pts


def path_fn(pts):
    """A smooth function z -> x through [(z, x)] points (z decreasing), Catmull-Rom between them."""
    pts = sorted(pts, key=lambda p: -p[0])

    def f(z):
        if z >= pts[0][0]:
            return pts[0][1]
        if z <= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            z0, z1 = pts[i][0], pts[i + 1][0]
            if z0 >= z >= z1:
                t = (z0 - z) / (z0 - z1)
                p0 = pts[max(i - 1, 0)][1]
                p1, p2 = pts[i][1], pts[i + 1][1]
                p3 = pts[min(i + 2, len(pts) - 1)][1]
                t2, t3 = t * t, t * t * t
                return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
        return pts[-1][1]
    return f


# ------------------------------------------------------------------ landforms and baked sunlight

class Landform:
    """A radial landform (mesa, butte, crag, cone, berg) round (cx, cz) on base height y0. The rim is a superellipse
    (rx, rz, power p, turned by rot), roughened by edge noise. inner: [(q, h, flute)] from the centre (q 0) to the rim
    (q 1), as a share of the rim's distance; outer: [(m, h, flute)] beyond the rim, in metres outwards. h is the height
    above y0; flute roughens a ring's radius by height (cliffs)."""

    def __init__(self, c, rx, rz, inner, outer, y0=0.0, rot=0.0, p=2.0, edge=0.12, seed=0.0, flute=0.0, fscale=1.0,
                 top_noise=0.0):
        self.cx, self.cz = c
        self.rx, self.rz, self.rot, self.p = rx, rz, rot, p
        self.inner, self.outer = inner, outer
        self.y0, self.edge, self.seed, self.flute, self.fscale = y0, edge, seed, flute, fscale
        self.top_noise = top_noise
        self.R = max(rx, rz) * (1 + 1.6 * edge) + (outer[-1][0] if outer else 0) + 2
        self.top = y0 + max([h for _, h, _ in inner] + [h for _, h, _ in outer]) + top_noise + 2

    def rim(self, phi):
        a = phi - self.rot
        ca, sa = abs(math.cos(a)), abs(math.sin(a))
        r = 1.0 / max(1e-30, ((ca / self.rx) ** self.p + (sa / self.rz) ** self.p)) ** (1.0 / self.p)
        d = (math.cos(phi), math.sin(phi), 0.0)
        k = 1.0 + self.edge * n3((d[0] * 1.5, d[1] * 1.5, 0.3), 1.0, self.seed) \
            + self.edge * 0.45 * n3((d[0] * 4.0, d[1] * 4.0, 0.7), 1.0, self.seed + 3.0)
        return r * k

    def prof(self, d, R):
        """Height above y0 at distance d from the centre, where the rim lies at R."""
        if d <= R:
            q = d / R
            pts = self.inner
            for i in range(len(pts) - 1):
                if pts[i][0] <= q <= pts[i + 1][0]:
                    t = (q - pts[i][0]) / max(1e-6, pts[i + 1][0] - pts[i][0])
                    return lerp(pts[i][1], pts[i + 1][1], t)
            return pts[-1][1]
        m = d - R
        prev = (0.0, self.inner[-1][1])
        for o in self.outer:
            if m <= o[0]:
                t = (m - prev[0]) / max(1e-6, o[0] - prev[0])
                return lerp(prev[1], o[1], t)
            prev = (o[0], o[1])
        return None

    def h(self, x, z):
        dx, dz = x - self.cx, z - self.cz
        if dx * dx + dz * dz > self.R * self.R:
            return None
        d = math.hypot(dx, dz)
        phi = math.atan2(dz, dx)
        R = self.rim(phi)
        v = self.prof(d, R)
        if v is None:
            return None
        if self.top_noise and d < R:
            v += self.top_noise * fbm(x, z, 0.03, 2, self.seed)
        return self.y0 + v

    def build(self, a, material, col, segs=48, ground=None, vis=None):
        """col(x, y, z, ny, hrel, out) -> colour (hrel: height share of the top; out: metres beyond the rim, < 0
        inside); vis(x, y, z) -> sun visibility (baked into the alpha)."""
        H = max([h for _, h, _ in self.inner] + [h for _, h, _ in self.outer]) or 1.0
        rings = [(q, h, f, False) for q, h, f in self.inner] + [(m, h, f, True) for m, h, f in self.outer]
        grid = []
        centre = None
        for ri, (k, hh, fl, out) in enumerate(rings):
            if not out and k == 0.0:
                centre = (self.cx, self.y0 + hh, self.cz)
                continue
            row = []
            for j in range(segs):
                phi = 2 * math.pi * j / segs + self.seed * 0.1
                R = self.rim(phi)
                d = R * k if not out else R + k
                y = self.y0 + hh
                if not out and self.top_noise:
                    y += self.top_noise * fbm(self.cx + math.cos(phi) * d, self.cz + math.sin(phi) * d, 0.03, 2,
                                              self.seed)
                if fl and self.flute:
                    d *= 1.0 + self.flute * fl * n3((math.cos(phi) * 7 * self.fscale, math.sin(phi) * 7 * self.fscale,
                                                     y * 0.045), 1.0, self.seed + 9)
                x, z = self.cx + math.cos(phi) * d, self.cz + math.sin(phi) * d
                if ri == len(rings) - 1 and ground is not None:
                    y = ground(x, z) - 0.8
                row.append([x, y, z, d - R])
            grid.append(row)
        # normals from the grid
        verts = []
        nr = len(grid)
        for i in range(nr):
            vr = []
            for j in range(segs):
                p = Vector(grid[i][j][:3])
                pa = Vector(grid[min(i + 1, nr - 1)][j][:3]) - Vector(grid[max(i - 1, 0)][j][:3])
                if i == 0 and centre is not None:
                    pa = Vector(grid[1][j][:3]) - Vector(centre)
                pb = Vector(grid[i][(j + 1) % segs][:3]) - Vector(grid[i][(j - 1) % segs][:3])
                n = pb.cross(pa)
                if n.length < 1e-9:
                    n = Vector((0, 1, 0))
                n.normalize()
                if n.y < 0 and abs(n.y) > 0.99:
                    n = -n
                ny = n.y
                hrel = (p.y - self.y0) / H
                c = col(p.x, p.y, p.z, ny, hrel, grid[i][j][3])
                s = vis(p.x + n.x * 1.5, p.y + abs(n.y) * 1.5 + 0.5, p.z + n.z * 1.5) if vis else 1.0
                vr.append((a.vert(p), wa(c, s)))
            verts.append(vr)
        if centre is not None:
            cv = a.vert(centre)
            cc = col(centre[0], centre[1], centre[2], 1.0, 1.0, -1.0)
            cs = vis(centre[0], centre[1] + 1.0, centre[2]) if vis else 1.0
            for j in range(segs):
                k = (j + 1) % segs
                e = [verts[0][j], verts[0][k]]
                a.face([e[1][0], e[0][0], cv], material, [e[1][1], e[0][1], wa(cc, cs)], sm=True)
        for i in range(nr - 1):
            for j in range(segs):
                k = (j + 1) % segs
                es = [verts[i][j], verts[i][k], verts[i + 1][k], verts[i + 1][j]]
                a.face([e[0] for e in es], material, [e[1] for e in es], sm=True)


class Sun:
    """Bakes the sun's visibility: marches from a point towards the sun over the ground and the landforms, with a soft
    penumbra; cylinders (posts, spires) are tested exactly."""

    def __init__(self, d, ground, forms, soft=10.0, hmax=None, area=(-1700.0, 1800.0, -1060.0, 0.0), step=6.0):
        self.d = Vector(d).normalized()
        self.ground = ground
        self.forms = forms
        self.soft = soft
        self.hmax = hmax if hmax is not None else max([f.top for f in forms] + [60.0])
        self.cyl = []
        # the landforms bucketed by 64 m cells, then the heights cached on a grid (the march reads them bilinearly)
        self.buckets = {}
        for f in forms:
            for i in range(int(math.floor((f.cx - f.R) / 64)), int(math.floor((f.cx + f.R) / 64)) + 1):
                for k in range(int(math.floor((f.cz - f.R) / 64)), int(math.floor((f.cz + f.R) / 64)) + 1):
                    self.buckets.setdefault((i, k), []).append(f)
        self.x0, self.x1, self.z0, self.z1 = area
        self.step = step
        self.nx = int((self.x1 - self.x0) / step) + 2
        self.nz = int((self.z1 - self.z0) / step) + 2
        self.grid = [[self.exact(self.x0 + i * step, self.z0 + k * step) for i in range(self.nx)] for k in range(self.nz)]

    def exact(self, x, z):
        h = self.ground(x, z)
        for f in self.buckets.get((int(math.floor(x / 64)), int(math.floor(z / 64))), ()):
            v = f.h(x, z)
            if v is not None and v > h:
                h = v
        return h

    def height(self, x, z):
        u = (x - self.x0) / self.step
        v = (z - self.z0) / self.step
        i, k = int(math.floor(u)), int(math.floor(v))
        if i < 0 or k < 0 or i >= self.nx - 1 or k >= self.nz - 1:
            return self.exact(x, z)
        fu, fv = u - i, v - k
        r0, r1 = self.grid[k], self.grid[k + 1]
        return (r0[i] * (1 - fu) + r0[i + 1] * fu) * (1 - fv) + (r1[i] * (1 - fu) + r1[i + 1] * fu) * fv

    def vis(self, x, y, z):
        d = self.d
        res = 1.0
        t = 1.0
        for _ in range(90):
            px, py, pz = x + d.x * t, y + d.y * t, z + d.z * t
            if py > self.hmax:
                break
            hh = self.height(px, pz)
            g = py - hh
            if g < 0:
                return 0.0
            res = min(res, self.soft * g / t)
            t += min(max(g * 0.5, 1.5), 0.12 * t + 4.0)
            if t > 3000:
                break
        for (cx, cz, r, top) in self.cyl:
            # where the ray passes the post's axis, horizontally
            hx, hz = d.x, d.z
            hl = math.hypot(hx, hz)
            if hl < 1e-6:
                continue
            ux, uz = hx / hl, hz / hl
            s = (cx - x) * ux + (cz - z) * uz
            if s <= 0:
                continue
            off = abs((cx - x) * uz - (cz - z) * ux)
            if off > r * 1.6:
                continue
            yy = y + d.y * (s / hl)
            if yy < top:
                res = min(res, smooth(r * 0.5, r * 1.6, off))
        return clamp01(res)


# ------------------------------------------------------------------ shared props

def rock(a, c, r, rng, top, side, segs=7, rings=4, vis=None):
    def cc(nx, ny, nz, q):
        col = mix(side, top, smooth(0.1, 0.8, ny))
        return wa(col, 1.0 if vis is None else vis(q.x, q.y + 0.5, q.z))
    a.blob(c, r, "rock", cc, segs=segs, rings=rings, rough=0.3, nscale=0.9, seed=rng.random() * 50, sm=False, cut=-0.4)


def pine(a, c, h, rng, green, tiers=3, segs=6, snow=None):
    a.sway_base = c[1]
    x, y, z = c
    a.lathe((x, y, z), [(h * 0.05, 0), (h * 0.04, h * 0.25)], 4, "wood", hexc("#2a1e16"), sm=False, cap=False)
    for i in range(tiers):
        t0 = 0.12 + i * (0.7 / tiers)
        r = h * 0.26 * (1 - i / (tiers + 0.8))
        yb = h * t0
        yt = yb + h * (0.5 if i < tiers - 1 else 0.88 - t0)

        def cc(px, py, pz, yb=yb, yt=yt):
            k = (py - y - yb) / (yt - yb)
            col = mul(green, 0.7 + 0.5 * k)
            if snow is not None and k > 0.05:
                col = mix(col, snow, 0.55 * (1 - k) * smooth(0.0, 0.3, k))
            return col
        a.lathe((x, y, z), [(r, yb), (r * 0.6, yb + (yt - yb) * 0.35), (0.0, yt)], segs, "foliage_sway", cc,
                sm=False, cap=False, rough=0.15, seed=rng.random() * 30, phase=rng.random())
    a.sway_base = None


def flag(a, base, h, w, col, ry=0.0, pole=hexc("#2a2420")):
    """A pole with a cloth flag that flutters (flag_sway: UV.y = distance from the pole)."""
    x, y, z = base
    a.tube([(x, y, z), (x, y + h, z)], max(0.12, px_size(base, 1.0)), "wood", pole, segs=4)
    cr, sr = math.cos(ry), math.sin(ry)
    n = 4
    for i in range(n):
        u0, u1 = w * i / n, w * (i + 1) / n
        p = [(x + u0 * cr, y + h - 0.05, z - u0 * sr), (x + u1 * cr, y + h - 0.05, z - u1 * sr),
             (x + u1 * cr, y + h - 0.05 - w * 0.62, z - u1 * sr), (x + u0 * cr, y + h - 0.05 - w * 0.62, z - u0 * sr)]
        a.poly(p, "flag_sway", col, uvs=[(0, u0), (0, u1), (0, u1), (0, u0)])


# ------------------------------------------------------------------ 0 Mesa Dusk

SUN0 = (0.9, 0.23, 0.36)   # towards the low sun: from the right, a little behind the viewer (the game's light agrees)


def cliff_profile(H, cap=0.97, foot=0.52, batter=3.0, talus=55.0, n_cliff=11, n_talus=7, top=0.7):
    """inner and outer rings for a mesa or butte H high: a flat top, a cap-rock lip, a sheer cliff (many rings, so
    the strata show) battered out by `batter` metres down to `foot` of the height, then a concave talus `talus`
    metres wide (fluted into gullies)."""
    inner = [(0.0, H, 0.0), (top, H, 0.0), (0.94, H * 0.998, 0.1), (0.985, H * 0.99, 0.4), (1.0, H * cap, 1.0)]
    outer = []
    for i in range(1, n_cliff + 1):
        t = i / n_cliff
        outer.append((0.25 + batter * t ** 1.5, H * (cap + (foot - cap) * t), 1.0))
    for i in range(1, n_talus + 1):
        t = i / n_talus
        outer.append((0.25 + batter + (talus - batter) * t ** 1.25, H * foot * (1.0 - t) ** 1.7, 0.9 * (1.0 - t) + 0.1))
    return inner, outer


def spire_profile(H, r):
    """a slender pinnacle: a rounded cap, a fluted shaft that thickens a little down to a small talus."""
    inner = [(0.0, H, 0.0), (0.5, H * 0.985, 0.2), (1.0, H * 0.94, 1.0)]
    outer = [(r * 0.04 + 0.05 * H * t, H * (0.94 - 0.62 * t), 1.0) for t in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0)]
    outer += [(0.05 * H + r * 0.5 + r * 2.0 * t, H * 0.32 * (1 - t) ** 1.6, 0.6 * (1 - t)) for t in (0.25, 0.5, 0.75, 1.0)]
    return inner, outer


def saguaro(a, c, h, rng, green=hexc("#3c4e2e"), vis=None):
    """A columnar cactus with arms (ribbed by flat shading)."""
    x, y, z = c
    r = h * 0.05
    lit = mix(green, hexc("#8a8a4a"), 0.3)

    def cc(i, p, q):
        k = smooth(-0.3, 0.6, (q - p).normalized().dot(Vector(SUN0))) if (q - p).length > 1e-6 else 0.5
        return wa(mix(mul(green, 0.75), lit, k), 1.0)
    a.tube([(x, y - 0.3, z), (x, y + h * 0.5, z), (x, y + h * 0.92, z)], [r * 1.05, r, r * 0.95], "rock", cc, segs=8,
           sm=False)
    a.lathe((x, y + h * 0.92, z), [(r * 0.95, 0), (r * 0.7, r * 0.6), (0.0, r * 0.95)], 8, "rock", lit, sm=True)
    n = rng.choice((1, 2, 2, 3))
    for k in range(n):
        an = rng.uniform(0, 2 * math.pi) if k == 0 else an + rng.uniform(2.0, 4.2)
        y0 = y + h * rng.uniform(0.35, 0.6)
        out = h * rng.uniform(0.12, 0.18)
        top = y0 + h * rng.uniform(0.18, 0.32)
        dx, dz = math.cos(an), math.sin(an)
        ra = r * 0.75
        pts = [(x + dx * r * 0.5, y0, z + dz * r * 0.5), (x + dx * out * 0.75, y0 + out * 0.05, z + dz * out * 0.75),
               (x + dx * out, y0 + out * 0.45, z + dz * out), (x + dx * out, top, z + dz * out)]
        a.tube(pts, [ra, ra, ra, ra * 0.95], "rock", cc, segs=6, sm=False)
        a.lathe((pts[-1][0], top, pts[-1][2]), [(ra * 0.95, 0), (0.0, ra * 0.9)], 6, "rock", lit)


def shrub(a, c, r, rng, col):
    def cc(nx, ny, nz, q):
        return wa(mix(mul(col, 0.6), mul(col, 1.15), smooth(-0.5, 0.8, ny)), 1.0)
    a.blob(c, (r, r * 0.6, r), "foliage_sway", cc, segs=6, rings=3, rough=0.35, nscale=1.4, seed=rng.random() * 40,
           cut=-0.2)


def prickly(a, c, s, rng):
    x, y, z = c
    g = hexc("#5e7040")
    for i in range(rng.randint(3, 6)):
        an = rng.uniform(0, 6.28)
        p = (x + math.cos(an) * s * 0.5, y + s * rng.uniform(0.3, 0.9), z + math.sin(an) * s * 0.3)
        a.blob(p, (s * 0.38, s * 0.45, s * 0.1), "rock", lambda nx, ny, nz, q: wa(mix(mul(g, 0.7), g, ny * 0.5 + 0.5), 1),
               segs=6, rings=3, rough=0.05, seed=rng.random())


def windpump(sc, c, h):
    """A farm wind pump: a lattice tower, the wheel of blades (rotor_0) and its tail vane."""
    x, y, z = c
    a = sc.acc("near_windpump")
    steel = hexc("#3a3430")
    w = h * 0.16
    legs = [(x - w, z - w), (x + w, z - w), (x + w, z + w), (x - w, z + w)]
    for lx, lz in legs:
        a.tube([(lx, y, lz), (x + (lx - x) * 0.12, y + h, z + (lz - z) * 0.12)], 0.09, "metal", steel, segs=3,
               sm=False)
    for k in range(4):
        t0, t1 = k / 4, (k + 1) / 4
        for i in range(4):
            j = (i + 1) % 4
            p0 = Vector((lerp(legs[i][0], x, t0 * 0.88), y + h * t0, lerp(legs[i][1], z, t0 * 0.88)))
            p1 = Vector((lerp(legs[j][0], x, t1 * 0.88), y + h * t1, lerp(legs[j][1], z, t1 * 0.88)))
            a.tube([p0, p1], 0.05, "metal", steel, segs=3, sm=False)
    a.box((x, y + h + 0.3, z), (0.5, 0.6, 0.9), "metal", steel)
    a.box((x + 0.1, y + h + 0.45, z - 2.1), (0.08, 1.2, 2.6), "metal", hexc("#6a5a48"))   # the tail vane
    a.box((x, y + 0.5, z + 1.4), (1.6, 1.0, 1.6), "wood", hexc("#5a4a3a"))   # the tank
    hub = (x, y + h + 0.45, z + 0.55)
    r = sc.acc("rotor_0", hub)
    blade = hexc("#8a8076")
    for k in range(14):
        an = 2 * math.pi * k / 14
        ca, sa = math.cos(an), math.sin(an)
        ca2, sa2 = math.cos(an + 0.16), math.sin(an + 0.16)
        r.poly([(hub[0] + ca * 0.4, hub[1] + sa * 0.4, hub[2]), (hub[0] + ca * 1.9, hub[1] + sa * 1.9, hub[2] + 0.12),
                (hub[0] + ca2 * 1.9, hub[1] + sa2 * 1.9, hub[2] - 0.12), (hub[0] + ca2 * 0.4, hub[1] + sa2 * 0.4, hub[2])],
               "metal", blade)
    r.lathe((hub[0], hub[1], hub[2] - 0.05), [(0.45, 0), (0.45, 0.1)], 8, "metal", steel)
    for rr in (1.0, 1.85):
        pts = [(hub[0] + math.cos(t * 2 * math.pi / 20) * rr, hub[1] + math.sin(t * 2 * math.pi / 20) * rr, hub[2])
               for t in range(21)]
        r.tube(pts, 0.04, "metal", steel, segs=3, sm=False)


def hawk(sc, i, pivot, r, y):
    """A hawk gliding round pivot (the node turns about Y)."""
    a = sc.acc("hawk_%d" % i, pivot)
    x, yy, z = pivot
    col = hexc("#2a201c")
    span = 2.6
    a.poly([(x + r, yy, z - 0.5), (x + r + 0.15, yy + 0.05, z + 0.4), (x + r + span / 2, yy + 0.35, z - 0.2)], "paint", col)
    a.poly([(x + r, yy, z - 0.5), (x + r - span / 2, yy + 0.35, z - 0.2), (x + r - 0.15, yy + 0.05, z + 0.4)], "paint", col)
    a.poly([(x + r - 0.12, yy, z + 0.3), (x + r + 0.12, yy, z + 0.3), (x + r, yy, z + 0.9)], "paint", col)


def hoodoo(a, c, h, r, rng, strata, cap, vis):
    """A hoodoo: a column of soft rock in bulges and necks, banded, under a darker cap stone."""
    x, y, z = c
    prof = [(r * 1.7, 0.0), (r * 1.3, h * 0.07), (r * 1.0, h * 0.16)]
    yy = h * 0.16
    k = 0
    while yy < h * 0.78:
        yy += h * rng.uniform(0.1, 0.17)
        prof.append(((0.68 if k % 2 == 0 else 0.98) * r * rng.uniform(0.9, 1.1), min(yy, h * 0.8)))
        k += 1
    prof += [(r * 0.75, h * 0.84), (r * 1.25, h * 0.87), (r * 1.3, h * 0.93), (r * 0.9, h * 0.985), (0.0, h)]

    def cc(px, py, pz):
        t = (py - y) / h
        if t > 0.85:
            col = cap
        else:
            b = (py - y) * 0.35 + 1.3 * n3((px * 0.2, py * 0.05, pz * 0.2), 1.0, 3)
            col = strata[int(b) % len(strata)]
        return wa(col, vis(px + (px - x) * 0.3, py + 0.5, pz + (pz - z) * 0.3))
    lean = (rng.uniform(-0.06, 0.06), rng.uniform(-0.04, 0.04))
    pts = [(x + lean[0] * py + 0.02 * h * math.sin(py / h * 5.0), y + py, z + lean[1] * py) for _, py in prof]
    a.tube(pts, [max(pr, 0.05) for pr, _ in prof], "rock", lambda i, p, q: cc(q.x, q.y, q.z), segs=10, sm=True,
           rough=0.14, seed=rng.random() * 40, nscale=0.5)


def shadow_ribbon(a, x, z, top, r, ground, gbase, sun):
    """The long shadow of a slender spire, laid on the ground as a strip of the ground's own colour with no sunlight
    in its middle (the vertex colour's alpha), widening and softening towards its tip."""
    s = Vector(sun)
    hl = math.hypot(s.x, s.z)
    dx, dz = -s.x / hl, -s.z / hl
    tan_el = s.y / hl
    px, pz = -dz, dx
    L = (top - ground(x, z)) / tan_el
    n = max(4, int(L / 3.0))
    rows = []
    for i in range(n + 1):
        t = i / n
        along = r * 0.3 + L * t
        cx, cz = x + dx * along, z + dz * along
        w = r * (1.5 + 1.3 * t)
        row = []
        for side in (-1.0, -0.45, 0.0, 0.45, 1.0):
            qx, qz = cx + px * w * side, cz + pz * w * side
            qy = ground(qx, qz) + 0.12 + 0.002 * (CAM.z - qz)
            dark = (1.0 - abs(side) ** 1.5) * (1.0 - 0.45 * t)
            row.append((a.vert((qx, qy, qz)), wa(gbase(qx, qy, qz, 1.0), 1.0 - dark)))
        rows.append(row)
    for i in range(n):
        for j in range(4):
            e = [rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]]
            a.face([q[0] for q in e], "ground", [q[1] for q in e], sm=True, out=(x, -1e4, z))


def mesa_dusk(sc):
    rng = random.Random(300)
    SAND, SAND2 = hexc("#c98652"), hexc("#b4643a")
    PALE, MUD = hexc("#dcb487"), hexc("#b98c66")
    SCRUB = hexc("#6c6a3e")
    river_x = path_fn([(10, 18.0), (-40, 34.0), (-90, 70.0), (-140, 58.0), (-190, 2.0), (-235, -48.0), (-270, -64.0),
                       (-330, -70.0), (-420, -90.0), (-560, -60.0), (-700, -120.0)])

    def river_k(x, z):
        w = 8.0 + 0.01 * (-z)
        return smooth(w * 2.0, w * 0.6, abs(x - river_x(z)))

    def ground(x, z):
        d = -z
        y = 1.2 + 1.8 * fbm(x, z, 0.012, 3, 1.0) + 0.5 * fbm(x, z, 0.06, 2, 2.0)
        y += smooth(250.0, 800.0, d) * (8.0 + 9.0 * fbm(x, z, 0.004, 3, 3.0))
        y -= 2.4 * river_k(x, z)
        return y

    forms = []
    # the railway plateau on the left (with the canyon the wash comes out of) and the block the tunnel enters
    A = Landform((-390.0, -300.0), 220.0, 55.0, *cliff_profile(50.0, talus=40.0), y0=1.5, p=4.0, edge=0.05, seed=1.0,
                 flute=0.05, fscale=5.0)
    B = Landform((-46.0, -290.0), 33.0, 36.0, *cliff_profile(62.0, talus=24.0, foot=0.42), y0=1.5, p=2.6, edge=0.1, seed=2.0,
                 flute=0.08, fscale=1.6)
    forms += [A, B]
    # the twin buttes on the right and a lone spire before them
    for (xs, z, r, H, sd) in ((64.0, -560.0, 26.0, 122.0, 3.0), (88.0, -600.0, 32.0, 140.0, 4.0)):
        x = sx(xs, z)
        forms.append(Landform((x, z), r, r * 0.8, *cliff_profile(H, cap=0.975, foot=0.6, batter=2.0, talus=80.0 * r / 26.0,
                              top=0.6), y0=ground(x, z), p=2.4, edge=0.12, seed=sd, flute=0.1, fscale=1.0))
    # small buttes out on the open plain, and hoodoos (built below): their shadows run long to the left
    for (xs, z, r, H, sd) in ((66.0, -300.0, 9.0, 30.0, 32.0), (104.0, -262.0, 12.0, 34.0, 35.0),
                              (40.0, -390.0, 14.0, 40.0, 36.0)):
        x = sx(xs, z)
        forms.append(Landform((x, z), r, r * 0.85, *cliff_profile(H, foot=0.55, batter=1.5, talus=r * 1.6, top=0.5),
                              y0=ground(x, z) - 0.5, edge=0.14, seed=sd, flute=0.1, fscale=0.7))
    hoodoos = [(sx(xs, z), z, r, H, sd) for (xs, z, r, H, sd) in
               ((75.0, -480.0, 6.5, 66.0, 5.0), (50.0, -232.0, 3.6, 25.0, 31.0), (28.0, -196.0, 2.8, 17.0, 33.0),
                (83.0, -214.0, 4.2, 29.0, 34.0), (58.0, -152.0, 2.3, 12.0, 37.0), (14.0, -262.0, 3.6, 23.0, 38.0),
                (93.0, -172.0, 3.0, 19.0, 39.0), (64.5, -246.0, 2.6, 15.0, 40.0))]
    # middle-distance mesas (to the sides; behind the middle they stay low)
    for (xs, z, rx, rz, H, sd, ry) in ((122.0, -380.0, 120.0, 50.0, 58.0, 7.0, -0.1), (40.0, -700.0, 120.0, 40.0, 44.0, 8.0, 0.0),
                                       (6.0, -760.0, 150.0, 55.0, 86.0, 9.0, 0.15), (116.0, -800.0, 160.0, 60.0, 80.0, 10.0, -0.1)):
        x = sx(xs, z)
        forms.append(Landform((x, z), rx, rz, *cliff_profile(H, talus=H * 0.9), y0=ground(x, z), p=3.0, edge=0.14,
                              seed=sd, rot=ry, flute=0.06, fscale=2.0))
    # the far range: a broken line of mesas along the horizon
    far = []
    x = -900.0
    k = 0
    while x < 1100:
        z = -900.0 - rng.uniform(0, 70)
        w = rng.uniform(60, 170)
        H = rng.uniform(40, 110)
        far.append(Landform((x + w, z), w, rng.uniform(35, 55), *cliff_profile(H, talus=H, n_cliff=5, n_talus=4),
                            y0=ground(x + w, z), p=3.0, edge=0.16, seed=20 + k, flute=0.05, fscale=2.0))
        x += 2 * w + rng.uniform(-30, 90)
        k += 1
    forms += far

    sun = Sun(SUN0, ground, forms, soft=8.0)
    for (x, z, r, H, sd) in hoodoos:   # slender spires: their shadows are tested exactly
        sun.cyl.append((x, z, r * 1.1, ground(x, z) + H))

    # foreground cacti and posts cast exact long shadows
    plants = []
    for i in range(34):
        z = rng.uniform(-40, -170)
        xs = rng.uniform(-30, 126)
        x = sx(xs, z)
        if river_k(x, z) > 0.2:
            continue
        h = rng.uniform(6.0, 13.0) * (1.0 + 0.004 * (-z))
        plants.append((x, z, h))
        sun.cyl.append((x, z, h * 0.12, ground(x, z) + h))

    STRATA = [hexc("#b8532c"), hexc("#c96a3a"), hexc("#a8462a"), hexc("#d48a58"), hexc("#bd5d32"), hexc("#e0a274"),
              hexc("#b04e2e")]
    CAP, TOP, TALUS = hexc("#7c3e2a"), hexc("#a27a50"), hexc("#b8653c")

    def mesa_col(x, y, z, ny, hrel, out):
        if out < -0.5 and ny > 0.6:
            c = mix(TOP, mul(TOP, 0.75), smooth(0.1, 0.5, n2(x, z, 0.08)))
            return mix(c, SCRUB, 0.35 * smooth(0.2, 0.45, n2(x, z, 0.3, 4)))
        band = y * 0.16 + 1.6 * n3((x * 0.01, y * 0.02, z * 0.01), 1.0, 2)
        c = STRATA[int(band) % len(STRATA)]
        c = mix(c, STRATA[(int(band) + 1) % len(STRATA)], smooth(0.75, 1.0, band % 1.0))
        if hrel > 0.9:
            c = mix(c, CAP, smooth(0.9, 0.95, hrel))
        # desert varnish streaks down the cliffs
        vs = n3((x * 0.15, y * 0.006, z * 0.15), 1.0, 7)
        c = mix(c, mul(c, 0.62), smooth(0.15, 0.5, vs) * smooth(0.95, 0.6, ny) * 0.8)
        if out > 3.0:   # the talus: scree going to sand
            c = mix(c, mix(TALUS, SAND, smooth(10.0, 45.0, out)), smooth(3.0, 12.0, out))
            c = mix(c, mul(c, 0.8), 0.5 * smooth(0.3, 0.6, n2(x, z, 0.4, 5)))
        return c

    def gbase(x, y, z, ny):
        c = mix(SAND, SAND2, smooth(-0.4, 0.5, fbm(x, z, 0.015, 3, 5)))
        c = mix(c, PALE, 0.4 * smooth(0.2, 0.6, fbm(x, z, 0.03, 2, 6)))
        rk = river_k(x, z)
        if rk > 0:
            cracks = smooth(0.0, 0.08, abs(n2(x, z, 0.35, 8)))
            bed = mix(mul(MUD, 0.75), PALE, cracks)
            c = mix(c, bed, rk)
            c = mix(c, mul(SAND2, 0.8), smooth(0.2, 0.5, rk) * smooth(0.95, 0.6, rk) * 0.5)   # the banks
        sc_ = smooth(0.25, 0.5, n2(x, z, 0.5, 4)) * (1 - rk)
        c = mix(c, SCRUB, sc_ * 0.45)
        c = mix(c, mul(c, 0.8), smooth(0.92, 0.75, ny))
        return c

    def gcol(x, y, z, ny):
        return wa(gbase(x, y, z, ny), sun.vis(x, y + 0.3, z))

    land = sc.acc("mid_desert")
    land.terrain(-6.0, -1000.0, 120, 150, ground, gcol, material="ground", margin=1.5)
    # a lip down in front so nothing shows below the near edge
    lip = sc.acc("near_lip")
    lip.terrain(-5.9, -6.0, 1, 150, lambda x, z: ground(x, z) - (30.0 if z > -5.95 else 0.0),
                lambda x, y, z, ny: wa(mul(SAND2, 0.7), 1.0), material="ground")

    def build_forms(lst, name, segs):
        a = sc.acc(name)
        for f in lst:
            f.build(a, "rock", mesa_col, segs=segs, ground=ground, vis=sun.vis)
    build_forms([A, B], "lm_plateaus", 72)
    build_forms(forms[2:4], "mid_buttes", 44)
    build_forms(forms[4:7], "mid_smallbuttes", 28)
    build_forms(forms[7:11], "mid_mesas", 56)
    ho = sc.acc("mid_hoodoos")
    sh = sc.acc("mid_shadows")
    for (x, z, r, H, sd) in hoodoos:
        y = ground(x, z)
        hoodoo(ho, (x, y - 1.0, z), H + 1.0, r, random.Random(int(sd * 100)), STRATA, CAP, sun.vis)
        shadow_ribbon(sh, x, z, y + H, r, ground, gbase, SUN0)
    build_forms(far, "far_mesas", 32)

    # the railway: rails along the plateau's rim, the trestle over the canyon, the tunnel into the block
    TZ, TY = -262.0, 51.6
    rail = sc.acc("lm_trestle")
    tim, dark = hexc("#4a3226"), hexc("#241a16")
    x0 = -300.0
    while (A.h(x0 + 1.0, TZ) or 0.0) > TY - 1.5 and x0 < 0.0:
        x0 += 1.0
    x1 = x0 + 10.0
    while (B.h(x1, TZ) or 0.0) < TY + 2.0 and x1 < 100.0:
        x1 += 1.0
    print("trestle", x0, x1)
    rail.box(((x0 - 460.0) / 2, TY, TZ), (x0 + 460.0, 0.5, 3.4), "wood", hexc("#3a2a22"))
    rail.box(((x0 + x1) / 2, TY, TZ), (x1 - x0 + 6, 0.9, 4.0), "wood", tim)
    for x in (x0 - 2, x1 + 2):
        rail.box((x, TY - 1.2, TZ), (6, 2.4, 6), "rock", hexc("#8a5a3a"))
    xb = x0 + 4
    while xb < x1 - 2:
        yb = ground(xb, TZ) - 1.0
        for ff in (A, B):
            v = ff.h(xb, TZ)
            if v is not None:
                yb = max(yb, v - 1.0)
        if yb < TY - 2:
            for s in (-1, 1):
                rail.tube([(xb, yb, TZ + s * 3.6), (xb, TY - 0.4, TZ + s * 1.6)], 0.32, "wood", dark, segs=4, sm=False)
            hh = TY - yb
            n = max(1, int(hh / 9.0))
            for k in range(n):
                ya, yb2 = yb + hh * k / n, yb + hh * (k + 1) / n
                wa_, wb = 3.6 - 2.0 * k / n, 3.6 - 2.0 * (k + 1) / n
                rail.tube([(xb, ya, TZ - wa_), (xb, yb2, TZ + wb)], 0.16, "wood", tim, segs=3, sm=False)
                rail.tube([(xb, yb2, TZ - wb), (xb, yb2, TZ + wb)], 0.16, "wood", tim, segs=3, sm=False)
        if xb + 8 < x1:
            rail.tube([(xb, TY - 3.5, TZ + 1.9), (xb + 8, TY - 3.5, TZ + 1.9)], 0.18, "wood", tim, segs=3, sm=False)
            # the bracing between this bent and the next, storey by storey
            yb_next = ground(xb + 8, TZ) - 1.0
            for ff in (A, B):
                v = ff.h(xb + 8, TZ)
                if v is not None:
                    yb_next = max(yb_next, v - 1.0)
            ylo = max(yb, yb_next)
            if ylo < TY - 4:
                n = max(1, int((TY - ylo) / 9.0))
                for k in range(n):
                    ya = ylo + (TY - 1.0 - ylo) * k / n
                    yc = ylo + (TY - 1.0 - ylo) * (k + 1) / n
                    for zz in (TZ + 2.4, TZ - 2.4):
                        rail.tube([(xb, ya, zz), (xb + 8, yc, zz)], 0.12, "wood", tim, segs=3, sm=False)
                        rail.tube([(xb + 8, ya, zz), (xb, yc, zz)], 0.12, "wood", tim, segs=3, sm=False)
                        rail.tube([(xb, yc, zz), (xb + 8, yc, zz)], 0.1, "wood", tim, segs=3, sm=False)
        xb += 8.0
    # the tunnel mouth in the block's west face
    tx = x1 + 1.0
    for dz in (-3.4, 3.4):
        rail.box((tx - 0.6, TY + 3.5, TZ + dz), (1.6, 7.0, 1.4), "rock", hexc("#7a4a32"))
    rail.box((tx - 0.6, TY + 7.6, TZ), (1.6, 1.4, 8.2), "rock", hexc("#7a4a32"))
    rail.box((tx - 0.2, TY + 3.4, TZ), (0.4, 6.8, 5.4), "paint", hexc("#0c0806"))

    # the train: a locomotive and lit coaches, sliding along x (origin at the nose)
    tr = sc.acc("train", (-330.0, TY + 0.4, TZ))
    nose = -330.0
    body, roof = hexc("#5a2a22"), hexc("#2a2224")
    tr.box((nose - 9.0, TY + 2.7, TZ), (18.0, 4.2, 3.2), "paint", hexc("#3a3a3e"))
    tr.box((nose - 3.0, TY + 5.3, TZ), (5.5, 1.2, 3.0), "paint", hexc("#2a2a2e"))
    tr.box((nose - 0.1, TY + 3.2, TZ), (0.3, 0.9, 1.6), "headlight_glow", (1, 1, 1))
    tr.box((nose - 2.0, TY + 4.0, TZ + 1.62), (2.0, 0.8, 0.05), "window_glow", (1, 1, 1))
    x = nose - 19.0
    for k in range(2):   # short enough to vanish whole into the tunnel's block
        L = 17.0
        tr.box((x - L / 2, TY + 2.6, TZ), (L - 0.6, 3.8, 3.0), "paint", body if k % 2 == 0 else hexc("#4a2420"))
        tr.box((x - L / 2, TY + 4.65, TZ), (L - 0.5, 0.4, 3.2), "roof", roof)
        for w in range(7):
            tr.box((x - 1.6 - w * 2.2, TY + 3.2, TZ + 1.52), (1.4, 0.9, 0.05), "window_glow", (1, 1, 1))
        x -= L
    sc.empty("headlight", (nose + 1.0, TY + 3.2, TZ))
    # where the nose stops: deep in the block, the whole train inside the tunnel (the block is ~60 m through)
    sc.empty("train_end", (x1 + 56.0, TY + 0.4, TZ))

    # the foreground: cacti, shrubs, rocks, a wind pump
    near = sc.acc("near_cacti")
    for (x, z, h) in plants:
        saguaro(near, (x, ground(x, z), z), h, rng)
    scrub = sc.acc("near_scrub")
    for i in range(160):
        z = rng.uniform(-30, -300)
        x = sx(rng.uniform(-40, 136), z)
        r = rng.uniform(0.8, 1.8) * (1.0 + 0.004 * (-z))
        y = ground(x, z)
        if rng.random() < 0.18:
            prickly(scrub, (x, y, z), r * 1.6, rng)
        else:
            shrub(scrub, (x, y + 0.1, z), r, rng, mix(mul(SCRUB, 0.75), hexc("#7a7650"), rng.random()))
    rocks = sc.acc("near_rocks")
    for i in range(28):
        z = rng.uniform(-20, -260)
        x = sx(rng.uniform(-40, 136), z)
        r = rng.uniform(1.0, 3.5) * (1.0 + 0.003 * (-z))
        rock(rocks, (x, ground(x, z) - 0.3, z), (r * 1.4, r * 0.8, r), rng, hexc("#9a5a3c"), hexc("#4a2a22"),
             vis=sun.vis)
    windpump(sc, (sx(10.0, -120.0), ground(sx(10.0, -120.0), -120.0) - 0.2, -120.0), 13.0)
    for i in range(2):
        hawk(sc, i, (sx(30.0 + i * 30, -110.0), sy(37.0 - i * 2, -110.0), -110.0 - i * 10), 14.0 + i * 5, 0)


# ------------------------------------------------------------------ 1 Alpine Front

SUN1 = (-0.5, 0.62, 0.6)   # a late-morning sun high on the left, behind the viewer


def ridged(x, z, s, oct=4, seed=0.0):
    v, a, f = 0.0, 0.5, s
    for i in range(oct):
        n = 1.0 - abs(n2(x, z, f, seed + i * 3.3))
        v += a * n * n
        a *= 0.5
        f *= 2.1
    return v


def mist_card(a, c, w, h, alpha=1.0, ry=0.0):
    """A soft vertical card of haze facing the camera (UV over the card; vertex alpha its opacity)."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)
    p = [(x - w / 2 * cr, y - h / 2, z + w / 2 * sr), (x + w / 2 * cr, y - h / 2, z - w / 2 * sr),
         (x + w / 2 * cr, y + h / 2, z - w / 2 * sr), (x - w / 2 * cr, y + h / 2, z + w / 2 * sr)]
    a.poly(p, "mist", (1, 1, 1, alpha), uvs=UV4)


def gable_house(a, c, w, d, h, ry, wall, roof, rng, upper=None, lit=0.0, win=hexc("#2a2420")):
    """A house with a pitched roof (ridge along x), deep eaves, small dark windows."""
    x, y, z = c
    a.box((x, y + h / 2, z), (w, h, d), "paint", wall, ry=ry)
    if upper:
        a.box((x, y + h * 0.78, z), (w + 0.05, h * 0.44, d + 0.05), "wood", upper, ry=ry)
    cr, sr = math.cos(ry), math.sin(ry)

    def P(u, v, yy):
        return (x + u * cr + v * sr, yy, z - u * sr + v * cr)
    rh = d * 0.45
    ow, od = w / 2 + 0.6, d / 2 + 0.7
    a.poly([P(-ow, -od, y + h - 0.2), P(ow, -od, y + h - 0.2), P(ow, 0, y + h + rh), P(-ow, 0, y + h + rh)], "roof", roof)
    a.poly([P(-ow, od, y + h - 0.2), P(-ow, 0, y + h + rh), P(ow, 0, y + h + rh), P(ow, od, y + h - 0.2)], "roof",
           mul(roof, 1.15))
    for s in (-1, 1):
        a.poly([P(s * w / 2, -d / 2, y + h), P(s * w / 2, d / 2, y + h), P(s * w / 2, 0, y + h + rh * 0.95)], "paint",
               upper or wall)
    n = max(1, int(w / 2.6))
    for i in range(n):
        u = (i + 0.5) / n * w - w / 2
        mat_ = "window_glow" if rng.random() < lit else "paint"
        a.box(P(u, d / 2 + 0.03, y + h * 0.45), (0.9, 1.1, 0.06), mat_, (1, 1, 1) if mat_ != "paint" else win, ry=ry)


def round_tower(a, c, r, h, wall, roof, cone=1.6, segs=10, crenel=False):
    x, y, z = c
    a.lathe((x, y, z), [(r * 1.08, 0), (r, h * 0.15), (r, h)], segs, "rock", wall, sm=True, cap=not cone)
    if crenel:
        for k in range(segs):
            an = 2 * math.pi * (k + 0.5) / segs
            a.box((x + math.cos(an) * r, y + h + 0.5, z + math.sin(an) * r), (r * 0.45, 1.0, 0.6), "rock", wall,
                  ry=-an)
    if cone:
        a.lathe((x, y + h, z), [(r * 1.18, 0), (r * 0.6, r * cone * 0.55), (0.0, r * cone * 1.25)], segs, "roof",
                roof, sm=False)
    for k in range(3):
        an = 1.6 + k * 0.7
        a.box((x + math.cos(an) * (r + 0.02), y + h * (0.45 + 0.17 * k), z + math.sin(an) * (r + 0.02)),
              (0.5, 1.4, 0.1), "paint", hexc("#1c1a1c"), ry=-an + math.pi / 2)


def castle(sc, top, rng):
    """A castle of pale stone on its crag: curtain walls, round corner towers with slate cones, a square keep, a tall
    slender tower, a hall, banners."""
    x, y, z = top
    a = sc.acc("lm_castle")
    fl = sc.acc("lm_castle_flags")
    wall, wall2 = hexc("#cbbfa8"), hexc("#b4a68e")
    slate, red = hexc("#3c4a66"), hexc("#a8302a")
    pts = [(-24, 10), (-8, 16), (14, 14), (24, 4), (20, -12), (2, -18), (-18, -12)]
    pts = [(x + px, z + pz) for px, pz in pts]
    for i in range(len(pts)):
        x0, z0 = pts[i]
        x1, z1 = pts[(i + 1) % len(pts)]
        L = math.hypot(x1 - x0, z1 - z0)
        ry = math.atan2(-(z1 - z0), x1 - x0)
        a.box(((x0 + x1) / 2, y + 4.0, (z0 + z1) / 2), (L, 9.0, 2.2), "rock", wall2, ry=ry)
        n = int(L / 1.6)
        for k in range(n):
            t = (k + 0.5) / n
            a.box((x0 + (x1 - x0) * t, y + 9.0, z0 + (z1 - z0) * t), (0.8, 1.1, 2.3), "rock", wall2, ry=ry)
        round_tower(a, (x0, y - 2.0, z0), 3.6 if i % 2 else 3.0, 17.0 + 3 * (i % 3), wall, slate, cone=1.8)
        flag(fl, (x0, y + 15.0 + 3 * (i % 3) + 3.0 * 1.8 * 1.25, z0), 3.0, 2.6, red if i % 2 else hexc("#e0c050"))
    # the gate tower facing the valley
    a.box((x - 2.0, y + 7.0, z + 16.5), (8.0, 16.0, 6.0), "rock", wall)
    a.box((x - 2.0, y + 3.0, z + 19.55), (3.2, 6.0, 0.2), "paint", hexc("#1c1612"))
    for k in range(5):
        a.box((x - 5.2 + k * 1.6, y + 15.6, z + 19.2), (0.8, 1.2, 0.6), "rock", wall)
    # the keep and the hall
    a.box((x + 6.0, y + 15.0, z - 4.0), (12.0, 30.0, 12.0), "rock", wall)
    a.lathe((x + 6.0, y + 30.0, z - 4.0), [(9.2, 0), (0.0, 9.0)], 4, "roof", slate, sm=False, phase=math.pi / 4)
    for k in range(4):
        a.box((x + 6.0 - 3 + k * 2.0, y + 22.0, z + 2.05), (0.6, 2.2, 0.1), "paint", hexc("#1c1a1c"))
    a.box((x - 10.0, y + 6.0, z - 2.0), (16.0, 12.0, 9.0), "rock", wall)
    gable_house(a, (x - 10.0, y + 12.0 - 0.1, z - 2.0), 16.0, 9.0, 0.1, 0.0, wall, slate, rng)
    # the slender tower: tall, a high cone, a gilded finial and the banner
    round_tower(a, (x - 1.0, y, z - 10.0), 3.2, 30.0, wall, slate, cone=3.0, segs=12)
    a.tube([(x - 1.0, y + 30.0 + 3.2 * 3.0 * 1.2, z - 10.0), (x - 1.0, y + 30.0 + 3.2 * 3.0 * 1.25 + 3.0, z - 10.0)],
           0.2, "metal", hexc("#c8a040"), segs=4)
    flag(fl, (x - 1.0, y + 30.0 + 3.2 * 3.0 * 1.25 + 2.5, z - 10.0), 4.5, 5.0, red)
    return a


def alpine_front(sc):
    rng = random.Random(400)
    GRASS, GRASS2, MEADOW = hexc("#5e8c36"), hexc("#4a7a2e"), hexc("#86a84a")
    FOREST, FOREST2 = hexc("#24402a"), hexc("#1c3424")
    ROCK, ROCK2 = hexc("#6a6a6c"), hexc("#48494e")
    SNOW = hexc("#dfe7f2")
    river_x = path_fn([(10, 66.0), (-30, 60.0), (-70, 82.0), (-110, 120.0), (-150, 150.0), (-190, 178.0), (-215, 196.0)])

    def river_k(x, z):
        if z < -222:
            return 0.0
        w = 7.0 + 0.02 * (-z)
        return smooth(w * 1.8, w * 0.8, abs(x - river_x(z)))

    def base(x, z):
        d = -z
        xs = xs_of(x, z)
        y = 2.0 + 2.0 * fbm(x, z, 0.01, 3, 1.0)
        side = smooth(30.0, 75.0, abs(xs - 50.0) + 8.0 * fbm(x, z, 0.01, 2, 7.0))
        y += side * (10.0 + 60.0 * smooth(60.0, 420.0, d)) * (0.7 + 0.6 * fbm(x, z, 0.005, 3, 2.0))
        # the forested ridges across the head of the valley
        y += smooth(380.0, 560.0, d) * (55.0 + 50.0 * fbm(x, z, 0.004, 3, 3.0) + 30.0 * ridged(x, z, 0.006, 3, 4.0))
        return y

    def ground(x, z):
        return base(x, z) - 1.6 * river_k(x, z)

    # the crag the castle stands on, the cliff the waterfall pours from
    CX_, CZ_ = sx(22.0, -250.0), -250.0
    crag = Landform((CX_, CZ_), 32.0, 27.0, [(0.0, 50.0, 0), (0.55, 49.0, 0.2), (0.9, 47.5, 0.6), (1.0, 46.0, 1.0)],
                    [(0.5 + 6.0 * t ** 1.3, 46.0 - 32.0 * t, 1.0) for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)] +
                    [(7.0 + 26 * t, 14.0 * (1 - t) ** 1.5, 0.7) for t in (0.25, 0.5, 0.75, 1.0)],
                    y0=ground(CX_, CZ_) - 1.0, p=2.2, edge=0.2, seed=11.0, flute=0.24, fscale=1.6, top_noise=1.5)
    WX, WZ = sx(86.0, -340.0), -340.0
    wcliff = Landform((WX, WZ), 70.0, 42.0, *cliff_profile(72.0, cap=0.98, foot=0.3, batter=5.0, talus=50.0, n_cliff=10),
                      y0=ground(WX, WZ) - 2.0, p=2.4, edge=0.1, seed=12.0, flute=0.14, fscale=2.4, top_noise=3.0)
    forms = [crag, wcliff]

    # the far peaks: cones and ridges, snow above the line
    peaks = [(-260.0, -820.0, 150.0, 260.0), (-40.0, -900.0, 172.0, 300.0), (150.0, -860.0, 140.0, 240.0),
             (330.0, -930.0, 180.0, 320.0), (520.0, -820.0, 135.0, 260.0), (-480.0, -900.0, 160.0, 300.0),
             (760.0, -920.0, 155.0, 300.0), (-720.0, -880.0, 140.0, 300.0)]

    def peak_h(x, z):
        h = 40.0 + 25.0 * fbm(x, z, 0.003, 2, 9.0)
        for (px, pz, H, r) in peaks:
            dd = math.hypot((x - px) / r, (z - pz) / (r * 0.75))
            if dd < 1.0:
                h = max(h, H * (1.0 - dd) ** 1.15)
        rg = ridged(x, z, 0.009, 4, 8.0)
        return h * (0.7 + 0.45 * rg) + 22.0 * rg * smooth(-640.0, -720.0, z)

    sun = Sun(SUN1, lambda x, z: max(ground(x, z), peak_h(x, z) if z < -620 else -1e9), forms, soft=6.0, hmax=300.0)

    def gcol(x, y, z, ny):
        d = -z
        c = mix(GRASS, GRASS2, smooth(-0.3, 0.5, fbm(x, z, 0.02, 3, 5)))
        c = mix(c, MEADOW, 0.5 * smooth(0.1, 0.5, fbm(x, z, 0.012, 2, 6)) * smooth(30.0, 5.0, y - 3.0))
        # forest on the slopes and the ridges, in patches with clearings
        fz = smooth(-0.15, 0.25, fbm(x, z, 0.008, 3, 7) + smooth(10.0, 40.0, y) * 0.5 - 0.3)
        c = mix(c, mix(FOREST, FOREST2, n2(x, z, 0.08, 8) * 0.5 + 0.5), fz * smooth(4.0, 14.0, y))
        # rock where it is steep
        c = mix(c, mix(ROCK, ROCK2, n2(x, z, 0.05, 9) * 0.5 + 0.5), smooth(0.78, 0.55, ny))
        rk = river_k(x, z)
        c = mix(c, hexc("#8a8270"), smooth(0.2, 0.6, rk))   # the gravel banks
        return wa(c, sun.vis(x, y + 0.5, z))

    def pcol(x, y, z, ny):
        snowline = 100.0 + 25.0 * fbm(x, z, 0.01, 3, 11)
        c = mix(ROCK, ROCK2, smooth(-0.3, 0.4, fbm(x, z, 0.02, 3, 12)))
        c = mix(c, mix(FOREST, FOREST2, 0.5), smooth(85.0, 60.0, y + 15.0 * fbm(x, z, 0.02, 2, 13)) * smooth(0.6, 0.85, ny))
        s = smooth(snowline - 10, snowline + 10, y) * smooth(0.6, 0.8, ny)
        s = max(s, smooth(snowline + 45, snowline + 75, y) * smooth(0.3, 0.55, ny) * 0.85)
        c = mix(c, SNOW, s)
        return wa(c, sun.vis(x, y + 1.0, z))

    land = sc.acc("mid_valley")
    land.terrain(-6.0, -660.0, 120, 150, ground, gcol, material="ground", margin=1.5)
    lip = sc.acc("near_lip")
    lip.terrain(-5.9, -6.0, 1, 150, lambda x, z: ground(x, z) - (30.0 if z > -5.95 else 0.0),
                lambda x, y, z, ny: wa(mul(GRASS2, 0.6), 1.0), material="ground")
    pk = sc.acc("far_peaks")
    pk.terrain(-600.0, -1000.0, 44, 230, peak_h, pcol, material="snow", margin=1.45)

    def crag_col(x, y, z, ny, hrel, out):
        c = mix(hexc("#6a6458"), hexc("#44403c"), smooth(-0.3, 0.4, n3((x * 0.08, y * 0.1, z * 0.08), 1.0, 3)))
        c = mix(c, mul(c, 0.7), smooth(0.2, 0.5, n3((x * 0.25, y * 0.02, z * 0.25), 1.0, 7)))   # streaks
        if ny > 0.55:
            c = mix(c, mix(GRASS2, FOREST, smooth(0.0, 0.4, n2(x, z, 0.1, 8))), smooth(0.55, 0.8, ny))
        return c
    a = sc.acc("lm_crag")
    crag.build(a, "rock", crag_col, segs=48, ground=ground, vis=sun.vis)

    def wcol(x, y, z, ny, hrel, out):
        c = mix(hexc("#5e5a52"), hexc("#3c3a38"), smooth(-0.3, 0.4, n3((x * 0.05, y * 0.12, z * 0.05), 1.0, 4)))
        c = mix(c, mul(c, 0.7), smooth(0.2, 0.5, n3((x * 0.2, y * 0.01, z * 0.2), 1.0, 5)))   # wet streaks
        c = mix(c, mix(FOREST, GRASS2, smooth(0.0, 0.3, n2(x, z, 0.05, 6))), smooth(0.5, 0.75, ny) * 0.9)
        if out > 8.0:
            c = mix(c, mix(GRASS2, FOREST, 0.5), 0.6 * smooth(8.0, 30.0, out))
        return c
    a = sc.acc("mid_cliff")
    wcliff.build(a, "rock", wcol, segs=64, ground=ground, vis=sun.vis)

    # the castle on the crag
    top_y = crag.h(CX_, CZ_)
    castle(sc, (CX_, top_y - 0.5, CZ_), rng)
    for i in range(2):
        hawk(sc, i, (CX_ + 30 + i * 40, top_y + 40 + i * 12, CZ_ + 20), 22.0 + i * 8, 0)

    # the waterfall: over the lip, a free fall, a cascade down the scree, a pool and the river
    fx = WX - 18.0
    zt = WZ
    while (wcliff.h(fx, zt) or 0.0) > wcliff.top - 8.0:
        zt += 0.5
    lip_y = wcliff.h(fx, zt - 1.0)
    zf = zt
    while (wcliff.h(fx, zf + 0.5) or -1e9) > lip_y - 58.0 and zf < WZ + 120:
        zf += 0.5
    foot_y = max(wcliff.h(fx, zf) or 0.0, ground(fx, zf))
    wf = sc.acc("mid_waterfall")
    W = 13.0
    rows = 14
    for i in range(rows):
        t0, t1 = i / rows, (i + 1) / rows
        y0, y1 = lip_y - (lip_y - foot_y) * t0, lip_y - (lip_y - foot_y) * t1
        z0, z1 = zt + 1.5 + 2.0 * t0 ** 2, zt + 1.5 + 2.0 * t1 ** 2
        wf.poly([(fx - W / 2, y0, z0), (fx + W / 2, y0, z0), (fx + W / 2 + 1.5 * t1, y1, z1), (fx - W / 2 - 1.5 * t1, y1, z1)],
                "waterfall", (1, 1, 1), uvs=[(0, lip_y - y0), (1, lip_y - y0), (1, lip_y - y1), (0, lip_y - y1)])
    # the cascade down to the pool
    zc = zf
    yprev = foot_y
    zprev = zf + 1.0
    run = lip_y - foot_y
    while True:
        zc += 3.0
        hc = max(wcliff.h(fx, zc) or -1e9, ground(fx, zc)) + 0.6
        wf.poly([(fx - W / 2 - 2, yprev, zprev), (fx + W / 2 + 2, yprev, zprev), (fx + W / 2 + 3, hc, zc), (fx - W / 2 - 3, hc, zc)],
                "waterfall", (1, 1, 1), uvs=[(0, run), (1, run), (1, run + (yprev - hc) + 3.0), (0, run + (yprev - hc) + 3.0)])
        run += (yprev - hc) + 3.0
        yprev, zprev = hc, zc
        if (wcliff.h(fx, zc) or -1e9) <= ground(fx, zc) + 0.3 or zc > WZ + 160:
            break
    ms = sc.acc("mid_mist")
    mist_card(ms, (fx, foot_y + 8, zf + 4), 40.0, 20.0, 0.7)
    mist_card(ms, (fx, yprev + 6, zprev + 6), 50.0, 16.0, 0.6)
    # the river from the pool to the field, a ribbon over its bed
    rv = sc.acc("mid_river")
    zz = zprev
    prev = None
    while zz < -6.0:
        xr = river_x(zz)
        w = 6.0 + 0.012 * (-zz)
        y = base(xr, zz) - 0.9
        row = [(xr - w, y, zz), (xr + w, y, zz)]
        if prev:
            rv.poly([prev[0], row[0], row[1], prev[1]], "water", (0.0, 0, 0))
        prev = row
        zz += max(2.0, 0.02 * (-zz))
    pool = sc.acc("mid_pool")
    disc(pool, (fx, yprev - 0.3, zprev + 4), 26.0, 15.0, "water", (0.4, 0, 0))

    # mist between the ridges, clinging to the far slopes
    for (xs, z, y, w, h, al) in ((10.0, -470.0, 70.0, 320.0, 50.0, 0.55), (70.0, -500.0, 80.0, 380.0, 50.0, 0.5),
                                 (40.0, -640.0, 105.0, 700.0, 70.0, 0.55), (-20.0, -700.0, 120.0, 500.0, 70.0, 0.45),
                                 (110.0, -720.0, 115.0, 600.0, 80.0, 0.45)):
        mist_card(ms, (sx(xs, z), y, z), w, h, al)

    # pines: on the valley sides, the crag's foot and the ridges; a village at the crag's foot
    pines = sc.acc("mid_pines")
    near = sc.acc("near_pines")
    village = []
    for i in range(9):
        z = rng.uniform(-205.0, -235.0)
        x = sx(rng.uniform(32.0, 44.0), z)
        village.append((x, z))
    n = 0
    tries = 0
    while n < 430 and tries < 6000:
        tries += 1
        z = -rng.uniform(40.0, 470.0)
        xs = rng.uniform(-40.0, 136.0)
        x = sx(xs, z)
        y = ground(x, z)
        if river_k(x, z) > 0.05 or (crag.h(x, z) or -1) > y or (wcliff.h(x, z) or -1) > y - 1:
            continue
        if any(math.hypot(x - vx, z - vz) < 18 for vx, vz in village):
            continue
        dens = smooth(-0.15, 0.25, fbm(x, z, 0.008, 3, 7) + smooth(10.0, 40.0, y) * 0.5 - 0.3) * smooth(4.0, 14.0, y)
        if rng.random() > dens * 0.9 + 0.05:
            continue
        h = rng.uniform(13.0, 24.0) * (1.0 + 0.0015 * (-z))
        g = mix(hexc("#2a4a2c"), hexc("#3a5a30"), rng.random())
        pine(near if z > -130 else pines, (x, y - 0.5, z), h, rng, g, tiers=3 if z > -200 else 2,
             segs=6 if z > -200 else 5)
        n += 1
    hs = sc.acc("mid_village")
    for k, (x, z) in enumerate(village):
        y = ground(x, z)
        w = rng.uniform(9.0, 13.0)
        gable_house(hs, (x, y - 0.5, z), w, w * 0.8, rng.uniform(5.0, 7.0), rng.uniform(-0.3, 0.3), hexc("#e6e0d2"),
                    hexc("#5a3a2e"), rng, upper=hexc("#7a5234"))
        if k % 3 == 0:
            sc.empty("chimney_%d" % k, (x + w * 0.25, y + 13.0, z))
    # the chapel
    x, z = sx(46.5, -228.0), -228.0
    y = ground(x, z)
    gable_house(hs, (x, y - 0.5, z), 14.0, 9.0, 8.0, 0.0, hexc("#ece6da"), hexc("#3a3a40"), rng)
    hs.box((x - 9.5, y + 8.0, z), (5.0, 17.0, 5.0), "paint", hexc("#ece6da"))
    hs.lathe((x - 9.5, y + 16.5, z), [(3.8, 0), (0.0, 13.0)], 4, "roof", hexc("#3a3a40"), sm=False, phase=math.pi / 4)
    rocks = sc.acc("near_rocks")
    for i in range(24):
        z = rng.uniform(-30, -200)
        x = sx(rng.uniform(-30, 126), z)
        r = rng.uniform(1.2, 3.5) * (1.0 + 0.003 * (-z))
        rock(rocks, (x, ground(x, z) - 0.4, z), (r * 1.3, r * 0.8, r), rng, hexc("#8c8a84"), hexc("#55545a"), vis=sun.vis)


def disc(a, c, rx, rz, material, col, n=18):
    """A flat ellipse facing up (water in a pool, a crater's lake)."""
    x, y, z = c
    a.poly([(x + math.cos(-2 * math.pi * k / n) * rx, y, z + math.sin(-2 * math.pi * k / n) * rz) for k in range(n)],
           material, col)


def rng_flower(x, z):
    h = (math.sin(x * 12.9898 + z * 78.233) * 43758.5453) % 1.0
    return (hexc("#e8d040"), hexc("#f0f0ec"), hexc("#a070c8"), hexc("#e06a5a"))[int(h * 4) % 4]



# ------------------------------------------------------------------ 2 Moonfall

SUN2 = (0.82, 0.2, 0.54)   # hard sunlight, low from the right behind the viewer: long crater shadows to the left


class Craters:
    """Bowl-shaped craters with raised rims and a skirt of ejecta, bucketed for speed."""

    def __init__(self):
        self.list = []
        self.buckets = {}

    def add(self, x, z, R, depth=None, rim=None):
        depth = depth if depth is not None else R * 0.22
        rim = rim if rim is not None else R * 0.07
        c = (x, z, R, depth, rim)
        self.list.append(c)
        reach = R * 2.2
        for i in range(int(math.floor((x - reach) / 50)), int(math.floor((x + reach) / 50)) + 1):
            for k in range(int(math.floor((z - reach) / 50)), int(math.floor((z + reach) / 50)) + 1):
                self.buckets.setdefault((i, k), []).append(c)

    def h(self, x, z):
        v = 0.0
        for (cx, cz, R, depth, rim) in self.buckets.get((int(math.floor(x / 50)), int(math.floor(z / 50))), ()):
            r = math.hypot(x - cx, z - cz) / R
            if r > 2.2:
                continue
            if r < 1.0:
                bowl = -depth * (1.0 - r * r) ** 1.2 + rim * r ** 6
            else:
                bowl = rim * math.exp(-((r - 1.0) / 0.28) ** 2) + rim * 0.3 * math.exp(-(r - 1.0) * 2.5)
            v += bowl
        return v

    def rays(self, x, z):
        """Bright ejecta round the fresh craters (the ones flagged with a negative depth are old and dark)."""
        k = 0.0
        for (cx, cz, R, depth, rim) in self.buckets.get((int(math.floor(x / 50)), int(math.floor(z / 50))), ()):
            r = math.hypot(x - cx, z - cz) / R
            if 0.9 < r < 2.2 and R > 12:
                an = math.atan2(z - cz, x - cx)
                k = max(k, smooth(2.2, 1.0, r) * smooth(0.3, 0.8, n2(an * 6.0, R, 1.0, 5)))
        return k


def dome(a, glow, c, r, rng, ring_col=hexc("#c8c8c4")):
    """A habitat dome: a ring wall with lit windows, the geodesic glass (dome_glow) and a dark rim."""
    x, y, z = c
    a.lathe((x, y, z), [(r * 1.04, 0.0), (r, r * 0.22)], 24, "metal", ring_col, cap=False)
    n = int(r * 1.3)
    for k in range(n):
        an = 2 * math.pi * k / n
        if math.sin(an) < -0.2:
            continue
        a.box((x + math.cos(an) * r * 1.005, y + r * 0.11, z + math.sin(an) * r * 1.005), (r * 0.18, r * 0.06, 0.2),
              "window_glow", (1, 1, 1), ry=-an + math.pi / 2)
    prof = [(r * math.cos(t * math.pi / 2), r * 0.22 + r * 0.85 * math.sin(t * math.pi / 2)) for t in
            (0.0, 0.18, 0.36, 0.52, 0.66, 0.78, 0.88, 0.96, 1.0)]
    glow.lathe((x, y, z), prof, 24, "dome_glow", (1, 1, 1), sm=True)
    a.lathe((x, y + r * 0.22, z), [(r * 1.06, 0.0), (r * 1.06, r * 0.04)], 24, "metal", hexc("#3a3a40"), cap=False)


def moonfall(sc):
    rng = random.Random(500)
    cr = Craters()
    # big craters in the middle and far distance, a fresh one with rays, many small ones near
    for (xs, z, R) in ((62.0, -330.0, 70.0), (10.0, -420.0, 95.0), (100.0, -520.0, 120.0), (40.0, -650.0, 140.0),
                       (-20.0, -760.0, 160.0), (78.0, -200.0, 34.0), (30.0, -240.0, 46.0), (52.0, -140.0, 20.0)):
        cr.add(sx(xs, z), z, R)
    for i in range(140):
        z = -rng.uniform(20.0, 900.0)
        x = sx(rng.uniform(-40.0, 136.0), z)
        R = rng.uniform(3.0, 10.0) * (1.0 + (-z) * 0.006)
        if math.hypot(x - 158.0, z + 245.0) < 90:   # keep the base's ground level
            continue
        cr.add(x, z, R)

    def highlands(x, z):
        d = -z
        h = 0.0
        for (px, pz, H, r) in ((-420.0, -880.0, 115.0, 300.0), (-130.0, -940.0, 95.0, 280.0), (180.0, -900.0, 85.0, 260.0),
                               (450.0, -860.0, 120.0, 320.0), (720.0, -940.0, 100.0, 300.0), (-700.0, -900.0, 95.0, 300.0)):
            dd = ((x - px) / r) ** 2 + ((z - pz) / (r * 0.7)) ** 2
            h = max(h, H * math.exp(-dd * 2.2))
        h += smooth(500.0, 800.0, d) * 30.0 * fbm(x, z, 0.006, 3, 5)
        return h

    def ground(x, z):
        d = -z
        y = 1.5 + 1.2 * fbm(x, z, 0.015, 3, 1.0) + 4.0 * fbm(x, z, 0.004, 2, 2.0) * smooth(60.0, 300.0, d)
        y += highlands(x, z)
        if math.hypot(x - 158.0, z + 245.0) < 80:   # the base's levelled pad
            y = lerp(y, 2.0, smooth(80.0, 55.0, math.hypot(x - 158.0, z + 245.0)))
        return y + cr.h(x, z)

    sun = Sun(SUN2, ground, [], soft=3.0, hmax=200.0)
    REG, REG2, MARE, BRIGHT = hexc("#8a8884"), hexc("#7a7874"), hexc("#55545a"), hexc("#b4b2ac")

    def gcol(x, y, z, ny):
        c = mix(REG, REG2, smooth(-0.4, 0.5, fbm(x, z, 0.02, 3, 3)))
        c = mix(c, MARE, 0.7 * smooth(0.0, 0.4, fbm(x, z, 0.0025, 3, 4)) * smooth(150.0, 400.0, -z))
        c = mix(c, BRIGHT, 0.6 * cr.rays(x, z))
        c = mix(c, mul(c, 0.85), smooth(0.95, 0.7, ny))
        # the rover's tracks
        if -215.0 > z > -222.0 and 78.0 < x < 218.0:
            c = mix(c, mul(c, 0.7), 0.6)
        return wa(c, sun.vis(x, y + 0.3, z))

    land = sc.acc("mid_regolith")
    land.terrain(-6.0, -1000.0, 140, 160, ground, gcol, material="ground", margin=1.5)
    lip = sc.acc("near_lip")
    lip.terrain(-5.9, -6.0, 1, 150, lambda x, z: ground(x, z) - (30.0 if z > -5.95 else 0.0),
                lambda x, y, z, ny: wa(mul(REG2, 0.6), 1.0), material="ground")
    # boulders strewn about (the ones near the camera cast real shadows)
    rocks = sc.acc("near_rocks")
    for i in range(70):
        z = -rng.uniform(15.0, 260.0)
        x = sx(rng.uniform(-40.0, 136.0), z)
        if math.hypot(x - 158.0, z + 245.0) < 85:
            continue
        r = rng.uniform(0.8, 3.0) * (1.0 + (-z) * 0.006)
        rock(rocks, (x, ground(x, z) - r * 0.3, z), (r * 1.2, r * 0.9, r), rng, hexc("#9a9894"), hexc("#55545a"),
             vis=sun.vis)

    # the base: domes linked by tubes, modules, solar arrays, a mast and a radar dish, the landing pad
    B = sc.acc("lm_base")
    G = sc.acc("lm_base_glow")
    BY = 2.0
    domes = [((158.0, -252.0), 19.0), ((124.0, -236.0), 11.0), ((194.0, -232.0), 9.5), ((220.0, -262.0), 7.0),
             ((98.0, -262.0), 8.0)]
    for (x, z), r in domes:
        dome(B, G, (x, BY, z), r, rng)
        sc.empty("light_warm_%d" % len(sc.empties), (x, BY + r * 0.5, z + r * 1.3))
    for (i, j) in ((0, 1), (0, 2), (2, 3), (1, 4)):
        (x0, z0), _ = domes[i]
        (x1, z1), _ = domes[j]
        B.tube([(x0, BY + 2.4, z0), (x1, BY + 2.4, z1)], 2.4, "metal", hexc("#b8b8b4"), segs=10)
        B.box(((x0 + x1) / 2, BY + 2.4, (z0 + z1) / 2 + 2.3), (1.8, 0.8, 0.2), "window_glow", (1, 1, 1))
    # the long habitat modules
    for (x, z, L) in ((186.0, -205.0, 26.0), (128.0, -205.0, 20.0)):
        B.tube([(x - L / 2, BY + 3.0, z), (x + L / 2, BY + 3.0, z)], 3.0, "metal", hexc("#d0d0cc"), segs=10, cap=True)
        for k in range(int(L / 3.0)):
            B.box((x - L / 2 + 2 + k * 3.0, BY + 3.4, z + 2.95), (1.4, 0.7, 0.1), "window_glow", (1, 1, 1))
        for s in (-1, 1):
            B.box((x + s * L * 0.35, BY + 0.4, z), (1.0, 0.8, 4.0), "metal", hexc("#3a3a40"))
    # solar arrays, angled to the sun
    for row in range(3):
        for k in range(7):
            x = 210.0 + k * 7.5
            z = -205.0 - row * 9.0
            B.tube([(x, BY, z), (x, BY + 2.4, z)], 0.15, "metal", hexc("#505058"), segs=4)
            B.box((x, BY + 2.8, z), (6.6, 0.15, 4.2), "glass", hexc("#1a2a5a"), ry=0.0)
    # the mast with its beacons and the radar dish
    mx, mz = 78.0, -232.0
    for k in range(4):
        an = k * math.pi / 2 + math.pi / 4
        B.tube([(mx + math.cos(an) * 2.2, BY, mz + math.sin(an) * 2.2), (mx + math.cos(an) * 0.4, BY + 42.0, mz + math.sin(an) * 0.4)],
               0.18, "metal", hexc("#8a8a90"), segs=3, sm=False)
    for k in range(8):
        y0, y1 = BY + k * 5.0, BY + (k + 1) * 5.0
        t0, t1 = k * 5.0 / 42.0, (k + 1) * 5.0 / 42.0
        w0, w1 = 2.2 - 1.8 * t0, 2.2 - 1.8 * t1
        B.tube([(mx - w0 * 0.7, y0, mz + w0 * 0.7), (mx + w1 * 0.7, y1, mz + w1 * 0.7)], 0.1, "metal", hexc("#8a8a90"),
               segs=3, sm=False)
    G.box((mx, BY + 42.6, mz), (0.9, 0.9, 0.9), "beacon_glow", (1, 1, 1))
    G.box((mx, BY + 26.0, mz + 0.8), (0.6, 0.6, 0.6), "beacon_glow", (1, 1, 1))
    sc.empty("light_red_0", (mx, BY + 42.0, mz + 2.0))
    rd = sc.acc("radar", (mx, BY + 34.0, mz))
    rd.lathe((mx, BY + 34.0, mz + 1.0), [(0.0, 0.0), (2.0, 0.3), (3.6, 1.1), (4.0, 1.5)], 12, "metal", hexc("#d8d8d4"),
             cap=False)
    rd.tube([(mx, BY + 34.0, mz), (mx, BY + 34.0, mz + 3.0)], 0.12, "metal", hexc("#8a8a90"), segs=4)
    # the landing pad: a disc ringed with lights, and the lander that comes and goes
    px, pz = 52.0, -282.0
    disc(B, (px, BY + 0.15, pz), 17.0, 17.0, "paint", hexc("#6a6a6e"), n=24)
    disc(B, (px, BY + 0.2, pz), 12.0, 12.0, "paint", hexc("#7a7a7a"), n=24)
    for k in range(16):
        an = 2 * math.pi * k / 16
        G.box((px + math.cos(an) * 16.0, BY + 0.5, pz + math.sin(an) * 16.0), (0.6, 0.4, 0.6), "lamp_glow", (1, 1, 1))
    sc.empty("light_cool_0", (px, BY + 6.0, pz + 10.0))
    ld = sc.acc("lander", (px, BY, pz))
    for k in range(4):
        an = k * math.pi / 2 + math.pi / 4
        ld.tube([(px + math.cos(an) * 2.2, BY + 3.0, pz + math.sin(an) * 2.2), (px + math.cos(an) * 4.4, BY + 0.2, pz + math.sin(an) * 4.4)],
                0.15, "metal", hexc("#9a9aa0"), segs=3, sm=False)
    ld.lathe((px, BY + 2.6, pz), [(2.6, 0.0), (3.0, 1.2), (3.0, 7.0), (2.0, 9.0), (0.6, 10.2), (0.0, 10.4)], 12, "metal",
             hexc("#e4e4e0"))
    ld.box((px, BY + 6.0, pz + 2.95), (1.0, 0.8, 0.12), "window_glow", (1, 1, 1))
    ld.box((px + 2.9, BY + 7.6, pz), (0.3, 0.3, 0.3), "beacon_glow", (1, 1, 1))
    th = sc.acc("lander_thrust", (px, BY, pz))
    for k in range(3):
        an = k * math.pi / 3
        dx, dz = math.cos(an) * 1.4, math.sin(an) * 1.4
        th.poly([(px - dx, BY + 2.6, pz - dz), (px + dx, BY + 2.6, pz + dz), (px + dx * 0.2, BY - 6.0, pz + dz * 0.2),
                 (px - dx * 0.2, BY - 6.0, pz - dz * 0.2)], "headlight_glow", (0.6, 0.8, 1.0))
    # the rover on its rounds
    rx, rz = 98.0, -218.0
    rv = sc.acc("rover", (rx, BY, rz))
    rv.box((rx, BY + 1.6, rz), (6.0, 1.6, 3.4), "metal", hexc("#d8d4cc"))
    rv.box((rx + 1.0, BY + 2.8, rz), (3.0, 1.0, 3.0), "glass", hexc("#2a3040"))
    for k in range(3):
        for s in (-1, 1):
            rv.tube([(rx - 2.2 + k * 2.2, BY + 0.7, rz + s * 1.5), (rx - 2.2 + k * 2.2, BY + 0.7, rz + s * 2.1)], 0.7,
                    "rock", hexc("#3a3a3e"), segs=8, cap=True)
    rv.box((rx + 3.05, BY + 1.8, rz + 1.0), (0.12, 0.35, 0.5), "headlight_glow", (1, 1, 1))
    rv.box((rx + 3.05, BY + 1.8, rz - 1.0), (0.12, 0.35, 0.5), "headlight_glow", (1, 1, 1))
    rv.tube([(rx - 2.0, BY + 2.4, rz), (rx - 2.0, BY + 5.0, rz)], 0.06, "metal", hexc("#8a8a90"), segs=3)


# ------------------------------------------------------------------ 3 Ember Isle

SUN3 = (-0.55, 0.5, 0.67)   # the moon, high on the left behind the viewer


def lava_flow(a, form, ground, phi0, r0, r1, w0, w1, seed, step=4.0, wiggle=0.12):
    """A river of lava down a cone's flank: from radius r0 to r1 along the angle phi0 (wandering), following the
    surface. UV.x across 0..1, UV.y along the flow in metres. Returns the points along it."""
    pts = []
    r = r0
    while r <= r1:
        phi = phi0 + wiggle * n2(r * 0.02, seed, 1.0, seed)
        x, z = form.cx + math.cos(phi) * r, form.cz + math.sin(phi) * r
        y = max(form.h(x, z) or -1e9, ground(x, z))
        pts.append(Vector((x, y + 0.5, z)))
        r += step
    L = 0.0
    prev = None
    for i, p in enumerate(pts):
        t = i / max(1, len(pts) - 1)
        w = lerp(w0, w1, t)
        q = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        side = Vector((-q.z, 0, q.x)).normalized()
        if prev is not None:
            L += (p - prev[2]).length
        lft, rgt = p - side * w / 2, p + side * w / 2
        lft.y = max(form.h(lft.x, lft.z) or -1e9, ground(lft.x, lft.z)) + 0.35
        rgt.y = max(form.h(rgt.x, rgt.z) or -1e9, ground(rgt.x, rgt.z)) + 0.35
        if prev is not None:
            a.poly([prev[0], lft, rgt, prev[1]], "lava_glow", (1, 1, 1),
                   uvs=[(0.0, prev[3]), (0.0, L), (1.0, L), (1.0, prev[3])])
        prev = (lft, rgt, p, L)
    return pts


def basalt_columns(a, c, n, r, h, rng, col):
    """A cluster of hexagonal basalt columns, stepped."""
    x, y, z = c
    for i in range(n):
        an = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, r * 2.5)
        cx, cz = x + math.cos(an) * d, z + math.sin(an) * d * 0.7
        hh = h * rng.uniform(0.4, 1.0) * (1.0 - d / (r * 3.2))
        a.lathe((cx, y, cz), [(r, 0.0), (r, hh)], 6, "rock", mul(col, rng.uniform(0.8, 1.15)), sm=False,
                phase=rng.uniform(0, 1))


def ember_isle(sc):
    rng = random.Random(600)
    VX, VZ = sx(74.0, -640.0), -640.0
    H = 100.0

    def ground(x, z):
        d = -z
        xs = xs_of(x, z)
        # the island: the ash plain near, a beach, the sea beyond; on the right the land runs on to the cone
        shore = -150.0 - 40.0 * fbm(x, z, 0.008, 2, 3.0) - 260.0 * smooth(55.0, 90.0, xs)
        land = 4.0 + 2.5 * fbm(x, z, 0.012, 3, 1.0) + 1.5 * fbm(x, z, 0.05, 2, 2.0)
        y = land * smooth(shore - 30.0, shore + 25.0, z) - 6.0 * (1.0 - smooth(shore - 30.0, shore + 25.0, z))
        # far islands on the left
        for (ix, iz, ir, ih) in ((sx(6.0, -720.0), -720.0, 120.0, 34.0), (sx(-30.0, -880.0), -880.0, 190.0, 52.0),
                                 (sx(30.0, -950.0), -950.0, 140.0, 26.0)):
            dd = math.hypot((x - ix) / ir, (z - iz) / (ir * 0.5))
            if dd < 1.2:
                y = max(y, ih * (1.0 - dd) ** 0.8 * (0.8 + 0.4 * fbm(x, z, 0.01, 2, 4.0)) if dd < 1.0 else -6.0)
        return y

    cone = Landform((VX, VZ), 30.0, 26.0,
                    [(0.0, H - 30.0, 0.0), (0.5, H - 27.0, 0.3), (0.82, H - 10.0, 0.8), (1.0, H, 1.0)],
                    [(6.0, H - 4.0, 1.0), (18.0, H * 0.88, 1.0), (40.0, H * 0.72, 0.9), (75.0, H * 0.53, 0.8),
                     (120.0, H * 0.35, 0.6), (175.0, H * 0.18, 0.4), (240.0, H * 0.06, 0.2), (300.0, -4.0, 0.0)],
                    y0=0.0, p=2.0, edge=0.12, seed=21.0, flute=0.06, fscale=3.0)
    # a second, older cone behind on the left, a ridge joining them
    old = Landform((VX - 330.0, VZ - 190.0), 40.0, 34.0, [(0.0, 70.0, 0), (0.7, 74.0, 0.3), (1.0, 80.0, 1.0)],
                   [(30.0, 64.0, 0.8), (90.0, 42.0, 0.6), (170.0, 18.0, 0.3), (260.0, -4.0, 0)], y0=0.0, edge=0.15,
                   seed=22.0, flute=0.08, fscale=2.0)
    forms = [cone, old]
    sun = Sun(SUN3, ground, forms, soft=6.0, hmax=150.0)
    ASH, ASH2, BASALT, SAND = hexc("#4a4442"), hexc("#5a504a"), hexc("#2c2a2e"), hexc("#28262a")
    RUST = hexc("#5a2a1a")

    def gcol(x, y, z, ny):
        c = mix(ASH, ASH2, smooth(-0.4, 0.5, fbm(x, z, 0.02, 3, 3)))
        c = mix(c, BASALT, smooth(0.8, 0.6, ny))
        c = mix(c, RUST, 0.35 * smooth(0.2, 0.6, fbm(x, z, 0.01, 2, 6)))
        c = mix(SAND, c, smooth(0.5, 3.0, y))   # black sand at the water
        # warmed by the lava: the ground round the cone's foot glows dull red
        hot = math.exp(-((x - VX) ** 2 + (z - VZ) ** 2) / 60000.0)
        c = mix(c, hexc("#4a1a10"), 0.6 * hot)
        return wa(c, sun.vis(x, y + 0.3, z))

    land = sc.acc("mid_island")
    land.terrain(-6.0, -1000.0, 120, 150, ground, gcol, material="ground", margin=1.5)
    lip = sc.acc("near_lip")
    lip.terrain(-5.9, -6.0, 1, 150, lambda x, z: ground(x, z) - (30.0 if z > -5.95 else 0.0),
                lambda x, y, z, ny: wa(mul(ASH, 0.6), 1.0), material="ground")

    def shallow(x, z):
        return smooth(-4.0, 0.2, ground(x, z))
    sea = sc.acc("mid_sea")
    sea.terrain(-60.0, -1000.0, 70, 90, lambda x, z: 0.0, lambda x, y, z, ny: (shallow(x, z), 0.0, 0.0),
                material="water", margin=1.8)

    def ccol(x, y, z, ny, hrel, out):
        c = mix(hexc("#262224"), hexc("#3a3230"), smooth(-0.3, 0.4, n3((x * 0.03, y * 0.05, z * 0.03), 1.0, 3)))
        c = mix(c, hexc("#4a2a22"), 0.4 * smooth(0.6, 0.9, hrel))   # oxidised near the top
        if out < 0.0:
            c = mix(c, hexc("#6a2412"), smooth(0.85, 0.7, hrel))   # the crater's hot walls
        return c
    a = sc.acc("lm_volcano")
    cone.build(a, "rock", ccol, segs=72, ground=ground, vis=sun.vis)
    old.build(a, "rock", ccol, segs=40, ground=ground, vis=sun.vis)
    # the lava lake in the crater, the fountain, the plume
    crater_y = cone.y0 + H - 27.0
    disc(a, (VX, crater_y + 1.5, VZ), 17.0, 15.0, "crater_glow", (1, 1, 1), n=20)
    sc.empty("ember_0", (VX, crater_y + 3.0, VZ))
    sc.empty("smoke_0", (VX, crater_y + 12.0, VZ))
    sc.empty("light_lava_0", (VX, H + 30.0, VZ + 40.0))
    sc.empty("glow_0", (VX, H + 10.0, VZ))
    # the lava rivers down the flanks; the longest reaches the sea on the left
    lv = sc.acc("lm_lava")
    flows = [(math.pi * 0.64, 290.0, 8.0, 20.0, 1.0), (math.pi * 0.47, 200.0, 7.0, 15.0, 2.0),
             (math.pi * 0.36, 150.0, 5.0, 10.0, 3.0), (math.pi * 0.56, 120.0, 4.0, 8.0, 4.0)]
    for k, (phi, r1, w0, w1, sd) in enumerate(flows):
        pts = lava_flow(lv, cone, ground, phi, 30.0, r1, w0, w1, sd)
        mid = pts[len(pts) // 2]
        sc.empty("light_lava_%d" % (k + 1), (mid.x, mid.y + 25.0, mid.z + 20.0))
        if k == 0:
            end = pts[-1]
            sc.empty("steam_0", (end.x, 0.5, end.z))
            sc.empty("glow_1", (end.x, 4.0, end.z))
        if k == 1:
            sc.empty("glow_2", (mid.x, mid.y + 3.0, mid.z))

    # glowing cracks in the ash plain, smoke from vents, basalt columns, charred trees
    ck = sc.acc("near_cracks")
    for i in range(14):
        z0 = -rng.uniform(40.0, 150.0)
        x0 = sx(rng.choice((rng.uniform(-30.0, 30.0), rng.uniform(70.0, 126.0))), z0)
        an = rng.uniform(0, math.pi)
        L = 0.0
        p = Vector((x0, 0, z0))
        prev = None
        for k in range(rng.randint(5, 9)):
            an += rng.uniform(-0.7, 0.7)
            q = p + Vector((math.cos(an), 0, math.sin(an))) * rng.uniform(4.0, 9.0)
            w = 0.9 * (1.0 - k / 10.0) + 0.2
            side = Vector((-math.sin(an), 0, math.cos(an))) * w
            a0, b0 = p - side, p + side
            a1, b1 = q - side * 0.8, q + side * 0.8
            for v in (a0, b0, a1, b1):
                v.y = ground(v.x, v.z) + 0.08
            seg = (q - p).length
            ck.poly([a0, a1, b1, b0], "crack_glow", (1, 1, 1), uvs=[(0, L), (0, L + seg), (1, L + seg), (1, L)])
            L += seg
            p = q
    for i in range(3):
        z = -rng.uniform(70.0, 160.0)
        x = sx(rng.uniform(-20.0, 116.0), z)
        sc.empty("chimney_%d" % i, (x, ground(x, z) + 0.5, z))
    bc = sc.acc("near_basalt")
    for (xs, z, n, r, h) in ((108.0, -60.0, 16, 1.6, 9.0), (-14.0, -90.0, 12, 2.0, 11.0), (96.0, -140.0, 10, 2.4, 13.0)):
        x = sx(xs, z)
        basalt_columns(bc, (x, ground(x, z) - 1.0, z), n, r, h, rng, hexc("#2a2628"))
    tr = sc.acc("near_trees")
    for i in range(16):
        z = -rng.uniform(30.0, 200.0)
        x = sx(rng.uniform(-40.0, 136.0), z)
        y = ground(x, z)
        h = rng.uniform(6.0, 12.0)
        lean = rng.uniform(-0.15, 0.15)
        tr.tube([(x, y - 0.5, z), (x + lean * h * 0.5, y + h * 0.6, z), (x + lean * h, y + h, z)], [0.35, 0.25, 0.08],
                "wood", hexc("#141012"), segs=5)
        for k in range(3):
            an = rng.uniform(0, 2 * math.pi)
            b0 = (x + lean * h * 0.55, y + h * rng.uniform(0.45, 0.75), z)
            tr.tube([b0, (b0[0] + math.cos(an) * h * 0.3, b0[1] + h * 0.18, b0[2] + math.sin(an) * h * 0.2)], [0.14, 0.04],
                    "wood", hexc("#141012"), segs=3)
    rocks = sc.acc("near_rocks")
    for i in range(30):
        z = -rng.uniform(15.0, 160.0)
        x = sx(rng.uniform(-40.0, 136.0), z)
        r = rng.uniform(0.8, 2.6)
        rock(rocks, (x, ground(x, z) - 0.3, z), (r * 1.3, r * 0.8, r), rng, hexc("#3a3436"), hexc("#141214"),
             vis=sun.vis)


# ------------------------------------------------------------------ 4 Frozen Wastes

SUN4 = (-0.75, 0.3, 0.56)   # the low moon on the left, behind the viewer


def station_module(a, c, L, w, h, ry, col, rng, legs=2.6, lit=0.75):
    """A station building on stilts: a long box, a band of windows, a darker roof."""
    x, y, z = c
    yb = y + legs
    cr, sr = math.cos(ry), math.sin(ry)
    a.box((x, yb + h / 2, z), (L, h, w), "paint", col, ry=ry, cols=(mul(col, 0.8), col))
    a.box((x, yb + h + 0.15, z), (L + 0.3, 0.3, w + 0.3), "metal", hexc("#3a3e46"), ry=ry)
    for k in range(int(L / 4.0)):
        if True:
            u = -L / 2 + 2.0 + k * 4.0
            px, pz = u * cr + (w / 2 + 0.03) * sr, -u * sr + (w / 2 + 0.03) * cr
            if rng.random() < lit:
                a.box((x + px, yb + h * 0.55, z + pz), (1.6, 0.9, 0.08), "window_glow", (1, 1, 1), ry=ry)
            else:
                a.box((x + px, yb + h * 0.55, z + pz), (1.6, 0.9, 0.08), "paint", hexc("#1a2230"), ry=ry)
    for u in (-L / 2 + 1.0, 0.0, L / 2 - 1.0):
        for v in (-w / 2 + 0.6, w / 2 - 0.6):
            px, pz = u * cr + v * sr, -u * sr + v * cr
            a.tube([(x + px, y - 1.0, z + pz), (x + px, yb, z + pz)], 0.22, "metal", hexc("#4a4e58"), segs=4)


def berg(form_list, c, rx, rz, H, seed, rot=0.0, tabular=True):
    if tabular:
        inner = [(0.0, H, 0.0), (0.8, H * 0.99, 0.1), (0.97, H * 0.97, 0.6), (1.0, H * 0.93, 1.0)]
        outer = [(0.6 + 1.2 * t, H * (0.93 - 0.95 * t) - 2.0 * t, 1.0) for t in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0)]
        outer += [(3.0, -4.0, 0.3)]
        f = Landform(c, rx, rz, inner, outer, y0=0.0, rot=rot, p=2.6, edge=0.16, seed=seed, flute=0.1, fscale=2.5)
    else:
        inner = [(0.0, H, 0.0), (0.3, H * 0.8, 0.4), (0.7, H * 0.45, 1.0), (1.0, H * 0.18, 1.0)]
        outer = [(4.0, H * 0.04, 0.6), (8.0, -4.0, 0.2)]
        f = Landform(c, rx, rz, inner, outer, y0=0.0, rot=rot, p=2.0, edge=0.3, seed=seed, flute=0.25, fscale=1.2)
    form_list.append(f)
    return f


def frozen_wastes(sc):
    rng = random.Random(700)
    SHORE = -235.0

    def ground(x, z):
        d = -z
        xs = xs_of(x, z)
        shore = SHORE - 30.0 * fbm(x, z, 0.01, 2, 3.0) - 160.0 * smooth(15.0, -30.0, xs)
        land = 3.0 + 2.0 * fbm(x, z, 0.012, 3, 1.0) + 0.6 * fbm(x * 0.3, z * 2.0, 0.08, 2, 2.0)   # wind-carved drifts
        k = smooth(shore - 6.0, shore + 4.0, z)
        y = land * k + (-0.2) * (1.0 - k)
        # the glaciated range on the left, far; the ice shelf's edge
        for (px, pz, H, r) in ((-520.0, -820.0, 150.0, 320.0), (-260.0, -900.0, 120.0, 260.0), (-760.0, -930.0, 170.0, 340.0),
                               (-30.0, -980.0, 70.0, 240.0)):
            dd = ((x - px) / r) ** 2 + ((z - pz) / (r * 0.7)) ** 2
            y = max(y, H * math.exp(-dd * 2.0) * (0.75 + 0.5 * ridged(x, z, 0.008, 3, 5.0)) - 2.0)
        return y

    forms = []
    for (xs, z, rx, rz, H, sd, tab) in ((56.0, -400.0, 46.0, 26.0, 24.0, 1.0, True), (86.0, -540.0, 95.0, 40.0, 38.0, 2.0, True),
                                        (112.0, -330.0, 22.0, 18.0, 30.0, 3.0, False), (30.0, -560.0, 28.0, 20.0, 34.0, 4.0, False),
                                        (70.0, -700.0, 120.0, 46.0, 34.0, 5.0, True), (120.0, -800.0, 80.0, 40.0, 30.0, 6.0, True),
                                        (44.0, -300.0, 12.0, 10.0, 12.0, 7.0, False), (98.0, -450.0, 14.0, 12.0, 15.0, 8.0, False),
                                        (8.0, -820.0, 60.0, 30.0, 26.0, 9.0, True)):
        berg(forms, (sx(xs, z), z), rx, rz, H, sd, rot=rng.uniform(-0.3, 0.3), tabular=tab)
    sun = Sun(SUN4, ground, forms, soft=6.0, hmax=180.0)
    SNOW, SNOW2, BLUE = hexc("#dfe8f3"), hexc("#c6d4e6"), hexc("#7894b8")

    def gcol(x, y, z, ny):
        c = mix(SNOW, SNOW2, smooth(-0.3, 0.5, fbm(x, z, 0.02, 3, 3)))
        c = mix(c, BLUE, smooth(0.8, 0.5, ny) * 0.7)
        c = mix(c, hexc("#4a5464"), smooth(0.55, 0.35, ny))   # rock where the far range is steep
        return wa(c, sun.vis(x, y + 0.3, z))

    land = sc.acc("mid_snowfield")
    land.terrain(-6.0, -1000.0, 120, 150, ground, gcol, material="snow", margin=1.5)
    lip = sc.acc("near_lip")
    lip.terrain(-5.9, -6.0, 1, 150, lambda x, z: ground(x, z) - (30.0 if z > -5.95 else 0.0),
                lambda x, y, z, ny: wa(SNOW2, 1.0), material="snow")
    ice = sc.acc("mid_seaice")
    ice.terrain(-150.0, -1000.0, 50, 80, lambda x, z: 0.0, lambda x, y, z, ny: (1, 1, 1, sun.vis(x, 0.3, z)),
                material="seaice", margin=1.8)
    # leads of open water wandering through the ice
    ld = sc.acc("mid_leads")
    for (z0, z1, xs0, sd) in ((-330.0, -720.0, 40.0, 1.0), (-450.0, -900.0, 100.0, 2.0)):
        prev = None
        z = z0
        while z > z1:
            x = sx(xs0 + 18.0 * math.sin(z * 0.012 + sd) + 8.0 * n2(z * 0.01, sd, 1.0, sd), z)
            w = 4.0 + 6.0 * (0.5 + 0.5 * math.sin(z * 0.03 + sd * 3))
            row = [(x - w, 0.06, z), (x + w, 0.06, z)]
            if prev:
                ld.poly([prev[0], row[0], row[1], prev[1]][::-1], "water", (0.0, 0, 0))
            prev = row
            z -= 8.0
    BERG_TOP, BERG, BERG_DEEP = hexc("#e8f0f8"), hexc("#a8c4dc"), hexc("#5a86b4")

    def bcol(x, y, z, ny, hrel, out):
        if ny > 0.7 and hrel > 0.85:
            return mix(BERG_TOP, hexc("#d0dcea"), smooth(-0.3, 0.4, n2(x, z, 0.05, 3)))
        c = mix(BERG, BERG_DEEP, smooth(0.1, 0.6, n3((x * 0.04, y * 0.25, z * 0.04), 1.0, 4)))
        c = mix(c, hexc("#ffffff"), 0.35 * smooth(0.55, 0.75, n3((x * 0.1, y * 0.6, z * 0.1), 1.0, 6)))   # bands
        c = mix(c, BERG_DEEP, smooth(0.3, 0.0, y) * 0.6)
        return c
    b = sc.acc("mid_bergs")
    for f in forms:
        if f.p >= 2.5:   # tabular
            f.build(b, "ice", bcol, segs=40 if f.rx > 30 else 24, ground=None, vis=sun.vis)
            continue
        # a jagged berg: a heap of broken, tilted ice
        brng = random.Random(int(f.seed * 31))
        H = f.top - 2.0
        for k in range(5):
            ox, oz = brng.uniform(-0.5, 0.5) * f.rx, brng.uniform(-0.4, 0.4) * f.rz
            hh = H * brng.uniform(0.45, 1.0) * (1.0 - 0.15 * k)
            rr = f.rx * brng.uniform(0.35, 0.6)

            def jc(nx, ny, nz, q, hh=hh):
                c = bcol(q.x, q.y, q.z, ny, q.y / max(hh, 1.0), 0.0)
                return wa(c, sun.vis(q.x + nx, q.y + 1.0, q.z + nz))
            b.blob((f.cx + ox, -2.0, f.cz + oz), (rr, hh, rr * 0.8), "ice", jc, segs=7, rings=5, rough=0.35,
                   nscale=0.7, seed=brng.random() * 40, sm=False, cut=0.0)

    # the station on the shore at the left: modules on stilts, the radome, the mast, a wind turbine, fuel tanks,
    # floodlights, a snowcat, flags along the track
    st = sc.acc("lm_station")
    sg = sc.acc("lm_station_glow")
    SX, SZ = sx(22.0, -190.0), -190.0
    gy = ground(SX, SZ)
    station_module(st, (SX, gy, SZ), 30.0, 9.0, 4.2, 0.0, hexc("#c4472a"), rng)
    station_module(st, (SX + 26.0, gy, SZ - 14.0), 22.0, 8.0, 3.8, 0.4, hexc("#d8d8d4"), rng)
    station_module(st, (SX - 24.0, gy, SZ - 10.0), 18.0, 8.0, 3.6, -0.3, hexc("#d8a030"), rng)
    st.tube([(SX + 12.0, gy + 4.5, SZ - 4.0), (SX + 18.0, gy + 4.5, SZ - 10.0)], 1.4, "metal", hexc("#9a9ea8"), segs=8)
    # the radome on its tower
    rx_, rz_ = SX + 52.0, SZ - 30.0
    st.box((rx_, gy + 5.0, rz_), (8.0, 10.0, 8.0), "paint", hexc("#d8d8d4"))
    st.blob((rx_, gy + 15.5, rz_), (7.0, 7.0, 7.0), "paint", hexc("#eeeeea"), segs=16, rings=8, rough=0.0, cut=-0.3)
    # the mast
    mx, mz = SX - 46.0, SZ - 22.0
    for k in range(3):
        an = k * 2 * math.pi / 3
        st.tube([(mx + math.cos(an) * 1.6, gy, mz + math.sin(an) * 1.6), (mx, gy + 46.0, mz)], 0.16, "metal",
                hexc("#c4472a") if k == 0 else hexc("#d8d8d4"), segs=3, sm=False)
        st.tube([(mx, gy + 30.0, mz), (mx + math.cos(an) * 30.0, gy - 0.5, mz + math.sin(an) * 22.0)], 0.04, "metal",
                hexc("#5a5e66"), segs=3, sm=False)
    for yy in (46.5, 31.0, 16.0):
        sg.box((mx, gy + yy, mz + 0.4), (0.8, 0.8, 0.8), "beacon_glow", (1, 1, 1))
    sc.empty("light_red_0", (mx, gy + 46.0, mz + 2.0))
    # the wind turbine
    tx_, tz_ = SX + 78.0, SZ - 50.0
    st.lathe((tx_, gy, tz_), [(1.4, 0.0), (0.7, 34.0)], 8, "paint", hexc("#e4e4e0"), cap=True)
    st.box((tx_, gy + 34.5, tz_ - 0.5), (1.6, 1.6, 3.6), "paint", hexc("#e4e4e0"))
    rot = sc.acc("rotor_0", (tx_, gy + 34.5, tz_ + 1.6))
    for k in range(3):
        an = k * 2 * math.pi / 3 + 0.3
        ca, sa = math.cos(an), math.sin(an)
        hub = Vector((tx_, gy + 34.5, tz_ + 1.6))
        rot.poly([hub + Vector((ca * 0.6 - sa * 0.7, sa * 0.6 + ca * 0.7, 0.05)), hub + Vector((ca * 15.0 - sa * 0.3, sa * 15.0 + ca * 0.3, 0.1)),
                  hub + Vector((ca * 15.0, sa * 15.0, 0.1)), hub + Vector((ca * 0.6 + sa * 0.5, sa * 0.6 - ca * 0.5, 0.05))],
                 "paint", hexc("#f0f0ec"))
    rot.blob((tx_, gy + 34.5, tz_ + 2.0), (0.8, 0.8, 1.2), "paint", hexc("#e4e4e0"), segs=8, rings=4, rough=0.0)
    # fuel tanks
    for k in range(3):
        st.tube([(SX - 6.0 + k * 6.5, gy + 2.2, SZ + 16.0), (SX - 6.0 + k * 6.5, gy + 2.2, SZ + 6.0)], 2.2, "paint",
                hexc("#c8b878"), segs=10, cap=True)
    # floodlights on poles, with their pools of light
    for k, (dx, dz) in enumerate(((-12.0, 16.0), (14.0, 12.0), (40.0, -8.0))):
        px, pz = SX + dx, SZ + dz
        py = ground(px, pz)
        st.tube([(px, py - 0.5, pz), (px, py + 10.0, pz)], 0.18, "metal", hexc("#4a4e58"), segs=4)
        sg.box((px, py + 10.0, pz + 0.4), (1.2, 0.6, 0.4), "lamp_glow", (1, 1, 1))
        sc.empty("light_warm_%d" % k, (px, py + 8.0, pz + 3.0))
    # a snowcat with its lights on, flags marking the track down to the sea ice
    cx_, cz_ = SX + 34.0, SZ + 20.0
    cy = ground(cx_, cz_)
    st.box((cx_, cy + 1.6, cz_), (5.6, 2.0, 3.2), "paint", hexc("#c4472a"))
    st.box((cx_ - 0.6, cy + 3.1, cz_), (3.4, 1.2, 3.0), "glass", hexc("#202838"))
    for s in (-1, 1):
        st.box((cx_, cy + 0.6, cz_ + s * 1.9), (6.4, 1.2, 0.9), "metal", hexc("#202228"))
    sg.box((cx_ + 2.85, cy + 2.0, cz_ + 1.0), (0.1, 0.4, 0.5), "headlight_glow", (1, 1, 1))
    sg.box((cx_ + 2.85, cy + 2.0, cz_ - 1.0), (0.1, 0.4, 0.5), "headlight_glow", (1, 1, 1))
    sc.empty("light_cool_0", (cx_ + 8.0, cy + 2.0, cz_))
    fl = sc.acc("near_flags")
    for k in range(10):
        z = SZ + 30.0 - k * 9.0
        x = cx_ + 10.0 + k * 9.0 + 6.0 * math.sin(k * 0.8)
        flag(fl, (x, ground(x, z) - 0.3, z), 2.6, 0.9, hexc("#e03a20") if k % 2 else hexc("#f0c020"))
    sc.empty("snow_0", (48.0, 1.0, -60.0))
    sc.empty("snow_1", (48.0, 2.0, -180.0))
    # ice blocks and drifts near
    rocks = sc.acc("near_ice")
    for i in range(26):
        z = -rng.uniform(20.0, 200.0)
        x = sx(rng.uniform(-40.0, 136.0), z)
        if math.hypot(x - SX, z - SZ) < 70:
            continue
        r = rng.uniform(0.8, 2.6)
        rock(rocks, (x, ground(x, z) - 0.3, z), (r * 1.3, r * 0.9, r), rng, hexc("#e0eaf4"), hexc("#7c9ac0"),
             vis=sun.vis)

# ------------------------------------------------------------------ main

THEMES = [mesa_dusk, alpine_front, moonfall, ember_isle, frozen_wastes]


def main():
    for n, fn in enumerate(THEMES):
        if ONLY and n not in ONLY:
            continue
        sc = Scene(n)
        fn(sc)
        sc.export()


main()
