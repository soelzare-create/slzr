<?php
/**
 * The proforma/invoice editor — your DaranX template, live: edit on the sheet,
 * save, print / PDF. Saving an invoice is what puts its amount on the
 * customer's account.
 */
defined('APP_DIR') || exit;

$id = (int) query('id');
$isNew = $id === 0;
$error = null;
$draft = null;

if ($isNew) {
    $type = query('new') === 'inv' ? 'inv' : 'qot';
    $doc = [
        'id' => 0, 'type' => $type, 'number' => doc_next_number($type), 'date' => jtoday(),
        'customer_id' => 0, 'cust_name' => '', 'cust_address' => '', 'cust_phone' => '',
        'discount' => 0, 'vat_on' => 0, 'vat_rate' => (float) setting('vat_rate'),
        'notes' => implode("\n", default_notes($type)), 'status' => 'active', 'source_id' => null, 'total' => 0,
    ];
    $prefill = customer_get((int) query('customer'));
    if ($prefill) {
        $doc['cust_name'] = $prefill['name'];
        $doc['cust_address'] = $prefill['address'];
        $doc['cust_phone'] = $prefill['phone'];
    }
    $items = [];
} else {
    $doc = doc_get($id);
    if (!$doc) {
        not_found();
    }
    $type = $doc['type'];
    $items = doc_items($id);
}
$readOnly = !$isNew && $doc['status'] === 'cancelled';

if (is_post()) {
    $payload = json_decode(post('payload'), true);
    if ($readOnly) {
        $error = 'فاکتور باطل‌شده قابل ویرایش نیست؛ اگر لازم است اول آن را بازگردانی کنید.';
    } elseif (!is_array($payload)) {
        $error = 'اطلاعات ارسالی نامعتبر است. دوباره تلاش کنید.';
    } else {
        if ($isNew) {
            $type = ($payload['type'] ?? '') === 'inv' ? 'inv' : 'qot';
        }
        try {
            $savedId = doc_save(doc_validate($payload, $type), $isNew ? null : $id);
            if ($type === 'qot') {
                flash('ok', 'پیش‌فاکتور ذخیره شد.');
            } elseif ($isNew) {
                flash('ok', 'فاکتور صادر شد و مبلغ آن به بدهی مشتری اضافه شد.');
            } else {
                flash('ok', 'فاکتور ذخیره شد و حساب مشتری به‌روز شد.');
            }
            redirect('doc', ['id' => $savedId]);
        } catch (UserError $ex) {
            $error = $ex->getMessage();
            $draft = $payload;
        }
    }
}

// --- What the editor script starts from -------------------------------------
$view = [
    'type' => $type,
    'number' => $doc['number'],
    'number_auto' => $isNew,
    'date' => $doc['date'],
    'cust_name' => $doc['cust_name'],
    'cust_address' => $doc['cust_address'],
    'cust_phone' => $doc['cust_phone'],
    'items' => $items,
    'discount' => (float) $doc['discount'],
    'vat_on' => (bool) $doc['vat_on'],
    'vat_rate' => (float) $doc['vat_rate'],
    'notes' => array_values(array_filter(explode("\n", (string) $doc['notes']), 'strlen')),
];
if ($draft) {
    // Re-show what the user typed after a validation error (values only).
    foreach (['number', 'date', 'cust_name', 'cust_address', 'cust_phone'] as $k) {
        if (isset($draft[$k]) && is_scalar($draft[$k])) {
            $view[$k] = (string) $draft[$k];
        }
    }
    $view['number_auto'] = $isNew && !empty($draft['number_auto']);
    $view['items'] = [];
    foreach ((is_array($draft['items'] ?? null) ? $draft['items'] : []) as $it) {
        if (is_array($it)) {
            $view['items'][] = [
                'title' => is_scalar($it['title'] ?? null) ? (string) $it['title'] : '',
                'qty' => is_numeric($it['qty'] ?? null) ? (float) $it['qty'] : null,
                'price' => is_numeric($it['price'] ?? null) ? (float) $it['price'] : null,
            ];
        }
    }
    $view['discount'] = is_numeric($draft['discount'] ?? null) ? (float) $draft['discount'] : 0;
    $view['vat_on'] = !empty($draft['vat_on']);
    $view['vat_rate'] = is_numeric($draft['vat_rate'] ?? null) ? (float) $draft['vat_rate'] : $view['vat_rate'];
    $view['notes'] = array_values(array_filter(is_array($draft['notes'] ?? null) ? $draft['notes'] : [], 'is_string'));
}

