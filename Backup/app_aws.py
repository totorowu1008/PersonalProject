了解！我將幫您把您之前的 Flask 版 LINE Bot 程式，改寫成可以部署在 AWS Lambda 上，並由 API Gateway 轉接的可執行完整版本。  
會保留您的主要邏輯與功能，改動重點如下：

- Flask 的 `app.route` 改成 `lambda_handler`
- 讀取設定改成環境變數（不再用 config.ini）
- 日誌改用標準 `logging`（Lambda 可自動輸出到 CloudWatch）
- 保留原有所有事件處理函式和主要功能流程

# 完整 Lambda 版示範程式碼

```python
# -*- coding: utf-8 -*-
import os
import json
import logging
from linebot.v3 import (
    WebhookHandler, Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage, TemplateMessage, ButtonsTemplate, URIAction, MessageAction,
    QuickReply, QuickReplyItem, ShowLoadingAnimationRequest
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import FollowEvent, MessageEvent, PostbackEvent, TextMessageContent
import google.generativeai as genai

# 請自行實作或匯入您之前 db 模組中的 get_db_connection
import db

# --- 讀取必要的環境變數 ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LIFF_PAYMENT_MANAGER_URL = os.environ.get('LIFF_PAYMENT_MANAGER_URL')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LIFF_PAYMENT_MANAGER_URL, GEMINI_API_KEY]):
    raise RuntimeError("必須設定所有環境變數: LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LIFF_PAYMENT_MANAGER_URL, GEMINI_API_KEY")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

user_states = {}

get_db_connection = db.get_db_connection  # 請確保此函式可用

payment_manager_url = f"https://personalproject-je9f.onrender.com/userid/"  # 依實際改


# ------ 您先前實作的各功能函式(包含：get_user_id、create_main_menu、start_consumption_flow、get_gemini_recommendation 等) ------

def get_payment_options(type_filter):
    logger.info('從資料庫獲取支付選項')
    conn = get_db_connection()
    if not conn:
        return []
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, open_url, apply_url, type FROM payment_options WHERE type = %s", (type_filter,))
        result = cursor.fetchall()
    conn.close()
    return result

def get_all_payment_options():
    logger.info('從資料庫獲取所有支付選項')
    conn = get_db_connection()
    if not conn:
        return []
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, open_url, apply_url, type FROM payment_options")
        result = cursor.fetchall()
    conn.close()
    return result

def get_user_id(line_user_id):
    logger.info('根據 line_user_id 查找或建立使用者，並返回資料庫 user.id')
    conn = get_db_connection()
    if not conn:
        return None
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE line_user_id = %s", (line_user_id,))
        user = cursor.fetchone()
        if user:
            user_id = user['id']
        else:
            cursor.execute("INSERT INTO users (line_user_id) VALUES (%s)", (line_user_id,))
            conn.commit()
            user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user_payment_methods(user_id):
    logger.info('獲取使用者已有的支付工具')
    conn = get_db_connection()
    if not conn:
        return [], []
    with conn.cursor() as cursor:
        sql = """
            SELECT po.name, po.type, po.open_url, po.apply_url
            FROM user_payment_methods upm
            JOIN payment_options po ON upm.payment_option_id = po.id
            WHERE upm.user_id = %s
        """
        cursor.execute(sql, (user_id,))
        methods = cursor.fetchall()
    conn.close()

    mobile_payments = [m for m in methods if m['type'] == 'mobile']
    credit_cards = [m for m in methods if m['type'] == 'credit_card']

    return mobile_payments, credit_cards

def create_main_menu(line_user_id):
    user_db_id = get_user_id(line_user_id)
    logger.info('建立主選單 TemplateMessage')
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
    logger.info('開始消費推薦流程')
    user_states[line_user_id] = {'step': 'awaiting_category'}
    quick_reply_items = [
        QuickReplyItem(action=MessageAction(label=cat, text=cat))
        for cat in ["餐飲", "購物", "交通", "娛樂", "網購"]
    ]
    api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(
                text="請告訴我這次的消費類別是什麼？\n(例如：餐飲、購物、繳費...)\n或直接點選下方建議類別。",
                quick_reply=QuickReply(items=quick_reply_items)
            )]
        )
    )

def save_transaction(user_id, category, amount, recommendations):
    logger.info('將交易與推薦結果存入資料庫')
    conn = get_db_connection()
    if not conn:
        return
    with conn.cursor() as cursor:
        sql = """
            INSERT INTO transactions (user_id, category, amount, recommended_options)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, category, amount, json.dumps(recommendations, ensure_ascii=False)))
    conn.commit()
    conn.close()

def format_recommendation_messages(reco_data):
    logger.info('將 Gemini 回傳的 JSON 格式化為 LINE 的 TemplateMessage')
    messages = []
    all_payment_options = {opt['name']: opt for opt in get_all_payment_options()}
    existing_reco = reco_data.get('existing_tools_recommendation')
    if existing_reco and existing_reco.get('recommendations'):
        for item in existing_reco['recommendations']:
            name = item.get('name')
            percent = item.get('percent', 0)
            cashback = item.get('cashback', '0元')
            reason = name + "：" + item.get('reason', '無特別理由')
            option_details = all_payment_options.get(name)

            action = None  # 若您想加入按鈕可自訂
            if action:
                messages.append(TemplateMessage(
                    alt_text=f"推薦：{name}",
                    template=ButtonsTemplate(title=f"推薦使用：{name}", text=reason, actions=[action])
                ))
            else:
                messages.append(TemplateMessage(
                    alt_text="推薦理由",
                    template=ButtonsTemplate(
                        text=f"【{name}】\n預估回饋：{percent} 回饋金：{cashback}",
                        actions=[MessageAction(label='查看詳情', text=reason)]
                    )
                ))
    else:
        messages.append(TextMessage(text="您現有的支付工具中，本次消費沒有特別合適的推薦。"))

    if not messages:
        return [TextMessage(text="抱歉，目前無法提供有效的建議。")]

    return messages

def get_gemini_recommendation(line_user_id, reply_token, api: MessagingApi):
    logger.info('呼叫 Gemini API 並回覆推薦結果')
    state = user_states.get(line_user_id)
    if not state:
        return
    user_id = get_user_id(line_user_id)
    category = state.get('category')
    amount = state.get('amount')

    mobile_payments, credit_cards = get_user_payment_methods(user_id)
    user_methods_str = ", ".join([p['name'] for p in mobile_payments] + [c['name'] for c in credit_cards])
    if not user_methods_str:
        user_methods_str = "無"

    all_options = get_all_payment_options()
    all_options_str = ", ".join([opt['name'] for opt in all_options])

    prompt = f"""
你是一位台灣地區的信用卡與行動支付優惠專家。請根據以下資訊，為使用者提供支付建議。

# 使用者資訊
- **本次消費類別**: {category}
- **預估消費金額**: {amount}元
- **使用者目前擁有的支付工具**: {user_methods_str}

# 任務
請嚴格按照指定的 JSON 格式回傳，不要有任何額外的文字或解釋。

- **就使用者「已有」的支付工具**: 從他擁有的工具中，選出最適合這次消費的前 5 名，並標示回饋%數，並自動計算預估回饋金。如果他沒有任何工具，或沒有適合的，請在 `recommendations` 中回傳空陣列 `[]`。

# JSON 格式範本
{{
  "existing_tools_recommendation": {{
    "title": "使用您現有的工具，推薦如下(請注意高%數的限額)：",
    "recommendations": [
      {{"name": "支付工具名稱", "percent": "%數", "cashback": "n元", "reason": "推薦理由"}},
    ]
  }}
}}
"""

    try:
        api.push_message(PushMessageRequest(to=line_user_id, messages=[TextMessage(text="正在為您分析最佳支付方式，請稍候...")]))

        response = gemini_model.generate_content(prompt)
        cleaned_response_text = response.text.strip().replace("``````", "")
        recommendations = json.loads(cleaned_response_text)

        logger.info(f"刷卡內容：{user_id}, {category}, {amount}, {recommendations}")
        save_transaction(user_id, category, amount, recommendations)

        reply_messages = format_recommendation_messages(recommendations)
        logger.info(f"回覆訊息：{reply_messages}")
        api.push_message(PushMessageRequest(to=line_user_id, messages=reply_messages))

    except Exception as e:
        logger.error(f"Gemini API 或後續處理出錯: {e}")
        api.push_message(PushMessageRequest(to=line_user_id, messages=[TextMessage(text="抱歉，分析時發生錯誤，請稍後再試。")]))

# --- 事件處理器 ---

@handler.add(FollowEvent)
def handle_follow(event):
    logger.info(f"FollowEvent received for user: {event.source.user_id}")
    line_user_id = event.source.user_id
    get_user_id(line_user_id)  # 確保在資料庫

    reply_message = TextMessage(text="歡迎使用 回饋達人！")

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[reply_message]
                )
            )
            line_bot_api.push_message(
                PushMessageRequest(
                    to=line_user_id,
                    messages=[create_main_menu(line_user_id)]
                )
            )
        except Exception as e:
            logger.error(f"Error in handle_follow: {e}")

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    logger.info('處理文字訊息事件')
    text = event.message.text
    line_user_id = event.source.user_id
    reply_token = event.reply_token
    logger.info(f"MessageEvent from {line_user_id}: '{text}'")
    state = user_states.get(line_user_id)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(
                chatId=line_user_id,
                loadingSeconds=20,
                reply_token=reply_token
            )
        )
        try:
            if text == "智慧消費推薦":
                logger.info("Matched '智慧消費推薦'")
                start_consumption_flow(line_user_id, reply_token, line_bot_api)
            elif text == "管理支付方式":
                logger.info("Matched '管理支付方式'")
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
                                        actions=[URIAction(label='前往管理', uri=payment_manager_url + str(user_db_id))]
                                    )
                                )
                            ]
                        )
                    )
                else:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text="抱歉，無法獲取您的用戶ID，請稍後再試。")]
                        )
                    )
            elif state and state.get('step') == 'awaiting_category':
                logger.info("State awaiting_category")
                state['category'] = text
                state['step'] = 'awaiting_amount'
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=f"好的，消費類別是「{text}」。\n請輸入您的預估消費金額（純數字）：")]
                    )
                )
            elif state and state.get('step') == 'awaiting_amount':
                logger.info("State awaiting_amount")
                if text.isdigit():
                    state['amount'] = int(text)
                    state['step'] = 'done'
                    get_gemini_recommendation(line_user_id, reply_token, line_bot_api)
                    user_states.pop(line_user_id, None)  # 清除狀態
                else:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text="請輸入有效的純數字金額。")]
                        )
                    )
            else:
                logger.info("Default: send main menu")
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[create_main_menu(line_user_id)]
                    )
                )
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")

@handler.add(PostbackEvent)
def handle_postback(event):
    logger.info(f"PostbackEvent received: {event.postback.data}")
    # 目前沒實作Postback內容，可自行擴充


# --- Lambda 入口函式 ---

def lambda_handler(event, context):
    logger.info(f"Lambda event: {json.dumps(event)[:500]}")  # 簡短印出
    try:
        headers = event.get('headers') or {}
        signature = headers.get('x-line-signature') or headers.get('X-Line-Signature')
        body = event.get('body')
        if body is None:
            return {
                'statusCode': 400,
                'body': 'Bad Request: no body'
            }
        handler.handle(body, signature)
        return {
            'statusCode': 200,
            'body': 'OK',
            'headers': {
                'Content-Type': 'text/plain'
            }
        }
    except InvalidSignatureError:
        logger.error("Invalid signature detected")
        return {
            'statusCode': 400,
            'body': 'Invalid signature'
        }
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }
