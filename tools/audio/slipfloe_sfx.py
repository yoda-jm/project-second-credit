#!/usr/bin/env python3
"""Sound effects for game 17 (Slipfloe), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game. Ice is modelled as struck resonant modes
(a few damped, slightly inharmonic sine modes rung by a click or a noise burst): a block stopping is a low
woody clunk, a block shattering is a crack followed by dozens of tiny glassy shards (short high inharmonic
bells scattered in time), sliding is circular band-passed noise with faint glassy resonances. The mites are
cute: a squish is a wet down-glide with a wobble and a squeak, then a glockenspiel chime (rising for a
double or triple crush). The wall shake is a low spring "boing" over a rumble; dizzy stars are high bells
circling with a wobbly tweet; the otter's fall is a slide whistle. The jingles are in G major like the music:
pizzicato-like plucks (Karplus-Strong), glockenspiel and celesta-like bells, sleigh-bell shakes and a soft
brassy voice for the gem fanfare. The loops (slide, chew) are built on circular noise, whole-cycle swells and
events wrapped round the end, so the last sample meets the first with no seam.
Usage: python3 tools/audio/slipfloe_sfx.py [out_dir]   (default: godot/games/slipfloe/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/slipfloe/audio/sfx", seed=1982)
t, env, lp, hp = s.t, s.env, s.lowpass, s.highpass


def n(sec):
    return int(SR * sec)


def mix(x, start, *bs):
    """Adds sounds (of any lengths) into x from `start`."""
    for b in bs:
        mix1(x, start, b)


def mix1(x, start, b):
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
    """A tone with a (scalar or curve) frequency and the given harmonics."""
    fv = np.broadcast_to(np.asarray(f, dtype=float), (n(sec),))
    ph = 2 * np.pi * np.cumsum(fv) / SR
    return sum(a * np.sin(k * ph) for k, a in harm)


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong): pizzicato-ish when damped."""
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


def celesta(f, sec=0.9, decay=0.5):
    """A celesta-ish tone: sweeter than the glockenspiel, an octave partial and a soft hammer tick."""
    x = s.bell(f, sec, partials=((1, 1.0), (2.0, 0.25), (4.1, 0.05)), decay=decay)
    return x + np.r_[0.12 * hp(s.noise(0.004), 4000), np.zeros(len(x) - n(0.004))]


def brass(f, sec, attack=0.025, decay=0.5, curve_=1.2, bright=1.0):
    """A soft brassy voice: a saw-like stack whose brightness opens with the attack, a touch of vibrato."""
    tt = t(sec)
    fv = np.broadcast_to(np.asarray(f, dtype=float), tt.shape) * (1 + 0.004 * np.clip(tt / 0.3, 0, 1) * np.sin(2 * np.pi * 5.5 * tt))
    x = osc(fv, sec, [(k, 1 / k) for k in range(1, 12)])
    fm = float(np.max(fv))
    cut = fm * (1.5 + 4 * bright * np.clip(tt / (attack * 3), 0, 1) * np.exp(-tt / 0.6)) + 400
    return lp(x, np.minimum(cut, 9000)) * env(n(sec), attack, decay, curve_)


def thump(f0, f1, sec, decay):
    return s.sweep(f0, f1, sec) * env(n(sec), 0.001, decay, 3)


def resonate(x, modes):
    """Rings an excitation through damped resonant modes (freq, decay seconds, amplitude)."""
    y = np.zeros(len(x))
    for f, dec, a in modes:
        ir_t = t(min(dec * 5, 0.8))
        ir = np.sin(2 * np.pi * f * ir_t) * np.exp(-ir_t / dec)
        y += a * np.convolve(x, ir)[:len(x)]
    return y


def shard(f, sec=0.25):
    """One tiny glassy shard: a short inharmonic ping."""
    return s.bell(f, sec, partials=((1, 1.0), (2.32, 0.5), (4.25, 0.3), (6.8, 0.15)), decay=sec * 0.6)


