/* Scroll story controller.
   One pinned "stage" per section (CSS position:sticky). GSAP ScrollTrigger reports progress,
   a short tween smooths it, and each scene only toggles classes or sets transform/opacity.
   No window scroll listeners. Reduced motion and edit mode switch the whole story to a static layout. */
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
  var cfgEl = $('story-cfg');
  if (!window.gsap || !window.ScrollTrigger || !cfgEl) { body.classList.add('no-story'); return; }
  gsap.registerPlugin(ScrollTrigger);
  var cfg = JSON.parse(cfgEl.textContent);
  var acts = [], pageTriggers = [], statik = false, started = false;

  /* ---------- act factory ---------- */
  function Act(id, bounds, h) {
    var sec = $(id); if (!sec) return;
    var stage = sec.querySelector('.stage'), caps = [].slice.call(sec.querySelectorAll('.cap')), last = -1, st = { p: 0 }, trig;
    function sceneOf(p) { var s = 0; for (var i = 0; i < bounds.length; i++) if (p >= bounds[i]) s = i + 1; return s; }
    function render() {
      var sc = sceneOf(st.p);
      if (sc !== last) {
        caps.forEach(function (c) { c.classList.toggle('on', +c.getAttribute('data-s') === sc); });
        if (h.scene) h.scene(sc);
        last = sc;
      }
      if (h.frame) h.frame(st.p, sc);
    }
    var a = {
      id: id, sec: sec,
      start: function () {
        trig = ScrollTrigger.create({
          trigger: sec, start: 'top top', end: 'bottom bottom', invalidateOnRefresh: true,
          onUpdate: function (self) { gsap.to(st, { p: self.progress, duration: .45, ease: 'power3.out', overwrite: true, onUpdate: render }); },
          onRefresh: function (self) { st.p = self.progress; last = -1; if (h.layout) h.layout(stage.clientWidth, stage.clientHeight); render(); }
        });
      },
      jump: function (p) { st.p = p; last = -1; render(); },
      stop: function () {
        if (trig) trig.kill(); trig = null; gsap.killTweensOf(st); last = -1; st.p = 0;
        caps.forEach(function (c) { c.classList.remove('on'); });
        if (h.reset) h.reset();
      }
    };
    acts.push(a); return a;
  }

  /* ---------- hero: store plan -> zones -> zone -> aisle -> shelf ---------- */
  (function () {
    var sec = $('top'); if (!sec) return;
    var world = $('world'), cam = $('cam'), plan = $('plan'), zones = [].slice.call(doc.querySelectorAll('#zones .zone')), aisleLbl = $('aisleLbl'),
        cpath = $('cpath'), cdot = $('cdot'), aisleView = $('aisleView'), ao = $('aisleOuter'), ai = $('aisleInner'), shelfView = $('shelfView'),
        shelfSvg = $('shelfsvg'), hud = $('hud'), copy = $('storyCopy'), crumbs = [].slice.call(doc.querySelectorAll('.crumb')),
        gapEmpty = $('gapEmpty'), gapFilled = $('gapFilled'), okBadge = $('okBadge'), qrBeam = $('qrBeam'), qrRing = $('qrRing');
    var L = cfg.plan, Z = cfg.zone, A = cfg.aisle, K = {}, vw = 0, vh = 0, narrow = false, pathLen = 1, lastCrumb = -1;
    function layout(w, h) {
      vw = w; vh = h; narrow = vw / vh < 1.05;
      world.setAttribute('viewBox', '0 0 ' + vw + ' ' + vh);
      K.s0 = narrow ? Math.min(vw * .94 / L.w, vh * .38 / L.h) : Math.min(vw * .5 / L.w, vh * .78 / L.h);
      K.a0 = narrow ? [vw * .5, vh * .72] : [vw * .28, vh * .54];
      K.s1 = narrow ? K.s0 * 1.02 : K.s0 * 1.1;
      K.s2 = narrow ? Math.min(vw * .9 / Z.w, vh * .42 / Z.h) : Math.min(vw * .46 / Z.w, vh * .8 / Z.h);
      K.a2 = narrow ? [vw * .5, vh * .36] : [vw * .34, vh * .52];
      K.s3 = narrow ? Math.min(vw * .62 / A.w, vh * .4 / A.h) : Math.min(vw * .3 / A.w, vh * .88 / A.h);
      var t = narrow ? cfg.aisleP : cfg.aisleL, k = Math.max(vw / t.W, vh / t.H);
      K.tx = (vw - t.W * k) / 2 + t.tx * k; K.ty = (vh - t.H * k) / 2 + t.ty * k; K.vx = (vw - t.W * k) / 2 + t.vx * k; K.vy = (vh - t.H * k) / 2 + t.vy * k;
      K.push = narrow ? 3.4 : 3.0;
      pathLen = cpath.getTotalLength();
    }
    function camAt(p) {
      var S, cx, cy, ax, ay, t;
      if (p < .16) { S = K.s0; cx = 800; cy = 500; ax = K.a0[0]; ay = K.a0[1]; }
      else if (p < .30) { t = ease(seg(p, .16, .30)); S = lerp(K.s0, K.s1, t); cx = 800; cy = 500; ax = K.a0[0]; ay = K.a0[1]; }
      else if (p < .46) { t = ease(seg(p, .30, .46)); S = elerp(K.s1, K.s2, t); cx = lerp(800, Z.cx, t); cy = lerp(500, Z.cy, t); ax = lerp(K.a0[0], K.a2[0], t); ay = lerp(K.a0[1], K.a2[1], t); }
      else if (p < .58) { t = ease(seg(p, .46, .58)); S = elerp(K.s2, K.s3, t); cx = lerp(Z.cx, A.cx, t); cy = lerp(Z.cy, A.cy, t); ax = K.a2[0]; ay = K.a2[1]; }
      else { S = K.s3; cx = A.cx; cy = A.cy; ax = K.a2[0]; ay = K.a2[1]; }
      return [S, cx, cy, ax, ay];
    }
    function frame(p) {
      var f = 1 - seg(p, .05, .15);
      copy.style.opacity = f; copy.style.transform = (narrow ? '' : 'translateY(-50%) ') + 'translateY(' + (-26 * (1 - f)) + 'px)'; copy.style.visibility = f < .01 ? 'hidden' : 'visible';
      var c = camAt(p);
      cam.setAttribute('transform', 'translate(' + c[3].toFixed(1) + ' ' + c[4].toFixed(1) + ') scale(' + c[0].toFixed(4) + ') translate(' + (-c[1]).toFixed(1) + ' ' + (-c[2]).toFixed(1) + ')');
      plan.style.opacity = 1 - seg(p, .54, .60); world.style.visibility = p > .61 ? 'hidden' : 'visible';
      zones.forEach(function (z, i) {
        var show = seg(p, .15 + i * .012, .22 + i * .012), target = z.getAttribute('data-z') === '4', dim = target ? 0 : seg(p, .30, .40) * .82;
        z.style.opacity = show * (1 - dim);
        var lab = z.querySelector('.zlabel'), ico = z.querySelector('.zicon'), o = target ? 1 - seg(p, .36, .42) : 1 - seg(p, .28, .34);
        lab.style.opacity = o; ico.style.opacity = o;
      });
      aisleLbl.style.opacity = seg(p, .38, .46) * (1 - seg(p, .55, .6));
      var pe = seg(p, .17, .33);
      cpath.style.strokeDashoffset = pathLen * (1 - pe); cpath.style.opacity = pe > 0 ? .9 * (1 - seg(p, .4, .5)) : 0;
      var pt = cpath.getPointAtLength(pathLen * pe); cdot.setAttribute('transform', 'translate(' + pt.x.toFixed(1) + ' ' + pt.y.toFixed(1) + ')'); cdot.style.opacity = pe > 0 ? 1 - seg(p, .36, .44) : 0;
      aisleView.style.opacity = seg(p, .55, .62) * (1 - seg(p, .785, .81));
      var f1 = ease(seg(p, .58, .68)), f2 = ease(seg(p, .68, .78));
      ao.style.transformOrigin = K.vx + 'px ' + K.vy + 'px'; ao.style.transform = 'scale(' + elerp(1, 1.22, f1).toFixed(4) + ')';
      ai.style.transformOrigin = K.tx + 'px ' + K.ty + 'px'; ai.style.transform = 'scale(' + elerp(1, K.push, f2).toFixed(4) + ')';
      shelfView.style.opacity = seg(p, .77, .80);
      shelfSvg.style.transform = 'scale(' + (lerp(1.12, 1, ease(seg(p, .77, .84))) * (1 + .04 * seg(p, .84, 1))).toFixed(4) + ')';
      var fill = seg(p, .935, .97), ok = seg(p, .965, .985), flag = seg(p, .78, .82);
      gapEmpty.style.opacity = flag * (1 - fill); gapFilled.style.opacity = fill; gapFilled.style.transform = 'translateY(' + ((1 - fill) * -14).toFixed(1) + 'px)'; okBadge.style.opacity = ok;
      var sw = seg(p, .895, .935);
      qrBeam.style.opacity = sw > 0 && sw < 1 ? 1 : 0; qrBeam.setAttribute('y', (cfg.qr.qy + (cfg.qr.qs - 6) * (.5 - .5 * Math.cos(sw * Math.PI * 2))).toFixed(1));
      qrRing.style.opacity = seg(p, .885, .9) * (1 - seg(p, .97, .99));
      hud.classList.toggle('show', p > .17 && p < .995);
    }
    function scene(sc) {
      var ci = sc <= 1 ? 0 : sc === 2 ? 1 : sc === 3 ? 2 : 3;
      if (ci !== lastCrumb) { crumbs.forEach(function (el, i) { el.classList.toggle('on', i === ci); el.classList.toggle('done', i < ci); }); lastCrumb = ci; }
    }
    function reset() {
      world.setAttribute('viewBox', '40 40 1520 960'); cam.removeAttribute('transform');
      [world, plan, aisleLbl, cpath, cdot, aisleView, shelfView, gapFilled, okBadge, qrBeam, qrRing, copy, gapEmpty].forEach(function (e) { e.removeAttribute('style'); });
      zones.forEach(function (z) { z.removeAttribute('style'); z.querySelector('.zlabel').removeAttribute('style'); z.querySelector('.zicon').removeAttribute('style'); });
      [ao, ai, shelfSvg].forEach(function (e) { e.removeAttribute('style'); }); cdot.removeAttribute('transform'); hud.classList.remove('show'); lastCrumb = -1;
    }
    Act('top', [.16, .30, .46, .74, .90], { layout: layout, frame: frame, scene: scene, reset: reset });
  })();

  /* ---------- act: problem (pins on the plan) ---------- */
  (function () {
    var avis = $('avisP'); if (!avis) return;
    var svg = $('worldP'), cam = $('camP'), pins = [].slice.call(avis.querySelectorAll('.pin')), dets = [].slice.call(avis.querySelectorAll('.pdet'));
    var aw = 0, ah = 0, base = 1, cur = 0;
    var T = [[800, 500, 1], [1090, 500, 3.4], [280, 515, 2.6], [670, 505, 2.0], [680, 830, 2.8], [800, 215, 3.0], [1380, 515, 2.8]];
    function put(k, instant) {
      var c = T[k], S = base * c[2], t = 'translate(' + aw / 2 + 'px,' + ah / 2 + 'px) scale(' + S + ') translate(' + (-c[0]) + 'px,' + (-c[1]) + 'px)';
      if (instant) cam.style.transition = 'none'; cam.style.transform = t; if (instant) { void cam.getBoundingClientRect(); cam.style.transition = ''; }
    }
    Act('problem', [.1, .26, .42, .58, .74, .88], {
      layout: function () { aw = avis.clientWidth; ah = avis.clientHeight; svg.setAttribute('viewBox', '0 0 ' + aw + ' ' + ah); base = Math.min(aw * .94 / 1400, ah * .9 / 860); put(cur, true); },
      scene: function (sc) {
        cur = sc; avis.setAttribute('data-sc', sc); put(sc);
        pins.forEach(function (p) { var k = +p.getAttribute('data-k'); p.classList.toggle('act', k === sc); p.classList.toggle('show', sc > 0); });
        dets.forEach(function (d) { d.classList.toggle('on', +d.getAttribute('data-k') === sc); });
      },
      reset: function () { svg.setAttribute('viewBox', '40 40 1520 960'); cam.removeAttribute('style'); pins.forEach(function (p) { p.classList.remove('act'); p.classList.add('show'); }); dets.forEach(function (d) { d.classList.remove('on'); }); }
    });
  })();

  /* ---------- act: how it works (editor, sheet, compare, analysis) ---------- */
  (function () {
    var avis = $('avisH'); if (!avis) return; var ovs = [].slice.call(avis.querySelectorAll('.ov'));
    Act('how', [.12, .32, .54, .76], {
      scene: function (sc) { avis.setAttribute('data-sc', sc); ovs.forEach(function (o) { o.classList.toggle('on', +o.getAttribute('data-s') === sc); }); },
      reset: function () { avis.setAttribute('data-sc', 1); ovs.forEach(function (o) { o.classList.remove('on'); }); }
    });
  })();

  /* ---------- act: opening a new store ---------- */
  (function () {
    var avis = $('avisO'); if (!avis) return; var svg = $('worldO'), cam = $('camO'), ovs = [].slice.call(avis.querySelectorAll('.ov'));
    Act('opening', [.14, .42, .72], {
      layout: function () { var aw = avis.clientWidth, ah = avis.clientHeight; svg.setAttribute('viewBox', '0 0 ' + aw + ' ' + ah); var b = Math.min(aw * .94 / 1400, ah * .9 / 860); cam.style.transform = 'translate(' + aw / 2 + 'px,' + ah / 2 + 'px) scale(' + b + ') translate(-800px,-500px)'; },
      scene: function (sc) { avis.setAttribute('data-sc', sc); ovs.forEach(function (o) { o.classList.toggle('on', +o.getAttribute('data-s') === sc); }); },
      reset: function () { svg.setAttribute('viewBox', '40 40 1520 960'); cam.removeAttribute('style'); avis.setAttribute('data-sc', 1); }
    });
  })();

  /* ---------- act: who (store -> chain -> franchise network) ---------- */
  (function () {
    var avis = $('avisW'); if (!avis) return; var sts = [].slice.call(avis.querySelectorAll('.st')), hub = $('hub'), row = avis.querySelector('.nl-row'), rad = [].slice.call(avis.querySelectorAll('.nl-ring'));
    function pos(el, x, y, s, o) { el.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + s + ')'; el.style.opacity = o; }
    function lay(sc) {
      sts.forEach(function (st, i) {
        if (sc === 0) pos(st, 800, 470, i === 0 ? 1.1 : .2, i === 0 ? .55 : 0);
        else if (sc === 1) pos(st, 800, 470, i === 0 ? 1.5 : .2, i === 0 ? 1 : 0);
        else if (sc === 2) { if (i < 5) pos(st, cfg.rowX[i], 500, 1, 1); else pos(st, cfg.rowX[2], 500, .2, 0); }
        else pos(st, cfg.ring[i][0], cfg.ring[i][1], .78, 1);
      });
      pos(hub, 800, 450, sc >= 3 ? 1.05 : .4, sc >= 3 ? 1 : 0);
      row.classList.toggle('on', sc === 2); rad.forEach(function (l) { l.classList.toggle('on', sc >= 3); });
    }
    Act('who', [.14, .4, .7], { scene: lay, reset: function () { lay(3); } });
  })();

  /* ---------- page-level triggers (progress bar, nav state, dark/light top bar) ---------- */
  function pageStart() {
    var prog = $('prog'), tb = $('topbar'), navLinks = [].slice.call(doc.querySelectorAll('.nav a')), dark = {};
    pageTriggers.push(ScrollTrigger.create({ start: 0, end: 'max', onUpdate: function (s) { prog.style.transform = 'scaleX(' + s.progress.toFixed(4) + ')'; } }));
    [].slice.call(doc.querySelectorAll('.story,.interlude')).forEach(function (el, i) {
      pageTriggers.push(ScrollTrigger.create({ trigger: el, start: 'top 40px', end: 'bottom 40px', onToggle: function (s) { dark[i] = s.isActive; tb.classList.toggle('ondark', Object.keys(dark).some(function (k) { return dark[k]; })); } }));
    });
    navLinks.forEach(function (a) {
      var t = doc.querySelector(a.getAttribute('href')); if (!t) return;
      pageTriggers.push(ScrollTrigger.create({ trigger: t, start: 'top 45%', end: 'bottom 45%', onToggle: function (s) { a.classList.toggle('on', s.isActive); } }));
    });
  }

  /* ---------- lifecycle ---------- */
  function start() {
    if (started) return; started = true; statik = false; body.classList.remove('no-story');
    acts.forEach(function (a) { a.start(); }); pageStart(); ScrollTrigger.refresh();
  }
  function stop() {
    started = false; acts.forEach(function (a) { a.stop(); });
    pageTriggers.forEach(function (t) { t.kill(); }); pageTriggers = []; ScrollTrigger.refresh();
    body.classList.add('no-story'); statik = true;
  }
  new MutationObserver(function () {
    var ed = body.classList.contains('editing');
    if (ed && started) stop(); else if (!ed && !started && !RM) start();
  }).observe(body, { attributes: true, attributeFilter: ['class'] });
  if (RM) { acts.forEach(function (a) { a.stop(); }); body.classList.add('no-story'); statik = true; }
  else {
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
