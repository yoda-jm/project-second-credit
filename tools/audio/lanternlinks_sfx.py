#!/usr/bin/env python3
"""Sound effects for game 26 (Lantern Links), synthesised with NumPy. Output CC BY-SA 4.0.
All of our own, nothing sampled or imitated from any other game: a mini-golf round in a lantern-lit garden, from
golden hour into the night. Hard things are struck resonators (a click rung through damped modes: steel, urethane,
wood, plastic, stone), water is filtered noise and rising-pitch bubbles, and the jingles are marimba, celesta,
glockenspiel and a plucked bass in G major like the music. No voices anywhere and no recordings.
The ball: putt_soft is a gentle tap of the steel putter face on the hard urethane ball (a crisp, rounded "tock"),
putt_hard a firmer click with a little steel ring (the game pitches both by power). bank_1 and bank_2 are the ball
knocking a hollow wooden rail, land the ball dropping back onto the felt after a jump (a soft thud), sand the ball
ploughing into a bunker (a dull thump and a hiss of grains), roll_loop the ball rolling on felt.
The water and the chasms: splash is the ball plopping into a pond (a plop, a small splash, bubbles rising), fall a
short descending whistle as it drops down a ravine and a distant clatter of pebbles far below, penalty a soft
descending "bwomp".
The cup: cup is a quick roll round the plastic cup (rattling clicks, speeding up) and a hollow "clonk" at the
bottom, lip the ball catching the lip and hopping out (a quick rattle and click).
The gadgets: blade is a windmill sail swatting the ball (a wooden clack and a canvas flap), windmill_loop the mill
turning (slow creaks of the shaft, a wooden gear ticking, a breath of wind), loop_whoosh the ball racing round a
loop-the-loop (a metallic rolling whoosh that rises and falls), pipe_in the ball gulped by a pipe and rattling down
the tube, pipe_out a hollow pop as it shoots out, boost an electric zip up off a booster pad, bumper a springy
rubber "boing-thwack" with a small bright electric ding, mover a stone clack off a sliding block, spinner a
woody thwap off a turnstile bar.
The round: tee is a soft two-note wood-block chime (the next player's turn), card a paper card sliding open,
holed_par a short celesta and marimba jingle, holed_birdie a brighter rising one with a little synthesised bird
chirp at the end, hole_in_one a joyful fanfare (bells, a marimba run up two octaves, a cymbal swell, the last chord
ringing), holed_bogey a gentle, deflated two-note "aww" on a muted horn, round_win the winner's jingle.
firework_launch is a rising whistle, firework_burst a soft pop with a crackle of sparks.
The ambience: crickets_loop is a night garden (crickets chirping at their own rates and pitches, near and far, a
very faint breeze), fountain_loop a small garden fountain trickling.
Loops (seamless, the last sample meets the first): roll_loop (2 s), windmill_loop (4 s), fountain_loop (5 s),
crickets_loop (8 s). They are built from circular noise, whole-cycle swells and events wrapped round the end.
Usage: python3 tools/audio/lanternlinks_sfx.py [out_dir]   (default: godot/games/lanternlinks/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/lanternlinks/audio/sfx", seed=1987)
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


def save_loop(name, x, gain, bright=9000):
    """Saves a loop: low-passed with the end wrapped in front (so the filter starts in its steady state), no fade."""
    x = x - np.mean(x)
    w = n(0.05)
    s.save(name, lp(np.r_[x[-w:], x], bright)[w:], gain, fade=False)


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


def click(sec=0.003, bright=3500):
    return lp(s.noise(sec), bright) * env(n(sec), 0.0003, sec / 3, 3)


def knock(f, sec=0.1, dec=0.02, ratio=2.7, bright=3500):
    """A struck hollow body: a click through two modes (wood, plastic or stone by the ratio and decay)."""
    ex = np.r_[click(0.003, bright), np.zeros(n(sec))]
    return resonate(ex, ((f, dec, 1.0), (f * ratio, dec * 0.4, 0.35)))


def marimba(f, sec=0.5, decay=0.18):
    x = s.bell(f, sec, partials=((1, 1.0), (3.93, 0.22), (9.2, 0.04)), decay=decay)
    return x + 0.25 * np.r_[click(0.006, 2500), np.zeros(len(x) - n(0.006))]


def celesta(f, sec=0.9, decay=0.4):
    """A celesta note: a soft struck bar, almost pure, a faint octave and a glassy upper partial."""
    tt = t(sec)
    x = s.bell(f, sec, partials=((1, 1.0), (2.0, 0.12), (4.1, 0.05)), decay=decay)
    return x * (1 + 0.4 * np.exp(-tt * 60))


def glock(f, sec=0.8, decay=0.35):
    return s.bell(f, sec, partials=((1, 1.0), (2.76, 0.18), (5.4, 0.06)), decay=decay)


def pluck(f, sec, bright=0.5, damp=0.996):
    """A plucked string (Karplus-Strong)."""
    N = n(sec)
    p = max(2, int(round(SR / f)))
    buf = lp(s.rng.uniform(-1, 1, p), 800 + 9000 * bright)
    buf -= np.mean(buf)
    y = np.zeros(N)
    y[:p] = buf[:min(p, N)]
    for i in range(p, N):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p - 1])
    return y * env(N, 0.001, sec, 0.5)


def whoosh(sec, f0, f1, q=1.0):
    """Air rushing: noise through a low-pass sweeping f0 -> f1."""
    return lp(hp(s.noise(sec), 150 * q), curve([(0, f0), (sec, f1)], sec))


def bubble(f, sec):
    """One bubble: a sine whose pitch rises as it forms (the water 'plip')."""
    f_c = f * np.geomspace(1, 2.2, n(sec))
    return np.sin(2 * np.pi * np.cumsum(f_c) / SR) * env(n(sec), 0.001, sec * 0.35, 3)


def band_noise(N, lo, hi, tilt=1.0):
    """Circular band-limited noise (filtered in the frequency domain), so it loops with no seam."""
    F = np.fft.rfftfreq(N, 1 / SR)
    x = np.fft.irfft(np.fft.rfft(s.rng.uniform(-1, 1, N)) * ((F > lo) & (F < hi)) / (1 + (F / hi) ** 2) ** tilt, N)
    return x / np.max(np.abs(x))


def circ_mix(x, start, b):
    """Mixes b into x wrapping round the end: for sounds placed in a loop."""
    idx = (start + np.arange(len(b))) % len(x)
    np.add.at(x, idx, b)


def ball(sec=0.12, bright=1.0):
    """The urethane ball itself: a hard, short, high 'tick' (two stiff modes that die almost at once)."""
    ex = np.r_[click(0.0015, 5000 + 4000 * bright), np.zeros(n(sec))]
    return resonate(ex, ((2350, 0.006, 1.0), (4100, 0.004, 0.5 * bright)))


def chirp(f, sec=0.07):
    """A little bird chirp (synthesised): a pure whistle that swoops up and flicks down, with a flutter."""
    fv = curve([(0, f), (sec * 0.45, f * 1.5), (sec, f * 1.1)], sec)
    return osc(fv, sec, ((1, 1.0), (2, 0.06))) * curve([(0, 0), (sec * 0.15, 1), (sec * 0.7, 0.8), (sec, 0)], sec)


def cricket(f, sec, pulses=3, rate=32.0):
    """One cricket chirp: a pure, slightly buzzy tone gated in quick pulses (the wings' strokes)."""
    tt = t(sec)
    gate = np.clip(np.sin(np.pi * tt * rate), 0, 1) ** 2 * (tt < pulses / rate)
    tone = osc(f * (1 + 0.004 * np.sin(2 * np.pi * rate * tt)), sec, ((1, 1.0), (2, 0.08), (3, 0.03)))
    return tone * gate


# G major (MIDI), the jingles' key
G3, B3, D4, E4, Fs4, G4, A4, B4, C5, D5, E5, Fs5, G5, A5, B5, C6, D6, E6, Fs6, G6, A6, B6, D7, G7 = (
    m2f(m) for m in (55, 59, 62, 64, 66, 67, 69, 71, 72, 74, 76, 78, 79, 81, 83, 84, 86, 88, 90, 91, 93, 95, 98, 103))
G2, C3, D3 = m2f(43), m2f(48), m2f(50)

# --- the ball ---
d = 0.2  # putt_soft: a gentle tap: the steel face on the urethane ball, a crisp, rounded "tock"
x = np.zeros(n(d))
face = resonate(np.r_[click(0.002, 4500), np.zeros(n(0.15))], ((1650, 0.012, 1.0), (3900, 0.006, 0.35)))
mix(x, 0, 0.8 * face, 0.4 * ball(0.1, 0.6), 0.3 * thump(420, 200, 0.05, 0.01))
save("putt_soft", lp(x, 7000), 0.36)

d = 0.4  # putt_hard: a firmer click, the ball's crack on top and a little ring of the steel head
x = np.zeros(n(d))
face = resonate(np.r_[click(0.0015, 8000), np.zeros(n(0.35))], ((1750, 0.02, 1.0), (4150, 0.012, 0.5),
                                                                 (6420, 0.06, 0.08), (9150, 0.04, 0.04)))
mix(x, 0, 0.8 * face, 0.6 * ball(0.1, 1.0), 0.35 * thump(520, 220, 0.05, 0.01))
save("putt_hard", x, 0.5)

d = 0.25  # bank_1: the ball knocks a hollow wooden rail
x = np.zeros(n(d))
mix(x, 0, 0.8 * knock(440, 0.2, 0.03, 2.45), 0.3 * ball(0.08, 0.5), 0.3 * thump(240, 120, 0.06, 0.015))
save("bank_1", x, 0.4)

d = 0.25  # bank_2: the same, a board a little lower and drier
x = np.zeros(n(d))
mix(x, 0, 0.8 * knock(365, 0.2, 0.024, 2.7), 0.3 * ball(0.08, 0.4), 0.35 * thump(210, 110, 0.06, 0.015))
save("bank_2", x, 0.4)

d = 0.25  # land: the ball drops back onto the felt after a jump: a soft padded thud, a click muffled by the cloth
x = np.zeros(n(d))
mix(x, 0, 0.8 * thump(150, 60, 0.15, 0.03), 0.2 * lp(ball(0.06, 0.3), 1800))
mix(x, 0, 0.2 * lp(s.noise(0.05), 900) * env(n(0.05), 0.001, 0.012, 3))
save("land", x, 0.4)

d = 0.6  # sand: the ball ploughs into a bunker: a dull thump, a crunch, a hiss of grains settling
x = np.zeros(n(d))
mix(x, 0, 0.7 * thump(130, 55, 0.2, 0.04), 0.3 * lp(s.noise(0.1), 2000) * env(n(0.1), 0.001, 0.03, 3))
ln = 0.5
grains = hp(s.noise(ln), 3000) * s.rng.uniform(0, 1, n(ln)) ** 6
hiss = hp(lp(s.noise(ln), 6500), 1800)
mix(x, n(0.01), (0.45 * grains + 0.15 * hiss) * curve([(0, 0), (0.03, 1), (0.2, 0.4), (ln, 0)], ln))
save("sand", lp(x, 6000), 0.4)

d = 2.0  # roll_loop: exactly 2 s: the ball rolling on felt, a soft low rumble with a faint turning lilt
N = n(d)
tt = np.arange(N) / SR
x = band_noise(N, 40, 320, 1.3) * (0.85 + 0.15 * np.sin(2 * np.pi * 14 * tt / d))
x += 0.12 * band_noise(N, 600, 2400) * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * tt / d + 1))
save_loop("roll_loop", x, 0.25, 3000)

