"""Nova Wardens (game 25) night backdrop: the last line of defence on a coastal hilltop, looking out over a sleeping
seaside city, its harbour and a calm sea. Original design: an invented, generic town (no real skyline, no real
landmark): terraced blocks, a harbour with cranes and a breakwater, a striped lighthouse on the left headland, a radar
station and searchlight batteries on the hills either side. Deterministic (fixed seeds); output CC BY-SA 4.0;
provenance: this script only, no third-party assets, no textures (vertex colours).
Run: blender -b --factory-startup -P tools/blender/novawardens_city.py -- godot/games/novawardens/art/backdrop

Coordinates: authored in Godot space (x right, y up, z towards the camera), converted on export.
The play field is x 0..11.2, y 0..12.8 on z = 0 (224 x 256 px at 0.05); the camera sits near (5.6, 5.8, 22), fov 36.
The crest the cannon stands on tops out at y = 0.95 for z -2..+3 (the game draws its ground line at y ~1.1). Behind
it the hill falls to a terrace (the city), then the harbour at sea level y = -12; the sea (drawn by the game as a disc
round the camera, see nova_backdrop.gd) ends at about 200 units, so the horizon lies near y = 3.8 on the play plane.
Nothing tall stands behind the middle of the field: the lighthouse, the radar and the lit hills are at the sides.

night_coast.glb holds
  fg_*          the crest and its sandbags (front, casts shadows)
  land          the terrain from the crest down to the shore and the headlands
  far_*         distant ridges and the far shore past the bay
  city_*        blocks (vertex colours), roofs, masts
  harbour_*     quays, piers, cranes, containers, the breakwater
  lh_*          the lighthouse and the keeper's cottage
  radar_*       the radar station (pylon, radome, hut)
and animated nodes, each with its origin at its pivot:
  beam              an empty at the lighthouse lantern (the game hangs the rotating beams there)
  dish_<i>          radar dishes (rotate about local Y)
  searchlight_<i>   empties at the searchlight lenses (the game adds the beams and aims them)
  boat_<i>          moored boats (bob)
Material names carry the game's hints: "*glow*" emissive (window_glow, coolwindow_glow, lamp_glow, blink_glow,
alarm_glow = the red air-raid lamps, lens_glow, lantern_glow, harbour_glow = the green and red harbour lights,
reflect_glow = light streaks lying on the water, UV.y running away from the light), "sea". All other colour is in the
vertex colours (COLOR_0, linear) over white materials.
"""
import bpy, math, os, sys, random
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "godot/games/novawardens/art/backdrop")

CAM = Vector((5.6, 5.8, 22.0))
TAN_W = 0.578   # half-width per unit of distance for fov 36 at 16:9
SL = -12.0      # sea level
CREST = 0.95


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


# ------------------------------------------------------------------ materials

