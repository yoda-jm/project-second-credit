"""Jelly Spike (game 24) beach backdrop: one tropical beach diorama around the 16 m volleyball court.
Original design: an invented, generic beach (palms, striped huts, a lifeguard tower, a tiki bar, a bonfire); nothing
is taken from any other game. Deterministic (fixed seeds); output CC BY-SA 4.0; provenance: this script only (its
geometry helpers come from tools/blender/popvoyage_backdrops.py), no third-party assets, no textures (vertex colours).
Writes beach_scene.glb and critters.glb (the models for the occasional background events: see critters()).
Run: blender -b --factory-startup -P tools/blender/jellyspike_beach.py -- godot/games/jellyspike/art/beach

Coordinates: authored in Godot space (x right, y up, z towards the camera) and converted on export. The court is
x 0..16 on the sand (y = 0, flat within 2 cm on the court), the play plane z = 0, the net at x = 8 (top 2.4 m); the
camera sits near (8, 4.5, 20), fov 36. beach_scene.glb holds
  near_*    the sand (court tape, footprints, blob dimples), the net and its posts, props, palms, the swash strip:
            near things cast shadows
  far_*     the far land (headlands with jungle), the sea (to z -1300), islands, far palms
  cloud_<i> puffy clouds (the game drifts them along x), boat_<i> (bob)
  crab_<i>, gull_<i>  spectators, origin at their feet (the game animates them)
  flame_<i>, bonfire_flame  flames (the game shows them at dusk and night)
and empties: light_torch_<i>, light_fire, light_lantern_<i> (where the game puts lights), smoke_fire, score_board
(the centre of the blank scoreboard, turned to face the camera: the game writes the score there), perch_<i> (the tops
of the mooring posts, where a gull may land) and coco_<i> (palm crowns a coconut may fall from).
Material names carry the game's hints: "sand" (vertex colour, grain shader), "sea" (UV.y = metres out from the
waterline: the breakers are drawn from it), "swash" (UV = (x, run-up 0..1)), "net" (UV in metres: a grid shader),
"*_sway" (palm_sway, foliage_sway: UV.y = height above the plant's foot, palm fronds UV.x along the frond;
flag_sway: UV.x = distance from the pole; bunting_sway: UV.y = depth below the rope), "cloud", "*_glow"
(lantern_glow and bulb_glow paper lanterns lit at dusk, ember_glow, fire_glow: flames, UV.y up the flame),
"trunk_sway" (palm trunks: the game draws ring bark from UV.y), "wood" and "thatch" (UV = metres along the face's
longest edge and across it, written automatically: the game's grain shader), "fabric" (matte cloth), "gloss"
(surfboards, bottles, the bucket: glossy with a clear coat).
All other colour is in the vertex colours (COLOR_0, linear), over white materials.
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/jellyspike/art/beach")

CAM = Vector((8.0, 4.5, 20.0))
TAN_W = 0.578  # half-width per unit of distance for fov 36 at 16:9


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
    return TAN_W * (CAM.z - z) * margin + 6.0


# ------------------------------------------------------------------ materials

MATS = {}
MAT_DEFS = {}  # filled below (materials)
GRAIN_MATS = ("wood", "thatch")  # the game's wood shader reads UV = (along the grain, across)


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
        if uvs is None and material in GRAIN_MATS and len(ids) >= 3:
            # grain coordinates for the wood shader: UV.x along the face's longest edge (the grain), UV.y across it
            ps = [self.v[i] for i in ids]
            best, axis = -1.0, Vector((1, 0, 0))
            for k in range(len(ps)):
                e = ps[(k + 1) % len(ps)] - ps[k]
                if e.length > best:
                    best, axis = e.length, e.normalized()
            nrm = (ps[1] - ps[0]).cross(ps[2] - ps[0])
            across = nrm.cross(axis).normalized() if nrm.length > 1e-9 else Vector((0, 1, 0))
            uvs = [(p.dot(axis), p.dot(across)) for p in ps]
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

    def rbox(self, c, size, r, material, col, ry=0.0, rx=0.0, cols=None):
        """A box with chamfered edges (bevel r), turned by rx about X then ry about Y. cols: (top, sides)."""
        cx, cy, cz = c
        h = (size[0] / 2, size[1] / 2, size[2] / 2)
        r = min(r, h[0] * 0.9, h[1] * 0.9, h[2] * 0.9)
        cr, sr, cx_, sx_ = math.cos(ry), math.sin(ry), math.cos(rx), math.sin(rx)

        def T(p):
            x, y, z = p
            y, z = y * cx_ - z * sx_, y * sx_ + z * cx_
            return (cx + x * cr + z * sr, cy + y, cz - x * sr + z * cr)
        top, side = (cols if cols else (col, col))
        V = {}
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    for k in range(3):
                        q = [sx * (h[0] - r), sy * (h[1] - r), sz * (h[2] - r)]
                        q[k] = (sx, sy, sz)[k] * h[k]
                        V[(sx, sy, sz, k)] = self.vert(T(q))
        C = (cx, cy, cz)

        def colf(k, s):
            return top if (k == 1 and s > 0) else side
        for k in range(3):
            a1, a2 = [i for i in range(3) if i != k]
            for s in (-1, 1):
                quad = []
                for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    sg = [0, 0, 0]
                    sg[k], sg[a1], sg[a2] = s, u, v
                    quad.append(V[(sg[0], sg[1], sg[2], k)])
                self.face(quad, material, colf(k, s), out=C)
        for k1 in range(3):
            for k2 in range(k1 + 1, 3):
                k3 = 3 - k1 - k2
                for s1 in (-1, 1):
                    for s2 in (-1, 1):
                        ids = []
                        for s3, kk in ((-1, k1), (1, k1), (1, k2), (-1, k2)):
                            sg = [0, 0, 0]
                            sg[k1], sg[k2], sg[k3] = s1, s2, s3
                            ids.append(V[(sg[0], sg[1], sg[2], kk)])
                        up = (k1 == 1 and s1 > 0) or (k2 == 1 and s2 > 0)
                        self.face(ids, material, mix(top, side, 0.5) if up else side, out=C)
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    self.face([V[(sx, sy, sz, k)] for k in range(3)], material, top if sy > 0 else side, out=C)

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
            a = 8 - half_w(z, margin) if xl is None else xl(z)
            b = 8 + half_w(z, margin) if xr is None else xr(z)
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
                ca.data[poly.loop_start + k].color = (*c, 1.0)
                if f[3] and uv:
                    # glTF flips V on export (v -> 1 - v): pre-flip so the game reads the values written here
                    uv.data[poly.loop_start + k].uv = (f[3][k][0], 1.0 - f[3][k][1])
        me.color_attributes.active_color = ca
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (o.x, -o.z, o.y)
        return ob


class Scene:
    """The objects of one .glb, built and exported together."""

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
            e.rotation_euler = (0, 0, getattr(self, "empty_rot", {}).get(name, 0.0))
            objs.append(e)
        bpy.ops.object.select_all(action="DESELECT")
        for ob in objs:
            ob.select_set(True)
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, "%s.glb" % self.n)
        bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB", export_yup=True,
                                  export_apply=True, export_animations=False, export_vertex_color="ACTIVE",
                                  export_extras=False)
        print("exported %s  %6d tris  %d nodes" % (self.n, total, len(objs)))
        for a in sorted(self.accs, key=lambda a: -a.tris())[:6]:
            print("    %-20s %6d" % (a.name, a.tris()))
        for m in list(bpy.data.meshes):
            bpy.data.meshes.remove(m)
        for m in list(bpy.data.materials):
            bpy.data.materials.remove(m)
        MATS.clear()
        return total


# ------------------------------------------------------------------ shared props

def cloud(sc, name, c, size, rng, top=(1, 1, 1), under=(0.72, 0.78, 0.9)):
    """A cumulus: a cluster of soft blobs, flat-bottomed, bright on top and blue-grey underneath."""
    a = sc.acc(name, c)
    n = rng.randint(5, 8)
    for i in range(n):
        t = (i / (n - 1)) * 2 - 1
        r = size * (0.55 + 0.45 * (1 - abs(t))) * rng.uniform(0.75, 1.1)
        p = (c[0] + t * size * 1.6 + rng.uniform(-0.2, 0.2) * size, c[1] + r * 0.25 + rng.uniform(0, 0.3) * size,
             c[2] + rng.uniform(-0.4, 0.4) * size)
        base = c[1]

        def cc(nx, ny, nz, q, base=base, r=r):
            k = smooth(base, base + r * 1.3, q[1])
            return mix(under, top, k)
        a.blob(p, (r, r * 0.75, r * 0.8), "cloud", cc, segs=10, rings=6, rough=0.12, nscale=0.9, seed=rng.random() * 9)
    return a


def rock(a, c, r, rng, col_top, col_side, flat=False, segs=7, wet=None):
    """A faceted boulder: flat-shaded facets, lighter on top, speckled, with a darker wet band at its foot
    (wet: the height of the waterline, if any) and a few lichen spots."""
    seed = rng.random() * 50
    base_y = c[1] - r[1] * 0.4

    def cc(nx, ny, nz, q):
        col = mix(col_side, col_top, smooth(0.0, 0.85, ny + 0.15 * n3(Vector(q), 1.3, seed)))
        col = mul(col, 0.9 + 0.2 * (0.5 + 0.5 * n3(Vector(q), 4.0, seed + 3)))
        if n3(Vector(q), 2.2, seed + 7) > 0.42 and ny > 0.2:
            col = mix(col, hexc("#c8b06a"), 0.45)
        foot = smooth(base_y + 0.35 * r[1], base_y, q[1])
        col = mix(col, mul(col_side, 0.62), foot * (1.0 if wet is None else 0.4))
        if wet is not None:
            col = mix(col, mul(col_side, 0.5), smooth(wet + 0.25, wet, q[1]))
        return col
    a.blob(c, r, "rock", cc, segs=max(segs, 11), rings=7, rough=0.34, nscale=0.9, seed=seed, sm=False, cut=-0.4)


def tuft(a, c, h, col_base, col_tip, rng, blades=5, material="foliage_sway"):
    """A grass tuft: thin leaning triangles."""
    a.sway_base = c[1]
    for i in range(blades):
        ang = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.15, 0.45) * h
        w = h * 0.08
        dx, dz = math.cos(ang), math.sin(ang)
        b = Vector(c) + Vector((dx * 0.05, 0, dz * 0.05))
        tip = b + Vector((dx * lean, h * rng.uniform(0.7, 1.1), dz * lean))
        side = Vector((-dz, 0, dx)) * w
        a.poly([b - side, b + side, tip], material, [col_base, col_base, col_tip], sm=False)




# ------------------------------------------------------------------ materials

MAT_DEFS.update({
    # name: (base colour, roughness, metallic, emission strength, alpha)
    "thatch": ((1, 1, 1), 0.95, 0, 0, 1),
    "fabric": ((1, 1, 1), 0.95, 0, 0, 1),
    "gloss": ((1, 1, 1), 0.15, 0, 0, 1),
    "trunk_sway": ((1, 1, 1), 0.9, 0, 0, 1),
    "sand": ((1, 1, 1), 0.95, 0, 0, 1),
    "tape": ((1, 1, 1), 0.6, 0, 0, 1),
    "paint": ((1, 1, 1), 0.55, 0, 0, 1),
    "wood": ((1, 1, 1), 0.8, 0, 0, 1),
    "rock": ((1, 1, 1), 0.85, 0, 0, 1),
    "metal": ((1, 1, 1), 0.35, 0.7, 0, 1),
    "cloth": ((1, 1, 1), 0.9, 0, 0, 1),
    "board": ((1, 1, 1), 0.9, 0, 0, 1),
    "critter": ((1, 1, 1), 0.5, 0, 0, 1),
    "cloud": ((1, 1, 1), 1.0, 0, 0, 1),
    "sea": ((1, 1, 1), 0.1, 0, 0, 1),
    "swash": ((1, 1, 1), 0.1, 0, 0, 1),
    "net": ((1, 1, 1), 0.8, 0, 0, 1),
    "palm_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "foliage_sway": ((1, 1, 1), 0.85, 0, 0, 1),
    "flag_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "bunting_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "lantern_glow": ((1.0, 0.8, 0.5), 0.6, 0, 2.0, 1),
    "bulb_glow": ((1.0, 0.85, 0.55), 0.4, 0, 3.0, 1),
    "ember_glow": ((1.0, 0.4, 0.1), 0.8, 0, 3.0, 1),
    "fire_glow": ((1.0, 0.6, 0.2), 1, 0, 4.0, 1),
})

SEA = -0.55
SLOPE = 0.045


# ------------------------------------------------------------------ the land

def shore_z(x):
    """Where the sand meets the still water (the waves run up past it)."""
    return -18.5 + 1.1 * math.sin(x * 0.06 + 1.0) + 0.9 * fbm(x, 0.0, 0.04, 2, 11)


def smin(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


def court_mask(x, z, pad=0.0):
    """1 on the court (x 0..16, z -4..4, grown by pad), falling to 0 over a metre."""
    return smooth(-1.0 - pad, 0.0 - pad, x) * smooth(17.0 + pad, 16.0 + pad, x) * \
        smooth(-5.0 - pad, -4.0 - pad, z) * smooth(5.0 + pad, 4.0 + pad, z)


def ripple(x, z):
    """Wind ripples on the dry sand: -1..1."""
    w = fbm(x, z, 0.18, 2, 3) * 2.5
    return math.sin((x * 0.3 + z * 1.0) * 4.2 + w) * (0.6 + 0.4 * n2(x, z, 0.3, 4))


def dunes(x, z):
    side = smooth(13.0, 22.0, abs(x - 8.0))
    back = smooth(shore_z(x) + 3.0, shore_z(x) + 9.0, z)
    return side * back * (0.35 + 0.9 * max(0.0, fbm(x, z, 0.07, 3, 5) + 0.3)) * (1.0 + 0.5 * smooth(20, 40, abs(x - 8)))


def h_land(x, z):
    """Sand and sea bed near the court, headlands at the far sides (all one function so the grids meet)."""
    d = shore_z(x) - z  # metres out to sea (negative on the beach)
    beach = SEA - SLOPE * d - 0.12 * max(0.0, d - 3.0) - 0.02 * max(0.0, d - 20.0) ** 1.3
    y = smin(0.0, beach, 0.5)
    y += dunes(x, z)
    # the headlands: jungle hills on the left, a lower rocky point on the right
    L = smooth(-20.0, -34.0, x - 0.45 * (z + 30.0) + 7.0 * fbm(x, z, 0.04, 2, 7)) * smooth(-22.0, -40.0, z)
    R = smooth(38.0, 52.0, x + 0.35 * (z + 30.0) + 6.0 * fbm(x, z, 0.05, 2, 8)) * smooth(-24.0, -45.0, z)
    hl = 2.0 + 13.0 * smooth(0.0, 1.0, L) * (0.7 + 0.5 * fbm(x, z, 0.03, 3, 9)) + 3.0 * max(0.0, -z - 90.0) * 0.02
    hr = 1.5 + 6.0 * smooth(0.0, 1.0, R) * (0.7 + 0.5 * fbm(x, z, 0.05, 3, 10))
    y = max(y, SEA - 3.0 + (hl + 3.0) * smooth(0.15, 0.5, L))
    y = max(y, SEA - 3.0 + (hr + 3.0) * smooth(0.15, 0.5, R))
    # churned sand on the court: small, and never more than a couple of centimetres off 0
    cm = court_mask(x, z)
    rip = ripple(x, z) * 0.028 * (1.0 - cm) * smooth(-1.0, 1.5, -d - 2.5)
    y += rip + cm * 0.012 * fbm(x, z, 1.3, 2, 12)
    return y


DRY, DRY2 = hexc("#f2d6a0"), hexc("#e8c486")
CRUST = hexc("#f8e6bc")
WET, WET2 = hexc("#c8a676"), hexc("#a98a5f")
GRASS, GRASS2 = hexc("#4f9a3a"), hexc("#8cc04c")
JUNGLE, JUNGLE2 = hexc("#2f7a3a"), hexc("#5aa845")
CLIFF, CLIFF2 = hexc("#8a7466"), hexc("#b89c84")


def sand_col(x, y, z, ny):
    d = shore_z(x) - z
    c = mix(DRY, DRY2, 0.5 + 0.5 * fbm(x, z, 0.25, 3, 21))
    cm = court_mask(x, z)
    r = ripple(x, z) * (1.0 - cm)
    c = mix(c, CRUST if r > 0 else mul(DRY2, 0.93), abs(r) * 0.35 * smooth(-1.0, 3.0, -d - 2.0))
    # the court: kicked-up sand, darker where the blobs work (round their home spots and under the net)
    churn = cm * (0.5 + 0.5 * n2(x, z, 1.1, 22))
    home = max(math.exp(-((x - 3.0) ** 2 + z * z * 2.0) / 9.0), math.exp(-((x - 13.0) ** 2 + z * z * 2.0) / 9.0))
    c = mix(c, mul(DRY2, 0.9), churn * 0.25 + home * 0.18 * cm)
    # damp sand near the water, then wet and glossy at the waterline
    c = mix(c, WET, smooth(-5.0, -0.5, d) * 0.85)
    c = mix(c, WET2, smooth(-0.6, 1.5, d))
    # grass on the dunes and the headlands
    if y > 0.5 and ny > 0.75:
        g = mix(GRASS, GRASS2, 0.5 + 0.5 * n2(x, z, 0.2, 23))
        c = mix(c, g, smooth(0.6, 1.6, y) * smooth(0.75, 0.9, ny) * (0.35 if abs(x - 8) < 30 else 1.0))
    if y > 2.5:
        c = mix(c, mix(JUNGLE, JUNGLE2, 0.5 + 0.5 * n2(x, z, 0.1, 24)), smooth(2.5, 4.0, y) * smooth(0.6, 0.85, ny))
        c = mix(c, mix(CLIFF, CLIFF2, 0.5 + 0.5 * math.sin(y * 1.7)), smooth(0.72, 0.5, ny))
    return c


def grid(a, xs, zs, h, col, material, sm=True):
    rows = []
    for z in zs:
        row = []
        for x in xs:
            y = h(x, z)
            e = 0.05
            gx = (h(x + e, z) - h(x - e, z)) / (2 * e)
            gz = (h(x, z + e) - h(x, z - e)) / (2 * e)
            ny = 1.0 / math.sqrt(1 + gx * gx + gz * gz)
            row.append((a.vert((x, y, z)), col(x, y, z, ny)))
        rows.append(row)
    for i in range(len(zs) - 1):
        for j in range(len(xs) - 1):
            es = [rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]]
            c = sum((a.v[e[0]] for e in es), Vector()) / 4
            a.face([e[0] for e in es], material, [e[1] for e in es], sm=sm, out=(c.x, c.y - 100, c.z))


def steps(a, b, n):
    return [a + (b - a) * i / n for i in range(n)]


def build_land(sc, rng):
    xs = steps(-60.0, -6.0, 30) + steps(-6.0, 22.0, 94) + steps(22.0, 76.0, 30) + [76.0]
    zs = steps(14.0, 7.0, 6) + steps(7.0, -7.0, 48) + steps(-7.0, -26.0, 34) + steps(-26.0, -34.0, 4) + [-34.0]
    near = sc.acc("near_sand")
    grid(near, xs, zs, h_land, sand_col, "sand")
    far = sc.acc("far_land")
    far.terrain(-33.5, -420.0, 60, 90, h_land, sand_col, material="sand", margin=1.9)

    # footprints: pairs of dimples across the court and down to the water (a darker bowl with a pale lip)
    fp = sc.acc("near_prints")

    def print_at(x, z, ang, s=1.0):
        y = h_land(x, z) + 0.006
        ca, sa = math.cos(ang), math.sin(ang)
        pts, cols = [], []
        for k in range(8):
            t = 2 * math.pi * k / 8
            u, v = math.cos(t) * 0.09 * s, math.sin(t) * 0.16 * s
            pts.append((x + u * ca - v * sa, y, z + u * sa + v * ca))
            cols.append(mix(hexc("#d9b98a"), CRUST, 0.5 + 0.5 * math.sin(t + ang + 2.0)))
        ids = [fp.vert(p) for p in pts]
        cid = fp.vert((x, y - 0.004, z))
        for k in range(8):
            fp.face([ids[k], ids[(k + 1) % 8], cid], "sand", [cols[k], cols[(k + 1) % 8], hexc("#cfae80")],
                    out=(x, y - 100, z))
    trails = [((-3.5, 2.0), (6.0, -1.5)), ((10.0, 3.0), (19.0, -3.0)), ((2.0, -3.5), (-4.0, -14.0)),
              ((14.0, -3.8), (20.0, -15.0)), ((5.0, 1.5), (7.2, -3.0)), ((12.0, -2.0), (9.0, -12.0)),
              ((-6.0, -6.0), (-8.0, -17.5)), ((24.0, 1.0), (25.0, -9.0))]
    for (x0, z0), (x1, z1) in trails:
        L = math.hypot(x1 - x0, z1 - z0)
        n = int(L / 0.42)
        ang = math.atan2(x1 - x0, z1 - z0)
        nx, nz = (z1 - z0) / L, -(x1 - x0) / L
        for i in range(n):
            t = i / max(1, n - 1)
            side = 0.13 if i % 2 else -0.13
            wob = 0.4 * math.sin(t * 7.0 + x0)
            px = x0 + (x1 - x0) * t + nx * (side + wob)
            pz = z0 + (z1 - z0) * t + nz * (side + wob)
            if shore_z(px) - pz > -0.8:
                continue
            print_at(px, pz, -ang + rng.uniform(-0.2, 0.2), rng.uniform(0.9, 1.1))
    # blob dimples on the court: soft round hollows where the jellies landed
    for i in range(14):
        side = i % 2
        x = rng.uniform(1.0, 7.0) if side == 0 else rng.uniform(9.0, 15.0)
        z = rng.uniform(-2.5, 2.5)
        y = h_land(x, z) + 0.005
        r = rng.uniform(0.25, 0.45)
        ring = [fp.vert((x + math.cos(2 * math.pi * k / 10) * r, y, z + math.sin(2 * math.pi * k / 10) * r * 0.8))
                for k in range(10)]
        cid = fp.vert((x, y, z))
        for k in range(10):
            t = 2 * math.pi * k / 10
            base = mix(DRY, DRY2, 0.5 + 0.5 * fbm(x, z, 0.25, 3, 21))
            lip = mix(base, CRUST, 0.25 + 0.25 * math.sin(t + 1.9))
            fp.face([ring[k], ring[(k + 1) % 10], cid], "sand", [lip, lip, mul(base, 0.95)], out=(x, y - 100, z))


def build_sea(sc):
    a = sc.acc("far_sea")
    dn, df = CAM.z + 12.0, CAM.z + 1300.0
    rows, cols = 96, 90
    grid_ = []
    for i in range(rows + 1):
        t = i / rows
        d = dn * (df / dn) ** t
        z = CAM.z - d
        hw = half_w(z, 2.3) + 20.0
        row = []
        for j in range(cols + 1):
            x = 8 - hw + 2 * hw * j / cols
            dist = shore_z(x) - z  # UV.y: metres out from the waterline (the shader draws the breakers from it)
            row.append((a.vert((x, SEA, z)), (x, dist)))
        grid_.append(row)
    for i in range(rows):
        for j in range(cols):
            es = [grid_[i][j], grid_[i + 1][j], grid_[i + 1][j + 1], grid_[i][j + 1]]
            a.face([e[0] for e in es], "sea", (1, 1, 1), uvs=[e[1] for e in es], sm=True,
                   out=(0, SEA - 100, CAM.z - dn))
    # the swash: a thin strip lying on the sand from just below the waterline to the top of the run-up
    s = sc.acc("near_swash")
    xs = steps(-45.0, 61.0, 150) + [61.0]
    vs = [-0.12, 0.0, 0.1, 0.22, 0.36, 0.5, 0.66, 0.82, 1.0]
    RUN = 7.0
    grid2 = []
    for v in vs:
        row = []
        for x in xs:
            z = shore_z(x) + v * RUN
            y = max(h_land(x, z), SEA) + 0.018
            row.append((s.vert((x, y, z)), (x, v)))
        grid2.append(row)
    for i in range(len(vs) - 1):
        for j in range(len(xs) - 1):
            es = [grid2[i][j], grid2[i + 1][j], grid2[i + 1][j + 1], grid2[i][j + 1]]
            s.face([e[0] for e in es], "swash", (1, 1, 1), uvs=[e[1] for e in es], sm=True,
                   out=(0, -100, 0))


# ------------------------------------------------------------------ the court

def build_court(sc, rng):
    c = sc.acc("near_court")
    blue, peg = hexc("#1f74d6"), hexc("#f2f2ee")
    W = 0.09

    def tape(x0, z0, x1, z1):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0) / 0.5))
        for i in range(n):
            ax, az = x0 + (x1 - x0) * i / n, z0 + (z1 - z0) * i / n
            bx, bz = x0 + (x1 - x0) * (i + 1) / n, z0 + (z1 - z0) * (i + 1) / n
            L = math.hypot(bx - ax, bz - az)
            ux, uz = (bz - az) / L * W / 2, -(bx - ax) / L * W / 2
            ya, yb = h_land(ax, az) + 0.012, h_land(bx, bz) + 0.012
            col = mul(blue, 0.93 + 0.1 * n2(ax, az, 2.0))
            c.poly([(ax - ux, ya, az - uz), (bx - ux, yb, bz - uz), (bx + ux, yb, bz + uz), (ax + ux, ya, az + uz)],
                   "tape", col, out=(ax, -100, az))
    Z0, Z1 = -3.6, 3.6
    tape(0, Z0, 16, Z0)
    tape(0, Z1, 16, Z1)
    tape(0, Z0, 0, Z1)
    tape(16, Z0, 16, Z1)
    tape(8, Z0, 8, Z1)
    for x, z in ((0, Z0), (16, Z0), (0, Z1), (16, Z1), (8, Z0), (8, Z1)):
        c.box((x, 0.02, z), (0.14, 0.05, 0.14), "paint", peg)

    # the net: two striped posts, the mesh (the game swaps a grid shader: UV in metres), a white top band,
    # antennae, guy ropes to pegs
    NZ0, NZ1 = -4.4, 2.0
    TOP = 2.4
    n = sc.acc("near_net")
    for z in (NZ0, NZ1):
        def band(i, p):
            return hexc("#e8452c") if int(p.y / 0.4) % 2 == 0 else hexc("#f7f5ef")
        pts = [(8.0, -0.3 + 0.2 * k, z) for k in range(16)]
        n.tube(pts, 0.075, "paint", band, segs=8, sm=True)
        n.lathe((8.0, 2.7, z), [(0.09, 0.0), (0.1, 0.05), (0.0, 0.12)], 8, "paint", hexc("#f7f5ef"), cap=False)
        n.box((8.0, 0.05, z), (0.34, 0.1, 0.34), "wood", hexc("#8a6a4a"))
    # the top band and the bottom cord
    n.box((8.0, TOP - 0.035, (NZ0 + NZ1) / 2), (0.03, 0.07, NZ1 - NZ0 - 0.1), "paint", hexc("#fbfbf6"))
    n.box((8.0, 0.62, (NZ0 + NZ1) / 2), (0.02, 0.03, NZ1 - NZ0 - 0.1), "paint", hexc("#eceae0"))
    for z in (NZ0 + 0.35, NZ1 - 0.35):
        n.box((8.0, TOP - 0.45, z), (0.04, 0.9, 0.05), "paint", hexc("#fbfbf6"))  # side bands
        pts = [(8.0, TOP - 0.9 + 0.2 * k, z) for k in range(9)]
        n.tube(pts, 0.018, "paint", lambda i, p: hexc("#e8452c") if i % 2 else hexc("#fbfbf6"), segs=5)
    for z, dz in ((NZ0, -1.6), (NZ1, 1.4)):
        n.tube([(8.0, 2.62, z), (8.0, 0.05, z + dz)], 0.012, "paint", hexc("#e9e2d0"), segs=4)
        n.box((8.0, 0.04, z + dz), (0.1, 0.08, 0.1), "wood", hexc("#8a6a4a"))
    m = sc.acc("near_netmesh")
    y0, y1 = 0.64, TOP - 0.07
    z0, z1 = NZ0 + 0.35, NZ1 - 0.35
    m.poly([(8.0, y0, z0), (8.0, y0, z1), (8.0, y1, z1), (8.0, y1, z0)], "net", (1, 1, 1),
           uvs=[(z0, y0), (z1, y0), (z1, y1), (z0, y1)], out=(-100, 1, 0))


# ------------------------------------------------------------------ props

def palm(a, c, H, lean, rng, fronds=10, green=None, coco=True, lod=False):
    """A coconut palm: a curved trunk (trunk_sway: the game draws ring bark from UV.y = height above the foot) with a
    root flare and ring bulges, a boot of leaf bases, a cluster of coconuts, and a crown of arching fronds, each a
    rachis with two rows of drooping leaflets (palm_sway: UV.x along the frond, so the tips flutter), plus a dead frond
    or two hanging down the trunk. lod: far palms, serrated flat fronds and a coarse trunk."""
    a.sway_base = c[1]
    x, y, z = c
    pr = random.Random(int(x * 1000) * 7 + int(z * 1000))  # the palm's own details (the scene rng stays in step)
    green = green or hexc("#3f9a3a")
    pts, radii = [], []
    N = 6 if lod else 22
    for i in range(N + 1):
        t = i / N
        bend = t ** 1.7
        # the trunk leans out, then turns a little back up under the crown
        up = 0.08 * H * max(0.0, t - 0.7) ** 2
        pts.append((x + lean[0] * H * bend - lean[0] * up, y + H * t, z + lean[1] * H * bend - lean[1] * up))
        r = (0.23 - 0.09 * t) * H / 8.0 + 0.05
        r *= 1.0 + 0.55 * smooth(0.1, 0.0, t)  # the root flare
        if not lod:
            r *= 1.0 if i % 2 == 0 else 0.93   # ring bulges
        radii.append(r)
    pts[0] = (x, y - 0.3, z)
    bark, bark2 = hexc("#7e6044"), hexc("#b89468")

    def tc(i, p):
        t = i / N
        return mix(mix(bark, bark2, 0.35 + 0.4 * (i % 2) + 0.2 * n2(p.x, p.y, 3.0, 31)), hexc("#9a8a5a"),
                   0.35 * smooth(0.8, 1.0, t))
    a.tube(pts, radii, "palm_sway" if lod else "trunk_sway", tc, segs=5 if lod else 10, sm=True)
    top = Vector(pts[-1])
    if not lod:
        # the boot: the swollen bases of old fronds wrapping the top of the trunk
        for k in range(7):
            ang = 2 * math.pi * k / 7 + pr.uniform(-0.2, 0.2)
            d = Vector((math.cos(ang), 0, math.sin(ang)))
            b0 = top + d * radii[-1] * 0.6 + Vector((0, -0.55, 0))
            a.tube([tuple(b0), tuple(b0 + d * 0.12 + Vector((0, 0.35, 0))), tuple(top + d * 0.3 + Vector((0, 0.25, 0)))],
                   [0.09, 0.08, 0.04], "palm_sway", lambda i, p: mix(hexc("#7a6a3a"), hexc("#9a8d52"), i / 2), segs=5)
    if coco:
        n_c = pr.randint(5, 8) if not lod else 3
        side = pr.uniform(0, 2 * math.pi)
        for k in range(n_c):
            ang = side + pr.uniform(-1.3, 1.3)
            p = top + Vector((math.cos(ang) * 0.26, -0.3 - pr.uniform(0, 0.25), math.sin(ang) * 0.26))
            ripe = pr.random()
            col = mix(hexc("#5f7a2a"), hexc("#8a6a30"), ripe)
            a.blob(tuple(p), (0.15, 0.17, 0.15), "palm_sway",
                   lambda nx, ny, nz, q, col=col: mix(mul(col, 0.7), mix(col, hexc("#c8b060"), 0.25), smooth(-0.6, 0.8, ny)),
                   segs=7, rings=5, rough=0.12, seed=pr.random() * 9)
    L0 = H * 0.42 + 1.2
    if lod:
        for k in range(fronds):
            ang = 2 * math.pi * k / fronds + rng.uniform(-0.25, 0.25)
            L = L0 * rng.uniform(0.85, 1.1)
            rise, droop = rng.uniform(0.25, 0.55), rng.uniform(1.1, 1.6)
            d = Vector((math.cos(ang), 0, math.sin(ang)))
            sd = Vector((-d.z, 0, d.x))
            S = 6
            spine = [top + d * (L * j / S * (1.0 - 0.15 * j / S)) + Vector((0, (rise * j / S - droop * (j / S) ** 2) * L * 0.55, 0))
                     for j in range(S + 1)]
            base_c, tip_c = mul(green, 0.62), mix(green, hexc("#b8d25a"), 0.45)
            for j in range(S):
                s0, s1 = j / S, (j + 1) / S
                w = L * 0.24 * math.sin(math.pi * min(1.0, s1 * 1.05)) ** 0.8 + 0.05
                for sgn in (-1, 1):
                    tip = (spine[j] + spine[j + 1]) / 2 + sd * sgn * w + d * (0.35 * w) + Vector((0, -0.45 * w, 0))
                    a.poly([spine[j], spine[j + 1], tip], "palm_sway",
                           [mix(base_c, tip_c, s0), mix(base_c, tip_c, s1), mix(base_c, tip_c, (s0 + s1) / 2)],
                           uvs=[(s0, spine[j].y - y), (s1, spine[j + 1].y - y), ((s0 + s1) / 2 + 0.1, tip.y - y)])
        return top
    nf = fronds + 4
    for k in range(nf + 1):
        dead = k >= nf
        ang = 2 * math.pi * k / nf + pr.uniform(-0.2, 0.2) if not dead else pr.uniform(0, 2 * math.pi)
        young = (not dead) and k >= nf - 3
        tier = k % 2  # alternate fronds sit a little higher and rise more: a layered crown
        L = L0 * (0.62 if young else pr.uniform(0.85, 1.12)) * (0.8 if dead else 1.0)
        rise = 1.0 if young else (pr.uniform(0.35, 0.65) if tier else pr.uniform(0.15, 0.4))
        droop = 0.7 if young else pr.uniform(1.15, 1.7)
        if dead:
            rise, droop = -0.4, 2.4
        d = Vector((math.cos(ang), 0, math.sin(ang)))
        sd = Vector((-d.z, 0, d.x))
        S = 9
        base = top + Vector((0, 0.12 * tier - (0.35 if dead else 0.0), 0))
        spine = []
        for j in range(S + 1):
            sj = j / S
            spine.append(base + d * (L * sj * (1.0 - 0.15 * sj)) + Vector((0, (rise * sj - droop * sj * sj) * L * 0.55, 0)))
        if dead:
            g0, g1 = hexc("#8a6a3a"), hexc("#b89458")
        else:
            gk = mix(green, hexc("#6aa83a"), pr.uniform(0.0, 0.35))
            g0, g1 = mul(gk, 0.55), mix(gk, hexc("#c8dc6a"), 0.4)
        # the rachis: a narrow ribbon, pale on top
        for j in range(S):
            s0, s1 = j / S, (j + 1) / S
            w0, w1 = 0.05 * (1 - s0) + 0.012, 0.05 * (1 - s1) + 0.012
            p0, p1 = spine[j], spine[j + 1]
            a.poly([p0 - sd * w0, p1 - sd * w1, p1 + sd * w1, p0 + sd * w0], "palm_sway", mix(g1, hexc("#d8d890"), 0.4),
                   uvs=[(s0, p0.y - y), (s1, p1.y - y), (s1, p1.y - y), (s0, p0.y - y)])
        # leaflets: two rows, longest mid-frond, swept towards the tip and folding down more towards it
        NL = 16
        for sgn in (-1, 1):
            for j in range(NL):
                sj = 0.08 + 0.9 * (j + 0.5 * (sgn > 0)) / NL
                fi = sj * S
                i0 = min(S - 1, int(fi))
                p = spine[i0].lerp(spine[i0 + 1], fi - i0)
                fwd = (spine[i0 + 1] - spine[i0]).normalized()
                ll = L * 0.36 * math.sin(math.pi * min(0.97, sj * 0.92 + 0.06)) ** 0.7 + 0.12
                fold = 0.25 + 0.85 * sj + pr.uniform(-0.12, 0.12)
                if dead:
                    fold = 1.3
                out_ = (sd * sgn * math.cos(fold) + Vector((0, -math.sin(fold), 0)) + fwd * 0.55).normalized()
                w = 0.06 + 0.04 * math.sin(math.pi * sj)
                mid = p + out_ * ll * 0.5 + Vector((0, -0.06 * ll, 0))
                tip = p + out_ * ll + Vector((0, -0.2 * ll, 0)) + fwd * 0.08 * ll
                cB = mix(g0, g1, 0.2 + 0.5 * sj)
                cT = mix(g1, hexc("#e0d880") if not dead else hexc("#c8a868"), 0.25 * sj + pr.uniform(0, 0.15))
                u0, u1, u2 = sj, sj + 0.15, sj + 0.3
                # a kite of two triangles, bent at its widest: base, the two sides at mid-length, the tip
                ml, mr = mid - fwd * w, mid + fwd * w
                a.poly([p, mr, ml], "palm_sway", [cB, mix(cB, cT, 0.55), mix(cB, cT, 0.5)],
                       uvs=[(u0, p.y - y), (u1, mid.y - y), (u1, mid.y - y)])
                a.poly([ml, mr, tip], "palm_sway", [mix(cB, cT, 0.5), mix(cB, cT, 0.55), cT],
                       uvs=[(u1, mid.y - y), (u1, mid.y - y), (u2, tip.y - y)])
    return top


def umbrella(a, c, R, cols, tilt=(0.0, 0.0), segs=8, rng=None):
    """A beach parasol: a two-part pole with a joint collar, a domed canopy whose panels sag between the ribs
    (alternating colours), rib tips, a scalloped valance and a finial. tilt: the lean of the pole (dx, dz per metre)."""
    from mathutils import Matrix
    x, y, z = c
    H = 2.3
    foot = Vector((x, y - 0.3, z))
    axis = Vector((tilt[0], 1.0, tilt[1])).normalized()
    rot = Vector((0, 1, 0)).rotation_difference(axis).to_matrix()
    top = Vector((x, y, z)) + axis * H

    def T(p):  # canopy space (y up about the pole top) to the scene
        return top + rot @ Vector(p)
    white = hexc("#eeece6")
    a.tube([tuple(foot), tuple(Vector((x, y, z)) + axis * 1.2)], 0.03, "metal", white, segs=6)
    a.tube([tuple(Vector((x, y, z)) + axis * 1.2), tuple(top + axis * 0.2)], 0.024, "metal", white, segs=6)
    a.lathe(tuple(Vector((x, y, z)) + axis * 1.16), [(0.045, 0), (0.045, 0.1)], 6, "metal", hexc("#c8c6c0"))
    a.lathe(tuple(Vector((x, y, z)) + axis * 1.9), [(0.04, 0), (0.05, 0.05), (0.035, 0.1)], 6, "paint", white)
    DOME = 0.42

    def surf(t, ang):
        """Canopy point at radius fraction t, angle ang (sagging between ribs)."""
        k = (ang / (2 * math.pi / segs)) % 1.0
        sag = 0.07 * math.sin(math.pi * k) * t
        r = R * t * (1.0 - 0.04 * math.sin(math.pi * k))
        return T((math.cos(ang) * r, DOME * (1.0 - t ** 1.5) - sag + 0.1, math.sin(ang) * r))
    TR, TA = 4, 3
    for j in range(segs):
        col = cols[j % len(cols)]
        a0 = 2 * math.pi * j / segs
        grid = [[a.vert(tuple(surf(i / TR, a0 + (2 * math.pi / segs) * q / TA))) for q in range(TA + 1)]
                for i in range(TR + 1)]
        for i in range(TR):
            for q in range(TA):
                lt = mix(col, (1, 1, 1), 0.08 * (1 - i / TR))
                ids = [grid[i][q], grid[i][q + 1], grid[i + 1][q + 1], grid[i + 1][q]]
                a.face(ids, "fabric", [lt, lt, col, col], sm=True, out=tuple(T((0, -3, 0))))
        # the valance: a scalloped flap hanging from the rim
        for q in range(TA):
            p0, p1 = surf(1.0, a0 + (2 * math.pi / segs) * q / TA), surf(1.0, a0 + (2 * math.pi / segs) * (q + 1) / TA)
            m = (p0 + p1) / 2
            dn = rot @ Vector((0, -1, 0))
            a.poly([tuple(p0), tuple(p1), tuple(p1 + dn * 0.12), tuple(m + dn * 0.2), tuple(p0 + dn * 0.12)], "fabric",
                   mul(col, 0.85), out=tuple(T((0, 0.2, 0))))
        # the rib tip
        a.blob(tuple(surf(1.0, a0) + rot @ Vector((0, -0.02, 0))), (0.03, 0.03, 0.03), "paint", white, segs=5,
               rings=3, rough=0.0)
    a.lathe(tuple(T((0, DOME + 0.08, 0))), [(0.07, 0), (0.05, 0.08), (0.02, 0.14), (0.0, 0.18)], 7, "paint",
            hexc("#f4f0e6"))


def towel(a, c, w, l, ry, cols):
    """A striped beach towel lying on the sand, rumpled in soft folds, with a rolled-up end (a pillow) and fringes.
    cols: the stripes along its length; the first colour is the border."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)
    n = len(cols)
    NU, NV = 16, 5

    def P(u, v, lift=0.0):
        px, pz = x + u * cr + v * sr, z - u * sr + v * cr
        fold = 0.018 * math.sin(u * 5.0 + v * 2.0 + x) + 0.012 * math.sin(v * 9.0 - u * 3.0)
        return (px, h_land(px, pz) + 0.03 + max(0.0, fold) + lift, pz)
    roll = 0.22
    for i in range(NU):
        u0, u1 = -l / 2 + roll + (l - roll) * i / NU, -l / 2 + roll + (l - roll) * (i + 1) / NU
        stripe = cols[min(n - 1, int((i + 0.5) / NU * n))]
        for j in range(NV):
            v0, v1 = -w / 2 + w * j / NV, -w / 2 + w * (j + 1) / NV
            col = cols[0] if j in (0, NV - 1) and n > 2 else stripe
            a.poly([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], "fabric", col, out=(x, y - 100, z), sm=True)
    # the rolled end
    px, pz = x + (-l / 2 + roll * 0.5) * cr, z - (-l / 2 + roll * 0.5) * sr
    yy = h_land(px, pz) + 0.1
    a.tube([(px - (w / 2) * sr, yy, pz - (w / 2) * cr), (px + (w / 2) * sr, yy, pz + (w / 2) * cr)], 0.1, "fabric",
           cols[1 % n], segs=8, cap=True)
    # fringes at the far end
    for j in range(9):
        v = -w / 2 + w * (j + 0.5) / 9
        p0 = P(l / 2, v)
        p1 = P(l / 2 + 0.08, v + 0.01)
        a.poly([p0, (p0[0] + 0.015 * sr, p0[1], p0[2] + 0.015 * cr), p1], "fabric", mul(cols[0], 0.95),
               out=(x, y - 100, z))


