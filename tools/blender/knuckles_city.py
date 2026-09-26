"""Neon Knuckles city kit: street buildings with real facades (recessed sash windows with lit rooms, blinds and
curtains, sills and lintels, cornices, fire escapes, drainpipes, shop fronts with glass, a lit interior, shelves and
a neon sign in glass tubes), parked cars, street furniture (hydrant, bin, dumpster, parking meter, sign post,
manhole), the docks (containers with doors and lettering, bollards, rope, a floodlight, a moored freighter, a
harbour crane) and the rooftops (water tower, AC unit, vents, antenna, satellite dish, stair hut, a billboard).

Blender: X runs along the street, -Y faces the camera, Z up (Godot: +Z towards the camera). Materials named
"brick", "glass", "neon", "neon2", "shop_glow", "awning_a" and "awning_b" are replaced in the game (tint per
building); the others are final. The sign lettering uses Kenney Future (CC0, godot/core/fonts). Shop names are
invented. Deterministic; output CC BY-SA 4.0; provenance: this script.
Run: blender -b --factory-startup -P tools/blender/knuckles_city.py -- godot/games/knuckles/art/models
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Matrix, Euler, Vector

out_dir = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
os.makedirs(out_dir, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(here, "..", "..", "godot", "core", "fonts", "kenney_future.ttf")
MATS = {}


def mat(name, color, rough=0.6, metal=0.0, emit=0.0, coat=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    MATS[name] = m
    return m


def M():
    """The shared palette (created once per scene reset)."""
    return {
        "brick": mat("brick", (0.45, 0.22, 0.16), 0.85),
        "stone": mat("stone", (0.52, 0.5, 0.47), 0.8),
        "trim": mat("trim", (0.12, 0.2, 0.18), 0.45, coat=0.3),
        "trim_cream": mat("trim_cream", (0.7, 0.66, 0.55), 0.45, coat=0.3),
        "trim_dark": mat("trim_dark", (0.04, 0.04, 0.045), 0.35, 0.7),
        "glass": mat("glass", (0.05, 0.06, 0.08), 0.05, alpha=0.3),
        "room_warm": mat("room_warm", (1.0, 0.6, 0.3), 0.8, emit=2.2),
        "room_side": mat("room_side", (0.9, 0.55, 0.3), 0.8, emit=0.55),
        "room_cool": mat("room_cool", (0.45, 0.6, 1.0), 0.8, emit=1.6),
        "room_cool_side": mat("room_cool_side", (0.35, 0.45, 0.8), 0.8, emit=0.4),
        "room_dark": mat("room_dark", (0.025, 0.025, 0.035), 0.9),
        "blind": mat("blind", (1.0, 0.82, 0.55), 0.7, emit=1.3),
        "slat": mat("slat", (0.25, 0.16, 0.08), 0.7),
        "curtain_red": mat("curtain_red", (0.75, 0.12, 0.14), 0.9, emit=0.5),
        "curtain_teal": mat("curtain_teal", (0.1, 0.5, 0.48), 0.9, emit=0.35),
        "silhouette": mat("silhouette", (0.02, 0.015, 0.015), 0.9),
        "bulb": mat("bulb", (1.0, 0.85, 0.6), 0.3, emit=8.0),
        "tv": mat("tv", (0.4, 0.7, 1.0), 0.3, emit=4.0),
        "sign_board": mat("sign_board", (0.03, 0.03, 0.04), 0.35, 0.5),
        "neon": mat("neon", (1.0, 1.0, 1.0), 0.3, emit=6.0),
        "neon2": mat("neon2", (1.0, 1.0, 1.0), 0.3, emit=6.0),
        "shop_glow": mat("shop_glow", (1.0, 0.9, 0.8), 0.8, emit=1.6),
        "shop_floor": mat("shop_floor", (0.3, 0.27, 0.24), 0.3),
        "shop_ceiling": mat("shop_ceiling", (0.12, 0.11, 0.1), 0.9),
        "goods_a": mat("goods_a", (0.9, 0.3, 0.25), 0.6, emit=0.25),
        "goods_b": mat("goods_b", (0.95, 0.85, 0.3), 0.6, emit=0.25),
        "goods_c": mat("goods_c", (0.3, 0.6, 0.95), 0.6, emit=0.25),
        "goods_d": mat("goods_d", (0.95, 0.95, 0.9), 0.6, emit=0.25),
        "counter": mat("counter", (0.28, 0.13, 0.06), 0.4, coat=0.5),
        "tile": mat("tile", (0.04, 0.1, 0.08), 0.15, coat=0.8),
        "iron": mat("iron", (0.06, 0.06, 0.07), 0.5, 0.7),
        "pipe": mat("pipe", (0.12, 0.15, 0.13), 0.5, 0.4),
        "ac": mat("ac", (0.55, 0.57, 0.55), 0.55, 0.3),
        "awning_a": mat("awning_a", (0.6, 0.1, 0.1), 0.85),
        "awning_b": mat("awning_b", (0.85, 0.82, 0.75), 0.85),
        "shutter": mat("shutter", (0.35, 0.36, 0.38), 0.5, 0.6),
    }


class MB:
    """Builds one mesh from many primitives with bmesh (fast, and one object per model)."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def _idx(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _tag(self, verts, m, smooth):
        i = self._idx(m)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i
            f.smooth = smooth

    def box(self, c, s, m, rot=(0, 0, 0)):
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=Matrix.LocRotScale(Vector(c), Euler(rot), Vector(s)))
        self._tag(r["verts"], m, False)

    def span(self, lo, hi, m):
        """A box between two corners."""
        self.box([(a + b) * 0.5 for a, b in zip(lo, hi)], [abs(b - a) for a, b in zip(lo, hi)], m)

    def cyl(self, r, depth, c, m, rot=(0, 0, 0), r2=None, segs=16, smooth=True):
        mx = Matrix.LocRotScale(Vector(c), Euler(rot), Vector((1, 1, 1)))
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                                  radius2=r if r2 is None else r2, depth=depth, matrix=mx)
        self._tag(v["verts"], m, smooth)

    def sphere(self, r, c, m, scale=(1, 1, 1), segs=12, rings=8):
        mx = Matrix.LocRotScale(Vector(c), Euler((0, 0, 0)), Vector(scale))
        v = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r, matrix=mx)
        self._tag(v["verts"], m, True)

    def rod(self, a, b, r, m, segs=8):
        """A cylinder from point a to point b."""
        a, b = Vector(a), Vector(b)
        d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        mx = Matrix.LocRotScale((a + b) * 0.5, q, Vector((1, 1, 1)))
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r,
                                  depth=d.length, matrix=mx)
        self._tag(v["verts"], m, True)

    def torus(self, R, r, c, m, rot=(0, 0, 0), segs=20, ring=8):
        """A ring (rope coils, tyres, neon circles)."""
        mx = Matrix.LocRotScale(Vector(c), Euler(rot), Vector((1, 1, 1)))
        grid = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            row = []
            for j in range(ring):
                b = 2 * math.pi * j / ring
                p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
                row.append(self.bm.verts.new(mx @ p))
            grid.append(row)
        faces = []
        for i in range(segs):
            for j in range(ring):
                i2, j2 = (i + 1) % segs, (j + 1) % ring
                faces.append(self.bm.faces.new((grid[i][j], grid[i2][j], grid[i2][j2], grid[i][j2])))
        idx = self._idx(m)
        for f in faces:
            f.material_index = idx
            f.smooth = True

    def prism(self, pts, y0, y1, m):
        """A side profile [(x, z)] extruded along Y from y0 to y1 (car bodies, roofs)."""
        bot = [self.bm.verts.new((x, y0, z)) for x, z in pts]
        top = [self.bm.verts.new((x, y1, z)) for x, z in pts]
        faces = [self.bm.faces.new(bot), self.bm.faces.new(list(reversed(top)))]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new((bot[i], bot[j], top[j], top[i])))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        idx = self._idx(m)
        for f in faces:
            f.material_index = idx

    def obj(self, name, bevel=0.0):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        for m in self.mats:
            me.materials.append(m)
        if bevel:
            select(o)
            b = o.modifiers.new("b", "BEVEL")
            b.width = bevel
            b.segments = 2
            b.limit_method = "ANGLE"
            bpy.ops.object.modifier_apply(modifier=b.name)
        return o


def select(o):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


FONT = None


def text(body, size, loc, m, rot=(math.pi / 2, 0, 0), tube=0.018, max_w=None, fill=False, extrude=0.0, spacing=1.08):
    """Glowing glass tubes along the letter outlines (neon), or flat painted letters (fill=True)."""
    global FONT
    if FONT is None:
        FONT = bpy.data.fonts.load(FONT_PATH)
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.data.body = body
    o.data.font = FONT
    o.data.size = size
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    o.data.space_character = spacing
    o.data.resolution_u = 4
    if fill:
        o.data.fill_mode = "BOTH"
        o.data.extrude = extrude
    else:
        o.data.fill_mode = "NONE"
        o.data.bevel_depth = tube
        o.data.bevel_resolution = 1
    bpy.context.view_layer.update()
    if max_w and o.dimensions.x > max_w:
        k = max_w / o.dimensions.x
        o.scale = (k, k, k)
    select(o)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    o.data.materials.clear()
    o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def export(objs, name):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    # merge the materials that came in twice (text objects bring their own slot)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True,
                              export_format="GLB", export_yup=True, export_apply=True)
    print("exported", name, len(o.data.vertices), "verts")
    reset()


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)


