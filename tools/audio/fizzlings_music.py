#!/usr/bin/env python3
"""Game 18 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own:
a little underwater toybox band. No quotations: nothing from the arcade game's music (its famous theme above
all: we avoid its key, its tempo feel and its rising scale figures) nor from any nursery or classical tune.
- fizzlings_theme: bouncy and cheerful, E flat major, 126 bpm, straight eighths with a calypso-ish 3-3-2 lilt
  in the tuba. Oom-pah sousaphone, a marimba arpeggio carpet, a clarinet tune, glockenspiel glints, a square
  "toy synth" blowing bubbles (short notes bent upwards, like a bubble forming), light kit with shaker and
  side stick. Form: intro 4 | A 8 (clarinet) | A' 8 (marimba and glockenspiel lead, low clarinet counter) |
  B 8 (clarinet and toy synth in A flat colours) | A'' 8 (tutti) | turn 4 in C minor (76 s).
- fizzlings_hurry: the same band when time runs short, 164 bpm, up a tone to F major: the A tune doubled by
  the glockenspiel, an eighth-note chase in D minor on marimba and clarinet over a driving tuba, the tune again
  with bubbles on every bar. 24 bars (35 s).
- fizzlings_boss: a boss stage, C minor, 150 bpm: a stomping tuba ostinato in eighths, timpani, a sixteenth
  marimba ostinato, clarinet and muted trumpet in octaves, orchestra-hit stabs, toms and a snare backbeat.
  Form: intro 4 | A 8 (clarinet) | B 8 (trumpet call over A flat, B flat, D flat) | A' 8 (tutti, glockenspiel
  doubling) = 28 bars (45 s).
Usage: python3 tools/audio/fizzlings_music.py
-> godot/games/fizzlings/audio/music/fizzlings_theme.ogg, fizzlings_hurry.ogg, fizzlings_boss.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop, TPB

OUT = "godot/games/fizzlings/audio/music/"
KICK, STICK, SNARE, CLAP, CLOSED, OPEN, CRASH, RIDE, TRI, SHAKER, CABASA, LTOM, MTOM, HTOM, TAMB = \
    36, 37, 38, 39, 42, 46, 49, 51, 81, 70, 69, 45, 47, 50, 54
GLOCK, MARIMBA, XYLO, CLARINET, TUBA, MUTED_TPT, TIMPANI, ORCH_HIT, SQUARE, PIZZ = 9, 12, 13, 71, 58, 59, 47, 55, 80, 45
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SHIFT = [0]  # a transposition for every note played (the hurry is up a tone)


def mel(text):
    """Parses a line like "g5/.75 f5/.25 r/.5" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens
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
    sh = 0 if track.ch == 9 else SHIFT[0]
    track.note(beat, max(0.05, length - 0.02), pitch + sh, max(1, min(127, int(vel))))


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


def bubble_track(ch, vol=70):
    """The toy synth: a square lead with a pitch-bend range of an octave, for bubbles that bend upwards."""
    tr = Track(ch, SQUARE, vol, 76, 80)
    tr.events += [(0, bytes([0xB0 | ch, 101, 0])), (0, bytes([0xB0 | ch, 100, 0])), (0, bytes([0xB0 | ch, 6, 12])),
                  (0, bytes([0xB0 | ch, 38, 0])), (0, bytes([0xB0 | ch, 74, 50]))]
    return tr


def bubble(track, beat, pitch, vel=70, rise=7, length=0.25):
    """One bubble: a short note that starts a little flat and bends up by `rise` semitones."""
    steps = 8
    bend(track, beat, 8192 - 1024)
    for k in range(1, steps + 1):
        bend(track, beat + length * 0.8 * k / steps, 8192 - 1024 + (1024 + rise * 8192 / 12) * k / steps)
    note(track, beat, length, pitch, vel)
    bend(track, beat + length * 0.97, 8192)


