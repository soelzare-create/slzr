<?php
/** Customers with their current balance; add a customer. */
defined('APP_DIR') || exit;

$error = null;
$form = [];
if (is_post()) {
    $form = $_POST;
    try {
        $id = customer_save(customer_validate($_POST));
        flash('ok', 'مشتری ثبت شد.');
        redirect('customer', ['id' => $id]);
    } catch (UserError $ex) {
        $error = $ex->getMessage();
    }
}

$q = clean_line(query('q'), 100);
$debtorsOnly = query('debtors') === '1';
$list = customers_list($q, $debtorsOnly);
$total = 0.0;
foreach ($list as $c) {
    $total += max(0, (float) $c['balance']);
}

layout_start('مشتریان', 'customers', ['error' => $error]);
?>
<main class="page">
  <div class="head">
    <h1>مشتریان</h1>
    <div class="actions">
      <span class="muted">جمع طلب: <b class="ink"><?= money($total) ?> <?= e(setting('unit')) ?></b></span>
    </div>
  </div>

  <details class="card collapse"<?= $error ? ' open' : '' ?>>
    <summary><span class="btn btn-primary btn-sm">+ مشتری جدید</span></summary>
    <form method="post" class="form mt">
      <?= csrf_field() ?>
      <?php customer_fields($form ? array_map(function ($v) { return is_string($v) ? $v : ''; }, $form) + ['opening_balance' => 0] : []); ?>
      <div class="actions"><button class="btn btn-primary">ثبت مشتری</button></div>
    </form>
  </details>

  <section class="card">
    <form class="search" method="get">
      <input type="hidden" name="p" value="customers">
      <input class="input" name="q" value="<?= e($q) ?>" placeholder="جستجو در نام یا شماره تماس…" aria-label="جستجو">
      <label class="chk"><input type="checkbox" name="debtors" value="1"<?= $debtorsOnly ? ' checked' : '' ?> data-autosubmit> فقط بدهکاران</label>
      <button class="btn btn-ghost">جستجو</button>
    </form>

    <?php if (!$list): ?>
      <p class="empty"><?= ($q !== '' || $debtorsOnly) ? 'موردی پیدا نشد.' : 'هنوز مشتری‌ای ثبت نشده. با اولین پیش‌فاکتور یا فاکتور، مشتری خودکار ساخته می‌شود.' ?></p>
    <?php else: ?>
      <div class="tbl"><table class="list wide">
        <thead><tr><th>مشتری</th><th>شماره تماس</th><th>مانده حساب</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($list as $c): ?>
          <tr>
            <td><a class="strong" href="<?= e(url('customer', ['id' => $c['id']])) ?>"><?= e($c['name']) ?></a></td>
            <td><?= e($c['phone']) ?></td>
            <td><?= balance_html($c['balance']) ?></td>
            <td class="row-actions">
              <a class="btn btn-ghost btn-sm" href="<?= e(url('payments', ['customer' => $c['id']])) ?>">ثبت دریافت</a>
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
