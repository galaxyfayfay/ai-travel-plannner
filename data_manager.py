"""data_manager.py — Local must-see attractions & curated highlights per city"""

# ── Must-see attractions per city ──────────────────────────────────────────
MUST_SEE: dict[str, list[dict]] = {
    # ── China ───────────────────────────────────────────────────────────────
    "beijing": [
        {"name": "故宫博物院 Forbidden City",     "type": "🏛️ Attraction", "rating": 4.9, "district": "东城区", "tip": "Book in advance online; 故宫官网 tickets sell out fast"},
        {"name": "长城 Great Wall (Mutianyu)",    "type": "🏛️ Attraction", "rating": 4.9, "district": "怀柔区", "tip": "Mutianyu is less crowded than Badaling"},
        {"name": "天坛 Temple of Heaven",         "type": "🏛️ Attraction", "rating": 4.8, "district": "东城区", "tip": "Visit early morning when locals practice tai chi"},
        {"name": "颐和园 Summer Palace",          "type": "🌿 Park",       "rating": 4.8, "district": "海淀区", "tip": "Take a boat across Kunming Lake"},
        {"name": "什刹海 Shichahai Lake",         "type": "🌿 Park",       "rating": 4.6, "district": "西城区", "tip": "Great for hutong cycling"},
        {"name": "南锣鼓巷 Nanluoguxiang",        "type": "🛍️ Shopping",  "rating": 4.4, "district": "东城区", "tip": "Best in the morning before crowds arrive"},
    ],
    "shanghai": [
        {"name": "外滩 The Bund",                 "type": "🏛️ Attraction", "rating": 4.9, "district": "黄浦区", "tip": "Night view from the riverside promenade is stunning"},
        {"name": "豫园 Yu Garden",                "type": "🌿 Park",       "rating": 4.7, "district": "黄浦区", "tip": "Go early; combined ticket with teahouse"},
        {"name": "上海博物馆 Shanghai Museum",    "type": "🏛️ Attraction", "rating": 4.8, "district": "黄浦区", "tip": "Free entry; ancient Chinese art & bronzes"},
        {"name": "新天地 Xintiandi",              "type": "🛍️ Shopping",  "rating": 4.6, "district": "黄浦区", "tip": "Shikumen (stone gate) architecture + chic cafés"},
        {"name": "田子坊 Tianzifang",            "type": "🛍️ Shopping",  "rating": 4.5, "district": "徐汇区", "tip": "Artisan crafts in former French Concession lanes"},
        {"name": "东方明珠 Oriental Pearl Tower", "type": "🏛️ Attraction", "rating": 4.6, "district": "浦东新区","tip": "Book ticket online to skip queues"},
    ],
    "chengdu": [
        {"name": "大熊猫繁育研究基地 Giant Panda Base","type": "🏛️ Attraction","rating": 4.9,"district": "成华区","tip": "Go before 10 AM when pandas are most active"},
        {"name": "宽窄巷子 Kuanzhai Alley",       "type": "🛍️ Shopping",  "rating": 4.6, "district": "青羊区", "tip": "Three parallel alleys with great food stalls"},
        {"name": "锦里 Jinli Ancient Street",     "type": "🏛️ Attraction", "rating": 4.5, "district": "武侯区", "tip": "Historic street with Sichuan snacks"},
        {"name": "青城山 Qingcheng Mountain",     "type": "🌿 Park",       "rating": 4.8, "district": "都江堰市","tip": "Half day hiking; Taoist temples en route"},
        {"name": "三星堆博物馆 Sanxingdui Museum","type": "🏛️ Attraction", "rating": 4.9, "district": "广汉市",  "tip": "World-class Bronze Age mysteries; 40 min from Chengdu"},
    ],
    "hangzhou": [
        {"name": "西湖 West Lake",                "type": "🌿 Park",       "rating": 4.9, "district": "西湖区", "tip": "UNESCO site; hire a boat for lake views"},
        {"name": "灵隐寺 Lingyin Temple",         "type": "🏛️ Attraction", "rating": 4.8, "district": "西湖区", "tip": "Arrive early; combine with Fei Lai Feng grottoes"},
        {"name": "中国丝绸博物馆 China Silk Museum","type": "🏛️ Attraction","rating": 4.7,"district": "西湖区", "tip": "Free entry; largest silk museum in the world"},
        {"name": "河坊街 He Fang Street",         "type": "🛍️ Shopping",  "rating": 4.4, "district": "上城区", "tip": "Traditional pharmacy, dragon beard candy demos"},
        {"name": "南宋御街 Southern Song Street", "type": "🏛️ Attraction", "rating": 4.5, "district": "上城区", "tip": "Archaeological site with 900-year-old road"},
    ],
    "xian": [
        {"name": "兵马俑 Terracotta Warriors",    "type": "🏛️ Attraction", "rating": 5.0, "district": "临潼区", "tip": "Pit 1 is largest; Pit 3 is most intact"},
        {"name": "西安城墙 Ancient City Wall",    "type": "🏛️ Attraction", "rating": 4.8, "district": "碑林区", "tip": "Rent a bike to ride the top (14 km loop)"},
        {"name": "大雁塔 Big Wild Goose Pagoda",  "type": "🏛️ Attraction", "rating": 4.7, "district": "雁塔区", "tip": "Music fountain show at 8 PM is spectacular"},
        {"name": "回民街 Muslim Quarter",         "type": "🍜 Restaurant",  "rating": 4.6, "district": "莲湖区", "tip": "Best for street food: rou jia mo, lamb skewers"},
        {"name": "陕西历史博物馆 Shaanxi History Museum","type": "🏛️ Attraction","rating": 4.9,"district": "雁塔区","tip": "Free but timed tickets; Tang dynasty treasures"},
    ],

    # ── Japan ────────────────────────────────────────────────────────────────
    "tokyo": [
        {"name": "Senso-ji Temple", "type": "🏛️ Attraction", "rating": 4.8, "district": "Asakusa", "tip": "Most atmospheric at dawn before the crowds"},
        {"name": "Shibuya Crossing","type": "🏛️ Attraction", "rating": 4.7, "district": "Shibuya", "tip": "Watch from Starbucks or Mag's Park above"},
        {"name": "Shinjuku Gyoen",  "type": "🌿 Park",       "rating": 4.8, "district": "Shinjuku","tip": "Stunning cherry blossoms in late March"},
        {"name": "teamLab Planets", "type": "🏛️ Attraction", "rating": 4.9, "district": "Toyosu",  "tip": "Book months ahead; genuinely mind-bending"},
        {"name": "Tokyo Skytree",   "type": "🏛️ Attraction", "rating": 4.6, "district": "Sumida",  "tip": "Clear day views to Mt Fuji from the top deck"},
        {"name": "Tsukiji Outer Market","type": "🍜 Restaurant","rating":4.7,"district": "Tsukiji", "tip": "Best sushi breakfast by 7 AM before it sells out"},
    ],
    "kyoto": [
        {"name": "Fushimi Inari Shrine",       "type": "🏛️ Attraction","rating": 4.9,"district":"Fushimi",    "tip": "Hike beyond the first gates for fewer crowds"},
        {"name": "Arashiyama Bamboo Grove",    "type": "🌿 Park",       "rating": 4.7,"district":"Arashiyama", "tip": "Visit at 6 AM for a magical quiet experience"},
        {"name": "Kinkaku-ji Golden Pavilion", "type": "🏛️ Attraction","rating": 4.8,"district":"Kita",       "tip": "Can't go inside but the reflection is perfect"},
        {"name": "Nishiki Market",             "type": "🛍️ Shopping",  "rating": 4.7,"district":"Nakagyo",    "tip": "Try yuba (tofu skin) and pickled vegetables"},
        {"name": "Philosopher's Path",         "type": "🌿 Park",       "rating": 4.8,"district":"Sakyo",      "tip": "2 km canal walk; lined with cherry trees in spring"},
    ],
    "osaka": [
        {"name": "Dotonbori",           "type": "🏛️ Attraction","rating": 4.7,"district": "Namba",    "tip": "Evening neon is best; try Kani Doraku crab"},
        {"name": "Osaka Castle Park",   "type": "🌿 Park",       "rating": 4.6,"district": "Chuo",     "tip": "Castle interior is a modern museum inside"},
        {"name": "Shinsekai",           "type": "🏛️ Attraction","rating": 4.5,"district": "Naniwa",   "tip": "Retro 1950s vibe; kushikatsu is the specialty"},
        {"name": "Kuromon Ichiba Market","type":"🛍️ Shopping",  "rating": 4.7,"district": "Chuo",     "tip": "1 km covered market; fresh seafood & street food"},
    ],

    # ── South Korea ──────────────────────────────────────────────────────────
    "seoul": [
        {"name": "Gyeongbokgung Palace","type": "🏛️ Attraction","rating": 4.8,"district": "Jongno",    "tip": "Changing of the guard ceremony at 10 AM & 2 PM"},
        {"name": "Bukchon Hanok Village","type":"🏛️ Attraction","rating": 4.7,"district": "Jongno",    "tip": "Wear hanbok for free entry to some sites"},
        {"name": "N Seoul Tower",       "type": "🏛️ Attraction","rating": 4.6,"district": "Yongsan",   "tip": "Take the cable car up at night for city lights"},
        {"name": "Dongdaemun Design Plaza","type":"🏛️ Attraction","rating":4.6,"district":"Jung",      "tip": "Zaha Hadid design; free to walk around outside"},
        {"name": "Hongdae Street",      "type": "🍺 Bar/Nightlife","rating":4.5,"district":"Mapo",     "tip": "Street performers on weekends; young vibrant crowd"},
    ],

    # ── Southeast Asia ───────────────────────────────────────────────────────
    "bangkok": [
        {"name": "Wat Pho Temple",       "type": "🏛️ Attraction","rating": 4.8,"district":"Rattanakosin","tip":"Reclining Buddha + temple massage school"},
        {"name": "Grand Palace",         "type": "🏛️ Attraction","rating": 4.9,"district":"Rattanakosin","tip":"Dress code enforced; cover knees & shoulders"},
        {"name": "Chatuchak Weekend Market","type":"🛍️ Shopping","rating": 4.6,"district":"Chatuchak",   "tip":"35 acres of stalls; Saturday & Sunday only"},
        {"name": "Khao San Road",        "type": "🍺 Bar/Nightlife","rating":4.3,"district":"Phra Nakhon","tip":"Backpacker central; lively after sunset"},
        {"name": "Chao Phraya River Cruise","type":"🏛️ Attraction","rating":4.7,"district":"Riverside",  "tip":"Hop-on hop-off tourist boat covers all key temples"},
    ],
    "singapore": [
        {"name": "Gardens by the Bay",   "type": "🌿 Park",       "rating": 4.9,"district":"Marina Bay", "tip":"Free Supertree light show at 7:45 PM & 8:45 PM"},
        {"name": "Marina Bay Sands Skypark","type":"🏛️ Attraction","rating":4.7,"district":"Marina Bay","tip":"Non-hotel guests pay entry fee for rooftop views"},
        {"name": "Chinatown Heritage Centre","type":"🏛️ Attraction","rating":4.6,"district":"Chinatown","tip":"Authentic Singapore-Chinese history"},
        {"name": "Sentosa Island",       "type": "🌿 Park",       "rating": 4.5,"district":"Sentosa",    "tip":"Universal Studios, beaches, cable car"},
        {"name": "Maxwell Food Centre",  "type": "🍜 Restaurant",  "rating": 4.8,"district":"Tanjong Pagar","tip":"Try stall 10 Tian Tian chicken rice"},
    ],
    "bali": [
        {"name": "Tanah Lot Temple",     "type": "🏛️ Attraction","rating": 4.8,"district":"Tabanan",    "tip":"Sunset views are spectacular; arrive an hour early"},
        {"name": "Ubud Sacred Monkey Forest","type":"🌿 Park",    "rating": 4.6,"district":"Ubud",       "tip":"Don't bring food; the monkeys will find it"},
        {"name": "Tegallalang Rice Terraces","type":"🌿 Park",    "rating": 4.7,"district":"Tegallalang","tip":"Best photos from the café terraces above"},
        {"name": "Kuta Beach",           "type": "🌿 Park",       "rating": 4.4,"district":"Kuta",       "tip":"Sunset surfing lessons available all day"},
        {"name": "Uluwatu Temple",       "type": "🏛️ Attraction","rating": 4.8,"district":"Pecatu",     "tip":"Kecak fire dance at sunset is unmissable"},
    ],

    # ── Europe ───────────────────────────────────────────────────────────────
    "paris": [
        {"name": "Eiffel Tower",         "type": "🏛️ Attraction","rating": 4.7,"district":"7th arr.",  "tip":"Book summit tickets online months ahead"},
        {"name": "Louvre Museum",        "type": "🏛️ Attraction","rating": 4.8,"district":"1st arr.",  "tip":"Go Wednesday or Friday evening (open till 9:45 PM)"},
        {"name": "Musée d'Orsay",        "type": "🏛️ Attraction","rating": 4.9,"district":"7th arr.",  "tip":"Best Impressionist collection in the world"},
        {"name": "Sacré-Cœur Basilica",  "type": "🏛️ Attraction","rating": 4.7,"district":"Montmartre","tip":"Free entry; panoramic city view from steps"},
        {"name": "Le Marais district",   "type": "🛍️ Shopping",  "rating": 4.7,"district":"3rd arr.",  "tip":"Medieval streets + galleries + falafel at L'As du Fallafel"},
    ],
    "london": [
        {"name": "British Museum",       "type": "🏛️ Attraction","rating": 4.8,"district":"Bloomsbury","tip":"Free entry; Rosetta Stone & Elgin Marbles"},
        {"name": "Borough Market",       "type": "🍜 Restaurant",  "rating": 4.7,"district":"Southwark","tip":"Open Thurs-Sat; arrive hungry"},
        {"name": "Tower of London",      "type": "🏛️ Attraction","rating": 4.7,"district":"City",      "tip":"Crown Jewels queue; book ahead"},
        {"name": "Tate Modern",          "type": "🏛️ Attraction","rating": 4.7,"district":"Southwark","tip":"Free entry; Switch House extension is great"},
        {"name": "Hyde Park",            "type": "🌿 Park",       "rating": 4.7,"district":"Westminster","tip":"Serpentine Gallery exhibitions often free"},
    ],
    "rome": [
        {"name": "Colosseum",            "type": "🏛️ Attraction","rating": 4.8,"district":"Celio",     "tip":"Book combined ticket online; skip the 2h queue"},
        {"name": "Vatican Museums & Sistine Chapel","type":"🏛️ Attraction","rating":4.9,"district":"Vatican","tip":"Early morning first-entry tours are worth the price"},
        {"name": "Trevi Fountain",       "type": "🏛️ Attraction","rating": 4.6,"district":"Trevi",     "tip":"Visit at 6 AM to have it almost to yourself"},
        {"name": "Borghese Gallery",     "type": "🏛️ Attraction","rating": 4.9,"district":"Pinciano",  "tip":"Strictly timed 2h slots; book months ahead"},
        {"name": "Trastevere neighbourhood","type":"🏛️ Attraction","rating":4.7,"district":"Trastevere","tip":"Evening passeggiata + aperitivo culture at its best"},
    ],
    "barcelona": [
        {"name": "Sagrada Família",      "type": "🏛️ Attraction","rating": 4.9,"district":"Eixample",  "tip":"Gaudí's masterpiece; book sunrise entry for pink light"},
        {"name": "Park Güell",           "type": "🌿 Park",       "rating": 4.7,"district":"Gràcia",    "tip":"Monumental Zone requires timed tickets"},
        {"name": "La Boqueria Market",   "type": "🛍️ Shopping",  "rating": 4.5,"district":"Old City",  "tip":"Go in the morning; tourist-heavy by noon"},
        {"name": "Gothic Quarter",       "type": "🏛️ Attraction","rating": 4.7,"district":"Barri Gòtic","tip":"Get lost in medieval lanes; El Call (Jewish Quarter)"},
        {"name": "Camp Nou",             "type": "🏛️ Attraction","rating": 4.7,"district":"Les Corts", "tip":"Museum tour available on non-match days"},
    ],

    # ── Americas ─────────────────────────────────────────────────────────────
    "new york": [
        {"name": "Central Park",         "type": "🌿 Park",       "rating": 4.9,"district":"Manhattan", "tip":"Rent a bike; Strawberry Fields & the Ramble"},
        {"name": "Metropolitan Museum of Art","type":"🏛️ Attraction","rating":4.8,"district":"Upper East Side","tip":"Pay-what-you-wish for NY state residents"},
        {"name": "Brooklyn Bridge Walk", "type": "🏛️ Attraction","rating": 4.7,"district":"Brooklyn",  "tip":"Walk from Manhattan to Brooklyn; sunrise is magical"},
        {"name": "High Line",            "type": "🌿 Park",       "rating": 4.6,"district":"Chelsea",   "tip":"Elevated park on old railway; free entry"},
        {"name": "Times Square",         "type": "🏛️ Attraction","rating": 4.2,"district":"Midtown",   "tip":"Best at night; TKTS discount Broadway tickets nearby"},
    ],

    # ── Middle East ──────────────────────────────────────────────────────────
    "dubai": [
        {"name": "Burj Khalifa",         "type": "🏛️ Attraction","rating": 4.8,"district":"Downtown",  "tip":"Book At the Top Sunset slot (cheaper & beautiful)"},
        {"name": "Dubai Museum / Al Fahidi","type":"🏛️ Attraction","rating":4.6,"district":"Deira",    "tip":"Best 1h history fix; in the old part of the city"},
        {"name": "Dubai Creek Dhow Cruise","type":"🏛️ Attraction","rating":4.6,"district":"Deira",    "tip":"Evening cruise with dinner; authentic local side"},
        {"name": "Gold Souk + Spice Souk","type":"🛍️ Shopping",  "rating": 4.7,"district":"Deira",    "tip":"Bargaining is expected; start at 40% of asking price"},
        {"name": "Jumeirah Beach",        "type": "🌿 Park",       "rating": 4.7,"district":"Jumeirah", "tip":"Burj Al Arab backdrop; free public beach access"},
    ],

    # ── Oceania ──────────────────────────────────────────────────────────────
    "sydney": [
        {"name": "Sydney Opera House",   "type": "🏛️ Attraction","rating": 4.8,"district":"Circular Quay","tip":"Book a show or guided backstage tour"},
        {"name": "Bondi Beach",          "type": "🌿 Park",       "rating": 4.7,"district":"Bondi",     "tip":"Bondi to Coogee coastal walk (6 km) is stunning"},
        {"name": "Royal Botanic Garden", "type": "🌿 Park",       "rating": 4.7,"district":"CBD",       "tip":"Free; great Opera House views from the garden"},
        {"name": "Taronga Zoo",          "type": "🏛️ Attraction","rating": 4.7,"district":"Mosman",    "tip":"Ferry from Circular Quay; arrive by opening for animals"},
        {"name": "The Rocks",            "type": "🏛️ Attraction","rating": 4.5,"district":"CBD",       "tip":"Saturday market + oldest pubs in Australia"},
    ],
}


