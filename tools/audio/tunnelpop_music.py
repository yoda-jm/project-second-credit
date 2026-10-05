#!/usr/bin/env python3
"""Game 32 (Tunnel Pop) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation or imitation of any arcade game's music (in particular nothing like any arcade walking tune), and no
existing film, folk or nursery theme. A small, bouncy underground band that walks: a staccato plucked lead
(kalimba and pizzicato, then clarinet, xylophone and bassoon taking turns), a walking acoustic bass in quarters with
chromatic approach notes, marimba chord stabs on the back-beats, a glockenspiel counter-line, and light percussion
(brush kit, maracas shaker, wood blocks ticking like a clock). The tune skips up broken chords and trots back down
in steps, a little dig-dig-dig of repeated notes in places.
The pulse never stops (no rests across the band, no build-up intro), so the game can pause the music while the hero
stands still and resume it when he walks, at any point.
- tunnelpop_theme: F major, 132 bpm, 42 bars (76.4 s). Form: groove 2 (bass, marimba and percussion on F, C7) |
  A 8 (kalimba and pizzicato: F F Bb F Gm C7 F C7) | B 8 (xylophone, glockenspiel counter: Bb Bb F D7 Gm C7 Am-D7
  Gm-C7) | A' 8 (clarinet, pizzicato under it, the glockenspiel counter-line) | C 8 (bassoon tiptoeing in D minor,
  no bass drum: Dm A7 Dm A7 Bb F G7 C7) | A'' 8 (tutti) -> back to the top.
- tunnelpop_hurry: the last critter runs for it, F major, 168 bpm, 14 bars (20.0 s): the A tune on xylophone and
  clarinet, then six bars of running eighths through Dm A7 Bb F G7 C7; the bass still walks, shaker sixteenths, wood
  blocks in eighths, pizzicato arpeggios.
No voices: no choir or voice patches.
Usage: python3 tools/audio/tunnelpop_music.py
-> godot/games/tunnelpop/audio/music/tunnelpop_theme.ogg, tunnelpop_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/tunnelpop/audio/music/"
KICK, STICK, BRUSH_TAP, BRUSH_SLAP, BRUSH_SWIRL, CLOSED, PEDAL, CRASH, MARACAS, HI_WOOD, LO_WOOD, CABASA = (
    36, 37, 38, 40, 39, 42, 44, 49, 70, 76, 77, 69)
GLOCK, MARIMBA, XYLO, ABASS, PIZZ, BASSOON, CLARINET, KALIMBA, BRUSH_KIT = 9, 12, 13, 32, 45, 70, 71, 108, 40
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def mel(text):
    """Parses "e5/.75 g5/.5 r/1 | ..." into [(beat, length, pitch)]; '#' sharpens, 'b' flattens (after the letter),
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


# chords: (bass tones root, third, fifth, sixth or seventh, in the walking range; voicing round middle C)
F, Bb, C7, Gm, Dm, A7, D7, Am, G7 = (
    ((41, 45, 48, 50), [57, 60, 65]), ((46, 50, 53, 55), [58, 62, 65]), ((36, 40, 43, 46), [58, 64, 67]),
    ((43, 46, 50, 52), [58, 62, 67]), ((38, 41, 45, 47), [57, 62, 65]), ((45, 49, 52, 55), [55, 61, 64]),
    ((38, 42, 45, 48), [54, 57, 60]), ((45, 48, 52, 54), [57, 60, 64]), ((43, 47, 50, 53), [53, 59, 62]))
GROOVE = [F, C7]
A_PROG = [F, F, Bb, F, Gm, C7, F, C7]
B_PROG = [Bb, Bb, F, D7, Gm, C7, (Am, D7), (Gm, C7)]
C_PROG = [Dm, A7, Dm, A7, Bb, F, G7, C7]
HURRY = A_PROG + [Dm, A7, Bb, F, G7, C7]

