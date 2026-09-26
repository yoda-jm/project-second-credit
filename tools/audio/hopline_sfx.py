#!/usr/bin/env python3
"""Sound effects for game 16 (Hopline), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game: the frogs' voices are pulsed formant croaks
(a buzzy glottal pulse gated in quick bursts, shaped by vowel resonances), the hop is a sine "boing" with a
decaying spring wobble, water is filtered noise plus rising-pitch bubble resonances, car horns are two detuned
reedy tones a third apart (soft attack, low-passed so they never bark), and the jingles are plucked strings
(Karplus-Strong, banjo-like when bright), a reedy clarinet-ish voice and small bells, in F major like the music.
The ambience loops (town traffic, the canal) are built on circular noise, whole-cycle swells and events wrapped
round the end, so the last sample meets the first with no seam.
Usage: python3 tools/audio/hopline_sfx.py [out_dir]   (default: godot/games/hopline/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/hopline/audio/sfx", seed=1981)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, b):
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


def voice(f0, formants, sec, breath=0.06, tilt=0.8):
    """A harmonic pulse whose harmonics are weighted by vowel resonances (freq, bandwidth, amplitude);
    f0 and each formant frequency may be scalars or curves."""
    N = n(sec)
    f0 = np.broadcast_to(np.asarray(f0, dtype=float), (N,))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = np.zeros(N)
    for k in range(1, 48):
        fk = k * f0
        g = sum(a / (1 + ((fk - np.broadcast_to(np.asarray(F, dtype=float), (N,))) / bw) ** 2) for F, bw, a in formants)
        x += np.sin(k * ph) * g * k ** -tilt * (fk < 15000)
    x += breath * lp(hp(s.noise(sec), 2000), 7000)
    return x


def gate(sec, rate, duty=0.55, sharp=3.0):
    """Quick amplitude bursts at `rate` per second (scalar or curve): the pulsing of a frog's call."""
    r = np.broadcast_to(np.asarray(rate, dtype=float), (n(sec),))
    ph = np.cumsum(r) / SR % 1
    return np.clip(np.sin(np.pi * np.clip(ph / duty, 0, 1)), 0, 1) ** sharp


def croak(sec, f0, formants, rate, breath=0.04):
    """A frog's croak: a low buzzy voice gated into pulses, with soft ends."""
    v = voice(f0, formants, sec, breath, tilt=0.6) * gate(sec, rate)
    e = np.ones(n(sec))
    a, r = n(0.012), n(min(0.05, sec / 3))
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return v * e


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong): banjo-like when bright, pizzicato when damped."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1 if i - p - 1 >= 0 else i - p])
    return y * env(N, 0.001, sec, 0.5)


def reed(f, sec, attack=0.03, decay=0.4, curve_=1.5, breath=0.08, vib=5.0):
    """A clarinet-like voice: odd harmonics, a vibrato that grows in, a breath of air."""
    tt = t(sec)
    fv = np.broadcast_to(np.asarray(f, dtype=float), tt.shape) * (1 + 0.006 * np.clip(tt / 0.25, 0, 1) * np.sin(2 * np.pi * vib * tt))
    ph = 2 * np.pi * np.cumsum(fv) / SR
    x = np.sin(ph) + 0.45 * np.sin(3 * ph) + 0.08 * np.sin(2 * ph) + 0.2 * np.sin(5 * ph) + 0.06 * np.sin(7 * ph)
    fm = float(np.max(fv))
    x = lp(x, min(5000, fm * 6)) + breath * lp(hp(s.noise(sec), fm), fm * 4)
    return x * env(n(sec), attack, decay, curve_)


