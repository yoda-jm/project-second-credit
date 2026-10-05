#!/usr/bin/env python3
"""Sound effects for game 33 (Bloomwand), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any arcade game: a fairy with a wand in a storybook garden, made of
FM bells and struck modes (sparkles, chimes, the hurry bell), harp-like plucked partials and a soft breathy flute tone
(jingles), sine glides (bubbles, bloops, the dizzy fall), filtered noise (steps, whooshes, the slam) and soft synth
brass (the letter fanfare). Every pitched sound sits in F major, the key of tools/audio/bloomwand_music.py.
- step is a soft 70 ms pat played on every footfall: vary it with pitch_scale = randf_range(0.92, 1.08).
- climb is a light wooden rung tick: alternate pitch_scale 1.0 and 1.06 on successive rungs.
- pop and fruit are one note each (F); the game can climb a chain of them: pitch_scale = 2 ** (step / 12) over the
  F major scale steps (0, 2, 4, 5, 7, 9, 11, 12).
- ladder_magic is about 1 s: a rising rainbow shimmer, its last bell rings while the ladder finishes growing.
No voices anywhere.
Usage: python3 tools/audio/bloomwand_sfx.py [out_dir]   (default: godot/games/bloomwand/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/bloomwand/audio/sfx", seed=3333)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, *bs):
    """Adds sounds (of any lengths) into x from `start`."""
    for b in bs:
        b = b[:max(0, len(x) - start)]
        x[start:start + len(b)] += b


def save(name, x, gain):
    """Saves a one-shot with its tail trimmed where it falls below -50 dB of the peak, a 2 ms fade-in against
    clicks."""
    w = n(0.01)
    rms = np.sqrt(np.convolve(np.asarray(x) ** 2, np.ones(w) / w, "same"))
    end = min(len(x), np.nonzero(rms > np.max(np.abs(x)) * 0.00316)[0][-1] + n(0.02))
    x = x[:end].copy()
    x[:n(0.002)] *= np.linspace(0, 1, n(0.002))
    s.save(name, x, gain)


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
        ir_t = t(min(dec * 7, 2.0))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec) * np.linspace(1, 0, len(ir_t)) ** 0.5
        L = len(x) + len(ir)
        y += a * np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return y


def click(sec=0.003, bright=3500):
    return lp(s.noise(sec), bright) * env(n(sec), 0.0003, sec / 3, 3)


def bandnoise(sec, lo, hi):
    return hp(lp(s.noise(sec), hi), lo)


def fmbell(f, sec, ratio=1.4, index=2.5, decay=0.4):
    tt = t(sec)
    e = np.exp(-tt / decay) * np.clip(tt / 0.0015, 0, 1)
    return np.sin(2 * np.pi * f * tt + index * e * np.sin(2 * np.pi * f * ratio * tt)) * e


def harp(f, sec, decay=0.6, bright=1.0):
    """A plucked string: harmonic partials, the upper ones dying faster, a soft 3 ms attack."""
    tt = t(sec)
    x = sum((bright / k) ** 1.4 * np.sin(2 * np.pi * f * k * 1.0008 ** (k - 1) * tt) * np.exp(-tt * k / decay)
            for k in range(1, 7))
    return x * np.clip(tt / 0.003, 0, 1)


def flute(f, sec, attack=0.04, release=0.1, vib=0.004):
    """A soft breathy flute: a near-sine with a little second and third harmonic, vibrato fading in, breath noise."""
    tt = t(sec)
    fv = f * (1 + vib * np.sin(2 * np.pi * 5.2 * tt) * np.clip((tt - 0.12) / 0.2, 0, 1))
    x = osc(fv, sec, ((1, 1.0), (2, 0.22), (3, 0.07)))
    breath = lp(lp(hp(s.noise(sec), f * 0.7), f * 1.6), f * 2.5)
    x += 0.5 * breath * (0.4 + 0.6 * np.exp(-tt / 0.05))
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return x * e


def brass(f, sec, attack=0.03, release=0.15, bright=3000):
    """A soft synth brass: two detuned saws through a filter that opens on the attack."""
    tt = t(sec)
    x = saw(f * 0.997, sec, 20) + saw(f * 1.003, sec, 20)
    cut = 600 + bright * (1 - np.exp(-tt / 0.06)) * (0.75 + 0.25 * np.exp(-tt / 0.3))
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return lp(x, cut) * e


def pad(f, sec, detune=0.006, bright=1800, attack=0.3, release=0.5):
    x = saw(f * (1 - detune), sec, 16) + saw(f * (1 + detune), sec, 16)
    e = np.clip(t(sec) / attack, 0, 1) * np.clip((sec - t(sec)) / release, 0, 1)
    return lp(x, bright) * e


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def bubble(f0, sec=0.07, rise=2.2):
    """One bubble blip: a sine gliding up fast as it closes."""
    fv = f0 * (1 + (rise - 1) * (t(sec) / sec) ** 2)
    return osc(fv, sec) * curve([(0, 0), (0.006, 1), (sec * 0.6, 0.7), (sec, 0)], sec)


def glitter(x, start, sec, count, lo=3500, hi=9000, level=0.2, fall=1.5):
    """Scatters tiny high bell pings over `sec`, thinning out."""
    for k in range(count):
        u = (k / count) ** fall
        st = start + sec * u + s.rng.uniform(0, 0.02)
        f = s.rng.uniform(lo, hi)
        mix(x, n(st), level * (1 - 0.7 * u) * s.rng.uniform(0.5, 1.0)
            * fmbell(f, 0.14, s.rng.uniform(1.4, 2.8), 1.0, s.rng.uniform(0.015, 0.04)))


# F major, in MIDI: F4 65, A4 69, C5 72, F5 77, A5 81, C6 84, F6 89, A6 93, C7 96
F_PENTA = (65, 67, 69, 72, 74, 77, 79, 81, 84, 86, 89, 91, 93, 96, 98, 101)

# ------------------------------------------------------------------ the fairy

d = 0.12  # step: a soft pat on mossy stone: a low muffled tap and a whisper of grass
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(190, 95, 0.06, 0.012))
mix(x, 0, 0.35 * lp(s.noise(0.05), curve([(0, 2200), (0.05, 500)], 0.05)) * env(n(0.05), 0.0015, 0.012, 3))
mix(x, n(0.006), 0.06 * bandnoise(0.05, 2500, 6000) * env(n(0.05), 0.003, 0.015, 3))
save("step", x, 0.3)

d = 0.2  # climb: a light wooden rung tick (a hollow little knock in the wood)
x = np.zeros(n(d))
ex = np.r_[click(0.002, 5000), np.zeros(n(d))]
mix(x, 0, 0.8 * resonate(ex, ((m2f(77) * 1.0, 0.022, 1.0), (m2f(77) * 2.32, 0.012, 0.45), (m2f(77) * 4.1, 0.006, 0.2))))
mix(x, 0, 0.25 * thump(260, 140, 0.03, 0.007))
save("climb", x, 0.35)

d = 0.6  # cast: the wand's zap: a quick bright rising glide through a sparkle, two bells (C7, F7) on top
x = np.zeros(n(d))
fv = curve([(0, 900), (0.12, 3200), (0.18, 3600)], 0.18)
mix(x, 0, 0.3 * osc(fv, 0.18, ((1, 1.0), (2, 0.15))) * curve([(0, 0), (0.01, 1), (0.18, 0)], 0.18))
mix(x, 0, 0.18 * bandnoise(0.25, curve([(0, 2000), (0.25, 6000)], 0.25), 12000) * curve([(0, 0), (0.03, 1), (0.25, 0)],
                                                                                         0.25))
mix(x, n(0.05), 0.22 * fmbell(m2f(96), 0.45, 2.0, 1.0, 0.1), 0.18 * fmbell(m2f(101), 0.45, 3.01, 0.8, 0.12))
glitter(x, 0.06, 0.4, 18, 5000, 11000, 0.12)
save("cast", x, 0.45)

d = 0.9  # catch: the creature wrapped in light: a flurry of bubbles rising, a wobbly glassy F chord holding it
x = np.zeros(n(d))
for k in range(9):
    f0 = s.rng.uniform(380, 900) * (1 + 0.08 * k)
    mix(x, n(0.025 * k + s.rng.uniform(0, 0.01)), (0.32 - 0.02 * k) * bubble(f0, s.rng.uniform(0.05, 0.08)))
tt = t(0.65)
wob = 1 + 0.012 * np.sin(2 * np.pi * 7 * tt)
for m, a in ((77, 0.16), (81, 0.12), (84, 0.12), (89, 0.08)):
    v = osc(m2f(m) * wob, 0.65, ((1, 1.0), (2, 0.08))) * curve([(0, 0), (0.06, 1), (0.25, 0.6), (0.65, 0)], 0.65)
    mix(x, n(0.2), a * v)
mix(x, n(0.2), 0.12 * fmbell(m2f(96), 0.5, 2.0, 0.8, 0.15))
glitter(x, 0.22, 0.5, 12, 4500, 9000, 0.06)
save("catch", x, 0.45)

d = 0.4  # slam_whoosh: the overhead swing: a breathy whoosh rising then falling as the bubble goes over
x = np.zeros(n(d))
wh = bandnoise(0.34, curve([(0, 300), (0.18, 1200), (0.34, 400)], 0.34), curve([(0, 1000), (0.18, 3200), (0.34, 1000)],
                                                                                0.34))
wh = lp(wh, 5000)
mix(x, 0, 0.7 * wh * curve([(0, 0), (0.17, 1), (0.34, 0)], 0.34) ** 1.5)
mix(x, 0, 0.12 * osc(curve([(0, 300), (0.17, 620), (0.34, 280)], 0.34), 0.34) * curve([(0, 0), (0.17, 1), (0.34, 0)], 0.34))
save("slam_whoosh", x, 0.4)

d = 0.6  # slam: a heavy comic thud: a deep boomy drop, a squashy crunch of dirt, a small bounce
x = np.zeros(n(d))
mix(x, 0, 1.0 * thump(120, 38, 0.45, 0.11))
mix(x, 0, 0.45 * lp(s.noise(0.12), curve([(0, 3000), (0.12, 300)], 0.12)) * env(n(0.12), 0.001, 0.035, 3))
mix(x, 0, 0.2 * osc(curve([(0, 300), (0.12, 150)], 0.12), 0.12) * env(n(0.12), 0.002, 0.04, 3))
mix(x, n(0.15), 0.3 * thump(90, 45, 0.18, 0.05))
save("slam", drive(x, 1.6), 0.52)

d = 0.8  # pop: the creature bursts into a bonus: a bright pop, a bloop up to F6, a sparkle of bells
x = np.zeros(n(d))
mix(x, 0, 0.6 * hp(s.noise(0.012), 1200) * env(n(0.012), 0.0003, 0.004, 3))
mix(x, 0, 0.35 * thump(700, 240, 0.04, 0.01))
mix(x, n(0.008), 0.4 * osc(curve([(0, m2f(77)), (0.07, m2f(89))], 0.12), 0.12, ((1, 1.0), (2, 0.2)))
    * curve([(0, 0), (0.008, 1), (0.12, 0)], 0.12))
mix(x, n(0.07), 0.3 * fmbell(m2f(89), 0.6, 2.0, 1.2, 0.15), 0.18 * fmbell(m2f(96), 0.5, 3.01, 1.0, 0.12))
glitter(x, 0.08, 0.55, 22, 5000, 11500, 0.13)
save("pop", x, 0.5)

d = 0.7  # flower: picked: a two-note music-box chime (C6, F6) with a sweet octave above
x = np.zeros(n(d))
mix(x, 0, 0.3 * fmbell(m2f(84), 0.4, 3.5, 1.1, 0.12))
mix(x, n(0.07), 0.38 * fmbell(m2f(89), 0.6, 3.5, 1.2, 0.2), 0.12 * fmbell(m2f(101), 0.5, 2.0, 0.6, 0.12))
mix(x, n(0.07), 0.12 * harp(m2f(77), 0.5, 0.25))
save("flower", x, 0.45)

d = 0.4  # fruit: a round juicy bloop (a sine pinged up to F5) and a little plock
x = np.zeros(n(d))
mix(x, 0, 0.55 * osc(curve([(0, m2f(65)), (0.05, m2f(77)), (0.25, m2f(77))], 0.25), 0.25, ((1, 1.0), (2, 0.25),
                                                                                               (3, 0.06)))
    * curve([(0, 0), (0.004, 1), (0.06, 0.6), (0.25, 0)], 0.25))
ex = np.r_[click(0.002, 6000), np.zeros(n(0.1))]
mix(x, 0, 0.12 * resonate(ex, ((1400, 0.015, 1.0), (2600, 0.008, 0.4))))
save("fruit", x, 0.42)

d = 0.9  # letter: a letter bubble picked: a bubble blip, then a quick F major bell figure (F A C F)
x = np.zeros(n(d))
mix(x, 0, 0.35 * bubble(600, 0.07, 2.5), 0.2 * bubble(900, 0.06, 2.0)[:])
for k, m in enumerate((77, 81, 84, 89)):
    mix(x, n(0.06 + 0.06 * k), 0.28 * fmbell(m2f(m), 0.7, 2.0, 1.1, 0.2 + 0.05 * k))
mix(x, n(0.24), 0.07 * pad(m2f(77), 0.6, 0.004, 3000, 0.05, 0.4))
save("letter", x, 0.45)

d = 1.3  # ladder_magic: the rainbow ladder conjured: a rising shimmer up the F pentatonic, a glassy pad swelling
x = np.zeros(n(d))
steps = F_PENTA[3:]
for k, m in enumerate(steps):
    st = 0.9 * k / len(steps)
    mix(x, n(st), 0.13 * fmbell(m2f(m), 0.5, 2.0, 1.0, 0.16), 0.06 * harp(m2f(m - 12), 0.4, 0.2))
for m in (65, 72, 77, 81):
    mix(x, 0, 0.05 * pad(m2f(m), 1.25, 0.005, curve([(0, 600), (1.0, 3500)], 1.25), 0.8, 0.4))
mix(x, 0, 0.1 * bandnoise(1.0, curve([(0, 1500), (1.0, 7000)], 1.0), 13000) * curve([(0, 0), (0.85, 1), (1.0, 0)], 1.0))
mix(x, n(0.92), 0.16 * fmbell(m2f(101), 0.4, 3.01, 1.0, 0.13))
glitter(x, 0.2, 1.0, 30, 5000, 11500, 0.07, 0.8)
save("ladder_magic", x, 0.45)

d = 2.0  # die: dizzy and sad: three sighing flute notes falling (C6 B5 Bb5), a wobbly glide down, little stars
x = np.zeros(n(d))
for k, m in enumerate((84, 83, 82)):
    mix(x, n(0.28 * k), 0.3 * flute(m2f(m), 0.3, 0.02, 0.08))
tt = t(0.95)
fv = curve([(0, m2f(81)), (0.95, m2f(81) / 2.6)], 0.95) * (1 + 0.035 * np.sin(2 * np.pi * 6.5 * tt))
mix(x, n(0.84), 0.3 * osc(fv, 0.95, ((1, 1.0), (2, 0.18), (3, 0.05))) * curve([(0, 0), (0.03, 1), (0.6, 0.7),
                                                                                (0.95, 0)], 0.95))
for k in range(8):   # stars circling her head: alternating high pings, softer and softer
    mix(x, n(0.9 + 0.11 * k), 0.07 * (1 - k / 9) * fmbell(m2f(96 if k % 2 else 101), 0.15, 2.0, 0.8, 0.04))
mix(x, n(1.78), 0.2 * thump(130, 70, 0.15, 0.04))
save("die", x, 0.42)

d = 2.4  # hurry: a warning handbell rung four times (F6, C6, F6, C6), brisk, ringing on
x = np.zeros(n(d))
for k, m in enumerate((89, 84, 89, 84)):
    ex = np.r_[click(0.002, 8000), np.zeros(n(2.2))]
    f = m2f(m)
    bell = resonate(ex, ((f, 0.35, 1.0), (f * 2.0, 0.2, 0.35), (f * 2.76, 0.12, 0.25), (f * 5.4, 0.04, 0.08)))
    mix(x, n(0.17 * k), (0.5 if k % 2 == 0 else 0.42) * bell)
save("hurry", x, 0.5)

# ------------------------------------------------------------------ jingles

d = 1.8  # level_start: a harp sweep up F major, a flute call (C6 A5 F6) over a soft chord
x = np.zeros(n(d))
for k, m in enumerate((53, 60, 65, 69, 72, 77, 81)):
    mix(x, n(0.04 * k), 0.16 * harp(m2f(m), 1.2, 0.5))
for m, st, ln in ((84, 0.32, 0.18), (81, 0.52, 0.18), (89, 0.72, 0.85)):
    mix(x, n(st), 0.22 * flute(m2f(m), ln, 0.025, 0.1))
for m in (65, 69, 72):
    mix(x, n(0.7), 0.035 * pad(m2f(m), 1.0, 0.004, 1600, 0.1, 0.6))
mix(x, n(0.72), 0.1 * fmbell(m2f(101), 0.8, 2.0, 1.0, 0.25))
save("level_start", x, 0.55)

d = 2.8  # level_clear: a happy skipping flute tune over harp chords, ending on a bright F chord with bells
x = np.zeros(n(d))
tune = ((77, 0.0, 0.14), (81, 0.15, 0.14), (84, 0.3, 0.28), (81, 0.6, 0.14), (84, 0.75, 0.14), (89, 0.9, 0.28),
        (88, 1.2, 0.14), (86, 1.35, 0.14), (88, 1.5, 0.14), (89, 1.65, 0.95))
for m, st, ln in tune:
    mix(x, n(st), 0.24 * flute(m2f(m), ln + 0.04, 0.015, 0.05, 0.003))
for st, chord in ((0.0, (53, 65, 69, 72)), (0.6, (58, 65, 70, 74)), (1.2, (60, 64, 70, 72)), (1.65, (53, 65, 69, 72,
                                                                                                     77))):
    for k, m in enumerate(chord):
        mix(x, n(st + 0.025 * k), 0.12 * harp(m2f(m), 1.0, 0.6))
for k, m in enumerate((89, 93, 96, 101)):
    mix(x, n(1.65 + 0.06 * k), 0.12 * fmbell(m2f(m), 1.0, 2.0, 1.1, 0.35))
glitter(x, 1.7, 1.0, 25, 5000, 11000, 0.06)
save("level_clear", x, 0.6)

d = 2.6  # extra: a full set of letters: a soft brass fanfare (C C C F, A-C F) with a bell arpeggio and sparkles
x = np.zeros(n(d))
for m, st, ln in ((72, 0.0, 0.1), (72, 0.13, 0.1), (72, 0.26, 0.1), (77, 0.39, 0.32), (81, 0.75, 0.12),
                  (84, 0.9, 0.12), (89, 1.05, 0.9)):
    mix(x, n(st), 0.18 * brass(m2f(m), ln + 0.06, 0.012, 0.06), 0.08 * brass(m2f(m - 12), ln + 0.06, 0.012, 0.06))
for m in (53, 60, 65, 69, 72, 77):
    mix(x, n(1.05), 0.07 * brass(m2f(m), 1.2, 0.03, 0.7, 2600))
for k, m in enumerate((77, 81, 84, 89, 93, 96, 101)):
    mix(x, n(1.05 + 0.05 * k), 0.12 * fmbell(m2f(m), 1.0, 2.0, 1.1, 0.3))
glitter(x, 1.1, 1.2, 35, 4500, 11000, 0.08)
save("extra", drive(x, 1.3), 0.6)

d = 3.2  # game_over: a gentle sad close: a slow falling flute (A5 G5 F5 D5 E5) over Bb, B flat minor, then F
x = np.zeros(n(d))
for m, st, ln in ((81, 0.0, 0.42), (79, 0.45, 0.42), (77, 0.9, 0.42), (74, 1.35, 0.42), (76, 1.8, 0.4),
                  (77, 2.2, 0.95)):
    mix(x, n(st), 0.22 * flute(m2f(m), ln, 0.04, 0.15, 0.005))
for st, chord, ln in ((0.0, (46, 62, 65, 70), 0.9), (0.9, (46, 61, 65, 70), 1.3), (2.2, (41, 60, 65, 69), 1.0)):
    for m in chord:
        mix(x, n(st), 0.035 * pad(m2f(m), ln, 0.004, 900, 0.15, 0.5))
    for k, m in enumerate(chord):
        mix(x, n(st + 0.04 * k), 0.08 * harp(m2f(m), 1.0, 0.5))
save("game_over", x, 0.55)

d = 1.8  # door_open: the magical gate: a low soft swell, a glassy shimmer rising, a bright F chord of bells opening
x = np.zeros(n(d))
mix(x, 0, 0.3 * osc(curve([(0, m2f(41)), (1.0, m2f(53))], 1.1), 1.1, ((1, 1.0), (2, 0.3)))
    * curve([(0, 0), (0.6, 1), (1.1, 0)], 1.1))
mix(x, 0, 0.1 * bandnoise(0.9, curve([(0, 800), (0.9, 6000)], 0.9), 12000) * curve([(0, 0), (0.75, 1), (0.9, 0)], 0.9))
for k, m in enumerate((72, 77, 81, 84, 89)):
    mix(x, n(0.12 * k), 0.08 * fmbell(m2f(m), 0.6, 2.0, 0.8, 0.2))
for k, m in enumerate((77, 81, 84, 89, 96)):
    mix(x, n(0.7 + 0.03 * k), 0.13 * fmbell(m2f(m), 1.1, 2.0, 1.2, 0.35))
for m in (65, 72, 77, 81):
    mix(x, n(0.7), 0.04 * pad(m2f(m), 1.0, 0.004, 2500, 0.03, 0.7))
glitter(x, 0.72, 0.9, 25, 5000, 11000, 0.07)
save("door_open", x, 0.5)
