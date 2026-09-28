#!/usr/bin/env python3
"""Sound effects for game 24 (Jelly Spike), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. Two jelly blobs play volleyball with a floaty beach
ball on a sunny tropical beach, played as a beach band: wobbling jelly, a hollow vinyl ball, sand, a rope net,
marimba, steel pan and a referee's pea whistle.
The ball: touch_soft is a soft jelly boing as a blob bumps it (a hollow vinyl thock over a wobbling glide), touch_hard
the spike (a wet, juicy slap, a crack of the vinyl and a quick whoosh). The blobs: jelly_jump is a springy wobble
up, jelly_land a squelch. ball_sand is the ball thumping into sand with a spray of grains hissing after it,
ball_net the rope net rattling and its top cord twanging, ball_wall a hollow bonk off the side boards.
The jingles are in F major like the music. No voices anywhere and no crowd: a point is cheered by seagulls
squawking (synthesised glides, not a recording) and a little marimba and steel-pan flourish.
Usage: python3 tools/audio/jellyspike_sfx.py [out_dir]   (default: godot/games/jellyspike/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/jellyspike/audio/sfx", seed=2024)
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


def knock(f, sec=0.1, dec=0.02, ratio=2.7):
    """A struck hollow body: a click through two modes (wood, vinyl or metal by the ratio and decay)."""
    ex = np.r_[click(), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * ratio, dec * 0.4, 0.35)))


def marimba(f, sec=0.5, decay=0.18):
    x = s.bell(f, sec, partials=((1, 1.0), (3.93, 0.22), (9.2, 0.04)), decay=decay)
    return x + 0.25 * np.r_[click(0.006, 2500), np.zeros(len(x) - n(0.006))]


def pan(f, sec=0.6, decay=0.3):
    """A steel pan note: a fundamental with the octave and a tuned twelfth, a soft metallic 'ping' on the attack."""
    tt = t(sec)
    x = s.bell(f, sec, partials=((1, 1.0), (2.0, 0.55), (3.0, 0.22), (4.02, 0.08)), decay=decay)
    return x * (1 + 0.5 * np.exp(-tt * 40)) + 0.08 * np.r_[click(0.004, 5000), np.zeros(len(x) - n(0.004))]


def glock(f, sec=0.8, decay=0.35):
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong)."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1])
    return y * env(N, 0.001, sec, 0.5)


def boing(f0, f1, sec, wob=18.0, depth=0.25, harm=((1, 1.0), (2, 0.3), (3, 0.1)), fade=9.0):
    """A rubbery, jelly 'boing': a tone gliding f0 -> f1 with a fast wobble that dies away."""
    tt = t(sec)
    fv = np.geomspace(f0, f1, n(sec)) * (1 + depth * np.sin(2 * np.pi * wob * tt) * np.exp(-tt * fade))
    return osc(fv, sec, harm)


def squelch(sec, f0, f1, wet=1.0):
    """Wet jelly: noise through a sweeping low-pass, chopped by a fast bubbly flutter, and a gulping tone."""
    tt = t(sec)
    flutter = 0.5 + 0.5 * np.sin(2 * np.pi * curve([(0, 45), (sec, 18)], sec) * tt) ** 2
    body = lp(hp(s.noise(sec), 120), curve([(0, f0 * 6), (sec, f1 * 3)], sec)) * flutter
    gulp = osc(curve([(0, f0), (sec, f1)], sec), sec, ((1, 1.0), (2, 0.25)))
    return (wet * 0.6 * body + 0.7 * gulp) * env(n(sec), 0.002, sec * 0.35, 2.5)


def whoosh(sec, f0, f1, q=1.0):
    """Air rushing: noise through a low-pass sweeping f0 -> f1."""
    return lp(hp(s.noise(sec), 150 * q), curve([(0, f0), (sec, f1)], sec))


def gull(f, sec, bend=1.4):
    """A seagull squawk (synthesised): a nasal, buzzy tone that leaps up, cracks and falls, a rough edge on it."""
    tt = t(sec)
    fv = curve([(0, f), (sec * 0.15, f * bend), (sec * 0.55, f * bend * 0.93), (sec, f * 0.7)], sec)
    fv = fv * (1 + 0.03 * np.sin(2 * np.pi * 31 * tt)) * (1 + 0.02 * s.rng.uniform(-1, 1, n(sec)))
    x = osc(fv, sec, [(k, 1 / k ** 0.6) for k in range(1, 14)])
    x = hp(lp(x, 4200), 700)
    x += 0.12 * hp(s.noise(sec), 2500)
    return x * curve([(0, 0), (sec * 0.08, 1), (sec * 0.6, 0.7), (sec, 0)], sec)


def vinyl_ball(f=260, sec=0.25, dec=0.03):
    """The beach ball's shell: a hollow, airy vinyl 'thock' (a knock through two low modes and a puff)."""
    x = knock(f, sec, dec, 2.3)
    mix(x, 0, 0.15 * lp(s.noise(sec), 1500) * env(n(sec), 0.001, 0.015, 3))
    return x


