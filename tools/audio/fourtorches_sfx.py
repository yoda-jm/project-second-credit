#!/usr/bin/env python3
"""Sound effects for game 35 (Four Torches), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any arcade game: a torch-lit dungeon crawl for 1-4 heroes, made of
filtered noise (whooshes, stone, wood, fire), sine and saw sweeps, struck-metal and struck-glass modes (blades, keys,
coins, chests), FM bells (magic) and soft synth brass and organ-like pads (jingles). The jingles sit in D minor, the
key of tools/audio/fourtorches_music.py.
- health_low is a two-tone warning (0.6 s, with silence at the end): the game repeats it every ~1 s while a hero is
  low on health. It is a one-shot, not a seamless loop.
- ghost_moan is a one-shot wail (no words, no voice: a sine and a band of noise bending in pitch).
No voices anywhere.
Usage: python3 tools/audio/fourtorches_sfx.py [out_dir]   (default: godot/games/fourtorches/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/fourtorches/audio/sfx", seed=3535)
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
    fv = np.broadcast_to(np.asarray(f, dtype=float), (n(sec),))
    ph = 2 * np.pi * np.cumsum(fv) / SR
    return sum(a * np.sin(k * ph) for k, a in harm)


def saw(f, sec, k=24):
    return osc(f, sec, [(i, 1 / i) for i in range(1, k + 1)])


def sq(f, sec, k=15):
    return osc(f, sec, [(i, 1 / i) for i in range(1, k + 1, 2)])


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude)."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 1.5))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        L = len(x) + len(ir)
        y += a * np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return y


def click(sec=0.003, bright=3500):
    return lp(s.noise(sec), bright) * env(n(sec), 0.0003, sec / 3, 3)


def strike(sec, modes, bright=6000):
    """A struck object: a click rung through its modes, `sec` long."""
    ex = np.r_[click(0.003, bright), np.zeros(n(sec) - n(0.003))]
    return resonate(ex, modes)


def bandnoise(sec, lo, hi):
    return hp(lp(s.noise(sec), hi), lo)


def fmbell(f, sec, ratio=1.4, index=2.5, decay=0.4):
    tt = t(sec)
    e = np.exp(-tt / decay)
    return np.sin(2 * np.pi * f * tt + index * e * np.sin(2 * np.pi * f * ratio * tt)) * e


def brass(f, sec, attack=0.03, release=0.15, bright=3500):
    """A soft synth brass: two detuned saws through a filter that opens on the attack."""
    tt = t(sec)
    x = saw(f * 0.997, sec, 20) + saw(f * 1.003, sec, 20)
    cut = 600 + bright * (1 - np.exp(-tt / 0.06)) * (0.75 + 0.25 * np.exp(-tt / 0.3))
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return lp(x, cut) * e


def organ(f, sec, attack=0.04, release=0.3):
    """A pipe-organ-like tone: drawbar sines (8', 4', 2 2/3', 2') with a slow chorus."""
    tt = t(sec)
    vib = 1 + 0.002 * np.sin(2 * np.pi * 5.2 * tt)
    x = osc(f * vib, sec, ((0.5, 0.5), (1, 1.0), (2, 0.55), (3, 0.3), (4, 0.22), (6, 0.08)))
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return x * e


def pad(f, sec, detune=0.006, bright=1800, attack=0.3, release=0.5):
    x = saw(f * (1 - detune), sec, 16) + saw(f * (1 + detune), sec, 16) + 0.6 * saw(f / 2, sec, 12)
    e = np.clip(t(sec) / attack, 0, 1) * np.clip((sec - t(sec)) / release, 0, 1)
    return lp(x, bright) * e


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def whoosh(sec, f0, f1, q=0.6):
    """A swept band of noise: a blade or a missile cutting the air."""
    c = curve([(0, f0), (sec, f1)], sec)
    return bandnoise(sec, c * q, c / q)


def fire(sec, rate=120):
    """A roar of flame: low rumbling noise with crackles."""
    x = lp(s.noise(sec), 900) * 0.8 + 0.3 * bandnoise(sec, 1200, 4000)
    pops = np.zeros(n(sec))
    for i in s.rng.integers(0, max(1, n(sec) - n(0.004)), int(rate * sec)):
        m = n(0.003)
        pops[i:i + m] += s.rng.uniform(-1, 1) * env(m, 0.0002, 0.001, 3)
    return x + 0.6 * lp(pops, 7000)


def glitter(x, start, sec, count, lo=3500, hi=9000, level=0.2, fall=1.5):
    """Scatters tiny high bell pings over `sec`, thinning out."""
    for k in range(count):
        u = (k / count) ** fall
        st = start + sec * u + s.rng.uniform(0, 0.02)
        f = s.rng.uniform(lo, hi)
        mix(x, n(st), level * (1 - 0.7 * u) * s.rng.uniform(0.5, 1.0)
            * fmbell(f, 0.14, s.rng.uniform(1.4, 2.8), 1.0, s.rng.uniform(0.015, 0.04)))


def coins(x, start, count, spread, level=0.3):
    """A spill of gold coins: bright metallic clinks."""
    for k in range(count):
        st = start + spread * (k / count) ** 1.3 + s.rng.uniform(0, 0.02)
        f = s.rng.uniform(2600, 4200)
        mix(x, n(st), level * s.rng.uniform(0.4, 1.0) * strike(0.25, ((f, 0.05, 1.0), (f * 1.52, 0.04, 0.6),
                                                                       (f * 2.31, 0.02, 0.35)), 9000))


# ------------------------------------------------------------------ heroes' attacks

d = 0.35  # swing: the knight's axe-hammer: a heavy whoosh, low and quick
x = np.zeros(n(d))
fv = curve([(0, 300), (0.12, 900), (0.3, 250)], 0.3)
mix(x, 0, 0.8 * bandnoise(0.3, 120, 1400) * curve([(0, 0), (0.1, 1), (0.3, 0)], 0.3))
mix(x, 0, 0.35 * whoosh(0.3, 400, 1600, 0.5) * curve([(0, 0), (0.12, 1), (0.3, 0)], 0.3))
mix(x, 0, 0.2 * osc(fv * 0.25, 0.3) * curve([(0, 0), (0.12, 1), (0.3, 0)], 0.3))
save("swing", x, 0.5)

d = 0.4  # throw: a blade thrown: a sharp metallic zing and a spinning whirr
x = np.zeros(n(d))
mix(x, 0, 0.3 * strike(0.3, ((2100, 0.05, 1.0), (3350, 0.04, 0.6), (5200, 0.02, 0.3)), 8000))
tt = t(0.35)
spin = 0.6 + 0.4 * np.sin(2 * np.pi * 26 * tt)
mix(x, 0, 0.6 * whoosh(0.35, 2500, 900, 0.55) * spin * curve([(0, 0), (0.04, 1), (0.35, 0)], 0.35))
save("throw", x, 0.5)

d = 0.7  # fireball_cast: the mage's spell: a magic rise and a whoomp of flame igniting
x = np.zeros(n(d))
mix(x, 0, 0.18 * osc(curve([(0, 300), (0.18, 1400)], 0.2), 0.2, ((1, 1.0), (2, 0.3)))
    * curve([(0, 0), (0.05, 1), (0.2, 0)], 0.2))
for k, m in enumerate((74, 77, 81)):
    mix(x, n(0.02 * k), 0.08 * fmbell(m2f(m + 12), 0.3, 2.0, 1.2, 0.08))
mix(x, n(0.12), 0.6 * fire(0.5, 80) * curve([(0, 0), (0.04, 1), (0.15, 0.6), (0.5, 0)], 0.5))
mix(x, n(0.12), 0.6 * thump(180, 60, 0.3, 0.08))
save("fireball_cast", x, 0.55)

d = 0.45  # arrow_shot: the ranger's bow: the string's twang, the arrow's hiss
x = np.zeros(n(d))
tt = t(0.3)
tw = osc(curve([(0, 190), (0.3, 175)], 0.3), 0.3, ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15)))
mix(x, 0, 0.5 * tw * env(n(0.3), 0.001, 0.06, 2.5) * (1 + 0.15 * np.sin(2 * np.pi * 30 * tt)))
mix(x, 0, 0.4 * click(0.004, 5000))
mix(x, n(0.01), 0.45 * whoosh(0.3, 4000, 1800, 0.6) * curve([(0, 0), (0.03, 1), (0.3, 0)], 0.3))
save("arrow_shot", x, 0.45)

d = 0.25  # hit_monster: a weapon lands: a meaty thud with a short crunch
x = np.zeros(n(d))
mix(x, 0, 0.9 * thump(170, 60, 0.2, 0.065))
mix(x, 0, 0.5 * lp(s.noise(0.08), curve([(0, 4000), (0.08, 600)], 0.08)) * env(n(0.08), 0.0008, 0.02, 3))
mix(x, 0, 0.15 * bandnoise(0.05, 2000, 6000) * env(n(0.05), 0.0005, 0.01, 3))
save("hit_monster", x, 0.5)

d = 0.6  # monster_die: a monster bursts into smoke: a pop, a falling growl, a dusty puff
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(240, 70, 0.2, 0.05))
fv = curve([(0, 260), (0.35, 70)], 0.35)
mix(x, 0, 0.3 * lp(saw(fv, 0.35, 12), 1200) * curve([(0, 0), (0.02, 1), (0.35, 0)], 0.35))
mix(x, n(0.05), 0.45 * lp(s.noise(0.5), curve([(0, 3000), (0.5, 400)], 0.5)) * curve([(0, 0), (0.03, 1), (0.5, 0)],
                                                                                       0.5))
save("monster_die", x, 0.5)

# ------------------------------------------------------------------ generators

d = 0.4  # gen_hit: a spawner struck: stone and bone knocking, a hollow ring
x = np.zeros(n(d))
mix(x, 0, 0.6 * strike(0.4, ((210, 0.06, 1.0), (470, 0.04, 0.7), (980, 0.03, 0.4), (1730, 0.015, 0.3)), 5000))
mix(x, 0, 0.6 * thump(130, 55, 0.15, 0.04))
mix(x, 0, 0.3 * lp(s.noise(0.1), 2500) * env(n(0.1), 0.001, 0.03, 3))
save("gen_hit", x, 0.5)

d = 1.3  # gen_break: a spawner collapses: a crack, rumbling stones tumbling down, dust
x = np.zeros(n(d))
mix(x, 0, 0.9 * thump(110, 35, 0.6, 0.18))
mix(x, 0, 0.5 * bandnoise(0.1, 800, 7000) * env(n(0.1), 0.0005, 0.03, 3))
for k in range(14):
    st = 0.05 + 0.75 * (k / 14) ** 1.2 + s.rng.uniform(0, 0.03)
    f = s.rng.uniform(250, 900)
    mix(x, n(st), 0.3 * (1 - 0.5 * k / 14) * strike(0.2, ((f, 0.03, 1.0), (f * 2.3, 0.015, 0.5)), 4000))
mix(x, n(0.05), 0.4 * lp(s.noise(1.2), curve([(0, 2500), (1.2, 300)], 1.2)) * curve([(0, 0), (0.05, 1), (1.2, 0)],
                                                                                       1.2))
save("gen_break", drive(x, 1.3), 0.6)

# ------------------------------------------------------------------ heroes hurt

d = 0.35  # hero_hurt: a blow on armour: a clank and a dull knock, a short dropping tone
x = np.zeros(n(d))
mix(x, 0, 0.35 * strike(0.3, ((620, 0.05, 1.0), (1430, 0.03, 0.6), (2950, 0.02, 0.3)), 6000))
mix(x, 0, 0.6 * thump(200, 80, 0.12, 0.03))
mix(x, n(0.02), 0.25 * lp(sq(curve([(0, 440), (0.2, 300)], 0.2), 0.2, 9), 2000) * env(n(0.2), 0.002, 0.06, 2))
save("hero_hurt", x, 0.5)

d = 2.0  # hero_die: a hero falls: a clatter of armour, a sinking minor line, the torch snuffed out
x = np.zeros(n(d))
mix(x, 0, 0.45 * strike(0.6, ((540, 0.08, 1.0), (1190, 0.05, 0.6), (2310, 0.03, 0.3)), 6000))
mix(x, n(0.12), 0.35 * strike(0.4, ((720, 0.05, 1.0), (1650, 0.03, 0.5)), 6000))
mix(x, 0, 0.6 * thump(150, 50, 0.3, 0.1))
for m, st, ln in ((62, 0.25, 0.3), (60, 0.55, 0.3), (58, 0.85, 0.3), (57, 1.15, 0.7)):
    mix(x, n(st), 0.12 * brass(m2f(m), ln, 0.02, 0.2, 1500), 0.08 * brass(m2f(m - 12), ln, 0.02, 0.2, 900))
mix(x, n(1.2), 0.3 * bandnoise(0.6, 800, 5000) * curve([(0, 0), (0.03, 1), (0.6, 0)], 0.6))   # the hiss of the torch
save("hero_die", x, 0.55)

# ------------------------------------------------------------------ dungeon

d = 1.1  # door_open: an iron-banded door grinding up: a clunk of the lock, a stony scrape with a creak, a thud
x = np.zeros(n(d))
mix(x, 0, 0.5 * strike(0.2, ((330, 0.03, 1.0), (850, 0.02, 0.5)), 5000), 0.4 * thump(160, 70, 0.1, 0.03))
tt = t(0.75)
grind = lp(s.noise(0.75), 1200) * (0.7 + 0.3 * np.sin(2 * np.pi * 11 * tt) * np.sin(2 * np.pi * 3 * tt))
mix(x, n(0.08), 0.6 * grind * curve([(0, 0), (0.08, 1), (0.6, 0.8), (0.75, 0)], 0.75))
creak = osc(curve([(0, 180), (0.4, 260), (0.6, 210)], 0.6) * (1 + 0.04 * np.sin(2 * np.pi * 37 * t(0.6))), 0.6,
            ((1, 1.0), (2, 0.6), (3, 0.4), (5, 0.2)))
mix(x, n(0.15), 0.08 * lp(creak, 2500) * curve([(0, 0), (0.1, 1), (0.6, 0)], 0.6))
mix(x, n(0.85), 0.5 * thump(120, 50, 0.2, 0.05))
save("door_open", x, 0.55)

d = 0.6  # key: a key picked up: a jingling iron ring
x = np.zeros(n(d))
for st, f in ((0.0, 2300), (0.05, 2900), (0.11, 2550)):
    mix(x, n(st), 0.35 * strike(0.45, ((f, 0.09, 1.0), (f * 1.47, 0.06, 0.6), (f * 2.09, 0.04, 0.4)), 9000))
mix(x, n(0.03), 0.15 * fmbell(m2f(86), 0.4, 3.5, 1.0, 0.12))
save("key", x, 0.45)

d = 1.0  # treasure: a chest or gold: a wooden clack, a spill of coins, a rising sparkle
x = np.zeros(n(d))
mix(x, 0, 0.4 * strike(0.2, ((280, 0.03, 1.0), (640, 0.02, 0.4)), 3500))
coins(x, 0.03, 16, 0.5, 0.35)
for k, m in enumerate((74, 77, 81, 86)):
    mix(x, n(0.08 + 0.05 * k), 0.13 * fmbell(m2f(m + 12), 0.5, 2.0, 1.2, 0.15))
save("treasure", x, 0.5)

d = 0.6  # food: a hearty bite and a warm, satisfied little two-note rise
x = np.zeros(n(d))
for st in (0.0, 0.11):
    mix(x, n(st), 0.6 * lp(s.noise(0.06), curve([(0, 5000), (0.06, 900)], 0.06)) * env(n(0.06), 0.001, 0.015, 3))
    mix(x, n(st), 0.3 * thump(220, 110, 0.05, 0.015))
for k, m in enumerate((69, 74)):
    tone = osc(m2f(m), 0.25, ((1, 1.0), (2, 0.3), (3, 0.1))) * env(n(0.25), 0.005, 0.08, 2)
    mix(x, n(0.25 + 0.09 * k), 0.25 * tone)
save("food", x, 0.6)

d = 2.2  # potion: the magic potion: a glassy uncork, an inrush, then a great boom with a shimmering wave
x = np.zeros(n(d))
mix(x, 0, 0.3 * strike(0.15, ((1800, 0.02, 1.0), (2700, 0.015, 0.5)), 8000))
mix(x, 0, 0.4 * thump(900, 300, 0.05, 0.012))
inr = bandnoise(0.45, curve([(0, 300), (0.45, 4000)], 0.45), 9000) * curve([(0, 0), (0.42, 1), (0.45, 0)], 0.45)
mix(x, n(0.05), 0.3 * inr)
mix(x, n(0.05), 0.12 * lp(saw(curve([(0, 80), (0.45, 640)], 0.45), 0.45, 16), 3000)
    * curve([(0, 0), (0.42, 1), (0.45, 0)], 0.45))
B = 0.5
mix(x, n(B), 1.0 * thump(90, 28, 1.4, 0.4))
mix(x, n(B), 0.6 * lp(s.noise(1.5), curve([(0, 6000), (0.3, 1500), (1.5, 200)], 1.5))
    * curve([(0, 1), (0.1, 0.8), (1.5, 0)], 1.5))
for m in (50, 57, 62, 65, 69, 74):   # D minor, wide, ringing out
    mix(x, n(B), 0.08 * organ(m2f(m), 1.5, 0.01, 1.2))
glitter(x, B + 0.05, 1.4, 50, 3000, 10000, 0.12)
save("potion", drive(x, 1.6), 0.7)

d = 2.0  # amulet: a rare power: a mystic rising chime figure over a swelling organ chord
x = np.zeros(n(d))
for k, m in enumerate((62, 65, 69, 74, 77, 81, 86)):
    mix(x, n(0.06 * k), 0.17 * fmbell(m2f(m + 12), 0.9, 3.01, 1.3, 0.3))
for m in (50, 62, 65, 69, 74):
    mix(x, n(0.3), 0.07 * organ(m2f(m), 1.6, 0.25, 0.8))
glitter(x, 0.45, 1.3, 30, 4000, 11000, 0.1)
save("amulet", x, 0.55)

d = 1.8  # exit: the stair down: a falling, spiralling chime cascade and a deep rumble, swallowed into the dark
x = np.zeros(n(d))
for k, m in enumerate((93, 89, 86, 81, 77, 74, 69, 65, 62, 57)):
    pan = 1.0 - 0.06 * k
    mix(x, n(0.08 * k), 0.16 * pan * fmbell(m2f(m), 0.6, 2.0, 1.2, 0.18))
sw = whoosh(1.2, 3000, 200, 0.5) * curve([(0, 0), (0.2, 1), (1.2, 0)], 1.2)
mix(x, n(0.1), 0.25 * sw)
mix(x, n(0.5), 0.5 * thump(70, 30, 1.2, 0.35))
save("exit", x, 0.55)

d = 0.6  # health_low: a warning: two pulses of a hollow alarm tone (A then D below), silence after
x = np.zeros(n(d))
for st, m in ((0.0, 69), (0.18, 62)):
    tone = sq(m2f(m), 0.16, 9)
    tone = lp(tone, 2400) * np.clip(t(0.16) / 0.006, 0, 1) * np.clip((0.16 - t(0.16)) / 0.04, 0, 1)
    mix(x, n(st), 0.35 * tone, 0.2 * osc(m2f(m) * 2, 0.16) * env(n(0.16), 0.003, 0.06, 2))
s.save("health_low", x, 0.32)   # keeps its silent tail: repeat it about every 1 s

d = 2.0  # ghost_moan: a wailing spirit: a hollow tone bending up and down through airy noise (no voice)
x = np.zeros(n(d))
tt = t(1.8)
fv = curve([(0, 220), (0.5, 330), (1.0, 300), (1.4, 350), (1.8, 200)], 1.8) * (1 + 0.012 * np.sin(2 * np.pi * 5 * tt))
moan = osc(fv, 1.8, ((1, 1.0), (2, 0.25), (3, 0.08)))
air = bandnoise(1.8, 500, 1600) * (0.6 + 0.4 * np.sin(2 * np.pi * 2.3 * tt))
shape = curve([(0, 0), (0.35, 1), (1.2, 0.8), (1.8, 0)], 1.8)
mix(x, 0, 0.35 * moan * shape, 0.25 * air * shape, 0.12 * osc(fv * 1.5, 1.8) * shape)
save("ghost_moan", lp(x, 3500), 0.36)

d = 0.6  # imp_fire: an imp hurls fire: a spitting hiss and a little whoosh
x = np.zeros(n(d))
mix(x, 0, 0.4 * bandnoise(0.08, 2000, 8000) * env(n(0.08), 0.001, 0.02, 2))
mix(x, n(0.02), 0.6 * fire(0.45, 150) * curve([(0, 0), (0.03, 1), (0.45, 0)], 0.45))
mix(x, n(0.02), 0.3 * whoosh(0.4, 600, 2500, 0.55) * curve([(0, 0), (0.08, 1), (0.4, 0)], 0.4))
save("imp_fire", x, 0.45)

d = 0.9  # join: a hero joins: a torch flares up and a bright horn call (D, A)
x = np.zeros(n(d))
mix(x, 0, 0.4 * fire(0.4, 100) * curve([(0, 0), (0.03, 1), (0.4, 0)], 0.4))
mix(x, n(0.08), 0.22 * brass(m2f(62), 0.18, 0.012, 0.06), 0.1 * brass(m2f(50), 0.18, 0.012, 0.06))
mix(x, n(0.26), 0.25 * brass(m2f(69), 0.55, 0.012, 0.3), 0.12 * brass(m2f(57), 0.55, 0.012, 0.3))
mix(x, n(0.26), 0.1 * fmbell(m2f(93), 0.5, 2.0, 1.0, 0.15))
save("join", x, 0.55)

# ------------------------------------------------------------------ jingles (D minor)

d = 2.6  # level_start: a new floor: a low drum roll and a grim brass call over an organ chord
x = np.zeros(n(d))
for k in range(12):
    mix(x, n(0.035 * k), (0.25 + 0.04 * k) * thump(90, 60, 0.2, 0.06))
mix(x, n(0.42), 0.9 * thump(85, 35, 0.9, 0.3))
for m, st, ln in ((50, 0.42, 0.22), (57, 0.66, 0.22), (62, 0.9, 0.3), (65, 1.22, 0.22), (62, 1.46, 1.0)):
    mix(x, n(st), 0.2 * brass(m2f(m + 12), ln + 0.05, 0.012, 0.1, 2500), 0.12 * brass(m2f(m), ln + 0.05, 0.012, 0.1,
                                                                                         1500))
for m in (38, 50, 57, 62, 65):
    mix(x, n(0.42), 0.06 * organ(m2f(m), 2.1, 0.08, 0.9))
mix(x, n(1.46), 0.6 * thump(85, 35, 0.8, 0.25))
save("level_start", drive(x, 1.3), 0.6)

d = 3.0  # level_clear: a victory call in D (the Picardy lift from minor to major), bells, a timpani roll
x = np.zeros(n(d))
for m, st, ln in ((62, 0.0, 0.14), (65, 0.16, 0.14), (69, 0.32, 0.14), (74, 0.48, 0.32), (72, 0.84, 0.14),
                  (74, 1.0, 0.14)):
    mix(x, n(st), 0.2 * brass(m2f(m), ln + 0.06, 0.012, 0.05), 0.1 * brass(m2f(m - 12), ln + 0.06, 0.012, 0.05))
for m in (50, 57, 62, 66, 69, 74, 78):   # D major
    mix(x, n(1.18), 0.085 * brass(m2f(m), 1.6, 0.03, 0.9, 3000), 0.04 * organ(m2f(m), 1.6, 0.03, 0.9))
for k in range(16):
    mix(x, n(0.85 + 0.02 * k), (0.15 + 0.02 * k) * thump(95, 70, 0.15, 0.05))
mix(x, n(1.18), 0.8 * thump(90, 38, 0.9, 0.3))
for k, m in enumerate((86, 90, 93, 98)):
    mix(x, n(1.18 + 0.06 * k), 0.13 * fmbell(m2f(m), 1.4, 2.0, 1.2, 0.4))
glitter(x, 1.22, 1.3, 30, 4000, 10000, 0.08)
save("level_clear", drive(x, 1.3), 0.65)

d = 3.4  # game_over: the last torch goes out: a slow falling brass line in D minor over a low organ, a final toll
x = np.zeros(n(d))
for m, st, ln in ((69, 0.0, 0.4), (65, 0.45, 0.4), (64, 0.9, 0.4), (62, 1.35, 1.4)):
    v = saw(m2f(m), ln, 14) * np.clip((ln - t(ln)) / 0.2, 0, 1) * np.clip(t(ln) / 0.03, 0, 1)
    mix(x, n(st), 0.18 * lp(v, 1500), 0.1 * lp(saw(m2f(m) / 2, ln, 10), 700) * np.clip((ln - t(ln)) / 0.2, 0, 1))
for m in (38, 50, 53, 57):
    mix(x, n(1.35), 0.07 * organ(m2f(m), 1.9, 0.15, 1.2))
mix(x, n(1.35), 0.4 * strike(2.0, ((110, 0.8, 1.0), (262, 0.5, 0.5), (415, 0.35, 0.3), (590, 0.2, 0.2)), 3000))
save("game_over", x, 0.6)
