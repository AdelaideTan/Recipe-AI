# parser.py

def clean_recipe(item):
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "image_url": item.get("image", ""),
        "ingredients_raw": item.get("ingredients", ""),  # 保留原始文字
        "steps_raw": [
            {
                "description": step.get("description", ""),
                "image": step.get("image", "")
            } for step in item.get("steps", [])
        ]
    }


