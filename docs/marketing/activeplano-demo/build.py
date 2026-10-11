"""Build the ActivePlano cinematic product demo (index.html) from real screenshots.
Each scene = one screenshot + an optional zoom rectangle (fractions of the image) + a short caption.
Run: python3 build.py   (needs src/engine, src/vendor, assets/*.webp)"""
from pathlib import Path
import json, html

HERE = Path(__file__).parent
W, H = 1920, 920  # screenshot aspect

# act id, act title, scenes: (image, focus (x, y, w, h) as fractions or None, title, line)
ACTS = [
  ("map", "نقشهٔ فروشگاه", [
    ("02-projects", None, "هر فروشگاه، یک پروژه", "پیش‌نویس و منتشرشده، همه در یک صفحه."),
    ("03-plan", None, "نقشهٔ فروشگاه", "نقشه را بارگذاری می‌کنید؛ هر قفسه روی آن یک کد می‌گیرد."),
    ("03-plan", (.49, .46, .34, .25), "همهٔ قفسه‌ها روی یک نقشه", "هر قفسه کد خودش را دارد؛ از ورودی تا صندوق."),
    ("03-plan", (.21, .13, .26, .46), "هر قفسه، یک شناسنامه", "گروه کالا، تعداد کالا، SKU و وزن کل روی همان قفسه."),
    ("03-plan", (.30, 0, .32, .2), "چیدمان با Agent", "دستیار هوشمند برای کل فروشگاه چیدمان پیشنهاد می‌دهد."),
  ]),
  ("shelf", "قفسه و کالا", [
    ("04-fixtures", None, "کتابخانهٔ قفسه‌ها", "مدل و ابعاد هر قفسه و یخچال یک بار ثبت می‌شود."),
    ("05-products", (.15, .03, .6, .55), "کاتالوگ کالا", "بارکد، گروه کالا، قیمت، وزن و ابعاد هر کالا."),
    ("06-shelf-edit", None, "چیدمان قفسه، طبقه‌به‌طبقه", "کالاها را روی قفسه می‌چینید و همه‌چیز همان لحظه حساب می‌شود."),
    ("06-shelf-edit", (0, .08, .31, .82), "اندازهٔ هر طبقه به سانتی‌متر", "جای هر کالا دقیق است؛ نه حدودی."),
    ("06-shelf-edit", (.31, .07, .36, .4), "همه‌چیز شمرده می‌شود", "تعداد نما، SKU، ارزش و وزن هر طبقه."),
    ("06-shelf-edit", (.65, .64, .18, .34), "کالای مکمل", "نرم‌افزار کالای مکمل را هم پیشنهاد می‌دهد."),
  ]),
  ("run", "اجرا و کنترل", [
    ("07-needed", (.15, 0, .62, .6), "فهرست کالای لازم", "تعداد، نما، قفسه‌ها و هزینهٔ تخمینی خرید هر کالا؛ با خروجی اکسل."),
    ("08-sheet", None, "برگهٔ چیدمان، آمادهٔ چاپ", "عکس قفسه، فهرست کالا و جای قفسه روی نقشه."),
    ("08-sheet", (.49, .69, .2, .16), "یک اسکن، وضعیت اجرا", "QR روی برگه نشان می‌دهد قفسه چیده شده یا نه."),
    ("08-sheet", (.49, .84, .2, .16), "سه امضا، یک مسئول", "طراح، سرپرست و مسئول چیدمان پای برگه امضا می‌کنند."),
  ]),
  ("insight", "تحلیل", [
    ("09-analysis1", None, "همهٔ پروژه‌ها در یک داشبورد", "ترکیب گروه‌های کالا، ارزش و پرچیدمان‌ترین کالاها."),
    ("09-analysis1", (.15, .15, .61, .16), "عددهای کلیدی", "تعداد پروژه، تجهیز، کالا و ارزش ریالی چیده‌شده."),
    ("10-analysis2", (.15, .03, .3, .38), "جا در برابر ارزش", "هر گروه کالا چقدر از قفسه را گرفته و چقدر ارزش دارد."),
  ]),
]

