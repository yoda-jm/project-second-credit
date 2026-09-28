#!/usr/bin/env python3
"""Game 23 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own: a
bright globe-trotting band for a traveller popping balloons in front of postcard landmarks. No quotations: nothing
from the arcade game's music, no folk or classical tune, no existing video-game or film theme. The melody travels:
a dotted climb up the tonic chord, a step back down, a leap to the next horizon.
- popvoyage_theme: D major, 132 bpm, straight eighths. An acoustic bass (root and fifth), a strummed nylon guitar,
  offbeat accordion chords, a light kit with tambourine and claves. Form: intro 4 (guitar and marimba ostinato,
  a timpani swell) | A 8 (accordion lead, glockenspiel an octave up) | A' 8 (trumpet lead, brass stabs, strings
  pad) | B 8 (strings and flute sing a longer line over G, A, F#m, Bm) | C 8 (a breakdown in B minor: marimba
  arpeggios, congas, xylophone and accordion on a darker tune, the F sharp major turn) | A'' 8 (tutti) = 44 bars
  (80.0 s).
- popvoyage_hurry: the last 15 seconds, 168 bpm, up a tone to E major: the A tune on trumpet and xylophone over
  driving bass eighths and sixteenth hats, then a chase in C sharp minor (marimba eighths, brass stabs, timpani).
  16 bars (22.9 s).
Usage: python3 tools/audio/popvoyage_music.py
-> godot/games/popvoyage/audio/music/popvoyage_theme.ogg, popvoyage_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/popvoyage/audio/music/"
KICK, SNARE, CLAP, CLOSED, OPEN_HAT, CRASH, TAMB, HI_CONGA, OPEN_CONGA, LO_CONGA, CLAVES, TRIANGLE = \
    36, 38, 39, 42, 46, 49, 54, 62, 63, 64, 75, 81
GLOCK, MARIMBA, XYLO, ACCORDION, NYLON, BASS, STRINGS, PIZZ, TIMPANI, TRUMPET, BRASS, FLUTE = \
    9, 12, 13, 21, 24, 32, 48, 45, 47, 56, 61, 73
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SHIFT = [0]  # a transposition for every pitched note (the hurry is up a tone)


def mel(text):
    """Parses a line like "c5/.5 f#5/1 r/.5" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens (after the
    letter), r is a rest; '|' bar marks are checked and ignored."""
    out, beat = [], 0.0
    for tok in text.split():
        if tok == "|":
            assert abs(beat % 4) < 1e-6, f"a bar of {beat % 4} beats before '|' in: {text}"
            continue
        p, ln = tok.split("/")
        ln = float(ln)
        if p != "r":
            m = re.fullmatch(r"([a-g])([#b]?)(-?\d)", p)
            out.append((beat, ln, 12 * (int(m.group(3)) + 1) + NOTE[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)]))
        beat += ln
    assert abs(beat % 4) < 1e-6, f"a last bar of {beat % 4} beats in: {text}"
    return out


def note(track, beat, length, pitch, vel):
    if track.ch != 9:
        pitch += SHIFT[0]
    track.note(beat, max(0.05, length - 0.02), pitch, max(1, min(127, int(vel))))


def play(track, start, line, vel, legato=0.9, shift=0, accent=6):
    for beat, length, pitch in line:
        note(track, start + beat, length * legato, pitch + shift, vel + (accent if beat % 1 == 0 else 0))


def split(bar):
    """A bar's chords as (offset, beats, chord): one chord fills the bar, two split it in half."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    drums = Track(9, 0, 96, 64, 25)
    drums.events.append((0, bytes([0xC9, 0])))
    return dict(bass=Track(0, BASS, 112, 64, 20), acc=Track(1, ACCORDION, 88, 50, 40), tpt=Track(2, TRUMPET, 96, 74, 50),
                brass=Track(3, BRASS, 78, 60, 45), strings=Track(4, STRINGS, 74, 70, 60),
                flute=Track(5, FLUTE, 86, 80, 55), mar=Track(6, MARIMBA, 92, 44, 40), gtr=Track(7, NYLON, 84, 36, 35),
                glock=Track(8, GLOCK, 66, 88, 55), pizz=Track(10, PIZZ, 80, 90, 35), xylo=Track(11, XYLO, 78, 84, 40),
                timp=Track(12, TIMPANI, 90, 64, 40), dr=drums)


# chords as (bass root, voicing around middle C), D major
D, A, Bm, G, Em, Fsm, Fs = ((38, [57, 62, 66]), (45, [57, 61, 64]), (47, [59, 62, 66]), (43, [55, 59, 62]),
                            (40, [55, 59, 64]), (42, [57, 61, 66]), (42, [58, 61, 66]))
