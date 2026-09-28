#!/usr/bin/env python3
"""Sound effects for game 21 (Deep Breath), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. A miner hurries through themed caverns before
his air runs out, played as a jaunty cartoon. Timber is the floor material: steps and landings are hollow plank
knocks (low wooden modes) over a soft heel thud. The keys are crystals: a glassy bell with high inharmonic
partials and a sparkle. Metal (the lift gate, the carts, the drill) rings through inharmonic resonant modes.
Every loop (the conveyor, the crumbling floor, the three guardians, the air warning) is built on circular
noise, whole-number cycles and grains wrapped round the loop, so it has no seam.
The jingles are in G (minor for danger, major for the clear) like the music, with its band: pizzicato strings
(Karplus-Strong), a tuba (a dark brassy voice), a xylophone, an accordion (two detuned reeds) and an anvil.
No voices anywhere: the death is a wheezing bellows gasp, a slide whistle falling, a thud and the helmet
rolling off.
Usage: python3 tools/audio/deepbreath_sfx.py [out_dir]   (default: godot/games/deepbreath/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/deepbreath/audio/sfx", seed=1983)
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


def save_loop(name, x, gain):
    x = x - np.mean(x)
    s.save(name, x, gain, fade=False)


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


def plank(f, sec=0.12, dec=0.025):
    """A hollow timber knock: a soft click through a plank's low, woody modes."""
    ex = np.r_[lp(s.noise(0.004), 3000) * env(n(0.004), 0.0003, 0.0015, 3), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 2.62, dec * 0.5, 0.45), (f * 4.3, dec * 0.3, 0.2)))


def knock(f, sec=0.08, dec=0.012):
    """A small stone knock: a short noise click through two low, quickly damped modes."""
    ex = np.r_[lp(s.noise(0.003), 4000) * env(n(0.003), 0.0002, 0.001, 3), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 2.3, dec * 0.6, 0.5), (f * 3.9, dec * 0.4, 0.25)))


def clank(f, sec=0.4, dec=0.08):
    """A metal clank: an impulse through inharmonic modes that ring a while."""
    ex = np.r_[1.0, 0.5 * hp(s.noise(0.002), 2000), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 1.59, dec * 0.8, 0.7), (f * 2.41, dec * 0.6, 0.5), (f * 3.7, dec * 0.4, 0.3)))


def anvil(f=1150, sec=0.9, dec=0.25):
    """An anvil struck by a hammer: a hard metal clang with long, bright inharmonic rings."""
    ex = np.r_[1.0, 0.6 * hp(s.noise(0.003), 3000), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * 2.08, dec * 0.7, 0.6), (f * 2.92, dec * 0.6, 0.45), (f * 4.17, dec * 0.4, 0.3)))


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong): pizzicato with a low damp."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1])
    return y * env(N, 0.001, sec, 0.5)


def glock(f, sec=0.8, decay=0.35):
    """A glockenspiel bar: a bright fundamental with the high inharmonic partials of a struck bar."""
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def crystal(f, sec=1.0, decay=0.5):
    """A glassy crystal chime: a pure fundamental, high inharmonic glass partials and a soft shimmer beat."""
    tt = t(sec)
    x = s.bell(f, sec, partials=((1, 1.0), (2.32, 0.35), (4.25, 0.18), (6.8, 0.08)), decay=decay)
    return x * (1 + 0.15 * np.sin(2 * np.pi * 6 * tt))


def xylo(f, sec=0.35, decay=0.09):
    """A xylophone bar: a short dry fundamental, the tuned twelfth, a hard mallet click."""
    x = s.bell(f, sec, partials=((1, 1.0), (3.0, 0.3), (6.1, 0.06)), decay=decay)
    return x + np.r_[0.12 * hp(s.noise(0.004), 2000), np.zeros(len(x) - n(0.004))]


def brass(f, sec, attack=0.025, decay=0.5, curve_=1.2, bright=1.0):
    """A round brassy voice: a saw-like stack whose brightness opens with the attack, a touch of vibrato."""
    tt = t(sec)
    fv = np.broadcast_to(np.asarray(f, dtype=float), tt.shape) * (1 + 0.004 * np.clip(tt / 0.3, 0, 1) * np.sin(2 * np.pi * 5.5 * tt))
    x = osc(fv, sec, [(k, 1 / k) for k in range(1, 12)])
    fm = float(np.max(fv))
    cut = fm * (1.5 + 4 * bright * np.clip(tt / (attack * 3), 0, 1) * np.exp(-tt / 0.6)) + 200
    return lp(x, np.minimum(cut, 9000)) * env(n(sec), attack, decay, curve_)


