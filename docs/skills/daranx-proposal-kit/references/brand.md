# DaranX brand reference — tokens & components

Exact, copy-pasteable values. These mirror the live DaranX website so every
deliverable matches. The `assets/template.html` in this skill already contains
all of this; use this file when you need a specific value or a component the
template doesn't yet include.

## Table of contents
1. Color tokens (light)
2. Color tokens (dark)
3. Type, shape, space
4. Core component CSS
5. Imagery helpers
6. Brand content strings
7. Cinematic & scroll layer

---

## 1. Color tokens (light)

```css
:root{
  --navy:#153A62;        /* primary brand */
  --navy-deep:#0E2749;
  --steel:#3E7BB6;       /* accent (the X, links, highlights) */
  --steel-soft:#6FA3D2;
  --silver:#D9D9D9;
  --ground:#F3F6FA;      /* page background */
  --surface:#FFFFFF;     /* cards */
  --surface-2:#EAF0F7;   /* tinted sections / alt */
  --ink:#12233A;         /* headings */
  --ink-soft:#43566E;    /* body */
  --ink-faint:#5E6E86;   /* captions */
  --line:#DCE4EE;
  --line-strong:#C2D0E0;
  --on-navy:#EAF1F8;     /* text on navy */
  --on-navy-soft:#AEC4DB;
  --on-navy-faint:#6E89A6;
  --accent-solid:#153A62;
  --on-accent:#FFFFFF;
  --grad:linear-gradient(120deg,#153A62 0%,#2E6098 55%,#3E7BB6 100%);
  --grad-soft:linear-gradient(120deg,#153A62,#3E7BB6);
  --shadow:0 1px 2px rgba(21,58,98,.06), 0 10px 30px rgba(21,58,98,.08);
  --shadow-lift:0 2px 8px rgba(21,58,98,.09), 0 22px 60px rgba(21,58,98,.16);
}
```

## 2. Color tokens (dark)

Redefine under `@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){…}}`
and also under `:root[data-theme="dark"]{…}` so a manual toggle works:

```css
--navy:#0C2036;  --navy-deep:#081627;
--steel:#5B95CE; --steel-soft:#7FB0DF;  --silver:#31465D;
--ground:#081320; --surface:#0F2338; --surface-2:#142B45;
--ink:#E9F0F8; --ink-soft:#A6BACF; --ink-faint:#8398AF;
--line:#1E3450; --line-strong:#2A4666;
--accent-solid:#5B95CE; --on-accent:#08151f;
--grad:linear-gradient(120deg,#1B4C7A 0%,#3E7BB6 55%,#7FB0DF 100%);
--grad-soft:linear-gradient(120deg,#2E6098,#7FB0DF);
--shadow:0 1px 2px rgba(0,0,0,.35), 0 12px 34px rgba(0,0,0,.4);
--shadow-lift:0 2px 8px rgba(0,0,0,.45), 0 26px 64px rgba(0,0,0,.55);
```

## 3. Type, shape, space

```css
--font:"Vazirmatn",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
--r-sm:10px; --r-md:16px; --r-lg:26px;   /* chips/buttons use 999px pills */
--maxw:1160px;
--gutter:clamp(1rem,4vw,2.5rem);
--sp-section:clamp(4rem,8vw,7.5rem);
```

Font face (self-hosted variable woff2, weights 100–900):

```css
@font-face{font-family:"Vazirmatn";src:url("assets/Vazirmatn-VF.woff2") format("woff2");
  font-weight:100 900;font-style:normal;font-display:swap}
```

Headings are heavy (800–900), body ~400–600. `h1` big
(`clamp(2.2rem,2.4vw+1.4rem,3.7rem)`), `h2` `clamp(1.6rem,1.3rem+1.4vw,2.4rem)`.
Line-height for Persian body ~1.9–2.05 (generous — Persian needs air).

## 4. Core component CSS

```css
/* section rhythm */
.sec{padding-block:var(--sp-section)}
.sec.alt{background:var(--surface-2)}
.wrap{max-width:var(--maxw);margin-inline:auto;padding-inline:var(--gutter)}

/* header rhythm: eyebrow -> h2 -> lead */
.eyebrow{display:inline-flex;align-items:center;gap:.5rem;font-size:.85rem;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:var(--steel)}
.eyebrow::before{content:"";width:26px;height:2px;background:var(--steel-soft);border-radius:2px}
.sec-head h2{color:var(--ink);margin-top:.6rem}
.lead{color:var(--ink-soft);font-size:1.08rem;line-height:1.95;max-width:62ch}

/* buttons */
.btn{display:inline-flex;align-items:center;gap:.5rem;border-radius:999px;font-weight:800;
  padding:.85rem 1.8rem;cursor:pointer;text-decoration:none;transition:transform .2s,box-shadow .2s}
.btn-primary{background:var(--accent-solid);color:var(--on-accent);box-shadow:var(--shadow)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:var(--shadow-lift)}
.btn-ghost,.btn-outline{background:transparent;color:var(--ink);border:1px solid var(--line-strong)}
.btn-light{background:#fff;color:var(--navy)}

/* pills / chips */
.chip,.hero-pill{display:inline-flex;align-items:center;gap:.5rem;border-radius:999px;
  padding:.4rem 1rem;font-weight:700;font-size:.9rem;color:var(--steel);
  background:var(--surface-2);border:1px solid var(--line)}

/* method strip (شناخت→طراحی→اجرا→پشتیبانی) */
.mstrip{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}
.mstep{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:1.3rem}
.mstep .n{width:34px;height:34px;border-radius:999px;display:grid;place-items:center;
  background:var(--grad-soft);color:#fff;font-weight:800;margin-bottom:.6rem}
@media(max-width:760px){.mstrip{grid-template-columns:repeat(2,1fr)}}

/* outcomes (check-marked results) */
.outcomes{display:flex;flex-wrap:wrap;gap:.7rem 1.4rem;margin-top:1.4rem}
.outcomes span{display:inline-flex;align-items:center;gap:.5rem;color:var(--ink-soft);font-weight:600}
.outcomes svg{width:20px;height:20px;color:var(--steel)}

/* cards */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.2rem}
.card,.pf-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);
  overflow:hidden;box-shadow:var(--shadow)}

/* cta block */
.cta{background:var(--grad);color:#fff;border-radius:var(--r-lg);padding:clamp(2rem,5vw,3.5rem);text-align:center}
.cta h2{color:#fff}

/* decorative banner (text-labeled brand image allowed here) */
.banner{position:relative;height:24vh;min-height:160px;max-height:300px;border-radius:var(--r-lg);
  overflow:hidden;border:1px solid var(--line);box-shadow:var(--shadow-lift);background:var(--surface-2)}
.banner img{width:100%;height:100%;object-fit:cover;display:block}

/* wide single-column body text (for description sections) */
.longcopy{max-width:none;color:var(--ink-soft);line-height:2.05;font-size:1.04rem}
.longcopy p{margin:0 0 1.1rem}
```

