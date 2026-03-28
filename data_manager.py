"""data_manager.py — Must-see attractions database"""

MUST_SEE = {
    "beijing": [
        {"name":"故宫博物院 Forbidden City",  "type":"🏛️ Attraction","rating":4.9,"district":"东城区","tip":"Book tickets online in advance — they sell out fast"},
        {"name":"长城 Great Wall (Mutianyu)", "type":"🏛️ Attraction","rating":4.9,"district":"怀柔区","tip":"Mutianyu is less crowded than Badaling"},
        {"name":"天坛 Temple of Heaven",      "type":"🏛️ Attraction","rating":4.8,"district":"东城区","tip":"Visit early morning for tai chi atmosphere"},
        {"name":"颐和园 Summer Palace",       "type":"🌿 Park",       "rating":4.8,"district":"海淀区","tip":"Take a boat across Kunming Lake"},
        {"name":"南锣鼓巷 Nanluoguxiang",     "type":"🛍️ Shopping",  "rating":4.4,"district":"东城区","tip":"Best before 10 AM before crowds"},
    ],
    "shanghai": [
        {"name":"外滩 The Bund",              "type":"🏛️ Attraction","rating":4.9,"district":"黄浦区","tip":"Night view is stunning"},
        {"name":"豫园 Yu Garden",             "type":"🌿 Park",       "rating":4.7,"district":"黄浦区","tip":"Go early morning"},
        {"name":"上海博物馆 Shanghai Museum",  "type":"🏛️ Attraction","rating":4.8,"district":"黄浦区","tip":"Free entry; amazing ancient art"},
        {"name":"新天地 Xintiandi",           "type":"🛍️ Shopping",  "rating":4.6,"district":"黄浦区","tip":"Shikumen architecture + chic cafés"},
        {"name":"田子坊 Tianzifang",          "type":"🛍️ Shopping",  "rating":4.5,"district":"徐汇区","tip":"Artisan crafts in French Concession lanes"},
    ],
    "tokyo": [
        {"name":"Senso-ji Temple",   "type":"🏛️ Attraction","rating":4.8,"district":"Asakusa","tip":"Most atmospheric at dawn"},
        {"name":"Shibuya Crossing",  "type":"🏛️ Attraction","rating":4.7,"district":"Shibuya","tip":"Watch from Starbucks above"},
        {"name":"Shinjuku Gyoen",    "type":"🌿 Park",       "rating":4.8,"district":"Shinjuku","tip":"Stunning cherry blossoms in late March"},
        {"name":"teamLab Planets",   "type":"🏛️ Attraction","rating":4.9,"district":"Toyosu", "tip":"Book months ahead"},
        {"name":"Tsukiji Outer Market","type":"🍜 Restaurant","rating":4.7,"district":"Tsukiji","tip":"Best sushi breakfast before 7 AM"},
    ],
    "kyoto": [
        {"name":"Fushimi Inari Shrine",     "type":"🏛️ Attraction","rating":4.9,"district":"Fushimi",    "tip":"Hike beyond first gates for fewer crowds"},
        {"name":"Arashiyama Bamboo Grove",  "type":"🌿 Park",       "rating":4.7,"district":"Arashiyama", "tip":"Visit at 6 AM for a magical experience"},
        {"name":"Kinkaku-ji Golden Pavilion","type":"🏛️ Attraction","rating":4.8,"district":"Kita",       "tip":"Perfect reflection on the pond"},
        {"name":"Nishiki Market",           "type":"🛍️ Shopping",  "rating":4.7,"district":"Nakagyo",    "tip":"Try yuba and pickled vegetables"},
        {"name":"Philosopher's Path",       "type":"🌿 Park",       "rating":4.8,"district":"Sakyo",      "tip":"2 km canal walk lined with cherry trees"},
    ],
    "seoul": [
        {"name":"Gyeongbokgung Palace",    "type":"🏛️ Attraction","rating":4.8,"district":"Jongno",  "tip":"Guard change at 10 AM & 2 PM"},
        {"name":"Bukchon Hanok Village",   "type":"🏛️ Attraction","rating":4.7,"district":"Jongno",  "tip":"Wear hanbok for atmosphere"},
        {"name":"N Seoul Tower",           "type":"🏛️ Attraction","rating":4.6,"district":"Yongsan", "tip":"Cable car up at night for city lights"},
        {"name":"Dongdaemun Design Plaza", "type":"🏛️ Attraction","rating":4.6,"district":"Jung",    "tip":"Zaha Hadid architecture"},
    ],
    "bangkok": [
        {"name":"Wat Pho Temple",        "type":"🏛️ Attraction","rating":4.8,"district":"Rattanakosin","tip":"Reclining Buddha + massage school"},
        {"name":"Grand Palace",          "type":"🏛️ Attraction","rating":4.9,"district":"Rattanakosin","tip":"Dress code enforced"},
        {"name":"Chatuchak Weekend Market","type":"🛍️ Shopping","rating":4.6,"district":"Chatuchak",   "tip":"Saturday & Sunday only"},
    ],
    "singapore": [
        {"name":"Gardens by the Bay",       "type":"🌿 Park",       "rating":4.9,"district":"Marina Bay","tip":"Free Supertree light show 7:45 PM"},
        {"name":"Marina Bay Sands Skypark", "type":"🏛️ Attraction","rating":4.7,"district":"Marina Bay","tip":"Rooftop infinity pool view"},
        {"name":"Maxwell Food Centre",      "type":"🍜 Restaurant",  "rating":4.8,"district":"Tanjong Pagar","tip":"Stall 10 Tian Tian chicken rice"},
    ],
    "paris": [
        {"name":"Eiffel Tower",      "type":"🏛️ Attraction","rating":4.7,"district":"7th arr.","tip":"Book summit tickets online months ahead"},
        {"name":"Louvre Museum",     "type":"🏛️ Attraction","rating":4.8,"district":"1st arr.","tip":"Go Wednesday evening (open till 9:45 PM)"},
        {"name":"Musée d'Orsay",    "type":"🏛️ Attraction","rating":4.9,"district":"7th arr.","tip":"Best Impressionist collection in the world"},
        {"name":"Sacré-Cœur",      "type":"🏛️ Attraction","rating":4.7,"district":"Montmartre","tip":"Free entry; panoramic city view"},
        {"name":"Le Marais",         "type":"🛍️ Shopping",  "rating":4.7,"district":"3rd arr.","tip":"Medieval streets + galleries + falafel"},
    ],
    "london": [
        {"name":"British Museum",   "type":"🏛️ Attraction","rating":4.8,"district":"Bloomsbury","tip":"Free entry; Rosetta Stone"},
        {"name":"Borough Market",   "type":"🍜 Restaurant",  "rating":4.7,"district":"Southwark","tip":"Open Thurs–Sat; arrive hungry"},
        {"name":"Tower of London",  "type":"🏛️ Attraction","rating":4.7,"district":"City",      "tip":"Crown Jewels; book ahead"},
        {"name":"Tate Modern",      "type":"🏛️ Attraction","rating":4.7,"district":"Southwark","tip":"Free entry"},
    ],
    "new york": [
        {"name":"Central Park",               "type":"🌿 Park",       "rating":4.9,"district":"Manhattan","tip":"Rent a bike; Strawberry Fields"},
        {"name":"Metropolitan Museum of Art", "type":"🏛️ Attraction","rating":4.8,"district":"Upper East","tip":"Suggested donation"},
        {"name":"Brooklyn Bridge Walk",       "type":"🏛️ Attraction","rating":4.7,"district":"Brooklyn",  "tip":"Sunrise is magical"},
        {"name":"High Line",                  "type":"🌿 Park",       "rating":4.6,"district":"Chelsea",   "tip":"Elevated park; free entry"},
    ],
    "dubai": [
        {"name":"Burj Khalifa",          "type":"🏛️ Attraction","rating":4.8,"district":"Downtown","tip":"Book sunset slot"},
        {"name":"Gold Souk & Spice Souk","type":"🛍️ Shopping",  "rating":4.7,"district":"Deira",   "tip":"Bargaining expected"},
        {"name":"Dubai Creek Dhow Cruise","type":"🏛️ Attraction","rating":4.6,"district":"Deira",  "tip":"Evening dinner cruise"},
    ],
    "bali": [
        {"name":"Tanah Lot Temple",           "type":"🏛️ Attraction","rating":4.8,"district":"Tabanan",    "tip":"Sunset views; arrive early"},
        {"name":"Ubud Sacred Monkey Forest",  "type":"🌿 Park",       "rating":4.6,"district":"Ubud",       "tip":"Don't bring food"},
        {"name":"Tegallalang Rice Terraces",  "type":"🌿 Park",       "rating":4.7,"district":"Tegallalang","tip":"Best photos from café terraces above"},
        {"name":"Uluwatu Temple",             "type":"🏛️ Attraction","rating":4.8,"district":"Pecatu",     "tip":"Kecak fire dance at sunset"},
    ],
}


