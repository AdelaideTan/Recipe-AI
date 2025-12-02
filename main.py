from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel #sec time
import json
import os
import uvicorn

from scraper import search_recipes, fetch_full_ingredients, fetch_steps #sec time
from parser import clean_recipe

app = FastAPI()

# 為了 POST 請求，定義一個輸入模型 (FastAPI 最佳實踐)
class URLPayload(BaseModel):
    recipe_url: str

@app.get("/recipes")
def get_recipes(q: str):
    raw_results = search_recipes(q)
    cleaned = [clean_recipe(r) for r in raw_results]

    formatted = json.dumps(
        jsonable_encoder({"recipes": cleaned}),
        ensure_ascii=False,
        indent=4
    )

    return Response(content=formatted, media_type="application/json")


# 2. 處理完整材料清單查詢 (新增路由，用於第二次 LINE 回覆)
@app.post("/ingredients")
def get_full_ingredients(payload: URLPayload):
    # 取得 n8n 傳來的食譜 URL
    url = payload.recipe_url
    
    if not url:
        raise HTTPException(status_code=400, detail="Missing recipe_url in request body")
    
    # 呼叫新的爬蟲函數，抓取完整的材料清單
    full_ingredients_list = fetch_full_ingredients(url)

    # **新增：為了 LLM 整合，我們可以順便抓取步驟**
    # 這是可選的，如果 LLM 需要食譜全貌來做簡介，就抓取。
    recipe_steps = fetch_steps(url) 

    # 這裡的邏輯可以回傳給 n8n，讓 n8n 的 LLM 節點進行整理
    response_data = {
        "status": "success",
        "original_url": url,
        "ingredients": full_ingredients_list, # 完整的材料清單 (e.g., [{"name":"雞肉","quantity":"300g"}, ...])
        "steps": recipe_steps # 完整的步驟清單 (可選)
    }

    formatted = json.dumps(
        jsonable_encoder(response_data),
        ensure_ascii=False,
        indent=4
    )
    
    return Response(content=formatted, media_type="application/json")


# 🔥 Railway 必要的啟動入口
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)



