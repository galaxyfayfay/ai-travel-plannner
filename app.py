"""
app.py v10 — AI Travel Planner Pro (Enhanced)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① Bilingual UI (EN / ZH) via i18n.py
② Must-see attractions panel (data_manager.py)
③ Multi-modal transport details (transport_planner.py)
④ Meal recommendations by city (meal_planner.py)
⑤ User auth + wishlist + check-in + points + vouchers
⑥ Collaboration link sharing
⑦ Place swap in itinerary
⑧ All v9 features preserved
"""

import streamlit as st
import requests
import math
import random
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(
    page_title="AI Travel Planner Pro",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Module imports (graceful fallbacks) ──────────────────────────────────────
try:
    from ai_planner import generate_itinerary
    AI_OK = True
except Exception as _imp_e:
    AI_OK = False
    _AI_ERR = str(_imp_e)

try:
    from i18n import t as _t
    I18N_OK = True
except Exception:
    I18N_OK = False
    def _t(key, lang="EN", **kwargs):
        return key

try:
    from transport_planner import (
        estimate_travel, estimate_all_modes,
        render_transport_comparison, dwell_time_minutes,
        haversine_km, TRANSPORT_MODES,
    )
    TRANSPORT_OK = True
except Exception:
    TRANSPORT_OK = False

try:
    from meal_planner import render_meal_panel, get_specialties
    MEAL_OK = True
except Exception:
    MEAL_OK = False

try:
    from data_manager import get_must_see, render_must_see_panel
    DATA_MGR_OK = True
except Exception:
    DATA_MGR_OK = False

try:
    from auth_manager import (
        register_user, login_user, get_user_from_session,
        logout_user, get_user, update_user,
        create_collab_link, join_collab,
    )
    AUTH_OK = True
except Exception:
    AUTH_OK = False

try:
    from wishlist_manager import (
        add_to_wishlist, remove_from_wishlist, get_wishlist,
        is_in_wishlist, save_itinerary as save_itin_db,
        render_wishlist_panel, swap_place_in_itinerary,
    )
    WISHLIST_OK = True
except Exception:
    WISHLIST_OK = False

try:
    from points_system import (
        add_points, get_points, redeem_voucher,
        render_points_panel, render_checkin_button,
        checkin, VOUCHER_CATALOG,
    )
    POINTS_OK = True
except Exception:
    POINTS_OK = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
/* ── Base ─── */
html,body,[class*="css"]{font-family:'Segoe UI',sans-serif}
.main .block-container{padding:1.5rem 2rem 3rem}
section[data-testid="stSidebar"]{background:#faf6ef!important}

/* ── Hero ─── */
.hero-box{background:linear-gradient(135deg,#c97d35 0%,#e8a558 50%,#3a8fd4 100%);
  border-radius:18px;padding:32px 28px;margin-bottom:24px;color:#fff}
.hero-box h1{margin:0 0 6px;font-size:2.1rem;font-weight:800}
.hero-box p{margin:0;opacity:.88;font-size:1.05rem}

/* ── Cards ─── */
.card-grid{display:flex;flex-wrap:wrap;gap:14px;margin:12px 0}
.info-card{background:#fff;border-radius:14px;padding:18px;flex:1;
  min-width:160px;box-shadow:0 2px 12px rgba(0,0,0,.07)}
.info-card .ic-icon{font-size:1.8rem;margin-bottom:8px}
.info-card .ic-title{font-weight:700;font-size:.95rem;margin-bottom:4px}
.info-card .ic-desc{color:#888;font-size:.82rem;line-height:1.4}

/* ── Section headings ─── */
.sec-head{font-size:1.1rem;font-weight:700;margin:18px 0 8px;
  padding-bottom:4px;border-bottom:2px solid #e8d5bb}

/* ── Budget pill ─── */
.budget-pill{display:inline-flex;align-items:center;gap:6px;
  background:#fff7ed;border:1px solid #e8a558;border-radius:20px;
  padding:3px 10px;font-size:.82rem;color:#c97d35;font-weight:600}

/* ── Table ─── */
.itin-table{width:100%;border-collapse:collapse;font-size:.84rem;margin-top:10px}
.itin-table th{background:#f5ede0;color:#8b5e2a;font-weight:600;
  padding:8px 10px;border-bottom:2px solid #e8d5bb;text-align:left;white-space:nowrap}
.itin-table td{padding:9px 10px;vertical-align:top;border-bottom:1px solid #f0e8d8}
.itin-table tr:hover td{background:#fffbf4}
.day-hdr td{background:#fdf3e3!important;font-weight:700;color:#8b5e2a;
  border-bottom:2px solid #e8d5bb!important;padding:10px!important}

/* ── Swap button ─── */
.swap-btn{background:none;border:1px dashed #bbb;border-radius:6px;
  padding:2px 7px;font-size:.75rem;color:#888;cursor:pointer}
.swap-btn:hover{background:#fff3e0;color:#c97d35;border-color:#c97d35}

/* ── Budget summary ─── */
.bsum-card{background:#fff;border-radius:12px;padding:14px;text-align:center;
  box-shadow:0 2px 10px rgba(0,0,0,.06)}
.bsum-card .day-lbl{font-size:.75rem;color:#888;margin-bottom:4px}
.bsum-card .day-amt{font-size:1.3rem;font-weight:800;color:#c97d35}
.bsum-card .day-rng{font-size:.72rem;color:#aaa}
.bsum-card .day-bud{font-size:.73rem;margin-top:4px;color:#777}

/* ── Rec cards ─── */
.rec-grid{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0}
.rec-card{background:#fff;border-radius:10px;padding:12px;
  flex:1;min-width:180px;max-width:240px;
  box-shadow:0 1px 8px rgba(0,0,0,.06);position:relative}
.rec-card .rc-name{font-weight:700;font-size:.86rem;margin-bottom:4px}
.rec-card .rc-meta{color:#888;font-size:.76rem}
.rc-badge{position:absolute;top:10px;right:10px;
  background:#fff8ee;border-radius:8px;padding:2px 7px;
  font-size:.78rem;color:#c97d35;font-weight:600}

/* ── Map heading ─── */
.map-head{font-size:1.1rem;font-weight:700;margin:20px 0 6px;
  padding-left:6px;border-left:4px solid #c97d35}

/* ── Auth panel ─── */
.auth-panel{background:#fff;border-radius:14px;padding:16px;
  box-shadow:0 2px 12px rgba(0,0,0,.08)}

/* ── Points card ─── */
.pts-card{border-radius:14px;padding:16px;color:#fff;
  background:linear-gradient(135deg,#c97d35,#e8a558)}

/* ── Wishlist badge ─── */
.wl-badge{display:inline-block;background:#ffe4c4;color:#c97d35;
  border-radius:10px;padding:1px 8px;font-size:.75rem;font-weight:600}

/* ── Must-see panel ─── */
.ms-card{background:#fff;border-radius:8px;padding:10px 12px;
  margin:6px 0;border-left:3px solid #c97d35}
.ms-tip{font-size:.76rem;color:#888;margin-top:3px}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS (carried over from v9 — unchanged)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AMAP_KEY = os.getenv("APIKEY", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEKKEY", "")

BUDGET_LEVELS_USD = [
    (0,   30,  "💚", "Economy",  "#2E7D32", "#e8f5e9"),
    (30,  80,  "💛", "Standard", "#B07020", "#fff8e1"),
    (80,  200, "🧡", "Comfort",  "#C62828", "#fff3e0"),
    (200, 9999,"❤️", "Luxury",   "#6A1B9A", "#f3e5f5"),
]

def budget_level(usd: int):
    for lo, hi, em, lb, bc, bg in BUDGET_LEVELS_USD:
        if usd < hi:
            return em, lb, bc, bg
    return "❤️", "Luxury", "#6A1B9A", "#f3e5f5"

CURRENCIES = {
    "CN": [("USD","$",1.0),("CNY","¥",7.25)],
    "JP": [("USD","$",1.0),("JPY","¥",155)],
    "KR": [("USD","$",1.0),("KRW","₩",1350)],
    "TH": [("USD","$",1.0),("THB","฿",36)],
    "SG": [("USD","$",1.0),("SGD","S$",1.35)],
    "FR": [("USD","$",1.0),("EUR","€",0.92)],
    "GB": [("USD","$",1.0),("GBP","£",0.79)],
    "IT": [("USD","$",1.0),("EUR","€",0.92)],
    "ES": [("USD","$",1.0),("EUR","€",0.92)],
    "US": [("USD","$",1.0)],
    "AU": [("USD","$",1.0),("AUD","A$",1.53)],
    "AE": [("USD","$",1.0),("AED","AED",3.67)],
    "NL": [("USD","$",1.0),("EUR","€",0.92)],
    "TR": [("USD","$",1.0),("TRY","₺",32)],
    "HK": [("USD","$",1.0),("HKD","HK$",7.82)],
    "TW": [("USD","$",1.0),("TWD","NT$",32)],
    "ID": [("USD","$",1.0),("IDR","Rp",16000)],
    "VN": [("USD","$",1.0),("VND","₫",25000)],
    "MY": [("USD","$",1.0),("MYR","RM",4.7)],
    "INT":[("USD","$",1.0)],
}

def _local_rate(country):
    pairs = CURRENCIES.get(country, [("USD","$",1.0)])
    if len(pairs) > 1:
        return pairs[1][1], pairs[1][2]
    return pairs[0][1], pairs[0][2]

def fmt_currency_row(usd, country):
    pairs = CURRENCIES.get(country, [("USD","$",1.0)])
    parts = [f"${usd}/day"]
    for code, sym, rate in pairs[1:]:
        amt = round(usd * rate)
        parts.append(f"{sym}{amt:,} {code}/day" if amt >= 10000 else f"{sym}{amt} {code}/day")
    return " ≈ ".join(parts)

COST_W = {
    "🏛️ Attraction": 0.18, "🍜 Restaurant": 0.25, "☕ Café": 0.10,
    "🌿 Park": 0.04, "🛍️ Shopping": 0.22, "🍺 Bar/Nightlife": 0.16,
    "🏨 Hotel": 0.00, "Transport": 0.12,
}
COST_FLOOR_USD = {
    "🏛️ Attraction": 4, "🍜 Restaurant": 6, "☕ Café": 3,
    "🌿 Park": 0, "🛍️ Shopping": 8, "🍺 Bar/Nightlife": 5,
    "🏨 Hotel": 0, "Transport": 1,
}

def cost_estimate(type_label, daily_usd, country):
    w = COST_W.get(type_label, 0.12)
    floor = COST_FLOOR_USD.get(type_label, 2)
    per_visit_usd = max(floor, daily_usd * w / 2)
    lo_usd = per_visit_usd * 0.65
    hi_usd = per_visit_usd * 1.45
    mid_usd = (lo_usd + hi_usd) / 2
    sym, rate = _local_rate(country)
    lo_l = round(lo_usd * rate); hi_l = round(hi_usd * rate)
    lo_u = round(lo_usd);        hi_u = round(hi_usd)
    if country == "US":
        return mid_usd, f"${lo_u}–${hi_u}"
    return mid_usd, f"${lo_u}–${hi_u} ({sym}{lo_l}–{sym}{hi_l})"

def transport_cost_estimate(dist_km, daily_usd, country):
    w = COST_W["Transport"]
    floor = COST_FLOOR_USD["Transport"]
    base = max(floor, daily_usd * w / 5)
    factor = max(1.0, dist_km / 3.0)
    lo_usd = base * factor * 0.7
    hi_usd = base * factor * 1.4
    mid_usd = (lo_usd + hi_usd) / 2
    sym, rate = _local_rate(country)
    lo_l = round(lo_usd * rate); hi_l = round(hi_usd * rate)
    lo_u = round(lo_usd);        hi_u = round(hi_usd)
    if country == "US":
        return mid_usd, f"${lo_u}–${hi_u}"
    return mid_usd, f"${lo_u}–${hi_u} ({sym}{lo_l}–{sym}{hi_l})"

# ── City databases (same as v9) ─────────────────────────────────────────────
CN_CITIES = {
    "beijing":(39.9042,116.4074),"shanghai":(31.2304,121.4737),
    "guangzhou":(23.1291,113.2644),"shenzhen":(22.5431,114.0579),
    "chengdu":(30.5728,104.0668),"hangzhou":(30.2741,120.1551),
    "xian":(34.3416,108.9398),"xi'an":(34.3416,108.9398),
    "chongqing":(29.5630,106.5516),"nanjing":(32.0603,118.7969),
    "wuhan":(30.5928,114.3055),"suzhou":(31.2990,120.5853),
    "tianjin":(39.3434,117.3616),"qingdao":(36.0671,120.3826),
    "xiamen":(24.4798,118.0894),"zhengzhou":(34.7466,113.6254),
    "changsha":(28.2278,112.9388),"kunming":(25.0453,102.7097),
    "sanya":(18.2526,109.5119),
}

INTL_CITIES = {
    "tokyo":(35.6762,139.6503,"JP",["Shinjuku","Shibuya","Asakusa","Harajuku","Ginza","Akihabara","Ueno","Roppongi"]),
    "osaka":(34.6937,135.5023,"JP",["Dotonbori","Namba","Umeda","Shinsekai","Tenoji","Shinsaibashi"]),
    "kyoto":(35.0116,135.7681,"JP",["Gion","Arashiyama","Higashiyama","Fushimi","Nishiki"]),
    "seoul":(37.5665,126.9780,"KR",["Gangnam","Hongdae","Myeongdong","Itaewon","Insadong","Bukchon"]),
    "bangkok":(13.7563,100.5018,"TH",["Sukhumvit","Silom","Rattanakosin","Chatuchak","Ari"]),
    "singapore":(1.3521,103.8198,"SG",["Marina Bay","Clarke Quay","Orchard","Chinatown","Little India","Bugis"]),
    "paris":(48.8566,2.3522,"FR",["Le Marais","Montmartre","Saint-Germain","Champs-Élysées","Bastille"]),
    "london":(51.5072,-0.1276,"GB",["Soho","Covent Garden","Shoreditch","South Bank","Notting Hill","Camden"]),
    "rome":(41.9028,12.4964,"IT",["Trastevere","Campo de' Fiori","Prati","Testaccio","Vatican"]),
    "barcelona":(41.3851,2.1734,"ES",["Gothic Quarter","Eixample","Gracia","El Born","Barceloneta"]),
    "new york":(40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Greenwich Village","Midtown","Williamsburg"]),
    "new york city":(40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Greenwich Village","Midtown"]),
    "sydney":(-33.8688,151.2093,"AU",["Circular Quay","Surry Hills","Newtown","Bondi","Glebe"]),
    "dubai":(25.2048,55.2708,"AE",["Downtown","Dubai Marina","Deira","JBR","DIFC"]),
    "amsterdam":(52.3676,4.9041,"NL",["Jordaan","De Pijp","Centrum","Oud-West","Oost"]),
    "istanbul":(41.0082,28.9784,"TR",["Beyoglu","Sultanahmet","Besiktas","Kadikoy","Uskudar"]),
    "hong kong":(22.3193,114.1694,"HK",["Central","Tsim Sha Tsui","Mong Kok","Causeway Bay","Wan Chai"]),
    "taipei":(25.0330,121.5654,"TW",["Daan","Xinyi","Zhongzheng","Shilin","Ximending"]),
    "bali":(-8.3405,115.0920,"ID",["Seminyak","Ubud","Canggu","Kuta","Sanur","Uluwatu"]),
    "ho chi minh city":(10.7769,106.7009,"VN",["District 1","District 3","Bui Vien","Ben Thanh"]),
    "kuala lumpur":(3.1390,101.6869,"MY",["KLCC","Bukit Bintang","Bangsar","Chow Kit"]),
}

PTYPES = {
    "🏛️ Attraction":{"cn":"景点","osm":("tourism","attraction"),"amap":"110000","emoji":"🏛️","color":"#3a8fd4"},
    "🍜 Restaurant": {"cn":"餐厅","osm":("amenity","restaurant"),  "amap":"050000","emoji":"🍜","color":"#c97d35"},
    "☕ Café":       {"cn":"咖啡馆","osm":("amenity","cafe"),       "amap":"050500","emoji":"☕","color":"#7a5c3a"},
    "🌿 Park":       {"cn":"公园","osm":("leisure","park"),         "amap":"110101","emoji":"🌿","color":"#3aaa7a"},
    "🛍️ Shopping":  {"cn":"购物","osm":("shop","mall"),            "amap":"060000","emoji":"🛍️","color":"#9b59b6"},
    "🍺 Bar/Nightlife":{"cn":"酒吧","osm":("amenity","bar"),       "amap":"050600","emoji":"🍺","color":"#e05c3a"},
    "🏨 Hotel":      {"cn":"酒店","osm":("tourism","hotel"),        "amap":"100000","emoji":"🏨","color":"#1abc9c"},
}

AMAP_ALT = {
    "🏛️ Attraction":["旅游景点","博物馆","历史","游览"],
    "🍜 Restaurant": ["餐馆","美食","饭店","特色菜"],
    "☕ Café":        ["咖啡","下午茶","cafe"],
    "🌿 Park":        ["公园","花园","绿地","广场"],
    "🛍️ Shopping":   ["商场","购物中心","超市","市集"],
    "🍺 Bar/Nightlife":["酒吧","KTV","夜店","清吧"],
    "🏨 Hotel":       ["酒店","宾馆","民宿","客栈"],
}

DAY_COLORS = ["#c97d35","#3a8fd4","#3aaa7a","#9b59b6","#e05c3a","#1abc9c","#e91e63","#f39c12"]
TDESC = {
    "景点":"Worth a visit","attraction":"Worth a visit",
    "餐厅":"Good place to eat","restaurant":"Good place to eat",
    "咖啡":"Great for a coffee break","cafe":"Great for a coffee break","咖啡馆":"Great for a coffee break",
    "公园":"Relax outdoors","park":"Relax outdoors",
    "购物":"Shopping stop","mall":"Shopping stop",
    "酒吧":"Evening out","bar":"Evening out",
    "酒店":"Place to stay","hotel":"Place to stay",
}

def tdesc(t):
    for k, v in TDESC.items():
        if k in str(t).lower():
            return v
    return "Local favourite"

CHAIN_BL = [
    "肯德基","麦当劳","星巴克","costa","711","全家","罗森",
    "kfc","mcdonald","starbucks","seven-eleven","family mart",
]

def is_chain(name):
    nl = name.lower()
    return any(kw in nl for kw in CHAIN_BL)

def _hav_m(lat1, lon1, lat2, lon2):
    R = 6371000
    dl = math.radians(lat2-lat1); dg = math.radians(lon2-lon1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dg/2)**2
    return R * 2 * math.asin(math.sqrt(min(1.0, a)))

def _name_sim(a, b):
    a, b = a.strip().lower(), b.strip().lower()
    if a == b: return True
    shorter, longer = (a,b) if len(a)<=len(b) else (b,a)
    return len(shorter) >= 3 and shorter in longer

def geo_dedup(places, radius_m=120.0):
    if not places: return []
    merged = [False]*len(places); kept = []
    for i, p in enumerate(places):
        if merged[i]: continue
        best = p
        for j in range(i+1, len(places)):
            if merged[j]: continue
            dist = _hav_m(best["lat"],best["lon"],places[j]["lat"],places[j]["lon"])
            if dist < 50 or (dist < radius_m and _name_sim(best["name"],places[j]["name"])):
                merged[j] = True
                if places[j]["rating"] > best["rating"]: best = places[j]
        kept.append(best)
    return kept

# ── World cities (same as v9) ───────────────────────────────────────────────
WORLD_CITIES = {
    "China":["Beijing","Shanghai","Guangzhou","Shenzhen","Chengdu","Hangzhou",
             "Xi'an","Chongqing","Nanjing","Wuhan","Suzhou","Tianjin",
             "Qingdao","Xiamen","Kunming","Sanya","Changsha","Zhengzhou"],
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya",
             "Hiroshima","Nara","Yokohama","Kobe","Okinawa","Hakone"],
    "South Korea":["Seoul","Busan","Incheon","Jeju","Daegu","Gwangju","Daejeon"],
    "Thailand":["Bangkok","Chiang Mai","Phuket","Pattaya","Hua Hin","Koh Samui"],
    "Vietnam":["Ho Chi Minh City","Hanoi","Da Nang","Hoi An","Nha Trang","Hue"],
    "Indonesia":["Bali","Jakarta","Yogyakarta","Lombok","Labuan Bajo","Medan"],
    "Malaysia":["Kuala Lumpur","Penang","Malacca","Kota Kinabalu","Langkawi","Johor Bahru"],
    "Singapore":["Singapore"],
    "Philippines":["Manila","Cebu","Boracay","Palawan","Davao","Bohol"],
    "India":["Mumbai","Delhi","Bangalore","Jaipur","Goa","Agra","Chennai","Kolkata","Varanasi"],
    "Nepal":["Kathmandu","Pokhara","Chitwan","Lumbini"],
    "UAE":["Dubai","Abu Dhabi","Sharjah","Ajman"],
    "Turkey":["Istanbul","Ankara","Cappadocia","Antalya","Bodrum","Izmir","Pamukkale"],
    "Israel":["Jerusalem","Tel Aviv","Haifa","Eilat"],
    "Jordan":["Amman","Petra","Wadi Rum","Aqaba"],
    "France":["Paris","Lyon","Marseille","Nice","Bordeaux","Toulouse","Strasbourg"],
    "Italy":["Rome","Milan","Florence","Venice","Naples","Bologna","Turin","Amalfi","Cinque Terre"],
    "Spain":["Barcelona","Madrid","Seville","Valencia","Granada","Bilbao","San Sebastian","Toledo"],
    "United Kingdom":["London","Edinburgh","Manchester","Birmingham","Bath","Cambridge","Oxford","York"],
    "Germany":["Berlin","Munich","Hamburg","Frankfurt","Cologne","Dresden","Heidelberg"],
    "Netherlands":["Amsterdam","Rotterdam","Utrecht","The Hague"],
    "Switzerland":["Zurich","Geneva","Bern","Lucerne","Interlaken","Zermatt"],
    "Austria":["Vienna","Salzburg","Innsbruck","Hallstatt","Graz"],
    "Greece":["Athens","Santorini","Mykonos","Crete","Rhodes","Thessaloniki","Corfu"],
    "Portugal":["Lisbon","Porto","Algarve","Sintra","Evora","Madeira"],
    "Czech Republic":["Prague","Brno","Cesky Krumlov","Karlovy Vary"],
    "Hungary":["Budapest","Eger","Pecs"],
    "Poland":["Warsaw","Krakow","Wroclaw","Gdansk","Poznan"],
    "Croatia":["Dubrovnik","Split","Zagreb","Hvar","Zadar"],
    "Norway":["Oslo","Bergen","Tromsø","Flam","Lofoten Islands"],
    "Sweden":["Stockholm","Gothenburg","Malmo","Uppsala","Kiruna"],
    "Denmark":["Copenhagen","Aarhus","Odense"],
    "Finland":["Helsinki","Rovaniemi","Turku","Tampere"],
    "Iceland":["Reykjavik","Akureyri","Vik","Selfoss"],
    "Russia":["Moscow","St. Petersburg","Vladivostok","Kazan","Sochi"],
    "USA":["New York","Los Angeles","Chicago","San Francisco","Miami","Boston",
           "Seattle","Las Vegas","New Orleans","Washington DC","Hawaii","Nashville"],
    "Canada":["Toronto","Vancouver","Montreal","Quebec City","Banff","Calgary"],
    "Mexico":["Mexico City","Cancun","Playa del Carmen","Oaxaca","Guadalajara"],
    "Brazil":["Rio de Janeiro","São Paulo","Salvador","Florianopolis","Iguazu Falls"],
    "Argentina":["Buenos Aires","Patagonia","Mendoza","Salta","Bariloche"],
    "Peru":["Lima","Cusco","Machu Picchu","Arequipa","Lake Titicaca"],
    "Colombia":["Bogota","Cartagena","Medellin","Santa Marta"],
    "Australia":["Sydney","Melbourne","Brisbane","Perth","Adelaide","Cairns","Gold Coast"],
    "New Zealand":["Auckland","Queenstown","Wellington","Christchurch","Rotorua"],
    "Morocco":["Marrakech","Fes","Casablanca","Chefchaouen","Essaouira","Rabat"],
    "Egypt":["Cairo","Luxor","Aswan","Alexandria","Hurghada","Sharm el-Sheikh"],
    "South Africa":["Cape Town","Johannesburg","Durban","Kruger","Garden Route"],
    "Kenya":["Nairobi","Mombasa","Masai Mara","Amboseli"],
    "Hong Kong":["Hong Kong"],
    "Taiwan":["Taipei","Tainan","Kaohsiung","Taichung","Hualien","Kenting"],
}

COUNTRY_CODES = {
    "China":"CN","Japan":"JP","South Korea":"KR","Thailand":"TH","Vietnam":"VN",
    "Indonesia":"ID","Malaysia":"MY","Singapore":"SG","Philippines":"PH","India":"IN",
    "UAE":"AE","Turkey":"TR","France":"FR","Italy":"IT","Spain":"ES",
    "United Kingdom":"GB","Germany":"DE","Netherlands":"NL","Switzerland":"CH",
    "Austria":"AT","Greece":"GR","Portugal":"PT","Czech Republic":"CZ",
    "Hungary":"HU","Poland":"PL","Croatia":"HR","Norway":"NO","Sweden":"SE",
    "Denmark":"DK","Finland":"FI","Iceland":"IS","Russia":"RU",
    "USA":"US","Canada":"CA","Mexico":"MX","Brazil":"BR","Argentina":"AR",
    "Peru":"PE","Colombia":"CO","Australia":"AU","New Zealand":"NZ",
    "Morocco":"MA","Egypt":"EG","South Africa":"ZA","Kenya":"KE",
    "Hong Kong":"HK","Taiwan":"TW","Nepal":"NP","Israel":"IL","Jordan":"JO",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AMAP DISTRICT LOADING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600, show_spinner=False)
def amap_get_districts(city_name):
    if not city_name.strip(): return []
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/config/district",
            params={"key":AMAP_KEY,"keywords":city_name,"subdistrict":1,
                    "extensions":"base","output":"json"},
            timeout=9,
        )
        data = r.json()
        if str(data.get("status")) != "1": return []
        tops = data.get("districts",[])
        if not tops: return []
        result = []
        for d in tops[0].get("districts",[]):
            name = (d.get("name") or "").strip()
            adcode = (d.get("adcode") or "").strip()
            center = (d.get("center") or "").strip()
            if not (name and adcode): continue
            lat = lon = None
            if "," in center:
                try: lon, lat = map(float, center.split(","))
                except Exception: pass
            result.append({"name":name,"adcode":adcode,"lat":lat,"lon":lon})
        return result
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def amap_geocode(address):
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"key":AMAP_KEY,"address":address,"output":"json"},
            timeout=8,
        )
        data = r.json()
        if str(data.get("status")) == "1" and data.get("geocodes"):
            loc = data["geocodes"][0].get("location","")
            if "," in loc:
                lon, lat = map(float, loc.split(","))
                return lat, lon
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def nominatim(q):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q":q,"format":"json","limit":1},
            headers={"User-Agent":"TravelPlannerPro/10"},
            timeout=9,
        ).json()
        if r: return float(r[0]["lat"]), float(r[0]["lon"])
    except Exception:
        pass
    return None

def geocode(addr, city, is_cn):
    if not addr.strip(): return None
    if is_cn:
        return amap_geocode(f"{addr} {city}") or nominatim(f"{addr} {city}")
    return nominatim(f"{addr} {city}") or nominatim(addr)

@st.cache_data(ttl=3600, show_spinner=False)
def get_nominatim_districts(city_name):
    if not city_name.strip(): return []
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q":city_name,"format":"json","limit":1},
            headers={"User-Agent":"TravelPlannerPro/10"},
            timeout=8,
        ).json()
        if not r: return []
        lat, lon = float(r[0]["lat"]), float(r[0]["lon"])
        q = (f'[out:json][timeout:20];'
             f'(relation["place"~"suburb|neighbourhood|quarter|borough|district"]'
             f'(around:20000,{lat},{lon});'
             f'node["place"~"suburb|neighbourhood|quarter|borough"]'
             f'(around:20000,{lat},{lon}););out tags 30;')
        els = []
        for ov_url in ["https://overpass-api.de/api/interpreter",
                       "https://overpass.kumi.systems/api/interpreter"]:
            try:
                els = requests.post(ov_url, data={"data":q}, timeout=18).json().get("elements",[])
                if els: break
            except Exception:
                continue
        names = []
        for el in els:
            n = (el.get("tags",{}).get("name:en") or el.get("tags",{}).get("name",""))
            if n and n not in names and len(n) > 1:
                names.append(n)
        return sorted(names[:25])
    except Exception:
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AMAP PLACE SEARCH (three-strategy, same as v9)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _parse_amap_pois(pois, cn_kw, type_label, limit, seen):
    results = []
    for p in pois:
        if len(results) + len(seen) >= limit: break
        name = p.get("name","")
        if not name or is_chain(name): continue
        loc = p.get("location","")
        if "," not in (loc or ""): continue
        try: plon, plat = map(float, loc.split(","))
        except Exception: continue
        key = (name, round(plat,4), round(plon,4))
        if key in seen: continue
        seen.add(key)
        biz = p.get("biz_ext") or {}
        try: rating = float(biz.get("rating") or 0) or 0.0
        except Exception: rating = 0.0
        tel = biz.get("tel") or p.get("tel") or ""
        if isinstance(tel, list): tel = "; ".join(t for t in tel if t)
        addr = p.get("address") or ""
        if isinstance(addr, list): addr = "".join(addr)
        results.append({
            "name":name,"lat":plat,"lon":plon,"rating":rating,
            "address":str(addr).strip(),"phone":str(tel).strip(),"website":"",
            "type":cn_kw,"type_label":type_label,
            "district":p.get("adname") or "","description":tdesc(cn_kw),
        })
    return results

def _amap_by_adcode(adcode, cn_kw, type_label, limit):
    places=[]; seen=set()
    amap_type = PTYPES.get(type_label,{}).get("amap","")
    last_err = None
    def _fetch(kw, types_code, page):
        params={"key":AMAP_KEY,"keywords":kw,"city":adcode,"citylimit":"true",
                "offset":25,"page":page,"extensions":"all","output":"json"}
        if types_code: params["types"] = types_code
        return requests.get("https://restapi.amap.com/v3/place/text",params=params,timeout=10).json()
    for page in range(1,6):
        if len(places)>=limit: break
        try:
            data=_fetch(cn_kw,amap_type,page)
            if str(data.get("status"))!="1": last_err=f"code={data.get('infocode')} {data.get('info')}"; break
            pois=data.get("pois") or []
            if not pois: break
            places.extend(_parse_amap_pois(pois,cn_kw,type_label,limit,seen))
        except Exception as ex: last_err=str(ex); break
    if len(places)<limit and amap_type:
        for page in range(1,4):
            if len(places)>=limit: break
            try:
                data=_fetch("",amap_type,page)
                if str(data.get("status"))!="1": break
                pois=data.get("pois") or []
                if not pois: break
                places.extend(_parse_amap_pois(pois,cn_kw,type_label,limit,seen))
            except Exception: break
    if len(places)<limit:
        for alt_kw in AMAP_ALT.get(type_label,[]):
            if alt_kw==cn_kw or len(places)>=limit: continue
            try:
                data=_fetch(alt_kw,amap_type,1)
                if str(data.get("status"))!="1": continue
                pois=data.get("pois") or []
                places.extend(_parse_amap_pois(pois,alt_kw,type_label,limit,seen))
            except Exception: continue
    return places[:limit], last_err

def _amap_around(lat, lon, cn_kw, type_label, limit, radius=8000):
    places=[]; errs=[]; seen=set()
    amap_type=PTYPES.get(type_label,{}).get("amap","")
    keywords_list=[cn_kw]+AMAP_ALT.get(type_label,[])
    for kw in keywords_list:
        if len(places)>=limit: break
        for page in range(1,5):
            if len(places)>=limit: break
            try:
                params={"key":AMAP_KEY,"location":f"{lon},{lat}","radius":radius,
                        "keywords":kw,"offset":25,"page":page,"extensions":"all","output":"json"}
                if amap_type: params["types"]=amap_type
                r=requests.get("https://restapi.amap.com/v3/place/around",params=params,timeout=10)
                data=r.json()
                if str(data.get("status"))!="1": errs.append(f"code={data.get('infocode')} {data.get('info')}"); break
                pois=data.get("pois") or []
                if not pois: break
                places.extend(_parse_amap_pois(pois,cn_kw,type_label,limit,seen))
            except Exception as ex: errs.append(str(ex)); break
    return places[:limit], (errs[0] if errs else None)

def search_cn(lat, lon, type_labels, limit_per_type, adcode="", district_name=""):
    all_p=[]; errs=[]
    for tl in type_labels:
        cn=PTYPES[tl]["cn"]
        if adcode: ps,e=_amap_by_adcode(adcode,cn,tl,limit_per_type)
        else: ps,e=_amap_around(lat,lon,cn,tl,limit_per_type)
        if e: errs.append(f"{tl}: {e}")
        all_p.extend(ps)
    seen,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    return out, errs

def _osm_single(lat, lon, ok, ov, type_label, limit, district=""):
    clat,clon=lat,lon
    if district:
        try:
            g=requests.get("https://nominatim.openstreetmap.org/search",
                params={"q":district,"format":"json","limit":1},
                headers={"User-Agent":"TravelPlannerPro/10"},timeout=5).json()
            if g: clat,clon=float(g[0]["lat"]),float(g[0]["lon"])
        except Exception: pass
    q=(f'[out:json][timeout:30];'
       f'(node["{ok}"="{ov}"](around:5000,{clat},{clon});'
       f'way["{ok}"="{ov}"](around:5000,{clat},{clon}););out center {limit*4};')
    els=[]
    for url in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
        try:
            r=requests.post(url,data={"data":q},timeout=28)
            els=r.json().get("elements",[])
            if els: break
        except Exception: continue
    places=[]
    for el in els:
        tags=el.get("tags",{})
        name=tags.get("name:en") or tags.get("name") or ""
        if not name or is_chain(name): continue
        elat=(el.get("lat",0) if el["type"]=="node" else el.get("center",{}).get("lat",0))
        elon=(el.get("lon",0) if el["type"]=="node" else el.get("center",{}).get("lon",0))
        if not elat or not elon: continue
        parts=[tags.get(k,"") for k in ["addr:housenumber","addr:street","addr:suburb","addr:city"] if tags.get(k)]
        places.append({
            "name":name,"lat":elat,"lon":elon,
            "rating":round(random.uniform(3.8,5.0),1),
            "address":", ".join(parts),"phone":tags.get("phone") or tags.get("contact:phone") or "",
            "website":tags.get("website") or tags.get("contact:website") or "",
            "type":ov,"type_label":type_label,
            "district":tags.get("addr:suburb") or tags.get("addr:city") or "",
            "description":tdesc(ov),
        })
        if len(places)>=limit: break
    return places

def search_intl(lat, lon, type_labels, limit_per_type, district=""):
    all_p=[]
    for tl in type_labels:
        ok,ov=PTYPES[tl]["osm"]
        all_p.extend(_osm_single(lat,lon,ok,ov,tl,limit_per_type,district))
    seen,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],3),round(p["lon"],3))
        if k not in seen: seen.add(k); out.append(p)
    return out

def demo_places(lat, lon, type_labels, n_per_type, seed, district=""):
    random.seed(seed)
    NAMES={
        "🏛️ Attraction":["Grand Museum","Sky Tower","Ancient Temple","Art Gallery","Historic Castle","Night Market","Cultural Center","Scenic Viewpoint","Old Town Square","Waterfront Walk"],
        "🍜 Restaurant":["Sakura Dining","Ramen House","Sushi Master","Hot Pot Garden","Yakitori Bar","Noodle King","Dim Sum Palace","Street Food Alley","Rooftop Kitchen","Harbour Grill"],
        "☕ Café":["Blue Bottle","Artisan Brew","Matcha Corner","Loft Coffee","Roast & Toast","Morning Pour","Bean & Book","The Cozy Cup"],
        "🌿 Park":["Riverside Park","Sakura Garden","Central Park","Bamboo Grove","Zen Garden","Hilltop Reserve"],
        "🛍️ Shopping":["Central Mall","Night Bazaar","Vintage Market","Designer District","Flea Market"],
        "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Garden","Night Club"],
        "🏨 Hotel":["Grand Palace Hotel","Boutique Inn","City View Hotel","Zen Retreat"],
    }
    DNAMES=["North Area","Central Area","South Area"]
    centers=[(lat+random.uniform(-.022,.022),lon+random.uniform(-.022,.022)) for _ in range(min(3,max(1,len(type_labels))))]
    result=[]
    for tl in type_labels:
        names=list(NAMES.get(tl,["Local Spot"])); random.shuffle(names)
        for i,name in enumerate(names[:n_per_type]):
            ci=i%len(centers); clat,clon=centers[ci]
            result.append({
                "name":name,"lat":round(clat+random.uniform(-.006,.006),5),"lon":round(clon+random.uniform(-.006,.006),5),
                "rating":round(random.uniform(4.0,4.9),1),
                "address":"Preview mode — connect to the internet for real addresses",
                "phone":"","website":"",
                "type":PTYPES[tl]["cn"] if tl in PTYPES else tl,
                "type_label":tl,"district":district or DNAMES[ci%len(DNAMES)],"description":tdesc(tl),
            })
    return result

@st.cache_data(ttl=180, show_spinner=False)
def fetch_all_places(city_lat, city_lon, country, is_cn, type_labels_t,
                     limit_per_type, day_adcodes_t, day_district_names_t,
                     day_anchor_lats_t, day_anchor_lons_t, _seed):
    random.seed(_seed)
    tls=list(type_labels_t); all_raw=[]; warn_msg=None; all_api_errs=[]; seen_adcodes=set()
    for d_idx in range(len(day_adcodes_t)):
        adc=day_adcodes_t[d_idx]; dname=day_district_names_t[d_idx]
        dlat=day_anchor_lats_t[d_idx] if day_anchor_lats_t[d_idx] is not None else city_lat
        dlon=day_anchor_lons_t[d_idx] if day_anchor_lons_t[d_idx] is not None else city_lon
        combo_key=adc or f"latlon_{round(dlat,3)}_{round(dlon,3)}"
        if combo_key in seen_adcodes: continue
        seen_adcodes.add(combo_key)
        if is_cn:
            ps,errs=search_cn(dlat,dlon,tls,limit_per_type,adc,dname)
            all_api_errs.extend(errs)
        else:
            ps=search_intl(dlat,dlon,tls,limit_per_type,dname)
        all_raw.extend(ps)
    seen,out=set(),[]
    for p in all_raw:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    out=geo_dedup(out)
    if not out:
        out=demo_places(city_lat,city_lon,tls,limit_per_type,_seed)
        if is_cn:
            if all_api_errs:
                sample_err="; ".join(all_api_errs[:2])
                warn_msg=(f"⚠️ **高德 API 无法返回数据**<br>错误：`{sample_err}`<br>"
                         "请检查Key类型（Web服务）并清空IP白名单。<br>当前显示演示数据。")
            else:
                warn_msg="⚠️ 高德 API 网络不可达，显示演示数据。"
        else:
            warn_msg="⚠️ Couldn't fetch live data right now — showing sample places."
    df=pd.DataFrame(out)
    for col in ["address","phone","website","type","type_label","district","description"]:
        if col not in df.columns: df[col]=""
    df["rating"]=pd.to_numeric(df["rating"],errors="coerce").fillna(0.0)
    df=df.sort_values("rating",ascending=False).reset_index(drop=True)
    return df, warn_msg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH UI HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_auth_panel(lang: str = "EN"):
    """Render login/register/logout in sidebar."""
    if not AUTH_OK:
        return

    tok = st.session_state.get("_auth_token", "")
    user = get_user_from_session(tok) if tok else None

    if user:
        uname = user.get("username", "")
        pts = user.get("points", 0) if POINTS_OK else 0
        st.markdown(
            f'<div style="background:#fff7ed;border-radius:10px;padding:10px 12px;margin-bottom:8px">'
            f'👤 <b>{uname}</b>  '
            f'<span class="wl-badge">🎫 {pts} pts</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(_t("auth_logout", lang), key="auth_logout_btn"):
            logout_user(tok)
            st.session_state.pop("_auth_token", None)
            st.rerun()
    else:
        tab_login, tab_reg = st.tabs([_t("auth_login", lang), _t("auth_register", lang)])
        with tab_login:
            uname = st.text_input(_t("auth_username", lang), key="li_user")
            pw = st.text_input(_t("auth_password", lang), type="password", key="li_pw")
            if st.button(_t("auth_login", lang), key="li_btn", use_container_width=True):
                ok, msg, tok = login_user(uname, pw)
                if ok:
                    st.session_state["_auth_token"] = tok
                    if POINTS_OK:
                        add_points(uname, "daily_login")
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        with tab_reg:
            ru = st.text_input(_t("auth_username", lang), key="reg_user")
            re = st.text_input(_t("auth_email", lang), key="reg_email")
            rp = st.text_input(_t("auth_password", lang), type="password", key="reg_pw")
            if st.button(_t("auth_register", lang), key="reg_btn", use_container_width=True):
                ok, msg = register_user(ru, rp, re)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


def _current_user(lang="EN"):
    """Return current user dict or None."""
    if not AUTH_OK:
        return None
    tok = st.session_state.get("_auth_token", "")
    return get_user_from_session(tok) if tok else None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WISHLIST BUTTON (inline, per-place)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _wishlist_btn(place_row: dict, city: str, lang: str = "EN"):
    """Render heart button + checkin button for a place."""
    user = _current_user(lang)
    if not user or not WISHLIST_OK:
        return
    uname = user["username"]
    in_wl = is_in_wishlist(uname, place_row.get("name", ""))
    wl_lbl = "💔 Remove" if in_wl else _t("wishlist_add", lang)
    if st.button(wl_lbl, key=f"wl_{place_row['name'][:20]}", help="Save to wishlist"):
        if in_wl:
            remove_from_wishlist(uname, place_row["name"])
            st.toast("Removed from wishlist")
        else:
            place_row["_city"] = city
            add_to_wishlist(uname, place_row)
            st.toast(_t("wishlist_saved", lang))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLACE SWAP UI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_swap_panel(itinerary: dict, df: pd.DataFrame, lang: str = "EN"):
    """Let users swap individual stops with alternatives."""
    if not itinerary:
        return
    with st.expander("🔄 Swap a Stop", expanded=False):
        st.caption("Replace any stop with a nearby alternative of the same type.")
        day_opts = list(itinerary.keys())
        sel_day = st.selectbox("Which day?", day_opts, key="swap_day")
        stops = itinerary.get(sel_day, [])
        if not stops:
            st.info("No stops on this day."); return
        stop_names = [f"Stop {i+1}: {s['name']}" for i, s in enumerate(stops)]
        sel_stop_idx = st.selectbox("Which stop to replace?", range(len(stop_names)),
                                    format_func=lambda i: stop_names[i], key="swap_stop")
        current_stop = stops[sel_stop_idx]
        cur_type = current_stop.get("type_label", "")
        cur_lat = current_stop.get("lat", 0)
        cur_lon = current_stop.get("lon", 0)

        # Find candidates of same type, not already in itinerary
        used = {s["name"] for stops_list in itinerary.values() for s in stops_list}
        candidates = df[
            (df["type_label"] == cur_type) & (~df["name"].isin(used))
        ].sort_values("rating", ascending=False).head(8)

        if candidates.empty:
            st.info("No alternatives found for this stop type."); return

        alt_names = candidates["name"].tolist()
        sel_alt = st.selectbox("Replace with:", alt_names, key="swap_alt")
        alt_row = candidates[candidates["name"] == sel_alt].iloc[0].to_dict()

        if st.button("✅ Confirm Swap", key="swap_confirm", use_container_width=True):
            new_itin = swap_place_in_itinerary(
                st.session_state.get("_itin", itinerary),
                sel_day, sel_stop_idx, alt_row,
            )
            st.session_state["_itin"] = new_itin
            st.success(f"Swapped! '{current_stop['name']}' → '{sel_alt}'")
            st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLLABORATION UI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_collab_panel(lang: str = "EN"):
    if not AUTH_OK:
        return
    user = _current_user(lang)
    if not user:
        st.caption(_t("auth_login_required", lang))
        return
    with st.expander(_t("collab_heading", lang), expanded=False):
        uname = user["username"]
        st.markdown(f"**{_t('collab_invite', lang)}**")
        itin_id = st.session_state.get("_collab_itin_id", "")
        if not itin_id:
            if st.button(_t("collab_share_link", lang), key="collab_gen"):
                import uuid as _uuid
                itin_id = str(_uuid.uuid4())[:8]
                token = create_collab_link(uname, itin_id)
                st.session_state["_collab_itin_id"] = itin_id
                st.session_state["_collab_token"] = token
                st.success(f"Share code: **{token}**")
                st.code(token)
        else:
            tok = st.session_state.get("_collab_token", "")
            st.success(f"Share code: **{tok}**")
            st.caption("Send this code to a friend. They can join from their app.")

        st.markdown("---")
        st.markdown("**Join someone's itinerary:**")
        join_code = st.text_input("Enter share code", key="collab_join_code", placeholder="ABC123XY")
        if st.button("🤝 Join", key="collab_join_btn"):
            ok, msg = join_collab(uname, join_code)
            st.success(msg) if ok else st.error(msg)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_map(df, lat, lon, itinerary, hotel_c=None, depart_c=None, arrive_c=None):
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB positron")
    visit_info = {}
    if itinerary:
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            for s_idx, s in enumerate(stops):
                visit_info[s["name"]] = (d_idx, s_idx + 1, s)

    if itinerary:
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            if len(stops) < 2: continue
            dc = DAY_COLORS[d_idx % len(DAY_COLORS)]
            for si in range(len(stops) - 1):
                a, b = stops[si], stops[si + 1]
                tr = a.get("transport_to_next") or {}
                folium.PolyLine(
                    [[a["lat"], a["lon"]], [b["lat"], b["lon"]]],
                    color=dc, weight=3.8, opacity=0.75, dash_array="7 4",
                ).add_to(m)
                mid = [(a["lat"] + b["lat"]) / 2, (a["lon"] + b["lon"]) / 2]
                pt = (
                    f"<div style='font-size:.8rem'>"
                    f"<b>{dl} · Leg {si+1}</b><br>"
                    f"{tr.get('mode','—')}<br>"
                    f"⏱ {tr.get('duration','—')} · 📏 {tr.get('distance_km','—')} km<br>"
                    f"💸 {tr.get('cost_str', tr.get('cost_str','—'))}<br>"
                    f"{a['name']} → {b['name']}</div>"
                )
                folium.Marker(
                    mid,
                    popup=folium.Popup(pt, max_width=210),
                    tooltip="🚦 Travel to next stop",
                    icon=folium.DivIcon(
                        html=f'<div style="width:9px;height:9px;border-radius:50%;background:{dc};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.3)"></div>',
                        icon_size=(9,9), icon_anchor=(4,4),
                    ),
                ).add_to(m)

    for _, row in df.iterrows():
        vi = visit_info.get(row["name"])
        if vi:
            d_idx, stop_num, _ = vi
            color = DAY_COLORS[d_idx % len(DAY_COLORS)]
            label = str(stop_num)
            day_info = f"Day {d_idx+1} · Stop {stop_num}"
        else:
            color = "#b0a090"; label = "·"; day_info = "Not scheduled"
        addr = str(row.get("address", ""))
        addr_h = (f"<br><small>📍 {addr[:60]}</small>" if addr and "demo" not in addr.lower() else "")
        ph_h = (f"<br><small>📞 {row['phone']}</small>" if row.get("phone") else "")
        dist_h = (f"<br><small>📌 {row.get('district','')}</small>" if row.get("district") else "")
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<div style='font-weight:700;font-size:.9rem'>{row['name']}</div>"
            f"<div style='color:#888;font-size:.78rem'>"
            f"⭐ {row['rating']:.1f} · {day_info}</div>"
            f"{dist_h}{addr_h}{ph_h}</div>"
        )
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{day_info} — {row['name']}",
            icon=folium.DivIcon(
                html=(f'<div style="width:22px;height:22px;border-radius:50%;'
                      f'background:{color};border:2px solid white;'
                      f'display:flex;align-items:center;justify-content:center;'
                      f'color:white;font-size:11px;font-weight:700;'
                      f'box-shadow:0 2px 6px rgba(0,0,0,.3)">{label}</div>'),
                icon_size=(22,22), icon_anchor=(11,11),
            ),
        ).add_to(m)

    def smark(coords, icon_char, tip):
        folium.Marker(
            list(coords), tooltip=tip,
            icon=folium.DivIcon(
                html=(f'<div style="font-size:22px;text-shadow:0 1px 3px rgba(0,0,0,.4)">{icon_char}</div>'),
                icon_size=(30,30), icon_anchor=(15,15),
            ),
        ).add_to(m)

    if hotel_c: smark(hotel_c, "🏨", "Your hotel")
    if depart_c: smark(depart_c, "🚩", "Starting Point")
    if arrive_c: smark(arrive_c, "🏁", "Final Departure")
    return m


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE  (with per-stop wishlist + checkin)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_table(df, itinerary, day_budgets, country, city="", lang="EN"):
    if isinstance(day_budgets, int):
        day_budgets = [day_budgets] * 30
    stop_map = {}
    if itinerary:
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            for s_idx, s in enumerate(stops):
                stop_map[s["name"]] = (d_idx, s_idx + 1, s)
    name_to_row = {row["name"]: row for _, row in df.iterrows()}
    scheduled = []
    if itinerary:
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            for s_idx, s in enumerate(stops):
                if s["name"] in name_to_row:
                    scheduled.append((d_idx, s_idx + 1, s["name"]))
    snames = {x[2] for x in scheduled}
    unscheduled = [row for _, row in df.iterrows() if row["name"] not in snames]

    rows_html = ""; seq = 0; cur_day = -1
    for d_idx, stop_num, name in scheduled:
        seq += 1
        row = name_to_row[name]
        color = DAY_COLORS[d_idx % len(DAY_COLORS)]
        d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else day_budgets[-1]
        if d_idx != cur_day:
            cur_day = d_idx
            day_stops = list((itinerary or {}).get(f"Day {d_idx+1}", []))
            _em_d, _lb_d, _lc_d, _bgc_d = budget_level(d_usd)
            rows_html += (
                f'<tr class="day-hdr"><td colspan="9">'
                f'Day {d_idx+1}  ·  {len(day_stops)} stops'
                f'  <span class="budget-pill">{_em_d} ${d_usd}/day</span>'
                f'</td></tr>'
            )
        _, _, sd = stop_map[name]
        rows_html += _trow(seq, row, d_idx+1, stop_num, sd, color, d_usd, country, lang)

    st.markdown(
        '<div style="overflow-x:auto">'
        '<table class="itin-table">'
        f'<thead><tr>'
        f'<th>{_t("tbl_seq",lang)}</th>'
        f'<th>{_t("tbl_day_stop",lang)}</th>'
        f'<th>{_t("tbl_time",lang)}</th>'
        f'<th>{_t("tbl_place",lang)}</th>'
        f'<th>{_t("tbl_district",lang)}</th>'
        f'<th>{_t("tbl_type",lang)}</th>'
        f'<th>{_t("tbl_rating",lang)}</th>'
        f'<th>{_t("tbl_transport",lang)}</th>'
        f'<th>{_t("tbl_contact",lang)}</th>'
        f'</tr></thead><tbody>'
        f'{rows_html}'
        '</tbody></table></div>',
        unsafe_allow_html=True,
    )

    # Meal suggestions (per day)
    if MEAL_OK and itinerary:
        avg_usd = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            if not stops: continue
            d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else avg_usd
            html = render_meal_panel(city, d_idx, d_usd, country, lang, seed=d_idx*7+42)
            st.markdown(html, unsafe_allow_html=True)

    # Must-see attractions
    if DATA_MGR_OK:
        ms_html = render_must_see_panel(city, lang)
        if ms_html:
            st.markdown(ms_html, unsafe_allow_html=True)

    if unscheduled:
        _render_extra_recommendations(unscheduled, day_budgets, country, city, lang)


def _trow(seq, row, day_n, stop_n, sd, color, daily_usd, country, lang="EN"):
    bg = "#fffdf8" if seq % 2 == 0 else "#faf6ef"
    if day_n:
        dc = (f'<span style="background:{color};color:#fff;border-radius:50%;'
              f'width:22px;height:22px;display:inline-flex;align-items:center;'
              f'justify-content:center;font-weight:700;font-size:11px">{stop_n}</span>'
              f'<br><small style="color:#999">D{day_n}</small>')
        tc = sd.get("time_slot","—") if sd else "—"
        tr = sd.get("transport_to_next") if sd else None
        if tr:
            dist_km = tr.get("distance_km",0) or 0
            _, t_cost = transport_cost_estimate(dist_km, daily_usd, country)
            ti = tr.get("transit_info","")
            ti_html = f'<br><small style="color:#999">{ti}</small>' if ti else ""
            rc = (f'{tr["mode"]}<br>'
                  f'<small style="color:#888">⏱ {tr["duration"]} · {dist_km} km<br>'
                  f'💸 {tr.get("cost_str",t_cost)}{ti_html}</small>')
        else:
            etr = sd.get("end_transport") if sd else None
            if etr:
                rc = (f'{etr["mode"]}<br>'
                      f'<small style="color:#888">→ {etr.get("to_label","End")}'
                      f' · {etr.get("duration","")}</small>')
            else:
                rc = f'<small style="color:#bbb">{_t("last_stop",lang)}</small>'
    else:
        dc = '—'; tc = "—"; rc = '—'
    tl = row.get("type_label","") or row.get("type","")
    type_c = f'<span style="font-size:.8rem">{tl}</span>' if tl and tl.lower() not in ("demo","") else "—"
    r_val = row.get("rating",0)
    rstr = f'⭐ {r_val:.1f}' if r_val > 0 else "—"
    desc = row.get("description","")
    cost_html = ""
    if day_n and daily_usd > 0 and tl:
        mid, cost_str = cost_estimate(tl, daily_usd, country)
        cost_html = f'<div style="font-size:.75rem;color:#c97d35;margin-top:2px">💰 {cost_str}</div>'
    nc = (f'<div style="font-weight:600;font-size:.86rem">{row["name"]}</div>'
          + (f'<div style="color:#888;font-size:.75rem">{desc}</div>' if desc else "")
          + (cost_html if cost_html else ""))
    addr = str(row.get("address",""))
    phone = str(row.get("phone",""))
    ct = ""
    if addr and "demo" not in addr.lower(): ct += f'<div style="font-size:.75rem">📍 {addr[:55]}</div>'
    if phone: ct += f'<div style="font-size:.75rem">📞 {phone}</div>'
    if not ct: ct = '—'
    dist = row.get("district","") or "—"
    return (
        f'<tr style="background:{bg}">'
        f'<td style="text-align:center;color:#999;font-size:.8rem">{seq}</td>'
        f'<td style="text-align:center">{dc}</td>'
        f'<td style="color:#777;font-size:.83rem;white-space:nowrap">{tc}</td>'
        f'<td>{nc}</td>'
        f'<td style="color:#777;font-size:.8rem">{dist}</td>'
        f'<td>{type_c}</td>'
        f'<td style="white-space:nowrap">{rstr}</td>'
        f'<td style="font-size:.8rem">{rc}</td>'
        f'<td style="font-size:.75rem">{ct}</td>'
        f'</tr>'
    )


def _render_extra_recommendations(unscheduled, day_budgets, country, city="", lang="EN"):
    avg_usd = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    CATS = [
        ("🌿 Nature",   ["🌿 Park"]),
        ("🏛️ Sights",  ["🏛️ Attraction"]),
        ("🍜 Dining",   ["🍜 Restaurant","☕ Café"]),
        ("🛍️ Shopping",["🛍️ Shopping"]),
        ("🍺 Nightlife",["🍺 Bar/Nightlife"]),
        ("🏨 Hotels",   ["🏨 Hotel"]),
    ]
    by_type: dict = {}
    for row in unscheduled:
        tl = row.get("type_label","") or row.get("type","")
        by_type.setdefault(tl, []).append(row)
    cat_data = []
    covered = set()
    for cat_name, type_list in CATS:
        items = []
        for tl in type_list:
            items.extend(by_type.get(tl, []))
            covered.add(tl)
        if items: cat_data.append((cat_name, items))
    others = [r for tl, rows in by_type.items() if tl not in covered for r in rows]
    if others: cat_data.append(("✨ Other", others))
    if not cat_data: return

    st.markdown(f'<div class="sec-head">{_t("rec_heading",lang)}</div>', unsafe_allow_html=True)
    st.caption(_t("rec_caption", lang))
    import random as _rnd
    user = _current_user(lang)
    uname = user["username"] if user else None

    for cat_name, places in cat_data:
        seed_key = f"_rec_{cat_name}"
        if seed_key not in st.session_state: st.session_state[seed_key] = 0
        col_h, col_b = st.columns([6, 1])
        with col_h:
            st.markdown(
                f'<div style="font-weight:600;font-size:.9rem;margin:10px 0 4px">{cat_name} '
                f'<span style="color:#bbb;font-size:.78rem">({min(10,len(places))} / {len(places)})</span></div>',
                unsafe_allow_html=True,
            )
        with col_b:
            if st.button(_t("rec_refresh",lang), key=f"_rfbtn_{cat_name}", help="Show different picks"):
                st.session_state[seed_key] = (st.session_state[seed_key]+1) % 9999
        _rnd.seed(st.session_state[seed_key])
        pool = list(places)
        picks = _rnd.sample(pool, min(10, len(pool)))
        picks.sort(key=lambda r: r.get("rating",0), reverse=True)
        cards_html = ""
        for p in picks:
            name = str(p.get("name",""))
            tl = str(p.get("type_label","") or p.get("type",""))
            rat = p.get("rating",0)
            dist = str(p.get("district","") or "—")
            addr = str(p.get("address","") or "")[:55]
            phone = str(p.get("phone","") or "")
            _, cost_s = cost_estimate(tl, avg_usd, country)
            rat_s = f"⭐ {rat:.1f}" if rat else "—"
            addr_s = f'<div style="font-size:.74rem;color:#999">📍 {addr}</div>' if addr and "demo" not in addr.lower() else ""
            ph_s = f'<div style="font-size:.74rem;color:#999">📞 {phone}</div>' if phone else ""
            cards_html += (
                f'<div class="rec-card">'
                f'<div class="rc-name">{name}</div>'
                f'<div class="rc-meta">{tl}  ·  {dist}</div>'
                f'{addr_s}{ph_s}'
                f'<div style="margin-top:6px;display:flex;justify-content:space-between">'
                f'<div style="font-size:.78rem">{rat_s}</div>'
                f'<div style="font-size:.75rem;color:#c97d35">💰 {cost_s}</div>'
                f'</div>'
                f'<span class="rc-badge">{tl.split()[0] if tl else ""}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="rec-grid">{cards_html}</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_budget_summary(itinerary, day_budgets, country, days, lang="EN"):
    if not itinerary: return
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*days
    sym, rate = _local_rate(country)

    def _fmt(usd_amt, d_usd):
        lo_u = round(usd_amt*0.8); hi_u = round(usd_amt*1.2)
        if country == "US": return f"${lo_u}–${hi_u}"
        lo_l = round(lo_u*rate); hi_l = round(hi_u*rate)
        return f"${lo_u}–${hi_u} ({sym}{lo_l}–{sym}{hi_l})"

    day_totals = []
    for d_idx, (dl, stops) in enumerate(itinerary.items()):
        if not stops: continue
        d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else day_budgets[-1]
        total_usd = 0.0
        for s in stops:
            tl = s.get("type_label","")
            mid, _ = cost_estimate(tl, d_usd, country)
            total_usd += mid
            tr = s.get("transport_to_next") or {}
            if tr:
                dist_km = tr.get("distance_km",0) or 0
                t_mid, _ = transport_cost_estimate(dist_km, d_usd, country)
                total_usd += t_mid
        day_totals.append((dl, total_usd, d_usd))
    if not day_totals: return

    st.markdown(f'<div class="sec-head">{_t("budget_heading",lang)}</div>', unsafe_allow_html=True)
    grand_total = sum(t for _, t, _ in day_totals)
    grand_budget = sum(d for _, _, d in day_totals)
    n_cols = min(len(day_totals), 4) + 1
    cols = st.columns(n_cols)
    any_over = False

    for i, (dl, total_usd, d_usd) in enumerate(day_totals):
        with cols[i % (n_cols-1)]:
            over = total_usd > d_usd * 1.1
            if over: any_over = True
            em, lb, lc, _ = budget_level(d_usd)
            amt_str = _fmt(total_usd, d_usd)
            over_str = " 🔴" if over else ""
            st.markdown(
                f'<div class="bsum-card">'
                f'<div class="day-lbl">{dl}</div>'
                f'<div class="day-amt">${round(total_usd)}{over_str}</div>'
                f'<div class="day-rng">{amt_str}</div>'
                f'<div class="day-bud">{em} {lb} · ${d_usd}/day</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with cols[-1]:
        _lo=round(grand_total*0.8); _hi=round(grand_total*1.2)
        _lo_l=round(_lo*rate); _hi_l=round(_hi*rate)
        grand_str=(f"${_lo}–${_hi}" if country=="US" else f"${_lo}–${_hi} ({sym}{_lo_l}–{sym}{_hi_l})")
        st.markdown(
            f'<div class="bsum-card" style="background:#fff7ed;border:1px solid #e8a558">'
            f'<div class="day-lbl">{_t("budget_total",lang)}</div>'
            f'<div class="day-amt" style="font-size:1.5rem">${round(grand_total)}</div>'
            f'<div class="day-rng">{grand_str}</div>'
            f'<div class="day-bud">{days} days · ${grand_budget} total</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if any_over:
        st.markdown(f'<div style="background:#fff3cd;border-radius:8px;padding:10px;margin-top:8px;font-size:.85rem">{_t("budget_over",lang)}</div>', unsafe_allow_html=True)

    with st.expander(_t("budget_breakdown",lang)):
        rows = []
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            if not stops: continue
            d_usd = day_budgets[d_idx] if d_idx<len(day_budgets) else day_budgets[-1]
            for s in stops:
                tl = s.get("type_label","")
                _, cost_rng = cost_estimate(tl, d_usd, country)
                rows.append({"Day":dl,"Place":s.get("name",""),"Type":tl,"Budget":f"${d_usd}/day","Est. Cost/person":cost_rng})
                tr = s.get("transport_to_next") or {}
                if tr:
                    dk = tr.get("distance_km",0) or 0
                    _, t_rng = transport_cost_estimate(dk, d_usd, country)
                    rows.append({"Day":dl,"Place":f"→ Transport ({tr.get('mode','')})","Type":"Transport","Budget":f"${d_usd}/day","Est. Cost/person":t_rng})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRANSPORT COMPARISON (expandable per leg)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_transport_details(itinerary, country, city, day_budgets, lang="EN"):
    """Show modal transport comparison for each leg."""
    if not TRANSPORT_OK or not itinerary:
        return
    if isinstance(day_budgets, int):
        day_budgets = [day_budgets] * 30
    with st.expander("🚇 Transport Options (all legs)", expanded=False):
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            if len(stops) < 2: continue
            d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else 60
            st.markdown(f"**{dl}**")
            for si in range(len(stops)-1):
                a, b = stops[si], stops[si+1]
                html = render_transport_comparison(
                    a["lat"], a["lon"], b["lat"], b["lon"],
                    a["name"], b["name"],
                    country=country, city=city, daily_usd=d_usd, lang=lang,
                )
                st.markdown(html, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF EXPORT (same as v9 + lang)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_pdf(itinerary, city, day_budgets, country):
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*30
    avg_usd = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    total_budget = sum(day_budgets)
    DAY_COLS=["#c97d35","#3a8fd4","#3aaa7a","#9b59b6","#e05c3a","#1abc9c","#e91e63","#f39c12"]
    def clean(s): return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    total_stops = sum(len(v) for v in itinerary.values() if v)
    _, label, _, _ = budget_level(avg_usd)
    curr_str = fmt_currency_row(avg_usd, country)

    all_marker_js=[]; all_polyline_js=[]; map_lats=[]; map_lons=[]
    for d_idx,(day_label,stops) in enumerate(itinerary.items()):
        if not stops: continue
        col=DAY_COLS[d_idx%len(DAY_COLS)]; poly_coords=[]
        for si,s in enumerate(stops):
            lat=s.get("lat",0); lon=s.get("lon",0)
            if not lat or not lon: continue
            map_lats.append(lat); map_lons.append(lon); poly_coords.append(f"[{lat},{lon}]")
            nm=(s.get("name","") or "").replace('"','\\"').replace("'","\\'")
            addr=(s.get("address","") or "")[:50].replace('"','\\"').replace("'","\\'")
            tsl=(s.get("time_slot","") or "").replace('"','\\"')
            all_marker_js.append(f'{{"lat":{lat},"lon":{lon},"n":"{nm}","d":{d_idx+1},"s":{si+1},"c":"{col}","a":"{addr}","t":"{tsl}"}}')
        if len(poly_coords)>1:
            all_polyline_js.append(f'{{"c":"{col}","pts":[{",".join(poly_coords)}]}}')

    clat=sum(map_lats)/len(map_lats) if map_lats else 35.0
    clon=sum(map_lons)/len(map_lons) if map_lons else 139.0
    markers_json="["+",".join(all_marker_js)+"]"
    polylines_json="["+",".join(all_polyline_js)+"]"

    days_html=""
    for d_idx,(day_label,stops) in enumerate(itinerary.items()):
        if not stops: continue
        d_usd=day_budgets[d_idx] if d_idx<len(day_budgets) else day_budgets[-1]
        col=DAY_COLS[d_idx%len(DAY_COLS)]; rows=""
        for si,s in enumerate(stops):
            tr=s.get("transport_to_next") or {}
            route=f"{tr.get('mode','—')} · {tr.get('duration','')}" if tr else "Last stop"
            addr=clean(s.get("address","")); phone=clean(s.get("phone",""))
            contact=""
            if addr and "demo" not in addr.lower(): contact+=f"<br>📍 {addr[:60]}<br>"
            if phone: contact+=f"<br>📞 {phone}<br>"
            tl=clean(s.get("type_label","")); name=clean(s.get("name",""))
            ts=clean(s.get("time_slot","—")); dist=clean(s.get("district","") or "—")
            rat=s.get("rating",0)
            rows+=f"<tr><td>{si+1}</td><td>{ts}</td><td>{name}{contact}</td><td>{tl}</td><td>{dist}</td><td>{'⭐ '+str(rat) if rat else '—'}</td><td>{clean(route)}</td></tr>"
        days_html+=f"<h3 style='color:{col};margin-top:20px'>{clean(day_label)} — {len(stops)} stops · ${d_usd}/day</h3><table style='width:100%;border-collapse:collapse;font-size:.85rem'><thead><tr style='background:#f5ede0'><th>#</th><th>Time</th><th>Place</th><th>Type</th><th>District</th><th>Rating</th><th>Route</th></tr></thead><tbody>{rows}</tbody></table>"

    legend_items=""
    for d_idx in range(min(len(itinerary),len(DAY_COLS))):
        col=DAY_COLS[d_idx%len(DAY_COLS)]
        legend_items+=f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px"><span style="width:12px;height:12px;border-radius:50%;background:{col};display:inline-block"></span>Day {d_idx+1}</span>'

    html=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Itinerary — {clean(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>body{{font-family:'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:20px;color:#333}}
h1{{color:#c97d35}}table td,table th{{padding:7px 10px;border:1px solid #eee;text-align:left}}
.info{{background:#fff7ed;border-radius:10px;padding:12px 16px;margin:16px 0;font-size:.9rem}}
#map{{height:400px;border-radius:12px;margin:20px 0}}
.legend{{margin:8px 0 16px}}</style></head><body>
<h1>✈ Travel Itinerary — {clean(city.title())}</h1>
<div class="info">Total budget: ${total_budget} · {len([b for b in day_budgets if b])} days · {total_stops} stops · avg ${avg_usd}/day · {label} · {clean(curr_str)}</div>
<div class="legend">{legend_items}</div>
<div id="map"></div>
{days_html}
<p style="color:#bbb;font-size:.78rem;margin-top:32px">Generated by Trip Planner · Cost estimates are approximate.<br>💡 To save as PDF: press Ctrl+P (or ⌘P on Mac) → Save as PDF</p>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',{{attribution:'CartoDB'}}).addTo(map);
var markers={markers_json};
markers.forEach(function(m){{
  var ic=L.divIcon({{html:'<div style="width:22px;height:22px;border-radius:50%;background:'+m.c+';border:2px solid white;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:700;box-shadow:0 2px 6px rgba(0,0,0,.3)">'+m.s+'</div>',iconSize:[22,22],iconAnchor:[11,11]}});
  L.marker([m.lat,m.lon],{{icon:ic}}).bindPopup('<b>'+m.n+'</b><br>Day '+m.d+' Stop '+m.s+'<br>'+m.t+'<br>'+m.a).addTo(map);
}});
var pls={polylines_json};
pls.forEach(function(pl){{L.polyline(pl.pts,{{color:pl.c,weight:3.5,opacity:.75,dashArray:'7 4'}}).addTo(map);}});
</script></body></html>"""
    return html.encode("utf-8")


def build_calendar_urls(itinerary, start_date_str, city):
    import urllib.parse
    from datetime import datetime, timedelta
    try: base_date=datetime.strptime(start_date_str,"%Y-%m-%d")
    except Exception: base_date=None
    SLOT_MAP={"9:00 AM":(9,0),"10:30 AM":(10,30),"12:00 PM":(12,0),"1:30 PM":(13,30),
              "3:00 PM":(15,0),"4:30 PM":(16,30),"6:00 PM":(18,0),"7:30 PM":(19,30),"9:00 PM":(21,0)}
    results=[]
    for d_idx,(day_label,stops) in enumerate(itinerary.items()):
        for si,s in enumerate(stops):
            name=s.get("name","Stop"); addr=s.get("address","") or city
            tslot=s.get("time_slot","9:00 AM"); hh,mm=SLOT_MAP.get(tslot,(9,0))
            if base_date:
                day_dt=base_date+timedelta(days=d_idx)
                start_dt=day_dt.replace(hour=hh,minute=mm,second=0)
                end_dt=start_dt+timedelta(hours=1,minutes=30)
                fmt="%Y%m%dT%H%M%S"
                dates_str=f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
            else: dates_str=""
            detail_parts=[f"📍 {city.title()} — {day_label} Stop {si+1}"]
            if s.get("type_label"): detail_parts.append(f"Type: {s['type_label']}")
            if s.get("phone"): detail_parts.append(f"📞 {s['phone']}")
            tr=s.get("transport_to_next") or {}
            if tr: detail_parts.append(f"Next: {tr.get('mode','')} {tr.get('duration','')}")
            params={"action":"TEMPLATE","text":f"{name} ({city.title()})","details":"<br />".join(detail_parts),"location":addr[:100]}
            if dates_str: params["dates"]=dates_str
            url="https://calendar.google.com/calendar/render?"+urllib.parse.urlencode(params)
            results.append({"day":day_label,"stop":si+1,"name":name,"url":url})
    return results


def render_export_panel(itinerary, city, day_budgets, country, lang="EN"):
    if not itinerary or not any(itinerary.values()): return
    if isinstance(day_budgets, int): day_budgets=[day_budgets]*30
    st.markdown(f'<div class="sec-head">{_t("export_heading",lang)}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1,1])
    with c1:
        st.markdown(f"**{_t('export_download',lang)}**")
        try:
            pdf_bytes=build_pdf(itinerary,city,day_budgets,country)
            st.download_button(
                label=_t("export_download_btn",lang),
                data=pdf_bytes,
                file_name=f"itinerary_{city.lower().replace(' ','_')}.html",
                mime="text/html",
                use_container_width=True,
            )
            st.caption(_t("export_caption",lang))
        except Exception as ex:
            st.error(_t("err_export_failed",lang,err=str(ex)))
    with c2:
        st.markdown(f"**{_t('export_calendar',lang)}**")
        start_date=st.date_input(_t("export_date",lang),key="export_date",label_visibility="collapsed")
        start_str=start_date.strftime("%Y-%m-%d") if start_date else ""
        cal_urls=build_calendar_urls(itinerary,start_str,city)
        if cal_urls:
            days_seen: dict={}
            for item in cal_urls: days_seen.setdefault(item["day"],[]).append(item)
            for day_lbl,items in days_seen.items():
                with st.expander(f"📅 {day_lbl} ({len(items)} events)",expanded=False):
                    for item in items:
                        st.markdown(
                            f'<a href="{item["url"]}" target="_blank" style="text-decoration:none;color:#3a8fd4">'
                            f'➕ Stop {item["stop"]}: {item["name"][:32]}</a>',
                            unsafe_allow_html=True,
                        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    # ── Language selector (top of sidebar) ──────────────────────
    lang = st.selectbox(
        "🌐 Language / 语言",
        ["EN — English", "ZH — 中文"],
        index=0,
        key="lang_sel",
        label_visibility="visible",
    )
    LANG = "ZH" if lang.startswith("ZH") else "EN"

    # ── Auth panel ───────────────────────────────────────────────
    if AUTH_OK:
        with st.expander("👤 Account", expanded=False):
            render_auth_panel(LANG)

    st.markdown("---")

    # ── Where heading ────────────────────────────────────────────
    st.markdown(f"### {_t('where_heading',LANG)}")
    all_countries = sorted(WORLD_CITIES.keys())
    prev_country = st.session_state.get("sel_country","")
    sel_country = st.selectbox(
        _t("pick_country",LANG),
        [""]+all_countries,
        index=([""]+all_countries).index(prev_country) if prev_country in all_countries else 0,
        key="sel_country",
    )
    if sel_country:
        city_opts_for_country = WORLD_CITIES.get(sel_country,[])
        prev_city_sel = st.session_state.get("sel_city_name","")
        city_sel_idx = (city_opts_for_country.index(prev_city_sel) if prev_city_sel in city_opts_for_country else 0)
        sel_city_name = st.selectbox(_t("pick_city",LANG), city_opts_for_country, index=city_sel_idx, key="sel_city_name")
    else:
        sel_city_name = ""

    city_override = st.text_input(
        _t("city_override",LANG), value="",
        placeholder=_t("city_placeholder",LANG), key="city_override",
    )
    if city_override.strip(): city_input = city_override.strip()
    elif sel_city_name: city_input = sel_city_name
    elif sel_country: city_input = sel_country
    else: city_input = "Tokyo"

    city_key = city_input.strip().lower()
    is_cn = city_key in CN_CITIES
    intl_data = INTL_CITIES.get(city_key)
    if is_cn:
        city_lat, city_lon = CN_CITIES[city_key]; country = "CN"
    elif intl_data:
        city_lat, city_lon, country = intl_data[0], intl_data[1], intl_data[2]
    else:
        city_lat = city_lon = None
        country = COUNTRY_CODES.get(sel_country,"INT")

    hotel_addr = st.text_input(_t("hotel_label",LANG), "", placeholder=_t("hotel_placeholder",LANG))
    depart_addr = st.text_input(_t("depart_label",LANG), "", placeholder=_t("depart_placeholder",LANG))
    arrive_addr = st.text_input(_t("arrive_label",LANG), "", placeholder=_t("arrive_placeholder",LANG))
    st.markdown("---")

    # ── Days & types ─────────────────────────────────────────────
    st.markdown(f"### {_t('plan_heading',LANG)}")
    days = st.number_input(_t("how_many_days",LANG), min_value=1, max_value=10, value=3, step=1)
    ndays = int(days)
    st.markdown(f'<div style="font-size:.85rem;color:#888;margin-bottom:4px">{_t("what_todo",LANG)}</div>', unsafe_allow_html=True)
    sel_types = st.multiselect("types", list(PTYPES.keys()),
                                default=["🏛️ Attraction","🍜 Restaurant"],
                                label_visibility="collapsed")
    if not sel_types: sel_types=["🏛️ Attraction"]

    # ── Districts ────────────────────────────────────────────────
    dist_key = f"dists_{city_key}"
    if dist_key not in st.session_state:
        if is_cn:
            with st.spinner(_t("loading_districts",LANG)+" "+city_input.strip()):
                st.session_state[dist_key] = amap_get_districts(city_input.strip())
        else:
            st.session_state[dist_key] = []
    amap_dists = st.session_state.get(dist_key,[])
    adcode_map: dict = {}; center_map: dict = {}
    for d in amap_dists:
        n,a,la,lo=d.get("name",""),d.get("adcode",""),d.get("lat"),d.get("lon")
        if n and a: adcode_map[n]=a
        if n and la is not None: center_map[n]=(la,lo)

    if is_cn and amap_dists:
        per_day_opts = ["Auto (city-wide)"]+[d["name"] for d in amap_dists]
    elif intl_data and len(intl_data)>3:
        per_day_opts = ["Auto (city-wide)"]+intl_data[3]
    else:
        dyn_key = f"dyn_dists_{city_key}"
        if dyn_key not in st.session_state and city_lat is not None:
            with st.spinner(_t("loading_neighbourhoods",LANG)):
                st.session_state[dyn_key] = get_nominatim_districts(city_input.strip())
        dyn_dists = st.session_state.get(dyn_key,[])
        per_day_opts = (["Auto (city-wide)"]+dyn_dists) if dyn_dists else ["Auto (city-wide)"]

    # ── Per-day tabs ─────────────────────────────────────────────
    st.markdown(f'<div class="sec-head">{_t("day_prefs_heading",LANG)}</div>', unsafe_allow_html=True)
    st.caption(_t("day_prefs_caption",LANG))
    day_quotas=[]; day_adcodes=[]; day_district_names=[]
    day_anchor_lats=[]; day_anchor_lons=[]; day_min_ratings=[]; day_budgets=[]

    if ndays <= 7:
        tabs = st.tabs([f"D{d+1}" for d in range(ndays)])
        for d_idx, tab in enumerate(tabs):
            with tab:
                d_sel=st.selectbox(_t("area_label",LANG),per_day_opts,key=f"da_{d_idx}",label_visibility="collapsed")
                auto=(d_sel=="Auto (city-wide)")
                if auto:
                    day_adcodes.append(""); day_district_names.append("")
                    day_anchor_lats.append(city_lat); day_anchor_lons.append(city_lon)
                else:
                    day_adcodes.append(adcode_map.get(d_sel,"")); day_district_names.append(d_sel)
                    if d_sel in center_map: dlat,dlon=center_map[d_sel]
                    else: dlat,dlon=city_lat,city_lon
                    day_anchor_lats.append(dlat); day_anchor_lons.append(dlon)
                min_r=st.slider(_t("min_rating_label",LANG),0.0,5.0,3.5,0.5,key=f"mr_{d_idx}")
                day_min_ratings.append(min_r)
                d_usd=st.slider(_t("daily_budget_label",LANG),min_value=10,max_value=500,value=60,step=5,format="$%d",key=f"bud_{d_idx}")
                _cr=fmt_currency_row(d_usd,country)
                _lp=_cr.split("≈",1)[-1].strip() if "≈" in _cr else ""
                st.markdown(
                    f'<div class="budget-pill">${d_usd}/day'+
                    (f'  ≈ {_lp}' if _lp else '')+f'</div>',
                    unsafe_allow_html=True,
                )
                day_budgets.append(d_usd)
                quota={}
                for tl in sel_types:
                    n=st.slider(tl,0,5,1,1,key=f"q_{d_idx}_{tl}")
                    if n>0: quota[tl]=n
                if not quota: quota={sel_types[0]:1}
                day_quotas.append(quota)
    else:
        d_sel=st.selectbox(_t("all_area_label",LANG),per_day_opts,key="da_all",label_visibility="collapsed")
        auto=(d_sel=="Auto (city-wide)")
        _adc="" if auto else adcode_map.get(d_sel,"")
        _dname="" if auto else d_sel
        if not auto and d_sel in center_map: _alat,_alon=center_map[d_sel]
        else: _alat,_alon=city_lat,city_lon
        day_adcodes=[_adc]*ndays; day_district_names=[_dname]*ndays
        day_anchor_lats=[_alat]*ndays; day_anchor_lons=[_alon]*ndays
        min_r=st.slider(_t("min_rating_label",LANG),0.0,5.0,3.5,0.5,key="mr_all")
        day_min_ratings=[min_r]*ndays
        _shared_usd=st.slider(_t("daily_budget_label",LANG),min_value=10,max_value=500,value=60,step=5,format="$%d",key="bud_all")
        _cr=fmt_currency_row(_shared_usd,country)
        _lp=_cr.split("≈",1)[-1].strip() if "≈" in _cr else ""
        st.markdown(
            f'<div class="budget-pill">${_shared_usd}/day'+
            (f'  ≈ {_lp}' if _lp else '')+f'</div>',
            unsafe_allow_html=True,
        )
        day_budgets=[_shared_usd]*ndays
        quota={}
        for tl in sel_types:
            n=st.slider(tl,0,5,1,1,key=f"qa_{tl}")
            if n>0: quota[tl]=n
        if not quota: quota={sel_types[0]:1}
        day_quotas=[dict(quota)]*ndays

    total_quota=sum(sum(q.values()) for q in day_quotas) if day_quotas else 4
    limit_per_type=max(30,total_quota*6)
    daily_usd=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    em,lb,lc,bgc=budget_level(daily_usd)

    st.markdown("---")
    if "seed" not in st.session_state: st.session_state.seed=42
    gen = st.button(_t("build_btn",LANG), use_container_width=True)
    ref = st.button(_t("refresh_btn",LANG), use_container_width=True)
    if ref:
        st.session_state.seed=random.randint(1,99999)
        st.cache_data.clear(); gen=True

    st.markdown("---")
    # Wishlist panel (if logged in)
    user = _current_user(LANG)
    if user and WISHLIST_OK:
        with st.expander(_t("wishlist_heading",LANG), expanded=False):
            render_wishlist_panel(user["username"], LANG)
    # Points panel (if logged in)
    if user and POINTS_OK:
        with st.expander(_t("points_heading",LANG), expanded=False):
            render_points_panel(user["username"], LANG)

    api_src = "高德地图 (Amap)" if is_cn else "Overpass OSM"
    st.markdown(f"{_t('data_source',LANG)}: {api_src}  ·  {_t('data_radius',LANG)}", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HERO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f'<div class="hero-box">'
    f'<h1>{_t("hero_title",LANG)}</h1>'
    f'<p>{_t("hero_subtitle",LANG)}</p>'
    f'</div>',
    unsafe_allow_html=True,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if gen:
    # Resolve coordinates
    if is_cn:
        lat, lon = city_lat, city_lon
        if lat is None:
            c = amap_geocode(city_input.strip())
            if c: lat, lon = c
            else: st.error(_t("err_city_not_found",LANG,city=city_input)); st.stop()
    elif intl_data:
        lat, lon = intl_data[0], intl_data[1]
    else:
        with st.spinner(_t("finding_dest",LANG)):
            coord = nominatim(city_input)
            if not coord: st.error(_t("err_city_not_found",LANG,city=city_input)); st.stop()
            lat, lon = coord

    hotel_c = depart_c = arrive_c = None
    with st.spinner(_t("looking_up_locations",LANG)):
        hotel_c  = geocode(hotel_addr,  city_input, is_cn) if hotel_addr  else None
        depart_c = geocode(depart_addr, city_input, is_cn) if depart_addr else None
        arrive_c = geocode(arrive_addr, city_input, is_cn) if arrive_addr else None

    area_label = city_input.title()
    with st.spinner(f"{_t('finding_places',LANG)} {area_label}…"):
        try:
            df, warn = fetch_all_places(
                lat, lon, country, is_cn, tuple(sel_types), limit_per_type,
                tuple(day_adcodes), tuple(day_district_names),
                tuple(day_anchor_lats), tuple(day_anchor_lons),
                st.session_state.seed,
            )
        except Exception as ex:
            st.error(f"Search error: {ex}"); st.stop()
    if warn: st.warning(warn)
    if df is None or df.empty:
        st.error(_t("err_no_places",LANG)); st.stop()

    itinerary = {}
    if not AI_OK:
        st.error(f"ai_planner import error: {_AI_ERR}")
    else:
        with st.spinner(_t("building_itin",LANG)):
            try:
                itinerary = generate_itinerary(
                    df, ndays, day_quotas,
                    hotel_lat=hotel_c[0] if hotel_c else None,
                    hotel_lon=hotel_c[1] if hotel_c else None,
                    depart_lat=depart_c[0] if depart_c else None,
                    depart_lon=depart_c[1] if depart_c else None,
                    arrive_lat=arrive_c[0] if arrive_c else None,
                    arrive_lon=arrive_c[1] if arrive_c else None,
                    day_min_ratings=day_min_ratings,
                    day_anchor_lats=day_anchor_lats,
                    day_anchor_lons=day_anchor_lons,
                    country=country,
                    city=city_input,
                    day_budgets=day_budgets,
                )
            except Exception as ex:
                st.error(_t("err_itinerary_failed",LANG,err=str(ex)))

    # Persist to session_state
    if itinerary:
        st.session_state.update({
            "_itin":itinerary,"_df":df,"_city":city_input,
            "_ndays":ndays,"_budgets":day_budgets,"_country":country,
            "_types":list(sel_types),"_lat":lat,"_lon":lon,
            "_hotel":hotel_c,"_depart":depart_c,"_arrive":arrive_c,"_lang":LANG,
        })
        # Auto-save for logged-in user
        user = _current_user(LANG)
        if user and WISHLIST_OK:
            try: save_itin_db(user["username"], itinerary, city_input, area_label)
            except Exception: pass
        if user and POINTS_OK:
            try: add_points(user["username"],"share",note=area_label)
            except Exception: pass

    # Metrics
    real = sum(len(v) for v in itinerary.values()) if itinerary else 0
    avg_r = df["rating"].replace(0,float("nan")).mean()
    total_budget_str = f"${sum(day_budgets)}" if len(set(day_budgets))>1 else f"${daily_usd}/day"
    for c, (lbl,val) in zip(st.columns(5),[
        (_t("metric_places",LANG),str(len(df))),
        (_t("metric_days",LANG),str(ndays)),
        (_t("metric_stops",LANG),str(real)),
        (_t("metric_rating",LANG),f"{avg_r:.1f}" if not math.isnan(avg_r) else "—"),
        (_t("metric_budget",LANG),total_budget_str),
    ]):
        c.metric(lbl,val)

    types_str=" + ".join(sel_types)
    st.markdown(f'<div class="sec-head">📋 {area_label}  ·  {types_str}</div>', unsafe_allow_html=True)
    render_table(df, itinerary, day_budgets, country, city_input, LANG)
    render_budget_summary(itinerary, day_budgets, country, ndays, LANG)

    # Transport comparison
    render_transport_details(itinerary, country, city_input, day_budgets, LANG)

    # Place swap
    if WISHLIST_OK:
        render_swap_panel(itinerary, df, LANG)

    # Map
    st.markdown(f'<div class="map-head">{_t("map_heading",LANG)}</div>', unsafe_allow_html=True)
    st.caption(_t("map_caption",LANG))
    try:
        m = build_map(df, lat, lon, itinerary, hotel_c, depart_c, arrive_c)
        st_folium(m, width="100%", height=560, returned_objects=[])
    except Exception as ex:
        st.error(_t("err_map_failed",LANG,err=str(ex)))

    # Collaboration
    render_collab_panel(LANG)

    # Export
    render_export_panel(itinerary, city_input, day_budgets, country, LANG)


elif "_itin" in st.session_state and "_df" in st.session_state:
    _it  = st.session_state["_itin"]
    _df  = st.session_state["_df"]
    _ci  = st.session_state.get("_city", city_input)
    _nd  = st.session_state.get("_ndays", ndays)
    _bud = st.session_state.get("_budgets", day_budgets)
    _ctr = st.session_state.get("_country", country)
    _tys = st.session_state.get("_types", list(sel_types))
    _lat = st.session_state.get("_lat", city_lat or 35.0)
    _lon = st.session_state.get("_lon", city_lon or 139.0)
    _hc  = st.session_state.get("_hotel")
    _dc  = st.session_state.get("_depart")
    _ac  = st.session_state.get("_arrive")
    _lg  = st.session_state.get("_lang", LANG)

    _real = sum(len(v) for v in _it.values()) if _it else 0
    _avg_r = _df["rating"].replace(0,float("nan")).mean()
    _du = round(sum(_bud)/len(_bud)) if _bud else 60
    _bstr = f"${sum(_bud)}" if len(set(_bud))>1 else f"${_du}/day"
    for c,(lbl,val) in zip(st.columns(5),[
        (_t("metric_places",_lg),str(len(_df))),
        (_t("metric_days",_lg),str(_nd)),
        (_t("metric_stops",_lg),str(_real)),
        (_t("metric_rating",_lg),f"{_avg_r:.1f}" if not math.isnan(_avg_r) else "—"),
        (_t("metric_budget",_lg),_bstr),
    ]):
        c.metric(lbl,val)

    _tstr=" + ".join(_tys)
    st.markdown(f'<div class="sec-head">📋 {_ci.title()}  ·  {_tstr}</div>', unsafe_allow_html=True)
    render_table(_df, _it, _bud, _ctr, _ci, _lg)
    render_budget_summary(_it, _bud, _ctr, _nd, _lg)
    render_transport_details(_it, _ctr, _ci, _bud, _lg)
    if WISHLIST_OK: render_swap_panel(_it, _df, _lg)
    st.markdown(f'<div class="map-head">{_t("map_heading",_lg)}</div>', unsafe_allow_html=True)
    st.caption(_t("map_caption",_lg))
    try:
        m = build_map(_df, _lat, _lon, _it, _hc, _dc, _ac)
        st_folium(m, width="100%", height=560, returned_objects=[])
    except Exception as ex:
        st.error(_t("err_map_failed",_lg,err=str(ex)))
    render_collab_panel(_lg)
    render_export_panel(_it, _ci, _bud, _ctr, _lg)


else:
    # Welcome state
    st.markdown("---")
    for col,(icon,title,desc) in zip(st.columns(4),[
        (_t("welcome_1_icon",LANG),_t("welcome_1_title",LANG),_t("welcome_1_desc",LANG)),
        (_t("welcome_2_icon",LANG),_t("welcome_2_title",LANG),_t("welcome_2_desc",LANG)),
        (_t("welcome_3_icon",LANG),_t("welcome_3_title",LANG),_t("welcome_3_desc",LANG)),
        (_t("welcome_4_icon",LANG),_t("welcome_4_title",LANG),_t("welcome_4_desc",LANG)),
    ]):
        with col:
            st.markdown(
                f'<div class="info-card">'
                f'<div class="ic-icon">{icon}</div>'
                f'<div class="ic-title">{title}</div>'
                f'<div class="ic-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
