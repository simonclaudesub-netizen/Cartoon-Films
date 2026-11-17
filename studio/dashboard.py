"""Erzeugt das Überwachungs-Dashboard als statische HTML-Datei (dashboard/index.html)."""
import html
import json
import os
from pathlib import Path

from . import db, selfcheck

OUT = db.ROOT / "dashboard" / "index.html"

STATE_LABEL = {"neu": "Neu", "in_produktion": "In Produktion", "freigabe_ausstehend": "Wartet auf Freigabe",
               "freigegeben": "Freigegeben", "veröffentlicht": "Veröffentlicht", "geplant": "Geplant (18:00)", "abgelehnt": "Abgelehnt (QC)",
               "fehler": "Fehler"}
STATE_TONE = {"freigabe_ausstehend": "warn", "freigegeben": "ok", "veröffentlicht": "ok", "geplant": "ok", "abgelehnt": "bad",
              "fehler": "bad"}


def e(x):
    return html.escape(str(x))


FILES = {}
MODE = {"artifact": False}


def _rel(p):
    """Lokal: relativer Pfad. Artifact-Modus: veröffentlichter Pfad unter media/."""
    p = Path(p)
    if MODE["artifact"]:
        key = "media/" + (p.parent.name + "_" + p.name if p.parent.name not in ("characters",) else p.name)
        FILES[key] = str(p)
        return key
    return os.path.relpath(p, OUT.parent)


def _voice_label(v):
    if v.get("engine") == "zonos":
        return f"ZONOS3 mit Emotions-Reglern (Vorlage: {v.get('ref_source', v['ref'])})"
    if v.get("engine") == "chatterbox":
        return f"Chatterbox (Referenz: {v.get('ref_source', v['ref'])})"
    return f"Piper {v.get('model')}"


