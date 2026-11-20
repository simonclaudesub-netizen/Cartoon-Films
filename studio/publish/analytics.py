"""Zuschauerbindung aus der YouTube Analytics API v2 – wo springen die Leute ab?

Offizieller Endpunkt (Scope yt-analytics.readonly, YouTube Analytics API im Google-Cloud-Projekt aktiviert):
  GET https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE&startDate&endDate&metrics&dimensions&filters
  - je Video: views, averageViewDuration, averageViewPercentage, likes, comments, shares, subscribersGained
  - Verlauf:  dimensions=elapsedVideoTimeRatio, metrics=audienceWatchRatio,relativeRetentionPerformance
              (nur für EIN Video pro Abfrage; 100 Punkte von 0,01 bis 1,0 der Videolänge)
YouTube liefert die Zahlen mit 1–3 Tagen Verzögerung; neue Folgen haben daher oft noch keine Daten.

  python -m studio.publish.analytics   -> stats/analytics.json + Kurzfassung je Folge und Einstellung
"""
import datetime as dt
import json
import sys

import requests

from .. import db
from . import youtube
from .comments import _published

API = "https://youtubeanalytics.googleapis.com/v2/reports"
START = "2026-11-01"


def _report(tok, **p):
    q = {"ids": "channel==MINE", "startDate": START, "endDate": dt.date.today().isoformat(), **p}
    r = requests.get(API, params=q, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    if r.status_code == 403:
        raise SystemExit("YouTube Analytics: keine Berechtigung – Zugang mit Analytics-Scope neu bestätigen "
                         "(python -m studio auth-youtube) und 'YouTube Analytics API' im Cloud-Projekt aktivieren.\n"
                         + r.text[:300])
    r.raise_for_status()
    j = r.json()
    cols = [h["name"] for h in j.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in j.get("rows", [])]


def _shots(ep):
    f = db.ROOT / "episodes" / ep / "timeline.json"
    if not f.exists():
        return [], 0
    tl = json.loads(f.read_text())
    out = []
    for s in tl["shots"]:
        txt = (s.get("caption") or "") or next((ln.get("text", "") for ln in s.get("lines", [])), "")
        out.append({"i": s["_index"] + 1, "t0": round(s["_t0"], 1), "t1": round(s["_t0"] + s["_dur"], 1),
                    "text": txt[:60]})
    return out, tl.get("duration", 0)


def _at(curve, sec, dur):
    """Anteil der Zuschauer (audienceWatchRatio) bei Sekunde sec."""
    if not curve or not dur:
        return None
    r = min(1.0, max(0.01, sec / dur))
    return min(curve, key=lambda p: abs(p["elapsedVideoTimeRatio"] - r))["audienceWatchRatio"]


def build():
    tok = youtube._token()
    pubs = _published()
    ids = ",".join(v for _, v, _ in pubs)
    per = {r["video"]: r for r in _report(tok, dimensions="video", filters=f"video=={ids}",
           metrics="views,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained")}
    res = []
    for ep, vid, sc in pubs:
        curve = _report(tok, dimensions="elapsedVideoTimeRatio", filters=f"video=={vid}",
                        metrics="audienceWatchRatio,relativeRetentionPerformance")
        shots, dur = _shots(ep)
        for s in shots:
            a, b = _at(curve, s["t0"], dur), _at(curve, s["t1"], dur)
            s["bindung_start"], s["bindung_ende"] = a, b
            s["verlust"] = round(a - b, 3) if a is not None and b is not None else None
        worst = max((s for s in shots if s["verlust"] is not None), key=lambda s: s["verlust"], default=None)
        res.append({"folge": ep, "video": vid, "titel": (sc.get("publish") or {}).get("title"), "dauer": dur,
                    "werte": per.get(vid, {}), "bindung_3s": _at(curve, 3, dur),
                    "bindung_ende": _at(curve, dur, dur), "relativ_zu_aehnlichen": (
                        round(sum(p["relativeRetentionPerformance"] for p in curve) / len(curve), 2) if curve else None),
                    "groesster_abbruch": worst, "einstellungen": shots, "hat_daten": bool(curve)})
    return res


def summary(res):
    out = []
    for r in res:
        w = r["werte"]
        if not r["hat_daten"]:
            out.append(f"{r['folge']}: noch keine Analytics-Daten (YouTube braucht 1–3 Tage)")
            continue
        g = r["groesster_abbruch"]
        out.append(f"{r['folge']}: {w.get('views', '?')} Aufrufe · Ø {w.get('averageViewPercentage', '?')} % gesehen · "
                   f"nach 3 s noch {r['bindung_3s']:.0%} · am Ende {r['bindung_ende']:.0%} · "
                   f"größter Abbruch Einstellung {g['i']} ({g['t0']}–{g['t1']} s, -{g['verlust']:.0%}): „{g['text']}“"
                   if g else f"{r['folge']}: Daten unvollständig")
    if any(r["hat_daten"] for r in res):
        out.append("(Werte über 100 % = Zuschauer schauen den Anfang mehrfach, z. B. durch Wiederholen/Loopen.)")
    return "\n".join(out)


def main(argv):
    res = build()
    out = db.ROOT / "stats"
    out.mkdir(exist_ok=True)
    (out / "analytics.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summary(res))


if __name__ == "__main__":
    main(sys.argv[1:])
