#!/usr/bin/env python3
"""Game 9 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0.
- blastyard_theme: an original, bouncy party loop in F major (square lead, marimba, clavinet offbeats, octave-jumping
  synth bass, brass stabs, drums with claps, cowbell and woodblock).
  Form: intro 4 | A 8 | B 8 | A 8 | drum break 4 | bridge 8 | A 8 bars, then it loops to the intro.
- blastyard_hurry: the same band, faster and in D minor, a tense 20-bar loop for sudden death.
Usage: python3 tools/audio/blastyard_music.py
-> godot/games/blastyard/audio/music/blastyard_theme.ogg and blastyard_hurry.ogg (+ .mid)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/blastyard/audio/music/"
KICK, SNARE, CLAP, HAT, OPEN, CRASH, TOM_L, TOM_M, TOM_H = 36, 38, 39, 42, 46, 49, 45, 47, 50
TAMB, COWBELL, BLOCK_HI, BLOCK_LO = 54, 56, 76, 77

# chords as (bass root, voicing); a bar may hold two chords, two beats each
F, Dm, Bb, C, Gm, Am, A = ((41, [60, 65, 69]), (38, [62, 65, 69]), (46, [62, 65, 70]), (36, [60, 64, 67]),
                           (43, [62, 67, 70]), (45, [60, 64, 69]), (45, [61, 64, 69]))


def chords_of(bar):
    """(beat offset, length, chord) for each chord in a bar."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band(bpm_feel):
    """A fresh set of tracks: lead, marimba, clavinet, bass, brass, drums."""
    return (Track(0, 80, 80, 70, 40),    # square lead
            Track(1, 12, 84, 44, 45),    # marimba
            Track(2, 7, 62, 88, 30),     # clavinet
            Track(3, 38, 100, 64, 15),   # synth bass
            Track(4, 62, 80, 56, 45),    # synth brass
            Track(9, 0, 96, 64, 20 if bpm_feel == "fast" else 28))


def play(track, start, line, vel, staccato=0.75, shift=0):
    for beat, length, pitch in line:
        track.note(start + beat, length * staccato, pitch + shift, vel)


