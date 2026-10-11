/* Cinematic Story Engine
   One pinned stage per act (CSS position:sticky inside a tall <section class="story">).
   GSAP ScrollTrigger reports progress; a short tween smooths it; scene handlers only toggle classes
   or set transform/opacity. One wheel/swipe gesture = one step (scene). Reduced motion, edit mode and
   no-JS all fall back to a static, fully readable page (body.no-story).

   Usage (after gsap + ScrollTrigger, before your scenes file calls StoryEngine.start()):
     StoryEngine.act('hero', [.2,.45,.7], {            // id of <section class="story">, scene boundaries (0..1)
       layout: function (w, h) {},                      // optional: stage size changed
       scene:  function (sc) {},                        // scene index changed (0..bounds.length)
       frame:  function (p, sc) {},                     // every smoothed progress update (continuous camera moves)
       reset:  function () {}                           // story stopped: remove every inline style you set
     }, [0, .32, .58, 1]);                              // stops: rest point of each scene (one per scene)
     StoryEngine.start();
   Captions: <div class="cap" data-s="N"> inside the act get .on for scene N automatically. */
(function () {
  'use strict';
  var doc = document, body = doc.body;
  var $ = function (id) { return doc.getElementById(id); };
  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var seg = function (p, a, b) { return clamp((p - a) / (b - a), 0, 1); };
  var ease = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var elerp = function (a, b, t) { return Math.exp(lerp(Math.log(a), Math.log(b), t)); };
  var RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ok = !!(window.gsap && window.ScrollTrigger);
  var acts = [], pageTriggers = [], statik = false, started = false;
  window.StoryEngine = { util: { $: $, clamp: clamp, seg: seg, ease: ease, lerp: lerp, elerp: elerp }, act: Act, start: boot, reduced: RM };
  if (!ok) { body.classList.add('no-story'); window.StoryEngine.act = function () {}; window.StoryEngine.start = function () {}; return; }
  gsap.registerPlugin(ScrollTrigger);

  /* ---------- act factory ---------- */
  function Act(id, bounds, h, stops) {
    var sec = $(id); if (!sec) return;
    h = h || {};
    var stage = sec.querySelector('.stage'), caps = [].slice.call(sec.querySelectorAll('.cap')), last = -1, st = { p: 0 }, trig;
    var rail = doc.createElement('div'); rail.className = 'steps'; rail.setAttribute('aria-hidden', 'true');
    for (var k = 0; k <= bounds.length; k++) rail.appendChild(doc.createElement('i'));
    var dots = [].slice.call(rail.children), hideDots0 = sec.hasAttribute('data-hero');
    if (!stops) { stops = [0]; for (var b = 0; b < bounds.length; b++) stops.push(b === bounds.length - 1 ? 1 : (bounds[b] + bounds[b + 1]) / 2); }
    function sceneOf(p) { var s = 0; for (var i = 0; i < bounds.length; i++) if (p >= bounds[i]) s = i + 1; return s; }
    function render() {
      var sc = sceneOf(st.p);
      if (sc !== last) {
        caps.forEach(function (c) { c.classList.toggle('on', +c.getAttribute('data-s') === sc); });
        sec.setAttribute('data-sc', sc);
        if (h.scene) h.scene(sc);
        dots.forEach(function (d, i) { d.classList.toggle('on', i === sc); }); rail.style.opacity = hideDots0 && sc === 0 ? 0 : '';
        last = sc;
      }
      if (h.frame) h.frame(st.p, sc);
    }
    var a = {
      id: id, sec: sec, stops: stops,
      start: function () {
        if (!rail.parentNode) stage.appendChild(rail);
        trig = ScrollTrigger.create({
          trigger: sec, start: 'top top', end: 'bottom bottom', invalidateOnRefresh: true,
          onUpdate: function (self) { gsap.to(st, { p: self.progress, duration: .22, ease: 'power2.out', overwrite: true, onUpdate: render }); },
          onRefresh: function (self) { st.p = self.progress; last = -1; if (h.layout) h.layout(stage.clientWidth, stage.clientHeight); render(); }
        });
      },
      stop: function () {
        if (trig) trig.kill(); trig = null; gsap.killTweensOf(st); last = -1; st.p = 0; if (rail.parentNode) rail.remove();
        caps.forEach(function (c) { c.classList.remove('on'); }); sec.removeAttribute('data-sc');
        if (h.reset) h.reset();
      }
    };
    acts.push(a); return a;
  }

  /* ---------- page-level: progress bar, nav state, dark top bar over stories ---------- */
  function pageStart() {
    var prog = $('prog'), tb = $('topbar'), navLinks = [].slice.call(doc.querySelectorAll('.nav a[href^="#"]')), dark = {};
    if (prog) pageTriggers.push(ScrollTrigger.create({ start: 0, end: 'max', onUpdate: function (s) { prog.style.transform = 'scaleX(' + s.progress.toFixed(4) + ')'; } }));
    if (tb) [].slice.call(doc.querySelectorAll('.story,.on-dark')).forEach(function (el, i) {
      pageTriggers.push(ScrollTrigger.create({ trigger: el, start: 'top 40px', end: 'bottom 40px', onToggle: function (s) { dark[i] = s.isActive; tb.classList.toggle('ondark', Object.keys(dark).some(function (k) { return dark[k]; })); } }));
    });
    navLinks.forEach(function (a) {
      var t = doc.querySelector(a.getAttribute('href')); if (!t) return;
      pageTriggers.push(ScrollTrigger.create({ trigger: t, start: 'top 45%', end: 'bottom 45%', onToggle: function (s) { a.classList.toggle('on', s.isActive); } }));
    });
  }

  /* ---------- one scroll = one step ----------
     Every scene of every act is a stop; after the story, sections are stops too (long sections are paged so
     nothing is skipped). A scroll gesture moves to the next stop in its direction and the scene in between
     plays as motion. Native scrolling, scrollbar, keyboard and anchors keep working. */
  var stopsPx = [];
  function buildStops() {
    var vh = innerHeight, max = ScrollTrigger.maxScroll(window), pts = [0];
    acts.forEach(function (a) { var top = a.sec.offsetTop, run = a.sec.offsetHeight - vh; a.stops.forEach(function (q) { pts.push(top + run * q); }); });
    var last = acts[acts.length - 1], after = last ? last.sec.offsetTop + last.sec.offsetHeight : 0;
    [].slice.call(doc.querySelectorAll('main > section, .foot')).forEach(function (el) {
      var top = el.offsetTop, h = el.offsetHeight; if (top < after - 2) return;
      pts.push(top);
      if (h > vh * 1.05) { for (var y = top + vh * .8; y < top + h - vh; y += vh * .8) pts.push(y); pts.push(top + h - vh); }
    });
    pts.push(max);
    stopsPx = pts.map(function (y) { return clamp(Math.round(y), 0, max); }).sort(function (a, b) { return a - b; })
      .filter(function (y, i, arr) { return i === 0 || y - arr[i - 1] > vh * .1; });
    if (stopsPx[stopsPx.length - 1] !== max) { if (max - stopsPx[stopsPx.length - 1] < vh * .1) stopsPx[stopsPx.length - 1] = max; else stopsPx.push(max); }
  }
  function nearStop(y) { for (var i = 0; i < stopsPx.length; i++) if (Math.abs(stopsPx[i] - y) < 6) return true; return false; }
  function nextStop(cur, d) {
    var i; if (d > 0) { for (i = 0; i < stopsPx.length; i++) if (stopsPx[i] > cur + 6) return stopsPx[i]; }
    else { for (i = stopsPx.length - 1; i >= 0; i--) if (stopsPx[i] < cur - 6) return stopsPx[i]; }
    return null;
  }
  /* fallback for keyboard, scrollbar and anchor jumps: settle on the next stop in the scroll direction */
  function stepTo(v, self) {
    var max = ScrollTrigger.maxScroll(window), cur = self.scroll(); if (!max || !stopsPx.length || busy || nearStop(cur)) return cur / max;
    var t = nextStop(cur, self.direction); return t === null ? v : t / max;
  }
  /* wheel / swipe: one gesture = one step, played as a tween so the scene between two stops reads as motion */
  var busy = false, tw = null, proxy = { y: 0 };
  function glide(t, dur) {
    busy = true; proxy.y = scrollY; if (tw) tw.kill();
    tw = gsap.to(proxy, { y: t, duration: dur, ease: 'power2.inOut', onUpdate: function () { scrollTo(0, proxy.y); },
      onComplete: function () { tw = null; setTimeout(function () { busy = false; }, 140); } });
  }
  function step(d) {
    if (busy || statik) return;
    var cur = scrollY, t = nextStop(cur, d); if (t === null) return;
    var dist = Math.abs(t - cur) / innerHeight;
    glide(t, clamp(.55 + dist * .35, .7, 1.25));
  }
  function onWheel(e) { if (!started || e.ctrlKey || body.classList.contains('editing')) return; e.preventDefault(); if (Math.abs(e.deltaY) < 3) return; step(e.deltaY > 0 ? 1 : -1); }
  var ty0 = null;
  function onTouchStart(e) { ty0 = e.touches.length === 1 ? e.touches[0].clientY : null; }
  function onTouchMove(e) { if (!started || ty0 === null || e.touches.length > 1) return; if (e.cancelable) e.preventDefault(); var dy = ty0 - e.touches[0].clientY; if (Math.abs(dy) > 28) { step(dy > 0 ? 1 : -1); ty0 = null; } }
  function onFocus(e) {
    var cap = e.target.closest && e.target.closest('.cap'); if (!cap || cap.classList.contains('on') || !started) return;
    var a = acts.filter(function (x) { return x.sec.contains(cap); })[0]; if (!a) return;
    var q = a.stops[+cap.getAttribute('data-s')]; if (q === undefined) return;
    busy = false; glide(a.sec.offsetTop + (a.sec.offsetHeight - innerHeight) * q, .8);
  }
  function onAnchor(e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a || !started || body.classList.contains('editing')) return;
    var el = doc.querySelector(a.getAttribute('href')); if (!el) return;
    e.preventDefault();
    var y = el.classList.contains('story') ? el.offsetTop : Math.max(0, el.offsetTop - 0);
    glide(Math.min(y, ScrollTrigger.maxScroll(window)), .9 + Math.min(1, Math.abs(y - scrollY) / innerHeight / 12) * .6);
    if (history.pushState) history.pushState(null, '', a.getAttribute('href'));
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1'); el.focus({ preventScroll: true });
  }
  function transitionsStart() {
    var vh = innerHeight;
    pageTriggers.push(ScrollTrigger.create({
      start: 0, end: 'max', onRefresh: buildStops,
      snap: { snapTo: stepTo, delay: .12, duration: { min: .5, max: 1.1 }, ease: 'power2.inOut', inertia: false }
    }));
    ScrollTrigger.addEventListener('refreshInit', buildStops);
    addEventListener('wheel', onWheel, { passive: false });
    addEventListener('touchstart', onTouchStart, { passive: true }); addEventListener('touchmove', onTouchMove, { passive: false });
    doc.addEventListener('click', onAnchor); doc.addEventListener('focusin', onFocus);
    /* outgoing act: its stage recedes while the next act rises over it */
    acts.forEach(function (a) {
      var stage = a.sec.querySelector('.stage');
      fx.push(gsap.fromTo(stage, { opacity: 1, scale: 1 }, { opacity: .15, scale: .93, ease: 'none', immediateRender: false,
        scrollTrigger: { trigger: a.sec, start: 'bottom bottom', end: 'bottom top', scrub: .3 } }));
    });
    /* regular sections: blocks leave upward and fade as the next ones arrive */
    [].slice.call(doc.querySelectorAll('[data-reveal]:not([data-keep])')).filter(function (el) { return !el.closest('.story,form,details,.faq'); }).forEach(function (el) {
      fx.push(gsap.fromTo(el, { opacity: 1, y: 0 }, { opacity: 0, y: -36, ease: 'none', immediateRender: false,
        scrollTrigger: { trigger: el, start: 'bottom 14%', end: 'bottom -4%', scrub: .3, onToggle: function (s) { if (s.isActive) el.style.transition = 'none'; } } }));
    });
    doc.querySelectorAll('details').forEach(function (d) { d.addEventListener('toggle', refreshSoon); });
  }
  var fx = [], rT = 0;
  function refreshSoon() { clearTimeout(rT); rT = setTimeout(function () { ScrollTrigger.refresh(); }, 120); }
  function transitionsStop() {
    ScrollTrigger.removeEventListener('refreshInit', buildStops);
    removeEventListener('wheel', onWheel); removeEventListener('touchstart', onTouchStart); removeEventListener('touchmove', onTouchMove);
    doc.removeEventListener('click', onAnchor); doc.removeEventListener('focusin', onFocus); if (tw) tw.kill(); tw = null; busy = false;
    fx.forEach(function (t) { if (t.scrollTrigger) t.scrollTrigger.kill(); t.kill(); gsap.set(t.targets(), { clearProps: 'opacity,transform,transition,scale' }); }); fx = [];
  }

  /* ---------- lifecycle ---------- */
  function start() {
    if (started) return; started = true; statik = false; body.classList.remove('no-story');
    acts.forEach(function (a) { a.start(); }); pageStart(); transitionsStart(); ScrollTrigger.refresh();
  }
  function stop() {
    started = false; acts.forEach(function (a) { a.stop(); }); transitionsStop();
    pageTriggers.forEach(function (t) { t.kill(); }); pageTriggers = []; ScrollTrigger.refresh();
    body.classList.add('no-story'); statik = true;
  }
  function boot() {
    new MutationObserver(function () {
      var ed = body.classList.contains('editing');
      if (ed && started) stop(); else if (!ed && !started && !RM) start();
    }).observe(body, { attributes: true, attributeFilter: ['class'] });
    if (RM || body.classList.contains('editing')) { acts.forEach(function (a) { a.stop(); }); body.classList.add('no-story'); statik = true; return; }
    start();
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { ScrollTrigger.refresh(); });
    addEventListener('load', function () { ScrollTrigger.refresh(); });
  }
  /* test and deep-link helper: jump an act to a progress value (0..1) */
  window.__actP = function (id, p) {
    var a = acts.filter(function (x) { return x.id === id; })[0]; if (!a) return;
    var tot = a.sec.offsetHeight - innerHeight; scrollTo({ top: a.sec.offsetTop + tot * p, behavior: 'instant' });
  };
})();
