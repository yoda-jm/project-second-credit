#!/usr/bin/env python3
"""Sound effects for game 20 (Henhouse Heist), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. A farmyard of wooden platforms, ladders and
lifts, played for laughs. Wood is the core material: steps and landings are soft thumps through the low,
hollow modes of a plank; the ladder and the lift creak (a rough, slowly bending squeak). The hens are
synthesised, not recorded: a buzzy glottal pulse train whose pitch jumps and falls, rung through three
formant resonances (a short "buk" and a longer rising "b-gawk"), kept high and small so they sound cute.
The goose is the same trick scaled up: a big nasal buzz with a pitch that cracks upwards. The two loops (the
wing beats and the lift's pulley) are built on circular noise and grains wrapped round the loop, with whole
numbers of cycles, so they have no seam.
The jingles are in G major like the music: plucked banjo-ish strings (Karplus-Strong with a bright attack),
a fiddle voice (a bowed saw stack with vibrato), a reedy harmonica (odd-heavy harmonics with a tremolo), an
upright bass pluck and a glockenspiel. No voices anywhere: the death is a slide whistle falling and a bonk.
Usage: python3 tools/audio/henhouse_sfx.py [out_dir]   (default: godot/games/henhouse/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/henhouse/audio/sfx", seed=1983)
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


def wood(f, sec=0.12, dec=0.02):
    """A knock on a wooden plank: a soft click through a hollow low mode and two woody overtones."""
    ex = np.r_[lp(s.noise(0.004), 3000) * env(n(0.004), 0.0003, 0.0015, 3), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 2.7, dec * 0.5, 0.45), (f * 4.6, dec * 0.3, 0.2)))


def twang(f, sec=0.4, dec=0.1):
    """A wire twang: an impulse through a string-like, slightly stretched harmonic series."""
    ex = np.r_[1.0, np.zeros(n(sec))]
    return resonate(ex, [(f * k * (1 + 0.002 * k * k), dec / (0.6 + 0.4 * k), 1 / k) for k in range(1, 7)])


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


def banjo(f, sec=0.5):
    """A banjo-ish pluck: a bright, quickly damped string plus the tight 'plink' of the drum head."""
    x = pluck(f, sec, 0.9, 0.992)
    return x + 0.25 * osc(f * 2, sec, ((1, 1.0), (1.5, 0.3))) * env(n(sec), 0.001, 0.05, 3)


def glock(f, sec=0.8, decay=0.35):
    """A glockenspiel bar: a bright fundamental with the high inharmonic partials of a struck bar."""
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def fiddle(f, sec, attack=0.04, release=0.08, bright=1.0):
    """A bowed fiddle: a saw stack with a delayed vibrato, a formant-ish lowpass and a little bow hiss."""
    tt = t(sec)
    fv = np.broadcast_to(np.asarray(f, dtype=float), tt.shape)
    fv = fv * (1 + 0.006 * np.clip((tt - 0.08) / 0.15, 0, 1) * np.sin(2 * np.pi * 5.8 * tt))
    x = osc(fv, sec, [(k, (1 / k) * (1.3 if 3 <= k <= 5 else 1.0)) for k in range(1, 14)])
    x = lp(x, 2600 + 1800 * bright) + 0.04 * hp(s.noise(sec), 3000)
    return x * curve([(0, 0), (attack, 1), (max(attack, sec - release), 0.85), (sec, 0)], sec)


def harmonica(f, sec, attack=0.03, release=0.06):
    """A reedy harmonica: odd-heavy harmonics with some even ones, a breathy onset and a light tremolo."""
    tt = t(sec)
    x = osc(f, sec, ((1, 1.0), (2, 0.35), (3, 0.6), (4, 0.2), (5, 0.35), (7, 0.18), (9, 0.08)))
    x = lp(x, 3500) * (1 + 0.12 * np.sin(2 * np.pi * 6.5 * tt)) + 0.05 * lp(hp(s.noise(sec), 1500), 5000)
    return x * curve([(0, 0), (attack, 1), (max(attack, sec - release), 0.8), (sec, 0)], sec)


def bass(f, sec=0.6):
    """An upright bass pluck: a round low tone with a thumpy attack."""
    x = osc(f, sec, ((1, 1.0), (2, 0.4), (3, 0.12))) * env(n(sec), 0.004, sec * 0.5, 2.5)
    x[:n(0.05)] += 0.3 * thump(f * 2, f, 0.05, 0.015)
    return x


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def glottal(fcurve, sec, sharp=6):
    """A buzzy pulse train (a voice-like source) following a pitch curve: narrow raised-cosine pulses."""
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(np.asarray(fcurve, dtype=float), (n(sec),))) / SR
    x = ((1 + np.cos(ph)) / 2) ** sharp
    return x - np.mean(x)


def syllable(f0, f1, sec, formants, amp=1.0, peak=0.25):
    """One bird syllable: a pitch jump up then a fall, through formant resonances, with a quick envelope."""
    fc = curve([(0, f0 * 0.9), (sec * peak, f0 * 1.15), (sec, f1)], sec)
    src = glottal(fc, sec)
    y = resonate(src, [(fr, 0.004 if fr > 1500 else 0.006, a) for fr, a in formants])
    return amp * y * curve([(0, 0), (0.006, 1), (sec * 0.6, 0.8), (sec, 0)], sec)


def hen_buk(f=620, sec=0.07, amp=1.0):
    """A short hen 'buk': small, bright, a pinched vowel."""
    return syllable(f, f * 0.8, sec, ((950, 1.0), (1900, 0.6), (3100, 0.25)), amp)


def hen_gawk(f=700, sec=0.26, amp=1.0):
    """The hen's longer 'b-gawk': a rising squawk that bends up and falls away, a more open vowel."""
    fc = curve([(0, f * 0.8), (0.05, f * 1.5), (sec * 0.6, f * 1.35), (sec, f * 0.9)], sec)
    src = glottal(fc, sec, 5)
    y = resonate(src, ((1150, 0.006, 1.0), (2100, 0.004, 0.55), (3300, 0.003, 0.25)))
    return amp * y * curve([(0, 0), (0.01, 1), (sec * 0.7, 0.85), (sec, 0)], sec)


