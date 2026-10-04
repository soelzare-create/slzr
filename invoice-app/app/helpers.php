<?php
/**
 * Small, dependency-free helpers: escaping, Persian digits/numbers, Jalali
 * dates, request/response, flash messages, CSRF and auth.
 */
defined('APP_DIR') || exit;

const APP_VERSION = '1.0.0';

/** An error message meant for the user (shown in Persian, never a crash). */
class UserError extends RuntimeException
{
}

// --- Escaping & text --------------------------------------------------------

function e($s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function valid_utf8(string $s): bool
{
    return $s === '' || preg_match('//u', $s) === 1;
}

function str_cut(string $s, int $max): string
{
    if (function_exists('mb_substr')) {
        return mb_substr($s, 0, $max, 'UTF-8');
    }
    return preg_match('/^.{0,' . $max . '}/us', $s, $m) ? $m[0] : '';
}

/** Arabic ي/ك → Persian ی/ک, so the same name typed twice matches. */
function fa_norm(string $s): string
{
    return strtr($s, ['ي' => 'ی', 'ى' => 'ی', 'ك' => 'ک', 'ۀ' => 'ه']);
}

/** One line of user text: no control chars, collapsed whitespace, trimmed. */
function clean_line($s, int $max = 200): string
{
    $s = is_scalar($s) ? (string) $s : '';
    if (!valid_utf8($s)) {
        return '';
    }
    $s = preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $s);
    $s = preg_replace('/\s+/u', ' ', $s);
    return str_cut(trim(fa_norm($s)), $max);
}

/** Multi-line user text: keeps line breaks, strips other control chars. */
function clean_text($s, int $max = 1000): string
{
    $s = is_scalar($s) ? (string) $s : '';
    if (!valid_utf8($s)) {
        return '';
    }
    $s = str_replace(["\r\n", "\r"], "\n", $s);
    $s = preg_replace('/[\x00-\x09\x0B-\x1F\x7F]+/u', ' ', $s);
    $s = preg_replace('/[ \t]+/u', ' ', $s);
    $s = preg_replace("/ *\n */u", "\n", $s);
    $s = preg_replace("/\n{3,}/u", "\n\n", $s);
    return str_cut(trim(fa_norm($s)), $max);
}

/** Lookup key for a customer name (case/space/Arabic-letter insensitive). */
function name_key(string $name): string
{
    $k = clean_line($name, 150);
    $k = str_replace("\u{200C}", ' ', $k); // ZWNJ vs. space
    $k = preg_replace('/\s+/u', ' ', $k);
    return function_exists('mb_strtolower') ? mb_strtolower($k, 'UTF-8') : strtolower($k);
}

// --- Digits & numbers -------------------------------------------------------

function fa($s): string
{
    return strtr((string) $s, ['0' => '۰', '1' => '۱', '2' => '۲', '3' => '۳', '4' => '۴',
        '5' => '۵', '6' => '۶', '7' => '۷', '8' => '۸', '9' => '۹']);
}

function en_digits($s): string
{
    return strtr((string) $s, [
        '۰' => '0', '۱' => '1', '۲' => '2', '۳' => '3', '۴' => '4',
        '۵' => '5', '۶' => '6', '۷' => '7', '۸' => '8', '۹' => '9',
        '٠' => '0', '١' => '1', '٢' => '2', '٣' => '3', '٤' => '4',
        '٥' => '5', '٦' => '6', '٧' => '7', '٨' => '8', '٩' => '9',
    ]);
}

/** Parse a number typed with Persian/Latin digits and separators; null if blank/invalid. */
function parse_num($s): ?float
{
    if (is_int($s) || is_float($s)) {
        return is_finite((float) $s) ? (float) $s : null;
    }
    if (!is_string($s)) {
        return null;
    }
    $s = en_digits(trim($s));
    $s = str_replace(['٫', '−', '/'], ['.', '-', '.'], $s);
    $s = preg_replace('/[,٬،\s]/u', '', $s);
    if ($s === '' || !is_numeric($s)) {
        return null;
    }
    $n = (float) $s;
    return is_finite($n) ? $n : null;
}

/** 1250000 → «۱٬۲۵۰٬۰۰۰» (always unsigned — callers label the sign). */
function money($n): string
{
    return fa(number_format(abs((float) $n), 0, '.', '٬'));
}

/** Quantity with up to 2 decimals: 1.5 → «۱٫۵». */
function qty_fa($n): string
{
    $s = number_format((float) $n, 2, '.', ',');
    $s = rtrim(rtrim($s, '0'), '.');
    return fa(strtr($s, [',' => '٬', '.' => '٫']));
}

