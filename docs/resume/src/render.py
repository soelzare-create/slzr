"""HTML/SVG generators for the resume: project articles (plans + photos) and the Kala-Val network diagram."""
import re
from pathlib import Path
from projects import PROJECTS

HERE = Path(__file__).parent
ROOT = HERE.parent
FA_D = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def icon(name, cls="ic"):
    svg = (HERE / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return f'<svg class="{cls}" viewBox="0 0 256 256" aria-hidden="true">{inner}</svg>'


def photo_slot(pid, n, name, draft):
    """Client build: only photos that exist. Draft build: a labelled slot for each missing photo."""
    rel = f"assets/photos/{pid}-{n}.jpg"
    if (ROOT / rel).exists():
        return f'<figure class="photo"><img src="{rel}" alt="عکس پروژهٔ {name}" decoding="async"></figure>'
    if not draft:
        return ""
    return (f'<figure class="photo empty">{icon("camera")}<span>جای عکس پروژه</span>'
            f'<code dir="ltr">{rel}</code></figure>')


def plan(f, cap, name):
    return (f'<figure class="plan"><button type="button" class="plan-btn" aria-label="نمایش بزرگ {cap}">'
            f'<img src="assets/plans/{f}.webp" alt="{cap}، {name}" decoding="async"></button>'
            f'<figcaption>{cap}<span class="zoom-hint">برای دیدن بزرگ‌تر، روی نقشه بزنید</span></figcaption></figure>')


def projects(draft=False):
    out = []
    for i, p in enumerate(PROJECTS):
        plans = "".join(plan(f, cap, p["name"]) for f, cap in p["plans"])
        if plans:
            plans = f'<div class="plans n{len(p["plans"])}">{plans}</div>'
        photos = "".join(photo_slot(p["id"], n, p["name"], draft) for n in range(1, p["photos"] + 1))
        if photos:
            photos = f'<div class="photos">{photos}</div>'
        media = f'<div class="proj-media">{plans}{photos}</div>' if (plans or photos) else ""
        scope = "".join(f"<li>{icon('check-circle')}<span>{x}</span></li>" for x in p["scope"])
        no = str(i + 1).zfill(2).translate(FA_D)
        cls = "proj" + (" flag" if p["flagship"] else "") + ("" if media else " solo")
        out.append(
            f'<article class="{cls}" id="p-{p["id"]}" data-reveal>'
            f'<div class="proj-text"><span class="proj-no" aria-hidden="true">{no}</span><span class="tag">{p["tag"]}</span>'
            f'<h3>{p["name"]}</h3><p class="proj-lead">{p["lead"]}</p><ul class="ticks">{scope}</ul></div>'
            f'{media}</article>')
    return "\n".join(out)


# Kala-Val: four separate networks, named for what they carry (plain words first, the VLAN number small)
VLANS = [("صندوق‌ها و کامپیوترها", "VLAN 10"), ("سرور و دستگاه‌های ضبط", "VLAN 20"),
         ("مدیریت و سرورهای مجازی", "VLAN 30"), ("۱۲۲ دوربین", "VLAN 100")]


def vlan_svg():
    """Central switch in the middle, one network per corner; links are drawn first so boxes cover their ends."""
    w, h, bw, bh = 560, 440, 252, 124
    core = (w / 2, h / 2)
    boxes = [(14, 14), (w - 14 - bw, 14), (14, h - 14 - bh), (w - 14 - bw, h - 14 - bh)]
    out = [f'<svg class="vlan" viewBox="0 0 {w} {h}" role="img" aria-label="چهار شبکهٔ جدا در کالا وال">']
    for x, y in boxes:
        out.append(f'<line class="lk" x1="{core[0]:.0f}" y1="{core[1]:.0f}" x2="{x + bw / 2:.0f}" y2="{y + bh / 2:.0f}"/>')
    for (x, y), (label, v) in zip(boxes, VLANS):
        cx = x + bw / 2
        out.append(f'<rect class="box" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="18"/>'
                   f'<text class="t1" x="{cx:.0f}" y="{y + 58}" text-anchor="middle">{label}</text>'
                   f'<text class="t2" x="{cx:.0f}" y="{y + 94}" text-anchor="middle" direction="ltr">{v}</text>')
    out.append(f'<rect class="core" x="{core[0] - 82:.0f}" y="{core[1] - 28:.0f}" width="164" height="56" rx="16"/>'
               f'<text class="t1 ct" x="{core[0]:.0f}" y="{core[1] + 10:.0f}" text-anchor="middle">سوئیچ مرکزی</text>')
    out.append("</svg>")
    return "".join(out)