def honk(f=260, sec=0.35, amp=1.0, crack=1.35):
    """A goose honk: a big nasal buzz (reedy pulses) whose pitch cracks upward then sags, a nasal formant set."""
    fc = curve([(0, f * 0.85), (0.04, f * crack), (sec * 0.5, f * (crack - 0.1)), (sec, f * 0.9)], sec)
    fc = fc * (1 + 0.02 * np.sin(2 * np.pi * 24 * t(sec)))  # a rough flutter in the throat
    src = glottal(fc, sec, 3)
    y = resonate(src, ((650, 0.008, 1.0), (1250, 0.006, 0.8), (2500, 0.004, 0.45), (3600, 0.003, 0.15)))
    y += 0.08 * lp(hp(s.noise(sec), 1500), 5000)  # breath
    return amp * y * curve([(0, 0), (0.015, 1), (sec * 0.75, 0.9), (sec, 0)], sec)


def wingbeat(sec=0.22, amp=1.0, lo=180, hi=1400):
    """One big wing beat: a whoosh swelling and falling (low-passed noise), a feathery flutter on top."""
    x = lp(hp(s.noise(sec), lo), hi) * curve([(0, 0), (sec * 0.35, 1), (sec, 0)], sec)
    x += 0.3 * hp(s.noise(sec), 2500) * curve([(0, 0), (sec * 0.3, 1), (sec * 0.6, 0)], sec) * \
        (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 70 * t(sec))))
    return amp * x


def creak(f0, f1, sec, amp=1.0, rough=0.4):
    """A wooden creak: a rough square-ish squeak slowly bending, with a stick-slip jitter."""
    fc = curve([(0, f0), (sec, f1)], sec) * (1 + 0.03 * lp(s.noise(sec), 30) * 8)
    cr = np.sign(osc(fc, sec)) * (1 - rough + rough * (s.rng.uniform(0, 1, n(sec)) > 0.5))
    return amp * lp(hp(cr, 250), 2400) * curve([(0, 0), (sec * 0.2, 1), (sec * 0.75, 0.7), (sec, 0)], sec)


# G major notes (MIDI), used by the jingles
(G2, D3, G3, B3, C4, D4, E4, Fs4, G4, A4, B4, C5, D5, E5, Fs5, G5, A5, B5, C6, D6, E6, G6, B6, D7,
 F4, Eb4, Db4, C3, Gb4) = (m2f(m) for m in (43, 50, 55, 59, 60, 62, 64, 66, 67, 69, 71, 72, 74, 76, 78, 79, 81, 83,
                                             84, 86, 88, 91, 95, 98, 65, 63, 61, 48, 66))

