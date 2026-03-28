"""meal_planner.py — City-specific meal recommendations"""

import random

MEAL_SLOTS = {
    "breakfast": {"en": "🌅 Breakfast",    "zh": "🌅 早餐",  "hours": (7,  9),  "frac": 0.12},
    "lunch":     {"en": "☀️ Lunch",        "zh": "☀️ 午餐",  "hours": (12, 14), "frac": 0.20},
    "dinner":    {"en": "🌙 Dinner",       "zh": "🌙 晚餐",  "hours": (18, 20), "frac": 0.28},
    "cafe":      {"en": "☕ Coffee Break",  "zh": "☕ 下午茶", "hours": (14, 16), "frac": 0.08},
    "supper":    {"en": "🌃 Late Snack",   "zh": "🌃 宵夜",  "hours": (21, 23), "frac": 0.10},
}

CITY_CUISINE = {
    "beijing":   {"breakfast":["老北京豆浆油条","护国寺包子","胡同早餐摊"],
                  "lunch":["烤鸭馆","炸酱面馆","涮羊肉火锅"],
                  "dinner":["全聚德烤鸭","四季民福","东来顺"],
                  "cafe":["三里屯精品咖啡","南锣鼓巷茶馆"],
                  "supper":["簋街麻辣小龙虾","夜市烤串"],
                  "specialties":["北京烤鸭","炸酱面","豆汁","驴打滚"]},
    "shanghai":  {"breakfast":["南翔小笼包","阿大葱油饼","沈大成糕点"],
                  "lunch":["小笼包","本帮菜馆","浦东海鲜"],
                  "dinner":["外滩畔餐厅","新天地法餐","上海老饭店"],
                  "cafe":["武康路精品咖啡","外滩咖啡馆"],
                  "supper":["城隍庙小吃","上海串吧"],
                  "specialties":["小笼包","生煎","红烧肉","黄鱼面"]},
    "chengdu":   {"breakfast":["赖汤圆","钟水饺","担担面"],
                  "lunch":["成都串串香","夫妻肺片","麻婆豆腐"],
                  "dinner":["宽窄巷子特色餐厅","锦里老餐馆","四川火锅"],
                  "cafe":["宽窄巷子茶馆","春熙路精品咖啡"],
                  "supper":["九眼桥酒吧","夜市烤串"],
                  "specialties":["麻婆豆腐","担担面","夫妻肺片","串串香"]},
    "tokyo":     {"breakfast":["Tsukiji sushi","Onigiri convenience","Tamago Kake Gohan"],
                  "lunch":["Ramen at Fuunji","Tonkatsu Maisen","Tempura Kondo"],
                  "dinner":["Omakase sushi","Yakitori under the tracks","Shibuya izakaya"],
                  "cafe":["% Arabica","Blue Bottle Shinjuku","Stumptown Harajuku"],
                  "supper":["Ramen Ichiran (midnight)","Shinjuku gyoza"],
                  "specialties":["Ramen","Sushi","Tempura","Tonkatsu","Yakitori"]},
    "kyoto":     {"breakfast":["Nishiki Market","Tofu ryori","Kissaten morning set"],
                  "lunch":["Obanzai set","Yudofu hot tofu","Soba Tagoto"],
                  "dinner":["Kaiseki at Kikunoi","Pontocho riverside"],
                  "cafe":["% Arabica Arashiyama","Sarasa Nishijin"],
                  "supper":["Gion izakaya","Kiyamachi late ramen"],
                  "specialties":["Kaiseki","Yudofu","Matcha sweets","Obanzai"]},
    "osaka":     {"breakfast":["Tamago sando","Kissaten morning set"],
                  "lunch":["Takoyaki Dotonbori","Okonomiyaki Mizuno","Kushikatsu Daruma"],
                  "dinner":["Kani Doraku","Namba standing sushi"],
                  "cafe":["Weekenders Coffee","Lilo Coffee"],
                  "supper":["Dotonbori street food","Shinsekai bars"],
                  "specialties":["Takoyaki","Okonomiyaki","Kushikatsu","Udon"]},
    "seoul":     {"breakfast":["Juk rice porridge","Convenience store kimbap"],
                  "lunch":["Bibimbap at Gogung","Korean BBQ Samgyeopsal"],
                  "dinner":["Korean BBQ Hongdae","Pojangmacha street food"],
                  "cafe":["Café Bora matcha","Fritz Coffee","Anthracite"],
                  "supper":["Jongno pojangmacha","Itaewon 24h chicken"],
                  "specialties":["Korean BBQ","Bibimbap","Tteokbokki","Japchae"]},
    "bangkok":   {"breakfast":["Jok rice porridge","Pa tong go Thai donuts"],
                  "lunch":["Pad Thai Thip Samai","Green curry restaurant"],
                  "dinner":["Yaowarat Chinatown seafood","Rooftop Silom"],
                  "cafe":["Roots Coffee","Ceresia Coffee"],
                  "supper":["Patpong Night Market","24h Silom noodles"],
                  "specialties":["Pad Thai","Tom Yum","Green Curry","Mango sticky rice"]},
    "singapore": {"breakfast":["Kaya toast Ya Kun","Roti prata"],
                  "lunch":["Chicken rice Tian Tian","Laksa at 328","Hawker Centre"],
                  "dinner":["Newton Food Centre","Lau Pa Sat satay"],
                  "cafe":["Carpenter & Cook","Nylon Coffee"],
                  "supper":["Maxwell Food Centre","Geylang durian"],
                  "specialties":["Chicken Rice","Chili Crab","Laksa","Char Kway Teow"]},
    "paris":     {"breakfast":["Croissant at Poilâne","Café au lait tartine"],
                  "lunch":["Brasserie set menu","Crêperie Montmartre"],
                  "dinner":["Bistro steak-frites","Saint-Germain wine bar"],
                  "cafe":["Café de Flore","Les Deux Magots"],
                  "supper":["Pigalle wine bars","Marais cocktails"],
                  "specialties":["Croissant","Onion soup","Steak tartare","Macarons"]},
    "london":    {"breakfast":["Full English caff","Borough Market breakfast"],
                  "lunch":["Fish & chips","Borough Market street food"],
                  "dinner":["Dishoom Indian","Hawksmoor steak"],
                  "cafe":["Monmouth Coffee","Ozone Coffee"],
                  "supper":["Soho cocktail bars","Camden kebab"],
                  "specialties":["Fish & Chips","Chicken Tikka","Afternoon Tea","Sunday Roast"]},
    "new york":  {"breakfast":["Bagel with lox Russ & Daughters","Diner pancakes"],
                  "lunch":["Dollar pizza","Katz's Deli pastrami","Halal cart"],
                  "dinner":["Carbone pasta","Peter Luger steak","Momofuku"],
                  "cafe":["Blue Bottle","Cafe Grumpy","La Colombe"],
                  "supper":["Katz's Deli late","Veselka Ukrainian"],
                  "specialties":["NY Pizza","Bagel","Pastrami sandwich","Cheesecake"]},
    "dubai":     {"breakfast":["Arabian breakfast spread","Hotel buffet"],
                  "lunch":["Al Fanar Emirati cuisine","Shawarma Al Ustad"],
                  "dinner":["Pierchic seafood","At.mosphere Burj Khalifa"],
                  "cafe":["% Arabica DIFC","Tom & Serg"],
                  "supper":["La Mer beach bars","Marina walk"],
                  "specialties":["Shawarma","Al Harees","Machboos","Karak Tea"]},
    "_default":  {"breakfast":["Local café breakfast","Hotel buffet","Street food market"],
                  "lunch":["Local restaurant","Food market","Street food"],
                  "dinner":["Restaurant district","Night market","Waterfront dining"],
                  "cafe":["Local café","Tea house","Rooftop café"],
                  "supper":["Night market","Late-night eateries"],
                  "specialties":["Local specialties","Street food","Regional cuisine"]},
}


