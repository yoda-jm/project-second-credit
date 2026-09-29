#!/usr/bin/env python3
"""Game 26 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own: an
easy evening garden party for a round of mini-golf under paper lanterns, from golden hour into the night. No
quotations: nothing from any golf game's music, no bossa nova or jazz standard, no existing video-game or film
theme. The motif is a putt: a pick-up, a climb up the chord (d g b) and a gentle roll back down (a f#).
- lanternlinks_theme: G major, 100 bpm, a straight bossa feel. An upright bass (root and fifth, the bossa step),
  nylon guitar comping on the 3-2 clave with a soft thumb, electric piano chords, a slow strings pad, brushes
  (swirls, taps on two and four, a side-stick on the clave, a shaker). Form: intro 4 (guitar, bass, electric
  piano, the brushes swirling in) | A 8 (the electric piano sings the tune) | B 8 (a clarinet takes the bridge
  through C, Cm6 and the minor turns, a flute answering) | A' 8 (the vibraphone with the tune, the flute's long
  counter-line above, the strings in) | tag 4 (Gmaj7, Cm6, back through Am7 D7 to the top) = 32 bars (76.8 s).
- lanternlinks_night: the same garden later at night, G major, 72 bpm, sparse and dreamy: a warm pad, a harp's
  slow broken chords, the bass on one and three, brushes barely swirling. The celesta plays the motif stretched
  out, then a music box takes the bridge with the celesta answering. Form: intro 4 (pad and a music-box
  arpeggio) | A 8 (celesta) | B 8 (music box) | outro 4 (the motif once more, fading to Am7 D7) = 24 bars (80.0 s).
Usage: python3 tools/audio/lanternlinks_music.py
-> godot/games/lanternlinks/audio/music/lanternlinks_theme.ogg, lanternlinks_night.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/lanternlinks/audio/music/"
BRUSH_KIT = 40  # the brush kit on the drum channel
KICK, STICK, TAP, SLAP, SWIRL, PEDAL, RIDE, MARACAS, TRIANGLE, CHIMES = 36, 37, 38, 39, 40, 44, 51, 70, 81, 84
CELESTA, MUSIC_BOX, VIBES, EPIANO, NYLON, UPRIGHT, HARP, STRINGS, CLARINET, FLUTE, WARM_PAD = \
    8, 10, 11, 4, 24, 32, 46, 49, 71, 73, 89
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


# chords as (bass root, a rootless four-note voicing around middle C: thirds, sevenths and colours)
Gmaj7, Em7, Am7, D7, Bm7, E7, Cmaj7, Cm6, Fsm7b5, B7, A7 = (
    (43, [59, 62, 66, 69]), (40, [55, 59, 62, 66]), (45, [60, 64, 67, 71]), (38, [54, 60, 64, 69]),
    (47, [57, 62, 66, 69]), (40, [56, 62, 66, 71]), (48, [59, 62, 64, 67]), (48, [57, 60, 63, 67]),
    (42, [57, 60, 64, 66]), (47, [57, 63, 66, 68]), (45, [55, 61, 64, 66]))
INTRO = [[Gmaj7], [Cmaj7], [Bm7, E7], [Am7, D7]]
A_PROG = [[Gmaj7], [Em7], [Am7], [D7], [Bm7, E7], [Am7, D7], [Gmaj7, Em7], [Am7, D7]]
B_PROG = [[Cmaj7], [Cm6], [Bm7], [E7], [Am7], [D7], [Fsm7b5, B7], [Am7, D7]]
TAG = [[Gmaj7], [Cm6], [Gmaj7], [Am7, D7]]
NIGHT_INTRO = [[Gmaj7], [Em7], [Cmaj7], [Am7, D7]]
NIGHT_A = [[Gmaj7], [Em7], [Am7], [D7], [Bm7], [E7], [Am7], [Cm6]]
NIGHT_B = [[Cmaj7], [Bm7], [Am7], [Gmaj7], [Cmaj7], [Cm6], [Bm7, E7], [Am7, D7]]
NIGHT_OUT = [[Gmaj7], [Cmaj7], [Gmaj7], [Am7, D7]]

TUNE_A = mel("r/.5 d5/.5 g5/.5 b5/1 a5/.5 f#5/1 | g5/1.5 e5/.5 d5/1 b4/1 | r/.5 c5/.5 e5/.5 g5/1 f#5/.5 e5/1 | "
             "f#5/2.5 r/.5 d5/.5 e5/.5 | f#5/.5 a5/.5 d6/1 b5/.5 g#5/.5 e5/1 | c6/1 a5/.5 e5/.5 f#5/.5 a5/.5 c6/1 | "
             "b5/1.5 a5/.5 g5/1 e5/1 | g5/.5 f#5/.5 e5/.5 d5/1 r/1.5")
COUNTER_A = mel("r/2 d6/1 b5/1 | g5/4 | r/2 e6/1 c6/1 | a5/4 | r/1 d6/1 b5/2 | c6/2 a5/2 | d6/2 b5/2 | c6/2 a5/1 r/1")
TUNE_B = mel("e5/.5 g5/.5 b5/1.5 a5/.5 g5/1 | eb5/.5 g5/.5 a5/1.5 g5/.5 eb5/1 | d5/.5 f#5/.5 a5/1.5 f#5/.5 d6/1 | "
             "b5/2 g#5/1 r/1 | c6/.5 b5/.5 a5/.5 e5/1 g5/.5 a5/1 | f#5/1.5 e5/.5 d5/1 c5/1 | "
             "a5/.5 c6/.5 e6/1 d#6/.5 b5/.5 f#5/1 | a5/1 g5/.5 e5/.5 f#5/.5 a5/.5 d5/1")
ANSWER_B = mel("r/3 d6/.5 e6/.5 | r/3 c6/.5 eb6/.5 | r/3 f#6/.5 a6/.5 | g#6/1 f#6/1 e6/2 | "
               "r/3 g6/.5 e6/.5 | r/3 a6/.5 f#6/.5 | r/4 | r/2 c6/1 d6/1")
TUNE_TAG = mel("r/.5 d5/.5 g5/.5 b5/1 a5/.5 f#5/1 | g5/2 eb5/2 | r/.5 d5/.5 g5/.5 b5/1 d6/1.5 | c6/1 a5/1 f#5/1 d5/1")

NIGHT_TUNE_A = mel("r/1 d5/1 g5/1 b5/1 | a5/3 f#5/1 | g5/1.5 e5/.5 c5/2 | d5/3 r/1 | "
                   "r/1 f#5/1 a5/1 d6/1 | b5/3 g#5/1 | c6/1.5 b5/.5 a5/1 e5/1 | g5/2 eb5/2")
NIGHT_TUNE_B = mel("e5/1 g5/1 b5/2 | a5/1.5 f#5/.5 d5/2 | c6/1 b5/1 a5/1 g5/1 | f#5/3 r/1 | "
                   "e6/2 d6/1 b5/1 | c6/2 a5/1 eb5/1 | d5/1 f#5/1 g#5/1 b5/1 | a5/2 f#5/1 r/1")
NIGHT_OUT_TUNE = mel("r/1 d5/1 g5/1 b5/1 | a5/3 f#5/1 | g5/4 | r/4")


def band():
    drums = Track(9, 0, 84, 64, 40)
    drums.events.append((0, bytes([0xC9, BRUSH_KIT])))
    return dict(bass=Track(0, UPRIGHT, 112, 60, 30), gtr=Track(1, NYLON, 92, 44, 45), ep=Track(2, EPIANO, 96, 72, 50),
                vibes=Track(3, VIBES, 90, 80, 60), strings=Track(4, STRINGS, 66, 64, 75),
                clar=Track(5, CLARINET, 88, 58, 55), flute=Track(6, FLUTE, 80, 86, 65),
                cel=Track(7, CELESTA, 100, 70, 70), box=Track(8, MUSIC_BOX, 88, 52, 75),
                harp=Track(10, HARP, 84, 40, 65), pad=Track(11, WARM_PAD, 70, 64, 80), dr=drums)


def parts(t):
    bass, gtr, ep, strings, harp, pad, dr = (t[k] for k in ("bass", "gtr", "ep", "strings", "harp", "pad", "dr"))

    def bossa_bass(b, bar, vel=96):
        """The bossa step: the root on one, the fifth on the and of two held over three, the root again on the and
        of four (per half bar when the bar holds two chords)."""
        for off, ln, (root, v) in split(bar):
            lo = root if root < 45 else root - 12
            if ln == 4:
                pat = [(0, lo, 1.4), (1.5, lo + 7, 0.45), (2, lo + 7, 1.4), (3.5, lo, 0.45)]
            else:
                pat = [(0, lo, 1.4), (1.5, lo + 7, 0.45)]
            for q, p, L in pat:
                note(bass, b + off + q, L, p, vel - (0 if q in (0, 2) else 14))

    def comp(b, bar, second, vel=60):
        """The nylon guitar: chord stabs on the 3-2 clave (one, the and of two, four | two, the and of three),
        a soft thumb on the root on each beat, the stab rolled up quickly."""
        hits = (1, 2.5) if second else (0, 1.5, 3)
        for off, ln, (root, v) in split(bar):
            lo = root if root < 45 else root - 12
            for q in range(int(ln)):
                note(gtr, b + off + q, 0.8, lo + 12 + (7 if q % 2 else 0), vel - 12)
        for q in hits:
            off, ln, (root, v) = [c for c in split(bar) if c[0] <= q][-1]
            for k, p in enumerate(v):
                note(gtr, b + q + k * 0.015, 0.45, p, vel + (6 if q == 0 else 0) - 2 * k)

    def keys(b, bar, vel=52, busy=True):
        """The electric piano: the chord laid on one and, when busy, pushed again on the and of two."""
        for off, ln, (root, v) in split(bar):
            for p in v:
                note(ep, b + off, 1.4 if busy else ln, p, vel)
                if busy and ln == 4:
                    note(ep, b + off + 2.5, 1.3, p, vel - 8)

    def pads(b, bar, vel=48, track=None):
        for off, ln, (root, v) in split(bar):
            for p in v:
                note(track or strings, b + off, ln, p, vel)

    def brushes(b, second, vel=54, fill=False):
        """Brushes: a swirl every half bar, taps on two and four, the side-stick on the clave, a soft kick on one
        and the and of two, a shaker in eighths."""
        note(dr, b, 1.9, SWIRL, vel - 6)
        note(dr, b + 2, 1.9, SWIRL, vel - 12)
        note(dr, b + 1, 0.2, TAP, vel)
        note(dr, b + 3, 0.2, SLAP if fill else TAP, vel + (8 if fill else 2))
        for q in ((1, 2.5) if second else (0, 1.5, 3)):
            note(dr, b + q, 0.1, STICK, vel - 8)
        for q in (0, 1.5):
            note(dr, b + q, 0.2, KICK, vel - 6 - (8 if q else 0))
        for k in range(8):
            note(dr, b + k * 0.5, 0.1, MARACAS, vel - 26 + (8 if k % 2 else 0))
        if fill:
            for k in range(4):
                note(dr, b + 2 + k * 0.5 + 0.25, 0.1, TAP, vel - 20 + 5 * k)

    def harp_roll(b, bar, vel=56, step=1.0):
        """The harp: slow broken chords, root then the voicing climbing."""
        for off, ln, (root, v) in split(bar):
            lo = root if root < 45 else root - 12
            notes = [lo + 12] + v + [v[1] + 12]
            for k in range(int(ln / step)):
                note(harp, b + off + k * step, step * 2, notes[k % len(notes)], vel - 4 * (k % 2))

    return bossa_bass, comp, keys, pads, brushes, harp_roll


def theme():
    t = band()
    bass, gtr, ep, vibes, strings, clar, flute, cel, dr = (t[k] for k in (
        "bass", "gtr", "ep", "vibes", "strings", "clar", "flute", "cel", "dr"))
    bossa_bass, comp, keys, pads, brushes, harp_roll = parts(t)

    def accomp(start, prog, vel=96, ep_vel=50, pad=False, busy=True):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            bossa_bass(b, ch, vel)
            comp(b, ch, i % 2 == 1, vel - 36)
            keys(b, ch, ep_vel, busy)
            brushes(b, i % 2 == 1, vel - 42, fill=i == len(prog) - 1)
            if pad:
                pads(b, ch, 46)

    # intro: guitar, bass and electric piano, the brushes swirling in, a vibraphone lift into the tune
    for i, ch in enumerate(INTRO):
        b = i * 4
        comp(b, ch, i % 2 == 1, 56 + 2 * i)
        bossa_bass(b, ch, 84 + 3 * i)
        keys(b, ch, 44 + 2 * i, busy=False)
        if i >= 1:
            brushes(b, i % 2 == 1, 44 + 3 * i, fill=i == 3)
        else:  # only the swirl and the shaker carry over from the loop's end
            note(dr, b, 1.9, SWIRL, 40)
            note(dr, b + 2, 1.9, SWIRL, 36)
            for k in range(8):
                note(dr, b + k * 0.5, 0.1, MARACAS, 30 + (8 if k % 2 else 0))
    for k, p in enumerate((62, 67, 71, 74)):
        note(vibes, 14 + k * 0.5, 0.45, p + 12, 52 + 5 * k)
    bar = 4

    accomp(bar, A_PROG, 96, 46)  # A: the electric piano sings the tune over its own soft chords
    play(ep, bar * 4, TUNE_A, 96, 0.92, 0)
    play(ep, bar * 4, TUNE_A, 56, 0.9, 12)  # doubled softly an octave up, a Rhodes shimmer
    note(dr, bar * 4, 3, RIDE, 40)
    bar += 8

    accomp(bar, B_PROG, 92, 44, pad=True)  # B: the clarinet takes the bridge, the flute answers at bar ends
    play(clar, bar * 4, TUNE_B, 88, 0.95, -12)
    play(flute, bar * 4, ANSWER_B, 64, 0.9)
    note(dr, bar * 4 + 28, 2, CHIMES, 38)
    bar += 8

    accomp(bar, A_PROG, 100, 42, pad=True)  # A': the vibraphone with the tune, the flute's counter-line above
    play(vibes, bar * 4, TUNE_A, 100, 0.85, 0)
    play(ep, bar * 4, TUNE_A, 48, 0.85, -12)
    play(flute, bar * 4, COUNTER_A, 66, 0.95)
    note(dr, bar * 4, 3, RIDE, 44)
    bar += 8

    accomp(bar, TAG, 90, 44, pad=True)  # tag: the motif on the electric piano and vibraphone together, back to the top
    play(ep, bar * 4, TUNE_TAG, 88, 0.9)
    play(vibes, bar * 4, TUNE_TAG, 60, 0.8, 12)
    note(dr, bar * 4 + 8, 4, TRIANGLE, 34)
    bar += 4
    assert bar == 32
    return list(t.values()), 100, bar


def night():
    t = band()
    bass, cel, box, pad, harp, dr = (t[k] for k in ("bass", "cel", "box", "pad", "harp", "dr"))
    bossa_bass, comp, keys, pads, brushes, harp_roll = parts(t)

    def bed(start, prog, vel=80, harp_on=True, brush=True):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            pads(b, ch, 54, pad)
            for off, ln, (root, v) in split(ch):  # the bass on one and three, long and soft
                lo = root if root < 45 else root - 12
                note(bass, b + off, min(ln, 2) * 0.9, lo, vel)
                if ln == 4:
                    note(bass, b + off + 2, 1.8, lo + 7, vel - 14)
            if harp_on:
                harp_roll(b, ch, vel - 30)
            if brush:
                note(dr, b, 3.8, SWIRL, 30)
                note(dr, b + 3, 0.2, TAP, 26)

    for i, ch in enumerate(NIGHT_INTRO):  # intro: the pad and a music-box arpeggio, the bass in at bar 3
        b = i * 4
        pads(b, ch, 50 + 2 * i, pad)
        for off, ln, (root, v) in split(ch):
            for k in range(int(ln * 2)):
                note(box, b + off + k * 0.5, 0.9, v[k % 4] + 12 + (12 if k % 8 >= 4 else 0), 50 + (10 if k % 4 == 0 else 0))
        if i >= 2:
            lo = ch[0][0] if ch[0][0] < 45 else ch[0][0] - 12
            note(bass, b, 1.8, lo, 70)
    bar = 4

    bed(bar, NIGHT_A)  # A: the celesta plays the motif stretched out
    play(cel, bar * 4, NIGHT_TUNE_A, 92, 0.95)
    note(dr, bar * 4, 4, CHIMES, 30)
    bar += 8

    bed(bar, NIGHT_B, 78, harp_on=False)  # B: the music box takes the bridge, the celesta answers in chord tones
    play(box, bar * 4, NIGHT_TUNE_B, 84, 0.95)
    for i, ch in enumerate(NIGHT_B):
        for off, ln, (root, v) in split(ch):
            b = (bar + i) * 4 + off
            note(cel, b + ln - 1, 0.9, v[2] + 12, 50)
            if ln == 4:
                note(cel, b + 2.5, 0.9, v[3], 46)
    bar += 8

    bed(bar, NIGHT_OUT, 74, brush=False)  # outro: the motif once more, fading, the harp leading back to the top
    play(cel, bar * 4, NIGHT_OUT_TUNE, 80, 0.95)
    note(dr, bar * 4 + 8, 4, SWIRL, 24)
    note(dr, bar * 4 + 12, 3, CHIMES, 26)
    bar += 4
    assert bar == 24
    return list(t.values()), 72, bar


for name, song in (("lanternlinks_theme", theme), ("lanternlinks_night", night)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
