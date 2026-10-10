/* In-page text editor: edit any text inside #doc, autosave a draft in this browser, and save the page
   back to an .html file. Runs before the story script so a restored draft is in place before it starts. */
(function () {
  'use strict';
  var doc = document.getElementById('doc'), bar = document.getElementById('editbar'); if (!doc || !bar) return;
  var KEY = 'dx-edit-draft:' + location.pathname, FILE = decodeURIComponent(location.pathname.split('/').pop() || 'index.html');
  var $ = function (id) { return document.getElementById(id); };
  var bT = $('edToggle'), bS = $('edSave'), bD = $('edDone'), bX = $('edDiscard'), st = $('edStatus');
  var dirty = false, fileHandle = null, timer = 0, cfg = {};
  try { cfg = JSON.parse($('story-cfg').textContent); } catch (e) {}
  function status(m) { st.textContent = m || ''; }

  /* strip everything the runtime adds, so drafts and saved files are the clean source */
  var RUNTIME = ['in', 'on', 'act', 'show', 'ondark', 'done', 'sent', 'has'];
  function clean(root) {
    root.querySelectorAll('[contenteditable],[spellcheck]').forEach(function (e) { e.removeAttribute('contenteditable'); e.removeAttribute('spellcheck'); });
    RUNTIME.forEach(function (c) { root.querySelectorAll('.' + c).forEach(function (e) { e.classList.remove(c); }); });
    root.querySelectorAll('[style]').forEach(function (e) {
      var keep = (e.getAttribute('style') || '').split(';').map(function (d) { return d.trim(); }).filter(function (d) { return d.indexOf('--') === 0; });
      if (keep.length) e.setAttribute('style', keep.join(';')); else e.removeAttribute('style');
    });
    root.querySelectorAll('[data-sc],[aria-busy],[aria-invalid]').forEach(function (e) { e.removeAttribute('data-sc'); e.removeAttribute('aria-busy'); e.removeAttribute('aria-invalid'); });
    root.querySelectorAll('svg.world,svg.awsvg').forEach(function (s) { s.setAttribute('viewBox', '40 40 1520 960'); });
    ['cam', 'cdot'].forEach(function (id) { var e = root.querySelector('#' + id); if (e) e.removeAttribute('transform'); });
    var qb = root.querySelector('#qrBeam'); if (qb && cfg.qr) qb.setAttribute('y', cfg.qr.qy);
    root.querySelectorAll('#aisleInner,#aisleOuter').forEach(function (e) { e.removeAttribute('style'); });
    root.querySelectorAll('.steps').forEach(function (e) { e.remove(); });
    var pc = root.querySelector('#needCount'); if (pc) { pc.textContent = ''; pc.className = 'need-count'; }
    return root;
  }

  try {
    var d = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (d && d.html) { doc.innerHTML = d.html; dirty = true; setTimeout(function () { status('پیش‌نویس ذخیره‌نشدهٔ قبلی بازیابی شد.'); bX.hidden = false; bS.hidden = false; }, 0); }
  } catch (e) {}

  function saveDraft() {
    var c = clean(doc.cloneNode(true));
    try { localStorage.setItem(KEY, JSON.stringify({ html: c.innerHTML, t: Date.now() })); status('پیش‌نویس در این مرورگر نگه داشته شد؛ برای ماندگاری «ذخیرهٔ فایل» را بزنید.'); }
    catch (e) { status('ذخیرهٔ پیش‌نویس در این مرورگر ممکن نشد؛ حتماً «ذخیرهٔ فایل» را بزنید.'); }
  }
  function setEditing(on) {
    document.body.classList.toggle('editing', on);
    doc.setAttribute('contenteditable', on ? 'true' : 'false'); doc.setAttribute('spellcheck', 'false');
    doc.querySelectorAll('svg,canvas,input,button,.ov').forEach(function (e) { e.setAttribute('contenteditable', 'false'); });
    if (on) status('روی هر متن کلیک کنید و تغییر دهید.'); else { doc.removeAttribute('contenteditable'); if (!dirty) status(''); }
    bT.hidden = on; bD.hidden = !on; bS.hidden = !(on || dirty); bX.hidden = !dirty;
  }
  bT.addEventListener('click', function () { setEditing(true); });
  bD.addEventListener('click', function () { setEditing(false); });
  doc.addEventListener('input', function () { if (!document.body.classList.contains('editing')) return; dirty = true; bS.hidden = false; bX.hidden = false; clearTimeout(timer); timer = setTimeout(saveDraft, 600); });
  doc.addEventListener('paste', function (e) { if (!document.body.classList.contains('editing')) return; e.preventDefault(); document.execCommand('insertText', false, (e.clipboardData || window.clipboardData).getData('text/plain')); });
  doc.addEventListener('click', function (e) { if (document.body.classList.contains('editing') && e.target.closest('a,summary')) e.preventDefault(); }, true);

  function serialize() {
    var r = clean(document.documentElement.cloneNode(true));
    r.classList.remove('js'); r.classList.remove('can-edit'); if (!r.getAttribute('class')) r.removeAttribute('class'); r.removeAttribute('data-theme');
    r.querySelectorAll('canvas').forEach(function (c) { c.removeAttribute('width'); c.removeAttribute('height'); });
    r.querySelector('body').classList.remove('editing', 'no-story'); if (!r.querySelector('body').getAttribute('class')) r.querySelector('body').removeAttribute('class');
    var open = 0; r.querySelectorAll('#doc .need').forEach(function (n) { if (/NEED/.test(n.textContent)) open++; });
    var rb = r.querySelector('meta[name="robots"]'); if (rb) rb.setAttribute('content', open ? 'noindex,nofollow' : 'index,follow,max-image-preview:large,max-snippet:-1');
    var s = r.querySelector('#edStatus'); if (s) s.textContent = '';
    ['edSave', 'edDone', 'edDiscard'].forEach(function (id) { var b = r.querySelector('#' + id); if (b) b.setAttribute('hidden', ''); });
    var t = r.querySelector('#edToggle'); if (t) t.removeAttribute('hidden');
    return '<!doctype html>\n' + r.outerHTML;
  }
  function done(msg) { dirty = false; try { localStorage.removeItem(KEY); } catch (e) {} bX.hidden = true; if (!document.body.classList.contains('editing')) bS.hidden = true; status(msg); }
  bS.addEventListener('click', async function () {
    var html = serialize(), blob = new Blob([html], { type: 'text/html' });
    if (window.showSaveFilePicker) {
      try {
        if (!fileHandle) fileHandle = await showSaveFilePicker({ suggestedName: FILE, types: [{ description: 'HTML', accept: { 'text/html': ['.html'] } }] });
        var w = await fileHandle.createWritable(); await w.write(blob); await w.close();
        done('ذخیره شد. فایل را در همان پوشهٔ قبلی (کنار پوشهٔ assets) نگه دارید.'); return;
      } catch (e) { if (e && e.name === 'AbortError') { status('ذخیره لغو شد؛ پیش‌نویس هنوز در این مرورگر هست.'); return; } fileHandle = null; }
    }
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = FILE; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    done('فایل دانلود شد. آن را جایگزین فایل قبلی کنید (در همان پوشه، کنار پوشهٔ assets).');
  });
  bX.addEventListener('click', function () { if (!confirm('همهٔ تغییرات ذخیره‌نشده دور ریخته شود؟')) return; try { localStorage.removeItem(KEY); } catch (e) {} location.reload(); });
  addEventListener('keydown', function (e) { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's' && (dirty || document.body.classList.contains('editing'))) { e.preventDefault(); bS.click(); } });
})();
