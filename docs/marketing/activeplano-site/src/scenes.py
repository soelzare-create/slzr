"""SVG scene generators for the ActivePlano landing page.

Everything the scroll story draws (store plan, aisle, shelf, franchise network)
is generated here so the page stays a single self-contained HTML file.
Icons come from Phosphor (MIT) through one <symbol> sprite; nothing is hand-drawn.
"""
import math
import random
import re
from pathlib import Path

PHOSPHOR = Path(__file__).parent / "vendor" / "phosphor"  # filled by build.py (copied from node_modules)

ICONS = [
    "carrot", "wine", "shopping-bag", "sparkle", "spray-bottle", "cash-register", "storefront", "warehouse",
    "qr-code", "chart-line-up", "trend-down", "users-three", "user-minus", "footprints", "clipboard-text",
    "question", "warning-circle", "check-circle", "seal-check", "files", "scan", "arrows-left-right", "ruler",
    "arrow-left", "plus", "minus", "list-checks", "stack", "chart-bar", "package", "user-switch",
]

# --- palette (one accent: mint; amber is a semantic alert colour only) -----------------------------
PRODUCT = ["#5DEBAF", "#9FF2CD", "#CDF2EB", "#E8F5F0", "#2FBF8A", "#017852", "#B9D9CC", "#7FA698"]
ALERT = "#F0C36B"
NIGHT = "#06201A"


def sprite(icons=ICONS, src=None):
    src = Path(src) if src else PHOSPHOR
    out = ['<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>']
    for n in icons:
        f = src / f"{n}.svg"
        inner = re.search(r"<svg[^>]*>(.*)</svg>", f.read_text(), re.S).group(1)
        out.append(f'<symbol id="i-{n}" viewBox="0 0 256 256">{inner}</symbol>')
    out.append("</defs></svg>")
    return "".join(out)


def ic(name, x, y, size, cls=""):
    """Icon inside an SVG scene (position + size in scene units)."""
    return f'<use href="#i-{name}" x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" class="{cls}"/>'


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ======================================================================= STORE PLAN (top view)
ZONES = [
    dict(i=1, name="لبنیات و تازه‌ها", x=140, y=120, w=1320, h=140, k="zA", icon="carrot"),
    dict(i=2, name="نوشیدنی", x=140, y=280, w=280, h=440, k="zB", icon="wine"),
    dict(i=3, name="خواربار", x=440, y=280, w=440, h=440, k="zC", icon="shopping-bag"),
    dict(i=4, name="آرایشی و بهداشتی", x=900, y=280, w=340, h=440, k="zT", icon="sparkle"),
    dict(i=5, name="شوینده", x=1260, y=280, w=200, h=440, k="zD", icon="spray-bottle"),
    dict(i=6, name="صندوق و تنقلات", x=940, y=760, w=520, h=120, k="zE", icon="cash-register"),
]
GOND = [930, 1010, 1090, 1170]  # zone 4 gondola x positions


