# Story patterns

Pick one arc (two at most) and one concrete world. The world is what the camera looks at; the arc is how the camera moves through it. Every scene must be caused by the previous one.

| Arc | Camera | Fits | Example scenes |
|---|---|---|---|
| **Zoom-in** (whole → part → detail → the moment) | push in, scale up around a focus point | products that act on a place or object (retail, buildings, factories, maps, devices) | ActivePlano: store plan → zones → one zone → aisle → shelf with an empty slot → QR scan fixes it |
| **Pull-back** (detail → system → network) | scale down, more copies appear | scale, franchises, platforms, marketplaces | one store → a chain in a row → a hub with stores around it |
| **Journey** (step 1 → 2 → 3 along a path) | pan along a path, a dot travels | processes, onboarding, logistics, services | order placed → picked → shipped → delivered, each a stop on a route |
| **Before / after** | same frame, state changes (wipe, morph, fill) | improvement, cleanup, optimisation, design services | messy shelf → planned shelf; red chart → green chart |
| **Assemble** (pieces fly into a whole) | parts move into place | platforms, modular products, teams, "everything in one place" | separate tools collapse into one screen |
| **Problem hunt** (pins on the world) | jump between hotspots on one map | listing pains or features without a boring list | six pins on a plan, each a hidden cost |
| **Day in the life** | timeline/clock advances | apps used daily, roles, field work | 8:00 open → 11:00 audit → 18:00 report |
| **Data reveal** | numbers/charts draw themselves | analytics, finance, results | bars grow, line draws, one bar highlights |

## Building the storyboard
1. Hook scene: the world in one frame + the question the reader already has (their words). Headline ≤ 8 words.
2. 3–5 scenes that move closer to the moment that matters (the pain, the gap, the risk).
3. Turn: show the product doing the fix (real screenshot, real sheet, real UI), one capability per scene.
4. Proof / scale: who uses it, how far it reaches (pull-back works well).
5. Exit to normal sections: benefits (bento), plans/pricing, FAQ, final CTA. These are readable sections, not pinned acts.

## Tests for a good arc
- Read only the scene titles in order: do they form one sentence-like chain? If not, reorder or cut.
- Remove all text: can a stranger tell what changed between scenes? If not, the visual is not doing its job.
- Each scene answers "so what?" of the previous one.
- The first act ends on the moment that matters (the problem made visible), not on a feature list.

## Visual vocabulary that worked
- A camera group `<g class="cam">` with `translate(anchor) scale(s) translate(-focus)`; interpolate scale exponentially (`elerp`) so zooms feel constant-speed.
- A route path drawn with `stroke-dashoffset` and a dot moving along `getPointAtLength`.
- Breadcrumb HUD (Store › Zone › Aisle › Shelf) to keep the viewer oriented while zooming.
- Pins/hotspots with a number and an alert-colour ring; label below or above the pin, never on it.
- State change in place (empty slot → filled slot → "matches plan" badge).
- Real product screenshots in frames, with highlight boxes on the part being explained.
- Network/hub diagrams for scale; bars and lines that draw for data.
