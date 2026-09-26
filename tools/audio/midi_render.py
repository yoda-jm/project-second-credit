"""Shared helpers for music written as code: a tiny MIDI writer and a FluidSynth renderer that produces a
seamless Ogg loop. Used by the per-game music scripts. Needs fluidsynth, oggenc and FluidR3_GM.sf2."""
import os, shutil, struct, subprocess, tempfile, wave
import numpy as np

TPB = 480
SR = 44100
SF2 = next((p for p in ["/usr/share/sounds/sf2/FluidR3_GM.sf2", "/usr/share/soundfonts/FluidR3_GM.sf2"]
            if os.path.exists(p)), None)


class Track:
    def __init__(self, channel, program, volume=100, pan=64, reverb=50):
        self.ch = channel
        self.events = []
        if channel != 9:
            self.events.append((0, bytes([0xC0 | channel, program])))
        self.events += [(0, bytes([0xB0 | channel, 7, volume])), (0, bytes([0xB0 | channel, 10, pan])),
                        (0, bytes([0xB0 | channel, 91, reverb]))]

    def note(self, beat, length, pitch, vel=90):
        self.events.append((int(beat * TPB), bytes([0x90 | self.ch, pitch, vel])))
        self.events.append((int((beat + length) * TPB) - 1, bytes([0x80 | self.ch, pitch, 0])))


def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, 0x80 | (n & 0x7F))
        n >>= 7
    return bytes(out)


def write_midi(path, tracks, bpm):
    chunks = []
    tempo = [(0, bytes([0xFF, 0x51, 0x03]) + int(60_000_000 / bpm).to_bytes(3, "big"))]
    for evs in [tempo] + [t.events for t in tracks]:
        data, last = b"", 0
        for tick, ev in sorted(evs, key=lambda e: (e[0], e[1][0] & 0xF0 == 0x90)):
            data += _vlq(tick - last) + ev
            last = tick
        data += _vlq(0) + b"\xFF\x2F\x00"
        chunks.append(b"MTrk" + struct.pack(">I", len(data)) + data)
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), TPB) + b"".join(chunks))


def render_loop(tracks, bpm, bars, out_ogg, gain=0.6, rms_db=None):
    """Renders the tracks, folds the reverb tail into the start (seamless loop), writes Ogg and the MIDI.
    Normalised to a -1 dB peak, or, with rms_db, to that RMS level (the peak still capped at -1 dB)."""
    with tempfile.TemporaryDirectory() as tmp:
        mid, raw, loop_wav = (os.path.join(tmp, n) for n in ("m.mid", "raw.wav", "loop.wav"))
        write_midi(mid, tracks, bpm)
        subprocess.run(["fluidsynth", "-ni", "-g", str(gain), "-r", str(SR), "-F", raw, SF2, mid], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with wave.open(raw) as w:
            ch = w.getnchannels()
            x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float).reshape(-1, ch)
        loop = int(round(bars * 4 * 60 / bpm * SR))
        y = x[:loop].copy()
        tail = x[loop:loop + SR * 4]
        y[:len(tail)] += tail
        scale = 0.89 * 32767 / np.max(np.abs(y))
        if rms_db is not None:
            scale = min(scale, 10 ** (rms_db / 20) * 32767 / np.sqrt(np.mean(y ** 2)))
        y *= scale
        with wave.open(loop_wav, "wb") as w:
            w.setnchannels(ch)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(y.astype("<i2").tobytes())
        os.makedirs(os.path.dirname(out_ogg), exist_ok=True)
        subprocess.run(["oggenc", "-Q", "-q", "5", "-o", out_ogg, loop_wav], check=True)
        shutil.copy(mid, out_ogg[:-4] + ".mid")
    return loop / SR
