#!/usr/bin/env python3
"""Game 21 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own:
a little mining band with the manic hurry of an 8-bit tune, played on real instruments. No quotations: nothing
from the home-computer game's music, no classical piece (in particular not "In the Hall of the Mountain King":
we avoid its stepwise climb up the minor scale and its repeated-note answer; our tune opens with a leap from
the fifth down to the tonic and skips round the chord), and no mining or work song ("Heigh-Ho", "Sixteen
Tons", "Clementine" and the like). The melodies were written for this game.
- deepbreath_theme: jaunty but tense, G minor, 150 bpm, straight eighths: tuba oom on 1 and 3 (root and fifth,
  a step into each chord change), pizzicato strings pah on 2 and 4, a light kit (kick, snare, closed
  hat), an anvil on the "and" of 4 and pickaxe woodblocks. Form: intro 4 (tuba and anvil, the pizzicato falls
  in) | A 8 (xylophone and pizzicato in octaves) | B 8 (the accordion in B flat major, pizzicato answering) |
  A' 8 (accordion on the tune, xylophone an octave up) | C 8 (a clockwork breakdown: xylophone ostinato over a
  tuba walk, anvil on every beat 2 and 4) | A'' 8 (tutti) = 44 bars (70.4 s).
- deepbreath_air: the air is running out: the same band, 184 bpm, up a tone to A minor, the tuba in driving
  eighths, a clock tick on the woodblock on every beat, tremolo strings: the A tune clipped short (breathless
  gaps), the clockwork ostinato with accordion gasps (short chords that swell and cut), the tune once more with
  the accordion shrill on top. 24 bars (31.3 s).
Usage: python3 tools/audio/deepbreath_music.py
-> godot/games/deepbreath/audio/music/deepbreath_theme.ogg, deepbreath_air.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/deepbreath/audio/music/"
KICK, STICK, SNARE, CLOSED, PEDAL, OPEN_HAT, CRASH, TAMB, HI_WOOD, LO_WOOD, CLAVES, TRIANGLE = \
    36, 37, 38, 42, 44, 46, 49, 54, 76, 77, 75, 81
PIZZ, TUBA, XYLO, ACCORDION, AGOGO, TREMOLO, STANDARD_KIT = 45, 58, 13, 21, 113, 44, 0
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SHIFT = [0]  # a transposition for every note played (the air variant is up a tone)


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


def band():
    drums = Track(9, 0, 100, 64, 25)
    drums.events.append((0, bytes([0xC9, STANDARD_KIT])))
    return dict(tuba=Track(0, TUBA, 110, 60, 25), pizz=Track(1, PIZZ, 100, 44, 40),
                xylo=Track(2, XYLO, 96, 80, 40), acc=Track(3, ACCORDION, 88, 70, 45),
                anvil=Track(4, AGOGO, 76, 90, 50), trem=Track(5, TREMOLO, 60, 34, 60), dr=drums)


# ---------------------------------------------------------------------------------------------------------------
# chords as (bass root, voicing around middle C), G minor
Gm, Cm, D7, Eb, Bb, F, Ab, D = ((43, [55, 58, 62]), (48, [55, 60, 63]), (50, [54, 57, 60]), (51, [55, 58, 63]),
                                (46, [53, 58, 62]), (41, [53, 57, 60]), (44, [56, 60, 63]), (50, [54, 57, 62]))
INTRO = [[Gm], [Gm], [Cm], [D7]]
A_PROG = [[Gm], [Gm], [Cm], [D7], [Eb], [Cm], [D7], [Gm]]
B_PROG = [[Eb], [Bb], [F], [Bb], [Eb], [Bb], [Cm], [D7]]
C_PROG = [[Cm], [Cm], [Gm], [Gm], [Ab], [Ab], [D7], [D7]]

TUNE_A = mel("d5/.5 r/.5 g4/.5 bb4/.5 d5/.5 g5/.5 f5/.5 d5/.5 | eb5/.5 d5/.5 bb4/.5 a4/.5 g4/1.5 r/.5 | "
             "eb5/.5 r/.5 c5/.5 g4/.5 eb5/.5 g5/.5 c6/1 | a5/.5 f#5/.5 d5/.5 c5/.5 a4/1 d5/1 | "
             "bb4/.5 eb5/.5 g5/.5 bb5/.5 g5/.5 eb5/.5 bb4/1 | c6/1 bb5/.5 g5/.5 eb5/.5 c5/.5 g5/1 | "
             "f#5/.5 a5/.5 d6/.5 c6/.5 a5/.5 f#5/.5 d5/.5 c5/.5 | bb4/.5 a4/.5 g4/1 d4/1 r/1")
TUNE_B = mel("g5/1.5 f5/.5 eb5/1 bb4/1 | d5/.5 f5/.5 bb5/1 a5/.5 f5/.5 d5/1 | c5/1 f5/1 a5/1.5 g5/.5 | f5/1 d5/1 bb4/2 | "
             "eb5/.5 g5/.5 bb5/.5 g5/.5 c6/1 bb5/1 | d6/1 bb5/.5 f5/.5 d5/1 f5/1 | g5/.5 eb5/.5 c5/.5 eb5/.5 g5/1 c6/1 | "
             "a5/1 f#5/1 d5/.5 e5/.5 f#5/1")
ANSWER_B = mel("r/3 bb4/.5 g4/.5 | r/3 d5/.5 bb4/.5 | r/3 c5/.5 a4/.5 | r/2 f4/.5 bb4/.5 d5/.5 f5/.5 | "
               "r/3 eb5/.5 bb4/.5 | r/3 f5/.5 d5/.5 | r/3 eb5/.5 c5/.5 | d5/.5 c5/.5 a4/.5 f#4/.5 d4/2")
OSTINATO = mel("c5/.5 g5/.5 eb5/.5 g5/.5 c6/.5 g5/.5 eb5/.5 g5/.5 | d5/.5 g5/.5 f5/.5 g5/.5 eb5/.5 g5/.5 d5/.5 g5/.5 | "
               "bb4/.5 d5/.5 g5/.5 d5/.5 bb5/.5 d5/.5 g5/.5 d5/.5 | a5/.5 g5/.5 f5/.5 d5/.5 bb4/.5 d5/.5 g4/1 | "
               "c5/.5 eb5/.5 ab5/.5 eb5/.5 c6/.5 ab5/.5 eb5/.5 ab5/.5 | g5/.5 eb5/.5 c5/.5 eb5/.5 ab5/1 g5/1 | "
               "f#5/.5 a5/.5 c6/.5 a5/.5 d6/.5 c6/.5 a5/.5 f#5/.5 | d5/.5 f#5/.5 a5/.5 c6/.5 d6/1 r/1")
WALK_C = mel("c3/1 d3/1 eb3/1 f3/1 | g3/1 f3/1 eb3/1 d3/1 | g2/1 a2/1 bb2/1 c3/1 | d3/1 c3/1 bb2/1 a2/1 | "
             "ab2/1 bb2/1 c3/1 eb3/1 | ab3/1 g3/1 f3/1 eb3/1 | d3/1 f#2/1 a2/1 c3/1 | d3/1 a2/1 d2/2")


def parts(t):
    tuba, pizz, anvil, dr = t["tuba"], t["pizz"], t["anvil"], t["dr"]

    def oom(b, bar, nxt=None, vel=100, drive=False):
        """The tuba: root on 1, the fifth below on 3, a step into the next chord on 4 when it changes; with
        drive, eighths (root, root, fifth, root...) for the air variant."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root >= 48 else root
            fifth = lo + 7 if lo + 7 <= 47 else lo - 5
            if drive:
                for k in range(int(ln * 2)):
                    note(tuba, b + off + k * 0.5, 0.35, (lo, lo, fifth, lo)[k % 4], vel - (0 if k % 2 == 0 else 14))
                continue
            note(tuba, b + off, 0.8, lo, vel)
            if ln == 4:
                note(tuba, b + off + 2, 0.8, fifth, vel - 8)
                if nxt is not None and nxt[0][0] != root:
                    tgt = nxt[0][0] - 12 if nxt[0][0] >= 48 else nxt[0][0]
                    note(tuba, b + 3.5, 0.45, tgt + (1 if tgt + 1 != lo else 2), vel - 14)

    def pah(b, bar, vel=74):
        """Pizzicato strings: a short chord on 2 and 4 (the 'pah'), a lighter one on the 'and' of 4."""
        for off, ln, (root, v) in split(bar):
            for q in range(int(ln)):
                if (off + q) % 2 == 1:
                    for k, p in enumerate(v):
                        note(pizz, b + off + q + k * 0.01, 0.2, p, vel)
            note(pizz, b + off + ln - 0.5, 0.15, v[-1], vel - 16)

    def kit(b, vel=64, busy=False, fill=False, tick=False):
        """A light kit: kick on 1 and 3, snare on 2 and 4, closed hats in eighths, the anvil on the 'and' of 4,
        pickaxe woodblocks on the offbeats; with tick, a clock tick on every beat."""
        for q in (0, 2) if not busy else (0, 1.5, 2, 2.5):
            note(dr, b + q, 0.2, KICK, vel + 4)
        for q in (1, 3):
            note(dr, b + q, 0.2, SNARE, vel)
        for k in range(8 if not busy else 16):
            step = 0.5 if not busy else 0.25
            note(dr, b + k * step, 0.1, CLOSED, vel - 14 + (8 if (k * step) % 1 == 0 else 0))
        note(anvil, b + 3.5, 0.3, 89, vel + 10)
        for q in (0.5, 2.5):
            note(dr, b + q, 0.1, HI_WOOD if q < 2 else LO_WOOD, vel - 12)
        if tick:
            for q in range(4):
                note(dr, b + q, 0.1, CLAVES if q % 2 == 0 else HI_WOOD, vel - 4)
        if fill:
            for k in range(4):
                note(dr, b + 3 + k * 0.25, 0.2, SNARE, vel - 8 + 5 * k)

    return oom, pah, kit


