# -*- coding: utf-8 -*-
"""LINE Bot 主程式（安全啟動版 + Gemini API 消費推薦流程）"""

import os
import time
import json
import logging
from flask import Flask, request, abort

# 嘗試載入外部 SDK
try:
    from linebot.v3 import WebhookHandler
    from linebot.v3.exceptions import InvalidSignatureError
    from linebot.v3.messaging import (
        Configuration,
        ApiClient,
        MessagingApi,
        ReplyMessageRequest,
        PushMessageRequest,
        TextMessage,
        TemplateMessage,
        ButtonsTemplate,
        URIAction,
        QuickReply,
        QuickReplyItem,
        MessageAction,
        ShowLoadingAnimationRequest
    )
    from linebot.v3.webhooks import FollowEvent, MessageEvent, PostbackEvent, TextMessageContent
    import google.generativeai as genai
except ImportError as e:
    logging.warning(f"LINE/Gemini SDK 載入失敗：{e}")

# 嘗試載入自訂 DB 模組
try:
    import db
except ImportError:
    db = None
    logging.warning("未找到 db 模組，資料庫功能將無法使用。")

# --- Flask 初始化 ---
app = Flask(__name__)
log_handler = logging.FileHandler('app.log', encoding='utf-8')
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

# --- 環境變數設定 ---
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_SECRET = os.environ.get('LINE_SECRET')
LINE_LIFF_URL = os.environ.get('LINE_LIFF_URL')
GEMINI_KEY = os.environ.get('GEMINI_KEY')
print(f"LINE_SECRET: {LINE_SECRET}")

# --- 全域資源延遲初始化 ---
_line_handler = None
_line_config = None
_gemini_model = None
user_states = {}
payment_manager_url = LINE_LIFF_URL.rstrip("/") + "/userid/"

# ===== 資料庫輔助函式 =====
def get_db_connection():
    """安全取得資料庫連線"""
    if db and hasattr(db, 'get_db_connection'):
        try:
            return db.get_db_connection()
        except Exception as e:
            app.logger.error(f"資料庫連線失敗：{e}")
    return None

# ===== 外部服務初始化 =====
def init_line_bot():
    """延遲初始化 LINE Bot"""
    global _line_handler, _line_config
    if not _line_handler and LINE_ACCESS_TOKEN and LINE_SECRET:
        try:
            _line_config = Configuration(access_token=LINE_ACCESS_TOKEN)
            _line_handler = WebhookHandler(LINE_SECRET)
            app.logger.info("LINE Bot 初始化成功")
        except Exception as e:
            app.logger.error(f"LINE Bot 初始化失敗：{e}")
    return _line_handler, _line_config

def init_gemini():
    """延遲初始化 Gemini"""
    global _gemini_model
    if not _gemini_model and GEMINI_KEY:
        try:
            genai.configure(api_key=GEMINI_KEY)
            _gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            app.logger.info("Gemini 初始化成功")
        except Exception as e:
            app.logger.error(f"Gemini 初始化失敗：{e}")
    return _gemini_model

# ===== 健康檢查路由 =====
@app.route("/")
def index():
    return "OK", 200

# ===== LINE Webhook =====
@app.route("/callback", methods=['POST'])
def callback():
    """LINE webhook 入口"""
    handler, config = init_line_bot()
    if not handler:
        app.logger.error("LINE Bot 尚未正確初始化")
        return "Service unavailable", 503

    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
    return "OK"

# --- 接收 user id 並 redirect ---
# app route 用於接收 user id 並重定向到支付方式管理頁面
@app.route("/userid/<user_id>")
def redirect_to_payment_manager(user_id):
    print('接收 user id 並重定向到支付方式管理頁面')
    if not user_id:
        app.logger.error("未提供有效的 user_id")
        return "錯誤：未提供有效的 user_id", 400

    # 構建重定向 URL
    redirect_url = f"{LINE_LIFF_URL}/pmgr.php?user_id={user_id}"
    app.logger.info(f"Redirecting to payment manager: {redirect_url}")
    return f'<html><body><script>window.location.href="{redirect_url}";</script></body></html>', 302

# ===== 資料庫相關功能 =====
def get_user_id(line_user_id):
    """依 LINE 使用者 ID 取得或建立資料庫 user_id"""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE line_user_id = %s", (line_user_id,))
            user = cursor.fetchone()
            if user:
                return user['id']
            cursor.execute("INSERT INTO users (line_user_id) VALUES (%s)", (line_user_id,))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        app.logger.error(f"get_user_id 失敗: {e}")
    finally:
        conn.close()
    return None