# F major (MIDI), the jingles' key
F3, A3, C4, F4, A4, Bb4, C5, D5, E5, F5, G5, A5, Bb5, C6, D6, E6, F6, A6, C7 = (
    m2f(m) for m in (53, 57, 60, 65, 69, 70, 72, 74, 76, 77, 79, 81, 82, 84, 86, 88, 89, 93, 96))
F2, C3, Bb2, G3 = m2f(41), m2f(48), m2f(46), m2f(55)

# --- the ball ---
d = 0.4  # touch_soft: a blob bumps the ball: a hollow vinyl thock over a soft wobbling jelly boing
x = np.zeros(n(d))
mix(x, 0, 0.6 * vinyl_ball(250, 0.25, 0.03), 0.5 * thump(220, 110, 0.12, 0.025))
mix(x, n(0.003), 0.4 * boing(300, 420, 0.3, 16, 0.18, fade=7) * env(n(0.3), 0.004, 0.08, 3))
save("touch_soft", lp(x, 5000), 0.34)

d = 0.5  # touch_hard: the spike: a wet, juicy slap, a crack of the vinyl, a bouncy jelly rebound and a whoosh away
x = np.zeros(n(d))
slap = lp(hp(s.noise(0.03), 700), 5500) * env(n(0.03), 0.0003, 0.006, 3)
mix(x, 0, 0.9 * slap, 0.7 * thump(300, 90, 0.15, 0.03), 0.5 * vinyl_ball(330, 0.2, 0.02))
mix(x, n(0.002), 0.8 * squelch(0.14, 500, 170, 1.2))
mix(x, n(0.01), 0.3 * boing(260, 520, 0.2, 24, 0.2) * env(n(0.2), 0.003, 0.05, 3))
mix(x, n(0.03), 0.14 * whoosh(0.3, 4000, 800) * curve([(0, 0), (0.02, 1), (0.3, 0)], 0.3))
save("touch_hard", x, 0.5)

d = 0.8  # ball_sand: the ball thumps into sand: a dull low thud, the sand crunching, a spray of grains hissing down
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(140, 50, 0.25, 0.05), 0.35 * vinyl_ball(180, 0.2, 0.02))
mix(x, 0, 0.35 * lp(s.noise(0.12), 1800) * env(n(0.12), 0.001, 0.03, 3))
ln = 0.7  # the spray: sparse grains (random crackle) over a soft hiss, brightest just after the hit
grains = hp(s.noise(ln), 3000) * (s.rng.uniform(0, 1, n(ln)) ** 6)
hiss = hp(lp(s.noise(ln), 7000), 2000)
mix(x, n(0.02), (0.5 * grains + 0.12 * hiss) * curve([(0, 0), (0.04, 1), (0.25, 0.45), (ln, 0)], ln))
save("ball_sand", x, 0.5)

