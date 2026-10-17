"""HTML/SVG generators for the resume: project articles (plans + photo slots) and the Kala-Val VLAN diagram."""
import re
from pathlib import Path
from projects import PROJECTS

HERE = Path(__file__).parent
FA_D = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def icon(name, cls="ic"):
    svg = (HERE / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return f'<svg class="{cls}" viewBox="0 0 256 256" aria-hidden="true">{inner}</svg>'


def photo_slot(pid, n, name):
    """An <img> that removes itself when the photo file is missing, leaving a labelled placeholder."""
    src = f"assets/photos/{pid}-{n}.jpg"
    return (f'<figure class="photo"><img src="{src}" alt="عکس پروژهٔ {name}" decoding="async" '
            "onerror=\"this.parentNode.classList.add('empty');this.remove()\">"
            f'<figcaption class="ph-empty">{icon("camera")}<span>جای عکس پروژه</span>'
            f'<code dir="ltr">{src}</code></figcaption></figure>')


def projects():
    out = []
    for i, p in enumerate(PROJECTS):
        plans = "".join(
            f'<figure class="plan"><a href="assets/plans/{f}.webp" target="_blank" rel="noopener" aria-label="بزرگ‌نمایی {cap}">'
            f'<img src="assets/plans/{f}.webp" alt="{cap}، {p["name"]}" decoding="async"></a><figcaption>{cap}</figcaption></figure>'
            for f, cap in p["plans"])
        if plans:
            plans = f'<div class="plans n{len(p["plans"])}">{plans}</div>'
        photos = "".join(photo_slot(p["id"], n, p["name"]) for n in range(1, p["photos"] + 1))
        scope = "".join(f"<li>{icon('check-circle')}<span>{x}</span></li>" for x in p["scope"])
        no = str(i + 1).zfill(2).translate(FA_D)
        flag = " flag" if p["flagship"] else ""
        out.append(
            f'<article class="proj{flag}" id="p-{p["id"]}" data-reveal>'
            f'<div class="proj-text"><span class="proj-no" aria-hidden="true">{no}</span><span class="tag">{p["tag"]}</span>'
            f'<h3>{p["name"]}</h3><p class="proj-lead">{p["lead"]}</p><ul class="ticks">{scope}</ul></div>'
            f'<div class="proj-media">{plans}<div class="photos">{photos}</div></div></article>')
    return "\n".join(out)


VLANS = [("VLAN 10", "کامپیوترها، صندوق‌ها و ترازوها"), ("VLAN 20", "سرور، ESXi و دستگاه‌های ضبط"),
         ("VLAN 30", "مدیریت و ۸ سرور مجازی"), ("VLAN 100", "۱۲۲ دوربین")]


def vlan_svg():
    """Core switch in the middle, one VLAN box per corner; links are drawn first so boxes cover their ends."""
    w, h, bw, bh = 560, 440, 236, 112
    core = (w / 2, h / 2)
    boxes = [(14, 14), (w - 14 - bw, 14), (14, h - 14 - bh), (w - 14 - bw, h - 14 - bh)]
    out = [f'<svg class="vlan" viewBox="0 0 {w} {h}" role="img" aria-label="چهار شبکهٔ جدا در کالا وال">']
    for x, y in boxes:
        out.append(f'<line class="lk" x1="{core[0]:.0f}" y1="{core[1]:.0f}" x2="{x + bw / 2:.0f}" y2="{y + bh / 2:.0f}"/>')
    for (x, y), (v, d) in zip(boxes, VLANS):
        cx = x + bw / 2
        out.append(f'<rect class="box" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="16"/>'
                   f'<text class="t1" x="{cx:.0f}" y="{y + 46}" text-anchor="middle" direction="ltr">{v}</text>'
                   f'<text class="t2" x="{cx:.0f}" y="{y + 82}" text-anchor="middle">{d}</text>')
    out.append(f'<rect class="core" x="{core[0] - 78:.0f}" y="{core[1] - 26:.0f}" width="156" height="52" rx="14"/>'
               f'<text class="t1 ct" x="{core[0]:.0f}" y="{core[1] + 9:.0f}" text-anchor="middle">سوئیچ کور</text>')
    out.append("</svg>")
    return "".join(out)
