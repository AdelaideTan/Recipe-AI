# parser.py

def clean_recipe(item):
    return {
        "title": item["title"],
        "url": item["url"],
        "summary": item.get("snippet", "")
    }
