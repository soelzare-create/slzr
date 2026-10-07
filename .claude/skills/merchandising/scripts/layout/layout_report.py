"""Build the DaranX category-layout report from a spec.

  python3 -I layout_report.py SPEC.py BASE.png OUTDIR
    BASE.png = `dxf_tools.py base ...` output (transparent line drawing of the plan, same crop as spec META["crop"])
  writes OUTDIR/<id>.html (standalone, everything inlined), OUTDIR/artifact/<id>.html (for a claude.ai artifact: no skeleton,
  no theme toggle) and OUTDIR/<id>-preview.html. Needs the daranx-proposal-kit template (found automatically, or DARANX_KIT=path).
"""
import sys, base64, html, re, os, math, glob, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SPEC, BASE_PNG, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
_sp = importlib.util.spec_from_file_location("layout_spec", SPEC); M = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(M)
META = M.META
from layout_common import label_fit
os.makedirs(f"{OUTDIR}/artifact", exist_ok=True)

def _find_kit():
    if os.environ.get("DARANX_KIT"): return os.environ["DARANX_KIT"]
    pats = ["/root/.claude/skills/**/daranx-proposal-kit/assets/template.html", os.path.expanduser("~/.claude/skills/**/daranx-proposal-kit/assets/template.html"),
            os.path.join(HERE, "../../../**/daranx-proposal-kit/assets/template.html")]
    for pat in pats:
        hit = glob.glob(pat, recursive=True)
        if hit: return hit[0]
    sys.exit("daranx-proposal-kit template not found; set DARANX_KIT=/path/to/template.html")
KIT = _find_kit()
ASSETS = os.path.join(HERE, "assets")
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def fa(n): return str(n).translate(FA)
def uri(path, mime): return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()

VX0, VY0, VW, VH = META["crop"]   # plan crop (DXF metres)
def P(x, y): return f"{x:.2f},{-y:.2f}"

ZI = {c[0]: c for c in M.Z}
STATIONS = META["stations"]
assert sorted(sum((s[1] for s in STATIONS), [])) == sorted(ZI), "station list must cover every zone"

PIN = '<svg viewBox="0 0 12 16" aria-hidden="true"><path d="M6 0a6 6 0 0 0-6 6c0 4.5 6 10 6 10s6-5.5 6-10a6 6 0 0 0-6-6zm0 8.4A2.4 2.4 0 1 1 6 3.6a2.4 2.4 0 0 1 0 4.8z"/></svg>'

ZG = {c: g[0] for g in M.GROUPS for c in g[7]}
GN = {g[0]: g for g in M.GROUPS}
# when the moving shopper first gets close to each group (fraction of the loop)
_pts = M.FLOW; _seg = [math.dist(a, b) for a, b in zip(_pts, _pts[1:])]; _L = sum(_seg)
def _at(t):
    d = t * _L
    for (a, b), l in zip(zip(_pts, _pts[1:]), _seg):
        if d <= l: return (a[0] + (b[0] - a[0]) * d / l, a[1] + (b[1] - a[1]) * d / l)
        d -= l
    return _pts[-1]
VIS = {}
for g in M.GROUPS:
    VIS[g[0]] = min(range(0, 401), key=lambda i: math.dist(_at(i / 400), g[5])) / 400
FLOW_D = "M" + " L".join(P(*p) for p in M.FLOW)
DUR = 22
# ---------- plan SVG
zones = []
for zi, (code, fam, poly, name, en, fix) in enumerate(M.Z):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    txt, fs, vert = label_fit(code, poly, M.SHORT)
    rot = f' transform="rotate(-90 {cx:.2f} {-cy:.2f})"' if vert else ""
    label = html.escape(f"{code} · {name}")
    zones.append(
        f'<g class="zn f-{fam}" data-c="{code}" data-g="{ZG[code]}" style="--i:{zi}" tabindex="0" role="button" aria-label="{label}">'
        f'<title>{label}</title><polygon points="{" ".join(P(*p) for p in poly)}"/>'
        f'<text x="{cx:.2f}" y="{-cy:.2f}" font-size="{fs:.3f}"{rot}>{html.escape(txt)}</text></g>')

FA_D = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
grs = []
for gi, (gid, fam, gfa, gen, polys, (lx, ly), grot, members) in enumerate(M.GROUPS):
    rot = f' transform="rotate(-90 {lx:.2f} {-ly:.2f})"' if grot else ""
    label_svg = (f'<text class="glab" x="{lx:.2f}" y="{-ly:.2f}"{rot}><tspan class="gtag" x="{lx:.2f}" dy="-.22">گروه کالایی {gid.translate(FA_D)}</tspan>'
                 f'<tspan class="gname" x="{lx:.2f}" dy=".42">{gfa}</tspan></text>') if gfa else ""
    grs.append(f'<g class="gr f-{fam}" data-g="{gid}" style="--i:{gi};--t:{VIS[gid]:.3f}">'
               + "".join(f'<polygon points="{" ".join(P(*q) for q in poly)}"/>' for poly in polys)
               + label_svg + "</g>")
