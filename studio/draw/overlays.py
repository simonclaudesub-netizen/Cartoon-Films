"""Bildschirm-Einblendungen: Serien-Label, Zeit-/Ort-Karten, Abstimmungs-Endkarte.

Sichere Zone für TikTok/Shorts: oben ~200 px (Suchleiste), unten ~420 px
(Beschreibung), rechts ~150 px (Like-/Kommentar-Buttons). Alle Texte bleiben
innerhalb x 70..930, y 230..1480.
"""
import math

from . import prims as P
from .persp import W, H

SAFE = (70, 230, 930, 1480)


def series_label(ctx, txt):
    ctx.select_font_face("Bangers")
    ctx.set_font_size(52)
    w = ctx.text_extents(txt).x_advance + 50
    x = (SAFE[0] + SAFE[2]) / 2
    P.rrect(ctx, x - w / 2, 250, w, 72, 20, "#111116", 0, alpha=0.75)
    P.text(ctx, txt, x, 305, 52, family="Bangers", bold=False, color="#ffd23f")


def caption(ctx, txt, t, dur, y=440):
    pop = min(1.0, t / 0.18)
    s = 0.6 + 0.4 * pop + 0.06 * math.sin(min(t, 0.5) * math.pi * 2) * (1 - min(1, t / 0.5))
    a = 1.0 if t < dur - 0.25 else max(0.0, (dur - t) / 0.25)
    if a <= 0:
        return
    x = (SAFE[0] + SAFE[2]) / 2
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.push_group()
    P.text(ctx, txt, 0, 0, 120, family="Bangers", bold=False, color="#ffd23f", outline=18)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def _badge():
    try:
        import json
        from ..db import ROOT
        return json.loads((ROOT / "config" / "studio.json").read_text(encoding="utf-8")).get("brand", {}).get("badge", "")
    except Exception:
        return ""


def endcard(ctx, data, t):
    ctx.set_source_rgba(0.05, 0.05, 0.08, min(0.78, t * 2.5))
    ctx.paint()
    x = (SAFE[0] + SAFE[2]) / 2
    badge = data.get("brand", _badge())
    if badge:  # Kanal-Marke über der Frage
        P.rrect(ctx, x - 260, 290, 520, 96, 48, "#ffd23f", 6)
        P.text(ctx, badge, x, 358, 64, family="Bangers", bold=False, color="#1a1a2e")
    q = data.get("question", "WAS SOLL ICH TUN?")
    lines = P.wrap(ctx, q, 100, 840, family="Bangers", bold=False)
    for i, l in enumerate(lines):
        P.text(ctx, l, x, 520 + i * 110, 100, family="Bangers", bold=False, color="#ffffff", outline=14)
    y0 = 560 + len(lines) * 110
    for i, (key, col) in enumerate((("A", "#3fa34d"), ("B", "#d6453d"))):
        k = max(0.0, min(1.0, (t - 0.3 - i * 0.25) / 0.2))
        if k <= 0:
            continue
        y = y0 + i * 230
        ctx.save()
        ctx.translate(x, y + 90)
        ctx.scale(k, k)
        ctx.translate(-x, -(y + 90))
        P.rrect(ctx, SAFE[0] + 10, y, SAFE[2] - SAFE[0] - 20, 180, 36, col, 7)
        P.ellipse(ctx, SAFE[0] + 110, y + 90, 62, 62, "#ffffff", 6)
        P.text(ctx, key, SAFE[0] + 110, y + 122, 92, family="Bangers", bold=False, color=col)
        opt = data.get("options", {}).get(key, "")
        ls = P.wrap(ctx, opt, 64, 620, family="Bangers", bold=False)
        for j, l in enumerate(ls[:2]):
            P.text(ctx, l, SAFE[0] + 200, y + 110 + (j - (len(ls[:2]) - 1) / 2) * 66, 64, family="Bangers",
                   bold=False, color="#ffffff", outline=8, align="left")
        ctx.restore()
    if t > 1.0:
        blink = 0.75 + 0.25 * math.sin(t * 6)
        P.text(ctx, data.get("cta", "Schreib A oder B in die Kommentare!"), x, y0 + 520, 50, color="#ffffff",
               outline=8)
        ctx.save()
        ctx.translate(x, y0 + 640)
        ctx.scale(blink, blink)
        P.text(ctx, data.get("next", "TEIL 2 FOLGT"), 0, 0, 80, family="Bangers", bold=False, color="#ffd23f",
               outline=12)
        ctx.restore()


def peephole(ctx, cx=540, cy=900, r=500):
    import cairo
    ctx.save()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.rectangle(-50, -50, W + 100, H + 100)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source_rgb(0.02, 0.02, 0.03)
    ctx.fill()
    g = cairo.RadialGradient(cx, cy, r * 0.55, cx, cy, r)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source_rgba(0.6, 0.65, 0.7, 0.35)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.restore()
