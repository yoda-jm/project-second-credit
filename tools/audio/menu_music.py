#!/usr/bin/env python3
"""Launcher music: a calm, spacious piece (A minor to C major, 76 BPM), written as code and rendered with
FluidSynth. Usage: python3 tools/audio/menu_music.py  -> godot/core/audio/menu_theme.ogg (CC BY-SA 4.0)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 76, 16
pad = Track(0, 91, 72, 40, 90)      # space voice pad
strings = Track(1, 49, 60, 88, 80)  # slow strings
bell = Track(2, 14, 70, 70, 100)    # tubular bells
bass = Track(3, 32, 80, 64, 40)     # acoustic bass
harp = Track(4, 46, 58, 100, 90)    # harp arpeggios

prog = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]  # Am F C G
for rep in range(2):
    for i, (root, notes) in enumerate(prog):
        b = rep * 32 + i * 8
        for n in notes:
            pad.note(b, 8, n, 55)
            strings.note(b, 8, n + 12, 40 + 10 * rep)
        bass.note(b, 3.5, root - 12, 70)
        bass.note(b + 4, 3.5, root - 12 + 7, 60)
        seq = [notes[0], notes[1], notes[2], notes[1] + 12, notes[2] + 12, notes[1] + 12]
        for k in range(24):
            harp.note(b + k / 3.0, 0.3, seq[k % len(seq)] + 12, 45 + (10 if k % 6 == 0 else 0))
        if rep == 1:
            bell.note(b, 4, notes[2] + 24, 50)
            bell.note(b + 4, 4, notes[0] + 24, 42)
secs = render_loop([pad, strings, bell, bass, harp], BPM, BARS, "godot/core/audio/menu_theme.ogg", gain=0.7)
print(f"wrote godot/core/audio/menu_theme.ogg ({secs:.1f} s loop)")
