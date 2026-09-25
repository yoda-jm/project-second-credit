#!/usr/bin/env python3
"""Sound effects for game 7 (Neon Knuckles), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/knuckles_sfx.py [out_dir]   (default: godot/games/knuckles/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/knuckles/audio/sfx", seed=1987)
t, env, lp = s.t, s.env, s.lowpass


def n(sec):
    return int(SR * sec)


def mix(x, start, b):
    b = b[:max(0, len(x) - start)]
    x[start:start + len(b)] += b


d = 0.25  # a punch: a dull body thump and a slap
thump = s.sweep(140, 55, d) * env(n(d), 0.001, 0.06, 3)
slap = s.highpass(s.noise(d), 1500) * env(n(d), 0.0005, 0.02, 4)
s.save("punch", thump + 0.6 * slap, 0.7)
d = 0.35  # a heavy blow (hook, kick, throw landing)
s.save("heavy", 1.2 * s.sweep(110, 40, d) * env(n(d), 0.001, 0.1, 3) + 0.7 * lp(s.noise(d), 2500) * env(n(d), 0.0005, 0.05, 4), 0.85)
d = 0.2  # a swing that misses: a whoosh
s.save("swing", lp(s.noise(d), np.geomspace(700, 3000, n(d))) * np.sin(np.pi * np.clip(t(d) / d, 0, 1)), 0.3)
d = 0.3  # the bat: a wooden crack
s.save("bat", s.bell(900, d, partials=((1, 1.0), (2.3, 0.6), (4.2, 0.3)), decay=0.08) + 0.5 * s.sweep(160, 60, d) * env(n(d), 0.001, 0.06), 0.8)
d = 0.25  # a knife slash
s.save("slash", s.highpass(s.noise(d), 4000) * env(n(d), 0.003, 0.08, 3) + 0.3 * s.sweep(3000, 6000, d) * env(n(d), 0.002, 0.05), 0.4)
d = 0.35  # a grunt
tt = t(d)
f0 = 150 - 50 * tt / d
voice = 2 * ((np.cumsum(f0) / SR) % 1.0) - 1.0
s.save("grunt", lp(voice, 800) * env(n(d), 0.01, 0.15, 2.5), 0.45)
d = 0.6  # someone hits the pavement
s.save("fall", s.sweep(90, 40, d) * env(n(d), 0.002, 0.2, 3) + 0.5 * lp(s.noise(d), 600) * env(n(d), 0.003, 0.25, 3), 0.8)
d = 1.0  # a KO: a descending sting
x = np.zeros(n(d))
for i, f in enumerate((660.0, 523.3, 392.0)):
    mix(x, n(i * 0.12), np.sign(np.sin(2 * np.pi * f * t(0.3))) * env(n(0.3), 0.005, 0.2, 2) * 0.3)
s.save("ko", lp(x, 3000), 0.5)
d = 0.2  # picking up a weapon
s.save("pickup", np.sin(2 * np.pi * np.cumsum(np.geomspace(500, 1500, n(d))) / SR) * env(n(d), 0.002, 0.12), 0.35)
d = 0.8  # GO: two bright chimes
x = np.zeros(n(d))
for i, f in enumerate((880.0, 1318.5)):
    mix(x, n(i * 0.15), s.bell(f, 0.6, decay=0.25))
s.save("go", x, 0.45)
d = 2.0  # stage clear: a synth arpeggio
x = np.zeros(n(d))
for i, f in enumerate((440.0, 554.4, 659.3, 880.0, 1108.7, 1318.5)):
    mix(x, n(i * 0.09), np.sign(np.sin(2 * np.pi * f * t(0.5))) * env(n(0.5), 0.003, 0.35, 1.5) * 0.25)
s.save("clear", lp(x, 5000), 0.55)
d = 2.0  # game over
x = np.zeros(n(d))
for i, f in enumerate((392.0, 369.99, 349.2, 329.6)):
    mix(x, n(i * 0.35), np.sign(np.sin(2 * np.pi * f * t(0.7))) * env(n(0.7), 0.005, 0.5, 1.5) * 0.25)
s.save("game_over", lp(x, 2500), 0.55)