def esc(s): return html.escape(s, quote=True)

parts = []
cfg = {}
for ai, (aid, atitle, scenes) in enumerate(ACTS):
    imgs, order = [], []
    for img, *_ in scenes:
        if img not in order: order.append(img)
    shots = "".join(f'<img class="shot" data-img="{im}" src="assets/{im}.webp" width="{W}" height="{H}" alt="" loading="{"eager" if ai == 0 else "lazy"}" decoding="async">' for im in order)
    caps = "".join(f'<div class="cap" data-s="{i}"><p class="cap-t">{esc(t)}</p><p>{esc(l)}</p></div>' for i, (_, _, t, l) in enumerate(scenes))
    n = len(scenes)
    parts.append(f'''<section class="story" id="{aid}" style="--len:{(n + 1) * 100}svh" aria-label="{esc(atitle)}">
  <div class="stage">
    <div class="chapter" aria-hidden="true"><span>{ai + 1}</span>{esc(atitle)}</div>
    <div class="screen scene"><div class="chrome" aria-hidden="true"><i></i><i></i><i></i><span>app.activeplano.com</span></div><div class="view"><div class="cam">{shots}<div class="ring"></div></div></div></div>
    <div class="caps">{caps}</div>
  </div>
</section>''')
    cfg[aid] = [{"img": im, "f": f} for im, f, _, _ in scenes]

