---
name: daranx-proposal-kit
description: "Build client-facing HTML documents in DaranX's visual identity — proposals (پروپوزال), final books (فاینال‌بوک), statements of work, plans, case studies, and any branded one-page or multi-section deliverable. Use this whenever the user asks for a DaranX / داران‌ایکس proposal, final book, offer, plan, report, or any HTML document meant to be sent to a customer or team, even if they don't say \"brand\" — it supplies the navy/steel palette, the Vazirmatn font, the RTL layout, a cinematic scroll-responsive template whose first screen gives the whole picture, and the شناخت→طراحی→اجرا→پشتیبانی narrative so every deliverable looks and reads like DaranX. Also use it to restyle an existing plain HTML document into DaranX's identity."
---

# DaranX Proposal & Document Kit

This skill produces **self-contained, RTL, Persian HTML documents** that carry
DaranX's visual identity and the way the company talks about its work. The
output is one `.html` file a salesperson can open, present, email, or print —
no build step, no external CSS/JS, fonts embedded locally.

Use it for proposals (پروپوزال), final books (فاینال‌بوک), scopes of work,
plans, case studies / portfolios (نمونه‌کار), and short branded reports.

Every document this kit produces follows **three non-negotiable rules**:

1. **The first screen is the whole picture** (§ The first screen).
2. **It feels cinematic**, calm and premium, never flashy (§ Cinematic language).
3. **It is scroll-responsive** on every screen size (§ Scroll-responsive behaviour).

## The brand in one breath

Everything you write for DaranX should feel like a single designed system, not
parts placed side by side. The company's own promise is literally that: **«ما
خدمات مختلف را کنار هم نمی‌گذاریم؛ آن‌ها را با هم طراحی می‌کنیم و مسئولیت نتیجه
را به عهده می‌گیریم.»** Carry that spirit into the document — coherent, calm,
confident, and honest.

- **Name:** always `DaranX` (never "Daranx"/"DaranEx"); the `X` takes the steel
  accent. Persian: «داران‌ایکس».
- **Core idea:** «همه چیز سرِ جای درستش.»
- **Design principle:** «طراحی مقدم بر اجراست» — design precedes execution.
- **Equation:** Design + Technology = Solution.
- **Three domains:** زیرساخت (Infrastructure) · امنیت (Security) · هوشمندی
  (Intelligence).
- **Voice:** formal Persian, business language (هزینه، ریسک، پایداری،
  بهره‌وری، امنیت، توسعه). Never invent metrics, logos, awards, or client
  names. If a number isn't given, describe the value qualitatively.
- **Contact block (use verbatim):** ۰۲۱-۸۸۹۶۴۱۱۶ · ۸۸۹۶۶۹۰۴ · ۰۹۳۵-۹۳۷۰۹۱۰ —
  تهران، میدان فاطمی، نبش چهلستون، ساختمان چهلستون، طبقه ۲، واحد ۲۰۲ —
  www.DaranX.com

## 1. The first screen: the whole picture

A decision-maker often reads only the first screen. So the hero is not a cover
page; it is a **one-screen executive briefing**. Without scrolling, in about 20
seconds, the reader must be able to answer all six questions:

| # | Question | Where it lives in the hero |
|---|---|---|
| 1 | این سند چیست و برای کیست؟ | `.kicker`: document type · client/project |
| 2 | چه پیشنهادی داریم؟ (the promise) | `h1`, one sentence, one `.glow` key phrase |
| 3 | حکم و نتیجه چیست؟ | `.verdict`, 2–3 lines: problem → what we do → outcome |
| 4 | در چه مقیاس و زمانی؟ | `.glance .facts`: exactly 4 facts (number + label) |
| 5 | چه چیزهایی شامل می‌شود و مسیر چیست؟ | `.glance .scope` chips (3–5) + `.journey` (4 steps with durations) |
| 6 | قدم بعدی چیست؟ | `.glance .next` + the primary button |

Rules for the hero:

- Write it **last**, after the body, as a distillation of the whole document.
  If the hero needs content the body doesn't contain, the body is incomplete.
- Every fact is real. A number the user didn't give is replaced with a
  qualitative fact (e.g. «سه‌زبانه»), never invented.
- Keep words lean: `h1` ≤ 12 words, verdict ≤ 45 words, each fact label ≤ 4 words.
- Desktop (1280×800): the entire hero, including the glance panel, is visible
  without scrolling. Phone (390×844): kicker, `h1`, verdict and the button are
  in the first screen, and the glance panel follows immediately.
- The hero stays dark (night navy + network motif) in both themes; it is the
  cinematic opening, the body follows the reader's theme.

## 2. Cinematic language

Cinematic here means *pacing and depth*, not effects. Use these, in this order of
importance:

- **Opening shot:** full-viewport night-navy hero with the live blue node
  network (the DaranX motif) on `<canvas>`, a soft vignette, and a staggered
  entrance (kicker → title → verdict → actions, glance panel alongside).
- **Chapters:** every section opens with a `.chapter` header: a huge outlined
  ghost number (`۰۱`, `۰۲`…), the eyebrow, and a short `h2`. Numbers run in order.