def plan_svg(sfx="", extra=""):
    """Top-down plan. Returns the inner markup of an <svg> (camera group #cam{sfx})."""
    s = sfx
    o = [f'<defs><pattern id="grid{s}" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="rgba(93,235,175,.07)" stroke-width="1"/></pattern>'
         f'<pattern id="strip{s}" width="22" height="50" patternUnits="userSpaceOnUse"><rect width="22" height="50" fill="#CDF2EB"/><rect y="46" width="22" height="4" fill="#9BBFB2"/></pattern>'
         f'<marker id="arr{s}" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M1 1L8 5L1 9" fill="none" stroke="#5DEBAF" stroke-width="2" stroke-linecap="round"/></marker></defs>']
    o.append(f'<g id="cam{s}" class="cam"><g id="plan{s}">')
    o.append('<rect class="floor" x="100" y="80" width="1400" height="840" rx="10"/>')
    o.append(f'<rect x="100" y="80" width="1400" height="840" rx="10" fill="url(#grid{s})"/>')
    o.append(f'<g id="zones{s}" class="zones">')
    for z in ZONES:
        cx = z["x"] + z["w"] / 2
        ly = z["y"] + (112 if z["i"] == 1 else 62 if z["i"] != 6 else 82)
        iy = z["y"] + (52 if z["i"] == 1 else 6 if z["i"] != 6 else 20)
        o.append(f'<g class="zone {z["k"]}" data-z="{z["i"]}" style="--zi:{z["i"]}"><rect class="zfill" x="{z["x"]}" y="{z["y"]}" width="{z["w"]}" height="{z["h"]}" rx="12"/>'
                 f'{ic(z["icon"], cx - 17, iy, 34, "zicon")}<text class="zlabel" x="{cx}" y="{ly}" text-anchor="middle">{z["name"]}</text></g>')
    o.append("</g>")
    o.append(f'<g id="fixtures{s}" class="fixtures">')
    o.append('<rect class="fx fxc" x="150" y="128" width="1300" height="26" rx="4"/>')
    for x0, x1 in [(200, 600), (700, 1100)]:
        o.append(f'<rect class="fx" x="{x0}" y="190" width="{x1 - x0}" height="22" rx="4"/>')
    for x in (190, 270, 350, 480, 560, 640, 720, 800, 1300, 1380):
        o.append(f'<rect class="fx fxs" x="{x}" y="372" width="22" height="318" rx="3" fill="url(#strip{s})"/>')
    for x in GOND:
        o.append(f'<rect class="fx fxt" x="{x}" y="372" width="22" height="318" rx="3" fill="url(#strip{s})"/>')
    for x in (1000, 1120, 1240, 1360):
        o.append(f'<rect class="fx fxk" x="{x}" y="810" width="80" height="30" rx="5"/>')
    o.append("</g>")
    o.append('<path class="wall" d="M100 80H1500V920H760M600 920H100Z"/>')
    o.append('<path class="door" d="M600 920V862A58 58 0 0 1 658 920"/>')
    o.append('<text class="dlabel" x="680" y="962" text-anchor="middle">ورودی</text>')
    o.append(f'<path id="cpath{s}" class="cpath" marker-end="url(#arr{s})" d="M680 915V800H1061V540"/>')
    o.append(f'<g id="cdot{s}" class="cdot"><circle r="15"/><circle r="6"/></g>')
    o.append(f'<g id="aisleLbl{s}" class="aislelbl">')
    for n, x in enumerate(GOND):
        o.append(f'<text class="glabel" x="{x + 11}" y="362" text-anchor="middle">B-0{n + 1}</text>')
    o.append('<text class="alabel" x="1061" y="716" text-anchor="middle">راهرو ۲</text>')
    o.append('<text class="alabel2" x="981" y="716" text-anchor="middle">۱</text><text class="alabel2" x="1141" y="716" text-anchor="middle">۳</text>')
    o.append("</g>")
    o.append("</g>")  # /plan
    o.append(extra)
    o.append("</g>")  # /cam
    return "".join(o)


# ======================================================================= PROBLEM PINS (on the plan)
PINS = [(1, 1101, 500), (2, 280, 520), (3, 872, 706), (4, 680, 884), (5, 858, 152), (6, 1380, 520)]