TUNE_A = mel("f5/.5 r/.25 f5/.25 a5/.5 c6/.5 a5/.5 f5/.5 g5/1 | a5/.5 g5/.5 f5/.5 e5/.5 d5/.5 e5/.5 f5/1 | "
             "d6/.5 r/.25 d6/.25 bb5/.5 f5/.5 g5/.5 a5/.5 bb5/1 | a5/.75 g5/.25 f5/.5 c5/.5 f5/1 a5/1 | "
             "g5/.5 bb5/.5 d6/.5 bb5/.5 a5/.5 g5/.5 f5/.5 e5/.5 | e5/.5 g5/.5 c6/.5 bb5/.5 g5/1 e5/1 | "
             "f5/.5 a5/.5 c6/.5 f6/.5 e6/.5 c6/.5 a5/.5 f5/.5 | g5/.75 a5/.25 g5/.5 e5/.5 c5/1 e5/1")
COUNTER_A = mel("a5/2 c6/2 | c6/2 a5/2 | bb5/2 d6/2 | c6/4 | bb5/2 d6/2 | bb5/2 g5/2 | a5/2 c6/2 | bb5/2 e5/2")
TUNE_B = mel("f6/1 d6/.5 bb5/.5 c6/.5 d6/.5 f6/1 | d6/.5 eb6/.5 d6/.5 c6/.5 bb5/1 f5/1 | "
             "c6/1 a5/.5 f5/.5 g5/.5 a5/.5 c6/1 | a5/.5 c6/.5 f#5/.5 a5/.5 d6/1.5 c6/.5 | "
             "bb5/.5 d6/.5 g6/.5 d6/.5 bb5/.5 a5/.5 g5/1 | c6/.5 e6/.5 g6/.5 e6/.5 bb5/1 g5/1 | "
             "a5/.5 c6/.5 e6/1 f#6/.5 d6/.5 c6/1 | bb5/.5 g5/.5 d6/1 c6/.5 bb5/.5 g5/.5 e5/.5")
COUNTER_B = mel("d6/2 f6/2 | f6/4 | c6/2 a5/2 | c6/2 f#5/2 | g5/2 bb5/2 | bb5/2 e6/2 | e6/2 f#6/2 | d6/2 c6/2")
TUNE_C = mel("d5/.5 f5/.5 a5/.5 f5/.5 d5/.5 e5/.5 f5/1 | c#5/.5 e5/.5 g5/.5 e5/.5 c#5/.5 d5/.5 e5/1 | "
             "d5/.5 f5/.5 a5/.5 d6/.5 c6/.5 a5/.5 f5/1 | e5/.5 g5/.5 bb5/.5 a5/.5 g5/.5 e5/.5 c#5/1 | "
             "d5/.5 f5/.5 bb5/1 a5/.5 bb5/.5 c6/1 | a5/.5 c6/.5 f6/1 e6/.5 d6/.5 c6/1 | "
             "b5/.5 d6/.5 g6/.5 f6/.5 d6/.5 b5/.5 g5/1 | c6/.5 bb5/.5 g5/.5 e5/.5 c5/.5 e5/.5 g5/.5 bb5/.5")
TUNE_H = mel("d6/.5 a5/.5 f5/.5 a5/.5 d6/.5 e6/.5 f6/.5 d6/.5 | c#6/.5 a5/.5 e5/.5 a5/.5 c#6/.5 d6/.5 e6/.5 c#6/.5 | "
             "d6/.5 bb5/.5 f5/.5 bb5/.5 d6/.5 f6/.5 bb6/1 | a6/.5 g6/.5 f6/.5 c6/.5 a5/.5 c6/.5 f6/1 | "
             "g6/.5 f6/.5 d6/.5 b5/.5 g5/.5 b5/.5 d6/.5 f6/.5 | e6/.5 g6/.5 c7/.5 bb6/.5 g6/.5 e6/.5 c6/.5 bb5/.5")


