# LINE BOT 架構：接收信用卡圖片，辨識銀行與卡片名稱

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage

import os
import cv2
import pytesseract
import requests
import re
from PIL import Image

# ====== LINE BOT 設定 ======
app = Flask(__name__)
line_bot_api = LineBotApi('你的 Channel Access Token')
handler = WebhookHandler('你的 Channel Secret')

# ====== 主程式入口 ======
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ====== 處理圖片訊息 ======
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)

    image_path = f"card_{message_id}.jpg"
    with open(image_path, 'wb') as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    result = process_card_image(image_path)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

# ====== 卡片辨識邏輯整合 ======
def process_card_image(image_path):
    try:
        # 讀圖 + 預處理
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)

        # === OCR 擷取卡號 ===
        text = pytesseract.image_to_string(gray)
        card_number = extract_card_number(text)

        result = []

        if card_number:
            result.append(f"卡號：{card_number}")
            bin_info = lookup_bin(card_number[:6])
            if bin_info:
                result.append(f"發卡銀行：{bin_info.get('bank', {}).get('name', '未知')}")
                result.append(f"卡片品牌：{bin_info.get('scheme', 'N/A')} / {bin_info.get('type', 'N/A')}")
        else:
            result.append("未能辨識卡號。")

        # === 卡片名稱（卡面比對，這裡先用簡單關鍵字範例） ===
        card_names = ['悠遊聯名卡', '白金卡', '世界卡', '商務卡', '御璽卡']
        for name in card_names:
            if name in text:
                result.append(f"辨識卡片名稱：{name}")

        if len(result) == 1:
            result.append("也許你可以換個角度再拍一次喔！")

        return "\n".join(result)

    except Exception as e:
        return f"辨識失敗：{str(e)}"

# ====== 擷取卡號 ======
def extract_card_number(text):
    matches = re.findall(r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})', text)
    if matches:
        return matches[0].replace(" ", "").replace("-", "")
    return None

# ====== 查詢 BIN API ======
def lookup_bin(bin_number):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

# ====== 啟動 Flask ======
if __name__ == "__main__":
    app.run(debug=True)
