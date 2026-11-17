// Encrypt a self-contained HTML page into a small loader page that decrypts it in the browser.
// Usage: node seal.mjs <in.html> <out.html> [key]   → prints the key to append to the link as #k=<key>
// Pass an existing key to re-seal an updated page without changing its link.
import { readFileSync, writeFileSync } from 'node:fs';
const [, , inp, out, given] = process.argv;
const b64u = b => Buffer.from(b).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const unb = s => new Uint8Array(Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64'));
const raw = given ? unb(given) : crypto.getRandomValues(new Uint8Array(32)), iv = crypto.getRandomValues(new Uint8Array(12));
const key = await crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt']);
const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, readFileSync(inp)));
const blob = Buffer.concat([Buffer.from(iv), Buffer.from(ct)]).toString('base64');
const page = `<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<title>سند اختصاصی | DaranX</title>
<meta property="og:type" content="website">
<meta property="og:title" content="پروپوزال اختصاصی داران‌ایکس">
<meta property="og:description" content="سندی که برای شما آماده شده است. برای دیدن، لینک را باز کنید.">
<style>
html,body{margin:0;height:100%}
body{display:grid;place-items:center;background:radial-gradient(120% 95% at 72% 8%,#3E7BB6,#153A62 45%,#081627 100%);
  color:#EAF1F8;font-family:system-ui,-apple-system,"Segoe UI",Tahoma,sans-serif;text-align:center;padding:16px}
.wm{font-weight:900;font-size:1.6rem}.wm span{color:#6FA3D2}
p{color:#AEC4DB;line-height:1.9;max-width:420px;margin:1rem auto 0}
.dot{display:inline-block;width:8px;height:8px;border-radius:9px;background:#6FA3D2;margin:1.2rem 3px 0;animation:b 1s infinite alternate}
form{margin-top:1.2rem;display:none;gap:.5rem;justify-content:center;flex-wrap:wrap}form.on{display:flex}
input{font:inherit;direction:ltr;width:min(320px,80vw);padding:.7rem .9rem;border-radius:12px;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.08);color:#fff}
button{font:inherit;font-weight:800;border:0;border-radius:999px;padding:.7rem 1.4rem;background:#fff;color:#153A62;cursor:pointer}
.dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
@keyframes b{to{opacity:.2}}
@media (prefers-reduced-motion:reduce){.dot{animation:none}}
</style>
</head>
<body>
<div><div class="wm" dir="ltr">Daran<span>X</span></div>
<p id="msg">در حال باز کردن سند...</p><div id="dots"><i class="dot"></i><i class="dot"></i><i class="dot"></i></div>
<form id="f"><input id="kin" aria-label="کد دسترسی" placeholder="کد دسترسی" autocomplete="off"><button>باز کردن سند</button></form></div>
<script id="sealed" type="application/octet-stream">${blob}</script>
<script>
/* The page content is AES-GCM encrypted; the key is only in the link (#k=...), which browsers never send to a server. */
(function () {
  var KEY = 'dx-seal:' + location.pathname, form = document.getElementById('f');
  function msg(t) { document.getElementById('msg').textContent = t; var d = document.getElementById('dots'); if (d) d.style.display = 'none'; }
  function ask(t) { msg(t); form.classList.add('on'); document.getElementById('kin').focus(); }
  function pick(s) { var m = /(?:^|[#?&])k=([A-Za-z0-9_-]{43})/.exec(s || ''); return m ? m[1] : null; }
  async function open(k) {
    if (!window.crypto || !crypto.subtle) return msg('این مرورگر سند را باز نمی‌کند. لطفاً لینک را در کروم یا سافاری باز کنید.');
    try {
      var b = function (s) { s = s.replace(/-/g, '+').replace(/_/g, '/'); var r = atob(s), u = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) u[i] = r.charCodeAt(i); return u; };
      var all = b(document.getElementById('sealed').textContent.trim());
      var key = await crypto.subtle.importKey('raw', b(k + '='), 'AES-GCM', false, ['decrypt']);
      var html = new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: all.slice(0, 12) }, key, all.slice(12)));
      try { sessionStorage.setItem(KEY, k); } catch (e) {}
      /* swap in the decrypted document, then re-create its scripts so they run in order */
      var nd = new DOMParser().parseFromString(html, 'text/html');
      document.replaceChild(document.adoptNode(nd.documentElement), document.documentElement);
      [].slice.call(document.querySelectorAll('script')).forEach(function (old) {
        var s = document.createElement('script');
        [].slice.call(old.attributes).forEach(function (a) { s.setAttribute(a.name, a.value); });
        s.text = old.text; old.parentNode.replaceChild(s, old);
      });
      /* the swapped page gets no load event of its own; send one so layout code measures the real page */
      setTimeout(function () { window.dispatchEvent(new Event('load')); }, 300);
    } catch (e) { ask('کد دسترسی درست نیست. لطفاً لینک کامل یا کد دسترسی را وارد کنید.'); }
  }
  form.addEventListener('submit', function (e) {
    e.preventDefault(); var v = document.getElementById('kin').value.trim(), k = pick(v) || (/^[A-Za-z0-9_-]{43}$/.test(v) ? v : null);
    if (!k) return ask('کد دسترسی درست نیست. لطفاً لینک کامل یا کد دسترسی را وارد کنید.');
    try { history.replaceState(null, '', location.pathname + '#k=' + k); } catch (e2) {}
    msg('در حال باز کردن سند...'); form.classList.remove('on'); open(k);
  });
  var k = pick(location.hash) || pick(location.search), saved = null;
  try { saved = sessionStorage.getItem(KEY); } catch (e) {}
  if (k || saved) open(k || saved);
  else ask('این سند خصوصی است. لینک کامل را باز کنید یا کد دسترسی را این‌جا وارد کنید.');
})();
</script>
</body>
</html>
`;
writeFileSync(out, page);
console.log(b64u(raw));