# --- water and chasms ---
d = 1.2  # splash: a plop, a small splash of droplets, bubbles rising
x = np.zeros(n(d))
mix(x, 0, 0.6 * bubble(260, 0.12), 0.5 * thump(300, 90, 0.1, 0.02))
mix(x, n(0.005), 0.5 * whoosh(0.3, 6000, 1200) * env(n(0.3), 0.003, 0.07, 3))
for k in range(9):  # droplets falling back
    mix(x, n(0.06 + s.rng.uniform(0, 0.25)), 0.12 * bubble(s.rng.uniform(900, 1600), 0.03))
for k in range(8):  # bubbles surfacing after
    mix(x, n(0.25 + k * 0.08 + s.rng.uniform(0, 0.05)), (0.18 * 0.85 ** k) * bubble(s.rng.uniform(450, 800), 0.05))
save("splash", lp(x, 8000), 0.45)

d = 1.4  # fall: a short descending whistle, then far below a distant clatter of pebbles
x = np.zeros(n(d))
ln = 0.65
fv = curve([(0, 1900), (ln, 520)], ln) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t(ln)))
mix(x, 0, 0.35 * osc(fv, ln, ((1, 1.0), (2, 0.05))) * curve([(0, 0), (0.05, 1), (0.5, 0.6), (ln, 0)], ln))
mix(x, 0, 0.08 * whoosh(ln, 3000, 800) * curve([(0, 0), (0.1, 1), (ln, 0)], ln))
far = np.zeros(n(0.7))
for k in range(9):
    mix(far, n(k * 0.045 + s.rng.uniform(0, 0.08) + 0.02 * k), (0.4 * 0.8 ** k) * knock(s.rng.uniform(900, 1700), 0.06, 0.008, 1.8))
