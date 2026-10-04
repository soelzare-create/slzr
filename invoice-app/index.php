<?php
/**
 * DaranX — پیش‌فاکتور، فاکتور و حساب مشتریان.
 *
 * Single entry point: every page is index.php?p=<page>, so the app runs on any
 * PHP host (in the domain root, a subdomain or a sub-folder) without URL rewriting.
 */
require __DIR__ . '/app/bootstrap.php';

// page => needs login
$routes = [
    'setup' => false, 'login' => false, 'logout' => true,
    'home' => true,
    'docs' => true, 'doc' => true, 'doc_action' => true,
    'customers' => true, 'customer' => true,
    'payments' => true, 'payment' => true,
    'settings' => true, 'backup' => true,
];

$page = query('p', 'home');
if (!isset($routes[$page])) {
    not_found();
}
if (!has_users() && $page !== 'setup') {
    redirect('setup');
}
if (is_post()) {
    csrf_check();
}
if ($routes[$page]) {
    require_login();
}

require APP_DIR . '/pages/' . $page . '.php';
