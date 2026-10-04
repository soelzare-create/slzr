<?php
/** Record money received from a customer (reduces their debt) + list of payments. */
defined('APP_DIR') || exit;

$error = null;
$form = [
    'customer_id' => query('customer'),
    'amount' => is_numeric(query('amount')) && (float) query('amount') > 0 ? money(query('amount')) : '',
    'date' => fa(jtoday()),
    'method' => PAY_METHODS[0],
    'note' => clean_line(query('note'), 300),
];

if (is_post()) {
    $form = array_map(function ($v) { return is_string($v) ? $v : ''; }, $_POST) + $form;
    try {
        $p = payment_validate($_POST);
        payment_save($p);
        $c = customer_get($p['customer_id']);
        flash('ok', 'دریافت ' . money($p['amount']) . ' ' . setting('unit') . ' از «' . $c['name'] . '» ثبت شد. '
            . 'مانده حساب: ' . strip_tags(balance_html($c['balance'], false)) . '.');
        redirect('customer', ['id' => $p['customer_id']]);
    } catch (UserError $ex) {
        $error = $ex->getMessage();
    }
}

$customers = customers_list();
$q = clean_line(query('q'), 100);
$list = payments_list($q);
$unit = setting('unit');

layout_start('دریافت‌ها', 'payments', ['error' => $error]);
?>
<main class="page">
  <div class="head"><h1>دریافت‌ها</h1></div>

  <section class="card">
    <h2>ثبت دریافت از مشتری</h2>
    <?php if (!$customers): ?>
      <p class="empty">اول یک مشتری ثبت کنید (یا یک فاکتور صادر کنید).</p>
    <?php else: ?>
    <form method="post" class="form">
      <?= csrf_field() ?>
      <div class="fgrid">
        <label class="field"><span>مشتری</span>
          <select name="customer_id" required>
            <option value="">— انتخاب کنید —</option>
            <?php foreach ($customers as $c): ?>
              <option value="<?= (int) $c['id'] ?>"<?= (string) $c['id'] === (string) $form['customer_id'] ? ' selected' : '' ?>>
                <?= e($c['name']) ?><?= (float) $c['balance'] > 0.5 ? ' — بدهی ' . money($c['balance']) : '' ?>
              </option>
            <?php endforeach; ?>
          </select></label>
        <label class="field"><span>مبلغ دریافتی (<?= e($unit) ?>)</span>
          <input name="amount" class="money" inputmode="decimal" value="<?= e($form['amount']) ?>" required placeholder="۰"></label>
        <label class="field"><span>تاریخ</span>
          <input name="date" value="<?= e($form['date']) ?>" required placeholder="۱۴۰۵/۰۱/۰۱"></label>
        <label class="field"><span>روش پرداخت</span>
          <select name="method">
            <?php foreach (PAY_METHODS as $m): ?>
              <option<?= $m === $form['method'] ? ' selected' : '' ?>><?= e($m) ?></option>
            <?php endforeach; ?>
          </select></label>
      </div>
      <label class="field"><span>توضیح <small>(اختیاری؛ مثلاً شماره پیگیری یا بابت کدام فاکتور)</small></span>
        <input name="note" value="<?= e($form['note']) ?>" maxlength="300"></label>
      <div class="actions">
        <button class="btn btn-primary">ثبت دریافت</button>
        <small class="muted">مبلغ از بدهی مشتری کم می‌شود؛ هر مبلغی (حتی بخشی از بدهی) قابل ثبت است.</small>
      </div>
    </form>
    <?php endif; ?>
  </section>

  <section class="card">
    <h2>دریافت‌های ثبت‌شده</h2>
    <form class="search" method="get">
      <input type="hidden" name="p" value="payments">
      <input class="input" name="q" value="<?= e($q) ?>" placeholder="جستجو در نام مشتری یا توضیح…" aria-label="جستجو">
      <button class="btn btn-ghost">جستجو</button>
    </form>
    <?php if (!$list): ?>
      <p class="empty"><?= $q !== '' ? 'موردی پیدا نشد.' : 'هنوز دریافتی ثبت نشده.' ?></p>
    <?php else: ?>
      <div class="tbl"><table class="list wide">
        <thead><tr><th>تاریخ</th><th>مشتری</th><th class="num">مبلغ (<?= e($unit) ?>)</th><th>روش</th><th>توضیح</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($list as $p): ?>
          <tr>
            <td class="nowrap"><?= fa($p['date']) ?></td>
            <td><a href="<?= e(url('customer', ['id' => $p['customer_id']])) ?>"><?= e($p['customer_name']) ?></a></td>
            <td class="num"><?= money($p['amount']) ?></td>
            <td class="nowrap"><?= e($p['method']) ?></td>
            <td class="small"><?= e($p['note']) ?></td>
            <td class="row-actions"><a class="btn btn-ghost btn-sm" href="<?= e(url('payment', ['id' => $p['id']])) ?>">ویرایش</a></td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table></div>
    <?php endif; ?>
  </section>
</main>
<?php
layout_end();
