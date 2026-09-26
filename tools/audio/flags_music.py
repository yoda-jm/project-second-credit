#!/usr/bin/env python3
"""Game 8 theme: an original, cheeky funk-rock battle march in D dorian (slap bass, brass stabs, crunchy guitar,
square lead, trumpet, funk drums with military snare rolls), written as code and rendered with FluidSynth.
Form: intro 4 | A 8 | B 8 | A 8 | drum break 4 | bridge 8 | A 8 bars, then it loops to the intro.
Usage: python3 tools/audio/flags_music.py -> godot/games/flags/audio/music/flags_theme.ogg. Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 116, 48
lead = Track(0, 80, 78, 72, 45)    # square lead
bass = Track(1, 36, 100, 64, 20)   # slap bass
brass = Track(2, 61, 86, 52, 45)   # brass section
gtr = Track(3, 29, 64, 34, 30)     # overdriven guitar
tpt = Track(4, 56, 80, 88, 50)     # trumpet
drum = Track(9, 0, 96, 64, 25)
KICK, SNARE, HAT, OPEN, CRASH, TOM_L, TOM_M, TOM_H = 36, 38, 42, 46, 49, 45, 47, 50

# chords as (bass root, brass voicing); a bar may hold two chords, two beats each
Dm, G, Bb, C, A, F = ((38, [62, 65, 69, 72]), (43, [62, 67, 71, 74]), (46, [62, 65, 70, 74]),
                      (36, [60, 64, 67, 72]), (45, [61, 64, 69, 73]), (41, [60, 65, 69, 72]))
A_PROG = [[Dm], [Dm], [G], [Bb, C], [Dm], [Dm], [G], [Bb, C]]
B_PROG = [[Bb], [C], [Dm], [Dm], [Bb], [C], [A], [A]]
BRIDGE = [[F], [C], [G], [A], [F], [C], [G], [A, A]]

# the hook (8 bars, beats from the start of the section)
HOOK = [(0, .5, 74), (.5, .5, 77), (1, .25, 79), (1.5, .5, 81), (2.5, .5, 79), (3, .5, 77), (3.5, .5, 74),
        (4, .75, 81), (5, .5, 84), (5.5, .25, 81), (6, 1.5, 79),
        (8, .5, 83), (8.5, .5, 81), (9, .5, 79), (9.5, .5, 77), (10, 1, 79), (11, .5, 74), (11.5, .5, 71),
        (12, 1, 74), (13, .5, 77), (14, .5, 79), (14.5, .5, 76), (15, 1, 79),
        (16, .5, 74), (16.5, .5, 77), (17, .25, 79), (17.5, .5, 81), (18.5, .5, 79), (19, .5, 77), (19.5, .5, 74),
        (20, .75, 81), (21, .5, 84), (21.5, .25, 81), (22, 1.5, 86),
        (24, .5, 83), (24.5, .5, 84), (25, 1, 86), (26, .5, 84), (26.5, .5, 83), (27, 1, 81),
        (28, .5, 77), (28.5, .5, 79), (29, .5, 77), (29.5, .5, 76), (30, 1.75, 74)]
# the B section: brass calls, the lead answers
B_CALL = [(0, .25), (.5, .25), (1.5, .5)]
B_ANSWER = [(2.5, .5, 77), (3, .5, 79), (3.5, .5, 81), (6.5, .5, 81), (7, .5, 79), (7.5, .5, 77),
            (10.5, .5, 81), (11, .5, 84), (11.5, .5, 86), (12, 2, 81), (14, .5, 77), (14.5, .5, 79), (15, 1, 81)]
# the bridge: a heroic trumpet line
BRIDGE_LINE = [(0, 1.5, 72), (1.5, .5, 77), (2, 2, 81), (4, 1.5, 79), (5.5, .5, 76), (6, 2, 72),
               (8, 1.5, 74), (9.5, .5, 79), (10, 2, 83), (12, 3.5, 85),
               (16, 1.5, 77), (17.5, .5, 81), (18, 2, 84), (20, 1.5, 84), (21.5, .5, 83), (22, 2, 79),
               (24, 1, 79), (25, 1, 83), (26, 2, 86), (28, 2, 85), (30, 1.5, 81)]
BASS_RIFF = [(0, .4, 0), (.75, .2, 0), (1, .3, 12), (1.5, .4, 0), (2.25, .2, 0), (2.5, .4, 10), (3, .3, 7), (3.5, .4, 5)]


def chords_of(bar):
    """(beat offset, length, chord) for each chord in a bar."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def bass_bar(b, bar, busy=True):
    for off, ln, (root, _) in chords_of(bar):
        for beat, length, iv in BASS_RIFF:
            if off <= beat < off + ln and (busy or beat in (0, 1.5, 2.5)):
                bass.note(b + beat, length, root + iv, 104 if beat in (0, 2) else 86)


def groove(b, fill=False, crash=False, ghosts=True):
    if crash:
        drum.note(b, 1, CRASH, 100)
    for k in range(16):
        q = k / 4
        if fill and q >= 2:
            continue
        drum.note(b + q, 0.1, OPEN if k == 14 else HAT, 72 if k % 2 == 0 else 48)
    for q in (0, .75, 2.5):
        drum.note(b + q, 0.2, KICK, 108)
    drum.note(b + 1, 0.2, SNARE, 104)
    if ghosts:
        for q in (1.75, 2.25):
            drum.note(b + q, 0.1, SNARE, 40)
    if fill:  # a tom run into the next section
        for i, p in enumerate((SNARE, SNARE, TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_L)):
            drum.note(b + 2 + i * 0.25, 0.2, p, 80 + i * 4)
    else:
        drum.note(b + 3, 0.2, SNARE, 104)
        if ghosts:
            drum.note(b + 3.75, 0.1, SNARE, 45)


