"""Systemprüfung: Sind alle lokalen Werkzeuge, Modelle und Zugänge vorhanden?"""
import importlib
import shutil
import subprocess
from pathlib import Path

from . import db
from .publish import tiktok, youtube

def _required_voices():
    out = set()
    for c in db.characters().values():
        v = c["voice"]
        if v.get("engine") == "chatterbox":
            out.add(("ref", v["ref"]))
            v = v.get("fallback", {})
        if v.get("model"):
            out.add(("piper", v["model"]))
    return sorted(out)


def run():
    out = []

    def add(name, ok, detail="", kind="pflicht"):
        out.append({"name": name, "ok": bool(ok), "detail": detail, "kind": kind})

    add("ffmpeg", shutil.which("ffmpeg"), _ver(["ffmpeg", "-version"]))
    for mod, label in (("cairo", "Cairo (Vektorgrafik)"), ("piper", "Piper TTS"), ("faster_whisper", "Whisper (QC)"),
                       ("cv2", "OpenCV (Linse)"), ("numpy", "NumPy"), ("PIL", "Pillow"), ("requests", "requests")):
        try:
            importlib.import_module(mod)
            add(label, True)
        except Exception as e:
            add(label, False, str(e))
    venv = db.ROOT / ".venv-tts" / "bin" / "python"
    ok = venv.exists() and subprocess.run([str(venv), "-c", "import chatterbox"], capture_output=True).returncode == 0
    add("Chatterbox Multilingual (.venv-tts)", ok, "Hauptstimmen, MIT-Lizenz")
    for kind, v in _required_voices():
        p = db.ROOT / v if kind == "ref" else db.ROOT / "assets" / "voices" / f"{v}.onnx"
        add(f"{'Referenzstimme' if kind == 'ref' else 'Piper-Stimme'} {Path(v).stem}", p.exists())
    fl = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
    add("Schrift Bangers", "Bangers" in fl)
    add("Schrift Comic Neue", "Comic Neue" in fl)
    add("Whisper-Modell 'small'", any((db.ROOT / "assets" / "whisper").glob("**/model.bin")))
    add("YouTube-Zugang", youtube.configured(), "config/secrets/youtube.json oder YT_*-Variablen", kind="zugang")
    add("TikTok-Zugang", tiktok.configured(), "config/secrets/tiktok.json", kind="zugang")
    return out


def _ver(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout.split("\n")[0][:60]
    except Exception:
        return ""
