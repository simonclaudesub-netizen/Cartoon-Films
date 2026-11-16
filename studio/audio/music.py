"""Prozedurale Hintergrundmusik (eigene Kompositionen per Algorithmus, lizenzfrei).

Stimmungen: tension, mystery, cozy, comedy, silence.
"""
import numpy as np

SR = 48000
NOTE = {n: i for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())}


def hz(name, octave):
    return 440 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def _reverb(x, decay=1.6, mix=0.3, seed=1):
    rng = np.random.default_rng(seed)
    n = int(decay * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 6.9 / decay)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return x * (1 - mix) + wet * mix


def _tone(f, d, kind="sine", a=0.01, r=0.5):
    t = np.arange(int(d * SR)) / SR
    if kind == "pluck":
        s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.5 for k in range(1, 6))
        env = np.minimum(1, t / 0.004) * np.exp(-t / r)
    elif kind == "bell":
        s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
        env = np.minimum(1, t / 0.002) * np.exp(-t / r)
    elif kind == "pad":
        s = sum(np.sin(2 * np.pi * f * (1 + det) * t) for det in (-0.004, 0, 0.005))
        env = np.minimum(1, t / max(a, 0.01)) * np.minimum(1, (d - t) / 0.4)
    else:
        s = np.sin(2 * np.pi * f * t)
        env = np.minimum(1, t / a) * np.exp(-t / r)
    return (s * env).astype(np.float64)


def _place(buf, x, at):
    o = int(at * SR)
    if o >= len(buf):
        return
    e = min(len(buf), o + len(x))
    buf[o:e] += x[:e - o]


def generate(mood, dur, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n)
    if mood == "silence" or dur <= 0:
        return out.astype(np.float32)
    if mood in ("tension", "mystery"):
        root = "D"
        scale = [("D", 0), ("D#", 0), ("F", 0), ("G", 0), ("A", 0), ("A#", 0), ("C", 1)]
        # Drone
        t = np.arange(n) / SR
        drone = sum(np.sin(2 * np.pi * hz(root, 2) * m * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)) / m
                    for m in (1, 1.5, 2.003))
        out += drone * 0.18 * (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t))
        bpm = 96 if mood == "tension" else 72
        beat = 60 / bpm
        b = 0
        while b * beat < dur:
            if mood == "tension":
                _place(out, _tone(hz(root, 2), 0.25, "pluck", r=0.12) * 0.35, b * beat)
                if b % 4 == 2:
                    tk = rng.normal(0, 1, int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / SR / 0.005)
                    _place(out, tk * 0.08, b * beat)
            if b % 2 == 0 and rng.random() < 0.6:
                nm, oc = scale[rng.integers(len(scale))]
                kind = "bell" if mood == "mystery" else "pluck"
                _place(out, _tone(hz(nm, 4 + oc), 1.8, kind, r=0.7) * 0.18, b * beat + (beat / 2 if rng.random() < 0.3 else 0))
            b += 1
        out = _reverb(out, 2.2, 0.35, seed)
    elif mood in ("cozy", "comedy"):
        bpm = 100 if mood == "cozy" else 124
        beat = 60 / bpm
        prog = [("C", "E", "G"), ("A", "C", "E"), ("F", "A", "C"), ("G", "B", "D")]
        bar = 0
        while bar * 4 * beat < dur:
            chord = prog[bar % 4]
            for k in range(8):
                nm = chord[[0, 1, 2, 1][k % 4]]
                oc = 4 if k % 4 != 2 else 5
                _place(out, _tone(hz(nm, oc), 0.5, "pluck", r=0.2) * 0.16, (bar * 4 + k / 2) * beat)
            _place(out, _tone(hz(chord[0], 2), 4 * beat, "pluck", r=0.6) * 0.3, bar * 4 * beat)
            if mood == "comedy":
                for k in range(4):
                    _place(out, _tone(hz(chord[k % 3], 5), 0.2, "bell", r=0.08) * 0.08, (bar * 4 + k + 0.5) * beat)
            bar += 1
        out = _reverb(out, 1.2, 0.2, seed)
    # weiche Ein-/Ausblendung
    f = min(int(0.4 * SR), n // 4)
    if f > 0:
        out[:f] *= np.linspace(0, 1, f)
        out[-f:] *= np.linspace(1, 0, f)
    peak = np.max(np.abs(out)) + 1e-9
    return (out / peak * 0.5).astype(np.float32)
