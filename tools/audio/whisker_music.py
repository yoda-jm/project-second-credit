#!/usr/bin/env python3
"""Game 4 theme: an original late-night alley swing, a 12-bar blues in F (tenor sax, piano comping, walking bass,
brushed drums), written as code and rendered with FluidSynth. Usage: python3 tools/audio/whisker_music.py
-> godot/games/whisker/audio/music/alley_theme.ogg. Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 128, 24
SW = 2 / 3  # swung eighths: the off-beat lands two thirds into the beat
sax = Track(0, 66, 84, 70, 50)    # tenor sax
pno = Track(1, 0, 66, 54, 45)     # piano
bass = Track(2, 32, 96, 64, 25)   # acoustic bass
drum = Track(9, 0, 70, 64, 30)
# 12-bar blues in F: F7 Bb7 F7 F7 | Bb7 Bb7 F7 F7 | C7 Bb7 F7 C7
blues = [41, 46, 41, 41, 46, 46, 41, 41, 48, 46, 41, 48]
chord = {41: [57, 63, 64 + 1], 46: [56, 62, 63 + 1], 48: [58, 64, 67]}  # shell voicings (3rd, 7th, 9th/5th)
walk = {41: [41, 45, 48, 50], 46: [46, 50, 53, 51], 48: [48, 52, 55, 53]}
# the head: a lazy, bluesy line (bar, beat, length, pitch), 12 bars
head = [(0, 0, 1, 72), (0, 1 + SW, .6, 75), (0, 2.5, 1.5, 77), (1, 0.5, 1, 80), (1, 2, 2, 77),
        (2, 0, .5, 75), (2, SW, .5, 72), (2, 1 + SW, 1, 69), (2, 3, 1, 72), (3, 0, 3, 70),
        (4, 0, 1, 77), (4, 1 + SW, .6, 80), (4, 2.5, 1.5, 82), (5, 1, 2, 80), (5, 3, 1, 77),
        (6, 0, .5, 75), (6, SW, .5, 72), (6, 1 + SW, 1, 70), (6, 3, 1, 69), (7, 0, 3, 72),
        (8, 0, 1.5, 79), (8, 2, 1, 77), (8, 3, 1, 75), (9, 0, 1.5, 77), (9, 2, 1, 75), (9, 3, 1, 72),
        (10, 0, .5, 69), (10, SW, .5, 72), (10, 1 + SW, 1, 70), (10, 3, 1, 69), (11, 0, 2, 67), (11, 2.5, 1, 72)]
for chorus in range(2):
    for i, root in enumerate(blues):
        b = (chorus * 12 + i) * 4
        for k, p in enumerate(walk[root]):
            bass.note(b + k, 0.9, p - 12, 92 if k == 0 else 80)
        for k in (1, 3):  # piano: short stabs on 2 and 4, a swung push before 3
            for nn in chord[root]:
                pno.note(b + k, 0.25, nn, 60)
        for nn in chord[root]:
            pno.note(b + 1 + SW, 0.2, nn, 48)
        for k in range(4):  # brushes: ride on the beats and the swung off-beat, hi-hat foot on 2 and 4
            drum.note(b + k, 0.2, 51, 58 if k % 2 == 0 else 50)
            drum.note(b + k + SW, 0.1, 51, 40)
            if k % 2 == 1:
                drum.note(b + k, 0.1, 44, 55)
            if k == 0 and i % 4 == 0:
                drum.note(b, 0.2, 36, 60)
    for bar, beat, length, pitch in head:
        sax.note((chorus * 12 + bar) * 4 + beat, length * 0.9, pitch - 12 + (12 if chorus == 1 and bar >= 8 else 0),
                 82 if chorus == 1 else 74)
secs = render_loop([sax, pno, bass, drum], BPM, BARS, "godot/games/whisker/audio/music/alley_theme.ogg", gain=0.6)
print(f"wrote alley_theme.ogg ({secs:.1f} s loop)")