def sleigh(sec, rate=14, amp=1.0):
    """A sleigh-bell shake: many small high jingles in quick bursts."""
    x = np.zeros(n(sec) + n(0.2))
    k = 0
    while k / rate < sec:
        for _ in range(3):
            mix(x, n(k / rate + s.rng.uniform(0, 0.02)), s.rng.uniform(0.3, 1) * shard(s.rng.uniform(4200, 7800), 0.12))
        k += 1
    x += 0.2 * hp(s.rng.uniform(-1, 1, len(x)), 6000) * np.r_[np.ones(n(sec)), np.linspace(1, 0, len(x) - n(sec))]
    return amp * x


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def circ_mix(x, start, b):
    """Mixes b into x wrapping round the end: for sounds placed in a loop."""
    idx = (start + np.arange(len(b))) % len(x)
    np.add.at(x, idx, b)


ICE_MODES = ((410, 0.05, 1.0), (1130, 0.03, 0.55), (2370, 0.018, 0.3), (3980, 0.01, 0.15))  # a block of ice

# G major notes, used by the jingles
G3, B3, D4, E4, Fs4, G4, A4, B4, C5, D5, E5, Fs5, G5, A5, B5, C6, D6, E6, G6, B6, D7 = (
    196.0, 246.9, 293.7, 329.6, 370.0, 392.0, 440.0, 493.9, 523.3, 587.3, 659.3, 740.0, 784.0, 880.0, 987.8,
    1046.5, 1174.7, 1318.5, 1568.0, 1975.5, 2349.3)

# --- the ice ---
d = 0.25  # push: the otter shoves a block: a padded thump, a scuff of snow, the block's body ringing faintly
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(150, 70, 0.12, 0.03))
mix(x, 0, 0.35 * lp(hp(s.noise(0.08), 400), 2500) * env(n(0.08), 0.004, 0.025, 3))
mix(x, n(0.005), 0.35 * resonate(np.r_[1.0, np.zeros(n(0.2))], ((330, 0.03, 1.0), (910, 0.015, 0.4))))
save("push", x, 0.45)

d = 0.5  # slide loop: exactly 0.5 s: an icy hiss and scrape in whole-cycle swells (2 and 4 per loop),
N = n(d)  # a low rumble of the block on the floor, faint glassy resonances ringing in the hiss
tt = np.arange(N) / SR
x = 0.35 * band_noise(N, 1800, 7000) * (0.75 + 0.25 * np.sin(2 * np.pi * 4 * tt / d))
x += 0.45 * band_noise(N, 60, 380, 1.3) * (0.85 + 0.15 * np.sin(2 * np.pi * 2 * tt / d + 1))
for f0 in (2210, 3470, 5120):  # narrow bands: the "singing" of ice rubbing ice
    x += 0.12 * band_noise(N, f0 * 0.985, f0 * 1.015) * (0.6 + 0.4 * np.sin(2 * np.pi * 2 * tt / d + f0))
for k in range(6):  # little skips of grit
    circ_mix(x, int(k * N / 6 + s.rng.uniform(0, N / 12)), 0.12 * hp(s.noise(0.006), 2500) * env(n(0.006), 0.0003, 0.002, 3))
x -= np.mean(x)
s.save("slide", x, 0.3, fade=False)

d = 0.5  # block stop: a solid ice clunk against a wall: a hard click, the block's modes, a low thud
x = np.zeros(n(d))
mix(x, 0, 0.8 * hp(s.noise(0.008), 1500) * env(n(0.008), 0.0002, 0.002, 3))
mix(x, 0, 1.1 * resonate(np.r_[1.0, np.zeros(n(0.4))], ICE_MODES))
mix(x, 0, 0.9 * thump(130, 55, 0.25, 0.06))
mix(x, n(0.01), 0.15 * lp(s.noise(0.15), 900) * env(n(0.15), 0.002, 0.05, 3))
save("block_stop", x, 0.55)

