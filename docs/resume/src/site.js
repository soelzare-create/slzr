/* Plan viewer: tap a plan to see it full screen. Pinch zoom stays with the browser.
   The phone's back button closes it (history entry), as do the close button, Escape and a tap on the backdrop. */
(function () {
  'use strict';
  var doc = document, plans = [].slice.call(doc.querySelectorAll('.plan'));
  if (!plans.length) return;
  var box = doc.createElement('div');
  box.className = 'lb'; box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.hidden = true;
  box.innerHTML = '<div class="lb-bar"><p class="lb-cap" id="lbCap"></p><button type="button" class="lb-x" aria-label="بستن">بستن</button></div>' +
    '<div class="lb-body"><img alt=""></div>';
  doc.body.appendChild(box);
  var img = box.querySelector('img'), cap = box.querySelector('.lb-cap'), btn = box.querySelector('.lb-x'), last = null, pushed = false;
  box.setAttribute('aria-labelledby', 'lbCap');

  function open(fig) {
    var src = fig.querySelector('img'), fc = fig.querySelector('figcaption');
    img.src = src.currentSrc || src.src; img.alt = src.alt; cap.textContent = fc && fc.firstChild ? fc.firstChild.textContent : '';
    last = fig.querySelector('.plan-btn'); box.hidden = false; doc.documentElement.classList.add('lb-open');
    requestAnimationFrame(function () { box.classList.add('on'); });
    btn.focus({ preventScroll: true });
    try { history.pushState({ lb: 1 }, ''); pushed = true; } catch (e) { pushed = false; }
  }
  function shut() {
    if (box.hidden) return;
    box.classList.remove('on'); doc.documentElement.classList.remove('lb-open');
    setTimeout(function () { box.hidden = true; img.removeAttribute('src'); }, 180);
    if (last) last.focus({ preventScroll: true });
  }
  function close() { if (pushed) { pushed = false; history.back(); } else shut(); }

  plans.forEach(function (fig) {
    var b = fig.querySelector('.plan-btn'); if (!b) return;
    b.addEventListener('click', function () { open(fig); });
  });
  btn.addEventListener('click', close);
  box.addEventListener('click', function (e) { if (e.target === box || e.target.classList.contains('lb-body')) close(); });
  addEventListener('popstate', function () { pushed = false; shut(); });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden) close(); });
})();