def glock(f, sec=0.8, decay=0.35):
    """A glockenspiel bar: a bright fundamental with the high inharmonic partials of a struck bar."""
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def woodblock(f, sec=0.12, decay=0.03):
    """A hollow wooden knock: a couple of damped modes and a click."""
    tt = t(sec)
    x = np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2.57 * tt) * np.exp(-tt / (decay * 0.4))
    return x * env(n(sec), 0.0005, decay, 3) + 0.3 * hp(s.noise(sec), 3000) * env(n(sec), 0.0002, 0.002, 3)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def bubble(f, sec):
    """One bubble: a sine whose pitch rises as it forms (the classic water 'plip')."""
    f_c = f * np.geomspace(1, 2.2, n(sec))
    return np.sin(2 * np.pi * np.cumsum(f_c) / SR) * env(n(sec), 0.001, sec * 0.35, 3)


def horn(f_lo, f_hi, sec, attack=0.02, bright=2600):
    """A car horn: two reedy tones a third apart, slightly detuned against each other, with a soft onset,
    a little pitch sag as the note starts, low-passed so it toots rather than blares."""
    tt = t(sec)
    sag = 1 - 0.015 * np.exp(-tt / 0.03)
    x = np.zeros(n(sec))
    for f, a in ((f_lo, 1.0), (f_hi, 0.85)):
        ph = 2 * np.pi * np.cumsum(f * sag) / SR
        x += a * (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.35 * np.sin(3 * ph) + 0.18 * np.sin(4 * ph) + 0.1 * np.sin(5 * ph))
    e = np.clip(tt / attack, 0, 1) ** 1.5 * np.clip((sec - tt) / 0.03, 0, 1)
    return lp(x, bright) * e


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def circ_mix(x, start, b):
    """Mixes b into x wrapping round the end: for sounds placed in a loop."""
    idx = (start + np.arange(len(b))) % len(x)
    np.add.at(x, idx, b)


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude)."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 0.6))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        y += a * np.convolve(x, ir)[:len(x)]
    return y


# F major notes, used by the jingles
F3, A3, C4, D4, E4, F4, G4, A4, Bb4, C5, D5, E5, F5, G5, A5, C6, F6 = (
    174.6, 220.0, 261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 466.2, 523.3, 587.3, 659.3, 698.5, 784.0, 880.0,
    1046.5, 1396.9)

# --- the frog ---
d = 0.2  # hop: a springy "boing" centred on one pitch (A4-ish) so the game can vary pitch_scale per hop;
x = np.zeros(n(d))  # a sine that bends up and wobbles like a spring, over a soft padded push-off
tt = t(d)
wob = 1 + 0.12 * np.sin(2 * np.pi * 28 * tt) * np.exp(-tt / 0.05)
f = curve([(0, 330), (0.035, 470), (0.2, 450)], d) * wob
ph = 2 * np.pi * np.cumsum(f) / SR
mix(x, 0, (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env(n(d), 0.003, 0.07, 3))
mix(x, 0, 0.5 * thump(160, 80, 0.06, 0.015))
mix(x, 0, 0.15 * lp(s.noise(0.02), 1500) * env(n(0.02), 0.0005, 0.005, 3))
save("hop", x, 0.42)

d = 0.8  # splat: a cartoon squish (a wet down-glide with a wobbly smack) and a short honk from the car
x = np.zeros(n(d))
mix(x, 0, 0.8 * lp(s.noise(0.2), np.geomspace(3500, 250, n(0.2))) * env(n(0.2), 0.001, 0.05, 3))
mix(x, 0, 0.8 * thump(240, 60, 0.25, 0.06))
sq = s.sweep(700, 160, 0.22) * env(n(0.22), 0.004, 0.08, 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 34 * t(0.22)))
mix(x, n(0.015), 0.5 * sq)
mix(x, n(0.03), 0.3 * croak(0.12, curve([(0, 260), (0.12, 150)], 0.12), ((700, 200, 1), (1400, 300, 0.4)), 45))
mix(x, n(0.26), 0.25 * horn(392, 494, 0.38, 0.015))  # the honk (G4 and B4): a driver's startled toot
save("splat", lp(x, 8000), 0.5)

