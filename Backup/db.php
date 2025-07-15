<?php
function get_db() {
    $host = 'localhost';
    $db = 'rewards';
    $user = 'root';
    $pass = 'MySQL123';
    $charset = 'utf8mb4';

    $conn = new PDO("mysql:host=$host;dbname=$db;charset=$charset", $user, $pass);
    //$conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    //$conn->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    return $conn;
}