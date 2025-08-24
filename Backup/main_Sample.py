import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import mysql.connector

# 從環境變數中讀取設定
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
db_host = os.environ.get('DB_HOST') # 這裡將使用 VM 的私有 IP
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

app = Flask(__name__)

# LINE Bot Webhook 處理
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        # 連線到 MySQL
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # 這裡可以執行您的資料庫查詢
        cursor.execute("SELECT message FROM bot_responses WHERE keyword = %s", (event.message.text,))
        result = cursor.fetchone()

        if result:
            reply_message = result[0]
        else:
            reply_message = "我目前無法理解您的意思。"
        
    except Exception as e:
        reply_message = f"資料庫連線失敗：{e}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))