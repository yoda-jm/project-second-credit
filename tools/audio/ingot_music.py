#!/usr/bin/env python3
"""Game 10 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0.
- ingot_theme: an original, adventurous temple-mine chase loop in D minor with a harmonic-minor and Phrygian
  colour (ocarina lead, pizzicato ostinato in 3-3-2, marimba, kalimba, low flute, string pad, acoustic bass,
  hand drums: congas, bongos, shaker, claves and a big low tom).
  Form: intro 4 | A 8 | B 8 | A 8 | drum break 4 | bridge 8 | A 8 bars, then it loops to the intro.
Usage: python3 tools/audio/ingot_music.py
-> godot/games/ingot/audio/music/ingot_theme.ogg (+ .mid)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/ingot/audio/music/"
KICK, TOM_L, TOM_F, CHINA, TAMB = 36, 45, 41, 52, 54
BONGO_HI, BONGO_LO, CONGA_MUTE, CONGA_HI, CONGA_LO, SHAKER, CLAVES = 60, 61, 62, 63, 64, 70, 75

# chords as (bass root, voicing); a bar may hold two chords, two beats each
Dm, Bb, C, A, Gm, F, Eb = ((38, [62, 65, 69]), (34, [62, 65, 70]), (36, [60, 64, 67]), (33, [61, 64, 69]),
                           (43, [62, 67, 70]), (41, [60, 65, 69]), (39, [63, 67, 70]))


def chords_of(bar):
    """(beat offset, length, chord) for each chord in a bar."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    """A fresh set of tracks: ocarina, pizzicato, marimba, bass, strings, low flute, kalimba, hand drums."""
    return (Track(0, 79, 92, 60, 55),    # ocarina lead
            Track(1, 45, 84, 40, 40),    # pizzicato strings
            Track(2, 12, 80, 88, 45),    # marimba
            Track(3, 32, 104, 64, 15),   # acoustic bass
            Track(4, 48, 52, 64, 70),    # string pad
            Track(5, 73, 86, 76, 60),    # low flute
            Track(6, 108, 74, 30, 50),   # kalimba
            Track(9, 0, 100, 64, 30))


def play(track, start, line, vel, staccato=0.75, shift=0):
    for beat, length, pitch in line:
        track.note(start + beat, length * staccato, pitch + shift, vel)


def theme():
    oca, pizz, mar, bass, pad, flute, kal, drum = band()
    A_PROG = [[Dm], [Dm], [Bb], [A], [Dm], [Gm], [Bb, A], [Dm]]
    B_PROG = [[Gm], [Dm], [Eb], [A], [Gm], [Bb], [Eb], [A]]
    BRIDGE = [[Dm], [C], [Bb], [A], [Dm], [C], [Eb], [A]]

    # the hook: a running, climbing ocarina tune, 8 bars
    HOOK = [(0, .5, 74), (.5, .5, 77), (1, .5, 81), (1.5, .5, 79), (2, 1, 77), (3, .5, 76), (3.5, .5, 74),
            (4, .75, 76), (4.75, .75, 77), (5.5, .5, 76), (6, 1.5, 74), (7.5, .5, 69),
            (8, .5, 70), (8.5, .5, 74), (9, .5, 77), (9.5, .5, 79), (10, 1, 82), (11, .5, 81), (11.5, .5, 79),
            (12, .5, 81), (12.5, .5, 79), (13, .5, 77), (13.5, .5, 76), (14, 1.5, 73), (15.5, .5, 76),
            (16, .5, 74), (16.5, .5, 77), (17, .5, 81), (17.5, .5, 86), (18, 1, 84), (19, .5, 82), (19.5, .5, 81),
            (20, .75, 79), (20.75, .75, 82), (21.5, .5, 81), (22, 1, 79), (23, .5, 77), (23.5, .5, 79),
            (24, .5, 81), (24.5, .5, 82), (25, 1, 77), (26, .5, 76), (26.5, .5, 77), (27, 1, 73),
            (28, 2, 74), (30.5, .5, 69), (31, .5, 73), (31.5, .5, 76)]
    # the B tune: long, singing notes; the Eb chords give it the old-temple colour
    B_TUNE = [(0, 1.5, 79), (1.5, .5, 82), (2, 1, 86), (3, 1, 84),
              (4, 1.5, 81), (5.5, .5, 77), (6, 2, 74),
              (8, 1.5, 75), (9.5, .5, 79), (10, 1, 82), (11, 1, 79),
              (12, 1, 81), (13, 1, 76), (14, 1, 73), (15, 1, 76),
              (16, 1.5, 79), (17.5, .5, 82), (18, 1, 86), (19, 1, 87),
              (20, 1.5, 86), (21.5, .5, 82), (22, 2, 77),
              (24, 1, 79), (25, 1, 82), (26, 1, 87), (27, 1, 86),
              (28, 1, 85), (29, 1, 81), (30, 2, 76)]
    # the bridge: a low, mysterious flute line over kalimba arpeggios
    BRIDGE_LINE = [(0, 2, 74), (2, 2, 77), (4, 3, 76), (7, 1, 72), (8, 2, 74), (10, 2, 70), (12, 4, 73),
                   (16, 2, 74), (18, 2, 77), (20, 2, 79), (22, 2, 81), (24, 3, 79), (27, 1, 75), (28, 4, 76)]
    BASS_332 = [(0, .9, 0), (1.5, .4, 0), (2, .4, 12), (3, .4, 0), (3.5, .4, 7)]

    def bass_bar(b, bar, busy=True):
        for off, ln, (root, _) in chords_of(bar):
            for beat, length, iv in BASS_332:
                if off <= beat < off + ln and (busy or beat in (0, 1.5, 3)):
                    bass.note(b + beat, length, root + iv, 108 if beat in (0, 1.5, 3) else 86)

    def pizz_bar(b, bar, vel=74):
        """The driving ostinato: eighths on the chord, accents in 3-3-2."""
        for off, ln, (_, v) in chords_of(bar):
            pat = [v[0], v[2], v[1], v[0] + 12, v[2], v[1], v[0] + 12, v[2]]
            for k in range(int(ln * 2)):
                q = off + k * 0.5
                pizz.note(b + q, 0.3, pat[int(q * 2)] - 12, vel + (14 if q in (0, 1.5, 3) else 0))

    def pad_bar(b, bar, vel=56):
        for off, ln, (_, v) in chords_of(bar):
            for p in v:
                pad.note(b + off, ln - 0.05, p - 12, vel)

    def hands(b, fill=False, big=False, tamb=False, sparse=False):
        """Hand drums: a conga pattern in 3-3-2, bongo chatter, shaker sixteenths, claves on the offbeats."""
        if big:
            drum.note(b, 1, CHINA, 70)
            drum.note(b, 0.5, TOM_F, 110)
        for k in range(16):
            if fill and k >= 8:
                continue
            drum.note(b + k / 4, 0.05, SHAKER, 58 if k % 2 == 0 else 38)
        drum.note(b, 0.2, KICK, 96)
        drum.note(b + 2.5, 0.2, KICK, 80)
        for q, p, v in ((0, CONGA_LO, 100), (1, CONGA_MUTE, 78), (1.5, CONGA_LO, 92), (2, CONGA_HI, 88),
                        (3, CONGA_LO, 96), (3.5, CONGA_HI, 84)):
            if not (fill and q >= 2):
                drum.note(b + q, 0.2, p, v)
        if not sparse:
            for q in (0.75, 1.25, 2.75, 3.25):
                if not (fill and q >= 2):
                    drum.note(b + q, 0.1, BONGO_HI, 64)
            for q in (1, 3):
                if not (fill and q == 3):
                    drum.note(b + q, 0.1, CLAVES, 72)
        if tamb:
            for q in (0.5, 1.5, 2.5, 3.5):
                drum.note(b + q, 0.1, TAMB, 56)
        if fill:  # bongos and congas tumble into the next section, the low tom lands it
            for i, p in enumerate((BONGO_HI, BONGO_HI, BONGO_LO, BONGO_LO, CONGA_HI, CONGA_HI, CONGA_LO, TOM_L)):
                drum.note(b + 2 + i * 0.25, 0.2, p, 78 + i * 4)

    bar = 0
    # intro (4 bars): the pizzicato ostinato and the pad alone, then the drums; the marimba hints at the hook
    for i, ch in enumerate(A_PROG[:4]):
        b = bar * 4
        pizz_bar(b, ch, 66)
        pad_bar(b, ch, 50)
        if i == 0:
            drum.note(b, 1, TOM_F, 104)
            drum.note(b, 1, CHINA, 60)
        if i >= 1:
            bass_bar(b, ch, busy=False)
        if i >= 2:
            hands(b, sparse=i == 2, fill=i == 3)
        else:
            for k in range(8):
                drum.note(b + k / 2, 0.05, SHAKER, 46 if k % 2 == 0 else 30)
        bar += 1
    play(mar, 8, HOOK[:12], 70, 0.8)

    def section_a(start_bar, lead_vel, full):
        for i, ch in enumerate(A_PROG):
            b = (start_bar + i) * 4
            bass_bar(b, ch)
            pizz_bar(b, ch)
            if full:
                pad_bar(b, ch, 52)
            hands(b, big=i in (0, 4), fill=i == 7, tamb=full and i >= 4)
        play(oca, start_bar * 4, HOOK, lead_vel, 0.85)
        if full:  # the marimba doubles the hook an octave down, bouncy and short
            play(mar, start_bar * 4, HOOK, 68, 0.5, -12)

    section_a(bar, 96, False)
    bar += 8

    # B: the ocarina sings long notes, the marimba answers in running eighths, the pad swells
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        bass_bar(b, ch)
        pizz_bar(b, ch, 68)
        pad_bar(b, ch, 60)
        hands(b, big=i in (0, 4), fill=i == 7, tamb=True)
        v = ch[0][1]
        run = [v[0], v[1], v[2], v[0] + 12, v[1] + 12, v[0] + 12, v[2], v[1]]
        for k in range(8):
            if k >= 4 or i % 2 == 1:
                mar.note(b + k * 0.5, 0.35, run[k] + 12, 62 + (10 if k % 2 == 0 else 0))
    play(oca, bar * 4, B_TUNE, 98, 0.95)
    bar += 8

    section_a(bar, 100, True)
    bar += 8

    # break (4 bars): stop-time; the low tom and bass hit the downbeats, hand drums chatter, ocarina echoes climb
    for i in range(4):
        b = (bar + i) * 4
        root, voicing = (Dm, Dm, Eb, A)[i]
        bass.note(b, 0.8, root, 112)
        for p in voicing:
            pizz.note(b, 0.3, p - 12, 96)
            pad.note(b, 1.5, p - 12, 60)
        drum.note(b, 0.5, TOM_F, 116)
        drum.note(b, 1, CHINA, 64 if i else 84)
        if i < 3:
            for q, p in ((1, BONGO_HI), (1.25, BONGO_HI), (1.5, BONGO_LO), (2, CONGA_HI), (2.5, CONGA_LO),
                         (2.75, CONGA_MUTE), (3, CLAVES), (3.5, BONGO_LO)):
                drum.note(b + q, 0.1, p, 82)
            play(oca, b, [(2.5, .5, 74 + 3 * i), (3, .5, 77 + 3 * i), (3.5, .5, 81 + 3 * i)], 84, 0.6)
        else:
            for k in range(16):  # a hand-drum roll up to the bridge
                drum.note(b + k / 4, 0.1, (CONGA_LO, CONGA_HI, BONGO_LO, BONGO_HI)[k // 4], 60 + k * 3)
    bar += 4

    # bridge: the low flute over kalimba arpeggios, the pizzicato steps back, the drums build
    for i, ch in enumerate(BRIDGE):
        b = (bar + i) * 4
        bass_bar(b, ch, busy=i >= 4)
        pad_bar(b, ch, 58)
        if i >= 4:
            pizz_bar(b, ch, 60)
        hands(b, big=i in (0, 4), fill=i == 7, sparse=i < 4, tamb=i >= 4)
        v = ch[0][1]
        arp = [v[0], v[1], v[2], v[0] + 12, v[2], v[1]] * 2
        for k in range(8):
            kal.note(b + k * 0.5, 0.45, arp[k] + 12, 66 + (10 if k % 2 == 0 else 0))
    play(flute, bar * 4, BRIDGE_LINE, 100, 0.95, -12)
    play(oca, bar * 4 + 16, BRIDGE_LINE[7:], 70, 0.95)
    bar += 8

    section_a(bar, 104, True)
    bar += 8
    assert bar == 48
    return [oca, pizz, mar, bass, pad, flute, kal, drum], 128, bar


for name, song in (("ingot_theme", theme),):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
