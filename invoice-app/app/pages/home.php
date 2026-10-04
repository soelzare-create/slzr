<?php
/** Dashboard: receivables, this month's numbers, debtors and recent documents. */
defined('APP_DIR') || exit;

$s = dashboard_stats();
$unit = setting('unit');
$debtors = array_slice(customers_list('', true), 0, 10);
$recentInv = docs_list('inv', '', 0, 6);
$recentQot = docs_list('qot', '', 0, 6);
$remaining = invoice_remaining();

layout_start('داشبورد', 'home');
?>
<main class="page">
  <div class="head">
    <h1>داشبورد</h1>
    <div class="actions">
      <a class="btn btn-ghost" href="<?= e(url('doc', ['new' => 'qot'])) ?>">+ پیش‌فاکتور</a>
      <a class="btn btn-ghost" href="<?= e(url('doc', ['new' => 'inv'])) ?>">+ فاکتور</a>
      <a class="btn btn-primary" href="<?= e(url('payments')) ?>">+ ثبت دریافت</a>
    </div>
  </div>

  <div class="tiles">
    <a class="tile hero" href="<?= e(url('customers', ['debtors' => 1])) ?>">
      <div class="k">طلب از مشتریان</div>
      <div class="v"><?= money($s['receivable']) ?> <small><?= e($unit) ?></small></div>
      <div class="s"><?= fa($s['debtors']) ?> مشتری بدهکار</div>
    </a>
    <a class="tile" href="<?= e(url('docs', ['type' => 'inv'])) ?>">
      <div class="k">فاکتورهای این ماه</div>
      <div class="v"><?= money($s['inv_sum']) ?> <small><?= e($unit) ?></small></div>
      <div class="s"><?= fa($s['inv_count']) ?> فاکتور</div>
    </a>
    <a class="tile" href="<?= e(url('payments')) ?>">
      <div class="k">دریافتی این ماه</div>
      <div class="v"><?= money($s['pay_sum']) ?> <small><?= e($unit) ?></small></div>
      <div class="s"><?= fa($s['pay_count']) ?> دریافت</div>
    </a>
    <a class="tile" href="<?= e(url('docs', ['type' => 'qot'])) ?>">
      <div class="k">پیش‌فاکتورهای باز</div>
      <div class="v"><?= fa($s['open_qot']) ?></div>
      <div class="s">هنوز به فاکتور تبدیل نشده</div>
    </a>
  </div>

  <div class="grid2">
    <section class="card">
      <h2>بدهکاران</h2>
      <?php if (!$debtors): ?>
        <p class="empty">هیچ مشتری بدهکاری ندارید.</p>
      <?php else: ?>
        <div class="tbl"><table class="list">
          <thead><tr><th>مشتری</th><th class="num">بدهی</th></tr></thead>
          <tbody>
          <?php foreach ($debtors as $c): ?>
            <tr>
              <td><a class="strong" href="<?= e(url('customer', ['id' => $c['id']])) ?>"><?= e($c['name']) ?></a></td>
              <td class="num"><?= money($c['balance']) ?></td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table></div>
      <?php endif; ?>
    </section>

    <section class="card">
      <h2>آخرین فاکتورها</h2>
      <?php if (!$recentInv): ?>
        <p class="empty">هنوز فاکتوری صادر نشده.</p>
      <?php else: ?>
        <div class="tbl"><table class="list">
          <thead><tr><th>شماره</th><th>مشتری</th><th class="num">مبلغ</th><th>وضعیت</th></tr></thead>
          <tbody>
          <?php foreach ($recentInv as $d): ?>
            <tr>
              <td><a class="mono" href="<?= e(url('doc', ['id' => $d['id']])) ?>"><?= e($d['number']) ?></a></td>
              <td><?= e($d['cust_name']) ?></td>
              <td class="num"><?= money($d['total']) ?></td>
              <td><?= invoice_badge($d, $remaining) ?></td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table></div>
      <?php endif; ?>

      <h2 class="mt">آخرین پیش‌فاکتورها</h2>
      <?php if (!$recentQot): ?>
        <p class="empty">هنوز پیش‌فاکتوری ثبت نشده.</p>
      <?php else: ?>
        <div class="tbl"><table class="list">
          <thead><tr><th>شماره</th><th>مشتری</th><th class="num">مبلغ</th><th>وضعیت</th></tr></thead>
          <tbody>
          <?php foreach ($recentQot as $d): ?>
            <tr>
              <td><a class="mono" href="<?= e(url('doc', ['id' => $d['id']])) ?>"><?= e($d['number']) ?></a></td>
              <td><?= e($d['cust_name']) ?></td>
              <td class="num"><?= money($d['total']) ?></td>
              <td><?= $d['inv_id'] ? '<span class="badge ok">فاکتور شد</span>' : '<span class="badge info">باز</span>' ?></td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table></div>
      <?php endif; ?>
    </section>
  </div>
</main>
<?php
layout_end();
