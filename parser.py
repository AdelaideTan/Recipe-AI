# parser.py

def clean_recipe(item):
    """
    清理並標準化食譜的所有資訊，這份 JSON 將存入快取並在第二次請求時回傳。
    """
    return {
        "title": item.get("title", ""),
        "original_url": item.get("url", ""),
        "image_url": item.get("image", ""),
        "ingredients_raw": item.get("ingredients", ""),  # 食材摘要
        "steps_raw": [
            {
                "description": step.get("description", ""),
                "image": step.get("image", "")
            } for step in item.get("steps", [])
        ]
        # 注意：如果你在 scraper.py 中有抓取「完整材料清單」而非摘要，
        # 這裡的欄位名稱應該根據 scraper 的輸出調整。
    }