def pins_layer():
    o = ['<g id="pinsP" class="pins">']
    o.append('<g class="pdet" data-k="1"><rect class="pd-box" x="1074" y="462" width="76" height="76" rx="10"/><text x="1112" y="446" text-anchor="middle" class="pd-t">جای خالی</text></g>')
    o.append('<g class="pdet" data-k="2">' + ic("user-minus", 196, 452, 72, "pd-ic") + '<text x="232" y="560" text-anchor="middle" class="pd-t">با رفتن یک نفر</text></g>')
    o.append('<g class="pdet" data-k="3"><path class="pd-route" d="M466 312H876V706H466Z"/>' + ic("footprints", 650, 470, 44, "pd-ic") + '<text x="671" y="760" text-anchor="middle" class="pd-t">سرکشی هر روزه</text></g>')
    o.append('<g class="pdet" data-k="4"><circle class="pd-box" cx="680" cy="772" r="62"/>' + ic("question", 646, 738, 68, "pd-ic") + '<text x="680" y="690" text-anchor="middle" class="pd-t">خرید حدسی</text></g>')
    o.append('<g class="pdet" data-k="5">' + ic("clipboard-text", 820, 150, 76, "pd-ic") + '<text x="858" y="130" text-anchor="middle" class="pd-t">بدون سند</text></g>')
    o.append('<g class="pdet" data-k="6">' + ic("trend-down", 1346, 456, 68, "pd-ic") + '<text x="1380" y="580" text-anchor="middle" class="pd-t">جای کم‌دید</text></g>')
    for k, x, y in PINS:
        o.append(f'<g class="pin" data-k="{k}" transform="translate({x} {y})"><circle class="pring" r="44"/><circle class="pdot" r="24"/><text class="pnum" y="9" text-anchor="middle">{k}</text></g>')
    o.append("</g>")
    return "".join(o)


def plan_problem():
    return plan_svg("P", pins_layer())


# ======================================================================= OPENING (new store)
def plan_open():
    marks = "".join(
        f'<g class="qrm" style="--i:{i}" transform="translate({x + 11 - 17} 498)"><rect width="34" height="34" rx="7" class="qrm-bg"/>{ic("qr-code", 5, 5, 24, "qrm-ic")}</g>'
        for i, x in enumerate(GOND))
    return plan_svg("O", f'<g id="qrmarksO">{marks}</g><path id="ribbonO" class="ribbon" d="M604 920H756"/>')