def tuba(f, sec, decay=0.4):
    """The tuba: the brassy voice, dark and round, with a little breathy puff on the attack."""
    x = brass(f, sec, 0.03, decay, 1.3, 0.45)
    return x + 0.08 * lp(s.noise(sec), 600) * env(n(sec), 0.005, 0.04, 3)


def accordion(f, sec, attack=0.03):
    """An accordion: two reeds a few cents apart (the musette beat), bright odd-and-even harmonics."""
    harm = [(k, (1 / k) * (1.0 if k % 2 else 0.7)) for k in range(1, 10)]
    x = osc(f, sec, harm) + osc(f * 1.004, sec, harm)
    return lp(x, 4500) * curve([(0, 0), (attack, 1), (sec - 0.04, 0.85), (sec, 0)], sec)


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


# G minor / G major notes (MIDI), used by the jingles
G2, D3, G3, Bb3, B3, D4, Eb4, F4, Fs4, G4, A4, Bb4, B4, C5, D5, Eb5, F5, Fs5, G5, A5, Bb5, B5, D6, G6, B6, D7, G7 = (
    m2f(m) for m in (43, 50, 55, 58, 59, 62, 63, 65, 66, 67, 69, 70, 71, 72, 74, 75, 77, 78, 79, 81, 82, 83, 86, 91, 95, 98, 103))

# --- the miner ---
for k, (f, g) in enumerate(((210, 1.0), (182, 0.9))):  # step_0, step_1: hobnailed boots on timber planks
    x = np.zeros(n(0.16))
    mix(x, 0, 0.5 * thump(f * 0.6, 60, 0.07, 0.02), 0.6 * plank(f, 0.12, 0.022))
    mix(x, n(0.002), 0.12 * knock(f * 9, 0.03, 0.003))  # the nails' tick
    save(f"step_{k}", lp(x, 4000) * g, 0.22 * g)

d = 0.25  # jump: a quick cloth whoosh and a springy rising blip, a creak of the plank he leaves
x = np.zeros(n(d))
mix(x, 0, 0.35 * lp(hp(s.noise(0.15), 500), np.geomspace(1200, 4000, n(0.15))) * env(n(0.15), 0.01, 0.05, 3))
mix(x, 0, 0.3 * osc(curve([(0, 300), (0.1, 620)], 0.1), 0.1, ((1, 1.0), (2, 0.25))) * env(n(0.1), 0.003, 0.04, 3))
mix(x, 0, 0.25 * plank(240, 0.1, 0.02))
save("jump", x, 0.3)

d = 0.3  # land: boots on the boards: a padded thud, a hollow plank knock and a little dust
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(130, 55, 0.12, 0.03), 0.6 * plank(165, 0.2, 0.035))
mix(x, n(0.01), 0.15 * lp(hp(s.noise(0.1), 1200), 5000) * env(n(0.1), 0.003, 0.03, 3))
save("land", lp(x, 4500), 0.38)

# --- keys and the lift ---
d = 1.3  # key: a crystal chime: two glassy notes a fourth apart (D, G) and a faint sparkle
x = np.zeros(n(d))
mix(x, 0, 0.35 * crystal(D6, 1.0, 0.7))
mix(x, n(0.06), 0.4 * crystal(G6, 1.2, 0.8))
mix(x, n(0.06), 0.05 * hp(s.noise(0.35), 7000) * env(n(0.35), 0.002, 0.1, 3))
save("key", x, 0.42)

d = 1.9  # key_last: the last key: brighter: a crystal run up the G major chord, a high bell and more sparkle
x = np.zeros(n(d))
for i, f in enumerate((D6, G6, B6, D7)):
    mix(x, n(i * 0.055), 0.3 * crystal(f, 1.2, 0.7), 0.12 * glock(f / 2, 0.6, 0.3))
mix(x, n(0.22), 0.25 * crystal(G7, 1.6, 0.9))
mix(x, n(0.05), 0.08 * hp(s.noise(0.9), 6500) * curve([(0, 0), (0.1, 1), (0.9, 0)], 0.9))
save("key_last", x, 0.5)