$customers = [];
foreach (db()->query('SELECT name, phone, address FROM customers ORDER BY name') as $c) {
    $customers[] = $c;
}
$data = [
    'doc' => $view,
    'isNew' => $isNew,
    'readOnly' => $readOnly,
    'unit' => setting('unit'),
    'nextNumbers' => $isNew ? ['qot' => doc_next_number('qot'), 'inv' => doc_next_number('inv')] : null,
    'defaultNotes' => ['qot' => default_notes('qot'), 'inv' => default_notes('inv')],
    'customers' => $customers,
];

// --- Status shown around a saved document ----------------------------------
$customer = $isNew ? null : customer_get((int) $doc['customer_id']);
$converted = (!$isNew && $type === 'qot') ? doc_invoice_of($id) : null;
$source = (!$isNew && $doc['source_id']) ? doc_get((int) $doc['source_id']) : null;
$left = null;
if (!$isNew && $type === 'inv' && $doc['status'] === 'active') {
    $left = invoice_remaining((int) $doc['customer_id'])[$id] ?? (float) $doc['total'];
}

$phones = array_values(array_filter(array_map('trim', explode("\n", setting('phones'))), 'strlen'));
$website = setting('website');
$websiteHref = 'https://' . preg_replace('~^https?://~i', '', strtolower($website));

$title = $isNew ? DOC_NAMES[$type] . ' جدید' : DOC_NAMES[$type] . ' ' . $doc['number'];
layout_start($title, $type, [
    'sheet' => true,
    'error' => $error,
    'body_attrs' => ' data-type="' . e($type) . '"' . ($readOnly ? ' data-ro="1"' : ''),
]);