# ======================================================================= AISLE (perspective view)
def aisle_svg(W, H, f, vpy, seed, uid, target_bay=1, gap=True):
    random.seed(seed)
    cx = W / 2
    eye, zmin, bayL, nb = 1.2, 1.5, 1.2, 8
    zend = zmin + bayL * nb
    BG = "#051A15"

    def P(x, y, z):
        return (cx + x * f / z, vpy - (y - eye) * f / z)

    def poly(pts, fill, extra=""):
        return '<polygon points="' + " ".join(f"{a:.0f},{b:.0f}" for a, b in pts) + f'" fill="{fill}" {extra}/>'

    def line(p, q, stroke, w=1, extra=""):
        return f'<line x1="{p[0]:.0f}" y1="{p[1]:.0f}" x2="{q[0]:.0f}" y2="{q[1]:.0f}" stroke="{stroke}" stroke-width="{w}" {extra}/>'

    o = [f'<svg class="aisle" id="aisle{uid}" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">']
    o.append(f'<defs><linearGradient id="fl{uid}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#0E3A2F"/><stop offset="1" stop-color="#07231C"/></linearGradient>'
             f'<linearGradient id="ce{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#030E0B"/><stop offset="1" stop-color="#061B16"/></linearGradient>'
             f'<linearGradient id="ew{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0E3A2F"/><stop offset="1" stop-color="#0A2D25"/></linearGradient></defs>')
    o.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    o.append(poly([P(-9, 2.9, .6), P(9, 2.9, .6), P(9, 2.9, zend), P(-9, 2.9, zend)], f"url(#ce{uid})"))
    o.append(poly([P(-9, 0, .5), P(9, 0, .5), P(9, 0, zend), P(-9, 0, zend)], f"url(#fl{uid})"))
    o.append(poly([P(-1, 0, zend), P(1, 0, zend), P(1, 2.9, zend), P(-1, 2.9, zend)], f"url(#ew{uid})"))
    for z in [zmin + i * bayL for i in range(nb + 1)]:
        o.append(line(P(-1, 0, z), P(1, 0, z), "rgba(93,235,175,.08)", 1))
    o.append(line(P(0, 0, .7), P(0, 0, zend), "rgba(93,235,175,.22)", 2, 'stroke-dasharray="14 12"'))
    # soft light pools on the floor under ceiling lights (no blur filters)
    for z in (2.2, 4.8, 7.4):
        o.append(poly([P(-.7, 0, z), P(.7, 0, z), P(.7, 0, z + 1.4), P(-.7, 0, z + 1.4)], "rgba(205,242,235,.045)"))
    levels = [0.14, 0.52, 0.90, 1.28, 1.66]
    for s in (-1, 1):
        o.append(poly([P(s, 0, .5), P(s, 2.05, .5), P(s, 2.05, zend), P(s, 0, zend)], "#0A3329"))
        for k in range(nb + 1):
            z = zmin + bayL * k
            o.append(line(P(s, 0, z), P(s, 2.05, z), "rgba(0,0,0,.4)", 2))
        for y in levels:
            if y < eye:
                o.append(poly([P(s, y, .5), P(s * .8, y, .5), P(s * .8, y, zend), P(s, y, zend)], "#1B5A49"))
            o.append(poly([P(s * .8, y, .5), P(s * .8, y + .045, .5), P(s * .8, y + .045, zend), P(s * .8, y, zend)], "#CDF2EB"))
        for k in range(nb):
            zb0 = zmin + bayL * k
            for li, y in enumerate(levels):
                nprod, z = 6, zb0 + .05
                gapzone = (s == 1 and k == target_bay and li == 2 and gap)
                for pi in range(nprod):
                    w = bayL / nprod * random.uniform(.78, .96)
                    h = random.choice([.20, .26, .32, .36])
                    c = random.choice(PRODUCT)
                    if gapzone and pi in (2, 3):
                        z += bayL / nprod
                        continue
                    fog = min(.85, (z - zmin) / (zend - zmin))
                    cc = mix(c, BG, fog * .8)
                    xx = s * .86
                    o.append(poly([P(xx, y + .045, z), P(xx, y + .045 + h, z), P(xx, y + .045 + h, z + w), P(xx, y + .045, z + w)], cc))
                    z += bayL / nprod
    for z in (2.2, 4.8, 7.4, 10.0):
        pts = [P(-.55, 2.9, z), P(.55, 2.9, z), P(.55, 2.9, z + 1.1), P(-.55, 2.9, z + 1.1)]
        o.append(poly(pts, "#E8F5F0"))
    zs = 4.9
    a, b = P(-.5, 2.2, zs), P(.5, 2.55, zs)
    o.append(f'<rect x="{a[0]:.0f}" y="{b[1]:.0f}" width="{b[0] - a[0]:.0f}" height="{a[1] - b[1]:.0f}" rx="6" fill="#0F4A3C" stroke="#5DEBAF" stroke-width="2"/>')
    ms = P(0, 2.37, zs)
    fs = (b[0] - a[0]) * .34
    o.append(f'<text x="{ms[0]:.0f}" y="{ms[1] + fs * .34:.0f}" text-anchor="middle" font-size="{fs:.0f}" font-weight="800" fill="#5DEBAF">راهرو ۲</text>')
    z0 = zmin + bayL * target_bay
    z1 = z0 + bayL
    tb = [P(1, 0, z0), P(1, 2.05, z0), P(1, 2.05, z1), P(1, 0, z1)]
    o.append(poly(tb, "rgba(93,235,175,.07)", 'class="tb" stroke="#5DEBAF" stroke-width="3" stroke-linejoin="round"'))
    tc = P(1, 1.0, (z0 + z1) / 2)
    lp = P(1, 2.12, (z0 + z1) / 2)
    o.append(f'<g class="tbl"><rect x="{lp[0] - 52:.0f}" y="{lp[1] - 30:.0f}" width="104" height="30" rx="15" fill="#5DEBAF"/><text x="{lp[0]:.0f}" y="{lp[1] - 9:.0f}" text-anchor="middle" font-size="16" font-weight="800" fill="{NIGHT}" direction="ltr">B-03</text></g>')
    o.append("</svg>")
    return "".join(o), dict(tx=round(tc[0], 1), ty=round(tc[1], 1), W=W, H=H, vx=cx, vy=vpy)


