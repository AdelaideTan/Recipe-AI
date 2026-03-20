# main.py
# LINE BOT 專案的核心後端 API，它使用 FastAPI 框架，扮演了食譜爬蟲、資料清洗，
# 以及最重要的——短期記憶體 (快取) 的角色
# 以下主要實現了兩大功能：first time search-食譜搜尋 和 sec time search-食譜詳情查詢 (快取機制)
import os
import time
import json
import uvicorn
from dotenv import load_dotenv

# 1. 優先讀取環境變數
load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

from fastapi import FastAPI, Response, HTTPException    # 引入 FastAPI 核心、回應處理和錯誤處理模組
from fastapi.encoders import jsonable_encoder           # 引入將 Python 物件轉為 JSON 格式的工具
from pydantic import BaseModel                          # 引入 Pydantic 用於定義資料結構 (驗證 POST 輸入)


from scraper import search_recipes, fetch_steps  # 確保 scraper 有匯出 fetch_steps      # 引入爬蟲模組（負責抓取資料）
from parser import clean_recipe                                                       # 引入資料清洗模組（負責標準化結構）

app = FastAPI()

# ----------------------------------------------------
# 【核心快取結構與設定】
# 用於儲存完整的食譜資料，以供第二次請求時直接讀取。
# ----------------------------------------------------
RECIPE_CACHE = {}               # 定義 In-Memory 快取：Python 字典，API 的臨時記憶體
CACHE_TTL_SECONDS = 3600        # 快取有效期設定為 1 小時 (可調整)

# Pydantic 模型用於第二次 POST 請求的輸入
class URLPayload(BaseModel):    
    recipe_url: str             # 定義 POST 請求 Body 必須包含 recipe_url 欄位


# ----------------------------------------------------
# 路由 0: GET /health (方案一：喚醒專用節點)
# ----------------------------------------------------
@app.get("/health")
def health_check():
    """
    用於被外部 cron-job 呼叫，防止 Render 進入休眠。
    """
    return {"status": "ok", "timestamp": time.time(), "cache_count": len(RECIPE_CACHE)}


# ----------------------------------------------------
# 路由 1: GET /recipes (第一次搜尋並快取 - 回傳完整資料)
# ----------------------------------------------------
@app.get("/recipes")            # 處理 GET 請求，用於初次食材搜尋
def get_recipes(q: str):        # q 參數即為使用者輸入的食材
    # 1. 執行爬蟲，獲取完整的原始資料 (三筆食譜的所有細節)
    raw_results = search_recipes(q)
    
    # 準備回傳給 n8n 的清單
    response_list = []
    
    for r in raw_results:
        # 2. 清理並標準化這筆完整的食譜資料 (包含所有 title, url, steps, ingredients...)
        cleaned = clean_recipe(r) 
        
        recipe_url = cleaned.get("original_url")
        if recipe_url:
            # 3. 將【完整的】清理後資料存入快取 (這是記憶體的來源)
            RECIPE_CACHE[recipe_url] = {
                "data": cleaned,
                "timestamp": time.time()
            }
            
            # 4. **【重要修改】**：直接將完整的 cleaned 資料加入回傳清單
            # 讓 n8n 收到所有細節 包括URL，用於製作 Flex Message 按鈕。
            response_list.append(cleaned)
            
    # 返回給 n8n 製作 Flex Message 的資料清單 (包含三個【完整】食譜)
    formatted = json.dumps(
        jsonable_encoder({"recipes": response_list}),
        ensure_ascii=False,
        indent=4
    )

    return Response(content=formatted, media_type="application/json")


# ----------------------------------------------------
# 路由 2: POST /recipe_details (第二次查詢快取 - 使用者點擊按鈕，查詢快取取得單一食譜詳情)
# ----------------------------------------------------
@app.post("/recipe_details")                        # 處理 POST 請求，專門用於查詢快取
def get_full_details(payload: URLPayload):
    """
    接收 n8n 傳來的單一食譜 URL，從快取中回傳該食譜的所有詳細資訊。
    """
    url = payload.recipe_url                        # 從 POST 請求 Body 中提取 URL
    
    # 1. 檢查快取
    cached_item = RECIPE_CACHE.get(url)             # 嘗試使用 URL 從字典中查找數據

    if not cached_item:
        try:
            # 呼叫 scraper 的 fetch_steps 現場抓取
            print(f"快取失效，嘗試現場重爬: {url}")
            steps = fetch_steps(url)
            if not steps:
                raise Exception("無法爬取步驟")
            
            # 建立一個臨時的標準格式
            recovery_data = {
                "title": "食譜詳情(重新載入)",
                "original_url": url,
                "steps_raw": [{"description": s.get("description", ""), "image": s.get("image", "")} for s in steps]
            }
            return Response(content=json.dumps(jsonable_encoder(recovery_data)), media_type="application/json")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"快取已失效且補爬失敗: {str(e)}")

    full_recipe_data = cached_item["data"] 
    formatted = json.dumps(
        jsonable_encoder(full_recipe_data),
        ensure_ascii=False,
        indent=4
    )
    return Response(content=formatted, media_type="application/json")


# 🔥 Render(雲端部署平台) 必要的啟動入口
if __name__ == "__main__":
    # Render 會自動提供 PORT 環境變數
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)     # 使用 Uvicorn 啟動 FastAPI 服務
