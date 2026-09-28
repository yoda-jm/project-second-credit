"""The valley and the jump arena for game 5 (Frostpeak Games): two alpine chalets (a family house and a hotel), the
village church, the gondola (cabin, pylon, station), a snow-cat, a hospitality tent and a TV camera on a tripod.
Deterministic; output CC BY-SA 4.0; provenance: this script (helpers from frostpeak_models.py).
Run: blender -b --factory-startup -P tools/blender/frostpeak_valley.py -- godot/games/frostpeak/art/models
1 unit = 1 m, Z up in Blender, fronts face -Y (+Z in Godot). Material names the game swaps for textures:
"timber" (planks), "plinth" (stone), "roof" and "cladding" (metal sheet).
"""
import math, os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from frostpeak_models import (Kit, mat, export, reset, SNOW, STEEL, DARK_STEEL, WINDOW, WHITE, RED, BLUE,  # noqa: E402
                              CONCRETE, WOOD)

TIMBER = mat("timber", (0.42, 0.26, 0.15), 0.85)
PLINTH = mat("plinth", (0.62, 0.62, 0.64), 0.9)
LIT = mat("window_lit", (1.0, 0.72, 0.4), 0.3, emit=2.2)
SHUTTER = mat("shutter", (0.55, 0.12, 0.1), 0.6)
PLASTER = mat("plaster", (0.93, 0.9, 0.84), 0.9)
ROOF = mat("roof", (0.3, 0.3, 0.33), 0.5, 0.6)


def _gable_roof(k, w, d, z, pitch, over=1.0, snow=0.35):
    """A pitched roof over a w x d box (ridge along x), eaves `over` metres beyond the walls, a thick snow cover
    and snow on the gable ends' ledges."""
    half = d / 2 + over
    rise = half * math.tan(pitch)
    slope = math.hypot(half, rise)
    for s in (-1, 1):
        cy = s * half / 2
        cz = z + rise / 2
        k.box(ROOF, (0, cy, cz), (w + 2 * over, slope, 0.22), rx=-s * pitch)
        k.box(SNOW, (0, cy * 0.98, cz + 0.26), (w + 2 * over - 0.1, slope - 0.1, snow), rx=-s * pitch)
    # the gable triangles under the roof
    for x in (-w / 2, w / 2):
        k.rings(TIMBER, [[(x, -d / 2, z), (x, d / 2, z), (x, 0, z + d / 2 * math.tan(pitch))],
                         [(x + (0.05 if x > 0 else -0.05), -d / 2, z), (x + (0.05 if x > 0 else -0.05), d / 2, z),
                          (x + (0.05 if x > 0 else -0.05), 0, z + d / 2 * math.tan(pitch))]], smooth=False)
    return rise


def _windows(k, w, y, z, n, h=1.1, lit=(0,)):
    """A row of n windows on a wall at y (front -Y), with shutters; some glow warm."""
    for i in range(n):
        x = -w / 2 + (i + 0.5) * w / n
        k.box(LIT if i in lit else WINDOW, (x, y - 0.03, z), (0.9, 0.06, h))
        k.box(WHITE, (x, y - 0.05, z - h / 2 - 0.06), (1.05, 0.12, 0.1))
        for s in (-1, 1):
            k.box(SHUTTER, (x + s * 0.72, y - 0.05, z), (0.45, 0.06, h + 0.1))


