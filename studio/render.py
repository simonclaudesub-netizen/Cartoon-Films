"""Rendering: Einstellungen -> Videosegmente, Tonmischung, Endschnitt (1080x1920, 30 fps)."""
import hashlib
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from . import db
from . import subtitles
from .audio import music, sfx, tts
from .scene import ShotRenderer

def _engine_hash():
    """Hash über den gesamten Zeichen-Code: jede Code-Änderung macht den Shot-Cache ungültig."""
    h = hashlib.sha1()
    base = Path(__file__).resolve().parent
    for p in sorted(list((base / "draw").glob("*.py")) + [base / "scene.py"]):
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


ENGINE_VERSION = _engine_hash()
SR = tts.SR
FONTS = db.ROOT / "assets" / "fonts"


def _shot_hash(shot, label):
    data = {k: v for k, v in shot.items() if k not in ("_wav", "_t0")}
    return hashlib.sha1(json.dumps([data, label, ENGINE_VERSION], sort_keys=True, default=str).encode()).hexdigest()[:16]


def _render_shot(args):
    shot, label, out, fps = args
    chars = db.characters()
    r = ShotRenderer(shot, chars, label, fps)
    vf = ["format=yuv420p"]  # Linsenverzeichnung passiert bereits im Compositor (scene.py)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", "1080x1920",
           "-r", str(fps), "-i", "-", "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
           "-g", "30", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    errors = 0
    for i in range(shot["_frames"]):
        try:
            surf = r.frame(i / fps)
            p.stdin.write(bytes(surf.get_data()))
        except Exception as e:  # Bildfehler protokollieren statt abstürzen
            errors += 1
            db.log(f"Frame-Fehler in Einstellung {shot['_index']} Bild {i}: {e!r}", "ERROR")
            p.stdin.write(bytes(1080 * 1920 * 4))
    p.stdin.close()
    p.wait()
    return {"index": shot["_index"], "errors": errors, "ok": p.returncode == 0}


def render_video(tl, work, workers=4):
    seg_dir = work / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    jobs, segs, report = [], [], {"rendered": [], "cached": [], "frame_errors": 0}
    for s in tl["shots"]:
        h = _shot_hash(s, tl["label"])
        out = seg_dir / f"shot{s['_index']:02d}_{h}.mp4"
        segs.append(out)
        if out.exists():
            report["cached"].append(s["_index"])
        else:
            for old in seg_dir.glob(f"shot{s['_index']:02d}_*.mp4"):
                old.unlink()
            jobs.append((s, tl["label"], out, tl["fps"]))
    if jobs:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for res in ex.map(_render_shot, jobs):
                report["rendered"].append(res["index"])
                report["frame_errors"] += res["errors"]
                if not res["ok"]:
                    raise RuntimeError(f"ffmpeg-Fehler in Einstellung {res['index']}")
    lst = work / "segments.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    out = work / "video_noaudio.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(out)], check=True)
    return out, report


def mix_audio(tl, work, overrides=None):
    ov = (overrides or {}).get("global", {})
    n = int(tl["duration"] * SR) + SR
    dia, fx, mus = np.zeros(n), np.zeros(n), np.zeros(n)

    def place(buf, x, t, gain=1.0):
        o = int(t * SR)
        e = min(len(buf), o + len(x))
        if o < e:
            buf[o:e] += x[:e - o] * gain

    for s in tl["shots"]:
        for ln in s.get("lines", []):
            place(dia, tts.read_wav(ln["_wav"]), s["_t0"] + ln["_start"], ln.get("gain", 1.0))
        for e in s.get("sfx", []):
            place(fx, sfx.make(e["name"]), s["_t0"] + e.get("at", 0.0), e.get("gain", 1.0))
    # Musik: zusammenhängende Abschnitte gleicher Stimmung
    segs, cur = [], None
    for s in tl["shots"]:
        mood = s.get("music", "silence")
        if cur and cur[0] == mood:
            cur[2] = s["_t0"] + s["_dur"]
        else:
            cur = [mood, s["_t0"], s["_t0"] + s["_dur"]]
            segs.append(cur)
    for i, (mood, a, b) in enumerate(segs):
        place(mus, music.generate(mood, b - a + 0.4, seed=i + 3), a)
    # Ducking: Musik leiser, wenn gesprochen wird
    hop = SR // 100
    env = np.sqrt(np.convolve(dia ** 2, np.ones(hop) / hop, mode="same"))
    duck = np.clip(env / 0.03, 0, 1)
    k = np.ones(int(0.25 * SR)) / int(0.25 * SR)
    duck = np.convolve(duck, k, mode="same")
    mus *= (1 - 0.82 * duck) * ov.get("music_gain", 0.32)
    mix = dia * 1.0 + fx * ov.get("sfx_gain", 0.8) + mus
    mix = mix[:int(tl["duration"] * SR)]
    peak = np.max(np.abs(mix)) + 1e-9
    if peak > 0.98:
        mix *= 0.98 / peak
    raw = work / "mix_raw.wav"
    _write_wav(raw, mix)
    # Zwei-Pass-Lautheitsnormalisierung auf -14 LUFS (Plattform-Standard)
    target = ov.get("lufs", -14.0)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af",
                           f"pan=stereo|c0=c0|c1=c0,loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rfind("{"):meas.rfind("}") + 1])
    out = work / "mix.wav"
    af = (f"pan=stereo|c0=c0|c1=c0,loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
          f"aresample={SR}")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af", af, "-ar", str(SR), "-ac", "2",
                    str(out)], check=True)
    return out


def _write_wav(path, x):
    import wave
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def final_mux(tl, work, video, audio, out, max_chars=subtitles.MAX_CHARS):
    ass = work / "subs.ass"
    ev = subtitles.write_ass(tl, ass, max_chars)
    vf = f"subtitles={ass}:fontsdir={FONTS}"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-i", str(audio), "-vf", vf,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart",
                    str(out)], check=True)
    # Vorschaubild (Cover) aus der stärksten Einstellung
    cover_t = tl.get("cover_t", 1.0)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(cover_t), "-i", str(out), "-frames:v", "1",
                    str(out.parent / "cover.jpg")], check=True)
    return ev
