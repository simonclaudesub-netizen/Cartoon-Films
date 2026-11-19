"""Platzhalter-Beat im Phonk-Stil (eigene, algorithmische Komposition – lizenzfrei).

Die echten Trend-Sounds (z.B. 'KITTY RALLY TWO - SLOW', 'Gorąca Jak San Pedro') sind
urheberrechtlich geschützt und werden NICHT ins Video gerendert. Sie werden in der TikTok-App
über 'Sound verwenden' / 'Sounds hinzufügen' daruntergelegt (Originalton auf 0 %).
Der Platzhalter sorgt nur dafür, dass das Video schon im Tempo geschnitten ist und auf
YouTube/Shorts nicht stumm läuft.
"""
import wave

import numpy as np

SR = 44100


def _env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def _808(f0, dur, glide=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.full(n, f0) * (1 + 1.6 * np.exp(-t * 40))
    if glide:
        f *= np.where(t > dur * 0.5, np.exp(np.log(glide / f0) * np.minimum(1, (t - dur * 0.5) / 0.08)), 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.tanh(2.6 * np.sin(ph)) * _env(n, 0.002, dur * 0.55)
    return x


def _cowbell(f, dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sq = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    # einfacher Bandpass über Differenz zweier Tiefpässe
    k1, k2 = 0.35, 0.06
    lp1 = np.zeros(n)
    lp2 = np.zeros(n)
    a = b = 0.0
    for i in range(n):
        a += k1 * (sq[i] - a)
        b += k2 * (sq[i] - b)
        lp1[i], lp2[i] = a, b
    return (lp1 - lp2) * _env(n, 0.001, 0.06 + dur * 0.25)


def _noise_hit(dur, d, hp=True, seed=0):
    n = int(dur * SR)
    x = np.random.default_rng(seed).normal(0, 1, n)
    if hp:
        x = np.diff(np.concatenate([[0], x]))
    return x * _env(n, 0.001, d)


def _clap(seed):
    x = np.zeros(int(0.35 * SR))
    for k, off in enumerate((0, 0.011, 0.022)):
        h = _noise_hit(0.3, 0.012 if k < 2 else 0.12, seed=seed + k)
        o = int(off * SR)
        x[o:o + len(h)] += h[:len(x) - o]
    return x * 0.7


def _place(buf, x, at, g=1.0):
    o = int(at * SR)
    if o >= len(buf):
        return
    e = min(len(buf), o + len(x))
    buf[o:e] += x[:e - o] * g


def _lowpass(x, k):
    y = np.empty_like(x)
    a = 0.0
    for i in range(len(x)):
        a += k * (x[i] - a)
        y[i] = a
    return y


def generate(bpm, dur, drop_beat=8, seed=1):
    """Stereo float32 (n, 2). drop_beat: ab diesem Schlag setzt der volle Beat ein."""
    n = int(dur * SR)
    drums, bass, bell = np.zeros(n), np.zeros(n), np.zeros(n)
    beat = 60 / bpm
    st = beat / 4
    root = 43.65  # F1
    prog = [1.0, 0.8409, 0.8909, 0.7492]  # F, Db, Eb, C (F-Moll)
    mel = [0, 3, 7, 3, 10, 7, 3, 0, 12, 10, 7, 10, 7, 3, 5, 3]
    clap = _clap(seed)
    hat = _noise_hit(0.05, 0.012, seed=seed + 9)
    bells = {}
    steps = int(dur / st) + 1
    for s in range(steps):
        t = s * st
        b = s // 4
        bar = s // 16
        pos = s % 16
        full = b >= drop_beat
        f = root * prog[bar % 4]
        if full:
            if pos in (0, 7, 10):
                _place(bass, _808(f * (2 if pos == 10 else 1), st * (6 if pos == 0 else 3),
                                  glide=f * 2 if pos == 7 else None), t, 0.9)
            if pos in (4, 12):
                _place(drums, clap, t, 0.6)
            roll = (bar % 2 == 1 and pos >= 14)
            if pos % 2 == 0 or roll:
                _place(drums, hat, t, 0.22 if pos % 4 == 0 else 0.14)
                if roll:
                    _place(drums, hat, t + st / 2, 0.12)
        if pos % 2 == 0 or full:
            note = mel[(pos + (bar % 2) * 3) % 16]
            fb = 523.25 * 2 ** (note / 12) * prog[bar % 4] / prog[0] ** 0
            key = round(fb, 1)
            if key not in bells:
                bells[key] = _cowbell(fb)
            _place(bell, bells[key], t, 0.28 if full else 0.18)
    # Intro gedämpft, dann Drop
    di = int(drop_beat * beat * SR)
    bell[:di] = _lowpass(bell[:di], 0.08) * 2.2
    mix_l = drums * 0.9 + bass * 0.75 + bell
    # Stereo: Glocke leicht verzögert rechts
    d = int(0.012 * SR)
    bell_r = np.concatenate([np.zeros(d), bell[:-d]])
    mix_r = drums * 0.9 + bass * 0.75 + bell_r
    st_ = np.stack([mix_l, mix_r], axis=1)
    fade = int(0.4 * SR)
    st_[-fade:] *= np.linspace(1, 0, fade)[:, None]
    st_ = np.tanh(st_ * 1.4)
    st_ /= np.max(np.abs(st_)) + 1e-9
    return (st_ * 0.89).astype(np.float32)


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