# ======================================================================= SHELF (front elevation)
def _item(x, base, maxh, kind, c):
    out = []
    if kind == "bottle":
        w, h = random.choice([34, 40, 46, 52]), random.uniform(.62, 1) * maxh
        out.append(f'<rect x="{x}" y="{base - h:.0f}" width="{w}" height="{h:.0f}" rx="9" fill="{c}"/>')
        out.append(f'<rect x="{x + w / 2 - 8:.0f}" y="{base - h - 12:.0f}" width="16" height="14" rx="3" fill="{mix(c, "#000000", .25)}"/>')
        out.append(f'<rect x="{x + 4}" y="{base - h * .62:.0f}" width="{w - 8}" height="{h * .3:.0f}" rx="4" fill="#E8F5F0" opacity=".85"/>')
    elif kind == "box":
        w, h = random.choice([44, 52, 60, 68]), random.uniform(.5, .85) * maxh
        out.append(f'<rect x="{x}" y="{base - h:.0f}" width="{w}" height="{h:.0f}" rx="4" fill="{c}"/>')
        out.append(f'<rect x="{x}" y="{base - h:.0f}" width="{w}" height="{h * .22:.0f}" rx="4" fill="{mix(c, "#000000", .22)}"/>')
        out.append(f'<rect x="{x + 6}" y="{base - h * .58:.0f}" width="{w - 12}" height="{h * .25:.0f}" rx="3" fill="#E8F5F0" opacity=".8"/>')
    elif kind == "tube":
        w, h = random.choice([22, 26, 30]), random.uniform(.5, .8) * maxh
        out.append(f'<rect x="{x}" y="{base - h:.0f}" width="{w}" height="{h:.0f}" rx="7" fill="{c}"/>')
        out.append(f'<rect x="{x + 3}" y="{base - h * .55:.0f}" width="{w - 6}" height="{h * .2:.0f}" rx="3" fill="#E8F5F0" opacity=".8"/>')
    else:
        w, h = random.choice([46, 54, 62]), random.uniform(.38, .55) * maxh
        out.append(f'<rect x="{x}" y="{base - h:.0f}" width="{w}" height="{h:.0f}" rx="10" fill="{c}"/>')
        out.append(f'<rect x="{x + 2}" y="{base - h - 10:.0f}" width="{w - 4}" height="12" rx="5" fill="{mix(c, "#000000", .3)}"/>')
    return out, w


