# 🍳 AI Recipe 烹飪小助手(n8n)

這是一個結合了 **FastAPI**、**BeautifulSoup4** 與 **n8n** 的智慧食譜搜尋系統。使用者只需在 LINE 輸入食材，系統便會自動從 iCook 爬取食譜、進行資料清洗，並透過 AI 整理出最易讀的烹飪步驟。

## ✨ 核心功能
- **智慧爬蟲**：自動解析 iCook 網頁，支援 `srcset` 懶載入圖片抓取。
- **高效快取 (In-Memory Cache)**：實作 TTL 快取機制，大幅提升第二次查詢（食譜詳情）的反應速度。
- **資料標準化**：將雜亂的網頁 HTML 轉換為乾淨的 JSON 結構。

## 🛠️ 技術棧
- **Language**: Python 3.9+
- **Framework**: FastAPI (Uvicorn)
- **Scraping**: BeautifulSoup4, Requests
- **Integration**: n8n (Workflow Automation)
- **Deployment**: Render (Web Service)

## 📂 專案結構
```bash
.
├── main.py              # FastAPI 主程式 & LINE Webhook 進入點
├── scraper.py           # iCook 食譜爬蟲邏輯
├── parser.py            # AI 格式轉換與文字處理
├── requirements.txt     # 專案依賴清單
└── .env                 # 環境變數
```

## 🚀 快速開始 (地端開發)

### 1. 複製專案與安裝環境
```bash
git clone [https://github.com/AdelaideTan/Recipe-AI.git](https://github.com/AdelaideTan/Recipe-AI.git)
cd Recipe-AI

# 建立並啟動虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝套件
pip install -r requirements.txt
```

### 2. 設定環境變數
在根目錄建立 .env 檔案，並填入以下資訊：
```bash
LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_Token
LINE_CHANNEL_SECRET=你的_LINE_Secret
GEMINI_API_KEY=你的_Gemini_Key
```

## 🌐 部署說明 (Render)
```bash
1. Build Command: pip install -r requirements.txt

2. Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

Environment Variables:
務必在 Render Dashboard 手動新增上述三個 API Keys。
```
## 🔄 n8n 工作流配置 (Workflow Setup)
本專案的核心自動化邏輯由 n8n 驅動。在開始設定前，請先完成以下步驟：

### 1. 匯入工作流檔案 (Import JSON)
本專案的 n8n/ 資料夾中包含三個關鍵的 .json 檔案。請依序在你的 n8n 平台中點擊 「Import from File」 並開啟它們：

flow1_entry for line.json: 負責接收 LINE 訊息並轉發給 FastAPI。

flow2_recipe_search for line.json: 負責處理 FastAPI 回傳的食譜資料並進行 AI 食譜摘要。

flow3_recipe_details for line.json: 負責從 FastAPI 獲取食譜詳情。

### 2. 修改節點設定 (Node Configuration)
匯入後，請務必針對以下節點進行手動調整：

Flow 1 - LINE 回傳 HTTP Request 節點:

請在 Credentials 中填入你的 LINE_CHANNEL_ACCESS_TOKEN。

Flow 2 & 3 - HTTP Request 節點:

將網址修改為你部署在 Render 的實際網址：
https://<你的-Render-專案名稱>.onrender.com/recipes

Flow 1 & 2 - AI Agent / Google Gemini 節點：

API Key: 請換成你自己的 GEMINI_API_KEY（可從 Google AI Studio 取得）。
Model: 免費版可選取 gemini-1.5-flash。

## 📝 API 說明
GET /recipes?q={食材}: 初次搜尋並將完整食譜存入快取。

POST /recipe_details: 根據食譜 URL 從快取提取詳細步驟。

GET /health: 健康檢查與快取狀態監測。

## 📝 備註
本專案僅供技術練習與個人使用，請尊重 iCook 之服務條款。

如有任何問題，歡迎聯絡開發者：Adelaide Tan