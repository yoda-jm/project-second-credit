#!/usr/bin/env python3
"""Game 6 theme: an original, jaunty field march in E minor (brass, piccolo, snare, bass drum, tuba), written as
code and rendered with FluidSynth. Usage: python3 tools/audio/boots_music.py
-> godot/games/boots/audio/music/boots_theme.ogg. Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 120, 16
horn = Track(0, 60, 82, 58, 40)    # french horns
pic = Track(1, 72, 70, 76, 45)     # piccolo
tuba = Track(2, 58, 90, 64, 25)
drum = Track(9, 0, 88, 64, 30)
prog = [40, 40, 45, 47, 40, 43, 45, 47]  # Em Em Am B | Em G Am B (roots)
theme = [(0, .75, 64), (.75, .25, 66), (1, 1, 67), (2, .75, 71), (2.75, .25, 69), (3, 1, 67),
         (4, .75, 69), (4.75, .25, 67), (5, 1, 66), (6, 2, 64),
         (8, .75, 72), (8.75, .25, 71), (9, 1, 69), (10, .75, 67), (10.75, .25, 66), (11, 1, 64),
         (12, 1, 66), (13, .5, 67), (13.5, .5, 69), (14, 2, 71)]
for rep in range(2):
    base = rep * 32
    for i, root in enumerate(prog):
        b = base + i * 4
        tuba.note(b, 0.9, root - 12 + 12, 92)
        tuba.note(b + 2, 0.9, root - 5, 84)
        for k in range(4):  # snare: the march rudiment, a roll into every other bar
            drum.note(b + k, 0.1, 38, 80 if k % 2 else 60)
            drum.note(b + k + 0.5, 0.1, 38, 45)
            if k == 3 and i % 2 == 1:
                for r in range(4):
                    drum.note(b + k + r * 0.125, 0.06, 38, 50 + r * 8)
        drum.note(b, 0.2, 36, 90)
        drum.note(b + 2, 0.2, 36, 80)
    for beat, length, pitch in theme:
        horn.note(base + beat, length * 0.9, pitch, 82 if rep else 74)
        if rep == 1:
            pic.note(base + beat + 16, length * 0.9, pitch + 12, 60)  # the piccolo answers in the second half
secs = render_loop([horn, pic, tuba, drum], BPM, BARS, "godot/games/boots/audio/music/boots_theme.ogg", gain=0.6)
print(f"wrote boots_theme.ogg ({secs:.1f} s loop)")
