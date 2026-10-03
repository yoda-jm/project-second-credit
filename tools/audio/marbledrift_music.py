#!/usr/bin/env python3
"""Game 27 (Marble Drift) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any arcade marble game's music (nor of any classical piece it borrowed), no existing film or game theme.
A driving, spacey synth band in the spirit of 80s arcade racers: octave-bouncing synth bass, sixteenth-note arpeggios,
a sawtooth lead, warm and sweeping pads over an electronic kit. The lead climbs a minor triad and falls back in a
3-3-2 push, like a marble taking a slope and rolling out.
- marbledrift_theme: E minor, 144 bpm, 48 bars (80.0 s). Form: intro 4 (sweep pad, the arpeggio and a crystal
  sparkle, the kit falls in) | A 8 (sawtooth lead over Em C D Bm Em C Am B, four on the floor) | A' 8 (the lead with
  a square lead an octave down, a string counter-line) | B 8 (the lift: C D G Em C D B, the lead soaring) | break 4
  (half time: the arpeggio, bass and pad alone, a tom roll) | C 8 (a darker square-lead tune over Am Em C D Am Em F B)
  | A'' 8 (tutti, the lead doubled at the octave) -> back to the top.
- marbledrift_hurry: the last ten seconds, E Phrygian, 154 bpm, 16 bars (24.9 s): sixteenth bass, a racing
  arpeggio, the lead in stabs over Em F Em F Am B Em B, then again an octave doubled with sixteenth hats and toms.
No voices: no choir or voice patches.
Usage: python3 tools/audio/marbledrift_music.py
-> godot/games/marbledrift/audio/music/marbledrift_theme.ogg, marbledrift_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/marbledrift/audio/music/"
KICK, CLAP, SNARE, CLOSED, OPEN, CRASH, RIDE, LO_TOM, MID_TOM, HI_TOM, TAMB = 36, 39, 38, 42, 46, 49, 51, 45, 47, 50, 54
SYNBASS, STRINGS, SQUARE, SAW, WARM, SWEEP, CRYSTAL, ATMOS, SYNBRASS = 38, 50, 80, 81, 89, 95, 98, 99, 62
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
Em, C, D, Bm, Am, G, B, F = ((40, [55, 59, 64]), (36, [55, 60, 64]), (38, [54, 57, 62]), (35, [54, 59, 62]),
                             (45, [57, 60, 64]), (43, [55, 59, 62]), (35, [54, 59, 63]), (41, [53, 57, 60]))
INTRO = [Em, Em, C, D]
A_PROG = [Em, C, D, Bm, Em, C, Am, B]
B_PROG = [C, D, G, Em, C, D, B, B]
BREAK = [Em, C, Am, B]
C_PROG = [Am, Em, C, D, Am, Em, F, B]
HURRY = [Em, F, Em, F, Am, B, Em, B]

TUNE_A = mel("e5/.75 g5/.75 b5/.5 a5/.5 g5/.5 e5/1 | e5/.5 g5/.5 c6/1 b5/.5 g5/.5 e5/1 | "
             "f#5/.75 a5/.75 d6/.5 c6/.5 a5/.5 f#5/1 | b5/1.5 a5/.5 f#5/1 d5/1 | "
             "e5/.75 g5/.75 b5/.5 e6/.5 d6/.5 b5/1 | c6/.5 b5/.5 g5/.5 e5/.5 g5/1 c6/1 | "
             "a5/.75 c6/.75 e6/.5 d6/.5 c6/.5 a5/1 | b5/1.5 a5/.5 f#5/1 d#5/1")
COUNTER_A = mel("b4/2 e5/2 | c5/2 g5/2 | a4/2 d5/2 | b4/4 | e5/2 g5/2 | e5/4 | c5/2 e5/2 | d#5/4")
TUNE_B = mel("g5/1 c6/1 e6/1.5 d6/.5 | f#6/1 e6/.5 d6/.5 a5/2 | b5/.5 d6/.5 g6/1.5 f#6/.5 d6/1 | e6/3 r/1 | "
             "e6/.5 d6/.5 c6/.5 g5/.5 c6/1 e6/1 | f#6/1 a6/1 f#6/.5 e6/.5 d6/1 | d#6/2 f#6/1 b6/1 | b6/3 r/1")
TUNE_C = mel("a4/.5 c5/.5 e5/.5 a5/1 g5/.5 e5/1 | g5/.5 f#5/.5 e5/1 b4/1 e5/1 | c5/.5 e5/.5 g5/.5 c6/1 b5/.5 g5/1 | "
             "a5/1.5 f#5/.5 d5/1 a5/1 | c6/.5 b5/.5 a5/1 e5/.5 a5/.5 c6/1 | b5/1.5 g5/.5 e5/2 | "
             "f5/.5 a5/.5 c6/1 a5/.5 f5/.5 c6/1 | b5/1 d#6/1 f#6/1 b5/1")
TUNE_H = mel("e5/.5 b5/.5 e6/.5 b5/.5 g5/.5 b5/.5 e6/.5 f#6/.5 | f6/.75 e6/.75 c6/.5 a5/1 f5/1 | "
             "e5/.5 b5/.5 e6/.5 b5/.5 g5/.5 b5/.5 g6/.5 f#6/.5 | f6/1 e6/.5 c6/.5 a5/2 | "
             "a5/.5 c6/.5 e6/.5 a5/.5 c6/.5 e6/.5 a6/.5 g6/.5 | f#6/.75 d#6/.75 b5/.5 f#5/1 a5/1 | "
             "g5/.5 b5/.5 e6/1 d#6/.5 e6/.5 g6/1 | f#6/1 d#6/1 b5/1 f#5/1")


def band():
    drums = Track(9, 0, 100, 64, 30)
    drums.events.append((0, bytes([0xC9, 24])))   # the electronic kit
    return dict(bass=Track(0, SYNBASS, 112, 64, 15), lead=Track(1, SAW, 92, 70, 60),
                lead2=Track(2, SQUARE, 76, 54, 55), arp=Track(3, SAW, 66, 40, 70),
                pad=Track(4, WARM, 80, 64, 90), sweep=Track(5, SWEEP, 70, 90, 110),
                strings=Track(6, STRINGS, 66, 30, 90), sparkle=Track(7, CRYSTAL, 62, 96, 120),
                atmos=Track(8, ATMOS, 56, 64, 120), brass=Track(10, SYNBRASS, 80, 80, 60), dr=drums)


def parts(t):
    bass, arp, pad, dr = t["bass"], t["arp"], t["pad"], t["dr"]

    def pulse(b, ch, vel=100, sixteenths=False):
        """The bass: driving eighths bouncing root and octave (sixteenths in the hurry)."""
        root, _ = ch
        lo = root - 12 if root >= 40 else root
        step = 0.25 if sixteenths else 0.5
        for k in range(int(4 / step)):
            p = lo + (12 if k % 2 else 0) if not sixteenths else lo + (12 if k % 4 == 2 else 0)
            note(bass, b + k * step, step * 0.8, p, vel - (0 if k % 2 == 0 else 14))

    def arpeggio(b, ch, vel=60, up=12):
        """Sixteenths up and down the chord over two octaves."""
        _, v = ch
        seq = [v[0], v[1], v[2], v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 12, v[2]]
        for k in range(16):
            note(arp, b + k * 0.25, 0.2, seq[k % 8] + up, vel + (12 if k % 4 == 0 else 0))

    def chord(b, ch, vel=56, beats=4):
        for p in ch[1]:
            note(pad, b, beats, p, vel)

    def kit(b, vel=88, full=True, half=False, fill=False, hats16=False):
        if half:
            note(dr, b, 0.2, KICK, vel)
            note(dr, b + 2, 0.2, SNARE, vel - 14)
        else:
            for q in (0, 1, 2, 3):
                note(dr, b + q, 0.2, KICK, vel + 4)
            if full:
                for q in (1, 3):
                    note(dr, b + q, 0.2, CLAP, vel - 8)
                    note(dr, b + q, 0.2, SNARE, vel - 26)
        step = 0.25 if hats16 else 0.5
        for k in range(int(4 / step)):
            st = k * step
            if st % 1 == 0.5 and full and not half:
                note(dr, b + st, 0.2, OPEN, vel - 30)
            else:
                note(dr, b + st, 0.1, CLOSED, vel - 34 + (8 if st % 1 == 0 else 0))
        if fill:
            for k, dd in enumerate((HI_TOM, HI_TOM, MID_TOM, MID_TOM, LO_TOM, LO_TOM, LO_TOM, LO_TOM)):
                note(dr, b + 2 + k * 0.25, 0.2, dd, vel - 20 + 3 * k)

    return pulse, arpeggio, chord, kit


def theme():
    t = band()
    lead, lead2, strings, sweep, sparkle, atmos, brass, dr = (t[k] for k in (
        "lead", "lead2", "strings", "sweep", "sparkle", "atmos", "brass", "dr"))
    pulse, arpeggio, chord, kit = parts(t)

    def section(start, prog, vel=100, pad=True, hats16=False):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            pulse(b, ch, vel)
            arpeggio(b, ch, vel - 46)
            if pad:
                chord(b, ch, vel - 48)
            kit(b, vel - 14, fill=i == len(prog) - 1, hats16=hats16)

    # intro: a sweep and the arpeggio, crystal sparkles, the bass in bar 2, the kit in bar 3 (a fill into A)
    for i, ch in enumerate(INTRO):
        b = i * 4
        arpeggio(b, ch, 46 + 6 * i)
        for p in ch[1]:
            note(sweep, b, 4, p + 12, 54)
        if i >= 1:
            pulse(b, ch, 80 + 6 * i)
        if i >= 2:
            kit(b, 74, full=i == 3, fill=i == 3)
    for k, (beat, p) in enumerate(((1.5, 88), (5.0, 83), (6.5, 91), (9.75, 88), (13.0, 95))):
        note(sparkle, beat, 1.5, p, 70)
    note(atmos, 0, 8, 64, 60)
    bar = 4

    section(bar, A_PROG)                       # A: the sawtooth lead
    play(lead, bar * 4, TUNE_A, 100, 0.86)
    note(dr, bar * 4, 0.5, CRASH, 80)
    bar += 8

    section(bar, A_PROG, 102, hats16=True)     # A': a square lead an octave down, a string counter-line
    play(lead, bar * 4, TUNE_A, 100, 0.86)
    play(lead2, bar * 4, TUNE_A, 70, 0.7, -12)
    play(strings, bar * 4, COUNTER_A, 70, 1.0, 12)
    note(dr, bar * 4, 0.5, CRASH, 84)
    bar += 8

    section(bar, B_PROG, 104)                  # B: the lift: the lead soars, synth brass punches the changes
    play(lead, bar * 4, TUNE_B, 102, 0.9)
    play(strings, bar * 4, TUNE_B, 56, 1.0, -12)
    for i, ch in enumerate(B_PROG):
        for q, ln in ((0, 0.4), (1.5, 0.4), (3, 0.9)):
            for p in ch[1]:
                note(brass, (bar + i) * 4 + q, ln, p, 64)
    note(dr, bar * 4, 0.5, CRASH, 88)
    for i in (3, 7):
        note(sweep, (bar + i) * 4, 4, B_PROG[i][1][2] + 12, 50)
    bar += 8

    for i, ch in enumerate(BREAK):             # break: half time, the arpeggio and bass, a sweep and sparkles
        b = (bar + i) * 4
        pulse(b, ch, 86)
        arpeggio(b, ch, 56, 24 if i % 2 else 12)
        for p in ch[1]:
            note(sweep, b, 4, p + 12, 58)
        kit(b, 74, half=True, fill=i == 3)
        note(sparkle, b + 1.5, 1.5, ch[1][2] + 24, 64)
    note(atmos, bar * 4, 16, 64, 56)
    bar += 4

    section(bar, C_PROG, 98)                   # C: a darker tune on the square lead, strings beneath
    play(lead2, bar * 4, TUNE_C, 98, 0.86)
    play(lead, bar * 4, TUNE_C, 50, 0.6, 12)
    for i, ch in enumerate(C_PROG):
        for p in ch[1]:
            note(strings, (bar + i) * 4, 4, p, 54)
    note(dr, bar * 4, 0.5, CRASH, 84)
    bar += 8

    section(bar, A_PROG, 106, hats16=True)     # A'': tutti, the lead doubled at the octave
    play(lead, bar * 4, TUNE_A, 104, 0.86)
    play(lead2, bar * 4, TUNE_A, 78, 0.8, -12)
    play(sparkle, bar * 4, TUNE_A, 44, 0.5, 12)
    play(strings, bar * 4, COUNTER_A, 74, 1.0, 12)
    note(dr, bar * 4, 0.5, CRASH, 92)
    bar += 8
    assert bar == 48
    return list(t.values()), 144, bar


def hurry():
    t = band()
    lead, lead2, strings, brass, dr = (t[k] for k in ("lead", "lead2", "strings", "brass", "dr"))
    pulse, arpeggio, chord, kit = parts(t)
    for half in range(2):
        for i, ch in enumerate(HURRY):
            b = (half * 8 + i) * 4
            pulse(b, ch, 104 + 4 * half, sixteenths=True)
            arpeggio(b, ch, 58 + 6 * half, 12)
            chord(b, ch, 50 + 6 * half)
            kit(b, 86 + 4 * half, hats16=True, fill=i == 7)
            for p in ch[1]:
                note(strings, b, 4, p + 12, 52 + 10 * half)
            for q in (0, 0.75, 1.5):            # brass stabs, 3-3-2
                for p in ch[1]:
                    note(brass, b + q, 0.3, p, 58 + 8 * half)
            if i % 2 == 0:
                note(dr, b, 0.5, CRASH, 70 + 10 * half)
        play(lead, half * 32, TUNE_H, 98 + 4 * half, 0.8)
        if half:
            play(lead2, 32, TUNE_H, 74, 0.7, -12)
    return list(t.values()), 154, 16


if __name__ == "__main__":
    for name, fn in (("marbledrift_theme", theme), ("marbledrift_hurry", hurry)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