def band():
    drums = Track(9, 0, 100, 64, 25)
    drums.events.append((0, bytes([0xC9, BRUSH_KIT])))
    return dict(kal=Track(0, KALIMBA, 100, 70, 40), pizz=Track(1, PIZZ, 84, 52, 40),
                clar=Track(2, CLARINET, 90, 66, 45), xylo=Track(3, XYLO, 90, 80, 40),
                glock=Track(4, GLOCK, 70, 88, 55), marimba=Track(5, MARIMBA, 82, 42, 35),
                bass=Track(6, ABASS, 112, 62, 20), bassoon=Track(7, BASSOON, 92, 58, 40), dr=drums)


def bars(prog):
    """A progression as (bar, beat offset, beats, chord, next chord): two chords in a bar split it in half."""
    flat = []
    for i, bar in enumerate(prog):
        cs = bar if isinstance(bar, tuple) and isinstance(bar[0], tuple) and len(bar[0]) == 2 \
            and isinstance(bar[0][1], list) else (bar,)
        for k, c in enumerate(cs):
            flat.append((i, k * 4 / len(cs), 4 / len(cs), c))
    return [(i, off, ln, c, flat[(j + 1) % len(flat)][3]) for j, (i, off, ln, c) in enumerate(flat)]


def parts(t):
    bass, marimba, pizz, dr = t["bass"], t["marimba"], t["pizz"], t["dr"]

    def walk(start, prog, vel=100, after=None):
        """Walking bass in short plucked quarters: root, third, fifth, then a chromatic step into the next root."""
        for k, (i, off, ln, ch, nxt) in enumerate(bars(prog)):
            if after is not None and k == len(bars(prog)) - 1:
                nxt = after
            b = (start + i) * 4 + off
            r, third, fifth, sixth = ch[0]
            nr = nxt[0][0]
            approach = nr - 1 if k % 2 == 0 else nr + 1
            line = [r, third, fifth, approach] if ln == 4 else [r, approach]
            if ln == 4 and (start + i) % 4 == 2:
                line = [r, fifth, sixth, approach]
            for q, p in enumerate(line):
                note(bass, b + q, 0.55, p, vel + (8 if q == 0 else 0))

    def stabs(start, prog, vel=60):
        """Marimba chord stabs on 2 and 4, a light one on the 'and' of 4."""
        for i, off, ln, ch, _ in bars(prog):
            b = (start + i) * 4 + off
            for q, v in (((1, vel), (3, vel), (3.5, vel - 18)) if ln == 4 else ((1, vel),)):
                for p in ch[1]:
                    note(marimba, b + q, 0.3, p + 12, v)

    def arp(start, prog, vel=56, step=0.5):
        """Pizzicato up and down the chord."""
        for i, off, ln, ch, _ in bars(prog):
            b = (start + i) * 4 + off
            v = ch[1]
            seq = [v[0], v[1], v[2], v[1] + 12, v[2] + 12, v[1] + 12, v[2], v[1]]
            for k in range(int(ln / step)):
                note(pizz, b + k * step, step * 0.6, seq[k % 8], vel + (10 if k % 2 == 0 else 0))

    def kit(start, nbars, vel=84, kick=True, wood=True, shaker=0.5, fill_every=8):
        """Brushes: soft kick on 1 and 3, brush slaps on 2 and 4, maracas, wood blocks ticking hi-lo on the beats."""
        for i in range(nbars):
            b = (start + i) * 4
            for q in (0, 2):
                if kick:
                    note(dr, b + q, 0.2, KICK, vel - 6)
            for q in (1, 3):
                note(dr, b + q, 0.2, BRUSH_SLAP, vel - 8)
            for k in range(int(4 / shaker)):
                st = k * shaker
                note(dr, b + st, 0.1, MARACAS, vel - 30 + (12 if st % 1 == 0.5 else 0))
            if wood:
                for q in range(4):
                    note(dr, b + q, 0.1, HI_WOOD if q % 2 == 0 else LO_WOOD, vel - 26 + (6 if q == 0 else 0))
            if (i + 1) % fill_every == 0:
                for k in range(4):
                    note(dr, b + 3 + k * 0.25, 0.2, BRUSH_TAP, vel - 20 + 5 * k)

    return walk, stabs, arp, kit


