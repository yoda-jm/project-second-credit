#!/usr/bin/env python3
"""Marble Drift's courses (our own designs, CC BY-SA 4.0), written into godot/games/marbledrift/courses/courses.drift.
Each course is built from primitives on a grid (1 unit per cell, x across, z down the course): platforms, ramps
(a steep ramp is a drop: the marble flies off and may shatter), walls, acid, glass (slippery) and rough floors, the
goal, enemies, and the route the demo marble follows (its points are also the checkpoints).
Usage: python3 tools/marble_courses.py"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "godot", "games", "marbledrift", "courses", "courses.drift")


class Course:
    def __init__(self, name, w, h, time, theme):
        self.name, self.w, self.h, self.time, self.theme = name, w, h, time, theme
        self.cells = [["_"] * w for _ in range(h)]
        self.v = [[0.0] * (w + 1) for _ in range(h + 1)]
        self.start = (1.5, 1.5)
        self.route = []
        self.enemies = []

    def _verts(self, x0, z0, x1, z1, f):
        for z in range(z0, z1 + 2):
            for x in range(x0, x1 + 2):
                if 0 <= z <= self.h and 0 <= x <= self.w:
                    self.v[z][x] = f(x, z)

    def plat(self, x0, z0, x1, z1, y, kind="."):
        """A flat platform over cells x0..x1, z0..z1 at height y."""
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                self.cells[z][x] = kind
        self._verts(x0, z0, x1, z1, lambda x, z: y)

    def ramp(self, x0, z0, x1, z1, ya, yb, axis="z", kind="."):
        """A ramp from height ya to yb along an axis (z: from row z0 to row z1 + 1; x: from column x0 to x1 + 1)."""
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                self.cells[z][x] = kind
        if axis == "z":
            n = z1 + 1 - z0
            self._verts(x0, z0, x1, z1, lambda x, z: ya + (yb - ya) * (z - z0) / n)
        else:
            n = x1 + 1 - x0
            self._verts(x0, z0, x1, z1, lambda x, z: ya + (yb - ya) * (x - x0) / n)

    def wall(self, x0, z0, x1, z1, y):
        """A low wall (rail) over cells, standing on the floor height y (it rises 1.5 above it)."""
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                self.cells[z][x] = "#"
        # its own vertices, without lowering a neighbouring floor's shared edge
        for z in range(z0, z1 + 2):
            for x in range(x0, x1 + 2):
                if 0 <= z <= self.h and 0 <= x <= self.w:
                    self.v[z][x] = max(self.v[z][x], y)

    def mark(self, x0, z0, x1, z1, kind):
        """Changes the kind of existing floor cells (acid, glass, rough, goal)."""
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if self.cells[z][x] != "_":
                    self.cells[z][x] = kind

    def text(self):
        out = ["[course]", "name=" + self.name, "time=%d" % self.time, "theme=%d" % self.theme,
               "size=%d,%d" % (self.w, self.h), "start=%g,%g" % self.start,
               "route=" + " ".join(",".join("%g" % v for v in p) for p in self.route)]
        for e in self.enemies:
            out.append("enemy=" + ",".join(str(v) for v in e))
        out.append("heights:")
        for row in self.v:
            out.append(" ".join(str(int(round(y * 10))) for y in row))
        out.append("cells:")
        for row in self.cells:
            out.append("".join(row))
        return "\n".join(out) + "\n"


courses = []

# 1: First Light (practice): wide ramps, two easy turns, the goal at the bottom
c = Course("First Light", 16, 48, 30, 0)
c.plat(4, 0, 11, 5, 12)
c.wall(3, 0, 3, 5, 12); c.wall(12, 0, 12, 5, 12)
c.ramp(4, 6, 11, 15, 12, 8)
c.plat(2, 16, 13, 21, 8)
c.ramp(8, 22, 13, 31, 8, 4)
c.plat(2, 32, 13, 37, 4)
c.ramp(2, 38, 7, 41, 4, 2)
c.plat(2, 42, 9, 47, 2)
c.mark(2, 45, 9, 47, "G")
c.start = (7.5, 2.5)
c.route = [(7.5, 8.0), (7.5, 14.0), (10.5, 19.0), (10.5, 27.0), (10.5, 33.5), (5.0, 35.5), (4.5, 40.0), (5.5, 46.0)]
courses.append(c)

# 2: Glass Steps: terraces dropping in safe steps, glass lanes, a narrow bridge over the void, an acid pool, a steelie
c = Course("Glass Steps", 18, 56, 35, 1)
c.plat(5, 0, 12, 5, 16)
c.wall(4, 0, 4, 5, 16); c.wall(13, 0, 13, 5, 16)
c.ramp(5, 6, 12, 9, 16, 14, kind="=")
c.plat(3, 10, 14, 15, 14)
c.ramp(3, 16, 14, 16, 14, 12)            # a step down: 2 units over one cell
c.plat(3, 17, 14, 22, 12)
c.mark(9, 18, 11, 20, "~")               # an acid pool to steer round
c.plat(7, 23, 9, 30, 12)                 # the narrow bridge
c.plat(3, 31, 14, 36, 12, "=")
c.ramp(3, 37, 14, 42, 12, 8, kind="^")
c.plat(3, 43, 14, 49, 8)
c.wall(2, 43, 2, 49, 8); c.wall(15, 43, 15, 49, 8)
c.ramp(6, 50, 11, 51, 8, 6)
c.plat(6, 52, 11, 55, 6)
c.mark(6, 53, 11, 55, "G")
c.start = (8.5, 2.5)
c.route = [(8.5, 8.0), (8.5, 12.5), (8.5, 16.5), (5.5, 19.5), (5.5, 21.5), (8.5, 23.5), (8.5, 30.5), (8.5, 34.0),
           (8.5, 40.0), (8.5, 46.0), (8.5, 51.0), (8.5, 54.0)]
c.enemies = [("steelie", 12.5, 33.5)]
courses.append(c)

# 3: Hopper Heights: narrow walkways with hoppers patrolling across them, a drop, a glass terrace
c = Course("Hopper Heights", 20, 60, 45, 2)
c.plat(7, 0, 12, 4, 18)
c.ramp(8, 5, 11, 10, 18, 15)
c.plat(8, 11, 11, 18, 15)
c.plat(2, 19, 11, 22, 15)
c.plat(2, 23, 5, 32, 15)
c.ramp(2, 33, 5, 33, 15, 12.5)
c.plat(2, 34, 13, 39, 12.5, "=")
c.ramp(10, 40, 13, 47, 12.5, 10)
c.plat(6, 48, 15, 53, 10)
c.plat(8, 54, 13, 59, 10)
c.mark(8, 56, 13, 59, "G")
c.start = (9.5, 2.0)
c.route = [(9.5, 8.0), (9.5, 13.0), (9.5, 17.0), (6.5, 20.5), (3.5, 22.5), (3.5, 28.0), (3.5, 33.0), (3.5, 36.5),
           (8.0, 37.0), (11.5, 39.5), (11.5, 45.0), (10.5, 50.5), (10.5, 57.0)]
c.enemies = [("hopper", 8.5, 14.5, 11.5, 14.5), ("hopper", 2.5, 27.5, 5.5, 27.5), ("hopper", 7.0, 51.0, 14.0, 51.0)]
courses.append(c)

# 4: Neon Gap: a long run down, a leap over the void to a lower deck, a narrow ramp, acid stripes
c = Course("Neon Gap", 16, 56, 35, 3)
c.plat(5, 0, 10, 5, 20)
c.ramp(5, 6, 10, 17, 20, 14)
c.plat(4, 18, 11, 21, 14)
c.plat(3, 25, 12, 32, 12)
c.ramp(6, 33, 9, 38, 12, 9)
c.plat(3, 39, 12, 44, 9)
c.mark(3, 41, 5, 42, "~"); c.mark(10, 41, 12, 42, "~")
c.ramp(5, 45, 10, 48, 9, 7)
c.plat(5, 49, 10, 55, 7)
c.mark(5, 52, 10, 55, "G")
c.start = (7.5, 2.5)
c.route = [(7.5, 8.0), (7.5, 15.0, 8.0), (7.5, 21.5, 9.5), (7.5, 27.0, 9.0), (7.5, 32.0), (7.5, 37.0), (7.5, 42.0),
           (7.5, 47.0), (7.5, 53.0)]
courses.append(c)

# 5: Steel Storm: an open deck with two steelies on the hunt and acid patches, a rough ramp, a third steelie
c = Course("Steel Storm", 22, 50, 45, 4)
c.plat(8, 0, 13, 4, 16)
c.wall(7, 0, 7, 4, 16); c.wall(14, 0, 14, 4, 16)
c.ramp(6, 5, 15, 12, 16, 12)
c.plat(2, 13, 19, 28, 12)
c.mark(9, 18, 12, 19, "~"); c.mark(5, 24, 7, 25, "~")
c.ramp(8, 29, 13, 36, 12, 8, kind="^")
c.plat(4, 37, 17, 42, 8)
c.ramp(8, 43, 13, 45, 8, 6)
c.plat(8, 46, 13, 49, 6)
c.mark(8, 47, 13, 49, "G")
c.start = (10.5, 2.0)
c.route = [(10.5, 8.0), (10.5, 14.0), (14.5, 17.0), (14.5, 22.0), (10.5, 27.0), (10.5, 33.0), (10.5, 39.0),
           (10.5, 44.0), (10.5, 48.0)]
c.enemies = [("steelie", 4.5, 20.5), ("steelie", 17.5, 22.5), ("steelie", 15.5, 40.0)]
courses.append(c)

# 6: Aurora Run: a long winding descent: glass, a drop, rough decks, hoppers and a steelie
c = Course("Aurora Run", 24, 70, 60, 5)
c.plat(2, 0, 7, 4, 24)
c.ramp(2, 5, 7, 12, 24, 20)
c.plat(2, 13, 21, 16, 20, "=")
c.ramp(18, 17, 21, 26, 20, 16)
c.plat(6, 27, 21, 30, 16)
c.plat(6, 31, 9, 36, 16)
c.ramp(6, 37, 9, 37, 16, 13.5)
c.plat(6, 38, 19, 43, 13.5, "^")
c.ramp(14, 44, 19, 53, 13.5, 9, kind="=")
c.plat(8, 54, 19, 59, 9)
c.ramp(8, 60, 11, 63, 9, 7)
c.plat(6, 64, 13, 69, 7)
c.mark(6, 66, 13, 69, "G")
c.start = (4.5, 2.0)
c.route = [(4.5, 10.0), (4.5, 14.5), (10.0, 14.5), (19.5, 14.5), (19.5, 21.0), (19.5, 28.5), (12.0, 28.5),
           (7.5, 30.0), (7.5, 35.0), (7.5, 39.0), (12.0, 40.5), (16.5, 42.5), (16.5, 49.0), (16.5, 55.0), (10.0, 57.0),
           (9.5, 62.0), (9.5, 67.0)]
c.enemies = [("hopper", 10.0, 28.5, 17.0, 28.5), ("steelie", 18.0, 40.5)]
courses.append(c)

open(OUT, "w").write("; Marble Drift: our own courses (CC BY-SA 4.0), made by tools/marble_courses.py.\n\n" +
                     "\n".join(c.text() for c in courses))
print("wrote", len(courses), "courses to", OUT)