d = 1.3  # shatter: a sharp crack, a crunchy burst, then bright shards tinkling down and thinning out
x = np.zeros(n(d))
mix(x, 0, 1.0 * hp(s.noise(0.012), 2000) * env(n(0.012), 0.0002, 0.003, 3))
mix(x, 0, 0.9 * resonate(np.r_[1.0, np.zeros(n(0.3))], ((520, 0.02, 1.0), (1450, 0.015, 0.6), (3100, 0.01, 0.4))))
crunch = hp(s.noise(0.25), 900) * (np.abs(s.rng.standard_normal(n(0.25))) > 1.6) * env(n(0.25), 0.001, 0.06, 3)
mix(x, 0, 0.6 * lp(crunch, 9000))
mix(x, 0, 0.5 * lp(hp(s.noise(0.3), 1500), 8000) * env(n(0.3), 0.001, 0.08, 3))
mix(x, 0, 0.5 * thump(180, 70, 0.15, 0.03))
for k in range(34):  # shards: early ones dense and loud, later sparse and quiet, pitched high
    st = 0.02 + 0.9 * (k / 34) ** 1.7 + s.rng.uniform(0, 0.03)
    mix(x, n(st), (0.5 - 0.012 * k) * shard(s.rng.uniform(2400, 7200), s.rng.uniform(0.1, 0.3)))
save("shatter", x, 0.55)


def crush(chime):
    """A mite squashed by a block: a wet squish that glides down with a wobble, a tiny squeak, then a chime."""
    d = 1.0
    x = np.zeros(n(d))
    mix(x, 0, 0.6 * lp(s.noise(0.14), np.geomspace(4000, 300, n(0.14))) * env(n(0.14), 0.001, 0.04, 3))
    sq = s.sweep(620, 170, 0.18) * env(n(0.18), 0.003, 0.07, 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 36 * t(0.18)))
    mix(x, 0, 0.55 * sq)
    mix(x, 0, 0.5 * thump(200, 70, 0.12, 0.03))
    mix(x, n(0.03), 0.25 * osc(curve([(0, 1900), (0.03, 2600), (0.08, 1700)], 0.08), 0.08) * env(n(0.08), 0.003, 0.03, 3))
    for i, f in enumerate(chime):
        mix(x, n(0.14 + i * 0.06), 0.3 * glock(f, 0.7, 0.3) + 0.12 * celesta(f / 2, 0.7, 0.35))
    return x


save("crush", crush((G5, D6)), 0.5)
save("crush_2", crush((B5, D6, G6)), 0.52)
save("crush_3", crush((D6, G6, B6, D7)), 0.55)

d = 0.6  # egg break: an egg inside the ice cracked: small shell clicks, a hollow pop, a few glassy crumbs
x = np.zeros(n(d))
for k in range(4):
    mix(x, n(k * 0.018 + s.rng.uniform(0, 0.006)),
        (0.5 + 0.15 * k) * resonate(np.r_[1.0, np.zeros(n(0.05))], ((2600 + 300 * k, 0.006, 1.0), (4800, 0.003, 0.4))))
mix(x, n(0.08), 0.6 * osc(curve([(0, 700), (0.06, 260)], 0.06), 0.06) * env(n(0.06), 0.001, 0.02, 3))
mix(x, n(0.08), 0.3 * lp(s.noise(0.08), 2000) * env(n(0.08), 0.001, 0.02, 3))
for k in range(6):
    mix(x, n(0.1 + k * 0.04 + s.rng.uniform(0, 0.02)), (0.2 - 0.025 * k) * shard(s.rng.uniform(3000, 6000), 0.12))
save("egg_break", x, 0.45)

d = 0.4  # hatch: a mite pops out: a round rising "pop" and a tiny chirpy squeak
x = np.zeros(n(d))
mix(x, 0, 0.8 * osc(curve([(0, 260), (0.05, 700)], 0.06), 0.06, ((1, 1.0), (2, 0.2))) * env(n(0.06), 0.001, 0.02, 3))
mix(x, 0, 0.2 * hp(s.noise(0.01), 2000) * env(n(0.01), 0.0003, 0.003, 3))
chirp = osc(curve([(0, 1500), (0.05, 2300), (0.1, 2000), (0.14, 2700)], 0.14), 0.14, ((1, 1.0), (2, 0.15)))
mix(x, n(0.07), 0.3 * chirp * curve([(0, 0), (0.01, 1), (0.1, 0.8), (0.14, 0)], 0.14))
save("hatch", x, 0.4)

