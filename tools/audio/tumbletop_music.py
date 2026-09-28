#!/usr/bin/env python3
"""Game 22 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. The tune is our own: a
bright, bouncy toybox band for a creature hopping round a pyramid in the clouds. No quotations: nothing from the
arcade game's sounds, no nursery rhyme, no classical piece, no existing video-game tune. The melody hops like the
hero: broken chords leaping up by fourths and fifths and tumbling back down in steps.
- tumbletop_theme: F major, 144 bpm, straight eighths. A bouncy acoustic bass (root, fifth, a hop up the octave),
  offbeat marimba chords, a light kit with a shaker and claps. Form: intro 4 (marimba ostinato and bass, the kit falls
  in) | A 8 (marimba lead, glockenspiel an octave up) | B 8 (a soft square lead sings a longer line, the marimba
  answers in broken chords) | A' 8 (steel drums on the tune, pizzicato under it) | C 8 (a breakdown: kalimba
  arpeggios, claps, the bass hopping in octaves, the glockenspiel twinkling) | A'' 8 (tutti) = 44 bars (73.3 s).
Usage: python3 tools/audio/tumbletop_music.py
-> godot/games/tumbletop/audio/music/tumbletop_theme.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/tumbletop/audio/music/"
KICK, SNARE, CLAP, CLOSED, OPEN_HAT, CRASH, TAMB, SHAKER, HI_WOOD, LO_WOOD, TRIANGLE = \
    36, 38, 39, 42, 46, 49, 54, 70, 76, 77, 81
MARIMBA, GLOCK, PIZZ, BASS, SQUARE, STEEL, KALIMBA, STANDARD_KIT = 12, 9, 45, 32, 80, 114, 108, 0
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def mel(text):
    """Parses a line like "c5/.5 f5/1 r/.5" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens (after the
    letter), r is a rest; '|' bar marks are checked and ignored."""
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


def play(track, start, line, vel, legato=0.9, shift=0, accent=6):
    for beat, length, pitch in line:
        note(track, start + beat, length * legato, pitch + shift, vel + (accent if beat % 1 == 0 else 0))


def split(bar):
    """A bar's chords as (offset, beats, chord): one chord fills the bar, two split it in half."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    drums = Track(9, 0, 96, 64, 25)
    drums.events.append((0, bytes([0xC9, STANDARD_KIT])))
    return dict(bass=Track(0, BASS, 112, 64, 20), mar=Track(1, MARIMBA, 100, 50, 40),
                glock=Track(2, GLOCK, 70, 84, 55), sq=Track(3, SQUARE, 64, 70, 50), steel=Track(4, STEEL, 88, 44, 45),
                pizz=Track(5, PIZZ, 84, 90, 35), kal=Track(6, KALIMBA, 92, 36, 45), comp=Track(7, MARIMBA, 76, 80, 35),
                dr=drums)


# chords as (bass root, voicing around middle C), F major
F, C, Dm, Bb, Gm, Am = ((41, [57, 60, 65]), (48, [55, 60, 64]), (50, [57, 62, 65]), (46, [58, 62, 65]),
                        (43, [58, 62, 67]), (45, [57, 60, 64]))
INTRO = [[F], [F], [Bb], [C]]
A_PROG = [[F], [C], [Dm], [Bb], [F], [Gm, C], [Dm, Bb], [C]]
B_PROG = [[Bb], [C], [Am], [Dm], [Gm], [C], [F, Dm], [Gm, C]]
C_PROG = [[Dm], [Dm], [Bb], [Bb], [Gm], [Gm], [C], [C]]

TUNE_A = mel("c5/.5 f5/.5 a5/.5 f5/.5 c6/1 a5/.5 f5/.5 | g5/.5 e5/.5 c5/.5 e5/.5 g5/1.5 r/.5 | "
             "a5/.5 f5/.5 d5/.5 f5/.5 a5/.5 d6/.5 c6/.5 a5/.5 | bb5/1 a5/.5 g5/.5 f5/1 d5/1 | "
             "c5/.5 f5/.5 a5/.5 c6/.5 f6/1 c6/.5 a5/.5 | bb5/.5 g5/.5 d5/.5 g5/.5 e5/.5 g5/.5 c6/.5 bb5/.5 | "
             "a5/.5 f5/.5 d5/.5 a5/.5 bb5/.5 f5/.5 d5/.5 bb4/.5 | c5/.5 e5/.5 g5/.5 bb5/.5 c6/1 r/1")
