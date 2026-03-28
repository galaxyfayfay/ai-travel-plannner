cat << 'EOF' > ai_planner.py
import os
import json
import math
import requests

DEEPSEEK_KEY = os.getenv("DEEPSEEKKEY")
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"

def _call_llm(prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a professional travel planner."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
    }

    r = requests.post(DEEPSEEK_API, headers=headers, json=payload, timeout=40)
    r.raise_for_status()
    return r.json()

def generate_itinerary(
    df,
    ndays,
    day_quotas,
    hotel_lat=None,
    hotel_lon=None,
    day_min_ratings=None,
    day_anchor_lats=None,
    day_anchor_lons=None,
):
    """
    ✅ This version is AI-driven.
    """

    places = []
    for _, row in df.iterrows():
        places.append({
            "name": row["name"],
            "lat": row["lat"],
            "lon": row["lon"],
            "type": row["type_label"],
            "rating": row["rating"],
            "district": row.get("district",""),
        })

    prompt = f"""
You are planning a {ndays}-day trip.

Rules:
- Choose places ONLY from the list below
- Each day must stay geographically compact
- Respect daily quotas
- Output STRICT JSON

Daily quotas:
{json.dumps(day_quotas, indent=2)}

Places:
{json.dumps(places[:80], indent=2)}

JSON format example:
{{
  "Day 1": [
    {{
      "name": "...",
      "time_slot": "9:00 AM"
    }}
  ]
}}
"""

    raw = _call_llm(prompt)
    content = raw["choices"][0]["message"]["content"]

    # ✅ 强制解析 JSON
    itinerary = json.loads(content)

    # ✅ 补全坐标 + 评分（从 df 回填）
    idx = {p["name"]: p for p in places}
    for stops in itinerary.values():
        for s in stops:
            full = idx.get(s["name"], {})
            s.update({
                "lat": full.get("lat"),
                "lon": full.get("lon"),
                "rating": full.get("rating", 0),
                "type_label": full.get("type"),
                "district": full.get("district"),
            })

    return itinerary
EOF
