#!/usr/bin/env python3
"""Generates a seamless water normal map (godot/core/art/textures/water/normal.png) from a sum of many waves
whose frequencies are integers per tile, so the result tiles perfectly and has no grid. CC BY-SA 4.0 (ours).
Usage: python3 tools/art_water_normals.py [size]"""
import sys, zlib, struct
import numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
rng = np.random.default_rng(2026)
u = np.linspace(0, 1, N, endpoint=False)
X, Y = np.meshgrid(u, u)
h = np.zeros((N, N))
for k in range(90):
    # integer wave vectors keep the tile seamless; a spread of lengths gives swell plus fine ripples
    r = rng.uniform(2, 22) ** 1.1
    a = rng.uniform(0, 2 * np.pi)
    kx, ky = int(round(r * np.cos(a))), int(round(r * np.sin(a)))
    if kx == 0 and ky == 0:
        continue
    amp = 1.0 / (np.hypot(kx, ky) ** 1.35)
    h += amp * np.sin(2 * np.pi * (kx * X + ky * Y) + rng.uniform(0, 2 * np.pi))
# sharpen crests a little (water waves are peaky)
h = h - h.min()
h = h / h.max()
h = h ** 1.4
gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * N / 2
gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * N / 2
strength = 0.035
nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(h)
l = np.sqrt(nx * nx + ny * ny + nz * nz)
img = np.stack([(nx / l + 1) * 127.5, (-ny / l + 1) * 127.5, (nz / l + 1) * 127.5], -1).astype(np.uint8)


def png(path, a):
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(a.shape[0]))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", a.shape[1], a.shape[0], 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


png("godot/core/art/textures/water/normal.png", img)
print("wrote water normal map", N)
