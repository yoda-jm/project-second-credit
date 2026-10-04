#!/usr/bin/env python3
"""Sound effects for game 31 (Tinplate Turbo), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any arcade game: wind-up tin racing cars on a toy diorama, made of
buzzy clockwork motors (detuned saws with a gear-tooth rattle), struck thin-metal modes (tin clunks and clatters),
filtered noise (tyre squeal, oil, water), springs (jumps), FM bells and soft synth brass (jingles). The jingles sit in
G major, the key of tools/audio/tinplate_music.py.
- engine_loop is 1.0 s and seamless (every modulation makes whole cycles in the loop, the noise is cross-faded end
  into start). Its motor note is G2 (98 Hz): the game sets pitch_scale from the car's speed (about 0.7 idle .. 2.0).
- skid_loop is 1.0 s and seamless, a steady squeal: fade it in and out with the slip.
- countdown_beep (three times) and go_beep are a fifth apart (D6, then G6 an octave above the motor's G).
No voices anywhere.
Usage: python3 tools/audio/tinplate_sfx.py [out_dir]   (default: godot/games/tinplate/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/tinplate/audio/sfx", seed=3131)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, *bs):
    """Adds sounds (of any lengths) into x from `start` (samples)."""
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


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def loop(make, sec, fade=0.2):
    """A seamless loop: renders sec + fade, then cross-fades the overhang into the start (equal power)."""
    x = make(sec + fade)
    L, F = n(sec), n(fade)
    y = x[:L].copy()
    a = np.linspace(0, np.pi / 2, F)
    y[:F] = y[:F] * np.sin(a) + x[L:L + F] * np.cos(a)
    return y


def tin(sec, base=1.0, decay=1.0, bright=1.0):
    """The ring of a pressed-tin shell: inharmonic, quickly damped thin-metal modes, scaled by base."""
    return [(380 * base, 0.05 * decay, 1.0), (910 * base, 0.035 * decay, 0.7), (1630 * base, 0.025 * decay, 0.5),
            (2470 * base, 0.018 * decay, 0.35 * bright), (3720 * base, 0.012 * decay, 0.25 * bright),
            (5150 * base, 0.008 * decay, 0.15 * bright)]


def clank(sec, base=1.0, decay=1.0, bright=1.0, hard=4000):
    """One tin strike: a click rung through the shell's modes."""
    ex = np.r_[click(0.004, hard), np.zeros(max(0, n(sec) - n(0.004)))]
    return resonate(ex, tin(sec, base, decay, bright))


def spring(f0, f1, sec, wob=28.0, depth=0.12):
    """A coil spring: a sweeping tone with a fast wobble that dies away (the boing)."""
    tt = t(sec)
    fv = curve([(0, f0), (sec, f1)], sec) * (1 + depth * np.exp(-tt / (sec * 0.5)) * np.sin(2 * np.pi * wob * tt))
    return osc(fv, sec, ((1, 1.0), (2, 0.25), (3, 0.1)))


def ratchet(x, start, count, rate, level=0.4, base=1.0):
    """Clockwork clicks: a wind-up key turning, `rate` clicks a second."""
    for k in range(count):
        mix(x, n(start + k / rate + s.rng.uniform(0, 0.004)),
            level * (0.8 + 0.2 * s.rng.uniform()) * clank(0.06, 2.6 * base, 0.4, 1.4, 7000))


# ------------------------------------------------------------------ the loops

