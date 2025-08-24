# db.py
import mysql.connector
import os
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 組態設定 (從環境變數讀取) ---
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_DATABASE = os.environ.get('DB_DATABASE')
DB_PORT = os.environ.get('DB_PORT', '3306')  # MySQL 預設 port 是 3306

def get_db_connection():
    """
    建立並回傳一個資料庫連線。
    如果連線失敗，將會印出錯誤訊息並回傳 None。
    """
    logger.info('嘗試建立資料庫連線...')
    logger.debug(f"連線參數: host={DB_HOST}, user={DB_USER}, database={DB_DATABASE}, port={DB_PORT}")
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            port=DB_PORT
        )
        logger.info('資料庫連線成功！')
        return connection
    except Exception as e:
        logger.error(f"資料庫連線失敗: {e}")
        return None
