<?php
/* ActivePlano lead endpoint (cPanel / PHP 7.4+).
   Accepts the JSON the site forms send, saves every request to api/leads/leads-XXXX.csv
   and, if $NOTIFY_EMAIL is set, emails it. Download the CSV from cPanel File Manager. */
$NOTIFY_EMAIL = '';            // e.g. 'sales@activeplano.com' (leave empty to only save to CSV)
$MAX_PER_HOUR = 6;             // per IP

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo '{"ok":false}'; exit; }

$raw = file_get_contents('php://input', false, null, 0, 8192);
$d = json_decode($raw, true);
if (!is_array($d)) { $d = $_POST; }
if (!empty($d['website'])) { echo '{"ok":true}'; exit; }              // honeypot: pretend success

function clean($v, $max = 120) { $v = trim(preg_replace('/[\r\n\t]+/u', ' ', (string)$v)); return mb_substr(strip_tags($v), 0, $max); }
$f = [
  'name'     => clean($d['name'] ?? ''),
  'company'  => clean($d['company'] ?? ''),
  'role'     => clean($d['role'] ?? ''),
  'phone'    => clean($d['phone'] ?? '', 30),
  'branches' => clean($d['branches'] ?? '', 10),
  'meeting'  => in_array(($d['meeting'] ?? ''), ['online', 'in-person'], true) ? $d['meeting'] : '',
  'city'     => clean($d['city'] ?? '', 60),
  'time'     => clean($d['time'] ?? '', 80),
  'source'   => clean($d['source'] ?? '', 30),
];
$digits = preg_replace('/\D+/', '', strtr($f['phone'], ['۰'=>'0','۱'=>'1','۲'=>'2','۳'=>'3','۴'=>'4','۵'=>'5','۶'=>'6','۷'=>'7','۸'=>'8','۹'=>'9']));
if (mb_strlen($f['name']) < 3 || strlen($digits) < 7) { http_response_code(422); echo '{"ok":false,"error":"invalid"}'; exit; }

$dir = __DIR__ . '/leads';
if (!is_dir($dir)) { @mkdir($dir, 0750, true); }
/* simple rate limit per IP */
$ip = $_SERVER['REMOTE_ADDR'] ?? '0';
$rl = $dir . '/rl-' . md5($ip) . '.txt';
$now = time(); $hits = [];
if (is_file($rl)) { $hits = array_filter(array_map('intval', explode(',', (string)file_get_contents($rl))), function ($t) use ($now) { return $t > $now - 3600; }); }
if (count($hits) >= $MAX_PER_HOUR) { http_response_code(429); echo '{"ok":false,"error":"rate"}'; exit; }
$hits[] = $now; file_put_contents($rl, implode(',', $hits), LOCK_EX);

$csv = $dir . '/leads-' . substr(hash('sha256', __FILE__ . php_uname()), 0, 12) . '.csv'; $new = !is_file($csv);   /* unguessable name + .htaccess deny */
$fh = fopen($csv, 'a');
if (!$fh) { http_response_code(500); echo '{"ok":false}'; exit; }
flock($fh, LOCK_EX);
if ($new) { fwrite($fh, "\xEF\xBB\xBF"); fputcsv($fh, ['date', 'name', 'company', 'role', 'phone', 'branches', 'meeting', 'city', 'preferred time', 'source', 'ip']); }
fputcsv($fh, [date('Y-m-d H:i'), $f['name'], $f['company'], $f['role'], $f['phone'], $f['branches'], $f['meeting'], $f['city'], $f['time'], $f['source'], $ip]);
flock($fh, LOCK_UN); fclose($fh);

if ($NOTIFY_EMAIL) {
  $meet = $f['meeting'] === 'in-person' ? 'حضوری' : ($f['meeting'] === 'online' ? 'آنلاین' : '-');
  $body = "درخواست جدید از سایت ActivePlano\n\nنام: {$f['name']}\nشرکت/فروشگاه: {$f['company']}\nسمت: {$f['role']}\nتلفن: {$f['phone']}\nتعداد شعبه: {$f['branches']}\nنوع جلسه: $meet\nشهر: {$f['city']}\nزمان پیشنهادی: {$f['time']}\nمنبع: {$f['source']}\n";
  $subject = '=?UTF-8?B?' . base64_encode('ActivePlano | درخواست ' . ($f['source'] === 'demo-meeting' ? 'جلسه' : 'دمو') . ': ' . $f['company']) . '?=';
  $host = preg_replace('/[^a-z0-9.\-]/i', '', $_SERVER['HTTP_HOST'] ?? 'localhost');
  @mail($NOTIFY_EMAIL, $subject, $body, "From: ActivePlano <no-reply@$host>\r\nContent-Type: text/plain; charset=UTF-8");
}
echo '{"ok":true}';
