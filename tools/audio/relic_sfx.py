#!/usr/bin/env python3
"""Sound effects for game 19 (Relic Run), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game or film. A jungle temple of traps, played for
laughs like an old adventure serial. The pistol is a cartoon pop (a snappy noise burst over a short falling
thump), not a real gunshot; ricochets are a whining sine gliding down. Stone is the core material: thuds are
falling sines under low-passed noise, rubble a spray of small resonant knocks (stone modes) thinning out.
Metal traps (spikes, the automatons) ring through inharmonic resonant modes. The two loops (the fuse and the
rolling boulder) are built on circular noise and grains wrapped round the loop, so they have no seam.
The jingles are in D (minor for danger, major for the treasure) like the music: a round brassy voice, marimba,
timpani (a pitched thump with a skin rattle), plucked strings (Karplus-Strong) and a glockenspiel.
No voices anywhere: the death is a slide whistle falling and a thud.
Usage: python3 tools/audio/relic_sfx.py [out_dir]   (default: godot/games/relic/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/relic/audio/sfx", seed=1989)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, *bs):
    """Adds sounds (of any lengths) into x from `start`."""
    for b in bs:
        b = b[:max(0, len(x) - start)]
        x[start:start + len(b)] += b


def circ_mix(x, start, b):
    """Mixes b into x wrapping round the end: for grains placed in a loop."""
    idx = (start + np.arange(len(b))) % len(x)
    np.add.at(x, idx, b)


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
        y += a * np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]  # FFT convolution: fast
    return y


def knock(f, sec=0.08, dec=0.012):
    """A small stone knock: a short noise click through two low, quickly damped modes."""
    ex = np.r_[lp(s.noise(0.003), 4000) * env(n(0.003), 0.0002, 0.001, 3), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 2.3, dec * 0.6, 0.5), (f * 3.9, dec * 0.4, 0.25)))


def clank(f, sec=0.4, dec=0.08):
    """A metal clank: an impulse through inharmonic modes that ring a while."""
    ex = np.r_[1.0, 0.5 * hp(s.noise(0.002), 2000), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 1.59, dec * 0.8, 0.7), (f * 2.41, dec * 0.6, 0.5), (f * 3.7, dec * 0.4, 0.3)))


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


def brass(f, sec, attack=0.025, decay=0.5, curve_=1.2, bright=1.0):
    """A round brassy voice: a saw-like stack whose brightness opens with the attack, a touch of vibrato."""
    tt = t(sec)
    fv = np.broadcast_to(np.asarray(f, dtype=float), tt.shape) * (1 + 0.004 * np.clip(tt / 0.3, 0, 1) * np.sin(2 * np.pi * 5.5 * tt))
    x = osc(fv, sec, [(k, 1 / k) for k in range(1, 12)])
    fm = float(np.max(fv))
    cut = fm * (1.5 + 4 * bright * np.clip(tt / (attack * 3), 0, 1) * np.exp(-tt / 0.6)) + 400
    return lp(x, np.minimum(cut, 9000)) * env(n(sec), attack, decay, curve_)


def timp(f, sec=1.0, decay=0.5):
    """A timpano: a pitched thump that sags a little, its inharmonic head modes, a soft mallet thud."""
    fv = f * (1 + 0.04 * np.exp(-t(sec) / 0.05))
    x = osc(fv, sec, ((1, 1.0), (1.5, 0.45), (1.99, 0.25), (2.44, 0.12))) * env(n(sec), 0.003, decay, 3)
    return x + 0.4 * lp(s.noise(sec), 300) * env(n(sec), 0.001, 0.05, 3)


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def rubble(sec, count, lo, hi, amp=1.0):
    """Stones tumbling: small knocks at random times and pitches, thinning out, over a low gritty rumble."""
    x = np.zeros(n(sec) + n(0.15))
    for k in range(count):
        st = sec * s.rng.uniform(0, 1) ** 1.8
        mix(x, n(st), s.rng.uniform(0.3, 1.0) * amp * (1 - 0.6 * st / sec) * knock(s.rng.uniform(lo, hi)))
    mix(x, 0, 0.25 * amp * lp(s.noise(sec), 400) * env(n(sec), 0.01, sec * 0.4, 2.5))
    return x


# D minor / D major notes (MIDI), used by the jingles
D2, A2, D3, F3, A3, Bb3, C4, D4, E4, F4, Fs4, G4, A4, Bb4, C5, Cs5, D5, E5, F5, Fs5, G5, A5, Bb5, D6, Fs6, A6, D7 = (
    m2f(m) for m in (38, 45, 50, 53, 57, 58, 60, 62, 64, 65, 66, 67, 69, 70, 72, 73, 74, 76, 77, 78, 79, 81, 82, 86, 90, 93, 98))

# --- the pistol ---
d = 0.35  # shot: a cartoon pop: a snappy bright burst, a short falling thump, a tiny springy ring of the cap
x = np.zeros(n(d))
mix(x, 0, 0.9 * lp(hp(s.noise(0.03), 700), np.geomspace(9000, 1500, n(0.03))) * env(n(0.03), 0.0003, 0.008, 3))
mix(x, 0, 0.9 * thump(420, 90, 0.12, 0.035))
mix(x, n(0.004), 0.25 * lp(s.noise(0.25), 900) * env(n(0.25), 0.002, 0.07, 3))
mix(x, n(0.002), 0.08 * clank(2400, 0.15, 0.02))
save("shot", x, 0.55)

d = 0.6  # ricochet: a hard tick on stone and the bullet's whine gliding down, wavering as it spins away
x = np.zeros(n(d))
mix(x, 0, 0.6 * knock(1800, 0.05, 0.006), 0.3 * hp(s.noise(0.01), 3000) * env(n(0.01), 0.0002, 0.003, 3))
tt = t(0.5)
fr = curve([(0, 3400), (0.5, 1300)], 0.5) * (1 + 0.02 * np.sin(2 * np.pi * 23 * tt))
mix(x, n(0.01), 0.35 * osc(fr, 0.5, ((1, 1.0), (2, 0.12))) * curve([(0, 0), (0.02, 1), (0.25, 0.5), (0.5, 0)], 0.5))
save("ricochet", x, 0.35)

d = 0.15  # empty: the hammer falls on nothing: a dry double click
x = np.zeros(n(d))
mix(x, 0, 0.7 * clank(3100, 0.04, 0.004))
mix(x, n(0.035), 0.5 * clank(2300, 0.04, 0.005))
save("empty", hp(x, 400), 0.3)

# --- dynamite ---
d = 0.35  # plant: the stick set down on stone: a soft paper-and-stone tap, a little scrape
x = np.zeros(n(d))
mix(x, 0, 0.6 * knock(420, 0.1, 0.02), 0.4 * thump(200, 110, 0.08, 0.02))
mix(x, n(0.03), 0.2 * lp(hp(s.noise(0.12), 1500), 5000) * curve([(0, 0), (0.03, 1), (0.12, 0)], 0.12))
save("plant", x, 0.35)

d = 1.0  # fuse: a burning fuse: hissing, sputters and small pops, all laid round the loop so it has no seam
N = n(d)
ph = np.arange(N) / N
x = band_noise(N, 2800, 11000, 0.6) * (0.75 + 0.25 * np.sin(2 * np.pi * 6 * ph) * np.sin(2 * np.pi * 4 * ph))
x += 0.35 * band_noise(N, 800, 2800) * (0.7 + 0.3 * np.cos(2 * np.pi * 9 * ph))
for k in range(30):  # crackles
    c = hp(s.noise(0.005), 1500) * env(n(0.005), 0.0002, 0.0018, 3)
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.6, 1.8) * c)
for k in range(5):  # sputters
    c = s.sweep(600, 220, 0.02) * env(n(0.02), 0.0005, 0.006, 3)
    circ_mix(x, int(s.rng.uniform(0, N)), 0.7 * c)
x -= np.mean(x)
s.save("fuse", x, 0.35, fade=False)

d = 2.4  # boom: dynamite: a round deep thump (not a harsh crack), a low-passed roar that swells and settles,
x = np.zeros(n(d))  # stones and dust raining down after
mix(x, 0, 1.1 * thump(110, 32, 1.0, 0.35))
mix(x, 0, 0.5 * lp(s.noise(0.06), 2500) * env(n(0.06), 0.0005, 0.02, 3))
roar = lp(s.noise(d), curve([(0, 1800), (0.2, 900), (2.4, 200)], d))
mix(x, 0, 0.9 * roar * curve([(0, 0), (0.015, 1), (0.4, 0.6), (2.4, 0)], d))
mix(x, 0, 0.6 * lp(s.noise(d), 90) * env(n(d), 0.01, 0.9, 2.5))
mix(x, n(0.25), 0.55 * rubble(1.6, 40, 250, 1100))
save("boom", lp(x, 6000), 0.78)

d = 1.4  # rubble: a wall comes down: a heavy crumble and a shower of stones settling
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(150, 60, 0.3, 0.1))
mix(x, 0, rubble(1.2, 55, 200, 1000))
save("rubble", x, 0.7)

# --- the explorer ---
d = 0.22  # jump: a quick cloth whoosh with a springy rising blip
x = np.zeros(n(d))
mix(x, 0, 0.35 * lp(hp(s.noise(0.15), 500), np.geomspace(1200, 4000, n(0.15))) * env(n(0.15), 0.01, 0.05, 3))
mix(x, 0, 0.3 * osc(curve([(0, 260), (0.1, 520)], 0.1), 0.1, ((1, 1.0), (2, 0.2))) * env(n(0.1), 0.003, 0.04, 3))
save("jump", x, 0.3)

d = 0.25  # land: boots on stone: a padded thud and a scuff of grit
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(140, 60, 0.12, 0.03), 0.3 * knock(380, 0.08, 0.015))
mix(x, n(0.01), 0.2 * lp(hp(s.noise(0.1), 1200), 5000) * env(n(0.1), 0.003, 0.03, 3))
save("land", lp(x, 4000), 0.35)

for k, (f, g) in enumerate(((330, 1.0), (290, 0.9))):  # step_0, step_1: a soft heel-toe pad with a little grit
    x = np.zeros(n(0.14))
    mix(x, 0, 0.6 * thump(f * 0.5, 55, 0.07, 0.018), 0.25 * knock(f, 0.06, 0.008))
    mix(x, n(0.025), 0.15 * lp(hp(s.noise(0.06), 1500), 5000) * env(n(0.06), 0.002, 0.02, 3))
    save(f"step_{k}", lp(x, 3500) * g, 0.2 * g)

d = 0.3  # climb: a rope ladder rung taking weight: a woody creak (a rough, slowly bending squeak) and a tap
x = np.zeros(n(d))
tt = t(0.22)
fc = curve([(0, 420), (0.22, 360)], 0.22)
cr = np.sign(osc(fc, 0.22)) * (0.6 + 0.4 * (s.rng.uniform(0, 1, n(0.22)) > 0.5))
mix(x, n(0.03), 0.3 * lp(hp(cr, 300), 2200) * curve([(0, 0), (0.04, 1), (0.16, 0.7), (0.22, 0)], 0.22))
mix(x, 0, 0.35 * knock(700, 0.06, 0.01))
save("climb", x, 0.25)

# --- traps ---
d = 0.8  # spikes: iron spikes spring from the floor: a scraping rush up, then a bright metallic shing ringing
x = np.zeros(n(d))
mix(x, 0, 0.35 * hp(s.noise(0.06), 2000) * curve([(0, 0), (0.05, 1), (0.06, 0)], 0.06))
mix(x, n(0.05), 0.7 * clank(1750, 0.7, 0.18), 0.4 * clank(2620, 0.6, 0.12))
mix(x, n(0.05), 0.2 * hp(s.noise(0.3), 5000) * env(n(0.3), 0.001, 0.08, 3))
mix(x, n(0.05), 0.4 * thump(200, 90, 0.08, 0.02))
save("spikes", x, 0.5)

d = 0.5  # dart: a puff from the wall slot and a thin whistle darting past (rising then dropping, Doppler-ish)
x = np.zeros(n(d))
mix(x, 0, 0.3 * lp(s.noise(0.04), 2500) * env(n(0.04), 0.001, 0.012, 3))
fw = curve([(0, 2600), (0.2, 3000), (0.4, 2100)], 0.4)
wh = osc(fw, 0.4) + 0.4 * hp(s.noise(0.4), 3000)
mix(x, n(0.02), 0.35 * wh * curve([(0, 0), (0.15, 1), (0.25, 0.8), (0.4, 0)], 0.4))
save("dart", x, 0.3)

d = 0.3  # dart_hit: the dart thunks into wood or stone: a hollow knock and a short quiver of the shaft
x = np.zeros(n(d))
mix(x, 0, 0.8 * knock(520, 0.2, 0.03), 0.4 * thump(260, 120, 0.06, 0.015))
tt = t(0.2)
mix(x, n(0.01), 0.15 * osc(180, 0.2, ((1, 1.0), (3, 0.3))) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * tt)) * env(n(0.2), 0.002, 0.06, 3))
save("dart_hit", x, 0.4)

d = 2.0  # boulder_roll: a heavy stone ball rolling: a deep circular rumble, a lumpy once-per-turn thud and
N = n(d)  # gravel crunching, all wrapped round the loop so it has no seam
ph = np.arange(N) / N
x = band_noise(N, 25, 140, 1.5) * (0.7 + 0.3 * np.sin(2 * np.pi * 5 * ph))
x += 0.3 * band_noise(N, 150, 700, 1.0) * (0.6 + 0.4 * np.sin(2 * np.pi * 10 * ph + 1))
f_roll = 36.0  # a whole number of cycles over the loop
x += 0.45 * np.sin(2 * np.pi * f_roll * ph * d) * (0.6 + 0.4 * np.cos(2 * np.pi * 5 * ph))
for k in range(5):  # a thud as the flat side comes round, five per loop
    circ_mix(x, int(k * N / 5 + s.rng.uniform(-400, 400)), 0.8 * thump(90, 45, 0.15, 0.05))
for k in range(60):  # grit crushed under it
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.05, 0.2) * knock(s.rng.uniform(300, 900), 0.04, 0.006))
x -= np.mean(x)
s.save("boulder_roll", x, 0.45, fade=False)

d = 1.0  # crusher: a stone block slams down: a grinding rush, a huge deep slam, dust hiss and a few pebbles
x = np.zeros(n(d))
mix(x, 0, 0.3 * lp(s.noise(0.12), 700) * curve([(0, 0), (0.11, 1), (0.12, 0)], 0.12))
mix(x, n(0.12), 1.0 * thump(120, 38, 0.6, 0.18), 0.6 * knock(160, 0.3, 0.05))
mix(x, n(0.12), 0.5 * lp(s.noise(0.6), curve([(0, 2500), (0.6, 300)], 0.6)) * env(n(0.6), 0.001, 0.15, 3))
mix(x, n(0.2), 0.3 * rubble(0.5, 10, 400, 1000))
save("crusher", lp(x, 5000), 0.75)

# --- enemies ---
d = 0.4  # enemy_hit: a clockwork automaton or skeleton struck: a hollow bonk and a tinny clank rattle
x = np.zeros(n(d))
mix(x, 0, 0.6 * thump(380, 180, 0.12, 0.04), 0.5 * clank(930, 0.3, 0.05))
for k in range(3):
    mix(x, n(0.05 + 0.04 * k), (0.25 - 0.06 * k) * knock(1400 + 300 * k, 0.05, 0.006))
save("enemy_hit", x, 0.45)

d = 0.9  # bat: a bat flutters past: soft leathery wing flaps in bursts and three high little squeaks
x = np.zeros(n(d))
for k in range(12):
    st = 0.02 + k * 0.065 + s.rng.uniform(0, 0.01)
    mix(x, n(st), (0.4 + 0.2 * (k % 2)) * lp(hp(s.noise(0.04), 300), 1800) * env(n(0.04), 0.004, 0.015, 3))
for st, f in ((0.1, 4200), (0.38, 4700), (0.62, 3900)):
    mix(x, n(st), 0.18 * osc(curve([(0, f), (0.03, f * 1.2), (0.06, f * 0.95)], 0.06), 0.06) * env(n(0.06), 0.004, 0.02, 3))
save("bat", x * curve([(0, 0.4), (0.4, 1), (0.9, 0.3)], d), 0.4)

# --- pickups ---
d = 0.9  # pickup_treasure: a bright chime: a glockenspiel and marimba skip up the D major chord, a sparkle
x = np.zeros(n(d))
for i, f in enumerate((A5, D6, Fs6, A6)):
    mix(x, n(i * 0.05), 0.3 * glock(f, 0.6, 0.25), 0.2 * marimba(f / 2, 0.3, 0.1))
mix(x, n(0.15), 0.12 * glock(D7, 0.7, 0.3))
mix(x, n(0.15), 0.06 * hp(s.noise(0.4), 7000) * env(n(0.4), 0.002, 0.12, 3))
save("pickup_treasure", x, 0.45)

d = 0.25  # pickup_ammo: click-clack: a box of cartridges snapped into the belt
x = np.zeros(n(d))
mix(x, 0, 0.6 * clank(2600, 0.06, 0.008), 0.3 * knock(900, 0.05, 0.008))
mix(x, n(0.07), 0.7 * clank(1900, 0.1, 0.012), 0.35 * knock(700, 0.06, 0.01))
save("pickup_ammo", x, 0.35)

d = 0.8  # secret: a discovery: a soft shimmer and a slow glockenspiel rise D A D' F#' with a bowed-ish pad
x = np.zeros(n(d + 0.8))
for i, f in enumerate((D5, A5, D6, Fs6)):
    mix(x, n(i * 0.1), 0.28 * glock(f, 1.0, 0.4))
for f in (D4, A4, Fs5):
    mix(x, 0, 0.05 * osc(f, 1.4, ((1, 1.0), (2, 0.3), (3, 0.15))) * curve([(0, 0), (0.3, 1), (1.4, 0)], 1.4))
mix(x, 0, 0.05 * hp(s.noise(1.2), 6000) * curve([(0, 0), (0.4, 1), (1.2, 0)], 1.2))
save("secret", x, 0.45)

# --- death and jingles ---
d = 1.3  # die: no voice: a slide whistle falling a long way, a wobbling "whoops", then a thud and a knock
x = np.zeros(n(d))
ln = 0.8
fs = curve([(0, 1500), (0.1, 1650), (0.8, 330)], ln) * (1 + 0.03 * np.sin(2 * np.pi * 8 * t(ln)))
mix(x, 0, 0.35 * osc(fs, ln, ((1, 1.0), (2, 0.08))) * curve([(0, 0), (0.03, 1), (0.7, 0.8), (0.8, 0)], ln))
mix(x, 0, 0.05 * lp(hp(s.noise(ln), 1000), 3000) * curve([(0, 0), (0.03, 1), (0.8, 0)], ln))
mix(x, n(0.82), 1.0 * thump(130, 45, 0.3, 0.08), 0.35 * knock(300, 0.1, 0.02))
mix(x, n(0.82), 0.2 * rubble(0.3, 6, 400, 900))
save("die", x, 0.55)

d = 2.2  # level_start: an adventure sting: a timpani roll swelling, a brass call up D-A-D and a held D chord
x = np.zeros(n(d))
for k in range(14):
    mix(x, n(k * 0.045), (0.05 + 0.03 * k) * timp(D2, 0.4, 0.2))
call = ((0.62, A3, 0.12), (0.76, D4, 0.12), (0.9, E4, 0.12), (1.04, F4, 0.18), (1.24, A4, 0.9))
for st, f, lnb in call:
    mix(x, n(st), 0.35 * brass(f, lnb + 0.05, 0.012, lnb * 0.8 + 0.1, 1.2))
for f in (D3, A3, D4, F4):
    mix(x, n(1.24), 0.1 * brass(f, 0.95, 0.03, 0.8, 1.3, 0.6))
mix(x, n(1.24), 0.5 * timp(D2, 0.9, 0.5), 0.15 * glock(D6, 0.7, 0.3))
for i, f in enumerate((D4, F4, A4, D5)):
    mix(x, n(1.24 + i * 0.03), 0.12 * pluck(f, 0.9, 0.6, 0.997))
save("level_start", x, 0.6)

d = 3.1  # level_clear: triumph: a marimba run up, a brass fanfare turning to D major, timpani and a big chord
x = np.zeros(n(d))
for i, f in enumerate((D4, F4, A4, D5, E5, F5, A5)):
    mix(x, n(i * 0.06), 0.25 * marimba(f, 0.4, 0.12))
fan = ((0.45, A4, 0.15), (0.62, D5, 0.15), (0.79, E5, 0.15), (0.96, Fs5, 0.35), (1.35, E5, 0.15), (1.52, Fs5, 0.15),
       (1.69, A5, 1.3))
for st, f, lnb in fan:
    mix(x, n(st), 0.3 * brass(f / 2, lnb + 0.05, 0.012, lnb * 0.8 + 0.1, 1.2), 0.08 * glock(f * 2, 0.3, 0.12))
for st, f in ((0.45, D2), (0.96, D2), (1.35, A2), (1.69, D2)):
    mix(x, n(st), 0.5 * timp(f, 0.8 if st < 1.6 else 1.4, 0.3 if st < 1.6 else 0.7))
for f in (D3, A3, D4, Fs4, A4):
    mix(x, n(1.69), 0.09 * brass(f, 1.35, 0.04, 1.0, 1.3, 0.6), 0.1 * pluck(f, 1.3, 0.6, 0.997))
for i, f in enumerate((D5, Fs5, A5, D6, Fs6, A6)):
    mix(x, n(1.69 + i * 0.04), 0.1 * glock(f, 0.8, 0.3))
mix(x, n(1.69), 0.08 * hp(s.noise(1.2), 6000) * env(n(1.2), 0.002, 0.4, 2.5))
save("level_clear", x, 0.6)

d = 2.6  # game_over: a comic-sad brass sigh winding down D minor (A, G, F, E...), a low timpani and a last knock
x = np.zeros(n(d))
for st, f in ((0.0, A4), (0.3, G4), (0.6, F4), (0.95, E4)):
    mix(x, n(st), 0.3 * brass(f / 2, 0.35 if st < 0.9 else 0.6, 0.02, 0.3, 1.3, 0.6), 0.15 * marimba(f, 0.4, 0.15))
mix(x, n(1.45), 0.3 * brass(D4 / 2, 1.0, 0.03, 0.8, 1.3, 0.5))
for f in (D3, F3, A3):
    mix(x, n(1.45), 0.12 * pluck(f, 1.1, 0.35, 0.996))
mix(x, n(1.45), 0.6 * timp(D2, 1.1, 0.5))
mix(x, n(0.95), 0.4 * timp(A2, 0.5, 0.25))
save("game_over", lp(x, 7000), 0.55)
