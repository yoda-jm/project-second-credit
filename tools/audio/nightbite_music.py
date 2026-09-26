#!/usr/bin/env python3
"""Game 12 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. All themes are our own.
- nightbite_theme: an original, driving neon-arcade loop in A minor (a sawtooth hook, a square arpeggiator in
  sixteenths, a pumping octave synth bass, a warm pad, synth-brass stabs, crystal sparkles, electronic drums).
  Form: intro 4 | A 8 | B 8 | A 8 | break 4 | C 8 | A' 8 | turnaround 4 bars at 140 bpm (about 89 s),
  then it loops to the intro.
- nightbite_fever: the same band, faster and brighter in D major, a 14-bar loop (20 s) while the spirits are scared.
Usage: python3 tools/audio/nightbite_music.py
-> godot/games/nightbite/audio/music/nightbite_theme.ogg and nightbite_fever.ogg (+ .mid)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/nightbite/audio/music/"
ELECTRONIC_KIT = 24  # the electronic kit on the drum channel
KICK, SNARE, CLAP, HAT, PEDAL, OPEN, CRASH, RIDE, TOM_L, TOM_M, TOM_H = 36, 40, 39, 42, 44, 46, 49, 51, 45, 47, 50
TAMB, SHAKER = 54, 70

# chords as (bass root, voicing); a bar may hold two chords, two beats each
Am, F, C, G, Dm, Em, E = ((45, [57, 60, 64]), (41, [57, 60, 65]), (36, [55, 60, 64]), (43, [55, 59, 62]),
                          (38, [57, 62, 65]), (40, [55, 59, 64]), (40, [56, 59, 64]))
D, A, Bm, Gmaj, Em2, Fsm = ((38, [62, 66, 69]), (45, [61, 64, 69]), (47, [62, 66, 71]), (43, [62, 67, 71]),
                            (40, [59, 64, 67]), (42, [61, 66, 69]))


def chords_of(bar):
    """(beat offset, length, chord) for each chord in a bar."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    """A fresh set of tracks: saw lead, square arpeggiator, synth bass, pad, synth brass, crystal, drums."""
    drums = Track(9, 0, 100, 64, 22)
    drums.events.append((0, bytes([0xC9, ELECTRONIC_KIT])))
    return (Track(0, 81, 88, 60, 45),    # sawtooth lead
            Track(1, 80, 64, 44, 40),    # square arpeggiator
            Track(2, 38, 104, 64, 10),   # synth bass
            Track(3, 89, 58, 84, 70),    # warm pad
            Track(4, 62, 76, 72, 40),    # synth brass stabs
            Track(5, 98, 56, 96, 80),    # crystal sparkles
            drums)


def play(track, start, line, vel, staccato=0.85, shift=0):
    for beat, length, pitch in line:
        track.note(start + beat, length * staccato, pitch + shift, vel)


def make_parts(arp_t, bass_t, pad_t, brass_t, drum):
    """The rhythm section as functions of a bar start (in beats) and a bar of chords."""
    ARP = (0, 1, 2, 3, 2, 1, 0, 2)  # up and back over the voicing and its top octave

    def arp_bar(b, bar, vel=62, octave=12, half=False):
        for off, ln, (_, v) in chords_of(bar):
            notes = v + [v[0] + 12]
            for k in range(int(ln * (2 if half else 4))):
                q = off + k * (0.5 if half else 0.25)
                arp_t.note(b + q, 0.2, notes[ARP[k % 8]] + octave, vel + (10 if k % 4 == 0 else 0))

    def bass_bar(b, bar, busy=True):
        """A pumping synth bass: the root on the beat, its octave on the offbeat sixteenth pairs."""
        for off, ln, (root, _) in chords_of(bar):
            for k in range(int(ln * 2)):
                q = off + k * 0.5
                if busy:
                    bass_t.note(b + q, 0.22, root, 104 if k % 2 == 0 else 92)
                    bass_t.note(b + q + 0.25, 0.2, root + 12, 80)
                elif k % 2 == 0:
                    bass_t.note(b + q, 0.9, root, 100)

    def pad_bar(b, bar, vel=50):
        for off, ln, (_, v) in chords_of(bar):
            for p in v:
                pad_t.note(b + off, ln - 0.05, p, vel)

    def stabs(b, bar, beats=(1.5, 3.5), vel=84):
        for off, ln, (_, v) in chords_of(bar):
            for beat in beats:
                if off <= beat < off + ln:
                    for p in v:
                        brass_t.note(b + beat, 0.3, p + 12, vel)

    def groove(b, crash=False, fill=False, hats=True, clap=True, ride=False, shaker=False):
        if crash:
            drum.note(b, 1, CRASH, 100)
        for q in range(4):  # four on the floor
            if not (fill and q == 3):
                drum.note(b + q, 0.2, KICK, 118 if q % 2 == 0 else 110)
        if clap:
            for q in (1, 3):
                if not (fill and q == 3):
                    drum.note(b + q, 0.2, SNARE, 100)
                    drum.note(b + q, 0.2, CLAP, 88)
        if hats:
            for k in range(16):
                if fill and k >= 12:
                    continue
                q = k / 4
                if k % 4 == 2:
                    drum.note(b + q, 0.2, OPEN, 74)
                else:
                    drum.note(b + q, 0.05, HAT, 62 if k % 2 == 0 else 42)
        if ride:
            for q in (0, 1, 2, 3):
                drum.note(b + q + 0.5, 0.2, RIDE, 60)
        if shaker:
            for k in range(16):
                drum.note(b + k / 4, 0.05, SHAKER, 46 if k % 2 else 30)
        if fill:  # a quick snare-and-tom run into the next bar
            for i, p in enumerate((SNARE, SNARE, TOM_H, TOM_M, TOM_M, TOM_L, SNARE, SNARE)):
                drum.note(b + 3 + i / 8, 0.1, p, 80 + i * 5)

    return arp_bar, bass_bar, pad_bar, stabs, groove


# ---------------------------------------------------------------- the theme
def theme():
    lead, arp, bass, pad, brass, crystal, drum = band()
    arp_bar, bass_bar, pad_bar, stabs, groove = make_parts(arp, bass, pad, brass, drum)
    A_PROG = [[Am], [F], [C], [G], [Am], [F], [G], [E]]
    B_PROG = [[F], [G], [Em], [Am], [F], [G], [Am], [E]]
    C_PROG = [[Am], [G], [F], [G], [Dm], [Em], [F], [E]]
    TURN = [[F], [G], [Dm, E], [E]]

    # the hook: bouncing off the chord tones, a snap up to the top, 8 bars
    HOOK = [(0, .5, 76), (.5, .5, 72), (1, .5, 69), (1.5, .5, 72), (2, .75, 76), (2.75, .75, 79), (3.5, .5, 76),
            (4, .5, 77), (4.5, .5, 76), (5, .5, 72), (5.5, 1, 69), (6.5, .5, 72), (7, 1, 74),
            (8, .75, 79), (8.75, .75, 76), (9.5, .5, 72), (10, 1, 74), (11, .5, 76), (11.5, .5, 79),
            (12, 1.5, 81), (13.5, .5, 79), (14, 1, 74), (15, 1, 71),
            (16, .5, 76), (16.5, .5, 72), (17, .5, 69), (17.5, .5, 72), (18, .75, 76), (18.75, .75, 79), (19.5, .5, 76),
            (20, .5, 77), (20.5, .5, 81), (21, .5, 84), (21.5, 1, 81), (22.5, .5, 77), (23, 1, 76),
            (24, .75, 79), (24.75, .75, 74), (25.5, .5, 71), (26, 1, 74), (27, 1, 79),
            (28, 1.5, 80), (29.5, .5, 76), (30, 1, 71), (31, 1, 68)]
    # the B tune: longer, soaring notes with syncopated pushes
    B_TUNE = [(0, 1.5, 81), (1.5, 1, 84), (2.5, 1.5, 81),
              (4, 1.5, 79), (5.5, 1, 83), (6.5, 1.5, 79),
              (8, 1.5, 76), (9.5, 1, 79), (10.5, 1, 83), (11.5, .5, 84),
              (12, 3, 81), (15, .5, 76), (15.5, .5, 79),
              (16, 1.5, 81), (17.5, 1, 84), (18.5, 1.5, 89),
              (20, 1.5, 86), (21.5, 1, 83), (22.5, 1.5, 79),
              (24, 1.5, 84), (25.5, 1, 83), (26.5, 1.5, 81),
              (28, 3, 80), (31, .5, 76), (31.5, .5, 71)]
    # the C line: a call on the brass, answered by the lead in quick runs
    C_CALL = [(0, 1, 76), (1, 1, 79), (2, 2, 81), (8, 1, 77), (9, 1, 81), (10, 2, 84),
              (16, 1, 77), (17, 1, 74), (18, 2, 77), (24, 1, 77), (25, 1, 76), (26, 2, 74)]
    C_ANSWER = [(4, .25, 81), (4.25, .25, 79), (4.5, .25, 76), (4.75, .25, 74), (5, .5, 76), (5.5, .5, 79), (6, 1.5, 74),
                (12, .25, 79), (12.25, .25, 77), (12.5, .25, 74), (12.75, .25, 71), (13, .5, 74), (13.5, .5, 77), (14, 1.5, 79),
                (20, .25, 81), (20.25, .25, 79), (20.5, .25, 76), (20.75, .25, 74), (21, .5, 76), (21.5, .5, 79), (22, 1.5, 83),
                (28, .5, 80), (28.5, .5, 83), (29, .5, 86), (29.5, .5, 83), (30, 2, 88)]

    def sparkle(b, pitches, vel=50):
        for k, p in enumerate(pitches):
            crystal.note(b + k * 0.75, 1.2, p, vel)

    bar = 0
    # intro (4 bars): the arpeggiator alone with a filtered kick, the bass creeps in, a snare roll lifts into A
    for i, ch in enumerate(A_PROG[:4]):
        b = bar * 4
        arp_bar(b, ch, 50 + 5 * i)
        pad_bar(b, ch, 40)
        if i >= 1:
            bass_bar(b, ch, busy=i >= 2)
        for q in range(4):
            drum.note(b + q, 0.2, KICK, 90 + 8 * i)
        if i >= 2:
            for k in range(8):
                drum.note(b + k / 2 + 0.5, 0.05, HAT, 48)
        if i == 3:
            for k in range(8):
                drum.note(b + 2 + k / 4, 0.1, SNARE, 60 + k * 6)
        bar += 1
    sparkle(0, (88, 84, 81, 76))

    def section_a(start, lead_vel, full):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            arp_bar(b, ch, 60)
            bass_bar(b, ch)
            pad_bar(b, ch, 46)
            groove(b, crash=i in (0, 4), fill=i == 7, shaker=full)
            if full or i % 2 == 1:
                stabs(b, ch)
        play(lead, start * 4, HOOK, lead_vel)
        if full:  # the crystal doubles the hook an octave up
            play(crystal, start * 4, HOOK, 44, 0.7, 12)

    section_a(bar, 92, False)
    bar += 8

    # B: the lead soars, the arpeggiator drops to eighths, the pad swells, a ride on the offbeats
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        arp_bar(b, ch, 56, 12, half=True)
        bass_bar(b, ch)
        pad_bar(b, ch, 58)
        groove(b, crash=i in (0, 4), fill=i == 7, ride=True)
        stabs(b, ch, (0, 2.5), 76)
    play(lead, bar * 4, B_TUNE, 96, 0.92, -12)
    play(crystal, bar * 4, B_TUNE[::2], 40, 0.9)
    bar += 8

    section_a(bar, 98, True)
    bar += 8

    # break (4 bars): the drums drop out, the bass holds long roots, the arpeggiator runs alone and climbs
    for i, ch in enumerate(([Am], [F], [G], [E])):
        b = (bar + i) * 4
        arp_bar(b, ch, 52 + 6 * i, 12 + (12 if i == 3 else 0))
        bass_bar(b, ch, busy=False)
        pad_bar(b, ch, 50)
        if i == 0:
            drum.note(b, 1, CRASH, 90)
        if i >= 2:  # the kick returns, then a rising snare roll
            for q in range(4):
                drum.note(b + q, 0.2, KICK, 100)
        if i == 3:
            for k in range(16):
                drum.note(b + k / 4, 0.1, SNARE, 50 + k * 4)
    sparkle(bar * 4, (81, 84, 88, 93), 46)
    bar += 4

    # C: call and answer between the brass and the lead, the arpeggiator in sixteenths, the full kit
    for i, ch in enumerate(C_PROG):
        b = (bar + i) * 4
        arp_bar(b, ch, 60)
        bass_bar(b, ch)
        pad_bar(b, ch, 44)
        groove(b, crash=i in (0, 4), fill=i == 7, shaker=True)
    play(brass, bar * 4, C_CALL, 88, 0.9)
    play(lead, bar * 4, C_ANSWER, 90, 0.85)
    bar += 8

    section_a(bar, 100, True)
    bar += 8

    # turnaround (4 bars): stop hits on the brass, the lead holds, a snare build back to the intro
    for i, ch in enumerate(TURN):
        b = (bar + i) * 4
        arp_bar(b, ch, 54)
        bass_bar(b, ch, busy=i < 2)
        pad_bar(b, ch, 44)
        stabs(b, ch, (0, 0.75, 1.5), 90)
        groove(b, crash=i == 0, hats=i < 3, clap=i < 3)
    play(lead, bar * 4, [(0, 2, 81), (2, 2, 79), (4, 4, 83), (8, 2, 81), (10, 2, 80), (12, 4, 76)], 80, 0.95)
    for k in range(16):
        drum.note((bar + 3) * 4 + k / 4, 0.1, SNARE if k < 12 else (TOM_H, TOM_M, TOM_M, TOM_L)[k - 12], 50 + k * 4)
    bar += 4
    assert bar == 52
    return [lead, arp, bass, pad, brass, crystal, drum], 140, bar


# ---------------------------------------------------------------- the fever loop, while the spirits are scared
def fever():
    lead, arp, bass, pad, brass, crystal, drum = band()
    arp_bar, bass_bar, pad_bar, stabs, groove = make_parts(arp, bass, pad, brass, drum)
    PROG = [[D], [A], [Bm], [Gmaj]]
    # a bright, skipping motif that keeps rising, 4 bars
    MOTIF = [(0, .5, 78), (.5, .5, 81), (1, .5, 86), (1.5, .5, 81), (2, .5, 83), (2.5, .5, 85), (3, 1, 88),
             (4, .5, 85), (4.5, .5, 81), (5, .5, 76), (5.5, .5, 81), (6, .5, 85), (6.5, .5, 88), (7, 1, 90),
             (8, .5, 86), (8.5, .5, 83), (9, .5, 78), (9.5, .5, 83), (10, .5, 86), (10.5, .5, 90), (11, 1, 88),
             (12, .75, 86), (12.75, .75, 83), (13.5, .5, 79), (14, .5, 81), (14.5, .5, 83), (15, 1, 86)]

    # 14 bars: three times the four-bar round (the second with brass, the third with everything), then a lift
    for rep in range(3):
        for i, ch in enumerate(PROG):
            b = (rep * 4 + i) * 4
            arp_bar(b, ch, 60 + 3 * rep)
            bass_bar(b, ch)
            pad_bar(b, ch, 44)
            groove(b, crash=i == 0, shaker=rep > 0)
            if rep >= 1:
                stabs(b, ch, (0.5, 1.5, 2.5, 3.5), 72 + 6 * rep)
        play(lead, rep * 16, MOTIF, 88 + 4 * rep, 0.7)
        if rep == 2:
            play(crystal, rep * 16, MOTIF, 46, 0.6)
    for i, ch in enumerate(([Em2], [A])):  # the lift: a rising run straight back into the top of the loop
        b = (12 + i) * 4
        arp_bar(b, ch, 66, 24)
        bass_bar(b, ch)
        pad_bar(b, ch, 50)
        groove(b, fill=i == 1, shaker=True)
        stabs(b, ch, (0, 1.5, 3), 88)
    play(lead, 48, [(k * 0.5, 0.5, p) for k, p in enumerate((76, 79, 83, 86, 88, 91, 88, 86,
                                                             85, 88, 91, 93, 90, 88, 85, 81))], 94, 0.7)
    return [lead, arp, bass, pad, brass, crystal, drum], 168, 14


for name, song in (("nightbite_theme", theme), ("nightbite_fever", fever)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
