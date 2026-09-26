#!/usr/bin/env python3
"""Sound effects for game 15 (Mossfolk), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own: the moss creatures' voices are tiny formant chirps (a buzzy glottal pulse shaped by two or three
vowel resonances, pitched far above a human voice), never words and no imitation of any other game's voices.
Wood creaks are stick-slip pulse trains through resonant bodies, earth is filtered noise, bricks and picks are
struck partials, and the jingles are plucked strings (Karplus-Strong), reedy woodwind tones and small bells.
The dig loop is built on whole cycles and circular noise, so its end meets its start with no click.
Usage: python3 tools/audio/mossfolk_sfx.py [out_dir]   (default: godot/games/mossfolk/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/mossfolk/audio/sfx", seed=1991)
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
    """A tiny creature's voice: a harmonic pulse whose harmonics are weighted by vowel resonances.
    f0 and each formant frequency may be scalars or curves; formants are (freq, bandwidth, amplitude)."""
    N = n(sec)
    f0 = np.broadcast_to(np.asarray(f0, dtype=float), (N,))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = np.zeros(N)
    for k in range(1, 40):
        fk = k * f0
        g = sum(a / (1 + ((fk - np.broadcast_to(np.asarray(F, dtype=float), (N,))) / bw) ** 2) for F, bw, a in formants)
        x += np.sin(k * ph) * g * k ** -tilt * (fk < 15000)
    x += breath * lp(hp(s.noise(sec), 2000), 7000)
    return x


def chirp_env(sec, attack=0.015, release=0.05):
    N = n(sec)
    e = np.ones(N)
    a, r = n(attack), n(release)
    e[:a] = np.linspace(0, 1, a) ** 1.5
    e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong): harp when bright, pizzicato when damped. `bright` shapes the pick."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1 if i - p - 1 >= 0 else i - p])
    return y * env(N, 0.001, sec, 0.5)


def reed(f, sec, attack=0.04, decay=0.4, curve_=1.5, breath=0.1, vib=5.0):
    """A clarinet-like voice: odd harmonics, a vibrato that grows in, a breath of air."""
    tt = t(sec)
    fv = f * (1 + 0.006 * np.clip(tt / 0.25, 0, 1) * np.sin(2 * np.pi * vib * tt))
    ph = 2 * np.pi * np.cumsum(fv) / SR
    x = np.sin(ph) + 0.45 * np.sin(3 * ph) + 0.08 * np.sin(2 * ph) + 0.2 * np.sin(5 * ph) + 0.06 * np.sin(7 * ph)
    x = lp(x, min(5000, f * 6)) + breath * lp(hp(s.noise(sec), f), f * 4)
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


def dirt(sec, lo, hi, attack, decay, curve_=2.0):
    """A crumble of earth: band-passed noise with a grainy flutter."""
    x = lp(hp(s.noise(sec), lo), hi) * env(n(sec), attack, decay, curve_)
    return x * (0.6 + 0.4 * (s.rng.uniform(0, 1, n(sec)) > 0.6))


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def circ_mix(x, start, b):
    """Mixes b into x wrapping round the end: for grains placed in a loop."""
    for i in range(len(b)):
        x[(start + i) % len(x)] += b[i]


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude): a wooden body."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 0.6))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        y += a * np.convolve(x, ir)[:len(x)]
    return y


# --- the hatch and the start ---
d = 1.35  # the hatch opens: an old wooden trapdoor creaks on its hinge (stick-slip bursts), then drops open
x = np.zeros(n(d))  # with a hollow wooden clunk and a puff of dust
rate = curve([(0, 38), (0.3, 70), (0.55, 45), (0.8, 90), (0.95, 60)], 0.95)  # the hinge slips faster and slower
ph = np.cumsum(rate) / SR
pulses = np.zeros(n(0.95))
idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
pulses[idx] = s.rng.uniform(0.6, 1.0, len(idx))
body = resonate(pulses, ((310, 0.012, 1.0), (730, 0.008, 0.7), (1240, 0.005, 0.45), (2150, 0.003, 0.25)))
body *= curve([(0, 0), (0.05, 1), (0.85, 0.9), (0.95, 0)], 0.95)
mix(x, 0, body)
mix(x, n(0.93), 1.3 * resonate(np.r_[1.0, np.zeros(n(0.3))], ((140, 0.05, 1.0), (330, 0.03, 0.6), (590, 0.015, 0.3))))
mix(x, n(0.93), 0.9 * thump(120, 55, 0.2, 0.06))
mix(x, n(0.95), 0.25 * dirt(0.35, 300, 3000, 0.01, 0.12))
save("hatch_open", lp(x, 9000), 0.5)

d = 0.95  # "let's go": a chorus of five little creatures chirping "wheee!" together, staggered, at different pitches
x = np.zeros(n(d))
for k, (f, st, ln) in enumerate(((620, 0.0, 0.5), (760, 0.04, 0.46), (540, 0.07, 0.55), (880, 0.11, 0.42),
                                 (690, 0.15, 0.6))):
    f = f * s.rng.uniform(0.97, 1.03)
    f0 = curve([(0, f * 0.8), (0.08, f * 1.1), (ln * 0.7, f * 1.45), (ln, f * 1.3)], ln)
    f0 *= 1 + 0.02 * np.sin(2 * np.pi * 9 * t(ln))
    F1 = curve([(0, 700), (0.1, 1000), (ln, 950)], ln)  # an "ooh" opening into an "ee"
    F2 = curve([(0, 1100), (0.1, 2600), (ln, 2900)], ln)
    v = voice(f0, ((F1, 200, 1.0), (F2, 350, 0.7), (3800, 500, 0.25)), ln) * chirp_env(ln, 0.02, 0.15)
    mix(x, n(st), 0.35 * v)
save("lets_go", lp(x, 10000), 0.38)

# --- skills ---
d = 0.14  # a skill given: a soft click and a little rounded pop
x = 0.6 * woodblock(1400, d, 0.012)
mix(x, n(0.008), 0.8 * s.sweep(420, 900, 0.06) * env(n(0.06), 0.002, 0.02, 3))
save("assign", x, 0.4)

d = 0.05  # picking a skill in the panel: a tiny dry tick
x = woodblock(2200, d, 0.006) + 0.3 * hp(s.noise(d), 4000) * env(n(d), 0.0002, 0.0015, 3)
save("select", x, 0.25)

d = 0.6  # digging (a loop): paws scraping earth, two strokes a loop, pebbles ticking in the soil
N = n(d)
ph = np.arange(N) / N
stroke = 0.35 + 0.65 * np.sin(np.pi * ((ph * 2) % 1)) ** 2
x = band_noise(N, 150, 1400, 1.2) * stroke + 0.35 * band_noise(N, 1400, 5000) * stroke ** 2
x += 0.5 * np.sin(2 * np.pi * 2 * 55 * ph) * stroke ** 3  # the soft thud of each scoop (whole cycles)
for k in range(10):
    g = woodblock(s.rng.uniform(1800, 3500), 0.02, 0.003)
    circ_mix(x, int(s.rng.uniform(0, N)), 0.35 * s.rng.uniform(0.4, 1) * g)
x -= np.mean(x)
s.save("dig", x, 0.3, fade=False)

d = 0.4  # bashing through a wall: a soft heavy thump into earth and a crumble
x = np.zeros(n(d))
mix(x, 0, thump(140, 45, 0.3, 0.08))
mix(x, 0, 0.5 * lp(s.noise(0.08), 900) * env(n(0.08), 0.001, 0.02, 3))
mix(x, n(0.02), 0.4 * dirt(0.35, 200, 2500, 0.01, 0.12))
save("bash", x, 0.55)

d = 0.45  # mining: a pick clinks on stone, a ringing metal tick, grit falling
x = np.zeros(n(d))
mix(x, 0, 0.6 * s.bell(2350, 0.4, partials=((1, 1.0), (1.53, 0.6), (2.41, 0.4), (3.9, 0.2)), decay=0.3))
mix(x, 0, 0.6 * hp(s.noise(0.01), 2500) * env(n(0.01), 0.0002, 0.002, 3))
mix(x, 0, 0.4 * thump(300, 150, 0.05, 0.015))
mix(x, n(0.02), 0.2 * dirt(0.3, 1500, 6000, 0.01, 0.08))
save("mine", x, 0.45)

d = 0.16  # a brick laid: a clay tile tapped into place, a clear pitch (C6) so the game can raise it per step
tt = t(d)
x = (np.sin(2 * np.pi * 1046.5 * tt) + 0.35 * np.sin(2 * np.pi * 1046.5 * 2.32 * tt) * np.exp(-tt / 0.01)
     + 0.15 * np.sin(2 * np.pi * 1046.5 * 3.9 * tt) * np.exp(-tt / 0.006)) * env(n(d), 0.0005, 0.035, 3)
x += 0.4 * thump(400, 250, d, 0.01) + 0.25 * hp(s.noise(d), 3000) * env(n(d), 0.0002, 0.0015, 3)
save("build", x, 0.4)

d = 0.42  # the builder is running out of bricks: three quick rising ticks
x = np.zeros(n(d))
for i, f in enumerate((1318.5, 1568.0, 1975.5)):
    mix(x, n(i * 0.11), 0.6 * glock(f, 0.25, 0.12))
    mix(x, n(i * 0.11), 0.4 * woodblock(f * 0.75, 0.05, 0.01))
save("builder_warn", x, 0.35)

d = 0.34  # a shrug: a tiny closed-mouth "hm?" that lifts at the end
f0 = curve([(0, 520), (0.14, 500), (0.28, 700), (0.34, 740)], d)
v = voice(f0, ((420, 150, 1.0), (1600, 400, 0.25), (2800, 500, 0.1)), d, breath=0.02)  # nasal "m"
save("shrug", lp(v * chirp_env(d, 0.03, 0.08), 6000), 0.2)

d = 0.5  # panic: a squeaky two-note alarm chirp, high then a drop (a creature's "uh-oh" in tone, not words)
x = np.zeros(n(d))
for st, ln, f_a, f_b in ((0.0, 0.16, 900, 980), (0.2, 0.28, 760, 640)):
    f0 = curve([(0, f_a), (ln, f_b)], ln) * (1 + 0.03 * np.sin(2 * np.pi * 14 * t(ln)))
    v = voice(f0, ((850, 200, 1.0), (1500, 300, 0.6), (3200, 500, 0.3)), ln, 0.05)  # an "uh"/"oh" colour
    mix(x, n(st), v * chirp_env(ln, 0.01, 0.06))
save("panic", lp(x, 9000), 0.24)

d = 0.5  # pop: a cute rounded pop (a quick rising bubble) with a soft puff of air and a sparkle
x = np.zeros(n(d))
mix(x, 0, 0.9 * s.sweep(300, 1300, 0.05) * env(n(0.05), 0.001, 0.02, 3))
mix(x, 0, 0.5 * hp(s.noise(0.01), 1500) * env(n(0.01), 0.0002, 0.002, 3))
puff = lp(s.noise(0.4), np.geomspace(2500, 400, n(0.4))) * env(n(0.4), 0.02, 0.1, 2.5)
mix(x, n(0.01), 0.5 * puff)
mix(x, n(0.03), 0.18 * glock(2637, 0.4, 0.15))
save("pop", x, 0.5)

d = 0.4  # splat: a soft squelch, a wet down-glide and a smack
x = np.zeros(n(d))
mix(x, 0, 0.7 * lp(s.noise(0.2), np.geomspace(3000, 300, n(0.2))) * env(n(0.2), 0.001, 0.05, 3))
mix(x, 0, 0.7 * thump(260, 70, 0.25, 0.06))
wob = s.sweep(500, 180, 0.2) * env(n(0.2), 0.005, 0.07, 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t(0.2)))
mix(x, n(0.02), 0.4 * wob)
save("splat", lp(x, 7000), 0.5)

d = 1.1  # drowning: a gloop into the water and bubbles rising, fewer and higher as it sinks
x = np.zeros(n(d))
mix(x, 0, 0.6 * lp(s.noise(0.12), 1200) * env(n(0.12), 0.002, 0.03, 3))
mix(x, 0, 0.6 * thump(180, 60, 0.3, 0.08))
for k in range(12):
    fr = s.rng.uniform(350, 700) * (1 + k * 0.08)
    ln = s.rng.uniform(0.03, 0.06)
    st = 0.08 + k * 0.07 + s.rng.uniform(0, 0.03)
    mix(x, n(st), (0.5 - k * 0.03) * s.sweep(fr, fr * 2.2, ln) * env(n(ln), 0.002, ln * 0.4, 3))
save("drown", lp(x, 6000), 0.5)

d = 0.62  # yippee: a happy two-hop chirp that leaps up, and a glint as the creature slips into its burrow
x = np.zeros(n(d))
for st, ln, pts in ((0.0, 0.13, ((0, 700), (0.13, 880))), (0.15, 0.3, ((0, 900), (0.1, 1350), (0.3, 1250)))):
    f0 = curve(pts, ln) * (1 + 0.02 * np.sin(2 * np.pi * 11 * t(ln)))
    v = voice(f0, ((950, 220, 1.0), (2700, 400, 0.8), (3900, 500, 0.25)), ln, 0.04)  # a bright "ee"
    mix(x, n(st), 0.6 * v * chirp_env(ln, 0.01, 0.07))
mix(x, n(0.3), 0.15 * glock(2093, 0.3, 0.12) + 0.12 * glock(3136, 0.3, 0.1))
save("yippee", lp(x, 10000), 0.3)

# --- hazards ---
d = 0.5  # a snapping plant trap: jaws crack shut (a sharp woody snap), then leaves rustle and settle
x = np.zeros(n(d))
mix(x, 0, 1.0 * hp(s.noise(0.015), 1500) * env(n(0.015), 0.0002, 0.004, 3))
mix(x, 0, 0.8 * resonate(np.r_[1.0, np.zeros(n(0.1))], ((520, 0.02, 1.0), (1180, 0.01, 0.5), (2600, 0.005, 0.3))))
mix(x, n(0.005), 0.5 * thump(300, 120, 0.08, 0.02))
rustle = lp(hp(s.noise(0.4), 2500), 8000) * env(n(0.4), 0.02, 0.1, 2)
rustle *= 0.5 + 0.5 * (np.sin(2 * np.pi * 23 * t(0.4)) > 0.2)
mix(x, n(0.04), 0.25 * rustle)
save("snap", x, 0.55)

d = 0.8  # crushed: a heavy stone slab drops, a deep thud, grit and pebbles pattering down
x = np.zeros(n(d))
mix(x, 0, thump(95, 32, 0.6, 0.15))
mix(x, 0, 0.6 * lp(s.noise(0.15), 700) * env(n(0.15), 0.001, 0.04, 3))
mix(x, 0, 0.35 * dirt(0.6, 300, 4000, 0.005, 0.18))
for k in range(8):
    mix(x, n(0.1 + k * 0.05 + s.rng.uniform(0, 0.03)), 0.15 * woodblock(s.rng.uniform(1500, 3000), 0.03, 0.004))
save("crush", x, 0.6)

d = 1.6  # "pop them all": a rising alarm, a warbling whistle climbing faster and faster over a ticking pulse
x = np.zeros(n(d))
f0 = np.geomspace(500, 1600, n(d))
wr = np.geomspace(5, 16, n(d))
wob = 1 + 0.06 * np.sin(2 * np.pi * np.cumsum(wr) / SR)
ph = 2 * np.pi * np.cumsum(f0 * wob) / SR
siren = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * curve([(0, 0), (0.1, 0.7), (1.4, 1), (1.6, 0)], d)
x += 0.4 * siren
for k, tk in enumerate(np.cumsum(np.geomspace(0.16, 0.06, 14))):
    mix(x, n(tk - 0.16), 0.35 * woodblock(900 + 60 * k, 0.06, 0.01))
save("nuke", lp(x, 9000), 0.33)

# --- level end ---
d = 3.0  # level done: a pizzicato run up, a clarinet tune answered by the glockenspiel, a full C major chord
x = np.zeros(n(d))  # with a woodblock kick, bells ringing out
for i, f in enumerate((261.6, 329.6, 392.0, 523.3, 659.3, 784.0)):
    mix(x, n(i * 0.07), 0.4 * pluck(f, 0.5, 0.45, 0.994))
for st, f, ln in ((0.5, 659.3, 0.2), (0.72, 784.0, 0.2), (0.94, 880.0, 0.2), (1.16, 784.0, 0.3), (1.5, 1046.5, 1.3)):
    mix(x, n(st), 0.35 * reed(f / 2, ln, 0.015, ln * 0.8, 1.5, 0.06))
    mix(x, n(st), 0.12 * glock(f * 2, 0.5, 0.2))
for f in (130.8, 196.0, 261.6, 329.6, 392.0):
    mix(x, n(1.5), 0.14 * reed(f, 1.4, 0.05, 0.9, 1.4, 0.04))
for i, f in enumerate((261.6, 392.0, 523.3, 659.3, 784.0, 1046.5)):
    mix(x, n(1.5 + i * 0.035), 0.25 * pluck(f, 1.3, 0.5, 0.997))
mix(x, n(1.5), 0.5 * thump(130, 50, 0.3, 0.08))
for i, st in enumerate((0.5, 0.94, 1.38)):
    mix(x, n(st), 0.2 * woodblock(900 if i % 2 else 1200, 0.1, 0.02))
for k in range(8):
    mix(x, n(1.55 + k * 0.13), 0.09 * glock(s.rng.choice((2093.0, 2637.0, 3136.0)), 0.6, 0.25))
save("level_done", x, 0.6)

d = 2.6  # level failed: a gentle falling bassoon-like line in A minor, a soft pizzicato echo, a quiet low chord
x = np.zeros(n(d))
for i, (f, ln) in enumerate(((329.6, 0.35), (293.7, 0.35), (261.6, 0.35), (246.9, 0.6))):
    mix(x, n(i * 0.36), 0.35 * reed(f / 2, ln + 0.1, 0.03, ln * 0.7, 1.6, 0.08, 4.5))
    mix(x, n(i * 0.36 + 0.18), 0.14 * pluck(f, 0.5, 0.3, 0.993))
for f in (110.0, 164.8, 220.0, 261.6, 329.6):
    mix(x, n(1.45), 0.15 * reed(f, 1.15, 0.08, 0.6, 1.5, 0.05, 4.0))
mix(x, n(1.45), 0.3 * pluck(110.0, 1.0, 0.25, 0.995))
save("level_fail", lp(x, 7000), 0.55)

d = 0.1  # a clock tick for the last seconds: a bright woodblock knock
x = woodblock(1650, d, 0.02) + 0.2 * glock(3300, d, 0.03)
save("tick", x, 0.3)
