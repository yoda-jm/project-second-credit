#!/usr/bin/env python3
"""Game 33 (Bloomwand) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any arcade game's music, no existing film, game, nursery or folk theme. A storybook garden band: a flute
tune over a harp waltz, pizzicato strings on the off-beats, a bassoon and arco bass on the downbeats, glockenspiel
glints, a clarinet taking the tune in the second verse, soft strings, and at most a triangle and a shaker.
The tune opens on a rising F major arpeggio (C F A, like the wand lifting) and falls back in a turning figure.
- bloomwand_theme: F major, 3/4 waltz, 160 bpm, 72 bars (81.0 s). Form: intro 8 (harp waltz, strings, glockenspiel and celesta over
  F Bb Gm C7 F Bb Gm7 C7) | A 16 (flute: an 8-bar question ending on C, an 8-bar answer closing on F) | A' 16
  (clarinet takes the tune, the flute weaves a counter-line, strings hold the harmony) | B 16 (D minor: a dancing
  eighth-note flute and oboe line, Dm A7 Dm Dm Gm C7 F A7 Bb C Am Dm Gm C7 F C7) | A'' 16 (tutti, the glockenspiel
  doubling the flute, triangle on the phrase heads) -> back to the top.
- bloomwand_hurry: the same garden in a hurry, F major, 4/4, 152 bpm, 12 bars (18.9 s): the opening arpeggio
  turned into running flute and glockenspiel eighths, bouncing pizzicato bass, harp sixteenths, tremolo strings,
  a shaker; F C7 F C7 | Bb Bbm F D7 | Gm C7 F C7 -> back to the top.
No voices: no choir or voice patches.
Usage: python3 tools/audio/bloomwand_music.py
-> godot/games/bloomwand/audio/music/bloomwand_theme.ogg, bloomwand_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/bloomwand/audio/music/"
TRI, MUTE_TRI, SHAKER, CABASA = 81, 80, 82, 69
GLOCK, CELESTA, HARP, PIZZ, STRINGS, TREMOLO, CONTRABASS, BASSOON, CLARINET, OBOE, FLUTE = (9, 8, 46, 45, 48, 44, 43,
                                                                                         70, 71, 68, 73)
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def mel(text, bar=4):
    """Parses "e5/.75 g5/.5 r/1 | ..." into [(beat, length, pitch)]; '#' sharpens, 'b' flattens (after the letter),
    r is a rest; '|' bar marks are checked against `bar` beats and ignored."""
    out, beat = [], 0.0
    for tok in text.split():
        if tok == "|":
            assert abs(beat % bar) < 1e-6, f"a bar of {beat % bar} beats before '|' in: {text}"
            continue
        p, ln = tok.split("/")
        ln = float(ln)
        if p != "r":
            m = re.fullmatch(r"([a-g])([#b]?)(-?\d)", p)
            out.append((beat, ln, 12 * (int(m.group(3)) + 1) + NOTE[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)]))
        beat += ln
    assert abs(beat % bar) < 1e-6, f"a last bar of {beat % bar} beats in: {text}"
    return out


def note(track, beat, length, pitch, vel):
    track.note(beat, max(0.05, length - 0.02), pitch, max(1, min(127, int(vel))))


def play(track, start, line, vel, legato=0.9, shift=0, accent=6, bar=3):
    for beat, length, pitch in line:
        note(track, start + beat, length * legato, pitch + shift, vel + (accent if beat % bar == 0 else 0))


# chords: (bass note, voicing round middle C)
F, Bb, Gm, C, C7, F7, Dm, A7, Am, Gm7, Bbm, D7 = (
    (41, [57, 60, 65]), (46, [58, 62, 65]), (43, [58, 62, 67]), (48, [55, 60, 64]), (48, [55, 58, 64]),
    (41, [57, 63, 65]), (38, [57, 62, 65]), (45, [55, 61, 64]), (45, [57, 60, 64]), (43, [58, 62, 65]),
    (46, [58, 61, 65]), (38, [57, 60, 66]))
INTRO = [F, Bb, Gm, C7, F, Bb, Gm7, C7]
A_PROG = [F, F, Bb, F, Gm, C7, F, C, F, F7, Bb, Dm, Gm, C7, F, F]
B_PROG = [Dm, A7, Dm, Dm, Gm, C7, F, A7, Bb, C, Am, Dm, Gm, C7, F, C7]
HURRY = [F, C7, F, C7, Bb, Bbm, F, D7, Gm, C7, F, C7]

TUNE_A = mel("c5/1 f5/1 a5/1 | g5/1.5 f5/.5 e5/1 | f5/1 d5/2 | c5/2 a4/1 | "
             "bb4/1 d5/1 g5/1 | bb5/1.5 a5/.5 g5/1 | a5/1 f5/1 c5/1 | g5/2 r/1 | "
             "c5/1 f5/1 a5/1 | c6/1.5 bb5/.5 a5/1 | d6/1.5 c6/.5 bb5/1 | a5/1 g5/1 f5/1 | "
             "g5/1 bb5/1 d6/1 | c6/1.5 bb5/.5 e5/1 | f5/3 | r/3", 3)
COUNTER_A = mel("a5/3 | c6/2 a5/1 | bb5/2 d6/1 | c6/3 | d6/2 bb5/1 | c6/2 bb5/1 | a5/2 c6/1 | g5/3 | "
                "a5/3 | eb6/2 c6/1 | d6/2 f6/1 | f6/2 d6/1 | d6/3 | e6/2 bb5/1 | c6/3 | a5/3", 3)
TUNE_B = mel("a5/.5 g5/.5 f5/.5 e5/.5 d5/1 | c#5/.5 d5/.5 e5/.5 g5/.5 a5/1 | f5/.5 e5/.5 d5/.5 f5/.5 a5/1 | "
             "d6/2 r/1 | bb5/.5 a5/.5 g5/.5 a5/.5 bb5/1 | c6/.5 bb5/.5 g5/.5 e5/.5 c5/1 | "
             "f5/.5 g5/.5 a5/.5 c6/.5 f6/1 | e6/2 c#6/1 | d6/1.5 c6/.5 bb5/1 | c6/1.5 bb5/.5 a5/.5 g5/.5 | "
             "a5/1.5 g5/.5 e5/1 | f5/1 a5/1 d6/1 | d6/1.5 c6/.5 bb5/1 | g5/1 bb5/1 e6/1 | f6/1 c6/1 a5/1 | "
             "bb5/1 g5/1 e5/1", 3)
INTRO_GLOCK = mel("c6/1 f6/1 a6/1 | r/3 | bb5/1 d6/1 g6/1 | e6/3 | c6/1 f6/1 a6/1 | d6/3 | bb5/1 d6/1 g6/1 | "
                  "c6/2 e6/1", 3)
TUNE_H = mel("c5/.5 f5/.5 a5/.5 c6/.5 a5/.5 f5/.5 a5/1 | bb4/.5 e5/.5 g5/.5 bb5/.5 g5/.5 e5/.5 g5/1 | "
             "c5/.5 f5/.5 a5/.5 c6/.5 f6/.5 e6/.5 d6/.5 c6/.5 | bb5/.5 a5/.5 g5/.5 f5/.5 e5/1 c5/1 | "
             "d5/.5 f5/.5 bb5/.5 d6/.5 c6/.5 bb5/.5 a5/.5 bb5/.5 | db6/.5 c6/.5 bb5/.5 f5/.5 db5/1 f5/1 | "
             "c6/.5 a5/.5 f5/.5 a5/.5 c6/1 f6/1 | f#6/.5 e6/.5 d6/.5 c6/.5 a5/1 f#5/1 | "
             "g5/.5 bb5/.5 d6/.5 g6/.5 f6/.5 d6/.5 bb5/1 | c6/.5 e6/.5 g6/.5 bb6/.5 a6/.5 g6/.5 e6/1 | "
             "f6/.5 e6/.5 f6/.5 c6/.5 a5/1 f5/1 | c5/.5 e5/.5 g5/.5 bb5/.5 a5/.5 g5/.5 f5/.5 e5/.5")


def band():
    drums = Track(9, 0, 70, 64, 50)
    return dict(flute=Track(0, FLUTE, 96, 70, 60), clarinet=Track(1, CLARINET, 92, 58, 60),
                oboe=Track(2, OBOE, 80, 80, 60), glock=Track(3, GLOCK, 68, 84, 70), harp=Track(4, HARP, 92, 46, 60),
                pizz=Track(5, PIZZ, 78, 76, 50), strings=Track(6, STRINGS, 62, 52, 80),
                bassoon=Track(7, BASSOON, 84, 60, 40), cbass=Track(8, CONTRABASS, 70, 64, 40),
                trem=Track(10, TREMOLO, 56, 40, 70), celesta=Track(11, CELESTA, 70, 90, 70), dr=drums)


def theme():
    t = band()
    flute, clarinet, oboe, glock, harp, pizz, strings, bassoon, cbass, celesta, dr = (t[k] for k in (
        "flute", "clarinet", "oboe", "glock", "harp", "pizz", "strings", "bassoon", "cbass", "celesta", "dr"))

    def waltz(bar, prog, vel=80, harp_on=True, bass_on=True, pad=0, shaker=False):
        """Bass on 1 (bassoon and arco bass, the fifth on alternate bars), pizzicato chords on 2 and 3, a harp
        arpeggio rippling up and down the chord in eighths, optional sustained strings and a soft shaker."""
        for i, (root, v) in enumerate(prog):
            b = (bar + i) * 3
            low = root if i % 2 == 0 or root + 7 > 50 else root + 7
            if bass_on:
                note(bassoon, b, 1.6, low, vel)
                note(cbass, b, 0.9, low - 12 if low - 12 >= 28 else low, vel - 14)
            for q in (1, 2):
                for p in v:
                    note(pizz, b + q, 0.3, p, vel - 18 - (6 if q == 2 else 0))
            if harp_on:
                seq = [root + 12, v[0], v[1], v[2], v[1] + 12, v[2] + 12][:6]
                if i % 2:
                    seq = [root + 12, v[2], v[1] + 12, v[2] + 12, v[0] + 12, v[1]]
                for k, p in enumerate(seq):
                    note(harp, b + k * 0.5, 0.9, p, vel - 22 + (8 if k == 0 else 0))
            if pad:
                for p in v:
                    note(strings, b, 3, p, pad)
            if shaker:
                for q in (1, 2, 2.5):
                    note(dr, b + q, 0.1, SHAKER, 46 if q % 1 else 56)

    # intro: the harp waltz with strings, glockenspiel and celesta calling the motif
    waltz(0, INTRO[:2], 84, pad=50)
    waltz(2, INTRO[2:], 86, pad=52)
    play(glock, 0, INTRO_GLOCK, 80, 0.9)
    play(celesta, 0, INTRO_GLOCK, 60, 0.9, -12)
    note(dr, 7 * 3 + 2, 0.5, MUTE_TRI, 50)
    bar = 8

    waltz(bar, A_PROG, 82)                       # A: the flute tune
    play(flute, bar * 3, TUNE_A, 92, 0.92)
    note(dr, bar * 3, 1, TRI, 60)
    bar += 16

    waltz(bar, A_PROG, 82, pad=48, shaker=True)  # A': clarinet tune, flute counter-line
    play(clarinet, bar * 3, TUNE_A, 92, 0.95, -12)
    play(flute, bar * 3, COUNTER_A, 74, 0.95)
    note(dr, bar * 3, 1, TRI, 60)
    bar += 16

    waltz(bar, B_PROG, 78, pad=44)               # B: D minor, dancing eighths, oboe a sixth below in places
    play(flute, bar * 3, TUNE_B, 90, 0.8)
    play(oboe, bar * 3, TUNE_B, 62, 0.8, -12)
    for i in (3, 7, 15):                          # celesta glints at the phrase ends
        root, v = B_PROG[i]
        for k, p in enumerate((v[0] + 24, v[1] + 24, v[2] + 24)):
            note(celesta, (bar + i) * 3 + 1 + k * 0.5, 0.5, p, 58)
    bar += 16

    waltz(bar, A_PROG, 86, pad=54, shaker=True)  # A'': tutti, glockenspiel doubling, triangle on phrase heads
    play(flute, bar * 3, TUNE_A, 98, 0.92)
    play(glock, bar * 3, TUNE_A, 56, 0.6, 12)
    play(clarinet, bar * 3, COUNTER_A, 70, 0.95, -12)
    for i in (0, 4, 8, 12):
        note(dr, (bar + i) * 3, 1, TRI, 62)
    bar += 16
    assert bar == 72
    return list(t.values()), 160, bar * 3 / 4


def hurry():
    t = band()
    flute, glock, harp, pizz, trem, bassoon, cbass, dr = (t[k] for k in (
        "flute", "glock", "harp", "pizz", "trem", "bassoon", "cbass", "dr"))
    for i, (root, v) in enumerate(HURRY):
        b = i * 4
        for k in range(8):   # bouncing pizzicato: bass on the beats, chord on the off-beats
            if k % 2 == 0:
                p = (root, root + 7, root + 12, root + 7)[k // 2] if root + 12 < 60 else root
                note(pizz, b + k * 0.5, 0.3, p, 92 if k % 4 == 0 else 82)
            else:
                for p in v:
                    note(pizz, b + k * 0.5, 0.25, p, 66)
        note(bassoon, b, 0.9, root, 86)
        note(bassoon, b + 2, 0.9, root + 7 if root + 7 <= 50 else root - 5, 80)
        note(cbass, b, 1.8, root - 12 if root - 12 >= 28 else root, 70)
        seq = [v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24]
        for k in range(16):   # harp sixteenths, up and down
            p = seq[k % 4] if (k // 4) % 2 == 0 else seq[3 - k % 4]
            note(harp, b + k * 0.25, 0.4, p, 58 + (12 if k % 4 == 0 else 0))
        for p in v:
            note(trem, b, 4, p + 12, 54 + 2 * i)
        for k in range(8):
            note(dr, b + k * 0.5, 0.1, SHAKER, 62 if k % 2 else 50)
        if i % 4 == 0:
            note(dr, b, 1, TRI, 66)
    play(flute, 0, TUNE_H, 96, 0.85, bar=4)
    play(glock, 0, TUNE_H, 52, 0.5, 12, bar=4)
    return list(t.values()), 152, len(HURRY)


if __name__ == "__main__":
    for name, fn in (("bloomwand_theme", theme), ("bloomwand_hurry", hurry)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
