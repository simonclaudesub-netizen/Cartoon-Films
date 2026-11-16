"""Automatische Qualitätskontrolle (0-100 Punkte, Mindestwert 90).

Kategorien und Höchstpunkte:
  technik 15 | ton 15 | stimmen 20 | bild 15 | konsistenz 10 | story 15 | untertitel 10
Kritische Fehler (z. B. falsches Format, kein Ton, unbekannte Figur) begrenzen
die Gesamtpunktzahl auf 59 – solche Videos werden nie veröffentlicht.
"""
import difflib
import json
import re
import subprocess

import numpy as np

from . import db, subtitles
from .audio import tts
from .modelsheet import look_hash

PASS_SCORE = 90
LINE_MIN = 0.85  # Mindest-Ähnlichkeit je Zeile; schlechtere Zeilen blockieren die Veröffentlichung


def line_min(text):
    """Lange Sätze strenger prüfen: dort verändert ein einzelnes falsches Wort die Ähnlichkeit kaum."""
    n = len(text.split())
    return LINE_MIN if n < 8 else min(0.94, LINE_MIN + 0.0075 * (n - 8))
_whisper = None


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    return json.loads(r.stdout)


def loudness(path):
    r = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", txt).group(1))
    tp = re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", txt)
    return I, float(tp.group(1)) if tp else 0.0


def detect(path, flt, key):
    r = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", flt, "-an", "-f", "null", "-"])
    return r.stderr


NUM = {"null": "0", "eins": "1", "ein": "1", "zwei": "2", "drei": "3", "vier": "4", "fünf": "5", "sechs": "6",
       "sieben": "7", "acht": "8", "neun": "9", "zehn": "10", "elf": "11", "zwölf": "12"}


FILLERS = r"\b(äh+m?|öh+m?|hm+|ähm|uh+|ah)\b"


def _norm(s):
    s = s.lower()
    s = re.sub(FILLERS, " ", s)  # Whisper schreibt Füllwörter grundsätzlich nicht mit
    s = re.sub(r"\b(" + "|".join(NUM) + r")\b", lambda m: NUM[m.group(1)] if m.group(1) != "ein" else "ein", s)
    s = re.sub(r"[^\wäöüß ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def transcribe(wav):
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("small", device="cpu", compute_type="int8",
                                download_root=str(db.ROOT / "assets" / "whisper"))
    audio = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(wav), "-ar", "16000", "-ac", "1",
                                          "-f", "f32le", "-"], capture_output=True).stdout, dtype=np.float32)
    segs, _ = _whisper.transcribe(audio, language="de", beam_size=5, vad_filter=False)
    return " ".join(s.text.strip() for s in segs)


def trailing_extra(expected, got):
    """Wörter, die die Stimme NACH dem Satzende zusätzlich 'erfunden' hat (Nachlaut/Halluzination)."""
    e, g = _norm(tts.tts_text(expected)).split(), _norm(got).split()
    blocks = [b for b in difflib.SequenceMatcher(None, e, g).get_matching_blocks() if b.size]
    if not blocks:
        return []
    last = blocks[-1]
    tail = g[last.b + last.size:] if last.a + last.size >= len(e) - 1 else []
    return tail + repeated_words(expected, got)


def repeated_words(expected, got):
    """Doppelt gesprochene Wörter/Silben ('Brandt-Brandt', 'tschüss tschüss'), die nicht im Text stehen."""
    raw = [w for w in re.split(r"[\s,.!?;:…\"„“]+", got.lower()) if w]
    e = _norm(tts.tts_text(expected)).split()
    exp_pairs = {(a, b) for a, b in zip(e, e[1:])}
    out = []
    for w in raw:
        parts = [x for x in w.split("-") if x]
        if len(parts) >= 2 and len(set(parts)) == 1 and len(parts[0]) >= 3:
            out.append(w)
    g = _norm(got).split()
    for a, b in zip(g, g[1:]):
        if a == b and len(a) >= 3 and (a, b) not in exp_pairs:
            out.append(f"{a} {b}")
    return out


def similarity(expected, got):
    """Kombiniert Zeichen- (40 %) und Wort-Übereinstimmung (60 %). Wort-Ebene deckt Verwechslungen
    wie 'dann bin' -> 'fänd ihn' auf, die auf Zeichenebene kaum auffallen."""
    g = _norm(got)
    best = 0.0
    for c in (_norm(expected), _norm(tts.tts_text(expected))):
        ch = difflib.SequenceMatcher(None, c, g).ratio()
        wd = difflib.SequenceMatcher(None, c.split(), g.split()).ratio()
        best = max(best, 0.4 * ch + 0.6 * wd)
    return best


