# SEO and GEO checklist (cinematic pages)

Cinematic pages hide most text until a scene is active; search engines and AI answer engines still need clean, plain, structured text.

## On the page
- `<title>`: Brand | primary keyword phrase (≤ 60 chars). Meta description: one plain sentence, 140–160 chars, keyword + outcome.
- Exactly one `<h1>` (hero). Act leads are `<h2>`, scene steps `<h3>`; scene captions that are labels, not headings, are `<p class="cap-t">`.
- A plain-text "What is {Brand}?" section right after the story: definition sentence with the primary keyword, who it is for, 3–4 factual bullets. This is what AI answers quote.
- Keyword in the first paragraph of the hero (`.verdict`).
- FAQ as `<details>` with real answers.
- Images: WebP, width/height set, meaningful alt, lazy below the fold. OG image 1200×630 (render the hero).
- Content stays in the DOM in every state; static mode for no-JS.

## Head
- canonical, hreflang (+ x-default), og:*, twitter:card, theme-color, color-scheme, favicon (inline SVG data URI ok), font preload.
- `robots`: `noindex,nofollow` while any `[NEED]` marker remains, then `index,follow,max-image-preview:large,max-snippet:-1`. The editor flips it automatically on save.

## Structured data (one JSON-LD @graph)
- Organization (+ parentOrganization if a product brand), WebSite, the product type (SoftwareApplication / Product / Service / LocalBusiness), WebPage (about, mainEntity, dateModified, speakable on the summary), FAQPage built only from answered questions, Offer only for prices actually shown on the page (currency code must be ISO, e.g. IRR = toman × 10).

## Files next to the page
- `robots.txt`: allow all, explicitly allow GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended; Sitemap line.
- `sitemap.xml` with lastmod and hreflang alternates.
- `llms.txt`: one-paragraph summary in English, pages, key facts (category, audience, plans/prices if public).

## Performance
- Single HTML with inlined CSS/JS (GSAP ~120 KB), images as files; total gzip ~120–150 KB before images.
- Animate transform/opacity only; no layout thrash; CLS 0 (reserve image space).
