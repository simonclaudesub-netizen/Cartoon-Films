"""Lokale Sprachsynthese: Qwen3-TTS (Hauptstimmen), ZONOS3-Mini und Piper als Rückfall – alles offline auf der CPU.

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
    # Kein Echo/Delay mehr (klang wie eine doppelte Stimme) – nur Klangfarbe
    "door": "highpass=f=160,lowpass=f=1600,volume=0.9",
    "phone": "highpass=f=320,lowpass=f=3400,volume=0.95",
    "inner": "equalizer=f=180:t=q:w=1:g=1.5",
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


# Klarheits-Kette für jede Stimme: Rumpeln weg, Präsenz anheben, sanft komprimieren
CLARITY = ("highpass=f=75,equalizer=f=300:t=q:w=1.2:g=-1.5,equalizer=f=3200:t=q:w=1.0:g=2.5,"
           "equalizer=f=7500:t=q:w=1.0:g=-1.5,acompressor=threshold=-21dB:ratio=2.5:attack=8:release=120:makeup=1.5")
POST_VERSION = 4
_REF_HASH = {}


def _ref_hash(ref):
    if ref not in _REF_HASH:
        p = ROOT / ref
        _REF_HASH[ref] = hashlib.sha1(p.read_bytes()).hexdigest()[:12] if p.exists() else ref
    return _REF_HASH[ref]


def resolve(voice):
    """Hauptstimme oder – falls deren Werkzeug fehlt – die nächste Rückfall-Stimme (Qwen3 → ZONOS3 → Piper)."""
    if voice.get("engine") == "qwen3":
        from . import qwen
        if qwen.available():
            return voice
        voice = {**voice.get("fallback_zonos", {}), "fallback": voice.get("fallback")}
    if voice.get("engine") == "zonos":
        from . import zonos
        if zonos.available():
            return voice
        voice = voice.get("fallback") or {}
    if not voice.get("model") and not voice.get("engine"):
        raise RuntimeError("Keine Stimme verfügbar (bash setup.sh)")
    return voice


def _key(text, voice, emotion, fx, length_mul, noise, seed):
    voice = resolve(voice)
    if voice.get("engine") == "qwen3":
        from . import qwen
        k = ["qw", text, _ref_hash(voice["ref"]), voice.get("ref_text", ""), qwen.MODEL, seed,
             fx, FX.get(fx), length_mul, voice.get("pitch", 0.0), CLARITY, POST_VERSION]
        return hashlib.sha1(json.dumps(k, ensure_ascii=False).encode()).hexdigest()[:16], None
    if voice.get("engine") == "zonos":
        from . import zonos
        k = ["zn", text, _ref_hash(voice["ref"]), zonos.controls_for(emotion, voice), seed,
             fx, FX.get(fx), length_mul, voice.get("pitch", 0.0), CLARITY, POST_VERSION]
        return hashlib.sha1(json.dumps(k, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16], None
    if voice.get("engine") == "chatterbox":
        ex = voice.get("exaggeration", {}).get(emotion) if isinstance(voice.get("exaggeration"), dict) else None
        ex = ex if ex is not None else EXAGGERATION.get(emotion, 0.5)
        k = ["cb", text, _ref_hash(voice["ref"]), ex, voice.get("cfg", 0.5), voice.get("temperature", 0.8), seed]
        k += [fx, FX.get(fx), length_mul, voice.get("pitch", 0.0), CLARITY, POST_VERSION]
        return hashlib.sha1(json.dumps(k, ensure_ascii=False).encode()).hexdigest()[:16], ex
    speaker = (voice.get("emotions") or {}).get(emotion, voice.get("speaker", 0))
    ls = voice.get("length_scale", 1.0) * length_mul
    k = [text, voice["model"], speaker, ls, voice.get("pitch", 0.0), fx, noise, 3]
    return hashlib.sha1(json.dumps(k, ensure_ascii=False).encode()).hexdigest()[:16], None


def prepare(requests):
    """Erzeugt alle noch fehlenden Qwen3-/ZONOS3-/Chatterbox-Zeilen in EINEM Worker-Lauf (Modell lädt nur einmal).
    requests: Liste von dicts mit text, voice, emotion, fx, length_mul, seed."""
    jobs, qjobs, n_zonos = [], [], 0
    for r in requests:
        v = resolve(r["voice"])
        if v.get("engine") == "qwen3":
            h, _ = _key(r["text"], v, r.get("emotion", "neutral"), r.get("fx"), r.get("length_mul", 1.0), None,
                        r.get("seed", 1))
            raw = CACHE / f"{h}.raw.wav"
            if not (CACHE / f"{h}.wav").exists() and not raw.exists() and str(raw) not in {j["out"] for j in qjobs}:
                qjobs.append({"text": tts_text(r["text"]), "ref": str(ROOT / v["ref"]), "ref_text": v.get("ref_text", ""),
                              "seed": r.get("seed", 1), "out": str(raw)})
            continue
        if v.get("engine") == "zonos":
            from . import zonos
            emo = r.get("emotion", "neutral")
            h, _ = _key(r["text"], v, emo, r.get("fx"), r.get("length_mul", 1.0), None, r.get("seed", 1))
            raw = CACHE / f"{h}.raw.wav"
            if not (CACHE / f"{h}.wav").exists() and not raw.exists():
                CACHE.mkdir(parents=True, exist_ok=True)
                zonos.generate(tts_text(r["text"]), ROOT / v["ref"], raw, zonos.controls_for(emo, v), r.get("seed", 1))
                n_zonos += 1
            continue
        if v.get("engine") != "chatterbox":
            continue
        h, ex = _key(r["text"], v, r.get("emotion", "neutral"), r.get("fx"), r.get("length_mul", 1.0), None,
                     r.get("seed", 1))
        if (CACHE / f"{h}.wav").exists() or (CACHE / f"{h}.raw.wav").exists():
            continue
        jobs.append({"text": tts_text(r["text"]), "ref": str(ROOT / v["ref"]), "exaggeration": ex,
                     "cfg": v.get("cfg", 0.5), "temperature": v.get("temperature", 0.8),
                     "seed": r.get("seed", 1), "out": str(CACHE / f"{h}.raw.wav")})
    if qjobs:
        from . import qwen
        CACHE.mkdir(parents=True, exist_ok=True)
        n_zonos += qwen.run(qjobs)
    if not jobs:
        return n_zonos
    CACHE.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([str(VENV_PY), str(WORKER)], input=json.dumps(jobs), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Chatterbox-Worker fehlgeschlagen: {p.stderr[-800:]}")
    return len(jobs) + n_zonos


def _post(raw, out, pitch, fx, tempo=1.0):
    filt = []
    if pitch:
        filt.append(f"rubberband=pitch={2 ** (pitch / 12):.4f}:formant=preserved")
    filt.append(f"aresample={SR}")
    if abs(tempo - 1.0) > 0.01:
        filt.append(f"atempo={tempo:.3f}")
    filt.append(CLARITY)
    if fx in FX:
        filt.append(FX[fx])
    filt.append("silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                "silenceremove=start_periods=1:start_threshold=-50dB,areverse")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af", ",".join(filt), "-ac", "1",
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(out)], check=True)


def synth(text, voice, emotion="neutral", fx=None, length_mul=1.0, noise=None, seed=1):
    """Erzeugt eine Sprachzeile -> (Pfad zur 48-kHz-WAV, Samples float32 mono)."""
    voice = resolve(voice)
    h, _ = _key(text, voice, emotion, fx, length_mul, noise, seed)
    out = CACHE / f"{h}.wav"
    if out.exists():
        return out, read_wav(out)
    CACHE.mkdir(parents=True, exist_ok=True)
    if voice.get("engine") in ("chatterbox", "zonos", "qwen3"):
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
