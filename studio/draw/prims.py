"""Zeichen-Grundbausteine im Studio-Stil: schwarze Konturen, flächige Farben.

Alle Formen werden mit Cairo als Vektoren gezeichnet. Konturen sind immer
INK (fast schwarz) mit runden Ecken, damit alles wie ein Comic aussieht.
"""
import math
import random

import cairo

INK = (0.07, 0.07, 0.09)
LW = 5.0  # Standard-Konturstärke in Pixeln (bei 1080 x 1920)


def rgb(c):
    """'#rrggbb' oder (r,g,b) -> (r,g,b) 0..1"""
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(c)


def shade(c, f):
    """Farbe abdunkeln (f<1) oder aufhellen (f>1)."""
    r, g, b = rgb(c)
    if f <= 1:
        return (r * f, g * f, b * f)
    return tuple(x + (1 - x) * (f - 1) for x in (r, g, b))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def set_col(ctx, c, alpha=1.0):
    r, g, b = rgb(c)
    ctx.set_source_rgba(r, g, b, alpha)


def ink(ctx, lw=LW, alpha=1.0):
    ctx.set_source_rgba(*INK, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)


def fill_stroke(ctx, color, lw=LW, alpha=1.0):
    """Aktuellen Pfad flächig füllen und schwarz umranden."""
    if color is not None:
        set_col(ctx, color, alpha)
        if lw:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if lw:
        ink(ctx, lw)
        ctx.stroke()
    elif color is None:
        ctx.new_path()


def poly(ctx, pts, color, lw=LW, close=True, alpha=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()
    fill_stroke(ctx, color if close else None, lw, alpha)


def line(ctx, pts, lw=LW, color=None):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if color is None:
        ink(ctx, lw)
    else:
        set_col(ctx, color)
        ctx.set_line_width(lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def rrect_path(ctx, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def rrect(ctx, x, y, w, h, r, color, lw=LW, alpha=1.0):
    rrect_path(ctx, x, y, w, h, r)
    fill_stroke(ctx, color, lw, alpha)


def ellipse_path(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def ellipse(ctx, cx, cy, rx, ry, color, lw=LW, rot=0.0, alpha=1.0):
    ellipse_path(ctx, cx, cy, rx, ry, rot)
    fill_stroke(ctx, color, lw, alpha)


def smooth_path(ctx, pts, closed=True, tension=0.5):
    """Catmull-Rom-Kurve durch Punkte (für organische Formen)."""
    n = len(pts)
    if n < 3:
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        return
    ctx.move_to(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        k = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def blob(ctx, pts, color, lw=LW, alpha=1.0):
    smooth_path(ctx, pts, True)
    fill_stroke(ctx, color, lw, alpha)


def limb(ctx, pts, width, color, lw=LW):
    """Arm/Bein als dicker, schwarz umrandeter Strich."""
    for w, col in ((width + 2 * lw, INK), (width, rgb(color))):
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.set_source_rgb(*col)
        ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def stains(ctx, x0, y0, x1, y1, color, n, seed, rmin=4, rmax=18, alpha=0.18):
    """Leichte Flecken/Verschmutzungen für detaillierte Hintergründe."""
    r = random.Random(seed)
    for _ in range(n):
        cx, cy = r.uniform(x0, x1), r.uniform(y0, y1)
        rad = r.uniform(rmin, rmax)
        pts = [(cx + math.cos(a) * rad * r.uniform(0.6, 1.2), cy + math.sin(a) * rad * r.uniform(0.6, 1.2))
               for a in [i * math.pi / 3 for i in range(6)]]
        smooth_path(ctx, pts, True)
        set_col(ctx, color, alpha)
        ctx.fill()


def text(ctx, s, x, y, size, family="Comic Neue", bold=True, color="#ffffff", outline=0,
         align="center", outline_color=INK):
    """Text zeichnen (optional mit Kontur). y = Grundlinie."""
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    if align == "center":
        x = x - ext.x_advance / 2
    elif align == "right":
        x = x - ext.x_advance
    ctx.move_to(x, y)
    ctx.text_path(s)
    if outline:
        ctx.set_source_rgb(*rgb(outline_color))
        ctx.set_line_width(outline)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    set_col(ctx, color)
    ctx.fill()
    return ext


def wrap(ctx, s, size, max_w, family="Comic Neue", bold=True):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if ctx.text_extents(t).x_advance > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines
