#!/usr/bin/env python3
"""Sound effects for game 30 (Ridgefire), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any artillery game: little tanks lobbing shells over hills, made of
swept sines (thumps, whistles), filtered noise with moving cut-offs (blasts, rumbles, wind, earth), inharmonic
resonant modes (metal clangs, clicks), FM bells (chimes, the till) and soft synth brass (fanfares). The jingles sit
in B flat major, the key of tools/audio/ridgefire_music.py.
- whistle is a falling shell's whistle, 1.5 s, to be pitched by the game (pitch_scale) and cut when the shell lands.
- aim_tick and power_tick are tiny clicks for repeating while a value changes (the game may pitch power_tick with the
  power: pitch_scale = 0.8 + 0.6 * power / max).
- roller (2.0 s) and wind (4.0 s) are seamless loops (the noise is cross-faded end into start, every modulation
  completes whole cycles), mastered at steady levels so the game can fade them in and out.
No voices anywhere.
Usage: python3 tools/audio/ridgefire_sfx.py [out_dir]   (default: godot/games/ridgefire/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/ridgefire/audio/sfx", seed=3030)
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


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def taper(m, frac=0.25):
    """A gain curve of m samples: flat, then a raised-cosine fade to zero over the last `frac` (no end clicks)."""
    g = np.ones(m)
    k = max(1, int(m * frac))
    g[-k:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, k))
    return g


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude)."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 2.0))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec) * taper(len(ir_t))
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
    return np.sin(2 * np.pi * f * tt + index * e * np.sin(2 * np.pi * f * ratio * tt)) * e * taper(len(tt))


def brass(f, sec, attack=0.03, release=0.15, bright=3500):
    """A soft synth brass: two detuned saws through a filter that opens on the attack."""
    tt = t(sec)
    x = saw(f * 0.997, sec, 20) + saw(f * 1.003, sec, 20)
    cut = 600 + bright * (1 - np.exp(-tt / 0.06)) * (0.75 + 0.25 * np.exp(-tt / 0.3))
    e = np.clip(tt / attack, 0, 1) * np.clip((sec - tt) / release, 0, 1)
    return lp(x, cut) * e


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def loop(make, sec, fade=0.3):
    """A seamless loop: renders sec + fade, then cross-fades the overhang into the start (equal power)."""
    x = make(sec + fade)
    L, F = n(sec), n(fade)
    y = x[:L].copy()
    a = np.linspace(0, np.pi / 2, F)
    y[:F] = y[:F] * np.sin(a) + x[L:L + F] * np.cos(a)
    return y


def crackle(sec, rate, bright=7000, size=0.003):
    """Random tiny pops of filtered noise, `rate` per second (debris, grit, fire)."""
    x = np.zeros(n(sec))
    for i in s.rng.integers(0, max(1, len(x) - n(size)), int(rate * sec)):
        m = n(size * s.rng.uniform(0.4, 1.4))
        x[i:i + m] += s.rng.uniform(-1, 1) * s.rng.uniform(0.3, 1.0) * env(m, 0.0002, size / 4, 3)[:len(x) - i]
    return lp(x, bright)


def rumble(sec, cut, rolls=0.0, seed_rate=3.0):
    """Low rolling noise: noise through two low-passes (cut may be a curve), swelling in slow random rolls."""
    x = lp(lp(s.noise(sec), cut), cut)
    x = x / (np.max(np.abs(x)) + 1e-9)
    if rolls:
        k = max(2, int(sec * seed_rate))
        g = np.interp(t(sec), np.linspace(0, sec, k), s.rng.uniform(1 - rolls, 1.0, k))
        x *= lp(g, 6.0)
    return x


def blast(sec, size=1.0, bright=6000):
    """The body of an explosion: a sharp crack, a pitched-down thump, a noise burst darkening as it decays."""
    x = np.zeros(n(sec))
    mix(x, 0, 0.6 * lp(s.noise(0.012), 9000) * env(n(0.012), 0.0002, 0.003, 3))
    mix(x, 0, 1.0 * thump(95 / size ** 0.3, 28, min(sec, 0.9 * size), 0.22 * size))
    nb = s.noise(sec)
    cut = curve([(0, bright), (0.05 * size, bright * 0.6), (0.4 * size, 900), (sec, 160)], sec)
    mix(x, 0, 0.75 * lp(nb, cut) * curve([(0, 0), (0.004, 1), (0.12 * size, 0.55), (sec, 0)], sec) ** 1.5)
    return x


def debris(x, start, sec, count, lo=0.02, hi=0.12, level=0.25):
    """Clods and grit falling back: small low thuds and pats, spread and thinning out over `sec`."""
    for k in range(count):
        u = s.rng.uniform(0, 1) ** 1.6
        st = start + sec * u
        d = s.rng.uniform(0.04, 0.12)
        f = s.rng.uniform(70, 160)
        mix(x, n(st), level * (1 - 0.6 * u) * s.rng.uniform(0.4, 1.0) * thump(f * 1.6, f, d, d / 3))
        mix(x, n(st), level * 0.4 * (1 - 0.6 * u) * lp(s.noise(d), s.rng.uniform(1200, 3000)) * env(n(d), 0.001,
                                                                                                    d / 4, 3))


def snare_roll(sec, rate=22, start_level=0.3, end_level=1.0):
    """A snare roll: fast noise taps with a drum-head body, crescendo from start_level to end_level."""
    x = np.zeros(n(sec) + n(0.1))
    k = 0
    while k / rate < sec:
        u = k / rate / sec
        lv = start_level + (end_level - start_level) * u
        tap = bandnoise(0.06, 1500, 7000) * env(n(0.06), 0.0005, 0.02, 3) + 0.5 * thump(240, 180, 0.06, 0.02)
        mix(x, n(k / rate + s.rng.uniform(0, 0.004)), lv * s.rng.uniform(0.8, 1.0) * tap)
        k += 1
    return x


def snare_hit(level=1.0):
    return level * (bandnoise(0.2, 1200, 8000) * env(n(0.2), 0.0005, 0.06, 3) + 0.7 * thump(230, 160, 0.2, 0.04))


def cymbal(sec, level=1.0):
    x = bandnoise(sec, 3000, 12000) * env(n(sec), 0.002, sec / 2.5, 3)
    tt = t(sec)
    ring = sum(np.sin(2 * np.pi * f * tt) for f in (3170, 4420, 5310, 6870)) * np.exp(-tt / (sec / 3))
    return level * (x + 0.05 * ring)


# ------------------------------------------------------------------ firing

d = 1.4  # fire: a cannon thump: the crack, a deep pitched-down boom, a short ring of the barrel, a puff
x = np.zeros(n(d))
mix(x, 0, 0.7 * lp(s.noise(0.015), 8000) * env(n(0.015), 0.0002, 0.004, 3))
mix(x, 0, 1.0 * thump(150, 38, 0.7, 0.16))
mix(x, 0, 0.55 * lp(s.noise(0.9), curve([(0, 5000), (0.08, 1800), (0.9, 250)], 0.9))
    * curve([(0, 0), (0.003, 1), (0.1, 0.5), (0.9, 0)], 0.9) ** 1.6)
ex = np.r_[click(0.003, 7000), np.zeros(n(0.6))]
mix(x, n(0.005), 0.18 * resonate(ex, ((610, 0.12, 1.0), (1515, 0.08, 0.6), (2730, 0.05, 0.35))))
mix(x, n(0.03), 0.3 * rumble(1.2, 120) * curve([(0, 0), (0.05, 1), (1.2, 0)], 1.2) ** 2)
save("fire", drive(x, 1.6), 0.7)

d = 2.4  # fire_big: a heavier charge: a double crack, a longer deeper boom, the ground shaking under it
x = np.zeros(n(d))
for st, lv in ((0.0, 0.8), (0.022, 0.5)):
    mix(x, n(st), lv * lp(s.noise(0.02), 9000) * env(n(0.02), 0.0002, 0.005, 3))
mix(x, 0, 1.0 * thump(120, 26, 1.3, 0.3))
mix(x, 0, 0.7 * lp(s.noise(1.5), curve([(0, 6000), (0.1, 2200), (1.5, 160)], 1.5))
    * curve([(0, 0), (0.003, 1), (0.18, 0.55), (1.5, 0)], 1.5) ** 1.5)
mix(x, n(0.02), 0.55 * rumble(2.2, curve([(0, 160), (2.2, 70)], 2.2), 0.5) * curve([(0, 0), (0.08, 1), (2.2, 0)],
                                                                                     2.2) ** 1.6)
ex = np.r_[click(0.004, 6000), np.zeros(n(0.9))]
mix(x, n(0.01), 0.14 * resonate(ex, ((430, 0.18, 1.0), (1180, 0.12, 0.6), (2050, 0.07, 0.3))))
save("fire_big", drive(x, 1.8), 0.75)

d = 1.5  # whistle: a falling shell: a thin whistle gliding down, a little vibrato, air rushing, louder as it nears
fv = curve([(0, 2350), (0.3, 2150), (1.5, 820)], d) * (1 + 0.012 * np.sin(2 * np.pi * 7.5 * t(d)))
amp = curve([(0, 0), (0.15, 0.35), (1.1, 0.85), (1.45, 1.0), (1.5, 0.0)], d)
x = 0.5 * osc(fv, d, ((1, 1.0), (2, 0.05), (3, 0.015))) * amp
air = bandnoise(d, curve([(0, 2500), (1.5, 900)], d), curve([(0, 6000), (1.5, 2800)], d))
x += 0.18 * air * amp
s.save("whistle", x, 0.5)

d = 0.8  # mirv_split: the warhead cracks open: a sharp pop, a metallic clink, three short whistles diverging
x = np.zeros(n(d))
mix(x, 0, 0.7 * lp(s.noise(0.02), 7000) * env(n(0.02), 0.0003, 0.006, 3), 0.6 * thump(300, 90, 0.1, 0.025))
ex = np.r_[click(0.002, 9000), np.zeros(n(0.3))]
mix(x, 0, 0.22 * resonate(ex, ((2350, 0.05, 1.0), (3710, 0.03, 0.6), (5210, 0.02, 0.3))))
for k, (f0, f1) in enumerate(((2000, 1300), (2300, 2600), (1700, 980))):
    sec = 0.55
    fv = curve([(0, f0), (sec, f1)], sec) * (1 + 0.01 * np.sin(2 * np.pi * (6 + k) * t(sec)))
    mix(x, n(0.03 + 0.02 * k), 0.16 * osc(fv, sec) * curve([(0, 0), (0.04, 1), (sec, 0)], sec))
mix(x, n(0.01), 0.15 * bandnoise(0.5, 2500, 8000) * curve([(0, 1), (0.5, 0)], 0.5) ** 2)
save("mirv_split", x, 0.55)

# ------------------------------------------------------------------ explosions

d = 1.3  # boom_small: a small shell bursting: crack, thump, a short dirt spray
x = blast(d, 0.6, 5000)
debris(x, 0.12, 0.9, 10, level=0.18)
mix(x, n(0.02), 0.25 * crackle(0.5, 120, 5000) * curve([(0, 1), (0.5, 0)], 0.5))
save("boom_small", drive(x, 1.6), 0.65)

d = 3.4  # boom: a big blast: crack, a heavy thump, a roar darkening into a long rumble, clods coming down
x = blast(d, 1.4, 7000)
mix(x, n(0.03), 0.8 * rumble(3.3, curve([(0, 220), (3.3, 60)], 3.3), 0.6) * curve([(0, 0), (0.1, 1), (0.8, 0.7),
                                                                                     (3.3, 0)], 3.3) ** 1.4)
debris(x, 0.25, 1.8, 26, level=0.2)
mix(x, n(0.02), 0.25 * crackle(1.0, 140, 4500) * curve([(0, 1), (1.0, 0)], 1.0))
save("boom", drive(x, 2.0), 0.8)

d = 7.0  # nuke: a huge, long, rolling explosion: a flash crack, a sub thump, a roar that swells, the rolls of thunder
x = np.zeros(n(d))
mix(x, 0, 0.9 * lp(s.noise(0.02), 10000) * env(n(0.02), 0.0002, 0.006, 3))
mix(x, 0, 1.0 * thump(70, 18, 2.5, 0.7))
roar = lp(s.noise(5.5), curve([(0, 3000), (0.5, 2400), (1.4, 1200), (5.5, 120)], 5.5))
mix(x, n(0.02), 0.8 * roar * curve([(0, 0.4), (0.05, 1), (0.6, 0.85), (1.5, 0.75), (5.5, 0)], 5.5) ** 1.3)
rb = rumble(6.6, curve([(0, 200), (6.6, 55)], 6.6), 0.75, 1.6)
mix(x, n(0.2), 1.0 * rb * curve([(0, 0), (0.6, 1), (3.0, 0.75), (6.6, 0)], 6.6) ** 1.2)
mix(x, n(0.65), 0.6 * thump(55, 22, 1.5, 0.45))      # the second wave
for st in (1.6, 2.5, 3.6):                           # rolls echoing back off the hills
    mix(x, n(st), 0.35 * lp(rumble(1.4, 140), 300) * curve([(0, 0), (0.25, 1), (1.4, 0)], 1.4) ** 1.5)
debris(x, 0.5, 3.0, 40, level=0.16)
mix(x, n(0.05), 0.2 * crackle(2.5, 100, 4000) * curve([(0, 1), (2.5, 0)], 2.5))
save("nuke", drive(x, 2.4), 0.85)

d = 1.4  # dirt: earth thudding down after a blast: soft heavy thuds, clods, a trickle of grit
x = np.zeros(n(d))
for st, f, lv in ((0.0, 90, 0.9), (0.09, 75, 0.7), (0.21, 110, 0.6), (0.34, 80, 0.5)):
    mix(x, n(st), lv * thump(f * 1.5, f * 0.7, 0.25, 0.07))
    mix(x, n(st), lv * 0.5 * lp(s.noise(0.2), 1400) * env(n(0.2), 0.002, 0.05, 3))
debris(x, 0.05, 0.9, 18, level=0.22)
grit = crackle(1.2, 300, 6000, 0.002) * curve([(0, 0), (0.1, 1), (0.5, 0.6), (1.2, 0)], 1.2)
mix(x, n(0.08), 0.3 * grit, 0.12 * bandnoise(1.1, 1500, 6000) * curve([(0, 0), (0.1, 1), (1.1, 0)], 1.1) ** 2)
save("dirt", x, 0.6)

d = 2.8  # tank_die: a tank breaking apart: a blast, plates ringing and clattering down, a crunch, a last pop
x = blast(d, 1.1, 6500)
ex = np.r_[click(0.004, 6000), np.zeros(n(2.0))]
mix(x, n(0.02), 0.2 * resonate(ex, ((310, 0.4, 1.0), (787, 0.3, 0.7), (1423, 0.2, 0.5), (2231, 0.12, 0.35),
                                    (3302, 0.08, 0.2))))
for k in range(9):   # plates and bolts landing: short clanks at random pitches
    st = 0.35 + 1.6 * (k / 9) ** 1.3 + s.rng.uniform(0, 0.05)
    f = s.rng.uniform(500, 1700)
    exk = np.r_[click(0.002, 8000), np.zeros(n(0.35))]
    mix(x, n(st), 0.12 * (1 - 0.5 * k / 9) * resonate(exk, ((f, 0.06, 1.0), (f * 2.41, 0.04, 0.6),
                                                            (f * 3.93, 0.025, 0.4))))
mix(x, n(0.06), 0.35 * crackle(0.4, 220, 5000) * curve([(0, 1), (0.4, 0)], 0.4))
mix(x, n(0.05), 0.6 * rumble(2.4, 150, 0.5) * curve([(0, 0), (0.1, 1), (2.4, 0)], 2.4) ** 1.6)
mix(x, n(1.9), 0.35 * thump(160, 60, 0.25, 0.06), 0.2 * lp(s.noise(0.2), 2500) * env(n(0.2), 0.001, 0.04, 3))
save("tank_die", drive(x, 1.8), 0.8)

d = 1.2  # hit_tank: a shell glancing off armour: a hard clang (inharmonic plate modes), a low knock
x = np.zeros(n(d))
ex = np.r_[click(0.003, 9000), np.zeros(n(d) - n(0.003))]
mix(x, 0, 0.8 * resonate(ex, ((523, 0.28, 1.0), (1287, 0.2, 0.7), (1931, 0.14, 0.55), (2766, 0.1, 0.4),
                              (4113, 0.06, 0.25), (5480, 0.04, 0.15))))
mix(x, 0, 0.5 * thump(180, 70, 0.15, 0.04))
mix(x, 0, 0.25 * bandnoise(0.08, 2000, 9000) * env(n(0.08), 0.0005, 0.02, 3))
save("hit_tank", drive(x, 1.4), 0.65)

# ------------------------------------------------------------------ the special shells


def roller_loop(sec):
    """An iron ball rolling over rough ground: a low rumble, spikes biting 8 times a second, grit."""
    tt = t(sec)
    base = 1 / 2.0
    x = 0.8 * rumble(sec, 180) * (0.85 + 0.15 * np.sin(2 * np.pi * 2 * base * tt))
    bite = np.zeros(n(sec))
    rate = 8.0
    for k in range(int(sec * rate) + 1):
        st = k / rate + s.rng.uniform(-0.006, 0.006)
        if st < 0:
            continue
        lv = 0.6 + 0.4 * s.rng.uniform()
        mix(bite, n(st), lv * 0.6 * thump(140, 70, 0.07, 0.02),
            lv * 0.25 * lp(s.noise(0.04), 2200) * env(n(0.04), 0.001, 0.012, 3))
    x += bite
    x += 0.12 * crackle(sec, 90, 4500)
    return lp(x, 2500)


s.save("roller", loop(roller_loop, 2.0, 0.2), 0.55, fade=False)

d = 1.5  # dig: a drill shell boring in: a whining motor, a grinding buzz through earth, chips of stone
tt = t(d)
x = np.zeros(n(d))
mf = curve([(0, 90), (0.15, 150), (1.3, 140), (1.5, 100)], d) * (1 + 0.04 * np.sin(2 * np.pi * 11 * tt))
buzz = lp(saw(mf, d, 30), 1800) * curve([(0, 0), (0.05, 1), (1.3, 0.9), (1.5, 0)], d)
whine = osc(mf * 7.02, d, ((1, 1.0), (2, 0.2))) * curve([(0, 0), (0.1, 0.5), (1.3, 0.5), (1.5, 0)], d)
grind = bandnoise(d, 400, 3000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * mf * 0.5 * tt)))
mix(x, 0, 0.45 * drive(buzz, 2.5), 0.08 * whine, 0.3 * grind * curve([(0, 0), (0.1, 1), (1.3, 0.8), (1.5, 0)], d))
mix(x, 0, 0.3 * crackle(1.4, 160, 5000, 0.004))
debris(x, 0.1, 1.2, 10, level=0.12)
save("dig", x, 0.42)

# ------------------------------------------------------------------ interface


def tick(f, sec, bright, level):
    ex = np.r_[click(0.0015, bright), np.zeros(n(sec))]
    return level * resonate(ex, ((f, 0.008, 1.0), (f * 2.7, 0.005, 0.4)))


x = tick(2300, 0.05, 6000, 1.0)   # aim_tick: a soft ratchet click as the barrel steps
save("aim_tick", x, 0.3)

x = tick(1350, 0.06, 4000, 1.0)   # power_tick: a woodier tick a fifth lower (pitch it with the power)
mix(x, 0, 0.3 * thump(700, 500, 0.03, 0.008))
save("power_tick", x, 0.3)

d = 1.1  # buy: a shop till of our own: a lever clunk, a drawer sliding, two bell dings and a jingle of coins
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(220, 110, 0.06, 0.015), 0.3 * lp(s.noise(0.03), 3000) * env(n(0.03), 0.0005, 0.008, 3))
ex = np.r_[click(0.002, 6000), np.zeros(n(0.2))]
mix(x, n(0.0), 0.2 * resonate(ex, ((1200, 0.02, 1.0), (2900, 0.012, 0.5))))
mix(x, n(0.07), 0.18 * bandnoise(0.12, 800, 3000) * curve([(0, 0), (0.03, 1), (0.12, 0)], 0.12))
mix(x, n(0.12), 0.45 * fmbell(m2f(89), 0.8, 3.5, 1.5, 0.3), 0.35 * fmbell(m2f(94), 0.8, 3.5, 1.4, 0.35)[:n(0.8)])
for k in range(7):   # coins
    st = 0.15 + 0.035 * k + s.rng.uniform(0, 0.02)
    f = s.rng.uniform(4200, 6800)
    mix(x, n(st), 0.1 * fmbell(f, 0.12, 1.41, 0.6, 0.03))
save("buy", x, 0.5)

d = 0.9  # turn: a short chime for whose turn it is: F then B flat, a soft octave glint
x = np.zeros(n(d))
mix(x, 0, 0.35 * fmbell(m2f(77), 0.6, 2.0, 1.0, 0.2))
mix(x, n(0.11), 0.45 * fmbell(m2f(82), 0.75, 2.0, 1.1, 0.3), 0.12 * fmbell(m2f(94), 0.6, 3.01, 0.8, 0.15))
save("turn", x, 0.45)


def wind_loop(sec):
    """A soft hilltop wind: band noise in two layers, swelling in gusts (whole cycles over 4 s), a faint whistle."""
    tt = t(sec)
    base = 1 / 4.0
    gust = 0.55 + 0.25 * np.sin(2 * np.pi * base * tt) + 0.2 * np.sin(2 * np.pi * 3 * base * tt + 1.0)
    lo = lp(lp(s.noise(sec), 500 + 350 * gust), 700)
    lo /= np.max(np.abs(lo)) + 1e-9
    hi = bandnoise(sec, 700, 1600 + 1400 * gust)
    hi /= np.max(np.abs(hi)) + 1e-9
    whist = osc(820 + 160 * np.sin(2 * np.pi * 2 * base * tt), sec) * 0.5 * (gust - 0.3).clip(0, None)
    x = 0.85 * lo * (0.6 + 0.4 * gust) + 0.2 * hi * gust ** 2 + 0.03 * whist
    return lp(x, 3500)


s.save("wind", loop(wind_loop, 4.0, 0.4), 0.45, fade=False)

# ------------------------------------------------------------------ jingles (B flat major)

d = 2.7  # win: a short brass fanfare: a triplet pick-up into B flat, up to the high B flat, a held chord, a cymbal
x = np.zeros(n(d))
line = ((65, 0.0, 0.11), (65, 0.12, 0.11), (65, 0.24, 0.11), (70, 0.36, 0.3), (74, 0.7, 0.14), (77, 0.86, 0.14),
        (82, 1.02, 1.5))
for m, st, ln in line:
    rel = 0.6 if ln > 1 else 0.06
    mix(x, n(st), 0.22 * brass(m2f(m), ln + 0.05, 0.012, rel), 0.1 * brass(m2f(m - 12), ln + 0.05, 0.012, rel))
for m in (46, 58, 62, 65, 70, 74, 77):
    mix(x, n(1.02), 0.08 * brass(m2f(m), 1.55, 0.02, 0.6, 2800))
mix(x, n(0.36), 0.35 * snare_hit(0.9), 0.5 * thump(110, 50, 0.3, 0.08))
mix(x, n(1.02), 0.4 * snare_roll(0.9, 24, 0.3, 0.5)[:n(0.9)], 0.7 * thump(100, 45, 0.5, 0.12),
    0.3 * cymbal(1.6))
save("win", drive(x, 1.3), 0.7)

d = 1.9  # round_start: a snare roll swelling, then a brass stab on B flat with the bass drum and a cymbal
x = np.zeros(n(d))
mix(x, 0, 0.45 * snare_roll(0.8, 24, 0.2, 1.0))
for m in (46, 58, 62, 65, 70):
    mix(x, n(0.82), 0.12 * brass(m2f(m), 0.5, 0.01, 0.3, 3500))
mix(x, n(0.82), 0.8 * thump(100, 42, 0.5, 0.12), 0.45 * snare_hit(1.0), 0.35 * cymbal(1.0))
save("round_start", drive(x, 1.3), 0.65)
