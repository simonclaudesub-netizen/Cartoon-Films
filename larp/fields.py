"""Leuchtende Partikel- und Strang-Systeme (additiv gezeichnet, das Bloom kommt in fx.py)."""
import math

import cairo

from .hud import PAL, col, hsh, noise


def additive(ctx):
    ctx.set_operator(cairo.OPERATOR_ADD)


def normal(ctx):
    ctx.set_operator(cairo.OPERATOR_OVER)


def strands(ctx, srcs, dst, t, n=80, c=None, a=0.07, spread=120.0, seed=0, lw=1.0, dst_spread=60.0, bend=0.5):
    """Bündel feiner Bézier-Linien von mehreren Quellen zu einem Ziel ('Daten fließen ins Netz')."""
    c = c or PAL["white"]
    additive(ctx)
    ctx.set_line_width(lw)
    for si, (sx, sy) in enumerate(srcs):
        for k in range(n):
            r1, r2, r3, r4 = (hsh(seed, si, k, q) for q in range(4))
            x0 = sx + (r1 - 0.5) * spread
            y0 = sy
            x3 = dst[0] + (r2 - 0.5) * dst_spread
            y3 = dst[1] + (r3 - 0.5) * dst_spread * 0.6
            w = noise(t * 0.6 + r4 * 10, r1 * 10) * 40
            x1 = x0 + (r3 - 0.5) * spread * 1.6 + w
            y1 = y0 + (y3 - y0) * bend
            x2 = x3 + (r1 - 0.5) * spread * 1.2 - w
            y2 = y3 - (y3 - y0) * 0.35
            col(ctx, c, a * (0.4 + r4))
            ctx.move_to(x0, y0)
            ctx.curve_to(x1, y1, x2, y2, x3, y3)
            ctx.stroke()
    normal(ctx)


def fan(ctx, origin, targets, t, n=120, c=None, a=0.06, seed=0, lw=1.0, spread=500.0):
    """Fächer von einem Rand-Ursprung zu vielen Zielen (z.B. rosa Ströme von den Seiten)."""
    c = c or PAL["accent"]
    additive(ctx)
    ctx.set_line_width(lw)
    ox, oy = origin
    for k in range(n):
        r1, r2, r3 = hsh(seed, k, 1), hsh(seed, k, 2), hsh(seed, k, 3)
        tx, ty = targets[int(r1 * len(targets)) % len(targets)]
        y0 = oy + (r2 - 0.5) * spread
        w = noise(t * 0.8 + r3 * 7, r2 * 5) * 30
        col(ctx, c, a * (0.5 + r3))
        ctx.move_to(ox, y0)
        ctx.curve_to(ox + (tx - ox) * 0.45, y0 + w, tx - (tx - ox) * 0.3, ty + (r3 - 0.5) * 140, tx, ty + (r2 - 0.5) * 40)
        ctx.stroke()
    normal(ctx)


def pulses(ctx, srcs, dst, t, n=6, c=None, seed=0, r=3.0, speed=0.6):
    """Kleine helle Punkte, die die Stränge entlang wandern."""
    c = c or PAL["white"]
    additive(ctx)
    for si, (sx, sy) in enumerate(srcs):
        for k in range(n):
            u = (t * speed + hsh(seed, si, k)) % 1.0
            x = sx + (dst[0] - sx) * u + math.sin(u * 3.1) * (hsh(seed, k, 9) - 0.5) * 120
            y = sy + (dst[1] - sy) * (u ** 0.9)
            col(ctx, c, 0.9 * math.sin(u * math.pi))
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.fill()
    normal(ctx)


# ---------------------------------------------------------------- Kern-Glyphe (eigene Form)
RAYS = [(-1.62, 1.0, 1.0), (-1.05, 0.86, 0.9), (-0.48, 0.97, 1.05), (0.18, 0.78, 0.85), (0.74, 0.93, 1.0),
        (1.31, 0.88, 0.95), (1.93, 1.0, 1.1), (2.49, 0.82, 0.9), (3.05, 0.95, 1.0), (3.66, 0.8, 0.88),
        (4.22, 0.9, 1.0)]


