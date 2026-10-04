#!/usr/bin/env python3
"""Game 28 (Fuseflight) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any arcade game's music, no existing film, game or folk theme. A bright, bouncy night-festival band: a
piccolo and flute tune doubled by glockenspiel, oom-pah tuba and pizzicato, marimba off-beats, brass punches,
steel drums in the middle section and a kit with tambourine. The tune leaps up an arpeggio and skips back down in
dotted steps, like the sprite bounding from ledge to ledge.
- fuseflight_theme: D major, 136 bpm, 44 bars (77.6 s). Form: intro 4 (glockenspiel sparkles over D G A A7, the band
  falls in) | A 8 (piccolo over D G A D D G Em A) | A' 8 (flute and piccolo, a string counter-line, brass punches) |
  B 8 (the lift: G A F#m Bm G A D D, the tune soaring an octave up) | C 8 (steel drums over Bm G D A Bm G Em A7,
  lighter kit) | A'' 8 (tutti, the glockenspiel doubling the tune) -> back to the top.
- fuseflight_power: the power time, A major, 160 bpm, 10 bars (15.0 s): galloping bass, xylophone sixteenths, brass
  stabs and a racing piccolo over A D E A F#m D B E, then D E rising back into the top.
No voices: no choir or voice patches.
Usage: python3 tools/audio/fuseflight_music.py
-> godot/games/fuseflight/audio/music/fuseflight_theme.ogg, fuseflight_power.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/fuseflight/audio/music/"
KICK, SNARE, SIDE, CLOSED, OPEN, CRASH, RIDE, LO_TOM, MID_TOM, HI_TOM, TAMB, CLAP = (36, 38, 37, 42, 46, 49, 51, 45,
                                                                                      47, 50, 54, 39)
GLOCK, MARIMBA, XYLO, ABASS, PIZZ, STRINGS, TRUMPET, TUBA, BRASS, PICCOLO, FLUTE, STEEL = (9, 12, 13, 32, 45, 48, 56,
                                                                                         58, 61, 72, 73, 114)
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


# chords: (bass root, fifth below/above for the oom-pah, voicing round middle C)
D, G, A, Bm, Em, Fsm, A7, E, B = ((38, 45, [57, 62, 66]), (43, 38, [55, 59, 62]), (45, 40, [57, 61, 64]),
                                  (47, 42, [54, 59, 62]), (40, 47, [55, 59, 64]), (42, 49, [54, 57, 61]),
                                  (45, 40, [55, 61, 64]), (40, 47, [56, 59, 64]), (47, 42, [54, 59, 63]))
INTRO = [D, G, A, A7]
A_PROG = [D, G, A, D, D, G, Em, A]
B_PROG = [G, A, Fsm, Bm, G, A, D, D]
C_PROG = [Bm, G, D, A, Bm, G, Em, A7]
POWER = [A, D, E, A, Fsm, D, B, E, D, E]

TUNE_A = mel("a4/.5 d5/.5 f#5/.5 a5/.5 f#5/.75 e5/.25 d5/1 | b5/.75 a5/.25 g5/.5 b5/.5 d6/1 b5/1 | "
             "c#6/.5 a5/.5 e5/.5 a5/.5 g5/.75 f#5/.25 e5/1 | f#5/.5 a5/.5 d6/1.5 r/1.5 | "
             "a4/.5 d5/.5 f#5/.5 a5/.5 d6/.75 c#6/.25 b5/.5 a5/.5 | g5/.5 b5/.5 d6/.5 g6/.5 f#6/.75 e6/.25 d6/1 | "
             "e5/.5 g5/.5 b5/.5 e6/.5 d6/.5 c#6/.5 b5/.5 a5/.5 | c#6/.75 b5/.25 a5/.5 g5/.5 e5/1 r/1")
COUNTER_A = mel("f#5/2 a5/2 | g5/2 b5/2 | e5/2 a5/2 | f#5/4 | f#5/2 a5/2 | b5/2 d6/2 | b5/2 g5/2 | c#6/2 e5/2")
TUNE_B = mel("d6/1 b5/.5 d6/.5 g6/1.5 f#6/.5 | e6/1 c#6/.5 e6/.5 a6/2 | f#6/.75 e6/.25 c#6/.5 a5/.5 f#5/1 a5/1 | "
             "b5/.5 c#6/.5 d6/.5 f#6/.5 b6/2 | g6/.75 f#6/.25 e6/.5 d6/.5 b5/1 d6/1 | "
             "c#6/.5 d6/.5 e6/.5 a6/.5 g6/1 e6/1 | f#6/1 a6/1 d7/1.5 a6/.5 | f#6/.5 e6/.5 d6/1 r/2")
TUNE_C = mel("f#5/.5 b5/.5 d6/.5 b5/.5 f#5/1 d5/1 | g5/.5 b5/.5 d6/1 e6/.5 d6/.5 b5/1 | "
             "a5/.5 f#5/.5 a5/.5 d6/.5 f#6/1.5 r/.5 | e6/.75 d6/.25 c#6/.5 b5/.5 a5/2 | "
             "d6/.5 c#6/.5 b5/.5 f#5/.5 b5/1 d6/1 | e6/.5 d6/.5 b5/.5 g5/.5 d6/1 b5/1 | "
             "g5/.5 b5/.5 e6/.5 g6/.5 f#6/.5 e6/.5 d6/.5 b5/.5 | c#6/1 e6/1 g6/1 a6/1")
TUNE_P = mel("e6/.25 c#6/.25 a5/.25 c#6/.25 e6/.5 a6/.5 g#6/.5 e6/.5 c#6/1 | "
             "f#6/.25 d6/.25 a5/.25 d6/.25 f#6/.5 a6/.5 f#6/.5 d6/.5 a5/1 | "
             "g#5/.5 b5/.5 e6/.5 g#6/.5 b6/.75 a6/.25 g#6/1 | a6/.5 e6/.5 c#6/.5 e6/.5 a6/2 | "
             "a5/.5 c#6/.5 f#6/.5 a6/.5 g#6/.5 f#6/.5 e6/.5 c#6/.5 | d6/.5 f#6/.5 a6/1 f#6/.5 d6/.5 a5/1 | "
             "b5/.5 d#6/.5 f#6/.5 b6/.5 a6/.5 f#6/.5 d#6/1 | e6/.5 g#6/.5 b6/1 b6/.5 a6/.5 g#6/1 | "
             "f#6/.25 a6/.25 d7/.5 f#6/.25 a6/.25 d7/.5 a6/.5 f#6/.5 d6/1 | "
             "e6/.25 g#6/.25 b6/.5 e6/.25 g#6/.25 b6/.5 d7/.5 c#7/.5 b6/1")


def band():
    drums = Track(9, 0, 100, 64, 30)
    return dict(lead=Track(0, PICCOLO, 92, 70, 50), flute=Track(1, FLUTE, 84, 56, 55),
                glock=Track(2, GLOCK, 74, 80, 60), tuba=Track(3, TUBA, 100, 64, 25),
                pizz=Track(4, PIZZ, 78, 44, 45), marimba=Track(5, MARIMBA, 80, 84, 40),
                strings=Track(6, STRINGS, 66, 40, 80), brass=Track(7, BRASS, 82, 76, 45),
                trumpet=Track(8, TRUMPET, 80, 60, 45), steel=Track(10, STEEL, 88, 72, 55),
                xylo=Track(11, XYLO, 76, 90, 40), bass=Track(12, ABASS, 96, 64, 20), dr=drums)


def parts(t):
    tuba, pizz, marimba, dr, bass = t["tuba"], t["pizz"], t["marimba"], t["dr"], t["bass"]

    def oompah(b, ch, vel=96):
        """Tuba on the beats (root, fifth), a bass pizzicato doubling, marimba chords skipping on the off-beats."""
        root, fifth, v = ch
        for q, p in ((0, root), (2, fifth)):
            note(tuba, b + q, 0.9, p, vel)
            note(bass, b + q, 0.6, p, vel - 10)
        note(tuba, b + 3.5, 0.4, root + (2 if fifth > root else -1), vel - 24)   # a little pickup
        for q in (0.5, 1, 1.5, 2.5, 3, 3.5):
            for p in v:
                note(marimba, b + q, 0.3, p + 12, vel - (32 if q % 1 else 22))

    def arp(b, ch, vel=58):
        """Pizzicato eighths up and down the chord."""
        _, _, v = ch
        seq = [v[0], v[1], v[2], v[1] + 12, v[2] + 12, v[1] + 12, v[2], v[1]]
        for k in range(8):
            note(pizz, b + k * 0.5, 0.3, seq[k], vel + (10 if k % 2 == 0 else 0))

    def kit(b, vel=86, light=False, fill=False, gallop=False):
        for q in (0, 2):
            note(dr, b + q, 0.2, KICK, vel + 4)
        if gallop:
            note(dr, b + 2.75, 0.2, KICK, vel - 10)
            note(dr, b + 0.75, 0.2, KICK, vel - 14)
        for q in (1, 3):
            note(dr, b + q, 0.2, SIDE if light else SNARE, vel - (14 if light else 4))
            note(dr, b + q + 0.5, 0.2, TAMB, vel - 30)
        step = 0.25 if gallop else 0.5
        for k in range(int(4 / step)):
            st = k * step
            note(dr, b + st, 0.1, RIDE if light else CLOSED, vel - 34 + (8 if st % 1 == 0 else 0))
        if fill:
            for k, dd in enumerate((SNARE, SNARE, HI_TOM, HI_TOM, MID_TOM, MID_TOM, LO_TOM, LO_TOM)):
                note(dr, b + 2 + k * 0.25, 0.2, dd, vel - 18 + 3 * k)

    return oompah, arp, kit


def theme():
    t = band()
    lead, flute, glock, strings, brass, trumpet, steel, dr = (t[k] for k in (
        "lead", "flute", "glock", "strings", "brass", "trumpet", "steel", "dr"))
    oompah, arp, kit = parts(t)

    def section(start, prog, vel=96, light=False, pizz=True):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            oompah(b, ch, vel)
            if pizz:
                arp(b, ch, vel - 40)
            kit(b, vel - 10, light=light, fill=i == len(prog) - 1)

    def punches(start, prog, vel=74):
        """Brass on the 'and' of 2 and on 4, every bar."""
        for i, ch in enumerate(prog):
            for q, ln in ((1.5, 0.35), (3, 0.6)):
                for p in ch[2]:
                    note(brass, (start + i) * 4 + q, ln, p + 12, vel)

    # intro: glockenspiel sparkles over the chords, the tuba from bar 2, the kit from bar 3, a fill into A
    for i, ch in enumerate(INTRO):
        b = i * 4
        _, _, v = ch
        for k, p in enumerate([v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24, v[2] + 12, v[1] + 24, v[2] + 24, v[0] + 24]):
            note(glock, b + k * 0.5, 0.4, p, 60 + 4 * i)
        for p in v:
            note(strings, b, 4, p, 50 + 5 * i)
        if i >= 1:
            oompah(b, ch, 80 + 5 * i)
        if i >= 2:
            kit(b, 74 + 4 * i, light=i == 2, fill=i == 3)
    bar = 4

    section(bar, A_PROG)                       # A: the piccolo tune
    play(t["lead"], bar * 4, TUNE_A, 98, 0.85)
    note(dr, bar * 4, 0.5, CRASH, 84)
    bar += 8

    section(bar, A_PROG, 98)                   # A': flute and piccolo, strings counter-line, brass punches
    play(lead, bar * 4, TUNE_A, 96, 0.85)
    play(flute, bar * 4, TUNE_A, 80, 0.8, -12)
    play(strings, bar * 4, COUNTER_A, 70, 1.0)
    punches(bar, A_PROG, 66)
    note(dr, bar * 4, 0.5, CRASH, 86)
    bar += 8

    section(bar, B_PROG, 102)                  # B: the lift, the tune an octave up, trumpet answering low
    play(lead, bar * 4, TUNE_B, 100, 0.88)
    play(flute, bar * 4, TUNE_B, 78, 0.85, -12)
    play(trumpet, bar * 4, TUNE_B, 70, 0.8, -24)
    punches(bar, B_PROG, 72)
    for i, ch in enumerate(B_PROG):
        for p in ch[2]:
            note(strings, (bar + i) * 4, 4, p + 12, 56)
    note(dr, bar * 4, 0.5, CRASH, 90)
    bar += 8

    section(bar, C_PROG, 92, light=True)       # C: steel drums, a lighter kit on the ride
    play(steel, bar * 4, TUNE_C, 100, 0.8)
    play(glock, bar * 4, TUNE_C, 46, 0.5, 12)
    for i, ch in enumerate(C_PROG):
        for p in ch[2]:
            note(strings, (bar + i) * 4, 4, p, 52)
    note(dr, bar * 4, 0.5, CRASH, 80)
    bar += 8

    section(bar, A_PROG, 104)                  # A'': tutti, the glockenspiel doubling the tune
    play(lead, bar * 4, TUNE_A, 104, 0.85)
    play(flute, bar * 4, TUNE_A, 84, 0.8, -12)
    play(glock, bar * 4, TUNE_A, 62, 0.6, 12)
    play(strings, bar * 4, COUNTER_A, 74, 1.0)
    play(trumpet, bar * 4, COUNTER_A, 62, 0.9, -12)
    punches(bar, A_PROG, 76)
    note(dr, bar * 4, 0.5, CRASH, 94)
    bar += 8
    assert bar == 44
    return list(t.values()), 136, bar


def power():
    t = band()
    lead, xylo, brass, strings, tuba, bass, dr = (t[k] for k in ("lead", "xylo", "brass", "strings", "tuba", "bass",
                                                                  "dr"))
    _, arp, kit = parts(t)
    for i, ch in enumerate(POWER):
        b = i * 4
        root, fifth, v = ch
        for k in range(8):   # galloping bass eighths: root, root, octave, fifth
            p = (root, root, root + 12, fifth)[k % 4]
            note(bass, b + k * 0.5, 0.35, p, 104 - (0 if k % 2 == 0 else 12))
        note(tuba, b, 1.8, root, 90)
        note(tuba, b + 2, 1.8, fifth, 84)
        seq = [v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24]
        for k in range(16):   # xylophone sixteenths
            note(xylo, b + k * 0.25, 0.2, seq[k % 4] + (12 if (k // 4) % 2 else 0), 60 + (14 if k % 4 == 0 else 0))
        for q, ln in ((0, 0.3), (0.75, 0.3), (1.5, 0.4), (3, 0.3), (3.5, 0.4)):   # brass stabs
            for p in v:
                note(brass, b + q, ln, p + 12, 78 if q in (0, 1.5) else 66)
        for p in v:
            note(strings, b, 4, p + 12, 58 + 2 * i)
        kit(b, 92, fill=i in (7, 9), gallop=True)
        if i % 4 == 0 or i == 8:
            note(dr, b, 0.5, CRASH, 88)
    play(lead, 0, TUNE_P, 100, 0.85)
    return list(t.values()), 160, len(POWER)


if __name__ == "__main__":
    for name, fn in (("fuseflight_theme", theme), ("fuseflight_power", power)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
