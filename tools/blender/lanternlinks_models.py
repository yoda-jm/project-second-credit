"""Lantern Links (game 26) props: the lantern garden's mini-golf gadgets and dressing.
Our own designs. Deterministic; output CC BY-SA 4.0; provenance: this script, no third-party assets.
Run: blender -b --factory-startup -P tools/blender/lanternlinks_models.py -- godot/games/lanternlinks/art/models [name ...]
Helpers come from blastyard_models.py (mat, box, cyl, sphere, ico, torus, rod, tube, prism, join, export, ...); the
lathe, clump and placement helpers below are this file's own.

Axes: built in Blender (Z up) and exported Y up, so Blender (x, y, z) is Godot (x, z, -y): Godot +Z is Blender -Y.
All sizes below are in Godot axes and metres; the game's grid cell is 0.5 m. Emissive materials all have "glow" in
their names (the game drives their energy by the hour). Every origin sits at the model's base centre unless stated.

windmill.glb      root "windmill" (the building, ~14.5k tris) and its child "blades" (~2k tris).
                  The base (a stone plinth) spans x -0.75..+0.75 and z -0.25..+0.25 (one 0.5 m wall cell along the
                  lane), 0.52 tall. A tunnel runs straight through it along Z: x -0.25..+0.25, straight sides up to
                  y 0.20 then a flat stone arch with its crown at y 0.30, open at both ends, no floor (the felt shows
                  through). Origin (0, 0, 0) = centre of the tunnel floor. Above it a stretched-octagon tower (1.7x as
                  wide as deep: 0.80 x 0.47 at its foot, 0.61 x 0.36 under the eaves at y 1.62) in cream plaster
                  (mill_plaster) with dark timber corners, rails and cross braces (mill_timber), a red tiled cap roof
                  in courses with ridge caps (mill_roof_tile, mill_roof_ridge; eaves reach x +-0.48, z +-0.30) and a
                  brass finial; the top is at y 2.34. Windows with warm panes (mill_window_glow), shutters and
                  flower boxes; a green door on the +X side opening onto a little railed balcony at each end of the
                  plinth (mill_rail); quoins and arch stones (mill_stone, mill_stone_dark); potted flowers.
                  Below y 0.6 the building stays inside z -0.25..+0.25; only the roof (above y 1.6) reaches +-0.30.
                  "blades": pivot at the hub, x 0, y 1.05, z +0.33 (just in front of the +Z face). Hub (to z 0.41),
                  windshaft (back into the tower to z 0.2) and four lattice sails (mill_sail_wood frames,
                  mill_sail_canvas cloth), each 0.98 from the hub axis to its tip, in the plane z 0.31..0.35.
                  Rest pose: blades straight up, down, left (-X) and right (+X); the down blade's tip is at y 0.07,
                  just above the tunnel mouth. Rotate the node about its local Z.
lantern_post.glb  root "lantern_post": a 1.9 m chamfered square wooden post (0.09 thick; cap to 1.94) on a stone
                  footing, with an arm and brace reaching +0.47 along X at y 1.86 and an iron hook. Child
                  "lantern" (the paper lantern below) with its pivot at the hook, x 0.40, y 1.82, z 0; it hangs
                  down to y 1.35. Materials post_wood, post_stone, post_iron + the lantern's.
paper_lantern.glb root "paper_lantern": a round ribbed paper lantern, 0.32 across, origin at the top of its hook
                  ring; the paper spans y -0.06..-0.36, the tassel ends at y -0.47. lantern_paper_glow (warm
                  orange-cream paper), lantern_wood (top and bottom caps), lantern_wire, lantern_tassel. ~2k tris.
stone_lantern.glb root "stone_lantern": a garden stone lantern 0.95 tall: hexagonal footing (0.44 across), round
                  pillar, hexagonal platform, a fire box with six glowing paper windows behind a wooden lattice
                  (stone_lantern_glow, stone_lantern_wood), a hexagonal roof 0.62 across with upturned corners and
                  a moss-dusted top, a bud finial. stone_lantern_stone, stone_lantern_moss.
flag.glb          root "flagstick": the pole, radius 0.012, from y 0 (origin: its bottom, sunk into the cup) to y 1.0,
                  white (flag_pole_white) with ten 0.1 m red bands on alternate segments (flag_pole_red), a gold
                  ball on top to y 1.03 (flag_gold) and two gold clips. Child "flag": a pennant, pivot on the pole
                  axis at y 0.83; the hoist spans y 0.72..0.94 at x 0.014, the point is at x 0.334, y 0.83 (it
                  flies along +X, flat in the XY plane). A 12 x 6 quad grid with UVs (U = 0 at the pole, 1 at the
                  point; V = 0 bottom, 1 top) for a waving vertex shader. flag_cloth (warm yellow, double sided).
bumper.glb        root "bumper": a mushroom bumper 0.2 tall. The red rubber ring (bumper_rubber) is a torus centred
                  at y 0.05, outer radius 0.18 (the physics radius, the widest part). Chrome skirt and dome
                  (bumper_chrome, dome from y 0.13 to 0.2, radius 0.15), a dark body (bumper_body), a ring of eight
                  glowing inset lights on the dome and eight on the body, plus a centre jewel (bumper_glow).
putter.glb        root "putter". Origin: centre of the bottom of the head. The head is a blade 0.025 thick along X,
                  0.11 long along Z (heel at z -0.055, toe at z +0.055), 0.03 tall, brushed steel
                  (putter_steel) with a brass face insert (putter_brass) on its +X side: the face points Godot +X,
                  the swing direction. A white sight line on top. A plumber's-neck hosel at the heel (z -0.045) and
                  a chrome shaft (putter_chrome) in the YZ plane, leaning 12 degrees from vertical towards -Z; a
                  black rubber grip (putter_grip) on the top 0.25 m. The butt end is at y 0.90, z -0.23.
spinner.glb       root "spinner": a brass post (spinner_brass) of radius 0.05 with a flange, a red painted cap
                  (spinner_paint) to y 0.30 and a brass knob; a bar through it at ball height, centre y 0.06,
                  x -0.36..+0.36, 0.05 thick (Z) x 0.07 tall (y 0.025..0.095), painted in cream and red stripes
                  (spinner_stripe_a, spinner_stripe_b) with brass end caps. Spin the whole node about Y.
tree_round.glb    root "tree_round": a broad deciduous tree, 4.6 tall, crown ~3.6 across, trunk with root flares
                  and branches (tree_bark), clumped leaf crowns in two greens (tree_leaf_a, tree_leaf_b). ~10k tris.
tree_tall.glb     root "tree_tall": a slender tree 6.2 tall, crown ~2.1 across, pale bark (tree_bark_pale). ~8k.
tree_cypress.glb  root "tree_cypress": an Italian cypress 5.1 tall, 1.3 across, tufted flame-shaped foliage
                  (cypress_leaf_a, cypress_leaf_b) on a short trunk. ~5.5k. (The trees' roots dip to y -0.25.)
bush.glb          two roots at the origin, "bush_a" (0.62 across, 0.55 tall, pink flowers: bush_flower_pink) and
                  "bush_b" (0.72 across, 0.5 tall, white flowers: bush_flower_white); leaves bush_leaf, bush_leaf_b.
                  Use one per spot. ~4.5k / 5.3k tris (most of it the flowers).
hedge_block.glb   root "hedge": a clipped box hedge 1.0 (X) x 0.6 (Y, height) x 0.5 (Z), lumpy leafy surface that
                  stays inside those bounds (hedge_leaf), flat bottom. Tiles side by side along X: the X ends are
                  flat at +-0.5 and the lumps repeat every 1.0 along X, so butted blocks show no seam. ~4.8k tris.
bench.glb         root "bench": a park bench 1.4 long (X), 0.56 deep, 0.83 tall; varnished wood slats (bench_wood),
                  cast iron ends with scrolled arm rests (bench_iron). The seat faces +Z.
gazebo.glb        root "gazebo": an octagonal gazebo, deck 2.9 across the flats (y 0..0.225), eaves 3.2 across,
                  3.55 tall to the finial. Eight white posts (gazebo_white) with railings on seven sides, the open
                  side and two stone steps (gazebo_stone) facing +Z; deck planks (gazebo_deck); fretwork valances;
                  a shingled roof (gazebo_shingle) with ridge caps and a louvred cupola (gazebo_trim); string lights
                  sagging along the eaves (gazebo_bulb_glow bulbs, gazebo_wire); the paper lantern hanging inside
                  from the ceiling (its hook at y 2.2). ~17.7k tris.
fountain.glb      root "fountain": a round two-tier stone fountain 1.44 across (fountain_stone, fountain_stone_wet
                  inside the bowls, fountain_brass spout). Lower basin: inner radius 0.60, inner floor y 0.12, rim
                  top y 0.44 (water surface about y 0.37). Upper bowl: inner radius 0.28, floor y 0.84, scalloped rim
                  top y 0.93 (water about y 0.9). The spout's tip is at y 1.18.
rock_a.glb, rock_b.glb  roots "rock_a" (0.55 x 0.45, 0.36 tall) and "rock_b" (0.5 x 0.4, 0.26 tall, flatter):
                  garden rocks (rock_stone) with moss on their tops (rock_moss), flat bottoms at y 0.
lily_pad.glb      two roots at the origin: "pad" (a notched pad 0.25 across, 0.012 thick, lily_pad) and "lily"
                  (a water-lily ~0.095 across, 0.046 tall: lily_petal white outer petals, lily_petal_pink inner,
                  lily_heart yellow stamens). Place the lily on a pad (or alone).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blastyard_models as K
from blastyard_models import mat, cyl, sphere, torus, rod, tube, prism, join, export, reset, finish

TAU = 2 * math.pi
PI8 = math.pi / 8


# ------------------------------------------------------------------ helpers

def box(size, loc, material, rot=(0, 0, 0), bevel=None, segs=1, smooth=35):
    """K.box with a single-segment bevel by default (a chamfer: small parts stay light)."""
    return K.box(size, loc, material, rot=rot, bevel=bevel, segs=segs, smooth=smooth)


def ico(r, loc, material, scale=(1, 1, 1), sub=2, rot=(0, 0, 0), smooth=80):
    """K.ico; note Blender's subdivisions count from 1 (1 = 20 faces, 2 = 80, 3 = 320, 4 = 1280)."""
    return K.ico(r, loc, material, scale=scale, sub=sub, rot=rot, smooth=smooth)