def core(ctx, cx, cy, R, t, pal=PAL, spin=0.35, alpha=0.88, wire=True):
    """Rotierender 3D-Strahlenkern aus 11 abgerundeten Kristall-Strahlen (Drahtgitter-Optik)."""
    phi = math.sin(t * spin * 2) * 0.55 + t * 0.12
    tilt = math.sin(t * 0.7) * 0.18
    cphi, sphi = math.cos(phi), math.sin(phi)
    rays = []
    for i, (ang, ln, wd) in enumerate(RAYS):
        a = ang + t * 0.08
        dx, dy, dz = math.cos(a), math.sin(a), 0.25 * math.sin(i * 2.3)
        x = dx * cphi + dz * sphi
        z = -dx * sphi + dz * cphi
        y = dy * math.cos(tilt) - z * math.sin(tilt)
        z = dy * math.sin(tilt) + z * math.cos(tilt)
        rays.append((z, x, y, ln, wd, i))
    rays.sort()
    for z, x, y, ln, wd, i in rays:
        L = R * ln * (0.92 + 0.08 * math.sin(t * 2 + i))
        tx, ty = cx + x * L, cy + y * L
        d = math.hypot(x, y) or 1e-3
        nx, ny = -y / d, x / d
        hw = R * 0.078 * wd
        depth = 0.55 + 0.45 * (z + 1) / 2
        # Körper des Strahls: Trapez + runde Spitze
        ctx.move_to(cx + nx * hw * 0.55, cy + ny * hw * 0.55)
        ctx.line_to(tx + nx * hw, ty + ny * hw)
        ctx.line_to(tx - nx * hw, ty - ny * hw)
        ctx.line_to(cx - nx * hw * 0.55, cy - ny * hw * 0.55)
        ctx.close_path()
        col(ctx, pal["white"], alpha * depth * 0.75)
        ctx.fill_preserve()
        col(ctx, pal["white"], 0.95)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.arc(tx, ty, hw, 0, 2 * math.pi)
        col(ctx, pal["white"], alpha * depth)
        ctx.fill()
        if wire:  # Drahtgitter-Schraffur entlang des Strahls
            col(ctx, pal["bg"], 0.55)
            ctx.set_line_width(1.2)
            for q in range(5):
                f = (q + 1) / 6 - 0.5
                ctx.move_to(cx + nx * hw * 1.1 * f + x * R * 0.12, cy + ny * hw * 1.1 * f + y * R * 0.12)
                ctx.line_to(tx + nx * hw * 2 * f, ty + ny * hw * 2 * f)
            ctx.stroke()
            for q in range(1, 6):
                u = q / 6
                px, py = cx + (tx - cx) * u, cy + (ty - cy) * u
                w2 = hw * (0.55 + 0.45 * u)
                ctx.move_to(px - nx * w2, py - ny * w2)
                ctx.line_to(px + nx * w2, py + ny * w2)
            ctx.stroke()
    col(ctx, pal["white"], 1)
    ctx.arc(cx, cy, R * 0.09, 0, 2 * math.pi)
    ctx.fill()


# ---------------------------------------------------------------- Konfidenz-Fluss (Mono-Szene)
def _bez(p, s):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p
    m = 1 - s
    x = m ** 3 * x0 + 3 * m * m * s * x1 + 3 * m * s * s * x2 + s ** 3 * x3
    y = m ** 3 * y0 + 3 * m * m * s * y1 + 3 * m * s * s * y2 + s ** 3 * y3
    dx = 3 * m * m * (x1 - x0) + 6 * m * s * (x2 - x1) + 3 * s * s * (x3 - x2)
    dy = 3 * m * m * (y1 - y0) + 6 * m * s * (y2 - y1) + 3 * s * s * (y3 - y2)
    d = math.hypot(dx, dy) or 1
    return x, y, -dy / d, dx / d


RIVER = ((600, -60), (640, 700), (700, 1080), (-120, 1060))


def river(ctx, t, pal=PAL, n_dust=1400, path=RIVER):
    """Breiter Partikelstrom mit hellen Bändern, links zerfällt er in Pixel-Staub."""
    # grauer Nebel rechts vom Strom
    additive(ctx)
    for k in range(260):
        s = hsh(k, 1)
        x, y, nx, ny = _bez(path, s)
        off = 140 + hsh(k, 2) * 420
        col(ctx, pal["white"], 0.025 + 0.03 * hsh(k, 3))
        ctx.set_line_width(1 + hsh(k, 4) * 3)
        ctx.move_to(x - nx * off, y - ny * off)
        x2, y2, _, _ = _bez(path, min(1, s + 0.05))
        ctx.line_to(x2 - nx * off, y2 - ny * off)
        ctx.stroke()
    # helle Bänder
    bands = [(-40, 14, 0.5), (-12, 22, 0.9), (20, 10, 0.6), (44, 26, 0.85), (82, 8, 0.4), (104, 18, 0.7), (-70, 6, 0.3)]
    for bi, (off, w, a) in enumerate(bands):
        off = off + noise(t * 0.5, bi) * 6
        for layer, (lw, la) in enumerate(((w * 2.4, 0.06), (w, 0.22), (max(1.5, w * 0.25), 0.6))):
            col(ctx, pal["white"], la * a)
            ctx.set_line_width(lw)
            for i in range(61):
                s = i / 60
                x, y, nx, ny = _bez(path, s)
                o = off * (0.6 + 0.6 * s)
                (ctx.line_to if i else ctx.move_to)(x + nx * o, y + ny * o)
            ctx.stroke()
    # Längs-Fasern im Strom
    for k in range(120):
        o = (hsh(k, 7) - 0.4) * 200
        s0 = (hsh(k, 8) + t * 0.08 * (0.5 + hsh(k, 9))) % 1.0
        col(ctx, pal["white"], 0.12)
        ctx.set_line_width(1)
        for i in range(8):
            s = min(1, s0 + i * 0.012)
            x, y, nx, ny = _bez(path, s)
            (ctx.line_to if i else ctx.move_to)(x + nx * o, y + ny * o)
        ctx.stroke()
    normal(ctx)
    # Pixel-Staub links
    for k in range(n_dust):
        s = (hsh(k, 11) + t * 0.025 * (0.3 + hsh(k, 12))) % 1.0
        x, y, nx, ny = _bez(path, s)
        d = 60 + (hsh(k, 13) ** 2.2) * 520
        px, py = x + nx * d, y + ny * d
        px += noise(t + k, k) * 6
        sz = 2 + hsh(k, 14) * (11 - d / 70)
        if sz < 1.5:
            continue
        a = max(0.0, 1 - d / 600)
        if hsh(k, 15) > 0.55:
            col(ctx, pal["white"], 0.9 * a)
            ctx.rectangle(px, py, sz, sz)
            ctx.fill()
        else:
            col(ctx, pal["white"], 0.75 * a)
            ctx.set_line_width(1)
            ctx.rectangle(px + 0.5, py + 0.5, sz, sz)
            ctx.stroke()