def neon_frame(mb, x0, x1, z0, z1, y, m, r=0.02):
    """A rounded rectangle of neon tube."""
    k = 0.12
    mb.rod((x0 + k, y, z0), (x1 - k, y, z0), r, m, 6)
    mb.rod((x0 + k, y, z1), (x1 - k, y, z1), r, m, 6)
    mb.rod((x0, y, z0 + k), (x0, y, z1 - k), r, m, 6)
    mb.rod((x1, y, z0 + k), (x1, y, z1 - k), r, m, 6)
    for cx, cz, a0 in ((x1 - k, z1 - k, 0), (x0 + k, z1 - k, 90), (x0 + k, z0 + k, 180), (x1 - k, z0 + k, 270)):
        for s in range(3):  # quarter circle corners, three short rods each
            a = math.radians(a0 + s * 30)
            b = math.radians(a0 + s * 30 + 30)
            mb.rod((cx + k * math.cos(a), y, cz + k * math.sin(a)), (cx + k * math.cos(b), y, cz + k * math.sin(b)), r, m, 6)


# ---------------------------------------------------------------------------------------------- buildings

BAY, GF, FH = 2.5, 4.0, 3.2


def window(mb, P, rnd, cx, z0, style, trim):
    """One upper-floor window in the opening [cx - 0.62, cx + 0.62] x [z0 + 0.8, z0 + 2.6]: frame, glass, the room
    behind (lit or dark) with blinds, curtains or a lamp, the sill and the lintel."""
    ww, zb, zt = 0.62, z0 + 0.8, z0 + 2.6
    x0, x1 = cx - ww, cx + ww
    roll = rnd.random()
    lit = "warm" if roll < 0.45 else ("cool" if roll < 0.58 else "dark")
    back = {"warm": P["room_warm"], "cool": P["room_cool"], "dark": P["room_dark"]}[lit]
    side = {"warm": P["room_side"], "cool": P["room_cool_side"], "dark": P["room_dark"]}[lit]
    # the room: back wall, liner walls, floor and ceiling
    mb.span((x0 - 0.3, 1.45, zb - 0.9), (x1 + 0.3, 1.55, zt + 0.3), back)
    mb.span((x0, 0.25, zb - 0.02), (x0 + 0.02, 1.45, zt), side)
    mb.span((x1 - 0.02, 0.25, zb - 0.02), (x1, 1.45, zt), side)
    mb.span((x0, 0.25, zt - 0.02), (x1, 1.45, zt), side)
    mb.span((x0, 0.25, zb - 0.02), (x1, 1.45, zb), P["room_dark"])
    if lit != "dark":
        # something in the room: a hanging lamp, a shelf, a plant or a TV glow
        what = rnd.random()
        if what < 0.35:
            mb.rod((cx + rnd.uniform(-0.3, 0.3), 1.0, zt), (cx, 1.0, zt - 0.45), 0.006, P["silhouette"], 4)
            mb.cyl(0.13, 0.12, (cx, 1.0, zt - 0.5), P["silhouette"], r2=0.04, segs=10)
            mb.sphere(0.04, (cx, 1.0, zt - 0.56), P["bulb"])
        elif what < 0.6:
            mb.span((x0 + 0.1, 1.2, zb), (x0 + 0.5, 1.4, zb + 1.3), P["silhouette"])
            for k in range(3):
                mb.span((x0 + 0.12, 1.15, zb + 0.35 + k * 0.4), (x0 + 0.48, 1.4, zb + 0.38 + k * 0.4), P["slat"])
        elif what < 0.8:
            mb.cyl(0.1, 0.3, (x1 - 0.25, 1.0, zb + 0.15), P["silhouette"], r2=0.12, segs=8)
            mb.sphere(0.24, (x1 - 0.25, 1.0, zb + 0.55), P["silhouette"], (1, 1, 1.3))
        else:
            mb.span((cx - 0.3, 1.3, zb + 0.1), (cx + 0.3, 1.42, zb + 0.5), P["tv"])
        dress = rnd.random()
        if dress < 0.45:  # a blind half down, glowing with the room behind it
            bottom = rnd.uniform(zb + 0.5, zt - 0.4)
            mb.span((x0 + 0.04, 0.3, bottom), (x1 - 0.04, 0.32, zt - 0.05), P["blind"])
            z = bottom
            while z < zt - 0.1:
                mb.span((x0 + 0.04, 0.29, z), (x1 - 0.04, 0.295, z + 0.012), P["slat"])
                z += 0.07
            mb.span((x0 + 0.04, 0.28, bottom - 0.03), (x1 - 0.04, 0.33, bottom + 0.01), P["slat"])
        elif dress < 0.8:  # curtains drawn to the sides
            c = P["curtain_red"] if rnd.random() < 0.5 else P["curtain_teal"]
            for s in (-1, 1):
                ex = x0 + 0.04 if s < 0 else x1 - 0.04
                w = rnd.uniform(0.18, 0.3)
                mb.span((ex if s < 0 else ex - w, 0.32, zb + 0.05), (ex + w if s < 0 else ex, 0.4, zt - 0.05), c)
            mb.span((x0, 0.3, zt - 0.08), (x1, 0.42, zt - 0.03), P["slat"])  # the rail
    else:
        if rnd.random() < 0.5:  # a closed blind in a dark room
            mb.span((x0 + 0.04, 0.3, zb + rnd.uniform(0.3, 1.2)), (x1 - 0.04, 0.32, zt - 0.05), P["slat"])
    # glass and the frame (a sash window: two panes, meeting rail; or a six-pane grid)
    mb.span((x0, 0.2, zb), (x1, 0.215, zt), P["glass"])
    f = 0.07
    mb.span((x0, 0.12, zb), (x0 + f, 0.26, zt), trim)
    mb.span((x1 - f, 0.12, zb), (x1, 0.26, zt), trim)
    mb.span((x0, 0.12, zt - f), (x1, 0.26, zt), trim)
    mb.span((x0, 0.12, zb), (x1, 0.26, zb + f), trim)
    mid = (zb + zt) * 0.5
    mb.span((x0, 0.14, mid - 0.035), (x1, 0.24, mid + 0.035), trim)
    if style == "grid":
        mb.span((cx - 0.025, 0.15, zb), (cx + 0.025, 0.23, zt), trim)
        for zz in (zb + (zt - zb) / 4, zb + 3 * (zt - zb) / 4):
            mb.span((x0, 0.15, zz - 0.02), (x1, 0.23, zz + 0.02), trim)
    else:
        mb.span((cx - 0.02, 0.15, mid), (cx + 0.02, 0.23, zt), trim)
    # sill and lintel in stone
    mb.span((x0 - 0.12, -0.12, zb - 0.1), (x1 + 0.12, 0.2, zb), P["stone"])
    mb.span((x0 - 0.1, -0.06, zb - 0.16), (x0 + 0.02, 0.0, zb - 0.1), P["stone"])
    mb.span((x1 - 0.02, -0.06, zb - 0.16), (x1 + 0.1, 0.0, zb - 0.1), P["stone"])
    if style == "arch":
        for k in range(7):  # a segmental arch of voussoirs
            a = math.radians(160 - k * 23.3)
            mb.box((cx + 0.78 * math.cos(a), -0.03, zt - 0.05 + 0.22 * math.sin(a)), (0.2, 0.12, 0.28), P["stone"], (0, -a + math.pi / 2, 0))
    else:
        mb.span((x0 - 0.1, -0.05, zt), (x1 + 0.1, 0.12, zt + 0.26), P["stone"])
        mb.box((cx, -0.08, zt + 0.12), (0.2, 0.08, 0.3), P["stone"])  # keystone
    return lit