def contact_sheet(video, tl, out):
    times = [s["_t0"] + s["_dur"] * 0.6 for s in tl["shots"]]
    cols = 6
    rows = (len(times) + cols - 1) // cols
    from PIL import Image
    sheet = Image.new("RGB", (cols * 270, rows * 480), "black")
    for i, t in enumerate(times):
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale=270:480", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
        if len(r.stdout) == 270 * 480 * 3:
            im = Image.frombytes("RGB", (270, 480), r.stdout)
            sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
    sheet.save(out)
    return out


def frame_stats(video, duration, step=0.5):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf", f"fps={1 / step},scale=108:192",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    n = len(r.stdout) // (108 * 192)
    fr = np.frombuffer(r.stdout[:n * 108 * 192], np.uint8).reshape(n, 192, 108).astype(np.float32)
    return [float(f.std()) for f in fr]


def run(ep_id, video, tl, script, render_report, max_chars=subtitles.MAX_CHARS):
    chars = db.characters()
    series = db.series(script["series"]) if script.get("series") else {}
    res = {"checks": [], "critical": [], "categories": {}, "line_tests": []}

    def check(cat, name, ok, pts, maxpts, detail="", critical=False):
        res["checks"].append({"cat": cat, "name": name, "ok": bool(ok), "points": round(pts, 2), "max": maxpts,
                              "detail": detail})
        if critical and not ok:
            res["critical"].append(f"{cat}: {name} ({detail})")

    # ---------------- Technik (15)
    pr = probe(video)
    vs = next((s for s in pr["streams"] if s["codec_type"] == "video"), {})
    as_ = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"])
    size_mb = int(pr["format"]["size"]) / 1e6
    okres = vs.get("width") == 1080 and vs.get("height") == 1920
    check("technik", "Auflösung 1080x1920 (9:16)", okres, 5 if okres else 0, 5, f"{vs.get('width')}x{vs.get('height')}", True)
    fps = eval(vs.get("r_frame_rate", "0/1"))
    check("technik", "30 fps", abs(fps - 30) < 0.1, 2 if abs(fps - 30) < 0.1 else 0, 2, f"{fps:.2f}")
    okd = 30 <= dur <= 60
    check("technik", "Dauer 30-60 s", okd, 4 if okd else (2 if 28 <= dur <= 62 else 0), 4, f"{dur:.1f} s",
          critical=not (28 <= dur <= 62))
    okc = vs.get("codec_name") == "h264" and vs.get("pix_fmt") == "yuv420p" and as_ is not None and as_["codec_name"] == "aac"
    check("technik", "H.264/yuv420p + AAC", okc, 2 if okc else 0, 2, f"{vs.get('codec_name')}/{vs.get('pix_fmt')}")
    check("technik", "Dateigröße < 250 MB", size_mb < 250, 2 if size_mb < 250 else 0, 2, f"{size_mb:.1f} MB")

    # ---------------- Ton (15)
    if as_ is None:
        check("ton", "Tonspur vorhanden", False, 0, 15, "keine Tonspur", True)
    else:
        I, tp = loudness(video)
        okI = abs(I - (-14)) <= 1.5
        check("ton", "Lautheit -14 LUFS ±1,5", okI, 6 if okI else max(0, 6 - abs(I + 14)), 6, f"{I:.1f} LUFS")
        check("ton", "True Peak ≤ -1 dBTP", tp <= -1.0, 4 if tp <= -1.0 else (2 if tp <= 0 else 0), 4, f"{tp:.1f} dBTP")
        mix = tts.read_wav(video.parent / "work" / "mix.wav") if (video.parent / "work" / "mix.wav").exists() else None
        clip = float(np.mean(np.abs(mix) > 0.995)) if mix is not None else 0
        check("ton", "Keine Übersteuerung", clip < 1e-4, 2 if clip < 1e-4 else 0, 2, f"{clip * 100:.3f} % Samples")
        okA = I > -30
        check("ton", "Ton hörbar (nicht stumm)", okA, 3 if okA else 0, 3, f"{I:.1f} LUFS", True)

    # ---------------- Stimmen / Verständlichkeit (20)
    sims = []
    for s in tl["shots"]:
        for ln in s.get("lines", []):
            got = transcribe(ln["_wav"])
            sim = similarity(ln.get("tts") or ln["text"], got)
            extra = trailing_extra(ln.get("tts") or ln["text"], got)
            sims.append(sim)
            res["line_tests"].append({"key": ln["_key"], "speaker": ln["speaker"], "text": ln["text"], "heard": got,
                                      "similarity": round(sim, 3), "extra": extra,
                                      "ok": sim >= line_min(ln["text"]) and not extra})
    avg = float(np.mean(sims)) if sims else 0
    bad = [t for t in res["line_tests"] if not t["ok"]]
    pts = 20 * max(0.0, min(1.0, (avg - 0.6) / 0.3)) - 3 * len(bad)
    check("stimmen", "Sprachverständlichkeit (Whisper-Abgleich)", avg >= 0.85 and not bad, max(0, pts), 20,
          f"Ø {avg:.2f}, {len(bad)} Zeile(n) unter Mindestwert ({LINE_MIN}, lange Sätze strenger) oder mit Nachlaut/Wiederholung")
    for t in bad:
        res.setdefault("blocking", []).append(f"Zeile {t['key']} ({t['speaker']}): gehört '{t['heard']}'")

    # ---------------- Bild & Animation (15)
    fe = render_report.get("frame_errors", 0)
    check("bild", "Keine Render-Fehler", fe == 0, max(0, 5 - fe), 5, f"{fe} fehlerhafte Bilder", critical=fe > 10)
    allowed = []
    for s in tl["shots"]:
        if s.get("blackout_at") is not None:
            allowed.append((s["_t0"] + s["blackout_at"] - 0.2, s["_t0"] + s["_dur"] + 0.2))
    bl = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", detect(video, "blackdetect=d=0.4:pix_th=0.06", "black"))
    unexpected = [(float(a), float(b)) for a, b in bl
                  if not any(lo <= float(a) and float(b) <= hi for lo, hi in allowed)]
    check("bild", "Keine ungeplanten Schwarzbilder", not unexpected, 4 if not unexpected else 0, 4, str(unexpected))
    fz = re.findall(r"freeze_start: ([\d.]+)", detect(video, "freezedetect=n=0.002:d=2.5", "freeze"))
    fz = [float(x) for x in fz if not any(lo <= float(x) <= hi for lo, hi in allowed)]
    check("bild", "Keine eingefrorenen Bilder > 2,5 s", not fz, 4 if not fz else 0, 4, str(fz))
    stds = frame_stats(video, dur)
    flat = sum(1 for i, v in enumerate(stds) if v < 4 and not any(lo <= i * 0.5 <= hi for lo, hi in allowed))
    check("bild", "Bildinhalt vorhanden (kein Leerbild)", flat == 0, 2 if flat == 0 else 0, 2, f"{flat} leere Stichproben")

    # ---------------- Figurenkonsistenz (10)
    used = {c["id"] for s in tl["shots"] for c in s.get("characters", [])} | \
           {ln["speaker"] for s in tl["shots"] for ln in s.get("lines", [])}
    missing = [c for c in used if c not in chars]
    check("konsistenz", "Alle Figuren in der Datenbank", not missing, 4 if not missing else 0, 4, str(missing), True)
    locked = series.get("model_sheet_hashes", {})
    drift = [c for c in used if c in chars and c in locked and look_hash(chars[c]["look"]) != locked[c]]
    unlocked = [c for c in used if c in chars and c not in locked]
    okh = not drift and not unlocked
    check("konsistenz", "Aussehen = gesperrtes Model-Sheet", okh, 6 if okh else (3 if not drift else 0), 6,
          f"abweichend: {drift}, nicht gesperrt: {unlocked}")

    # ---------------- Story & Dramaturgie (15)
    first = tl["shots"][0]
    hook_t = min([ln["_start"] for ln in first.get("lines", [])] + [0.0 if first.get("caption") else 99] +
                 [e.get("at", 99) for e in first.get("sfx", [])])
    check("story", "Hook in der 1. Sekunde", hook_t <= 1.0, 3 if hook_t <= 1.0 else 0, 3, f"{hook_t:.2f} s")
    end = tl["shots"][-1].get("endcard") or {}
    okcl = bool(script.get("cliffhanger")) and set(end.get("options", {})) >= {"A", "B"}
    check("story", "Cliffhanger + A/B-Abstimmung", okcl, 4 if okcl else 0, 4, "")
    lines = [ln for s in tl["shots"] for ln in s.get("lines", [])]
    long_lines = [ln["text"] for ln in lines if len(ln["text"].split()) > 22]
    check("story", "Zeilen ≤ 22 Wörter", not long_lines, 2 if not long_lines else 0, 2, str(long_lines))
    fast_ln = [ln for ln in lines if len(ln["text"].split()) >= 5 and len(ln["text"].split()) / max(ln["_dur"], 0.1) > 4.0]
    fast = [ln["text"] for ln in fast_ln]
    res["fast_lines"] = [ln["_key"] for ln in fast_ln]
    check("story", "Sprechtempo ≤ 4 Wörter/s", not fast, 2 if not fast else 0, 2, str(fast))
    badshots = [s["_index"] for s in tl["shots"] if not (1.0 <= s["_dur"] <= 8.5)]
    check("story", "Einstellungslänge 1-8,5 s (Tempo)", not badshots, 2 if not badshots else 0, 2, str(badshots))
    cast = set(series.get("cast", [])) or used
    outsiders = [c for c in used if c not in cast]
    check("story", "Nur Figuren aus dem Serien-Cast", not outsiders, 2 if not outsiders else 0, 2, str(outsiders))

    # ---------------- Untertitel & Schnitt (10)
    ev = subtitles.events(tl, max_chars)
    covered = {(e["speaker"], e["text"]) for e in ev}
    sub_lines = [ln for ln in lines if not ln.get("no_sub")]
    words_ev = " ".join(e["text"] for e in ev).split()
    words_ln = " ".join(ln["text"] for ln in sub_lines).split()
    okcov = words_ev == words_ln
    check("untertitel", "Jede Dialogzeile untertitelt", okcov, 4 if okcov else 0, 4, f"{len(ev)} Einblendungen")
    toolong = [e["text"] for e in ev if len(e["text"]) > max_chars + 4]
    check("untertitel", f"Max. {max_chars + 4} Zeichen je Einblendung", not toolong, 2 if not toolong else 0, 2, str(toolong))
    short = [e["text"] for e in ev if e["end"] - e["start"] < 0.4]
    check("untertitel", "Mindest-Lesezeit 0,4 s", not short, 2 if not short else (1 if len(short) <= 2 else 0), 2, str(short))
    overlap = any(b["start"] < a["end"] - 1e-3 for a, b in zip(ev, ev[1:])) or any(e["end"] > dur + 0.05 for e in ev)
    check("untertitel", "Keine Überlappung, innerhalb der Laufzeit", not overlap, 2 if not overlap else 0, 2, "")

    for c in res["checks"]:
        cat = res["categories"].setdefault(c["cat"], {"points": 0, "max": 0})
        cat["points"] = round(cat["points"] + c["points"], 2)
        cat["max"] += c["max"]
    total = round(sum(c["points"] for c in res["checks"]), 1)
    if res["critical"]:
        total = min(total, 59)
    res["score"] = total
    res.setdefault("blocking", [])
    res["passed"] = total >= PASS_SCORE and not res["critical"] and not res["blocking"]
    res["duration"] = dur
    res["contact_sheet"] = str(contact_sheet(video, tl, video.parent / "qc_contact.png"))
    return res