# ---------------------------------------------------------------- Wirbel (Trading-Szene)
def vortex(ctx, cx, cy, rx, ry, t, pal=PAL, n=1900, depth=230):
    """Partikel-Wirbel / Trichter mit Bewegungsspuren."""
    additive(ctx)
    for gr, ga in ((1.25, 0.05), (0.95, 0.07), (0.6, 0.06)):
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, *pal["accent"], ga)
        g.add_color_stop_rgba(1, *pal["accent"], 0)
        ctx.save()
        ctx.translate(cx, cy + 40)
        ctx.scale(rx * gr, ry * gr * 1.6)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    ctx.set_line_width(1.6)
    cols = (pal["accent"], pal["accent2"], pal["white"])
    for k in range(n):
        r = 0.25 + 1.1 * hsh(k, 1) ** 0.7
        w = 0.9 / (r ** 1.4)
        th = hsh(k, 2) * 2 * math.pi + t * w
        drop = max(0, 0.95 - r) * depth
        seg = 0.08 + 0.12 * hsh(k, 3)
        c = cols[0] if hsh(k, 4) < 0.62 else (cols[1] if hsh(k, 4) < 0.85 else cols[2])
        front = (math.sin(th) + 1) / 2
        col(ctx, c, (0.22 + 0.6 * front) * (0.5 + 0.5 * hsh(k, 5)))
        for i in range(5):
            a = th - seg * i / 4
            x = cx + r * rx * math.cos(a)
            y = cy + r * ry * math.sin(a) + drop
            (ctx.line_to if i else ctx.move_to)(x, y)
        ctx.stroke()
    # heller Rand-Ring und Innenring
    for rr, aa, lw in ((1.0, 0.35, 2.5), (0.42, 0.5, 1.5)):
        col(ctx, pal["white"], aa)
        ctx.set_line_width(lw)
        ctx.save()
        ctx.translate(cx, cy + max(0, 0.95 - rr) * depth)
        ctx.scale(rr * rx, rr * ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.stroke()
    # Funken
    for k in range(260):
        th = hsh(k, 21) * 2 * math.pi + t * 0.6
        r = 0.9 + 0.3 * hsh(k, 22)
        col(ctx, pal["white"], 0.7 * hsh(k, 23))
        ctx.rectangle(cx + r * rx * math.cos(th), cy + r * ry * math.sin(th) - hsh(k, 24) * 60, 2, 2)
        ctx.fill()
    normal(ctx)


def grid(ctx, w, h, step=60, pal=PAL, a=0.05):
    col(ctx, pal["white"], a)
    for x in range(0, w + 1, step):
        for y in range(0, h + 1, step):
            ctx.rectangle(x - 1, y - 1, 2, 2)
    ctx.fill()


def ruler(ctx, x, y, w, n, pal=PAL, labels=True):
    """Lineal mit Zahlen (wie die Zeitleiste in der Bildmitte)."""
    col(ctx, pal["white"], 0.3)
    ctx.set_line_width(1)
    for i in range(n + 1):
        xx = x + w * i / n
        ctx.move_to(xx, y)
        ctx.line_to(xx, y + (8 if i % 5 == 0 else 4))
    ctx.stroke()
    if labels:
        from .hud import text
        for i in range(0, n + 1, 2):
            text(ctx, x + w * i / n, y + 20, f"{i:02d}", 9, pal["dim"], align="c", pal=pal)
