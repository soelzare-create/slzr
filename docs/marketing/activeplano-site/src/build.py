"""Build ../index.html from this folder. NOTE: rebuilding overwrites edits made with the in-page editor
(copy those into body.html first)."""
import json, re, shutil
from pathlib import Path
import scenes as S

HERE = Path(__file__).parent
NM = Path("/tmp/claude-0/-home-user-slzr/2b9c05d0-2aae-55f2-9079-74916987c93e/scratchpad/deps/node_modules/@phosphor-icons/core/assets/regular")
ph = HERE / "vendor" / "phosphor"
ph.mkdir(exist_ok=True)
for n in S.ICONS:
    if not (ph / f"{n}.svg").exists():
        shutil.copy(NM / f"{n}.svg", ph / f"{n}.svg")

aL, dL = S.aisle_svg(1600, 900, 900, 430, 3, "L")
aP, dP = S.aisle_svg(900, 1500, 560, 700, 3, "P")
shelf_main, qr = S.shelf_svg("")
shelf_how, _ = S.shelf_svg("H", dims=False, state=False)
net, row_x, ring = S.network_svg()

body = (HERE / "body.html").read_text()
rep = {
    "SPRITE": S.sprite(), "PLAN_MAIN": S.plan_svg(""), "AISLE_L": aL, "AISLE_P": aP, "SHELF_MAIN": shelf_main,
    "PLAN_PROBLEM": S.plan_problem(), "SHELF_HOW": shelf_how, "MINI_OK": S.mini_shelf(False), "MINI_GAP": S.mini_shelf(True),
    "CHART": S.chart_svg(), "PLAN_OPEN": S.plan_open(), "NETWORK": net,
    "ICON_PM": '<svg class="ic i-plus" aria-hidden="true"><use href="#i-plus"/></svg><svg class="ic i-minus" aria-hidden="true"><use href="#i-minus"/></svg>',
}
for k, v in rep.items():
    body = body.replace("{{%s}}" % k, v)
body = re.sub(r"\{\{ICON:([a-z-]+)\}\}", r'<svg class="ic" aria-hidden="true"><use href="#i-\1"/></svg>', body)
body = re.sub(r"\{\{ICON_GLYPH:([a-z-]+)\}\}", r'<svg class="glyph" aria-hidden="true"><use href="#i-\1"/></svg>', body)
assert "{{" not in body, re.findall(r"\{\{[^}]*\}\}", body)

cfg = dict(plan=dict(w=1400, h=860), zone=dict(w=340, h=440, cx=1070, cy=500), aisle=dict(w=110, h=360, cx=1061, cy=515),
           aisleL=dL, aisleP=dP, qr=qr, rowX=row_x, ring=ring)
rd = lambda p: (HERE / p).read_text()
import html as H
SITE = "https://www.activeplano.com/"
title = "ActivePlano | نرم‌افزار پلانوگرام و چیدمان فروشگاه"
desc = "ActivePlano نرم‌افزار پلانوگرام فروشگاهی است: طراحی چیدمان، برگهٔ اجرای هر قفسه با QR، کنترل چیدمان واقعی و تحلیل فروش. محصول به‌سرما و داران ایکس."
plain = lambda t: re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t))).strip()

# FAQPage schema only from answers that are final (no open [NEED] marker), so it always matches visible text
faq = []
for m in re.finditer(r"<details><summary>(.*?)</summary><p class=\"ans\">(.*?)</p></details>", body, re.S):
    q, a = plain(re.sub(r"<svg.*?</svg>", "", m.group(1), flags=re.S)), plain(m.group(2))
    if "NEED" not in a and "NEED" not in q:
        faq.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
open_needs = len(re.findall(r"NEED", re.sub(r"<script.*?</script>|<svg.*?</svg>", "", body, flags=re.S)))
robots = "index,follow,max-image-preview:large,max-snippet:-1" if open_needs == 0 else "noindex,nofollow"
if open_needs:
    print(f"WARNING: {open_needs} open [NEED] markers: page is built with noindex until they are resolved")

org = {"@type": "Organization", "@id": SITE + "#org", "name": "ActivePlano", "url": SITE, "logo": SITE + "assets/og.png",
       "parentOrganization": {"@type": "Organization", "name": "داران ایکس", "alternateName": "DaranX"}}
