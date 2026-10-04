<?php
/** Download a consistent copy of the SQLite database. */
defined('APP_DIR') || exit;

$file = db_file();
$pdo = db();
$pdo->exec('BEGIN IMMEDIATE'); // hold writers off while the file is copied out
try {
    header('Content-Type: application/octet-stream');
    header('Content-Disposition: attachment; filename="daranx-backup-' . str_replace('/', '-', jtoday()) . '.sqlite"');
    header('Content-Length: ' . filesize($file));
    readfile($file);
} finally {
    $pdo->exec('COMMIT');
}
exit;
