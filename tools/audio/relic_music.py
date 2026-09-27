#!/usr/bin/env python3
"""Game 19 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own:
a small adventure-serial orchestra lost in a jungle temple. No quotations: nothing from the original game's
music and nothing from any film's adventure march (we avoid their keys, the dotted rising march figure and
the major-key heroic leaps; our tune lives in D minor over a Latin 3-3-2 lilt instead).
- relic_theme: heroic but playful, D minor, 132 bpm. A galloping string ostinato in eighths accented 3-3-2,
  pizzicato bass on the same lilt, timpani on the roots, congas, maracas and claves, a marimba carpet.
  Form: intro 4 (timpani and ostinato, the horns swelling) | A 8 (trumpet tune, horn pads) |
  A' 8 (trumpet and horns in octaves, a trombone counter-line) | B 8 (F major, playful: flute and marimba,
  trumpet answers, pizzicato) | C 8 (bridge: the strings take a long heroic line over Bb C Am Dm, a snare
  roll and timpani build on A7) | A'' 8 (tutti) | tag 4 (brass hits on the 3-3-2, back to the top) = 48 bars (87 s).
- relic_chase: the rolling boulder, D minor, 168 bpm: tremolo strings, a low brass ostinato of repeated D's
  with a flat-sixth sting, timpani on every beat, driving snare and congas, the trumpet shouting fragments
  of the theme's opening figure a step higher each time, chromatic Dm/Eb shifts. 24 bars (34 s).
- relic_tomb: inner temple, mysterious and sparse, D phrygian, 72 bpm. A low string drone (D and A) with a
  slow pad shifting Dm Eb Dm Gm, a soft vibraphone and marimba figure, a breathy flute melody, kalimba drips
  bending up like water falling into a pool, a very soft low timpani and a rattle now and then.
  Form: A 8 (drone, mallets, drips) | B 8 (flute) | C 8 (flute and the strings swelling) = 24 bars (80 s).
Usage: python3 tools/audio/relic_music.py
-> godot/games/relic/audio/music/relic_theme.ogg, relic_chase.ogg, relic_tomb.ogg (+ .mid)."""
import os, re, sys
import random
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop, TPB

OUT = "godot/games/relic/audio/music/"
KICK, STICK, SNARE, CRASH, RIDE, CABASA, MARACAS, CLAVES, HI_WOOD, LO_WOOD = 36, 37, 38, 49, 51, 69, 70, 75, 76, 77
MUTE_CONGA, OPEN_CONGA, LOW_CONGA, HI_BONGO, LO_BONGO, LTOM, HTOM, SUS = 62, 63, 64, 60, 61, 41, 48, 57
TRUMPET, TROMBONE, HORN, BRASS, STRINGS, SLOW_STR, TREM_STR, PIZZ, CONTRABASS, TIMPANI = 56, 57, 60, 61, 48, 49, 44, 45, 43, 47
MARIMBA, VIBES, FLUTE, KALIMBA, GLOCK, CELLO = 12, 11, 73, 108, 9, 42
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
LILT = (0, 1.5, 3)  # the 3-3-2 accents of a bar in eighths


def mel(text):
    """Parses a line like "d5/1.5 a4/.5 r/1" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens
    (after the letter), r is a rest; '|' bar marks are checked and ignored."""
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
    track.note(beat, max(0.05, length - 0.02), pitch, max(1, min(127, int(vel))))


def play(track, start, line, vel, legato=0.9, shift=0, accent=6):
    for beat, length, pitch in line:
        note(track, start + beat, length * legato, pitch + shift, vel + (accent if beat % 1 == 0 else 0))


