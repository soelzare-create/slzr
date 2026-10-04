<?php
/** Sign in, with a lockout after repeated failures. */
defined('APP_DIR') || exit;

if (current_user()) {
    redirect('home');
}

$error = null;
$username = '';
if (is_post()) {
    $username = trim(post('username'));
    $key = client_ip() . '|' . strtolower($username);
    if (login_locked($key)) {
        $error = 'به دلیل چند تلاش ناموفق، ورود برای ۱۵ دقیقه قفل شد. بعداً دوباره امتحان کنید.';
    } else {
        $user = user_by_name($username);
        if ($user && password_verify(post('password'), $user['pass_hash'])) {
            login_clear($key);
            if (password_needs_rehash($user['pass_hash'], PASSWORD_DEFAULT)) {
                db()->prepare('UPDATE users SET pass_hash = ? WHERE id = ?')
                    ->execute([password_hash(post('password'), PASSWORD_DEFAULT), $user['id']]);
            }
            login_user((int) $user['id']);
            redirect('home');
        }
        login_failed($key);
        usleep(400000);
        $error = 'نام کاربری یا رمز عبور اشتباه است.';
    }
}

auth_start('ورود', 'پیش‌فاکتور، فاکتور و حساب مشتریان');
?>
<?php if ($error): ?><div class="flash err"><?= e($error) ?></div><?php endif; ?>
<form method="post" class="form">
  <?= csrf_field() ?>
  <label class="field"><span>نام کاربری</span>
    <input name="username" value="<?= e($username) ?>" dir="ltr" required autofocus autocomplete="username"></label>
  <label class="field"><span>رمز عبور</span>
    <input type="password" name="password" dir="ltr" required autocomplete="current-password"></label>
  <button class="btn btn-primary btn-block">ورود</button>
</form>
<?php
auth_end();
