// Encrypt a self-contained HTML page into a small loader page that decrypts it in the browser.
// Usage: node seal.mjs <in.html> <out.html>   → prints the key to append to the link as #k=<key>
import { readFileSync, writeFileSync } from 'node:fs';
const [, , inp, out] = process.argv;
const b64u = b => Buffer.from(b).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const raw = crypto.getRandomValues(new Uint8Array(32)), iv = crypto.getRandomValues(new Uint8Array(12));
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
.dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
@keyframes b{to{opacity:.2}}
@media (prefers-reduced-motion:reduce){.dot{animation:none}}
</style>
</head>
<body>
<div><div class="wm" dir="ltr">Daran<span>X</span></div>
<p id="msg">در حال باز کردن سند...</p><div id="dots"><i class="dot"></i><i class="dot"></i><i class="dot"></i></div></div>
<script id="sealed" type="application/octet-stream">${blob}</script>
<script>
/* The page content is AES-GCM encrypted; the key is only in the link (#k=...), which browsers never send to a server. */
(async function () {
  var KEY = 'dx-seal:' + location.pathname;
  function fail(t) { document.getElementById('msg').textContent = t; document.getElementById('dots').remove(); }
  try {
    var m = /[#&]k=([A-Za-z0-9_-]{43})/.exec(location.hash), k = m ? m[1] : null;
    try { if (k) sessionStorage.setItem(KEY, k); else k = sessionStorage.getItem(KEY); } catch (e) {}
    if (!k) return fail('لینک کامل نیست. لطفاً همان لینکی را که برایتان ارسال شده، کامل باز کنید.');
    if (!window.crypto || !crypto.subtle) return fail('این مرورگر سند را باز نمی‌کند. لطفاً لینک را در کروم یا سافاری باز کنید.');
    var b = function (s) { s = s.replace(/-/g, '+').replace(/_/g, '/'); var r = atob(s), u = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) u[i] = r.charCodeAt(i); return u; };
    var all = b(document.getElementById('sealed').textContent.trim());
    var key = await crypto.subtle.importKey('raw', b(k + '='), 'AES-GCM', false, ['decrypt']);
    var html = new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: all.slice(0, 12) }, key, all.slice(12)));
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
  } catch (e) { fail('سند باز نشد. لطفاً لینک ارسالی را دوباره و کامل باز کنید.'); }
})();
</script>
</body>
</html>
`;
writeFileSync(out, page);
console.log(b64u(raw));
