#!/usr/bin/env python3
"""Sound effects for game 27 (Marble Drift), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any arcade marble game: a glass marble on floating courses, made of
filtered noise, struck-glass and struck-metal resonances (an excitation rung through damped modes), FM bells, sine
sweeps and soft saw synths. The jingles sit in E minor / E major, the key of tools/audio/marbledrift_music.py.
Loops: roll_loop and roll_rough_loop are 2.0 s and seamless (their noise is cross-faded end into start, every
modulation completes whole cycles), mastered at a steady level so the game can pitch them and fade them with speed.
No voices anywhere.
Usage: python3 tools/audio/marbledrift_sfx.py [out_dir]   (default: godot/games/marbledrift/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/marbledrift/audio/sfx", seed=2727)
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


def pad(f, sec, detune=0.006, bright=1800, attack=0.3, release=0.5):
    x = saw(f * (1 - detune), sec, 16) + saw(f * (1 + detune), sec, 16) + 0.6 * saw(f / 2, sec, 12)
    e = np.clip(t(sec) / attack, 0, 1) * np.clip((sec - t(sec)) / release, 0, 1)
    return lp(x, bright) * e


def brass(f, sec, attack=0.03, release=0.15, bright=3500):
    """A soft synth brass: two detuned saws through a filter that opens on the attack."""
    tt = t(sec)
    x = saw(f * 0.997, sec, 20) + saw(f * 1.003, sec, 20)
    cut = 600 + bright * (1 - np.exp(-tt / 0.06)) * (0.75 + 0.25 * np.exp(-tt / 0.3))
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return lp(x, cut) * e


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


GLASS = ((2210, 0.05, 1.0), (3570, 0.035, 0.6), (5230, 0.025, 0.4), (7480, 0.015, 0.25))   # a glass ball's modes


# ------------------------------------------------------------------ rolling loops

def roll(sec):
    """A glass marble rolling on smooth floor: a low hollow rumble, the floor's faint hiss, tiny glass ticks."""
    L = n(sec)
    tt = t(sec)
    base = 1 / 2.0                                         # the loop is 2.0 s: modulations in multiples of 0.5 Hz
    rumble = lp(lp(s.noise(sec), 380), 380)
    rumble = rumble / (np.max(np.abs(rumble)) + 1e-9)
    body = resonate(lp(s.noise(sec), 1500) * 0.3, ((220, 0.03, 1.0), (430, 0.02, 0.6), (910, 0.012, 0.35)))
    body = body / (np.max(np.abs(body)) + 1e-9)
    hiss = bandnoise(sec, 2500, 7000)
    hiss = hiss / (np.max(np.abs(hiss)) + 1e-9)
    wob = 0.8 + 0.2 * np.sin(2 * np.pi * 7 * base * tt) * (0.7 + 0.3 * np.sin(2 * np.pi * 2 * base * tt))
    ticks = np.zeros(L)
    for i in s.rng.integers(0, L - n(0.02), 40):
        ticks[i] += s.rng.uniform(0.3, 1.0) * s.rng.choice((-1, 1))
    ticks = resonate(ticks, GLASS)
    ticks = ticks / (np.max(np.abs(ticks)) + 1e-9)
    return (0.7 * rumble + 0.45 * body) * wob + 0.07 * hiss + 0.1 * ticks


def roll_rough(sec):
    """On rough floor: a gritty, bumpier roll: dense small knocks through low wooden-ish modes over the rumble."""
    L = n(sec)
    tt = t(sec)
    base = 1 / 2.0
    rumble = lp(lp(s.noise(sec), 320), 320)
    rumble = rumble / (np.max(np.abs(rumble)) + 1e-9)
    grit = np.zeros(L)
    for i in s.rng.integers(0, L - n(0.01), int(220 * sec)):
        grit[i] += s.rng.uniform(0.2, 1.0) * s.rng.choice((-1, 1))
    grit = resonate(lp(grit, 5000), ((420, 0.012, 1.0), (930, 0.008, 0.6), (1900, 0.005, 0.4), (3100, 0.004, 0.25)))
    grit = grit / (np.max(np.abs(grit)) + 1e-9)
    bumps = 0.65 + 0.35 * np.abs(np.sin(2 * np.pi * 11 * base * tt)) ** 3 + 0.15 * np.sin(2 * np.pi * 3 * base * tt)
    hiss = bandnoise(sec, 1500, 5000)
    hiss = hiss / (np.max(np.abs(hiss)) + 1e-9)
    return 0.7 * rumble * bumps + 0.6 * grit * (0.8 + 0.2 * bumps) + 0.08 * hiss


