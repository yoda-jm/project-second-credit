#!/usr/bin/env python3
"""Writes Tinplate Turbo's tracks (godot/games/tinplate/tracks/tracks.tin, our own designs, CC BY-SA 4.0).

Each track is a closed Catmull-Rom curve through hand-placed points on a 48 x 28 m board (x right, z down the screen),
an optional height per point (a bridge where a figure-eight crosses itself), hazards and ramps. The script checks that
no two parts of a track come closer than the road's width plus a margin (except over and under a bridge, and next to
each other along the road), and that everything stays on the board; `--preview DIR` draws each track as a PNG.
"""
import math, sys, os

W, H = 48.0, 28.0
TRACKS = [
    dict(name="Garden Party", theme=0, laps=5, width=4.6,
         points=[(8, 5), (24, 4), (40, 5), (44.5, 10), (43.5, 19.5), (37.5, 23.5), (31, 22.5), (27, 16.5), (21, 16.5),
                 (17, 22.5), (10, 23.5), (4, 19), (3.5, 10)],
         puddle=[(36, 5.2)]),
    dict(name="Canyon Eight", theme=1, laps=5, width=4.4,
         points=[(10, 23.4), (17, 20), (24, 14, 0), (31, 8), (38, 4.6), (44, 8), (44.5, 14), (44, 20), (38, 23.4), (31, 20),
                 (24, 14, 2.4), (17, 8), (10, 4.6), (4, 8), (3.5, 14), (4, 20)],
         ramp=[(44.4, 14)], oil=[(5, 16)]),
    dict(name="Snowdrift Bends", theme=2, laps=5, width=4.6,
         points=[(6, 5), (20, 4.2), (27, 8), (34, 4.5), (43, 6), (44.5, 13), (38, 16), (40, 22.5), (30, 24), (22, 19.5),
                 (14, 24), (5, 21), (3.8, 13)],
         oil=[(39.5, 16.5)], puddle=[(24, 21)]),
    dict(name="Harbour Lights", theme=3, laps=5, width=4.6,
         points=[(6, 5), (26, 4.5), (42, 5), (43.8, 10), (39.5, 11.5), (38, 14.5), (39.5, 17.5), (43.8, 19), (42, 23.5),
                 (24, 23.5), (6, 23.5), (4.2, 19), (8.5, 17.5), (10, 14.5), (8.5, 11.5), (4.2, 10)],
         ramp=[(24, 23.5)], puddle=[(16, 4.9), (32, 23.5)]),
    dict(name="Neon Crossing", theme=4, laps=6, width=4.2,
         points=[(6, 4.8), (18, 4.8), (24, 8), (30, 14, 0), (36, 20), (42, 23.5), (45.2, 17), (43, 6.5), (36, 8, 1.0),
                 (30, 14, 2.4), (24, 20, 1.0), (18, 23.5), (6, 23.5), (3.5, 14)],
         oil=[(40, 4.9), (8, 23.4)]),
    dict(name="Autumn Woods", theme=5, laps=5, width=4.6,
         points=[(6, 6), (14, 4), (22, 8), (30, 4), (40, 5), (44.5, 12), (40, 17), (44, 23), (32, 24), (26, 19), (18, 24), (8, 23),
                 (4, 15)],
         puddle=[(22.2, 8.5), (26.2, 19.5)], ramp=[(35, 4.4)]),
]


def cr(a, b, c, d, t):
    return tuple(0.5 * ((2 * b[i]) + (-a[i] + c[i]) * t + (2 * a[i] - 5 * b[i] + 4 * c[i] - d[i]) * t * t
                        + (-a[i] + 3 * b[i] - 3 * c[i] + d[i]) * t * t * t) for i in range(3))


def samples(tr):
    pts = [(p[0], p[1], p[2] if len(p) > 2 else 0.0) for p in tr["points"]]
    n = len(pts)
    out = []
    for i in range(n):
        for k in range(30):
            out.append(cr(pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n], k / 30))
    # evenly every 0.5 m
    cum = [0.0]
    for i in range(1, len(out) + 1):
        a, b = out[i - 1], out[i % len(out)]
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = cum[-1]
    cnt = int(L / 0.5)
    res = []
    j = 0
    for s in range(cnt):
        want = s * L / cnt
        while j < len(out) - 1 and cum[j + 1] < want:
            j += 1
        f = (want - cum[j]) / max(1e-6, cum[j + 1] - cum[j])
        a, b = out[j], out[(j + 1) % len(out)]
        res.append(tuple(a[i] + (b[i] - a[i]) * f for i in range(3)))
    return res, L


