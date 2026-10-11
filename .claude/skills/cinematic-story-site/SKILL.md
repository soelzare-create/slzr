---
name: cinematic-story-site
description: Build cinematic, graphics-led, scroll-story websites and landing pages where the page tells one logical story scene by scene, each scroll moves to the next scene with motion, and every screen carries very little text. Use whenever the user wants a landing page, product site, campaign page, launch page, portfolio or explainer that should feel cinematic, story-driven, "motion graphic", scroll-responsive, Apple-style or "like the ActivePlano landing", even if they only say "a beautiful landing page", "a site that tells our story" or "less text, more visuals". Also use to turn an existing text-heavy page into a story. Not for dashboards, admin panels or long documentation.
---

# Cinematic Story Site

A page is a short film the reader scrolls through. One story, told in acts and scenes. Each scroll gesture plays the next scene as motion. Each scene shows one idea with a graphic and at most one short line of text. The page still works as plain text for people, search engines and AI.

This skill came out of the ActivePlano landing (store plan → zones → aisle → shelf). **That map is one example of a story, not the template.** Every new site gets its own world and its own arc.

## The five rules
1. **Story first.** Before any code, write the arc: where we start, what changes, where we land, why the reader should act. Every scene must follow from the previous one (cause → effect, whole → part, before → after). If a scene can be swapped with another without breaking the logic, it is not a story yet.
2. **Graphics carry the meaning.** The visual explains; the text only names what you see. A reader who skips all text should still follow the story from the visuals.
3. **Few words.** Hero: headline ≤ 8 words + one sentence. Caption: title ≤ 6 words + one line ≤ 20 words. One idea per scene. No paragraphs inside the story.
4. **One gesture = one scene.** Wheel tick / swipe / PageDown moves to the next stop; the in-between plays as motion. The outgoing scene leaves before the next arrives.
5. **Nothing is lost when motion is off.** Reduced motion, edit mode and no-JS show every scene as a readable static layout. A plain-text summary section ("What is X?") and the full SEO/GEO set are mandatory.

## Workflow

### 1. Read the brief (5 minutes, no code)
Collect: product/subject, audience and their pain in their own words, the one action we want, brand colours/fonts/logo, real material (screenshots, photos, numbers, customer names with permission), language and direction (fa/ar = RTL), deadline. Ask only for what blocks the story; mark the rest `[NEED: …]` in the page.

### 2. Find the world and the arc
Pick the **world**: the concrete thing the story happens in (a store, a factory line, a city, a document, a device, a body, a timeline, a supply chain, a code editor). Then pick an **arc** from `references/story-patterns.md` (zoom-in, journey, before/after, assemble, pull-back, day-in-the-life, problem-hunt). Combine at most two.

Write the storyboard as a table and show it to the user before building:

| Act | Scene | What the viewer sees (visual) | Camera / motion | Title (≤6 words) | Line (≤20 words) |
|---|---|---|---|---|---|

Typical shape: Act 1 hook (the world + the moment that matters) → Act 2 the problem made visible → Act 3 how it works (real screenshots) → Act 4 who it is for / scale → then normal sections (benefits, pricing, FAQ, CTA). 3–6 scenes per act, 4–5 acts max.

### 3. Design system
Use the brand palette from real assets (screenshots, logo), one accent, plus one semantic "alert" colour used only for problem moments. Stage (the cinematic block) is usually dark; content sections follow the system theme. Self-host the font. Icons from one library (Phosphor/Tabler), never hand-drawn. Persian/Arabic: never letter-spacing; numerals inside SVG need `direction="ltr"`. If design skills are installed (design-taste-frontend, emil-design-eng, ui-ux-pro-max), apply them for taste, motion curves and accessibility.

### 4. Build with the engine
Start from `assets/template/index.html`, `assets/engine/*` and `assets/vendor/*` (GSAP 3 + ScrollTrigger, free licence). Read `references/engine.md` for the API and the gotchas. In short:
- Each act is `<section class="story" id="…" style="--len:Nsvh">` with one sticky `.stage`; N ≈ (scenes + 1) × 100.
- Visual layers are `.scene` (full-bleed) or `.scene.side`; captions are `.cap[data-s=N]`; per-scene overlays are `.ov[data-s=N]`.
- Register each act: `StoryEngine.act(id, bounds, {layout, scene, frame, reset}, stops)` then `StoryEngine.start()`.
- Generate scene graphics as inline SVG (by hand-written JS/Python generators, not one-off drawings) so they stay crisp, editable and light. Real screenshots go in `.frame` overlays as WebP with width/height set and private data blurred.
- Ship as one self-contained HTML (`scripts/inline.py`) plus an `assets/` folder (font, images, og.png). Always hand the user the whole folder (zip), never the HTML alone.

### 5. Write the words (three passes)
1. Draft the captions from the storyboard.
2. Plain-language pass: replace jargon with the reader's words, one idea per sentence, active voice, numbers instead of adjectives.
3. Expert pass: check every claim is true for this product (no invented results, prices or customers); remove anything not in the brief; mark gaps `[NEED: …]`.
No em/en dashes in visible text; no filler intros ("In today's world…").

### 6. SEO / GEO (mandatory)
See `references/seo-geo.md`: unique title and description, one h1, logical h2/h3 (scene captions that are not real headings use `<p class="cap-t">`), plain-text "What is X?" section with the primary keyword in the first sentence, JSON-LD graph (Organization, WebSite, product type, WebPage, FAQPage only for answered questions, Offer only for published prices), OG/Twitter image 1200×630, canonical/hreflang, robots.txt allowing AI crawlers, sitemap.xml, llms.txt. Keep `noindex` while any `[NEED]` remains.

### 7. QA, then iterate (at least two rounds)
Run `node scripts/qa.js page.html out/` and look at every screenshot (desktop and phone). Fix and re-run. Checklist in `references/qa.md`. The usual failures: labels sitting on top of shapes, captions covering the subject, text under the top bar, a section taller than one screen inside the paging, hidden content in static mode, broken image paths when the HTML is sent alone.

### 8. Deliver
Zip the site folder; commit the source (generators + page) so it can be rebuilt; say what is still `[NEED]`, what was not tested (real phones), and how to edit text (in-page editor: open the file locally or add `?edit`).

## Files
- `assets/engine/story-engine.js`: acts, scene switching, one-gesture-one-step paging, act-to-act curtains, section exit fades, static fallback, `window.__actP(id,p)` test helper.
- `assets/engine/base.css`: tokens, stage, captions choreography, overlays, step dots, sections, form, editor, static mode, reduced motion. Change tokens, not structure.
- `assets/engine/editor.js`: in-page text editor (draft in localStorage, save back to .html). Load before the engine.
- `assets/engine/ui.js`: reveals, `[NEED]` counter, accessible demo form (inline errors, focusable summary, honeypot, endpoint via `data-endpoint`).
- `assets/template/index.html`: a working two-act example (zoom-in hero + screenshot act) to copy and replace.
- `scripts/inline.py`: inline CSS/JS into one HTML. `scripts/qa.js`: step-through screenshots + checks.
- `references/`: story patterns, engine API and gotchas, craft rules, SEO/GEO, QA checklist, components (form, pricing steps, FAQ).
