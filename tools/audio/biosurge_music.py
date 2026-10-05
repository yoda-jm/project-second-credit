#!/usr/bin/env python3
"""Game 34 (Biosurge) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of any game's music, no existing film or game theme. Electronic and synth, with an organic, pulsing edge
for a flight through living caverns: the kick doubles like a heartbeat, the bass throbs in sixteenths, gurgling FX
patches and kalimba drops sit in the breakdowns.
- biosurge_theme: E minor (a Phrygian F in the breakdown), 132 bpm, 48 bars (87.3 s). Form: intro 4 (heartbeat
  kick, sweep pad, crystal arpeggio, the bass creeping in) | A 8 (saw lead over a sixteenth synth bass: Em Em C D
  Em Em C B) | B 8 (the lead climbs: Am Am Em Em C D B B, square arpeggios, claps) | C 8 (breakdown: half-time
  heartbeat, kalimba and vibraphone call over Em F Em F C D Em B, gurgles) | A' 8 (full, a counter-line) |
  D 8 (climax: the tune an octave up over C D Em Em Am B Em B) | outro 4 (back down to the heartbeat) -> the top.
- biosurge_boss: E Phrygian, 150 bpm, 24 bars (38.4 s): toms and a rising bass in the intro, a driving octave-bass
  riff on E with F and Bb stabs, synth brass hits, a screaming saw lead, double-time hats, fills; loops to the top.
- biosurge_shop: a relaxed, quirky shop groove in C, 96 bpm, 12 bars (30.0 s): fretless bass, Rhodes chords on the
  off-beats, a kalimba and marimba tune that hops about (Dm7 G7 Cmaj7 Am7, then Fmaj7 E7 Am7 D7, Dm7 G7 C C),
  a light kit with shaker and woodblock.
No voices: no choir, voice-lead or halo patches.
Usage: python3 tools/audio/biosurge_music.py
-> godot/games/biosurge/audio/music/biosurge_theme.ogg, biosurge_boss.ogg, biosurge_shop.ogg (+ .mid)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/biosurge/audio/music/"
ELECTRONIC_KIT = 24
KICK, RIM, SNARE, CLAP, E_SNARE, CLOSED, PEDAL, OPEN, CRASH, RIDE = 36, 37, 38, 39, 40, 42, 44, 46, 49, 51
LO_TOM, MID_TOM, HI_TOM, TAMB, COWBELL, SHAKER, WOODBLOCK, CABASA = 45, 47, 50, 54, 56, 70, 76, 69
(EPIANO, VIBES, MARIMBA, FRETLESS, SQUARE, SAW, BASS_LEAD, WARM_PAD, POLY_PAD, SWEEP_PAD, CRYSTAL, ATMOS,
 GOBLINS, SCIFI, KALIMBA, SYNTH_BASS, SYNTH_BASS2, SYNTH_BRASS, MELO_TOM, PIZZ, STRINGS) = (
    4, 11, 12, 35, 80, 81, 87, 89, 90, 95, 98, 99, 101, 103, 108, 38, 39, 62, 117, 45, 48)
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


def kit_track(reverb=25):
    d = Track(9, 0, 104, 64, reverb)
    d.events.append((0, bytes([0xC9, ELECTRONIC_KIT])))
    return d


# chords: (bass root, voicing)
Em, C, D, B, Am, F, G, Bm = ((40, [59, 64, 67]), (36, [60, 64, 67]), (38, [57, 62, 66]), (35, [59, 63, 66]),
                             (33, [57, 60, 64]), (41, [57, 60, 65]), (43, [59, 62, 67]), (35, [59, 62, 66]))
A_PROG = [Em, Em, C, D, Em, Em, C, B]
B_PROG = [Am, Am, Em, Em, C, D, B, B]
C_PROG = [Em, F, Em, F, C, D, Em, B]
D_PROG = [C, D, Em, Em, Am, B, Em, B]

TUNE_A = mel("e5/.75 e5/.25 g5/.5 b5/.5 a5/.5 g5/.5 f#5/.5 g5/.5 | e5/1 b4/.5 d5/.5 e5/2 | "
             "g5/.75 g5/.25 e5/.5 g5/.5 c6/1 b5/.5 a5/.5 | f#5/.75 f#5/.25 a5/.5 d6/.5 c6/.5 b5/.5 a5/1 | "
             "e5/.75 e5/.25 g5/.5 b5/.5 e6/1 d6/.5 b5/.5 | g5/.5 a5/.5 b5/1 g5/.5 e5/.5 b4/1 | "
             "c6/.75 b5/.25 a5/.5 g5/.5 e5/1 g5/1 | f#5/.75 d#5/.25 f#5/.5 b5/.5 d#6/1 b5/1")
COUNTER_A = mel("b4/2 g4/2 | b4/2 e5/2 | c5/2 e5/2 | d5/2 f#5/2 | b4/2 g4/2 | b4/2 e5/2 | e5/2 c5/2 | d#5/2 f#5/2")
TUNE_B = mel("a5/1.5 c6/.5 e6/1 d6/.5 c6/.5 | b5/.5 c6/.5 a5/1 e5/2 | g5/1.5 b5/.5 e6/1 f#6/.5 g6/.5 | "
             "f#6/.5 e6/.5 b5/1 g5/2 | e6/1 g6/.5 e6/.5 c6/1 e6/1 | f#6/1 a6/.5 f#6/.5 d6/1 a5/1 | "
             "b5/.5 d#6/.5 f#6/.5 b6/.5 a6/1 f#6/1 | d#6/1 f#6/1 b5/2")
CALL_C = mel("e5/2 f5/2 | e5/1 b4/1 g4/2 | e5/2 f5/2 | g5/1 f5/1 e5/2 | c5/2 e5/2 | d5/2 f#5/2 | e5/3 r/1 | "
             "d#5/2 f#5/2")
TUNE_D = mel("e6/.75 e6/.25 g6/.5 e6/.5 c6/1 g5/1 | f#6/.75 f#6/.25 a6/.5 f#6/.5 d6/1 a5/1 | "
             "g6/.5 f#6/.5 e6/.5 b5/.5 e6/1 g6/1 | b6/1.5 a6/.5 g6/1 e6/1 | "
             "a6/.75 g6/.25 e6/.5 c6/.5 a5/1 c6/1 | b5/.5 d#6/.5 f#6/.5 a6/.5 b6/1 a6/1 | "
             "g6/.5 e6/.5 b5/.5 e6/.5 g6/1 b6/1 | a6/.75 f#6/.25 d#6/.5 b5/.5 f#6/2")


def theme():
    dr = kit_track()
    lead = Track(0, SAW, 88, 64, 45)
    lead2 = Track(1, SQUARE, 70, 40, 50)
    arp = Track(2, SQUARE, 58, 88, 55)
    bass = Track(3, SYNTH_BASS, 108, 64, 12)
    sub = Track(4, SYNTH_BASS2, 84, 64, 10)
    pad = Track(5, WARM_PAD, 64, 64, 80)
    sweep = Track(6, SWEEP_PAD, 60, 54, 90)
    crystal = Track(7, CRYSTAL, 58, 76, 70)
    kalimba = Track(8, KALIMBA, 80, 46, 70)
    vibes = Track(10, VIBES, 74, 82, 80)
    gob = Track(11, GOBLINS, 54, 64, 90)
    brass = Track(12, SYNTH_BRASS, 70, 70, 45)
    tracks = [dr, lead, lead2, arp, bass, sub, pad, sweep, crystal, kalimba, vibes, gob, brass]

    def heartbeat(b, vel=100, bars=1):
        """Lub-dub: a kick on 1 and the 'a' of 1, again on 3 and the 'a' of 3."""
        for i in range(bars):
            for q in (0, 2):
                note(dr, b + i * 4 + q, 0.2, KICK, vel)
                note(dr, b + i * 4 + q + 0.75, 0.2, KICK, vel - 22)

    def drive(b, vel=96, claps=True, fill=False, open_hat=True):
        for q in range(4):
            note(dr, b + q, 0.2, KICK, vel + 4)
        note(dr, b + 3.75, 0.2, KICK, vel - 26)   # the heartbeat's echo before the bar line
        for q in (1, 3):
            note(dr, b + q, 0.2, E_SNARE, vel - 6)
            if claps:
                note(dr, b + q, 0.2, CLAP, vel - 18)
        for k in range(16):
            st = k * 0.25
            if open_hat and k in (6, 14):
                note(dr, b + st, 0.2, OPEN, vel - 30)
            else:
                note(dr, b + st, 0.1, CLOSED, vel - 40 + (14 if k % 4 == 2 else 0))
        if fill:
            for k, dd in enumerate((E_SNARE, E_SNARE, HI_TOM, HI_TOM, MID_TOM, MID_TOM, LO_TOM, LO_TOM)):
                note(dr, b + 2 + k * 0.25, 0.2, dd, vel - 16 + 3 * k)

    def throb(b, ch, vel=100, half=False):
        """The sixteenth bass: root, root, octave, root; half: eighths."""
        root = ch[0] + 12 if ch[0] < 36 else ch[0]
        if half:
            for k in range(8):
                note(bass, b + k * 0.5, 0.4, root + (12 if k % 4 == 3 else 0), vel - (0 if k % 2 == 0 else 14))
            return
        for k in range(16):
            p = (root, root, root + 12, root)[k % 4]
            note(bass, b + k * 0.25, 0.2, p, vel - (0 if k % 4 == 0 else 16) + (6 if k % 4 == 2 else 0))
        note(sub, b, 3.9, root - 12, vel - 20)

    def pad_bar(b, ch, vel=54, track=None):
        for p in ch[1]:
            note(track or pad, b, 4, p, vel)

    def arp_bar(b, ch, vel=52, octave=12, track=None):
        v = ch[1] + [ch[1][0] + 12]
        seq = (0, 1, 2, 3, 2, 1, 2, 3)
        for k in range(16):
            note(track or arp, b + k * 0.25, 0.2, v[seq[k % 8]] + octave, vel + (10 if k % 4 == 0 else 0))

    bar = 0
    # intro: the heartbeat alone, a sweep pad rising, crystal arpeggio, the bass creeping in on bar 3
    for i in range(4):
        b = (bar + i) * 4
        heartbeat(b, 84 + 6 * i)
        pad_bar(b, Em, 50 + 6 * i, sweep)
        arp_bar(b, Em, 40 + 6 * i, 24, crystal)
        if i >= 2:
            throb(b, Em, 80 + 8 * i, half=i == 2)
        if i == 3:
            for k in range(8):
                note(dr, b + 2 + k * 0.25, 0.2, (E_SNARE, E_SNARE, HI_TOM, HI_TOM, MID_TOM, MID_TOM, LO_TOM, LO_TOM)[k],
                     70 + 4 * k)
    note(gob, 0, 6, 52, 50)
    bar += 4

    def section_a(bar, vel_lead=98, counter=False):
        for i, ch in enumerate(A_PROG):
            b = (bar + i) * 4
            drive(b, 96, fill=i == 7)
            throb(b, ch, 104)
            pad_bar(b, ch, 50)
            if counter:
                arp_bar(b, ch, 48)
        play(lead, bar * 4, TUNE_A, vel_lead, 0.88)
        play(lead2, bar * 4, TUNE_A, 56, 0.6, -12)
        if counter:
            play(brass, bar * 4, COUNTER_A, 70, 0.95)
        note(dr, bar * 4, 0.5, CRASH, 92)

    section_a(bar)                                # A
    bar += 8
    for i, ch in enumerate(B_PROG):               # B: the lead climbs, square arpeggios, claps
        b = (bar + i) * 4
        drive(b, 100, fill=i == 7)
        throb(b, ch, 106)
        pad_bar(b, ch, 56)
        arp_bar(b, ch, 50)
        for q in (1.5, 3.5):                       # brass off-beat stabs
            for p in ch[1]:
                note(brass, b + q, 0.3, p + 12, 66)
    play(lead, bar * 4, TUNE_B, 100, 0.88)
    play(lead2, bar * 4, TUNE_B, 58, 0.6, -12)
    note(dr, bar * 4, 0.5, CRASH, 96)
    bar += 8
    for i, ch in enumerate(C_PROG):               # C: the breakdown, half-time heartbeat, kalimba and vibes
        b = (bar + i) * 4
        heartbeat(b, 92)
        note(dr, b + 2, 0.2, RIM, 70)
        for k in range(8):
            note(dr, b + k * 0.5, 0.1, SHAKER, 54 + (10 if k % 2 else 0))
        note(sub, b, 3.9, ch[0] - 12 if ch[0] >= 36 else ch[0], 92)
        note(bass, b, 1.5, ch[0] + (12 if ch[0] < 36 else 0), 90)
        note(bass, b + 2.5, 1.0, ch[0] + (12 if ch[0] < 36 else 0), 76)
        pad_bar(b, ch, 60)
        v = ch[1]
        for k, p in enumerate([v[0] + 12, v[2], v[1] + 12, v[2] + 12, v[0] + 24, v[2] + 12, v[1] + 12, v[2]]):
            note(kalimba, b + k * 0.5, 0.45, p, 66 + (10 if k % 4 == 0 else 0))
        if i % 2 == 1:
            note(gob, b + 1, 2.5, 48 + (i % 4) * 2, 46)
    play(vibes, bar * 4, CALL_C, 84, 0.95, 12)
    play(lead2, bar * 4, CALL_C, 48, 0.9)
    note(dr, bar * 4, 0.5, CRASH, 72)
    bar += 8
    section_a(bar, 102, counter=True)             # A': full, with a counter-line
    bar += 8
    for i, ch in enumerate(D_PROG):               # D: the climax, the tune an octave up
        b = (bar + i) * 4
        drive(b, 104, fill=i == 7)
        throb(b, ch, 108)
        pad_bar(b, ch, 60)
        arp_bar(b, ch, 54, 24, crystal)
        arp_bar(b, ch, 50)
        for q in (0, 1.5, 3):
            for p in ch[1]:
                note(brass, b + q, 0.4 if q else 0.8, p, 72)
    play(lead, bar * 4, TUNE_D, 104, 0.88)
    play(lead2, bar * 4, TUNE_D, 62, 0.7, -12)
    note(dr, bar * 4, 0.5, CRASH, 100)
    bar += 8
    for i in range(4):                            # outro: back down to the heartbeat
        b = (bar + i) * 4
        heartbeat(b, 96 - 4 * i)
        throb(b, Em, 96 - 8 * i, half=i >= 2)
        pad_bar(b, Em, 56 - 4 * i, sweep)
        arp_bar(b, Em, 46 - 4 * i, 24, crystal)
    note(dr, bar * 4, 0.5, CRASH, 84)
    play(vibes, bar * 4, mel("e5/2 b4/2 | g5/2 f#5/2 | e5/4 | r/4"), 70, 0.95, 12)
    bar += 4
    assert bar == 48
    return tracks, 132, bar


# the boss: E Phrygian
RIFF = mel("e2/.25 e2/.25 e3/.25 e2/.25 e2/.25 f2/.25 e2/.25 e3/.25 e2/.25 e2/.25 g2/.25 e2/.25 f2/.25 e2/.25 "
           "bb2/.25 a2/.25")
BOSS_LEAD_A = mel("e5/1.5 f5/.5 e5/1 b4/1 | g5/.75 f5/.25 e5/.5 d5/.5 e5/2 | e5/1.5 f5/.5 g5/1 bb5/1 | "
                  "a5/.75 g5/.25 f5/.5 g5/.5 e5/2 | b5/1.5 c6/.5 b5/1 f5/1 | g5/.75 a5/.25 bb5/.5 a5/.5 g5/1 f5/1 | "
                  "e5/.5 f5/.5 g5/.5 bb5/.5 b5/1 c6/1 | b5/2 r/2")
BOSS_LEAD_B = mel("e6/1 f6/1 e6/.5 d6/.5 c6/1 | b5/1 c6/.5 b5/.5 a5/1 f5/1 | g5/1 a5/1 bb5/1 c6/1 | "
                  "b5/3 r/1 | e6/1 f6/1 g6/1 f6/1 | e6/.5 d6/.5 c6/.5 b5/.5 a5/1 f5/1 | "
                  "e5/.5 f5/.5 g5/.5 a5/.5 bb5/.5 c6/.5 d6/.5 e6/.5 | f6/2 e6/2")
BOSS_CH = {"E": (40, [52, 59, 64]), "F": (41, [53, 57, 60]), "G": (43, [55, 58, 62]), "Bb": (46, [53, 58, 62]),
           "C": (36, [55, 60, 64]), "D": (38, [57, 62, 65])}


def boss():
    dr = kit_track(20)
    lead = Track(0, SAW, 92, 64, 40)
    lead2 = Track(1, BASS_LEAD, 72, 50, 35)
    bass = Track(2, SYNTH_BASS, 112, 64, 10)
    brass = Track(3, SYNTH_BRASS, 84, 70, 40)
    pad = Track(4, POLY_PAD, 60, 64, 70)
    arp = Track(5, SQUARE, 54, 92, 50)
    fx = Track(6, SCIFI, 56, 64, 80)
    tom = Track(7, MELO_TOM, 80, 40, 30)
    tracks = [dr, lead, lead2, bass, brass, pad, arp, fx, tom]

    def hits(b, vel=96, fill=False, intense=True):
        for q in range(4):
            note(dr, b + q, 0.2, KICK, vel + 4)
            if intense:
                note(dr, b + q + 0.5, 0.2, KICK, vel - 30)
        for q in (1, 3):
            note(dr, b + q, 0.2, E_SNARE, vel)
            note(dr, b + q, 0.2, CLAP, vel - 16)
        for k in range(16):
            note(dr, b + k * 0.25, 0.1, CLOSED, vel - 36 + (12 if k % 2 == 0 else 0))
        if fill:
            for k, dd in enumerate((HI_TOM, HI_TOM, HI_TOM, MID_TOM, MID_TOM, MID_TOM, LO_TOM, LO_TOM)):
                note(dr, b + 2 + k * 0.25, 0.2, dd, vel - 10 + 2 * k)

    def stabs(b, chords, vel=80):
        for k, (q, name) in enumerate(chords):
            for p in BOSS_CH[name][1]:
                note(brass, b + q, 0.35, p + 12, vel)

    bar = 0
    for i in range(4):   # intro: toms and the riff rising in, the fx swelling
        b = i * 4
        for k in range(8):
            note(tom, b + k * 0.5, 0.3, 45 + (k % 4 == 3) * 5 + 2 * i, 70 + 6 * i)
            note(dr, b + k * 0.5, 0.2, LO_TOM if k % 2 == 0 else MID_TOM, 60 + 8 * i)
        if i >= 2:
            play(bass, b, RIFF, 90 + 8 * i, 0.85)
            play(bass, b + 2, RIFF[:8], 90 + 8 * i, 0.85)
        note(pad, b, 4, 52, 50 + 8 * i)
        note(pad, b, 4, 53 if i % 2 else 59, 46 + 8 * i)
        if i == 3:
            for k in range(8):
                note(dr, b + 2 + k * 0.25, 0.2, E_SNARE, 70 + 5 * k)
    note(fx, 0, 8, 40, 60)
    bar = 4
    progA = ["E", "E", "F", "E", "E", "G", "F", "E"]
    for i, name in enumerate(progA):
        b = (bar + i) * 4
        hits(b, 100, fill=i == 7)
        shift = {"F": 1, "G": 3}.get(name, 0)
        play(bass, b, RIFF, 108, 0.85, shift)
        play(bass, b + 2, RIFF[:8], 104, 0.85, shift)
        stabs(b, [(0, name), (1.5, name), (2.75, "F" if name == "E" else "E"), (3.5, name)])
        for p in BOSS_CH[name][1]:
            note(pad, b, 4, p, 56)
    play(lead, bar * 4, BOSS_LEAD_A, 102, 0.9)
    play(lead2, bar * 4, BOSS_LEAD_A, 70, 0.8, -12)
    note(dr, bar * 4, 0.5, CRASH, 100)
    bar += 8
    progB = ["C", "D", "Bb", "E", "C", "D", "Bb", "E"]
    for i, name in enumerate(progB):
        b = (bar + i) * 4
        hits(b, 104, fill=i in (3, 7))
        root = BOSS_CH[name][0]
        for k in range(16):
            p = (root, root + 12, root, root + 12)[k % 4]
            note(bass, b + k * 0.25, 0.2, p, 110 - (0 if k % 4 == 0 else 14))
        stabs(b, [(0, name), (0.75, name), (1.5, name), (3, name)], 86)
        v = BOSS_CH[name][1] + [BOSS_CH[name][1][0] + 12]
        for k in range(16):
            note(arp, b + k * 0.25, 0.2, v[(0, 1, 2, 3, 2, 1, 2, 3)[k % 8]] + 24, 52 + (10 if k % 4 == 0 else 0))
        if i % 4 == 0:
            note(dr, b, 0.5, CRASH, 96)
    play(lead, bar * 4, BOSS_LEAD_B, 106, 0.9)
    play(lead2, bar * 4, BOSS_LEAD_B, 72, 0.8, -12)
    bar += 8
    for i in range(4):   # the turn: everything on the riff, toms rolling into the top
        b = (bar + i) * 4
        hits(b, 104, fill=i == 3)
        play(bass, b, RIFF, 110, 0.85)
        play(bass, b + 2, RIFF[:8], 106, 0.85)
        for k in range(8):
            note(tom, b + k * 0.5, 0.3, 52 - (k % 4) * 2, 84)
        stabs(b, [(0, "E"), (0.75, "F"), (1.5, "E"), (2.5, "F"), (3, "E")], 90)
    play(lead, bar * 4, mel("e6/.5 f6/.5 e6/1 b5/2 | c6/.5 b5/.5 a5/.5 f5/.5 e5/2 | "
                            "e6/.5 f6/.5 g6/1 f6/1 e6/1 | bb5/1 b5/1 c6/1 f6/1"), 104, 0.9)
    bar += 4
    assert bar == 24
    return tracks, 150, bar


# the shop: C major, a relaxed quirky groove
S_CH = {"Dm7": (38, [53, 57, 60, 64]), "G7": (43, [53, 59, 62, 65]), "Cmaj7": (36, [52, 55, 59, 64]),
        "Am7": (45, [55, 60, 64, 67]), "Fmaj7": (41, [52, 57, 60, 64]), "E7": (40, [56, 59, 62, 64]),
        "D7": (38, [54, 57, 60, 64]), "C": (36, [52, 55, 60, 64])}
SHOP_PROG = ["Dm7", "G7", "Cmaj7", "Am7", "Fmaj7", "E7", "Am7", "D7", "Dm7", "G7", "C", "C"]
SHOP_TUNE = mel("a5/.5 r/.5 f5/.5 a5/.5 c6/.75 b5/.25 a5/1 | g5/.5 r/.5 b5/.5 d6/.5 f6/1 e6/.5 d6/.5 | "
                "e6/1.5 g5/.5 b5/1 c6/1 | a5/.5 c6/.5 e6/.5 c6/.5 a5/1 r/1 | "
                "c6/.5 r/.5 a5/.5 c6/.5 e6/.75 d6/.25 c6/1 | b5/.5 g#5/.5 b5/.5 d6/.5 e6/1 d6/1 | "
                "c6/.5 a5/.5 e5/.5 a5/.5 c6/.5 e6/.5 g6/1 | f#6/.75 e6/.25 d6/.5 c6/.5 a5/1 f#5/1 | "
                "f5/.5 a5/.5 d6/.5 c6/.5 a5/.5 f5/.5 d5/1 | g5/.5 b5/.5 d6/.5 f6/.5 e6/.5 d6/.5 b5/1 | "
                "c6/.5 e6/.5 g6/.5 e6/.5 c6/1 g5/1 | e5/.5 g5/.5 c6/1.5 r/1.5")
SHOP_BASS = [(0, 1.0, 0), (1.5, 0.5, 7), (2, 1.0, 12), (3, 0.5, 10), (3.5, 0.5, 7)]


def shop():
    dr = Track(9, 0, 96, 64, 30)
    bass = Track(0, FRETLESS, 104, 60, 20)
    ep = Track(1, EPIANO, 74, 50, 55)
    kal = Track(2, KALIMBA, 88, 76, 60)
    mar = Track(3, MARIMBA, 70, 40, 50)
    vib = Track(4, VIBES, 54, 90, 70)
    pad = Track(5, WARM_PAD, 46, 64, 80)
    pizz = Track(6, PIZZ, 60, 30, 45)
    tracks = [dr, bass, ep, kal, mar, vib, pad, pizz]
    for i, name in enumerate(SHOP_PROG):
        b = i * 4
        root, v = S_CH[name]
        for q, ln, iv in SHOP_BASS:   # a bouncy fretless line: root, fifth, octave, seventh, fifth
            if iv == 10:   # the seventh: major on a maj7, a sixth on the plain triad
                iv = 11 if "maj" in name else 9 if name == "C" else 10
            p = root + iv
            note(bass, b + q, ln * 0.85, p, 96 - (0 if q % 1 == 0 else 14))
        for q in (0.5, 1.5, 2.5, 3.5):   # Rhodes on the off-beats
            for p in v:
                note(ep, b + q, 0.35, p + 12, 62 + (6 if q == 1.5 else 0))
        for p in v:
            note(pad, b, 4, p, 40)
        for k, p in enumerate((v[0] + 24, v[2] + 12, v[1] + 24, v[3] + 12)):   # pizzicato plinks, a quirky skip
            note(pizz, b + (0.0, 0.75, 2.0, 3.25)[k], 0.3, p, 48)
        # the kit: kick on 1 and the 'and' of 2, rim on 2 and 4, shaker eighths, a woodblock tick
        for q in (0, 1.5, 2.5):
            note(dr, b + q, 0.2, KICK, 88 if q == 0 else 72)
        for q in (1, 3):
            note(dr, b + q, 0.2, RIM, 80)
        for k in range(8):
            note(dr, b + k * 0.5, 0.1, SHAKER, 50 + (12 if k % 2 else 0))
        note(dr, b + 3.75, 0.1, WOODBLOCK, 62)
        if i % 4 == 3:
            note(dr, b + 3.5, 0.1, COWBELL, 58)
    play(kal, 0, SHOP_TUNE, 96, 0.8)
    play(mar, 0, SHOP_TUNE, 60, 0.6, -12)
    for i in (2, 6, 10):   # vibraphone answers
        play(vib, i * 4 + 2, [(0, 0.5, 79), (0.5, 0.5, 76), (1, 1, 72)], 56, 0.95)
    return tracks, 96, len(SHOP_PROG)


if __name__ == "__main__":
    for name, fn in (("biosurge_theme", theme), ("biosurge_boss", boss), ("biosurge_shop", shop)):
        tracks, bpm, bars = fn()
        secs = render_loop(tracks, bpm, bars, OUT + name + ".ogg", gain=0.5, rms_db=-17.0)
        print(f"wrote {name}.ogg ({secs:.1f} s loop)")