def shelf_svg(sfx="", dims=False, state=True):
    """Front view of fixture B-03. state=True adds the empty slot + QR + fill/ok layers used by the story."""
    random.seed(5)
    W, H = 1200, 780
    BOARDS = [150, 271, 394, 530, 675]
    LAB = ["175", "147.5", "119.5", "88.5", "55.5"]
    s = sfx
    o = [f'<svg class="shelfsvg" id="shelfsvg{s}" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">']
    o.append(f'<defs><linearGradient id="beam{s}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5DEBAF" stop-opacity="0"/><stop offset=".5" stop-color="#5DEBAF"/><stop offset="1" stop-color="#5DEBAF" stop-opacity="0"/></linearGradient></defs>')
    o.append('<rect x="150" y="76" width="900" height="676" rx="12" fill="#0D3A2F" stroke="#17604C" stroke-width="2"/>')
    for x in range(190, 1020, 30):
        o.append(f'<line x1="{x}" y1="86" x2="{x}" y2="742" stroke="rgba(0,0,0,.18)" stroke-width="2"/>')
    o.append('<rect x="150" y="18" width="900" height="54" rx="10" fill="#145C48"/>')
    o.append('<text x="600" y="55" text-anchor="middle" font-size="30" font-weight="800" fill="#5DEBAF" direction="ltr">B-03</text>')
    for y, l in zip(BOARDS, LAB):
        o.append(f'<line x1="120" y1="{y}" x2="146" y2="{y}" stroke="#5DEBAF" stroke-width="2"/>')
        o.append(f'<text x="112" y="{y + 5}" text-anchor="end" font-size="16" font-weight="700" fill="#A9CDBF" font-family="Inter,Arial,sans-serif">{l}</text>')
    o.append('<line x1="133" y1="150" x2="133" y2="675" stroke="rgba(93,235,175,.4)" stroke-width="1" stroke-dasharray="3 5"/>')
    GX0, GX1 = 540, 700
    for bi, base in enumerate(BOARDS):
        maxh = [64, 100, 104, 118, 126][bi]
        x = 186
        o.append(f'<rect x="170" y="{base}" width="860" height="12" rx="3" fill="#CDF2EB"/><rect x="170" y="{base + 12}" width="860" height="5" fill="#000" opacity=".22"/>')
        while x < 1002:
            kind = random.choice(["bottle", "bottle", "box", "tube", "jar"])
            c = random.choice(PRODUCT)
            if bi == 2 and state and GX0 <= x < GX1 + 10:
                _, _w = _item(GX0 + 14, base, maxh, "bottle", random.choice(PRODUCT))
                x = GX1 + 16
                continue
            items, w = _item(x, base, maxh, kind, c)
            if x + w > 1008:
                break
            o.extend(items)
            x += w + random.choice([4, 6, 8])
        for lx in range(186, 1000, 92):
            if bi == 2 and state and GX0 - 30 < lx < GX1:
                continue
            o.append(f'<rect x="{lx}" y="{base + 19}" width="52" height="11" rx="2" fill="#E8F5F0" opacity=".85"/>')
    if state:
        gf, x = [], GX0 + 8
        for c in ["#5DEBAF", "#9FF2CD", "#2FBF8A", "#CDF2EB"]:
            items, w = _item(x, 394, 104, "bottle", c)
            gf.extend(items)
            x += w + 6
            if x > GX1 - 30:
                break
        o.append(f'<g id="gapFilled{s}" class="gapfilled">{"".join(gf)}</g>')
        mid = (GX0 + GX1) / 2
        o.append(f'<g id="gapEmpty{s}" class="gapempty"><rect class="gaprect" x="{GX0}" y="284" width="{GX1 - GX0}" height="104" rx="10"/>'
                 f'<rect x="{mid - 76}" y="318" width="152" height="38" rx="19" fill="{ALERT}"/><text x="{mid}" y="344" text-anchor="middle" font-size="20" font-weight="800" fill="#3A2A00">جای خالی</text></g>')
        o.append(f'<g id="okBadge{s}" class="okbadge"><rect x="{mid - 74}" y="326" width="148" height="40" rx="20" fill="#5DEBAF"/>{ic("check-circle", mid - 66, 330, 32, "ok-ic")}'
                 f'<text x="{mid + 14}" y="353" text-anchor="middle" font-size="17" font-weight="800" fill="{NIGHT}">مطابق طرح</text></g>')
        qx, qy, qs = 1076, 296, 96
        o.append(f'<g id="qrPlate{s}"><rect id="qrRing{s}" class="qrring" x="{qx - 10}" y="{qy - 10}" width="{qs + 20}" height="{qs + 20}" rx="18"/><rect x="{qx}" y="{qy}" width="{qs}" height="{qs}" rx="10" fill="#E8F5F0"/>'
                 f'{ic("qr-code", qx + 8, qy + 8, qs - 16, "qr-ic")}<rect id="qrBeam{s}" x="{qx - 10}" y="{qy}" width="{qs + 20}" height="6" rx="3" fill="url(#beam{s})" opacity="0"/></g>')
    if dims:
        labs = ["27.5", "28", "31", "33"]
        d = ['<g class="dims">']
        for i in range(4):
            y0, y1 = BOARDS[i] + 16, BOARDS[i + 1] - 2
            d.append(f'<rect x="172" y="{y0}" width="856" height="{y1 - y0}" rx="8" fill="rgba(93,235,175,.07)" stroke="#5DEBAF" stroke-width="2" stroke-dasharray="7 6"/>')
            d.append(f'<g><rect x="888" y="{(y0 + y1) / 2 - 16:.0f}" width="118" height="32" rx="16" fill="#5DEBAF"/><text x="947" y="{(y0 + y1) / 2 + 6:.0f}" text-anchor="middle" font-size="17" font-weight="800" fill="{NIGHT}" direction="ltr" font-family="Inter,Arial,sans-serif">{labs[i]} cm</text></g>')
        d.append("</g>")
        o.append("".join(d))
    o.append("</svg>")
    return "".join(o), dict(qy=296, qs=96)


