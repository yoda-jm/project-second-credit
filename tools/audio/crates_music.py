#!/usr/bin/env python3
"""Game 11 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0.
- crates_theme: an original, calm and cosy harbour-warehouse loop in G major to think along to (clarinet lead,
  a whistled answer, nylon guitar picking, accordion and reed-organ chords, upright bass, brushes, a ship's bell).
  Form: intro 4 | A 8 | B 8 | A' 8 | turnaround 4 bars at 76 bpm (about 101 s), then it loops to the intro.
Usage: python3 tools/audio/crates_music.py
-> godot/games/crates/audio/music/crates_theme.ogg (+ .mid)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/crates/audio/music/"
BRUSH_KIT = 40  # the brush kit on the drum channel
KICK, BRUSH_TAP, BRUSH_SLAP, BRUSH_SWIRL, RIDE, TRIANGLE = 36, 38, 39, 40, 51, 81

# chords as (bass root, guitar voicing); a bar may hold two chords, two beats each
G, Em, C, D, Bm, Am, D7, Cmaj7 = ((43, [55, 59, 62, 67]), (40, [52, 59, 64, 67]), (36, [48, 55, 60, 64]),
                                  (38, [50, 57, 62, 66]), (35, [54, 59, 62, 66]), (45, [52, 57, 60, 64]),
                                  (38, [50, 57, 60, 66]), (36, [48, 55, 59, 64]))


def chords_of(bar):
    """(beat offset, length, chord) for each chord in a bar."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    """A fresh set of tracks: clarinet, whistle, guitar, accordion, bass, reed organ, ship's bell, brushes."""
    drums = Track(9, 0, 84, 64, 45)
    drums.events.append((0, bytes([0xC9, BRUSH_KIT])))
    return (Track(0, 71, 92, 58, 60),    # clarinet lead
            Track(1, 78, 70, 76, 70),    # whistle
            Track(2, 24, 92, 44, 45),    # nylon guitar
            Track(3, 21, 56, 84, 55),    # accordion
            Track(4, 32, 100, 64, 25),   # upright (acoustic) bass
            Track(5, 20, 50, 64, 70),    # reed organ, the harmonium pad
            Track(6, 14, 62, 90, 90),    # tubular bell, the ship's bell
            drums)


def play(track, start, line, vel, legato=0.92, shift=0):
    for beat, length, pitch in line:
        track.note(start + beat, length * legato, pitch + shift, vel)


