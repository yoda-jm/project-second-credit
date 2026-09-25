#!/usr/bin/env python3
"""Sound effects for game 1, synthesised from scratch with NumPy (no samples, no third-party audio).

Usage: python3 tools/audio/rocks_sfx.py [out_dir]   (default: godot/games/rocks/audio/sfx)
Deterministic (fixed seed). Licence of the output: CC BY-SA 4.0. Provenance: this script.
"""
import os, sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(1984)
out = sys.argv[1] if len(sys.argv) > 1 else "godot/games/rocks/audio/sfx"
os.makedirs(out, exist_ok=True)


def t(sec):
    return np.arange(int(SR * sec)) / SR


def env(n, attack=0.005, decay=0.2, curve=4.0):
    x = np.arange(n) / SR
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    d = np.exp(-curve * np.clip(x - attack, 0, None) / max(decay, 1e-4))
    return a * d


def lowpass(x, cutoff):
    # one-pole low-pass, cutoff in Hz (scalar or per-sample array)
    c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    k = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += k[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def noise(sec):
    return rng.uniform(-1, 1, int(SR * sec))


def sweep(f0, f1, sec, shape=np.sin):
    tt = t(sec)
    f = np.geomspace(f0, f1, len(tt))
    return shape(2 * np.pi * np.cumsum(f) / SR)


def bell(freq, sec, partials=((1, 1.0), (2.76, 0.5), (5.4, 0.25), (8.9, 0.12)), decay=0.5):
    tt = t(sec)
    s = sum(a * np.sin(2 * np.pi * freq * r * tt) * np.exp(-tt * (3 + r) / decay) for r, a in partials)
    return s


def save(name, x, gain=0.9):
    x = np.asarray(x, dtype=float)
    fade = min(len(x), int(SR * 0.004))
    x[-fade:] *= np.linspace(1, 0, fade)
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    with wave.open(os.path.join(out, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    print("wrote", name, f"{len(x) / SR:.2f}s")


# digging through dirt: a short crumbly crunch
n = noise(0.16)
save("dig", lowpass(n, np.geomspace(2600, 500, len(n))) * env(len(n), 0.002, 0.08) +
     0.3 * lowpass(noise(0.16), 300) * env(len(n), 0.001, 0.03), 0.55)

# walking on empty floor: a soft tap
n = noise(0.07)
save("step", lowpass(n, 900) * env(len(n), 0.001, 0.02), 0.3)

# boulder landing: a heavy thud with a stony click on top
d = 0.35
thud = sweep(110, 42, d) * env(int(SR * d), 0.002, 0.18)
click = highpass(noise(d), 1500) * env(int(SR * d), 0.0005, 0.015)
grit = lowpass(noise(d), 1200) * env(int(SR * d), 0.002, 0.08)
save("boulder_land", thud + 0.35 * click + 0.4 * grit, 0.8)

# boulder pushed or rolling: a grinding scrape
d = 0.25
scrape = lowpass(noise(d), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t(d)))
save("boulder_roll", scrape * env(int(SR * d), 0.02, 0.15, 3), 0.5)

# gem landing: a bright glassy ting
save("gem_land", bell(1760, 0.5, decay=0.25) + 0.3 * bell(2637, 0.5, decay=0.2), 0.45)

# gem collected: a quick rising arpeggio of bells
notes = [1046.5, 1318.5, 1568.0, 2093.0]
x = np.zeros(int(SR * 0.6))
for i, f in enumerate(notes):
    b = bell(f, 0.6 - i * 0.05, decay=0.35)
    s = int(SR * 0.045 * i)
    x[s:s + len(b)] += b * (0.8 + 0.1 * i)
save("gem_collect", x, 0.6)

# explosion: a boom, a crackle and a long rumble
d = 1.6
boom = sweep(90, 28, d) * env(int(SR * d), 0.003, 0.5, 3)
crack = lowpass(noise(d), np.geomspace(6000, 300, int(SR * d))) * env(int(SR * d), 0.001, 0.35, 3)
rumble = lowpass(noise(d), 180) * env(int(SR * d), 0.05, 1.0, 2.5)
save("explosion", 1.0 * boom + 0.8 * crack + 1.2 * rumble, 0.95)

# the exit opens: a warm rising chord with shimmer
d = 1.4
tt = t(d)
chord = sum(np.sin(2 * np.pi * f * tt * (1 + 0.02 * tt)) for f in (261.6, 329.6, 392.0, 523.3))
shimmer = sum(0.2 * np.sin(2 * np.pi * f * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * tt)) for f in (1046.5, 1568))
save("exit_open", (chord + shimmer) * env(len(tt), 0.25, 0.9, 2.5), 0.6)

# player appears at the entrance: a sparkling whoosh up
d = 0.7
wh = lowpass(noise(d), np.geomspace(300, 5000, int(SR * d))) * env(int(SR * d), 0.35, 0.3, 4)
save("hatch", wh + 0.3 * bell(1568, d, decay=0.3), 0.55)

# entering the exit: a bright ascending run
x = np.zeros(int(SR * 0.9))
for i, f in enumerate([523.3, 659.3, 784.0, 1046.5, 1318.5, 1568.0]):
    b = bell(f, 0.5, decay=0.3)
    s = int(SR * 0.06 * i)
    x[s:s + len(b)] += b
save("exit_enter", x, 0.6)

# last seconds: a clock tick
save("tick", highpass(noise(0.03), 2000) * env(int(SR * 0.03), 0.0005, 0.008) +
     0.5 * np.sin(2 * np.pi * 1800 * t(0.03)) * env(int(SR * 0.03), 0.0005, 0.01), 0.4)

# time out / death: a descending sad slide
d = 0.9
save("fail", sweep(440, 110, d, lambda p: np.sign(np.sin(p)) * 0.5 + np.sin(p)) * env(int(SR * d), 0.01, 0.6, 2.5) *
     0.5, 0.5)

# amoeba: a wet bubble
d = 0.18
save("amoeba", sweep(220, 520, d) * env(int(SR * d), 0.005, 0.08) * (1 + 0.5 * np.sin(2 * np.pi * 40 * t(d))), 0.35)

# magic wall: a shimmering chime
save("magic_wall", bell(880, 0.6, decay=0.4) * (1 + 0.6 * np.sin(2 * np.pi * 12 * t(0.6))), 0.4)

# creature explodes into gems (butterfly): explosion with a crystal tail
d = 1.4
x = sweep(120, 40, d) * env(int(SR * d), 0.003, 0.4, 3) + 0.6 * lowpass(noise(d), 2500) * env(int(SR * d), 0.001, 0.3, 3)
tail = sum(bell(f, d, decay=0.6) for f in (1318.5, 1760, 2349))
save("butterfly_burst", x + 0.25 * tail, 0.9)
