#!/usr/bin/env python3
"""Game 13 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. The theme is our own.
- prism_theme: an original, bright and bouncy electronic loop in E major (a sawtooth hook, a square
  arpeggiator in sixteenths, a celesta arpeggio on top, glockenspiel bells doubling the tune, crystal sparkles,
  a driving octave synth bass, a polysynth pad, four-on-the-floor kick with claps and offbeat hats).
  Form: intro 4 | A 8 | B 8 | A 8 | break 4 | C 8 | A' 8 bars at 128 bpm (90 s), then it loops to the intro.
Usage: python3 tools/audio/prism_music.py
-> godot/games/prism/audio/music/prism_theme.ogg (+ .mid)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/prism/audio/music/"
ELECTRONIC_KIT = 24  # the electronic kit on the drum channel
KICK, SNARE, CLAP, HAT, OPEN, CRASH, RIDE, TOM_L, TOM_M, TOM_H = 36, 40, 39, 42, 46, 49, 51, 45, 47, 50
SHAKER = 70

# chords as (bass root, voicing); a bar may hold two chords, two beats each
E, B, Csm, A = (40, [64, 68, 71]), (35, [63, 66, 71]), (37, [64, 68, 73]), (45, [64, 69, 73])
Gsm, Fsm = (44, [63, 68, 71]), (42, [64, 69, 73])


def chords_of(bar):
    """(beat offset, length, chord) for each chord in a bar."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    """The tracks: saw lead, square arpeggiator, synth bass, pad, glockenspiel, crystal, celesta, drums."""
    drums = Track(9, 0, 100, 64, 22)
    drums.events.append((0, bytes([0xC9, ELECTRONIC_KIT])))
    return (Track(0, 81, 86, 58, 45),    # sawtooth lead
            Track(1, 80, 60, 40, 40),    # square arpeggiator
            Track(2, 39, 106, 64, 10),   # synth bass
            Track(3, 90, 54, 86, 70),    # polysynth pad
            Track(4, 9, 70, 76, 60),     # glockenspiel bells
            Track(5, 98, 54, 100, 80),   # crystal sparkles
            Track(6, 8, 62, 28, 55),     # celesta arpeggio
            drums)


def play(track, start, line, vel, staccato=0.85, shift=0):
    for beat, length, pitch in line:
        track.note(start + beat, length * staccato, pitch + shift, vel)


def make_parts(arp_t, bass_t, pad_t, cel_t, drum):
    """The rhythm section as functions of a bar start (in beats) and a bar of chords."""
    ARP = (0, 1, 2, 3, 1, 2, 3, 2)  # climbing through the voicing and its top octave, bouncing near the top

    def arp_bar(b, bar, vel=60, octave=12, half=False):
        for off, ln, (_, v) in chords_of(bar):
            notes = v + [v[0] + 12]
            for k in range(int(ln * (2 if half else 4))):
                q = off + k * (0.5 if half else 0.25)
                arp_t.note(b + q, 0.2, notes[ARP[k % 8]] + octave, vel + (10 if k % 4 == 0 else 0))

    def celesta_bar(b, bar, vel=56):
        """Eighths two octaves up, falling where the square arpeggio climbs: a glassy counter-line."""
        for off, ln, (_, v) in chords_of(bar):
            notes = [v[0] + 12] + v[::-1]
            for k in range(int(ln * 2)):
                cel_t.note(b + off + k * 0.5, 0.4, notes[k % 4] + 24, vel + (8 if k % 2 == 0 else 0))

    def bass_bar(b, bar, busy=True):
        """A driving bass: a short root on the beat, the octave on the offbeat, a pickup on the last sixteenth."""
        for off, ln, (root, _) in chords_of(bar):
            for k in range(int(ln)):
                q = off + k
                if busy:
                    bass_t.note(b + q, 0.2, root, 100)
                    bass_t.note(b + q + 0.5, 0.22, root + 12, 94)
                    bass_t.note(b + q + 0.75, 0.15, root + 12, 72)
                elif k % 2 == 0:
                    bass_t.note(b + q, 1.8, root, 96)

    def pad_bar(b, bar, vel=48):
        for off, ln, (_, v) in chords_of(bar):
            for p in v:
                pad_t.note(b + off, ln - 0.05, p, vel)

    def groove(b, crash=False, fill=False, hats=True, clap=True, shaker=False, ride=False):
        if crash:
            drum.note(b, 1, CRASH, 100)
        for q in range(4):  # four on the floor
            if not (fill and q == 3):
                drum.note(b + q, 0.2, KICK, 118 if q % 2 == 0 else 110)
        if clap:
            for q in (1, 3):
                if not (fill and q == 3):
                    drum.note(b + q, 0.2, CLAP, 104)
                    drum.note(b + q, 0.2, SNARE, 70)
        if hats:
            for k in range(16):
                if fill and k >= 12:
                    continue
                q = k / 4
                if k % 4 == 2:
                    drum.note(b + q, 0.2, OPEN, 76)
                else:
                    drum.note(b + q, 0.05, HAT, 60 if k % 2 == 0 else 40)
        if shaker:
            for k in range(16):
                drum.note(b + k / 4, 0.05, SHAKER, 44 if k % 2 else 28)
        if ride:
            for q in range(4):
                drum.note(b + q + 0.5, 0.2, RIDE, 58)
        if fill:  # a clap-and-tom run into the next bar
            for i, p in enumerate((CLAP, SNARE, TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, CLAP)):
                drum.note(b + 3 + i / 8, 0.1, p, 80 + i * 5)

    return arp_bar, celesta_bar, bass_bar, pad_bar, groove


def theme():
    lead, arp, bass, pad, bells, crystal, celesta, drum = band()
    arp_bar, celesta_bar, bass_bar, pad_bar, groove = make_parts(arp, bass, pad, celesta, drum)
    A_PROG = [[E], [B], [Csm], [A], [E], [B], [A], [B]]
    B_PROG = [[A], [B], [Gsm], [Csm], [A], [B], [E], [B]]
    C_PROG = [[Csm], [A], [E], [B], [Csm], [A], [Fsm], [B]]

    # the hook: a bouncing figure off the chord tones, springing up to a high answer, 8 bars
    HOOK = [(0, .5, 76), (.5, .5, 83), (1, .5, 80), (1.5, .5, 83), (2, .75, 88), (2.75, .75, 83), (3.5, .5, 80),
            (4, .5, 78), (4.5, .5, 83), (5, .5, 87), (5.5, 1, 83), (6.5, .5, 78), (7, 1, 75),
            (8, .5, 76), (8.5, .5, 80), (9, .5, 85), (9.5, .5, 80), (10, .75, 88), (10.75, .75, 85), (11.5, .5, 80),
            (12, 1.5, 81), (13.5, .5, 80), (14, 1, 78), (15, 1, 76),
            (16, .5, 76), (16.5, .5, 83), (17, .5, 80), (17.5, .5, 83), (18, .75, 88), (18.75, .75, 90), (19.5, .5, 92),
            (20, 1.5, 90), (21.5, .5, 87), (22, 1, 83), (23, .5, 87), (23.5, .5, 90),
            (24, .5, 88), (24.5, .5, 85), (25, .5, 81), (25.5, .5, 85), (26, 1, 88), (27, 1, 85),
            (28, 1.5, 87), (29.5, .5, 83), (30, 1, 78), (31, 1, 75)]
    # the B tune: long, soaring notes with syncopated pushes
    B_TUNE = [(0, 1.5, 85), (1.5, 1, 88), (2.5, 1.5, 85),
              (4, 1.5, 87), (5.5, 1, 90), (6.5, 1.5, 87),
              (8, 1.5, 83), (9.5, 1, 87), (10.5, 1, 92), (11.5, .5, 90),
              (12, 3, 88), (15, .5, 85), (15.5, .5, 88),
              (16, 1.5, 88), (17.5, 1, 93), (18.5, 1.5, 88),
              (20, 1.5, 90), (21.5, 1, 87), (22.5, 1.5, 83),
              (24, 1.5, 88), (25.5, 1, 92), (26.5, 1.5, 95),
              (28, 3, 87), (31, .5, 83), (31.5, .5, 78)]
    # the C line: a call on the bells, answered by the lead in quick falling runs
    C_CALL = [(0, 1, 80), (1, 1, 83), (2, 2, 85), (8, 1, 76), (9, 1, 80), (10, 2, 83),
              (16, 1, 80), (17, 1, 85), (18, 2, 88), (24, 1, 81), (25, 1, 85), (26, 2, 88)]
    C_ANSWER = [(4, .25, 88), (4.25, .25, 85), (4.5, .25, 81), (4.75, .25, 76), (5, .5, 81), (5.5, .5, 85), (6, 1.5, 88),
                (12, .25, 90), (12.25, .25, 87), (12.5, .25, 83), (12.75, .25, 78), (13, .5, 83), (13.5, .5, 87), (14, 1.5, 90),
                (20, .25, 88), (20.25, .25, 85), (20.5, .25, 81), (20.75, .25, 76), (21, .5, 81), (21.5, .5, 85), (22, 1.5, 88),
                (28, .5, 87), (28.5, .5, 90), (29, .5, 95), (29.5, .5, 90), (30, 2, 87)]

    def sparkle(b, pitches, vel=50):
        for k, p in enumerate(pitches):
            crystal.note(b + k * 0.75, 1.2, p, vel)

    bar = 0
    # intro (4 bars): the arpeggiator alone over a kick, the bass and celesta slide in, a clap roll lifts into A
    for i, ch in enumerate(A_PROG[:4]):
        b = bar * 4
        arp_bar(b, ch, 50 + 5 * i)
        pad_bar(b, ch, 38)
        if i >= 1:
            bass_bar(b, ch, busy=i >= 2)
        if i >= 2:
            celesta_bar(b, ch, 44 + 6 * i)
            for k in range(4):
                drum.note(b + k + 0.5, 0.2, OPEN, 56)
        for q in range(4):
            drum.note(b + q, 0.2, KICK, 92 + 8 * i)
        if i == 3:
            for k in range(8):
                drum.note(b + 2 + k / 4, 0.1, CLAP, 60 + k * 6)
        bar += 1
    sparkle(0, (88, 83, 80, 76))

    def section_a(start, lead_vel, full):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            arp_bar(b, ch, 58)
            bass_bar(b, ch)
            pad_bar(b, ch, 44)
            groove(b, crash=i in (0, 4), fill=i == 7, shaker=full)
            if full:
                celesta_bar(b, ch, 50)
        play(lead, start * 4, HOOK, lead_vel)
        play(bells, start * 4, HOOK if full else HOOK[::3], 58 if full else 50, 0.7, 12 if full else 0)

    section_a(bar, 92, False)
    bar += 8

    # B: the lead soars an octave down, the arpeggiator drops to eighths, the celesta and a ride carry the pulse
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        arp_bar(b, ch, 54, 12, half=True)
        celesta_bar(b, ch, 52)
        bass_bar(b, ch)
        pad_bar(b, ch, 56)
        groove(b, crash=i in (0, 4), fill=i == 7, ride=True)
    play(lead, bar * 4, B_TUNE, 96, 0.92, -12)
    play(bells, bar * 4, B_TUNE[::2], 52, 0.9)
    bar += 8

    section_a(bar, 98, True)
    bar += 8

    # break (4 bars): the drums drop out, the bass holds long roots, the arpeggios run alone and climb
    for i, ch in enumerate(([Csm], [A], [B], [B])):
        b = (bar + i) * 4
        arp_bar(b, ch, 50 + 6 * i, 12 + (12 if i == 3 else 0))
        celesta_bar(b, ch, 46 + 4 * i)
        bass_bar(b, ch, busy=False)
        pad_bar(b, ch, 52)
        if i == 0:
            drum.note(b, 1, CRASH, 90)
        if i >= 2:  # the kick returns, then a rising clap roll
            for q in range(4):
                drum.note(b + q, 0.2, KICK, 100)
        if i == 3:
            for k in range(16):
                drum.note(b + k / 4, 0.1, CLAP, 50 + k * 4)
    sparkle(bar * 4, (80, 85, 88, 92), 46)
    sparkle(bar * 4 + 8, (83, 87, 90, 95), 50)
    bar += 4

    # C: call and answer between the bells and the lead, the arpeggiator in sixteenths, the full kit
    for i, ch in enumerate(C_PROG):
        b = (bar + i) * 4
        arp_bar(b, ch, 58)
        bass_bar(b, ch)
        pad_bar(b, ch, 44)
        groove(b, crash=i in (0, 4), fill=i == 7, shaker=True)
    play(bells, bar * 4, C_CALL, 82, 0.9)
    play(lead, bar * 4, C_ANSWER, 90, 0.85)
    bar += 8

    section_a(bar, 100, True)
    sparkle(bar * 4 + 16, (88, 92, 95, 100), 44)
    bar += 8
    assert bar == 48
    return [lead, arp, bass, pad, bells, crystal, celesta, drum], 128, bar


tracks, bpm, bars = theme()
secs = render_loop(tracks, bpm, bars, OUT + "prism_theme.ogg", gain=0.6)
print(f"wrote prism_theme.ogg ({secs:.1f} s loop)")
