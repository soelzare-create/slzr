<?php
/** List of proformas or invoices, with search. */
defined('APP_DIR') || exit;

$type = query('type') === 'inv' ? 'inv' : 'qot';
$q = clean_line(query('q'), 100);
$docs = docs_list($type, $q);
$remaining = $type === 'inv' ? invoice_remaining() : [];
$title = $type === 'inv' ? 'فاکتورها' : 'پیش‌فاکتورها';

layout_start($title, $type);
?>
<main class="page">
  <div class="head">
    <h1><?= e($title) ?></h1>
    <div class="actions">
      <a class="btn btn-primary" href="<?= e(url('doc', ['new' => $type])) ?>">+ <?= e(DOC_NAMES[$type]) ?> جدید</a>
    </div>
  </div>

  <section class="card">
    <form class="search" method="get">
      <input type="hidden" name="p" value="docs">
      <input type="hidden" name="type" value="<?= e($type) ?>">
      <input class="input" name="q" value="<?= e($q) ?>" placeholder="جستجو در شماره یا نام مشتری…" aria-label="جستجو">
      <button class="btn btn-ghost">جستجو</button>
      <?php if ($q !== ''): ?><a class="btn btn-link" href="<?= e(url('docs', ['type' => $type])) ?>">نمایش همه</a><?php endif; ?>
    </form>

    <?php if (!$docs): ?>
      <p class="empty"><?= $q !== '' ? 'موردی پیدا نشد.' : 'هنوز ' . e(DOC_NAMES[$type]) . 'ی ثبت نشده است.' ?></p>
    <?php else: ?>
      <div class="tbl"><table class="list wide">
        <thead><tr><th>شماره</th><th>تاریخ</th><th>مشتری</th><th class="num">مبلغ (<?= e(setting('unit')) ?>)</th><th>وضعیت</th></tr></thead>
        <tbody>
        <?php foreach ($docs as $d): ?>
          <tr class="<?= $d['status'] === 'cancelled' ? 'is-void' : '' ?>">
            <td><a class="mono" href="<?= e(url('doc', ['id' => $d['id']])) ?>"><?= e($d['number']) ?></a></td>
            <td><?= fa($d['date']) ?></td>
            <td><a href="<?= e(url('customer', ['id' => $d['customer_id']])) ?>"><?= e($d['cust_name']) ?></a></td>
            <td class="num"><?= money($d['total']) ?></td>
            <td>
              <?php if ($type === 'inv'): ?>
                <?= invoice_badge($d, $remaining) ?>
              <?php elseif ($d['inv_id']): ?>
                <a class="badge ok" href="<?= e(url('doc', ['id' => $d['inv_id']])) ?>">فاکتور شد: <span dir="ltr"><?= e($d['inv_number']) ?></span></a>
              <?php else: ?>
                <span class="badge info">باز</span>
              <?php endif; ?>
            </td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table></div>
    <?php endif; ?>
  </section>
</main>
<?php
layout_end();