def get_all_payment_options():
    """取得所有支付工具選項"""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, open_url, apply_url, type FROM payment_options")
            return cursor.fetchall()
    except Exception as e:
        app.logger.error(f"get_all_payment_options 失敗: {e}")
    finally:
        conn.close()
    return []

def get_user_payment_methods(user_id):
    """取得使用者已設定的支付工具"""
    conn = get_db_connection()
    if not conn: return [], []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT po.name, po.type, po.open_url, po.apply_url
                FROM user_payment_methods upm
                JOIN payment_options po ON upm.payment_option_id = po.id
                WHERE upm.user_id = %s
            """, (user_id,))
            methods = cursor.fetchall()
        mobile_payments = [m for m in methods if m['type'] == 'mobile']
        credit_cards = [m for m in methods if m['type'] == 'credit_card']
        return mobile_payments, credit_cards
    except Exception as e:
        app.logger.error(f"get_user_payment_methods 失敗: {e}")
    finally:
        conn.close()
    return [], []

# ===== 功能流程 =====
def create_main_menu(line_user_id):
    """建立主選單按鈕"""
    user_db_id = get_user_id(line_user_id) or 0
    return TemplateMessage(
        alt_text='主選單',
        template=ButtonsTemplate(
            title='回饋達人',
            text='請選擇您要使用的服務：',
            actions=[
                MessageAction(label='智慧消費推薦', text='智慧消費推薦'),
                URIAction(label='管理支付方式', uri=payment_manager_url + str(user_db_id))
            ]
        )
    )

def start_consumption_flow(line_user_id, reply_token, api: MessagingApi):
    """開始消費推薦流程"""
    user_states[line_user_id] = {'step': 'awaiting_category'}
    quick_reply_items = [QuickReplyItem(action=MessageAction(label=cat, text=cat))
                         for cat in ["餐飲", "購物", "交通", "娛樂", "網購"]]
    api.reply_message(
        ReplyMessageRequest(reply_token=reply_token,
                            messages=[TextMessage(text="請選擇消費類別：",
                                                   quick_reply=QuickReply(items=quick_reply_items))])
    )

def get_gemini_recommendation(line_user_id, reply_token, api: MessagingApi):
    """呼叫 Gemini API 取得消費推薦"""
    model = init_gemini()
    if not model:
        api.push_message(PushMessageRequest(to=line_user_id,
                                            messages=[TextMessage(text="抱歉，系統未設定 Gemini API")]))
        return
    state = user_states.get(line_user_id)
    if not state:
        return

    user_id = get_user_id(line_user_id)
    category = state.get('category')
    amount = state.get('amount')
    mobile_payments, credit_cards = get_user_payment_methods(user_id)
    user_methods_str = ", ".join([p['name'] for p in mobile_payments] + [c['name'] for c in credit_cards]) or "無"

    # 生成 prompt
    prompt = f"""
    你是一位台灣地區的信用卡與行動支付優惠專家。請根據以下資訊，為使用者提供支付建議：
    類別：{category}
    金額：{amount}
    已有支付工具：{user_methods_str}
    請以 JSON 格式回傳：
    {{
      "existing_tools_recommendation": {{
        "title": "推薦列表",
        "recommendations": [
          {{"name": "支付工具名稱", "percent": "%數", "cashback": "n元", "reason": "理由"}}
        ]
      }}
    }}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        recommendations = json.loads(cleaned_response_text)
        reply_messages = format_recommendation_messages(recommendations)
        api.push_message(PushMessageRequest(to=line_user_id, messages=reply_messages))
    except Exception as e:
        app.logger.error(f"Gemini 推薦流程錯誤: {e}")
        api.push_message(PushMessageRequest(to=line_user_id,
                                            messages=[TextMessage(text="抱歉，分析時發生錯誤")]))

def format_recommendation_messages(reco_data):
    """將 Gemini 回傳的 JSON 格式化為 LINE 訊息"""
    messages = []
    all_payment_options = {opt['name']: opt for opt in get_all_payment_options()}
    existing_reco = reco_data.get('existing_tools_recommendation')
    if existing_reco and existing_reco.get('recommendations'):
        for item in existing_reco['recommendations']:
            name = item.get('name')
            percent = item.get('percent', 0)
            cashback = item.get('cashback', '0元')
            reason = f"{name}：{item.get('reason', '無理由')}"
            messages.append(TemplateMessage(
                alt_text=f"推薦：{name}",
                template=ButtonsTemplate(text=f"【{name}】回饋：{percent} 預估金額：{cashback}",
                                         actions=[MessageAction(label='查看詳情', text=reason)])
            ))
    else:
        messages.append(TextMessage(text="沒有合適的推薦"))
    return messages

