#!/usr/bin/env python3
"""Sound effects for game 25 (Nova Wardens), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from the arcade game (none of its sounds, not its march notes): a
night-sky defence played on analogue-style synths: filtered saws, sine subs, FM bells, plasma crackle and noise.
The march beat: step_0 .. step_3 are four short deep pulses, G2, E flat 2, C2, G1 (down a C minor arpeggio, so they
sit on the music's C minor pad): a sine sub with a click, a saw body through a closing low-pass and a faint fifth
on top. Each is 0.2 s and dry at its end, so the game can play them as fast as the thinning fleet asks.
The hits: each invader kind has its own voice: the squid a glassy high pop with a chirp, the crab a metallic crunch
(struck-plate modes and grit), the octopus a wet low burst (a falling blob and a squelch).
ufo_loop is a seamless 1.2 s loop (every partial and every modulation completes whole cycles in it): a low throbbing
hum under a slow glassy warble, played while the mothership crosses.
No voices anywhere.
Usage: python3 tools/audio/novawardens_sfx.py [out_dir]   (default: godot/games/novawardens/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/novawardens/audio/sfx", seed=2525)
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
    """A tone with a (scalar or curve) frequency and the given harmonics."""
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
        ir_t = t(min(dec * 5, 0.8))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        L = len(x) + len(ir)
        y += a * np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return y


def click(sec=0.003, bright=3500):
    return lp(s.noise(sec), bright) * env(n(sec), 0.0003, sec / 3, 3)


def bandnoise(sec, lo, hi):
    return hp(lp(s.noise(sec), hi), lo)


def crackle(sec, rate=300, bright=6000):
    """Sparse random electric pops."""
    x = np.zeros(n(sec))
    k = int(rate * sec)
    for i in s.rng.integers(0, len(x) - n(0.004), k):
        x[i:i + n(0.004)] += s.rng.uniform(-1, 1) * env(n(0.004), 0.0002, 0.001, 3)
    return lp(x, bright)


def fmbell(f, sec, ratio=1.4, index=2.5, decay=0.4):
    """A glassy FM bell."""
    tt = t(sec)
    e = np.exp(-tt / decay)
    return np.sin(2 * np.pi * f * tt + index * e * np.sin(2 * np.pi * f * ratio * tt)) * e


def pad(f, sec, detune=0.006, bright=1800, attack=0.3, release=0.5):
    """A soft detuned saw pad."""
    x = saw(f * (1 - detune), sec, 16) + saw(f * (1 + detune), sec, 16) + 0.6 * saw(f / 2, sec, 12)
    e = np.clip(t(sec) / attack, 0, 1) * np.clip((sec - t(sec)) / release, 0, 1)
    return lp(x, bright) * e


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


G1, C2, Eb2, G2 = m2f(31), m2f(36), m2f(39), m2f(43)
C4, Eb4, G4, Bb4, C5, D5, Eb5, G5, C6, Eb6, G6, C7 = (m2f(m) for m in (60, 63, 67, 70, 72, 74, 75, 79, 84, 87, 91, 96))

# ------------------------------------------------------------------ the march beat

for i, f in enumerate((G2, Eb2, C2, G1)):
    d = 0.2
    tt = t(d)
    fv = f * (1 + 0.25 * np.exp(-tt / 0.012))            # a small pitch drop on the attack: a punch
    sub = osc(fv, d) * env(n(d), 0.002, 0.075, 2.2)
    body = lp(saw(fv, d, 20), 180 + 1400 * np.exp(-tt / 0.03)) * env(n(d), 0.002, 0.05, 2.5)
    fifth = osc(fv * 3, d) * env(n(d), 0.002, 0.03, 3)
    x = 1.0 * sub + 0.45 * body + 0.08 * fifth
    mix(x, 0, 0.25 * click(0.004, 2500))
    x = drive(x, 1.6)
    x *= np.clip((d - tt) / 0.03, 0, 1)                   # dry at its end
    s.save("step_%d" % i, x, 0.8)

# ------------------------------------------------------------------ the cannon

d = 0.32  # shot: a charged bolt: a bright falling zap, a pulse of air and a soft sub kick
x = np.zeros(n(d))
z = saw(curve([(0, 2600), (0.05, 1300), (0.2, 520)], d), d, 10) * env(n(d), 0.001, 0.07, 2.5)
mix(x, 0, 0.35 * lp(z, curve([(0, 9000), (0.2, 1500)], d)))
mix(x, 0, 0.3 * osc(curve([(0, 3400), (0.08, 1800)], 0.1), 0.1, ((1, 1.0), (2, 0.3))) * env(n(0.1), 0.001, 0.025, 3))
mix(x, 0, 0.2 * lp(bandnoise(0.12, 1200, 4000), 5000) * env(n(0.12), 0.001, 0.03, 3))
mix(x, 0, 0.35 * thump(180, 60, 0.1, 0.03))
save("shot", x, 0.5)

# ------------------------------------------------------------------ invader hits

d = 0.45  # hit_squid: a glassy high pop, a chirp up and a sparkle falling away
x = np.zeros(n(d))
mix(x, 0, 0.5 * bandnoise(0.06, 2000, 9000) * env(n(0.06), 0.0005, 0.015, 3))
mix(x, 0, 0.35 * osc(curve([(0, 900), (0.07, 2600)], 0.09), 0.09, ((1, 1.0), (2, 0.4))) * env(n(0.09), 0.001, 0.04, 2))
mix(x, n(0.03), 0.3 * fmbell(G6, 0.35, 2.1, 3.0, 0.08), 0.2 * fmbell(C7, 0.3, 1.7, 2.0, 0.06))
mix(x, 0, 0.25 * thump(400, 120, 0.08, 0.02))
save("hit_squid", x, 0.55)

d = 0.5  # hit_crab: a metallic crunch: struck plates ringing, grit and a low knock
x = np.zeros(n(d))
ex = np.r_[click(0.006, 6000), np.zeros(n(d) - n(0.006))]
mix(x, 0, 0.9 * resonate(ex, ((743, 0.05, 1.0), (1187, 0.04, 0.7), (1931, 0.03, 0.5), (2767, 0.02, 0.35))))
mix(x, 0, 0.4 * bandnoise(0.15, 800, 5000) * env(n(0.15), 0.001, 0.04, 3) * (1 + np.sign(np.sin(2 * np.pi * 70 * t(0.15)))) / 2)
mix(x, 0, 0.45 * thump(220, 70, 0.12, 0.035))
mix(x, n(0.01), 0.15 * crackle(0.2, 250, 5000) * env(n(0.2), 0.001, 0.08, 2))
save("hit_crab", drive(x, 1.5), 0.55)

d = 0.55  # hit_octopus: a wet low burst: a falling blob, a squelch of filtered noise, bubbles
x = np.zeros(n(d))
mix(x, 0, 0.6 * osc(curve([(0, 320), (0.2, 70)], 0.3), 0.3, ((1, 1.0), (2, 0.35), (3, 0.1))) * env(n(0.3), 0.002, 0.1, 2))
sq_n = lp(lp(s.noise(0.25), curve([(0, 2500), (0.05, 500), (0.25, 220)], 0.25)), 1800) * env(n(0.25), 0.001, 0.07, 2)
mix(x, 0, 0.6 * sq_n)
for k, st in enumerate((0.07, 0.12, 0.2)):
    mix(x, n(st), 0.12 * osc(curve([(0, 500 + 200 * k), (0.04, 900 + 300 * k)], 0.05), 0.05) * env(n(0.05), 0.002, 0.015, 2))
mix(x, 0, 0.5 * thump(140, 45, 0.18, 0.05))
save("hit_octopus", x, 0.6)

# ------------------------------------------------------------------ bombs and shields

d = 0.2  # bomb_drop: a small falling bloop (quiet, it plays often)
x = np.zeros(n(d))
mix(x, 0, osc(curve([(0, 700), (0.15, 260)], d), d, ((1, 1.0), (2, 0.25))) * env(n(d), 0.003, 0.05, 2))
mix(x, 0, 0.2 * bandnoise(0.05, 1000, 4000) * env(n(0.05), 0.001, 0.015, 3))
save("bomb_drop", lp(x, 3000), 0.3)

d = 0.35  # bomb_ground: a fizzling thud into the ground
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(160, 45, 0.15, 0.04))
mix(x, 0, 0.35 * lp(s.noise(0.3), curve([(0, 3000), (0.3, 400)], 0.3)) * env(n(0.3), 0.001, 0.09, 2))
mix(x, n(0.02), 0.12 * crackle(0.25, 180, 2500) * env(n(0.25), 0.001, 0.1, 2))
save("bomb_ground", x, 0.45)

d = 0.25  # shield_hit: the barrier crumbles: grains of grit, a dull chip
x = np.zeros(n(d))
for k in range(9):
    st = 0.004 + 0.018 * k + s.rng.uniform(0, 0.01)
    g = lp(bandnoise(0.015, 700, 3000), 4000) * env(n(0.015), 0.0005, 0.004, 3)
    mix(x, n(st), (0.6 - 0.05 * k) * g)
mix(x, 0, 0.35 * thump(300, 110, 0.06, 0.015))
save("shield_hit", x, 0.4)

# ------------------------------------------------------------------ the player

d = 1.6  # player_die: the tank bursts: a crack, electric sputter, a power-down whine and a low boom
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(120, 30, 0.6, 0.18))
mix(x, 0, 0.7 * lp(s.noise(1.0), curve([(0, 5000), (0.1, 2000), (1.0, 250)], 1.0)) * env(n(1.0), 0.001, 0.3, 2))
mix(x, n(0.02), 0.3 * crackle(1.1, 220, 4000) * curve([(0, 1), (0.8, 0.6), (1.1, 0)], 1.1))
whine = saw(curve([(0, 900), (1.2, 70)], 1.3), 1.3, 12) * curve([(0, 0), (0.05, 1), (1.0, 0.6), (1.3, 0)], 1.3)
mix(x, n(0.05), 0.2 * lp(whine, 2500))
sput = sq(55, 0.6) * (np.sin(2 * np.pi * 13 * t(0.6)) > 0.2) * env(n(0.6), 0.01, 0.25, 1.5)
mix(x, n(0.5), 0.15 * lp(sput, 900))
save("player_die", drive(x, 1.4), 0.7)

d = 1.5  # extra_life: a rising FM-bell arpeggio up C minor to a bright shimmer
x = np.zeros(n(d))
for k, f in enumerate((C5, Eb5, G5, C6, Eb6, G6)):
    mix(x, n(k * 0.07), 0.3 * fmbell(f, 0.8, 2.0, 1.5, 0.25))
mix(x, n(0.42), 0.18 * pad(C5, 0.9, 0.004, 5000, 0.02, 0.6), 0.14 * pad(G5, 0.9, 0.004, 5000, 0.02, 0.6))
mix(x, n(0.42), 0.06 * bandnoise(0.8, 6000, 12000) * curve([(0, 0), (0.1, 1), (0.8, 0)], 0.8))
save("extra_life", x, 0.5)

# ------------------------------------------------------------------ the mothership

d = 1.2  # ufo_loop: seamless. 1.2 s: frequencies are multiples of 1/1.2 Hz (every partial completes whole cycles)
tt = t(d)
base = 1 / d
hum = (np.sin(2 * np.pi * 90 * base * tt) + 0.5 * np.sin(2 * np.pi * 180 * base * tt)
       + 0.25 * np.sin(2 * np.pi * 271 * base * tt))                                   # 75 Hz + detuned partials
throb = 0.65 + 0.35 * np.sin(2 * np.pi * 8 * base * tt)                                # ~6.7 Hz throb
war = 2 * np.pi * 540 * base * tt + 6.0 * np.sin(2 * np.pi * 3 * base * tt)           # a 450 Hz tone gliding
warble = np.sin(war) + 0.3 * np.sin(2 * war)
shimmer = np.sin(2 * np.pi * 1500 * base * tt + 2 * np.sin(2 * np.pi * 36 * base * tt)) * (0.5 + 0.5 * np.sin(2 * np.pi * 2 * base * tt))
x = 0.6 * hum * throb + 0.22 * warble * (0.7 + 0.3 * np.sin(2 * np.pi * 4 * base * tt)) + 0.05 * shimmer
s.save("ufo_loop", x, 0.45, fade=False)

d = 1.4  # ufo_hit: the saucer bursts: a bright crack, a falling cascade of bells (the score), a deep boom
x = np.zeros(n(d))
mix(x, 0, 0.7 * thump(200, 35, 0.5, 0.15))
mix(x, 0, 0.6 * lp(s.noise(0.6), curve([(0, 6000), (0.6, 500)], 0.6)) * env(n(0.6), 0.001, 0.15, 2))
for k, f in enumerate((G6, Eb6, C6, G5, Eb5, C5)):
    mix(x, n(0.06 + k * 0.06), 0.25 * fmbell(f, 0.6, 1.4, 2.0, 0.2))
mix(x, n(0.02), 0.2 * crackle(0.6, 200, 4000) * env(n(0.6), 0.001, 0.2, 2))
save("ufo_hit", x, 0.65)

# ------------------------------------------------------------------ the waves

d = 2.4  # wave_clear: a proud minor-to-major lift: C minor pulses, then an A flat to a bright C major chord
x = np.zeros(n(d))
for k, f in enumerate((C4, Eb4, G4, C5)):
    mix(x, n(k * 0.11), 0.25 * fmbell(f * 2, 0.5, 2.0, 1.2, 0.15), 0.15 * pad(f, 0.3, 0.004, 3000, 0.01, 0.15))
for f in (m2f(56), m2f(60), m2f(63)):   # A flat major
    mix(x, n(0.5), 0.13 * pad(f, 0.45, 0.005, 2500, 0.02, 0.2))
for f in (m2f(48), m2f(55), m2f(60), m2f(64), m2f(67), m2f(72)):   # C major, open
    mix(x, n(0.95), 0.1 * pad(f, 1.4, 0.005, 3500, 0.03, 1.0))
mix(x, n(0.95), 0.3 * fmbell(C6, 1.2, 2.0, 1.5, 0.4), 0.2 * fmbell(m2f(88), 1.2, 2.0, 1.2, 0.4))
mix(x, n(0.95), 0.4 * thump(110, 40, 0.3, 0.1))
save("wave_clear", x, 0.6)

d = 3.4  # game_over: the defence falls: a slow C minor descent on a dark pad, a Db shadow, the last pulse
x = np.zeros(n(d))
for k, f in enumerate((G4, Eb4, C4, m2f(55))):
    mix(x, n(k * 0.4), 0.28 * fmbell(f, 0.9, 1.4, 1.5, 0.35), 0.14 * pad(f / 2, 0.6, 0.006, 1500, 0.05, 0.3))
for f in (m2f(37), m2f(49), m2f(53), m2f(56)):   # D flat
    mix(x, n(1.6), 0.13 * pad(f, 0.8, 0.006, 1300, 0.1, 0.4))
for f in (m2f(36), m2f(48), m2f(51), m2f(55)):   # C minor, low
    mix(x, n(2.25), 0.14 * pad(f, 1.1, 0.006, 1100, 0.1, 0.9))
mix(x, n(2.25), 0.5 * thump(70, 30, 0.6, 0.25))
save("game_over", lp(x, 6000), 0.6)

d = 3.2  # land: they have landed: a low cluster swelling (C, D flat, G flat), a rumble, a slam, a bleak ring
x = np.zeros(n(d))
sw = curve([(0, 0), (1.6, 1), (1.7, 0.8), (3.2, 0)], d)
for f in (m2f(24), m2f(36), m2f(37), m2f(42), m2f(48)):
    mix(x, 0, 0.14 * lp(saw(f * curve([(0, 1), (3.2, 0.97)], d), d, 14), curve([(0, 200), (1.6, 1600), (3.2, 300)], d)) * sw)
mix(x, 0, 0.3 * lp(s.noise(d), 180) * sw)
mix(x, n(1.6), 1.0 * thump(90, 25, 1.0, 0.35), 0.5 * lp(s.noise(0.6), 1500) * env(n(0.6), 0.001, 0.12, 2))
mix(x, n(1.65), 0.2 * fmbell(m2f(66), 1.4, 1.41, 3.0, 0.5), 0.15 * fmbell(m2f(60), 1.4, 1.41, 3.0, 0.5))
save("land", drive(x, 1.3), 0.75)
