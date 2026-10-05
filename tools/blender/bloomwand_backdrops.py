"""Bloomwand (game 33) fairy-tale backdrops: six dioramas that stand behind the 20 x 15 single-screen levels, one per
theme: a spring glade of giant bluebells and toadstools, a twilight meadow with a fairy ring of glowing mushrooms, a
grotto of luminous crystals round a glowing pool, a castle floating above a sunset sea of clouds, a snowy night forest
with lantern-lit tree houses round a frozen pond, and a briar tower in a storm. Original designs: every place is an
invented, generic storybook one. Deterministic (fixed seeds); output CC BY-SA 4.0; provenance: this script only
(written by Claude Code for the project), no third-party assets, no textures (vertex colours).
Run: .tools/bin/blender -b --factory-startup -P tools/blender/bloomwand_backdrops.py -- \
         godot/games/bloomwand/art/backdrops [n ...]

Coordinates: authored in Godot space (x right, y up, z towards the camera) and converted on export. The level is
x 0..20, y 0..15 on the plane z = 0 (blocks 1 m deep, z -0.5..0.5); the camera sits near (10, 7.5, 27), fov 36.
Nothing comes nearer than z = -1.5. Each backdrop_<n>.glb holds
  fg_*      the framing elements beyond the level's sides and the bank under its floor (z -1.5 .. about -10)
  mid_*     ground, water and props behind the level; what lies behind its middle is kept soft and quiet
  lm_*      the landmarks (the fairy ring, the far chamber, the floating castle, the tree houses, the briar tower)
  far_*     far hills, forests and ridges, no further than z -205 (the sky dome's radius is 230)
and named nodes the game animates, each with its origin at its pivot:
  float_<i>  bob gently (floating islands)          drift_<i>  slide slowly to and fro along x (cloud banks)
  swing_<i>  swing about local Z (hanging lanterns)
and empties where the game adds lights and living things: light_warm_<i> / light_cool_<i> / light_magic_<i> /
light_glow_<i> (an omni light), butterfly_<i>, firefly_<i>, petal_<i>, sparkle_<i>, wisp_<i> (motes round it).
Material names carry the game's hints: "*glow*" emissive (lantern_glow tinted by the vertex colour, window_glow,
lamp_glow, door_glow, glowcap_glow (mushroom caps, tinted), dot_glow, glowworm_glow, magic_glow, reflect_glow (light
streaks lying on water or ice: UV.y from the light's foot towards the viewer)), "water" / "ice" / "pool" (the game's
water shader; vertex colour R marks the shallows), "falls" (a waterfall: UV.y down the fall), "beam" (a shaft of
light: UV.x across, UV.y from its source), "mist" (a soft bank: UV.x across, UV.y up; tinted by the vertex colour),
"cloud" (puffy, lit), "crystal" (luminous, tinted by the vertex colour), "*sway*" (bent in the breeze by UV.y, the
height above the plant's foot). All other colour is in the vertex colours (COLOR_0, linear) over white materials,
with the theme's air already mixed in by distance (aerial perspective).
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/bloomwand/art/backdrops")
ONLY = [int(a) for a in argv[1:]]

CAM = Vector((10.0, 7.5, 27.0))
TAN_W = 0.578  # half-width per unit of distance for fov 36 at 16:9
TAN_H = 0.325


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
    return TAN_W * (CAM.z - z) * margin + 6.0


def sx(xs, z):
    """The world x that shows at level x `xs` for depth z (the level plane is z = 0)."""
    return 10.0 + (xs - 10.0) * (CAM.z - z) / CAM.z


def sy(ys, z):
    return 7.5 + (ys - 7.5) * (CAM.z - z) / CAM.z


def xs_of(x, z):
    """Where world x at depth z shows on the level plane."""
    return 10.0 + (x - 10.0) * CAM.z / (CAM.z - z)


def ys_of(y, z):
    return 7.5 + (y - 7.5) * CAM.z / (CAM.z - z)


def dist(p):
    return (Vector(p) - CAM).length


def bez(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t


# ------------------------------------------------------------------ materials

MATS = {}
MAT_DEFS = {
    # name: (base colour, roughness, metallic, emission strength)
    "ground": ((1, 1, 1), 0.95, 0, 0),
    "rock": ((1, 1, 1), 0.85, 0, 0),
    "bark": ((1, 1, 1), 0.9, 0, 0),
    "wood": ((1, 1, 1), 0.8, 0, 0),
    "paint": ((1, 1, 1), 0.6, 0, 0),
    "roof": ((1, 1, 1), 0.5, 0, 0),
    "metal": ((1, 1, 1), 0.35, 0.7, 0),
    "cap": ((1, 1, 1), 0.4, 0, 0),
    "stem": ((1, 1, 1), 0.7, 0, 0),
    "snow": ((1, 1, 1), 0.7, 0, 0),
    "cloud": ((1, 1, 1), 1.0, 0, 0),
    "water": ((1, 1, 1), 0.1, 0, 0),
    "ice": ((1, 1, 1), 0.1, 0, 0),
    "pool": ((1, 1, 1), 0.1, 0, 0),
    "falls": ((1, 1, 1), 1, 0, 0),
    "beam": ((1, 1, 1), 1, 0, 0),
    "mist": ((1, 1, 1), 1, 0, 0),
    "crystal": ((1, 1, 1), 0.1, 0, 2.0),
    "foliage_sway": ((1, 1, 1), 0.85, 0, 0),
    "grass_sway": ((1, 1, 1), 0.85, 0, 0),
    "flower_sway": ((1, 1, 1), 0.7, 0, 0),
    "blossom_sway": ((1, 1, 1), 0.8, 0, 0),
    "lantern_glow": ((1.0, 0.7, 0.35), 0.4, 0, 3.0),
    "window_glow": ((1.0, 0.72, 0.4), 0.4, 0, 2.5),
    "lamp_glow": ((1.0, 0.82, 0.55), 0.4, 0, 4.0),
    "door_glow": ((1.0, 0.7, 0.4), 0.4, 0, 2.0),
    "glowcap_glow": ((0.4, 1.0, 0.9), 0.4, 0, 3.0),
    "dot_glow": ((0.8, 1.0, 1.0), 0.4, 0, 4.0),
    "glowworm_glow": ((0.4, 0.9, 1.0), 0.4, 0, 4.0),
    "magic_glow": ((0.8, 0.4, 1.0), 0.4, 0, 4.0),
    "reflect_glow": ((1.0, 0.75, 0.4), 1, 0, 1.2),
}
NOAIR = ("glow", "water", "ice", "pool", "beam", "mist", "falls", "crystal")
AIR = None   # (colour, per metre, start distance, max share): the theme's aerial perspective


def mat(name):
    if name in MATS:
        return MATS[name]
    col, rough, metal, emit = MAT_DEFS[name]
    m = bpy.data.materials.new(name)
    if not m.node_tree:
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


def aired(c, p, mname):
    if AIR is None or any(s in mname for s in NOAIR):
        return c
    col, k, d0, mx = AIR
    d = (p - CAM).length - d0
    if d <= 0:
        return c
    return mix(c, col, (1 - math.exp(-d * k)) * mx)


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

    def scale_about(self, c, k, first=0):
        """Scales the vertices added since index `first` about c."""
        c = Vector(c)
        for i in range(first, len(self.v)):
            self.v[i] = c + (self.v[i] - c) * k

    # -------- primitives

    def box(self, c, size, material, col, ry=0.0, taper=1.0, cols=None):
        cx, cy, cz = c
        sx_, sy_, sz_ = size[0] / 2, size[1] / 2, size[2] / 2
        cr, sr = math.cos(ry), math.sin(ry)
        pts = []
        for yy in (-1, 1):
            k = taper if yy > 0 else 1.0
            for xx, zz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                x, z = xx * sx_ * k, zz * sz_ * k
                pts.append(self.vert((cx + x * cr + z * sr, cy + yy * sy_, cz - x * sr + z * cr)))
        top, side = (cols if cols else (col, col))
        C = (cx, cy, cz)
        self.face([pts[4], pts[5], pts[6], pts[7]], material, top, out=C)
        self.face([pts[0], pts[1], pts[2], pts[3]], material, side, out=C)
        for i in range(4):
            j = (i + 1) % 4
            self.face([pts[i], pts[j], pts[4 + j], pts[4 + i]], material, side, out=C)

    def lathe(self, c, prof, segs, material, col, sm=True, rough=0.0, nscale=0.5, seed=0.0, sx=1.0, sz=1.0,
              cap=True, phase=0.0):
        """Revolves prof [(r, y)] (bottom to top) about a vertical axis at c. col: colour or fn(x, y, z)."""
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
        """A tube along pts with per-point radii. col: colour or fn(i, point) -> colour."""
        cf = col if callable(col) else (lambda i, p: col)
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
        for i in range(len(pts) - 1):
            c = (pts[i] + pts[i + 1]) / 2
            for j in range(segs):
                k = (j + 1) % segs
                ids = [rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]]
                cs = [cf(i, pts[i]), cf(i, pts[i]), cf(i + 1, pts[i + 1]), cf(i + 1, pts[i + 1])]
                self.face(ids, material, cs, sm=sm, out=c)
        if cap:
            i = len(pts) - 1
            t = self.vert(pts[i])
            far = pts[i] - (pts[i] - pts[i - 1]).normalized() * 100
            for j in range(segs):
                self.face([rings[i][j], rings[i][(j + 1) % segs], t], material, cf(i, pts[i]), out=far)

    def terrain(self, z_near, z_far, rows, cols, h, col, material="ground", sm=True, xl=None, xr=None, margin=1.5,
                down=False, geo=True):
        """A height field whose rows widen with distance (so it always fills the view). h(x, z) -> y;
        col(x, y, z, ny) -> colour, ny the up component of the normal. down: it faces down (a ceiling)."""
        dn, df = CAM.z - z_near, CAM.z - z_far
        grid = []
        for i in range(rows + 1):
            t = i / rows
            d = dn * (df / dn) ** t if geo else dn + (df - dn) * t
            z = CAM.z - d
            a = 10 - half_w(z, margin) if xl is None else xl(z)
            b = 10 + half_w(z, margin) if xr is None else xr(z)
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
                          out=(c.x, c.y + (100 if down else -100), c.z))

    def ridge(self, xs, z, base, top_fn, col, material="rock", sm=True):
        """A vertical silhouette sheet (for far ranges): top_fn(x) -> y, from y=base."""
        prev = None
        for x in xs:
            y = top_fn(x)
            a = self.vert((x, base, z))
            b = self.vert((x, y, z))
            if prev:
                pa, pb, py = prev
                self.face([pa, a, b, pb], material, [col(x, base), col(x, base), col(x, y), col(x, py)], sm=sm,
                          out=(x, (base + y) / 2, z - 100))
            prev = (a, b, y)

    def ribbon(self, pts, widths, material, col, uv=False, facing=None):
        """A flat strip along pts, turned to face the camera (or across `facing`); col: colour or fn(t) -> colour.
        uv: UV.x across (0..1), UV.y the distance along from the first point."""
        pts = [Vector(p) for p in pts]
        cf = col if callable(col) else (lambda t: col)
        L = 0.0
        prev = None
        n = len(pts)
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            side = (facing if facing is not None else t.cross(CAM - p)).normalized()
            w = widths[i] if isinstance(widths, (list, tuple)) else widths
            if i:
                L += (p - pts[i - 1]).length
            cur = (p - side * w / 2, p + side * w / 2, L, cf(i / max(1, n - 1)))
            if prev:
                q = [prev[0], prev[1], cur[1], cur[0]]
                uvs = [(0, prev[2]), (1, prev[2]), (1, cur[2]), (0, cur[2])] if uv else None
                self.poly(q, material, [prev[3], prev[3], cur[3], cur[3]], uvs=uvs, out=None)
            prev = cur

    def card(self, c, w, h, material, col, up=Vector((0, 1, 0)), uv=True):
        """A quad facing the camera, centred at c (UV.x across, UV.y up)."""
        c = Vector(c)
        to = (CAM - c)
        right = up.cross(to).normalized()
        u = to.cross(right).normalized()
        pts = [c - right * w / 2 - u * h / 2, c + right * w / 2 - u * h / 2, c + right * w / 2 + u * h / 2,
               c - right * w / 2 + u * h / 2]
        cols = col if isinstance(col, list) else [col] * 4
        self.poly(pts, material, cols, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)] if uv else None)

    def spike(self, p, d, L, w, material, col, tip=None):
        """A three-sided thorn from p along d."""
        p, d = Vector(p), Vector(d).normalized()
        ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
        a = d.cross(ref).normalized()
        b = d.cross(a)
        base = [p + (a * math.cos(k * 2.094) + b * math.sin(k * 2.094)) * w for k in range(3)]
        t = p + d * L
        for k in range(3):
            self.poly([base[k], base[(k + 1) % 3], t], material, [col, col, tip or col], out=p - d)

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
        uv = me.uv_layers.new(name="UVMap") if any(f[3] for f in self.f) else None
        for poly, f in zip(me.polygons, self.f):
            poly.material_index = names.index(f[1])
            poly.use_smooth = f[4]
            for k in range(poly.loop_total):
                c = lin(aired(f[2][k], self.v[f[0][k]], f[1]))
                ca.data[poly.loop_start + k].color = (*c, 1.0)
                if f[3] and uv:
                    uv.data[poly.loop_start + k].uv = (f[3][k][0], 1.0 - f[3][k][1])
        me.color_attributes.active_color = ca
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (o.x, -o.z, o.y)
        return ob


class Scene:
    def __init__(self, n):
        self.n = n
        self.accs = []
        self.empties = []

    def acc(self, name, origin=(0, 0, 0)):
        a = Acc(name, origin)
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
        for a in sorted(self.accs, key=lambda a: -a.tris())[:8]:
            print("    %-22s %6d" % (a.name, a.tris()))
        for m in list(bpy.data.meshes):
            bpy.data.meshes.remove(m)
        for m in list(bpy.data.materials):
            bpy.data.materials.remove(m)
        MATS.clear()
        return total


# ------------------------------------------------------------------ shared props

UV4 = [(0, 0), (1, 0), (1, 1), (0, 1)]


def rock(a, c, r, rng, top, side, segs=7, rings=4, material="rock"):
    def cc(nx, ny, nz, q):
        return mix(side, top, smooth(0.0, 0.8, ny))
    a.blob(c, r, material, cc, segs=segs, rings=rings, rough=0.3, nscale=0.9, seed=rng.random() * 50, sm=False, cut=-0.4)


def grass_patch(a, rng, n, region, ground, cols, h=(0.3, 0.8), w=0.06, avoid=None):
    """n blades scattered in region (x0, x1, z0, z1) on ground(x, z), each one triangle facing the camera."""
    x0, x1, z0, z1 = region
    for i in range(n):
        x, z = rng.uniform(x0, x1), rng.uniform(z1, z0)
        if avoid and avoid(x, z):
            continue
        y = ground(x, z) - 0.05
        hh = rng.uniform(*h)
        lean = rng.uniform(-0.35, 0.35) * hh
        to = (CAM - Vector((x, y, z)))
        side = Vector((to.z, 0, -to.x)).normalized() * w * (0.6 + 0.02 * dist((x, y, z)))
        c = rng.choice(cols)
        a.sway_base = y
        a.poly([(x - side.x, y, z - side.z), (x + side.x, y, z + side.z), (x + lean, y + hh, z + rng.uniform(-0.1, 0.1))],
               "grass_sway", [mul(c, 0.5), mul(c, 0.5), c])
    a.sway_base = None


def fern(a, base, size, rng, green, n=7):
    """A fern: fronds arching out from the crown, each a toothed strip."""
    x, y, z = base
    a.sway_base = y
    for k in range(n):
        an = (k / n) * 2 * math.pi + rng.uniform(-0.3, 0.3)
        out = Vector((math.cos(an), 0, math.sin(an) * 0.6))
        L = size * rng.uniform(0.75, 1.1)
        p0 = Vector(base)
        p1 = p0 + out * L * 0.35 + Vector((0, L * 0.75, 0))
        p2 = p0 + out * L + Vector((0, L * 0.25, 0))
        pts = [bez(p0, p1, p2, t / 8) for t in range(9)]
        ws = [L * 0.22 * math.sin(math.pi * min(1.0, 0.15 + t / 8 * 0.95)) * (1.0 if t % 2 else 0.55) for t in range(9)]
        a.ribbon(pts, ws, "foliage_sway", lambda t, g=green: mix(mul(g, 0.55), mul(g, 1.15), t * 1.3))
    a.sway_base = None


def toadstool(a, base, h, r, cap, rng, spots=True, glow=False, stem_col=hexc("#e8dfcc"), lean=0.0,
              gill=hexc("#d8b8a0"), spot_col=hexc("#fff8ec"), segs=14):
    """A toadstool: a pale stem with a skirt, a domed cap (glossy, or glowing) with white spots."""
    x, y, z = base
    top = Vector((x + lean * h, y + h, z))
    a.tube([(x, y - 0.1, z), (x + lean * h * 0.35, y + h * 0.5, z), top], [r * 0.24, r * 0.19, r * 0.16],
           "stem", lambda i, p: mix(mul(stem_col, 0.75), stem_col, i / 2), segs=8)
    a.lathe((x, y - 0.1, z), [(r * 0.34, 0), (r * 0.3, h * 0.1), (r * 0.2, h * 0.2)], 8, "stem", mul(stem_col, 0.85),
            cap=False)
    a.lathe((top.x, top.y - h * 0.18, top.z), [(r * 0.3, 0), (r * 0.22, h * 0.06)], 8, "stem", mul(stem_col, 0.9),
            cap=False)
    m = "glowcap_glow" if glow else "cap"
    ty = top.y

    def cc(px, py, pz):
        k = (py - ty) / (r * 0.7)
        if k < 0.02:
            return gill
        return mix(mul(cap, 0.6), mix(cap, (1, 1, 1), 0.12), smooth(0.0, 0.9, k))
    prof = [(r * 0.18, -r * 0.02), (r * 0.7, -r * 0.1), (r * 1.0, -r * 0.08), (r * 1.04, 0.02 * r),
            (r * 0.95, 0.28 * r), (r * 0.72, 0.52 * r), (r * 0.38, 0.66 * r), (0.0, 0.7 * r)]
    a.lathe((top.x, ty, top.z), prof, segs, m, cc, sm=True)
    if spots:
        face = math.atan2(CAM.z - z, CAM.x - x)
        for k in range(rng.randint(7, 11)):
            an = face + rng.uniform(-1.6, 1.6)
            t = rng.uniform(0.15, 0.85)
            rr = r * (1.0 - 0.9 * t) + 0.02
            yy = ty + r * (0.05 + 0.6 * math.sin(t * math.pi / 2))
            s = r * rng.uniform(0.06, 0.11)
            a.blob((top.x + math.cos(an) * rr, yy, top.z + math.sin(an) * rr), (s, s * 0.5, s),
                   "dot_glow" if glow else "cap", spot_col, segs=6, rings=2, rough=0.1)


def bluebell(a, base, H, lean, rng, bell=hexc("#5c58d8"), n=7, dz=0.0, leaves=True):
    """A giant bluebell: a stem rising and nodding over to one side, the bells hanging along its arch."""
    x, y, z = base
    a.sway_base = y
    P0 = Vector(base)
    P1 = Vector((x + lean * H * 0.1, y + H * 1.1, z))
    P2 = Vector((x + lean * H * 0.6, y + H * 0.78, z + dz))
    pts = [bez(P0, P1, P2, t / 10) for t in range(11)]
    stem = hexc("#4a7a3a")
    a.tube(pts, [H * 0.02 * (1 - 0.6 * t / 10) for t in range(11)], "flower_sway",
           lambda i, p: mix(mul(stem, 0.6), stem, i / 10), segs=6)
    dark, rim = mul(bell, 0.45), mix(bell, (0.85, 0.85, 1.0), 0.3)
    for k in range(n):
        t = 0.42 + 0.58 * k / max(1, n - 1)
        p = bez(P0, P1, P2, t)
        r = H * 0.05 * (1.0 - 0.45 * k / n)
        q = p + Vector((rng.uniform(-0.6, 0.6) * r + lean * r * 0.4, -r * 1.3, rng.uniform(-0.8, 0.8) * r))
        a.tube([p, q], H * 0.006, "flower_sway", stem, segs=3)
        prof = [(r * 1.3, -r * 2.25), (r * 1.08, -r * 2.05), (r * 0.98, -r * 1.5), (r * 0.82, -r * 0.8),
                (r * 0.55, -r * 0.2), (r * 0.15, 0.0)]
        qy = q.y

        def cc(px, py, pz, qy=qy, r=r):
            return mix(rim, dark, smooth(-r * 2.2, 0.0, py - qy))
        a.lathe(tuple(q), prof, 7, "flower_sway", cc, sm=True, phase=rng.random())
    if leaves:
        for k in range(3):
            an = rng.uniform(0, 2 * math.pi)
            out = Vector((math.cos(an), 0, math.sin(an) * 0.5))
            L = H * rng.uniform(0.3, 0.45)
            lp = [bez(P0, P0 + out * L * 0.3 + Vector((0, L * 0.8, 0)), P0 + out * L + Vector((0, L * 0.2, 0)), t / 6)
                  for t in range(7)]
            a.ribbon(lp, [H * 0.035 * math.sin(math.pi * (0.2 + 0.8 * t / 6)) for t in range(7)], "flower_sway",
                     lambda t: mix(hexc("#2a4a26"), hexc("#5a8a3a"), t))
    a.sway_base = None


def broadleaf(a, leaves, base, h, r, rng, bark, green, crown=True, lean=0.0, branches=3, roots=True, segs=8,
              blobs=4, rough=0.12, crown_r=None):
    x, y, z = base
    pts = []
    for i in range(7):
        t = i / 6
        pts.append((x + lean * h * t + 0.06 * h * math.sin(t * 3 + x), y - 0.4 + h * t, z + 0.03 * h * math.sin(t * 2 + z)))
    a.tube(pts, [r * (1.25 - 0.55 * i / 6) for i in range(7)], "bark",
           lambda i, p, b=bark: mix(mul(b, 0.65), b, 0.4 + 0.6 * n2(p[0], p[1], 0.7)), segs=segs, rough=rough,
           seed=rng.random() * 9, nscale=0.6)
    if roots:
        for k in range(5):
            an = k * 1.257 + rng.uniform(-0.3, 0.3)
            d = Vector((math.cos(an), 0, math.sin(an)))
            a.tube([(x, y + r * 0.9, z), (x + d.x * r * 1.4, y + 0.1, z + d.z * r * 1.4),
                    (x + d.x * r * 2.4, y - 0.3, z + d.z * r * 2.4)], [r * 0.45, r * 0.3, r * 0.1], "bark",
                   mul(bark, 0.8), segs=5)
    ends = []
    for k in range(branches):
        t = rng.uniform(0.55, 0.85)
        p = Vector(pts[int(t * 6)])
        an = rng.uniform(0, 2 * math.pi) if k else math.pi * (0 if rng.random() < 0.5 else 1)
        d = Vector((math.cos(an), rng.uniform(0.5, 1.0), math.sin(an) * 0.6)).normalized()
        e = p + d * h * rng.uniform(0.25, 0.4)
        m = (p + e) / 2 + Vector((0, h * 0.05, 0))
        a.tube([p, m, e], [r * 0.45, r * 0.3, r * 0.12], "bark", bark, segs=5)
        ends.append(e)
    ends.append(Vector(pts[-1]))
    if crown:
        leaves.sway_base = y + h * 0.4
        cr = crown_r or h * 0.22
        for e in ends:
            for j in range(max(1, blobs // 2)):
                rr = cr * rng.uniform(0.7, 1.1)
                c = e + Vector((rng.uniform(-1, 1) * rr * 0.6, rng.uniform(-0.2, 0.5) * rr, rng.uniform(-1, 1) * rr * 0.4))

                def cc(nx, ny, nz, q, g=green):
                    return mix(mul(g, 0.45), mix(g, (1, 1, 0.8), 0.12), smooth(-0.7, 0.9, ny + 0.2 * nx))
                leaves.blob(tuple(c), (rr, rr * 0.75, rr * 0.9), "foliage_sway", cc, segs=8, rings=5, rough=0.3,
                            nscale=1.3, seed=rng.random() * 40)
        leaves.sway_base = None
    return ends


def pine(a, c, h, rng, green, snow=0.0, tiers=4, trunk=hexc("#2a1e18"), segs=7, wf=1.0):
    """A conifer: stacked drooping tiers; snow lies on their upper surfaces."""
    x, y, z = c
    a.sway_base = y
    a.lathe((x, y - 0.3, z), [(h * 0.045, 0), (h * 0.03, h * 0.35)], 5, "bark", trunk, sm=False, cap=False)
    for i in range(tiers):
        t0 = 0.12 + i * (0.78 / tiers)
        r = h * 0.3 * wf * (1 - i / (tiers + 0.7))
        yb = h * t0
        yt = yb + h * 0.4
        sd = rng.random() * 30

        def cc(px, py, pz, yb=yb, yt=yt, sd=sd):
            k = (py - y - yb) / (yt - yb)
            g = mul(green, 0.7 + 0.5 * k)
            if snow > 0:
                s = smooth(0.2, 0.55, k + 0.25 * n3((px, py, pz), 1.6, sd)) * snow
                g = mix(g, mix(hexc("#b8c8e8"), hexc("#f2f6ff"), k), s)
            return g
        a.lathe((x, y, z), [(r, yb), (r * 0.92, yb + (yt - yb) * 0.08), (r * 0.5, yb + (yt - yb) * 0.4), (0.0, yt)], segs,
                "foliage_sway", cc, sm=False, cap=False, rough=0.16, seed=sd, phase=rng.random())
    a.sway_base = None


def crystal(a, base, d, L, r, col, material="crystal"):
    base, d = Vector(base), Vector(d).normalized()
    a.tube([base - d * r * 0.5, base + d * L * 0.8, base + d * L], [r * 0.85, r, 0.001], material,
           lambda i, p: mix(mul(col, 0.7), mix(col, (1, 1, 1), 0.25), i / 2), segs=6, sm=False)


def crystal_cluster(a, base, size, rng, cols, n=7, spread=0.7, up=Vector((0, 1, 0))):
    for k in range(n):
        an = rng.uniform(0, 2 * math.pi)
        tilt = spread * (0.15 + 0.85 * (k / n) ** 0.7) if k else 0.05
        d = (up + Vector((math.cos(an), 0, math.sin(an))) * math.tan(tilt)).normalized()
        L = size * rng.uniform(0.55, 1.0) * (1.0 if k == 0 else 0.8)
        r = L * rng.uniform(0.12, 0.17)
        off = Vector((math.cos(an), 0, math.sin(an))) * size * 0.12 * rng.random()
        crystal(a, Vector(base) + off, d, L, r, rng.choice(cols))


def lantern(a, c, s, col=hexc("#ffc070"), frame=hexc("#2a2420")):
    """A little glass lantern: a glowing core in a dark frame with a hood and a ring."""
    x, y, z = c
    a.blob((x, y, z), (s * 0.32, s * 0.42, s * 0.32), "lantern_glow", col, segs=7, rings=4, rough=0.0)
    for k in range(4):
        an = k * math.pi / 2 + math.pi / 4
        a.tube([(x + math.cos(an) * s * 0.36, y - s * 0.45, z + math.sin(an) * s * 0.36),
                (x + math.cos(an) * s * 0.36, y + s * 0.45, z + math.sin(an) * s * 0.36)], s * 0.035, "metal", frame, segs=3)
    a.lathe((x, y - s * 0.55, z), [(s * 0.45, 0), (s * 0.42, s * 0.1)], 6, "metal", frame)
    a.lathe((x, y + s * 0.45, z), [(s * 0.5, 0), (s * 0.12, s * 0.35), (0.0, s * 0.4)], 6, "metal", frame)
    a.lathe((x, y + s * 0.85, z), [(s * 0.1, 0), (s * 0.1, s * 0.12)], 5, "metal", frame, cap=False)


def cloud_puff(a, c, size, rng, top, bottom, n=7, sun=Vector((-1, 0.3, 0)), flat=0.55, rim=None, material="cloud",
               segs=10, rings=6):
    """A heap of puffs, white-lit on top and towards the sun, tinted in the shade below."""
    c = Vector(c)
    sun = sun.normalized()
    for k in range(n):
        if k == 0:
            off, r = Vector((0, 0, 0)), size
        else:
            an = rng.uniform(0, 2 * math.pi)
            off = Vector((math.cos(an) * size * rng.uniform(0.5, 1.1), rng.uniform(-0.15, 0.5) * size,
                          math.sin(an) * size * 0.5))
            r = size * rng.uniform(0.45, 0.8)
        p = c + off

        def cc(nx, ny, nz, q):
            k2 = smooth(-0.6, 0.9, ny * 0.8 + (nx * sun.x + nz * sun.z) * 0.5)
            col = mix(bottom, top, k2)
            if rim is not None:
                col = mix(col, rim, smooth(0.3, 1.0, nx * sun.x + nz * sun.z) * 0.6)
            return col
        a.blob(tuple(p), (r, r * flat, r * 0.8), material, cc, segs=segs, rings=rings, rough=0.18, nscale=1.0,
               seed=rng.random() * 50, cut=-0.3)


def mist_bank(a, c, w, h, col, segs=1):
    """A soft bank of mist: a camera-facing card (UV.y up), tinted by its vertex colour."""
    a.card(c, w, h, "mist", col)


def beam(a, top, bottom, w0, w1, col=(1, 1, 1)):
    """A shaft of light from top to bottom, turned to face the camera (UV.x across, UV.y from the source, 0..1)."""
    top, bottom = Vector(top), Vector(bottom)
    d = (bottom - top)
    mid = (top + bottom) / 2
    side = d.cross(CAM - mid).normalized()
    pts = [top - side * w0 / 2, top + side * w0 / 2, bottom + side * w1 / 2, bottom - side * w1 / 2]
    a.poly(pts, "beam", col, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])


def reflection(refl, x, y, z, wl, w, col, k=1.0, L=None):
    """A streak of light on water or ice under a light at (x, y, z), running towards the camera."""
    h = y - wl
    if h <= 0.05:
        return
    d = Vector((CAM.x - x, CAM.z - z)).normalized()
    p = Vector((-d.y, d.x))
    L = (L if L else min(1.2 + h * 1.4, 14.0)) * k
    w = max(w, 0.0016 * dist((x, y, z)))
    fx, fz = x + d.x * 0.1, z + d.y * 0.1
    yy = wl + 0.03
    refl.poly([(fx - p.x * w, yy, fz - p.y * w), (fx + p.x * w, yy, fz + p.y * w),
               (fx + d.x * L + p.x * w * 1.6, yy, fz + d.y * L + p.y * w * 1.6),
               (fx + d.x * L - p.x * w * 1.6, yy, fz + d.y * L - p.y * w * 1.6)], "reflect_glow", col, uvs=UV4)


def bank(a, h, col, z=-1.5, depth=-9.0, x0=-30.0, x1=50.0, n=80):
    """The ground's front edge under the level's floor: a rough face from the ground down out of view."""
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    prev = None
    for x in xs:
        top = h(x, z)
        zz = z + 0.25 * n2(x, 0, 0.7, 3)
        a_ = a.vert((x, depth, zz + 0.3))
        m_ = a.vert((x, top - 0.6 + 0.2 * n2(x, 1, 1.3), zz + 0.15 * n2(x, 5, 2.0)))
        b_ = a.vert((x, top, z - 0.05))
        if prev:
            pa, pm, pb, px = prev
            a.face([pa, a_, m_, pm], "ground", [col(px, depth), col(x, depth), col(x, top - 0.6), col(px, top - 0.6)],
                   out=(x, top - 3, z - 50), sm=True)
            a.face([pm, m_, b_, pb], "ground", [col(px, top - 0.6), col(x, top - 0.6), col(x, top), col(px, top)],
                   out=(x, top - 3, z - 50), sm=True)
        prev = (a_, m_, b_, x)


# ------------------------------------------------------------------ 0 Bluebell Glade

def bluebell_glade(sc):
    global AIR
    AIR = (hexc("#b0c8bc"), 0.0075, 22.0, 0.72)
    rng = random.Random(3300)

    def brook_xs(z):
        return 8.5 + 9.0 * smooth(-70.0, -3.0, z) + 1.6 * math.sin(z * 0.11 + 1.0) * smooth(-120, -20, z)

    def brook_w(z):
        return 0.8 + 2.6 * smooth(-90.0, -4.0, z)

    def base_h(x, z):
        xs = xs_of(x, z)
        side = smooth(3.0, 15.0, abs(xs - 10.0))
        rise = smooth(-14.0, -120.0, z) * (2.0 + 9.0 * side) + 1.2 * smooth(-40, -120, z)
        bump = 0.45 * fbm(x, z, 0.09, 3, 2) * smooth(-3.0, -12.0, z) + 1.6 * fbm(x, z, 0.03, 3, 7) * smooth(-25, -60, z)
        return -0.25 + rise + bump

    def ground(x, z):
        bx = sx(brook_xs(z), z)
        d = abs(x - bx)
        w = brook_w(z)
        return base_h(x, z) - 0.7 * smooth(w + 1.4, w * 0.5, d)

    def water_y(z):
        return base_h(sx(brook_xs(z), z), z) - 0.5

    def bells(x, z):
        return smooth(-0.1, 0.25, fbm(x, z, 0.07, 3, 11)) * smooth(-2.0, -6.0, z)

    grass_a, grass_b = hexc("#4e7a2e"), hexc("#7aa640")
    moss, blue = hexc("#3e6a2a"), hexc("#5650d0")

    def gcol(x, y, z, ny):
        c = mix(grass_a, grass_b, n2(x, z, 0.25, 4) * 0.5 + 0.5)
        c = mix(c, mix(blue, hexc("#7a6ae0"), n2(x, z, 1.3) * 0.5 + 0.5), bells(x, z) * 0.9)
        bx = sx(brook_xs(z), z)
        c = mix(c, moss, smooth(brook_w(z) + 1.8, brook_w(z) * 0.6, abs(x - bx)) * 0.8)
        c = mix(c, hexc("#5a4a32"), smooth(0.85, 0.6, ny) * 0.5)
        sun = 0.25 * smooth(0.2, 0.7, fbm(x * 0.6 + z * 0.3, z, 0.08, 2, 9))   # dappled sunlight
        return mix(c, hexc("#c8d870"), sun)
    land = sc.acc("mid_ground")
    land.terrain(-1.5, -170.0, 60, 90, ground, gcol, margin=1.35)
    fgb = sc.acc("fg_bank")
    bank(fgb, ground, lambda x, y: mix(hexc("#2a2018"), hexc("#4a3a26"), smooth(-3, 0, y)))
    for i in range(26):   # moss and stones along the bank's edge
        x = rng.uniform(-14, 34)
        rock(fgb, (x, ground(x, -1.7) - 0.15, -1.8), (rng.uniform(0.3, 0.7), rng.uniform(0.2, 0.4), 0.4), rng,
             hexc("#6a8a4a"), hexc("#4a4a40"), segs=6, rings=3)

    # the brook: a ribbon winding from the far trees to the right-hand side
    wat = sc.acc("mid_brook")
    zs = [-1.6 - (i / 40) ** 1.6 * 115 for i in range(41)]
    prev = None
    for z in zs:
        bx = sx(brook_xs(z), z)
        w = brook_w(z) + 0.5
        wy = water_y(z)
        row = [wat.vert((bx - w, wy, z)), wat.vert((bx, wy, z)), wat.vert((bx + w, wy, z))]
        if prev:
            for k in range(2):
                wat.face([prev[k], row[k], row[k + 1], prev[k + 1]], "water",
                         [(1.0 if k == 0 else 0.0, 0, 0), (1.0 if k == 0 else 0.0, 0, 0), (1.0 if k == 1 else 0.0, 0, 0),
                          (1.0 if k == 1 else 0.0, 0, 0)], out=(bx, wy - 100, z))
        prev = row
    stones = sc.acc("mid_stones")
    for z in zs[2:30]:
        for s in (-1, 1):
            if rng.random() < 0.6:
                bx = sx(brook_xs(z), z) + s * (brook_w(z) + rng.uniform(0.2, 0.9))
                r = rng.uniform(0.25, 0.6) * (1 + 0.01 * -z)
                rock(stones, (bx, water_y(z) + 0.1, z), (r * 1.3, r * 0.6, r), rng, hexc("#8a8a7a"), hexc("#4a4c44"),
                     segs=6, rings=3)
    # stepping stones across it, near
    for k in range(4):
        z = -7.0 - k * 0.2
        bx = sx(brook_xs(z), z) - 2.4 + k * 1.6
        rock(stones, (bx, water_y(z) + 0.05, z - k * 0.6), (0.55, 0.3, 0.45), rng, hexc("#9a9a88"), hexc("#5a5a50"),
             segs=7, rings=3)

    # meadow life: grass, small bluebell clumps, little toadstools, ferns
    gr = sc.acc("mid_grass")

    def in_brook(x, z):
        return abs(x - sx(brook_xs(z), z)) < brook_w(z) + 0.6
    grass_patch(gr, rng, 1700, (-12, 32, -1.6, -9), ground, [hexc("#5a8a30"), hexc("#7aaa3a"), hexc("#4a7428"),
                hexc("#8ab84a")], h=(0.25, 0.7), avoid=in_brook)
    grass_patch(gr, rng, 1100, (-20, 40, -9, -26), ground, [hexc("#5a8a30"), hexc("#7aaa3a"), hexc("#6a9a3a")],
                h=(0.4, 0.9), w=0.08, avoid=in_brook)
    fl = sc.acc("mid_bluebells")
    for i in range(240):
        z = -rng.uniform(2.5, 34.0) ** 1.0
        x = rng.uniform(sx(-6, z), sx(26, z))
        if in_brook(x, z) or bells(x, z) < 0.25:
            continue
        y = ground(x, z)
        fl.sway_base = y
        h = rng.uniform(0.35, 0.65)
        fl.tube([(x, y, z), (x + 0.05, y + h, z), (x + 0.14, y + h * 0.9, z)], 0.02, "flower_sway", hexc("#4a7a3a"), segs=3)
        for k in range(3):
            q = (x + 0.04 + k * 0.05, y + h * (0.88 - k * 0.12), z)
            fl.lathe(q, [(0.07, -0.13), (0.05, -0.06), (0.015, 0.0)], 5, "flower_sway",
                     mix(blue, hexc("#9a90f0"), rng.random()), sm=True)
    fl.sway_base = None
    tl = sc.acc("mid_toadstools")
    for i in range(18):
        z = -rng.uniform(4.0, 30.0)
        xs = rng.choice((rng.uniform(-6, 2), rng.uniform(17, 26), rng.uniform(2, 17)))
        x = sx(xs, z)
        if in_brook(x, z):
            continue
        r = rng.uniform(0.25, 0.6)
        toadstool(tl, (x, ground(x, z), z), r * rng.uniform(1.0, 1.6), r, hexc("#d03a2a") if rng.random() < 0.7 else
                  hexc("#c8783a"), rng, segs=10)
    fe = sc.acc("mid_ferns")
    for i in range(22):
        z = -rng.uniform(5.0, 40.0)
        xs = rng.choice((rng.uniform(-6, 1), rng.uniform(19, 26)))
        x = sx(xs, z)
        fern(fe, (x, ground(x, z) - 0.1, z), rng.uniform(1.0, 2.0), rng, hexc("#4a8a32"))

    # trees: the mid wood at the sides, a lighter, hazier wood behind the middle, the far forest wall
    tr = sc.acc("mid_trees")
    lv = sc.acc("mid_leaves")
    placed = []
    for i in range(46):
        for _ in range(30):
            z = -rng.uniform(14.0, 95.0)
            xs = rng.uniform(-8.0, 28.0)
            c = abs(xs - 10.0) < 8.0
            if c and z > -45.0:
                continue
            x = sx(xs, z)
            if in_brook(x, z) or abs(x - sx(brook_xs(z), z)) < brook_w(z) + 2.5:
                continue
            if any((x - q[0]) ** 2 + (z - q[1]) ** 2 < 40 for q in placed):
                continue
            break
        else:
            continue
        placed.append((x, z))
        h = rng.uniform(24, 34)
        broadleaf(tr, lv, (x, ground(x, z), z), h, rng.uniform(0.6, 1.1), rng, hexc("#6a5440"),
                  mix(hexc("#4a7a2a"), hexc("#6a9a34"), rng.random()), branches=2, roots=z > -40, segs=6,
                  crown_r=rng.uniform(5, 7))
    # the far forest wall: trunks and crowns in the haze
    far = sc.acc("far_forest")
    for i in range(110):
        z = -rng.uniform(100.0, 165.0)
        x = rng.uniform(sx(-12, z), sx(32, z))
        y = ground(x, z)
        h = rng.uniform(20, 32)
        far.tube([(x, y - 1, z), (x, y + h * 0.7, z)], [0.9, 0.5], "bark", hexc("#3a4a3a"), segs=4)
        g = mix(hexc("#3a6a34"), hexc("#5a8a40"), rng.random())
        far.sway_base = y
        for k in range(2):
            r = rng.uniform(5, 8)
            far.blob((x + rng.uniform(-2, 2), y + h * (0.65 + 0.2 * k), z), (r, r * 0.8, r * 0.8), "foliage_sway",
                     lambda nx, ny, nz, q, g=g: mix(mul(g, 0.6), g, smooth(-0.5, 0.9, ny)), segs=7, rings=4, rough=0.3,
                     seed=rng.random() * 30)
        far.sway_base = None
    ridge = sc.acc("far_hills")
    for k, (z, base, amp, c) in enumerate(((-180.0, 18.0, 14.0, "#7a9a8a"), (-200.0, 24.0, 20.0, "#8aa8a0"))):
        xs_ = [sx(-14, z) + i * (sx(34, z) - sx(-14, z)) / 70 for i in range(71)]
        ridge.ridge(xs_, z, -2.0, lambda x, z=z, base=base, amp=amp, k=k: base + amp * (0.5 + 0.5 * fbm(x, z, 0.012, 3,
                    40 + k)), lambda x, y, c=c: hexc(c), material="ground")

    # the canopy overhead: leaf masses along the top, thick at the corners, opening over the middle
    can = sc.acc("mid_canopy")
    can.sway_base = 14.0
    for i in range(70):
        z = -rng.uniform(8.0, 45.0)
        xs = rng.uniform(-7.0, 27.0)
        ctr = smooth(9.0, 3.0, abs(xs - 10.5))
        if rng.random() < ctr * 0.85:
            continue
        ys = rng.uniform(15.0, 18.5) + ctr * 1.5
        x, y = sx(xs, z), sy(ys, z)
        r = rng.uniform(3.0, 5.5) * (1 + 0.012 * -z)
        g = mix(hexc("#3a6a26"), hexc("#7aa83a"), rng.random())

        def cc(nx, ny, nz, q, g=g):
            return mix(mul(g, 0.5), mix(g, hexc("#d8e870"), 0.35), smooth(-0.4, 0.9, -nx * 0.6 + ny * 0.5 + 0.3))
        can.blob((x, y, z), (r, r * 0.6, r * 0.8), "foliage_sway", cc, segs=9, rings=5, rough=0.35, nscale=1.2,
                 seed=rng.random() * 30)
    # ivy hanging from the canopy at the sides
    for i in range(16):
        z = -rng.uniform(6.0, 22.0)
        xs = rng.choice((rng.uniform(-6, 0.5), rng.uniform(19.5, 26)))
        x, y = sx(xs, z), sy(rng.uniform(15.5, 17.5), z)
        L = rng.uniform(3.0, 7.0)
        pts = [(x + 0.2 * math.sin(t * 2.0), y - L * t / 6, z) for t in range(7)]
        can.sway_base = y - L - 2
        can.tube(pts, 0.04, "foliage_sway", hexc("#3a5a24"), segs=3)
        for t in range(1, 7):
            p = pts[t]
            s = rng.uniform(0.18, 0.3)
            can.blob((p[0] + rng.uniform(-0.15, 0.15), p[1], p[2]), (s, s * 0.7, s * 0.4), "foliage_sway",
                     mix(hexc("#4a7a2a"), hexc("#7aa83a"), rng.random()), segs=5, rings=2, rough=0.1)
    can.sway_base = None

    # sunbeams through the canopy gap, falling to the right
    bm = sc.acc("mid_beams")
    d = Vector((0.42, -1.0, 0.12)).normalized()
    for i in range(6):
        z = -rng.uniform(18.0, 50.0)
        xs = rng.uniform(0.0, 12.0)
        top = Vector((sx(xs, z), sy(17.5, z), z))
        L = (top.y - ground(top.x, z)) / -d.y
        w0 = rng.uniform(1.0, 2.6) * (1 + 0.01 * -z)
        beam(bm, top, top + d * L, w0, w0 * 1.7, mix((1, 0.92, 0.7), (1, 1, 0.9), rng.random()))
        sc.empty("sparkle_%d" % i, tuple(top + d * L * 0.6))
    # mist lying in the hollows far off
    ms = sc.acc("mid_mist")
    for i in range(10):
        z = -rng.uniform(40.0, 120.0)
        x = rng.uniform(sx(-6, z), sx(26, z))
        mist_bank(ms, (x, ground(x, z) + 1.0, z), rng.uniform(25, 50), rng.uniform(3, 6), hexc("#e8f0e0"))

    # a hawthorn in blossom on the left, mid-distance
    bl = sc.acc("mid_blossom")
    bx, bz = sx(-2.5, -24.0), -24.0
    ends = broadleaf(tr, bl, (bx, ground(bx, bz), bz), 11, 0.5, rng, hexc("#4a3a30"), hexc("#f8d4e2"), branches=4,
                     crown_r=2.6, blobs=6)
    sc.empty("petal_0", (bx + 2, ground(bx, bz) + 8, bz))

    # foreground left: the giant bluebells arching over, a ring of toadstools at their feet, ferns
    fgl = sc.acc("fg_bluebells")
    for (xs, z, H, lean, n) in ((-3.2, -4.5, 10.5, 1.0, 8), (-1.6, -6.5, 8.2, 1.0, 7), (-4.6, -3.2, 12.5, 0.7, 9),
                                (0.2, -9.0, 6.4, 0.8, 6)):
        x = sx(xs, z)
        bluebell(fgl, (x, ground(x, z), z), H, lean, rng, n=n, dz=0.5,
                 bell=mix(hexc("#5450d4"), hexc("#7a5ae0"), rng.random()))
    fgt = sc.acc("fg_toadstools")
    for (xs, z, h, r, col) in ((-2.4, -3.0, 2.6, 1.7, "#d42e22"), (-0.6, -2.4, 1.3, 0.9, "#e0402a"),
                               (-4.2, -4.0, 3.6, 2.3, "#c82a20"), (0.4, -3.6, 0.8, 0.55, "#e04a30")):
        x = sx(xs, z)
        toadstool(fgt, (x, ground(x, z), z), h, r, hexc(col), rng, lean=rng.uniform(-0.08, 0.08))
    for (xs, z) in ((-1.0, -3.4), (-5.0, -6.0), (1.2, -5.0)):
        x = sx(xs, z)
        fern(fgt, (x, ground(x, z) - 0.1, z), 2.0, rng, hexc("#4a8a2e"), n=8)
    sc.empty("butterfly_0", (sx(-1.0, -4), 4.5, -4.0))
    sc.empty("butterfly_1", (sx(21.5, -6), 3.5, -6.0))
    sc.empty("butterfly_2", (sx(6.0, -18), 2.5, -18.0))

    # foreground right: the old oak, its roots, a fairy door with a lit window, bracket fungi, toadstools
    fgr = sc.acc("fg_oak")
    lvr = sc.acc("fg_oak_leaves")
    ox, oz = sx(24.2, -7.0), -7.0
    oy = ground(ox, oz)
    bark = hexc("#6e5440")
    oak_moss = hexc("#5a7a32")
    pts = [(ox, oy - 1.0, oz), (ox - 0.4, oy + 4, oz), (ox - 0.4, oy + 8, oz), (ox - 0.3, oy + 12, oz - 0.2),
           (ox - 0.2, oy + 16, oz - 0.5), (ox - 0.6, oy + 20, oz - 0.8), (ox - 1.0, oy + 24, oz - 1)]
    fgr.tube(pts, [2.8, 2.4, 2.2, 2.0, 1.9, 1.75, 1.6], "bark",
             lambda i, p, q=None: mix(mix(mul(bark, 0.55), bark, 0.3 + 0.7 * n2(p[0], p[1], 0.5)), oak_moss,
                                      smooth(0.05, 0.35, n2(p[0] * 0.4, p[1] * 0.3, 1.0, 5)) * 0.7),
             segs=16, rough=0.14, seed=4.0, nscale=0.5)
    for k in range(7):   # buttress roots
        an = k * 0.9 + 1.6
        d2 = Vector((math.cos(an), 0, math.sin(an) * 0.8))
        fgr.tube([(ox, oy + 2.4, oz), (ox + d2.x * 2.8, oy + 0.4, oz + d2.z * 2.8), (ox + d2.x * 4.6, oy - 0.4, oz + d2.z * 4.0)],
                 [1.1, 0.7, 0.25], "bark", mul(bark, 0.85), segs=7, rough=0.15, seed=k)
    # the fairy door, facing the camera on the trunk's foot
    dx, dz = ox - 2.2, oz + 1.4
    fgr.box((dx, oy + 0.75, dz), (1.0, 1.5, 0.25), "wood", hexc("#6a3a24"))
    fgr.lathe((dx, oy + 1.5, dz), [(0.5, 0), (0.0, 0.5)], 8, "wood", hexc("#5a3020"), sx=1.0, sz=0.25)
    fgr.blob((dx, oy + 1.2, dz + 0.14), (0.16, 0.16, 0.04), "door_glow", (1, 1, 1), segs=8, rings=3, rough=0.0)
    fgr.blob((dx + 0.3, oy + 0.75, dz + 0.15), (0.06, 0.06, 0.06), "metal", hexc("#c8a040"), segs=5, rings=2)
    lantern(fgr, (dx + 0.8, oy + 1.6, dz + 0.3), 0.32)
    sc.empty("light_warm_0", (dx + 0.6, oy + 1.4, dz + 1.0))
    for k in range(4):   # bracket fungi up the trunk
        yy = oy + 4.5 + k * 2.6
        an = math.pi * (0.75 + 0.25 * k % 2)
        fgr.lathe((ox + math.cos(an) * 2.2, yy, oz + 0.8), [(0.9, 0), (0.8, 0.12), (0.0, 0.18)], 9, "cap",
                  hexc("#c89a5a"), sz=0.5)
    for (dxs, dz2, h, r) in ((-3.6, 0.8, 1.2, 0.8), (-4.3, 1.6, 0.7, 0.5), (-2.8, 2.5, 0.5, 0.35)):
        toadstool(fgr, (ox + dxs, ground(ox + dxs, oz + dz2), oz + dz2), h, r, hexc("#d8783a"), rng)
    for (dxs, dz2) in ((-5.5, 0.5), (-1.2, 3.0)):
        fern(fgr, (ox + dxs, ground(ox + dxs, oz + dz2) - 0.1, oz + dz2), 2.2, rng, hexc("#4a8a2e"), n=8)
    lvr.sway_base = 14.0
    for i in range(10):   # its crown at the top right
        r = rng.uniform(3.0, 4.5)
        p = (ox - rng.uniform(-1, 9), oy + rng.uniform(19, 23), oz - rng.uniform(0, 4))
        g = mix(hexc("#3a6a26"), hexc("#6a9a34"), rng.random())
        lvr.blob(p, (r, r * 0.6, r * 0.8), "foliage_sway", lambda nx, ny, nz, q, g=g: mix(mul(g, 0.45), mix(g,
                 hexc("#d8e870"), 0.3), smooth(-0.4, 0.9, -nx * 0.6 + ny * 0.5 + 0.3)), segs=9, rings=5, rough=0.35,
                 nscale=1.2, seed=rng.random() * 30)
    lvr.sway_base = None
    # a bough reaching over the top-left from a tree out of view
    fgl.tube([(sx(-7, -6), sy(13, -6), -6), (sx(-2, -6), sy(16.2, -6), -6.5), (sx(4, -6), sy(17.2, -6), -7)],
             [0.7, 0.45, 0.2], "bark", bark, segs=7)
    lv2 = sc.acc("fg_bough_leaves")
    lv2.sway_base = 12.0
    for i in range(9):
        t = rng.random()
        p = bez(Vector((sx(-7, -6), sy(13, -6), -6)), Vector((sx(-2, -6), sy(16.2, -6), -6.5)),
                Vector((sx(4, -6), sy(17.2, -6), -7)), t)
        r = rng.uniform(1.2, 2.2)
        g = mix(hexc("#3a6a26"), hexc("#7aa83a"), rng.random())
        lv2.blob(tuple(p + Vector((0, rng.uniform(-0.5, 0.5), 0))), (r, r * 0.6, r * 0.8), "foliage_sway",
                 lambda nx, ny, nz, q, g=g: mix(mul(g, 0.45), mix(g, hexc("#d8e870"), 0.3), smooth(-0.4, 0.9, -nx * 0.6 +
                                                                                                   ny * 0.5 + 0.3)),
                 segs=8, rings=4, rough=0.3, seed=rng.random() * 30)
    lv2.sway_base = None


# ------------------------------------------------------------------ 1 Mushroom Ring

def mushroom_ring(sc):
    global AIR
    AIR = (hexc("#3a3468"), 0.014, 12.0, 0.85)
    rng = random.Random(3301)
    RC, RR = Vector((10.5, 0, -17.0)), 6.2   # the ring's centre and radius
    GLOWS = [hexc("#58f0d8"), hexc("#7ad8ff"), hexc("#b088ff"), hexc("#ff8ad8"), hexc("#a0ffb0")]

    def ground(x, z):
        xs = xs_of(x, z)
        side = smooth(4.0, 16.0, abs(xs - 10.0))
        rise = smooth(-30.0, -130.0, z) * (2.5 + 6.0 * side) + 0.4 * smooth(-12, -40, z)
        return -0.25 + rise + 0.35 * fbm(x, z, 0.1, 3, 5) * smooth(-3, -10, z) + 1.4 * fbm(x, z, 0.035, 3, 3) * \
            smooth(-25, -70, z)

    def ringlight(x, z):
        d = math.hypot(x - RC.x, (z - RC.z))
        return math.exp(-((d - RR) ** 2) / 6.0) + 0.5 * math.exp(-d * d / 30.0)

    g1, g2 = hexc("#24402e"), hexc("#3a5a36")

    def gcol(x, y, z, ny):
        c = mix(g1, g2, n2(x, z, 0.3, 2) * 0.5 + 0.5)
        c = mix(c, hexc("#4a3a5a"), smooth(-30, -80, z) * 0.4)
        return mix(c, hexc("#4ab8a0"), min(1.0, ringlight(x, z)) * 0.55)
    land = sc.acc("mid_ground")
    land.terrain(-1.5, -170.0, 56, 84, ground, gcol, margin=1.35)
    fgb = sc.acc("fg_bank")
    bank(fgb, ground, lambda x, y: mix(hexc("#18141e"), hexc("#2a2a30"), smooth(-3, 0, y)))
    gr = sc.acc("mid_grass")
    grass_patch(gr, rng, 1800, (-12, 32, -1.6, -10), ground, [hexc("#2e5a3a"), hexc("#3a6a44"), hexc("#4a7a4a"),
                hexc("#5a6a8a")], h=(0.3, 0.9))
    grass_patch(gr, rng, 1200, (-20, 40, -10, -30), ground, [hexc("#2e5a3a"), hexc("#3a6a44"), hexc("#4a6a5a")],
                h=(0.5, 1.1), w=0.08)

    # the fairy ring: glowing mushrooms in a circle, a few lights in it, wisps rising
    ring = sc.acc("lm_ring")
    n = 34
    for k in range(n):
        an = k * 2 * math.pi / n + rng.uniform(-0.05, 0.05)
        x = RC.x + math.cos(an) * RR * rng.uniform(0.95, 1.05)
        z = RC.z + math.sin(an) * RR * rng.uniform(0.95, 1.05)
        r = rng.uniform(0.25, 0.5)
        toadstool(ring, (x, ground(x, z), z), r * rng.uniform(1.4, 2.2), r, rng.choice(GLOWS), rng, glow=True,
                  stem_col=hexc("#c8d8e0"), gill=hexc("#e8fff8"), spot_col=(1, 1, 1), segs=9, spots=rng.random() < 0.5,
                  lean=rng.uniform(-0.12, 0.12))
    for k in range(4):
        an = k * math.pi / 2 + 0.4
        sc.empty("light_glow_%d" % k, (RC.x + math.cos(an) * RR, ground(RC.x, RC.z) + 1.2, RC.z + math.sin(an) * RR))
    sc.empty("wisp_0", (RC.x, ground(RC.x, RC.z) + 0.6, RC.z))
    # small glowing mushrooms scattered about the meadow
    sm = sc.acc("mid_glowcaps")
    for i in range(40):
        z = -rng.uniform(4.0, 40.0)
        xs = rng.uniform(-6, 26)
        x = sx(xs, z)
        if abs(math.hypot(x - RC.x, z - RC.z) - RR) < 1.5:
            continue
        r = rng.uniform(0.12, 0.28)
        toadstool(sm, (x, ground(x, z), z), r * 1.8, r, rng.choice(GLOWS), rng, glow=True, stem_col=hexc("#b8c8d0"),
                  gill=hexc("#e8fff8"), spots=False, segs=7)

    # far hills: layered silhouettes, the lone tree on the hill under the rising moon
    far = sc.acc("far_hills")
    for k, (z, base, amp, c) in enumerate(((-120.0, 6.0, 9.0, "#2a2a52"), (-155.0, 10.0, 14.0, "#33335e"),
                                           (-190.0, 14.0, 22.0, "#3e3a6a"))):
        xs_ = [sx(-14, z) + i * (sx(34, z) - sx(-14, z)) / 80 for i in range(81)]
        far.ridge(xs_, z, -4.0, lambda x, z=z, base=base, amp=amp, k=k: base + amp * (0.5 + 0.5 * fbm(x, z, 0.014, 3,
                  60 + k)) * (0.55 + 0.6 * smooth(0, 1, abs(xs_of(x, z) - 10) / 14)),
                  lambda x, y, c=c: mix(hexc(c), mul(hexc(c), 0.7), smooth(20, -2, y)), material="ground")
    lx, lz = sx(17.0, -118.0), -118.0
    ly = 6.0 + 9.0 * (0.5 + 0.5 * fbm(lx, lz, 0.014, 3, 60)) * (0.55 + 0.6 * smooth(0, 1, abs(xs_of(lx, lz) - 10) / 14))
    lt = sc.acc("far_lonetree")
    broadleaf(lt, lt, (lx, ly - 0.5, lz), 14, 0.6, rng, hexc("#1a1a30"), hexc("#20203e"), branches=4, crown_r=3.4,
              roots=False, segs=5)
    # forest edges at the sides, mid-distance
    tr = sc.acc("mid_trees")
    lv = sc.acc("mid_leaves")
    for i in range(30):
        z = -rng.uniform(28.0, 90.0)
        xs = rng.choice((rng.uniform(-9, 1.5), rng.uniform(18.5, 29)))
        x = sx(xs, z)
        broadleaf(tr, lv, (x, ground(x, z), z), rng.uniform(14, 22), rng.uniform(0.5, 0.9), rng, hexc("#2a2430"),
                  mix(hexc("#2a4058"), hexc("#3a5a5a"), rng.random()), branches=3, roots=False, segs=5,
                  crown_r=rng.uniform(3.5, 5))
    # mist over the meadow, lit violet
    ms = sc.acc("mid_mist")
    for i in range(12):
        z = -rng.uniform(22.0, 110.0)
        x = rng.uniform(sx(-6, z), sx(26, z))
        mist_bank(ms, (x, ground(x, z) + 0.8, z), rng.uniform(25, 45), rng.uniform(2.5, 5), hexc("#8a7ac8"))
    # foreground left: a towering glowing mushroom and its brood, foxgloves
    fgl = sc.acc("fg_mushrooms")
    for (xs, z, h, r, c, lean) in ((-3.0, -5.0, 7.5, 3.0, GLOWS[0], 0.06), (-0.6, -3.0, 3.2, 1.3, GLOWS[3], -0.05),
                                   (-5.2, -3.0, 4.2, 1.7, GLOWS[2], 0.0), (0.6, -6.5, 1.8, 0.8, GLOWS[1], 0.0),
                                   (-1.6, -2.2, 1.2, 0.55, GLOWS[4], 0.0)):
        x = sx(xs, z)
        toadstool(fgl, (x, ground(x, z), z), h, r, c, rng, glow=True, stem_col=hexc("#c8d0e0"), gill=hexc("#f0fffa"),
                  spot_col=(1, 1, 1), lean=lean)
    sc.empty("light_glow_4", (sx(-3.0, -5.0), 6.0, -2.5))
    fx = sc.acc("fg_foxgloves")
    for (xs, z, H) in ((-4.6, -6.0, 5.0), (-3.8, -7.2, 6.2), (1.4, -8.0, 3.6), (-6.0, -4.5, 4.4)):
        x = sx(xs, z)
        y = ground(x, z)
        fx.sway_base = y
        fx.tube([(x, y, z), (x + 0.2, y + H, z)], [0.08, 0.03], "flower_sway", hexc("#3a5a3a"), segs=4)
        for k in range(12):
            t = 0.4 + 0.58 * k / 12
            r = 0.22 * (1 - 0.6 * k / 12) * H / 5
            an = k * 2.4
            q = (x + 0.2 * t + math.cos(an) * r * 0.9, y + H * t, z + math.sin(an) * r * 0.9)
            fx.lathe(q, [(r * 0.75, -r * 2.2), (r * 0.9, -r * 1.6), (r * 0.5, -r * 0.3), (0.06, 0)], 6, "flower_sway",
                     lambda px, py, pz, qy=q[1], r=r: mix(hexc("#e86ac8"), hexc("#7a2a7a"), smooth(-r * 2.2, 0, py - qy)))
        fx.sway_base = None
    grass_patch(fx, rng, 300, (sx(-7, -4), sx(1, -4), -2.0, -8.0), ground, [hexc("#3a6a44"), hexc("#4a7a4a")],
                h=(0.8, 2.0), w=0.1)
    grass_patch(fx, rng, 300, (sx(19, -4), sx(27, -4), -2.0, -8.0), ground, [hexc("#3a6a44"), hexc("#4a7a4a")],
                h=(0.8, 2.0), w=0.1)
    # foreground right: an old gnarled tree, lanterns hung from its boughs
    fgr = sc.acc("fg_oldtree")
    lvr = sc.acc("fg_oldtree_leaves")
    ox, oz = sx(24.5, -8.0), -8.0
    oy = ground(ox, oz)
    bark = hexc("#3a3040")
    trunk = [(ox, oy - 1, oz), (ox + 0.8, oy + 5, oz), (ox - 0.6, oy + 10, oz - 0.5), (ox - 0.2, oy + 15, oz - 1.0),
             (ox + 1.0, oy + 22, oz - 1.5)]
    fgr.tube(trunk, [2.0, 1.5, 1.3, 1.1, 0.9], "bark", lambda i, p: mix(mul(bark, 0.6), bark, n2(p[0], p[1], 0.4) * 0.5 +
             0.5), segs=12, rough=0.2, seed=2.0)
    for k in range(5):
        an = k * 1.1 + 1.5
        d2 = Vector((math.cos(an), 0, math.sin(an) * 0.8))
        fgr.tube([(ox, oy + 1.8, oz), (ox + d2.x * 2.4, oy + 0.3, oz + d2.z * 2.4), (ox + d2.x * 3.8, oy - 0.4, oz + d2.z * 3.4)],
                 [0.8, 0.5, 0.2], "bark", mul(bark, 0.8), segs=6, rough=0.15, seed=k)
    boughs = [[(ox - 0.5, oy + 11, oz - 0.5), (ox - 5, oy + 13.5, oz - 0.8), (ox - 9.5, oy + 13.0, oz - 1.2),
               (ox - 13, oy + 14.4, oz - 1.5)],
              [(ox - 0.2, oy + 15.5, oz - 1), (ox - 4, oy + 18, oz - 1.5), (ox - 9, oy + 18.5, oz - 2)]]
    for b in boughs:
        fgr.tube(b, [0.7, 0.45, 0.3, 0.15][:len(b)], "bark", bark, segs=7, rough=0.15)
    si = 0
    for b, ts in ((boughs[0], (0.35, 0.7, 0.95)), (boughs[1], (0.6,))):
        for t in ts:
            k = t * (len(b) - 1)
            i0 = min(int(k), len(b) - 2)
            p = Vector(b[i0]).lerp(Vector(b[i0 + 1]), k - i0)
            L = rng.uniform(1.0, 2.2)
            sw = sc.acc("swing_%d" % si, tuple(p))
            sw.tube([p, p - Vector((0, L, 0))], 0.025, "metal", hexc("#1a1418"), segs=3)
            lantern(sw, (p.x, p.y - L - 0.4, p.z), 0.6)
            sc.empty("light_warm_%d" % si, (p.x, p.y - L - 0.5, p.z + 0.6))
            si += 1
    lvr.sway_base = 12.0
    for i in range(12):
        b = boughs[i % 2]
        p = Vector(b[rng.randint(1, len(b) - 1)])
        r = rng.uniform(1.6, 2.8)
        g = mix(hexc("#1e3a3a"), hexc("#2e4e44"), rng.random())
        lvr.blob(tuple(p + Vector((rng.uniform(-1.5, 1.5), rng.uniform(0, 1.5), rng.uniform(-1, 0.5)))), (r, r * 0.6, r * 0.8),
                 "foliage_sway", lambda nx, ny, nz, q, g=g: mix(mul(g, 0.5), mix(g, hexc("#6a5aa0"), 0.3), smooth(-0.5, 0.9, ny)),
                 segs=8, rings=4, rough=0.35, seed=rng.random() * 30)
    lvr.sway_base = None
    for i in range(6):
        sc.empty("firefly_%d" % i, (rng.uniform(sx(-4, -10), sx(24, -10)), rng.uniform(1.0, 4.0), -rng.uniform(5.0, 25.0)))


# ------------------------------------------------------------------ 2 Crystal Grotto

def crystal_grotto(sc):
    global AIR
    AIR = (hexc("#1a2450"), 0.02, 14.0, 0.8)
    rng = random.Random(3302)
    PC, PRX, PRZ = Vector((10.0, 0, -22.0)), 8.5, 7.0    # the pool
    BACK = -58.0
    CRY = [hexc("#7ae8ff"), hexc("#b07aff"), hexc("#ff7ad8"), hexc("#7affc8")]

    def pool_d(x, z):
        return math.hypot((x - PC.x) / PRX, (z - PC.z) / PRZ)

    def floor(x, z):
        xs = xs_of(x, z)
        side = smooth(8.0, 18.0, abs(xs - 10.0))
        h = -0.3 + 1.6 * fbm(x, z, 0.08, 3, 2) * smooth(-3, -12, z) + side * 3.0 * smooth(-4, -30, z)
        h += 2.5 * smooth(-35, -70, z)
        h -= 1.6 * smooth(1.15, 0.8, pool_d(x, z))
        return h

    def ceil(x, z):
        xs = xs_of(x, z)
        c = abs(xs - 10.0)
        top = 19.5 + 4.0 * smooth(-5, -50, z) + 3.0 * fbm(x, z, 0.06, 3, 8)
        return top - 26.0 * smooth(12.0, 26.0, c) ** 1.3

    def fcol(x, y, z, ny):
        c = mix(hexc("#342c52"), hexc("#4a4070"), n2(x, z, 0.4, 3) * 0.5 + 0.5)
        c = mix(c, hexc("#221e36"), smooth(0.8, 0.5, ny) * 0.6)
        c = mix(c, hexc("#8a5ab8"), math.exp(-((x - sx(-3.0, -4.5)) ** 2 + (z + 4.5) ** 2) / 30.0) * 0.6)
        c = mix(c, hexc("#4aa8b8"), math.exp(-((x - sx(23.8, -5.0)) ** 2 + (z + 5.0) ** 2) / 30.0) * 0.6)
        pd = pool_d(x, z)
        return mix(c, hexc("#3ab8c8"), math.exp(-((pd - 1.0) ** 2) * 6.0) * 0.6)
    fl = sc.acc("mid_floor")
    fl.terrain(-1.5, BACK - 2, 50, 70, floor, fcol, margin=1.35)
    fgb = sc.acc("fg_bank")
    bank(fgb, floor, lambda x, y: mix(hexc("#120e1c"), hexc("#2a2440"), smooth(-3, 0, y)))

    def ccol(x, y, z, ny):
        return mix(hexc("#2a2444"), hexc("#463a66"), n2(x, y, 0.3, 6) * 0.5 + 0.5)
    ce = sc.acc("mid_ceiling")
    ce.terrain(-1.5, BACK - 2, 46, 70, ceil, ccol, material="rock", margin=1.35, down=True)
    # the back wall, with an arch through to the far chamber
    wall = sc.acc("mid_backwall")
    AX, AY, AW, AH = 11.0, 0.0, 9.5, 12.5
    nx_, ny_ = 112, 56
    grid = []
    for j in range(ny_ + 1):
        row = []
        for i in range(nx_ + 1):
            x = -60 + 140 * i / nx_
            y = -5 + 40 * j / ny_
            dd = math.hypot((x - AX) / AW, (y - AY) / AH)
            z = BACK + 6.0 * fbm(x, y, 0.06, 4, 4) + 2.5 * abs(n2(x * 0.3, y, 0.4, 9)) - 6.0 * smooth(1.5, 1.0, dd)
            if dd < 1.0:   # inside the arch: pulled out onto its rim and back, so the opening is a smooth tunnel
                k = 1.0 / max(dd, 1e-3)
                x, y = AX + (x - AX) * k, AY + (y - AY) * k
                z = BACK - 6.0 - 6.0 * (1.0 - dd)
            row.append((wall.vert((x, y, z)), dd))
        grid.append(row)
    for j in range(ny_):
        for i in range(nx_):
            es = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            if all(e[1] < 0.97 for e in es):
                continue
            cols = [mix(mix(hexc("#3a3466"), hexc("#5a4e88"), n2(wall.v[e[0]].x, wall.v[e[0]].y, 0.15, 2) * 0.5 + 0.5),
                        hexc("#5ad0e8"), smooth(1.9, 0.98, e[1]) * 0.85) for e in es]
            p = wall.v[es[0][0]]
            wall.face([e[0] for e in es], "rock", cols, out=(p.x, p.y, p.z - 100), sm=True)
    # the far chamber beyond the arch: a glowing crystal heart, haze
    fc = sc.acc("lm_chamber")
    fc.terrain(BACK - 2, -105, 10, 30, lambda x, z: 1.0, lambda x, y, z, ny: (0.9, 0, 0), material="pool", margin=0.4)
    fc.ridge([AX - 40 + i * 2 for i in range(41)], -100, -2, lambda x: 30, lambda x, y: mix(hexc("#2a6a8a"),
             hexc("#1a1840"), smooth(0, 18, y + 3 * n2(x, 0, 0.2))))
    crystal_cluster(fc, (AX + 1, 0.5, -78), 11.0, rng, [hexc("#9af4ff"), hexc("#c8a8ff")], n=11, spread=0.6)
    crystal_cluster(fc, (AX - 7, 0.5, -70), 5.0, rng, [hexc("#7ae8ff"), hexc("#b07aff")], n=7)
    crystal_cluster(fc, (AX + 8, 0.5, -68), 4.5, rng, [hexc("#ff9ae8"), hexc("#7ae8ff")], n=6)
    sc.empty("light_cool_4", (AX, 6.0, BACK - 4))
    for k in range(10):   # crystals round the arch
        an = math.pi * (0.05 + 0.9 * k / 9)
        p = (AX + math.cos(an) * AW * 0.98, AY + math.sin(an) * AH * 0.97, BACK - 2.0)
        crystal_cluster(fc, p, rng.uniform(1.0, 2.2), rng, [CRY[0], CRY[1], CRY[3]], n=4,
                        up=Vector((math.cos(an), math.sin(an), 0.4)).normalized())
    ms = sc.acc("mid_mist")
    mist_bank(ms, (AX, 6.0, -95.0), 50, 26, hexc("#5ad8f8"))
    mist_bank(ms, (AX, 3.0, BACK - 10), 26, 8, hexc("#8ae8ff"))
    for i in range(6):
        z = -rng.uniform(25.0, 52.0)
        x = rng.uniform(sx(-4, z), sx(24, z))
        mist_bank(ms, (x, floor(x, z) + 0.8, z), rng.uniform(18, 30), rng.uniform(2, 3.5), hexc("#6a8ac8"))
    # the pool
    pl = sc.acc("mid_pool")
    rows = 16
    prev = None
    for i in range(rows + 1):
        z = PC.z + PRZ * 1.12 - 2 * PRZ * 1.12 * i / rows
        row = []
        for j in range(25):
            x = PC.x - PRX * 1.15 + 2 * PRX * 1.15 * j / 24
            row.append((pl.vert((x, -0.9, z)), min(1.0, max(0.0, pool_d(x, z) - 0.55) * 2.2)))
        if prev:
            for j in range(24):
                es = [prev[j], row[j], row[j + 1], prev[j + 1]]
                if all(pool_d(pl.v[e[0]].x, pl.v[e[0]].z) > 1.15 for e in es):
                    continue
                pl.face([e[0] for e in es], "pool", [(e[1], 0, 0) for e in es], out=(0, -100, z))
        prev = row
    sc.empty("light_cool_0", (PC.x, 0.4, PC.z))
    sc.empty("light_cool_1", (PC.x - 5, 0.4, PC.z + 2))
    sc.empty("light_cool_2", (PC.x + 5, 0.4, PC.z - 2))
    # stalactites from the ceiling, stalagmites from the floor
    st = sc.acc("mid_stalactites")
    for i in range(130):
        z = -rng.uniform(3.0, 56.0)
        xs = rng.uniform(-8, 28)
        x = sx(xs, z)
        y = ceil(x, z)
        if y < sy(14.0, z) and abs(xs - 10) < 14:
            continue
        L = rng.uniform(1.0, 5.5) * (1.4 if abs(xs - 10) > 9 else 0.8)
        r = L * rng.uniform(0.12, 0.2)
        st.lathe((x, y - L, z), [(0.02, 0), (r * 0.35, L * 0.4), (r, L * 0.85), (r * 1.4, L + 0.6)], 6, "rock",
                 lambda px, py, pz: mix(hexc("#5a5070"), hexc("#2a2440"), smooth(y - L, y, py)), sm=True, rough=0.15,
                 seed=rng.random() * 9)
    for i in range(55):
        z = -rng.uniform(4.0, 60.0)
        xs = rng.choice((rng.uniform(-8, 3), rng.uniform(17, 28), rng.uniform(3, 17)))
        x = sx(xs, z)
        if pool_d(x, z) < 1.25:
            continue
        L = rng.uniform(0.6, 3.5) * (1.3 if abs(xs - 10) > 8 else 0.6)
        r = L * rng.uniform(0.2, 0.3)
        y = floor(x, z)
        st.lathe((x, y - 0.3, z), [(r, 0), (r * 0.6, L * 0.4), (r * 0.2, L * 0.9), (0.0, L)], 6, "rock",
                 lambda px, py, pz, y=y, L=L: mix(hexc("#3a3460"), hexc("#8a80b8"), smooth(y, y + L, py)), sm=True,
                 rough=0.15, seed=rng.random() * 9)
    for (xs, z) in ((-1.5, -30.0), (21.5, -34.0), (2.0, -48.0), (19.0, -50.0)):
        x = sx(xs, z)
        y0, y1 = floor(x, z) - 0.5, ceil(x, z) + 1.0
        r = rng.uniform(1.4, 2.0)
        st.lathe((x, y0, z), [(r * 1.8, 0), (r * 1.0, (y1 - y0) * 0.2), (r * 0.6, (y1 - y0) * 0.45), (r * 0.7, (y1 - y0) * 0.6),
                              (r * 1.2, (y1 - y0) * 0.85), (r * 2.2, y1 - y0)], 9, "rock",
                 lambda px, py, pz: mix(hexc("#4a4278"), hexc("#2a2448"), smooth(y0, y1, py) * 0.8 + 0.2 * n2(px, py, 0.8)),
                 rough=0.2, seed=rng.random() * 9)
    # glow-worms: threads hanging from the ceiling, a bead of light on each
    gw = sc.acc("mid_glowworms")
    for i in range(460):
        z = -rng.uniform(4.0, 56.0)
        xs = rng.uniform(-7, 27)
        x = sx(xs, z)
        y = ceil(x, z)
        if y < 3.0:
            continue
        L = rng.uniform(0.3, 2.2)
        s = max(0.05, 0.0016 * dist((x, y, z)))
        gw.box((x, y - L, z), (s, s * 1.3, s), "glowworm_glow", mix(hexc("#7aeaff"), hexc("#a0ffd0"), rng.random()))
        if z > -30 and rng.random() < 0.5:
            gw.ribbon([(x, y, z), (x, y - L, z)], 0.012, "rock", hexc("#4a6a80"))
    # crystals: big clusters framing the sides, smaller ones about the floor and walls
    cr = sc.acc("fg_crystals")
    for (xs, z, s, cols, n, up) in ((-3.2, -4.5, 7.5, [CRY[1], CRY[2]], 9, (0.35, 1, 0)), (-0.8, -3.0, 3.0, [CRY[1]], 5, (0.2, 1, 0.2)),
                                    (23.8, -5.0, 8.0, [CRY[0], CRY[3]], 9, (-0.35, 1, 0)), (21.2, -3.2, 2.8, [CRY[0]], 5, (-0.1, 1, 0.2)),
                                    (-5.0, -9.0, 5.0, [CRY[2], CRY[1]], 7, (0.2, 1, 0)), (25.5, -10.0, 5.5, [CRY[3], CRY[0]], 7, (-0.2, 1, 0))):
        x = sx(xs, z)
        crystal_cluster(cr, (x, floor(x, z) - 0.3, z), s, rng, cols, n=n, spread=0.75, up=Vector(up).normalized())
    sc.empty("light_magic_0", (sx(-3.0, -4.5), 3.0, -2.5))
    sc.empty("light_cool_3", (sx(23.6, -5.0), 3.0, -2.8))
    rk = sc.acc("fg_rocks")
    for (xs, z, r) in ((-4.5, -3.0, 2.8), (-6.5, -7.0, 4.0), (25.0, -3.5, 2.6), (27.0, -8.0, 4.4), (-2.0, -2.2, 1.3),
                       (22.4, -2.3, 1.4)):
        x = sx(xs, z)
        rock(rk, (x, floor(x, z) - 0.2, z), (r * 1.2, r * 0.8, r), rng, hexc("#4a4266"), hexc("#221e34"), segs=9, rings=5)
    mc = sc.acc("mid_crystals")
    for i in range(36):
        z = -rng.uniform(8.0, 60.0)
        xs = rng.choice((rng.uniform(-7, 2), rng.uniform(18, 27), rng.uniform(2, 18)))
        x = sx(xs, z)
        if pool_d(x, z) < 1.15:
            continue
        crystal_cluster(mc, (x, floor(x, z) - 0.2, z), rng.uniform(0.8, 2.6) * (1.6 if abs(xs - 10) > 8 else 1.0),
                        rng, CRY, n=rng.randint(3, 6))
    for i in range(18):   # crystals growing down from the ceiling
        z = -rng.uniform(6.0, 50.0)
        xs = rng.choice((rng.uniform(-7, 1), rng.uniform(19, 27)))
        x = sx(xs, z)
        crystal_cluster(mc, (x, ceil(x, z) + 0.3, z), rng.uniform(1.0, 2.6), rng, CRY, n=4, up=Vector((0, -1, 0)))
    # a crack in the ceiling: shafts of pale light falling into the pool
    bm = sc.acc("mid_beams")
    d = Vector((0.2, -1.0, 0.05)).normalized()
    for i in range(3):
        top = Vector((PC.x - 8 + rng.uniform(-1.0, 1.0), 24.0, PC.z - 3 + rng.uniform(-2, 2)))
        L = (top.y + 0.9) / -d.y
        w = rng.uniform(0.8, 1.8)
        beam(bm, top, top + d * L, w, w * 2.0, (0.75, 0.9, 1.0))
    for i in range(4):
        sc.empty("sparkle_%d" % i, (PC.x + rng.uniform(-6, 6), rng.uniform(1.5, 8), PC.z + rng.uniform(-4, 4)))
    sc.empty("wisp_0", (PC.x, 0.0, PC.z))


# ------------------------------------------------------------------ 3 Cloud Castle

def cloud_castle(sc):
    global AIR
    AIR = (hexc("#f0c4b8"), 0.0045, 40.0, 0.55)
    rng = random.Random(3303)
    SUN = Vector((-0.6, 0.1, -0.8)).normalized()
    top_c, low_c, rim_c = hexc("#fff6ea"), hexc("#7a5aa8"), hexc("#ffb060")

    def sea_h(x, z):
        return -2.4 - 2.0 * smooth(-10, -120, z) + 1.8 * fbm(x, z, 0.04, 4, 3) + 0.8 * fbm(x, z, 0.12, 2, 8)

    def scol(x, y, z, ny):
        k = smooth(-4.6, -1.0, y + 2.0 * smooth(-10, -120, z))
        c = mix(low_c, mix(hexc("#ffd0c0"), top_c, 0.4), k)
        c = mix(c, mul(low_c, 0.8), smooth(0.85, 0.55, ny) * (1 - k) * 0.7)
        side = smooth(-40, 80, -x)   # the sun side is warmer
        return mix(c, rim_c, side * 0.45 * k)
    sea = sc.acc("mid_cloudsea")
    sea.terrain(-1.5, -200.0, 56, 90, sea_h, scol, material="cloud", margin=1.35)
    # the bank under the level: a row of big puffs
    fgb = sc.acc("fg_bank")
    for i in range(22):
        x = -14 + i * 2.2 + rng.uniform(-0.5, 0.5)
        cloud_puff(fgb, (x, -2.6 + rng.uniform(-0.3, 0.3), -2.6), rng.uniform(1.6, 2.4), rng, top_c, low_c, n=3,
                   sun=SUN, rim=rim_c, segs=9, rings=5)
    # cloud towers on the horizon, lit from the sunset side
    fcl = sc.acc("far_clouds")
    for i in range(26):
        z = -rng.uniform(150.0, 195.0)
        x = rng.uniform(sx(-14, z), sx(34, z))
        s = rng.uniform(10, 20)
        cloud_puff(fcl, (x, sea_h(x, z) + s * 0.3, z), s, rng, mix(top_c, rim_c, 0.5), mix(low_c, hexc("#c08aa8"), 0.4),
                   n=5, sun=SUN, rim=hexc("#ff9a5a"), segs=9, rings=5)
    # drifting banks at the sides, mid-distance (the game slides them slowly)
    for k, (xs, z, s, ys) in enumerate(((-4.0, -40.0, 6.5, 3.0), (25.0, -55.0, 7.5, 5.0), (4.0, -90.0, 9.0, 4.0),
                                        (19.0, -120.0, 11.0, 6.5), (-6.0, -25.0, 4.0, 9.0))):
        x, y = sx(xs, z), sy(ys, z)
        d = sc.acc("drift_%d" % k, (x, y, z))
        cloud_puff(d, (x, y, z), s, rng, top_c, low_c, n=6, sun=SUN, rim=rim_c, flat=0.5)

    # the floating castle: an island of rock with a grassy top, a waterfall off its lip, towers with blue roofs
    CX, CZ = sx(18.6, -72.0), -72.0
    CY = sy(8.2, -72.0)
    isl = sc.acc("float_0", (CX, CY, CZ))
    R = 13.0

    def icol(px, py, pz):
        k = (py - CY) / 16.0
        return mix(mix(hexc("#5a3e62"), hexc("#b88a7a"), smooth(-1.0, 0.0, k)), hexc("#e8a878"),
                   smooth(0.0, 1.0, (CX - px) / R) * 0.35)
    isl.lathe((CX, CY - 16, CZ), [(0.3, 0), (R * 0.15, 2.0), (R * 0.3, 4.0), (R * 0.5, 6.5), (R * 0.65, 9.0), (R * 0.8, 11.5),
                                  (R * 0.92, 13.5), (R, 15.6), (R * 0.98, 16.0)],
              18, "rock", icol, rough=0.3, nscale=0.8, seed=3.0)
    isl.lathe((CX, CY, CZ), [(R * 1.0, -0.1), (R * 0.95, 0.5), (0.0, 0.7)], 14, "ground",
              lambda px, py, pz: hexc("#6aa040"), rough=0.08, seed=4.0)
    for i in range(14):   # hanging roots
        an = rng.uniform(0, 2 * math.pi)
        p = Vector((CX + math.cos(an) * R * 0.7, CY - 6, CZ + math.sin(an) * R * 0.7))
        isl.tube([p, p + Vector((0.3, -4, 0)), p + Vector((-0.2, -8, 0.2))], [0.3, 0.18, 0.05], "bark", hexc("#4a3a3a"),
                 segs=4)
    fx = CX - R * 0.85
    isl.poly([(fx - 1.2, CY + 0.2, CZ + 4), (fx + 0.4, CY + 0.2, CZ + 5), (fx + 0.6, CY - 40, CZ + 6), (fx - 2.5, CY - 40, CZ + 5)],
             "falls", (1, 1, 1), uvs=UV4)
    for k in range(5):   # trees on the island
        an = rng.uniform(0, 2 * math.pi)
        p = (CX + math.cos(an) * R * 0.75, CY + 0.5, CZ + math.sin(an) * R * 0.6)
        broadleaf(isl, isl, p, rng.uniform(4, 6), 0.25, rng, hexc("#4a3a3a"), hexc("#5a9a40"), branches=2, crown_r=1.6,
                  roots=False, segs=5)
    wall, roof, trim = hexc("#fbeedd"), hexc("#3a5ad8"), hexc("#e8d4b8")

    def tower(x, z, base, h, r, roof_h, windows=2):
        isl.lathe((x, base, z), [(r, 0), (r, h), (r * 1.15, h + 0.2), (r * 1.15, h + 0.8)], 12, "paint",
                  lambda px, py, pz: mix(mix(hexc("#c8a8c8"), wall, smooth(base, base + h, py)), hexc("#ffd8a8"),
                                         smooth(0.0, 1.0, (x - px) / r) * 0.5))
        isl.lathe((x, base + h + 0.8, z), [(r * 1.3, 0), (r * 0.9, roof_h * 0.35), (r * 0.4, roof_h * 0.75), (0.0, roof_h)], 12,
                  "roof", lambda px, py, pz: mix(mul(roof, 0.7), roof, smooth(0, roof_h, py - base - h)))
        top = base + h + 0.8 + roof_h
        isl.tube([(x, top, z), (x, top + 2.2, z)], 0.06, "metal", hexc("#c8a040"), segs=3)
        isl.poly([(x, top + 2.2, z), (x + 1.6, top + 1.9, z), (x, top + 1.6, z)], "paint", hexc("#e04a5a"))
        to = Vector((CAM.x - x, 0, CAM.z - z)).normalized()
        for k in range(windows):
            yy = base + h * (0.35 + 0.4 * k / max(1, windows - 1))
            p = Vector((x, yy, z)) + to * (r + 0.02)
            isl.box(tuple(p), (r * 0.35, r * 0.6, 0.1), "window_glow", (1, 1, 1), ry=math.atan2(to.x, to.z))
    by = CY + 0.4
    isl.box((CX, by + 3.5, CZ), (14, 7, 9), "paint", wall, cols=(mul(wall, 0.9), mul(wall, 0.92)))
    for i in range(8):   # crenellations along the front wall
        isl.box((CX - 6.3 + i * 1.8, by + 7.4, CZ + 4.3), (0.9, 0.8, 0.5), "paint", trim)
    isl.box((CX, by + 2.0, CZ + 4.55), (2.4, 4.0, 0.1), "wood", hexc("#6a3a2a"))
    isl.box((CX, by + 2.0, CZ + 4.62), (1.6, 2.4, 0.05), "window_glow", (1, 1, 1))
    tower(CX, CZ - 1.0, by + 7.0, 10.0, 2.6, 8.0, 3)
    tower(CX - 7.0, CZ + 3.5, by, 11.0, 1.8, 6.0)
    tower(CX + 7.0, CZ + 3.5, by, 10.0, 1.8, 6.0)
    tower(CX - 6.5, CZ - 4.0, by, 14.0, 1.5, 5.5)
    tower(CX + 6.0, CZ - 4.5, by, 15.5, 1.6, 6.0)
    tower(CX + 2.8, CZ - 2.0, by + 7.0, 5.0, 1.0, 4.0, 1)
    sc.empty("light_warm_0", (CX, by + 3, CZ + 7))
    # a little island on the left with a cottage and a tree, and stray rocks
    LX, LZ, LY = sx(0.5, -105.0), -105.0, sy(12.0, -105.0)
    li = sc.acc("float_1", (LX, LY, LZ))
    li.lathe((LX, LY - 8, LZ), [(0.2, 0), (2.5, 2.5), (5.2, 6.0), (6.0, 7.8), (5.8, 8.0)], 11, "rock",
             lambda px, py, pz: mix(hexc("#6a4a5a"), hexc("#a88a7a"), smooth(LY - 8, LY, py)), rough=0.25, seed=7.0)
    li.lathe((LX, LY, LZ), [(6.0, -0.1), (5.6, 0.4), (0.0, 0.5)], 11, "ground", hexc("#6aa040"), rough=0.08, seed=4.0)
    li.box((LX + 1.0, LY + 1.6, LZ), (3.2, 2.4, 2.6), "paint", hexc("#f0e0c8"))
    li.lathe((LX + 1.0, LY + 2.8, LZ), [(2.4, 0), (0.0, 2.2)], 4, "roof", hexc("#c04a4a"), sm=False, phase=math.pi / 4,
             sx=1.0, sz=0.9)
    li.box((LX + 1.0, LY + 1.6, LZ + 1.32), (0.6, 0.7, 0.05), "window_glow", (1, 1, 1))
    broadleaf(li, li, (LX - 2.5, LY + 0.3, LZ), 6.5, 0.3, rng, hexc("#4a3a3a"), hexc("#f0b8c8"), branches=3, crown_r=1.8,
              roots=False, segs=5)
    for k, (xs, ys, z, s) in enumerate(((7.0, 15.0, -140.0, 2.5), (23.0, 14.0, -50.0, 1.2), (-3.0, 6.5, -60.0, 1.6))):
        x, y = sx(xs, z), sy(ys, z)
        rk = sc.acc("float_%d" % (2 + k), (x, y, z))
        rk.lathe((x, y - s * 2.5, z), [(0.1, 0), (s * 0.5, s * 0.6), (s * 0.8, s * 1.2), (s * 1.1, s * 1.9), (s * 1.2, s * 2.3),
                                       (s * 1.1, s * 2.5)], 10, "rock",
                 lambda px, py, pz, y=y, s=s: mix(hexc("#6a4a6a"), hexc("#c89a88"), smooth(y - s * 2.5, y, py)),
                 rough=0.35, nscale=0.9, seed=k * 3.0)
        rk.lathe((x, y, z), [(s * 1.12, -0.05), (s * 0.9, s * 0.15), (0.0, s * 0.25)], 10, "ground", hexc("#7ab048"),
                 rough=0.1, seed=k)
    # foreground: big cloud banks in the lower corners, a high bank at the upper left
    fgc = sc.acc("fg_clouds")
    for (xs, ys, z, s, n) in ((-3.5, 1.0, -6.0, 3.8, 8), (-1.0, -0.5, -3.0, 2.2, 5), (24.0, 1.2, -6.5, 4.2, 8),
                              (21.5, -0.4, -3.5, 2.4, 5), (-4.5, 15.5, -9.0, 3.4, 6), (25.5, 16.5, -12.0, 3.8, 6)):
        x, y = sx(xs, z), sy(ys, z)
        cloud_puff(fgc, (x, y, z), s, rng, top_c, low_c, n=n, sun=SUN, rim=rim_c, flat=0.6)
    # a floating rock with a flowering tree in the upper left foreground
    fr = sc.acc("float_5", (sx(-2.5, -10), sy(12.0, -10), -10.0))
    x, y, z = sx(-2.5, -10), sy(12.0, -10), -10.0
    fr.lathe((x, y - 3.5, z), [(0.1, 0), (1.2, 1.6), (2.2, 3.0), (2.4, 3.5), (2.3, 3.6)], 9, "rock",
             lambda px, py, pz: mix(hexc("#6a4a5a"), hexc("#b89a8a"), smooth(y - 3.5, y, py)), rough=0.25, seed=2.0)
    fr.lathe((x, y + 0.1, z), [(2.4, -0.1), (2.2, 0.2), (0.0, 0.3)], 9, "ground", hexc("#7ab048"))
    broadleaf(fr, fr, (x + 0.4, y + 0.2, z), 4.5, 0.18, rng, hexc("#4a3a3a"), hexc("#ffc0d0"), branches=3, crown_r=1.3,
              roots=False, segs=5)
    for k in range(3):
        an = rng.uniform(0, 6.28)
        fr.tube([(x + math.cos(an) * 1.5, y - 1.5, z + math.sin(an)), (x + math.cos(an) * 1.6, y - 4.5, z + math.sin(an))],
                [0.08, 0.02], "bark", hexc("#4a3a3a"), segs=3)
    sc.empty("petal_0", (x + 0.5, y + 3.5, z))


# ------------------------------------------------------------------ 4 Winter Hollow

def winter_hollow(sc):
    global AIR
    AIR = (hexc("#22305a"), 0.014, 12.0, 0.85)
    rng = random.Random(3304)
    PC, PRX, PRZ = Vector((9.5, 0, -19.0)), 9.0, 5.5   # the frozen pond
    WL = -0.55

    def pond_d(x, z):
        return math.hypot((x - PC.x) / PRX, (z - PC.z) / PRZ)

    def ground(x, z):
        xs = xs_of(x, z)
        side = smooth(5.0, 16.0, abs(xs - 10.0))
        h = -0.2 + smooth(-26, -120, z) * (2.0 + 8.0 * side) + 0.5 * fbm(x, z, 0.08, 3, 2) * smooth(-3, -10, z)
        h += 1.5 * fbm(x, z, 0.03, 3, 6) * smooth(-20, -60, z)
        return h - 0.6 * smooth(1.2, 0.95, pond_d(x, z))

    def gcol(x, y, z, ny):
        c = mix(hexc("#c8d8f0"), hexc("#f0f6ff"), n2(x, z, 0.4, 2) * 0.5 + 0.5)
        c = mix(c, hexc("#8a9ac8"), smooth(0.9, 0.6, ny) * 0.6)
        return c
    land = sc.acc("mid_ground")
    land.terrain(-1.5, -170.0, 56, 84, ground, gcol, material="snow", margin=1.35)
    fgb = sc.acc("fg_bank")
    bank(fgb, ground, lambda x, y: mix(hexc("#6a7aa8"), hexc("#d8e4f8"), smooth(-2.5, 0, y)))
    # the pond, frozen; lantern posts round it, their light lying on the ice
    ice = sc.acc("mid_ice")
    refl = sc.acc("mid_reflections")
    rows = 14
    prev = None
    for i in range(rows + 1):
        z = PC.z + PRZ * 1.1 - 2 * PRZ * 1.1 * i / rows
        row = []
        for j in range(25):
            x = PC.x - PRX * 1.12 + 2 * PRX * 1.12 * j / 24
            row.append((ice.vert((x, WL, z)), min(1.0, max(0.0, pond_d(x, z) - 0.6) * 2.5)))
        if prev:
            for j in range(24):
                es = [prev[j], row[j], row[j + 1], prev[j + 1]]
                ice.face([e[0] for e in es], "ice", [(e[1], 0, 0) for e in es], out=(0, -100, z))
        prev = row
    posts = sc.acc("mid_posts")
    li = 0
    for k in range(6):
        an = math.pi * (0.1 + 0.8 * k / 5)
        x = PC.x + math.cos(an) * PRX * 1.12 * (1 if k % 2 else 1.05)
        z = PC.z - math.sin(an) * PRZ * 1.15
        y = ground(x, z)
        posts.tube([(x, y - 0.2, z), (x, y + 2.0, z)], 0.07, "wood", hexc("#3a2a24"), segs=4)
        posts.tube([(x, y + 2.0, z), (x + 0.35, y + 2.05, z)], 0.04, "wood", hexc("#3a2a24"), segs=3)
        lantern(posts, (x + 0.35, y + 1.6, z), 0.42)
        reflection(refl, x + 0.35, y + 1.6, z, WL, 0.18, hexc("#ffb060"), 1.0)
        if k in (0, 2, 3, 5):
            sc.empty("light_warm_%d" % li, (x + 0.35, y + 1.6, z + 0.4))
            li += 1
    # pines everywhere but the middle; the far forest; snowy mountains
    tr = sc.acc("mid_pines")
    for i in range(110):
        for _ in range(20):
            z = -rng.uniform(10.0, 110.0)
            xs = rng.uniform(-9.0, 29.0)
            if abs(xs - 10.0) < 7.5 and z > -40.0:
                continue
            x = sx(xs, z)
            if pond_d(x, z) < 1.3:
                continue
            break
        else:
            continue
        pine(tr, (x, ground(x, z), z), rng.uniform(8, 17), rng, mix(hexc("#1a3a3a"), hexc("#24483e"), rng.random()),
             snow=1.0, tiers=4, segs=7)
    far = sc.acc("far_pines")
    for i in range(170):
        z = -rng.uniform(110.0, 165.0)
        x = rng.uniform(sx(-14, z), sx(34, z))
        pine(far, (x, ground(x, z), z), rng.uniform(12, 20), rng, hexc("#1e3440"), snow=0.8, tiers=3, segs=5)
    mt = sc.acc("far_mountains")
    for k, (z, base, amp, c0, c1) in enumerate(((-175.0, 16.0, 26.0, "#5a6a9a", "#c8d4f0"),
                                                (-198.0, 26.0, 40.0, "#4a5a8a", "#aab8e0"))):
        xs_ = [sx(-14, z) + i * (sx(34, z) - sx(-14, z)) / 100 for i in range(101)]

        def top(x, z=z, base=base, amp=amp, k=k):
            u = fbm(x, z, 0.01, 4, 70 + k)
            return base + amp * (0.5 + 0.5 * u) * (0.6 + 0.5 * smooth(0, 1, abs(xs_of(x, z) - 10) / 14))
        mt.ridge(xs_, z, -4.0, top, lambda x, y, c0=c0, c1=c1, top=top: mix(hexc(c0), hexc(c1), smooth(top(x) - 14, top(x),
                 y) * (0.6 + 0.4 * n2(x, y, 0.15))), material="snow")
    # cottages in the far trees, windows lit
    ct = sc.acc("far_cottages")
    for (xs, z) in ((3.0, -95.0), (17.0, -100.0), (13.5, -125.0)):
        x = sx(xs, z)
        y = ground(x, z)
        ct.box((x, y + 1.6, z), (6, 3.2, 4.5), "wood", hexc("#5a3a2a"))
        ct.lathe((x, y + 3.2, z), [(4.6, 0), (0.0, 3.0)], 4, "snow", hexc("#e8f0ff"), sm=False, phase=math.pi / 4, sz=0.8)
        ct.box((x - 1.2, y + 1.6, z + 2.28), (1.0, 1.0, 0.05), "window_glow", (1, 1, 1))
        ct.box((x + 1.4, y + 1.6, z + 2.28), (1.0, 1.0, 0.05), "window_glow", (1, 1, 1))
        ct.box((x + 1.8, y + 4.6, z - 0.8), (0.8, 2.2, 0.8), "paint", hexc("#4a3a3a"))

    # the tree houses: two great trees, one each side, with round huts, lit windows, lanterns, a bridge between
    th = sc.acc("lm_treehouses")
    thl = sc.acc("lm_treehouse_snow")
    trees = [(sx(-0.8, -20.0), -20.0, 12.5), (sx(20.8, -24.0), -24.0, 13.5)]
    hut_tops = []
    bark = hexc("#4a3a34")
    for k, (x, z, hh) in enumerate(trees):
        y = ground(x, z)
        th.tube([(x, y - 0.5, z), (x + 0.3, y + hh, z), (x - 0.2, y + hh + 12, z)], [1.3, 1.0, 0.5], "bark",
                lambda i, p: mix(mul(bark, 0.6), bark, n2(p[0], p[1], 0.5) * 0.5 + 0.5), segs=10, rough=0.12)
        # the platform and the hut
        th.lathe((x, y + hh - 0.4, z), [(3.6, 0), (3.6, 0.4)], 12, "wood", hexc("#6a4a34"))
        thl.lathe((x, y + hh, z), [(3.65, 0), (3.5, 0.15), (0.0, 0.2)], 12, "snow", hexc("#eef4ff"))
        for j in range(8):   # struts
            an = j * math.pi / 4
            th.tube([(x + math.cos(an) * 0.9, y + hh - 3.2, z + math.sin(an) * 0.9),
                     (x + math.cos(an) * 3.2, y + hh - 0.4, z + math.sin(an) * 3.2)], 0.1, "wood", hexc("#4a3424"), segs=3)
        th.lathe((x, y + hh, z), [(2.4, 0), (2.4, 2.6)], 12, "wood",
                 lambda px, py, pz: mix(hexc("#7a5238"), hexc("#8a6040"), (math.atan2(pz - z, px - x) * 3) % 1.0))
        thl.lathe((x, y + hh + 2.6, z), [(3.1, 0), (2.4, 0.9), (1.0, 2.6), (0.0, 3.4)], 12, "snow",
                  lambda px, py, pz: mix(hexc("#a8b8e0"), hexc("#f4f8ff"), smooth(y + hh + 2.6, y + hh + 4, py)))
        to = Vector((CAM.x - x, 0, CAM.z - z)).normalized()
        for j, off in enumerate((-0.6, 0.7)):
            side = Vector((to.z, 0, -to.x))
            p = Vector((x, y + hh + 1.3, z)) + to * 2.42 + side * off * 1.4
            th.box(tuple(p), (0.75, 0.9, 0.08), "window_glow", (1, 1, 1), ry=math.atan2(to.x, to.z))
        sc.empty("light_warm_%d" % (4 + k), (x + to.x * 3.5, y + hh + 1.4, z + to.z * 3.5))
        # a ladder down the trunk
        for j in range(int(hh / 0.6)):
            p = Vector((x, y + 0.3 + j * 0.6, z)) + to * 1.25
            th.box(tuple(p), (0.9, 0.08, 0.08), "wood", hexc("#5a3e2a"), ry=math.atan2(to.x, to.z))
        # snowy boughs above the hut
        pine(th, (x, y + hh + 5.5, z), 9.0, rng, hexc("#1e4038"), snow=1.0, tiers=3)
        hut_tops.append(Vector((x, y + hh + 0.1, z)))
        for j in range(2):   # lanterns hung from the platform's rim
            an = math.atan2(to.z, to.x) + (j - 0.5) * 1.2
            p = Vector((x + math.cos(an) * 3.3, y + hh - 0.4, z + math.sin(an) * 3.3))
            sw = sc.acc("swing_%d" % (k * 2 + j), tuple(p))
            sw.tube([p, p - Vector((0, 0.9, 0))], 0.02, "metal", hexc("#1a1418"), segs=3)
            lantern(sw, (p.x, p.y - 1.25, p.z), 0.5)
    # the rope bridge between them, lanterns along it
    A, B = hut_tops[0] + Vector((3.4, 0, 0)), hut_tops[1] + Vector((-3.4, 0, 0))
    n = 40
    for i in range(n):
        t0, t1 = i / n, (i + 0.8) / n
        p0 = A.lerp(B, t0) - Vector((0, 2.2 * 4 * t0 * (1 - t0), 0))
        p1 = A.lerp(B, t1) - Vector((0, 2.2 * 4 * t1 * (1 - t1), 0))
        th.box(tuple((p0 + p1) / 2), ((p1 - p0).length, 0.08, 1.2), "wood", hexc("#6a4a34"),
               ry=-math.atan2(p1.z - p0.z, p1.x - p0.x))
    for s in (-0.6, 0.6):
        pts = [A.lerp(B, t / 20) - Vector((0, 2.2 * 4 * (t / 20) * (1 - t / 20) - 1.0, -s)) for t in range(21)]
        th.tube(pts, 0.04, "wood", hexc("#5a4a3a"), segs=3)
    for i in range(1, 6):
        t = i / 6
        p = A.lerp(B, t) - Vector((0, 2.2 * 4 * t * (1 - t) - 1.0, 0.6))
        lantern(th, (p.x, p.y - 0.4, p.z), 0.35)
    # snow-laden firs framing the sides in the foreground
    fg = sc.acc("fg_firs")
    for (xs, z, h) in ((-5.0, -6.0, 24.0), (-1.8, -3.0, 7.0), (25.2, -7.0, 26.0), (22.0, -3.2, 6.5), (-7.5, -14.0, 22.0),
                       (28.0, -15.0, 24.0)):
        x = sx(xs, z)
        pine(fg, (x, ground(x, z), z), h, rng, mix(hexc("#1e4040"), hexc("#285048"), rng.random()), snow=1.0, tiers=6,
             segs=10, wf=0.7)
    sn = sc.acc("fg_drifts")
    for i in range(18):
        xs = rng.choice((rng.uniform(-6, 0.5), rng.uniform(19.5, 26)))
        z = -rng.uniform(2.0, 9.0)
        x = sx(xs, z)
        r = rng.uniform(0.8, 2.0)
        sn.blob((x, ground(x, z) - 0.2, z), (r * 1.6, r * 0.6, r), "snow", lambda nx, ny, nz, q: mix(hexc("#9aaad8"),
                hexc("#f4f8ff"), smooth(-0.2, 0.8, ny)), segs=9, rings=4, rough=0.15, cut=0.0)
    # mist over the pond and between the trees
    ms = sc.acc("mid_mist")
    for i in range(10):
        z = -rng.uniform(25.0, 110.0)
        x = rng.uniform(sx(-6, z), sx(26, z))
        mist_bank(ms, (x, ground(x, z) + 1.0, z), rng.uniform(25, 45), rng.uniform(3, 6), hexc("#7a8ac8"))
    for i in range(4):
        sc.empty("sparkle_%d" % i, (PC.x + rng.uniform(-7, 7), WL + 0.3, PC.z + rng.uniform(-3, 3)))


# ------------------------------------------------------------------ 5 Thorn Tower

def thorn_vine(a, pts, r0, rng, bark=hexc("#2a2228"), thorn=hexc("#4a3a3a"), roses=0, leaves=True, segs=6, every=0.6):
    """A briar: a woody tube along pts with thorns all along, a few leaves and roses."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    a.tube(pts, [r0 * (1 - 0.75 * i / (n - 1)) for i in range(n)], "bark", lambda i, p: mix(mul(bark, 0.7), bark,
           n2(p[0], p[1], 0.8) * 0.5 + 0.5), segs=segs, rough=0.1)
    L = sum((pts[i + 1] - pts[i]).length for i in range(n - 1))
    k = 0.0
    while k < L:
        s = k
        for i in range(n - 1):
            seg = (pts[i + 1] - pts[i]).length
            if s <= seg:
                p = pts[i].lerp(pts[i + 1], s / seg)
                t = (pts[i + 1] - pts[i]).normalized()
                rr = r0 * (1 - 0.75 * (i + s / seg) / (n - 1))
                ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
                an = rng.uniform(0, 6.28)
                o = (t.cross(ref).normalized() * math.cos(an) + t.cross(t.cross(ref)).normalized() * math.sin(an))
                a.spike(p + o * rr * 0.8, (o + t * 0.35), rr * 2.2 + 0.08, rr * 0.4 + 0.02, "bark", thorn)
                break
            s -= seg
        k += every * rng.uniform(0.6, 1.4) * max(0.4, r0 * 2)
    return L


