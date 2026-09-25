#!/usr/bin/env python3
"""Interface sounds for the launcher and menus (move, select, back), synthesised with NumPy.
Usage: python3 tools/audio/ui_sfx.py [out_dir]  (default: godot/core/audio). Output licence: CC BY-SA 4.0.
"""
import os, sys, wave
import numpy as np

SR = 44100
out = sys.argv[1] if len(sys.argv) > 1 else "godot/core/audio"
os.makedirs(out, exist_ok=True)


def tone(freqs, dur, decay, bright=0.3):
    t = np.arange(int(SR * dur)) / SR
    s = sum(np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) for f in freqs)
    a = np.clip(t / 0.003, 0, 1) * np.exp(-t / decay)
    return s * a


def save(name, x, gain):
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    with wave.open(os.path.join(out, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    print("wrote", name)


save("ui_move", tone([1320], 0.08, 0.025, 0.1), 0.35)
x = np.concatenate([tone([880, 1320], 0.07, 0.03), tone([1175, 1760], 0.3, 0.09)])
save("ui_select", x, 0.5)
save("ui_back", np.concatenate([tone([988], 0.07, 0.03), tone([659], 0.2, 0.06)]), 0.4)
t = np.arange(int(SR * 1.2)) / SR
whoosh = np.random.default_rng(3).uniform(-1, 1, len(t)) * np.sin(np.pi * t / 1.2) ** 2
save("ui_start", whoosh * 0.4 + tone([523.3, 659.3, 784, 1046.5], 1.2, 0.5), 0.6)