far = lp(far, 2200)
mix(x, n(0.7), 0.5 * far, 0.2 * thump(110, 60, 0.12, 0.03))
save("fall", x, 0.32)

d = 0.7  # penalty: a soft descending "bwomp"
x = np.zeros(n(d))
fv = curve([(0, 230), (0.5, 92)], d)
b = osc(fv, d, ((1, 1.0), (2, 0.35), (3, 0.12)))
mix(x, 0, lp(b, curve([(0, 1500), (d, 400)], d)) * curve([(0, 0), (0.03, 1), (0.35, 0.6), (d, 0)], d))
save("penalty", x, 0.3)

# --- the cup ---
d = 0.7  # cup: a quick roll round the plastic cup (clicks speeding up), then the hollow clonk at the bottom
x = np.zeros(n(d))
st = 0.0
for k in range(7):
    gap = 0.065 * 0.8 ** k
    mix(x, n(st), (0.18 + 0.03 * k) * knock(s.rng.uniform(1700, 2100), 0.04, 0.005, 1.7, 5000))
    st += gap
mix(x, 0, 0.06 * lp(hp(s.noise(st), 400), 2500) * curve([(0, 0.4), (st, 1)], st))
mix(x, n(st + 0.02), 0.9 * knock(310, 0.4, 0.05, 2.15), 0.5 * thump(190, 80, 0.12, 0.03))
mix(x, n(st + 0.1), 0.18 * knock(330, 0.3, 0.03, 2.15))  # a little settling second knock
save("cup", x, 0.5)

