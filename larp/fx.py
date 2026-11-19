"""Nachbearbeitung pro Bild (NumPy/OpenCV): Bloom, Chromatic Aberration, Glitch, Flash, Scanlines, Korn."""
import cv2
import numpy as np

W, H = 1080, 1920
_cache = {}


def _vignette():
    if "vig" not in _cache:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
        v = np.clip(1.15 - 0.55 * d ** 2, 0.45, 1.0)
        scan = np.ones(H, np.float32)
        scan[::3] = 0.9
        _cache["vig"] = (v * scan[:, None])[..., None]
        rng = np.random.default_rng(5)
        _cache["grain"] = [rng.normal(0, 3, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]
    return _cache["vig"]


def process(bgra, t, fx, seed=0):
    """bgra: (H, W, 4) uint8 von Cairo. fx: dict mit bump, flash, glitch, chroma, mono. -> BGR uint8."""
    img = bgra[..., :3].astype(np.float32)
    # Bloom: helle Bereiche weichzeichnen und addieren
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bright = np.clip(small - 110, 0, None) * 1.6
    b1 = cv2.GaussianBlur(bright, (0, 0), 6)
    b2 = cv2.GaussianBlur(bright, (0, 0), 22)
    bloom = cv2.resize(b1 * 0.9 + b2 * 0.8, (W, H), interpolation=cv2.INTER_LINEAR)
    img += bloom * (0.85 + 0.6 * fx.get("bump", 0))
    # Chromatic Aberration (auf dem Beat stärker)
    ca = int(round((0 if fx.get("mono") else 1) + 12 * fx.get("chroma", 0)))
    if ca > 0:
        img[..., 2] = np.roll(img[..., 2], ca, axis=1)
        img[..., 0] = np.roll(img[..., 0], -ca, axis=1)
    # Glitch: horizontale Streifen verschieben
    g = fx.get("glitch", 0)
    if g > 0.05:
        rng = np.random.default_rng(int(t * 1000) + seed)
        for _ in range(int(6 + 18 * g)):
            y0 = int(rng.integers(0, H - 10))
            hh = int(rng.integers(6, 90))
            dx = int(rng.integers(-120, 120) * g)
            img[y0:y0 + hh] = np.roll(img[y0:y0 + hh], dx, axis=1)
            if rng.random() < 0.3:
                img[y0:y0 + hh, :, int(rng.integers(0, 3))] *= 1.8
    # Flash
    fl = fx.get("flash", 0)
    if fl > 0.01:
        img = img * (1 - 0.35 * fl) + 255 * 0.85 * fl
    img *= _vignette()
    gr = _cache["grain"][int(t * 12) % 6]
    img += cv2.resize(gr, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    if fx.get("mono"):
        m = img.mean(axis=2, keepdims=True)
        img = img * 0.15 + m * 0.85
    return np.clip(img, 0, 255).astype(np.uint8)
