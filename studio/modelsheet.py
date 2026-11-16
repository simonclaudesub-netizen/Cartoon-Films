"""Erzeugt Referenzbilder (Model Sheets) für jede Figur.

Die Bilder dienen als visuelle Referenz für die Qualitätskontrolle und
Dokumentation; der Hash des `look`-Objekts wird in der Datenbank gesperrt.
"""
import hashlib
import json

import cairo

from . import db
from .draw import characters as C
from .draw import prims as P

POSES = [("neutral", "down"), ("happy", "wave"), ("angry", "hips"), ("scared", "shrug"),
         ("surprised", "raise"), ("suspicious", "cross"), ("sad", "down"), ("creepy", "hold")]


def look_hash(look):
    return hashlib.sha256(json.dumps(look, sort_keys=True).encode()).hexdigest()[:16]


def render(char, path):
    w, h = 2400, 1100
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    P.set_col(ctx, "#f3efe4")
    ctx.paint()
    P.text(ctx, f"{char['name']}  -  {char['role']}", 40, 70, 46, align="left", color="#222222")
    P.text(ctx, f"look-hash {look_hash(char['look'])}", w - 40, 70, 28, align="right", color="#666666")
    for i, (expr, arms) in enumerate(POSES):
        x = 150 + i * 300
        C.draw(ctx, char["look"], x, 1000, 1.05, expr=expr, arms=arms, t=0.3,
               mouth=0.6 if expr in ("surprised", "scared") else 0.0,
               prop="cake" if arms == "hold" else None)
        P.text(ctx, expr, x, 1080, 30, color="#333333")
    surf.write_to_png(str(path))


def render_all():
    out = []
    for char in db.characters().values():
        p = db.ROOT / "db" / "characters" / f"{char['id']}_sheet.png"
        render(char, p)
        out.append(p)
    return out


if __name__ == "__main__":
    for p in render_all():
        print(p)