def get_must_see(city, limit=5):
    cl = city.strip().lower()
    data = MUST_SEE.get(cl)
    if not data:
        for k in MUST_SEE:
            if k in cl or cl in k:
                data = MUST_SEE[k]
                break
    if not data:
        return []
    return sorted(data, key=lambda x: x.get("rating", 0), reverse=True)[:limit]


def render_must_see_panel(city, lang="EN"):
    items = get_must_see(city, 5)
    if not items:
        return ""
    title   = "⭐ 当地必游景点" if lang == "ZH" else "⭐ Local Must-See Attractions"
    caption = "精选热门目的地" if lang == "ZH" else "Curated highlights for this destination"
    cards = ""
    for item in items:
        tip = item.get("tip","")
        tip_h = f'<div style="font-size:.76rem;color:#888;margin-top:3px">💡 {tip}</div>' if tip else ""
        cards += (f'<div style="background:#fff;border-radius:8px;padding:10px 12px;'
                  f'margin:6px 0;border-left:3px solid #c97d35">'
                  f'<div style="font-weight:600;font-size:.88rem">{item["name"]}</div>'
                  f'<div style="color:#777;font-size:.78rem">'
                  f'{item["type"]}  ·  {item.get("district","")}  ·  ⭐ {item["rating"]}</div>'
                  f'{tip_h}</div>')
    return (f'<div style="background:#fdf8f0;border-radius:14px;padding:14px;margin:12px 0">'
            f'<div style="font-weight:700;font-size:.95rem;margin-bottom:4px">{title}</div>'
            f'<div style="color:#888;font-size:.78rem;margin-bottom:10px">{caption}</div>'
            f'{cards}</div>')