def chalet():
    """A two-storey chalet: a stone ground floor, a timber upper floor with a balcony on the gable front, a broad
    roof deep in snow, a chimney."""
    k = Kit()
    w, d = 9.0, 11.0  # the ridge runs along y (the gable faces -Y)
    k.box(PLINTH, (0, 0, 1.4), (w, d, 2.8))
    k.box(TIMBER, (0, 0, 4.2), (w + 0.1, d + 0.1, 2.8))
    for i in range(12):  # vertical boards
        k.box(TIMBER, (-w / 2 + 0.4 + i * (w - 0.8) / 11, -d / 2 - 0.08, 4.2), (0.1, 0.06, 2.8))
    for z, lit in ((1.5, (1,)), (4.3, (0, 2))):
        _windows(k, w - 1, -d / 2, z, 3, 1.2, lit)
    for x in (-w / 2, w / 2):  # side windows
        for yy in (-2.5, 2.5):
            k.box(WINDOW, (x + (0.03 if x > 0 else -0.03), yy, 4.3), (0.06, 0.9, 1.1))
    # the balcony on the front, carved boards
    k.box(TIMBER, (0, -d / 2 - 0.8, 2.95), (w - 0.6, 1.6, 0.15))
    for i in range(22):
        k.box(TIMBER, (-w / 2 + 0.5 + i * (w - 1.0) / 21, -d / 2 - 1.55, 3.45), (0.18, 0.05, 0.85))
    k.box(TIMBER, (0, -d / 2 - 1.55, 3.9), (w - 0.6, 0.12, 0.1))
    k.box(SNOW, (0, -d / 2 - 1.55, 3.98), (w - 0.6, 0.16, 0.08))
    # the roof: ridge along y, so build it turned
    pitch = math.radians(24)
    half = w / 2 + 1.3
    rise = half * math.tan(pitch)
    slope = math.hypot(half, rise)
    for s in (-1, 1):
        k.box(ROOF, (s * half / 2, 0, 5.6 + rise / 2), (slope, d + 2.4, 0.24), ry=s * pitch)
        k.box(SNOW, (s * half / 2 * 0.98, 0, 5.6 + rise / 2 + 0.3), (slope - 0.1, d + 2.3, 0.4), ry=s * pitch)
    for y in (-d / 2, d / 2):  # gables
        yy = y + (-0.05 if y < 0 else 0.05)
        k.rings(TIMBER, [[(-w / 2, y, 5.6), (w / 2, y, 5.6), (0, y, 5.6 + w / 2 * math.tan(pitch))],
                         [(-w / 2, yy, 5.6), (w / 2, yy, 5.6), (0, yy, 5.6 + w / 2 * math.tan(pitch))]], smooth=False)
    k.box(PLINTH, (2.0, 2.5, 7.4), (0.8, 0.8, 2.6))
    k.box(SNOW, (2.0, 2.5, 8.75), (0.9, 0.9, 0.15))
    k.box(WOOD, (0, -d / 2 - 0.06, 0.9), (1.2, 0.08, 2.0))  # door
    # the woodpile under the eaves
    for i in range(3):
        k.box(mat("logs", (0.55, 0.38, 0.22), 0.9), (w / 2 + 0.5, -2.0 + i * 1.2, 0.6), (0.8, 1.1, 1.2))
    export(k.obj(), "chalet")


def hotel():
    """A four-storey hotel in the alpine style: a plastered lower half, timber above, long balconies with
    flower boxes, a snow-laden roof and a lit sign board."""
    k = Kit()
    w, d = 20.0, 12.0
    k.box(PLINTH, (0, 0, 0.6), (w + 0.2, d + 0.2, 1.2))
    k.box(PLASTER, (0, 0, 3.6), (w, d, 5.6))
    k.box(TIMBER, (0, 0, 8.6), (w + 0.1, d + 0.1, 4.4))
    for fl, z in enumerate((2.3, 5.0, 7.8, 10.3)):
        lit = (1, 4) if fl % 2 == 0 else (0, 3, 5)
        _windows(k, w - 2, -d / 2, z, 6, 1.3, lit)
        _windows(k, w - 2, d / 2 + 0.12, z, 6, 1.3, ())
        if fl >= 1:  # balconies
            k.box(TIMBER, (0, -d / 2 - 0.9, z - 0.9), (w - 1.0, 1.8, 0.15))
            for i in range(40):
                k.box(TIMBER, (-w / 2 + 0.7 + i * (w - 1.4) / 39, -d / 2 - 1.75, z - 0.45), (0.16, 0.05, 0.8))
            k.box(TIMBER, (0, -d / 2 - 1.75, z - 0.02), (w - 1.0, 0.12, 0.1))
            k.box(SNOW, (0, -d / 2 - 1.75, z + 0.05), (w - 1.0, 0.16, 0.07))
    pitch = math.radians(22)
    rise = _gable_roof(k, w, d, 10.8, pitch, 1.4, 0.45)
    k.box(DARK_STEEL, (0, -d / 2 - 0.2, 12.2 + rise * 0.2), (8.0, 0.2, 1.3))
    k.box(mat("sign_lit", (1.0, 0.85, 0.55), 0.4, emit=1.5), (0, -d / 2 - 0.32, 12.2 + rise * 0.2), (7.6, 0.04, 0.9))
    k.box(WOOD, (0, -d / 2 - 0.06, 1.5), (2.2, 0.1, 2.6))
    export(k.obj(), "hotel")


