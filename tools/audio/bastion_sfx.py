#!/usr/bin/env python3
"""Sound effects for game 2 (Bastion Coast), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/bastion_sfx.py [out_dir]   (default: godot/games/bastion/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/bastion/audio/sfx", seed=1990)
t, env, lp = s.t, s.env, s.lowpass

d = 1.4  # our cannon: a deep boom with a sharp crack
boom = s.sweep(95, 30, d) * env(int(SR * d), 0.002, 0.45, 3)
crack = lp(s.noise(d), np.geomspace(7000, 250, int(SR * d))) * env(int(SR * d), 0.0005, 0.2, 3)
s.save("cannon_fire", 1.2 * boom + crack + 0.5 * lp(s.noise(d), 160) * env(int(SR * d), 0.03, 0.9, 2.5), 0.9)

d = 1.2  # an enemy ship's cannon, further away: duller
s.save("ship_fire", lp(1.0 * s.sweep(80, 35, d) * env(int(SR * d), 0.004, 0.4, 3) +
                       0.7 * lp(s.noise(d), 900) * env(int(SR * d), 0.002, 0.3, 3), 1200), 0.6)

d = 0.9  # incoming shot: a falling whistle
s.save("whistle", s.sweep(2400, 700, d) * env(int(SR * d), 0.15, 0.7, 1.5) * (0.8 + 0.2 * np.sin(2 * np.pi * 9 * t(d))), 0.3)

d = 1.1  # splash
n = s.noise(d)
s.save("splash", lp(n, np.geomspace(5000, 400, len(n))) * env(len(n), 0.005, 0.5, 3) +
       0.4 * s.sweep(300, 120, d) * env(len(n), 0.002, 0.1), 0.7)

d = 1.3  # wall destroyed: crumbling stones
x = 0.8 * s.sweep(70, 35, d) * env(int(SR * d), 0.003, 0.3, 3)
for k in range(14):
    st = int(SR * (0.02 + k * 0.06 + s.rng.uniform(0, 0.04)))
    click = s.highpass(s.noise(0.05), 800) * env(int(SR * 0.05), 0.0005, 0.02)
    x[st:st + len(click)] += click * (1 - k / 16)
x += 0.6 * lp(s.noise(d), 600) * env(int(SR * d), 0.01, 0.6, 3)
s.save("wall_destroyed", x, 0.8)

d = 0.25  # placing a wall piece: a stone thunk
s.save("wall_place", s.sweep(180, 90, d) * env(int(SR * d), 0.002, 0.08) + 0.4 * lp(s.noise(d), 1500) * env(int(SR * d), 0.001, 0.03), 0.6)

d = 0.5  # placing a cannon: an iron clank
s.save("cannon_place", s.bell(420, d, ((1, 1), (2.4, 0.6), (4.1, 0.4)), 0.25) + 0.5 * s.highpass(s.noise(d), 3000) * env(int(SR * d), 0.0005, 0.02), 0.6)

d = 0.08  # rotating a piece: a small click
s.save("rotate", s.highpass(s.noise(d), 2500) * env(int(SR * d), 0.0005, 0.015) + 0.4 * np.sin(2 * np.pi * 1500 * t(d)) * env(int(SR * d), 0.0005, 0.02), 0.35)

d = 2.2  # a ship sinks: creak and bubbles
creak = s.sweep(140, 60, d, lambda p: np.sign(np.sin(p)) * 0.3 + np.sin(p)) * env(int(SR * d), 0.2, 1.2, 2)
bub = np.zeros(int(SR * d))
for k in range(30):
    st = int(s.rng.uniform(0.3, d - 0.2) * SR)
    b = s.sweep(s.rng.uniform(300, 700), s.rng.uniform(800, 1400), 0.06) * env(int(SR * 0.06), 0.002, 0.03)
    bub[st:st + len(b)] += b * 0.3
s.save("ship_sunk", lp(creak, 900) + bub + 0.3 * lp(s.noise(d), 300) * env(int(SR * d), 0.3, 1.0, 2), 0.7)

d = 1.4  # phase horn: a brass-like call on a fifth
tt = t(d)
horn = sum(np.sign(np.sin(2 * np.pi * f * tt)) * a for f, a in ((196, 0.5), (293.7, 0.35), (392, 0.2)))
s.save("horn", lp(horn, 1400) * env(len(tt), 0.08, 1.0, 2.2), 0.55)

d = 2.4  # game over: a slow falling lament
x = np.zeros(int(SR * d))
for i, f in enumerate([392, 349.2, 311.1, 293.7]):
    b = s.bell(f, 1.2, ((1, 1), (2, 0.4), (3, 0.2)), 0.8)
    st = int(SR * 0.4 * i)
    x[st:st + len(b)] += b
s.save("game_over", x, 0.6)