def _get_data(city):
    cl = city.strip().lower()
    if cl in CITY_CUISINE:
        return CITY_CUISINE[cl]
    for k in CITY_CUISINE:
        if k != "_default" and k in cl:
            return CITY_CUISINE[k]
    return CITY_CUISINE["_default"]


def get_meal_recommendations(city, meal_type="lunch", count=3, seed=42):
    data = _get_data(city)
    opts = data.get(meal_type, data.get("lunch", ["Local restaurant"]))
    random.seed(seed)
    return random.sample(opts, min(count, len(opts)))


def get_specialties(city):
    return _get_data(city).get("specialties", ["Local specialties"])


def render_meal_panel(city, day_idx, daily_usd, country, lang="EN", seed=42):
    slots = ["breakfast", "lunch", "dinner"]
    if daily_usd >= 60:  slots.append("cafe")
    if daily_usd >= 80:  slots.append("supper")
    cards = ""
    for slot in slots:
        info = MEAL_SLOTS[slot]
        label = info.get("zh" if lang == "ZH" else "en", slot)
        budget = round(daily_usd * info["frac"])
        picks = get_meal_recommendations(city, slot, 2, seed + day_idx)
        items = "".join(f"<div style='margin:2px 0;font-size:.82rem'>• {p}</div>" for p in picks)
        cards += (f"<div style='background:#fff;border-radius:8px;padding:10px;margin:6px 0;"
                  f"border-left:3px solid #c97d35'>"
                  f"<div style='font-weight:600;font-size:.88rem'>{label}</div>"
                  f"<div style='color:#888;font-size:.75rem;margin-bottom:4px'>"
                  f"~{info['hours'][0]}:00 · Budget ≈${budget}</div>{items}</div>")
    specs = "  ·  ".join(get_specialties(city)[:5])
    title = "🍽️ 餐饮推荐" if lang == "ZH" else "🍽️ Meal Suggestions"
    must  = "必尝" if lang == "ZH" else "Must try"
    return (f"<div style='background:#fdf8f0;border-radius:12px;padding:14px;margin:10px 0'>"
            f"<div style='font-weight:700;margin-bottom:8px'>{title} — Day {day_idx+1}</div>"
            f"{cards}"
            f"<div style='margin-top:8px;font-size:.78rem;color:#888'>🌟 {must}: {specs}</div>"
            f"</div>")
