"""Prüft ein Drehbuch, bevor Rechenzeit in die Produktion fließt."""
import json

from . import db
from .draw import characters as C
from .draw import sets as S

SFX = {"knock", "knock_hard", "creak", "buzz", "ping", "whoosh", "sting", "heartbeat", "steps", "thud",
       "lights_out", "keys", "riser"}
MOODS = {"tension", "mystery", "cozy", "comedy", "silence"}
POV = {"none", "phone", "door", "box", "table", "knock"}
FX = {None, "door", "phone", "inner", "radio"}


def script(ep_id):
    p = db.episode_dir(ep_id) / "script.json"
    if not p.exists():
        return [f"{p} fehlt"]
    sc = json.loads(p.read_text(encoding="utf-8"))
    chars = db.characters()
    errs = []
    for k in ("id", "title", "label", "shots", "publish", "cliffhanger"):
        if k not in sc:
            errs.append(f"Feld '{k}' fehlt")
    for i, s in enumerate(sc.get("shots", [])):
        w = f"Einstellung {i}:"
        if s.get("set") not in S.SETS:
            errs.append(f"{w} unbekannte Kulisse '{s.get('set')}' (verfügbar: {sorted(S.SETS)})")
            continue
        st = S.SETS[s["set"]]()
        for c in s.get("characters", []):
            if c["id"] not in chars:
                errs.append(f"{w} unbekannte Figur '{c['id']}'")
            if "spot" in c and c["spot"] not in st.spots:
                errs.append(f"{w} Position '{c['spot']}' gibt es in '{s['set']}' nicht ({sorted(st.spots)})")
            if c.get("expr", "neutral") not in C.EXPRESSIONS:
                errs.append(f"{w} Ausdruck '{c.get('expr')}' unbekannt")
            if c.get("arms", "down") not in C.ARM_POSES:
                errs.append(f"{w} Armhaltung '{c.get('arms')}' unbekannt")
        for ln in s.get("lines", []):
            if ln.get("speaker") not in chars:
                errs.append(f"{w} Sprecher '{ln.get('speaker')}' unbekannt")
            if ln.get("fx") not in FX:
                errs.append(f"{w} Stimm-Effekt '{ln.get('fx')}' unbekannt")
            if ln.get("expr") and ln["expr"] not in C.EXPRESSIONS:
                errs.append(f"{w} Ausdruck '{ln['expr']}' unbekannt")
        for e in s.get("sfx", []):
            if e.get("name") not in SFX:
                errs.append(f"{w} Soundeffekt '{e.get('name')}' unbekannt")
        if s.get("music", "silence") not in MOODS:
            errs.append(f"{w} Musikstimmung '{s.get('music')}' unbekannt")
        if (s.get("pov") or {}).get("mode", "none") not in POV:
            errs.append(f"{w} POV-Modus unbekannt")
    cs = sc.get("cover_shot")
    if cs is not None and not (0 <= cs < len(sc.get("shots", []))):
        errs.append(f"cover_shot {cs} existiert nicht (nur {len(sc.get('shots', []))} Einstellungen)")
    if sc.get("shots") and not sc["shots"][-1].get("endcard"):
        errs.append("Letzte Einstellung braucht eine Abstimmungs-Endkarte (endcard)")
    return errs
