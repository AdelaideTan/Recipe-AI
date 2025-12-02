import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_best_image_url(img_tag):
    """
    從 img 標籤中提取最佳圖片 URL，以應對懶載入和響應式圖片。
    優先順序：srcset (抓取最大解析度) > data-src > src
    """
    if not img_tag:
        return ""
    
    # 1. 優先從 srcset 提取最大尺寸的 URL
    srcset = img_tag.get("srcset")
    if srcset:
        try:
            # srcset 格式為 "url1 w1, url2 w2, ..."，抓取第一個 URL (通常是最大解析度)
            first_url_descriptor = srcset.split(",")[0].strip()
            # 提取 URL 部分 (在空格之前)
            return first_url_descriptor.split(" ")[0]
        except IndexError:
            # 如果解析 srcset 失敗，則嘗試其他屬性
            pass

    # 2. 次要嘗試 data-src (iCook 網站常用)
    data_src = img_tag.get("data-src")
    if data_src:
        return data_src
        
    # 3. 最後嘗試 src (可能是 Base64 透明圖，但作為後備)
    return img_tag.get("src", "")


def fetch_steps(url):
    """
    抓取單道食譜的步驟列表，每個步驟包含：
    {
        "description": "文字",
        "image": "圖片網址或空字串"
    }
    """
    resp = requests.get(url, headers=HEADERS)
    # 這裡檢查是否成功取得內容是個好習慣
    if resp.status_code != 200:
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")

    steps_list = []

    # 每個步驟是 <figure class="recipe-step-instruction">
    step_containers = soup.select("figure.recipe-step-instruction")
    for step in step_containers:
        # 抓文字
        p_tag = step.select_one("figcaption.recipe-step-description > p.recipe-step-description-content")
        text = p_tag.get_text(strip=True) if p_tag else ""

        # 抓圖片 (已修改)
        img_tag = step.select_one("a.recipe-step-cover > img")
        img_url = get_best_image_url(img_tag) # 使用新的 helper 函數

        steps_list.append({
            "description": text,
            "image": img_url
        })

    return steps_list

def search_recipes(query: str, limit=3):
    """
    query: 使用者輸入的食材（可能是 1~多個）
    limit: 回傳幾筆
    """

    # 多食材處理：雞肉 洋蔥 → ["雞肉","洋蔥"]
    ingredients = [q.strip() for q in query.replace(",", " ").split() if q.strip()]

    search_keyword = "+".join(ingredients)
    search_url = f"https://icook.tw/search/{search_keyword}"

    resp = requests.get(search_url, headers=HEADERS)
    # 這裡檢查是否成功取得內容是個好習慣
    if resp.status_code != 200:
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")

    cards = soup.select(".browse-recipe-item")

    results = []

    for card in cards:
        # -----------------------
        # 抓標題
        # -----------------------
        title_tag = card.select_one(".browse-recipe-name")
        title = title_tag.text.strip() if title_tag else ""

        # -----------------------
        # 抓網址
        # -----------------------
        link_tag = card.select_one("a")
        url = (
            "https://icook.tw" + link_tag["href"]
            if link_tag and link_tag.has_attr("href")
            else ""
        )

        # -----------------------
        # 抓食材摘要
        # -----------------------
        summary_tag = card.select_one(".browse-recipe-content-ingredient")
        summary = summary_tag.text.strip() if summary_tag else ""

        # -----------------------
        # 抓照片（封面圖）(已修改)
        # -----------------------
        # 根據 iCook 結構，封面圖的 <img> 標籤同時具有 .browse-recipe-cover-img 類別
        img_tag = card.select_one("img.browse-recipe-cover-img")
        img_url = get_best_image_url(img_tag) # 使用新的 helper 函數

        # -----------------------
        # 食材過濾：確保包含全部使用者輸入的食材
        # -----------------------
        if ingredients:
            if not all(ing in summary for ing in ingredients):
                continue

        # -----------------------
        # 抓 steps（文字 + 圖片）
        # -----------------------
        steps_list = fetch_steps(url)

        results.append({
            "title": title,
            "url": url,
            "image": img_url,
            "ingredients": summary,
            "steps": steps_list
        })

        if len(results) >= limit:
            break

    return results

# 範例使用
if __name__ == '__main__':
    search_results = search_recipes("麻奶鍋", limit=1)
    
    if search_results:
        recipe = search_results[0]
        print(f"--- 查詢結果：{recipe['title']} ---")
        print(f"封面圖 URL (已優化): {recipe['image']}")
        print("步驟詳情：")
        for step in recipe['steps']:
            print(f"  描述: {step['description']}")
            print(f"  圖片 URL: {step['image']}")
        print("--- 查詢結束 ---")
    else:
        print("未找到符合條件的食譜。")