## 5. Imagery helpers

```css
/* graceful fallback: show branded gradient + icon when img missing */
.noimg{background:radial-gradient(120% 95% at 72% 8%,var(--steel),var(--navy) 62%)}
.ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:.55rem;
  color:#dce9f7;font-weight:700}
/* usage: <img onerror="this.closest('.banner').classList.add('noimg')"> + a .ph placeholder */

/* full-bleed image behind centered text */
.hero-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2}
.hero-scrim::before{content:"";position:absolute;inset:0;z-index:-1;
  background:linear-gradient(180deg,rgba(8,20,34,.74),rgba(8,20,34,.55) 45%,rgba(8,20,34,.85))}

/* only if a text-labeled image must sit behind text: dissolve it */
.img-busy .hero-bg{filter:blur(2px) brightness(.82) saturate(1.1);transform:scale(1.05)}
.img-busy.hero-scrim::before{background:
  radial-gradient(58% 52% at 50% 48%,rgba(6,14,26,.82),rgba(6,14,26,.42) 60%,transparent),
  linear-gradient(180deg,rgba(8,20,34,.34),rgba(8,20,34,.5))}
```

## 6. Brand content strings (reusable)

- Name: `DaranX` (X in steel) / «داران‌ایکس»
- Tagline: «همه چیز سرِ جای درستش.»
- Principle: «طراحی مقدم بر اجراست.»
- Differentiator: «ما خدمات مختلف را کنار هم نمی‌گذاریم؛ آن‌ها را با هم طراحی
  می‌کنیم و مسئولیت نتیجه را به عهده می‌گیریم.»
- Equation: «Design + Technology = Solution»
- Method: شناخت · طراحی · اجرا · پشتیبانی
- Domains: زیرساخت (Infrastructure) · امنیت (Security) · هوشمندی (Intelligence)
- Phones: ۰۲۱-۸۸۹۶۴۱۱۶ · ۸۸۹۶۶۹۰۴ · ۰۹۳۵-۹۳۷۰۹۱۰  (tel: +982188964116 / +982188966904 / +989359370910)
- Address: تهران، میدان فاطمی، نبش چهلستون، ساختمان چهلستون، طبقه ۲، واحد ۲۰۲
- Site: www.DaranX.com

---

## 7. Cinematic & scroll layer

Added tokens (both themes; dark value `--night:#050E1B`):

```css
--night:#07152A;                      /* always-dark hero & interludes */
--ease:cubic-bezier(.22,1,.36,1);     /* the only easing curve */
--sp:clamp(4rem,9vw,8rem);            /* section rhythm */
```

| Element | Spec |
|---|---|
| Hero | `min-height:100svh`; night background + two radial steel glows + vignette; `<canvas id="net">` node network, ≤80 nodes, links under 140px, `rgba(127,176,223,.22)` lines |
| Glance panel | glass: `linear-gradient(160deg,rgba(255,255,255,.10),rgba(255,255,255,.04))`, 1px `rgba(255,255,255,.16)` border, `blur(10px)` |
| Entrance | `[data-hero]` fade + 22px rise, 1.1s, stagger via `--d` (.05s → .55s) |
| Reveal | `[data-reveal]` opacity 0 → 1, 28px rise, 6px blur → 0, .9s, threshold .15 |
| Chapter number | `.chapter .no`: 4.5–9rem, weight 900, transparent fill, 1.5px `--line-strong` stroke |
| Interlude | night band, `blockquote` 1.5–2.7rem weight 850, max 28ch |
| Progress | 3px bar under the top bar, `--grad-soft`, `scaleX(scroll/max)` |
| Parallax | `data-parallax` factor × distance from viewport centre; skip off-screen |
| Count-up | `data-count`, 1.2s ease-out cubic, Persian digits |

Motion budget: every animation off under `prefers-reduced-motion`; nothing
loops except the canvas drift and the scroll cue; content visible without JS.
