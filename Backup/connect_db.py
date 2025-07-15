import pymysql

# 資料庫連線設定
DB_HOST = config.get('DATABASE', 'HOST')
DB_USER = config.get('DATABASE', 'USER')
DB_PASSWORD = config.get('DATABASE', 'PASSWORD')
DB_DATABASE = config.get('DATABASE', 'DATABASE')

# --- 資料庫輔助函式 ---
def get_db_connection():
    print('建立並返回資料庫連線')
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        print('建立資料庫連線成功！')
        return connection
    except pymysql.MySQLError as e:
        app.logger.error(f"資料庫連線失敗: {e}")
        return None
