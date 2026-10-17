#!/usr/bin/env python3
"""Turn link_calc.py results into a cinematic, self-contained Persian (RTL) HTML report.

Usage:
    python3 build_report.py results.json -o report.html [--prices prices.json]

prices.json (optional, filled from a live web search, never invented):
{ "date": "1405/07/25",
  "items": { "mikrotik-lhg5ac": {"price": "۸٬۹۰۰٬۰۰۰ تومان", "unit": "هر عدد", "source": "https://torob.com/...", "shop": "ترب"} } }
Models without a price show a visible [NEED: قیمت روز] chip.

Story (cinematic-story-site engine, one gesture = one scene):
  Act 1  map      : the sites appear -> link lines draw with distance -> antenna directions
  Act 2+ profile  : terrain -> obstacles -> earth bulge -> masts rise -> Fresnel zone clears (one act per link, max 4)
  Act    budget   : transmit power -> path loss -> received signal -> fade margin (main link, balanced pick)
  Sections        : equipment tiers with prices, PtMP sectors, installation sheet, field checklist, plain summary
"""
import argparse, base64, html, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / 'assets'
FA_DIGITS = str.maketrans('0123456789.-', '۰۱۲۳۴۵۶۷۸۹٫−')
TIER_FA = {'economy': 'اقتصادی', 'balanced': 'بهینه (پیشنهاد اصلی)', 'pro': 'حرفه‌ای'}
TIER_WHY = {'economy': 'کمترین هزینه که نیاز را برآورده می‌کند.',
            'balanced': 'بهترین نسبت کارایی به قیمت با حاشیهٔ امن.',
            'pro': 'بیشترین ظرفیت و پایداری برای رشد آینده.'}


def fa(x, nd=None):
    if isinstance(x, float) and nd is not None:
        x = f'{x:.{nd}f}'
        if '.' in x:
            x = x.rstrip('0').rstrip('.')
    return str(x).translate(FA_DIGITS)


def km(m):
    return fa(m / 1000, 2) + ' کیلومتر' if m >= 1000 else fa(round(m)) + ' متر'


def e(s):
    return html.escape(str(s), quote=True)


def need(text):
    return f'<span class="need">[NEED: {e(text)}]</span>'


# ------------------------------------------------------------------ scene CSS helpers
def scene_css(act, n_scenes, hidden_rules):
    """Elements with class s{k} are hidden until scene k, then stay visible; .draw lines draw; .grow masts rise."""
    p = 'html.js body:not(.no-story) '
    out = []
    for k in range(1, n_scenes):
        on = ','.join(f'{p}#{act}[data-sc="{j}"] .s{k}' for j in range(k, n_scenes))
        out.append(f'{p}#{act} .s{k}{{opacity:0}}')
        out.append(f'{p}#{act} .s{k}.draw{{opacity:1;stroke-dashoffset:1}}')
        out.append(f'{p}#{act} .s{k}.grow{{opacity:1;transform:scaleY(0)}}')
        out.append(f'{on}{{opacity:1;stroke-dashoffset:0;transform:none}}')
    return '\n'.join(out + hidden_rules)