MATS = {}
MAT_DEFS = {
    # name: (base colour, roughness, metallic, emission strength)
    "ground": ((1, 1, 1), 0.95, 0, 0),
    "rock": ((1, 1, 1), 0.85, 0, 0),
    "paint": ((1, 1, 1), 0.6, 0, 0),
    "metal": ((1, 1, 1), 0.4, 0.6, 0),
    "fabric": ((1, 1, 1), 0.95, 0, 0),
    "sea": ((1, 1, 1), 0.1, 0, 0),
    "window_glow": ((1.0, 0.72, 0.38), 0.4, 0, 2.5),
    "coolwindow_glow": ((0.7, 0.85, 1.0), 0.4, 0, 2.0),
    "lamp_glow": ((1.0, 0.66, 0.3), 0.4, 0, 3.0),
    "blink_glow": ((1.0, 0.12, 0.08), 0.4, 0, 5.0),
    "alarm_glow": ((1.0, 0.08, 0.05), 0.4, 0, 5.0),
    "lens_glow": ((0.85, 0.92, 1.0), 0.4, 0, 5.0),
    "lantern_glow": ((1.0, 0.9, 0.7), 0.4, 0, 5.0),
    "harbour_glow": ((1.0, 1.0, 1.0), 0.4, 0, 4.0),
    "reflect_glow": ((1.0, 0.7, 0.35), 1, 0, 1.2),
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

    def box(self, c, size, material, col, ry=0.0, taper=1.0, cols=None, bottom=True):
        """An axis box (turned by ry about Y); taper shrinks the top; cols: (top, sides) colours."""
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
        if bottom:
            self.face([pts[0], pts[1], pts[2], pts[3]], material, side, out=C)
        for i in range(4):
            j = (i + 1) % 4
            sc = side if not callable(side) else side(i)
            self.face([pts[i], pts[j], pts[4 + j], pts[4 + i]], material, sc, out=C)

    def lathe(self, c, prof, segs, material, col, sm=True, cap=True):
        """Revolves prof [(r, y)] (bottom to top) about a vertical axis at c. col: colour or fn(y) -> colour."""
        cx, cy, cz = c
        cf = col if callable(col) else (lambda y: col)
        rings = []
        for r, y in prof:
            rings.append([self.vert((cx + math.cos(2 * math.pi * j / segs) * r, cy + y,
                                     cz + math.sin(2 * math.pi * j / segs) * r)) for j in range(segs)])
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

    def tube(self, a, b, r, material, col, segs=5):
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
        for j in range(segs):
            k = (j + 1) % segs
            self.face([ra[j], ra[k], rb[k], rb[j]], material, col, out=m)

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
        uv = me.uv_layers.new(name="UVMap") if any(f[3] for f in self.f) else None
        for poly, f in zip(me.polygons, self.f):
            poly.material_index = names.index(f[1])
            poly.use_smooth = f[4]
            for k in range(poly.loop_total):
                ca.data[poly.loop_start + k].color = (*lin(f[2][k]), 1.0)
                if f[3] and uv:
                    uv.data[poly.loop_start + k].uv = f[3][k]
        me.color_attributes.active_color = ca
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (o.x, -o.z, o.y)
        return ob


class Scene:
    def __init__(self):
        self.accs = []
        self.empties = []

    def acc(self, name, origin=(0, 0, 0)):
        a = Acc(name, origin)
        self.accs.append(a)
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
        for a in sorted(self.accs, key=lambda a: -a.tris())[:10]:
            print("    %-20s %6d" % (a.name, a.tris()))
        return total


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


GRASS = hexc("#1d2a2c")
GRASS_LIT = hexc("#3a4c50")
EARTH = hexc("#27262e")
ROCK = hexc("#3a3a46")


def land_col(x, y, z, ny):
    c = mix(GRASS, GRASS_LIT, 0.5 + 0.5 * n2(x, z, 0.15, 1.0))
    c = mix(ROCK, c, smooth(0.55, 0.85, ny))
    c = mix(mul(hexc("#2a2e3a"), 0.9), c, smooth(SL - 0.5, SL + 1.5, y))
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


def build_land(sc):
    fg = sc.acc("fg_crest")
    terrain(fg, 9.0, -6.0, 8, 60, margin=1.2)
    land = sc.acc("land")
    terrain(land, -6.0, -210.0, 70, 90)
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
                fg.box((xx, y, -1.8), (0.66, 0.3, 0.45), "fabric", c, cols=(mul(c, 1.15), c), bottom=False)
            x += 0.7
    for x, s in ((-4.8, 1.0), (16.4, -1.0)):
        y = land_h(x, -3.0)
        fg.box((x, y + 0.6, -3.0), (2.6, 1.4, 2.2), "rock", hexc("#3c3e46"), taper=0.85,
               cols=(hexc("#4a4c56"), hexc("#34363e")), bottom=False)
        fg.box((x, y + 0.75, -1.88), (1.4, 0.16, 0.02), "lamp_glow", (1, 1, 1), bottom=False)


def far_ridges(sc):
    rng = random.Random(9)
    a = sc.acc("far_ridges")
    # low far hills left of the headland and far behind the right-hand hills, fogged into the horizon
    for (x0, x1, z, base, hh, seed, col) in ((-240.0, -60.0, -230.0, SL - 1, 26.0, 1.0, "#1a2034"),
                                             (60.0, 260.0, -260.0, SL - 1, 34.0, 2.0, "#18203a"),
                                             (-160.0, -40.0, -175.0, SL - 1, 12.0, 3.0, "#1c2436")):
        n = 60
        prev = None
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            e = smooth(x0, x0 + (x1 - x0) * 0.25, x) * (1 - smooth(x0 + (x1 - x0) * 0.7, x1, x))
            y = base + hh * e * (0.55 + 0.45 * fbm(x, z, 0.02, 3, seed))
            va = a.vert((x, base - 4, z))
            vb = a.vert((x, y, z))
            if prev:
                c = hexc(col)
                a.face([prev[0], va, vb, prev[1]], "rock", [c, c, mul(c, 1.25), mul(c, 1.25)], out=(x, y, z - 50))
            prev = (va, vb)
    # a few lights on the far shore
    for i in range(40):
        x = rng.uniform(55, 140)
        z = rng.uniform(-150, -130) - (x - 55) * 0.35
        y = land_h(x, z)
        if y < SL + 0.5:
            continue
        a.box((x, y + 0.3, z), (0.5, 0.5, 0.5), "lamp_glow" if rng.random() < 0.7 else "coolwindow_glow", (1, 1, 1),
              bottom=False)


# ------------------------------------------------------------------ the city

WALLS = [hexc(h) for h in ("#4a4a5c", "#55505a", "#3e4654", "#5a5660", "#48505a", "#524a50", "#3a3e4c")]
ROOFS = [hexc(h) for h in ("#2a2a36", "#34303a", "#26303a", "#3a3036")]


def py_limit(x, z):
    """The highest a roof may reach on the play plane (keeps the middle of the field clear)."""
    px = CAM.x + (x - CAM.x) * plane_factor(z)
    side = smooth(3.5, 9.0, abs(px - CAM.x))
    return 2.5 + 3.8 * side


def building(a, win, rng, x, z, w, d, h, ground, roofmat_extra=None):
    wall = rng.choice(WALLS)
    roof = rng.choice(ROOFS)
    top = ground + h
    kind = rng.random()
    taper = 1.0
    a.box((x, ground + h / 2 - 1.0, z), (w, h + 2.0, d), "paint", wall, cols=(roof, wall), bottom=False)
    if kind < 0.3:
        # a pitched roof
        ry = 0.0
        a.poly([(x - w / 2, top, z + d / 2), (x + w / 2, top, z + d / 2), (x + w / 2, top + d * 0.35, z),
                (x - w / 2, top + d * 0.35, z)], "paint", roof, out=(x, top - 5, z + d))
        a.poly([(x - w / 2, top, z - d / 2), (x + w / 2, top, z - d / 2), (x + w / 2, top + d * 0.35, z),
                (x - w / 2, top + d * 0.35, z)], "paint", mul(roof, 0.8), out=(x, top - 5, z - d))
        a.poly([(x - w / 2, top, z - d / 2), (x - w / 2, top, z + d / 2), (x - w / 2, top + d * 0.35, z)], "paint", wall,
               out=(x + 5, top, z))
        a.poly([(x + w / 2, top, z - d / 2), (x + w / 2, top, z + d / 2), (x + w / 2, top + d * 0.35, z)], "paint", wall,
               out=(x - 5, top, z))
    elif kind < 0.55:
        # a parapet and a water tank or a lift housing
        a.box((x + rng.uniform(-w, w) * 0.25, top + 0.5, z + rng.uniform(-d, d) * 0.2), (w * 0.3, 1.0, d * 0.3),
              "paint", mul(wall, 0.8), bottom=False)
    # windows: rows of floors on the front (facing the camera) and on the side facing the middle
    lit = rng.uniform(0.18, 0.5)
    cool = rng.uniform(0.0, 0.5)
    fh = 1.3
    y = ground + 0.9
    while y < top - 0.5:
        xx = x - w / 2 + 0.7
        while xx < x + w / 2 - 0.5:
            if rng.random() < lit:
                win.quad_facing((xx, y, z + d / 2 + 0.03), 0.5, 0.7,
                                "coolwindow_glow" if rng.random() < cool else "window_glow")
            xx += 1.05
        sx = x - w / 2 - 0.03 if x > CAM.x else x + w / 2 + 0.03
        zz = z - d / 2 + 0.7
        while zz < z + d / 2 - 0.5:
            if rng.random() < lit * 0.7:
                win.quad_facing((sx, y, zz), 0.5, 0.7, "window_glow", axis="x", sign=1 if x > CAM.x else -1)
            zz += 1.05
        y += fh
    return top


def build_city(sc):
    rng = random.Random(25)
    a = sc.acc("city_blocks")
    win = sc.acc("city_windows")
    lamps = sc.acc("city_lamps")
    masts = sc.acc("city_masts")
    tops = []
    z = -50.0
    row = 0
    while z > -88.0:
        x = -34.0 + (1.7 if row % 2 else 0.0)
        while x < 33.0:
            w = rng.uniform(3.0, 5.2)
            d = rng.uniform(3.0, 5.0)
            cx, cz = x + w / 2, z + rng.uniform(-0.6, 0.6)
            x += w + rng.uniform(0.4, 1.4)
            if rng.random() < 0.12:
                continue
            ground = min(land_h(cx - w / 2, cz), land_h(cx + w / 2, cz), land_h(cx, cz - d / 2), land_h(cx, cz + d / 2))
            if ground < SL + 1.2 or cz < shore_z(cx) + 6.0:
                continue
            # not on the steep hills: the base must be near the terrace's own slope
            if abs(land_h(cx, cz) - profile(cz / shore_z(cx))) > 2.5:
                continue
            lim_y = CAM.y + (py_limit(cx, cz) - CAM.y) / plane_factor(cz)
            hmax = lim_y - ground
            h = rng.uniform(3.0, 7.0)
            h = min(h, hmax)
            if h < 2.2:
                continue
            top = building(a, win, rng, cx, cz, w, d, h, ground)
            tops.append((cx, top, cz, h))
        # a street of sodium lamps in front of the row
        zz = z + 3.2
        xl = -34.0
        while xl < 33.0:
            g = land_h(xl, zz)
            if g > SL + 1.0 and zz > shore_z(xl) + 4:
                lamps.box((xl, g + 1.6, zz), (0.28, 0.28, 0.28), "lamp_glow", (1, 1, 1), bottom=False)
            xl += rng.uniform(3.2, 4.2)
        z -= rng.uniform(6.8, 8.0)
        row += 1
    # cottages scattered on the slope below the crest, left and right of the field
    for i in range(26):
        cx = rng.choice([rng.uniform(-34.0, -8.0), rng.uniform(18.0, 34.0)])
        cz = rng.uniform(-48.0, -14.0)
        g = land_h(cx, cz)
        if abs(g - profile(cz / shore_z(cx))) > 3.0:
            continue
        w, d = rng.uniform(2.2, 3.2), rng.uniform(2.0, 2.8)
        building(a, win, rng, cx, cz, w, d, rng.uniform(2.2, 3.4), g)
    # a winding road down the hill from the crest to the harbour, lit on both sides
    for i in range(70):
        t = i / 69.0
        zz = -8.0 - t * 80.0
        xx = 30.0 - 18.0 * t + 6.0 * math.sin(t * 7.0)
        for off in (-1.0, 1.0):
            g = land_h(xx + off, zz)
            if g > SL + 1.0:
                lamps.box((xx + off, g + 1.3, zz), (0.24, 0.24, 0.24), "lamp_glow", (1, 1, 1), bottom=False)
    # masts with blinking aviation lights on the tall roofs, and the air-raid lamps (the game makes them flash)
    tall = sorted(tops, key=lambda t: -t[3])
    for (cx, top, cz, h) in tall[:6]:
        masts.tube((cx, top, cz), (cx, top + 3.0, cz), 0.08, "metal", hexc("#2a2c34"))
        masts.box((cx, top + 3.1, cz), (0.3, 0.3, 0.3), "blink_glow", (1, 1, 1))
    for (cx, top, cz, h) in rng.sample(tops, min(22, len(tops))):
        masts.tube((cx, top, cz), (cx, top + 1.0, cz), 0.07, "metal", hexc("#2a2c34"))
        masts.blob((cx, top + 1.15, cz), (0.32, 0.26, 0.32), "alarm_glow", (1, 1, 1), segs=8, rings=4)


# ------------------------------------------------------------------ the harbour

def build_harbour(sc):
    rng = random.Random(40)
    q = sc.acc("harbour_quays")
    lights = sc.acc("harbour_lights")
    refl = sc.acc("harbour_reflections")
    stone = hexc("#4c4a54")
    # the quay along the bay
    for i in range(40):
        x0 = -20.0 + i * 1.8
        z0 = shore_z(x0 + 0.9)
        if z0 < -125:
            continue
        q.box((x0 + 0.9, SL + 0.5, z0 + 1.2), (1.85, 2.2, 4.0), "rock", mul(stone, rng.uniform(0.85, 1.05)),
              cols=(hexc("#5a5864"), stone), bottom=False)
    # piers out into the bay
    for px in (-6.0, 8.0, 22.0):
        z0 = shore_z(px)
        q.box((px, SL + 0.6, z0 - 8.0), (2.2, 1.4, 16.0), "rock", stone, cols=(hexc("#5a5864"), stone), bottom=False)
        for k in range(4):
            zz = z0 - 2.0 - k * 4.4
            q.tube((px + 1.0, SL + 1.3, zz), (px + 1.0, SL + 3.4, zz), 0.06, "metal", hexc("#2a2c34"))
            lights.box((px + 1.0, SL + 3.5, zz), (0.3, 0.3, 0.3), "lamp_glow", (1, 1, 1))
            refl.poly([(px + 0.8, SL + 0.03, zz + 0.4), (px + 1.2, SL + 0.03, zz + 0.4),
                       (px + 1.35, SL + 0.03, zz + 9.0), (px + 0.65, SL + 0.03, zz + 9.0)], "reflect_glow", (1, 1, 1),
                      uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], out=(px, SL - 5, zz))
    # container cranes on the right-hand quay, and stacks of containers
    crane = hexc("#5a4a44")
    for i, cx in enumerate((30.0, 37.0, 44.0)):
        z0 = shore_z(cx)
        base = SL + 1.6
        for lx in (-1.4, 1.4):
            for lz in (0.5, 4.5):
                q.tube((cx + lx, base, z0 + lz), (cx + lx, base + 9.0, z0 + lz), 0.18, "metal", crane)
        q.box((cx, base + 9.3, z0 + 1.0), (3.4, 0.6, 16.0), "metal", crane)
        q.box((cx, base + 10.6, z0 + 5.0), (1.6, 2.2, 1.6), "metal", mul(crane, 0.8))
        lights.box((cx, base + 11.9, z0 + 5.0), (0.35, 0.35, 0.35), "blink_glow", (1, 1, 1))
        lights.box((cx, base + 9.3, z0 - 7.0), (0.3, 0.3, 0.3), "blink_glow", (1, 1, 1))
        lights.box((cx - 1.2, base + 8.4, z0 + 2.5), (0.3, 0.3, 0.3), "lamp_glow", (1, 1, 1))
    cc = [hexc(h) for h in ("#7a3a30", "#2e4a6a", "#6a5a2a", "#3a5a4a", "#5a3a5a")]
    for i in range(34):
        cx = rng.uniform(27.0, 50.0)
        cz = rng.uniform(4.0, 12.0) + shore_z(cx)
        g = land_h(cx, cz)
        if g < SL + 0.8:
            continue
        stack = rng.randint(1, 3)
        for k in range(stack):
            c = rng.choice(cc)
            q.box((cx, g + 0.6 + k * 1.2, cz), (3.0, 1.2, 1.25), "metal", c, cols=(mul(c, 1.2), c), bottom=False)
    # the breakwater from the right-hand shore, with the harbour lights (green at the tip, red on the far pier)
    pts = [(58.0, -110.0), (46.0, -118.0), (34.0, -124.0), (22.0, -128.0), (14.0, -129.0)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        ry = math.atan2(-(z1 - z0), x1 - x0)
        q.box(((x0 + x1) / 2, SL + 0.4, (z0 + z1) / 2), (L + 0.6, 2.0, 2.4), "rock", hexc("#3e3e48"), ry=ry,
              cols=(hexc("#4e4c56"), hexc("#34343e")), bottom=False)
    tip = pts[-1]
    q.lathe((tip[0], SL + 1.4, tip[1]), [(0.5, 0), (0.4, 2.4), (0.0, 2.6)], 8, "paint", hexc("#3a6a4a"))
    lights.blob((tip[0], SL + 4.3, tip[1]), (0.4, 0.4, 0.4), "harbour_glow", (0.2, 1.0, 0.45), segs=8, rings=4)
    refl.poly([(tip[0] - 0.3, SL + 0.03, tip[1] + 1.5), (tip[0] + 0.3, SL + 0.03, tip[1] + 1.5),
               (tip[0] + 0.6, SL + 0.03, tip[1] + 16.0), (tip[0] - 0.6, SL + 0.03, tip[1] + 16.0)], "reflect_glow",
              (0.3, 1.0, 0.5), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], out=(tip[0], SL - 5, tip[1]))
    rp = (-6.0, shore_z(-6.0) - 16.5)
    q.lathe((rp[0], SL + 1.3, rp[1]), [(0.45, 0), (0.35, 2.0), (0.0, 2.2)], 8, "paint", hexc("#6a3a3a"))
    lights.blob((rp[0], SL + 3.8, rp[1]), (0.38, 0.38, 0.38), "harbour_glow", (1.0, 0.2, 0.15), segs=8, rings=4)
    # moored boats with a cabin light each
    for i, (bx, bz) in enumerate(((2.5, -100.0), (13.0, -103.0), (16.5, -98.0), (-1.0, -97.0), (26.0, -102.0),
                                  (-12.0, -100.0))):
        b = sc.acc("boat_%d" % i, (bx, SL, bz))
        L = rng.uniform(3.0, 5.0)
        hull = rng.choice([hexc("#c8c4bc"), hexc("#3a4a6a"), hexc("#7a3a34")])
        b.box((bx, SL + 0.35, bz), (0.5 * L, 0.7, 1.3), "paint", hull, taper=1.15, cols=(hexc("#6a6258"), hull))
        b.box((bx - 0.2, SL + 1.0, bz), (0.45 * L * 0.5, 0.7, 0.9), "paint", hexc("#d8d4cc"))
        b.quad_facing((bx - 0.2, SL + 1.05, bz + 0.46), 0.5, 0.3, "window_glow")
        b.tube((bx + 0.2, SL + 0.7, bz), (bx + 0.2, SL + 3.2, bz), 0.04, "metal", hexc("#8a8a90"))
        b.box((bx + 0.2, SL + 3.25, bz), (0.15, 0.15, 0.15), "lamp_glow", (1, 1, 1))