d = 1.6  # portal_open: the lift gate rattles open: a latch clack, a scissor gate folding (a run of metal
x = np.zeros(n(d))  # rattles and a sliding scrape), then the lift bell rings twice
mix(x, 0, 0.6 * clank(1400, 0.15, 0.02), 0.4 * thump(200, 90, 0.06, 0.02))
for k in range(16):
    st = 0.08 + k * 0.035 + s.rng.uniform(-0.006, 0.006)
    mix(x, n(st), s.rng.uniform(0.15, 0.35) * clank(s.rng.uniform(1700, 3200), 0.1, 0.015))
mix(x, n(0.08), 0.15 * lp(hp(s.noise(0.6), 1500), 6000) * curve([(0, 0), (0.1, 1), (0.5, 0.8), (0.6, 0)], 0.6))
mix(x, n(0.7), 0.5 * clank(900, 0.2, 0.03))  # the gate hits its stop
for k in range(2):
    mix(x, n(0.8 + 0.28 * k), 0.4 * s.bell(1320, 0.8, ((1, 1.0), (2.0, 0.3), (2.76, 0.4), (5.4, 0.12)), 0.5))
save("portal_open", x, 0.5)

d = 1.5  # portal_enter: the lift drops away: a gate clack, a whoosh falling in pitch and a cable rumble
x = np.zeros(n(d))
mix(x, 0, 0.4 * clank(1600, 0.1, 0.015))
wh = lp(hp(s.noise(1.3), 200), curve([(0, 3500), (1.3, 300)], 1.3))
mix(x, n(0.05), 0.7 * wh * curve([(0, 0), (0.25, 1), (0.9, 0.5), (1.3, 0)], 1.3))
mix(x, n(0.05), 0.25 * osc(curve([(0, 520), (1.2, 140)], 1.2), 1.2, ((1, 1.0), (2, 0.2))) *
    curve([(0, 0), (0.2, 1), (1.2, 0)], 1.2))
mix(x, n(0.05), 0.35 * lp(s.noise(1.3), 120) * curve([(0, 0), (0.3, 1), (1.3, 0)], 1.3))
save("portal_enter", x, 0.5)

d = 0.6  # crumble: a floor tile giving way: sand sifting and small stones and splinters falling, all laid
N = n(d)  # round the loop (it may be repeated while he stands on it)
ph = np.arange(N) / N
x = 0.35 * band_noise(N, 1500, 7000, 0.8) * (0.7 + 0.3 * np.sin(2 * np.pi * 5 * ph))
x += 0.3 * band_noise(N, 150, 700, 1.0)
for k in range(22):
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.2, 0.7) * knock(s.rng.uniform(450, 1300), 0.05, 0.007))
for k in range(4):
    circ_mix(x, int(s.rng.uniform(0, N)), 0.5 * plank(s.rng.uniform(280, 420), 0.06, 0.01))
save_loop("crumble", x, 0.35)

d = 1.0  # conveyor: a rattling belt: rollers clacking eight times a second, a chain rattle, a motor hum with
N = n(d)  # a whole number of cycles, all circular
ph = np.arange(N) / N
x = 0.25 * band_noise(N, 300, 2500, 1.0) * (0.6 + 0.4 * np.sin(2 * np.pi * 8 * ph) ** 2)
x += 0.2 * (np.sin(2 * np.pi * 100 * ph) + 0.4 * np.sin(2 * np.pi * 200 * ph) + 0.2 * np.sin(2 * np.pi * 300 * ph))
for k in range(8):
    circ_mix(x, int(k * N / 8), 0.7 * clank(780 + 60 * (k % 2), 0.08, 0.012))
    circ_mix(x, int((k + 0.5) * N / 8), 0.3 * knock(1500, 0.04, 0.005))
for k in range(30):
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.05, 0.15) * clank(s.rng.uniform(2200, 3800), 0.03, 0.004))
save_loop("conveyor", lp(x, 7000), 0.3)

# --- air ---
d = 1.0  # air_low: a warning: two pinched gauge beeps, a pause, a lower one, as a loop
N = n(d)
x = np.zeros(N)
for st, f in ((0.0, 1480), (0.16, 1480), (0.48, 1110)):
    ln = 0.1
    b = osc(f, ln, ((1, 1.0), (3, 0.3), (5, 0.12))) * curve([(0, 0), (0.005, 1), (0.09, 0.8), (0.1, 0)], ln)
    mix(x, n(st), b)
save_loop("air_low", x, 0.22)

d = 0.07  # air_tick: counting the air bonus: a short bright blip with a xylophone tick
x = np.zeros(n(d))
mix(x, 0, 0.5 * osc(1760, d, ((1, 1.0), (2, 0.2))) * env(n(d), 0.001, 0.02, 3), 0.3 * xylo(G6, d, 0.02))
s.save("air_tick", x, 0.2)