TUNE_B = mel("d6/1.5 c6/.5 bb5/1 f5/1 | g5/1.5 a5/.5 bb5/1 c6/1 | e5/1 a5/1 c6/1.5 b5/.5 | a5/2 f5/1 d5/1 | "
             "bb5/1.5 a5/.5 g5/1 d5/1 | e5/.5 g5/.5 c6/1 e6/1.5 d6/.5 | c6/1 a5/1 f5/1 a5/1 | g5/1 bb5/1 c6/1.5 r/.5")
INTRO_OST = mel("f5/.5 c5/.5 a5/.5 c5/.5 f5/.5 c5/.5 a5/.5 c6/.5 | f5/.5 c5/.5 a5/.5 c5/.5 f5/.5 c5/.5 a5/.5 c6/.5 | "
                "f5/.5 d5/.5 bb5/.5 d5/.5 f5/.5 d5/.5 bb5/.5 d6/.5 | g5/.5 e5/.5 c6/.5 e5/.5 g5/.5 bb5/.5 c6/1")


def parts(t):
    bass, comp, dr = t["bass"], t["comp"], t["dr"]

    def bounce(b, bar, vel=100, octaves=False):
        """The bass: root on 1, the fifth on 2, a hop up the octave on the 'and', root on 3, the fifth on 4; with
        octaves, root and octave in eighths (the breakdown)."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root >= 48 else root
            fifth = lo + 7
            if octaves:
                for k in range(int(ln * 2)):
                    note(bass, b + off + k * 0.5, 0.3, lo + (12 if k % 2 else 0), vel - (10 if k % 2 else 0))
                continue
            pat = [(0, lo, 0.8), (1, fifth, 0.4), (1.5, lo + 12, 0.35), (2, lo, 0.8), (3, fifth, 0.4), (3.5, lo + 12, 0.3)]
            for q, p, L in pat:
                if q < ln:
                    note(bass, b + off + q, L, p, vel - (0 if q % 2 == 0 else 12))

    def skank(b, bar, vel=70):
        """Offbeat marimba chords (the bounce), a little softer on the second and fourth 'and'."""
        for off, ln, (root, v) in split(bar):
            for q in (0.5, 1.5, 2.5, 3.5):
                if q < ln:
                    for k, p in enumerate(v):
                        note(comp, b + off + q + k * 0.008, 0.25, p + 12, vel - (8 if q in (1.5, 3.5) else 0))

    def kit(b, vel=64, busy=False, fill=False, claps=False):
        for q in (0, 2) if not busy else (0, 1.5, 2, 3.5):
            note(dr, b + q, 0.2, KICK, vel + 6)
        for q in (1, 3):
            note(dr, b + q, 0.2, CLAP if claps else SNARE, vel - (0 if claps else 6))
        for k in range(8):
            note(dr, b + k * 0.5, 0.1, SHAKER, vel - 18 + (8 if k % 2 == 0 else 0))
            if k % 2 == 1:
                note(dr, b + k * 0.5, 0.1, CLOSED, vel - 14)
        if fill:
            for k, dd in enumerate((HI_WOOD, HI_WOOD, LO_WOOD, LO_WOOD)):
                note(dr, b + 3 + k * 0.25, 0.1, dd, vel - 4 + 3 * k)

    return bounce, skank, kit


def theme():
    t = band()
    bass, mar, glock, sq, steel, pizz, kal, comp, dr = (t[k] for k in ("bass", "mar", "glock", "sq", "steel", "pizz",
                                                                        "kal", "comp", "dr"))
    bounce, skank, kit = parts(t)

    def accomp(start, prog, vel=100, busy=False, claps=False, comp_vel=66):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            bounce(b, ch, vel)
            skank(b, ch, comp_vel)
            kit(b, vel - 38, busy, fill=i == len(prog) - 1, claps=claps)

    # intro: the marimba ostinato and the bass; the kit falls in at bar 3; a glockenspiel sparkle into the tune
    play(mar, 0, INTRO_OST, 86, 0.8)
    for i, ch in enumerate(INTRO):
        b = i * 4
        bounce(b, ch, 88 + 3 * i)
        if i >= 2:
            kit(b, 56, fill=i == 3)
    for k, p in enumerate((72, 77, 81, 84)):
        note(glock, 14 + k * 0.5, 0.4, p + 12, 60 + 6 * k)
    bar = 4

    accomp(bar, A_PROG)  # A: marimba lead, glockenspiel an octave up
    play(mar, bar * 4, TUNE_A, 104, 0.8)
    play(glock, bar * 4, TUNE_A, 62, 0.6, 12)
    note(dr, bar * 4, 0.5, CRASH, 50)
    bar += 8

    accomp(bar, B_PROG, 96, comp_vel=58)  # B: the square lead sings, the marimba answers in broken chords
    play(sq, bar * 4, TUNE_B, 84, 0.95)
    for i, ch in enumerate(B_PROG):
        for off, ln, (root, v) in split(ch):
            b = (bar + i) * 4 + off
            arp = [v[0], v[1], v[2], v[1] + 12] if ln == 4 else [v[0], v[2]]
            for k, p in enumerate(arp):
                note(mar, b + 2 + k * 0.5 if ln == 4 else b + 1 + k * 0.5, 0.4, p + 12, 72 + 3 * k)
    bar += 8

    accomp(bar, A_PROG, 100, busy=True)  # A': steel drums on the tune, pizzicato an octave down
    play(steel, bar * 4, TUNE_A, 96, 0.85)
    play(pizz, bar * 4, TUNE_A, 70, 0.5, -12)
    note(dr, bar * 4, 0.5, CRASH, 56)
    bar += 8

    for i, ch in enumerate(C_PROG):  # C: the breakdown: kalimba arpeggios, claps, the bass in octaves
        b = (bar + i) * 4
        bounce(b, ch, 94, octaves=True)
        kit(b, 58, claps=True, fill=i == 7)
        root, v = ch[0]
        arp = [v[0], v[1], v[2], v[0] + 12, v[1] + 12, v[2], v[1], v[0] + 12] if i % 2 == 0 else \
              [v[2] + 12, v[1] + 12, v[0] + 12, v[2], v[1], v[0], v[1], v[2]]
        for k, p in enumerate(arp):
            note(kal, b + k * 0.5, 0.45, p + 12, 80 + (10 if k % 4 == 0 else 0))
        if i % 2 == 1:  # the glockenspiel twinkles on the top notes
            for k, p in enumerate((v[2] + 24, v[1] + 24)):
                note(glock, b + 2.5 + k * 0.75, 0.5, p, 58)
        if i >= 6:
            for q in (0, 1, 2, 3):
                note(dr, b + q, 0.1, TAMB, 50 + 6 * q)
    note(dr, bar * 4 + 28, 4, TRIANGLE, 44)
    bar += 8

    accomp(bar, A_PROG, 104, busy=True, claps=True)  # A'': tutti
    play(mar, bar * 4, TUNE_A, 104, 0.8)
    play(steel, bar * 4, TUNE_A, 80, 0.8, 12)
    play(glock, bar * 4, TUNE_A, 56, 0.5, 12)
    play(pizz, bar * 4, TUNE_A, 66, 0.5, -12)
    note(dr, bar * 4, 0.5, CRASH, 60)
    bar += 8
    assert bar == 44
    return list(t.values()), 144, bar


tracks, bpm, bars = theme()
os.makedirs(OUT, exist_ok=True)
secs = render_loop(tracks, bpm, bars, OUT + "tumbletop_theme.ogg", gain=0.6, rms_db=-18.3)
print(f"wrote tumbletop_theme.ogg ({secs:.1f} s loop)")