def theme():
    cla, whistle, gtr, acc, bass, organ, bell, drum = band()
    INTRO = [[G], [Cmaj7], [G], [D]]
    A_PROG = [[G], [Em], [C], [D], [G], [Bm], [C, D], [G]]
    B_PROG = [[Em], [C], [G], [D], [Em], [Am], [C], [D]]
    TURN = [[C], [G], [Am], [D7]]

    # the A tune: an unhurried, rocking clarinet line, 8 bars
    A_TUNE = [(0, 1.5, 71), (1.5, .5, 72), (2, 1, 74), (3, 1, 71),
              (4, 1.5, 67), (5.5, .5, 69), (6, 2, 71),
              (8, 1.5, 72), (9.5, .5, 71), (10, 1, 69), (11, 1, 72),
              (12, 3, 69), (15, 1, 66),
              (16, 1.5, 71), (17.5, .5, 72), (18, 1, 74), (19, 1, 79),
              (20, 1.5, 78), (21.5, .5, 76), (22, 2, 74),
              (24, 1, 76), (25, 1, 72), (26, 1, 74), (27, 1, 69),
              (28, 3.5, 67)]
    # the B tune: it climbs a little and looks out to sea, then settles on D to lead home
    B_TUNE = [(0, 2, 76), (2, 1, 79), (3, 1, 78),
              (4, 2, 76), (6, 1, 72), (7, 1, 74),
              (8, 3, 74), (11, 1, 71),
              (12, 2, 69), (14, 1, 71), (15, 1, 72),
              (16, 2, 76), (18, 1, 79), (19, 1, 83),
              (20, 2, 81), (22, 1, 79), (23, 1, 76),
              (24, 2, 79), (26, 1, 76), (27, 1, 72),
              (28, 3, 74), (31, 1, 62)]
    # the whistled answers in the A section's long notes
    ANSWERS = [(13, .5, 78), (13.5, .5, 81), (14, 1, 79), (29, .5, 74), (29.5, .5, 76), (30, 1.5, 79)]
    TURN_LINE = [(0, 1, 76), (1, 1, 74), (2, 2, 72), (4, 1.5, 71), (5.5, .5, 72), (6, 2, 74),
                 (8, 1, 72), (9, 1, 71), (10, 2, 69), (12, 2, 66), (14, 1, 69), (15, 1, 74)]
    PICK = [0, 2, 1, 3, 0, 2, 1, 2]  # which voicing note each eighth plays; 0 is the thumb

    def guitar_bar(b, bar, vel=64):
        for off, ln, (_, v) in chords_of(bar):
            for k in range(int(ln * 2)):
                q = off + k * 0.5
                i = PICK[int(q * 2)]
                gtr.note(b + q + 0.012 * (k % 2), 1.0 if i == 0 else 0.7, v[i], vel + (10 if i == 0 else 0))

    def bass_bar(b, bar, walk=False):
        for off, ln, (root, _) in chords_of(bar):
            bass.note(b + off, min(ln, 2) - 0.2, root, 96)
            if ln == 4:
                bass.note(b + 2, 1.6 if not walk else 0.9, root + 7, 84)
                if walk:
                    bass.note(b + 3, 0.9, root + 9, 76)

    def chord_bar(track, b, bar, vel, octave=0):
        for off, ln, (_, v) in chords_of(bar):
            for p in v[1:]:
                track.note(b + off, ln - 0.08, p + octave, vel)

    def brushes(b, swirl=True, taps=True, fill=False):
        """Brushes: a swirl on each half bar, soft taps on 2 and 4, a whisper of a kick on 1."""
        drum.note(b, 0.3, KICK, 50)
        if swirl:
            drum.note(b, 1.9, BRUSH_SWIRL, 52)
            drum.note(b + 2, 1.9, BRUSH_SWIRL, 44)
        if taps:
            drum.note(b + 1, 0.2, BRUSH_TAP, 58)
            drum.note(b + 3, 0.2, BRUSH_SLAP if fill else BRUSH_TAP, 62 if fill else 56)
            drum.note(b + 2.5 + 1 / 6, 0.1, BRUSH_TAP, 34)  # a little swung ghost
        if fill:
            for k, q in enumerate((3.5, 3.5 + 1 / 6, 3.5 + 2 / 6)):
                drum.note(b + q, 0.1, BRUSH_TAP, 40 + 8 * k)

    def ship_bell(b, vel=48):
        bell.note(b, 3.5, 67, vel)
        bell.note(b + 0.5, 3, 67, vel - 18)

    bar = 0
    # intro (4 bars): the guitar alone, a distant ship's bell, the reed organ and bass creep in
    ship_bell(0)
    for i, ch in enumerate(INTRO):
        b = bar * 4
        guitar_bar(b, ch, 58)
        if i >= 1:
            chord_bar(organ, b, ch, 40)
        if i >= 2:
            bass_bar(b, ch)
            brushes(b, taps=i == 3)
        bar += 1

    def section_a(start, lead, answer, full):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            guitar_bar(b, ch, 62)
            bass_bar(b, ch, walk=i in (3, 7))
            chord_bar(organ, b, ch, 44)
            if full:
                chord_bar(acc, b, ch, 40)
            brushes(b, fill=i == 7)
        play(lead, start * 4, A_TUNE, 88)
        play(answer, start * 4, ANSWERS, 60)

    section_a(bar, cla, whistle, False)
    bar += 8

    # B: the whistle takes the tune, the clarinet sings a low counterline, the accordion breathes the chords
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        guitar_bar(b, ch, 60)
        bass_bar(b, ch, walk=i in (3, 7))
        chord_bar(acc, b, ch, 48)
        brushes(b, fill=i == 7)
        v = ch[0][1]
        cla.note(b, 1.9, v[2], 60)
        cla.note(b + 2, 1.9, v[1] + (12 if v[1] < 55 else 0), 56)
        if i == 4:
            drum.note(b, 2, TRIANGLE, 30)
    play(whistle, bar * 4, B_TUNE, 76)
    bar += 8

    # A': the tune comes home on the clarinet, with the accordion; a ship's bell marks the start
    ship_bell(bar * 4, 40)
    section_a(bar, cla, whistle, True)
    bar += 8

    # turnaround (4 bars): the accordion hums a falling line, the band thins out, the D7 leads to the intro
    for i, ch in enumerate(TURN):
        b = (bar + i) * 4
        guitar_bar(b, ch, 56)
        bass_bar(b, ch, walk=i == 3)
        chord_bar(organ, b, ch, 40)
        brushes(b, taps=i < 3)
    play(acc, bar * 4, TURN_LINE, 56, 0.9)
    play(cla, bar * 4 + 12, [(0, 2, 66), (2, 2, 69)], 52)
    bar += 4
    assert bar == 32
    return [cla, whistle, gtr, acc, bass, organ, bell, drum], 76, bar


for name, song in (("crates_theme", theme),):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