d = 0.4  # lip: the ball catches the lip, rattles and hops out with a click
x = np.zeros(n(d))
for k, (st, f) in enumerate(((0, 1900), (0.03, 2200), (0.052, 1750))):
    mix(x, n(st), 0.35 * knock(f, 0.05, 0.005, 1.7, 5000))
mix(x, n(0.07), 0.3 * knock(330, 0.2, 0.02, 2.15))
mix(x, n(0.16), 0.3 * ball(0.06, 0.5), 0.2 * thump(180, 90, 0.05, 0.012))
save("lip", x, 0.4)

# --- the gadgets ---
d = 0.4  # bumper: a springy rubber boing-thwack with a small bright electric ding
x = np.zeros(n(d))
slap = lp(hp(s.noise(0.03), 600), 5000) * env(n(0.03), 0.0003, 0.006, 3)
mix(x, 0, 0.6 * slap, 0.6 * thump(260, 90, 0.1, 0.025))
tb = t(0.3)
fv = np.geomspace(170, 330, n(0.3)) * (1 + 0.25 * np.sin(2 * np.pi * 22 * tb) * np.exp(-tb * 10))
mix(x, n(0.004), 0.45 * osc(fv, 0.3, ((1, 1.0), (2, 0.3), (3, 0.1))) * env(n(0.3), 0.003, 0.08, 3))
ding = glock(D7, 0.4, 0.14) + 0.4 * osc(D7 * 1.004, 0.4) * env(n(0.4), 0.001, 0.05, 3)
mix(x, n(0.012), 0.16 * ding)
save("bumper", x, 0.45)

d = 0.35  # blade: a windmill sail swats the ball: a wooden clack and a canvas flap
x = np.zeros(n(d))
mix(x, 0, 0.8 * knock(520, 0.2, 0.022, 2.3), 0.3 * ball(0.06, 0.5))
ln = 0.12
flap = lp(hp(s.noise(ln), 300), 2800) * (0.5 + 0.5 * np.sin(2 * np.pi * 55 * t(ln)) ** 2)
mix(x, n(0.015), 0.4 * flap * curve([(0, 0), (0.01, 1), (ln, 0)], ln))
save("blade", x, 0.4)

d = 0.25  # mover: the ball clacks off a sliding stone block (hard, dense, a gritty edge)
x = np.zeros(n(d))
mix(x, 0, 0.7 * knock(1150, 0.15, 0.011, 1.85, 6000), 0.3 * ball(0.06, 0.8), 0.35 * thump(180, 90, 0.06, 0.012))
mix(x, 0, 0.12 * hp(s.noise(0.04), 2500) * env(n(0.04), 0.0005, 0.01, 3))
save("mover", x, 0.42)