# --- the farmhand ---
for k, (f, g) in enumerate(((210, 1.0), (185, 0.9))):  # step_0, step_1: soft boot heel-toe on a wooden plank
    x = np.zeros(n(0.16))
    mix(x, 0, 0.6 * thump(f * 0.6, 60, 0.07, 0.018), 0.45 * wood(f, 0.1, 0.018))
    mix(x, n(0.03), 0.2 * wood(f * 1.3, 0.06, 0.008))
    mix(x, n(0.02), 0.06 * lp(hp(s.noise(0.05), 1500), 4000) * env(n(0.05), 0.002, 0.015, 3))
    save(f"step_{k}", lp(x, 3000) * g, 0.2 * g)

d = 0.32  # climb: a wooden ladder rung taking weight: a short creak and a boot tap on the rung
x = np.zeros(n(d))
mix(x, n(0.03), 0.35 * creak(470, 400, 0.22))
mix(x, 0, 0.4 * wood(520, 0.08, 0.012), 0.25 * thump(180, 90, 0.05, 0.012))
save("climb", x, 0.25)

d = 0.34  # jump: a springy hop: a "boing" rising with a wobble that settles, a small cloth whoosh
x = np.zeros(n(d))
tt = t(0.3)
fb = curve([(0, 180), (0.08, 420), (0.3, 480)], 0.3) * (1 + 0.1 * np.sin(2 * np.pi * 17 * tt) * np.exp(-tt / 0.08))
mix(x, 0, 0.45 * osc(fb, 0.3, ((1, 1.0), (2, 0.25), (3, 0.08))) * env(n(0.3), 0.004, 0.09, 3))
mix(x, 0, 0.15 * lp(hp(s.noise(0.12), 600), 3500) * env(n(0.12), 0.01, 0.04, 3))
save("jump", x, 0.3)

d = 0.3  # land: boots on boards: a padded thud, the plank's hollow knock and a tiny creak
x = np.zeros(n(d))
mix(x, 0, 0.9 * thump(150, 55, 0.14, 0.035), 0.5 * wood(160, 0.15, 0.03))
mix(x, n(0.03), 0.12 * creak(380, 330, 0.14))
save("land", lp(x, 3500), 0.35)

# --- pickups ---
d = 0.9  # egg: a bright banjo pluck on D then a glockenspiel chime up to G, a sparkle
x = np.zeros(n(d))
mix(x, 0, 0.5 * banjo(D5, 0.5))
mix(x, n(0.06), 0.3 * glock(G6, 0.8, 0.3), 0.18 * glock(B6, 0.7, 0.25))
mix(x, n(0.06), 0.05 * hp(s.noise(0.3), 7000) * env(n(0.3), 0.002, 0.08, 3))
save("egg", x, 0.42)

d = 0.35  # grain: a soft rustle of seed (a spray of tiny ticks in band noise) and a round little blip
x = np.zeros(n(d))
mix(x, 0, 0.35 * lp(hp(s.noise(0.2), 1800), 7000) * curve([(0, 0), (0.03, 1), (0.2, 0)], 0.2))
for k in range(18):
    st = 0.15 * s.rng.uniform(0, 1) ** 1.5
    mix(x, n(st), s.rng.uniform(0.1, 0.3) * wood(s.rng.uniform(2500, 4500), 0.02, 0.002))
mix(x, n(0.05), 0.45 * osc(curve([(0, B5), (0.03, E6)], 0.12), 0.12, ((1, 1.0), (2, 0.1))) * env(n(0.12), 0.003, 0.04, 3))
save("grain", x, 0.3)

# --- the hens: cute synthesised clucks ---
for k, parts in enumerate((
        ((0.0, "buk", 640), (0.11, "buk", 620), (0.21, "gawk", 700)),
        ((0.0, "buk", 700), (0.09, "buk", 690), (0.18, "buk", 660), (0.28, "buk", 600)),
        ((0.0, "gawk", 760), (0.3, "buk", 620), (0.39, "buk", 580)))):
    x = np.zeros(n(0.7))
    for st, kind, f in parts:
        mix(x, n(st), hen_buk(f, 0.07) if kind == "buk" else hen_gawk(f, 0.26))
    save(f"cluck_{k}", hp(x, 300), 0.3)

# --- the goose ---
d = 0.9  # goose_honk: a big comic honk: "HONK-onk", the second one lower and shorter
x = np.zeros(n(d))
mix(x, 0, honk(250, 0.38, 1.0, 1.4))
mix(x, n(0.46), honk(220, 0.26, 0.75, 1.3))
save("goose_honk", hp(x, 120), 0.45)

