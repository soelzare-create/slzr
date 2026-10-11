# Engine API and gotchas

## Markup
```html
<section class="story" id="hero" data-hero style="--len:600svh" aria-label="…">   <!-- data-hero: hide step dots on scene 0 -->
  <div class="stage">
    <svg class="scene" id="world" viewBox="…">…<g id="cam" class="cam">…</g></svg>  <!-- full-bleed visual -->
    <div class="scene side">… <div class="ov" data-s="2">…</div></div>          <!-- visual beside captions; per-scene overlays -->
    <div class="vignette"></div>
    <div class="story-copy">badge, h1, .verdict, .hero-actions</div>          <!-- hero only -->
    <div class="caps"><div class="cap" data-s="1"><p class="cap-t">Title</p><p>One line.</p></div>…</div>
  </div>
</section>
```
`--len` ≈ (number of scenes + 1) × 100svh. Captions are siblings in `.caps`; the engine toggles `.on` on the caption whose `data-s` equals the current scene and sets `data-sc` on the section (style scenes with `#id[data-sc="2"] …`).

## JS
```js
StoryEngine.act('hero', [.16,.30,.46,.74,.90], {   // boundaries between scenes (progress 0..1)
  layout(w, h) {},          // stage resized: recompute camera constants
  scene(sc) {},             // discrete changes: toggle classes, swap overlays (CSS transitions do the motion)
  frame(p, sc) {},          // continuous camera/zoom/path: set transform/opacity only
  reset() {}                // remove every inline style/attribute you set (static mode and editor depend on it)
}, [0,.27,.45,.66,.86,1]);  // stops: one rest point per scene (where a scroll gesture lands)
StoryEngine.start();        // once, after all acts
const { seg, ease, lerp, elerp, clamp } = StoryEngine.util;
```
`window.__actP('hero', .5)` jumps an act to a progress value (tests, deep links).

## How stepping works
- Stops = every act's scene stops + the top of every normal section (sections taller than the viewport are paged every 80% so nothing is skipped) + the end of the page.
- Wheel/touch are intercepted (non-passive) and turned into one glide to the next stop (0.7–1.25 s, power2.inOut). Ctrl+wheel (zoom) and multi-touch (pinch) pass through.
- Keyboard, scrollbar and anchor jumps fall back to ScrollTrigger snap in the scroll direction.
- Anchor clicks glide and move focus; focusing a control inside a hidden caption glides to its scene.
- Off in reduced motion and edit mode (body.no-story), native scrolling returns.

## Gotchas learned the hard way
- `html{scroll-behavior:smooth}` fights the glide: base.css sets `html.js{scroll-behavior:auto}`.
- Section tops are stops: give the first section after the story `padding-top ≥ nav height` or its heading hides under the top bar.
- Exit fades of normal sections must start late (`bottom 14%`), otherwise headings fade while still being read.
- A section that must be seen whole (pricing) must fit in one viewport at 1280×720: drop stair offsets, widen the container, tighten type.
- Every `frame()` value must be a pure function of progress (no accumulation), so jumping and reversing work.
- `transform` on SVG groups: use the `transform` attribute for SVG, CSS transform for HTML layers.
- Text in SVG: `paint-order:stroke` with a stage-coloured stroke for legibility over shapes; `direction="ltr"` on numbers in RTL pages (otherwise `text-anchor` flips and numbers sit on tick lines).
- Labels never on top of shapes: reserve empty space in the generator (move fixtures, not just labels), check every zoom level, bump label size on phones (`@media (max-aspect-ratio:21/20)`).
- Hide fine labels on phones if the caption already says the same thing.
- Captions sit on one side; keep the camera focus on the other side (anchor at ~36% width on desktop).
- Never `transition: all`; animate transform/opacity only; no scroll listeners.
- Editor: load editor.js before the engine; never put generated config inside `#doc`; implement `window.EDITOR_CLEAN(root)` to undo scene-set attributes before saving.
- The HTML references `assets/…`: always deliver the folder (zip), not the HTML alone.