d = 0.7  # ball_net: the rope net rattles (knots knocking) and its top cord twangs
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(200, 110, 0.12, 0.025), 0.3 * lp(s.noise(0.08), 2500) * env(n(0.08), 0.001, 0.02, 3))
for k in range(8):
    st = 0.01 + k * 0.035 + s.rng.uniform(-0.01, 0.01)
    mix(x, n(st), (0.3 * 0.82 ** k) * knock(s.rng.uniform(700, 1300), 0.06, 0.006, 2.1))
tw = osc(147 * (1 + 0.02 * np.sin(2 * np.pi * 7 * t(0.6))) * curve([(0, 1.03), (0.05, 1.0)], 0.6), 0.6,
         ((1, 1.0), (2, 0.6), (3, 0.35), (4, 0.2), (5, 0.1)))
mix(x, n(0.005), 0.35 * lp(tw, 2500) * env(n(0.6), 0.002, 0.18, 2))
mix(x, n(0.005), 0.25 * pluck(147, 0.6, 0.6, 0.994))
save("ball_net", x, 0.42)

d = 0.35  # ball_wall: a hollow bonk off the side boards: wood and the ball's vinyl
x = np.zeros(n(d))
mix(x, 0, 0.7 * knock(380, 0.25, 0.035, 2.6), 0.4 * vinyl_ball(240, 0.2, 0.025), 0.4 * thump(200, 90, 0.1, 0.02))
save("ball_wall", x, 0.38)

# --- the blobs ---
d = 0.4  # jelly_jump: a springy jelly wobble rising, a little suck of air as it leaves the sand
x = np.zeros(n(d))
mix(x, 0, 0.45 * boing(180, 520, 0.3, 14, 0.22, ((1, 1.0), (2, 0.2)), 6) * env(n(0.3), 0.01, 0.12, 2.5))
mix(x, 0, 0.3 * squelch(0.08, 250, 400, 0.8))
mix(x, 0, 0.1 * whoosh(0.2, 800, 3000) * curve([(0, 0), (0.05, 1), (0.2, 0)], 0.2))
save("jelly_jump", x, 0.3)

d = 0.4  # jelly_land: a squelch: the jelly splats onto the sand, a wet gulp and a sagging wobble
x = np.zeros(n(d))
mix(x, 0, 0.7 * squelch(0.18, 320, 110, 1.3), 0.5 * thump(150, 60, 0.15, 0.03))
mix(x, n(0.02), 0.25 * boing(160, 120, 0.25, 11, 0.2, ((1, 1.0), (2, 0.2)), 8) * env(n(0.25), 0.005, 0.07, 3))
mix(x, 0, 0.15 * hp(s.noise(0.2), 3000) * s.rng.uniform(0, 1, n(0.2)) ** 6 * env(n(0.2), 0.002, 0.06, 3))
save("jelly_land", lp(x, 5000), 0.34)

# --- the referee and the game ---
d = 0.5  # serve: a hand-toss boing and a light pan ping (the rally starts)
x = np.zeros(n(d))
mix(x, 0, 0.5 * vinyl_ball(260, 0.2, 0.02), 0.35 * boing(260, 390, 0.25, 16, 0.12) * env(n(0.25), 0.003, 0.07, 3))
mix(x, n(0.06), 0.25 * pan(C6, 0.4, 0.15), 0.15 * pan(F6, 0.4, 0.12))
save("serve", x, 0.34)


def whistle(sec, f=2700):
    """A pea whistle: a pure tone warbled fast by the rolling pea, a breathy edge."""
    tt = t(sec)
    trill = 1 + 0.035 * np.sin(2 * np.pi * 38 * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * 3.1 * tt))
    tone = osc(f * trill, sec, ((1, 1.0), (2, 0.08)))
    amp = 1 + 0.25 * np.sin(2 * np.pi * 38 * tt)
    breath = hp(lp(s.noise(sec), 6000), 2000)
    return (tone * amp + 0.1 * breath) * curve([(0, 0), (0.015, 1), (sec - 0.03, 0.9), (sec, 0)], sec)


