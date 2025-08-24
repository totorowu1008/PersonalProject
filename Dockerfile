# 使用官方 Python 映像檔作為基礎
FROM python:3.12-slim
# 設定工作目錄
WORKDIR /app
# 將 requirements.txt 複製到工作目錄
COPY requirements.txt .
# 安裝所有依賴
RUN pip install -r requirements.txt
# 將所有檔案複製到工作目錄
COPY . .
# 設定環境變數
ENV PORT 8080
# 執行應用程式
CMD ["python", "main.py"]