#!/usr/bin/env python3
"""Game 16 music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Every tune is our own:
a small ragtime/swing band for a cosy canal town (no quotations: nothing from the arcade game's tunes nor from
the children's songs it used, no classic rags).
- hopline_theme: jaunty, F major, 144 bpm, swung eighths. Stride piano (bass and chord on alternate beats),
  clarinet tune, muted trumpet, a trombone answering in the low register, banjo on the off-beats, upright bass
  (two-feel, then walking), brushes and a ride, a xylophone glint.
  Form: intro 4 | A 8 (clarinet) | A' 8 (clarinet and trumpet) | B 8 (trumpet, in B flat colours) |
  C 8 (stop-time call and answer in D minor, clarinet and trombone) | A' 8 | loops to the intro (73 s).
- hopline_hurry: the same band chasing the clock, 176 bpm, lighter swing: the A tune pushed up, a banjo strum
  on every beat, an eighth-note chase round the circle of fifths, the xylophone doubling at the end, and a
  C7 turnaround back to the top. 24 bars (33 s).
Usage: python3 tools/audio/hopline_music.py
-> godot/games/hopline/audio/music/hopline_theme.ogg and hopline_hurry.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/hopline/audio/music/"
BRUSH_KIT = 40  # the brush kit on the drum channel
KICK, TAP, SLAP, SWIRL, STICK, PEDAL, RIDE, CRASH = 36, 38, 39, 40, 37, 44, 51, 49
PIANO, BANJO, CLARINET, MUTED_TPT, TROMBONE, UPRIGHT, XYLO = 0, 105, 71, 59, 57, 32, 13
NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SWING = [0.62]  # where the off-beat eighth lands (0.5 = straight); set per piece

# chords as (root, alternate bass, voicing around middle C)
F, F6, F7 = (41, 36, [57, 60, 65]), (41, 36, [57, 62, 65]), (41, 36, [57, 63, 65])
Bb, Bbm, Bdim = (46, 41, [58, 62, 65]), (46, 41, [58, 61, 65]), (47, 41, [59, 62, 65, 68])
C7, G7, D7, A7, Dm = (36, 43, [58, 60, 64]), (43, 38, [59, 62, 65]), (38, 45, [57, 60, 66]), \
    (45, 40, [55, 61, 64]), (38, 45, [57, 62, 65])
Gm7, E7 = (43, 38, [58, 62, 65]), (40, 47, [56, 62, 64])


def mel(text):
    """Parses a line like "a4/.5 c5/1 r/.5" into [(beat, length, pitch)]; '#' sharpens, 'b' flattens
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


