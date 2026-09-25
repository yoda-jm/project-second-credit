#!/usr/bin/env python3
"""In-game music for game 1: an original piece written as code (MIDI), rendered with FluidSynth and the
FluidR3_GM SoundFont (MIT), made loop-seamless and encoded to Ogg Vorbis.

Usage: python3 tools/audio/glimmerdeep_music.py [out_dir]   (default: godot/games/glimmerdeep/audio/music)
Needs fluidsynth, oggenc and the FluidR3_GM.sf2 SoundFont. Licence of the music: CC BY-SA 4.0.
"""
import os, struct, subprocess, sys, tempfile, wave
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "godot/games/glimmerdeep/audio/music"
SF2 = next(p for p in ["/usr/share/sounds/sf2/FluidR3_GM.sf2", "/usr/share/soundfonts/FluidR3_GM.sf2"] if os.path.exists(p))
TPB = 480           # ticks per beat
BPM = 96
BARS = 16
SR = 44100


class Track:
    def __init__(self, channel, program, volume=100, pan=64):
        self.ch = channel
        self.events = []  # (tick, bytes)
        if channel != 9:
            self.events.append((0, bytes([0xC0 | channel, program])))
        self.events.append((0, bytes([0xB0 | channel, 7, volume])))
        self.events.append((0, bytes([0xB0 | channel, 10, pan])))
        self.events.append((0, bytes([0xB0 | channel, 91, 50])))  # reverb send

    def note(self, beat, length, pitch, vel=90):
        on = int(beat * TPB)
        off = int((beat + length) * TPB) - 1
        self.events.append((on, bytes([0x90 | self.ch, pitch, vel])))
        self.events.append((off, bytes([0x80 | self.ch, pitch, 0])))


def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, 0x80 | (n & 0x7F))
        n >>= 7
    return bytes(out)


def write_midi(path, tracks):
    chunks = []
    tempo = [(0, bytes([0xFF, 0x51, 0x03]) + int(60_000_000 / BPM).to_bytes(3, "big"))]
    for evs in [tempo] + [t.events for t in tracks]:
        data = b""
        last = 0
        for tick, ev in sorted(evs, key=lambda e: (e[0], e[1][0] & 0xF0 == 0x90)):
            data += vlq(tick - last) + ev
            last = tick
        data += vlq(0) + b"\xFF\x2F\x00"
        chunks.append(b"MTrk" + struct.pack(">I", len(data)) + data)
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), TPB) + b"".join(chunks))


# ---- the piece: D minor, i - VI - III - VII, two bars each, played twice with a build-up
D, F, A, Bb, C, E, G = 62, 65, 69, 70, 72, 64, 67
chords = [(50, [62, 65, 69]), (46, [58, 62, 65]), (53, [60, 65, 69]), (48, [60, 64, 67])]  # Dm Bb F C

pad = Track(0, 89, 70, 50)        # warm pad
bass = Track(1, 38, 95, 64)       # synth bass
arp = Track(2, 8, 60, 90)         # celesta arpeggio
lead = Track(3, 11, 78, 40)       # vibraphone melody
drums = Track(9, 0, 85, 64)

melody = [  # (beat within 8-bar phrase, length, pitch)
    (0, 1.5, 74), (1.5, 0.5, 72), (2, 1, 69), (3, 1, 72), (4, 3, 74), (7, 1, 77),
    (8, 1.5, 74), (9.5, 0.5, 72), (10, 2, 70), (12, 2, 69), (14, 2, 65),
    (16, 1.5, 72), (17.5, 0.5, 74), (18, 1, 77), (19, 1, 76), (20, 3, 72), (23, 1, 69),
    (24, 1, 67), (25, 1, 69), (26, 1, 72), (27, 1, 74), (28, 4, 76),
]
for rep in range(2):
    base = rep * 32
    for i, (root, notes) in enumerate(chords):
        b0 = base + i * 8
        for n in notes:
            pad.note(b0, 8, n, 60)
        for k in range(16):
            bass.note(b0 + k * 0.5, 0.45, root - 12 + (12 if k % 4 == 3 else 0), 88 if k % 2 == 0 else 70)
        if rep == 1 or i >= 2:
            seq = notes + [notes[0] + 12, notes[1] + 12]
            for k in range(32):
                arp.note(b0 + k * 0.25, 0.22, seq[k % len(seq)] + 12, 55 + (15 if k % 4 == 0 else 0))
    if rep == 1:
        for beat, length, pitch in melody:
            lead.note(base + beat, length, pitch, 82)
    for bar in range(8):
        b0 = base + bar * 4
        drums.note(b0, 0.25, 36, 100)
        drums.note(b0 + 2.5, 0.25, 36, 80)
        if rep == 1 or bar >= 4:
            drums.note(b0 + 1, 0.25, 38, 70)
            drums.note(b0 + 3, 0.25, 38, 78)
        for k in range(8):
            drums.note(b0 + k * 0.5, 0.2, 42, 38 + (12 if k % 2 == 0 else 0))

os.makedirs(OUT, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    mid = os.path.join(tmp, "cave.mid")
    raw = os.path.join(tmp, "raw.wav")
    write_midi(mid, [pad, bass, arp, lead, drums])
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", str(SR), "-F", raw, SF2, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(raw) as w:
        ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float).reshape(-1, ch)
    loop = int(round(BARS * 4 * 60 / BPM * SR))
    y = x[:loop].copy()
    tail = x[loop:loop + SR * 4]
    y[:len(tail)] += tail  # fold the reverb tail into the start: the loop point is seamless
    y *= 0.89 * 32767 / np.max(np.abs(y))
    loop_wav = os.path.join(tmp, "loop.wav")
    with wave.open(loop_wav, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.astype("<i2").tobytes())
    subprocess.run(["oggenc", "-Q", "-q", "5", "-o", os.path.join(OUT, "cave_theme.ogg"), loop_wav], check=True)
    import shutil
    shutil.copy(mid, os.path.join(OUT, "cave_theme.mid"))
print(f"wrote {OUT}/cave_theme.ogg ({loop / SR:.1f} s loop) and cave_theme.mid")
