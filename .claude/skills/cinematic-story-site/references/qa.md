# QA checklist (run at least two rounds)

Run `node scripts/qa.js page.html qa-out` and open every screenshot.

## Story
- [ ] Titles read in order form one logical chain; no scene can be swapped.
- [ ] With text hidden, the visuals still show what changed.
- [ ] Every scene has ≤ ~25 words on screen (qa.js prints words per caption).

## Legibility (every stop, desktop 1440×900 and 1920×960, phone 390×844)
- [ ] No label on top of a shape, line or another label; numbers not struck through by ticks.
- [ ] Caption never covers the subject of its scene.
- [ ] Nothing under the top bar at section stops.
- [ ] Phone: map/scene labels large enough (≥ ~11px rendered); fine labels hidden if the caption repeats them.

## Motion
- [ ] One wheel tick / swipe = one stop, both directions; no skipped content in tall sections.
- [ ] Old caption fully leaves before the new one; no empty glass box mid-transition.
- [ ] Act-to-act curtain: outgoing stage recedes, next rises.
- [ ] Reduced motion: static layout, all scenes readable (`reduced-motion-full.png`).

## Function
- [ ] No JS errors; no horizontal overflow.
- [ ] Nav links glide to sections and update the URL; skip link works; focus visible.
- [ ] Form: errors inline + summary; success state; endpoint set (or the "not configured" message shows).
- [ ] Editor: edit, save, draft restore; saved file has no runtime classes/styles.
- [ ] Assets load when the folder is opened from a zip (relative paths).

## SEO/GEO
- [ ] One h1, logical headings, summary section, JSON-LD parses, robots matches [NEED] state, OG image exists, robots.txt/sitemap/llms.txt present.