d = 0.3  # spinner: a woody thwap off the turning turnstile bar
x = np.zeros(n(d))
mix(x, 0, 0.7 * knock(270, 0.25, 0.035, 2.35), 0.4 * lp(hp(s.noise(0.02), 500), 3000) * env(n(0.02), 0.0005, 0.005, 3))
mix(x, 0, 0.35 * thump(200, 100, 0.07, 0.015), 0.25 * ball(0.06, 0.5))
save("spinner", x, 0.42)

d = 1.1  # loop_whoosh: the ball races round a loop-the-loop track: a metallic rolling whoosh rising and falling
x = np.zeros(n(d))
shape = curve([(0, 0), (0.25, 0.8), (0.5, 1.0), (0.8, 0.6), (d, 0)], d)
pitch = curve([(0, 0.8), (0.5, 1.35), (d, 0.9)], d)
roll = hp(s.noise(d), 200) * (0.6 + 0.4 * s.rng.uniform(0, 1, n(d)) ** 2)
ring = sum(a * osc(f * pitch, d) for f, a in ((720, 1.0), (1330, 0.6), (2170, 0.35), (3080, 0.2)))
ring *= 0.6 + 0.4 * lp(np.abs(s.noise(d)), 60) / 0.5
mix(x, 0, 0.5 * lp(roll, 700 + 2800 * (pitch - 0.8)) * shape, 0.12 * ring * shape)
mix(x, 0, 0.15 * whoosh(d, 900, 900) * shape)
save("loop_whoosh", lp(lp(x, 3500), 6000), 0.36)

tube = ((230, 0.05, 1.0), (460, 0.04, 0.6), (690, 0.03, 0.35), (920, 0.02, 0.2))
d = 0.9  # pipe_in: the ball dropped into a pipe: a hollow gulp, then a rattle down the tube, fading away
x = np.zeros(n(d))
g = osc(curve([(0, 520), (0.12, 170)], 0.15), 0.15, ((1, 1.0), (2, 0.2))) * env(n(0.15), 0.003, 0.05, 3)
mix(x, 0, 0.5 * g, 0.3 * resonate(np.r_[click(0.004, 3000), np.zeros(n(0.2))], tube))
st = 0.1
for k in range(10):
    ex = np.r_[click(0.002, 5000), np.zeros(n(0.12))]
    tick = resonate(ex, tube) * 0.3 + knock(s.rng.uniform(1600, 2000), 0.12, 0.005, 1.7, 5000)[:len(ex)]
    mix(x, n(st), (0.25 * 0.8 ** k) * lp(tick, 5000 - 350 * k))
    st += 0.05 + 0.012 * k
save("pipe_in", x, 0.42)

d = 0.4  # pipe_out: a hollow pop as the ball shoots out of the mouth
x = np.zeros(n(d))
puff = hp(s.noise(0.05), 200) * env(n(0.05), 0.001, 0.012, 3)
mix(x, 0, 0.6 * resonate(np.r_[puff, np.zeros(n(0.3))], tube), 0.5 * thump(380, 140, 0.08, 0.018))
mix(x, n(0.01), 0.2 * ball(0.06, 0.6))
save("pipe_out", x, 0.42)

d = 0.35  # boost: a booster pad: a short electric zip upward
x = np.zeros(n(d))
fv = np.geomspace(260, 2300, n(d)) * (1 + 0.04 * np.sin(2 * np.pi * 45 * t(d)))
z = osc(fv, d, [(k, 1 / k) for k in range(1, 8)])
mix(x, 0, 0.35 * lp(z, curve([(0, 1500), (d, 6000)], d)) * curve([(0, 0), (0.02, 1), (0.22, 0.8), (d, 0)], d))
mix(x, 0, 0.08 * hp(s.noise(d), 3000) * curve([(0, 0), (0.1, 1), (d, 0)], d))
save("boost", x, 0.28)

