# -*- coding: utf-8 -*-
import configparser # 新增 configparser
from flask import Flask, request, abort
import os

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# --- 組態設定 (從 config.ini 讀取) ---
config = configparser.ConfigParser()
# 確保檔案路徑正確，並使用 utf-8 編碼讀取
config.read('config.ini', encoding='utf-8')

# LINE 設定
LINE_CHANNEL_ACCESS_TOKEN = config.get('LINE', 'CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = config.get('LINE', 'CHANNEL_SECRET')

# --- 初始化 ---
app = Flask(__name__)

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 50000))
    app.run(host='0.0.0.0', port=port,debug=True)