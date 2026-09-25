#!/usr/bin/env python3
"""Sound effects for game 4 (Whisker Alley), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/whisker_sfx.py [out_dir]   (default: godot/games/whisker/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/whisker/audio/sfx", seed=1984)
t, env, lp = s.t, s.env, s.lowpass


def n(sec):
    return int(SR * sec)


def mix(x, start, b):
    """Adds b into x at sample `start`, clipped to x."""
    b = b[:max(0, len(x) - start)]
    x[start:start + len(b)] += b


def formant_voice(f0, formants, sec, vib=0.0):
    """A buzzy source through resonant bands: meows and barks."""
    tt = t(sec)
    f = f0(tt) if callable(f0) else np.full(len(tt), f0)
    f = f * (1 + vib * np.sin(2 * np.pi * 6 * tt))
    ph = np.cumsum(f) / SR
    src = 2 * (ph % 1.0) - 1.0  # saw
    out = np.zeros(len(tt))
    for fc, bw, gain in formants(tt):
        # a crude band pass: difference of two low passes
        out += gain * (lp(src, fc + bw) - lp(src, max(fc - bw, 50)))
    return out


def meow(sec, lo, hi, name, gain=0.6):
    tt = t(sec)
    shape = np.sin(np.pi * np.clip(tt / sec, 0, 1)) ** 0.7
    f0 = lambda x: lo + (hi - lo) * np.sin(np.pi * np.clip(x / sec, 0, 1)) ** 1.5
    # the vowel slides "ee" -> "ow"
    form = lambda x: [(float(np.interp(sec * 0.3, [0, sec], [2300, 900])), 300, 1.0), (700.0, 200, 0.8)]
    v = formant_voice(f0, form, sec, 0.01)
    s.save(name, v * shape, gain)


meow(0.55, 480, 720, "meow")
meow(1.0, 520, 260, "sad_meow", 0.55)

d = 0.25  # jump: a soft upward whoosh
s.save("jump", lp(s.noise(d), np.geomspace(600, 2500, n(d))) * env(n(d), 0.02, 0.1, 2), 0.3)

d = 0.5  # a trash-can lid: a metal clang and a springy boing
clang = s.bell(420, d, partials=((1, 1.0), (2.3, 0.6), (3.9, 0.4), (5.7, 0.25)), decay=0.25)
boing = np.sin(2 * np.pi * np.cumsum(220 + 160 * np.exp(-t(d) * 6) * np.sin(2 * np.pi * 11 * t(d))) / SR) * env(n(d), 0.003, 0.3, 2)
s.save("bounce", clang * 0.8 + boing * 0.5, 0.55)

d = 0.15  # landing on soft paws
s.save("land", lp(s.noise(d), 700) * env(n(d), 0.002, 0.05, 3), 0.35)

d = 0.35  # the bulldog's bark: a rough, low "wuf"
tt = t(d)
bark = formant_voice(lambda x: 160 - 60 * x / d, lambda x: [(600.0, 250, 1.0), (1300.0, 300, 0.5)], d)
bark += 0.4 * lp(s.noise(d), 1500) * env(n(d), 0.005, 0.08, 3)
s.save("bark", bark * env(n(d), 0.01, 0.2, 2.5), 0.7)

d = 0.8  # a window's shutters creaking open
f = 180 + 60 * np.sin(2 * np.pi * 2.5 * t(d)) + 30 * s.rng.standard_normal(n(d)).cumsum() / np.sqrt(n(d))
cr = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t(d)))
s.save("creak", lp(cr, 1400) * env(n(d), 0.05, 0.6, 1.5), 0.25)

d = 0.4  # a boot flying past
s.save("whoosh", lp(s.noise(d), np.geomspace(3000, 500, n(d))) * np.sin(np.pi * np.clip(t(d) / d, 0, 1)), 0.35)

d = 0.3  # the boot hits: a thud and a cartoon "bonk"
bonk = s.sweep(900, 300, d) * env(n(d), 0.001, 0.08, 3)
s.save("bonk", bonk + 0.6 * s.sweep(120, 60, d) * env(n(d), 0.002, 0.1, 3), 0.6)

d = 0.7  # splash into the bowl
x = lp(s.noise(d), np.geomspace(6000, 500, n(d))) * env(n(d), 0.004, 0.35, 3)
for k in range(6):  # bubbles
    st = n(0.1 + k * 0.08)
    b = np.sin(2 * np.pi * np.cumsum(np.geomspace(600 + 90 * k, 1400 + 90 * k, n(0.06))) / SR) * env(n(0.06), 0.003, 0.03)
    mix(x, st, 0.35 * b)
s.save("splash", x, 0.6)

d = 0.35  # catching something: a pop and a sparkle
pop = s.sweep(1200, 300, 0.08) * env(n(0.08), 0.001, 0.03)
x = np.zeros(n(d))
x[:len(pop)] += pop
x += 0.5 * s.bell(1760, d, decay=0.2)
s.save("catch", x, 0.55)

d = 0.18  # a mouse squeak
s.save("squeak", np.sin(2 * np.pi * np.cumsum(3200 + 900 * np.sin(2 * np.pi * 14 * t(d))) / SR) * env(n(d), 0.005, 0.1, 2), 0.3)

d = 0.9  # the cage crashes to the floor
x = 0.8 * s.bell(640, d, partials=((1, 1.0), (2.7, 0.7), (4.1, 0.5), (6.3, 0.3)), decay=0.3)
x += 0.6 * lp(s.noise(d), 3000) * env(n(d), 0.001, 0.2, 3)
s.save("cage_crash", x, 0.6)

d = 0.35  # a canary's chirp
x = np.zeros(n(d))
for k in range(3):
    st = n(k * 0.1)
    c = np.sin(2 * np.pi * np.cumsum(np.geomspace(3000, 4600, n(0.07))) / SR) * env(n(0.07), 0.004, 0.04)
    mix(x, st, c)
s.save("chirp", x, 0.3)

d = 0.5  # the broom's swish
s.save("swish", lp(s.noise(d), 2500) * np.sin(np.pi * np.clip(t(d) / d, 0, 1)) ** 2, 0.4)

d = 0.5  # the eel's zap
zap = np.sign(np.sin(2 * np.pi * 60 * t(d))) * s.noise(d) * env(n(d), 0.001, 0.3, 2)
s.save("zap", s.highpass(zap, 800), 0.5)

d = 1.4  # a room won: a jazzy arpeggio
x = np.zeros(n(d))
for i, f in enumerate((392.0, 493.9, 587.3, 740.0, 880.0)):
    b = s.bell(f, d - i * 0.08, partials=((1, 1.0), (2, 0.35), (3, 0.1)), decay=0.5)
    mix(x, n(i * 0.08), b)
s.save("room_won", x, 0.6)

d = 2.0  # game over
x = np.zeros(n(d))
for i, f in enumerate((440.0, 415.3, 392.0, 329.6)):
    b = s.bell(f, d - i * 0.35, partials=((1, 1.0), (2, 0.25)), decay=0.8)
    mix(x, n(i * 0.35), b)
s.save("game_over", x, 0.55)
