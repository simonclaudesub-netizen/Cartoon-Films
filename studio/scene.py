"""Setzt ein einzelnes Bild (Frame) einer Einstellung zusammen.

Ebenen: Hintergrund (gecacht) -> bewegte Details -> Figuren -> Vordergrund ->
Licht/Nacht-Färbung -> leuchtende Elemente -> POV-Hände -> Türspion-Maske ->
Einblendungen.
"""
import math
import zlib

import cairo
import numpy as np

from .draw import characters as C
from .draw import overlays as O
from .draw import pov as POV
from .draw import prims as P
from .draw import sets as S
from .draw.persp import W, H

M = 300  # Rand für Kamerabewegungen
E = 170  # Bildreserve für die Linsenverzeichnung
SS = 1.25  # Supersampling des Hintergrund-Caches (bleibt beim Zoomen scharf)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


class ShotRenderer:
    def __init__(self, shot, chars, label="", fps=30):
        self.shot = shot
        self.chars = chars
        self.label = label
        self.fps = fps
        self.set = S.make(shot["set"], shot.get("time", "day"), shot.get("variant"))
        zoom = shot.get("zoom", 1.0)
        self.set.cam.f *= zoom
        self.set.lights = [((W / 2 + (x - W / 2) * zoom, self.set.cam.cy + (y - self.set.cam.cy) * zoom), r * zoom, c, a)
                           for (x, y), r, c, a in self.set.lights]
        self.dur = shot["_dur"]
        self._bg = self._cache(self.set.back)
        self._fg = self._cache(self.set.front)
        self._maps = None
        self._keep = None

    def _cache(self, fn):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((W + 2 * M) * SS), int((H + 2 * M) * SS))
        ctx = cairo.Context(surf)
        ctx.scale(SS, SS)
        ctx.translate(M, M)
        fn(ctx)
        return surf

    def _blit(self, ctx, surf):
        ctx.save()
        ctx.translate(-M, -M)
        ctx.scale(1 / SS, 1 / SS)
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()
        ctx.restore()

    # ------------------------------------------------------------ Kamera
    def camera(self, t):
        cam = self.shot.get("camera", {}) or {}
        mv, st = cam.get("move", "static"), cam.get("strength", 1.0)
        k = ease(t / max(self.dur, 0.01))
        z, ox, oy, rot = 1.0, 0.0, 0.0, 0.0
        if mv == "push_in":
            z = 1.0 + 0.16 * st * k
        elif mv == "zoom_out":
            z = 1.0 + 0.16 * st * (1 - k)
        elif mv == "pan_left":
            ox, z = 90 * st * (1 - 2 * k), 1.08
        elif mv == "pan_right":
            ox, z = -90 * st * (1 - 2 * k), 1.08
        elif mv == "tilt_down":
            oy, z = -120 * st * (1 - k), 1.08
        # Handkamera-Gefühl (POV)
        ox += 9 * math.sin(t * 0.7) + 4 * math.sin(t * 1.9)
        oy += 7 * math.sin(t * 0.9 + 1.0)
        rot += 0.004 * math.sin(t * 0.5)
        for p in cam.get("punch", []):  # schneller Dramatik-Zoom
            if t >= p:
                z *= 1.0 + 0.14 * ease((t - p) / 0.15)
        for s in cam.get("shake", []):
            if s <= t < s + 0.6:
                a = 18 * (1 - (t - s) / 0.6)
                ox += a * math.sin(t * 83)
                oy += a * math.cos(t * 71)
        return z, ox, oy, rot

    # ------------------------------------------------------------ Figuren
    def _speaking(self, cid, t):
        for ln in self.shot.get("lines", []):
            if ln["speaker"] == cid and ln["_start"] <= t < ln["_start"] + ln["_dur"]:
                env = ln.get("_env", [])
                i = int((t - ln["_start"]) * self.fps)
                return ln, (env[i] if 0 <= i < len(env) else 0.0)
        return None, 0.0

    def draw_characters(self, ctx, t):
        cam = self.set.cam
        items = []
        for ch in self.shot.get("characters", []):
            spec = self.chars[ch["id"]]
            x, z = self.set.spots.get(ch.get("spot", ""), (ch.get("x", 0.0), ch.get("z", 3.0)))
            x, z = ch.get("x", x), ch.get("z", z)
            items.append((z, x, ch, spec))
        for z, x, ch, spec in sorted(items, key=lambda i: -i[0]):
            look = spec["look"]
            bob = 0.0
            enter = ch.get("enter")
            if enter:
                k = ease(t / 0.9)
                x = x + (-1.8 if enter == "left" else 1.8) * (1 - k)
                if k < 1:
                    bob = -abs(math.sin(t * 9)) * 0.03
            if ch.get("approach"):
                z = z + ch["approach"] * (1 - ease(t / max(self.dur, 0.1)))
            line, mouth = self._speaking(ch["id"], t)
            expr = (line or {}).get("expr") or ch.get("expr", "neutral")
            seed = zlib.crc32(ch["id"].encode()) % 1000 / 1000 * 3
            blink = 1.0 if ((t + seed) % 3.6) < 0.13 else 0.0
            sx, sy = cam.p(x, cam.eye + bob, z)
            s = C.scale_for(cam, z, look)
            C.draw(ctx, look, sx, sy, s, pose=ch.get("pose", "stand"), expr=expr, mouth=mouth, blink=blink,
                   t=t + seed, arms=(line or {}).get("arms") or ch.get("arms", "down"), prop=ch.get("prop"),
                   look_dir=ch.get("look", 0.0), silhouette=ch.get("silhouette", False),
                   talking=line is not None and mouth > 0.05)

    # ------------------------------------------------------------ Licht
    def grade(self, ctx, t):
        st = self.set
        if not st.night:
            return
        lvl = st.light_level(t)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_MULTIPLY)
        ctx.set_source_rgb(*(c * (0.55 + 0.45 * lvl) for c in st.tint))
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_ADD)
        for (cx, cy), r, col, a in st.lights:
            g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
            g.add_color_stop_rgba(0, *col, a * lvl)
            g.add_color_stop_rgba(1, *col, 0)
            ctx.set_source(g)
            ctx.paint()
        ctx.restore()

    # ------------------------------------------------------------ Linse
    def _lens_maps(self, k):
        """Tonnenverzeichnung (Weitwinkel/Türspion) als Remap-Tabelle für OpenCV."""
        import cv2
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy = W / 2, H / 2
        R = math.hypot(cx, cy)
        r2 = ((xs - cx) / R) ** 2 + ((ys - cy) / R) ** 2
        f = (1 + k * r2) / (1 + k * 0.3)
        sx = (cx + (xs - cx) * f + E).astype(np.float32)
        sy = (cy + (ys - cy) * f + E).astype(np.float32)
        return cv2.convertMaps(sx, sy, cv2.CV_16SC2)

    def _apply_lens(self, src):
        import cv2
        stride = src.get_stride()
        a = np.ndarray((H + 2 * E, stride // 4, 4), np.uint8, src.get_data())
        k = self.shot.get("lens", 0.0)
        if not k:
            out = np.ascontiguousarray(a[E:E + H, E:E + W])
        else:
            if self._maps is None:
                self._maps = self._lens_maps(k)
            out = cv2.remap(a, self._maps[0], self._maps[1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        self._keep = out
        return cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, W, H, W * 4)

    # ------------------------------------------------------------ Frame
    def frame(self, t):
        big = cairo.ImageSurface(cairo.FORMAT_ARGB32, W + 2 * E, H + 2 * E)
        ctx = cairo.Context(big)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        z, ox, oy, rot = self.camera(t)

        def cam_tf():
            ctx.translate(W / 2 + E, H / 2 + E)
            ctx.scale(z, z)
            ctx.rotate(rot)
            ctx.translate(-W / 2 + ox, -H / 2 + oy)

        ctx.save()
        cam_tf()
        self._blit(ctx, self._bg)
        self.set.dynamic(ctx, t)
        self.draw_characters(ctx, t)
        self._blit(ctx, self._fg)
        ctx.restore()
        ctx.save()
        ctx.translate(E, E)
        self.grade(ctx, t)
        ctx.restore()
        ctx.save()
        cam_tf()
        self.set.emissive(ctx, t)
        ctx.restore()
        big.flush()
        surf = self._apply_lens(big)
        ctx = cairo.Context(surf)
        pov = self.shot.get("pov")
        if pov and pov.get("mode", "none") != "none":
            ctx.push_group()
            POV.draw(ctx, pov["mode"], self.chars["du"]["look"], t, pov)
            if self.set.night and pov["mode"] != "phone":
                ctx.set_operator(cairo.OPERATOR_ATOP)
                ctx.set_source_rgba(0.04, 0.05, 0.14, 0.5)
                ctx.paint()
            ctx.pop_group_to_source()
            ctx.paint()
        if self.shot.get("peephole"):
            O.peephole(ctx)
        bo = self.shot.get("blackout_at")
        if bo is not None and t >= bo:
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
        fi = self.shot.get("fade_in", 0)
        if fi and t < fi:
            ctx.set_source_rgba(0, 0, 0, 1 - t / fi)
            ctx.paint()
        if self.shot.get("endcard"):
            O.endcard(ctx, self.shot["endcard"], t)
        if self.shot.get("caption"):
            O.caption(ctx, self.shot["caption"], t, self.shot.get("caption_dur", 2.2))
        if self.label:
            O.series_label(ctx, self.label)
        surf.flush()
        return surf
