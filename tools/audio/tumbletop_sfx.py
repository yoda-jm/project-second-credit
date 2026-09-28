#!/usr/bin/env python3
"""Sound effects for game 22 (Tumbletop), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. A fuzzy hopper paints the tops of a pyramid of
cubes floating over the clouds, played as a toybox: springs, marimba and glockenspiel bars, candy-glass chimes,
slide whistles and soft rubber thuds. The cube tops chime as they change colour: "paint" and "paint_done" are
short tonal notes on C (the game pitches them up a major scale as a streak builds), the finished colour rings
brighter with a fifth and a sparkle. The jingles are in F major like the music, on the same band: marimba,
glockenspiel, pizzicato, a soft square lead and a kick.
No voices anywhere (and no speech-like babble): the hero's death is a bonk, a wobbling spring and a few dizzy
chirps from a toy bird whistle.
Usage: python3 tools/audio/tumbletop_sfx.py [out_dir]   (default: godot/games/tumbletop/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/tumbletop/audio/sfx", seed=1982)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, *bs):
    """Adds sounds (of any lengths) into x from `start`."""
    for b in bs:
        b = b[:max(0, len(x) - start)]
        x[start:start + len(b)] += b


def save(name, x, gain):
    """Saves a one-shot with its tail trimmed where it falls below -50 dB of the peak."""
    w = n(0.01)
    rms = np.sqrt(np.convolve(np.asarray(x) ** 2, np.ones(w) / w, "same"))
    end = min(len(x), np.nonzero(rms > np.max(np.abs(x)) * 0.00316)[0][-1] + n(0.02))
    s.save(name, x[:end], gain)


def curve(points, sec):
    """A control curve through (time, value) points, linear between them, held at the ends."""
    ts, vs = zip(*points)
    return np.interp(t(sec), ts, vs)


def osc(f, sec, harm=((1, 1.0),)):
    """A tone with a (scalar or curve) frequency and the given harmonics."""
    fv = np.broadcast_to(np.asarray(f, dtype=float), (n(sec),))
    ph = 2 * np.pi * np.cumsum(fv) / SR
    return sum(a * np.sin(k * ph) for k, a in harm)


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude)."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 0.8))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        L = len(x) + len(ir)
        y += a * np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return y


def block(f, sec=0.1, dec=0.02):
    """A hollow toy block knocked: a soft click through two woody modes."""
    ex = np.r_[lp(s.noise(0.003), 3500) * env(n(0.003), 0.0003, 0.001, 3), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 2.7, dec * 0.4, 0.35)))


def marimba(f, sec=0.5, decay=0.18):
    """A marimba bar: a warm fundamental with its tuned fourth partial, a soft mallet thock."""
    x = s.bell(f, sec, partials=((1, 1.0), (3.93, 0.22), (9.2, 0.04)), decay=decay)
    return x + 0.25 * np.r_[lp(s.noise(0.006), 2500) * env(n(0.006), 0.0005, 0.002, 3), np.zeros(len(x) - n(0.006))]


def glock(f, sec=0.8, decay=0.35):
    """A glockenspiel bar: a bright fundamental with the high inharmonic partials of a struck bar."""
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def candy(f, sec=0.6, decay=0.3):
    """A candy-glass chime: a pure note, glassy partials and a quick shimmer."""
    tt = t(sec)
    x = s.bell(f, sec, partials=((1, 1.0), (2.32, 0.3), (4.25, 0.12)), decay=decay)
    return x * (1 + 0.12 * np.sin(2 * np.pi * 9 * tt))


def square(f, sec, attack=0.01, decay=0.3, bright=4000):
    """A soft square lead (odd harmonics, low-passed): the toybox synth voice."""
    x = osc(f, sec, [(k, 1 / k) for k in range(1, 14, 2)])
    return lp(x, bright) * env(n(sec), attack, decay, 1.5)


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong): pizzicato with a low damp."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1])
    return y * env(N, 0.001, sec, 0.5)


def spring(f0, f1, sec, wob=18.0, depth=0.25, harm=((1, 1.0), (2, 0.3), (3, 0.1))):
    """A spring 'boing': a tone gliding f0 -> f1 with a fast wobble that dies away."""
    tt = t(sec)
    fv = np.geomspace(f0, f1, n(sec)) * (1 + depth * np.sin(2 * np.pi * wob * tt) * np.exp(-tt * 9))
    return osc(fv, sec, harm)


def whistle(fcurve, sec, breath=0.12, vib=6.0):
    """A slide whistle: a near-sine tone on a pitch curve, a little vibrato and breath."""
    tt = t(sec)
    fv = fcurve * (1 + 0.008 * np.sin(2 * np.pi * vib * tt))
    return osc(fv, sec, ((1, 1.0), (2, 0.06), (3, 0.03))) + breath * lp(hp(s.noise(sec), 1500), 6000)


def whoosh(sec, f0, f1, q=1.0):
    """Air rushing: noise through a low-pass sweeping f0 -> f1."""
    return lp(hp(s.noise(sec), 150 * q), curve([(0, f0), (sec, f1)], sec))


# F major (MIDI), the jingles' key
F3, A3, C4, F4, G4, A4, Bb4, C5, D5, E5, F5, G5, A5, Bb5, C6, D6, E6, F6, G6, A6, C7, F7 = (
    m2f(m) for m in (53, 57, 60, 65, 67, 69, 70, 72, 74, 76, 77, 79, 81, 82, 84, 86, 88, 89, 91, 93, 96, 101))
F2, C3 = m2f(41), m2f(48)

# --- Pip ---
d = 0.2  # hop: a springy boing up and a puff of air as the feet leave the cube
x = np.zeros(n(d))
mix(x, 0, 0.45 * spring(380, 760, 0.16, 22, 0.12) * env(n(0.16), 0.003, 0.06, 2.5))
mix(x, 0, 0.2 * whoosh(0.12, 1500, 4500) * env(n(0.12), 0.01, 0.04, 3))
mix(x, 0, 0.3 * block(900, 0.05, 0.008))
save("hop", x, 0.32)

d = 0.2  # land: a soft padded tap on a hollow cube top
x = np.zeros(n(d))
mix(x, 0, 0.7 * thump(160, 70, 0.1, 0.025), 0.5 * block(420, 0.15, 0.03))
mix(x, n(0.004), 0.1 * lp(hp(s.noise(0.05), 1500), 5000) * env(n(0.05), 0.002, 0.015, 3))
save("land", lp(x, 5000), 0.3)

d = 0.4  # paint: the top changes colour: a short marimba and glockenspiel note on C6 (the game climbs a scale)
x = np.zeros(n(d))
mix(x, 0, 0.6 * marimba(C6, d, 0.2), 0.25 * glock(C7, d, 0.15))
save("paint", x, 0.38)

d = 0.8  # paint_done: the finished colour: the same note brighter, a glass fifth above and a sparkle
x = np.zeros(n(d))
mix(x, 0, 0.55 * marimba(C6, 0.6, 0.14), 0.35 * glock(C7, d, 0.22), 0.25 * candy(G6 * 2, 0.6, 0.18))
mix(x, n(0.03), 0.06 * hp(s.noise(0.3), 7000) * env(n(0.3), 0.004, 0.08, 3))
save("paint_done", x, 0.42)

d = 0.4  # undo: a colour knocked back: a flat, buzzy descending blat and a dull block
x = np.zeros(n(d))
fs = curve([(0, 330), (0.3, 180)], 0.3)
bz = osc(fs, 0.3, [(k, 1 / k) for k in range(1, 12)]) + osc(fs * 1.03, 0.3, [(k, 1 / k) for k in range(1, 12)])
mix(x, 0, 0.3 * lp(bz, 2200) * env(n(0.3), 0.01, 0.15, 1.5), 0.4 * block(300, 0.15, 0.03))
save("undo", x, 0.32)

d = 1.6  # fall: off the edge: a slide whistle falling away through the clouds, the wind, a faraway puff
x = np.zeros(n(d))
ln = 1.35
mix(x, 0, 0.4 * whistle(curve([(0, 1500), (0.08, 1600), (1.35, 260)], ln), ln, 0.05) *
    curve([(0, 0), (0.03, 1), (1.0, 0.7), (1.35, 0)], ln))
mix(x, 0, 0.25 * whoosh(1.4, 3000, 600) * curve([(0, 0), (0.3, 1), (1.4, 0)], 1.4))
mix(x, n(1.35), 0.2 * lp(s.noise(0.25), 500) * env(n(0.25), 0.02, 0.08, 3))
save("fall", x, 0.45)

# --- the disc ---
d = 0.9  # disc: stepping on a cloud-disc: a soft whoosh up and a harp-like sparkle up the F major chord
x = np.zeros(n(d))
mix(x, 0, 0.3 * whoosh(0.6, 600, 5000) * curve([(0, 0), (0.2, 1), (0.6, 0)], 0.6))
for i, f in enumerate((F5, A5, C6, F6, A6, C7)):
    mix(x, n(0.04 + i * 0.05), 0.22 * candy(f, 0.5, 0.2), 0.1 * pluck(f / 2, 0.4, 0.8, 0.995))
save("disc", x, 0.45)

d = 2.3  # ride: the flight back to the top: airy wind swelling, a shimmer tremolo rising, landing chime
x = np.zeros(n(d))
ln = 2.2
mix(x, 0, 0.3 * whoosh(ln, 800, 2500) * curve([(0, 0), (0.5, 1), (1.6, 0.8), (2.2, 0)], ln))
tr = osc(curve([(0, F5), (1.8, F6)], ln), ln, ((1, 1.0), (2, 0.2))) + osc(curve([(0, A5), (1.8, A6)], ln), ln)
mix(x, 0, 0.12 * tr * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * t(ln))) * curve([(0, 0), (0.4, 1), (1.9, 1), (2.2, 0)], ln))
mix(x, n(2.0), 0.2 * glock(F6, 0.3, 0.12))
save("ride", x, 0.4)

# --- enemies ---
d = 0.45  # drop: an enemy dropping in from the sky: a short falling whistle and a soft plop
x = np.zeros(n(d))
mix(x, 0, 0.3 * whistle(curve([(0, 2200), (0.3, 900)], 0.3), 0.3, 0.03) * curve([(0, 0), (0.02, 1), (0.3, 0)], 0.3))
mix(x, n(0.3), 0.5 * thump(200, 90, 0.12, 0.03))
save("drop", x, 0.3)

d = 0.2  # bounce: a rubber ball thudding on a step (the game pitches it per ball)
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(220, 90, 0.15, 0.035), 0.3 * spring(300, 250, 0.12, 30, 0.08) * env(n(0.12), 0.002, 0.03, 3))
mix(x, 0, 0.2 * block(700, 0.06, 0.01))
save("bounce", lp(x, 4000), 0.4)

d = 0.8  # hatch: the purple egg cracks: three shell snaps, a pop and a little scaly shimmer
x = np.zeros(n(d))
for k, st in enumerate((0.0, 0.12, 0.2)):
    mix(x, n(st), (0.4 + 0.2 * k) * hp(s.noise(0.02), 2000) * env(n(0.02), 0.0005, 0.004, 3),
        0.3 * block(1300 - 200 * k, 0.05, 0.008))
mix(x, n(0.3), 0.6 * thump(500, 120, 0.12, 0.03), 0.2 * lp(s.noise(0.08), 3000) * env(n(0.08), 0.002, 0.02, 3))
for i, f in enumerate((Bb5, G5, E5, D6)):
    mix(x, n(0.34 + i * 0.05), 0.08 * candy(f, 0.3, 0.1))
save("hatch", x, 0.4)

d = 0.8  # hiss: the serpent: a breathy hiss with a rattling flutter (no voice)
x = np.zeros(n(d))
h = lp(hp(s.noise(0.75), 3000), 9000) * curve([(0, 0), (0.05, 1), (0.5, 0.8), (0.75, 0)], 0.75)
rattle = 0.65 + 0.35 * np.sign(np.sin(2 * np.pi * 28 * t(0.75)))
mix(x, 0, 0.5 * h * rattle)
save("hiss", x, 0.28)

d = 1.7  # lure: the serpent follows Pip off the edge: a long, wobbling whistle falling low, the wind, a puff
x = np.zeros(n(d))
ln = 1.4
fs = curve([(0, 900), (1.4, 110)], ln) * (1 + 0.06 * np.sin(2 * np.pi * 7 * t(ln)))
mix(x, 0, 0.4 * whistle(fs, ln, 0.03) * curve([(0, 0), (0.05, 1), (1.1, 0.7), (1.4, 0)], ln))
mix(x, 0, 0.2 * whoosh(1.4, 2500, 400) * curve([(0, 0), (0.3, 1), (1.4, 0)], 1.4))
mix(x, n(1.4), 0.35 * lp(s.noise(0.3), 400) * env(n(0.3), 0.02, 0.1, 3), 0.3 * thump(120, 50, 0.3, 0.08))
save("lure", x, 0.5)

d = 1.5  # freeze: the green ball: everything stops: a glassy cluster sweeping down, then a held icy chord
x = np.zeros(n(d))
for i, f in enumerate((C7, A6, F6, E6, C6, A5)):
    mix(x, n(i * 0.035), 0.16 * candy(f, 0.8, 0.35))
chord = sum(osc(f, 1.2, ((1, 1.0), (2, 0.15))) for f in (F5, A5, C6, E6))
mix(x, n(0.22), 0.07 * chord * (0.75 + 0.25 * np.sin(2 * np.pi * 11 * t(1.2))) * curve([(0, 0), (0.1, 1), (1.2, 0)], 1.2))
mix(x, 0, 0.08 * hp(s.noise(0.5), 6000) * env(n(0.5), 0.005, 0.2, 3))
save("freeze", x, 0.42)

d = 0.6  # catch: an imp caught: a bright pop and a two-note ding up
x = np.zeros(n(d))
mix(x, 0, 0.5 * spring(600, 1400, 0.08, 40, 0.1) * env(n(0.08), 0.001, 0.03, 3))
mix(x, n(0.05), 0.35 * glock(C6, 0.3, 0.12), 0.3 * marimba(C6, 0.3, 0.1))
mix(x, n(0.14), 0.4 * glock(G6, 0.45, 0.2), 0.3 * marimba(G5, 0.4, 0.12))
save("catch", x, 0.42)

d = 1.8  # die: caught: a bonk, a wobbling spring sagging down, and dizzy toy-bird chirps circling
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(420, 110, 0.12, 0.03), 0.5 * block(560, 0.2, 0.04))
ln = 0.9
mix(x, n(0.08), 0.35 * spring(620, 180, ln, 9, 0.12, ((1, 1.0), (2, 0.35), (3, 0.15))) *
    curve([(0, 0), (0.02, 1), (0.7, 0.6), (0.9, 0)], ln))
for k in range(5):  # a toy bird whistle: quick up-chirps, fading as they circle away
    st = 0.75 + k * 0.17
    f = 2600 + 300 * (k % 2)
    mix(x, n(st), (0.18 * 0.82 ** k) * whistle(curve([(0, f), (0.06, f * 1.3)], 0.07), 0.07, 0.0) * env(n(0.07), 0.003, 0.03, 2))
save("die", x, 0.5)

# --- jingles ---
d = 2.0  # round_start: a bouncy call: marimba up the F chord over pizzicato and kick, glockenspiel tag
x = np.zeros(n(d))
beat = 0.2
for k, f in enumerate((C5, F5, A5, C6, A5, C6)):
    mix(x, n(k * beat), 0.35 * marimba(f, 0.4, 0.12))
for k in range(3):
    mix(x, n(k * beat * 2), 0.5 * thump(110, 45, 0.15, 0.05), 0.2 * pluck(F2 * 2 if k % 2 == 0 else C3, 0.3, 0.5, 0.99))
mix(x, n(6 * beat), 0.4 * marimba(F6, 0.8, 0.3), 0.3 * glock(F6, 1.0, 0.4), 0.5 * thump(110, 45, 0.2, 0.06))
for f in (F4, A4, C5):
    mix(x, n(6 * beat), 0.08 * square(f, 0.6, 0.01, 0.4, 3000))
save("round_start", x, 0.55)

d = 2.8  # round_clear: the pyramid done: glock and marimba run, a pizzicato cadence (Bb, C, F), a big chord
x = np.zeros(n(d))
for i, f in enumerate((F5, A5, C6, F6, A6, C7)):
    mix(x, n(i * 0.05), 0.2 * glock(f, 0.4, 0.12), 0.2 * marimba(f / 2, 0.3, 0.08))
for st, root, ch in ((0.4, m2f(46), (Bb4, D5, F5)), (0.7, C3, (Bb4, C5, E5)), (1.0, C3, (C5, E5, G5))):
    mix(x, n(st), 0.4 * pluck(root, 0.3, 0.5, 0.99), 0.4 * thump(110, 45, 0.15, 0.05))
    for p in ch:
        mix(x, n(st + 0.15), 0.07 * square(p, 0.14, 0.005, 0.1, 3500), 0.12 * marimba(p, 0.2, 0.08))
mix(x, n(1.35), 0.6 * pluck(F2, 1.2, 0.5, 0.997), 0.5 * thump(110, 40, 0.3, 0.08))
for f in (F4, A4, C5, F5):
    mix(x, n(1.35), 0.08 * square(f, 1.2, 0.01, 0.8, 3000), 0.12 * marimba(f, 0.8, 0.3))
for i, f in enumerate((C7, F7)):
    mix(x, n(1.35 + i * 0.08), 0.22 * glock(f, 1.2, 0.5))
mix(x, n(1.4), 0.07 * hp(s.noise(0.9), 7000) * curve([(0, 0), (0.1, 1), (0.9, 0)], 0.9))
save("round_clear", x, 0.6)

d = 3.0  # game_over: the tune sags: marimba stepping down (C, A, F, E) over pizzicato, a slow low F, a last plink
x = np.zeros(n(d))
for st, f in ((0.0, C5), (0.35, A4), (0.7, F4), (1.05, E5 / 2)):
    mix(x, n(st), 0.4 * marimba(f, 0.5, 0.18), 0.1 * square(f, 0.3, 0.01, 0.2, 2000), 0.25 * pluck(f / 2, 0.4, 0.4, 0.99))
mix(x, n(1.5), 0.45 * pluck(F2, 1.3, 0.4, 0.997), 0.3 * marimba(F3, 1.2, 0.5))
for f in (F3, A3, C4):
    mix(x, n(1.5), 0.07 * square(f * curve([(0, 1), (1.2, 0.97)], 1.2), 1.2, 0.03, 0.9, 1800))
mix(x, n(2.45), 0.15 * glock(F5, 0.5, 0.2))
save("game_over", lp(x, 7000), 0.55)

d = 1.3  # extra_life: a cheery glockenspiel and marimba run up F major with a spring and a sparkle
x = np.zeros(n(d))
for i, f in enumerate((F5, A5, C6, F6, A6, C7)):
    mix(x, n(i * 0.06), 0.22 * glock(f, 0.4, 0.12), 0.2 * marimba(f / 2, 0.3, 0.1))
mix(x, n(0.36), 0.25 * spring(500, 1000, 0.2, 20, 0.1) * env(n(0.2), 0.003, 0.08, 2.5))
mix(x, n(0.4), 0.25 * candy(F7, 0.8, 0.35))
save("extra_life", x, 0.5)
