from fastapi import FastAPI, Response, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel # 用於處理 POST 請求的 JSON body
import json
import os
import uvicorn
import time # 用於快取管理

from scraper import search_recipes # 保持不變，它已經抓取所有細節
from parser import clean_recipe

app = FastAPI()

# ----------------------------------------------------
# 【核心快取結構與設定】
# Key: Recipe URL (作為唯一的識別符)
# Value: {
#   "data": 完整食譜資料JSON,
#   "timestamp": 儲存時間
# }
# ----------------------------------------------------
RECIPE_CACHE = {} 
CACHE_TTL_SECONDS = 3600 # 快取有效期設定為 1 小時

# Pydantic 模型用於第二次 POST 請求的輸入
class URLPayload(BaseModel):
    recipe_url: str

# ----------------------------------------------------
# 路由 1: GET /recipes (第一次搜尋並快取)
# ----------------------------------------------------
@app.get("/recipes")
def get_recipes(q: str):
    # 1. 執行爬蟲，獲取完整的原始資料 (三筆食譜的所有細節)
    raw_results = search_recipes(q)
    
    # 準備回傳給 n8n 製作 Flex Message 封面的精簡清單
    response_list = []
    
    for r in raw_results:
        # 2. 清理並標準化這筆完整的食譜資料
        cleaned = clean_recipe(r) 
        
        recipe_url = cleaned.get("original_url")
        if recipe_url:
            # 3. 將【完整的】清理後資料存入快取
            RECIPE_CACHE[recipe_url] = {
                "data": cleaned,
                "timestamp": time.time()
            }
            
            # 4. 準備【精簡的】資料回傳給 n8n，用於 LINE Flex Message 封面
            response_list.append({
                "title": cleaned.get("title"),
                "original_url": recipe_url, # 關鍵：URL 必須回傳給 n8n 嵌入按鈕
                "image_url": cleaned.get("image_url"),
                # 這裡使用摘要，方便 LLM 整理簡介
                "ingredients_raw": cleaned.get("ingredients_raw"), 
            })
            
    # 返回給 n8n 製作 Flex Message 的資料清單 (包含三個精簡食譜)
    formatted = json.dumps(
        jsonable_encoder({"recipes": response_list}),
        ensure_ascii=False,
        indent=4
    )

    return Response(content=formatted, media_type="application/json")


# ----------------------------------------------------
# 路由 2: POST /recipe_details (第二次查詢快取)
# ----------------------------------------------------
@app.post("/recipe_details")
def get_full_details(payload: URLPayload):
    """
    接收 n8n 傳來的單一食譜 URL，從快取中回傳該食譜的所有詳細資訊。
    """
    url = payload.recipe_url
    
    # 1. 檢查快取中是否有這個 URL 的資料
    cached_item = RECIPE_CACHE.get(url)

    if cached_item:
        # 這裡可以加入過期檢查，若無則忽略
        # if time.time() - cached_item["timestamp"] > CACHE_TTL_SECONDS:
        #     del RECIPE_CACHE[url]
        #     raise HTTPException(status_code=404, detail=f"Recipe details for {url} have expired.")

        # 2. 從快取中直接取出完整的食譜資料
        full_recipe_data = cached_item["data"] 
        
        # 3. 回傳這份包含所有細節 (title, image, ingredients, steps) 的資料給 n8n
        formatted = json.dumps(
            jsonable_encoder(full_recipe_data),
            ensure_ascii=False,
            indent=4
        )
        return Response(content=formatted, media_type="application/json")
        
    # 如果快取中找不到
    raise HTTPException(status_code=404, detail=f"Recipe details for {url} not found in cache.")


# 🔥 Railway 必要的啟動入口
if __name__ == "__main__":
    # ... (保持不變)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)