def motor(sec):
    """A wind-up motor at G2: buzzy detuned saws, a gear-tooth rattle (14 Hz, whole cycles in 1 s), a thin gear whine
    on the octave-and-fifth, a soft whirr of noise."""
    tt = t(sec)
    f = 98.0
    buzz = saw(f, sec, 18) + 0.7 * saw(f * 1.006, sec, 18) + 0.4 * sq(f * 2, sec, 9)
    buzz = lp(lp(buzz, 1300), 2200)
    rattle = 0.72 + 0.28 * np.abs(np.sin(2 * np.pi * 7 * tt)) ** 0.5   # 14 Hz teeth
    flutter = 1 + 0.06 * np.sin(2 * np.pi * 3 * tt)
    whine = osc(f * 6 * (1 + 0.004 * np.sin(2 * np.pi * 2 * tt)), sec, ((1, 1.0), (2, 0.2)))
    whirr = lp(bandnoise(sec, 400, 1800), 2500) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 7 * tt)))
    x = 0.62 * buzz * rattle * flutter + 0.06 * whine + 0.08 * whirr
    return lp(drive(x * 1.4, 1.2), 4000)


s.save("engine_loop", loop(motor, 1.0), 0.5, fade=False)


def squeal(sec):
    """Tyre squeal: a wavering tone near 1.4 kHz over resonant band noise; modulations in whole cycles."""
    tt = t(sec)
    f = 1380 * (1 + 0.025 * np.sin(2 * np.pi * 5 * tt) + 0.012 * np.sin(2 * np.pi * 13 * tt + 1))
    tone = osc(f, sec, ((1, 1.0), (2, 0.35), (3, 0.12)))
    nb = lp(lp(bandnoise(sec, 900, 3000), 3000), 4000)
    nb = nb / (np.max(np.abs(nb)) + 1e-9)
    rough = 0.75 + 0.25 * np.sin(2 * np.pi * 9 * tt) * np.sin(2 * np.pi * 2 * tt)
    return lp((0.6 * tone * rough + 0.35 * nb) * (0.9 + 0.1 * np.sin(2 * np.pi * 3 * tt)), 6000)


s.save("skid_loop", loop(squeal, 1.0), 0.42, fade=False)

# ------------------------------------------------------------------ knocks

d = 0.5  # bump: a tin car clunks into a wall: a hollow tin strike over a soft thud, a short rattle
x = np.zeros(n(d))
mix(x, 0, 0.9 * clank(d, 1.0, 1.0, 0.9, 3500))
mix(x, 0, 0.7 * thump(160, 60, 0.12, 0.035))
mix(x, n(0.05), 0.25 * clank(0.2, 1.7, 0.4, 1.2, 6000), 0.15 * clank(0.2, 2.3, 0.3, 1.2, 7000))
save("bump", x, 0.55)

d = 1.3  # crash: a big tin clatter: a heavy strike, the shell bouncing and rattling, springs and loose bits settling
x = np.zeros(n(d))
mix(x, 0, 1.0 * clank(0.9, 0.8, 1.6, 1.0, 3000), 0.9 * thump(130, 42, 0.3, 0.09))
mix(x, 0, 0.35 * lp(s.noise(0.25), curve([(0, 6000), (0.25, 700)], 0.25)) * env(n(0.25), 0.001, 0.05, 3))
for k, (st, b, lv) in enumerate(((0.07, 1.25, 0.6), (0.15, 0.95, 0.5), (0.26, 1.5, 0.4), (0.4, 1.1, 0.3),
                                 (0.55, 1.8, 0.2), (0.66, 1.3, 0.16), (0.75, 2.2, 0.1))):
    mix(x, n(st), lv * clank(0.4, b, 0.7, 1.2, 5000))
mix(x, n(0.1), 0.18 * spring(520, 300, 0.6, 31, 0.2) * env(n(0.6), 0.005, 0.2, 3))
ratchet(x, 0.3, 9, 22, 0.12, 1.2)
save("crash", drive(x, 1.3), 0.62)

d = 0.4  # car_hit: two tin cars knocking: a bright double clank, one a touch higher
x = np.zeros(n(d))
mix(x, 0, 0.8 * clank(0.35, 1.3, 0.8, 1.1, 5000))
mix(x, n(0.028), 0.6 * clank(0.35, 1.62, 0.7, 1.1, 5000))
mix(x, 0, 0.4 * thump(220, 110, 0.06, 0.015))
save("car_hit", x, 0.5)

