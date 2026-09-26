#!/usr/bin/env python3
"""Sound effects for game 12 (Nightbite), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own: glassy neon blips and synth sweeps, no imitation of any arcade maze game's sounds.
Usage: python3 tools/audio/nightbite_sfx.py [out_dir]   (default: godot/games/nightbite/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/nightbite/audio/sfx", seed=1980)
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
    """A tone following a per-sample frequency curve: 'saw' (buzzy), 'square' (hollow) or 'sine'."""
    ph = 2 * np.pi * np.cumsum(freqs) / SR
    if shape == "sine":
        return np.sin(ph)
    ks = range(1, harmonics + 1) if shape == "saw" else range(1, 2 * harmonics, 2)
    return sum(np.sin(k * ph) / k for k in ks)


def synth(f, sec, shape="saw", attack=0.005, decay=0.25, curve=2.5, cutoff=4000, detune=0.006):
    """A neon synth voice: two detuned oscillators through a low-pass, with an envelope."""
    fv = np.full(n(sec), float(f)) if np.isscalar(f) else f
    x = tone(fv * (1 - detune / 2), shape) + tone(fv * (1 + detune / 2), shape)
    return lp(x, cutoff) * env(n(sec), attack, decay, curve)


def glint(f, sec=0.3, decay=0.12):
    """A glassy chime: a bright bell with an octave on top."""
    return s.bell(f, sec, partials=((1, 1.0), (2.0, 0.35), (3.01, 0.2), (5.4, 0.08)), decay=decay)


def loop_fix(freqs, sec):
    """Scales a frequency curve so the phase runs a whole number of cycles over the loop: no click at the seam."""
    cyc = np.sum(freqs) / SR
    return freqs * max(1, round(cyc)) / cyc


def loop_lp(x, cutoff):
    """A low-pass that has already run once around the loop, so its state meets itself at the seam."""
    return lp(np.tile(x, 2), cutoff)[len(x):]


def band_noise(N, lo, hi):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2), N)
    return x / np.max(np.abs(x))


# --- eating ---
for k, (f0, f1) in enumerate(((1760, 1320), (1976, 1480))):
    d = 0.06  # a pellet bite: a tiny glassy "tik" that dips in pitch, a soft sine body and a breath of air
    x = 0.8 * s.sweep(f0, f1, d) * env(n(d), 0.0015, 0.018, 3)
    x += 0.35 * glint(f0 * 1.5, d, 0.02)
    x += 0.15 * lp(hp(s.noise(d), 3000), 9000) * env(n(d), 0.0005, 0.006, 4)
    save(f"munch_{k}", lp(x, 7000), 0.28)

d = 1.1  # a power orb: a whoosh of air that opens up, a rising synth sweep and a shimmer of chimes climbing
tt = t(d)
x = lp(s.noise(d), np.geomspace(300, 9000, n(d))) * np.clip(tt / 0.25, 0, 1) * env(n(d), 0.25, 0.35, 2)
sweep = synth(np.geomspace(110, 880, n(d)), d, "saw", 0.02, 0.5, 2, 3500, 0.012)
x = 0.6 * x + 0.5 * sweep
mix(x, 0, 0.6 * s.sweep(160, 50, 0.2) * env(n(0.2), 0.001, 0.05, 3))  # a soft low thump under the hit
for i, f in enumerate((880.0, 1108.7, 1318.5, 1760.0, 2217.5, 2637.0, 3520.0)):
    mix(x, n(0.12 + i * 0.07), 0.3 * glint(f, 0.5, 0.18))
save("power", x, 0.55)

d = 1.5  # the spirits scared: a seamless wobbling synth, a minor chord warbling in and out of tune
N = n(d)
tt = np.arange(N) / SR
wob = 1 + 0.03 * np.sin(2 * np.pi * 6 * tt / d)  # 6 wobbles per loop, a whole number
x = np.zeros(N)
for f, a in ((220.0, 1.0), (261.6, 0.6), (329.6, 0.5), (440.0, 0.35)):
    x += a * tone(loop_fix(f * wob, d), "square", 6)
trem = 0.7 + 0.3 * np.sin(2 * np.pi * 12 * tt / d)  # a quicker flutter, 12 per loop
gate = 0.75 + 0.25 * np.cos(2 * np.pi * 6 * tt / d)
x = loop_lp(x * trem * gate, 1800) + 0.08 * band_noise(N, 2000, 6000) * gate
x -= np.mean(x)
s.save("scared_loop", x, 0.35, fade=False)

d = 0.38  # a spirit eaten: a bubbly pop that springs up in pitch, a bright top chime (the game raises the pitch)
x = np.zeros(n(d))
mix(x, 0, 0.9 * s.sweep(300, 1400, 0.09) * env(n(0.09), 0.001, 0.05, 2))
mix(x, 0, 0.3 * lp(hp(s.noise(0.02), 1500), 8000) * env(n(0.02), 0.0003, 0.004, 4))
mix(x, n(0.06), 0.5 * synth(1318.5, 0.3, "square", 0.002, 0.1, 3, 5000))
mix(x, n(0.06), 0.4 * glint(2637.0, 0.3, 0.1))
save("eat_spook", x, 0.5)

d = 1.0  # eyes rushing home: a seamless flutter, eight quick rising chirps per second over a wind
N = n(d)
chirp_len = N // 8
x = np.zeros(N)
m = chirp_len
f = np.geomspace(900, 2200, m)
ch = tone(f, "square", 4) * np.sin(np.pi * np.arange(m) / m) ** 2
for k in range(8):
    x[k * m:(k + 1) * m] += ch * (1.0 if k % 2 == 0 else 0.85)
x = loop_lp(x, 5000) + 0.25 * band_noise(N, 800, 5000) * (0.7 + 0.3 * np.cos(2 * np.pi * 8 * np.arange(N) / N))
x -= np.mean(x)
s.save("eyes_home", x, 0.3, fade=False)

# --- bonus gems ---
d = 0.9  # a gem appears: a sparkle of chimes tumbling in, bright air
x = np.zeros(n(d))
for i, f in enumerate((2637.0, 3520.0, 2960.0, 3951.1, 4698.6)):
    mix(x, n(i * 0.06), 0.4 * glint(f, 0.6, 0.2))
x += 0.12 * lp(hp(s.noise(d), 6000), 14000) * env(n(d), 0.12, 0.25, 2)
save("fruit", x, 0.4)

d = 0.6  # a gem eaten: a crunchy pop, then a quick bright rising pair of notes and a chime
x = np.zeros(n(d))
mix(x, 0, 0.7 * s.sweep(500, 1600, 0.05) * env(n(0.05), 0.0008, 0.03, 3))
mix(x, 0, 0.35 * lp(hp(s.noise(0.04), 2000), 9000) * env(n(0.04), 0.0005, 0.01, 4))
mix(x, n(0.04), 0.4 * synth(1046.5, 0.18, "square", 0.002, 0.07, 3, 5000))
mix(x, n(0.11), 0.45 * synth(1568.0, 0.4, "square", 0.002, 0.15, 3, 6000))
mix(x, n(0.11), 0.35 * glint(3136.0, 0.45, 0.16))
save("fruit_eat", x, 0.5)

# --- the hero ---
d = 1.7  # caught: the light fizzles out, a warbling pitch dive with crackling sparks, then a small pop
tt = t(1.4)
f = np.geomspace(1400, 70, len(tt)) * (1 + 0.05 * np.sin(2 * np.pi * np.geomspace(14, 5, len(tt)) * tt))
dive = synth(f, 1.4, "saw", 0.005, 0.9, 1.2, 3000, 0.02)
fizz = lp(hp(s.noise(1.4), 1200), np.geomspace(10000, 1500, len(tt)))
fizz *= (s.rng.uniform(0, 1, len(tt)) > 0.992).astype(float).cumsum() % 2 * 0.5 + 0.5  # crackles
fizz = fizz * env(len(tt), 0.01, 0.7, 1.5)
x = np.zeros(n(d))
mix(x, 0, 0.55 * dive + 0.35 * fizz)
mix(x, n(1.36), 0.8 * s.sweep(700, 90, 0.3) * env(n(0.3), 0.001, 0.08, 3))
mix(x, n(1.36), 0.4 * lp(s.noise(0.3), 2500) * env(n(0.3), 0.0005, 0.05, 4))
save("die", x, 0.6)

d = 1.3  # an extra life: a quick major run up on bright plucks, landing on a shimmering chord
x = np.zeros(n(d))
for i, f in enumerate((659.3, 830.6, 987.8, 1318.5, 1661.2)):
    mix(x, n(i * 0.06), 0.4 * synth(f, 0.25, "square", 0.002, 0.08, 3, 6000))
for f in (659.3, 987.8, 1318.5, 1661.2):
    mix(x, n(0.32), 0.18 * synth(f, 0.95, "saw", 0.01, 0.5, 1.5, 5000, 0.012))
for k in range(6):
    mix(x, n(0.34 + k * 0.08), 0.12 * glint(s.rng.choice((2637.0, 3322.4, 3951.1)), 0.35, 0.12))
save("extra_life", x, 0.55)

# --- stages ---
d = 2.1  # ready: a synth arpeggio winds up over a rising filter, two stabs, a final chord with a sparkle
x = np.zeros(n(d))
arp = (220.0, 261.6, 329.6, 440.0, 523.3, 659.3, 880.0, 1046.5)
for i in range(12):
    f = arp[i % 8] * (2 if i >= 8 else 1)
    mix(x, n(i * 0.095), 0.3 * synth(f, 0.14, "saw", 0.002, 0.05, 3, 1200 + 400 * i))
mix(x, 0, 0.25 * lp(s.noise(1.15), np.geomspace(200, 7000, n(1.15))) * np.clip(t(1.15) / 1.15, 0, 1) ** 2)
for st, chord in ((1.15, (349.2, 440.0, 523.3)), (1.33, (392.0, 493.9, 587.3))):
    for f in chord:
        mix(x, n(st), 0.25 * synth(f, 0.16, "saw", 0.002, 0.06, 3, 4500))
    mix(x, n(st), 0.5 * s.sweep(150, 50, 0.12) * env(n(0.12), 0.001, 0.03, 3))
for f in (220.0, 440.0, 554.4, 659.3, 880.0):
    mix(x, n(1.52), 0.18 * synth(f, 0.58, "saw", 0.004, 0.3, 1.6, 5000, 0.012))
mix(x, n(1.52), 0.7 * s.sweep(160, 45, 0.18) * env(n(0.18), 0.001, 0.05, 3))
mix(x, n(1.55), 0.3 * glint(3520.0, 0.5, 0.15))
save("ready", x, 0.6)

d = 2.1  # stage clear: a sparkling climb, a bouncy three-note tag and a bright major chord that rings out
x = np.zeros(n(d))
for i, f in enumerate((523.3, 659.3, 784.0, 1046.5, 1318.5, 1568.0, 2093.0)):
    mix(x, n(i * 0.05), 0.25 * synth(f, 0.18, "square", 0.002, 0.06, 3, 6000))
for st, f in ((0.42, 1568.0), (0.57, 1760.0), (0.72, 2093.0)):
    mix(x, n(st), 0.35 * synth(f, 0.16, "saw", 0.002, 0.07, 3, 5000))
    mix(x, n(st), 0.4 * s.sweep(140, 55, 0.1) * env(n(0.1), 0.001, 0.025, 3))
for f in (261.6, 523.3, 659.3, 784.0, 1046.5):
    mix(x, n(0.9), 0.16 * synth(f, 1.2, "saw", 0.008, 0.7, 1.4, 5500, 0.014))
mix(x, n(0.9), 0.8 * s.sweep(170, 45, 0.25) * env(n(0.25), 0.001, 0.07, 3))
for k in range(8):
    mix(x, n(0.92 + k * 0.07), 0.1 * glint(s.rng.choice((2093.0, 2637.0, 3136.0, 4186.0)), 0.4, 0.14))
save("stage_clear", x, 0.6)

d = 0.7  # the pace rises: two quick climbing blips and a whoosh that pulls forward
x = np.zeros(n(d))
mix(x, 0, 0.45 * synth(np.geomspace(440, 880, n(0.1)), 0.1, "square", 0.002, 0.05, 2, 5000))
mix(x, n(0.12), 0.5 * synth(np.geomspace(660, 1320, n(0.14)), 0.14, "square", 0.002, 0.07, 2, 6000))
tt = t(0.55)
mix(x, n(0.1), 0.45 * lp(s.noise(0.55), np.geomspace(800, 8000, len(tt))) * np.sin(np.pi * tt / 0.55) ** 2)
save("speed_up", x, 0.45)

# --- interface ---
d = 0.06  # a menu move: a tiny neon tick
save("menu_move", glint(2349.3, d, 0.015) + 0.4 * s.sweep(1500, 1100, d) * env(n(d), 0.001, 0.012, 3), 0.3)

d = 0.35  # a menu choice: two synth blips up and a chime
x = np.zeros(n(d))
mix(x, 0, 0.5 * synth(880.0, 0.12, "square", 0.002, 0.05, 3, 5000))
mix(x, n(0.06), 0.55 * synth(1318.5, 0.28, "square", 0.002, 0.1, 3, 6000) + 0.35 * glint(2637.0, 0.28, 0.1))
save("menu_select", x, 0.45)