d = 1.3  # wall shake: the arena wall wobbles: a deep spring "boing" with a slow wobble, over a low rumble
x = np.zeros(n(d))
tt = t(d)
wob = 1 + 0.18 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt / 0.35)
f = curve([(0, 55), (0.04, 95), (1.3, 82)], d) * wob
mix(x, 0, osc(f, d, ((1, 1.0), (2, 0.35), (3, 0.12))) * env(n(d), 0.004, 0.4, 3))
rum = lp(s.noise(d), 260) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * tt)) * env(n(d), 0.01, 0.35, 3)
mix(x, 0, 0.9 * rum)
mix(x, 0, 0.5 * resonate(np.r_[1.0, np.zeros(n(0.6))], ((180, 0.08, 1.0), (470, 0.05, 0.4))))
mix(x, 0, 0.25 * lp(hp(s.noise(0.05), 300), 2500) * env(n(0.05), 0.001, 0.015, 3))
save("wall_shake", lp(x, 3000), 0.6)

d = 1.4  # stun: dizzy stars circling: high bells in a spinning pattern that pans in pitch, a wobbly "tweet"
x = np.zeros(n(d))
pat = (B6, D7, G6, D7, B6, E6 * 2, G6, D7)
for k in range(10):
    f = pat[k % len(pat)] * (1 + 0.01 * np.sin(k))
    mix(x, n(k * 0.1), (0.32 - 0.02 * k) * glock(f, 0.35, 0.12))
tw = osc(2400 * (1 + 0.08 * np.sin(2 * np.pi * 7 * t(1.0))), 1.0) * curve([(0, 0), (0.1, 1), (0.8, 0.6), (1.0, 0)], 1.0)
mix(x, n(0.05), 0.08 * tw)
save("stun", x, 0.4)

d = 0.45  # stomp: walking over a stunned mite: a soft padded bounce, a squeak, a coin-like ping
x = np.zeros(n(d))
mix(x, 0, 0.7 * osc(curve([(0, 180), (0.03, 320), (0.12, 260)], 0.12), 0.12) * env(n(0.12), 0.002, 0.04, 3))
mix(x, 0, 0.3 * thump(140, 60, 0.08, 0.02))
mix(x, n(0.02), 0.25 * osc(curve([(0, 2200), (0.06, 1500)], 0.06), 0.06) * env(n(0.06), 0.002, 0.02, 3))
mix(x, n(0.07), 0.3 * glock(E6, 0.35, 0.15) + 0.25 * glock(B6, 0.35, 0.15))
save("stomp", x, 0.42)

d = 2.8  # gem line: a triumphant sparkly fanfare: a brassy call (G C D G) over plucked chords, a glittering
x = np.zeros(n(d))  # run up two octaves, a held G major chord with sleigh bells and falling sparkles
call = ((0.0, D5, 0.13), (0.15, G5, 0.13), (0.30, B5, 0.13), (0.45, D6, 0.3), (0.8, B5, 0.13), (0.95, D6, 1.5))
for st, f, ln in call:
    mix(x, n(st), 0.3 * brass(f / 2, ln + 0.05, 0.012, ln * 0.8 + 0.1, 1.2))
    mix(x, n(st), 0.12 * glock(f * 2, 0.4, 0.15))
for f in (G3, D4, G4, B4, D5):
    mix(x, n(0.95), 0.1 * brass(f, 1.5, 0.05, 1.1, 1.3, 0.6))
for i, f in enumerate((G3, B3, D4, G4, B4, D5)):
    mix(x, n(0.95 + i * 0.025), 0.2 * pluck(f, 1.4, 0.75, 0.997))
