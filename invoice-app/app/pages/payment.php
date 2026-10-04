<?php
/** Edit or delete a recorded payment (to fix a mistake). */
defined('APP_DIR') || exit;

$id = (int) query('id');
$pay = payment_get($id);
if (!$pay) {
    not_found();
}

$error = null;
$form = [
    'customer_id' => (string) $pay['customer_id'],
    'amount' => money($pay['amount']),
    'date' => fa($pay['date']),
    'method' => $pay['method'],
    'note' => $pay['note'],
];

if (is_post()) {
    if (post('action') === 'delete') {
        payment_delete($id);
        flash('ok', 'دریافت حذف شد و مبلغ آن به بدهی مشتری برگشت.');
        redirect('customer', ['id' => $pay['customer_id']]);
    }
    $form = array_map(function ($v) { return is_string($v) ? $v : ''; }, $_POST) + $form;
    try {
        $p = payment_validate($_POST);
        payment_save($p, $id);
        flash('ok', 'دریافت ویرایش شد.');
        redirect('customer', ['id' => $p['customer_id']]);
    } catch (UserError $ex) {
        $error = $ex->getMessage();
    }
}

$customers = customers_list();
layout_start('ویرایش دریافت', 'payments', ['error' => $error]);
?>
<main class="page narrow">
  <div class="head">
    <h1>ویرایش دریافت</h1>
    <div class="actions"><a class="btn btn-ghost" href="<?= e(url('customer', ['id' => $pay['customer_id']])) ?>">→ حساب <?= e($pay['customer_name']) ?></a></div>
  </div>
  <section class="card">
    <form method="post" class="form">
      <?= csrf_field() ?>
      <input type="hidden" name="action" value="save">
      <div class="fgrid">
        <label class="field"><span>مشتری</span>
          <select name="customer_id" required>
            <?php foreach ($customers as $c): ?>
              <option value="<?= (int) $c['id'] ?>"<?= (string) $c['id'] === (string) $form['customer_id'] ? ' selected' : '' ?>><?= e($c['name']) ?></option>
            <?php endforeach; ?>
          </select></label>
        <label class="field"><span>مبلغ (<?= e(setting('unit')) ?>)</span>
          <input name="amount" class="money" inputmode="decimal" value="<?= e($form['amount']) ?>" required></label>
        <label class="field"><span>تاریخ</span>
          <input name="date" value="<?= e($form['date']) ?>" required></label>
        <label class="field"><span>روش پرداخت</span>
          <select name="method">
            <?php foreach (PAY_METHODS as $m): ?>
              <option<?= $m === $form['method'] ? ' selected' : '' ?>><?= e($m) ?></option>
            <?php endforeach; ?>
          </select></label>
      </div>
      <label class="field"><span>توضیح</span>
        <input name="note" value="<?= e($form['note']) ?>" maxlength="300"></label>
      <div class="actions"><button class="btn btn-primary">ذخیره</button></div>
    </form>
    <form method="post" class="mt" data-confirm="این دریافت حذف شود؟ مبلغ آن دوباره به بدهی مشتری اضافه می‌شود.">
      <?= csrf_field() ?>
      <input type="hidden" name="action" value="delete">
      <button class="btn btn-danger btn-sm">حذف دریافت</button>
    </form>
  </section>
</main>
<?php
layout_end();
