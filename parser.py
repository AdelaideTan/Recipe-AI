# parser.py

def clean_recipe(item):
    """
    清理並標準化第一次 API 呼叫的結果。
    
    :param item: 來自 scraper.search_recipes 的單筆結果。
    """
    return {
        "title": item.get("title", ""),
        # **關鍵：原食譜網址**，n8n 會將此嵌入按鈕 payload
        "original_url": item.get("url", ""), 
        "image_url": item.get("image", ""),
        "ingredients_summary": item.get("ingredients_summary", "")  # 使用摘要而非原始文字
        # 移除 steps_raw
    }

# 可選：新增一個函數來處理第二次 API 呼叫的回傳
def format_full_ingredients(api_response):
    """
    清理並標準化第二次 API 呼叫 (ingredients) 的結果。
    """
    ingredients_list = api_response.get("ingredients", [])
    
    # 轉換成人類易讀的格式給 LLM 處理
    readable_list = [f"{item['name']} - {item['quantity']}" for item in ingredients_list]
    
    return {
        "recipe_url": api_response.get("original_url"),
        "full_ingredients_text": "\n".join(readable_list),
        "steps_data": api_response.get("steps", [])
    }