d = 0.9  # plop: the frog drops into the canal: a hollow "plop" bubble, a splash, bubbles rising after
x = np.zeros(n(d))
mix(x, 0, 0.6 * bubble(260, 0.09))
mix(x, 0, 0.3 * thump(200, 70, 0.2, 0.05))
splash = lp(hp(s.noise(0.3), 500), np.geomspace(5000, 900, n(0.3))) * env(n(0.3), 0.003, 0.07, 2.5)
mix(x, n(0.01), 0.8 * splash)
for k in range(9):
    fr = s.rng.uniform(450, 900) * (1 + k * 0.06)
    ln = s.rng.uniform(0.025, 0.05)
    mix(x, n(0.12 + k * 0.07 + s.rng.uniform(0, 0.03)), (0.4 - k * 0.03) * bubble(fr, ln))
save("plop", lp(x, 7000), 0.5)

d = 1.1  # home: a happy two-part croak that lifts ("rib-bit!"), then a bright chime (C6 E6 G6 over a pluck)
x = np.zeros(n(d))
mix(x, 0, 0.7 * croak(0.13, curve([(0, 190), (0.13, 210)], 0.13), ((650, 220, 1), (1500, 350, 0.5), (2600, 500, 0.2)), 38))
mix(x, n(0.15), 0.8 * croak(0.2, curve([(0, 230), (0.1, 300), (0.2, 290)], 0.2),
                             ((800, 240, 1), (1900, 400, 0.6), (2900, 500, 0.25)), 42))
for i, f in enumerate((C6, 1318.5, 1568.0)):
    mix(x, n(0.36 + i * 0.07), 0.3 * glock(f, 0.7, 0.3))
mix(x, n(0.36), 0.35 * pluck(C5, 0.7, 0.6, 0.996) + 0.2 * pluck(E5, 0.7, 0.6, 0.996))
save("home", x, 0.55)

d = 2.6  # all five home: a jaunty fanfare, a banjo run up, a clarinet call answered by bells, a full F chord
x = np.zeros(n(d))  # with a kick and a cymbal-ish shimmer, and a proud croak on top
for i, f in enumerate((F3, A3, C4, F4, A4, C5)):
    mix(x, n(i * 0.06), 0.35 * pluck(f, 0.45, 0.8, 0.993))
call = ((0.40, C5, 0.14), (0.56, C5, 0.14), (0.72, D5, 0.14), (0.88, E5, 0.2), (1.12, G5, 0.12), (1.26, F5, 1.25))
for st, f, ln in call:
    mix(x, n(st), 0.38 * reed(f / 2, ln, 0.012, ln * 0.8, 1.4, 0.05))
    mix(x, n(st), 0.1 * glock(f * 2, 0.4, 0.15))
for f in (F3, C4, F4, A4, C5):
    mix(x, n(1.26), 0.12 * reed(f, 1.25, 0.04, 0.9, 1.3, 0.03))
for i, f in enumerate((F3, C4, F4, A4, C5, F5)):
    mix(x, n(1.26 + i * 0.03), 0.22 * pluck(f, 1.2, 0.75, 0.997))
for st in (0.4, 0.72, 1.26):
    mix(x, n(st), 0.5 * thump(120, 50, 0.25, 0.07))
shim = hp(s.noise(1.2), 6000) * env(n(1.2), 0.002, 0.4, 2.5)
mix(x, n(1.26), 0.1 * shim)
mix(x, n(1.35), 0.35 * croak(0.3, curve([(0, 240), (0.15, 330), (0.3, 320)], 0.3),
                             ((850, 250, 1), (2000, 400, 0.6), (3000, 500, 0.2)), 40))
for k in range(7):
    mix(x, n(1.4 + k * 0.12), 0.07 * glock(s.rng.choice((F6, 1760.0, 2093.0)), 0.5, 0.2))
save("all_home", x, 0.6)

d = 0.6  # fly: a quick tongue "thwip" and a gulp, then a sparkle climbing (A6 C7 F7)
x = np.zeros(n(d))
mix(x, 0, 0.5 * s.sweep(1800, 500, 0.05) * env(n(0.05), 0.001, 0.02, 3))
mix(x, 0, 0.25 * hp(s.noise(0.03), 3000) * env(n(0.03), 0.0005, 0.008, 3))
mix(x, n(0.06), 0.5 * s.sweep(220, 120, 0.07) * env(n(0.07), 0.004, 0.025, 3))
for i, f in enumerate((1760.0, 2093.0, 2793.8)):
    mix(x, n(0.1 + i * 0.05), 0.22 * glock(f, 0.4, 0.15))
