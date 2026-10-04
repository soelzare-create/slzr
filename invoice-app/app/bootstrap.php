<?php
/**
 * Bootstrap: environment checks, config, error handling, security headers,
 * session and database. Included once by index.php.
 */

if (PHP_VERSION_ID < 70400) {
    header('Content-Type: text/html; charset=utf-8');
    exit('<p dir="rtl">این برنامه به PHP نسخهٔ 7.4 یا بالاتر نیاز دارد. نسخهٔ فعلی هاست: '
        . htmlspecialchars(PHP_VERSION) . '</p>');
}
if (!extension_loaded('pdo_sqlite')) {
    header('Content-Type: text/html; charset=utf-8');
    exit('<p dir="rtl">افزونهٔ <b>pdo_sqlite</b> روی هاست فعال نیست. از پنل هاست '
        . '(Select PHP Version ← Extensions) آن را فعال کنید.</p>');
}

define('APP_DIR', __DIR__);
define('ROOT_DIR', dirname(__DIR__));

// Optional overrides live in app/config.php (see config.sample.php).
$cfg = ['data_dir' => ROOT_DIR . '/data', 'debug' => false];
if (is_file(APP_DIR . '/config.php')) {
    $user_cfg = require APP_DIR . '/config.php';
    if (is_array($user_cfg)) {
        $cfg = array_merge($cfg, $user_cfg);
    }
}
define('DATA_DIR', rtrim((string) $cfg['data_dir'], '/\\'));
define('DEBUG', (bool) $cfg['debug']);
unset($cfg, $user_cfg);

date_default_timezone_set('Asia/Tehran');
error_reporting(E_ALL);
ini_set('display_errors', DEBUG ? '1' : '0');
ini_set('log_errors', '1');

const DENY_ALL_HTACCESS = "<IfModule mod_authz_core.c>\n  Require all denied\n</IfModule>\n"
    . "<IfModule !mod_authz_core.c>\n  Order allow,deny\n  Deny from all\n</IfModule>\n";

require APP_DIR . '/helpers.php';
require APP_DIR . '/db.php';
require APP_DIR . '/model.php';
require APP_DIR . '/layout.php';

ensure_data_dir();
ini_set('error_log', DATA_DIR . '/error.log');

set_exception_handler(function ($ex) {
    error_log((string) $ex);
    fatal('خطای غیرمنتظره‌ای رخ داد. جزئیات در فایل data/error.log ثبت شد.'
        . (DEBUG ? "\n\n" . $ex : ''), 500);
});

send_security_headers();
start_session();

function ensure_data_dir(): void
{
    if (!is_dir(DATA_DIR) && !@mkdir(DATA_DIR, 0755, true)) {
        fatal('پوشهٔ data ساخته نشد. در کنار index.php یک پوشه به نام data بسازید و دسترسی آن را 755 بگذارید.');
    }
    if (!is_writable(DATA_DIR)) {
        fatal('پوشهٔ data قابل نوشتن نیست. از File Manager هاست، دسترسی (Permission) آن را 755 یا 775 بگذارید.');
    }
    // Keep the database out of reach even if these files were not uploaded.
    if (!is_file(DATA_DIR . '/.htaccess')) {
        @file_put_contents(DATA_DIR . '/.htaccess', DENY_ALL_HTACCESS);
    }
    if (!is_file(DATA_DIR . '/index.html')) {
        @file_put_contents(DATA_DIR . '/index.html', '');
    }
    if (!is_dir(DATA_DIR . '/sessions')) {
        @mkdir(DATA_DIR . '/sessions', 0700);
    }
}

function send_security_headers(): void
{
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: same-origin');
    header("Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        . "script-src 'self'; font-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");
    header('Cache-Control: no-store, private');
    if (is_https()) {
        header('Strict-Transport-Security: max-age=15552000');
    }
}

function start_session(): void
{
    $idle = 12 * 3600;
    $path = rtrim(str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? '/')), '/') . '/';
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.gc_maxlifetime', (string) $idle);
    ini_set('session.gc_probability', '1');
    ini_set('session.gc_divisor', '100');
    if (is_dir(DATA_DIR . '/sessions') && is_writable(DATA_DIR . '/sessions')) {
        session_save_path(DATA_DIR . '/sessions');
    }
    session_name('dxinv');
    session_set_cookie_params([
        'lifetime' => 0, 'path' => $path, 'secure' => is_https(),
        'httponly' => true, 'samesite' => 'Lax',
    ]);
    session_start();
    $now = time();
    if (!empty($_SESSION['uid']) && $now - (int) ($_SESSION['seen'] ?? 0) > $idle) {
        $_SESSION = [];
        session_regenerate_id(true);
    }
    $_SESSION['seen'] = $now;
}