def church():
    """The village church: a white nave with round windows, a bell tower with a clock and a slender spire."""
    k = Kit()
    k.box(PLASTER, (0, 2, 4.0), (9.0, 18.0, 8.0))
    for y in range(-4, 10, 4):
        for x in (-4.52, 4.52):
            k.box(WINDOW, (x, y, 4.8), (0.06, 1.2, 3.0))
    pitch = math.radians(38)
    half = 4.5 + 0.6
    rise = half * math.tan(pitch)
    slope = math.hypot(half, rise)
    for s in (-1, 1):
        k.box(ROOF, (s * half / 2, 2, 8.0 + rise / 2), (slope, 19.0, 0.2), ry=s * pitch)
        k.box(SNOW, (s * half / 2 * 0.98, 2, 8.0 + rise / 2 + 0.25), (slope - 0.1, 18.8, 0.3), ry=s * pitch)
    for y in (-7.0, 11.0):
        yy = y + (-0.05 if y < 0 else 0.05)
        k.rings(PLASTER, [[(-4.5, y, 8.0), (4.5, y, 8.0), (0, y, 8.0 + 4.5 * math.tan(pitch))],
                          [(-4.5, yy, 8.0), (4.5, yy, 8.0), (0, yy, 8.0 + 4.5 * math.tan(pitch))]], smooth=False)
    # the tower at the front
    k.box(PLASTER, (0, -9.5, 9.0), (4.6, 4.6, 18.0))
    for side in ((0, -2.32), (0, 2.32), (-2.32, 0), (2.32, 0)):
        c = (side[0], -9.5 + side[1], 15.5)
        size = (1.4, 0.06, 2.2) if side[0] == 0 else (0.06, 1.4, 2.2)
        k.box(mat("belfry", (0.08, 0.08, 0.1), 0.9), c, size)
    k.tube(mat("clock", (0.95, 0.95, 0.9), 0.4), (0, -11.8, 12.5), (0, -11.9, 12.5), 1.0, segs=24, smooth=False)
    k.tube(mat("gold", (0.95, 0.75, 0.3), 0.3, 1.0), (0, -11.9, 12.5), (0, -11.95, 12.5), 0.2, segs=12)
    spire = mat("spire", (0.25, 0.42, 0.38), 0.5, 0.5)
    k.tube(spire, (0, -9.5, 18.0), (0, -9.5, 29.0), 3.1, 0.05, 8, smooth=False)
    k.tube(mat("gold", (0.95, 0.75, 0.3), 0.3, 1.0), (0, -9.5, 29.0), (0, -9.5, 31.0), 0.06, segs=6)
    k.box(mat("gold", (0.95, 0.75, 0.3), 0.3, 1.0), (0, -9.5, 30.3), (0.8, 0.06, 0.08))
    k.box(WOOD, (0, -11.85, 1.6), (1.8, 0.1, 3.2))
    export(k.obj(), "church")