def building(name, bays, floors, sign, rnd, style="sash", awning=False, fire_escape=False, blade=None, trim_key="trim",
             ac=True):
    reset()
    P = M()
    trim = P[trim_key]
    W = bays * BAY
    D = 3.6
    x0, x1 = -W / 2, W / 2
    top = GF + floors * FH
    mb = MB()
    # ---- ground floor: pilasters, fascia, the shop front
    pw = 0.4
    for a, b in ((x0, x0 + pw), (x1 - pw, x1)):
        mb.span((a, 0.0, 0.0), (b, D, GF), P["brick"])
        mb.span((a - 0.03, -0.05, 0.0), (b + 0.03, 0.2, 0.45), P["stone"])  # plinth
        mb.span((a - 0.05, -0.08, 2.9), (b + 0.05, 0.2, 3.05), P["stone"])  # capital
    mb.span((x0, 0.0, 3.), (x1, 0.45, GF), P["sign_board"])  # fascia
    mb.span((x0 - 0.05, -0.2, GF - 0.02), (x1 + 0.05, 0.3, GF + 0.18), P["stone"])  # cornice over the shop
    sx0, sx1 = x0 + pw, x1 - pw
    door_left = rnd.random() < 0.5
    dw = 1.1
    dx0, dx1 = (sx0, sx0 + dw) if door_left else (sx1 - dw, sx1)
    gx0, gx1 = (dx1, sx1) if door_left else (sx0, dx0)
    # interior: floor, ceiling, glowing back wall, shelves with goods, a counter, pendant lamps
    mb.span((sx0, 0.4, 0.0), (sx1, D - 0.3, 0.3), P["shop_floor"])
    mb.span((sx0, 0.45, 2.95), (sx1, D - 0.3, 3.05), P["shop_ceiling"])
    mb.span((sx0, D - 0.35, 0.0), (sx1, D - 0.2, 3.05), P["shop_glow"])
    goods = [P["goods_a"], P["goods_b"], P["goods_c"], P["goods_d"]]
    for k in range(3):
        z = 1.0 + k * 0.62
        mb.span((sx0 + 0.2, D - 0.85, z - 0.04), (sx1 - 0.2, D - 0.35, z), P["counter"])
        x = sx0 + 0.25
        while x < sx1 - 0.35:
            w = rnd.uniform(0.12, 0.3)
            h = rnd.uniform(0.18, 0.45)
            mb.span((x, D - 0.75, z), (x + w, D - 0.45, z + h), goods[rnd.randrange(4)])
            x += w + rnd.uniform(0.03, 0.12)
    cx0 = gx0 + 0.4
    mb.span((cx0, 1.6, 0.3), (min(cx0 + 2.4, gx1 - 0.3), 2.2, 1.3), P["counter"])
    mb.span((cx0 + 0.3, 1.75, 1.3), (cx0 + 0.7, 2.05, 1.55), P["trim_dark"])  # the till
    x = gx0 + 0.7
    while x < gx1 - 0.5:
        mb.rod((x, 1.2, 2.95), (x, 1.2, 2.45), 0.008, P["iron"], 4)
        mb.cyl(0.18, 0.2, (x, 1.2, 2.38), P["iron"], r2=0.05, segs=12)
        mb.sphere(0.06, (x, 1.2, 2.28), P["bulb"])
        x += 1.6
    # the shop window: stall riser in glazed tiles, glass, a slim frame with a transom
    mb.span((gx0, 0.3, 0.0), (gx1, 0.55, 0.55), P["tile"])
    mb.span((gx0, 0.42, 0.55), (gx1, 0.44, 2.95), P["glass"])
    mb.span((gx0, 0.36, 0.55), (gx1, 0.5, 0.62), P["trim_dark"])
    mb.span((gx0, 0.36, 2.22), (gx1, 0.5, 2.3), P["trim_dark"])
    mb.span((gx0, 0.36, 2.9), (gx1, 0.5, 3.), P["trim_dark"])
    n = max(2, round((gx1 - gx0) / 1.6))
    for k in range(n + 1):
        x = gx0 + (gx1 - gx0) * k / n
        mb.span((x - 0.04, 0.36, 0.55), (x + 0.04, 0.5, 3.), P["trim_dark"])
    # the door, set back in a tiled porch, with a glass panel
    mb.span((dx0, 0.0, 0.0), (dx1, 1.2, 0.05), P["tile"])
    mb.span((dx0 + 0.1, 1.15, 0.0), (dx1 - 0.1, 1.25, 2.2), P["trim"])
    mb.span((dx0 + 0.25, 1.1, 0.9), (dx1 - 0.25, 1.15, 2.0), P["shop_glow"])
    mb.span((dx0 + 0.1, 1.1, 2.2), (dx1 - 0.1, 1.25, 3.), P["glass"])
    mb.span((dx0, 0.3, 0.0), (dx0 + 0.06, 1.2, 3.), P["tile"])
    mb.span((dx1 - 0.06, 0.3, 0.0), (dx1, 1.2, 3.), P["tile"])
    mb.sphere(0.05, ((dx0 + dx1) * 0.5, 0.9, 2.9), P["bulb"])
    # a small neon in the shop window: OPEN in a ring
    ox = gx1 - 0.9 if door_left else gx0 + 0.9
    mbn = MB()
    mbn.torus(0.34, 0.015, (ox, 0.6, 2.0), P["neon2"], rot=(math.pi / 2, 0, 0), segs=24, ring=6)
    extra = [text("OPEN", 0.16, (ox, 0.6, 2.0), P["neon2"], tube=0.01, max_w=0.52)]
    # awning or a rolled-up shutter over the glass
    if awning:
        depth, z_hi, z_lo = 1.2, 2.98, 2.55
        slope = math.atan2(z_hi - z_lo, depth)
        k, x = 0, sx0
        while x < sx1 - 0.01:
            w = min(0.42, sx1 - x)
            m = P["awning_a"] if k % 2 == 0 else P["awning_b"]
            mb.box((x + w / 2, -depth / 2 + 0.1, (z_hi + z_lo) / 2), (w, math.hypot(depth, z_hi - z_lo), 0.03), m, (-slope, 0, 0))
            mb.span((x, -depth + 0.07, z_lo - 0.28), (x + w, -depth + 0.1, z_lo), m)  # valance
            x += w
            k += 1
        for ax in (sx0 + 0.1, sx1 - 0.1):
            mb.rod((ax, 0.1, z_lo - 0.5), (ax, -depth + 0.1, z_lo), 0.018, P["iron"])
    else:
        mb.span((sx0, -0.1, 2.7), (sx1, 0.35, 2.98), P["shutter"])
        for k in range(4):
            mb.span((sx0, -0.12, 2.73 + k * 0.065), (sx1, -0.1, 2.75 + k * 0.065), P["iron"])
    # the fascia sign: neon letters in a tube frame, with the board's rim
    fx0, fx1 = x0 + pw + 0.2, x1 - pw - 0.2
    neon_frame(mbn, fx0, fx1, 3.12, GF - 0.1, -0.03, P["neon2"], 0.018)
    extra.append(text(sign, 0.5, ((fx0 + fx1) / 2, -0.04, (3.12 + GF - 0.1) / 2), P["neon"], tube=0.022, max_w=fx1 - fx0 - 0.5))
    # ---- upper floors: spandrels, piers, windows
    kinds = []
    for f in range(floors):
        z0 = GF + f * FH
        mb.span((x0, 0.0, z0), (x1, 1.6, z0 + 0.8), P["brick"])
        mb.span((x0, 0.0, z0 + 2.6), (x1, 1.6, z0 + FH), P["brick"])
        xs = [x0 + (i + 0.5) * BAY for i in range(bays)]
        edges = [x0] + [v for x in xs for v in (x - 0.62, x + 0.62)] + [x1]
        for i in range(0, len(edges), 2):
            mb.span((edges[i], 0.0, z0 + 0.8), (edges[i + 1], 1.6, z0 + 2.6), P["brick"])
        if f > 0:
            mb.span((x0, -0.06, z0 - 0.04), (x1, 0.0, z0 + 0.1), P["stone"])  # string course
        for i, x in enumerate(xs):
            kinds.append(window(mb, P, rnd, x, z0, style, trim))
            if ac and rnd.random() < 0.18 and not (fire_escape and i < 2):
                mb.span((x - 0.32, -0.42, z0 + 0.45), (x + 0.32, 0.0, z0 + 0.82), P["ac"])
                for g in range(5):
                    mb.span((x - 0.28, -0.43, z0 + 0.5 + g * 0.06), (x + 0.28, -0.42, z0 + 0.52 + g * 0.06), P["iron"])
                mb.rod((x - 0.25, 0.0, z0 + 0.2), (x - 0.25, -0.4, z0 + 0.45), 0.012, P["iron"], 4)
                mb.rod((x + 0.25, 0.0, z0 + 0.2), (x + 0.25, -0.4, z0 + 0.45), 0.012, P["iron"], 4)
    mb.span((x0, 1.55, GF), (x1, D, top), P["brick"])  # the mass behind the rooms
    # ---- the cornice and the parapet
    mb.span((x0, -0.12, top), (x1, 0.3, top + 0.2), P["stone"])
    mb.span((x0, -0.36, top + 0.2), (x1, 0.3, top + 0.42), P["stone"])
    x = x0 + 0.1
    while x < x1 - 0.1:
        mb.span((x, -0.2, top + 0.06), (x + 0.1, 0.0, top + 0.2), P["stone"])  # dentils
        x += 0.28
    mb.span((x0, 0.0, top + 0.42), (x1, 0.4, top + 1.1), P["brick"])
    mb.span((x0 - 0.02, -0.05, top + 1.1), (x1 + 0.02, 0.45, top + 1.2), P["stone"])
    # ---- a drainpipe down one side
    px = x0 + 0.2 if rnd.random() < 0.5 else x1 - 0.2
    mb.cyl(0.065, top + 0.2, (px, -0.14, (top + 0.2) / 2), P["pipe"], segs=10)
    mb.span((px - 0.16, -0.32, top - 0.3), (px + 0.16, -0.02, top + 0.05), P["pipe"])  # hopper head
    z = 0.8
    while z < top:
        mb.span((px - 0.09, -0.22, z), (px + 0.09, 0.0, z + 0.05), P["iron"])
        z += 2.2
    mb.cyl(0.08, 0.2, (px, -0.2, 0.1), P["pipe"], rot=(math.pi / 2, 0, 0), segs=10)  # the shoe
    # ---- a fire escape over the first two bays
    if fire_escape:
        fx0, fx1 = x0 + 0.3, x0 + 2 * BAY - 0.3
        for f in range(floors):
            z = GF + f * FH + 0.3
            mb.span((fx0, -1.05, z - 0.05), (fx1, -0.02, z), P["iron"])
            for k in range(12):  # the grating's bars
                gx = fx0 + (fx1 - fx0) * (k + 0.5) / 12
                mb.span((gx - 0.01, -1.05, z - 0.09), (gx + 0.01, -0.02, z - 0.05), P["iron"])
            mb.rod((fx0, -1.05, z + 1.0), (fx1, -1.05, z + 1.0), 0.02, P["iron"], 6)
            mb.rod((fx0, -1.05, z + 0.5), (fx1, -1.05, z + 0.5), 0.012, P["iron"], 6)
            for ex in (fx0, fx1):
                mb.rod((ex, -1.05, z + 1.0), (ex, -0.02, z + 1.0), 0.02, P["iron"], 6)
            n = 14
            for k in range(n + 1):
                bx = fx0 + (fx1 - fx0) * k / n
                mb.span((bx - 0.012, -1.062, z), (bx + 0.012, -1.038, z + 1.0), P["iron"])
            mb.rod((fx0 + 0.2, -0.05, z - 0.05), (fx0 + 0.2, -0.95, z - 0.6), 0.025, P["iron"], 6)  # brackets
            mb.rod((fx1 - 0.2, -0.05, z - 0.05), (fx1 - 0.2, -0.95, z - 0.6), 0.025, P["iron"], 6)
            if f + 1 < floors:  # stairs to the next landing
                sa = Vector((fx1 - 0.3, -0.55, z))
                sb = Vector((fx0 + 1.6, -0.55, z + FH))
                for side in (-0.28, 0.28):
                    mb.rod(sa + Vector((0, side, 0)), sb + Vector((0, side, 0)), 0.03, P["iron"], 6)
                    mb.rod(sa + Vector((0, side, 0.9)), sb + Vector((0, side, 0.9)), 0.015, P["iron"], 6)
                steps = 11
                for k in range(1, steps):
                    p = sa.lerp(sb, k / steps)
                    mb.span((p.x - 0.1, -0.83, p.z - 0.02), (p.x + 0.1, -0.27, p.z + 0.02), P["iron"])
        # the drop ladder, pulled up under the first landing
        lx = fx1 - 0.5
        for s in (-0.2, 0.2):
            mb.rod((lx + s, -1.0, GF + 0.3), (lx + s, -1.0, GF - 1.6), 0.018, P["iron"], 6)
        for k in range(7):
            zz = GF - 1.5 + k * 0.28
            mb.rod((lx - 0.2, -1.0, zz), (lx + 0.2, -1.0, zz), 0.012, P["iron"], 4)
    # ---- a blade sign sticking out, neon on both faces
    if blade:
        bx = x1 - 0.2 if (fire_escape or rnd.random() < 0.5) else x0 + 0.2
        bz0 = GF - 0.7
        bz1 = bz0 + 0.72 * len(blade) + 0.4
        mb.span((bx - 0.08, -1.45, bz0), (bx + 0.08, -0.35, bz1), P["sign_board"])
        for zz in (bz0 + 0.3, bz1 - 0.3):
            mb.rod((bx, 0.0, zz), (bx, -0.4, zz), 0.03, P["iron"], 6)
        for s in (-1, 1):
            xf = bx + s * 0.1
            letters = "\n".join(blade)
            t = text(letters, 0.52, (xf, -0.9, (bz0 + bz1) / 2), P["neon"], rot=(math.pi / 2, 0, s * math.pi / 2),
                     tube=0.02)
            t.data.update()
            extra.append(t)
            for a, b in (((xf, -1.38, bz0 + 0.1), (xf, -1.38, bz1 - 0.1)), ((xf, -0.42, bz0 + 0.1), (xf, -0.42, bz1 - 0.1)),
                         ((xf, -1.38, bz0 + 0.1), (xf, -0.42, bz0 + 0.1)), ((xf, -1.38, bz1 - 0.1), (xf, -0.42, bz1 - 0.1))):
                mbn.rod(a, b, 0.018, P["neon2"], 6)
    o = mb.obj(name)
    export([o, mbn.obj(name + "_n")] + extra, name)