def mini_shelf(gap):
    W, H, boards = 360, 220, [60, 120, 180]
    o = [f'<svg viewBox="0 0 {W} {H}" class="mini" aria-hidden="true"><rect x="8" y="4" width="344" height="212" rx="10" fill="#0D3A2F" stroke="#17604C" stroke-width="2"/>']
    for bi, b in enumerate(boards):
        o.append(f'<rect x="16" y="{b}" width="328" height="6" rx="2" fill="#CDF2EB"/>')
        x = 24
        random.seed(100 + bi)
        while x < 326:
            w, h, c = random.choice([16, 20, 24, 28]), random.choice([28, 34, 40, 46]), random.choice(PRODUCT)
            if gap and bi == 1 and 150 <= x < 210:
                x = 214
                continue
            if x + w > 334:
                break
            o.append(f'<rect x="{x}" y="{b - h}" width="{w}" height="{h}" rx="4" fill="{c}"/>')
            x += w + 4
    if gap:
        o.append(f'<rect class="mini-gap" x="150" y="68" width="62" height="48" rx="8"/>')
    o.append("</svg>")
    return "".join(o)


def chart_svg():
    random.seed(8)
    hs = [70, 110, 90, 140, 120, 160, 130]
    o = ['<svg viewBox="0 0 420 240" class="chart" aria-hidden="true"><line x1="30" y1="200" x2="400" y2="200" stroke="rgba(205,242,235,.35)"/>']
    pts = []
    for i, h in enumerate(hs):
        x = 52 + i * 50
        o.append(f'<rect class="cb" style="--i:{i}" x="{x}" y="{200 - h}" width="28" height="{h}" rx="5" fill="#2FBF8A"/>')
        pts.append((x + 14, 200 - h - 18 - (i % 3) * 6))
    o.append('<polyline class="cl" points="' + " ".join(f"{a},{b}" for a, b in pts) + '" fill="none" stroke="#5DEBAF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
    for a, b in pts:
        o.append(f'<circle cx="{a}" cy="{b}" r="5" fill="#5DEBAF"/>')
    o.append("</svg>")
    return "".join(o)


# ======================================================================= FRANCHISE NETWORK
def network_svg():
    ring = [(800 + math.cos(-math.pi / 2 + i * math.pi / 4) * 560, 450 + math.sin(-math.pi / 2 + i * math.pi / 4) * 300) for i in range(8)]
    row_x = [320, 560, 800, 1040, 1280]
    o = ['<svg viewBox="0 0 1600 900" class="net" id="netW" preserveAspectRatio="xMidYMid meet" aria-hidden="true">']
    o.append('<g id="netLines"><line class="nl nl-row" x1="320" y1="500" x2="1280" y2="500"/>')
    for i, (x, y) in enumerate(ring):
        o.append(f'<line class="nl nl-ring" x1="800" y1="450" x2="{x:.0f}" y2="{y:.0f}"/>')
    o.append("</g>")
    o.append(f'<g id="hub" class="hub"><circle class="hub-bg" r="92"/>{ic("warehouse", -48, -62, 96, "hub-ic")}<text y="76" text-anchor="middle" class="hub-t">انبار مرکزی</text></g>')
    for i in range(8):
        o.append(f'<g class="st" data-i="{i}"><circle class="st-bg" r="46"/>{ic("storefront", -26, -26, 52, "st-ic")}</g>')
    o.append("</svg>")
    return "".join(o), row_x, [(round(x), round(y)) for x, y in ring]