x = loop(roll, 2.0)
s.save("roll_loop", x, 0.6, fade=False)
x = loop(roll_rough, 2.0)
s.save("roll_rough_loop", x, 0.6, fade=False)

# ------------------------------------------------------------------ impacts

d = 0.45  # bump: a glass knock on a wall: a hard click ringing the ball's modes, a dull knock of the wall
x = np.zeros(n(d))
ex = np.r_[click(0.002, 9000), np.zeros(n(d) - n(0.002))]
mix(x, 0, 0.8 * resonate(ex, GLASS))
mix(x, 0, 0.45 * thump(260, 110, 0.08, 0.02))
mix(x, 0, 0.25 * lp(s.noise(0.03), 2500) * env(n(0.03), 0.0005, 0.006, 3))
save("bump", x, 0.6)

d = 0.5  # land: a thud on the floor, a short glass tick on top
x = np.zeros(n(d))
mix(x, 0, 0.9 * thump(150, 45, 0.3, 0.07))
mix(x, 0, 0.35 * lp(s.noise(0.08), curve([(0, 1800), (0.08, 300)], 0.08)) * env(n(0.08), 0.001, 0.02, 3))
ex = np.r_[click(0.002, 7000), np.zeros(n(0.3))]
mix(x, 0, 0.25 * resonate(ex, GLASS))
save("land", drive(x, 1.3), 0.7)

d = 1.6  # shatter: a crack, a burst of glass, then fragments tinkling down and settling
x = np.zeros(n(d))
ex = np.r_[click(0.004, 12000), np.zeros(n(0.5))]
mix(x, 0, 0.7 * resonate(ex, ((2900, 0.03, 1.0), (4300, 0.025, 0.8), (6100, 0.02, 0.6), (8200, 0.012, 0.4))))
mix(x, 0, 0.6 * bandnoise(0.25, 2500, 11000) * env(n(0.25), 0.0005, 0.05, 2.5))
mix(x, 0, 0.5 * thump(220, 70, 0.12, 0.03))
for k in range(70):   # fragments: thinning out and dropping in level over the second
    u = (k / 70) ** 1.6
    st = 0.01 + 1.25 * u + s.rng.uniform(0, 0.03)
    f = s.rng.uniform(2800, 9500)
    ping = fmbell(f, 0.12, s.rng.uniform(1.3, 2.7), 1.2, s.rng.uniform(0.01, 0.03))
    mix(x, n(st), (0.32 * (1 - 0.75 * u)) * ping * s.rng.uniform(0.5, 1.0))
for k in range(14):   # a few heavier pieces bouncing
    st = 0.05 + 0.08 * k + s.rng.uniform(0, 0.04)
    ex = np.r_[click(0.002, 8000), np.zeros(n(0.12))]
    mix(x, n(st), 0.25 * (1 - k / 16) * resonate(ex, ((s.rng.uniform(1800, 3200), 0.02, 1.0),
                                                      (s.rng.uniform(4000, 6000), 0.012, 0.5))))
mix(x, n(0.02), 0.08 * bandnoise(1.2, 4000, 12000) * curve([(0, 1), (0.3, 0.5), (1.2, 0)], 1.2))
save("shatter", drive(x, 1.8), 0.7)

d = 1.8  # acid: a hot sizzle that bubbles and eats the marble away, its glassy tone sinking and dissolving
x = np.zeros(n(d))
sz = bandnoise(1.6, 2000, 6500) * curve([(0, 0), (0.03, 1), (0.6, 0.8), (1.6, 0)], 1.6)
sz *= 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 23 * t(1.6) + 3 * np.sin(2 * np.pi * 3.1 * t(1.6))))
mix(x, 0, 0.45 * sz)
crk = np.zeros(n(1.5))
for i in s.rng.integers(0, len(crk) - n(0.004), 380):
    crk[i:i + n(0.004)] += s.rng.uniform(-1, 1) * env(n(0.004), 0.0002, 0.0008, 3)
mix(x, 0, 0.35 * lp(crk, 7000) * curve([(0, 1), (1.0, 0.6), (1.5, 0)], 1.5))
for k in range(18):   # bubbles: small rising blips
    st = s.rng.uniform(0.05, 1.3)
    f0 = s.rng.uniform(500, 1200)
    mix(x, n(st), 0.1 * osc(curve([(0, f0), (0.04, f0 * 1.8)], 0.05), 0.05) * env(n(0.05), 0.002, 0.015, 2))
