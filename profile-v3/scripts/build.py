"""Builds everything on the profile.

  python scripts/build.py                  -> README + all images for the current hour in Pune
  python scripts/build.py --slot night     -> force a time of day (testing)
  python scripts/build.py --sample-stats   -> fill the activity card with sample numbers (testing)

Standard library only, so the GitHub Action needs nothing installed. The activity card needs
GITHUB_TOKEN (the Action provides it); without it the existing card is kept.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "scripts")
USER = os.environ.get("PROFILE_USER", "TejasThange3")
W = 880

FONTS = json.load(open(os.path.join(HERE, "fonts.json")))
GIFS = json.load(open(os.path.join(HERE, "gifs.json")))
ICONS = json.load(open(os.path.join(HERE, "icons.json")))

MONO = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
DISPLAY = "'Sora', 'Segoe UI', Helvetica, Arial, sans-serif"
SCRIPT = "'Great Vibes', 'Segoe Script', cursive"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(bg="#0e1018", panel="#151927", stroke="#272c41", text="#e7e9f3", muted="#8b91aa",
                 faint="#5b6078", accent="#c4a6ff", accent2="#8fd3a8", key="#9db4ff",
                 tile1="#1c2133", tile2="#131726", slab="#090b12", hi="#ffffff", glyph="#e7e9f3",
                 bar="#c4a6ff", bar0="#2a2f45", live="#7ee2a0"),
    "light": dict(bg="#faf9fd", panel="#f1eff8", stroke="#dedbea", text="#1d1b2c", muted="#6b6882",
                  faint="#a3a0b8", accent="#6a46d1", accent2="#2f8a5a", key="#3d5bb8",
                  tile1="#ffffff", tile2="#f1eff8", slab="#d9d5e8", hi="#ffffff", glyph="#1d1b2c",
                  bar="#6a46d1", bar0="#e3e0ee", live="#1f9d55"),
}
SLOT_LABEL = {"morning": "MORNING", "afternoon": "AFTERNOON", "evening": "EVENING", "night": "NIGHT"}


# ---------------------------------------------------------------- helpers
def font_css(*families):
    faces = []
    for fam in families:
        for w, b64 in FONTS[fam].items():
            faces.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
                         f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "<style><![CDATA[" + "".join(faces) + "]]></style>"


def write(name, text):
    path = os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def frame(t, h, title, desc, body, fonts=()):
    css = font_css(*fonts) if fonts else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" '
            f'aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>{css}'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["stroke"]}"/>'
            f'{body}</svg>')


def reveal(i, step=0.06):
    """Fade + rise on load. Elements stay visible in viewers that ignore SMIL."""
    d = i * step
    total = d + 0.5
    k = d / total if total else 0
    return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{k:.3f};1" dur="{total:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 6;0 6;0 0" '
            f'keyTimes="0;{k:.3f};1" dur="{total:.2f}s" fill="freeze"/>')


def lum(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def pune_now():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        return dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)


def slot_for_hour(h):
    if 5 <= h < 11:
        return "morning"
    if 11 <= h < 16:
        return "afternoon"
    if 16 <= h < 19:
        return "evening"
    return "night"


def pick_gif(now, slot):
    """Rotates through the slot's GIFs, a new one each hour."""
    options = GIFS[slot]
    idx = (now.timetuple().tm_yday * 24 + now.hour) % len(options)
    return options[idx]


# ---------------------------------------------------------------- name strip under the GIF
def plate(theme, slot, gif):
    t = THEMES[theme]
    h = 104
    credit = f'{SLOT_LABEL[slot]} · {gif["art"].upper()}' + (f' · ART BY {gif["by"].upper()}' if gif["by"] else "")
    b = [f'<text x="40" y="70" font-family="{SCRIPT}" font-size="50" fill="{t["text"]}">Tejas Thange</text>',
         f'<text x="{W - 40}" y="48" text-anchor="end" font-family="{MONO}" font-size="13" letter-spacing="3" '
         f'fill="{t["text"]}">18.52°N 73.86°E · PUNE</text>',
         f'<text x="{W - 40}" y="72" text-anchor="end" font-family="{MONO}" font-size="10.5" letter-spacing="2" '
         f'fill="{t["muted"]}">{escape(credit)}</text>']
    return frame(t, h, "Tejas Thange · Pune",
                 f"Signed Tejas Thange. 18.52 degrees north, 73.86 degrees east, Pune. {gif['art']}.",
                 "".join(b), fonts=("Great Vibes", "JetBrains Mono"))