def link(me, name):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def new_obj(bm, name, material, smooth=60, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = finish(link(me, name), material, smooth=smooth)
    for m in mats:
        o.data.materials.append(m)
    return o


def lathe(profile, material, segs=24, phase=0.0, shape=None, name="lathe", smooth=60, mats=(), mat_fn=None, sx=1.0):
    """Surface of revolution about Z through (r, z) pairs. Walk the profile so the outside is on your right when
    looking along +tangent (top to bottom for a convex body, inner floor outwards for a bowl): normals then face out.
    shape(a, k, i, r, z) -> (radius multiplier, dz) deforms ring i; mat_fn(i) picks the material of band i;
    sx stretches X (for stretched octagons)."""
    bm = bmesh.new()
    rings = []
    for i, (r, z) in enumerate(profile):
        if r < 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for k in range(segs):
            a = phase + TAU * k / segs
            m, dz = shape(a, k, i, r, z) if shape else (1.0, 0.0)
            ring.append(bm.verts.new((r * m * math.cos(a) * sx, r * m * math.sin(a), z + dz)))
        rings.append(ring)
    for i, (r0, r1) in enumerate(zip(rings, rings[1:])):
        for k in range(segs):
            q = [r0[k % len(r0)], r1[k % len(r1)], r1[(k + 1) % len(r1)], r0[(k + 1) % len(r0)]]
            q = [v for j, v in enumerate(q) if v not in q[:j]]
            if len(q) >= 3:
                f = bm.faces.new(q)
                if mat_fn:
                    f.material_index = mat_fn(i)
    return new_obj(bm, name, material, smooth, mats)


def poly_r(a, n, phase=0.0):
    """Radius multiplier of a regular n-gon of unit flat radius whose flats face phase + k * 2pi/n."""
    step = TAU / n
    dev = ((a - phase + step / 2) % step) - step / 2
    return 1.0 / math.cos(dev)


def place(parts, M):
    for o in K.flatten([parts]):
        o.matrix_world = M @ o.matrix_world
    return parts


def T(v):
    return Matrix.Translation(Vector(v))


def Rz(a):
    return Matrix.Rotation(a, 4, "Z")


def Rx(a):
    return Matrix.Rotation(a, 4, "X")


def Ry(a):
    return Matrix.Rotation(a, 4, "Y")


def clump_point(d, r, c, S, seed, amp, freq, fine):
    off = Vector((seed * 7.13, seed * 3.71, seed * 5.29))
    n1 = noise.noise(d * freq + off)
    n2 = noise.noise(d * freq * 4.7 + off * 1.7)
    n3 = noise.noise(d * freq * 11.0 + off * 2.3)
    p = d * r * (1 + amp * n1 + fine * n2 + fine * 0.6 * n3)
    return Vector(c) + Vector((p.x * S[0], p.y * S[1], p.z * S[2]))


def clump(r, c, material, seed, sub=4, scale=(1, 1, 1), amp=0.22, freq=1.7, fine=0.1, floor=None):
    """A leafy clump: an icosphere pushed in and out by two octaves of noise (lumps, then leaf clusters)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1, location=(0, 0, 0))
    o = K.active()
    for v in o.data.vertices:
        p = clump_point(v.co.normalized(), r, c, scale, seed, amp, freq, fine)
        if floor is not None:
            p.z = max(p.z, floor)
        v.co = p
    o.data.update()
    return finish(o, material, smooth=80)


def flower_bumps(n, r, c, S, seed, amp, freq, fine, mats, rnd, size=0.022, zmin=-0.2):
    """n small flower bumps sitting on the surface of a clump built with the same parameters."""
    out = []
    for k in range(n):
        a = rnd.uniform(0, TAU)
        e = rnd.uniform(zmin, 1.2)
        d = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))).normalized()
        p = clump_point(d, r, c, S, seed, amp, freq, fine)
        o = ico(size * rnd.uniform(0.8, 1.2), p, mats[k % len(mats)], scale=(1, 1, 0.7), sub=2)
        out.append(o)
    return out


def ring_band(z_top, z_bot, r_in, r_out, material, segs=8, phase=PI8, sx=1.0, smooth=30):
    """A closed band (a beam around a polygon): r are vertex radii."""
    return lathe([(r_in, z_top), (r_out, z_top), (r_out, z_bot), (r_in, z_bot), (r_in, z_top)], material, segs, phase,
                 smooth=smooth, sx=sx)


def flowers_row(x0, x1, y, z, rnd, petals, leaf, n=6):
    parts = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n + rnd.uniform(-0.01, 0.01)
        parts.append(ico(0.026, (x, y + rnd.uniform(-0.01, 0.01), z + 0.012), leaf, scale=(1.2, 1.0, 0.8), sub=1))
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.2 + 0.6 * rnd.random()) / n
        parts.append(ico(0.018, (x, y + rnd.uniform(-0.02, 0.02), z + 0.035 + rnd.uniform(0, 0.012)),
                         petals[k % len(petals)], scale=(1, 1, 0.75), sub=1))
    return parts


def flower_mats():
    return (mat("flower_red", (0.8, 0.08, 0.06), 0.5), mat("flower_pink", (0.95, 0.42, 0.6), 0.5),
            mat("flower_yellow", (1.0, 0.72, 0.1), 0.5), mat("flower_leaf", (0.1, 0.28, 0.06), 0.65))


# ------------------------------------------------------------------ windmill

SX = 1.7                     # the tower is 1.7x wider (X) than deep (Z)
TZ0, TZ1 = 0.52, 1.62        # tower foot and eaves
TR0, TR1 = 0.235, 0.18       # flat radius (depth half) at foot and top
PIVOT = Vector((0, -0.33, 1.05))   # Blender coordinates of the blades' hub (Godot z = +0.33)


def trf(z):
    return TR0 + (TR1 - TR0) * (z - TZ0) / (TZ1 - TZ0)


def tcorner(k, z, out=0.0):
    a = PI8 + k * math.pi / 4
    r = (trf(z) + out) / math.cos(PI8)
    return Vector((r * math.cos(a) * SX, r * math.sin(a), z))


def on_tower(parts, a, z, out=0.0):
    """Moves parts built on the XZ plane facing -Y (centred at the origin) onto the tower face whose outward
    direction is angle a (0 = +X, pi/2 = +Y, -pi/2 = -Y), centred at height z."""
    side = abs(math.cos(a)) > 0.5
    f = SX if side else 1.0
    tau = math.atan((TR0 - TR1) * f / (TZ1 - TZ0))
    M = Rz(a + math.pi / 2) @ T((0, -(trf(z) * f + out), z)) @ Rx(-tau)
    return place(parts, M)


def window(a, z, w, h, M, flowers=False, shutters=True, oculus=False, rnd=None):
    timber, glow, sill_m, paint, wood = M["timber"], M["glow"], M["plaster_dark"], M["paint"], M["box"]
    parts = []
    if oculus:
        parts.append(cyl(w / 2, 0.02, (0, 0.004, 0), glow, rot=(math.pi / 2, 0, 0), verts=20))
        parts.append(torus(w / 2 + 0.008, 0.012, (0, -0.004, 0), timber, rot=(math.pi / 2, 0, 0), verts=20, minor=6))
        parts.append(box((w, 0.012, 0.01), (0, -0.004, 0), timber, bevel=0.002))
        parts.append(box((0.01, 0.012, w), (0, -0.004, 0), timber, bevel=0.002))
    else:
        parts.append(box((w, 0.02, h), (0, 0.006, 0), glow, bevel=0.0))
        t = 0.018
        parts += [box((w + 2 * t, 0.028, t), (0, -0.006, s * (h / 2 + t / 2)), timber, bevel=0.004) for s in (-1, 1)]
        parts += [box((t, 0.028, h), (s * (w / 2 + t / 2), -0.006, 0), timber, bevel=0.004) for s in (-1, 1)]
        parts.append(box((0.008, 0.012, h), (0, -0.002, 0), timber, bevel=0.002))
        parts.append(box((w, 0.012, 0.008), (0, -0.002, h * 0.12), timber, bevel=0.002))
        parts.append(box((w + 0.07, 0.04, 0.018), (0, -0.016, -h / 2 - t - 0.006), sill_m, bevel=0.005))
        if shutters:
            for s in (-1, 1):
                x = s * (w / 2 + t + w / 4 + 0.008)
                parts.append(box((w / 2, 0.012, h + 0.01), (x, -0.012, 0), paint, bevel=0.003))
                for zz in (-h * 0.3, h * 0.3):
                    parts.append(box((w / 2 - 0.012, 0.006, 0.012), (x, -0.02, zz), paint, bevel=0.002))
    if flowers:
        zb = -h / 2 - 0.07
        parts.append(box((w + 0.08, 0.06, 0.055), (0, -0.04, zb), wood, bevel=0.008))
        parts.append(box((w + 0.06, 0.045, 0.01), (0, -0.04, zb + 0.026), M["soil"], bevel=0.0))
        parts += flowers_row(-w / 2 - 0.03, w / 2 + 0.03, -0.04, zb + 0.02, rnd, M["petals"], M["leaf"],
                             n=max(3, int((w + 0.08) / 0.045)))
    return on_tower(parts, a, z)


def door(M):
    paint, timber, brass, glow = M["door"], M["timber"], M["brass"], M["glow"]
    w, h = 0.13, 0.3
    parts = []
    for k in range(3):
        x = -w / 2 + w / 6 + k * w / 3
        parts.append(box((w / 3 - 0.004, 0.016, h), (x, 0.004, 0), paint, bevel=0.003))
    for zz in (-h * 0.3, h * 0.3):
        parts.append(box((w - 0.01, 0.008, 0.02), (0, -0.007, zz), paint, bevel=0.002))
    parts.append(box((0.012, 0.008, h * 0.62), (0, -0.007, 0), paint, rot=(0, 0.42, 0), bevel=0.002))
    t = 0.018
    parts += [box((t, 0.03, h + t), (s * (w / 2 + t / 2), -0.006, t / 2), timber, bevel=0.004) for s in (-1, 1)]
    parts.append(box((w + 2 * t + 0.02, 0.034, 0.024), (0, -0.008, h / 2 + 0.012), timber, bevel=0.005))
    parts.append(sphere(0.008, (w * 0.32, -0.012, 0), brass, segs=8, rings=5))
    # a little lamp over the door
    parts.append(box((0.012, 0.03, 0.012), (0, -0.02, h / 2 + 0.05), M["iron"], bevel=0.002))
    parts.append(cyl(0.016, 0.03, (0, -0.042, h / 2 + 0.035), glow, verts=8))
    parts.append(cyl(0.022, 0.012, (0, -0.042, h / 2 + 0.056), M["iron"], r2=0.008, verts=8))
    return on_tower(parts, 0.0, TZ0 + 0.005 + h / 2)


def rail_run(p0, p1, z0, M, n_bal):
    """A little white railing from p0 to p1 (xy) standing on z0."""
    p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    mid = (p0 + p1) / 2
    parts = [box((L + 0.02, 0.022, 0.018), (mid.x, mid.y, z0 + 0.18), M["rail"], rot=(0, 0, ang), bevel=0.005),
             box((L, 0.016, 0.012), (mid.x, mid.y, z0 + 0.03), M["rail"], rot=(0, 0, ang), bevel=0.003)]
    for p in (p0, p1):
        parts.append(box((0.026, 0.026, 0.19), (p.x, p.y, z0 + 0.095), M["rail"], bevel=0.005))
        parts.append(sphere(0.016, (p.x, p.y, z0 + 0.2), M["rail"], segs=8, rings=5))
    for k in range(1, n_bal):
        p = p0 + d * (k / n_bal)
        parts.append(box((0.01, 0.01, 0.14), (p.x, p.y, z0 + 0.105), M["rail"], bevel=0.0))
    return parts


def pot(x, y, z, M, rnd):
    parts = [cyl(0.05, 0.07, (x, y, z + 0.035), M["pot"], r2=0.062, verts=14, bevel=0.006),
             torus(0.062, 0.008, (x, y, z + 0.07), M["pot"], verts=14, minor=4),
             cyl(0.055, 0.01, (x, y, z + 0.066), M["soil"], verts=12)]
    for k in range(5):
        a = k * TAU / 5 + rnd.uniform(-0.3, 0.3)
        parts.append(ico(0.035, (x + 0.03 * math.cos(a), y + 0.03 * math.sin(a), z + 0.1), M["leaf"],
                         scale=(1, 1, 0.8), sub=2))
    for k in range(6):
        a = k * TAU / 6 + 0.4
        parts.append(ico(0.018, (x + 0.045 * math.cos(a), y + 0.045 * math.sin(a), z + 0.13 + rnd.uniform(0, 0.02)),
                         M["petals"][k % 3], scale=(1, 1, 0.75), sub=2))
    return parts


def windmill():
    rnd = random.Random(26)
    red, pink, yellow, leaf = flower_mats()
    M = dict(
        stone=mat("mill_stone", (0.52, 0.47, 0.41), 0.82, coat=0.05),
        stone_dark=mat("mill_stone_dark", (0.33, 0.3, 0.27), 0.85),
        plaster=mat("mill_plaster", (0.86, 0.79, 0.64), 0.78),
        plaster_dark=mat("mill_sill", (0.7, 0.64, 0.54), 0.75),
        timber=mat("mill_timber", (0.12, 0.075, 0.045), 0.6, coat=0.3),
        roof=mat("mill_roof_tile", (0.52, 0.11, 0.06), 0.5, coat=0.35),
        ridge=mat("mill_roof_ridge", (0.34, 0.07, 0.04), 0.5, coat=0.35),
        glow=mat("mill_window_glow", (1.0, 0.7, 0.36), 0.4, emit=3.0),
        paint=mat("mill_shutter", (0.16, 0.34, 0.27), 0.4, coat=0.6),
        door=mat("mill_door", (0.18, 0.36, 0.28), 0.4, coat=0.6),
        rail=mat("mill_rail", (0.88, 0.85, 0.78), 0.45, coat=0.5),
        brass=mat("mill_brass", (0.86, 0.63, 0.28), 0.28, 1.0),
        iron=mat("mill_iron", (0.08, 0.08, 0.08), 0.5, 0.7),
        box=mat("mill_box_wood", (0.36, 0.2, 0.1), 0.6, coat=0.3),
        soil=mat("mill_soil", (0.12, 0.08, 0.05), 0.95),
        pot=mat("mill_pot", (0.62, 0.3, 0.17), 0.7),
        petals=(red, pink, yellow), leaf=leaf)
    stone, stone_dark, timber = M["stone"], M["stone_dark"], M["timber"]
    parts = []

    # --- the plinth, with the tunnel: a U-shaped outline (open at the floor) extruded along the lane
    arch = [(0.25 * math.cos(t), 0.2 + 0.1 * math.sin(t)) for t in (math.pi * (1 - j / 14) for j in range(15))]
    poly = [(-0.72, 0.0), (-0.25, 0.0)] + arch + [(0.25, 0.0), (0.72, 0.0), (0.72, 0.46), (-0.72, 0.46)]
    parts.append(prism(poly, 0.44, (0, 0, 0), stone, bevel=0.008, segs=1))
    # cornice slab (full footprint) and plinth band at the foot (split by the tunnel)
    parts.append(box((1.5, 0.5, 0.06), (0, 0, 0.49), stone_dark, bevel=0.015))
    parts.append(box((1.46, 0.46, 0.02), (0, 0, 0.45), stone, bevel=0.006))
    for s in (-1, 1):
        parts.append(box((0.49, 0.5, 0.07), (s * 0.495, 0, 0.035), stone_dark, bevel=0.015))
    # quoins at the four corners, alternating long and short
    for sx in (-1, 1):
        for sy in (-1, 1):
            for j in range(4):
                z = 0.07 + 0.0975 * j + 0.047
                lx, ly = (0.16, 0.1) if j % 2 == 0 else (0.1, 0.16)
                parts.append(box((lx, ly, 0.09), (sx * (0.75 - lx / 2), sy * (0.25 - ly / 2), z), M["plaster_dark"],
                                 bevel=0.012, segs=1))
    # arch stones and jambs on both faces (they stop at the arch line, the tunnel stays clear)
    for sy in (-1, 1):
        y = sy * 0.235
        for j in range(9):
            t = math.pi * (1 - (j + 0.5) / 9)
            p = Vector((0.25 * math.cos(t), 0, 0.2 + 0.1 * math.sin(t)))
            n = Vector((math.cos(t) / 0.25, 0, math.sin(t) / 0.1)).normalized()
            size = 0.13 if j == 4 else 0.1
            c = p + n * (size / 2 + 0.002)
            th = math.atan2(n.x, n.z)
            parts.append(box((0.058, 0.03, size), (c.x, y, c.z), stone if j != 4 else M["plaster_dark"],
                             rot=(0, th, 0), bevel=0.008, segs=1))
        for s in (-1, 1):
            for j, (z0, z1) in enumerate(((0.07, 0.14), (0.14, 0.2))):
                wx = 0.07 if j == 0 else 0.1
                parts.append(box((wx, 0.03, z1 - z0 - 0.004), (s * (0.25 + wx / 2 + 0.002), y, (z0 + z1) / 2),
                                 stone, bevel=0.008, segs=1))

    # --- the tower: a stretched octagon in plaster with timber framing
    rv = lambda rf: rf / math.cos(PI8)
    parts.append(lathe([(0, TZ1), (rv(TR1), TZ1), (rv(TR0), TZ0), (0, TZ0)], M["plaster"], 8, PI8, smooth=30,
                       sx=SX, name="tower"))
    for k in range(8):
        parts.append(rod(tcorner(k, TZ0, -0.006), tcorner(k, TZ1, -0.006), 0.017, timber, verts=6))
    for z, h in ((TZ0 + 0.03, 0.025), (1.0, 0.02), (TZ1 - 0.03, 0.03)):
        rf = trf(z)
        parts.append(ring_band(z + h, z - h, rv(rf - 0.01), rv(rf + 0.012), timber, sx=SX))
    # X braces on the four diagonal faces, lower and upper panels
    for k in (0, 2, 4, 6):
        for zlo, zhi in ((TZ0 + 0.06, 0.975), (1.025, TZ1 - 0.065)):
            def fp(u, z):
                return tcorner(k, z, 0.004).lerp(tcorner(k + 1, z, 0.004), u)
            parts.append(rod(fp(0.12, zlo), fp(0.88, zhi), 0.011, timber, verts=6))
            parts.append(rod(fp(0.88, zlo), fp(0.12, zhi), 0.011, timber, verts=6))
    # windows, door, bearing block
    parts += window(-math.pi / 2, 1.38, 0.12, 0.12, M, oculus=True)
    parts += window(math.pi / 2, 0.78, 0.11, 0.15, M, flowers=True, rnd=rnd)
    parts += window(math.pi / 2, 1.3, 0.1, 0.13, M)
    parts += window(0.0, 1.3, 0.09, 0.13, M, flowers=True, shutters=False, rnd=rnd)
    parts += window(math.pi, 0.8, 0.09, 0.14, M, shutters=False)
    parts += window(math.pi, 1.3, 0.09, 0.13, M, flowers=True, shutters=False, rnd=rnd)
    parts += door(M)
    parts.append(box((0.13, 0.05, 0.13), (0, -trf(PIVOT.z) - 0.012, PIVOT.z), timber, bevel=0.012))
    parts.append(cyl(0.04, 0.02, (0, -trf(PIVOT.z) - 0.045, PIVOT.z), M["brass"], rot=(math.pi / 2, 0, 0), verts=16,
                     bevel=0.004))

    # --- the cap roof: tile courses (a sawtooth profile) on a stretched octagon, corrugated into tiles
    ZT, ZE, RE = 2.235, 1.62, 0.265
    rr = lambda z: RE * max(0.0, (ZT - z) / (ZT - ZE)) ** 0.85
    B = [ZT - (ZT - ZE) * j / 7 for j in range(8)]
    prof = [(0, ZT)]
    for j in range(1, 8):
        prof.append((rr(B[j]) + 0.013, B[j] - 0.004))
        if j < 7:
            prof.append((rr(B[j]), B[j]))
    prof += [(RE + 0.013, ZE - 0.02), (RE - 0.03, ZE - 0.02), (0.12, ZE - 0.02)]
    n_tile = len(prof) - 4

    def tiles(a, k, i, r, z):
        m = poly_r(a, 8)
        if 0 < i <= n_tile:
            m *= 1.0 + 0.02 * (k % 2)
        return m, 0.0
    parts.append(lathe(prof, M["roof"], 64, 0.0, shape=tiles, smooth=50, sx=SX, name="roof",
                       mats=(M["timber"],), mat_fn=lambda i: 1 if i >= len(prof) - 3 else 0))
    for k in range(8):
        a = PI8 + k * math.pi / 4
        pts, rads = [], []
        for j in range(8):
            z = ZT - 0.02 - (ZT - 0.02 - ZE) * j / 7
            R = (rr(z) + 0.016) / math.cos(PI8)
            pts.append((R * math.cos(a) * SX, R * math.sin(a), z + 0.008))
            rads.append(0.013)
        parts.append(tube(pts, rads, M["ridge"], verts=6))
    parts.append(sphere(0.03, (0, 0, ZT + 0.015), M["brass"], segs=12, rings=8))
    parts.append(rod((0, 0, ZT + 0.04), (0, 0, 2.32), 0.008, M["brass"], r2=0.002, verts=8))
    parts.append(sphere(0.012, (0, 0, 2.3), M["brass"], segs=8, rings=6))

    # --- balconies at both ends of the plinth, a pot of flowers on each
    for s in (-1, 1):
        x0, x1 = s * 0.43, s * 0.72
        parts += rail_run((x1, -0.225), (x1, 0.225), 0.52, M, 6)
        parts += rail_run((x0, -0.225), (x1, -0.225), 0.52, M, 4)
        parts += rail_run((x0, 0.225), (x1, 0.225), 0.52, M, 4)
        parts += pot(s * 0.6, 0.1, 0.52, M, rnd)
    root = join(parts, "windmill")

    # --- the blades: built around the hub with one blade pointing up, then turned by quarter turns about Y
    sail_wood = mat("mill_sail_wood", (0.4, 0.27, 0.16), 0.6, coat=0.25)
    canvas = mat("mill_sail_canvas", (0.9, 0.85, 0.72), 0.85)
    canvas.use_backface_culling = False
    bl = []
    for q in range(4):
        b = [box((0.034, 0.03, 0.95), (0, 0, 0.03 + 0.475), sail_wood, bevel=0.006),
             box((0.016, 0.02, 0.76), (0.215, 0, 0.58), sail_wood, bevel=0.004),
             box((0.01, 0.012, 0.74), (0.11, -0.004, 0.58), sail_wood, bevel=0.002),
             box((0.19, 0.003, 0.73), (0.11, 0.008, 0.58), canvas, bevel=0.0),
             box((0.055, 0.01, 0.7), (-0.045, 0.004, 0.6), sail_wood, bevel=0.003)]
        for j in range(10):
            z = 0.21 + 0.745 * j / 9
            b.append(box((0.215, 0.014, 0.012), (0.1, -0.006, z), sail_wood, bevel=0.0))
        b.append(box((0.03, 0.028, 0.03), (0, 0, 0.965), M["iron"], bevel=0.006))
        place(b, Ry(q * math.pi / 2))
        bl += b
    bl.append(cyl(0.065, 0.07, (0, 0.0, 0), M["timber"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01, segs=2))
    bl.append(cyl(0.022, 0.13, (0, 0.07, 0), M["iron"], rot=(math.pi / 2, 0, 0), verts=12))
    bl.append(cyl(0.05, 0.03, (0, -0.045, 0), M["brass"], rot=(math.pi / 2, 0, 0), r2=0.02, verts=16, bevel=0.004))
    bl.append(sphere(0.018, (0, -0.062, 0), M["brass"], segs=10, rings=6))
    for q in range(4):   # bolts on the hub
        a = q * math.pi / 2 + math.pi / 4
        bl.append(sphere(0.008, (0.045 * math.cos(a), -0.036, 0.045 * math.sin(a)), M["iron"], segs=6, rings=4))
    place(bl, T(PIVOT))
    blades = join(bl, "blades", pivot=PIVOT)
    export(root, "windmill", [(blades, root)])


# ------------------------------------------------------------------ lanterns

def lantern_parts(top):
    """The round paper lantern hanging from `top` (the top of its hook ring)."""
    paper = mat("lantern_paper_glow", (1.0, 0.68, 0.38), 0.6, emit=2.5)
    wood = mat("lantern_wood", (0.12, 0.07, 0.04), 0.5, coat=0.4)
    wire = mat("lantern_wire", (0.22, 0.2, 0.17), 0.4, 0.8)
    cord = mat("lantern_tassel", (0.72, 0.1, 0.07), 0.85)
    t = Vector(top)
    cz = t.z - 0.21
    parts = [torus(0.011, 0.0035, (0, 0, t.z - 0.0145), wire, rot=(math.pi / 2, 0, 0), verts=12, minor=4),
             rod((0, 0, t.z - 0.026), (0, 0, t.z - 0.055), 0.0035, wire, verts=6)]
    N = 36
    prof = []
    for j in range(N + 1):
        z = 0.141 - 0.282 * j / N
        r = 0.16 * math.sqrt(max(0.0, 1 - (z / 0.15) ** 2))
        if j % 3 == 0 and 0 < j < N:
            r *= 0.968
        prof.append((r, cz + z))
    paper_o = lathe(prof, paper, 20, name="paper", smooth=70)
    paper_o.data.materials[0].use_backface_culling = False
    parts.append(paper_o)
    # caps: short wooden drums with a rim
    for zc, sgn, rc in ((cz + 0.145, 1, 0.062), (cz - 0.145, -1, 0.068)):
        parts.append(lathe([(0, zc + 0.016 * sgn), (rc - 0.008, zc + 0.016 * sgn), (rc, zc + 0.01 * sgn),
                            (rc, zc - 0.006 * sgn), (rc - 0.015, zc - 0.014 * sgn), (0, zc - 0.014 * sgn)][::sgn],
                           wood, 16, smooth=40))
    parts.append(rod((0, 0, cz - 0.16), (0, 0, cz - 0.19), 0.003, cord, verts=6))
    parts.append(sphere(0.012, (0, 0, cz - 0.196), wood, segs=10, rings=6))
    parts.append(lathe([(0, cz - 0.205), (0.008, cz - 0.206), (0.014, cz - 0.22), (0.019, cz - 0.255),
                        (0.017, cz - 0.262), (0, cz - 0.262)], cord, 12, smooth=60))
    for o in parts:
        o.location += Vector((t.x, t.y, 0))
    return parts


def paper_lantern():
    export(join(lantern_parts((0, 0, 0)), "paper_lantern"), "paper_lantern")


def lantern_post():
    wood = mat("post_wood", (0.3, 0.19, 0.11), 0.6, coat=0.3)
    stone = mat("post_stone", (0.5, 0.47, 0.43), 0.85)
    iron = mat("post_iron", (0.1, 0.09, 0.08), 0.45, 0.8)
    parts = [box((0.28, 0.28, 0.1), (0, 0, 0.05), stone, bevel=0.03, segs=2),
             box((0.2, 0.2, 0.06), (0, 0, 0.12), stone, bevel=0.02, segs=2),
             box((0.12, 0.12, 0.08), (0, 0, 0.18), iron, bevel=0.008, segs=1),
             box((0.09, 0.09, 1.9 - 0.14), (0, 0, 0.14 + (1.9 - 0.14) / 2), wood, bevel=0.012, segs=1),
             box((0.11, 0.11, 0.025), (0, 0, 1.9), wood, bevel=0.006, segs=1),
             cyl(0.075, 0.04, (0, 0, 1.93), wood, r2=0.0, verts=4, rot=(0, 0, math.pi / 4)),
             # the arm, its end block and a brace
             box((0.46, 0.05, 0.05), (0.23, 0, 1.86), wood, bevel=0.008, segs=1),
             box((0.06, 0.06, 0.06), (0.44, 0, 1.86), wood, bevel=0.01, segs=1),
             box((0.3, 0.04, 0.035), (0.14, 0, 1.73), wood, rot=(0, math.radians(-45), 0), bevel=0.006, segs=1),
             # iron straps where the arm meets the post
             box((0.1, 0.1, 0.018), (0, 0, 1.79), iron, bevel=0.003, segs=1),
             box((0.052, 0.056, 0.012), (0.36, 0, 1.86), iron, bevel=0.002, segs=1),
             # the hook
             rod((0.4, 0, 1.836), (0.4, 0, 1.826), 0.004, iron, verts=6),
             torus(0.009, 0.0025, (0.4, 0, 1.826), iron, rot=(0, 0, 0), verts=10, minor=4)]
    root = join(parts, "lantern_post")
    lan = join(lantern_parts((0.4, 0, 1.82)), "lantern", pivot=(0.4, 0, 1.82))
    export(root, "lantern_post", [(lan, root)])


def stone_lantern():
    stone = mat("stone_lantern_stone", (0.52, 0.5, 0.46), 0.85)
    moss = mat("stone_lantern_moss", (0.2, 0.3, 0.1), 0.9)
    glow = mat("stone_lantern_glow", (1.0, 0.72, 0.4), 0.6, emit=2.5)
    wood = mat("stone_lantern_wood", (0.14, 0.08, 0.05), 0.6)
    H = math.pi / 6   # hexagons with flats at pi/6 + k pi/3 (a corner at +X)
    hexs = lambda rf: (lambda a, k, i, r, z: (poly_r(a, 6, H), 0.0))
    parts = []
    # footing: two hexagonal steps
    parts.append(lathe([(0, 0.1), (0.17, 0.1), (0.19, 0.08), (0.2, 0.06), (0.2, 0.0), (0, 0.0)], stone, 6, 0.0,
                       shape=hexs(1), smooth=30))
    parts.append(lathe([(0, 0.13), (0.12, 0.13), (0.14, 0.11), (0.14, 0.1), (0, 0.1)], stone, 6, 0.0,
                       shape=hexs(1), smooth=30))
    # round pillar with two rings
    parts.append(lathe([(0, 0.44), (0.07, 0.44), (0.075, 0.42), (0.065, 0.3), (0.07, 0.16), (0.085, 0.14),
                        (0.085, 0.13), (0, 0.13)], stone, 20, smooth=50))
    parts.append(torus(0.068, 0.008, (0, 0, 0.405), stone, verts=20, minor=5))
    # platform (the middle hexagon)
    parts.append(lathe([(0, 0.51), (0.15, 0.51), (0.17, 0.495), (0.17, 0.47), (0.1, 0.44), (0, 0.44)], stone, 6,
                       0.0, shape=hexs(1), smooth=30))
    # the fire box: six glowing paper panels, stone corner posts, a lattice
    parts.append(lathe([(0, 0.7), (0.105, 0.7), (0.105, 0.51), (0, 0.51)], glow, 6, 0.0, shape=hexs(1), smooth=30))
    for k in range(6):
        a = k * math.pi / 3
        c = Vector((math.cos(a), math.sin(a), 0)) * 0.118
        parts.append(box((0.04, 0.04, 0.19), (c.x, c.y, 0.605), stone, rot=(0, 0, a), bevel=0.008, segs=1))
        fa = a + math.pi / 6
        n = Vector((math.cos(fa), math.sin(fa), 0))
        p = n * (0.105 * math.cos(math.pi / 6) + 0.004)
        parts.append(box((0.008, 0.1, 0.008), (p.x, p.y, 0.62), wood, rot=(0, 0, fa), bevel=0.0))
        parts.append(box((0.008, 0.008, 0.17), (p.x, p.y, 0.605), wood, rot=(0, 0, fa), bevel=0.0))
        if k % 2 == 0:   # a round window cut in a stone panel on alternate sides
            parts.append(torus(0.035, 0.01, (p.x + n.x * 0.004, p.y + n.y * 0.004, 0.6), stone,
                               rot=(math.pi / 2, 0, fa + math.pi / 2), verts=16, minor=4))
    parts.append(lathe([(0, 0.72), (0.14, 0.72), (0.15, 0.71), (0.15, 0.7), (0, 0.7)], stone, 6, 0.0,
                       shape=hexs(1), smooth=30))
    # the roof: concave hexagon with upturned corners, moss on the upper slope

    def roof(a, k, i, r, z):
        m = poly_r(a, 6, H)
        c = ((math.cos(6 * a) + 1) / 2) ** 8
        lift = c * 0.045 * (min(r, 0.3) / 0.3) ** 3 if i <= 7 else 0.0
        return m * (1 + 0.05 * c * (r / 0.3) ** 2), lift
    prof = [(0.045, 0.86), (0.07, 0.845), (0.11, 0.815), (0.16, 0.785), (0.21, 0.762), (0.26, 0.748), (0.3, 0.742),
            (0.31, 0.735), (0.305, 0.722), (0.25, 0.718), (0.16, 0.72), (0.12, 0.72)]
    parts.append(lathe(prof, stone, 48, 0.0, shape=roof, smooth=45, mats=(moss,),
                       mat_fn=lambda i: 1 if i < 3 else 0))
    # finial: a lotus collar and a flame-shaped bud
    parts.append(lathe([(0, 0.955), (0.012, 0.95), (0.03, 0.93), (0.038, 0.905), (0.03, 0.885), (0.02, 0.88),
                        (0.042, 0.875), (0.05, 0.862), (0.045, 0.85), (0, 0.85)], stone, 16, smooth=60))
    export(join(parts, "stone_lantern"), "stone_lantern")


# ------------------------------------------------------------------ flag, bumper, putter, spinner

def flag():
    white = mat("flag_pole_white", (0.9, 0.9, 0.88), 0.3, coat=0.6)
    red = mat("flag_pole_red", (0.72, 0.06, 0.05), 0.3, coat=0.6)
    gold = mat("flag_gold", (0.95, 0.72, 0.3), 0.22, 1.0)
    cloth = mat("flag_cloth", (0.98, 0.7, 0.1), 0.85)
    cloth.use_backface_culling = False
    prof = [(0, 1.0), (0.012, 1.0)] + [(0.012, 1.0 - 0.1 * j) for j in range(1, 11)] + [(0, 0.0)]
    parts = [lathe(prof, white, 12, smooth=50, mats=(red,),
                   mat_fn=lambda i: 1 if 1 <= i <= 10 and (i - 1) % 2 == 1 else 0),
             sphere(0.017, (0, 0, 1.013), gold, segs=14, rings=8)]
    for z in (0.725, 0.935):
        parts.append(cyl(0.016, 0.012, (0, 0, z), gold, verts=12, bevel=0.002))
    root = join(parts, "flagstick")
    # the pennant: a 12 x 6 quad grid with UVs
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    NU, NV = 12, 6
    V = []
    for i in range(NU + 1):
        u = i / NU
        hh = 0.11 * (1 - u) + 0.0015
        V.append([bm.verts.new((0.014 + 0.32 * u, 0, 0.83 + (2 * j / NV - 1) * hh)) for j in range(NV + 1)])
    for i in range(NU):
        for j in range(NV):
            f = bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]))
            for l in f.loops:
                ii = min(range(NU + 1), key=lambda q: abs(0.014 + 0.32 * q / NU - l.vert.co.x))
                l[uv].uv = (ii / NU, (l.vert.co.z - 0.83) / (2 * (0.11 * (1 - ii / NU) + 0.0015)) + 0.5)
    fl = new_obj(bm, "flag", cloth, smooth=80)
    fl.location = (0, 0, 0)
    fl = join([fl], "flag", pivot=(0, 0, 0.83))
    export(root, "flag", [(fl, root)])


def bumper():
    rubber = mat("bumper_rubber", (0.75, 0.04, 0.03), 0.3, coat=1.0)
    chrome = mat("bumper_chrome", (0.9, 0.9, 0.92), 0.08, 1.0)
    body = mat("bumper_body", (0.08, 0.08, 0.1), 0.4, coat=0.5)
    glow = mat("bumper_glow", (1.0, 0.55, 0.25), 0.3, emit=4.0)
    parts = [lathe([(0.11, 0.035), (0.14, 0.03), (0.16, 0.02), (0.166, 0.01), (0.166, 0.0), (0, 0.0)], chrome, 40,
                   smooth=50),
             torus(0.15, 0.03, (0, 0, 0.05), rubber, verts=48, minor=12),
             lathe([(0.13, 0.14), (0.125, 0.135), (0.125, 0.07), (0.13, 0.065)], body, 40, smooth=40),
             lathe([(0, 0.2), (0.04, 0.199), (0.08, 0.194), (0.115, 0.183), (0.14, 0.166), (0.15, 0.152),
                    (0.148, 0.138), (0.13, 0.132), (0.11, 0.132)], chrome, 40, smooth=60)]
    for k in range(8):   # lights round the body under the dome, and on the dome's shoulder
        a = k * TAU / 8 + math.pi / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        parts.append(rod(d * 0.12 + Vector((0, 0, 0.1)), d * 0.131 + Vector((0, 0, 0.1)), 0.012, glow, verts=10))
        p = d * 0.075 + Vector((0, 0, 0.1945))
        tilt = Matrix.Rotation(0.3, 3, Vector((-d.y, d.x, 0)))
        lens = sphere(0.009, (0, 0, 0), glow, scale=(1, 1, 0.35), segs=10, rings=6)
        bez = torus(0.0095, 0.0025, (0, 0, -0.001), chrome, verts=10, minor=4)
        for o in (lens, bez):
            o.data.transform(tilt.to_4x4())
            o.location = p
            parts.append(o)
    parts.append(sphere(0.03, (0, 0, 0.186), glow, scale=(1, 1, 0.45), segs=16, rings=8))
    parts.append(torus(0.032, 0.005, (0, 0, 0.194), chrome, verts=16, minor=4))
    export(join(parts, "bumper"), "bumper")


def putter():
    steel = mat("putter_steel", (0.62, 0.63, 0.65), 0.35, 1.0)
    brass = mat("putter_brass", (0.85, 0.62, 0.3), 0.3, 1.0)
    chrome = mat("putter_chrome", (0.92, 0.92, 0.94), 0.1, 1.0)
    grip = mat("putter_grip", (0.03, 0.03, 0.03), 0.75)
    paint = mat("putter_line", (0.95, 0.95, 0.95), 0.4)
    # Blender: the face looks along +X, heel at Blender +Y (Godot -Z)
    parts = [box((0.025, 0.11, 0.03), (0, 0, 0.015), steel, bevel=0.005, segs=2),
             box((0.003, 0.084, 0.02), (0.0125, 0, 0.015), brass, bevel=0.001, segs=1),
             box((0.012, 0.0016, 0.0012), (0, 0, 0.0302), paint, bevel=0.0),
             box((0.03, 0.016, 0.012), (-0.002, 0.047, 0.006), steel, bevel=0.004, segs=1),   # heel weight
             box((0.03, 0.016, 0.012), (-0.002, -0.047, 0.006), steel, bevel=0.004, segs=1)]  # toe weight
    # plumber's neck: up from the heel, a short jog back, then the shaft
    h0 = Vector((0, 0.045, 0.028))
    h1 = Vector((0, 0.045, 0.05))
    h2 = Vector((-0.012, 0.045, 0.058))
    h3 = Vector((-0.012, 0.047, 0.075))
    parts.append(tube([h0, h1, h2, h3], [0.0055, 0.0055, 0.0055, 0.006], steel, verts=10, caps=False))
    d = Vector((0, math.sin(math.radians(12)), math.cos(math.radians(12))))
    L = 0.843
    top = h3 + d * L
    parts.append(rod(h3, top - d * 0.02, 0.0048, chrome, r2=0.0042, verts=12))
    parts.append(rod(h3 - d * 0.003, h3 + d * 0.02, 0.0065, steel, r2=0.0052, verts=12))
    g0 = top - d * 0.25
    parts.append(rod(g0, top, 0.0105, grip, r2=0.013, verts=14))
    parts.append(sphere(0.013, top, grip, scale=(1, 1, 0.4), segs=14, rings=6))
    parts.append(rod(g0 - d * 0.002, g0 + d * 0.012, 0.0115, brass, verts=14))
    o = join(parts, "putter")
    print("  putter butt end (Blender):", tuple(round(c, 3) for c in top))
    export(o, "putter")


def spinner():
    brass = mat("spinner_brass", (0.86, 0.64, 0.3), 0.28, 1.0)
    paint = mat("spinner_paint", (0.66, 0.08, 0.06), 0.35, coat=0.7)
    sa = mat("spinner_stripe_a", (0.9, 0.84, 0.7), 0.4, coat=0.6)
    sb = mat("spinner_stripe_b", (0.68, 0.08, 0.06), 0.4, coat=0.6)
    parts = [lathe([(0.05, 0.27), (0.05, 0.03), (0.075, 0.018), (0.078, 0.0), (0, 0.0)], brass, 28, smooth=50),
             lathe([(0, 0.3), (0.025, 0.299), (0.045, 0.29), (0.056, 0.278), (0.056, 0.268), (0.045, 0.265)],
                   paint, 28, smooth=60),
             sphere(0.014, (0, 0, 0.305), brass, segs=12, rings=6),
             torus(0.052, 0.006, (0, 0, 0.12), brass, verts=28, minor=5),
             torus(0.052, 0.006, (0, 0, 0.225), brass, verts=28, minor=5)]
    n = 8
    x0, x1 = -0.34, 0.34
    for k in range(n):
        a = x0 + (x1 - x0) * k / n
        b = x0 + (x1 - x0) * (k + 1) / n
        parts.append(box((b - a, 0.05, 0.07), ((a + b) / 2, 0, 0.06), sa if k % 2 == 0 else sb, bevel=0.004, segs=1))
    for s in (-1, 1):
        parts.append(box((0.022, 0.054, 0.074), (s * 0.349, 0, 0.06), brass, bevel=0.007, segs=2))
    export(join(parts, "spinner"), "spinner")


# ------------------------------------------------------------------ trees and shrubs

def leaf_mats():
    return (mat("tree_leaf_a", (0.08, 0.2, 0.045), 0.75), mat("tree_leaf_b", (0.17, 0.29, 0.06), 0.75))


def tree_round():
    bark = mat("tree_bark", (0.2, 0.14, 0.1), 0.9)
    la, lb = leaf_mats()
    parts = [tube([(0, 0, -0.05), (0.03, 0.02, 0.7), (0.0, 0.06, 1.4), (-0.04, 0.05, 1.9)], [0.2, 0.16, 0.14, 0.12],
                  bark, verts=12)]
    for k in range(5):
        a = k * TAU / 5 + 0.4
        parts.append(tube([(0, 0, 0.35), (0.22 * math.cos(a), 0.22 * math.sin(a), 0.08),
                           (0.36 * math.cos(a), 0.36 * math.sin(a), -0.02)], [0.1, 0.06, 0.03], bark, verts=7))
    crowns = [((0.0, 0.0, 3.3), 1.2, 1), ((0.95, 0.3, 2.85), 0.85, 2), ((-0.9, -0.2, 2.95), 0.9, 3),
              ((0.2, -0.9, 2.8), 0.82, 4), ((-0.25, 0.85, 3.05), 0.85, 5), ((0.35, 0.25, 3.95), 0.72, 6),
              ((-0.4, -0.3, 3.8), 0.66, 7)]
    for (c, r, s) in crowns:
        cv = Vector(c)
        start = Vector((-0.04, 0.05, 1.8))
        mid = start.lerp(cv, 0.5) + Vector((0, 0, 0.25))
        if cv.length > 3.35 or abs(cv.x) + abs(cv.y) > 0.3:
            parts.append(tube([start, mid, start.lerp(cv, 0.85)], [0.09, 0.06, 0.035], bark, verts=7))
        parts.append(clump(r, c, la if s % 2 else lb, s, sub=4, scale=(1, 1, 0.82)))
    export(join(parts, "tree_round"), "tree_round")


def tree_tall():
    bark = mat("tree_bark_pale", (0.4, 0.36, 0.31), 0.8)
    la, lb = leaf_mats()
    parts = [tube([(0, 0, -0.05), (0.02, 0.0, 1.5), (-0.03, 0.03, 3.2), (0.0, 0.02, 4.8), (0.02, 0.0, 5.5)],
                  [0.15, 0.12, 0.09, 0.06, 0.03], bark, verts=10)]
    for k in range(4):
        a = k * TAU / 4 + 0.8
        parts.append(tube([(0, 0, 0.3), (0.18 * math.cos(a), 0.18 * math.sin(a), 0.05),
                           (0.28 * math.cos(a), 0.28 * math.sin(a), -0.02)], [0.07, 0.045, 0.025], bark, verts=6))
    crowns = [((0.0, 0.0, 3.0), 0.8, 1), ((0.35, 0.15, 3.7), 0.7, 2), ((-0.3, -0.2, 3.6), 0.72, 3),
              ((0.05, 0.05, 4.5), 0.75, 4), ((-0.15, 0.3, 4.2), 0.6, 5), ((0.1, -0.05, 5.3), 0.62, 6),
              ((0.25, -0.3, 2.6), 0.55, 7), ((-0.3, 0.25, 2.7), 0.5, 8)]
    for (c, r, s) in crowns:
        cv = Vector(c)
        if abs(cv.x) + abs(cv.y) > 0.2:
            base = Vector((0, 0.02, cv.z - 0.7))
            parts.append(tube([base, base.lerp(cv, 0.8)], [0.05, 0.025], bark, verts=6))
        parts.append(clump(r, c, la if s % 2 else lb, 10 + s, sub=4 if r > 0.6 else 3, scale=(1, 1, 1.3)))
    export(join(parts, "tree_tall"), "tree_tall")


def tree_cypress():
    bark = mat("tree_bark", (0.2, 0.14, 0.1), 0.9)
    ca = mat("cypress_leaf_a", (0.035, 0.1, 0.035), 0.78)
    cb = mat("cypress_leaf_b", (0.06, 0.15, 0.045), 0.78)
    parts = [tube([(0, 0, -0.05), (0, 0, 0.6)], [0.12, 0.09], bark, verts=10)]
    # flame outline, sampled bottom-up then reversed for the lathe (top to bottom)
    N = 44
    prof = []
    for j in range(N + 1):
        t = j / N                 # 0 at the top
        z = 5.1 - 4.75 * t
        r = 0.55 * math.sin(math.pi * min(1.0, t * 1.12) ** 0.75) ** 0.9 if t < 1 else 0.3
        r = max(r, 0.0) if j else 0.0
        if j == N:
            r = 0.12
        prof.append((r, z))
    prof.append((0, 0.33))

    def tufts(a, k, i, r, z):
        n = noise.noise(Vector((math.cos(a) * 2.2, math.sin(a) * 2.2, z * 2.6)))
        n2 = noise.noise(Vector((math.cos(a) * 7, math.sin(a) * 7, z * 9)) + Vector((5, 1, 2)))
        return 1 + 0.2 * n + 0.07 * n2, 0.0
    parts.append(lathe(prof, ca, 32, shape=tufts, smooth=80, mats=(cb,), mat_fn=lambda i: (i // 3) % 2))
    rnd = random.Random(7)
    for k in range(9):
        z = 0.9 + 3.4 * k / 8
        t = (5.1 - z) / 4.75
        r = 0.55 * math.sin(math.pi * min(1.0, t * 1.12) ** 0.75) ** 0.9
        a = rnd.uniform(0, TAU)
        parts.append(clump(0.28 * (0.6 + r), (r * 0.8 * math.cos(a), r * 0.8 * math.sin(a), z),
                           ca if k % 2 else cb, 30 + k, sub=3, scale=(0.8, 0.8, 1.5)))
    export(join(parts, "tree_cypress"), "tree_cypress")


def bush_one(name, clumps, flower_m, seed):
    leaf = mat("bush_leaf", (0.08, 0.21, 0.05), 0.75)
    leaf2 = mat("bush_leaf_b", (0.14, 0.28, 0.07), 0.75)
    rnd = random.Random(seed)
    parts = []
    for n, (c, r) in enumerate(clumps):
        s = seed * 10 + n
        parts.append(clump(r, c, leaf if n % 2 else leaf2, s, sub=3, amp=0.2, freq=2.2, fine=0.08, floor=0.0))
        parts += flower_bumps(7, r, c, (1, 1, 1), s, 0.2, 2.2, 0.08, [flower_m], rnd, size=0.022, zmin=0.0)
    return join(parts, name)


def bush():
    pink = mat("bush_flower_pink", (0.95, 0.4, 0.6), 0.5)
    white = mat("bush_flower_white", (0.95, 0.93, 0.88), 0.5)
    a = bush_one("bush_a", [((0, 0, 0.26), 0.26), ((0.14, 0.08, 0.2), 0.18), ((-0.13, 0.06, 0.18), 0.17),
                            ((0.02, -0.14, 0.17), 0.17), ((0.03, 0.02, 0.4), 0.16)], pink, 3)
    b = bush_one("bush_b", [((0, 0, 0.24), 0.27), ((0.2, 0.05, 0.17), 0.18), ((-0.2, -0.02, 0.18), 0.18),
                            ((0.05, 0.18, 0.16), 0.16), ((-0.02, -0.18, 0.15), 0.16), ((0.08, 0, 0.36), 0.15)],
                 white, 4)
    export([a, b], "bush")


def hedge_block():
    leaf = mat("hedge_leaf", (0.07, 0.19, 0.045), 0.78)
    hx, hy, hz = 0.5, 0.25, 0.6          # half X, half depth (Blender Y), full height
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    o = K.active()
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=19, use_grid_fill=True)
    rho = 0.07
    ext = Vector((hx, hy, hz / 2))
    def leafy(w):
        return (0.03 * (0.5 + 0.5 * noise.noise(w * 6.0)) + 0.022 * (0.5 + 0.5 * noise.noise(w * 17.0 + Vector((3, 1, 2))))
                + 0.01 * (0.5 + 0.5 * noise.noise(w * 40.0 + Vector((7, 5, 1)))))
    for v in bm.verts:
        p = Vector((v.co.x * ext.x, v.co.y * ext.y, v.co.z * ext.z))
        # rounded along the length only: the X ends stay flat at +-0.5 so blocks butt together
        inner = Vector((p.x, max(-(ext.y - rho), min(ext.y - rho, p.y)), max(-(ext.z - rho), min(ext.z - rho, p.z))))
        d = p - inner
        if d.length < 1e-6:          # the flat end faces: left as they are
            v.co = p + Vector((0, 0, hz / 2))
            continue
        n = d.normalized()
        q = inner + n * rho
        w = q + Vector((0, 0, hz / 2))
        t = (w.x + hx) / (2 * hx)    # blend with the noise one block over: periodic along X, no seams
        amt = leafy(w) * (1 - t) + leafy(w - Vector((2 * hx, 0, 0))) * t
        if v.co.z < -0.999:
            n = Vector((n.x, n.y, 0))
            amt *= 0.4
            w.z = 0.0
        v.co = w - n * amt
    bm.to_mesh(o.data)
    bm.free()
    finish(o, leaf, smooth=70)
    export(join([o], "hedge"), "hedge_block")


# ------------------------------------------------------------------ bench, gazebo, fountain

def bench():
    wood = mat("bench_wood", (0.42, 0.23, 0.11), 0.45, coat=0.5)
    iron = mat("bench_iron", (0.05, 0.06, 0.05), 0.45, 0.6)
    parts = []
    for k in range(5):   # seat slats, the front one at -Y (Godot +Z)
        y = -0.2 + k * 0.083
        parts.append(box((1.4, 0.07, 0.03), (0, y, 0.44), wood, bevel=0.008, segs=2))
    tilt = math.radians(14)
    for k in range(3):   # back slats, leaning back
        s = 0.53 + k * 0.12
        y = 0.18 + (s - 0.5) * math.tan(tilt)
        parts.append(box((1.4, 0.03, 0.085), (0, y + 0.03, s), wood, rot=(-tilt, 0, 0), bevel=0.008, segs=2))
    for x in (-0.62, 0.0, 0.62):
        r = 0.016
        # front leg, back leg rising into the backrest upright, the seat rail
        parts.append(tube([(x, -0.22, 0.03), (x, -0.2, 0.2), (x, -0.19, 0.42)], [r, r, r], iron, verts=8))
        parts.append(tube([(x, 0.24, 0.03), (x, 0.19, 0.2), (x, 0.17, 0.42), (x, 0.235, 0.68), (x, 0.265, 0.82)],
                          [r, r, r, r, 0.014], iron, verts=8))
        parts.append(tube([(x, -0.23, 0.41), (x, 0.0, 0.415), (x, 0.2, 0.41)], [0.014, 0.014, 0.014], iron, verts=8))
        for y in (-0.22, 0.24):
            parts.append(box((0.05, 0.06, 0.012), (x, y, 0.006), iron, bevel=0.003, segs=1))
        if x != 0.0:   # arm rest with a scroll at its front
            parts.append(tube([(x, 0.2, 0.62), (x, 0.0, 0.63), (x, -0.2, 0.62), (x, -0.25, 0.58), (x, -0.24, 0.53),
                               (x, -0.2, 0.52)], [0.016, 0.017, 0.017, 0.015, 0.012, 0.01], iron, verts=8))
            parts.append(tube([(x, -0.2, 0.44), (x, -0.21, 0.5), (x, -0.215, 0.56)], [0.012, 0.012, 0.012], iron,
                              verts=8))
            parts.append(box((0.05, 0.36, 0.022), (x, -0.02, 0.645), wood, bevel=0.008, segs=2))
            # a decorative scroll in the side frame, under the seat
            parts.append(torus(0.05, 0.008, (x, 0.02, 0.28), iron, rot=(0, math.pi / 2, 0), verts=14, minor=4))
    export(join(parts, "bench"), "bench")


def gazebo():
    white = mat("gazebo_white", (0.88, 0.86, 0.8), 0.45, coat=0.4)
    trim = mat("gazebo_trim", (0.26, 0.34, 0.3), 0.45, coat=0.4)
    deck = mat("gazebo_deck", (0.4, 0.26, 0.15), 0.6, coat=0.25)
    stone = mat("gazebo_stone", (0.5, 0.47, 0.42), 0.85)
    shingle = mat("gazebo_shingle", (0.24, 0.27, 0.3), 0.6, coat=0.2)
    ridge = mat("gazebo_ridge", (0.16, 0.18, 0.2), 0.5, coat=0.3)
    brass = mat("gazebo_brass", (0.86, 0.63, 0.28), 0.28, 1.0)
    bulb = mat("gazebo_bulb_glow", (1.0, 0.76, 0.42), 0.4, emit=4.0)
    wire = mat("gazebo_wire", (0.05, 0.05, 0.05), 0.5)
    rv = lambda rf: rf / math.cos(PI8)
    parts = []
    # platform and deck planks
    parts.append(lathe([(0, 0.2), (rv(1.44), 0.2), (rv(1.47), 0.18), (rv(1.47), 0.13), (rv(1.43), 0.11),
                        (rv(1.43), 0.0), (0, 0.0)], stone, 8, PI8, smooth=30))
    rf = 1.42
    for k in range(24):
        y = -rf + 0.06 + k * (2 * rf - 0.12) / 23
        hw = min(rf, rf * math.sqrt(2) - abs(y) - 0.012) - 0.01
        parts.append(box((2 * hw, 0.113, 0.025), (0, y, 0.2125), deck, bevel=0.005, segs=1))
    for s in (1, 2):   # steps up to the open side, facing -Y (Godot +Z)
        parts.append(box((1.0, 0.16 * (3 - s), 0.075 * (3 - s) - 0.0), (0, -1.43 - 0.08 * (3 - s), 0.0375 * (3 - s)),
                         stone, bevel=0.015, segs=1))
    # posts at the corners
    RP = 1.3
    for k in range(8):
        a = PI8 + k * math.pi / 4
        p = Vector((math.cos(a), math.sin(a), 0)) * rv(RP)
        parts.append(box((0.14, 0.14, 0.12), (p.x, p.y, 0.285), white, rot=(0, 0, a), bevel=0.02, segs=1))
        parts.append(box((0.1, 0.1, 2.2), (p.x, p.y, 0.225 + 1.1), white, rot=(0, 0, a), bevel=0.012, segs=1))
        parts.append(box((0.14, 0.14, 0.06), (p.x, p.y, 2.32), white, rot=(0, 0, a), bevel=0.012, segs=1))
    # railings on seven sides and valances on all eight
    L = 2 * RP * math.tan(PI8) - 0.1
    for k in range(8):
        a = k * math.pi / 4
        M = T((RP * math.cos(a), RP * math.sin(a), 0)) @ Rz(a + math.pi / 2)
        side = []
        if k != 6:
            side += [box((L + 0.02, 0.07, 0.04), (0, 0, 0.95), white, bevel=0.01, segs=1),
                     box((L, 0.05, 0.04), (0, 0, 0.32), white, bevel=0.008, segs=1)]
            for j in range(9):
                x = -L / 2 + L * (j + 0.5) / 9
                side.append(box((0.025, 0.025, 0.59), (x, 0, 0.635), white, bevel=0.0))
        n = 20
        arch = [(-L / 2 + L * j / n, -0.08 - 0.17 * abs(2 * j / n - 1) ** 3.5) for j in range(n + 1)]
        poly = arch + [(L / 2, 0.0), (-L / 2, 0.0)]
        side.append(prism(poly, 0.025, (0, 0, 2.35), white, bevel=0.004, segs=1))
        for j in range(3):   # pierced circles in the valance
            x = (j - 1) * L * 0.3
            side.append(torus(0.028, 0.006, (x, -0.016, 2.29), trim, rot=(math.pi / 2, 0, 0), verts=12, minor=3))
        place(side, M)
        parts += side
    # eave beam
    parts.append(ring_band(2.5, 2.35, rv(RP - 0.06), rv(RP + 0.07), white))
    # the roof: shingle courses, then the soffit and ceiling
    ZT, ZE, RE, RT = 3.12, 2.5, 1.6, 0.3
    rr = lambda z: RT + (RE - RT) * max(0.0, (ZT - z) / (ZT - ZE)) ** 1.15
    NC = 9
    B = [ZT - (ZT - ZE) * j / NC for j in range(NC + 1)]
    prof = [(RT - 0.05, ZT + 0.005), (rr(B[0]), B[0])]
    for j in range(1, NC + 1):
        prof.append((rr(B[j]) + 0.018, B[j] - 0.006))
        if j < NC:
            prof.append((rr(B[j]), B[j]))
    n_sh = len(prof) - 2
    prof += [(RE + 0.018, ZE - 0.04), (RE - 0.05, ZE - 0.04), (rv(RP) - 0.1, 2.49), (0, 2.49)]

    def shingles(a, k, i, r, z):
        m = poly_r(a, 8)
        if 1 <= i <= n_sh:
            m *= 1.0 + 0.012 * (k % 2)
        return m, 0.0
    parts.append(lathe(prof, shingle, 64, 0.0, shape=shingles, smooth=45, mats=(white,),
                       mat_fn=lambda i: 1 if i > n_sh else 0))
    for k in range(8):
        a = PI8 + k * math.pi / 4
        pts = []
        for j in range(9):
            z = ZT - (ZT - ZE) * j / 8
            R = (rr(z) + 0.022) / math.cos(PI8)
            pts.append((R * math.cos(a), R * math.sin(a), z + 0.01))
        parts.append(tube(pts, [0.02] * 9, ridge, verts=6))
    # the cupola: an octagonal louvred drum, its own little roof and a finial
    parts.append(lathe([(0, 3.33), (rv(0.26), 3.33), (rv(0.26), 3.08), (0, 3.08)], white, 8, PI8, smooth=30))
    for k in range(8):
        a = k * math.pi / 4
        c = Vector((math.cos(a), math.sin(a), 0)) * 0.262
        for j in range(4):
            parts.append(box((0.012, 0.13, 0.018), (c.x, c.y, 3.14 + 0.04 * j), trim, rot=(0.0, -0.5, a),
                             bevel=0.0))
    parts.append(lathe([(0, 3.5), (0.05, 3.48), (rv(0.36), 3.35), (rv(0.37), 3.33), (rv(0.25), 3.33), (0, 3.33)],
                       shingle, 8, PI8, smooth=30))
    parts.append(sphere(0.035, (0, 0, 3.51), brass, segs=12, rings=8))
    parts.append(rod((0, 0, 3.53), (0, 0, 3.6), 0.01, brass, r2=0.002, verts=8))
    # string lights along the eaves: a sagging wire between the corners, five bulbs per side
    RL = (RE + 0.01) / math.cos(PI8)
    for k in range(8):
        a0 = PI8 + k * math.pi / 4
        a1 = a0 + math.pi / 4
        c0 = Vector((math.cos(a0), math.sin(a0), 0)) * RL + Vector((0, 0, ZE - 0.05))
        c1 = Vector((math.cos(a1), math.sin(a1), 0)) * RL + Vector((0, 0, ZE - 0.05))
        pt = lambda t: c0.lerp(c1, t) - Vector((0, 0, 0.18 * 4 * t * (1 - t)))
        parts.append(tube([pt(j / 10) for j in range(11)], [0.004] * 11, wire, verts=4, caps=False))
        for j in range(5):
            p = pt((j + 0.5) / 5)
            parts.append(cyl(0.009, 0.022, p - Vector((0, 0, 0.012)), wire, verts=6))
            parts.append(sphere(0.022, p - Vector((0, 0, 0.038)), bulb, scale=(1, 1, 1.25), segs=8, rings=5))
    # the lantern inside, hanging on a chain from the ceiling
    parts.append(rod((0, 0, 2.49), (0, 0, 2.2), 0.005, wire, verts=6))
    parts += lantern_parts((0, 0, 2.2))
    export(join(parts, "gazebo"), "gazebo")


def fountain():
    stone = mat("fountain_stone", (0.62, 0.58, 0.51), 0.72)
    wet = mat("fountain_stone_wet", (0.34, 0.33, 0.3), 0.35, coat=0.6)
    brass = mat("fountain_brass", (0.75, 0.55, 0.25), 0.3, 1.0)
    # lower basin: inner floor outwards, up the inner wall, over the rim, down the outside, underneath
    low = [(0, 0.12), (0.57, 0.12), (0.6, 0.15), (0.6, 0.4), (0.62, 0.43), (0.65, 0.44), (0.7, 0.44), (0.72, 0.42),
           (0.72, 0.39), (0.69, 0.37), (0.68, 0.11), (0.71, 0.09), (0.72, 0.06), (0.72, 0.0), (0, 0.0)]
    parts = [lathe(low, stone, 48, smooth=40, mats=(wet,), mat_fn=lambda i: 1 if i < 3 else 0)]
    parts.append(torus(0.685, 0.012, (0, 0, 0.26), stone, verts=48, minor=5))
    # the pedestal: a baluster
    parts.append(lathe([(0.11, 0.74), (0.12, 0.72), (0.09, 0.66), (0.075, 0.55), (0.1, 0.42), (0.13, 0.3),
                        (0.12, 0.2), (0.15, 0.17), (0.17, 0.13), (0.17, 0.115), (0, 0.115)], stone, 24, smooth=50))
    parts.append(torus(0.08, 0.012, (0, 0, 0.62), stone, verts=24, minor=5))

    def scallop(a, k, i, r, z):
        return (1 + 0.035 * math.cos(16 * a), 0.0) if 3 <= i <= 6 else (1.0, 0.0)
    up = [(0, 0.84), (0.24, 0.845), (0.28, 0.87), (0.29, 0.91), (0.31, 0.93), (0.35, 0.93), (0.36, 0.915),
          (0.34, 0.885), (0.26, 0.82), (0.16, 0.77), (0.11, 0.74), (0.1, 0.72), (0, 0.72)]
    parts.append(lathe(up, stone, 64, shape=scallop, smooth=40, mats=(wet,), mat_fn=lambda i: 1 if i < 2 else 0))
    # the top: a small urn and a spout
    parts.append(lathe([(0, 1.12), (0.02, 1.115), (0.045, 1.09), (0.06, 1.04), (0.05, 0.99), (0.03, 0.96),
                        (0.035, 0.9), (0.06, 0.87), (0.06, 0.84), (0, 0.84)], stone, 20, smooth=50))
    parts.append(lathe([(0, 1.18), (0.008, 1.178), (0.012, 1.16), (0.01, 1.12), (0.018, 1.11), (0, 1.11)], brass, 12,
                       smooth=50))
    export(join(parts, "fountain"), "fountain")


# ------------------------------------------------------------------ rocks and lilies

def rock(name, seed, size, height):
    st = mat("rock_stone", (0.25, 0.24, 0.22), 0.85)
    moss = mat("rock_moss", (0.16, 0.28, 0.07), 0.9)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=(0, 0, 0))
    o = K.active()
    off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
    for v in o.data.vertices:
        d = v.co.normalized()
        n1 = noise.noise(d * 1.3 + off)
        n2 = noise.noise(d * 3.5 + off * 2)
        rr = 1 + 0.22 * n1 + 0.08 * n2
        p = Vector((d.x * size[0] / 2, d.y * size[1] / 2, d.z * height * 0.8)) * rr
        p.z += height * 0.28
        p.z = max(p.z, 0.0)
        v.co = p
    o.data.update()
    top = max(v.co.z for v in o.data.vertices)
    for v in o.data.vertices:
        v.co.z *= height / top
    finish(o, st, smooth=38)
    o.data.materials.append(moss)
    for p in o.data.polygons:
        c = p.center
        if p.normal.z + 0.35 * noise.noise(c * 3.0 + off) > 0.62 and c.z > height * 0.4:
            p.material_index = 1
    export(join([o], name), name)


def rock_a():
    rock("rock_a", 3, (0.55, 0.45), 0.36)


def rock_b():
    rock("rock_b", 8, (0.5, 0.4), 0.26)


def lily_pad():
    padm = mat("lily_pad", (0.1, 0.28, 0.07), 0.45, coat=0.5)
    white = mat("lily_petal", (0.95, 0.92, 0.88), 0.5)
    pinkm = mat("lily_petal_pink", (0.95, 0.52, 0.66), 0.5)
    heart = mat("lily_heart", (1.0, 0.75, 0.1), 0.5, emit=0.2)
    # the pad: a polar grid with a notch, rim curling up a little, then solidified
    bm = bmesh.new()
    notch = math.radians(24)
    NA, NR = 36, 4
    centre = bm.verts.new((0, 0, 0.012))
    rings = []
    for i in range(1, NR + 1):
        r = 0.125 * i / NR
        ring = []
        for k in range(NA + 1):
            a = notch / 2 + (TAU - notch) * k / NA
            wob = 1 + 0.03 * math.sin(5 * a)
            ring.append(bm.verts.new((r * wob * math.cos(a), r * wob * math.sin(a), 0.012 + 0.006 * (i / NR) ** 3)))
        rings.append(ring)
    for k in range(NA):
        bm.faces.new((centre, rings[0][k], rings[0][k + 1]))
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(NA):
            bm.faces.new((r0[k], r1[k], r1[k + 1], r0[k + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    pad = new_obj(bm, "pad", padm, smooth=60)
    if pad.data.polygons[0].normal.z < 0:
        pad.data.flip_normals()
    K.select(pad)
    s = pad.modifiers.new("s", "SOLIDIFY")
    s.thickness = 0.01
    s.offset = -1
    bpy.ops.object.modifier_apply(modifier=s.name)
    pad = join([pad], "pad")
    # the lily
    parts = []
    for ring, (n, L, tilt, m, rot0) in enumerate(((8, 0.05, 0.55, white, 0.0), (8, 0.04, 0.95, pinkm, math.pi / 8),
                                                   (6, 0.028, 1.25, pinkm, 0.2))):
        for k in range(n):
            a = rot0 + k * TAU / n
            o = sphere(1.0, (0, 0, 0), m, scale=(L / 2, 0.013 + 0.004 * (2 - ring), 0.004), segs=10, rings=6)
            o.data.transform(Matrix.Translation((L / 2, 0, 0)))
            o.data.transform(Matrix.Rotation(-tilt * 0.5, 4, "Y"))
            o.data.transform(Matrix.Rotation(a, 4, "Z"))
            o.data.transform(Matrix.Translation((0, 0, 0.018 + 0.004 * ring)))
            parts.append(o)
    parts.append(cyl(0.012, 0.02, (0, 0, 0.022), heart, verts=12))
    for k in range(10):
        a = k * TAU / 10
        parts.append(rod((0.006 * math.cos(a), 0.006 * math.sin(a), 0.03),
                         (0.013 * math.cos(a), 0.013 * math.sin(a), 0.045), 0.0022, heart, verts=4))
    parts.append(cyl(0.02, 0.018, (0, 0, 0.009), padm, r2=0.012, verts=10))
    lily = join(parts, "lily")
    export([pad, lily], "lily_pad")


JOBS = {"windmill": windmill, "lantern_post": lantern_post, "paper_lantern": paper_lantern,
        "stone_lantern": stone_lantern, "flag": flag, "bumper": bumper, "putter": putter, "spinner": spinner,
        "tree_round": tree_round, "tree_tall": tree_tall, "tree_cypress": tree_cypress, "bush": bush,
        "hedge_block": hedge_block, "bench": bench, "gazebo": gazebo, "fountain": fountain, "rock_a": rock_a,
        "rock_b": rock_b, "lily_pad": lily_pad}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["."]
    K.OUT = args[0]
    os.makedirs(K.OUT, exist_ok=True)
    for k, fn in JOBS.items():
        if not args[1:] or k in args[1:]:
            reset()
            fn()
