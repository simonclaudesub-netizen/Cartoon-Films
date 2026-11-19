"""Die vier Dashboard-Welten des LARP-Kanals (Weltkoordinaten 1080 x 1920).

Jede Szene ist eine Funktion draw(ctx, t, cfg) – t läuft durchgehend weiter, auch über
Schnitte hinweg, damit Zähler, Logs und Partikel nie springen.

Alle Zahlen sind ausgedacht ("metrics illustrative") – das steht auch klein im Bild.
"""
import math

from . import fields as F
from . import hud as H
from .hud import MONO, PAL

W, HH = 1080, 1920


def _bg(ctx, pal):
    H.rect(ctx, 0, 0, W, HH, pal["bg"])
    F.grid(ctx, W, HH, 48, pal, 0.06)


def _header(ctx, left, mid, right, pal, y=22, hot=None):
    H.rect(ctx, 0, 0, W, y + 40, pal["bg"], 0.95)
    H.text(ctx, 18, y + 24, left, 19, pal["white"], bold=True, pal=pal)
    if hot:
        x = 18 + H.tw(ctx, left + " ", 19, True)
        H.text(ctx, x, y + 24, hot, 19, pal["accent"], bold=True, pal=pal)
    H.text(ctx, W / 2 + 120, y + 22, mid, 11, pal["dim"], align="c", pal=pal)
    H.text(ctx, W - 18, y + 22, right, 12, pal["accent"], align="r", bold=True, pal=pal)
    H.col(ctx, pal["edge"], 0.12)
    ctx.set_line_width(1)
    ctx.move_to(0, y + 40)
    ctx.line_to(W, y + 40)
    ctx.stroke()


def _footer(ctx, left, right, pal, y=1898):
    H.text(ctx, 14, y, left, 11, pal["dim"], pal=pal)
    H.text(ctx, W - 14, y, right, 11, pal["dim"], align="r", pal=pal)


# =====================================================================  1) AGENT OPS
TOP = [
    ("agent.core", "122/s", [("budget", "$2,000 / mo"), ("model", "vek-2.1"), ("mode", "delegate"), ("workers", "14")]),
    ("whatsapp.inbox", "174/s", [("open chats", "20-50"), ("window", "24h · free"), ("replies", "1,200"), ("status", "live")]),
    ("knowledge.index", "124/s", [("prices", "loaded"), ("policies", "loaded"), ("faqs", "48 / 48"), ("store", "vector · $25")]),
    ("sources", "173/s", [("scope", "public"), ("city", "Austin"), ("niche", "dental"), ("records", "240 / 240")]),
    ("guardrails", "88/s", [("send", "ask first"), ("prices", "locked"), ("spend cap", "$500"), ("actions", "sandboxed")]),
]