# ------------------------------------------------------------------ landmarks

def build_lighthouse(sc):
    x, z = -30.0, -88.0
    g = land_h(x, z)
    a = sc.acc("lh_tower")
    white, red = hexc("#dcd8d0"), hexc("#b0343a")
    H = 15.0

    def band(y):
        return red if int(y / (H / 5.0)) % 2 == 1 else white
    # the tower in bands (each ring's colour by its height)
    rings = [(1.8 - 0.75 * t / 20.0, H * t / 20.0) for t in range(21)]
    for i in range(20):
        c = band((rings[i][1] + rings[i + 1][1]) / 2)
        a.lathe((x, g, z), [rings[i], rings[i + 1]], 16, "paint", c, cap=False)
    a.lathe((x, g + H, z), [(1.6, 0.0), (1.6, 0.25), (0.9, 0.25)], 16, "metal", hexc("#2a2c34"), cap=False)
    a.lathe((x, g + H + 0.25, z), [(0.85, 0.0), (0.85, 1.7)], 12, "lantern_glow", (1, 1, 1), cap=False)
    a.lathe((x, g + H + 1.95, z), [(1.05, 0.0), (0.6, 0.6), (0.1, 1.2), (0.0, 1.5)], 12, "metal", hexc("#2a2c34"))
    sc.empty("beam", (x, g + H + 1.1, z))
    # the keeper's cottage with a lit window
    c = sc.acc("lh_cottage")
    c.box((x + 4.5, g + 1.2, z + 1.5), (5.0, 2.4, 3.2), "paint", hexc("#c8c4bc"), cols=(hexc("#5a3a34"), hexc("#b8b4ac")),
          bottom=False)
    c.quad_facing((x + 3.5, g + 1.3, z + 3.13), 0.7, 0.8, "window_glow")
    c.quad_facing((x + 5.6, g + 1.3, z + 3.13), 0.7, 0.8, "window_glow")
    # a line of posts with lamps down to the landing
    for k in range(6):
        px = x + 6 + k * 3.0
        pz = z + 5 + k * 2.0
        c.box((px, land_h(px, pz) + 0.8, pz), (0.22, 0.22, 0.22), "lamp_glow", (1, 1, 1), bottom=False)