GROUPS_SVG = "".join(grs)
flow = " ".join(P(*p) for p in M.FLOW); spine = " ".join(P(*p) for p in M.SPINE)
import math
chev = []
for (x1, y1), (x2, y2) in zip(M.FLOW, M.FLOW[1:]):
    if math.dist((x1, y1), (x2, y2)) > 3:
        mx, my = (x1 + x2) / 2, -(y1 + y2) / 2
        ang = math.degrees(math.atan2(-(y2 - y1), x2 - x1))
        chev.append(f'<path class="chev" d="M-.26 -.22 L.18 0 L-.26 .22 z" transform="translate({mx:.2f} {my:.2f}) rotate({ang:.1f})"/>')
CHEV = "".join(chev)
GHOSTS = "".join(
    f'<rect class="ghost" x="{o[0]}" y="{-o[3]}" width="{o[2] - o[0]:.2f}" height="{o[3] - o[1]:.2f}" rx=".1"/>'
    f'<text class="ghost-t" x="{(o[0] + o[2]) / 2:.2f}" y="{-(o[1] + o[3]) / 2:.2f}">{t}</text>' for o, t in META.get("ghosts", []))
DOORS = "".join(f'<text class="door-t{" sm" if sm else ""}" x="{x}" y="{-y}">{t}</text>' for t, x, y, sm in META["doors"])
PLAN = f'''<svg class="plan-svg" viewBox="{VX0} {-(VY0 + VH)} {VW} {VH}" role="img" aria-labelledby="plan-t">
  <title id="plan-t">نقشهٔ پیشنهادی چیدمان دسته‌کالا با مسیر مشتری</title>
  <defs><marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" class="ahp"/></marker></defs>
  <image class="base" href="%%BASE%%" x="{VX0}" y="{-(VY0 + VH)}" width="{VW}" height="{VH}" preserveAspectRatio="none"/>
  {GROUPS_SVG}
  {GHOSTS}
  <polyline class="spine" points="{spine}" marker-mid="url(#ah)"/>
  <polyline class="flow" points="{flow}" marker-end="url(#ah)"/>
  {CHEV}
  {"".join(zones)}
  <g class="dotg"><animateMotion dur="{DUR}s" repeatCount="indefinite" path="{FLOW_D}" rotate="0"/><circle class="halo" r=".42"/><circle class="dot" r=".18"/></g>
  {DOORS}
</svg>'''

legend = "".join(f'<span><i class="lg f-{k}"></i>{v[0]}</span>' for k, v in M.FAM.items())
chips = "".join(f'<button type="button" class="gchip f-{g[1]}" data-g="{g[0]}"><i class="lg"></i>گروه {g[0].translate(FA)} · {g[2]}</button>' for g in M.GROUPS)

rows = []
for title, codes in STATIONS:
    rows.append(f'<li class="st">{title}</li>')
    for c in codes:
        code, fam, poly, name, en, fix = ZI[c]
        rows.append(f'<li class="row" id="r-{c}"><button type="button" class="code loc" data-loc="{c}" '
                    f'aria-label="نمایش {c} روی نقشه">{PIN}{c}</button><span class="fam"><i class="lg f-{fam}"></i>{M.FAM[fam][0]}</span>'
                    f'<p><b>{name}</b><span class="fix">{fix}</span></p></li>')

def lk(c): return f'<button type="button" class="mini loc" data-loc="{c}">{c}</button>'
def _dec(t): return re.sub(r"\[\[([A-Za-z0-9]+)\]\]", lambda m: lk(m.group(1)), t)
DECISIONS = "\n      ".join(f"<li>{_dec(t)}</li>" for t in META["decisions"])
ROUTE = "\n      ".join(f'<li><i class="lg f-{f}"></i>{t}</li>' for f, t in META["route"])
def _stat(i, lab, v):
    v = len(M.Z) if v == "{zones}" else v
    return f'<div class="stat" role="listitem"><span class="lbl">{lab}</span><span class="val" data-to="{v}">{fa(v)}</span></div>'
STATS = "\n    ".join(_stat(i, l, v) for i, (l, v) in enumerate(META["stats"]))

BODY = f'''<body>
<header class="topbar"><div class="wrap">
  <a class="brand" href="#top"><img src="%%LOGO%%" alt="DaranX"></a>
  <div class="top-right"><span class="chip">طرح چیدمان · مرچندایزینگ</span>%%TOGGLE%%</div>
</div></header>

<section class="hero" id="top"><div class="wrap">
  <span class="eyebrow">{META["eyebrow"]}</span>
  <h1>{META["h1"]}</h1>
  <p>{META["sub"]}</p>
  <p class="meta-line">تهیه‌شده توسط <bdi>DaranX</bdi> · {META["date"]}</p>
</div></section>

<main>
<section class="glance"><div class="wrap">
  <div class="stats" role="list">
    {STATS}
  </div>
  <div class="g2">
    <div class="box"><h2>{fa(len(META["decisions"]))} تصمیم کلیدی</h2><ol class="acts">
      {DECISIONS}
    </ol></div>
    <div class="box"><h2>مسیر مشتری</h2><ol class="route">
      {ROUTE}
    </ol>
    <p class="pro">{META["pro"]}</p></div>
  </div>
</div></section>

<section class="planbox" id="plan"><div class="wrap">
  <div class="plan-head"><h2>نقشهٔ پیشنهادی</h2><span class="hint-m">نقشه را بکشید تا بقیه‌اش را ببینید</span><span class="hint-g">روی گروه بزنید تا روشن شود</span></div>
  <div class="gchips" role="group" aria-label="گروه‌های کالایی">{chips}</div>
  <div class="legend">{legend}<span><i class="lg flow"></i>مسیر اصلی</span><span><i class="lg spine"></i>مسیر کوتاه</span></div>
  <figure class="plan-fig"><div class="plan-scroll" id="plan-scroll">{PLAN}</div>
    <figcaption><span id="info" class="info" aria-live="polite">روی هر کد بزنید تا نام دسته و تجهیزش را ببینید.</span></figcaption>
  </figure>
</div></section>

<section class="more"><div class="wrap">
  <div class="more-head"><h2>جزئیات</h2><button class="btn-x" id="toggle-all" type="button">باز کردن همه</button></div>
  <p class="hint">کدها دوطرفه‌اند: کد روی نقشه ← نام و جایگاه · کد در فهرست ← محل روی نقشه.</p>
  <details id="d-list"><summary><span>همهٔ جایگاه‌ها به ترتیب مسیر</span><em>{fa(len(M.Z))} جایگاه</em></summary>
    <ol class="rows">{"".join(rows)}</ol></details>
</div></section>
</main>

<footer class="foot"><div class="wrap">
  <div class="brand" style="color:#fff">Daran<span style="color:var(--steel-soft)">X</span></div>
  <div class="ph-row"><a href="tel:+982188964116">۰۲۱-۸۸۹۶۴۱۱۶</a> · <a href="tel:+982188966904">۸۸۹۶۶۹۰۴</a> · <a href="tel:+989359370910">۰۹۳۵-۹۳۷۰۹۱۰</a></div>
  <div>تهران، میدان فاطمی، نبش چهلستون، ساختمان چهلستون، طبقه ۲، واحد ۲۰۲</div>
  <div><a href="https://www.daranx.com">www.DaranX.com</a> — همه چیز سرِ جای درستش.</div>
</div></footer>
'''