def agent_ops(ctx, t, cfg):
    pal = PAL
    _bg(ctx, pal)
    _header(ctx, f"{cfg['system']} / AGENT OPS", f"system one · {cfg['version']} · 14 workers",
            "● LIVE", pal)
    # obere Panel-Reihe (läuft links/rechts aus dem Bild – wirkt dichter)
    pw, gap, x0, y0, ph = 262, 12, -116, 78, 300
    srcs = []
    for i, (title, rate, rows) in enumerate(TOP):
        x = x0 + i * (pw + gap)
        yy = H.panel(ctx, x, y0, pw, ph, title, "▪ " + rate, pal, hot=(int(t * 1.2) % 5 == i))
        H.kv(ctx, x + 14, yy + 14, pw - 28, rows, 13, 22, pal)
        H.spark(ctx, x + 14, y0 + 150, pw - 28, 46, t, i + 3, pal["accent"] if i % 2 else pal["white"], pal=pal, lw=1.3)
        H.bars(ctx, x + 14, y0 + ph - 92, pw - 28, 78, 22, t, seed=i * 11, pal=pal)
        srcs.append((x + pw / 2, y0 + ph))
    # Netz aus feinen Strängen von oben in den Kern
    cx, cy = 540, 1010
    F.strands(ctx, srcs, (cx, cy), t, n=150, a=0.12, spread=230, seed=3, dst_spread=220, bend=0.25)
    F.pulses(ctx, srcs, (cx, cy), t, n=5, seed=4)
    for k in range(16):
        x = 40 + k * 66 + H.noise(t * 0.3, k) * 10
        y = 470 + H.hsh(k, 3) * 150
        H.tag(ctx, x, y, str(int(100 + H.hsh(k, 5) * 900)), pal, size=10, a=0.85)
    F.ruler(ctx, 0, 662, W, 60, pal)
    # rosa Fächer von den Seiten
    tgt = [(cx - 160, cy - 120), (cx - 60, cy + 80), (cx + 120, cy - 60), (cx + 40, cy + 160)]
    F.fan(ctx, (-20, 1010), tgt, t, n=220, a=0.13, seed=8, spread=600, lw=1.2)
    F.fan(ctx, (W + 20, 1010), tgt, t, n=220, a=0.13, seed=9, spread=600, lw=1.2)
    # Panels um den Kern
    left = [("schedule", "plan", [("D1-2", "prototype"), ("D3-7", "kb · qualify"), ("D8-13", "live · demo"), ("D14", "close")]),
            ("lead.json", "", [("fields", "name · need · budget"), ("schema", "typed"), ("written", f"{int(150 + t * 4)}"), ("state", "typed")]),
            ("price_gate", "gate 3", [("value", "$500 / mo"), ("on_missing", "STOP · ASK"), ("owner", "you"), ("status", "resolved")])]
    right = [("vector.db", "", [("rows", "1,536"), ("chunks", "620"), ("cost", "$25 / mo"), ("recall", "0.94")]),
             ("deploy.live", "gate 2", [("host", "$20 / mo"), ("url", "public"), ("uptime", "99.9%"), ("status", "live")]),
             ("your_call", "gate 1", [("input", "$500 / mo"), ("authority", "human"), ("offer", "ready"), ("send", "not approved")])]
    for col_x, items in ((150, left), (590, right)):
        for j, (title, r, rows) in enumerate(items):
            y = 760 + j * 190
            yy = H.panel(ctx, col_x, y, 340, 172, title, r, pal, alpha=0.82, hot=(title == "your_call"))
            H.kv(ctx, col_x + 14, yy + 18, 312, rows, 13, 26, pal,
                 vcol=pal["text"])
    # Seitenleisten
    yy = H.panel(ctx, -20, 760, 160, 540, "drafts", "", pal, alpha=0.8)
    for k in range(18):
        s = ["draft-07.md", "source-linked", "one detail", "/contact", "verified", "sent: false",
             "sending", "pending", "sampled"][k % 9]
        H.text(ctx, -6, yy + 14 + k * 27, s, 12, pal["accent"] if "pending" in s else pal["dim"], pal=pal)
    yy = H.panel(ctx, 940, 760, 160, 260, "kb.index", "", pal, alpha=0.8)
    H.kv(ctx, 954, yy + 16, 120, [("chunks", "620"), ("faqs", "48"), ("store", "vec")], 12, 24, pal)
    yy = H.panel(ctx, 940, 1040, 160, 260, "pipeline", "", pal, alpha=0.8, hot=True)
    H.kv(ctx, 954, yy + 16, 120, [("clients", "0"), ("price", "$500"), ("pot.", "$2k"), ("sent", "0")], 12, 24, pal)
    # Kern-Glyphe
    F.core(ctx, cx, cy, 300, t)
    # Banner
    H.rect(ctx, 150, 1338, 780, 62, pal["panel"], 0.95)
    H.frame(ctx, 150, 1338, 780, 62, pal["edge"], 0.25)
    H.rect(ctx, 150, 1338, 5, 62, pal["accent"])
    H.text(ctx, 172, 1364, "DAYS 10-13 · DEMO + OUTREACH", 18, pal["white"], bold=True, pal=pal)
    H.text(ctx, 172, 1388, "25 demos → 25 drafts → 6 calls → 0 sent without you", 12, pal["dim"], pal=pal)
    # untere Reihe
    y0 = 1420
    yy = H.panel(ctx, -10, y0, 280, 380, "STREAM", "4 l/s", pal)
    ent = [("opener", "send: disabled"), ("slot", "TUE 10:30 booked"), ("$500", "client #2"),
           ("progress", "saved after call"), ("spend", "$0.41 / $1.00"), ("draft", "personalized"),
           ("lead", "qualified · 0.91"), ("ask", "human approval"), ("kb", "chunk 412 recalled")]
    H.log(ctx, 6, yy, 250, 330, ent, t, rate=3.0, size=12, pal=pal, cols=[0, 0.36])
    yy = H.panel(ctx, 280, y0, 260, 380, "DISPATCH", "6 workers", pal)
    names = ["maps.pull", "kb.load", "qualify", "deploy", "outreach", "close"]
    for k, nm in enumerate(names):
        v = min(1, max(0, (t * 0.18 + 1.2 - k * 0.2)))
        H.text(ctx, 292, yy + 20 + k * 26, f"w{k + 1}  {nm}", 12, pal["text"], pal=pal)
        H.progress(ctx, 410, yy + 10 + k * 26, 80, 10, v, pal["white"] if v >= 1 else pal["accent"], pal, segs=12)
        H.text(ctx, 528, yy + 20 + k * 26, "done" if v >= 1 else f"{int(v * 100)}%", 11,
               pal["dim"] if v >= 1 else pal["accent"], align="r", pal=pal)
    H.wave(ctx, 292, y0 + 250, 236, 100, t, 3, pal["accent"], pal, amp=0.35, freq=14)
    H.text(ctx, 292, y0 + 368, f"tok/s {int(2800 + H.noise(t, 2) * 300):,}", 11, pal["dim"], pal=pal)
    yy = H.panel(ctx, 550, y0, 260, 380, "FORMULAS · LIVE", "eval 3/7", pal)
    H.kv(ctx, 564, yy + 18, 232, [("chats", "Σ inbox"), ("conv", "0.20"), ("cost/chat", "$0.08"),
                                  ("infra", "$166"), ("MRR", "$0", pal["accent"]), ("margin", "-$166", pal["accent"]),
                                  ("p(close)", f"{0.86 + 0.01 * math.sin(t):.3f}")], 13, 30, pal)
    H.text(ctx, 564, y0 + 368, "gate: p ≥ 0.85 → ask you", 11, pal["dim"], pal=pal)
    yy = H.panel(ctx, 820, y0, 280, 380, "OUTPUT / RATE", "", pal, hot=True)
    H.text(ctx, 834, yy + 80, "$0", 78, pal["white"], bold=True, pal=pal)
    H.text(ctx, 834, yy + 108, "0 of 4 · $500 · modeled", 12, pal["dim"], pal=pal)
    H.bars(ctx, 834, yy + 130, 240, 120, 16, t, seed=77, pal=pal, palette=(pal["accent"], pal["accent2"]))
    H.text(ctx, 834, y0 + 368, "· human approval required", 11, pal["accent"], pal=pal)
    _footer(ctx, f"{cfg['system']} · agent ops", "metrics illustrative · simulated", pal)