for i, f in enumerate((G5, A5, B5, D6, E6, G6, A5 * 2, B6, D7)):
    mix(x, n(0.95 + i * 0.035), 0.12 * glock(f, 0.5, 0.2))
mix(x, n(0.9), 0.35 * sleigh(0.8, 16))
for st in (0.0, 0.45, 0.95):
    mix(x, n(st), 0.5 * thump(110, 45, 0.3, 0.08))
mix(x, n(0.95), 0.1 * hp(s.noise(1.4), 6000) * env(n(1.4), 0.002, 0.5, 2.5))
for k in range(9):
    mix(x, n(1.3 + k * 0.13), (0.1 - 0.007 * k) * shard(s.rng.choice((G6, B6, D7, 3136.0)), 0.3))
save("gem_line", x, 0.6)

d = 0.4  # chew loop: exactly 0.4 s: a mite nibbling ice: four crunchy bites (clicky gated noise and a tiny
N = n(d)  # ice ping) at uneven spacing, all wrapped round the end
x = np.zeros(N)
for k, st in enumerate((0.0, 0.09, 0.21, 0.3)):
    ln = 0.05
    bite = hp(s.noise(ln), 1200) * (np.abs(s.rng.standard_normal(n(ln))) > 1.2) * env(n(ln), 0.001, 0.015, 3)
    circ_mix(x, n(st), (0.8 if k % 2 == 0 else 0.6) * lp(bite, 7000))
    circ_mix(x, n(st), 0.25 * resonate(np.r_[1.0, np.zeros(n(0.05))], ((1800 + 250 * k, 0.008, 1.0), (3900, 0.004, 0.4))))
x -= np.mean(x)
s.save("chew", x, 0.4, fade=False)

d = 1.8  # die: the otter caught: a sad slide whistle falling with vibrato, a soft bonk, two drooping plucks
x = np.zeros(n(d))
mix(x, 0, 0.5 * thump(300, 120, 0.1, 0.03) + 0.3 * glock(E5, 0.1, 0.05))
ln = 1.2
f = curve([(0, 1300), (0.15, 1350), (1.2, 330)], ln) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t(ln)))
wh = osc(f, ln, ((1, 1.0), (2, 0.08))) + 0.08 * lp(hp(s.noise(ln), 1000), 5000)
mix(x, n(0.12), 0.45 * wh * curve([(0, 0), (0.04, 1), (0.9, 0.8), (1.2, 0)], ln))
for i, fp in enumerate((B3, G3 * 0.944)):  # B3 then F#3: a little sigh
    mix(x, n(1.3 + i * 0.2), 0.3 * pluck(fp, 0.6, 0.4, 0.995))
save("die", x, 0.45)

d = 2.1  # ready: a bright start jingle: plucked bass bouncing (G D G D), a celesta and glockenspiel tune,
x = np.zeros(n(d))  # sleigh-bell shakes on the beats, a final G chord with a sparkle
beat = 60 / 150
tune = ((0, D5, 0.5), (0.5, G5, 0.5), (1, B5, 0.5), (1.5, A5, 0.5), (2, G5, 0.5), (2.5, B5, 0.5), (3, D6, 0.5),
        (3.5, E6, 0.25), (3.75, Fs5 * 2, 0.25), (4, G6, 1.2))
for b, f, lnb in tune:
    mix(x, n(b * beat), 0.3 * celesta(f, 0.7, 0.35), 0.1 * glock(f * 2, 0.4, 0.15))
for b, f in ((0, G3 / 2), (1, D4 / 2), (2, G3 / 2), (3, D4 / 2), (4, G3 / 2)):
    mix(x, n(b * beat), 0.45 * pluck(f, 0.5 if b < 4 else 1.2, 0.35, 0.995))
    if b < 4:
        for g in (B3, D4, G4):
            mix(x, n((b + 0.5) * beat), 0.08 * pluck(g, 0.25, 0.5, 0.99))
for b in range(5):
    mix(x, n(b * beat), 0.15 * sleigh(0.1, 30))
