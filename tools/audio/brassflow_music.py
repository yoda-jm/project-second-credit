#!/usr/bin/env python3
"""Game 29 (Brassflow) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any earlier pipe game's music, nor of any existing film, game or classical theme.
A playful clockwork band for a steampunk workshop: a tuba oom-pah, pizzicato and harpsichord on the off-beats,
wood blocks ticking like an escapement, a staccato clarinet tune that climbs and drops like a little machine, a
bassoon answering, glockenspiel and music-box sparkle, an accordion in the bridge, a guiro ratchet for the fills.
- brassflow_theme: D major, 112 bpm, 36 bars (77.1 s). Form: intro 4 (the clock ticks, a music-box figure, the tuba
  comes in) | A 8 (the clarinet tune over D A Bm F#m G D Em-A D) | A' 8 (the tune on xylophone and clarinet, a bassoon
  counter-line, glockenspiel) | B 8 (the bridge: an oboe tune over G Gm D B7 Em A7 D A7, accordion, the ratchet) |
  A'' 8 (tutti: the tune doubled, brass stabs, cymbals) -> back to the top.
- brassflow_hurry: while the glow flows, B minor, 150 bpm, 12 bars (19.2 s): a galloping tuba, sixteenth wood-block
  ticks, a racing xylophone tune over Bm G A F# (twice) and Em F# Bm F#, brass stabs, snare.
No voices: no choir or voice patches.
Usage: python3 tools/audio/brassflow_music.py
-> godot/games/brassflow/audio/music/brassflow_theme.ogg, brassflow_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/brassflow/audio/music/"
KICK, STICK, SNARE, CLOSED, PEDAL, CRASH, RIDE_BELL, TAMB, TRIANGLE = 36, 37, 38, 42, 44, 49, 53, 54, 81
CLAVES, HI_BLOCK, LO_BLOCK, GUIRO_S, GUIRO_L, CABASA = 75, 76, 77, 73, 74, 69
HARPSI, CELESTA, GLOCK, MUSICBOX, MARIMBA, XYLO = 6, 8, 9, 10, 12, 13
ACCORDION, PIZZ, TUBA, BRASS, OBOE, BASSOON, CLARINET = 21, 45, 58, 61, 68, 70, 71
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def mel(text):
    """Parses "d5/.5 f#5/.5 r/1 | ..." into [(beat, length, pitch)]; '#' sharpens, 'b' flattens (after the letter),
    r is a rest; '|' bar marks are checked and ignored."""
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


def play(track, start, line, vel, legato=0.9, shift=0, accent=8):
    for beat, length, pitch in line:
        note(track, start + beat, length * legato, pitch + shift, vel + (accent if beat % 1 == 0 else 0))


# chords: (tuba root, voicing round middle C)
D, A, Bm, Fsm, G, Em, Gm, B7, A7, Fs = ((38, [54, 57, 62]), (33, [52, 57, 61]), (35, [54, 59, 62]),
                                        (42, [54, 57, 61]), (43, [55, 59, 62]), (40, [55, 59, 64]),
                                        (43, [55, 58, 62]), (35, [54, 57, 63]), (33, [55, 57, 61]),
                                        (42, [54, 58, 61]))
# a progression: one entry per bar, a chord or a list of (chord, beats)
A_PROG = [D, A, Bm, Fsm, G, D, [(Em, 2), (A, 2)], D]
B_PROG = [G, Gm, D, B7, Em, A7, D, A7]
INTRO = [D, D, A, D]
H_PROG = [Bm, G, A, Fs, Bm, G, A, Fs, Em, Fs, Bm, Fs]

TUNE_A = mel("d5/.5 f#5/.5 a5/.5 f#5/.5 d6/1 a5/1 | c#6/.5 b5/.5 a5/.5 g5/.5 e5/1 a4/1 | "
             "b4/.5 d5/.5 f#5/.5 b5/.5 a5/.5 f#5/.5 d5/1 | c#5/.5 e5/.5 f#5/.5 a5/.5 c#6/2 | "
             "b5/.5 a5/.5 g5/.5 b5/.5 d6/1 b5/1 | a5/.5 f#5/.5 d5/.5 f#5/.5 a5/1 d5/1 | "
             "e5/.5 g5/.5 b5/.5 e6/.5 c#6/.5 a5/.5 e5/.5 g5/.5 | f#5/1 d5/.5 a4/.5 d5/2")
COUNTER_A = mel("f#3/2 a3/2 | e3/2 c#3/2 | d3/2 f#3/2 | c#3/2 a2/2 | b2/2 d3/2 | a2/2 f#3/2 | g3/2 a3/2 | d3/4")
TUNE_B = mel("d5/1.5 b4/.5 g4/1 b4/1 | d5/1.5 bb4/.5 g4/2 | a4/.5 b4/.5 a4/.5 f#4/.5 d5/2 | "
             "d#5/1 f#5/1 a5/1 f#5/1 | g5/1.5 f#5/.5 e5/1 b4/1 | c#5/1 e5/1 g5/1 a5/1 | "
             "f#5/1.5 e5/.5 d5/1 a4/1 | e5/.5 f#5/.5 g5/.5 a5/.5 c#6/1 e6/1")
BOX = mel("a5/.5 d6/.5 f#6/.5 d6/.5 a5/.5 d6/.5 f#6/.5 a6/.5 | a5/.5 d6/.5 f#6/.5 d6/.5 a5/.5 d6/.5 f#6/.5 a6/.5 | "
          "a5/.5 c#6/.5 e6/.5 c#6/.5 a5/.5 c#6/.5 e6/.5 g6/.5 | f#6/1 e6/.5 d6/.5 a5/2")
TUNE_H = mel("b5/.25 a5/.25 b5/.25 d6/.25 f#6/.5 d6/.5 b5/.5 f#5/.5 d5/.5 f#5/.5 | "
             "g5/.25 f#5/.25 g5/.25 b5/.25 d6/.5 b5/.5 g5/1 b5/1 | "
             "a5/.25 g5/.25 a5/.25 c#6/.25 e6/.5 c#6/.5 a5/.5 e5/.5 c#5/.5 e5/.5 | "
             "f#5/.5 a#5/.5 c#6/.5 f#6/.5 e6/.5 c#6/.5 a#5/1")
TUNE_H3 = mel("e5/.5 g5/.5 b5/.5 e6/.5 d6/.5 b5/.5 g5/1 | f#5/.5 a#5/.5 c#6/.5 e6/.5 c#6/1 a#5/1 | "
              "b5/.25 c#6/.25 d6/.25 e6/.25 f#6/1 d6/.5 b5/.5 f#5/1 | f#5/.5 a#5/.5 c#6/.5 e6/.5 f#6/2")


def bars(prog):
    """Yields (bar index, beat offset in the bar, chord, beats) for a progression."""
    for i, entry in enumerate(prog):
        if isinstance(entry, list):
            off = 0
            for ch, ln in entry:
                yield i, off, ch, ln
                off += ln
        else:
            yield i, 0, entry, 4


def band():
    drums = Track(9, 0, 96, 64, 25)
    return dict(tuba=Track(0, TUBA, 112, 60, 25), pizz=Track(1, PIZZ, 82, 44, 45),
                harpsi=Track(2, HARPSI, 66, 84, 45), clar=Track(3, CLARINET, 100, 70, 55),
                bassoon=Track(4, BASSOON, 84, 52, 50), xylo=Track(5, XYLO, 84, 76, 50),
                glock=Track(6, GLOCK, 70, 92, 70), box=Track(7, MUSICBOX, 76, 64, 80),
                oboe=Track(8, OBOE, 92, 58, 55), accord=Track(10, ACCORDION, 66, 40, 60),
                brass=Track(11, BRASS, 82, 64, 50), celesta=Track(12, CELESTA, 60, 96, 80), dr=drums)


def parts(t):
    tuba, pizz, harpsi, dr = t["tuba"], t["pizz"], t["harpsi"], t["dr"]

    def oompah(b, prog, vel=100, gallop=False):
        """The tuba on the strong beats (root, then the fifth), pizzicato and harpsichord chords on the off-beats;
        gallop: eighth-note tuba (root, fifth, octave, fifth) and pizzicato on every eighth."""
        for i, off, ch, ln in bars(prog):
            root, v = ch
            st = b + i * 4 + off
            if gallop:
                for k in range(int(ln * 2)):
                    p = root + (0, 7, 12, 7)[k % 4]
                    note(tuba, st + k * 0.5, 0.4, p, vel - (0 if k % 2 == 0 else 16))
                    for q in v:
                        note(pizz, st + k * 0.5 + 0.25, 0.2, q, vel - 40 + (6 if k % 2 else 0))
            else:
                for k in range(int(ln // 2)):
                    note(tuba, st + 2 * k, 0.9, root + (0 if k % 2 == 0 else 7), vel)
                for k in range(int(ln)):
                    if k % 2 == 1:
                        for q in v:
                            note(pizz, st + k, 0.3, q, vel - 34)
                            note(harpsi, st + k + 0.02, 0.4, q + 12, vel - 40)

    def ticks(b, nbars, vel=80, sixteenths=False, ratchet_last=False, kit=False, brush=False):
        """Wood blocks: tick (high) on the beats, tock (low) between them; sixteenth ticks in the hurry."""
        step = 0.25 if sixteenths else 0.5
        for k in range(int(nbars * 4 / step)):
            st = b + k * step
            beat = (k * step) % 4
            if beat % 1 == 0:
                note(dr, st, 0.1, HI_BLOCK if beat % 2 == 0 else LO_BLOCK, vel)
            elif not sixteenths or beat % 0.5 == 0:
                note(dr, st, 0.1, CLAVES if sixteenths else LO_BLOCK, vel - 26)
            else:
                note(dr, st, 0.1, CABASA, vel - 30)
            if kit and beat % 2 == 0:
                note(dr, st, 0.2, KICK, vel + 6)
            if kit and beat % 2 == 1:
                note(dr, st, 0.2, SNARE if not brush else STICK, vel - 10)
        if ratchet_last:
            end = b + nbars * 4
            note(dr, end - 1.0, 0.45, GUIRO_L, vel)
            note(dr, end - 0.5, 0.2, GUIRO_S, vel - 6)
            note(dr, end - 0.25, 0.2, GUIRO_S, vel)

    return oompah, ticks


def theme():
    t = band()
    clar, bassoon, xylo, glock, box, oboe, accord, brass, celesta, dr = (t[k] for k in (
        "clar", "bassoon", "xylo", "glock", "box", "oboe", "accord", "brass", "celesta", "dr"))
    oompah, ticks = parts(t)
    # intro: the clock ticks alone, the music box winds up, the tuba from bar 3
    ticks(0, 4, 74, ratchet_last=True)
    play(box, 0, BOX, 70, 0.9)
    oompah(8, INTRO[2:], 92)
    note(dr, 15.5, 0.3, TRIANGLE, 70)
    bar = 4

    oompah(bar * 4, A_PROG, 100)                 # A: the clarinet tune, staccato
    ticks(bar * 4, 8, 78, ratchet_last=True, kit=True, brush=True)
    play(clar, bar * 4, TUNE_A, 100, 0.55)
    note(dr, bar * 4, 0.5, CRASH, 70)
    bar += 8

    oompah(bar * 4, A_PROG, 104)                 # A': xylophone with the clarinet, a bassoon counter-line, glock
    ticks(bar * 4, 8, 82, ratchet_last=True, kit=True)
    play(xylo, bar * 4, TUNE_A, 92, 0.5)
    play(clar, bar * 4, TUNE_A, 78, 0.55, -12)
    play(bassoon, bar * 4, COUNTER_A, 86, 0.95, 12)
    for i, off, ch, ln in bars(A_PROG):
        if off == 0:
            note(glock, (bar + i) * 4 + 0.0, 1.0, ch[1][2] + 24, 66)
    note(dr, bar * 4, 0.5, CRASH, 76)
    bar += 8

    oompah(bar * 4, B_PROG, 96)                  # B: the bridge, an oboe tune, accordion chords, a ratchet
    ticks(bar * 4, 8, 70, ratchet_last=True)
    play(oboe, bar * 4, TUNE_B, 98, 0.92)
    play(bassoon, bar * 4, TUNE_B, 62, 0.9, -24)
    for i, off, ch, ln in bars(B_PROG):
        for q in ch[1]:
            note(accord, (bar + i) * 4, 1.6, q, 62)
            note(accord, (bar + i) * 4 + 2, 1.6, q, 56)
        note(celesta, (bar + i) * 4 + 3.5, 0.5, ch[1][2] + 24, 54)
    for i in (1, 3, 5, 7):
        note(dr, (bar + i) * 4 + 3, 0.4, GUIRO_L, 66)
    bar += 8

    oompah(bar * 4, A_PROG, 108)                 # A'': tutti
    ticks(bar * 4, 8, 86, ratchet_last=True, kit=True)
    play(clar, bar * 4, TUNE_A, 102, 0.55)
    play(xylo, bar * 4, TUNE_A, 86, 0.5, 12)
    play(glock, bar * 4, TUNE_A, 56, 0.5, 12)
    play(bassoon, bar * 4, COUNTER_A, 84, 0.95, 12)
    for i, off, ch, ln in bars(A_PROG):
        for q, l2 in ((0, 0.4), (1.5, 0.4), (3, 0.6)):
            if q >= off and q < off + ln:
                for p in ch[1]:
                    note(brass, (bar + i) * 4 + q, l2, p, 64)
    note(dr, bar * 4, 0.5, CRASH, 84)
    note(dr, (bar + 4) * 4, 0.5, CRASH, 74)
    bar += 8
    assert bar == 36
    return list(t.values()), 112, bar


def hurry():
    t = band()
    xylo, clar, brass, glock, dr = (t[k] for k in ("xylo", "clar", "brass", "glock", "dr"))
    oompah, ticks = parts(t)
    oompah(0, H_PROG, 108, gallop=True)
    ticks(0, 12, 84, sixteenths=True, kit=True, ratchet_last=True)
    play(xylo, 0, TUNE_H, 100, 0.6)
    play(xylo, 16, TUNE_H, 104, 0.6)
    play(clar, 16, TUNE_H, 76, 0.5, -12)
    play(xylo, 32, TUNE_H3, 106, 0.6)
    play(clar, 32, TUNE_H3, 82, 0.5, -12)
    play(glock, 32, TUNE_H3, 56, 0.5, 12)
    for i, ch in enumerate(H_PROG):
        for q in (0, 0.75, 1.5):            # brass stabs, 3-3-2
            for p in ch[1]:
                note(brass, i * 4 + q, 0.3, p, 60 + (8 if i >= 4 else 0))
        if i % 4 == 0:
            note(dr, i * 4, 0.5, CRASH, 76)
    return list(t.values()), 150, 12


if __name__ == "__main__":
    for name, fn in (("brassflow_theme", theme), ("brassflow_hurry", hurry)):
        tracks, bpm, nbars = fn()
        secs = render_loop(tracks, bpm, nbars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
