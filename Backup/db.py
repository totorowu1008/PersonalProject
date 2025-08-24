# db.py
import mysql.connector
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
#DB_PORT = config.get('DATABASE', 'PORT', fallback='5432') # PostgreSQL 預設 port 是 5432

def get_db_connection():
    """
    建立並回傳一個資料庫連線。
    使用 psycopg2 函式庫連線到 PostgreSQL 資料庫。
    如果連線失敗，將會印出錯誤訊息並回傳 None。
    """
    logger.info('嘗試建立資料庫連線...')
    try:
        # 連線到 MySQL
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = conn.cursor()
        logger.info('資料庫連線成功！')
        return connection
    except Exception as e: # 捕獲 psycopg2 專屬的錯誤
        logger.error(f"資料庫連線失敗: {e}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == '__main__':
    # 範例用法：測試資料庫連線
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                # PostgreSQL 查詢當前資料庫名稱的語法是 current_database()
                cursor.execute("SELECT current_database();")
                record = cursor.fetchone()
                logger.info(f"您已連線到資料庫: {record[0]}") # DictCursor 在單欄查詢時，直接取 record[0] 即可
        except Exception as e:
            logger.error(f"執行查詢時發生錯誤: {e}")
        finally:
            conn.close()
    else:
        logger.error("無法建立資料庫連線。")