BUILDINGS = [
    # name, bays, floors, sign, style, awning, fire escape, blade, trim
    ("bldg_0", 3, 4, "NOODLE HOUSE", "sash", True, False, "HOTEL", "trim_cream"),
    ("bldg_1", 3, 3, "LUCKY PAWN", "grid", False, True, None, "trim"),
    ("bldg_2", 4, 5, "KARAOKE", "arch", False, False, "BAR", "trim_cream"),
    ("bldg_3", 3, 4, "ARCADE 88", "sash", False, True, "24H", "trim"),
    ("bldg_4", 4, 3, "JADE DINER", "grid", True, False, None, "trim_cream"),
    ("bldg_5", 2, 4, "LIQUOR", "arch", False, False, "OPEN", "trim"),
    ("bldg_6", 2, 5, "TATTOO", "sash", True, True, None, "trim_cream"),
    ("bldg_7", 3, 4, "VIDEO CLUB", "grid", False, False, "CAFE", "trim"),
]


# ---------------------------------------------------------------------------------------------- vehicles and street

def car(name, paint_c):
    reset()
    paint = mat(name + "_paint", paint_c, 0.18, 0.5, coat=1.0)
    glass = mat("car_glass", (0.03, 0.04, 0.06), 0.04, 0.4, coat=1.0)
    tyre = mat("tyre", (0.03, 0.03, 0.03), 0.85)
    rim = mat("chrome", (0.85, 0.86, 0.9), 0.12, 1.0)
    black = mat("car_black", (0.02, 0.02, 0.025), 0.5)
    head = mat("headlight", (1.0, 0.95, 0.8), 0.2, emit=5.0)
    tail = mat("taillight", (1.0, 0.06, 0.05), 0.2, emit=4.0)
    amber = mat("indicator", (1.0, 0.5, 0.05), 0.2, emit=2.0)
    plate = mat("plate", (0.85, 0.82, 0.6), 0.5)
    W = 1.78
    mb = MB()
    # the body: a side profile with round wheel arches, extruded across
    wz, wr = 0.33, 0.43
    prof = [(2.28, 0.3), (2.34, 0.52), (2.3, 0.74), (2.1, 0.84), (1.0, 0.92), (0.72, 0.95), (-1.55, 0.97), (-2.05, 0.95),
            (-2.28, 0.86), (-2.34, 0.55), (-2.28, 0.3)]
    bottom = []
    for cx in (-1.38, 1.38):
        bottom.append((cx - wr, 0.3))
        for k in range(1, 10):
            a = math.pi - math.pi * k / 10
            bottom.append((cx + wr * math.cos(a), wz + wr * math.sin(a)))
        bottom.append((cx + wr, 0.3))
    prof = prof + bottom
    mb.prism(prof, -W / 2, W / 2, paint)
    body = mb.obj("body", bevel=0.05)
    mb = MB()
    # the cabin: glass all round, a roof, pillars
    cab = [(0.72, 0.95), (0.02, 1.42), (-1.02, 1.43), (-1.62, 0.97)]
    mb.prism(cab, -W / 2 + 0.1, W / 2 - 0.1, glass)
    mb.prism([(0.06, 1.4), (0.0, 1.47), (-1.02, 1.48), (-1.08, 1.41)], -W / 2 + 0.08, W / 2 - 0.08, paint)
    for s in (-1, 1):
        y = s * (W / 2 - 0.095)
        mb.rod((0.72, y, 0.95), (0.03, y, 1.43), 0.045, paint, 6)          # A pillar
        mb.rod((-0.48, y, 0.96), (-0.48, y, 1.44), 0.05, paint, 6)          # B pillar
        mb.rod((-1.6, y, 0.97), (-1.03, y, 1.44), 0.07, paint, 6)           # C pillar
        mb.box((0.62, s * (W / 2 + 0.06), 1.0), (0.14, 0.12, 0.09), black)  # mirror
        mb.span((-1.9, s * W / 2 - 0.012, 0.6), (1.9, s * W / 2 + 0.012, 0.64), rim)  # side trim
        for hx in (0.25, -0.85):
            mb.span((hx - 0.1, s * W / 2 - 0.02, 0.84), (hx + 0.1, s * W / 2 + 0.02, 0.87), rim)  # handles
        for x, z0, z1 in ((0.35, 0.35, 0.93), (-0.5, 0.35, 0.95)):  # door shut lines
            mb.span((x - 0.006, s * W / 2 - 0.01, z0), (x + 0.006, s * W / 2 + 0.01, z1), black)
    # front: grille, headlights, bumpers, indicators, plate; rear: tail lamps
    mb.span((2.28, -0.5, 0.52), (2.34, 0.5, 0.74), black)
    for k in range(4):
        mb.span((2.3, -0.48, 0.55 + k * 0.05), (2.345, 0.48, 0.565 + k * 0.05), rim)
    for s in (-1, 1):
        mb.box((2.33, s * 0.66, 0.66), (0.04, 0.3, 0.15), head)
        mb.box((2.31, s * 0.8, 0.5), (0.04, 0.1, 0.06), amber)
        mb.box((-2.33, s * 0.62, 0.72), (0.04, 0.42, 0.14), tail)
    for x in (2.36, -2.36):
        mb.span((x - 0.1, -W / 2 - 0.02, 0.28), (x + 0.1, W / 2 + 0.02, 0.42), black)
        mb.box((x + (0.1 if x > 0 else -0.1), 0, 0.35), (0.02, 0.5, 0.12), plate)
    for x in (-1.38, 1.38):
        for s in (-1, 1):
            y = s * (W / 2 - 0.13)
            mb.cyl(0.33, 0.22, (x, y, 0.33), tyre, rot=(math.pi / 2, 0, 0), segs=24)
            mb.cyl(0.21, 0.23, (x, y + s * 0.005, 0.33), rim, rot=(math.pi / 2, 0, 0), segs=20)
            mb.cyl(0.07, 0.24, (x, y + s * 0.01, 0.33), black, rot=(math.pi / 2, 0, 0), segs=10)
            for k in range(5):
                a = k * 2 * math.pi / 5
                mb.box((x + 0.13 * math.cos(a), y + s * 0.12, 0.33 + 0.13 * math.sin(a)), (0.06, 0.02, 0.1), black, (0, a, 0))
        mb.span((x - 0.42, -W / 2 + 0.26, 0.28), (x + 0.42, W / 2 - 0.26, 0.76), black)  # the wheel wells' dark inside
    mb.span((-2.1, -W / 2 + 0.1, 0.18), (2.1, W / 2 - 0.1, 0.32), black)  # underside
    export([body, mb.obj(name + "_d")], name)


