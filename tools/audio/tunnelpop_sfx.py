#!/usr/bin/env python3
"""Sound effects for game 32 (Tunnel Pop), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any arcade game: a mole-kid miner in garden earth with a brass hand
pump, made of filtered noise with moving cut-offs (soil, air, flame, rumbles), swept sines (thumps, twangs, the
whistle of a falling rock), damped resonant modes (wood ticks, pebbles, the pump's brass), FM bells (sparkles,
chimes) and plucked-mallet tones (jingles). The jingles sit in F major, the key of tools/audio/tunnelpop_music.py.
- walk_loop (1.0 s, four light taps and two wood ticks) and dig_loop (1.2 s, crunching soil) are seamless loops (any
  noise is cross-faded end into start, every modulation completes whole cycles), mastered at steady levels so the
  game can fade them in and out (about 0.08 s) as the hero starts and stops.
- pump is one squeeze at neutral pitch (0.27 s); the game climbs it over the four steps, e.g.
  pitch_scale = 2 ** (step * 3 / 12) for step 0..3 (a minor third a step), and plays pop on the last.
- rock_fall is a falling whistle and rumble (0.7 s) that fades by itself; the game may cut it when rock_land plays.
- last_one is a one-shot sting: start the hurry music when it ends (or when it is half done).
No voices anywhere.
Usage: python3 tools/audio/tunnelpop_sfx.py [out_dir]   (default: godot/games/tunnelpop/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/tunnelpop/audio/sfx", seed=3232)
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


def mallet(f, sec, decay=0.35, partials=((1, 1.0), (3.93, 0.25), (9.2, 0.06))):
    """A marimba-like bar: a few inharmonic partials, the upper ones dying fast, a soft knock on the attack."""
    tt = t(sec)
    x = sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * r ** 0.7 / decay) for r, a in partials)
    return x * np.clip(tt / 0.002, 0, 1)


def pluck(f, sec, decay=0.3, bright=8):
    """A plucked string: harmonics 1/k, the higher ones fading faster (a cheap Karplus-Strong look-alike)."""
    tt = t(sec)
    x = sum(np.sin(2 * np.pi * f * k * tt) / k * np.exp(-tt * (1 + 0.6 * k) / decay) for k in range(1, bright + 1))
    return x * np.clip(tt / 0.0015, 0, 1)


def wood(level=1.0, hi=True):
    """A small wood-block tick."""
    ex = np.r_[click(0.002, 7000), np.zeros(n(0.08))]
    modes = ((1250, 0.018, 1.0), (2750, 0.01, 0.4)) if hi else ((880, 0.022, 1.0), (1980, 0.012, 0.4))
    return level * resonate(ex, modes)


def loop(make, sec, fade=0.2):
    """A seamless loop: renders sec + fade, then cross-fades the overhang into the start (equal power)."""
    L, F = n(sec), n(fade)
    x = make(sec + fade + 0.01)
    y = x[:L].copy()
    a = np.linspace(0, np.pi / 2, F)
    y[:F] = y[:F] * np.sin(a) + x[L:L + F] * np.cos(a)
    return y


def crackle(sec, rate, bright=7000, size=0.003):
    """Random tiny pops of filtered noise, `rate` per second (soil grains, confetti fizz, flame sparks)."""
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
        mix(x, n(st), level * (1 - 0.7 * u) * s.rng.uniform(0.5, 1.0)
            * fmbell(s.rng.uniform(lo, hi), 0.14, s.rng.uniform(1.4, 2.8), 1.0, s.rng.uniform(0.015, 0.04)))


def pebbles(x, start, sec, count, level=0.2):
    """Little stones dribbling: short knocks through random stony modes, spread over `sec`, getting softer."""
    for k in range(count):
        u = k / max(1, count - 1)
        st = start + sec * u + s.rng.uniform(-0.02, 0.03)
        f = s.rng.uniform(1600, 3800)
        ex = np.r_[click(0.0015, 8000), np.zeros(n(0.05))]
        mix(x, max(0, n(st)), level * (1 - 0.5 * u) * s.rng.uniform(0.5, 1.0)
            * resonate(ex, ((f, 0.008, 1.0), (f * 1.7, 0.005, 0.5))))


def drive(x, k=2.0):
    return np.tanh(k * x) / np.tanh(k)


def outro(x, sec):
    """Fades the last `sec` of a jingle, so a ringing chord ends gently instead of being cut."""
    m = n(sec)
    x[-m:] *= np.linspace(1, 0, m) ** 1.5
    return x


# ------------------------------------------------------------------ the miner: walking and digging

def walk(sec):
    """Four soft taps a second on packed earth (left a touch lower than right), a little wood tick on two of them."""
    x = np.zeros(n(sec))
    for k in range(int(round(sec * 4)) + 1):
        st = n(k * 0.25 + 0.012)
        lo = 1.0 if k % 2 == 0 else 1.12
        mix(x, st, 0.55 * thump(170 * lo, 85 * lo, 0.07, 0.016))
        mix(x, st, 0.35 * lp(s.noise(0.035), 2200 * lo) * env(n(0.035), 0.0006, 0.008, 3))
        mix(x, st, 0.08 * bandnoise(0.05, 1500, 5000) * env(n(0.05), 0.002, 0.012, 3))
        if k % 2 == 1:
            mix(x, st + n(0.006), wood(0.12, hi=k % 4 == 1))
    return x


s.save("walk_loop", loop(walk, 1.0, 0.01), 0.5, fade=False)


def dig(sec):
    """Crunching soil: dense grains of low crackle, a scraping band of noise pulsing five times a second, a low
    rumble of moving earth, and every 0.3 s a crumbling clod."""
    tt = t(sec)
    pulse = 0.55 + 0.45 * np.sin(2 * np.pi * 5 * tt) ** 2
    grains = crackle(sec, 900, 2600, 0.004)
    grains = grains / (np.max(np.abs(grains)) + 1e-9)
    scrape = bandnoise(sec, 500, 2400 + 600 * np.sin(2 * np.pi * 2.5 * tt))
    scrape = scrape / (np.max(np.abs(scrape)) + 1e-9)
    rumble = lp(lp(s.noise(sec), 220), 260)
    rumble = rumble / (np.max(np.abs(rumble)) + 1e-9)
    x = 0.6 * grains * pulse + 0.25 * scrape * pulse + 0.35 * rumble
    for k in range(int(sec / 0.3) + 1):
        mix(x, n(k * 0.3 + 0.05), 0.25 * thump(120, 60, 0.08, 0.02))
    return x


s.save("dig_loop", loop(dig, 1.2), 0.42, fade=False)

# ------------------------------------------------------------------ the pump

d = 0.4  # shoot: the hose thrust: an airy whoosh out, a springy twang of the coil
x = np.zeros(n(d))
wh = bandnoise(0.22, curve([(0, 600), (0.22, 3000)], 0.22), curve([(0, 2500), (0.22, 8000)], 0.22))
mix(x, 0, 0.45 * wh * curve([(0, 0), (0.04, 1), (0.22, 0)], 0.22))
tt = t(0.35)
fv = 260 * (1 + 0.35 * np.exp(-tt / 0.03)) * (1 + 0.06 * np.sin(2 * np.pi * 34 * tt) * np.exp(-tt / 0.12))
mix(x, n(0.02), 0.35 * osc(fv, 0.35, ((1, 1.0), (2, 0.35), (3, 0.2), (5, 0.08))) * env(n(0.35), 0.002, 0.16, 2.5))
mix(x, n(0.02), 0.25 * thump(380, 160, 0.05, 0.012))
save("shoot", x, 0.5)

d = 0.25  # hook: it catches: a rubbery thup and a short elastic wobble
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(240, 95, 0.12, 0.025))
mix(x, 0, 0.3 * lp(s.noise(0.02), 1800) * env(n(0.02), 0.0005, 0.005, 3))
tt = t(0.18)
fv = curve([(0, 150), (0.05, 230), (0.18, 210)], 0.18) * (1 + 0.08 * np.sin(2 * np.pi * 26 * tt))
mix(x, n(0.01), 0.3 * osc(fv, 0.18, ((1, 1.0), (2, 0.4), (3, 0.15))) * env(n(0.18), 0.004, 0.05, 2.5))
save("hook", x, 0.5)

d = 0.3  # pump: one squeeze: a plunger thunk, a puff of air rushing through, the rubber stretching with a squeak
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(150, 80, 0.07, 0.02))
ex = np.r_[click(0.002, 6000), np.zeros(n(0.1))]
mix(x, 0, 0.12 * resonate(ex, ((1430, 0.03, 1.0), (2380, 0.02, 0.5), (3900, 0.012, 0.25))))   # brass barrel
air = bandnoise(0.24, curve([(0, 700), (0.24, 1400)], 0.24), curve([(0, 3000), (0.24, 5000)], 0.24))
mix(x, n(0.015), 0.4 * air * curve([(0, 0), (0.05, 1), (0.16, 0.8), (0.24, 0)], 0.24))
tt = t(0.2)
fv = curve([(0, 260), (0.2, 400)], 0.2) * (1 + 0.03 * np.sin(2 * np.pi * 30 * tt))
mix(x, n(0.06), 0.18 * lp(saw(fv, 0.2, 10), 2200) * curve([(0, 0), (0.06, 1), (0.2, 0)], 0.2))
save("pump", x, 0.5)

d = 0.9  # pop: a big balloon pop: a sharp crack, a low boom, rubber flapping, then a confetti fizz with sparkles
x = np.zeros(n(d))
mix(x, 0, 0.7 * hp(s.noise(0.012), 600) * env(n(0.012), 0.0002, 0.003, 3))
mix(x, 0, 1.0 * thump(170, 42, 0.35, 0.1))
mix(x, 0, 0.5 * lp(s.noise(0.15), curve([(0, 6000), (0.15, 800)], 0.15)) * env(n(0.15), 0.001, 0.035, 3))
tt = t(0.12)
mix(x, n(0.01), 0.25 * lp(s.noise(0.12), 1500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 45 * tt)))
    * curve([(0, 1), (0.12, 0)], 0.12))
fz = crackle(0.6, 220, 9000, 0.002) * curve([(0, 0), (0.05, 1), (0.6, 0)], 0.6)
mix(x, n(0.06), 0.35 * fz)
glitter(x, 0.08, 0.55, 18, 4500, 10000, 0.12)
save("pop", drive(x, 1.3), 0.62)

d = 0.65  # crush: a rock lands on a critter: a heavy thud, a comic squish sliding down
x = np.zeros(n(d))
mix(x, 0, 1.0 * thump(110, 38, 0.45, 0.12))
mix(x, 0, 0.45 * lp(s.noise(0.25), curve([(0, 2500), (0.25, 300)], 0.25)) * env(n(0.25), 0.001, 0.06, 3))
tt = t(0.3)
fv = curve([(0, 620), (0.3, 170)], 0.3) * (1 + 0.07 * np.sin(2 * np.pi * 21 * tt))
sq_ = lp(saw(fv, 0.3, 12), curve([(0, 2800), (0.3, 700)], 0.3)) * curve([(0, 0), (0.02, 1), (0.3, 0)], 0.3)
mix(x, n(0.03), 0.3 * sq_)
wet = bandnoise(0.25, curve([(0, 900), (0.25, 300)], 0.25), curve([(0, 3000), (0.25, 1200)], 0.25))
mix(x, n(0.03), 0.25 * wet * (0.6 + 0.4 * np.sin(2 * np.pi * 17 * t(0.25))) * curve([(0, 0), (0.03, 1), (0.25, 0)],
                                                                                      0.25))
save("crush", drive(x, 1.2), 0.62)

# ------------------------------------------------------------------ rocks

d = 0.85  # rock_wobble: a rock working loose: a grinding wobble, a few knocks, dribbling pebbles
x = np.zeros(n(d))
tt = t(0.8)
wob = 0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt) ** 2
grind = lp(s.noise(0.8), 450 + 250 * np.sin(2 * np.pi * 9 * tt) ** 2) * wob * curve([(0, 0), (0.05, 1), (0.6, 0.9),
                                                                                    (0.8, 0)], 0.8)
mix(x, 0, 0.8 * grind)
for k, st in enumerate((0.02, 0.2, 0.36, 0.52)):
    mix(x, n(st), (0.4 - 0.05 * k) * thump(140 if k % 2 else 110, 60, 0.09, 0.025))
pebbles(x, 0.1, 0.65, 9, 0.22)
save("rock_wobble", x, 0.5)

d = 0.72  # rock_fall: a falling whistle and a growing rumble, fading out by itself
x = np.zeros(n(d))
tt = t(0.7)
fv = curve([(0, 1250), (0.7, 480)], 0.7) * (1 + 0.01 * np.sin(2 * np.pi * 6 * tt))
mix(x, 0, 0.16 * osc(fv, 0.7, ((1, 1.0), (2, 0.05))) * curve([(0, 0), (0.08, 1), (0.55, 0.8), (0.7, 0)], 0.7))
mix(x, 0, 0.45 * lp(lp(s.noise(0.7), 300), 350) * curve([(0, 0.2), (0.5, 1), (0.7, 0)], 0.7))
mix(x, 0, 0.12 * bandnoise(0.7, 1200, 4000) * curve([(0, 0), (0.2, 1), (0.7, 0)], 0.7))
pebbles(x, 0.0, 0.4, 4, 0.12)
save("rock_fall", x, 0.45)

d = 1.0  # rock_land: a heavy thud and the rock crumbling apart
x = np.zeros(n(d))
mix(x, 0, 1.0 * thump(95, 32, 0.6, 0.16))
mix(x, 0, 0.5 * lp(s.noise(0.3), curve([(0, 3000), (0.3, 350)], 0.3)) * env(n(0.3), 0.001, 0.07, 3))
cr = crackle(0.75, 260, 3000, 0.006) * curve([(0, 0), (0.04, 1), (0.75, 0)], 0.75)
mix(x, n(0.03), 0.6 * cr)
mix(x, n(0.03), 0.3 * lp(s.noise(0.7), 600) * curve([(0, 1), (0.7, 0)], 0.7))
pebbles(x, 0.1, 0.7, 10, 0.2)
save("rock_land", drive(x, 1.2), 0.62)

# ------------------------------------------------------------------ the critters

d = 0.65  # breathe: a short roaring whoosh of flame
x = np.zeros(n(d))
sec = 0.6
cut = curve([(0, 400), (0.12, 2600), (0.4, 1500), (0.6, 600)], sec)
roar = lp(lp(s.noise(sec), cut), cut * 1.2)
roar = roar / (np.max(np.abs(roar)) + 1e-9)
flicker = 0.8 + 0.2 * np.sin(2 * np.pi * 14 * t(sec)) * np.sin(2 * np.pi * 5 * t(sec))
mix(x, 0, 0.8 * roar * flicker * curve([(0, 0), (0.06, 1), (0.35, 0.8), (0.6, 0)], sec))
low = lp(lp(s.noise(sec), 140), 160)
mix(x, 0, 0.35 * low / (np.max(np.abs(low)) + 1e-9) * curve([(0, 0), (0.1, 1), (0.6, 0)], sec))
mix(x, n(0.05), 0.25 * crackle(0.5, 120, 6000) * curve([(0, 1), (0.5, 0)], 0.5))
mix(x, 0, 0.3 * thump(90, 50, 0.2, 0.06))
save("breathe", x, 0.55)

d = 0.65  # ghost: a critter goes ghost: a spooky wavering warble, pitch sagging and lifting, through a breathy veil
x = np.zeros(n(d))
sec = 0.6
tt = t(sec)
fv = curve([(0, 660), (0.25, 520), (0.6, 700)], sec) * (1 + 0.045 * np.sin(2 * np.pi * 7.5 * tt))
mix(x, 0, 0.3 * osc(fv, sec, ((1, 1.0), (2, 0.12))) * curve([(0, 0), (0.08, 1), (0.45, 0.8), (0.6, 0)], sec))
mix(x, 0, 0.12 * osc(fv * 1.498, sec) * curve([(0, 0), (0.15, 1), (0.6, 0)], sec))
mix(x, 0, 0.12 * bandnoise(sec, 600, 2500) * curve([(0, 0), (0.2, 1), (0.6, 0)], sec))
save("ghost", x, 0.45)

# ------------------------------------------------------------------ vegetables

d = 0.8  # veg_appear: a little pop-in and a sparkly rising chime (F major)
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(500, 200, 0.05, 0.012), 0.3 * lp(s.noise(0.015), 5000) * env(n(0.015), 0.0004, 0.004, 3))
for k, m in enumerate((84, 89, 93, 96)):
    mix(x, n(0.04 + 0.05 * k), 0.22 * fmbell(m2f(m), 0.6, 2.0, 1.2, 0.18 + 0.03 * k))
glitter(x, 0.1, 0.6, 22, 5000, 11000, 0.1)
save("veg_appear", x, 0.5)

d = 0.8  # veg_take: a crunchy bite (two crunches) and a bright collect chime (C7, F7)
x = np.zeros(n(d))
for st in (0.0, 0.08):
    mix(x, n(st), 0.6 * crackle(0.07, 900, 7000, 0.003) * curve([(0, 1), (0.07, 0)], 0.07))
    mix(x, n(st), 0.3 * bandnoise(0.05, 1500, 6000) * env(n(0.05), 0.001, 0.012, 3))
    mix(x, n(st), 0.25 * thump(220, 120, 0.04, 0.01))
mix(x, n(0.14), 0.32 * fmbell(m2f(96), 0.5, 3.5, 1.3, 0.1))
mix(x, n(0.2), 0.36 * fmbell(m2f(101), 0.6, 3.5, 1.4, 0.18), 0.14 * fmbell(m2f(108), 0.4, 2.0, 0.8, 0.1))
save("veg_take", x, 0.55)

# ------------------------------------------------------------------ the hero's fate and jingles

d = 1.5  # die: a sad descending wobble (three sagging steps down, then a slide), a soft plop at the end
x = np.zeros(n(d))
for k, (m, st, ln) in enumerate(((77, 0.0, 0.26), (76, 0.26, 0.26), (75, 0.52, 0.26))):
    tt = t(ln)
    fv = m2f(m) * (1 + 0.035 * np.sin(2 * np.pi * 9 * tt)) * curve([(0, 1), (ln, 0.985)], ln)
    v = lp(sq(fv, ln, 9), 2600) * curve([(0, 0), (0.01, 1), (ln - 0.03, 0.8), (ln, 0)], ln)
    mix(x, n(st), 0.22 * v, 0.12 * osc(fv / 2, ln) * curve([(0, 0), (0.01, 1), (ln, 0)], ln))
ln = 0.6
tt = t(ln)
fv = curve([(0, m2f(74)), (ln, m2f(58))], ln) * (1 + 0.05 * np.sin(2 * np.pi * 7 * tt))
mix(x, n(0.78), 0.22 * lp(sq(fv, ln, 9), 2200) * curve([(0, 0), (0.01, 1), (0.45, 0.7), (ln, 0)], ln),
    0.12 * osc(fv / 2, ln) * curve([(0, 1), (ln, 0)], ln))
mix(x, n(1.36), 0.4 * thump(160, 70, 0.12, 0.03), 0.15 * lp(s.noise(0.06), 1500) * env(n(0.06), 0.001, 0.015, 3))
save("die", x, 0.55)


def jingle_note(x, m, st, ln, level=0.25, wood_tick=False):
    """One jingle note: a mallet bar doubled by a soft pluck an octave down."""
    mix(x, n(st), level * mallet(m2f(m), ln + 0.4, 0.3), 0.6 * level * pluck(m2f(m - 12), ln + 0.4, 0.25))
    if wood_tick:
        mix(x, n(st), wood(0.1))


def bass_note(x, m, st, ln, level=0.3):
    mix(x, n(st), level * pluck(m2f(m), ln + 0.2, 0.22, 5) * curve([(0, 1), (ln, 1), (ln + 0.2, 0)], ln + 0.2))


B8 = 60 / 150 / 2   # an eighth at 150 bpm

d = 2.3  # level_start: a cheerful little march-in: a skipping F major run up and a bright landing
x = np.zeros(n(d))
for k, m in enumerate((72, 77, 81, 77, 79, 81, 84)):
    jingle_note(x, m, k * B8, B8, 0.24, wood_tick=k % 2 == 1)
for k, m in enumerate((53, 57, 48, 52)):
    bass_note(x, m, k * 2 * B8, 2 * B8)
for m in (77, 81, 84, 89):
    mix(x, n(7 * B8), 0.14 * mallet(m2f(m), 1.2, 0.5))
bass_note(x, 41, 7 * B8, 0.8, 0.4)
mix(x, n(7 * B8), 0.18 * fmbell(m2f(96), 1.0, 2.0, 1.0, 0.3), wood(0.15))
save("level_start", x, 0.55)

d = 3.0  # level_clear: a happy run up two octaves, a playful turn, a full F major landing with bells
x = np.zeros(n(d))
line = ((72, 0, 1), (77, 1, 1), (81, 2, 1), (84, 3, 1), (89, 4, 1), (88, 5, 0.5), (89, 5.5, 0.5), (91, 6, 1),
        (88, 7, 1), (84, 8, 1), (86, 9, 1), (88, 10, 1))
for m, st, ln in line:
    jingle_note(x, m, st * B8, ln * B8, 0.22, wood_tick=st % 2 == 1)
for k, m in enumerate((41, 45, 48, 46, 43, 48)):
    bass_note(x, m, k * 2 * B8, 2 * B8)
for m in (65, 72, 77, 81, 84, 89):
    mix(x, n(11 * B8), 0.11 * mallet(m2f(m), 1.6, 0.6))
bass_note(x, 41, 11 * B8, 1.0, 0.45)
for k, m in enumerate((89, 93, 96, 101)):
    mix(x, n(11 * B8 + 0.05 * k), 0.13 * fmbell(m2f(m), 1.3, 2.0, 1.2, 0.35))
glitter(x, 11 * B8, 1.0, 26, 5000, 11000, 0.08)
save("level_clear", outro(drive(x, 1.2), 0.5), 0.62)

d = 1.8  # last_one: a hurried sting: fast repeated notes edging up chromatically to an unresolved C7
x = np.zeros(n(d))
S = 60 / 176 / 4   # sixteenths at 176 bpm
seq = (84, 84, 84, 85, 86, 86, 86, 87, 88, 88, 89, 90, 91, 91, 91, 91)
for k, m in enumerate(seq):
    jingle_note(x, m, k * S, S * 0.8, 0.2, wood_tick=k % 2 == 0)
for k in range(8):
    bass_note(x, (48, 55)[k % 2], k * 2 * S, S * 1.5, 0.3)
st = 16 * S
for m in (70, 76, 79, 84):   # C7, a dominant left hanging
    mix(x, n(st), 0.12 * mallet(m2f(m), 0.9, 0.35), 0.06 * lp(sq(m2f(m), 0.5, 7), 3000)
        * curve([(0, 1), (0.4, 0.6), (0.5, 0)], 0.5))
bass_note(x, 36, st, 0.5, 0.4)
mix(x, n(st), wood(0.18), 0.25 * thump(200, 90, 0.08, 0.02))
save("last_one", outro(x, 0.3), 0.55)

d = 3.6  # game_over: a gentle, slightly comic sad tune stepping down, a sagging slide, a little plink to end
x = np.zeros(n(d))
Q = 60 / 112
for k, m in enumerate((81, 79, 77, 76, 74, 72)):
    jingle_note(x, m, k * Q * 0.5, Q * 0.5, 0.22)
for k, m in enumerate((53, 48, 46, 43)):
    bass_note(x, m, k * Q * 0.75, Q * 0.7, 0.3)
st = 3 * Q
ln = 1.1
tt = t(ln)
fv = m2f(70) * curve([(0, 1), (0.3, 1), (ln, 2 ** (-5 / 12))], ln) * (1 + 0.03 * np.sin(2 * np.pi * 6 * tt))
mix(x, n(st), 0.2 * lp(saw(fv, ln, 12), 1400) * curve([(0, 0), (0.03, 1), (0.8, 0.8), (ln, 0)], ln),
    0.1 * lp(saw(fv / 2, ln, 10), 700) * curve([(0, 0), (0.03, 1), (ln, 0)], ln))
bass_note(x, 41, st + ln, 0.9, 0.35)
for m in (65, 69, 72):
    mix(x, n(st + ln), 0.1 * mallet(m2f(m), 1.2, 0.5))
mix(x, n(st + ln + 0.35), 0.15 * fmbell(m2f(101), 0.5, 2.0, 0.8, 0.12), wood(0.08))
save("game_over", outro(x, 0.4), 0.55)

d = 1.1  # extra_life: a bright 1-up arpeggio, F major up two octaves in square bells, a sparkle
x = np.zeros(n(d))
for k, m in enumerate((77, 81, 84, 89, 93, 96, 101)):
    tone = sq(m2f(m), 0.2, 9) * env(n(0.2), 0.002, 0.07, 2)
    mix(x, n(0.055 * k), 0.13 * lp(tone, 7000), 0.12 * fmbell(m2f(m + 12), 0.3, 2.0, 0.6, 0.1))
mix(x, n(0.38), 0.25 * fmbell(m2f(101), 0.7, 3.01, 1.2, 0.25), 0.2 * fmbell(m2f(89), 0.7, 2.0, 1.0, 0.3))
glitter(x, 0.38, 0.6, 18, 5000, 11000, 0.1)
save("extra_life", x, 0.55)