INTRO = [[D], [G], [Em], [A]]
A_PROG = [[D], [A], [Bm], [G], [D], [Em, A], [Bm, G], [A]]
B_PROG = [[G], [A], [Fsm], [Bm], [Em], [A], [D, Bm], [Em, A]]
C_PROG = [[Bm], [Bm], [G], [G], [Em], [Em], [Fs], [Fs]]
CHASE_PROG = [[Bm], [A], [G], [Fs], [Bm], [A], [Em], [Fs]]

TUNE_A = mel("a4/.5 d5/.5 f#5/.75 e5/.25 d5/.5 f#5/.5 a5/1 | g5/.5 f#5/.5 e5/.5 c#5/.5 e5/2 | "
             "f#5/.5 b5/.5 a5/.5 f#5/.5 d5/.75 e5/.25 f#5/1 | g5/1.5 f#5/.5 e5/1 r/1 | "
             "a4/.5 d5/.5 f#5/.75 e5/.25 d5/.5 a5/.5 d6/1 | b5/.5 a5/.5 g5/.5 e5/.5 a5/.5 g5/.5 e5/.5 c#5/.5 | "
             "d5/.5 f#5/.5 b5/1 g5/.5 b5/.5 d6/1 | c#6/.75 b5/.25 a5/.5 e5/.5 a5/1 r/1")
TUNE_B = mel("b5/2 a5/1 g5/1 | e5/2 c#5/1 a4/1 | c#5/1.5 f#5/.5 a5/2 | f#5/3 r/1 | "
             "g5/1.5 b5/.5 e6/2 | c#6/1 b5/1 a5/1 e5/1 | f#5/1 a5/1 d6/1 b5/1 | e5/1 g5/1 c#6/1.5 r/.5")
TUNE_C = mel("f#5/1.5 e5/.5 d5/.5 c#5/.5 b4/1 | d5/.5 e5/.5 f#5/.5 g5/.5 f#5/2 | g5/1.5 f#5/.5 e5/.5 d5/.5 b4/1 | "
             "d5/1 g5/1 b5/2 | e5/1.5 f#5/.5 g5/.5 f#5/.5 e5/1 | b5/1 g5/1 e5/2 | "
             "a#4/.5 c#5/.5 e5/.5 f#5/.5 a#5/1 c#6/1 | f#5/1 a#5/1 c#6/.5 e6/.5 f#6/1")
INTRO_OST = mel("d5/.5 a4/.5 f#5/.5 a4/.5 d5/.5 a4/.5 f#5/.5 a5/.5 | d5/.5 b4/.5 g5/.5 b4/.5 d5/.5 b4/.5 g5/.5 b5/.5 | "
                "e5/.5 b4/.5 g5/.5 b4/.5 e5/.5 b4/.5 g5/.5 b5/.5 | e5/.5 c#5/.5 a5/.5 c#5/.5 e5/.5 g5/.5 a5/1")
CHASE = mel("b4/.5 d5/.5 f#5/.5 d5/.5 b5/.5 f#5/.5 d5/.5 f#5/.5 | a4/.5 c#5/.5 e5/.5 c#5/.5 a5/.5 e5/.5 c#5/.5 e5/.5 | "
            "g4/.5 b4/.5 d5/.5 b4/.5 g5/.5 d5/.5 b4/.5 d5/.5 | f#4/.5 a#4/.5 c#5/.5 a#4/.5 f#5/.5 c#5/.5 a#4/.5 c#5/.5 | "
            "b4/.5 d5/.5 f#5/.5 d5/.5 b5/.5 f#5/.5 d5/.5 f#5/.5 | a4/.5 c#5/.5 e5/.5 c#5/.5 a5/.5 e5/.5 c#5/.5 e5/.5 | "
            "e5/.5 g5/.5 b5/.5 g5/.5 e6/.5 b5/.5 g5/.5 b5/.5 | f#5/.5 a#5/.5 c#6/.5 e6/.5 f#6/1 r/1")


