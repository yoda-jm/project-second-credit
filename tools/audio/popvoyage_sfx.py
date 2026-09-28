#!/usr/bin/env python3
"""Sound effects for game 23 (Pop Voyage), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. A young traveller pops bouncing balloons with a
harpoon launcher across postcard landmarks, played as a bright travel band: rubber, air, brass-ish squares, marimba,
glockenspiel and plucked strings.
The balloons: pop_0 .. pop_3 get bigger and deeper (a sharp snap of stretched rubber, a burst of air, a low thump
of the air leaving and the slap of the rubber flapping), "split" is a layer played with the pop of a balloon that
splits (two rubbery squeaks flying apart), the bounces are soft rubber boings. The jingles are in D major like the
music, on the same band.
No voices anywhere (and no speech-like babble): the hero's death is a bonk, a squealing deflating balloon and a
flop.
Usage: python3 tools/audio/popvoyage_sfx.py [out_dir]   (default: godot/games/popvoyage/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/popvoyage/audio/sfx", seed=1989)
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


def click(sec=0.003, bright=3500):
    return lp(s.noise(sec), bright) * env(n(sec), 0.0003, sec / 3, 3)


def knock(f, sec=0.1, dec=0.02, ratio=2.7):
    """A struck hollow body: a click through two modes (wood, stone or metal by the ratio and decay)."""
    ex = np.r_[click(), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * ratio, dec * 0.4, 0.35)))


def marimba(f, sec=0.5, decay=0.18):
    x = s.bell(f, sec, partials=((1, 1.0), (3.93, 0.22), (9.2, 0.04)), decay=decay)
    return x + 0.25 * np.r_[click(0.006, 2500), np.zeros(len(x) - n(0.006))]


def glock(f, sec=0.8, decay=0.35):
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def chime(f, sec=0.6, decay=0.3):
    """A glassy chime with a quick shimmer."""
    x = s.bell(f, sec, partials=((1, 1.0), (2.32, 0.3), (4.25, 0.12)), decay=decay)
    return x * (1 + 0.12 * np.sin(2 * np.pi * 9 * t(sec)))


def brass(f, sec, attack=0.02, decay=0.4, bright=3000, vib=5.5):
    """A soft brass-like voice: a sawtooth with a filter that opens on the attack, a little vibrato."""
    tt = t(sec)
    fv = f * (1 + 0.004 * np.sin(2 * np.pi * vib * tt) * np.clip(tt / 0.15, 0, 1))
    x = osc(fv, sec, [(k, 1 / k) for k in range(1, 16)])
    cut = bright * (0.35 + 0.65 * np.clip(tt / max(attack * 3, 1e-3), 0, 1))
    return lp(x, cut) * env(n(sec), attack, decay, 1.5)


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong)."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1])
    return y * env(N, 0.001, sec, 0.5)


def boing(f0, f1, sec, wob=18.0, depth=0.25, harm=((1, 1.0), (2, 0.3), (3, 0.1))):
    """A rubbery 'boing': a tone gliding f0 -> f1 with a fast wobble that dies away."""
    tt = t(sec)
    fv = np.geomspace(f0, f1, n(sec)) * (1 + depth * np.sin(2 * np.pi * wob * tt) * np.exp(-tt * 9))
    return osc(fv, sec, harm)


def squeak(f0, f1, sec):
    """Rubber rubbed: a buzzy, nasal glide (a pulse wave through a band)."""
    fv = np.geomspace(f0, f1, n(sec))
    x = osc(fv, sec, [(k, 1 / k ** 0.8) for k in range(1, 10)])
    return hp(lp(x, 4500), 500) * env(n(sec), 0.004, sec * 0.5, 2)


def whoosh(sec, f0, f1, q=1.0):
    """Air rushing: noise through a low-pass sweeping f0 -> f1."""
    return lp(hp(s.noise(sec), 150 * q), curve([(0, f0), (sec, f1)], sec))


def balloon_pop(size):
    """size 0..3: a snap of rubber (brighter and shorter when small), a burst of air, the low thump of the air
    leaving and the rubber flapping (a few decaying wobbles), deeper and longer for bigger balloons."""
    k = size / 3.0
    d = 0.25 + 0.35 * k
    x = np.zeros(n(d))
    snap = hp(s.noise(0.012), 2500 - 1200 * k) * env(n(0.012), 0.0002, 0.0025 + 0.002 * k, 3)
    mix(x, 0, (1.0 - 0.45 * k) * snap)
    air = lp(hp(s.noise(0.2), 300), 7000 - 3500 * k) * env(n(0.2), 0.0005, 0.02 + 0.03 * k, 3)
    mix(x, 0, (0.5 - 0.2 * k) * air)
    f0 = 330 - 230 * k ** 0.8
    mix(x, 0, (0.55 + 0.35 * k) * thump(f0 * 1.8, f0 * 0.5, 0.25 + 0.3 * k, 0.035 + 0.09 * k))
    fl = 38 - 12 * k        # the rubber shreds flapping
    ln = 0.1 + 0.14 * k
    tt = t(ln)
    flap = lp(s.noise(ln), 1200 - 400 * k) * np.maximum(0, np.sin(2 * np.pi * fl * tt)) ** 3 * np.exp(-tt / (0.035 + 0.07 * k))
    mix(x, n(0.006), (0.45 + 0.3 * k) * flap)
    mix(x, 0, 0.18 * knock(900 - 450 * k, 0.12, 0.012 + 0.01 * k, 1.9))
    return x


# D major (MIDI), the jingles' key
D4, Fs4, A4, B4, D5, E5, Fs5, G5, A5, B5, Cs6, D6, E6, Fs6, A6, B6, D7 = (
    m2f(m) for m in (62, 66, 69, 71, 74, 76, 78, 79, 81, 83, 85, 86, 88, 90, 93, 95, 98))
D2, A2, D3, Fs3, A3, G3, E3, Cs5 = m2f(38), m2f(45), m2f(50), m2f(54), m2f(57), m2f(55), m2f(52), m2f(73)

# --- the harpoon ---
d = 0.35  # fire: a pneumatic thwip from the launcher and the wire zinging upward
x = np.zeros(n(d))
mix(x, 0, 0.6 * lp(hp(s.noise(0.06), 800), 5000) * env(n(0.06), 0.001, 0.012, 3), 0.5 * thump(260, 90, 0.08, 0.02))
zing = osc(curve([(0, 700), (0.3, 2400)], 0.3), 0.3, ((1, 1.0), (2.01, 0.4), (3.02, 0.2)))
mix(x, n(0.01), 0.22 * zing * curve([(0, 0), (0.01, 1), (0.12, 0.5), (0.3, 0)], 0.3))
mix(x, n(0.01), 0.12 * whoosh(0.25, 1500, 6000) * curve([(0, 0), (0.03, 1), (0.25, 0)], 0.25))
save("fire", x, 0.4)

d = 0.5  # wire_stick: the sticky wire bites the ceiling: a metal tunk and the line twanging
x = np.zeros(n(d))
mix(x, 0, 0.7 * knock(620, 0.3, 0.05, 2.41), 0.3 * knock(1700, 0.2, 0.03, 1.53))
tw = osc(310 * (1 + 0.03 * np.sin(2 * np.pi * 11 * t(0.45))), 0.45, ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15)))
mix(x, n(0.005), 0.3 * lp(tw, 3000) * env(n(0.45), 0.002, 0.12, 2))
save("wire_stick", x, 0.36)

# --- the balloons ---
for size, gain in ((0, 0.4), (1, 0.45), (2, 0.5), (3, 0.56)):
    save("pop_%d" % size, balloon_pop(size), gain)

d = 0.3  # split: layered with the pop: two rubbery squeaks flying apart (one up, one down) and a whoosh
x = np.zeros(n(d))
mix(x, n(0.01), 0.35 * squeak(520, 900, 0.16), 0.3 * squeak(480, 330, 0.18))
mix(x, 0, 0.18 * whoosh(0.22, 3000, 900) * env(n(0.22), 0.01, 0.07, 3))
save("split", x, 0.3)

d = 0.2  # bounce_small: a light rubber boing on the floor
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(260, 120, 0.1, 0.02), 0.35 * boing(360, 440, 0.15, 26, 0.12) * env(n(0.15), 0.002, 0.04, 3))
save("bounce_small", lp(x, 4500), 0.28)

d = 0.4  # bounce_big: a fat, soft rubber whump with a low wobble
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(150, 55, 0.3, 0.05),
    0.4 * boing(140, 180, 0.35, 12, 0.2, ((1, 1.0), (2, 0.4), (3, 0.15))) * env(n(0.35), 0.003, 0.09, 3))
mix(x, 0, 0.1 * lp(s.noise(0.05), 1200) * env(n(0.05), 0.001, 0.01, 3))
save("bounce_big", lp(x, 2500), 0.36)

# --- blocks and items ---
d = 0.7  # block_break: a cracked stone block shatters: a crack, a crunch, rubble tumbling, a gilded ting
x = np.zeros(n(d))
mix(x, 0, 0.8 * hp(s.noise(0.02), 1500) * env(n(0.02), 0.0003, 0.005, 3), 0.7 * thump(200, 60, 0.2, 0.05))
mix(x, n(0.005), 0.4 * lp(s.noise(0.2), 2500) * env(n(0.2), 0.002, 0.05, 3))
for k in range(9):
    st = 0.06 + k * 0.05 + s.rng.uniform(-0.02, 0.02)
    mix(x, n(st), (0.35 * 0.85 ** k) * knock(s.rng.uniform(500, 1400), 0.08, 0.008, 2.3))
mix(x, n(0.02), 0.12 * glock(2 * A5, 0.5, 0.2))
save("block_break", x, 0.5)

d = 0.6  # item_drop: a prize tumbles out: a falling whistle and a sparkle
x = np.zeros(n(d))
mix(x, 0, 0.25 * osc(curve([(0, 2000), (0.35, 900)], 0.35), 0.35, ((1, 1.0), (2, 0.08))) *
    curve([(0, 0), (0.02, 1), (0.35, 0)], 0.35))
for i, f in enumerate((A6, Fs6, D6)):
    mix(x, n(0.03 + i * 0.05), 0.15 * chime(f, 0.3, 0.1))
save("item_drop", x, 0.32)

d = 0.6  # item_take: picked up: a quick marimba-glock rise to a bright ding
x = np.zeros(n(d))
for i, f in enumerate((D6, Fs6, A6)):
    mix(x, n(i * 0.045), 0.3 * marimba(f / 2, 0.25, 0.08), 0.2 * glock(f, 0.25, 0.08))
mix(x, n(0.14), 0.4 * glock(D7, 0.45, 0.2), 0.2 * chime(A6, 0.45, 0.18))
save("item_take", x, 0.42)

d = 1.0  # shield_on: a bubble wraps round the hero: a rising bubbly warble and a soft glassy chord
x = np.zeros(n(d))
ln = 0.5
wv = osc(curve([(0, 300), (0.5, 1300)], ln) * (1 + 0.15 * np.sin(2 * np.pi * 24 * t(ln))), ln, ((1, 1.0), (2, 0.1)))
mix(x, 0, 0.3 * wv * curve([(0, 0), (0.05, 1), (0.5, 0)], ln))
for i, f in enumerate((D6, Fs6, A6, D7)):
    mix(x, n(0.25 + i * 0.03), 0.12 * chime(f, 0.7, 0.3))
save("shield_on", x, 0.32)

d = 0.8  # shield_lost: the bubble bursts: a wet pop, glassy shards falling and a sagging tone
x = np.zeros(n(d))
mix(x, 0, 0.6 * hp(s.noise(0.01), 3000) * env(n(0.01), 0.0002, 0.003, 3), 0.5 * thump(900, 200, 0.1, 0.02))
for i, f in enumerate((D7, A6, Fs6, D6, A5)):
    mix(x, n(0.02 + i * 0.05), 0.14 * chime(f * (1 - 0.01 * i), 0.3, 0.1))
mix(x, n(0.05), 0.2 * osc(curve([(0, 800), (0.5, 300)], 0.5), 0.5, ((1, 1.0), (2, 0.2))) * env(n(0.5), 0.01, 0.2, 2))
save("shield_lost", x, 0.42)

d = 1.4  # freeze: the pocket watch: tick, tock, a click of the crown, then a held icy shimmer (the balloons stop)
x = np.zeros(n(d))
mix(x, 0, 0.5 * knock(2600, 0.08, 0.006, 1.6))
mix(x, n(0.16), 0.5 * knock(2000, 0.08, 0.006, 1.6))
mix(x, n(0.3), 0.6 * knock(3200, 0.06, 0.004, 1.4), 0.25 * glock(A6, 0.6, 0.3))
for i, f in enumerate((D7, A6, Fs6, D6)):
    mix(x, n(0.32 + i * 0.03), 0.12 * chime(f, 0.8, 0.35))
ch = sum(osc(f, 1.0, ((1, 1.0), (2, 0.1))) for f in (D5, Fs5, A5, Cs6))
mix(x, n(0.36), 0.09 * ch * (0.75 + 0.25 * np.sin(2 * np.pi * 10 * t(1.0))) * curve([(0, 0), (0.1, 1), (1.0, 0)], 1.0))
mix(x, n(0.3), 0.06 * hp(s.noise(0.6), 6000) * env(n(0.6), 0.005, 0.25, 3))
save("freeze", x, 0.42)

d = 1.6  # charge: a firework: a fizzing fuse, a whoosh up, a bang and crackling sparks (every balloon bursts)
x = np.zeros(n(d))
fz = hp(s.noise(0.35), 3000) * (0.6 + 0.4 * s.rng.uniform(0, 1, n(0.35)) ** 4)
mix(x, 0, 0.25 * fz * curve([(0, 0), (0.03, 1), (0.35, 0.7)], 0.35))
mix(x, n(0.3), 0.3 * whoosh(0.3, 800, 6000) * curve([(0, 0), (0.25, 1), (0.3, 0)], 0.3),
    0.15 * osc(curve([(0, 600), (0.3, 1800)], 0.3), 0.3) * curve([(0, 0), (0.25, 1), (0.3, 0)], 0.3))
mix(x, n(0.6), 0.9 * thump(140, 40, 0.5, 0.12), 0.6 * lp(s.noise(0.4), 3000) * env(n(0.4), 0.001, 0.07, 3))
for k in range(26):
    st = 0.68 + s.rng.uniform(0, 0.8)
    mix(x, n(st), s.rng.uniform(0.08, 0.2) * hp(s.noise(0.006), 2500) * env(n(0.006), 0.0002, 0.0015, 3))
for i, f in enumerate((D6, A6, Fs6, D7)):
    mix(x, n(0.65 + i * 0.04), 0.08 * chime(f, 0.6, 0.25))
save("charge", x, 0.55)

# --- the hero ---
d = 1.7  # die: a bonk, a balloon squealing as it deflates, and the flop onto the ground
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(420, 110, 0.12, 0.03), 0.5 * knock(560, 0.2, 0.04))
ln = 1.0
fv = curve([(0, 900), (0.2, 1000), (1.0, 250)], ln) * (1 + 0.05 * np.sin(2 * np.pi * 17 * t(ln)))
sq = hp(lp(osc(fv, ln, [(k, 1 / k ** 0.9) for k in range(1, 9)]), 3500), 300)
mix(x, n(0.12), 0.25 * sq * curve([(0, 0), (0.03, 1), (0.8, 0.6), (1.0, 0)], ln))
mix(x, n(0.12), 0.1 * whoosh(1.0, 3000, 800) * curve([(0, 0), (0.1, 1), (1.0, 0)], 1.0))
mix(x, n(1.2), 0.7 * thump(160, 60, 0.25, 0.05), 0.2 * lp(s.noise(0.15), 800) * env(n(0.15), 0.002, 0.04, 3))
mix(x, n(1.38), 0.35 * thump(140, 60, 0.15, 0.03))
save("die", x, 0.5)

# --- clock and jingles ---
d = 0.45  # timeout_warn: the clock nags: two quick high beeps (the game repeats it each second)
x = np.zeros(n(d))
for st in (0.0, 0.14):
    b = lp(osc(A5 * 2, 0.1, ((1, 1.0), (3, 0.3), (5, 0.1))), 6000) * env(n(0.1), 0.002, 0.05, 2)
    mix(x, n(st), 0.35 * b, 0.2 * knock(3000, 0.05, 0.004, 1.5))
save("timeout_warn", x, 0.36)

d = 0.1  # bonus_tick: one count of the time bonus: a tiny bright tick
x = np.zeros(n(d))
mix(x, 0, 0.4 * glock(A6 * 2, 0.08, 0.03), 0.3 * knock(4000, 0.05, 0.003, 1.5))
save("bonus_tick", x, 0.28)

d = 2.2  # stage_start: a travel fanfare: brass up the D chord over pizzicato and kick, a glock tag
x = np.zeros(n(d))
beat = 0.18
for k, f in enumerate((A4, D5, Fs5, A5, Fs5, A5)):
    mix(x, n(k * beat), 0.22 * brass(f, 0.3, 0.01, 0.15, 3500), 0.25 * marimba(f, 0.3, 0.1))
for k in range(3):
    mix(x, n(k * beat * 2), 0.5 * thump(110, 45, 0.15, 0.05), 0.3 * pluck(D3 if k % 2 == 0 else A2, 0.3, 0.5, 0.99))
mix(x, n(6 * beat), 0.5 * thump(110, 45, 0.2, 0.06), 0.4 * pluck(D2 * 2, 1.0, 0.5, 0.997))
for f in (D5, Fs5, A5, D6):
    mix(x, n(6 * beat), 0.12 * brass(f, 0.9, 0.02, 0.5, 3000))
mix(x, n(6 * beat), 0.3 * glock(D7, 1.0, 0.4), 0.2 * glock(A6, 1.0, 0.4))
save("stage_start", x, 0.55)

d = 2.8  # stage_clear: a run up the scale, a cadence (G, A, D) with brass stabs, a big chord and sparkle
x = np.zeros(n(d))
for i, f in enumerate((D5, E5, Fs5, G5, A5, B5, Cs6, D6)):
    mix(x, n(i * 0.04), 0.2 * marimba(f, 0.25, 0.08), 0.1 * glock(f * 2, 0.25, 0.08))
for st, root, ch in ((0.4, G3, (B4, D5, G5)), (0.7, A3, (Cs5, E5, A5)), (1.0, A3, (Cs5, E5, G5))):
    mix(x, n(st), 0.4 * pluck(root / 2, 0.3, 0.5, 0.99), 0.4 * thump(110, 45, 0.15, 0.05))
    for p in ch:
        mix(x, n(st), 0.08 * brass(p, 0.18, 0.005, 0.12, 3500))
mix(x, n(1.3), 0.6 * pluck(D2, 1.3, 0.5, 0.997), 0.5 * thump(110, 40, 0.3, 0.08))
for f in (D4, Fs4, A4, D5, Fs5):
    mix(x, n(1.3), 0.08 * brass(f, 1.3, 0.02, 0.8, 3000), 0.1 * marimba(f, 0.8, 0.3))
for i, f in enumerate((A6, D7)):
    mix(x, n(1.3 + i * 0.08), 0.22 * glock(f, 1.2, 0.5))
mix(x, n(1.35), 0.07 * hp(s.noise(0.9), 7000) * curve([(0, 0), (0.1, 1), (0.9, 0)], 0.9))
save("stage_clear", x, 0.6)

d = 3.0  # game_over: the tune runs out of road: brass stepping down over pizzicato, a slow low D minor, a plink
x = np.zeros(n(d))
for st, f in ((0.0, A4), (0.35, Fs4), (0.7, D4), (1.05, m2f(61))):
    mix(x, n(st), 0.15 * brass(f, 0.35, 0.02, 0.25, 2000), 0.3 * marimba(f, 0.5, 0.18), 0.25 * pluck(f / 2, 0.4, 0.4, 0.99))
mix(x, n(1.5), 0.45 * pluck(D2, 1.3, 0.4, 0.997), 0.3 * marimba(D3, 1.2, 0.5))
for f in (D3, m2f(53), A3):
    mix(x, n(1.5), 0.08 * brass(f * curve([(0, 1), (1.2, 0.97)], 1.2), 1.2, 0.05, 0.9, 1500))
mix(x, n(2.45), 0.15 * glock(D5 * 2, 0.5, 0.2))
save("game_over", lp(x, 7000), 0.55)

d = 1.3  # extra_life: a cheery run up D major, a rubber boing and a sparkle
x = np.zeros(n(d))
for i, f in enumerate((D6, Fs6, A6, D7)):
    mix(x, n(i * 0.07), 0.22 * glock(f, 0.4, 0.12), 0.2 * marimba(f / 2, 0.3, 0.1))
mix(x, n(0.3), 0.2 * boing(500, 1000, 0.2, 20, 0.1) * env(n(0.2), 0.003, 0.08, 2.5))
mix(x, n(0.34), 0.12 * brass(D5, 0.6, 0.01, 0.35, 4000), 0.12 * brass(Fs5, 0.6, 0.01, 0.35, 4000),
    0.12 * brass(A5, 0.6, 0.01, 0.35, 4000))
mix(x, n(0.36), 0.25 * chime(D7 * 2, 0.8, 0.35))
save("extra_life", x, 0.5)
