"""Nova Wardens (game 25) night backdrop: the last line of defence on a coastal hilltop, looking out over a sleeping
seaside town, its harbour and a calm sea. Original design: an invented, generic town (no real skyline, no real
landmark): terraced streets of houses (pitched and hipped roofs, chimneys, balconies, shopfronts with awnings and neon
signs, rooftop water tanks), a church with a spire and a town hall with a clock tower at the sides, a harbour
promenade, a pleasure pier with a lit wheel and a carousel, moored boats and a ferry, a striped lighthouse on the left
headland, a radar station and a military post on the crest (sandbags, crates, drums, a radio mast, a flag, searchlight
crews), pine woods on layered ridges, winding roads. Deterministic (fixed seeds); output CC BY-SA 4.0; provenance:
this script only, no third-party assets, no textures (vertex colours).
Run: blender -b --factory-startup -P tools/blender/novawardens_city.py -- godot/games/novawardens/art/backdrop

Coordinates: authored in Godot space (x right, y up, z towards the camera), converted on export.
The play field is x 0..11.2, y 0..12.8 on z = 0 (224 x 256 px at 0.05); the game's camera sits near (5.6, 5.2, 18.2),
fov 36, looking at (5.6, 6.4, 0). The crest the cannon stands on tops out at y = 0.95 for z -2..+3 (the game draws its
ground line at ~1.1). Behind it the hill falls to a terrace (the town), then the harbour at sea level y = -12; the sea
(drawn by the game as a disc round the camera, see nova_backdrop.gd) ends at about 200 units, so the horizon lies near
y = 3.9 on the play plane. Nothing tall stands behind the middle of the field (py_limit): the lighthouse, the radar,
the spire, the clock tower, the wheel and the lit hills are at the sides.

night_coast.glb holds
  fg_*          the crest, its sandbags and the military post (front, casts shadows)
  land          the terrain from the crest down to the shore and the headlands
  far_*         distant ridges (with pine silhouettes) and the far shore past the bay
  wood_*        pine woods
  city_*        houses (vertex colours), roofs, windows, lamps, signs, landmarks, roads
  harbour_*     quays, promenade, piers, cranes, containers, the breakwater, the fair, foam, reflections
  lh_*          the lighthouse and the keeper's cottage
  radar_*       the radar station (pylon, radome, hut)
and animated nodes, each with its origin at its pivot:
  beam              an empty at the lighthouse lantern (the game hangs the rotating beams there)
  dish_<i>          radar dishes (rotate about local Y)
  searchlight_<i>   empties at the searchlight lenses (the game adds the beams and aims them)
  boat_<i>          moored boats (bob)
  ferry_0           the night ferry (the game moves it across the bay along +x)
  wheel_0           the pier's big wheel (turns about local Z)
  carousel_0        the carousel (turns about local Y)
Material names carry the game's hints: "*glow*" emissive (window_glow, coolwindow_glow, shop_glow = lit shopfronts
(vertex colour), lamp_glow, blink_glow,
alarm_glow = the red air-raid lamps, lens_glow, lantern_glow, harbour_glow = coloured lights (vertex colour),
neon_glow = signs (vertex colour), bulb_glow = the fair's bulbs (vertex colour; UV.x runs round the wheel, UV.y out
along a spoke), clock_glow, stained_glow (vertex colour), pool_glow = pools of lamplight on the ground (UV 0..1 across),
reflect_glow = light streaks lying on the water (UV.y from the light (0) away (1)), foam_glow (UV.x along the shore in
units, UV.y from the shore (0) out to sea (1))), "flag" (cloth that waves; UV.x from the pole (0) to the fly (1)),
"glass" (dark windows), "sea". All other colour is in the vertex colours (COLOR_0, linear) over white materials.
night_coast_paths.tres (next to the glb) holds the roads as polylines at headlight height (metadata "roads", an Array
of PackedVector3Array), for the game's moving car lights.
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/novawardens/art/backdrop")

CAM = Vector((5.6, 5.2, 18.2))   # the game's camera (it sways a little round this)
TAN_W = 0.578   # half-width per unit of distance for fov 36 at 16:9
SL = -12.0      # sea level
CREST = 0.95
PATHS = {"roads": []}


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


def half_w(z, margin=1.4):
    return TAN_W * (CAM.z - z) * margin + 8.0


def plane_factor(z):
    """How much a length at depth z shrinks when projected on the play plane z = 0."""
    return CAM.z / (CAM.z - z)


def plane_xy(x, y, z):
    """Where a point lands on the play plane (as seen from the camera)."""
    k = plane_factor(z)
    return CAM.x + (x - CAM.x) * k, CAM.y + (y - CAM.y) * k


def uv(u, v):
    """A UV as the game reads it (the glTF exporter flips V)."""
    return (u, 1.0 - v)


# ------------------------------------------------------------------ materials

MATS = {}
MAT_DEFS = {
    # name: (base colour, roughness, metallic, emission strength)
    "ground": ((1, 1, 1), 0.95, 0, 0),
    "foliage": ((1, 1, 1), 0.9, 0, 0),
    "rock": ((1, 1, 1), 0.85, 0, 0),
    "paint": ((1, 1, 1), 0.6, 0, 0),
    "road": ((1, 1, 1), 0.55, 0, 0),
    "glass": ((1, 1, 1), 0.12, 0.4, 0),
    "metal": ((1, 1, 1), 0.4, 0.6, 0),
    "fabric": ((1, 1, 1), 0.95, 0, 0),
    "flag": ((1, 1, 1), 0.9, 0, 0),
    "sea": ((1, 1, 1), 0.1, 0, 0),
    "window_glow": ((1.0, 0.72, 0.38), 0.4, 0, 2.5),
    "coolwindow_glow": ((0.7, 0.85, 1.0), 0.4, 0, 2.0),
    "shop_glow": ((1.0, 0.8, 0.5), 0.4, 0, 2.5),
    "lamp_glow": ((1.0, 0.66, 0.3), 0.4, 0, 3.0),
    "blink_glow": ((1.0, 0.12, 0.08), 0.4, 0, 5.0),
    "alarm_glow": ((1.0, 0.08, 0.05), 0.4, 0, 5.0),
    "lens_glow": ((0.85, 0.92, 1.0), 0.4, 0, 5.0),
    "lantern_glow": ((1.0, 0.9, 0.7), 0.4, 0, 5.0),
    "harbour_glow": ((1.0, 1.0, 1.0), 0.4, 0, 4.0),
    "neon_glow": ((1.0, 1.0, 1.0), 0.4, 0, 4.0),
    "bulb_glow": ((1.0, 1.0, 1.0), 0.4, 0, 4.0),
    "clock_glow": ((1.0, 0.92, 0.75), 0.4, 0, 3.0),
    "stained_glow": ((1.0, 1.0, 1.0), 0.4, 0, 2.0),
    "pool_glow": ((1.0, 0.7, 0.35), 1, 0, 1.0),
    "reflect_glow": ((1.0, 0.7, 0.35), 1, 0, 1.2),
    "foam_glow": ((0.8, 0.9, 1.0), 1, 0, 1.0),
}


def mat(name):
    if name in MATS:
        return MATS[name]
    col, rough, metal, emit = MAT_DEFS[name]
    m = bpy.data.materials.new(name)
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

    def vert(self, p):
        self.v.append(Vector(p))
        return len(self.v) - 1

    def face(self, ids, material, col, uvs=None, sm=False, out=None):
        ids = list(ids)
        cols = list(col) if isinstance(col, list) else [col] * len(ids)
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

    def box(self, c, size, material, col, ry=0.0, taper=1.0, cols=None, bottom=True, uvc=None):
        """An axis box (turned by ry about Y); taper shrinks the top; cols: (top, sides) colours; uvc: one UV for
        every corner."""
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
        U = [uvc] * 4 if uvc else None
        self.face([pts[4], pts[5], pts[6], pts[7]], material, top, uvs=U, out=C)
        if bottom:
            self.face([pts[0], pts[1], pts[2], pts[3]], material, side, uvs=U, out=C)
        for i in range(4):
            j = (i + 1) % 4
            sc = side if not callable(side) else side(i)
            self.face([pts[i], pts[j], pts[4 + j], pts[4 + i]], material, sc, uvs=U, out=C)

    def lathe(self, c, prof, segs, material, col, sm=True, cap=True, a0=0.0):
        """Revolves prof [(r, y)] (bottom to top) about a vertical axis at c. col: colour or fn(y) -> colour."""
        cx, cy, cz = c
        cf = col if callable(col) else (lambda y: col)
        rings = []
        for r, y in prof:
            rings.append([self.vert((cx + math.cos(a0 + 2 * math.pi * j / segs) * r, cy + y,
                                     cz + math.sin(a0 + 2 * math.pi * j / segs) * r)) for j in range(segs)])
        for i in range(len(rings) - 1):
            ym = cy + (prof[i][1] + prof[i + 1][1]) / 2
            for j in range(segs):
                k = (j + 1) % segs
                ids = [rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]]
                self.face(ids, material, [cf(self.v[q].y - cy) for q in ids], sm=sm, out=(cx, ym, cz))
        if cap and prof[-1][0] > 1e-4:
            t = self.vert((cx, cy + prof[-1][1], cz))
            for j in range(segs):
                ids = [rings[-1][j], rings[-1][(j + 1) % segs], t]
                self.face(ids, material, cf(prof[-1][1]), sm=sm, out=(cx, cy - 1e3, cz))

    def tube(self, a, b, r, material, col, segs=5, uvc=None):
        a, b = Vector(a), Vector(b)
        t = (b - a).normalized()
        ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
        n = t.cross(ref).normalized()
        bn = t.cross(n)
        ra, rb = [], []
        for j in range(segs):
            ang = 2 * math.pi * j / segs
            d = n * math.cos(ang) + bn * math.sin(ang)
            ra.append(self.vert(a + d * r))
            rb.append(self.vert(b + d * r))
        m = (a + b) / 2
        U = [uvc] * 4 if uvc else None
        for j in range(segs):
            k = (j + 1) % segs
            self.face([ra[j], ra[k], rb[k], rb[j]], material, col, uvs=U, out=m)

    def blob(self, c, r, material, col, segs=10, rings=6, cut=-1.0, sm=True):
        cx, cy, cz = c
        rx, ry, rz = r
        grid = []
        for i in range(rings + 1):
            t = i / rings
            lat = math.asin(cut) + (math.pi / 2 - math.asin(cut)) * t
            row = []
            for j in range(segs if i < rings else 1):
                lon = 2 * math.pi * j / segs
                row.append(self.vert((cx + math.cos(lat) * math.cos(lon) * rx, cy + math.sin(lat) * ry,
                                      cz + math.cos(lat) * math.sin(lon) * rz)))
            grid.append(row)
        C = (cx, cy + ry * cut * 0.5, cz)
        cf = col if callable(col) else (lambda y: col)
        for i in range(rings):
            for j in range(segs):
                k = (j + 1) % segs
                ids = ([grid[i][j], grid[i][k], grid[i + 1][0]] if i + 1 == rings else
                       [grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]])
                self.face(ids, material, [cf((self.v[q].y - cy) / ry) for q in ids], sm=sm, out=C)

    def gem(self, c, s, material, col, u=(0.5, 0.5)):
        """A small octahedron (a bulb or a far lamp) with one UV for all its corners."""
        x, y, z = c
        P = [self.vert(p) for p in ((x + s, y, z), (x - s, y, z), (x, y + s, z), (x, y - s, z), (x, y, z + s),
                                     (x, y, z - s))]
        for a, b in ((0, 4), (4, 1), (1, 5), (5, 0)):
            for t in (2, 3):
                self.face([P[a], P[b], P[t]], material, col, uvs=[uv(*u)] * 3, out=c)

    def quad_facing(self, c, w, h, material, col=(1, 1, 1), axis="z", sign=1):
        """A small upright rectangle facing +z (axis z) or +-x (axis x)."""
        x, y, z = c
        if axis == "z":
            pts = [(x - w / 2, y - h / 2, z), (x + w / 2, y - h / 2, z), (x + w / 2, y + h / 2, z),
                   (x - w / 2, y + h / 2, z)]
            out = (x, y, z - 1)
        else:
            pts = [(x, y - h / 2, z - w / 2), (x, y - h / 2, z + w / 2), (x, y + h / 2, z + w / 2),
                   (x, y + h / 2, z - w / 2)]
            out = (x - sign, y, z)
        self.poly(pts, material, col, out=out)

    def flat(self, c, w, d, material, col=(1, 1, 1), ry=0.0, uvq=True):
        """A horizontal quad (UV 0..1 across when uvq), facing up."""
        x, y, z = c
        cr, sr = math.cos(ry), math.sin(ry)
        pts = []
        for xx, zz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            lx, lz = xx * w / 2, zz * d / 2
            pts.append((x + lx * cr + lz * sr, y, z - lx * sr + lz * cr))
        U = [uv(0, 0), uv(1, 0), uv(1, 1), uv(0, 1)] if uvq else None
        self.poly(pts, material, col, uvs=U, out=(x, y - 5, z))

    def streak(self, x, z, w, length, material="reflect_glow", col=(1, 1, 1), y=SL + 0.03):
        """A light's reflection on the water: from (x, z) towards the camera, widening; UV.y from the light."""
        d = Vector((CAM.x - x, CAM.z - z)).normalized()
        s = Vector((d.y, -d.x))
        a0 = Vector((x, z)) + s * w * 0.35
        a1 = Vector((x, z)) - s * w * 0.35
        e = Vector((x, z)) + d * length
        b0, b1 = e + s * w, e - s * w
        self.poly([(a0.x, y, a0.y), (a1.x, y, a1.y), (b1.x, y, b1.y), (b0.x, y, b0.y)], material, col,
                  uvs=[uv(0, 0), uv(1, 0), uv(1, 1), uv(0, 1)], out=(x, y - 5, z))

    def build(self):
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        o = self.o
        me.from_pydata([(p.x - o.x, -(p.z - o.z), p.y - o.y) for p in self.v], [], [f[0] for f in self.f])
        names = []
        for f in self.f:
            if f[1] not in names:
                names.append(f[1])
        for n in names:
            me.materials.append(mat(n))
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        uvl = me.uv_layers.new(name="UVMap") if any(f[3] for f in self.f) else None
        for poly, f in zip(me.polygons, self.f):
            poly.material_index = names.index(f[1])
            poly.use_smooth = f[4]
            for k in range(poly.loop_total):
                ca.data[poly.loop_start + k].color = (*lin(f[2][k]), 1.0)
                if f[3] and uvl:
                    uvl.data[poly.loop_start + k].uv = f[3][k]
        me.color_attributes.active_color = ca
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (o.x, -o.z, o.y)
        return ob


