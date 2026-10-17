"""Build ../index.html (DaranX resume) from this folder.
Run: python3 build.py   NOTE: rebuilding overwrites edits saved from the in-page editor (copy them into body.html first)."""
import json, math, random, re
from pathlib import Path
import render as R

HERE = Path(__file__).parent
ROOT = HERE.parent
rd = lambda p: (HERE / p).read_text(encoding="utf-8")

# ---------- act 1: node network with the ten clients (three flagships are larger) ----------
# (id, label, x, y, label position, flagship)
KEYS = [("k-k", "کالا وال", 520, 250, "below", True), ("k-a", "آرتمیس", 820, 520, "below", True), ("k-t", "توریور", 330, 610, "above", True),
        ("k-r", "راگا مارکت", 210, 330, "below", False), ("k-al", "کاشی آلسن", 760, 190, "above", False), ("k-rj", "رویال جین", 960, 330, "below", False),
        ("k-g", "گاراژ ۵۱", 600, 770, "below", False), ("k-rb", "کلینیک رابین", 640, 420, "below", False), ("k-az", "کلینیک آرزو", 960, 700, "below", False),
        ("k-b", "به‌سرما", 190, 150, "below", False)]
T = KEYS[2]
KEY_LINKS = [("k-b", "k-k"), ("k-k", "k-al"), ("k-al", "k-rj"), ("k-k", "k-rb"), ("k-rb", "k-a"), ("k-rj", "k-a"), ("k-a", "k-az"),
             ("k-a", "k-g"), ("k-g", "k-t"), ("k-t", "k-r"), ("k-r", "k-b"), ("k-r", "k-k"), ("k-rb", "k-t")]
BR_ANGLES = [200, 160, 120, 90, 60, 20, -20]   # degrees, SVG y-down; the top stays clear for the label
BR_DONE = 5
BR_R = 125


def network():
    rnd = random.Random(7)
    pts = []
    # wider than the viewBox so zooming out on phones never shows an empty edge
    while len(pts) < 150:
        x, y = rnd.uniform(-420, 2020), rnd.uniform(-160, 1060)
        # keep the key nodes and the branch ring readable
        if any(math.hypot(x - kx, y - ky) < 95 for _, _, kx, ky, _, _ in KEYS):
            continue
        if math.hypot(x - T[2], y - T[3]) < BR_R + 60:
            continue
        if all(math.hypot(x - a, y - b) > 70 for a, b in pts):
            pts.append((x, y))
    lines, deg = [], [0] * len(pts)
    for i, (x1, y1) in enumerate(pts):
        near = sorted(((math.hypot(x1 - x2, y1 - y2), j) for j, (x2, y2) in enumerate(pts) if j > i))
        for d, j in near[:3]:
            if d < 165 and deg[i] < 3 and deg[j] < 3:
                deg[i] += 1; deg[j] += 1
                lines.append(f'<line class="net-l" x1="{x1:.0f}" y1="{y1:.0f}" x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}"/>')
    nodes = "".join(f'<circle class="net-n" cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice((2.5, 3, 4)):.1f}"/>' for x, y in pts)
    # faint links from each key node to its nearest background nodes, so keys sit inside the network
    for _, _, kx, ky, _, _ in KEYS:
        for d, (x, y) in sorted((math.hypot(kx - x, ky - y), (x, y)) for x, y in pts)[:3]:
            lines.append(f'<line class="net-l" x1="{kx}" y1="{ky}" x2="{x:.0f}" y2="{y:.0f}"/>')
    K = {k[0]: k for k in KEYS}
    key_l = "".join(f'<line class="key-l" x1="{K[a][2]}" y1="{K[a][3]}" x2="{K[b][2]}" y2="{K[b][3]}"/>' for a, b in KEY_LINKS)
    br = []
    for i, ang in enumerate(BR_ANGLES):
        r = math.radians(ang)
        x, y = T[2] + BR_R * math.cos(r), T[3] + BR_R * math.sin(r)
        done = i < BR_DONE
        inner = '<circle class="in" cx="%.0f" cy="%.0f" r="7"/>' % (x, y) if done else ""
        br.append(f'<g class="br {"done" if done else "wait"}"><line x1="{T[2]}" y1="{T[3]}" x2="{x:.0f}" y2="{y:.0f}"/>'
                  f'<circle cx="{x:.0f}" cy="{y:.0f}" r="16"/>{inner}</g>')
    keys = []
    for kid, name, x, y, pos, big in KEYS:
        r0, r1, r2, off = (34, 24, 11, 62) if big else (22, 15, 7, 44)
        ty = y + off if pos == "below" else y - off + 18
        keys.append(f'<g class="key{" big" if big else ""}" id="{kid}"><circle class="halo" cx="{x}" cy="{y}" r="{r0}"/><circle class="ring" cx="{x}" cy="{y}" r="{r1}"/>'
                    f'<circle class="core" cx="{x}" cy="{y}" r="{r2}"/><text x="{x}" y="{ty}" text-anchor="middle">{name}</text></g>')
    return "".join(lines) + nodes + key_l + "".join(br) + "".join(keys)


