#!/usr/bin/env python3
"""Game 17 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own:
a small wintry toy orchestra for an otter on the ice under the aurora. No quotations: nothing from the arcade
game's music nor from the classical and folk pieces such games used, no carols.
- slipfloe_theme: upbeat and playful, G major, 132 bpm, straight eighths. Xylophone and then flute tunes over a
  light synth bass (root and octave bounce), pizzicato off-beat chords, a marimba arpeggio carpet, celesta and
  glockenspiel glints, sleigh bells, brushes. Form: intro 4 | A 8 (xylophone) | A' 8 (flute, celesta
  countermelody, strings) | B 8 (celesta and flute in C and E colours, harp) | A'' 8 (tutti) | turn 4 (73 s).
- slipfloe_hurry: the same band when one mite is left, 168 bpm, up a tone to A major: the A tune on xylophone
  and flute, an eighth-note chase in the relative minor on xylophone over a driving bass, the tune again with
  sleigh bells on every beat. 24 bars (34 s).
Usage: python3 tools/audio/slipfloe_music.py
-> godot/games/slipfloe/audio/music/slipfloe_theme.ogg and slipfloe_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/slipfloe/audio/music/"
BRUSH_KIT = 40  # the brush kit on the drum channel
KICK, TAP, SLAP, SWIRL, PEDAL, CLOSED, RIDE, CRASH, TRI, TRI_MUTE, JINGLE, TAMB = \
    36, 38, 39, 40, 44, 42, 51, 49, 81, 80, 83, 54
CELESTA, GLOCK, MUSICBOX, MARIMBA, XYLO, SYNTHBASS, PIZZ, FLUTE, STRINGS, HARP, PICCOLO = \
    8, 9, 10, 12, 13, 38, 45, 73, 48, 46, 72
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

# chords as (bass root, voicing around middle C)
G, Em, C, D, Am, D7, Bm, E7, Cmaj7, A7 = ((43, [59, 62, 67]), (40, [59, 64, 67]), (36, [60, 64, 67]),
                                          (38, [57, 62, 66]), (45, [57, 60, 64]), (38, [57, 60, 66]),
                                          (47, [59, 62, 66]), (40, [56, 62, 64]), (36, [59, 64, 67]),
                                          (45, [57, 61, 67]))
A_PROG = [[G], [Em], [C], [D], [G], [Em], [Am, D7], [G]]
B_PROG = [[C], [D], [Bm], [Em], [Am], [D], [E7], [D7]]
TURN = [[Am], [D7], [Em, C], [D7]]
CHASE = [[Em], [C], [G], [D], [Em], [C], [Am], [D7]]


def mel(text):
    """Parses a line like "d5/.5 g5/1 r/.5" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens
    (after the letter), r is a rest; '|' bar marks are checked and ignored."""
    out, beat = [], 0.0
    for tok in text.split():
        if tok == "|":
            assert beat % 4 == 0, f"a bar of {beat % 4} beats before '|' in: {text}"
            continue
        p, ln = tok.split("/")
        ln = float(ln)
        if p != "r":
            m = re.fullmatch(r"([a-g])([#b]?)(-?\d)", p)
            out.append((beat, ln, 12 * (int(m.group(3)) + 1) + NOTE[m.group(1)] + {"#": 1, "b": -1, "": 0}[m.group(2)]))
        beat += ln
    assert beat % 4 == 0, f"a last bar of {beat % 4} beats in: {text}"
    return out


TUNE_A = mel("d5/.5 g5/.5 b5/.5 g5/.5 a5/.25 b5/.25 a5/.5 g5/1 | e5/.5 g5/.5 b5/1 e6/.75 d6/.25 b5/1 | "
             "c6/.5 b5/.5 a5/.5 g5/.5 e5/.5 g5/.5 c6/1 | b5/.5 a5/.5 f#5/.5 d5/.5 a5/1.5 r/.5 | "
             "d5/.5 g5/.5 b5/.5 d6/.5 g6/.75 f#6/.25 d6/1 | e6/.5 d6/.5 b5/.5 g5/.5 e5/1 g5/1 | "
             "a5/.5 c6/.5 e6/.5 c6/.5 d6/.5 c6/.5 a5/.5 f#5/.5 | g5/1.5 d5/.5 g4/1 r/1")
TUNE_B = mel("e6/1.5 d6/.5 c6/1 g5/1 | f#5/1.5 a5/.5 d6/2 | d6/.5 c#6/.5 b5/1 f#5/1 d5/1 | g5/1.5 f#5/.5 e5/2 | "
             "c6/1 e6/1 a6/1.5 g6/.5 | f#6/1 d6/1 a5/2 | g#5/.5 b5/.5 d6/.5 e6/.5 g#6/1 e6/1 | "
             "f#6/.5 e6/.5 d6/.5 c6/.5 a5/.5 f#5/.5 d5/1")
COUNTER = mel("b5/2 d6/2 | g6/2 e6/2 | e6/2 g6/1 e6/1 | f#6/2 d6/2 | b5/2 d6/1 g6/1 | g6/2 b5/2 | "
              "c6/2 a5/1 c6/1 | b5/2 r/2")
TURN_TUNE = mel("e6/.25 d6/.25 c6/.5 a5/1 r/2 | f#5/.25 g5/.25 a5/.5 d6/1 r/2 | "
                "g5/.5 b5/.5 e6/.5 d6/.5 c6/.5 e6/.5 g6/1 | f#6/.5 e6/.5 d6/.5 c6/.5 a5/.5 f#5/.5 d5/1")


def split(bar):
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def play(track, start, line, vel, legato=0.85, shift=0, accent=6, only=None):
    for beat, length, pitch in line:
        if only and not only(beat):
            continue
        v = vel + (accent if beat % 1 == 0 else 0)
        track.note(start + beat, max(0.05, length * legato), pitch + shift, max(1, min(127, int(v))))


def band(drum_vol=96):
    dr = Track(9, 0, drum_vol, 64, 40)
    dr.events.append((0, bytes([0xC9, BRUSH_KIT])))
    return dict(xyl=Track(0, XYLO, 100, 44, 45), flu=Track(1, FLUTE, 92, 80, 55), cel=Track(2, CELESTA, 88, 88, 60),
                glk=Track(3, GLOCK, 62, 96, 55), mar=Track(4, MARIMBA, 84, 36, 45), bass=Track(5, SYNTHBASS, 92, 64, 20),
                pz=Track(6, PIZZ, 100, 70, 40), strg=Track(7, STRINGS, 50, 58, 70), hrp=Track(8, HARP, 72, 30, 60),
                box=Track(10, MUSICBOX, 70, 100, 60), dr=dr)


def parts(b_, shift):
    xyl, mar, bass, pz, dr, glk = b_["xyl"], b_["mar"], b_["bass"], b_["pz"], b_["dr"], b_["glk"]

    def bassline(b, bar, vel=92, drive=False):
        """Light synth bass: the root on the beat, the octave bouncing on the 'and', the fifth on beat 3."""
        for off, ln, (root, _) in split(bar):
            r = root - 12 + shift
            for k in range(int(ln)):
                q = b + off + k
                bass.note(q, 0.4, r + (7 if k == 2 else 0), vel if k % 2 == 0 else vel - 10)
                if drive or k % 2 == 1:
                    bass.note(q + 0.5, 0.25, r + 12, vel - 18)

    def offbeats(b, bar, vel=78):
        """Pizzicato chords on the off-beats, short and springy."""
        for off, ln, (_, v) in split(bar):
            for k in range(int(ln)):
                for p in v:
                    pz.note(b + off + k + 0.5, 0.25, p + shift, vel - (8 if k % 2 else 0))

    def carpet(b, bar, vel=62):
        """The marimba: chord tones in eighths, up and back, an octave above the voicing."""
        for off, ln, (_, v) in split(bar):
            notes = [v[0] + 12, v[1] + 12, v[2] + 12, v[1] + 12]
            for k in range(int(ln * 2)):
                mar.note(b + off + k * 0.5, 0.4, notes[k % 4] + shift, vel + (10 if k % 2 == 0 else 0))

    def brushes(b, full=True, fill=False, jingle=2):
        """Brushes: swirl through the bar, taps on 2 and 4, a kick on 1 and 3; sleigh bells on the beats
        (jingle=2: on 2 and 4, jingle=4: every beat)."""
        dr.note(b, 3.9, SWIRL, 46)
        dr.note(b, 0.2, KICK, 70)
        dr.note(b + 2, 0.2, KICK, 58)
        if full:
            dr.note(b + 1, 0.2, SLAP, 64)
            dr.note(b + 3, 0.2, SLAP, 70)
            for k in range(8):
                dr.note(b + k / 2, 0.05, PEDAL if k % 2 else CLOSED, 30 if k % 2 else 40)
        for q in range(4):
            if jingle == 4 or q % 2 == 1:
                dr.note(b + q, 0.2, JINGLE, 88 if q % 2 else 72)
        if fill:
            for i in range(6):
                dr.note(b + 3 + i / 6, 0.1, TAP, 46 + 9 * i)

    return bassline, offbeats, carpet, brushes


# ---------------------------------------------------------------------------------------------------------------
def theme():
    b_ = band()
    xyl, flu, cel, glk, mar, bass, pz, strg, hrp, box, dr = (b_[k] for k in
                                                             ("xyl", "flu", "cel", "glk", "mar", "bass", "pz",
                                                              "strg", "hrp", "box", "dr"))
    bassline, offbeats, carpet, brushes = parts(b_, 0)
    bar = 0
    for i, ch in enumerate([[G], [C], [G], [D7]]):  # intro: marimba alone, sleigh bells, the bass, a celesta run
        b = bar * 4
        carpet(b, ch, 54 + 4 * i)
        dr.note(b, 1, TRI, 44)
        if i >= 1:
            for q in range(4):
                dr.note(b + q, 0.2, JINGLE, 66 + 10 * (q % 2))
        if i >= 2:
            bassline(b, ch, 84)
            offbeats(b, ch, 66)
        bar += 1
    play(cel, 8, mel("g6/.5 d6/.5 b5/.5 d6/.5 g6/2"), 52, 0.9)
    play(cel, 12, mel("f#6/.25 e6/.25 d6/.25 c6/.25 a5/.5 f#5/.5 d5/1 r/1"), 58, 0.9)
    dr.note(15, 1, CRASH, 34)

    def section_a(start, lead, lead_vel, counter, tutti):
        for i, ch in enumerate(A_PROG):
            b = (start + i) * 4
            bassline(b, ch)
            offbeats(b, ch)
            carpet(b, ch, 66 if tutti else 60)
            brushes(b, fill=i == 7, jingle=4 if tutti else 2)
            if counter:
                for p in ch[0][1]:
                    strg.note(b, 3.9, p, 44)
        play(lead, start * 4, TUNE_A, lead_vel, 0.8 if lead is xyl else 0.92)
        play(glk, start * 4, TUNE_A, 50, 0.7, 12, only=lambda q: q % 2 == 0)
        if counter:
            play(cel, start * 4, COUNTER, 62, 0.9)
        if tutti:
            play(xyl, start * 4, TUNE_A, 76, 0.8, -12)
            play(box, start * 4, COUNTER, 58, 0.9, 12)

    section_a(bar, xyl, 96, False, False)
    bar += 8
    section_a(bar, flu, 92, True, False)
    bar += 8
    for i, ch in enumerate(B_PROG):  # B: celesta and flute sing longer notes, harp rolls, strings, lighter beat
        b = (bar + i) * 4
        bassline(b, ch, 84)
        for off, ln, (root, v) in split(ch):
            for k, p in enumerate([root + 12] + v + [v[0] + 12]):
                hrp.note(b + off + k * 0.12, 1.8, p, 56)
            for p in v:
                strg.note(b + off, ln - 0.05, p, 50)
            for k in range(int(ln)):
                pz.note(b + off + k + 0.5, 0.25, v[k % 3] + 12, 62)
        brushes(b, full=i % 2 == 0, fill=i == 7)
        dr.note(b, 1, TRI, 40)
    play(cel, bar * 4, TUNE_B, 86, 0.95)
    play(flu, bar * 4, TUNE_B, 72, 0.95, -12)
    play(mar, bar * 4 + 28, mel("d4/.5 e4/.5 f#4/.5 g4/.5 a4/.5 b4/.5 c5/.5 c#5/.5"), 74, 0.9)
    bar += 8
    section_a(bar, flu, 98, True, True)
    bar += 8
    for i, ch in enumerate(TURN):  # the turn: xylophone twirls, the marimba climbs back to the intro
        b = (bar + i) * 4
        bassline(b, ch, 86)
        offbeats(b, ch, 70)
        brushes(b, full=i < 2, fill=i == 3)
    play(xyl, bar * 4, TURN_TUNE, 90, 0.8)
    play(glk, bar * 4, TURN_TUNE, 44, 0.7, 12, only=lambda q: q % 1 == 0)
    play(mar, bar * 4 + 12, mel("d4/.5 e4/.5 f#4/.5 g4/.5 a4/.5 b4/.5 c5/.5 c#5/.5"), 78, 0.9)
    bar += 4
    assert bar == 40
    return list(b_.values()), 132, bar


# ---------------------------------------------------------------------------------------------------------------
def hurry():
    """One mite left: faster, up a tone, the bass driving in eighths, sleigh bells on every beat."""
    b_ = band(100)
    xyl, flu, cel, glk, mar, pz, strg, dr = (b_[k] for k in ("xyl", "flu", "cel", "glk", "mar", "pz", "strg", "dr"))
    SH = 2
    bassline, offbeats, carpet, brushes = parts(b_, SH)
    bar = 0
    for i, ch in enumerate(A_PROG):  # A: the tune on xylophone with a flute an octave down
        b = (bar + i) * 4
        bassline(b, ch, 94, drive=True)
        offbeats(b, ch, 76)
        carpet(b, ch, 60)
        brushes(b, fill=i == 7, jingle=4)
    play(xyl, 0, TUNE_A, 98, 0.8, SH)
    play(flu, 0, TUNE_A, 66, 0.9, SH - 12)
    bar += 8
    for i, ch in enumerate(CHASE):  # the chase: eighth notes zig-zagging through the chord, strings pulsing
        b = (bar + i) * 4
        bassline(b, ch, 96, drive=True)
        brushes(b, fill=i in (3, 7), jingle=4)
        for off, ln, (root, v) in split(ch):
            tones = [v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24, v[2] + 12, v[1] + 12, v[0] + 12, v[1] + 12]
            if i % 2:
                tones = tones[3:] + tones[:3]
            for k in range(int(ln * 2)):
                xyl.note(b + off + k * 0.5, 0.35, tones[k % 8] + SH, 82 + (12 if k % 2 == 0 else 0))
            for k in range(int(ln * 2)):
                for p in v:
                    strg.note(b + off + k * 0.5, 0.4, p + SH, 40 + (10 if k % 2 == 0 else 0))
        glk.note(b, 1, split(ch)[0][2][1][2] + 24 + SH, 52)
    play(flu, bar * 4, mel("b5/2 g5/2 | e6/2 c6/2 | d6/2 b5/2 | a5/4 | b5/2 g5/2 | e6/2 g6/2 | "
                           "e6/1 c6/1 a5/1 c6/1 | d6/1 f#6/1 a6/2"), 80, 0.95, SH)
    bar += 8
    for i, ch in enumerate(A_PROG):  # A again, flute on top now, celesta glints, the xylophone an octave down
        b = (bar + i) * 4
        bassline(b, ch, 96, drive=True)
        offbeats(b, ch, 78)
        carpet(b, ch, 64)
        brushes(b, fill=i == 7, jingle=4)
    play(flu, bar * 4, TUNE_A, 96, 0.9, SH)
    play(xyl, bar * 4, TUNE_A, 78, 0.8, SH - 12)
    play(cel, bar * 4, TUNE_A, 50, 0.7, SH + 12, only=lambda q: q % 2 == 0)
    bar += 8
    assert bar == 24
    return list(b_.values()), 168, bar


for name, fn in (("slipfloe_theme", theme), ("slipfloe_hurry", hurry)):
    tracks, bpm, bars = fn()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
