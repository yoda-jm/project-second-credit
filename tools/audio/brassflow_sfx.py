#!/usr/bin/env python3
"""Sound effects for game 29 (Brassflow), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any earlier pipe game: a steampunk workshop at night, made of struck
metal (an excitation rung through damped inharmonic modes: heavy plates, brass fittings, a wrench), filtered noise
(steam, rushing liquid, splashes), little sine chirps for bubbles, breathy steam whistles (noise rung through a narrow
resonance with a sine core) and FM bells. The jingles sit in D major, the key of tools/audio/brassflow_music.py.
place          a heavy metal clunk: the piece set down on the board (a thud, a brass ring, a latch click)
replace        a clatter and a wrench: the old piece knocked off, a ratchet turning
move           a soft tick (the cursor)
flow_start     a valve wheel squeaking open, then the glow rushing in
fill           a short gurgle (the game pitches it up with the length)
cross_bonus    a bright chime: an arpeggio of bells over a shimmer
spill          a splash and a long steam hiss
passed         a steam whistle fanfare: short, short, long on a D major chord, a bell on top
failed         a whistle sagging down, a clank, a sigh of steam
game_over      three falling whistle notes, a heavy clank, the boiler sighing out
fast           a whoosh
countdown_tick a clockwork tick
flow_loop      a seamless 2.0 s bubbling flow (the noise cross-faded end into start, modulations in whole cycles)
No voices anywhere.
Usage: python3 tools/audio/brassflow_sfx.py [out_dir]   (default: godot/games/brassflow/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/brassflow/audio/sfx", seed=2929)
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


def strike(sec, bright=6000):
    """An excitation: a short click padded with silence to sec."""
    return np.r_[click(0.003, bright), np.zeros(n(sec) - n(0.003))]


def bandnoise(sec, lo, hi):
    return hp(lp(s.noise(sec), hi), lo)


def fmbell(f, sec, ratio=1.4, index=2.5, decay=0.4):
    tt = t(sec)
    e = np.exp(-tt / decay)
    return np.sin(2 * np.pi * f * tt + index * e * np.sin(2 * np.pi * f * ratio * tt)) * e


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def loop(make, sec, fade=0.25):
    """A seamless loop: renders sec + fade, then cross-fades the overhang into the start (equal power)."""
    x = make(sec + fade)
    L, F = n(sec), n(fade)
    y = x[:L].copy()
    a = np.linspace(0, np.pi / 2, F)
    y[:F] = y[:F] * np.sin(a) + x[L:L + F] * np.cos(a)
    return y


def whistle(f, sec, attack=0.04, release=0.12, breath=0.5, bend=None):
    """A steam whistle: noise rung through a narrow resonance at f (and a weak octave), a sine core, a breathy
    chiff on the attack. bend: an optional pitch curve multiplier (array of n(sec))."""
    L = n(sec)
    tt = t(sec)
    fv = f * (bend if bend is not None else 1.0) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * tt))
    core = osc(fv, sec, ((1, 1.0), (2, 0.12), (3, 0.05)))
    if bend is None:
        air = norm(resonate(s.noise(sec), ((f, 0.08, 1.0), (2 * f, 0.05, 0.3))))
    else:
        air = norm(bandnoise(sec, f * 0.7, f * 1.6))
    chiff = bandnoise(sec, 2000, 8000) * env(L, 0.002, 0.06, 3)
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return (0.7 * core + breath * air) * e + 0.25 * chiff


PLATE = ((180, 0.06, 1.0), (433, 0.05, 0.7), (781, 0.04, 0.5), (1265, 0.03, 0.35), (1890, 0.02, 0.2))
BRASS = ((612, 0.12, 1.0), (1530, 0.09, 0.6), (2740, 0.07, 0.4), (4110, 0.05, 0.25))
WRENCH = ((1150, 0.08, 1.0), (2980, 0.05, 0.6), (5300, 0.03, 0.3))

# ------------------------------------------------------------------ the board

d = 0.6  # place: a heavy metal clunk: a low thud, the plate ringing, a brass fitting, a latch click after
x = np.zeros(n(d))
mix(x, 0, 0.9 * thump(140, 50, 0.25, 0.06))
mix(x, 0, 0.6 * resonate(strike(d, 4000), PLATE))
mix(x, 0, 0.25 * resonate(strike(d, 8000), BRASS))
mix(x, n(0.07), 0.3 * resonate(strike(0.2, 9000), ((3300, 0.012, 1.0), (5200, 0.008, 0.5))))
save("place", drive(x, 1.6), 0.75)

d = 0.95  # replace: the old piece knocked off (two clanks), a wrench ratcheting, the new one landing
x = np.zeros(n(d))
mix(x, 0, 0.6 * resonate(strike(0.4, 7000), BRASS), 0.4 * thump(220, 90, 0.1, 0.03))
mix(x, n(0.09), 0.45 * resonate(strike(0.4, 6000), ((840, 0.08, 1.0), (2100, 0.05, 0.6), (3600, 0.03, 0.3))))
mix(x, n(0.16), 0.3 * resonate(strike(0.3, 6000), ((1320, 0.05, 1.0), (3150, 0.03, 0.5))))
for k in range(9):  # the ratchet: quick even clicks through the wrench's modes
    mix(x, n(0.3 + k * 0.034), (0.28 - 0.01 * k) * resonate(strike(0.08, 9000), WRENCH))
mix(x, n(0.62), 0.7 * thump(130, 50, 0.22, 0.05), 0.45 * resonate(strike(0.33, 4000), PLATE))
save("replace", drive(x, 1.5), 0.7)

d = 0.12  # move: a soft tick
x = np.zeros(n(d))
mix(x, 0, 0.6 * resonate(strike(d, 5000), ((2600, 0.008, 1.0), (4100, 0.005, 0.4))))
mix(x, 0, 0.3 * thump(600, 300, 0.02, 0.006))
save("move", lp(x, 7000), 0.35)

d = 2.0  # flow_start: a valve wheel squeaks open (a clunk), then the glow rushes into the pipe
x = np.zeros(n(d))
mix(x, 0, 0.6 * resonate(strike(0.4, 5000), BRASS))
sq = osc(curve([(0, 900), (0.35, 1250), (0.5, 1100)], 0.5) * (1 + 0.03 * np.sin(2 * np.pi * 31 * t(0.5))), 0.5,
         ((1, 1.0), (2, 0.4), (3, 0.2))) * curve([(0, 0), (0.05, 1), (0.4, 0.7), (0.5, 0)], 0.5)
mix(x, n(0.05), 0.2 * sq)
rush = lp(bandnoise(1.6, 150, 4000), curve([(0, 600), (0.5, 3200), (1.6, 1600)], 1.6))
rush *= curve([(0, 0), (0.25, 1), (1.0, 0.8), (1.6, 0)], 1.6) * (0.85 + 0.15 * np.sin(2 * np.pi * 9 * t(1.6)))
mix(x, n(0.35), 0.55 * norm(rush))
for k in range(16):  # bubbles in the rush
    st = s.rng.uniform(0.45, 1.6)
    f0 = s.rng.uniform(300, 900)
    mix(x, n(st), 0.12 * osc(curve([(0, f0), (0.05, f0 * 1.9)], 0.06), 0.06) * env(n(0.06), 0.003, 0.02, 2))
mix(x, n(0.35), 0.5 * thump(110, 45, 0.4, 0.12))
save("flow_start", x, 0.65)

d = 0.32  # fill: a short gurgle: three bubbles over a liquid glug
x = np.zeros(n(d))
mix(x, 0, 0.6 * lp(thump(180, 90, 0.2, 0.06), 900))
for k, (st, f0) in enumerate(((0.0, 420), (0.06, 560), (0.13, 480), (0.18, 700))):
    ln = 0.07
    mix(x, n(st), (0.35 - 0.04 * k) * osc(curve([(0, f0), (ln, f0 * 2.1)], ln), ln, ((1, 1.0), (2, 0.15)))
        * env(n(ln), 0.004, 0.03, 2))
mix(x, 0, 0.12 * lp(s.noise(0.25), 1800) * env(n(0.25), 0.01, 0.08, 2))
save("fill", x, 0.55)

d = 1.5  # cross_bonus: a bright chime: D major bells climbing, a shimmer
x = np.zeros(n(d))
for k, m in enumerate((86, 90, 93, 98)):
    mix(x, n(k * 0.06), 0.3 * fmbell(m2f(m), 1.3, 3.5, 1.3, 0.35))
mix(x, n(0.24), 0.18 * fmbell(m2f(102), 1.2, 2.0, 1.0, 0.5))
mix(x, 0, 0.06 * bandnoise(1.2, 6000, 14000) * curve([(0, 0), (0.25, 1), (1.2, 0)], 1.2)
    * (0.6 + 0.4 * np.sin(2 * np.pi * 16 * t(1.2))))
save("cross_bonus", x, 0.55)

d = 2.4  # spill: a splash (a burst, droplets falling back) and a long steam hiss
x = np.zeros(n(d))
mix(x, 0, 0.9 * norm(lp(lp(s.noise(0.35), curve([(0, 3500), (0.35, 500)], 0.35)), 2500)) * env(n(0.35), 0.002, 0.1, 2.5))
mix(x, 0, 0.6 * thump(160, 60, 0.25, 0.06))
for k in range(26):
    st = 0.05 + (k / 26) ** 1.4 * 0.8 + s.rng.uniform(0, 0.03)
    f0 = s.rng.uniform(600, 2400)
    mix(x, n(st), 0.12 * (1 - k / 30) * osc(curve([(0, f0), (0.03, f0 * 1.6)], 0.035), 0.035)
        * env(n(0.035), 0.001, 0.012, 2))
hiss = lp(bandnoise(2.2, 2000, 9000), 6000) * curve([(0, 0), (0.15, 1), (0.9, 0.7), (2.2, 0)], 2.2)
hiss *= 0.8 + 0.2 * np.sin(2 * np.pi * 7 * t(2.2))
mix(x, n(0.12), 0.16 * norm(hiss))
save("spill", x, 0.65)

d = 0.35  # fast: a whoosh
x = np.zeros(n(d))
wh = lp(lp(hp(s.noise(d), curve([(0, 200), (0.18, 700), (d, 300)], d)), curve([(0, 700), (0.18, 3200), (d, 900)], d)),
        curve([(0, 900), (0.18, 3500), (d, 1100)], d))
mix(x, 0, norm(wh) * curve([(0, 0), (0.15, 1), (d, 0)], d))
save("fast", x, 0.55)

d = 0.2  # countdown_tick: a clockwork tick (escapement click and a little brass ring)
x = np.zeros(n(d))
mix(x, 0, 0.7 * resonate(strike(d, 9000), ((3100, 0.01, 1.0), (4700, 0.007, 0.5), (1650, 0.02, 0.3))))
mix(x, n(0.012), 0.3 * resonate(strike(0.15, 9000), ((2200, 0.008, 1.0),)))
save("countdown_tick", x, 0.45)

# ------------------------------------------------------------------ the level's end

D4, FS4, A4, D5, FS5, A5 = (m2f(m) for m in (62, 66, 69, 74, 78, 81))

d = 3.0  # passed: a steam whistle fanfare: short, short, long on D major (D5 F#5 A5), a bell, a puff of steam
x = np.zeros(n(d))
for st, ln in ((0.0, 0.16), (0.22, 0.16), (0.46, 1.5)):
    for f, a in ((D5, 0.3), (FS5, 0.26), (A5, 0.24), (D4, 0.12)):
        mix(x, n(st), a * whistle(f, ln, 0.02, 0.1 if ln < 0.5 else 0.5))
for k, m in enumerate((86, 90, 93)):
    mix(x, n(0.46 + 0.09 * k), 0.12 * fmbell(m2f(m), 1.6, 2.0, 1.1, 0.45))
mix(x, n(1.8), 0.18 * bandnoise(1.0, 2500, 9000) * curve([(0, 0), (0.05, 1), (1.0, 0)], 1.0))
mix(x, 0, 0.35 * thump(110, 50, 0.2, 0.05))
save("passed", x, 0.65)

d = 2.4  # failed: a whistle sagging down a fourth, a clank, a sigh of steam
x = np.zeros(n(d))
bend = curve([(0, 1.0), (0.2, 1.0), (1.1, 0.72)], 1.2)
mix(x, 0, 0.4 * whistle(A4, 1.2, 0.03, 0.4, bend=bend), 0.25 * whistle(D5, 1.2, 0.03, 0.4, bend=bend))
mix(x, n(1.15), 0.7 * resonate(strike(0.6, 4000), PLATE), 0.6 * thump(120, 45, 0.3, 0.08))
mix(x, n(1.2), 0.25 * lp(bandnoise(1.1, 400, 6000), curve([(0, 5000), (1.1, 800)], 1.1))
    * curve([(0, 0), (0.1, 1), (1.1, 0)], 1.1))
save("failed", drive(x, 1.2), 0.65)

d = 4.0  # game_over: three falling whistle notes (A, F#, D, the last one sinking), a heavy clank, the boiler sighs out
x = np.zeros(n(d))
for k, (f, st, ln) in enumerate(((A4, 0.0, 0.45), (FS4, 0.55, 0.45), (D4, 1.1, 1.3))):
    b = curve([(0, 1.0), (ln * 0.4, 1.0), (ln, 0.9)], ln) if k == 2 else None
    mix(x, n(st), 0.4 * whistle(f, ln, 0.03, 0.15 if k < 2 else 0.6, bend=b),
        0.2 * whistle(f * 1.5, ln, 0.03, 0.15 if k < 2 else 0.6, bend=b))
mix(x, n(2.35), 0.9 * thump(100, 35, 0.5, 0.15), 0.8 * resonate(strike(1.2, 3500), PLATE),
    0.3 * resonate(strike(1.0, 6000), BRASS))
sigh = lp(bandnoise(1.5, 300, 7000), curve([(0, 6000), (1.5, 500)], 1.5)) * curve([(0, 0), (0.15, 1), (1.5, 0)], 1.5)
mix(x, n(2.45), 0.3 * norm(sigh))
save("game_over", drive(x, 1.3), 0.65)

# ------------------------------------------------------------------ the flowing loop


def flow(sec):
    """The glow flowing through the pipes: a low liquid rumble, a gentle swash, bubbles popping at random."""
    L = n(sec)
    tt = t(sec)
    base = 1 / 2.0     # the loop is 2.0 s: modulations in multiples of 0.5 Hz
    rumble = norm(lp(lp(s.noise(sec), 260), 260))
    swash = norm(lp(bandnoise(sec, 300, 2500), 1800))
    swash *= 0.6 + 0.4 * np.sin(2 * np.pi * 2 * base * tt) * (0.7 + 0.3 * np.sin(2 * np.pi * 5 * base * tt))
    bub = np.zeros(L)
    for st in s.rng.uniform(0, sec - 0.08, int(14 * sec)):
        f0 = s.rng.uniform(250, 800)
        ln = s.rng.uniform(0.04, 0.08)
        b = osc(curve([(0, f0), (ln, f0 * s.rng.uniform(1.6, 2.4))], ln), ln) * env(n(ln), 0.004, ln * 0.4, 2)
        mix(bub, n(st), b * s.rng.uniform(0.4, 1.0))
    return 0.6 * rumble + 0.3 * swash + 0.35 * bub


s.save("flow_loop", loop(flow, 2.0), 0.55, fade=False)