SCRIPT = '''<script>
(function(){
  %%THEMEJS%%
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var NAMES=%%NAMES%%;
  var info=document.getElementById('info'),svg=document.querySelector('.plan-svg'),tm=0;
  function zone(c){return svg.querySelector('.zn[data-c="'+c+'"]');}
  function mark(row){document.querySelectorAll('.row.target').forEach(function(r){if(r!==row)r.classList.remove('target','hit')});
    if(row){row.classList.add('target');row.classList.remove('hit');void row.offsetWidth;row.classList.add('hit');}}
  function select(c,scroll){var z=zone(c);if(!z)return;
    svg.querySelectorAll('.zn.sel').forEach(function(e){e.classList.remove('sel')});
    z.classList.add('sel');svg.classList.add('locating');clearTimeout(tm);tm=setTimeout(function(){svg.classList.remove('locating')},5000);
    var n=NAMES[c];info.innerHTML='<b dir="ltr">'+c+'</b> · '+n[0]+' <span class="fx">— '+n[1]+'</span> <span class="gb">'+n[2]+'</span> <a href="#r-'+c+'" class="to-row">در فهرست ↓</a>';
    setGroup(z.dataset.g,false);
    if(scroll){var box=document.getElementById('plan');box.scrollIntoView({block:'start',behavior:reduce?'auto':'smooth'});
      var sc=document.getElementById('plan-scroll'),r=z.getBoundingClientRect(),s=sc.getBoundingClientRect();
      if(sc.scrollWidth>sc.clientWidth)sc.scrollLeft+=(r.left+r.width/2)-(s.left+s.width/2);}}
  var gcur=null;
  function setGroup(g,toggle){if(toggle&&gcur===g)g=null;gcur=g;
    svg.querySelectorAll('.gr.on').forEach(function(e){e.classList.remove('on')});
    document.querySelectorAll('.gchip.on').forEach(function(e){e.classList.remove('on')});
    svg.classList.toggle('gsel',!!g);
    svg.querySelectorAll('.zn').forEach(function(e){e.classList.toggle('ing',!!g&&e.dataset.g===g)});
    if(g){var r=svg.querySelector('.gr[data-g="'+g+'"]'),ch=document.querySelector('.gchip[data-g="'+g+'"]');
      if(r)r.classList.add('on');if(ch)ch.classList.add('on');}}
  document.querySelectorAll('.gchip').forEach(function(b){b.addEventListener('click',function(){
    svg.querySelectorAll('.zn.sel').forEach(function(e){e.classList.remove('sel')});svg.classList.remove('locating');
    setGroup(b.dataset.g,true);info.textContent=gcur?'گروه '+b.textContent.replace(/^گروه /,'').trim()+' — روی هر کد بزنید تا جزئیاتش را ببینید.':'روی هر کد بزنید تا نام دسته و تجهیزش را ببینید.';});});
  svg.querySelectorAll('.gr').forEach(function(r){r.addEventListener('click',function(){setGroup(r.dataset.g,true)})});
  var io='IntersectionObserver' in window&&new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){svg.classList.add('play');io.disconnect();}})},{threshold:.15});
  if(io)io.observe(svg);else svg.classList.add('play');
  svg.addEventListener('click',function(e){var z=e.target.closest('.zn');if(z)select(z.dataset.c,false);});
  svg.addEventListener('keydown',function(e){var z=e.target.closest('.zn');if(z&&(e.key==='Enter'||e.key===' ')){e.preventDefault();select(z.dataset.c,false);}});
  function openRow(id){var t=document.getElementById(id);if(!t)return;var d=t.closest('details');if(d&&!d.open)d.open=true;
    mark(t);t.scrollIntoView({block:'center',behavior:reduce?'auto':'smooth'});}
  document.addEventListener('click',function(e){var b=e.target.closest('.loc');
    if(b){var row=b.closest('.row');if(row&&row.id)mark(row);select(b.dataset.loc,true);return;}
    var a=e.target.closest('a.to-row');if(a){e.preventDefault();openRow(a.getAttribute('href').slice(1));}});
  var all=document.querySelectorAll('details'),tg=document.getElementById('toggle-all');
  tg.addEventListener('click',function(){var open=tg.dataset.open!=='1';all.forEach(function(d){d.open=open});
    tg.dataset.open=open?'1':'0';tg.textContent=open?'بستن همه':'باز کردن همه';});
  addEventListener('beforeprint',function(){all.forEach(function(d){d.open=true})});
  var faNum=function(n){return String(n).replace(/[0-9]/g,function(d){return '۰۱۲۳۴۵۶۷۸۹'[d]})};
  if(!reduce){document.querySelectorAll('.stat .val[data-to]').forEach(function(el,i){
    var to=+el.dataset.to,t0=null,dur=900+i*150;el.textContent=faNum(0);
    function step(ts){if(!t0)t0=ts;var k=Math.min(1,(ts-t0)/dur);k=1-Math.pow(1-k,3);
      el.textContent=faNum(Math.round(to*k));if(k<1)requestAnimationFrame(step);}
    setTimeout(function(){requestAnimationFrame(step)},250+i*90);});}
})();
</script>
</body>
</html>
'''

THEMEJS = '''var r=document.documentElement,b=document.getElementById('tt');
  try{var s=localStorage.getItem('dx-doc-theme');if(s)r.setAttribute('data-theme',s);}catch(e){}
  if(b)b.addEventListener('click',function(){var cur=r.getAttribute('data-theme');
    var dark=cur?cur==='dark':matchMedia('(prefers-color-scheme:dark)').matches;
    var next=dark?'light':'dark';r.setAttribute('data-theme',next);
    try{localStorage.setItem('dx-doc-theme',next)}catch(e){}});'''

