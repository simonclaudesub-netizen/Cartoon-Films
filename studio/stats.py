"""Leistungszahlen beider Kanäle für die Übersichtsseite (Dashboard).

Quellen (nur lesend):
  YouTube Data API v3: channels?part=statistics&mine=true, videos?part=statistics,status&id=...
  TikTok: Die eigene TikTok-App hat keinen Lese-Scope für Aufrufe (nur video.upload). Zahlen kommen daher
    aus `published.tiktok.zahlen` (vom Kanalinhaber abgelesen, `python -m studio tiktok-zahlen …`);
    nur für alte Buffer-Posts ohne solche Zahlen fragt das Skript Buffer (post.metrics).
  Abstimmungen: db/series/<serie>.json (votes), von `studio votes` aus den Kommentaren gezählt.
Schreibt drei JSON-Dateien {rows, meta} nach stats/ (für das Hochladen ins Dashboard).
"""
import datetime as dt
import json
from pathlib import Path

import requests

from . import db
from .publish import buffer, youtube

OUT = db.ROOT / "stats"
YT = "https://www.googleapis.com/youtube/v3"


def _yt_get(path, **params):
    r = requests.get(f"{YT}/{path}", params=params, headers={"Authorization": f"Bearer {youtube._token()}"}, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])


def _episodes():
    eps = []
    for d in sorted((db.ROOT / "episodes").iterdir()):
        if not (d / "status.json").exists() or not (d / "script.json").exists():
            continue
        st = json.loads((d / "status.json").read_text())
        sc = json.loads((d / "script.json").read_text())
        if st.get("published"):
            eps.append((d.name, sc, st))
    return eps


def collect():
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    eps = _episodes()
    videos, errors = [], []

    yt_ids = {st["published"]["youtube"]["id"]: (ep, sc, st) for ep, sc, st in eps if st["published"].get("youtube")}
    yt_items = {it["id"]: it for it in _yt_get("videos", part="statistics,status,snippet", id=",".join(yt_ids))} if yt_ids else {}
    for vid, (ep, sc, st) in yt_ids.items():
        it = yt_items.get(vid, {})
        s, status = it.get("statistics", {}), it.get("status", {})
        pub = st["published"]["youtube"]
        live = status.get("privacyStatus") == "public"
        videos.append({"folge": sc.get("episode"), "titel": sc.get("title"), "plattform": "YouTube",
                       "status": "öffentlich" if live else "geplant" if status.get("publishAt") else status.get("privacyStatus", "?"),
                       "veroeffentlicht": status.get("publishAt") or pub.get("publish_at") or it.get("snippet", {}).get("publishedAt"),
                       "aufrufe": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                       "kommentare": int(s.get("commentCount", 0)), "teilen": None,
                       "link": pub.get("url") or f"https://youtube.com/shorts/{vid}"})

    for ep, sc, st in eps:
        tk = st["published"].get("tiktok")
        if not tk:
            continue
        z = tk.get("zahlen")
        if z or tk.get("mode") != "buffer":  # Posteingang/manuell: abgelesene Zahlen (oder noch keine)
            videos.append({"folge": sc.get("episode"), "titel": sc.get("title"), "plattform": "TikTok",
                           "status": "öffentlich" if z or tk.get("manual") else "Entwurf im Posteingang",
                           "veroeffentlicht": (z or {}).get("stand") or tk.get("publish_at"),
                           "aufrufe": (z or {}).get("aufrufe"), "likes": (z or {}).get("likes"),
                           "kommentare": (z or {}).get("kommentare"), "teilen": (z or {}).get("teilen"),
                           "link": tk.get("url") or ""})
            continue
        try:
            p = buffer._q("query($id: PostId!) { post(input: {id: $id}) { status dueAt sentAt externalLink "
                          "metrics { type value } } }", {"id": tk["buffer_post_id"]})["post"]
        except Exception as e:  # noqa: BLE001
            errors.append(f"TikTok {ep}: {e}")
            continue
        m = {x["type"]: x["value"] for x in p.get("metrics") or []}
        sent = p["status"] == "sent"
        videos.append({"folge": sc.get("episode"), "titel": sc.get("title"), "plattform": "TikTok",
                       "status": "öffentlich" if sent else "geplant" if p["status"] == "scheduled" else p["status"],
                       "veroeffentlicht": p.get("sentAt") or p.get("dueAt"),
                       "aufrufe": int(m.get("views", 0)) if sent else 0, "likes": int(m.get("reactions", 0)) if sent else 0,
                       "kommentare": int(m.get("comments", 0)) if sent else 0, "teilen": int(m.get("shares", 0)) if sent else 0,
                       "link": p.get("externalLink") or ""})
    videos.sort(key=lambda r: (r["folge"] or 0, r["plattform"]))

    kanaele = []
    ch = _yt_get("channels", part="snippet,statistics", mine="true")
    if ch:
        s = ch[0]["statistics"]
        kanaele.append({"plattform": "YouTube", "name": ch[0]["snippet"]["title"],
                        "abonnenten": None if s.get("hiddenSubscriberCount") else int(s.get("subscriberCount", 0)),
                        "aufrufe_gesamt": int(s.get("viewCount", 0)), "videos": int(s.get("videoCount", 0))})
    tk_rows = [v for v in videos if v["plattform"] == "TikTok"]
    if tk_rows:
        names = [st["published"]["tiktok"].get("channel") for _, _, st in eps if st["published"].get("tiktok")]
        name = next((n for n in names if n), None)
        kanaele.append({"plattform": "TikTok", "name": "@" + name if name else "TikTok", "abonnenten": None,
                        "aufrufe_gesamt": sum(v["aufrufe"] or 0 for v in tk_rows),
                        "videos": sum(1 for v in tk_rows if v["status"] == "öffentlich")})

    abst = []
    for s in db.series_all().values() if isinstance(db.series_all(), dict) else db.series_all():
        titles = {e["id"]: (e["n"], e["title"]) for e in s.get("episodes", [])}
        for v in s.get("votes", []):
            n, t = titles.get(v["episode"], (None, v["episode"]))
            abst.append({"folge": n, "titel": t, "A": v["counts"].get("A", 0), "B": v["counts"].get("B", 0),
                         "stimmen": v.get("total", 0), "gewinner": v.get("winner")})

    code = Path(__file__).read_text(encoding="utf-8")
    meta = [{"label": "Abgerufen", "value": now}, {"label": "stats.py", "value": code, "type": "code", "lang": "python"}]
    if errors:
        meta.append({"label": "Fehler", "value": "; ".join(errors)})
    OUT.mkdir(exist_ok=True)
    out = {}
    for name, rows in (("videos", videos), ("kanaele", kanaele), ("abstimmungen", abst)):
        f = OUT / f"{name}.json"
        f.write_text(json.dumps({"rows": rows, "meta": meta}, ensure_ascii=False, indent=1), encoding="utf-8")
        out[name] = f
    return out, errors


if __name__ == "__main__":
    files, errs = collect()
    for k, f in files.items():
        print(k, len(json.loads(f.read_text())["rows"]), "Zeilen ->", f.relative_to(db.ROOT))
    for e in errs:
        print("FEHLER", e)
