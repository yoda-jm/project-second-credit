#!/usr/bin/env python3
"""Game 31 (Tinplate Turbo) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any arcade game's music, no existing film, game or folk theme. A bouncy toy-box band for wind-up tin
racers: a honky-tonk toy piano, xylophone and glockenspiel tunes, a clarinet and a piccolo, tuba and a driving
pizzicato bass, brass punches, and a kit with wood blocks that tick like clockwork. The intro winds the key up (wood
block clicks speeding up) before the band sets off.
- tinplate_theme: G major, 152 bpm, 48 bars (75.8 s). Form: intro 4 (the wind-up: wood blocks accelerating over
  G D C D, glockenspiel sparkles, the band falling in) | A 8 (toy piano tune over G D Em C G D C D, glockenspiel an
  octave up) | A' 8 (clarinet and xylophone, a pizzicato counter-line, brass punches) | B 8 (the lift: piccolo and
  glockenspiel over C D Bm Em Am D G D) | C 8 (the music box over Em C G D Em C Am D, a lighter kit of wood blocks and
  side-stick) | A'' 8 (tutti) | tag 4 (C D C D7, a snare roll back into the top).
- tinplate_menu: C major, 108 bpm, 14 bars (31.1 s), for the podium and the upgrade shop: a music box and celesta
  tune over pizzicato, soft strings and a tick-tock of wood blocks, C Am F G C Am Dm G F G Em Am Dm G.
No voices: no choir or voice patches.
Usage: python3 tools/audio/tinplate_music.py
-> godot/games/tinplate/audio/music/tinplate_theme.ogg, tinplate_menu.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/tinplate/audio/music/"
KICK, SNARE, SIDE, CLOSED, OPEN, CRASH, RIDE, TAMB, CLAP, HI_WB, LO_WB, COWBELL, LO_TOM, MID_TOM, HI_TOM = (
    36, 38, 37, 42, 46, 49, 51, 54, 39, 76, 77, 56, 45, 47, 50)
HONKY, CELESTA, GLOCK, MUSICBOX, XYLO, ABASS, PIZZ, STRINGS, TRUMPET, TUBA, BRASS, CLARINET, PICCOLO = (
    3, 8, 9, 10, 13, 32, 45, 48, 56, 58, 61, 71, 72)
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


# chords: (bass root, fifth, voicing round middle C)
G, D, Em, C, Bm, Am, D7, Dm, F = ((43, 50, [55, 59, 62]), (38, 45, [54, 57, 62]), (40, 47, [55, 59, 64]),
                                  (36, 43, [55, 60, 64]), (47, 42, [54, 59, 62]), (45, 40, [57, 60, 64]),
                                  (38, 45, [54, 57, 60]), (38, 45, [53, 57, 62]), (41, 36, [53, 57, 60]))
INTRO = [G, D, C, D]
A_PROG = [G, D, Em, C, G, D, C, D]
B_PROG = [C, D, Bm, Em, Am, D, G, D]
C_PROG = [Em, C, G, D, Em, C, Am, D]
TAG = [C, D, C, D7]
MENU = [C, Am, F, G, C, Am, Dm, G, F, G, Em, Am, Dm, G]

TUNE_A = mel("d5/.5 g5/.5 b5/.5 g5/.5 d6/.75 b5/.25 g5/1 | a5/.5 f#5/.5 d5/.5 f#5/.5 a5/1 r/1 | "
             "b5/.5 g5/.5 e5/.5 g5/.5 b5/.75 c6/.25 b5/.5 a5/.5 | g5/.5 e5/.5 c5/.5 e5/.5 g5/2 | "
             "d5/.5 g5/.5 b5/.5 d6/.5 g6/.75 f#6/.25 e6/.5 d6/.5 | c6/.5 a5/.5 f#5/.5 a5/.5 d6/1 c6/.5 a5/.5 | "
             "b5/.5 c6/.5 d6/.5 e6/.5 g6/.5 e6/.5 c6/.5 e6/.5 | d6/.75 c6/.25 b5/.5 a5/.5 f#5/.5 a5/.5 d6/1")
COUNTER_A = mel("b4/1 d5/1 g5/2 | f#5/1 a5/1 d5/2 | g5/1 b5/1 e5/2 | e5/1 g5/1 c5/2 | "
                "b4/1 d5/1 g5/2 | a5/1 f#5/1 d5/2 | e5/1 g5/1 c6/2 | a5/1 f#5/1 d5/2")
TUNE_B = mel("e6/1 d6/.5 c6/.5 g5/1 e5/1 | f#6/1 e6/.5 d6/.5 a5/2 | d6/.5 a5/.5 b5/.5 f#5/.5 b5/1 d6/1 | "
             "e6/.5 b5/.5 g5/.5 b5/.5 e6/2 | c6/.5 e6/.5 a6/1 g6/.5 e6/.5 c6/1 | d6/.5 f#6/.5 a6/1 f#6/.5 d6/.5 a5/1 | "
             "g6/.75 f#6/.25 g6/.5 d6/.5 b5/.5 d6/.5 g6/1 | a6/.5 g6/.5 f#6/.5 e6/.5 d6/.5 c6/.5 b5/.5 a5/.5")
TUNE_C = mel("b4/1.5 e5/.5 g5/1 f#5/1 | e5/1.5 c5/.5 e5/1 g5/1 | d5/1.5 b4/.5 d5/1 g5/1 | f#5/2 a5/2 | "
             "b5/1.5 a5/.5 g5/1 e5/1 | g5/1.5 e5/.5 c6/2 | a5/1 c6/1 e6/1 c6/1 | d6/1 a5/.5 f#5/.5 d5/1 r/1")
TUNE_TAG = mel("e5/.5 g5/.5 c6/.5 g5/.5 e6/1 c6/1 | f#5/.5 a5/.5 d6/.5 a5/.5 f#6/1 d6/1 | "
               "g5/.5 c6/.5 e6/.5 c6/.5 g6/1 e6/1 | a6/.5 f#6/.5 d6/.5 c6/.5 a5/.5 f#5/.5 d5/1")
TUNE_M = mel("e5/1 g5/1 c6/1.5 b5/.5 | a5/1 e5/1 c5/2 | f5/1 a5/1 c6/1 a5/1 | g5/1.5 f5/.5 e5/1 d5/1 | "
             "e5/1 g5/1 c6/1.5 d6/.5 | e6/1 c6/1 a5/2 | f5/1 a5/1 d6/1 c6/1 | b5/2 g5/2 | "
             "a5/1 c6/1 f6/1.5 e6/.5 | d6/1 b5/1 g5/2 | g5/1 b5/1 e6/1 d6/1 | c6/1.5 b5/.5 a5/2 | "
             "f5/1 a5/1 d6/1 f6/1 | e6/1 d6/1 b5/1 g5/1")


def band():
    return dict(piano=Track(0, HONKY, 92, 60, 40), glock=Track(1, GLOCK, 70, 80, 55),
                xylo=Track(2, XYLO, 84, 72, 40), clar=Track(3, CLARINET, 86, 54, 50),
                picc=Track(4, PICCOLO, 84, 70, 50), tuba=Track(5, TUBA, 96, 64, 25),
                bass=Track(6, ABASS, 98, 64, 20), pizz=Track(7, PIZZ, 76, 44, 45),
                brass=Track(8, BRASS, 80, 76, 40), box=Track(10, MUSICBOX, 92, 58, 60),
                strings=Track(11, STRINGS, 60, 40, 80), trumpet=Track(12, TRUMPET, 74, 60, 45),
                dr=Track(9, 0, 100, 64, 25))


def parts(t):
    piano, tuba, bass, dr = t["piano"], t["tuba"], t["bass"], t["dr"]

    def drive_bass(b, ch, vel=96, half=False):
        """Tuba on 1 and 3; the bass driving eighths root-root-octave-fifth; piano chords on the off-beats."""
        root, fifth, v = ch
        note(tuba, b, 0.9, root, vel)
        note(tuba, b + 2, 0.9, fifth if fifth < root + 12 else fifth - 12, vel - 6)
        pat = (root, root, root + 12, fifth if fifth > root else fifth + 12)
        for k in range(4 if half else 8):
            st = k * (1.0 if half else 0.5)
            note(bass, b + st, 0.4 if not half else 0.8, pat[k % 4], vel - (4 if k % 2 == 0 else 14))
        for q in (0.5, 1.5, 2.5, 3.5):
            for p in v:
                note(piano, b + q, 0.3, p, vel - 34)

    def kit(b, vel=86, light=False, fill=False):
        for q in (0, 2):
            note(dr, b + q, 0.2, KICK, vel + 4)
        if not light:
            note(dr, b + 2.5, 0.2, KICK, vel - 16)
        for q in (1, 3):
            note(dr, b + q, 0.2, SIDE if light else SNARE, vel - (14 if light else 2))
        for k in range(8):
            st = k * 0.5
            note(dr, b + st, 0.1, HI_WB if light else CLOSED, vel - (30 if light else 34) + (8 if st % 1 == 0 else 0))
        note(dr, b + 3.5, 0.1, LO_WB if not light else HI_WB, vel - 24)   # the clockwork tick
        if light:
            note(dr, b + 1.5, 0.1, LO_WB, vel - 30)
        else:
            note(dr, b + 1.5, 0.2, TAMB, vel - 30)
            note(dr, b + 3.5, 0.2, TAMB, vel - 30)
        if fill:
            for k, d in enumerate((SNARE, SNARE, HI_TOM, HI_TOM, MID_TOM, MID_TOM, LO_TOM, SNARE)):
                note(dr, b + 2 + k * 0.25, 0.2, d, vel - 18 + 3 * k)

    def punches(b, ch, vel=74):
        for q, ln in ((0.5, 0.3), (1.5, 0.3), (3.0, 0.5)):
            for p in ch[2]:
                note(t["brass"], b + q, ln, p + 12, vel)

    return drive_bass, kit, punches


def theme():
    t = band()
    drive_bass, kit, punches = parts(t)
    dr = t["dr"]

    def section(start, prog, vel=96, light=False):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            drive_bass(b, ch, vel, half=light)
            kit(b, vel - 10, light=light, fill=i == len(prog) - 1)

    # intro: the wind-up, wood blocks speeding up (quarters, eighths, triplets, sixteenths) over the chords
    for i, ch in enumerate(INTRO):
        b = i * 4
        step = (1.0, 0.5, 1 / 3, 0.25)[i]
        k = 0
        while k * step < 4 - 1e-6:
            note(dr, b + k * step, 0.1, HI_WB if k % 2 == 0 else LO_WB, 60 + 8 * i + (10 if k % 2 == 0 else 0))
            k += 1
        _, _, v = ch
        for j, p in enumerate([v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24, v[2] + 12, v[1] + 24, v[2] + 24,
                               v[0] + 24]):
            note(t["glock"], b + j * 0.5, 0.4, p, 54 + 5 * i)
        for p in v:
            note(t["strings"], b, 4, p, 46 + 6 * i)
        if i >= 1:
            note(t["tuba"], b, 0.9, ch[0], 80 + 4 * i)
            note(t["tuba"], b + 2, 0.9, ch[0], 76 + 4 * i)
        if i >= 2:
            for q in (0.5, 1.5, 2.5, 3.5):
                for p in v:
                    note(t["piano"], b + q, 0.3, p, 54 + 6 * i)
    for k in range(8):   # a snare roll into A
        note(dr, 14 + k * 0.25, 0.2, SNARE, 60 + 5 * k)
    bar = 4

    section(bar, A_PROG)                       # A: the toy piano tune, glockenspiel an octave up
    play(t["piano"], bar * 4, TUNE_A, 100, 0.8)
    play(t["glock"], bar * 4, TUNE_A, 58, 0.5, 12)
    note(dr, bar * 4, 0.5, CRASH, 84)
    bar += 8

    section(bar, A_PROG, 98)                   # A': clarinet and xylophone, pizzicato counter-line, brass punches
    play(t["clar"], bar * 4, TUNE_A, 92, 0.85, -12)
    play(t["xylo"], bar * 4, TUNE_A, 84, 0.6)
    play(t["pizz"], bar * 4, COUNTER_A, 74, 0.6)
    for i, ch in enumerate(A_PROG):
        punches((bar + i) * 4, ch, 64)
    note(dr, bar * 4, 0.5, CRASH, 86)
    bar += 8

    section(bar, B_PROG, 102)                  # B: the lift, piccolo and glockenspiel, trumpet low
    play(t["picc"], bar * 4, TUNE_B, 96, 0.85, -12)
    play(t["glock"], bar * 4, TUNE_B, 66, 0.55)
    play(t["trumpet"], bar * 4, TUNE_B, 66, 0.8, -24)
    for i, ch in enumerate(B_PROG):
        punches((bar + i) * 4, ch, 70)
        for p in ch[2]:
            note(t["strings"], (bar + i) * 4, 4, p + 12, 52)
    note(dr, bar * 4, 0.5, CRASH, 90)
    bar += 8

    section(bar, C_PROG, 90, light=True)       # C: the music box and clarinet over wood blocks
    play(t["box"], bar * 4, TUNE_C, 100, 0.9, 12)
    play(t["clar"], bar * 4, TUNE_C, 70, 0.95)
    for i, ch in enumerate(C_PROG):
        for p in ch[2]:
            note(t["strings"], (bar + i) * 4, 4, p, 50)
    note(dr, bar * 4, 0.5, CRASH, 74)
    bar += 8

    section(bar, A_PROG, 104)                  # A'': tutti
    play(t["piano"], bar * 4, TUNE_A, 104, 0.8)
    play(t["xylo"], bar * 4, TUNE_A, 86, 0.6)
    play(t["glock"], bar * 4, TUNE_A, 62, 0.5, 12)
    play(t["clar"], bar * 4, COUNTER_A, 80, 0.9)
    play(t["trumpet"], bar * 4, COUNTER_A, 60, 0.85, -12)
    for i, ch in enumerate(A_PROG):
        punches((bar + i) * 4, ch, 72)
    note(dr, bar * 4, 0.5, CRASH, 94)
    bar += 8

    for i, ch in enumerate(TAG):               # tag: a rising turnaround, a roll back into the top
        b = (bar + i) * 4
        drive_bass(b, ch, 100)
        kit(b, 92, fill=False)
        punches(b, ch, 76)
    play(t["xylo"], bar * 4, TUNE_TAG, 90, 0.6)
    play(t["piano"], bar * 4, TUNE_TAG, 92, 0.8)
    for k in range(16):
        note(dr, (bar + 3) * 4 + k * 0.25, 0.2, SNARE, 56 + 3 * k)
    bar += 4
    assert bar == 48
    return list(t.values()), 152, bar


def menu():
    t = band()
    box, cel, pizz, strings, dr, glock = (t["box"], Track(13, CELESTA, 80, 76, 60), t["pizz"], t["strings"],
                                          t["dr"], t["glock"])
    for i, ch in enumerate(MENU):
        b = i * 4
        root, fifth, v = ch
        for q, p in ((0, root + 12), (1, v[0]), (2, fifth + 12 if fifth < root else fifth), (3, v[0])):
            note(pizz, b + q, 0.5, p, 70 if q % 2 == 0 else 56)
        for p in v:
            note(strings, b, 4, p, 44)
        for q in (0.5, 1.5, 2.5, 3.5):   # celesta chords ticking on the off-beats
            for p in v:
                note(cel, b + q, 0.25, p + 12, 40)
        for q in range(4):   # tick-tock
            note(dr, b + q, 0.1, HI_WB if q % 2 == 0 else LO_WB, 46 + (6 if q == 0 else 0))
        if i % 4 == 3:
            note(dr, b + 3.5, 0.1, HI_WB, 40)
    play(box, 0, TUNE_M, 96, 0.95, 12)
    play(glock, 0, TUNE_M, 34, 0.5, 12)
    return list(t.values()) + [cel], 108, len(MENU)


if __name__ == "__main__":
    for name, fn in (("tinplate_theme", theme), ("tinplate_menu", menu)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