# ---------------------------------------------------------------- terminal card
CARD = [
    ("name", "Tejas Thange"),
    ("role", "AI/ML Engineer"),
    ("now", "AI Programming Intern @ Mimic Productions"),
    ("", "porting RAG ingestion to Python · building a web-scraping service for RAG"),
    ("focus", "LLM apps · RAG · computer vision · speech AI"),
    ("edu", "B.Tech AI & ML · Symbiosis Institute of Technology · 2026"),
    ("base", "Pune, India · open to AI Engineer, Applied AI and GenAI roles"),
]


def card(theme):
    t = THEMES[theme]
    h = 300
    b = [f'<rect x="1" y="1" width="{W - 2}" height="38" rx="13" fill="{t["panel"]}"/>',
         f'<rect x="1" y="26" width="{W - 2}" height="14" fill="{t["panel"]}"/>',
         f'<line x1="1" y1="39.5" x2="{W - 1}" y2="39.5" stroke="{t["stroke"]}"/>']
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        b.append(f'<circle cx="{24 + i * 20}" cy="20" r="6" fill="{c}"/>')
    b.append(f'<text x="{W / 2}" y="25" text-anchor="middle" font-family="{MONO}" font-size="13" '
             f'fill="{t["muted"]}">tejas@pune: ~</text>')
    y = 76
    b.append(f'<g>{reveal(0)}<text x="32" y="{y}" font-family="{MONO}" font-size="15" xml:space="preserve">'
             f'<tspan fill="{t["accent2"]}">tejas@pune</tspan><tspan fill="{t["muted"]}">:~$ </tspan>'
             f'<tspan fill="{t["text"]}">whoami</tspan></text></g>')
    y += 34
    for i, (k, v) in enumerate(CARD, start=1):
        vcol = t["accent"] if k == "name" else t["text"]
        weight = ' font-weight="700"' if k == "name" else ""
        b.append(f'<g>{reveal(i)}<text x="32" y="{y}" font-family="{MONO}" font-size="15" xml:space="preserve">'
                 f'<tspan fill="{t["key"]}">{escape(k.ljust(7))}</tspan>'
                 f'<tspan fill="{vcol}"{weight}>{escape(v)}</tspan></text></g>')
        y += 24
    y += 10
    b.append(f'<g>{reveal(len(CARD) + 1)}<text x="32" y="{y}" font-family="{MONO}" font-size="15" xml:space="preserve">'
             f'<tspan fill="{t["accent2"]}">tejas@pune</tspan><tspan fill="{t["muted"]}">:~$ </tspan></text>'
             f'<rect x="153" y="{y - 13}" width="9" height="17" fill="{t["text"]}">'
             f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></rect></g>')
    return frame(t, h, "whoami: Tejas Thange",
                 "Terminal card. Tejas Thange, AI/ML Engineer, AI Programming Intern at Mimic Productions, "
                 "focused on LLM apps, RAG, computer vision and speech AI. Pune, India.", "".join(b),
                 fonts=("JetBrains Mono",))


# ---------------------------------------------------------------- tech icons
TECH = [
    ("AI & ML", [("python", "Python"), ("pytorch", "PyTorch"), ("scikitlearn", "Scikit-Learn"),
                 ("opencv", "OpenCV"), ("langgraph", "LangGraph"), ("onnx", "ONNX Runtime")]),
    ("Backend & Data", [("fastapi", "FastAPI"), ("streamlit", "Streamlit"), ("mysql", "MySQL"),
                        ("mongodb", "MongoDB"), ("pandas", "Pandas"), ("numpy", "NumPy")]),
    ("Web & Platforms", [("nextdotjs", "Next.js"), ("vercel", "Vercel"), ("wordpress", "WordPress"),
                         ("text:AWS", "AWS"), ("raspberrypi", "Raspberry Pi"), ("git", "Git"),
                         ("github", "GitHub"), ("githubactions", "Actions")]),
    ("AI Tools", [("claude", "Claude Code"), ("text:>_", "Codex"), ("cursor", "Cursor"), ("text:WF", "Wispr Flow")]),
]


def tech(theme):
    t = THEMES[theme]
    tile, gap, x0 = 64, 100, 44
    b = [f'<defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["tile1"]}"/>'
         f'<stop offset="1" stop-color="{t["tile2"]}"/></linearGradient>'
         f'<linearGradient id="gl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["hi"]}" '
         f'stop-opacity="{0.10 if theme == "dark" else 0.9}"/><stop offset="0.5" stop-color="{t["hi"]}" stop-opacity="0"/>'
         f'</linearGradient><filter id="sh" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="6" '
         f'stdDeviation="5" flood-color="#000" flood-opacity="{0.45 if theme == "dark" else 0.14}"/></filter></defs>']
    y, n = 34, 0
    for group, items in TECH:
        b.append(f'<text x="{x0 - 8}" y="{y}" font-family="{MONO}" font-size="12" letter-spacing="2" '
                 f'fill="{t["muted"]}">{escape(group.upper())}</text>')
        b.append(f'<line x1="{x0 - 8 + len(group) * 9.4 + 12}" y1="{y - 4}" x2="{W - 36}" y2="{y - 4}" stroke="{t["stroke"]}"/>')
        y += 18
        for i, (slug, label) in enumerate(items):
            x = x0 + i * gap
            g = [f'<rect x="{x}" y="{y + 5}" width="{tile}" height="{tile}" rx="16" fill="{t["slab"]}"/>',
                 f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="16" fill="url(#tg)" stroke="{t["stroke"]}" filter="url(#sh)"/>',
                 f'<rect x="{x + 1}" y="{y + 1}" width="{tile - 2}" height="{tile - 2}" rx="15" fill="url(#gl)"/>']
            if slug.startswith("text:"):
                word = slug[5:]
                g.append(f'<text x="{x + tile / 2}" y="{y + tile / 2 + 7}" text-anchor="middle" font-family="{MONO}" '
                         f'font-size="{20 if len(word) <= 2 else 17}" font-weight="700" fill="{t["glyph"]}">{escape(word)}</text>')
            else:
                ic = ICONS[slug]
                col = "#" + ic["hex"]
                l = lum(ic["hex"])
                if (theme == "dark" and l < 0.06) or (theme == "light" and l > 0.8):
                    col = t["glyph"]
                elif theme == "dark" and l < 0.3:
                    col = mix(col, "#ffffff", 0.45 - l)
                g.append(f'<path transform="translate({x + 16} {y + 16}) scale({32 / 24:.4f})" fill="{col}" d="{ic["path"]}"/>')
            g.append(f'<text x="{x + tile / 2}" y="{y + tile + 26}" text-anchor="middle" font-family="{SANS}" '
                     f'font-size="12" fill="{t["text"]}">{escape(label)}</text>')
            b.append(f'<g>{reveal(n, 0.035)}{"".join(g)}</g>')
            n += 1
        y += tile + 58
    return frame(t, y - 18, "Tech stack", "Tools and technologies: " +
                 ", ".join(lbl for _, items in TECH for _, lbl in items), "".join(b), fonts=("JetBrains Mono",))


# ---------------------------------------------------------------- live activity card
QUERY = """query($login:String!){user(login:$login){followers{totalCount}
repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100,isFork:false){totalCount
nodes{name stargazerCount primaryLanguage{name color}}}
pushed:repositories(ownerAffiliations:OWNER,first:1,orderBy:{field:PUSHED_AT,direction:DESC}){nodes{name pushedAt}}
created:repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:1,orderBy:{field:CREATED_AT,direction:DESC}){nodes{name createdAt}}
contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}"""


def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": USER})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    u = data["data"]["user"]
    days = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    langs = {}
    for n in u["repositories"]["nodes"]:
        if n["primaryLanguage"]:
            k = n["primaryLanguage"]["name"]
            langs.setdefault(k, [0, n["primaryLanguage"]["color"] or "#888888"])[0] += 1
    pushed = (u["pushed"]["nodes"] or [{}])[0]
    created = (u["created"]["nodes"] or [{}])[0]
    return dict(total=u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
                repos=u["repositories"]["totalCount"],
                stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
                followers=u["followers"]["totalCount"], days=days,
                last_push=(pushed.get("name"), pushed.get("pushedAt")),
                newest=(created.get("name"), created.get("createdAt")),
                langs=sorted(langs.items(), key=lambda kv: -kv[1][0]))


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1
    while i >= 0 and counts[i]:
        cur += 1
        i -= 1
    return cur, longest


def ist(iso):
    if not iso:
        return ""
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) + dt.timedelta(hours=5, minutes=30)
    return f"{t.day} {t.strftime('%b')} · {t.strftime('%H:%M')} IST"