def split(bar):
    """A bar's chords as (offset, beats, chord): one chord fills the bar, two split it in half."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def bend(track, beat, value):
    v = max(0, min(16383, int(value)))
    track.events.append((int(beat * TPB), bytes([0xE0 | track.ch, v & 0x7F, v >> 7])))


def bend_range(track, semis):
    ch = track.ch
    track.events += [(0, bytes([0xB0 | ch, 101, 0])), (0, bytes([0xB0 | ch, 100, 0])), (0, bytes([0xB0 | ch, 6, semis])),
                     (0, bytes([0xB0 | ch, 38, 0]))]


# chords as (bass root, voicing around middle C)
Dm, Bb, Gm, A7, F, C, Am, Eb, E7, Cm = ((38, [57, 62, 65]), (46, [58, 62, 65]), (43, [58, 62, 67]), (45, [57, 61, 67]),
                                        (41, [57, 60, 65]), (36, [55, 60, 64]), (45, [57, 60, 64]), (39, [55, 58, 63]),
                                        (40, [56, 59, 64]), (36, [55, 60, 63]))


def band():
    drums = Track(9, 0, 104, 64, 30)
    return dict(tpt=Track(0, TRUMPET, 108, 70, 50), horn=Track(1, HORN, 96, 52, 55), tbn=Track(2, TROMBONE, 100, 78, 45),
                ost=Track(3, STRINGS, 92, 44, 45), pad=Track(4, SLOW_STR, 84, 84, 60), bass=Track(5, PIZZ, 110, 60, 30),
                cb=Track(6, CONTRABASS, 90, 60, 35), timp=Track(7, TIMPANI, 112, 58, 50), mar=Track(8, MARIMBA, 96, 36, 45),
                fl=Track(10, FLUTE, 96, 88, 55), glk=Track(11, GLOCK, 76, 92, 60), trem=Track(12, TREM_STR, 88, 40, 50),
                dr=drums)


def parts(t):
    ost, bass, timp, mar, dr, pad, horn = t["ost"], t["bass"], t["timp"], t["mar"], t["dr"], t["pad"], t["horn"]

    def ostinato(b, bar, vel=74, oct_=0):
        """The galloping strings: root, root, fifth / root, root, fifth / sixth-or-octave, fifth, in eighths."""
        for off, ln, (root, v) in split(bar):
            r = root + 12 if root < 48 else root
            r += 12 * oct_
            pat = [r, r, r + 7, r, r, r + 7, r + 12, r + 7]
            for k in range(int(ln * 2)):
                q = off + k * 0.5
                note(ost, b + q, 0.35, pat[int(q * 2) % 8], vel + (14 if q in LILT else 0))

    def pizz(b, bar, vel=90):
        for off, ln, (root, v) in split(bar):
            for q in LILT:
                if off <= q < off + ln:
                    note(bass, b + q, 0.6, root if q != 3 else root + 7 - (12 if root + 7 > 50 else 0), vel)

    def timpani(b, bar, vel=84, roll=False):
        root = bar[0][0]
        tr = root if root < 45 else root - 12
        note(timp, b, 0.9, tr, vel)
        if len(bar) > 1:
            note(timp, b + 2, 0.9, bar[1][0] if bar[1][0] < 45 else bar[1][0] - 12, vel - 6)
        if roll:
            for k in range(8):
                note(timp, b + 2 + k * 0.25, 0.25, 45 if bar[-1][0] % 12 == 9 else tr, vel - 20 + 4 * k)

    def carpet(b, bar, vel=60):
        """Marimba sixteenths up and down the chord, soft, on the 3-3-2."""
        for off, ln, (root, v) in split(bar):
            tones = [p + 12 for p in v] + [v[0] + 24]
            for k in range(int(ln * 2)):
                q = off + k * 0.5
                note(mar, b + q, 0.4, tones[(k * 3 + (k // 3)) % 4], vel + (10 if q in LILT else 0))

    def pads(b, bar, track=None, vel=62, shift=0):
        track = track or pad
        for off, ln, (root, v) in split(bar):
            for p in v:
                note(track, b + off, ln, p + shift, vel)

    def perc(b, vel=70, busy=False, fill=False, snare_roll=False):
        """Jungle percussion: congas on a tumbao-ish figure, maracas in eighths, claves on the 3-3-2, a kick."""
        for k in range(8):
            q = k * 0.5
            note(dr, b + q, 0.2, MARACAS, vel - 22 + (8 if k % 2 else 0))
        for q in LILT:
            note(dr, b + q, 0.2, CLAVES, vel - 18)
        for q, p, dv in ((0, MUTE_CONGA, -8), (1, MUTE_CONGA, -14), (1.5, OPEN_CONGA, 0), (2.5, LOW_CONGA, -4),
                         (3, OPEN_CONGA, -2), (3.5, LOW_CONGA, -6)):
            note(dr, b + q, 0.2, p, vel + dv)
        note(dr, b, 0.3, KICK, vel)
        note(dr, b + 1.5, 0.3, KICK, vel - 12)
        if busy:
            for q in (0.5, 2, 2.75):
                note(dr, b + q, 0.1, HI_BONGO if q != 2 else LO_BONGO, vel - 16)
        if fill:
            for k, p in enumerate((HI_BONGO, HI_BONGO, LO_BONGO, OPEN_CONGA, OPEN_CONGA, LOW_CONGA, LTOM, LTOM)):
                note(dr, b + 2 + k * 0.25, 0.1, p, vel - 10 + 3 * k)
        if snare_roll:
            for k in range(16):
                note(dr, b + k * 0.25, 0.1, SNARE, 40 + 3 * k)

    return ostinato, pizz, timpani, carpet, pads, perc


# ---------------------------------------------------------------------------------------------------------------
INTRO = [[Dm], [Dm], [Dm], [A7]]
A_PROG = [[Dm], [Bb], [Gm], [A7], [Dm], [F], [Gm, A7], [Dm]]
B_PROG = [[F], [C], [Dm], [Bb], [F], [C], [Bb, C], [F]]
C_PROG = [[Bb], [C], [Am], [Dm], [Bb], [C], [A7], [A7]]
TAG = [[Dm], [Dm], [Bb, C], [A7]]

TUNE_A = mel("d5/1.5 a4/.5 d5/.5 e5/.5 f5/1 | bb5/1.5 a5/.5 g5/.5 f5/.5 d5/1 | g5/.5 a5/.5 bb5/.5 g5/.5 d6/1.5 c6/.5 | "
             "a5/3 r/.5 a4/.5 | d5/1.5 a4/.5 d5/.5 e5/.5 f5/1 | c6/1.5 a5/.5 f5/.5 g5/.5 a5/1 | "
             "bb5/.5 a5/.5 g5/.5 f5/.5 e5/.5 f5/.5 g5/.5 c#6/.5 | d6/3 r/1")
COUNTER_A = mel("d3/2 f3/2 | f3/2 d3/2 | g3/2 bb3/2 | a3/2 c#3/2 | d3/2 a3/2 | a3/2 c4/2 | bb3/2 a3/2 | d3/3 r/1")
TUNE_B = mel("c6/.5 a5/.5 f5/.5 a5/.5 c6/1 f6/1 | e6/.5 d6/.5 c6/.5 g5/.5 e5/1 g5/1 | "
             "f5/.5 a5/.5 d6/.5 a5/.5 f6/1 e6/.5 d6/.5 | d6/1 bb5/1 f5/1 r/1 | c6/.5 a5/.5 f5/.5 a5/.5 c6/1 f6/1 | "
             "g6/.5 f6/.5 e6/.5 d6/.5 c6/1 bb5/1 | a5/.5 bb5/.5 d6/.5 f6/.5 e6/.5 d6/.5 c6/.5 bb5/.5 | a5/2 f5/1 r/1")
ANSWER_B = mel("r/4 | r/4 | r/4 | r/3 f4/.5 a4/.5 | r/4 | r/4 | r/4 | r/2 c5/.5 c5/.5 f5/1")
TUNE_C = mel("d5/2 f5/1 bb5/1 | c6/2 g5/1 e5/1 | a5/2 c6/1 e6/1 | d6/3 a5/1 | bb5/1.5 a5/.5 bb5/1 d6/1 | "
             "c6/1.5 bb5/.5 c6/1 e6/1 | e6/1 c#6/1 a5/1 e5/1 | g5/.5 a5/.5 bb5/.5 c#6/.5 e6/1 r/1")
TAG_HITS = mel("d5/.5 r/1 d5/.5 r/1 d5/.5 r/.5 | f5/.5 r/1 e5/.5 r/1 d5/.5 r/.5 | f5/.5 r/1 f5/.5 r/.5 g5/.5 r/.5 g5/.5 | "
               "a5/.5 r/1 a5/.5 r/1 c#5/.5 e5/.5")


def theme():
    t = band()
    tpt, horn, tbn, fl, mar, glk, cb, ost = t["tpt"], t["horn"], t["tbn"], t["fl"], t["mar"], t["glk"], t["cb"], t["ost"]
    ostinato, pizz, timpani, carpet, pads, perc = parts(t)

    for i, ch in enumerate(INTRO):  # the ostinato and timpani alone, percussion creeps in, horns swell
        b = i * 4
        ostinato(b, ch, 66 + 4 * i)
        timpani(b, ch, 80, roll=i == 3)
        if i >= 1:
            perc(b, 56 + 4 * i, fill=i == 3)
        if i >= 2:
            pizz(b, ch, 84)
            pads(b, ch, horn, 50 + 10 * (i - 2))
    bar = 4

    def section(prog, lead, lead_vel, horn_oct=False, counter=False, busy=False, last_fill=True):
        nonlocal bar
        for i, ch in enumerate(prog):
            b = (bar + i) * 4
            ostinato(b, ch, 74)
            pizz(b, ch)
            timpani(b, ch, 86, roll=last_fill and i == 7)
            carpet(b, ch, 50 if not busy else 58)
            pads(b, ch, None, 58)
            if not horn_oct:
                pads(b, ch, horn, 56)
            perc(b, 72, busy=busy, fill=last_fill and i == 7)
            note(cb, b, 3.8, ch[0][0] - 12 if ch[0][0] >= 40 else ch[0][0], 70)
        play(tpt, bar * 4, lead, lead_vel)
        if horn_oct:
            play(horn, bar * 4, lead, lead_vel - 10, 0.9, -12)
        if counter:
            play(tbn, bar * 4, COUNTER_A, 84, 0.95)
        bar += 8

    section(A_PROG, TUNE_A, 96)
    section(A_PROG, TUNE_A, 102, horn_oct=True, counter=True, busy=True)

    for i, ch in enumerate(B_PROG):  # B: F major, playful: flute and marimba lead, lighter strings, trumpet answers
        b = (bar + i) * 4
        pizz(b, ch, 84)
        pads(b, ch, None, 50)
        timpani(b, ch, 70)
        perc(b, 66, busy=True, fill=i == 7)
        root, v = ch[0]
        for q in (1, 3):  # off-beat string stabs instead of the gallop
            for p in v:
                note(ost, b + q, 0.3, p, 66)
    play(t["fl"], bar * 4, TUNE_B, 92)
    play(mar, bar * 4, TUNE_B, 82, 0.6, -12)
    play(glk, bar * 4, [n_ for n_ in TUNE_B if n_[0] % 8 == 0], 56, 0.5)
    play(tpt, bar * 4, ANSWER_B, 88, 0.7)
    bar += 8

    for i, ch in enumerate(C_PROG):  # C: the strings take the long heroic line; snare roll and timpani on A7
        b = (bar + i) * 4
        ostinato(b, ch, 70 + 2 * i)
        pizz(b, ch, 88)
        timpani(b, ch, 84 + 2 * i, roll=i >= 6)
        pads(b, ch, horn, 60 + 2 * i)
        perc(b, 70, fill=i == 7, snare_roll=i == 7)
        note(cb, b, 3.8, ch[0][0] - 12 if ch[0][0] >= 40 else ch[0][0], 76)
    play(t["pad"], bar * 4, TUNE_C, 96, 1.0)
    play(t["pad"], bar * 4, TUNE_C, 84, 1.0, -12)
    play(tbn, bar * 4, [(b_, ln, p - 24) for b_, ln, p in TUNE_C if b_ >= 24], 80)  # the low brass joins at the end
    note(t["dr"], (bar + 7) * 4 + 3.5, 0.5, CRASH, 90)
    bar += 8

    section(A_PROG, TUNE_A, 108, horn_oct=True, counter=True, busy=True, last_fill=False)  # A'': tutti
    play(glk, (bar - 8) * 4, [n_ for n_ in TUNE_A if n_[0] % 4 == 0], 62, 0.5)
    note(t["dr"], (bar - 8) * 4, 1, CRASH, 96)

    for i, ch in enumerate(TAG):  # tag: brass hits on the 3-3-2, the gallop carries on back into the intro
        b = (bar + i) * 4
        ostinato(b, ch, 72)
        pizz(b, ch, 90)
        timpani(b, ch, 88, roll=i == 3)
        perc(b, 70, fill=i == 3)
    play(tpt, bar * 4, TAG_HITS, 96, 0.8)
    play(horn, bar * 4, TAG_HITS, 88, 0.8, -12)
    play(tbn, bar * 4, TAG_HITS, 84, 0.8, -24)
    bar += 4
    assert bar == 48
    return list(t.values()), 132, bar


# ---------------------------------------------------------------------------------------------------------------
CHASE_1 = [[Dm], [Eb], [Dm], [Eb], [Bb], [C], [A7], [A7]]
CHASE_2 = [[Gm], [A7], [Dm], [Bb], [Gm], [Eb], [A7], [A7]]
# the trumpet shouts the theme's opening figure, a step higher each time
SHOUT_1 = mel("d5/1.5 a4/.5 d5/.5 e5/.5 f5/1 | eb5/1.5 bb4/.5 eb5/.5 f5/.5 g5/1 | d5/1.5 a4/.5 d5/.5 e5/.5 f5/1 | "
              "g5/1.5 eb5/.5 g5/.5 a5/.5 bb5/1 | f5/.5 bb5/.5 d6/1 c6/.5 bb5/.5 a5/1 | g5/.5 c6/.5 e6/1 d6/.5 c6/.5 bb5/1 | "
              "a5/2 c#6/2 | e6/1 c#6/.5 a5/.5 g5/.5 e5/.5 c#5/1")
SHOUT_2 = mel("g5/1.5 d5/.5 g5/.5 a5/.5 bb5/1 | a5/1.5 e5/.5 a5/.5 bb5/.5 c#6/1 | d6/1.5 a5/.5 d6/.5 e6/.5 f6/1 | "
              "d6/2 bb5/2 | bb5/1.5 g5/.5 d5/1 g5/1 | bb5/1.5 g5/.5 eb5/1 g5/1 | a5/1 bb5/1 c#6/1 e6/1 | a5/4")


def chase():
    t = band()
    tpt, horn, tbn, trem, timp, cb, dr, ost = t["tpt"], t["horn"], t["tbn"], t["trem"], t["timp"], t["cb"], t["dr"], t["ost"]
    ostinato, pizz, timpani, carpet, pads, perc = parts(t)

    def drive(b, ch, vel, fill=False):
        root, v = ch[0]
        low = root if root < 45 else root - 12
        for q in range(4):  # timpani on every beat, the root and its fifth
            note(timp, b + q, 0.5, low if q % 2 == 0 else (low + 7 if low + 7 <= 45 else low - 5), vel - (0 if q == 0 else 10))
        for k in range(8):  # low brass: repeated roots in eighths, a flat-sixth sting at the end of the bar
            p = low + 12 if k < 7 else low + 20
            note(tbn, b + k * 0.5, 0.3, p, vel - 6 + (12 if k * 0.5 in LILT else 0))
        for p in v:  # tremolo strings, the whole bar
            note(trem, b, 3.9, p, vel - 20)
            note(trem, b, 3.9, p + 12, vel - 26)
        ostinato(b, ch, vel - 8, oct_=1)
        note(cb, b, 3.8, low, vel - 10)
        for k in range(8):  # a driving snare on the eighths, accents on 2 and 4
            note(dr, b + k * 0.5, 0.1, SNARE, vel - 30 + (26 if k in (2, 6) else 0))
        perc(b, vel - 6, busy=True, fill=fill)

    for i, ch in enumerate(CHASE_1):
        drive(i * 4, ch, 96, fill=i == 7)
    play(tpt, 0, SHOUT_1, 104, 0.85)
    play(horn, 0, SHOUT_1, 88, 0.9, -12)
    for i, ch in enumerate(CHASE_2):
        drive((8 + i) * 4, ch, 100, fill=i == 7)
    play(tpt, 32, SHOUT_2, 106, 0.85)
    play(horn, 32, SHOUT_2, 90, 0.9, -12)
    note(dr, 32, 1, CRASH, 100)
    for i, ch in enumerate(CHASE_1):  # again, the tune up an octave in the flute and glockenspiel too
        drive((16 + i) * 4, ch, 104, fill=i == 7)
    play(tpt, 64, SHOUT_1, 110, 0.85)
    play(horn, 64, SHOUT_1, 94, 0.9, -12)
    play(t["fl"], 64, SHOUT_1, 84, 0.85, 12)
    play(t["glk"], 64, [n_ for n_ in SHOUT_1 if n_[0] % 2 == 0], 58, 0.5)
    note(dr, 64, 1, CRASH, 104)
    return list(t.values()), 168, 24


# ---------------------------------------------------------------------------------------------------------------
TOMB_PROG = [Dm, Eb, Dm, Gm, Dm, Eb, Cm, Dm]
FLUTE_B = mel("r/2 a4/1 bb4/1 | a4/3 r/1 | r/1 f4/.5 g4/.5 a4/1 d5/1 | c5/2 bb4/1 a4/1 | r/2 d5/1 eb5/1 | "
              "d5/2 c5/1 bb4/1 | a4/1 g4/1 bb4/1 a4/1 | d4/3 r/1")
FLUTE_C = mel("r/1 d5/1 f5/1 a5/1 | bb5/2 a5/1 g5/1 | a5/3 r/1 | r/1 g5/.5 f5/.5 d5/1 bb4/1 | r/1 a4/1 d5/1 f5/1 | "
              "eb5/2 d5/1 bb4/1 | c5/1.5 bb4/.5 a4/1 g4/1 | a4/4")


def tomb():
    rng = random.Random(1989)
    t = band()
    fl, mar, glk, timp, cb, pad, dr = t["fl"], t["mar"], t["glk"], t["timp"], t["cb"], t["pad"], t["dr"]
    cello = Track(13, CELLO, 92, 50, 60)
    vib = Track(14, VIBES, 80, 76, 70)
    drip = Track(15, KALIMBA, 76, 96, 90)
    bend_range(drip, 12)
    fig = mel("d5/1 a4/1 eb5/1 a4/1")

    for i in range(24):
        b = i * 4
        root, v = TOMB_PROG[i % 8]
        note(cb, b, 4.0, 38 if i % 2 == 0 else 38, 62)  # the drone: D low, with A above in the cellos
        note(cello, b, 4.0, 45 if i % 4 != 3 else 46, 54 + (8 if i >= 16 else 0))
        swell = 44 + (16 if 16 <= i < 22 else 8 if i >= 22 else 0) + (6 if i % 8 in (3, 4) else 0)  # eases back at the end
        for p in v:
            note(pad, b, 4.0, p, swell if i >= 4 else 36 + 2 * i)
        for q, (_, ln, p) in enumerate(fig):  # the vibraphone figure, its third note following the chord
            pp = p if q != 2 else v[-1] + 12
            if i % 2 == 0 or q < 2:
                note(vib, b + q, 1.0, pp, 46 + (6 if q == 0 else 0))
        if i % 4 == 2:
            for k, p in enumerate((v[0], v[1], v[2], v[0] + 12)):
                note(mar, b + 2 + k * 0.25, 0.3, p + 12, 42 + 4 * k)
        if i % 4 == 0:
            note(timp, b, 1.5, 38, 44 + (12 if i % 8 == 0 else 0))
        if i % 8 == 7:
            note(timp, b + 3, 0.5, 45, 40)
        if i % 4 == 1:
            note(dr, b + 2.5, 0.5, CABASA, 30)
            note(dr, b + 3, 0.5, MARACAS, 26)
        for k in range(rng.choice((1, 2, 2, 3))):  # drips: a high kalimba plink bending up, like a drop
            q = rng.choice((0.5, 1.25, 1.75, 2.5, 3.25, 3.5))
            p = rng.choice((86, 89, 93, 94, 98))
            bend(drip, b + q, 8192)
            for s_ in range(1, 7):
                bend(drip, b + q + 0.03 * s_, 8192 + 8191 * 0.25 * s_ / 6)
            note(drip, b + q, 0.25, p, rng.randint(36, 58))
            bend(drip, b + q + 0.3, 8192)
        if i in (0, 12):
            note(glk, b + 1.5, 1, 86, 34)
    play(fl, 32, FLUTE_B, 74, 0.95)
    play(fl, 64, FLUTE_C, 80, 0.95)
    play(cello, 64, [(b_, ln, p - 12) for b_, ln, p in FLUTE_C if ln >= 1], 50, 1.0)  # the cellos shadow it low
    return list(t.values()) + [cello, vib, drip], 72, 24


for name, song in (("relic_theme", theme), ("relic_chase", chase), ("relic_tomb", tomb)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
