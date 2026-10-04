<?php
/** Company letterhead, defaults, password, and database backup. */
defined('APP_DIR') || exit;

$error = null;
$user = current_user();

if (is_post()) {
    try {
        if (post('action') === 'password') {
            $row = user_by_name($user['username']);
            if (!password_verify(post('current'), $row['pass_hash'])) {
                throw new UserError('رمز فعلی اشتباه است.');
            }
            if (strlen(post('new')) < 8) {
                throw new UserError('رمز جدید باید حداقل ۸ کاراکتر باشد.');
            }
            if (post('new') !== post('new2')) {
                throw new UserError('تکرار رمز جدید یکسان نیست.');
            }
            db()->prepare('UPDATE users SET pass_hash = ? WHERE id = ?')
                ->execute([password_hash(post('new'), PASSWORD_DEFAULT), $user['id']]);
            flash('ok', 'رمز عبور تغییر کرد.');
            redirect('settings');
        }

        $rate = parse_num(post('vat_rate'));
        if ($rate === null || $rate < 0 || $rate > 100) {
            throw new UserError('درصد مالیات باید عددی بین ۰ تا ۱۰۰ باشد.');
        }
        $values = [
            'company_name' => clean_line(post('company_name'), 150),
            'company_tagline' => clean_line(post('company_tagline'), 150),
            'signature' => clean_line(post('signature'), 100),
            'phones' => clean_text(post('phones'), 300),
            'address' => clean_line(post('address'), 300),
            'website' => clean_line(post('website'), 100),
            'unit' => clean_line(post('unit'), 20) ?: 'ریال',
            'vat_rate' => (string) $rate,
            'notes_qot' => clean_text(post('notes_qot'), 2000),
            'notes_inv' => clean_text(post('notes_inv'), 2000),
        ];
        if ($values['company_name'] === '') {
            throw new UserError('نام شرکت را وارد کنید.');
        }
        settings_save($values);
        flash('ok', 'تنظیمات ذخیره شد.');
        redirect('settings');
    } catch (UserError $ex) {
        $error = $ex->getMessage();
    }
}

$s = settings();
if (is_post() && post('action') !== 'password') {
    foreach ($s as $k => $v) {
        $s[$k] = post($k, $v); // keep what was typed
    }
}

layout_start('تنظیمات', 'settings', ['error' => $error]);
?>
<main class="page narrow">
  <div class="head"><h1>تنظیمات</h1></div>

  <section class="card">
    <h2>سربرگ و پانویس اسناد</h2>
    <form method="post" class="form">
      <?= csrf_field() ?>
      <input type="hidden" name="action" value="company">
      <div class="fgrid">
        <label class="field"><span>نام شرکت (سربرگ)</span>
          <input name="company_name" value="<?= e($s['company_name']) ?>" required maxlength="150"></label>
        <label class="field"><span>شعار زیر نام</span>
          <input name="company_tagline" value="<?= e($s['company_tagline']) ?>" maxlength="150"></label>
        <label class="field"><span>نام زیر «مهر و امضا»</span>
          <input name="signature" value="<?= e($s['signature']) ?>" maxlength="100"></label>
        <label class="field"><span>وب‌سایت</span>
          <input name="website" value="<?= e($s['website']) ?>" dir="ltr" maxlength="100"></label>
      </div>
      <div class="fgrid">
        <label class="field"><span>تلفن‌ها <small>(هر کدام در یک خط)</small></span>
          <textarea name="phones" rows="3"><?= e($s['phones']) ?></textarea></label>
        <label class="field"><span>آدرس</span>
          <textarea name="address" rows="3"><?= e($s['address']) ?></textarea></label>
      </div>

      <h2 class="mt">پیش‌فرض‌ها</h2>
      <div class="fgrid">
        <label class="field"><span>واحد پول</span>
          <input name="unit" value="<?= e($s['unit']) ?>" maxlength="20">
          <small>فقط عنوان است؛ مبالغ ثبت‌شده تبدیل نمی‌شوند.</small></label>
        <label class="field"><span>درصد مالیات بر ارزش افزوده</span>
          <input name="vat_rate" value="<?= e(fa($s['vat_rate'])) ?>" inputmode="decimal"></label>
      </div>
      <div class="fgrid">
        <label class="field"><span>توضیحات پیش‌فرض پیش‌فاکتور <small>(هر بند در یک خط)</small></span>
          <textarea name="notes_qot" rows="4"><?= e($s['notes_qot']) ?></textarea></label>
        <label class="field"><span>توضیحات پیش‌فرض فاکتور <small>(هر بند در یک خط)</small></span>
          <textarea name="notes_inv" rows="4"><?= e($s['notes_inv']) ?></textarea></label>
      </div>
      <div class="actions"><button class="btn btn-primary">ذخیره تنظیمات</button></div>
    </form>
  </section>

  <section class="card">
    <h2>تغییر رمز عبور</h2>
    <form method="post" class="form">
      <?= csrf_field() ?>
      <input type="hidden" name="action" value="password">
      <input type="text" name="username" value="<?= e($user['username']) ?>" autocomplete="username" hidden>
      <div class="fgrid">
        <label class="field"><span>رمز فعلی</span>
          <input type="password" name="current" dir="ltr" required autocomplete="current-password"></label>
        <label class="field"><span>رمز جدید</span>
          <input type="password" name="new" dir="ltr" required minlength="8" autocomplete="new-password"></label>
        <label class="field"><span>تکرار رمز جدید</span>
          <input type="password" name="new2" dir="ltr" required minlength="8" autocomplete="new-password"></label>
      </div>
      <div class="actions"><button class="btn btn-primary">تغییر رمز</button>
        <small class="muted">نام کاربری شما: <b dir="ltr"><?= e($user['username']) ?></b></small></div>
    </form>
  </section>

  <section class="card">
    <h2>پشتیبان‌گیری</h2>
    <p>همهٔ اطلاعات (مشتریان، اسناد و دریافت‌ها) در یک فایل ذخیره می‌شود. هر چند وقت یک بار نسخهٔ پشتیبان بگیرید و جای امنی نگه دارید.</p>
    <a class="btn btn-ghost" href="<?= e(url('backup')) ?>">دانلود فایل پشتیبان</a>
  </section>
</main>
<?php
layout_end();
