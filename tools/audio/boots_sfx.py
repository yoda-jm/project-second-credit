#!/usr/bin/env python3
"""Sound effects for game 6 (Muddy Boots), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/boots_sfx.py [out_dir]   (default: godot/games/boots/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/boots/audio/sfx", seed=1993)
t, env, lp = s.t, s.env, s.lowpass


def n(sec):
    return int(SR * sec)


def mix(x, start, b):
    b = b[:max(0, len(x) - start)]
    x[start:start + len(b)] += b


d = 0.35  # our rifle: a sharp crack and a short thump
x = s.highpass(s.noise(d), 1200) * env(n(d), 0.0005, 0.04, 4) + 0.7 * s.sweep(160, 60, d) * env(n(d), 0.001, 0.06, 3)
s.save("shot", x + 0.3 * lp(s.noise(d), 800) * env(n(d), 0.002, 0.2, 3), 0.6)

d = 0.4  # the enemy's rifle: duller, further away
s.save("enemy_shot", lp(s.noise(d), 2500) * env(n(d), 0.001, 0.06, 4) + 0.5 * s.sweep(120, 50, d) * env(n(d), 0.002, 0.08, 3), 0.45)

d = 0.15  # a bullet hitting the ground
s.save("impact", lp(s.noise(d), 3000) * env(n(d), 0.0005, 0.03, 4), 0.3)

d = 0.4  # a grenade thrown
s.save("throw", lp(s.noise(d), np.geomspace(500, 2000, n(d))) * env(n(d), 0.03, 0.2, 2), 0.3)

d = 2.0  # an explosion: a deep boom, a crack and falling debris
boom = s.sweep(80, 25, d) * env(n(d), 0.002, 0.6, 3)
crack = lp(s.noise(d), np.geomspace(6000, 200, n(d))) * env(n(d), 0.0005, 0.35, 3)
debris = np.zeros(n(d))
for k in range(12):
    mix(debris, n(0.3 + k * 0.1 + s.rng.uniform(0, 0.05)), s.highpass(s.noise(0.04), 1000) * env(n(0.04), 0.0005, 0.02) * (1 - k / 13))
s.save("explosion", 1.3 * boom + crack + 0.3 * debris + 0.5 * lp(s.noise(d), 150) * env(n(d), 0.01, 1.0, 2), 0.9)

d = 1.2  # a rocket: the launch whoosh and the hiss
s.save("rocket", lp(s.noise(d), np.geomspace(800, 5000, n(d))) * env(n(d), 0.01, 0.8, 1.5) + 0.4 * s.sweep(200, 90, d) * env(n(d), 0.002, 0.2, 3), 0.55)

d = 0.9  # a splash in the river
s.save("splash", lp(s.noise(d), np.geomspace(5000, 400, n(d))) * env(n(d), 0.004, 0.45, 3), 0.6)

d = 0.4  # a soldier falls: a short, low "ugh"
tt = t(d)
f0 = 180 - 80 * tt / d
ph = np.cumsum(f0) / SR
voice = (2 * (ph % 1.0) - 1.0)
s.save("ugh", lp(voice, 900) * env(n(d), 0.01, 0.2, 2.5), 0.4)

d = 1.4  # a hut collapsing: splintering wood
x = np.zeros(n(d))
for k in range(20):
    c = s.bell(s.rng.uniform(300, 900), 0.12, partials=((1, 1.0), (2.3, 0.5)), decay=0.05) * 0.4
    mix(x, n(s.rng.uniform(0, 0.8)), c)
x += 0.6 * lp(s.noise(d), 700) * env(n(d), 0.02, 0.8, 2)
s.save("collapse", x, 0.7)

d = 0.25  # picking up supplies
x = np.zeros(n(d))
mix(x, 0, s.highpass(s.noise(0.03), 2000) * env(n(0.03), 0.0005, 0.01))
mix(x, n(0.08), np.sin(2 * np.pi * 1200 * t(0.12)) * env(n(0.12), 0.002, 0.08))
s.save("pickup", x, 0.4)

d = 1.4  # a hostage rescued: a small cheer
x = (lp(s.noise(d), 2200) - lp(s.noise(d), 350)) * env(n(d), 0.1, 1.0, 1.8)
s.save("cheer", x, 0.45)

d = 2.4  # mission complete: a bugle call
x = np.zeros(n(d))
for st, ln, f in ((0.0, 0.18, 523.3), (0.2, 0.18, 659.3), (0.4, 0.18, 784.0), (0.62, 0.9, 1046.5), (1.55, 0.7, 784.0)):
    tt = t(ln + 0.2)
    horn = sum((0.8 ** k) * np.sin(2 * np.pi * f * k * tt) for k in range(1, 6)) * env(len(tt), 0.02, ln * 0.7 + 0.15, 1.5)
    mix(x, n(st), lp(horn, 3000))
s.save("mission_won", x, 0.6)

d = 2.2  # squad lost: a slow falling horn
x = np.zeros(n(d))
for st, f in ((0.0, 392.0), (0.6, 349.2), (1.2, 293.7)):
    tt = t(0.9)
    horn = sum((0.7 ** k) * np.sin(2 * np.pi * f * k * tt) for k in range(1, 5)) * env(len(tt), 0.05, 0.7, 1.5)
    mix(x, n(st), lp(horn, 2000))
s.save("mission_lost", x, 0.55)
