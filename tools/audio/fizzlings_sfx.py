#!/usr/bin/env python3
"""Sound effects for game 18 (Fizzlings), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. An underwater toybox: the bubble is the core
sound. A bubble is modelled as a sine whose pitch rises quickly as it forms and fades (the Minnaert "bloop"),
a pop as a tiny click with a very short, high rising blip. Enemies are wind-up tin toys: the clockwork rattle
is a train of small resonant metal clicks (a ratchet) speeding up, over a rising spring. The trap is a gloopy
low bloop with a slow pitch wobble, a chain of pops a marimba and glockenspiel run climbing two octaves.
The specials: the water wave is a swelling band of noise full of bubbles over a low surge, the fire a
flickering roar with crackles, the bolt a crack and a buzzing zap falling in pitch. The ghost that chases slow
players is a breathy whoosh and a detuned, wavering glide. The jingles are in E flat major like the music:
marimba, glockenspiel, plucks (Karplus-Strong), a soft square "toy synth" and a round brassy voice for the
fanfare, with bubbles rising through them.
Usage: python3 tools/audio/fizzlings_sfx.py [out_dir]   (default: godot/games/fizzlings/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/fizzlings/audio/sfx", seed=1986)
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


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bloop(f, sec=0.12, rise=2.2, amp=1.0):
    """One bubble: a sine rising fast from f to f*rise, fading as it goes (a bubble forming and closing)."""
    fv = f * np.geomspace(1, rise, n(sec))
    return amp * osc(fv, sec) * env(n(sec), 0.003, sec * 0.35, 3)


def pop(f, sec=0.07):
    """A bubble popping: a tiny bright click and a very short high rising blip."""
    x = np.zeros(n(sec))
    mix(x, 0, 0.6 * hp(s.noise(0.004), 3000) * env(n(0.004), 0.0002, 0.001, 3))
    mix(x, 0, osc(f * np.geomspace(1, 2.6, n(0.04)), 0.04, ((1, 1.0), (2, 0.15))) * env(n(0.04), 0.0005, 0.012, 3))
    return x


def bubbles(sec, rate, lo, hi, amp=1.0, grow=0.0):
    """A stream of small bubbles at random times and pitches (grow > 0: pitches drift up over the stream)."""
    x = np.zeros(n(sec) + n(0.2))
    k = int(sec * rate)
    for i in range(k):
        st = s.rng.uniform(0, sec)
        f = s.rng.uniform(lo, hi) * (1 + grow * st / sec)
        mix(x, n(st), s.rng.uniform(0.3, 1.0) * amp * bloop(f, s.rng.uniform(0.04, 0.1), s.rng.uniform(1.6, 2.8)))
    return x


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong)."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1 if i - p - 1 >= 0 else i - p])
    return y * env(N, 0.001, sec, 0.5)


def glock(f, sec=0.8, decay=0.35):
    """A glockenspiel bar: a bright fundamental with the high inharmonic partials of a struck bar."""
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def marimba(f, sec=0.5, decay=0.18):
    """A marimba bar: a warm fundamental, the tuned fourth partial, a soft mallet knock."""
    x = s.bell(f, sec, partials=((1, 1.0), (3.93, 0.22), (9.2, 0.04)), decay=decay)
    return x + np.r_[0.1 * lp(s.noise(0.006), 2500), np.zeros(len(x) - n(0.006))]


def toy(f, sec, decay=0.15, bright=0.6):
    """A soft square 'toy synth' blip: odd harmonics, rounded by a low-pass."""
    x = osc(f, sec, [(k, 1 / k) for k in (1, 3, 5, 7, 9)])
    fm = float(np.max(np.asarray(f, dtype=float)))
    return lp(x, min(9000, fm * (2 + 6 * bright))) * env(n(sec), 0.002, decay, 3)


def brass(f, sec, attack=0.025, decay=0.5, curve_=1.2, bright=1.0):
    """A round brassy voice: a saw-like stack whose brightness opens with the attack, a touch of vibrato."""
    tt = t(sec)
    fv = np.broadcast_to(np.asarray(f, dtype=float), tt.shape) * (1 + 0.004 * np.clip(tt / 0.3, 0, 1) * np.sin(2 * np.pi * 5.5 * tt))
    x = osc(fv, sec, [(k, 1 / k) for k in range(1, 12)])
    fm = float(np.max(fv))
    cut = fm * (1.5 + 4 * bright * np.clip(tt / (attack * 3), 0, 1) * np.exp(-tt / 0.6)) + 400
    return lp(x, np.minimum(cut, 9000)) * env(n(sec), attack, decay, curve_)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude)."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 0.8))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        y += a * np.convolve(x, ir)[:len(x)]
    return y


def tick(f=3200):
    """One small tin click: a sharp impulse through two metal modes."""
    return resonate(np.r_[1.0, np.zeros(n(0.03))], ((f, 0.004, 1.0), (f * 1.73, 0.0025, 0.5)))


# E flat major notes (MIDI), used by the jingles
Eb3, Bb3, Eb4, F4, G4, Ab4, Bb4, C5, D5, Eb5, F5, G5, Ab5, Bb5, C6, D6, Eb6, F6, G6, Bb6, Eb7 = (
    m2f(m) for m in (51, 58, 63, 65, 67, 68, 70, 72, 74, 75, 77, 79, 80, 82, 84, 86, 87, 89, 91, 94, 99))
Ab3, G3, Db4, B3, Gb4 = m2f(56), m2f(55), m2f(61), m2f(59), m2f(66)

# --- the bubbles ---
d = 0.5  # blow: a bubbly puff: a soft breath through the snout, a big round bubble forming, little ones after
x = np.zeros(n(d))
mix(x, 0, 0.35 * lp(hp(s.noise(0.18), 300), curve([(0, 900), (0.05, 2600), (0.18, 700)], 0.18)) * env(n(0.18), 0.02, 0.06, 3))
mix(x, n(0.03), 0.9 * bloop(260, 0.22, 2.4))
mix(x, n(0.03), 0.25 * osc(260 * np.geomspace(1, 2.4, n(0.22)), 0.22, ((2, 1.0),)) * env(n(0.22), 0.003, 0.06, 3))
for k, f in enumerate((620, 780, 990)):
    mix(x, n(0.12 + k * 0.045 + s.rng.uniform(0, 0.01)), (0.4 - 0.08 * k) * bloop(f, 0.07, 2.0))
save("blow", x, 0.42)

for k, f in enumerate((700, 880, 1080, 1320)):  # pop_0..pop_3: the same pop at four pitches, low to high
    x = np.zeros(n(0.18))
    mix(x, 0, pop(f, 0.08))
    mix(x, n(0.01), 0.18 * lp(s.noise(0.05), 5000) * env(n(0.05), 0.001, 0.012, 3))
    mix(x, n(0.02), 0.2 * bloop(f * 1.6, 0.05, 1.8))
    save(f"pop_{k}", x, 0.4)

d = 0.9  # trap: a tin toy caught in a bubble: a big gloopy bubble closing round it with a slow wobble,
x = np.zeros(n(d))  # a muffled clank of the toy inside, a glassy shimmer as the bubble sets
tt = t(0.7)
fw = curve([(0, 140), (0.12, 330), (0.7, 300)], 0.7) * (1 + 0.14 * np.sin(2 * np.pi * 7 * tt) * np.exp(-tt / 0.35))
mix(x, 0, 0.8 * osc(fw, 0.7, ((1, 1.0), (2, 0.3), (3, 0.08))) * env(n(0.7), 0.01, 0.2, 3))
mix(x, 0, 0.35 * lp(s.noise(0.15), np.geomspace(3000, 300, n(0.15))) * env(n(0.15), 0.003, 0.05, 3))
mix(x, n(0.06), 0.3 * lp(resonate(np.r_[1.0, np.zeros(n(0.2))], ((820, 0.03, 1.0), (1930, 0.02, 0.5))), 1500))
for k, f in enumerate((Bb5, Eb6, G6)):
    mix(x, n(0.22 + k * 0.05), 0.1 * glock(f, 0.5, 0.2))
mix(x, n(0.1), 0.35 * bubbles(0.35, 20, 400, 900))
save("trap", x, 0.5)

d = 1.6  # chain: several trapped toys popped at once: a quick run of pops rising, a marimba and glockenspiel
x = np.zeros(n(d))  # arpeggio climbing two octaves, sparkles and a bright chord on top
run = (Eb5, G5, Bb5, Eb6, G6, Bb6, Eb7)
for i, f in enumerate(run):
    mix(x, n(i * 0.06), 0.35 * pop(700 + 150 * i), 0.3 * marimba(f / 2, 0.5, 0.15), 0.2 * glock(f, 0.6, 0.2))
for f in (Eb6, G6, Bb6):
    mix(x, n(0.45), 0.14 * glock(f, 1.0, 0.45))
for f in (Eb4, G4, Bb4, Eb5):
    mix(x, n(0.45), 0.16 * pluck(f, 1.0, 0.7, 0.997))
for k in range(12):
    mix(x, n(0.45 + k * 0.07 + s.rng.uniform(0, 0.03)), (0.12 - 0.008 * k) * glock(s.rng.choice((Eb7, 2 * G6, 2 * Bb6)), 0.3, 0.1))
mix(x, n(0.4), 0.3 * bubbles(0.6, 30, 600, 1400, grow=0.6))
save("chain", x, 0.55)

d = 0.3  # treat: a cheerful blip up a fourth (B flat to E flat) with a marimba under it
x = np.zeros(n(d))
mix(x, 0, 0.4 * toy(Bb5, 0.07, 0.04), 0.3 * marimba(Bb5, 0.2, 0.08))
mix(x, n(0.06), 0.45 * toy(Eb6, 0.18, 0.08), 0.35 * marimba(Eb6, 0.25, 0.1), 0.12 * glock(Eb6 * 2, 0.25, 0.1))
save("treat", x, 0.42)

d = 0.9  # treat_big: a big treat: a toy-synth arpeggio up the E flat chord, a glockenspiel sparkle, a pop
x = np.zeros(n(d))
mix(x, 0, 0.3 * pop(900))
for i, f in enumerate((Eb5, G5, Bb5, Eb6, G6)):
    mix(x, n(0.02 + i * 0.05), 0.35 * toy(f, 0.12 if i < 4 else 0.4, 0.06 if i < 4 else 0.2), 0.25 * marimba(f, 0.3, 0.1))
for f in (Eb6, G6, Bb6):
    mix(x, n(0.22), 0.12 * glock(f * 2 if f < G6 else f, 0.6, 0.25))
save("treat_big", x, 0.48)

d = 0.25  # jump: a soft rising toy-synth swoop with a little bubble at the top
x = np.zeros(n(d))
mix(x, 0, 0.5 * toy(curve([(0, 300), (0.12, 720)], 0.14), 0.14, 0.06, 0.4))
mix(x, 0, 0.12 * lp(hp(s.noise(0.08), 800), 4000) * env(n(0.08), 0.005, 0.03, 3))
mix(x, n(0.06), 0.25 * bloop(900, 0.06, 1.8))
save("jump", x, 0.32)

d = 0.2  # land: soft: a padded thump on the toybox floor and a tiny wet squish
x = np.zeros(n(d))
mix(x, 0, 0.7 * thump(160, 70, 0.1, 0.025))
mix(x, 0, 0.2 * lp(s.noise(0.06), np.geomspace(2500, 400, n(0.06))) * env(n(0.06), 0.002, 0.02, 3))
save("land", lp(x, 3000), 0.3)

d = 0.6  # bounce_bubble: jumping on a bubble: a springy "boing" rising with a rubbery wobble, a bloop
x = np.zeros(n(d))
tt = t(0.5)
fb = curve([(0, 150), (0.05, 420), (0.5, 380)], 0.5) * (1 + 0.1 * np.sin(2 * np.pi * 14 * tt) * np.exp(-tt / 0.15))
mix(x, 0, 0.7 * osc(fb, 0.5, ((1, 1.0), (2, 0.25), (3, 0.1))) * env(n(0.5), 0.003, 0.12, 3))
mix(x, 0, 0.3 * thump(120, 70, 0.08, 0.02))
mix(x, n(0.02), 0.3 * bloop(500, 0.12, 2.4))
save("bounce_bubble", x, 0.42)

d = 1.0  # angry: the tin toys wind up angry: a clockwork ratchet clicking faster and faster, a spring rising
x = np.zeros(n(d))  # under it, and a tinny "ding" as the key lets go
st = 0.0
k = 0
while st < 0.72:
    mix(x, n(st), (0.5 + 0.3 * (k % 2)) * tick(2800 + 400 * (k % 3)))
    st += 0.075 * (1 - st / 0.9) + 0.012
    k += 1
spr = osc(curve([(0, 90), (0.75, 260)], 0.75), 0.75, ((1, 1.0), (2, 0.5), (3, 0.3), (5, 0.15)))
mix(x, 0, 0.18 * lp(spr, 1800) * curve([(0, 0), (0.1, 1), (0.7, 1), (0.75, 0)], 0.75))
mix(x, n(0.74), 0.4 * resonate(np.r_[1.0, np.zeros(n(0.25))], ((1850, 0.06, 1.0), (4300, 0.03, 0.4))))
mix(x, n(0.74), 0.3 * thump(220, 90, 0.1, 0.03))
save("angry", x, 0.52)

d = 1.6  # hurry: a warning jingle: urgent toy-synth triplets climbing in two waves, a glockenspiel alarm on top
x = np.zeros(n(d))
waves = ((Eb5, Gb4 * 2, Ab5, Bb5), (F5, Ab5, Bb5, C6))
for w, notes in enumerate(waves):
    for i, f in enumerate(notes):
        for r in range(3):
            st = w * 0.62 + i * 0.13 + r * 0.043
            if st < 1.3:
                mix(x, n(st), (0.2 + 0.05 * r) * toy(f * (2 if r == 2 else 1), 0.05, 0.025, 0.7))
        mix(x, n(w * 0.62 + i * 0.13), 0.15 * marimba(f / 2, 0.2, 0.08))
for st, f in ((1.24, D6), (1.34, D6), (1.44, Eb6)):
    mix(x, n(st), 0.35 * toy(f, 0.08, 0.04, 0.8), 0.2 * glock(f, 0.3, 0.12))
save("hurry", x, 0.5)

d = 1.7  # die: the axolotl caught: a wobbly bubble sinking, a soft bonk, two sad falling bloops, a drooping tone
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(320, 110, 0.1, 0.03), 0.25 * tick(1900))
ln = 1.0
f = curve([(0, 900), (1.0, 180)], ln) * (1 + 0.05 * np.sin(2 * np.pi * 7 * t(ln)))
mix(x, n(0.1), 0.45 * toy(f, ln, 0.5, 0.3) * curve([(0, 0), (0.03, 1), (0.8, 0.7), (1.0, 0)], ln))
for i, fp in enumerate((Bb3, G3)):
    mix(x, n(1.12 + i * 0.22), 0.35 * pluck(fp, 0.5, 0.4, 0.994))
    mix(x, n(1.12 + i * 0.22), 0.25 * bloop(fp, 0.2, 0.55))
save("die", x, 0.55)

d = 1.3  # extra life: a marimba and toy-synth arpeggio climbing two octaves, glockenspiel chord, bubbles
x = np.zeros(n(d))
for i, f in enumerate((Eb4, G4, Bb4, Eb5, G5, Bb5, Eb6)):
    mix(x, n(i * 0.065), 0.3 * marimba(f, 0.4, 0.12), 0.15 * toy(f * 2, 0.08, 0.04))
for f in (Eb6, G6, Bb6):
    mix(x, n(0.46), 0.2 * glock(f, 0.8, 0.35))
mix(x, n(0.4), 0.25 * bubbles(0.5, 24, 700, 1500, grow=0.5))
save("extra_life", x, 0.5)

d = 0.6  # letter: a letter bubble collected: a pop, then a bright double chime (E flat and B flat)
x = np.zeros(n(d))
mix(x, 0, 0.4 * pop(1100))
mix(x, n(0.03), 0.3 * glock(Eb6, 0.5, 0.2), 0.2 * toy(Eb6, 0.07, 0.03))
mix(x, n(0.11), 0.35 * glock(Bb6, 0.5, 0.25), 0.2 * toy(Bb5, 0.1, 0.05))
save("letter", x, 0.45)

d = 3.2  # extend: every letter collected: a big fanfare: a brassy call over a marimba roll, tuba-like low brass,
x = np.zeros(n(d))  # a glittering glockenspiel run, a held E flat chord, bubbles streaming up, sparkles falling
call = ((0.0, Bb4, 0.12), (0.14, Eb5, 0.12), (0.28, G5, 0.12), (0.42, Bb5, 0.3), (0.8, G5, 0.12), (0.94, Bb5, 0.12),
        (1.08, Eb6, 1.6))
for st, f, ln in call:
    mix(x, n(st), 0.3 * brass(f / 2, ln + 0.05, 0.012, ln * 0.8 + 0.1, 1.2))
    mix(x, n(st), 0.12 * glock(f * 2, 0.4, 0.15))
for st, f in ((0.0, Eb3), (0.42, Bb3 / 2), (0.8, Eb3), (1.08, Eb3 / 2)):
    mix(x, n(st), 0.25 * brass(f, 0.35 if st < 1 else 1.6, 0.02, 0.3 if st < 1 else 1.2, 1.3, 0.4))
for f in (Eb4, G4, Bb4, Eb5):
    mix(x, n(1.08), 0.1 * brass(f, 1.7, 0.05, 1.2, 1.3, 0.6))
for k in range(18):  # a marimba roll up the chord under the held note
    f = (Eb4, G4, Bb4, Eb5, G5, Bb5)[k % 6]
    mix(x, n(1.08 + k * 0.05), (0.18 - 0.006 * k) * marimba(f, 0.3, 0.1))
for i, f in enumerate((Eb5, F5, G5, Bb5, C6, Eb6, F6, G6, Bb6, Eb7)):
    mix(x, n(1.08 + i * 0.035), 0.12 * glock(f, 0.5, 0.2))
for st in (0.0, 0.42, 0.8, 1.08):
    mix(x, n(st), 0.45 * thump(110, 45, 0.3, 0.08))
mix(x, n(1.08), 0.12 * hp(s.noise(1.4), 6000) * env(n(1.4), 0.002, 0.5, 2.5))
mix(x, n(1.0), 0.35 * bubbles(1.4, 30, 500, 1300, grow=0.8))
for k in range(10):
    mix(x, n(1.6 + k * 0.12), (0.1 - 0.007 * k) * glock(s.rng.choice((Eb7, 2 * G6, 2 * Bb6)), 0.3, 0.1))
save("extend", x, 0.6)

d = 2.2  # water_flood: the water special: a wave rushes through: a swelling surge of noise, a deep rumble,
x = np.zeros(n(d))  # a bright spray on the crest and a stream of bubbles all the way
tt = t(d)
sw = curve([(0, 0), (0.35, 1), (1.2, 0.8), (2.2, 0)], d)
mix(x, 0, 0.6 * lp(hp(s.noise(d), 200), curve([(0, 400), (0.4, 3500), (2.2, 800)], d)) * sw * (0.8 + 0.2 * np.sin(2 * np.pi * 3 * tt)))
mix(x, 0, 0.8 * lp(s.noise(d), 180) * sw)
mix(x, n(0.25), 0.2 * hp(s.noise(0.8), 4000) * env(n(0.8), 0.05, 0.25, 3))
mix(x, 0, 0.5 * bubbles(1.9, 40, 250, 900))
save("water_flood", x, 0.55)

d = 1.3  # fire: the fire special: a quick whoosh that catches into a flickering roar, crackles popping in it
x = np.zeros(n(d))
tt = t(d)
flick = 0.7 + 0.3 * np.abs(lp(s.noise(d), 12)) * 6
roar = lp(hp(s.noise(d), 120), curve([(0, 600), (0.12, 3000), (1.3, 900)], d))
mix(x, 0, 0.7 * roar * np.clip(flick, 0, 1.4) * curve([(0, 0), (0.1, 1), (0.9, 0.7), (1.3, 0)], d))
mix(x, 0, 0.5 * lp(s.noise(d), 150) * curve([(0, 0), (0.12, 1), (1.3, 0)], d))
for k in range(26):
    st = s.rng.uniform(0.05, 1.15)
    mix(x, n(st), s.rng.uniform(0.2, 0.6) * resonate(np.r_[1.0, np.zeros(n(0.02))], ((s.rng.uniform(1800, 4500), 0.002, 1.0),)))
save("fire", x, 0.55)

d = 0.9  # bolt: the lightning special: a sharp crack, a buzzing zap falling in pitch with a jittering level,
x = np.zeros(n(d))  # a low boom behind it
mix(x, 0, 1.0 * hp(s.noise(0.02), 1500) * env(n(0.02), 0.0003, 0.005, 3))
zf = curve([(0, 1400), (0.6, 110)], 0.6)
zap = np.sign(osc(zf, 0.6)) * 0.5 + 0.5 * osc(zf * 1.5, 0.6)
jit = (s.rng.uniform(0, 1, n(0.6) // 400 + 1) > 0.3).repeat(400)[:n(0.6)] * 0.6 + 0.4
mix(x, 0, 0.4 * lp(zap, 5000) * jit * env(n(0.6), 0.002, 0.25, 2.5))
mix(x, 0, 0.35 * hp(s.noise(0.5), 2500) * jit[:n(0.5)] * env(n(0.5), 0.001, 0.12, 3))
mix(x, n(0.02), 0.7 * thump(90, 35, 0.8, 0.25))
save("bolt", x, 0.6)

d = 2.1  # ready: a bouncy start jingle: tuba-ish plucked bass (E flat, B flat), a marimba and toy-synth tune,
x = np.zeros(n(d))  # a glockenspiel chord and a burst of bubbles at the end
beat = 60 / 150
tune = ((0, Bb4, 0.5), (0.5, Eb5, 0.5), (1, G5, 0.25), (1.25, F5, 0.25), (1.5, Eb5, 0.5), (2, Bb5, 0.5),
        (2.5, Ab5, 0.25), (2.75, G5, 0.25), (3, F5, 0.5), (3.5, D5, 0.5), (4, Eb5, 1.0))
for b, f, lnb in tune:
    mix(x, n(b * beat), 0.3 * marimba(f, 0.5, 0.15), 0.15 * toy(f, lnb * beat, lnb * beat * 0.6, 0.5))
for b, f in ((0, Eb3 / 2), (1, Bb3 / 2), (2, Eb3 / 2), (3, Bb3 / 2), (4, Eb3 / 2)):
    mix(x, n(b * beat), 0.45 * pluck(f, 0.4 if b < 4 else 1.0, 0.3, 0.995))
    if b < 4:
        for g in (G4, Bb4, Eb5):
            mix(x, n((b + 0.5) * beat), 0.07 * marimba(g, 0.2, 0.06))
for f in (Eb5, G5, Bb5, Eb6):
    mix(x, n(4 * beat), 0.12 * glock(f * 2 if f < Bb5 else f, 0.9, 0.35))
mix(x, n(4 * beat), 0.3 * bubbles(0.5, 26, 600, 1400, grow=0.6))
save("ready", x, 0.55)

d = 2.2  # stage clear: a happy run: marimba arpeggio climbing, a brassy rising third, a glockenspiel chord
x = np.zeros(n(d))
for i, f in enumerate((Eb4, G4, Bb4, Eb5, G5, Bb5, Eb6)):
    mix(x, n(i * 0.07), 0.3 * marimba(f, 0.4, 0.12), 0.1 * glock(f * 2, 0.3, 0.12))
for st, f, lnb in ((0.52, G5, 0.18), (0.72, Ab5, 0.18), (0.92, Bb5, 1.1)):
    mix(x, n(st), 0.3 * brass(f / 2, lnb, 0.015, lnb * 0.7 + 0.1, 1.2), 0.15 * toy(f, lnb, lnb * 0.6))
for f in (Eb3, Bb3, Eb4, G4):
    mix(x, n(0.92), 0.1 * brass(f, 1.1, 0.04, 0.8, 1.3, 0.5), 0.15 * pluck(f, 1.2, 0.6, 0.997))
for f in (Eb6, G6, Bb6):
    mix(x, n(0.95), 0.12 * glock(f, 1.0, 0.45))
mix(x, n(0.9), 0.3 * bubbles(0.7, 26, 600, 1400, grow=0.6))
for st in (0.52, 0.92):
    mix(x, n(st), 0.4 * thump(110, 45, 0.3, 0.08))
save("stage_clear", x, 0.58)

d = 2.6  # game over: a gentle comic-sad marimba line winding down (B flat, A flat, G, F... E flat), an A flat
x = np.zeros(n(d))  # minor colour sighing back home, a last bubble sinking
for st, f in ((0.0, Bb5), (0.28, Ab5), (0.58, G5), (0.92, F5)):
    mix(x, n(st), 0.3 * marimba(f, 0.6, 0.2), 0.08 * glock(f, 0.4, 0.15))
for f in (Ab3, m2f(59), Eb4):  # A flat minor: Ab3 Cb4 Eb4
    mix(x, n(0.92), 0.14 * pluck(f, 1.0, 0.4, 0.996))
mix(x, n(1.35), 0.32 * marimba(Eb5, 1.0, 0.45), 0.1 * glock(Eb6, 0.8, 0.3))
for f in (Eb3 / 2, Bb3 / 2, Eb3, G3, Bb3):
    mix(x, n(1.35), 0.2 * pluck(f, 1.2, 0.35, 0.997))
mix(x, n(1.9), 0.2 * bloop(400, 0.5, 0.45))
save("game_over", lp(x, 8000), 0.55)

d = 1.8  # ghost: the chaser that comes when a stage drags: a breathy whoosh sweeping past, and a detuned,
x = np.zeros(n(d))  # wavering glide (two voices beating) rising and falling like a sigh
tt = t(d)
wh = lp(hp(s.noise(d), curve([(0, 300), (0.8, 1200), (1.8, 400)], d)), curve([(0, 800), (0.8, 4000), (1.8, 900)], d))
mix(x, 0, 0.5 * wh * curve([(0, 0), (0.7, 1), (1.8, 0)], d))
fg = curve([(0, 420), (0.6, 700), (1.2, 520), (1.8, 360)], d) * (1 + 0.025 * np.sin(2 * np.pi * 5.5 * tt))
g = osc(fg, d, ((1, 1.0), (2, 0.1))) + osc(fg * 1.012, d, ((1, 0.8),)) + 0.5 * osc(fg * 1.5, d)
mix(x, 0, 0.18 * g * curve([(0, 0), (0.3, 1), (1.4, 0.8), (1.8, 0)], d))
save("ghost", x, 0.45)