def hydrant():
    reset()
    red = mat("hydrant", (0.75, 0.08, 0.05), 0.35, 0.3, coat=0.6)
    cap = mat("hydrant_cap", (0.9, 0.75, 0.2), 0.4, 0.4)
    mb = MB()
    mb.cyl(0.2, 0.08, (0, 0, 0.04), red, segs=16)
    mb.cyl(0.14, 0.55, (0, 0, 0.35), red, segs=16)
    mb.cyl(0.18, 0.06, (0, 0, 0.62), red, segs=16)
    mb.sphere(0.15, (0, 0, 0.68), cap, (1, 1, 0.8))
    mb.cyl(0.04, 0.1, (0, 0, 0.82), cap, segs=6)
    for a in (0, math.pi):
        mb.cyl(0.06, 0.2, (0.16 * math.cos(a), 0, 0.46), red, rot=(0, math.pi / 2, 0), segs=12)
        mb.cyl(0.075, 0.04, (0.26 * math.cos(a), 0, 0.46), cap, rot=(0, math.pi / 2, 0), segs=6)
    mb.cyl(0.08, 0.16, (0, -0.16, 0.42), red, rot=(math.pi / 2, 0, 0), segs=12)
    mb.cyl(0.095, 0.04, (0, -0.25, 0.42), cap, rot=(math.pi / 2, 0, 0), segs=6)
    export([mb.obj("hydrant")], "hydrant")


def bin_():
    reset()
    green = mat("bin", (0.08, 0.18, 0.12), 0.45, 0.5)
    rim = mat("bin_rim", (0.4, 0.4, 0.42), 0.3, 0.8)
    bag = mat("trash_bag", (0.04, 0.04, 0.05), 0.25, coat=0.6)
    mb = MB()
    mb.cyl(0.3, 0.9, (0, 0, 0.47), green, segs=20)
    for z in (0.12, 0.5, 0.88):
        mb.torus(0.305, 0.02, (0, 0, z), rim, segs=24, ring=6)
    for k in range(10):
        a = k * 2 * math.pi / 10
        mb.span((0.3 * math.cos(a) - 0.02, 0.3 * math.sin(a) - 0.02, 0.15), (0.3 * math.cos(a) + 0.02, 0.3 * math.sin(a) + 0.02, 0.85), rim)
    mb.sphere(0.27, (0, 0, 0.95), bag, (1, 1, 0.45))
    mb.cyl(0.03, 0.04, (0, 0, 0.0), rim, segs=8)
    export([mb.obj("bin")], "bin")


def dumpster():
    reset()
    body = mat("dumpster", (0.1, 0.25, 0.18), 0.55, 0.5)
    rust = mat("rust", (0.35, 0.16, 0.06), 0.9)
    lid = mat("dumpster_lid", (0.04, 0.05, 0.05), 0.4)
    black = mat("car_black", (0.02, 0.02, 0.025), 0.5)
    mb = MB()
    mb.prism([(-0.95, 0.15), (0.95, 0.15), (0.95, 1.25), (-0.95, 1.25)], -0.55, 0.55, body)
    for x in (-0.6, 0.0, 0.6):
        mb.span((x - 0.04, -0.58, 0.18), (x + 0.04, -0.55, 1.22), body)  # ribs
    mb.span((-0.95, -0.6, 1.1), (0.95, -0.55, 1.25), rust)
    mb.span((-0.9, -0.3, 0.2), (-0.2, -0.56, 0.5), rust)
    mb.box((-0.48, 0.0, 1.32), (0.93, 1.2, 0.05), lid, (0.12, 0, 0))
    mb.box((0.48, 0.0, 1.35), (0.93, 1.2, 0.05), lid, (0.25, 0, 0.03))
    for x in (-0.8, 0.8):
        for y in (-0.4, 0.4):
            mb.cyl(0.08, 0.05, (x, y, 0.08), black, rot=(math.pi / 2, 0, 0), segs=10)
    mb.span((-1.02, -0.3, 0.75), (-0.95, 0.3, 0.9), body)  # side pockets
    mb.span((0.95, -0.3, 0.75), (1.02, 0.3, 0.9), body)
    export([mb.obj("dumpster", bevel=0.015)], "dumpster")


def meter():
    reset()
    pole = mat("meter_pole", (0.15, 0.15, 0.17), 0.4, 0.7)
    head = mat("meter_head", (0.35, 0.37, 0.4), 0.3, 0.8)
    glass = mat("meter_glass", (0.6, 0.9, 0.7), 0.1, emit=0.8)
    mb = MB()
    mb.cyl(0.035, 1.2, (0, 0, 0.6), pole, segs=10)
    mb.sphere(0.13, (0, 0, 1.32), head, (1, 0.8, 1.2))
    mb.box((0, -0.1, 1.36), (0.12, 0.02, 0.08), glass)
    export([mb.obj("meter")], "meter")


def sign_post():
    reset()
    pole = mat("meter_pole", (0.15, 0.15, 0.17), 0.4, 0.7)
    white = mat("sign_white", (0.85, 0.85, 0.85), 0.4)
    red = mat("sign_red", (0.7, 0.05, 0.05), 0.4)
    blue = mat("sign_blue", (0.05, 0.2, 0.6), 0.4)
    mb = MB()
    mb.cyl(0.03, 2.6, (0, 0, 1.3), pole, segs=8)
    mb.cyl(0.3, 0.02, (0, -0.04, 2.3), blue, rot=(math.pi / 2, 0, 0), segs=24)
    mb.torus(0.27, 0.035, (0, -0.055, 2.3), red, rot=(math.pi / 2, 0, 0), segs=24, ring=6)
    mb.box((0, -0.055, 2.3), (0.5, 0.02, 0.06), red, (0, math.pi / 4, 0))
    mb.span((-0.25, -0.05, 1.7), (0.25, -0.03, 1.95), white)
    export([mb.obj("sign_post")], "sign_post")


def manhole():
    reset()
    iron = mat("manhole", (0.12, 0.11, 0.1), 0.35, 0.8)
    mb = MB()
    mb.cyl(0.42, 0.02, (0, 0, 0.01), iron, segs=24)
    for r in (0.12, 0.24, 0.36):
        mb.torus(r, 0.012, (0, 0, 0.02), iron, segs=24, ring=4)
    for k in range(6):
        a = k * math.pi / 6
        mb.box((0, 0, 0.02), (0.8, 0.02, 0.012), iron, (0, 0, a))
    export([mb.obj("manhole")], "manhole")


