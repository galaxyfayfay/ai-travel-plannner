"""
app.py v9 — AI Travel Planner Pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① "Where are you going" = City + Hotel/Start/End only (clean sidebar)
② Per-day quota & area: district (Amap adcode CN / static intl), min-rating, quota
③ Budget slider USD-base + live multi-currency row + CNY level gauge
④ CN districts via Amap /v3/config/district — real adcodes + centroids (session_state cached)
⑤ Triple Amap search strategy: keyword+type → type only → alt keywords
⑥ Geographic dedup (120m radius + name similarity)
⑦ Budget-aware cost estimates (place + transport) + daily over-budget alert
⑧ Table strictly ordered Day1#1 → Day1#2 → Day2#1 …
⑨ Map: single Marker popup + route mid-dots
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

try:
    from ai_planner import generate_itinerary
    AI_OK = True
except Exception as _imp_e:
    AI_OK = False
    _AI_ERR = str(_imp_e)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Outfit:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
.stApp{background:linear-gradient(150deg,#faf8f4 0%,#f2ebe0 50%,#ede4d6 100%);color:#2a1f12;}

/* hero */
.hero{text-align:center;padding:1.6rem 1rem .4rem;}
.hero-title{font-family:'Playfair Display',serif;font-size:2.55rem;font-weight:700;color:#1a1206;line-height:1.15;}
.hero-acc{background:linear-gradient(90deg,#a85820,#d4873a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hero-sub{color:#9a8470;font-size:.83rem;font-weight:300;letter-spacing:.15em;text-transform:uppercase;margin-top:.25rem;}

/* section titles */
.sec{font-family:'Playfair Display',serif;font-size:1.15rem;color:#1a1206;
     border-bottom:2px solid #e0cdb8;padding-bottom:.3rem;margin:1.4rem 0 .7rem;}

/* table */
.tt{width:100%;border-collapse:collapse;font-size:.79rem;}
.tt th{background:#f0e6d4;color:#5a3a18;font-weight:600;padding:.48rem .6rem;
       text-align:left;border-bottom:2px solid #d4b896;white-space:nowrap;}
.tt td{padding:.42rem .6rem;border-bottom:1px solid #ede0ce;vertical-align:top;line-height:1.52;}
.tt tr:hover td{background:#fffaf4;}
.day-sep td{background:linear-gradient(90deg,#f5e8d4,#faf6f0)!important;
            font-weight:700;color:#7a3a0e;font-size:.80rem;}
.day-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle;}
.sbadge{display:inline-flex;align-items:center;justify-content:center;
        width:18px;height:18px;border-radius:50%;font-size:.63rem;font-weight:700;
        color:#fff;vertical-align:middle;margin-right:3px;}
.rpill{display:inline-block;background:#f3ece0;border:1px solid #ddd0bc;color:#5c4228;
       border-radius:9px;padding:.04rem .42rem;font-size:.69rem;white-space:nowrap;}
.ttag{display:inline-block;background:#e8f4e8;border:1px solid #b8d8b8;color:#2a5a2a;
      border-radius:8px;padding:.02rem .36rem;font-size:.66rem;}
.rstar{color:#c97d35;font-weight:600;}
.desc-it{color:#8a7060;font-style:italic;font-size:.73rem;}
.addr-sm{color:#6a5540;font-size:.72rem;}
.cost-pill{font-size:.67rem;color:#8a5820;background:#fdf3e3;border:1px solid #e8d0b0;
           border-radius:7px;padding:.02rem .38rem;display:inline-block;margin-top:1px;}
.over-budget{font-size:.67rem;color:#c0392b;font-weight:600;}

/* budget gauge */
.bbar-wrap{background:#ede4d6;border-radius:7px;height:6px;margin:.3rem 0 .12rem;overflow:hidden;}
.bbar-fill{height:100%;border-radius:7px;}
.blabel-row{display:flex;justify-content:space-between;font-size:.63rem;color:#9a8470;}
.budget-main{font-size:.92rem;font-weight:600;color:#3a2914;}
.blevel{display:inline-block;border-radius:8px;padding:.07rem .48rem;
        font-size:.71rem;font-weight:600;margin-left:.3rem;vertical-align:middle;}
.currency-row{font-size:.73rem;color:#7a6040;margin-top:.1rem;}

/* sidebar */
[data-testid="stSidebar"]{background:#f5eddf!important;border-right:1px solid #ddd0bc;}
[data-testid="stSidebar"] label{color:#3a2914!important;}
[data-testid="stSidebar"] small,[data-testid="stSidebar"] p{color:#6a5540!important;}
[data-testid="stSidebar"] h3{color:#3a2914!important;}
[data-testid="stSidebar"] hr{border-color:#ddd0bc;}

/* section label in sidebar */
.sdiv{font-size:.78rem;font-weight:600;color:#7a3a0e;letter-spacing:.04em;
      text-transform:uppercase;margin:.6rem 0 .2rem;}

/* buttons */
.stButton>button{background:linear-gradient(90deg,#a85820,#d4873a)!important;
  color:#fff!important;font-weight:600!important;font-size:.88rem!important;
  border:none!important;border-radius:10px!important;
  padding:.46rem 1rem!important;width:100%!important;
  white-space:nowrap!important;transition:all .18s!important;}
.stButton>button:hover{filter:brightness(1.1)!important;transform:translateY(-1px)!important;}

/* metrics */
[data-testid="metric-container"]{background:#fffdf8!important;border:1px solid #e8d9c4!important;
  border-radius:10px!important;padding:.6rem .8rem!important;}
[data-testid="stMetricValue"]{color:#1a1206!important;font-weight:600!important;}
[data-testid="stMetricLabel"]{color:#6a5540!important;}

/* guide cards */
.gcard{background:#fffdf8;border:1px solid #e8d9c4;border-radius:12px;
       padding:1.1rem .9rem;text-align:center;}
.gcard-icon{font-size:1.65rem;margin-bottom:.25rem;}
.gcard-title{font-weight:600;color:#7a3a0e;font-size:.86rem;margin-bottom:.12rem;}
.gcard-desc{color:#9a8470;font-size:.73rem;}

/* budget summary cards */
.bsum-card{background:#fffdf8;border:1px solid #e8d9c4;border-radius:10px;
           padding:.65rem .85rem;margin:.3rem 0;text-align:center;}
.bsum-day{font-size:.78rem;color:#6a5540;margin-bottom:.12rem;}
.bsum-amt{font-size:1.15rem;font-weight:700;color:#3a2914;}
.bsum-level{font-size:.7rem;margin-top:.1rem;}
.bsum-over{color:#c0392b;font-weight:700;}

hr{border-color:#e8d9c4;}
</style>""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AMAP_KEY    = os.getenv("APIKEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEKKEY")

# ── Budget: USD base ─────────────────────────────────────────────────────────
# Thresholds in USD/day → (emoji, label, bar_color, badge_bg)
BUDGET_LEVELS_USD = [
    (0,   30,   "💚", "Economy",  "#2E7D32", "#e8f5e9"),
    (30,  80,   "💛", "Standard", "#B07020", "#fff8e1"),
    (80,  200,  "🧡", "Comfort",  "#C62828", "#fff3e0"),
    (200, 9999, "❤️", "Luxury",   "#6A1B9A", "#f3e5f5"),
]

def budget_level(usd: int):
    for lo, hi, em, lb, bc, bg in BUDGET_LEVELS_USD:
        if usd < hi:
            return em, lb, bc, bg
    return "❤️", "Luxury", "#6A1B9A", "#f3e5f5"

# USD → local currency conversions: country → [(code, symbol, rate_from_usd)]
CURRENCIES = {
    "CN":  [("USD","$",1.0), ("CNY","¥",7.25)],
    "JP":  [("USD","$",1.0), ("JPY","¥",155)],
    "KR":  [("USD","$",1.0), ("KRW","₩",1350)],
    "TH":  [("USD","$",1.0), ("THB","฿",36)],
    "SG":  [("USD","$",1.0), ("SGD","S$",1.35)],
    "FR":  [("USD","$",1.0), ("EUR","€",0.92)],
    "GB":  [("USD","$",1.0), ("GBP","£",0.79)],
    "IT":  [("USD","$",1.0), ("EUR","€",0.92)],
    "ES":  [("USD","$",1.0), ("EUR","€",0.92)],
    "US":  [("USD","$",1.0)],
    "AU":  [("USD","$",1.0), ("AUD","A$",1.53)],
    "AE":  [("USD","$",1.0), ("AED","AED",3.67)],
    "NL":  [("USD","$",1.0), ("EUR","€",0.92)],
    "TR":  [("USD","$",1.0), ("TRY","₺",32)],
    "HK":  [("USD","$",1.0), ("HKD","HK$",7.82)],
    "TW":  [("USD","$",1.0), ("TWD","NT$",32)],
    "ID":  [("USD","$",1.0), ("IDR","Rp",16000)],
    "VN":  [("USD","$",1.0), ("VND","₫",25000)],
    "MY":  [("USD","$",1.0), ("MYR","RM",4.7)],
    "INT": [("USD","$",1.0)],
}

def _local_rate(country: str):
    """Return (local_sym, local_rate_from_usd) for the primary local currency."""
    pairs = CURRENCIES.get(country, [("USD","$",1.0)])
    if len(pairs) > 1:
        return pairs[1][1], pairs[1][2]
    return pairs[0][1], pairs[0][2]

def fmt_currency_row(usd: int, country: str) -> str:
    """Build currency display row: $X/day  ≈  ¥Y CNY/day"""
    pairs = CURRENCIES.get(country, [("USD","$",1.0)])
    parts = [f"${usd}/day"]
    for code, sym, rate in pairs[1:]:  # skip USD (already shown)
        amt = round(usd * rate)
        if amt >= 10000:
            parts.append(f"{sym}{amt:,} {code}/day")
        else:
            parts.append(f"{sym}{amt} {code}/day")
    return "  ≈  ".join(parts)

# Cost weights by type (fraction of daily USD budget)
COST_W = {
    "🏛️ Attraction":   0.18,
    "🍜 Restaurant":    0.25,
    "☕ Café":           0.10,
    "🌿 Park":          0.04,
    "🛍️ Shopping":      0.22,
    "🍺 Bar/Nightlife": 0.16,
    "🏨 Hotel":          0.00,
    "Transport":         0.12,
}
# Floor costs in USD
COST_FLOOR_USD = {
    "🏛️ Attraction":   4,
    "🍜 Restaurant":    6,
    "☕ Café":           3,
    "🌿 Park":          0,
    "🛍️ Shopping":      8,
    "🍺 Bar/Nightlife": 5,
    "🏨 Hotel":          0,
    "Transport":         1,
}

def cost_estimate(type_label: str, daily_usd: int, country: str):
    """Return (mid_usd, display_str) for a single place visit."""
    w = COST_W.get(type_label, 0.12)
    floor = COST_FLOOR_USD.get(type_label, 2)
    per_visit_usd = max(floor, daily_usd * w / 2)
    lo_usd = per_visit_usd * 0.65
    hi_usd = per_visit_usd * 1.45
    mid_usd = (lo_usd + hi_usd) / 2
    sym, rate = _local_rate(country)
    lo_l = round(lo_usd * rate)
    hi_l = round(hi_usd * rate)
    lo_u = round(lo_usd)
    hi_u = round(hi_usd)
    if country == "US":
        return mid_usd, f"${lo_u}–${hi_u}"
    return mid_usd, f"${lo_u}–${hi_u}  ({sym}{lo_l}–{sym}{hi_l})"

def transport_cost_estimate(dist_km: float, daily_usd: int, country: str):
    """Return (mid_usd, display_str) for a transport leg."""
    w = COST_W["Transport"]
    floor = COST_FLOOR_USD["Transport"]
    base = max(floor, daily_usd * w / 5)
    factor = max(1.0, dist_km / 3.0)
    lo_usd = base * factor * 0.7
    hi_usd = base * factor * 1.4
    mid_usd = (lo_usd + hi_usd) / 2
    sym, rate = _local_rate(country)
    lo_l = round(lo_usd * rate)
    hi_l = round(hi_usd * rate)
    lo_u = round(lo_usd)
    hi_u = round(hi_usd)
    if country == "US":
        return mid_usd, f"${lo_u}–${hi_u}"
    return mid_usd, f"${lo_u}–${hi_u}  ({sym}{lo_l}–{sym}{hi_l})"

# CN city coords
CN_CITIES = {
    "beijing":    (39.9042, 116.4074),
    "shanghai":   (31.2304, 121.4737),
    "guangzhou":  (23.1291, 113.2644),
    "shenzhen":   (22.5431, 114.0579),
    "chengdu":    (30.5728, 104.0668),
    "hangzhou":   (30.2741, 120.1551),
    "xian":       (34.3416, 108.9398),
    "xi'an":      (34.3416, 108.9398),
    "chongqing":  (29.5630, 106.5516),
    "nanjing":    (32.0603, 118.7969),
    "wuhan":      (30.5928, 114.3055),
    "suzhou":     (31.2990, 120.5853),
    "tianjin":    (39.3434, 117.3616),
    "qingdao":    (36.0671, 120.3826),
    "xiamen":     (24.4798, 118.0894),
    "zhengzhou":  (34.7466, 113.6254),
    "chengzhou":  (28.2278, 112.9388),
    "changsha":   (28.2278, 112.9388),
    "kunming":    (25.0453, 102.7097),
    "sanya":      (18.2526, 109.5119),
}

# International city data: (lat, lon, country, [districts])
INTL_CITIES = {
    "tokyo":          (35.6762, 139.6503, "JP", ["Shinjuku","Shibuya","Asakusa","Harajuku","Ginza","Akihabara","Ueno","Roppongi"]),
    "osaka":          (34.6937, 135.5023, "JP", ["Dotonbori","Namba","Umeda","Shinsekai","Tenoji","Shinsaibashi"]),
    "kyoto":          (35.0116, 135.7681, "JP", ["Gion","Arashiyama","Higashiyama","Fushimi","Nishiki"]),
    "seoul":          (37.5665, 126.9780, "KR", ["Gangnam","Hongdae","Myeongdong","Itaewon","Insadong","Bukchon"]),
    "bangkok":        (13.7563, 100.5018, "TH", ["Sukhumvit","Silom","Rattanakosin","Chatuchak","Ari"]),
    "singapore":      (1.3521,  103.8198, "SG", ["Marina Bay","Clarke Quay","Orchard","Chinatown","Little India","Bugis"]),
    "paris":          (48.8566,   2.3522, "FR", ["Le Marais","Montmartre","Saint-Germain","Champs-Élysées","Bastille"]),
    "london":         (51.5072,  -0.1276, "GB", ["Soho","Covent Garden","Shoreditch","South Bank","Notting Hill","Camden"]),
    "rome":           (41.9028,  12.4964, "IT", ["Trastevere","Campo de' Fiori","Prati","Testaccio","Vatican"]),
    "barcelona":      (41.3851,   2.1734, "ES", ["Gothic Quarter","Eixample","Gracia","El Born","Barceloneta"]),
    "new york":       (40.7128, -74.0060, "US", ["Manhattan","Brooklyn","SoHo","Greenwich Village","Midtown","Williamsburg"]),
    "new york city":  (40.7128, -74.0060, "US", ["Manhattan","Brooklyn","SoHo","Greenwich Village","Midtown"]),
    "sydney":         (-33.8688,151.2093, "AU", ["Circular Quay","Surry Hills","Newtown","Bondi","Glebe"]),
    "dubai":          (25.2048,  55.2708, "AE", ["Downtown","Dubai Marina","Deira","JBR","DIFC"]),
    "amsterdam":      (52.3676,   4.9041, "NL", ["Jordaan","De Pijp","Centrum","Oud-West","Oost"]),
    "istanbul":       (41.0082,  28.9784, "TR", ["Beyoglu","Sultanahmet","Besiktas","Kadikoy","Uskudar"]),
    "hong kong":      (22.3193, 114.1694, "HK", ["Central","Tsim Sha Tsui","Mong Kok","Causeway Bay","Wan Chai"]),
    "taipei":         (25.0330, 121.5654, "TW", ["Daan","Xinyi","Zhongzheng","Shilin","Ximending"]),
    "bali":           (-8.3405, 115.0920, "ID", ["Seminyak","Ubud","Canggu","Kuta","Sanur","Uluwatu"]),
    "ho chi minh city":(10.7769,106.7009, "VN", ["District 1","District 3","Bui Vien","Ben Thanh"]),
    "kuala lumpur":   (3.1390,  101.6869, "MY", ["KLCC","Bukit Bintang","Bangsar","Chow Kit"]),
}

PTYPES = {
    "🏛️ Attraction":   {"cn":"景点",   "osm":("tourism","attraction"), "amap":"110000","emoji":"🏛️","color":"#3a8fd4"},
    "🍜 Restaurant":    {"cn":"餐厅",   "osm":("amenity","restaurant"), "amap":"050000","emoji":"🍜","color":"#c97d35"},
    "☕ Café":           {"cn":"咖啡馆", "osm":("amenity","cafe"),       "amap":"050500","emoji":"☕","color":"#7a5c3a"},
    "🌿 Park":          {"cn":"公园",   "osm":("leisure","park"),        "amap":"110101","emoji":"🌿","color":"#3aaa7a"},
    "🛍️ Shopping":      {"cn":"购物",   "osm":("shop","mall"),           "amap":"060000","emoji":"🛍️","color":"#9b59b6"},
    "🍺 Bar/Nightlife": {"cn":"酒吧",   "osm":("amenity","bar"),         "amap":"050600","emoji":"🍺","color":"#e05c3a"},
    "🏨 Hotel":          {"cn":"酒店",   "osm":("tourism","hotel"),       "amap":"100000","emoji":"🏨","color":"#1abc9c"},
}

# Alternate CN keywords to broaden Amap search
AMAP_ALT = {
    "🏛️ Attraction":   ["旅游景点","博物馆","历史","游览"],
    "🍜 Restaurant":    ["餐馆","美食","饭店","特色菜"],
    "☕ Café":           ["咖啡","下午茶","cafe"],
    "🌿 Park":          ["公园","花园","绿地","广场"],
    "🛍️ Shopping":      ["商场","购物中心","超市","市集"],
    "🍺 Bar/Nightlife": ["酒吧","KTV","夜店","清吧"],
    "🏨 Hotel":          ["酒店","宾馆","民宿","客栈"],
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

# ── Geographic deduplication ──────────────────────────────────────────────────
def _hav_m(lat1, lon1, lat2, lon2):
    R = 6371000
    dl = math.radians(lat2 - lat1); dg = math.radians(lon2 - lon1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dg/2)**2
    return R * 2 * math.asin(math.sqrt(min(1.0, a)))

def _name_sim(a: str, b: str) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    if a == b: return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return len(shorter) >= 3 and shorter in longer

def geo_dedup(places: list, radius_m: float = 120.0) -> list:
    """Merge nearby duplicates, keeping the highest-rated version."""
    if not places: return []
    merged = [False] * len(places)
    kept = []
    for i, p in enumerate(places):
        if merged[i]: continue
        best = p
        for j in range(i + 1, len(places)):
            if merged[j]: continue
            dist = _hav_m(best["lat"], best["lon"], places[j]["lat"], places[j]["lon"])
            if dist < 50 or (dist < radius_m and _name_sim(best["name"], places[j]["name"])):
                merged[j] = True
                if places[j]["rating"] > best["rating"]:
                    best = places[j]
        kept.append(best)
    return kept

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AMAP DISTRICT LOADING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600, show_spinner=False)
def amap_get_districts(city_name: str) -> list:
    """Fetch sub-district list for a CN city via Amap /v3/config/district.
    Returns [{"name","adcode","lat","lon"}, ...] or [] on failure."""
    if not city_name.strip():
        return []
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/config/district",
            params={"key": AMAP_KEY, "keywords": city_name,
                    "subdistrict": 1, "extensions": "base", "output": "json"},
            timeout=9,
        )
        data = r.json()
        if str(data.get("status")) != "1":
            return []
        tops = data.get("districts", [])
        if not tops:
            return []
        result = []
        for d in tops[0].get("districts", []):
            name   = (d.get("name")   or "").strip()
            adcode = (d.get("adcode") or "").strip()
            center = (d.get("center") or "").strip()
            if not (name and adcode):
                continue
            lat = lon = None
            if "," in center:
                try:
                    lon, lat = map(float, center.split(","))
                except Exception:
                    pass
            result.append({"name": name, "adcode": adcode, "lat": lat, "lon": lon})
        return result
    except Exception:
        return []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GEOCODING HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600, show_spinner=False)
def amap_geocode(address: str):
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"key": AMAP_KEY, "address": address, "output": "json"},
            timeout=8,
        )
        data = r.json()
        if str(data.get("status")) == "1" and data.get("geocodes"):
            loc = data["geocodes"][0].get("location", "")
            if "," in loc:
                lon, lat = map(float, loc.split(","))
                return lat, lon
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def nominatim(q: str):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers={"User-Agent": "TravelPlannerPro/8"},
            timeout=9,
        ).json()
        if r:
            return float(r[0]["lat"]), float(r[0]["lon"])
    except Exception:
        pass
    return None

def geocode(addr: str, city: str, is_cn: bool):
    if not addr.strip():
        return None
    if is_cn:
        return amap_geocode(f"{addr} {city}") or nominatim(f"{addr} {city}")
    return nominatim(f"{addr} {city}") or nominatim(addr)

# ── World city database for cascading selector ──────────────────────────────
WORLD_CITIES = {
    # China
    "China": ["Beijing","Shanghai","Guangzhou","Shenzhen","Chengdu","Hangzhou",
               "Xi'an","Chongqing","Nanjing","Wuhan","Suzhou","Tianjin",
               "Qingdao","Xiamen","Kunming","Sanya","Changsha","Zhengzhou"],
    # Japan
    "Japan": ["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya",
              "Hiroshima","Nara","Yokohama","Kobe","Okinawa","Hakone"],
    # South Korea
    "South Korea": ["Seoul","Busan","Incheon","Jeju","Daegu","Gwangju","Daejeon"],
    # Southeast Asia
    "Thailand": ["Bangkok","Chiang Mai","Phuket","Pattaya","Hua Hin","Koh Samui"],
    "Vietnam": ["Ho Chi Minh City","Hanoi","Da Nang","Hoi An","Nha Trang","Hue"],
    "Indonesia": ["Bali","Jakarta","Yogyakarta","Lombok","Labuan Bajo","Medan"],
    "Malaysia": ["Kuala Lumpur","Penang","Malacca","Kota Kinabalu","Langkawi","Johor Bahru"],
    "Singapore": ["Singapore"],
    "Philippines": ["Manila","Cebu","Boracay","Palawan","Davao","Bohol"],
    # South Asia
    "India": ["Mumbai","Delhi","Bangalore","Jaipur","Goa","Agra","Chennai","Kolkata","Varanasi"],
    "Nepal": ["Kathmandu","Pokhara","Chitwan","Lumbini"],
    # Middle East
    "UAE": ["Dubai","Abu Dhabi","Sharjah","Ajman"],
    "Turkey": ["Istanbul","Ankara","Cappadocia","Antalya","Bodrum","Izmir","Pamukkale"],
    "Israel": ["Jerusalem","Tel Aviv","Haifa","Eilat"],
    "Jordan": ["Amman","Petra","Wadi Rum","Aqaba"],
    # Europe
    "France": ["Paris","Lyon","Marseille","Nice","Bordeaux","Toulouse","Strasbourg","Mont Saint-Michel"],
    "Italy": ["Rome","Milan","Florence","Venice","Naples","Bologna","Turin","Amalfi","Cinque Terre","Siena"],
    "Spain": ["Barcelona","Madrid","Seville","Valencia","Granada","Bilbao","San Sebastian","Toledo","Cordoba"],
    "United Kingdom": ["London","Edinburgh","Manchester","Birmingham","Bath","Cambridge","Oxford","York","Bristol"],
    "Germany": ["Berlin","Munich","Hamburg","Frankfurt","Cologne","Dresden","Heidelberg","Rothenburg"],
    "Netherlands": ["Amsterdam","Rotterdam","Utrecht","The Hague","Bruges","Leiden"],
    "Switzerland": ["Zurich","Geneva","Bern","Lucerne","Interlaken","Zermatt"],
    "Austria": ["Vienna","Salzburg","Innsbruck","Hallstatt","Graz"],
    "Greece": ["Athens","Santorini","Mykonos","Crete","Rhodes","Thessaloniki","Corfu"],
    "Portugal": ["Lisbon","Porto","Algarve","Sintra","Evora","Madeira"],
    "Czech Republic": ["Prague","Brno","Cesky Krumlov","Karlovy Vary"],
    "Hungary": ["Budapest","Eger","Pecs"],
    "Poland": ["Warsaw","Krakow","Wroclaw","Gdansk","Poznan"],
    "Croatia": ["Dubrovnik","Split","Zagreb","Hvar","Zadar","Plitvice"],
    "Norway": ["Oslo","Bergen","Tromsø","Flam","Lofoten Islands"],
    "Sweden": ["Stockholm","Gothenburg","Malmo","Uppsala","Kiruna"],
    "Denmark": ["Copenhagen","Aarhus","Odense"],
    "Finland": ["Helsinki","Rovaniemi","Turku","Tampere"],
    "Iceland": ["Reykjavik","Akureyri","Vik","Selfoss"],
    "Russia": ["Moscow","St. Petersburg","Vladivostok","Kazan","Sochi"],
    # Americas
    "USA": ["New York","Los Angeles","Chicago","San Francisco","Miami","Boston",
             "Seattle","Las Vegas","New Orleans","Washington DC","Hawaii","Nashville"],
    "Canada": ["Toronto","Vancouver","Montreal","Quebec City","Banff","Calgary","Ottawa","Victoria"],
    "Mexico": ["Mexico City","Cancun","Playa del Carmen","Oaxaca","Guadalajara","San Miguel de Allende"],
    "Brazil": ["Rio de Janeiro","São Paulo","Salvador","Florianopolis","Iguazu Falls","Manaus"],
    "Argentina": ["Buenos Aires","Patagonia","Mendoza","Salta","Iguazu Falls","Bariloche"],
    "Peru": ["Lima","Cusco","Machu Picchu","Arequipa","Lake Titicaca"],
    "Colombia": ["Bogota","Cartagena","Medellin","Santa Marta","Cali"],
    # Oceania
    "Australia": ["Sydney","Melbourne","Brisbane","Perth","Adelaide","Cairns","Gold Coast","Darwin"],
    "New Zealand": ["Auckland","Queenstown","Wellington","Christchurch","Rotorua","Milford Sound"],
    # Africa
    "Morocco": ["Marrakech","Fes","Casablanca","Chefchaouen","Essaouira","Rabat"],
    "Egypt": ["Cairo","Luxor","Aswan","Alexandria","Hurghada","Sharm el-Sheikh"],
    "South Africa": ["Cape Town","Johannesburg","Durban","Kruger","Garden Route","Stellenbosch"],
    "Kenya": ["Nairobi","Mombasa","Masai Mara","Amboseli","Zanzibar"],
    # Hong Kong / Taiwan
    "Hong Kong": ["Hong Kong"],
    "Taiwan": ["Taipei","Tainan","Kaohsiung","Taichung","Hualien","Kenting"],
}

# Country → country code mapping
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

@st.cache_data(ttl=3600, show_spinner=False)
def get_nominatim_districts(city_name: str) -> list:
    """Fetch neighbourhood/district names for any city via Overpass."""
    if not city_name.strip():
        return []
    try:
        # Get city center
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city_name, "format": "json", "limit": 1},
            headers={"User-Agent": "TravelPlannerPro/11"}, timeout=8,
        ).json()
        if not r:
            return []
        lat, lon = float(r[0]["lat"]), float(r[0]["lon"])
        # Query Overpass for suburbs/neighbourhoods within 20km
        q = (f'[out:json][timeout:20];'
             f'(relation["place"~"suburb|neighbourhood|quarter|borough|district"]'
             f'(around:20000,{lat},{lon});'
             f'node["place"~"suburb|neighbourhood|quarter|borough"]'
             f'(around:20000,{lat},{lon}););out tags 30;')
        els = []
        for ov_url in ["https://overpass-api.de/api/interpreter",
                       "https://overpass.kumi.systems/api/interpreter"]:
            try:
                els = requests.post(ov_url, data={"data": q}, timeout=18).json().get("elements", [])
                if els: break
            except Exception:
                continue
        names = []
        for el in els:
            n = (el.get("tags", {}).get("name:en")
                 or el.get("tags", {}).get("name", ""))
            if n and n not in names and len(n) > 1:
                names.append(n)
        return sorted(names[:25])
    except Exception:
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLACE SEARCH — AMAP (CN)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _parse_amap_pois(pois, cn_kw, type_label, limit, seen):
    results = []
    for p in pois:
        if len(results) + len(seen) >= limit:
            break
        name = p.get("name", "")
        if not name or is_chain(name):
            continue
        loc = p.get("location", "")
        if "," not in (loc or ""):
            continue
        try:
            plon, plat = map(float, loc.split(","))
        except Exception:
            continue
        key = (name, round(plat, 4), round(plon, 4))
        if key in seen:
            continue
        seen.add(key)
        biz = p.get("biz_ext") or {}
        try:
            rating = float(biz.get("rating") or 0) or 0.0
        except Exception:
            rating = 0.0
        tel = biz.get("tel") or p.get("tel") or ""
        if isinstance(tel, list):
            tel = "; ".join(t for t in tel if t)
        addr = p.get("address") or ""
        if isinstance(addr, list):
            addr = "".join(addr)
        results.append({
            "name": name, "lat": plat, "lon": plon, "rating": rating,
            "address": str(addr).strip(), "phone": str(tel).strip(), "website": "",
            "type": cn_kw, "type_label": type_label,
            "district": p.get("adname") or "", "description": tdesc(cn_kw),
        })
    return results

def _amap_by_adcode(adcode: str, cn_kw: str, type_label: str, limit: int):
    """Triple-strategy Amap text search by district adcode."""
    places = []; seen = set()
    amap_type = PTYPES.get(type_label, {}).get("amap", "")
    last_err = None

    def _fetch_text(kw, types_code, page):
        params = {"key": AMAP_KEY, "keywords": kw, "city": adcode,
                  "citylimit": "true", "offset": 25, "page": page,
                  "extensions": "all", "output": "json"}
        if types_code:
            params["types"] = types_code
        r = requests.get("https://restapi.amap.com/v3/place/text",
                         params=params, timeout=10)
        return r.json()

    # Strategy 1: keyword + type code
    for page in range(1, 6):
        if len(places) >= limit: break
        try:
            data = _fetch_text(cn_kw, amap_type, page)
            if str(data.get("status")) != "1":
                last_err = f"code={data.get('infocode')} {data.get('info')}"; break
            pois = data.get("pois") or []
            if not pois: break
            places.extend(_parse_amap_pois(pois, cn_kw, type_label, limit, seen))
        except Exception as ex:
            last_err = str(ex); break

    # Strategy 2: type code only (broader)
    if len(places) < limit and amap_type:
        for page in range(1, 4):
            if len(places) >= limit: break
            try:
                data = _fetch_text("", amap_type, page)
                if str(data.get("status")) != "1": break
                pois = data.get("pois") or []
                if not pois: break
                places.extend(_parse_amap_pois(pois, cn_kw, type_label, limit, seen))
            except Exception:
                break

    # Strategy 3: alternate keywords
    if len(places) < limit:
        for alt_kw in AMAP_ALT.get(type_label, []):
            if alt_kw == cn_kw or len(places) >= limit: continue
            try:
                data = _fetch_text(alt_kw, amap_type, 1)
                if str(data.get("status")) != "1": continue
                pois = data.get("pois") or []
                places.extend(_parse_amap_pois(pois, alt_kw, type_label, limit, seen))
            except Exception:
                continue

    return places[:limit], last_err

def _amap_around(lat: float, lon: float, cn_kw: str, type_label: str, limit: int, radius: int = 8000):
    """Fallback: Amap around search by lat/lon."""
    places = []; errs = []; seen = set()
    amap_type = PTYPES.get(type_label, {}).get("amap", "")
    keywords_list = [cn_kw] + AMAP_ALT.get(type_label, [])
    for kw in keywords_list:
        if len(places) >= limit:
            break
        for page in range(1, 5):
            if len(places) >= limit:
                break
            try:
                params = {
                    "key": AMAP_KEY, "location": f"{lon},{lat}",
                    "radius": radius, "keywords": kw,
                    "offset": 25, "page": page, "extensions": "all", "output": "json",
                }
                if amap_type:
                    params["types"] = amap_type
                r = requests.get("https://restapi.amap.com/v3/place/around",
                                 params=params, timeout=10)
                data = r.json()
                if str(data.get("status")) != "1":
                    errs.append(f"code={data.get('infocode')} {data.get('info')}")
                    break
                pois = data.get("pois") or []
                if not pois:
                    break
                places.extend(_parse_amap_pois(pois, cn_kw, type_label, limit, seen))
            except Exception as ex:
                errs.append(str(ex)); break
    return places[:limit], (errs[0] if errs else None)

def search_cn(lat, lon, type_labels, limit_per_type, adcode="", district_name=""):
    all_p = []; errs = []
    for tl in type_labels:
        cn = PTYPES[tl]["cn"]
        if adcode:
            ps, e = _amap_by_adcode(adcode, cn, tl, limit_per_type)
        else:
            ps, e = _amap_around(lat, lon, cn, tl, limit_per_type)
        if e:
            errs.append(f"{tl}: {e}")
        all_p.extend(ps)
    # dedup
    seen, out = set(), []
    for p in all_p:
        k = (p["name"], round(p["lat"], 4), round(p["lon"], 4))
        if k not in seen:
            seen.add(k); out.append(p)
    return out, errs

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLACE SEARCH — OSM (International)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _osm_single(lat, lon, ok, ov, type_label, limit, district=""):
    clat, clon = lat, lon
    if district:
        try:
            g = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": district, "format": "json", "limit": 1},
                headers={"User-Agent": "TravelPlannerPro/8"}, timeout=5,
            ).json()
            if g:
                clat, clon = float(g[0]["lat"]), float(g[0]["lon"])
        except Exception:
            pass
    q = (f'[out:json][timeout:30];'
         f'(node["{ok}"="{ov}"](around:5000,{clat},{clon});'
         f'way["{ok}"="{ov}"](around:5000,{clat},{clon}););out center {limit * 4};')
    els = []
    for url in ["https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter"]:
        try:
            r = requests.post(url, data={"data": q}, timeout=28)
            els = r.json().get("elements", [])
            if els:
                break
        except Exception:
            continue
    places = []
    for el in els:
        tags = el.get("tags", {})
        name = tags.get("name:en") or tags.get("name") or ""
        if not name or is_chain(name):
            continue
        elat = (el.get("lat", 0) if el["type"] == "node"
                else el.get("center", {}).get("lat", 0))
        elon = (el.get("lon", 0) if el["type"] == "node"
                else el.get("center", {}).get("lon", 0))
        if not elat or not elon:
            continue
        parts = [tags.get(k, "") for k in
                 ["addr:housenumber", "addr:street", "addr:suburb", "addr:city"]
                 if tags.get(k)]
        places.append({
            "name": name, "lat": elat, "lon": elon,
            "rating": round(random.uniform(3.8, 5.0), 1),
            "address": ", ".join(parts),
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "website": tags.get("website") or tags.get("contact:website") or "",
            "type": ov, "type_label": type_label,
            "district": tags.get("addr:suburb") or tags.get("addr:city") or "",
            "description": tdesc(ov),
        })
        if len(places) >= limit:
            break
    return places

def search_intl(lat, lon, type_labels, limit_per_type, district=""):
    all_p = []
    for tl in type_labels:
        ok, ov = PTYPES[tl]["osm"]
        all_p.extend(_osm_single(lat, lon, ok, ov, tl, limit_per_type, district))
    seen, out = set(), []
    for p in all_p:
        k = (p["name"], round(p["lat"], 3), round(p["lon"], 3))
        if k not in seen:
            seen.add(k); out.append(p)
    return out

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEMO DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def demo_places(lat, lon, type_labels, n_per_type, seed, district=""):
    random.seed(seed)
    NAMES = {
        "🏛️ Attraction":   ["Grand Museum","Sky Tower","Ancient Temple","Art Gallery",
                             "Historic Castle","Night Market","Cultural Center",
                             "Scenic Viewpoint","Old Town Square","Waterfront Walk"],
        "🍜 Restaurant":    ["Sakura Dining","Ramen House","Sushi Master","Hot Pot Garden",
                             "Yakitori Bar","Noodle King","Dim Sum Palace",
                             "Street Food Alley","Rooftop Kitchen","Harbour Grill"],
        "☕ Café":           ["Blue Bottle","Artisan Brew","Matcha Corner","Loft Coffee",
                             "Roast & Toast","Morning Pour","Bean & Book","The Cozy Cup"],
        "🌿 Park":          ["Riverside Park","Sakura Garden","Central Park",
                             "Bamboo Grove","Zen Garden","Hilltop Reserve"],
        "🛍️ Shopping":      ["Central Mall","Night Bazaar","Vintage Market",
                             "Designer District","Flea Market"],
        "🍺 Bar/Nightlife": ["Rooftop Bar","Jazz Lounge","Craft Beer Hall",
                             "Cocktail Garden","Night Club"],
        "🏨 Hotel":          ["Grand Palace Hotel","Boutique Inn",
                             "City View Hotel","Zen Retreat"],
    }
    DNAMES = ["North Area", "Central Area", "South Area"]
    centers = [
        (lat + random.uniform(-.022, .022), lon + random.uniform(-.022, .022))
        for _ in range(min(3, max(1, len(type_labels))))
    ]
    result = []
    for tl in type_labels:
        names = list(NAMES.get(tl, ["Local Spot"]))
        random.shuffle(names)
        for i, name in enumerate(names[:n_per_type]):
            ci = i % len(centers)
            clat, clon = centers[ci]
            result.append({
                "name": name,
                "lat": round(clat + random.uniform(-.006, .006), 5),
                "lon": round(clon + random.uniform(-.006, .006), 5),
                "rating": round(random.uniform(4.0, 4.9), 1),
                "address": "Preview mode — connect to the internet for real addresses",
                "phone": "", "website": "",
                "type": PTYPES[tl]["cn"] if tl in PTYPES else tl,
                "type_label": tl,
                "district": district or DNAMES[ci % len(DNAMES)],
                "description": tdesc(tl),
            })
    return result

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGGREGATE SEARCH (all days combined, deduped)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=180, show_spinner=False)
def fetch_all_places(city_lat, city_lon, country, is_cn,
                     type_labels_t, limit_per_type,
                     day_adcodes_t, day_district_names_t,
                     day_anchor_lats_t, day_anchor_lons_t,
                     _seed):
    """Fetch places for all day-district combos, deduplicated."""
    random.seed(_seed)
    tls = list(type_labels_t)
    all_raw = []
    warn_msg = None
    all_api_errs = []

    seen_adcodes = set()
    for d_idx in range(len(day_adcodes_t)):
        adc  = day_adcodes_t[d_idx]
        dname = day_district_names_t[d_idx]
        dlat = day_anchor_lats_t[d_idx] if day_anchor_lats_t[d_idx] is not None else city_lat
        dlon = day_anchor_lons_t[d_idx] if day_anchor_lons_t[d_idx] is not None else city_lon

        # Skip duplicate adcodes
        combo_key = adc or f"latlon_{round(dlat,3)}_{round(dlon,3)}"
        if combo_key in seen_adcodes:
            continue
        seen_adcodes.add(combo_key)

        if is_cn:
            ps, errs = search_cn(dlat, dlon, tls, limit_per_type, adc, dname)
            all_api_errs.extend(errs)
        else:
            ps = search_intl(dlat, dlon, tls, limit_per_type, dname)
        all_raw.extend(ps)

    # Global dedup — first key-based, then geo-proximity
    seen, out = set(), []
    for p in all_raw:
        k = (p["name"], round(p["lat"], 4), round(p["lon"], 4))
        if k not in seen:
            seen.add(k); out.append(p)
    out = geo_dedup(out)

    # Fallback to demo
    if not out:
        out = demo_places(city_lat, city_lon, tls, limit_per_type, _seed)
        if is_cn:
            if all_api_errs:
                sample_err = "; ".join(all_api_errs[:2])
                warn_msg = (
                    f"⚠️ **高德 API 无法返回数据**\n\n"
                    f"错误：`{sample_err}`\n\n"
                    f"**Key 已内置**：`{AMAP_KEY}`\n\n"
                    "**排查步骤：**\n"
                    "1. 确认 Key 类型为 **Web 服务**（非 Android/iOS SDK）\n"
                    "2. 高德控制台 → 该 Key → 编辑 → **IP白名单完全清空** → 保存\n"
                    "3. 等 1 分钟后重试\n\n"
                    "当前显示演示数据。"
                )
            else:
                warn_msg = (
                    "⚠️ 高德 API 网络不可达（此服务器无法访问 restapi.amap.com）。\n\n"
                    f"**Key 已内置**：`{AMAP_KEY}`  ← 本机运行时正常使用。\n\n"
                    "当前显示演示数据。"
                )
        else:
            warn_msg = "⚠️ Couldn't fetch live data right now — showing sample places so you can try the app."

    df = pd.DataFrame(out)
    for col in ["address","phone","website","type","type_label","district","description"]:
        if col not in df.columns:
            df[col] = ""
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    df = df.sort_values("rating", ascending=False).reset_index(drop=True)
    return df, warn_msg

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

    # Route lines + mid-dot popups
    if itinerary:
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            if len(stops) < 2:
                continue
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
                    f"<div style='font-family:sans-serif;padding:5px;min-width:180px'>"
                    f"<b style='color:#5a3a18'>{dl} · Leg {si+1}</b><br>"
                    f"<span style='font-size:13px'>{tr.get('mode','—')}</span><br>"
                    f"<span style='color:#555;font-size:11px'>"
                    f"⏱ {tr.get('duration','—')} · 📏 {tr.get('distance_km','—')} km</span><br>"
                    f"<span style='color:#aaa;font-size:10px'>{a['name']} → {b['name']}</span></div>"
                )
                folium.Marker(
                    mid,
                    popup=folium.Popup(pt, max_width=210),
                    tooltip="🚦 Travel to next stop",
                    icon=folium.DivIcon(
                        html=(f'<div style="width:9px;height:9px;background:{dc};'
                              f'border:2px solid white;border-radius:50%;cursor:pointer;'
                              f'box-shadow:0 1px 3px rgba(0,0,0,.3)"></div>'),
                        icon_size=(9, 9), icon_anchor=(4, 4),
                    ),
                ).add_to(m)

    # Place markers — single Marker with popup (click the numbered circle)
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
        addr_h = (f"<div style='font-size:11px;color:#666;margin-top:2px'>📍 {addr[:60]}</div>"
                  if addr and "demo" not in addr.lower() else "")
        ph_h = (f"<div style='font-size:11px;color:#666'>📞 {row['phone']}</div>"
                if row.get("phone") else "")
        dist_h = (f"<div style='font-size:10px;color:#999'>📌 {row.get('district','')}</div>"
                  if row.get("district") else "")

        popup_html = (
            f"<div style='font-family:Outfit,sans-serif;min-width:190px;max-width:240px;padding:4px 2px'>"
            f"<div style='font-size:13px;font-weight:700;color:#1a1206'>{row['name']}</div>"
            f"<div style='margin:3px 0'>"
            f"<span style='color:#c97d35;font-size:12px'>⭐ {row['rating']:.1f}</span>"
            f"&nbsp;<span style='font-size:11px;color:{color};font-weight:600'>{day_info}</span></div>"
            f"{dist_h}{addr_h}{ph_h}</div>"
        )
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{day_info} — {row['name']}",
            icon=folium.DivIcon(
                html=(f'<div style="font-size:11px;font-weight:700;color:#fff;background:{color};'
                      f'border-radius:50%;width:22px;height:22px;line-height:22px;'
                      f'text-align:center;cursor:pointer;'
                      f'box-shadow:0 2px 6px rgba(0,0,0,.35);'
                      f'border:2px solid rgba(255,255,255,.8)">{label}</div>'),
                icon_size=(22, 22), icon_anchor=(11, 11),
            ),
        ).add_to(m)

    # Special location markers
    def smark(coords, icon_char, tip):
        folium.Marker(
            list(coords), tooltip=tip,
            icon=folium.DivIcon(
                html=(f'<div style="font-size:20px;line-height:30px;text-align:center;'
                      f'filter:drop-shadow(0 2px 3px rgba(0,0,0,.4))">{icon_char}</div>'),
                icon_size=(30, 30), icon_anchor=(15, 15),
            ),
        ).add_to(m)
    if hotel_c:  smark(hotel_c,  "🏨", "Your hotel")
    if depart_c: smark(depart_c, "🚩", "Starting Point")
    if arrive_c: smark(arrive_c, "🏁", "Final Departure")
    return m

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_table(df, itinerary, day_budgets, country):
    """Strictly ordered: Day1#1 → Day1#2 → Day2#1 …"""
    # day_budgets: list of USD budgets per day (or int for backward compat)
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

    rows_html = ""
    seq = 0
    cur_day = -1

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
                f'<tr class="day-sep"><td colspan="9" style="padding:.3rem .6rem">'
                f'<span class="day-dot" style="background:{color}"></span>'
                f'<b>Day {d_idx+1}</b> &nbsp;·&nbsp; {len(day_stops)} stops'
                f'&nbsp;<span class="blevel" style="background:{_bgc_d};color:{_lc_d};'
                f'font-size:.63rem;padding:.02rem .35rem">{_em_d} ${d_usd}/day</span>'
                f'</td></tr>'
            )
        _, _, sd = stop_map[name]
        rows_html += _trow(seq, row, d_idx + 1, stop_num, sd, color, d_usd, country)

    st.markdown(
        '<div style="overflow-x:auto;border-radius:12px;border:1px solid #e0cdb8;'
        'box-shadow:0 2px 8px rgba(0,0,0,.05)">'
        '<table class="tt"><thead><tr>'
        '<th style="width:24px">#</th>'
        '<th>Day / Stop</th>'
        '<th>Time</th>'
        '<th style="min-width:148px">Place</th>'
        '<th>District</th>'
        '<th>Type</th>'
        '<th>Rating</th>'
        '<th>Getting There</th>'
        '<th>Contact & Address</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )
    # 分类推荐（额外未排入行程的地点）
    if unscheduled:
        _render_extra_recommendations(unscheduled, day_budgets, country)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXTRA RECOMMENDATIONS (categorized, max 10, refreshable)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_extra_recommendations(unscheduled, day_budgets, country):
    avg_usd = round(sum(day_budgets) / len(day_budgets)) if day_budgets else 60

    # 定义分类及其包含的 type_label
    CATS = [
        ("🌿 自然风光 Nature",    ["🌿 Park"]),
        ("🏛️ 都市景点 Sights",    ["🏛️ Attraction"]),
        ("🍜 餐饮美食 Dining",     ["🍜 Restaurant", "☕ Café"]),
        ("🛍️ 购物 Shopping",      ["🛍️ Shopping"]),
        ("🍺 夜生活 Nightlife",    ["🍺 Bar/Nightlife"]),
        ("🏨 住宿 Hotels",         ["🏨 Hotel"]),
    ]

    # 将未排程地点按 type_label 分组
    by_type: dict = {}
    for row in unscheduled:
        tl = row.get("type_label","") or row.get("type","")
        by_type.setdefault(tl, []).append(row)

    # 按分类聚合
    cat_data = []
    covered  = set()
    for cat_name, type_list in CATS:
        items = []
        for tl in type_list:
            items.extend(by_type.get(tl, []))
            covered.add(tl)
        if items:
            cat_data.append((cat_name, items))
    # 剩余未归类
    others = [r for tl, rows in by_type.items() if tl not in covered for r in rows]
    if others:
        cat_data.append(("✨ 其他 Other", others))

    if not cat_data:
        return

    st.markdown('<div class="sec">💡 More Places You Might Like</div>', unsafe_allow_html=True)
    st.caption("These places didn't make it into your itinerary but are worth exploring. Hit 🔄 on any category to see different suggestions.")

    import random as _rnd
    for cat_name, places in cat_data:
        seed_key = f"_rec_{cat_name}"
        if seed_key not in st.session_state:
            st.session_state[seed_key] = 0

        col_h, col_b = st.columns([6, 1])
        with col_h:
            st.markdown(
                f'<div style="font-weight:700;font-size:.88rem;color:#3a2914;'
                f'margin:.7rem 0 .25rem;padding:.2rem .5rem;'
                f'border-left:3px solid #c97d35">{cat_name} '
                f'<span style="font-size:.72rem;color:#888;font-weight:400">'
                f'({min(10,len(places))} / {len(places)})</span></div>',
                unsafe_allow_html=True,
            )
        with col_b:
            if st.button("🔄", key=f"_rfbtn_{cat_name}", help="Show me different picks"):
                st.session_state[seed_key] = (st.session_state[seed_key] + 1) % 9999

        # 根据 seed 随机选 ≤10 条，然后按评分降序
        _rnd.seed(st.session_state[seed_key])
        pool  = list(places)
        picks = _rnd.sample(pool, min(10, len(pool)))
        picks.sort(key=lambda r: r.get("rating", 0), reverse=True)

        cards_html = ""
        for p in picks:
            name  = str(p.get("name",""))
            tl    = str(p.get("type_label","") or p.get("type",""))
            rat   = p.get("rating", 0)
            dist  = str(p.get("district","") or "—")
            addr  = str(p.get("address","") or "")[:55]
            phone = str(p.get("phone","") or "")
            _, cost_s = cost_estimate(tl, avg_usd, country)
            rat_s  = f"⭐ {rat:.1f}" if rat else "—"
            addr_s = f"📍 {addr}" if addr and "demo" not in addr.lower() else ""
            ph_s   = f"📞 {phone}" if phone else ""
            tl_clean = tl  # already "🏛️ Attraction" etc — no extra emoji needed
            cards_html += (
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
                f'padding:.4rem .6rem;border-bottom:1px solid #f0e4d0">'
                f'<div style="flex:1;min-width:0;margin-right:.5rem">'
                f'<div style="font-weight:600;font-size:.82rem;color:#1a1206;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{name}</div>'
                f'<div style="font-size:.70rem;color:#7a6040">{tl_clean} &nbsp;·&nbsp; {dist}</div>'
                + (f'<div style="font-size:.68rem;color:#9a8060">{addr_s}</div>' if addr_s else '')
                + (f'<div style="font-size:.68rem;color:#9a8060">{ph_s}</div>' if ph_s else '')
                + f'</div>'
                f'<div style="text-align:right;flex-shrink:0;min-width:72px">'
                f'<div style="font-size:.76rem;font-weight:700;color:#c97d35">{rat_s}</div>'
                f'<div style="font-size:.67rem;color:#a07040">💰 {cost_s}</div>'
                f'</div></div>'
            )

        st.markdown(
            '<div style="background:#fffdf8;border:1px solid #e8d4b8;border-radius:10px;'
            'overflow:hidden;margin-bottom:.5rem">' + cards_html + '</div>',
            unsafe_allow_html=True,
        )


def _trow(seq, row, day_n, stop_n, sd, color, daily_usd, country):
    bg = "#fffdf8" if seq % 2 == 0 else "#faf6ef"

    if day_n:
        dc = (f'<span class="sbadge" style="background:{color}">{stop_n}</span>'
              f'<span class="day-dot" style="background:{color}"></span><b>D{day_n}</b>')
        tc = sd.get("time_slot", "—") if sd else "—"
        tr = sd.get("transport_to_next") if sd else None
        if tr:
            dist_km = tr.get("distance_km", 0) or 0
            _, t_cost = transport_cost_estimate(dist_km, daily_usd, country)
            rc = (f'<span class="rpill">{tr["mode"]}</span><br>'
                  f'<span style="font-size:.68rem;color:#888">'
                  f'{tr["duration"]} · {dist_km} km</span><br>'
                  f'<span style="font-size:.63rem;color:#a07040">💸 {t_cost}</span>')
        else:
            etr = sd.get("end_transport") if sd else None
            if etr:
                rc = (f'<span class="rpill" style="background:#e8f4e8">{etr["mode"]}</span><br>'
                      f'<span style="font-size:.66rem;color:#3a8a3a">→ {etr.get("to_label","End")}</span>')
            else:
                rc = '<span style="color:#ccc;font-size:.70rem">Last stop of the day</span>'
    else:
        dc = '<span style="color:#ccc;font-size:.72rem">—</span>'
        tc = "—"
        rc = '<span style="color:#ccc;font-size:.70rem">—</span>'

    tl = row.get("type_label", "") or row.get("type", "")
    type_c = f'<span class="ttag">{tl}</span>' if tl and tl.lower() not in ("demo", "") else "—"

    r_val = row.get("rating", 0)
    rstr = f'<span class="rstar">⭐ {r_val:.1f}</span>' if r_val > 0 else "—"

    desc = row.get("description", "")
    # Cost estimate + over-budget warning
    cost_html = ""
    if day_n and daily_usd > 0 and tl:
        mid, cost_str = cost_estimate(tl, daily_usd, country)
        cost_html = f'<span class="cost-pill">💰 {cost_str}</span>'

    nc = (f'<b>{row["name"]}</b>'
          + (f'<div class="desc-it">{desc}</div>' if desc else "")
          + (f'<div style="margin-top:1px">{cost_html}</div>' if cost_html else ""))

    addr = str(row.get("address", ""))
    phone = str(row.get("phone", ""))
    ct = ""
    if addr and "demo" not in addr.lower():
        ct += f'<div class="addr-sm">📍 {addr[:55]}</div>'
    if phone:
        ct += f'<div class="addr-sm">📞 {phone}</div>'
    if not ct:
        ct = '<span style="color:#ccc;font-size:.70rem">—</span>'

    dist = row.get("district", "") or "—"

    return (
        f'<tr style="background:{bg}">'
        f'<td style="color:#bbb;text-align:center;font-size:.70rem">{seq}</td>'
        f'<td>{dc}</td>'
        f'<td style="color:#6a5540;white-space:nowrap;font-size:.76rem">{tc}</td>'
        f'<td>{nc}</td>'
        f'<td style="color:#6a5540;font-size:.76rem">{dist}</td>'
        f'<td>{type_c}</td>'
        f'<td style="text-align:center">{rstr}</td>'
        f'<td>{rc}</td>'
        f'<td>{ct}</td></tr>'
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUDGET SUMMARY PANEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_budget_summary(itinerary, day_budgets, country, days):
    if not itinerary:
        return
    if isinstance(day_budgets, int):
        day_budgets = [day_budgets] * days
    sym, rate = _local_rate(country)

    def _fmt(usd_amt, d_usd):
        lo_u = round(usd_amt * 0.8)
        hi_u = round(usd_amt * 1.2)
        if country == "US":
            return f"${lo_u}–${hi_u}"
        lo_l = round(lo_u * rate)
        hi_l = round(hi_u * rate)
        return f"${lo_u}–${hi_u}  ({sym}{lo_l}–{sym}{hi_l})"

    day_totals = []
    for d_idx, (dl, stops) in enumerate(itinerary.items()):
        if not stops: continue
        d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else day_budgets[-1]
        total_usd = 0.0
        for s in stops:
            tl = s.get("type_label", "")
            mid, _ = cost_estimate(tl, d_usd, country)
            total_usd += mid
            tr = s.get("transport_to_next") or {}
            if tr:
                dist_km = tr.get("distance_km", 0) or 0
                t_mid, _ = transport_cost_estimate(dist_km, d_usd, country)
                total_usd += t_mid
        day_totals.append((dl, total_usd, d_usd))

    if not day_totals:
        return

    st.markdown(
        '<div class="sec">💰 Cost Estimate <span style="font-size:.78rem;'
        'color:#9a8470;font-weight:400">(per person, including entry + transport)</span></div>',
        unsafe_allow_html=True,
    )

    grand_total = sum(t for _, t, _ in day_totals)
    grand_budget = sum(d for _, _, d in day_totals)
    n_cols = min(len(day_totals), 4) + 1
    cols = st.columns(n_cols)

    any_over = False
    for i, (dl, total_usd, d_usd) in enumerate(day_totals):
        with cols[i % (n_cols - 1)]:
            over = total_usd > d_usd * 1.1
            if over: any_over = True
            em, lb, lc, _ = budget_level(d_usd)
            amt_str = _fmt(total_usd, d_usd)
            over_str = " 🔴" if over else ""
            st.markdown(
                f'<div class="bsum-card">'
                f'<div class="bsum-day">{dl}</div>'
                f'<div class="bsum-amt{" bsum-over" if over else ""}">'
                f'${round(total_usd)}{over_str}</div>'
                f'<div style="font-size:.68rem;color:#7a6040;margin-top:2px">{amt_str}</div>'
                f'<div class="bsum-level">{em} {lb} · your budget ${d_usd}/day</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with cols[-1]:
        _lo = round(grand_total * 0.8)
        _hi = round(grand_total * 1.2)
        _lo_l = round(_lo * rate); _hi_l = round(_hi * rate)
        grand_str = (f"${_lo}–${_hi}" if country == "US"
                     else f"${_lo}–${_hi}  ({sym}{_lo_l}–{sym}{_hi_l})")
        st.markdown(
            f'<div class="bsum-card">'
            f'<div class="bsum-day">Total Est.</div>'
            f'<div class="bsum-amt">${round(grand_total)}</div>'
            f'<div style="font-size:.68rem;color:#7a6040;margin-top:2px">{grand_str}</div>'
            f'<div class="bsum-level">{days} days · total budget ${grand_budget}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if any_over:
        st.markdown(
            '<div style="background:#fff3f3;border:1px solid #f5c6c6;border-radius:8px;'
            'padding:.55rem .85rem;margin:.4rem 0;font-size:.8rem;color:#c0392b">'
            '🔴 <b>A few days are over your budget.</b> Try reducing the number of stops, or pick an area '
            'where places are closer together to save on transport.</div>',
            unsafe_allow_html=True,
        )

    with st.expander("📊 See full cost breakdown"):
        rows = []
        for d_idx, (dl, stops) in enumerate(itinerary.items()):
            if not stops: continue
            d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else day_budgets[-1]
            for s in stops:
                tl = s.get("type_label", "")
                _, cost_rng = cost_estimate(tl, d_usd, country)
                rows.append({"Day": dl, "Place": s.get("name", ""),
                             "Type": tl, "Budget": f"${d_usd}/day",
                             "Est. Cost/person": cost_rng})
                tr = s.get("transport_to_next") or {}
                if tr:
                    dk = tr.get("distance_km", 0) or 0
                    _, t_rng = transport_cost_estimate(dk, d_usd, country)
                    rows.append({"Day": dl,
                                 "Place": f"→ Transport ({tr.get('mode','')})",
                                 "Type": "Transport", "Budget": f"${d_usd}/day",
                                 "Est. Cost/person": t_rng})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF EXPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_pdf(itinerary: dict, city: str, day_budgets, country: str) -> bytes:
    """Generate self-contained HTML itinerary with embedded Leaflet map."""
    if isinstance(day_budgets, int):
        day_budgets = [day_budgets] * 30
    avg_usd      = round(sum(day_budgets) / len(day_budgets)) if day_budgets else 60
    total_budget = sum(day_budgets)
    DAY_COLS     = ["#c97d35","#3a8fd4","#3aaa7a","#9b59b6","#e05c3a","#1abc9c","#e91e63","#f39c12"]

    def clean(s):
        return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    total_stops = sum(len(v) for v in itinerary.values() if v)
    _, label, _, _ = budget_level(avg_usd)
    curr_str    = fmt_currency_row(avg_usd, country)

    # ── Build Leaflet marker + polyline data ──────────────────────────────
    all_marker_js   = []
    all_polyline_js = []
    map_lats = []; map_lons = []

    for d_idx, (day_label, stops) in enumerate(itinerary.items()):
        if not stops: continue
        col = DAY_COLS[d_idx % len(DAY_COLS)]
        poly_coords = []
        for si, s in enumerate(stops):
            lat = s.get("lat", 0); lon = s.get("lon", 0)
            if not lat or not lon: continue
            map_lats.append(lat); map_lons.append(lon)
            poly_coords.append(f"[{lat},{lon}]")
            nm  = (s.get("name","") or "").replace('"','\\"').replace("'","\\'")
            addr= (s.get("address","") or "")[:50].replace('"','\\"').replace("'","\\'")
            tsl = (s.get("time_slot","") or "").replace('"','\\"')
            all_marker_js.append(
                f'{{"lat":{lat},"lon":{lon},"n":"{nm}",'
                f'"d":{d_idx+1},"s":{si+1},"c":"{col}",'
                f'"a":"{addr}","t":"{tsl}"}}'
            )
        if len(poly_coords) > 1:
            all_polyline_js.append(f'{{"c":"{col}","pts":[{",".join(poly_coords)}]}}')

    clat = sum(map_lats)/len(map_lats) if map_lats else 35.0
    clon = sum(map_lons)/len(map_lons) if map_lons else 139.0
    markers_json   = "[" + ",".join(all_marker_js)   + "]"
    polylines_json = "[" + ",".join(all_polyline_js) + "]"

    # ── Build per-day HTML tables ─────────────────────────────────────────
    days_html = ""
    for d_idx, (day_label, stops) in enumerate(itinerary.items()):
        if not stops: continue
        d_usd = day_budgets[d_idx] if d_idx < len(day_budgets) else day_budgets[-1]
        col   = DAY_COLS[d_idx % len(DAY_COLS)]
        rows  = ""
        for si, s in enumerate(stops):
            tr    = s.get("transport_to_next") or {}
            route = f"{tr.get('mode','—')} · {tr.get('duration','')}" if tr else "Last stop"
            addr  = clean(s.get("address",""))
            phone = clean(s.get("phone",""))
            contact = ""
            if addr and "demo" not in addr.lower():
                contact += f"<div style='color:#6a5540;font-size:11px'>📍 {addr[:60]}</div>"
            if phone:
                contact += f"<div style='color:#6a5540;font-size:11px'>📞 {phone}</div>"
            tl   = clean(s.get("type_label",""))
            name = clean(s.get("name",""))
            ts   = clean(s.get("time_slot","—"))
            dist = clean(s.get("district","") or "—")
            rat  = s.get("rating", 0)
            rows += f"""<tr>
  <td style='text-align:center;color:#fff;background:{col};
      font-size:11px;font-weight:700;width:26px;min-width:26px'>{si+1}</td>
  <td style='color:#7a5a30;white-space:nowrap;font-size:12px'>{ts}</td>
  <td><b style='font-size:13px'>{name}</b>{contact}</td>
  <td style='font-size:11px;color:#5a4030'>{tl}</td>
  <td style='font-size:11px;color:#7a5a30'>{dist}</td>
  <td style='font-size:11px;color:#888'>{'⭐ '+str(rat) if rat else '—'}</td>
  <td style='font-size:11px;color:#5a5a5a'>{clean(route)}</td>
</tr>"""

        days_html += f"""
<div style='margin:20px 0 7px;border-left:4px solid {col};padding-left:10px'>
  <span style='font-size:15px;font-weight:700;color:{col}'>{clean(day_label)}</span>
  <span style='font-size:12px;color:#888;margin-left:8px'>{len(stops)} stops · budget ${d_usd}/day</span>
</div>
<table style='width:100%;border-collapse:collapse;font-size:12px;margin-bottom:10px'>
  <thead><tr style='background:#f5ede0'>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>#</th>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>Time</th>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>Place</th>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>Type</th>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>District</th>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>Rating</th>
    <th style='padding:5px 4px;font-size:11px;color:#a85820;border-bottom:1.5px solid #d4b896;text-align:left'>Route</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>"""

    # Legend HTML
    legend_items = ""
    for d_idx in range(min(len(itinerary), len(DAY_COLS))):
        col = DAY_COLS[d_idx % len(DAY_COLS)]
        legend_items += (f'<span style="display:inline-flex;align-items:center;gap:4px;'
                         f'margin-right:12px;font-size:11px">'
                         f'<span style="width:12px;height:12px;border-radius:50%;'
                         f'background:{col};display:inline-block"></span>Day {d_idx+1}</span>')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Itinerary — {clean(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  body{{font-family:Arial,sans-serif;color:#2a1f12;margin:0;background:#fff}}
  .page{{max-width:960px;margin:0 auto;padding:24px 28px}}
  h1{{color:#a85820;font-size:22px;margin-bottom:4px}}
  .sub{{color:#6a5540;font-size:13px;margin-bottom:14px}}
  table td{{padding:5px 4px;border-bottom:1px solid #ede0ce;vertical-align:top}}
  #map{{width:100%;height:420px;border-radius:10px;border:1.5px solid #d4b896;
        margin-bottom:22px;z-index:1}}
  .legend{{margin:8px 0 18px;padding:6px 10px;background:#faf6ef;
           border-radius:6px;border:1px solid #e8d9c4}}
  @media print{{
    body{{margin:0}}
    #map{{display:none!important}}
    .no-print{{display:none}}
    table{{page-break-inside:auto}}
    tr{{page-break-inside:avoid}}
  }}
</style>
</head>
<body>
<div class="page">
<h1>✈ Travel Itinerary — {clean(city.title())}</h1>
<div class="sub">
  Total budget: <b>${total_budget}</b> ({len([b for b in day_budgets if b])} days) &nbsp;·&nbsp;
  {total_stops} stops &nbsp;·&nbsp; avg ${avg_usd}/day &nbsp;·&nbsp; {label}
  &nbsp;·&nbsp; {clean(curr_str).replace(str(avg_usd)+"/day","avg/day")}
</div>
<hr style='border:none;border-top:2px solid #a85820;margin-bottom:16px'>

<div id="map"></div>
<div class="legend">{legend_items}</div>

{days_html}

<hr style='border:none;border-top:1px solid #ccc;margin-top:24px'>
<p style='color:#999;font-size:10px;text-align:center'>
  Generated by Trip Planner &nbsp;·&nbsp; Map: Leaflet + CartoDB Voyager &nbsp;·&nbsp;
  Cost estimates are approximate and for guidance only.<br>
  <span class='no-print'>💡 To save as PDF: press Ctrl+P (Windows) or ⌘P (Mac), then choose "Save as PDF"</span>
</p>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function(){{
  var markers   = {markers_json};
  var polylines = {polylines_json};

  var map = L.map('map', {{zoomControl:true}}).setView([{clat},{clon}], 13);
  L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{attribution:'&copy; OpenStreetMap contributors', maxZoom:19}}).addTo(map);

  // Draw route polylines first (under markers)
  polylines.forEach(function(pl) {{
    L.polyline(pl.pts, {{color:pl.c, weight:3, opacity:0.75, dashArray:'7,4'}}).addTo(map);
  }});

  // Draw stop markers
  var bounds = [];
  markers.forEach(function(m) {{
    var icon = L.divIcon({{
      className: '',
      html: '<div style="background:'+m.c+';color:#fff;font-size:11px;font-weight:700;'
          + 'width:26px;height:26px;border-radius:50%;line-height:26px;text-align:center;'
          + 'box-shadow:0 2px 7px rgba(0,0,0,.45);border:2px solid rgba(255,255,255,.9)">'
          + m.s + '</div>',
      iconSize: [26,26], iconAnchor: [13,13]
    }});
    var popup = '<b>Day '+m.d+' · Stop '+m.s+'</b><br>'
              + '<b>'+m.n+'</b><br>'
              + (m.t ? '<span style="color:#888">'+m.t+'</span><br>' : '')
              + (m.a ? '<span style="font-size:11px;color:#6a5540">📍 '+m.a+'</span>' : '');
    L.marker([m.lat, m.lon], {{icon:icon}}).bindPopup(popup).addTo(map);
    bounds.push([m.lat, m.lon]);
  }});

  if (bounds.length > 0) {{
    map.fitBounds(L.latLngBounds(bounds).pad(0.18));
  }}
}})();
</script>
</body>
</html>"""
    return html.encode("utf-8")



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CALENDAR URL BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_calendar_urls(itinerary: dict, start_date_str: str, city: str) -> list[dict]:
    """
    Build Google Calendar 'Add event' URLs for each stop.
    Returns list of {day, stop, name, url}.
    """
    import urllib.parse
    from datetime import datetime, timedelta

    try:
        base_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except Exception:
        base_date = None

    # Time slot → (hour, minute)
    SLOT_MAP = {
        "9:00 AM":  (9, 0),  "10:30 AM": (10,30), "12:00 PM": (12, 0),
        "1:30 PM":  (13,30), "3:00 PM":  (15, 0), "4:30 PM":  (16,30),
        "6:00 PM":  (18, 0), "7:30 PM":  (19,30), "9:00 PM":  (21, 0),
    }

    results = []
    for d_idx, (day_label, stops) in enumerate(itinerary.items()):
        for si, s in enumerate(stops):
            name = s.get("name", "Stop")
            addr = s.get("address", "") or city
            tslot = s.get("time_slot", "9:00 AM")
            hh, mm = SLOT_MAP.get(tslot, (9, 0))

            if base_date:
                day_dt = base_date + timedelta(days=d_idx)
                start_dt = day_dt.replace(hour=hh, minute=mm, second=0)
                end_dt   = start_dt + timedelta(hours=1, minutes=30)
                fmt = "%Y%m%dT%H%M%S"
                dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
            else:
                dates_str = ""

            detail_parts = [f"📍 {city.title()} — {day_label} Stop {si+1}"]
            if s.get("type_label"):
                detail_parts.append(f"Type: {s['type_label']}")
            if s.get("phone"):
                detail_parts.append(f"📞 {s['phone']}")
            tr = s.get("transport_to_next") or {}
            if tr:
                detail_parts.append(f"Next: {tr.get('mode','')} {tr.get('duration','')}")

            params = {
                "action": "TEMPLATE",
                "text":   f"{name} ({city.title()})",
                "details": "\n".join(detail_parts),
                "location": addr[:100],
            }
            if dates_str:
                params["dates"] = dates_str

            url = "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)
            results.append({"day": day_label, "stop": si + 1, "name": name, "url": url})
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPORT PANEL (PDF download + Calendar URLs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_export_panel(itinerary: dict, city: str, day_budgets, country: str):
    if not itinerary or not any(itinerary.values()):
        return
    if isinstance(day_budgets, int):
        day_budgets = [day_budgets] * 30
    avg_usd = round(sum(day_budgets) / len(day_budgets)) if day_budgets else 60
    st.markdown('<div class="sec">📤 Save or Share Your Trip</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("**📄 Download as a file (open in browser → print to PDF)**")
        try:
            pdf_bytes = build_pdf(itinerary, city, day_budgets, country)
            st.download_button(
                label="⬇️ Download itinerary",
                data=pdf_bytes,
                file_name=f"itinerary_{city.lower().replace(' ','_')}.html",
                mime="text/html",
                use_container_width=True,
            )
            st.caption("Open the downloaded file in Chrome or Safari, then press Ctrl+P (or ⌘P on Mac) to save as PDF.")
        except Exception as ex:
            st.error(f"Couldn't generate the download file: {ex}")

    with c2:
        st.markdown("**📅 Add stops to Google Calendar**")
        start_date = st.date_input("When does your trip start?",
                                   key="export_date",
                                   label_visibility="collapsed")
        start_str = start_date.strftime("%Y-%m-%d") if start_date else ""
        cal_urls = build_calendar_urls(itinerary, start_str, city)
        if cal_urls:
            # Group by day, show as expandable
            days_seen: dict = {}
            for item in cal_urls:
                days_seen.setdefault(item["day"], []).append(item)
            for day_lbl, items in days_seen.items():
                with st.expander(f"📅 {day_lbl} ({len(items)} events)", expanded=False):
                    for item in items:
                        st.markdown(
                            f'<a href="{item["url"]}" target="_blank" style="'
                            f'display:inline-block;margin:.12rem 0;font-size:.79rem;'
                            f'color:#a85820;text-decoration:none;'
                            f'border:1px solid #e0cdb8;border-radius:6px;'
                            f'padding:.18rem .55rem;background:#fffdf8">'
                            f'➕ Stop {item["stop"]}: {item["name"][:32]}</a>',
                            unsafe_allow_html=True,
                        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FLOATING AI ASSISTANT (DeepSeek)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HERO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    '<div class="hero">'
    '<div class="hero-title">✈️ <span class="hero-acc">Trip Planner</span></div>'
    '<div class="hero-sub">Tell us where you\'re headed — we\'ll build your perfect itinerary</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    # ── SECTION 1: Where are you going ──────────────────────────
    st.markdown("### 🌏 Where are you headed?")

    # ── Cascading: Country → City → (District in per-day tabs) ────
    # Level 1: Country / Region
    all_countries = sorted(WORLD_CITIES.keys())
    prev_country = st.session_state.get("sel_country", "")
    sel_country = st.selectbox(
        "🌐 Pick a country or region",
        [""] + all_countries,
        index=([""] + all_countries).index(prev_country) if prev_country in all_countries else 0,
        key="sel_country",
    )

    # Level 2: City within selected country
    if sel_country:
        city_opts_for_country = WORLD_CITIES.get(sel_country, [])
        prev_city_sel = st.session_state.get("sel_city_name", "")
        city_sel_idx = (city_opts_for_country.index(prev_city_sel)
                        if prev_city_sel in city_opts_for_country else 0)
        sel_city_name = st.selectbox(
            "🏙️ Which city?",
            city_opts_for_country,
            index=city_sel_idx,
            key="sel_city_name",
        )
    else:
        sel_city_name = ""

    # Level 3: Free-text override for any unlisted place
    city_override = st.text_input(
        "✏️ Not in the list? Type any city:",
        value="",
        placeholder="e.g. Kyoto, Cusco, Zanzibar, Queenstown…",
        key="city_override",
    )

    # Resolve final city_input
    if city_override.strip():
        city_input = city_override.strip()
    elif sel_city_name:
        city_input = sel_city_name
    elif sel_country:
        city_input = sel_country  # fallback: use country name
    else:
        city_input = "Tokyo"

    city_key  = city_input.strip().lower()
    is_cn     = city_key in CN_CITIES
    intl_data = INTL_CITIES.get(city_key)

    if is_cn:
        city_lat, city_lon = CN_CITIES[city_key]
        country = "CN"
    elif intl_data:
        city_lat, city_lon, country = intl_data[0], intl_data[1], intl_data[2]
    else:
        city_lat = city_lon = None
        country = COUNTRY_CODES.get(sel_country, "INT")

    hotel_addr  = st.text_input("🏨 Where are you staying?", "",
                                placeholder="Hotel name or address, e.g. Shinjuku Prince Hotel")
    depart_addr = st.text_input("🚩 Where do you start on Day 1?", "",
                                placeholder="e.g. Tokyo Station, your airport arrival point")
    arrive_addr = st.text_input("🏁 Where do you leave from at the end?", "",
                                placeholder="e.g. Narita Airport, train station")

    st.markdown("---")

    # ── SECTION 2: Per-day quota & area ─────────────────────────
    st.markdown("### 🗓️ Plan your days")

    # Trip duration
    days = st.number_input("How many days is your trip?", min_value=1, max_value=10,
                           value=3, step=1)
    ndays = int(days)


    # ── Place types ─────────────────────────────────────────────
    st.markdown('<div class="sdiv">What do you want to do?</div>', unsafe_allow_html=True)
    sel_types = st.multiselect(
        "types", list(PTYPES.keys()),
        default=["🏛️ Attraction", "🍜 Restaurant"],
        label_visibility="collapsed",
    )
    if not sel_types:
        sel_types = ["🏛️ Attraction"]

    # ── Load districts: Amap (CN) / static INTL_CITIES / Nominatim ──
    dist_key = f"dists_{city_key}"
    if dist_key not in st.session_state:
        if is_cn:
            with st.spinner(f"Loading {city_input.strip()} districts…"):
                st.session_state[dist_key] = amap_get_districts(city_input.strip())
        else:
            st.session_state[dist_key] = []

    amap_dists: list = st.session_state.get(dist_key, [])

    adcode_map: dict = {}   # district_name → adcode
    center_map: dict = {}   # district_name → (lat, lon)
    for d in amap_dists:
        n, a, la, lo = d.get("name",""), d.get("adcode",""), d.get("lat"), d.get("lon")
        if n and a:
            adcode_map[n] = a
        if n and la is not None:
            center_map[n] = (la, lo)

    # Build district options: Amap > static INTL > Nominatim Overpass
    if is_cn and amap_dists:
        per_day_opts = ["Auto (city-wide)"] + [d["name"] for d in amap_dists]
    elif intl_data and len(intl_data) > 3:
        per_day_opts = ["Auto (city-wide)"] + intl_data[3]
    else:
        # Dynamic Overpass lookup for any city
        dyn_key = f"dyn_dists_{city_key}"
        if dyn_key not in st.session_state and city_lat is not None:
            with st.spinner(f"Loading {city_input.strip()} neighbourhoods…"):
                st.session_state[dyn_key] = get_nominatim_districts(city_input.strip())
        dyn_dists = st.session_state.get(dyn_key, [])
        per_day_opts = (["Auto (city-wide)"] + dyn_dists) if dyn_dists else ["Auto (city-wide)"]

    # ── Per-day tabs ─────────────────────────────────────────────
    st.markdown('<div class="sdiv">Day-by-day preferences</div>', unsafe_allow_html=True)
    st.caption("Customise each day — choose an area, how picky you are about ratings, and how many places to visit.")

    day_quotas          = []
    day_adcodes         = []
    day_district_names  = []
    day_anchor_lats     = []
    day_anchor_lons     = []
    day_min_ratings     = []
    day_budgets         = []   # NEW: per-day USD budget

    if ndays <= 7:
        tabs = st.tabs([f"D{d+1}" for d in range(ndays)])
        for d_idx, tab in enumerate(tabs):
            with tab:
                d_sel = st.selectbox(
                    "Area", per_day_opts,
                    key=f"da_{d_idx}", label_visibility="collapsed",
                )
                auto = (d_sel == "Auto (city-wide)")
                if auto:
                    day_adcodes.append("")
                    day_district_names.append("")
                    day_anchor_lats.append(city_lat)
                    day_anchor_lons.append(city_lon)
                else:
                    day_adcodes.append(adcode_map.get(d_sel, ""))
                    day_district_names.append(d_sel)
                    if d_sel in center_map:
                        dlat, dlon = center_map[d_sel]
                    else:
                        dlat, dlon = city_lat, city_lon
                    day_anchor_lats.append(dlat)
                    day_anchor_lons.append(dlon)

                min_r = st.slider("Minimum rating (how strict?)", 0.0, 5.0, 3.5, 0.5,
                                  key=f"mr_{d_idx}")
                day_min_ratings.append(min_r)

                # ── Per-day budget slider ────────────────────────
                d_usd = st.slider(
                    "💰 Daily spending budget (USD)", min_value=10, max_value=500,
                    value=60, step=5, format="$%d",
                    key=f"bud_{d_idx}",
                )
                _cr  = fmt_currency_row(d_usd, country)
                _lp  = _cr.split("≈", 1)[-1].strip() if "≈" in _cr else ""
                st.markdown(
                    f'<div style="font-size:.72rem;color:#7a5a30;margin:-.05rem 0 .35rem">'
                    f'<b>${d_usd}/day</b>'
                    + (f' &nbsp;≈ {_lp}' if _lp else '')
                    + '</div>',
                    unsafe_allow_html=True,
                )
                day_budgets.append(d_usd)

                quota = {}
                for tl in sel_types:
                    n = st.slider(
                        tl, 0, 5, 1, 1,
                        key=f"q_{d_idx}_{tl}",
                    )
                    if n > 0:
                        quota[tl] = n
                if not quota:
                    quota = {sel_types[0]: 1}
                day_quotas.append(quota)
    else:
        # > 7 days: single shared tab
        d_sel = st.selectbox("Which area? (applies to all days)", per_day_opts,
                             key="da_all", label_visibility="collapsed")
        auto = (d_sel == "Auto (city-wide)")
        _adc = "" if auto else adcode_map.get(d_sel, "")
        _dname = "" if auto else d_sel
        if not auto and d_sel in center_map:
            _alat, _alon = center_map[d_sel]
        else:
            _alat, _alon = city_lat, city_lon

        day_adcodes        = [_adc]   * ndays
        day_district_names = [_dname] * ndays
        day_anchor_lats    = [_alat]  * ndays
        day_anchor_lons    = [_alon]  * ndays

        min_r = st.slider("Minimum rating (how strict?)", 0.0, 5.0, 3.5, 0.5, key="mr_all")
        day_min_ratings = [min_r] * ndays

        _shared_usd = st.slider(
            "💰 Daily spending budget (USD)", min_value=10, max_value=500,
            value=60, step=5, format="$%d", key="bud_all",
        )
        _cr  = fmt_currency_row(_shared_usd, country)
        _lp  = _cr.split("≈", 1)[-1].strip() if "≈" in _cr else ""
        st.markdown(
            f'<div style="font-size:.72rem;color:#7a5a30;margin:-.05rem 0 .35rem">'
            f'<b>${_shared_usd}/day</b>'
            + (f' &nbsp;≈ {_lp}' if _lp else '')
            + '</div>',
            unsafe_allow_html=True,
        )
        day_budgets = [_shared_usd] * ndays

        quota = {}
        for tl in sel_types:
            n = st.slider(tl, 0, 5, 1, 1, key=f"qa_{tl}")
            if n > 0:
                quota[tl] = n
        if not quota:
            quota = {sel_types[0]: 1}
        day_quotas = [dict(quota)] * ndays

    max_per_day      = max(sum(q.values()) for q in day_quotas) if day_quotas else 4
    total_quota      = sum(sum(q.values()) for q in day_quotas) if day_quotas else 4
    # Need enough candidates per type for all days: total × 6, min 30
    limit_per_type   = max(30, total_quota * 6)
    # Representative budget for display (average across days)
    daily_usd = round(sum(day_budgets) / len(day_budgets)) if day_budgets else 60
    em, lb, lc, bgc = budget_level(daily_usd)

    st.markdown("---")
    if "seed" not in st.session_state:
        st.session_state.seed = 42

    gen = st.button("🚀 Build my itinerary", use_container_width=True)
    ref = st.button("🔄 Try different places", use_container_width=True)
    if ref:
        st.session_state.seed = random.randint(1, 99999)
        st.cache_data.clear()
        gen = True

    st.markdown("---")
    api_src = "高德地图 (Amap)" if is_cn else "Overpass OSM"
    st.markdown(f"<small>📡 Data: {api_src} &nbsp;·&nbsp; Places within 8 km of each other</small>",
                unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN CONTENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if gen:
    # ── Resolve city coordinates
    if is_cn:
        lat, lon = city_lat, city_lon
        if lat is None:
            c = amap_geocode(city_input.strip())
            if c:
                lat, lon = c
            else:
                st.error(f"We couldn't find '{city_input}' on the map. Try a different spelling or a nearby city."); st.stop()
    elif intl_data:
        lat, lon = intl_data[0], intl_data[1]
    else:
        with st.spinner("🌐 Finding your destination…"):
            coord = nominatim(city_input)
        if not coord:
            st.error(f"Hmm, we couldn't locate '{city_input}'. Try the full city name or check the spelling."); st.stop()
        lat, lon = coord

    # ── Geocode saved locations
    hotel_c = depart_c = arrive_c = None
    with st.spinner("📍 Looking up your saved locations…"):
        hotel_c  = geocode(hotel_addr,  city_input, is_cn) if hotel_addr  else None
        depart_c = geocode(depart_addr, city_input, is_cn) if depart_addr else None
        arrive_c = geocode(arrive_addr, city_input, is_cn) if arrive_addr else None

    # ── Fetch places
    area_label = city_input.title()
    with st.spinner(f"🔍 Finding great places in {area_label}…"):
        try:
            df, warn = fetch_all_places(
                lat, lon, country, is_cn,
                tuple(sel_types), limit_per_type,
                tuple(day_adcodes),
                tuple(day_district_names),
                tuple(day_anchor_lats),
                tuple(day_anchor_lons),
                st.session_state.seed,
            )
        except Exception as ex:
            st.error(f"Something went wrong while searching for places: {ex}"); st.stop()

    if warn:
        st.warning(warn)
    if df is None or df.empty:
        st.error("No places found for this combination. Try a different city, area, or place type."); st.stop()

    # ── Build itinerary
    itinerary = {}
    if not AI_OK:
        st.error(f"ai_planner import error: {_AI_ERR}")
    else:
        with st.spinner("✨ Putting your itinerary together…"):
            try:
                itinerary = generate_itinerary(
                    df, ndays, day_quotas,
                    hotel_lat   = hotel_c[0]  if hotel_c  else None,
                    hotel_lon   = hotel_c[1]  if hotel_c  else None,
                    depart_lat  = depart_c[0] if depart_c else None,
                    depart_lon  = depart_c[1] if depart_c else None,
                    arrive_lat  = arrive_c[0] if arrive_c else None,
                    arrive_lon  = arrive_c[1] if arrive_c else None,
                    day_min_ratings  = day_min_ratings,
                    day_anchor_lats  = day_anchor_lats,
                    day_anchor_lons  = day_anchor_lons,
                )
            except Exception as ex:
                st.error(f"We hit a snag building your itinerary: {ex}")

    # ── 持久化到 session_state（下载按钮触发 rerun 时恢复）
    if itinerary:
        st.session_state["_itin"]    = itinerary
        st.session_state["_df"]      = df
        st.session_state["_city"]    = city_input
        st.session_state["_ndays"]   = ndays
        st.session_state["_budgets"] = day_budgets
        st.session_state["_country"] = country
        st.session_state["_types"]   = list(sel_types)
        st.session_state["_lat"]     = lat
        st.session_state["_lon"]     = lon
        st.session_state["_hotel"]   = hotel_c
        st.session_state["_depart"]  = depart_c
        st.session_state["_arrive"]  = arrive_c

    # ── Metrics row
    real  = sum(len(v) for v in itinerary.values()) if itinerary else 0
    avg_r = df["rating"].replace(0, float("nan")).mean()
    total_budget_str = f"${sum(day_budgets)}" if len(set(day_budgets)) > 1 else f"${daily_usd}/day"
    for c, (lbl, val) in zip(st.columns(5), [
        ("📍 Places",  str(len(df))),
        ("📅 Days",    str(ndays)),
        ("🗓️ Stops",   str(real)),
        ("⭐ Avg Rating", f"{avg_r:.1f}" if not math.isnan(avg_r) else "—"),
        ("💰 Budget",  total_budget_str),
    ]):
        c.metric(lbl, val)

    # ── Table
    types_str = " + ".join(sel_types)
    st.markdown(
        f'<div class="sec">📋 Your Itinerary — {area_label} &nbsp;·&nbsp; {types_str}</div>',
        unsafe_allow_html=True,
    )
    render_table(df, itinerary, day_budgets, country)

    # ── Budget summary
    render_budget_summary(itinerary, day_budgets, country, ndays)

    # ── Map
    st.markdown('<div class="sec">🗺️ Your Route on the Map</div>', unsafe_allow_html=True)
    st.caption("Tap a numbered circle to see place details · Tap a route dot for travel info · 🏨 = your hotel  🚩 = Day 1 start  🏁 = departure point")
    try:
        m = build_map(df, lat, lon, itinerary, hotel_c, depart_c, arrive_c)
        st_folium(m, width="100%", height=560, returned_objects=[])
    except Exception as ex:
        st.error(f"The map couldn't load: {ex}")

    # ── Export panel
    render_export_panel(itinerary, city_input, day_budgets, country)

elif "_itin" in st.session_state and "_df" in st.session_state:
    # ── 从 session_state 恢复（下载/日历等按钮触发的 rerun）──────
    _it  = st.session_state["_itin"]
    _df  = st.session_state["_df"]
    _ci  = st.session_state.get("_city",  city_input)
    _nd  = st.session_state.get("_ndays", ndays)
    _bud = st.session_state.get("_budgets", day_budgets)
    _ctr = st.session_state.get("_country", country)
    _tys = st.session_state.get("_types",   list(sel_types))
    _lat = st.session_state.get("_lat",     city_lat or 35.0)
    _lon = st.session_state.get("_lon",     city_lon or 139.0)
    _hc  = st.session_state.get("_hotel")
    _dc  = st.session_state.get("_depart")
    _ac  = st.session_state.get("_arrive")

    _real  = sum(len(v) for v in _it.values()) if _it else 0
    _avg_r = _df["rating"].replace(0, float("nan")).mean()
    _du    = round(sum(_bud)/len(_bud)) if _bud else 60
    _bstr  = f"${sum(_bud)}" if len(set(_bud)) > 1 else f"${_du}/day"
    for c, (lbl, val) in zip(st.columns(5), [
        ("📍 Places",     str(len(_df))),
        ("📅 Days",       str(_nd)),
        ("🗓️ Stops",      str(_real)),
        ("⭐ Avg Rating", f"{_avg_r:.1f}" if not math.isnan(_avg_r) else "—"),
        ("💰 Budget",     _bstr),
    ]):
        c.metric(lbl, val)

    _tstr = " + ".join(_tys)
    st.markdown(
        f'<div class="sec">📋 Your Itinerary — {_ci.title()} &nbsp;·&nbsp; {_tstr}</div>',
        unsafe_allow_html=True,
    )
    render_table(_df, _it, _bud, _ctr)
    render_budget_summary(_it, _bud, _ctr, _nd)
    st.markdown('<div class="sec">🗺️ Your Route on the Map</div>', unsafe_allow_html=True)
    st.caption("Tap a numbered circle to see place details · Tap a route dot for travel info · 🏨 = your hotel  🚩 = Day 1 start  🏁 = departure point")
    try:
        m = build_map(_df, _lat, _lon, _it, _hc, _dc, _ac)
        st_folium(m, width="100%", height=560, returned_objects=[])
    except Exception as ex:
        st.error(f"The map couldn't load: {ex}")
    render_export_panel(_it, _ci, _bud, _ctr)

else:
    # ── Welcome state
    st.markdown("---")
    for col, (icon, title, desc) in zip(st.columns(4), [
        ("🎯", "You decide the mix",  "Choose exactly what goes into each day — 2 sights, 1 café, whatever you want"),
        ("💰", "Stay on budget",   "Set a daily budget and see estimated costs in your local currency"),
        ("📍", "Plan by neighbourhood", "Pick the area you want to explore each day — the app clusters nearby places automatically"),
        ("🗺️", "No marathon days",   "All stops on a given day are kept within 8 km of each other — no exhausting detours"),
    ]):
        with col:
            st.markdown(
                f'<div class="gcard">'
                f'<div class="gcard-icon">{icon}</div>'
                f'<div class="gcard-title">{title}</div>'
                f'<div class="gcard-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,

            )