body = "\n".join(parts)
css = (HERE / "src/engine/base.css").read_text()
site_css = r'''
@font-face{font-family:"Vazirmatn";src:url("assets/Vazirmatn-VF.woff2") format("woff2");font-weight:100 900;font-display:swap}
:root{--st-bg:#06201A;--st-surface:#0B332A;--st-ink:#E8F5F0;--st-ink-2:#A9CDBF;--st-ink-3:#7FA698;--st-line:rgba(205,242,235,.14);--st-line-2:rgba(205,242,235,.26);
  --brand:#5DEBAF;--brand-ink:#06201A;--bg:#06201A;--surface:#0B332A;--ink:#E8F5F0;--ink-2:#A9CDBF;--ink-3:#7FA698;--line:rgba(205,242,235,.14);--line-2:rgba(205,242,235,.26);
  --accent:#5DEBAF;--accent-ink:#06201A;--accent-text:#5DEBAF;--font:"Vazirmatn",system-ui,sans-serif}
body{background:var(--st-bg)}
.topbar{background:color-mix(in srgb,var(--st-bg) 80%,transparent);border-bottom-color:var(--st-line)}
.wm{direction:ltr;color:var(--st-ink)}.wm b{color:var(--brand)}
/* screen: a browser window the camera moves inside */
.screen{inset:auto;top:calc(50% + var(--nav-h) / 2);transform:translateY(-50%);inset-inline-end:clamp(1rem,3vw,3rem);width:min(66vw,calc((100svh - var(--nav-h) - 150px) * 2.087));height:auto;
  display:block;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 40px 100px rgba(0,0,0,.55),0 0 0 1px var(--st-line-2)}
.chrome{height:30px;flex:none;display:flex;align-items:center;gap:6px;padding:0 12px;background:#E8EFEC;direction:ltr}
.chrome i{width:10px;height:10px;border-radius:50%;background:#C9D6D1}.chrome span{margin-inline-start:12px;font:600 11px/1 system-ui;color:#6B8078;background:#fff;border-radius:6px;padding:4px 10px}
.view{position:relative;overflow:hidden;aspect-ratio:1920/920}
.cam{position:absolute;left:0;top:0;right:auto;bottom:auto;width:100%;height:100%;transform-origin:0 0;transition:transform 1100ms var(--ease-in-out);will-change:transform}
.shot{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top;opacity:0;transition:opacity 500ms ease}
.shot.on{opacity:1}
.ring{display:none;position:absolute;border:3px solid var(--brand);border-radius:10px;box-shadow:0 0 0 9999px rgba(6,32,26,.0);opacity:0;transition:opacity 400ms ease 700ms}
.story[data-zoom="1"] .ring{opacity:0}
.chapter{position:absolute;z-index:var(--z-hud);top:calc(var(--nav-h) + 10px);inset-inline-start:var(--cx);display:flex;align-items:center;gap:.6rem;font-weight:800;color:var(--st-ink-2);font-size:.95rem}
.chapter span{display:grid;place-items:center;width:1.7rem;height:1.7rem;border-radius:50%;background:var(--brand);color:var(--brand-ink);font-size:.85rem}
.cap{width:min(330px,26vw)}
.hero-sec{min-height:100svh;display:grid;place-items:center;text-align:center;padding:calc(var(--nav-h) + 2rem) var(--gutter) 3rem;
  background:radial-gradient(60% 50% at 50% 40%,rgba(93,235,175,.12),transparent 70%),var(--st-bg)}
.hero-sec h1{color:var(--st-ink)}.hero-sec h1 em{font-style:normal;color:var(--brand)}
.hero-sec p{color:var(--st-ink-2);font-size:1.15rem;margin-top:1rem}
.hero-sec .hint{margin-top:2.4rem;font-size:.9rem;color:var(--st-ink-3)}
.hero-shot{margin:2.2rem auto 0;width:min(880px,90vw);border-radius:14px;overflow:hidden;box-shadow:0 40px 100px rgba(0,0,0,.55),0 0 0 1px var(--st-line-2)}
.hero-shot img{display:block;width:100%;height:auto}
.end{min-height:100svh;display:grid;place-items:center;text-align:center;padding:var(--sp) var(--gutter)}
.end h2{color:var(--st-ink)}.end p{color:var(--st-ink-2);margin-top:1rem}
.end .acts{display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap;margin-top:2rem}
.need{background:#FFF1D6;color:#6E4300;border:1px dashed #D99A2B;border-radius:6px;padding:0 .4em;font-weight:700}

.meet{width:min(1040px,100%);display:grid;grid-template-columns:1fr 1.25fr;gap:clamp(1.5rem,4vw,3rem);align-items:start;text-align:start}
.meet-head p{margin-top:.8rem}.meet-head a{color:var(--brand);font-weight:800}
.end .form{background:var(--st-surface);border:1px solid var(--st-line);border-radius:20px;padding:clamp(1.1rem,3vw,1.8rem)}
.field input{background:#F3F8F5;color:#0E2A23;border-color:transparent}
.field label,.meet-type legend{color:var(--st-ink)}
.meet-type{grid-column:1/-1;border:0;padding:0;margin:0;display:flex;gap:.6rem;flex-wrap:wrap;align-items:center}
.meet-type legend{font-weight:800;font-size:.92rem;margin-bottom:.4rem;width:100%}
.meet-type label{display:inline-flex;align-items:center;gap:.45rem;min-height:44px;padding:.4rem 1rem;border:1px solid var(--st-line-2);border-radius:999px;cursor:pointer;color:var(--st-ink);font-weight:700}
.meet-type label:has(input:checked){background:var(--brand);color:var(--brand-ink);border-color:var(--brand)}
.meet-type input{accent-color:var(--brand-ink);margin:0}
.form-ok h3{color:var(--st-ink)}.form-msg{color:var(--st-ink-2)}
.field .err{color:#FFB4A8}
@media(max-width:860px){.meet{grid-template-columns:1fr}}
@media(max-width:860px),(max-aspect-ratio:21/20){
  .screen{top:calc(var(--nav-h) + 56px);transform:none;inset-inline:.8rem;width:auto}
  .view{aspect-ratio:auto;height:min(58svh,calc((100vw - 1.6rem) * 1.3))}
  .chrome{height:22px}.chrome span{display:none}
  .cap{width:auto}
  .chapter{top:calc(var(--nav-h) + 16px)}
}
body.no-story .screen,html:not(.js) .screen{position:relative;inset:auto;transform:none;width:100%;order:2}
body.no-story .cam,html:not(.js) .cam{position:relative;transform:none!important;display:grid;gap:1rem}
body.no-story .shot,html:not(.js) .shot{position:relative;opacity:1;height:auto}
body.no-story .view,html:not(.js) .view{aspect-ratio:auto}
body.no-story .chapter,html:not(.js) .chapter{position:relative;inset:auto;order:0}
'''
scenes_js = '''(function(){
var E=StoryEngine, CFG=%s;
Object.keys(CFG).forEach(function(id){
  var sec=document.getElementById(id); if(!sec) return;
  var view=sec.querySelector('.view'), cam=sec.querySelector('.cam'), ring=sec.querySelector('.ring'), shots=[].slice.call(sec.querySelectorAll('.shot')), S=CFG[id], cur=0;
  var DEF=[.1,0,.8,1];  /* phone: default framing = main content, sidebar cropped */
  function place(){
    var s=S[cur], vw=view.clientWidth, vh=view.clientHeight, iw=Math.max(vw, vh*1920/920), ih=iw*920/1920, narrow=iw>vw+2;
    cam.style.width=iw+'px'; cam.style.height=ih+'px';
    shots.forEach(function(im){ im.classList.toggle('on', im.getAttribute('data-img')===s.img); });
    var f=s.f||(narrow?DEF:null);
    if(!f){ cam.style.transform='translate(0px,0px) scale(1)'; return; }
    var k=Math.max(1, Math.min(3.2, .92*vw/(f[2]*iw), .92*vh/(f[3]*ih)));
    var tx=vw/2-(f[0]+f[2]/2)*iw*k, ty=vh/2-(f[1]+f[3]/2)*ih*k;
    tx=Math.min(0, Math.max(vw-iw*k, tx)); ty=Math.min(0, Math.max(vh-ih*k, ty));
    cam.style.transform='translate('+tx.toFixed(1)+'px,'+ty.toFixed(1)+'px) scale('+k.toFixed(3)+')';
  }
  var bounds=[]; for(var i=1;i<S.length;i++) bounds.push(i/S.length);
  E.act(id, bounds, {
    layout:function(){ place(); },
    scene:function(sc){ cur=sc; place(); },
    reset:function(){ cam.removeAttribute('style'); ring.removeAttribute('style'); shots.forEach(function(im){ im.classList.remove('on'); }); }
  });
});
E.start();
})();''' % json.dumps(cfg)

