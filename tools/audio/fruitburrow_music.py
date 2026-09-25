#!/usr/bin/env python3
"""Game 3 theme: an original, bouncy garden tune in F major (marimba, clarinet, tuba, glockenspiel, light drums),
written as code and rendered with FluidSynth. Usage: python3 tools/audio/fruitburrow_music.py
-> godot/games/fruitburrow/audio/music/garden_theme.ogg. Licence CC BY-SA 4.0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

BPM, BARS = 132, 16
mar = Track(0, 12, 88, 58, 35)    # marimba (lead)
cla = Track(1, 71, 70, 76, 45)    # clarinet (answers)
tuba = Track(2, 58, 92, 64, 20)   # tuba
glock = Track(3, 9, 55, 44, 50)   # glockenspiel sparkles
drum = Track(9, 0, 80, 64, 25)
# F  Dm  Bb  C  |  F  Am  Bb C  (two beats each in the second half)
prog = [(41, [65, 69, 72]), (38, [62, 65, 69]), (46, [58, 62, 65]), (36, [60, 64, 67]),
        (41, [65, 69, 72]), (45, [57, 60, 64]), (46, [58, 62, 65]), (36, [60, 64, 67])]
# the tune: short hops and a bouncing turn (beats, length, pitch), 8 bars
tune = [(0, .5, 72), (.5, .5, 74), (1, 1, 77), (2, .5, 76), (2.5, .5, 74), (3, 1, 72),
        (4, .5, 69), (4.5, .5, 72), (5, 1, 74), (6, 1.5, 72), (7.5, .5, 69),
        (8, .5, 70), (8.5, .5, 72), (9, 1, 74), (10, .5, 72), (10.5, .5, 70), (11, 1, 69),
        (12, .5, 67), (12.5, .5, 69), (13, .5, 70), (13.5, .5, 72), (14, 2, 67),
        (16, .5, 72), (16.5, .5, 74), (17, 1, 77), (18, .5, 79), (18.5, .5, 77), (19, 1, 76),
        (20, .5, 72), (20.5, .5, 76), (21, 1, 79), (22, 1.5, 77), (23.5, .5, 76),
        (24, .5, 74), (24.5, .5, 72), (25, 1, 70), (26, .5, 72), (26.5, .5, 74), (27, 1, 76),
        (28, 1, 77), (29, .5, 72), (29.5, .5, 69), (30, 2, 65)]
answer = [(3.5, .5, 65), (7, .5, 64), (11.5, .5, 62), (15, 1, 64), (19.5, .5, 69), (23, .5, 72), (27.5, .5, 67), (31, 1, 60)]
for rep in range(2):
    base = rep * 32
    for i, (root, notes) in enumerate(prog):
        b = base + i * 4
        tuba.note(b, 0.9, root if root < 40 else root - 12, 96)  # oom (kept in the tuba range)
        tuba.note(b + 2, 0.9, root - 5, 84)                                          # pah
        for k in range(4):
            drum.note(b + k, 0.15, 36 if k % 2 == 0 else 38, 80 if k % 2 == 0 else 60)
            drum.note(b + k + 0.5, 0.1, 42, 40)
        for k in (1, 3):  # off-beat marimba chords
            for nn in notes:
                mar.note(b + k + 0.5, 0.3, nn - 12, 52)
    for beat, length, pitch in tune:
        mar.note(base + beat, length * 0.9, pitch, 86 if rep == 1 else 78)
    for beat, length, pitch in answer:
        cla.note(base + beat, length * 0.95, pitch, 70)
    if rep == 1:
        for beat, length, pitch in tune[::3]:
            glock.note(base + beat, 0.3, pitch + 12, 50)
secs = render_loop([mar, cla, tuba, glock, drum], BPM, BARS, "godot/games/fruitburrow/audio/music/garden_theme.ogg", gain=0.6)
print(f"wrote garden_theme.ogg ({secs:.1f} s loop)")