def rose(a, c, s, rng, col=hexc("#a01830")):
    """A rose turned towards the viewer: cupped layers of scalloped petals, darker deep inside, and a few sepals."""
    c = Vector(c)
    ax = ((CAM - c).normalized() + Vector((0, 0.5, 0))).normalized()
    u = ax.cross(Vector((0, 1, 0))).normalized()
    v = ax.cross(u)
    segs = 15
    for k in range(4):
        R = s * (1.0 - 0.21 * k)
        npet = 5 if k < 2 else 3
        ph = k * 0.9 + rng.random()
        inner, h0, h1 = s * 0.12, -s * 0.3 + k * s * 0.1, s * (0.02 + 0.12 * k)
        ri, ro = [], []
        for j in range(segs):
            t = 2 * math.pi * j / segs
            d = u * math.cos(t) + v * math.sin(t)
            sc = 0.78 + 0.22 * abs(math.cos(npet * t / 2 + ph))
            ri.append(a.vert(c + ax * h0 + d * inner))
            ro.append(a.vert(c + ax * (h1 + 0.08 * s * sc) + d * R * sc))
        deep, lip = mul(col, 0.35 + 0.1 * k), mix(col, (1, 0.6, 0.65), 0.15 if k == 0 else 0.05)
        for j in range(segs):
            jj = (j + 1) % segs
            a.face([ri[j], ri[jj], ro[jj], ro[j]], "flower_sway", [deep, deep, lip, lip], sm=True, out=c - ax * s * 3)
    a.blob(tuple(c + ax * s * 0.25), (s * 0.18, s * 0.18, s * 0.18), "flower_sway", mul(col, 0.5), segs=5, rings=2, rough=0.1)
    for k in range(5):
        t = 2 * math.pi * k / 5 + rng.random()
        d = u * math.cos(t) + v * math.sin(t)
        a.spike(c - ax * s * 0.2 + d * s * 0.3, d * 1.0 - ax * 0.3, s * 0.9, s * 0.12, "flower_sway", hexc("#2a4a2a"))