page = f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ActivePlano | دموی نرم‌افزار پلانوگرام</title>
<meta name="description" content="دموی تصویری ActivePlano: از نقشهٔ فروشگاه تا چیدمان قفسه، برگهٔ چیدمان با QR و تحلیل؛ با تصویرهای واقعی نرم‌افزار.">
<meta name="robots" content="noindex,follow">
<meta name="theme-color" content="#06201A">
<link rel="preload" href="assets/Vazirmatn-VF.woff2" as="font" type="font/woff2" crossorigin>
<style>
{css}
{site_css}
</style>
<script>document.documentElement.classList.add('js')</script>
</head>
<body>
<header class="topbar ondark" id="topbar"><div class="wrap">
  <a href="#intro" class="wm">Active<b>Plano</b></a>
  <nav class="nav" aria-label="بخش‌ها"><a href="#map">نقشه</a><a href="#shelf">قفسه و کالا</a><a href="#run">اجرا</a><a href="#insight">تحلیل</a></nav>
  <a class="btn btn-brand btn-sm" href="#contact">جلسهٔ دمو</a>
</div><div class="progress" aria-hidden="true"><i id="prog"></i></div></header>
<main>
<section class="hero-sec on-dark" id="intro">
  <div>
    <h1>ActivePlano <em>از نزدیک</em></h1>
    <p>از نقشهٔ فروشگاه تا قفسهٔ کنترل‌شده؛ با تصویرهای واقعی نرم‌افزار.</p>
    <div class="hero-shot"><img src="assets/01-login.webp" width="{W}" height="{H}" alt="صفحهٔ ورود ActivePlano"></div>
    <p class="hint">اسکرول کنید؛ هر حرکت، یک قدم.</p>
  </div>