def deck_chair(a, c, ry, col):
    """A folding wooden deck chair: rounded rails, cross bars, and a striped canvas sling that sags between them."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)

    def P(u, v, s):
        return (x + u * cr + s * sr, y + v, z - u * sr + s * cr)
    wood, wood2 = hexc("#c9a577"), hexc("#b08a5c")
    for s in (-0.3, 0.3):
        a.tube([P(-0.62, 0, s), P(0.38, 0.95, s)], 0.025, "wood", wood, segs=6)       # the back rails
        a.tube([P(0.42, 0, s * 0.9), P(-0.36, 0.58, s * 0.9)], 0.023, "wood", wood2, segs=6)  # the legs
        a.tube([P(-0.3, 0.02, s * 0.84), P(0.0, 0.33, s * 0.84)], 0.02, "wood", wood2, segs=5)  # the stand
        a.blob(P(0.0, 0.43, s * 0.95), (0.03, 0.03, 0.03), "metal", hexc("#c8c0b0"), segs=5, rings=3, rough=0.0)
    for u, v in ((-0.6, 0.02), (0.36, 0.93), (-0.36, 0.58), (-0.3, 0.02)):
        a.tube([P(u, v, -0.31), P(u, v, 0.31)], 0.022, "wood", wood, segs=6, cap=True)
    # the sling: a sagging sheet of striped canvas (stripes along its length), from the top bar to the front bar
    NR, NC = 10, 6

    def Q(t, sN):
        u = -0.58 + 0.93 * t
        v = 0.08 + 0.84 * t - 0.2 * math.sin(math.pi * t)
        # the middle sags a little more than the edges
        v -= 0.035 * math.cos(sN * math.pi / 2) * math.sin(math.pi * t)
        return P(u, v, sN * 0.28)
    stripes = [col, hexc("#f6f3ea"), col, hexc("#f6f3ea"), col, hexc("#f6f3ea")]
    for i in range(NR):
        for j in range(NC):
            t0, t1 = i / NR, (i + 1) / NR
            s0, s1 = -1 + 2 * j / NC, -1 + 2 * (j + 1) / NC
            a.poly([Q(t0, s0), Q(t1, s0), Q(t1, s1), Q(t0, s1)], "fabric", stripes[j], out=P(-2, 2.0, 0), sm=True)


def surfboard(a, c, ry, lean, col, stripe):
    """A glossy surfboard stuck nose-up in the sand: a pointed nose, a squash tail, domed deck and bottom, a thin
    stringer down the middle, a stripe and a fin by the tail."""
    x, y, z = c
    L = 2.3
    cr, sr = math.cos(ry), math.sin(ry)

    def width(t):  # t 0 tail .. 1 nose
        return 0.27 * (math.sin(math.pi * min(1.0, 0.18 + t * 0.86)) ** 0.75) * (1.0 - 0.3 * t ** 3) + 0.03

    def P(u, v, th):
        xx = x + u * cr + lean * (v + 0.4) + th * sr
        return (xx, y + v, z - u * sr + th * cr)
    NR = 14
    xs = (-1.0, -0.8, -0.45, 0.0, 0.45, 0.8, 1.0)
    rows = []
    for i in range(NR + 1):
        t = i / NR
        v = -0.45 + L * t
        wd = width(t) if i < NR else 0.0
        row = []
        for s_ in xs:
            th = (0.035 * (1 - s_ * s_) + 0.006) * (1.0 - 0.6 * t ** 2)
            row.append([a.vert(P(s_ * wd, v, th)), a.vert(P(s_ * wd, v, -th))])
        rows.append(row)
    for i in range(NR):
        v = -0.45 + L * (i + 0.5) / NR
        for j in range(len(xs) - 1):
            mid = (xs[j] + xs[j + 1]) / 2
            colr = col
            if abs(v - 0.95) < 0.1 or abs(v - 1.18) < 0.05:
                colr = stripe
            if abs(mid) < 0.25:
                colr = mul(colr, 0.8) if abs(v - 0.95) >= 0.1 else colr  # the stringer
            for f in (0, 1):
                a.face([rows[i][j][f], rows[i][j + 1][f], rows[i + 1][j + 1][f], rows[i + 1][j][f]], "gloss", colr,
                       sm=True, out=P(0, v, -5 if f == 0 else 5))
        # the rails join deck and bottom
        for j in (0, len(xs) - 1):
            a.face([rows[i][j][0], rows[i + 1][j][0], rows[i + 1][j][1], rows[i][j][1]], "gloss", mul(col, 0.9),
                   sm=True, out=P(0, v, 0))
    # the fin, on the bottom near the tail
    f0, f1 = -0.3, 0.02
    a.poly([P(0, f0, -0.04), P(0, f1, -0.04), P(0, f0 + 0.02, -0.22)], "gloss", mul(stripe, 0.9), out=P(-3, 0, -0.1))


def feather_flag(a, c, H, col, col2):
    """A tall teardrop beach banner on a bent pole; the cloth waves (flag_sway, UV.x = distance from the pole)."""
    x, y, z = c
    a.tube([(x, y - 0.4, z), (x, y + H, z)], 0.03, "metal", hexc("#d8d8d8"), segs=5)
    rows = 12
    top = y + H
    for i in range(rows):
        t0, t1 = i / rows, (i + 1) / rows
        y0 = top - t0 * H * 0.78
        y1 = top - t1 * H * 0.78

        def wid(t):
            return 0.95 * (math.sin(math.pi * min(1, t * 1.15) * 0.5 + 0.35) ** 1.2) * (1.0 - 0.75 * t ** 2) + 0.05
        w0, w1 = wid(t0), wid(t1)
        cA = col if (t0 < 0.55 or t0 > 0.75) else col2
        a.poly([(x, y0, z), (x, y1, z), (x + w1, y1 - 0.12 * w1, z), (x + w0, y0 - 0.12 * w0, z)], "flag_sway",
               [cA] * 4, uvs=[(0.0, y0 - y), (0.0, y1 - y), (w1, y1 - y), (w0, y0 - y)])


def bunting(a, p0, p1, sag, n, cols, rng):
    """A rope of little pennants between two points (bunting_sway: UV.y = depth below the rope)."""
    p0, p1 = Vector(p0), Vector(p1)
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(p0 + (p1 - p0) * t - Vector((0, sag * 4 * t * (1 - t), 0)))
    a.tube(pts, 0.012, "wood", hexc("#e8e0cc"), segs=3)
    for i in range(n):
        q0, q1 = pts[i], pts[i + 1]
        m = (q0 + q1) / 2
        a.poly([tuple(q0), tuple(q1), tuple(m + Vector((0, -0.34, 0)))], "bunting_sway", cols[i % len(cols)],
               uvs=[(0, 0), (0, 0), (0, 0.34)])


def lantern_string(a, p0, p1, sag, n, cols, rng, lights=None):
    """Paper lanterns hanging from a rope (lantern_glow: lit at dusk and night)."""
    p0, p1 = Vector(p0), Vector(p1)
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(p0 + (p1 - p0) * t - Vector((0, sag * 4 * t * (1 - t), 0)))
    a.tube(pts, 0.012, "wood", hexc("#3a3028"), segs=3)
    for i in range(1, n):
        p = pts[i] - Vector((0, 0.24, 0))
        a.tube([tuple(pts[i]), tuple(p + Vector((0, 0.18, 0)))], 0.008, "wood", hexc("#3a3028"), segs=3)
        col = cols[i % len(cols)]
        # a ribbed paper lantern: the profile steps in at each rib; dark caps top and bottom, a tassel
        prof = [(0.05, 0.0), (0.11, 0.025), (0.145, 0.06), (0.138, 0.075), (0.172, 0.11), (0.165, 0.13), (0.185, 0.18),
                (0.165, 0.23), (0.172, 0.25), (0.138, 0.285), (0.145, 0.3), (0.11, 0.335), (0.05, 0.36)]
        a.lathe(tuple(p - Vector((0, 0.18, 0))), prof, 10, "lantern_glow", col, sm=True)
        a.lathe(tuple(p + Vector((0, 0.165, 0))), [(0.06, 0), (0.06, 0.03), (0.0, 0.035)], 8, "wood", hexc("#2a2420"))
        a.lathe(tuple(p - Vector((0, 0.2, 0))), [(0.0, -0.01), (0.06, 0.0), (0.06, 0.03)], 8, "wood", hexc("#2a2420"),
                cap=False)
        a.tube([tuple(p - Vector((0, 0.2, 0))), tuple(p - Vector((0, 0.34, 0)))], [0.012, 0.02], "fabric",
               mul(col, 0.8), segs=4)
        if lights is not None and i == n // 2:
            lights.append(tuple(p))


def torch(sc, a, i, c, H=2.0):
    """A bamboo tiki torch; its flame is flame_<i> (shown at dusk and night), the light an empty light_torch_<i>."""
    x, y, z = c
    pts = [(x, y - 0.3, z)] + [(x, y + H * k / 6, z) for k in range(1, 7)]
    a.tube(pts, 0.05, "wood", lambda i_, p: hexc("#c9a35c") if i_ % 2 else hexc("#a88346"), segs=6)
    for k in range(1, 6):
        a.lathe((x, y + H * k / 6 - 0.02, z), [(0.058, 0), (0.058, 0.04)], 6, "wood", hexc("#7e6034"), cap=False)
    a.lathe((x, y + H, z), [(0.06, 0), (0.12, 0.05), (0.16, 0.12), (0.18, 0.2), (0.185, 0.28), (0.13, 0.3)], 10,
            "thatch", lambda px, py, pz: hexc("#6a4a2a") if int((math.atan2(pz - z, px - x) * 3.2 + (py - y) * 40)) % 2
            else hexc("#8a6436"), cap=True)
    a.lathe((x, y + H + 0.26, z), [(0.13, 0), (0.0, 0.02)], 8, "ember_glow", (1.0, 0.45, 0.15), cap=False)
    flame(sc, "flame_%d" % i, (x, y + H + 0.27, z), 0.55, 0.16)
    sc.empty("light_torch_%d" % i, (x, y + H + 0.6, z))


def flame(sc, name, c, H, R):
    """Three crossed quads; the fire shader draws a flickering tongue of flame on them (UV.y up the flame)."""
    f = sc.acc(name, c)
    x, y, z = c
    for k in range(3):
        ang = math.pi * k / 3
        dx, dz = math.cos(ang) * R, math.sin(ang) * R
        f.poly([(x - dx, y, z - dz), (x + dx, y, z + dz), (x + dx, y + H, z + dz), (x - dx, y + H, z - dz)],
               "fire_glow", (1, 1, 1), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])


def hut(a, c, w, d, h, wall, trim, roof, ry=0.0):
    """A beach hut: vertical planks in two tones with dark seams, white corner posts and trim, a pitched roof of
    overlapping boards with bargeboards and a ridge cap, a panelled door with a porthole window, a step and a shelf
    of shells; the door faces +z."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)

    def P(u, v, s):
        return (x + u * cr + s * sr, y + v, z - u * sr + s * cr)
    a.rbox(P(0, -0.12, 0), (w + 0.4, 0.3, d + 0.4), 0.04, "wood", hexc("#b0916a"), ry=ry)
    n = 9
    light = mix(wall, (1, 1, 1), 0.5)
    for i in range(n):
        u0 = -w / 2 + w * (i + 0.5) / n
        col = wall if i % 2 == 0 else light
        col = mul(col, 0.96 + 0.08 * n2(x + i, z, 1.0, 5))
        a.box(P(u0, h / 2, 0), (w / n - 0.018, h, d), "wood", col, ry=ry)
        a.box(P(u0 + w / n / 2, h / 2, 0), (0.02, h - 0.02, d - 0.02), "paint", mul(wall, 0.45), ry=ry)
    for su in (-1, 1):
        for ss in (-1, 1):
            a.rbox(P(su * (w / 2 + 0.02), h / 2, ss * (d / 2 + 0.02)), (0.1, h + 0.04, 0.1), 0.02, "paint", trim, ry=ry)
    a.rbox(P(0, h + 0.02, d / 2 + 0.04), (w + 0.16, 0.1, 0.06), 0.02, "paint", trim, ry=ry)
    rh = d * 0.42
    o = 0.26
    ridge0, ridge1 = P(0, h + rh, -d / 2 - o), P(0, h + rh, d / 2 + o)
    rows = 5
    for sgn in (-1, 1):
        for k in range(rows):
            t0, t1 = k / rows, (k + 1) / rows + 0.06
            def E(t, ss):
                return P(sgn * (w / 2 + o) * (1 - t), h - 0.08 + (rh + 0.08) * t, ss)
            col = mul(roof, 0.9 + 0.12 * (k % 2))
            a.poly([E(t0, -d / 2 - o), E(t0, d / 2 + o), E(min(1.0, t1), d / 2 + o), E(min(1.0, t1), -d / 2 - o)],
                   "wood", col, out=P(0, h, 0))
            # the board's lower edge: a thin lip that catches the light
            a.poly([E(t0, -d / 2 - o), E(t0, d / 2 + o), (E(t0, d / 2 + o)[0], E(t0, d / 2 + o)[1] - 0.05,
                    E(t0, d / 2 + o)[2]), (E(t0, -d / 2 - o)[0], E(t0, -d / 2 - o)[1] - 0.05, E(t0, -d / 2 - o)[2])],
                   "wood", mul(roof, 0.6), out=P(0, h, 0))
        # bargeboards along the gables
        for ss in (-1, 1):
            p0 = Vector(P(sgn * (w / 2 + o), h - 0.08, ss * (d / 2 + o)))
            p1 = Vector(P(0, h + rh, ss * (d / 2 + o)))
            a.tube([tuple(p0), tuple(p1)], 0.045, "paint", trim, segs=4)
    a.tube([ridge0, ridge1], 0.06, "paint", trim, segs=6, cap=True)
    for ss in (-1, 1):
        a.poly([P(-w / 2, h, ss * d / 2), P(w / 2, h, ss * d / 2), P(0, h + rh, ss * d / 2)], "paint", trim,
               out=P(0, h, 0))
    # the door: frame, panels, a porthole, a knob; a step in front
    a.rbox(P(0, h * 0.42, d / 2 + 0.03), (w * 0.52, h * 0.86, 0.05), 0.02, "paint", trim, ry=ry)
    a.rbox(P(0, h * 0.4, d / 2 + 0.06), (w * 0.42, h * 0.78, 0.04), 0.015, "wood", mul(wall, 0.72), ry=ry)
    for v in (0.2, 0.52):
        a.rbox(P(0, h * v, d / 2 + 0.085), (w * 0.3, h * 0.2, 0.02), 0.01, "wood", mul(wall, 0.82), ry=ry)
    ring = [P(0.25 * math.cos(2 * math.pi * k / 12) * 0.5, h * 0.72 + 0.25 * math.sin(2 * math.pi * k / 12) * 0.5,
              d / 2 + 0.09) for k in range(13)]
    a.tube(ring, 0.025, "paint", trim, segs=5)
    a.poly(ring[:12], "paint", hexc("#2a4a66"), out=P(0, h * 0.72, 0))
    a.blob(P(w * 0.15, h * 0.42, d / 2 + 0.1), (0.035, 0.035, 0.035), "metal", hexc("#d8b24a"), segs=6, rings=3,
           rough=0.0)
    a.rbox(P(0, 0.08, d / 2 + 0.35), (w * 0.6, 0.12, 0.4), 0.03, "wood", hexc("#c8a67a"), ry=ry)