d = 4.0  # windmill_loop: exactly 4 s: the mill turning, the shaft creaking twice a turn, a wooden gear ticking
N = n(d)  # eight times a second, the wind breathing in whole cycles; every event wrapped round the end
tt = np.arange(N) / SR
x = 0.25 * band_noise(N, 80, 900, 1.2) * (0.7 + 0.3 * np.sin(2 * np.pi * tt / d))
for k in range(16):  # the gear teeth, alternating two woods
    f = 780 if k % 2 == 0 else 640
    circ_mix(x, n(k * 0.25), (0.2 if k % 4 == 0 else 0.13) * knock(f, 0.08, 0.012, 2.4))
for st, f0, ln in ((0.55, 95, 0.7), (2.6, 110, 0.6)):  # creaks: a stick-slip pulse train rung through the wood
    m = n(ln)
    rate = curve([(0, f0), (ln * 0.5, f0 * 1.3), (ln, f0 * 0.9)], ln)
    ph = np.cumsum(rate) / SR
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (0.6 + 0.4 * s.rng.uniform(0, 1, m))
    cr = resonate(pulses, ((330, 0.02, 1.0), (860, 0.012, 0.6), (1720, 0.006, 0.3)))
    circ_mix(x, n(st), 0.4 * cr * np.sin(np.pi * np.arange(m) / m) ** 2)
save_loop("windmill_loop", x, 0.3, 6000)

# --- the round ---
def woodblock(f):
    """A tuned wood block: a knock with a longer ring, a soft marimba an octave down under it."""
    return knock(f, 0.4, 0.07, 2.9, 3000)[:n(0.4)] * 0.8 + 0.3 * marimba(f / 2, 0.4, 0.14)


d = 0.8  # tee: a soft two-note wood-block chime, D6 then G5 (the next player's turn)
x = np.zeros(n(d))
mix(x, 0, 0.35 * woodblock(D6))
mix(x, n(0.16), 0.35 * woodblock(G5))
save("tee", x, 0.34)

d = 0.5  # card: a paper card slides out and opens (a papery swish and a soft flick)
x = np.zeros(n(d))
ln = 0.32
sw = hp(lp(s.noise(ln), curve([(0, 2500), (ln, 7000)], ln)), 1200)
sw *= 1 + 0.4 * lp(s.noise(ln), 40) * 4
mix(x, 0, 0.3 * sw * curve([(0, 0), (0.12, 1), (0.26, 0.5), (ln, 0)], ln))
mix(x, n(0.27), 0.25 * resonate(np.r_[click(0.003, 6000), np.zeros(n(0.1))], ((2400, 0.008, 1.0), (4200, 0.004, 0.5))))
save("card", x, 0.3)

d = 1.2  # holed_par: a short, pleasant jingle, celesta over marimba: G5 B5 D6, then a G6 chord ringing
x = np.zeros(n(d))
for k, f in enumerate((G5, B5, D6)):
    mix(x, n(k * 0.11), 0.28 * celesta(f, 0.6, 0.2), 0.22 * marimba(f / 2, 0.4, 0.12))
for f in (G5, B5, D6, G6):
    mix(x, n(0.33), 0.14 * celesta(f, 0.85, 0.35))
mix(x, n(0.33), 0.3 * marimba(G4, 0.8, 0.3), 0.3 * pluck(G2 * 2, 0.8, 0.4, 0.995))
save("holed_par", x, 0.48)

d = 1.7  # holed_birdie: a brighter rising run to a sunny chord, and a little bird chirping a reply
x = np.zeros(n(d))
for k, f in enumerate((G5, A5, B5, D6, E6, G6)):
    mix(x, n(k * 0.07), 0.22 * celesta(f, 0.5, 0.18), 0.16 * marimba(f / 2, 0.35, 0.1), 0.1 * glock(f * 2, 0.4, 0.12))
for f in (B5, D6, G6, B6):
    mix(x, n(0.44), 0.13 * celesta(f, 1.0, 0.4))
mix(x, n(0.44), 0.18 * glock(D7, 1.0, 0.4), 0.3 * marimba(G4, 0.9, 0.3), 0.3 * pluck(G2 * 2, 0.9, 0.4, 0.996))
for k, (st, f) in enumerate(((0.8, 3200), (0.88, 3600), (0.96, 3400), (1.18, 3900), (1.25, 3700))):
    mix(x, n(st), 0.12 * chirp(f, 0.06 if k < 3 else 0.05))
save("holed_birdie", x, 0.52)