# ===== LINE 事件處理 =====
handler, _ = init_line_bot()
if handler:
    @handler.add(FollowEvent)
    def handle_follow(event):
        """處理使用者加入好友事件"""
        app.logger.info(f"FollowEvent from {event.source.user_id}")
        line_user_id = event.source.user_id
        get_user_id(line_user_id)
        _, config = init_line_bot()
        with ApiClient(config) as api_client:
            line_bot_api = MessagingApi(api_client)
            try:
                line_bot_api.reply_message(
                    ReplyMessageRequest(reply_token=event.reply_token,
                                        messages=[TextMessage(text="歡迎使用 回饋達人！")])
                )
                line_bot_api.push_message(
                    PushMessageRequest(to=line_user_id,
                                       messages=[create_main_menu(line_user_id)])
                )
            except Exception as e:
                app.logger.error(f"handle_follow 錯誤: {e}")

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        """處理使用者文字訊息"""
        text = event.message.text
        line_user_id = event.source.user_id
        reply_token = event.reply_token
        _, config = init_line_bot()
        with ApiClient(config) as api_client:
            line_bot_api = MessagingApi(api_client)
            try:
                if text == "智慧消費推薦":
                    start_consumption_flow(line_user_id, reply_token, line_bot_api)
                elif text == "管理支付方式":
                    #print(f"管理支付方式設定頁面 {LINE_LIFF_URL}")
                    user_db_id = get_user_id(line_user_id)
                    if user_db_id:
                        line_bot_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=reply_token,
                                messages=[
                                    TextMessage(text="請點擊下方連結管理您的支付方式："),
                                    TemplateMessage(
                                        alt_text="管理支付方式",
                                        template=ButtonsTemplate(
                                            title='支付方式管理',
                                            text='點擊按鈕進入設定頁面',
                                            actions=[URIAction(label='前往管理',
                                                               uri=payment_manager_url + str(user_db_id))]
                                        )
                                    )
                                ]
                            )
                        )
                    else:
                        line_bot_api.reply_message(
                            ReplyMessageRequest(reply_token=reply_token,
                                                messages=[TextMessage(text="無法取得您的用戶ID")])
                        )
                elif user_states.get(line_user_id, {}).get('step') == 'awaiting_category':
                    # 記錄類別
                    user_states[line_user_id]['category'] = text
                    user_states[line_user_id]['step'] = 'awaiting_amount'
                    line_bot_api.reply_message(
                        ReplyMessageRequest(reply_token=reply_token,
                                            messages=[TextMessage(text=f"好的，消費類別是「{text}」，請輸入金額：")])
                    )
                elif user_states.get(line_user_id, {}).get('step') == 'awaiting_amount':
                    if text.isdigit():
                        user_states[line_user_id]['amount'] = int(text)

                        # --- 在呼叫 Gemini API 之前先顯示等待訊息並載入動畫 ---
                        line_bot_api.reply_message(
                            ReplyMessageRequest(reply_token=reply_token,
                                                messages=[TextMessage(text="正在分析您的消費資料，請稍候...")])
                        )

                        line_bot_api.show_loading_animation(
                            ShowLoadingAnimationRequest(
                                chatId=line_user_id,
                                loadingSeconds=30, # 載入時間可自訂，最長60秒
                            )
                        )
                        
                        # 呼叫 Gemini API 獲取推薦
                        get_gemini_recommendation(line_user_id, reply_token, line_bot_api)
                        user_states.pop(line_user_id, None)
                    else:
                        line_bot_api.reply_message(
                            ReplyMessageRequest(reply_token=reply_token,
                                                messages=[TextMessage(text="請輸入有效的金額（純數字）")])
                        )
                else:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(reply_token=reply_token,
                                            messages=[create_main_menu(line_user_id)])
                    )
            except Exception as e:
                app.logger.error(f"handle_message 錯誤: {e}")
                # 若無法識別訊息，回覆主選單
                line_bot_api.reply_message(
                    ReplyMessageRequest(reply_token=reply_token,
                            messages=[create_main_menu(line_user_id)])
                )

# ===== 主程式啟動 =====
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)