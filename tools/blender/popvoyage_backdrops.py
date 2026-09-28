"""Pop Voyage (game 23) landmark backdrops: eight dioramas that stand behind the 16 x 10 arena, one per stage theme.
Original designs: every landmark is an invented, generic one (a striped lighthouse, windmills, a natural arch, a
tiered temple, a glacier, a volcano, a harbour town, a tundra village); none copies a real building. Deterministic
(fixed seeds); output CC BY-SA 4.0; provenance: this script only, no third-party assets, no textures (vertex colours).
Run: blender -b --factory-startup -P tools/blender/popvoyage_backdrops.py -- godot/games/popvoyage/art/backdrops [n ...]

Coordinates: everything is authored in Godot space (x right, y up, z towards the camera) and converted on export.
The arena is x 0..16, y 0..10 on the plane z = 0; the camera sits near (8, 5, 22) (fov 35). Each backdrop_<n>.glb holds
  fg_*      the foreground strip: the floor the traveller runs on (top exactly y = 0 across the view for
            z -1.2..+2.5), running on to z = +9.5 so the bottom of the screen is filled, plus props beyond the ends
  mid_*     terrain (to the horizon) and props; fog and muted colours keep what is behind the arena calm
  lm_*      the landmark (lighthouse, windmills, arch, pagoda, glacier, harbour town and bridge, village);
            Ember Peak's volcano is part of its mid_land height field
  far_*     ranges, islands, mesas, treelines as far as z -520 (the sea runs on to z -1300 to reach the horizon)
  cloud_<i> puffy clouds (the game drifts them along x)
and animated nodes, each with its origin at its pivot:
  0 beam (rotate about local Y), boat_<i> / buoy_<i> (bob)
  1 sails_<i> (rotate about local Z: the sails face the camera), boat_<i>
  2 -
  3 -
  4 berg_<i> (bob), floe_<i> (bob)
  5 smoke_anchor (an empty at the crater: the game emits smoke there)
  6 wheel (rotate about local Z) with gondola_<k> (origin at its rim pin: carry it round, keep it upright),
    boat_<i> (bob), ferry (glides along x)
  7 aurora (curtain ribbons; UV.x runs along a curtain, UV.y from its foot (0) to its top (1)), smoke_<i> (empties
    at the chimney tops)
Material names carry the game's hints: "*glow*" emissive (window_glow, coolwindow_glow, lamp_glow, bulb_glow,
lava_glow, beam_glow, blink_glow, aurora_glow; reflect_glow = light streaks lying on the water, spill_glow = lamp
light pooled on snow, both with UV.y running away from the light), "water" (the game swaps a wave shader; vertex
colour R marks the shallows), "*sway*" (the game bends it in the wind by UV.y, the height above the plant's foot),
"cloud", "ice", "snow". All other colour is in the vertex colours (COLOR_0, linear), over white materials.
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/popvoyage/art/backdrops")
ONLY = [int(a) for a in argv[1:]]

CAM = Vector((8.0, 5.0, 22.0))
TAN_W = 0.5606  # half-width per unit of distance for fov 35 at 16:9


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
MAT_DEFS = {
    # name: (base colour, roughness, metallic, emission strength, alpha)
    "ground": ((1, 1, 1), 0.95, 0, 0, 1),
    "rock": ((1, 1, 1), 0.85, 0, 0, 1),
    "paint": ((1, 1, 1), 0.55, 0, 0, 1),
    "wood": ((1, 1, 1), 0.8, 0, 0, 1),
    "metal": ((1, 1, 1), 0.35, 0.7, 0, 1),
    "glass": ((1, 1, 1), 0.15, 0.2, 0, 1),
    "snow": ((1, 1, 1), 0.6, 0, 0, 1),
    "ice": ((1, 1, 1), 0.18, 0, 0, 1),
    "cloud": ((1, 1, 1), 1.0, 0, 0, 1),
    "water": ((1, 1, 1), 0.1, 0, 0, 1),
    "foliage_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "bamboo_sway": ((1, 1, 1), 0.6, 0, 0, 1),
    "blossom_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "aurora_glow": ((0.3, 1.0, 0.6), 1, 0, 3.0, 1),
    "beam_glow": ((1.0, 0.95, 0.75), 1, 0, 2.0, 1),
    "lamp_glow": ((1.0, 0.82, 0.45), 0.4, 0, 4.0, 1),
    "window_glow": ((1.0, 0.75, 0.4), 0.4, 0, 2.5, 1),
    "coolwindow_glow": ((0.75, 0.88, 1.0), 0.4, 0, 2.0, 1),
    "lava_glow": ((1.0, 0.38, 0.08), 0.6, 0, 5.0, 1),
    "blink_glow": ((1.0, 0.15, 0.1), 0.4, 0, 5.0, 1),
    "reflect_glow": ((1.0, 0.7, 0.35), 1, 0, 1.2, 1),
    "spill_glow": ((1.0, 0.7, 0.4), 1, 0, 0.8, 1),
    "bulb_glow": ((1.0, 0.9, 0.7), 0.4, 0, 4.0, 1),
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
                    uv.data[poly.loop_start + k].uv = f[3][k]
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


def rock(a, c, r, rng, col_top, col_side, flat=False, segs=7):
    def cc(nx, ny, nz, q):
        return mix(col_side, col_top, smooth(0.2, 0.8, ny))
    a.blob(c, r, "rock", cc, segs=segs, rings=4, rough=0.3, nscale=0.9, seed=rng.random() * 50, sm=not flat and False,
           cut=-0.4)


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


def pine(a, c, h, rng, green, snow=None, trunk=hexc("#5a3d2b"), tiers=4):
    a.sway_base = c[1]
    x, y, z = c
    a.lathe((x, y, z), [(h * 0.05, 0), (h * 0.05, h * 0.2)], 5, "wood", trunk, sm=False, cap=False)
    for i in range(tiers):
        t0 = 0.15 + i * (0.75 / tiers)
        r = h * 0.32 * (1 - i / (tiers + 0.6))
        yb = h * t0
        yt = yb + h * 0.42

        def cc(px, py, pz, yb=yb, yt=yt):
            k = (py - y - yb) / (yt - yb)
            base = mul(green, 0.75 + 0.35 * k)
            if snow:
                return mix(base, snow, smooth(0.25, 0.4, k) * 0.8)
            return base
        a.lathe((x, y, z), [(r, yb), (r * 0.55, yb + (yt - yb) * 0.35), (0.0, yt)], 7, "foliage_sway", cc,
                sm=False, cap=False, rough=0.12, seed=rng.random() * 30, phase=rng.random())


def leafy_tree(a, c, h, rng, green, trunk=hexc("#6b4a33"), material="foliage_sway", light=None):
    a.sway_base = c[1]
    x, y, z = c
    a.tube([(x, y, z), (x + rng.uniform(-0.2, 0.2), y + h * 0.45, z)], [h * 0.05, h * 0.035], "wood", trunk, segs=5)
    light = light or mul(green, 1.35)
    for i in range(3):
        r = h * rng.uniform(0.22, 0.3)
        p = (x + rng.uniform(-0.2, 0.2) * h, y + h * (0.55 + 0.15 * i), z + rng.uniform(-0.15, 0.15) * h)

        def cc(nx, ny, nz, q):
            return mix(mul(green, 0.7), light, smooth(-0.5, 0.8, ny + 0.3 * nx))
        a.blob(p, (r, r * 0.85, r), material, cc, segs=8, rings=5, rough=0.2, nscale=1.2, seed=rng.random() * 40)


def poplar(a, c, h, rng, green):
    a.sway_base = c[1]
    x, y, z = c
    a.tube([(x, y, z), (x, y + h * 0.2, z)], h * 0.03, "wood", hexc("#5a4030"), segs=4)

    def cc(nx, ny, nz, q):
        return mix(mul(green, 0.65), mul(green, 1.25), smooth(-0.6, 0.7, nx * 0.6 + ny * 0.4))
    a.blob((x, y + h * 0.58, z), (h * 0.13, h * 0.42, h * 0.13), "foliage_sway", cc, segs=7, rings=6, rough=0.15,
           seed=rng.random() * 40)


def gable_house(a, c, w, d, h, wall, roof, rng, ry=0.0, windows=None, window_mat="window_glow", chimney=True):
    """A small house (ridge along x before turning): walls, a pitched roof, a chimney and optional lit windows."""
    x, y, z = c
    cr, sr = math.cos(ry), math.sin(ry)

    def P(u, v, s):  # local (u along ridge, v up, s across) to world
        return (x + u * cr + s * sr, y + v, z - u * sr + s * cr)
    a.box((x, y + h / 2, z), (w, h, d), "paint", wall, ry=ry)
    rh = d * 0.45
    o = 0.25
    ridge = [P(-w / 2 - o, h + rh, 0), P(w / 2 + o, h + rh, 0)]
    for s in (-1, 1):
        a.poly([P(-w / 2 - o, h - 0.1, s * (d / 2 + o)), P(w / 2 + o, h - 0.1, s * (d / 2 + o)), ridge[1], ridge[0]],
               "paint", roof, out=P(0, h, 0))
    for u in (-1, 1):
        a.poly([P(u * w / 2, h, -d / 2), P(u * w / 2, h, d / 2), P(u * w / 2, h + rh, 0)], "paint", wall,
               out=P(0, h, 0))
    if chimney:
        a.box(P(w * 0.25, h + rh * 0.9, d * 0.15), (0.35, rh * 1.0, 0.35), "rock", mul(wall, 0.7), ry=ry)
    if windows:
        for u in windows:
            p = P(u * w / 2 * 0.6, h * 0.55, d / 2 + 0.02)
            a.box(p, (0.6, 0.7, 0.04), window_mat, (1, 1, 1), ry=ry)


# ------------------------------------------------------------------ 0 Lighthouse Point


def sea(sc, level, near_z=-1.0, far_z=-1300.0, shallow_fn=None):
    a = sc.acc("mid_sea")

    def col(x, y, z, ny):
        s = shallow_fn(x, z) if shallow_fn else 0.0
        return (s, 0.0, 0.0)
    a.terrain(near_z, far_z, 70, 80, lambda x, z: level, col, material="water", sm=True, margin=2.2)
    return a


def lighthouse_point(sc):
    rng = random.Random(10)
    SEA = -0.7
    sand, wet = hexc("#e9d3a4"), hexc("#b99f78")
    grass, grass2 = hexc("#5f9e3c"), hexc("#94bf55")
    cliff, cliff2 = hexc("#7a6a62"), hexc("#a88f7a")

    # the boardwalk: pale boards along x on a sand bed
    fg = sc.acc("fg_boardwalk")
    zc = 2.5
    row = 0
    while zc > -1.3:
        dz = 0.36
        x = -16.0 + rng.uniform(0, 2)
        while x < 32:
            L = rng.uniform(2.5, 4.5)
            tone = rng.uniform(0.9, 1.05)
            c = mul(mix(hexc("#d8b98f"), hexc("#c49a6c"), rng.random() * 0.6), tone)
            fg.box((x + L / 2, -0.09, zc - dz / 2), (L - 0.04, 0.18, dz - 0.04), "wood", c,
                   cols=(c, mul(c, 0.7)))
            x += L
        zc -= dz
        row += 1
    # posts along the front edge and the sea edge
    for x in range(-16, 33, 3):
        fg.box((x, -0.6, -1.25), (0.22, 1.2, 0.22), "wood", hexc("#8a6a4a"))
        fg.box((x + 0.5, -0.4, 2.6), (0.24, 0.9, 0.24), "wood", hexc("#8a6a4a"))
    # sand in front (to the bottom of the screen) with dune grass beyond the arena's ends
    sandf = sc.acc("fg_sand")
    sandf.terrain(9.5, 2.3, 6, 40, lambda x, z: -0.25 + 0.25 * fbm(x, z, 0.15, 2) - 0.1,
                  lambda x, y, z, ny: mix(sand, mul(sand, 0.9), n2(x, z, 0.4) * 0.5 + 0.5), margin=1.6)
    grassf = sc.acc("fg_grass")
    for i in range(70):
        side = rng.choice((-1, 1))
        x = 8 + side * rng.uniform(9.5, 22)
        z = rng.uniform(2.8, 7.5)
        tuft(grassf, (x, -0.1, z), rng.uniform(0.5, 0.9), hexc("#8a9a50"), hexc("#d6d58a"), rng, blades=6)
    for x, z in ((-6.5, 4.5), (22.5, 5.2)):
        rock(grassf, (x, -0.2, z), (0.9, 0.6, 0.7), rng, hexc("#b0a89c"), hexc("#7b726a"))

    # the land: a beach under the boardwalk, the headland on the right with its cove, a low point on the left
    def h(x, z):
        base = -1.6 + 1.2 * smooth(-7.0, -1.0, z)  # the beach sinks into the sea
        # the headland: rises beyond x ~ 20 from z -12 back
        m = smooth(19.0, 33.0, x + 0.25 * (z + 20) + 5 * fbm(x, z, 0.05, 2, 1))
        m *= smooth(-12.0, -30.0, z + 4 * fbm(x, z, 0.07, 2, 2))
        top = 8.5 + 3.0 * fbm(x, z, 0.03, 3, 3) + 0.08 * max(0, x - 30)
        cl = smooth(0.25, 0.55, m)
        y = base * (1 - cl) + (top * cl) + 1.2 * fbm(x, z, 0.25, 2, 4) * cl * (1 - cl) * 4
        # the low point on the left
        lm = smooth(-6.0, -22.0, x - 0.3 * (z + 25) + 4 * fbm(x, z, 0.06, 2, 5)) * smooth(-10.0, -24.0, z)
        y = max(y, -1.6 + 4.5 * lm + 1.0 * fbm(x, z, 0.2, 2, 6) * lm)
        # far islands' shoulders never needed here: the sea runs to the horizon
        return y

    def col(x, y, z, ny):
        if y < SEA + 0.35:
            return mix(wet, sand, smooth(SEA, SEA + 0.35, y))
        if ny < 0.72:
            band = 0.5 + 0.5 * math.sin(y * 2.2 + 1.5 * n2(x, z, 0.08, 3))
            return mul(mix(cliff, cliff2, 0.35 + 0.5 * band), 0.85 + 0.15 * smooth(-0.5, 4.0, y))
        k = smooth(0.72, 0.9, ny)
        g = mix(grass, grass2, 0.5 + 0.5 * n2(x, z, 0.12))
        if y < 1.5:
            g = mix(sand, g, smooth(0.2, 1.5, y))
        return mix(mix(cliff2, cliff, 0.3), g, k)
    land = sc.acc("mid_land")
    land.terrain(-1.2, -170, 72, 110, h, col, margin=1.6)

    # chunky rocks along the cliff foot and the shore
    rk = sc.acc("mid_rocks")
    for i in range(46):
        z = rng.uniform(-8, -70)
        x = rng.uniform(17, 40) + 0.3 * (-z - 10) * 0.2
        if h(x, z) < SEA - 0.2 or h(x, z) > 4:
            continue
        s = rng.uniform(0.6, 2.2)
        rock(rk, (x, SEA - 0.2, z), (s * 1.3, s, s * 1.1), rng, cliff2, mul(cliff, 0.85))
    for x, z, s in ((-9, -9, 1.2), (-12, -12, 1.8), (-7, -6, 0.7), (21, -6, 1.0), (24, -8.5, 1.6)):
        rock(rk, (x, SEA - 0.1, z), (s * 1.4, s, s), rng, cliff2, mul(cliff, 0.85))
    # sea stacks on the left
    for x, z, hh, r in ((-24, -40, 9, 2.8), (-34, -58, 12, 3.4), (-16, -70, 6, 2.2)):
        def cc(px, py, pz, hh=hh):
            return mix(mul(cliff, 0.9), cliff2, 0.5 + 0.5 * n2(px, py, 0.6))
        rk.lathe((x, SEA - 0.5, z), [(r * 1.3, 0), (r * 1.05, hh * 0.3), (r, hh * 0.7), (r * 0.9, hh)], 9, "rock",
                 cc, sm=False, rough=0.18, nscale=0.8, seed=x)
        rk.blob((x, SEA - 0.5 + hh, z), (r * 0.95, 0.8, r * 0.95), "ground", grass, segs=9, rings=3, rough=0.2,
                cut=0.0)

    # the lighthouse on the headland, just beyond the arena's right end
    LX, LZ = 35.0, -52.0
    LY = h(LX, LZ) - 0.2
    lm = sc.acc("lm_lighthouse")
    stone = hexc("#cfc6b8")
    lm.lathe((LX, LY, LZ), [(3.0, -1.0), (3.0, 0.6), (2.6, 1.0), (2.6, 1.4)], 8, "rock", stone, sm=False)
    red, white = hexc("#d4412f"), hexc("#f6f1e6")
    TH = 12.5

    def band(x, y, z):
        k = (y - LY - 1.4) / TH
        return red if int(k * 5 + 0.0001) % 2 == 0 else white
    prof = []
    for i in range(11):
        t = i / 10
        prof.append((1.9 - 0.75 * t, 1.4 + TH * t))
    # add ring edges at the band boundaries so the stripes are crisp
    prof2 = []
    for i in range(6):
        t0 = i / 5
        prof2.append((1.9 - 0.75 * t0, 1.4 + TH * t0 + (0.001 if i else 0)))
        if i < 5:
            t1 = (i + 1) / 5 - 0.0005
            prof2.append((1.9 - 0.75 * t1, 1.4 + TH * t1))
    lm.lathe((LX, LY, LZ), prof2, 16, "paint", band, sm=True, cap=False)
    top = LY + 1.4 + TH
    lm.lathe((LX, top, LZ), [(1.15, 0), (1.9, 0.15), (1.9, 0.45), (1.15, 0.45)], 16, "paint", hexc("#2f3438"),
             sm=False)
    for j in range(16):  # the gallery rail
        a_ = 2 * math.pi * j / 16
        lm.box((LX + 1.8 * math.cos(a_), top + 0.95, LZ + 1.8 * math.sin(a_)), (0.08, 1.0, 0.08), "metal",
               hexc("#2f3438"))
    lm.lathe((LX, top + 1.4, LZ), [(1.85, 0), (1.85, 0.08)], 16, "metal", hexc("#2f3438"), sm=False)
    lm.lathe((LX, top + 0.45, LZ), [(0.95, 0), (0.95, 1.7)], 10, "lamp_glow", (1, 1, 1), sm=False, cap=False)
    for j in range(10):
        a_ = 2 * math.pi * j / 10
        lm.box((LX + 0.97 * math.cos(a_), top + 1.3, LZ + 0.97 * math.sin(a_)), (0.08, 1.7, 0.08), "metal",
               hexc("#2f3438"))
    lm.lathe((LX, top + 2.15, LZ), [(1.25, 0), (1.0, 0.35), (0.5, 0.9), (0.08, 1.3), (0.0, 1.9)], 12, "paint", red,
             sm=True, cap=False)
    for k in range(4):  # little windows up the tower
        yy = LY + 3.5 + k * 3.4
        r = 1.9 - 0.75 * ((yy - LY - 1.4) / TH) + 0.02
        lm.box((LX + r * math.cos(1.9), yy, LZ + r * math.sin(1.9)), (0.4, 0.7, 0.06), "paint", hexc("#2a3a48"),
               ry=-1.9 + math.pi / 2)
    # the keeper's cottage
    hy = h(LX - 7, LZ + 3) - 0.1
    gable_house(lm, (LX - 7.5, hy, LZ + 3), 6.0, 3.8, 2.6, hexc("#f4efe4"), hexc("#b8423a"), rng, ry=0.25,
                windows=None)
    for u in (-1.5, 1.5):
        lm.box((LX - 7.5 + u, hy + 1.4, LZ + 3 + 1.95 + u * 0.25 * 0.25), (0.7, 0.8, 0.05), "paint",
               hexc("#3a5c7a"), ry=0.25)
    # a path of pale stones down the headland
    # the beam: two soft cones from the lantern (the game turns it)
    bm = sc.acc("beam", (LX, top + 1.3, LZ))
    for s in (1, -1):
        L, R = 16.0, 1.6
        pts = []
        for k in range(10):
            a_ = 2 * math.pi * k / 10
            pts.append((LX + s * L, top + 1.3 + R * math.cos(a_), LZ + R * math.sin(a_)))
        tip = bm.vert((LX + s * 0.4, top + 1.3, LZ))
        ring = [bm.vert(p) for p in pts]
        for k in range(10):
            bm.face([tip, ring[k], ring[(k + 1) % 10]], "beam_glow", [(1, 1, 1)] * 3,
                    uvs=[(0.5, 0.0), (k / 10, 1.0), ((k + 1) / 10, 1.0)])

    # the sea and its boats
    sea(sc, SEA, shallow_fn=lambda x, z: smooth(SEA - 0.9, SEA + 0.1, h(x, z)))
    for i, (x, z, s) in enumerate(((-11.0, -62.0, 1.0), (58.0, -130.0, 1.4))):
        b = sc.acc("boat_%d" % i, (x, SEA, z))
        b.lathe((x, SEA - 0.3, z), [(0.0, 0), (0.6 * s, 0.1), (0.75 * s, 0.6 * s)], 8, "paint", hexc("#f2f2ee"),
                sx=2.6, sm=True, cap=True)
        b.box((x, SEA + 0.5 * s, z), (4.0 * s, 0.12, 1.4 * s), "wood", hexc("#b98a5a"))
        b.tube([(x, SEA + 0.5, z), (x, SEA + 6.5 * s, z)], 0.07, "wood", hexc("#8a6a4a"), segs=4)
        b.poly([(x + 0.15, SEA + 1.0 * s, z), (x + 0.15, SEA + 6.2 * s, z), (x + 2.9 * s, SEA + 1.1 * s, z)],
               "paint", hexc("#fbf6ec"))
        b.poly([(x - 0.15, SEA + 1.2 * s, z), (x - 0.15, SEA + 5.2 * s, z), (x - 2.1 * s, SEA + 1.2 * s, z)],
               "paint", hexc("#e8674a"))
    bu = sc.acc("buoy_0", (-4.0, SEA, -16.0))
    bu.lathe((-4.0, SEA - 0.3, -16.0), [(0.5, 0), (0.55, 0.5), (0.3, 1.0), (0.12, 1.8), (0.0, 2.0)], 8, "paint",
             lambda x, y, z: hexc("#e0452f") if y < SEA + 1.0 else hexc("#f3efe6"), sm=False)
    # distant islands on the horizon
    far = sc.acc("far_islands")
    for x, z, w, hh in ((-150, -330, 70, 16), (-60, -420, 50, 10), (160, -380, 90, 22), (90, -300, 30, 7)):
        far.blob((x, SEA - 2, z), (w, hh, w * 0.3), "ground",
                 lambda nx, ny, nz, q: mix(hexc("#6f8a74"), hexc("#98ae8c"), ny), segs=12, rings=4, rough=0.2,
                 nscale=0.5, seed=x, cut=0.0)
    # clouds far over the sea
    for i in range(7):
        x = -140 + i * 45 + rng.uniform(-10, 10)
        cloud(sc, "cloud_%d" % i, (x, rng.uniform(38, 70), rng.uniform(-240, -300)), rng.uniform(9, 15), rng,
              under=hexc("#c3cfe3"))


# ------------------------------------------------------------------ 1 Windmill Meadow

TULIPS = [hexc("#e5484d"), hexc("#f5c542"), hexc("#f08bb0"), hexc("#f28a3c"), hexc("#f4efe6"), hexc("#9a6ad0"),
          hexc("#d93a6a")]


def windmill(sc, i, c, s, rng):
    """A tapered eight-sided smock mill on a brick base with a stage, a boat-shaped cap and four lattice sails
    (the sails node turns about its local Z; the sails face the camera)."""
    x, y, z = c
    a = sc.acc("lm_windmill_%d" % i)
    brick, body, trim = hexc("#9c4a38"), hexc("#3f5a4a"), hexc("#efe8da")
    a.lathe((x, y, z), [(3.6 * s, -0.3), (3.6 * s, 2.4 * s), (3.3 * s, 2.6 * s)], 8, "rock",
            lambda px, py, pz: mul(brick, 0.9 + 0.2 * ((int(py * 3) % 2))), sm=False, phase=math.pi / 8)
    a.lathe((x, y + 2.6 * s, z), [(3.0 * s, 0), (2.0 * s, 8.0 * s)], 8, "wood",
            lambda px, py, pz: mix(body, mul(body, 1.25), (py - y) / (11 * s)), sm=False, cap=False, phase=math.pi / 8)
    # the stage (a gallery round the body) with its rail
    a.lathe((x, y + 4.2 * s, z), [(2.75 * s, 0), (4.4 * s, 0.0), (4.4 * s, 0.25 * s), (2.7 * s, 0.25 * s)], 16,
            "wood", hexc("#6a4a32"), sm=False)
    for j in range(20):
        an = 2 * math.pi * j / 20
        a.box((x + 4.3 * s * math.cos(an), y + 4.9 * s, z + 4.3 * s * math.sin(an)), (0.1 * s, 1.1 * s, 0.1 * s),
              "wood", trim)
    a.lathe((x, y + 5.45 * s, z), [(4.3 * s, 0), (4.3 * s, 0.1 * s)], 20, "wood", trim, sm=False)
    # the cap: a boat-shaped hood
    top = y + 10.6 * s
    a.lathe((x, top, z), [(2.3 * s, 0), (2.3 * s, 0.6 * s), (1.8 * s, 1.6 * s), (0.9 * s, 2.3 * s), (0.0, 2.5 * s)],
            10, "paint", hexc("#5b3a2c"), sz=1.35, sm=True, cap=False)
    # a door and two windows
    a.box((x, y + 1.1 * s, z + 3.62 * s), (1.2 * s, 2.0 * s, 0.1), "paint", hexc("#2f4a3a"))
    for k in (0, 1):
        yy = y + (6.0 + 2.6 * k) * s
        rr = 3.0 * s - 1.0 * s * ((yy - y - 2.6 * s) / (8 * s)) + 0.05
        a.box((x, yy, z + rr), (0.8 * s, 1.0 * s, 0.1), "paint", trim)
        a.box((x, yy, z + rr + 0.04), (0.55 * s, 0.75 * s, 0.1), "glass", hexc("#34424a"))
    hub = Vector((x, top + 1.1 * s, z + 3.4 * s))
    a.tube([hub - Vector((0, 0, 1.6 * s)), hub], 0.35 * s, "wood", hexc("#4a3a2c"), segs=8)
    sl = sc.acc("sails_%d" % i, hub)
    sl.lathe((hub.x, hub.y - 0.5 * s, hub.z), [(0.5 * s, 0), (0.5 * s, 1.0 * s)], 8, "wood", hexc("#3c2e24"))
    L, W = 8.5 * s, 1.7 * s
    for k in range(4):
        an = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(an), math.sin(an), 0))
        side = Vector((-d.y, d.x, 0))
        o = Vector((0, 0, 0.12 * s))
        sl.tube([hub + o, hub + o + d * L], [0.14 * s, 0.09 * s], "wood", hexc("#e8dcc0"), segs=4, sm=False)
        # the lattice frame on one side of the stock and the canvas behind it
        r0, r1 = 1.4 * s, L - 0.2 * s
        fr = hexc("#efe6d2")
        for t in range(9):
            rr = r0 + (r1 - r0) * t / 8
            p = hub + o + d * rr
            sl.tube([p, p + side * W], 0.05 * s, "wood", fr, segs=3, sm=False)
        sl.tube([hub + o + d * r0 + side * W, hub + o + d * r1 + side * W], 0.06 * s, "wood", fr, segs=3, sm=False)
        cv = [hub + d * r0 + side * 0.1 * s, hub + d * r1 + side * 0.1 * s, hub + d * r1 + side * W,
              hub + d * r0 + side * W]
        sl.poly(cv, "paint", [hexc("#f5ecdc"), hexc("#f5ecdc"), hexc("#e8dcc4"), hexc("#e8dcc4")])
    return a


def windmill_meadow(sc):
    rng = random.Random(11)
    LAND, WL = -0.25, -0.6
    grass, grass2 = hexc("#6fa64a"), hexc("#98c060")

    # the brick path along the canal, and a verge of grass and tulips in front of it
    fg = sc.acc("fg_path")
    zc = 2.5
    row = 0
    while zc > -1.25:
        dz = 0.42
        x = -16.0 - (0.45 if row % 2 else 0.0)
        while x < 32:
            L = 0.9
            c = mul(mix(hexc("#b85a42"), hexc("#9a4838"), rng.random()), rng.uniform(0.92, 1.06))
            fg.box((x + L / 2, -0.06, zc - dz / 2), (L - 0.05, 0.12, dz - 0.05), "rock", c, cols=(c, mul(c, 0.7)))
            x += L
        zc -= dz
        row += 1
    fg.box((8, -0.5, -1.2), (60, 1.0, 0.25), "rock", hexc("#8a8078"))           # the canal's kerb
    fg.box((8, -0.1, 2.62), (60, 0.2, 0.24), "rock", hexc("#bdb4a6"))           # the path's front edge
    verge = sc.acc("fg_verge")
    verge.terrain(9.5, 2.7, 6, 50, lambda x, z: -0.12 + 0.12 * fbm(x, z, 0.2, 2),
                  lambda x, y, z, ny: mix(grass, grass2, 0.5 + 0.5 * n2(x, z, 0.3)), margin=1.6)
    fl = sc.acc("fg_tulips")
    for i in range(260):
        side = rng.choice((-1, 1))
        x = 8 + side * rng.uniform(9.0, 24)
        z = rng.uniform(3.0, 8.5)
        if rng.random() < 0.25:
            x = rng.uniform(-10, 26)
            z = rng.uniform(6.0, 9.0)
        col = rng.choice(TULIPS)
        fl.sway_base = -0.1
        h = rng.uniform(0.45, 0.75)
        fl.poly([(x - 0.02, -0.1, z), (x + 0.02, -0.1, z), (x + 0.01, -0.1 + h, z)], "foliage_sway", hexc("#4f8a3a"))
        fl.poly([(x, -0.1, z), (x + 0.15, -0.1 + h * 0.5, z + 0.05), (x + 0.03, -0.1 + h * 0.2, z)], "foliage_sway",
                hexc("#5f9a44"))
        fl.lathe((x, -0.1 + h - 0.05, z), [(0.07, 0), (0.14, 0.1), (0.13, 0.25), (0.0, 0.19)], 6, "foliage_sway",
                 lambda px, py, pz, col=col: mul(col, 0.8 + 1.2 * (py - (-0.1 + h))), sm=False, cap=False)
        fl.sway_base = None
    for x in (-5.0, 21.5):
        fl.box((x, 0.35, 1.5), (0.5, 0.7, 0.5), "wood", hexc("#8a6a4a"))             # posts of a little bridge
    # the land: blocks of field and pasture between the canals (the water shows through the gaps)
    land = sc.acc("mid_fields")
    xs = [(-400.0, -8.5), (-5.5, 21.5), (24.5, 420.0)]
    zs = [(-5.6, -38.0), (-40.5, -76.0), (-78.5, -135.0), (-137.5, -1300.0)]
    sat = 0.12
    for bi, (x0, x1) in enumerate(xs):
        for bj, (z0, z1) in enumerate(zs):
            land.box(((x0 + x1) / 2, (LAND - 1.2) / 2, (z0 + z1) / 2), (x1 - x0, LAND + 1.2, z0 - z1), "ground",
                     grass2, cols=(mix(grass, grass2, 0.3), hexc("#6a5a40")))
            if bj == 3:
                continue
            # stripes of tulips running away from the viewer (muted: they sit behind the play)
            w = 2.6
            k = rng.randint(0, 6)
            x = max(x0, -120) + 0.4
            while x + w < min(x1, 140):
                col = TULIPS[k % len(TULIPS)]
                k += 1
                centre = abs(x + w / 2 - 8) < 16 and bj == 0
                cc = desat(col, sat + (0.18 if centre else 0.0))
                if rng.random() < 0.25:
                    cc = mix(grass, grass2, 0.6)
                lo, hi = LAND, LAND + 0.3
                pts = [(x, lo, z0 - 0.4), (x + 0.2, hi, z0 - 0.4), (x + w - 0.2, hi, z0 - 0.4), (x + w, lo, z0 - 0.4)]
                # the top runs in little humps (rows of blooms), brighter on their crests
                nseg = 26 if bj == 0 else 14
                for g in range(nseg):
                    za = z0 - 0.4 + (z1 - z0 + 0.8) * g / nseg
                    zb = z0 - 0.4 + (z1 - z0 + 0.8) * (g + 1) / nseg
                    zm = (za + zb) / 2
                    for q in range(3):
                        c2 = cc if q == 1 else mix(cc, hexc("#4f7a3a"), 0.55)
                        kv = 0.92 + 0.16 * n2(x, zm, 0.4, 7)
                        lo_c, hi_c = mul(mix(c2, hexc("#4f7a3a"), 0.25), kv * 0.9), mul(c2, kv * 1.08)
                        bump = 0.12 if q == 1 else 0.06
                        pa = [(pts[q][0], pts[q][1], za), (pts[q + 1][0], pts[q + 1][1], za)]
                        pm_ = [(pts[q][0], pts[q][1] + (bump if q > 0 else 0), zm),
                               (pts[q + 1][0], pts[q + 1][1] + (bump if q < 2 else 0), zm)]
                        pb = [(pts[q][0], pts[q][1], zb), (pts[q + 1][0], pts[q + 1][1], zb)]
                        land.poly([pa[0], pa[1], pm_[1], pm_[0]], "ground", [lo_c, lo_c, hi_c, hi_c],
                                  out=(x + w / 2, -50, zm))
                        land.poly([pm_[0], pm_[1], pb[1], pb[0]], "ground", [hi_c, hi_c, lo_c, lo_c],
                                  out=(x + w / 2, -50, zm))
                land.poly([pts[0], pts[1], pts[2], pts[3]], "ground", mix(cc, hexc("#4f7a3a"), 0.4),
                          out=(x + w / 2, 0, z1))
                x += w + 0.5
    sea(sc, WL, near_z=-1.2, far_z=-150.0)
    sc.accs[-1].name = "mid_canals"
    # poplars along the side canals, farms, and the windmills
    tr = sc.acc("mid_trees")
    for z in range(-17, -135, -7):
        for xx in (-10.2, 26.2):
            poplar(tr, (xx + rng.uniform(-0.3, 0.3), LAND, z + rng.uniform(-1, 1)), rng.uniform(7, 9.5), rng,
                   hexc("#4f8a3e"))
    for i in range(40):
        x = rng.uniform(-160, 180)
        z = rng.uniform(-150, -260)
        if abs(x - 8) < 20 and z > -200:
            continue
        leafy_tree(tr, (x, LAND, z), rng.uniform(7, 11), rng, hexc("#5a8f45"))
    fm = sc.acc("mid_farms")
    for (x, z, ry, sz) in ((33, -24, 0.3, 1.0), (-30, -62, -0.2, 1.2), (52, -96, 0.5, 1.1), (-70, -118, 0.1, 1.3)):
        gable_house(fm, (x, LAND, z), 6 * sz, 4.5 * sz, 3 * sz, hexc("#e9e0d0"), hexc("#b0463a"), rng, ry=ry)
        gable_house(fm, (x + 6 * sz, LAND, z - 3), 4 * sz, 4 * sz, 2.4 * sz, hexc("#8a4a3a"), hexc("#4a4640"), rng,
                    ry=ry + 0.1, chimney=False)
        for k in range(3):
            leafy_tree(tr, (x - 5 * sz + k * 2.5, LAND, z - 5 - k), rng.uniform(5, 7), rng, hexc("#5a9046"))
    for i, (x, z, s) in enumerate(((-17.0, -34.0, 1.0), (38.0, -58.0, 1.05), (-52.0, -100.0, 1.1),
                                   (20.0, -175.0, 1.0), (72.0, -150.0, 1.0))):
        windmill(sc, i, (x, LAND, z), s, rng)
    # a moored barge in the front canal
    b = sc.acc("boat_0", (-9.0, WL, -3.4))
    b.lathe((-9.0, WL - 0.4, -3.4), [(0.0, 0), (0.7, 0.1), (0.8, 0.75)], 8, "paint", hexc("#2f5a7a"), sx=3.4,
            sm=True, cap=True)
    b.box((-9.4, WL + 0.95, -3.4), (2.2, 0.8, 1.1), "paint", hexc("#e9dfcc"), cols=(hexc("#b0463a"), hexc("#e9dfcc")))
    for i in range(8):
        x = -140 + i * 42 + rng.uniform(-10, 10)
        cloud(sc, "cloud_%d" % i, (x, rng.uniform(40, 75), rng.uniform(-230, -300)), rng.uniform(10, 16), rng,
              under=hexc("#c6d4e6"))


# ------------------------------------------------------------------ 2 Sandstone Arch

def strata(y, seed=0.0):
    bands = [hexc("#d27a3e"), hexc("#b8552e"), hexc("#e4a064"), hexc("#a4462a"), hexc("#d88a4c"), hexc("#ecb880")]
    k = y * 0.55 + 0.6 * n2(y, seed, 0.2)
    i = int(math.floor(k)) % len(bands)
    return mix(bands[i], bands[(i + 1) % len(bands)], smooth(0.7, 1.0, k - math.floor(k)))


def mesa(a, c, R, H, rng, sx=1.0, sz=1.0, cool=0.0):
    seed = rng.random() * 100

    def cc(x, y, z):
        base = strata(y - c[1], seed)
        return mix(base, hexc("#a8745a"), cool)
    prof = [(R * 1.55, -1.0), (R * 1.25, H * 0.18), (R * 1.04, H * 0.34), (R * 1.0, H * 0.55), (R * 0.97, H * 0.8),
            (R * 0.98, H * 0.94), (R * 1.02, H), (R * 0.95, H + 0.4), (0.0, H + 0.6)]
    a.lathe(c, prof, 18, "rock", cc, sm=False, rough=0.22, nscale=0.35, seed=seed, sx=sx, sz=sz, cap=False)


def cactus(a, c, h, rng):
    x, y, z = c
    g = hexc("#5c8a4c")
    a.sway_base = None
    a.tube([(x, y - 0.2, z), (x, y + h, z)], [0.28 * h / 3, 0.24 * h / 3], "paint", g, segs=8, cap=True)
    for s in (-1, 1):
        yy = y + h * rng.uniform(0.35, 0.55)
        e = h * 0.28
        a.tube([(x, yy, z), (x + s * e, yy, z), (x + s * e, yy + h * 0.35, z)], 0.18 * h / 3, "paint", mul(g, 1.1),
               segs=7, cap=True)


def sandstone_arch(sc):
    rng = random.Random(12)
    sand, sand2, shade = hexc("#e2a462"), hexc("#eebd80"), hexc("#b87444")

    def dunes(x, z):
        far = smooth(-3.0, -45.0, z) * (1.0 - 0.7 * smooth(-150.0, -300.0, z))
        u = x * 0.012 + z * 0.06 + 0.8 * fbm(x, z, 0.01, 2, 3)   # crests run across the view, as receding ridges
        r = 0.5 + 0.5 * math.sin(u * math.pi * 2)
        return -0.15 + far * (0.6 + 3.2 * r * r + 1.5 * fbm(x, z, 0.02, 2, 4)) + 0.08 * fbm(x, z, 0.4, 2, 5) * (1 - far)

    def col(x, y, z, ny):
        c = mix(sand, sand2, 0.5 + 0.5 * n2(x, z, 0.08))
        return mix(shade, c, smooth(0.8, 0.98, ny))
    fg = sc.acc("fg_sand")
    fg.terrain(9.5, -1.3, 14, 70, lambda x, z: 0.0 if z < 2.6 else 0.18 * smooth(2.6, 5.0, z) * (1 + fbm(x, z, 0.3, 2)),
               lambda x, y, z, ny: mix(sand2, sand, 0.5 + 0.5 * n2(x, z, 0.35)), margin=1.6)
    pb = sc.acc("fg_pebbles")
    for i in range(90):
        x = rng.uniform(-14, 30)
        z = rng.uniform(2.8, 8.5) if 0 <= x <= 16 else rng.uniform(-1.2, 8.5)
        s = rng.uniform(0.08, 0.3) * (2.5 if not 0 <= x <= 16 and rng.random() < 0.2 else 1.0)
        rock(pb, (x, -0.02, z), (s * 1.3, s * 0.7, s), rng, hexc("#d49a6a"), hexc("#9a5e3e"))
    for i in range(24):
        x = rng.choice((rng.uniform(-14, -1.5), rng.uniform(17.5, 30)))
        tuft(pb, (x, 0.0, rng.uniform(-0.8, 7)), rng.uniform(0.4, 0.7), hexc("#9a8a50"), hexc("#d8c48a"), rng, 7)
    cactus(pb, (-1.2, 0, 5.0), 2.4, rng)
    cactus(pb, (17.6, 0, 4.2), 2.9, rng)
    land = sc.acc("mid_dunes")
    land.terrain(-1.3, -420, 110, 110, dunes, col, margin=1.6)
    # the great arch, left of the play, legs deep in its own rubble
    lm = sc.acc("lm_arch")
    AX, AZ, SPAN, H = -25.0, -88.0, 15.0, 28.0
    pts, rad = [], []
    for i in range(29):
        t = i / 28
        th = math.pi * t
        pts.append((AX - SPAN * math.cos(th), -3.0 + (H + 3.0) * math.sin(th) ** 0.8, AZ + 2.0 * math.sin(th * 2)))
        rad.append(3.0 + 3.8 * (abs(math.cos(th)) ** 3))

    def acol(i, p, v):
        return mix(strata(v.y, 4.0), hexc("#b86a44"), 0.15 * (1 - smooth(-1.0, 1.0, v.y - p.y)))
    lm.tube(pts, rad, "rock", acol, segs=9, sm=False, rough=0.2, seed=3.0, nscale=0.25)
    for sx_ in (-1, 1):
        for k in range(5):
            rock(lm, (AX + sx_ * SPAN + rng.uniform(-6, 6), dunes(AX + sx_ * SPAN, AZ) - 0.3, AZ + rng.uniform(-4, 6)),
                 (rng.uniform(1.2, 3), rng.uniform(0.8, 2), rng.uniform(1.2, 2.5)), rng, hexc("#e0a070"),
                 hexc("#a45e3e"))
    # mesas and buttes: a group on the right, a hoodoo field, a far line on the horizon
    ms = sc.acc("far_mesas")
    for (x, z, R, H2, sx_, sz_) in ((64, -125, 12, 19, 1.4, 0.8), (100, -160, 18, 28, 1.2, 1.0),
                                    (30, -150, 9, 18, 1.0, 1.0), (-70, -170, 20, 26, 1.8, 0.8),
                                    (-150, -260, 30, 34, 1.5, 0.8), (140, -280, 26, 40, 1.6, 0.8),
                                    (10, -330, 22, 24, 2.4, 0.7), (-40, -400, 24, 30, 1.6, 0.8)):
        cool = smooth(-100, -350, z) * 0.35
        mesa(ms, (x, dunes(x, z) - 1.0, z), R, H2, rng, sx_, sz_, cool)
    hd = sc.acc("mid_hoodoos")
    for (x, z, h) in ((28, -30, 7), (31, -34, 10), (34, -29, 6), (-26, -24, 5), (40, -44, 9)):
        y = dunes(x, z) - 0.5
        seed = rng.random() * 50
        hd.lathe((x, y, z), [(1.6, 0), (1.1, h * 0.3), (0.8, h * 0.6), (1.0, h * 0.8), (0.7, h * 0.9), (1.2, h * 0.92),
                             (1.3, h), (0.0, h + 0.4)], 8, "rock", lambda px, py, pz, s=seed: strata(py, s), sm=False,
                 rough=0.12, seed=seed, cap=False)
    for i in range(3):
        x = -120 + i * 110 + rng.uniform(-20, 20)
        cloud(sc, "cloud_%d" % i, (x, rng.uniform(60, 80), rng.uniform(-300, -340)), rng.uniform(8, 12), rng,
              top=hexc("#fff8ee"), under=hexc("#e6d0c0"))


# ------------------------------------------------------------------ 3 Bamboo Temple

def roof(a, cx, cy, cz, inner, outer, drop, lift, col_top, col_under, thick=0.35):
    """A square hip roof with flared, upturned corners: from an inner square (half size `inner`) at cy down to the
    eaves (half `outer`), corners lifted by `lift`."""
    def ring(h, y, curl):
        pts = []
        for k in range(4):
            a0 = k * math.pi / 2
            c0 = (math.cos(a0) - math.sin(a0), math.sin(a0) + math.cos(a0))   # corners (+/-1, +/-1)
            c1 = (math.cos(a0 + math.pi / 2) - math.sin(a0 + math.pi / 2), math.sin(a0 + math.pi / 2) + math.cos(a0 + math.pi / 2))
            for t in (0.0, 0.25, 0.5, 0.75):
                u = c0[0] + (c1[0] - c0[0]) * t
                v = c0[1] + (c1[1] - c0[1]) * t
                cor = abs(t - 0.5) * 2  # 1 at corners, 0 mid-side
                pts.append((cx + u * h, y + curl * cor ** 2.2, cz + v * h))
        return pts
    top = ring(inner, cy, 0.0)
    mid = ring(inner + (outer - inner) * 0.55, cy - drop * 0.7, lift * 0.25)
    eave = ring(outer, cy - drop, lift)
    under = ring(outer, cy - drop - thick, lift)
    und_in = ring(inner * 0.95, cy - drop - thick * 0.5, 0.0)
    n = len(top)
    C = (cx, cy - drop, cz)
    rows = [top, mid, eave]
    for r in range(2):
        for k in range(n):
            j = (k + 1) % n
            a.poly([rows[r][k], rows[r][j], rows[r + 1][j], rows[r + 1][k]], "paint",
                   [col_top] * 2 + [mul(col_top, 1.15)] * 2, out=(cx, cy - 50, cz), sm=True)
    for k in range(n):
        j = (k + 1) % n
        a.poly([eave[k], eave[j], under[j], under[k]], "paint", hexc("#d8c9a8"), out=C)
        a.poly([under[k], under[j], und_in[j], und_in[k]], "paint", col_under, out=(cx, cy + 50, cz))
    a.poly(top, "paint", col_top)


def pagoda(sc, c, rng):
    x, y, z = c
    a = sc.acc("lm_pagoda")
    stone = hexc("#b8b2a6")
    a.box((x, y + 0.4, z), (13, 1.0, 13), "rock", stone, cols=(mul(stone, 1.08), mul(stone, 0.85)))
    a.box((x, y + 1.2, z), (10.5, 0.8, 10.5), "rock", stone, cols=(mul(stone, 1.08), mul(stone, 0.85)))
    for k in range(6):  # steps up the front
        a.box((x, y + 0.15 + k * 0.28, z + 6.5 + 1.6 - k * 0.35), (3.4, 0.28, 0.5), "rock", mul(stone, 0.95))
    wall, pillar, tile, under = hexc("#f0e6d2"), hexc("#b8342a"), hexc("#35494a"), hexc("#c8552e")
    yy = y + 1.6
    base = 8.2
    for t in range(5):
        w = base * (1 - 0.13 * t)
        hgt = 3.4 if t == 0 else 2.5
        bw = w * 0.62
        a.box((x, yy + hgt / 2, z), (bw, hgt, bw), "paint", wall)
        for sx_ in (-1, 1):
            for sz_ in (-1, 1):
                a.box((x + sx_ * bw / 2, yy + hgt / 2, z + sz_ * bw / 2), (0.32, hgt, 0.32), "paint", pillar)
        # a door or shutters on each face, and a red rail on the balcony
        for k in range(4):
            an = k * math.pi / 2
            dx, dz = math.sin(an), math.cos(an)
            a.box((x + dx * (bw / 2 + 0.02), yy + hgt * 0.45, z + dz * (bw / 2 + 0.02)), (bw * 0.35, hgt * 0.6, 0.06),
                  "paint", pillar if t == 0 else hexc("#6a2a22"), ry=an)
        a.box((x, yy + hgt + 0.05, z), (bw + 0.6, 0.12, bw + 0.6), "paint", pillar)
        ry_top = yy + hgt + 0.9
        roof(a, x, ry_top, z, bw * 0.42, w * 0.66, 1.1, 0.75 + 0.05 * t, tile, under)
        yy = ry_top
        if t < 4:
            yy += 0.05
    # the finial: a mast with rings and a gold jewel
    gold = hexc("#e2b84a")
    a.tube([(x, yy, z), (x, yy + 4.5, z)], 0.14, "metal", gold, segs=6)
    for k in range(7):
        a.lathe((x, yy + 0.8 + k * 0.45, z), [(0.42 - k * 0.03, 0), (0.42 - k * 0.03, 0.12)], 10, "metal", gold)
    a.blob((x, yy + 4.7, z), (0.35, 0.45, 0.35), "metal", gold, segs=8, rings=5, rough=0.0)
    return a


def bamboo(a, c, h, rng, green=hexc("#7fae4e")):
    x, y, z = c
    a.sway_base = y
    lean = (rng.uniform(-0.6, 0.6), rng.uniform(-0.3, 0.3))
    pts = []
    n = 8
    for i in range(n + 1):
        t = i / n
        pts.append((x + lean[0] * t * t * h * 0.15, y + h * t, z + lean[1] * t * t * h * 0.15))
    g = mul(green, rng.uniform(0.85, 1.1))

    def cc(i, p):
        return mul(g, 0.9) if i % 2 == 0 else g   # node bands
    a.tube(pts, [0.13 * h / 12] * (n + 1), "bamboo_sway", cc, segs=5, sm=True)
    leaf = hexc("#6a9a3a")
    for i in range(12):
        t = rng.uniform(0.45, 1.0)
        p = Vector(pts[int(t * n)])
        an = rng.uniform(0, 2 * math.pi)
        d = Vector((math.cos(an), -0.35, math.sin(an)))
        side = Vector((-d.z, 0, d.x)) * 0.16
        L = rng.uniform(0.9, 1.5)
        lc = mul(leaf, rng.uniform(0.8, 1.2))
        a.poly([p, p + d * L * 0.5 + side, p + d * L, p + d * L * 0.5 - side], "bamboo_sway", [mul(lc, 0.8), lc,
               mul(lc, 1.2), lc])
    a.sway_base = None


def cherry(a, c, h, rng):
    x, y, z = c
    a.sway_base = y
    bark = hexc("#4a3530")
    trunk = [(x, y, z), (x + 0.3, y + h * 0.3, z), (x - 0.2, y + h * 0.5, z + 0.2)]
    a.tube(trunk, [h * 0.06, h * 0.045, h * 0.035], "wood", bark, segs=6)
    for k in range(4):
        an = k * math.pi / 2 + rng.uniform(-0.3, 0.3)
        e = (x + math.cos(an) * h * 0.35, y + h * rng.uniform(0.62, 0.75), z + math.sin(an) * h * 0.25)
        a.tube([trunk[2], e], [h * 0.03, h * 0.015], "wood", bark, segs=4)
    pinks = [hexc("#f6b8cc"), hexc("#f9cddb"), hexc("#ee9fbb")]
    for i in range(7):
        an = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.1, 0.4) * h
        p = (x + math.cos(an) * rr, y + h * rng.uniform(0.62, 0.9), z + math.sin(an) * rr * 0.7)
        r = h * rng.uniform(0.17, 0.25)
        pk = rng.choice(pinks)

        def cc(nx, ny, nz, q, pk=pk):
            return mix(mul(pk, 0.78), mix(pk, (1, 0.95, 0.97), 0.4), smooth(-0.6, 0.8, ny + 0.2 * nx))
        a.blob(p, (r, r * 0.75, r), "blossom_sway", cc, segs=8, rings=5, rough=0.25, nscale=1.4, seed=rng.random() * 30)
    a.sway_base = None


def stone_lantern(a, c, lit=True):
    x, y, z = c
    st = hexc("#a8a49a")
    a.lathe((x, y, z), [(0.45, 0), (0.45, 0.2), (0.18, 0.3), (0.16, 1.2), (0.35, 1.3), (0.35, 1.4)], 6, "rock", st,
            sm=False, phase=math.pi / 6)
    a.box((x, y + 1.72, z), (0.5, 0.64, 0.5), "rock", st)
    a.box((x, y + 1.72, z), (0.54, 0.34, 0.3), "lamp_glow" if lit else "rock", (1, 1, 1))
    a.box((x, y + 1.72, z), (0.3, 0.34, 0.54), "lamp_glow" if lit else "rock", (1, 1, 1))
    a.lathe((x, y + 2.04, z), [(0.62, 0), (0.55, 0.12), (0.12, 0.45), (0.0, 0.5)], 6, "rock", mul(st, 0.9), sm=False,
            phase=math.pi / 6)
    a.blob((x, y + 2.62, z), (0.1, 0.14, 0.1), "rock", st, segs=6, rings=3, rough=0.0)


def bamboo_temple(sc):
    rng = random.Random(13)
    moss, moss2, earth = hexc("#6f9a58"), hexc("#9ab872"), hexc("#7a6a52")
    PX, PZ = 31.0, -50.0

    def h(x, z):
        hill = 6.5 * smooth(0.0, 1.0, 1.0 - math.hypot((x - PX) / 26.0, (z - PZ) / 18.0)) ** 0.7
        hill = min(hill, 6.0) if math.hypot(x - PX, z - PZ) < 11 else hill
        left = 5.0 * smooth(-8.0, -30.0, x + 0.3 * (z + 20)) * smooth(-10.0, -30.0, z)
        far = smooth(-70.0, -160.0, z) * (18 + 22 * fbm(x, z, 0.012, 3, 7)) + smooth(-170.0, -300.0, z) * 30 * (0.6 + fbm(x, z, 0.008, 3, 8))
        return -0.2 + max(hill, left + 1.2 * fbm(x, z, 0.08, 2, 9)) + far + 0.25 * fbm(x, z, 0.15, 2, 10)

    def col(x, y, z, ny):
        c = mix(moss, moss2, 0.5 + 0.5 * n2(x, z, 0.1))
        far = smooth(-80.0, -250.0, z)
        c = mix(c, hexc("#7f9aa0"), far * 0.6)
        return mix(earth, c, smooth(0.6, 0.85, ny))
    land = sc.acc("mid_land")
    land.terrain(-1.3, -420, 76, 100, h, col, margin=1.6)
    # the flagstone courtyard
    fg = sc.acc("fg_court")
    z = 2.6
    while z > -1.3:
        dz = rng.choice((0.8, 1.0, 1.2))
        x = -16.0 + rng.uniform(-0.6, 0)
        while x < 32:
            L = rng.uniform(0.9, 1.8)
            c = mul(mix(hexc("#b8b4aa"), hexc("#a0a49a"), rng.random()), rng.uniform(0.9, 1.06))
            fg.box((x + L / 2, -0.07, z - dz / 2), (L - 0.07, 0.14, dz - 0.07), "rock", c, cols=(c, mul(c, 0.75)))
            x += L
        z -= dz
    fg.box((8, -0.4, 0.65), (60, 0.5, 4.0), "ground", hexc("#4a6a3a"))  # moss in the joints
    mg = sc.acc("fg_moss")
    mg.terrain(9.5, 2.5, 6, 50, lambda x, z: -0.1 + 0.15 * fbm(x, z, 0.3, 2),
               lambda x, y, z, ny: mix(moss, moss2, 0.5 + 0.5 * n2(x, z, 0.4)), margin=1.6)
    for x in (-3.2, 19.2):
        stone_lantern(mg, (x, 0, 1.2))
    for i in range(50):
        x = rng.choice((rng.uniform(-14, -1), rng.uniform(17, 30)))
        tuft(mg, (x, 0.0, rng.uniform(3, 8)), rng.uniform(0.3, 0.6), hexc("#4f7a3a"), hexc("#a6c47a"), rng, 6)
    # the pagoda on its hill, stairs up to it, lanterns and a gate
    pagoda(sc, (PX, h(PX, PZ) - 0.2, PZ), rng)
    st = sc.acc("lm_stairs")
    for k in range(18):
        t = k / 17
        zz = PZ + 8 + t * 16
        xx = PX - 1 - t * 6
        st.box((xx, h(xx, zz) - 0.1, zz), (3.0, 0.35, 1.0), "rock", hexc("#b0aca0"))
    for (x, zz) in ((PX - 5, PZ + 7), (PX + 5, PZ + 7)):
        stone_lantern(st, (x, h(x, zz) - 0.1, zz))
    gt = sc.acc("lm_gate")
    GX, GZ = -16.0, -30.0
    gy = h(GX, GZ) - 0.3
    red = hexc("#c23a2a")
    for s in (-1, 1):
        gt.tube([(GX + s * 3.2, gy, GZ), (GX + s * 3.0, gy + 8.0, GZ)], 0.36, "paint", red, segs=8)
        gt.box((GX + s * 3.1, gy + 0.3, GZ), (0.95, 0.6, 0.95), "rock", hexc("#3a3a3a"))
    gt.box((GX, gy + 6.6, GZ), (8.2, 0.5, 0.45), "paint", red)
    gt.box((GX, gy + 8.2, GZ), (9.6, 0.5, 0.7), "paint", red, cols=(hexc("#2e2e30"), red))
    gt.box((GX, gy + 8.6, GZ), (10.4, 0.3, 0.9), "paint", hexc("#2e2e30"))
    # bamboo groves (left, and beyond the right of the play) and cherry trees
    bb = sc.acc("mid_bamboo")
    for i in range(70):
        x = rng.uniform(-40, -10)
        zz = rng.uniform(-6, -20)
        if x > -12 and zz > -12:
            continue
        bamboo(bb, (x, h(x, zz) - 0.2, zz), rng.uniform(10, 15), rng)
    for i in range(40):
        x = rng.uniform(40, 60)
        zz = rng.uniform(-10, -40)
        bamboo(bb, (x, h(x, zz) - 0.2, zz), rng.uniform(11, 16), rng)
    ch = sc.acc("mid_cherry")
    for (x, zz, hh) in ((22.0, -24.0, 7.5), (-6.0, -34.0, 6.0), (16.0, -40.0, 5.0), (-30.0, -48.0, 7.0),
                        (44.0, -58.0, 7.0), (4.0, -70.0, 6.0)):
        cherry(ch, (x, h(x, zz) - 0.1, zz), hh, rng)
    fr = sc.acc("far_trees")
    for i in range(70):
        x = rng.uniform(-200, 220)
        zz = rng.uniform(-90, -200)
        pine(fr, (x, h(x, zz) - 0.3, zz), rng.uniform(8, 14), rng, hexc("#4f7a60"), tiers=3)
    for i in range(3):
        x = -120 + i * 120 + rng.uniform(-20, 20)
        cloud(sc, "cloud_%d" % i, (x, rng.uniform(55, 70), rng.uniform(-300, -340)), rng.uniform(10, 14), rng,
              top=hexc("#fff4f2"), under=hexc("#dcd2dc"))


# ------------------------------------------------------------------ 4 Glacier Bay

def iceberg(a, c, r, hgt, rng, sx=1.0, sz=1.0):
    seed = rng.random() * 100
    x, y, z = c

    def cc(px, py, pz):
        k = (py - y) / hgt
        n = n3((px, py, pz), 0.35, seed)
        top = mix(hexc("#e9f7ff"), hexc("#ffffff"), smooth(0.3, 0.9, k))
        crev = mix(hexc("#7fd0ec"), hexc("#48a8d8"), smooth(-0.2, 0.4, n))
        c2 = mix(top, crev, smooth(0.15, 0.45, n) * 0.8)
        return mix(hexc("#5fc8d8"), c2, smooth(-0.05, 0.25, k))  # turquoise at the waterline
    prof = [(r * 1.15, -1.2), (r * 1.1, 0.0), (r, hgt * 0.25), (r * 0.9, hgt * 0.55), (r * rng.uniform(0.5, 0.8), hgt * 0.8),
            (r * rng.uniform(0.2, 0.5), hgt), (0.0, hgt * 1.02)]
    a.lathe((x, y, z), prof, 9, "ice", cc, sm=False, rough=0.32, nscale=0.4, seed=seed, sx=sx, sz=sz, cap=False,
            phase=rng.random() * 3)


def glacier_bay(sc):
    rng = random.Random(14)
    SEA = -0.8
    snow, snow2 = hexc("#eef5fc"), hexc("#c9dcee")
    rockc = hexc("#4a5566")

    def fgh(x, z):
        if z < 2.6 and -18 < x < 34:
            return 0.0
        return 0.35 * smooth(2.6, 5.5, z) * (1 + fbm(x, z, 0.25, 2)) + 0.3 * smooth(-1.0, -3.0, -abs(x - 8) + 26)
    fg = sc.acc("fg_snow")
    fg.terrain(9.5, -1.3, 20, 90, lambda x, z: fgh(x, z) + (0.06 * n2(x * 0.5, z * 2.0, 1.2, 35) if z > 2.6 else 0.0),
               lambda x, y, z, ny: mix(hexc("#bcd2ea"), snow, smooth(0.8, 1.0, ny) * 0.6 +
               0.4 * (0.5 + 0.5 * n2(x, z, 0.3))), material="snow", margin=1.6)
    edge = sc.acc("fg_iceedge")
    for i in range(34):
        x = -18 + i * 1.5 + rng.uniform(-0.2, 0.2)
        edge.box((x, -0.5, -1.45), (1.55, 1.1 + rng.uniform(0, 0.2), 0.5), "ice", hexc("#bfe6f6"),
                 cols=(snow, hexc("#8fd0ea")))
    for x, z, s in ((-6.0, 4.5, 0.9), (23.0, 5.5, 1.2), (-10.0, 1.0, 0.7), (26.5, 1.5, 0.8)):
        rock(edge, (x, 0.0, z), (s * 1.3, s * 0.8, s), rng, snow, rockc)
    # the bay
    sea(sc, SEA)
    # icebergs (bob) and floes
    for i, (x, z, r, hgt, sx_, sz_) in enumerate(((-15, -24, 3.2, 4.5, 1.4, 1.0), (28, -30, 4.0, 6.5, 1.1, 0.9),
                                                    (-36, -58, 6.0, 9.0, 1.3, 1.0), (60, -80, 8.0, 12, 1.4, 1.0),
                                                    (14, -90, 3.0, 3.5, 1.6, 1.0), (-80, -110, 9.0, 11, 1.5, 1.0))):
        b = sc.acc("berg_%d" % i, (x, SEA, z))
        iceberg(b, (x, SEA, z), r, hgt, rng, sx_, sz_)
    for i, (x, z, r) in enumerate(((-6.0, -6.0, 1.2), (22.0, -8.0, 1.6), (3.0, -14.0, 0.8), (-18.0, -12.0, 1.0),
                                   (34.0, -16.0, 1.4))):
        f = sc.acc("floe_%d" % i, (x, SEA, z))
        f.lathe((x, SEA - 0.2, z), [(r, 0), (r * 0.95, 0.32), (r * 0.6, 0.38), (0.0, 0.4)], 7, "ice",
                lambda px, py, pz: mix(hexc("#9fd8ec"), snow, smooth(SEA + 0.1, SEA + 0.2, py)), sm=False,
                rough=0.25, seed=x, sx=1.4, cap=False)
    # the glacier: a wall of blue ice across the head of the bay, its tongue rising back between the peaks
    GZ = -125.0

    def front_z(x):
        return GZ - 8 * fbm(x, 0, 0.03, 2, 21) + 0.0004 * (x - 10) ** 2

    def top_y(x):
        return 9 + 3 * fbm(x, 0, 0.05, 2, 22)
    gl = sc.acc("lm_glacier")
    cols_ = 120
    xs = [-150 + 330 * i / cols_ for i in range(cols_ + 1)]
    rows = 7
    grid = []
    for x in xs:
        col_ = []
        ty = top_y(x)
        for r in range(rows + 1):
            t = r / rows
            y = SEA - 1 + (ty - SEA + 1) * t
            groove = n2(x, 0, 0.9, 23) * 0.6 + n2(x, y, 0.35, 24) * 0.4
            zz = front_z(x) + 1.6 * groove - 3.0 * t * t
            col_.append(gl.vert((x, y, zz)))
        grid.append((col_, ty))
    for i in range(cols_):
        for r in range(rows):
            ids = [grid[i][0][r], grid[i + 1][0][r], grid[i + 1][0][r + 1], grid[i][0][r + 1]]
            cs = []
            for q in ids:
                v = gl.v[q]
                g = n2(v.x, 0, 0.9, 23)
                c = mix(hexc("#d8f0fc"), hexc("#7cc4ea"), smooth(-0.3, 0.4, g))
                c = mix(c, hexc("#3f94cc"), smooth(0.25, 0.6, g) * 0.8)
                c = mix(hexc("#6fc0dc"), c, smooth(SEA, SEA + 2.0, v.y))
                cs.append(c)
            gl.face(ids, "ice", cs, out=(gl.v[ids[0]].x, gl.v[ids[0]].y, -1000))

    def gh(x, z):
        f = front_z(x)
        back = smooth(f, f - 120, z)
        valley = math.exp(-((x - 10) / 60.0) ** 2)
        return top_y(x) - 2.0 + back * (8 + 8 * (1 - valley)) + 1.0 * fbm(x, z, 0.08, 2, 25)

    def gcol(x, y, z, ny):
        streak = n2(x * 0.3, z * 0.05, 1.0, 26)
        c = mix(snow, snow2, 0.5 + 0.5 * n2(x, z, 0.05))
        c = mix(c, hexc("#b8d0e6"), smooth(0.4, 0.7, streak) * 0.6)
        return c
    top = sc.acc("lm_glacier_top")
    top.terrain(GZ - 2, -420, 30, 100, gh, gcol, material="snow", margin=1.6)
    # the peaks round the bay
    def mh(x, z):
        n = max(0.0, 1.0 - abs(fbm(x, z, 0.012, 4, 30)))
        ridge = n ** 2.5
        side = 0.35 + 0.65 * smooth(15.0, 90.0, abs(x - 10))
        return -2 + smooth(-190.0, -280.0, z) * (12 + 40 * ridge * side) + smooth(-150.0, -200.0, z) * 10 * side

    def mcol(x, y, z, ny):
        snowy = smooth(0.74, 0.88, ny) * smooth(8.0, 26.0, y + 8 * n2(x, z, 0.05))
        snowy *= 1.0 - smooth(0.25, 0.45, n2(x * 0.4, y * 1.5, 0.12, 32)) * 0.85   # rock ribs through the snow
        rk = mix(rockc, hexc("#6e7c94"), 0.5 + 0.5 * n2(x, y, 0.1))
        return mix(rk, mix(hexc("#b4cce6"), snow, smooth(0.8, 0.95, ny)), snowy)
    mt = sc.acc("far_peaks")
    mt.terrain(-150, -560, 50, 140, mh, mcol, material="rock", margin=1.6, sm=False)
    # the shores left and right of the bay: rocky with snow
    def sh(x, z):
        side = max(smooth(-30.0, -60.0, x + 0.3 * z), smooth(50.0, 80.0, x - 0.2 * z))
        return SEA - 2 + side * (7 + 8 * fbm(x, z, 0.03, 3, 31)) * smooth(-20.0, -50.0, z)

    def scol(x, y, z, ny):
        s_ = smooth(0.7, 0.88, ny) * smooth(SEA + 2.5, SEA + 6.0, y + 2.0 * n2(x, z, 0.1, 34))
        s_ *= 1.0 - smooth(0.3, 0.5, n2(x * 0.5, y * 1.2, 0.15, 33)) * 0.8
        return mix(mix(rockc, hexc("#7a8698"), 0.5 + 0.5 * n2(x, y, 0.2)), mix(snow2, snow, ny), s_)
    shore = sc.acc("mid_shores")
    shore.terrain(-20, -150, 40, 90, sh, scol, material="rock", margin=1.6, sm=False)
    # a red boathouse and a hut on the left shore: a warm accent and a sense of scale
    hut = sc.acc("lm_huts")
    for (x, z, w, d, hh, ry) in ((-23.0, -64.0, 6.0, 4.5, 3.0, 0.35), (-30.5, -71.0, 4.5, 4.0, 2.6, 0.2)):
        y = max(sh(x, z), sh(x + 2, z), sh(x - 2, z)) - 0.3
        hut.box((x, y - 1.5, z), (w + 1.0, 3.0, d + 1.0), "rock", rockc)
        gable_house(hut, (x, y, z), w, d, hh, hexc("#b8322a"), hexc("#f4f8ff"), rng, ry=ry,
                    windows=(-1, 1), window_mat="window_glow")
    fx, fz = -18.5, -61.0
    fy = sh(fx, fz)
    hut.tube([(fx, fy - 0.3, fz), (fx, fy + 7.0, fz)], 0.08, "metal", hexc("#d8dce4"), segs=4)
    hut.poly([(fx, fy + 6.9, fz), (fx + 2.4, fy + 6.4, fz), (fx, fy + 5.9, fz)], "paint", hexc("#2a6ac8"))
    for i in range(3):
        x = -100 + i * 100 + rng.uniform(-20, 20)
        cloud(sc, "cloud_%d" % i, (x, rng.uniform(70, 90), rng.uniform(-330, -360)), rng.uniform(8, 12), rng,
              under=hexc("#c4d4ea"))


# ------------------------------------------------------------------ 5 Ember Peak

def hexagons(a, x0, x1, z0, z1, r, hfn, colfn):
    """Basalt columns: hexagonal prisms whose tops follow hfn(x, z)."""
    dx = r * math.sqrt(3)
    row = 0
    z = z1
    while z > z0 - r:
        x = x0 + (dx / 2 if row % 2 else 0.0)
        while x < x1:
            top = hfn(x, z)
            out = [(x + (r - 0.03) * math.cos(math.pi / 6 + k * math.pi / 3),
                    z + (r - 0.03) * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
            c = colfn(x, z)
            a.prism(out, top - 2.5, top, "rock", lambda y, c=c, top=top: mul(c, 0.55 + 0.45 * smooth(top - 1.5, top, y)),
                    top=mul(c, 1.15))
            x += dx
        z -= r * 1.5
        row += 1


def ember_peak(sc):
    rng = random.Random(15)
    basalt, basalt2 = hexc("#35323a"), hexc("#4a4450")
    VX, VZ, VR, VH = -26.0, -190.0, 95.0, 46.0

    def cone(x, z):
        d = math.hypot(x - VX, (z - VZ) * 1.1)
        an = math.atan2(z - VZ, x - VX)
        gully = 0.08 * math.sin(an * 22 + 2 * n2(x, z, 0.02, 40)) * smooth(10, 60, d)
        prof = (1 - smooth(0, VR, d)) ** 1.6
        y = VH * prof * (1 + gully) + 0.0
        crater = 7.0 * (1 - smooth(4.0, 11.0, d))
        return y - crater

    def h(x, z):
        base = -0.3 + 0.9 * fbm(x, z, 0.06, 3, 41) * smooth(-2.0, -12.0, z)
        ridge = smooth(30.0, 70.0, x - 0.2 * z) * smooth(-40.0, -90.0, z) * (14 + 16 * (1 - abs(fbm(x, z, 0.03, 3, 42))))
        leftr = smooth(-30.0, -60.0, x) * smooth(-30.0, -70.0, z) * (6 + 6 * fbm(x, z, 0.05, 2, 43))
        return base + max(cone(x, z), ridge, leftr)

    def col(x, y, z, ny):
        c = mix(basalt, basalt2, 0.5 + 0.5 * n2(x, z, 0.1))
        c = mix(c, hexc("#5a3a34"), smooth(0.8, 0.5, ny) * 0.5)
        d = math.hypot(x - VX, (z - VZ) * 1.1)
        c = mix(c, hexc("#7a3a2a"), (1 - smooth(8, 26, d)) * 0.8)     # the hot rim
        return c
    land = sc.acc("mid_land")
    land.terrain(-1.3, -480, 80, 110, h, col, material="rock", margin=1.6)
    # basalt columns: a flat pavement for the play, stepping up beyond its ends and in front
    fg = sc.acc("fg_basalt")

    def ch(x, z):
        if z < 2.8 and -15 < x < 31:
            return 0.0
        return 0.25 + 0.9 * abs(n2(x, z, 0.4, 44)) + 0.4 * smooth(-1, -3, -abs(x - 8) + 23)
    hexagons(fg, -17.0, 33.0, -1.3, 9.5, 0.62, ch, lambda x, z: mix(basalt, basalt2, 0.5 + 0.5 * n2(x, z, 0.7, 45)))
    # glowing seams between the columns beyond the play, and pools of lava at the sides
    lv = sc.acc("fg_lava")
    for (x, z, r) in ((-9.0, 5.5, 1.1), (25.0, 6.5, 1.3), (-13.0, 1.0, 0.8), (30.0, 0.5, 0.9)):
        lv.lathe((x, 0.12, z), [(r, 0), (0.0, 0.02)], 12, "lava_glow", (1, 1, 1), sm=False, rough=0.25, seed=x,
                 sx=1.5, cap=False)
    # lava rivers winding out of the dark plain on both sides
    def river(pts_xz, w):
        pts = []
        for (x, z) in pts_xz:
            pts.append(Vector((x, h(x, z) + 0.08, z)))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            d = (b - a)
            side = Vector((-d.z, 0, d.x)).normalized()
            wa, wb = w * (0.7 + 0.3 * math.sin(i)), w * (0.7 + 0.3 * math.sin(i + 1))
            lv.poly([a - side * wa, b - side * wb, b + side * wb, a + side * wa], "lava_glow", (1, 1, 1),
                    out=(a.x, a.y - 50, a.z))
            for s in (-1, 1):
                lv.poly([a + side * wa * s, b + side * wb * s, b + side * (wb + 0.5) * s + Vector((0, 0.15, 0)),
                         a + side * (wa + 0.5) * s + Vector((0, 0.15, 0))], "rock", hexc("#2a2226"),
                        out=(a.x, a.y - 50, a.z))
    def meander(x0, z0, x1, z1, n, amp, seed):
        out = []
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t + amp * math.sin(t * 7 + seed) * math.sin(t * math.pi)
            z = z0 + (z1 - z0) * t
            out.append((x, z))
        return out
    river(meander(-60, -90, -16, -8, 40, 5.0, 1.0), 1.4)
    river(meander(38, -52, 24, -14, 30, 3.0, 2.0), 0.9)
    river(meander(-8, -60, -30, -40, 14, 2.0, 3.0), 0.8)
    # lava tongues down the volcano's face and the crater's glowing throat
    for k, an in enumerate((1.35, 1.7, 2.05)):
        pts = []
        for i in range(26):
            d = 9 + i * 3.0
            x = VX + math.cos(an + 0.08 * math.sin(i * 0.5 + k)) * d
            z = VZ + math.sin(an + 0.08 * math.sin(i * 0.5 + k)) * d / 1.1
            pts.append((x, z))
        river(pts, 1.4 - 0.2 * k)
    lv.lathe((VX, cone(VX, VZ) + 1.5, VZ), [(8.5, 0), (0.0, -2.0)], 16, "lava_glow", (1, 1, 1), sm=False, rough=0.2,
             cap=False, sz=1 / 1.1)
    sc.empty("smoke_anchor", (VX, VH - 3.0, VZ))
    # spires of black rock at the sides of the plain
    sp = sc.acc("mid_spires")
    for (x, z, hh) in ((-20, -16, 6), (-24, -22, 9), (27, -18, 7), (31, -26, 11), (24, -30, 5), (-34, -34, 12)):
        seed = rng.random() * 40
        sp.lathe((x, h(x, z) - 0.5, z), [(1.8, 0), (1.3, hh * 0.4), (0.9, hh * 0.8), (0.0, hh)], 7, "rock",
                 lambda px, py, pz: mix(basalt, basalt2, n2(px, py, 0.5) * 0.5 + 0.5), sm=False, rough=0.25, seed=seed,
                 cap=False)
    for i in range(4):
        x = -110 + i * 80 + rng.uniform(-20, 20)
        cloud(sc, "cloud_%d" % i, (x, rng.uniform(70, 95), rng.uniform(-330, -380)), rng.uniform(10, 16), rng,
              top=hexc("#e89a7a"), under=hexc("#5a3050"))


# ------------------------------------------------------------------ 6 Harbour Lights

def lit_facade(a, x0, x1, y0, y1, z, rng, lit=0.8, cool=0.25, cw=1.1, rh=1.4):
    """Windows on a facade facing the camera (z): small emissive quads, some dark."""
    x = x0 + cw * 0.6
    while x < x1 - cw * 0.4:
        y = y0 + rh * 0.7
        while y < y1 - rh * 0.3:
            if rng.random() < lit:
                m = "coolwindow_glow" if rng.random() < cool else "window_glow"
                a.poly([(x - cw * 0.28, y - rh * 0.25, z), (x + cw * 0.28, y - rh * 0.25, z),
                        (x + cw * 0.28, y + rh * 0.25, z), (x - cw * 0.28, y + rh * 0.25, z)], m, (1, 1, 1))
            y += rh
        x += cw


def harbour_lights(sc):
    rng = random.Random(16)
    WL = -1.4
    granite, granite2 = hexc("#6a6a74"), hexc("#83808a")
    # the quay: granite setts, a coping stone along the edge, the wall down to the water
    fg = sc.acc("fg_quay")
    z = 2.6
    row = 0
    while z > -1.0:
        dz = 0.55
        x = -16.0 - (0.4 if row % 2 else 0.0)
        while x < 32:
            L = rng.uniform(0.7, 1.1)
            c = mul(mix(granite, granite2, rng.random()), rng.uniform(0.9, 1.08))
            fg.box((x + L / 2, -0.07, z - dz / 2), (L - 0.05, 0.14, dz - 0.05), "rock", c, cols=(c, mul(c, 0.7)))
            x += L
        z -= dz
        row += 1
    fg.box((8, -0.05, -1.15), (60, 0.2, 0.7), "rock", hexc("#9a96a0"))
    fg.box((8, -0.8, -1.35), (60, 1.5, 0.4), "rock", hexc("#4a4a54"))
    fg.terrain(9.5, 2.55, 4, 30, lambda x, z: -0.02, lambda x, y, z, ny: mix(granite, hexc("#55535c"), 0.5 +
               0.5 * n2(x, z, 0.5)), material="rock", margin=1.6)
    # bollards, lamp posts and a stack of crates beyond the play's ends
    for x in (-5.0, 21.0):
        fg.lathe((x, 0, -0.6), [(0.25, 0), (0.22, 0.5), (0.3, 0.6), (0.0, 0.7)], 10, "metal", hexc("#2a2c34"))
    for x in (-2.8, 18.8):
        fg.tube([(x, 0, 0.2), (x, 4.6, 0.2)], [0.09, 0.06], "metal", hexc("#20242c"), segs=8)
        fg.lathe((x, 0, 0.2), [(0.22, 0), (0.18, 0.5), (0.1, 0.7)], 8, "metal", hexc("#20242c"), cap=False)
        fg.blob((x, 4.9, 0.2), (0.32, 0.36, 0.32), "lamp_glow", (1, 1, 1), segs=10, rings=6, rough=0.0)
        fg.lathe((x, 5.15, 0.2), [(0.42, 0), (0.1, 0.3), (0.0, 0.35)], 10, "metal", hexc("#20242c"))
    cr = sc.acc("fg_cargo")
    for (x, z, s, c) in ((24.0, 0.6, 1.1, "#7a4a34"), (25.3, 0.7, 1.0, "#3a5a7a"), (24.6, 0.6, 0.9, "#7a6a3a"),
                         (-8.5, 0.8, 1.0, "#5a3a2e")):
        yy = 0.55 if x != 24.6 else 1.6
        cr.box((x, yy, z), (s, s, s), "wood", hexc(c))
    # the water: dark and glossy
    sea(sc, WL)
    # the far shore: a waterfront town climbing a hill, a clock tower, lights along the promenade
    SZ = -78.0

    def hill(x, z):
        return WL + 1.2 + smooth(SZ - 4, SZ - 90, z) * (26 + 14 * fbm(x, z, 0.02, 3, 50)) + \
            smooth(-80.0, -140.0, x) * 12 * smooth(SZ, SZ - 60, z)
    land = sc.acc("mid_hill")
    land.terrain(SZ + 2, -420, 50, 100, hill, lambda x, y, z, ny: mix(hexc("#1e2438"), hexc("#28304a"), n2(x, z, 0.1) *
                 0.5 + 0.5), material="ground", margin=1.6)
    land.box((8, WL + 0.6, SZ + 3), (600, 1.2, 6), "rock", hexc("#2a2e40"))          # the promenade wall
    town = sc.acc("lm_town")
    lights = sc.acc("lm_town_lights")
    streaks = sc.acc("mid_reflections")
    bld = [hexc("#2a3350"), hexc("#34304a"), hexc("#2e3a4e"), hexc("#3a3a52")]
    x = -150.0
    while x < 170:
        w = rng.uniform(5, 11)
        centre = abs(x - 8) < 26
        tall = rng.uniform(6, 16) + (rng.uniform(8, 26) if -60 < x < -10 or 30 < x < 70 else 0)
        if centre:
            tall *= 0.6
        zf = SZ - rng.uniform(1, 12)
        yb = hill(x, zf) - 0.5
        c = rng.choice(bld)
        town.box((x + w / 2, yb + tall / 2, zf - 4), (w - 0.3, tall, 8), "paint", c, cols=(mul(c, 1.2), c))
        if rng.random() < 0.4:  # a pitched roof
            town.prism([(x + 0.1, zf), (x + w - 0.1, zf), (x + w - 0.1, zf - 8), (x + 0.1, zf - 8)], yb + tall,
                       yb + tall + 0.1, "paint", c)
            town.poly([(x + 0.1, yb + tall, zf), (x + w - 0.1, yb + tall, zf), (x + w / 2, yb + tall + w * 0.35, zf - 4)],
                      "paint", mul(c, 0.8))
        lit_facade(lights, x + 0.3, x + w - 0.3, yb + 0.8, yb + tall - 0.3, zf + 0.02, rng,
                   lit=0.45 if centre else 0.7)
        if tall > 24:
            lights.box((x + w / 2, yb + tall + 0.6, zf - 4), (0.4, 0.4, 0.4), "blink_glow", (1, 1, 1))
        x += w + rng.uniform(0.2, 2.5)
    # the clock tower on the left of the waterfront
    TX = -34.0
    ty = hill(TX, SZ - 6)
    town.box((TX, ty + 14, SZ - 6), (5, 28, 5), "paint", hexc("#3a3448"))
    town.prism([(TX - 2.8, SZ - 3.2), (TX + 2.8, SZ - 3.2), (TX + 2.8, SZ - 8.8), (TX - 2.8, SZ - 8.8)], ty + 28,
               ty + 28.3, "paint", hexc("#4a4458"))
    town.lathe((TX, ty + 28.3, SZ - 6), [(3.3, 0), (0.0, 8.0)], 4, "metal", hexc("#3a5a58"), sm=False, phase=math.pi / 4)
    lights.poly([(TX + 1.6 * math.cos(k * math.pi / 8), ty + 23 + 1.6 * math.sin(k * math.pi / 8), SZ - 3.45)
                 for k in range(16)], "window_glow", (1, 1, 1))
    # promenade lamps and their reflections
    for i in range(60):
        lx = -150 + i * 5.3
        lights.box((lx, WL + 2.2, SZ + 5.5), (0.3, 0.3, 0.3), "bulb_glow", (1, 1, 1))
        L = rng.uniform(14, 22)
        w = 0.35
        streaks.poly([(lx - w, WL + 0.03, SZ + 5.5), (lx + w, WL + 0.03, SZ + 5.5), (lx + w * 1.4, WL + 0.03, SZ + 5.5 + L),
                      (lx - w * 1.4, WL + 0.03, SZ + 5.5 + L)], "reflect_glow", hexc("#ffcf8a"),
                     uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # the suspension bridge, reaching away across the left of the bay
    br = sc.acc("lm_bridge")
    bl = sc.acc("lm_bridge_lights")
    A = Vector((-66.0, 0.0, -38.0))
    B = Vector((-4.0, 0.0, -75.0))
    d = (B - A)
    Ln = d.length
    d.normalize()
    side = Vector((-d.z, 0, d.x))
    DECK = 7.0
    steel = hexc("#3a4258")
    for i in range(40):
        t0, t1 = i / 40, (i + 1) / 40
        p0, p1 = A + d * Ln * t0, A + d * Ln * t1
        br.poly([p0 - side * 3 + Vector((0, DECK, 0)), p1 - side * 3 + Vector((0, DECK, 0)),
                 p1 + side * 3 + Vector((0, DECK, 0)), p0 + side * 3 + Vector((0, DECK, 0))], "paint", steel,
                out=(p0.x, -100, p0.z))
        br.poly([p0 - side * 3 + Vector((0, DECK - 1.2, 0)), p1 - side * 3 + Vector((0, DECK - 1.2, 0)),
                 p1 - side * 3 + Vector((0, DECK, 0)), p0 - side * 3 + Vector((0, DECK, 0))], "paint", mul(steel, 0.8),
                out=p0 + side * 10)
    towers = [0.22, 0.78]
    TOP = 25.0
    br.box((B.x, (WL + DECK) / 2, B.z), (6.5, DECK - WL, 6.5), "rock", hexc("#2e3044"),
           ry=math.atan2(side.x, side.z))                                   # the abutment on the far shore
    for t in towers:
        p = A + d * Ln * t
        for s in (-1, 1):
            q = p + side * s * 3.4
            br.box((q.x, WL + (TOP - WL) / 2, q.z), (1.4, TOP - WL, 1.4), "paint", hexc("#4a3a4a"))
            bl.box((q.x, TOP + 0.4, q.z), (0.6, 0.6, 0.6), "blink_glow", (1, 1, 1))
        br.box((p.x, TOP - 2, p.z), (0.9, 1.2, 7.0), "paint", hexc("#4a3a4a"), ry=math.atan2(side.x, side.z))
        br.box((p.x, DECK + 6, p.z), (0.9, 1.0, 7.0), "paint", hexc("#4a3a4a"), ry=math.atan2(side.x, side.z))
    # main cables with their lights, deck lights, and the lights' reflections
    for s in (-1, 1):
        prev = None
        for i in range(81):
            t = i / 80
            span_t = (t - towers[0]) / (towers[1] - towers[0])
            if t < towers[0]:
                y = DECK + (TOP - DECK) * (t / towers[0]) ** 1.5
            elif t > towers[1]:
                y = DECK + (TOP - DECK) * ((1 - t) / (1 - towers[1])) ** 1.5
            else:
                y = DECK + 1.0 + (TOP - DECK - 1.0) * (2 * span_t - 1) ** 2
            p = A + d * Ln * t + side * s * 3.4 + Vector((0, y, 0))
            if prev is not None:
                br.tube([prev, p], 0.12, "metal", steel, segs=3, sm=False)
            if i % 2 == 0:
                bl.box((p.x, p.y, p.z), (0.28, 0.28, 0.28), "bulb_glow", (1, 1, 1))
            prev = p
        for i in range(0, 60):
            p = A + d * Ln * (i / 60) + side * s * 3.2 + Vector((0, DECK + 0.3, 0))
            bl.box((p.x, p.y, p.z), (0.25, 0.25, 0.25), "bulb_glow", (1, 1, 1))
            if s == 1 and i % 2 == 0:
                q = Vector((p.x, WL + 0.03, p.z))
                streaks.poly([q - Vector((0.5, 0, 0)), q + Vector((0.5, 0, 0)), q + Vector((0.6, 0, 14)),
                              q + Vector((-0.6, 0, 14))], "reflect_glow", hexc("#ffd9a0"),
                             uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # the harbour wheel on the right, turning slowly
    WX, WZ, WR = 44.0, -64.0, 13.0
    HY = WL + WR + 3.5
    lg = sc.acc("lm_wheel_stand")
    for s in (-1, 1):
        for q in (-1, 1):
            lg.tube([(WX + s * 6.5, WL + 0.5, WZ + q * 2.0), (WX, HY, WZ + q * 1.2)], 0.35, "metal", hexc("#c8c0d8"),
                    segs=5)
    lg.box((WX, WL + 1.2, WZ), (16, 2.0, 7), "rock", hexc("#2e3040"))
    wh = sc.acc("wheel", (WX, HY, WZ))
    rim = hexc("#e0d8f0")
    for q in (-0.8, 0.8):
        pts = [(WX + WR * math.cos(2 * math.pi * k / 48), HY + WR * math.sin(2 * math.pi * k / 48), WZ + q)
               for k in range(49)]
        wh.tube(pts, 0.16, "metal", rim, segs=4, sm=False)
    wh.tube([(WX, HY, WZ - 1.3), (WX, HY, WZ + 1.3)], 0.6, "metal", rim, segs=8, cap=True)
    gcols = ["#e8505a", "#f0c040", "#4ab0e8", "#7ad070", "#c070e0", "#f08a40"]
    for k in range(16):
        an = 2 * math.pi * k / 16
        e = Vector((WX + WR * math.cos(an), HY + WR * math.sin(an), WZ))
        for q in (-0.8, 0.8):
            wh.tube([(WX, HY, WZ + q), (e.x, e.y, WZ + q)], 0.07, "metal", rim, segs=3, sm=False)
        gd = sc.acc("gondola_%d" % k, (e.x, e.y, WZ))   # hangs from the rim: the game keeps it upright
        gd.tube([(e.x, e.y, WZ), (e.x, e.y - 0.5, WZ)], 0.05, "metal", rim, segs=3, sm=False)
        gd.box((e.x, e.y - 1.1, WZ), (1.5, 1.4, 1.3), "paint", hexc(gcols[k % 6]))
        gd.box((e.x, e.y - 1.0, WZ + 0.66), (1.1, 0.6, 0.04), "window_glow", (1, 1, 1))
    for k in range(64):
        an = 2 * math.pi * k / 64
        wh.box((WX + (WR + 0.25) * math.cos(an), HY + (WR + 0.25) * math.sin(an), WZ + 0.9), (0.3, 0.3, 0.3),
               "bulb_glow", (1, 1, 1))
    for k in range(10):
        xx = WX - 9 + k * 2
        streaks.poly([(xx - 0.5, WL + 0.03, WZ + 4), (xx + 0.5, WL + 0.03, WZ + 4), (xx + 0.7, WL + 0.03, WZ + 26),
                      (xx - 0.7, WL + 0.03, WZ + 26)], "reflect_glow", hexc("#f0c8ff"), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # boats: a fishing boat and a yacht at their moorings, the ferry crossing far out
    for i, (x, z, s, hull) in enumerate(((-11.0, -9.0, 1.0, "#b84a3a"), (27.0, -15.0, 1.2, "#e8e4e0"))):
        b = sc.acc("boat_%d" % i, (x, WL, z))
        b.lathe((x, WL - 0.5, z), [(0.0, 0), (0.8 * s, 0.15), (1.0 * s, 1.0 * s)], 10, "paint", hexc(hull), sx=3.0,
                sm=True, cap=True)
        b.box((x - 0.6 * s, WL + 1.4 * s, z), (2.0 * s, 1.1 * s, 1.4 * s), "paint", hexc("#e8e4dc"))
        b.box((x - 0.6 * s, WL + 1.5 * s, z + 0.71 * s), (1.5 * s, 0.4 * s, 0.03), "window_glow", (1, 1, 1))
        b.tube([(x + 0.4 * s, WL + 1.0, z), (x + 0.4 * s, WL + 6.5 * s, z)], 0.07, "metal", hexc("#8a8a90"), segs=4)
        b.box((x + 0.4 * s, WL + 6.6 * s, z), (0.22, 0.22, 0.22), "bulb_glow", (1, 1, 1))
        streaks.poly([(x - 1.2, WL + 0.03, z + 1.2), (x + 0.2, WL + 0.03, z + 1.2), (x + 0.4, WL + 0.03, z + 7),
                      (x - 1.4, WL + 0.03, z + 7)], "reflect_glow", hexc("#ffc880"), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    f = sc.acc("ferry", (4.0, WL, -52.0))
    f.lathe((4.0, WL - 0.6, -52.0), [(0.0, 0), (1.4, 0.2), (1.6, 1.6)], 10, "paint", hexc("#e8e8f0"), sx=5.0)
    f.box((4.0, WL + 2.4, -52.0), (12, 1.6, 3.0), "paint", hexc("#f0f0f4"))
    f.box((4.0, WL + 2.4, -50.48), (11, 0.6, 0.04), "window_glow", (1, 1, 1))
    f.box((5.0, WL + 3.8, -52.0), (5, 1.2, 2.6), "paint", hexc("#f0f0f4"))
    f.box((5.0, WL + 3.9, -50.68), (4.4, 0.5, 0.04), "window_glow", (1, 1, 1))
    f.box((1.0, WL + 5.0, -52.0), (0.8, 1.6, 0.8), "paint", hexc("#c83a3a"))
    # scattered house lights on the dark hill above the town
    hl = sc.acc("far_hill_lights")
    for i in range(260):
        x = rng.uniform(-200, 220)
        z = rng.uniform(SZ - 20, SZ - 120)
        hl.box((x, hill(x, z) + 0.4, z), (0.5, 0.5, 0.5), rng.choice(("window_glow", "window_glow", "coolwindow_glow")),
               (1, 1, 1))


# ------------------------------------------------------------------ 7 Aurora Fields

def cabin(sc, a, c, w, d, h, rng, ry, lit, smoke_i=None):
    x, y, z = c
    logs = hexc("#6a4632")
    gable_house(a, (x, y, z), w, d, h, logs, hexc("#f4f8ff"), rng, ry=ry, windows=(-1, 1) if lit else None,
                window_mat="window_glow")
    if lit:
        cr, sr = math.cos(ry), math.sin(ry)
        # a warm glow of the window light on the snow in front
        a.poly([(x + (-w / 2) * cr + (d / 2 + 0.1) * sr, y + 0.03, z - (-w / 2) * sr + (d / 2 + 0.1) * cr),
                (x + (w / 2) * cr + (d / 2 + 0.1) * sr, y + 0.03, z - (w / 2) * sr + (d / 2 + 0.1) * cr),
                (x + (w / 2) * cr + (d / 2 + 2.2) * sr, y + 0.03, z - (w / 2) * sr + (d / 2 + 2.2) * cr),
                (x + (-w / 2) * cr + (d / 2 + 2.2) * sr, y + 0.03, z - (-w / 2) * sr + (d / 2 + 2.2) * cr)],
               "spill_glow", hexc("#ffb060"), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    if smoke_i is not None:
        rh = d * 0.45
        sc.empty("smoke_%d" % smoke_i, (x + w * 0.25 * math.cos(ry) + d * 0.15 * math.sin(ry), y + h + rh * 1.45,
                                         z - w * 0.25 * math.sin(ry) + d * 0.15 * math.cos(ry)))


def aurora_fields(sc):
    rng = random.Random(17)
    snow, snow2, shade = hexc("#e8f0fa"), hexc("#c8d8ec"), hexc("#9ab0cc")

    def h(x, z):
        if z > -1.3:
            if z < 2.6 and -18 < x < 34:
                return 0.0
            return 0.3 * smooth(2.6, 5.0, z) * (1 + fbm(x, z, 0.3, 2)) + 0.3 * smooth(-1, -3, -abs(x - 8) + 26)
        lake = math.hypot((x + 8) / 22.0, (z + 30) / 10.0)
        roll = 1.2 * fbm(x, z, 0.03, 3, 60) * smooth(-2.0, -15.0, z)
        far = smooth(-120.0, -260.0, z) * (20 + 40 * (1 - abs(fbm(x, z, 0.01, 4, 61))) ** 2)
        y = -0.3 + roll + far
        if lake < 1.0:
            y = min(y, -0.5 - 0.3 * (1 - lake))
        return y

    def col(x, y, z, ny):
        c = mix(snow2, snow, 0.5 + 0.5 * n2(x, z, 0.08))
        return mix(shade, c, smooth(0.75, 0.97, ny))
    fg = sc.acc("fg_snow")
    fg.terrain(9.5, -1.3, 16, 70, h, col, material="snow", margin=1.6)
    land = sc.acc("mid_land")
    land.terrain(-1.3, -520, 80, 110, h, col, material="snow", margin=1.6)
    lake = sc.acc("mid_lake")
    lake.lathe((-8.0, -0.52, -30.0), [(21.5, 0), (0.0, 0.0)], 40, "ice", lambda x, y, z: mix(hexc("#86a4cc"),
               hexc("#a4bede"), 0.5 + 0.5 * n2(x, z, 0.2)), sm=False, sz=10.0 / 22.0 * 1.0, cap=False)
    # fence posts and a lantern at the edge of the play
    fp = sc.acc("fg_fence")
    for x in list(range(-14, -1, 2)) + list(range(18, 31, 2)):
        yy = h(x, 3.0)
        fp.box((x, yy + 0.55, 3.0), (0.16, 1.1, 0.16), "wood", hexc("#5a4030"))
        fp.box((x, yy + 1.13, 3.0), (0.22, 0.08, 0.22), "snow", snow)
    for (a0, a1) in ((-14, -2), (18, 30)):
        for yy in (0.45, 0.85):
            fp.box(((a0 + a1) / 2, yy, 3.0), (a1 - a0, 0.08, 0.06), "wood", hexc("#6a4a36"))
    fp.tube([(-2.8, 0, 1.0), (-2.8, 2.8, 1.0)], 0.07, "metal", hexc("#20242c"), segs=6)
    fp.box((-2.8, 3.05, 1.0), (0.4, 0.5, 0.4), "lamp_glow", (1, 1, 1))
    fp.lathe((-2.8, 3.3, 1.0), [(0.36, 0), (0.0, 0.3)], 4, "metal", hexc("#20242c"), phase=math.pi / 4)
    # the village
    vl = sc.acc("lm_village")
    si = 0
    for (x, z, w, d, hh, ry, lit) in ((-32, -34, 6, 4.5, 3, 0.2, True), (-22, -40, 5, 4, 2.6, -0.1, True),
                                      (-40, -46, 7, 5, 3.2, 0.3, True), (-14, -48, 4.5, 4, 2.4, 0.0, False),
                                      (-28, -54, 5, 4, 2.6, 0.15, True), (30, -36, 6, 4.5, 3, -0.25, True),
                                      (40, -44, 5, 4, 2.6, -0.1, True), (26, -52, 4.5, 4, 2.4, 0.1, False)):
        smoke = si if lit and si < 4 else None
        cabin(sc, vl, (x, h(x, z) - 0.1, z), w, d, hh, rng, ry, lit, smoke)
        if smoke is not None:
            si += 1
    # a little chapel with a lit window and a bell cote
    cx, cz = -48.0, -60.0
    cy = h(cx, cz) - 0.1
    gable_house(vl, (cx, cy, cz), 5, 9, 5, hexc("#e8e0d4"), hexc("#f4f8ff"), rng, ry=math.pi / 2 + 0.2, chimney=False)
    vl.box((cx, cy + 9.5, cz + 3.5), (1.6, 3.0, 1.6), "paint", hexc("#e8e0d4"))
    vl.lathe((cx, cy + 11.0, cz + 3.5), [(1.2, 0), (0.0, 3.0)], 4, "paint", hexc("#3a4a6a"), phase=math.pi / 4)
    vl.box((cx, cy + 9.5, cz + 4.32), (0.6, 1.0, 0.05), "window_glow", (1, 1, 1))
    # pines round the village and a dark treeline far off
    pn = sc.acc("mid_pines")
    for i in range(90):
        x = rng.uniform(-80, 90)
        z = rng.uniform(-20, -90)
        if -14 < x < 30 and z > -60:
            continue
        pine(pn, (x, h(x, z) - 0.2, z), rng.uniform(4, 9), rng, hexc("#1e3a34"), snow=snow)
    far = sc.acc("far_pines")
    for i in range(160):
        x = rng.uniform(-220, 240)
        z = rng.uniform(-100, -170)
        pine(far, (x, h(x, z) - 0.2, z), rng.uniform(6, 11), rng, hexc("#18302e"), snow=snow2, tiers=3)
    # the aurora: three curtains high over the tundra
    au = sc.acc("aurora")
    for k, (z0, y0, hgt, x0, x1, amp) in enumerate(((-320.0, 62.0, 60.0, -240.0, 60.0, 30.0),
                                                     (-400.0, 90.0, 80.0, -60.0, 300.0, 40.0),
                                                     (-280.0, 78.0, 40.0, 60.0, 220.0, 25.0))):
        n = 90
        rows = 4
        grid = []
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            z = z0 + amp * math.sin(t * 5.0 + k) + amp * 0.5 * math.sin(t * 13.0 + 2 * k)
            yb = y0 + 12 * math.sin(t * 3.0 + k * 1.7)
            colm = []
            for r in range(rows + 1):
                v = r / rows
                colm.append((au.vert((x, yb + hgt * v, z - v * 20)), (t, v)))
            grid.append(colm)
        for i in range(n):
            for r in range(rows):
                es = [grid[i][r], grid[i + 1][r], grid[i + 1][r + 1], grid[i][r + 1]]
                au.face([e[0] for e in es], "aurora_glow", (1, 1, 1), uvs=[e[1] for e in es])


THEMES = [lighthouse_point, windmill_meadow, sandstone_arch, bamboo_temple, glacier_bay, ember_peak, harbour_lights,
          aurora_fields]


def main():
    for n, fn in enumerate(THEMES):
        if ONLY and n not in ONLY:
            continue
        sc = Scene(n)
        fn(sc)
        sc.export()


main()
