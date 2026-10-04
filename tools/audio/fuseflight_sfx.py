#!/usr/bin/env python3
"""Sound effects for game 28 (Fuseflight), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any arcade game: a firework sprite at a night festival, made of
filtered noise (fuses, whooshes, bursts), sine and square sweeps (leaps, whistles), FM bells and struck-glass modes
(sparkles, chimes) and soft synth brass (fanfares). The jingles sit in D major, the key of
tools/audio/fuseflight_music.py.
- eat is one chime in D; the game climbs it with the chain: pitch_scale = 2 ** (2 * chain / 12) (a whole tone a step).
- glide_loop is 2.0 s and seamless (its noise is cross-faded end into start, every modulation completes whole cycles),
  mastered at a steady level so the game can fade it in and out while the sprite glides.
No voices anywhere.
Usage: python3 tools/audio/fuseflight_sfx.py [out_dir]   (default: godot/games/fuseflight/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/fuseflight/audio/sfx", seed=2828)
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
        ir_t = t(min(dec * 5, 1.2))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        L = len(x) + len(ir)
        y += a * np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return y


def click(sec=0.003, bright=3500):
    return lp(s.noise(sec), bright) * env(n(sec), 0.0003, sec / 3, 3)


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


def pad(f, sec, detune=0.006, bright=1800, attack=0.3, release=0.5):
    x = saw(f * (1 - detune), sec, 16) + saw(f * (1 + detune), sec, 16) + 0.6 * saw(f / 2, sec, 12)
    e = np.clip(t(sec) / attack, 0, 1) * np.clip((sec - t(sec)) / release, 0, 1)
    return lp(x, bright) * e


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def loop(make, sec, fade=0.25):
    """A seamless loop: renders sec + fade, then cross-fades the overhang into the start (equal power)."""
    x = make(sec + fade)
    L, F = n(sec), n(fade)
    y = x[:L].copy()
    a = np.linspace(0, np.pi / 2, F)
    y[:F] = y[:F] * np.sin(a) + x[L:L + F] * np.cos(a)
    return y


def crackle(sec, rate, bright=7000, size=0.003):
    """Fuse crackle: random tiny pops of filtered noise, `rate` per second."""
    x = np.zeros(n(sec))
    for i in s.rng.integers(0, max(1, len(x) - n(size)), int(rate * sec)):
        m = n(size * s.rng.uniform(0.4, 1.4))
        x[i:i + m] += s.rng.uniform(-1, 1) * s.rng.uniform(0.3, 1.0) * env(m, 0.0002, size / 4, 3)[:len(x) - i]
    return lp(x, bright)


def glitter(x, start, sec, count, lo=3500, hi=9000, level=0.2, fall=1.5):
    """Scatters tiny high bell pings over `sec`, thinning out."""
    for k in range(count):
        u = (k / count) ** fall
        st = start + sec * u + s.rng.uniform(0, 0.02)
        f = s.rng.uniform(lo, hi)
        mix(x, n(st), level * (1 - 0.7 * u) * s.rng.uniform(0.5, 1.0)
            * fmbell(f, 0.14, s.rng.uniform(1.4, 2.8), 1.0, s.rng.uniform(0.015, 0.04)))


def burst(x, start, size=1.0, level=1.0, pitch=1.0):
    """A firework shell bursting: a boom, a crackling spray of sparks, a sizzle settling."""
    mix(x, n(start), level * 0.9 * thump(110 * pitch, 38, 0.45 * size, 0.12 * size))
    mix(x, n(start), level * 0.5 * lp(s.noise(0.25), curve([(0, 5000), (0.25, 600)], 0.25)) * env(n(0.25), 0.001,
                                                                                                   0.06 * size, 3))
    sec = 0.9 * size
    mix(x, n(start + 0.03), level * 0.4 * crackle(sec, 260, 9000) * curve([(0, 0.2), (0.12, 1), (sec, 0)], sec))
    mix(x, n(start + 0.02), level * 0.09 * bandnoise(sec, 4000, 11000) * curve([(0, 1), (sec, 0)], sec))


# ------------------------------------------------------------------ the sprite

d = 0.42  # jump: a springy bright swoop up, a soft whoosh of the cape
x = np.zeros(n(d))
fv = curve([(0, 330), (0.16, 990), (0.3, 1180)], 0.3)
mix(x, 0, 0.45 * osc(fv, 0.3, ((1, 1.0), (2, 0.18), (3, 0.06))) * env(n(0.3), 0.004, 0.09, 2.2))
mix(x, 0, 0.18 * sq(fv * 0.5, 0.3, 7) * env(n(0.3), 0.003, 0.05, 2.5))
mix(x, 0, 0.25 * bandnoise(0.35, curve([(0, 600), (0.35, 2000)], 0.35), 4500) * curve([(0, 0), (0.05, 1), (0.35, 0)],
                                                                                        0.35))
mix(x, 0, 0.3 * thump(170, 90, 0.06, 0.015))
save("jump", x, 0.5)

d = 0.3  # land: a soft papery pat and a light thud
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(150, 55, 0.18, 0.045))
mix(x, 0, 0.4 * lp(s.noise(0.06), curve([(0, 3500), (0.06, 600)], 0.06)) * env(n(0.06), 0.0008, 0.015, 3))
ex = np.r_[click(0.002, 6000), np.zeros(n(0.12))]
mix(x, 0, 0.12 * resonate(ex, ((820, 0.02, 1.0), (1650, 0.012, 0.5))))
save("land", x, 0.45)

d = 0.4  # bump: the head knocks a platform: a hollow lantern bonk, a wobble
x = np.zeros(n(d))
ex = np.r_[click(0.003, 5000), np.zeros(n(d) - n(0.003))]
mix(x, 0, 0.7 * resonate(ex, ((310, 0.08, 1.0), (690, 0.05, 0.55), (1240, 0.03, 0.3), (2010, 0.02, 0.15))))
tt = t(0.3)
mix(x, 0, 0.3 * osc(420 * (1 - 0.25 * (1 - np.exp(-tt / 0.08))) * (1 + 0.05 * np.sin(2 * np.pi * 18 * tt)), 0.3)
    * env(n(0.3), 0.002, 0.08, 2.5))
mix(x, 0, 0.4 * thump(200, 80, 0.07, 0.02))
save("bump", x, 0.5)

# ------------------------------------------------------------------ fireworks

d = 0.7  # take: a firework collected: a pop, a quick rising whoosh, a little twinkle
x = np.zeros(n(d))
mix(x, 0, 0.7 * lp(s.noise(0.02), 4000) * env(n(0.02), 0.0005, 0.005, 3))
mix(x, 0, 0.5 * thump(420, 140, 0.06, 0.015))
wh = bandnoise(0.4, curve([(0, 800), (0.4, 5000)], 0.4), curve([(0, 2500), (0.4, 11000)], 0.4))
mix(x, n(0.01), 0.45 * wh * curve([(0, 0), (0.12, 1), (0.4, 0)], 0.4))
mix(x, n(0.02), 0.22 * osc(curve([(0, 700), (0.3, 2600)], 0.3), 0.3) * curve([(0, 0), (0.05, 1), (0.3, 0)], 0.3))
mix(x, n(0.2), 0.22 * fmbell(m2f(86), 0.5, 2.0, 1.0, 0.12), 0.15 * fmbell(m2f(93), 0.5, 2.0, 1.0, 0.1))
save("take", x, 0.55)

d = 1.2  # take_lit: the lit firework: a brighter pop, a whistle up, a sparkling D major shimmer
x = np.zeros(n(d))
mix(x, 0, 0.8 * lp(s.noise(0.02), 6000) * env(n(0.02), 0.0005, 0.005, 3))
mix(x, 0, 0.5 * thump(520, 160, 0.06, 0.015))
wh = bandnoise(0.45, curve([(0, 1200), (0.45, 7000)], 0.45), 13000)
mix(x, 0, 0.35 * wh * curve([(0, 0), (0.1, 1), (0.45, 0)], 0.45))
mix(x, 0, 0.28 * osc(curve([(0, 900), (0.32, 3300)], 0.32), 0.32, ((1, 1.0), (2, 0.1)))
    * curve([(0, 0), (0.04, 1), (0.32, 0.3)], 0.32))
for k, m in enumerate((86, 90, 93, 98, 102)):
    mix(x, n(0.12 + 0.045 * k), 0.2 * fmbell(m2f(m), 0.8, 3.01, 1.2, 0.22 + 0.03 * k))
glitter(x, 0.15, 0.85, 40, 4500, 11000, 0.14)
save("take_lit", x, 0.6)

d = 0.7  # lit: a fuse catching: a scratch and flare, then a hissing crackle that settles
x = np.zeros(n(d))
mix(x, 0, 0.5 * bandnoise(0.06, 1500, 9000) * env(n(0.06), 0.001, 0.02, 2))
flare = bandnoise(0.6, 2500, 9000) * curve([(0, 0), (0.03, 1), (0.15, 0.55), (0.6, 0)], 0.6)
mix(x, n(0.02), 0.3 * flare)
mix(x, n(0.02), 0.55 * crackle(0.6, 160, 6000) * curve([(0, 1), (0.6, 0)], 0.6))
mix(x, n(0.03), 0.1 * fmbell(m2f(93), 0.4, 2.0, 0.8, 0.08))
save("lit", x, 0.5)

# ------------------------------------------------------------------ enemies and power

d = 0.8  # spawn: an enemy drops in: a sly descending bloop through a little puff of smoke
x = np.zeros(n(d))
fv = curve([(0, 880), (0.45, 260)], 0.45) * (1 + 0.04 * np.sin(2 * np.pi * 9 * t(0.45)))
mix(x, 0, 0.35 * osc(fv, 0.45, ((1, 1.0), (2, 0.3), (3, 0.12))) * curve([(0, 0), (0.02, 1), (0.45, 0)], 0.45))
mix(x, 0, 0.18 * lp(sq(fv * 0.5, 0.45, 9), 1800) * curve([(0, 0), (0.05, 1), (0.45, 0)], 0.45))
mix(x, n(0.35), 0.25 * lp(s.noise(0.35), curve([(0, 2500), (0.35, 500)], 0.35)) * curve([(0, 0), (0.04, 1), (0.35, 0)],
                                                                                          0.35))
mix(x, n(0.36), 0.3 * thump(160, 70, 0.1, 0.03))
save("spawn", x, 0.45)

d = 0.7  # wing: an imp sprouts wings and takes off: two leathery flaps and a rising squeak
x = np.zeros(n(d))
for st in (0.0, 0.17):
    fl = lp(s.noise(0.12), 1600) * curve([(0, 0), (0.02, 1), (0.12, 0)], 0.12)
    mix(x, n(st), 0.6 * fl)
    mix(x, n(st), 0.35 * thump(130, 70, 0.08, 0.025))
fv = curve([(0, 600), (0.25, 1500), (0.32, 1350)], 0.32) * (1 + 0.03 * np.sin(2 * np.pi * 22 * t(0.32)))
mix(x, n(0.3), 0.25 * osc(fv, 0.32, ((1, 1.0), (2, 0.4), (3, 0.15))) * curve([(0, 0), (0.03, 1), (0.32, 0)], 0.32))
save("wing", x, 0.45)

d = 1.6  # power: a magical surge: a fast rising sweep through a D major glitter, a swelling chord, a gleam on top
x = np.zeros(n(d))
sw = saw(curve([(0, 110), (0.7, 880)], 0.8), 0.8, 16)
mix(x, 0, 0.18 * lp(sw, curve([(0, 400), (0.8, 6000)], 0.8)) * curve([(0, 0), (0.6, 1), (0.8, 0)], 0.8))
mix(x, 0, 0.2 * bandnoise(0.8, curve([(0, 300), (0.8, 5000)], 0.8), 12000) * curve([(0, 0), (0.75, 1), (0.8, 0)], 0.8))
for k, m in enumerate((62, 66, 69, 74, 78, 81, 86, 90)):
    mix(x, n(0.05 + 0.08 * k), 0.13 * fmbell(m2f(m), 0.6, 2.0, 1.4, 0.18))
for m in (62, 69, 74, 78, 81):
    mix(x, n(0.68), 0.09 * brass(m2f(m), 0.9, 0.04, 0.5, 3200))
mix(x, n(0.68), 0.6 * thump(130, 45, 0.4, 0.12))
glitter(x, 0.68, 0.85, 30, 5000, 12000, 0.12)
save("power", drive(x, 1.4), 0.6)

d = 1.0  # power_end: the magic winding down: a falling shimmer and a soft sigh of a chord
x = np.zeros(n(d))
for k, m in enumerate((90, 86, 81, 78, 74, 69)):
    mix(x, n(0.07 * k), 0.15 * fmbell(m2f(m), 0.5, 2.0, 1.0, 0.15))
sw = saw(curve([(0, 700), (0.9, 160)], 0.9), 0.9, 12)
mix(x, 0, 0.12 * lp(sw, curve([(0, 4000), (0.9, 500)], 0.9)) * curve([(0, 0), (0.05, 1), (0.9, 0)], 0.9))
save("power_end", x, 0.45)

d = 0.6  # eat: an enemy turned to points: a two-note glassy chime (A6 then D7) over a coin-like ping
x = np.zeros(n(d))
mix(x, 0, 0.35 * fmbell(m2f(81), 0.5, 3.5, 1.3, 0.09))
mix(x, n(0.06), 0.4 * fmbell(m2f(86), 0.5, 3.5, 1.4, 0.16), 0.15 * fmbell(m2f(98), 0.4, 2.0, 0.8, 0.1))
ex = np.r_[click(0.002, 9000), np.zeros(n(0.3))]
mix(x, 0, 0.15 * resonate(ex, ((3520, 0.04, 1.0), (5300, 0.03, 0.5))))
save("eat", x, 0.5)

d = 1.0  # letter: a bonus letter: a warm rising four-note bell figure
x = np.zeros(n(d))
for k, m in enumerate((74, 78, 81, 86)):
    mix(x, n(0.07 * k), 0.3 * fmbell(m2f(m), 0.7, 2.0, 1.2, 0.25 + 0.05 * k))
mix(x, n(0.21), 0.08 * pad(m2f(74), 0.7, 0.004, 3500, 0.05, 0.4))
save("letter", x, 0.5)

d = 2.0  # die: a fizzle (the crest burning out) and a sad whistle falling, ending in a little puff
x = np.zeros(n(d))
fz = crackle(0.8, 300, 8000) * curve([(0, 1), (0.8, 0)], 0.8)
mix(x, 0, 0.45 * fz, 0.3 * bandnoise(0.7, 3000, 9000) * curve([(0, 1), (0.7, 0)], 0.7))
mix(x, 0, 0.5 * thump(300, 120, 0.08, 0.02))
fv = curve([(0, 1760), (0.25, 1700), (1.2, 330)], 1.25) * (1 + 0.025 * np.sin(2 * np.pi * 6 * t(1.25)))
wh = osc(fv, 1.25, ((1, 1.0), (2, 0.06))) * curve([(0, 0), (0.05, 1), (0.9, 0.7), (1.25, 0)], 1.25)
mix(x, n(0.15), 0.35 * wh)
mix(x, n(1.35), 0.3 * lp(s.noise(0.4), curve([(0, 1500), (0.4, 300)], 0.4)) * curve([(0, 0), (0.03, 1), (0.4, 0)],
                                                                                         0.4))
mix(x, n(1.35), 0.35 * thump(110, 50, 0.25, 0.07))
save("die", x, 0.55)

# ------------------------------------------------------------------ jingles

d = 3.6  # stage_clear: three rockets whistle up and burst, then a brass fanfare in D with bells
x = np.zeros(n(d))
for k, (st, f0) in enumerate(((0.0, 600), (0.18, 700), (0.36, 650))):
    fv = curve([(0, f0), (0.42, f0 * 3.2)], 0.45) * (1 + 0.01 * np.sin(2 * np.pi * 7 * t(0.45)))
    mix(x, n(st), 0.14 * osc(fv, 0.45, ((1, 1.0), (2, 0.1))) * curve([(0, 0), (0.05, 1), (0.45, 0.6)], 0.45))
    mix(x, n(st), 0.1 * bandnoise(0.45, 2000, 8000) * curve([(0, 0), (0.1, 1), (0.45, 0.3)], 0.45))
    burst(x, st + 0.45, 0.9, 0.55 - 0.08 * k, 1.0 + 0.15 * k)
for m, st, ln in ((69, 0.95, 0.14), (74, 1.1, 0.14), (78, 1.25, 0.14), (81, 1.4, 0.3), (78, 1.75, 0.14), (81, 1.9, 0.14)):
    mix(x, n(st), 0.2 * brass(m2f(m), ln + 0.06, 0.012, 0.05), 0.1 * brass(m2f(m - 12), ln + 0.06, 0.012, 0.05))
for m in (50, 57, 62, 66, 69, 74, 78):   # D major, wide
    mix(x, n(2.06), 0.09 * brass(m2f(m), 1.45, 0.03, 0.8, 3000))
for k, m in enumerate((86, 90, 93, 98)):
    mix(x, n(2.06 + 0.06 * k), 0.15 * fmbell(m2f(m), 1.4, 2.0, 1.2, 0.4))
burst(x, 2.06, 1.4, 0.5, 0.9)
glitter(x, 2.1, 1.3, 40, 4000, 11000, 0.1)
save("stage_clear", drive(x, 1.3), 0.65)

d = 3.0  # game_over: the festival lights go out: a slow falling brass line (D, B, G, A... down to D) and a last pop
x = np.zeros(n(d))
for m, st, ln in ((74, 0.0, 0.35), (71, 0.38, 0.35), (67, 0.76, 0.35), (66, 1.14, 0.4), (62, 1.6, 1.1)):
    fv = m2f(m) * (curve([(0, 1), (ln * 0.7, 1), (ln, 0.97)], ln) if st > 1.5 else 1.0)
    v = saw(fv, ln, 14) * np.clip((ln - t(ln)) / 0.15, 0, 1) * np.clip(t(ln) / 0.02, 0, 1)
    mix(x, n(st), 0.2 * lp(v, 1600), 0.12 * lp(saw(fv / 2, ln, 10), 800) * np.clip((ln - t(ln)) / 0.15, 0, 1))
mix(x, n(1.6), 0.08 * pad(m2f(50), 1.2, 0.005, 900, 0.1, 0.8), 0.06 * pad(m2f(57), 1.2, 0.005, 900, 0.1, 0.8))
mix(x, n(2.55), 0.25 * thump(220, 90, 0.08, 0.02), 0.12 * crackle(0.3, 80, 5000) * curve([(0, 1), (0.3, 0)], 0.3))
save("game_over", x, 0.6)

d = 1.6  # extra_life: a bright 1-up flourish: D major arpeggio up two octaves in square bells, a sparkle
x = np.zeros(n(d))
for k, m in enumerate((74, 78, 81, 86, 90, 93, 98)):
    tone = sq(m2f(m), 0.22, 9) * env(n(0.22), 0.002, 0.08, 2)
    mix(x, n(0.06 * k), 0.13 * lp(tone, 7000), 0.12 * fmbell(m2f(m + 12), 0.3, 2.0, 0.6, 0.1))
mix(x, n(0.42), 0.25 * fmbell(m2f(98), 1.1, 3.01, 1.2, 0.35), 0.2 * fmbell(m2f(86), 1.1, 2.0, 1.0, 0.4))
glitter(x, 0.42, 0.9, 25, 5000, 11000, 0.1)
save("extra_life", x, 0.55)


# ------------------------------------------------------------------ the glide loop

def glide(sec):
    """A soft wind: band noise swaying in pitch and level (whole cycles in 2 s), a faint cloth flutter."""
    tt = t(sec)
    base = 1 / 2.0
    sway = 0.5 + 0.5 * np.sin(2 * np.pi * 1 * base * tt)
    lo = lp(lp(s.noise(sec), 700 + 300 * sway), 900)
    lo = lo / (np.max(np.abs(lo)) + 1e-9)
    hi = bandnoise(sec, 900, 2200 + 600 * sway)
    hi = hi / (np.max(np.abs(hi)) + 1e-9)
    flutter = 0.75 + 0.25 * np.sin(2 * np.pi * 13 * base * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * base * tt))
    x = (0.8 * lo * (0.8 + 0.2 * sway) + 0.14 * hi * flutter) * (0.85 + 0.15 * np.sin(2 * np.pi * 2 * base * tt))
    return lp(x, 3000)


s.save("glide_loop", loop(glide, 2.0), 0.45, fade=False)
