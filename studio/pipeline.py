"""Produktions-Pipeline mit automatischer Fehlerkorrektur (max. 3 Versuche).

produce(ep_id):
  1. Zeitleiste (TTS) -> 2. Video (nur geänderte Einstellungen werden neu gerendert)
  3. Tonmischung -> 4. Endschnitt mit Untertiteln -> 5. QC
  6. Bei < 90 Punkten: betroffene Teile korrigieren und erneut prüfen.
Nach dem 3. erfolglosen Versuch wird die Episode gesperrt ("abgelehnt").
"""
import json
import time
import traceback

from . import db, qc, render, subtitles, timeline
from .modelsheet import look_hash

MAX_ATTEMPTS = 3


def _load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def lock_model_sheets(series_id):
    """Sperrt das aktuelle Aussehen aller Serienfiguren (Figurenkonsistenz)."""
    s = db.series(series_id)
    chars = db.characters()
    hashes = s.setdefault("model_sheet_hashes", {})
    for cid in s.get("cast", []):
        hashes.setdefault(cid, look_hash(chars[cid]["look"]))
    db.save_series(s)
    return hashes


def fixes_for(res, tl, ov):
    """Leitet aus dem QC-Ergebnis konkrete Korrekturen ab. Gibt Liste der Maßnahmen zurück."""
    actions = []
    g = ov.setdefault("global", {})
    lines_ov = ov.setdefault("lines", {})
    for t in res["line_tests"]:
        if not t["ok"]:
            lo = lines_ov.setdefault(t["key"], {})
            if db.character(t["speaker"])["voice"].get("engine") == "chatterbox":
                lo["seed"] = lo.get("seed", 1) + 1  # neue Aufnahme ("Take") statt Tempo-Änderung
                actions.append(f"Zeile {t['key']} neu einsprechen, Take {lo['seed']} (Ähnlichkeit {t['similarity']})")
            else:
                lo["length_mul"] = round(lo.get("length_mul", 1.0) * 1.1, 3)
                lo["noise"] = round(max(0.3, lo.get("noise", 0.6) - 0.15), 2)
                actions.append(f"Zeile {t['key']} langsamer & deutlicher neu sprechen (Ähnlichkeit {t['similarity']})")
    for c in res["checks"]:
        if c["ok"]:
            continue
        n = c["name"]
        if n.startswith("Dauer"):
            if res["duration"] > 60:
                # Zielgenau kürzen: Pausen tragen den Großteil, Sprechtempo höchstens -10 %
                excess = res["duration"] - 57.0
                pads = sum(s.get("pad_start", 0.3) + s.get("pad_end", 0.45) for s in tl["shots"]) * g.get("pad_mul", 1.0)
                factor = max(0.3, 1 - excess / max(pads, 1e-3))
                g["pad_mul"] = round(g.get("pad_mul", 1.0) * factor, 3)
                g["gap"] = 0.12
                if factor <= 0.3:
                    g["length_mul"] = round(max(0.9, g.get("length_mul", 1.0) * 0.95), 3)
                actions.append(f"Episode {res['duration']:.1f} s zu lang: Pausen auf {factor:.0%} kürzen")
            else:
                g["pad_mul"] = round(g.get("pad_mul", 1.0) * 1.4, 3)
                actions.append("Episode zu kurz: Pausen verlängern")
        elif n.startswith("Lautheit") or n.startswith("True Peak") or n.startswith("Keine Übersteuerung"):
            g["music_gain"] = round(g.get("music_gain", 0.32) * 0.85, 3)
            g["sfx_gain"] = round(g.get("sfx_gain", 0.8) * 0.85, 3)
            actions.append("Ton: Musik/Effekte leiser, Normalisierung wiederholen")
        elif n.startswith("Max.") or n.startswith("Mindest-Lesezeit"):
            g["max_chars"] = max(16, g.get("max_chars", subtitles.MAX_CHARS) - 4) if n.startswith("Max.") else \
                g.get("max_chars", subtitles.MAX_CHARS) + 6
            actions.append("Untertitel neu aufteilen")
        elif n.startswith("Keine eingefrorenen"):
            g["force_motion"] = True
            actions.append("Statische Einstellungen bekommen Kamerafahrt")
        elif n.startswith("Sprechtempo"):
            for key in res.get("fast_lines", []):
                lo = lines_ov.setdefault(key, {})
                lo["length_mul"] = round(lo.get("length_mul", 1.0) * 1.15, 3)
            actions.append(f"Zu schnelle Zeilen {res.get('fast_lines')} langsamer sprechen")
    return actions


MAX_TAKES = 4