# ------------------------------------------------------------------ act 1: map
def map_svg(R):
    sites = R['sites']
    lat0 = sum(s['lat'] for s in sites) / len(sites)
    lon0 = sum(s['lon'] for s in sites) / len(sites)
    xy = {s['id']: ((s['lon'] - lon0) * math.cos(math.radians(lat0)) * 111320, -(s['lat'] - lat0) * 110540) for s in sites}
    span = max(max(abs(v[0]) for v in xy.values()) / 300, max(abs(v[1]) for v in xy.values()) / 210, 1e-9)
    P = {k: (v[0] / span, v[1] / span) for k, v in xy.items()}   # fits in a 600 x 420 box around (0,0)
    g = []
    # faint survey grid around the area (world feel)
    for i in range(-12, 13):
        g.append(f'<line class="grid" x1="{i*80}" y1="-700" x2="{i*80}" y2="700"/>')
        g.append(f'<line class="grid" x1="-1000" y1="{i*80}" x2="1000" y2="{i*80}"/>')
    # links
    labelled = {}
    for l in R['links']:
        (x1, y1), (x2, y2) = P[l['a']], P[l['b']]
        cls = 'link' if l['feasible'] else 'link bad'
        g.append(f'<line class="{cls} s2 draw" pathLength="1" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ln = math.hypot(x2 - x1, y2 - y1) or 1
        nx, ny = -(y2 - y1) / ln, (x2 - x1) / ln          # unit normal; push the label to the upper side
        if ny > 0:
            nx, ny = -nx, -ny
        d = l['distance_m']
        lab = f'{d/1000:.2f} km' if d >= 1000 else f'{d:.0f} m'
        g.append(f'<text class="dist s2" x="{mx+nx*26:.1f}" y="{my+ny*26+8:.1f}" text-anchor="middle" direction="ltr">{lab}</text>')
        # azimuth ticks at both ends
        for sid, az, (ox, oy) in ((l['a'], l['azimuth_ab'], (x1, y1)), (l['b'], l['azimuth_ba'], (x2, y2))):
            # nearly parallel links from one site would stack their bearing labels: label only the first
            if any(abs((az - q + 180) % 360 - 180) < 10 for q in labelled.setdefault(sid, [])):
                continue
            labelled[sid].append(az)
            r = math.radians(az)
            tx, ty = ox + math.sin(r) * min(70, ln * .3), oy - math.cos(r) * min(70, ln * .3)
            g.append(f'<line class="az s3 draw" pathLength="1" x1="{ox:.1f}" y1="{oy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>')
            # beside the link, on the side opposite the distance label, a short way from the site
            al = min(62, ln * .28)
            lx, ly = ox + math.sin(r) * al - nx * 24, oy - math.cos(r) * al - ny * 24 + 6
            g.append(f'<text class="azl s3" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" direction="ltr">{az:.0f}°</text>')
    for s in sites:
        x, y = P[s['id']]
        hub = ' hub' if R.get('hub') == s['id'] else ''
        # put the name on the side away from this site's links, so it never sits on a line or bearing label
        vx = vy = 0.0
        for l in R['links']:
            if s['id'] in (l['a'], l['b']):
                ox, oy = P[l['b'] if l['a'] == s['id'] else l['a']]
                n = math.hypot(ox - x, oy - y) or 1
                vx, vy = vx + (ox - x) / n, vy + (oy - y) / n
        n = math.hypot(vx, vy)
        ux, uy = (-vx / n, -vy / n) if n > .2 else (0, 1)
        lx, ly = x + ux * 36, y + uy * 40 + 9
        anchor = 'end' if ux < -.4 else 'start' if ux > .4 else 'middle'
        g.append(f'<g class="site{hub}"><circle class="halo s1" cx="{x:.1f}" cy="{y:.1f}" r="26"/>'
                 f'<circle class="pin" cx="{x:.1f}" cy="{y:.1f}" r="9"/>'
                 f'<text class="sname s1" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" direction="ltr">{e(s.get("name", s["id"]))}</text></g>')
    return '\n'.join(g)


# ------------------------------------------------------------------ act 2: profile
def profile_svg(l, sites):
    pr = l['profile']
    d, gnd, ob, bul, fr = pr['d'], pr['ground'], pr['obstacle'], pr['bulge'], pr['fresnel']
    D = d[-1] or 1
    ok = l['feasible']
    hA = l.get('antenna_asl_a_m', pr['base_a'])
    hB = l.get('antenna_asl_b_m', pr['base_b'])
    line = [hA + (hB - hA) * x / D for x in d]
    lo = min(gnd) - 4
    hi = max(max(hA, hB), max(line[i] + fr[i] for i in range(len(d))), max(gnd[i] + ob[i] + bul[i] for i in range(len(d)))) + 6
    X0, X1, Y0, Y1 = 70, 930, 60, 520
    X = lambda x: X0 + (X1 - X0) * x / D
    Y = lambda h: Y1 - (Y1 - Y0) * (h - lo) / (hi - lo)
    pts = lambda arr: ' '.join(f'{X(d[i]):.1f},{Y(arr[i]):.1f}' for i in range(len(d)))
    g = []
    # axis ticks (LTR numbers)
    step = 10 ** math.floor(math.log10(max(hi - lo, 1)))
    if (hi - lo) / step < 4:
        step /= 2
    h = math.ceil(lo / step) * step
    while h <= hi:
        g.append(f'<line class="tick" x1="{X0}" x2="{X1}" y1="{Y(h):.1f}" y2="{Y(h):.1f}"/><text class="tl" x="{X0-10}" y="{Y(h)+5:.1f}" text-anchor="end" direction="ltr">{h:g} m</text>')
        h += step
    for i in range(0, 6):
        x = D * i / 5
        g.append(f'<text class="tl" x="{X(x):.1f}" y="{Y1+30}" text-anchor="middle" direction="ltr">{x/1000:.2f} km</text>')
    # ground (+ bulge appears at scene 3 as a lifted outline)
    ground_poly = f'{X0},{Y1+2} ' + pts(gnd) + f' {X1},{Y1+2}'
    g.append(f'<polygon class="ground" points="{ground_poly}"/>')
    lifted = [gnd[i] + bul[i] for i in range(len(d))]
    g.append(f'<polyline class="bulge s3 draw" pathLength="1" points="{pts(lifted)}"/>')
    # obstacles: clutter band + named obstacles (scene 2)
    clutter = [gnd[i] + bul[i] + ob[i] for i in range(len(d))]
    if max(ob) > 0:
        poly = pts(clutter) + ' ' + ' '.join(f'{X(d[i]):.1f},{Y(lifted[i]):.1f}' for i in reversed(range(len(d))))
        g.append(f'<polygon class="clutter s2" points="{poly}"/>')
    for o in l.get('obstacles', []):
        i = min(range(len(d)), key=lambda j: abs(d[j] - o['at_m']))
        top = gnd[i] + bul[i] + o['height_m']
        g.append(f'<g class="s2"><rect class="obst" x="{X(d[i])-9:.1f}" y="{Y(top):.1f}" width="18" height="{Y(gnd[i])-Y(top):.1f}"/>'
                 f'<text class="olab" x="{X(d[i]):.1f}" y="{Y(top)-12:.1f}" text-anchor="middle">{e(o["name"])}</text></g>')
    # Fresnel zone (scene 5): full F1 and the 60 % core
    up = [line[i] + fr[i] for i in range(len(d))]
    dn = [line[i] - fr[i] for i in range(len(d))]
    poly = pts(up) + ' ' + ' '.join(f'{X(d[i]):.1f},{Y(dn[i]):.1f}' for i in reversed(range(len(d))))
    g.append(f'<polygon class="fresnel s5" points="{poly}"/>')
    c = l.get('clearance_target', 0.6)
    up6 = [line[i] + c * fr[i] for i in range(len(d))]
    dn6 = [line[i] - c * fr[i] for i in range(len(d))]
    poly6 = pts(up6) + ' ' + ' '.join(f'{X(d[i]):.1f},{Y(dn6[i]):.1f}' for i in reversed(range(len(d))))
    g.append(f'<polygon class="fresnel6 s5" points="{poly6}"/>')
    g.append(f'<line class="los s5 draw" pathLength="1" x1="{X(0):.1f}" y1="{Y(hA):.1f}" x2="{X(D):.1f}" y2="{Y(hB):.1f}"/>')
    # buildings + masts at both ends (masts rise in scene 4)
    for x, base_g, base, ant, sid in ((0, gnd[0], pr['base_a'], hA, l['a']), (D, gnd[-1], pr['base_b'], hB, l['b'])):
        bx = X(x) - (0 if x == 0 else 30)
        g.append(f'<rect class="bld" x="{bx:.1f}" y="{Y(base):.1f}" width="30" height="{max(Y(base_g)-Y(base),1):.1f}"/>')
        mx = X(x) + (15 if x == 0 else -15)
        g.append(f'<line class="mast s4 grow" x1="{mx:.1f}" y1="{Y(base):.1f}" x2="{mx:.1f}" y2="{Y(ant):.1f}"/>')
        g.append(f'<circle class="ant s4" cx="{mx:.1f}" cy="{Y(ant):.1f}" r="7"/>')
        g.append(f'<text class="slab s4" x="{min(max(mx, X0 + 70), X1 - 70):.1f}" y="{Y(ant)-18:.1f}" text-anchor="middle">{e(sites[sid].get("name", sid))}</text>')
    if ok:
        ci = min(range(len(d)), key=lambda j: abs(d[j] - l['critical_point_m']))
        g.append(f'<circle class="crit s5" cx="{X(d[ci]):.1f}" cy="{Y(clutter[ci]):.1f}" r="8"/>')
        g.append(f'<text class="clab s5" x="{X(d[ci]):.1f}" y="{Y(clutter[ci])+30:.1f}" text-anchor="middle" direction="ltr">{l["min_clearance_pct"]}% F1</text>')
    return '\n'.join(g)


# ------------------------------------------------------------------ act 3: budget
def budget_svg(b, radio, target):
    tx, G = b['tx_dbm'], radio['gain_dbi']
    eirp = b['eirp_dbm']
    after_path = eirp - b['loss_db']
    rx, sens = b['rx_dbm'], b['sens_dbm']
    lo, hi = min(sens - 10, after_path - 5), eirp + 8
    X0, Y0, Y1 = 90, 50, 520
    Y = lambda v: Y0 + (Y1 - Y0) * (hi - v) / (hi - lo)
    cols = [('Tx', 0, tx, 's1 pos', f'{tx:g} dBm'), ('+ آنتن', tx, eirp, 's1 pos', f'+{G:g} dB'),
            ('− مسیر', eirp, after_path, 's2 neg', f'−{b["loss_db"]:g} dB'), ('+ آنتن', after_path, rx, 's3 pos', f'+{G:g} dB')]
    g = []
    for v in range(int(math.ceil(lo / 10) * 10), int(hi) + 1, 10):
        g.append(f'<line class="tick" x1="{X0}" x2="960" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="tl" x="{X0-10}" y="{Y(v)+5:.1f}" text-anchor="end" direction="ltr">{v} dBm</text>')
    w, gap = 140, 50
    for i, (name, a, bb, cls, lab) in enumerate(cols):
        x = X0 + 40 + i * (w + gap)
        top, bot = (Y(max(a, bb)), Y(min(a, bb))) if i else (Y(tx), Y(lo))
        g.append(f'<g class="{cls.split()[0]}"><rect class="bar {cls.split()[1]}" x="{x}" y="{top:.1f}" width="{w}" height="{max(bot-top,2):.1f}" rx="6"/>'
                 f'<text class="bl" x="{x+w/2}" y="{Y1+30}" text-anchor="middle">{name}</text>'
                 f'<text class="bv" x="{x+w/2}" y="{top-10:.1f}" text-anchor="middle" direction="ltr">{lab}</text></g>')
        if i < 3:
            nxt = cols[i + 1][1]
            g.append(f'<line class="conn {cols[i+1][3].split()[0]}" x1="{x+w}" x2="{x+w+gap}" y1="{Y(nxt):.1f}" y2="{Y(nxt):.1f}"/>')
    xs = X0 + 40 + 3 * (w + gap)
    g.append(f'<g class="s4"><line class="sens" x1="{X0}" x2="960" y1="{Y(sens):.1f}" y2="{Y(sens):.1f}"/>'
             f'<text class="sl" x="{X0+8}" y="{Y(sens)+22:.1f}" direction="ltr">sensitivity {sens} dBm ({b["modulation"]}, {b["width_mhz"]} MHz)</text>'
             f'<line class="mbr" x1="{xs+w+22}" x2="{xs+w+22}" y1="{Y(rx):.1f}" y2="{Y(sens):.1f}"/>'
             f'<text class="ml" x="{xs+w+30}" y="{(Y(rx)+Y(sens))/2+6:.1f}" direction="ltr">{b["margin_db"]:g} dB</text></g>')
    return '\n'.join(g)


# ------------------------------------------------------------------ page
def build(R, prices):
    sites = {s['id']: s for s in R['sites']}
    cat = R['catalog']
    links = R['links']
    L0 = links[0]
    name = lambda sid: sites[sid].get('name', sid)
    P = (prices or {}).get('items', {})
    pdate = (prices or {}).get('date')
    n_sites = len(sites)
    total_km = sum(l['distance_m'] for l in links)
    feasible_all = all(l['feasible'] for l in links)

    css_rules, acts_js, story = [], [], []

    # ---------------- act 1
    if n_sites == 2:
        h1 = f'{e(name(L0["a"]))} تا {e(name(L0["b"]))}، <em>{km(L0["distance_m"])}</em>'
    else:
        h1 = f'{fa(n_sites)} نقطه، <em>{fa(len(links))} لینک رادیویی</em>'
    verdict = ('هر لینک با ارتفاع دکل مشخص و تجهیزات موجود در بازار ایران برقرار می‌شود.' if feasible_all
               else 'بخشی از مسیرها دید مستقیم ندارند و به نقطهٔ واسط یا سازهٔ بلندتر نیاز دارند.')
    az_line = '؛ '.join(f'{e(name(l["a"]))} رو به {fa(round(l["azimuth_ab"]))}° ({l["compass_ab"]})' for l in links[:3])
    dist_line = '؛ '.join(f'{e(name(l["a"]))} تا {e(name(l["b"]))}: {km(l["distance_m"])}' for l in links[:3])
    story.append(f'''
<section class="story" id="map" data-hero style="--len:500svh" aria-label="نقشهٔ نقاط و مسیر لینک‌ها">
  <div class="stage">
    <svg class="scene" id="world" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><g id="cam" class="cam">{map_svg(R)}</g></svg>
    <div class="vignette" aria-hidden="true"></div>
    <div class="story-copy" id="storyCopy">
      <span class="badge">طرح لینک رادیویی · {fa(R["freq_ghz"])} گیگاهرتز</span>
      <h1>{h1}</h1>
      <p class="verdict">{verdict}</p>
      <div class="hero-actions"><a class="btn btn-brand" href="#gear">تجهیزات پیشنهادی</a><a class="btn btn-ghost" href="#install">برگهٔ نصب</a></div>
    </div>
    <div class="caps">
      <div class="cap" data-s="1"><p class="cap-t">{fa(n_sites)} نقطه روی نقشه</p><p>مختصات از لینک‌های شما خوانده شد.</p></div>
      <div class="cap" data-s="2"><p class="cap-t">فاصلهٔ مستقیم</p><p>{dist_line}</p></div>
      <div class="cap" data-s="3"><p class="cap-t">جهت آنتن‌ها</p><p>{az_line}</p></div>
    </div>
  </div>
</section>''')
    css_rules.append(scene_css('map', 4, ['html.js body:not(.no-story) #map:not([data-sc="0"]) .story-copy{opacity:0;visibility:hidden}',
                                          '#map .story-copy{transition:opacity 260ms var(--ease-out),visibility 0s linear 260ms}']))
    acts_js.append("E.act('map',[.2,.45,.72],{frame:mapFrame,reset:function(){cam.removeAttribute('transform')}},[0,.32,.58,1]);")

    # ---------------- profile acts
    for i, l in enumerate(links[:4]):
        aid = f'p{i}'
        A, B = name(l['a']), name(l['b'])
        obs = '، '.join(f'{e(o["name"])} {fa(o["height_m"])} متر' for o in l['obstacles'])
        obs_line = (f'ساختمان‌ها حدود {fa(l["clutter_m"])} متر' if l['clutter_m'] else 'بدون پوشش ساختمانی عمومی') + (f'؛ {obs}.' if obs else '.')
        if l['feasible']:
            mast_line = f'{e(A)}: {fa(l["mast_a_m"])} متر، {e(B)}: {fa(l["mast_b_m"])} متر روی بام.'
            fres_t = 'منطقهٔ فرنل آزاد است'
            fres_l = f'دست‌کم {fa(l["min_clearance_pct"])}٪ منطقهٔ فرنل اول خالی است؛ هدف {fa(round(l["clearance_target"]*100))}٪.'
        else:
            mast_line = 'حتی با بلندترین دکل مجاز، مسیر باز نمی‌شود.'
            fres_t = 'مسیر بسته است'
            fres_l = 'یک نقطهٔ واسط (رله) یا سازهٔ بلندتر لازم است.'
        warn = '' if l['terrain_ok'] else f' {need("دادهٔ ارتفاع زمین دریافت نشد")}'
        story.append(f'''
<section class="story" id="{aid}" style="--len:600svh" aria-label="پروفایل مسیر {e(A)} تا {e(B)}">
  <div class="stage">
    <div class="scene side" aria-hidden="true"><svg class="prof" viewBox="0 0 1000 580" preserveAspectRatio="xMidYMid meet">{profile_svg(l, sites)}</svg></div>
    <div class="caps">
      <div class="cap lead" data-s="0"><h2>مسیر {e(A)} تا {e(B)} از کنار</h2><p>زمین، موانع و انحنای زمین در طول {km(l["distance_m"])}.{warn}</p></div>
      <div class="cap" data-s="1"><h3>ارتفاع زمین</h3><p>{e(A)} {fa(l["ground_a_m"], 1)} متر، {e(B)} {fa(l["ground_b_m"], 1)} متر؛ اختلاف {fa(abs(l["ground_diff_m"]), 1)} متر.</p></div>
      <div class="cap" data-s="2"><h3>موانع مسیر</h3><p>{obs_line}</p></div>
      <div class="cap" data-s="3"><h3>انحنای زمین</h3><p>وسط مسیر، زمین {fa(l["max_bulge_m"], 1)} متر بالا می‌آید و جلوی دید را می‌گیرد.</p></div>
      <div class="cap" data-s="4"><h3>ارتفاع دکل</h3><p>{mast_line}</p></div>
      <div class="cap" data-s="5"><h3>{fres_t}</h3><p>{fres_l}</p></div>
    </div>
  </div>
</section>''')
        css_rules.append(scene_css(aid, 6, []))
        acts_js.append(f"E.act('{aid}',[.14,.32,.5,.68,.84]);")

    # ---------------- budget act (main link, balanced pick)
    bal_id = L0.get('picks', {}).get('balanced')
    bal = next((o for o in L0.get('radio_options', []) if o['id'] == bal_id), None)
    if bal and bal.get('margin_db') is not None:
        m = cat[bal_id]
        story.append(f'''
<section class="story" id="budget" style="--len:500svh" aria-label="بودجهٔ لینک">
  <div class="stage">
    <div class="scene side" aria-hidden="true"><svg class="bud" viewBox="0 0 1000 570" preserveAspectRatio="xMidYMid meet">{budget_svg(bal, m, L0["fade_margin_target_db"])}</svg></div>
    <div class="caps">
      <div class="cap lead" data-s="0"><h2>سیگنال کافی می‌رسد؟</h2><p>با <span class="ltr">{e(m["brand"])} {e(m["model"])}</span> در هر دو طرف.</p></div>
      <div class="cap" data-s="1"><h3>توان ارسال</h3><p>فرستنده {fa(bal["tx_dbm"])} و آنتن {fa(m["gain_dbi"])}؛ توان مؤثر {fa(bal["eirp_dbm"])} dBm.</p></div>
      <div class="cap" data-s="2"><h3>افت مسیر</h3><p>در {km(L0["distance_m"])}، {fa(bal["loss_db"])} دسی‌بل از سیگنال کم می‌شود.</p></div>
      <div class="cap" data-s="3"><h3>سیگنال دریافتی</h3><p>آنتن مقابل آن را به {fa(bal["rx_dbm"])} dBm می‌رساند.</p></div>
      <div class="cap" data-s="4"><h3>حاشیهٔ اطمینان {fa(bal["margin_db"])} دسی‌بل</h3><p>هدف دست‌کم {fa(L0["fade_margin_target_db"])}؛ ظرفیت واقعی حدود {fa(bal["real_mbps"])} مگابیت.</p></div>
    </div>
  </div>
</section>''')
        css_rules.append(scene_css('budget', 5, []))
        acts_js.append("E.act('budget',[.18,.4,.62,.82]);")

    # ---------------- equipment section
    gear = []
    for l in links:
        opts = {o['id']: o for o in l.get('radio_options', [])}
        cards = []
        for tier in ('economy', 'balanced', 'pro'):
            mid = l.get('picks', {}).get(tier)
            if not mid:
                continue
            m, o = cat[mid], opts[mid]
            p = P.get(mid)
            price = (f'<p class="price">{e(p["price"])} <small>{e(p.get("unit", ""))}</small></p>'
                     f'<p class="src">منبع: <a href="{e(p["source"])}" rel="noopener" target="_blank">{e(p.get("shop") or "لینک")}</a></p>') if p else f'<p class="price">{need("قیمت روز")}</p>'
            if o.get('margin_db') is None:
                spec = f'<li>باند ۶۰ گیگاهرتز{" + پشتیبان ۵" if m.get("backup_5ghz") else ""}</li><li>ظرفیت واقعی تا {fa(o["max_mbps"])} مگابیت</li><li>برد مناسب تا {km(m["range_km"]*1000)}</li>'
            else:
                spec = (f'<li>آنتن {fa(m["gain_dbi"])} dBi، پرتو {fa(m.get("beam_deg", "-"))}°</li>'
                        f'<li>تنظیم پیشنهادی: کانال {fa(o["width_mhz"])} MHz، <span class="ltr">{e(o["modulation"])}</span></li>'
                        f'<li>ظرفیت واقعی: {fa(o["real_mbps"])} (تا {fa(o["max_mbps"])}) مگابیت</li>'
                        f'<li>حاشیهٔ اطمینان: {fa(o["margin_db"])} dB</li>')
            cards.append(f'''<article class="card tier-{tier}" data-reveal><p class="tier">{TIER_FA[tier]}</p>
<h3 class="ltr">{e(m["brand"])} {e(m["model"])}</h3><p class="why">{TIER_WHY[tier]}</p><ul>{spec}<li>پورت {e(m["port"])}، دمای کاری <span class="ltr">{e(m["temp"])}</span> °C</li></ul>
<p class="note">{e(m["notes"])}</p>{price}</article>''')
        title = f'{e(name(l["a"]))} ↔ {e(name(l["b"]))}'
        body = ''.join(cards) if cards else '<p>هیچ رادیویی با این فاصله و حاشیهٔ اطمینان مناسب نیست؛ نقطهٔ واسط لازم است.</p>'
        gear.append(f'<div class="linkgear"><h3 class="lg-t">{title} · {km(l["distance_m"])}</h3><div class="cards">{body}</div></div>')
    price_note = f'قیمت‌ها به تاریخ {fa(pdate)} از فروشگاه‌های ایرانی جست‌وجو شده‌اند و با نوسان ارز تغییر می‌کنند.' if pdate else 'قیمت روز هنوز وارد نشده است.'

    star_html = ''
    st = R.get('star')
    if st:
        aps = ''.join(f'<li><span class="ltr">{e(cat[a["ap"]]["brand"])} {e(cat[a["ap"]]["model"])}</span> با کلاینت <span class="ltr">{e(cat[a["cpe"]]["model"])}</span>: '
                      f'دورترین نقطه {fa(a["worst_client"]["real_mbps"])} مگابیت با حاشیهٔ {fa(a["worst_client"]["margin_db"])} dB'
                      f'{" · قیمت: " + e(P[a["ap"]]["price"]) if a["ap"] in P else ""}</li>' for a in st['ap_options'])
        adv = ('تعداد نقاط کم یا ترافیک زیاد است؛ برای هر شعبه یک لینک نقطه‌به‌نقطهٔ جدا بهتر است.' if st['advice'] == 'ptp'
               else f'یک ایستگاه مرکزی با {fa(st["sectors_needed"])} آنتن سکتور {fa(st["sector_beam_deg"])} درجه همهٔ نقاط را پوشش می‌دهد.')
        star_html = f'''<section class="sec" id="star" aria-labelledby="h-star"><div class="wrap">
<h2 id="h-star" data-reveal>شبکهٔ چندنقطه‌ای از {e(name(st["hub"]))}</h2>
<div class="prose" data-reveal><p>نقاط در بازهٔ {fa(st["spread_deg"])} درجه پخش‌اند و دورترین آن‌ها {km(st["farthest_m"])} فاصله دارد. {adv}</p>
<ul>{aps or "<li>هیچ آنتن سکتوری با این فاصله مناسب نیست.</li>"}</ul></div></div></section>'''

    # ---------------- install sheet
    rows = []
    for l in links:
        for side, peer, az, tilt, mast, new, agl, g in (
                ('a', 'b', l['azimuth_ab'], l.get('tilt_a_deg'), l.get('mast_a_m'), l.get('new_mast_a_m'), l.get('antenna_agl_a_m'), l['ground_a_m']),
                ('b', 'a', l['azimuth_ba'], l.get('tilt_b_deg'), l.get('mast_b_m'), l.get('new_mast_b_m'), l.get('antenna_agl_b_m'), l['ground_b_m'])):
            s = sites[l[side]]
            ok = l['feasible']
            rows.append(f'<tr><td>{e(name(l[side]))}</td><td>{e(name(l[peer]))}</td>'
                        f'<td class="ltr">{s["lat"]:.6f}, {s["lon"]:.6f}</td><td>{fa(g, 1)}</td><td>{fa(s.get("building_m", 0))}</td>'
                        f'<td>{fa(mast) if ok else "—"}{f" (جدید {fa(new)})" if ok and new != mast else ""}</td><td>{fa(agl) if ok else "—"}</td>'
                        f'<td>{fa(az, 1)}°</td><td>{fa(tilt, 2) if ok else "—"}°</td></tr>')
    install = f'''<section class="sec" id="install" aria-labelledby="h-install"><div class="wrap">
<h2 id="h-install" data-reveal>برگهٔ نصب</h2>
<p class="sub" data-reveal>ارتفاع‌ها به متر؛ آزیموت نسبت به شمال جغرافیایی (برای قطب‌نما حدود ۳ درجه انحراف مغناطیسی خوزستان را در نظر بگیرید)؛ شیب مثبت یعنی رو به بالا.</p>
<div class="tbl" data-reveal><table><thead><tr><th>نقطه</th><th>رو به</th><th>مختصات</th><th>ارتفاع زمین</th><th>ارتفاع بام</th><th>دکل روی بام</th><th>ارتفاع آنتن از زمین</th><th>آزیموت</th><th>شیب</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div></div></section>'''

    # ---------------- checklist + assumptions
    terrain_warn = '' if all(l['terrain_ok'] for l in links) else f'<li>{need("ارتفاع زمین از سرویس‌های آنلاین دریافت نشد؛ اعداد با ارتفاع دستی یا صفر حساب شده‌اند")}</li>'
    checks = f'''<section class="sec" id="checks" aria-labelledby="h-checks"><div class="wrap">
<h2 id="h-checks" data-reveal>قبل از خرید و نصب</h2>
<div class="prose" data-reveal><ul>
{terrain_warn}
<li><b>بازدید میدانی:</b> از بام یک طرف با دوربین دوچشمی یا پهپاد، طرف مقابل را ببینید. دادهٔ ماهواره‌ای ساختمان‌های تازه و درخت‌ها را نشان نمی‌دهد.</li>
<li><b>اسکن تداخل:</b> با ابزار Scan در MikroTik یا airView در Ubiquiti کانال خلوت را پیدا کنید؛ در شهر کانال ۲۰ یا ۴۰ مگاهرتز پایدارتر است.</li>
<li><b>مقررات:</b> باند و توان تشعشعی (EIRP) را با ضوابط سازمان تنظیم مقررات و ارتباطات رادیویی تطبیق دهید.</li>
<li><b>دکل:</b> برای آنتن‌های پرتو باریک (۵ درجه و کمتر) دکل باید بدون لرزش باشد؛ مهار سیمی و پایهٔ محکم.</li>
<li><b>گرما و گردوخاک:</b> دمای کاری دستگاه را چک کنید، کابل شبکهٔ Outdoor شیلددار و کانکتور ضدآب بزنید.</li>
<li><b>صاعقه و ارت:</b> ارت دکل، محافظ PoE (Surge Protector) و UPS برای هر دو طرف.</li>
</ul>
<p class="assume">فرض‌ها: فرکانس {fa(R["freq_ghz"])} گیگاهرتز، ضریب انحنا k={fa(L0["k"])}، هدف پاک‌بودن {fa(round(L0["clearance_target"]*100))}٪ منطقهٔ فرنل، منبع ارتفاع: <span class="ltr">{e(L0["terrain_source"])}</span>، حساسیت گیرنده‌ها مقادیر معمول 802.11ac است؛ پیش از خرید با دیتاشیت تطبیق دهید.</p></div></div></section>'''

    summary_items = ''.join(
        f'<li>{e(name(l["a"]))} تا {e(name(l["b"]))}: {km(l["distance_m"])}، اختلاف ارتفاع زمین {fa(abs(l["ground_diff_m"]), 1)} متر، '
        + (f'دکل {fa(l["mast_a_m"])} و {fa(l["mast_b_m"])} متر روی بام، آزیموت {fa(round(l["azimuth_ab"]))}° و {fa(round(l["azimuth_ba"]))}°.' if l['feasible'] else 'بدون دید مستقیم؛ نقطهٔ واسط لازم است.')
        + '</li>' for l in links)
    what = f'''<section class="sec" id="what" aria-labelledby="h-what"><div class="wrap">
<h2 id="h-what" data-reveal>این طرح لینک رادیویی چه می‌گوید؟</h2>
<div class="prose" data-reveal><p>این گزارش طرح لینک رادیویی نقطه‌به‌نقطه برای «{e(R["project"])}» است: {fa(n_sites)} نقطه، {fa(len(links))} لینک و مجموع {km(total_km)} مسیر در باند {fa(R["freq_ghz"])} گیگاهرتز با نیاز {fa(R["required_mbps"])} مگابیت واقعی.</p>
<ul>{summary_items}</ul></div></div></section>'''

    gear_html = f'''<section class="sec" id="gear" aria-labelledby="h-gear"><div class="wrap">
<h2 id="h-gear" data-reveal>تجهیزات پیشنهادی</h2>
<p class="sub" data-reveal>برای هر لینک سه گزینه، همه در بازار ایران. {price_note}</p>
{"".join(gear)}</div></section>'''

    nav = '<a href="#p0">پروفایل مسیر</a>' + ('<a href="#budget">بودجهٔ لینک</a>' if bal else '') + '<a href="#gear">تجهیزات</a><a href="#install">نصب</a>'
    return TEMPLATE.format(
        title=e(R['project']), desc=e(f'طرح لینک رادیویی {R["project"]}: فاصله، ارتفاع دکل، بودجهٔ لینک و تجهیزات پیشنهادی.'),
        font=base64.b64encode((ASSETS / 'fonts' / 'Vazirmatn-wght.woff2').read_bytes()).decode(),
        base_css=(ASSETS / 'engine' / 'base.css').read_text(encoding='utf-8'),
        scene_css='\n'.join(css_rules), nav=nav, story='\n'.join(story),
        sections=what + gear_html + star_html + install + checks, date=fa(R['generated']),
        gsap=(ASSETS / 'vendor' / 'gsap.min.js').read_text(encoding='utf-8'),
        st=(ASSETS / 'vendor' / 'ScrollTrigger.min.js').read_text(encoding='utf-8'),
        engine=(ASSETS / 'engine' / 'story-engine.js').read_text(encoding='utf-8'),
        ui=(ASSETS / 'engine' / 'ui.js').read_text(encoding='utf-8'),
        acts='\n  '.join(acts_js))


TEMPLATE = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>طرح لینک رادیویی | {title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex,nofollow">
<style>
@font-face{{font-family:"Vazirmatn";src:url(data:font/woff2;base64,{font}) format("woff2");font-weight:100 900;font-display:swap}}
{base_css}
</style>
<style>
:root{{--font:"Vazirmatn",system-ui,sans-serif;--brand:#3DDC97;--brand-ink:#06130D;--alert:#FF6B5B;--st-bg:#071018;--st-surface:#0E1A24}}
.grid{{stroke:rgba(238,242,248,.05);stroke-width:1}}
.link{{stroke:var(--brand);stroke-width:4;stroke-dasharray:1;stroke-dashoffset:0;transition:stroke-dashoffset 1.1s var(--ease-in-out)}}
.link.bad{{stroke:var(--alert)}}
.az{{stroke:var(--st-ink-2);stroke-width:2;stroke-dasharray:1;transition:stroke-dashoffset .7s var(--ease-out)}}
.dist,.azl{{fill:var(--st-ink);font:800 22px var(--font);paint-order:stroke;stroke:var(--st-bg);stroke-width:7px;stroke-linejoin:round}}
.azl{{font-size:17px;fill:var(--st-ink-2)}}
.pin{{fill:var(--st-ink)}}.hub .pin{{fill:var(--brand)}}
.halo{{fill:none;stroke:var(--brand);stroke-width:2;opacity:.8}}
.sname{{fill:var(--st-ink);font:800 24px var(--font);paint-order:stroke;stroke:var(--st-bg);stroke-width:8px;stroke-linejoin:round}}
.north path{{fill:var(--st-ink-2)}}.north text{{fill:var(--st-ink-2);font:700 16px var(--font)}}
.prof,.bud{{width:100%;height:100%}}
.tick{{stroke:var(--st-line);stroke-width:1}}
.tl{{fill:var(--st-ink-3);font:600 15px var(--font)}}
.ground{{fill:#6B5434;stroke:#B08A55;stroke-width:2}}
.bulge{{fill:none;stroke:#E6C48A;stroke-width:2.5;stroke-dasharray:1;transition:stroke-dashoffset 1s var(--ease-in-out)}}
.clutter{{fill:rgba(170,182,202,.28)}}
.obst{{fill:var(--alert);opacity:.85}}
.olab,.slab{{fill:var(--st-ink);font:800 17px var(--font);paint-order:stroke;stroke:var(--st-bg);stroke-width:6px;stroke-linejoin:round}}
.bld{{fill:#2A3B4C;stroke:#4A6075}}
.mast{{stroke:var(--st-ink);stroke-width:5;stroke-linecap:round;transform-box:fill-box;transform-origin:50% 100%;transition:transform 1s var(--ease-out)}}
.ant{{fill:var(--brand)}}
.los{{stroke:var(--brand);stroke-width:2.5;stroke-dasharray:1;transition:stroke-dashoffset .9s var(--ease-in-out)}}
.fresnel{{fill:rgba(61,220,151,.12);stroke:rgba(61,220,151,.5);stroke-width:1}}
.fresnel6{{fill:rgba(61,220,151,.22)}}
.crit{{fill:none;stroke:#F2C14E;stroke-width:3}}
.clab{{fill:#F2C14E;font:800 17px var(--font);paint-order:stroke;stroke:var(--st-bg);stroke-width:6px}}
.bar.pos{{fill:var(--brand)}}.bar.neg{{fill:var(--alert)}}
.bl{{fill:var(--st-ink-2);font:700 18px var(--font)}}
.bv{{fill:var(--st-ink);font:800 18px var(--font)}}
.conn{{stroke:var(--st-ink-3);stroke-dasharray:4 4}}
.sens{{stroke:#F2C14E;stroke-width:2;stroke-dasharray:8 6}}
.sl{{fill:#F2C14E;font:700 15px var(--font)}}
.mbr{{stroke:#F2C14E;stroke-width:3}}.ml{{fill:#F2C14E;font:900 22px var(--font)}}
svg [class*=" s"],svg [class^="s"]{{transition:opacity 420ms var(--ease-out),stroke-dashoffset 1s var(--ease-in-out),transform 1s var(--ease-out)}}
{scene_css}
.sub{{max-width:70ch;margin-top:.8rem;color:var(--ink-3)}}
.linkgear{{margin-top:2.6rem}}.lg-t{{font-size:1.2rem;margin-bottom:1rem}}
.cards{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-card);padding:1.4rem;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:.5rem}}
.card.tier-balanced{{border:2px solid var(--accent-text)}}
.card h3{{font-size:1.15rem;text-align:start}}
.card ul{{margin:.3rem 0;padding-inline-start:1.1rem;font-size:.95rem;display:grid;gap:.25rem}}
.tier{{font-weight:900;color:var(--accent-text);font-size:.9rem}}.why{{color:var(--ink);font-weight:700}}
.note{{font-size:.88rem;color:var(--ink-3)}}.price{{margin-top:auto;font-weight:900;font-size:1.15rem;color:var(--ink)}}.src{{font-size:.85rem}}
.tbl{{overflow-x:auto;margin-top:1.4rem;border:1px solid var(--line);border-radius:16px}}
table{{border-collapse:collapse;width:100%;min-width:760px;font-size:.93rem}}
th,td{{padding:.7rem .8rem;border-bottom:1px solid var(--line);text-align:start;white-space:nowrap}}
th{{background:color-mix(in srgb,var(--ink) 5%,transparent);color:var(--ink);font-weight:800}}
.assume{{margin-top:1.4rem;font-size:.9rem;color:var(--ink-3)}}
@media (max-aspect-ratio:21/20){{.tl{{font-size:24px}}.olab,.slab,.clab{{font-size:26px}}.bl,.bv{{font-size:26px}}.sl{{font-size:22px}}.ml{{font-size:30px}}.dist{{font-size:30px}}.azl{{font-size:24px}}.sname{{font-size:32px}}}}
</style>
<script>document.documentElement.classList.add('js');</script>
</head>
<body>
<a class="skip" href="#what">رفتن به خلاصهٔ متنی</a>
<header class="topbar" id="topbar"><div class="wrap">
  <a href="#map" class="wm">لینک رادیویی</a>
  <nav class="nav" aria-label="بخش‌ها">{nav}</nav>
  <a class="btn btn-brand btn-sm" href="#gear">تجهیزات</a>
</div><div class="progress" aria-hidden="true"><i id="prog"></i></div></header>
<div id="doc"><main>
{story}
{sections}
</main>
<footer class="foot"><div class="wrap">تهیه‌شده با اسکیل P2P Radio Connection · {date}</div></footer>
</div>
<script>{gsap}</script>
<script>{st}</script>
<script>{engine}</script>
<script>
(function () {{
  var E = StoryEngine, U = E.util, cam = document.getElementById('cam');
  /* map camera: slow push-in, focus away from the caption side; fits the map on phones */
  function mapFrame(p) {{
    var asp = innerWidth / innerHeight, wide = asp > 1.05;
    var visW = asp >= 16 / 9 ? 1600 : 900 * asp, fit = Math.min(1, visW * .8 / 720);
    var s = fit * U.lerp(1.12, 1, U.ease(U.seg(p, 0, .5)));
    var ax = wide ? 1600 * .36 : 800, ay = wide ? 470 : 330;
    cam.setAttribute('transform', 'translate(' + ax + ' ' + ay + ') scale(' + s.toFixed(4) + ')');
  }}
  {acts}
  E.start();
}})();
</script>
<script>{ui}</script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('-o', '--out', default='report.html')
    ap.add_argument('--prices')
    a = ap.parse_args()
    R = json.loads(Path(a.results).read_text(encoding='utf-8'))
    prices = json.loads(Path(a.prices).read_text(encoding='utf-8')) if a.prices else None
    out = build(R, prices)
    Path(a.out).write_text(out, encoding='utf-8')
    print(f'wrote {a.out} ({len(out)//1024} KB)')


if __name__ == '__main__':
    main()