def thorn_tower(sc):
    global AIR
    AIR = (hexc("#5a4462"), 0.011, 18.0, 0.8)
    rng = random.Random(3305)
    TX, TZ = sx(14.5, -78.0), -78.0

    def ground(x, z):
        xs = xs_of(x, z)
        side = smooth(4.0, 16.0, abs(xs - 10.0))
        h = -0.3 + smooth(-20, -120, z) * (2.0 + 9.0 * side) + 0.6 * fbm(x, z, 0.1, 3, 2) * smooth(-3, -10, z)
        h += 2.0 * fbm(x, z, 0.035, 3, 9) * smooth(-15, -50, z)
        d = math.hypot(x - TX, (z - TZ) * 1.2)
        h += 13.0 * smooth(26.0, 6.0, d)   # the crag the tower stands on
        return h

    def gcol(x, y, z, ny):
        c = mix(hexc("#2a2830"), hexc("#3a3440"), n2(x, z, 0.3, 4) * 0.5 + 0.5)
        c = mix(c, hexc("#2e3a2e"), smooth(0.1, 0.5, fbm(x, z, 0.12, 2, 3)) * smooth(0.7, 0.9, ny) * 0.6)
        return mix(c, hexc("#4a4048"), smooth(0.8, 0.55, ny) * 0.6)
    land = sc.acc("mid_ground")
    land.terrain(-1.5, -175.0, 56, 84, ground, gcol, margin=1.35)
    fgb = sc.acc("fg_bank")
    bank(fgb, ground, lambda x, y: mix(hexc("#120e14"), hexc("#2a2430"), smooth(-3, 0, y)))
    # the crag: tumbled rocks round the tower's foot
    cg = sc.acc("lm_crag")
    for i in range(30):
        an = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(4.0, 16.0)
        x, z = TX + math.cos(an) * d, TZ + math.sin(an) * d * 0.8
        r = rng.uniform(1.5, 4.0)
        rock(cg, (x, ground(x, z) - 0.5, z), (r * 1.2, r * 0.9, r), rng, hexc("#4a4250"), hexc("#221e28"), segs=7, rings=4)
    # the tower: a stout round base, a slender shaft, a jagged crown and a spire; briars wind up it
    tw = sc.acc("lm_tower")
    br = sc.acc("lm_briars")
    ty = ground(TX, TZ) - 1.0
    TS = 0.74   # the tower is built full size and scaled down about its foot
    stone = hexc("#3a3444")

    def scol(px, py, pz):
        b = math.floor((py - ty) / 0.9)
        k = (math.sin(b * 12.9 + math.floor(math.atan2(pz - TZ, px - TX) * 6 + (b % 2) * 0.5) * 7.3) * 0.5 + 0.5)
        return mix(mul(stone, 0.75), mul(stone, 1.15), k)
    prof = [(5.5, 0), (5.2, 8), (4.0, 10), (3.4, 12), (3.0, 26), (3.4, 27), (3.6, 30), (3.0, 30.5), (3.0, 34),
            (3.8, 34.5), (3.8, 35.5)]
    tw.lathe((TX, ty, TZ), prof, 14, "paint", scol, sm=False)
    for k in range(10):   # the crown's teeth
        an = k * 2 * math.pi / 10
        tw.box((TX + math.cos(an) * 3.6, ty + 36.4, TZ + math.sin(an) * 3.6), (0.8, 1.8, 0.8), "paint", stone, ry=-an)
    tw.lathe((TX, ty + 35.5, TZ), [(3.2, 0), (2.4, 3.0), (1.0, 8.0), (0.0, 13.0)], 10, "roof",
             lambda px, py, pz: mix(hexc("#2a2238"), hexc("#3a2e4a"), smooth(ty + 35, ty + 48, py)))
    tw.tube([(TX, ty + 48.5, TZ), (TX, ty + 51, TZ)], 0.08, "metal", hexc("#6a5a6a"), segs=3)
    # turrets on the base and a balcony
    for k in range(3):
        an = math.pi * (0.25 + 0.5 * k)
        x, z = TX + math.cos(an) * 5.3, TZ + math.sin(an) * 5.3
        tw.lathe((x, ty + 4, z), [(0.2, 0), (1.2, 1.5), (1.2, 7), (1.4, 7.2), (1.4, 7.6)], 8, "paint", stone)
        tw.lathe((x, ty + 11.6, z), [(1.6, 0), (0.0, 4.5)], 8, "roof", hexc("#2a2238"))
    # windows: one glowing violet high up, a warm one lower, the rest dark
    to = Vector((CAM.x - TX, 0, CAM.z - TZ)).normalized()
    ry = math.atan2(to.x, to.z)
    for (h, r, m, w) in ((31.8, 3.62, "magic_glow", (1.0, 1.6)), (20.0, 3.05, "window_glow", (0.7, 1.2)),
                         (6.0, 5.3, "rock", (1.2, 2.0)), (15.0, 3.1, "rock", (0.6, 1.1))):
        p = Vector((TX, ty + h, TZ)) + to * r
        tw.box(tuple(p), (w[0], w[1], 0.15), m, (1, 1, 1) if "glow" in m else hexc("#0a080c"), ry=ry)
    sc.empty("light_magic_0", tuple(Vector((TX, ty + 31.8 * TS, TZ)) + to * 6.0 * TS))
    sc.empty("light_warm_0", tuple(Vector((TX, ty + 20.0 * TS, TZ)) + to * 5.0 * TS))
    sc.empty("wisp_0", (TX, ty + 32.0 * TS, TZ))
    # briars wound up the tower
    for s in range(3):
        pts = []
        for i in range(60):
            t = i / 59
            h = t * 34.0
            rr = 0.25 + (5.6 if h < 8 else 3.3 if h > 12 else 5.6 - (h - 8) * 0.58)
            an = s * 2.1 + t * 9.0
            pts.append((TX + math.cos(an) * rr, ty + h, TZ + math.sin(an) * rr))
        thorn_vine(br, pts, 0.35, rng, every=1.4, segs=5)
    for i in range(10):
        an = rng.uniform(-0.8, 0.8) + math.atan2(to.z, to.x)
        h = rng.uniform(4, 30)
        rr = 3.5 if h > 12 else 5.7
        rose(br, (TX + math.cos(an) * rr, ty + h, TZ + math.sin(an) * rr), 0.7, rng)
    tw.scale_about((TX, ty, TZ), TS)
    br.scale_about((TX, ty, TZ), TS)
    # thickets: bramble tangles across the land, dead trees
    th = sc.acc("mid_brambles")
    for i in range(70):
        z = -rng.uniform(6.0, 70.0)
        xs = rng.choice((rng.uniform(-7, 3), rng.uniform(17, 27), rng.uniform(3, 17)))
        x = sx(xs, z)
        y = ground(x, z)
        for k in range(rng.randint(2, 4)):
            an = rng.uniform(0, 6.28)
            L = rng.uniform(1.5, 4.0) * (1.6 if abs(xs - 10) > 8 else 1.0)
            p0 = Vector((x, y - 0.2, z))
            p2 = p0 + Vector((math.cos(an) * L, 0.0, math.sin(an) * L * 0.5))
            p1 = (p0 + p2) / 2 + Vector((0, L * rng.uniform(0.4, 0.8), 0))
            thorn_vine(th, [bez(p0, p1, p2, t / 6) for t in range(7)], 0.08 + 0.02 * L, rng, every=1.2, segs=4)
    dt = sc.acc("mid_deadtrees")
    for i in range(22):
        z = -rng.uniform(15.0, 110.0)
        xs = rng.choice((rng.uniform(-9, 2), rng.uniform(18, 29)))
        x = sx(xs, z)
        y = ground(x, z)
        h = rng.uniform(8, 16)
        lean = rng.uniform(-0.15, 0.15)
        trunk = [(x, y - 0.5, z), (x + lean * h * 0.5, y + h * 0.5, z), (x + lean * h, y + h, z)]
        dt.tube(trunk, [h * 0.05, h * 0.035, h * 0.01], "bark", hexc("#2a2228"), segs=5)
        for k in range(4):
            t = rng.uniform(0.4, 0.9)
            p = Vector(trunk[0]).lerp(Vector(trunk[2]), t)
            an = rng.uniform(0, 6.28)
            e = p + Vector((math.cos(an) * h * 0.3, h * rng.uniform(0.1, 0.3), math.sin(an) * h * 0.15))
            m = (p + e) / 2 + Vector((0, h * 0.05, 0))
            dt.tube([p, m, e, e + Vector((math.cos(an) * h * 0.08, -h * 0.03, 0))], [h * 0.02, h * 0.012, h * 0.005, 0.01],
                    "bark", hexc("#2a2228"), segs=3)
    # a ruined wall and a gate on the path up to the tower
    rw = sc.acc("mid_ruins")
    for i in range(14):
        z = -40.0 - i * 0.2
        xs = -3.0 + i * 0.9
        x = sx(xs, z)
        hh = rng.uniform(0.8, 3.5) * (1.0 if i % 5 else 0.3)
        rw.box((x, ground(x, z) + hh / 2 - 0.3, z), (2.2, hh, 1.2), "rock", mul(hexc("#4a4250"), rng.uniform(0.8, 1.1)))
    # the far ridges under the storm
    far = sc.acc("far_ridges")
    for k, (z, base, amp, c) in enumerate(((-150.0, 10.0, 14.0, "#2a2232"), (-190.0, 16.0, 22.0, "#3a2a3a"))):
        xs_ = [sx(-14, z) + i * (sx(34, z) - sx(-14, z)) / 80 for i in range(81)]
        far.ridge(xs_, z, -4.0, lambda x, z=z, base=base, amp=amp, k=k: base + amp * (0.5 + 0.5 * fbm(x, z, 0.015, 4,
                  80 + k)) * (0.6 + 0.5 * smooth(0, 1, abs(xs_of(x, z) - 10) / 14)), lambda x, y, c=c: hexc(c),
                  material="rock")
    ms = sc.acc("mid_mist")
    for i in range(10):
        z = -rng.uniform(25.0, 110.0)
        x = rng.uniform(sx(-6, z), sx(26, z))
        mist_bank(ms, (x, ground(x, z) + 1.0, z), rng.uniform(25, 45), rng.uniform(3, 6), hexc("#6a5a7a"))
    # foreground: great briars arching in from both sides, roses on them
    fg = sc.acc("fg_briars")
    fr = sc.acc("fg_roses")
    arcs = [[(sx(-7, -5), -2.0, -5.0), (sx(-4, -5), 6, -5.5), (sx(-1, -5), 13, -6.0), (sx(3.5, -5), sy(16.8, -5), -6.5)],
            [(sx(-6, -3), -1.0, -3.5), (sx(-1.5, -3), 2.5, -3.5), (sx(1.5, -3), 1.0, -3.5), (sx(3.0, -3), -1.5, -3.5)],
            [(sx(27, -6), -2.0, -6.0), (sx(23.5, -6), 7, -6.5), (sx(21.5, -6), 13, -7.0), (sx(16.5, -6), sy(17.0, -6), -7.5)],
            [(sx(26, -3), -1.0, -3.2), (sx(22, -3), 3.2, -3.2), (sx(20.5, -3), 1.5, -3.2), (sx(19, -3), -1.5, -3.2)],
            [(sx(-6, -9), sy(9, -9), -9.0), (sx(-2.5, -9), sy(12, -9), -9.0), (sx(-6.5, -9), sy(16.5, -9), -9.0)],
            [(sx(27, -10), sy(10, -10), -10.0), (sx(23, -10), sy(12.5, -10), -10.0), (sx(26, -10), sy(17, -10), -10.0)]]
    for k, a in enumerate(arcs):
        P = [Vector(p) for p in a]
        pts = []
        for i in range(len(P) - 1):
            for j in range(6):
                t = j / 6
                pts.append(P[i].lerp(P[i + 1], t) + Vector((0, 0.6 * math.sin(t * math.pi) * (1 if i % 2 else -1), 0)))
        pts.append(P[-1])
        r0 = 0.32 if k in (0, 2) else 0.2
        thorn_vine(fg, pts, r0, rng, every=0.45, segs=7)
        for j in range(2 if k in (0, 2) else 1):
            p = pts[rng.randint(2, len(pts) - 3)]
            rose(fr, (p.x, p.y + 0.3, p.z + 0.4), 0.6, rng, col=hexc("#c01832"))
    for i in range(14):   # leaves on the foreground briars
        a = arcs[rng.choice((0, 2, 4, 5))]
        p = Vector(a[rng.randint(0, len(a) - 1)]) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0.3))
        fr.sway_base = p.y - 2
        fr.blob(tuple(p), (0.35, 0.15, 0.22), "flower_sway", hexc("#2a3a2a"), segs=5, rings=2, rough=0.1)
    fr.sway_base = None
    rk = sc.acc("fg_rocks")
    for (xs, z, r) in ((-4.2, -4.0, 1.8), (24.0, -4.5, 2.0), (-1.2, -2.4, 0.8), (21.0, -2.6, 0.9)):
        x = sx(xs, z)
        rock(rk, (x, ground(x, z) - 0.2, z), (r * 1.3, r * 0.7, r), rng, hexc("#4a4250"), hexc("#1e1a24"), segs=8, rings=4)


# ------------------------------------------------------------------ main

THEMES = [bluebell_glade, mushroom_ring, crystal_grotto, cloud_castle, winter_hollow, thorn_tower]


def main():
    global AIR
    for n, fn in enumerate(THEMES):
        if ONLY and n not in ONLY:
            continue
        AIR = None
        sc = Scene(n)
        fn(sc)
        sc.export()


main()
