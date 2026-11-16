"""Ich-Perspektive: eigene Hände/Arme im Vordergrund (wie im Referenz-Screenshot)."""
import math

from . import prims as P
from .persp import W, H


def hand(ctx, x, y, ang, s, skin, side=1, grip=False):
    """Handrücken-Ansicht, Finger zeigen in Richtung `ang` (Radiant, 0 = nach oben)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(s, s)
    # Finger
    fl = [46, 58, 56, 44] if not grip else [26, 30, 30, 24]
    for i, fx in enumerate((-36, -12, 12, 34)):
        P.rrect(ctx, fx - 11, -60 - fl[i], 22, fl[i] + 20, 11, skin, 4.5)
        if not grip:
            P.line(ctx, [(fx - 6, -60 - fl[i] + 22), (fx + 6, -60 - fl[i] + 22)], 2.5)
    # Handfläche
    P.blob(ctx, [(-48, -62), (-50, 10), (-30, 40), (30, 40), (50, 8), (48, -62), (0, -70)], skin, 5)
    # Daumen
    P.blob(ctx, [(-side * 44, -10), (-side * 82, -48), (-side * 92, -66), (-side * 74, -72), (-side * 46, -46)],
           skin, 4.5)
    for k in range(3):
        P.line(ctx, [(-28 + k * 22, -54), (-22 + k * 22, -58)], 2.5)
    ctx.restore()


def forearm(ctx, start, end, width, sleeve, skin):
    """Unterarm vom Bildrand bis zum Handgelenk."""
    P.limb(ctx, [start, end], width, sleeve)
    dx, dy = end[0] - start[0], end[1] - start[1]
    ln = math.hypot(dx, dy) or 1
    ux, uy = dx / ln, dy / ln
    cx, cy = end[0] - ux * 28, end[1] - uy * 28
    P.ellipse(ctx, cx, cy, width * 0.55, width * 0.2, P.shade(sleeve, 0.85), 4.5,
              rot=math.atan2(uy, ux) + math.pi / 2)


def draw(ctx, mode, look, t, params=None):
    params = params or {}
    sleeve, skin = look["top_color"], look["skin"]
    sway_x = math.sin(t * 1.4) * 10
    sway_y = math.sin(t * 2.1) * 8
    if mode == "phone":
        _phone(ctx, sleeve, skin, t, params, sway_x, sway_y)
    elif mode == "door":
        reach = params.get("reach", 1.0)
        tx, ty = params.get("target", (640, 1000))
        k = min(1.0, t / 1.2) * reach
        ex, ey = 1150 + (tx + 40 - 1150) * k + sway_x, 2100 + (ty + 140 - 2100) * k + sway_y
        forearm(ctx, (1180, 2150), (ex, ey), 150, sleeve, skin)
        hand(ctx, ex - 10, ey - 50, -0.5, 1.15, skin, side=-1)
    elif mode == "box":
        P.poly(ctx, [(140 + sway_x, 1500 + sway_y), (940 + sway_x, 1500 + sway_y), (1000 + sway_x, 2000),
                     (80 + sway_x, 2000)], "#c9a26b", 6)
        P.poly(ctx, [(140 + sway_x, 1500 + sway_y), (940 + sway_x, 1500 + sway_y), (880 + sway_x, 1420 + sway_y),
                     (200 + sway_x, 1420 + sway_y)], "#dcb882", 6)
        P.rrect(ctx, 490 + sway_x, 1500 + sway_y, 100, 500, 0, "#e9d6a6", 4)
        for side in (-1, 1):
            x = 540 + side * 420 + sway_x
            forearm(ctx, (x + side * 120, 2150), (x, 1720 + sway_y), 150, sleeve, skin)
            hand(ctx, x - side * 10, 1640 + sway_y, side * 0.25, 1.1, skin, side=side, grip=True)
    elif mode == "table":
        for side in (-1, 1):
            x = 540 + side * 250 + sway_x * 0.4
            forearm(ctx, (x + side * 300, 2150), (x, 1640), 160, sleeve, skin)
            hand(ctx, x - side * 6, 1560, -side * 0.35, 1.2, skin, side=side)
    elif mode == "knock":
        k = abs(math.sin(t * 9)) if params.get("knocking") else 0
        x, y = 760 + sway_x, 1250 + k * 40
        forearm(ctx, (1120, 2150), (x + 30, y + 150), 150, sleeve, skin)
        hand(ctx, x + 10, y + 90, -0.35, 1.2, skin, side=-1, grip=True)


def _phone(ctx, sleeve, skin, t, params, sx, sy):
    pw, ph = 560, 1000
    px, py = 540 - pw / 2 + sx, 640 + sy
    # Hände: Handflächen HINTER dem Gerät, Daumen vorne auf dem Rand
    gy = py + ph - 260
    for side in (-1, 1):
        ex = 540 + side * (pw / 2 + 14) + sx
        forearm(ctx, (ex + side * 230, 2150), (ex + side * 40, gy + 230), 150, sleeve, skin)
        P.blob(ctx, [(ex - 70, gy - 40), (ex + 70, gy - 40), (ex + 80, gy + 150), (ex + side * 40, gy + 230),
                     (ex - 80, gy + 150)], skin)
    P.rrect(ctx, px - 22, py - 22, pw + 44, ph + 44, 60, "#1c1c22", 6)
    P.rrect(ctx, px, py, pw, ph, 42, "#ece5dd", 3)
    # Kopfzeile
    ctx.save()
    P.rrect_path(ctx, px, py, pw, ph, 42)
    ctx.clip()
    P.set_col(ctx, "#2f6f63")
    ctx.rectangle(px, py, pw, 150)
    ctx.fill()
    contact = params.get("contact", "Lina")
    P.ellipse(ctx, px + 80, py + 92, 34, 34, params.get("avatar", "#c4473a"), 3)
    P.text(ctx, contact[:1], px + 80, py + 106, 40, color="#ffffff")
    P.text(ctx, contact, px + 135, py + 88, 40, align="left", color="#ffffff")
    P.text(ctx, params.get("status", "online"), px + 135, py + 128, 26, align="left", color="#cfe9e2")
    # Nachrichten
    y = py + 190
    msgs = params.get("messages", [])
    for m in msgs:
        if t < m["at"]:
            if m.get("from") != "du" and t > m["at"] - 1.2:
                P.rrect(ctx, px + 24, y, 130, 64, 26, "#ffffff", 3)
                for k in range(3):
                    a = 0.4 + 0.6 * (math.sin(t * 8 - k) > 0)
                    P.ellipse(ctx, px + 60 + k * 30, y + 32, 9, 9, (0.5, 0.5, 0.5), 0, alpha=a)
            break
        pop = max(0.05, min(1.0, (t - m["at"]) / 0.18))
        mine = m.get("from") == "du"
        lines = P.wrap(ctx, m["text"], 34, pw - 170)
        bh = 30 + 44 * len(lines)
        ctx.select_font_face("Comic Neue")
        ctx.set_font_size(34)
        bw = max(ctx.text_extents(l).x_advance for l in lines) + 48
        bx = px + pw - 24 - bw if mine else px + 24
        ctx.save()
        ctx.translate(bx + bw / 2, y + bh / 2)
        ctx.scale(pop, pop)
        ctx.translate(-(bx + bw / 2), -(y + bh / 2))
        P.rrect(ctx, bx, y, bw, bh, 26, "#d4f5c4" if mine else "#ffffff", 3)
        for i, l in enumerate(lines):
            P.text(ctx, l, bx + 24, y + 52 + i * 44, 34, align="left", color="#1f1f1f")
        ctx.restore()
        y += bh + 22
    ctx.restore()
    for side in (-1, 1):
        ex = 540 + side * (pw / 2 + 22) + sx
        # Fingerspitzen, die um die Gerätekante greifen
        for f in range(3):
            P.rrect(ctx, ex - 18 - side * 4, gy - 60 + f * 46, 40, 40, 18, skin, 4.5)
        # Daumen auf der Vorderseite
        ctx.save()
        ctx.translate(540 + side * (pw / 2 - 20) + sx, gy + 170)
        ctx.rotate(-side * 0.55)
        P.rrect(ctx, -26, -110, 52, 140, 26, skin, 4.5)
        P.line(ctx, [(-12, -84), (12, -84)], 3)
        ctx.restore()
