#!/usr/bin/env python3
"""Sound effects for game 14 (Inkstorm), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own: pen scratches, brush swishes, plucked strings (Karplus-Strong), reedy woodwind tones and
small bells, no imitation of any line-drawing arcade game's sounds. Loops (draw_fast, draw_slow, fuse) are
built on whole cycles and circular noise, so their end meets their start with no click.
Usage: python3 tools/audio/inkstorm_sfx.py [out_dir]   (default: godot/games/inkstorm/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/inkstorm/audio/sfx", seed=1981)
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


def add(*parts):
    """Sums sounds of different lengths, padding the shorter ones with silence."""
    x = np.zeros(max(len(p) for p in parts))
    for p in parts:
        x[:len(p)] += p
    return x


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong): harp when bright, pizzicato when damped. `bright` shapes the pick."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1 if i - p - 1 >= 0 else i - p])
    return y * env(N, 0.001, sec, 0.5)


def reed(f, sec, attack=0.04, decay=0.4, curve=1.5, breath=0.12, vib=5.0):
    """A woodwind voice: odd-leaning harmonics with a gentle vibrato that grows in, and a breath of air."""
    tt = t(sec)
    fv = f * (1 + 0.006 * np.clip(tt / 0.25, 0, 1) * np.sin(2 * np.pi * vib * tt))
    ph = 2 * np.pi * np.cumsum(fv) / SR
    x = np.sin(ph) + 0.35 * np.sin(3 * ph) + 0.15 * np.sin(2 * ph) + 0.1 * np.sin(5 * ph)
    x = lp(x, min(5000, f * 6)) + breath * lp(hp(s.noise(sec), f), f * 4)
    return x * env(n(sec), attack, decay, curve)


def chime(f, sec=0.6, decay=0.25):
    """A small hand bell: warm inharmonic partials."""
    return s.bell(f, sec, partials=((1, 1.0), (2.0, 0.3), (2.76, 0.25), (5.4, 0.06)), decay=decay)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def swish(sec, lo, hi, attack, decay, curve=2.0):
    """A brush swish: noise swept through a rising band."""
    return lp(hp(s.noise(sec), lo), np.geomspace(hi / 3, hi, n(sec))) * env(n(sec), attack, decay, curve)


def loop_lp(x, cutoff):
    """A low-pass that has already run once around the loop, so its state meets itself at the seam."""
    return lp(np.tile(x, 2), cutoff)[len(x):]


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def circ_mix(x, start, b):
    """Mixes b into x wrapping round the end: for grains placed in a loop."""
    for i in range(len(b)):
        x[(start + i) % len(x)] += b[i]


# --- drawing (loops) ---
d = 0.25  # the fast pen: a scratchy nib dragging over paper, four strokes per loop, grit ticks in between
N = n(d)
ph = np.arange(N) / N
stroke = 0.55 + 0.45 * np.sin(np.pi * ((ph * 4) % 1)) ** 0.8  # four scratches a loop, a whole number
x = band_noise(N, 1800, 9000, 0.7) * stroke
x += 0.4 * band_noise(N, 500, 1600) * stroke
grit = np.zeros(N)
for k in range(14):  # tiny fibre catches
    g = hp(s.noise(0.004), 3000) * env(n(0.004), 0.0002, 0.0015, 3)
    circ_mix(grit, int(s.rng.uniform(0, N)), 0.8 * s.rng.uniform(0.4, 1) * g)
x += grit
x -= np.mean(x)
s.save("draw_fast", x, 0.28, fade=False)

d = 0.5  # the slow brush: a soft, wet sweep of bristles, two strokes per loop, low and airy
N = n(d)
ph = np.arange(N) / N
stroke = 0.6 + 0.4 * np.sin(np.pi * ((ph * 2) % 1)) ** 1.5
x = band_noise(N, 250, 2600, 1.2) * stroke + 0.25 * band_noise(N, 2500, 6000) * stroke ** 2
x = loop_lp(x, 3500)
x -= np.mean(x)
s.save("draw_slow", x, 0.22, fade=False)

d = 0.035  # a very soft tick along the edge: a pencil tap on card
x = lp(hp(s.noise(d), 1200), 5000) * env(n(d), 0.0003, 0.006, 4) + 0.4 * thump(900, 600, d, 0.006)
save("move_tick", x, 0.14)

# --- claiming land ---
d = 0.9  # a small claim: a brush swish lays the wash, a harp plucks a D major triad up, a little bell blooms
x = np.zeros(n(d))
mix(x, 0, 0.35 * swish(0.25, 400, 5000, 0.03, 0.12))
for i, f in enumerate((293.7, 370.0, 440.0, 587.3)):
    mix(x, n(0.04 + i * 0.045), 0.5 * pluck(f, 0.8, 0.55, 0.997))
mix(x, n(0.2), 0.3 * chime(1174.7, 0.65, 0.3))
save("claim_small", lp(x, 9000), 0.45)

d = 2.0  # a big claim: a long painterly bloom, a sweeping wash, a rising harp flourish, a woodwind chord that
x = np.zeros(n(d))  # swells, and bells scattering like drops of colour
tt = t(1.2)
mix(x, 0, 0.35 * lp(hp(s.noise(1.2), 300), np.geomspace(800, 9000, n(1.2))) * np.sin(np.pi * np.clip(tt / 1.2, 0, 1)) ** 1.5)
run = (293.7, 370.0, 440.0, 587.3, 740.0, 880.0, 1174.7, 1480.0, 1760.0)
for i, f in enumerate(run):
    mix(x, n(i * 0.05), 0.4 * pluck(f, 1.2, 0.6, 0.997))
for f, a in ((293.7, 0.35), (440.0, 0.3), (587.3, 0.3), (740.0, 0.25)):
    mix(x, n(0.42), a * reed(f, 1.4, 0.15, 0.6, 1.6, 0.08))
mix(x, n(0.42), 0.45 * thump(150, 60, 0.3, 0.09))
for k in range(9):
    mix(x, n(0.46 + k * 0.1), 0.14 * chime(s.rng.choice((1760.0, 2217.5, 2349.3, 2960.0)), 0.6, 0.25))
save("claim_big", lp(x, 10000), 0.6)

d = 0.4  # a small bell for each 5 %: a clear high ping with a soft wooden knock under it
x = 0.7 * chime(1567.98, d, 0.2) + 0.2 * chime(3135.96, d, 0.08)
mix(x, 0, 0.25 * thump(700, 400, 0.02, 0.006))
save("percent_tick", x, 0.3)

# --- danger ---
d = 0.45  # a spark born on the edge: a crackle of static and a thin rising zing
x = np.zeros(n(d))
for k in range(10):
    c = hp(s.noise(0.006), 2000) * env(n(0.006), 0.0002, 0.002, 3)
    mix(x, n(k * 0.022 + s.rng.uniform(0, 0.01)), s.rng.uniform(0.4, 1) * c)
tt = t(d)
z = s.sweep(900, 3600, d) * env(n(d), 0.02, 0.12, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * tt))
x += 0.35 * z
save("spark_spawn", lp(x, 11000), 0.42)

d = 1.0  # a burning fuse: hissing air, sputters and pops, all laid round the loop so it has no seam
N = n(d)
ph = np.arange(N) / N
x = band_noise(N, 2500, 10000, 0.6) * (0.75 + 0.25 * np.sin(2 * np.pi * 7 * ph) * np.sin(2 * np.pi * 3 * ph))
x += 0.4 * band_noise(N, 700, 2500) * (0.7 + 0.3 * np.cos(2 * np.pi * 11 * ph))
for k in range(26):  # crackles
    c = hp(s.noise(0.005), 1500) * env(n(0.005), 0.0002, 0.0018, 3)
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.6, 1.8) * c)
for k in range(4):  # little pops
    c = s.sweep(500, 200, 0.02) * env(n(0.02), 0.0005, 0.006, 3)
    circ_mix(x, int(s.rng.uniform(0, N)), 0.8 * c)
x -= np.mean(x)
s.save("fuse", x, 0.4, fade=False)

d = 1.0  # the storm splits: a swirling rush that tears, then two voices spin apart, one up and one down
x = np.zeros(n(d))
tt = t(d)
swirl = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(np.geomspace(4, 14, n(d))) / SR)
mix(x, 0, 0.5 * lp(hp(s.noise(d), 200), 1500 + 3500 * swirl) * env(n(d), 0.05, 0.35, 2))
mix(x, n(0.25), 0.6 * lp(hp(s.noise(0.12), 1000), 7000) * env(n(0.12), 0.001, 0.03, 3))  # the tear
mix(x, n(0.25), 0.5 * thump(160, 50, 0.2, 0.06))
for f0, f1 in ((220.0, 440.0), (220.0, 110.0)):
    ln = 0.7
    v = s.sweep(f0, f1, ln) + 0.3 * s.sweep(f0 * 2.01, f1 * 2.01, ln)
    mix(x, n(0.27), 0.28 * lp(v * env(n(ln), 0.01, 0.3, 2) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t(ln))), 3000))
save("storm_split", x, 0.5)

d = 1.7  # the marker caught: an ink splash (a wet splat, droplets pattering), then a sad falling bassoon line
x = np.zeros(n(d))
mix(x, 0, 0.8 * lp(s.noise(0.25), np.geomspace(6000, 400, n(0.25))) * env(n(0.25), 0.001, 0.06, 3))
mix(x, 0, 0.8 * thump(200, 55, 0.18, 0.05))
for k in range(7):  # droplets: tiny rising plops
    fr = s.rng.uniform(600, 1300)
    mix(x, n(0.07 + k * 0.04 + s.rng.uniform(0, 0.02)), 0.22 * s.sweep(fr, fr * 1.8, 0.03) * env(n(0.03), 0.001, 0.01, 3))
for i, (f0, f1, ln) in enumerate(((392.0, 370.0, 0.28), (349.2, 329.6, 0.28), (293.7, 220.0, 0.8))):
    mix(x, n(0.35 + i * 0.28), 0.35 * reed(np.geomspace(f0, f1, n(ln)).mean(), ln, 0.02, ln * 0.6, 1.5, 0.1, 4.5)
        * np.linspace(1, 0.9, n(ln)))
    mix(x, n(0.35 + i * 0.28), 0.2 * pluck(f0 / 2, ln + 0.2, 0.3, 0.994))
save("die", lp(x, 8000), 0.6)

# --- stages ---
d = 1.9  # ready: a harp rolls up a D minor chord, a flute-like reed answers with a rising question, a soft bell
x = np.zeros(n(d))
for i, f in enumerate((146.8, 220.0, 293.7, 349.2, 440.0, 587.3, 698.5, 880.0)):
    mix(x, n(i * 0.06), 0.4 * pluck(f, 1.4, 0.5, 0.997))
for st, f, ln in ((0.55, 587.3, 0.25), (0.8, 659.3, 0.25), (1.05, 880.0, 0.8)):
    mix(x, n(st), 0.4 * reed(f, ln, 0.03, ln * 0.7, 1.4, 0.1))
mix(x, n(1.05), 0.2 * chime(1760.0, 0.8, 0.3))
mix(x, n(1.05), 0.4 * thump(130, 55, 0.2, 0.06))
save("ready", x, 0.6)

d = 2.6  # stage clear: a bright harp climb, two woodwind stabs, a full major bloom that rings with bells
x = np.zeros(n(d))
for i, f in enumerate((293.7, 370.0, 440.0, 587.3, 740.0, 880.0, 1174.7)):
    mix(x, n(i * 0.055), 0.35 * pluck(f, 1.0, 0.6, 0.997))
for st, chord in ((0.45, (440.0, 554.4, 659.3)), (0.65, (493.9, 587.3, 740.0))):
    for f in chord:
        mix(x, n(st), 0.22 * reed(f, 0.18, 0.01, 0.12, 2.5, 0.06))
    mix(x, n(st), 0.35 * thump(160, 70, 0.1, 0.03))
for f in (146.8, 293.7, 370.0, 440.0, 587.3, 740.0):
    mix(x, n(0.9), 0.18 * reed(f, 1.65, 0.06, 0.9, 1.4, 0.05))
for i, f in enumerate((293.7, 440.0, 587.3, 740.0, 880.0)):
    mix(x, n(0.9 + i * 0.03), 0.28 * pluck(f, 1.6, 0.6, 0.998))
mix(x, n(0.9), 0.7 * thump(150, 45, 0.3, 0.08))
for k in range(10):
    mix(x, n(0.95 + k * 0.1), 0.1 * chime(s.rng.choice((1760.0, 2217.5, 2349.3, 2960.0)), 0.6, 0.25))
save("stage_clear", x, 0.6)

d = 2.6  # game over: a slow minor descent on the reed, a dull harp echo, a low D minor chord that fades
x = np.zeros(n(d))
for i, f in enumerate((440.0, 392.0, 349.2, 329.6)):
    mix(x, n(i * 0.32), 0.35 * reed(f, 0.5, 0.03, 0.3, 1.8, 0.1, 4.5))
    mix(x, n(i * 0.32 + 0.16), 0.15 * pluck(f / 2, 0.5, 0.3, 0.993))
for f in (73.4, 146.8, 220.0, 293.7, 349.2):
    mix(x, n(1.3), 0.16 * reed(f, 1.3, 0.05, 0.7, 1.5, 0.06, 4.0))
mix(x, n(1.3), 0.5 * thump(110, 40, 0.35, 0.12))
save("game_over", x, 0.55)

d = 1.3  # an extra life: a quick harp run up to a ringing major chord, a reed holding the top, bells
x = np.zeros(n(d))
for i, f in enumerate((587.3, 740.0, 880.0, 1174.7, 1480.0)):
    mix(x, n(i * 0.06), 0.35 * pluck(f, 1.0, 0.65, 0.997))
for f in (587.3, 880.0, 1174.7):
    mix(x, n(0.32), 0.2 * reed(f, 0.9, 0.04, 0.5, 1.5, 0.05))
for k in range(6):
    mix(x, n(0.34 + k * 0.08), 0.12 * chime(s.rng.choice((2349.3, 2960.0, 3520.0)), 0.5, 0.2))
save("extra_life", x, 0.55)