def get_must_see(city: str, limit: int = 5) -> list[dict]:
    """Return must-see attractions for a city, sorted by rating."""
    city_lc = city.strip().lower()
    data = MUST_SEE.get(city_lc)
    if not data:
        for key in MUST_SEE:
            if key in city_lc or city_lc in key:
                data = MUST_SEE[key]
                break
    if not data:
        return []
    return sorted(data, key=lambda x: x.get("rating", 0), reverse=True)[:limit]


def render_must_see_panel(city: str, lang: str = "EN") -> str:
    """Return HTML card for must-see attractions."""
    items = get_must_see(city, limit=6)
    if not items:
        return ""

    title = "⭐ 当地必游景点" if lang == "ZH" else "⭐ Local Must-See Attractions"
    caption = "精选热门目的地" if lang == "ZH" else "Curated highlights for this destination"

    cards = ""
    for item in items:
        tip = item.get("tip", "")
        tip_html = (
            f'<div style="font-size:0.76rem;color:#888;margin-top:3px">💡 {tip}</div>'
            if tip else ""
        )
        cards += (
            f'<div style="background:#fff;border-radius:8px;padding:10px 12px;'
            f'margin:6px 0;border-left:3px solid #c97d35">'
            f'<div style="font-weight:600;font-size:0.88rem">'
            f'{item["name"]}</div>'
            f'<div style="color:#777;font-size:0.78rem">'
            f'{item["type"]}  ·  {item.get("district","")}  ·  ⭐ {item["rating"]}</div>'
            f'{tip_html}'
            f'</div>'
        )

    return (
        f'<div style="background:#fdf8f0;border-radius:14px;padding:14px;margin:12px 0">'
        f'<div style="font-weight:700;font-size:0.95rem;margin-bottom:4px">{title}</div>'
        f'<div style="color:#888;font-size:0.78rem;margin-bottom:10px">{caption}</div>'
        f'{cards}'
        f'</div>'
    )
