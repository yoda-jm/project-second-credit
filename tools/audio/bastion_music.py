#!/usr/bin/env python3
"""Game 2 theme: an original sea shanty in D Dorian (accordion, fiddle, pizzicato bass, drums), written as code
and rendered with FluidSynth. Usage: python3 tools/audio/bastion_music.py -> godot/games/bastion/audio/music/
Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 112, 16
acc = Track(0, 21, 78, 50, 40)     # accordion
fid = Track(1, 40, 82, 80, 50)     # violin
bass = Track(2, 45, 90, 64, 30)    # pizzicato strings
drum = Track(9, 0, 90, 64, 30)
chords = [(38, [62, 65, 69]), (36, [60, 64, 67]), (38, [62, 65, 69]), (45, [57, 61, 64])]  # Dm C Dm A
tune = [(0, 1, 74), (1, .5, 72), (1.5, .5, 71), (2, 1, 69), (3, 1, 67), (4, 1.5, 65), (5.5, .5, 67), (6, 2, 69),
        (8, 1, 72), (9, .5, 71), (9.5, .5, 69), (10, 1, 67), (11, 1, 64), (12, 3, 69), (15, 1, 73),
        (16, 1, 74), (17, .5, 76), (17.5, .5, 77), (18, 1, 76), (19, 1, 74), (20, 1.5, 72), (21.5, .5, 71), (22, 2, 69),
        (24, 1, 65), (25, 1, 67), (26, 1, 69), (27, 1, 64), (28, 4, 62)]
for rep in range(2):
    base = rep * 32
    for i, (root, notes) in enumerate(chords * 2):
        b = base + i * 4
        for k in range(4):  # oom-pah on the accordion
            acc.note(b + k, 0.25, root, 70)
            for n in notes:
                acc.note(b + k + 0.5, 0.35, n, 58)
        bass.note(b, 0.8, root - 12 + 12, 92)
        bass.note(b + 2, 0.8, root - 12 + 19, 80)
        for k in range(4):
            drum.note(b + k, 0.2, 36 if k % 2 == 0 else 45, 90 if k % 2 == 0 else 70)
            if rep == 1:
                drum.note(b + k + 0.5, 0.1, 42, 45)
    for beat, length, pitch in tune:
        fid.note(base + beat, length * 0.95, pitch + (0 if rep == 0 else 12 * 0), 84 if rep == 1 else 72)
secs = render_loop([acc, fid, bass, drum], BPM, BARS, "godot/games/bastion/audio/music/coast_theme.ogg", gain=0.6)
print(f"wrote coast_theme.ogg ({secs:.1f} s loop)")