d = 0.9  # whistle_point: two short blasts and a long one
x = np.zeros(n(d))
mix(x, 0, 0.5 * whistle(0.09))
mix(x, n(0.14), 0.5 * whistle(0.09))
mix(x, n(0.29), 0.5 * whistle(0.55))
save("whistle_point", x, 0.2)

d = 1.6  # cheer_point: seagulls squawk overhead and a quick marimba and steel-pan flourish up F major
x = np.zeros(n(d))
for st, f, ln, g in ((0.05, 1150, 0.28, 0.2), (0.3, 1350, 0.22, 0.16), (0.48, 1250, 0.3, 0.18), (0.9, 1500, 0.2, 0.1)):
    mix(x, n(st), g * gull(f, ln, s.rng.uniform(1.3, 1.5)))
for i, f in enumerate((F5, A5, C6, F6, A6)):
    mix(x, n(0.02 + i * 0.07), 0.24 * marimba(f / 2, 0.35, 0.1), 0.14 * pan(f, 0.4, 0.14))
mix(x, n(0.4), 0.28 * pan(C7, 0.9, 0.35), 0.2 * pan(A6, 0.9, 0.35), 0.18 * marimba(F4, 0.8, 0.3))
save("cheer_point", x, 0.5)

d = 0.8  # match_point: a tension sting: a low pan and marimba tremolo on C with a rising half-step, a tom thump
x = np.zeros(n(d))
for k in range(10):
    f = C5 if k < 6 else m2f(73)
    mix(x, n(k * 0.05), (0.12 + 0.012 * k) * marimba(f, 0.15, 0.05), (0.08 + 0.01 * k) * pan(f / 2, 0.15, 0.05))
mix(x, 0, 0.5 * thump(120, 50, 0.3, 0.07))
mix(x, n(0.5), 0.6 * thump(110, 45, 0.3, 0.06), 0.25 * pan(D5, 0.3, 0.12), 0.2 * pan(m2f(80), 0.3, 0.12))
save("match_point", x, 0.46)

d = 2.8  # match_win: a steel-pan and marimba fanfare in F, plucked bass, a gull cries over the last chord
x = np.zeros(n(d))
beat = 0.16
for k, f in enumerate((C5, F5, A5, C6, A5, C6)):
    mix(x, n(k * beat), 0.26 * pan(f, 0.35, 0.12), 0.22 * marimba(f / 2, 0.3, 0.1))
for k, f in enumerate((F2, C3, F2)):
    mix(x, n(k * beat * 2), 0.5 * thump(110, 45, 0.15, 0.05), 0.35 * pluck(f * 2, 0.35, 0.5, 0.99))
for st, root, ch in ((1.0, Bb2, (Bb4, D5, F5)), (1.3, C3, (Bb4, C5, E5))):
    mix(x, n(st), 0.4 * pluck(root * 2, 0.3, 0.5, 0.99), 0.4 * thump(110, 45, 0.15, 0.05))
    for p in ch:
        mix(x, n(st), 0.1 * pan(p, 0.3, 0.1))
mix(x, n(1.6), 0.6 * pluck(F2 * 2, 1.2, 0.5, 0.997), 0.5 * thump(110, 40, 0.3, 0.08))
for f in (F4, A4, C5, F5):
    mix(x, n(1.6), 0.12 * pan(f, 1.2, 0.5), 0.1 * marimba(f, 0.9, 0.3))
mix(x, n(1.6), 0.25 * pan(F6, 1.2, 0.5), 0.15 * glock(C7, 1.2, 0.5))
mix(x, n(1.95), 0.12 * gull(1300, 0.3, 1.45))
mix(x, n(1.62), 0.05 * hp(s.noise(0.9), 7000) * curve([(0, 0), (0.1, 1), (0.9, 0)], 0.9))
save("match_win", x, 0.6)

d = 0.08  # menu_tick: a tiny woody marimba tick
x = np.zeros(n(d))
mix(x, 0, 0.4 * marimba(C6, 0.08, 0.025), 0.3 * knock(2400, 0.05, 0.004, 1.6))
save("menu_tick", x, 0.28)
