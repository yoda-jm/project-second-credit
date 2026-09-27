#!/usr/bin/env python3
"""Game 20 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own:
a little barn-dance string band. No quotations: nothing from the home-computer game's music, and no folk or
fiddle tune (Turkey in the Straw, Old MacDonald, Chicken Reel, Cluck Old Hen, Arkansas Traveler, Soldier's Joy,
Cripple Creek and the like: we steer clear of their opening figures, their chromatic "chicken" runs and their
call-and-answer shapes). The melodies were written for this game.
- henhouse_theme: jaunty, G major, 132 bpm, straight eighths in a bluegrass two-beat: upright bass on 1 and 3
  (root and fifth, a walk into each chord change), guitar boom-chuck and a mandolin chop on 2 and 4, banjo
  forward rolls in eighths over the fifth-string drone, brushes and a washboard (guiro and cabasa). Form:
  intro 4 (banjo alone, the band falls in) | A 8 (fiddle) | B 8 (harmonica) | A' 8 (the banjo takes the tune,
  fiddle long notes under it) | C 8 (E minor colours, fiddle and harmonica in thirds) | A'' 8 (tutti, the
  harmonica an octave down) = 44 bars (80 s).
- henhouse_goose: the goose is loose: the same band, 168 bpm, up a tone to A major, the bass in driving
  eighths, busier brushes: the A tune pushed with fiddle and banjo together, an eighth-note chase in the
  relative minor on the fiddle with harmonica stabs and trombone "honks" sliding down, then the tune again with
  the harmonica on top. 24 bars (34 s).
Usage: python3 tools/audio/henhouse_music.py
-> godot/games/henhouse/audio/music/henhouse_theme.ogg, henhouse_goose.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop, TPB

OUT = "godot/games/henhouse/audio/music/"
KICK, STICK, BRUSH_TAP, BRUSH_SLAP, BRUSH_SWIRL, CLOSED, PEDAL, CRASH, RIDE, CABASA, GUIRO_S, GUIRO_L, COWBELL, \
    WOODBLOCK = 36, 37, 38, 40, 39, 42, 44, 49, 51, 69, 73, 74, 56, 76
BANJO, FIDDLE, HARMONICA, UPRIGHT, GUITAR, TROMBONE, BRUSH_KIT = 105, 110, 22, 32, 25, 57, 40
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SHIFT = [0]  # a transposition for every note played (the goose chase is up a tone)


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


def bend(track, beat, value):
    v = max(0, min(16383, int(value)))
    track.events.append((int(beat * TPB), bytes([0xE0 | track.ch, v & 0x7F, v >> 7])))


def band():
    drums = Track(9, 0, 104, 64, 30)
    drums.events.append((0, bytes([0xC9, BRUSH_KIT])))
    mando = Track(5, GUITAR, 80, 84, 35)
    mando.events.insert(0, (0, bytes([0xB5, 0, 16])))  # bank 16, program 25: the mandolin in FluidR3
    bone = Track(6, TROMBONE, 92, 50, 45)
    bone.events += [(0, bytes([0xB6, 101, 0])), (0, bytes([0xB6, 100, 0])), (0, bytes([0xB6, 6, 12])),
                    (0, bytes([0xB6, 38, 0]))]  # a pitch-bend range of an octave, for the honks
    return dict(bass=Track(0, UPRIGHT, 112, 60, 25), banjo=Track(1, BANJO, 96, 48, 35),
                fid=Track(2, FIDDLE, 100, 76, 50), harp=Track(3, HARMONICA, 92, 58, 45),
                gtr=Track(4, GUITAR, 84, 40, 35), mando=mando, bone=bone, dr=drums)


# ---------------------------------------------------------------------------------------------------------------
# chords as (bass root, voicing around middle C), G major
G, C, D, D7, Em, Am, A7, E7, B7 = ((43, [55, 59, 62]), (48, [55, 60, 64]), (50, [54, 57, 62]), (50, [54, 57, 60]),
                                   (40, [55, 59, 64]), (45, [57, 60, 64]), (45, [55, 61, 64]), (40, [56, 59, 62]),
                                   (47, [54, 57, 63]))
INTRO = [[G], [G], [C], [D7]]
A_PROG = [[G], [G], [C], [G], [Em], [A7], [D7], [G]]
B_PROG = [[C], [C], [G], [G], [Am], [D7], [G, E7], [Am, D7]]
C_PROG = [[Em], [C], [G], [D], [Em], [C], [A7], [D7]]

TUNE_A = mel("b4/.5 d5/.5 g5/.5 d5/.5 e5/1 d5/.5 b4/.5 | g4/.5 a4/.5 b4/.5 d5/.5 g5/1.5 r/.5 | "
             "e5/.5 g5/.5 c6/.5 g5/.5 e5/.5 c5/.5 e5/.5 g5/.5 | b5/1 a5/.5 g5/.5 d5/1 r/1 | "
             "e5/.5 f#5/.5 g5/.5 b5/.5 e6/1 d6/.5 b5/.5 | c#6/.5 a5/.5 e5/.5 a5/.5 g5/1 e5/.5 c#5/.5 | "
             "d5/.5 f#5/.5 a5/.5 c6/.5 b5/.5 a5/.5 f#5/.5 d5/.5 | g5/1.5 d5/.5 g4/1 r/1")
UNDER_A = mel("d4/2 b3/2 | d4/2 g4/2 | e4/2 g4/2 | d4/4 | g4/2 b4/2 | a4/2 g4/2 | f#4/2 c5/2 | b4/2 r/2")
TUNE_B = mel("e5/1.5 d5/.5 c5/1 e5/1 | g5/1 a5/.5 g5/.5 e5/2 | d5/1.5 b4/.5 g4/1 b4/1 | d5/.5 e5/.5 d5/.5 b4/.5 d5/2 | "
             "c5/1 e5/1 a5/1.5 g5/.5 | f#5/1 e5/.5 d5/.5 c5/1 a4/1 | b4/.5 d5/.5 g5/1 g#5/1 b5/1 | a5/1 e5/1 f#5/1 d5/1")
TUNE_C = mel("b5/1 g5/.5 e5/.5 b4/1 e5/1 | g5/.5 e5/.5 c5/.5 e5/.5 g5/1 c6/1 | b5/.5 a5/.5 g5/.5 d5/.5 b4/1 d5/1 | "
             "a5/1.5 f#5/.5 d5/1 r/1 | e6/1 d6/.5 b5/.5 g5/1 b5/1 | c6/.5 b5/.5 a5/.5 g5/.5 e5/1 g5/1 | "
             "a5/.5 g5/.5 e5/.5 c#5/.5 a4/1 c#5/1 | d5/.5 e5/.5 f#5/.5 a5/.5 c6/1 a5/.5 f#5/.5")
# the harmony a third (or sixth) under TUNE_C, for the harmonica
HARM_C = mel("g5/1 e5/.5 b4/.5 g4/1 b4/1 | e5/.5 c5/.5 g4/.5 c5/.5 e5/1 g5/1 | g5/.5 f#5/.5 d5/.5 b4/.5 g4/1 b4/1 | "
             "f#5/1.5 d5/.5 a4/1 r/1 | b5/1 b5/.5 g5/.5 e5/1 g5/1 | a5/.5 g5/.5 e5/.5 e5/.5 c5/1 e5/1 | "
             "e5/.5 e5/.5 c#5/.5 a4/.5 e4/1 a4/1 | a4/.5 c5/.5 d5/.5 f#5/.5 a5/1 f#5/.5 d5/.5")
CHASE_PROG = [[Em], [C], [Em], [B7], [Em], [C], [Am, B7], [D7]]  # (becomes F sharp minor up a tone)
CHASE = mel("e5/.5 g5/.5 b5/.5 g5/.5 e6/.5 b5/.5 g5/.5 b5/.5 | c6/.5 g5/.5 e5/.5 g5/.5 c6/.5 e6/.5 c6/.5 g5/.5 | "
            "b5/.5 e5/.5 g5/.5 b5/.5 e6/.5 d6/.5 b5/.5 g5/.5 | f#5/.5 a5/.5 d#6/.5 a5/.5 b5/.5 f#5/.5 d#5/.5 f#5/.5 | "
            "g5/.5 b5/.5 e6/.5 b5/.5 g5/.5 e5/.5 g5/.5 b5/.5 | e6/.5 c6/.5 g5/.5 c6/.5 e6/.5 g6/.5 e6/.5 c6/.5 | "
            "a5/.5 c6/.5 e6/.5 c6/.5 b5/.5 d#6/.5 f#6/.5 d#6/.5 | d6/.5 c6/.5 a5/.5 f#5/.5 d5/.5 f#5/.5 a5/.5 c6/.5")


def parts(t):
    bass, banjo, gtr, mando, dr = t["bass"], t["banjo"], t["gtr"], t["mando"], t["dr"]

    def two_beat(b, bar, nxt=None, vel=96, drive=False):
        """The upright bass: root on 1, the fifth below on 3, a walk up into the next chord on 4 when it changes;
        with drive, eighths (root, root, fifth, root...) for the goose chase."""
        for off, ln, (root, v) in split(bar):
            lo = root - 12 if root >= 48 else root
            fifth = lo + 7 if lo + 7 <= 47 else lo - 5
            if drive:
                for k in range(int(ln * 2)):
                    note(bass, b + off + k * 0.5, 0.4, (lo, lo, fifth, lo)[k % 4], vel - (0 if k % 2 == 0 else 12))
                continue
            note(bass, b + off, 0.9, lo, vel)
            if ln == 4:
                note(bass, b + off + 2, 0.9, fifth, vel - 8)
                if nxt is not None and nxt[0][0] != root:  # walk into the change: a step from below
                    tgt = nxt[0][0] - 12 if nxt[0][0] >= 48 else nxt[0][0]
                    note(bass, b + 3, 0.45, fifth, vel - 14)
                    note(bass, b + 3.5, 0.45, tgt - 2 if (tgt - 2) % 12 not in (1, 3, 6, 8, 10) else tgt - 1, vel - 12)

    def chuck(b, bar, vel=70):
        """Guitar boom-chuck: a low strum on 1 and 3 (just the chord's lower notes), a full strum on 2 and 4;
        the mandolin chops short on 2 and 4."""
        for off, ln, (root, v) in split(bar):
            for q in range(int(ln)):
                beat = b + off + q
                if (off + q) % 2 == 0:
                    for k, p in enumerate(v[:2]):
                        note(gtr, beat + k * 0.02, 0.4, p - 12 if p > 57 else p, vel - 12)
                else:
                    for k, p in enumerate([root + 12 if root + 12 < 55 else root] + v):
                        note(gtr, beat + k * 0.015, 0.35, p, vel)
                    for p in v:
                        note(mando, beat, 0.12, p + 12, vel + 4)

    def roll(b, bar, vel=64):
        """Banjo forward rolls in eighths: middle, high, drone, repeated in a 3-3-2 over the fifth-string g."""
        for off, ln, (root, v) in split(bar):
            a, hi, drone = v[1] + 12, v[2] + 12, 67 + 12
            seq = (a, hi, drone, a, hi, drone, a, hi)
            for k in range(int(ln * 2)):
                note(banjo, b + off + k * 0.5, 0.45, seq[(int(off * 2) + k) % 8], vel + (10 if k in (0, 3, 6) else 0))

    def brushes(b, vel=62, busy=False, fill=False):
        """Brushes and washboard: soft kick on 1 and 3, brush slap on 2 and 4, a swirl through the bar, guiro
        scrapes on the offbeats and cabasa sixteenths like a thimbled washboard."""
        for q in (0, 2) if not busy else (0, 1.5, 2, 3.5):
            note(dr, b + q, 0.2, KICK, vel + 2)
        for q in (1, 3):
            note(dr, b + q, 0.2, BRUSH_SLAP, vel + 6)
        note(dr, b, 1.9, BRUSH_SWIRL, vel - 22)
        note(dr, b + 2, 1.9, BRUSH_SWIRL, vel - 22)
        for k in range(8):
            if k % 2 == 1:
                note(dr, b + k * 0.5, 0.2, GUIRO_S, vel - 18 + (6 if busy else 0))
        for k in range(16):
            note(dr, b + k * 0.25, 0.1, CABASA, vel - 24 + (10 if k % 4 == 2 else 0) + (4 if busy else 0))
        if fill:
            for k in range(4):
                note(dr, b + 3 + k * 0.25, 0.2, BRUSH_TAP, vel - 6 + 4 * k)
            note(dr, b + 3.5, 0.4, GUIRO_L, vel - 10)

    return two_beat, chuck, roll, brushes


def theme():
    SHIFT[0] = 0
    t = band()
    fid, harp, banjo, dr = t["fid"], t["harp"], t["banjo"], t["dr"]
    two_beat, chuck, roll, brushes = parts(t)

    def accomp(start, prog, vel=94, busy=False, rolls=True, nxt_first=None):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            nxt = prog[i + 1] if i + 1 < len(prog) else nxt_first
            two_beat(b, ch, nxt, vel)
            chuck(b, ch, vel - 24)
            if rolls:
                roll(b, ch, vel - 34)
            brushes(b, vel - 32, busy, fill=i == len(prog) - 1)

    bar = 0
    for i, ch in enumerate(INTRO):  # intro: the banjo rolls alone, then bass, guitar and brushes fall in
        b = i * 4
        roll(b, ch, 62 + 3 * i)
        if i >= 1:
            two_beat(b, ch, INTRO[i + 1] if i < 3 else A_PROG[0], 88)
        if i >= 2:
            chuck(b, ch, 66)
            brushes(b, 56, fill=i == 3)
    for k, p in enumerate((62, 66, 69)):  # a fiddle pickup into the tune
        note(fid, 14.5 + k * 0.5, 0.45, p, 70 + 6 * k)
    bar += 4

    accomp(bar, A_PROG, nxt_first=B_PROG[0])  # A: the fiddle tune
    play(fid, bar * 4, TUNE_A, 96, 0.92)
    bar += 8

    accomp(bar, B_PROG, 90, nxt_first=A_PROG[0])  # B: the harmonica, the fiddle answering with long notes
    play(harp, bar * 4, TUNE_B, 96, 0.95)
    for i, ch in enumerate(B_PROG):
        if i % 2 == 1:
            note(fid, (bar + i) * 4 + 2, 1.9, ch[-1][1][-1] + 12, 62)
    bar += 8

    accomp(bar, A_PROG, 94, busy=True, rolls=False, nxt_first=C_PROG[0])  # A': the banjo takes the tune
    play(banjo, bar * 4, TUNE_A, 100, 0.8)
    for i in range(8):  # fill the eighths between the tune's notes with drone notes, so the banjo keeps rolling
        for k in range(8):
            q = (bar + i) * 4 + k * 0.5
            if not any(abs(q - (bar * 4 + bt)) < 1e-6 for bt, _, _ in TUNE_A):
                note(banjo, q, 0.4, 79 if k % 3 else A_PROG[i][0][1][1] + 12, 62)
    play(fid, bar * 4, UNDER_A, 72, 0.97, 12)
    bar += 8

    accomp(bar, C_PROG, 92, nxt_first=A_PROG[0])  # C: E minor colours, fiddle and harmonica in thirds
    play(fid, bar * 4, TUNE_C, 96, 0.92)
    play(harp, bar * 4, HARM_C, 80, 0.92)
    bar += 8

    accomp(bar, A_PROG, 98, busy=True, nxt_first=INTRO[0])  # A'': tutti, the harmonica an octave down
    play(fid, bar * 4, TUNE_A, 100, 0.92)
    play(harp, bar * 4, TUNE_A, 76, 0.9, -12)
    note(dr, bar * 4, 0.5, CRASH, 50)
    bar += 8
    assert bar == 44
    return list(t.values()), 132, bar


def honk(track, beat, pitch, vel=84, length=0.5):
    """A trombone 'honk': a short blat that slides down a minor third at the end, like the goose."""
    steps = 8
    note(track, beat, length, pitch, vel)
    for k in range(1, steps + 1):
        bend(track, beat + length * (0.4 + 0.5 * k / steps), 8192 - 3 * 8192 / 12 * k / steps)
    bend(track, beat + length * 0.98, 8192)


def goose():
    SHIFT[0] = 2
    t = band()
    fid, harp, banjo, bone, dr = t["fid"], t["harp"], t["banjo"], t["bone"], t["dr"]
    two_beat, chuck, roll, brushes = parts(t)

    def accomp(start, prog, vel, drive=False, nxt_first=None):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            two_beat(b, ch, prog[i + 1] if i + 1 < len(prog) else nxt_first, vel, drive)
            chuck(b, ch, vel - 22)
            roll(b, ch, vel - 30)
            brushes(b, vel - 28, True, fill=i == len(prog) - 1)

    accomp(0, A_PROG, 96, nxt_first=CHASE_PROG[0])  # A: the tune pushed, fiddle and banjo together
    play(fid, 0, TUNE_A, 100, 0.85)
    play(banjo, 0, TUNE_A, 70, 0.6, 12, 0)
    note(dr, 0, 0.5, CRASH, 60)

    accomp(8, CHASE_PROG, 98, drive=True, nxt_first=A_PROG[0])  # the chase in the relative minor
    play(fid, 32, CHASE, 102, 0.85)
    for i, ch in enumerate(CHASE_PROG):
        b = (8 + i) * 4
        for q in (1.5, 3.5):
            for p in ch[-1][1]:
                note(harp, b + q, 0.35, p + 12, 80)
        if i % 2 == 0:  # the goose honks on the trombone
            honk(bone, b + 2, ch[0][1][-1] - 12 + (0 if i % 4 == 0 else 3), 88, 0.6)
    note(dr, 32, 0.5, CRASH, 66)

    accomp(16, A_PROG, 100, nxt_first=A_PROG[0])  # A again, the harmonica on top, the goose once more
    play(harp, 64, TUNE_A, 100, 0.85)
    play(fid, 64, UNDER_A, 80, 0.95, 12)
    honk(bone, 64 + 28 + 2, 62 - 12, 86, 0.6)
    note(dr, 64, 0.5, CRASH, 60)
    return list(t.values()), 168, 24


for name, song in (("henhouse_theme", theme), ("henhouse_goose", goose)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