# ---------------------------------------------------------------- the theme
def theme():
    lead, mar, clav, bass, brass, drum = band("party")
    A_PROG = [[F], [Dm], [Bb], [C], [F], [Dm], [Bb, C], [F]]
    B_PROG = [[Bb], [C], [Am], [Dm], [Gm], [C], [Bb], [C]]
    BRIDGE = [[Dm], [Bb], [F], [C], [Dm], [Bb], [Gm], [C]]

    # the hook: jumpy and staccato, 8 bars
    HOOK = [(0, .5, 72), (.5, .5, 77), (1, .5, 76), (1.5, .5, 77), (2, 1, 81), (3, .5, 79), (3.5, .5, 77),
            (4, .5, 74), (4.5, .5, 77), (5, 1, 81), (6, .5, 79), (6.5, .5, 77), (7, 1, 74),
            (8, .5, 70), (8.5, .5, 74), (9, .5, 77), (9.5, .5, 79), (10, 1, 81), (11, .5, 79), (11.5, .5, 77),
            (12, .5, 76), (12.5, .5, 77), (13, .5, 79), (14, 1.5, 72),
            (16, .5, 72), (16.5, .5, 77), (17, .5, 76), (17.5, .5, 77), (18, 1, 81), (19, .5, 79), (19.5, .5, 77),
            (20, .5, 74), (20.5, .5, 77), (21, 1, 81), (22, .5, 84), (22.5, .5, 82), (23, 1, 81),
            (24, .5, 82), (24.5, .5, 81), (25, .5, 79), (25.5, .5, 77), (26, .5, 76), (26.5, .5, 77), (27, 1, 79),
            (28, .5, 81), (28.5, .5, 79), (29, 1.5, 77), (31, .5, 72), (31.5, .5, 74)]
    # the B tune: syncopated, climbing, a little bigger
    B_TUNE = [(0, .75, 74), (.75, .75, 77), (1.5, 1, 82), (2.5, .5, 81), (3, 1, 77),
              (4, .75, 76), (4.75, .75, 79), (5.5, 1, 84), (6.5, .5, 82), (7, 1, 79),
              (8, .75, 76), (8.75, .75, 81), (9.5, 1, 84), (10.5, .5, 81), (11, 1, 76),
              (12, .75, 77), (12.75, .75, 74), (13.5, 2.5, 77),
              (16, .75, 74), (16.75, .75, 79), (17.5, 1, 82), (18.5, .5, 81), (19, 1, 79),
              (20, .75, 76), (20.75, .75, 79), (21.5, 1, 84), (22.5, .5, 82), (23, 1, 79),
              (24, .5, 77), (24.5, .5, 79), (25, .5, 82), (25.5, .5, 81), (26, 1, 77), (27, 1, 74),
              (28, 1, 76), (29, 1, 79), (30, 2, 84)]
    # the bridge: a singing brass line over marimba arpeggios
    BRIDGE_LINE = [(0, 2, 81), (2, 2, 77), (4, 3, 82), (7, 1, 81), (8, 2, 77), (10, 2, 72), (12, 4, 76),
                   (16, 2, 81), (18, 2, 77), (20, 2, 82), (22, 2, 84), (24, 2, 86), (26, 2, 82), (28, 3, 84), (31, 1, 79)]
    BASS_BOUNCE = [(0, .4, 0), (.5, .3, 12), (1, .4, 0), (1.5, .3, 12), (2, .4, 0), (2.5, .3, 12), (3, .4, 7), (3.5, .3, 12)]

    def bass_bar(b, bar, busy=True):
        for off, ln, (root, _) in chords_of(bar):
            for beat, length, iv in BASS_BOUNCE:
                if off <= beat < off + ln and (busy or beat in (0, 2)):
                    bass.note(b + beat, length, root + iv, 104 if beat % 1 == 0 else 84)

    def clav_bar(b, bar, vel=70):
        for off, ln, (_, voicing) in chords_of(bar):
            for k in range(int(ln)):
                for p in voicing:
                    clav.note(b + off + k + 0.5, 0.18, p, vel)

    def groove(b, fill=False, crash=False, cowbell=False, tamb=False):
        if crash:
            drum.note(b, 1, CRASH, 96)
        for k in range(8):
            q = k / 2
            if fill and q >= 2:
                continue
            drum.note(b + q, 0.1, OPEN if k == 7 else HAT, 70 if k % 2 else 52)
        for q in (0, 1.5, 2, 3.25):  # a bouncy kick
            if not (fill and q > 2):
                drum.note(b + q, 0.2, KICK, 110 if q in (0, 2) else 88)
        for q in (1, 3):
            if not (fill and q == 3):
                drum.note(b + q, 0.2, SNARE, 96)
                drum.note(b + q, 0.2, CLAP, 84)
        if cowbell:
            for q in (0.5, 1.5, 2.5, 3.5):
                drum.note(b + q, 0.1, COWBELL, 58)
        if tamb:
            for k in range(16):
                drum.note(b + k / 4, 0.05, TAMB, 50 if k % 2 else 34)
        if fill:  # woodblocks and toms bounce into the next section
            for i, p in enumerate((BLOCK_HI, BLOCK_LO, BLOCK_HI, BLOCK_LO, TOM_H, TOM_M, TOM_L, SNARE)):
                drum.note(b + 2 + i * 0.25, 0.2, p, 80 + i * 4)

    def brass_stabs(b, bar, beats=(2.5, 3.5), vel=86):
        for off, ln, (_, voicing) in chords_of(bar):
            for beat in beats:
                if off <= beat < off + ln:
                    for p in voicing:
                        brass.note(b + beat, 0.25, p + 12, vel)

    bar = 0
    # intro (4 bars): bass and clav, woodblocks, then the drums; the marimba teases the hook
    for i, ch in enumerate(A_PROG[:4]):
        b = bar * 4
        bass_bar(b, ch, busy=i >= 1)
        clav_bar(b, ch, 62)
        if i < 2:
            for k in range(4):
                drum.note(b + k, 0.1, BLOCK_HI if k % 2 == 0 else BLOCK_LO, 70)
                drum.note(b + k + 0.5, 0.1, HAT, 44)
        else:
            groove(b, crash=i == 2, fill=i == 3)
        bar += 1
    play(mar, 8, HOOK[:13], 76, 0.9)

    def section_a(start_bar, lead_vel, full):
        for i, ch in enumerate(A_PROG):
            b = (start_bar + i) * 4
            bass_bar(b, ch)
            clav_bar(b, ch, 70)
            groove(b, crash=i in (0, 4), fill=i == 7, cowbell=full)
            if i % 2 == 1 or full:
                brass_stabs(b, ch)
        play(lead, start_bar * 4, HOOK, lead_vel)
        if full:  # the marimba doubles the hook an octave up, a touch behind for bounce
            play(mar, start_bar * 4, HOOK, 70, 0.6, 12)

    section_a(bar, 86, False)
    bar += 8

    # B: the lead climbs, the brass answers at the end of each bar, tambourine on top
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        bass_bar(b, ch)
        clav_bar(b, ch, 66)
        groove(b, crash=i in (0, 4), fill=i == 7, tamb=True)
        brass_stabs(b, ch, (3, 3.5), 92)
    play(lead, bar * 4, B_TUNE, 88, 0.85)
    bar += 8

    section_a(bar, 92, True)
    bar += 8

    # break (4 bars): stop-time; the band hits the downbeats, woodblocks and cowbell chatter, a tom roll to the bridge
    for i in range(4):
        b = (bar + i) * 4
        root, voicing = (Dm, Dm, Bb, C)[i]
        bass.note(b, 0.4, root, 106)
        bass.note(b + 1.5, 0.3, root + 12, 90)
        for p in voicing:
            brass.note(b, 0.3, p + 12, 100)
        if i == 0:
            drum.note(b, 1, CRASH, 100)
        drum.note(b, 0.2, KICK, 110)
        if i < 3:
            for q, p in ((1, BLOCK_HI), (1.5, BLOCK_LO), (2, COWBELL), (2.5, BLOCK_HI), (2.75, BLOCK_HI), (3, CLAP), (3.5, COWBELL)):
                drum.note(b + q, 0.1, p, 78)
            play(lead, b, [(2.5, .5, 77 + 2 * i), (3, .5, 81 + 2 * i), (3.5, .5, 84 + i)], 80, 0.6)
        else:
            for k in range(16):
                drum.note(b + k / 4, 0.1, (SNARE, TOM_H, TOM_M, TOM_L)[k // 4], 60 + k * 3)
    bar += 4

    # bridge: the brass sings, the marimba runs arpeggios, the clav keeps the offbeat
    for i, ch in enumerate(BRIDGE):
        b = (bar + i) * 4
        bass_bar(b, ch, busy=i >= 4)
        clav_bar(b, ch, 58)
        groove(b, crash=i in (0, 4), fill=i == 7, tamb=i >= 4)
        v = ch[0][1]
        arp = [v[0], v[1], v[2], v[0] + 12, v[2], v[1]] * 2
        for k in range(8):
            mar.note(b + k * 0.5, 0.4, arp[k] + 12, 64 + (8 if k % 2 == 0 else 0))
    play(brass, bar * 4, BRIDGE_LINE, 92, 0.95)
    play(lead, bar * 4 + 16, BRIDGE_LINE[7:], 64, 0.95, -12)
    bar += 8

    section_a(bar, 96, True)
    bar += 8
    assert bar == 48
    return [lead, mar, clav, bass, brass, drum], 132, bar


# ---------------------------------------------------------------- the sudden-death loop
def hurry():
    lead, mar, clav, bass, brass, drum = band("fast")
    PROG = [[Dm], [Dm], [Bb], [A]]
    MOTIF = [(0, .5, 74), (.5, .5, 77), (1, .5, 81), (1.5, .5, 77), (2, .5, 74), (2.5, .5, 77), (3, .5, 81), (3.5, .5, 86),
             (4, .5, 84), (4.5, .5, 81), (5, .5, 77), (5.5, .5, 81), (6, 1, 84), (7, .5, 81), (7.5, .5, 77),
             (8, .5, 74), (8.5, .5, 77), (9, .5, 82), (9.5, .5, 77), (10, .5, 74), (10.5, .5, 77), (11, .5, 82), (11.5, .5, 86),
             (12, .5, 85), (12.5, .5, 81), (13, .5, 76), (13.5, .5, 81), (14, .5, 85), (14.5, .5, 88), (15, 1, 85)]
    ALARM = [(0, 2, 81), (2, 2, 82), (4, 2, 84), (6, 2, 86), (8, 2, 82), (10, 2, 86), (12, 2, 85), (14, 2, 88)]

    def pulse(b, ch, vel=100):
        root, voicing = ch[0]
        for k in range(8):
            bass.note(b + k * 0.5, 0.35, root + (12 if k % 2 else 0), vel if k % 2 == 0 else vel - 16)
        for k in range(16):  # a nervous sixteenth-note ostinato
            mar.note(b + k / 4, 0.2, voicing[(0, 1, 2, 1)[k % 4]] + 12, 66 if k % 4 == 0 else 50)

    def drive(b, fill=False, crash=False, cowbell=True):
        if crash:
            drum.note(b, 1, CRASH, 100)
        for k in range(16):
            if fill and k >= 12:
                continue
            drum.note(b + k / 4, 0.05, HAT, 64 if k % 2 == 0 else 40)
        for q in range(4):
            drum.note(b + q, 0.2, KICK, 112)
        for q in (1, 3):
            if not (fill and q == 3):
                drum.note(b + q, 0.2, SNARE, 100)
                drum.note(b + q, 0.2, CLAP, 76)
        if cowbell:
            for q in (0.5, 1.5, 2.5, 3.5):
                drum.note(b + q, 0.1, COWBELL, 60)
        if fill:
            for i, p in enumerate((SNARE, TOM_H, TOM_M, TOM_L)):
                drum.note(b + 3 + i * 0.25, 0.2, p, 96)

    # 20 bars: 4 of band alone, 8 of the motif, 4 of brass alarm calls over the lead, 4 of the motif with everything
    for rep in range(5):
        for i, ch in enumerate(PROG):
            b = (rep * 4 + i) * 4
            pulse(b, ch, 96 + 2 * rep)
            drive(b, crash=i == 0, fill=i == 3, cowbell=rep > 0)
            for p in ch[0][1]:
                clav.note(b + 0.5, 0.15, p, 64)
                clav.note(b + 2.5, 0.15, p, 64)
            if rep >= 3:
                for p in ch[0][1]:
                    brass.note(b, 0.3, p + 12, 96)
                    brass.note(b + 1.5, 0.3, p + 12, 88)
        base = rep * 16
        if rep in (1, 2, 4):
            play(lead, base, MOTIF, 84 + 4 * rep, 0.7)
        if rep == 3:
            play(brass, base, ALARM, 100, 0.95)
            play(lead, base, MOTIF, 70, 0.5, -12)
    return [lead, mar, clav, bass, brass, drum], 168, 20


for name, song in (("blastyard_theme", theme), ("blastyard_hurry", hurry)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