fam_light = "".join(f"--c-{k}:{v[2]};" for k, v in M.FAM.items())
fam_dark = "".join(f"--c-{k}:{v[3]};" for k, v in M.FAM.items())
fam_rules = "".join(f".f-{k}{{--c:var(--c-{k})}}" for k in M.FAM)
CSS = '''
:root{%%FL%%--sev-crit:#B42318;--sev-major:#B76E00;--sev-minor:#7A8699}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){%%FD%%--sev-crit:#F97066;--sev-major:#FDB022;--sev-minor:#8398AF}}
:root[data-theme="dark"]{%%FD%%--sev-crit:#F97066;--sev-major:#FDB022;--sev-minor:#8398AF}
%%FR%%
.wrap{max-width:1040px}
.top-right{display:flex;align-items:center;gap:.7rem}
.brand img{height:34px;width:auto}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .topbar .brand img{filter:brightness(0) invert(1)}}
:root[data-theme="dark"] .topbar .brand img{filter:brightness(0) invert(1)}
.hero{background:linear-gradient(240deg,#0E2749 0%,#153A62 55%,#2E6098 100%);color:#fff;padding:2.1rem 0 1.9rem}
.hero .eyebrow{color:#cfe0f2}.hero .eyebrow::before{background:#cfe0f2}
.hero h1{color:#fff;font-size:clamp(1.4rem,1.05rem+1.5vw,2.1rem);font-weight:900;margin:.7rem 0 .5rem;line-height:1.5}
.hero p{margin:0;color:var(--on-navy);font-size:1.02rem}
.hero .meta-line{margin-top:.5rem;font-size:.85rem;color:var(--on-navy-soft)}
.glance{padding:1.5rem 0 1rem}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:.75rem 1rem;display:flex;flex-direction:column;gap:.15rem;box-shadow:var(--shadow)}
.stat .lbl{color:var(--ink-faint);font-size:.88rem;font-weight:700}
.stat .val{color:var(--ink);font-size:1.9rem;font-weight:800;line-height:1.2}
.g2{display:grid;grid-template-columns:1.15fr .85fr;gap:.9rem;margin-top:.9rem}
.box{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:1rem 1.2rem;box-shadow:var(--shadow)}
.box h2{font-size:1.1rem;margin-bottom:.5rem}
.acts{margin:0;padding-inline-start:1.2rem;line-height:1.95;color:var(--ink-soft)}
.acts li{margin:.15rem 0}.acts li::marker{color:var(--steel);font-weight:900}
.route{list-style:none;margin:0;padding:0;line-height:2;color:var(--ink-soft)}
.route li{display:flex;align-items:center;gap:.5rem}
.pro{margin:.5rem 0 0;color:var(--steel);font-size:.88rem;font-weight:700;line-height:1.8}
.lg{display:inline-block;width:14px;height:11px;border-radius:3px;background:var(--c);flex:none;opacity:.85}
.lg.flow{height:0;border-top:3px solid var(--steel);border-radius:0;background:none}
.lg.spine{height:0;border-top:2px dashed var(--steel);border-radius:0;background:none;opacity:.7}
button.mini{font-family:inherit;font-size:.74rem;font-weight:800;direction:ltr;unicode-bidi:isolate;white-space:nowrap;cursor:pointer;
  color:var(--steel);background:var(--surface-2);border:1px solid var(--line-strong);border-radius:999px;padding:.05rem .5rem;margin-inline-start:.15rem;vertical-align:1px}
button.mini:hover,button.mini:focus-visible{background:var(--steel);color:#fff;border-color:var(--steel)}
/* plan */
.planbox{padding:.4rem 0 1rem}
.plan-head{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;margin:.4rem 0 .5rem}
.plan-head h2{font-size:1.25rem}
.hint-m{display:none;color:var(--ink-faint);font-size:.82rem}
.plan-head{flex-wrap:wrap}
.legend{display:flex;flex-wrap:wrap;gap:.35rem 1rem;color:var(--ink-soft);font-size:.86rem;margin-bottom:.6rem}
.legend span{display:inline-flex;align-items:center;gap:.4rem}
.plan-fig{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);box-shadow:var(--shadow);padding:.6rem}
.plan-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.plan-svg{display:block;width:100%;height:auto;min-width:640px}
.plan-svg .base{opacity:.62}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .plan-svg .base{filter:invert(1);opacity:.55}}
:root[data-theme="dark"] .plan-svg .base{filter:invert(1);opacity:.55}
.gr{cursor:pointer}
.gr polygon{fill:var(--c);fill-opacity:.17;stroke:var(--c);stroke-opacity:.55;stroke-width:.04;stroke-dasharray:.2 .14;transition:fill-opacity .3s}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .gr polygon{fill-opacity:.24}}
:root[data-theme="dark"] .gr polygon{fill-opacity:.24}
.glab{font-family:var(--font);text-anchor:middle;dominant-baseline:central;pointer-events:none;paint-order:stroke;stroke:var(--surface);stroke-width:.07;stroke-linejoin:round}
.gtag{font-size:.25px;font-weight:700;fill:var(--ink-soft)}
.gname{font-size:.36px;font-weight:900;fill:var(--ink)}
.gr.on polygon{fill-opacity:.42!important;stroke-opacity:1;stroke-dasharray:none;stroke-width:.08}
.plan-svg.gsel .gr:not(.on){opacity:.35}.plan-svg.gsel .zn:not(.ing):not(.sel){opacity:.35}
.gr{transition:opacity .3s}
.dot{fill:var(--steel);stroke:#fff;stroke-width:.06}.halo{fill:var(--steel);opacity:.28}
.gchips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.1rem 0 .7rem}
.gchip{font-family:inherit;font-size:.82rem;font-weight:700;color:var(--ink);cursor:pointer;display:inline-flex;align-items:center;gap:.4rem;
  background:color-mix(in srgb,var(--c) 14%,var(--surface));border:1px solid color-mix(in srgb,var(--c) 55%,var(--line));border-radius:999px;padding:.28rem .8rem;transition:transform .15s,background .2s}
.gchip:hover{transform:translateY(-2px)}
.gchip.on{background:color-mix(in srgb,var(--c) 38%,var(--surface));border-color:var(--c)}
.gb{display:inline-block;font-size:.8rem;font-weight:700;color:var(--ink);background:var(--surface-2);border-radius:999px;padding:0 .6rem;margin-inline:.2rem}
.hint-g{color:var(--ink-faint);font-size:.82rem}
.zn{cursor:pointer;outline:none}
.zn polygon{fill:var(--c);fill-opacity:.5;stroke:var(--c);stroke-width:.04;transition:fill-opacity .2s,opacity .25s}
.zn text{fill:var(--ink);font-family:var(--font);font-weight:800;text-anchor:middle;dominant-baseline:central;direction:ltr;
  paint-order:stroke;stroke:var(--surface);stroke-width:.06;stroke-linejoin:round;pointer-events:none}
.zn:hover polygon,.zn:focus-visible polygon{fill-opacity:.8}
.zn.sel polygon{fill-opacity:.9;stroke:var(--ink);stroke-width:.1}
.plan-svg.locating .zn:not(.sel){opacity:.3}
.zn{transition:opacity .25s}
.flow{fill:none;stroke:var(--steel);stroke-width:.11;stroke-linejoin:round;stroke-dasharray:.42 .24;opacity:.95}
.spine{fill:none;stroke:var(--steel);stroke-width:.06;stroke-dasharray:.18 .18;opacity:.7}
.ahp{fill:var(--steel)}
.chev{fill:var(--steel)}
.ghost{fill:none;stroke:var(--ink-faint);stroke-width:.05;stroke-dasharray:.15 .12}
.ghost-t{fill:var(--ink-faint);font-family:var(--font);font-size:.28px;text-anchor:middle;dominant-baseline:central}
.door-t{fill:var(--ink);font-family:var(--font);font-size:.42px;font-weight:800;text-anchor:middle}
.door-t.sm{font-size:.3px;font-weight:700;fill:var(--ink-soft)}
figcaption{margin-top:.5rem;color:var(--ink-faint);font-size:.9rem;min-height:1.6em}
.info b{color:var(--ink)}.info .fx{color:var(--ink-faint)}.info a{font-weight:700;white-space:nowrap}
/* details */
.more{padding:.4rem 0 2.4rem}
.more-head{display:flex;align-items:center;justify-content:space-between;margin:.6rem 0}
.more-head h2{font-size:1.2rem}
.hint{margin:-.2rem 0 .5rem;color:var(--ink-faint);font-size:.85rem}
.btn-x{font-family:inherit;font-weight:700;font-size:.88rem;color:var(--steel);background:transparent;border:1px solid var(--line-strong);border-radius:999px;padding:.35rem .9rem;cursor:pointer}
details{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);margin:.55rem 0;box-shadow:var(--shadow)}
summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:.6rem;padding:.85rem 1.1rem;font-weight:800;color:var(--ink)}
summary::-webkit-details-marker{display:none}
summary::before{content:"";width:8px;height:8px;border-inline-end:2px solid var(--steel);border-bottom:2px solid var(--steel);transform:rotate(45deg);transition:transform .2s;flex:none;margin-top:-4px}
details[open]>summary::before{transform:rotate(225deg);margin-top:4px}
summary em{margin-inline-start:auto;font-style:normal;font-weight:600;font-size:.85rem;color:var(--ink-faint)}
details>*:not(summary){margin-inline:1.1rem}
details>*:last-child{margin-bottom:1rem}
.rows{list-style:none;padding:0;margin-top:.1rem}
.st{font-weight:800;color:var(--steel);font-size:.9rem;padding:.7rem 0 .2rem;border-top:1px solid var(--line)}
.st:first-child{border-top:0;padding-top:.1rem}
.row{display:grid;grid-template-columns:auto auto 1fr;gap:.2rem .7rem;align-items:start;padding:.5rem 0;border-top:1px dashed var(--line);scroll-margin-top:90px}
.st+.row{border-top:0}
.row .code{font-weight:900;color:var(--steel);direction:ltr;unicode-bidi:isolate;font-size:.85rem;padding-top:.1rem}
button.code.loc{font-family:inherit;display:inline-flex;align-items:center;gap:.3rem;cursor:pointer;background:var(--surface-2);
  border:1px solid var(--line-strong);border-radius:999px;padding:.08rem .55rem .08rem .45rem;line-height:1.5}
button.code.loc svg{width:9px;height:12px;fill:currentColor;flex:none}
button.code.loc:hover,button.code.loc:focus-visible{background:var(--steel);border-color:var(--steel);color:#fff}
.fam{display:inline-flex;align-items:center;gap:.35rem;font-size:.8rem;font-weight:700;color:var(--ink-soft);white-space:nowrap;padding-top:.2rem}
.sev{display:inline-flex;align-items:center;gap:.3rem;font-size:.8rem;font-weight:700;color:var(--ink-soft);white-space:nowrap;padding-top:.15rem}
.sev i{width:9px;height:9px;border-radius:50%;display:inline-block}
.sev.crit i{background:var(--sev-crit)}.sev.major i{background:var(--sev-major)}.sev.minor i{background:var(--sev-minor)}
.row p{margin:0;line-height:1.8}.row b{color:var(--ink);font-weight:700}
.fix{display:block;color:var(--ink-faint);font-size:.88rem}
.row.target{position:relative;z-index:1;border-radius:10px;padding-inline:.65rem;margin-inline:-.65rem;
  background:color-mix(in srgb,var(--steel) 9%,var(--surface));box-shadow:0 0 0 2px var(--steel);border-top-color:transparent}
.row.target+.row{border-top-color:transparent}
.bul{margin-top:.3rem;padding-inline-start:1.2rem;line-height:1.9;color:var(--ink-soft)}
@keyframes hit{0%{box-shadow:0 0 0 9px color-mix(in srgb,var(--steel) 35%,transparent)}100%{box-shadow:0 0 0 2px var(--steel)}}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes heroflow{from{background-position:0% 50%}to{background-position:100% 50%}}
@keyframes march{to{stroke-dashoffset:-1.32}}
@keyframes selp{0%,100%{stroke-width:.1}50%{stroke-width:.22}}
@keyframes gin{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}
@keyframes zpop{from{opacity:0;transform:scale(.5)}to{opacity:1;transform:none}}
@keyframes visit{0%{fill-opacity:.55;stroke-opacity:1;stroke-width:.1}14%{fill-opacity:.17;stroke-width:.04}100%{fill-opacity:.17;stroke-width:.04}}
@keyframes chev{0%,100%{opacity:.35}50%{opacity:1}}
@keyframes halo{0%,100%{transform:scale(.7);opacity:.35}50%{transform:scale(1.25);opacity:.08}}
@keyframes lab{from{opacity:0;transform:translateY(.25px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.dotg{display:none}}
@media (prefers-reduced-motion:no-preference){
  .plan-svg:not(.play) .gr,.plan-svg:not(.play) .zn,.plan-svg:not(.play) .flow,.plan-svg:not(.play) .chev{opacity:0}
  .plan-svg .gr{transform-box:fill-box;transform-origin:center}
  .plan-svg.play .gr{animation:gin .8s ease backwards;animation-delay:calc(var(--i) * .22s)}
  .plan-svg.play .gr polygon{animation:visit %%DUR%%s linear infinite;animation-delay:calc(2.5s + var(--t) * %%DUR%%s)}
  .plan-svg.play .glab{animation:lab .7s ease backwards;animation-delay:calc(.5s + var(--i) * .22s)}
  .plan-svg .zn{transform-box:fill-box;transform-origin:center}
  .plan-svg.play .zn{animation:zpop .55s cubic-bezier(.2,.9,.3,1.35) backwards;animation-delay:calc(.9s + var(--i) * .035s)}
  .plan-svg.play .flow{animation:march 2.2s linear infinite,gin 1s ease 1.2s backwards}
  .plan-svg .chev{animation:chev 2.4s ease-in-out infinite}
  .plan-svg .halo{transform-box:fill-box;transform-origin:center;animation:halo 1.6s ease-in-out infinite}
  .gchip{animation:rise .5s ease backwards}.gchip:nth-child(2){animation-delay:.07s}.gchip:nth-child(3){animation-delay:.14s}.gchip:nth-child(4){animation-delay:.21s}.gchip:nth-child(5){animation-delay:.28s}.gchip:nth-child(6){animation-delay:.35s}
  .hero{background-size:200% 200%;animation:heroflow 18s ease-in-out infinite alternate}
  .hero .eyebrow,.hero h1,.hero p{animation:rise .7s ease both}.hero h1{animation-delay:.08s}.hero p{animation-delay:.16s}
  .stat{animation:rise .55s ease both}.stat:nth-child(2){animation-delay:.07s}.stat:nth-child(3){animation-delay:.14s}.stat:nth-child(4){animation-delay:.21s}
  .box{animation:rise .6s ease .28s both}.box+.box{animation-delay:.36s}
  .zn.sel polygon{animation:selp 1s ease 3}
  .row.hit{animation:hit 1.4s ease}
  details[open]>:not(summary){animation:rise .35s ease both}
}
@media(max-width:760px){.g2{grid-template-columns:1fr}.hint-m{display:inline}.hint-g{display:none}}
@media(max-width:560px){.row{grid-template-columns:auto 1fr}.row p{grid-column:1/-1}.stats{grid-template-columns:repeat(2,1fr)}.top-right .chip{display:none}}
@media print{*{animation:none!important}.topbar,.btn-x,.hint,.hint-m{display:none}.plan-svg{min-width:0}
  .hero,.zn polygon,.lg,.sev i{-webkit-print-color-adjust:exact;print-color-adjust:exact}details,.row,.plan-fig{break-inside:avoid}}
</style>
'''.replace("%%DUR%%", str(DUR)).replace("%%FL%%", fam_light).replace("%%FD%%", fam_dark).replace("%%FR%%", fam_rules)