def dish(sc, name, c, r, tilt, pylon_h, col):
    """A radar dish on a turntable: its node's origin is the turntable (rotate about local Y)."""
    x, y, z = c
    d = sc.acc(name, (x, y + pylon_h, z))
    # the dish: a shallow paraboloid facing +z, tilted up by `tilt`
    rings, segs = 5, 18
    ca, sa = math.cos(tilt), math.sin(tilt)
    centre = Vector((x, y + pylon_h + r * 0.9, z))

    def P(rr, a):
        lx, ly = math.cos(a) * rr, math.sin(a) * rr
        lz = (rr * rr) / (4.0 * r * 0.6)  # depth of the bowl
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
            d.face(ids, "paint", [mul(col, 0.8 + 0.2 * (i + (q > 1)) / rings) for q in range(4)], sm=True)
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
    dish(sc, "dish_0", (x, g, z), 2.6, 0.45, ph + 0.15, hexc("#b8bcc4"))
    p.blob((x - 5.5, g + 0.6, z - 2.0), (2.1, 2.3, 2.1), "paint", hexc("#c8ccd4"), segs=14, rings=7, cut=-0.3)
    p.box((x + 4.0, land_h(x + 4, z + 1.5) + 0.9, z + 1.5), (3.6, 2.0, 2.4), "paint", hexc("#5a5e56"),
          cols=(hexc("#3a3e3a"), hexc("#5a5e56")), bottom=False)
    for k in range(3):
        p.quad_facing((x + 2.9 + k * 1.1, land_h(x + 4, z + 1.5) + 1.1, z + 2.73), 0.6, 0.5, "coolwindow_glow")
    mx = x - 2.0
    p.tube((mx, g - 0.5, z - 5.0), (mx, g + 11.0, z - 5.0), 0.08, "metal", steel)
    p.box((mx, g + 11.1, z - 5.0), (0.3, 0.3, 0.3), "blink_glow", (1, 1, 1))
    p.box((mx, g + 7.0, z - 5.0), (0.25, 0.25, 0.25), "blink_glow", (1, 1, 1))
    # the small dish on the right knoll
    x2, z2 = 23.0, -11.5
    g2 = land_h(x2, z2)
    p.tube((x2, g2 - 0.5, z2), (x2, g2 + 1.6, z2), 0.2, "metal", steel)
    dish(sc, "dish_1", (x2, g2, z2), 1.2, 0.7, 1.6, hexc("#aab0ba"))


