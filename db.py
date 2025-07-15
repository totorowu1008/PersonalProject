# db.py
import pymysql
import configparser
import os
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從 config.ini 讀取資料庫設定
config = configparser.ConfigParser()
# 假設 config.ini 在與 db.py 相同的目錄
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
if not os.path.exists(config_path):
    logger.error(f"錯誤：找不到 '{config_path}' 檔案。請確認檔案是否存在。")
    # 如果找不到 config.ini，可以選擇性地退出或使用預設值
    raise FileNotFoundError(f"config.ini 檔案未找到於 {config_path}")

config.read(config_path, encoding='utf-8')

DB_HOST = config.get('DATABASE', 'HOST')
DB_USER = config.get('DATABASE', 'USER')
DB_PASSWORD = config.get('DATABASE', 'PASSWORD')
DB_DATABASE = config.get('DATABASE', 'DATABASE')

def get_db_connection():
    """
    建立並回傳一個資料庫連線。
    使用 pymysql 函式庫連線到 MySQL 資料庫。
    如果連線失敗，將會印出錯誤訊息並回傳 None。
    """
    logger.info('嘗試建立資料庫連線...')
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor, # 讓 cursor 回傳字典形式的行，方便存取
            charset='utf8mb4'
        )
        logger.info('資料庫連線成功！')
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"資料庫連線失敗: {e}")
        return None

if __name__ == '__main__':
    # 範例用法：測試資料庫連線
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DATABASE();")
                record = cursor.fetchone()
                logger.info(f"您已連線到資料庫: {record['DATABASE()']}")
        except Exception as e:
            logger.error(f"執行查詢時發生錯誤: {e}")
        finally:
            conn.close()
    else:
        logger.error("無法建立資料庫連線。")

