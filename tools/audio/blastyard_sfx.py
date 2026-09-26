#!/usr/bin/env python3
"""Sound effects for game 9 (Blastyard), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/blastyard_sfx.py [out_dir]   (default: godot/games/blastyard/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/blastyard/audio/sfx", seed=1983)
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
    """A tone following a per-sample frequency curve: 'saw' (brassy), 'square' (chippy) or 'sine'."""
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


def boom(sec, f0=160, f1=38, tail=1.0, punch=2.5):
    """A cartoon explosion: a fat falling thump, a darkening noise burst and a rumble, squashed for punch."""
    x = (1.4 * s.sweep(f0, f1, sec) * env(n(sec), 0.002, 0.22 * tail, 3)
         + lp(s.noise(sec), np.geomspace(7000, 160, n(sec))) * env(n(sec), 0.0008, 0.28 * tail, 3)
         + 0.6 * lp(s.noise(sec), 200) * env(n(sec), 0.01, 0.7 * tail, 2.2))
    return np.tanh(punch * x / np.max(np.abs(x)))


def squeak(f0, f1, sec, vib=0.0, shape="square"):
    """A cute little voice: a pitch glide with a touch of vibrato through a soft low-pass."""
    tt = t(sec)
    f = np.geomspace(f0, f1, n(sec)) * (1 + vib * np.sin(2 * np.pi * 9 * tt))
    return lp(tone(f, shape, 5), 4500) * env(n(sec), 0.004, sec * 0.5, 1.5)


# --- bombs ---
d = 0.28  # a bomb set down: a soft, heavy clunk on the ground
x = 0.9 * s.sweep(170, 70, d) * env(n(d), 0.001, 0.05, 3) + 0.5 * knock(260, d, 0.035)
x += 0.25 * lp(s.noise(d), 900) * env(n(d), 0.0005, 0.02, 4)
save("place", lp(x, 3000), 0.55)

d = 1.0  # a lit fuse: exactly 1 s, circular noise and crackles wrapped around, so it loops with no seam
N = n(d)
tt = np.arange(N) / SR
F = np.fft.rfftfreq(N, 1 / SR)
band = np.exp(-((np.log(np.maximum(F, 1) / 4200)) ** 2) / 0.5)  # a hiss centred near 4 kHz
hiss = np.fft.irfft(np.fft.rfft(s.noise(d)) * band, N)
hiss /= np.max(np.abs(hiss))
flutter = 0.75 + 0.15 * np.sin(2 * np.pi * 13 * tt) + 0.1 * np.sin(2 * np.pi * 29 * tt + 1.3)
crackle = np.zeros(N)
for k in range(38):  # sparks popping
    c = hp(s.noise(0.006), 2500) * env(n(0.006), 0.0002, 0.0015, 4) * s.rng.uniform(0.3, 1.0)
    i = (np.arange(len(c)) + int(s.rng.uniform(0, N))) % N
    crackle[i] += c
s.save("fuse", 0.8 * hiss * flutter + 0.5 * crackle, 0.4, fade=False)

d = 1.0  # a bomb goes off: a punchy, round cartoon boom
x = boom(d, 170, 40, 0.8, 2.8)
x += 0.25 * s.bell(900, d, partials=((1, 1.0), (1.5, 0.5)), decay=0.03)  # the "pow" of the flash
save("explode", x, 0.85)

d = 1.8  # a chain reaction: three booms tumbling one into the next, and a long rumble
x = np.zeros(n(d))
for k, (st, f0) in enumerate(((0.0, 170), (0.12, 140), (0.27, 120))):
    mix(x, n(st), boom(1.3, f0, 34, 0.9 + 0.2 * k, 2.6) * (1 - 0.12 * k))
x += 0.7 * lp(s.noise(d), 150) * env(n(d), 0.05, 0.9, 2)
save("explode_big", np.tanh(1.3 * x / np.max(np.abs(x))), 0.9)

d = 0.7  # a wooden crate bursts: a crack, knocks of planks and a patter of splinters
x = 0.9 * lp(hp(s.noise(d), 500), 4000) * env(n(d), 0.0005, 0.035, 4)
x += 0.6 * s.sweep(220, 90, d) * env(n(d), 0.001, 0.05, 3)
for k, f in enumerate((340, 420, 290, 510, 380)):
    mix(x, n(0.01 + k * 0.045 + s.rng.uniform(0, 0.02)), 0.55 * knock(f, 0.15, 0.03) * (1 - 0.12 * k))
for k in range(12):
    mix(x, n(0.18 + k * 0.035 + s.rng.uniform(0, 0.02)),
        0.25 * hp(s.noise(0.02), 2000) * env(n(0.02), 0.0003, 0.006) * (1 - k / 13))
save("crate", x, 0.7)

d = 0.5  # a bomb kicked: a boot thunk, then the bomb sliding away over the ground
x = 0.8 * s.sweep(200, 80, d) * env(n(d), 0.001, 0.04, 3) + 0.4 * knock(300, d, 0.03)
slide = lp(hp(s.noise(d), 300), 1400) * np.clip((t(d) - 0.03) / 0.03, 0, 1) * env(n(d), 0.001, 0.3, 2.5)
save("kick", x + 0.35 * slide * (1 + 0.3 * np.sin(2 * np.pi * 23 * t(d))), 0.7)

d = 0.22  # a bomb stops against a wall: a dull thud
x = 0.9 * s.sweep(140, 60, d) * env(n(d), 0.001, 0.04, 3) + 0.4 * knock(210, d, 0.025)
save("bump", lp(x, 2500), 0.5)

# --- power-ups ---
d = 0.5  # a power-up collected: a bright rising arpeggio with a sparkle
x = np.zeros(n(d))
for i, f in enumerate((784.0, 987.8, 1174.7, 1568.0)):
    mix(x, n(i * 0.05), 0.3 * lp(note(f, 0.18, "square", 0.002, 0.08, 2), 7000))
    mix(x, n(i * 0.05), 0.4 * s.bell(f * 2, 0.3, decay=0.15))
mix(x, n(0.2), 0.5 * s.bell(3136, 0.3, decay=0.2))
save("pickup", x, 0.5)

d = 0.9  # a skull (a bad power-up): a queasy, wobbling descent on detuned squares
tt = t(d)
f = 420 * np.exp(-1.1 * tt) * (1 + 0.06 * np.sin(2 * np.pi * 7 * tt))
x = tone(f, "square", 6) + tone(f * 1.06, "square", 6)
x = lp(x, 1200 + 900 * np.sin(2 * np.pi * 3.5 * tt) ** 2) * env(n(d), 0.01, 0.45, 1.5)
save("skull", x, 0.45)

# --- characters ---
d = 0.3  # a player hurt: a cute "ouch" squeak and a pop
x = squeak(700, 1300, 0.12, 0.02)
x = np.concatenate([x, np.zeros(n(d) - len(x))])
mix(x, n(0.1), 0.6 * s.sweep(900, 300, 0.08) * env(n(0.08), 0.0005, 0.02, 3))
save("hurt", x, 0.5)

d = 1.1  # a player out: a pop, then a balloon deflating with a sad little whistle
x = np.zeros(n(d))
mix(x, 0, 0.9 * s.sweep(1200, 200, 0.09) * env(n(0.09), 0.0003, 0.02, 3) + 0.5 * hp(s.noise(0.09), 1500) * env(n(0.09), 0.0003, 0.008, 4))
tt = t(0.9)
whistle = tone(np.geomspace(900, 180, n(0.9)) * (1 + 0.04 * np.sin(2 * np.pi * 14 * tt)), "square", 4)
air = lp(hp(s.noise(0.9), 600), 2600)
fall = np.clip(tt / 0.03, 0, 1) * np.clip((0.9 - tt) / 0.25, 0, 1)
mix(x, n(0.12), (0.35 * lp(whistle, 2500) + 0.5 * air * (0.7 + 0.3 * np.sin(2 * np.pi * 26 * tt))) * fall)
save("die", x, 0.55)

d = 0.5  # an enemy defeated: a squeaky "boing" and a puff
x = np.zeros(n(d))
mix(x, 0, squeak(600, 1500, 0.1))
mix(x, n(0.09), 0.8 * squeak(1500, 350, 0.18, 0.05))
mix(x, n(0.2), 0.4 * lp(s.noise(0.25), 3000) * env(n(0.25), 0.01, 0.08, 3))
save("enemy_die", x, 0.5)

# --- rounds ---
d = 2.1  # a round won: a bouncy fanfare, a trill and a held major chord
x = np.zeros(n(d))
for st, ln, f in ((0.0, 0.1, 523.3), (0.12, 0.1, 659.3), (0.24, 0.1, 784.0), (0.36, 0.22, 1046.5),
                  (0.62, 0.1, 880.0), (0.74, 0.3, 1046.5)):
    mix(x, n(st), 0.33 * lp(note(f, ln + 0.08, "square", 0.003, ln, 1.5), 5000))
    mix(x, n(st), 0.25 * s.bell(f * 2, 0.3, decay=0.12))
for f in (349.2, 440.0, 523.3, 698.5):
    mix(x, n(1.1), 0.18 * lp(note(f, 1.0, "saw", 0.01, 0.7, 1.4, vib=0.006), 3500))
for f in (523.3, 659.3, 784.0, 1046.5):
    mix(x, n(1.1), 0.12 * lp(note(f, 1.0, "square", 0.01, 0.7, 1.4, vib=0.006), 4000))
mix(x, n(1.1), 0.5 * s.bell(2093, 0.9, decay=0.4) + 0.3 * lp(s.noise(0.9), 7000) * env(n(0.9), 0.001, 0.25, 3))
save("win", x, 0.65)

d = 1.4  # a draw: a shrug, two puzzled notes that go nowhere, and a soft plonk
x = np.zeros(n(d))
mix(x, 0, 0.35 * lp(note(587.3, 0.3, "square", 0.005, 0.2, 2) + 0.5 * note(740.0, 0.3, "square", 0.005, 0.2, 2), 3000))
mix(x, n(0.32), 0.35 * lp(note(554.4, 0.3, "square", 0.005, 0.2, 2) + 0.5 * note(698.5, 0.3, "square", 0.005, 0.2, 2), 3000))
mix(x, n(0.66), 0.4 * lp(note(587.3, 0.7, "square", 0.005, 0.4, 1.5, vib=0.02), 1800))
mix(x, n(0.66), 0.5 * knock(180, 0.3, 0.05))
save("draw", x, 0.5)

d = 0.12  # a countdown tick: a woodblock
save("countdown", knock(1100, d, 0.02), 0.5)

d = 0.8  # go: a bright stab with a whoosh
x = np.zeros(n(d))
for f in (523.3, 659.3, 784.0, 1046.5, 1318.5):
    mix(x, 0, 0.2 * lp(note(f, 0.6, "saw", 0.004, 0.25, 2), 5000))
mix(x, 0, 0.6 * s.bell(2093, 0.6, decay=0.25))
mix(x, 0, 0.5 * s.sweep(160, 60, 0.3) * env(n(0.3), 0.001, 0.06, 3))
x += 0.3 * lp(hp(s.noise(d), 1500), np.geomspace(2000, 9000, n(d))) * env(n(d), 0.05, 0.2, 2)
save("go", x, 0.65)

d = 1.5  # hurry up: a sudden-death siren, three wails that climb
tt = t(d)
ph = (tt / 0.5) % 1
f = np.where(ph < 0.7, 520 + 380 * ph / 0.7, 900 - 380 * (ph - 0.7) / 0.3) * (1 + 0.08 * (tt / d))
x = lp(tone(f, "square", 8) + 0.6 * tone(f * 1.5, "square", 6), 3500)
x *= np.clip(tt / 0.02, 0, 1) * np.clip((d - tt) / 0.08, 0, 1) * (0.8 + 0.2 * np.sin(2 * np.pi * 12 * tt))
save("hurry", np.tanh(1.4 * x / np.max(np.abs(x))), 0.32)

d = 0.8  # a block slams down in sudden death: a heavy stone slam, a crunch and a little dust
x = 1.4 * s.sweep(110, 35, d) * env(n(d), 0.001, 0.12, 3)
x += 0.9 * lp(s.noise(d), np.geomspace(5000, 200, n(d))) * env(n(d), 0.0005, 0.06, 3)
x += 0.4 * knock(150, d, 0.06) + 0.35 * lp(s.noise(d), 400) * env(n(d), 0.01, 0.35, 2)
for k in range(6):
    mix(x, n(0.08 + k * 0.05 + s.rng.uniform(0, 0.02)), 0.15 * hp(s.noise(0.02), 2500) * env(n(0.02), 0.0003, 0.006))
save("block_drop", np.tanh(1.8 * x / np.max(np.abs(x))), 0.8)

d = 1.2  # solo: the exit door appears, a rising shimmer of bells over a soft swell
x = np.zeros(n(d))
for i, f in enumerate((523.3, 659.3, 784.0, 987.8, 1174.7, 1568.0, 1975.5, 2349.3)):
    mix(x, n(i * 0.055), 0.35 * s.bell(f, 0.6, decay=0.35))
x += 0.3 * lp(note(392.0, d, "saw", 0.3, 0.6, 1.5) + note(587.3, d, "saw", 0.3, 0.6, 1.5), 1500)
x += 0.12 * lp(hp(s.noise(d), 3000), 9000) * env(n(d), 0.3, 0.3, 2)
save("exit_open", x, 0.55)

d = 2.6  # solo: a stage cleared, a cheerful run up, a bounce and a big final chord
x = np.zeros(n(d))
run = ((0.0, 392.0), (0.09, 440.0), (0.18, 493.9), (0.27, 523.3), (0.36, 587.3), (0.45, 659.3), (0.54, 698.5))
for st, f in run:
    mix(x, n(st), 0.3 * lp(note(f * 2, 0.12, "square", 0.002, 0.07, 2), 6000))
for st, ln, f in ((0.66, 0.18, 1568.0), (0.88, 0.1, 1318.5), (1.0, 0.1, 1568.0), (1.12, 0.3, 2093.0)):
    mix(x, n(st), 0.3 * lp(note(f, ln + 0.08, "square", 0.003, ln, 1.5), 6000))
    mix(x, n(st), 0.2 * s.bell(f, 0.3, decay=0.15))
for f in (261.6, 392.0, 523.3, 659.3, 784.0, 1046.5):
    mix(x, n(1.45), 0.14 * lp(note(f, 1.15, "saw", 0.01, 0.8, 1.3, vib=0.006), 3500))
mix(x, n(1.45), 0.6 * s.sweep(130, 55, 0.5) * env(n(0.5), 0.002, 0.1, 3))
mix(x, n(1.45), 0.5 * s.bell(2093, 1.1, decay=0.5))
for k in range(10):  # a little sparkle cascade on the chord
    mix(x, n(1.5 + k * 0.07), 0.12 * s.bell(s.rng.choice((2637.0, 3136.0, 3520.0, 4186.0)), 0.25, decay=0.1))
save("stage_clear", x, 0.65)

# --- interface ---
d = 0.06  # a menu move: a tiny bubble blip
save("menu_move", lp(tone(np.geomspace(900, 1400, n(d)), "square", 4), 6000) * env(n(d), 0.002, 0.03, 2), 0.35)

d = 0.25  # a menu choice: a two-note pop
x = np.zeros(n(d))
mix(x, 0, lp(note(880.0, 0.08, "square", 0.002, 0.04, 2), 6000))
mix(x, n(0.07), lp(note(1318.5, 0.16, "square", 0.002, 0.08, 2), 6000) + 0.5 * s.bell(2637, 0.16, decay=0.1))
save("menu_select", x, 0.45)
