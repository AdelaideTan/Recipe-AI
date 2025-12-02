# scraper.py (新增 fetch_full_ingredients 函數)

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# (get_best_image_url 和 fetch_steps 保持不變，略過...)
def get_best_image_url(img_tag):
    # ... (保持不變)
    if not img_tag:
        return ""
    
    # 1. 優先從 srcset 提取最大尺寸的 URL
    srcset = img_tag.get("srcset")
    if srcset:
        try:
            first_url_descriptor = srcset.split(",")[0].strip()
            return first_url_descriptor.split(" ")[0]
        except IndexError:
            pass

    # 2. 次要嘗試 data-src (iCook 網站常用)
    data_src = img_tag.get("data-src")
    if data_src:
        return data_src
        
    # 3. 最後嘗試 src 
    return img_tag.get("src", "")

def fetch_steps(url):
    # ... (保持不變)
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")
    steps_list = []
    step_containers = soup.select("figure.recipe-step-instruction")
    for step in step_containers:
        p_tag = step.select_one("figcaption.recipe-step-description > p.recipe-step-description-content")
        text = p_tag.get_text(strip=True) if p_tag else ""
        img_tag = step.select_one("a.recipe-step-cover > img")
        img_url = get_best_image_url(img_tag)
        steps_list.append({
            "description": text,
            "image": img_url
        })

    return steps_list

# 新增：抓取完整的材料清單
def fetch_full_ingredients(url: str):
    """
    抓取單道食譜的完整材料清單。
    """
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    ingredients_list = []

    # iCook 完整材料清單通常在 .recipe-ingredient-list 下
    # 每個項目是 .recipe-ingredient-item
    ingredient_items = soup.select(".recipe-ingredient-item")

    for item in ingredient_items:
        # 抓取材料名稱
        name_tag = item.select_one(".ingredient-name")
        name = name_tag.get_text(strip=True) if name_tag else ""

        # 抓取份量/數量
        quantity_tag = item.select_one(".ingredient-quantity")
        quantity = quantity_tag.get_text(strip=True) if quantity_tag else ""

        if name:
             ingredients_list.append({
                "name": name,
                "quantity": quantity
             })

    return ingredients_list

# search_recipes 需要調整，不再爬取 steps，只傳回封面所需資訊
def search_recipes(query: str, limit=3):
    """
    query: 使用者輸入的食材（可能是 1~多個）
    limit: 回傳幾筆
    """
    # ... (前半段保持不變)
    ingredients = [q.strip() for q in query.replace(",", " ").split() if q.strip()]
    search_keyword = "+".join(ingredients)
    search_url = f"https://icook.tw/search/{search_keyword}"
    resp = requests.get(search_url, headers=HEADERS)
    if resp.status_code != 200:
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".browse-recipe-item")
    results = []

    for card in cards:
        # ... (抓取 title, url, summary, image 保持不變)
        title_tag = card.select_one(".browse-recipe-name")
        title = title_tag.text.strip() if title_tag else ""
        link_tag = card.select_one("a")
        url = ("https://icook.tw" + link_tag["href"] if link_tag and link_tag.has_attr("href") else "")
        summary_tag = card.select_one(".browse-recipe-content-ingredient")
        summary = summary_tag.text.strip() if summary_tag else ""
        img_tag = card.select_one("img.browse-recipe-cover-img")
        img_url = get_best_image_url(img_tag)

        # -----------------------
        # 食材過濾
        # -----------------------
        if ingredients:
            if not all(ing in summary for ing in ingredients):
                continue

        # -----------------------
        # 這裡**不再爬取 steps**，因為這會增加第一次請求的延遲。
        # 第一次只傳回封面所需資訊。
        # -----------------------
        
        results.append({
            "title": title,
            "url": url,
            "image": img_url,
            "ingredients_summary": summary, # 區分摘要和完整清單
        })

        if len(results) >= limit:
            break

    return results

# -----------------------------------------------------
# (你現有的 search_recipes 裡面爬取 steps 的邏輯可以移除，
# 讓第一次搜尋更快。如果你的 LLM 需要 steps 資訊，可以保留。)
# -----------------------------------------------------