class Scene:
    def __init__(self):
        self.accs = []
        self.named = {}
        self.empties = []

    def acc(self, name, origin=(0, 0, 0)):
        if name in self.named:
            return self.named[name]
        a = Acc(name, origin)
        self.accs.append(a)
        self.named[name] = a
        return a

    def empty(self, name, p):
        self.empties.append((name, p))

    def export(self, fname):
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        objs, total = [], 0
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
        path = os.path.join(OUT, fname)
        bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB", export_yup=True,
                                  export_apply=True, export_animations=False, export_vertex_color="ACTIVE",
                                  export_extras=False)
        print("exported %s  %6d tris  %d nodes" % (fname, total, len(objs)))
        for a in sorted(self.accs, key=lambda a: -a.tris())[:16]:
            print("    %-20s %6d" % (a.name, a.tris()))
        return total


def write_paths(fname):
    """The roads as polylines for the game's car lights (a text resource, so the export keeps it)."""
    arrs = []
    for p in PATHS["roads"]:
        arrs.append("PackedVector3Array(%s)" % ", ".join("%.2f, %.2f, %.2f" % tuple(q) for q in p))
    txt = ('[gd_resource type="Resource" format=3]\n\n[resource]\nmetadata/roads = [%s]\n' % ", ".join(arrs))
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(txt)
    print("wrote %s  %d roads" % (fname, len(arrs)))


# ------------------------------------------------------------------ the land

def shore_z(x):
    """Where the land meets the sea along x (the bay in the middle, headlands either side)."""
    return -92.0 - 70.0 * smooth(-16.0, -40.0, x) - 30.0 * smooth(44.0, 70.0, x)


# gaussian hills: (x, z, radius, height)
HILLS = [
    (-11.0, -19.0, 9.0, 7.5),    # the radar hill (left)
    (-24.0, -26.0, 12.0, 5.0),
    (21.5, -9.0, 5.0, 2.6),      # the searchlight knoll (right)
    (-44.0, -70.0, 16.0, 5.0),   # the lighthouse headland's back
    (-35.0, -40.0, 14.0, 4.0),
    (62.0, -120.0, 22.0, 16.0),  # the far side of the bay
    (90.0, -150.0, 30.0, 22.0),
    (40.0, -30.0, 14.0, 6.0),    # the right-hand slope
]