d = 2.0  # goose_free: the cage bursts: a wooden crack and splinters, wire twangs, a flurry of wings, a honk
x = np.zeros(n(d))
mix(x, 0, 0.9 * thump(160, 50, 0.3, 0.08), 0.7 * wood(240, 0.3, 0.05), 0.4 * lp(s.noise(0.05), 5000) * env(n(0.05), 0.0005, 0.015, 3))
for k in range(16):  # splinters
    st = 0.25 * s.rng.uniform(0, 1) ** 1.6
    mix(x, n(st), s.rng.uniform(0.15, 0.45) * wood(s.rng.uniform(500, 1600), 0.05, 0.008))
mix(x, n(0.02), 0.25 * twang(330, 0.8, 0.25), 0.2 * twang(441, 0.7, 0.2))
for k in range(7):  # the goose's wings, a burst of beats getting going
    mix(x, n(0.15 + k * 0.13), (0.4 + 0.05 * k) * wingbeat(0.2))
mix(x, n(1.05), 0.9 * honk(270, 0.4, 1.0, 1.45))
save("goose_free", hp(x, 50), 0.7)

d = 1.0  # flap: big wing beats, a loop of 1 s: four beats, each a whoosh, over circular low air noise
N = n(d)
ph = np.arange(N) / N
x = 0.15 * band_noise(N, 120, 900, 1.2) * (0.6 + 0.4 * np.cos(2 * np.pi * 4 * ph))
for k in range(4):
    circ_mix(x, int(k * N / 4 + s.rng.uniform(-300, 300)), wingbeat(0.2, 0.9 + 0.1 * (k % 2)))
x -= np.mean(x)
s.save("flap", x, 0.4, fade=False)

d = 2.0  # lift: a creaky pulley loop: a low rumble of the drum, a ratchet click train, two long rope creaks
N = n(d)
ph = np.arange(N) / N
x = 0.35 * band_noise(N, 40, 250, 1.3) * (0.8 + 0.2 * np.sin(2 * np.pi * 2 * ph))
for k in range(16):  # ratchet pawl clicks, 8 per second
    circ_mix(x, int(k * N / 16), (0.35 if k % 2 == 0 else 0.25) * wood(900 + 60 * (k % 3), 0.04, 0.005))
for st, (f0, f1) in ((0.1, (330, 290)), (1.1, (300, 350))):  # the rope creaking round the wheel
    circ_mix(x, n(st), 0.35 * creak(f0, f1, 0.6, 1.0, 0.5))
circ_mix(x, n(0.62), 0.12 * twang(110, 0.4, 0.12))
x -= np.mean(x)
s.save("lift", x, 0.35, fade=False)

# --- death and jingles ---
d = 1.5  # die: no voice: a slide whistle falling a long way, a wooden bonk, a few little bounces
x = np.zeros(n(d))
ln = 0.8
fs = curve([(0, 1600), (0.08, 1750), (0.8, 300)], ln) * (1 + 0.03 * np.sin(2 * np.pi * 8 * t(ln)))
mix(x, 0, 0.35 * osc(fs, ln, ((1, 1.0), (2, 0.08))) * curve([(0, 0), (0.03, 1), (0.7, 0.8), (0.8, 0)], ln))
mix(x, 0, 0.05 * lp(hp(s.noise(ln), 1000), 3000) * curve([(0, 0), (0.03, 1), (0.8, 0)], ln))
mix(x, n(0.82), 1.0 * thump(140, 45, 0.3, 0.08), 0.6 * wood(190, 0.25, 0.05))
for k, (st, a) in enumerate(((1.05, 0.35), (1.2, 0.2), (1.3, 0.1))):
    mix(x, n(st), a * wood(260 + 40 * k, 0.12, 0.02), a * 0.8 * thump(120, 60, 0.08, 0.02))
save("die", x, 0.55)

d = 0.08  # bonus_tick: a small bright wooden tick with a blip, for counting down the time bonus
x = np.zeros(n(d))
mix(x, 0, 0.4 * wood(1800, 0.04, 0.004), 0.3 * osc(G6, 0.05, ((1, 1.0), (2, 0.1))) * env(n(0.05), 0.001, 0.012, 3))
save("bonus_tick", x, 0.28)

d = 2.3  # level_start: a farmyard jingle: a banjo roll up G, fiddle and harmonica answering, a bass and a chord
x = np.zeros(n(d))
roll = (G4, B4, D5, G4, B4, D5, G5, D5)
for i, f in enumerate(roll):
    mix(x, n(i * 0.1), 0.3 * banjo(f, 0.4))
