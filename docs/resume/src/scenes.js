/* DaranX resume scenes. Handlers only set transform/opacity/attributes; reset() removes everything they set. */
(function () {
  var E = window.StoryEngine; if (!E) return;
  var U = E.util, $ = U.$, W = 1600, H = 900;
  /* Scene drawings ship framed for the static page (no JS, reduced motion, old browsers): viewBox cropped to the
     content, "meet". While the story runs they use the full 1600x900 world with "slice" and a moving camera. */
  var SVGS = [].slice.call(document.querySelectorAll('svg.scene[data-static]')), live = false;
  function liveFrame() {
    if (live) return; live = true;
    SVGS.forEach(function (s) { s.setAttribute('viewBox', '0 0 1600 900'); s.setAttribute('preserveAspectRatio', 'xMidYMid slice'); });
  }
  function staticFrame() {
    live = false;
    SVGS.forEach(function (s) { s.setAttribute('viewBox', s.getAttribute('data-static')); s.setAttribute('preserveAspectRatio', 'xMidYMid meet'); });
  }

  /* Visible part of a 1600x900 "slice" viewBox, and where the subject should sit:
     desktop keeps the focus on the left (captions sit on the right in RTL), phones centre it and shrink to fit. */
  function view(contentW) {
    var asp = innerWidth / innerHeight, visW = asp < W / H ? H * asp : W, x0 = (W - visW) / 2, desk = asp > 1.05;
    return { ax: desk ? x0 + visW * .36 : W / 2, ay: desk ? H / 2 : H * .5, k: desk ? 1 : Math.min(1, visW * .92 / contentW) };
  }
  function cam(v, s, fx, fy) {
    return 'translate(' + v.ax.toFixed(1) + ' ' + v.ay.toFixed(1) + ') scale(' + (s * v.k).toFixed(4) + ') translate(' + (-fx).toFixed(1) + ' ' + (-fy).toFixed(1) + ')';
  }

  /* ---------- act 1: network -> three key projects -> Tourior's branches ---------- */
  var c1 = $('cam'), copy = $('storyCopy');
  var F0 = [680, 460], F1 = [590, 460], F2 = [330, 630];
  E.act('hero', [.3, .65], {
    frame: function (p) {
      liveFrame();
      var v = view(940), t1 = U.ease(U.seg(p, .1, .3)), t2 = U.ease(U.seg(p, .5, .82));
      var s = U.elerp(1, 1.06, t1) * U.elerp(1, 1.9, t2);
      var fx = U.lerp(U.lerp(F0[0], F1[0], t1), F2[0], t2), fy = U.lerp(U.lerp(F0[1], F1[1], t1), F2[1], t2);
      c1.setAttribute('transform', cam(v, s, fx, fy));
      var f = 1 - U.seg(p, .04, .14); copy.style.opacity = f; copy.style.visibility = f < .01 ? 'hidden' : 'visible';
    },
    reset: function () { staticFrame(); c1.removeAttribute('transform'); copy.removeAttribute('style'); }
  });


  /* ---------- act 2: Kala-Val, real plan then VLANs then support ---------- */
  var kvo = [].slice.call(document.querySelectorAll('#kalaval .ov'));
  E.act('kalaval', [.25, .5, .75], {
    scene: function (sc) { kvo.forEach(function (o) { o.classList.toggle('on', o.getAttribute('data-s').split(' ').indexOf(String(sc)) > -1); }); },
    reset: function () { kvo.forEach(function (o) { o.classList.remove('on'); }); }
  });

  /* ---------- act 3: three domains converge, then the four-step method ---------- */
  var c2 = $('cam2'), c3 = $('cam3'), vs = ['v1', 'v2', 'v3'].map($), line = $('mLine'), dot = $('mDot');
  var nodes = [].slice.call(document.querySelectorAll('#method .m-node'));
  var X = nodes.map(function (n) { return +n.querySelector('circle').getAttribute('cx'); });
  /* dot position along the four nodes, one segment per scroll step (stops: .38 .54 .70 1) */
  function along(p) {
    var ks = [.38, .54, .70, 1], u = 0;
    for (var i = 0; i < 3; i++) u += U.ease(U.seg(p, ks[i], ks[i + 1]));
    var i0 = Math.min(2, Math.floor(u)); return U.lerp(X[i0], X[i0 + 1], u - i0);
  }
  E.act('system', [.12, .3, .46, .62, .78], {
    scene: function (sc) { nodes.forEach(function (n, i) { n.classList.toggle('on', sc >= 2 && i <= sc - 2); }); },
    frame: function (p) {
      liveFrame();
      var v = view(1000), t = U.ease(U.seg(p, .03, .17));
      c2.setAttribute('transform', cam(v, 1, 540, 520)); c3.setAttribute('transform', cam(v, 1, 560, 500));
      vs.forEach(function (g) {
        var dx = +g.getAttribute('data-dx') * (1 - t), dy = +g.getAttribute('data-dy') * (1 - t);
        g.setAttribute('transform', 'translate(' + dx.toFixed(1) + ' ' + dy.toFixed(1) + ')');
      });
      var x = along(p); line.setAttribute('x2', x.toFixed(1)); dot.setAttribute('cx', x.toFixed(1));
    },
    reset: function () {
      c2.removeAttribute('transform'); c3.removeAttribute('transform'); vs.forEach(function (g) { g.removeAttribute('transform'); });
      line.setAttribute('x2', X[3]); dot.setAttribute('cx', X[3]); nodes.forEach(function (n) { n.classList.remove('on'); });
    }
  }, [0, .21, .38, .54, .70, 1]);

  E.start();
})();
