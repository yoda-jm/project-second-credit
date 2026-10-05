#!/usr/bin/env python3
"""Game 35 (Four Torches) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any arcade game's music, no existing film, game or folk theme. A driving dark-fantasy dungeon march:
galloping low strings (cellos and basses), timpani and a heavy kit with toms, a church organ and string pads, horns
and trombones carrying the tune, tremolo strings and taiko in the breakdown. No voices: no choir or voice patches
(GM programs 52-54 are never used).
- fourtorches_theme: D minor, 128 bpm, 48 bars (90.0 s). Form: intro 4 (timpani and the galloping ostinato over Dm,
  the organ and a half-time kit) | A 8 (horns over Dm Bb C Dm Dm Bb Gm A) | A' 8 (strings take the tune, the horns answer
  low, organ pads) | B 8 (the lift: Bb F C Dm Bb F Gm A, the tune soaring on the organ and strings) | C 8 (breakdown:
  tremolo strings, taiko and toms, long horn calls over Dm Dm Bb Bb Gm Gm A A) | A'' 8 (tutti) | outro 4 (Dm Bb A A,
  winding back into the intro) -> back to the top.
- fourtorches_danger: low health, D minor, 152 bpm, 20 bars (31.6 s): a sixteenth-note string ostinato rocking on the
  minor second (D / Eb), a heartbeat kick, brass stabs and a high, anxious horn line over Dm Dm Eb Eb Dm Dm Bb A.
Usage: python3 tools/audio/fourtorches_music.py
-> godot/games/fourtorches/audio/music/fourtorches_theme.ogg, fourtorches_danger.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/fourtorches/audio/music/"
KICK, SNARE, CLOSED, CRASH, RIDE, LO_TOM, MID_TOM, HI_TOM, FLOOR_TOM = 36, 38, 42, 49, 51, 45, 47, 50, 41
ORGAN, CELLO, CBASS, TREM, PIZZ, STRINGS, SLOW_STR, TIMPANI, TROMBONE, TUBA, HORN, BRASS, TAIKO = (
    19, 42, 43, 44, 45, 48, 49, 47, 57, 58, 60, 61, 116)
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


# chords: (bass root, voicing round middle C)
Dm, Bb, C, A, Gm, F, Eb = ((38, [57, 62, 65]), (46, [58, 62, 65]), (48, [55, 60, 64]), (45, [57, 61, 64]),
                           (43, [55, 58, 62]), (41, [57, 60, 65]), (39, [55, 58, 63]))
INTRO = [Dm, Dm, Dm, A]
A_PROG = [Dm, Bb, C, Dm, Dm, Bb, Gm, A]
B_PROG = [Bb, F, C, Dm, Bb, F, Gm, A]
C_PROG = [Dm, Dm, Bb, Bb, Gm, Gm, A, A]
OUTRO = [Dm, Bb, A, A]
DANGER = [Dm, Dm, Eb, Eb, Dm, Dm, Bb, A]

TUNE_A = mel("d5/1.5 a4/.5 d5/.5 e5/.5 f5/1 | f5/1.5 d5/.5 bb4/1 d5/1 | e5/1.5 c5/.5 e5/.5 g5/.5 c6/1 | "
             "a5/2 r/1 a4/1 | d5/1.5 a4/.5 d5/.5 e5/.5 f5/.5 g5/.5 | a5/1 bb5/.5 a5/.5 g5/1 f5/1 | "
             "g5/.75 f5/.25 e5/.5 d5/.5 bb4/1 g5/1 | a5/2 c#5/1 e5/1")
ANSWER_A = mel("r/2 d4/1 f4/1 | r/2 d4/1 bb3/1 | r/2 c4/1 e4/1 | d4/2 a3/2 | r/2 d4/1 f4/1 | r/2 f4/1 d4/1 | "
               "r/2 g4/1 bb4/1 | a4/2 e4/2")
TUNE_B = mel("f5/1 bb5/1 d6/1.5 c6/.5 | c6/1 a5/1 f5/2 | g5/1 c6/1 e6/1.5 d6/.5 | d6/3 r/1 | "
             "d6/1 f6/1 bb5/1 d6/1 | c6/1.5 a5/.5 f5/1 a5/1 | bb5/1 a5/1 g5/1 bb5/1 | a5/2 g5/1 c#6/1")
CALLS = mel("d5/4 | f5/4 | f5/2 d5/2 | bb4/4 | g5/4 | bb5/2 a5/2 | a5/4 | c#6/2 e6/2")
TUNE_D = mel("a5/1.5 g5/.5 f5/1 e5/1 | d5/2 a5/2 | bb5/1.5 a5/.5 g5/1 bb5/1 | a5/4 | "
             "d6/1.5 c6/.5 a5/1 f5/1 | d5/2 f5/2 | f5/1 e5/1 d5/1 bb4/1 | a4/2 c#5/1 e5/1")


def band():
    drums = Track(9, 0, 100, 64, 35)
    return dict(horn=Track(0, HORN, 98, 54, 60), bone=Track(1, TROMBONE, 84, 74, 55),
                organ=Track(2, ORGAN, 64, 64, 85), cello=Track(3, CELLO, 100, 50, 40),
                cbass=Track(4, CBASS, 96, 78, 35), strings=Track(5, STRINGS, 86, 64, 75),
                pad=Track(6, SLOW_STR, 72, 40, 90), trem=Track(7, TREM, 76, 88, 70),
                timp=Track(8, TIMPANI, 104, 64, 50), brass=Track(10, BRASS, 80, 70, 50),
                taiko=Track(11, TAIKO, 100, 64, 40), tuba=Track(12, TUBA, 84, 64, 30), dr=drums)


def parts(t):
    cello, cbass, timp, dr, organ, pad = t["cello"], t["cbass"], t["timp"], t["dr"], t["organ"], t["pad"]

    def gallop(b, ch, vel=92):
        """The galloping ostinato: cellos in eighth + two sixteenths, the basses on the beat an octave down."""
        root = ch[0] + 12
        for q in range(4):
            for st, ln in ((0, 0.45), (0.5, 0.22), (0.75, 0.22)):
                p = root + (12 if q == 2 and st == 0 else 0) + (7 if q == 3 and st == 0.75 else 0)
                note(cello, b + q + st, ln, p, vel - (0 if st == 0 else 14) + (6 if q == 0 else 0))
            note(cbass, b + q, 0.8, ch[0], vel - 6)

    def timpani(b, ch, vel=96, roll=False):
        root = ch[0] if ch[0] >= 41 else ch[0] + 12
        note(timp, b, 0.9, root, vel)
        note(timp, b + 2, 0.9, root + (7 if root + 7 <= 57 else -5), vel - 14)
        if roll:
            for k in range(8):
                note(timp, b + 2 + k * 0.25, 0.25, root, vel - 30 + 4 * k)

    def kit(b, vel=88, fill=False, half=False):
        note(dr, b, 0.2, KICK, vel + 6)
        note(dr, b + 1.5, 0.2, KICK, vel - 6)
        note(dr, b + 2, 0.2, KICK, vel)
        if not half:
            note(dr, b + 3.5, 0.2, KICK, vel - 10)
        for q in ((2,) if half else (1, 3)):
            note(dr, b + q, 0.2, SNARE, vel)
        for k in range(8):
            note(dr, b + k * 0.5, 0.1, RIDE if half else CLOSED, vel - 34 + (8 if k % 2 == 0 else 0))
        if fill:
            for k, d in enumerate((HI_TOM, HI_TOM, MID_TOM, MID_TOM, LO_TOM, LO_TOM, FLOOR_TOM, FLOOR_TOM)):
                note(dr, b + 2 + k * 0.25, 0.2, d, vel - 14 + 3 * k)

    def chord(track, b, ch, ln, vel, shift=0):
        for p in ch[1]:
            note(track, b, ln, p + shift, vel)

    return gallop, timpani, kit, chord


def theme():
    t = band()
    horn, bone, organ, strings, pad, trem, brass, taiko, tuba, dr, cello = (t[k] for k in (
        "horn", "bone", "organ", "strings", "pad", "trem", "brass", "taiko", "tuba", "dr", "cello"))
    gallop, timpani, kit, chord = parts(t)

    def section(start, prog, vel=92, drums=True):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            gallop(b, ch, vel)
            timpani(b, ch, vel, roll=i == len(prog) - 1)
            if drums:
                kit(b, vel - 6, fill=i == len(prog) - 1)

    # intro: timpani and the gallop over Dm, the organ swelling in, the kit from bar 3
    for i, ch in enumerate(INTRO):
        b = i * 4
        gallop(b, ch, 90 + 2 * i)
        timpani(b, ch, 94 + 2 * i, roll=i == 3)
        chord(organ, b, ch, 4, 68 + 4 * i)
        note(organ, b, 4, ch[0], 68 + 4 * i)
        kit(b, 80 + 4 * i, fill=i == 3, half=i < 2)
    bar = 4

    section(bar, A_PROG)                        # A: the horns
    play(horn, bar * 4, TUNE_A, 100, 0.9)
    for i, ch in enumerate(A_PROG):
        chord(pad, (bar + i) * 4, ch, 4, 60)
    note(dr, bar * 4, 0.5, CRASH, 88)
    bar += 8

    section(bar, A_PROG, 96)                    # A': strings take the tune, horns and trombones answer, organ
    play(strings, bar * 4, TUNE_A, 96, 0.92)
    play(strings, bar * 4, TUNE_A, 76, 0.92, -12)
    play(bone, bar * 4, ANSWER_A, 86, 0.85)
    play(horn, bar * 4, ANSWER_A, 70, 0.85, 12)
    for i, ch in enumerate(A_PROG):
        chord(organ, (bar + i) * 4, ch, 4, 62)
    note(dr, bar * 4, 0.5, CRASH, 90)
    bar += 8

    section(bar, B_PROG, 100)                   # B: the lift, organ and strings soaring, brass punches
    play(organ, bar * 4, TUNE_B, 84, 0.95)
    play(strings, bar * 4, TUNE_B, 92, 0.95)
    play(horn, bar * 4, TUNE_B, 78, 0.9, -12)
    for i, ch in enumerate(B_PROG):
        b = (bar + i) * 4
        chord(pad, b, ch, 4, 64)
        for q, ln in ((0, 0.6), (2.5, 0.4)):
            chord(brass, b + q, ch, ln, 78)
        note(tuba, b, 3.5, ch[0], 80)
    note(dr, bar * 4, 0.5, CRASH, 96)
    bar += 8

    # C: the breakdown: tremolo strings, taiko and toms, long horn calls, no kit
    for i, ch in enumerate(C_PROG):
        b = (bar + i) * 4
        gallop(b, ch, 80)
        chord(trem, b, ch, 4, 66 + 3 * i)
        note(trem, b, 4, ch[0] + 12, 66 + 3 * i)
        for q, v in ((0, 104), (1.5, 84), (2, 96), (3, 80), (3.5, 86)):
            note(taiko, b + q, 0.3, 50, v)
        for k, d in enumerate((LO_TOM, FLOOR_TOM, LO_TOM, MID_TOM)):
            note(dr, b + 0.5 + k, 0.2, d, 70 + 4 * (i % 4))
        timpani(b, ch, 84, roll=i == 7)
        if i == 7:
            kit(b, 92, fill=True, half=True)
    play(horn, bar * 4, CALLS, 96, 0.95)
    play(bone, bar * 4, CALLS, 80, 0.95, -12)
    bar += 8

    section(bar, A_PROG, 104)                   # A'': tutti
    play(horn, bar * 4, TUNE_A, 104, 0.9)
    play(strings, bar * 4, TUNE_A, 96, 0.92, 12)
    play(bone, bar * 4, ANSWER_A, 90, 0.85)
    for i, ch in enumerate(A_PROG):
        b = (bar + i) * 4
        chord(organ, b, ch, 4, 66)
        note(tuba, b, 3.5, ch[0], 84)
        for q, ln in ((0, 0.5), (1.5, 0.4), (3, 0.5)):
            chord(brass, b + q, ch, ln, 74)
    note(dr, bar * 4, 0.5, CRASH, 100)
    bar += 8

    # outro: the gallop winding down to the intro's level, the organ holding, a timpani roll into the top
    for i, ch in enumerate(OUTRO):
        b = (bar + i) * 4
        gallop(b, ch, 92 - 4 * i)
        timpani(b, ch, 92, roll=i == 3)
        chord(organ, b, ch, 4, 70 - 4 * i)
        note(organ, b, 4, ch[0], 66)
        kit(b, 84 - 4 * i, fill=i == 3, half=i < 3)
    play(horn, bar * 4, mel("d5/2 f5/1 e5/1 | d5/4 | c#5/4 | e5/2 a4/2"), 90, 0.95)
    note(dr, bar * 4, 0.5, CRASH, 90)
    bar += 4
    assert bar == 48
    return list(t.values()), 128, bar


def danger():
    t = band()
    horn, brass, cello, cbass, trem, timp, dr, strings, bone = (t[k] for k in (
        "horn", "brass", "cello", "cbass", "trem", "timp", "dr", "strings", "bone"))
    _, _, kit, chord = parts(t)
    prog = [Dm, Dm, Dm, A] + DANGER + DANGER
    for i, ch in enumerate(prog):
        b = i * 4
        root = ch[0] + 12
        # a sixteenth ostinato rocking on the minor second above the root
        seq = [root, root, root + 1, root, root + 12, root, root + 1, root]
        for k in range(16):
            note(cello, b + k * 0.25, 0.2, seq[k % 8], 84 + (14 if k % 4 == 0 else 0))
        note(cbass, b, 3.8, ch[0], 92)
        # a heartbeat: two kicks, then the timpani on 3
        for q, v in ((0, 104), (0.4, 84), (2, 100), (2.4, 80)):
            note(dr, b + q, 0.2, KICK, v)
        note(timp, b + 3, 0.5, root if root <= 57 else root - 12, 92)
        if i >= 4:
            chord(trem, b, ch, 4, 70 + (8 if i >= 12 else 0))
            for q in (1, 3):
                note(dr, b + q, 0.2, SNARE, 78 + (10 if i >= 12 else 0))
            for k in range(8):
                note(dr, b + k * 0.5, 0.1, CLOSED, 56 + (10 if k % 2 == 0 else 0))
            for q, ln in ((0, 0.3), (1.75, 0.3), (2.5, 0.4)):
                chord(brass, b + q, ch, ln, 80 if q == 0 else 70)
        if i in (3, 11, 19):
            for k, d in enumerate((HI_TOM, MID_TOM, LO_TOM, FLOOR_TOM, HI_TOM, MID_TOM, LO_TOM, FLOOR_TOM)):
                note(dr, b + 2 + k * 0.25, 0.2, d, 80 + 3 * k)
        if i in (4, 12):
            note(dr, b, 0.5, CRASH, 96)
    play(horn, 12 * 4, TUNE_D, 100, 0.9)
    play(strings, 12 * 4, TUNE_D, 80, 0.9, 12)
    play(bone, 4 * 4, mel("d4/4 | f4/4 | eb4/4 | g4/4 | f4/4 | d4/4 | d4/4 | c#4/4"), 82, 0.95)
    return list(t.values()), 152, len(prog)


if __name__ == "__main__":
    for name, fn in (("fourtorches_theme", theme), ("fourtorches_danger", danger)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