tone = osc(curve([(0, 1650), (1.4, 420)], 1.4), 1.4, ((1, 1.0), (2.76, 0.3)))
tone *= curve([(0, 0), (0.05, 1), (1.4, 0)], 1.4) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t(1.4)))
mix(x, n(0.05), 0.16 * tone)
mix(x, 0, 0.3 * thump(140, 50, 0.2, 0.05))
save("acid", x, 0.6)

d = 1.8  # fall: a falling whistle sinking away, rushing air fading with it
x = np.zeros(n(d))
fv = curve([(0, 1500), (1.7, 260)], 1.7) * (1 + 0.012 * np.sin(2 * np.pi * 6.5 * t(1.7)))
wh = osc(fv, 1.7, ((1, 1.0), (2, 0.08))) * curve([(0, 0), (0.06, 1), (0.8, 0.7), (1.7, 0)], 1.7)
mix(x, 0, 0.35 * wh)
air = lp(hp(s.noise(1.7), curve([(0, 1800), (1.7, 300)], 1.7)), curve([(0, 5000), (1.7, 900)], 1.7))
mix(x, 0, 0.3 * air * curve([(0, 0), (0.15, 1), (1.7, 0)], 1.7))
save("fall", x, 0.55)

d = 1.4  # respawn: a crystal shimmer: a rising E major glass arpeggio over a bright noise sheen and a soft pad
x = np.zeros(n(d))
for k, m in enumerate((76, 80, 83, 88, 92, 95)):
    mix(x, n(0.04 + k * 0.055), 0.22 * fmbell(m2f(m), 1.0, 3.01, 1.1, 0.28 + 0.04 * k))
mix(x, 0, 0.08 * bandnoise(1.2, 6000, 13000) * curve([(0, 0), (0.3, 1), (1.2, 0)], 1.2)
    * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * t(1.2))))
mix(x, n(0.05), 0.08 * pad(m2f(64), 1.1, 0.004, 4000, 0.25, 0.6), 0.06 * pad(m2f(71), 1.1, 0.004, 4000, 0.25, 0.6))
save("respawn", x, 0.55)

d = 1.4  # checkpoint: a clear two-note chime, E6 then B6, ringing over an octave E
x = np.zeros(n(d))
mix(x, 0, 0.35 * fmbell(m2f(88), 1.3, 2.0, 1.3, 0.35), 0.12 * fmbell(m2f(76), 1.3, 2.0, 0.8, 0.45))
mix(x, n(0.11), 0.35 * fmbell(m2f(95), 1.2, 2.0, 1.3, 0.35), 0.1 * fmbell(m2f(100), 1.0, 2.0, 0.8, 0.2))
save("checkpoint", x, 0.55)

d = 0.6  # knock_steelie: heavy steel on glass: a hard clack ringing inharmonic metal modes, a low thump
x = np.zeros(n(d))
ex = np.r_[click(0.003, 9000), np.zeros(n(d) - n(0.003))]
mix(x, 0, 0.8 * resonate(ex, ((612, 0.09, 1.0), (1489, 0.06, 0.7), (2533, 0.045, 0.5), (3870, 0.03, 0.35),
                              (5310, 0.02, 0.2))))
mix(x, 0, 0.3 * resonate(ex, GLASS))
mix(x, 0, 0.7 * thump(180, 55, 0.18, 0.045))
save("knock_steelie", drive(x, 1.6), 0.7)

d = 0.75  # knock_hopper: a springy boing: a bent tone wobbling as the spring rings, a rubber pop
x = np.zeros(n(d))
tt = t(0.7)
fv = 210 * (1 + 0.65 * (1 - np.exp(-tt / 0.05))) * (1 + 0.16 * np.exp(-tt / 0.22) * np.sin(2 * np.pi * 14 * tt))
mix(x, 0, 0.5 * osc(fv, 0.7, ((1, 1.0), (2, 0.25), (3, 0.08))) * env(n(0.7), 0.003, 0.22, 2.2))
tw = osc(fv * 4.1, 0.7, ((1, 1.0),)) * env(n(0.7), 0.002, 0.12, 2.5)
mix(x, 0, 0.12 * tw)
mix(x, 0, 0.35 * thump(320, 130, 0.06, 0.015))
save("knock_hopper", x, 0.6)

# ------------------------------------------------------------------ the race

