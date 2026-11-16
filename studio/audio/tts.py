"""Lokale Sprachsynthese mit Piper (Open Source, läuft offline auf der CPU).

Jede Figur hat eine feste Stimme (Modell, Sprecher-ID, Tempo, Tonhöhe).
Emotionen wählen bei mehrstimmigen Modellen (thorsten_emotional) die
passende Sprecher-ID. Effekte (durch die Tür, Telefon, innerer Monolog)
werden mit ffmpeg aufgebracht.
"""
import hashlib
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from ..db import ROOT

SR = 48000
VOICES = ROOT / "assets" / "voices"
CACHE = ROOT / "cache" / "tts"
_loaded = {}

# Aussprache-Hilfen nur für die Sprachausgabe (Untertitel bleiben unverändert)
PRONOUNCE = {
    "4B": "Vier Be", "4A": "Vier A", "03:07": "drei Uhr sieben", "3:07": "drei Uhr sieben",
    "Okan": "Okan", "Hm": "Hmm", "Äh": "Äh,", "z.B.": "zum Beispiel",
}

FX = {
    "door": "highpass=f=180,lowpass=f=1100,aecho=0.8:0.5:35:0.25,volume=0.85",
    "phone": "highpass=f=320,lowpass=f=3400,volume=0.95",
    "inner": "aecho=0.85:0.6:55:0.18",
    "radio": "highpass=f=400,lowpass=f=3000,acrusher=bits=10:mix=0.2",
}


def tts_text(text):
    out = text
    for k, v in PRONOUNCE.items():
        out = out.replace(k, v)
    return out


def _voice(model):
    if model not in _loaded:
        from piper import PiperVoice
        _loaded[model] = PiperVoice.load(str(VOICES / f"{model}.onnx"))
    return _loaded[model]


VENV_PY = ROOT / ".venv-tts" / "bin" / "python"
WORKER = Path(__file__).resolve().parent / "chatterbox_worker.py"
# Emotion -> Ausdrucksstärke (Chatterbox "exaggeration")
EXAGGERATION = {"neutral": 0.5, "happy": 0.6, "angry": 0.7, "scared": 0.75, "surprised": 0.7, "sad": 0.45,
                "creepy": 0.65, "whisper": 0.35, "suspicious": 0.55}


def _key(text, voice, emotion, fx, length_mul, noise, seed):
    if voice.get("engine") == "chatterbox":
        ex = voice.get("exaggeration", {}).get(emotion) if isinstance(voice.get("exaggeration"), dict) else None
        ex = ex if ex is not None else EXAGGERATION.get(emotion, 0.5)
        k = ["cb", text, voice["ref"], ex, voice.get("cfg", 0.5), voice.get("temperature", 0.8), seed, fx,
             length_mul, voice.get("pitch", 0.0), 2]
        return hashlib.sha1(json.dumps(k, ensure_ascii=False).encode()).hexdigest()[:16], ex
    speaker = (voice.get("emotions") or {}).get(emotion, voice.get("speaker", 0))
    ls = voice.get("length_scale", 1.0) * length_mul
    k = [text, voice["model"], speaker, ls, voice.get("pitch", 0.0), fx, noise, 3]
    return hashlib.sha1(json.dumps(k, ensure_ascii=False).encode()).hexdigest()[:16], None


def prepare(requests):
    """Erzeugt alle noch fehlenden Chatterbox-Zeilen in EINEM Worker-Lauf (Modell lädt nur einmal).
    requests: Liste von dicts mit text, voice, emotion, fx, length_mul, seed."""
    jobs = []
    for r in requests:
        v = r["voice"]
        if v.get("engine") != "chatterbox":
            continue
        h, ex = _key(r["text"], v, r.get("emotion", "neutral"), r.get("fx"), r.get("length_mul", 1.0), None,
                     r.get("seed", 1))
        if (CACHE / f"{h}.wav").exists() or (CACHE / f"{h}.raw.wav").exists():
            continue
        jobs.append({"text": tts_text(r["text"]), "ref": str(ROOT / v["ref"]), "exaggeration": ex,
                     "cfg": v.get("cfg", 0.5), "temperature": v.get("temperature", 0.8),
                     "seed": r.get("seed", 1), "out": str(CACHE / f"{h}.raw.wav")})
    if not jobs:
        return 0
    CACHE.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([str(VENV_PY), str(WORKER)], input=json.dumps(jobs), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Chatterbox-Worker fehlgeschlagen: {p.stderr[-800:]}")
    return len(jobs)


def _post(raw, out, pitch, fx, tempo=1.0):
    filt = []
    if pitch:
        filt.append(f"rubberband=pitch={2 ** (pitch / 12):.4f}:formant=preserved")
    filt.append(f"aresample={SR}")
    if abs(tempo - 1.0) > 0.01:
        filt.append(f"atempo={tempo:.3f}")
    if fx in FX:
        filt.append(FX[fx])
    filt.append("silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                "silenceremove=start_periods=1:start_threshold=-50dB,areverse")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af", ",".join(filt), "-ac", "1",
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(out)], check=True)


def synth(text, voice, emotion="neutral", fx=None, length_mul=1.0, noise=None, seed=1):
    """Erzeugt eine Sprachzeile -> (Pfad zur 48-kHz-WAV, Samples float32 mono)."""
    h, _ = _key(text, voice, emotion, fx, length_mul, noise, seed)
    out = CACHE / f"{h}.wav"
    if out.exists():
        return out, read_wav(out)
    CACHE.mkdir(parents=True, exist_ok=True)
    if voice.get("engine") == "chatterbox":
        raw = CACHE / f"{h}.raw.wav"
        if not raw.exists():
            prepare([{"text": text, "voice": voice, "emotion": emotion, "fx": fx, "length_mul": length_mul,
                      "seed": seed}])
        _post(raw, out, voice.get("pitch", 0.0), fx, tempo=1.0 / length_mul)
        return out, read_wav(out)
    speaker = (voice.get("emotions") or {}).get(emotion, voice.get("speaker", 0))
    from piper import SynthesisConfig
    multi = _voice(voice["model"]).config.num_speakers > 1
    cfg = SynthesisConfig(speaker_id=speaker if multi else None,
                          length_scale=voice.get("length_scale", 1.0) * length_mul,
                          noise_scale=noise if noise is not None else 0.6, noise_w_scale=0.75)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        raw = tmp.name
    with wave.open(raw, "wb") as w:
        _voice(voice["model"]).synthesize_wav(tts_text(text), w, syn_config=cfg)
    _post(raw, out, voice.get("pitch", 0.0), fx)
    Path(raw).unlink(missing_ok=True)
    return out, read_wav(out)


def read_wav(p):
    with wave.open(str(p), "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
    return data


def mouth_envelope(samples, fps=30):
    """Lautstärke pro Videobild -> Mundöffnung 0..1 (für Lippensynchronität)."""
    hop = SR // fps
    n = int(np.ceil(len(samples) / hop))
    env = np.array([np.sqrt(np.mean(samples[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    if len(env) == 0:
        return []
    ref = np.percentile(env, 90) + 1e-6
    env = np.clip(env / ref, 0, 1.2)
    env = np.where(env < 0.18, 0, env)
    # kleine Variation, damit der Mund nicht "flattert"
    sm = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    return [round(float(min(1.0, v)), 3) for v in sm]