def report_md(res, attempt):
    out = [f"# QC-Bericht – Versuch {attempt}", "", f"**Gesamt: {res['score']} / 100** – "
           f"{'BESTANDEN' if res['passed'] else 'NICHT BESTANDEN'} (Mindestwert {PASS_SCORE})", ""]
    if res["critical"]:
        out += ["**Kritische Fehler:**", *[f"- {c}" for c in res["critical"]], ""]
    if res.get("blocking"):
        out += ["**Muss korrigiert werden (blockiert Veröffentlichung):**", *[f"- {c}" for c in res["blocking"]], ""]
    out += ["| Kategorie | Punkte |", "|---|---|"]
    out += [f"| {k} | {v['points']} / {v['max']} |" for k, v in res["categories"].items()]
    out += ["", "| Prüfung | OK | Punkte | Detail |", "|---|---|---|---|"]
    out += [f"| {c['name']} | {'✅' if c['ok'] else '❌'} | {c['points']}/{c['max']} | {c['detail']} |" for c in res["checks"]]
    out += ["", "## Sprachtest (Whisper hört jede Zeile ab)", "", "| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |",
            "|---|---|---|---|---|"]
    out += [f"| {t['key']} | {t['speaker']} | {t['text']} | {t['heard']} | {t['similarity']} |" for t in res["line_tests"]]
    return "\n".join(out) + "\n"
