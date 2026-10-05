#!/usr/bin/env python3
"""Game 30 (Ridgefire) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any game's music, and no existing march, film or folk theme. A small military band that does not take
itself too seriously: trumpets and trombones, a tuba oom-pah, horns and clarinets on the after-beats, a piccolo
showing off above, a glockenspiel, snare, bass drum and cymbals.
- ridgefire_theme: B flat major, 120 bpm, 40 bars (80.0 s). Form: intro 4 (a snare roll and a trumpet call on
  repeated notes, B flat B flat E flat F7) | A 8 (the trumpets' march tune over B flat, F7, E flat, C7 F7, dotted
  and bouncy) | A' 8 (tutti, the piccolo's twittering obbligato and the glockenspiel on top) | trio 8 (E flat
  major, softer: clarinets and horns sing a long-breathed tune, light snare) | trio' 8 (tutti, the trombones
  barging in with a staccato counter-melody) | tag 4 (C minor, F7 back to B flat, a snare roll into the top).
- ridgefire_shop: the shop between rounds, F major, 100 bpm, 16 bars (38.4 s), swung: a clarinet with chromatic
  turns over a staccato bassoon walk, vibraphone off-beats, pizzicato strings, a muted trumpet answering, wood
  block and soft kit, a cheeky B flat minor bar and a D7 detour.
No voices: no choir or voice patches.
Usage: python3 tools/audio/ridgefire_music.py
-> godot/games/ridgefire/audio/music/ridgefire_theme.ogg, ridgefire_shop.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/ridgefire/audio/music/"
KICK, BASS_DRUM, SNARE, SIDE, CLOSED, PEDAL, OPEN, CRASH, RIDE, SPLASH, HI_WOOD, LO_WOOD, TAMB = (
    36, 35, 38, 37, 42, 44, 46, 49, 51, 55, 76, 77, 54)
GLOCK, VIBES, PIZZ, STRINGS, TRUMPET, TROMBONE, TUBA, MUTED, HORN, BRASS, CLARINET, PICCOLO, FLUTE, BASSOON = (
    9, 11, 45, 48, 56, 57, 58, 59, 60, 61, 71, 72, 73, 70)
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


def swing(beat, amount):
    """Delays the off-beat eighths by `amount` beats (a lazy swing)."""
    return beat + amount if abs(beat % 1 - 0.5) < 1e-6 else beat


def play(track, start, line, vel, legato=0.9, shift=0, accent=8, sw=0.0):
    for beat, length, pitch in line:
        b = swing(beat, sw)
        note(track, start + b, length * legato - (b - beat), pitch + shift, vel + (accent if beat % 1 == 0 else 0))


# chords: (bass root, the other oom-pah note, voicing round middle C)
Bb, F7, Eb, C7, Cm, Gm, Ab, Bb7, D7, Fm = ((46, 41, [58, 62, 65]), (41, 48, [57, 60, 63]), (39, 46, [58, 63, 67]),
                                         (36, 43, [58, 60, 64]), (36, 43, [55, 60, 63]), (43, 38, [55, 58, 62]),
                                         (44, 39, [56, 60, 63]), (46, 41, [56, 58, 62]), (38, 45, [54, 57, 60]),
                                         (41, 48, [56, 60, 65]))
INTRO = [Bb, Bb, Eb, F7]
A_PROG = [Bb, Bb, F7, Bb, Eb, Bb, (C7, F7), Bb]
TRIO = [Eb, Bb7, Eb, Ab, Eb, Cm, F7, Bb7]
TAG = [Cm, F7, Bb, F7]

CALL = mel("f4/.5 f4/.25 f4/.25 f4/1 bb4/.5 bb4/.25 bb4/.25 bb4/1 | d5/.5 d5/.25 d5/.25 d5/1 f5/2 | "
           "f5/.75 eb5/.25 d5/.75 c5/.25 bb4/1 c5/1 | d5/.5 eb5/.5 e5/.5 f5/.5 r/2")
TUNE_A = mel("f4/.75 f4/.25 bb4/1 d5/1 f5/1 | d5/.75 bb4/.25 d5/.5 f5/.5 bb5/2 | "
             "a5/.75 g5/.25 f5/.5 eb5/.5 c5/1 a4/1 | bb4/.5 c5/.5 d5/.5 eb5/.5 f5/1.5 r/.5 | "
             "g5/.75 f5/.25 eb5/.5 g5/.5 bb5/1 g5/1 | f5/.75 d5/.25 bb4/.5 d5/.5 f5/2 | "
             "e5/.5 f5/.5 g5/.5 c5/.5 f5/.5 g5/.5 a5/.5 c6/.5 | bb5/1 f5/.5 d5/.5 bb4/1 r/1")
PICC_A = mel("d6/.5 f6/.5 bb6/.5 f6/.5 d6/.5 f6/.5 bb6/1 | c6/.25 d6/.25 eb6/.25 d6/.25 bb5/1 f6/.5 d6/.5 bb5/1 | "
             "c6/.5 eb6/.5 a6/.5 eb6/.5 c6/.5 eb6/.5 a6/1 | bb6/.5 a6/.5 g6/.5 f6/.5 d6/1 r/1 | "
             "eb6/.5 g6/.5 bb6/.5 g6/.5 eb6/.5 g6/.5 bb6/1 | d6/.5 f6/.5 bb6/.5 f6/.5 d6/1 bb5/1 | "
             "c6/.5 e6/.5 g6/.5 bb6/.5 a6/.5 f6/.5 c6/.5 eb6/.5 | d6/.5 f6/.5 bb6/1 bb5/1 r/1")
TUNE_T = mel("g4/1.5 ab4/.5 bb4/1 eb5/1 | d5/1.5 c5/.5 bb4/2 | g4/.5 bb4/.5 eb5/1 g5/1.5 f5/.5 | "
             "eb5/1 c5/1 ab4/2 | bb4/1.5 c5/.5 d5/.5 eb5/.5 f5/1 | g5/1.5 f5/.5 eb5/1 c5/1 | "
             "f5/1 a4/1 c5/1 eb5/1 | d5/2 bb4/1 r/1")
BONES_T = mel("eb3/.5 r/.5 g3/.5 r/.5 bb3/1 g3/1 | ab3/.5 r/.5 f3/.5 r/.5 d3/1 f3/1 | "
              "g3/.5 bb3/.5 eb4/.5 bb3/.5 g3/1 eb3/1 | ab3/.5 c4/.5 eb4/.5 c4/.5 ab3/2 | "
              "g3/.5 r/.5 bb3/.5 r/.5 eb4/1 d4/1 | c4/.5 bb3/.5 g3/.5 eb3/.5 c3/2 | "
              "f3/.5 a3/.5 c4/.5 eb4/.5 f4/1 eb4/1 | d4/.5 c4/.5 bb3/.5 ab3/.5 f3/1 d3/1")
TUNE_TAG = mel("c5/1 eb5/1 g5/1 c6/1 | a5/.5 g5/.5 f5/.5 eb5/.5 c5/2 | d5/.5 f5/.5 bb5/1 f5/1 d5/1 | "
               "c5/1 r/1 r/2")


def band():
    return dict(trumpet=Track(0, TRUMPET, 100, 70, 45), trumpet2=Track(1, TRUMPET, 84, 56, 45),
                bones=Track(2, TROMBONE, 96, 52, 40), tuba=Track(3, TUBA, 104, 64, 25),
                horn=Track(4, HORN, 80, 84, 55), clar=Track(5, CLARINET, 84, 76, 50),
                picc=Track(6, PICCOLO, 80, 90, 55), glock=Track(7, GLOCK, 70, 96, 60),
                flute=Track(8, FLUTE, 74, 40, 55), brass=Track(10, BRASS, 70, 64, 45), dr=Track(9, 0, 100, 64, 30))


def theme():
    t = band()
    tr, tr2, bones, tuba, horn, clar, picc, glock, flute, brass, dr = (t[k] for k in (
        "trumpet", "trumpet2", "bones", "tuba", "horn", "clar", "picc", "glock", "flute", "brass", "dr"))

    def bar_chords(b, ch):
        """One bar: a chord, or two (half a bar each)."""
        return [(b, 4, ch)] if isinstance(ch[0], int) else [(b, 2, ch[0]), (b + 2, 2, ch[1])]

    def oompah(b, ch, vel=96, soft=False):
        """Tuba on 1 and 3 (root, then the other note), horns and clarinets on the after-beats 2 and 4."""
        for st, ln, c in bar_chords(b, ch):
            root, other, v = c
            note(tuba, st, 0.8, root, vel)
            if ln == 4:
                note(tuba, st + 2, 0.8, other, vel - 8)
            for q in ((1, 3) if ln == 4 else (1,)):
                for p in v:
                    note(horn, st + q, 0.45, p, vel - (30 if soft else 22))
                    if not soft:
                        note(clar, st + q, 0.35, p + 12, vel - 36)

    def drums(b, vel=90, light=False, fill=False, roll_into=False):
        note(dr, b, 0.3, BASS_DRUM, vel)
        note(dr, b + 2, 0.3, BASS_DRUM, vel - 8)
        if light:
            for q in (1, 3):
                note(dr, b + q, 0.2, SIDE, vel - 22)
            for q in (0.5, 1.5, 2.5, 3.5):
                note(dr, b + q, 0.1, CLOSED, vel - 40)
        else:
            # a march figure: 1 . e & | 2 ... with flams on 2 and 4
            for q, v in ((0, -20), (0.75, -26), (1, 0), (1.5, -18), (2.5, -20), (2.75, -26), (3, 4), (3.5, -16)):
                note(dr, b + q, 0.1, SNARE, vel + v)
            for q in (0.97, 2.97):
                note(dr, b + q, 0.05, SNARE, vel - 34)
        if fill or roll_into:
            for k in range(16 if roll_into else 8):
                q = (0 if roll_into else 2) + k * 0.25
                note(dr, b + q, 0.12, SNARE, vel - 30 + 2 * k)

    def section(start, prog, vel=96, light=False, soft=False):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            oompah(b, ch, vel, soft)
            drums(b, vel - 6, light=light, fill=i == len(prog) - 1)

    # intro: a swelling snare roll under a trumpet call, the band joining on the E flat
    for k in range(32):
        note(dr, k * 0.25, 0.12, SNARE, 40 + k)
    note(dr, 0, 0.5, BASS_DRUM, 80)
    play(tr, 0, CALL, 100, 0.85)
    play(tr2, 0, CALL, 80, 0.85, -12)
    for i, ch in enumerate(INTRO):
        b = i * 4
        if i >= 2:
            oompah(b, ch, 86 + 6 * i)
            for p in ch[2]:
                note(brass, b, 3.5, p, 62 + 6 * i)
        else:
            note(tuba, b, 3.8, ch[0], 80)
    drums(8, 86)
    drums(12, 90, fill=True)
    bar = 4

    section(bar, A_PROG)                       # A: the trumpets' tune
    play(tr, bar * 4, TUNE_A, 100, 0.82)
    play(tr2, bar * 4, TUNE_A, 78, 0.82, -12)
    note(dr, bar * 4, 0.5, CRASH, 90)
    bar += 8

    section(bar, A_PROG, 102)                  # A': tutti, the piccolo twittering on top, glockenspiel
    play(tr, bar * 4, TUNE_A, 104, 0.82)
    play(tr2, bar * 4, TUNE_A, 84, 0.82, -12)
    play(bones, bar * 4, TUNE_A, 72, 0.8, -24)
    play(picc, bar * 4, PICC_A, 84, 0.7)
    play(glock, bar * 4, TUNE_A, 60, 0.5, 12)
    for i in (0, 4):
        note(dr, (bar + i) * 4, 0.5, CRASH, 92)
    bar += 8

    section(bar, TRIO, 86, light=True, soft=True)   # trio: clarinets and horns, softer, a flute above
    play(clar, bar * 4, TUNE_T, 96, 0.95)
    play(horn, bar * 4, TUNE_T, 80, 0.95, -12)
    play(flute, bar * 4, TUNE_T, 56, 0.9, 12)
    note(dr, bar * 4, 0.5, SPLASH, 70)
    bar += 8

    section(bar, TRIO, 100)                    # trio': tutti, trombones barging in with their staccato line
    play(tr, bar * 4, TUNE_T, 100, 0.9)
    play(clar, bar * 4, TUNE_T, 84, 0.9, 12)
    play(horn, bar * 4, TUNE_T, 80, 0.9, -12)
    play(bones, bar * 4, BONES_T, 106, 0.55, 0, 10)
    play(glock, bar * 4, TUNE_T, 54, 0.5, 24)
    for i in (0, 4):
        note(dr, (bar + i) * 4, 0.5, CRASH, 94)
    bar += 8

    for i, ch in enumerate(TAG):               # tag: back to B flat, a roll into the top
        b = (bar + i) * 4
        oompah(b, ch, 100)
        if i < 3:
            drums(b, 94)
        else:
            drums(b, 90, roll_into=True)
        for p in ch[2]:
            note(brass, b, 3.6, p + 12, 72)
    play(tr, bar * 4, TUNE_TAG, 104, 0.85)
    play(tr2, bar * 4, TUNE_TAG, 84, 0.85, -12)
    play(picc, bar * 4, TUNE_TAG, 66, 0.7, 12)
    bar += 4
    assert bar == 40
    return list(t.values()), 120, bar


F, Dm, Gm7, C7s, D7s, Gm_, Bbs, Bbm = ((41, 48, [57, 60, 65]), (38, 45, [57, 62, 65]), (43, 38, [53, 58, 62]),
                                     (36, 43, [52, 58, 60]), (38, 45, [54, 57, 60]), (43, 38, [55, 58, 62]),
                                     (46, 41, [53, 58, 62]), (46, 41, [53, 58, 61]))
SHOP = [F, Dm, Gm7, C7s, F, D7s, Gm_, C7s, Bbs, Bbm, F, D7s, Gm7, C7s, F, C7s]
TUNE_S = mel("c5/.5 a4/.5 f4/.5 a4/.5 c5/1 r/1 | d5/.5 c#5/.5 d5/.5 f5/.5 a5/1 r/1 | "
             "bb5/.5 a5/.5 g5/.5 f5/.5 e5/.5 f5/.5 g5/1 | e5/1.5 c5/.5 bb4/1 r/1 | "
             "a4/.5 c5/.5 f5/.5 a5/.5 g#5/.5 a5/.5 c6/1 | f#5/.75 a5/.25 d6/1 c6/.5 a5/.5 f#5/1 | "
             "g5/.5 bb5/.5 d6/.5 bb5/.5 a5/.5 g5/.5 f5/1 | e5/.5 f5/.5 g5/.5 bb5/.5 c6/1 r/1 | "
             "d6/1 c6/.5 bb5/.5 f5/1 d5/1 | db6/1 c6/.5 bb5/.5 f5/1 db5/1 | "
             "c5/.5 f5/.5 a5/.5 c6/.5 a5/1 f5/1 | f#5/.5 a5/.5 c6/.5 eb6/.5 d6/1 a5/1 | "
             "bb5/.5 a5/.5 g5/.5 f5/.5 d5/1 f5/1 | e5/.5 g5/.5 bb5/.5 c6/.5 d6/.5 c6/.5 bb5/1 | "
             "a5/1.5 g5/.25 f5/.25 c5/1 a4/1 | bb4/.5 c5/.5 d5/.5 e5/.5 g5/.5 e5/.5 c5/1")
# the muted trumpet answers in the rests of the tune
ANSWER = mel("r/3 a5/.25 bb5/.25 c6/.5 | r/3 f5/.5 a5/.5 | r/4 | r/3 g5/.5 bb5/.5 | r/4 | r/4 | r/4 | "
             "r/3 e6/.5 c6/.5 | r/4 | r/4 | r/4 | r/4 | r/4 | r/4 | r/4 | r/4")


def shop():
    clar = Track(0, CLARINET, 96, 70, 45)
    bassoon = Track(1, BASSOON, 100, 56, 30)
    vibes = Track(2, VIBES, 74, 84, 55)
    pizz = Track(3, PIZZ, 70, 44, 45)
    muted = Track(4, MUTED, 80, 90, 50)
    glock = Track(5, GLOCK, 52, 100, 60)
    dr = Track(9, 0, 82, 64, 30)
    SW = 0.08
    for i, ch in enumerate(SHOP):
        b = i * 4
        root, other, v = ch
        nxt = SHOP[(i + 1) % len(SHOP)][0]
        walk = (root, other if other > root else other + 12, root + 12, nxt + (1 if nxt < root + 6 else -1))
        for q, p in enumerate(walk):            # a staccato bassoon walk, a chromatic step into the next bar
            note(bassoon, b + q, 0.45, p, 92 if q % 2 == 0 else 80)
        for q in (0.5, 1.5, 2.5, 3.5):         # vibraphone off-beats
            for p in v:
                note(vibes, b + swing(q, SW), 0.3, p + 12, 58 if q in (1.5, 3.5) else 50)
        seq = [v[0], v[1], v[2], v[1]]
        for k in range(4):
            note(pizz, b + k, 0.3, seq[k] + 12, 56)
        note(dr, b, 0.2, KICK, 64)
        note(dr, b + 2, 0.2, KICK, 56)
        for q in (1, 3):
            note(dr, b + q, 0.2, SIDE, 58)
        for q in (0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5):
            note(dr, b + swing(q, SW), 0.1, PEDAL if q % 1 else CLOSED, 40 + (6 if q % 1 == 0 else 0))
        if i % 4 == 3:
            for q, w in ((2.5, HI_WOOD), (3, LO_WOOD), (3.5, HI_WOOD)):
                note(dr, b + swing(q, SW), 0.15, w, 70)
        if i in (7, 15):
            note(dr, b + 3.5 + SW, 0.2, SPLASH, 50)
    play(clar, 0, TUNE_S, 92, 0.75, 0, 8, SW)
    play(glock, 0, [x for x in TUNE_S if x[0] >= 32], 40, 0.4, 12, 4, SW)   # bars 9-16 sparkle
    play(muted, 0, ANSWER, 82, 0.6, 0, 6, SW)
    return [clar, bassoon, vibes, pizz, muted, glock, dr], 100, len(SHOP)


if __name__ == "__main__":
    for name, fn in (("ridgefire_theme", theme), ("ridgefire_shop", shop)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-18.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