save("fly", x, 0.4)

d = 0.9  # lady: a sweet two-note (C5 then A5, a sixth up) on bells and a soft reed, with a tiny high chirp
x = np.zeros(n(d))
mix(x, 0, 0.3 * glock(C6, 0.6, 0.3))
mix(x, 0, 0.25 * reed(C5, 0.3, 0.02, 0.25, 1.5, 0.03))
mix(x, n(0.22), 0.35 * glock(1760.0, 0.6, 0.35) + 0.3 * reed(A5, 0.6, 0.02, 0.45, 1.5, 0.03))
mix(x, n(0.26), 0.25 * croak(0.12, curve([(0, 420), (0.12, 560)], 0.12), ((1100, 250, 1), (2800, 400, 0.6)), 50))
save("lady", x, 0.4)

d = 0.95  # time running low: tick-tock knocks under a two-tone whistle that bends up (a clock's worried "hurry!")
x = np.zeros(n(d))
for i in range(4):
    mix(x, n(i * 0.22), 0.5 * woodblock(1700 if i % 2 == 0 else 1250, 0.08, 0.015))
for st, a, b in ((0.0, 1400, 1700), (0.44, 1500, 1900)):
    ln = 0.3
    f = curve([(0, a), (ln, b)], ln) * (1 + 0.012 * np.sin(2 * np.pi * 7 * t(ln)))
    w = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.1 * lp(hp(s.noise(ln), 1200), 4000)
    mix(x, n(st), 0.35 * w * curve([(0, 0), (0.03, 1), (0.25, 0.9), (0.3, 0)], ln))
save("time_warn", x, 0.35)

d = 0.75  # time up: a warm buzzer, two low tones beating against each other, not a harsh square
x = np.zeros(n(d))
tt = t(0.7)
for f in (110.0, 116.5, 220.0):
    ph = 2 * np.pi * f * tt
    mix(x, 0, (np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.45 * np.sin(3 * ph) + 0.3 * np.sin(5 * ph)) * (0.5 if f > 200 else 1))
x[:n(0.7)] *= np.clip(tt / 0.01, 0, 1) * np.clip((0.7 - tt) / 0.06, 0, 1)
save("time_up", lp(x, 1800), 0.33)

d = 1.3  # extra life: a banjo arpeggio climbing two octaves and a bell chord at the top
x = np.zeros(n(d))
for i, f in enumerate((F4, A4, C5, F5, A5, C6)):
    mix(x, n(i * 0.07), 0.35 * pluck(f, 0.6, 0.8, 0.995))
    mix(x, n(i * 0.07), 0.08 * glock(f * 2, 0.3, 0.12))
for f in (F5, A5, C6):
    mix(x, n(0.45), 0.2 * glock(f * 2, 0.8, 0.35))
mix(x, n(0.45), 0.3 * reed(F5, 0.7, 0.02, 0.5, 1.4, 0.03))
save("extra_life", x, 0.5)

d = 2.1  # ready: a start jingle in the ragtime spirit of the theme (not its tune): a banjo and clarinet line
x = np.zeros(n(d))  # over a stride bass (root, chord, fifth, chord), a chromatic pickup to a held F6 chord, a croak
beat = 60 / 150
line = ((0, C5, 0.5), (0.5, D5, 0.5), (1, E5, 0.5), (1.5, G5, 1.0), (2.5, E5, 0.5), (3, 622.3, 0.5),
        (3.5, E5, 0.5), (4, F5, 1.5))
for b, f, ln in line:
    mix(x, n(b * beat), 0.35 * reed(f / 2, ln * beat, 0.012, ln * beat * 0.8, 1.5, 0.05))
    mix(x, n(b * beat), 0.22 * pluck(f, 0.5, 0.85, 0.994))
