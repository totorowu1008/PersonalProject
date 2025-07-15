<html>
<head>
    <title>Payment Manager</title>
</head>
<body>
    <h1>支付方式管理</h1>
    <form action="payment_methods_save.php" method="post">
    <?php
        require_once 'db.php';
        
        if (isset($_POST['user_id'])) {
            $user_id = $_POST['user_id'];
        } else if (isset($_GET['user_id'])) {
            $user_id = $_GET['user_id'];
        } else {
            $user_id = "1";
        }

        $db = get_db();
        $stmt = $db->prepare("SELECT payment_option_id FROM user_payment_methods where user_id = $user_id");
        $stmt->execute();
        $selected_methods = $stmt->fetchAll(PDO::FETCH_COLUMN, 0);
        
        $stmt = $db->prepare("SELECT * FROM payment_methods order by type, rank, id");
        $stmt->execute();
        $methods = $stmt->fetchAll(PDO::FETCH_ASSOC);
        foreach ($methods as $method) {
            $checked = '';
            if (in_array($method['id'], $selected_methods)) {
                $checked = 'checked';
            }
            echo '<div>';
            echo '<input type="checkbox" name="method_' . htmlspecialchars($method['id'])  . '" ' . $checked . '>' . htmlspecialchars($method['name']);
            echo '</div>';
        }
    ?>
    </form> 
</body>
</html>