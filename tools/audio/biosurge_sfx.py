#!/usr/bin/env python3
"""Sound effects for game 34 (Biosurge), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any game: a chrome-and-teal fighter flying through living caverns.
The ship's sounds are clean synth (sine and saw sweeps, filtered noise, FM shimmer); the creatures' are wet and
organic (filtered-noise squelches with fast formant sweeps, bubbly pitch blips, resonant chitin knocks). The jingles
sit in E minor, the key of tools/audio/biosurge_music.py.
- shoot is short and quiet enough to repeat every few frames; credit is one pling (E7) the game may pitch per pickup
  (pitch_scale = 2 ** (semitones / 12)).
- laser_loop is 1.2 s and seamless (its noise is cross-faded end into start, every modulation completes whole cycles),
  mastered at a steady level so the game can hold it while the beam fires.
No voices anywhere.
Usage: python3 tools/audio/biosurge_sfx.py [out_dir]   (default: godot/games/biosurge/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/biosurge/audio/sfx", seed=3434)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, *bs):
    """Adds sounds (of any lengths) into x from sample `start`."""
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


def synth_lead(f, sec, attack=0.01, release=0.12, bright=4000, detune=0.004):
    """Two detuned saws through a filter that opens on the attack: a bright synth voice."""
    tt = t(sec)
    x = saw(f * (1 - detune), sec, 22) + saw(f * (1 + detune), sec, 22)
    cut = 500 + bright * (1 - np.exp(-tt / 0.04)) * (0.7 + 0.3 * np.exp(-tt / 0.25))
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
    L = n(sec)
    F = min(n(fade), len(x) - L)
    y = x[:L].copy()
    a = np.linspace(0, np.pi / 2, F)
    y[:F] = y[:F] * np.sin(a) + x[L:L + F] * np.cos(a)
    return y


def squelch(sec, f0=2400, f1=300, q=0.5, level=1.0):
    """A wet squelch: noise through a falling formant (a band that sweeps down fast), slightly gurgled."""
    tt = t(sec)
    fc = curve([(0, f0), (sec * 0.35, (f0 * f1) ** 0.5), (sec, f1)], sec)
    gur = 1 + 0.35 * np.sin(2 * np.pi * 38 * tt)
    x = s.noise(sec)
    y = lp(x, fc * gur * (1 + q))
    y = y - lp(y, fc * gur * (1 - q * 0.8))
    return level * y / (np.max(np.abs(y)) + 1e-9) * env(n(sec), 0.002, sec * 0.3, 2.5)


def bubble(f0, f1, sec, level=1.0):
    """A bubble pop: a sine sweeping up fast, a short decay."""
    fv = curve([(0, f0), (sec, f1)], sec)
    return level * osc(fv, sec) * env(n(sec), 0.001, sec * 0.35, 2.5)


def crackle(sec, rate, bright=7000, size=0.003):
    """Random tiny pops of filtered noise, `rate` per second."""
    x = np.zeros(n(sec))
    for i in s.rng.integers(0, max(1, len(x) - n(size)), int(rate * sec)):
        m = n(size * s.rng.uniform(0.4, 1.4))
        x[i:i + m] += s.rng.uniform(-1, 1) * s.rng.uniform(0.3, 1.0) * env(m, 0.0002, size / 4, 3)[:len(x) - i]
    return lp(x, bright)


def splats(x, start, sec, count, level=0.3):
    """Wet gobbets landing: little squelches and bubble pops scattered over `sec`, thinning out."""
    for k in range(count):
        u = (k / count) ** 1.6
        st = start + sec * u + s.rng.uniform(0, 0.02)
        ln = s.rng.uniform(0.04, 0.09)
        mix(x, n(st), level * (1 - 0.6 * u) * squelch(ln, s.rng.uniform(1500, 3500), s.rng.uniform(250, 600), 0.4))
        if k % 3 == 0:
            f = s.rng.uniform(300, 700)
            mix(x, n(st), 0.5 * level * (1 - 0.6 * u) * bubble(f, f * 2.2, 0.05))


def boom(x, start, size=1.0, level=1.0, pitch=1.0):
    """An explosion: a low thump, a burst of noise closing down, a rumble, a wet crackle of debris."""
    mix(x, n(start), level * 0.9 * thump(140 * pitch, 32, 0.6 * size, 0.16 * size))
    nb = 0.5 * size
    mix(x, n(start), level * 0.7 * lp(s.noise(nb), curve([(0, 6000), (nb, 300)], nb)) * env(n(nb), 0.001,
                                                                                          0.08 * size, 3))
    rb = 1.2 * size
    mix(x, n(start), level * 0.5 * lp(lp(s.noise(rb), 180), 140) * 6 * curve([(0, 0), (0.03, 1), (rb, 0)], rb))
    cs = 0.7 * size
    mix(x, n(start + 0.02), level * 0.25 * crackle(cs, 140, 5000, 0.004) * curve([(0, 1), (cs, 0)], cs))


# ------------------------------------------------------------------ the ship's guns

d = 0.14  # shoot: a tight, bright pulse: a fast falling chirp, a click, a short low tick of body
x = np.zeros(n(d))
fv = curve([(0, 2600), (0.02, 1500), (0.09, 620)], 0.1)
mix(x, 0, 0.42 * osc(fv, 0.1, ((1, 1.0), (2, 0.25), (3, 0.08))) * env(n(0.1), 0.001, 0.03, 2.4))
mix(x, 0, 0.16 * lp(sq(fv * 0.5, 0.1, 7), 3500) * env(n(0.1), 0.001, 0.02, 2.5))
mix(x, 0, 0.35 * click(0.004, 7000))
mix(x, 0, 0.3 * thump(220, 110, 0.05, 0.012))
save("shoot", x, 0.42)

d = 0.45  # shoot_big: a heavy charged blast: a saw dive through a closing filter, a thump, a hiss
x = np.zeros(n(d))
fv = curve([(0, 1400), (0.05, 600), (0.32, 110)], 0.34)
mix(x, 0, 0.35 * lp(saw(fv, 0.34, 18), curve([(0, 7000), (0.34, 600)], 0.34)) * env(n(0.34), 0.002, 0.1, 2.2))
mix(x, 0, 0.3 * osc(fv * 0.5, 0.34, ((1, 1.0), (2, 0.3))) * env(n(0.34), 0.002, 0.12, 2.2))
mix(x, 0, 0.75 * thump(170, 45, 0.3, 0.07))
mix(x, 0, 0.3 * bandnoise(0.25, 1500, 9000) * env(n(0.25), 0.001, 0.05, 3))
save("shoot_big", drive(x, 1.5), 0.55)

d = 0.6  # homing: a missile away: a pop, a hissing whoosh rising, a little seeker chirp
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(300, 120, 0.06, 0.015), 0.3 * click(0.004, 5000))
wh = bandnoise(0.55, curve([(0, 500), (0.55, 3500)], 0.55), curve([(0, 2500), (0.55, 10000)], 0.55))
mix(x, n(0.01), 0.45 * wh * curve([(0, 0), (0.06, 1), (0.25, 0.6), (0.55, 0)], 0.55))
for k in range(3):
    mix(x, n(0.12 + 0.07 * k), 0.12 * osc(curve([(0, 1800 + 300 * k), (0.04, 2600 + 300 * k)], 0.05), 0.05)
        * env(n(0.05), 0.002, 0.015, 2))
save("homing", x, 0.45)


def beam(sec):
    """The laser hum: detuned saws on E3 and B3 through a wobbling filter, a high whine, a fizz, all in whole
    cycles of 1.2 s."""
    tt = t(sec)
    base = 1 / 1.2
    wob = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * base * tt)
    tone = saw(m2f(52) * (1 + 0.002 * np.sin(2 * np.pi * 4 * base * tt)), sec, 20) + 0.7 * saw(m2f(59) * 1.003, sec,
                                                                                               20)
    tone = lp(tone, 900 + 1400 * wob)
    whine = osc(m2f(88) * (1 + 0.006 * np.sin(2 * np.pi * 7 * base * tt)), sec, ((1, 1.0), (2, 0.2)))
    fizz = bandnoise(sec, 3000, 9000) * (0.7 + 0.3 * np.sin(2 * np.pi * 12 * base * tt))
    sub = osc(m2f(40), sec) * 0.6
    return 0.35 * tone / (np.max(np.abs(tone)) + 1e-9) + 0.06 * whine + 0.08 * fizz + 0.15 * sub


s.save("laser_loop", loop(beam, 1.2, 0.2), 0.42, fade=False)

# ------------------------------------------------------------------ creatures

d = 0.32  # enemy_shoot: a creature spits a spore: a gulp, a rising wet blip, a hiss of the orb leaving
x = np.zeros(n(d))
mix(x, 0, 0.5 * squelch(0.08, 1800, 400, 0.45))
mix(x, n(0.03), 0.45 * bubble(260, 820, 0.14))
mix(x, n(0.04), 0.12 * bandnoise(0.2, 2500, 7000) * curve([(0, 0), (0.03, 1), (0.2, 0)], 0.2))
mix(x, n(0.03), 0.18 * osc(curve([(0, 520), (0.15, 1100)], 0.16), 0.16, ((1, 1.0), (2, 0.4)))
    * env(n(0.16), 0.003, 0.05, 2))
save("enemy_shoot", x, 0.4)

d = 0.2  # hit: a bolt strikes flesh: a wet squelch and a hard little tick
x = np.zeros(n(d))
mix(x, 0, 0.7 * squelch(0.14, 2400, 300, 0.45))
mix(x, 0, 0.3 * bubble(200, 520, 0.05))
ex = np.r_[click(0.002, 9000), np.zeros(n(0.08))]
mix(x, 0, 0.35 * resonate(ex, ((2900, 0.012, 1.0), (4700, 0.008, 0.5))))
mix(x, 0, 0.3 * thump(260, 140, 0.04, 0.01))
save("hit", x, 0.45)

d = 0.9  # boom_small: a creature bursts: a pop, a wet splash, gobbets landing
x = np.zeros(n(d))
mix(x, 0, 0.6 * bubble(180, 520, 0.05))
boom(x, 0.01, 0.55, 0.8, 1.3)
mix(x, 0, 0.6 * squelch(0.22, 2600, 220, 0.5))
splats(x, 0.08, 0.5, 8, 0.22)
save("boom_small", drive(x, 1.4), 0.55)

d = 2.2  # boom_big: a big organism ruptures: a deep blast, a long splash, a rain of debris and bubbles
x = np.zeros(n(d))
boom(x, 0.0, 1.4, 1.0, 0.8)
boom(x, 0.12, 0.8, 0.5, 1.2)
mix(x, 0, 0.6 * squelch(0.5, 2200, 150, 0.5))
splats(x, 0.2, 1.4, 22, 0.2)
save("boom_big", drive(x, 1.6), 0.62)

d = 0.4  # boss_hit: a shot sparks off the boss's hide: a chitin knock ringing, a squelch under it
x = np.zeros(n(d))
ex = np.r_[click(0.003, 6000), np.zeros(n(d))]
mix(x, 0, 0.5 * resonate(ex, ((410, 0.06, 1.0), (930, 0.04, 0.6), (1710, 0.03, 0.35), (2650, 0.02, 0.2))))
mix(x, 0, 0.4 * squelch(0.12, 2000, 300, 0.4))
mix(x, 0, 0.5 * thump(160, 70, 0.12, 0.03))
save("boss_hit", x, 0.5)

d = 5.0  # boss_die: the boss dies: a groan falling, a chain of bursts across the body, one huge rupture, a long rumble
x = np.zeros(n(d))
gl = 2.2
fv = curve([(0, 150), (0.4, 165), (gl, 45)], gl) * (1 + 0.04 * np.sin(2 * np.pi * 6.5 * t(gl)))
groan = lp(saw(fv, gl, 26) + 0.6 * saw(fv * 1.5, gl, 18), curve([(0, 1500), (gl, 300)], gl))
mix(x, 0, 0.3 * groan * curve([(0, 0), (0.1, 1), (1.6, 0.8), (gl, 0)], gl))
for k, st in enumerate((0.0, 0.32, 0.55, 0.85, 1.05, 1.3, 1.5, 1.7)):
    boom(x, st, 0.6 + 0.05 * k, 0.45 + 0.03 * k, 1.4 - 0.06 * k)
    mix(x, n(st), 0.25 * squelch(0.15, 2800, 300, 0.5))
boom(x, 2.05, 2.2, 1.0, 0.65)
mix(x, n(2.05), 0.6 * squelch(0.7, 1800, 120, 0.5))
splats(x, 2.2, 2.2, 30, 0.16)
rb = 2.9
mix(x, n(2.05), 0.5 * lp(lp(s.noise(rb), 120), 90) * 9 * curve([(0, 0), (0.1, 1), (rb, 0)], rb))
save("boss_die", drive(x, 1.6), 0.7)

# ------------------------------------------------------------------ the player

d = 0.6  # player_hit: the hull takes a blow: an impact, an electric crackle, a short falling warning bleep
x = np.zeros(n(d))
mix(x, 0, 0.7 * thump(180, 60, 0.2, 0.05))
ex = np.r_[click(0.003, 5000), np.zeros(n(0.3))]
mix(x, 0, 0.4 * resonate(ex, ((620, 0.05, 1.0), (1480, 0.03, 0.5), (2380, 0.02, 0.3))))
mix(x, n(0.01), 0.35 * crackle(0.35, 300, 9000, 0.002) * curve([(0, 1), (0.35, 0)], 0.35))
mix(x, n(0.02), 0.18 * bandnoise(0.3, 2000, 8000) * curve([(0, 1), (0.3, 0)], 0.3))
for k in range(2):
    mix(x, n(0.12 + 0.13 * k), 0.16 * lp(sq(m2f(81 - 5 * k), 0.1, 9), 4000) * env(n(0.1), 0.002, 0.05, 2))
save("player_hit", x, 0.55)

d = 1.0  # shield: a force field raised: a shimmering rising chord, a soft whoomp, a fizz of energy settling
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(90, 160, 0.3, 0.1))
tt = t(0.9)
for k, m in enumerate((64, 71, 76, 83)):   # E B E B: open fifths
    fv = m2f(m) * curve([(0, 0.5), (0.25, 1.0), (0.9, 1.0)], 0.9) * (1 + 0.004 * np.sin(2 * np.pi * (5 + k) * tt))
    v = np.sin(2 * np.pi * np.cumsum(fv) / SR + 1.2 * np.sin(2 * np.pi * fv * 2.0 * tt) * np.exp(-tt / 0.3))
    mix(x, n(0.02 * k), 0.12 * v * curve([(0, 0), (0.2, 1), (0.9, 0)], 0.9))
mix(x, 0, 0.12 * bandnoise(0.9, curve([(0, 800), (0.4, 6000)], 0.9), 11000) * curve([(0, 0), (0.25, 1), (0.9, 0)],
                                                                                     0.9))
save("shield", x, 0.5)

d = 2.6  # die: the ship breaks up: a blast, a falling engine whine, sparks, a last pop
x = np.zeros(n(d))
boom(x, 0.0, 1.3, 1.0, 1.0)
fv = curve([(0, 1900), (0.15, 2000), (1.5, 160)], 1.6) * (1 + 0.03 * np.sin(2 * np.pi * 9 * t(1.6)))
mix(x, n(0.05), 0.2 * lp(saw(fv, 1.6, 12), 5000) * curve([(0, 0), (0.05, 1), (1.2, 0.6), (1.6, 0)], 1.6))
mix(x, n(0.05), 0.3 * crackle(1.4, 220, 9000, 0.002) * curve([(0, 1), (1.4, 0)], 1.4))
boom(x, 0.55, 0.6, 0.45, 1.3)
boom(x, 1.25, 0.9, 0.5, 0.9)
save("die", drive(x, 1.5), 0.65)

# ------------------------------------------------------------------ pickups and the shop

d = 0.5  # credit: a bubble-coin: a tiny pop, then a glassy two-partial pling on E7
x = np.zeros(n(d))
mix(x, 0, 0.25 * bubble(700, 1600, 0.03))
mix(x, n(0.012), 0.45 * fmbell(m2f(100), 0.45, 2.0, 1.1, 0.12), 0.18 * fmbell(m2f(112), 0.3, 3.0, 0.6, 0.06))
ex = np.r_[click(0.002, 9000), np.zeros(n(0.2))]
mix(x, n(0.012), 0.12 * resonate(ex, ((5274, 0.05, 1.0), (7900, 0.03, 0.4))))
save("credit", x, 0.42)

d = 1.4  # power: a power-up: a fast rising sweep, an E minor arpeggio climbing into E major, a bright gleam
x = np.zeros(n(d))
sw = saw(curve([(0, 120), (0.55, 1000)], 0.6), 0.6, 16)
mix(x, 0, 0.18 * lp(sw, curve([(0, 400), (0.6, 7000)], 0.6)) * curve([(0, 0), (0.45, 1), (0.6, 0)], 0.6))
for k, m in enumerate((64, 67, 71, 76, 79, 83, 88)):
    mix(x, n(0.04 + 0.06 * k), 0.12 * lp(sq(m2f(m), 0.16, 9), 6000) * env(n(0.16), 0.002, 0.06, 2),
        0.1 * fmbell(m2f(m + 12), 0.3, 2.0, 0.8, 0.08))
for m in (64, 68, 71, 76, 80):   # E major: the lift
    mix(x, n(0.48), 0.07 * synth_lead(m2f(m), 0.85, 0.01, 0.6, 5000))
mix(x, n(0.48), 0.4 * thump(120, 60, 0.3, 0.08))
mix(x, n(0.5), 0.2 * fmbell(m2f(100), 0.8, 2.0, 1.2, 0.25))
save("power", drive(x, 1.3), 0.55)

d = 0.8  # buy: a purchase: two quick register blips, a coin chime cascade, a soft thunk of the drawer
x = np.zeros(n(d))
for k, m in enumerate((76, 83)):
    mix(x, n(0.07 * k), 0.2 * lp(sq(m2f(m), 0.08, 9), 5000) * env(n(0.08), 0.001, 0.04, 2))
for k, m in enumerate((88, 95, 100)):
    mix(x, n(0.16 + 0.05 * k), 0.22 * fmbell(m2f(m), 0.5, 2.0, 1.0, 0.12))
mix(x, n(0.15), 0.4 * thump(200, 90, 0.1, 0.03), 0.15 * bubble(500, 1300, 0.05))
save("buy", x, 0.5)

d = 1.4  # shop_open: the shop's valve sighs open: a wet whoosh, a bubble, a quirky three-note greeting
x = np.zeros(n(d))
wh = lp(s.noise(0.6), curve([(0, 400), (0.3, 2500), (0.6, 600)], 0.6))
mix(x, 0, 0.5 * wh * curve([(0, 0), (0.25, 1), (0.6, 0)], 0.6))
mix(x, n(0.15), 0.4 * squelch(0.25, 1400, 300, 0.4))
for k, (m, st) in enumerate(((71, 0.45), (76, 0.6), (74, 0.78))):   # B E D: a sly little hello
    v = osc(m2f(m), 0.4, ((1, 1.0), (3, 0.25), (4, 0.12))) * env(n(0.4), 0.003, 0.09, 2)   # a marimba-ish knock
    mix(x, n(st), 0.3 * v, 0.12 * bubble(m2f(m) * 0.5, m2f(m), 0.06))
mix(x, n(0.78), 0.12 * fmbell(m2f(86), 0.6, 2.0, 0.8, 0.2))
save("shop_open", x, 0.5)

d = 2.6  # warning: the boss alarm: three two-tone whoops (a pulsing saw siren) over a sub pulse
x = np.zeros(n(d))
for k in range(3):
    st = k * 0.8
    sec = 0.7
    fv = curve([(0, m2f(64)), (0.3, m2f(71)), (0.36, m2f(64)), (0.66, m2f(71)), (0.7, m2f(70))], sec)
    v = lp(saw(fv, sec, 18) + saw(fv * 1.007, sec, 18), 3000) * curve([(0, 0), (0.02, 1), (0.66, 1), (0.7, 0)], sec)
    mix(x, n(st), 0.16 * v, 0.6 * thump(70, 50, 0.4, 0.15))
    mix(x, n(st), 0.08 * sq(fv * 2, sec, 9) * curve([(0, 0), (0.02, 1), (0.66, 1), (0.7, 0)], sec))
save("warning", drive(x, 1.4), 0.6)

# ------------------------------------------------------------------ jingles (E minor)

d = 2.6  # level_start: a heartbeat, a rising sweep, and the ship's motif stabbed in on Em - D - E5
x = np.zeros(n(d))
for st in (0.0, 0.22, 0.75, 0.97):   # two heartbeats
    mix(x, n(st), 0.5 * thump(70, 45, 0.25, 0.06))
sw = bandnoise(1.3, curve([(0, 300), (1.3, 6000)], 1.3), 12000)
mix(x, n(0.2), 0.25 * sw * curve([(0, 0), (1.25, 1), (1.3, 0)], 1.3))
for m, st, ln in ((64, 1.5, 0.15), (71, 1.65, 0.15), (74, 1.8, 0.12), (76, 1.95, 0.6)):
    mix(x, n(st), 0.16 * synth_lead(m2f(m), ln + 0.05, 0.005, 0.05), 0.1 * synth_lead(m2f(m - 12), ln + 0.05,
                                                                                      0.005, 0.05))
for m in (40, 52, 59, 64, 71):
    mix(x, n(1.95), 0.07 * pad(m2f(m), 0.6, 0.006, 3000, 0.01, 0.4))
mix(x, n(1.5), 0.5 * thump(100, 45, 0.3, 0.08))
mix(x, n(1.95), 0.6 * thump(110, 40, 0.4, 0.12))
save("level_start", drive(x, 1.3), 0.6)

d = 3.4  # level_clear: a bright synth fanfare: the motif climbs, lands on E major with arpeggios and a shimmer
x = np.zeros(n(d))
for m, st, ln in ((64, 0.0, 0.14), (67, 0.15, 0.14), (71, 0.3, 0.14), (76, 0.45, 0.3), (74, 0.8, 0.14),
                  (76, 0.95, 0.14), (79, 1.1, 0.14), (83, 1.25, 0.5)):
    mix(x, n(st), 0.15 * synth_lead(m2f(m), ln + 0.05, 0.005, 0.05, 5000),
        0.08 * synth_lead(m2f(m - 12), ln + 0.05, 0.005, 0.05, 3000))
for m in (40, 52, 56, 59, 64, 68, 71):   # E major, wide
    mix(x, n(1.8), 0.06 * pad(m2f(m), 1.6, 0.006, 3500, 0.02, 1.0))
for k in range(12):   # an arpeggio sparkling over it
    m = (76, 80, 83, 88)[k % 4] + (12 if k >= 8 else 0)
    mix(x, n(1.8 + 0.09 * k), 0.09 * fmbell(m2f(m), 0.4, 2.0, 1.0, 0.12))
mix(x, n(1.8), 0.6 * thump(110, 40, 0.5, 0.14))
mix(x, n(1.8), 0.12 * bandnoise(1.2, 4000, 12000) * curve([(0, 1), (1.2, 0)], 1.2))
for st in (0.0, 0.45, 0.8, 1.25):
    mix(x, n(st), 0.35 * thump(90, 50, 0.15, 0.04))
save("level_clear", drive(x, 1.3), 0.62)

d = 3.6  # game_over: a slow falling line (E D B G F# E) over a dark pad, the heartbeat slowing and stopping
x = np.zeros(n(d))
for m, st, ln in ((76, 0.0, 0.35), (74, 0.4, 0.35), (71, 0.8, 0.35), (67, 1.2, 0.35), (66, 1.6, 0.45),
                  (64, 2.1, 1.2)):
    mix(x, n(st), 0.14 * synth_lead(m2f(m - 12), ln, 0.02, 0.2, 1500), 0.08 * synth_lead(m2f(m - 24), ln, 0.02, 0.2,
                                                                                        900))
for m in (40, 47, 52, 55):
    mix(x, n(1.6), 0.06 * pad(m2f(m), 1.9, 0.005, 900, 0.3, 1.0))
for st, lvl in ((0.0, 0.5), (0.25, 0.4), (1.0, 0.45), (1.27, 0.35), (2.3, 0.35), (2.6, 0.22)):
    mix(x, n(st), lvl * thump(65, 40, 0.3, 0.07))
save("game_over", x, 0.6)