for b, f in ((0, F3 / 2), (1, None), (2, 130.8), (3, None), (4, F3 / 2)):
    if f is None:  # the off-beat chord
        for g in (A3, C4, F4):
            mix(x, n(b * beat), 0.12 * pluck(g, 0.3, 0.5, 0.99))
    else:
        mix(x, n(b * beat), 0.4 * pluck(f, 0.6, 0.35, 0.995))
for f in (F3, A3, D4, F4, A4):  # the F6 chord (F A D F A) rings out
    mix(x, n(4 * beat), 0.12 * pluck(f, 1.3, 0.7, 0.998))
for b in range(5):
    mix(x, n(b * beat), 0.2 * woodblock(900 if b % 2 else 1300, 0.06, 0.012))
mix(x, n(4 * beat + 0.3), 0.3 * croak(0.24, curve([(0, 200), (0.24, 250)], 0.24), ((700, 220, 1), (1700, 380, 0.5)), 36))
save("ready", x, 0.55)

d = 2.6  # game over: a comic-sad clarinet line sagging down in half steps, a low pluck, a slow deflated croak
x = np.zeros(n(d))
for i, (f, ln) in enumerate(((A4, 0.3), (415.3, 0.3), (G4, 0.3), (370.0, 0.9))):
    st = i * 0.34
    if ln > 0.5:  # the last note droops a touch, like a sigh
        f = curve([(0, f), (0.4, f), (0.9, f * 0.97)], ln)
    mix(x, n(st), 0.4 * reed(f, ln, 0.03, ln * 0.8, 1.4, 0.06, 4.5))
for f in (87.3, 130.8, 174.6):
    mix(x, n(1.02), 0.25 * pluck(f, 1.4, 0.3, 0.997))
mix(x, n(1.02), 0.12 * reed(185.0, 1.3, 0.1, 0.8, 1.4, 0.03))  # F#3: a sour, comic final chord
mix(x, n(1.7), 0.35 * croak(0.55, curve([(0, 160), (0.55, 105)], 0.55), ((520, 200, 1), (1200, 300, 0.4)), 22))
save("game_over", lp(x, 7000), 0.45)

# --- the canal ---
d = 0.8  # turtle dive: a bubbly "blub-blub" as the shell sinks: lower, slower bubbles and a soft gulp
x = np.zeros(n(d))
mix(x, 0, 0.5 * lp(s.noise(0.1), 900) * env(n(0.1), 0.003, 0.03, 3))
for k in range(8):
    fr = 520 * (0.92 ** k) * s.rng.uniform(0.9, 1.1)
    ln = 0.05 + 0.01 * k
    mix(x, n(0.02 + k * 0.075 + s.rng.uniform(0, 0.02)), (0.7 - 0.05 * k) * bubble(fr, ln))
mix(x, 0, 0.3 * thump(150, 70, 0.3, 0.1))
save("turtle_dive", lp(x, 5000), 0.45)

d = 0.6  # croc snap: a low gravelly rumble as the jaws open, then a hard woody clack and a thud
x = np.zeros(n(d))
gr = lp(s.noise(0.2), 400) * gate(0.2, 32, 0.5, 2) * curve([(0, 0), (0.15, 1), (0.2, 0.8)], 0.2)
mix(x, 0, 0.6 * gr + 0.3 * s.sweep(70, 90, 0.2) * curve([(0, 0), (0.18, 1), (0.2, 0.5)], 0.2))
mix(x, n(0.2), 1.0 * hp(s.noise(0.012), 1500) * env(n(0.012), 0.0002, 0.003, 3))
mix(x, n(0.2), 0.9 * resonate(np.r_[1.0, np.zeros(n(0.15))], ((380, 0.025, 1.0), (910, 0.012, 0.5), (2100, 0.005, 0.3))))
mix(x, n(0.2), 0.6 * thump(180, 60, 0.15, 0.04))
save("croc_snap", x, 0.55)

# --- the street ---
d = 0.42  # horn A: a small car's quick double toot (A4 and C#5)
x = np.zeros(n(d))
mix(x, 0, horn(440, 554, 0.12))
mix(x, n(0.17), horn(440, 554, 0.22))
save("horn_a", x, 0.3)

