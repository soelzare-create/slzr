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
title = "ActivePlano | نرم‌افزار پلانوگرام و چیدمان فروشگاه"
desc = "ActivePlano چیدمان فروشگاه را از نقشهٔ کلی تا تک‌تک قفسه‌ها مستند و قابل‌اندازه‌گیری می‌کند. محصول به‌سرما و داران ایکس."
ld = json.dumps({"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "ActivePlano", "applicationCategory": "BusinessApplication",
                 "operatingSystem": "Web", "description": desc, "url": "https://www.activeplano.com/"}, ensure_ascii=False)
head = f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="website">
<link rel="canonical" href="https://www.activeplano.com/">
<meta name="theme-color" content="#0B332A">
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
print("built", len(out))
