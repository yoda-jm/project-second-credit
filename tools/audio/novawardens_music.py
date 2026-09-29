#!/usr/bin/env python3
"""Game 25 (Nova Wardens) music, written as code and rendered with FluidSynth. Licence CC BY-SA 4.0. Our own: no
quotation of the arcade game (which had no music beyond its march beat), no existing film or game theme.
- novawardens_ambient: a dark night-sky pad loop that sits under the game's march beat (the step_0..3 pulses in
  tools/audio/novawardens_sfx.py, G2 - Eb2 - C2 - G1) without fighting it: no drums, no bass pulse, nothing on a
  beat grid the ear could lock to; everything above 100 Hz except one soft pedal. C minor, 60 bpm, 18 bars (72 s).
  Layers: a warm pad on long chords (Cm9, Abmaj7#11, Fm9, Gsus4 -> G, Ebmaj7, Dbmaj7 (a Phrygian shadow), Cm), slow
  strings doubling the upper voices, a sweep pad fading in and out, a low contrabass pedal on C and G, sparse
  celesta and vibraphone notes like distant stars (a small rising figure, its answer falling), a brightness FX pad
  for the shimmer. No voices: no choir or halo patches.
Usage: python3 tools/audio/novawardens_music.py
-> godot/games/novawardens/audio/music/novawardens_ambient.ogg (+ .mid)."""
import os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from midi_render import Track, render_loop

OUT = "godot/games/novawardens/audio/music/"
CELESTA, VIBES, CONTRABASS, STRINGS_SLOW, WARM_PAD, POLY_PAD, SWEEP_PAD, BRIGHTNESS = 8, 11, 43, 49, 89, 90, 95, 100

BPM, BARS = 60, 18


def note(track, beat, length, pitch, vel):
    track.note(beat, max(0.05, length - 0.05), pitch, max(1, min(127, int(vel))))


# the progression: (bars, pedal, voicing), C minor
PROG = [(2, 36, [55, 58, 62, 63, 67]),        # Cm9: G Bb D Eb G  (over C)
        (2, 32, [56, 60, 63, 67, 74]),        # Abmaj7#11-ish: Ab C Eb G D
        (2, 29, [56, 60, 63, 67, 68]),        # Fm9: Ab C Eb G Ab
        (1, 31, [55, 60, 62, 67]),            # Gsus4
        (1, 31, [55, 59, 62, 67]),            # G
        (2, 39, [55, 58, 62, 63, 70]),        # Ebmaj7: Eb G Bb D
        (2, 37, [53, 56, 60, 65, 72]),        # Dbmaj7 (the Phrygian shadow)
        (2, 32, [56, 60, 63, 67, 72]),        # Ab
        (2, 31, [55, 59, 62, 65, 67]),        # G7 (back to the top)
        (2, 36, [55, 58, 62, 63, 67])]        # Cm9
assert sum(b for b, _, _ in PROG) == BARS

# stars: (beat, pitch, instrument 0 celesta / 1 vibes); a rising figure and its falling answer, sparse, off the grid
STARS = [(1.75, 79, 0), (2.9, 84, 0), (4.6, 86, 0), (9.3, 75, 1), (10.1, 79, 1), (13.7, 87, 0), (15.2, 84, 0),
         (17.8, 80, 0), (21.4, 91, 0), (22.3, 86, 0), (26.6, 79, 1), (27.5, 82, 1), (28.4, 86, 1), (33.1, 87, 0),
         (34.9, 82, 0), (38.3, 89, 0), (39.1, 84, 0), (41.7, 77, 1), (45.2, 84, 0), (46.0, 86, 0), (46.8, 91, 0),
         (50.6, 89, 1), (53.3, 80, 0), (54.1, 84, 0), (58.7, 87, 0), (59.6, 83, 0), (62.2, 86, 1), (65.9, 79, 0),
         (66.8, 84, 0), (67.5, 87, 0)]


def song():
    pad = Track(0, WARM_PAD, 92, 64, 90)
    strings = Track(1, STRINGS_SLOW, 64, 50, 100)
    sweep = Track(2, SWEEP_PAD, 58, 80, 110)
    bass = Track(3, CONTRABASS, 70, 64, 70)
    cel = Track(4, CELESTA, 70, 30, 120)
    vib = Track(5, VIBES, 60, 98, 120)
    shine = Track(6, BRIGHTNESS, 44, 64, 127)
    poly = Track(7, POLY_PAD, 50, 64, 100)
    bar = 0
    rnd = random.Random(25)
    for bars, pedal, v in PROG:
        b, L = bar * 4, bars * 4
        for k, p in enumerate(v):   # the pad, voices entering a little apart (a slow bloom)
            note(pad, b + 0.15 * k, L - 0.15 * k + 0.3, p, 58 + 4 * k)
        for p in v[-3:]:
            note(strings, b + 0.5, L - 0.2, p + 12 if p < 70 else p, 46)
        note(bass, b, L + 0.2, pedal if pedal >= 28 else pedal + 12, 60)
        note(bass, b + L / 2, L / 2 + 0.2, pedal + 7 if pedal + 7 >= 28 else pedal + 19, 44)
        if bar % 4 == 0:   # the sweep pad breathes every four bars
            note(sweep, b + 1, 7, v[1] + 12, 50)
            note(sweep, b + 1, 7, v[3] + 12, 44)
        note(poly, b + 2, L - 1.5, v[0] - 12, 34)
        if bar in (6, 12):
            note(shine, b, 8, v[-1] + 12, 40)
        bar += bars
    for beat, p, ins in STARS:
        note(vib if ins else cel, beat, 2.5, p, 44 + rnd.randint(0, 14))
    return [pad, strings, sweep, bass, cel, vib, shine, poly]


if __name__ == "__main__":
    secs = render_loop(song(), BPM, BARS, OUT + "novawardens_ambient.ogg", gain=0.6, rms_db=-22.0)
    print(f"wrote novawardens_ambient.ogg ({secs:.1f} s loop)")