for st, f in ((0.0, G2), (0.4, D3), (0.8, G2)):
    mix(x, n(st), 0.45 * bass(f, 0.45))
mix(x, n(0.8), 0.22 * fiddle(E5, 0.18), 0.22 * fiddle(D5, 0.12))
mix(x, n(1.0), 0.2 * fiddle(B4, 0.16))
mix(x, n(1.2), 0.25 * fiddle(G5, 1.0, 0.03, 0.4))
mix(x, n(1.2), 0.15 * harmonica(B4, 1.0, 0.03, 0.4), 0.12 * harmonica(D5, 1.0, 0.03, 0.4))
mix(x, n(1.2), 0.5 * bass(G2, 0.9))
for i, f in enumerate((G3, D4, G4, B4, D5)):
    mix(x, n(1.2 + i * 0.02), 0.13 * banjo(f, 0.9))
mix(x, n(1.2), 0.12 * glock(G6, 0.8, 0.3))
save("level_start", x, 0.6)

d = 2.8  # level_clear: a hoedown flourish: a banjo run, fiddle and harmonica in thirds, a shave and a big G chord
x = np.zeros(n(d))
for i, f in enumerate((D4, G4, B4, D5, E5, G5, B5, D6)):
    mix(x, n(i * 0.06), 0.24 * banjo(f, 0.35))
tune = ((0.5, D5, B4, 0.2), (0.72, E5, C5, 0.2), (0.94, Fs5, A4, 0.2), (1.16, G5, B4, 0.3), (1.5, A5, Fs5, 0.14),
        (1.66, B5, G5, 1.1))
for st, f, f2, lnb in tune:
    mix(x, n(st), 0.24 * fiddle(f, lnb, 0.02, 0.05 if lnb < 1 else 0.5), 0.16 * harmonica(f2, lnb, 0.02, 0.05 if lnb < 1 else 0.5))
for st, f in ((0.5, G2), (0.94, D3), (1.16, G2), (1.5, D3)):
    mix(x, n(st), 0.45 * bass(f, 0.35))
mix(x, n(1.66), 0.55 * bass(G2, 1.1))
for i, f in enumerate((G3, B3, D4, G4, B4, D5, G5)):
    mix(x, n(1.66 + i * 0.015), 0.1 * banjo(f, 1.1))
for i, f in enumerate((G5, B5, D6, G6)):
    mix(x, n(1.66 + i * 0.05), 0.09 * glock(f, 0.9, 0.3))
save("level_clear", x, 0.6)

d = 2.7  # game_over: a comic-sad slide down: the fiddle sighs G, F#, F, E (chromatic), the harmonica bends
x = np.zeros(n(d))  # a low wheeze, a last lonely banjo pluck and a bass thunk
for st, f in ((0.0, G4), (0.32, Fs4), (0.64, F4)):
    mix(x, n(st), 0.28 * fiddle(f, 0.3, 0.03, 0.08, 0.6))
fe = curve([(0, E4), (0.5, E4), (1.1, E4 * 0.94)], 1.1)
mix(x, n(0.96), 0.3 * fiddle(fe, 1.1, 0.03, 0.5, 0.5))
mix(x, n(0.96), 0.14 * harmonica(curve([(0, C4), (0.6, C4), (1.1, C4 * 0.94)], 1.1), 1.1, 0.05, 0.5))
for st, f in ((0.0, G2), (0.32, D3), (0.64, C3)):
    mix(x, n(st), 0.4 * bass(f, 0.3))
mix(x, n(0.96), 0.5 * bass(C3, 0.8))
mix(x, n(2.1), 0.5 * bass(G2, 0.5), 0.2 * banjo(G3, 0.5))
save("game_over", lp(x, 7000), 0.55)

d = 1.2  # extra_life: a quick banjo arpeggio up two octaves of G, a glockenspiel ring and a harmonica chord
x = np.zeros(n(d))
for i, f in enumerate((G4, B4, D5, G5, B5, D6)):
    mix(x, n(i * 0.05), 0.25 * banjo(f, 0.4))
mix(x, n(0.3), 0.14 * harmonica(G5, 0.7, 0.02, 0.4), 0.12 * harmonica(B5, 0.7, 0.02, 0.4))
for i, f in enumerate((G6, B6, D7)):
    mix(x, n(0.3 + i * 0.04), 0.14 * glock(f, 0.8, 0.3))
save("extra_life", x, 0.5)