def theme():
    SHIFT[0] = 0
    t = band()
    tuba, pizz, xylo, acc, anvil, dr = t["tuba"], t["pizz"], t["xylo"], t["acc"], t["anvil"], t["dr"]
    oom, pah, kit = parts(t)

    def accomp(start, prog, vel=100, busy=False, nxt_first=None):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            oom(b, ch, prog[i + 1] if i + 1 < len(prog) else nxt_first, vel)
            pah(b, ch, vel - 26)
            kit(b, vel - 36, busy, fill=i == len(prog) - 1)

    for i, ch in enumerate(INTRO):  # intro: tuba and anvil alone, then the pizzicato and the kit fall in
        b = i * 4
        oom(b, ch, INTRO[i + 1] if i < 3 else A_PROG[0], 90 + 3 * i)
        note(anvil, b + 3.5, 0.3, 89, 70)
        if i >= 1:
            pah(b, ch, 66 + 3 * i)
        if i >= 2:
            kit(b, 60, fill=i == 3)
    for k, p in enumerate((62, 66, 69, 72)):  # a xylophone pickup up the D7 into the tune
        note(xylo, 14 + k * 0.5, 0.45, p + 12, 70 + 6 * k)
    bar = 4

    accomp(bar, A_PROG, nxt_first=B_PROG[0])  # A: xylophone and pizzicato in octaves
    play(xylo, bar * 4, TUNE_A, 100, 0.8)
    play(pizz, bar * 4, TUNE_A, 70, 0.6, -12)
    bar += 8

    accomp(bar, B_PROG, 96, nxt_first=A_PROG[0])  # B: the accordion in B flat, the pizzicato answering
    play(acc, bar * 4, TUNE_B, 90, 0.92)
    play(pizz, bar * 4, ANSWER_B, 84, 0.6)
    bar += 8

    accomp(bar, A_PROG, 100, busy=True, nxt_first=C_PROG[0])  # A': accordion on the tune, xylophone up high
    play(acc, bar * 4, TUNE_A, 92, 0.9)
    play(xylo, bar * 4, TUNE_A, 76, 0.7, 12)
    note(dr, bar * 4, 0.5, CRASH, 56)
    bar += 8

    for i, ch in enumerate(C_PROG):  # C: the clockwork breakdown, tuba walking, anvil on 2 and 4
        b = (bar + i) * 4
        pah(b, ch, 66)
        for q in (0, 2):
            note(dr, b + q, 0.2, KICK, 70)
        for q in (1, 3):
            note(anvil, b + q, 0.3, 89 if q == 1 else 86, 84)
            note(dr, b + q, 0.2, STICK, 60)
        for k in range(16):
            note(dr, b + k * 0.25, 0.1, CLOSED if k % 2 == 0 else PEDAL, 46 + (8 if k % 4 == 0 else 0))
        if i % 2 == 1:  # accordion stabs
            for p in ch[0][1]:
                note(acc, b + 1.5, 0.3, p + 12, 72)
                note(acc, b + 3.5, 0.3, p + 12, 66)
    play(xylo, bar * 4, OSTINATO, 94, 0.8)
    play(tuba, bar * 4, WALK_C, 96, 0.85)
    note(dr, bar * 4 + 28, 4, TRIANGLE, 40)
    bar += 8

    accomp(bar, A_PROG, 104, busy=True, nxt_first=INTRO[0])  # A'': tutti
    play(xylo, bar * 4, TUNE_A, 102, 0.8)
    play(acc, bar * 4, TUNE_A, 86, 0.9, -12)
    play(pizz, bar * 4, TUNE_A, 70, 0.6, -12)
    note(dr, bar * 4, 0.5, CRASH, 62)
    bar += 8
    assert bar == 44
    return list(t.values()), 150, bar