for f in (G4, B4, D5, G5):
    mix(x, n(4 * beat), 0.12 * pluck(f, 1.2, 0.7, 0.998))
mix(x, n(4 * beat), 0.25 * sleigh(0.5, 18))
save("ready", x, 0.55)

d = 2.8  # stage clear: a happy run: plucked arpeggio climbing, a brassy rising third, a bell chord and sleighs
x = np.zeros(n(d))
for i, f in enumerate((G4, B4, D5, G5, B5, D6, G6)):
    mix(x, n(i * 0.07), 0.3 * pluck(f, 0.5, 0.8, 0.994), 0.1 * glock(f * 2, 0.3, 0.12))
for st, f, lnb in ((0.55, B5, 0.2), (0.78, C6, 0.2), (1.0, D6, 1.4)):
    mix(x, n(st), 0.3 * brass(f / 2, lnb, 0.015, lnb * 0.7 + 0.1, 1.2))
    mix(x, n(st), 0.25 * celesta(f, 0.8, 0.4))
for f in (G3, D4, G4, B4):
    mix(x, n(1.0), 0.1 * brass(f, 1.4, 0.04, 1.0, 1.3, 0.5))
    mix(x, n(1.0), 0.18 * pluck(f, 1.6, 0.7, 0.998))
for f in (G6, B6, D7):
    mix(x, n(1.05), 0.12 * glock(f, 1.0, 0.45))
mix(x, n(1.0), 0.3 * sleigh(0.9, 16))
for st in (0.55, 1.0):
    mix(x, n(st), 0.4 * thump(110, 45, 0.3, 0.08))
save("stage_clear", x, 0.58)

d = 2.8  # game over: a gentle, comic-sad music-box line winding down (D C B A... G, slowing), a low hollow pluck,
x = np.zeros(n(d))  # a minor iv colour (C minor) that sighs back to G
for st, f in ((0.0, D6), (0.28, C6), (0.58, B5), (0.92, A5)):
    mix(x, n(st), 0.3 * celesta(f, 0.8, 0.4), 0.08 * glock(f, 0.5, 0.2))
for f in (C5 / 2, 311.1, G4):  # C minor over the last: C4 Eb4 G4
    mix(x, n(0.92), 0.14 * pluck(f, 1.0, 0.4, 0.996))
mix(x, n(1.35), 0.32 * celesta(G5, 1.3, 0.7))
for f in (G3 / 2, D4 / 2, G3, B3, D4):
    mix(x, n(1.35), 0.2 * pluck(f, 1.4, 0.35, 0.997))
f = curve([(0, 1100), (0.6, 700)], 0.6) * (1 + 0.02 * np.sin(2 * np.pi * 5 * t(0.6)))
mix(x, n(1.9), 0.1 * osc(f, 0.6) * curve([(0, 0), (0.05, 1), (0.6, 0)], 0.6))
save("game_over", lp(x, 8000), 0.45)

d = 1.3  # extra life: a celesta arpeggio climbing two octaves, sleigh bells and a bell chord at the top
x = np.zeros(n(d))
for i, f in enumerate((G4, B4, D5, G5, B5, D6)):
    mix(x, n(i * 0.07), 0.3 * pluck(f, 0.5, 0.8, 0.995), 0.15 * celesta(f * 2, 0.4, 0.2))
for f in (G5, B5, D6):
    mix(x, n(0.45), 0.2 * glock(f * 2, 0.8, 0.35))
mix(x, n(0.42), 0.25 * sleigh(0.4, 18))
save("extra_life", x, 0.5)

d = 0.1  # time bonus: one counting tick, a bright short woody-glassy blip (the game repeats it as it counts)
x = np.zeros(n(d))
mix(x, 0, 0.6 * osc(1760, 0.06, ((1, 1.0), (2.76, 0.2))) * env(n(0.06), 0.0005, 0.015, 3))
mix(x, 0, 0.3 * resonate(np.r_[1.0, np.zeros(n(0.05))], ((3500, 0.005, 1.0),)))
save("time_bonus", x, 0.35)
