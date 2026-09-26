#!/usr/bin/env python3
"""Sound effects for game 10 (Ingot Run), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/ingot_sfx.py [out_dir]   (default: godot/games/ingot/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/ingot/audio/sfx", seed=1984)
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
    """A tone following a per-sample frequency curve: 'saw' (brassy), 'square' (hollow) or 'sine'."""
    ph = 2 * np.pi * np.cumsum(freqs) / SR
    if shape == "sine":
        return np.sin(ph)
    ks = range(1, harmonics + 1) if shape == "saw" else range(1, 2 * harmonics, 2)
    return sum(np.sin(k * ph) / k for k in ks)


def note(f, sec, shape="saw", attack=0.01, decay=0.3, curve=2.0, vib=0.0):
    tt = t(sec)
    return tone(f * (1 + vib * np.sin(2 * np.pi * 5.5 * tt)), shape) * env(len(tt), attack, decay, curve)


def knock(f, sec=0.12, decay=0.03):
    """A hollow wooden knock: inharmonic partials that die fast, and a click."""
    wood = s.bell(f, sec, partials=((1, 1.0), (1.58, 0.6), (2.31, 0.35), (3.9, 0.15)), decay=decay)
    return wood + 0.5 * lp(hp(s.noise(sec), 800), 5000) * env(n(sec), 0.0003, 0.006, 4)


def stone(f, sec=0.1, decay=0.02):
    """A brick chip: a dry, stony knock with more grit than wood."""
    x = s.bell(f, sec, partials=((1, 1.0), (1.73, 0.7), (2.9, 0.5), (4.6, 0.3)), decay=decay)
    return x + 0.8 * lp(hp(s.noise(sec), 1200), 7000) * env(n(sec), 0.0002, 0.008, 4)


def marimba(f, sec=0.4, decay=0.25):
    """A marimba bar: the fundamental with its tuned fourth and tenth partials."""
    return s.bell(f, sec, partials=((1, 1.0), (4.0, 0.25), (9.9, 0.06)), decay=decay)


def ocarina(f, sec, attack=0.03, decay=0.6, curve=1.5, vib=0.012):
    """A breathy ocarina: an almost pure tone with a soft second harmonic, vibrato and a little air."""
    tt = t(sec)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 0.15, 0, 1))) / SR
    x = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.04 * np.sin(3 * ph)
    x += 0.08 * lp(hp(s.noise(sec), f), f * 3)
    return x * env(n(sec), attack, decay, curve)


def grunt(f0, f1, sec, rough=0.3):
    """A comic guard voice: a buzzy glottal glide through a low 'uh' formant, with a rasp."""
    tt = t(sec)
    f = np.geomspace(f0, f1, n(sec)) * (1 + 0.03 * np.sin(2 * np.pi * 30 * tt))
    v = lp(tone(f, "saw", 14), 900) + 0.5 * lp(hp(tone(f, "saw", 14), 500), 1300)
    v += rough * lp(hp(s.noise(sec), 300), 1500) * np.abs(np.sin(np.pi * np.cumsum(f) / SR))
    return v * np.clip(tt / 0.01, 0, 1) * np.clip((sec - tt) / (sec * 0.4), 0, 1)


def squeak(f0, f1, sec, vib=0.0, shape="square"):
    """A little voice: a pitch glide with a touch of vibrato through a soft low-pass."""
    tt = t(sec)
    f = np.geomspace(f0, f1, n(sec)) * (1 + vib * np.sin(2 * np.pi * 9 * tt))
    return lp(tone(f, shape, 5), 4500) * env(n(sec), 0.004, sec * 0.5, 1.5)


# --- the runner moving ---
d = 0.09  # a footstep: a soft padded tap on stone
x = 0.8 * s.sweep(150, 70, d) * env(n(d), 0.001, 0.018, 3)
x += 0.5 * lp(hp(s.noise(d), 400), 2200) * env(n(d), 0.0008, 0.012, 4)
save("step", lp(x, 2500), 0.35)

d = 0.22  # a ladder rung: a grip tap and a short wooden creak (stick-slip pulses through the wood)
tt = t(d)
rate = np.geomspace(55, 85, n(d))
pulses = np.clip(np.sin(2 * np.pi * np.cumsum(rate) / SR), 0, 1) ** 8
creak = lp(hp(s.noise(d), 500), 2200) * pulses + 0.6 * lp(tone(rate * 3.1, "saw", 8), 1600) * pulses
creak *= np.clip((tt - 0.02) / 0.03, 0, 1) * np.clip((d - tt) / 0.08, 0, 1)
x = 0.7 * knock(420, d, 0.02) + 0.8 * creak
save("ladder", x, 0.4)

d = 0.26  # a hand over hand on the bar: two grips, each a small iron clink and a rope rasp
x = np.zeros(n(d))
for k, st in enumerate((0.0, 0.12)):
    g = 0.5 * s.bell(1650 + 180 * k, 0.12, partials=((1, 1.0), (2.41, 0.5), (3.87, 0.3)), decay=0.03)
    g += 0.6 * lp(hp(s.noise(0.12), 1500), 4500) * env(n(0.12), 0.004, 0.035, 3)
    mix(x, n(st), g * (1 - 0.2 * k))
save("bar", x, 0.35)

d = 0.4  # a fall: a short whoosh that darkens as the runner drops, and a faint falling whistle
tt = t(d)
shape = np.clip(tt / 0.05, 0, 1) * np.clip((d - tt) / 0.15, 0, 1)
x = lp(s.noise(d), np.geomspace(4000, 500, n(d))) * shape
x += 0.15 * s.sweep(1100, 450, d) * shape
save("fall", x, 0.4)

d = 0.25  # a landing: a soft thump, a scuff and a puff of dust
x = 1.0 * s.sweep(130, 50, d) * env(n(d), 0.001, 0.04, 3) + 0.4 * knock(190, d, 0.025)
x += 0.4 * lp(hp(s.noise(d), 600), 3000) * env(n(d), 0.01, 0.06, 3)
save("land", lp(x, 3000), 0.5)

# --- bricks ---
d = 0.5  # a brick zapped away: a crackling downward zap, then the brick crumbling into grit
x = np.zeros(n(d))
zap = lp(tone(np.geomspace(1800, 220, n(0.14)), "square", 6), 5000) * env(n(0.14), 0.001, 0.07, 2)
mix(x, 0, 0.5 * zap * (1 + 0.5 * np.sign(np.sin(2 * np.pi * 60 * t(0.14)))))
for k in range(14):  # chips tumbling down
    f = s.rng.uniform(500, 1400)
    mix(x, n(0.05 + k * 0.022 + s.rng.uniform(0, 0.012)), 0.35 * stone(f, 0.06, 0.012) * (1 - k / 16))
x += 0.45 * lp(s.noise(d), 1500) * np.clip((t(d) - 0.04) / 0.03, 0, 1) * env(n(d), 0.001, 0.14, 2.5)
save("dig", x, 0.6)

d = 0.75  # a hole refills: a low grinding rumble swelling up, stones knocking faster, and a solid clunk
tt = t(d)
swell = np.clip(tt / 0.5, 0, 1) ** 1.5 * np.clip((0.62 - tt) / 0.04, 0, 1)
x = 0.8 * lp(s.noise(d), 180) * swell * 3
x += 0.3 * lp(hp(s.noise(d), 300), 1200) * swell * (0.6 + 0.4 * np.sin(2 * np.pi * 17 * tt))
st = 0.05
while st < 0.58:  # knocks that accelerate as the bricks close up
    mix(x, n(st), 0.3 * stone(s.rng.uniform(250, 600), 0.06, 0.015))
    st += 0.09 * (1 - st / 0.75) + 0.015
clunk = 1.3 * s.sweep(160, 55, 0.13) * env(n(0.13), 0.001, 0.05, 3) + 0.7 * stone(300, 0.13, 0.03)
mix(x, n(0.6), clunk)
save("refill", np.tanh(1.4 * x / np.max(np.abs(x))), 0.6)

# --- gold ---
d = 0.5  # a gold ingot: a bright two-note chime with a glint on top
x = np.zeros(n(d))
mix(x, 0, 0.6 * s.bell(1318.5, 0.3, decay=0.12))
mix(x, n(0.06), 0.7 * s.bell(1975.5, 0.44, decay=0.2))
mix(x, n(0.06), 0.25 * s.bell(3951, 0.3, decay=0.1))
mix(x, 0, 0.15 * hp(s.noise(0.03), 4000) * env(n(0.03), 0.0002, 0.006, 4))
save("gold", x, 0.5)

d = 1.6  # the last gold: a rising D minor arpeggio of chimes over an ocarina swell, then the exit shines out in D major
x = np.zeros(n(d))
arp = (293.7, 349.2, 440.0, 554.4, 587.3, 698.5, 880.0, 1108.7, 1174.7)
for i, f in enumerate(arp):
    mix(x, n(i * 0.07), 0.3 * marimba(f, 0.5, 0.2) + 0.28 * s.bell(f * 2, 0.5, decay=0.3))
mix(x, 0, 0.18 * ocarina(293.7, 0.75, 0.3, 0.5, 1.5))
for f in (587.3, 740.0, 880.0, 1174.7):  # the D major bloom
    mix(x, n(0.66), 0.14 * ocarina(f, 0.94, 0.02, 0.5, 1.6))
mix(x, n(0.66), 0.45 * s.bell(2349.3, 0.94, decay=0.45))
for k in range(12):
    mix(x, n(0.68 + k * 0.05), 0.1 * s.bell(s.rng.choice((2349.3, 2960.0, 3520.0, 4698.6)), 0.25, decay=0.1))
x += 0.1 * lp(hp(s.noise(d), 3500), 10000) * np.clip(t(d) / 0.66, 0, 1) * env(n(d), 0.66, 0.3, 2)
save("all_gold", x, 0.6)

# --- guards ---
d = 0.55  # a guard drops into a hole: a comic falling slide-whistle, a thud and an "oof"
x = np.zeros(n(d))
mix(x, 0, 0.2 * lp(tone(np.geomspace(900, 350, n(0.12)), "sine"), 3000) * env(n(0.12), 0.005, 0.1, 1))
mix(x, n(0.11), 1.2 * s.sweep(180, 55, 0.2) * env(n(0.2), 0.001, 0.05, 3) + 0.5 * knock(160, 0.2, 0.03))
mix(x, n(0.11), 0.4 * s.bell(620, 0.2, partials=((1, 1.0), (1.5, 0.3)), decay=0.04))
mix(x, n(0.16), 0.55 * grunt(190, 120, 0.2))
save("trapped", x, 0.6)

d = 0.45  # a guard climbs out: two scrabbling scrapes, a knock and a "hup!"
x = np.zeros(n(d))
for k, st in enumerate((0.0, 0.09, 0.17)):
    mix(x, n(st), 0.35 * lp(hp(s.noise(0.06), 900), 3500) * env(n(0.06), 0.003, 0.02, 3))
    mix(x, n(st), 0.3 * stone(380 + 90 * k, 0.05, 0.012))
mix(x, n(0.24), 0.5 * grunt(150, 240, 0.14, 0.2))
save("guard_escape", x, 0.5)

d = 0.65  # a guard buried by a refilling hole: a grinding crunch, a squashed "urk" and a heavy clunk
x = np.zeros(n(d))
x += 0.7 * lp(s.noise(d), np.geomspace(3000, 300, n(d))) * env(n(d), 0.001, 0.12, 2.5)
for k in range(10):
    mix(x, n(k * 0.018 + s.rng.uniform(0, 0.01)), 0.3 * stone(s.rng.uniform(300, 900), 0.05, 0.01))
mix(x, n(0.03), 0.5 * grunt(260, 90, 0.2, 0.5))
mix(x, n(0.2), 1.3 * s.sweep(140, 45, 0.3) * env(n(0.3), 0.001, 0.07, 3) + 0.6 * stone(220, 0.3, 0.04))
save("guard_crushed", np.tanh(1.5 * x / np.max(np.abs(x))), 0.5)

d = 0.55  # a guard reappears at the top: a magical pop, a puff and a sparkle
x = np.zeros(n(d))
mix(x, 0, 0.5 * lp(hp(s.noise(0.2), 800), np.geomspace(1000, 7000, n(0.2))) * np.clip(t(0.2) / 0.2, 0, 1) ** 2)
mix(x, n(0.18), 0.8 * s.sweep(300, 1400, 0.05) * env(n(0.05), 0.0005, 0.02, 3))
mix(x, n(0.18), 0.4 * lp(s.noise(0.2), 2500) * env(n(0.2), 0.002, 0.05, 3))
for k, f in enumerate((1568.0, 2093.0, 2637.0)):
    mix(x, n(0.2 + k * 0.04), 0.3 * s.bell(f, 0.3, decay=0.12))
save("guard_respawn", x, 0.45)

# --- the runner ---
d = 1.6  # caught: a hit, then a sad falling line in D minor on a wobbly ocarina, ending on a low chord
x = np.zeros(n(d))
mix(x, 0, 0.9 * s.sweep(220, 60, 0.2) * env(n(0.2), 0.001, 0.05, 3) + 0.6 * knock(240, 0.2, 0.03))
mix(x, 0, 0.3 * lp(hp(s.noise(0.15), 1000), 5000) * env(n(0.15), 0.0005, 0.03, 3))
for k, f in enumerate((880.0, 698.5, 587.3, 554.4)):
    mix(x, n(0.14 + k * 0.17), 0.45 * ocarina(f, 0.22, 0.01, 0.15, 1.5, 0.02))
    mix(x, n(0.14 + k * 0.17), 0.2 * marimba(f / 2, 0.3, 0.15))
for f in (146.8, 220.0, 293.7, 349.2):
    mix(x, n(0.84), 0.2 * lp(note(f, 0.76, "saw", 0.01, 0.5, 1.6, vib=0.01), 1400))
mix(x, n(0.84), 0.35 * ocarina(293.7, 0.76, 0.01, 0.5, 1.6, 0.03))
save("die", x, 0.55)

d = 2.6  # a cavern cleared: a marimba run up, an ocarina call over hand-drum hits, a big D major chord
x = np.zeros(n(d))
for i, f in enumerate((293.7, 349.2, 392.0, 440.0, 523.3, 587.3, 698.5, 880.0)):
    mix(x, n(i * 0.06), 0.4 * marimba(f * 2, 0.35, 0.18))
for st, ln, f in ((0.5, 0.18, 880.0), (0.7, 0.18, 1046.5), (0.9, 0.12, 987.8), (1.04, 0.3, 1174.7)):
    mix(x, n(st), 0.4 * ocarina(f, ln + 0.1, 0.01, ln, 1.4))
    mix(x, n(st), 0.35 * knock(200 if st < 1 else 150, 0.15, 0.04))  # the hand drum
for f in (146.8, 293.7, 370.0, 440.0, 587.3, 740.0, 880.0):
    mix(x, n(1.4), 0.12 * lp(note(f, 1.2, "saw", 0.02, 0.8, 1.3, vib=0.006), 3000))
mix(x, n(1.4), 0.35 * ocarina(1174.7, 1.2, 0.01, 0.8, 1.3))
mix(x, n(1.4), 0.7 * s.sweep(120, 50, 0.5) * env(n(0.5), 0.002, 0.1, 3))
mix(x, n(1.4), 0.45 * s.bell(2349.3, 1.2, decay=0.5))
for k in range(10):  # a cascade of glints on the chord
    mix(x, n(1.45 + k * 0.07), 0.12 * s.bell(s.rng.choice((2349.3, 2960.0, 3520.0, 4698.6)), 0.25, decay=0.1))
save("level_clear", x, 0.65)

# --- interface ---
d = 0.07  # a menu move: a tiny marimba tick
save("menu_move", marimba(1174.7, d, 0.03) + 0.3 * knock(1500, d, 0.01), 0.35)

d = 0.3  # a menu choice: two marimba notes and a chime
x = np.zeros(n(d))
mix(x, 0, marimba(880.0, 0.12, 0.06))
mix(x, n(0.07), marimba(1318.5, 0.23, 0.1) + 0.5 * s.bell(2637, 0.23, decay=0.1))
save("menu_select", x, 0.45)
