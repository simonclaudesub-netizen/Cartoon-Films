"""Qwen3-TTS (Alibaba Qwen, Apache-2.0) – lokale Hauptstimmen mit Stimmklon (Wahl im Blindtest, 17.11.2026).

Läuft als Hilfsprozess in .venv-qwen (torch für die CPU), damit die Haupt-Umgebung schlank bleibt.
Keine externen Dienste: das Modell liegt im Hugging-Face-Zwischenspeicher (von setup.sh geladen).
Das Basis-Modell hat keine Emotions-Regler; Gefühl kommt aus Text, Satzzeichen und Nachbearbeitung.
"""
import json
import os
import subprocess
from pathlib import Path

from ..db import ROOT

VENV_PY = ROOT / ".venv-qwen" / "bin" / "python"
WORKER = Path(__file__).resolve().parent / "qwen_worker.py"
MODEL = os.environ.get("STUDIO_QWEN_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base")
HUB = ROOT / "assets" / "qwen"  # Modell-Zwischenspeicher im Projekt (gitignored), von setup.sh gefüllt
_OK = None


def _env(**extra):
    return dict(os.environ, HF_HUB_CACHE=str(HUB), HF_HUB_DISABLE_XET="1", **extra)


NEEDED = ("config.json", "model.safetensors", "vocab.json", "merges.txt",
          "speech_tokenizer/config.json", "speech_tokenizer/model.safetensors")


def model_complete():
    """Alle Modelldateien vollständig vorhanden? (abgebrochene Downloads liegen als *.incomplete in blobs/)"""
    d = HUB / ("models--" + MODEL.replace("/", "--"))
    snaps = sorted((d / "snapshots").glob("*")) if d.exists() else []
    if not snaps or any((d / "blobs").glob("*.incomplete")):
        return False
    return all((snaps[-1] / f).is_file() for f in NEEDED)


def available():
    global _OK
    if _OK is None:
        _OK = VENV_PY.exists() and model_complete() and subprocess.run(
            [str(VENV_PY), "-c", "import qwen_tts"], capture_output=True).returncode == 0
    return _OK


def run(jobs):
    """Spricht alle Aufträge in EINEM Worker-Lauf ein (Modell lädt nur einmal, ~3 Min.)."""
    if not jobs:
        return 0
    env = _env(HF_HUB_OFFLINE="1", STUDIO_QWEN_MODEL=MODEL)
    p = subprocess.run([str(VENV_PY), str(WORKER)], input=json.dumps(jobs), capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"Qwen3-Worker fehlgeschlagen: {p.stderr[-800:]}")
    missing = [j["out"] for j in jobs if not Path(j["out"]).exists()]
    if missing:
        raise RuntimeError(f"Qwen3-Worker: {len(missing)} Zeilen fehlen")
    return len(jobs)


def describe(voice):
    return f"Qwen3-TTS (Klon: {Path(voice['ref']).name})"
