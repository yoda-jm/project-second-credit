#!/usr/bin/env python3
"""Game 15 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own
(no classical or folk quotations): a small chamber/folk orchestra for a cute cavern adventure.
- mossfolk_theme_a: bouncy, in F major, 120 bpm. Clarinet tune over pizzicato oom-pah and marimba, glockenspiel
  doubling, a flute and oboe bridge, woodblock and triangle. Form: intro 4 | A 8 | A' 8 | B 8 | A 8 | turn 4 (80 s).
- mossfolk_theme_b: curious and a little mysterious, D dorian, 100 bpm. A tiptoeing bassoon tune over a marimba
  ostinato and pizzicato steps, clarinet echoes, celesta and harp glints, a low timpani pulse.
  Form: intro 4 | A 8 | A' 8 | B 8 | A'' 8 | outro 4 (96 s).
- mossfolk_theme_c: busy and march-like, Bb major, 128 bpm. Piccolo and clarinet over tuba oom-pah, pizzicato
  offbeats, snare cadences, a bassoon countermelody, a legato trio in Eb, a xylophone call-and-answer.
  Form: intro 4 | A 8 | A' 8 | trio 8 | C 8 | A 8 | turn 4 (90 s).
Usage: python3 tools/audio/mossfolk_music.py
-> godot/games/mossfolk/audio/music/mossfolk_theme_{a,b,c}.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/mossfolk/audio/music/"
ORCH_KIT = 48  # the orchestral kit on the drum channel
KICK, SNARE, CRASH, TRI, TRI_MUTE, WB_HI, WB_LO, TAMB, SHAKER, CASTANET = 36, 38, 49, 81, 80, 76, 77, 54, 70, 85
# GM programs
PIZZ, CLARINET, BASSOON, OBOE, FLUTE, PICCOLO, GLOCK, MARIMBA, XYLO, CELESTA, HARP, TUBA, TIMPANI, STRINGS, HORN = \
    45, 71, 70, 68, 73, 72, 9, 12, 13, 8, 46, 58, 47, 48, 60

NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def mel(text):
    """Parses a line like "a4/.5 c5/.5 f5/.75 r/1" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens
    (after the letter), r is a rest; '|' bar marks are ignored."""
    out, beat = [], 0.0
    for tok in text.split():
        if tok == "|":
            assert beat % 4 == 0, f"a bar of {beat % 4} beats before '|' in: {text}"
            continue
        p, ln = tok.split("/")
        ln = float(ln)
        if p != "r":
            m = re.fullmatch(r"([a-g])([#b]?)(-?\d)", p)
            out.append((beat, ln, 12 * (int(m.group(3)) + 1) + NOTE[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)]))
        beat += ln
    assert beat % 4 == 0, f"a last bar of {beat % 4} beats in: {text}"
    return out, beat


def play(track, start, line, vel, staccato=0.9, shift=0, accent=None):
    notes, _ = line if isinstance(line, tuple) else (line, 0)
    for beat, length, pitch in notes:
        v = vel + (accent if accent and beat % 1 == 0 else 0)
        track.note(start + beat, length * staccato, pitch + shift, max(1, min(127, v)))


def chords_of(bar):
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def drums(volume=90, reverb=50):
    d = Track(9, 0, volume, 64, reverb)
    d.events.append((0, bytes([0xC9, ORCH_KIT])))
    return d


# ---------------------------------------------------------------------------------------------------------------
def theme_a():
    """Bouncy, F major."""
    cla, glk, flu, obo, bsn = Track(0, CLARINET, 100, 52, 45), Track(1, GLOCK, 64, 84, 55), \
        Track(2, FLUTE, 90, 76, 55), Track(3, OBOE, 84, 44, 50), Track(4, BASSOON, 90, 60, 40)
    pz, mar, hrp, dr = Track(5, PIZZ, 108, 64, 40), Track(6, MARIMBA, 88, 40, 45), Track(7, HARP, 70, 90, 60), drums()
    tracks = [cla, glk, flu, obo, bsn, pz, mar, hrp, dr]
    F, C, Dm, Bb, Gm, C7, Am, G7, A7 = ((41, [57, 60, 65]), (36, [55, 60, 64]), (38, [57, 62, 65]),
                                        (34, [58, 62, 65]), (43, [58, 62, 67]), (36, [58, 60, 64]),
                                        (45, [57, 60, 64]), (43, [59, 62, 65]), (45, [57, 61, 64]))
    A_PROG = [[F], [C], [Dm], [Bb, C], [F], [Gm], [Bb, C7], [F]]
    B_PROG = [[Bb], [F], [Gm], [C], [Am], [Dm], [G7], [C7]]
    TURN = [[Dm], [Gm], [C7], [C7]]
    TUNE_A = mel("a4/.5 c5/.5 f5/.75 e5/.25 f5/.5 g5/.5 a5/1 | g5/.5 e5/.5 c5/1 r/.5 e5/.5 g5/.5 c6/.5 | "
                 "a5/.75 g5/.25 f5/.5 d5/.5 e5/.5 f5/.5 d5/1 | bb4/.5 d5/.5 f5/.5 bb5/.5 a5/.5 g5/.5 e5/1 | "
                 "a4/.5 c5/.5 f5/.75 e5/.25 f5/.5 a5/.5 c6/1 | bb5/.5 a5/.5 g5/.5 d5/.5 g5/1 f5/.5 e5/.5 | "
                 "d5/.5 f5/.5 bb5/.5 a5/.5 g5/.5 e5/.5 c5/.5 e5/.5 | f5/1.5 c5/.5 f4/1 r/1")
    TUNE_B = mel("d6/1.5 c6/.5 bb5/1 f5/1 | a5/1.5 g5/.5 f5/2 | g5/.5 a5/.5 bb5/1 d6/1 bb5/1 | c6/2 bb5/.5 a5/.5 g5/1 | "
                 "e5/1 a5/1 c6/1.5 b5/.5 | a5/1 f5/1 d5/2 | g5/.5 a5/.5 b5/.5 d6/.5 f6/1 d6/1 | "
                 "e6/1 c6/.5 bb5/.5 g5/.5 e5/.5 c5/1")
    COUNTER = mel("r/2 a3/.5 bb3/.5 c4/1 | g3/1 r/1 e3/.5 f3/.5 g3/1 | f3/2 d3/.5 e3/.5 f3/1 | d3/1 f3/1 c4/1 bb3/1 | "
                  "a3/1 r/1 c4/.5 bb3/.5 a3/1 | g3/1.5 a3/.5 bb3/1 d4/1 | bb3/1 d4/1 c4/1 bb3/1 | a3/1 c3/1 f3/1 r/1")
    RUN_UP = mel("c3/.5 d3/.5 e3/.5 f3/.5 g3/.5 a3/.5 bb3/.5 b3/.5")  # the bassoon leads the loop home

    def oompah(b, bar, vel=96):
        for off, ln, (root, v) in chords_of(bar):
            for k in range(int(ln)):
                if k % 2 == 0:
                    pz.note(b + off + k, 0.4, root if (b // 4) % 2 == 0 or k else root + 7, vel)
                else:
                    for p in v:
                        pz.note(b + off + k, 0.3, p, vel - 22)
                    pz.note(b + off + k + 0.5, 0.3, v[-1], vel - 34)

    def marimba_bar(b, bar, vel=70):
        for off, ln, (_, v) in chords_of(bar):
            notes = [v[0] + 12, v[1] + 12, v[2] + 12, v[1] + 12]
            for k in range(int(ln * 2)):
                mar.note(b + off + k * 0.5, 0.45, notes[k % 4], vel + (10 if k % 2 == 0 else 0))

    def groove(b, full=True, fill=False):
        for q in range(4):
            dr.note(b + q + 0.5, 0.1, WB_HI if q % 2 == 0 else WB_LO, 72)
        if full:
            dr.note(b, 0.2, KICK, 70)
            dr.note(b + 2, 0.2, KICK, 60)
            dr.note(b + 1, 0.2, TAMB, 44)
            dr.note(b + 3, 0.2, TAMB, 50)
            for k in range(8):
                dr.note(b + k / 2, 0.05, SHAKER, 36 if k % 2 else 26)
        if fill:
            for i in range(6):
                dr.note(b + 3 + i / 6, 0.1, SNARE, 50 + 8 * i)

    bar = 0
    for i, ch in enumerate(A_PROG[:4]):  # intro: marimba and pizzicato, a triangle, glockenspiel glints
        b = bar * 4
        marimba_bar(b, ch, 58 + 4 * i)
        if i >= 1:
            oompah(b, ch, 84 + 4 * i)
        dr.note(b, 1, TRI, 50)
        glk.note(b + 3.5, 0.5, 84 - i * 2, 50)
        bar += 1
    dr.note(bar * 4 - 1, 1, CRASH, 40)

    def section_a(start, lead_vel, answer):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            oompah(b, ch)
            marimba_bar(b, ch)
            groove(b, fill=i == 7)
        play(cla, start * 4, TUNE_A, lead_vel, 0.8, 0, 8)
        play(glk, start * 4, [x for x in TUNE_A[0] if x[0] % 1 == 0], 52, 0.8, 12)
        if answer:
            play(bsn, start * 4, COUNTER, 78, 0.85)
            play(flu, start * 4, TUNE_A, 56, 0.8, 12)

    section_a(bar, 94, False)
    bar += 8
    section_a(bar, 98, True)
    bar += 8
    for i, ch in enumerate(B_PROG):  # B: flute and oboe sing longer notes, the harp rolls chords, softer beat
        b = (bar + i) * 4
        oompah(b, ch, 86)
        for off, ln, (root, v) in chords_of(ch):
            for k, p in enumerate([root + 12] + v + [v[0] + 12]):
                hrp.note(b + off + k * 0.12, 1.8, p, 58)
        for k in range(4):
            mar.note(b + k + 0.5, 0.4, ch[0][1][k % 3] + 24, 56)
        groove(b, full=i % 2 == 0, fill=i == 7)
        dr.note(b, 1, TRI, 44)
    play(flu, bar * 4, TUNE_B, 92, 0.92)
    play(obo, bar * 4, TUNE_B, 62, 0.92, -12)
    play(bsn, bar * 4 + 28, RUN_UP, 70, 0.9)
    bar += 8
    section_a(bar, 100, True)
    bar += 8
    for i, ch in enumerate(TURN):  # the turnaround: clarinet trills, bassoon climbs back to the intro
        b = (bar + i) * 4
        oompah(b, ch, 88)
        marimba_bar(b, ch, 64)
        groove(b, full=i < 2, fill=i == 3)
    play(cla, bar * 4, mel("f5/.25 e5/.25 d5/.5 a5/1 r/2 | g5/.25 f5/.25 d5/.5 bb5/1 r/2 | "
                           "c6/.5 bb5/.5 a5/.5 g5/.5 e5/.5 g5/.5 bb5/1 | c6/2 r/2"), 90, 0.85)
    play(bsn, bar * 4 + 12, RUN_UP, 80, 0.9)
    bar += 4
    assert bar == 40
    return tracks, 120, bar


# ---------------------------------------------------------------------------------------------------------------
def theme_b():
    """Curious and a little mysterious, D dorian."""
    bsn, cla, obo, flu = Track(0, BASSOON, 110, 54, 50), Track(1, CLARINET, 92, 74, 55), \
        Track(2, OBOE, 86, 44, 60), Track(3, FLUTE, 80, 84, 65)
    mar, pz, cel, hrp, tim, strg, dr = Track(4, MARIMBA, 90, 64, 50), Track(5, PIZZ, 100, 40, 45), \
        Track(6, CELESTA, 70, 96, 70), Track(7, HARP, 70, 30, 70), Track(8, TIMPANI, 76, 64, 50), \
        Track(10, STRINGS, 40, 64, 75), drums(80, 60)
    tracks = [bsn, cla, obo, flu, mar, pz, cel, hrp, tim, strg, dr]
    Dm, GD, Bb, C, A7s, A7, F7, Em7, Gm, E7 = ((38, [57, 62, 65]), (38, [59, 62, 67]), (34, [58, 62, 65]),
                                             (36, [55, 60, 64]), (33, [57, 62, 64]), (33, [55, 61, 64]),
                                             (41, [57, 60, 64]), (40, [55, 59, 62]), (43, [55, 58, 62]),
                                             (40, [56, 59, 62]))
    A_PROG = [[Dm], [GD], [Dm], [GD], [Bb], [C], [A7s], [A7]]
    B_PROG = [[F7], [Em7], [Dm], [A7], [Gm], [Bb], [E7], [A7]]
    TUNE = mel("d3/.5 r/.5 f3/.5 a3/.5 b3/.75 a3/.25 g3/1 | f3/.5 e3/.5 d3/.5 e3/.5 f3/.5 g3/.5 a3/1 | "
               "d4/.5 r/.5 c4/.5 a3/.5 b3/.5 c4/.5 a3/1 | b3/1.5 g3/.5 e3/1 r/1 | "
               "f3/.5 g3/.5 a3/.5 bb3/.5 d4/1 c4/.5 bb3/.5 | e4/.5 r/.5 g3/.5 c4/.5 e4/.5 d4/.5 c4/1 | "
               "d4/1 a3/.5 d4/.5 e4/1.5 d4/.5 | c#4/2 a3/1 r/1")
    ECHO = mel("r/3 a4/.25 b4/.25 d5/.5 | r/3 e5/.25 d5/.25 a4/.5 | r/3 c5/.25 d5/.25 f5/.5 | r/2 g5/.5 e5/.5 b4/1 | "
               "r/3 d5/.25 f5/.25 bb5/.5 | r/3 c5/.25 e5/.25 g5/.5 | r/2 a5/.5 e5/.5 d5/1 | r/2 e5/.5 g5/.5 a5/1")
    TUNE_B = mel("a5/1.5 g5/.5 e5/1 c5/1 | d5/1.5 e5/.5 g5/2 | f5/1 e5/.5 d5/.5 a4/2 | c#5/1 e5/1 g5/1.5 f5/.5 | "
                 "bb5/1.5 a5/.5 g5/1 d5/1 | f5/1.5 d5/.5 bb4/2 | e5/.5 g#5/.5 b5/1 d6/1 b5/1 | c#6/2 a5/1 e5/1")

    def ostinato(b, bar, vel=66):
        """The marimba: root, fifth, ninth, fifth, octave, fifth, third, fifth in eighths, a quiet tick-tock."""
        for off, ln, (root, v) in chords_of(bar):
            r = root + 24
            notes = (r, r + 7, r + 14, r + 7, r + 12, r + 7, v[1] + 12 if v[1] < r else v[1], r + 7)
            for k in range(int(ln * 2)):
                mar.note(b + off + k * 0.5, 0.4, notes[k % 8], vel + (8 if k % 4 == 0 else 0))

    def steps(b, bar, vel=90):
        """Pizzicato bass tiptoeing on the beats: root, fifth, octave, a neighbour."""
        for off, ln, (root, _) in chords_of(bar):
            for k, iv in enumerate((0, 7, 12, 10)[:int(ln)]):
                pz.note(b + off + k, 0.3, root + iv, vel - 8 * (k % 2))

    def ticks(b, busy):
        dr.note(b, 0.1, WB_LO, 64)
        dr.note(b + 1.5, 0.1, WB_HI, 50)
        dr.note(b + 2, 0.1, WB_LO, 58)
        if busy:
            dr.note(b + 3.5, 0.1, WB_HI, 56)
            dr.note(b + 2.75, 0.1, CASTANET, 40)
            for k in range(4):
                dr.note(b + k + 0.5, 0.05, SHAKER, 30)

    def glint(b, pitches, vel=50, step=0.25):
        for k, p in enumerate(pitches):
            cel.note(b + k * step, 0.8, p, vel)

    bar = 0
    for i, ch in enumerate(A_PROG[:4]):  # intro: the marimba alone, then the pizzicato, a timpani heartbeat
        b = bar * 4
        ostinato(b, ch, 54 + 4 * i)
        if i >= 2:
            steps(b, ch, 80)
        tim.note(b, 1, 38, 64)
        tim.note(b + 2.5, 0.5, 45, 44)
        strg.note(b, 4, 62 if i % 2 == 0 else 67, 40)
        bar += 1
    glint(12, (86, 89, 93, 96), 44)

    def section_a(start, lead, lead_vel, shift, extra):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            ostinato(b, ch)
            steps(b, ch)
            ticks(b, extra)
            if i % 2 == 0:
                tim.note(b, 1, ch[0][0] + 12 if ch[0][0] < 36 else ch[0][0], 58)
            strg.note(b, 3.9, ch[0][1][1], 36)
        play(lead, start * 4, TUNE, lead_vel, 0.7, shift, 6)
        if extra:
            play(obo, start * 4, ECHO, 64, 0.8)
            glint(start * 4 + 30, (98, 93, 89, 86), 40)
            hrp.note(start * 4 + 26, 2, 74, 50)

    section_a(bar, bsn, 100, 0, False)
    bar += 8
    section_a(bar, cla, 90, 12, True)
    play(bsn, bar * 4, TUNE, 62, 0.7, 0)
    bar += 8
    for i, ch in enumerate(B_PROG):  # B: the flute wonders aloud over harp arpeggios and held strings
        b = (bar + i) * 4
        for off, ln, (root, v) in chords_of(ch):
            for k in range(int(ln * 2)):
                hrp.note(b + off + k * 0.5, 1.2, ([root + 12] + v + [v[0] + 12, v[1] + 12, v[2] + 12, v[1] + 12])[k % 8], 56)
            for p in v:
                strg.note(b + off, ln - 0.05, p, 44)
            pz.note(b + off, 0.4, root, 86)
            pz.note(b + off + 2.5, 0.3, root + 7, 70)
        dr.note(b, 1, TRI, 36 if i % 2 else 46)
        if i in (3, 7):
            glint(b + 2, (93, 97, 100, 105), 42)
    play(flu, bar * 4, TUNE_B, 88, 0.95)
    play(cla, bar * 4, mel("r/2 c5/2 | r/2 b4/2 | r/2 a4/2 | r/2 c#5/2 | r/2 d5/2 | r/2 bb4/2 | r/2 b4/2 | r/2 c#5/2"),
         58, 0.95)
    bar += 8
    section_a(bar, bsn, 104, 0, True)
    play(cla, bar * 4, TUNE, 70, 0.7, 12)
    play(cel, bar * 4, [x for x in TUNE[0] if x[0] % 2 == 0], 40, 0.6, 24)
    bar += 8
    for i, ch in enumerate([[Dm], [GD], [Bb], [A7]]):  # outro: everything thins back to the marimba, a question
        b = (bar + i) * 4
        ostinato(b, ch, 64 - 3 * i)
        steps(b, ch, 84)
        tim.note(b, 1, 38 if i < 3 else 45, 56)
        ticks(b, False)
    play(bsn, bar * 4, mel("d3/.5 r/.5 f3/.5 a3/.5 b3/2 | r/4 | f3/.5 r/.5 d4/.5 bb3/.5 a3/2 | c#4/.5 e4/.5 g4/1 r/2"),
         90, 0.7)
    glint(bar * 4 + 14, (81, 85, 88, 91), 40, 0.5)
    bar += 4
    assert bar == 40
    return tracks, 100, bar


# ---------------------------------------------------------------------------------------------------------------
def theme_c():
    """Busy, march-like, Bb major."""
    pic, cla, bsn, glk, xyl = Track(0, PICCOLO, 84, 80, 45), Track(1, CLARINET, 100, 50, 45), \
        Track(2, BASSOON, 92, 64, 40), Track(3, GLOCK, 60, 90, 50), Track(4, XYLO, 84, 36, 45)
    tuba, pz, hrn, dr = Track(5, TUBA, 100, 64, 30), Track(6, PIZZ, 96, 76, 40), Track(7, HORN, 60, 40, 55), \
        drums(96, 40)
    tracks = [pic, cla, bsn, glk, xyl, tuba, pz, hrn, dr]
    Bb, F7, Eb, F, Gm, Cm, Bb7, Ab, Dm, C7 = ((34, [58, 62, 65]), (41, [57, 60, 63]), (39, [58, 63, 67]),
                                              (41, [57, 60, 65]), (43, [58, 62, 67]), (36, [55, 60, 63]),
                                              (34, [56, 62, 65]), (44, [56, 60, 63]), (38, [57, 62, 65]),
                                              (36, [58, 60, 64]))
    A_PROG = [[Bb], [F7], [Bb], [Eb, F], [Gm], [Cm], [F7], [Bb]]
    TRIO = [[Eb], [Bb7], [Eb], [Ab], [Eb], [Cm], [F7], [Bb7]]
    C_PROG = [[Eb], [F], [Dm], [Gm], [Eb], [F], [C7], [F7]]
    TUNE = mel("f5/.75 f5/.25 bb5/1 d6/.75 c6/.25 bb5/1 | a5/.5 c6/.5 a5/.5 f5/.5 g5/.5 a5/.5 bb5/.5 c6/.5 | "
               "d6/.75 c6/.25 bb5/.5 f5/.5 d5/1 f5/1 | g5/.5 bb5/.5 eb6/1 d6/.5 c6/.5 a5/1 | "
               "g5/.75 g5/.25 bb5/.5 d6/.5 g6/1 f6/.5 eb6/.5 | c6/.5 eb6/.5 d6/.5 c6/.5 bb5/.5 a5/.5 g5/1 | "
               "f5/.5 a5/.5 c6/.5 eb6/.5 d6/.5 c6/.5 a5/1 | bb5/1 f5/.5 d5/.5 bb4/1 r/1")
    COUNTER = mel("d4/2 f4/1 d4/1 | c4/1.5 eb4/.5 c4/1 a3/1 | bb3/2 d4/1 bb3/1 | bb3/1 g3/1 a3/1 c4/1 | "
                  "d4/1.5 bb3/.5 g3/2 | eb4/1 c4/1 g3/1 eb4/1 | c4/1 a3/1 f3/1 a3/1 | bb3/2 r/2")
    TRIO_TUNE = mel("g5/1.5 bb5/.5 eb6/2 | d6/1 c6/1 bb5/1 ab5/1 | g5/1.5 f5/.5 eb5/1 g5/1 | c6/3 ab5/1 | "
                    "bb5/1.5 g5/.5 eb5/1 bb5/1 | eb6/1.5 d6/.5 c6/2 | a5/1 c6/1 f6/1 eb6/1 | d6/2 bb5/1 ab5/1")
    CALL = mel("g6/.5 bb6/.5 g6/.5 eb6/.5 f6/1 r/1 | r/4 | f6/.5 a6/.5 f6/.5 d6/.5 e6/1 r/1 | r/4 | "
               "bb6/.5 g6/.5 eb6/.5 g6/.5 bb6/1 r/1 | r/4 | e6/.5 g6/.5 bb6/.5 g6/.5 e6/1 r/1 | r/4")
    ANSWER = mel("r/4 | c3/.5 f3/.5 a3/.5 c4/.5 a3/.5 f3/.5 c3/1 | r/4 | d3/.5 g3/.5 bb3/.5 d4/.5 bb3/.5 g3/.5 d3/1 | "
                 "r/4 | a3/.5 c4/.5 f4/.5 c4/.5 a3/.5 f3/.5 c3/1 | r/4 | eb3/.5 f3/.5 a3/.5 c4/.5 eb4/.5 c4/.5 a3/.5 f3/.5")

    def oompah(b, bar, vel=92):
        """Tuba on the beats (root, fifth), pizzicato chords on the offbeats: the march's spring."""
        for off, ln, (root, v) in chords_of(bar):
            for k in range(int(ln)):
                tuba.note(b + off + k, 0.45, root + (7 if k % 2 else 0) - 12 if root > 36 else root + (7 if k % 2 else 0),
                          vel if k % 2 == 0 else vel - 12)
                for p in v:
                    pz.note(b + off + k + 0.5, 0.25, p, vel - 20)

    def snare_bar(b, fill=False, soft=False):
        if soft:
            for q in range(4):
                dr.note(b + q + 0.5, 0.1, SNARE, 40)
            return
        for k in range(8):
            dr.note(b + k / 2, 0.1, SNARE, 70 if k % 2 == 0 else 50)
        dr.note(b + 1.75, 0.05, SNARE, 44)
        dr.note(b + 3.75, 0.05, SNARE, 44)
        dr.note(b, 0.2, KICK, 84)
        dr.note(b + 2, 0.2, KICK, 76)
        if fill:
            for k in range(8):
                dr.note(b + 2 + k / 4, 0.05, SNARE, 60 + 5 * k)

    bar = 0
    for i in range(4):  # intro: a snare cadence, the tuba and pizzicato join, horns call
        b = bar * 4
        snare_bar(b, fill=i == 3)
        if i >= 2:
            oompah(b, [Bb] if i == 2 else [F7], 84)
        bar += 1
    play(hrn, 8, mel("f4/.75 f4/.25 bb4/1 d5/2 | c5/.75 c5/.25 a4/1 f4/2"), 80, 0.9)
    dr.note(15, 1, CRASH, 50)

    def section_a(start, counter, loud):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            oompah(b, ch)
            snare_bar(b, fill=i == 7)
            if i in (0, 4):
                dr.note(b, 1, CRASH, 60)
        play(cla, start * 4, TUNE, 92 if loud else 86, 0.8, -12 if not loud else 0, 8)
        if loud:
            play(pic, start * 4, TUNE, 72, 0.7, 0, 6)
            play(glk, start * 4, [x for x in TUNE[0] if x[0] % 1 == 0], 50, 0.8, 12)
        if counter:
            play(bsn, start * 4, COUNTER, 84, 0.85)

    section_a(bar, False, False)
    bar += 8
    section_a(bar, True, True)
    bar += 8
    for i, ch in enumerate(TRIO):  # trio: legato clarinet in Eb, soft horns, brushed snare, lighter tuba
        b = (bar + i) * 4
        oompah(b, ch, 80)
        snare_bar(b, soft=True)
        for p in ch[0][1]:
            hrn.note(b, 3.9, p - 12 if p > 60 else p, 48)
        dr.note(b, 1, TRI, 40)
    play(cla, bar * 4, TRIO_TUNE, 94, 0.95)
    play(bsn, bar * 4, TRIO_TUNE, 60, 0.95, -24)
    play(glk, bar * 4 + 28, mel("f6/.5 d6/.5 bb5/.5 f5/.5 ab5/1 bb5/1"), 46, 0.8)
    bar += 8
    for i, ch in enumerate(C_PROG):  # C: xylophone runs and the piccolo call, the bassoon answers, busy snare
        b = (bar + i) * 4
        oompah(b, ch)
        snare_bar(b, fill=i == 7)
        for off, ln, (root, v) in chords_of(ch):
            notes = [v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24]
            for k in range(int(ln * 4)):
                xyl.note(b + off + k * 0.25, 0.2, notes[(k if (k // 4) % 2 == 0 else 3 - k) % 4], 56 + (14 if k % 4 == 0 else 0))
        dr.note(b + 1, 0.2, TAMB, 50)
        dr.note(b + 3, 0.2, TAMB, 56)
    play(pic, bar * 4, CALL, 88, 0.8)
    play(glk, bar * 4, CALL, 50, 0.8, -12)
    play(bsn, bar * 4, ANSWER, 100, 0.8)
    bar += 8
    section_a(bar, True, True)
    bar += 8
    for i, ch in enumerate([[Gm], [Cm], [F7], [F7]]):  # the turn back to the top: the cadence again, horns rise
        b = (bar + i) * 4
        oompah(b, ch, 88)
        snare_bar(b, fill=i == 3)
    play(hrn, bar * 4, mel("d4/1 g4/1 bb4/2 | eb4/1 g4/1 c5/2 | c5/.75 c5/.25 f5/1 eb5/2 | c5/2 a4/2"), 76, 0.9)
    play(cla, bar * 4 + 8, mel("f5/.5 g5/.5 a5/.5 bb5/.5 c6/.5 d6/.5 eb6/1 | c6/.25 d6/.25 c6/.25 a5/.25 f5/1 r/2"), 84, 0.8)
    bar += 4
    assert bar == 48
    return tracks, 128, bar


for name, fn in (("mossfolk_theme_a", theme_a), ("mossfolk_theme_b", theme_b), ("mossfolk_theme_c", theme_c)):
    tracks, bpm, bars = fn()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