d = 3.3  # hole_in_one: a joyful fanfare: bell chords, a marimba run up two octaves, a cymbal swell, the chord rings
x = np.zeros(n(d))
for st, ch in ((0.0, (G5, B5, D6)), (0.24, (A5, C6, E6)), (0.48, (B5, D6, G6))):
    for f in ch:
        mix(x, n(st), 0.12 * glock(f, 0.6, 0.25), 0.1 * celesta(f, 0.6, 0.2))
    mix(x, n(st), 0.3 * pluck(ch[0] / 4, 0.4, 0.45, 0.99))
run = [G4, A4, B4, D5, E5, G5, A5, B5, D6, E6, G6, A6, B6]
for k, f in enumerate(run):
    mix(x, n(0.72 + k * 0.045), (0.14 + 0.006 * k) * marimba(f, 0.35, 0.1))
ln = 1.35  # the suspended cymbal swell into the big chord
cym = hp(s.noise(ln), 4500) * curve([(0, 0), (1.25, 1), (ln, 0.6)], ln) ** 2
mix(x, n(0.3), 0.18 * cym)
hit = 1.32
mix(x, n(hit), 0.1 * hp(s.noise(1.6), 5000) * env(n(1.6), 0.002, 0.5, 2))
for f in (G4, B4, D5, G5, B5, D6, G6):
    mix(x, n(hit), 0.08 * celesta(f, 1.9, 0.9), 0.06 * marimba(f, 1.2, 0.4))
for f in (G6, B6, D7):
    mix(x, n(hit), 0.08 * glock(f, 1.9, 0.8))
mix(x, n(hit), 0.4 * pluck(G2 * 2, 1.9, 0.45, 0.998), 0.35 * thump(110, 45, 0.3, 0.08))
for k, f in enumerate((D6, G6, B6, D7)):  # a sparkle of bells as it rings
    mix(x, n(hit + 0.5 + k * 0.12), 0.08 * glock(f, 0.8, 0.3))
save("hole_in_one", x, 0.62)


def muted_horn(f0, f1, sec, bend_at=0.6):
    """A muted brass-like tone (no voice): harmonics under a closing low-pass, a slow vibrato, a sag at the end."""
    fv = curve([(0, f0), (sec * bend_at, f0), (sec, f1)], sec) * (1 + 0.006 * np.sin(2 * np.pi * 5 * t(sec)))
    x = osc(fv, sec, [(k, 1 / k ** 1.1) for k in range(1, 10)])
    x = lp(x, curve([(0, 500), (0.06, 1300), (sec, 600)], sec))
    return x * curve([(0, 0), (0.05, 1), (sec * 0.7, 0.8), (sec, 0)], sec)


d = 1.2  # holed_bogey: a gentle, deflated "aww": two notes on a muted horn, D4 then B3 sagging flat
x = np.zeros(n(d))
mix(x, 0, 0.4 * muted_horn(D4, D4, 0.3))
mix(x, n(0.3), 0.45 * muted_horn(B3, m2f(57.4), 0.8, 0.45))
mix(x, n(0.3), 0.15 * marimba(G3, 0.6, 0.2))
save("holed_bogey", x, 0.3)

d = 3.8  # round_win: the winner's jingle: a marimba and celesta tune in G over I-IV-V-I, a plucked bass, bells
x = np.zeros(n(d))
beat = 0.2
tune = ((0, D5), (1, G5), (2, B5), (3, D6), (4, C6), (5, B5), (6, A5), (7, B5), (8, C6), (9, E6), (10, D6),
        (11, B5), (12, A5), (13, Fs5), (14, A5), (15, D6))
for k, f in tune:
    mix(x, n(k * beat), 0.22 * marimba(f, 0.35, 0.12), 0.12 * celesta(f * 2, 0.4, 0.15))
for st, root, ch in ((0, G2, (B4, D5, G5)), (4, C3, (C5, E5, G5)), (8, C3, (C5, E5, A5)), (12, D3, (C5, Fs5, A5))):
    mix(x, n(st * beat), 0.4 * pluck(root * 2, 0.8, 0.45, 0.994), 0.3 * thump(110, 45, 0.15, 0.05))
    mix(x, n((st + 2) * beat), 0.3 * pluck(root * 3, 0.5, 0.45, 0.99))
    for p in ch:
        mix(x, n(st * beat), 0.07 * celesta(p, 0.7, 0.25))
end = 16 * beat
for f in (G4, B4, D5, G5, B5, D6):
    mix(x, n(end), 0.1 * celesta(f, 2.0, 0.9), 0.07 * marimba(f, 1.4, 0.45))
