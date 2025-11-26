from fastapi import FastAPI
from scraper import search_recipes
from parser import clean_recipe

app = FastAPI()

@app.get("/recipes")
def get_recipes(q: str):
    raw_results = search_recipes(q)  # 搜尋食譜
    cleaned = [clean_recipe(r) for r in raw_results]  # 清洗成乾淨格式
    return {"recipes": cleaned}