def build(standalone):
    tpl = open(KIT, encoding="utf-8").read()
    head = tpl.split("</head>")[0]
    head = re.sub(r"<!-- DaranX document template.*?-->", "<!-- Category layout report — DaranX (summary first). -->", head, flags=re.S)
    head = head.replace("<title>{{عنوان سند}} — DaranX</title>",
                        f"<title>{META['name']} — طرح چیدمان دسته‌کالا — DaranX</title>\n<meta name=\"description\" content=\"طرح چیدمان دسته‌کالای فروشگاه بر پایهٔ تجهیزات موجود: نقشه، مسیر مشتری و جایگاه هر دسته.\">")
    head = head.replace('url("assets/Vazirmatn-VF.woff2")', 'url("' + uri(f"{ASSETS}/Vazirmatn-VF.woff2", "font/woff2") + '")')
    i = head.rfind("</style>")
    head = head[:i] + CSS.lstrip("\n") + head[i + len("</style>"):]
    names = {c: [n, fix, 'گروه ' + ZG[c].translate(FA) + ' · ' + GN[ZG[c]][2]] for c, f, p, n, e, fix in M.Z}
    import json
    body = ((BODY + SCRIPT).replace("%%BASE%%", uri(BASE_PNG, "image/png"))
                .replace("%%LOGO%%", uri(f"{ASSETS}/daranx-logo.svg", "image/svg+xml"))
                .replace("%%NAMES%%", json.dumps(names, ensure_ascii=False))
                .replace("%%TOGGLE%%", '<button class="theme-toggle" id="tt" aria-label="روشن/تیره">◐</button>' if standalone else "")
                .replace("%%THEMEJS%%", THEMEJS if standalone else ""))
    assert "%%" not in body and "{{" not in head
    if standalone:
        return head + "</head>\n" + body
    styles = "".join(re.findall(r"<style[^>]*>.*?</style>", head, flags=re.S))
    styles = styles.replace(':root:not([data-theme="light"]){', ':root:not([data-theme="light"]){color-scheme:dark;').replace(':root[data-theme="dark"]{', ':root[data-theme="dark"]{color-scheme:dark;')
    styles = styles.replace(".topbar{position:sticky;top:0;", ".topbar{position:sticky;top:env(safe-area-inset-top,0px);") + "<style>.dxroot{direction:rtl}</style>"
    b = body.split("<body>", 1)[1].split("</body>", 1)[0]
    return f"<title>{META['name']} — طرح چیدمان</title>\n" + styles + '\n<div class="dxroot" dir="rtl" lang="fa">\n' + b.strip() + '\n</div>\n'

sa = build(True); art = build(False)
open(f"{OUTDIR}/{META['id']}.html", "w", encoding="utf-8").write(sa)
open(f"{OUTDIR}/artifact/{META['id']}.html", "w", encoding="utf-8").write(art)
open(f"{OUTDIR}/{META['id']}-preview.html", "w", encoding="utf-8").write('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}</style></head><body>' + art + '</body></html>')
print("standalone", len(sa) // 1024, "KB; artifact", len(art) // 1024, "KB")