d = 1.0  # steam: a burst of steam from a pipe: a sharp valve knock, a hiss swelling and fading
x = np.zeros(n(d))
mix(x, 0, 0.4 * clank(1100, 0.08, 0.01))
hs = lp(hp(s.noise(0.95), 2500), 10000) + 0.3 * lp(hp(s.noise(0.95), 600), 2000)
mix(x, n(0.02), hs * curve([(0, 0), (0.04, 1), (0.35, 0.75), (0.95, 0)], 0.95))
save("steam", x, 0.35)

# --- guardians (loops) ---
d = 1.0  # guardian_cart: a mine cart rolling: wheels knocking over rail joints (a pair twice a round),
N = n(d)  # a low rumble, a squeak of the axle
ph = np.arange(N) / N
x = 0.4 * band_noise(N, 40, 300, 1.2) * (0.7 + 0.3 * np.sin(2 * np.pi * 4 * ph))
x += 0.2 * band_noise(N, 800, 3000, 1.0) * (0.5 + 0.5 * np.sin(2 * np.pi * 2 * ph) ** 2)
for k in range(2):
    for j, dt in enumerate((0.0, 0.11)):
        circ_mix(x, int((k * 0.5 + dt) * N), 0.8 * clank(420 + 40 * j, 0.15, 0.03))
        circ_mix(x, int((k * 0.5 + dt) * N), 0.6 * thump(140, 70, 0.08, 0.02))
sq = osc(1900 + 150 * np.sin(2 * np.pi * 1 * ph), d) * (0.5 + 0.5 * np.cos(2 * np.pi * 2 * ph)) ** 6
x += 0.08 * sq
save_loop("guardian_cart", x, 0.4)

d = 0.5  # guardian_drill: a clockwork drill: a gear whine with a whole number of cycles, a grinding chatter
N = n(d)
ph = np.arange(N) / N
cyc = 400  # 800 Hz over half a second
w = sum(np.sin(2 * np.pi * cyc * k * ph) / k for k in range(1, 8))
x = 0.25 * w * (0.7 + 0.3 * np.sin(2 * np.pi * 15 * ph))
x += 0.5 * band_noise(N, 1500, 6000, 0.8) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 15 * ph)))
for k in range(30):
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.1, 0.3) * knock(s.rng.uniform(900, 1600), 0.03, 0.004))
save_loop("guardian_drill", lp(x, 8000), 0.28)

d = 0.8  # guardian_bat: a cave bat: leathery wing flaps (ten a loop) and two little squeaks
N = n(d)
x = 0.03 * band_noise(N, 300, 1500)
for k in range(10):
    circ_mix(x, int(k * N / 10), (0.45 + 0.15 * (k % 2)) * lp(hp(s.noise(0.045), 300), 1700) * env(n(0.045), 0.005, 0.016, 3))
for st, f in ((0.18, 4300), (0.55, 3800)):
    circ_mix(x, n(st), 0.2 * osc(curve([(0, f), (0.03, f * 1.2), (0.06, f * 0.95)], 0.06), 0.06) * env(n(0.06), 0.004, 0.02, 3))
save_loop("guardian_bat", x, 0.3)

# --- death and jingles ---
d = 1.8  # die: no voice: a wheezing bellows gasp (a breathy reed choking up), a slide whistle falling, a
x = np.zeros(n(d))  # thud on the boards and the helmet clattering round and round
gl = 0.3
gasp = lp(hp(s.noise(gl), 700), curve([(0, 1200), (gl, 3500)], gl)) * curve([(0, 0), (0.2, 1), (0.3, 0)], gl)
mix(x, 0, 0.35 * gasp, 0.12 * accordion(curve([(0, 520), (gl, 700)], gl), gl, 0.1))
ln = 0.7
fs = curve([(0, 1400), (0.06, 1500), (0.7, 300)], ln) * (1 + 0.03 * np.sin(2 * np.pi * 8 * t(ln)))
mix(x, n(0.32), 0.35 * osc(fs, ln, ((1, 1.0), (2, 0.08))) * curve([(0, 0), (0.03, 1), (0.6, 0.8), (0.7, 0)], ln))
mix(x, n(1.02), 1.0 * thump(130, 45, 0.3, 0.08), 0.6 * plank(150, 0.25, 0.04))
for k in range(6):  # the helmet wobbling to rest, the bounces closer and quieter
    mix(x, n(1.08 + sum(0.12 * 0.72 ** j for j in range(k))), (0.4 * 0.75 ** k) * clank(1250 + 40 * k, 0.1, 0.02))