def sw(beat):
    """Swings a position: an eighth on the 'and' of a beat moves late."""
    i = int(beat // 1)
    f = beat - i
    return i + SWING[0] if abs(f - 0.5) < 1e-6 else beat


def note(track, beat, length, pitch, vel):
    a, b = sw(beat), sw(beat + length)
    track.note(a, max(0.05, b - a - 0.02), pitch, max(1, min(127, int(vel))))


def play(track, start, line, vel, legato=0.92, shift=0, accent=6):
    for beat, length, pitch in line:
        v = vel + (accent if beat % 1 == 0 else 0)
        a, b = sw(start + beat), sw(start + beat + length)
        track.note(a, max(0.05, (b - a) * legato), pitch + shift, max(1, min(127, int(v))))


def third_below(p):
    """The diatonic third below in F major (B natural, from G7, falls to G)."""
    scale = [0, 2, 4, 5, 7, 9, 10]
    pc = p % 12
    if pc not in scale:
        return p - 4
    return p - (pc - scale[(scale.index(pc) - 2) % 7]) % 12


def split(bar):
    """A bar's chords as (offset, beats, chord): one chord fills the bar, two split it in half."""
    ln = 4 / len(bar)
    return [(k * ln, ln, c) for k, c in enumerate(bar)]


def band():
    drums = Track(9, 0, 108, 64, 35)
    drums.events.append((0, bytes([0xC9, BRUSH_KIT])))
    return dict(pno=Track(0, PIANO, 127, 58, 35), cla=Track(1, CLARINET, 98, 44, 45),
                tpt=Track(2, MUTED_TPT, 104, 84, 45), tbn=Track(3, TROMBONE, 104, 70, 40),
                bjo=Track(4, BANJO, 96, 90, 30), bass=Track(5, UPRIGHT, 96, 60, 25),
                xyl=Track(6, XYLO, 104, 36, 50), dr=drums)


def parts(t):
    pno, bjo, bass, dr = t["pno"], t["bjo"], t["bass"], t["dr"]

    def stride(b, bar, vel=84, rh=True):
        """Stride piano: the left hand leaps between a low bass (root, then the alternate bass) and a mid chord;
        the right hand pokes syncopated chord stabs an octave up."""
        for off, ln, (root, alt, v) in split(bar):
            for k in range(int(ln)):
                q = b + off + k
                if k % 2 == 0:
                    lo = root if (off + k) % 4 == 0 or len(bar) > 1 else alt
                    lo = lo - 12 if lo >= 40 else lo  # an octave in the left hand, from about E1 to E3
                    note(pno, q, 0.9, lo, vel + 4)
                    note(pno, q, 0.9, lo + 12, vel - 8)
                else:
                    for p in v:
                        note(pno, q, 0.45, p, vel - 16)
            if rh:
                top = [p + 12 for p in v]
                for q in ((0.5, 1.5) if ln == 2 else (0.5, 1.5, 3)):
                    for p in top:
                        note(pno, b + off + q, 0.4, p, vel - 20)

    def banjo(b, bar, vel=70, every=False):
        """Banjo chords on 2 and 4 (every beat when hurrying), a lighter brush-strum on the others."""
        for off, ln, (root, alt, v) in split(bar):
            for k in range(int(ln)):
                q = b + off + k
                strong = (off + k) % 2 == 1
                if strong or every:
                    for j, p in enumerate(v + [v[0] + 12]):
                        note(bjo, q + j * 0.012, 0.35, p + 12 if p < 60 else p, vel if strong else vel - 14)

    def two_feel(b, bar, vel=92):
        for off, ln, (root, alt, v) in split(bar):
            note(bass, b + off, 1.6, root, vel)
            if ln == 4:
                note(bass, b + off + 2, 1.6, alt if alt > root - 7 else alt + 12, vel - 6)

    def walk(b, bar, nxt, vel=92):
        """A walking line: root, third or fifth, fifth, then a half step into the next chord's root."""
        for off, ln, (root, alt, v) in split(bar):
            third = min(p for p in v) % 12
            steps = [root, root + ((third - root) % 12), root + 7, None] if ln == 4 else [root, root + 7]
            for k, p in enumerate(steps):
                if p is None:
                    p = nxt + (1 if nxt < root + 7 else -1)
                note(bass, b + off + k, 0.9, p if p < 52 else p - 12, vel - (0 if k % 2 == 0 else 6))

    def brushes(b, vel=60, busy=False, fill=False):
        """Brushes: a whisper of a kick on 1 and 3, taps on 2 and 4, a swung ride, swirls on the snare."""
        for q in range(4):
            note(dr, b + q, 0.3, RIDE, vel - 8 + (8 if q % 2 else 0))
            if q % 2:
                note(dr, b + q + 0.5, 0.2, RIDE, vel - 18)
                note(dr, b + q, 0.2, TAP, vel + 4)
                note(dr, b + q, 0.2, PEDAL, vel - 10)
            else:
                note(dr, b + q, 0.2, KICK, vel)
                note(dr, b + q, 0.9, SWIRL, vel - 22)
        if busy:
            for q in (0.5, 2.5):
                note(dr, b + q, 0.1, TAP, vel - 24)
        if fill:
            for k in range(6):
                dr.note(b + 3 + k / 6, 0.1, SLAP, vel - 12 + 5 * k)

    return stride, banjo, two_feel, walk, brushes


# ---------------------------------------------------------------------------------------------------------------
INTRO = [[C7], [C7], [F, D7], [G7, C7]]
A_PROG = [[F], [D7], [G7], [C7], [F], [F7], [Bb, Bbm], [F, C7]]
A_END = [[F], [D7], [G7], [C7], [F], [F7], [Bb, Bbm], [F]]
B_PROG = [[Bb], [Bdim], [F], [D7], [G7], [C7], [F, D7], [G7, C7]]
C_PROG = [[Dm], [A7], [Dm], [A7], [Bb], [F], [G7], [C7]]

TUNE_A = mel("a4/.5 c5/1 f5/.5 r/.5 e5/.5 f5/1 | f#5/.5 a5/1 f#5/.5 d5/1 c5/1 | "
             "b4/.5 d5/1 g5/.5 f5/.5 d5/.5 b4/1 | c5/1.5 e5/.5 g5/.5 bb5/1 a5/.5 | "
             "a5/.5 c6/1 a5/.5 f5/1 r/.5 c5/.5 | eb5/.5 f5/1 a5/.5 c6/.5 a5/.5 f5/1 | "
             "d5/.5 f5/.5 bb5/1 db5/.5 f5/.5 bb5/1 | a5/1 g5/.5 f5/.5 e5/.5 g5/.5 c5/1")
TUNE_A_END = [n_ for n_ in TUNE_A if n_[0] < 28] + [(28 + b, ln, p) for b, ln, p in mel("f5/1.5 c5/.5 f4/1 r/1")]
# the trumpet's answers in A': short muted fills in the gaps of the tune
FILLS_A = mel("r/3 c5/.5 d5/.5 | r/3 a4/.5 c5/.5 | r/3 f5/.5 d5/.5 | r/2.5 e5/.5 r/1 | "
              "r/3 f5/.5 g5/.5 | r/3 c5/.5 eb5/.5 | r/4 | r/2 bb4/.5 c5/.5 r/1")
TUNE_B = mel("f5/1.5 d5/.5 bb4/1 d5/1 | ab5/1.5 f5/.5 d5/1 b4/1 | c5/.5 d5/.5 f5/.5 a5/1 g5/.5 f5/1 | "
             "f#5/1.5 a5/.5 c6/1 a5/1 | b5/.5 a5/.5 g5/.5 f5/1 d5/.5 b4/1 | c5/.5 e5/.5 g5/.5 bb5/1 a5/.5 g5/1 | "
             "a5/1 f5/1 f#5/1 a5/1 | g5/.5 f5/.5 d5/1 e5/.5 g5/.5 c6/1")
# the clarinet under the trumpet in B: long low notes, a lazy countermelody
COUNTER_B = mel("d4/2 f4/2 | f4/2 ab4/2 | a4/3 c4/1 | c4/2 d4/2 | d4/2 b3/2 | bb3/2 c4/2 | c4/2 d4/2 | b3/2 bb3/2")
# C: stop-time call (clarinet) and answer (trombone), then the two together over Bb F G7 C7
CALL_C = mel("a5/.5 f5/.5 d5/.5 f5/.5 a5/1 r/1 | r/4 | d6/.5 c6/.5 a5/.5 f5/.5 d5/1 r/1 | r/4 | "
             "d5/1 f5/1 bb5/1.5 a5/.5 | a5/1 c6/1 a5/1 f5/1 | g5/.5 a5/.5 b5/.5 d6/.5 f6/1 d6/1 | "
             "e6/1 c6/.5 bb5/.5 g5/.5 e5/.5 c5/1")
ANSWER_C = mel("r/4 | r/1 e3/.5 g3/.5 c#4/.5 e4/.5 c#4/1 | r/4 | r/1 a3/.5 g3/.5 e3/.5 c#3/.5 a2/1 | "
               "bb2/2 d3/2 | f3/2 c3/2 | g2/2 b2/2 | c3/2 e3/1 g3/1")
PICKUP = mel("r/4 | r/4 | r/4 | r/2 g4/.5 a4/.5 bb4/.5 b4/.5")  # the clarinet climbs into the A tune


def theme():
    SWING[0] = 0.62
    t = band()
    pno, cla, tpt, tbn, xyl, dr = t["pno"], t["cla"], t["tpt"], t["tbn"], t["xyl"], t["dr"]
    stride, banjo, two_feel, walk, brushes = parts(t)

    bar = 0
    for i, ch in enumerate(INTRO):  # intro: the piano vamps alone, the band falls in, a clarinet pickup
        b = (bar + i) * 4
        stride(b, ch, 78 + 3 * i, rh=i >= 1)
        if i >= 2:
            banjo(b, ch, 60)
            two_feel(b, ch, 84)
            brushes(b, 50, fill=i == 3)
    note(xyl, 0.5, 0.5, 84, 60)
    note(xyl, 1, 0.5, 88, 64)
    play(cla, 0, PICKUP, 84)
    bar += 4

    def section(prog, lead, fills, walking, vel=88, nxt=41):
        nonlocal bar
        for i, ch in enumerate(prog):
            b = (bar + i) * 4
            stride(b, ch, 82)
            banjo(b, ch, 66)
            if walking:
                n_root = prog[i + 1][0][0] if i + 1 < len(prog) else nxt
                walk(b, ch, n_root)
            else:
                two_feel(b, ch)
            brushes(b, 58, busy=walking, fill=i == 7)
        play(cla, bar * 4, lead, vel)
        if fills:
            play(tpt, bar * 4, fills, 76, 0.8)
        bar += 8

    section(A_PROG, TUNE_A, None, False)
    section(A_PROG, TUNE_A, FILLS_A, True, 94, 46)

    for i, ch in enumerate(B_PROG):  # B: the muted trumpet takes the tune, the clarinet goes low and lazy
        b = (bar + i) * 4
        stride(b, ch, 76, rh=i % 2 == 0)
        banjo(b, ch, 62)
        walk(b, ch, B_PROG[i + 1][0][0] if i < 7 else 38)
        brushes(b, 56, fill=i == 7)
        if i in (3, 7):
            note(xyl, b + 3.5, 0.5, 84 + (5 if i == 7 else 0), 58)
    play(tpt, bar * 4, TUNE_B, 92)
    play(cla, bar * 4, COUNTER_B, 70, 0.95)
    bar += 8

    for i, ch in enumerate(C_PROG):  # C: stop-time for four bars (hits on 1 and the 'and' of 2), then all in
        b = (bar + i) * 4
        root, alt, v = ch[0]
        if i < 4:
            for q in (0, 1.5):
                for p in v:
                    note(pno, b + q, 0.4, p, 86)
                    note(t["bjo"], b + q, 0.3, p + 12 if p < 60 else p, 72)
                note(pno, b + q, 0.4, root - 12, 90)
                note(t["bass"], b + q, 0.4, root, 98)
                note(dr, b + q, 0.2, TAP, 76)
                note(dr, b + q, 0.2, KICK, 70)
            note(dr, b, 0.5, CRASH if i == 0 else PEDAL, 52)
        else:
            stride(b, ch, 86)
            banjo(b, ch, 70)
            walk(b, ch, C_PROG[i + 1][0][0] if i < 7 else 41)
            brushes(b, 62, busy=True, fill=i == 7)
    play(cla, bar * 4, CALL_C, 92)
    play(tbn, bar * 4, ANSWER_C, 90, 0.9)
    play(tpt, bar * 4, [(b, ln, third_below(p)) for b, ln, p in CALL_C if b >= 16], 72)  # a third below, last 4 bars
    note(xyl, bar * 4 + 16, 0.5, 86, 64)
    note(xyl, bar * 4 + 20, 0.5, 89, 64)
    bar += 8

    section(A_END, TUNE_A_END, FILLS_A, True, 96, 36)
    note(xyl, (bar - 1) * 4 + 1.5, 0.5, 77, 64)  # a xylophone wink on the final F
    note(xyl, (bar - 1) * 4 + 2, 0.5, 89, 70)
    assert bar == 44
    return list(t.values()), 144, bar


# ---------------------------------------------------------------------------------------------------------------
CHASE_PROG = [[F], [A7], [D7], [D7], [G7], [G7], [C7], [C7]]
HURRY_A = mel("c5/.5 f5/.5 a5/.5 f5/.5 c6/1 a5/1 | a5/.5 f#5/.5 d5/.5 f#5/.5 a5/1 c6/1 | "
              "b5/.5 g5/.5 d5/.5 g5/.5 f5/1 d5/1 | e5/.5 g5/.5 bb5/.5 c6/.5 e6/1 c6/1 | "
              "a5/.5 c6/.5 f6/.5 c6/.5 a5/1 f5/1 | eb5/.5 f5/.5 a5/.5 c6/.5 eb6/1 c6/1 | "
              "d6/.5 bb5/.5 f5/.5 bb5/.5 db6/.5 bb5/.5 f5/.5 db5/.5 | c5/1 a4/.5 c5/.5 e5/.5 g5/.5 bb5/1")
CHASE = mel("c5/.5 d5/.5 e5/.5 f5/.5 a5/.5 g5/.5 f5/.5 c5/.5 | c#5/.5 e5/.5 g5/.5 a5/.5 c#6/.5 a5/.5 g5/.5 e5/.5 | "
            "d5/.5 f#5/.5 a5/.5 c6/.5 d6/.5 c6/.5 a5/.5 f#5/.5 | a5/.5 f#5/.5 d5/.5 f#5/.5 a5/.5 c6/.5 eb6/.5 d6/.5 | "
            "b5/.5 g5/.5 d5/.5 g5/.5 b5/.5 d6/.5 f6/.5 d6/.5 | b5/.5 a5/.5 g5/.5 f5/.5 d5/.5 f5/.5 g5/.5 b5/.5 | "
            "c6/.5 bb5/.5 g5/.5 e5/.5 c5/.5 e5/.5 g5/.5 bb5/.5 | c6/1 bb5/.5 g5/.5 e5/.5 c5/.5 d5/.5 e5/.5")
# the trombone pushes low long notes under the chase
PUSH = mel("f2/2 c3/2 | a2/2 e3/2 | d3/2 a2/2 | d3/2 f#3/2 | g2/2 d3/2 | g2/2 b2/2 | c3/2 g2/2 | c3/2 e3/2")


def hurry():
    SWING[0] = 0.58
    t = band()
    cla, tpt, tbn, xyl = t["cla"], t["tpt"], t["tbn"], t["xyl"]
    stride, banjo, two_feel, walk, brushes = parts(t)

    def accomp(start, prog, vel):
        for i, ch in enumerate(prog):
            b = (start + i) * 4
            stride(b, ch, vel, rh=True)
            banjo(b, ch, vel - 12, every=True)
            walk(b, ch, prog[i + 1][0][0] if i + 1 < len(prog) else 41, vel + 8)
            brushes(b, vel - 20, busy=True, fill=i == 7)

    accomp(0, A_PROG, 84)  # A: the clarinet tune pushed into running arpeggios, trumpet stabs on the offbeats
    play(cla, 0, HURRY_A, 94, 0.85)
    for i in range(8):
        note(tpt, i * 4 + 1.5, 0.3, A_PROG[i][0][2][-1] + 12, 70)
        note(tpt, i * 4 + 3.5, 0.3, A_PROG[i][-1][2][-1] + 12, 74)
    accomp(8, CHASE_PROG, 88)  # the chase: clarinet and trumpet in unison runs round the circle of fifths
    play(cla, 32, CHASE, 96, 0.85)
    play(tpt, 32, CHASE, 76, 0.8, -12)
    play(tbn, 32, PUSH, 88, 0.95)
    accomp(16, A_PROG, 92)  # A again, the xylophone doubling an octave up, the C7 turn back to the top
    play(cla, 64, HURRY_A, 98, 0.85)
    play(xyl, 64, HURRY_A, 70, 0.6, 12, 0)
    play(tbn, 64, PUSH, 80, 0.95)
    return list(t.values()), 176, 24


for name, song in (("hopline_theme", theme), ("hopline_hurry", hurry)):
    tracks, bpm, bars = song()
    secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.6, rms_db=-18.3)
    print(f"wrote {name}.ogg ({secs:.1f} s loop)")
