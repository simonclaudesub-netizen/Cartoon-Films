"""Kommandozeile des Studios:  python -m studio <befehl>

  check                      Systemprüfung (Werkzeuge, Stimmen, Zugänge)
  sheets                     Model-Sheets (Referenzbilder) aller Figuren erzeugen
  validate <episode>         Drehbuch prüfen (Figuren, Kulissen, Felder)
  produce <episode>          Episode produzieren inkl. QC + automatischer Korrektur (max. 3 Versuche)
  approve <episode>          Freigabe erteilen (nur nach bestandener QC)
  publish <episode> [--dry-run] [--platform youtube|tiktok]
  votes <episode> [--a N --b N]   Abstimmung auswerten (YouTube automatisch, TikTok manuell)
  tiktok-paket <episode>     Beschreibung + Checkliste für den manuellen TikTok-Upload
  manuell-gepostet <episode> <plattform> [url]   manuellen Upload vermerken
  dashboard                  Dashboard erzeugen (dashboard/index.html)
  auth-youtube <client_id> <client_secret> [code]
  auth-tiktok <client_key> <client_secret> <refresh_token>
"""
import argparse
import json
import sys

from . import db


def main(argv=None):
    ap = argparse.ArgumentParser(prog="studio", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--platform", action="append")
    ap.add_argument("--a", type=int)
    ap.add_argument("--b", type=int)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        from . import selfcheck
        res = selfcheck.run()
        for c in res:
            print(("OK   " if c["ok"] else ("--   " if c["kind"] == "zugang" else "FEHLT")), c["name"], c["detail"])
        sys.exit(0 if all(c["ok"] for c in res if c["kind"] == "pflicht") else 1)
    elif a.cmd == "sheets":
        from . import modelsheet
        for p in modelsheet.render_all():
            print(p)
    elif a.cmd == "validate":
        from . import validate
        errs = validate.script(a.args[0])
        print("\n".join(errs) or "Drehbuch OK")
        sys.exit(1 if errs else 0)
    elif a.cmd == "produce":
        from . import pipeline, validate
        errs = validate.script(a.args[0])
        if errs:
            print("\n".join(errs))
            sys.exit(1)
        res = pipeline.produce(a.args[0])
        print(f"QC: {res['score']} Punkte – bereit zur Freigabe" if res else "Episode abgelehnt (siehe qc_report.md)")
        sys.exit(0 if res else 2)
    elif a.cmd == "approve":
        from . import release
        release.approve(a.args[0])
    elif a.cmd == "publish":
        from . import release
        print(json.dumps(release.publish(a.args[0], a.platform, a.dry_run), ensure_ascii=False, indent=2))
    elif a.cmd == "votes":
        from . import release
        if a.a is not None or a.b is not None:
            st = db.status(a.args[0])
            db.set_status(a.args[0], st.get("state", "?"), manual_votes={"A": a.a or 0, "B": a.b or 0})
        print(json.dumps(release.collect_votes(a.args[0]), ensure_ascii=False, indent=2))
    elif a.cmd == "tiktok-paket":
        from . import release
        p = release.tiktok_package(a.args[0])
        print(p.read_text(encoding="utf-8"))
    elif a.cmd == "manuell-gepostet":
        from . import release
        release.mark_published_manually(a.args[0], a.args[1], a.args[2] if len(a.args) > 2 else "")
        print("Als veröffentlicht vermerkt.")
    elif a.cmd == "dashboard":
        from . import dashboard
        print(dashboard.build())
    elif a.cmd == "auth-youtube":
        from .publish import youtube
        if len(a.args) == 2:
            print("1. Diese Adresse im Browser öffnen und zustimmen:\n", youtube.auth_url(a.args[0]))
            print("2. Der Browser landet auf http://localhost:8765/?code=... (Seite lädt nicht – normal).")
            print("3. Den code-Wert kopieren und erneut aufrufen: auth-youtube <id> <secret> <code>")
        else:
            youtube.exchange_code(*a.args[:3])
            print("YouTube-Zugang gespeichert. Kanal:", youtube.channel())
    elif a.cmd == "youtube-test":
        from .publish import youtube
        print(youtube.channel())
    elif a.cmd == "auth-tiktok":
        from .publish import tiktok
        tiktok.SECRETS.parent.mkdir(parents=True, exist_ok=True)
        tiktok.SECRETS.write_text(json.dumps({"client_key": a.args[0], "client_secret": a.args[1],
                                              "refresh_token": a.args[2]}, indent=2))
        print("TikTok-Zugang gespeichert.")
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