save("die", x, 0.55)

d = 2.1  # level_start: a jaunty call: tuba oom-pahs under a pizzicato and xylophone pickup G-Bb-D, the
x = np.zeros(n(d))  # accordion holds the G minor chord, an anvil clang
beat = 0.21
for k, f in enumerate((G2, D3, G2, D3)):
    mix(x, n(k * beat * 2), 0.5 * tuba(f, 0.3, 0.2))
    for p in (Bb3, D4, G4):
        mix(x, n(k * beat * 2 + beat), 0.08 * pluck(p, 0.25, 0.6, 0.99))
for k, f in enumerate((D5, G5, Bb5, A5, G5, D5, Fs5)):
    mix(x, n(k * beat), 0.3 * xylo(f, 0.3, 0.08))
mix(x, n(8 * beat), 0.5 * tuba(G2, 0.5, 0.35), 0.35 * xylo(G5, 0.5, 0.15), 0.3 * anvil(1150, 0.5, 0.15))
for f in (G3, Bb3, D4, G4):
    mix(x, n(8 * beat), 0.1 * accordion(f, 0.4))
save("level_start", x, 0.6)

d = 2.6  # level_clear: the lift arrives: a xylophone run up G major, accordion and tuba bouncing a cadence
x = np.zeros(n(d))  # (C, D7, G) and a big G chord with an anvil ring and the lift bell
for i, f in enumerate((G4, B4, D5, G5, B5, D6)):
    mix(x, n(i * 0.05), 0.25 * xylo(f, 0.3, 0.08))
cad = ((0.35, m2f(48), (m2f(64), m2f(67), m2f(72))), (0.65, m2f(50), (m2f(66), m2f(69), m2f(72))),
       (0.95, m2f(50), (m2f(66), m2f(69), m2f(74))))
for st, root, ch in cad:
    mix(x, n(st), 0.45 * tuba(root / 2, 0.28, 0.2))
    for p in ch:
        mix(x, n(st + 0.15), 0.08 * accordion(p, 0.13))
mix(x, n(1.3), 0.55 * tuba(G2, 1.0, 0.7), 0.35 * anvil(1150, 1.0, 0.3))
for f in (G3, B3, D4, G4, B4):
    mix(x, n(1.3), 0.07 * accordion(f, 1.1, 0.02), 0.08 * pluck(f, 1.0, 0.6, 0.996))
for i, f in enumerate((D6, G6, B6)):
    mix(x, n(1.3 + i * 0.05), 0.15 * xylo(f, 0.4, 0.12))
mix(x, n(1.5), 0.2 * s.bell(1320, 1.0, ((1, 1.0), (2.0, 0.3), (2.76, 0.4), (5.4, 0.12)), 0.6))
save("level_clear", x, 0.6)

d = 2.8  # game_over: the tuba slumps down (D, C, Bb, A) as the accordion bellows sag, a low G and a lonely
x = np.zeros(n(d))  # pizzicato
for st, f in ((0.0, D4), (0.32, C5 / 2), (0.64, Bb3), (0.98, A4 / 2)):
    mix(x, n(st), 0.45 * tuba(f / 2, 0.3 if st < 0.9 else 0.5, 0.25), 0.12 * accordion(f, 0.28 if st < 0.9 else 0.45))
mix(x, n(1.55), 0.55 * tuba(G2, 1.2, 0.8))
for f in (G3, Bb3, D4):
    mix(x, n(1.55), 0.08 * accordion(f * curve([(0, 1), (1.1, 0.97)], 1.1), 1.1, 0.05))
mix(x, n(2.25), 0.12 * pluck(G4, 0.5, 0.4, 0.99))
save("game_over", lp(x, 7000), 0.55)

d = 1.3  # extra_life: a cheery xylophone and crystal run up G major with an accordion squeeze and a bell
x = np.zeros(n(d))
for i, f in enumerate((G5, B5, D6, G6, B6, D7)):
    mix(x, n(i * 0.06), 0.25 * xylo(f, 0.3, 0.08), 0.12 * crystal(f, 0.6, 0.25))
for f in (G4, B4, D5):
    mix(x, n(0.36), 0.08 * accordion(f, 0.5, 0.02))
mix(x, n(0.36), 0.22 * crystal(G7, 0.9, 0.4))
save("extra_life", x, 0.5)
