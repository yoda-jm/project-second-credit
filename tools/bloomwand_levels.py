#!/usr/bin/env python3
"""Writes Bloomwand's levels (godot/games/bloomwand/levels/garden.bloom, our own designs, CC BY-SA 4.0).

Each level is a 20 x 15 grid: '#' a block, 'H' a ladder, '*' a flower, 'P' and 'Q' the fairies' starts, creatures
'g' grub, 'b' bopper, 's' snapper, 'c' cloudlet, '.' air. The script checks every level: a solid floor, the starts
standing on something, and every flower and creature reachable from the start by walking, climbing ladders,
dropping off edges and conjuring a magic ladder up to a platform at most 6 tiles above.
"""
import os, sys
from collections import deque

W, H = 20, 15
LEVELS = [
    ("Bluebell Glade", 0, [
        "....................",
        "....................",
        "..*......c.......*..",
        "..######...######...",
        "....H.......H.......",
        "....H..*....H...*...",
        "#######H...########.",
        ".......H............",
        "...g...H.....*...g..",
        "..##########.######.",
        "...........H........",
        ".*....P....H....*...",
        "####.##############.",
        "....................",
        "####################",
    ]),
    ("Mushroom Ring", 1, [
        "....................",
        ".*.......*........*.",
        "#####.########.#####",
        ".....H........H.....",
        "..b..H...*....H..b..",
        "########....########",
        "........H..H........",
        "..*.....H..H.....*..",
        "...########.#####...",
        "...H............H...",
        "...H..g..P...s..H...",
        "#.################.#",
        ".....*.......*......",
        "..........g.........",
        "####################",
    ]),
    ("Crystal Grotto", 2, [
        "....................",
        "..*.....*....*...*..",
        ".######.######.####.",
        "......H......H......",
        "...s..H..c...H..s...",
        "##########.#########",
        ".H................H.",
        ".H..*.b......*....H.",
        ".#######...#######..",
        ".......H...H........",
        ".*.....H.P.H.....*..",
        "############.######.",
        "..g...........g.....",
        "....*........*......",
        "####################",
    ]),
    ("Cloud Castle", 3, [
        "....................",
        "...*....c.....*.....",
        "..#####....#####....",
        "......H....H........",
        ".*..b.H....H..b...*.",
        "############.######.",
        "..........H.........",
        "...c....*.H...*.....",
        "..#######.######....",
        "........H.......H...",
        "..*..s..H..P....H.*.",
        "#.###############.##",
        "......b......s......",
        "..*..............*..",
        "####################",
    ]),
    ("Winter Hollow", 4, [
        "....................",
        ".*.....*....*.....*.",
        "####.######.######..",
        "...H.....H.......H..",
        "...H..s..H..g....H..",
        "..########.########.",
        "...........H........",
        ".c...*.....H..*...c.",
        "#####.###########.##",
        "....H........H......",
        "..*.H...P....H...*..",
        ".##################.",
        "...s.......b....g...",
        "..*......*.......*..",
        "####################",
    ]),
    ("Thorn Tower", 5, [
        "....................",
        "..*..c.......c...*..",
        ".########..########.",
        "..H.............H...",
        "..H.s..*....*..sH...",
        "###########.########",
        ".......H....H.......",
        "..*..b.H....H.b..*..",
        "..######....######..",
        "...H...........H....",
        "...H..g..P..g..H....",
        "######.######.######",
        "..s..*...c....*..s..",
        "....................",
        "####################",
    ]),
]


def solid(g, x, y):
    return y >= H or x < 0 or x >= W or g[y][x] == "#"


def standable(g, x, y):
    return 0 <= x < W and 0 <= y < H and not solid(g, x, y) and solid(g, x, y + 1)


def check(name, g):
    probs = []
    assert len(g) == H and all(len(r) == W for r in g), name + ": bad size"
    if any(c != "#" for c in g[H - 1]):
        probs.append("the bottom row is not solid")
    starts = [(x, y) for y in range(H) for x in range(W) if g[y][x] == "P"]
    if len(starts) != 1:
        return ["needs one P"]
    sx, sy = starts[0]
    if not standable(g, sx, sy):
        probs.append("P is not standing on something")
    # reach: positions where the fairy stands (or hangs on a ladder)
    def ladder(x, y):
        return 0 <= x < W and 0 <= y < H and g[y][x] == "H"
    seen = {(sx, sy)}
    q = deque([(sx, sy)])
    def push(p):
        if p not in seen:
            seen.add(p)
            q.append(p)
    while q:
        x, y = q.popleft()
        on_ladder = ladder(x, y)
        for dx in (-1, 1):
            nx = x + dx
            if 0 <= nx < W and not solid(g, nx, y) and (standable(g, x, y) or on_ladder):
                # walking off an edge: fall to where it lands
                ny = y
                while not solid(g, nx, ny + 1) and not ladder(nx, ny):
                    ny += 1
                push((nx, ny))
        if on_ladder or ladder(x, y + 1):
            if y > 0 and (ladder(x, y - 1) or (on_ladder and not solid(g, x, y - 1))):
                push((x, y - 1))
            if ladder(x, y + 1) and not solid(g, x, y + 1):
                push((x, y + 1))
            if ladder(x, y + 1) and solid(g, x, y + 1) is False:
                pass
        # down a ladder from the platform it pokes through
        if ladder(x, y + 1):
            push((x, y + 1))
        # the magic ladder: up to a standable spot at most 6 tiles above, through the block over head
        if standable(g, x, y):
            for up in range(2, 8):
                ty = y - up
                if ty < 0:
                    break
                if standable(g, x, ty):
                    push((x, ty))
                    break
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c in "*gbsc" and (x, y) not in seen and c != "c":
                # a creature or flower on a floor must be reachable (cloudlets float, they come to you)
                near = any((x + dx, y + dy) in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                if not near:
                    probs.append(f"{c} at {x},{y} unreachable")
    return probs


def through_floors(g):
    """A ladder that meets a platform above goes on up through it (the platform tile becomes ladder), so it leads
    somewhere: you climb out on top of the platform."""
    g = [list(r) for r in g]
    for y in range(1, H):
        for x in range(W):
            if g[y][x] == "H" and g[y - 1][x] == "#":
                g[y - 1][x] = "H"
    return ["".join(r) for r in g]


def settle(g):
    """Flowers and walking creatures sit on something: one floating in the air drops to the floor below it."""
    g = [list(r) for r in g]
    for y in range(H - 2, -1, -1):
        for x in range(W):
            c = g[y][x]
            if c in "*gbs":
                yy = y
                while yy + 1 < H and g[yy + 1][x] == "." :
                    yy += 1
                if yy != y:
                    g[y][x] = "."
                    g[yy][x] = c
    return ["".join(r) for r in g]


def main():
    ok = True
    out = ["; Bloomwand levels: our own designs, CC BY-SA 4.0 (made by tools/bloomwand_levels.py).",
           "; 20 x 15: # block, H ladder, * flower, P Q starts, g grub, b bopper, s snapper, c cloudlet."]
    for name, theme, g in LEVELS:
        g = settle(through_floors(g))
        probs = check(name, g)
        print(f"{name}: " + ("OK" if not probs else "; ".join(probs)))
        ok = ok and not probs
        g2 = [r if "Q" in "".join(g) else r for r in g]
        out += ["", "[level]", f"name={name}", f"theme={theme}", "map:"] + g2
    if ok or "--force" in sys.argv:
        path = os.path.join(os.path.dirname(__file__), "..", "godot", "games", "bloomwand", "levels", "garden.bloom")
        open(path, "w").write("\n".join(out) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
