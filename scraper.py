# scraper.py
import requests
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

def search_recipes(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": f"{query} 食譜"
    }
    resp = requests.get(url, params=params).json()

    items = resp.get("items", [])[:3]  # 取前 3 個

    return [
        {
            "title": item["title"],
            "url": item["link"],
            "snippet": item.get("snippet", "")
        }
        for item in items
    ]
