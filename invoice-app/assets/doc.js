/* DaranX — proforma / invoice editor on the A4 sheet (from the quotation template). */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var data = JSON.parse($('#docData').textContent);
  var doc = data.doc;
  var ro = !!data.readOnly;
  var body = document.body;
  var toFa = DX.toFa, parse = DX.parse, fmt = DX.fmt;

  function toEn(s) {
    return String(s == null ? '' : s)
      .replace(/[۰-۹]/g, function (c) { return c.charCodeAt(0) - 1776; })
      .replace(/[٠-٩]/g, function (c) { return c.charCodeAt(0) - 1632; });
  }
  function numOrNull(s) { s = String(s == null ? '' : s).trim(); return s === '' ? null : parse(s); }
  function text(el) { return (el.innerText || el.textContent || '').replace(/ /g, ' ').trim(); }
  function setText(el, s) { el.innerText = s || ''; if (!text(el)) el.innerHTML = ''; }

  /* ----- amount in Persian words ----- */
  var ON = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه'];
  var TE = ['ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده'];
  var TN = ['', '', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود'];
  var HU = ['', 'یکصد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد'];
  var SC = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون', 'کوادریلیون'];
  function w3(n) {
    var p = [], h = Math.floor(n / 100), r = n % 100;
    if (h) p.push(HU[h]);
    if (r) {
      if (r < 10) p.push(ON[r]);
      else if (r < 20) p.push(TE[r - 10]);
      else { var t = Math.floor(r / 10), o = r % 10; p.push(TN[t] + (o ? ' و ' + ON[o] : '')); }
    }
    return p.join(' و ');
  }
  function words(n) {
    n = Math.round(n);
    if (!isFinite(n) || n <= 0) return '';
    var g = []; while (n > 0) { g.push(n % 1000); n = Math.floor(n / 1000); }
    if (g.length > SC.length) return '';
    var out = [];
    for (var i = g.length - 1; i >= 0; i--) { if (g[i]) out.push(w3(g[i]) + (SC[i] ? ' ' + SC[i] : '')); }
    return out.join(' و ');
  }

  /* ----- dirty tracking: never lose unsaved edits silently ----- */
  var dirty = false;
  function markDirty() { if (!ro) dirty = true; }
  window.addEventListener('beforeunload', function (e) {
    if (dirty) { e.preventDefault(); e.returnValue = ''; }
  });
  function guard(e) {
    if (e.defaultPrevented || !dirty) return;
    if (window.confirm('تغییرات ذخیره نشده‌اند و از بین می‌روند. ادامه می‌دهید؟')) dirty = false;
    else e.preventDefault();
  }
  Array.prototype.forEach.call(document.querySelectorAll('form[data-guard]'), function (f) {
    f.addEventListener('submit', guard);
  });
  Array.prototype.forEach.call(document.querySelectorAll('a[data-guard]'), function (a) {
    a.addEventListener('click', guard);
  });

  /* ----- rows ----- */
  var tbody = $('#rows');
  var ROW = '<td class="c rn"></td>' +
    '<td><div class="ce title" contenteditable="true" data-ph="شرح کالا یا خدمت"></div></td>' +
    '<td class="c"><input class="qty" inputmode="decimal" placeholder="۱" aria-label="تعداد"></td>' +
    '<td class="c"><input class="price" inputmode="decimal" placeholder="۰" aria-label="قیمت واحد"></td>' +
    '<td class="c line"></td>' +
    '<td class="del c"><button type="button" class="rm" aria-label="حذف ردیف">×</button></td>';
  function rows() { return Array.prototype.slice.call(tbody.children); }
  function addRow(item, focus) {
    var tr = document.createElement('tr');
    tr.innerHTML = ROW;
    tbody.appendChild(tr);
    if (item) {
      setText($('.title', tr), item.title);
      $('.qty', tr).value = item.qty == null ? '' : fmt(item.qty);
      $('.price', tr).value = item.price == null ? '' : fmt(item.price);
    }
    if (ro) lock(tr);
    recalc();
    if (focus) $('.title', tr).focus();
    return tr;
  }

  function recalc() {
    var sum = 0;
    rows().forEach(function (tr, i) {
      $('.rn', tr).textContent = toFa(i + 1);
      var ps = $('.price', tr).value.trim(), qs = $('.qty', tr).value.trim();
      var has = ps !== '';
      var line = has ? Math.round(parse(ps) * (qs === '' ? 1 : parse(qs))) : 0;
      $('.line', tr).textContent = has ? fmt(line) : '';
      sum += line;
    });
    var disc = Math.round(parse($('#disc').value));
    var base = sum - disc;
    var vatOn = body.classList.contains('vat-on');
    var vat = vatOn ? Math.round(base * parse($('#rate').value) / 100) : 0;
    var pay = base + vat;
    $('#sumTot').textContent = fmt(sum);
    $('#vatAmt').textContent = fmt(vat);
    $('#pay').textContent = fmt(pay);
    $('#rowDisc').classList.toggle('zero', disc === 0);
    var w = words(pay);
    $('#words').textContent = w ? w + ' ' + data.unit : '';
  }

  tbody.addEventListener('input', recalc);
  tbody.addEventListener('click', function (e) {
    var b = e.target.closest('.rm');
    if (!b || ro) return;
    var tr = b.closest('tr');
    if (rows().length === 1) {
      $('.title', tr).innerHTML = ''; $('.qty', tr).value = ''; $('.price', tr).value = '';
    } else tr.remove();
    markDirty();
    recalc();
  });
  tbody.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.classList.contains('price')) {
      e.preventDefault();
      var tr = e.target.closest('tr');
      var next = tr.nextElementSibling || addRow(null, false);
      $('.title', next).focus();
    }
  });

  /* number inputs: Persian digits + separators when leaving a field */
  document.addEventListener('focusout', function (e) {
    var t = e.target;
    if (t.tagName === 'INPUT' && t.closest('.sheet') && t.id !== 'cust' && !t.classList.contains('rate') &&
        t.value.trim() !== '') {
      t.value = fmt(parse(t.value));
    }
  });
  $('#disc').addEventListener('input', recalc);
  $('#rate').addEventListener('input', recalc);
  $('#add').addEventListener('click', function () { addRow(null, true); markDirty(); });
  $('#sheet').addEventListener('input', markDirty);

  /* ----- plain-text editing helpers ----- */
  document.addEventListener('paste', function (e) {
    if (!e.target.closest || !e.target.closest('[contenteditable]')) return;
    e.preventDefault();
    var t = (e.clipboardData || window.clipboardData).getData('text/plain');
    document.execCommand('insertText', false, t);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.classList && e.target.classList.contains('one')) { e.preventDefault(); e.target.blur(); }
    if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) { e.preventDefault(); save(); }
  });
  document.addEventListener('input', function (e) {
    var t = e.target;
    if (t.classList && t.classList.contains('ce') && !text(t)) t.innerHTML = '';
  });

  /* ----- customer: pick an existing one to fill phone/address ----- */
  var custIn = $('#cust'), custList = $('#custList'), byKey = {};
  function key(s) {
    return String(s || '').replace(/ي|ى/g, 'ی').replace(/ك/g, 'ک').replace(/‌/g, ' ')
      .replace(/\s+/g, ' ').trim().toLowerCase();
  }
  data.customers.forEach(function (c) {
    byKey[key(c.name)] = c;
    var o = document.createElement('option');
    o.value = c.name;
    custList.appendChild(o);
  });
  custIn.addEventListener('change', function () {
    var c = byKey[key(custIn.value)];
    if (c) { setText($('#addr'), c.address); setText($('#phone'), c.phone); }
    setTitle();
  });

  /* ----- document type (only switchable before the first save) ----- */
  var TYPES = {
    qot: { fa: 'پیش‌فاکتور', en: 'QUOTATION', lbl: 'شماره پیش‌فاکتور:', pre: 'QOT-' },
    inv: { fa: 'فاکتور', en: 'INVOICE', lbl: 'شماره فاکتور:', pre: 'INV-' }
  };
  var type = doc.type;
  var notes = $('#notes'), notesDirty = false;
  notes.addEventListener('input', function () { notesDirty = true; });
  function fillNotes(list) {
    notes.innerHTML = '';
    (list || []).forEach(function (n) { var li = document.createElement('li'); li.textContent = n; notes.appendChild(li); });
  }
  function setTitle() {
    var c = custIn.value.trim();
    document.title = TYPES[type].fa + ' ' + text($('#docNo')) + (c ? ' — ' + c : '') + ' — DaranX';
  }
  function setType(k, init) {
    var prev = type, t = TYPES[k];
    type = k;
    body.setAttribute('data-type', k);
    $('#docFa').textContent = t.fa; $('#docEn').textContent = t.en; $('#numLbl').textContent = t.lbl;
    $('#docNo').setAttribute('data-ph', t.pre + '0000');
    var no = $('#docNo');
    if (data.nextNumbers && (text(no) === '' || text(no) === data.nextNumbers[prev])) no.textContent = data.nextNumbers[k];
    $('#tQot').setAttribute('aria-pressed', k === 'qot');
    $('#tInv').setAttribute('aria-pressed', k === 'inv');
    var sv = $('#save'); if (sv) sv.textContent = k === 'inv' ? 'صدور فاکتور' : 'ذخیره';
    if (!notesDirty && !init) fillNotes(data.defaultNotes[k]);
    setTitle();
  }
  if ($('#tQot')) {
    $('#tQot').addEventListener('click', function () { setType('qot'); });
    $('#tInv').addEventListener('click', function () { setType('inv'); });
  }
  $('#docNo').addEventListener('input', setTitle);

  $('#vatSw').addEventListener('change', function () {
    body.classList.toggle('vat-on', this.checked);
    markDirty();
    recalc();
  });

  /* ----- read-only (cancelled invoice) ----- */
  function lock(scope) {
    Array.prototype.forEach.call(scope.querySelectorAll('[contenteditable]'), function (el) {
      el.setAttribute('contenteditable', 'false');
    });
    Array.prototype.forEach.call(scope.querySelectorAll('input'), function (el) { el.readOnly = true; });
  }

  /* ----- collect & save ----- */
  function collect() {
    var number = text($('#docNo'));
    return {
      type: type,
      number: toEn(number),
      number_auto: !!(data.isNew && data.nextNumbers && number === data.nextNumbers[type]),
      date: toEn(text($('#date'))),
      cust_name: custIn.value.trim(),
      cust_address: text($('#addr')),
      cust_phone: text($('#phone')),
      items: rows().map(function (tr) {
        return { title: text($('.title', tr)), qty: numOrNull($('.qty', tr).value), price: numOrNull($('.price', tr).value) };
      }).filter(function (it) { return it.title !== '' || it.price !== null; }),
      discount: numOrNull($('#disc').value),
      vat_on: $('#vatSw').checked,
      vat_rate: numOrNull($('#rate').value),
      notes: (notes.innerText || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean)
    };
  }
  function save() {
    var btn = $('#save');
    if (ro || !btn || btn.disabled) return;
    var p = collect();
    if (!p.cust_name) { alert('نام مشتری را وارد کنید.'); custIn.focus(); return; }
    if (!p.items.length) { alert('حداقل یک ردیف کالا یا خدمت وارد کنید.'); return; }
    $('#payload').value = JSON.stringify(p);
    dirty = false;
    btn.disabled = true;
    $('#saveForm').submit();
  }
  if ($('#save')) $('#save').addEventListener('click', save);
  $('#pr').addEventListener('click', function () {
    if (dirty && !window.confirm('تغییرات هنوز ذخیره نشده‌اند. همین نسخه چاپ شود؟')) return;
    window.print();
  });

  /* ----- init ----- */
  custIn.value = doc.cust_name || '';
  setText($('#addr'), doc.cust_address);
  setText($('#phone'), doc.cust_phone);
  $('#date').textContent = toFa(doc.date || '');
  $('#docNo').textContent = doc.number || '';
  $('#disc').value = doc.discount ? fmt(doc.discount) : '';
  $('#rate').value = toFa(doc.vat_rate == null ? 10 : doc.vat_rate);
  $('#vatSw').checked = !!doc.vat_on;
  body.classList.toggle('vat-on', !!doc.vat_on);
  fillNotes(doc.notes);
  if (doc.items && doc.items.length) doc.items.forEach(function (it) { addRow(it, false); });
  else for (var i = 0; i < 4; i++) addRow(null, false);
  if (ro) { lock(document); custIn.readOnly = true; }
  if (data.isNew) setType(type, true); else setTitle();
  recalc();
  if (data.isNew && !custIn.value) custIn.focus();
})();