def theme():
    t = band()
    kal, pizz, clar, xylo, glock, bassoon, dr = (t[k] for k in ("kal", "pizz", "clar", "xylo", "glock", "bassoon",
                                                                 "dr"))
    walk, stabs, arp, kit = parts(t)
    bar = 0

    walk(bar, GROOVE, 96, after=F)           # groove: the band already walking, no lead
    stabs(bar, GROOVE, 56)
    kit(bar, 2, 80, fill_every=2)
    bar += 2

    walk(bar, A_PROG, 100, after=Bb)         # A: kalimba and pizzicato, staccato
    stabs(bar, A_PROG, 58)
    kit(bar, 8, 84)
    play(kal, bar * 4, TUNE_A, 100, 0.55)
    play(pizz, bar * 4, TUNE_A, 70, 0.4, -12)
    bar += 8

    walk(bar, B_PROG, 102, after=F)          # B: xylophone, glockenspiel counter
    stabs(bar, B_PROG, 60)
    kit(bar, 8, 86)
    play(xylo, bar * 4, TUNE_B, 96, 0.6)
    play(glock, bar * 4, COUNTER_B, 64, 0.7)
    arp(bar, B_PROG, 48)
    bar += 8

    walk(bar, A_PROG, 100, after=Dm)         # A': clarinet, pizzicato under it, glockenspiel counter
    stabs(bar, A_PROG, 58)
    kit(bar, 8, 84, shaker=0.25)
    play(clar, bar * 4, TUNE_A, 92, 0.5)
    play(pizz, bar * 4, TUNE_A, 62, 0.4, -12)
    play(glock, bar * 4, COUNTER_A, 62, 0.7, 12)
    bar += 8

    walk(bar, C_PROG, 96, after=F)           # C: bassoon tiptoeing in D minor, no bass drum
    stabs(bar, C_PROG, 52)
    kit(bar, 8, 78, kick=False)
    play(bassoon, bar * 4, TUNE_C, 96, 0.45)
    play(pizz, bar * 4, TUNE_C, 60, 0.35, 12)
    bar += 8

    walk(bar, A_PROG, 104, after=F)          # A'': tutti
    stabs(bar, A_PROG, 62)
    kit(bar, 8, 88, shaker=0.25)
    play(kal, bar * 4, TUNE_A, 100, 0.55)
    play(clar, bar * 4, TUNE_A, 78, 0.5, -12)
    play(xylo, bar * 4, TUNE_A, 70, 0.5, 12)
    play(glock, bar * 4, COUNTER_A, 60, 0.7, 12)
    arp(bar, A_PROG, 44)
    bar += 8
    assert bar == 42
    return list(t.values()), 132, bar


def hurry():
    t = band()
    clar, xylo, kal, glock = t["clar"], t["xylo"], t["kal"], t["glock"]
    walk, stabs, arp, kit = parts(t)
    walk(0, HURRY, 106)
    stabs(0, HURRY, 60)
    arp(0, HURRY, 52)
    kit(0, len(HURRY), 90, shaker=0.25, fill_every=4)
    for i in range(len(HURRY)):          # wood blocks on the off-beats too: eighths, urgent
        for q in (0.5, 1.5, 2.5, 3.5):
            note(t["dr"], i * 4 + q, 0.1, HI_WOOD, 58)
    play(xylo, 0, TUNE_A, 100, 0.5)
    play(clar, 0, TUNE_A, 84, 0.45, -12)
    play(xylo, 32, TUNE_H, 98, 0.5)
    play(kal, 32, TUNE_H, 80, 0.45, -12)
    play(glock, 32, mel("d6/4 | c#6/4 | d6/4 | c6/4 | b5/4 | bb5/4"), 58, 0.6, 12)
    return list(t.values()), 168, len(HURRY)


if __name__ == "__main__":
    for name, fn in (("tunnelpop_theme", theme), ("tunnelpop_hurry", hurry)):
        tracks, bpm, nbars = fn()
        secs = render_loop(tracks, bpm, nbars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
