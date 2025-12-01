from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
import json
import os
import uvicorn

from scraper import search_recipes
from parser import clean_recipe

app = FastAPI()

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


# 🔥 Railway 必要的啟動入口
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)