def street_lamp():
    reset()
    iron = mat("lamp_iron", (0.06, 0.07, 0.08), 0.4, 0.7)
    glow = mat("lamp_glow", (1.0, 0.82, 0.5), 0.3, emit=9.0)
    mb = MB()
    mb.cyl(0.18, 0.5, (0, 0, 0.25), iron, r2=0.1, segs=12)
    mb.cyl(0.21, 0.08, (0, 0, 0.04), iron, segs=12)
    for z in (0.55, 1.4):
        mb.torus(0.085, 0.02, (0, 0, z), iron, segs=12, ring=4)
    mb.cyl(0.07, 4.6, (0, 0, 2.8), iron, r2=0.05, segs=12)
    # a curved arm out over the road, and the lantern
    pts = [(0, 0, 5.0), (0, 0.25, 5.2), (0, 0.6, 5.3), (0, 1.0, 5.3), (0, 1.25, 5.25)]
    for a, b in zip(pts, pts[1:]):
        mb.rod(a, b, 0.045, iron)
    mb.cyl(0.32, 0.18, (0, 1.3, 5.12), iron, r2=0.1, segs=16)
    mb.cyl(0.22, 0.08, (0, 1.3, 4.99), glow, segs=16)
    mb.sphere(0.03, (0, 0, 5.14), iron)
    export([mb.obj("street_lamp")], "street_lamp")


# ---------------------------------------------------------------------------------------------- docks

def container():
    colours = [(0.62, 0.16, 0.1), (0.1, 0.3, 0.55), (0.16, 0.42, 0.26), (0.75, 0.55, 0.12)]
    names = ["ORCA LINE", "SEAVALE", "NORDBAY", "MARLOW"]
    for i, c in enumerate(colours):
        reset()
        steel = mat("container_%d" % i, c, 0.55, 0.45)
        dark = mat("container_dark_%d" % i, tuple(v * 0.55 for v in c), 0.6, 0.45)
        paint = mat("stencil", (0.9, 0.9, 0.85), 0.6)
        mb = MB()
        L, Wd, H = 6.0, 2.44, 2.6
        mb.span((-L / 2 + 0.1, -Wd / 2 + 0.04, 0.12), (L / 2 - 0.1, Wd / 2 - 0.04, H - 0.12), steel)
        k = 0
        x = -L / 2 + 0.2
        while x < L / 2 - 0.2:  # corrugation on the long sides
            mb.span((x, -Wd / 2, 0.14), (x + 0.12, Wd / 2, H - 0.14), steel if k % 2 == 0 else dark)
            x += 0.24
            k += 1
        for sx in (-1, 1):  # corner posts, rails, castings
            for sy in (-1, 1):
                mb.span((sx * L / 2 - 0.1 * (sx > 0), sy * Wd / 2 - 0.1 * (sy > 0), 0), (sx * L / 2 + 0.1 * (sx < 0), sy * Wd / 2 + 0.1 * (sy < 0), H), dark)
                for z in (0, H - 0.12):
                    mb.span((sx * L / 2 - 0.18 * (sx > 0) - 0.005, sy * Wd / 2 - 0.16 * (sy > 0) - 0.005, z),
                            (sx * L / 2 + 0.18 * (sx < 0) + 0.005, sy * Wd / 2 + 0.16 * (sy < 0) + 0.005, z + 0.12), mat("casting", (0.1, 0.1, 0.1), 0.6, 0.6))
        for z in (0.0, H - 0.14):
            for sy in (-1, 1):
                mb.span((-L / 2, sy * Wd / 2 - 0.08, z), (L / 2, sy * Wd / 2 + 0.08, z + 0.14), dark)
        # the doors at +X: two leaves, four lock bars with handles
        mb.span((L / 2 - 0.02, -Wd / 2 + 0.1, 0.14), (L / 2 + 0.02, Wd / 2 - 0.1, H - 0.14), steel)
        for y in (-0.9, -0.45, 0.45, 0.9):
            mb.rod((L / 2 + 0.05, y, 0.2), (L / 2 + 0.05, y, H - 0.2), 0.025, dark, 6)
            mb.span((L / 2 + 0.03, y - 0.03, 1.1), (L / 2 + 0.1, y + 0.15, 1.16), dark)
        # the line's name, stencilled on the side facing the street, and a code
        ts = [text(names[i], 0.5, (-0.6, -Wd / 2 - 0.01, 1.7), paint, fill=True, extrude=0.004, max_w=4.4, spacing=1.15),
              text("%sU %06d" % (names[i][:3], 104217 * (i + 3) % 999999), 0.17, (1.9, -Wd / 2 - 0.01, 2.25), paint, fill=True, extrude=0.003)]
        export([mb.obj("container_%d" % i)] + ts, "container_%d" % i)


def bollard():
    reset()
    iron = mat("bollard", (0.05, 0.05, 0.06), 0.45, 0.7)
    yellow = mat("bollard_paint", (0.8, 0.6, 0.1), 0.5)
    rope = mat("rope", (0.55, 0.45, 0.3), 0.95)
    mb = MB()
    mb.cyl(0.3, 0.1, (0, 0, 0.05), iron, segs=16)
    mb.cyl(0.2, 0.55, (0, 0, 0.38), iron, r2=0.17, segs=16)
    mb.cyl(0.28, 0.1, (0, 0, 0.7), yellow, segs=16)
    mb.sphere(0.2, (0, 0, 0.75), iron, (1, 1, 0.5))
    for k in range(3):  # a hawser looped round it
        mb.torus(0.23 + k * 0.012, 0.035, (0, 0, 0.3 + k * 0.08), rope, segs=20, ring=6)
    export([mb.obj("bollard")], "bollard")


def rope_coil():
    reset()
    rope = mat("rope", (0.55, 0.45, 0.3), 0.95)
    mb = MB()
    for k in range(6):
        mb.torus(0.42 - (k % 2) * 0.06, 0.045, (0, 0, 0.05 + k * 0.07), rope, segs=24, ring=6)
    export([mb.obj("rope_coil")], "rope_coil")


def dock_light():
    reset()
    steel = mat("lamp_iron", (0.06, 0.07, 0.08), 0.4, 0.7)
    glow = mat("flood_glow", (1.0, 0.7, 0.35), 0.3, emit=10.0)
    mb = MB()
    mb.span((-0.25, -0.25, 0), (0.25, 0.25, 0.4), mat("concrete", (0.4, 0.4, 0.4), 0.9))
    mb.cyl(0.09, 4.4, (0, 0, 2.4), steel, r2=0.06, segs=10)
    mb.span((-0.7, -0.08, 4.6), (0.7, 0.08, 4.7), steel)
    for x in (-0.55, 0.55):
        mb.box((x, -0.15, 4.45), (0.4, 0.3, 0.25), steel, (0.5, 0, 0))
        mb.box((x, -0.29, 4.37), (0.32, 0.02, 0.18), glow, (0.5, 0, 0))
    for z in range(1, 5):  # a climbing ladder
        mb.rod((-0.06, 0.1, z), (0.06, 0.1, z), 0.012, steel, 4)
    export([mb.obj("dock_light")], "dock_light")


