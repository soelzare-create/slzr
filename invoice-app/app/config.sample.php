<?php
/**
 * Optional settings. To use, copy this file to app/config.php and edit.
 * Without app/config.php the defaults below are used.
 */
return [
    // Where the database and sessions are stored. Best: a folder OUTSIDE
    // public_html, e.g. '/home/USERNAME/daranx-data'. Must be writable by PHP.
    'data_dir' => __DIR__ . '/../data',

    // true only while troubleshooting: shows error details on screen.
    'debug' => false,
];