d = 0.45  # horn B: a delivery van's single lower honk (E4 and G#4), a little rounder
x = horn(330, 415, 0.42, 0.03, 2000)
save("horn_b", x, 0.28)

# --- ambience loops ---
d = 8.0  # distant town traffic: exactly 8 s, a low city hum, tyre hiss swelling in whole cycles, cars passing
N = n(d)  # far off (an engine tone that swells and drops in pitch), a faint bicycle bell; all wrapped round the end
tt = np.arange(N) / SR
x = 0.5 * band_noise(N, 30, 220, 1.2) * (0.8 + 0.2 * np.sin(2 * np.pi * 2 * tt / d))
x += 0.12 * band_noise(N, 400, 2500) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * tt / d + 0.7))
for k, (st, f0, ln) in enumerate(((0.3, 95, 3.0), (2.6, 120, 2.6), (4.9, 80, 3.4), (6.6, 110, 2.8))):
    m = n(ln)
    u = np.arange(m) / m
    f = f0 * (1.06 - 0.12 / (1 + np.exp(-(u - 0.5) * 10)))  # the engine pitch drops as the car passes
    ph = 2 * np.pi * np.cumsum(f) / SR
    eng = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)
    hiss = lp(hp(s.noise(ln), 600), 3000)
    car = (0.5 * lp(eng, 600) + 0.6 * hiss) * np.sin(np.pi * u) ** 3
    circ_mix(x, n(st), 0.35 * car)
for st in (3.7,):  # a far-off bicycle bell, two rings
    for j in range(2):
        circ_mix(x, n(st + j * 0.14), 0.05 * s.bell(2350, 0.5, partials=((1, 1.0), (1.5, 0.4), (2.4, 0.3)), decay=0.4))
x -= np.mean(x)
s.save("traffic_loop", lp(np.r_[x[-n(0.05):], x], 6000)[n(0.05):], 0.2, fade=False)

d = 8.0  # the canal: exactly 8 s, water lapping at the stones in whole-cycle swells, small splashes, a few
N = n(d)  # frogs croaking far and near, a bubble now and then; every event wrapped round the end
tt = np.arange(N) / SR
x = 0.4 * band_noise(N, 60, 600) * (0.6 + 0.25 * np.sin(2 * np.pi * 4 * tt / d) + 0.15 * np.sin(2 * np.pi * 3 * tt / d + 1))
x += 0.05 * band_noise(N, 800, 4000) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * tt / d))
for k in range(7):  # laps
    ln = s.rng.uniform(0.5, 0.9)
    lap = lp(hp(s.noise(ln), 300), s.rng.uniform(1300, 2400)) * np.sin(np.pi * t(ln) / ln) ** 3
    lap *= 1 + 0.5 * np.sin(2 * np.pi * s.rng.uniform(8, 13) * t(ln))
    circ_mix(x, n(k * d / 7 + s.rng.uniform(0, 0.6)), 0.3 * lap)
for st, f0, ln, rate, a in ((0.9, 150, 0.35, 30, 0.22), (1.35, 150, 0.25, 30, 0.2), (4.2, 220, 0.2, 45, 0.12),
                            (4.45, 230, 0.2, 45, 0.12), (6.3, 120, 0.5, 24, 0.18), (7.6, 260, 0.15, 50, 0.1)):
    fr = croak(ln, f0 * (1 + 0.05 * np.sin(np.pi * t(ln) / ln)), ((550, 200, 1), (1300, 300, 0.45), (2400, 500, 0.15)), rate)
    circ_mix(x, n(st), a * lp(fr, 3500))
for k in range(6):  # bubbles surfacing
    circ_mix(x, int(s.rng.uniform(0, N)), 0.08 * bubble(s.rng.uniform(500, 900), 0.04))
x -= np.mean(x)
s.save("river_loop", lp(np.r_[x[-n(0.05):], x], 7000)[n(0.05):], 0.25, fade=False)