# =====================================================================  2) DECISION PIPELINE
COLS = [
    [("Noul · worth_reply", "yes / no", "0.91"), ("Score · lead_quality", "labels", "0.85"),
     ("Choice · action", "legal acts", "reply"), ("Score · viral_fit", "views", "0.72"),
     ("Score · urgency", "routed", "0.64"), ("Choice · next_worker", "research", "write"),
     ("Noul · safe_to_run", "sandbox", "yes")],
    [("choice head", "one label", "0.93"), ("no generation", "structured", "free"),
     ("state encoder", "JSON-in", "packed"), ("score head", "ordered", "0.88"),
     ("median latency", "public", "~256ms"), ("noul head", "yes / no", "0.97"), ("cost", "per 1M", "$0.042")],
    [("quarantine", "phishing", "held"), ("draft reply", "worth it", "LLM"), ("book_call", "calendar", "sent?"),
     ("type_destination", "folder", "/leads"), ("draft_short", "clip", "60s"), ("eng_oncall", "critical", "page"),
     ("review", "human gate", "you")],
]


def pipeline(ctx, t, cfg):
    pal = PAL
    _bg(ctx, pal)
    _header(ctx, f"{cfg['system']} / DECISION PIPELINE", "STATE → QUESTIONS → VEK → GATE → CODE",
            f"system one · {cfg['version']}", pal)
    # Kennzahlen
    k = int(5597 + t * 61)
    H.kpi(ctx, 8, 76, 352, 150, "DECISIONS · THIS RUN", f"{k:,}", "one loop × 10 000", t, 1, pal)
    H.progress(ctx, 20, 196, 200, 6, (k % 10000) / 10000, pal["accent"], pal, segs=30)
    H.kpi(ctx, 366, 76, 352, 150, "MEDIAN LATENCY · REPORTED", f"~{int(256 + H.noise(t, 4) * 6)}ms",
          "public demos · not SLAs", t, 2, pal)
    H.kpi(ctx, 724, 76, 352, 150, "COST · 10 000 DECISIONS", "≈$0.42", "$0.042 / M in · out free", t, 3, pal,
          vcol=pal["accent"], spark_on=False)
    # Tabs
    H.rect(ctx, 0, 240, 150, 40, pal["accent"], 0.9)
    H.text(ctx, 12, 266, "CASE 04 / 12", 14, pal["white"], bold=True, pal=pal)
    H.text(ctx, 166, 268, "✕ FEED POST", 22, pal["white"], bold=True, pal=pal)
    tabs = ["STATE", "ASK", "VEK", "GATE", "CODE"]
    act = int(t * 1.6) % 5
    for i, s in enumerate(tabs):
        x = 690 + i * 78
        H.rect(ctx, x, 246, 70, 28, pal["accent"] if i == act else pal["panel"], 0.95)
        H.frame(ctx, x, 246, 70, 28, pal["edge"], 0.3)
        H.text(ctx, x + 35, 265, s, 12, pal["white"], bold=True, align="c", pal=pal)
    # Karten-Spalten + Stränge
    xs, cw, ch, gy, y0 = (24, 394, 764), 292, 112, 20, 300
    pos = []
    for ci, items in enumerate(COLS):
        pos.append([(xs[ci], y0 + j * (ch + gy)) for j in range(len(items))])
    F.additive(ctx)
    for ci in range(2):
        for j, (ax, ay) in enumerate(pos[ci]):
            for jj, (bx, by) in enumerate(pos[ci + 1]):
                if H.hsh(ci, j, jj) > 0.45:
                    continue
                for s in range(9):
                    r = H.hsh(ci, j, jj, s)
                    c = pal["accent"] if r < 0.25 else pal["white"]
                    H.col(ctx, c, 0.05 + 0.1 * r)
                    ctx.set_line_width(1)
                    x0, y_0 = ax + cw, ay + 30 + r * 60
                    x3, y3 = bx, by + 30 + H.hsh(s, j) * 60
                    wob = H.noise(t * 0.7 + s, r * 9) * 25
                    ctx.move_to(x0, y_0)
                    ctx.curve_to(x0 + 60 + wob, y_0, x3 - 60 - wob, y3, x3, y3)
                    ctx.stroke()
    # lange vertikale Lichtfasern zwischen den Spalten
    for g, gx in enumerate((350, 722)):
        for s in range(40):
            r = H.hsh(g, s, 5)
            H.col(ctx, pal["white"] if r > 0.3 else pal["accent"], 0.06 + 0.08 * r)
            ctx.set_line_width(1)
            x = gx + (r - 0.5) * 50
            ctx.move_to(x, 290)
            ctx.curve_to(x + H.noise(t * 0.5, s) * 40, 700, x - H.noise(t * 0.4, s + 3) * 40, 1000, x + (r - .5) * 30, 1240)
            ctx.stroke()
    F.normal(ctx)
    for ci, items in enumerate(COLS):
        for j, (title, sub, val) in enumerate(items):
            x, y = pos[ci][j]
            hot = (int(t * 2) % 7 == j and ci == int(t * 2 / 7) % 3)
            H.rect(ctx, x, y, cw, ch, pal["panel"], 0.88)
            H.frame(ctx, x, y, cw, ch, pal["accent"] if hot else pal["edge"], 0.6 if hot else 0.15)
            H.rect(ctx, x + 10, y + 16, 6, 6, pal["accent"] if "Score" in title or hot else pal["white"])
            H.text(ctx, x + 24, y + 24, title, 14, pal["white"], bold=True, pal=pal)
            H.text(ctx, x + 12, y + 50, sub, 11, pal["dim"], pal=pal)
            H.text(ctx, x + 12, y + 70, "confidence", 11, pal["dim"], pal=pal)
            H.text(ctx, x + cw - 12, y + 52, val, 13, pal["accent"] if hot else pal["text"], align="r", pal=pal)
            H.progress(ctx, x + 12, y + 86, cw * 0.55, 4, 0.4 + 0.5 * H.hsh(ci, j), pal["white"], pal)
            for e in (x, x + cw):
                H.col(ctx, pal["white"], 0.9)
                ctx.arc(e, y + 56, 3.2, 0, 6.283)
                ctx.fill()
    # rosa Licht-Orb wandert durch die Pipeline
    u = (t * 0.22) % 1.0
    ox = 60 + u * 960
    oy = 600 + math.sin(u * 7) * 240
    F.additive(ctx)
    for rr, aa in ((60, 0.06), (30, 0.15), (12, 0.6), (5, 1.0)):
        H.col(ctx, pal["accent"] if rr > 10 else pal["white"], aa)
        ctx.arc(ox, oy, rr, 0, 6.283)
        ctx.fill()
    H.col(ctx, pal["accent"], 0.5)
    ctx.set_line_width(10)
    ctx.move_to(-10, 860)
    ctx.line_to(330, 860)
    ctx.stroke()
    F.normal(ctx)
    # unten: vier Panels
    y1 = 1250
    yy = H.panel(ctx, 6, y1, 262, 270, "PARALLEL QUESTIONS", "one state", pal)
    for i, (nm, c) in enumerate((("Choice A", pal["white"]), ("Choice B", pal["accent"]), ("Score A", pal["cyan"]),
                                 ("Score B", pal["cyan"]), ("Noul A", pal["white"]), ("Noul B", pal["white"]))):
        H.text(ctx, 18, yy + 22 + i * 32, nm, 12, pal["dim"], pal=pal)
        H.progress(ctx, 100, yy + 12 + i * 32, 150, 9, 0.2 + 0.75 * abs(math.sin(t * 0.7 + i)), c, pal)
    yy = H.panel(ctx, 276, y1, 262, 270, "CONFIDENCE STREAM", "SIM", pal)
    for s, c in enumerate((pal["white"], pal["accent"], pal["yellow"], pal["cyan"])):
        H.wave(ctx, 288, yy + 10, 238, 190, t + s, s * 3 + 1, c, pal, lw=1.8, amp=0.38)
    H.col(ctx, pal["white"], 0.3)
    ctx.set_dash([4, 4])
    ctx.move_to(288, yy + 60)
    ctx.line_to(526, yy + 60)
    ctx.stroke()
    ctx.set_dash([])
    yy = H.panel(ctx, 546, y1, 262, 270, "12 USE CASES", "case 04", pal)
    uc = ["email", "youtube", "skool", "feed", "meetings", "clips", "contracts", "leads", "brain-dump",
          "support", "trading", "agents"]
    hl = int(t * 2.2) % 12
    for i, s in enumerate(uc):
        x, y = 558 + (i % 3) * 82, yy + 10 + (i // 3) * 54
        H.rect(ctx, x, y, 76, 46, pal["accent"] if i == hl else pal["white"], 0.9 if i == hl else 0.06)
        H.text(ctx, x + 6, y + 16, f"{i + 1:02d}", 10, pal["white"] if i == hl else pal["dim"], pal=pal)
        H.text(ctx, x + 6, y + 36, s, 12, pal["white"], bold=True, pal=pal)
    yy = H.panel(ctx, 816, y1, 270, 270, "chief.py", "14 l", pal)
    H.code(ctx, 820, yy - 6, 264, 230, CHIEF, t, cps=30, size=11, pal=pal)
    y2 = 1530
    yy = H.panel(ctx, 6, y2, 400, 270, "RUN LOG", "5 l/s", pal)
    ent = [("human", "review requested"), ("save", "progress after call"), ("wait", "actions 7/10 · spend ok"),
           ("Choice", "next_worker → write"), ("write", "0.93 · 3ms"), ("Choice", "folder → /leads"),
           ("Noul", "worth_reply · yes"), ("gate", "0.91 ≥ 0.85 pass")]
    H.log(ctx, 20, yy, 372, 220, ent, t, rate=5, size=12, pal=pal, cols=[0, 0.24])
    yy = H.panel(ctx, 414, y2, 330, 270, "THE SPLIT", "who does what", pal)
    for i, (nm, v, c) in enumerate((("LLM writes", 0.25, pal["white"]), ("VEK decides", 0.95, pal["accent"]),
                                    ("code acts", 0.7, pal["cyan"]))):
        H.text(ctx, 428, yy + 34 + i * 54, nm, 14, pal["text"], pal=pal)
        H.progress(ctx, 560, yy + 22 + i * 54, 170, 14, v * (0.9 + 0.1 * math.sin(t * 3 + i)), c, pal, segs=18)
    yy = H.panel(ctx, 752, y2, 334, 270, "GUARDRAILS", "always", pal, hot=True)
    H.text(ctx, 766, yy + 30, "spend cap", 13, pal["dim"], pal=pal)
    H.progress(ctx, 880, yy + 20, 120, 12, 0.28, pal["yellow"], pal)
    H.text(ctx, 1076, yy + 30, "$0.28 / 1", 12, pal["text"], align="r", pal=pal)
    H.text(ctx, 766, yy + 70, "actions", 13, pal["dim"], pal=pal)
    H.progress(ctx, 880, yy + 60, 120, 12, 0.4, pal["accent"], pal, segs=10)
    H.text(ctx, 1076, yy + 70, "4 / 10", 12, pal["text"], align="r", pal=pal)
    H.text(ctx, 766, yy + 120, "▣ never auto-post to X", 14, pal["white"], pal=pal)
    H.text(ctx, 766, yy + 150, "▣ human gets the last word", 14, pal["white"], pal=pal)
    H.text(ctx, 766, yy + 180, "▣ sandboxed actions", 14, pal["white"], pal=pal)
    H.text(ctx, W / 2, 1850, "LLM WRITES · VEK DECIDES · CODE ACTS", 22, pal["white"], bold=True, align="c", pal=pal)
    _footer(ctx, f"{cfg['system']} · pipeline", "metrics illustrative · prices and gate from the run", pal)


CHIEF = [
    "# chief.py",
    "from vektor import Client, Choice",
    "client = Client(model=\"vek-2.1.4\")",
    "",
    "state = {\"goal\": goal,",
    "         \"done\": notes}",
    "result = client.decide(",
    "    state=state,",
    "    questions={",
    "      \"next_worker\": Choice(",
    "        [\"research\", \"write\",",
    "         \"review\"]),",
    "    })",
    "assert result.confidence >= 0.85",
]


# =====================================================================  3) MONO CONFIDENCE FIELD
MONO_CODE = [
    "class Guard:",
    "    spend_cap = 1.00",
    "    max_actions = 10",
    "    auto_post = False          # never to X",
    "",
    "    def check(self, run):",
    "        assert run.cost <= self.spend_cap",
    "        assert run.actions <= self.max_actions",
    "        run.save_progress()     # resume later",
    "",
    "async def loop(inbox):",
    "    async for state in inbox.stream():",
    "        res = decide(state)",
    "        log.write(state.id, res, ms=res.latency)",
    "        Guard().check(res.run)",
    "",
    "def calibrate(samples):",
    "    ok = [s for s in samples if s.correct]",
    "    return len(ok) / len(samples)",
    "",
    "def explain(ans):",
    "    return {",
    "        \"label\": ans.label,",
    "        \"confidence\": round(ans.confidence, 2),",
    "        \"who_acts\": \"code\" if ans.confidence >= 0.85",
    "                    else \"human\",",
    "    }",
]


def mono_field(ctx, t, cfg):
    pal = MONO
    H.rect(ctx, 0, 0, W, HH, (0, 0, 0))
    _header(ctx, "/ CONFIDENCE FIELD · MONO", f"{int(12482 + t * 37):,}   ~260 ms   ≈ $0.42   0.85",
            "■ LIVE", pal)
    F.river(ctx, t, pal)
    # Achse rechts vom Feld
    for i in range(10):
        y = 130 + i * 105
        H.text(ctx, 752, y, f"{1 - i / 10:.1f}", 11, pal["dim"], align="r", pal=pal)
        H.col(ctx, pal["white"], 0.3)
        ctx.move_to(758, y - 4)
        ctx.line_to(768, y - 4)
        ctx.stroke()
    gy = 130 + 1.5 * 105 - 4
    H.col(ctx, pal["white"], 0.5)
    ctx.set_dash([6, 6])
    ctx.set_line_width(1)
    ctx.move_to(300, gy)
    ctx.line_to(770, gy)
    ctx.stroke()
    ctx.set_dash([])
    H.callout(ctx, 520, gy - 22, "GATE 0.85", pal=pal, inverted=True, size=14)
    H.text(ctx, 700, gy - 34, "pass ↑ code acts", 11, pal["text"], align="r", pal=pal)
    H.text(ctx, 700, gy + 34, "review ↓ human", 11, pal["dim"], align="r", pal=pal)
    case = ["worth_reply · yes · 0.91", "phishing · quarantine · 0.97", "lead_quality · 0.85",
            "book_call · ask · 0.72"][int(t / 2.2) % 4]
    H.text(ctx, 440, gy + 62, "case 02 · youtube", 11, pal["dim"], pal=pal)
    w, h = H.callout(ctx, 430, gy + 72, "→ " + case, pal=pal, inverted=True, size=14)
    H.col(ctx, pal["white"], 0.8)
    ctx.move_to(430, gy + 72 + h / 2)
    ctx.line_to(250, gy + 82)
    ctx.stroke()
    bx, by = 222 + H.noise(t * 0.4, 1) * 10, gy + 62
    for dx, dy in ((0, 0), (36, 0), (0, 36), (36, 36)):
        ctx.move_to(bx + dx + (8 if dx == 0 else -8), by + dy)
        ctx.line_to(bx + dx, by + dy)
        ctx.line_to(bx + dx, by + dy + (8 if dy == 0 else -8))
    ctx.stroke()
    H.callout(ctx, 110, 590, "STATE · email", "ask · choice", pal=pal, size=14)
    H.callout(ctx, 420, 790, f"{cfg['system']} DECIDES · NEVER CHATS", "typed answers · zero tokens out", pal=pal, size=15)
    # rechte Spalte
    H.rect(ctx, 780, 62, 300, 1130, (0.02, 0.02, 0.02), 1)
    H.frame(ctx, 780, 62, 300, 1130, pal["edge"], 0.2)
    H.text(ctx, 792, 112, cfg["system"][:3], 40, pal["white"], bold=True, pal=pal)
    H.text(ctx, 900, 92, "SYSTEM ONE", 11, pal["white"], bold=True, pal=pal)
    H.text(ctx, 900, 110, "decides · never chats", 11, pal["dim"], pal=pal)
    H.text(ctx, 792, 150, "Heads state", 13, pal["white"], bold=True, pal=pal)
    hdr = ["st", "ask", "gate", "code", "llm"]
    for i, s in enumerate(hdr):
        H.text(ctx, 830 + i * 52, 176, s, 10, pal["dim"], align="c", pal=pal)
    for r in range(13):
        y = 200 + r * 40
        for c in range(5):
            v = H.hsh(r, c, int(t * 4 + r))
            x = 808 + c * 52
            if (r + c) % 3 == 0:
                H.progress(ctx, x, y - 9, 44, 8, v, pal["white"], pal, segs=5)
            else:
                H.text(ctx, x + 22, y, f"{v:.2f}" if v < 0.99 else "1.0", 11,
                       pal["white"] if v > 0.8 else pal["dim"], align="c", pal=pal)
    H.text(ctx, 792, 740, "meters", 11, pal["dim"], pal=pal)
    for i in range(8):
        x = 800 + i * 34
        v = 0.3 + 0.65 * abs(H.noise(t * 1.3, i))
        for s in range(16):
            on = s / 16 < v
            H.rect(ctx, x, 1150 - s * 24, 22, 18, pal["white"], 0.9 if on else 0.08)
    # Statuszeile
    H.rect(ctx, 0, 1196, W, 34, (0.06, 0.06, 0.06))
    H.text(ctx, 12, 1218, f"■ field · code · heads   llm.idle   {cfg['system'].lower()}.ask 241ms   "
                          f"gate {0.71 + 0.2 * abs(math.sin(t)):.2f} HOLD → human   calendar.send_link", 12, pal["text"], pal=pal)
    # unten: Code + Tabellen
    H.rect(ctx, 0, 1236, 650, 600, (0.02, 0.02, 0.02))
    H.code(ctx, 6, 1240, 640, 590, MONO_CODE, t, cps=42, size=13, pal=pal, start=-6, lineno=31,
           hl_line=int(t * 0.8) % 20)
    x0 = 662
    yy = H.panel(ctx, x0, 1240, 414, 190, "ROUTER", "last 6", pal)
    rows = [("02", "worth_reply", "code", "0.91"), ("01", "phishing", "code", "0.97"), ("12", "click", "code", "0.91"),
            ("08", "lead_quality", "human", "0.82"), ("02", "worth_reply", "code", "0.98"), ("01", "billing", "code", "0.94")]
    for i, (a, b, c, d) in enumerate(rows):
        y = yy + 16 + i * 22
        H.text(ctx, x0 + 12, y, a, 12, pal["dim"], pal=pal)
        H.text(ctx, x0 + 46, y, b, 12, pal["white"], pal=pal)
        H.text(ctx, x0 + 250, y, c, 12, pal["white"] if c == "code" else pal["dim"], bold=True, pal=pal)
        H.text(ctx, x0 + 400, y, d, 12, pal["text"], align="r", pal=pal)
    yy = H.panel(ctx, x0, 1440, 414, 150, "LATENCY", "p50 ~263 ms", pal)
    for i in range(48):
        u = (i - 24) / 7
        v = math.exp(-u * u / 2) * (0.85 + 0.15 * H.noise(t * 2, i))
        H.rect(ctx, x0 + 14 + i * 8, yy + 100 - v * 90, 5, v * 90, pal["white"], 0.9)
    yy = H.panel(ctx, x0, 1600, 414, 120, "CONFIDENCE", "gate 0.85", pal)
    for i in range(60):
        x = x0 + 14 + H.hsh(i, 1) * 386
        y = yy + 8 + ((H.hsh(i, 2) + t * 0.05 * H.hsh(i, 3)) % 1) * 70
        H.col(ctx, pal["white"], 0.85)
        if i % 2:
            ctx.rectangle(x, y, 4, 4)
            ctx.fill()
        else:
            ctx.arc(x, y, 3, 0, 6.283)
            ctx.set_line_width(1)
            ctx.stroke()
    yy = H.panel(ctx, x0, 1730, 414, 110, "TOKENS OUT", f"{cfg['system'].lower()} never generates", pal)
    H.text(ctx, x0 + 14, yy + 56, "0", 56, pal["white"], bold=True, pal=pal)
    H.text(ctx, x0 + 64, yy + 30, "tokens out · free", 12, pal["text"], pal=pal)
    H.text(ctx, x0 + 64, yy + 50, "in $0.042 / M", 12, pal["dim"], pal=pal)
    _footer(ctx, f"{cfg['system']} · confidence field", "metrics illustrative · simulated", pal)


# =====================================================================  4) TRADING DESK
DESK_CODE = [
    "from vek import choice, score, ask, gate",
    "from desk import Desk, Operator, Book",
    "",
    "desk = Desk(ops=6, perms=\"explicit\")",
    "book = Book([\"BTC\", \"ETH\", \"SOL\", \"HYPE\"])",
    "",
    "@desk.on(\"tick\")",
    "def on_tick(tick):",
    "    ctx = analyst.share(tick)",
    "    act = ask(\"act?\", ctx)",
    "    if not act:",
    "        return reporter.skip(tick)",
    "    side = choice([\"LONG\", \"SHORT\"], ctx)",
    "    size = score(\"size\", ctx)",
    "    chk = risk.evaluate(side, size)",
    "    if gate(chk.conf) < 0.85:",
    "        return human.review(chk)",
    "    executor.paper_fill(side, size)  # sim",
]


def _desk_log():
    who = ["core", "watcher", "analyst", "ask", "choice", "risk", "gate", "executor", "reporter"]
    msg = ["absorbed ctx #4471", "BTC 84,212", "ctx 4471 p=0.91", "act? p=0.91", "LONG conf=0.93",
           "dd 0.4% limits ok", "0.93 ≥ 0.85", "PAPER 0.34 BTC-PERP", "evidence #4471", "HYPE 88.78",
           "LONG conf=0.95", "PAPER 0.21 HYPE-PERP", "SOL 119.2", "SHORT conf=0.81", "0.79 < 0.85 → human"]
    out = []
    for i in range(45):
        s = 58 * 60 + 39 + i * 7
        out.append((f"[{22 + s // 3600:02d}:{(s // 60) % 60:02d}.{(s * 37) % 1000:03d}]", who[i % len(who)],
                    msg[(i * 4) % len(msg)]))
    return out


DESK_LOG = _desk_log()


def trading(ctx, t, cfg):
    pal = dict(PAL, accent=(1.0, 0.36, 0.75), accent2=(0.75, 0.45, 1.0))
    H.rect(ctx, 0, 0, W, HH, (0.03, 0.02, 0.05))
    F.grid(ctx, W, HH, 48, pal, 0.05)
    H.rect(ctx, 0, 0, W, 64, pal["bg"])
    H.rect(ctx, 0, 18, 8, 30, pal["accent"])
    H.text(ctx, 20, 44, cfg["system"][:3], 26, pal["white"], bold=True, pal=pal)
    H.text(ctx, 20 + H.tw(ctx, cfg["system"][:3] + " ", 26, True), 44, "Trading Desk", 26, pal["accent"], bold=True, pal=pal)
    H.text(ctx, 600, 30, "ORBITAL SIGNAL ENGINE", 13, pal["white"], bold=True, align="c", pal=pal)
    H.text(ctx, 600, 48, "OBSERVE · REASON · EXECUTE · LEARN", 10, pal["dim"], align="c", pal=pal)
    H.text(ctx, 900, 40, "● SIM", 13, pal["accent"], bold=True, pal=pal)
    s = int(14 * 3600 + 23 * 60 + 5 + t)
    H.text(ctx, W - 12, 40, f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}", 13, pal["text"], align="r", pal=pal)
    # Agenten-Leiste
    ags = [("01 WATCHER", "RUN"), ("02 ANALYST", "ACTIVE"), ("03 RISK", "CHECK"), ("04 EXECUTOR", "FILL"),
           ("05 REPORTER", "SYNC"), ("06 HUMAN", "IDLE")]
    hot = int(t * 1.5) % 6
    for i, (n, st) in enumerate(ags):
        x = i * 180
        H.rect(ctx, x + 2, 70, 176, 86, pal["panel"], 0.95)
        H.frame(ctx, x + 2, 70, 176, 86, pal["accent"] if i == hot else pal["edge"], 0.7 if i == hot else 0.15)
        H.text(ctx, x + 12, 92, n, 11, pal["white"], bold=True, pal=pal)
        H.rect(ctx, x + 132, 80, 40, 16, pal["accent"] if i == hot else pal["white"], 0.9 if i == hot else 0.1)
        H.text(ctx, x + 152, 92, st, 9, pal["white"], bold=True, align="c", pal=pal)
        H.spark(ctx, x + 12, 104, 110, 40, t, i + 20, pal["white"], pal=pal, lw=1.3)
        H.text(ctx, x + 170, 144, f"{0.9 + 0.09 * H.hsh(i, 2):.2f}", 13, pal["text"], align="r", pal=pal)
    # links: Markt, Orderbuch, Volatilität
    yy = H.panel(ctx, 0, 170, 250, 400, "MARKET", "SIM", pal)
    mk = [("BTC", 84668, 0), ("ETH", 2713, 0), ("SOL", 119.15, 2), ("HYPE", 89.14, 2), ("ARB", 0.859, 3),
          ("OP", 1.213, 3), ("LINK", 13.42, 2), ("AVAX", 21.06, 2)]
    for i, (sy, v, d) in enumerate(mk):
        y = yy + 22 + i * 44
        H.text(ctx, 12, y, sy, 13, pal["white"], bold=True, pal=pal)
        val = v * (1 + 0.002 * H.noise(t * 2, i))
        H.text(ctx, 150, y, f"{val:,.{d}f}", 12, pal["text"], align="r", pal=pal)
        H.spark(ctx, 160, y - 22, 80, 26, t, i + 40, pal["accent"], pal=pal, lw=1.2, n=24)
    yy = H.panel(ctx, 0, 580, 250, 260, "ORDER BOOK", "BTC-PERP", pal)
    mid = 125 + H.noise(t, 9) * 6
    for side, sgn in ((pal["accent"], -1), (pal["accent2"], 1)):
        ctx.move_to(mid, yy + 190)
        for i in range(30):
            x = mid + sgn * i * 4
            y = yy + 190 - (i ** 1.25) * 6 * (0.9 + 0.1 * H.noise(t * 3, i))
            ctx.line_to(x, max(yy + 10, y))
        ctx.line_to(mid + sgn * 116, yy + 190)
        ctx.close_path()
        H.col(ctx, side, 0.45)
        ctx.fill()
    H.text(ctx, 12, yy + 214, "SPREAD 3.4", 11, pal["dim"], pal=pal)
    yy = H.panel(ctx, 0, 850, 250, 300, "VOLATILITY", "100 AVG", pal)
    H.text(ctx, 12, yy + 52, f"{2.9 + 0.1 * math.sin(t):.1f}%", 44, pal["white"], bold=True, pal=pal)
    H.bars(ctx, 12, yy + 80, 226, 170, 20, t, seed=31, pal=pal, palette=(pal["accent"], pal["white"]))
    # Mitte: Wirbel
    cx, cy = 560, 640
    F.vortex(ctx, cx, cy, 340, 135, t, pal, n=2600, depth=210)
    H.text(ctx, cx, cy + 120, "SIGNAL CORE", 11, pal["white"], align="c", bold=True, pal=pal)
    for (x, y, a, b, dx, dy) in ((560, 330, "RISK HOLD", "gate", 0, 0), (270, 520, "CHOICE / SH", "conf", 0, 0),
                                 (640, 930, "GATE / HOLD", "0.7", 0, 0)):
        x += H.noise(t * 0.5, x) * 6
        H.rect(ctx, x, y, 200, 56, pal["panel"], 0.92)
        H.frame(ctx, x, y, 200, 56, pal["white"], 0.5)
        H.text(ctx, x + 12, y + 22, a, 13, pal["accent"], bold=True, pal=pal)
        H.text(ctx, x + 12, y + 44, b, 11, pal["dim"], pal=pal)
        H.bars(ctx, x + 140, y + 30, 50, 18, 6, t, seed=x, pal=pal, palette=(pal["white"],))
    H.col(ctx, pal["white"], 0.7)
    ctx.set_line_width(1)
    ctx.move_to(660, 386)
    ctx.line_to(cx, cy)
    ctx.line_to(700, 930)
    ctx.stroke()
    H.tag(ctx, 420, 830, "● conf 0.81", pal, size=11)
    H.tag(ctx, 830, 1010, "● LONG 0.34", pal, size=11)
    # rechts: Evidenz, Übergaben, Risiko
    yy = H.panel(ctx, 830, 170, 250, 300, "EVIDENCE MATRIX", "", pal)
    H.heat(ctx, 840, yy + 4, 232, 250, 7, 7, t, 5, pal)
    yy = H.panel(ctx, 830, 480, 250, 320, "HANDOFFS", "/24h", pal)
    for i, n in enumerate(["WATCHER", "ANALYST", "RISK", "EXECUTOR", "REPORTER", "HUMAN"]):
        H.text(ctx, 842, yy + 20 + i * 44, n, 11, pal["dim"], pal=pal)
        H.progress(ctx, 842, yy + 28 + i * 44, 226, 4, 0.2 + 0.75 * abs(math.sin(t * 0.5 + i * 1.3)), pal["accent"], pal)
    yy = H.panel(ctx, 830, 810, 250, 340, "RISK GAUGE", "", pal)
    H.gauge(ctx, 955, yy + 140, 90, 0.18 + 0.06 * math.sin(t), pal)
    H.text(ctx, 955, yy + 230, f"DD {0.4 + 0.05 * math.sin(t):.1f}%", 22, pal["white"], bold=True, align="c", pal=pal)
    H.text(ctx, 955, yy + 260, "limits ok · paper only", 11, pal["dim"], align="c", pal=pal)
    # Metrik-Leiste
    for i, (lb, v) in enumerate((("SIGNALS / 5", "7"), ("PRECISION", "0.95"), ("CONF", "0.96"),
                                 ("EXPOSURE", "0.38u"), ("DRAWDOWN", "0.4%"))):
        x = i * 216
        H.rect(ctx, x + 2, 1166, 212, 80, pal["panel"], 0.95)
        H.frame(ctx, x + 2, 1166, 212, 80, pal["edge"], 0.15)
        H.text(ctx, x + 12, 1186, lb, 10, pal["dim"], pal=pal)
        H.text(ctx, x + 12, 1228, v, 24, pal["accent"] if i == 4 else pal["white"], bold=True, pal=pal)
        H.spark(ctx, x + 110, 1196, 96, 36, t, i + 60, pal["white"], pal=pal, lw=1.2, n=24)
    # Code + Live-Log
    H.rect(ctx, 0, 1256, 600, 470, pal["panel"], 0.95)
    for i, nm in enumerate(["vek_desk.py", "vek_core.py", "risk_gate.py"]):
        H.text(ctx, 12 + i * 140, 1280, nm, 12, pal["accent"] if i == 2 else pal["dim"], bold=(i == 2), pal=pal)
    H.rect(ctx, 292, 1288, 100, 2, pal["accent"])
    H.code(ctx, 4, 1296, 592, 420, DESK_CODE, t, cps=36, size=13, pal=pal, start=-4, hl_line=8)
    yy = H.panel(ctx, 608, 1256, 472, 470, "LIVE LOG", "ALL · TRADES · SIGNALS · RISK", pal)
    H.log(ctx, 618, yy, 452, 420, DESK_LOG, t, rate=4.5, size=12, pal=pal, cols=[0, 0.3, 0.52])
    # KPI-Fuß
    for i, (lb, v) in enumerate((("DECISIONS", f"{int(10148 + t * 23):,}"), ("GATE PASS", "90.9%"),
                                 ("MEDIAN LATENCY", "251 ms"), ("COST / 10K", "$0.42"), ("POSITION RISK", "LOW"))):
        x = i * 216
        H.text(ctx, x + 12, 1756, lb, 10, pal["dim"], pal=pal)
        H.text(ctx, x + 12, 1800, v, 30, pal["accent"] if i == 3 else pal["white"], bold=True, pal=pal)
        H.spark(ctx, x + 12, 1812, 190, 30, t, i + 80, pal["white"], pal=pal, lw=1, a=0.5)
    H.text(ctx, W / 2, 1872, "SIMULATED · PAPER TRADING · NOT TRADING ADVICE", 13, pal["white"], bold=True, align="c", pal=pal)
    _footer(ctx, f"{cfg['system']} · orbital signal engine", "metrics illustrative", pal, y=1904)


# =====================================================================  5) END-KARTE / KERN
def core_card(ctx, t, cfg):
    pal = PAL
    H.rect(ctx, 0, 0, W, HH, (0.01, 0.01, 0.015))
    F.grid(ctx, W, HH, 48, pal, 0.05)
    srcs = [(x, -40) for x in (80, 300, 540, 780, 1000)] + [(x, HH + 40) for x in (120, 540, 960)]
    F.strands(ctx, srcs[:5], (540, 900), t, n=90, a=0.06, spread=300, seed=21, dst_spread=120, bend=0.3)
    F.strands(ctx, srcs[5:], (540, 900), t, n=90, c=pal["accent"], a=0.06, spread=300, seed=22, dst_spread=120, bend=0.3)
    F.core(ctx, 540, 900, 340, t * 1.4)
    H.text(ctx, W / 2, 1380, cfg["system"], 64, pal["white"], bold=True, align="c", pal=pal)
    H.text(ctx, W / 2, 1426, "decides · never chats", 20, pal["dim"], align="c", pal=pal)
    _footer(ctx, "", "metrics illustrative · simulated", pal)


SCENES = {"agent_ops": agent_ops, "pipeline": pipeline, "mono_field": mono_field, "trading": trading,
          "core_card": core_card}