def searchlight(sc, i, x, z, aim_yaw):
    g = land_h(x, z)
    a = sc.acc("searchlight_mount_%d" % i)
    steel = hexc("#34363e")
    a.box((x, g + 0.25, z), (1.4, 0.5, 1.4), "rock", hexc("#44444c"), bottom=False)
    for s in (-1, 1):
        a.tube((x + s * 0.5, g + 0.5, z), (x + s * 0.5, g + 1.6, z), 0.07, "metal", steel)
    a.lathe((x, g + 1.2, z), [(0.55, 0.0), (0.6, 0.9), (0.0, 0.92)], 12, "metal", steel)
    a.lathe((x, g + 2.13, z), [(0.34, 0.0), (0.0, 0.02)], 12, "lens_glow", (1, 1, 1))
    sc.empty("searchlight_%d" % i, (x, g + 1.9, z))


def build_searchlights(sc):
    searchlight(sc, 0, -8.0, -9.0, 0.3)
    searchlight(sc, 1, -19.0, -24.0, 0.5)
    searchlight(sc, 2, 20.2, -7.5, -0.3)
    searchlight(sc, 3, 24.5, -12.0, -0.4)
    searchlight(sc, 4, 50.0, -85.0, -0.5)
    searchlight(sc, 5, -26.0, -60.0, 0.4)


def main():
    sc = Scene()
    build_land(sc)
    far_ridges(sc)
    build_city(sc)
    build_harbour(sc)
    build_lighthouse(sc)
    build_radar(sc)
    build_searchlights(sc)
    sc.export("night_coast.glb")


main()
