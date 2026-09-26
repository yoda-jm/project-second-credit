#!/usr/bin/env python3
"""Iron Flags campaign maps, generated from a short description of each battlefield (territory grid, rivers, ridges,
what stands in each territory), deterministic. Output: godot/games/flags/packs/first-war/first-war.flags (our text format, see
godot/games/flags/engine/flags_map.gd). Licence CC BY-SA 4.0. Usage: python3 tools/flags_maps.py"""
import os, random

OUT = os.path.join(os.path.dirname(__file__), "..", "godot", "games", "flags", "packs", "first-war", "first-war.flags")


class Map:
    def __init__(self, name, planet, cols, rows, zw, zh, seed):
        self.name, self.planet = name, planet
        self.rnd = random.Random(seed)
        self.cols, self.rows, self.zw, self.zh = cols, rows, zw, zh
        self.w, self.h = cols * zw + 2, rows * zh + 2
        self.g = [["." for _ in range(self.w)] for _ in range(self.h)]
        self.lines = []
        self.solid = set()  # footprints, kept clear of props
        for x in range(self.w):
            self.g[0][x] = self.g[self.h - 1][x] = "#"
        for y in range(self.h):
            self.g[y][0] = self.g[y][self.w - 1] = "#"
        self.zones = []
        for r in range(rows):
            for c in range(cols):
                self.zones.append((1 + c * zw, 1 + r * zh, zw, zh))
        for z in self.zones:
            self.lines.append("zone %d %d %d %d" % z)

    def set(self, x, y, ch):
        if 0 < x < self.w - 1 and 0 < y < self.h - 1:
            self.g[y][x] = ch

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else "#"

    def zone(self, c, r):
        return self.zones[r * self.cols + c]

    def rough(self, n, size=3):
        for _ in range(n):
            cx, cy = self.rnd.randrange(2, self.w - 2), self.rnd.randrange(2, self.h - 2)
            for _ in range(size * size):
                x, y = cx + self.rnd.randint(-size, size), cy + self.rnd.randint(-size, size)
                if self.get(x, y) == ".":
                    self.set(x, y, ":")

    def outcrops(self, n, size=2):
        """small rock islands to break up the open ground"""
        for _ in range(n):
            cx, cy = self.rnd.randrange(3, self.w - 3), self.rnd.randrange(3, self.h - 3)
            for y in range(cy - size, cy + size + 1):
                for x in range(cx - size, cx + size + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= size * size + self.rnd.randint(-1, 1) and self.get(x, y) in ".:":
                        self.set(x, y, "#")

    def ridge_h(self, y, x0, x1, gaps, ch="#"):
        """a horizontal wall of rock (or lava / water) with gaps [(x, width)]"""
        for x in range(x0, x1):
            if any(g <= x < g + gw for g, gw in gaps):
                continue
            wob = self.rnd.choice([0, 0, 0, 1])
            self.set(x, y, ch)
            if wob:
                self.set(x, y + 1, ch)

    def ridge_v(self, x, y0, y1, gaps, ch="#"):
        for y in range(y0, y1):
            if any(g <= y < g + gw for g, gw in gaps):
                continue
            self.set(x, y, ch)
            if self.rnd.random() < 0.25:
                self.set(x + 1, y, ch)

    def river_h(self, y, width, bridges, ch="~"):
        """a meandering river across the map; bridges [(x, width)] cross it"""
        yy = y
        for x in range(1, self.w - 1):
            if self.rnd.random() < 0.25:
                yy += self.rnd.choice([-1, 1])
                yy = max(y - 2, min(y + 2, yy))
            for k in range(width):
                bridge = any(b <= x < b + bw for b, bw in bridges)
                self.set(x, yy + k, "b" if bridge else ch)
            for b, bw in bridges:  # bridges are straight: fill their span over the river's wobble
                if b <= x < b + bw:
                    for k in range(-2, width + 3):
                        if self.get(x, y + k) in "~%":
                            self.set(x, y + k, "b")

    def road(self, a, b):
        (x0, y0), (x1, y1) = a, b
        x, y = x0, y0
        while x != x1:
            self._road_cell(x, y)
            x += 1 if x1 > x else -1
        while y != y1:
            self._road_cell(x, y)
            y += 1 if y1 > y else -1
        self._road_cell(x, y)

    def _road_cell(self, x, y):
        for dx in (0, 1):
            c = self.get(x + dx, y)
            if c in ".:":
                self.set(x + dx, y, "=")
            elif c == "#":
                self.set(x + dx, y, "=")  # roads cut through rock
            elif c in "~%":
                self.set(x + dx, y, "b")

    def clear(self, x, y, w, h, ch="."):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if self.get(xx, yy) not in "=b":
                    self.set(xx, yy, ch)
                self.solid.add((xx, yy))

    def put(self, line, x, y, w=1, h=1, clear=True):
        if clear:
            self.clear(x - 1, y - 1, w + 2, h + 2)
        self.lines.append(line)

    def flag(self, c, r, dx=0, dy=0):
        x0, y0, zw, zh = self.zone(c, r)
        x, y = x0 + zw // 2 + dx, y0 + zh // 2 + dy
        self.clear(x - 1, y - 1, 3, 3)
        self.lines.append("flag %d %d" % (x, y))
        return x, y

    def building(self, kind, team, c, r, dx, dy, size):
        x0, y0, zw, zh = self.zone(c, r)
        x, y = x0 + dx, y0 + dy
        self.clear(x - 1, y - 1, size[0] + 2, size[1] + 3)
        self.lines.append("%s %s %d %d" % (kind, team, x, y))
        return x + size[0] // 2, y + size[1]

    def unit(self, cls, kind, team, x, y):
        self.clear(x, y, 2 if cls == "cannon" else 1, 2 if cls == "cannon" else 1)
        self.lines.append("%s %s %s %d %d" % (cls, kind, team, x, y))

    def crate(self, kind, x, y):
        self.clear(x, y, 1, 1)
        self.lines.append("crate %s %d %d" % (kind, x, y))

    def props(self, kinds, n):
        for _ in range(n):
            x, y = self.rnd.randrange(2, self.w - 2), self.rnd.randrange(2, self.h - 2)
            if self.get(x, y) in ".:" and (x, y) not in self.solid:
                self.lines.append("prop %s %d %d" % (self.rnd.choice(kinds), x, y))
                self.solid.add((x, y))

    def text(self):
        out = ["[map]", "name=" + self.name, "planet=" + self.planet]
        out += ["".join(r) for r in self.g]
        out += self.lines
        return "\n".join(out) + "\n"


FORT, RF, VF, RADAR, REPAIR = (10, 12), (4, 5), (4, 5), (4, 3), (5, 4)


def dust_bowl():
    """Map 1: six territories in the desert, two factories to fight over, a ridge with three passes."""
    m = Map("Dust Bowl", "desert", 2, 3, 22, 20, 11)
    m.rough(22, 3)
    m.outcrops(12)
    m.ridge_h(21, 1, m.w - 1, [(8, 4), (21, 4), (35, 4)])
    m.ridge_h(41, 1, m.w - 1, [(6, 4), (20, 5), (36, 4)])
    flags = {}
    for r in range(3):
        for c in range(2):
            flags[(c, r)] = m.flag(c, r, 3 if c == 0 else -3, 4 if r == 0 else (-4 if r == 2 else 0))
    for a, b in [((0, 0), (1, 0)), ((0, 1), (1, 1)), ((0, 2), (1, 2)), ((0, 0), (0, 1)), ((1, 1), (1, 2)), ((0, 1), (0, 2)), ((1, 0), (1, 1))]:
        m.road(flags[a], flags[b])
    m.building("fort", "blue", 1, 0, 6, 2, FORT)
    m.building("fort", "red", 0, 2, 5, 6, FORT)
    m.building("robot_factory", "neutral", 0, 0, 2, 3, RF)
    m.building("robot_factory", "neutral", 1, 2, 15, 10, RF)
    m.building("vehicle_factory", "neutral", 1, 1, 14, 3, VF)
    m.building("radar", "neutral", 0, 1, 2, 12, RADAR)
    m.unit("cannon", "gatling", "blue", 34, 16)
    m.unit("cannon", "gatling", "red", 10, 44)
    m.unit("cannon", "gun", "neutral", 8, 26)
    m.unit("vehicle", "jeep", "neutral", 30, 30)
    m.unit("vehicle", "tank_light", "neutral", 12, 36)
    for i, (x, y) in enumerate([(26, 49), (28, 50), (30, 49)]):
        m.unit("robot", "grunt", "red", x, y)
    for x, y in [(12, 50), (13, 51)]:
        m.unit("robot", "psycho", "red", x, y)
    for x, y in [(14, 10), (16, 11), (18, 10)]:
        m.unit("robot", "grunt", "blue", x, y)
    for x, y in [(30, 14), (31, 15)]:
        m.unit("robot", "psycho", "blue", x, y)
    m.crate("grenades", 22, 28)
    m.crate("rockets", 20, 33)
    m.props(["cactus", "cactus", "palm", "ruin_pillar"], 70)
    return m


def frost_line():
    """Map 2: nine territories on the ice, a frozen river crossed by three bridges, guns on every bank."""
    m = Map("Frost Line", "arctic", 3, 3, 20, 20, 23)
    m.rough(26, 3)
    m.outcrops(16)
    m.river_h(29, 3, [(8, 4), (30, 4), (50, 4)])
    m.ridge_v(21, 2, 26, [(8, 4), (18, 3)])
    m.ridge_v(41, 36, 60, [(40, 4), (52, 3)])
    flags = {}
    for r in range(3):
        for c in range(3):
            flags[(c, r)] = m.flag(c, r, 0, 4 if r == 0 else (-4 if r == 2 else 5))
    for r in range(3):
        m.road(flags[(0, r)], flags[(1, r)])
        m.road(flags[(1, r)], flags[(2, r)])
    for c in range(3):
        m.road(flags[(c, 0)], flags[(c, 1)])
        m.road(flags[(c, 1)], flags[(c, 2)])
    m.building("fort", "blue", 2, 0, 5, 2, FORT)
    m.building("fort", "red", 0, 2, 4, 6, FORT)
    m.building("robot_factory", "neutral", 0, 0, 3, 3, RF)
    m.building("robot_factory", "neutral", 2, 2, 12, 9, RF)
    m.building("vehicle_factory", "neutral", 1, 1, 2, 2, VF)
    m.building("vehicle_factory", "neutral", 1, 2, 13, 11, VF)
    m.building("vehicle_factory", "neutral", 1, 0, 12, 2, VF)
    m.building("repair", "neutral", 2, 1, 12, 2, REPAIR)
    m.building("radar", "neutral", 0, 1, 2, 2, RADAR)
    for x, y, k in [(14, 24, "gun"), (46, 24, "gun"), (28, 36, "gatling"), (54, 36, "howitzer"), (8, 36, "gatling")]:
        m.unit("cannon", k, "neutral", x, y)
    m.unit("cannon", "gatling", "blue", 50, 16)
    m.unit("cannon", "gatling", "red", 12, 46)
    m.unit("vehicle", "tank_medium", "neutral", 32, 26)
    m.unit("vehicle", "jeep", "neutral", 6, 20)
    m.unit("vehicle", "jeep", "neutral", 55, 40)
    for x, y in [(18, 50), (19, 52), (20, 50)]:
        m.unit("robot", "grunt", "red", x, y)
    for x, y in [(22, 55), (23, 56)]:
        m.unit("robot", "tough", "red", x, y)
    for x, y in [(42, 10), (43, 12), (44, 10)]:
        m.unit("robot", "grunt", "blue", x, y)
    for x, y in [(40, 5), (41, 6)]:
        m.unit("robot", "tough", "blue", x, y)
    m.crate("rockets", 31, 44)
    m.crate("grenades", 31, 15)
    m.props(["pine", "pine", "dead_tree", "ruin_pillar"], 90)
    return m


def magma_works():
    """Map 3: twelve territories on a volcanic world, lava channels, rock walls to blast through, the full arsenal."""
    m = Map("Magma Works", "volcanic", 3, 4, 20, 18, 37)
    m.rough(30, 3)
    m.outcrops(18)
    m.river_h(19, 2, [(6, 4), (44, 4)], ch="%")
    m.river_h(55, 2, [(16, 4), (52, 4)], ch="%")
    m.ridge_h(37, 1, m.w - 1, [(9, 3), (29, 4), (50, 3)])
    m.ridge_v(21, 38, 54, [(44, 3)])
    m.ridge_v(41, 20, 36, [(26, 3)])
    flags = {}
    for r in range(4):
        for c in range(3):
            flags[(c, r)] = m.flag(c, r, 0, 3 if r == 0 else (-3 if r == 3 else 0))
    for r in range(4):
        m.road(flags[(0, r)], flags[(1, r)])
        m.road(flags[(1, r)], flags[(2, r)])
    for c in range(3):
        for r in range(3):
            if (c + r) % 2 == 0:
                m.road(flags[(c, r)], flags[(c, r + 1)])
    m.building("fort", "blue", 1, 0, 5, 1, FORT)
    m.building("fort", "red", 1, 3, 5, 5, FORT)
    m.building("robot_factory", "neutral", 0, 0, 2, 2, RF)
    m.building("robot_factory", "neutral", 2, 3, 13, 9, RF)
    m.building("robot_factory", "neutral", 2, 1, 13, 2, RF)
    m.building("robot_factory", "neutral", 0, 2, 2, 9, RF)
    m.building("vehicle_factory", "neutral", 2, 0, 13, 2, VF)
    m.building("vehicle_factory", "neutral", 0, 3, 2, 9, VF)
    m.building("vehicle_factory", "neutral", 1, 1, 2, 2, VF)
    m.building("vehicle_factory", "neutral", 1, 2, 13, 9, VF)
    m.building("repair", "neutral", 0, 1, 2, 11, REPAIR)
    m.building("repair", "neutral", 2, 2, 13, 2, REPAIR)
    m.building("radar", "neutral", 2, 1, 2, 12, RADAR)
    for x, y, k in [(8, 16, "gun"), (52, 16, "missile"), (30, 34, "howitzer"), (12, 40, "gatling"), (48, 40, "gatling"), (30, 58, "gun")]:
        m.unit("cannon", k, "neutral", x, y)
    m.unit("cannon", "gatling", "blue", 36, 12)
    m.unit("cannon", "gatling", "red", 24, 62)
    for x, y, k in [(10, 30, "tank_light"), (50, 46, "tank_light"), (30, 44, "apc"), (32, 28, "tank_heavy")]:
        m.unit("vehicle", k, "neutral", x, y)
    for x, y in [(27, 70), (29, 71), (31, 70)]:
        m.unit("robot", "grunt", "red", x, y)
    for x, y in [(36, 68), (37, 69)]:
        m.unit("robot", "sniper", "red", x, y)
    m.unit("robot", "pyro", "red", 24, 68)
    for x, y in [(27, 16), (29, 17), (31, 16)]:
        m.unit("robot", "grunt", "blue", x, y)
    for x, y in [(36, 16), (37, 17)]:
        m.unit("robot", "sniper", "blue", x, y)
    m.unit("robot", "laser", "blue", 24, 16)
    m.crate("grenades", 10, 46)
    m.crate("rockets", 50, 28)
    m.crate("rockets", 30, 50)
    m.props(["crystal", "crystal", "dead_tree", "ruin_pillar"], 90)
    return m


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    maps = [dust_bowl(), frost_line(), magma_works()]
    with open(OUT, "w") as f:
        f.write("; Iron Flags: the first campaign. Generated by tools/flags_maps.py (CC BY-SA 4.0).\n")
        for m in maps:
            f.write(m.text())
    for m in maps:
        print(m.name, m.w, "x", m.h, len(m.zones), "zones")
