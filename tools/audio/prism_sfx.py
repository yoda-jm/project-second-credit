#!/usr/bin/env python3
"""Sound effects for game 13 (Prism Breaker), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own: glass chimes, synth plucks and filtered air, no imitation of any brick-breaker's sounds.
Usage: python3 tools/audio/prism_sfx.py [out_dir]   (default: godot/games/prism/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/prism/audio/sfx", seed=1987)
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
    """A synth voice: two detuned oscillators through a low-pass, with an envelope."""
    fv = np.full(n(sec), float(f)) if np.isscalar(f) else f
    x = tone(fv * (1 - detune / 2), shape) + tone(fv * (1 + detune / 2), shape)
    return lp(x, cutoff) * env(n(sec), attack, decay, curve)


def glass(f, sec=0.5, decay=0.2):
    """A crystal chime: inharmonic partials like a struck glass rod, bright and clean."""
    return s.bell(f, sec, partials=((1, 1.0), (2.32, 0.45), (4.25, 0.22), (6.63, 0.1)), decay=decay)


def glint(f, sec=0.3, decay=0.12):
    """A glassy sparkle: a bright bell with an octave on top."""
    return s.bell(f, sec, partials=((1, 1.0), (2.0, 0.35), (3.01, 0.2), (5.4, 0.08)), decay=decay)


def add(*parts):
    """Sums sounds of different lengths, padding the shorter ones with silence."""
    x = np.zeros(max(len(p) for p in parts))
    for p in parts:
        x[:len(p)] += p
    return x


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def tick(sec, lo, hi, decay):
    return lp(hp(s.noise(sec), lo), hi) * env(n(sec), 0.0003, decay, 4)


# --- the ball ---
d = 0.16  # off the paddle: a round sine thump with a short pitch drop, a soft pluck on top, a breath of air
x = 0.9 * thump(520, 260, d, 0.05)
x += 0.35 * synth(784.0, d, "square", 0.001, 0.035, 3, 3000)
mix(x, 0, 0.2 * tick(0.02, 1500, 7000, 0.004))
save("paddle", lp(x, 6000), 0.5)

d = 0.07  # off the frame: a short metallic tick, two close inharmonic partials and a snap of noise
tt = t(d)
x = (np.sin(2 * np.pi * 2350 * tt) + 0.6 * np.sin(2 * np.pi * 3710 * tt) + 0.3 * np.sin(2 * np.pi * 5230 * tt))
x *= env(n(d), 0.0005, 0.018, 3)
mix(x, 0, 0.4 * tick(0.015, 3000, 10000, 0.003))
save("wall", x, 0.3)

# six crystal bricks: a major pentatonic climb (C D E G A C), so a fast combo plays a little tune
for k, f in enumerate((1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 2093.0)):
    d = 0.5
    x = 0.8 * glass(f, d, 0.26)
    x += 0.25 * glint(f * 2, d, 0.06)
    mix(x, 0, 0.35 * tick(0.03, 2500, 12000, 0.006))  # the shatter
    shards = np.zeros(n(d))  # a few tiny shards tinkling after the break
    for j in range(4):
        mix(shards, n(0.03 + 0.035 * j + s.rng.uniform(0, 0.015)), 0.12 * glint(f * s.rng.choice((3, 4, 5)), 0.12, 0.02))
    save(f"brick_{k}", lp(x + shards, 14000), 0.42)

d = 0.3  # a hard brick hit but not broken: a tight crystal clink, higher and shorter, no shatter
x = 0.8 * glass(2489.0, d, 0.07) + 0.4 * glass(3729.3, d, 0.04)
mix(x, 0, 0.3 * tick(0.01, 4000, 12000, 0.002))
save("hard", x, 0.38)

d = 0.55  # off steel or gold: a dull ring, low inharmonic metal partials damped quickly, a knock under it
tt = t(d)
x = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * r) for f, a, r in
        ((392.0, 1.0, 9), (1043.0, 0.45, 14), (1587.0, 0.25, 20), (2311.0, 0.12, 28)))
x *= np.clip(tt / 0.001, 0, 1)
mix(x, 0, 0.5 * thump(300, 120, 0.06, 0.02))
save("steel", lp(x, 5000), 0.42)

d = 0.25  # launched: a quick rising zip and a click
x = 0.6 * synth(np.geomspace(330, 1320, n(d)), d, "square", 0.002, 0.1, 2, 5000)
mix(x, 0, 0.5 * thump(600, 300, 0.05, 0.015))
save("launch", x, 0.45)

d = 1.3  # the ball lost: a falling glassy line, three sighing steps down, a low fizzle out
x = np.zeros(n(d))
for i, (f0, f1) in enumerate(((880.0, 830.6), (698.5, 659.3), (587.3, 440.0))):
    ln = 0.24 if i < 2 else 0.8
    mix(x, n(i * 0.24), 0.4 * synth(np.geomspace(f0, f1, n(ln)), ln, "saw", 0.005, 0.12 if i < 2 else 0.4, 2, 2600, 0.014))
    mix(x, n(i * 0.24), 0.2 * glass(f0 * 2, 0.4, 0.1))
tt = t(0.7)
mix(x, n(0.5), 0.3 * lp(s.noise(0.7), np.geomspace(4000, 300, len(tt))) * env(len(tt), 0.05, 0.3, 2))
save("lose_ball", x, 0.55)

# --- capsules ---
d = 0.4  # a capsule caught: a soft pop and a bright two-note chime up
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(400, 900, 0.05, 0.02))
mix(x, n(0.02), 0.4 * synth(1318.5, 0.12, "square", 0.002, 0.05, 3, 6000))
mix(x, n(0.08), add(0.4 * synth(1975.5, 0.3, "square", 0.002, 0.1, 3, 7000), 0.3 * glint(3951.1, 0.3, 0.1)))
save("capsule", x, 0.45)

d = 0.2  # a laser shot: a fast falling zap with a buzzy edge
x = 0.7 * synth(np.geomspace(3200, 600, n(d)), d, "saw", 0.001, 0.06, 2.5, 7000, 0.02)
mix(x, 0, 0.3 * tick(0.03, 3000, 12000, 0.008))
save("laser", x, 0.35)

d = 0.55  # the paddle widens: a stretchy rising sweep with a shimmer opening up
x = 0.5 * synth(np.geomspace(220, 660, n(d)), d, "saw", 0.01, 0.3, 1.8, 3000, 0.02)
x += 0.2 * lp(s.noise(d), np.geomspace(500, 8000, n(d))) * env(n(d), 0.1, 0.2, 2)
mix(x, n(0.3), 0.25 * glint(1760.0, 0.25, 0.08))
save("grow", x, 0.45)

d = 0.45  # the paddle shrinks: the same stretch reversed, squeezed down
x = 0.5 * synth(np.geomspace(660, 200, n(d)), d, "saw", 0.005, 0.25, 1.8, 2500, 0.02)
x += 0.15 * lp(s.noise(d), np.geomspace(6000, 400, n(d))) * env(n(d), 0.01, 0.15, 2)
save("shrink", x, 0.42)

d = 0.3  # the ball held: a soft magnetic clamp, a low blip and a hum that settles
x = 0.6 * thump(700, 350, 0.08, 0.03)
x = np.concatenate([x, np.zeros(n(d) - len(x))])
tt = t(d)
x += 0.35 * lp(tone(np.full(n(d), 220.0), "square", 5), 1500) * env(n(d), 0.01, 0.1, 2) * (1 + 0.3 * np.sin(2 * np.pi * 30 * tt))
save("catch", x, 0.42)

d = 0.7  # multi-ball: three quick glassy pings splitting apart, each a fifth higher, with a sparkle
x = np.zeros(n(d))
for i, f in enumerate((1318.5, 1975.5, 2960.0)):
    mix(x, n(i * 0.07), add(0.4 * glass(f, 0.5, 0.15), 0.2 * synth(f / 2, 0.15, "square", 0.001, 0.05, 3, 5000)))
for k in range(5):
    mix(x, n(0.2 + k * 0.05), 0.1 * glint(s.rng.choice((3520.0, 4186.0, 4698.6)), 0.25, 0.06))
save("multiball", x, 0.45)

d = 0.9  # slow: a lazy falling glide on a soft pad, like time easing off
tt = t(d)
x = 0.5 * synth(np.geomspace(988, 494, n(d)) * (1 + 0.01 * np.sin(2 * np.pi * 5 * tt)), d, "square", 0.02, 0.5, 1.5, 2200, 0.02)
x += 0.3 * synth(np.geomspace(740, 370, n(d)), d, "sine", 0.03, 0.5, 1.5, 4000)
save("slow", x, 0.42)

d = 1.3  # an extra life: a bright major run up on plucks, landing on a shimmering glass chord
x = np.zeros(n(d))
for i, f in enumerate((783.99, 987.77, 1174.7, 1568.0, 1975.5)):
    mix(x, n(i * 0.06), 0.4 * synth(f, 0.25, "square", 0.002, 0.08, 3, 6000))
for f in (783.99, 1174.7, 1568.0, 1975.5):
    mix(x, n(0.32), add(0.16 * synth(f, 0.95, "saw", 0.01, 0.5, 1.5, 5000, 0.012), 0.1 * glass(f * 2, 0.9, 0.3)))
for k in range(6):
    mix(x, n(0.34 + k * 0.08), 0.12 * glint(s.rng.choice((3136.0, 3951.1, 4698.6)), 0.35, 0.12))
save("extra_life", x, 0.55)

# --- drones ---
d = 0.45  # a drone popped: a crunchy burst, a springing blip and a spray of glass bits
x = np.zeros(n(d))
mix(x, 0, 0.7 * lp(s.noise(0.2), np.geomspace(8000, 600, n(0.2))) * env(n(0.2), 0.0005, 0.05, 3))
mix(x, 0, 0.7 * thump(220, 60, 0.12, 0.04))
mix(x, n(0.02), 0.4 * synth(np.geomspace(500, 1600, n(0.1)), 0.1, "square", 0.001, 0.05, 2, 5000))
for k in range(4):
    mix(x, n(0.05 + k * 0.04), 0.12 * glint(s.rng.choice((2637.0, 3136.0, 3520.0)), 0.2, 0.05))
save("drone_pop", x, 0.5)

# --- stages ---
d = 2.1  # ready: a crystal arpeggio winds up over rising air, two stabs, a bright chord with a sparkle
x = np.zeros(n(d))
arp = (293.7, 370.0, 440.0, 587.3, 740.0, 880.0, 1174.7, 1480.0)
for i in range(12):
    f = arp[i % 8] * (2 if i >= 8 else 1)
    mix(x, n(i * 0.09), add(0.25 * synth(f, 0.14, "square", 0.002, 0.05, 3, 1500 + 400 * i), 0.15 * glass(f * 2, 0.2, 0.05)))
mix(x, 0, 0.22 * lp(s.noise(1.1), np.geomspace(200, 7000, n(1.1))) * np.clip(t(1.1) / 1.1, 0, 1) ** 2)
for st, chord in ((1.1, (392.0, 493.9, 587.3)), (1.28, (440.0, 554.4, 659.3))):
    for f in chord:
        mix(x, n(st), 0.22 * synth(f, 0.16, "saw", 0.002, 0.06, 3, 4500))
    mix(x, n(st), 0.5 * thump(150, 50, 0.12, 0.03))
for f in (293.7, 587.3, 740.0, 880.0, 1174.7):
    mix(x, n(1.46), 0.16 * synth(f, 0.62, "saw", 0.004, 0.32, 1.6, 5000, 0.012))
mix(x, n(1.46), 0.7 * thump(160, 45, 0.18, 0.05))
for k, f in enumerate((2349.3, 2960.0, 3520.0)):
    mix(x, n(1.5 + k * 0.05), 0.25 * glass(f, 0.55, 0.16))
save("ready", x, 0.6)

d = 2.6  # stage clear: a sparkling glass climb, a bouncy tag, a big major chord that rings and glitters
x = np.zeros(n(d))
for i, f in enumerate((587.3, 740.0, 880.0, 1174.7, 1480.0, 1760.0, 2349.3)):
    mix(x, n(i * 0.05), add(0.22 * synth(f, 0.18, "square", 0.002, 0.06, 3, 6000), 0.15 * glass(f * 2, 0.3, 0.08)))
for st, f in ((0.42, 1760.0), (0.57, 1975.5), (0.72, 2349.3)):
    mix(x, n(st), 0.32 * synth(f, 0.16, "saw", 0.002, 0.07, 3, 5000))
    mix(x, n(st), 0.4 * thump(140, 55, 0.1, 0.025))
for f in (293.7, 587.3, 740.0, 880.0, 1174.7, 1480.0):
    mix(x, n(0.9), 0.14 * synth(f, 1.6, "saw", 0.008, 0.9, 1.4, 5500, 0.014))
mix(x, n(0.9), 0.8 * thump(170, 45, 0.25, 0.07))
for k in range(12):
    mix(x, n(0.92 + k * 0.08), 0.1 * glass(s.rng.choice((2349.3, 2960.0, 3520.0, 4698.6)), 0.5, 0.15))
save("stage_clear", x, 0.6)

d = 1.3  # the break-out door: a deep whoosh sweeping past, a rising tone pulled through it, a glass flash
tt = t(d)
shape = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.5
x = 0.6 * lp(s.noise(d), np.geomspace(300, 9000, n(d)) * (0.3 + shape)) * shape
x += 0.35 * synth(np.geomspace(110, 1760, n(d)), d, "saw", 0.3, 0.6, 1.2, 3000, 0.03) * shape
mix(x, n(0.8), 0.3 * glass(2637.0, 0.5, 0.15))
save("warp", x, 0.5)

d = 2.6  # game over: a slow minor descent on a soft saw, a sad glass echo, a low final chord fading out
x = np.zeros(n(d))
for i, f in enumerate((659.3, 587.3, 523.3, 493.9)):
    mix(x, n(i * 0.32), 0.35 * synth(f, 0.5, "saw", 0.01, 0.25, 2, 2400, 0.014))
    mix(x, n(i * 0.32 + 0.16), 0.12 * glass(f * 2, 0.4, 0.12))
for f in (110.0, 220.0, 261.6, 329.6, 440.0):
    mix(x, n(1.3), 0.14 * synth(f, 1.3, "saw", 0.02, 0.7, 1.4, 1800, 0.016))
mix(x, n(1.3), 0.5 * thump(120, 40, 0.3, 0.1))
save("game_over", x, 0.55)