def live(theme, s, now):
    t = THEMES[theme]
    h = 400
    colw = (W - 72) / 4
    b = []
    # header
    b.append(f'<circle cx="44" cy="38" r="5" fill="{t["live"]}"/>'
             f'<circle cx="44" cy="38" r="5" fill="none" stroke="{t["live"]}" stroke-width="1.5">'
             f'<animate attributeName="r" values="5;12" dur="1.8s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0.8;0" dur="1.8s" repeatCount="indefinite"/></circle>')
    b.append(f'<text x="60" y="43" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{t["text"]}">LIVE</text>')
    stamp = f"REFRESHED {now.day} {now.strftime('%b').upper()} · {now.strftime('%H:%M')} IST"
    b.append(f'<text x="{W - 36}" y="43" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="2" '
             f'fill="{t["muted"]}">{stamp}</text>')
    b.append(f'<line x1="36" y1="64.5" x2="{W - 36}" y2="64.5" stroke="{t["stroke"]}"/>')

    def tile(i, row, label, value, sub="", extra=""):
        x = 36 + (i % 4) * colw
        y0 = 104 if row == 0 else 214
        size = min(34, (colw - 12) / max(1, len(value) * 0.66))
        return (f'<g>{reveal(i + row * 4)}'
                f'<text x="{x}" y="{y0}" font-family="{MONO}" font-size="11.5" letter-spacing="3" fill="{t["muted"]}">{escape(label)}</text>'
                f'<text x="{x}" y="{y0 + 42}" font-family="{DISPLAY}" font-weight="700" font-size="{size:.1f}" '
                f'fill="{t["accent"]}">{escape(value)}</text>'
                f'{extra}<text x="{x}" y="{y0 + 66}" font-family="{MONO}" font-size="12" fill="{t["muted"]}">{escape(sub)}</text></g>')

    if s:
        cur, longest = streaks(s["days"])
        week = s["days"][-7:]
        wk = sum(d["contributionCount"] for d in week)
        peak = max([d["contributionCount"] for d in week] + [1])
        bars = []
        for j, d in enumerate(week):
            bh = max(2, 16 * d["contributionCount"] / peak)
            bars.append(f'<rect x="{36 + j * 24}" y="{104 + 66 - bh:.1f}" width="20" height="{bh:.1f}" rx="2" '
                        f'fill="{t["bar"] if d["contributionCount"] else t["bar0"]}"/>')
        month = sum(d["contributionCount"] for d in s["days"][-30:])
        lp_name, lp_at = s["last_push"]
        nr_name, nr_at = s["newest"]
        short = lambda n: (n[:13] + "…") if n and len(n) > 14 else (n or "—")
        tiles = [
            tile(0, 0, "ACTIVITY · 7D", str(wk), "", "".join(bars)),
            tile(1, 0, "CURRENT STREAK", f"{cur}d", f"{s['total']:,} in the last year"),
            tile(2, 0, "STARS EARNED", f"★ {s['stars']}", "own repos, no forks"),
            tile(3, 0, "FOLLOWERS", str(s["followers"]), f"{s['repos']} public repos"),
            tile(0, 1, "LONGEST STREAK", f"{longest}d", "last 12 months"),
            tile(1, 1, "LAST PUSH", short(lp_name), ist(lp_at)),
            tile(2, 1, "NEWEST REPO", short(nr_name), ist(nr_at).split(" · ")[0] if nr_at else ""),
            tile(3, 1, "LAST 30 DAYS", str(month), "contributions"),
        ]
        b.extend(tiles)
        # languages
        b.append(f'<line x1="36" y1="300.5" x2="{W - 36}" y2="300.5" stroke="{t["stroke"]}"/>')
        b.append(f'<text x="36" y="330" font-family="{MONO}" font-size="11.5" letter-spacing="3" '
                 f'fill="{t["muted"]}">LANGUAGES · BY REPO</text>')
        langs = s["langs"][:5]
        other = sum(v[0] for _, v in s["langs"][5:])
        if other:
            langs = langs + [("Other", [other, t["faint"]])]
        total = sum(v[0] for _, v in langs) or 1
        x, bw = 36.0, W - 72
        b.append(f'<clipPath id="lb"><rect x="36" y="344" width="{bw}" height="12" rx="4"/></clipPath><g clip-path="url(#lb)">')
        for name, (n, color) in langs:
            w = bw * n / total
            b.append(f'<rect x="{x:.1f}" y="344" width="{max(w - 2, 1):.1f}" height="12" fill="{color}"/>')
            x += w
        b.append("</g>")
        lx = 36.0
        for name, (n, color) in langs:
            label = f"{name} {round(100 * n / total)}%"
            b.append(f'<circle cx="{lx + 5}" cy="377" r="5" fill="{color}"/><text x="{lx + 16}" y="381" '
                     f'font-family="{MONO}" font-size="12" fill="{t["text"]}">{escape(label)}</text>')
            lx += 34 + len(label) * 7.3
        desc = (f"{wk} contributions in the last 7 days, {cur}-day streak, {s['total']} in the last year, "
                f"{s['stars']} stars, {s['followers']} followers.")
    else:
        b.append(f'<text x="{W / 2}" y="220" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="2" '
                 f'fill="{t["muted"]}">ACTIVITY APPEARS AFTER THE FIRST REFRESH RUN</text>')
        desc = "Activity appears after the first refresh run."
    return frame(t, h, "Live GitHub activity", desc, "".join(b), fonts=("Sora", "JetBrains Mono"))


