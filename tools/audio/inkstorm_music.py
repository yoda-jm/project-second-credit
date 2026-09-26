#!/usr/bin/env python3
"""Game 14 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Both pieces are our own.
- inkstorm_theme: an original, calm-but-tense folk-chamber loop in D minor (pizzicato strings, harp arpeggios,
  a flute tune, a clarinet answer, oboe and bassoon, a soft brush kit), over a low undercurrent: a contrabass
  pedal and tremolo strings that swell and ebb, and quiet timpani rolls.
  Form: intro 4 | A 8 | B 8 | A' 8 bars at 84 bpm (80 s), then it loops to the intro.
- inkstorm_tension: the same ensemble, faster and more urgent (112 bpm, 16 bars, 34 s), for when the claimed
  land is close to the target: a restless oboe motif, driving pizzicato, timpani on every beat, strings
  sawing in tremolo, a flat-two (E flat) turn before the loop.
Usage: python3 tools/audio/inkstorm_music.py
-> godot/games/inkstorm/audio/music/inkstorm_theme.ogg and inkstorm_tension.ogg (+ .mid)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop, TPB

OUT = "godot/games/inkstorm/audio/music/"
BRUSH_KIT = 40  # the brush kit on the drum channel
KICK, TAP, SLAP, SWIRL, STICK, PEDAL, SHAKER, TOM_L, TOM_M = 36, 38, 39, 40, 37, 44, 70, 45, 47

# chords as (bass root, voicing)
Dm, Bb, C, Am = (38, [62, 65, 69]), (34, [62, 65, 70]), (36, [64, 67, 72]), (33, [64, 69, 72])
Gm, A, F, Eb = (31, [62, 67, 70]), (33, [61, 64, 69]), (29, [65, 69, 72]), (39, [63, 67, 70])


def band():
    """The ensemble: flute, clarinet, oboe, pizzicato, harp, contrabass, tremolo strings, bassoon, timpani, brushes."""
    drums = Track(9, 0, 84, 64, 40)
    drums.events.append((0, bytes([0xC9, BRUSH_KIT])))
    return (Track(0, 73, 92, 70, 60),    # flute
            Track(1, 71, 88, 50, 55),    # clarinet
            Track(2, 68, 82, 80, 55),    # oboe
            Track(3, 45, 90, 44, 45),    # pizzicato strings
            Track(4, 46, 82, 88, 70),    # harp
            Track(5, 43, 82, 60, 50),    # contrabass pedal
            Track(6, 44, 60, 64, 70),    # tremolo strings (the undercurrent)
            Track(7, 70, 80, 56, 45),    # bassoon
            Track(8, 47, 84, 64, 60),    # timpani
            drums)


def play(track, start, line, vel, staccato=0.9, shift=0):
    for beat, length, pitch in line:
        track.note(start + beat, length * staccato, pitch + shift, vel)


def swell(track, beat, length, lo, hi, steps=16):
    """An expression (CC11) rise and fall over `length` beats: the strings breathing in and out."""
    for k in range(steps + 1):
        v = lo + (hi - lo) * (1 - abs(2 * k / steps - 1))
        track.events.append((int((beat + length * k / steps) * TPB), bytes([0xB0 | track.ch, 11, int(v)])))


def make_parts(pizz, harp, bass, trem, bsn, timp, drum):
    """The accompaniment as functions of a bar start (in beats) and a chord."""
    PIZZ = (0, 2, 1, 2, 0, 2, 1, 2)

    def pizz_bar(b, ch, vel=70, sixteenths=False, rest=True):
        v = [p - 12 for p in ch[1]] + [ch[1][0]]
        steps = 16 if sixteenths else 8
        for k in range(steps):
            if rest and not sixteenths and k == 7:
                continue  # a breath at the end of each bar
            q = k * 4 / steps
            pizz.note(b + q, 0.2, v[PIZZ[k % 8]] if k % 8 else ch[0] + 12, vel + (12 if k % 4 == 0 else 0))

    def harp_bar(b, ch, vel=58, dense=False):
        """A rolling arpeggio from the low octave up, falling back on the second half."""
        v = ch[1]
        notes = [v[0] - 12, v[1] - 12, v[2] - 12, v[0], v[1], v[2], v[0] + 12, v[2]]
        step = 0.25 if dense else 0.5
        for k in range(int(4 / step)):
            harp.note(b + k * step, 1.2, notes[k % 8], vel + (8 if k % 4 == 0 else 0))

    def bassoon_bar(b, ch, vel=66, walk=True):
        r = ch[0] + 12
        if walk:
            for q, p in ((0, r), (1.5, r + 7), (2, r + 12), (3, r + 7)):
                bsn.note(b + q, 0.9 if q != 1.5 else 0.45, p, vel)
        else:
            bsn.note(b, 3.8, r, vel)

    def groove(b, vel=54, busy=False):
        drum.note(b, 0.2, KICK, vel + 16)
        drum.note(b + 2.5, 0.2, KICK, vel + 6)
        for q in (1, 3):
            drum.note(b + q, 0.2, TAP, vel + 10)
        drum.note(b, 1.8, SWIRL, vel - 10)
        drum.note(b + 2, 1.8, SWIRL, vel - 14)
        for k in range(8 if not busy else 16):
            drum.note(b + k * (0.5 if not busy else 0.25), 0.05, SHAKER, (vel - 18) + (10 if k % 2 == 0 else 0))

    def roll(b, beats, pitch, v0, v1):
        """A timpani roll in 32nds, growing from v0 to v1."""
        m = int(beats * 8)
        for k in range(m):
            timp.note(b + k / 8, 0.12, pitch, int(v0 + (v1 - v0) * k / max(1, m - 1)))

    return pizz_bar, harp_bar, bassoon_bar, groove, roll


def theme():
    flute, clar, oboe, pizz, harp, bass, trem, bsn, timp, drum = band()
    pizz_bar, harp_bar, bassoon_bar, groove, roll = make_parts(pizz, harp, bass, trem, bsn, timp, drum)
    A_PROG = [Dm, Bb, C, Am, Dm, Bb, Gm, A]
    B_PROG = [Gm, Dm, Bb, F, Gm, Dm, Eb, A]
    INTRO = [Dm, Dm, Bb, A]

    # the A tune (flute): a lilting line that leans on the minor third and climbs to a questioning top
    A_TUNE = [(0, 1, 74), (1, .5, 77), (1.5, .5, 76), (2, 1.5, 74), (3.5, .5, 69),
              (4, 1.5, 77), (5.5, .5, 79), (6, 1, 77), (7, 1, 74),
              (8, 1, 76), (9, .5, 79), (9.5, .5, 84), (10, 1.5, 81), (11.5, .5, 79),
              (12, 3, 76), (15, .5, 72), (15.5, .5, 76),
              (16, 1, 74), (17, .5, 77), (17.5, .5, 81), (18, 1.5, 86), (19.5, .5, 84),
              (20, 1, 82), (21, 1, 81), (22, 1.5, 77), (23.5, .5, 74),
              (24, 1, 79), (25, .5, 82), (25.5, .5, 81), (26, 1, 79), (27, 1, 77),
              (28, 1.5, 76), (29.5, .5, 73), (30, 2, 76)]
    # the B tune (clarinet): lower and longer, darkening on the E flat
    B_TUNE = [(0, 2, 67), (2, 1, 70), (3, 1, 74), (4, 3, 69), (7, 1, 65),
              (8, 2, 70), (10, 1, 74), (11, 1, 77), (12, 3, 72), (15, 1, 69),
              (16, 2, 70), (18, 1, 74), (19, 1, 79), (20, 2, 77), (22, 2, 74),
              (24, 1.5, 75), (25.5, .5, 74), (26, 2, 70), (28, 2, 73), (30, 2, 69)]
    # the flute's sparse high answers in B, and the oboe's little call in the intro
    B_ANSWER = [(3, .5, 86), (3.5, .5, 84), (7, 1, 81), (11, .5, 89), (11.5, .5, 86), (15, 1, 84),
                (19, .5, 86), (19.5, .5, 82), (23, 1, 81), (27, .5, 82), (27.5, .5, 79), (31, 1, 76)]
    CALL = [(4, .5, 69), (4.5, .5, 72), (5, 1.5, 74), (6.5, .5, 72), (7, 1, 69),
            (12, .5, 69), (12.5, .5, 70), (13, 1, 73), (14, 2, 76)]

    bar = 0
    # the undercurrent under the whole loop: a contrabass pedal and low tremolo strings breathing in and out
    for sec_start, bars, pedal in ((0, 4, 38), (4, 8, 38), (12, 8, 31), (20, 8, 38)):
        for k in range(0, bars, 2):
            bass.note((sec_start + k) * 4, 7.9, pedal, 70)
        for k in range(0, bars, 4):
            b = (sec_start + k) * 4
            swell(trem, b, 16, 30, 90 if sec_start == 12 else 70)
            trem.note(b, 15.9, pedal + 12, 64)
            trem.note(b, 15.9, pedal + 19, 52)

    # intro: harp and pizzicato alone, the oboe calls, a timpani roll leans into A
    for i, ch in enumerate(INTRO):
        b = (bar + i) * 4
        harp_bar(b, ch, 50 + 4 * i)
        if i >= 1:
            pizz_bar(b, ch, 58 + 4 * i)
        if i == 0:
            timp.note(b, 1, 38, 70)
    play(oboe, 0, CALL, 70)
    roll(12, 2, 33, 30, 76)
    bar += 4

    # A: the flute tune over pizzicato, bassoon walking, soft brushes
    for i, ch in enumerate(A_PROG):
        b = (bar + i) * 4
        pizz_bar(b, ch, 66)
        bassoon_bar(b, ch, 62)
        groove(b, 50)
        if i in (0, 4):
            timp.note(b, 1, 38, 66)
        if i % 2 == 1:
            harp_bar(b, ch, 44)
    play(flute, bar * 4, A_TUNE, 84)
    bar += 8

    # B: the clarinet sings low, harp rolling in sixteenths, the flute answers high, the strings rise
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        harp_bar(b, ch, 50, dense=True)
        pizz_bar(b, ch, 58, rest=i != 7)
        bassoon_bar(b, ch, 58, walk=False)
        groove(b, 46)
        if i in (0, 4):
            timp.note(b, 1, ch[0] + 12 if ch[0] < 36 else ch[0], 70)
    play(clar, bar * 4, B_TUNE, 86, 0.95)
    play(flute, bar * 4, B_ANSWER, 64, 0.8)
    roll(bar * 4 + 28, 4, 33, 34, 84)
    bar += 8

    # A': the tune in flute and oboe an octave apart, the clarinet sustains, busier brushes, then the A chord
    for i, ch in enumerate(A_PROG):
        b = (bar + i) * 4
        pizz_bar(b, ch, 72)
        bassoon_bar(b, ch, 66)
        harp_bar(b, ch, 48)
        groove(b, 56, busy=i >= 4)
        clar.note(b, 3.8, ch[1][1], 50)
        if i in (0, 4):
            timp.note(b, 1, 38, 72)
    play(flute, bar * 4, A_TUNE, 88)
    play(oboe, bar * 4, A_TUNE, 62, 0.9, -12)
    roll(bar * 4 + 30, 2, 33, 28, 60)
    bar += 8
    assert bar == 28
    return [flute, clar, oboe, pizz, harp, bass, trem, bsn, timp, drum], 84, bar


def tension():
    flute, clar, oboe, pizz, harp, bass, trem, bsn, timp, drum = band()
    pizz_bar, harp_bar, bassoon_bar, groove, roll = make_parts(pizz, harp, bass, trem, bsn, timp, drum)
    PROG = [Dm, Bb, Gm, A]
    MOTIF = {  # a restless eighth-note figure per chord (keyed by its bass root), up to the top and back
        38: [(0, .5, 74), (.5, .5, 77), (1, .5, 81), (1.5, .5, 77), (2, .75, 86), (2.75, .25, 84), (3, .5, 81), (3.5, .5, 77)],
        34: [(0, .5, 74), (.5, .5, 77), (1, .5, 82), (1.5, .5, 77), (2, .75, 86), (2.75, .25, 84), (3, .5, 82), (3.5, .5, 81)],
        31: [(0, .5, 79), (.5, .5, 82), (1, .5, 86), (1.5, .5, 82), (2, .75, 79), (2.75, .25, 77), (3, .5, 74), (3.5, .5, 79)],
        33: [(0, 1, 76), (1, .5, 73), (1.5, .5, 76), (2, 1, 81), (3, .25, 79), (3.25, .25, 77), (3.5, .25, 76), (3.75, .25, 73)],
    }

    def urgent_bar(b, ch, vel, busy):
        pizz_bar(b, ch, vel, sixteenths=busy, rest=False)
        for q in range(4):  # the timpani on every beat, on the root
            timp.note(b + q, 0.4, 38 if ch[0] in (38, 34, 39) else 33, 62 + (14 if q == 0 else 0))
            bass.note(b + q, 0.45, ch[0], 84)
        for q in (0, 1.5, 2, 3):
            drum.note(b + q, 0.2, KICK if q in (0, 2) else TOM_L, 74)
        for q in (1, 3):
            drum.note(b + q, 0.2, SLAP, 70)
        for k in range(16):
            drum.note(b + k / 4, 0.05, SHAKER, 40 + (12 if k % 2 == 0 else 0))
        bsn.note(b, 1.9, ch[0] + 12, 72)
        bsn.note(b + 2, 1.9, ch[0] + 19, 66)

    # the undercurrent: tremolo strings on the chord, swelling each bar
    for bar in range(16):
        ch = (PROG * 3 + [Eb, Eb, A, A])[bar]
        b = bar * 4
        swell(trem, b, 4, 50, 110 if bar >= 12 else 92, 8)
        for p in ch[1]:
            trem.note(b, 3.95, p - 12, 70)

    # three rounds of the four-bar motif: oboe alone, then flute doubling, then clarinet runs and dense harp
    for rep in range(3):
        for i, ch in enumerate(PROG):
            b = (rep * 4 + i) * 4
            urgent_bar(b, ch, 66 + 4 * rep, rep >= 1)
            if rep >= 2:
                harp_bar(b, ch, 52, dense=True)
            play(oboe, b, MOTIF[ch[0]], 80 + 4 * rep, 0.8)
            if rep >= 1:
                play(flute, b, MOTIF[ch[0]], 72 + 4 * rep, 0.75, 12)
            if rep == 2:
                play(clar, b, [(k * 0.25, 0.25, ch[1][k % 3] - 12 + 12 * (k // 3 % 2)) for k in range(16)], 60, 0.8)

    # the turn: an ominous flat-two chord held under a high trill, then A pulling back to D minor
    for i, ch in enumerate((Eb, Eb, A, A)):
        b = (12 + i) * 4
        urgent_bar(b, ch, 80, True)
        harp_bar(b, ch, 56, dense=True)
    play(oboe, 48, [(0, 3, 82), (3, 1, 79), (4, 2, 82), (6, 2, 86)], 90, 0.95)
    play(flute, 48, [(k * 0.25, 0.25, 94 if k % 2 == 0 else 93) for k in range(32)], 60, 0.9)
    play(oboe, 56, [(0, .5, 81), (.5, .5, 79), (1, .5, 77), (1.5, .5, 76), (2, 2, 73)], 90)
    run = [(k * 0.25, 0.25, p) for k, p in enumerate((69, 70, 72, 73, 74, 76, 77, 79, 81, 82, 84, 85, 86, 88, 89, 91))]
    play(flute, 60, run, 80, 0.85)
    play(clar, 60, run, 64, 0.85, -12)
    roll(56, 8, 33, 50, 100)
    return [flute, clar, oboe, pizz, harp, bass, trem, bsn, timp, drum], 112, 16


for name, song in (("inkstorm_theme", theme), ("inkstorm_tension", tension)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
