#!/usr/bin/env python3
"""Sound effects for game 11 (Crate Keeper), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/crates_sfx.py [out_dir]   (default: godot/games/crates/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/crates/audio/sfx", seed=1982)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, b):
    b = b[:max(0, len(x) - start)]
    x[start:start + len(b)] += b


def save(name, x, gain):
    """Saves a one-shot with its tail trimmed where it falls below -50 dB of the peak."""
    w = n(0.01)
    rms = np.sqrt(np.convolve(np.asarray(x) ** 2, np.ones(w) / w, "same"))
    end = min(len(x), np.nonzero(rms > np.max(np.abs(x)) * 0.00316)[0][-1] + n(0.02))
    s.save(name, x[:end], gain)


def tone(freqs, shape="saw", harmonics=8):
    """A tone following a per-sample frequency curve: 'saw' (reedy), 'square' (hollow) or 'sine'."""
    ph = 2 * np.pi * np.cumsum(freqs) / SR
    if shape == "sine":
        return np.sin(ph)
    ks = range(1, harmonics + 1) if shape == "saw" else range(1, 2 * harmonics, 2)
    return sum(np.sin(k * ph) / k for k in ks)


def knock(f, sec=0.12, decay=0.03):
    """A hollow wooden knock: inharmonic partials that die fast, and a click."""
    wood = s.bell(f, sec, partials=((1, 1.0), (1.58, 0.6), (2.31, 0.35), (3.9, 0.15)), decay=decay)
    return wood + 0.5 * lp(hp(s.noise(sec), 800), 5000) * env(n(sec), 0.0003, 0.006, 4)


def marimba(f, sec=0.4, decay=0.25):
    """A marimba bar: the fundamental with its tuned fourth and tenth partials."""
    return s.bell(f, sec, partials=((1, 1.0), (4.0, 0.25), (9.9, 0.06)), decay=decay)


def pluck(f, sec=0.8, bright=0.5, damp=0.996):
    """A nylon-string pluck (Karplus-Strong): a burst of noise circulating in a softly damped delay line."""
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 1500 + 6000 * bright)
    out = np.empty(n(sec))
    for i in range(len(out)):
        k = i % p
        out[i] = buf[k]
        buf[k] = damp * 0.5 * (buf[k] + buf[k - 1])
    return out * env(len(out), 0.001, sec, 0.5)


def reed(f, sec, attack=0.04, decay=0.8, curve=1.2, vib=0.004):
    """A harmonium or accordion reed: two slightly detuned saws beating slowly, through a soft low-pass."""
    tt = t(sec)
    fv = f * (1 + vib * np.sin(2 * np.pi * 5 * tt))
    x = tone(fv, "saw", 10) + tone(fv * 1.0035, "saw", 10)
    return lp(x, 2200) * env(n(sec), attack, decay, curve)


def clarinet(f, sec, attack=0.03, decay=0.6, curve=1.4, vib=0.008):
    """A woody clarinet: odd harmonics, a gentle vibrato that grows in, and a breath of air."""
    tt = t(sec)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5 * tt) * np.clip(tt / 0.2, 0, 1))) / SR
    x = np.sin(ph) + 0.35 * np.sin(3 * ph) + 0.15 * np.sin(5 * ph) + 0.06 * np.sin(7 * ph)
    x += 0.05 * lp(hp(s.noise(sec), f), f * 4)
    return lp(x, 3500) * env(n(sec), attack, decay, curve)


def grunt(f0, f1, sec, rough=0.3):
    """A small effort voice: a buzzy glottal glide through a low 'uh' formant, with a rasp."""
    tt = t(sec)
    f = np.geomspace(f0, f1, n(sec)) * (1 + 0.03 * np.sin(2 * np.pi * 30 * tt))
    v = lp(tone(f, "saw", 14), 900) + 0.5 * lp(hp(tone(f, "saw", 14), 500), 1300)
    v += rough * lp(hp(s.noise(sec), 300), 1500) * np.abs(np.sin(np.pi * np.cumsum(f) / SR))
    return v * np.clip(tt / 0.01, 0, 1) * np.clip((sec - tt) / (sec * 0.4), 0, 1)


def band_noise(N, lo, hi):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2), N)
    return x / np.max(np.abs(x))


def wrap(x, start, b):
    """Mixes b into the loop x at start, wrapping around the end."""
    x[(np.arange(len(b)) + start) % len(x)] += b


# --- the keeper moving ---
for k, (f, body) in enumerate(((230, 120), (255, 132), (215, 112))):
    d = 0.08  # a footstep: a soft boot on wooden boards, a low thud and a faint board knock
    x = 0.8 * s.sweep(body * 1.2, body * 0.6, d) * env(n(d), 0.001, 0.016, 3)
    x += 0.35 * knock(f, d, 0.012)
    x += 0.3 * lp(hp(s.noise(d), 500), 2000) * env(n(d), 0.0008, 0.01, 4)
    save(f"step_{k}", lp(x, 2200), 0.3)

d = 0.3  # a push: a heavy crate sliding on boards, a start knock, then a rough stick-slip scrape that eases off
tt = t(d)
rate = np.geomspace(70, 45, n(d)) * (1 + 0.1 * s.rng.standard_normal(n(d)).cumsum() / np.sqrt(n(d)))
pulses = 0.4 + 0.6 * np.clip(np.sin(2 * np.pi * np.cumsum(rate) / SR), 0, 1) ** 3
shape = np.clip(tt / 0.02, 0, 1) * np.clip((0.26 - tt) / 0.12, 0, 1)
scrape = lp(hp(s.noise(d), 180), 1400) * pulses * shape
x = 0.9 * scrape + 0.35 * lp(tone(rate * 2.2, "saw", 6), 700) * pulses * shape
x += 0.6 * s.sweep(110, 70, d) * env(n(d), 0.002, 0.05, 3) + 0.4 * knock(170, d, 0.03)
save("push", lp(x, 2600), 0.5)

d = 0.4  # a bump: a dull thud against the wall or a stuck crate, and a small "hmph"
x = np.zeros(n(d))
mix(x, 0, 1.1 * s.sweep(120, 45, 0.2) * env(n(0.2), 0.001, 0.045, 3) + 0.45 * knock(150, 0.2, 0.025))
mix(x, 0, 0.2 * lp(s.noise(0.08), 900) * env(n(0.08), 0.0005, 0.015, 4))
mix(x, n(0.05), 0.35 * grunt(210, 160, 0.13, 0.25))
save("bump", lp(x, 3000), 0.5)

# --- goals ---
d = 0.9  # on a goal: a latch click, then a warm two-note chime (B then G above), with a pluck under it
x = np.zeros(n(d))
mix(x, 0, 0.6 * knock(1900, 0.05, 0.006))
mix(x, 0, 0.4 * hp(s.noise(0.01), 3000) * env(n(0.01), 0.0002, 0.002, 4))
mix(x, n(0.035), 0.5 * knock(2500, 0.04, 0.004))
mix(x, n(0.06), 0.55 * s.bell(987.8, 0.5, decay=0.3) + 0.3 * pluck(493.9, 0.5, 0.4))
mix(x, n(0.14), 0.65 * s.bell(1568.0, 0.76, decay=0.45) + 0.3 * pluck(784.0, 0.76, 0.4))
mix(x, n(0.14), 0.12 * s.bell(3136.0, 0.4, decay=0.15))
save("on_goal", x, 0.5)

d = 0.3  # off a goal: a soft descending blip, two muted marimba notes
x = np.zeros(n(d))
mix(x, 0, 0.6 * marimba(784.0, 0.15, 0.06))
mix(x, n(0.07), 0.6 * marimba(587.3, 0.22, 0.08))
mix(x, 0, 0.25 * s.sweep(700, 420, 0.18) * env(n(0.18), 0.003, 0.07, 2))
save("off_goal", lp(x, 4000), 0.35)

# --- rewinds ---
d = 0.2  # an undo: a quick reversed swish, rising in pitch and brightness, cut short
tt = t(d)
swell = np.clip(tt / d, 0, 1) ** 2.5 * np.clip((d - tt) / 0.012, 0, 1)
x = lp(s.noise(d), np.geomspace(500, 5000, n(d))) * swell
x += 0.3 * lp(tone(np.geomspace(250, 900, n(d)), "saw", 5), 2500) * swell
save("undo", x, 0.35)

d = 0.8  # a restart: a tape rewind, warbling chirps that speed up and rise, then a soft wooden set-down
tt = t(0.66)
f = np.geomspace(180, 1400, len(tt)) * (1 + 0.06 * np.sin(2 * np.pi * np.geomspace(6, 22, len(tt)) * tt))
warble = lp(tone(f, "saw", 6), 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(np.geomspace(8, 30, len(tt))) / SR))
sw = lp(s.noise(0.66), np.geomspace(400, 6000, len(tt)))
shape = np.clip(tt / 0.1, 0, 1) * np.clip((0.66 - tt) / 0.02, 0, 1) * (0.4 + 0.6 * tt / 0.66)
x = np.zeros(n(d))
mix(x, 0, (0.35 * warble + 0.6 * sw) * shape)
mix(x, n(0.66), 0.7 * knock(260, 0.14, 0.03) + 0.5 * s.sweep(130, 70, 0.14) * env(n(0.14), 0.001, 0.03, 3))
save("restart", x, 0.4)

# --- rewards ---
d = 2.6  # a level solved: a plucked G major run up, a clarinet tune over a reed chord, a ship's bell, glints
x = np.zeros(n(d))
for i, f in enumerate((196.0, 246.9, 293.7, 392.0, 493.9, 587.3)):
    mix(x, n(i * 0.07), 0.4 * pluck(f, 1.2, 0.5))
for st, ln, f in ((0.46, 0.14, 587.3), (0.62, 0.14, 659.3), (0.78, 0.14, 740.0), (0.94, 0.3, 784.0),
                  (1.26, 0.12, 740.0), (1.4, 1.2, 784.0)):
    mix(x, n(st), 0.35 * clarinet(f, ln + 0.08, 0.02, ln, 1.3))
for f in (98.0, 196.0, 246.9, 293.7, 392.0):  # the accordion chord blooms under the last note
    mix(x, n(1.4), 0.1 * reed(f, 1.2, 0.05, 0.7, 1.4))
mix(x, n(1.4), 0.4 * pluck(98.0, 1.2, 0.3) + 0.3 * pluck(196.0, 1.2, 0.4))
mix(x, n(1.4), 0.35 * s.bell(784.0, 1.2, partials=((1, 1.0), (2.0, 0.4), (2.76, 0.3), (5.4, 0.1)), decay=0.9))
for k in range(8):
    mix(x, n(1.46 + k * 0.08), 0.08 * s.bell(s.rng.choice((1568.0, 1975.5, 2349.3, 3136.0)), 0.3, decay=0.12))
save("solved", x, 0.6)

d = 0.8  # a star: a quick sparkle of high chimes rising, and a shimmer of air
x = np.zeros(n(d))
for i, f in enumerate((1568.0, 1975.5, 2349.3, 3136.0)):
    mix(x, n(i * 0.05), 0.45 * s.bell(f, 0.6, decay=0.25))
mix(x, n(0.2), 0.25 * s.bell(3951.1, 0.5, decay=0.2))
x += 0.12 * lp(hp(s.noise(d), 5000), 12000) * np.clip(t(d) / 0.15, 0, 1) * env(n(d), 0.15, 0.2, 2)
save("star", x, 0.45)

# --- interface ---
d = 0.07  # a menu move: a tiny wooden tick
save("menu_move", marimba(1174.7, d, 0.03) + 0.3 * knock(1500, d, 0.01), 0.35)

d = 0.35  # a menu choice: two plucks and a chime
x = np.zeros(n(d))
mix(x, 0, 0.6 * pluck(587.3, 0.2, 0.6))
mix(x, n(0.07), 0.6 * pluck(784.0, 0.28, 0.6) + 0.4 * s.bell(1568.0, 0.28, decay=0.12))
save("menu_select", x, 0.45)

# --- ambience ---
d = 20.0  # the harbour at dusk: exactly 20 s, every sound wrapped around the loop, so it meets itself with no seam
N = n(d)
tt = np.arange(N) / SR
# waves: low rolling noise that swells in whole cycles per loop (5 and 3 per 20 s), plus slower laps on the piles
roll = band_noise(N, 40, 500) * (0.55 + 0.25 * np.sin(2 * np.pi * 5 * tt / d) + 0.2 * np.sin(2 * np.pi * 3 * tt / d + 1))
x = 0.5 * roll + 0.12 * band_noise(N, 20, 120)
x += 0.05 * band_noise(N, 500, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 5 * tt / d))  # a faint wash of spray
for k in range(9):  # laps: small splashes of brighter water against the quay
    ln = s.rng.uniform(0.8, 1.4)
    lap = lp(hp(s.noise(ln), 250), s.rng.uniform(1200, 2200)) * np.sin(np.pi * t(ln) / ln) ** 3
    lap *= 1 + 0.5 * np.sin(2 * np.pi * s.rng.uniform(7, 12) * t(ln))
    wrap(x, n(k * d / 9 + s.rng.uniform(0, 1.2)), 0.35 * lap)
for st in (3.1, 13.8):  # a wooden creak: a moored boat pulling on the pier, stick-slip pulses through the plank
    ln = 1.1
    rate = np.geomspace(18, 34, n(ln)) if st < 10 else np.geomspace(30, 16, n(ln))
    pulses = np.clip(np.sin(2 * np.pi * np.cumsum(rate) / SR), 0, 1) ** 10
    cr = lp(hp(s.noise(ln), 300), 1400) * pulses + 0.7 * lp(tone(rate * 9, "saw", 8), 1100) * pulses
    wrap(x, n(st), 0.35 * cr * np.sin(np.pi * t(ln) / ln))
for st, f0, calls in ((1.5, 1300, 2), (8.6, 1450, 3), (16.2, 1200, 1)):  # distant gulls: "kee-ow" calls
    for c in range(calls):
        ln = s.rng.uniform(0.35, 0.5)
        m = n(ln)
        f = f0 * (1 + 0.1 * c) * np.interp(np.arange(m), [0, m * 0.2, m], [0.75, 1.15, 0.8])
        ph = 2 * np.pi * np.cumsum(f) / SR
        g = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.15 * lp(hp(s.noise(ln), 1500), 4000)
        g = lp(g, 2800) * np.sin(np.pi * t(ln) / ln) ** 1.5
        at = n(st + c * s.rng.uniform(0.45, 0.6))
        wrap(x, at, 0.06 * g)
        wrap(x, at + n(0.19), 0.02 * lp(g, 1500))  # its echo off the warehouses
x -= np.mean(x)
s.save("ambience", x, 0.25, fade=False)
