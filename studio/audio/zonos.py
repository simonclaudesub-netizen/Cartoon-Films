"""ZONOS3-Mini (Zyphra, Apache-2.0) – lokale Sprachsynthese mit Stimmklon und Emotions-Steuerung.

Läuft als lokaler C++/ggml-Server auf der CPU (nur 127.0.0.1, keine externen Dienste).
Gebaut von setup.sh nach vendor/ZONOS3-Mini/servers/ggml.

Emotionen werden über die „Steering“-Regler des Modells gesteuert (Stimmfarbe bleibt erhalten):
ruhig ↔ aufgeregt (mood.arousal), langsamer ↔ schneller (delivery.tempo), Flüstern, Angst, Wut, Freude …
"""
import base64
import json
import os
import subprocess
import time
from pathlib import Path

import requests

from ..db import ROOT

HOME = ROOT / "vendor" / "ZONOS3-Mini" / "servers" / "ggml"
BIN = HOME / "build" / "zonos3-server"
BACKBONE = HOME / "gguf" / "backbone-ptq.gguf"
URL = "http://127.0.0.1:1919"
LOG = ROOT / "logs" / "zonos_server.log"

# Regler je Emotion (Dosen innerhalb der vom Hersteller als „safe“ markierten Bereiche)
EMOTION_CONTROLS = {
    "neutral": {"delivery.conversational": 2},
    "calm": {"emotions.serene": 4, "mood.arousal": -2, "delivery.tempo": -0.6, "delivery.conversational": 2},
    "whisper": {"delivery.whisper": 1.5, "mood.arousal": -1.5, "delivery.tempo": -0.4},
    "scared": {"emotions.scared": 4, "mood.arousal": 2, "delivery.tempo": 0.6, "delivery.conversational": 2},
    "panic": {"emotions.scared": 6, "mood.arousal": 3, "delivery.tempo": 1.2, "delivery.conversational": 3},
    "surprised": {"mood.arousal": 2.5, "expressive.expressive": 4, "delivery.conversational": 2},
    "angry": {"emotions.angry": 3, "mood.arousal": 2, "mood.valence": -2},
    "happy": {"emotions.happy": 3, "mood.valence": 2.5, "delivery.conversational": 3},
    "suspicious": {"mood.arousal": -1.5, "mood.valence": -1.5, "delivery.tempo": -0.5},
    "creepy": {"delivery.whisper": 0.8, "mood.arousal": -2.5, "mood.valence": -2.5, "delivery.tempo": -0.8},
    "sad": {"emotions.sad": 4, "delivery.tempo": -0.4},
    "smirk": {"mood.valence": 1.5, "delivery.conversational": 3},
}


def controls_for(emotion, voice):
    c = dict(EMOTION_CONTROLS.get(emotion or "neutral", EMOTION_CONTROLS["neutral"]))
    for k, v in (voice.get("controls") or {}).items():  # feste Regler der Figur (z. B. älter, tiefer)
        c[k] = round(c.get(k, 0) + v, 3)
    return c


def available():
    return BIN.exists() and BACKBONE.exists()


def running():
    try:
        return requests.get(f"{URL}/v2/capabilities", timeout=3).status_code == 200
    except requests.RequestException:
        return False


def ensure_server(timeout=240):
    if running():
        return
    if not available():
        raise RuntimeError("ZONOS3 nicht installiert (bash setup.sh)")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    libs = sorted({str(p.parent) for p in (HOME / "build").rglob("*.so*")})
    env = dict(os.environ, LD_LIBRARY_PATH=":".join(libs + [os.environ.get("LD_LIBRARY_PATH", "")]))
    subprocess.Popen([str(BIN), str(BACKBONE), "--host", "127.0.0.1", "--port", "1919", "--cpu"],
                     cwd=str(HOME), stdout=open(LOG, "ab"), stderr=subprocess.STDOUT, start_new_session=True, env=env)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if running():
            return
        time.sleep(2)
    raise RuntimeError(f"ZONOS3-Server startet nicht (siehe {LOG})")


_REF_B64 = {}


def generate(text, ref, out, controls, seed=1):
    ensure_server()
    ref = str(ref)
    if ref not in _REF_B64:
        _REF_B64[ref] = base64.b64encode(Path(ref).read_bytes()).decode()
    body = {"text": text, "language": "de", "stream": False, "format": "wav", "seed": int(seed),
            "speaker_mode": "embedding", "speaker_audio_base64": _REF_B64[ref]}
    if controls:
        body["controls"] = controls
    r = requests.post(f"{URL}/v2/generate", json=body, timeout=900)
    if r.status_code != 200:
        raise RuntimeError(f"ZONOS3 {r.status_code}: {r.text[:300]}")
    Path(out).write_bytes(r.content)
    return out


def describe(voice):
    return f"ZONOS3 (Klon: {Path(voice['ref']).name}{', Regler ' + json.dumps(voice['controls']) if voice.get('controls') else ''})"
