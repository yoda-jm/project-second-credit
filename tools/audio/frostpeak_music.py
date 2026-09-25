#!/usr/bin/env python3
"""Game 5 theme: an original, bright sporting march in D major (brass, strings, timpani, glockenspiel), written as
code and rendered with FluidSynth. Usage: python3 tools/audio/frostpeak_music.py
-> godot/games/frostpeak/audio/music/frostpeak_theme.ogg. Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 112, 16
brass = Track(0, 61, 86, 64, 45)   # brass section
strings = Track(1, 48, 76, 56, 55)  # strings
low = Track(2, 58, 88, 64, 30)     # tuba
glock = Track(3, 9, 60, 72, 50)
drum = Track(9, 0, 80, 64, 40)
# D  G  A  D  |  Bm G  A  D   (a bar each), twice
prog = [(50, [62, 66, 69]), (43, [59, 62, 67]), (45, [61, 64, 69]), (50, [62, 66, 69]),
        (47, [59, 62, 66]), (43, [59, 62, 67]), (45, [61, 64, 69]), (50, [62, 66, 69])]
theme = [(0, 1.5, 74), (1.5, .5, 76), (2, 1, 78), (3, 1, 81), (4, 2, 83), (6, 1, 81), (7, 1, 78),
         (8, 1.5, 76), (9.5, .5, 78), (10, 1, 79), (11, 1, 76), (12, 3, 73), (15, 1, 69),
         (16, 1.5, 71), (17.5, .5, 74), (18, 1, 78), (19, 1, 79), (20, 2, 78), (22, 1, 76), (23, 1, 74),
         (24, 1, 76), (25, 1, 78), (26, 1, 76), (27, 1, 73), (28, 4, 74)]
for rep in range(2):
    base = rep * 32
    for i, (root, notes) in enumerate(prog):
        b = base + i * 4
        low.note(b, 0.9, root - 12, 92)
        low.note(b + 2, 0.9, root - 5, 80)
        for nn in notes:
            strings.note(b, 3.9, nn - 12, 58 + rep * 8)
        drum.note(b, 0.3, 47, 70)  # timpani-like toms on the downbeat
        for k in range(4):
            drum.note(b + k, 0.1, 38, 50 if k % 2 else 35)
            drum.note(b + k + 0.5, 0.1, 42, 30)
    for beat, length, pitch in theme:
        brass.note(base + beat, length * 0.9, pitch - (12 if rep == 0 else 0), 84 if rep else 74)
        if rep == 1 and length >= 1:
            glock.note(base + beat, 0.4, pitch + 12, 45)
secs = render_loop([brass, strings, low, glock, drum], BPM, BARS, "godot/games/frostpeak/audio/music/frostpeak_theme.ogg", gain=0.6)
print(f"wrote frostpeak_theme.ogg ({secs:.1f} s loop)")
