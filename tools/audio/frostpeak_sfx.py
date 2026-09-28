#!/usr/bin/env python3
"""Sound effects for game 5 (Frostpeak Games), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/frostpeak_sfx.py [out_dir]   (default: godot/games/frostpeak/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/frostpeak/audio/sfx", seed=1985)
t, env, lp = s.t, s.env, s.lowpass


def n(sec):
    return int(SR * sec)


def mix(x, start, b):
    b = b[:max(0, len(x) - start)]
    x[start:start + len(b)] += b


d = 4.0  # the crowd: many voices as band-limited noise with slow swells (loops)
x = lp(s.noise(d), 1400) - lp(s.noise(d), 250)
swell = 0.7 + 0.3 * np.sin(2 * np.pi * 0.35 * t(d)) * np.sin(2 * np.pi * 0.13 * t(d))
x *= swell
fade = n(0.3)
x[:fade] = x[:fade] * np.linspace(0, 1, fade) + x[-fade:] * np.linspace(1, 0, fade)  # seamless loop
s.save("crowd", x[:-fade], 0.5)

d = 2.0  # a cheer: the crowd rising
x = (lp(s.noise(d), 2500) - lp(s.noise(d), 300)) * env(n(d), 0.25, 1.4, 1.5)
for k in range(10):  # a few whistles
    st = n(s.rng.uniform(0.1, 0.9))
    f0 = s.rng.uniform(1800, 2600)
    w = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f0 * 1.3, n(0.3))) / SR) * env(n(0.3), 0.02, 0.2, 2)
    mix(x, st, 0.25 * w)
s.save("cheer", x, 0.7)

d = 0.35  # a skate stride: the blade scraping the ice
scrape = s.highpass(s.noise(d), 3000) * env(n(d), 0.01, 0.2, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 40 * t(d)))
s.save("stride", lp(scrape, 9000), 0.35)

d = 0.6  # the starting pistol
bang = s.noise(d) * env(n(d), 0.0005, 0.15, 4)
s.save("pistol", lp(bang, 4000) + 0.4 * lp(s.noise(d), 300) * env(n(d), 0.001, 0.4, 2), 0.9)

d = 0.18  # countdown beeps
s.save("beep", np.sin(2 * np.pi * 880 * t(d)) * env(n(d), 0.003, 0.15, 1.2), 0.4)
s.save("beep_go", np.sin(2 * np.pi * 1760 * t(0.4)) * env(n(0.4), 0.003, 0.35, 1.2), 0.45)

d = 3.0  # wind on the in-run and in the air (loops)
w = lp(s.noise(d), 700 + 400 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t(d))))
fade = n(0.3)
w[:fade] = w[:fade] * np.linspace(0, 1, fade) + w[-fade:] * np.linspace(1, 0, fade)
s.save("wind", w[:-fade], 0.5)

d = 0.5  # skis leaving the lip: a whoosh
s.save("takeoff", lp(s.noise(d), np.geomspace(800, 4000, n(d))) * env(n(d), 0.05, 0.3, 2), 0.5)

d = 0.5  # landing: a soft thump in the snow
s.save("land", s.sweep(140, 60, d) * env(n(d), 0.002, 0.15, 3) + 0.5 * lp(s.noise(d), 1200) * env(n(d), 0.002, 0.2, 3), 0.7)

d = 1.0  # a fall: a tumble in the snow
x = np.zeros(n(d))
for k in range(5):
    b = s.sweep(160 - k * 15, 60, 0.18) * env(n(0.18), 0.002, 0.08, 3) + 0.4 * lp(s.noise(0.18), 900) * env(n(0.18), 0.002, 0.1)
    mix(x, n(k * 0.16), b * (1 - k * 0.15))
s.save("fall", x, 0.7)

d = 3.2  # the medal fanfare: brassy triads
x = np.zeros(n(d))
notes = [(0.0, 0.35, (587.3, 740.0, 880.0)), (0.4, 0.2, (587.3, 740.0, 880.0)), (0.65, 0.2, (659.3, 784.0, 987.8)),
         (0.9, 1.6, (740.0, 880.0, 1174.7))]
for st, ln, chord in notes:
    for f in chord:
        tt = t(ln + 0.5)
        brass = sum((1 / k) * np.sin(2 * np.pi * f * k * tt) for k in range(1, 7))
        brass *= env(len(tt), 0.03, ln * 0.8 + 0.3, 1.5)
        mix(x, n(st), 0.25 * lp(brass, 3500))
s.save("fanfare", x, 0.7)

# ---- the TV replay and the biathlon (added after the first set, so the sounds above keep their noise)

d = 0.6  # the replay wipe: a bright airy swish across the stereo-less screen
sw = lp(s.noise(d), np.geomspace(600, 6000, n(d))) * env(n(d), 0.12, 0.25, 3)
s.save("swoosh", sw + 0.25 * s.sweep(300, 1400, d) * env(n(d), 0.1, 0.2, 4), 0.5)

d = 0.9  # the small-bore rifle: a sharp crack, a short echo off the woods
crack = s.highpass(s.noise(d), 1500) * env(n(d), 0.0003, 0.03, 5)
body = lp(s.noise(d), 900) * env(n(d), 0.0005, 0.08, 4)
x = crack + 0.6 * body
echo = np.zeros(n(d))
mix(echo, n(0.19), 0.25 * lp(x[:n(0.4)], 2500))
mix(echo, n(0.33), 0.12 * lp(x[:n(0.4)], 1800))
s.save("rifle", x + echo, 0.8)

d = 0.35  # a hit: the steel flap snaps up over the target, far off
clank = s.bell(1850, d, ((1, 1.0), (2.3, 0.45), (3.9, 0.2)), 0.12) * env(n(d), 0.001, 0.2, 3)
s.save("target_hit", clank + 0.3 * s.highpass(s.noise(d), 3000) * env(n(d), 0.0005, 0.02, 5), 0.5)

d = 0.5  # a miss: a soft thud into the snow of the berm
s.save("target_miss", lp(s.noise(d), 500) * env(n(d), 0.002, 0.08, 4), 0.35)

d = 0.5  # the heart, lying at the range: lub-dub
beat = np.zeros(n(d))
for st, f, a in ((0.0, 55, 1.0), (0.14, 70, 0.6)):
    mix(beat, n(st), a * np.sin(2 * np.pi * f * s.t(0.12)) * env(n(0.12), 0.005, 0.05, 4))
s.save("heartbeat", lp(beat, 300), 0.6)

d = 0.4  # a skating push on skis: the edge biting and the ski hissing out, the poles' click
push = s.highpass(s.noise(d), 1800) * env(n(d), 0.02, 0.25, 2.5)
click = np.zeros(n(d))
mix(click, n(0.02), 0.5 * s.highpass(s.noise(0.03), 4000) * env(n(0.03), 0.0005, 0.01, 5))
s.save("ski_push", lp(push, 7000) + click, 0.35)