# ------------------------------------------------------------------ air

d = 0.6  # jump: a springy boing up off the ramp, a whoosh of air
x = np.zeros(n(d))
mix(x, 0, 0.42 * spring(260, 720, 0.45, 26, 0.1) * curve([(0, 0), (0.01, 1), (0.3, 0.6), (0.45, 0)], 0.45))
wh = bandnoise(0.5, 500, curve([(0, 1500), (0.5, 4500)], 0.5))
mix(x, n(0.02), 0.3 * wh * curve([(0, 0), (0.12, 1), (0.5, 0)], 0.5))
mix(x, 0, 0.5 * clank(0.12, 1.4, 0.4, 1.0, 5000))
save("jump", x, 0.5)

d = 0.5  # land: a tin thunk on the wheels, the springs bouncing once, a little rattle
x = np.zeros(n(d))
mix(x, 0, 0.85 * thump(140, 50, 0.2, 0.05), 0.6 * clank(0.4, 0.9, 0.8, 0.8, 3000))
mix(x, n(0.02), 0.18 * spring(300, 220, 0.3, 24, 0.25) * env(n(0.3), 0.004, 0.1, 3))
ratchet(x, 0.05, 4, 40, 0.1, 1.5)
save("land", x, 0.55)

# ------------------------------------------------------------------ the track

d = 0.8  # oil: a slippery squelch: a gloopy low bubble sliding down, a wet smear of noise
x = np.zeros(n(d))
tt = t(0.6)
fv = curve([(0, 340), (0.18, 520), (0.6, 140)], 0.6) * (1 + 0.08 * np.sin(2 * np.pi * 17 * tt))
gl = osc(fv, 0.6, ((1, 1.0), (2, 0.5), (3, 0.2)))
mix(x, 0, 0.45 * lp(gl, 1500) * curve([(0, 0), (0.03, 1), (0.6, 0)], 0.6))
for k in range(5):
    st = 0.02 + 0.09 * k + s.rng.uniform(0, 0.03)
    mix(x, n(st), 0.22 * osc(curve([(0, 220 + 60 * k), (0.06, 520 + 80 * k)], 0.07), 0.07)
        * env(n(0.07), 0.003, 0.03, 2.5))
mix(x, 0, 0.25 * lp(s.noise(0.7), curve([(0, 2500), (0.7, 400)], 0.7)) * curve([(0, 0), (0.05, 1), (0.7, 0)], 0.7))
save("oil", x, 0.5)

d = 0.9  # splash: a puddle splash: a burst of spray, then droplets plinking back down
x = np.zeros(n(d))
sp = lp(bandnoise(0.45, 400, curve([(0, 7000), (0.45, 1800)], 0.45)), 6000)
mix(x, 0, 0.6 * sp * curve([(0, 0), (0.01, 1), (0.08, 0.6), (0.45, 0)], 0.45))
mix(x, 0, 0.5 * thump(180, 70, 0.12, 0.03))
for k in range(9):
    st = 0.1 + 0.07 * k + s.rng.uniform(0, 0.04)
    f0 = s.rng.uniform(700, 1500)
    mix(x, n(st), 0.16 * (1 - k / 10) * osc(curve([(0, f0), (0.05, f0 * 2.2)], 0.05), 0.05)
        * env(n(0.05), 0.001, 0.02, 2.5))
save("splash", x, 0.5)

d = 1.0  # wrench: the pickup: a clink of steel and a bright little G major sparkle upwards
x = np.zeros(n(d))
mix(x, 0, 0.45 * clank(0.3, 3.2, 0.9, 1.5, 9000))
for k, m in enumerate((79, 83, 86, 91)):
    mix(x, n(0.04 + 0.06 * k), 0.3 * fmbell(m2f(m), 0.6, 3.5, 1.2, 0.18 + 0.04 * k))
