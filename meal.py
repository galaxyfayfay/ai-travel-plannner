"""meal_planner.py — Meal-type recommendations by city/cuisine"""

import random
from typing import Optional

# ── Meal slot definitions ───────────────────────────────────────────────────
MEAL_SLOTS = {
    "breakfast": {"en": "🌅 Breakfast",   "zh": "🌅 早餐",  "hours": (7, 9),   "budget_frac": 0.12},
    "lunch":     {"en": "☀️ Lunch",       "zh": "☀️ 午餐",  "hours": (12, 14), "budget_frac": 0.20},
    "dinner":    {"en": "🌙 Dinner",      "zh": "🌙 晚餐",  "hours": (18, 20), "budget_frac": 0.28},
    "cafe":      {"en": "☕ Coffee Break", "zh": "☕ 下午茶", "hours": (14, 16), "budget_frac": 0.08},
    "supper":    {"en": "🌃 Late Snack",  "zh": "🌃 宵夜",  "hours": (21, 23), "budget_frac": 0.10},
}

# City-specific cuisine data
CITY_CUISINE = {
    # China
    "beijing": {
        "breakfast": ["老北京豆浆油条", "包子铺", "胡同早餐摊", "护国寺小吃"],
        "lunch": ["烤鸭馆 (Peking Duck)", "炸酱面馆", "涮羊肉", "宫廷菜"],
        "dinner": ["全聚德烤鸭", "便宜坊", "四季民福", "东来顺涮肉"],
        "cafe": ["三里屯精品咖啡", "南锣鼓巷茶馆", "798艺术区咖啡"],
        "supper": ["簋街麻辣小龙虾", "夜市烤串", "老北京小吃夜市"],
        "specialties": ["北京烤鸭", "炸酱面", "豆汁", "驴打滚", "爆肚"],
    },
    "shanghai": {
        "breakfast": ["大壶春生煎包", "阿大葱油饼", "沈大成糕点", "永和大王"],
        "lunch": ["小笼包 (Xiao Long Bao)", "本帮菜馆", "浦东新区海鲜", "南翔馒头店"],
        "dinner": ["外滩畔的精致餐厅", "新天地法国餐厅", "上海老饭店", "功德林素菜"],
        "cafe": ["武康路精品咖啡", "外滩咖啡馆", "田子坊下午茶"],
        "supper": ["城隍庙小吃", "长乐路夜宵", "上海串吧"],
        "specialties": ["小笼包", "生煎", "红烧肉", "糖醋排骨", "黄鱼面"],
    },
    "chengdu": {
        "breakfast": ["赖汤圆", "钟水饺", "张老二凉粉", "担担面"],
        "lunch": ["成都串串香", "夫妻肺片", "麻婆豆腐", "口水鸡"],
        "dinner": ["宽窄巷子特色餐厅", "锦里老餐馆", "郫县豆瓣鱼", "四川火锅"],
        "cafe": ["宽窄巷子茶馆", "春熙路精品咖啡", "青羊宫旁茶馆"],
        "supper": ["九眼桥酒吧一条街", "夜市烤串", "冒菜夜宵"],
        "specialties": ["麻婆豆腐", "担担面", "夫妻肺片", "串串香", "钟水饺"],
    },
    "xian": {
        "breakfast": ["胡辣汤+肉夹馍", "羊肉泡馍", "biangbiang面", "凉皮"],
        "lunch": ["回民街小吃", "贾三灌汤包", "同盛祥羊肉泡馍"],
        "dinner": ["永兴坊唐宫宴", "陕西十三朝美食", "城墙根特色餐厅"],
        "cafe": ["钟楼附近咖啡馆", "书院门茶馆"],
        "supper": ["回民街夜市", "大唐不夜城小吃"],
        "specialties": ["肉夹馍", "biangbiang面", "羊肉泡馍", "凉皮", "灌汤包"],
    },
    "hangzhou": {
        "breakfast": ["小笼包", "葱包桧", "油炸臭豆腐"],
        "lunch": ["龙井虾仁", "西湖醋鱼", "东坡肉", "叫化鸡"],
        "dinner": ["南宋御街餐厅", "知味观", "楼外楼"],
        "cafe": ["西湖边茶馆 (龙井茶)", "南宋御街咖啡"],
        "supper": ["武林夜市", "河坊街小吃"],
        "specialties": ["龙井虾仁", "东坡肉", "西湖醋鱼", "叫化鸡", "片儿川面"],
    },

    # Japan
    "tokyo": {
        "breakfast": ["Tsukiji Market sushi", "Tamago Kake Gohan", "Hotel Japanese breakfast", "Onigiri convenience"],
        "lunch": ["Ramen at Fuunji", "Sushi Saito", "Tonkatsu Maisen", "Tempura Kondo"],
        "dinner": ["Omakase sushi bar", "Yakitori under the tracks", "Shibuya izakaya", "Roppongi fine dining"],
        "cafe": ["Blue Bottle Coffee", "Stumptown Harajuku", "Sarasa Hanazono Kyoto-style", "% Arabica"],
        "supper": ["Ramen Ichiran (midnight)", "Shinjuku gyoza", "Ebisu late-night sushi"],
        "specialties": ["Ramen", "Sushi", "Tempura", "Tonkatsu", "Yakitori", "Takoyaki"],
    },
    "osaka": {
        "breakfast": ["Tamago sando convenience store", "Kissaten morning set", "Namba Hotel breakfast"],
        "lunch": ["Takoyaki at Dotonbori", "Okonomiyaki Mizuno", "Kushikatsu Daruma", "Udon Marugame"],
        "dinner": ["Kani Doraku", "Matsuzakagyu wagyu", "Namba standing sushi", "Fune no Minato"],
        "cafe": ["Weekenders Coffee", "Lilo Coffee", "About Life Coffee"],
        "supper": ["Dotonbori street food", "Shinsekai kushikatsu bars", "Tenjinbashi shotengai"],
        "specialties": ["Takoyaki", "Okonomiyaki", "Kushikatsu", "Udon", "Wagyu beef"],
    },
    "kyoto": {
        "breakfast": ["Nishiki Market breakfast", "Tofu ryori (tofu cuisine)", "Kissaten morning set"],
        "lunch": ["Obanzai (Kyoto-style set)", "Yudofu hot tofu", "Soba Tagoto"],
        "dinner": ["Kaiseki at Kikunoi", "Pontocho riverside", "Gion high-class kaiseki"],
        "cafe": ["% Arabica Arashiyama", "Weekenders Coffee", "Sarasa Nishijin", "Nakamura-ro teahouse"],
        "supper": ["Gion izakaya", "Pontocho bar hopping", "Kiyamachi late-night ramen"],
        "specialties": ["Kaiseki", "Yudofu", "Matcha sweets", "Obanzai", "Soba"],
    },

    # Korea
    "seoul": {
        "breakfast": ["Juk (rice porridge) at Bongjukheon", "Convenience store kimbap", "Hotel buffet"],
        "lunch": ["Bibimbap at Gogung", "Samgyeopsal BBQ", "Naengmyeon cold noodles", "Sundubu jjigae"],
        "dinner": ["Korean BBQ Hongdae", "Myeongdong tofu hotpot", "Gangnam beef galbi", "Pojangmacha street food"],
        "cafe": ["Café bora (matcha soft-serve)", "Fritz Coffee", "Anthracite Coffee", "Ediya Bukchon"],
        "supper": ["Jongno pojangmacha", "Hongdae bar street", "Itaewon 24h chicken"],
        "specialties": ["Korean BBQ", "Bibimbap", "Kimchi jjigae", "Tteokbokki", "Japchae"],
    },

    # Southeast Asia
    "bangkok": {
        "breakfast": ["Jok (rice porridge)", "Pa tong go (Thai donuts)", "Boat noodles Chatuchak"],
        "lunch": ["Pad Thai Thip Samai", "Green curry restaurant", "Mango sticky rice", "Som tum papaya salad"],
        "dinner": ["Yaowarat Chinatown seafood", "Rooftop restaurant Silom", "Khaosan Road street food"],
        "cafe": ["Roots Coffee", "Ceresia Coffee", "Graph Café"],
        "supper": ["Patpong Night Market", "Ratchada Night Market", "24h Silom noodles"],
        "specialties": ["Pad Thai", "Tom Yum Goong", "Green Curry", "Som Tum", "Mango sticky rice"],
    },
    "singapore": {
        "breakfast": ["Kaya toast + soft-boiled eggs (Ya Kun)", "Roti prata", "Dim sum"],
        "lunch": ["Chicken rice at Tian Tian", "Laksa at 328", "Chili crab East Coast Park", "Hawker Centre"],
        "dinner": ["Newton Food Centre", "Lau Pa Sat satay", "Chinatown Complex food centre"],
        "cafe": ["Carpenter & Cook", "Nylon Coffee", "Papa Palheta"],
        "supper": ["Maxwell Food Centre", "Geylang durian stalls", "24h prata shops"],
        "specialties": ["Chicken Rice", "Chili Crab", "Laksa", "Char Kway Teow", "Hokkien Mee"],
    },

    # Europe
    "paris": {
        "breakfast": ["Croissant at Poilâne", "Café au lait + tartine", "Pain au chocolat boulangerie"],
        "lunch": ["Brasserie set menu", "Crêperie Montmartre", "Baguette sandwich picnic by Seine"],
        "dinner": ["Bistro steak-frites", "Le Grand Véfour", "Saint-Germain wine bar", "Marais falafel"],
        "cafe": ["Café de Flore", "Les Deux Magots", "Shakespeare & Co coffee"],
        "supper": ["Pigalle wine bars", "Marais cocktail bars", "Oberkampf late bars"],
        "specialties": ["Croissant", "Croque Monsieur", "Onion soup", "Steak tartare", "Macarons"],
    },
    "london": {
        "breakfast": ["Full English at a caff", "Borough Market breakfast", "Avocado toast Shoreditch"],
        "lunch": ["Fish & chips", "Borough Market street food", "Pub lunch"],
        "dinner": ["Dishoom (Indian)", "Ottolenghi", "Hawksmoor steak", "Sketch afternoon tea"],
        "cafe": ["Monmouth Coffee", "Ozone Coffee", "Farm Girl", "Allpress"],
        "supper": ["Soho cocktail bars", "Shoreditch late bars", "Camden late-night kebab"],
        "specialties": ["Fish & Chips", "Chicken Tikka Masala", "Afternoon Tea", "Sunday Roast", "Pie & Mash"],
    },
    "rome": {
        "breakfast": ["Cornetto + cappuccino", "Bar San Calisto", "Suppli food truck"],
        "lunch": ["Pasta carbonara Roscioli", "Cacio e pepe", "Supplì al telefono", "Artichokes alla romana"],
        "dinner": ["Trastevere trattorias", "Campo de' Fiori wine bar", "Prati family restaurant"],
        "cafe": ["Sant'Eustachio il Caffè", "Bar Giolitti gelato", "Antico Caffè Greco"],
        "supper": ["Testaccio bar street", "Trastevere aperitivo"],
        "specialties": ["Carbonara", "Cacio e pepe", "Supplì", "Carciofi", "Gelato", "Tiramisu"],
    },

    # Americas
    "new york": {
        "breakfast": ["Bagel with lox (Russ & Daughters)", "Diner pancakes", "Egg sandwich bodega"],
        "lunch": ["Dollar pizza slice", "Katz's Deli pastrami", "Smorgasburg food market", "Halal cart"],
        "dinner": ["Le Bernardin", "Carbone pasta", "Peter Luger steak", "Momofuku Noodle Bar"],
        "cafe": ["Blue Bottle", "Cafe Grumpy", "Abraço espresso", "La Colombe"],
        "supper": ["Katz's Deli open late", "Veselka Ukrainian", "McSorley's Old Ale House"],
        "specialties": ["NY Pizza", "Bagel", "Pastrami sandwich", "Cheesecake", "Hot dog"],
    },

    # Middle East
    "dubai": {
        "breakfast": ["Kaak Al Askar", "Arabian breakfast spread", "Hotel buffet"],
        "lunch": ["Al Fanar Emirati cuisine", "Shawarma Al Ustad", "Zaroob Lebanese"],
        "dinner": ["Pierchic seafood", "At.mosphere Burj Khalifa", "La Petite Maison"],
        "cafe": ["% Arabica DIFC", "Tom & Serg", "Nightjar Coffee"],
        "supper": ["La Mer beach bars", "Dubai Marina walk", "Jumeirah beach night food"],
        "specialties": ["Shawarma", "Al Harees", "Machboos", "Luqaimat", "Karak Tea"],
    },

    # Default fallback
    "_default": {
        "breakfast": ["Local café breakfast", "Hotel breakfast buffet", "Street food morning market"],
        "lunch": ["Local restaurant lunch set", "Food market", "Street food stalls"],
        "dinner": ["Restaurant district dinner", "Night market", "Waterfront dining"],
        "cafe": ["Local specialty café", "Tea house", "Rooftop café"],
        "supper": ["Night market", "Late-night eateries", "Bar street"],
        "specialties": ["Local specialties", "Street food", "Regional cuisine"],
    },
}