def gondola_cabin():
    """An eight-seat gondola cabin with wrap-round windows, hanging from its arm and the grip (the grip's top is
    the model's origin, where the cable runs)."""
    shell = mat("cabin_red", (0.8, 0.1, 0.12), 0.35, 0.2, coat=0.8)
    k = Kit()
    rings = []
    for z, rx, ry in ((-6.3, 0.9, 0.8), (-6.2, 1.1, 1.0), (-5.6, 1.15, 1.05), (-4.6, 1.15, 1.05), (-4.2, 1.05, 0.95), (-4.05, 0.8, 0.7)):
        rings.append([(rx * math.cos(2 * math.pi * i / 16), ry * math.sin(2 * math.pi * i / 16), z) for i in range(16)])
    k.rings(shell, rings)
    # the window band
    band = []
    for z in (-5.55, -4.6):
        band.append([(1.17 * math.cos(2 * math.pi * i / 16), 1.07 * math.sin(2 * math.pi * i / 16), z) for i in range(16)])
    k.rings(WINDOW, band, cap=False)
    k.box(DARK_STEEL, (0, 0, -3.95), (1.0, 0.8, 0.2))
    k.bar(DARK_STEEL, (0, 0, -3.9), (0, 0, -0.5), 0.12)
    k.bar(DARK_STEEL, (0, 0, -0.5), (0.5, 0, 0.0), 0.12)
    k.box(DARK_STEEL, (0.5, 0, 0.05), (0.7, 0.4, 0.35))
    export(k.obj(), "gondola_cabin")


def gondola_pylon():
    """A tubular pylon 22 m tall with a cross-arm; the two cables ride on sheave trains 3 m either side of the
    centre, 22 m up (the game hangs the cables there)."""
    paint = mat("pylon_paint", (0.8, 0.82, 0.85), 0.35, 0.7)
    k = Kit()
    k.box(CONCRETE, (0, 0, 0.3), (2.4, 2.4, 0.6))
    k.tube(paint, (0, 0, 0.6), (0, 0, 21.0), 0.75, 0.5, 16)
    k.box(paint, (0, 0, 21.2), (7.4, 0.9, 0.7))
    for x in (-3.0, 3.0):  # sheave trains along the cable (y)
        k.box(DARK_STEEL, (x, 0, 21.7), (0.35, 5.0, 0.3))
        for y in (-2.0, -1.0, 0.0, 1.0, 2.0):
            k.tube(DARK_STEEL, (x - 0.2, y, 21.85), (x + 0.2, y, 21.85), 0.22, segs=10)
    for i in range(40):  # the ladder
        k.box(STEEL, (0, -0.8 + 0.3 * min(1.0, i / 40.0), 1.0 + i * 0.5), (0.5, 0.04, 0.04))
    k.box(DARK_STEEL, (0, 0, 20.6), (2.4, 2.0, 0.1))
    export(k.obj(), "gondola_pylon")


def gondola_station():
    """A gondola station: a glazed hall on a stone base, a wide arched roof over the bullwheel, the cables leaving
    from the front (-Y) at 6 m, 3 m either side of the centre."""
    k = Kit()
    k.box(PLINTH, (0, 2, 1.0), (16.0, 22.0, 2.0))
    k.box(mat("cladding", (0.4, 0.48, 0.58), 0.6, 0.5), (0, 6, 4.0), (16.0, 14.0, 4.0))
    k.box(WINDOW, (0, -1.02, 4.0), (15.0, 0.06, 3.2))
    rings = []
    for i in range(13):
        a = math.pi * i / 12
        rings.append((8.8 * math.cos(a), 5.0 * math.sin(a)))
    for y0, y1 in ((-8.0, 13.0),):
        k.rings(mat("roof", (0.3, 0.3, 0.33), 0.5, 0.6), [[(x, y0, 6.0 + z) for x, z in rings], [(x, y1, 6.0 + z) for x, z in rings]], smooth=True)
        k.rings(SNOW, [[(x * 1.01, y0 + 0.2, 6.3 + z) for x, z in rings[3:10]], [(x * 1.01, y1 - 0.2, 6.3 + z) for x, z in rings[3:10]]], smooth=True, cap=False)
    k.tube(DARK_STEEL, (0, -3.5, 5.6), (0, -3.5, 6.0), 3.2, segs=24)  # the bullwheel
    for x in (-3.0, 3.0):
        k.box(DARK_STEEL, (x, -4.5, 5.9), (0.4, 7.0, 0.3))
    k.box(BLUE, (0, -8.05, 9.5), (9.0, 0.1, 1.2))
    export(k.obj(), "gondola_station")