def ship():
    """A small freighter, seen broadside: hull with a boot top, a white bridge with lit windows, a deck of boxes."""
    reset()
    hull = mat("hull", (0.08, 0.08, 0.1), 0.5, 0.3)
    boot = mat("hull_red", (0.45, 0.06, 0.05), 0.6)
    white = mat("ship_white", (0.75, 0.75, 0.72), 0.5)
    lit = mat("ship_window", (1.0, 0.85, 0.55), 0.3, emit=3.0)
    red = mat("mast_red", (1.0, 0.1, 0.08), 0.3, emit=8.0)
    green = mat("mast_green", (0.1, 1.0, 0.3), 0.3, emit=8.0)
    mb = MB()
    L = 64.0
    prof = [(-L / 2, 0.0), (L / 2 - 6, 0.0), (L / 2, 3.0), (L / 2 + 1.5, 7.0), (-L / 2 + 1, 7.0), (-L / 2, 5.0)]
    mb.prism(prof, -6, 6, hull)
    mb.span((-L / 2 + 0.3, -6.05, -0.5), (L / 2 - 6.5, 6.05, 1.2), boot)
    for sy in (-1, 1):  # both sides: sheer stripe, portholes, a draught scale at the bow
        mb.span((-L / 2 + 1, sy * 6.02 - 0.02, 6.55), (L / 2, sy * 6.02 + 0.02, 6.75), white)
        for k in range(14):
            x = -L / 2 + 6 + k * 2.6
            mb.cyl(0.2, 0.08, (x, sy * 6.03, 5.0), lit if k % 3 != 1 else white, rot=(math.pi / 2, 0, 0), segs=10)
        for k in range(6):
            mb.span((L / 2 - 7.5, sy * 6.03 - 0.02, 0.4 + k * 0.5), (L / 2 - 7.1, sy * 6.03 + 0.02, 0.5 + k * 0.5), white)
    # the bridge at the stern
    bx = -L / 2 + 6
    for f in range(4):
        z = 7 + f * 2.6
        w = 9 - f * 0.6
        mb.span((bx - 3.5, -w / 2, z), (bx + 3.5, w / 2, z + 2.6), white)
        for k in range(6):
            wx = bx - 2.8 + k * 1.1
            for sy in (-1, 1):
                if (k + f + (sy > 0)) % 4 != 3:
                    mb.span((wx - 0.35, sy * w / 2 - 0.02, z + 1.0), (wx + 0.35, sy * w / 2 + 0.02, z + 1.8), lit)
    mb.span((bx - 4.2, -5.2, 17.4), (bx + 4.2, 5.2, 17.6), white)
    mb.cyl(1.2, 5, (bx + 1.5, 0, 20), boot, segs=14)  # funnel
    mb.rod((bx, -2, 17.6), (bx, -2, 24), 0.12, white, 6)
    mb.sphere(0.25, (bx, -2, 24.2), red)
    mb.sphere(0.25, (L / 2 - 2, -2, 12.2), green)
    mb.rod((L / 2 - 2, -2, 7), (L / 2 - 2, -2, 12), 0.12, white, 6)
    # a deck cargo of containers in the line colours
    cols = [mat("deck_%d" % i, c, 0.55, 0.4) for i, c in enumerate([(0.62, 0.16, 0.1), (0.1, 0.3, 0.55), (0.16, 0.42, 0.26), (0.75, 0.55, 0.12), (0.5, 0.5, 0.5)])]
    rnd = random.Random(5)
    x = bx + 5
    while x < L / 2 - 8:
        for y in (-3.8, -1.3, 1.2):
            for t in range(rnd.randint(1, 3)):
                mb.span((x, y, 7 + t * 2.6), (x + 6, y + 2.44, 7 + t * 2.6 + 2.55), cols[rnd.randrange(5)])
        x += 6.2
    # a string of deck lights
    for k in range(12):
        for sy in (-1, 1):
            mb.sphere(0.15, (bx + 5 + k * 3.6, sy * 6.1, 7.3), lit)
    ts = [text("MERIDIAN STAR", 1.1, (L / 2 - 16, sy * 6.05, 5.6), white, rot=(math.pi / 2, 0, 0 if sy < 0 else math.pi), fill=True, extrude=0.01)
          for sy in (-1, 1)]
    export([mb.obj("ship")] + ts, "ship")


def crane():
    """A harbour crane: a portal on four legs, the turning house with a lit cab, a lattice jib raised against the sky."""
    reset()
    steel = mat("crane_steel", (0.75, 0.42, 0.1), 0.5, 0.4)
    dark = mat("crane_dark", (0.1, 0.1, 0.1), 0.5, 0.5)
    lit = mat("ship_window", (1.0, 0.85, 0.55), 0.3, emit=3.0)
    red = mat("mast_red", (1.0, 0.1, 0.08), 0.3, emit=8.0)
    mb = MB()
    for sx in (-3, 3):
        for sy in (-3, 3):
            mb.rod((sx, sy, 0), (sx * 0.5, sy * 0.5, 9), 0.35, steel, 8)
    for z in (3, 6):
        k = 1 - z / 18
        for a, b in (((-3 * k, -3 * k), (3 * k, -3 * k)), ((-3 * k, 3 * k), (3 * k, 3 * k)), ((-3 * k, -3 * k), (-3 * k, 3 * k)), ((3 * k, -3 * k), (3 * k, 3 * k))):
            mb.rod((a[0], a[1], z), (b[0], b[1], z), 0.18, steel, 6)
    mb.cyl(2.2, 0.8, (0, 0, 9.4), steel, segs=20)
    mb.span((-2.5, -2.0, 9.8), (3.5, 2.0, 13.8), steel)  # machine house
    mb.span((-4.5, -1.4, 10.2), (-2.4, 1.4, 12.6), dark)  # cab
    mb.span((-4.55, -1.3, 11.0), (-4.5, 1.3, 12.3), lit)
    mb.span((-4.4, -1.42, 11.0), (-2.6, -1.4, 12.3), lit)
    mb.span((2.5, -1.5, 10.0), (4.6, 1.5, 12.5), dark)  # counterweight
    # the jib: a lattice of four chords with zig-zag lacing, raised 50 degrees
    base = Vector((-2.0, 0, 12.5))
    d = Vector((-math.cos(math.radians(50)), 0, math.sin(math.radians(50))))
    Lj = 30.0
    n = d.cross(Vector((0, 1, 0))).normalized()
    for oy in (-0.9, 0.9):
        for on in (-0.6, 0.6):
            off = Vector((0, oy, 0)) + n * on
            mb.rod(base + off, base + d * Lj + off * 0.4, 0.14, steel, 6)
    steps = 20
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        s0, s1 = 1 - 0.6 * t0, 1 - 0.6 * t1
        for oy in (-0.9, 0.9):
            a = base + d * Lj * t0 + (Vector((0, oy, 0)) + n * (0.6 if k % 2 else -0.6)) * s0
            b = base + d * Lj * t1 + (Vector((0, oy, 0)) + n * (-0.6 if k % 2 else 0.6)) * s1
            mb.rod(a, b, 0.06, steel, 4)
    tip = base + d * Lj
    mb.sphere(0.35, tip + Vector((0, 0, 0.4)), red)
    mb.rod(tip, tip + Vector((0, 0, -16)), 0.03, dark, 4)  # the hoist rope and a hook block
    mb.span(tuple(tip + Vector((-0.4, -0.3, -17))), tuple(tip + Vector((0.4, 0.3, -16))), steel)
    mb.rod((3.0, 0, 13.8), (0.5, 0, 22), 0.2, steel, 6)  # A-frame and the luffing tie
    mb.rod((0.5, 0, 22), tuple(tip), 0.05, dark, 4)
    mb.sphere(0.3, (0.5, 0, 22.2), red)
    export([mb.obj("crane")], "crane")


# ---------------------------------------------------------------------------------------------- rooftops

def water_tank():
    reset()
    wood = mat("tank_wood", (0.42, 0.28, 0.17), 0.85)
    wood_d = mat("tank_wood_dark", (0.3, 0.2, 0.12), 0.85)
    iron = mat("tank_iron", (0.12, 0.12, 0.13), 0.5, 0.6)
    roof = mat("tank_roof", (0.18, 0.16, 0.15), 0.7, 0.3)
    mb = MB()
    n = 28
    for k in range(n):  # staves
        a = 2 * math.pi * k / n
        mb.box((1.1 * math.cos(a), 1.1 * math.sin(a), 3.2), (0.23, 0.08, 2.4), wood if k % 3 else wood_d, (0, 0, a + math.pi / 2))
    mb.cyl(1.08, 2.3, (0, 0, 3.2), wood_d, segs=20)
    for z in (2.2, 2.7, 3.2, 3.7, 4.2):  # hoops
        mb.torus(1.15, 0.025, (0, 0, z), iron, segs=28, ring=4)
    mb.cyl(1.3, 0.9, (0, 0, 4.85), roof, r2=0.08, segs=24)
    mb.cyl(0.08, 0.3, (0, 0, 5.4), iron, segs=8)
    mb.span((-1.3, -1.3, 1.9), (1.3, 1.3, 2.0), iron)  # the platform
    for x in (-0.9, 0.9):
        for y in (-0.9, 0.9):
            mb.span((x - 0.07, y - 0.07, 0), (x + 0.07, y + 0.07, 1.95), iron)
    for a, b in (((-0.9, -0.9, 0.1), (0.9, -0.9, 1.85)), ((0.9, -0.9, 0.1), (-0.9, -0.9, 1.85)),
                 ((-0.9, 0.9, 0.1), (-0.9, -0.9, 1.85)), ((0.9, 0.9, 0.1), (0.9, -0.9, 1.85))):
        mb.rod(a, b, 0.025, iron, 4)  # cross bracing
    for s in (-0.18, 0.18):  # a ladder up the side
        mb.rod((0.5 + s, -1.25, 0), (0.5 + s, -1.25, 4.4), 0.02, iron, 4)
    for k in range(15):
        mb.rod((0.32, -1.25, 0.3 + k * 0.28), (0.68, -1.25, 0.3 + k * 0.28), 0.012, iron, 4)
    mb.rod((0, -1.1, 2.1), (0, -1.9, 0.1), 0.05, iron, 6)  # the outflow pipe
    export([mb.obj("water_tank")], "water_tank")


