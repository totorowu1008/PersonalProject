# -*- coding: utf-8 -*-
import os
import json
import pymysql
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction,
    URIAction,
    QuickReply,
    QuickReplyItem,
    MessageAction
)
from linebot.v3.webhooks import MessageEvent, PostbackEvent, FollowEvent
import google.generativeai as genai

# --- 組態設定 (請填入您的資訊) ---
# 從環境變數讀取，更安全
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'ssQrOOBQYh4dUUo4kelWkY6aLpEgtvHIAMNaG5hUbUO5eHFVFmDYaRNGWiNjuCPgiIN6HoTAw4oypmhMSBz0Oezt2/q9F1XxWikY8prUGBfdir05yddvDEjsG07yJ7RLGQH2GA4CjzK7C63Vla8IXQdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '60a59fdd8b5672af0a140196561b122b')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAS9LXxfsT50p3lka0BDM1wJU1TlCMQHak')

# 資料庫連線設定
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'MySQL123')
DB_DATABASE = os.getenv('DB_DATABASE', 'rewards')

# --- 初始化 ---
app = Flask(__name__)

# LINE Bot API 設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Gemini API 設定
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# 使用者狀態追蹤 (簡易版，正式上線建議使用 Redis 或資料庫)
user_states = {}

# --- 資料庫輔助函式 ---
def get_db_connection():
    """建立並返回資料庫連線"""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        return connection
    except pymysql.MySQLError as e:
        app.logger.error(f"資料庫連線失敗: {e}")
        return None

def get_payment_options(type_filter):
    """從資料庫獲取支付選項"""
    conn = get_db_connection()
    if not conn: return []
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM payment_options WHERE type = %s", (type_filter,))
        result = cursor.fetchall()
    conn.close()
    return result

def get_user_id(line_user_id):
    """根據 line_user_id 查找或建立使用者，並返回資料庫 user.id"""
    conn = get_db_connection()
    if not conn: return None
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
    """獲取使用者已有的支付工具"""
    conn = get_db_connection()
    if not conn: return [], []
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

# --- LINE Bot 主要路由 ---
@app.route("/callback", methods=['POST'])
def callback():
    """接收 LINE Webhook 的主要進入點"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel secret.")
        abort(400)
    return 'OK'

# --- LINE 事件處理器 ---
@handler.add(FollowEvent)
def handle_follow(event):
    """處理 '加入好友' 事件"""
    line_user_id = event.source.user_id
    get_user_id(line_user_id) # 確保使用者已在資料庫中
    
    reply_message = TextMessage(text="歡迎使用智慧消費推薦 Bot！\n請點擊下方選單開始。")
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message, create_main_menu()]
            )
        )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息事件"""
    text = event.message.text
    line_user_id = event.source.user_id
    reply_token = event.reply_token
    
    state = user_states.get(line_user_id)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        if text == "基本資料設定":
            start_registration(line_user_id, reply_token, line_bot_api)
        elif text == "智慧消費推薦":
            start_consumption_flow(line_user_id, reply_token, line_bot_api)
        elif state and state.get('step') == 'awaiting_category':
            # 儲存消費類別，並詢問金額
            state['category'] = text
            state['step'] = 'awaiting_amount'
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=f"好的，消費類別是「{text}」。\n請輸入您的預估消費金額（純數字）：")]
                )
            )
        elif state and state.get('step') == 'awaiting_amount':
            if text.isdigit():
                # 儲存金額，並觸發 Gemini 推薦
                state['amount'] = int(text)
                state['step'] = 'done'
                get_gemini_recommendation(line_user_id, reply_token, line_bot_api)
                user_states.pop(line_user_id, None) # 清除狀態
            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text="請輸入有效的純數字金額。")]
                    )
                )
        else:
            # 預設回覆或顯示主選單
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[create_main_menu()]
                )
            )

@handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件 (使用者點擊按鈕)"""
    data = event.postback.data
    line_user_id = event.source.user_id
    reply_token = event.reply_token
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 解析 postback data
        params = dict(x.split('=') for x in data.split('&'))
        action = params.get('action')
        
        if action == 'register_mobile':
            handle_mobile_selection(line_user_id, params, reply_token, line_bot_api)
        elif action == 'register_card':
            handle_card_selection(line_user_id, params, reply_token, line_bot_api)

# --- 功能流程函式 ---
def create_main_menu():
    """建立主選單 TemplateMessage"""
    return TemplateMessage(
        alt_text='主選單',
        template=ButtonsTemplate(
            title='智慧消費管家',
            text='請選擇您要使用的服務：',
            actions=[
                MessageAction(label='基本資料設定', text='基本資料設定'),
                MessageAction(label='智慧消費推薦', text='智慧消費推薦'),
            ]
        )
    )

def start_registration(line_user_id, reply_token, api: MessagingApi):
    """開始註冊流程，詢問行動支付"""
    user_states[line_user_id] = {'step': 'register_mobile', 'selections': []}
    
    mobile_options = get_payment_options('mobile')
    quick_reply_items = [
        QuickReplyItem(action=PostbackAction(label=opt['name'], data=f"action=register_mobile&id={opt['id']}", display_text=f"選擇 {opt['name']}"))
        for opt in mobile_options
    ]
    quick_reply_items.append(QuickReplyItem(action=PostbackAction(label="都沒有/選完了", data="action=register_mobile&id=done", display_text="都沒有/選完了")))

    api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="請選擇您擁有的行動支付（可複選），完成後請按「都沒有/選完了」。", quick_reply=QuickReply(items=quick_reply_items))]
        )
    )

def handle_mobile_selection(line_user_id, params, reply_token, api: MessagingApi):
    """處理行動支付選擇"""
    state = user_states.get(line_user_id)
    if not state or state.get('step') != 'register_mobile':
        return # 狀態不符，不處理

    selection_id = params.get('id')
    if selection_id == 'done':
        # 行動支付選擇完成，詢問信用卡
        ask_for_credit_cards(line_user_id, reply_token, api)
    else:
        # 記錄選擇
        if selection_id not in state['selections']:
            state['selections'].append(selection_id)
        # 可以在這裡回覆一個暫時的訊息，讓使用者知道已選擇
        api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=f"已加入選擇。請繼續選擇或按「都沒有/選完了」。")]
            )
        )

def ask_for_credit_cards(line_user_id, reply_token, api: MessagingApi):
    """詢問信用卡"""
    state = user_states.get(line_user_id)
    state['step'] = 'register_card'
    state['mobile_selections'] = state.pop('selections', []) # 將行動支付選擇暫存
    state['selections'] = [] # 重置選擇列表給信用卡用

    card_options = get_payment_options('credit_card')
    quick_reply_items = [
        QuickReplyItem(action=PostbackAction(label=opt['name'], data=f"action=register_card&id={opt['id']}", display_text=f"選擇 {opt['name']}"))
        for opt in card_options
    ]
    quick_reply_items.append(QuickReplyItem(action=PostbackAction(label="都沒有/選完了", data="action=register_card&id=done", display_text="都沒有/選完了")))

    api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="接下來，請選擇您擁有的信用卡（可複選），完成後請按「都沒有/選完了」。", quick_reply=QuickReply(items=quick_reply_items))]
        )
    )

def handle_card_selection(line_user_id, params, reply_token, api: MessagingApi):
    """處理信用卡選擇並儲存到資料庫"""
    state = user_states.get(line_user_id)
    if not state or state.get('step') != 'register_card':
        return

    selection_id = params.get('id')
    if selection_id == 'done':
        # 完成所有選擇，寫入資料庫
        user_id = get_user_id(line_user_id)
        all_selections = state.get('mobile_selections', []) + state.get('selections', [])
        
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                # 先清除舊資料
                cursor.execute("DELETE FROM user_payment_methods WHERE user_id = %s", (user_id,))
                # 插入新資料
                if all_selections:
                    values = [(user_id, int(pid)) for pid in all_selections]
                    cursor.executemany("INSERT INTO user_payment_methods (user_id, payment_option_id) VALUES (%s, %s)", values)
            conn.commit()
            conn.close()
        
        user_states.pop(line_user_id, None) # 清除狀態
        api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text="基本資料設定完成！")]
            )
        )
    else:
        # 記錄選擇
        if selection_id not in state['selections']:
            state['selections'].append(selection_id)
        api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=f"已加入選擇。請繼續選擇或按「都沒有/選完了」。")]
            )
        )

def start_consumption_flow(line_user_id, reply_token, api: MessagingApi):
    """開始消費推薦流程"""
    user_states[line_user_id] = {'step': 'awaiting_category'}
    
    # 預設幾個常用類別
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

def get_gemini_recommendation(line_user_id, reply_token, api: MessagingApi):
    """呼叫 Gemini API 並回覆推薦結果"""
    state = user_states.get(line_user_id)
    if not state: return

    user_id = get_user_id(line_user_id)
    category = state.get('category')
    amount = state.get('amount')

    # 獲取使用者現有工具和所有工具
    mobile_payments, credit_cards = get_user_payment_methods(user_id)
    user_methods_str = ", ".join([p['name'] for p in mobile_payments] + [c['name'] for c in credit_cards])
    if not user_methods_str: user_methods_str = "無"

    all_options = get_payment_options('mobile') + get_payment_options('credit_card')
    all_options_str = ", ".join([opt['name'] for opt in all_options])

    # 建立給 Gemini 的 Prompt
    prompt = f"""
    你是一位台灣地區的信用卡與行動支付優惠專家。請根據以下資訊，為使用者提供支付建議。

    # 使用者資訊
    - **本次消費類別**: {category}
    - **預估消費金額**: 新台幣 {amount} 元
    - **使用者目前擁有的支付工具**: {user_methods_str}

    # 任務
    請分為兩部分提供建議，並嚴格按照指定的 JSON 格式回傳，不要有任何額外的文字或解釋。

    1.  **就使用者「已有」的支付工具**: 從他擁有的工具中，推薦最適合這次消費的前 3 名，並說明推薦原因（例如：高回饋、符合通路加碼等）。如果他沒有任何工具，或沒有適合的，請在 `recommendations` 中回傳空陣列 `[]`。
    2.  **就使用者「尚未擁有」的支付工具**: 從台灣市場上所有主流支付工具中（參考列表：{all_options_str}），推薦最適合這次消費的前 3 名，並說明申辦後的潛在好處。

    # JSON 格式範本
    {{
      "existing_tools_recommendation": {{
        "title": "使用您現有的工具，推薦如下：",
        "recommendations": [
          {{
            "name": "支付工具名稱",
            "reason": "推薦原因"
          }}
        ]
      }},
      "new_tools_recommendation": {{
        "title": "若申辦新工具，可考慮：",
        "recommendations": [
          {{
            "name": "支付工具名稱",
            "reason": "推薦原因"
          }}
        ]
      }}
    }}
    """

    try:
        api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text="正在為您分析最佳支付方式，請稍候...")])
        )
        
        response = gemini_model.generate_content(prompt)
        
        # 清理 Gemini 回應，確保是純 JSON
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        recommendations = json.loads(cleaned_response_text)
        
        # 儲存交易紀錄
        save_transaction(user_id, category, amount, recommendations)

        # 格式化並傳送回覆訊息
        reply_messages = format_recommendation_messages(recommendations)
        
        # 使用 push_message 才能傳送多則訊息
        api.push_message(line_user_id, messages=reply_messages)

    except Exception as e:
        app.logger.error(f"Gemini API 或後續處理出錯: {e}")
        api.push_message(line_user_id, messages=[TextMessage(text="抱歉，分析時發生錯誤，請稍後再試。")])


def format_recommendation_messages(reco_data):
    """將 Gemini 回傳的 JSON 格式化為 LINE 的 TemplateMessage"""
    messages = []
    
    # 處理現有工具推薦
    existing_reco = reco_data.get('existing_tools_recommendation')
    if existing_reco and existing_reco.get('recommendations'):
        all_payment_options = {opt['name']: opt for opt in get_payment_options('mobile') + get_payment_options('credit_card')}
        
        text = existing_reco.get('title', '現有工具推薦：') + "\n"
        for item in existing_reco['recommendations']:
            name = item.get('name')
            reason = item.get('reason')
            
            # 查找支付工具的詳細資訊
            option_details = all_payment_options.get(name)
            action_label = "開啟 APP" if option_details and option_details.get('type') == 'mobile' else "查看詳情"
            
            # 只有行動支付且有 open_url 才提供按鈕
            if option_details and option_details.get('type') == 'mobile' and option_details.get('open_url'):
                action = URIAction(label=action_label, uri=option_details.get('open_url'))
            else:
                # 信用卡或無連結的行動支付不提供按鈕
                 messages.append(TextMessage(text=f"【{name}】\n{reason}"))
                 continue

            messages.append(TemplateMessage(
                alt_text=f"推薦：{name}",
                template=ButtonsTemplate(
                    title=f"推薦使用：{name}",
                    text=reason,
                    actions=[action]
                )
            ))
    else:
        messages.append(TextMessage(text="您現有的支付工具中，本次消費沒有特別合適的推薦。"))

    # 處理新工具推薦
    new_reco = reco_data.get('new_tools_recommendation')
    if new_reco and new_reco.get('recommendations'):
        all_payment_options = {opt['name']: opt for opt in get_payment_options('mobile') + get_payment_options('credit_card')}
        
        messages.append(TextMessage(text="---")) # 分隔線
        
        for item in new_reco['recommendations']:
            name = item.get('name')
            reason = item.get('reason')
            
            option_details = all_payment_options.get(name)
            
            if option_details and option_details.get('apply_url'):
                action = URIAction(label="前往申辦", uri=option_details.get('apply_url'))
                messages.append(TemplateMessage(
                    alt_text=f"可考慮申辦：{name}",
                    template=ButtonsTemplate(
                        title=f"可考慮申辦：{name}",
                        text=reason,
                        actions=[action]
                    )
                ))
            else:
                messages.append(TextMessage(text=f"【建議申辦：{name}】\n{reason}"))
    
    if not messages:
        return [TextMessage(text="抱歉，目前無法提供有效的建議。")]
        
    return messages


def save_transaction(user_id, category, amount, recommendations):
    """將交易與推薦結果存入資料庫"""
    conn = get_db_connection()
    if not conn: return
    
    with conn.cursor() as cursor:
        sql = """
            INSERT INTO transactions (user_id, category, amount, recommended_options)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, category, amount, json.dumps(recommendations, ensure_ascii=False)))
    conn.commit()
    conn.close()


# --- 主程式進入點 ---
if __name__ == "__main__":
    # 注意：在生產環境中，請使用 Gunicorn 或 uWSGI 等 WSGI 伺服器
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 50000))
    app.run(host='0.0.0.0', port=port)

