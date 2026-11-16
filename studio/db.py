"""Charakter-, Serien- und Episoden-Datenbank (JSON-Dateien, git-freundlich)."""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = ROOT / "db" / "characters"
SERIES_DIR = ROOT / "db" / "series"
EP_DIR = ROOT / "episodes"
LOG_FILE = ROOT / "logs" / "studio.log"


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(p)


def characters():
    return {p.stem: _load(p) for p in sorted(CHAR_DIR.glob("*.json"))}


def character(cid):
    return _load(CHAR_DIR / f"{cid}.json")


def series_all():
    return {p.stem: _load(p) for p in sorted(SERIES_DIR.glob("*.json"))}


def series(sid):
    return _load(SERIES_DIR / f"{sid}.json")


def save_series(s):
    save(SERIES_DIR / f"{s['id']}.json", s)


def episode_dir(ep_id):
    return EP_DIR / ep_id


def episodes():
    out = []
    for d in sorted(EP_DIR.iterdir()) if EP_DIR.exists() else []:
        if (d / "script.json").exists():
            st = _load(d / "status.json") if (d / "status.json").exists() else {}
            out.append({"id": d.name, "script": _load(d / "script.json"), "status": st})
    return out


def status(ep_id):
    p = episode_dir(ep_id) / "status.json"
    return _load(p) if p.exists() else {"id": ep_id, "state": "neu", "history": []}


def set_status(ep_id, state, **extra):
    st = status(ep_id)
    st["state"] = state
    st.update(extra)
    st.setdefault("history", []).append({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "state": state,
                                         **{k: v for k, v in extra.items() if isinstance(v, (str, int, float))}})
    save(episode_dir(ep_id) / "status.json", st)
    return st


def log(msg, level="INFO"):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)