/** tel: link target for a phone typed in settings (Tehran numbers get +9821). */
function tel_href(string $phone): string
{
    $d = preg_replace('/\D+/', '', en_digits($phone));
    if (strpos($d, '0') === 0) {
        $d = '+98' . substr($d, 1);
    } elseif (strlen($d) === 8) {
        $d = '+9821' . $d;
    }
    return 'tel:' . $d;
}
?>
<div class="docbar no-print">
  <div class="in">
    <?php if ($isNew): ?>
      <div class="seg" role="group" aria-label="نوع سند">
        <button type="button" id="tQot" aria-pressed="<?= $type === 'qot' ? 'true' : 'false' ?>">پیش‌فاکتور</button>
        <button type="button" id="tInv" aria-pressed="<?= $type === 'inv' ? 'true' : 'false' ?>">فاکتور</button>
      </div>
    <?php else: ?>
      <a class="btn btn-ghost btn-sm" href="<?= e(url('docs', ['type' => $type])) ?>" data-guard>→ <?= $type === 'inv' ? 'فاکتورها' : 'پیش‌فاکتورها' ?></a>
    <?php endif; ?>

    <label class="chk"><input type="checkbox" id="vatSw"<?= $readOnly ? ' disabled' : '' ?>> مالیات بر ارزش افزوده</label>

    <?php if ($readOnly): ?>
      <span class="badge muted">باطل‌شده</span>
    <?php elseif ($left !== null): ?>
      <?= invoice_badge($doc, [$id => $left]) ?>
    <?php elseif ($converted): ?>
      <a class="badge ok" href="<?= e(url('doc', ['id' => $converted['id']])) ?>" data-guard>فاکتور شد: <span dir="ltr"><?= e($converted['number']) ?></span></a>
    <?php endif; ?>

    <span class="spacer"></span>

    <?php if (!$readOnly): ?>
      <button type="button" class="btn btn-primary" id="save"><?= $isNew && $type === 'inv' ? 'صدور فاکتور' : 'ذخیره' ?></button>
    <?php endif; ?>
    <button type="button" class="btn btn-ghost" id="pr">چاپ / PDF</button>

    <?php if (!$isNew && $type === 'qot' && !$converted): ?>
      <form method="post" action="<?= e(url('doc_action')) ?>" data-guard
            data-confirm="این پیش‌فاکتور به فاکتور تبدیل شود؟ مبلغ فاکتور به بدهی مشتری اضافه می‌شود.">
        <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="convert">
        <button class="btn btn-accent">تبدیل به فاکتور</button>
      </form>
    <?php endif; ?>
    <?php if ($left !== null && $left > 0): ?>
      <a class="btn btn-accent" data-guard href="<?= e(url('payments', [
          'customer' => $doc['customer_id'], 'amount' => (int) $left, 'note' => 'بابت فاکتور ' . $doc['number'],
      ])) ?>">ثبت دریافت</a>
    <?php endif; ?>

    <?php if (!$isNew): ?>
      <details class="more">
        <summary class="btn btn-ghost" aria-label="عملیات بیشتر">⋯</summary>
        <div class="menu">
          <?php if ($customer): ?>
            <a href="<?= e(url('customer', ['id' => $customer['id']])) ?>" data-guard>حساب مشتری</a>
          <?php endif; ?>
          <?php if ($type === 'inv' && $doc['status'] === 'active'): ?>
            <form method="post" action="<?= e(url('doc_action')) ?>" data-guard
                  data-confirm="فاکتور باطل شود؟ مبلغ آن از بدهی مشتری کم می‌شود (قابل بازگردانی است).">
              <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="cancel">
              <button class="danger">ابطال فاکتور</button>
            </form>
          <?php endif; ?>
          <?php if ($readOnly): ?>
            <form method="post" action="<?= e(url('doc_action')) ?>">
              <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="restore">
              <button>بازگردانی فاکتور</button>
            </form>
          <?php endif; ?>
          <?php if ($type === 'qot' || $readOnly): ?>
            <form method="post" action="<?= e(url('doc_action')) ?>" data-guard
                  data-confirm="<?= e(DOC_NAMES[$type]) ?> برای همیشه حذف شود؟">
              <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="delete">
              <button class="danger">حذف <?= e(DOC_NAMES[$type]) ?></button>
            </form>
          <?php endif; ?>
        </div>
      </details>
    <?php endif; ?>
  </div>
</div>

<main class="stage">
<div class="stage-in">
  <?php if ($source || $converted || $customer || $readOnly): ?>
  <div class="banners no-print">
    <?php if ($readOnly): ?>
      <div class="banner">این فاکتور باطل شده و در بدهی مشتری حساب نمی‌شود.</div>
    <?php endif; ?>
    <?php if ($source): ?>
      <div class="banner">صادرشده از پیش‌فاکتور
        <a class="mono" href="<?= e(url('doc', ['id' => $source['id']])) ?>" data-guard><?= e($source['number']) ?></a></div>
    <?php endif; ?>
    <?php if ($converted): ?>
      <div class="banner">این پیش‌فاکتور به فاکتور
        <a class="mono" href="<?= e(url('doc', ['id' => $converted['id']])) ?>" data-guard><?= e($converted['number']) ?></a> تبدیل شده است.</div>
    <?php endif; ?>
    <?php if ($customer && $type === 'inv'): ?>
      <div class="banner">مانده کل حساب
        <a href="<?= e(url('customer', ['id' => $customer['id']])) ?>" data-guard><?= e($customer['name']) ?></a>:
        <?= balance_html($customer['balance']) ?></div>
    <?php endif; ?>
  </div>
  <?php endif; ?>

