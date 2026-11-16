"""Soundeffekte, vollständig synthetisch erzeugt (keine fremden Sample-Dateien)."""
import numpy as np

SR = 48000
_rng = np.random.default_rng(7)


def _t(d):
    return np.arange(int(d * SR)) / SR


def _env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(d, 1e-4))
    return e


def _lp(x, cutoff):
    """Einfacher Tiefpass (FFT)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def _hp(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (cutoff / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X, len(x))


def knock(n=3, spacing=0.28, hard=1.0):
    out = np.zeros(int((n * spacing + 0.4) * SR))
    for i in range(n):
        d = int(0.18 * SR)
        t = _t(0.18)
        body = np.sin(2 * np.pi * (110 + 40 * np.exp(-t * 30)) * t) * _env(d, 0.001, 0.035)
        click = _lp(_rng.normal(0, 1, d), 1800) * _env(d, 0.0005, 0.012) * 0.6
        s = (body + click) * hard * (0.9 + 0.1 * _rng.random())
        o = int(i * spacing * SR)
        out[o:o + d] += s
    return out * 0.9


def creak(d=1.4):
    t = _t(d)
    f = 180 + 60 * np.sin(2 * np.pi * 0.9 * t) + 30 * np.sin(2 * np.pi * 3.1 * t)
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    grit = (np.sin(2 * np.pi * 23 * t) > 0.6).astype(float) * 0.5 + 0.5
    s = _lp(saw * grit, 2400) * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.3)
    return s * 0.25


def buzz(d=0.9):
    t = _t(d)
    s = np.sign(np.sin(2 * np.pi * 160 * t)) * 0.3 * (np.sin(2 * np.pi * 12 * t) > -0.2)
    return _lp(s, 900) * np.minimum(1, (d - t) / 0.05) * 0.5


def ping():
    t = _t(0.6)
    s = (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 1980 * t)) * _env(len(t), 0.002, 0.12)
    s2 = np.sin(2 * np.pi * 1760 * t) * _env(len(t), 0.002, 0.15)
    o = int(0.09 * SR)
    s[o:] += s2[:len(s) - o] * 0.8
    return s * 0.35


def whoosh(d=0.6):
    t = _t(d)
    n = _rng.normal(0, 1, len(t))
    s = _hp(_lp(n, 2500), 300) * np.sin(np.pi * t / d) ** 2
    return s * 0.35


def sting(d=2.2):
    """Dissonanter Schreck-Akkord (Horror-Stinger)."""
    t = _t(d)
    s = np.zeros_like(t)
    for f in (146.8, 155.6, 207.7, 311.1, 329.6):
        s += np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * 5.5 * t))
    s = s / 5 * np.minimum(1, t / 0.04) * np.exp(-t / 0.9)
    hit = _lp(_rng.normal(0, 1, len(t)), 400) * _env(len(t), 0.002, 0.15) * 1.5
    return (s + hit) * 0.5


def heartbeat(n=4, bpm=88):
    sp = 60 / bpm
    out = np.zeros(int((n * sp + 0.5) * SR))
    for i in range(n):
        for k, (dt, g) in enumerate(((0, 1.0), (0.17, 0.7))):
            t = _t(0.2)
            b = np.sin(2 * np.pi * (55 + 25 * np.exp(-t * 25)) * t) * _env(len(t), 0.003, 0.05) * g
            o = int((i * sp + dt) * SR)
            out[o:o + len(b)] += b
    return out * 0.9


def steps(n=4, spacing=0.45):
    out = np.zeros(int((n * spacing + 0.3) * SR))
    for i in range(n):
        d = int(0.12 * SR)
        s = _lp(_rng.normal(0, 1, d), 900) * _env(d, 0.002, 0.03)
        o = int(i * spacing * SR)
        out[o:o + d] += s * (0.7 + 0.3 * (i % 2))
    return out * 0.6


def thud():
    t = _t(0.5)
    s = np.sin(2 * np.pi * (70 + 50 * np.exp(-t * 20)) * t) * _env(len(t), 0.002, 0.08)
    s += _lp(_rng.normal(0, 1, len(t)), 700) * _env(len(t), 0.001, 0.03) * 0.5
    return s * 0.8


def lights_out():
    t = _t(0.9)
    hum = np.sin(2 * np.pi * 100 * t) * 0.15 * (t < 0.25)
    clunk = _lp(_rng.normal(0, 1, len(t)), 1200) * _env(len(t), 0.001, 0.05) * (t > 0.25)
    return hum + np.roll(clunk, int(0.25 * SR)) * 0.9


def keys():
    out = np.zeros(int(0.8 * SR))
    for i in range(7):
        t = _t(0.25)
        f = _rng.uniform(3000, 6000)
        s = np.sin(2 * np.pi * f * t) * _env(len(t), 0.0005, 0.04) * 0.25
        o = int(_rng.uniform(0, 0.5) * SR)
        out[o:o + len(s)] += s
    return out


def riser(d=1.5):
    t = _t(d)
    f = 200 * (4 ** (t / d))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2 * 0.25
    return s + whoosh(d) * (t / d)


LIB = {"knock": knock, "knock_hard": lambda: knock(4, 0.22, 1.4), "creak": creak, "buzz": buzz, "ping": ping,
       "whoosh": whoosh, "sting": sting, "heartbeat": heartbeat, "steps": steps, "thud": thud,
       "lights_out": lights_out, "keys": keys, "riser": riser}


def make(name):
    return LIB[name]().astype(np.float32)