def snowcat():
    """A piste basher: a red body and cab on wide tracks, a front blade and the tiller behind."""
    red = mat("snowcat_red", (0.78, 0.12, 0.1), 0.45, 0.2, coat=0.6)
    rubber = mat("track", (0.12, 0.12, 0.13), 0.9)
    k = Kit()
    for s in (-1, 1):
        k.box(rubber, (s * 1.6, 0, 0.55), (1.3, 5.2, 1.1))
        for i in range(4):
            k.tube(DARK_STEEL, (s * 1.0, -1.8 + i * 1.2, 0.55), (s * 2.2, -1.8 + i * 1.2, 0.55), 0.45, segs=12)
    k.box(red, (0, 0.4, 1.6), (2.6, 4.4, 1.2))
    k.box(red, (0, -0.9, 2.8), (2.4, 2.2, 1.3))
    k.box(WINDOW, (0, -2.02, 2.85), (2.2, 0.05, 1.0))
    for s in (-1, 1):
        k.box(WINDOW, (s * 1.22, -0.9, 2.85), (0.05, 1.8, 0.9))
    k.box(mat("beacon", (1.0, 0.55, 0.1), 0.3, emit=3.0), (0, -0.9, 3.55), (0.3, 0.3, 0.15))
    k.box(DARK_STEEL, (0, -3.4, 0.7), (4.6, 0.3, 1.1), rx=0.2)  # the blade
    k.box(red, (0, -3.2, 0.9), (4.4, 0.1, 0.8), rx=0.2)
    k.box(DARK_STEEL, (0, 3.4, 0.6), (4.2, 1.4, 0.7))  # the tiller
    k.box(SNOW, (0, -3.6, 0.35), (4.4, 0.8, 0.5))
    export(k.obj(), "snowcat")


def tent():
    """A hospitality tent: a white pagoda roof over a square frame, a coloured valance and open sides."""
    fabric = mat("tent_white", (0.96, 0.96, 0.97), 0.7)
    k = Kit()
    w = 6.0
    for x in (-1, 1):
        for y in (-1, 1):
            k.tube(STEEL, (x * w / 2, y * w / 2, 0), (x * w / 2, y * w / 2, 2.6), 0.05, segs=6)
    rings = [[(x * w / 2 * f, y * w / 2 * f, z) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
             for f, z in ((1.08, 2.55), (0.75, 3.1), (0.35, 4.0), (0.05, 5.2))]
    k.rings(fabric, rings, smooth=False)
    for y in (-w / 2 - 0.02, w / 2 + 0.02):
        k.box(BLUE, (0, y, 2.35), (w, 0.04, 0.45))
    for x in (-w / 2 - 0.02, w / 2 + 0.02):
        k.box(BLUE, (x, 0, 2.35), (0.04, w, 0.45))
    k.box(fabric, (0, w / 2, 1.3), (w, 0.04, 2.6))  # the back wall
    k.box(WOOD, (0, -1.0, 0.5), (3.0, 0.8, 1.0))  # a counter
    export(k.obj(), "tent")


if __name__ == "__main__":
    reset()
    chalet()
    hotel()
    church()
    gondola_cabin()
    gondola_pylon()
    gondola_station()
    snowcat()
    tent()