def recording_session(sc, chars, ov, ep_id):
    """Sprachaufnahme mit Takes: jede Zeile wird abgehört, fehlerhafte Zeilen werden neu eingesprochen;
    am Ende gewinnt pro Zeile der BESTE Take."""
    lines_ov = ov.setdefault("lines", {})
    best = {}  # key -> (score, seed)
    tl = timeline.build(sc, chars, ov)
    for take in range(1, MAX_TAKES + 1):
        bad = []
        for s in tl["shots"]:
            for ln in s.get("lines", []):
                if chars[ln["speaker"]]["voice"].get("engine") != "chatterbox":
                    continue
                key = ln["_key"]
                seed = lines_ov.get(key, {}).get("seed", 1)
                heard = qc.transcribe(ln["_wav"])
                txt = ln.get("tts") or ln["text"]
                sim, extra = qc.similarity(txt, heard), qc.trailing_extra(txt, heard)
                score = sim - (0.3 if extra else 0)
                if key not in best or score > best[key][0]:
                    best[key] = (score, seed)
                if sim < qc.LINE_MIN or extra:
                    bad.append((key, round(sim, 2), heard))
        if not bad:
            db.log(f"[{ep_id}] Sprachaufnahme: alle Zeilen sauber (Runde {take})")
            return tl
        if take == MAX_TAKES:
            break
        for key, sim, heard in bad:
            lines_ov.setdefault(key, {})["seed"] = 1 + take + 10 * (take - 1)  # neue, nie benutzte Takes
        db.log(f"[{ep_id}] Sprachaufnahme Runde {take}: neue Takes für {bad}")
        tl = timeline.build(sc, chars, ov)
    # bester Take je Zeile
    for key, (score, seed) in best.items():
        lines_ov.setdefault(key, {})["seed"] = seed
    db.log(f"[{ep_id}] Sprachaufnahme: beste Takes übernommen, offen: {[b[0] for b in bad]}", "WARN")
    return timeline.build(sc, chars, ov)


def produce(ep_id, max_attempts=MAX_ATTEMPTS, workers=4):
    ep = db.episode_dir(ep_id)
    script = json.loads((ep / "script.json").read_text(encoding="utf-8"))
    chars = db.characters()
    if script.get("series"):
        lock_model_sheets(script["series"])
    ov_path = ep / "overrides.json"
    ov = _load(ov_path, {})
    work = ep / "work"
    work.mkdir(parents=True, exist_ok=True)
    attempts = []
    db.set_status(ep_id, "in_produktion")
    for attempt in range(1, max_attempts + 1):
        t0 = time.time()
        db.log(f"[{ep_id}] Versuch {attempt}: Zeitleiste + Stimmen")
        try:
            sc = json.loads(json.dumps(script))
            if ov.get("global", {}).get("force_motion"):
                for s in sc["shots"]:
                    s.setdefault("camera", {}).setdefault("move", "push_in")
            tl = recording_session(sc, chars, ov, ep_id)
            ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=2), encoding="utf-8")
            cs = script.get("cover_shot")
            if cs is not None and 0 <= cs < len(tl["shots"]):
                tl["cover_t"] = tl["shots"][cs]["_t0"] + tl["shots"][cs]["_dur"] * 0.6
            db.log(f"[{ep_id}] Laufzeit {tl['duration']:.1f} s, {len(tl['shots'])} Einstellungen – rendere Video")
            video, rep = render.render_video(tl, work, workers)
            db.log(f"[{ep_id}] gerendert: {rep['rendered']} | aus Cache: {rep['cached']}")
            audio = render.mix_audio(tl, work, ov)
            final = ep / "final.mp4"
            mc = ov.get("global", {}).get("max_chars", subtitles.MAX_CHARS)
            render.final_mux(tl, work, video, audio, final, mc)
            db.log(f"[{ep_id}] Qualitätskontrolle läuft")
            res = qc.run(ep_id, final, tl, script, rep, mc)
        except Exception as e:
            db.log(f"[{ep_id}] Fehler in Versuch {attempt}: {e!r}\n{traceback.format_exc()}", "ERROR")
            attempts.append({"attempt": attempt, "error": repr(e)})
            db.set_status(ep_id, "fehler", attempts=attempts)
            continue
        (ep / f"qc_attempt{attempt}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        (ep / "qc_report.md").write_text(qc.report_md(res, attempt), encoding="utf-8")
        (ep / "timeline.json").write_text(json.dumps({k: v for k, v in tl.items()}, ensure_ascii=False, default=str),
                                          encoding="utf-8")
        entry = {"attempt": attempt, "score": res["score"], "passed": res["passed"], "critical": res["critical"],
                 "seconds": round(time.time() - t0, 1), "rendered_shots": rep["rendered"]}
        db.log(f"[{ep_id}] QC Versuch {attempt}: {res['score']} Punkte – {'bestanden' if res['passed'] else 'nicht bestanden'}")
        if res["passed"]:
            attempts.append(entry)
            db.set_status(ep_id, "freigabe_ausstehend", score=res["score"], attempts=attempts,
                          duration=res["duration"], final=str(final))
            cfg = json.loads((db.ROOT / "config" / "studio.json").read_text(encoding="utf-8"))
            if not cfg["publishing"].get("require_manual_approval", True):
                db.set_status(ep_id, "freigegeben", approved_by="qc-automatik")
                db.log(f"[{ep_id}] automatisch freigegeben (QC {res['score']} >= {qc.PASS_SCORE})")
            return res
        before = json.dumps(ov, sort_keys=True)
        actions = fixes_for(res, tl, ov)
        if json.dumps(ov, sort_keys=True) == before:
            actions = []  # Korrektur bewirkt nichts mehr -> abbrechen statt Rechenzeit verschwenden
        entry["fixes"] = actions
        attempts.append(entry)
        ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=2), encoding="utf-8")
        db.log(f"[{ep_id}] Korrekturen: {actions or ['keine automatische Korrektur möglich']}", "WARN")
        if not actions:
            break
    db.set_status(ep_id, "abgelehnt", attempts=attempts)
    db.log(f"[{ep_id}] Episode nach {len(attempts)} Versuchen abgelehnt – wird NICHT veröffentlicht", "ERROR")
    return None
