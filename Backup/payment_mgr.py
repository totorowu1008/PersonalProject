from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

def get_db():
    return pymysql.connect(host='localhost', user='root', password='MySQL123', db='rewards', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

@app.route('/api/get_methods')
def get_methods():
    line_user_id = request.args.get('line_user_id')
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM user WHERE line_user_id=%s", (line_user_id,))
        user = cursor.fetchone()
        user_id = user['id'] if user else None

        cursor.execute("SELECT id, name FROM payment_methods")
        methods = cursor.fetchall()

        cursor.execute("SELECT payment_method_id FROM user_payment_methods WHERE user_id=%s", (user_id,))
        selected = [row['payment_method_id'] for row in cursor.fetchall()]

    return jsonify({'user_id': user_id, 'methods': methods, 'selected_method_ids': selected})

@app.route('/api/save_methods', methods=['POST'])
def save_methods():
    data = request.json
    user_id = data['user_id']
    method_ids = data['method_ids']
    custom_names = data.get('custom_names', [])
    conn = get_db()
    with conn.cursor() as cursor:
        # 新增自訂支付方式
        for name in custom_names:
            cursor.execute("INSERT INTO payment_methods (name) VALUES (%s)", (name,))
            conn.commit()
            cursor.execute("SELECT id FROM payment_methods WHERE name=%s", (name,))
            method_ids.append(cursor.fetchone()['id'])
        # 先刪除舊的
        cursor.execute("DELETE FROM user_payment_methods WHERE user_id=%s", (user_id,))
        # 再新增
        for mid in method_ids:
            cursor.execute("INSERT INTO user_payment_methods (user_id, payment_method_id) VALUES (%s, %s)", (user_id, mid))
        conn.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(port=50000, debug=True)