# ---------- act 2: three domains (venn) and the four-step method ----------
VENN = [("v1", "زیرساخت", 540, 400, 0, -230, 0, -92), ("v2", "امنیت", 670, 610, 320, 130, 96, 70), ("v3", "هوشمندی", 410, 610, -320, 130, -96, 70)]


def venn():
    out = ['<g id="venn" class="venn">']
    for vid, name, cx, cy, dx, dy, lx, ly in VENN:
        out.append(f'<g id="{vid}" data-dx="{dx}" data-dy="{dy}"><circle cx="{cx}" cy="{cy}" r="165"/>'
                   f'<text x="{cx + lx}" y="{cy + ly + 12}" text-anchor="middle">{name}</text></g>')
    gx = sum(v[2] for v in VENN) / 3
    gy = sum(v[3] for v in VENN) / 3
    out.append(f'<text class="mid" x="{gx:.0f}" y="{gy + 10:.0f}" text-anchor="middle">راهکار</text></g>')
    return "".join(out)


METHOD = [("شناخت", 920), ("طراحی", 680), ("اجرا", 440), ("پشتیبانی", 200)]
FA = "۰۱۲۳۴۵۶۷۸۹"


def method():
    y = 470
    x0, x1 = METHOD[0][1], METHOD[-1][1]
    out = [f'<g id="method"><line class="m-track" x1="{x0}" y1="{y}" x2="{x1}" y2="{y}"/>'
           f'<line class="m-line" id="mLine" x1="{x0}" y1="{y}" x2="{x1}" y2="{y}"/>'
           f'<circle class="m-dot" id="mDot" cx="{x1}" cy="{y}" r="9"/>']
    for i, (name, x) in enumerate(METHOD):
        out.append(f'<g class="m-node" data-i="{i}"><circle cx="{x}" cy="{y}" r="32"/>'
                   f'<text class="n" x="{x}" y="{y + 8}" text-anchor="middle">{FA[i + 1]}</text>'
                   f'<text x="{x}" y="{y + 86}" text-anchor="middle">{name}</text></g>')
    out.append('</g>')
    return "".join(out)


def icon(name):
    svg = rd(f"icons/{name}.svg")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return f'<svg class="ic" viewBox="0 0 256 256" aria-hidden="true">{inner}</svg>'


import base64, mimetypes