- **Interludes:** 1–2 full-width `.interlude` bands per document with a single
  memorable sentence (a principle, a verdict, the client's goal). They give the
  document breathing room between heavy chapters. Never more than two.
- **Depth:** large type contrast, generous section spacing, subtle parallax on
  interludes and banners, glass panel on the hero.
- **Restraint:** one accent family (navy/steel), slow eased motion
  (`--ease`, 0.9–1.4s), no bouncing, no spinning, no autoplay sound or video.

## 3. Scroll-responsive behaviour

The template's script already implements all of this; keep the hooks intact
when you edit content:

| Behaviour | Hook |
|---|---|
| Reveal on scroll (fade + rise + de-blur, staggered) | `data-reveal` (variants `fade`, `scale`) + `style="--d:.15s"` for stagger |
| Reading progress bar | `#prog` inside the top bar |
| Top bar turns solid after the hero; nav highlights the current chapter | sections with `id` + `data-chapter="نام"`; nav links `href="#id"` |
| Chapter rail (dots) on wide screens, built automatically | every `[data-chapter]` section |
| Hero copy drifts and fades as you scroll away | `#heroCopy` |
| Parallax | `data-parallax="0.12"` (positive = slower, negative = faster) |
| Numbers count up when visible (Persian digits) | `data-count="۱۲"` on the number element |
| Method line draws across the four steps | `.mstrip[data-line]` |

Non-negotiables:

- **Content is visible without JavaScript** (reveal styles apply only under
  `html.js`) and in print.
- **`prefers-reduced-motion`** disables every animation, parallax and the canvas
  drift; the document must still look complete.
- **Responsive:** no horizontal page scroll at any width; 16px minimum side
  gutter on phones; tables live inside `.tablewrap` (they scroll on their own);
  grids collapse to one column; use `100svh`, not only `100vh`, for full-height
  blocks.
- Scroll handlers are `passive` and batched with `requestAnimationFrame`; the
  canvas pauses when off-screen.

## How to build a document

1. **Start from the template.** Copy `assets/template.html` to the output file
   and copy the `assets/` folder (font + logo) next to it; references are
   relative (`assets/Vazirmatn-VF.woff2`, `assets/daranx-logo.svg`).
2. **Plan chapters** from the request. Keep, delete or duplicate the template's
   chapters; renumber the ghost numbers; update the nav links to match the
   section ids. Add new components using the existing tokens (see
   `references/brand.md`); don't restart the CSS.
3. **Write the body first, then the hero** (§1), then pick one or two interlude
   sentences.
4. **Fill real content.** Replace every `{{...}}` placeholder. Nothing may read
   like lorem-ipsum or a leftover sample. Prices you weren't given stay as
   clearly marked blanks for the user.
5. **Keep it RTL and Persian** in the UI, English in code/comments. Wrap Latin
   fragments that sit inside Persian sentences (brand name, file names, phone
   numbers) in `<bdi>` or `.ltr` so punctuation doesn't jump.
6. **Verify before handing over** (required): render headless and look at the
   screenshots:
   - 1280×800, first screen only: all six hero questions answered, nothing cut off;
   - 390×844, first screen and a full-page capture: no horizontal overflow
     (`scrollWidth - innerWidth === 0`), readable tables;
   - dark theme first screen;
   - with reduced motion emulated: everything visible.
   If Playwright's bundled browser is missing, launch the preinstalled Chromium
   with `--headless=new`.

## Document skeleton (recommended order)

1. **Hero = whole picture (§1)** — replaces the old cover page.
2. **Executive summary (خلاصهٔ اجرایی)** — 3–5 lines + outcomes.
3. **Understanding the need (شناخت)** — show you understood the real problem.
4. *Interlude* (optional).
5. **Approach / method (روش کار)** — the four-step strip شناخت→طراحی→اجرا→پشتیبانی.
6. **Scope / solution (محدوده و راهکار)** — cards per domain, outcomes.
7. **Evidence (نمونه‌کار / سابقه)** — only if real; otherwise delete.
8. **Commercials / timeline (زمان‌بندی و شرایط)** — tables; never fabricate prices.
9. **Next step (قدم بعدی)** — the CTA + contact block in the footer.

A short offer can be hero + summary + scope + next step. Use judgment, but the
hero rule always applies.

## Component cheat-sheet

Full CSS lives in the template; values in `references/brand.md`.

- Hero: `.hero` › `.hero-grid` › `.hero-copy` (`.kicker`, `h1 .glow`, `.verdict`,
  `.hero-actions`, `.hero-meta`) + `aside.glance` (`.facts/.fact`, `.scope`,
  `.journey`, `.next`) + `.cue`.
- Chapters: `.chapter` (`.no` ghost number, `.eyebrow`, `h2`), `.lead`, `.longcopy`.
- `.interlude` (statement band, `blockquote` + `cite`).
- `.mstrip` + `.mstep` (four-step method; line draws on scroll).
- `.cards` / `.card`, `.outcomes`, `.tablewrap` + `table`, `.banner`.
- Buttons: `.btn-light` (on dark), `.btn-glass` (secondary on dark),
  `.btn-primary`, `.btn-ghost`. Pills: `.chip`.
- `.cta` (closing block), `.foot` (contact).

## Imagery rules (learned the hard way)

- The DaranX motif is a **dark-navy field with a blue node/network graphic** and
  a glowing icon. The hero canvas draws it live; keep other backgrounds in that family.
- **Behind text, use text-free images** so nothing collides. If you must place a
  text-labeled image behind text, blur + darken it so the foreground stays legible.
- **Text-labeled images belong on decorative banners**, not behind paragraphs.
- Always give an image a graceful fallback: `.banner.noimg` shows a branded
  gradient when a file is missing, so a document never looks broken.

## Theming and accessibility

- Light and dark themes are defined via CSS variables; the body sets an explicit
  background. Use the tokens (`--navy`, `--steel`, `--ink`…), never hard-coded
  colors, except inside the always-dark hero and interludes.
- Keep text contrast on dark at `--on-navy` or white; never put `--ink-faint` on navy.
- Links and buttons have visible focus; the rail labels appear on focus too.

## When details matter

For exact color values (light + dark), radii, shadows, spacing scale, and the
cinematic/scroll layer, read `references/brand.md`. Don't guess hex values.
