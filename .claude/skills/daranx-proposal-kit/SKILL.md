---
name: daranx-proposal-kit
description: >-
  Build client-facing HTML documents in DaranX's visual identity — proposals
  (پروپوزال), final books (فاینال‌بوک), statements of work, case studies, and
  any branded one-page or multi-section deliverable. Use this whenever the user
  asks for a DaranX / داران‌ایکس proposal, final book, offer, report, or any HTML
  document meant to be sent to a customer, even if they don't say "brand" — it
  supplies the navy/steel palette, the Vazirmatn font, the RTL layout, the
  component library, and the شناخت→طراحی→اجرا→پشتیبانی narrative so every
  deliverable looks and reads like DaranX. Also use it to restyle an existing
  plain HTML document into DaranX's identity.
---

# DaranX Proposal & Document Kit

This skill produces **self-contained, RTL, Persian HTML documents** that carry
DaranX's visual identity and the way the company talks about its work. The
output is one `.html` file a salesperson can open, present, email, or print —
no build step, no external CSS/JS, fonts embedded locally.

Use it for proposals (پروپوزال), final books (فاینال‌بوک), scopes of work,
case studies / portfolios (نمونه‌کار), and short branded reports.

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

## How to build a document

1. **Start from the template.** Copy `assets/template.html` to the output file.
   It already contains the full design system (CSS tokens, Vazirmatn @font-face,
   light/dark themes, every component) and a demo of each section. Also copy the
   `assets/` folder next to it (the font and logo) so the file is self-contained
   and works offline — references are relative (`assets/Vazirmatn-VF.woff2`,
   `assets/daranx-logo.svg`).
2. **Decide the sections** from the request, then keep, delete, or duplicate the
   template's sample sections. Don't start the CSS from scratch — the value of
   this kit is that the tokens and components are already correct.
3. **Fill real content.** Replace every placeholder (`{{...}}` and the sample
   Persian copy) with the customer's actual situation. Leave nothing that reads
   like lorem-ipsum or a leftover sample.
4. **Keep it RTL and Persian** in the UI, English in code/comments. Numbers in
   the body read naturally in Persian; phone numbers stay LTR.
5. **Check it renders** — if you can, open it headless and screenshot before
   handing it over, the way the website work in this project was verified.

## Document skeleton (recommended order)

Mirror the flow the brand uses everywhere — recognition before design, design
before execution, support from day one:

1. **Cover (کاور)** — full-screen: client/project name, a one-line promise,
   DaranX logo, date. A quiet navy image or gradient; don't crowd it.
2. **Executive summary (خلاصهٔ اجرایی / معرفی)** — who DaranX is for this
   client and what this document proposes, in 3–5 lines.
3. **Understanding the need (شناخت)** — show you understood the real problem
   before proposing anything. This is where trust is won.
4. **Approach / method (روش کار)** — the four-step strip
   شناخت→طراحی→اجرا→پشتیبانی, tailored to this engagement.
5. **Scope / solution (محدوده و راهکار)** — what's included, per domain where
   relevant; outcomes list with check marks.
6. **Evidence (نمونه‌کار / سابقه)** — portfolio cards, only if real.
7. **Commercials / timeline (زمان‌بندی و شرایط)** — tables; never fabricate
   prices, insert placeholders the user fills.
8. **Close (CTA / تماس)** — a confident next step + the contact block.

Not every document needs all eight — a short offer might be cover + summary +
scope + close. Use judgment.

## Component cheat-sheet

The template ships these ready to use (full CSS in `references/brand.md`):

- `eyebrow` → `h2` → `lead` : the standard section header rhythm.
- `.btn-primary` (solid navy), `.btn-ghost` / `.btn-outline` (quiet),
  `.btn-light` (on dark).
- `.chip` / `.hero-pill` : pill labels.
- `.mstrip` + `.mstep` : the four-step method strip.
- `.outcomes` : a row of check-marked result statements.
- `.cards` / `.pf-card` : feature or portfolio cards.
- `.sec` / `.sec.alt` : section wrapper (alt = tinted background for rhythm).
- `.cta` : the closing call-to-action block.
- `.banner` : a wide decorative header image (text-labeled brand image is fine
  here); content imagery behind text should be text-free. See the imagery rule
  below.

## Imagery rules (learned the hard way)

- The DaranX motif is a **dark-navy field with a blue node/network graphic** and
  a glowing icon. Keep backgrounds in that family.
- **Behind text, use text-free images** so nothing collides. If you must place a
  text-labeled image behind text, blur + darken it (see `.img-busy` in the
  template) so the foreground stays legible.
- **Text-labeled images belong on decorative banners**, not behind paragraphs.
- Always give an image a graceful fallback: the template's `.noimg` pattern
  shows a branded gradient + icon when a file is missing, so a document never
  looks broken before the real photo is dropped in.

## Theming, motion, accessibility

- Light and dark themes are both defined via CSS variables; the body sets an
  explicit background. Don't hard-code colors — use the `--navy`, `--steel`,
  `--ink`… tokens so both themes stay correct.
- Keep motion subtle (`.reveal` fade-in). Always honor
  `prefers-reduced-motion` — the template already gates animation on it.
- Target phone width too: a 16px side gutter, no horizontal scroll.

## When details matter

For the exact color values (light + dark), radii, shadows, spacing scale, and
copy-pasteable CSS for each component, read `references/brand.md`. Read it
whenever you need a token you don't remember or are adding a component the
template doesn't already include — don't guess hex values.