mix(x, n(end), 0.14 * glock(G6, 1.6, 0.7), 0.1 * glock(B6, 1.6, 0.6), 0.45 * pluck(G2 * 2, 1.6, 0.45, 0.998))
mix(x, n(end), 0.35 * thump(110, 40, 0.3, 0.08), 0.06 * hp(s.noise(1.2), 6000) * env(n(1.2), 0.003, 0.4, 2))
for k, f in enumerate((G6, D6, B6, G7)):
    mix(x, n(end + 0.25 + k * 0.11), 0.07 * glock(f, 0.7, 0.25))
save("round_win", x, 0.6)

d = 1.3  # firework_launch: a rising whistle and the hiss of the rocket's trail
x = np.zeros(n(d))
fv = np.geomspace(700, 2800, n(d)) * (1 + 0.01 * np.sin(2 * np.pi * 9 * t(d)))
shape = curve([(0, 0), (0.1, 0.8), (1.0, 1.0), (d, 0)], d)
mix(x, 0, 0.25 * osc(fv, d, ((1, 1.0), (2, 0.04))) * shape)
mix(x, 0, 0.12 * hp(lp(s.noise(d), 5000), 1500) * curve([(0, 0), (0.03, 1), (0.3, 0.5), (d, 0)], d))
mix(x, 0, 0.3 * thump(160, 70, 0.1, 0.02))
save("firework_launch", x, 0.2)

d = 1.5  # firework_burst: a soft, rounded pop (far off) and a crackle of sparks dying away
x = np.zeros(n(d))
mix(x, 0, 0.7 * lp(thump(120, 40, 0.3, 0.07), 900), 0.3 * lp(s.noise(0.08), 1500) * env(n(0.08), 0.002, 0.03, 3))
ln = 1.3
sparks = hp(s.noise(ln), 2000) * (s.rng.uniform(0, 1, n(ln)) ** 30)
mix(x, n(0.12), 0.9 * lp(sparks, 7000) * curve([(0, 0), (0.08, 1), (0.6, 0.5), (ln, 0)], ln))
save("firework_burst", lp(x, 6000), 0.34)

# --- the ambience ---
d = 8.0  # crickets_loop: exactly 8 s: a night garden: crickets chirping each at its own steady rate (whole
N = n(d)  # numbers of chirps per loop), near and far, a very faint breeze swelling in whole cycles
tt = np.arange(N) / SR
x = 0.03 * band_noise(N, 120, 1400, 1.3) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / d))
for f, per_loop, pulses, rate, a, bright in ((4400, 16, 3, 30, 0.22, 9000), (4950, 20, 4, 36, 0.14, 7000),
                                              (3900, 11, 3, 26, 0.1, 5000), (5300, 26, 2, 40, 0.07, 4500),
                                              (4150, 13, 5, 34, 0.05, 3800)):
    period = d / per_loop
    ch = lp(cricket(f, (pulses + 1) / rate, pulses, rate), bright)
    off = s.rng.uniform(0, period)
    for k in range(per_loop):
        circ_mix(x, n(off + k * period), a * s.rng.uniform(0.75, 1.0) * ch)
# a slower, farther cricket trills in two long bursts per loop
for st in (1.3, 5.3):
    tr = cricket(3650, 1.2, 40, 34) * np.sin(np.pi * t(1.2) / 1.2) ** 2
    circ_mix(x, n(st), 0.04 * lp(tr, 3000))
save_loop("crickets_loop", x, 0.22, 11000)

d = 5.0  # fountain_loop: exactly 5 s: a small garden fountain: a trickle of water into a basin, a low burble,
N = n(d)  # little drops plipping in; all wrapped round the end
tt = np.arange(N) / SR
x = 0.35 * band_noise(N, 400, 5000, 0.8) * (0.8 + 0.12 * np.sin(2 * np.pi * 3 * tt / d) + 0.08 * np.sin(2 * np.pi * 7 * tt / d))
x += 0.3 * band_noise(N, 80, 500, 1.2) * (0.8 + 0.2 * np.sin(2 * np.pi * 2 * tt / d + 1))
for k in range(70):
    circ_mix(x, int(s.rng.uniform(0, N)), s.rng.uniform(0.04, 0.12) * bubble(s.rng.uniform(500, 1800), s.rng.uniform(0.015, 0.04)))
save_loop("fountain_loop", x, 0.25, 7000)