def band(kit=0):
    drums = Track(9, 0, 110, 64, 30)
    if kit:
        drums.events.append((0, bytes([0xC9, kit])))
    return dict(tuba=Track(0, TUBA, 108, 60, 30), mar=Track(1, MARIMBA, 104, 44, 45), cla=Track(2, CLARINET, 100, 72, 50),
                glk=Track(3, GLOCK, 88, 88, 60), bub=bubble_track(4), pizz=Track(5, PIZZ, 84, 36, 40),
                tpt=Track(6, MUTED_TPT, 100, 82, 45), timp=Track(7, TIMPANI, 104, 56, 45),
                hit=Track(8, ORCH_HIT, 80, 64, 50), xyl=Track(10, XYLO, 96, 40, 50), dr=drums)


# ---------------------------------------------------------------------------------------------------------------
# chords as (bass root, voicing around middle C), E flat major
Eb, Cm, Ab, Bb7, Fm7, Gm, G7, Abm, C7, F7 = ((39, [55, 58, 63]), (36, [55, 60, 63]), (44, [56, 60, 63]),
                                             (46, [56, 58, 62]), (41, [56, 60, 63]), (43, [55, 58, 62]),
                                             (43, [53, 59, 62]), (44, [56, 59, 63]), (36, [55, 58, 64]),
                                             (41, [57, 60, 63]))
Dm, A7 = (38, [57, 62, 65]), (45, [55, 61, 64])
INTRO = [[Eb], [Ab], [Eb], [Bb7]]
A_PROG = [[Eb], [Eb, Cm], [Fm7], [Bb7], [Eb], [G7, Cm], [Ab, Bb7], [Eb]]
B_PROG = [[Ab], [Bb7], [Gm], [Cm], [Fm7], [Bb7], [Ab, Abm], [Bb7]]
TURN = [[Cm], [Fm7], [Ab, Bb7], [Bb7]]

TUNE_A = mel("g5/.75 f5/.25 eb5/.5 bb4/.5 r/.5 g5/.5 bb5/1 | c6/.5 bb5/.5 g5/1 r/.5 eb5/.5 g5/1 | "
             "ab5/.75 g5/.25 f5/.5 c5/.5 r/.5 ab5/.5 c6/1 | bb5/1.5 ab5/.5 f5/.5 d5/.5 bb4/1 | "
             "g5/.75 f5/.25 eb5/.5 bb4/.5 r/.5 eb6/.5 d6/.5 c6/.5 | b5/.5 g5/.5 d5/.5 f5/.5 eb5/.5 g5/.5 c6/1 | "
             "ab5/.5 c6/.5 eb6/1 d6/.5 c6/.5 bb5/.5 ab5/.5 | g5/1 eb5/.5 f5/.5 eb5/1 r/1")
COUNTER_A = mel("bb4/2 g4/2 | ab4/2 g4/2 | ab4/2 c5/2 | d5/2 ab4/2 | bb4/2 g4/2 | f4/1 d4/1 eb4/2 | c4/2 d4/2 | "
                "eb4/2 bb3/2")
TUNE_B = mel("c6/1.5 bb5/.5 ab5/1 eb5/1 | d5/.5 f5/.5 ab5/.5 bb5/1.5 r/1 | bb5/1.5 a5/.5 g5/1 d5/1 | "
             "eb5/.5 g5/.5 c6/1 bb5/.5 g5/.5 eb5/1 | f5/.5 ab5/.5 c6/.5 eb6/1.5 c6/1 | d6/1 bb5/.5 ab5/.5 f5/1 d5/1 | "
             "eb5/.5 ab5/.5 c6/1 cb6/1 ab5/1 | bb5/.5 c6/.5 d6/.5 f6/.5 d6/1 bb5/1")
TUNE_TURN = mel("c5/.5 eb5/.5 g5/.5 c6/.5 bb5/1 g5/1 | ab5/.5 c6/.5 f6/.5 eb6/.5 c6/1 ab5/1 | "
                "c6/1 bb5/.5 ab5/.5 d6/1 c6/.5 bb5/.5 | bb5/.5 ab5/.5 f5/.5 d5/.5 bb4/.5 c5/.5 d5/.5 f5/.5")


