"""Freigabe, Veröffentlichung und Abstimmungs-Auswertung.

Regel: Ein Video wird NUR veröffentlicht, wenn
  1. die QC bestanden ist (>= 90 Punkte, keine kritischen Fehler),
  2. es freigegeben wurde (`approve`), solange require_manual_approval=true,
  3. publishing.enabled=true in config/studio.json steht und Zugangsdaten vorhanden sind.
"""
import datetime as dt
import json
from zoneinfo import ZoneInfo

from . import db
from .publish import tiktok, votes, youtube

CONFIG = db.ROOT / "config" / "studio.json"


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def approve(ep_id, by="mensch"):
    st = db.status(ep_id)
    if st.get("state") not in ("freigabe_ausstehend", "freigegeben"):
        raise SystemExit(f"Nicht freigebbar – Status ist '{st.get('state')}' (QC muss bestanden sein).")
    db.set_status(ep_id, "freigegeben", approved_by=by)
    db.log(f"[{ep_id}] freigegeben von {by}")


def _meta(ep_id):
    sc = json.loads((db.episode_dir(ep_id) / "script.json").read_text(encoding="utf-8"))
    meta = dict(sc["publish"])
    tl_p = db.episode_dir(ep_id) / "timeline.json"
    if tl_p.exists():
        meta["cover_ms"] = int(json.loads(tl_p.read_text()).get("cover_t", 1.0) * 1000)
    return sc, meta


def publish_slot(cfg, now=None, min_lead_min=20):
    """Nächster Veröffentlichungstermin (z. B. 18:00 Europe/Berlin) als UTC-ISO-String:
    heute, wenn noch mind. 20 Minuten Vorlauf, sonst morgen. None = kein Termin konfiguriert."""
    sch = cfg.get("schedule", {})
    if not sch.get("publish_time"):
        return None
    tz = ZoneInfo(sch.get("timezone", "Europe/Berlin"))
    now = now or dt.datetime.now(tz)
    h, m = map(int, sch["publish_time"].split(":"))
    slot = now.astimezone(tz).replace(hour=h, minute=m, second=0, microsecond=0)
    if slot - now < dt.timedelta(minutes=min_lead_min):
        slot += dt.timedelta(days=1)  # Termin heute verpasst -> morgen zur selben Zeit (nie sofort)
    return slot.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def publish(ep_id, platforms=None, dry_run=False, now=None):
    cfg = config()
    st = db.status(ep_id)
    video = db.episode_dir(ep_id) / "final.mp4"
    sc, meta = _meta(ep_id)
    plats = platforms or [p for p, c in cfg["publishing"]["platforms"].items() if c.get("enabled")]
    plan = {}
    slot = publish_slot(cfg, now)
    for p in plats:
        priv = cfg["publishing"]["platforms"][p]["privacy"]
        plan[p] = youtube.build_metadata(meta, priv, slot) if p == "youtube" else \
            {"post_info": tiktok.build_post_info(meta, priv), "source": "FILE_UPLOAD"}
    if dry_run:
        return {"dry_run": True, "plan": plan}
    # Harte Sperre unabhängig von der Konfiguration: nur bestandene QC + Freigabe (manuell oder QC-Automatik)
    if st.get("state") not in ("freigegeben", "veröffentlicht", "geplant"):
        raise SystemExit(f"Keine Veröffentlichung: Episode ist nicht freigegeben (Status '{st.get('state')}').")
    if (st.get("score") or 0) < 90:
        raise SystemExit(f"Keine Veröffentlichung: QC-Wert {st.get('score')} unter 90.")
    if not cfg["publishing"].get("enabled"):
        raise SystemExit("Keine Veröffentlichung: publishing.enabled=false in config/studio.json.")
    results = st.get("published", {})
    for p in plats:
        if p in results:
            continue
        priv = cfg["publishing"]["platforms"][p]["privacy"]
        try:
            if p == "youtube":
                if not youtube.configured():
                    raise RuntimeError("YouTube-Zugangsdaten fehlen (python -m studio auth-youtube)")
                results[p] = youtube.upload(video, meta, priv, slot)
            elif p == "tiktok":
                if not tiktok.configured():
                    raise RuntimeError("TikTok-Zugangsdaten fehlen (python -m studio auth-tiktok)")
                results[p] = tiktok.publish(video, meta, priv)
            results.get("errors", {}).pop(p, None)
            db.log(f"[{ep_id}] veröffentlicht auf {p}: {results[p]}")
        except Exception as e:
            db.log(f"[{ep_id}] Veröffentlichung auf {p} fehlgeschlagen: {e}", "ERROR")
            results.setdefault("errors", {})[p] = str(e)
    if not results.get("errors"):
        results.pop("errors", None)
    state = "veröffentlicht" if any(k in results for k in ("youtube", "tiktok")) else st.get("state")
    if state == "veröffentlicht" and all(r.get("publish_at") for k, r in results.items() if k in ("youtube", "tiktok")):
        state = "geplant"
    db.set_status(ep_id, state, published=results)
    if state in ("veröffentlicht", "geplant") and sc.get("series"):
        s = db.series(sc["series"])
        if ep_id not in [e["id"] for e in s.get("episodes", [])]:
            s.setdefault("episodes", []).append({"id": ep_id, "n": sc["episode"], "title": sc["title"]})
            db.save_series(s)
    return results