def march_roll(b, bar_index):
    """A military snare cadence for the break: flams on the beats, a crescendo roll at the end."""
    drum.note(b, 0.2, KICK, 100)
    drum.note(b + 2, 0.2, KICK, 90)
    if bar_index < 3:
        for k in range(8):
            drum.note(b + k * 0.5, 0.1, SNARE, 95 if k % 2 == 0 else 62)
        for k in (1, 3):
            drum.note(b + k + 0.25, 0.08, SNARE, 50)
            drum.note(b + k + 0.375, 0.08, SNARE, 55)
    else:
        for k in range(32):
            drum.note(b + k * 0.125, 0.06, SNARE, 45 + k * 2)


def brass_stabs(b, bar, pattern=((1.5, .2), (2.75, .2), (3.5, .3)), vel=92):
    for off, ln, (_, voicing) in chords_of(bar):
        for beat, length in pattern:
            if off <= beat < off + ln:
                for p in voicing:
                    brass.note(b + beat, length, p, vel)


def guitar_chug(b, bar, vel=74):
    for off, ln, (root, _) in chords_of(bar):
        r = root + 12 if root < 40 else root
        for k in range(int(ln * 2)):
            beat = off + k * 0.5
            for p in (r, r + 7, r + 12):
                gtr.note(b + beat, 0.22 if k % 2 == 0 else 0.15, p, vel if k % 2 == 0 else vel - 20)


bar = 0
# intro (4 bars): bass and drums, guitar enters, a snare roll in
for i, ch in enumerate(A_PROG[:4]):
    b = bar * 4
    bass_bar(b, ch, busy=i >= 2)
    if i < 3:
        groove(b, crash=i == 0, ghosts=i > 0)
    else:
        groove(b, fill=True)
    if i >= 2:
        guitar_chug(b, ch, 64)
    bar += 1


def section_a(start_bar, lead_vel, with_trumpet):
    for i, ch in enumerate(A_PROG):
        b = (start_bar + i) * 4
        bass_bar(b, ch)
        groove(b, crash=i == 0, fill=i == 7)
        brass_stabs(b, ch, ((3.5, .3),) if i % 2 == 0 else ((1.5, .2), (2.75, .2), (3.5, .3)), 88)
        if with_trumpet:
            guitar_chug(b, ch, 70)
    for beat, length, pitch in HOOK:
        lead.note(start_bar * 4 + beat, length * 0.9, pitch, lead_vel)
        if with_trumpet:
            tpt.note(start_bar * 4 + beat, length * 0.9, pitch - 12, 84)


section_a(bar, 84, False)
bar += 8

# B: brass calls on every bar, the lead answers, the guitar chugs
for i, ch in enumerate(B_PROG):
    b = (bar + i) * 4
    bass_bar(b, ch)
    groove(b, crash=i in (0, 4), fill=i == 7)
    guitar_chug(b, ch, 72)
    for beat, length in B_CALL:
        for p in ch[0][1]:
            brass.note(b + beat, length, p, 100)
for rep in range(2):
    for beat, length, pitch in B_ANSWER:
        lead.note(bar * 4 + rep * 16 + beat, length * 0.9, pitch, 80 + 6 * rep)
bar += 8

section_a(bar, 90, True)
bar += 8

# break (4 bars): military snare cadence, brass hits on the downbeats, bass pedal
for i in range(4):
    b = (bar + i) * 4
    march_roll(b, i)
    bass.note(b, 0.4, 38, 104)
    bass.note(b + 2, 0.4, 38 if i < 3 else 45, 96)
    for p in Dm[1] if i < 3 else A[1]:
        brass.note(b, 0.35, p, 104)
        if i == 3:
            brass.note(b + 2, 1.9, p, 96)
    if i < 3:
        lead.note(b + 3, 0.2, 74 + i * 3, 70)
        lead.note(b + 3.5, 0.4, 77 + i * 3, 76)
bar += 4

# bridge: the trumpet sings, brass pads, the guitar rides eighths
for i, ch in enumerate(BRIDGE):
    b = (bar + i) * 4
    bass_bar(b, ch)
    groove(b, crash=i in (0, 4), fill=i == 7)
    guitar_chug(b, ch, 66)
    for p in ch[0][1]:
        brass.note(b, 0.3, p - 12 if p > 70 else p, 84)
        brass.note(b + 2.5, 0.25, p - 12 if p > 70 else p, 78)
for beat, length, pitch in BRIDGE_LINE:
    tpt.note(bar * 4 + beat, length * 0.92, pitch, 96)
bar += 8

# final A: everything, the trumpet doubling the hook an octave down
section_a(bar, 96, True)
bar += 8
assert bar == BARS

secs = render_loop([lead, bass, brass, gtr, tpt, drum], BPM, BARS, "godot/games/flags/audio/music/flags_theme.ogg", gain=0.6)
print(f"wrote flags_theme.ogg ({secs:.1f} s loop)")
