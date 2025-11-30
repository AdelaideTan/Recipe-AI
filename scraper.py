import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_steps(url):
    """
    抓取單道食譜的步驟列表，每個步驟包含：
    {
        "description": "文字",
        "image": "圖片網址或空字串"
    }
    """
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    steps_list = []

    # 每個步驟是 <figure class="recipe-step-instruction">
    step_containers = soup.select("figure.recipe-step-instruction")
    for step in step_containers:
        # 抓文字
        p_tag = step.select_one("figcaption.recipe-step-description > p.recipe-step-description-content")
        text = p_tag.get_text(strip=True) if p_tag else ""

        # 抓圖片
        img_tag = step.select_one("a.recipe-step-cover > img")
        img_url = ""
        if img_tag:
            if img_tag.has_attr("data-src"):
                img_url = img_tag["data-src"]
            elif img_tag.has_attr("src"):
                img_url = img_tag["src"]

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
        # 抓照片（封面圖）
        # -----------------------
        img_tag = card.select_one(".browse-recipe-cover-img")
        img_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

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
