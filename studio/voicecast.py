"""Automatisches Stimmen-Casting: testet lokale Piper-Stimmen auf Verständlichkeit (Whisper)
und schätzt die Grundfrequenz (F0) -> passende Stimmlage für Alter/Geschlecht der Figur.

Aufruf: python -m studio.voicecast <figur> [--female|--male]
"""
import json
import sys

import numpy as np

from . import db, qc
from .audio import tts


def f0_median(x, sr=tts.SR):
    x = x[::2]
    sr //= 2
    fr = int(0.04 * sr)
    vals = []
    for i in range(0, len(x) - fr, fr):
        seg = x[i:i + fr] - np.mean(x[i:i + fr])
        if np.sqrt(np.mean(seg ** 2)) < 0.02:
            continue
        ac = np.correlate(seg, seg, "full")[fr - 1:]
        lo, hi = sr // 400, sr // 70
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.3 * ac[0]:
            vals.append(sr / k)
    return float(np.median(vals)) if vals else 0.0


def candidates():
    c = [{"model": "de_DE-kerstin-low", "speaker": 0}, {"model": "de_DE-ramona-low", "speaker": 0},
         {"model": "de_DE-eva_k-x_low", "speaker": 0}, {"model": "de_DE-karlsson-low", "speaker": 0},
         {"model": "de_DE-thorsten-medium", "speaker": 0}]
    # mls-medium getestet am 16.11.2026: Verständlichkeit < 0,3 -> ausgeschlossen
    return c


def evaluate(lines, cand, pitch=0.0, length=1.0):
    v = dict(cand, pitch=pitch, length_scale=length)
    sims, f0s = [], []
    for t in lines:
        p, smp = tts.synth(t, v)
        sims.append(qc.similarity(t, qc.transcribe(p)))
        f0s.append(f0_median(smp))
    return {"voice": v, "sim": round(float(np.mean(sims)), 3), "min": round(float(np.min(sims)), 3),
            "f0": round(float(np.median(f0s)), 1)}


def cast(cid, f0_range):
    sc = [json.loads(p.read_text()) for p in db.EP_DIR.glob("*/script.json")]
    lines = [ln.get("tts") or ln["text"] for s in sc for sh in s["shots"] for ln in sh.get("lines", [])
             if ln["speaker"] == cid][:5]
    res = []
    for c in candidates():
        r = evaluate(lines, c)
        r["fits"] = f0_range[0] <= r["f0"] <= f0_range[1]
        res.append(r)
        print(json.dumps(r), flush=True)
    good = sorted([r for r in res if r["fits"]], key=lambda r: (-r["min"], -r["sim"]))
    return good, res


if __name__ == "__main__":
    cid = sys.argv[1]
    rng = (150, 260) if "--female" in sys.argv else (80, 150)
    good, res = cast(cid, rng)
    (db.ROOT / "logs" / f"casting_{cid}.json").write_text(json.dumps(res, indent=1))
    print("BESTE:", json.dumps(good[:5], indent=1))