def ac_unit():
    reset()
    body = mat("ac_body", (0.62, 0.64, 0.63), 0.45, 0.4)
    grill = mat("ac_grill", (0.1, 0.1, 0.11), 0.5, 0.6)
    rust = mat("rust", (0.35, 0.16, 0.06), 0.9)
    mb = MB()
    mb.span((-0.9, -0.55, 0.12), (0.9, 0.55, 1.1), body)
    mb.span((-0.95, -0.6, 0), (0.95, 0.6, 0.12), grill)
    for x in (-0.45, 0.45):  # two fans on top, with guards
        mb.cyl(0.38, 0.04, (x, 0, 1.12), grill, segs=24)
        for k in range(3):
            mb.torus(0.12 + k * 0.12, 0.012, (x, 0, 1.16), body, segs=20, ring=4)
        mb.box((x, 0, 1.15), (0.7, 0.02, 0.02), body)
        mb.box((x, 0, 1.15), (0.02, 0.7, 0.02), body)
    for k in range(9):  # louvres on the front
        mb.span((-0.8, -0.56, 0.25 + k * 0.09), (0.8, -0.55, 0.29 + k * 0.09), grill)
    mb.span((0.3, -0.565, 0.15), (0.8, -0.555, 0.35), rust)
    mb.rod((0.9, 0.3, 0.5), (1.3, 0.3, 0.5), 0.05, grill, 8)
    mb.rod((1.3, 0.3, 0.5), (1.3, 0.3, 0.0), 0.05, grill, 8)
    export([mb.obj("ac_unit", bevel=0.01)], "ac_unit")


def vents():
    reset()
    metal = mat("vent_metal", (0.5, 0.52, 0.55), 0.35, 0.8)
    dark = mat("vent_dark", (0.08, 0.08, 0.09), 0.5, 0.6)
    mb = MB()
    # a turbine vent, a mushroom vent and a gooseneck, on a curb
    mb.span((-1.2, -0.4, 0), (1.2, 0.4, 0.2), mat("curb", (0.3, 0.3, 0.3), 0.9))
    mb.cyl(0.18, 0.6, (-0.7, 0, 0.5), metal, segs=14)
    for k in range(16):
        a = k * 2 * math.pi / 16
        mb.box((-0.7 + 0.24 * math.cos(a), 0.24 * math.sin(a), 0.95), (0.03, 0.12, 0.3), metal, (0.3, 0, a))
    mb.sphere(0.27, (-0.7, 0, 1.08), metal, (1, 1, 0.45))
    mb.cyl(0.12, 0.8, (0.2, 0, 0.6), metal, segs=12)
    mb.cyl(0.3, 0.12, (0.2, 0, 1.05), dark, r2=0.1, segs=16)
    mb.cyl(0.08, 0.6, (0.9, 0, 0.5), dark, segs=10)
    mb.rod((0.9, 0, 0.8), (0.9, -0.15, 1.0), 0.08, dark, 10)
    mb.rod((0.9, -0.15, 1.0), (0.9, -0.35, 0.95), 0.08, dark, 10)
    export([mb.obj("vents")], "vents")


def antenna():
    reset()
    steel = mat("antenna", (0.3, 0.3, 0.32), 0.4, 0.8)
    red = mat("mast_red", (1.0, 0.1, 0.08), 0.3, emit=8.0)
    dish = mat("dish", (0.75, 0.75, 0.72), 0.5, 0.2)
    mb = MB()
    mb.cyl(0.04, 6.0, (0, 0, 3.0), steel, segs=8)
    for z, w in ((3.5, 1.4), (4.4, 1.1), (5.2, 0.8)):
        mb.rod((-w / 2, 0, z), (w / 2, 0, z), 0.015, steel, 4)
        for k in range(5):
            x = -w / 2 + w * k / 4
            mb.rod((x, -0.25, z), (x, 0.25, z), 0.01, steel, 4)
    for a in (0, 2.1, 4.2):  # guy wires
        mb.rod((0, 0, 4.5), (1.8 * math.cos(a), 1.8 * math.sin(a), 0), 0.006, steel, 3)
    mb.sphere(0.08, (0, 0, 6.05), red)
    # a satellite dish on a short post
    mb.cyl(0.05, 0.9, (1.4, -0.3, 0.45), steel, segs=8)
    mb.sphere(0.5, (1.4, -0.45, 1.05), dish, (1, 0.25, 1), 16, 8)
    mb.rod((1.4, -0.55, 1.05), (1.4, -0.95, 1.05), 0.015, steel, 4)
    export([mb.obj("antenna")], "antenna")


def stair_hut():
    reset()
    wall = mat("brick", (0.45, 0.22, 0.16), 0.85)
    door = mat("hut_door", (0.3, 0.07, 0.06), 0.5, 0.3)
    bulb = mat("bulb", (1.0, 0.85, 0.6), 0.3, emit=8.0)
    roof = mat("tar", (0.08, 0.08, 0.08), 0.6)
    stone = mat("stone", (0.52, 0.5, 0.47), 0.8)
    mb = MB()
    mb.span((-1.5, -1.2, 0), (1.5, 1.2, 2.9), wall)
    mb.span((-1.6, -1.3, 2.9), (1.6, 1.3, 3.05), stone)
    mb.span((-1.55, -1.25, 3.05), (1.55, 1.25, 3.12), roof)
    mb.span((-0.5, -1.25, 0), (0.5, -1.18, 2.2), door)
    mb.span((-0.58, -1.26, 2.2), (0.58, -1.17, 2.3), stone)
    mb.span((0.3, -1.3, 1.0), (0.36, -1.25, 1.12), mat("chrome", (0.85, 0.86, 0.9), 0.12, 1.0))
    mb.cyl(0.1, 0.1, (0, -1.25, 2.55), mat("lamp_iron", (0.06, 0.07, 0.08), 0.4, 0.7), rot=(math.pi / 2, 0, 0), segs=10)
    mb.sphere(0.07, (0, -1.32, 2.5), bulb)
    export([mb.obj("stair_hut")], "stair_hut")


def billboard(name, words, sub):
    reset()
    steel = mat("crane_dark", (0.1, 0.1, 0.1), 0.5, 0.5)
    board = mat("sign_board", (0.03, 0.03, 0.04), 0.35, 0.5)
    neon = mat("neon", (1.0, 1.0, 1.0), 0.3, emit=6.0)
    neon2 = mat("neon2", (1.0, 1.0, 1.0), 0.3, emit=6.0)
    lamp = mat("bulb", (1.0, 0.85, 0.6), 0.3, emit=8.0)
    mb = MB()
    W, z0, z1 = 12.0, 2.0, 6.0
    mb.span((-W / 2, 0.0, z0), (W / 2, 0.2, z1), board)
    for x in (-W / 2 + 1, -W / 4, 0.0, W / 4, W / 2 - 1):  # the frame behind it
        mb.span((x - 0.08, 0.2, 0), (x + 0.08, 0.36, z1), steel)
        mb.rod((x, 0.3, z1 - 0.3), (x, 2.2, 0), 0.06, steel, 6)
    for z in (z0 + 0.2, (z0 + z1) / 2, z1 - 0.2):
        mb.span((-W / 2, 0.2, z - 0.06), (W / 2, 0.3, z + 0.06), steel)
    mb.span((-W / 2, -0.8, z0 - 0.1), (W / 2, 0.0, z0), steel)  # catwalk
    mb.rod((-W / 2, -0.8, z0 + 0.8), (W / 2, -0.8, z0 + 0.8), 0.02, steel, 4)
    for k in range(13):
        x = -W / 2 + k * W / 12
        mb.rod((x, -0.8, z0), (x, -0.8, z0 + 0.8), 0.015, steel, 4)
    for k in range(4):  # goose-neck lamps along the top
        x = -W / 2 + 1.5 + k * 3
        mb.rod((x, 0.0, z1), (x, -0.6, z1 + 0.35), 0.025, steel, 4)
        mb.sphere(0.08, (x, -0.65, z1 + 0.3), lamp)
    neon_frame(mb, -W / 2 + 0.25, W / 2 - 0.25, z0 + 0.25, z1 - 0.25, -0.03, neon2, 0.035)
    ts = [text(words, 1.3, (0, -0.05, (z0 + z1) / 2 + 0.45), neon, tube=0.04, max_w=W - 1.5),
          text(sub, 0.5, (0, -0.05, z0 + 0.85), neon2, tube=0.022, max_w=W - 3)]
    export([mb.obj(name)] + ts, name)


reset()
for spec in BUILDINGS:
    nm, bays, floors, sign, style, awn, fe, blade, trim = spec
    building(nm, bays, floors, sign, random.Random(nm), style, awn, fe, blade, trim)
car("car_0", (0.45, 0.05, 0.08))
car("car_1", (0.05, 0.28, 0.3))
car("car_2", (0.7, 0.66, 0.58))
hydrant()
bin_()
dumpster()
meter()
sign_post()
manhole()
street_lamp()
container()
bollard()
rope_coil()
dock_light()
ship()
crane()
water_tank()
ac_unit()
vents()
antenna()
stair_hut()
billboard("billboard_0", "NIGHT OWL", "RADIO 99.5 FM")
billboard("billboard_1", "STAR HOTEL", "ROOMS  BY THE HOUR")