mix(x, n(0.22), 0.14 * fmbell(m2f(98), 0.6, 2.0, 0.8, 0.25))
save("wrench", x, 0.5)

# ------------------------------------------------------------------ race control

d = 0.3  # countdown_beep: a round square-wave beep on D6
tone = sq(m2f(86), 0.22, 9) * np.clip((0.22 - t(0.22)) / 0.03, 0, 1) * np.clip(t(0.22) / 0.004, 0, 1)
x = np.zeros(n(d))
mix(x, 0, 0.5 * lp(tone, 5000), 0.2 * fmbell(m2f(98), 0.25, 2.0, 0.6, 0.06))
save("countdown_beep", x, 0.5)

d = 0.8  # go_beep: the same voice an octave-and-a-fourth up on G6, longer, with a bell on top
tone = sq(m2f(91), 0.6, 9) * np.clip((0.6 - t(0.6)) / 0.12, 0, 1) * np.clip(t(0.6) / 0.004, 0, 1)
x = np.zeros(n(d))
mix(x, 0, 0.5 * lp(tone, 6000), 0.15 * sq(m2f(79), 0.6, 7) * np.clip((0.6 - t(0.6)) / 0.12, 0, 1),
    0.25 * fmbell(m2f(103), 0.7, 2.0, 1.0, 0.2))
save("go_beep", x, 0.55)

d = 1.1  # lap: a ding: a bright bell on G6 with a D7 shimmer
x = np.zeros(n(d))
mix(x, 0, 0.5 * fmbell(m2f(91), 1.1, 3.5, 1.6, 0.35), 0.22 * fmbell(m2f(98), 1.0, 2.0, 0.8, 0.25),
    0.1 * fmbell(m2f(103), 0.8, 2.0, 0.6, 0.15))
save("lap", x, 0.5)

d = 1.6  # final_lap: a short bell phrase: ding-ding-ding, then a ringing high G
x = np.zeros(n(d))
for k, (st, m, ln) in enumerate(((0.0, 86, 0.4), (0.13, 86, 0.4), (0.26, 86, 0.4), (0.42, 91, 1.1))):
    mix(x, n(st), 0.42 * fmbell(m2f(m), ln, 3.5, 1.5, 0.12 if k < 3 else 0.4),
        0.15 * fmbell(m2f(m + 12), ln, 2.0, 0.7, 0.1 if k < 3 else 0.3))
mix(x, n(0.42), 0.08 * brass(m2f(67), 0.8, 0.02, 0.5), 0.07 * brass(m2f(71), 0.8, 0.02, 0.5),
    0.07 * brass(m2f(74), 0.8, 0.02, 0.5))
save("final_lap", x, 0.55)

d = 2.8  # finish: the chequered flag: a snare roll, a bright brass fanfare in G with glockenspiel, a cymbal swell
x = np.zeros(n(d))
for k in range(16):   # the roll into it
    st = 0.025 * k
    mix(x, n(st), (0.08 + 0.015 * k) * bandnoise(0.03, 1500, 7000) * env(n(0.03), 0.001, 0.01, 3))
for m, st, ln in ((67, 0.4, 0.12), (71, 0.53, 0.12), (74, 0.66, 0.12), (79, 0.79, 0.32), (74, 1.13, 0.12),
                  (79, 1.27, 1.0)):
    mix(x, n(st), 0.2 * brass(m2f(m), ln + 0.05, 0.01, 0.06), 0.1 * brass(m2f(m - 12), ln + 0.05, 0.01, 0.06),
        0.12 * fmbell(m2f(m + 12), 0.5, 3.5, 1.2, 0.15))
for m in (55, 62, 67, 71, 74):
    mix(x, n(1.27), 0.07 * brass(m2f(m), 1.4, 0.03, 0.8, 2800))
