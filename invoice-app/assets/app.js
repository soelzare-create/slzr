/* DaranX — small page helpers shared by every screen. Loaded in <head>. */
(function () {
  'use strict';
  var root = document.documentElement;

  // Theme: restore the saved choice before first paint (the sheet stays paper-white).
  try {
    var saved = localStorage.getItem('dx-doc-theme');
    if (saved) root.setAttribute('data-theme', saved);
  } catch (e) { /* storage blocked */ }

  var FA = '۰۱۲۳۴۵۶۷۸۹';
  function toFa(s) { return String(s).replace(/\d/g, function (d) { return FA[d]; }); }
  function parse(s) {
    s = String(s == null ? '' : s)
      .replace(/[۰-۹]/g, function (c) { return c.charCodeAt(0) - 1776; })
      .replace(/[٠-٩]/g, function (c) { return c.charCodeAt(0) - 1632; })
      .replace(/٫/g, '.').replace(/[,٬،\s]/g, '');
    var n = parseFloat(s);
    return isFinite(n) ? n : 0;
  }
  var nf;
  try { nf = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 2 }); } catch (e) { nf = null; }
  function fmt(n) {
    return nf ? nf.format(n) : toFa(String(Math.round(n * 100) / 100).replace(/\B(?=(\d{3})+(?!\d))/g, '٬'));
  }
  window.DX = { toFa: toFa, parse: parse, fmt: fmt };

  document.addEventListener('DOMContentLoaded', function () {
    var tt = document.getElementById('tt');
    if (tt) {
      tt.addEventListener('click', function () {
        var cur = root.getAttribute('data-theme');
        var dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
        var next = dark ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('dx-doc-theme', next); } catch (e) { /* ignore */ }
      });
    }

    // <form data-confirm="…"> asks before submitting.
    document.addEventListener('submit', function (e) {
      var msg = e.target.getAttribute && e.target.getAttribute('data-confirm');
      if (msg && !window.confirm(msg)) e.preventDefault();
    }, true);

    // Money inputs: Persian digits + thousands separators when leaving the field.
    document.addEventListener('focusout', function (e) {
      var t = e.target;
      if (t.classList && t.classList.contains('money') && t.value.trim() !== '') {
        t.value = fmt(parse(t.value));
      }
    });

    Array.prototype.forEach.call(document.querySelectorAll('[data-print]'), function (b) {
      b.addEventListener('click', function () { window.print(); });
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-autosubmit]'), function (el) {
      el.addEventListener('change', function () { el.form.submit(); });
    });

    // Close an open "more" menu when clicking elsewhere.
    document.addEventListener('click', function (e) {
      Array.prototype.forEach.call(document.querySelectorAll('details.more[open]'), function (d) {
        if (!d.contains(e.target)) d.removeAttribute('open');
      });
    });
  });
})();