</section>
{body}
<section class="end on-dark" id="contact">
  <div class="meet">
    <div class="meet-head">
      <h2>ActivePlano را روی فروشگاه خودتان ببینید</h2>
      <p>یک جلسهٔ حضوری یا آنلاین می‌گذاریم و چیدمان یکی از قفسه‌های شما را با هم می‌سازیم.</p>
      <p>یا همین حالا تماس بگیرید: <a dir="ltr" href="tel:+982188977021">۰۲۱-۸۸۹۷۷۰۲۱-۳۰</a></p>
    </div>
    <form class="form" id="demoForm" data-endpoint="../api/lead.php" novalidate>
      <div class="errsum" id="errsum" role="alert" tabindex="-1" aria-labelledby="errtitle"><h3 id="errtitle">برای ارسال، این موارد را اصلاح کنید</h3><ul id="errlist"></ul></div>
      <div class="fields">
        <fieldset class="field meet-type"><legend>نوع جلسه</legend>
          <label><input type="radio" name="meeting" value="online" checked> آنلاین</label>
          <label><input type="radio" name="meeting" value="in-person"> حضوری</label>
        </fieldset>
        <div class="field"><label for="f-name">نام و نام خانوادگی</label><input id="f-name" name="name" autocomplete="name" required aria-describedby="err-name"><p class="err" id="err-name"></p></div>
        <div class="field"><label for="f-company">نام فروشگاه یا شرکت</label><input id="f-company" name="company" autocomplete="organization" required aria-describedby="err-company"><p class="err" id="err-company"></p></div>
        <div class="field"><label for="f-phone">شمارهٔ تماس</label><input id="f-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" dir="ltr" required aria-describedby="err-phone"><p class="err" id="err-phone"></p></div>
        <div class="field"><label for="f-city">شهر (اختیاری)</label><input id="f-city" name="city" autocomplete="address-level2"></div>
        <div class="field"><label for="f-branches">تعداد شعبه (اختیاری)</label><input id="f-branches" name="branches" inputmode="numeric" aria-describedby="err-branches"><p class="err" id="err-branches"></p></div>
        <div class="field"><label for="f-time">زمان مناسب برای شما (اختیاری)</label><input id="f-time" name="time" placeholder="مثلاً شنبه‌ها صبح"></div>
        <input type="hidden" name="source" value="demo-meeting"><input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
        <button class="btn btn-brand" id="demoBtn" type="submit">درخواست جلسه</button>
        <p class="form-msg" id="formMsg" role="status" aria-live="polite"></p>
      </div>
      <div class="form-ok" role="status"><h3 id="okTitle">درخواست شما ثبت شد</h3><p>برای هماهنگی زمان جلسه به‌زودی با شما تماس می‌گیریم.</p></div>
    </form>
  </div>
</section>
</main>
<script>{(HERE / "src/vendor/gsap.min.js").read_text()}</script>
<script>{(HERE / "src/vendor/ScrollTrigger.min.js").read_text()}</script>
<script>{(HERE / "src/engine/story-engine.js").read_text()}</script>
<script>{scenes_js}</script>
<script>{(HERE / "src/engine/ui.js").read_text()}</script>
</body>
</html>
'''
(HERE / "index.html").write_text(page, encoding="utf-8")
print("built", len(page) // 1024, "KB,", sum(len(s) for _, _, s in ACTS), "scenes")