mix(x, n(1.27), 0.5 * thump(110, 45, 0.35, 0.1),
    0.18 * bandnoise(1.3, 4000, 12000) * curve([(0, 1), (1.3, 0)], 1.3))
save("finish", drive(x, 1.3), 0.62)

d = 1.5  # upgrade: the shop: a wind-up key cranked (ratchet clicks rising), then a cheerful bell ka-ching
x = np.zeros(n(d))
for k in range(10):
    mix(x, n(0.04 * k), (0.25 + 0.02 * k) * clank(0.06, 2.4 + 0.08 * k, 0.4, 1.4, 7000))
mix(x, n(0.42), 0.4 * clank(0.3, 3.0, 1.2, 1.6, 9000))
for k, m in enumerate((79, 86, 91)):
    mix(x, n(0.45 + 0.05 * k), 0.3 * fmbell(m2f(m), 0.9, 3.5, 1.4, 0.3))
save("upgrade", x, 0.55)

d = 3.4  # win: a jaunty victory jingle in G: glockenspiel and brass, a wind-up whirr of joy, the last chord ringing
x = np.zeros(n(d))
tune = ((79, 0.0, 0.14), (83, 0.15, 0.14), (86, 0.3, 0.14), (91, 0.45, 0.3), (88, 0.8, 0.14), (91, 0.95, 0.14),
        (93, 1.1, 0.14), (95, 1.25, 0.9))
for m, st, ln in tune:
    mix(x, n(st), 0.16 * brass(m2f(m - 12), ln + 0.05, 0.01, 0.06), 0.18 * fmbell(m2f(m), 0.6, 3.5, 1.3, 0.2))
for st, ch in ((0.0, (55, 59, 62)), (0.45, (55, 59, 62)), (0.8, (60, 64, 67)), (1.1, (62, 66, 69)),
               (1.25, (55, 59, 62, 67))):
    for m in ch:
        mix(x, n(st), 0.06 * brass(m2f(m), 0.3 if st < 1.2 else 1.9, 0.01, 0.1 if st < 1.2 else 1.0, 2500))
    mix(x, n(st), 0.3 * thump(120, 50, 0.2, 0.06))
mix(x, n(1.25), 0.12 * bandnoise(1.6, 5000, 12000) * curve([(0, 1), (1.6, 0)], 1.6))
whirr = lp(saw(curve([(0, 150), (0.5, 420)], 0.5), 0.5, 12), 2000) * curve([(0, 0), (0.1, 1), (0.5, 0)], 0.5)
mix(x, n(1.25), 0.12 * whirr)
save("win", drive(x, 1.2), 0.62)

d = 3.0  # lose: the clockwork runs down: the motor whirr slowing and dropping, a few lazy clicks, a wistful line down
x = np.zeros(n(d))
sec = 1.6
fv = curve([(0, 196), (1.6, 55)], sec)
wd = lp(saw(fv, sec, 16) + 0.6 * saw(fv * 1.006, sec, 16), curve([(0, 1800), (1.6, 500)], sec))
mix(x, 0, 0.3 * wd * curve([(0, 1), (1.2, 0.6), (1.6, 0)], sec) * (0.75 + 0.25 * np.abs(np.sin(np.cumsum(fv) * np.pi
                                                                                                 / SR * 0.07))))
for k, st in enumerate((0.3, 0.55, 0.85, 1.2, 1.6, 2.05)):
    mix(x, n(st), 0.22 * clank(0.08, 2.4, 0.4, 1.4, 7000))
for m, st, ln in ((74, 0.1, 0.4), (72, 0.55, 0.4), (71, 1.0, 0.4), (69, 1.45, 0.4), (67, 1.9, 1.0)):
    v = fmbell(m2f(m), ln + 0.4, 3.5, 1.0, 0.3)
    mix(x, n(st), 0.2 * v, 0.06 * brass(m2f(m - 12), ln, 0.03, 0.2, 1200))
save("lose", x, 0.55)
