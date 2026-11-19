"""Schnitt im Beat-Raster: Spezifikation (JSON) -> Bilder -> Video (+ Platzhalter-Beat).

Spezifikation (channels/larp/videos/<id>.json):
  bpm, shots: [{scene, beats, cam: {from: [cx, cy, zoom], to: [...]}, text, punch}]
Jede Einstellung dauert eine ganze Zahl von Schlägen – geschnitten wird immer auf dem Beat.
"""
import json
import math
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cairo
import numpy as np

from . import beat as B
from . import fx as FX
from . import hud as H
from .scenes import SCENES

ROOT = Path(__file__).resolve().parent.parent
CHANNEL = ROOT / "channels" / "larp"
W, HH, FPS = 1080, 1920, 30


def load(vid):
    p = Path(vid)
    if not p.exists():
        p = CHANNEL / "videos" / f"{vid}.json"
    spec = json.loads(p.read_text())
    cfg = json.loads((CHANNEL / "channel.json").read_text())
    spec.setdefault("system", cfg["system"])
    spec.setdefault("version", cfg["version"])
    spec["_id"] = p.stem
    return spec


def timeline(spec):
    bt = 60 / spec["bpm"]
    t, out = 0.0, []
    for i, s in enumerate(spec["shots"]):
        d = s["beats"] * bt
        out.append(dict(s, t0=t, t1=t + d, index=i))
        t += d
    return out, t


def _ease(u):
    return u * u * (3 - 2 * u)


def _cam(shot, u):
    cam = shot.get("cam", {})
    a = cam.get("from", [540, 960, 1.0])
    b = cam.get("to", [540, 960, 1.06])
    e = _ease(u)
    return [a[i] + (b[i] - a[i]) * e for i in range(3)]


def _text(ctx, lines, reveal, y=600):
    """Hook-Text im Kurzvideo-Stil, zeichenweise eingetippt."""
    size = 50
    H.font(ctx, size, True)
    total = int(reveal)
    lh = size * 1.32
    yy = y
    for ln in lines:
        s = ln[:max(0, total)]
        total -= len(ln)
        full_w = ctx.text_extents(ln).x_advance
        x = (W - full_w) / 2
        if s:
            ctx.set_source_rgba(0, 0, 0, 0.82)
            ctx.rectangle(x - 18, yy - size - 8, ctx.text_extents(s).x_advance + 36, lh + 4)
            ctx.fill()
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.move_to(x, yy)
            ctx.show_text(s)
        yy += lh + 10


def frame_at(spec, tl, t):
    shot = next((s for s in tl if s["t0"] <= t < s["t1"]), tl[-1])
    bt = 60 / spec["bpm"]
    u = (t - shot["t0"]) / (shot["t1"] - shot["t0"])
    cx, cy, z = _cam(shot, u)
    ph = (t / bt) % 1.0
    beat_no = int(t / bt + 1e-6)
    bump = math.exp(-ph * 7) * (1.0 if beat_no % 4 == 0 else 0.55)
    if beat_no < spec.get("drop_beat", 8):
        bump *= 0.35
    since = t - shot["t0"]
    punch = shot.get("punch", 0.14)
    z *= 1 + 0.022 * bump + punch * math.exp(-since * 9)
    hw, hh = W / (2 * z), HH / (2 * z)
    cx = min(max(cx, hw), W - hw)
    cy = min(max(cy, hh), HH - hh)
    shake = math.exp(-since * 14) * 10
    cx += math.sin(t * 91) * shake
    cy += math.cos(t * 77) * shake

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, HH)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    ctx.save()
    ctx.translate(W / 2, HH / 2)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)
    SCENES[shot["scene"]](ctx, t + spec.get("t_offset", 4.0), spec)
    ctx.restore()
    if shot.get("text"):
        _text(ctx, shot["text"], since * 34, shot.get("text_y", 640))
    surf.flush()
    arr = np.ndarray((HH, W, 4), np.uint8, surf.get_data()).copy()
    fxp = {
        "bump": bump,
        "flash": math.exp(-since * 16) * (0.9 if shot["index"] else 0.0) * (1.0 if shot.get("flash", True) else 0),
        "glitch": math.exp(-since * 11) * (1.0 if shot["index"] else 0.0) + (0.5 * bump if beat_no % 8 == 7 else 0),
        "chroma": math.exp(-since * 8) + 0.4 * bump,
        "mono": shot["scene"] == "mono_field",
    }
    return FX.process(arr, t, fxp, seed=shot["index"])


def _render_chunk(args):
    spec, f0, f1, out = args
    tl, _ = timeline(spec)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{HH}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15",
           "-pix_fmt", "yuv420p", "-g", "30", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame_at(spec, tl, f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


def still(vid, t, out):
    spec = load(vid)
    tl, _ = timeline(spec)
    import cv2
    cv2.imwrite(str(out), frame_at(spec, tl, t))


def render(vid, workers=4, audio=None, audio_offset=0.0):
    spec = load(vid)
    tl, dur = timeline(spec)
    vdir = CHANNEL / "out" / spec["_id"]
    work = vdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    nf = int(round(dur * FPS))
    k = max(1, workers * 2)
    bounds = [round(nf * i / k) for i in range(k + 1)]
    jobs = [(spec, bounds[i], bounds[i + 1], work / f"part{i:02d}.mp4") for i in range(k)]
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_render_chunk, jobs))
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    silent = vdir / "video_ohne_ton.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "16M", "-bufsize", "32M",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)], check=True)
    # Ton: eigener Platzhalter-Beat oder eine selbst gelieferte, lizenzierte Datei
    wav = work / "beat.wav"
    if audio:
        src = ["-ss", str(audio_offset), "-i", str(audio)]
    else:
        B.write_wav(wav, B.generate(spec["bpm"], dur, spec.get("drop_beat", 8)))
        src = ["-i", str(wav)]
    final = vdir / "final.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), *src, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-t", f"{dur:.3f}", "-movflags", "+faststart", str(final)], check=True)
    import cv2
    cv2.imwrite(str(vdir / "cover.jpg"), frame_at(spec, tl, spec.get("cover_t", tl[min(1, len(tl) - 1)]["t0"] + 1.0)),
                [cv2.IMWRITE_JPEG_QUALITY, 92])
    (vdir / "tiktok.txt").write_text(_caption(spec), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    return final, dur


def _caption(spec):
    cfg = json.loads((CHANNEL / "channel.json").read_text())
    tags = " ".join(cfg["hashtags"] + spec.get("hashtags", []))
    snd = spec.get("sound") or cfg["sounds"][0]
    return (f"{spec.get('caption', '')}\n\n{tags}\n\n"
            f"--- Checkliste TikTok-App ---\n"
            f"1. Sound wählen: {snd['title']} – {snd['artist']} (Start bei ca. {snd.get('start', '0:00')})\n"
            f"2. Originalton auf 0 % (Platzhalter-Beat), Sound auf 100 %\n"
            f"3. 'KI-generierte Inhalte' einschalten\n"
            f"4. Geschnitten auf {spec['bpm']} BPM – ggf. Sound-Startpunkt verschieben, bis die Schnitte auf dem Beat sitzen\n")