def lifeguard_tower(sc, a, c, rng):
    x, y, z = c
    red, white, wood = hexc("#e04a36"), hexc("#f7f3ea"), hexc("#b7936a")
    P = 2.6
    for dx in (-0.9, 0.9):
        for dz in (-0.8, 0.8):
            a.tube([(x + dx * 1.15, y - 0.4, z + dz * 1.15), (x + dx, y + P, z + dz)], 0.07, "wood", wood, segs=5)
    for dz in (-0.8, 0.8):
        a.tube([(x - 1.0, y + 0.6, z + dz), (x + 1.0, y + 1.9, z + dz)], 0.04, "wood", wood, segs=4)
    for k in range(9):  # the deck: planks with gaps
        a.rbox((x - 1.1 + 2.2 * k / 8, y + P, z), (0.24, 0.12, 2.3), 0.02, "wood",
               mul(wood, 0.92 + 0.12 * ((k * 7) % 3) / 2))
    # the cabin: white clapboard with a red band, framed windows, a roof with an overhang and a ridge
    for k in range(6):
        a.rbox((x, y + P + 0.2 + 0.25 * k, z), (1.9, 0.26, 1.7), 0.03, "paint", mul(white, 0.95 + 0.05 * (k % 2)))
    a.rbox((x, y + P + 1.1, z + 0.86), (1.95, 0.35, 0.05), 0.02, "paint", red)
    a.box((x, y + P + 1.1, z - 0.86), (1.4, 0.45, 0.04), "paint", hexc("#3a5068"))
    for u in (-0.72, 0.72):
        a.rbox((x + u * 0.6, y + P + 0.7, z + 0.87), (0.5, 0.55, 0.04), 0.02, "paint", hexc("#f7f3ea"))
        a.box((x + u * 0.6, y + P + 0.7, z + 0.88), (0.38, 0.43, 0.03), "paint", hexc("#2e4660"))
    for u in (-0.95, 0.95):
        for w_ in (-0.85, 0.85):
            a.rbox((x + u, y + P + 0.8, z + w_), (0.1, 1.6, 0.1), 0.02, "paint", white)
    a.rbox((x, y + P + 1.62, z), (2.5, 0.1, 2.3), 0.03, "paint", red)
    a.rbox((x, y + P + 1.8, z), (1.8, 0.26, 1.7), 0.08, "paint", mul(red, 0.92))
    a.rbox((x, y + P + 1.97, z), (0.9, 0.1, 1.72), 0.04, "paint", white)
    # the railing and the ramp
    for k in range(9):
        a.box((x - 1.1 + 2.2 * k / 8, y + P + 0.4, z + 1.05), (0.05, 0.7, 0.05), "paint", white)
    a.box((x, y + P + 0.75, z + 1.05), (2.25, 0.06, 0.06), "paint", white)
    for k in range(8):
        t = k / 7
        a.box((x + 1.25 + 1.6 * t, y + P * (1 - t) + 0.02, z + 0.4), (0.26, 0.05, 0.8), "wood", mul(wood, 0.9))
    a.tube([(x + 1.2, y + P, z + 0.8), (x + 2.9, y, z + 0.8)], 0.035, "wood", wood, segs=4)
    # a lifebuoy on the front and the flag on a mast
    ring = []
    for k in range(13):
        ang = 2 * math.pi * k / 12
        ring.append((x + 0.55 + 0.26 * math.cos(ang), y + P + 0.55 + 0.26 * math.sin(ang), z + 0.9))
    a.tube(ring, 0.07, "paint", lambda i, p: red if (i // 3) % 2 == 0 else white, segs=6)
    a.tube([(x - 0.7, y + P + 1.6, z - 0.5), (x - 0.7, y + P + 3.6, z - 0.5)], 0.03, "metal", hexc("#dcdcdc"), segs=4)
    top = y + P + 3.55
    for i in range(6):
        u0, u1 = i / 6 * 1.2, (i + 1) / 6 * 1.2
        for band, col in ((0, red), (1, hexc("#f5d33a"))):
            ya, yb = top - band * 0.36, top - (band + 1) * 0.36
            a.poly([(x - 0.7 + u0, ya, z - 0.5), (x - 0.7 + u1, ya, z - 0.5), (x - 0.7 + u1, yb, z - 0.5),
                    (x - 0.7 + u0, yb, z - 0.5)], "flag_sway", col,
                   uvs=[(u0, ya - y), (u1, ya - y), (u1, yb - y), (u0, yb - y)])


def scoreboard(sc, a, c, ry):
    """A beach scoreboard: two posts, a slatted frame and a blank dark board (the game writes the score on it:
    the empty score_board sits at the board's centre, facing along +z turned by ry; the board is 2.8 x 1.5)."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)

    def P(u, v, s=0.0):
        return (x + u * cr + s * sr, y + v, z - u * sr + s * cr)
    wood, wood2 = hexc("#a47b52"), hexc("#c49a6c")
    for u in (-1.35, 1.35):
        a.rbox(P(u, 1.9), (0.18, 4.6, 0.18), 0.03, "wood", wood, ry=ry)
        a.lathe(P(u, 4.2), [(0.13, 0), (0.0, 0.16)], 4, "wood", wood2, cap=False, phase=math.pi / 4 - ry)
        for v in (2.35, 3.85):  # rope lashings where the frame meets the posts
            a.lathe(P(u, v), [(0.115, 0), (0.115, 0.1)], 8, "thatch", hexc("#d8c08a"), cap=False)
    B, BW, BH = 3.1, 2.8, 1.5
    for v, hh in ((B + BH / 2 + 0.12, 0.14), (B - BH / 2 - 0.12, 0.14)):
        a.rbox(P(0, v, -0.04), (BW + 0.5, hh, 0.12), 0.03, "wood", wood2, ry=ry)
    for u in (-(BW / 2 + 0.12), BW / 2 + 0.12):
        a.rbox(P(u, B, -0.04), (0.14, BH + 0.1, 0.12), 0.03, "wood", wood2, ry=ry)
    a.box(P(0, B, -0.08), (BW + 0.1, BH + 0.1, 0.06), "wood", mul(wood, 0.8), ry=ry)
    a.box(P(0, B, 0.0), (BW, BH, 0.04), "board", hexc("#1d3a4a"), ry=ry)
    a.box(P(0, B, 0.03), (0.04, BH * 0.85, 0.02), "paint", hexc("#e8e2cc"), ry=ry)
    # a little sun-bleached sign board on top and palm-leaf thatch
    a.box(P(0, B + BH / 2 + 0.42, -0.02), (1.8, 0.42, 0.08), "paint", hexc("#f2c94a"), ry=ry)
    for u in (-0.9, 0.9):
        a.box(P(u * 0.5, B + BH / 2 + 0.42, 0.03), (0.5, 0.1, 0.02), "paint", hexc("#e0663a"), ry=ry)
    sc.empty_rot = getattr(sc, "empty_rot", {})
    sc.empty("score_board", P(0, B, 0.05))
    sc.empty_rot["score_board"] = ry


def bonfire(sc, a, c, rng):
    x, y, z = c
    for k in range(10):
        ang = 2 * math.pi * k / 10
        rock(a, (x + math.cos(ang) * 0.75, y, z + math.sin(ang) * 0.6), (0.2, 0.16, 0.18), rng, hexc("#9a8f84"),
             hexc("#5e554e"))
    for k in range(5):
        ang = 2 * math.pi * k / 5 + 0.3
        a.tube([(x + math.cos(ang) * 0.55, y + 0.02, z + math.sin(ang) * 0.45), (x, y + 0.75, z)], 0.07, "wood",
               lambda i, p: hexc("#6a4a30") if i == 0 else hexc("#2f2520"), segs=5)
    a.blob((x, y, z), (0.5, 0.1, 0.4), "ember_glow", (1.0, 0.45, 0.15), segs=8, rings=2, rough=0.3, cut=0.0)
    flame(sc, "bonfire_flame", (x, y + 0.05, z), 1.3, 0.5)
    sc.empty("light_fire", (x, y + 1.0, z))
    sc.empty("smoke_fire", (x, y + 1.3, z))
    # logs to sit on
    for dx, dz, r in ((-1.6, 0.2, 0.4), (1.5, -0.3, -0.5)):
        a.tube([(x + dx - 0.6 * math.cos(r), y + 0.14, z + dz - 0.6 * math.sin(r)),
                (x + dx + 0.6 * math.cos(r), y + 0.14, z + dz + 0.6 * math.sin(r))], 0.15, "wood", hexc("#8a6a48"),
               segs=7, cap=True)


def tiki_bar(sc, a, c, rng, lights):
    """A tiki bar: bamboo posts with nodes, a counter faced with bamboo, stools, a carved tiki post, bottles, a sign,
    and a shaggy roof: a thatched cone with three tiers of ragged straw fringe."""
    x, y, z = c
    pr = random.Random(77)
    wood = hexc("#9a7048")
    thatch, thatch2, thatch3 = hexc("#dcbc72"), hexc("#b58e48"), hexc("#8e6c38")

    def bamboo(p0, p1, r, col=hexc("#c9a35c")):
        p0, p1 = Vector(p0), Vector(p1)
        L = (p1 - p0).length
        n = max(2, int(L / 0.45))
        pts = [tuple(p0.lerp(p1, k / n)) for k in range(n + 1)]
        a.tube(pts, r, "wood", lambda i, p: col if i % 2 else mul(col, 0.88), segs=6)
        for k in range(1, n):
            q = p0.lerp(p1, k / n)
            a.lathe(tuple(q - Vector((0, 0.02, 0))), [(r * 1.18, 0), (r * 1.18, 0.04)], 6, "wood", mul(col, 0.7),
                    cap=False)
    for dx in (-1.6, 1.6):
        for dz in (-1.0, 1.0):
            bamboo((x + dx, y - 0.3, z + dz), (x + dx, y + 2.5, z + dz), 0.08, hexc("#a88346"))
    a.rbox((x, y + 0.55, z + 0.9), (3.4, 1.1, 0.35), 0.03, "wood", hexc("#7a5234"))
    a.rbox((x, y + 1.14, z + 0.95), (3.7, 0.08, 0.6), 0.03, "wood", hexc("#c49a6c"))
    for k in range(13):  # bamboo facing on the counter
        bamboo((x - 1.68 + 3.36 * k / 12, y, z + 1.08), (x - 1.68 + 3.36 * k / 12, y + 1.1, z + 1.08), 0.045)
    # stools
    for k in range(3):
        sx = x - 1.0 + k
        for ang in (0.4, 2.5, 4.6):
            a.tube([(sx + math.cos(ang) * 0.14, y, z + 1.55 + math.sin(ang) * 0.14), (sx, y + 0.62, z + 1.55)], 0.025,
                   "wood", hexc("#8a6440"), segs=4)
        a.lathe((sx, y + 0.62, z + 1.55), [(0.2, 0), (0.21, 0.04), (0.19, 0.08), (0.0, 0.085)], 10, "fabric",
                [hexc("#e8402c"), hexc("#ffd24a"), hexc("#1fb5a8")][k])
    # a carved tiki post by the counter: stacked face, brows, eyes, a wide mouth
    tx, tz = x + 2.1, z + 1.3
    a.rbox((tx, y + 0.8, tz), (0.42, 1.9, 0.42), 0.07, "wood", hexc("#8a5a34"))
    for v, col, sz in ((1.45, hexc("#5a3a22"), (0.44, 0.08, 0.46)), (1.15, hexc("#f2e6c8"), (0.1, 0.1, 0.46)),
                       (0.78, hexc("#3a2616"), (0.3, 0.12, 0.46)), (0.3, hexc("#5a3a22"), (0.46, 0.06, 0.46))):
        a.box((tx, y + v, tz + 0.01), sz, "paint", col)
    for s_ in (-1, 1):
        a.box((tx + s_ * 0.1, y + 1.15, tz + 0.02), (0.1, 0.1, 0.46), "paint", hexc("#f2e6c8"))
        a.box((tx + s_ * 0.1, y + 1.15, tz + 0.03), (0.04, 0.05, 0.46), "paint", hexc("#1a1210"))
    # the roof: a steep cone under the fringe
    apex = (x, y + 3.9, z)
    R = 3.0
    NS = 16
    for k in range(NS):
        a0, a1 = 2 * math.pi * k / NS, 2 * math.pi * (k + 1) / NS
        p0 = (x + math.cos(a0) * R * 0.95, y + 2.45, z + math.sin(a0) * R * 0.66)
        p1 = (x + math.cos(a1) * R * 0.95, y + 2.45, z + math.sin(a1) * R * 0.66)
        a.poly([p0, p1, apex], "thatch", [thatch2, thatch2, thatch], out=(x, y, z))
    # the fringe: three tiers of ragged straw strips hanging from rings round the cone
    for tier, (ty, tr, drop) in enumerate(((2.45, 1.0, 0.55), (3.0, 0.62, 0.45), (3.5, 0.3, 0.35))):
        NF = 44 - tier * 12
        for k in range(NF):
            a0, a1 = 2 * math.pi * k / NF, 2 * math.pi * (k + 1) / NF
            q0 = Vector((x + math.cos(a0) * R * tr * 1.02, y + ty, z + math.sin(a0) * R * tr * 0.7))
            q1 = Vector((x + math.cos(a1) * R * tr * 1.02, y + ty, z + math.sin(a1) * R * tr * 0.7))
            outv = Vector((math.cos((a0 + a1) / 2), 0, math.sin((a0 + a1) / 2))) * 0.12
            dd = drop * pr.uniform(0.75, 1.15)
            m = (q0 + q1) / 2 + outv - Vector((0, dd, 0))
            m0 = q0 + outv * 0.8 - Vector((0, dd * pr.uniform(0.6, 0.9), 0))
            m1 = q1 + outv * 0.8 - Vector((0, dd * pr.uniform(0.6, 0.9), 0))
            col = [thatch, thatch2, mix(thatch, thatch3, 0.4)][pr.randint(0, 2)]
            a.poly([tuple(q0), tuple(q1), tuple(m1), tuple(m), tuple(m0)], "thatch",
                   [mul(col, 1.05), mul(col, 1.05), mul(col, 0.85), mul(col, 0.8), mul(col, 0.85)], out=(x, y + ty + 1, z))
    # a sign and bottles
    a.rbox((x, y + 2.1, z + 1.25), (1.8, 0.4, 0.06), 0.03, "wood", hexc("#2a9d8f"))
    for k in range(5):
        a.box((x - 0.7 + k * 0.35, y + 2.1, z + 1.29), (0.2, 0.2, 0.02), "paint",
              [hexc("#ffd24a"), hexc("#ff7a45"), hexc("#ff4f7b"), hexc("#fff0c8"), hexc("#ffd24a")][k], ry=0.78)
    for k in range(7):
        a.lathe((x - 1.2 + k * 0.4, y + 1.18, z + 0.4), [(0.06, 0), (0.06, 0.2), (0.025, 0.26), (0.02, 0.34)], 7, "gloss",
                [hexc("#3cb371"), hexc("#f2a33a"), hexc("#e05a8a"), hexc("#5aa9e6")][k % 4])
    lantern_string(a, (x - 1.6, y + 2.35, z + 1.0), (x + 1.6, y + 2.35, z + 1.0), 0.25, 5,
                   [hexc("#ff7a45"), hexc("#ffd24a"), hexc("#ff4f7b")], rng, lights)


def crab(sc, name, c, ry, col):
    """A little beach crab, origin at its feet (the game scuttles it sideways and bobs its claws)."""
    a = sc.acc(name, c, ry)
    x, y, z = c
    dark = mul(col, 0.7)
    a.blob((x, y + 0.13, z), (0.2, 0.09, 0.15), "critter",
           lambda nx, ny, nz, q: mix(dark, mix(col, (1, 0.8, 0.6), 0.2), smooth(-0.3, 0.8, ny)), segs=9, rings=5,
           rough=0.05)
    for s in (-1, 1):
        for k in range(3):
            zz = z + s * (0.08 + 0.02 * k)
            xx = x - 0.1 + 0.1 * k
            a.tube([(xx, y + 0.12, zz), (xx + 0.02, y + 0.16, zz + s * 0.16), (xx + 0.04, y + 0.0, zz + s * 0.24)],
                   0.018, "critter", dark, segs=4)
        # claws, raised and forward (towards +x before the turn)
        a.tube([(x + 0.12, y + 0.14, z + s * 0.1), (x + 0.22, y + 0.24, z + s * 0.17)], 0.03, "critter", col, segs=5)
        a.blob((x + 0.28, y + 0.28, z + s * 0.19), (0.08, 0.06, 0.05), "critter", col, segs=7, rings=4, rough=0.05)
        # eyes on stalks
        a.tube([(x + 0.12, y + 0.18, z + s * 0.05), (x + 0.16, y + 0.29, z + s * 0.06)], 0.012, "critter", dark,
               segs=4)
        a.blob((x + 0.16, y + 0.3, z + s * 0.06), (0.025, 0.025, 0.025), "critter", hexc("#101010"), segs=5, rings=3,
               rough=0.0)


def gull(sc, name, c, ry, s=1.0):
    """A standing seagull, origin at its feet, facing +x before the turn."""
    a = sc.acc(name, c, ry)
    x, y, z = c
    white, grey, dark = hexc("#f8f8f4"), hexc("#a8b2bc"), hexc("#30343a")
    a.blob((x, y + 0.3 * s, z), (0.22 * s, 0.14 * s, 0.13 * s), "critter",
           lambda nx, ny, nz, q: mix(hexc("#dfe2e4"), white, smooth(-0.6, 0.3, ny)), segs=9, rings=5, rough=0.02)
    for sd in (-1, 1):
        a.blob((x - 0.04 * s, y + 0.34 * s, z + sd * 0.1 * s), (0.2 * s, 0.07 * s, 0.05 * s), "critter",
               lambda nx, ny, nz, q: mix(grey, dark, smooth(-0.12 * s, -0.22 * s, q[0] - x)), segs=7, rings=4,
               rough=0.02)
    a.poly([(x - 0.2 * s, y + 0.33 * s, z - 0.05 * s), (x - 0.2 * s, y + 0.33 * s, z + 0.05 * s),
            (x - 0.36 * s, y + 0.36 * s, z)], "critter", dark)
    a.blob((x + 0.17 * s, y + 0.5 * s, z), (0.085 * s, 0.08 * s, 0.075 * s), "critter", white, segs=8, rings=5,
           rough=0.0)
    a.tube([(x + 0.24 * s, y + 0.5 * s, z), (x + 0.36 * s, y + 0.48 * s, z)], [0.022 * s, 0.008 * s], "critter",
           hexc("#f2c230"), segs=5)
    for sd in (-1, 1):
        a.blob((x + 0.22 * s, y + 0.53 * s, z + sd * 0.055 * s), (0.014 * s,) * 3, "critter", hexc("#101010"),
               segs=4, rings=3, rough=0.0)
        a.tube([(x, y + 0.2 * s, z + sd * 0.04 * s), (x + 0.01 * s, y, z + sd * 0.05 * s)], 0.012 * s, "critter",
               hexc("#f08a3a"), segs=4)
        a.poly([(x + 0.01 * s, y + 0.003, z + sd * 0.05 * s), (x + 0.09 * s, y + 0.003, z + sd * 0.09 * s),
                (x + 0.09 * s, y + 0.003, z + sd * 0.01 * s)], "critter", hexc("#f08a3a"))


def shell(a, c, col, rng):
    """A scallop (a ribbed fan with a hinge) or, one time in three, a little spiral whelk."""
    x, y, z = c
    ang = rng.uniform(0, 2 * math.pi)
    ca, sa = math.cos(ang), math.sin(ang)
    if rng.random() < 0.33:
        pts, rad = [], []
        for k in range(7):
            t = k / 6
            r = 0.05 * (1 - t) + 0.008
            pts.append((x + (t * 0.14 - 0.07) * ca + 0.012 * math.sin(k * 2.1) * sa, y + 0.03 * (1 - t) + 0.02,
                        z - (t * 0.14 - 0.07) * sa + 0.012 * math.cos(k * 2.1) * ca))
            rad.append(r)
        a.tube(pts, rad, "paint", lambda i, p: mix(mul(col, 0.75), col, (i % 2) * 0.8), segs=6, cap=True)
        return
    hinge = a.vert((x - 0.05 * ca, y + 0.012, z + 0.05 * sa))
    ribs = 9
    prev = None
    for k in range(ribs + 1):
        t = -1.0 + 2.0 * k / ribs
        th = ang + t * 1.1
        edge = (x + math.cos(th) * 0.08, y + 0.02 + (0.012 if k % 2 == 0 else 0.0), z - math.sin(th) * 0.08)
        mid = (x + math.cos(th) * 0.045, y + 0.03 + (0.008 if k % 2 == 0 else 0.0), z - math.sin(th) * 0.045)
        e, m = a.vert(edge), a.vert(mid)
        if prev:
            pe, pm = prev
            cB = mix(mul(col, 0.8), col, 0.5 + 0.5 * (k % 2))
            a.face([hinge, pm, m], "paint", [mul(col, 1.05), cB, cB], out=(x, y - 1, z))
            a.face([pm, pe, e, m], "paint", [cB, mul(cB, 0.9), mul(cB, 0.9), cB], out=(x, y - 1, z))
        prev = (e, m)


def starfish(a, c, col, ry):
    """A plump five-armed starfish: arms with a raised ridge, a darker rim and pale bumps along the top."""
    x, y, z = c
    cid = a.vert((x, y + 0.05, z))
    ridge, rim = [], []
    for k in range(10):
        ang = ry + math.pi * k / 5
        arm = k % 2 == 0
        r = 0.17 if arm else 0.06
        rim.append(a.vert((x + math.cos(ang) * r, y + 0.006, z + math.sin(ang) * r)))
        rr = 0.13 if arm else 0.045
        ridge.append(a.vert((x + math.cos(ang) * rr, y + (0.03 if arm else 0.04), z + math.sin(ang) * rr)))
    pale = mix(col, (1, 0.95, 0.85), 0.45)
    for k in range(10):
        j = (k + 1) % 10
        a.face([ridge[k], ridge[j], cid], "paint", [pale if k % 2 == 0 else col, pale if j % 2 == 0 else col,
                                                    mix(col, pale, 0.5)], out=(x, y - 1, z))
        a.face([rim[k], rim[j], ridge[j], ridge[k]], "paint", [mul(col, 0.75), mul(col, 0.75), col, col],
               out=(x, y - 1, z))


def sandcastle(a, c, rng, flags=None):
    """A sandcastle: a crenellated keep, three round towers with pointed or crenellated tops, walls between them, a
    doorway, a moat of wet sand, shells pressed into the walls and a paper flag on the keep (flag_sway)."""
    x, y, z = c
    sand, wet, dark = hexc("#e9cf9c"), hexc("#b89868"), hexc("#8a6a48")
    rs = random.Random(int(x * 100) + int(z * 10))

    def sc_col(px, py, pz):
        return mul(sand, 0.9 + 0.12 * n2(px * 6, py * 6 + pz * 6, 1.0, 17))
    # the moat: a ring of wet sand
    for k in range(18):
        a0, a1 = 2 * math.pi * k / 18, 2 * math.pi * (k + 1) / 18
        pts = [(x + math.cos(a0) * 0.95, y + 0.004, z + math.sin(a0) * 0.95),
               (x + math.cos(a1) * 0.95, y + 0.004, z + math.sin(a1) * 0.95),
               (x + math.cos(a1) * 0.7, y + 0.012, z + math.sin(a1) * 0.7),
               (x + math.cos(a0) * 0.7, y + 0.012, z + math.sin(a0) * 0.7)]
        a.poly(pts, "sand", [mix(wet, sand, 0.4), mix(wet, sand, 0.4), wet, wet], out=(x, y - 100, z), sm=True)
    # the keep: a square block with merlons
    a.rbox((x, y + 0.25, z), (0.5, 0.5, 0.5), 0.03, "sand", sand, cols=(mul(sand, 1.04), mul(sand, 0.94)))
    for i in range(3):
        for sgn in (-1, 1):
            u = -0.2 + 0.2 * i
            a.box((x + u, y + 0.55, z + sgn * 0.21), (0.09, 0.1, 0.08), "sand", sand)
            a.box((x + sgn * 0.21, y + 0.55, z + u), (0.08, 0.1, 0.09), "sand", sand)
    a.box((x, y + 0.12, z + 0.26), (0.14, 0.22, 0.03), "sand", dark)
    towers = [(-0.48, 0.28, 0.16, 0.5), (0.46, 0.3, 0.14, 0.45), (0.0, -0.46, 0.15, 0.62)]
    for k, (dx, dz, r, hh) in enumerate(towers):
        tx, tz = x + dx, z + dz
        a.lathe((tx, y, tz), [(r * 1.1, 0), (r, hh * 0.4), (r * 0.95, hh)], 10, "sand", sc_col, sm=True, cap=True)
        if k == 2:
            for m in range(6):
                ang = 2 * math.pi * m / 6
                a.box((tx + math.cos(ang) * r * 0.85, y + hh + 0.05, tz + math.sin(ang) * r * 0.85), (0.06, 0.1, 0.06),
                      "sand", sand, ry=-ang)
        else:
            a.lathe((tx, y + hh, tz), [(r * 1.05, 0), (0.0, r * 1.6)], 10, "sand", mul(sand, 1.03), sm=False)
        a.box((tx, y + hh * 0.6, tz + r * 0.95), (0.05, 0.07, 0.02), "sand", dark)
    # walls from the towers to the keep
    for dx, dz, _r, _h in towers:
        p0, p1 = Vector((x + dx, 0, z + dz)), Vector((x, 0, z))
        L = (p1 - p0).length
        mid = (p0 + p1) / 2
        ang = math.atan2(-(p1 - p0).z, (p1 - p0).x)
        a.box((mid.x, y + 0.12, mid.z), (L, 0.24, 0.1), "sand", sand, ry=ang)
    for k in range(4):
        ang = rs.uniform(0, 2 * math.pi)
        shell(a, (x + math.cos(ang) * 0.6, y + 0.01, z + math.sin(ang) * 0.6),
              rs.choice([hexc("#f6d0c4"), hexc("#fbeee0"), hexc("#f2b8a0")]), rs)
    if flags is not None:
        flags.tube([(x, y + 0.5, z), (x, y + 0.95, z)], 0.008, "wood", hexc("#e8dcc0"), segs=3)
        flags.poly([(x, y + 0.95, z), (x, y + 0.8, z), (x + 0.2, y + 0.875, z)], "flag_sway", hexc("#ff4f7b"),
                   uvs=[(0.0, 0.95), (0.0, 0.8), (0.2, 0.875)])


def cooler(a, c, ry, col):
    """A picnic cooler: a rounded body, a white lid with a lip, a carrying handle and a latch."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)

    def P(u, v, s):
        return (x + u * cr + s * sr, y + v, z - u * sr + s * cr)
    a.rbox(P(0, 0.2, 0), (0.7, 0.4, 0.45), 0.05, "paint", col, ry=ry)
    a.rbox(P(0, 0.44, 0), (0.74, 0.09, 0.49), 0.035, "paint", hexc("#f7f3ea"), ry=ry)
    a.rbox(P(0, 0.34, 0.235), (0.14, 0.08, 0.03), 0.01, "paint", hexc("#f7f3ea"), ry=ry)
    a.tube([P(-0.28, 0.46, 0), P(-0.24, 0.56, 0), P(0.24, 0.56, 0), P(0.28, 0.46, 0)], 0.018, "paint",
           hexc("#dcdcd6"), segs=5)
    a.rbox(P(0, 0.2, 0.23), (0.5, 0.2, 0.01), 0.004, "paint", mul(col, 0.8), ry=ry)


def bucket(a, c, col):
    """A child's sand bucket with a rolled rim and a handle, and a spade leaning on it."""
    x, y, z = c
    a.lathe((x, y, z), [(0.0, 0.0), (0.13, 0.0), (0.18, 0.28), (0.195, 0.3), (0.19, 0.32), (0.17, 0.31)], 10, "gloss",
            col, cap=False)
    a.lathe((x, y + 0.02, z), [(0.0, 0.0), (0.13, 0.0)], 10, "sand", hexc("#e0c490"), cap=False)
    a.tube([(x - 0.19, y + 0.3, z), (x - 0.12, y + 0.46, z), (x + 0.12, y + 0.46, z), (x + 0.19, y + 0.3, z)], 0.008,
           "paint", hexc("#ffd24a"), segs=4)
    a.tube([(x + 0.1, 0.05, z + 0.3), (x + 0.4, 0.55, z + 0.2)], 0.018, "gloss", hexc("#ffd24a"), segs=5)
    a.rbox((x + 0.07, 0.07, z + 0.31), (0.16, 0.22, 0.02), 0.01, "gloss", hexc("#ffd24a"), rx=0.2, ry=0.3)


def posts(sc, a, xs):
    """A short row of old weathered mooring posts at the water's edge (gulls land on them: perch_<i> empties)."""
    k = 0
    for x, z, hh in xs:
        yb = h_land(x, z)
        top = yb + hh
        a.tube([(x, yb - 0.5, z), (x + 0.02, top - 0.05, z)], [0.11, 0.1], "wood",
               lambda i, p: hexc("#7a6a58") if i == 0 else hexc("#9a8a74"), segs=8)
        a.lathe((x + 0.02, top - 0.06, z), [(0.1, 0.0), (0.08, 0.06), (0.0, 0.08)], 8, "wood", hexc("#a89a84"),
                cap=False)
        # a wet dark band and barnacles at the foot
        a.lathe((x, yb - 0.02, z), [(0.125, 0.0), (0.115, 0.3)], 8, "rock", hexc("#4e4a42"), cap=False)
        for m in range(5):
            ang = 2 * math.pi * m / 5 + x
            a.blob((x + math.cos(ang) * 0.11, yb + 0.1 + 0.05 * (m % 2), z + math.sin(ang) * 0.11), (0.03, 0.025, 0.03),
                   "rock", hexc("#d8d2c4"), segs=5, rings=3, rough=0.2)
        sc.empty("perch_%d" % k, (x + 0.02, top + 0.02, z))
        k += 1


# ------------------------------------------------------------------ the whole beach

def beach(sc):
    rng = random.Random(24)
    build_land(sc, rng)
    build_sea(sc)
    build_court(sc, rng)

    def Y(x, z):
        return h_land(x, z)

    # palms: big ones framing the court, more behind on the dunes (sides only: the middle stays open)
    pl = sc.acc("near_palms")
    palms = [(-5.4, -1.2, 9.5, (0.34, -0.06)), (21.6, -1.8, 10.0, (-0.3, -0.05)), (-9.0, -9.5, 8.0, (0.18, 0.08)),
             (-13.0, -4.5, 9.0, (0.22, 0.02)), (24.5, -8.5, 8.5, (-0.2, 0.06)), (28.5, -4.0, 9.5, (-0.25, 0.0)),
             (-16.5, -13.5, 7.5, (0.1, 0.1)), (31.0, -14.0, 7.0, (-0.12, 0.1)), (-20.0, -7.0, 10.0, (0.18, -0.02)),
             (35.0, -8.0, 10.5, (-0.2, 0.0)), (-7.5, -16.8, 6.0, (0.28, 0.16)), (23.5, -16.5, 6.5, (-0.26, 0.2))]
    tops = []
    for x, z, H, lean in palms:
        green = mix(hexc("#2f8f3a"), hexc("#5aa83c"), rng.random())
        tops.append(palm(pl, (x, Y(x, z), z), H, lean, rng, fronds=rng.randint(9, 11), green=green))
    # where the occasional coconut falls from (the game drops one now and then): palms behind the side props
    for i in (2, 4):
        sc.empty("coco_%d" % i, tuple(tops[i] + Vector((0.2, -0.45, 0.25))))
    far_p = sc.acc("far_palms")
    for i in range(60):
        side = -1 if i % 2 == 0 else 1
        z = rng.uniform(-24, -95)
        x = (rng.uniform(-60, -24) - 0.3 * (-z - 24)) if side < 0 else (rng.uniform(40, 80) + 0.25 * (-z - 24))
        y = Y(x, z)
        if y < SEA + 0.4:
            continue
        palm(far_p, (x, y - 0.2, z), rng.uniform(6, 11), (rng.uniform(-0.15, 0.15), rng.uniform(-0.1, 0.1)), rng,
             fronds=7, green=mix(hexc("#27773a"), hexc("#4f9c42"), rng.random()), coco=False, lod=True)
    jungle = sc.acc("far_jungle")
    for i in range(160):
        side = -1 if i % 2 == 0 else 1
        z = rng.uniform(-30, -160)
        x = (rng.uniform(-110, -22) - 0.3 * (-z - 24)) if side < 0 else (rng.uniform(42, 120) + 0.25 * (-z - 24))
        y = Y(x, z)
        if y < 1.0:
            continue
        r = rng.uniform(1.6, 3.6)
        g = mix(hexc("#1f6a34"), hexc("#4c9a3c"), rng.random())

        def cc(nx, ny, nz, q, g=g):
            return mix(mul(g, 0.65), mul(g, 1.3), smooth(-0.5, 0.9, ny + 0.3 * nz))
        jungle.blob((x, y + r * 0.5, z), (r, r * 0.8, r), "foliage_sway", cc, segs=7, rings=4, rough=0.25,
                    seed=rng.random() * 30)

    # props on the left: scoreboard, flag, torch, umbrella, towels, a chair, board, the bonfire, the tiki bar
    lights = []
    pr = sc.acc("near_props")
    scoreboard(sc, pr, (-4.3, Y(-4.3, -4.8), -4.8), 0.28)
    fl = sc.acc("near_flags")
    feather_flag(fl, (-2.0, Y(-2.0, -10.5), -10.5), 3.6, hexc("#ff4f7b"), hexc("#ffd24a"))
    feather_flag(fl, (19.6, Y(19.6, -10.0), -10.0), 3.6, hexc("#1fb5a8"), hexc("#ffd24a"))
    tr = sc.acc("near_torches")
    torch(sc, tr, 0, (-1.3, Y(-1.3, -4.2), -4.2))
    torch(sc, tr, 1, (17.3, Y(17.3, -4.2), -4.2))
    torch(sc, tr, 2, (-3.6, Y(-3.6, 1.8), 1.8), H=1.7)
    torch(sc, tr, 3, (19.6, Y(19.6, 1.6), 1.6), H=1.7)
    umbrella(pr, (-7.6, Y(-7.6, -6.5), -6.5), 1.5, [hexc("#e8402c"), hexc("#f7f3ea")], tilt=(0.1, 0.0))
    umbrella(pr, (-11.5, Y(-11.5, -10.5), -10.5), 1.4, [hexc("#ffc93a"), hexc("#1fb5a8")], tilt=(0.08, 0.05))
    umbrella(pr, (22.8, Y(22.8, -5.0), -5.0), 1.5, [hexc("#2f7fe0"), hexc("#f7f3ea")], tilt=(-0.1, 0.0))
    umbrella(pr, (27.0, Y(27.0, -11.0), -11.0), 1.4, [hexc("#ff7a45"), hexc("#ff4f7b"), hexc("#f7f3ea")],
             tilt=(-0.05, 0.05))
    towel(pr, (-7.2, 0, -5.4), 0.9, 1.9, 0.3, [hexc("#ffd24a"), hexc("#ff7a45"), hexc("#ff4f7b"), hexc("#ff7a45"),
                                               hexc("#ffd24a")])
    towel(pr, (-10.8, 0, -9.0), 0.9, 1.9, -0.2, [hexc("#1fb5a8"), hexc("#f7f3ea")] * 3)
    towel(pr, (22.0, 0, -3.8), 0.9, 1.9, -0.35, [hexc("#7a5cd6"), hexc("#f7f3ea"), hexc("#7a5cd6"), hexc("#ffd24a"),
                                                 hexc("#7a5cd6")])
    towel(pr, (26.2, 0, -9.6), 0.9, 1.9, 0.25, [hexc("#e8402c"), hexc("#f7f3ea")] * 3)
    deck_chair(pr, (-8.4, Y(-8.4, -7.2), -7.2), 0.5, hexc("#1f74d6"))
    deck_chair(pr, (23.8, Y(23.8, -6.0), -6.0), math.pi - 0.5, hexc("#e8402c"))
    surfboard(pr, (-3.3, Y(-3.3, -7.8), -7.8), 0.0, 0.08, hexc("#ffd24a"), hexc("#ff4f7b"))
    surfboard(pr, (-2.5, Y(-2.5, -8.3), -8.3), 0.2, -0.05, hexc("#1fb5a8"), hexc("#f7f3ea"))
    surfboard(pr, (19.6, Y(19.6, -7.6), -7.6), -0.2, -0.07, hexc("#ff7a45"), hexc("#2f7fe0"))
    bonfire(sc, pr, (-6.2, Y(-6.2, -13.0), -13.0), rng)
    tiki_bar(sc, pr, (-14.2, Y(-14.2, -9.0), -9.0), rng, lights)
    # a cooler, a bucket and spade, shells, starfish, a sandcastle in the front corners
    cooler(pr, (-2.3, Y(-2.3, -1.0), -1.0), 0.3, hexc("#2f7fe0"))
    bucket(pr, (18.6, Y(18.6, 2.6), 2.6), hexc("#ff4f7b"))
    sandcastle(pr, (-2.4, Y(-2.4, 3.8), 3.8), rng, fl)
    for i in range(18):
        x = rng.choice([rng.uniform(-3.5, -0.6), rng.uniform(16.6, 19.5)])
        z = rng.uniform(-3, 4.5)
        shell(pr, (x, Y(x, z), z), rng.choice([hexc("#f6d0c4"), hexc("#fbeee0"), hexc("#f2b8a0")]), rng)
    starfish(pr, (-1.2, Y(-1.2, 3.2), 3.2), hexc("#ff7a45"), 0.3)
    starfish(pr, (17.5, Y(17.5, 4.0), 4.0), hexc("#e8402c"), 1.1)

    # the right: the lifeguard tower, a row of beach huts on the dune
    lt = sc.acc("near_tower")
    lifeguard_tower(sc, lt, (21.8, Y(21.8, -11.5), -11.5), rng)
    hu = sc.acc("near_huts")
    for i, (wall, roof) in enumerate(((hexc("#ff8fab"), hexc("#e8402c")), (hexc("#7fd6c8"), hexc("#1f74d6")),
                                      (hexc("#ffd24a"), hexc("#ff7a45")), (hexc("#9ec9ff"), hexc("#2f7fe0")),
                                      (hexc("#c6a0ff"), hexc("#7a5cd6")))):
        x = 27.5 + i * 2.6
        z = -18.0 + i * 0.35
        hut(hu, (x, Y(x, z), z), 2.0, 1.8, 2.3, wall, hexc("#fbfbf6"), roof, ry=-0.12)

    # string lights and bunting, at the sides only
    ls = sc.acc("near_lanterns")
    lcols = [hexc("#ff7a45"), hexc("#ffd24a"), hexc("#ff4f7b"), hexc("#7fd6c8"), hexc("#fff0c8")]
    lantern_string(ls, (tops[0].x - 0.3, tops[0].y - 1.6, tops[0].z), (tops[3].x + 0.2, tops[3].y - 1.8, tops[3].z),
                   1.0, 9, lcols, rng, lights)
    lantern_string(ls, (tops[1].x + 0.3, tops[1].y - 1.6, tops[1].z), (tops[5].x - 0.2, tops[5].y - 1.8, tops[5].z),
                   1.0, 9, lcols, rng, lights)
    lantern_string(ls, (tops[2].x, tops[2].y - 1.5, tops[2].z), (tops[6].x, tops[6].y - 1.2, tops[6].z), 0.8, 7,
                   lcols, rng, lights)
    bu = sc.acc("near_bunting")
    bcols = [hexc("#ff4f7b"), hexc("#ffd24a"), hexc("#1fb5a8"), hexc("#2f7fe0"), hexc("#ff7a45")]
    bunting(bu, (-2.0, Y(-2.0, -10.5) + 3.4, -10.5), (tops[0].x + 0.2, tops[0].y - 2.4, tops[0].z), 0.5, 12, bcols, rng)
    bunting(bu, (19.6, Y(19.6, -10.0) + 3.4, -10.0), (tops[1].x - 0.2, tops[1].y - 2.4, tops[1].z), 0.5, 12, bcols, rng)
    bunting(bu, (21.8, Y(21.8, -11.5) + 6.1, -11.5), (tops[4].x, tops[4].y - 1.4, tops[4].z), 0.6, 10, bcols, rng)
    for i, p in enumerate(lights):
        sc.empty("light_lantern_%d" % i, p)

    # rocks at the waterline on both sides, dune grass
    rk = sc.acc("near_rocks")
    for x, z, s in ((-10.5, -20.0, 1.3), (-12.8, -21.5, 2.0), (-8.6, -21.0, 0.8), (-15.5, -19.5, 1.1),
                    (26.0, -21.5, 1.4), (28.5, -22.5, 2.1), (24.0, -21.0, 0.7), (-4.2, 5.5, 0.7),
                    (20.8, 5.0, 0.9), (-5.0, -3.0, 0.45)):
        at_sea = z < -18.0
        rock(rk, (x, Y(x, z) - 0.15 * s, z), (s * 1.3, s * 0.8, s), rng, hexc("#c4b6a2"), hexc("#6e645c"),
             wet=(SEA + 0.15) if at_sea else None)
    posts(sc, sc.acc("near_posts"), [(-3.2, -18.9, 1.35), (-2.35, -19.35, 1.0), (-1.5, -19.9, 1.6)])
    gr = sc.acc("near_grass")
    for i in range(110):
        side = rng.choice((-1, 1))
        x = 8 + side * rng.uniform(13.5, 30)
        z = rng.uniform(-16, 6)
        if Y(x, z) < 0.05 and rng.random() < 0.6:
            continue
        tuft(gr, (x, Y(x, z) - 0.05, z), rng.uniform(0.4, 0.8), hexc("#7f9a44"), hexc("#d2d27e"), rng, blades=6)

    # distant islands and sails, clouds (sides of the sky more than the middle)
    far = sc.acc("far_islands")
    for x, z, w, hh in ((-190, -520, 80, 18), (-95, -640, 36, 9), (210, -560, 90, 22), (120, -700, 40, 8),
                        (30, -900, 30, 4)):
        far.blob((x, SEA - 1.5, z), (w, hh, w * 0.35), "sand",
                 lambda nx, ny, nz, q: mix(hexc("#5f8f76"), hexc("#8fb38e"), ny), segs=14, rings=4, rough=0.2,
                 nscale=0.5, seed=x, cut=0.0)
        far.blob((x, SEA - 0.8, z + w * 0.3), (w * 1.05, 1.2, w * 0.1), "sand", hexc("#e7d7b0"), segs=12, rings=2,
                 rough=0.1, cut=0.0)
    for i, (x, z, s) in enumerate(((-46.0, -130.0, 1.0), (70.0, -190.0, 1.3), (-120.0, -330.0, 1.8))):
        b = sc.acc("boat_%d" % i, (x, SEA, z))
        b.lathe((x, SEA - 0.3, z), [(0.0, 0), (0.6 * s, 0.1), (0.75 * s, 0.6 * s)], 8, "paint", hexc("#f7f5ef"),
                sx=2.6, sm=True, cap=True)
        b.tube([(x, SEA + 0.5, z), (x, SEA + 6.5 * s, z)], 0.07 * s, "wood", hexc("#8a6a4a"), segs=4)
        b.poly([(x + 0.15, SEA + 1.0 * s, z), (x + 0.15, SEA + 6.2 * s, z), (x + 2.9 * s, SEA + 1.1 * s, z)],
               "paint", hexc("#fbf6ec"))
        b.poly([(x - 0.15, SEA + 1.2 * s, z), (x - 0.15, SEA + 5.2 * s, z), (x - 2.1 * s, SEA + 1.2 * s, z)],
               "paint", [hexc("#ff4f7b"), hexc("#ffd24a"), hexc("#1fb5a8")][i])
    for i in range(9):
        x = [-190, -140, -90, 110, 160, 220, -40, 60, 0][i] + rng.uniform(-15, 15)
        y = rng.uniform(55, 95) if i < 6 else rng.uniform(95, 130)
        cloud(sc, "cloud_%d" % i, (x, y, rng.uniform(-320, -420)), rng.uniform(11, 17) * (0.7 if i >= 6 else 1.0),
              rng, under=hexc("#c3d2e6"))

    # the critters: crabs in the front corners and by the water, gulls perched and standing about
    crab(sc, "crab_0", (-1.8, Y(-1.8, 2.4), 2.4), 0.2, hexc("#f06038"))
    crab(sc, "crab_1", (18.2, Y(18.2, 3.1), 3.1), -0.3, hexc("#ff7a45"))
    crab(sc, "crab_2", (-3.8, Y(-3.8, -15.5), -15.5), 0.0, hexc("#e8502c"))
    crab(sc, "crab_3", (20.5, Y(20.5, -15.0), -15.0), 0.4, hexc("#f06038"))
    gull(sc, "gull_0", (21.8 - 0.4, Y(21.8, -11.5) + 2.6 + 1.93, -11.5), -2.5, 1.0)
    gull(sc, "gull_1", (-4.3 + 0.9, Y(-4.3, -4.8) + 4.34, -4.8 - 0.25), -0.4, 0.9)
    gull(sc, "gull_2", (-3.4, Y(-3.4, -0.6), -0.6), -0.3, 1.0)
    gull(sc, "gull_3", (19.9, Y(19.9, -1.2), -1.2), math.pi + 0.4, 1.0)


# ------------------------------------------------------------------ the background life (critters.glb)

def critters(sc):
    """Models for the beach's occasional background events, each at the origin facing +x, feet (or the waterline)
    at y = 0: ev_crab, ev_gull (standing), ev_dolphin, ev_turtle, ev_kite_0/1 (tail: flag_sway, UV.x down the tail),
    ev_coconut, ev_ferry, ev_sail. The game moves them (spike_beach.gd)."""
    crab(sc, "ev_crab", (0.0, 0.0, 0.0), 0.0, hexc("#f2683a"))
    gull(sc, "ev_gull", (0.0, 0.0, 0.0), 0.0, 1.0)

    # a dolphin: a sleek body curving up to the beak, dark above and pale below, a dorsal fin, flippers and flukes
    d = sc.acc("ev_dolphin")
    prof = [(-1.1, 0.04, 0.0), (-0.95, 0.07, 0.01), (-0.7, 0.14, 0.02), (-0.4, 0.23, 0.03), (-0.05, 0.28, 0.03),
            (0.3, 0.27, 0.02), (0.55, 0.22, 0.0), (0.72, 0.17, -0.02), (0.84, 0.1, -0.05), (0.92, 0.06, -0.07),
            (1.08, 0.025, -0.08)]
    top_c, belly_c = hexc("#4f6076"), hexc("#dfe4e8")

    def dc(i, p, v):
        k = smooth(-0.06, 0.08, v.y - p.y)
        return mix(belly_c, top_c, k)
    d.tube([(x, y, 0.0) for x, _r, y in prof], [r for _x, r, _y in prof], "critter", dc, segs=10, cap=True)
    d.poly([(-0.25, 0.24, 0.0), (0.2, 0.25, 0.0), (-0.32, 0.6, 0.0)], "critter", top_c)
    for sgn in (-1, 1):
        d.poly([(0.42, -0.1, sgn * 0.18), (0.25, -0.12, sgn * 0.2), (0.12, -0.22, sgn * 0.45)], "critter", top_c)
        d.poly([(-1.02, 0.0, 0.0), (-1.12, 0.0, sgn * 0.02), (-1.42, 0.04, sgn * 0.34), (-1.3, 0.02, sgn * 0.12)],
               "critter", top_c, out=(-1.2, -1.0, 0.0))
        d.blob((0.8, 0.07, sgn * 0.1), (0.022, 0.022, 0.022), "critter", hexc("#101418"), segs=5, rings=3, rough=0.0)

    # a sea turtle: a domed shell with plates and pale seams, a pale plastron, head, flippers
    t = sc.acc("ev_turtle")
    shell_d, shell_l, seam = hexc("#5a4a2a"), hexc("#8a7038"), hexc("#c8b27a")

    def tc(nx, ny, nz, q):
        u, v = q[0] * 5.0, q[2] * 5.5
        cell = abs(math.sin(u + 0.4 * math.sin(v))) * abs(math.sin(v * 1.1 + 0.3))
        base = mix(shell_d, shell_l, 0.5 + 0.5 * n2(q[0], q[2], 3.0, 4))
        return mix(seam, base, smooth(0.04, 0.22, cell))
    t.blob((0.0, 0.1, 0.0), (0.46, 0.2, 0.36), "critter", tc, segs=14, rings=6, rough=0.04, cut=0.0)
    t.blob((0.0, 0.1, 0.0), (0.44, 0.06, 0.34), "critter", hexc("#d8c890"), segs=12, rings=3, rough=0.0)
    t.tube([(0.35, 0.1, 0.0), (0.5, 0.14, 0.0)], 0.07, "critter", hexc("#7a8a58"), segs=6)
    t.blob((0.58, 0.15, 0.0), (0.12, 0.08, 0.085), "critter",
           lambda nx, ny, nz, q: mix(hexc("#6a7a48"), hexc("#a8b078"), smooth(0.3, -0.5, ny)), segs=8, rings=5, rough=0.05)
    for sgn in (-1, 1):
        t.blob((0.64, 0.18, sgn * 0.055), (0.018, 0.018, 0.018), "critter", hexc("#101010"), segs=5, rings=3, rough=0.0)
        t.blob((0.22, 0.06, sgn * 0.4), (0.12, 0.025, 0.22), "critter", hexc("#7a8a58"), segs=8, rings=3, rough=0.1)
        t.blob((-0.38, 0.05, sgn * 0.24), (0.09, 0.022, 0.1), "critter", hexc("#7a8a58"), segs=7, rings=3, rough=0.1)

    # two kites: a bowed diamond in two colours on crossed spars, with a ribbon tail and bows
    for k, (c1, c2) in enumerate(((hexc("#ff4f7b"), hexc("#ffd24a")), (hexc("#1fb5a8"), hexc("#ff7a45")))):
        kt = sc.acc("ev_kite_%d" % k)
        T_, R_, B_, L_, C_ = (0, 0.9, 0), (0.6, 0.25, 0), (0, -0.75, 0), (-0.6, 0.25, 0), (0, 0.25, 0.1)
        kt.poly([T_, R_, C_], "fabric", c1)
        kt.poly([R_, B_, C_], "fabric", c2)
        kt.poly([B_, L_, C_], "fabric", c1)
        kt.poly([L_, T_, C_], "fabric", c2)
        kt.tube([(0, 0.9, 0.02), (0, -0.75, 0.02)], 0.012, "wood", hexc("#e8dcc0"), segs=3)
        kt.tube([(-0.6, 0.25, 0.04), (0.6, 0.25, 0.04)], 0.012, "wood", hexc("#e8dcc0"), segs=3)
        n = 14
        for i in range(n):
            y0, y1 = -0.75 - 0.3 * i, -0.75 - 0.3 * (i + 1)
            kt.poly([(-0.03, y0, 0), (0.03, y0, 0), (0.03, y1, 0), (-0.03, y1, 0)], "flag_sway", c2 if i % 2 else c1,
                    uvs=[(0.3 * i, 0), (0.3 * i, 0), (0.3 * (i + 1), 0), (0.3 * (i + 1), 0)])
            if i % 3 == 2:
                for sg in (-1, 1):
                    kt.poly([(0, y1, 0), (sg * 0.16, y1 + 0.07, 0), (sg * 0.16, y1 - 0.07, 0)], "flag_sway",
                            c1 if sg < 0 else c2, uvs=[(0.3 * (i + 1), 0)] * 3)

    cc = sc.acc("ev_coconut")
    cc.blob((0.0, 0.0, 0.0), (0.15, 0.17, 0.15), "critter",
            lambda nx, ny, nz, q: mix(hexc("#4f6a24"), hexc("#8a7a3a"), smooth(-0.6, 0.8, ny)), segs=8, rings=5,
            rough=0.12, seed=2.0)

    # a little ferry: a navy hull with a white band, two decks with window strips, a red funnel, a mast
    f = sc.acc("ev_ferry")
    outline = []
    for k in range(24):
        ang = 2 * math.pi * k / 24
        cx_, sz_ = math.cos(ang), math.sin(ang)
        xx = 11.0 * cx_ if cx_ > 0 else 10.0 * (abs(cx_) ** 0.3) * -1
        zz = 2.6 * sz_ * (1.0 - 0.75 * max(0.0, cx_) ** 3)
        outline.append((xx, zz))
    f.prism(outline, -0.6, 1.4, "paint", lambda y: hexc("#26365a") if y < 1.0 else hexc("#26365a"))
    f.prism([(x_ * 0.99, z_ * 0.99) for x_, z_ in outline], 1.4, 2.0, "paint", hexc("#f4f2ea"))
    f.rbox((-1.0, 2.8, 0.0), (15.0, 1.6, 4.4), 0.2, "paint", hexc("#f7f5ef"))
    f.box((-1.0, 2.9, 0.0), (14.6, 0.5, 4.46), "paint", hexc("#2a4a66"))
    f.rbox((-2.0, 4.2, 0.0), (9.0, 1.3, 3.8), 0.2, "paint", hexc("#f7f5ef"))
    f.box((-2.0, 4.3, 0.0), (8.6, 0.45, 3.86), "paint", hexc("#2a4a66"))
    f.rbox((1.8, 5.2, 0.0), (2.2, 0.9, 3.0), 0.15, "paint", hexc("#f7f5ef"))
    f.box((2.4, 5.3, 0.0), (1.2, 0.35, 3.06), "paint", hexc("#2a4a66"))
    f.rbox((-4.2, 6.0, 0.0), (1.8, 2.4, 1.3), 0.3, "paint", hexc("#e04a36"))
    f.rbox((-4.2, 7.3, 0.0), (1.85, 0.4, 1.35), 0.15, "paint", hexc("#1a1a1e"))
    f.tube([(2.2, 5.6, 0.0), (2.2, 8.4, 0.0)], 0.08, "metal", hexc("#e8e8e8"), segs=5)
    f.tube([(10.5, 2.0, 0.0), (8.0, 8.2, 0.0), (-9.5, 2.0, 0.0)], 0.03, "metal", hexc("#e8e8e8"), segs=3)
    for i in range(10):  # little flags along the stays
        u = (i + 0.5) / 10
        px, py = 10.5 + (8.0 - 10.5) * u * 2 if u < 0.5 else 8.0 + (-9.5 - 8.0) * (u - 0.5) * 2, 0
        py = 2.0 + 6.2 * (u * 2 if u < 0.5 else (1 - u) * 2)
        f.poly([(px, py, 0.0), (px + 0.35, py - 0.02, 0.0), (px + 0.17, py - 0.45, 0.0)], "paint",
               [hexc("#ff4f7b"), hexc("#ffd24a"), hexc("#1fb5a8")][i % 3])

    # a sailboat with a striped sail
    b = sc.acc("ev_sail")
    s_ = 1.5
    b.lathe((0.0, -0.3, 0.0), [(0.0, 0), (0.6 * s_, 0.1), (0.75 * s_, 0.6 * s_)], 10, "paint", hexc("#f7f5ef"),
            sx=2.6, sm=True, cap=True)
    b.lathe((0.0, 0.55 * s_ - 0.3, 0.0), [(0.76 * s_, 0.0), (0.78 * s_, 0.1)], 10, "paint", hexc("#1f74d6"), sx=2.6,
            cap=False)
    b.tube([(0.0, 0.5, 0.0), (0.0, 7.0 * s_, 0.0)], 0.07 * s_, "wood", hexc("#8a6a4a"), segs=5)
    bands = [hexc("#ff4f7b"), hexc("#ffd24a"), hexc("#1fb5a8"), hexc("#f7f5ef")]
    for i in range(4):
        y0, y1 = 1.0 * s_ + i * 1.35 * s_, 1.0 * s_ + (i + 1) * 1.35 * s_
        w0, w1 = 3.2 * s_ * (1 - (y0 - 1.0 * s_) / (5.6 * s_)), 3.2 * s_ * (1 - (y1 - 1.0 * s_) / (5.6 * s_))
        b.poly([(0.15, y0, 0.0), (0.15, y1, 0.0), (0.15 + max(0.02, w1), y1 - 0.05, 0.0), (0.15 + w0, y0, 0.0)],
               "fabric", bands[i])
    b.poly([(-0.15, 1.2 * s_, 0.0), (-0.15, 6.4 * s_, 0.0), (-2.4 * s_, 1.2 * s_, 0.0)], "fabric", hexc("#fbf6ec"))


def main():
    sc = Scene("beach_scene")
    beach(sc)
    sc.export()
    cr = Scene("critters")
    critters(cr)
    cr.export()


main()