/** Balance with its Persian label: positive = customer owes us. */
function balance_html($b, bool $badge = true): string
{
    $b = (float) $b;
    if (abs($b) < 0.5) {
        return $badge ? '<span class="badge ok">تسویه</span>' : 'تسویه';
    }
    $txt = money($b) . ' ' . e(setting('unit'));
    if (!$badge) {
        return $txt . ($b > 0 ? ' بدهکار' : ' بستانکار');
    }
    return $b > 0
        ? '<span class="badge danger">' . $txt . ' بدهکار</span>'
        : '<span class="badge info">' . $txt . ' بستانکار</span>';
}

// --- Jalali (Persian) calendar ---------------------------------------------

/** Gregorian → Jalali. Returns [y, m, d]. */
function g2j(int $gy, int $gm, int $gd): array
{
    $g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
    $gy2 = ($gm > 2) ? ($gy + 1) : $gy;
    $days = 355666 + (365 * $gy) + intdiv($gy2 + 3, 4) - intdiv($gy2 + 99, 100)
        + intdiv($gy2 + 399, 400) + $gd + $g_d_m[$gm - 1];
    $jy = -1595 + (33 * intdiv($days, 12053));
    $days %= 12053;
    $jy += 4 * intdiv($days, 1461);
    $days %= 1461;
    if ($days > 365) {
        $jy += intdiv($days - 1, 365);
        $days = ($days - 1) % 365;
    }
    if ($days < 186) {
        $jm = 1 + intdiv($days, 31);
        $jd = 1 + ($days % 31);
    } else {
        $jm = 7 + intdiv($days - 186, 30);
        $jd = 1 + (($days - 186) % 30);
    }
    return [$jy, $jm, $jd];
}

/** Today's Jalali date as «1405/07/12» (Latin digits — the storage format). */
function jtoday(?int $ts = null): string
{
    $ts = $ts ?? time();
    [$y, $m, $d] = g2j((int) date('Y', $ts), (int) date('n', $ts), (int) date('j', $ts));
    return sprintf('%04d/%02d/%02d', $y, $m, $d);
}

/** Normalize a typed Jalali date (Persian digits, - or . separators); null if invalid. */
function jdate_norm($s): ?string
{
    $s = en_digits(trim(is_scalar($s) ? (string) $s : ''));
    $s = str_replace(['-', '.', '\\', ' '], ['/', '/', '/', ''], $s);
    if (!preg_match('~^(\d{2}|\d{4})/(\d{1,2})/(\d{1,2})$~', $s, $m)) {
        return null;
    }
    $y = (int) $m[1];
    $mo = (int) $m[2];
    $d = (int) $m[3];
    if ($y < 100) {
        $y += 1400;
    }
    if ($y < 1300 || $y > 1500 || $mo < 1 || $mo > 12 || $d < 1 || $d > 31 || ($mo > 6 && $d > 30)) {
        return null;
    }
    return sprintf('%04d/%02d/%02d', $y, $mo, $d);
}

function now(): string
{
    return date('Y-m-d H:i:s');
}

// --- Request / response -----------------------------------------------------

function is_post(): bool
{
    return ($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST';
}

function post(string $k, string $default = ''): string
{
    $v = $_POST[$k] ?? $default;
    return is_string($v) ? $v : $default;
}

function query(string $k, string $default = ''): string
{
    $v = $_GET[$k] ?? $default;
    return is_string($v) ? $v : $default;
}

function is_https(): bool
{
    return (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https')
        || (($_SERVER['SERVER_PORT'] ?? '') === '443');
}

function url(string $p = 'home', array $q = []): string
{
    return 'index.php?' . http_build_query(['p' => $p] + $q);
}

function redirect(string $p = 'home', array $q = []): void
{
    header('Location: ' . url($p, $q), true, 303);
    exit;
}

function flash(string $type, string $msg): void
{
    $_SESSION['flash'][] = [$type, $msg];
}

function take_flashes(): array
{
    $f = $_SESSION['flash'] ?? [];
    unset($_SESSION['flash']);
    return $f;
}

// --- CSRF -------------------------------------------------------------------

function csrf_token(): string
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf" value="' . e(csrf_token()) . '">';
}

function csrf_check(): void
{
    if (!hash_equals(csrf_token(), post('csrf'))) {
        http_response_code(400);
        fatal('نشست شما منقضی شده است. صفحه را دوباره باز کنید و دوباره تلاش کنید.');
    }
}

// --- Auth -------------------------------------------------------------------

function current_user(): ?array
{
    static $user = false;
    if ($user === false) {
        $user = null;
        if (!empty($_SESSION['uid'])) {
            $st = db()->prepare('SELECT id, username FROM users WHERE id = ?');
            $st->execute([(int) $_SESSION['uid']]);
            $user = $st->fetch() ?: null;
        }
    }
    return $user;
}

function require_login(): void
{
    if (!current_user()) {
        redirect('login');
    }
}

function login_user(int $uid): void
{
    session_regenerate_id(true);
    $_SESSION['uid'] = $uid;
    $_SESSION['seen'] = time();
    unset($_SESSION['csrf']);
}

function client_ip(): string
{
    return (string) ($_SERVER['REMOTE_ADDR'] ?? '');
}
