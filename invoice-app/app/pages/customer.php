<?php
/** One customer: balance, statement (printable), proformas, edit details. */
defined('APP_DIR') || exit;

$id = (int) query('id');
$c = customer_get($id);
if (!$c) {
    not_found();
}

$error = null;
$form = null;
if (is_post()) {
    try {
        if (post('action') === 'delete') {
            customer_delete($id);
            flash('ok', 'مشتری «' . $c['name'] . '» حذف شد.');
            redirect('customers');
        }
        customer_save(customer_validate($_POST), $id);
        flash('ok', 'مشخصات مشتری ذخیره شد.');
        redirect('customer', ['id' => $id]);
    } catch (UserError $ex) {
        $error = $ex->getMessage();
        if (post('action') !== 'delete') {
            $form = array_map(function ($v) { return is_string($v) ? $v : ''; }, $_POST);
        }
    }
}

$ledger = customer_ledger($c);
$proformas = docs_list('qot', '', $id, 50);
$cancelled = array_filter(docs_list('inv', '', $id, 100), function ($d) {
    return $d['status'] === 'cancelled';
});
$unit = setting('unit');
$balance = (float) $c['balance'];

layout_start($c['name'], 'customers', ['error' => $error]);
?>
<main class="page">
  <div class="print-only print-head">
    <b><?= e(setting('company_name')) ?></b>
    <span>صورت‌حساب مشتری — تاریخ <?= fa(jtoday()) ?></span>
  </div>

  <div class="head">
    <div>
      <h1><?= e($c['name']) ?></h1>
      <div class="sub"><?= e($c['phone']) ?><?= $c['phone'] && $c['address'] ? ' · ' : '' ?><?= e($c['address']) ?></div>
    </div>
    <div class="actions no-print">
      <a class="btn btn-ghost" href="<?= e(url('doc', ['new' => 'qot', 'customer' => $id])) ?>">+ پیش‌فاکتور</a>
      <a class="btn btn-ghost" href="<?= e(url('doc', ['new' => 'inv', 'customer' => $id])) ?>">+ فاکتور</a>
      <a class="btn btn-primary" href="<?= e(url('payments', ['customer' => $id] + ($balance > 0 ? ['amount' => (int) $balance] : []))) ?>">+ ثبت دریافت</a>
    </div>
  </div>

  <div class="balance-card <?= $balance > 0.5 ? 'debt' : ($balance < -0.5 ? 'credit' : 'zero') ?>">
    <span>مانده حساب</span>
    <b><?= abs($balance) < 0.5 ? 'تسویه' : money($balance) . ' ' . e($unit) ?></b>
    <span><?= $balance > 0.5 ? 'بدهکار — مشتری باید پرداخت کند' : ($balance < -0.5 ? 'بستانکار — مشتری اضافه پرداخت کرده' : 'حساب صاف است') ?></span>
  </div>

  <div class="grid-main">
    <section class="card">
      <div class="card-head">
        <h2>صورت‌حساب</h2>
        <button type="button" class="btn btn-ghost btn-sm no-print" data-print>چاپ صورت‌حساب</button>
      </div>
      <?php if (!$ledger): ?>
        <p class="empty">هنوز فاکتور یا دریافتی برای این مشتری ثبت نشده.</p>
      <?php else: ?>
        <div class="tbl"><table class="list wide ledger">
          <thead><tr><th>تاریخ</th><th>شرح</th><th class="num">بدهکار</th><th class="num">بستانکار</th><th class="num">مانده</th></tr></thead>
          <tbody>
          <?php foreach ($ledger as $r): ?>
            <tr>
              <td class="nowrap"><?= fa($r['date']) ?></td>
              <td>
                <?php if ($r['kind'] === 'inv'): ?>
                  <a href="<?= e(url('doc', ['id' => $r['id']])) ?>"><?= e($r['label']) ?></a>
                <?php elseif ($r['kind'] === 'pay'): ?>
                  <a href="<?= e(url('payment', ['id' => $r['id']])) ?>"><?= e($r['label']) ?></a>
                <?php else: ?>
                  <?= e($r['label']) ?>
                <?php endif; ?>
                <?php if ($r['note'] !== ''): ?><div class="small muted"><?= e($r['note']) ?></div><?php endif; ?>
              </td>
              <td class="num"><?= $r['debit'] ? money($r['debit']) : '' ?></td>
              <td class="num"><?= $r['credit'] ? money($r['credit']) : '' ?></td>
              <td class="num">
                <?= abs($r['balance']) < 0.5 ? '۰' : money($r['balance']) ?>
                <small class="muted"><?= $r['balance'] > 0.5 ? 'بد' : ($r['balance'] < -0.5 ? 'بس' : '') ?></small>
              </td>
            </tr>
          <?php endforeach; ?>
          </tbody>
          <tfoot><tr>
            <td colspan="4">مانده نهایی (<?= e($unit) ?>)</td>
            <td class="num"><?= balance_html($balance, false) ?></td>
          </tr></tfoot>
        </table></div>
      <?php endif; ?>
    </section>

    <div class="stack no-print">
      <section class="card">
        <h2>پیش‌فاکتورها</h2>
        <?php if (!$proformas): ?>
          <p class="empty small">پیش‌فاکتوری ندارد.</p>
        <?php else: ?>
          <ul class="mini">
            <?php foreach ($proformas as $d): ?>
              <li>
                <a class="mono" href="<?= e(url('doc', ['id' => $d['id']])) ?>"><?= e($d['number']) ?></a>
                <span class="muted"><?= fa($d['date']) ?></span>
                <span class="num"><?= money($d['total']) ?></span>
                <?= $d['inv_id'] ? '<span class="badge ok">فاکتور شد</span>' : '<span class="badge info">باز</span>' ?>
              </li>
            <?php endforeach; ?>
          </ul>
        <?php endif; ?>
        <?php if ($cancelled): ?>
          <h2 class="mt">فاکتورهای باطل‌شده</h2>
          <ul class="mini">
            <?php foreach ($cancelled as $d): ?>
              <li><a class="mono" href="<?= e(url('doc', ['id' => $d['id']])) ?>"><?= e($d['number']) ?></a>
                <span class="muted"><?= fa($d['date']) ?></span><span class="num"><?= money($d['total']) ?></span></li>
            <?php endforeach; ?>
          </ul>
        <?php endif; ?>
      </section>

      <details class="card collapse"<?= $form ? ' open' : '' ?>>
        <summary><h2>ویرایش مشخصات</h2></summary>
        <form method="post" class="form mt">
          <?= csrf_field() ?>
          <input type="hidden" name="action" value="save">
          <?php customer_fields($form ?? $c); ?>
          <div class="actions"><button class="btn btn-primary">ذخیره</button></div>
        </form>
        <form method="post" class="mt" data-confirm="مشتری «<?= e($c['name']) ?>» حذف شود؟">
          <?= csrf_field() ?>
          <input type="hidden" name="action" value="delete">
          <button class="btn btn-danger btn-sm">حذف مشتری</button>
          <small class="muted">فقط مشتری بدون سند و دریافتی حذف می‌شود.</small>
        </form>
      </details>
    </div>
  </div>
</main>
<?php
layout_end();
