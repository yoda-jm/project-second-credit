"""Shared sound-synthesis helpers (NumPy) for the per-game sound-effect scripts."""
import os, wave
import numpy as np

SR = 44100


class Synth:
    def __init__(self, out_dir, seed=1):
        self.out = out_dir
        self.rng = np.random.default_rng(seed)
        os.makedirs(out_dir, exist_ok=True)

    @staticmethod
    def t(sec):
        return np.arange(int(SR * sec)) / SR

    @staticmethod
    def env(n, attack=0.005, decay=0.2, curve=4.0):
        x = np.arange(n) / SR
        return np.clip(x / max(attack, 1e-4), 0, 1) * np.exp(-curve * np.clip(x - attack, 0, None) / max(decay, 1e-4))

    @staticmethod
    def lowpass(x, cutoff):
        c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
        k = 1 - np.exp(-2 * np.pi * c / SR)
        y = np.empty_like(x)
        acc = 0.0
        for i in range(len(x)):
            acc += k[i] * (x[i] - acc)
            y[i] = acc
        return y

    def highpass(self, x, cutoff):
        return x - self.lowpass(x, cutoff)

    def noise(self, sec):
        return self.rng.uniform(-1, 1, int(SR * sec))

    def sweep(self, f0, f1, sec, shape=np.sin):
        f = np.geomspace(f0, f1, int(SR * sec))
        return shape(2 * np.pi * np.cumsum(f) / SR)

    def bell(self, freq, sec, partials=((1, 1.0), (2.76, 0.5), (5.4, 0.25)), decay=0.5):
        tt = self.t(sec)
        return sum(a * np.sin(2 * np.pi * freq * r * tt) * np.exp(-tt * (3 + r) / decay) for r, a in partials)

    def save(self, name, x, gain=0.9, fade=True):
        x = np.asarray(x, dtype=float)
        if fade:  # off for seamless loops, whose end must meet their start
            fade = min(len(x), int(SR * 0.004))
            x[-fade:] *= np.linspace(1, 0, fade)
        x = x / (np.max(np.abs(x)) + 1e-9) * gain
        with wave.open(os.path.join(self.out, name + ".wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((x * 32767).astype("<i2").tobytes())
        print("wrote", name, f"{len(x) / SR:.2f}s")