def sample_stats():
    import random
    rng = random.Random(3)
    start = dt.date.today() - dt.timedelta(days=370)
    days = [dict(date=(start + dt.timedelta(days=i)).isoformat(),
                 contributionCount=max(0, int(rng.gauss(2, 3)))) for i in range(371)]
    return dict(total=sum(d["contributionCount"] for d in days), repos=28, stars=6, followers=12, days=days,
                last_push=("docqa", "2026-10-02T04:12:00Z"), newest=("email-support-reply-rag", "2026-09-20T10:00:00Z"),
                langs=[("Python", [14, "#3572A5"]), ("Jupyter Notebook", [6, "#DA5B0B"]),
                       ("TypeScript", [4, "#3178c6"]), ("JavaScript", [2, "#f1e05a"]), ("HTML", [2, "#e34c26"])])


# ---------------------------------------------------------------- README
def readme(slot, gif):
    tpl = open(os.path.join(HERE, "README.template.md"), encoding="utf-8").read()
    wide = gif["w"] / gif["h"] >= 1.5
    size = 'width="100%"' if wide else 'height="440"'
    credit = (f'art: <a href="https://giphy.com/gifs/{gif["id"]}">{escape(gif["by"])}</a> via GIPHY'
              if gif["by"] else f'art: <a href="https://giphy.com/gifs/{gif["id"]}">via GIPHY</a>')
    return (tpl.replace("{{GIF_URL}}", f'https://i.giphy.com/media/{gif["id"]}/giphy.gif')
               .replace("{{GIF_SIZE}}", size)
               .replace("{{GIF_ALT}}", escape(f'{gif["art"]}, a pixel-art animation shown for {slot} in Pune'))
               .replace("{{CREDIT}}", credit))


def main():
    now = pune_now()
    slot = sys.argv[sys.argv.index("--slot") + 1] if "--slot" in sys.argv else slot_for_hour(now.hour)
    gif = pick_gif(now, slot)
    write("README.md", readme(slot, gif))
    for th in THEMES:
        write(f"assets/plate-{th}.svg", plate(th, slot, gif))
        write(f"assets/card-{th}.svg", card(th))
        write(f"assets/tech-{th}.svg", tech(th))
    print("slot:", slot, "gif:", gif["id"], gif["art"])

    s = None
    if "--sample-stats" in sys.argv:
        s = sample_stats()
    else:
        try:
            s = fetch_stats()
        except Exception as e:  # stats never block the rest of the refresh
            print("stats skipped:", e)
    if s or not os.path.exists(os.path.join(ROOT, "assets", "live-dark.svg")):
        for th in THEMES:
            write(f"assets/live-{th}.svg", live(th, s, now))
        print("live card:", "updated" if s else "placeholder")


if __name__ == "__main__":
    main()
