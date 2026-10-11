# Craft rules (taste, motion, words, accessibility)

## Visual
- One accent colour across the whole page; one alert colour for problem moments only. No purple/blue AI gradients unless the brand is that.
- Brand colours come from real assets (screenshots, logo), not from a palette generator.
- Stage: dark, faint grid or texture, vignette. Content sections: light/dark following the system.
- Shapes: one radius scale (e.g. buttons pill, cards 20px, inputs 12px).
- Icons from one library, same stroke weight; no emoji.
- Real screenshots beat illustrations for "how it works"; blur customer names.
- Bento for benefits (mixed cell sizes), steps for plans; avoid three equal cards.

## Motion (Emil Kowalski principles)
- Purpose for every motion: orientation (zoom), cause→effect (state change), focus (highlight). No decoration loops except subtle pulses on the active hotspot.
- Custom curves: ease-out `cubic-bezier(.23,1,.32,1)`, in-out `cubic-bezier(.77,0,.175,1)`. UI feedback < 300 ms; scene glides 0.7–1.25 s.
- Exit faster than enter; the old caption leaves (200 ms) before the new one arrives (delay 180 ms, children staggered 80 ms).
- Never animate from scale(0); start at .95–.985 with opacity.
- Buttons: `:active{transform:scale(.97)}`.

## Words
- Hero: problem in the reader's words (≤ 8 words) + one sentence with what it is and the outcome + 2 CTAs (primary, "see how it works").
- Caption: title ≤ 6 words, one line ≤ 20 words. One idea.
- Plain language, active voice, concrete nouns and numbers. Replace jargon with what the reader would say (e.g. "zone" → "section", "OOS" → "empty shelf").
- No invented claims, results, customers or prices. Unknowns become visible `[NEED: …]` chips (counted in the editor bar) and keep the page `noindex`.
- No em/en dashes in visible text; no "It's not X, it's Y" constructions.
- Persian/Arabic: no letter-spacing; ZWNJ (نیم‌فاصله) correct; Persian digits in text, LTR digits inside SVG charts.

## Accessibility
- Contrast ≥ 4.5:1 for text (check captions over imagery), focus rings visible, 44px touch targets.
- Skip link to the plain-text summary; scene SVGs `aria-hidden`, the meaning lives in captions.
- Form: visible labels, inline errors, focusable error summary, loading and success states, honeypot.
- Reduced motion = static readable layout, not a frozen frame.