def profile(u):
    """The hill's fall from the crest (u = 0) to the shore (u = 1) and under the sea."""
    pts = [(0.0, CREST), (0.022, CREST), (0.07, -2.5), (0.2, -6.6), (0.55, -8.4), (0.88, -10.4), (1.0, -12.6),
           (1.2, -20.0)]
    if u <= 0:
        return CREST
    for (u0, y0), (u1, y1) in zip(pts, pts[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            t = t * t * (3 - 2 * t)
            return y0 + (y1 - y0) * t
    return pts[-1][1]


def land_h(x, z):
    u = z / shore_z(x)
    y = profile(u)
    if z > 3.0:
        y = CREST - (z - 3.0) * 0.25
    for hx, hz, r, hh in HILLS:
        d2 = ((x - hx) ** 2 + (z - hz) ** 2) / (r * r)
        y += hh * math.exp(-d2)
    # the crest stays level under the play field; everything else is broken up a little
    calm = smooth(-4.0, -1.0, z) * (1.0 - smooth(-3.0, -7.0, x)) * (1.0 - smooth(14.5, 18.5, x))
    y += (1.0 - calm) * (0.8 * fbm(x, z, 0.08, 3, 2.0) + 0.25 * n2(x, z, 0.6, 5.0))
    return y


def slope(x, z, e=0.6):
    gx = (land_h(x + e, z) - land_h(x - e, z)) / (2 * e)
    gz = (land_h(x, z + e) - land_h(x, z - e)) / (2 * e)
    return gx, gz


def terraced(x, z, tol=2.5):
    """True where the ground is the town's gentle terrace (not a hill)."""
    return abs(land_h(x, z) - profile(z / shore_z(x))) < tol


GRASS = hexc("#1d2a2c")
GRASS_LIT = hexc("#3a4c50")
EARTH = hexc("#27262e")
ROCK = hexc("#3a3a46")


def land_col(x, y, z, ny):
    c = mix(GRASS, GRASS_LIT, 0.5 + 0.5 * n2(x, z, 0.15, 1.0))
    c = mix(ROCK, c, smooth(0.55, 0.85, ny))
    # a pale beach line and wet dark rock at the waterline
    c = mix(hexc("#4a4a50"), c, smooth(SL + 0.3, SL + 1.4, y))
    c = mix(mul(hexc("#2a2e3a"), 0.9), c, smooth(SL - 0.5, SL + 0.2, y))
    return c


def terrain(a, z_near, z_far, rows, cols, margin=1.4):
    dn, df = CAM.z - z_near, CAM.z - z_far
    grid = []
    for i in range(rows + 1):
        t = i / rows
        d = dn * (df / dn) ** t
        z = CAM.z - d
        hw = half_w(z, margin)
        row = []
        for j in range(cols + 1):
            x = CAM.x - hw + 2 * hw * j / cols
            y = land_h(x, z)
            e = 0.02 * d + 0.05
            gx = (land_h(x + e, z) - land_h(x - e, z)) / (2 * e)
            gz = (land_h(x, z + e) - land_h(x, z - e)) / (2 * e)
            ny = 1.0 / math.sqrt(1 + gx * gx + gz * gz)
            row.append((a.vert((x, y, z)), land_col(x, y, z, ny)))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            es = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            c = sum((a.v[e[0]] for e in es), Vector()) / 4
            a.face([e[0] for e in es], "ground", [e[1] for e in es], sm=True, out=(c.x, c.y - 100, c.z))


# footprints of everything standing on the ground (x, z, radius), hashed in cells: the woods keep clear of them all,
# the houses of the landmarks (block)
FOOT = {}
BLOCK = []
CELL = 8.0


def keep_clear(x, z, r, block=False):
    for i in range(int((x - r) // CELL), int((x + r) // CELL) + 1):
        for j in range(int((z - r) // CELL), int((z + r) // CELL) + 1):
            FOOT.setdefault((i, j), []).append((x, z, r))
    if block:
        BLOCK.append((x, z, r))


def is_clear(x, z, r=0.0):
    for fx, fz, fr in FOOT.get((int(x // CELL), int(z // CELL)), ()):
        if (x - fx) ** 2 + (z - fz) ** 2 < (fr + r) ** 2:
            return False
    return True


def unblocked(x, z, r):
    return all((x - bx) ** 2 + (z - bz) ** 2 >= (br + r) ** 2 for bx, bz, br in BLOCK)


def build_land(sc):
    fg = sc.acc("fg_crest")
    terrain(fg, 9.0, -6.0, 8, 60, margin=1.2)
    land = sc.acc("land")
    terrain(land, -6.0, -210.0, 76, 104)
    # sandbags along the back of the crest either side of the field, and a pillbox at each end
    rng = random.Random(3)
    bag = hexc("#4a4636")
    for x0, x1 in ((-9.0, -1.2), (12.4, 20.0)):
        x = x0
        while x < x1:
            for row in range(2):
                xx = x + (0.35 if row else 0.0)
                y = land_h(xx, -1.8) + 0.18 + row * 0.3
                c = mul(bag, rng.uniform(0.8, 1.1))
                fg.box((xx, y, -1.8), (0.66, 0.3, 0.45), "fabric", c, cols=(mul(c, 1.15), c), bottom=False,
                       taper=0.9)
            x += 0.7
    for x, s in ((-4.8, 1.0), (16.4, -1.0)):
        y = land_h(x, -3.0)
        fg.box((x, y + 0.6, -3.0), (2.6, 1.4, 2.2), "rock", hexc("#3c3e46"), taper=0.85,
               cols=(hexc("#4a4c56"), hexc("#34363e")), bottom=False)
        fg.box((x, y + 0.75, -1.88), (1.4, 0.16, 0.02), "lamp_glow", (1, 1, 1), bottom=False)
        # a slab roof with a lip, and sandbags on it
        fg.box((x, y + 1.38, -3.0), (2.5, 0.16, 2.1), "rock", hexc("#44464e"), bottom=False)
        for k in range(3):
            fg.box((x - 0.7 + k * 0.7, y + 1.58, -3.4), (0.62, 0.26, 0.42), "fabric", mul(bag, 0.9 + 0.1 * k),
                   bottom=False, taper=0.85)
        keep_clear(x, -3.0, 2.2)


# ------------------------------------------------------------------ the military post

OLIVE = hexc("#3e4230")
KHAKI = hexc("#57533c")
STEEL = hexc("#2c2e34")


def crate(a, x, y, z, s, ry, col):
    a.box((x, y + s[1] / 2, z), s, "paint", col, ry=ry, cols=(mul(col, 1.2), col), bottom=False)
    # the lid's rim and a pale stencil panel on the side facing the camera
    a.box((x, y + s[1] + 0.03, z), (s[0] + 0.06, 0.06, s[2] + 0.06), "paint", mul(col, 0.8), ry=ry, bottom=False)
    cr, sr = math.cos(ry), math.sin(ry)
    fz = s[2] / 2 + 0.01
    px, pz = x + fz * sr, z + fz * cr
    w, h = s[0] * 0.45, s[1] * 0.35
    ex, ez = cr * w / 2, -sr * w / 2
    yy = y + s[1] * 0.55
    a.poly([(px - ex, yy - h / 2, pz - ez), (px + ex, yy - h / 2, pz + ez), (px + ex, yy + h / 2, pz + ez),
            (px - ex, yy + h / 2, pz - ez)], "paint", mul(col, 1.6), out=(x, yy, z))


def drum(a, x, y, z, col):
    a.lathe((x, y, z), [(0.3, 0.0), (0.3, 0.3), (0.32, 0.32), (0.3, 0.34), (0.3, 0.62), (0.32, 0.64), (0.3, 0.66),
                        (0.3, 0.9)], 8, "metal", col)


def soldier(a, x, z, face=0.0, pose="stand", s=1.0):
    """A soldier's silhouette (helmet, greatcoat, rifle): face = yaw (0 looks at the camera, pi away from it);
    pose: stand, glass (binoculars up), point, work (hands on the searchlight), sit."""
    g = land_h(x, z)
    cf, sf = math.cos(face), math.sin(face)

    def P(lx, ly, lz):
        return (x + (lx * cf + lz * sf) * s, g + ly * s, z + (-lx * sf + lz * cf) * s)

    coat, dark, skin = hexc("#3a3c2e"), hexc("#23241e"), hexc("#6a5a4c")
    sit = pose == "sit"
    hip = 0.55 if sit else 0.95
    # legs (boots to hips), or seated legs forward
    for sx in (-0.11, 0.11):
        if sit:
            a.tube(P(sx, hip, 0.0), P(sx, hip, 0.42), 0.075 * s, "fabric", coat, segs=4)
            a.tube(P(sx, hip, 0.42), P(sx, 0.05, 0.48), 0.07 * s, "fabric", coat, segs=4)
        else:
            a.tube(P(sx, 0.05, 0.0), P(sx * 0.8, hip, 0.0), 0.08 * s, "fabric", coat, segs=4)
        a.box(P(sx, 0.06, 0.07 if not sit else 0.52), (0.13 * s, 0.12 * s, 0.26 * s), "fabric", dark, ry=face)
    # the greatcoat (a tapered body down to the knees) and the belt
    a.box(P(0, hip + 0.2 if not sit else hip + 0.3, 0), (0.44 * s, (0.9 if not sit else 0.66) * s, 0.28 * s),
          "fabric", coat, ry=face, taper=0.85, bottom=False)
    a.box(P(0, hip + 0.6, 0), (0.42 * s, 0.07 * s, 0.27 * s), "fabric", dark, ry=face)
    top = hip + 0.62 + (0.1 if sit else 0.0)
    a.box(P(0, top + 0.2, 0), (0.46 * s, 0.4 * s, 0.26 * s), "fabric", coat, ry=face, taper=0.9)
    # head and helmet
    a.blob(P(0, top + 0.53, 0.02), (0.1 * s, 0.12 * s, 0.1 * s), "fabric", skin, segs=6, rings=3)
    a.blob(P(0, top + 0.58, 0.0), (0.16 * s, 0.1 * s, 0.17 * s), "metal", hexc("#3a3e32"), segs=8, rings=3, cut=0.0)
    a.lathe(P(0, top + 0.575, 0.0), [(0.19 * s, 0.0), (0.14 * s, 0.03 * s)], 8, "metal", hexc("#34382c"), cap=False)
    # arms
    sh_y = top + 0.34
    for side in (-1, 1):
        sh = P(side * 0.25, sh_y, 0)
        if pose == "glass":
            el = P(side * 0.22, sh_y - 0.05, 0.28)
            hand = P(side * 0.06, top + 0.5, 0.2)
        elif pose == "point" and side > 0:
            el = P(0.35, sh_y + 0.1, 0.2)
            hand = P(0.5, sh_y + 0.3, 0.55)
        elif pose == "work":
            el = P(side * 0.3, sh_y - 0.2, 0.25)
            hand = P(side * 0.2, sh_y - 0.1, 0.5)
        elif sit:
            el = P(side * 0.28, sh_y - 0.3, 0.1)
            hand = P(side * 0.18, sh_y - 0.4, 0.35)
        else:
            el = P(side * 0.29, sh_y - 0.32, 0.02)
            hand = P(side * 0.27, sh_y - 0.62, 0.05)
        a.tube(sh, el, 0.065 * s, "fabric", coat, segs=4)
        a.tube(el, hand, 0.055 * s, "fabric", coat, segs=4)
    if pose == "glass":
        a.box(P(0, top + 0.5, 0.2), (0.18 * s, 0.07 * s, 0.1 * s), "metal", dark, ry=face)
    # a rifle slung across the back
    a.tube(P(-0.2, hip + 0.1, -0.17), P(0.22, top + 0.5, -0.17), 0.025 * s, "metal", dark, segs=3)


def build_post(sc):
    fg = sc.acc("fg_post")
    rng = random.Random(77)
    # left of the field: the signals corner, with crates, drums, the radio mast and a field radio
    gx = lambda x, z: land_h(x, z)
    for i, (x, z, ry, w) in enumerate(((-2.4, -2.7, 0.2, 1.0), (-3.3, -2.9, -0.1, 0.8), (-2.8, -3.2, 0.4, 0.7),
                                        (-6.4, -2.4, 0.1, 1.1), (-7.3, -2.6, -0.3, 0.9))):
        y = gx(x, z) - 0.05
        crate(fg, x, y, z, (w, 0.62, 0.62), ry, mul(OLIVE, rng.uniform(0.85, 1.1)))
        if i in (0, 3):
            crate(fg, x + 0.1, y + 0.68, z, (w * 0.8, 0.5, 0.55), ry + 0.3, mul(OLIVE, 1.05))
        keep_clear(x, z, 0.8)
    for (x, z) in ((-8.1, -2.2), (-8.6, -2.7), (-8.2, -3.3), (-0.9, -3.0)):
        drum(fg, x, gx(x, z) - 0.05, z, mul(hexc("#3a4a36"), rng.uniform(0.8, 1.1)))
    # the radio mast: a lattice-less pole with cross arms, guy wires and a blinking top light
    mx, mz = -6.0, -4.4
    mg = gx(mx, mz)
    H = 8.5
    fg.tube((mx, mg - 0.3, mz), (mx, mg + H, mz), 0.07, "metal", STEEL)
    for k, yy in enumerate((H * 0.55, H * 0.8)):
        fg.tube((mx - 0.7, mg + yy, mz), (mx + 0.7, mg + yy, mz), 0.03, "metal", STEEL, segs=3)
        for s in (-0.7, 0.7):
            fg.tube((mx + s, mg + yy, mz), (mx + s, mg + yy + 0.9, mz), 0.015, "metal", STEEL, segs=3)
    for ang in (0.5, 2.6, 4.7):
        ax, az = mx + math.cos(ang) * 3.2, mz + math.sin(ang) * 3.2
        fg.tube((mx, mg + H * 0.72, mz), (ax, gx(ax, az) - 0.1, az), 0.012, "metal", hexc("#5a5c62"), segs=3)
    fg.box((mx, mg + H + 0.1, mz), (0.22, 0.22, 0.22), "blink_glow", (1, 1, 1))
    fg.box((mx, mg + H * 0.55 + 0.1, mz), (0.16, 0.16, 0.16), "blink_glow", (1, 1, 1))
    keep_clear(mx, mz, 1.0)
    # a signaller sitting on a crate at the field radio, and a lookout with binoculars
    rx, rz = -3.9, -3.9
    crate(fg, rx + 0.6, gx(rx + 0.6, rz) - 0.05, rz, (0.6, 0.45, 0.5), 0.2, OLIVE)
    fg.box((rx + 0.6, gx(rx + 0.6, rz) + 0.55, rz), (0.4, 0.22, 0.3), "metal", hexc("#2e3228"), ry=0.2)
    fg.box((rx + 0.52, gx(rx + 0.6, rz) + 0.62, rz + 0.16), (0.1, 0.05, 0.01), "lamp_glow", (1, 1, 1), bottom=False)
    fg.tube((rx + 0.75, gx(rx + 0.6, rz) + 0.62, rz), (rx + 0.85, gx(rx + 0.6, rz) + 2.4, rz - 0.1), 0.012, "metal",
            STEEL, segs=3)
    soldier(fg, rx, rz, face=2.2, pose="sit", s=0.95)
    soldier(fg, -1.6, -2.3, face=math.pi + 0.15, pose="glass", s=0.95)
    # right of the field: the flag, crates, a sandbagged searchlight pit with its crew
    fx, fz = 12.9, -2.2
    fgy = gx(fx, fz)
    FH = 5.6
    fg.tube((fx, fgy - 0.3, fz), (fx, fgy + FH, fz), 0.04, "metal", hexc("#6a6a70"), segs=5)
    fg.blob((fx, fgy + FH + 0.04, fz), (0.06, 0.06, 0.06), "metal", hexc("#b0a060"), segs=6, rings=3)
    # the flag: an original banner (night blue, a gold band, a pale chevron at the hoist), a grid for the wave
    cols_n, rows_n = 12, 6
    fw, fh = 0.95, 0.6
    y0 = fgy + FH - 0.05 - fh
    grid = [[fg.vert((fx + 0.05 + fw * i / cols_n, y0 + fh * j / rows_n, fz)) for j in range(rows_n + 1)]
            for i in range(cols_n + 1)]
    for i in range(cols_n):
        for j in range(rows_n):
            u0, u1 = i / cols_n, (i + 1) / cols_n
            v0, v1 = j / rows_n, (j + 1) / rows_n
            um, vm = (u0 + u1) / 2, (v0 + v1) / 2
            # an original banner: pale field, a deep red band, a gold lozenge at the hoist
            c = hexc("#c8ccd4")
            if 0.36 < vm < 0.64:
                c = hexc("#8a2a2e")
            if abs(um - 0.2) * 1.6 + abs(vm - 0.5) < 0.22:
                c = hexc("#e0b848")
            fg.face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]], "flag", c,
                    uvs=[uv(u0, v0), uv(u1, v0), uv(u1, v1), uv(u0, v1)], out=(fx + 1, y0, fz - 1))
    keep_clear(fx, fz, 0.5)
    for (x, z, ry) in ((14.6, -3.2, 0.3), (15.4, -3.0, -0.2)):
        crate(fg, x, gx(x, z) - 0.05, z, (0.9, 0.6, 0.6), ry, mul(OLIVE, rng.uniform(0.85, 1.05)))
    # the searchlight pit: a ring of sandbags round searchlight 2
    sx, sz = SEARCHLIGHTS[2][1], SEARCHLIGHTS[2][2]
    sg = gx(sx, sz)
    for k in range(16):
        ang = math.pi * 0.15 + k * math.pi * 1.7 / 15
        for row in range(2):
            a2 = ang + (0.1 if row else 0.0)
            bx, bz = sx + math.cos(a2) * 1.9, sz + math.sin(a2) * 1.9
            fg.box((bx, gx(bx, bz) + 0.12 + row * 0.26, bz), (0.6, 0.26, 0.4), "fabric",
                   mul(hexc("#4a4636"), rng.uniform(0.8, 1.1)), ry=-a2 + math.pi / 2, bottom=False, taper=0.9)
    soldier(fg, sx - 0.2, sz + 0.95, face=math.pi + 0.3, pose="work", s=0.95)
    soldier(fg, sx + 1.2, sz + 0.2, face=math.pi - 0.6, pose="point", s=0.95)
    keep_clear(sx, sz, 2.4)
    # and a lookout by searchlight 0 on the left
    lx, lz = SEARCHLIGHTS[0][1], SEARCHLIGHTS[0][2]
    soldier(fg, lx + 0.9, lz + 0.6, face=math.pi - 0.4, pose="glass", s=0.95)
    for k in range(10):
        ang = math.pi * 0.2 + k * math.pi * 1.6 / 9
        bx, bz = lx + math.cos(ang) * 1.6, lz + math.sin(ang) * 1.6
        fg.box((bx, gx(bx, bz) + 0.12, bz), (0.6, 0.26, 0.4), "fabric", mul(hexc("#4a4636"), rng.uniform(0.8, 1.1)),
               ry=-ang + math.pi / 2, bottom=False, taper=0.9)
    keep_clear(lx, lz, 2.0)


# ------------------------------------------------------------------ woods and far ridges

PINE_DARK = hexc("#0c1618")
PINE_LIT = hexc("#23383a")


def pine(a, x, y, z, h, rng, tiers=3, segs=5):
    """A pine: stacked cones (no bases), darker at the foot of each tier, the tips catching the moon."""
    r = h * rng.uniform(0.26, 0.34)
    lean = rng.uniform(-0.05, 0.05) * h
    base = mix(PINE_DARK, PINE_LIT, rng.uniform(0.0, 0.25))
    tip = mix(PINE_DARK, PINE_LIT, rng.uniform(0.55, 1.0))
    a0 = rng.uniform(0, 6.28)
    for k in range(tiers):
        t0 = 0.12 + k * (0.72 / tiers)
        by = y + h * t0
        ty = y + h * min(1.0, t0 + 0.5)
        rr = r * (1.0 - 0.7 * k / tiers)
        apex = a.vert((x + lean * (k + 1) / tiers, ty, z))
        ring = [a.vert((x + math.cos(a0 + 6.2832 * j / segs) * rr, by - 0.12 * rr,
                        z + math.sin(a0 + 6.2832 * j / segs) * rr)) for j in range(segs)]
        for j in range(segs):
            q = (j + 1) % segs
            a.face([ring[j], ring[q], apex], "foliage", [base, base, tip], out=(x, by - 50, z))


def build_woods(sc):
    rng = random.Random(501)
    near = sc.acc("wood_near")
    far = sc.acc("wood_far")
    n = 0
    zz = -6.0
    while zz > -200.0:
        step = 0.9 + (-zz) * 0.02
        hw = half_w(zz, 1.25)
        xx = CAM.x - hw
        while xx < CAM.x + hw:
            x = xx + rng.uniform(-0.45, 0.45) * step
            z = zz + rng.uniform(-0.45, 0.45) * step
            xx += step * rng.uniform(0.8, 1.2)
            g = land_h(x, z)
            if g < SL + 1.2:
                continue
            px, py = plane_xy(x, g, z)
            if math.hypot(x - CAM.x, z - CAM.z) < 38.0:
                continue
            # the woods: clumps where a noise is high, thicker on the hills and headlands than on the terrace
            hill = 0.0 if terraced(x, z, 2.0) and not (x < -17.0 and z < -56.0) else 1.0
            dens = 0.5 + 0.6 * fbm(x, z, 0.07, 3, 8.0) + 0.45 * hill - 0.15
            if -60.0 < z < -46.0 and terraced(x, z, 2.0):
                dens -= 0.5   # the town's upper streets
            # keep the slope right behind the ground line open (it reads as the field's floor)
            if -0.8 < px < 12.0 and z > -50.0:
                continue
            if rng.random() > dens:
                continue
            h = rng.uniform(2.6, 4.6) * (1.0 + 0.3 * hill)
            if not is_clear(x, z, h * 0.3):
                continue
            gx, gz = slope(x, z)
            if gx * gx + gz * gz > 2.2:
                continue
            if -zz < 70:
                pine(near, x, g - 0.35, z, h, rng, tiers=3, segs=5)
            else:
                pine(far, x, g - 0.35, z, h * 1.1, rng, tiers=2, segs=4)
            n += 1
        zz -= step
    print("pines", n)


SEA_C = (5.6, 22.0)   # the game's sea disc: centred here, radius 200 (anything farther would float over its rim)


def far_ridges(sc):
    rng = random.Random(9)
    a = sc.acc("far_ridges")
    # layered ridges past the bay at the sides, on arcs inside the sea disc (so their feet stand in the water):
    # the nearer darker, lower, crested with pines; the farther paler (the fog does the rest). The middle of the
    # horizon (behind the field) stays open sea.
    layers = (
        # radius, angle from, angle to (0 = straight out to sea, negative to the left), height, seed, colour, trees
        (196.0, -1.25, -0.12, 14.0, 1.0, "#262e4c", False),
        (196.0, 0.3, 1.3, 19.0, 2.0, "#262e4c", False),
        (182.0, -1.2, -0.17, 10.0, 4.0, "#1c2440", True),
        (184.0, 0.38, 1.2, 13.0, 5.0, "#1c2440", True),
        (168.0, -1.15, -0.21, 7.0, 3.0, "#141a30", True),
    )
    for (R, a0, a1, hh, seed, col, trees) in layers:
        n = int(R * (a1 - a0) / 1.4)
        prev = None
        c = hexc(col)
        for i in range(n + 1):
            t = i / n
            ang = a0 + (a1 - a0) * t
            rr = R - 8.0 * abs(n2(t * 9.0, R, 1.0, seed))
            x, z = SEA_C[0] + math.sin(ang) * rr, SEA_C[1] - math.cos(ang) * rr
            e = smooth(0.0, 0.3, t) * (1 - smooth(0.7, 1.0, t))
            if a0 < 0:
                e = smooth(0.0, 0.25, t) * (1 - smooth(0.55, 1.0, t))
            rough = fbm(x, z, 0.025, 4, seed) + 0.25 * abs(n2(x, z, 0.12, seed + 2.0))
            y = SL - 0.5 + hh * e * (0.5 + 0.5 * rough)
            va = a.vert((x, SL - 3.0, z))
            vb = a.vert((x, y, z))
            if prev:
                a.face([prev[0], va, vb, prev[1]], "rock", [c, c, mul(c, 1.15), mul(c, 1.15)],
                       out=(SEA_C[0] + math.sin(ang) * (R + 50), y, SEA_C[1] - math.cos(ang) * (R + 50)))
            prev = (va, vb)
            if trees and e > 0.08:
                for k in range(2):
                    tx, tz = x + rng.uniform(-0.6, 0.6), z + 0.2
                    th = rng.uniform(1.0, 2.2) * (R / 170.0)
                    tw = th * 0.28
                    a.poly([(tx - tw, y - 0.4, tz), (tx + tw, y - 0.4, tz), (tx, y + th, tz)],
                           "foliage", [c, c, mul(c, 0.85)], out=(tx, y, tz - 5))
    # lights on the far shore past the bay: villages on the right-hand hills
    for i in range(70):
        x = rng.uniform(55, 150)
        z = rng.uniform(-155, -125) - (x - 55) * 0.4
        y = land_h(x, z)
        if y < SL + 0.5:
            continue
        a.gem((x, y + 0.4, z), 0.28, "lamp_glow" if rng.random() < 0.7 else "coolwindow_glow", (1, 1, 1))
        # lights near the water on the far side of the bay throw streaks across it
        if y < SL + 5.0:
            for dz in (1.0, 2.0, 3.0, 4.0):
                if land_h(x + (CAM.x - x) * 0.02 * dz, z + dz * 1.5) < SL - 0.2:
                    sc.acc("harbour_reflections").streak(x, z + dz * 1.5, 0.5, 14.0)
                    break


# ------------------------------------------------------------------ the town

WALLS = [hexc(h) for h in ("#4a4a5c", "#55505a", "#3e4654", "#5a5660", "#48505a", "#524a50", "#3a3e4c", "#5c5448",
                           "#46505a", "#605a52")]
ROOFS = [hexc(h) for h in ("#2a2a36", "#34303a", "#26303a", "#3a3036", "#42302c", "#2c3440")]
AWNINGS = [hexc(h) for h in ("#7a2a30", "#2a5a4a", "#2a3a6a", "#6a4a24", "#5a2a5a")]
NEONS = [hexc(h) for h in ("#ff3aa0", "#30e0ff", "#50ff90", "#ffb030", "#a070ff", "#ff4040")]
GLASS = hexc("#141c2a")


def py_limit(x, z):
    """The highest a roof may reach on the play plane (keeps the middle of the field clear)."""
    px = CAM.x + (x - CAM.x) * plane_factor(z)
    side = smooth(3.5, 9.0, abs(px - CAM.x))
    # the sea's horizon is at about 3.6: the rows nearest the field stay lower so the harbour shows over them
    mid = 2.75 + 0.5 * smooth(-50.0, -85.0, z)
    return mid + (6.25 - mid) * side


def y_limit(x, z):
    return CAM.y + (py_limit(x, z) - CAM.y) / plane_factor(z)


def gable(a, x, z, w, d, top, rh, roof, wall, over=0.25):
    """A pitched roof, its ridge along x, with eaves."""
    x0, x1 = x - w / 2 - over * 0.5, x + w / 2 + over * 0.5
    zf, zb = z + d / 2 + over, z - d / 2 - over
    ye = top - over * rh / (d / 2)
    yt = top + rh
    a.poly([(x0, ye, zf), (x1, ye, zf), (x1, yt, z), (x0, yt, z)], "paint", roof, out=(x, top - 5, z + d))
    a.poly([(x0, ye, zb), (x1, ye, zb), (x1, yt, z), (x0, yt, z)], "paint", mul(roof, 0.75), out=(x, top - 5, z - d))
    for sx in (-1, 1):
        xx = x + sx * w / 2
        a.poly([(xx, top, z - d / 2), (xx, top, z + d / 2), (xx, yt, z)], "paint", wall, out=(x, top, z))


def chimney(a, x, y0, z, h, col):
    a.box((x, y0 + h / 2, z), (0.42, h, 0.42), "paint", col, bottom=False)
    a.box((x, y0 + h + 0.06, z), (0.58, 0.12, 0.58), "paint", mul(col, 0.8))
    a.box((x, y0 + h + 0.2, z), (0.14, 0.2, 0.14), "paint", hexc("#6a4a3a"), bottom=False)


def water_tank(a, x, y0, z, r=0.7):
    wood = hexc("#5a4a3c")
    for lx, lz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        a.tube((x + lx * r * 0.7, y0, z + lz * r * 0.7), (x + lx * r * 0.6, y0 + 1.4, z + lz * r * 0.6), 0.05,
               "metal", STEEL, segs=3)
    a.lathe((x, y0 + 1.4, z), [(r, 0.0), (r, 1.3), (r * 1.05, 1.32)], 8, "paint",
            lambda y: mix(mul(wood, 0.7), wood, y / 1.3), cap=False)
    a.lathe((x, y0 + 2.72, z), [(r * 1.08, 0.0), (0.05, 0.55)], 8, "paint", hexc("#2e2c30"))


def neon_sign(deco, rng, x, y, z, kind):
    col = rng.choice(NEONS)
    if kind == 0:
        # a blade sign sticking out from the wall
        deco.box((x, y, z + 0.4), (0.1, 1.5, 0.6), "neon_glow", col)
        deco.box((x, y, z + 0.4), (0.14, 1.6, 0.66), "paint", hexc("#1a1a22"), bottom=True)
    elif kind == 1:
        # a bar above the shopfront, with a second tube under it
        deco.box((x, y, z + 0.06), (1.8, 0.16, 0.05), "neon_glow", col)
        deco.box((x - 0.2, y - 0.3, z + 0.06), (1.2, 0.08, 0.05), "neon_glow", rng.choice(NEONS))
    else:
        # a small arrow or a ring
        deco.lathe((x, y, z + 0.06), [(0.35, -0.04), (0.35, 0.04)], 10, "neon_glow", col, cap=False)


def building(a, win, deco, rng, x, z, w, d, h, ground, shop=True):
    wall = rng.choice(WALLS)
    roof = rng.choice(ROOFS)
    top = ground + h
    a.box((x, ground + h / 2 - 1.0, z), (w, h + 2.0, d), "paint", wall, cols=(roof, wall), bottom=False)
    # a string course under the eaves
    a.box((x, top - 0.1, z), (w + 0.12, 0.18, d + 0.12), "paint", mul(wall, 0.75), bottom=False)
    kind = rng.random()
    rise = 0.0
    if kind < 0.45:
        rh = d * rng.uniform(0.28, 0.42)
        gable(a, x, z, w, d, top, rh, roof, wall)
        rise = rh
        for k in range(rng.randint(0, 2)):
            chimney(a, x + rng.uniform(-w / 2 + 0.5, w / 2 - 0.5), top, z + rng.choice((-1, 1)) * d * 0.18,
                    rh * 0.7 + 0.8, mul(rng.choice(WALLS), 0.9))
    elif kind < 0.66:
        rh = min(w, d) * rng.uniform(0.3, 0.45)
        a.box((x, top + rh / 2, z), (w + 0.3, rh, d + 0.3), "paint", roof, taper=0.25, cols=(roof, roof),
              bottom=False)
        rise = rh
        if rng.random() < 0.6:
            chimney(a, x + rng.uniform(-w / 4, w / 4), top, z, rh + 0.6, mul(wall, 0.9))
        # dormer windows on the front slope
        if w > 3.4 and rng.random() < 0.6:
            for k in range(2):
                dx = x + (k - 0.5) * w * 0.4
                win.quad_facing((dx, top + rh * 0.35, z + d / 2 - 0.1), 0.4, 0.45,
                                "window_glow" if rng.random() < 0.5 else "glass", GLASS)
    else:
        a.box((x, top + 0.2, z), (w + 0.3, 0.4, d + 0.3), "paint", mul(wall, 0.85), bottom=False)
        r = rng.random()
        if r < 0.1:
            water_tank(a, x + rng.uniform(-w, w) * 0.2, top + 0.4, z + rng.uniform(-d, d) * 0.15)
            rise = 3.2
        elif r < 0.45:
            a.box((x + rng.uniform(-w, w) * 0.25, top + 0.9, z + rng.uniform(-d, d) * 0.2), (w * 0.3, 1.0, d * 0.3),
                  "paint", mul(wall, 0.8), bottom=False)
            rise = 1.4
        elif r < 0.62:
            # a rooftop sign on two posts
            col = rng.choice(NEONS)
            for s in (-1, 1):
                a.tube((x + s * w * 0.3, top + 0.4, z + d * 0.3), (x + s * w * 0.3, top + 1.6, z + d * 0.3), 0.04,
                       "metal", STEEL, segs=3)
            deco.box((x, top + 1.35, z + d * 0.3), (w * 0.62, 0.5, 0.06), "paint", hexc("#1a1a24"))
            deco.box((x, top + 1.45, z + d * 0.3 + 0.05), (w * 0.52, 0.1, 0.04), "neon_glow", col)
            deco.box((x - w * 0.08, top + 1.25, z + d * 0.3 + 0.05), (w * 0.36, 0.08, 0.04), "neon_glow",
                     rng.choice(NEONS))
            rise = 1.8
    # the ground floor: a lit shopfront with an awning and maybe a neon sign, or a door and dark windows
    fz = z + d / 2 + 0.03
    first = ground + 0.9
    if shop and h > 3.4 and rng.random() < 0.55:
        sw = w * 0.72
        win.quad_facing((x, ground + 0.95, fz), sw, 1.3, "shop_glow",
                        rng.choice([(1.0, 0.85, 0.6), (1.0, 0.75, 0.5), (0.5, 0.62, 0.85), (1.0, 0.9, 0.75)]))
        ac = rng.choice(AWNINGS)
        strips = 5
        for k in range(strips):
            x0 = x - sw / 2 - 0.1 + (sw + 0.2) * k / strips
            x1 = x - sw / 2 - 0.1 + (sw + 0.2) * (k + 1) / strips
            c = ac if k % 2 == 0 else mix(ac, (0.85, 0.82, 0.75), 0.6)
            deco.poly([(x0, ground + 2.05, fz), (x1, ground + 2.05, fz), (x1, ground + 1.75, fz + 0.9),
                       (x0, ground + 1.75, fz + 0.9)], "fabric", c, out=(x, ground, z))
        if rng.random() < 0.55:
            k = rng.randint(0, 2)
            if k == 0:
                neon_sign(deco, rng, x + rng.choice((-1, 1)) * (w / 2 - 0.25), ground + 3.1, fz, 0)
            else:
                neon_sign(deco, rng, x, ground + 2.5, fz, k)
        first = ground + 2.9
    else:
        win.quad_facing((x + rng.uniform(-w, w) * 0.25, ground + 0.75, fz), 0.7, 1.4, "paint", hexc("#2a2226"))
    # windows: rows of floors on the front (facing the camera) and on the side facing the middle
    lit = rng.uniform(0.3, 0.62)
    cool = rng.uniform(0.0, 0.5)
    balcony = kind >= 0.66 and rng.random() < 0.45
    fh = 1.3
    y = first
    nx = max(1, int((w - 0.6) / 1.05))
    x0 = x - (nx - 1) * 1.05 / 2
    while y < top - 0.5:
        for i in range(nx):
            xx = x0 + i * 1.05
            if rng.random() < lit:
                win.quad_facing((xx, y, fz), 0.5, 0.7, "coolwindow_glow" if rng.random() < cool else "window_glow")
            else:
                win.quad_facing((xx, y, fz), 0.5, 0.7, "glass", mul(GLASS, rng.uniform(0.8, 1.4)))
        if balcony and y > ground + 2.0:
            bc = mul(wall, 0.65)
            a.box((x, y - 0.42, z + d / 2 + 0.3), (w * 0.8, 0.1, 0.6), "paint", bc)
            a.box((x, y - 0.18, z + d / 2 + 0.58), (w * 0.8, 0.42, 0.04), "metal", mul(bc, 0.7))
        sx = x - w / 2 - 0.03 if x > CAM.x else x + w / 2 + 0.03
        zz = z - d / 2 + 0.7
        while zz < z + d / 2 - 0.5:
            if rng.random() < lit * 0.7:
                win.quad_facing((sx, y, zz), 0.5, 0.7, "window_glow", axis="x", sign=1 if x > CAM.x else -1)
            zz += 1.05
        y += fh
    keep_clear(x, z, max(w, d) * 0.62)
    return top + rise


def lamp_post(a, glow, pools, x, z, h=3.0, arm=0.55, dirx=1.0, g=None):
    """A street lamp: a post, an arm, a lamp head and the pool of light it throws."""
    g = land_h(x, z) if g is None else g
    a.tube((x, g - 0.3, z), (x, g + h, z), 0.055, "metal", STEEL, segs=4)
    a.tube((x, g + h, z), (x + arm * dirx, g + h + 0.12, z), 0.035, "metal", STEEL, segs=3)
    glow.box((x + arm * dirx, g + h, z), (0.3, 0.12, 0.26), "lamp_glow", (1, 1, 1))
    pools.flat((x + arm * dirx, land_h(x + arm * dirx, z) + 0.1, z), 3.4, 3.4, "pool_glow")
    keep_clear(x, z, 0.4)


def road(a, pts, width, lift=0.12, col=hexc("#1e2026")):
    """A strip of tarmac along pts (x, z), hugging the ground; returns the polyline at headlight height."""
    out = []
    prev = None
    for i, (x, z) in enumerate(pts):
        j0, j1 = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = Vector((j1[0] - j0[0], j1[1] - j0[1])).normalized()
        s = Vector((-t.y, t.x)) * width / 2
        ya = land_h(x + s.x, z + s.y) + lift
        yb = land_h(x - s.x, z - s.y) + lift
        va = a.vert((x + s.x, ya, z + s.y))
        vb = a.vert((x - s.x, yb, z - s.y))
        if prev:
            a.face([prev[0], prev[1], vb, va], "road", col, out=(x, min(ya, yb) - 5, z))
        prev = (va, vb)
        out.append((x, land_h(x, z) + 0.45, z))
    return out


def build_city(sc):
    rng = random.Random(25)
    a = sc.acc("city_blocks")
    win = sc.acc("city_windows")
    deco = sc.acc("city_signs")
    lamps = sc.acc("city_lamps")
    posts = sc.acc("city_posts")
    pools = sc.acc("city_pools")
    masts = sc.acc("city_masts")
    roads = sc.acc("city_roads")
    tops = []
    build_landmarks(sc, a, win, deco, lamps, rng)
    z = -45.0
    row = 0
    while z > -94.0:
        # the street in front of the row: tarmac, a line of lamps, and the path for the cars
        zz = z + 3.3
        seg = []
        xl = -48.0
        while xl <= 48.0:
            ok = land_h(xl, zz) > SL + 1.0 and zz > shore_z(xl) + 4 and terraced(xl, zz, 3.0)
            if ok:
                seg.append((xl, zz + 0.4 * math.sin(xl * 0.07 + row)))
            if (not ok or xl + 1.5 > 48.0) and len(seg) > 6:
                PATHS["roads"].append(road(roads, seg, 2.2))
                seg = []
            elif not ok:
                seg = []
            xl += 1.5
        xl = -46.0 + rng.uniform(0, 2)
        side = 1.0
        while xl < 46.0:
            g = land_h(xl, zz + 1.3)
            if g > SL + 1.0 and zz > shore_z(xl) + 4 and terraced(xl, zz, 3.0):
                lamp_post(posts, lamps, pools, xl, zz + 1.3 * side, h=2.8, arm=0.5, dirx=0.0)
            xl += rng.uniform(4.6, 5.8)
            side = -side
        x = -48.0 + (1.7 if row % 2 else 0.0)
        while x < 48.0:
            w = rng.uniform(2.6, 4.8)
            d = rng.uniform(3.0, 4.6)
            cx, cz = x + w / 2, z + rng.uniform(-0.5, 0.5)
            x += w + rng.uniform(0.2, 0.8)
            if rng.random() < 0.05:
                continue
            ground = min(land_h(cx - w / 2, cz), land_h(cx + w / 2, cz), land_h(cx, cz - d / 2), land_h(cx, cz + d / 2))
            if ground < SL + 1.2 or cz < shore_z(cx) + 6.0:
                continue
            # not on the steep hills: the base must be near the terrace's own slope
            if not terraced(cx, cz, 3.2) or not unblocked(cx, cz, max(w, d) * 0.5):
                continue
            hmax = y_limit(cx, cz) - ground
            h = rng.uniform(3.0, 7.5)
            if hmax < 2.2:
                continue
            h = min(h, hmax - 0.5)
            if h < 2.2:
                continue
            top = building(a, win, deco, rng, cx, cz, w, d, h, ground)
            tops.append((cx, ground + h, cz, h))
        z -= rng.uniform(5.6, 6.4)
        row += 1
    # cottages scattered on the slope below the crest, left and right of the field
    for i in range(140):
        cx = rng.choice([rng.uniform(-40.0, -8.0), rng.uniform(18.0, 52.0), rng.uniform(26.0, 52.0)])
        cz = rng.uniform(-60.0, -14.0)
        g = land_h(cx, cz)
        gx_, gz_ = slope(cx, cz)
        if gx_ * gx_ + gz_ * gz_ > 0.25 or not unblocked(cx, cz, 2.0) or not is_clear(cx, cz, 1.6):
            continue
        if -0.8 < plane_xy(cx, g, cz)[0] < 12.0:
            continue
        w, d = rng.uniform(2.2, 3.4), rng.uniform(2.0, 2.8)
        g = min(land_h(cx - w / 2, cz - d / 2), land_h(cx + w / 2, cz - d / 2), land_h(cx - w / 2, cz + d / 2),
                land_h(cx + w / 2, cz + d / 2))
        building(a, win, deco, rng, cx, cz, w, d, rng.uniform(2.4, 3.6), g - 0.2, shop=False)
    # a winding road down the right-hand hill from the crest to the harbour, lamps on posts along it
    pts = []
    for i in range(90):
        t = i / 89.0
        pts.append((30.0 - 18.0 * t + 6.0 * math.sin(t * 7.0), -8.0 - t * 80.0))
    PATHS["roads"].append(road(roads, pts, 1.8))
    for i in range(0, 90, 3):
        xx, zz = pts[i]
        for off in (-1.3, 1.3):
            g = land_h(xx + off, zz)
            if g > SL + 1.0 and (i // 3) % 2 == (0 if off < 0 else 1):
                lamps.box((xx + off, g + 1.9, zz), (0.22, 0.14, 0.22), "lamp_glow", (1, 1, 1), bottom=False)
                posts.tube((xx + off, g - 0.2, zz), (xx + off, g + 1.85, zz), 0.045, "metal", STEEL, segs=3)
                pools.flat((xx + off, g + 0.1, zz), 2.6, 2.6, "pool_glow")
                keep_clear(xx + off, zz, 0.6)
        keep_clear(xx, zz, 1.4)
    # and one down the left towards the lighthouse, through the woods
    pts = []
    for i in range(80):
        t = i / 79.0
        pts.append((-6.0 - 16.0 * t - 5.0 * math.sin(t * 6.0), -9.0 - t * 72.0))
    PATHS["roads"].append(road(roads, pts, 1.6))
    for i in range(0, 80, 5):
        xx, zz = pts[i]
        g = land_h(xx + 1.2, zz)
        lamps.box((xx + 1.2, g + 1.9, zz), (0.2, 0.14, 0.2), "lamp_glow", (1, 1, 1), bottom=False)
        posts.tube((xx + 1.2, g - 0.2, zz), (xx + 1.2, g + 1.85, zz), 0.045, "metal", STEEL, segs=3)
    for (xx, zz) in pts:
        keep_clear(xx, zz, 1.3)
    # the coast road round the far right-hand shore of the bay, climbing over the hill in bends, lamps along it
    pts = []
    x = 44.0
    while x < 120.0:
        z = -92.0
        while z > -220.0 and land_h(x, z) > SL + 3.0:
            z -= 0.5
        pts.append((x, z + 1.5))
        x += 2.0
    for k in range(1, 5):
        # the hairpins up the hill beyond
        x0, z0 = pts[-1]
        for i in range(8):
            t = i / 7.0
            pts.append((x0 + (8.0 if k % 2 else -8.0) * t, z0 - 6.0 * (k - 1) / 4.0 - 1.5 * t))
    good = [(x, z) for (x, z) in pts if land_h(x, z) > SL + 0.8]
    if len(good) > 4:
        PATHS["roads"].append(road(roads, good, 1.6))
        for i in range(0, len(good), 4):
            xx, zz = good[i]
            g = land_h(xx, zz + 1.0)
            lamps.gem((xx, g + 1.8, zz + 1.0), 0.18, "lamp_glow", (1, 1, 1))
            posts.tube((xx, g - 0.2, zz + 1.0), (xx, g + 1.7, zz + 1.0), 0.04, "metal", STEEL, segs=3)
            keep_clear(xx, zz, 1.4)
    # masts with blinking aviation lights on the tall roofs, and the air-raid lamps (the game makes them flash)
    tall = sorted(tops, key=lambda t: -t[3])
    for (cx, top, cz, h) in tall[:6]:
        masts.tube((cx, top, cz), (cx, top + 3.0, cz), 0.08, "metal", hexc("#2a2c34"))
        masts.box((cx, top + 3.1, cz), (0.3, 0.3, 0.3), "blink_glow", (1, 1, 1))
    for (cx, top, cz, h) in rng.sample(tops, min(24, len(tops))):
        masts.tube((cx, top, cz), (cx, top + 1.0, cz), 0.07, "metal", hexc("#2a2c34"))
        masts.blob((cx, top + 1.15, cz), (0.32, 0.26, 0.32), "alarm_glow", (1, 1, 1), segs=8, rings=4)


def build_landmarks(sc, a, win, deco, lamps, rng):
    """The church with its spire (left of the field) and the town hall's clock tower (right)."""
    # the church: nave with a pitched roof along z, a tower and spire at the front, lit tall windows
    cx, cz = -20.0, -52.0
    g = land_h(cx, cz) - 0.3
    stone = hexc("#5a5a66")
    roof = hexc("#2c3038")
    a.box((cx, g + 2.5, cz - 4.0), (5.0, 5.0, 9.0), "paint", stone, cols=(roof, stone), bottom=False)
    # the nave's roof (ridge along z)
    for sx in (-1, 1):
        a.poly([(cx + sx * 2.8, g + 4.8, cz - 8.8), (cx + sx * 2.8, g + 4.8, cz + 0.8), (cx, g + 7.4, cz + 0.8),
                (cx, g + 7.4, cz - 8.8)], "paint", roof if sx > 0 else mul(roof, 0.8), out=(cx, g, cz - 4))
    a.poly([(cx - 2.5, g + 5.0, cz + 0.5), (cx + 2.5, g + 5.0, cz + 0.5), (cx, g + 7.3, cz + 0.5)], "paint", stone,
           out=(cx, g + 5, cz - 5))
    for k in range(3):
        win.quad_facing((cx + 2.53, g + 2.6, cz - 1.5 - k * 2.6), 0.9, 2.2, "stained_glow",
                        [hexc("#ff9a50"), hexc("#ffc070"), hexc("#a060ff"), hexc("#50a0ff")], axis="x", sign=-1)
    # the rose window over the door (on the gable, seen past the tower's side)
    tz = cz + 2.2
    a.box((cx, g + 4.5, tz), (2.6, 9.0, 2.6), "paint", mul(stone, 1.05), bottom=False)
    a.box((cx, g + 9.1, tz), (2.9, 0.3, 2.9), "paint", mul(stone, 0.8), bottom=False)
    for s in (-1, 1):
        win.quad_facing((cx + s * 0.45, g + 7.6, tz + 1.31), 0.4, 1.2, "glass", GLASS)
    win.quad_facing((cx, g + 1.3, tz + 1.31), 1.0, 2.0, "stained_glow", hexc("#ffb060"))
    win.quad_facing((cx, g + 4.6, tz + 1.31), 0.5, 1.4, "stained_glow",
                    [hexc("#50a0ff"), hexc("#50a0ff"), hexc("#ff6a50"), hexc("#ff6a50")])
    # the spire: an eight-sided cone with pinnacles, a cross on top
    a.lathe((cx, g + 9.25, tz), [(1.35, 0.0), (0.05, 6.5)], 8, "paint",
            lambda y: mix(hexc("#2a3038"), hexc("#48505c"), y / 6.5), a0=math.pi / 8)
    for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        a.lathe((cx + sx * 1.25, g + 9.25, tz + sz * 1.25), [(0.2, 0.0), (0.0, 1.2)], 4, "paint", stone)
    a.box((cx, g + 16.1, tz), (0.06, 0.9, 0.06), "metal", hexc("#8a8070"))
    a.box((cx, g + 16.25, tz), (0.45, 0.06, 0.06), "metal", hexc("#8a8070"))
    lamps.box((cx, g + 0.4, tz + 3.0), (0.2, 0.2, 0.2), "lamp_glow", (1, 1, 1))
    keep_clear(cx, cz - 3.0, 6.5, block=True)
    # the town hall: a lit two-storey block with a slim clock tower of pale stone rising from it
    hx, hz = 34.0, -51.0
    g = min(land_h(hx - 3, hz), land_h(hx + 3, hz), land_h(hx, hz)) - 0.3
    wall = hexc("#7a7468")
    trim = hexc("#5c574f")
    a.box((hx, g + 2.4, hz), (8.0, 4.8, 4.6), "paint", wall, cols=(hexc("#2c3036"), wall), bottom=False)
    a.box((hx, g + 4.9, hz), (8.4, 0.3, 5.0), "paint", trim, bottom=False)
    gable(a, hx, hz, 8.0, 4.6, g + 5.0, 1.5, hexc("#2c3036"), wall)
    for i in range(5):
        win.quad_facing((hx - 3.2 + i * 1.6, g + 1.2, hz + 2.33), 0.9, 1.6, "window_glow")
        win.quad_facing((hx - 3.2 + i * 1.6, g + 3.4, hz + 2.33), 0.6, 1.0, "window_glow" if i % 2 else "glass", GLASS)
    T = 2.2
    tz = hz + 0.4
    a.box((hx, g + 7.0, tz), (T, 9.0, T), "paint", mul(wall, 1.12), bottom=False)
    for yy in (5.6, 8.0):
        a.box((hx, g + yy, tz), (T + 0.16, 0.14, T + 0.16), "paint", trim, bottom=False)
    for k in range(2):
        win.quad_facing((hx, g + 6.4 + k * 1.3, tz + T / 2 + 0.02), 0.3, 0.7, "glass", GLASS)
    # the clock stage, a little wider, with a face on the front and on the side facing the middle
    cy = g + 12.2
    a.box((hx, cy, tz), (T + 0.4, 2.6, T + 0.4), "paint", mul(wall, 1.2), bottom=False)
    a.box((hx, cy + 1.4, tz), (T + 0.7, 0.22, T + 0.7), "paint", trim, bottom=False)
    for (fx, fz, ax) in ((hx, tz + T / 2 + 0.22, "z"), (hx - T / 2 - 0.22, tz, "x")):
        pts = []
        for k in range(16):
            ang = 2 * math.pi * k / 16
            if ax == "z":
                pts.append((fx + math.cos(ang) * 0.8, cy + math.sin(ang) * 0.8, fz))
            else:
                pts.append((fx, cy + math.sin(ang) * 0.8, fz + math.cos(ang) * 0.8))
        win.poly(pts, "clock_glow", (1, 1, 1), out=(hx, cy, tz))
        hand = hexc("#16161a")
        if ax == "z":
            deco.poly([(fx - 0.035, cy, fz + 0.02), (fx + 0.035, cy, fz + 0.02), (fx + 0.035, cy + 0.62, fz + 0.02),
                       (fx - 0.035, cy + 0.62, fz + 0.02)], "paint", hand, out=(fx, cy, fz - 1))
            deco.poly([(fx, cy - 0.035, fz + 0.02), (fx, cy + 0.035, fz + 0.02), (fx + 0.42, cy - 0.2, fz + 0.02),
                       (fx + 0.42, cy - 0.27, fz + 0.02)], "paint", hand, out=(fx, cy, fz - 1))
        else:
            deco.poly([(fx - 0.02, cy, fz - 0.035), (fx - 0.02, cy, fz + 0.035), (fx - 0.02, cy + 0.6, fz + 0.035),
                       (fx - 0.02, cy + 0.6, fz - 0.035)], "paint", hand, out=(fx + 1, cy, fz))
    # the open belfry on corner piers, a dim lamp inside, a pyramid roof, a lantern and a vane
    by = cy + 1.5
    for sx in (-1, 1):
        for sz in (-1, 1):
            a.box((hx + sx * (T / 2 - 0.12), by + 0.8, tz + sz * (T / 2 - 0.12)), (0.24, 1.6, 0.24), "paint",
                  mul(wall, 1.12))
    win.gem((hx, by + 0.7, tz), 0.22, "lamp_glow", (1, 1, 1))
    a.box((hx, by + 1.7, tz), (T + 0.3, 0.2, T + 0.3), "paint", trim, bottom=False)
    a.box((hx, by + 3.0, tz), (T + 0.2, 2.4, T + 0.2), "paint", hexc("#2a3434"), taper=0.08, bottom=False)
    a.tube((hx, by + 4.1, tz), (hx, by + 5.2, tz), 0.03, "metal", hexc("#8a8070"), segs=3)
    a.box((hx + 0.18, by + 5.0, tz), (0.4, 0.14, 0.02), "metal", hexc("#8a8070"))
    lamps.box((hx, by + 5.3, tz), (0.16, 0.16, 0.16), "blink_glow", (1, 1, 1))
    keep_clear(hx, hz, 5.0, block=True)
    # two water towers on legs in the town, just under the horizon
    for (x, z) in ((13.0, -79.0), (-13.0, -70.0)):
        gg = land_h(x, z)
        hs = min(1.0, (y_limit(x, z) - gg) / 9.6)
        for lx, lz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            a.tube((x + lx * 1.2, gg - 0.3, z + lz * 1.2), (x + lx * 0.8, gg + 6.0 * hs, z + lz * 0.8), 0.09, "metal",
                   STEEL, segs=4)
        for yy in (2.0 * hs, 4.0 * hs):
            for (ax, az, bx, bz) in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
                k = 1.2 - 0.4 * yy / 6.0
                a.tube((x + ax * k, gg + yy, z + az * k), (x + bx * k, gg + yy, z + bz * k), 0.04, "metal", STEEL,
                       segs=3)
        a.lathe((x, gg + 6.0 * hs, z), [(0.3, 0.0), (1.6, 0.6), (1.6, 2.6), (1.2, 3.1), (0.0, 3.4)], 12, "paint",
                lambda y: mix(hexc("#3a3e46"), hexc("#5a5e68"), y / 3.4))
        lamps.box((x, gg + 6.0 * hs + 3.5, z), (0.2, 0.2, 0.2), "blink_glow", (1, 1, 1))
        keep_clear(x, z, 2.2, block=True)


# ------------------------------------------------------------------ the harbour

def coastline():
    """The shore as polylines (marching squares over the land's height at sea level)."""
    step = 1.2
    xs = [x * step for x in range(int(-110 / step), int(120 / step))]
    zs = [-40.0 - k * step for k in range(int(170 / step))]
    H = [[land_h(x, z) - SL for x in xs] for z in zs]
    segs = []
    for i in range(len(zs) - 1):
        for j in range(len(xs) - 1):
            c = [(xs[j], zs[i], H[i][j]), (xs[j + 1], zs[i], H[i][j + 1]), (xs[j + 1], zs[i + 1], H[i + 1][j + 1]),
                 (xs[j], zs[i + 1], H[i + 1][j])]
            pts = []
            for k in range(4):
                a, b = c[k], c[(k + 1) % 4]
                if (a[2] > 0) != (b[2] > 0):
                    t = a[2] / (a[2] - b[2])
                    pts.append((round(a[0] + (b[0] - a[0]) * t, 3), round(a[1] + (b[1] - a[1]) * t, 3)))
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
            elif len(pts) == 4:
                segs.append((pts[0], pts[1]))
                segs.append((pts[2], pts[3]))
    # chain the segments
    adj = {}
    for s in segs:
        for p in s:
            adj.setdefault(p, []).append(s)
    used = set()
    lines = []
    for s in segs:
        if s in used:
            continue
        used.add(s)
        line = [s[0], s[1]]
        for end in (1, 0):
            while True:
                p = line[-1] if end else line[0]
                nxt = [t for t in adj.get(p, []) if t not in used]
                if not nxt:
                    break
                t = nxt[0]
                used.add(t)
                q = t[1] if t[0] == p else t[0]
                if end:
                    line.append(q)
                else:
                    line.insert(0, q)
        if len(line) > 4:
            lines.append(line)
    return lines


def foam_strip(a, line, width, inner=0.35):
    """Foam along a shore polyline: from just up the beach out to sea (towards falling ground)."""
    L = 0.0
    prev = None
    for i, (x, z) in enumerate(line):
        if i:
            L += math.hypot(x - line[i - 1][0], z - line[i - 1][1])
        gx, gz = slope(x, z, 0.8)
        n = Vector((-gx, -gz))
        if n.length < 1e-4:
            n = Vector((0, -1))
        n.normalize()
        y = SL + 0.05
        va = a.vert((x - n.x * inner, y, z - n.y * inner))
        vb = a.vert((x + n.x * width, y, z + n.y * width))
        if prev:
            a.face([prev[0], prev[1], vb, va], "foam_glow", (1, 1, 1),
                   uvs=[uv(prev[2], 0), uv(prev[2], 1), uv(L, 1), uv(L, 0)], out=(x, y - 5, z))
        prev = (va, vb, L)


def boat(sc, name, bx, bz, L, rng, kind="motor", facing=1.0):
    """A moored boat: a hull with a pointed bow, a cabin with lit windows, a mast with its lights; its reflections
    on the water go with it (the node bobs)."""
    b = sc.acc(name, (bx, SL, bz))
    W = L * 0.3
    hull = rng.choice([hexc("#c8c4bc"), hexc("#34466a"), hexc("#7a3a34"), hexc("#2a5a4a"), hexc("#d0ccc0")])
    deck = hexc("#6a6258")
    f = facing
    top = [(-L / 2, -W / 2), (L * 0.18, -W / 2), (L / 2, 0.0), (L * 0.18, W / 2), (-L / 2, W / 2)]
    y1, y0 = SL + 0.75, SL - 0.1
    T = [b.vert((bx + px * f, y1, bz + pz)) for px, pz in top]
    B = [b.vert((bx + px * f * 0.9, y0, bz + pz * 0.6)) for px, pz in top]
    C = (bx, SL + 0.3, bz)
    for i in range(5):
        j = (i + 1) % 5
        b.face([T[i], T[j], B[j], B[i]], "paint", [hull, hull, mul(hull, 0.55), mul(hull, 0.55)], out=C)
    b.face(T, "paint", deck, out=(bx, SL - 5, bz))
    # a stripe along the side facing the camera
    b.poly([(bx - L / 2 * f, y1 - 0.12, bz + W / 2 + 0.01), (bx + L * 0.18 * f, y1 - 0.12, bz + W / 2 + 0.01),
            (bx + L * 0.18 * f, y1 - 0.2, bz + W / 2 + 0.01), (bx - L / 2 * f, y1 - 0.2, bz + W / 2 + 0.01)], "paint",
           mul(hull, 0.5) if hull[0] > 0.6 else hexc("#d8d4cc"), out=(bx, y1, bz - 5))
    if kind == "motor":
        cw = L * 0.36
        b.box((bx - L * 0.08 * f, y1 + 0.45, bz), (cw, 0.9, W * 0.75), "paint", hexc("#d8d4cc"),
              cols=(hexc("#8a8680"), hexc("#d8d4cc")))
        for k in range(3):
            b.quad_facing((bx - L * 0.08 * f - cw / 3 + k * cw / 3, y1 + 0.52, bz + W * 0.375 + 0.02), cw / 4.5, 0.32,
                          "window_glow" if rng.random() < 0.75 else "coolwindow_glow")
        b.streak(bx - L * 0.08 * f, bz + W * 0.4, 0.45, 5.0, col=(1, 1, 1))
        mh = 2.2
    else:
        mh = L * 1.3
        b.box((bx - L * 0.1 * f, y1 + 0.2, bz), (L * 0.3, 0.4, W * 0.6), "paint", hexc("#c8c4bc"))
        b.quad_facing((bx - L * 0.1 * f, y1 + 0.22, bz + W * 0.3 + 0.02), 0.3, 0.18, "window_glow")
        # the furled sail on its boom
        b.tube((bx + L * 0.1 * f, y1 + 0.9, bz), (bx - L * 0.4 * f, y1 + 0.8, bz), 0.1, "fabric", hexc("#b8b4a8"),
               segs=4)
    b.tube((bx + L * 0.1 * f, y1, bz), (bx + L * 0.1 * f, y1 + mh, bz), 0.035, "metal", hexc("#8a8a90"), segs=4)
    b.box((bx + L * 0.1 * f, y1 + mh + 0.06, bz), (0.14, 0.14, 0.14), "lamp_glow", (1, 1, 1))
    b.streak(bx + L * 0.1 * f, bz + 0.3, 0.2, 5.0 + mh, col=(1, 1, 1))
    # side lights: red to port, green to starboard
    for s, c in ((-1, (1.0, 0.15, 0.1)), (1, (0.2, 1.0, 0.4))):
        b.box((bx + L * 0.15 * f, y1 + 0.1, bz + s * W * 0.45), (0.1, 0.1, 0.1), "harbour_glow", c)
    keep_clear(bx, bz, L * 0.6)


def ferry(sc):
    """The night ferry, crossing the bay (the game moves it along +x): two decks of lit windows, a funnel, lights."""
    fx, fz = 0.0, -150.0
    b = sc.acc("ferry_0", (fx, SL, fz))
    L, W = 22.0, 4.2
    hull = hexc("#2a3450")
    top = [(-L / 2, -W / 2), (L * 0.3, -W / 2), (L / 2, 0.0), (L * 0.3, W / 2), (-L / 2, W / 2)]
    y1, y0 = SL + 1.8, SL - 0.2
    T = [b.vert((fx + px, y1, fz + pz)) for px, pz in top]
    B = [b.vert((fx + px * 0.95, y0, fz + pz * 0.7)) for px, pz in top]
    for i in range(5):
        j = (i + 1) % 5
        b.face([T[i], T[j], B[j], B[i]], "paint", [hull, hull, mul(hull, 0.5), mul(hull, 0.5)], out=(fx, SL, fz))
    b.poly([(fx - L / 2, y1 - 0.25, fz + W / 2 + 0.01), (fx + L * 0.3, y1 - 0.25, fz + W / 2 + 0.01),
            (fx + L * 0.3, y1 - 0.45, fz + W / 2 + 0.01), (fx - L / 2, y1 - 0.45, fz + W / 2 + 0.01)], "paint",
           hexc("#c8c4bc"), out=(fx, y1, fz - 5))
    white = hexc("#d8d6d0")
    decks = ((L * 0.72, 1.4, -0.08), (L * 0.5, 1.2, -0.12))
    y = y1
    for k, (dl, dh, off) in enumerate(decks):
        b.box((fx + L * off, y + dh / 2, fz), (dl, dh, W * 0.82), "paint", white, cols=(hexc("#8a8a88"), white))
        nwin = int(dl / 0.9)
        for i in range(nwin):
            wx = fx + L * off - dl / 2 + 0.45 + i * 0.9
            b.quad_facing((wx, y + dh * 0.55, fz + W * 0.41 + 0.02), 0.5, 0.42,
                          "window_glow" if (i * 7 + k * 3) % 5 else "coolwindow_glow")
        y += dh
    b.box((fx - L * 0.12, y + 0.9, fz), (1.4, 1.8, 1.4), "paint", hexc("#b03a34"), taper=0.9)
    b.box((fx - L * 0.12, y + 1.9, fz), (1.3, 0.3, 1.3), "paint", hexc("#1a1a1e"))
    b.tube((fx + L * 0.12, y, fz), (fx + L * 0.12, y + 3.2, fz), 0.06, "metal", hexc("#8a8a90"))
    b.box((fx + L * 0.12, y + 3.3, fz), (0.22, 0.22, 0.22), "lamp_glow", (1, 1, 1))
    b.box((fx + L * 0.45, y1 + 0.3, fz + W * 0.4), (0.18, 0.18, 0.18), "harbour_glow", (0.2, 1.0, 0.4))
    b.box((fx - L * 0.48, y1 + 0.5, fz), (0.2, 0.2, 0.2), "lamp_glow", (1, 1, 1))
    for i in range(7):
        b.streak(fx - L * 0.35 + i * L * 0.11, fz + W * 0.5, 0.9, 16.0, col=(1, 1, 1))


def ferris_wheel(sc, lights, q, refl, x, z, R, base):
    """The pier's big wheel: a turning rim of bulbs with gondolas on an A-frame. wheel_0's origin is the hub."""
    hub = Vector((x, base + R + 1.4, z))
    w = sc.acc("wheel_0", tuple(hub))
    steel = hexc("#b8bcc8")
    nspk = 16
    segs = 40
    for dz in (-0.45, 0.45):
        ring = [hub + Vector((math.cos(2 * math.pi * k / segs) * R, math.sin(2 * math.pi * k / segs) * R, dz))
                for k in range(segs)]
        for k in range(segs):
            w.tube(ring[k], ring[(k + 1) % segs], 0.07, "metal", steel, segs=3)
        for k in range(nspk):
            ang = 2 * math.pi * k / nspk
            w.tube(hub + Vector((0, 0, dz * 0.6)), hub + Vector((math.cos(ang) * R, math.sin(ang) * R, dz)), 0.04,
                   "metal", steel, segs=3)
    for k in range(nspk):
        ang = 2 * math.pi * k / nspk
        p = hub + Vector((math.cos(ang) * R, math.sin(ang) * R, 0))
        w.tube(p + Vector((0, 0, -0.45)), p + Vector((0, 0, 0.45)), 0.05, "metal", steel, segs=3)
        # a gondola hanging from the rim
        cabin = rng_w.choice([hexc("#c84a4a"), hexc("#3a6ac8"), hexc("#e0b040"), hexc("#3aa070")])
        w.box((p.x, p.y - 0.55, p.z), (0.7, 0.6, 0.7), "paint", cabin, cols=(mul(cabin, 0.7), cabin))
        w.box((p.x, p.y - 0.2, p.z), (0.8, 0.08, 0.8), "paint", mul(cabin, 0.6))
    # the bulbs: round the rim (UV.x = angle, UV.y = 1) and out along every spoke (UV.y = radius)
    pal = [hexc("#ffd890"), hexc("#ff5aa8"), hexc("#50d8ff"), hexc("#ffd890"), hexc("#a0ff70")]
    nb = 64
    for k in range(nb):
        ang = 2 * math.pi * k / nb
        p = hub + Vector((math.cos(ang) * (R + 0.12), math.sin(ang) * (R + 0.12), 0.5))
        w.gem(tuple(p), 0.13, "bulb_glow", pal[k % 5], u=(k / nb, 1.0))
    for k in range(nspk):
        ang = 2 * math.pi * k / nspk
        for i in range(1, 6):
            r = R * i / 6.0
            p = hub + Vector((math.cos(ang) * r, math.sin(ang) * r, 0.5))
            w.gem(tuple(p), 0.1, "bulb_glow", pal[(k + i) % 5], u=(k / nspk, r / R))
    w.blob(tuple(hub + Vector((0, 0, 0.5))), (0.45, 0.45, 0.2), "bulb_glow", hexc("#ffe0a0"), segs=8, rings=3)
    # the A-frame and its platform
    for dz in (-0.9, 0.9):
        for dx in (-1, 1):
            q.tube((x + dx * R * 0.55, base, z + dz * 1.3), tuple(hub + Vector((0, 0, dz))), 0.14, "metal",
                   hexc("#3a3e48"), segs=4)
    q.tube(tuple(hub + Vector((0, 0, -1.0))), tuple(hub + Vector((0, 0, 1.0))), 0.18, "metal", hexc("#3a3e48"))
    q.box((x, base + 0.3, z), (R * 1.4, 0.6, 3.6), "paint", hexc("#4a4a54"), bottom=False)
    q.box((x - R * 0.4, base + 1.1, z + 1.2), (1.2, 1.0, 1.0), "paint", hexc("#c84a4a"), bottom=False)
    q.quad_facing((x - R * 0.4, base + 1.1, z + 1.72), 0.8, 0.5, "window_glow")
    # its reflection: coloured streaks below
    for k, c in enumerate((hexc("#ffd890"), hexc("#ff5aa8"), hexc("#50d8ff"), hexc("#ffd890"), hexc("#ff5aa8"))):
        refl.streak(x - R * 0.8 + k * R * 0.4, z + 1.5, 0.9, 14.0 + 3.0 * (k % 2), col=c)


def carousel(sc, lights, x, z, base):
    """A carousel under a striped tent roof, bulbs round its rim (carousel_0 turns about local Y)."""
    c = sc.acc("carousel_0", (x, base, z))
    r = 2.6
    c.lathe((x, base, z), [(r, 0.0), (r, 0.35), (0.0, 0.4)], 16, "paint", hexc("#7a3a3a"))
    c.tube((x, base, z), (x, base + 3.4, z), 0.25, "paint", hexc("#d0b060"), segs=8)
    for k in range(16):
        a0 = 2 * math.pi * k / 16
        col = hexc("#d84a5a") if k % 2 else hexc("#e8e0d0")
        c.poly([(x + math.cos(a0) * (r + 0.3), base + 3.1, z + math.sin(a0) * (r + 0.3)),
                (x + math.cos(a0 + math.pi / 8) * (r + 0.3), base + 3.1, z + math.sin(a0 + math.pi / 8) * (r + 0.3)),
                (x, base + 4.6, z)], "fabric", col, out=(x, base, z))
        # the valance and a bulb
        c.poly([(x + math.cos(a0) * (r + 0.3), base + 3.1, z + math.sin(a0) * (r + 0.3)),
                (x + math.cos(a0 + math.pi / 8) * (r + 0.3), base + 3.1, z + math.sin(a0 + math.pi / 8) * (r + 0.3)),
                (x + math.cos(a0 + math.pi / 16) * (r + 0.3), base + 2.75, z + math.sin(a0 + math.pi / 16) * (r + 0.3))],
               "fabric", mul(col, 0.8), out=(x, base + 3, z))
        c.gem((x + math.cos(a0) * (r + 0.32), base + 3.05, z + math.sin(a0) * (r + 0.32)), 0.1, "bulb_glow",
              hexc("#ffd890"), u=(k / 16, 1.0))
        if k % 2 == 0:
            # a horse on its pole
            hx, hz = x + math.cos(a0 + 0.2) * (r - 0.6), z + math.sin(a0 + 0.2) * (r - 0.6)
            c.tube((hx, base + 0.4, hz), (hx, base + 3.1, hz), 0.03, "metal", hexc("#d0b060"), segs=3)
            c.box((hx, base + 1.4 + 0.3 * math.sin(k), hz), (0.2, 0.35, 0.7), "paint", hexc("#e8e0d0"),
                  ry=-a0)
    c.gem((x, base + 4.7, z), 0.16, "bulb_glow", hexc("#ffe0a0"), u=(0.0, 0.0))


def build_fair(sc, q, lights, refl):
    """The pleasure pier on the right of the bay: the wheel stands where the pier meets the shore, the deck runs out
    west on piles with lamps, a carousel, booths and festoons of bulbs."""
    pz = -107.0
    x1 = 47.5
    while land_h(x1, pz) < SL + 0.3 and x1 < 60.0:
        x1 += 0.5
    x0 = x1 - 17.0
    deck = SL + 1.6
    cx = (x0 + x1) / 2
    q.box((cx, deck - 0.2, pz), (x1 - x0, 0.4, 6.0), "paint", hexc("#4a4038"),
          cols=(hexc("#5a5048"), hexc("#3a3430")), bottom=False)
    xx = x0 + 0.5
    while xx < x1:
        for dz in (-2.7, 2.7):
            q.tube((xx, SL - 1.0, pz + dz), (xx, deck - 0.3, pz + dz), 0.14, "metal", hexc("#2e2c30"), segs=4)
        xx += 3.0
    # railings, lamps along the front edge and a festoon of bulbs between them
    for dz in (-2.9, 2.9):
        q.tube((x0, deck + 0.9, pz + dz), (x1, deck + 0.9, pz + dz), 0.03, "metal", hexc("#8a8a90"), segs=3)
    q.tube((x0, deck + 0.9, pz - 2.9), (x0, deck + 0.9, pz + 2.9), 0.03, "metal", hexc("#8a8a90"), segs=3)
    pal = [hexc("#ffd890"), hexc("#ff5aa8"), hexc("#50d8ff"), hexc("#a0ff70")]
    n = 6
    for k in range(n + 1):
        lx = x0 + 0.4 + k * (x1 - x0 - 2.0) / n
        for dz in (-2.9, 2.9):
            q.tube((lx, deck, pz + dz), (lx, deck + 2.6, pz + dz), 0.05, "metal", hexc("#2a2a30"), segs=4)
            lights.gem((lx, deck + 2.7, pz + dz), 0.18, "lamp_glow", (1, 1, 1))
        refl.streak(lx, pz + 3.4, 0.5, 9.0)
        if k < n:
            step = (x1 - x0 - 2.0) / n
            for i in range(1, 8):
                t = i / 8.0
                sag = 0.6 * 4 * t * (1 - t)
                lights.gem((lx + t * step, deck + 2.5 - sag, pz + 2.9), 0.08, "bulb_glow", pal[(k + i) % 4],
                           u=((k + t) / n, 0.5))
    wx = x1 + 1.0
    wbase = max(deck, land_h(wx, pz) + 0.2)
    ferris_wheel(sc, lights, q, refl, wx, pz, 6.2, wbase)
    carousel(sc, lights, x0 + 7.0, pz - 0.4, deck)
    for k, bx in enumerate((x0 + 2.4, x0 + 11.5)):
        c = AWNINGS[k + 1]
        q.box((bx, deck + 1.0, pz - 1.4), (2.0, 2.0, 1.8), "paint", hexc("#d8d0c0"), bottom=False)
        q.quad_facing((bx, deck + 1.0, pz - 0.48), 1.4, 0.8, "window_glow")
        for s_ in range(4):
            sx0 = bx - 1.0 + s_ * 0.5
            q.poly([(sx0, deck + 2.1, pz - 0.5), (sx0 + 0.5, deck + 2.1, pz - 0.5), (sx0 + 0.5, deck + 1.8, pz + 0.2),
                    (sx0, deck + 1.8, pz + 0.2)], "fabric", c if s_ % 2 == 0 else hexc("#e8e0d0"),
                   out=(bx, deck, pz - 1.4))
        lights.box((bx, deck + 2.4, pz - 0.5), (1.4, 0.3, 0.05), "neon_glow", pal[k + 1])
    keep_clear(cx, pz, 4.0)
    keep_clear(wx, pz, 7.0, block=True)


def build_harbour(sc):
    rng = random.Random(40)
    q = sc.acc("harbour_quays")
    lights = sc.acc("harbour_lights")
    refl = sc.acc("harbour_reflections")
    foam = sc.acc("harbour_foam")
    prom = sc.acc("harbour_promenade")
    stone = hexc("#4c4a54")
    # the quay along the bay, with a promenade on top: a railing, benches, double lamps and their reflections
    for i in range(44):
        x0 = -22.0 + i * 1.8
        z0 = shore_z(x0 + 0.9)
        if z0 < -125:
            continue
        q.box((x0 + 0.9, SL + 0.5, z0 + 1.2), (1.85, 2.2, 4.0), "rock", mul(stone, rng.uniform(0.85, 1.05)),
              cols=(hexc("#5a5864"), stone), bottom=False)
        keep_clear(x0 + 0.9, z0 + 1.2, 2.0)
    pts = []
    x = -21.0
    while x < 56.0:
        z0 = shore_z(x)
        if z0 > -125:
            pts.append((x, z0 + 0.1))
        x += 1.8
    for (x, z) in pts:
        prom.tube((x, SL + 1.6, z), (x, SL + 2.5, z), 0.03, "metal", hexc("#6a6a72"), segs=3)
    for (a0, b0) in zip(pts, pts[1:]):
        prom.tube((a0[0], SL + 2.45, a0[1]), (b0[0], SL + 2.45, b0[1]), 0.025, "metal", hexc("#6a6a72"), segs=3)
    for k, (x, z) in enumerate(pts):
        if k % 3 != 1:
            continue
        g = SL + 1.6
        prom.tube((x, g, z + 0.4), (x, g + 3.2, z + 0.4), 0.06, "metal", STEEL, segs=4)
        prom.tube((x - 0.5, g + 3.1, z + 0.4), (x + 0.5, g + 3.1, z + 0.4), 0.035, "metal", STEEL, segs=3)
        for s in (-0.5, 0.5):
            lights.blob((x + s, g + 3.35, z + 0.4), (0.18, 0.2, 0.18), "lamp_glow", (1, 1, 1), segs=6, rings=3)
        prom.flat((x, g + 0.08, z + 1.5), 3.6, 3.0, "pool_glow")
        if k % 6 == 1:
            prom.box((x + 1.4, g + 0.3, z + 1.0), (1.4, 0.12, 0.45), "paint", hexc("#4a3a2e"))
            prom.box((x + 1.4, g + 0.55, z + 1.22), (1.4, 0.4, 0.06), "paint", hexc("#4a3a2e"))
    PATHS["roads"].append([(x, SL + 1.6 + 0.45, z + 3.2) for (x, z) in pts])
    # piers out into the bay, lamps along them
    for px in (-6.0, 8.0, 22.0):
        z0 = shore_z(px)
        q.box((px, SL + 0.6, z0 - 8.0), (2.2, 1.4, 16.0), "rock", stone, cols=(hexc("#5a5864"), stone), bottom=False)
        for k in range(4):
            zz = z0 - 2.0 - k * 4.4
            q.tube((px + 1.0, SL + 1.3, zz), (px + 1.0, SL + 3.4, zz), 0.06, "metal", hexc("#2a2c34"))
            lights.box((px + 1.0, SL + 3.5, zz), (0.3, 0.3, 0.3), "lamp_glow", (1, 1, 1))
            refl.streak(px + 1.0, zz + 0.4, 0.5, 11.0)
        # bollards
        for k in range(6):
            q.lathe((px - 0.8, SL + 1.3, z0 - 1.0 - k * 2.6), [(0.14, 0.0), (0.12, 0.35), (0.18, 0.42), (0.0, 0.46)], 6,
                    "metal", hexc("#2a2c34"))
    # container cranes on the right-hand quay, and stacks of containers
    crane = hexc("#5a4a44")
    for i, cx in enumerate((25.0, 32.0)):
        z0 = shore_z(cx)
        base = SL + 1.6
        for lx in (-1.4, 1.4):
            for lz in (0.5, 4.5):
                q.tube((cx + lx, base, z0 + lz), (cx + lx, base + 9.0, z0 + lz), 0.18, "metal", crane)
            q.tube((cx + lx, base + 4.5, z0 + 0.5), (cx + lx, base + 4.5, z0 + 4.5), 0.1, "metal", crane)
            q.tube((cx + lx, base + 0.5, z0 + 0.5), (cx + lx, base + 8.5, z0 + 4.5), 0.07, "metal", crane, segs=4)
        q.box((cx, base + 9.3, z0 + 1.0), (3.4, 0.6, 16.0), "metal", crane)
        q.box((cx, base + 10.6, z0 + 5.0), (1.6, 2.2, 1.6), "metal", mul(crane, 0.8))
        q.quad_facing((cx, base + 10.7, z0 + 5.82), 1.0, 0.6, "coolwindow_glow")
        q.box((cx, base + 8.6, z0 - 4.0), (1.2, 0.8, 1.2), "metal", mul(crane, 0.7))
        q.tube((cx, base + 8.2, z0 - 4.0), (cx, base + 3.0, z0 - 4.0), 0.02, "metal", hexc("#2a2a2e"), segs=3)
        lights.box((cx, base + 11.9, z0 + 5.0), (0.35, 0.35, 0.35), "blink_glow", (1, 1, 1))
        lights.box((cx, base + 9.3, z0 - 7.0), (0.3, 0.3, 0.3), "blink_glow", (1, 1, 1))
        lights.box((cx - 1.2, base + 8.4, z0 + 2.5), (0.3, 0.3, 0.3), "lamp_glow", (1, 1, 1))
        keep_clear(cx, z0 + 2.5, 3.5)
    cc = [hexc(h) for h in ("#7a3a30", "#2e4a6a", "#6a5a2a", "#3a5a4a", "#5a3a5a", "#8a6a3a")]
    for i in range(44):
        cx = rng.uniform(21.0, 40.0)
        cz = rng.uniform(4.0, 12.0) + shore_z(cx)
        g = land_h(cx, cz)
        if g < SL + 0.8:
            continue
        stack = rng.randint(1, 3)
        for k in range(stack):
            c = rng.choice(cc)
            q.box((cx, g + 0.6 + k * 1.2, cz), (3.0, 1.2, 1.25), "metal", c, cols=(mul(c, 1.2), c), bottom=False)
            q.box((cx, g + 0.6 + k * 1.2, cz + 0.63), (2.8, 1.0, 0.02), "metal", mul(c, 0.8), bottom=False)
        keep_clear(cx, cz, 1.8)
    # the breakwater from the right-hand shore, with the harbour lights (green at the tip, red on the far pier)
    bw = [(58.0, -110.0), (46.0, -118.0), (34.0, -124.0), (22.0, -128.0), (14.0, -129.0)]
    for (x0, z0), (x1, z1) in zip(bw, bw[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        ry = math.atan2(-(z1 - z0), x1 - x0)
        q.box(((x0 + x1) / 2, SL + 0.4, (z0 + z1) / 2), (L + 0.6, 2.0, 2.4), "rock", hexc("#3e3e48"), ry=ry,
              cols=(hexc("#4e4c56"), hexc("#34343e")), bottom=False)
        # armour blocks tumbled along its seaward and inner faces
        for k in range(int(L / 1.3)):
            t = (k + 0.5) / int(L / 1.3)
            bx, bz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            for s in (-1, 1):
                nx, nz = -(z1 - z0) / L * s, (x1 - x0) / L * s
                q.box((bx + nx * 1.5 + rng.uniform(-0.3, 0.3), SL + 0.1, bz + nz * 1.5), (1.0, 0.9, 1.0), "rock",
                      mul(hexc("#3a3a44"), rng.uniform(0.8, 1.2)), ry=rng.uniform(0, 3), taper=0.8)
    line = []
    for (x0, z0), (x1, z1) in zip(bw, bw[1:]):
        for k in range(8):
            t = k / 8
            line.append((x0 + (x1 - x0) * t, z0 + (z1 - z0) * t))
    line.append(bw[-1])
    for s in (1, -1):
        Lc = 0.0
        prev = None
        for i, (x, z) in enumerate(line):
            j0, j1 = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
            t = Vector((j1[0] - j0[0], j1[1] - j0[1])).normalized()
            n = Vector((-t.y, t.x)) * s
            if i:
                Lc += math.hypot(x - line[i - 1][0], z - line[i - 1][1])
            va = foam.vert((x + n.x * 1.6, SL + 0.06, z + n.y * 1.6))
            vb = foam.vert((x + n.x * 4.0, SL + 0.06, z + n.y * 4.0))
            if prev:
                foam.face([prev[0], prev[1], vb, va], "foam_glow", (1, 1, 1),
                          uvs=[uv(prev[2], 0), uv(prev[2], 1), uv(Lc, 1), uv(Lc, 0)], out=(x, SL - 5, z))
            prev = (va, vb, Lc)
    tip = bw[-1]
    foam.flat((tip[0] - 1.5, SL + 0.07, tip[1]), 6.0, 5.0, "foam_glow")
    q.lathe((tip[0], SL + 1.4, tip[1]), [(0.5, 0), (0.4, 2.4), (0.0, 2.6)], 8, "paint", hexc("#3a6a4a"))
    lights.blob((tip[0], SL + 4.3, tip[1]), (0.4, 0.4, 0.4), "harbour_glow", (0.2, 1.0, 0.45), segs=8, rings=4)
    refl.streak(tip[0], tip[1] + 1.5, 0.7, 18.0, col=(0.3, 1.0, 0.5))
    rp = (-6.0, shore_z(-6.0) - 16.5)
    q.lathe((rp[0], SL + 1.3, rp[1]), [(0.45, 0), (0.35, 2.0), (0.0, 2.2)], 8, "paint", hexc("#6a3a3a"))
    lights.blob((rp[0], SL + 3.8, rp[1]), (0.38, 0.38, 0.38), "harbour_glow", (1.0, 0.2, 0.15), segs=8, rings=4)
    refl.streak(rp[0], rp[1] + 1.0, 0.6, 16.0, col=(1.0, 0.25, 0.2))
    # the shore's foam, where the land runs into the sea (not along the quays)
    for ln in coastline():
        keep = []
        for (x, z) in ln:
            quay = -23.0 < x < 57.0 and z > shore_z(x) - 3.0 and z > -126.0
            far = math.hypot(x - CAM.x, z - 22.0) > 190.0
            if quay or far:
                if len(keep) > 3:
                    foam_strip(foam, keep, 1.7)
                keep = []
            else:
                keep.append((x, z))
        if len(keep) > 3:
            foam_strip(foam, keep, 1.7)
    # moored boats and the fair
    for i, (bx, bz, kind) in enumerate(((2.5, -100.0, "motor"), (13.0, -103.0, "sail"), (16.5, -98.5, "motor"),
                                        (-1.0, -97.0, "sail"), (26.0, -102.0, "motor"), (-12.0, -100.0, "motor"),
                                        (-16.0, -104.0, "sail"), (5.0, -108.0, "sail"), (19.0, -114.0, "motor"))):
        boat(sc, "boat_%d" % i, bx, bz, rng.uniform(3.2, 5.2), rng, kind, facing=rng.choice((-1.0, 1.0)))
    build_fair(sc, q, lights, refl)
    ferry(sc)


# ------------------------------------------------------------------ landmarks

def build_lighthouse(sc):
    x, z = -30.0, -88.0
    g = land_h(x, z)
    a = sc.acc("lh_tower")
    white, red = hexc("#dcd8d0"), hexc("#b0343a")
    H = 15.0
    dark = hexc("#23252c")

    def band(y):
        return red if int(y / (H / 5.0)) % 2 == 1 else white
    # the tower in bands (each ring's colour by its height), on a stone plinth
    a.lathe((x, g - 0.5, z), [(2.6, 0.0), (2.6, 1.3), (2.3, 1.5)], 16, "rock", hexc("#5a5a62"), cap=False)
    rings = [(1.8 - 0.75 * t / 20.0, H * t / 20.0) for t in range(21)]
    for i in range(20):
        c = band((rings[i][1] + rings[i + 1][1]) / 2)
        a.lathe((x, g, z), [rings[i], rings[i + 1]], 18, "paint", c, cap=False)
    # the door, its lamp, and small windows climbing the tower on the camera's side
    a.quad_facing((x, g + 1.0, z + 1.83), 0.8, 1.6, "paint", hexc("#2a2226"))
    a.box((x, g + 2.1, z + 1.9), (0.2, 0.2, 0.2), "lamp_glow", (1, 1, 1))
    for k, yy in enumerate((4.0, 7.2, 10.4, 13.0)):
        r = 1.8 - 0.75 * yy / H
        ang = 0.5 * (k % 2) - 0.25
        wx, wz = x + math.sin(ang) * (r + 0.02), z + math.cos(ang) * (r + 0.02)
        a.quad_facing((wx, g + yy, wz), 0.35, 0.6, "window_glow" if k % 2 else "glass", GLASS)
    # the corbelled watch room under the gallery
    a.lathe((x, g + H - 0.2, z), [(1.05, 0.0), (1.5, 0.3)], 18, "paint", white, cap=False)
    # the gallery: a deck, a railing of posts with two rails
    a.lathe((x, g + H + 0.1, z), [(1.75, 0.0), (1.75, 0.18), (0.9, 0.18)], 18, "metal", dark, cap=False)
    n = 18
    top_r = [(x + math.cos(2 * math.pi * k / n) * 1.68, z + math.sin(2 * math.pi * k / n) * 1.68) for k in range(n)]
    for k in range(n):
        px, pz = top_r[k]
        a.tube((px, g + H + 0.28, pz), (px, g + H + 1.15, pz), 0.025, "metal", dark, segs=3)
        qx, qz = top_r[(k + 1) % n]
        for yy in (0.7, 1.15):
            a.tube((px, g + H + yy, pz), (qx, g + H + yy, qz), 0.025, "metal", dark, segs=3)
    # the lantern: a glazed drum with mullions, a domed roof with a ventilator ball and a lightning rod
    a.lathe((x, g + H + 0.28, z), [(0.95, 0.0), (0.95, 0.35)], 12, "metal", dark, cap=False)
    a.lathe((x, g + H + 0.63, z), [(0.85, 0.0), (0.85, 1.55)], 12, "lantern_glow", (1, 1, 1), cap=False)
    for k in range(8):
        ang = 2 * math.pi * k / 8
        a.tube((x + math.cos(ang) * 0.87, g + H + 0.63, z + math.sin(ang) * 0.87),
               (x + math.cos(ang) * 0.87, g + H + 2.18, z + math.sin(ang) * 0.87), 0.03, "metal", dark, segs=3)
    a.lathe((x, g + H + 2.18, z), [(1.05, 0.0), (0.95, 0.25), (0.6, 0.7), (0.15, 1.05), (0.0, 1.1)], 12, "metal",
            hexc("#2e3a36"))
    a.blob((x, g + H + 3.45, z), (0.2, 0.2, 0.2), "metal", hexc("#2e3a36"), segs=6, rings=3)
    a.tube((x, g + H + 3.6, z), (x, g + H + 4.6, z), 0.02, "metal", dark, segs=3)
    sc.empty("beam", (x, g + H + 1.4, z))
    keep_clear(x, z, 3.0)
    # the keeper's cottage with a pitched roof, a chimney and lit windows, a wall round the yard
    c = sc.acc("lh_cottage")
    cx, cz = x + 4.8, z + 1.5
    cg = land_h(cx, cz)
    c.box((cx, cg + 1.0, cz), (5.0, 2.6, 3.2), "paint", hexc("#c8c4bc"), cols=(hexc("#5a3a34"), hexc("#b8b4ac")),
          bottom=False)
    gable(c, cx, cz, 5.0, 3.2, cg + 2.3, 1.3, hexc("#4a3430"), hexc("#b8b4ac"))
    chimney(c, cx + 1.6, cg + 2.3, cz - 0.4, 1.6, hexc("#8a8078"))
    c.quad_facing((cx - 1.0, cg + 1.3, cz + 1.63), 0.7, 0.8, "window_glow")
    c.quad_facing((cx + 1.1, cg + 1.3, cz + 1.63), 0.7, 0.8, "window_glow")
    c.quad_facing((cx + 0.05, cg + 0.9, cz + 1.63), 0.6, 1.4, "paint", hexc("#3a2a24"))
    for k in range(14):
        ang = 0.3 + k * 0.33
        wx, wz = x + 1.5 + math.cos(ang) * 6.5, z + 1.0 + math.sin(ang) * 4.2
        c.box((wx, land_h(wx, wz) + 0.35, wz), (1.2, 0.7, 0.35), "rock", mul(hexc("#8a8a90"), 0.8), ry=-ang)
    keep_clear(cx, cz, 4.0)
    # a line of posts with lamps down to the landing
    for k in range(6):
        px = x + 6 + k * 3.0
        pz = z + 5 + k * 2.0
        pg = land_h(px, pz)
        c.tube((px, pg - 0.2, pz), (px, pg + 0.75, pz), 0.04, "metal", STEEL, segs=3)
        c.box((px, pg + 0.8, pz), (0.22, 0.22, 0.22), "lamp_glow", (1, 1, 1), bottom=False)
        keep_clear(px, pz, 0.8)


def dish(sc, name, c, r, tilt, pylon_h, col):
    """A radar dish on a turntable: its node's origin is the turntable (rotate about local Y)."""
    x, y, z = c
    d = sc.acc(name, (x, y + pylon_h, z))
    # the dish: a shallow paraboloid facing +z, tilted up by `tilt`, in panels
    rings, segs = 6, 20
    ca, sa = math.cos(tilt), math.sin(tilt)
    centre = Vector((x, y + pylon_h + r * 0.9, z))

    def P(rr, a, back=0.0):
        lx, ly = math.cos(a) * rr, math.sin(a) * rr
        lz = (rr * rr) / (4.0 * r * 0.6) - back  # depth of the bowl
        # tilt the bowl's axis (+z) up by `tilt` (a turn about x)
        yy = ly * ca - lz * sa
        zz = -ly * sa - lz * ca
        return centre + Vector((lx, yy, zz))
    grid = [[d.vert(P(r * max(i, 0.02) / rings, 2 * math.pi * j / segs)) for j in range(segs)]
            for i in range(rings + 1)]
    for i in range(rings):
        for j in range(segs):
            k = (j + 1) % segs
            ids = [grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]]
            shade = 0.82 + 0.1 * ((i + j) % 2) + 0.08 * i / rings
            d.face(ids, "paint", mul(col, shade), sm=True)
    # the rim and the ribs behind the bowl
    for j in range(segs):
        a0, a1 = 2 * math.pi * j / segs, 2 * math.pi * (j + 1) / segs
        d.tube(P(r, a0), P(r, a1), 0.05, "metal", hexc("#6a6e78"), segs=3)
    for j in range(0, segs, 2):
        a0 = 2 * math.pi * j / segs
        d.tube(P(r * 0.15, a0, 0.35), P(r, a0, 0.05), 0.04, "metal", hexc("#3a3c44"), segs=3)
    # the feed on struts
    tip = centre + Vector((0, sa, ca)) * r * 0.9
    for j in range(3):
        a = 2 * math.pi * j / 3 + 0.5
        d.tube(P(r * 0.95, a), tip, 0.05, "metal", hexc("#3a3c44"), segs=4)
    d.blob(tuple(tip), (0.2, 0.2, 0.2), "metal", hexc("#3a3c44"), segs=6, rings=3)
    d.box((x, y + pylon_h + 0.4, z), (0.9, 0.8, 0.9), "metal", hexc("#3a3c44"))
    d.tube((x, y + pylon_h + 0.4, z), tuple(centre), 0.18, "metal", hexc("#3a3c44"))


def build_radar(sc):
    # the station on the left hill: a lattice pylon, the big dish, a radome, a hut and a mast
    x, z = -11.5, -19.5
    g = land_h(x, z)
    p = sc.acc("radar_station")
    steel = hexc("#3a3e48")
    ph = 4.0
    for (lx, lz) in ((-1.2, -1.2), (1.2, -1.2), (1.2, 1.2), (-1.2, 1.2)):
        p.tube((x + lx, g - 0.5, z + lz), (x + lx * 0.4, g + ph, z + lz * 0.4), 0.09, "metal", steel, segs=4)
    for k in range(3):
        yy = g + 0.8 + k * 1.2
        s = 1.2 - 0.8 * (yy - g) / ph
        for (ax, az, bx, bz) in ((-s, -s, s, -s), (s, -s, s, s), (s, s, -s, s), (-s, s, -s, -s)):
            p.tube((x + ax, yy, z + az), (x + bx, yy + 1.2, z + bz), 0.04, "metal", steel, segs=4)
    p.box((x, g + ph, z), (1.4, 0.3, 1.4), "metal", steel)
    dish(sc, "dish_0", (x, g, z), 2.6, 0.45, ph + 0.15, hexc("#aab0ba"))
    # the radome, panelled, on a ring wall
    p.lathe((x - 5.5, g - 0.3, z - 2.0), [(2.2, 0.0), (2.2, 0.9)], 16, "rock", hexc("#4a4c54"), cap=False)
    p.blob((x - 5.5, g + 0.6, z - 2.0), (2.1, 2.3, 2.1), "paint",
           lambda t: mix(hexc("#8a90a0"), hexc("#c8ccd4"), 0.5 + 0.5 * t), segs=16, rings=8, cut=-0.3)
    p.box((x - 5.5, g + 3.0, z - 2.0), (0.18, 0.18, 0.18), "blink_glow", (1, 1, 1))
    hx, hz = x + 4.0, z + 1.5
    hg = land_h(hx, hz)
    p.box((hx, hg + 0.9, hz), (3.6, 2.0, 2.4), "paint", hexc("#5a5e56"), cols=(hexc("#3a3e3a"), hexc("#5a5e56")),
          bottom=False)
    p.box((hx, hg + 1.95, hz), (3.9, 0.12, 2.7), "paint", hexc("#34383a"))
    for k in range(3):
        p.quad_facing((hx - 1.1 + k * 1.1, hg + 1.1, hz + 1.23), 0.6, 0.5, "coolwindow_glow")
    p.box((hx + 1.3, hg + 1.7, hz + 1.3), (0.16, 0.16, 0.16), "lamp_glow", (1, 1, 1))
    # a fence round the compound: posts and two wires
    fence = []
    for k in range(22):
        ang = k * 2 * math.pi / 22
        fence.append((x - 1.0 + math.cos(ang) * 8.5, z - 0.5 + math.sin(ang) * 6.0))
    for k, (fx, fz) in enumerate(fence):
        fg_ = land_h(fx, fz)
        p.tube((fx, fg_ - 0.2, fz), (fx, fg_ + 1.3, fz), 0.03, "metal", steel, segs=3)
        nx, nz = fence[(k + 1) % len(fence)]
        ng = land_h(nx, nz)
        for yy in (0.6, 1.2):
            p.tube((fx, fg_ + yy, fz), (nx, ng + yy, nz), 0.01, "metal", hexc("#5a5c64"), segs=3)
    keep_clear(x - 1.0, z - 0.5, 8.8)
    mx = x - 2.0
    p.tube((mx, g - 0.5, z - 5.0), (mx, g + 11.0, z - 5.0), 0.08, "metal", steel)
    p.box((mx, g + 11.1, z - 5.0), (0.3, 0.3, 0.3), "blink_glow", (1, 1, 1))
    p.box((mx, g + 7.0, z - 5.0), (0.25, 0.25, 0.25), "blink_glow", (1, 1, 1))
    # the small dish on the right knoll
    x2, z2 = 23.0, -11.5
    g2 = land_h(x2, z2)
    p.tube((x2, g2 - 0.5, z2), (x2, g2 + 1.6, z2), 0.2, "metal", steel)
    dish(sc, "dish_1", (x2, g2, z2), 1.2, 0.7, 1.6, hexc("#aab0ba"))
    keep_clear(x2, z2, 2.0)


# the searchlights: (index, x, z)
SEARCHLIGHTS = [(0, -8.0, -9.0), (1, -19.0, -24.0), (2, 17.6, -5.6), (3, 24.5, -12.0), (4, 50.0, -85.0),
                (5, -26.0, -60.0)]


def searchlight(sc, i, x, z):
    g = land_h(x, z)
    a = sc.acc("searchlight_mount_%d" % i)
    steel = hexc("#34363e")
    a.box((x, g + 0.25, z), (1.4, 0.5, 1.4), "rock", hexc("#44444c"), bottom=False)
    for s in (-1, 1):
        a.tube((x + s * 0.5, g + 0.5, z), (x + s * 0.5, g + 1.6, z), 0.07, "metal", steel)
    a.lathe((x, g + 1.2, z), [(0.55, 0.0), (0.6, 0.9), (0.0, 0.92)], 12, "metal", steel)
    a.lathe((x, g + 2.13, z), [(0.34, 0.0), (0.0, 0.02)], 12, "lens_glow", (1, 1, 1))
    sc.empty("searchlight_%d" % i, (x, g + 1.9, z))
    keep_clear(x, z, 1.5)


def build_searchlights(sc):
    for i, x, z in SEARCHLIGHTS:
        searchlight(sc, i, x, z)


rng_w = random.Random(61)


def main():
    sc = Scene()
    build_land(sc)
    build_searchlights(sc)
    build_post(sc)
    build_radar(sc)
    build_lighthouse(sc)
    build_harbour(sc)
    build_city(sc)
    far_ridges(sc)
    build_woods(sc)
    sc.export("night_coast.glb")
    write_paths("night_coast_paths.tres")


main()
