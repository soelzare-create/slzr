<?php
/**
 * SQLite database: one file under data/, created and migrated on first use.
 *
 * The file name carries a random suffix (data/db_<hex>.sqlite) so it cannot be
 * guessed even on a server that ignores data/.htaccess.
 */
defined('APP_DIR') || exit;

function db_file(): string
{
    $found = glob(DATA_DIR . '/db_*.sqlite') ?: [];
    if ($found) {
        return $found[0];
    }
    // First run: pick the name under a lock so parallel requests agree on one file.
    $lock = fopen(DATA_DIR . '/.lock', 'c');
    flock($lock, LOCK_EX);
    $found = glob(DATA_DIR . '/db_*.sqlite') ?: [];
    $file = $found ? $found[0] : DATA_DIR . '/db_' . bin2hex(random_bytes(8)) . '.sqlite';
    if (!$found) {
        touch($file);
    }
    flock($lock, LOCK_UN);
    fclose($lock);
    return $file;
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . db_file(), null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 10,
        ]);
        $pdo->exec('PRAGMA foreign_keys = ON');
        db_migrate($pdo);
    }
    return $pdo;
}

/** Run $fn inside a write transaction (BEGIN IMMEDIATE serializes writers). */
function tx(callable $fn)
{
    $pdo = db();
    $pdo->exec('BEGIN IMMEDIATE');
    try {
        $result = $fn($pdo);
        $pdo->exec('COMMIT');
        return $result;
    } catch (Throwable $ex) {
        $pdo->exec('ROLLBACK');
        throw $ex;
    }
}

/** Schema migrations, tracked with PRAGMA user_version. Append new steps only. */
function db_migrate(PDO $pdo): void
{
    $steps = [
        1 => "
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                pass_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE settings (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL
            );
            CREATE TABLE login_attempts (
                k TEXT NOT NULL,
                ts INTEGER NOT NULL
            );
            CREATE INDEX login_attempts_k ON login_attempts(k, ts);

            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_key TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                opening_balance INTEGER NOT NULL DEFAULT 0,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            -- Proformas (qot) and invoices (inv). Only active invoices make the
            -- customer a debtor; totals are computed server-side on save.
            CREATE TABLE docs (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL CHECK (type IN ('qot', 'inv')),
                number TEXT NOT NULL,
                date TEXT NOT NULL,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                cust_name TEXT NOT NULL,
                cust_address TEXT NOT NULL DEFAULT '',
                cust_phone TEXT NOT NULL DEFAULT '',
                subtotal INTEGER NOT NULL DEFAULT 0,
                discount INTEGER NOT NULL DEFAULT 0,
                vat_on INTEGER NOT NULL DEFAULT 0,
                vat_rate REAL NOT NULL DEFAULT 10,
                vat_amount INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
                source_id INTEGER REFERENCES docs(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (type, number)
            );
            CREATE INDEX docs_customer ON docs(customer_id, type, status);
            CREATE INDEX docs_source ON docs(source_id);
            CREATE INDEX docs_date ON docs(type, date);

            CREATE TABLE doc_items (
                id INTEGER PRIMARY KEY,
                doc_id INTEGER NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
                pos INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                qty REAL,
                price INTEGER,
                line_total INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX doc_items_doc ON doc_items(doc_id, pos);

            -- Money received from a customer; reduces their debt.
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                amount INTEGER NOT NULL CHECK (amount > 0),
                date TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE INDEX payments_customer ON payments(customer_id, date);
        ",
    ];

    $version = (int) $pdo->query('PRAGMA user_version')->fetchColumn();
    foreach ($steps as $v => $sql) {
        if ($v <= $version) {
            continue;
        }
        $pdo->exec('BEGIN IMMEDIATE');
        try {
            // Re-check under the write lock: a parallel request may have migrated.
            if ((int) $pdo->query('PRAGMA user_version')->fetchColumn() < $v) {
                $pdo->exec($sql);
                $pdo->exec('PRAGMA user_version = ' . (int) $v);
            }
            $pdo->exec('COMMIT');
        } catch (Throwable $ex) {
            $pdo->exec('ROLLBACK');
            throw $ex;
        }
    }
}
