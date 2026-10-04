<?php
/** First run: create the admin account (only while no user exists). */
defined('APP_DIR') || exit;

if (has_users()) {
    redirect('login');
}

$error = null;
$username = '';
if (is_post()) {
    $username = trim(post('username'));
    $pass = post('password');
    if (!preg_match('/^[A-Za-z0-9_.\-]{3,32}$/', $username)) {
        $error = 'نام کاربری باید ۳ تا ۳۲ کاراکتر از حروف انگلیسی، عدد یا . _ - باشد.';
    } elseif (strlen($pass) < 8) {
        $error = 'رمز عبور باید حداقل ۸ کاراکتر باشد.';
    } elseif ($pass !== post('password2')) {
        $error = 'تکرار رمز عبور با خودش یکسان نیست.';
    } else {
        $uid = tx(function (PDO $pdo) use ($username, $pass) {
            if ((int) $pdo->query('SELECT COUNT(*) FROM users')->fetchColumn() > 0) {
                return 0; // someone finished setup a moment earlier
            }
            $pdo->prepare('INSERT INTO users (username, pass_hash, created_at) VALUES (?, ?, ?)')
                ->execute([$username, password_hash($pass, PASSWORD_DEFAULT), now()]);
            return (int) $pdo->lastInsertId();
        });
        if (!$uid) {
            redirect('login');
        }
        login_user($uid);
        flash('ok', 'حساب شما ساخته شد. ابتدا مشخصات شرکت را بررسی کنید.');
        redirect('settings');
    }
}

auth_start('راه‌اندازی اولیه', 'یک نام کاربری و رمز عبور برای ورود به برنامه انتخاب کنید.');
?>
<?php if ($error): ?><div class="flash err"><?= e($error) ?></div><?php endif; ?>
<form method="post" class="form" autocomplete="off">
  <?= csrf_field() ?>
  <label class="field"><span>نام کاربری (انگلیسی)</span>
    <input name="username" value="<?= e($username) ?>" dir="ltr" required autofocus pattern="[A-Za-z0-9_.\-]{3,32}"></label>
  <label class="field"><span>رمز عبور (حداقل ۸ کاراکتر)</span>
    <input type="password" name="password" dir="ltr" required minlength="8" autocomplete="new-password"></label>
  <label class="field"><span>تکرار رمز عبور</span>
    <input type="password" name="password2" dir="ltr" required minlength="8" autocomplete="new-password"></label>
  <button class="btn btn-primary btn-block">ساخت حساب و ورود</button>
</form>
<?php
auth_end();