def get_meal_recommendations(
    city: str,
    meal_type: str = "lunch",
    count: int = 3,
    seed: int = 42,
    lang: str = "EN",
) -> list[str]:
    """Return meal recommendations for a city + meal type."""
    city_lc = city.strip().lower()
    # Try exact match, then partial match
    data = CITY_CUISINE.get(city_lc)
    if not data:
        for key in CITY_CUISINE:
            if key != "_default" and key in city_lc:
                data = CITY_CUISINE[key]
                break
    if not data:
        data = CITY_CUISINE["_default"]

    options = data.get(meal_type, data.get("lunch", ["Local restaurant"]))
    random.seed(seed)
    picks = random.sample(options, min(count, len(options)))
    return picks


def get_specialties(city: str) -> list[str]:
    """Return must-try food specialties for a city."""
    city_lc = city.strip().lower()
    data = CITY_CUISINE.get(city_lc)
    if not data:
        for key in CITY_CUISINE:
            if key != "_default" and key in city_lc:
                data = CITY_CUISINE[key]
                break
    if not data:
        return ["Local specialties"]
    return data.get("specialties", ["Local specialties"])


def render_meal_panel(
    city: str,
    day_idx: int,
    daily_usd: int,
    country: str,
    lang: str = "EN",
    seed: int = 42,
) -> str:
    """Render an HTML meal recommendation panel for one day."""
    from i18n import t as _t

    slots_to_show = ["breakfast", "lunch", "dinner"]
    if daily_usd >= 60:
        slots_to_show.append("cafe")
    if daily_usd >= 80:
        slots_to_show.append("supper")

    cards = ""
    for slot in slots_to_show:
        slot_info = MEAL_SLOTS[slot]
        label = slot_info.get("zh" if lang == "ZH" else "en", slot)
        budget_frac = slot_info["budget_frac"]
        slot_budget = round(daily_usd * budget_frac)
        picks = get_meal_recommendations(city, slot, count=2, seed=seed + day_idx, lang=lang)

        items_html = "".join(
            f"<div style='margin:2px 0;font-size:0.82rem'>• {p}</div>"
            for p in picks
        )
        cards += (
            f"<div style='background:#fff;border-radius:8px;padding:10px;margin:6px 0;"
            f"border-left:3px solid #c97d35'>"
            f"<div style='font-weight:600;font-size:0.88rem'>{label}</div>"
            f"<div style='color:#888;font-size:0.75rem;margin-bottom:4px'>"
            f"~{slot_info['hours'][0]}:00 · Budget ≈${slot_budget}</div>"
            f"{items_html}"
            f"</div>"
        )

    specialties = get_specialties(city)
    spec_html = "  ·  ".join(specialties[:5])

    return (
        f"<div style='background:#fdf8f0;border-radius:12px;padding:14px;margin:10px 0'>"
        f"<div style='font-weight:700;margin-bottom:8px'>🍽️ "
        f"{'餐饮推荐' if lang=='ZH' else 'Meal Suggestions'} — Day {day_idx+1}</div>"
        f"{cards}"
        f"<div style='margin-top:8px;font-size:0.78rem;color:#888'>"
        f"🌟 {'必尝' if lang=='ZH' else 'Must try'}: {spec_html}</div>"
        f"</div>"
    )