def build(artifact=False):
    MODE["artifact"] = artifact
    FILES.clear()
    checks = selfcheck.run()
    eps = db.episodes()
    series = db.series_all()
    chars = db.characters()
    cfg = json.loads((db.ROOT / "config" / "studio.json").read_text())
    log = (db.LOG_FILE.read_text(encoding="utf-8").splitlines()[-40:] if db.LOG_FILE.exists() else [])

    ep_rows, details = [], []
    for ep in reversed(eps):
        st, sc = ep["status"], ep["script"]
        d = db.episode_dir(ep["id"])
        qcf = sorted(d.glob("qc_attempt*.json"))
        qc = json.loads(qcf[-1].read_text()) if qcf else None
        score = qc["score"] if qc else None
        tone = STATE_TONE.get(st.get("state"), "")
        tries = " → ".join(str(a.get("score", "Fehler")) for a in st.get("attempts", []))
        ep_rows.append(f"""<tr><td><b>{e(sc.get('label', ep['id']))}</b><div class=muted>{e(sc.get('title', ''))}</div></td>
<td><span class="pill {tone}">{e(STATE_LABEL.get(st.get('state'), st.get('state', '?')))}</span></td>
<td class=num>{'' if score is None else f'<b>{score}</b>/100'}<div class=muted>{e(tries)}</div></td>
<td class=num>{e(round(st['duration'], 1)) + ' s' if st.get('duration') else ''}</td>
<td>{e(', '.join(k for k in (st.get('published') or {}) if k != 'errors') or '–')}</td></tr>""")
        if qc:
            cats = "".join(
                f"<div class=bar><span>{e(k)}</span><div class=track><div class=fill style='width:{v['points'] / v['max'] * 100:.0f}%'></div></div><b>{v['points']}/{v['max']}</b></div>"
                for k, v in qc["categories"].items())
            fails = "".join(f"<li>{e(c['name'])}: {e(c['detail'])}</li>" for c in qc["checks"] if not c["ok"]) or "<li>Keine</li>"
            lines = "".join(
                f"<tr><td>{e(t['speaker'])}</td><td>{e(t['text'])}</td><td class=muted>{e(t['heard'])}</td><td class=num>{t['similarity']:.2f}</td></tr>"
                for t in qc["line_tests"])
            video = f"<video controls playsinline preload=metadata poster='{_rel(d / 'cover.jpg')}' src='{_rel(d / 'final.mp4')}'></video>" \
                if (d / "final.mp4").exists() else ""
            votes = st.get("votes")
            vt = f"A: {votes['counts']['A']} · B: {votes['counts']['B']} (Sieger: {votes.get('winner') or 'offen'})" if votes else "noch keine Stimmen ausgewertet"
            details.append(f"""<section class=card><h2>{e(sc.get('label'))} – {e(sc.get('title'))}</h2>
<div class=epgrid><div>{video}</div><div>
<p>{e(sc.get('summary', ''))}</p>
<h3>QC-Punkte je Kategorie</h3>{cats}
<h3>Nicht bestandene Prüfungen</h3><ul>{fails}</ul>
<h3>Abstimmung</h3><p>{e(vt)}</p>
<h3>Kontaktabzug</h3><img class=contact src='{_rel(d / 'qc_contact.png')}' alt='Kontaktabzug aller Einstellungen'>
</div></div>
<details><summary>Sprachtest – Whisper hört jede Zeile ab</summary><div class=scroll><table><tr><th>Figur</th><th>Soll</th><th>Gehört</th><th>Ähnl.</th></tr>{lines}</table></div></details>
</section>""")

    ser_cards = "".join(f"""<div class=card><h3>{e(s['title'])}</h3><p>{e(s['logline'])}</p>
<p class=muted>Folgen: {len(s.get('episodes', []))} veröffentlicht · Abstimmungen: {len(s.get('votes', []))}</p>
<details><summary>Pläne für die nächste Folge</summary><p><b>A:</b> {e(s.get('next_plans', {}).get('A', ''))}</p><p><b>B:</b> {e(s.get('next_plans', {}).get('B', ''))}</p></details></div>"""
                        for s in series.values())
    char_cards = "".join(f"""<div class=card><h3>{e(c['name'])}</h3><p class=muted>{e(c['role'])}</p><p>{e(c['personality'])}</p>
<p class=muted>Stimme: {e(_voice_label(c['voice']))}</p><img class=sheet src='{_rel(db.CHAR_DIR / (c['id'] + '_sheet.png'))}' alt='Model-Sheet {e(c['name'])}'></div>"""
                         for c in chars.values())
    chk = "".join(f"<li class='{'ok' if c['ok'] else ('warn' if c['kind'] == 'zugang' else 'bad')}'>{'✓' if c['ok'] else '✗'} {e(c['name'])} <span class=muted>{e(c['detail'])}</span></li>" for c in checks)
    pub = cfg["publishing"]
    head = """<title>Du entscheidest – Studio</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bangers&family=Inter:wght@400;600;700&display=swap">
<style>
/* Layout: ein Kontrollraum – Episoden-Status oben, darunter je Episode Video + QC-Messwerte, dann Datenbanken */
:root{--bg:#edf0ea;--card:#ffffff;--ink:#17171c;--muted:#5b645d;--line:#d4dbd2;--accent:#e0a800;--accent-ink:#7a5900;
--ok:#2f8a4c;--warn:#a96a12;--bad:#c53b33;--on-sem:#ffffff;--code:#f4f6f2;
--display:"Bangers","Impact",system-ui,sans-serif;--body:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121513;--card:#1b201c;--ink:#e9ece6;--muted:#9aa59c;--line:#2c332d;--accent:#ffd23f;--accent-ink:#ffd23f;--ok:#4fb46d;--warn:#e0a43a;--bad:#e2635b;--on-sem:#101210;--code:#151915;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121513;--card:#1b201c;--ink:#e9ece6;--muted:#9aa59c;--line:#2c332d;--accent:#ffd23f;--accent-ink:#ffd23f;--ok:#4fb46d;--warn:#e0a43a;--bad:#e2635b;--on-sem:#101210;--code:#151915;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--body)}
main{max-width:1180px;margin:0 auto;padding-block:24px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:20px}
h1{font:400 44px/1 var(--display);letter-spacing:.02em;margin:0}
h1 span{color:var(--accent-ink)}
h2{font-size:18px;margin:0 0 12px;text-wrap:balance}h3{font-size:13px;margin:16px 0 6px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
p{margin:0 0 8px;max-width:68ch}
.muted{color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;min-width:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-block;padding:2px 10px;border-radius:99px;font-size:13px;font-weight:600;background:var(--line);color:var(--ink)}
.pill.ok{background:var(--ok);color:var(--on-sem)}.pill.warn{background:var(--warn);color:var(--on-sem)}.pill.bad{background:var(--bad);color:var(--on-sem)}
ul.checks{list-style:none;padding:0;columns:2;margin:0}ul.checks li{padding:3px 0;break-inside:avoid}
li.ok{color:var(--ok)}li.warn{color:var(--warn)}li.bad{color:var(--bad)}
.epgrid{display:grid;grid-template-columns:minmax(220px,320px) minmax(0,1fr);gap:20px}
video{width:100%;max-width:100%;aspect-ratio:9/16;border-radius:10px;background:#000}
.bar{display:grid;grid-template-columns:100px minmax(0,1fr) 64px;gap:8px;align-items:center;font-size:14px;margin:4px 0}
.track{height:8px;background:var(--line);border-radius:4px}.fill{height:100%;background:var(--accent);border-radius:4px}
img.contact,img.sheet{width:100%;border-radius:8px;border:1px solid var(--line);display:block}
pre{white-space:pre-wrap;font-size:12px;max-height:320px;overflow:auto;background:var(--code);padding:10px;border-radius:8px;margin:0}
details summary{cursor:pointer;font-weight:600;margin-top:12px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:700px){.epgrid{grid-template-columns:1fr}ul.checks{columns:1}h1{font-size:36px}}
</style>"""
    body = f"""<main>
<header><h1>Du entscheidest <span>Studio</span></h1><p class=muted>Veröffentlichung: <b>{'AKTIV' if pub['enabled'] else 'AUS (Testbetrieb)'}</b> · manuelle Freigabe: {'ja' if pub['require_manual_approval'] else 'nein'} · Mindest-QC: {cfg['quality']['min_score']} Punkte · Stand {e(log[-1][:16] if log else '')}</p></header>
<section class=card><h2>Episoden</h2><div class=scroll><table><tr><th>Episode</th><th>Status</th><th>QC</th><th>Länge</th><th>Plattformen</th></tr>{''.join(ep_rows)}</table></div></section>
{''.join(details)}
<section><h2>Serien</h2><div class=grid>{ser_cards}</div></section>
<section><h2>Figuren-Datenbank</h2><div class=grid>{char_cards}</div></section>
<section class=card><h2>Systemprüfung</h2><ul class=checks>{chk}</ul></section>
<section class=card><h2>Protokoll (letzte 40 Einträge)</h2><pre>{e(chr(10).join(log))}</pre></section>
</main>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if artifact:
        out = OUT.parent / "artifact.html"
        out.write_text(head + "\n" + body, encoding="utf-8")
        return out, dict(FILES)
    page = f"<!doctype html><html lang=de><head><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1,viewport-fit=cover\">{head}</head><body>{body}</body></html>"
    OUT.write_text(page, encoding="utf-8")
    return OUT