<article class="sheet<?= $readOnly ? ' void' : '' ?>" id="sheet">
  <div class="main">
  <header class="hd">
    <div class="co">
      <img src="<?= e(asset('logo.svg')) ?>" alt="DaranX">
      <div>
        <b><?= e(setting('company_name')) ?></b>
        <small><?= e(setting('company_tagline')) ?></small>
      </div>
    </div>
    <div class="dt">
      <span class="en" id="docEn"><?= $type === 'inv' ? 'INVOICE' : 'QUOTATION' ?></span>
      <h1 id="docFa"><?= e(DOC_NAMES[$type]) ?></h1>
    </div>
  </header>

  <section class="info">
    <div class="box">
      <h3>مشخصات مشتری</h3>
      <dl class="kv">
        <dt>نام مشتری:</dt>
        <dd><input class="ce-in" id="cust" list="custList" placeholder="نام شخص یا شرکت" autocomplete="off" aria-label="نام مشتری"><datalist id="custList"></datalist></dd>
        <dt>آدرس:</dt><dd><div class="ce" contenteditable="true" data-ph="نشانی مشتری" id="addr"></div></dd>
        <dt>شماره تماس:</dt><dd><div class="ce one" contenteditable="true" data-ph="شماره تماس" id="phone"></div></dd>
      </dl>
    </div>
    <div class="box">
      <h3>مشخصات سند</h3>
      <dl class="kv">
        <dt>تاریخ صدور:</dt><dd><div class="ce one" contenteditable="true" data-ph="۱۴۰۵/۰۱/۰۱" id="date"></div></dd>
        <dt id="numLbl"><?= $type === 'inv' ? 'شماره فاکتور:' : 'شماره پیش‌فاکتور:' ?></dt>
        <dd><div class="ce one ltr" contenteditable="true" dir="ltr" data-ph="<?= e(DOC_PREFIX[$type]) ?>0000" id="docNo"></div></dd>
        <dt>واحد پول:</dt><dd><div id="unit"><?= e(setting('unit')) ?></div></dd>
      </dl>
    </div>
  </section>

  <section class="tbl-wrap">
    <table class="items">
      <thead>
        <tr>
          <th>ردیف</th>
          <th class="l">شرح کالا / خدمت</th>
          <th>تعداد</th>
          <th>قیمت واحد</th>
          <th>قیمت کل</th>
          <th class="del"></th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
    <div class="addrow"><button type="button" id="add">+ افزودن ردیف</button></div>
  </section>

  <section class="sum">
    <div>
      <div class="words">
        <h3>مبلغ قابل پرداخت به حروف</h3>
        <p id="words"></p>
      </div>
      <div class="sig">
        <span>مهر و امضا</span>
        <b><?= e(setting('signature')) ?></b>
      </div>
    </div>
    <div class="tot">
      <div class="r"><span>جمع کل</span><span id="sumTot">۰</span></div>
      <div class="r zero" id="rowDisc"><span>تخفیف</span><input id="disc" inputmode="decimal" placeholder="۰" aria-label="تخفیف"></div>
      <div class="r vat"><span>مالیات بر ارزش افزوده (<input class="rate" id="rate" inputmode="decimal" aria-label="درصد مالیات">٪)</span><span id="vatAmt">۰</span></div>
      <div class="r pay"><span>قابل پرداخت</span><span id="pay">۰</span></div>
    </div>
  </section>

  <section class="notes">
    <h3>توضیحات</h3>
    <ul contenteditable="true" id="notes"></ul>
  </section>
  </div>

  <footer class="ft">
    <div class="row">
      <div class="b">Daran<span class="x2">X</span></div>
      <div class="ph"><?php foreach ($phones as $i => $ph): ?><?= $i ? ' · ' : '' ?><a href="<?= e(tel_href($ph)) ?>"><?= e($ph) ?></a><?php endforeach; ?></div>
    </div>
    <div class="row">
      <div><?= e(setting('address')) ?></div>
      <?php if ($website !== ''): ?><div><a href="<?= e($websiteHref) ?>"><?= e($website) ?></a></div><?php endif; ?>
    </div>
  </footer>
</article>
</div>
</main>

<form id="saveForm" method="post" action="<?= e($isNew ? url('doc') : url('doc', ['id' => $id])) ?>" hidden>
  <?= csrf_field() ?>
  <input type="hidden" name="payload" id="payload">
</form>
<script type="application/json" id="docData"><?= json_encode($data, JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?></script>
<?php
layout_end(['doc.js']);