d = 3.2  # finish: a fanfare: synth brass climbing E - G# - B, a B - C# - D# pickup, a wide E major chord and bells
x = np.zeros(n(d))
for k, (m, st, ln) in enumerate(((64, 0.0, 0.16), (68, 0.16, 0.16), (71, 0.32, 0.3),
                                 (71, 0.66, 0.12), (73, 0.8, 0.12), (75, 0.94, 0.14))):
    mix(x, n(st), 0.22 * brass(m2f(m), ln + 0.06, 0.012, 0.05), 0.12 * brass(m2f(m - 12), ln + 0.06, 0.012, 0.05))
for m in (52, 59, 64, 68, 71, 76):   # E major, open
    mix(x, n(1.12), 0.1 * brass(m2f(m), 1.9, 0.03, 0.9, 3000))
mix(x, n(1.12), 0.06 * pad(m2f(40), 2.0, 0.004, 900, 0.05, 1.0))
for k, m in enumerate((88, 92, 95, 100)):
    mix(x, n(1.12 + 0.07 * k), 0.16 * fmbell(m2f(m), 1.6, 2.0, 1.2, 0.4))
mix(x, n(1.12), 0.5 * thump(110, 40, 0.3, 0.1), 0.12 * bandnoise(0.8, 5000, 12000) * env(n(0.8), 0.002, 0.25, 2))
save("finish", x, 0.65)

d = 0.2  # countdown_beep: a soft clean beep, A5
x = np.zeros(n(d))
mix(x, 0, osc(m2f(81), 0.16, ((1, 1.0), (3, 0.12), (5, 0.04))) * np.clip((0.16 - t(0.16)) / 0.02, 0, 1)
    * np.clip(t(0.16) / 0.003, 0, 1))
save("countdown_beep", lp(x, 6000), 0.45)

d = 0.7  # go: the same beep an octave up (A6), longer, with a fifth and a little sparkle
x = np.zeros(n(d))
e = np.clip((0.6 - t(0.6)) / 0.25, 0, 1) * np.clip(t(0.6) / 0.003, 0, 1)
mix(x, 0, osc(m2f(93), 0.6, ((1, 1.0), (3, 0.12), (5, 0.04))) * e, 0.3 * osc(m2f(88), 0.6) * e)
mix(x, 0, 0.12 * fmbell(m2f(100), 0.5, 2.0, 1.0, 0.15))
save("go", lp(x, 7000), 0.5)

d = 1.15  # time_low: a ticking warning: tick, tock, tick, tock, quickening, with a two-tone alert under it
x = np.zeros(n(d))
for k, st in enumerate((0.0, 0.3, 0.55, 0.75)):
    ex = np.r_[click(0.002, 9000), np.zeros(n(0.1))]
    mix(x, n(st), 0.6 * resonate(ex, ((2400 if k % 2 == 0 else 1800, 0.012, 1.0), (5100, 0.006, 0.4))))
for k, (m, st) in enumerate(((84, 0.0), (79, 0.3), (84, 0.55), (79, 0.75))):
    b = sq(m2f(m), 0.14, 9) * np.clip((0.14 - t(0.14)) / 0.03, 0, 1) * np.clip(t(0.14) / 0.003, 0, 1)
    mix(x, n(st + 0.005), 0.3 * lp(b, 3500))
save("time_low", x, 0.5)

d = 1.7  # time_up: a buzzer, then a sad sinking two-note fall
x = np.zeros(n(d))
bz = sq(curve([(0, 118), (0.55, 112)], 0.55), 0.55, 21) * (0.75 + 0.25 * np.sign(np.sin(2 * np.pi * 30 * t(0.55))))
mix(x, 0, 0.4 * lp(bz, 2200) * np.clip((0.55 - t(0.55)) / 0.04, 0, 1) * np.clip(t(0.55) / 0.004, 0, 1))
for m, st, ln in ((64, 0.62, 0.38), (59, 1.0, 0.65)):
    fv = m2f(m) * curve([(0, 1), (ln * 0.6, 1), (ln, 0.94)], ln)
    v = saw(fv, ln, 14) * np.clip((ln - t(ln)) / 0.15, 0, 1) * np.clip(t(ln) / 0.02, 0, 1)
    mix(x, n(st), 0.2 * lp(v, 1400), 0.12 * lp(saw(fv / 2, ln, 10), 700) * np.clip((ln - t(ln)) / 0.15, 0, 1))
save("time_up", x, 0.6)