def parts(t):
    bass, gtr, acc, dr = t["bass"], t["gtr"], t["acc"], t["dr"]

    def walk(b, bar, vel=100, drive=False):
        """The bass: root on 1, the fifth on 3 with a pickup; with drive, eighths on the root (the hurry)."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root >= 45 else root
            if drive:
                for k in range(int(ln * 2)):
                    note(bass, b + off + k * 0.5, 0.35, lo + (12 if k % 4 == 3 else 0), vel - (0 if k % 2 == 0 else 12))
                continue
            pat = [(0, lo, 1.3), (1.5, lo + 7, 0.4), (2, lo + 7, 1.3), (3.5, lo + 12, 0.4)]
            for q, p, L in pat:
                if q < ln:
                    note(bass, b + off + q, min(L, ln - q), p, vel - (0 if q % 2 == 0 else 14))

    def strum(b, bar, vel=64):
        """The nylon guitar: down on 1, up on 1&, down-up on 2& .. 3, up on 4&; each chord rolled."""
        for off, ln, (root, v) in split(bar):
            for q, down, accent in ((0, True, 8), (1.5, False, 0), (2, True, 4), (2.5, False, 0), (3.5, False, 0)):
                if q >= ln:
                    continue
                vs = v + [v[0] + 12]
                order = vs if down else vs[::-1]
                for k, p in enumerate(order):
                    note(gtr, b + off + q + k * 0.012, 0.4, p, vel + accent - 3 * k)

    def squeeze(b, bar, vel=58):
        """Offbeat accordion chords, short and bouncy."""
        for off, ln, (root, v) in split(bar):
            for q in (0.5, 1.5, 2.5, 3.5):
                if q < ln:
                    for p in v:
                        note(acc, b + off + q, 0.3, p + 12, vel - (6 if q in (1.5, 3.5) else 0))

    def kit(b, vel=64, busy=False, fill=False, latin=False):
        for q in (0, 2) if not busy else (0, 1.5, 2, 2.75):
            note(dr, b + q, 0.2, KICK, vel + 6)
        for q in (1, 3):
            note(dr, b + q, 0.2, SNARE, vel - 6)
        for k in range(16 if busy else 8):
            st = k * (0.25 if busy else 0.5)
            note(dr, b + st, 0.1, CLOSED, vel - 20 + (10 if st % 1 == 0.5 else 0))
        note(dr, b + 1, 0.1, TAMB, vel - 14)
        note(dr, b + 3, 0.1, TAMB, vel - 14)
        if latin:  # claves in a 3-2 son figure, congas
            for q in (0, 0.75, 1.5, 2.5, 3):
                note(dr, b + q, 0.1, CLAVES, vel - 10)
            for q, dd in ((0.5, HI_CONGA), (1, OPEN_CONGA), (2.5, HI_CONGA), (3, LO_CONGA), (3.5, OPEN_CONGA)):
                note(dr, b + q, 0.1, dd, vel - 8)
        if fill:
            for k, dd in enumerate((HI_CONGA, OPEN_CONGA, LO_CONGA, LO_CONGA)):
                note(dr, b + 3 + k * 0.25, 0.1, dd, vel + 3 * k)

    return walk, strum, squeeze, kit


def theme():
    SHIFT[0] = 0
    t = band()
    bass, acc, tpt, brass, strings, flute, mar, gtr, glock, pizz, xylo, timp, dr = (t[k] for k in (
        "bass", "acc", "tpt", "brass", "strings", "flute", "mar", "gtr", "glock", "pizz", "xylo", "timp", "dr"))
    walk, strum, squeeze, kit = parts(t)

    def accomp(start, prog, vel=100, busy=False, acc_vel=58, pad=False, stabs=False):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            walk(b, ch, vel)
            strum(b, ch, vel - 36)
            squeeze(b, ch, acc_vel)
            kit(b, vel - 38, busy, fill=i == len(prog) - 1)
            for off, ln, (root, v) in split(ch):
                if pad:
                    for p in v:
                        note(strings, b + off, ln, p, 58)
                if stabs:
                    for q in (1.5, 3.5):
                        if q < ln:
                            for p in v:
                                note(brass, b + off + q, 0.3, p, 74)

    # intro: guitar and marimba ostinato, the kit falls in at bar 3, a timpani swell into the tune
    play(mar, 0, INTRO_OST, 84, 0.8)
    for i, ch in enumerate(INTRO):
        b = i * 4
        walk(b, ch, 86 + 3 * i)
        strum(b, ch, 58 + 2 * i)
        if i >= 2:
            kit(b, 54, fill=i == 3)
    for k in range(8):
        note(timp, 14 + k * 0.25, 0.25, 45, 50 + 6 * k)
    for k, p in enumerate((69, 74, 78, 81)):
        note(glock, 14 + k * 0.5, 0.4, p + 12, 60 + 6 * k)
    bar = 4

    accomp(bar, A_PROG)  # A: accordion lead, glockenspiel an octave up
    play(acc, bar * 4, TUNE_A, 100, 0.85)
    play(glock, bar * 4, TUNE_A, 52, 0.5, 12)
    note(dr, bar * 4, 0.5, CRASH, 52)
    bar += 8

    accomp(bar, A_PROG, 100, busy=True, acc_vel=48, pad=True, stabs=True)  # A': the trumpet, brass stabs, a pad
    play(tpt, bar * 4, TUNE_A, 98, 0.85)
    note(dr, bar * 4, 0.5, CRASH, 58)
    bar += 8

    accomp(bar, B_PROG, 94, acc_vel=46)  # B: strings and flute sing, the marimba answers in broken chords
    play(strings, bar * 4, TUNE_B, 92, 1.0)
    play(flute, bar * 4, TUNE_B, 78, 0.95, 12)
    for i, ch in enumerate(B_PROG):
        for off, ln, (root, v) in split(ch):
            b = (bar + i) * 4 + off
            arp = [v[0], v[1], v[2], v[1] + 12] if ln == 4 else [v[0], v[2]]
            for k, p in enumerate(arp):
                note(mar, b + 2 + k * 0.5 if ln == 4 else b + 1 + k * 0.5, 0.4, p + 12, 70 + 3 * k)
    bar += 8

    for i, ch in enumerate(C_PROG):  # C: the breakdown in B minor, marimba arpeggios, congas, a darker tune
        b = (bar + i) * 4
        walk(b, ch, 92)
        kit(b, 56, latin=True, fill=i == 7)
        root, v = ch[0]
        arp = [v[0], v[1], v[2], v[0] + 12, v[1] + 12, v[2], v[1], v[0] + 12]
        for k, p in enumerate(arp):
            note(mar, b + k * 0.5, 0.45, p + 12, 74 + (10 if k % 4 == 0 else 0))
        for q in (1, 3):
            for p in v:
                note(pizz, b + q, 0.3, p, 62)
        if i >= 6:
            for k in range(8):
                note(timp, b + k * 0.5, 0.3, root + 12 if root < 43 else root, 60 + 4 * k)
    play(xylo, bar * 4, TUNE_C, 88, 0.8)
    play(acc, bar * 4, TUNE_C, 70, 0.9, -12)
    note(dr, bar * 4 + 28, 4, TRIANGLE, 44)
    bar += 8

    accomp(bar, A_PROG, 104, busy=True, acc_vel=52, pad=True, stabs=True)  # A'': tutti
    play(tpt, bar * 4, TUNE_A, 100, 0.85)
    play(acc, bar * 4, TUNE_A, 86, 0.85, -12)
    play(glock, bar * 4, TUNE_A, 54, 0.5, 12)
    play(flute, bar * 4, TUNE_A, 64, 0.8, 12)
    note(dr, bar * 4, 0.5, CRASH, 62)
    bar += 8
    assert bar == 44
    return list(t.values()), 132, bar


def hurry():
    SHIFT[0] = 2
    t = band()
    tpt, xylo, mar, brass, timp, dr = (t[k] for k in ("tpt", "xylo", "mar", "brass", "timp", "dr"))
    walk, strum, squeeze, kit = parts(t)
    for i, ch in enumerate(A_PROG):  # A: the tune pushed, driving bass eighths, sixteenth hats
        b = i * 4
        walk(b, ch, 100, drive=True)
        squeeze(b, ch, 60)
        kit(b, 66, busy=True, fill=i == 7)
    play(tpt, 0, TUNE_A, 100, 0.8)
    play(xylo, 0, TUNE_A, 76, 0.5, 12)
    note(dr, 0, 0.5, CRASH, 64)
    for i, ch in enumerate(CHASE_PROG):  # the chase in the relative minor
        b = (8 + i) * 4
        walk(b, ch, 104, drive=True)
        kit(b, 68, busy=True, latin=True, fill=i == 7)
        root, v = ch[0]
        for q in (0, 1.5, 3):
            for p in v:
                note(brass, b + q, 0.3, p, 80 + (8 if q == 0 else 0))
        for k in range(4):
            note(timp, b + k, 0.3, root + 12 if root < 43 else root, 62 + (12 if k == 0 else 0))
    play(mar, 32, CHASE, 100, 0.8)
    play(tpt, 32, [(b, ln, p) for b, ln, p in CHASE if b % 1 == 0], 78, 0.9, -12)
    note(dr, 32, 0.5, CRASH, 70)
    return list(t.values()), 168, 16


for name, song in (("popvoyage_theme", theme), ("popvoyage_hurry", hurry)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