graph = [
    org,
    {"@type": "WebSite", "@id": SITE + "#site", "url": SITE, "name": "ActivePlano", "inLanguage": "fa-IR", "publisher": {"@id": SITE + "#org"}},
    {"@type": "SoftwareApplication", "@id": SITE + "#app", "name": "ActivePlano", "alternateName": ["اکتیو پلانو", "Active Plano"],
     "applicationCategory": "BusinessApplication", "applicationSubCategory": "Planogram software", "operatingSystem": "Web",
     "inLanguage": "fa-IR", "description": desc, "url": SITE, "image": SITE + "assets/og.png",
     "audience": {"@type": "BusinessAudience", "audienceType": "فروشگاه‌های خرده‌فروشی، زنجیره‌های فروشگاهی و فرانچایزرها"},
     "featureList": ["طراحی چیدمان فروشگاه و زون‌بندی", "برگهٔ اجرای هر قفسه با QR", "مقایسهٔ چیدمان واقعی با طرح", "تحلیل فروش ماهانه و اصلاح چیدمان", "برآورد شارژ اول شعبهٔ جدید"],
     "publisher": {"@id": SITE + "#org"}},
    {"@type": "WebPage", "@id": SITE + "#page", "url": SITE, "name": title, "description": desc, "inLanguage": "fa-IR",
     "isPartOf": {"@id": SITE + "#site"}, "about": {"@id": SITE + "#app"}, "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + "assets/og.png", "width": 1200, "height": 630}},
]
if faq:
    graph.append({"@type": "FAQPage", "@id": SITE + "#faq", "mainEntity": faq, "inLanguage": "fa-IR"})
ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
FAV = "data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230B332A'/%3E%3Cpath d='M16 7l8 18h-4l-1.6-4h-4.8L12 25H8z' fill='%235DEBAF'/%3E%3C/svg%3E"
head = f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{SITE}">
<link rel="alternate" hreflang="fa" href="{SITE}"><link rel="alternate" hreflang="x-default" href="{SITE}">
<meta property="og:type" content="website"><meta property="og:site_name" content="ActivePlano"><meta property="og:locale" content="fa_IR">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="نقشهٔ فروشگاه و قفسهٔ ActivePlano">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{SITE}assets/og.png">
<meta name="theme-color" content="#0B332A"><meta name="color-scheme" content="light dark">
<link rel="icon" href="{FAV}">
<link rel="preload" href="assets/Vazirmatn-VF.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">{ld}</script>
<style>
{rd("styles.css")}
</style>
<script>document.documentElement.classList.add('js');if(location.protocol==='file:'||/[?&]edit|#edit/.test(location.search+location.hash))document.documentElement.classList.add('can-edit');</script>
</head>
'''
out = (head + "<body>\n" + body + f'\n<script type="application/json" id="story-cfg">{json.dumps(cfg)}</script>\n'
       + "<script>\n" + rd("editor.js") + "\n</script>\n<script>\n" + rd("vendor/gsap.min.js") + "\n</script>\n<script>\n"
       + rd("vendor/ScrollTrigger.min.js") + "\n</script>\n<script>\n" + rd("story.js") + "\n</script>\n<script>\n" + rd("ui.js") + "\n</script>\n</body>\n</html>\n")
(HERE.parent / "index.html").write_text(out)
ROOT = HERE.parent
(ROOT / "robots.txt").write_text("""User-agent: *
Allow: /

# AI and answer-engine crawlers are welcome to read the public page
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: https://www.activeplano.com/sitemap.xml
""")
import datetime
(ROOT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url><loc>{SITE}</loc><lastmod>{datetime.date.today().isoformat()}</lastmod><xhtml:link rel="alternate" hreflang="fa" href="{SITE}"/></url>
</urlset>
""")
(ROOT / "llms.txt").write_text(f"""# ActivePlano

> ActivePlano (اکتیو پلانو) is planogram and store-layout software from Behsarma and DaranX, the first planogram software for retail stores in Iran. It covers layout design, per-shelf execution sheets with QR codes, comparison of the real shelf with the planned layout, and monthly sales analysis. Built for retail stores, chains and franchisors. Language: Persian.

## Pages
- [Home]({SITE}): what ActivePlano is, how it works, cooperation models, FAQ and demo request form.

## Key facts
- Category: planogram software, store layout management, retail execution control.
- Audience: store managers and sales staff, retail chains, franchisors with a central warehouse.
- Four cooperation models: panel without dataset, panel with dataset, layout deployment and planogram delivery, franchisor model.
- Website: {SITE}
""")
print("built", len(out))
