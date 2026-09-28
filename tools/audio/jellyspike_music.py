#!/usr/bin/env python3
"""Game 24 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own: a
sunny, bouncy beach band for two jelly blobs playing volleyball on a tropical beach. No quotations: nothing from
any volleyball game's music, no folk, calypso standard or classical tune, no existing video-game or film theme. The
melody bounces like the ball: a 3-3-2 skip up the tonic chord, a sixth that hangs in the air, a drop back to the sand.
- jellyspike_theme: F major, 120 bpm, straight eighths over a 3-3-2 lilt. A fingered bass (root, octave and fifth),
  a ukulele-like chop (a nylon guitar voiced high and short), marimba, a light kit (kick, rim, shaker, bongos,
  claves, a triangle). Form: intro 4 (ukulele, bass and a 3-3-2 marimba figure over shaker and claves, the kit
  in bar 3, a timbale fill) | A 8 (steel drums lead) | A' 8 (steel drums and vibraphone an octave up, a marimba
  counter-line, a strings pad) | B 8 (flute and steel drums sing a longer line over Bb, C, Am, Dm, the marimba
  answering) | C 4 (a breakdown in D minor: kalimba, congas and bass) | A'' 8 (tutti) = 40 bars (80.0 s).
- jellyspike_tense: match point, 152 bpm, D minor: a steel-drum riff over marimba sixteenths and driving bass
  eighths, then the riff an octave up with low toms and timbale rolls, the A major turn back to the top.
  16 bars (25.3 s).
Usage: python3 tools/audio/jellyspike_music.py
-> godot/games/jellyspike/audio/music/jellyspike_theme.ogg, jellyspike_tense.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/jellyspike/audio/music/"
KICK, RIM, SNARE, CLOSED, TAMB, CRASH, HI_BONGO, LO_BONGO, MUTE_CONGA, OPEN_CONGA, LO_CONGA, HI_TIMBALE, \
    LO_TIMBALE, CABASA, MARACAS, CLAVES, TRIANGLE, LO_TOM, MID_TOM = \
    36, 37, 38, 42, 54, 49, 60, 61, 62, 63, 64, 65, 66, 69, 70, 75, 81, 45, 47
VIBES, MARIMBA, NYLON, BASS, STRINGS, TIMPANI, FLUTE, KALIMBA, STEEL = 11, 12, 24, 33, 48, 47, 73, 108, 114
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def mel(text):
    """Parses a line like "c5/.5 f#5/1 r/.5" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens (after the
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
    drums = Track(9, 0, 92, 64, 25)
    drums.events.append((0, bytes([0xC9, 0])))
    return dict(bass=Track(0, BASS, 112, 64, 20), uke=Track(1, NYLON, 84, 40, 35), steel=Track(2, STEEL, 100, 76, 55),
                vibes=Track(3, VIBES, 70, 88, 60), strings=Track(4, STRINGS, 64, 64, 65),
                flute=Track(5, FLUTE, 84, 82, 55), mar=Track(6, MARIMBA, 90, 46, 40),
                kal=Track(7, KALIMBA, 84, 90, 50), timp=Track(8, TIMPANI, 84, 64, 40), dr=drums)


# chords as (bass root, voicing around middle C), F major and D minor
F, C, Dm, Bb, Gm, Am, A = ((41, [57, 60, 65]), (48, [55, 60, 64]), (50, [57, 62, 65]), (46, [58, 62, 65]),
                           (43, [55, 58, 62]), (45, [57, 60, 64]), (45, [57, 61, 64]))
INTRO = [[F], [Bb], [F], [C]]
A_PROG = [[F], [C], [Dm], [Bb], [F], [Gm, C], [Dm, Bb], [C]]
B_PROG = [[Bb], [C], [Am], [Dm], [Gm], [C], [F, Dm], [Gm, C]]
C_PROG = [[Dm], [Dm], [Bb], [C]]
TENSE_PROG = [[Dm], [Bb], [Gm], [A], [Dm], [Bb], [Gm, C], [A]]

TUNE_A = mel("f5/.75 a5/.75 c6/.5 a5/.5 c6/.5 d6/1 | c6/.75 bb5/.75 g5/.5 e5/1 r/1 | "
             "d5/.75 f5/.75 a5/.5 f5/.5 a5/.5 c6/1 | bb5/.5 a5/.5 f5/.5 d5/.5 f5/2 | "
             "f5/.75 a5/.75 c6/.5 a5/.5 c6/.5 f6/1 | d6/.5 bb5/.5 g5/1 e5/.5 g5/.5 c6/1 | "
             "a5/.75 f5/.75 d6/.5 bb5/.75 f5/.75 d6/.5 | c6/.75 bb5/.25 g5/.5 e5/.5 g5/1 r/1")
COUNTER_A = mel("r/2 f4/1 a4/1 | g4/2 c5/1 e4/1 | r/2 a4/1 d5/1 | d5/2 bb4/2 | "
                "r/2 f4/1 c5/1 | bb4/2 c5/1 e5/1 | d5/2 f5/2 | e5/2 c5/1 r/1")
TUNE_B = mel("r/.5 f5/.5 bb5/.5 d6/1 c6/.5 bb5/1 | c6/1.5 g5/.5 e5/1 g5/1 | a5/.5 c6/.5 e6/1.5 d6/.5 c6/1 | "
             "d6/2.5 r/.5 a5/.5 c6/.5 | d6/.5 bb5/.5 g5/1 bb5/.5 d6/.5 g6/1 | f6/.75 e6/.25 d6/.5 c6/.5 bb5/1 g5/1 | "
             "a5/.5 c6/.5 f6/1 e6/.5 d6/.5 a5/1 | bb5/1 a5/.5 g5/.5 e5/1 r/1")
TUNE_C = mel("a5/.5 d6/.5 f6/.5 d6/.5 a5/1 f5/1 | e5/.5 f5/.5 a5/.5 c6/1.5 a5/1 | "
             "d6/.75 c6/.75 bb5/.5 f5/1 d5/1 | e5/.5 g5/.5 c6/.5 e6/.5 g6/1 r/1")
TENSE = mel("d5/.5 f5/.5 a5/.5 d5/.5 f5/.5 a5/.5 d6/.5 c6/.5 | bb5/.75 a5/.75 f5/.5 d5/1 r/1 | "
            "g5/.5 bb5/.5 d6/.5 g5/.5 bb5/.5 d6/.5 g6/.5 f6/.5 | e6/.75 c#6/.75 a5/.5 e5/1 r/1 | "
            "a5/.5 d6/.5 f6/.5 a5/.5 d6/.5 f6/.5 a6/.5 g6/.5 | f6/.75 d6/.75 bb5/.5 f5/1 r/1 | "
            "g5/.5 bb5/.5 d6/1 e5/.5 g5/.5 c6/1 | c#6/.5 e6/.5 a6/1 g6/.5 e6/.5 c#6/1")


def parts(t):
    bass, uke, mar, dr = t["bass"], t["uke"], t["mar"], t["dr"]

    def bounce(b, bar, vel=100, drive=False):
        """The bass: a bouncing root, octave and fifth (1, 1a, 2&, 3, 3&, 4, 4&); with drive, eighths (the tense)."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root >= 45 else root
            if drive:
                for k in range(int(ln * 2)):
                    note(bass, b + off + k * 0.5, 0.35, lo + (7 if k % 4 == 3 else 0), vel - (0 if k % 2 == 0 else 12))
                continue
            pat = [(0, lo, 0.6), (0.75, lo, 0.4), (1.5, lo + 12, 0.4), (2, lo + 7, 0.6), (2.5, lo + 12, 0.4),
                   (3, lo, 0.4), (3.5, lo + 7, 0.4)]
            for q, p, L in pat:
                if q < ln:
                    note(bass, b + off + q, L, p, vel - (0 if q % 1 == 0 else 16))

    def chop(b, bar, vel=64):
        """The ukulele: short, bright chops voiced high and close, rolled fast."""
        for off, ln, (root, v) in split(bar):
            vs = [v[2], v[0] + 12, v[1] + 12, v[2] + 12]
            for q, down, accent in ((0, True, 8), (0.75, False, 0), (1.5, True, 4), (2, False, 0), (2.5, True, 4),
                                    (3, False, 0), (3.5, False, 2)):
                if q >= ln:
                    continue
                order = vs if down else vs[::-1]
                for k, p in enumerate(order):
                    note(uke, b + off + q + k * 0.01, 0.22, p, vel + accent - 3 * k)

    def skip(b, bar, vel=74):
        """The marimba's 3-3-2 figure through the chord."""
        for off, ln, (root, v) in split(bar):
            fig = [(0, v[0]), (0.75, v[2]), (1.5, v[1] + 12), (2, v[0] + 12), (2.75, v[2]), (3.5, v[1])]
            for q, p in fig:
                if q < ln:
                    note(mar, b + off + q, 0.4, p + 12, vel + (10 if q in (0, 2) else 0))

    def kit(b, vel=64, busy=False, fill=False, congas=False):
        for q in (0, 2) if not busy else (0, 1.5, 2, 3.5):
            note(dr, b + q, 0.2, KICK, vel + 4)
        for q in (1, 3):
            note(dr, b + q, 0.2, RIM if not busy else SNARE, vel - 10)
        for k in range(16 if busy else 8):
            st = k * (0.25 if busy else 0.5)
            note(dr, b + st, 0.1, MARACAS, vel - 22 + (10 if st % 1 == 0.5 else 0))
        for q in (0, 0.75, 1.5, 2.5, 3):  # claves: 3-2
            note(dr, b + q, 0.1, CLAVES, vel - 18)
        for q, dd in ((0.5, HI_BONGO), (1.5, LO_BONGO), (2.5, HI_BONGO), (3.25, HI_BONGO), (3.5, LO_BONGO)):
            note(dr, b + q, 0.1, dd, vel - 12)
        if congas:
            for q, dd in ((0.5, MUTE_CONGA), (1, OPEN_CONGA), (2.5, MUTE_CONGA), (3, LO_CONGA), (3.5, OPEN_CONGA)):
                note(dr, b + q, 0.1, dd, vel - 4)
        if fill:
            for k in range(8):
                note(dr, b + 2 + k * 0.25, 0.1, HI_TIMBALE if k < 4 else LO_TIMBALE, vel - 8 + 3 * k)

    return bounce, chop, skip, kit


def theme():
    t = band()
    bass, uke, steel, vibes, strings, flute, mar, kal, timp, dr = (t[k] for k in (
        "bass", "uke", "steel", "vibes", "strings", "flute", "mar", "kal", "timp", "dr"))
    bounce, chop, skip, kit = parts(t)

    def accomp(start, prog, vel=100, busy=False, pad=False, marimba=True):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            bounce(b, ch, vel)
            chop(b, ch, vel - 38)
            if marimba:
                skip(b, ch, vel - 34)
            kit(b, vel - 40, busy, fill=i == len(prog) - 1)
            if pad:
                for off, ln, (root, v) in split(ch):
                    for p in v:
                        note(strings, b + off, ln, p, 52)

    # intro: the ukulele, bass and the marimba skip, the kit falls in at bar 3, a timbale fill and a vibraphone lift into the tune
    for i, ch in enumerate(INTRO):
        b = i * 4
        chop(b, ch, 58 + 2 * i)
        skip(b, ch, 70 + 2 * i)
        bounce(b, ch, 88 + 3 * i)
        if i >= 2:
            kit(b, 54, fill=i == 3)
        else:  # a shaker and claves carry the groove over from the loop's end
            for k in range(8):
                note(dr, b + k * 0.5, 0.1, MARACAS, 44 + (10 if k % 2 else 0))
            for q in (0, 0.75, 1.5, 2.5, 3):
                note(dr, b + q, 0.1, CLAVES, 46)
    for k, p in enumerate((72, 77, 81, 84)):
        note(vibes, 14 + k * 0.5, 0.4, p, 60 + 6 * k)
    bar = 4

    accomp(bar, A_PROG)  # A: the steel drums lead
    play(steel, bar * 4, TUNE_A, 100, 0.8)
    note(dr, bar * 4, 0.5, CRASH, 48)
    bar += 8

    accomp(bar, A_PROG, 100, busy=True, pad=True, marimba=False)  # A': steel and vibes, a marimba counter-line
    play(steel, bar * 4, TUNE_A, 98, 0.8)
    play(vibes, bar * 4, TUNE_A, 56, 0.6, 12)
    play(mar, bar * 4, COUNTER_A, 84, 0.9, 12)
    note(dr, bar * 4, 0.5, CRASH, 54)
    bar += 8

    accomp(bar, B_PROG, 94, marimba=False)  # B: flute and steel drums sing, the marimba answers in broken chords
    play(flute, bar * 4, TUNE_B, 84, 0.95)
    play(steel, bar * 4, TUNE_B, 70, 0.8, -12)
    for i, ch in enumerate(B_PROG):
        for off, ln, (root, v) in split(ch):
            b = (bar + i) * 4 + off
            arp = [v[0], v[1], v[2], v[1] + 12] if ln == 4 else [v[0], v[2]]
            for k, p in enumerate(arp):
                note(mar, b + 2 + k * 0.5 if ln == 4 else b + 1 + k * 0.5, 0.4, p + 12, 68 + 3 * k)
        for off, ln, (root, v) in split(ch):
            for p in v:
                note(strings, (bar + i) * 4 + off, ln, p, 50)
    bar += 8

    for i, ch in enumerate(C_PROG):  # C: the breakdown in D minor: kalimba, congas and bass, the ukulele out
        b = (bar + i) * 4
        bounce(b, ch, 90)
        kit(b, 54, congas=True, fill=i == 3)
        root, v = ch[0]
        for q in (1, 3):
            for p in v:
                note(mar, b + q, 0.3, p, 56)
        if i == 3:
            for k in range(8):
                note(timp, b + k * 0.5, 0.3, 48, 54 + 5 * k)
    play(kal, bar * 4, TUNE_C, 96, 0.85)
    play(vibes, bar * 4, TUNE_C, 48, 0.6, -12)
    note(dr, bar * 4 + 12, 4, TRIANGLE, 44)
    bar += 4

    accomp(bar, A_PROG, 104, busy=True, pad=True)  # A'': tutti
    play(steel, bar * 4, TUNE_A, 102, 0.8)
    play(flute, bar * 4, TUNE_A, 64, 0.8, 12)
    play(vibes, bar * 4, TUNE_A, 50, 0.6)
    play(kal, bar * 4, COUNTER_A, 70, 0.8, 12)
    note(dr, bar * 4, 0.5, CRASH, 60)
    bar += 8
    assert bar == 40
    return list(t.values()), 120, bar


def tense():
    t = band()
    steel, mar, strings, timp, dr = (t[k] for k in ("steel", "mar", "strings", "timp", "dr"))
    bounce, chop, skip, kit = parts(t)
    for half in range(2):
        for i, ch in enumerate(TENSE_PROG):
            b = (half * 8 + i) * 4
            bounce(b, ch, 100 + 4 * half, drive=True)
            chop(b, ch, 56)
            kit(b, 64 + 4 * half, busy=True, congas=half == 1, fill=i == 7)
            for off, ln, (root, v) in split(ch):  # marimba sixteenths through the chord
                for k in range(int(ln * 4)):
                    p = v[k % 3] + 12 + (12 if k % 8 >= 6 else 0)
                    note(mar, b + off + k * 0.25, 0.2, p, 62 + (14 if k % 4 == 0 else 0))
                for p in v:
                    note(strings, b + off, ln, p, 48 + 10 * half)
            if half == 1:
                root = ch[0][0]
                for k in range(4):
                    note(timp, b + k, 0.3, root + 12 if root < 43 else root, 60 + (14 if k == 0 else 0))
                for q in (1.5, 3.5):
                    note(dr, b + q, 0.1, LO_TOM if i % 2 else MID_TOM, 70)
        play(steel, half * 32, TENSE, 100 + 2 * half, 0.8, 12 * half)
        note(dr, half * 32, 0.5, CRASH, 62 + 6 * half)
    return list(t.values()), 152, 16


for name, song in (("jellyspike_theme", theme), ("jellyspike_tense", tense)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
