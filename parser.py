# parser.py
# 這段是為了標準化（Clean and Standardize）從爬蟲 (scraper.py) 抓取到的原始食譜資料
# 它的功能是將各種原始數據整理成一個固定、清晰的 JSON 結構，以便後續的 API 處理和快取儲存。
def clean_recipe(item):
    """
    清理並標準化食譜的所有資訊，這份 JSON 將存入快取並在第二次請求時回傳。
    """
    # 函數接收一個從 scraper.py 傳來的單筆食譜原始資料字典 (item)
    return {
        # 確保所有欄位都存在，如果原始資料沒有該欄位，則賦予空字串 ""
        "title": item.get("title", ""),                     # 食譜名稱
        "original_url": item.get("url", ""),                # 食譜原始網址 (作為快取的唯一 Key)
        "image_url": item.get("image", ""),                 # 食譜封面照片 URL
        "ingredients_raw": item.get("ingredients", ""),     # 食材摘要 (原始爬取的文字，供 LLM 整理)
        "steps_raw": [# 處理步驟清單 (這是包含圖片和文字的詳細步驟)
            {
                "description": step.get("description", ""), # 提取步驟文字描述
                "image": step.get("image", "")              # 提取步驟圖片 URL
            } for step in item.get("steps", [])             # 遍歷原始資料中的 'steps' 列表
        ]
        # 注意：如果在 scraper.py 中有抓取「完整材料清單」而非摘要，
        # 這裡的欄位名稱應該根據 scraper 的輸出調整。
    }


