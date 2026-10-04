<?php
defined('APP_DIR') || exit;

if (!is_post()) {
    redirect('home');
}
$_SESSION = [];
session_regenerate_id(true);
redirect('login');