def toybox_parts(t):
    tuba, mar, pizz, dr, bub = t["tuba"], t["mar"], t["pizz"], t["dr"], t["bub"]

    def oompah(b, bar, vel=92, lilt=True):
        """The sousaphone: root on 1, fifth on 3 (a 3-3-2 lilt: root, the 'and' of 2, 4), pizzicato 'pah' chords."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root > 40 else root
            hits = ((0, lo, 1.3), (1.5, lo + 7, 1.2), (3, lo + 12 if lo + 12 < 52 else lo, 0.8)) if lilt and ln == 4 \
                else ((0, lo, 0.9), (2, lo + 7, 0.9)) if ln == 4 else ((0, lo, 0.9), (1, lo + 7, 0.8))
            for q, p, l_ in hits:
                if q < ln:
                    note(tuba, b + off + q, l_, p, vel - (0 if q == 0 else 8))
            for q in range(int(ln)):
                if (off + q) % 2 == 1:
                    for p in v:
                        note(pizz, b + off + q, 0.3, p, vel - 22)

    def carpet(b, bar, vel=62, pattern=(0, 2, 1, 2, 0, 3, 1, 2)):
        """The marimba: eighth-note broken chords an octave up, with the top note an octave higher on 3."""
        for off, ln, (root, v) in split(bar):
            tones = [p + 12 for p in v] + [v[0] + 24]
            for k in range(int(ln * 2)):
                p = tones[pattern[(int(off * 2) + k) % len(pattern)]]
                note(mar, b + off + k * 0.5, 0.45, p, vel + (8 if k % 2 == 0 else 0))

    def kit(b, vel=64, busy=False, fill=False):
        """Light kit: kick on 1 and the 'and' of 2, side stick on 2 and 4, closed hat eighths, shaker sixteenths."""
        for q in (0, 1.5, 2.5) if busy else (0, 1.5):
            note(dr, b + q, 0.2, KICK, vel + 6)
        if busy:
            note(dr, b + 2, 0.2, KICK, vel)
        for q in (1, 3):
            note(dr, b + q, 0.2, CLAP if busy and q == 3 else STICK, vel - 4)
        for k in range(8):
            note(dr, b + k * 0.5, 0.2, CLOSED, vel - 14 + (6 if k % 2 == 0 else 0))
        for k in range(16):
            note(dr, b + k * 0.25, 0.1, SHAKER, vel - 28 + (8 if k % 4 == 2 else 0))
        if fill:
            for k, dr_ in enumerate((HTOM, HTOM, MTOM, LTOM)):
                note(dr, b + 3 + k * 0.25, 0.2, dr_, vel + 2 * k)

    def blow(b, bar, vel=60, where=(3.5,)):
        """Bubbles from the toy synth: chord tones two octaves up, bent upwards."""
        for q in where:
            root, v = [c for off, ln, c in split(bar) if off <= q][-1]
            bubble(bub, b + q, v[int(b + q) % len(v)] + 24, vel, 5 + int(b) % 4)

    return oompah, carpet, kit, blow


def theme():
    SHIFT[0] = 0
    t = band()
    cla, glk, bub, xyl, dr, mar = t["cla"], t["glk"], t["bub"], t["xyl"], t["dr"], t["mar"]
    oompah, carpet, kit, blow = toybox_parts(t)
    bar = 0
    for i, ch in enumerate(INTRO):  # intro: the marimba alone, bubbles, the tuba and kit fall in
        b = (bar + i) * 4
        carpet(b, ch, 58 + 3 * i)
        blow(b, ch, 56, (1.5, 3.5) if i < 3 else (1.5,))
        if i >= 2:
            oompah(b, ch, 86)
            kit(b, 54, fill=i == 3)
    for k, p in enumerate((70, 75, 79)):  # a glockenspiel pickup into the tune
        note(glk, 14.5 + k * 0.5, 0.5, p + 12, 60 + 6 * k)
    bar += 4

    def accomp(start, prog, vel=90, busy=False, bubbles=(3.5,)):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            oompah(b, ch, vel)
            carpet(b, ch, vel - 30)
            kit(b, vel - 28, busy, fill=i == len(prog) - 1)
            blow(b, ch, 54, bubbles)

    accomp(bar, A_PROG)  # A: the clarinet tune
    play(cla, bar * 4, TUNE_A, 92)
    for i in (1, 3, 5, 7):
        note(glk, (bar + i) * 4 + 3.5, 0.5, A_PROG[i][-1][1][-1] + 24, 56)
    bar += 8

    accomp(bar, A_PROG, busy=True)  # A': marimba and glockenspiel take the tune, the clarinet goes low
    play(mar, bar * 4, TUNE_A, 96, 0.8, 0)
    play(glk, bar * 4, TUNE_A, 62, 0.6, 12, 0)
    play(cla, bar * 4, COUNTER_A, 76, 0.95)
    bar += 8

    for i, ch in enumerate(B_PROG):  # B: legato clarinet in A flat colours, toy-synth answers, lighter kit
        b = (bar + i) * 4
        oompah(b, ch, 84, lilt=i % 2 == 0)
        carpet(b, ch, 54, (0, 1, 2, 3, 2, 1, 0, 1))
        kit(b, 56, fill=i == 7)
        blow(b, ch, 58, (2.5, 3.5) if i % 2 else (3.5,))
    play(cla, bar * 4, TUNE_B, 94, 0.97)
    bar += 8

    accomp(bar, A_PROG, 94, busy=True, bubbles=(1.5, 3.5))  # A'': tutti, clarinet and glockenspiel, xylophone
    play(cla, bar * 4, TUNE_A, 96)
    play(glk, bar * 4, TUNE_A, 58, 0.6, 12, 0)
    play(xyl, bar * 4, COUNTER_A, 60, 0.4, 12, 0)
    bar += 8

    accomp(bar, TURN, 88)  # turn: C minor colour, the clarinet climbing back to the intro
    play(cla, bar * 4, TUNE_TURN, 88, 0.85)
    play(mar, bar * 4, TUNE_TURN, 60, 0.7, -12)
    note(dr, bar * 4, 0.5, CRASH, 60)
    bar += 4
    assert bar == 40
    return list(t.values()), 126, bar


# ---------------------------------------------------------------------------------------------------------------
CHASE_PROG = [[Cm], [Ab], [Fm7], [G7], [Cm], [Ab], [Fm7, G7], [Bb7]]  # (becomes D minor up a tone)
CHASE = mel("c5/.5 eb5/.5 g5/.5 eb5/.5 c6/.5 g5/.5 eb5/.5 g5/.5 | ab5/.5 eb5/.5 c5/.5 eb5/.5 ab5/.5 c6/.5 eb6/.5 c6/.5 | "
            "f5/.5 ab5/.5 c6/.5 ab5/.5 f5/.5 c5/.5 f5/.5 ab5/.5 | g5/.5 b5/.5 d6/.5 b5/.5 f6/.5 d6/.5 b5/.5 g5/.5 | "
            "eb6/.5 c6/.5 g5/.5 c6/.5 eb6/.5 g6/.5 eb6/.5 c6/.5 | c6/.5 ab5/.5 eb5/.5 ab5/.5 c6/.5 eb6/.5 ab6/.5 eb6/.5 | "
            "f6/.5 c6/.5 ab5/.5 f5/.5 g5/.5 b5/.5 d6/.5 f6/.5 | eb6/.5 d6/.5 bb5/.5 f5/.5 d5/.5 f5/.5 ab5/.5 bb5/.5")


def hurry():
    SHIFT[0] = 2
    t = band()
    cla, glk, mar, tuba, dr = t["cla"], t["glk"], t["mar"], t["tuba"], t["dr"]
    oompah, carpet, kit, blow = toybox_parts(t)

    def accomp(start, prog, vel, drive=False):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            if drive:  # the tuba drives eighths under the chase
                root = ch[0][0] - 12 if ch[0][0] > 40 else ch[0][0]
                for k in range(8):
                    note(tuba, b + k * 0.5, 0.4, root + (7 if k % 4 == 3 else 0), vel - (0 if k % 2 == 0 else 10))
                for q in (1, 3):
                    for p in ch[-1][1]:
                        note(t["pizz"], b + q, 0.3, p, vel - 24)
            else:
                oompah(b, ch, vel, lilt=False)
            carpet(b, ch, vel - 30)
            kit(b, vel - 26, True, fill=i == 7)
            blow(b, ch, 56, (3.5,))

    accomp(0, A_PROG, 90)  # A: the clarinet tune, pushed, with the glockenspiel an octave up
    play(cla, 0, TUNE_A, 96, 0.85)
    play(glk, 0, TUNE_A, 56, 0.5, 12, 0)
    accomp(8, CHASE_PROG, 94, drive=True)  # the chase in the relative minor
    play(mar, 32, CHASE, 100, 0.8)
    play(cla, 32, [(b, ln, p) for b, ln, p in CHASE if b % 1 == 0], 80, 0.9, -12)
    note(dr, 32, 0.5, CRASH, 70)
    accomp(16, A_PROG, 96)  # A again, bubbles and xylophone
    play(cla, 64, TUNE_A, 100, 0.85)
    play(t["xyl"], 64, TUNE_A, 66, 0.5, 12, 0)
    for i in range(8):
        blow((16 + i) * 4, A_PROG[i], 60, (1.5,))
    return list(t.values()), 164, 24


# ---------------------------------------------------------------------------------------------------------------
# boss: C minor
bCm, bFm, bAb, bG7, bBb, bEb, bDb = ((36, [55, 60, 63]), (41, [56, 60, 65]), (44, [56, 60, 63]), (43, [53, 59, 62]),
                                     (46, [58, 62, 65]), (39, [55, 58, 63]), (37, [56, 61, 65]))
BOSS_INTRO = [[bCm], [bCm], [bAb], [bG7]]
BOSS_A = [[bCm], [bCm], [bAb], [bG7], [bCm], [bFm], [bAb, bG7], [bCm]]
BOSS_B = [[bAb], [bBb], [bEb], [bCm], [bAb], [bDb], [bG7], [bG7]]
BOSS_TUNE_A = mel("c5/.5 r/.5 c5/.5 eb5/.5 g5/1 f5/.5 eb5/.5 | d5/.5 eb5/.5 f5/.5 g5/.5 ab5/1.5 g5/.5 | "
                  "c6/1 ab5/.5 eb5/.5 c5/1 eb5/1 | d5/.5 f5/.5 b5/1 ab5/.5 g5/.5 f5/1 | "
                  "eb5/.5 g5/.5 c6/1 r/.5 bb5/.5 ab5/.5 g5/.5 | ab5/.5 f5/.5 c5/1 f5/.5 ab5/.5 c6/1 | "
                  "eb6/1 c6/1 d6/1 b5/1 | c6/1.5 g5/.5 eb5/.5 d5/.5 c5/1")
BOSS_TUNE_B = mel("ab4/1.5 eb5/.5 ab5/2 | bb4/1.5 f5/.5 bb5/2 | g5/.5 f5/.5 eb5/1 bb4/1 eb5/1 | "
                  "c5/.5 d5/.5 eb5/.5 g5/.5 c6/2 | c6/1.5 bb5/.5 ab5/1 eb5/1 | db6/1.5 c6/.5 ab5/1 f5/1 | "
                  "g5/.5 b5/.5 d6/.5 f6/.5 d6/1 b5/1 | g5/.5 ab5/.5 b5/.5 c6/.5 d6/.5 eb6/.5 f6/.5 g6/.5")


def boss():
    SHIFT[0] = 0
    t = band()
    tuba, mar, cla, tpt, glk, timp, hit, dr, pizz = (t[k] for k in ("tuba", "mar", "cla", "tpt", "glk", "timp", "hit",
                                                                    "dr", "pizz"))

    def stomp(b, bar, vel=96):
        """The tuba ostinato in eighths (root, root, fifth, root, octave, fifth, root, minor third)."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root > 40 else root
            third = 3 if (v[1] - root) % 12 in (3, 8) or (v[0] - root) % 12 == 3 else 4
            for k, iv in enumerate((0, 0, 7, 0, 12, 7, 0, third)[:int(ln * 2)]):
                note(tuba, b + off + k * 0.5, 0.35, lo + iv, vel - (0 if k % 2 == 0 else 12))

    def run(b, bar, vel=56):
        """The marimba in sixteenths: root, fifth, octave, third, an octave up, turning."""
        for off, ln, (root, v) in split(bar):
            tones = [v[0] + 12, v[1] + 12, v[2] + 12, v[1] + 24]
            for k in range(int(ln * 4)):
                note(mar, b + off + k * 0.25, 0.22, tones[(0, 1, 2, 3, 2, 1, 2, 1)[k % 8]], vel + (10 if k % 4 == 0 else 0))

    def drums(b, vel=70, fill=False, half=False):
        for q in (0, 0.75, 2, 2.5) if not half else (0, 2):
            note(dr, b + q, 0.2, KICK, vel + 6)
        for q in (1, 3):
            note(dr, b + q, 0.2, SNARE, vel + (0 if half else 4))
        for k in range(8):
            note(dr, b + k * 0.5, 0.2, CLOSED if k % 4 != 3 else OPEN, vel - 16 + (6 if k % 2 == 0 else 0))
        for k in range(16):
            note(dr, b + k * 0.25, 0.1, CABASA, vel - 30)
        if fill:
            for k, tom in enumerate((HTOM, HTOM, MTOM, MTOM, LTOM, LTOM, SNARE, SNARE)):
                note(dr, b + 2 + k * 0.25, 0.2, tom, vel - 4 + 2 * k)

    def timpani(b, bar, vel=90):
        root = split(bar)[0][2][0]
        note(timp, b, 0.9, root, vel)
        note(timp, b + 3.5, 0.4, root + 7 if root + 7 <= 50 else root - 5, vel - 20)

    for i, ch in enumerate(BOSS_INTRO):  # intro: tuba and timpani, the marimba creeping in, a stab to start
        b = i * 4
        stomp(b, ch, 90 + 2 * i)
        timpani(b, ch, 84 + 4 * i)
        if i >= 1:
            run(b, ch, 42 + 6 * i)
        if i >= 2:
            drums(b, 62, fill=i == 3, half=i == 2)
    for q in (0, 1.5):
        for p in (48, 55, 60):
            note(hit, q, 0.3, p, 90)

    def section(start, prog, lead, lead2, vel=96, glock=False):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            stomp(b, ch)
            run(b, ch, 54)
            timpani(b, ch)
            drums(b, 70, fill=i == 7)
            for q in (1.5, 3):
                for p in ch[-1][1]:
                    note(pizz, b + q, 0.25, p, 70)
            if i % 4 == 0:
                for p in (ch[0][0], ch[0][0] + 7, ch[0][0] + 12):
                    note(hit, b, 0.3, p + 12, 80)
                note(dr, b, 0.5, CRASH, 72)
        play(lead, start * 4, prog is BOSS_B and BOSS_TUNE_B or BOSS_TUNE_A, vel, 0.9)
        if lead2:
            play(lead2, start * 4, prog is BOSS_B and BOSS_TUNE_B or BOSS_TUNE_A, vel - 18, 0.9, -12)
        if glock:
            play(glk, start * 4, BOSS_TUNE_A, 58, 0.5, 12, 0)

    section(4, BOSS_A, cla, None, 96)
    section(12, BOSS_B, tpt, cla, 98)
    section(20, BOSS_A, cla, tpt, 100, glock=True)
    return list(t.values()), 150, 28


for name, song in (("fizzlings_theme", theme), ("fizzlings_hurry", hurry), ("fizzlings_boss", boss)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
