#!/usr/bin/env python3
"""Sound effects for game 8 (Iron Flags), synthesised with NumPy. Output CC BY-SA 4.0.
Usage: python3 tools/audio/flags_sfx.py [out_dir]   (default: godot/games/flags/audio/sfx)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import Synth, SR

s = Synth(sys.argv[1] if len(sys.argv) > 1 else "godot/games/flags/audio/sfx", seed=1996)
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


def tone(freqs, shape="saw", harmonics=8):
    """A tone following a per-sample frequency curve: 'saw' (brassy), 'square' (chippy) or 'sine'."""
    ph = 2 * np.pi * np.cumsum(freqs) / SR
    if shape == "sine":
        return np.sin(ph)
    ks = range(1, harmonics + 1) if shape == "saw" else range(1, 2 * harmonics, 2)
    return sum(np.sin(k * ph) / k for k in ks)


def note(f, sec, shape="saw", attack=0.01, decay=0.3, curve=2.0, vib=0.0):
    tt = t(sec)
    return tone(f * (1 + vib * np.sin(2 * np.pi * 5.5 * tt)), shape) * env(len(tt), attack, decay, curve)


def shot(bright=1.0, body=150.0, sec=0.18):
    """One robot gun round: a noise crack, a pitched thump and a tiny metallic ring."""
    crack = hp(s.noise(sec), 1500) * env(n(sec), 0.0005, 0.025 * bright, 4)
    thump = s.sweep(body, body * 0.4, sec) * env(n(sec), 0.001, 0.05, 3)
    ring = s.bell(2200 * bright, sec, partials=((1, 1.0), (2.7, 0.4)), decay=0.04)
    return crack + 0.8 * thump + 0.12 * ring


def boom(sec, f0=90, f1=25, crack_from=6000, tail=1.0):
    """An explosion body: a falling sine thump, a darkening crack and a rumble."""
    return (1.3 * s.sweep(f0, f1, sec) * env(n(sec), 0.002, 0.25 * tail, 3)
            + lp(s.noise(sec), np.geomspace(crack_from, 150, n(sec))) * env(n(sec), 0.0005, 0.3 * tail, 3)
            + 0.6 * lp(s.noise(sec), 180) * env(n(sec), 0.01, 0.8 * tail, 2))


def debris(sec, count, start=0.25):
    x = np.zeros(n(sec))
    for k in range(count):
        mix(x, n(start + k * (sec - start - 0.1) / count + s.rng.uniform(0, 0.04)),
            hp(s.noise(0.04), 1500) * env(n(0.04), 0.0005, 0.015) * (1 - k / (count + 1)))
    return x


def robot_voice(syllables, grit=0.0):
    """A cheeky robot voice: a buzzy pulse through two formant bands, ring-modulated. Each syllable is
    (seconds, start Hz, end Hz, formant 1, formant 2)."""
    out = []
    for sec, f0, f1, fa, fb in syllables:
        buzz = tone(np.geomspace(f0, f1, n(sec)), "saw", 14)
        v = lp(hp(buzz, fa * 0.7), fa * 1.3) + 0.6 * lp(hp(buzz, fb * 0.75), fb * 1.25)
        v *= env(n(sec), 0.008, sec * 0.6, 1.5)
        out += [v, np.zeros(n(0.02))]
    v = np.concatenate(out)
    v *= 0.55 + 0.45 * np.sin(2 * np.pi * 95 * np.arange(len(v)) / SR)  # ring modulation
    if grit:
        v = np.tanh(v / (np.max(np.abs(v)) + 1e-9) * (1 + 4 * grit))
    return v


# --- guns ---
d = 0.34  # a robot rifle: a three-round burst
x = np.zeros(n(d))
for k in range(3):
    mix(x, n(k * 0.075), shot(1.0, 170, 0.16) * (1 - 0.12 * k))
save("rifle", x, 0.62)

d = 0.42  # a submachine gun: a fast rattle
x = np.zeros(n(d))
for k in range(7):
    mix(x, n(k * 0.048), shot(1.3, 210, 0.1) * (0.8 + 0.2 * (k % 2)))
save("smg", x, 0.55)

d = 0.7  # a sniper rifle: a sharp supersonic crack and a long thin echo
crack = hp(s.noise(d), 2500) * env(n(d), 0.0002, 0.012, 3)
body = s.sweep(420, 70, d) * env(n(d), 0.0005, 0.05, 3)
echo = lp(hp(s.noise(d), 700), 3500) * env(n(d), 0.03, 0.3, 3) * 0.25
save("sniper", 1.4 * crack + 0.7 * body + echo + 0.15 * s.bell(3100, d, decay=0.1), 0.7)

d = 0.9  # a rocket launch: a pop and a whoosh that flies away
whoosh = lp(s.noise(d), np.geomspace(700, 5000, n(d))) * env(n(d), 0.015, 0.45, 2)
save("rocket", whoosh + 0.7 * s.sweep(180, 70, d) * env(n(d), 0.001, 0.08, 3)
       + 0.3 * hp(s.noise(d), 3000) * env(n(d), 0.0005, 0.02, 4), 0.6)

d = 0.62  # a flamethrower burst: a flickering roar
tt = t(d)
flicker = 0.7 + 0.3 * np.sin(2 * np.pi * 17 * tt) * np.sin(2 * np.pi * 7.3 * tt + 1)
shape = np.clip(tt / 0.05, 0, 1) * np.clip((d - tt) / 0.2, 0, 1)
roar = lp(s.noise(d), 1400) + 0.35 * hp(lp(s.noise(d), 5000), 1800)
save("flame", roar * flicker * shape + 0.4 * s.sweep(90, 60, d) * shape, 0.55)

d = 0.28  # a laser: a falling zap with a buzz
zap = tone(np.geomspace(2600, 240, n(d)), "square", 6) * env(n(d), 0.001, 0.12, 2)
save("laser", lp(zap, 7000) + 0.3 * np.sin(2 * np.pi * 60 * t(d)) * zap, 0.45)

d = 1.3  # a tank gun: a heavy boom with a crack
x = boom(d, 110, 28, 5000, 1.0) + 0.5 * lp(s.noise(d), 220) * env(n(d), 0.01, 0.6, 2) + 0.8 * hp(s.noise(d), 1500) * env(n(d), 0.0005, 0.03, 4)
save("tank_gun", x, 0.85)

d = 0.9  # a gatling gun: a whine that spins up under a rattle of rounds
x = 0.18 * tone(np.geomspace(120, 480, n(d)), "saw", 6) * np.clip(t(d) / 0.1, 0, 1) * np.clip((d - t(d)) / 0.25, 0, 1)
x = lp(x, 2500)
for k in range(22):
    mix(x, n(0.06 + k * 0.034), shot(1.1, 190, 0.08) * 0.7)
save("gatling", x, 0.6)

d = 1.6  # a howitzer: a deep, distant thump and a long rumble
x = 1.5 * s.sweep(65, 22, d) * env(n(d), 0.003, 0.35, 3) + 0.7 * lp(s.noise(d), 260) * env(n(d), 0.005, 0.9, 2)
x += 0.25 * lp(s.noise(d), 3000) * env(n(d), 0.001, 0.04, 4)
save("howitzer", x, 0.85)

d = 1.1  # a missile launch: an ignition pop, a rising roar and a hiss
x = 0.8 * s.sweep(150, 60, d) * env(n(d), 0.001, 0.07, 3)
x += lp(s.noise(d), np.geomspace(400, 6000, n(d))) * env(n(d), 0.04, 0.7, 1.6)
x += 0.25 * tone(np.geomspace(300, 900, n(d)), "saw", 4) * env(n(d), 0.05, 0.5, 2)
save("missile", x, 0.6)

# --- impacts ---
d = 0.9  # a small explosion: a grenade, a robot, a light vehicle
save("explosion_small", boom(d, 120, 35, 7000, 0.5) + 0.25 * debris(d, 6, 0.2), 0.8)

d = 2.6  # a big explosion: a building or a fort, two booms and a long fall of debris
x = boom(d, 75, 20, 5000, 1.3)
mix(x, n(0.18), 0.8 * boom(d - 0.18, 60, 18, 3000, 1.1))
x += 0.35 * debris(d, 22, 0.35)
save("explosion_big", x, 0.9)

d = 0.4  # a bullet ricochets off armour: a clank and a whining ping
clank = s.bell(1700, d, partials=((1, 1.0), (2.41, 0.7), (3.93, 0.4), (5.8, 0.2)), decay=0.06)
ping = np.sin(2 * np.pi * np.cumsum(np.geomspace(4200, 2100, n(d))) / SR) * env(n(d), 0.02, 0.12, 2)
save("hit_metal", clank + 0.5 * ping + 0.5 * hp(s.noise(d), 3000) * env(n(d), 0.0003, 0.01, 4), 0.5)

d = 0.65  # a robot dies: a falling squeak, a sputter and a crunch of scrap
tt = t(d)
squeak = tone(900 * np.exp(-3 * tt) + 120, "square", 5) * env(n(d), 0.003, 0.25, 1.5)
held = np.repeat(squeak[::120], 120)[:len(squeak)]  # sample-and-hold for a crunchy, broken voice
x = np.zeros(n(d))
mix(x, 0, 0.5 * lp(held, 4000) * np.clip((0.4 - tt) / 0.1, 0, 1))
for k in range(5):
    mix(x, n(0.28 + k * 0.05), s.bell(s.rng.uniform(600, 1400), 0.1, partials=((1, 1.0), (2.9, 0.5)), decay=0.04) * 0.3)
x += 0.4 * lp(s.noise(d), 1500) * env(n(d), 0.26, 0.15, 3) * (tt > 0.25)
save("robot_die", x, 0.55)

# --- jingles and interface ---
d = 1.25  # a flag captured: a bright rising arpeggio, sparkle and a held major chord
x = np.zeros(n(d))
for i, f in enumerate((523.3, 659.3, 784.0, 1046.5)):
    mix(x, n(i * 0.08), 0.35 * lp(note(f, 0.3, "square", 0.003, 0.15, 2), 5000))
    mix(x, n(i * 0.08), 0.5 * s.bell(f * 2, 0.4, decay=0.2))
for f in (523.3, 659.3, 784.0, 1046.5):
    mix(x, n(0.34), 0.2 * lp(note(f, 0.9, "saw", 0.01, 0.6, 1.5, vib=0.006), 3500))
mix(x, n(0.34), 0.6 * s.bell(2093, 0.9, decay=0.4))
save("capture", x, 0.6)

d = 1.05  # a territory lost: two falling minor notes, a little flat and dusty
x = np.zeros(n(d))
for st, f, ln in ((0.0, 466.2, 0.3), (0.25, 349.2, 0.8)):
    mix(x, n(st), lp(note(f, ln, "square", 0.005, ln * 0.6, 1.8) + 0.6 * note(f * 1.19, ln, "square", 0.005, ln * 0.6, 1.8), 2200) * 0.3)
mix(x, n(0.25), 0.5 * s.sweep(90, 45, 0.4) * env(n(0.4), 0.002, 0.12, 3))
save("lost", x, 0.55)

d = 0.5  # a unit ready: a hydraulic clunk and two pleasant pings
x = 0.4 * s.sweep(160, 70, d) * env(n(d), 0.001, 0.04, 3) + 0.2 * hp(s.noise(d), 2000) * env(n(d), 0.0005, 0.01, 4)
mix(x, n(0.06), s.bell(784.0, 0.35, decay=0.25))
mix(x, n(0.16), s.bell(1174.7, 0.34, decay=0.3))
save("unit_ready", x, 0.5)

d = 0.08  # a unit selected: a short blip
save("select", lp(tone(np.geomspace(1100, 1700, n(d)), "square", 4), 6000) * env(n(d), 0.002, 0.04, 2), 0.35)

save("order", robot_voice([(0.1, 380, 470, 520, 950), (0.14, 520, 400, 480, 1800)]), 0.5)  # "ro-ger!"
save("attack_order", robot_voice([(0.07, 300, 330, 700, 1200), (0.07, 330, 300, 600, 1000),
                                    (0.14, 320, 520, 650, 1700)], grit=0.6), 0.55)  # "at-tack!"

d = 1.0  # a tank engine: exactly 1 s with whole-number frequencies, so the loop meets itself with no click
N = n(d)
tt = np.arange(N) / SR
fire = 30  # firing pulses per second
ph = s.rng.uniform(0, 2 * np.pi, 40)
x = sum(np.sin(2 * np.pi * fire * k * tt + ph[k - 1]) / k ** 1.2 for k in range(1, 41))
pulse = 0.6 + 0.4 * np.sin(2 * np.pi * fire * tt) ** 2
F = np.fft.rfftfreq(N, 1 / SR)
rumble = np.fft.irfft(np.fft.rfft(s.noise(d)) / (1 + (F / 350) ** 4), N)  # circular filter: seamless
rumble /= np.max(np.abs(rumble))
tracks = np.zeros(N)
for k in range(6):  # track links clanking, wrapped around the loop
    c = hp(s.noise(0.03), 1800) * env(n(0.03), 0.0005, 0.008)
    i = np.arange(len(c)) + n(k / 6 + s.rng.uniform(0, 0.02))
    tracks[i % N] += c
wob = 1 + 0.15 * np.sin(2 * np.pi * 4 * tt)
x = (0.5 * x / np.max(np.abs(x)) + 0.6 * rumble * pulse) * wob + 0.25 * tracks
s.save("engine", x, 0.6, fade=False)

d = 3.0  # victory: a brass fanfare over a snare roll
x = np.zeros(n(d))
for st, ln, f in ((0.0, 0.13, 392.0), (0.15, 0.13, 523.3), (0.3, 0.13, 659.3), (0.45, 0.5, 784.0),
                  (1.0, 0.13, 659.3), (1.15, 0.13, 784.0)):
    mix(x, n(st), 0.35 * lp(note(f, ln + 0.1, "saw", 0.015, ln, 1.5), 3200))
for f in (261.6, 329.6, 392.0, 523.3, 1046.5):
    mix(x, n(1.3), 0.22 * lp(note(f, 1.7, "saw", 0.02, 1.2, 1.2, vib=0.005), 3000))
for k in range(20):  # the roll swells into the final chord
    mix(x, n(0.6 + k * 0.035), 0.15 * (0.3 + k / 20) * hp(s.noise(0.05), 1200) * env(n(0.05), 0.0005, 0.02))
mix(x, n(1.3), 0.8 * s.sweep(110, 50, 1.2) * env(n(1.2), 0.002, 0.3, 3) + 0.3 * lp(s.noise(1.2), 6000) * env(n(1.2), 0.001, 0.4, 3))
save("victory", x, 0.65)

d = 3.0  # defeat: a cartoon "wah wah wah waaah" on a muted brass, and a thud
x = np.zeros(n(d))
for st, ln, f, v in ((0.0, 0.42, 392.0, 0), (0.48, 0.42, 370.0, 0), (0.96, 0.42, 349.2, 0), (1.44, 1.5, 329.6, 0.02)):
    tt = t(ln)
    wah = lp(note(f, ln, "saw", 0.03, ln * 0.8, 1.2, vib=v), 400 + 1800 * np.sin(np.pi * np.clip(tt / ln, 0, 1)) ** 0.7)
    mix(x, n(st), 0.4 * wah)
mix(x, n(2.1), 0.9 * s.sweep(80, 30, 0.8) * env(n(0.8), 0.002, 0.2, 3))
save("defeat", x, 0.6)

d = 1.3  # a fort under attack: a two-tone klaxon, three times
x = np.zeros(n(d))
for k in range(3):
    for j, f in enumerate((587.3, 740.0)):
        mix(x, n(k * 0.42 + j * 0.2), lp(tone(np.full(n(0.2), f), "square", 8), 3000) * env(n(0.2), 0.005, 0.15, 1))
save("alarm", np.tanh(1.5 * x), 0.5)