def check(tr):
    s, L = samples(tr)
    n = len(s)
    w = tr["width"]
    problems = []
    for i in range(n):
        x, z, h = s[i]
        if x < w / 2 + 0.6 or x > W - w / 2 - 0.6 or z < w / 2 + 0.6 or z > H - w / 2 - 0.6:
            problems.append(f"off the board at sample {i} ({x:.1f},{z:.1f})")
            break
    worst = 99.0
    for i in range(0, n, 2):
        for j in range(i + 1, n, 2):
            along = min(abs(i - j), n - abs(i - j)) * 0.5
            if along < w * 2.2:
                continue
            if abs(s[i][2] - s[j][2]) > 0.9:
                continue   # over and under a bridge
            d = math.hypot(s[i][0] - s[j][0], s[i][1] - s[j][1])
            worst = min(worst, d)
            if d < w + 1.0:
                problems.append(f"parts too close: samples {i} and {j} ({d:.1f} m)")
                return problems, L, worst
    return problems, L, worst


def write(path):
    lines = ["; Tinplate Turbo tracks: our own designs, CC BY-SA 4.0 (made by tools/tinplate_tracks.py).",
             "; Board 48 x 28 m, x right, z down the screen; points x,z[,height]."]
    for tr in TRACKS:
        lines += ["", "[track]", f"name={tr['name']}", f"theme={tr['theme']}", f"laps={tr['laps']}", f"width={tr['width']}",
                  "points=" + " ".join(",".join(f"{v:g}" for v in p) for p in tr["points"])]
        for k in ("oil", "puddle", "ramp"):
            for p in tr.get(k, []):
                lines.append(f"{k}={p[0]:g},{p[1]:g}")
    open(path, "w").write("\n".join(lines) + "\n")


def preview(tr, path):
    from PIL import Image, ImageDraw
    k = 16
    im = Image.new("RGB", (int(W * k), int(H * k)), (60, 110, 60))
    d = ImageDraw.Draw(im)
    s, _ = samples(tr)
    for x, z, h in s:
        r = tr["width"] / 2 * k
        col = (90, 90, 95) if h < 0.5 else (150, 120, 90)
        d.ellipse((x * k - r, z * k - r, x * k + r, z * k + r), fill=col)
    for i, (x, z, h) in enumerate(s):
        if i % 4 == 0:
            d.point((x * k, z * k), fill=(255, 255, 255))
    for p in tr.get("oil", []):
        d.ellipse((p[0] * k - 15, p[1] * k - 15, p[0] * k + 15, p[1] * k + 15), fill=(20, 20, 20))
    for p in tr.get("puddle", []):
        d.ellipse((p[0] * k - 15, p[1] * k - 15, p[0] * k + 15, p[1] * k + 15), fill=(80, 140, 220))
    for p in tr.get("ramp", []):
        d.rectangle((p[0] * k - 10, p[1] * k - 10, p[0] * k + 10, p[1] * k + 10), fill=(240, 160, 40))
    x, z, _ = s[0]
    d.line((x * k - 30, z * k, x * k + 30, z * k), fill=(255, 255, 255), width=3)
    im.save(path)


if __name__ == "__main__":
    ok = True
    for tr in TRACKS:
        probs, L, worst = check(tr)
        print(f"{tr['name']}: {L:.0f} m, closest other part {worst:.1f} m", "OK" if not probs else probs)
        ok = ok and not probs
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(out, exist_ok=True)
        for i, tr in enumerate(TRACKS):
            preview(tr, os.path.join(out, f"track_{i}.png"))
    if ok or "--force" in sys.argv:
        write(os.path.join(os.path.dirname(__file__), "..", "godot", "games", "tinplate", "tracks", "tracks.tin"))
    sys.exit(0 if ok else 1)
