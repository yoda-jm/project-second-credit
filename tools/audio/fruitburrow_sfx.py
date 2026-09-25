#!/usr/bin/env python3
"""Sound effects for game 3 (Fruitburrow), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/fruitburrow_sfx.py [out_dir]   (default: godot/games/fruitburrow/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/fruitburrow/audio/sfx", seed=1984)
t, env, lp = s.t, s.env, s.lowpass


def n(sec):
    return int(SR * sec)


d = 0.22  # digging: a soft crunch of soil
x = lp(s.noise(d), 1800) * env(n(d), 0.004, 0.08, 3)
for k in range(5):
    st = n(0.01 + k * 0.035)
    g = s.highpass(s.noise(0.02), 1500) * env(n(0.02), 0.0005, 0.01)
    x[st:st + len(g)] += 0.5 * g
s.save("dig", x, 0.5)

d = 0.5  # fruit: a bright two-note pluck
x = np.zeros(n(d))
for i, f in enumerate((1046.5, 1568.0)):
    b = s.bell(f, d - i * 0.06, partials=((1, 1.0), (2, 0.3), (3, 0.12)), decay=0.35)
    x[n(i * 0.06):n(i * 0.06) + len(b)] += b
s.save("fruit", x, 0.55)

d = 0.7  # apple wobble: a wooden rattle
x = np.zeros(n(d))
for k in range(10):
    st = n(k * 0.065)
    tk = np.sin(2 * np.pi * (520 + 40 * (k % 2)) * t(0.04)) * env(n(0.04), 0.001, 0.015)
    x[st:st + len(tk)] += tk * (0.6 + 0.4 * (k / 10))
s.save("apple_wobble", x, 0.45)

d = 0.55  # apple falling: a short descending whistle
s.save("apple_fall", s.sweep(1500, 500, d) * env(n(d), 0.02, 0.4, 1.5), 0.3)

d = 0.4  # apple lands: a soft thud
s.save("apple_land", s.sweep(160, 60, d) * env(n(d), 0.002, 0.12, 3) + 0.4 * lp(s.noise(d), 500) * env(n(d), 0.001, 0.06), 0.7)

d = 0.6  # apple breaks: a juicy squish
sq = lp(s.noise(d), np.geomspace(3500, 300, n(d))) * env(n(d), 0.003, 0.25, 3)
s.save("apple_break", sq + 0.6 * s.sweep(220, 70, d) * env(n(d), 0.002, 0.1, 3), 0.75)

d = 0.7  # a monster squashed: splat and a cartoon boing
boing = np.sin(2 * np.pi * np.cumsum(300 + 120 * np.sin(2 * np.pi * 9 * t(d)) * np.exp(-t(d) * 4)) / SR) * env(n(d), 0.003, 0.35, 2)
splat = lp(s.noise(d), np.geomspace(3500, 300, n(d))) * env(n(d), 0.003, 0.2, 3)
s.save("squash", 0.8 * splat + boing, 0.75)

d = 0.3  # throwing the ball: a rising zip
s.save("throw", s.sweep(300, 1800, d) * env(n(d), 0.005, 0.15, 2) + 0.2 * s.highpass(s.noise(d), 3000) * env(n(d), 0.002, 0.05), 0.4)

d = 0.08  # the ball bouncing off a wall: a small tick
s.save("bounce", np.sin(2 * np.pi * 1400 * t(d)) * env(n(d), 0.0005, 0.02), 0.3)

d = 0.6  # the ball knocks out a monster: a pop and a chime
pop = s.sweep(900, 200, 0.12) * env(n(0.12), 0.001, 0.04)
x = np.zeros(n(d))
x[:len(pop)] += pop
x += 0.6 * s.bell(1318.5, d, decay=0.3)
s.save("monster_hit", x, 0.6)

d = 0.45  # a monster comes out of the nest: a bubbly blurp
f = 180 + 80 * np.sin(2 * np.pi * 14 * t(d))
s.save("monster_spawn", np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n(d), 0.02, 0.25, 2), 0.4)

d = 0.8  # a monster starts digging: a low growl
g = lp(s.noise(d), 400) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t(d)))
s.save("transform", g * env(n(d), 0.05, 0.5, 2) + 0.5 * s.sweep(110, 70, d) * env(n(d), 0.05, 0.5, 2), 0.6)

d = 0.4  # the ball is back: a twinkle
x = np.zeros(n(d))
for i, f in enumerate((1568.0, 2093.0, 2637.0)):
    b = s.bell(f, d - i * 0.05, decay=0.2)
    x[n(i * 0.05):n(i * 0.05) + len(b)] += b * 0.6
s.save("ball_back", x, 0.35)

d = 1.4  # the gardener is caught: a descending wah-wah
f = np.concatenate([np.full(n(0.3), 392.0), np.full(n(0.3), 370.0), np.full(n(0.3), 349.2), np.geomspace(330, 200, n(0.5))])
sq_wave = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
tt = np.arange(len(f)) / SR
wah = lp(sq_wave, 600 + 500 * (0.5 + 0.5 * np.sin(2 * np.pi * 3.3 * tt)))
s.save("death", wah * env(len(f), 0.01, 1.2, 1.2), 0.5)

d = 1.6  # garden cleared: a happy arpeggio
x = np.zeros(n(d))
for i, f in enumerate((523.3, 659.3, 784.0, 1046.5, 1318.5)):
    b = s.bell(f, d - i * 0.09, partials=((1, 1.0), (2, 0.4), (4, 0.1)), decay=0.6)
    x[n(i * 0.09):n(i * 0.09) + len(b)] += b
s.save("clear", x, 0.6)

d = 2.2  # game over: a slow, sad three-note fall
x = np.zeros(n(d))
for i, f in enumerate((392.0, 329.6, 261.6)):
    b = s.bell(f, d - i * 0.45, partials=((1, 1.0), (2, 0.25)), decay=0.9)
    x[n(i * 0.45):n(i * 0.45) + len(b)] += b
s.save("game_over", x, 0.55)
