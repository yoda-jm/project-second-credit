"""Fuseflight (game 28) festival backdrops: five night dioramas that stand behind the 16 x 12 arena, one per stage
theme (stages/festival.fuse). Original designs: every place is an invented, generic one (a lantern harbour with a
breakwater and a pier, a hillside temple town with a tiered pagoda, a rocky coast with a striped lighthouse and a
beach bonfire, a fairground with a wheel, a carousel and windmills, an old city square with clock towers and domes);
none copies a real place or building. Deterministic (fixed seeds); output CC BY-SA 4.0; provenance: this script
only (written by Claude Code for the project), no third-party assets, no textures (vertex colours).
Run: .tools/bin/blender -b --factory-startup -P tools/blender/fuseflight_backdrops.py -- \
         godot/games/fuseflight/art/backdrops [n ...]

Coordinates: everything is authored in Godot space (x right, y up, z towards the camera) and converted on export.
The arena is x 0..16, y 0..12 on the plane z = 0; the camera sits near (8, 6, 21) (fov 38). Each backdrop_<n>.glb holds
  fg_*      the foreground strip: the floor the hero runs on (top exactly y = 0 across the view for z -2..+3,
            running on to z = +6), plus props beyond the arena's ends (lantern posts, stone lanterns)
  mid_*     terrain, water and props behind the arena; what lies behind the arena's middle is kept dark and quiet
  lm_*      the landmarks (breakwater and pier, pagoda and temple, lighthouse, wheel and carousel, hall and towers)
  far_*     far shores, ridges and the town beyond, no further than z -200 (the sky dome's radius is 230)
and named nodes the game animates, each with its origin at its pivot:
  0 boat_<i> (bob)
  1 -
  2 beam (rotate about local Y), boat_<i> (bob)
  3 wheel (rotate about local Z) with gondola_<k> (origin at its rim pin: carry it round, keep it upright),
    carousel (rotate about local Y), sails_<i> (rotate about local Z: the sails face the camera)
  4 -
and empties: light_warm_<i> / light_fire_<i> / light_cool_<i> (the game puts an omni light there), spark_<i> (the
bonfire: sparks rise from it), rise_<i> (sky lanterns rise from round it), petal_<i> (petals fall round it).
Material names carry the game's hints: "*glow*" emissive (lantern_glow: paper lanterns, tinted by the vertex
colour; window_glow, lamp_glow, bulb_glow (many-coloured string bulbs), warmbulb_glow, stall_glow, fire_glow,
flame_glow (UV: x across, y up the flame), beam_glow, beacon_glow, clock_glow, lens_glow; reflect_glow = light
streaks lying on the water, UV.y running from the light's foot towards the viewer, tinted by the vertex colour),
"water" (the game swaps a wave shader; vertex colour R marks the shallows), "*sway*" (bent in the breeze by UV.y,
the height above the plant's foot). All other colour is in the vertex colours (COLOR_0, linear), over white materials.
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/fuseflight/art/backdrops")
ONLY = [int(a) for a in argv[1:]]

CAM = Vector((8.0, 6.0, 21.0))
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
    return TAN_W * (CAM.z - z) * margin + 6.0


# ------------------------------------------------------------------ materials

MATS = {}
MAT_DEFS = {
    # name: (base colour, roughness, metallic, emission strength, alpha)
    "ground": ((1, 1, 1), 0.95, 0, 0, 1),
    "rock": ((1, 1, 1), 0.85, 0, 0, 1),
    "paint": ((1, 1, 1), 0.6, 0, 0, 1),
    "roof": ((1, 1, 1), 0.5, 0, 0, 1),
    "wood": ((1, 1, 1), 0.8, 0, 0, 1),
    "metal": ((1, 1, 1), 0.35, 0.7, 0, 1),
    "canvas": ((1, 1, 1), 0.9, 0, 0, 1),
    "water": ((1, 1, 1), 0.1, 0, 0, 1),
    "foliage_sway": ((1, 1, 1), 0.85, 0, 0, 1),
    "blossom_sway": ((1, 1, 1), 0.8, 0, 0, 1),
    "lantern_glow": ((1.0, 0.55, 0.3), 0.4, 0, 3.0, 1),
    "window_glow": ((1.0, 0.72, 0.4), 0.4, 0, 2.5, 1),
    "stall_glow": ((1.0, 0.75, 0.45), 0.4, 0, 1.6, 1),
    "lamp_glow": ((1.0, 0.82, 0.55), 0.4, 0, 4.0, 1),
    "bulb_glow": ((1.0, 0.9, 0.7), 0.4, 0, 4.0, 1),
    "warmbulb_glow": ((1.0, 0.85, 0.6), 0.4, 0, 4.0, 1),
    "fire_glow": ((1.0, 0.45, 0.12), 0.6, 0, 4.0, 1),
    "flame_glow": ((1.0, 0.6, 0.2), 1, 0, 4.0, 1),
    "beam_glow": ((1.0, 0.95, 0.8), 1, 0, 2.0, 1),
    "beacon_glow": ((1.0, 0.2, 0.15), 0.4, 0, 5.0, 1),
    "clock_glow": ((1.0, 0.93, 0.75), 0.4, 0, 2.5, 1),
    "lens_glow": ((1.0, 0.95, 0.8), 0.4, 0, 8.0, 1),
    "reflect_glow": ((1.0, 0.75, 0.4), 1, 0, 1.2, 1),
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


# ------------------------------------------------------------------ shared props


# ------------------------------------------------------------------ screen helpers and shared props

DARK = hexc("#17151c")
LANTERNS = [hexc("#ff3a22"), hexc("#ff6a24"), hexc("#ffa23a"), hexc("#ff4a5e"), hexc("#ffc860")]
UV4 = [(0, 0), (1, 0), (1, 1), (0, 1)]


def sx(xs, z):
    """The world x that shows at arena x `xs` for depth z (the arena plane is z = 0)."""
    return 8.0 + (xs - 8.0) * (CAM.z - z) / CAM.z


def sy(ys, z):
    return 6.0 + (ys - 6.0) * (CAM.z - z) / CAM.z


def xs_of(x, z):
    """Where world x at depth z shows on the arena plane."""
    return 8.0 + (x - 8.0) * CAM.z / (CAM.z - z)


def dist(p):
    return (Vector(p) - CAM).length


def catenary(A, B, sag, n):
    A, B = Vector(A), Vector(B)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = A.lerp(B, t)
        p.y -= sag * 4 * t * (1 - t)
        pts.append(p)
    return pts


def wire(a, pts, col=DARK, r=0.025):
    rr = max(r, 0.0011 * dist(pts[len(pts) // 2]))   # never thinner than about a pixel
    a.tube(pts, rr, "metal", col, segs=3, sm=False)


def reflection(refl, x, y, z, wl, w, col, k=1.0):
    """A streak of light on the water under a light at (x, y, z), running towards the camera."""
    h = y - wl
    if h <= 0.05 or refl is None:
        return
    d = Vector((CAM.x - x, CAM.z - z)).normalized()
    p = Vector((-d.y, d.x))
    L = min(1.5 + h * 1.7, 34.0) * k
    w = max(w, 0.0016 * dist((x, y, z)))
    fx, fz = x + d.x * 0.15, z + d.y * 0.15
    yy = wl + 0.05
    refl.poly([(fx - p.x * w, yy, fz - p.y * w), (fx + p.x * w, yy, fz + p.y * w),
               (fx + d.x * L + p.x * w * 1.7, yy, fz + d.y * L + p.y * w * 1.7),
               (fx + d.x * L - p.x * w * 1.7, yy, fz + d.y * L - p.y * w * 1.7)], "reflect_glow", col, uvs=UV4)


def lantern(a, c, r, col, segs=7, caps=True):
    """A round paper lantern (lit from within), with dark rims top and bottom."""
    x, y, z = c
    prof = [(r * 0.45, -r * 0.82), (r * 0.9, -r * 0.45), (r, 0.0), (r * 0.9, r * 0.45), (r * 0.45, r * 0.82)]
    a.lathe((x, y, z), prof, segs, "lantern_glow", col, sm=True, cap=True)
    if caps:
        a.lathe((x, y + r * 0.78, z), [(r * 0.5, 0), (r * 0.5, r * 0.2), (0.0, r * 0.24)], 5, "metal", DARK, sm=False)
        a.lathe((x, y - r * 0.98, z), [(r * 0.48, 0), (r * 0.48, r * 0.2)], 5, "metal", DARK, sm=False, cap=False)


def lantern_string(a, A, B, sag, step, r, rng, refl=None, wl=0.0, palette=LANTERNS, segs=6, caps=False, hang=1.3):
    L = (Vector(B) - Vector(A)).length
    n = max(2, int(L / step))
    pts = catenary(A, B, sag, n * 2)
    wire(a, pts)
    for i in range(1, n):
        p = pts[i * 2]
        col = rng.choice(palette)
        lantern(a, (p.x, p.y - r * hang, p.z), r, col, segs=segs, caps=caps)
        if refl is not None:
            reflection(refl, p.x, p.y - r * hang, p.z, wl, r * 0.9, mul(col, 0.9))


def bulb_string(a, A, B, sag, step, size, material="bulb_glow", wire_col=DARK):
    L = (Vector(B) - Vector(A)).length
    n = max(2, int(L / step))
    pts = catenary(A, B, sag, n)
    wire(a, pts, wire_col)
    s = max(size, 0.0018 * dist(pts[len(pts) // 2]))
    for p in pts[1:-1]:
        a.box((p.x, p.y - s * 0.6, p.z), (s, s * 1.2, s), material, (1, 1, 1))
    return pts


def lamp_post(a, c, h, r=0.3, post=hexc("#1c1a22"), arms=0):
    x, y, z = c
    a.lathe((x, y, z), [(0.28, 0), (0.24, 0.5), (0.12, 0.7)], 8, "metal", post, cap=False)
    a.tube([(x, y, z), (x, y + h, z)], [0.09, 0.06], "metal", post, segs=6)
    tops = [(x, y + h + r, z)]
    if arms:
        tops = []
        for s in (-1, 1):
            a.tube([(x, y + h - 0.6, z), (x + s * 0.5, y + h - 0.3, z), (x + s * 0.8, y + h - 0.4, z)], 0.045, "metal",
                   post, segs=4)
            tops.append((x + s * 0.8, y + h - 0.4 - r * 1.1, z))
    for t in tops:
        a.blob(t, (r, r * 1.15, r), "lamp_glow", (1, 1, 1), segs=8, rings=5, rough=0.0)
        a.lathe((t[0], t[1] + r * 1.0, t[2]), [(r * 1.2, 0), (r * 0.3, r * 0.6), (0.0, r * 0.75)], 8, "metal", post)
    return tops


def hip_roof(a, cx, cy, cz, ix, iz, ox, oz, drop, lift, top, under=hexc("#2a2026"), thick=0.25, ry=0.0):
    """A hipped roof with upturned corners: from an inner rectangle (half sizes ix, iz) at cy down to the eaves
    (half ox, oz) at cy - drop, the corners lifted by `lift`; turned by ry about Y."""
    cr, sr = math.cos(ry), math.sin(ry)

    def ring(hx, hz, y, curl):
        pts = []
        cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        for k in range(4):
            c0, c1 = cs[k], cs[(k + 1) % 4]
            for t in (0.0, 0.25, 0.5, 0.75):
                u = c0[0] + (c1[0] - c0[0]) * t
                v = c0[1] + (c1[1] - c0[1]) * t
                cor = abs(t - 0.5) * 2
                px, pz = u * hx, v * hz
                pts.append((cx + px * cr + pz * sr, y + curl * cor ** 2.2, cz - px * sr + pz * cr))
        return pts
    tp = ring(ix, iz, cy, 0.0)
    mid = ring(ix + (ox - ix) * 0.55, iz + (oz - iz) * 0.55, cy - drop * 0.72, lift * 0.25)
    eave = ring(ox, oz, cy - drop, lift)
    und = ring(ox, oz, cy - drop - thick, lift)
    und_in = ring(ix * 0.95, iz * 0.95, cy - drop - thick * 0.5, 0.0)
    n = len(tp)
    rows = [tp, mid, eave]
    for r in range(2):
        for k in range(n):
            j = (k + 1) % n
            a.poly([rows[r][k], rows[r][j], rows[r + 1][j], rows[r + 1][k]], "roof",
                   [top] * 2 + [mul(top, 1.25)] * 2, out=(cx, cy - 50, cz), sm=True)
    for k in range(n):
        j = (k + 1) % n
        a.poly([eave[k], eave[j], und[j], und[k]], "roof", mul(top, 0.7), out=(cx, cy - drop, cz))
        a.poly([und[k], und[j], und_in[j], und_in[k]], "roof", under, out=(cx, cy + 50, cz))
    a.poly(tp, "roof", top)
    return [eave[k] for k in (0, 4, 8, 12)]   # the four corners


def windows_on(a, cx, cy, cz, w, h, ry, cols, rows, mat_name="window_glow", lit=0.7, rng=None, ww=0.5, wh=0.6,
               side=1.0, depth=0.5):
    """Windows on the face of a box (centre cx, cy, cz; face half-depth `depth` along local z, turned by ry)."""
    cr, sr = math.cos(ry), math.sin(ry)
    for i in range(cols):
        for j in range(rows):
            if rng and rng.random() > lit:
                continue
            u = (i + 0.5) / cols * w - w / 2
            v = (j + 0.5) / rows * h - h / 2
            s = depth * side + 0.03 * side
            px, pz = u * cr + s * sr, -u * sr + s * cr
            a.box((cx + px, cy + v, cz + pz), (ww, wh, 0.04), mat_name, (1, 1, 1), ry=ry)


def eastern_house(a, c, w, d, h, ry, rng, lit=0.7, wall=hexc("#4a3e3a"), timber=hexc("#241a18"),
                  roof_col=hexc("#2a3038"), lanterns=None, refl=None, wl=0.0):
    """A plastered house with a dark timber frame, paper windows and a hipped roof with lifted corners."""
    x, y, z = c
    a.box((x, y + h / 2, z), (w, h, d), "paint", wall, ry=ry, cols=(wall, mul(wall, 0.8)))
    a.box((x, y + h - 0.12, z), (w + 0.08, 0.24, d + 0.08), "wood", timber, ry=ry)
    a.box((x, y + 0.2, z), (w + 0.08, 0.4, d + 0.08), "wood", timber, ry=ry)
    cols = max(1, int(w / 1.6))
    windows_on(a, x, y + h * 0.5, z, w * 0.85, h * 0.5, ry, cols, 1, lit=lit, rng=rng, ww=0.9, wh=h * 0.35,
               depth=d / 2)
    corners = hip_roof(a, x, y + h + d * 0.32, z, w * 0.32, 0.12, w / 2 + 0.5, d / 2 + 0.5, d * 0.32 + 0.25, 0.35,
                       roof_col, ry=ry)
    if lanterns is not None:
        for q in corners:
            if q[2] > z - 0.1 or rng.random() < 0.3:
                col = rng.choice(LANTERNS)
                lantern(lanterns, (q[0], q[1] - 0.45, q[2]), 0.2, col, segs=5, caps=False)
    return corners


def pagoda(a, lan, c, s, rng):
    """A five-tier pagoda (our own: cream walls, red posts, dark tiles, a gold finial), lanterns at the eaves."""
    x, y, z = c
    stone = hexc("#5a5650")
    a.box((x, y + 0.5 * s, z), (12 * s, 1.0 * s, 12 * s), "rock", stone, cols=(mul(stone, 1.1), mul(stone, 0.8)))
    a.box((x, y + 1.2 * s, z), (10 * s, 0.6 * s, 10 * s), "rock", stone)
    wall, pillar, tile = hexc("#6a5a4a"), hexc("#7a1e18"), hexc("#28323a")
    yy = y + 1.5 * s
    base = 8.0 * s
    for t in range(5):
        w = base * (1 - 0.13 * t)
        hgt = (3.2 if t == 0 else 2.4) * s
        bw = w * 0.62
        a.box((x, yy + hgt / 2, z), (bw, hgt, bw), "paint", wall)
        for sx_ in (-1, 1):
            for sz_ in (-1, 1):
                a.box((x + sx_ * bw / 2, yy + hgt / 2, z + sz_ * bw / 2), (0.32 * s, hgt, 0.32 * s), "paint", pillar)
        for k in range(4):
            an = k * math.pi / 2
            dx, dz = math.sin(an), math.cos(an)
            a.box((x + dx * (bw / 2 + 0.03), yy + hgt * 0.45, z + dz * (bw / 2 + 0.03)), (bw * 0.42, hgt * 0.55, 0.06),
                  "window_glow", (1, 1, 1), ry=an)
        a.box((x, yy + hgt + 0.05 * s, z), (bw + 0.6 * s, 0.12 * s, bw + 0.6 * s), "paint", pillar)
        ry_top = yy + hgt + 0.9 * s
        corners = hip_roof(a, x, ry_top, z, bw * 0.42, bw * 0.42, w * 0.66, w * 0.66, 1.1 * s, (0.7 + 0.05 * t) * s,
                           tile)
        for q in corners:
            lantern(lan, (q[0], q[1] - 0.55 * s, q[2]), 0.32 * s, LANTERNS[t % len(LANTERNS)], segs=6, caps=False)
            wire(lan, [Vector(q), Vector((q[0], q[1] - 0.25 * s, q[2]))])
        yy = ry_top + 0.05 * s
    gold = hexc("#b08a3a")
    a.tube([(x, yy, z), (x, yy + 4.2 * s, z)], 0.14 * s, "metal", gold, segs=6)
    for k in range(6):
        a.lathe((x, yy + 0.8 * s + k * 0.45 * s, z), [(0.42 * s - k * 0.03 * s, 0), (0.42 * s - k * 0.03 * s, 0.12 * s)],
                10, "metal", gold)
    a.blob((x, yy + 4.4 * s, z), (0.35 * s, 0.45 * s, 0.35 * s), "lamp_glow", (1, 1, 1), segs=8, rings=5, rough=0.0)
    return yy + 4.8 * s


def cherry(a, c, h, rng, pinks=(hexc("#c87090"), hexc("#d890a8"), hexc("#b05878"))):
    x, y, z = c
    a.sway_base = y
    bark = hexc("#2e2226")
    trunk = [(x, y, z), (x + 0.3 * h / 6, y + h * 0.3, z), (x - 0.2 * h / 6, y + h * 0.5, z + 0.2)]
    a.tube(trunk, [h * 0.06, h * 0.045, h * 0.035], "wood", bark, segs=6)
    for k in range(4):
        an = k * math.pi / 2 + rng.uniform(-0.3, 0.3)
        e = (x + math.cos(an) * h * 0.35, y + h * rng.uniform(0.62, 0.75), z + math.sin(an) * h * 0.25)
        a.tube([trunk[2], e], [h * 0.03, h * 0.015], "wood", bark, segs=4)
    for i in range(8):
        an = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.1, 0.42) * h
        p = (x + math.cos(an) * rr, y + h * rng.uniform(0.6, 0.92), z + math.sin(an) * rr * 0.7)
        r = h * rng.uniform(0.17, 0.25)
        pk = rng.choice(pinks)

        def cc(nx, ny, nz, q, pk=pk):
            return mix(mul(pk, 0.55), mix(pk, (1, 0.9, 0.94), 0.3), smooth(-0.7, 0.6, -ny * 0.6 + 0.4 * nz))
        a.blob(p, (r, r * 0.75, r), "blossom_sway", cc, segs=8, rings=5, rough=0.25, nscale=1.4,
               seed=rng.random() * 30)
    a.sway_base = None


def round_tree(a, c, h, rng, green, material="foliage_sway"):
    x, y, z = c
    a.sway_base = y
    a.tube([(x, y, z), (x, y + h * 0.4, z)], h * 0.05, "wood", hexc("#1e1816"), segs=4)
    for i in range(2):
        r = h * rng.uniform(0.26, 0.34)
        p = (x + rng.uniform(-0.15, 0.15) * h, y + h * (0.58 + 0.18 * i), z + rng.uniform(-0.1, 0.1) * h)

        def cc(nx, ny, nz, q):
            return mix(mul(green, 0.6), mul(green, 1.3), smooth(-0.6, 0.8, ny))
        a.blob(p, (r, r * 0.85, r), material, cc, segs=7, rings=4, rough=0.2, nscale=1.2, seed=rng.random() * 40)
    a.sway_base = None


def pine(a, c, h, rng, green, tiers=3):
    a.sway_base = c[1]
    x, y, z = c
    a.lathe((x, y, z), [(h * 0.05, 0), (h * 0.05, h * 0.2)], 4, "wood", hexc("#221a16"), sm=False, cap=False)
    for i in range(tiers):
        t0 = 0.15 + i * (0.75 / tiers)
        r = h * 0.3 * (1 - i / (tiers + 0.6))
        yb = h * t0
        yt = yb + h * 0.45

        def cc(px, py, pz, yb=yb, yt=yt):
            return mul(green, 0.75 + 0.4 * (py - y - yb) / (yt - yb))
        a.lathe((x, y, z), [(r, yb), (r * 0.55, yb + (yt - yb) * 0.35), (0.0, yt)], 6, "foliage_sway", cc,
                sm=False, cap=False, rough=0.12, seed=rng.random() * 30, phase=rng.random())
    a.sway_base = None


def rock(a, c, r, rng, top, side, segs=7, rings=4):
    def cc(nx, ny, nz, q):
        return mix(side, top, smooth(0.1, 0.8, ny))
    a.blob(c, r, "rock", cc, segs=segs, rings=rings, rough=0.3, nscale=0.9, seed=rng.random() * 50, sm=False, cut=-0.4)


def person(a, c, h, col, rng):
    x, y, z = c
    w = rng.uniform(0.9, 1.15)
    a.lathe((x, y, z), [(0.13 * h * w, 0.0), (0.16 * h * w, 0.25 * h), (0.15 * h * w, 0.55 * h), (0.12 * h * w, 0.78 * h),
                        (0.05 * h, 0.82 * h)], 6, "canvas", col, sm=True, cap=True)
    a.blob((x, y + 0.9 * h, z), (0.08 * h, 0.1 * h, 0.08 * h), "canvas", col, segs=6, rings=4, rough=0.0)


def flame(a, c, h, w, n=3, rot=0.0):
    x, y, z = c
    for k in range(n):
        an = rot + k * math.pi / n
        dx, dz = math.cos(an) * w / 2, math.sin(an) * w / 2
        a.poly([(x - dx, y, z - dz), (x + dx, y, z + dz), (x + dx, y + h, z + dz), (x - dx, y + h, z - dz)],
               "flame_glow", (1, 1, 1), uvs=UV4)


def boat(sc, name, c, s, rng, hull, wl, refl, lanterns=True, cabin=True, flip=False):
    """A wooden harbour boat (bobs as one node): hull, cabin with a lit window, a mast and lanterns strung from
    the masthead to the bow and the stern."""
    x, _, z = c
    b = sc.acc(name, (x, wl, z))
    f = -1.0 if flip else 1.0
    b.lathe((x, wl - 0.45 * s, z), [(0.0, 0), (0.75 * s, 0.12 * s), (1.0 * s, 0.85 * s), (1.0 * s, 1.0 * s)], 10, "paint",
            lambda px, py, pz: hull if py > wl + 0.15 * s else mul(hull, 0.45), sx=3.0, sm=True, cap=True)
    b.box((x, wl + 0.53 * s, z), (5.6 * s, 0.06 * s, 1.7 * s), "wood", hexc("#4a3628"))
    if cabin:
        cx = x - 0.8 * s * f
        b.box((cx, wl + 0.95 * s, z), (1.8 * s, 0.9 * s, 1.3 * s), "wood", hexc("#5a4030"))
        b.box((cx, wl + 1.45 * s, z), (2.2 * s, 0.12 * s, 1.6 * s), "roof", hexc("#22242c"))
        b.box((cx, wl + 1.0 * s, z + 0.66 * s), (1.2 * s, 0.35 * s, 0.03), "window_glow", (1, 1, 1))
    top = (x + 0.6 * s * f, wl + 5.0 * s, z)
    b.tube([(x + 0.6 * s * f, wl + 0.5 * s, z), top], 0.06 * s, "wood", hexc("#2e2018"), segs=4)
    b.box((top[0], top[1] - 0.2 * s, top[2]), (0.2 * s, 0.2 * s, 0.2 * s), "lamp_glow", (1, 1, 1))
    reflection(refl, top[0], top[1], top[2], wl, 0.15 * s, hexc("#ffd090"))
    if lanterns:
        for end in ((x + 2.9 * s, wl + 0.9 * s, z), (x - 2.9 * s, wl + 1.0 * s, z)):
            lantern_string(b, top, end, 0.35 * s, 0.55 * s, 0.14 * s, rng, refl=None)
            pts = catenary(top, end, 0.35 * s, 4)
            for p in pts[1:-1]:
                reflection(refl, p.x, p.y, p.z, wl, 0.16 * s, hexc("#ff7a3a"), 0.8)
    return b


def sea(sc, level, near_z=-2.0, far_z=-200.0, shallow_fn=None, rows=50, cols=60):
    a = sc.acc("mid_sea")

    def col(x, y, z, ny):
        s = shallow_fn(x, z) if shallow_fn else 0.0
        return (s, 0.0, 0.0)
    a.terrain(near_z, far_z, rows, cols, lambda x, z: level, col, material="water", sm=True, margin=1.9)
    return a


def plank_floor(fg, rng, c0, c1, z0=6.0, z1=-2.0, dz=0.42):
    z = z0
    while z > z1:
        x = -18.0
        while x < 34:
            L = rng.uniform(2.5, 4.5)
            c = mul(mix(c0, c1, rng.random()), rng.uniform(0.85, 1.05))
            fg.box((x + L / 2, -0.06, z - dz / 2), (L - 0.04, 0.12, dz - 0.04), "wood", c, cols=(c, mul(c, 0.6)))
            x += L
        z -= dz


def far_lights(a, n, rng, xr, zr, hfn, mats=("window_glow", "window_glow", "lamp_glow"), size=0.45):
    for i in range(n):
        z = rng.uniform(*zr)
        x = rng.uniform(*xr)
        y = hfn(x, z)
        s = max(size, 0.0015 * dist((x, y, z)))
        a.box((x, y + s, z), (s, s, s), rng.choice(mats), (1, 1, 1))


# ------------------------------------------------------------------ 0 Lantern Harbour

def lantern_harbour(sc):
    rng = random.Random(100)
    WL = -1.1
    refl = sc.acc("mid_reflections")
    # the quay: a deck of dark boards on piles, a beam along its edge
    fg = sc.acc("fg_deck")
    plank_floor(fg, rng, hexc("#4a3a30"), hexc("#6a5242"))
    fg.box((8, -0.32, -2.42), (64, 0.5, 0.3), "wood", hexc("#2e241e"))
    x = -16.0
    while x < 34:
        fg.tube([(x, WL - 0.6, -2.45), (x, -0.1, -2.45)], 0.17, "wood", hexc("#241c18"), segs=6)
        x += 2.3
    # lantern posts beyond the arena's ends, strung with lanterns back to the breakwater and the pier
    posts = sc.acc("fg_posts")
    for px, side in ((-2.0, -1), (18.0, 1)):
        posts.lathe((px, 0, -1.0), [(0.3, 0), (0.25, 0.4), (0.13, 0.55)], 8, "rock", hexc("#3a3640"), cap=False)
        posts.tube([(px, 0, -1.0), (px, 5.6, -1.0)], [0.1, 0.08], "wood", hexc("#2a1e18"), segs=6)
        posts.tube([(px, 5.3, -1.0), (px - side * 0.9, 5.25, -1.0)], 0.05, "wood", hexc("#2a1e18"), segs=4)
        lantern(posts, (px - side * 0.9, 4.55, -1.0), 0.42, LANTERNS[0 if side < 0 else 3], segs=10)
        wire(posts, [Vector((px - side * 0.9, 5.25, -1.0)), Vector((px - side * 0.9, 4.9, -1.0))])
        sc.empty("light_warm_%d" % (0 if side < 0 else 1), (px - side * 0.9, 4.4, -0.6))
        far = (sx(-3.5 if side < 0 else 19.5, -14.0), 4.4, -14.0)
        lantern_string(posts, (px, 5.5, -1.0), far, 1.0, 0.95, 0.2, rng, refl=refl, wl=WL, segs=7, caps=True)
    sea(sc, WL, near_z=-2.3, far_z=-205.0)

    # the breakwater on the left: a granite mole running out into the bay, lantern posts strung together, a light at
    # its end
    mole = sc.acc("lm_breakwater")
    lan = sc.acc("lm_breakwater_lanterns")
    P0, P1 = Vector((-9.0, 0, -6.0)), Vector((-50.0, 0, -88.0))
    d = (P1 - P0)
    Ln = d.length
    d.normalize()
    side = Vector((d.z, 0, -d.x))   # points into the harbour (to the right)
    ry = math.atan2(d.x, d.z)
    TOP = WL + 1.5
    n = int(Ln / 3.0)
    for i in range(n):
        p = P0 + d * (Ln * (i + 0.5) / n)
        c = mul(mix(hexc("#3a3a46"), hexc("#4a4652"), rng.random()), rng.uniform(0.85, 1.1))
        mole.box((p.x, (TOP + WL - 1.0) / 2, p.z), (4.2, TOP - WL + 1.0, Ln / n - 0.08), "rock", c,
                 cols=(mul(c, 1.15), mul(c, 0.7)), ry=ry)
        if i % 2 == 0:
            for s in (-1, 1):
                q = p + side * s * 2.6 + d * rng.uniform(-1, 1)
                rock(mole, (q.x, WL - 0.2, q.z), (1.1, 0.8, 1.0), rng, hexc("#3a3844"), hexc("#22222c"), segs=6, rings=3)
    prev = None
    k = 0
    for i in range(0, n + 1, 2):
        p = P0 + d * (Ln * i / n) + side * 1.6
        h = 4.2
        mole.tube([(p.x, TOP, p.z), (p.x, TOP + h, p.z)], 0.09, "wood", hexc("#2a1e18"), segs=5)
        lantern(lan, (p.x, TOP + h - 0.5, p.z), 0.32, LANTERNS[k % 5], segs=7)
        reflection(refl, p.x, TOP + h - 0.5, p.z, WL, 0.3, LANTERNS[k % 5])
        if prev is not None:
            lantern_string(lan, prev, (p.x, TOP + h, p.z), 0.8, 0.9, 0.17, rng, refl=refl, wl=WL, segs=6)
        prev = (p.x, TOP + h, p.z)
        k += 1
    # the harbour light at the end: a squat white tower with a red lantern
    E = P1 + d * 2.0
    mole.lathe((E.x, WL - 0.5, E.z), [(3.0, 0), (3.0, TOP - WL + 0.5)], 10, "rock", hexc("#3e3c48"))
    mole.lathe((E.x, TOP, E.z), [(1.3, 0), (1.0, 6.0), (1.25, 6.1), (1.25, 6.3)], 10, "paint",
               lambda x, y, z: hexc("#c8c4c0") if (y - TOP) % 2.0 < 1.4 else hexc("#a83a32"))
    mole.box((E.x, TOP + 6.9, E.z), (1.2, 1.2, 1.2), "beacon_glow", (1, 1, 1))
    mole.lathe((E.x, TOP + 7.5, E.z), [(1.0, 0), (0.0, 0.9)], 8, "metal", hexc("#3a2a2a"))
    reflection(refl, E.x, TOP + 6.9, E.z, WL, 0.8, hexc("#ff4a3a"), 1.4)
    # boats moored inside the breakwater
    hulls = [hexc("#7a2a22"), hexc("#2a4a6a"), hexc("#6a5a3a"), hexc("#3a5a4a"), hexc("#5a2a4a")]
    bi = 0
    for t, s in ((0.2, 1.0), (0.42, 1.15), (0.66, 1.25)):
        p = P0 + d * (Ln * t) + side * 6.5
        boat(sc, "boat_%d" % bi, (p.x, 0, p.z), s, rng, hulls[bi % 5], WL, refl, flip=bi % 2 == 1)
        bi += 1

    # the pier on the right: a wooden walk on piles out to a pavilion, lamps all along, bulbs strung between them
    pier = sc.acc("lm_pier")
    pl = sc.acc("lm_pier_lights")
    Q0, Q1 = Vector((22.0, 0, -2.4)), Vector((38.0, 0, -66.0))
    d2 = (Q1 - Q0)
    L2 = d2.length
    d2.normalize()
    s2 = Vector((d2.z, 0, -d2.x))
    ry2 = math.atan2(d2.x, d2.z)
    DECK = 0.15
    npl = int(L2 / 1.2)
    for i in range(npl):
        p = Q0 + d2 * (L2 * (i + 0.5) / npl)
        c = mul(mix(hexc("#4a3a30"), hexc("#5e4a3a"), rng.random()), 1.0)
        pier.box((p.x, DECK - 0.1, p.z), (3.4, 0.2, L2 / npl - 0.06), "wood", c, ry=ry2)
        if i % 3 == 0:
            for s in (-1, 1):
                q = p + s2 * s * 1.6
                pier.tube([(q.x, WL - 0.5, q.z), (q.x, DECK - 0.2, q.z)], 0.13, "wood", hexc("#241c18"), segs=5)
    for s in (-1, 1):   # railings
        a = Q0 + s2 * s * 1.65 + Vector((0, DECK + 0.9, 0))
        b = Q1 + s2 * s * 1.65 + Vector((0, DECK + 0.9, 0))
        pier.tube([a, b], 0.05, "wood", hexc("#3a2c22"), segs=4)
    prev = {}
    for i in range(0, 11):
        t = i / 10
        for s in (-1, 1):
            p = Q0 + d2 * (L2 * t * 0.95) + s2 * s * 1.65
            tops = lamp_post(pier, (p.x, DECK, p.z), 3.2, r=0.22)
            reflection(refl, p.x, DECK + 3.4, p.z, WL, 0.25, hexc("#ffd8a0"))
            top = (p.x, DECK + 3.3, p.z)
            if s in prev:
                bulb_string(pl, prev[s], top, 0.45, 0.6, 0.11, "warmbulb_glow")
            prev[s] = top
        if i % 2 == 1 and i < 10:   # lanterns across the walk
            a = Q0 + d2 * (L2 * t * 0.95) - s2 * 1.65 + Vector((0, DECK + 3.2, 0))
            b = Q0 + d2 * (L2 * t * 0.95) + s2 * 1.65 + Vector((0, DECK + 3.2, 0))
            lantern_string(pl, a, b, 0.5, 0.8, 0.18, rng, refl=refl, wl=WL, segs=6)
    # the pavilion at the pier's end: two lifted roofs, lit screens, lanterns at every corner
    pv = sc.acc("lm_pavilion")
    C = Q1 + d2 * 3.0
    pier.box((C.x, DECK - 0.1, C.z), (9, 0.3, 9), "wood", hexc("#4a3a30"), ry=ry2)
    for s in (-1, 1):
        for q in (-1, 1):
            pp = C + s2 * s * 3.6 + d2 * q * 3.6
            pv.tube([(pp.x, WL - 0.5, pp.z), (pp.x, DECK + 4.0, pp.z)], 0.2, "paint", hexc("#6a1a16"), segs=6)
    pv.box((C.x, DECK + 1.9, C.z), (6.0, 3.4, 6.0), "window_glow", (1, 1, 1), ry=ry2)
    for k, (yb, half, lift) in enumerate(((DECK + 5.4, 5.6, 0.9), (DECK + 8.0, 3.6, 0.7))):
        corners = hip_roof(pv, C.x, yb, C.z, half * 0.35, half * 0.35, half, half, 1.6, lift, hexc("#26303a"), ry=ry2)
        if k == 0:
            pv.box((C.x, yb + 0.55, C.z), (3.6, 1.2, 3.6), "paint", hexc("#5a4a3a"), ry=ry2)
        for q in corners:
            lantern(pl, (q[0], q[1] - 0.6, q[2]), 0.36, LANTERNS[k * 2], segs=8)
            reflection(refl, q[0], q[1] - 0.6, q[2], WL, 0.4, LANTERNS[k * 2], 1.2)
    pv.tube([(C.x, DECK + 8.0, C.z), (C.x, DECK + 10.0, C.z)], 0.1, "metal", hexc("#8a6a2a"), segs=5)
    reflection(refl, C.x, DECK + 2.5, C.z, WL, 2.4, hexc("#ffb060"), 1.4)
    for t, s in ((0.3, 1.1), (0.62, 1.3)):
        p = Q0 + d2 * (L2 * t) - s2 * 5.5
        boat(sc, "boat_%d" % bi, (p.x, 0, p.z), s, rng, hulls[bi % 5], WL, refl, flip=True)
        bi += 1
    # two small boats out on the water, each with a single lantern
    for (xx, zz) in ((sx(5.0, -48.0), -48.0), (sx(11.5, -64.0), -64.0)):
        b = sc.acc("boat_%d" % bi, (xx, WL, zz))
        b.lathe((xx, WL - 0.3, zz), [(0.0, 0), (0.5, 0.1), (0.7, 0.6)], 8, "paint", hexc("#2a2420"), sx=2.6)
        b.tube([(xx + 0.8, WL + 0.3, zz), (xx + 0.8, WL + 2.2, zz)], 0.05, "wood", DARK, segs=4)
        lantern(b, (xx + 0.8, WL + 1.9, zz), 0.28, LANTERNS[1], segs=6)
        reflection(refl, xx + 0.8, WL + 1.9, zz, WL, 0.3, LANTERNS[1], 1.3)
        bi += 1
    # paper lanterns floating on the water, mostly off to the sides
    fl = sc.acc("mid_floating")
    for i in range(16):
        z = rng.uniform(-9, -40)
        xs = rng.choice((rng.uniform(-5, 2.0), rng.uniform(14.5, 21), rng.uniform(2, 14.5)))
        x = sx(xs, z)
        col = rng.choice(LANTERNS)
        fl.box((x, WL + 0.05, z), (0.5, 0.12, 0.5), "wood", DARK)
        lantern(fl, (x, WL + 0.35, z), 0.2, col, segs=5, caps=False)
        reflection(refl, x, WL + 0.6, z, WL, 0.18, col, 0.5)

    # the far shore across the bay: dark hills, the waterfront town and its lights, a temple roof on the hill
    SZ = -150.0

    def hill(x, z):
        return WL + 0.8 + smooth(SZ + 2, SZ - 30, z) * (14 + 9 * fbm(x, z, 0.02, 3, 20)) * \
            (0.55 + 0.45 * smooth(0, 60, abs(x - 8)))
    land = sc.acc("far_hill")
    land.terrain(SZ + 4, -200, 16, 60, hill, lambda x, y, z, ny: mix(hexc("#121420"), hexc("#1a1c2c"),
                 n2(x, z, 0.08) * 0.5 + 0.5), material="ground", margin=1.4)
    town = sc.acc("far_town")
    tl = sc.acc("far_town_lights")
    x = -120.0
    bld = [hexc("#1e2030"), hexc("#24222e"), hexc("#20263a")]
    while x < 140:
        w = rng.uniform(4, 9)
        zf = SZ - rng.uniform(0, 6)
        yb = WL + 0.5
        hgt = rng.uniform(3, 8)
        c = rng.choice(bld)
        town.box((x + w / 2, yb + hgt / 2, zf - 3), (w - 0.4, hgt, 6), "paint", c)
        hip_roof(town, x + w / 2, yb + hgt + 1.2, zf - 3, w * 0.25, 0.3, w / 2 + 0.4, 3.4, 1.4, 0.4, hexc("#141820"))
        centre = abs(xs_of(x + w / 2, zf) - 8) < 5
        for j in range(int(w / 1.6)):
            if rng.random() < (0.35 if centre else 0.7):
                wx = x + 0.8 + j * 1.6
                tl.box((wx, yb + hgt * 0.45, zf + 0.02), (0.7, 0.8, 0.05), "window_glow", (1, 1, 1))
        x += w + rng.uniform(0.5, 3)
    for i in range(70):   # the lantern line along the waterfront, long reflections
        lx = -120 + i * 3.7
        if abs(xs_of(lx, SZ + 2) - 8) < 3.5 and i % 2:
            continue
        col = LANTERNS[i % 5]
        lantern(tl, (lx, WL + 2.6, SZ + 2), 0.35, col, segs=5, caps=False)
        reflection(refl, lx, WL + 2.6, SZ + 2, WL, 0.35, col, 1.6)
    # the temple roof on the far hill (left of centre)
    TX, TZ = sx(1.0, -175.0), -175.0
    ty = hill(TX, TZ)
    town.box((TX, ty + 3, TZ), (14, 6, 9), "paint", hexc("#24202a"))
    hip_roof(town, TX, ty + 9.5, TZ, 4.5, 0.4, 9.5, 6.5, 3.4, 1.2, hexc("#181c26"))
    hip_roof(town, TX, ty + 12.5, TZ, 2.0, 0.3, 5.0, 3.6, 2.2, 0.8, hexc("#181c26"))
    windows_on(tl, TX, ty + 3, TZ, 10, 2.4, 0.0, 5, 1, ww=1.4, wh=1.6, depth=4.5)
    far_lights(tl, 80, rng, (-140, 160), (SZ - 8, -195), hill, size=0.5)
    # far islands at the sides of the bay mouth
    isl = sc.acc("far_islands")
    for (xc, zc, r, hh) in ((sx(-3.0, -120.0), -120.0, 26.0, 9.0), (sx(19.5, -110.0), -110.0, 22.0, 7.0)):
        isl.blob((xc, WL - 1.0, zc), (r, hh, r * 0.6), "rock", lambda nx, ny, nz, q: mix(hexc("#0e1018"), hexc("#181a26"),
                 smooth(0.0, 0.9, ny)), segs=14, rings=5, rough=0.25, nscale=0.5, seed=xc, cut=0.0)
        far_lights(tl, 8, rng, (xc - r * 0.6, xc + r * 0.6), (zc + 2, zc - 2), lambda x, z: WL + 1.0, size=0.5)


# ------------------------------------------------------------------ 1 Pagoda Steps

def pagoda_steps(sc):
    rng = random.Random(201)
    stone, stone2 = hexc("#5a5658"), hexc("#6e6a68")
    # the terrace: worn stone slabs, a kerb at the back, stone lanterns beyond the ends
    fg = sc.acc("fg_terrace")
    z = 6.0
    row = 0
    while z > -2.6:
        dz = 0.9
        x = -18.0 - (0.5 if row % 2 else 0.0)
        while x < 34:
            L = rng.uniform(1.0, 1.6)
            c = mul(mix(stone, stone2, rng.random()), rng.uniform(0.85, 1.05))
            fg.box((x + L / 2, -0.08, z - dz / 2), (L - 0.05, 0.16, dz - 0.05), "rock", c, cols=(c, mul(c, 0.6)))
            x += L
        z -= dz
        row += 1
    fg.box((8, 0.05, -2.95), (64, 0.5, 0.6), "rock", hexc("#4a4648"))
    for i, x in enumerate((-2.6, 18.6)):
        stone_lantern(fg, (x, 0.0, -1.2), 1.35)
        sc.empty("light_warm_%d" % i, (x, 2.6, -0.6))

    # the hill: rising behind the arena, higher at the sides; vertex colours warm near the lantern-lit stairs
    def stair_x(xs0, z):
        return sx(xs0, z)
    STAIRS = [(-0.4, -14.0, -86.0), (16.4, -14.0, -82.0)]   # (arena x it holds, foot z, top z)

    def hill(x, z):
        xs = xs_of(x, z)
        side = smooth(3.0, 11.0, abs(xs - 8.0))
        hh = (0.3 + 16.0 * smooth(-12.0, -105.0, z) ** 1.2) * (0.5 + 0.62 * side)
        hh += 1.8 * fbm(x, z, 0.035, 3, 7) * smooth(-10.0, -30.0, z)
        return hh

    def warm(x, z):
        w = 0.0
        for xs0, z0, z1 in STAIRS:
            if z1 - 4 < z < z0 + 2:
                dx = abs(x - stair_x(xs0, z))
                w = max(w, math.exp(-dx * dx / 30.0))
        return w

    def hcol(x, y, z, ny):
        base = mix(hexc("#121a1e"), hexc("#1c2620"), n2(x, z, 0.12) * 0.5 + 0.5)
        base = mix(base, hexc("#24282c"), smooth(0.85, 0.6, ny) * 0.6)
        return mix(base, hexc("#5a3424"), warm(x, z) * 0.75)
    land = sc.acc("mid_hill")
    land.terrain(-2.9, -200.0, 56, 80, hill, hcol, material="ground", margin=1.4)

    # the stairs: stone flights up each side, a lantern on a post every few steps on both sides, lanterns strung
    # across, a gate at the foot of each
    st = sc.acc("lm_stairs")
    lan = sc.acc("lm_lanterns")
    for si, (xs0, z0, z1) in enumerate(STAIRS):
        z = z0
        prev = None
        k = 0
        while z > z1:
            x = stair_x(xs0, z)
            y = hill(x, z)
            nz_ = z - 0.9
            nx_ = stair_x(xs0, nz_)
            ny_ = hill(nx_, nz_)
            ry = math.atan2(nx_ - x, nz_ - z)
            top = max(y, ny_)
            st.box((x, top - 0.6, z - 0.45), (3.2, 1.2 + abs(ny_ - y), 0.95), "rock", mul(stone, 0.8),
                   cols=(mul(stone, 0.95), mul(stone, 0.6)), ry=ry)
            if k % 3 == 0:
                for s in (-1, 1):
                    px = x + s * 2.0 * math.cos(ry)
                    pz = z - s * 2.0 * math.sin(ry)
                    py = hill(px, pz)
                    st.tube([(px, py - 0.3, pz), (px, py + 1.5, pz)], 0.07, "wood", hexc("#2a1a16"), segs=4)
                    lantern(lan, (px, py + 1.25, pz), 0.24, LANTERNS[(k // 3 + si) % 5], segs=6, caps=False)
                if k % 9 == 0 and z < z0 - 3:   # a string across, overhead
                    a = (x - 2.0 * math.cos(ry), y + 3.6, z + 2.0 * math.sin(ry))
                    b = (x + 2.0 * math.cos(ry), y + 3.6, z - 2.0 * math.sin(ry))
                    lantern_string(lan, a, b, 0.5, 0.75, 0.2, rng, segs=5)
                    for s in (-1, 1):
                        px = x + s * 2.0 * math.cos(ry)
                        pz = z - s * 2.0 * math.sin(ry)
                        st.tube([(px, hill(px, pz) + 1.4, pz), (px, y + 3.7, pz)], 0.06, "wood", hexc("#2a1a16"),
                                segs=4)
            z = nz_
            k += 1
        # the gate at the foot: two red posts, two beams, a little roof, a lantern hanging in the middle
        gx = stair_x(xs0, z0 - 1.5)
        gz = z0 - 1.5
        gy = hill(gx, gz)
        red = hexc("#8a1e16")
        for s in (-1, 1):
            st.tube([(gx + s * 2.3, gy - 0.3, gz), (gx + s * 2.2, gy + 6.0, gz)], 0.24, "paint", red, segs=8)
        st.box((gx, gy + 5.0, gz), (6.0, 0.35, 0.4), "paint", red)
        st.box((gx, gy + 6.2, gz), (6.8, 0.4, 0.5), "paint", hexc("#1e1a1c"))
        hip_roof(st, gx, gy + 7.2, gz, 2.8, 0.1, 3.9, 0.9, 0.9, 0.45, hexc("#26303a"))
        lantern(lan, (gx, gy + 3.9, gz), 0.55, LANTERNS[0], segs=10)
        wire(lan, [Vector((gx, gy + 5.0, gz)), Vector((gx, gy + 4.4, gz))])
        sc.empty("light_warm_%d" % (2 + si), (gx, gy + 3.5, gz + 1.5))
    # the pagoda at the top of the right-hand stair, the temple hall at the top of the left
    pg = sc.acc("lm_pagoda")
    px, pz = stair_x(16.6, -84.0) + 3.0, -88.0
    pagoda(pg, lan, (px, hill(px, pz) - 0.5, pz), 1.05, rng)
    hall = sc.acc("lm_hall")
    hx, hz = stair_x(-0.6, -90.0) - 2.0, -92.0
    hy = hill(hx, hz) - 0.3
    hall.box((hx, hy + 0.7, hz), (26, 1.4, 16), "rock", mul(stone, 0.8))
    hall.box((hx, hy + 4.4, hz), (20, 6.0, 11), "paint", hexc("#4a3a32"))
    for i in range(7):
        hall.tube([(hx - 9 + i * 3, hy + 1.4, hz + 5.7), (hx - 9 + i * 3, hy + 7.4, hz + 5.7)], 0.25, "paint",
                  hexc("#6a1a14"), segs=6)
    windows_on(lan, hx, hy + 4.2, hz, 17, 3.4, 0.0, 6, 1, ww=2.0, wh=3.0, depth=5.5)
    for corners in (hip_roof(hall, hx, hy + 11.0, hz, 7.0, 0.5, 13.0, 8.0, 3.8, 1.4, hexc("#24303a")),
                    hip_roof(hall, hx, hy + 14.8, hz, 4.0, 0.3, 8.0, 4.6, 2.6, 1.0, hexc("#24303a"))):
        for q in corners:
            lantern(lan, (q[0], q[1] - 0.8, q[2]), 0.45, LANTERNS[0], segs=8)
    hall.box((hx, hy + 12.0, hz), (12, 1.6, 6), "paint", hexc("#3a2e28"))
    # the town: houses on the slopes, many lit, lanterns at their eaves; dark trees between; cherries in blossom
    town = sc.acc("mid_town")
    trees = sc.acc("mid_trees")
    blossom = sc.acc("mid_blossom")
    placed = []
    for i in range(52):
        for _ in range(20):
            z = rng.uniform(-18.0, -110.0)
            xs = rng.uniform(-6.0, 22.0)
            x = sx(xs, z)
            if warm(x, z) > 0.3 or (abs(xs - 8.0) < 6.0 and z > -45.0):
                continue
            if any((x - q[0]) ** 2 + (z - q[1]) ** 2 < 70 for q in placed):
                continue
            break
        else:
            continue
        placed.append((x, z))
        centre = abs(xs - 8.0) < 5.0 and z > -60
        w, d = rng.uniform(5, 8), rng.uniform(4, 6)
        y = hill(x, z) - 0.6
        wall = mul(mix(hexc("#3a302c"), hexc("#4a3a30"), rng.random()), 0.9)
        eastern_house(town, (x, y, z), w, d, rng.uniform(2.6, 3.4), rng.uniform(-0.25, 0.25), rng,
                      lit=0.15 if centre else 0.6, wall=wall, lanterns=None if centre else lan)
    for i in range(120):
        z = rng.uniform(-6.0, -120.0)
        xs = rng.uniform(-6.0, 22.0)
        x = sx(xs, z)
        if warm(x, z) > 0.5 or any((x - q[0]) ** 2 + (z - q[1]) ** 2 < 25 for q in placed):
            continue
        g = mul(hexc("#18261e"), rng.uniform(0.8, 1.2))
        if rng.random() < 0.5:
            pine(trees, (x, hill(x, z) - 0.3, z), rng.uniform(5, 9), rng, g)
        else:
            round_tree(trees, (x, hill(x, z) - 0.3, z), rng.uniform(4, 7), rng, g)
    for (xs, z, h) in ((-3.6, -5.0, 5.0), (19.6, -5.5, 5.2), (-2.0, -18.0, 5.5), (18.0, -20.0, 5.5), (1.0, -30.0, 6.0),
                       (15.0, -34.0, 6.0), (-4.0, -44.0, 7.0), (20.0, -46.0, 7.0)):
        x = sx(xs, z)
        cherry(blossom, (x, hill(x, z) - 0.2, z), h, rng)
    sc.empty("petal_0", (sx(-2.0, -6.0), 6.0, -6.0))
    sc.empty("petal_1", (sx(18.0, -6.0), 6.0, -6.0))
    for i, (xs, z) in enumerate(((-2.0, -40.0), (17.0, -35.0), (3.0, -70.0), (13.0, -75.0), (8.0, -95.0))):
        x = sx(xs, z)
        sc.empty("rise_%d" % i, (x, hill(x, z) + 1.0, z))
    # the far ridge behind the hill: layered dark mountains
    far = sc.acc("far_ridges")
    for k, (z, base, amp, c) in enumerate(((-150.0, 14.0, 16.0, "#0e1220"), (-185.0, 16.0, 24.0, "#0b0e1a"))):
        xs_ = [sx(-12, z) + i * (sx(28, z) - sx(-12, z)) / 80 for i in range(81)]
        far.ridge(xs_, z, -2.0, lambda x, z=z, base=base, amp=amp, k=k: base + amp * (0.5 + 0.5 * fbm(x, z, 0.015, 4, 30 + k)) *
                  (0.6 + 0.5 * smooth(0, 1, abs(xs_of(x, z) - 8) / 12)), lambda x, y, c=c: hexc(c), material="rock")


def stone_lantern(a, c, s=1.0, lit=True):
    x, y, z = c
    st = hexc("#5e5a56")
    a.lathe((x, y, z), [(0.45 * s, 0), (0.45 * s, 0.2 * s), (0.18 * s, 0.3 * s), (0.16 * s, 1.2 * s),
                        (0.35 * s, 1.3 * s), (0.35 * s, 1.4 * s)], 6, "rock", st, sm=False, phase=math.pi / 6)
    a.box((x, y + 1.72 * s, z), (0.5 * s, 0.64 * s, 0.5 * s), "rock", st)
    a.box((x, y + 1.72 * s, z), (0.54 * s, 0.34 * s, 0.3 * s), "lamp_glow" if lit else "rock", (1, 1, 1))
    a.box((x, y + 1.72 * s, z), (0.3 * s, 0.34 * s, 0.54 * s), "lamp_glow" if lit else "rock", (1, 1, 1))
    a.lathe((x, y + 2.04 * s, z), [(0.62 * s, 0), (0.55 * s, 0.12 * s), (0.12 * s, 0.45 * s), (0.0, 0.5 * s)], 6, "rock",
            mul(st, 0.9), sm=False, phase=math.pi / 6)


# ------------------------------------------------------------------ 2 Lighthouse Rocks

def lighthouse_rocks(sc):
    rng = random.Random(302)
    WL = -1.0
    refl = sc.acc("mid_reflections")
    sand, wet = hexc("#5a5048"), hexc("#3a3634")
    CLIFF_XS = 1.2   # the cliff edge holds this arena x

    def edge_x(z):
        return sx(CLIFF_XS, z) - 2.0 * smooth(-10, -60, z)

    def cliff_top(z):
        return 3.0 + 13.0 * smooth(-6.0, -55.0, z) - 4.0 * smooth(-70.0, -110.0, z)

    def beach(x, z):
        """The beach: flat under the arena, shelving into the sea, running on up the right-hand side."""
        xs = xs_of(x, z)
        shelf = (WL - 0.9) * smooth(-2.5, -11.0, z)
        right = smooth(13.0, 16.5, xs) * smooth(-90.0, -60.0, z)
        up = 0.25 * smooth(-3.0, -40.0, z) + 0.6 * fbm(x, z, 0.1, 2, 4) * smooth(-6.0, -20.0, z)
        return shelf + (up - shelf) * right

    def cliff(x, z):
        e = edge_x(z)
        k = smooth(e + 4.5, e - 1.5, x)
        top = cliff_top(z) + 1.6 * fbm(x, z, 0.08, 3, 9)
        face = 2.2 * fbm(x * 0.3, z, 0.35, 3, 2)
        return top * k + face * k * (1 - k) * 4 - 6.0 * (1 - k)

    def ground(x, z):
        return max(beach(x, z), cliff(x, z))

    fg = sc.acc("fg_beach")
    fg.terrain(6.0, -2.4, 6, 50, lambda x, z: 0.0, lambda x, y, z, ny: mix(sand, mul(sand, 1.2), n2(x, z, 1.5) * 0.5 +
               0.5), material="ground", margin=1.5)
    for i in range(30):
        xs = rng.choice((rng.uniform(-6, -0.5), rng.uniform(16.5, 22)))
        z = rng.uniform(-2.2, 1.5)
        x = sx(xs, z)
        r = rng.uniform(0.3, 0.9)
        rock(fg, (x, 0.0, z), (r * 1.3, r, r), rng, hexc("#4a4650"), hexc("#26242c"), segs=6, rings=3)

    def gcol(x, y, z, ny):
        c = mix(wet, sand, smooth(WL - 0.4, WL + 0.6, y))
        rk = smooth(0.75, 0.45, ny) + smooth(1.5, 3.0, y) * smooth(-8, -12, z)
        c = mix(c, mix(hexc("#2a2830"), hexc("#3a3640"), n2(x, z, 0.3) * 0.5 + 0.5), clamp01(rk))
        fire = math.exp(-((x - FX) ** 2 + (z - FZ) ** 2) / 90.0)
        return mix(c, hexc("#8a4a2a"), fire * 0.55)
    FX, FZ = sx(18.6, -16.0), -16.0
    land = sc.acc("mid_shore")
    land.terrain(-2.4, -200.0, 64, 90, ground, gcol, material="ground", margin=1.5)

    def shallow(x, z):
        return smooth(WL - 1.2, WL + 0.05, ground(x, z))
    sea(sc, WL, near_z=-2.4, far_z=-205.0, shallow_fn=shallow, rows=60, cols=70)
    # boulders along the cliff foot and in the surf
    rk = sc.acc("mid_rocks")
    for i in range(36):
        z = rng.uniform(-6, -80)
        x = edge_x(z) + rng.uniform(0.5, 6.0)
        r = rng.uniform(0.8, 2.6)
        rock(rk, (x, WL - 0.2, z), (r * 1.3, r, r * 1.1), rng, hexc("#3a3844"), hexc("#1a1a22"), segs=7, rings=4)
    # sea stacks out in the water
    for (xs, z, r, h) in ((4.0, -62.0, 3.0, 9.0), (6.0, -70.0, 1.8, 6.0), (12.5, -90.0, 3.5, 7.0)):
        x = sx(xs, z)
        rk.blob((x, WL - 1.0, z), (r, h, r * 0.9), "rock", lambda nx, ny, nz, q: mix(hexc("#14141c"), hexc("#262632"),
                smooth(-0.2, 0.9, ny + 0.3 * nx)), segs=9, rings=6, rough=0.3, nscale=0.8, seed=x, cut=0.0)
    # the lighthouse on the headland: a striped tower, the gallery, the lantern room, the keeper's cottage
    lh = sc.acc("lm_lighthouse")
    LZ = -46.0
    LX = edge_x(LZ) - 4.0
    ly = cliff(LX, LZ) - 0.5
    TH = 11.0
    lh.lathe((LX, ly, LZ), [(1.7, 0), (1.5, TH * 0.5), (1.25, TH)], 14, "paint",
             lambda x, y, z: hexc("#d8d4cc") if int((y - ly) / (TH / 5)) % 2 == 0 else hexc("#a8302a"), sm=True)
    lh.lathe((LX, ly + TH, LZ), [(1.9, 0), (1.9, 0.25)], 14, "metal", hexc("#202024"))
    lh.lathe((LX, ly + TH + 0.25, LZ), [(1.0, 0), (1.0, 1.6)], 10, "lens_glow", (1, 1, 1), cap=False)
    for k in range(8):
        an = k * math.pi / 4
        lh.tube([(LX + math.cos(an) * 1.02, ly + TH + 0.25, LZ + math.sin(an) * 1.02),
                 (LX + math.cos(an) * 1.02, ly + TH + 1.85, LZ + math.sin(an) * 1.02)], 0.05, "metal", DARK, segs=3)
    lh.lathe((LX, ly + TH + 1.85, LZ), [(1.3, 0), (0.2, 1.0), (0.0, 1.5)], 12, "metal", hexc("#3a1a18"))
    lh.box((LX + 4.5, ly + 1.4, LZ + 1.0), (5.0, 2.8, 3.6), "paint", hexc("#8a8480"))
    lh.prism([(LX + 1.8, LZ + 3.0), (LX + 7.2, LZ + 3.0), (LX + 7.2, LZ - 1.0), (LX + 1.8, LZ - 1.0)], ly + 2.8, ly + 2.9,
             "roof", hexc("#2a2428"))
    lh.poly([(LX + 1.8, ly + 2.8, LZ + 3.0), (LX + 7.2, ly + 2.8, LZ + 3.0), (LX + 7.2, ly + 4.2, LZ + 1.0),
             (LX + 1.8, ly + 4.2, LZ + 1.0)], "roof", hexc("#2a2428"))
    for k in range(2):
        lh.box((LX + 3.5 + k * 2.2, ly + 1.5, LZ + 2.82), (0.8, 0.9, 0.04), "window_glow", (1, 1, 1))
    sc.empty("light_cool_0", (LX, ly + TH + 1.0, LZ + 3.0))
    bm = sc.acc("beam", (LX, ly + TH + 1.05, LZ))
    for s in (-1, 1):
        tip = Vector((LX, ly + TH + 1.05, LZ))
        ring = []
        for k in range(10):
            an = 2 * math.pi * k / 10
            ring.append(tip + Vector((s * 60.0, math.sin(an) * 3.2 - 2.5, math.cos(an) * 3.2)))
        for k in range(10):
            bm.face([bm.vert(tip), bm.vert(ring[k]), bm.vert(ring[(k + 1) % 10])], "beam_glow", [(1, 1, 1)] * 3,
                    uvs=[(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)], sm=True)
    reflection(refl, LX, ly + TH + 1.0, LZ, WL, 0.3, hexc("#ffe8c0"), 0.7)
    # the festival on the beach: the bonfire, people round it, tents with lanterns, torches, boats drawn up
    fire = sc.acc("lm_bonfire")
    fy = beach(FX, FZ)
    for k in range(9):
        an = k * 2 * math.pi / 9
        fire.tube([(FX + math.cos(an) * 1.8, fy, FZ + math.sin(an) * 1.8), (FX + math.cos(an) * 0.2, fy + 2.6, FZ +
                   math.sin(an) * 0.2)], 0.2, "wood", hexc("#2a1a12"), segs=5)
    for k in range(12):
        an = k * 2 * math.pi / 12
        rock(fire, (FX + math.cos(an) * 2.4, fy, FZ + math.sin(an) * 2.4), (0.45, 0.35, 0.4), rng, hexc("#3a3030"),
             hexc("#1a1414"), segs=5, rings=3)
    fire.blob((FX, fy + 0.2, FZ), (1.6, 0.6, 1.6), "fire_glow", (1, 1, 1), segs=10, rings=4, rough=0.3, cut=0.0)
    flame(fire, (FX, fy + 0.2, FZ), 5.2, 3.0, n=3)
    flame(fire, (FX + 0.5, fy + 0.2, FZ + 0.3), 3.6, 2.2, n=2, rot=0.4)
    flame(fire, (FX - 0.6, fy + 0.2, FZ - 0.2), 3.0, 1.8, n=2, rot=1.1)
    sc.empty("light_fire_0", (FX, fy + 2.5, FZ + 1.0))
    sc.empty("spark_0", (FX, fy + 3.0, FZ))
    reflection(refl, FX, fy + 3.0, FZ, WL, 1.8, hexc("#ff8a3a"), 0.6)
    ppl = sc.acc("mid_people")
    for k in range(11):
        an = rng.uniform(0, 2 * math.pi)
        if math.sin(an) > 0.6 and abs(math.cos(an)) < 0.6:
            an += math.pi   # keep the near side of the fire open
        r = rng.uniform(4.0, 6.0)
        x, z = FX + math.cos(an) * r, FZ + math.sin(an) * r
        person(ppl, (x, beach(x, z), z), rng.uniform(1.6, 1.9), hexc("#16121a"), rng)
    tents = sc.acc("mid_tents")
    lan = sc.acc("mid_lanterns")
    tp = []
    for i, (xs, z) in enumerate(((16.0, -34.0), (18.8, -40.0), (21.5, -30.0), (14.2, -48.0))):
        x = sx(xs, z)
        y = beach(x, z)
        stripe = (hexc("#8a2a2a"), hexc("#c8b8a0")) if i % 2 == 0 else (hexc("#2a4a7a"), hexc("#c8b8a0"))
        tents.lathe((x, y, z), [(3.2, 0), (3.2, 2.2), (0.0, 5.0)], 12, "canvas",
                    lambda px, py, pz, x=x, z=z, st=stripe: st[int((math.atan2(pz - z, px - x) + math.pi) / (2 * math.pi)
                                                                   * 12) % 2], sm=False)
        tents.box((x, y + 1.0, z + 3.15), (1.4, 2.0, 0.05), "stall_glow", (1, 1, 1))
        tp.append((x, y + 5.0, z))
    for a_, b_ in ((tp[0], tp[1]), (tp[0], tp[2]), (tp[1], tp[3])):
        lantern_string(lan, a_, b_, 1.4, 1.0, 0.22, rng, segs=6)
    for k in range(7):   # torches along the beach path
        t = k / 6
        z = -6.0 - t * 34.0
        x = sx(14.6 + 2.0 * t, z)
        y = beach(x, z)
        lan.tube([(x, y, z), (x, y + 2.2, z)], 0.07, "wood", hexc("#2a1a12"), segs=4)
        flame(lan, (x, y + 2.15, z), 0.9, 0.45, n=2)
    for i, (xs, z) in enumerate(((19.0, -8.0), (21.0, -22.0))):
        x = sx(xs, z)
        b = sc.acc("mid_boat_%d" % i)
        b.lathe((x, beach(x, z) - 0.2, z), [(0.0, 0), (0.7, 0.12), (0.9, 0.8)], 10, "paint",
                hexc("#3a4a5a") if i else hexc("#5a2a22"), sx=3.0)
    # far headlands on the right horizon, a few cottage lights
    far = sc.acc("far_headland")
    for k, (z, base, amp, x0, x1, c) in enumerate(((-150.0, WL, 12.0, 11.0, 26.0, "#0e1018"),
                                                    (-185.0, WL, 18.0, 14.0, 30.0, "#0b0c14"))):
        xs_ = [sx(x0, z) + i * (sx(x1, z) - sx(x0, z)) / 50 for i in range(51)]
        far.ridge(xs_, z, WL - 1.0, lambda x, z=z, amp=amp, x0=x0, k=k: WL + amp * smooth(sx(x0, z), sx(x0 + 4, z), x) *
                  (0.6 + 0.4 * fbm(x, z, 0.03, 3, 40 + k)), lambda x, y, c=c: hexc(c), material="rock")
    fl = sc.acc("far_lights")
    far_lights(fl, 14, rng, (sx(13, -150), sx(22, -150)), (-149, -151), lambda x, z: WL + 2.0 + 3.0 * rng.random(),
               size=0.5)
    # the moon's path on the sea
    mp = sc.acc("mid_moonpath")
    for k in range(18):
        z0 = -40.0 - k * 9.0
        x = sx(14.5, z0)
        w = 0.25 + 0.08 * k + rng.uniform(0, 0.4)
        mp.poly([(x - w, WL + 0.05, z0), (x + w, WL + 0.05, z0), (x + w * 1.2, WL + 0.05, z0 + 8.0),
                 (x - w * 1.2, WL + 0.05, z0 + 8.0)], "reflect_glow", hexc("#a8b8e0"), uvs=UV4)


def clamp01(v):
    return max(0.0, min(1.0, v))


# ------------------------------------------------------------------ 3 Windmill Fair

def windmill(sc, i, c, s, rng):
    x, y, z = c
    a = sc.acc("lm_windmill_%d" % i)
    body = hexc("#2a2628")
    a.lathe((x, y, z), [(2.2 * s, 0), (1.9 * s, 4.0 * s), (1.5 * s, 8.0 * s)], 8, "paint", body, sm=False)
    a.lathe((x, y + 8.0 * s, z), [(1.75 * s, 0), (1.2 * s, 1.2 * s), (0.0, 2.2 * s)], 8, "roof", hexc("#1a1616"), sm=False)
    a.box((x, y + 4.6 * s, z + 1.85 * s), (0.6 * s, 0.8 * s, 0.05), "window_glow", (1, 1, 1))
    a.box((x, y + 1.1 * s, z + 2.1 * s), (0.9 * s, 1.6 * s, 0.05), "window_glow", (1, 1, 1))
    hub = (x, y + 8.6 * s, z + 2.0 * s)
    sl = sc.acc("sails_%d" % i, hub)
    wood = hexc("#3a3230")
    for k in range(4):
        an = k * math.pi / 2 + i * 0.4
        dx, dy = math.cos(an), math.sin(an)
        px, py = -dy, dx
        sl.tube([hub, (hub[0] + dx * 7.0 * s, hub[1] + dy * 7.0 * s, hub[2])], 0.1 * s, "wood", wood, segs=4)
        r0, r1, w = 1.3 * s, 6.8 * s, 1.1 * s
        q = [(hub[0] + dx * r0, hub[1] + dy * r0), (hub[0] + dx * r1, hub[1] + dy * r1),
             (hub[0] + dx * r1 + px * w, hub[1] + dy * r1 + py * w), (hub[0] + dx * r0 + px * w * 0.8, hub[1] + dy * r0 + py * w * 0.8)]
        sl.poly([(p[0], p[1], hub[2] + 0.05) for p in q], "canvas", hexc("#4a4440"))
        for t in range(1, 6):
            rr = r0 + (r1 - r0) * t / 6
            sl.tube([(hub[0] + dx * rr, hub[1] + dy * rr, hub[2] + 0.1),
                     (hub[0] + dx * rr + px * w, hub[1] + dy * rr + py * w, hub[2] + 0.1)], 0.04 * s, "wood", wood,
                    segs=3, sm=False)
    sl.lathe((hub[0], hub[1], hub[2] - 0.3), [(0.35 * s, 0), (0.35 * s, 0.5)], 8, "metal", DARK)


def windmill_fair(sc):
    rng = random.Random(403)
    earth, grass = hexc("#3a3028"), hexc("#16201a")
    # the midway: trodden earth and straw under the arena
    fg = sc.acc("fg_ground")
    fg.terrain(6.0, -2.4, 6, 50, lambda x, z: 0.0, lambda x, y, z, ny: mix(earth, hexc("#4a3c2c"), n2(x, z, 1.2) * 0.5 +
               0.5), material="ground", margin=1.5)
    for i in range(14):
        xs = rng.choice((rng.uniform(-6, -0.5), rng.uniform(16.5, 22)))
        z = rng.uniform(-2.0, 1.0)
        x = sx(xs, z)
        fg.box((x, 0.45, z), (1.2, 0.9, 0.9), "wood", hexc("#5a4632"), ry=rng.uniform(-0.4, 0.4))   # hay bales
    lights = []   # warm pools on the grass

    def field(x, z):
        h = 0.08 * fbm(x, z, 0.3, 2, 1) * smooth(-3.0, -8.0, z)
        h += smooth(-75.0, -125.0, z) * (7.0 + 5.0 * fbm(x, z, 0.02, 3, 5))
        return h

    def fcol(x, y, z, ny):
        c = mix(grass, hexc("#1e2a1e"), n2(x, z, 0.2) * 0.5 + 0.5)
        c = mix(c, earth, smooth(-2.4, -6.0, z) * smooth(-14.0, -6.0, z) * 0.6)
        w = 0.0
        for (lx, lz, r) in lights:
            w = max(w, math.exp(-((x - lx) ** 2 + (z - lz) ** 2) / (r * r)))
        return mix(c, hexc("#6a4a2a"), w * 0.6)
    WX, WZ, WR = sx(0.1, -48.0), -48.0, 12.5
    HY = WR + 2.8
    CX, CZ = sx(17.8, -22.0), -22.0
    lights += [(WX, WZ + 4, 14.0), (CX, CZ, 9.0), (sx(19.0, -60.0), -60.0, 12.0)]
    land = sc.acc("mid_field")
    land.terrain(-2.4, -200.0, 50, 80, field, fcol, material="ground", margin=1.5)

    # the wheel: rim and spokes outlined in bulbs, sixteen gondolas, an A-frame stand and a ticket booth
    lg = sc.acc("lm_wheel_stand")
    steel = hexc("#3a3a48")
    for s in (-1, 1):
        for q in (-1, 1):
            lg.tube([(WX + s * 6.0, 0.0, WZ + q * 2.2), (WX, HY, WZ + q * 1.1)], 0.3, "metal", steel, segs=5)
    lg.box((WX, 1.2, WZ + 3.5), (5.0, 2.4, 2.4), "paint", hexc("#5a1e22"))
    lg.box((WX, 1.3, WZ + 4.72), (3.6, 1.2, 0.05), "stall_glow", (1, 1, 1))
    wh = sc.acc("wheel", (WX, HY, WZ))
    rim = hexc("#c8c0d0")
    for q in (-0.75, 0.75):
        pts = [(WX + WR * math.cos(2 * math.pi * k / 48), HY + WR * math.sin(2 * math.pi * k / 48), WZ + q)
               for k in range(49)]
        wh.tube(pts, 0.14, "metal", rim, segs=4, sm=False)
        pts = [(WX + WR * 0.55 * math.cos(2 * math.pi * k / 32), HY + WR * 0.55 * math.sin(2 * math.pi * k / 32), WZ + q)
               for k in range(33)]
        wh.tube(pts, 0.08, "metal", rim, segs=3, sm=False)
    wh.tube([(WX, HY, WZ - 1.2), (WX, HY, WZ + 1.2)], 0.55, "metal", rim, segs=8, cap=True)
    for k in range(16):
        an = 2 * math.pi * k / 16
        e = (WX + WR * math.cos(an), HY + WR * math.sin(an))
        for q in (-0.75, 0.75):
            wh.tube([(WX, HY, WZ + q), (e[0], e[1], WZ + q)], 0.06, "metal", rim, segs=3, sm=False)
        for j in range(1, 9):   # bulbs along the front spokes
            t = j / 9
            wh.box((WX + (e[0] - WX) * t, HY + (e[1] - HY) * t, WZ + 0.9), (0.2, 0.2, 0.2), "bulb_glow", (1, 1, 1))
        gd = sc.acc("gondola_%d" % k, (e[0], e[1], WZ))
        gd.tube([(e[0], e[1], WZ), (e[0], e[1] - 0.5, WZ)], 0.05, "metal", rim, segs=3, sm=False)
        gc = [hexc("#c03a3a"), hexc("#d8a030"), hexc("#3a7ac0"), hexc("#3aa060")][k % 4]
        gd.box((e[0], e[1] - 1.15, WZ), (1.5, 1.3, 1.3), "paint", gc)
        gd.lathe((e[0], e[1] - 0.5, WZ), [(0.95, 0), (0.0, 0.35)], 6, "paint", mul(gc, 0.7))
        gd.box((e[0], e[1] - 1.05, WZ + 0.66), (1.1, 0.55, 0.04), "window_glow", (1, 1, 1))
    for k in range(72):
        an = 2 * math.pi * k / 72
        wh.box((WX + (WR + 0.25) * math.cos(an), HY + (WR + 0.25) * math.sin(an), WZ + 0.85), (0.24, 0.24, 0.24),
               "warmbulb_glow", (1, 1, 1))
    sc.empty("light_warm_0", (WX + 4.0, 4.0, WZ + 6.0))

    # the carousel: a striped canopy ringed with bulbs, horses on gilded poles, a mirrored centre; it turns
    car = sc.acc("carousel", (CX, 0.0, CZ))
    cb = sc.acc("lm_carousel_base")
    R = 5.2
    cb.lathe((CX, 0.0, CZ), [(R + 0.4, 0), (R + 0.4, 0.5), (0.0, 0.5)], 24, "wood", hexc("#3a2a24"))
    car.lathe((CX, 0.5, CZ), [(R, 0), (R, 0.12), (0.0, 0.12)], 24, "paint", hexc("#6a4a3a"))
    car.lathe((CX, 0.6, CZ), [(1.3, 0), (1.3, 4.6)], 10, "window_glow", (1, 1, 1), cap=False)
    stripe = (hexc("#a8262a"), hexc("#e0d0b0"))
    car.lathe((CX, 5.2, CZ), [(R + 0.5, 0), (R + 0.5, 0.7), (R * 0.5, 2.0), (0.0, 2.8)], 24, "canvas",
              lambda px, py, pz: stripe[int((math.atan2(pz - CZ, px - CX) + math.pi) / (2 * math.pi) * 24) % 2], sm=False)
    car.lathe((CX, 7.9, CZ), [(0.15, 0), (0.1, 1.2)], 6, "metal", hexc("#b08a3a"))
    for k in range(48):
        an = 2 * math.pi * k / 48
        car.box((CX + (R + 0.55) * math.cos(an), 5.3, CZ + (R + 0.55) * math.sin(an)), (0.2, 0.2, 0.2), "warmbulb_glow",
                (1, 1, 1))
    for k in range(12):
        an = 2 * math.pi * k / 12
        for j in range(1, 5):
            rr = (R + 0.5) * (1 - j / 5.0)
            car.box((CX + rr * math.cos(an), 5.9 + 2.0 * j / 5.0, CZ + rr * math.sin(an)), (0.17, 0.17, 0.17),
                    "bulb_glow", (1, 1, 1))
        px, pz = CX + (R - 0.9) * math.cos(an), CZ + (R - 0.9) * math.sin(an)
        car.tube([(px, 0.6, pz), (px, 5.2, pz)], 0.06, "metal", hexc("#c8a040"), segs=4)
        hy = 1.6 + 0.5 * math.sin(k * 1.7)
        hc = [hexc("#e8e0d0"), hexc("#3a2a24"), hexc("#c8a060")][k % 3]
        ty = an + math.pi / 2
        car.box((px, hy, pz), (0.5, 0.55, 1.4), "paint", hc, ry=ty)
        car.box((px + 0.6 * math.sin(ty), hy + 0.5, pz + 0.6 * math.cos(ty)), (0.3, 0.7, 0.35), "paint", hc, ry=ty)
    sc.empty("light_warm_1", (CX - 2.0, 3.0, CZ + 6.0))

    # stalls along the back of the midway: striped awnings over glowing counters
    stl = sc.acc("mid_stalls")
    ln = sc.acc("mid_lights")
    tops = []
    for i in range(9):
        xs = -3.5 + i * 3.0
        z = -34.0 - (i % 2) * 3.0
        x = sx(xs, z)
        w = rng.uniform(3.5, 4.5)
        cols = [(hexc("#8a2a2a"), hexc("#d8c8a8")), (hexc("#2a4a7a"), hexc("#d8c8a8")), (hexc("#2a6a3a"), hexc("#e0c080"))][i % 3]
        stl.box((x, 1.2, z), (w, 2.4, 2.6), "wood", hexc("#3a2c24"))
        stl.box((x, 1.3, z + 1.32), (w * 0.8, 0.9, 0.05), "stall_glow", (1, 1, 1))
        for k in range(6):
            x0 = x - w / 2 + k * w / 6
            stl.poly([(x0, 2.6, z + 1.3), (x0 + w / 6, 2.6, z + 1.3), (x0 + w / 6, 3.4, z - 0.2), (x0, 3.4, z - 0.2)],
                     "canvas", cols[k % 2])
        stl.tube([(x - w / 2, 0, z + 1.3), (x - w / 2, 4.2, z + 1.3)], 0.06, "wood", DARK, segs=3)
        tops.append((x - w / 2, 4.2, z + 1.3))
        lights.append((x, z + 2.0, 4.0))
    # the big top at the back right, the string lights
    bt = sc.acc("lm_bigtop")
    BX, BZ = sx(19.5, -64.0), -64.0
    stripe2 = (hexc("#8a1e22"), hexc("#d8ccb0"))
    bt.lathe((BX, 0.0, BZ), [(9.0, 0), (9.0, 4.0), (5.0, 7.5), (0.0, 12.0)], 20, "canvas",
             lambda px, py, pz: stripe2[int((math.atan2(pz - BZ, px - BX) + math.pi) / (2 * math.pi) * 20) % 2], sm=False)
    bt.tube([(BX, 11.5, BZ), (BX, 14.5, BZ)], 0.1, "metal", DARK, segs=4)
    bt.poly([(BX, 14.4, BZ), (BX + 1.6, 14.0, BZ), (BX, 13.6, BZ)], "paint", hexc("#c8a030"))
    bt.box((BX, 1.6, BZ + 9.0), (3.0, 3.2, 0.1), "stall_glow", (1, 1, 1))
    for k in range(6):
        an = -0.3 + k * 0.6 + math.pi
        g = (BX + 15.0 * math.cos(an), 0.0, BZ - 15.0 * math.sin(an) * 0.6)
        ln.tube([g, (g[0], 3.5, g[2])], 0.07, "wood", DARK, segs=3)
        bulb_string(ln, (BX, 12.0, BZ), (g[0], 3.5, g[2]), 0.8, 0.9, 0.18)
    # strings of coloured bulbs: over the near sides and between the stalls, the wheel and the carousel
    poles = [(sx(-3.0, -7.0), -7.0), (sx(-4.5, -16.0), -16.0), (sx(19.0, -7.0), -7.0), (sx(21.0, -14.0), -14.0)]
    pt = []
    for (x, z) in poles:
        fg.tube([(x, 0, z), (x, 6.0, z)], 0.08, "wood", DARK, segs=4)
        pt.append((x, 6.0, z))
    bulb_string(ln, pt[0], pt[1], 0.7, 0.55, 0.13)
    bulb_string(ln, pt[2], pt[3], 0.7, 0.55, 0.13)
    bulb_string(ln, pt[0], (WX + 6.0, 6.5, WZ + 2.0), 1.5, 0.8, 0.16)
    bulb_string(ln, pt[2], (CX, 7.6, CZ), 1.0, 0.6, 0.14)
    bulb_string(ln, pt[3], (BX - 6.0, 6.0, BZ + 6.0), 1.8, 0.9, 0.18)
    for a_, b_ in zip(tops[:-1], tops[1:]):
        bulb_string(ln, a_, b_, 0.5, 0.5, 0.14)
    # windmills on the ridge, trees along it
    for i, xs in enumerate((1.5, 6.5, 11.0, 15.5)):
        z = -112.0 - (i % 2) * 14.0
        x = sx(xs, z)
        windmill(sc, i, (x, field(x, z) - 0.4, z), 1.15, rng)
    tr = sc.acc("far_trees")
    for i in range(70):
        z = rng.uniform(-95, -150)
        x = sx(rng.uniform(-8, 24), z)
        round_tree(tr, (x, field(x, z) - 0.3, z), rng.uniform(4, 8), rng, hexc("#0e1612"))
    fl = sc.acc("far_lights")
    far_lights(fl, 30, rng, (-120, 140), (-130, -190), field, size=0.5)


# ------------------------------------------------------------------ 4 Comet Square

def facade_x(a, lit, x, z0, z1, h, face, rng, wall, lit_share=0.42, arcade=True):
    """A row of tall old houses along x = const (face +1 looks towards +x), from z0 to z1."""
    z = z0
    while z > z1:
        w = rng.uniform(5.0, 8.0)
        hh = h * rng.uniform(0.85, 1.15)
        zc = z - w / 2
        c = mul(wall, rng.uniform(0.8, 1.15))
        a.box((x - face * 4.0, hh / 2, zc), (8.0, hh, w - 0.1), "paint", c, cols=(mul(c, 0.8), c))
        a.box((x + face * 0.05, hh - 0.3, zc), (0.5, 0.6, w), "paint", mul(c, 1.2))       # cornice
        a.box((x + face * 0.05, 3.6, zc), (0.4, 0.3, w), "paint", mul(c, 1.2))             # string course
        a.prism([(x - face * 8.0, zc - w / 2 + 0.05), (x, zc - w / 2 + 0.05), (x, zc + w / 2 - 0.05),
                 (x - face * 8.0, zc + w / 2 - 0.05)], hh, hh + 0.05, "roof", hexc("#1c1e26"))
        a.poly([(x, hh, zc - w / 2 + 0.05), (x, hh, zc + w / 2 - 0.05), (x - face * 3.5, hh + 3.0, zc)], "roof",
               hexc("#22262e"))
        if rng.random() < 0.35:   # a turret dome
            a.lathe((x - face * 2.0, hh, zc), [(1.3, 0), (1.3, 1.2), (1.4, 1.6), (1.0, 2.6), (0.2, 3.6), (0.0, 4.2)], 10,
                    "roof", hexc("#2a3a40"))
        n = max(2, int(w / 1.8))
        for i in range(n):
            u = zc - w / 2 + (i + 0.5) * w / n
            for j in range(int((hh - 4.5) / 2.6)):
                yy = 5.4 + j * 2.6
                if rng.random() < lit_share:
                    lit.box((x + face * 0.06, yy, u), (0.05, 1.5, 0.8), "window_glow", (1, 1, 1))
                else:
                    a.box((x + face * 0.06, yy, u), (0.05, 1.5, 0.8), "paint", hexc("#0e1018"))
            if arcade and i % 2 == 0:
                lit.box((x + face * 0.06, 1.6, u), (0.05, 2.4, 1.2), "stall_glow", (1, 1, 1))
        z -= w


def comet_square(sc):
    rng = random.Random(504)
    pav, pav2 = hexc("#4a4448"), hexc("#5e565a")
    # the square: paved in fans of setts; flat at y = 0 all the way to the hall
    fg = sc.acc("fg_square")

    def pcol(x, y, z, ny):
        r = math.hypot(x - 8.0, z + 26.0)
        fan = 0.5 + 0.5 * math.sin(r * 2.6 + math.atan2(z + 26.0, x - 8.0) * 3.0)
        c = mix(pav, pav2, fan * 0.6 + 0.4 * (n2(x, z, 2.0) * 0.5 + 0.5))
        return c
    fg.terrain(6.0, -2.4, 10, 60, lambda x, z: 0.0, pcol, material="rock", margin=1.5)
    sq = sc.acc("mid_square")

    def scol(x, y, z, ny):
        c = pcol(x, y, z, ny)
        glow = 0.0
        for lx in (-9.0, 25.0):
            glow = max(glow, math.exp(-((x - lx) ** 2) / 30.0) * (0.6 + 0.4 * math.cos(z * 0.9)))
        glow = max(glow, math.exp(-((x - 8.0) ** 2 + (z + 26.0) ** 2) / 40.0))
        return mix(c, hexc("#7a5a3a"), glow * 0.5)
    sq.terrain(-2.4, -60.0, 40, 90, lambda x, z: 0.0, scol, material="rock", margin=1.5)
    # the side rows of old houses with lit arcades, and street lamps and bunting along them
    rows = sc.acc("lm_rows")
    lit = sc.acc("lm_rows_lights")
    facade_x(rows, lit, -14.0, -2.0, -50.0, 17.0, 1, rng, hexc("#4a4048"))
    facade_x(rows, lit, 30.0, -2.0, -50.0, 17.0, -1, rng, hexc("#48424e"))
    lamps = sc.acc("mid_lamps")
    for side, lx in ((-1, -9.0), (1, 25.0)):
        prev = None
        for k in range(7):
            z = -4.0 - k * 6.5
            lamp_post(lamps, (lx, 0.0, z), 4.2, r=0.28, arms=1)
            top = (lx, 4.6, z)
            if prev:
                bulb_string(lamps, prev, top, 0.6, 0.6, 0.12, "warmbulb_glow")
            prev = top
        sc.empty("light_warm_%d" % (0 if side < 0 else 1), (lx, 4.0, -6.0))
    for z in (-10.0, -24.0, -38.0):   # bunting between the rows, high up, only near the sides
        for s in (-1, 1):
            x0 = -14.0 if s < 0 else 30.0
            x1 = -6.0 if s < 0 else 22.0
            pts = catenary((x0, 12.0, z), (x1, 9.0, z - 4.0), 0.8, 10)
            wire(lamps, pts)
            for i, p in enumerate(pts[1:-1]):
                lamps.poly([(p.x - 0.3, p.y, p.z), (p.x + 0.3, p.y, p.z), (p.x, p.y - 0.7, p.z)], "canvas",
                           [hexc("#a82a2a"), hexc("#d8b040"), hexc("#2a5aa0"), hexc("#e0e0d8")][i % 4])
    # the fountain in the middle of the square
    fn = sc.acc("mid_fountain")
    FZ = -27.0
    fn.lathe((8.0, 0.0, FZ), [(4.6, 0), (4.6, 0.8), (4.2, 0.8), (4.2, 0.5), (0.0, 0.5)], 24, "rock", hexc("#5a5458"))
    fn.lathe((8.0, 0.55, FZ), [(4.2, 0), (0.0, 0.0)], 24, "water", (0.4, 0, 0), cap=False)
    fn.lathe((8.0, 0.5, FZ), [(0.8, 0), (0.6, 1.6), (2.0, 2.0), (2.0, 2.2), (0.4, 2.2), (0.35, 3.4), (1.0, 3.7),
                              (1.0, 3.85), (0.25, 3.85), (0.2, 4.6), (0.0, 4.8)], 16, "rock", hexc("#666064"))
    fn.blob((8.0, 5.0, FZ), (0.3, 0.3, 0.3), "lamp_glow", (1, 1, 1), segs=8, rings=4, rough=0.0)
    for k in range(6):
        an = k * math.pi / 3 + 0.3
        fn.box((8.0 + 4.4 * math.cos(an), 0.95, FZ + 4.4 * math.sin(an)), (0.25, 0.25, 0.25), "lamp_glow", (1, 1, 1))
    # the hall across the back: a long facade with a portico, a great ribbed dome on a drum, two smaller domes
    hall = sc.acc("lm_hall")
    hl = sc.acc("lm_hall_lights")
    HZ = -58.0
    stone = hexc("#3e3a42")
    hall.box((8.0, 8.0, HZ - 6.0), (46.0, 16.0, 12.0), "paint", stone, cols=(mul(stone, 0.8), stone))
    hall.box((8.0, 16.3, HZ), (47.0, 0.7, 0.8), "paint", mul(stone, 1.3))
    for i in range(14):
        x = -13.0 + i * 3.2
        if abs(x - 8.0) < 5.0:
            continue
        for j in range(3):
            if rng.random() < 0.45:
                hl.box((x, 3.5 + j * 4.2, HZ + 0.05), (1.1, 2.2, 0.05), "window_glow", (1, 1, 1))
            else:
                hall.box((x, 3.5 + j * 4.2, HZ + 0.05), (1.1, 2.2, 0.05), "paint", hexc("#0e0e16"))
    for i in range(6):   # the portico
        x = 8.0 - 5.0 + i * 2.0
        hall.lathe((x, 0.0, HZ + 2.6), [(0.55, 0), (0.45, 0.4), (0.45, 9.6), (0.6, 10.0)], 10, "paint", mul(stone, 1.35))
    hall.box((8.0, 10.4, HZ + 2.6), (12.0, 0.9, 1.6), "paint", mul(stone, 1.3))
    hall.poly([(1.8, 10.85, HZ + 3.4), (14.2, 10.85, HZ + 3.4), (8.0, 13.2, HZ + 3.4)], "paint", mul(stone, 1.2))
    hl.box((8.0, 3.2, HZ + 0.06), (2.6, 6.0, 0.05), "stall_glow", (1, 1, 1))
    for i in range(6):
        hl.box((8.0 - 5.0 + i * 2.0, 0.25, HZ + 3.4), (0.35, 0.3, 0.35), "lamp_glow", (1, 1, 1))
    DX, DZ = 8.0, HZ - 8.0
    hall.lathe((DX, 16.0, DZ), [(7.0, 0), (7.0, 4.5), (7.4, 4.8), (7.4, 5.2)], 20, "paint", mul(stone, 1.1))
    for k in range(10):
        an = k * 2 * math.pi / 10 + 0.15
        if math.sin(an) > -0.2:
            hl.box((DX + 7.05 * math.cos(an), 18.2, DZ + 7.05 * math.sin(an)), (0.8, 2.0, 0.8), "window_glow", (1, 1, 1),
                   ry=-an)
    dome_c = hexc("#2a3a44")
    hall.lathe((DX, 21.2, DZ), [(7.2, 0), (6.9, 2.4), (6.0, 4.6), (4.4, 6.6), (2.4, 7.9), (0.9, 8.4), (0.0, 8.5)], 24, "roof",
               lambda x, y, z: dome_c if int((math.atan2(z - DZ, x - DX) + math.pi) / (2 * math.pi) * 24) % 3 else
               mul(dome_c, 1.5), sm=True)
    hall.lathe((DX, 29.6, DZ), [(0.9, 0), (0.9, 1.6), (1.1, 1.7), (0.0, 2.6)], 10, "paint", mul(stone, 1.2))
    hl.lathe((DX, 30.0, DZ), [(0.75, 0), (0.75, 1.1)], 8, "lamp_glow", (1, 1, 1), cap=False)
    hall.tube([(DX, 32.2, DZ), (DX, 34.0, DZ)], 0.1, "metal", hexc("#b08a3a"), segs=4)
    for sxx in (-1, 1):
        x = 8.0 + sxx * 16.0
        hall.lathe((x, 16.0, HZ - 5.0), [(3.0, 0), (3.0, 2.2), (3.4, 3.2), (2.8, 5.0), (1.4, 6.6), (0.2, 7.8), (0.0, 8.6)],
                   14, "roof", hexc("#2a3e46"))
        hl.box((x, 17.0, HZ - 1.95), (0.8, 1.2, 0.05), "window_glow", (1, 1, 1))
    # the clock towers at the back corners: belfries, lit clock faces, spires
    tw = sc.acc("lm_towers")
    tl = sc.acc("lm_towers_lights")
    for i, (xs, z) in enumerate(((-0.2, -50.0), (16.2, -50.0))):
        x = sx(xs, z)
        tw.box((x, 9.5, z), (5.2, 19.0, 5.2), "paint", hexc("#3a343e"), cols=(hexc("#2a2630"), hexc("#3a343e")))
        tw.box((x, 19.2, z), (5.8, 0.5, 5.8), "paint", hexc("#4a4450"))
        tw.box((x, 21.5, z), (4.6, 4.0, 4.6), "paint", hexc("#34303a"))
        for k in range(4):   # belfry openings, dimly lit
            an = k * math.pi / 2
            tl.box((x + math.sin(an) * 2.32, 21.6, z + math.cos(an) * 2.32), (1.6, 2.4, 0.05), "stall_glow", (1, 1, 1),
                   ry=an)
        tw.box((x, 23.7, z), (5.2, 0.4, 5.2), "paint", hexc("#4a4450"))
        tw.lathe((x, 23.9, z), [(3.0, 0), (0.0, 7.5)], 4, "roof", hexc("#26343a"), sm=False, phase=math.pi / 4)
        tw.tube([(x, 31.2, z), (x, 33.0, z)], 0.08, "metal", hexc("#b08a3a"), segs=4)
        cy = 16.0
        face = [(x + 1.7 * math.cos(k * math.pi / 10), cy + 1.7 * math.sin(k * math.pi / 10), z + 2.63) for k in range(20)]
        tl.poly(face, "clock_glow", (1, 1, 1))
        ring = [(x + 1.95 * math.cos(k * math.pi / 10), cy + 1.95 * math.sin(k * math.pi / 10), z + 2.62) for k in range(21)]
        tw.tube(ring, 0.12, "metal", hexc("#8a6a2a"), segs=4, sm=False)
        for (L, an, w) in ((1.0, 1.9 + i * 0.7, 0.12), (1.45, 0.5 - i * 1.3, 0.08)):   # the hands
            ex, ey = x + L * math.cos(an), cy + L * math.sin(an)
            tw.poly([(x - w * math.sin(an), cy + w * math.cos(an), z + 2.68), (x + w * math.sin(an), cy - w * math.cos(an), z + 2.68),
                     (ex, ey, z + 2.68)], "metal", hexc("#141218"))
    # the city beyond: rooftops, domes and spires, a few windows
    far = sc.acc("far_city")
    fl = sc.acc("far_lights")
    for k in range(80):
        z = rng.uniform(-75.0, -180.0)
        xs = rng.uniform(-10.0, 26.0)
        x = sx(xs, z)
        w = rng.uniform(6, 14)
        h = rng.uniform(8, 18) * (0.7 if abs(xs - 8) < 6 else 1.0)
        c = mul(hexc("#14141e"), rng.uniform(0.8, 1.2))
        far.box((x, h / 2, z), (w, h, rng.uniform(6, 10)), "paint", c)
        r = rng.random()
        if r < 0.15:
            far.lathe((x, h, z), [(w * 0.25, 0), (w * 0.25, 1.0), (w * 0.2, 2.5), (0.0, w * 0.35 + 2.0)], 10, "roof",
                      hexc("#141c22"))
        elif r < 0.27:
            far.lathe((x, h, z), [(1.2, 0), (0.0, rng.uniform(6, 12))], 4, "roof", hexc("#12161e"), sm=False)
            fl.box((x, h + 0.5, z + 1.25), (0.5, 0.5, 0.5), "beacon_glow", (1, 1, 1))
        for i in range(int(w / 2)):
            if rng.random() < 0.3:
                s = max(0.5, 0.0015 * dist((x, h, z)))
                fl.box((x - w / 2 + 1 + i * 2, rng.uniform(2, h - 1), z + 5.0), (s, s * 1.3, 0.05), "window_glow",
                       (1, 1, 1))


# ------------------------------------------------------------------ main

THEMES = [lantern_harbour, pagoda_steps, lighthouse_rocks, windmill_fair, comet_square]


def main():
    for n, fn in enumerate(THEMES):
        if ONLY and n not in ONLY:
            continue
        sc = Scene(n)
        fn(sc)
        sc.export()


main()
