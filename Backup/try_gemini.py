import google.generativeai as genai
import configparser
import os

def get_gemini_api_key(config_file='config.ini'):
    """
    從 config.ini 檔案中讀取 Gemini API Key。
    """
    config = configparser.ConfigParser()
    
    # 檢查 config.ini 檔案是否存在
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"錯誤：找不到 '{config_file}' 檔案。請確認檔案是否存在。")

    config.read(config_file)

    if 'GEMINI' not in config:
        raise ValueError(f"錯誤：'{config_file}' 中缺少 '[GEMINI]' 區段。")

    if 'API_KEY' not in config['GEMINI']:
        raise ValueError(f"錯誤：'{config_file}' 的 '[GEMINI]' 區段中缺少 'API_KEY'。")

    return config['GEMINI']['API_KEY']

def main():
    try:
        # 1. 從 config.ini 讀取 API Key
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)

        # 2. 初始化 Gemini 2.5 Flash 模型
        # 使用 'gemini-2.5-flash' 指定模型
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("Gemini 2.5 Flash 模型已成功初始化。")

        # 3. 進行簡單的文字生成
        prompt = "請用一句話介紹台灣的美食特色。"
        print(f"\n發送提示：'{prompt}'")
        response = model.generate_content(prompt)
        print("模型回應：", response.text)

        print("\n" + "="*30 + "\n")

        # 4. 進行多輪對話 (範例)
        print("開始多輪對話 (輸入 'exit' 結束)：")
        chat = model.start_chat(history=[])

        while True:
            user_input = input("你: ")
            if user_input.lower() == 'exit':
                break
            
            response = chat.send_message(user_input)
            print(f"Gemini: {response.text}")

        print("\n對話結束。")
        print("\n--- 完整對話歷史 ---")
        for message in chat.history:
            print(f"{message.role}: {message.parts[0].text}")


    except FileNotFoundError as e:
        print(e)
        print("請確認您已在專案根目錄下建立 'config.ini' 檔案，並依範例填入內容。")
    except ValueError as e:
        print(e)
        print("請檢查 'config.ini' 檔案的格式是否正確。")
    except Exception as e:
        print(f"串接 Gemini API 時發生錯誤: {e}")

if __name__ == "__main__":
    main()