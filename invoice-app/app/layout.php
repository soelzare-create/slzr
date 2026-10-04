<?php
/**
 * Page chrome: <head>, top navigation, flash messages, error pages.
 */
defined('APP_DIR') || exit;

const NAV = [
    'home' => ['داشبورد', []],
    'qot' => ['پیش‌فاکتورها', ['p' => 'docs', 'type' => 'qot']],
    'inv' => ['فاکتورها', ['p' => 'docs', 'type' => 'inv']],
    'customers' => ['مشتریان', ['p' => 'customers']],
    'payments' => ['دریافت‌ها', ['p' => 'payments']],
    'settings' => ['تنظیمات', ['p' => 'settings']],
];

function asset(string $file): string
{
    return 'assets/' . $file . '?v=' . APP_VERSION;
}

function html_head(string $title, array $css = ['app.css']): void
{
    ?><!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title><?= e($title) ?></title>
<link rel="icon" href="<?= e(asset('favicon.svg')) ?>" type="image/svg+xml">
<?php foreach ($css as $f): ?>
<link rel="stylesheet" href="<?= e(asset($f)) ?>">
<?php endforeach; ?>
<script src="<?= e(asset('app.js')) ?>"></script>
</head>
<?php
}

/**
 * Open a logged-in page. $opt: sheet (bool) = document editor page,
 * error (string) = extra error message shown with the flashes.
 */
function layout_start(string $title, string $active = '', array $opt = []): void
{
    $sheet = !empty($opt['sheet']);
    html_head($title . ' — DaranX', $sheet ? ['app.css', 'sheet.css'] : ['app.css']);
    echo '<body class="' . ($sheet ? 'sheet-page' : '') . '"' . ($opt['body_attrs'] ?? '') . ">\n";
    $user = current_user();
    ?>
<nav class="nav no-print">
  <div class="in">
    <a class="brand" href="index.php">Daran<span class="x">X</span></a>
    <div class="links">
      <?php foreach (NAV as $key => [$label, $q]): ?>
        <a href="<?= e(url($q['p'] ?? 'home', array_diff_key($q, ['p' => 1]))) ?>"<?= $key === $active ? ' aria-current="page"' : '' ?>><?= e($label) ?></a>
      <?php endforeach; ?>
    </div>
    <div class="nav-end">
      <?php if ($user): ?>
        <form method="post" action="<?= e(url('logout')) ?>">
          <?= csrf_field() ?>
          <button class="linkbtn" title="<?= e($user['username']) ?>">خروج</button>
        </form>
      <?php endif; ?>
      <button type="button" class="theme-toggle" id="tt" aria-label="روشن/تیره"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/></svg></button>
    </div>
  </div>
</nav>
<?php
    flashes($opt['error'] ?? null);
}

function flashes(?string $error = null): void
{
    $list = take_flashes();
    if ($error) {
        $list[] = ['err', $error];
    }
    if (!$list) {
        return;
    }
    echo '<div class="flashes no-print">';
    foreach ($list as [$type, $msg]) {
        echo '<div class="flash ' . ($type === 'ok' ? 'ok' : 'err') . '" role="status">' . e($msg) . '</div>';
    }
    echo '</div>';
}

function layout_end(array $scripts = []): void
{
    foreach ($scripts as $s) {
        echo '<script src="' . e(asset($s)) . '"></script>' . "\n";
    }
    echo "</body>\n</html>\n";
}

/** Centered card used by the login and first-run setup screens. */
function auth_start(string $title, string $subtitle): void
{
    html_head($title . ' — DaranX');
    ?>
<body>
<main class="auth">
  <div class="auth-card">
    <div class="auth-hd">
      <img src="<?= e(asset('logo.svg')) ?>" alt="DaranX">
      <h1><?= e($title) ?></h1>
      <p><?= e($subtitle) ?></p>
    </div>
    <div class="auth-bd">
<?php
    flashes();
}

function auth_end(): void
{
    echo "    </div>\n  </div>\n</main>\n";
    layout_end();
}

/** Minimal standalone error page (works before the DB is available). */
function fatal(string $msg, int $code = 0): void
{
    if ($code && !headers_sent()) {
        http_response_code($code);
    }
    if (!headers_sent()) {
        header('Content-Type: text/html; charset=utf-8');
    }
    echo '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        . '<meta name="viewport" content="width=device-width, initial-scale=1"><title>DaranX</title>'
        . '<link rel="stylesheet" href="' . e(asset('app.css')) . '"></head><body>'
        . '<main class="page"><div class="card"><h2>پیام سیستم</h2><p style="white-space:pre-wrap">'
        . e($msg) . '</p><p><a class="btn btn-ghost" href="index.php">بازگشت به برنامه</a></p></div></main></body></html>';
    exit;
}

function not_found(): void
{
    fatal('صفحه یا موردی که دنبالش هستید پیدا نشد.', 404);
}

/** Shared fields of the add/edit customer form. */
function customer_fields(array $c): void
{
    // From the DB the balance is a signed number; after a failed submit it is
    // the raw typed text plus the chosen side.
    $raw = $c['opening_balance'] ?? '';
    $creditor = ($c['opening_side'] ?? '') === 'creditor';
    if (is_string($raw) && $raw !== '' && !is_numeric($raw)) {
        $obText = $raw;
    } else {
        $ob = (float) $raw;
        $obText = $ob ? money($ob) : '';
        $creditor = $creditor || $ob < 0;
    }
    ?>
  <div class="fgrid">
    <label class="field"><span>نام شخص یا شرکت</span>
      <input name="name" value="<?= e($c['name'] ?? '') ?>" required maxlength="150"></label>
    <label class="field"><span>شماره تماس</span>
      <input name="phone" value="<?= e($c['phone'] ?? '') ?>" maxlength="80"></label>
  </div>
  <label class="field"><span>آدرس</span>
    <textarea name="address" rows="2" maxlength="400"><?= e($c['address'] ?? '') ?></textarea></label>
  <div class="fgrid">
    <label class="field"><span>مانده از قبل <small>(اگر قبل از این برنامه حساب داشته)</small></span>
      <input name="opening_balance" class="money" inputmode="decimal" value="<?= e($obText) ?>" placeholder="۰"></label>
    <label class="field"><span>نوع مانده</span>
      <select name="opening_side">
        <option value="debtor"<?= $creditor ? '' : ' selected' ?>>بدهکار (مشتری به ما بدهکار است)</option>
        <option value="creditor"<?= $creditor ? ' selected' : '' ?>>بستانکار (ما به مشتری بدهکاریم)</option>
      </select></label>
  </div>
  <label class="field"><span>یادداشت</span>
    <textarea name="note" rows="2" maxlength="1000"><?= e($c['note'] ?? '') ?></textarea></label>
<?php
}