def tiktok_package(ep_id):
    """Upload-Paket für das manuelle Hochladen in der TikTok-App: Beschreibung + Hinweise."""
    sc, meta = _meta(ep_id)
    d = db.episode_dir(ep_id)
    caption = tiktok.build_post_info(meta, "PUBLIC_TO_EVERYONE")["title"]
    txt = (f"{caption}\n\n---\nCHECKLISTE TIKTOK-UPLOAD ({sc.get('label')})\n"
           f"1. Video: {d / 'final.mp4'}\n2. Beschreibung oben kopieren\n"
           f"3. Weitere Optionen -> 'KI-generierte Inhalte' EINschalten\n"
           f"4. Titelbild: ca. Sekunde {meta.get('cover_ms', 1000) / 1000:.0f}\n"
           f"5. Nach dem Posten: Kommentare später in tiktok_comments.txt einfügen (Abstimmung A/B)\n")
    (d / "tiktok_upload.txt").write_text(txt, encoding="utf-8")
    return d / "tiktok_upload.txt"


def mark_published_manually(ep_id, platform, url=""):
    st = db.status(ep_id)
    pub = st.get("published", {})
    pub[platform] = {"platform": platform, "manual": True, "url": url}
    db.set_status(ep_id, "veröffentlicht", published=pub)


def collect_votes(ep_id):
    st = db.status(ep_id)
    sc, _ = _meta(ep_id)
    opts = (sc.get("cliffhanger") or {}).get("options", {})
    parts, sources = [], {}
    yt = (st.get("published") or {}).get("youtube")
    if yt and youtube.configured():
        t = votes.tally(youtube.comments(yt["id"]), opts)
        parts.append(t)
        sources["youtube"] = t
    tk_file = db.episode_dir(ep_id) / "tiktok_comments.txt"
    if tk_file.exists():
        cm = [{"author": f"tk{i}", "text": l} for i, l in enumerate(tk_file.read_text(encoding="utf-8").splitlines()) if l.strip()]
        t = votes.tally(cm, opts)
        parts.append(t)
        sources["tiktok_import"] = t
    manual = st.get("manual_votes")
    if manual:
        parts.append({"counts": manual, "total": sum(manual.values())})
        sources["manuell"] = manual
    result = votes.merge(*parts) if parts else {"counts": {"A": 0, "B": 0}, "total": 0, "winner": None}
    result["sources"] = sources
    db.set_status(ep_id, st.get("state", "?"), votes=result)
    if sc.get("series"):
        s = db.series(sc["series"])
        s["votes"] = [v for v in s.get("votes", []) if v.get("episode") != ep_id]
        s["votes"].append({"episode": ep_id, **result})
        db.save_series(s)
    return result
