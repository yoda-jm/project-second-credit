#!/usr/bin/env python3
"""Game 7 theme: an original synthwave track in A minor (square lead, synth bass, pads, drum machine), written as
code and rendered with FluidSynth. Usage: python3 tools/audio/knuckles_music.py
-> godot/games/knuckles/audio/music/knuckles_theme.ogg. Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 118, 16
lead = Track(0, 80, 80, 64, 50)   # square lead
bass = Track(1, 38, 96, 64, 25)   # synth bass
pad = Track(2, 89, 62, 64, 70)    # warm pad
drum = Track(9, 0, 92, 64, 20)
prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]  # Am F C G
riff = [(0, .5, 69), (.5, .5, 72), (1, .5, 76), (1.5, 1, 74), (2.5, .5, 72), (3, 1, 69),
        (4, .5, 65), (4.5, .5, 69), (5, .5, 72), (5.5, 1, 74), (6.5, .5, 72), (7, 1, 69),
        (8, .5, 67), (8.5, .5, 72), (9, .5, 76), (9.5, 1, 79), (10.5, .5, 76), (11, 1, 74),
        (12, .5, 71), (12.5, .5, 74), (13, 1, 79), (14, 2, 76)]
for rep in range(4):
    base = rep * 16
    for i, (root, notes) in enumerate(prog):
        b = base + i * 4
        for k in range(8):  # driving eighth-note bass
            bass.note(b + k * 0.5, 0.4, root - 12 + (12 if k % 4 == 3 else 0), 90 if k % 2 == 0 else 72)
        for nn in notes:
            pad.note(b, 3.9, nn, 55)
        for k in range(4):
            drum.note(b + k, 0.2, 36 if k % 2 == 0 else 38, 100 if k % 2 == 0 else 90)
            drum.note(b + k + 0.5, 0.1, 42, 55)
    if rep >= 1:
        for beat, length, pitch in riff:
            lead.note(base + beat, length * 0.9, pitch, 80 if rep >= 2 else 70)
secs = render_loop([lead, bass, pad, drum], BPM, BARS, "godot/games/knuckles/audio/music/knuckles_theme.ogg", gain=0.6)
print(f"wrote knuckles_theme.ogg ({secs:.1f} s loop)")
