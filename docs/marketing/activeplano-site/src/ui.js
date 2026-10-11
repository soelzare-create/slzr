/* UI behaviour: scroll reveals (IntersectionObserver), open-item counter for the draft, and the demo form. */
(function () {
  'use strict';
  var doc = document, body = doc.body, $ = function (id) { return doc.getElementById(id); };
  var FA = '۰۱۲۳۴۵۶۷۸۹', fa = function (n) { return String(n).replace(/\d/g, function (d) { return FA[d]; }); };
  var latin = function (s) { return String(s).replace(/[۰-۹]/g, function (d) { return FA.indexOf(d); }).replace(/[٠-٩]/g, function (d) { return d.charCodeAt(0) - 1632; }); };

  /* ---- reveals ---- */
  var items = [].slice.call(doc.querySelectorAll('[data-reveal]'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { threshold: .15, rootMargin: '0px 0px -6% 0px' });
    items.forEach(function (el) { io.observe(el); });
  } else items.forEach(function (el) { el.classList.add('in'); });
  new MutationObserver(function () { if (body.classList.contains('editing')) items.forEach(function (el) { el.classList.add('in'); }); }).observe(body, { attributes: true, attributeFilter: ['class'] });

  /* ---- draft markers: count what is still open, unwrap chips that were edited ---- */
  var docEl = $('doc'), cnt = $('needCount');
  function needs() {
    [].slice.call(docEl.querySelectorAll('.need')).forEach(function (n) { if (!/NEED/.test(n.textContent)) n.classList.remove('need'); });
    if (!cnt) return;
    var n = docEl.querySelectorAll('.need').length;
    cnt.textContent = n ? fa(n) + ' مورد تکمیل‌نشده' : 'همه‌چیز تکمیل است';
    cnt.className = 'need-count' + (n ? ' has' : '');
  }
  needs(); docEl.addEventListener('input', needs);
  new MutationObserver(function () { if (body.classList.contains('editing')) [].slice.call(docEl.querySelectorAll('details')).forEach(function (d) { d.open = true; }); }).observe(body, { attributes: true, attributeFilter: ['class'] });

  /* ---- demo form: labels above, specific inline errors, focusable summary, loading + success states ---- */
  var form = $('demoForm'); if (!form) return;
  var summary = $('errsum'), list = $('errlist'), msg = $('formMsg'), btn = $('demoBtn');
  var RULES = {
    name: function (v) { return v.length < 3 ? 'نام و نام خانوادگی را وارد کنید.' : ''; },
    company: function (v) { return v.length < 2 ? 'نام فروشگاه یا شرکت را وارد کنید.' : ''; },
    phone: function (v) { var d = latin(v).replace(/[\s\-()+]/g, ''); return !d ? 'شمارهٔ تماس را وارد کنید.' : (!/^\d{7,15}$/.test(d) ? 'شمارهٔ تماس درست نیست؛ فقط عدد وارد کنید.' : ''); },
    branches: function (v) { return v && !/^\d{1,5}$/.test(latin(v).trim()) ? 'تعداد شعبه را فقط با عدد بنویسید.' : ''; }
  };
  function check(input) {
    var r = RULES[input.name]; if (!r) return true;
    var e = r(input.value.trim()), p = $('err-' + input.name);
    input.setAttribute('aria-invalid', e ? 'true' : 'false'); if (p) p.textContent = e; return !e;
  }
  [].slice.call(form.querySelectorAll('input[name]')).forEach(function (i) { i.addEventListener('blur', function () { if (i.value || i.getAttribute('aria-invalid') === 'true') check(i); }); i.addEventListener('input', function () { if (i.getAttribute('aria-invalid') === 'true') check(i); }); });
  form.addEventListener('submit', function (ev) {
    ev.preventDefault(); msg.textContent = '';
    var bad = [].slice.call(form.querySelectorAll('input[name]')).filter(function (i) { return !check(i); });
    if (bad.length) {
      list.innerHTML = ''; bad.forEach(function (i) { var li = doc.createElement('li'), a = doc.createElement('a'); a.href = '#' + i.id; a.textContent = $('err-' + i.name).textContent; li.appendChild(a); list.appendChild(li); });
      summary.classList.add('on'); summary.focus(); return;
    }
    summary.classList.remove('on');
    var data = {}; [].slice.call(form.elements).forEach(function (el) { if (el.name) data[el.name] = el.value.trim(); });
    if (data.website) return; /* honeypot */
    var ep = form.getAttribute('data-endpoint');
    if (!ep) { msg.textContent = 'مقصد ارسال فرم هنوز تنظیم نشده است (نسخهٔ پیش‌نویس).'; return; }
    btn.setAttribute('aria-busy', 'true'); msg.textContent = 'در حال ارسال...';
    fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
      .then(function (r) { if (!r.ok) throw 0; form.reset(); form.classList.add('sent'); var h = $('okTitle'); if (h) { h.setAttribute('tabindex', '-1'); h.focus(); } })
      .catch(function () { msg.textContent = 'ارسال انجام نشد. لطفاً دوباره تلاش کنید.'; })
      .then(function () { btn.removeAttribute('aria-busy'); });
  });
})();