def data_uri(rel):
    p = ROOT / rel
    mime = {".webp": "image/webp", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}[p.suffix.lower()]
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def assemble(draft):
    body = rd("body.html").replace("{{NETWORK}}", network()).replace("{{VENN}}", venn()).replace("{{METHOD}}", method())
    body = body.replace("{{PROJECTS}}", R.projects(draft)).replace("{{VLAN}}", R.vlan_svg())
    body = re.sub(r"\{\{ICON:([a-z-]+)\}\}", lambda m: icon(m.group(1)), body)
    assert "{{" not in body, re.findall(r"\{\{[^}]*\}\}", body)
    if not draft:
        # the client copy carries no editing tools
        body = re.sub(r'<div class="editbar".*?</div>\s*', "", body, flags=re.S)
        body = body.replace('<span id="needCount" class="need-count"></span>', "")
    return body


title = "رزومهٔ داران‌ایکس | شبکه، دوربین و سرور برای کسب‌وکارها"
desc = "رزومهٔ داران‌ایکس: ده کارفرما از فروشگاه‌های زنجیره‌ای تا کلینیک‌ها و کارخانه‌ها، با نقشه‌های واقعی پروژه‌ها؛ کالا وال، توریور، آرتمیس و دیگران."
SITE = "https://www.daranx.com/"
ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "Organization", "@id": SITE + "#org", "name": "DaranX", "alternateName": "داران‌ایکس", "url": SITE,
     "slogan": "همه چیز سرِ جای درستش", "telephone": "+982188964116",
     "address": {"@type": "PostalAddress", "addressLocality": "تهران", "streetAddress": "میدان فاطمی، نبش چهلستون، ساختمان چهلستون، طبقه ۲، واحد ۲۰۲", "addressCountry": "IR"},
     "knowsAbout": ["زیرساخت", "امنیت", "هوشمندی"]},
    {"@type": "WebPage", "name": title, "description": desc, "inLanguage": "fa-IR", "about": {"@id": SITE + "#org"}},
]}
FAV = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23153A62'/%3E"
       "%3Cpath d='M9 9l14 14M23 9L9 23' stroke='%237FB0DF' stroke-width='3.4' stroke-linecap='round'/%3E%3C/svg%3E")
# fonts load from file:// only when embedded (Chrome blocks file-origin font fetches)
FONT_URI = "url(data:font/woff2;base64," + base64.b64encode((ROOT / "assets" / "Vazirmatn-VF.woff2").read_bytes()).decode() + ")"


def page(draft):
    body = assemble(draft)
    edit_flag = ("if(location.protocol==='file:'||/[?&]edit|#edit/.test(location.search+location.hash))"
                 "document.documentElement.classList.add('can-edit');") if draft else ""
    head = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex,nofollow">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:locale" content="fa_IR">
<meta name="theme-color" content="#07152A"><meta name="color-scheme" content="light dark">
<link rel="icon" href="{FAV}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>
{rd("engine/base.css")}
{rd("site.css").replace('url("assets/Vazirmatn-VF.woff2")', FONT_URI)}
</style>
<script>document.documentElement.classList.add('js');{edit_flag}</script>
</head>
"""
    files = (["engine/editor.js"] if draft else []) + ["vendor/gsap.min.js", "vendor/ScrollTrigger.min.js", "engine/story-engine.js", "scenes.js", "engine/ui.js", "site.js"]
    js = "".join(f"<script>\n{rd(p)}\n</script>\n" for p in files)
    out = head + "<body>\n" + body + "\n" + js + "</body>\n</html>\n"
    if not draft:
        # one self-contained file: every image travels inside the HTML, so it opens from any messenger or phone
        out = re.sub(r'(src|href)="(assets/[^"]+\.(?:webp|svg|jpe?g|png))"', lambda m: f'{m.group(1)}="{data_uri(m.group(2))}"', out)
        assert 'src="assets/' not in out
    return out


client, draft = page(False), page(True)
(ROOT / "index.html").write_text(client, encoding="utf-8")
(ROOT / "draft.html").write_text(draft, encoding="utf-8")
print(f"client index.html {len(client) // 1024} KB (self-contained), draft.html {len(draft) // 1024} KB")