def air():
    SHIFT[0] = 2
    t = band()
    tuba, pizz, xylo, acc, anvil, trem, dr = t["tuba"], t["pizz"], t["xylo"], t["acc"], t["anvil"], t["trem"], t["dr"]
    oom, pah, kit = parts(t)

    def accomp(start, prog, vel, nxt_first=None):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            oom(b, ch, None, vel, drive=True)
            pah(b, ch, vel - 24)
            kit(b, vel - 32, True, fill=i == len(prog) - 1, tick=True)
            for p in ch[0][1]:  # tremolo strings hold the harmony, swelling each bar
                note(trem, b, 3.9, p, 58 + 4 * (i % 2))

    accomp(0, A_PROG, 100)  # A: the tune clipped short, breathless
    play(xylo, 0, TUNE_A, 104, 0.45)
    play(pizz, 0, TUNE_A, 76, 0.4, -12)
    note(dr, 0, 0.5, CRASH, 62)

    accomp(8, C_PROG, 100)  # the clockwork ostinato with accordion gasps
    play(xylo, 32, OSTINATO, 98, 0.6)
    for i, ch in enumerate(C_PROG):
        b = (8 + i) * 4
        for q, v in ((1.5, 70), (1.75, 84), (3.5, 70), (3.75, 88)):  # a gasp: a short swell and a cut
            for p in ch[0][1]:
                note(acc, b + q, 0.2, p + 12, v)
    note(dr, 32, 0.5, CRASH, 62)

    accomp(16, A_PROG, 104)  # the tune once more, the accordion shrill on top
    play(acc, 64, TUNE_A, 96, 0.55, 12)
    play(xylo, 64, TUNE_A, 90, 0.45)
    note(dr, 64, 0.5, CRASH, 66)
    return list(t.values()), 184, 24


for name, song in (("deepbreath_theme", theme), ("deepbreath_air", air)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
