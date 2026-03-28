cat << 'EOF' > must_see.py
MUST_SEE = {
    "tokyo": [
        {"name": "Senso-ji", "district": "Asakusa", "rating": 4.8, "heat": 98},
        {"name": "Shibuya Crossing", "district": "Shibuya", "rating": 4.7, "heat": 95},
        {"name": "Meiji Shrine", "district": "Harajuku", "rating": 4.6, "heat": 92},
    ],
    "paris": [
        {"name": "Eiffel Tower", "district": "7th Arr.", "rating": 4.7, "heat": 99},
        {"name": "Louvre Museum", "district": "1st Arr.", "rating": 4.8, "heat": 98},
    ],
}

def get_must_see(city: str, district: str = "", topk: int = 5):
    city = city.lower()
    items = MUST_SEE.get(city, [])
    if district:
        items = [i for i in items if i["district"] == district]
    return sorted(items, key=lambda x: (x["heat"], x["rating"]), reverse=True)[:topk]
EOF
