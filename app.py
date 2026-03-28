"""
app.py v11 — AI Travel Planner Pro
Fixes: secrets reading, NULL display, swap UI, i18n
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

# ══════════════════════════════════════════════════════════════════
# API KEYS — read from Streamlit secrets OR environment variables
# ══════════════════════════════════════════════════════════════════
def _get_secret(key: str) -> str:
    """Read from st.secrets first, then os.getenv."""
    try:
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, "")

AMAP_KEY = _get_secret("APIKEY")
DEEPSEEK_KEY = _get_secret("DEEPSEEKKEY")

# ══════════════════════════════════════════════════════════════════
# LANG — init before any _t() call
# ══════════════════════════════════════════════════════════════════
if "lang_sel" not in st.session_state:
    st.session_state["lang_sel"] = "EN — English"
LANG = "ZH" if st.session_state["lang_sel"].startswith("ZH") else "EN"

# ══════════════════════════════════════════════════════════════════
# i18n
# ══════════════════════════════════════════════════════════════════
try:
    from i18n import t as _ti
    def _t(key, **kw): return _ti(key, LANG, **kw)
    I18N_OK = True
except Exception:
    I18N_OK = False
    _FB = {
        "hero_title": "✈️ Trip Planner",
        "hero_subtitle": "Tell us where you're headed — we'll build your perfect itinerary",
        "where_heading": "🌏 Where are you headed?",
        "pick_country": "🌐 Country / Region",
        "pick_city": "🏙️ City",
        "city_override": "✏️ Or type any city:",
        "city_placeholder": "e.g. Kyoto, Paris, Dubai…",
        "hotel_label": "🏨 Where are you staying?",
        "hotel_placeholder": "Hotel name or address",
        "depart_label": "🚩 Day 1 starting point",
        "depart_placeholder": "e.g. Tokyo Station",
        "arrive_label": "🏁 Final departure point",
        "arrive_placeholder": "e.g. Narita Airport",
        "plan_heading": "🗓️ Plan your days",
        "how_many_days": "How many days?",
        "what_todo": "What do you want to do?",
        "day_prefs_heading": "Day-by-day preferences",
        "day_prefs_caption": "Choose area, rating filter, and place count per day.",
        "area_label": "Area",
        "min_rating_label": "Min rating",
        "daily_budget_label": "💰 Daily budget (USD)",
        "all_area_label": "Area (all days)",
        "build_btn": "🚀 Build my itinerary",
        "refresh_btn": "🔄 Try different places",
        "loading_districts": "Loading districts…",
        "loading_neighbourhoods": "Loading neighbourhoods…",
        "finding_dest": "Finding destination…",
        "looking_up_locations": "Looking up locations…",
        "finding_places": "Finding places in",
        "building_itin": "Building itinerary…",
        "metric_places": "📍 Places",
        "metric_days": "📅 Days",
        "metric_stops": "🗓️ Stops",
        "metric_rating": "⭐ Avg Rating",
        "metric_budget": "💰 Budget",
        "tbl_seq": "#",
        "tbl_day_stop": "Day/Stop",
        "tbl_time": "Time",
        "tbl_place": "Place",
        "tbl_district": "District",
        "tbl_type": "Type",
        "tbl_rating": "Rating",
        "tbl_transport": "Getting There",
        "tbl_contact": "Contact",
        "map_heading": "🗺️ Route Map",
        "map_caption": "Click markers for details",
        "budget_heading": "💰 Cost Estimate",
        "budget_over": "🔴 Some days exceed budget.",
        "budget_total": "Total",
        "budget_breakdown": "📊 Breakdown",
        "export_heading": "📤 Save / Share",
        "export_download": "📄 Download HTML",
        "export_download_btn": "⬇️ Download",
        "export_calendar": "📅 Google Calendar",
        "export_date": "Start date?",
        "export_caption": "Open in browser → Ctrl+P → Save as PDF",
        "rec_heading": "💡 More Places",
        "rec_caption": "Worth exploring.",
        "rec_refresh": "🔄",
        "welcome_1_icon": "🎯", "welcome_1_title": "You decide", "welcome_1_desc": "Mix any types",
        "welcome_2_icon": "💰", "welcome_2_title": "Budget aware", "welcome_2_desc": "Local currency costs",
        "welcome_3_icon": "📍", "welcome_3_title": "By neighbourhood", "welcome_3_desc": "Clusters nearby places",
        "welcome_4_icon": "🗺️", "welcome_4_title": "No detours", "welcome_4_desc": "All stops within 8 km",
        "wishlist_heading": "💫 Wishlist",
        "wishlist_empty": "Wishlist empty.",
        "wishlist_add": "❤️ Save",
        "wishlist_saved": "✅ Saved!",
        "points_heading": "🎫 Points",
        "points_checkin": "📍 Check In",
        "points_checkin_done": "✅ Checked in!",
        "points_redeem": "🎁 Redeem",
        "points_balance": "Balance",
        "points_history": "History",
        "auth_login": "🔐 Sign In",
        "auth_register": "📝 Register",
        "auth_logout": "🚪 Sign Out",
        "auth_username": "Username",
        "auth_password": "Password",
        "auth_email": "Email",
        "auth_login_required": "Please sign in.",
        "collab_heading": "🤝 Collaborate",
        "collab_share_link": "📋 Share code",
        "mustsee_heading": "⭐ Must-See",
        "mustsee_caption": "Curated highlights",
        "err_city_not_found": "City '{city}' not found.",
        "err_itinerary_failed": "Itinerary error: {err}",
        "err_map_failed": "Map error: {err}",
        "err_no_places": "No places found.",
        "err_export_failed": "Export error: {err}",
        "data_source": "📡 Data",
        "data_radius": "Within 8 km",
        "last_stop": "Last stop",
        "transport_comparison": "🚇 Transport Options",
        "swap_heading": "🔄 Swap a Stop",
        "swap_caption": "Replace any stop with a nearby alternative.",
        "meal_suggestion": "🍽️ Meal Suggestions",
        "ai_rec_heading": "⭐ AI Recommendations",
        "ai_rec_caption": "AI-curated must-visit highlights for this destination",
    }
    def _t(key, **kw):
        text = _FB.get(key, key)
        if kw:
            try:
                text = text.format(**kw)
            except Exception:
                pass
        return text

# ══════════════════════════════════════════════════════════════════
# OTHER MODULE IMPORTS
# ══════════════════════════════════════════════════════════════════
try:
    from ai_planner import generate_itinerary
    AI_OK = True
except Exception as _e:
    AI_OK = False
    _AI_ERR = str(_e)

try:
    from transport_planner import (
        estimate_travel, estimate_all_modes,
        render_transport_comparison, haversine_km,
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
        logout_user, create_collab_link, join_collab,
    )
    AUTH_OK = True
except Exception:
    AUTH_OK = False

try:
    from wishlist_manager import (
        add_to_wishlist, remove_from_wishlist, get_wishlist,
        is_in_wishlist, save_itinerary as _save_itin,
        render_wishlist_panel, swap_place_in_itinerary,
    )
    WISHLIST_OK = True
except Exception:
    WISHLIST_OK = False

try:
    from points_system import (
        add_points, get_points, render_points_panel,
        render_checkin_button, checkin,
    )
    POINTS_OK = True
except Exception:
    POINTS_OK = False

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
html,body,[class*="css"]{font-family:'Segoe UI',sans-serif}
.main .block-container{padding:1.5rem 2rem 3rem}
section[data-testid="stSidebar"]{background:#faf6ef!important}
.hero-box{background:linear-gradient(135deg,#c97d35 0%,#e8a558 50%,#3a8fd4 100%);
  border-radius:18px;padding:32px 28px;margin-bottom:24px;color:#fff}
.hero-box h1{margin:0 0 6px;font-size:2.1rem;font-weight:800}
.hero-box p{margin:0;opacity:.88;font-size:1.05rem}
.info-card{background:#fff;border-radius:14px;padding:18px;flex:1;
  min-width:160px;box-shadow:0 2px 12px rgba(0,0,0,.07)}
.ic-icon{font-size:1.8rem;margin-bottom:8px}
.ic-title{font-weight:700;font-size:.95rem;margin-bottom:4px}
.ic-desc{color:#888;font-size:.82rem;line-height:1.4}
.sec-head{font-size:1.1rem;font-weight:700;margin:18px 0 8px;
  padding-bottom:4px;border-bottom:2px solid #e8d5bb}
.budget-pill{display:inline-flex;align-items:center;gap:6px;
  background:#fff7ed;border:1px solid #e8a558;border-radius:20px;
  padding:3px 10px;font-size:.82rem;color:#c97d35;font-weight:600}
.itin-table{width:100%;border-collapse:collapse;font-size:.84rem;margin-top:10px}
.itin-table th{background:#f5ede0;color:#8b5e2a;font-weight:600;
  padding:8px 10px;border-bottom:2px solid #e8d5bb;text-align:left;white-space:nowrap}
.itin-table td{padding:9px 10px;vertical-align:top;border-bottom:1px solid #f0e8d8}
.itin-table tr:hover td{background:#fffbf4}
.day-hdr td{background:#fdf3e3!important;font-weight:700;color:#8b5e2a;
  border-bottom:2px solid #e8d5bb!important;padding:10px!important}
.bsum-card{background:#fff;border-radius:12px;padding:14px;text-align:center;
  box-shadow:0 2px 10px rgba(0,0,0,.06)}
.bsum-card .day-lbl{font-size:.75rem;color:#888;margin-bottom:4px}
.bsum-card .day-amt{font-size:1.3rem;font-weight:800;color:#c97d35}
.bsum-card .day-rng{font-size:.72rem;color:#aaa}
.bsum-card .day-bud{font-size:.73rem;margin-top:4px;color:#777}
.rec-grid{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0}
.rec-card{background:#fff;border-radius:10px;padding:12px;
  flex:1;min-width:180px;max-width:240px;
  box-shadow:0 1px 8px rgba(0,0,0,.06);position:relative}
.rc-name{font-weight:700;font-size:.86rem;margin-bottom:4px}
.rc-meta{color:#888;font-size:.76rem}
.rc-badge{position:absolute;top:10px;right:10px;background:#fff8ee;
  border-radius:8px;padding:2px 7px;font-size:.78rem;color:#c97d35;font-weight:600}
.map-head{font-size:1.1rem;font-weight:700;margin:20px 0 6px;
  padding-left:6px;border-left:4px solid #c97d35}
.wl-badge{display:inline-block;background:#ffe4c4;color:#c97d35;
  border-radius:10px;padding:1px 8px;font-size:.75rem;font-weight:600}
/* Swap panel */
.swap-card{background:#fff7ed;border:1px solid #e8a558;border-radius:12px;
  padding:14px;margin:8px 0}
.swap-card h4{margin:0 0 10px;color:#c97d35;font-size:.95rem}
/* AI rec panel */
.ai-rec-panel{background:linear-gradient(135deg,#fff7ed,#f0f7ff);
  border-radius:14px;padding:16px;margin:14px 0;
  border:1px solid #e8d5bb}
.ai-rec-item{background:#fff;border-radius:8px;padding:10px 12px;
  margin:6px 0;border-left:3px solid #3a8fd4}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
BUDGET_LEVELS_USD = [
    (0,   30,  "💚", "Economy",  "#2E7D32", "#e8f5e9"),
    (30,  80,  "💛", "Standard", "#B07020", "#fff8e1"),
    (80,  200, "🧡", "Comfort",  "#C62828", "#fff3e0"),
    (200, 9999,"❤️", "Luxury",   "#6A1B9A", "#f3e5f5"),
]

def budget_level(usd):
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
    p = CURRENCIES.get(country, [("USD","$",1.0)])
    return (p[1][1], p[1][2]) if len(p) > 1 else (p[0][1], p[0][2])

def fmt_currency_row(usd, country):
    p = CURRENCIES.get(country, [("USD","$",1.0)])
    parts = [f"${usd}/day"]
    for _, sym, rate in p[1:]:
        a = round(usd * rate)
        parts.append(f"{sym}{a:,}/day" if a >= 10000 else f"{sym}{a}/day")
    return " ≈ ".join(parts)

COST_W = {
    "🏛️ Attraction": 0.18, "🍜 Restaurant": 0.25, "☕ Café": 0.10,
    "🌿 Park": 0.04, "🛍️ Shopping": 0.22, "🍺 Bar/Nightlife": 0.16,
    "🏨 Hotel": 0.00, "Transport": 0.12,
}
COST_FL = {
    "🏛️ Attraction": 4, "🍜 Restaurant": 6, "☕ Café": 3,
    "🌿 Park": 0, "🛍️ Shopping": 8, "🍺 Bar/Nightlife": 5,
    "🏨 Hotel": 0, "Transport": 1,
}

def cost_estimate(tl, daily_usd, country):
    w = COST_W.get(tl, .12)
    fl = COST_FL.get(tl, 2)
    pv = max(fl, daily_usd * w / 2)
    lo = pv * .65; hi = pv * 1.45; mid = (lo + hi) / 2
    sym, rate = _local_rate(country)
    if country == "US":
        return mid, f"${round(lo)}–${round(hi)}"
    return mid, f"${round(lo)}–${round(hi)} ({sym}{round(lo*rate)}–{sym}{round(hi*rate)})"

def transport_cost_estimate(dist_km, daily_usd, country):
    base = max(1, daily_usd * .12 / 5)
    f = max(1., dist_km / 3.)
    lo = base * f * .7; hi = base * f * 1.4; mid = (lo + hi) / 2
    sym, rate = _local_rate(country)
    if country == "US":
        return mid, f"${round(lo)}–${round(hi)}"
    return mid, f"${round(lo)}–${round(hi)} ({sym}{round(lo*rate)}–{sym}{round(hi*rate)})"

CN_CITIES = {
    "beijing": (39.9042,116.4074), "shanghai": (31.2304,121.4737),
    "guangzhou": (23.1291,113.2644), "shenzhen": (22.5431,114.0579),
    "chengdu": (30.5728,104.0668), "hangzhou": (30.2741,120.1551),
    "xian": (34.3416,108.9398), "xi'an": (34.3416,108.9398),
    "chongqing": (29.5630,106.5516), "nanjing": (32.0603,118.7969),
    "wuhan": (30.5928,114.3055), "suzhou": (31.2990,120.5853),
    "tianjin": (39.3434,117.3616), "qingdao": (36.0671,120.3826),
    "xiamen": (24.4798,118.0894), "zhengzhou": (34.7466,113.6254),
    "changsha": (28.2278,112.9388), "kunming": (25.0453,102.7097),
    "sanya": (18.2526,109.5119),
}

INTL_CITIES = {
    "tokyo": (35.6762,139.6503,"JP",["Shinjuku","Shibuya","Asakusa","Harajuku","Ginza","Akihabara"]),
    "osaka": (34.6937,135.5023,"JP",["Dotonbori","Namba","Umeda","Shinsekai","Tenoji"]),
    "kyoto": (35.0116,135.7681,"JP",["Gion","Arashiyama","Higashiyama","Fushimi","Nishiki"]),
    "seoul": (37.5665,126.9780,"KR",["Gangnam","Hongdae","Myeongdong","Itaewon","Insadong"]),
    "bangkok": (13.7563,100.5018,"TH",["Sukhumvit","Silom","Rattanakosin","Chatuchak"]),
    "singapore": (1.3521,103.8198,"SG",["Marina Bay","Clarke Quay","Orchard","Chinatown","Bugis"]),
    "paris": (48.8566,2.3522,"FR",["Le Marais","Montmartre","Saint-Germain","Bastille"]),
    "london": (51.5072,-0.1276,"GB",["Soho","Covent Garden","Shoreditch","South Bank","Camden"]),
    "rome": (41.9028,12.4964,"IT",["Trastevere","Campo de' Fiori","Prati","Vatican"]),
    "barcelona": (41.3851,2.1734,"ES",["Gothic Quarter","Eixample","Gracia","El Born"]),
    "new york": (40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Greenwich Village","Midtown"]),
    "new york city": (40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Midtown"]),
    "sydney": (-33.8688,151.2093,"AU",["Circular Quay","Surry Hills","Newtown","Bondi"]),
    "dubai": (25.2048,55.2708,"AE",["Downtown","Dubai Marina","Deira","JBR","DIFC"]),
    "amsterdam": (52.3676,4.9041,"NL",["Jordaan","De Pijp","Centrum","Oost"]),
    "istanbul": (41.0082,28.9784,"TR",["Beyoglu","Sultanahmet","Besiktas","Kadikoy"]),
    "hong kong": (22.3193,114.1694,"HK",["Central","Tsim Sha Tsui","Mong Kok","Causeway Bay"]),
    "taipei": (25.0330,121.5654,"TW",["Daan","Xinyi","Zhongzheng","Shilin","Ximending"]),
    "bali": (-8.3405,115.0920,"ID",["Seminyak","Ubud","Canggu","Kuta","Uluwatu"]),
    "ho chi minh city": (10.7769,106.7009,"VN",["District 1","District 3","Bui Vien"]),
    "kuala lumpur": (3.1390,101.6869,"MY",["KLCC","Bukit Bintang","Bangsar","Chow Kit"]),
}

PTYPES = {
    "🏛️ Attraction": {"cn":"景点","osm":("tourism","attraction"),"amap":"110000","color":"#3a8fd4"},
    "🍜 Restaurant":  {"cn":"餐厅","osm":("amenity","restaurant"), "amap":"050000","color":"#c97d35"},
    "☕ Café":         {"cn":"咖啡馆","osm":("amenity","cafe"),     "amap":"050500","color":"#7a5c3a"},
    "🌿 Park":         {"cn":"公园","osm":("leisure","park"),       "amap":"110101","color":"#3aaa7a"},
    "🛍️ Shopping":    {"cn":"购物","osm":("shop","mall"),          "amap":"060000","color":"#9b59b6"},
    "🍺 Bar/Nightlife":{"cn":"酒吧","osm":("amenity","bar"),       "amap":"050600","color":"#e05c3a"},
    "🏨 Hotel":        {"cn":"酒店","osm":("tourism","hotel"),      "amap":"100000","color":"#1abc9c"},
}

AMAP_ALT = {
    "🏛️ Attraction": ["旅游景点","博物馆","历史","游览"],
    "🍜 Restaurant":  ["餐馆","美食","饭店","特色菜"],
    "☕ Café":         ["咖啡","下午茶","cafe"],
    "🌿 Park":         ["公园","花园","绿地","广场"],
    "🛍️ Shopping":    ["商场","购物中心","超市","市集"],
    "🍺 Bar/Nightlife":["酒吧","KTV","夜店","清吧"],
    "🏨 Hotel":        ["酒店","宾馆","民宿","客栈"],
}

DAY_COLORS = ["#c97d35","#3a8fd4","#3aaa7a","#9b59b6","#e05c3a","#1abc9c","#e91e63","#f39c12"]

TDESC = {
    "景点":"Worth a visit","attraction":"Worth a visit",
    "餐厅":"Good place to eat","restaurant":"Good place to eat",
    "咖啡":"Great for a coffee break","cafe":"Great for a coffee break",
    "公园":"Relax outdoors","park":"Relax outdoors",
    "购物":"Shopping stop","mall":"Shopping stop",
    "酒吧":"Evening out","bar":"Evening out",
    "酒店":"Place to stay","hotel":"Place to stay",
}

def tdesc(s):
    for k, v in TDESC.items():
        if k in str(s).lower():
            return v
    return "Local favourite"

CHAIN_BL = [
    "肯德基","麦当劳","星巴克","costa","711","全家","罗森",
    "kfc","mcdonald","starbucks","seven-eleven","family mart",
]
def is_chain(n):
    return any(k in n.lower() for k in CHAIN_BL)

def _hav_m(la1, lo1, la2, lo2):
    R = 6371000
    dl = math.radians(la2-la1); dg = math.radians(lo2-lo1)
    a = (math.sin(dl/2)**2
         + math.cos(math.radians(la1)) * math.cos(math.radians(la2)) * math.sin(dg/2)**2)
    return R * 2 * math.asin(math.sqrt(min(1., a)))

def _nsim(a, b):
    a, b = a.strip().lower(), b.strip().lower()
    if a == b: return True
    s, l = (a,b) if len(a)<=len(b) else (b,a)
    return len(s) >= 3 and s in l

def geo_dedup(places, r=120.):
    if not places: return []
    merged = [False]*len(places); kept = []
    for i, p in enumerate(places):
        if merged[i]: continue
        best = p
        for j in range(i+1, len(places)):
            if merged[j]: continue
            d = _hav_m(best["lat"],best["lon"],places[j]["lat"],places[j]["lon"])
            if d < 50 or (d < r and _nsim(best["name"],places[j]["name"])):
                merged[j] = True
                if places[j]["rating"] > best["rating"]:
                    best = places[j]
        kept.append(best)
    return kept

WORLD_CITIES = {
    "China":["Beijing","Shanghai","Guangzhou","Shenzhen","Chengdu","Hangzhou",
             "Xi'an","Chongqing","Nanjing","Wuhan","Suzhou","Tianjin",
             "Qingdao","Xiamen","Kunming","Sanya","Changsha","Zhengzhou"],
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya","Hiroshima","Nara","Hakone"],
    "South Korea":["Seoul","Busan","Incheon","Jeju","Daegu"],
    "Thailand":["Bangkok","Chiang Mai","Phuket","Pattaya","Koh Samui"],
    "Vietnam":["Ho Chi Minh City","Hanoi","Da Nang","Hoi An","Nha Trang"],
    "Indonesia":["Bali","Jakarta","Yogyakarta","Lombok"],
    "Malaysia":["Kuala Lumpur","Penang","Malacca","Langkawi"],
    "Singapore":["Singapore"],
    "Philippines":["Manila","Cebu","Boracay","Palawan"],
    "India":["Mumbai","Delhi","Bangalore","Jaipur","Goa","Agra","Chennai"],
    "UAE":["Dubai","Abu Dhabi","Sharjah"],
    "Turkey":["Istanbul","Cappadocia","Antalya","Bodrum","Pamukkale"],
    "France":["Paris","Lyon","Nice","Bordeaux","Strasbourg"],
    "Italy":["Rome","Milan","Florence","Venice","Naples","Amalfi","Cinque Terre"],
    "Spain":["Barcelona","Madrid","Seville","Valencia","Granada","Bilbao"],
    "United Kingdom":["London","Edinburgh","Manchester","Bath","Cambridge","Oxford"],
    "Germany":["Berlin","Munich","Hamburg","Frankfurt","Cologne","Dresden"],
    "Netherlands":["Amsterdam","Rotterdam","Utrecht"],
    "Switzerland":["Zurich","Geneva","Lucerne","Interlaken","Zermatt"],
    "Austria":["Vienna","Salzburg","Innsbruck","Hallstatt"],
    "Greece":["Athens","Santorini","Mykonos","Crete","Rhodes"],
    "Portugal":["Lisbon","Porto","Algarve","Sintra"],
    "Czech Republic":["Prague","Brno","Cesky Krumlov"],
    "Hungary":["Budapest"],
    "Poland":["Warsaw","Krakow","Wroclaw","Gdansk"],
    "Croatia":["Dubrovnik","Split","Zagreb","Hvar"],
    "Norway":["Oslo","Bergen","Tromsø","Lofoten Islands"],
    "Sweden":["Stockholm","Gothenburg","Kiruna"],
    "Denmark":["Copenhagen","Aarhus"],
    "Finland":["Helsinki","Rovaniemi"],
    "Iceland":["Reykjavik","Akureyri"],
    "Russia":["Moscow","St. Petersburg","Vladivostok"],
    "USA":["New York","Los Angeles","Chicago","San Francisco","Miami","Boston",
           "Seattle","Las Vegas","Washington DC","Nashville"],
    "Canada":["Toronto","Vancouver","Montreal","Banff","Quebec City"],
    "Mexico":["Mexico City","Cancun","Playa del Carmen","Oaxaca"],
    "Brazil":["Rio de Janeiro","São Paulo","Salvador","Iguazu Falls"],
    "Argentina":["Buenos Aires","Patagonia","Mendoza","Bariloche"],
    "Peru":["Lima","Cusco","Machu Picchu","Arequipa"],
    "Colombia":["Bogota","Cartagena","Medellin"],
    "Australia":["Sydney","Melbourne","Brisbane","Perth","Cairns","Gold Coast"],
    "New Zealand":["Auckland","Queenstown","Wellington","Rotorua"],
    "Morocco":["Marrakech","Fes","Casablanca","Chefchaouen"],
    "Egypt":["Cairo","Luxor","Aswan","Alexandria"],
    "South Africa":["Cape Town","Johannesburg","Durban","Kruger"],
    "Kenya":["Nairobi","Mombasa","Masai Mara"],
    "Hong Kong":["Hong Kong"],
    "Taiwan":["Taipei","Tainan","Kaohsiung","Taichung","Hualien"],
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
    "Hong Kong":"HK","Taiwan":"TW",
}

# ══════════════════════════════════════════════════════════════════
# AI RECOMMENDATIONS (DeepSeek or built-in fallback)
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_recommendations(city: str, country: str, days: int, types: list, lang: str = "EN") -> list:
    """
    Get AI-powered place recommendations.
    Tries DeepSeek API first; falls back to curated data_manager list.
    Returns list of dicts: {name, type, why, tip, rating}
    """
    # Try DeepSeek
    if DEEPSEEK_KEY:
        try:
            type_str = ", ".join(types[:5])
            if lang == "ZH":
                prompt = (f"为{city}旅行推荐{days}天行程中的10个必去地点，"
                          f"类型包括：{type_str}。"
                          f"请以JSON数组格式返回，每项包含字段："
                          f"name(地点名), type(类型), why(推荐原因，20字以内), "
                          f"tip(实用贴士，20字以内), rating(4.0-5.0的数字)。"
                          f"只返回JSON，不要其他文字。")
            else:
                prompt = (f"Recommend 10 must-visit places in {city} for a {days}-day trip. "
                          f"Types: {type_str}. "
                          f"Return a JSON array only. Each item: "
                          f"name, type, why (reason ≤15 words), tip (practical tip ≤15 words), "
                          f"rating (4.0-5.0). No other text.")

            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}",
                         "Content-Type": "application/json"},
                json={"model": "deepseek-chat",
                      "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.7, "max_tokens": 800},
                timeout=15,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                # Extract JSON array
                import re
                m = re.search(r'\[.*\]', content, re.DOTALL)
                if m:
                    import json
                    items = json.loads(m.group())
                    if isinstance(items, list) and items:
                        return items[:10]
        except Exception:
            pass

    # Fallback: use data_manager curated list
    if DATA_MGR_OK:
        items = get_must_see(city, limit=8)
        return [{"name": it["name"], "type": it["type"],
                 "why": it.get("tip","Worth a visit")[:50],
                 "tip": it.get("tip",""),
                 "rating": it.get("rating", 4.5)}
                for it in items]

    # Last resort: built-in mini database
    BUILTIN = {
        "beijing":    [{"name":"故宫","type":"🏛️ Attraction","why":"World's largest palace complex","tip":"Book online, sell out fast","rating":4.9},
                       {"name":"长城(慕田峪)","type":"🏛️ Attraction","why":"Less crowded than Badaling","tip":"Go early morning","rating":4.9},
                       {"name":"天坛","type":"🏛️ Attraction","why":"Ming dynasty ceremonial site","tip":"Visit at sunrise for tai chi","rating":4.8}],
        "shanghai":   [{"name":"外滩","type":"🏛️ Attraction","why":"Iconic waterfront skyline","tip":"Night view is breathtaking","rating":4.9},
                       {"name":"豫园","type":"🌿 Park","why":"Classical Chinese garden","tip":"Go early morning","rating":4.7},
                       {"name":"小笼包 南翔","type":"🍜 Restaurant","why":"Best xiao long bao in Shanghai","tip":"Queue early","rating":4.8}],
        "tokyo":      [{"name":"Senso-ji","type":"🏛️ Attraction","why":"Tokyo's oldest temple","tip":"Dawn visit avoids crowds","rating":4.8},
                       {"name":"Shibuya Crossing","type":"🏛️ Attraction","why":"World's busiest crossing","tip":"Watch from Starbucks above","rating":4.7},
                       {"name":"Tsukiji Market","type":"🍜 Restaurant","why":"Freshest sushi breakfast","tip":"Go before 9 AM","rating":4.7}],
        "paris":      [{"name":"Louvre","type":"🏛️ Attraction","why":"World's largest art museum","tip":"Go Wednesday evening","rating":4.8},
                       {"name":"Eiffel Tower","type":"🏛️ Attraction","why":"Iconic iron lattice tower","tip":"Book summit tickets ahead","rating":4.7},
                       {"name":"Musée d'Orsay","type":"🏛️ Attraction","why":"Best Impressionist collection","tip":"Less queue than Louvre","rating":4.9}],
    }
    city_lc = city.strip().lower()
    for k, v in BUILTIN.items():
        if k in city_lc:
            return v
    return []


def render_ai_recommendations(city: str, country: str, days: int,
                               types: list, lang: str = "EN"):
    """Render the AI recommendations panel."""
    recs = get_ai_recommendations(city, country, days, types, lang)
    if not recs:
        return

    title = _t("ai_rec_heading") if I18N_OK else "⭐ AI Recommendations"
    caption = _t("ai_rec_caption") if I18N_OK else "AI-curated must-visit highlights"

    st.markdown(
        f'<div class="ai-rec-panel">'
        f'<div style="font-weight:700;font-size:1rem;margin-bottom:4px">{title}</div>'
        f'<div style="color:#888;font-size:.8rem;margin-bottom:10px">'
        f'{"🤖 Powered by DeepSeek AI" if DEEPSEEK_KEY else "📚 Curated recommendations"}'
        f'  ·  {caption}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(recs), 3))
    for i, rec in enumerate(recs):
        with cols[i % min(len(recs), 3)]:
            nm = str(rec.get("name",""))
            tp = str(rec.get("type",""))
            why = str(rec.get("why",""))
            tip = str(rec.get("tip",""))
            rat = rec.get("rating", 4.5)
            st.markdown(
                f'<div class="ai-rec-item">'
                f'<div style="font-weight:700;font-size:.88rem">{nm}</div>'
                f'<div style="color:#3a8fd4;font-size:.75rem">{tp}</div>'
                f'<div style="color:#555;font-size:.78rem;margin-top:3px">{why}</div>'
                f'{"<div style=color:#c97d35;font-size:.74rem>💡 "+tip+"</div>" if tip else ""}'
                f'<div style="color:#888;font-size:.74rem;margin-top:3px">⭐ {rat}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# GEOCODING
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def _amap_get_districts(city):
    if not city.strip() or not AMAP_KEY:
        return []
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/config/district",
            params={"key": AMAP_KEY, "keywords": city, "subdistrict": 1,
                    "extensions": "base", "output": "json"},
            timeout=9,
        ).json()
        if str(r.get("status")) != "1" or not r.get("districts"):
            return []
        out = []
        for d in r["districts"][0].get("districts", []):
            n = (d.get("name") or "").strip()
            a = (d.get("adcode") or "").strip()
            c = (d.get("center") or "").strip()
            if not (n and a): continue
            lat = lon = None
            if "," in c:
                try:
                    lon, lat = map(float, c.split(","))
                except Exception:
                    pass
            out.append({"name": n, "adcode": a, "lat": lat, "lon": lon})
        return out
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def _amap_geocode(addr):
    if not AMAP_KEY:
        return None
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"key": AMAP_KEY, "address": addr, "output": "json"},
            timeout=8,
        ).json()
        if str(r.get("status")) == "1" and r.get("geocodes"):
            loc = r["geocodes"][0].get("location", "")
            if "," in loc:
                lon, lat = map(float, loc.split(","))
                return lat, lon
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def _nominatim(q):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers={"User-Agent": "TravelPlannerPro/11"},
            timeout=9,
        ).json()
        if r:
            return float(r[0]["lat"]), float(r[0]["lon"])
    except Exception:
        pass
    return None

def _geocode(addr, city, is_cn):
    if not addr.strip(): return None
    if is_cn:
        return _amap_geocode(f"{addr} {city}") or _nominatim(f"{addr} {city}")
    return _nominatim(f"{addr} {city}") or _nominatim(addr)

@st.cache_data(ttl=3600, show_spinner=False)
def _get_nominatim_districts(city):
    if not city.strip(): return []
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "TravelPlannerPro/11"},
            timeout=8,
        ).json()
        if not r: return []
        lat, lon = float(r[0]["lat"]), float(r[0]["lon"])
        q = (f'[out:json][timeout:20];'
             f'(relation["place"~"suburb|neighbourhood|quarter|district"]'
             f'(around:20000,{lat},{lon});'
             f'node["place"~"suburb|neighbourhood|quarter"]'
             f'(around:20000,{lat},{lon}););out tags 30;')
        els = []
        for url in ["https://overpass-api.de/api/interpreter",
                    "https://overpass.kumi.systems/api/interpreter"]:
            try:
                els = requests.post(url, data={"data": q}, timeout=18).json().get("elements", [])
                if els: break
            except Exception:
                continue
        names = []
        for el in els:
            n = el.get("tags", {}).get("name:en") or el.get("tags", {}).get("name", "")
            if n and n not in names and len(n) > 1:
                names.append(n)
        return sorted(names[:25])
    except Exception:
        return []

# ══════════════════════════════════════════════════════════════════
# PLACE SEARCH — AMAP
# ══════════════════════════════════════════════════════════════════
def _parse_amap(pois, cn_kw, tl, limit, seen):
    out = []
    for p in pois:
        if len(out) + len(seen) >= limit: break
        nm = p.get("name", "")
        if not nm or is_chain(nm): continue
        loc = p.get("location", "")
        if "," not in (loc or ""): continue
        try:
            plon, plat = map(float, loc.split(","))
        except Exception:
            continue
        k = (nm, round(plat,4), round(plon,4))
        if k in seen: continue
        seen.add(k)
        biz = p.get("biz_ext") or {}
        try:
            rating = float(biz.get("rating") or 0) or 0.0
        except Exception:
            rating = 0.0
        tel = biz.get("tel") or p.get("tel") or ""
        if isinstance(tel, list): tel = "; ".join(t for t in tel if t)
        addr = p.get("address") or ""
        if isinstance(addr, list): addr = "".join(addr)
        out.append({
            "name": nm, "lat": plat, "lon": plon, "rating": rating,
            "address": str(addr).strip(), "phone": str(tel).strip(), "website": "",
            "type": cn_kw, "type_label": tl,
            "district": p.get("adname") or "", "description": tdesc(cn_kw),
        })
    return out

def _amap_by_adcode(adcode, cn_kw, tl, limit):
    if not AMAP_KEY:
        return [], "No AMAP_KEY"
    places = []; seen = set(); at = PTYPES.get(tl,{}).get("amap",""); err = None

    def _f(kw, tc, pg):
        params = {"key": AMAP_KEY, "keywords": kw, "city": adcode,
                  "citylimit": "true", "offset": 25, "page": pg,
                  "extensions": "all", "output": "json"}
        if tc: params["types"] = tc
        return requests.get("https://restapi.amap.com/v3/place/text",
                             params=params, timeout=10).json()

    for pg in range(1, 6):
        if len(places) >= limit: break
        try:
            d = _f(cn_kw, at, pg)
            if str(d.get("status")) != "1":
                err = f"{d.get('infocode')} {d.get('info')}"; break
            ps = d.get("pois") or []
            if not ps: break
            places.extend(_parse_amap(ps, cn_kw, tl, limit, seen))
        except Exception as e:
            err = str(e); break

    if len(places) < limit and at:
        for pg in range(1, 4):
            if len(places) >= limit: break
            try:
                d = _f("", at, pg)
                if str(d.get("status")) != "1": break
                ps = d.get("pois") or []
                if not ps: break
                places.extend(_parse_amap(ps, cn_kw, tl, limit, seen))
            except Exception:
                break

    if len(places) < limit:
        for ak in AMAP_ALT.get(tl, []):
            if ak == cn_kw or len(places) >= limit: continue
            try:
                d = _f(ak, at, 1)
                if str(d.get("status")) != "1": continue
                places.extend(_parse_amap(d.get("pois") or [], ak, tl, limit, seen))
            except Exception:
                continue

    return places[:limit], err

def _amap_around(lat, lon, cn_kw, tl, limit, radius=8000):
    if not AMAP_KEY:
        return [], "No AMAP_KEY"
    places = []; errs = []; seen = set(); at = PTYPES.get(tl,{}).get("amap","")
    for kw in [cn_kw] + AMAP_ALT.get(tl, []):
        if len(places) >= limit: break
        for pg in range(1, 5):
            if len(places) >= limit: break
            try:
                params = {"key": AMAP_KEY, "location": f"{lon},{lat}", "radius": radius,
                          "keywords": kw, "offset": 25, "page": pg,
                          "extensions": "all", "output": "json"}
                if at: params["types"] = at
                d = requests.get("https://restapi.amap.com/v3/place/around",
                                  params=params, timeout=10).json()
                if str(d.get("status")) != "1":
                    errs.append(f"{d.get('infocode')}"); break
                ps = d.get("pois") or []
                if not ps: break
                places.extend(_parse_amap(ps, cn_kw, tl, limit, seen))
            except Exception as e:
                errs.append(str(e)); break
    return places[:limit], (errs[0] if errs else None)

def search_cn(lat, lon, tls, lpt, adcode="", dname=""):
    all_p = []; errs = []
    for tl in tls:
        cn = PTYPES[tl]["cn"]
        if adcode:
            ps, e = _amap_by_adcode(adcode, cn, tl, lpt)
        else:
            ps, e = _amap_around(lat, lon, cn, tl, lpt)
        if e: errs.append(f"{tl}: {e}")
        all_p.extend(ps)
    seen, out = set(), []
    for p in all_p:
        k = (p["name"], round(p["lat"],4), round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    return out, errs

# ══════════════════════════════════════════════════════════════════
# PLACE SEARCH — OSM
# ══════════════════════════════════════════════════════════════════
def _osm_single(lat, lon, ok, ov, tl, limit, district=""):
    clat, clon = lat, lon
    if district:
        try:
            g = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": district, "format": "json", "limit": 1},
                headers={"User-Agent": "TravelPlannerPro/11"},
                timeout=5,
            ).json()
            if g:
                clat, clon = float(g[0]["lat"]), float(g[0]["lon"])
        except Exception:
            pass

    q = (f'[out:json][timeout:30];'
         f'(node["{ok}"="{ov}"](around:5000,{clat},{clon});'
         f'way["{ok}"="{ov}"](around:5000,{clat},{clon}););out center {limit*4};')

    els = []
    for url in ["https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter"]:
        try:
            r = requests.post(url, data={"data": q}, timeout=28)
            result = r.json().get("elements", [])
            if result:
                els = result
                break
        except Exception:
            continue

    places = []
    for el in els:
        tags = el.get("tags", {})
        nm = tags.get("name:en") or tags.get("name") or ""
        if not nm or is_chain(nm): continue
        elat = (el.get("lat", 0) if el["type"] == "node"
                else el.get("center", {}).get("lat", 0))
        elon = (el.get("lon", 0) if el["type"] == "node"
                else el.get("center", {}).get("lon", 0))
        if not elat or not elon: continue
        pts = [tags.get(k, "") for k in
               ["addr:housenumber","addr:street","addr:suburb","addr:city"]
               if tags.get(k)]
        places.append({
            "name": nm, "lat": elat, "lon": elon,
            "rating": round(random.uniform(3.8, 5.0), 1),
            "address": ", ".join(pts),
            "phone": tags.get("phone", ""),
            "website": tags.get("website", ""),
            "type": ov, "type_label": tl,
            "district": tags.get("addr:suburb", ""),
            "description": tdesc(ov),
        })
        if len(places) >= limit:
            break
    return places

def search_intl(lat, lon, tls, lpt, district=""):
    all_p = []
    for tl in tls:
        ok, ov = PTYPES[tl]["osm"]
        all_p.extend(_osm_single(lat, lon, ok, ov, tl, lpt, district))
    seen, out = set(), []
    for p in all_p:
        k = (p["name"], round(p["lat"],3), round(p["lon"],3))
        if k not in seen: seen.add(k); out.append(p)
    return out

# ══════════════════════════════════════════════════════════════════
# DEMO PLACES
# ══════════════════════════════════════════════════════════════════
def demo_places(lat, lon, tls, n, seed, district=""):
    random.seed(seed)
    NAMES = {
        "🏛️ Attraction": ["Grand Museum","Sky Tower","Ancient Temple","Art Gallery",
                          "Historic Castle","Night Market","Cultural Center","Scenic Viewpoint"],
        "🍜 Restaurant":  ["Sakura Dining","Ramen House","Sushi Master","Hot Pot Garden",
                          "Yakitori Bar","Noodle King","Street Food Alley","Harbour Grill"],
        "☕ Café":         ["Blue Bottle","Artisan Brew","Matcha Corner","Loft Coffee",
                          "Morning Pour","The Cozy Cup"],
        "🌿 Park":         ["Riverside Park","Sakura Garden","Central Park","Bamboo Grove"],
        "🛍️ Shopping":    ["Central Mall","Night Bazaar","Vintage Market","Designer District"],
        "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Garden"],
        "🏨 Hotel":        ["Grand Palace Hotel","Boutique Inn","City View Hotel"],
    }
    centers = [(lat+random.uniform(-.022,.022), lon+random.uniform(-.022,.022))
               for _ in range(3)]
    out = []
    for tl in tls:
        nms = list(NAMES.get(tl, ["Local Spot"]))
        random.shuffle(nms)
        for i, nm in enumerate(nms[:n]):
            ci = i % 3; clat, clon = centers[ci]
            out.append({
                "name": nm,
                "lat": round(clat + random.uniform(-.006,.006), 5),
                "lon": round(clon + random.uniform(-.006,.006), 5),
                "rating": round(random.uniform(4.0, 4.9), 1),
                "address": "Preview — connect to internet for real data",
                "phone": "", "website": "",
                "type": PTYPES[tl]["cn"] if tl in PTYPES else tl,
                "type_label": tl,
                "district": district or ["North","Central","South"][ci],
                "description": tdesc(tl),
            })
    return out

@st.cache_data(ttl=180, show_spinner=False)
def fetch_all_places(clat, clon, country, is_cn, tls_t, lpt,
                     adcodes_t, dnames_t, alats_t, alons_t, _seed):
    random.seed(_seed)
    tls = list(tls_t); all_raw = []; warn = None; api_errs = []; seen_k = set()
    for i in range(len(adcodes_t)):
        adc = adcodes_t[i]; dn = dnames_t[i]
        dlat = alats_t[i] if alats_t[i] is not None else clat
        dlon = alons_t[i] if alons_t[i] is not None else clon
        ck = adc or f"ll_{round(dlat,3)}_{round(dlon,3)}"
        if ck in seen_k: continue
        seen_k.add(ck)
        if is_cn:
            ps, errs = search_cn(dlat, dlon, tls, lpt, adc, dn)
            api_errs.extend(errs)
        else:
            ps = search_intl(dlat, dlon, tls, lpt, dn)
        all_raw.extend(ps)

    seen, out = set(), []
    for p in all_raw:
        k = (p["name"], round(p["lat"],4), round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    out = geo_dedup(out)

    if not out:
        out = demo_places(clat, clon, tls, lpt, _seed)
        if is_cn:
            warn = ("⚠️ 高德 API 无数据（检查Key IP白名单）" if api_errs
                    else "⚠️ 高德 API 网络不可达") + "，显示演示数据。"
        else:
            warn = "⚠️ Couldn't fetch live data — showing sample places."

    df = pd.DataFrame(out)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c] = ""
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.)
    return df.sort_values("rating", ascending=False).reset_index(drop=True), warn

# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    tok = st.session_state.get("_auth_token","")
    return get_user_from_session(tok) if tok else None

def render_auth_sidebar():
    if not AUTH_OK: return
    user = _cur_user()
    if user:
        pts = get_points(user["username"]) if POINTS_OK else 0
        st.markdown(
            f'<div style="background:#fff7ed;border-radius:10px;padding:10px;margin-bottom:8px">'
            f'👤 <b>{user["username"]}</b>  '
            f'<span class="wl-badge">🎫 {pts} pts</span></div>',
            unsafe_allow_html=True)
        if st.button(_t("auth_logout"), key="auth_lo"):
            logout_user(st.session_state.get("_auth_token",""))
            st.session_state.pop("_auth_token", None)
            st.rerun()
    else:
        t1, t2 = st.tabs([_t("auth_login"), _t("auth_register")])
        with t1:
            u = st.text_input(_t("auth_username"), key="li_u")
            p = st.text_input(_t("auth_password"), type="password", key="li_p")
            if st.button(_t("auth_login"), key="li_b", use_container_width=True):
                ok, msg, tok = login_user(u, p)
                if ok:
                    st.session_state["_auth_token"] = tok
                    if POINTS_OK: add_points(u, "daily_login")
                    st.success(msg); st.rerun()
                else:
                    st.error(msg)
        with t2:
            ru = st.text_input(_t("auth_username"), key="re_u")
            re_e = st.text_input(_t("auth_email"), key="re_e")
            rp = st.text_input(_t("auth_password"), type="password", key="re_p")
            if st.button(_t("auth_register"), key="re_b", use_container_width=True):
                ok, msg = register_user(ru, rp, re_e)
                (st.success if ok else st.error)(msg)

# ══════════════════════════════════════════════════════════════════
# MAP
# ══════════════════════════════════════════════════════════════════
def build_map(df, lat, lon, itinerary, hotel_c=None, depart_c=None, arrive_c=None):
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB positron")
    vi = {}
    if itinerary:
        for di, (dl, stops) in enumerate(itinerary.items()):
            for si, s in enumerate(stops):
                vi[s["name"]] = (di, si+1, s)

    if itinerary:
        for di, (dl, stops) in enumerate(itinerary.items()):
            if len(stops) < 2: continue
            dc = DAY_COLORS[di % len(DAY_COLORS)]
            for si in range(len(stops)-1):
                a, b = stops[si], stops[si+1]
                tr = a.get("transport_to_next") or {}
                folium.PolyLine(
                    [[a["lat"],a["lon"]], [b["lat"],b["lon"]]],
                    color=dc, weight=3.8, opacity=.75, dash_array="7 4",
                ).add_to(m)
                mid = [(a["lat"]+b["lat"])/2, (a["lon"]+b["lon"])/2]
                pt = (f"<div style='font-size:.8rem'><b>{dl} · Leg {si+1}</b><br>"
                      f"{tr.get('mode','—')}<br>"
                      f"⏱ {tr.get('duration','—')} · 📏 {tr.get('distance_km','—')} km<br>"
                      f"{a['name']} → {b['name']}</div>")
                folium.Marker(
                    mid,
                    popup=folium.Popup(pt, max_width=210),
                    tooltip="🚦 Travel",
                    icon=folium.DivIcon(
                        html=(f'<div style="width:9px;height:9px;border-radius:50%;'
                              f'background:{dc};border:2px solid white"></div>'),
                        icon_size=(9,9), icon_anchor=(4,4),
                    ),
                ).add_to(m)

    for _, row in df.iterrows():
        v = vi.get(row["name"])
        if v:
            di, sn, _ = v
            color = DAY_COLORS[di % len(DAY_COLORS)]
            label = str(sn)
            day_info = f"Day {di+1} · Stop {sn}"
        else:
            color = "#b0a090"; label = "·"; day_info = "Not scheduled"
        addr = str(row.get("address",""))
        ph = str(row.get("phone",""))
        pop = (f"<div style='min-width:180px'>"
               f"<div style='font-weight:700'>{row['name']}</div>"
               f"<div style='color:#888;font-size:.78rem'>⭐ {row['rating']:.1f} · {day_info}</div>"
               f"{'<div style=font-size:.74rem>📍'+addr[:55]+'</div>' if addr and 'demo' not in addr.lower() else ''}"
               f"{'<div style=font-size:.74rem>📞'+ph+'</div>' if ph else ''}</div>")
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=folium.Popup(pop, max_width=250),
            tooltip=f"{day_info} — {row['name']}",
            icon=folium.DivIcon(
                html=(f'<div style="width:22px;height:22px;border-radius:50%;background:{color};'
                      f'border:2px solid white;display:flex;align-items:center;justify-content:center;'
                      f'color:white;font-size:11px;font-weight:700;'
                      f'box-shadow:0 2px 6px rgba(0,0,0,.3)">{label}</div>'),
                icon_size=(22,22), icon_anchor=(11,11),
            ),
        ).add_to(m)

    def sm(c, ic, tip):
        folium.Marker(
            list(c), tooltip=tip,
            icon=folium.DivIcon(
                html=f'<div style="font-size:22px">{ic}</div>',
                icon_size=(30,30), icon_anchor=(15,15),
            ),
        ).add_to(m)

    if hotel_c:  sm(hotel_c,  "🏨", "Your hotel")
    if depart_c: sm(depart_c, "🚩", "Starting Point")
    if arrive_c: sm(arrive_c, "🏁", "Final Departure")
    return m

# ══════════════════════════════════════════════════════════════════
# INLINE SWAP — renders swap UI directly in the itinerary table row
# ══════════════════════════════════════════════════════════════════
def render_inline_swap(itinerary: dict, df: pd.DataFrame, day_key: str, stop_idx: int):
    """
    Show alternatives for one specific stop and let user confirm swap.
    Called when user clicks the swap button for a row.
    """
    if not WISHLIST_OK:
        st.info("swap_place_in_itinerary not available.")
        return

    stops = itinerary.get(day_key, [])
    if stop_idx >= len(stops):
        return

    cur = stops[stop_idx]
    cur_type = cur.get("type_label", "")
    used = {s["name"] for sl in itinerary.values() for s in sl}

    cands = (df[(df["type_label"] == cur_type) & (~df["name"].isin(used))]
             .sort_values("rating", ascending=False)
             .head(6))

    if cands.empty:
        st.warning("No alternatives found for this stop type.")
        return

    with st.container():
        st.markdown(
            f'<div class="swap-card"><h4>🔄 Replace: <b>{cur["name"]}</b> ({cur_type})</h4></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(min(len(cands), 3))
        for i, (_, alt_row) in enumerate(cands.iterrows()):
            with cols[i % min(len(cands), 3)]:
                nm = alt_row["name"]
                rat = alt_row.get("rating", 0)
                dist = alt_row.get("district", "")
                addr = str(alt_row.get("address",""))[:40]
                key = f"swap_confirm_{day_key}_{stop_idx}_{nm[:10]}"
                st.markdown(
                    f"**{nm}**  <br />"
                    f"⭐ {rat:.1f} · {dist}  <br />"
                    f"{'📍 '+addr if addr and 'demo' not in addr.lower() else ''}",
                )
                if st.button(f"✅ Use this", key=key, use_container_width=True):
                    new_it = swap_place_in_itinerary(
                        st.session_state.get("_itin", itinerary),
                        day_key, stop_idx, alt_row.to_dict(),
                    )
                    st.session_state["_itin"] = new_it
                    # Clear the swap panel state
                    swap_state_key = f"_swap_open_{day_key}_{stop_idx}"
                    st.session_state.pop(swap_state_key, None)
                    st.success(f"✅ Replaced with **{nm}**!")
                    st.rerun()

        if st.button("✖ Cancel", key=f"swap_cancel_{day_key}_{stop_idx}"):
            swap_state_key = f"_swap_open_{day_key}_{stop_idx}"
            st.session_state.pop(swap_state_key, None)
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# TABLE with per-row swap buttons
# ══════════════════════════════════════════════════════════════════
def render_table(df, itinerary, day_budgets, country, city=""):
    if isinstance(day_budgets, int):
        day_budgets = [day_budgets] * 30

    stop_map = {}
    if itinerary:
        for di, (dl, stops) in enumerate(itinerary.items()):
            for si, s in enumerate(stops):
                stop_map[s["name"]] = (di, si, dl, s)  # note: si is 0-based index

    n2r = {row["name"]: row for _, row in df.iterrows()}
    scheduled = []
    if itinerary:
        for di, (dl, stops) in enumerate(itinerary.items()):
            for si, s in enumerate(stops):
                if s["name"] in n2r:
                    scheduled.append((di, si, dl, s["name"]))

    snames = {x[3] for x in scheduled}
    unscheduled = [row for _, row in df.iterrows() if row["name"] not in snames]

    # Render day by day with inline swap
    seq = 0
    cur_day = -1
    current_itin = st.session_state.get("_itin", itinerary)

    for di, si, dl, nm in scheduled:
        seq += 1
        row = n2r[nm]
        color = DAY_COLORS[di % len(DAY_COLORS)]
        d_usd = day_budgets[di] if di < len(day_budgets) else day_budgets[-1]

        # Day header
        if di != cur_day:
            cur_day = di
            day_stops = list((current_itin or {}).get(f"Day {di+1}", []))
            em, lb, _, __ = budget_level(d_usd)
            st.markdown(
                f'<div style="background:#fdf3e3;border-left:4px solid {color};'
                f'padding:10px 14px;margin:14px 0 4px;border-radius:0 8px 8px 0;'
                f'font-weight:700;color:#8b5e2a">'
                f'Day {di+1}  ·  {len(day_stops)} stops  '
                f'<span class="budget-pill">{em} ${d_usd}/day</span></div>',
                unsafe_allow_html=True,
            )

        # Row container
        stop_data = stop_map.get(nm)
        sd = stop_data[3] if stop_data else {}
        swap_key = f"_swap_open_Day {di+1}_{si}"

        with st.container():
            # Main row
            c_num, c_info, c_transport, c_swap = st.columns([1, 5, 3, 1])

            with c_num:
                st.markdown(
                    f'<div style="text-align:center;padding-top:8px">'
                    f'<div style="width:28px;height:28px;border-radius:50%;background:{color};'
                    f'color:#fff;font-weight:700;font-size:12px;display:inline-flex;'
                    f'align-items:center;justify-content:center;margin:0 auto">{si+1}</div>'
                    f'<div style="color:#999;font-size:.72rem;margin-top:2px">'
                    f'{sd.get("time_slot","") if sd else ""}</div></div>',
                    unsafe_allow_html=True,
                )

            with c_info:
                tl = row.get("type_label","") or row.get("type","")
                rat = row.get("rating", 0)
                desc = row.get("description","")
                addr = str(row.get("address",""))
                ph = str(row.get("phone",""))
                _, cost_str = cost_estimate(tl, d_usd, country) if tl else (0,"")

                info_html = (
                    f'<div style="padding:6px 0">'
                    f'<div style="font-weight:700;font-size:.9rem">{nm}</div>'
                    f'<div style="color:#888;font-size:.76rem">'
                    f'{tl}{"  ·  ⭐ "+str(rat) if rat else ""}{"  ·  "+row.get("district","") if row.get("district") else ""}</div>'
                )
                if desc:
                    info_html += f'<div style="color:#aaa;font-size:.74rem">{desc}</div>'
                if cost_str:
                    info_html += f'<div style="color:#c97d35;font-size:.74rem">💰 {cost_str}</div>'
                if addr and "demo" not in addr.lower():
                    info_html += f'<div style="color:#888;font-size:.73rem">📍 {addr[:60]}</div>'
                if ph:
                    info_html += f'<div style="color:#888;font-size:.73rem">📞 {ph}</div>'
                info_html += '</div>'
                st.markdown(info_html, unsafe_allow_html=True)

            with c_transport:
                tr = sd.get("transport_to_next") if sd else None
                if tr:
                    dk = tr.get("distance_km", 0) or 0
                    _, tcost = transport_cost_estimate(dk, d_usd, country)
                    ti = tr.get("transit_info","")
                    st.markdown(
                        f'<div style="font-size:.8rem;padding:6px 0">'
                        f'<div style="font-weight:600">{tr["mode"]}</div>'
                        f'<div style="color:#888">⏱ {tr["duration"]} · 📏 {dk} km</div>'
                        f'<div style="color:#c97d35">💸 {tr.get("cost_str", tcost)}</div>'
                        f'{"<div style=color:#999;font-size:.72rem>"+ti+"</div>" if ti else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    et = sd.get("end_transport") if sd else None
                    if et:
                        st.markdown(
                            f'<div style="font-size:.8rem;color:#888;padding:6px 0">'
                            f'{et["mode"]}<br>→ {et.get("to_label","End")}'
                            f'{"  · "+et.get("duration","") if et.get("duration") else ""}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="font-size:.76rem;color:#bbb;padding:6px 0">'
                            f'{_t("last_stop")}</div>',
                            unsafe_allow_html=True,
                        )

            with c_swap:
                swap_open = st.session_state.get(swap_key, False)
                btn_label = "✖" if swap_open else "🔄"
                btn_help = "Cancel swap" if swap_open else "Swap this stop"
                if st.button(btn_label, key=f"swapbtn_{di}_{si}",
                             help=btn_help, use_container_width=True):
                    st.session_state[swap_key] = not swap_open
                    st.rerun()

        # Swap panel (shown below the row when open)
        if st.session_state.get(swap_key, False):
            render_inline_swap(current_itin, df, f"Day {di+1}", si)

        st.markdown('<hr style="margin:2px 0;border:none;border-top:1px solid #f0e8d8">',
                    unsafe_allow_html=True)

    # Meal suggestions
    if MEAL_OK and itinerary:
        avg_usd = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
        for di, (dl, stops) in enumerate(itinerary.items()):
            if not stops: continue
            d_usd = day_budgets[di] if di < len(day_budgets) else avg_usd
            st.markdown(render_meal_panel(city, di, d_usd, country, LANG, di*7+42),
                        unsafe_allow_html=True)

    # Must-see / AI recommendations
    render_ai_recommendations(city, country,
                               len(itinerary) if itinerary else 3,
                               list(PTYPES.keys()), LANG)

    if unscheduled:
        _render_extra(unscheduled, day_budgets, country)

# ══════════════════════════════════════════════════════════════════
# EXTRA RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════
def _render_extra(unscheduled, day_budgets, country):
    avg = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    CATS = [
        ("🌿 Nature",    ["🌿 Park"]),
        ("🏛️ Sights",   ["🏛️ Attraction"]),
        ("🍜 Dining",    ["🍜 Restaurant","☕ Café"]),
        ("🛍️ Shopping", ["🛍️ Shopping"]),
        ("🍺 Nightlife", ["🍺 Bar/Nightlife"]),
        ("🏨 Hotels",    ["🏨 Hotel"]),
    ]
    by_type = {}
    for r in unscheduled:
        tl = r.get("type_label","") or r.get("type","")
        by_type.setdefault(tl, []).append(r)

    cat_data = []; covered = set()
    for cn, tls in CATS:
        items = []
        for tl in tls: items.extend(by_type.get(tl, []))
        for tl in tls: covered.add(tl)
        if items: cat_data.append((cn, items))

    others = [r for tl, rs in by_type.items() if tl not in covered for r in rs]
    if others: cat_data.append(("✨ Other", others))
    if not cat_data: return

    st.markdown(f'<div class="sec-head">{_t("rec_heading")}</div>', unsafe_allow_html=True)
    st.caption(_t("rec_caption"))

    import random as _r
    for cn, places in cat_data:
        sk = f"_rec_{cn}"
        if sk not in st.session_state: st.session_state[sk] = 0
        c1, c2 = st.columns([6, 1])
        with c1:
            st.markdown(
                f'<div style="font-weight:600;margin:10px 0 4px">{cn} '
                f'<span style="color:#bbb;font-size:.78rem">({min(10,len(places))}/{len(places)})</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button(_t("rec_refresh"), key=f"_rf_{cn}"):
                st.session_state[sk] = (st.session_state[sk]+1) % 9999

        _r.seed(st.session_state[sk])
        picks = sorted(_r.sample(places, min(10, len(places))),
                       key=lambda r: r.get("rating",0), reverse=True)

        cards = ""
        for p in picks:
            nm = str(p.get("name",""))
            tl = str(p.get("type_label","") or p.get("type",""))
            rat = p.get("rating",0)
            dist = str(p.get("district","") or "—")
            addr = str(p.get("address","") or "")[:55]
            ph = str(p.get("phone","") or "")
            _, cs = cost_estimate(tl, avg, country)
            addr_h = (f'<div style="font-size:.74rem;color:#999">📍 {addr}</div>'
                      if addr and "demo" not in addr.lower() else "")
            ph_h = f'<div style="font-size:.74rem;color:#999">📞 {ph}</div>' if ph else ""
            cards += (
                f'<div class="rec-card">'
                f'<div class="rc-name">{nm}</div>'
                f'<div class="rc-meta">{tl} · {dist}</div>'
                f'{addr_h}{ph_h}'
                f'<div style="margin-top:6px;display:flex;justify-content:space-between">'
                f'<div style="font-size:.78rem">{"⭐"+str(rat) if rat else "—"}</div>'
                f'<div style="font-size:.75rem;color:#c97d35">💰 {cs}</div></div>'
                f'<span class="rc-badge">{tl.split()[0] if tl else ""}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="rec-grid">{cards}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BUDGET SUMMARY
# ══════════════════════════════════════════════════════════════════
def render_budget_summary(itinerary, day_budgets, country, days):
    if not itinerary: return
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*days
    sym, rate = _local_rate(country)
    tots = []
    for di, (dl, stops) in enumerate(itinerary.items()):
        if not stops: continue
        du = day_budgets[di] if di < len(day_budgets) else day_budgets[-1]
        t = sum(
            cost_estimate(s.get("type_label",""), du, country)[0]
            + transport_cost_estimate(
                (s.get("transport_to_next") or {}).get("distance_km",0) or 0, du, country)[0]
            for s in stops
        )
        tots.append((dl, t, du))
    if not tots: return

    st.markdown(f'<div class="sec-head">{_t("budget_heading")}</div>', unsafe_allow_html=True)
    gt = sum(t for _,t,_ in tots); gb = sum(d for _,_,d in tots)
    nc = min(len(tots), 4) + 1; cols = st.columns(nc); any_over = False

    for i, (dl, t, du) in enumerate(tots):
        with cols[i % (nc-1)]:
            over = t > du * 1.1
            if over: any_over = True
            em, lb, _, __ = budget_level(du)
            lo_u = round(t*.8); hi_u = round(t*1.2)
            rng = (f"${lo_u}–${hi_u}" if country=="US"
                   else f"${lo_u}–${hi_u} ({sym}{round(lo_u*rate)}–{sym}{round(hi_u*rate)})")
            st.markdown(
                f'<div class="bsum-card">'
                f'<div class="day-lbl">{dl}</div>'
                f'<div class="day-amt">${round(t)}{"🔴" if over else ""}</div>'
                f'<div class="day-rng">{rng}</div>'
                f'<div class="day-bud">{em} {lb} · ${du}/day</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with cols[-1]:
        lo = round(gt*.8); hi = round(gt*1.2)
        gs = (f"${lo}–${hi}" if country=="US"
              else f"${lo}–${hi} ({sym}{round(lo*rate)}–{sym}{round(hi*rate)})")
        st.markdown(
            f'<div class="bsum-card" style="background:#fff7ed;border:1px solid #e8a558">'
            f'<div class="day-lbl">{_t("budget_total")}</div>'
            f'<div class="day-amt" style="font-size:1.5rem">${round(gt)}</div>'
            f'<div class="day-rng">{gs}</div>'
            f'<div class="day-bud">{days}d · ${gb} total</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if any_over:
        st.markdown(
            f'<div style="background:#fff3cd;border-radius:8px;padding:10px;'
            f'margin-top:8px;font-size:.85rem">{_t("budget_over")}</div>',
            unsafe_allow_html=True,
        )
    with st.expander(_t("budget_breakdown")):
        rows = []
        for di, (dl, stops) in enumerate(itinerary.items()):
            if not stops: continue
            du = day_budgets[di] if di < len(day_budgets) else day_budgets[-1]
            for s in stops:
                tl = s.get("type_label",""); _, cr = cost_estimate(tl, du, country)
                rows.append({"Day":dl,"Place":s.get("name",""),"Type":tl,
                              "Budget":f"${du}/day","Est.":cr})
                tr = s.get("transport_to_next") or {}
                if tr:
                    dk = tr.get("distance_km",0) or 0
                    _, tr2 = transport_cost_estimate(dk, du, country)
                    rows.append({"Day":dl,"Place":f"→ {tr.get('mode','')}",
                                 "Type":"Transport","Budget":f"${du}/day","Est.":tr2})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════
# TRANSPORT COMPARISON
# ══════════════════════════════════════════════════════════════════
def render_transport_details(itinerary, country, city, day_budgets):
    if not TRANSPORT_OK or not itinerary: return
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*30
    with st.expander(_t("transport_comparison"), expanded=False):
        for di, (dl, stops) in enumerate(itinerary.items()):
            if len(stops) < 2: continue
            du = day_budgets[di] if di < len(day_budgets) else 60
            st.markdown(f"**{dl}**")
            for si in range(len(stops)-1):
                a, b = stops[si], stops[si+1]
                st.markdown(
                    render_transport_comparison(
                        a["lat"], a["lon"], b["lat"], b["lon"],
                        a["name"], b["name"],
                        country=country, city=city, daily_usd=du, lang=LANG,
                    ),
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════════
# COLLAB
# ══════════════════════════════════════════════════════════════════
def render_collab_panel():
    if not AUTH_OK: return
    user = _cur_user()
    if not user:
        with st.expander(_t("collab_heading"), expanded=False):
            st.caption(_t("auth_login_required"))
        return
    with st.expander(_t("collab_heading"), expanded=False):
        uname = user["username"]
        if st.button(_t("collab_share_link"), key="cb_gen"):
            import uuid as _uu
            tok = create_collab_link(uname, str(_uu.uuid4())[:8])
            st.session_state["_collab_tok"] = tok
        if "_collab_tok" in st.session_state:
            st.success(f"Share Code: **{st.session_state['_collab_tok']}**")
        st.markdown("---")
        jc = st.text_input("Join code", key="cb_jc", placeholder="ABC123XY")
        if st.button("🤝 Join", key="cb_jb"):
            ok, msg = join_collab(uname, jc)
            (st.success if ok else st.error)(msg)

# ══════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════
def build_pdf(itinerary, city, day_budgets, country):
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*30
    avg = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    DC = ["#c97d35","#3a8fd4","#3aaa7a","#9b59b6","#e05c3a","#1abc9c","#e91e63","#f39c12"]
    def cl(s): return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    _, lb, _, __ = budget_level(avg)
    total_stops = sum(len(v) for v in itinerary.values() if v)
    mjs = []; pjs = []; mlats = []; mlons = []
    for di, (dl, stops) in enumerate(itinerary.items()):
        if not stops: continue
        c = DC[di % len(DC)]; pc = []
        for si, s in enumerate(stops):
            lat = s.get("lat",0); lon = s.get("lon",0)
            if not lat or not lon: continue
            mlats.append(lat); mlons.append(lon); pc.append(f"[{lat},{lon}]")
            nm = (s.get("name","") or "").replace('"','\\"').replace("'","\\'")
            mjs.append(f'{{"lat":{lat},"lon":{lon},"n":"{nm}","d":{di+1},"s":{si+1},"c":"{c}"}}')
        if len(pc) > 1:
            pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')
    clat = sum(mlats)/len(mlats) if mlats else 35.
    clon = sum(mlons)/len(mlons) if mlons else 139.
    days_h = ""
    for di, (dl, stops) in enumerate(itinerary.items()):
        if not stops: continue
        du = day_budgets[di] if di < len(day_budgets) else day_budgets[-1]
        c = DC[di % len(DC)]; rows = ""
        for si, s in enumerate(stops):
            tr = s.get("transport_to_next") or {}
            route = f"{tr.get('mode','—')} · {tr.get('duration','')}" if tr else "Last stop"
            rows += (f"<tr><td>{si+1}</td><td>{cl(s.get('time_slot','—'))}</td>"
                     f"<td>{cl(s.get('name',''))}</td><td>{cl(s.get('type_label',''))}</td>"
                     f"<td>{cl(s.get('district',''))}</td>"
                     f"<td>{'⭐'+str(s.get('rating',0)) if s.get('rating') else '—'}</td>"
                     f"<td>{cl(route)}</td></tr>")
        days_h += (f"<h3 style='color:{c}'>{cl(dl)} — {len(stops)} stops · ${du}/day</h3>"
                   f"<table style='width:100%;border-collapse:collapse;font-size:.85rem'>"
                   f"<thead><tr style='background:#f5ede0'><th>#</th><th>Time</th>"
                   f"<th>Place</th><th>Type</th><th>District</th>"
                   f"<th>Rating</th><th>Route</th></tr></thead>"
                   f"<tbody>{rows}</tbody></table>")
    html = (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<title>Itinerary — {cl(city.title())}</title>'
            f'<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>'
            f'<style>body{{font-family:"Segoe UI",sans-serif;max-width:900px;margin:0 auto;padding:20px}}'
            f'h1{{color:#c97d35}}table td,th{{padding:6px 10px;border:1px solid #eee;text-align:left}}'
            f'#map{{height:400px;border-radius:12px;margin:20px 0}}</style></head><body>'
            f'<h1>✈ {cl(city.title())}</h1>'
            f'<p style="background:#fff7ed;border-radius:8px;padding:10px">'
            f'${sum(day_budgets)} total · {len(itinerary)} days · {total_stops} stops · '
            f'avg ${avg}/day · {lb}</p>'
            f'<div id="map"></div>{days_h}'
            f'<p style="color:#bbb;font-size:.78rem;margin-top:32px">'
            f'Generated by Trip Planner · 💡 Ctrl+P → Save as PDF</p>'
            f'<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
            f'<script>var m=L.map("map").setView([{clat},{clon}],13);'
            f'L.tileLayer("https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png",'
            f'{{attribution:"CartoDB"}}).addTo(m);'
            f'[{",".join(mjs)}].forEach(function(mk){{'
            f'var ic=L.divIcon({{html:"<div style=\\"width:22px;height:22px;border-radius:50%;'
            f'background:"+mk.c+";border:2px solid white;display:flex;align-items:center;'
            f'justify-content:center;color:white;font-size:11px;font-weight:700\\">"+mk.s+"</div>",'
            f'iconSize:[22,22],iconAnchor:[11,11]}});'
            f'L.marker([mk.lat,mk.lon],{{icon:ic}})'
            f'.bindPopup("<b>"+mk.n+"</b><br>Day "+mk.d+" Stop "+mk.s).addTo(m);}});'
            f'[{",".join(pjs)}].forEach(function(pl){{'
            f'L.polyline(pl.pts,{{color:pl.c,weight:3.5,opacity:.75,dashArray:"7 4"}}).addTo(m);}});'
            f'</script></body></html>')
    return html.encode("utf-8")

def build_calendar_urls(itinerary, start_date_str, city):
    import urllib.parse
    from datetime import datetime, timedelta
    try:
        bd = datetime.strptime(start_date_str, "%Y-%m-%d")
    except Exception:
        bd = None
    SM = {"9:00 AM":(9,0),"10:30 AM":(10,30),"12:00 PM":(12,0),"1:30 PM":(13,30),
          "3:00 PM":(15,0),"4:30 PM":(16,30),"6:00 PM":(18,0),"7:30 PM":(19,30),"9:00 PM":(21,0)}
    out = []
    for di, (dl, stops) in enumerate(itinerary.items()):
        for si, s in enumerate(stops):
            nm = s.get("name","Stop"); addr = s.get("address","") or city
            hh, mm = SM.get(s.get("time_slot","9:00 AM"), (9,0))
            ds = ""
            if bd:
                dd = bd + timedelta(days=di)
                st2 = dd.replace(hour=hh, minute=mm, second=0)
                et = st2 + timedelta(hours=1, minutes=30)
                ds = f"{st2.strftime('%Y%m%dT%H%M%S')}/{et.strftime('%Y%m%dT%H%M%S')}"
            p = {"action":"TEMPLATE","text":f"{nm} ({city.title()})","location":addr[:100],
                 "details":f"{city.title()} · {dl} Stop {si+1}"}
            if ds: p["dates"] = ds
            out.append({"day":dl,"stop":si+1,"name":nm,
                        "url":"https://calendar.google.com/calendar/render?"
                              +urllib.parse.urlencode(p)})
    return out

def render_export_panel(itinerary, city, day_budgets, country):
    if not itinerary or not any(itinerary.values()): return
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*30
    st.markdown(f'<div class="sec-head">{_t("export_heading")}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{_t('export_download')}**")
        try:
            data = build_pdf(itinerary, city, day_budgets, country)
            st.download_button(
                _t("export_download_btn"), data=data,
                file_name=f"itinerary_{city.lower().replace(' ','_')}.html",
                mime="text/html", use_container_width=True,
            )
            st.caption(_t("export_caption"))
        except Exception as e:
            st.error(_t("err_export_failed", err=str(e)))
    with c2:
        st.markdown(f"**{_t('export_calendar')}**")
        sd = st.date_input(_t("export_date"), key="exp_date", label_visibility="collapsed")
        ss = sd.strftime("%Y-%m-%d") if sd else ""
        urls = build_calendar_urls(itinerary, ss, city)
        if urls:
            dseen = {}
            for it in urls: dseen.setdefault(it["day"],[]).append(it)
            for dl, items in dseen.items():
                with st.expander(f"📅 {dl} ({len(items)} events)", expanded=False):
                    for it in items:
                        st.markdown(
                            f'<a href="{it["url"]}" target="_blank" '
                            f'style="text-decoration:none;color:#3a8fd4">'
                            f'➕ Stop {it["stop"]}: {it["name"][:32]}</a>',
                            unsafe_allow_html=True,
                        )

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # Language selector
    lang_disp = st.selectbox(
        "🌐 Language / 语言",
        ["EN — English", "ZH — 中文"],
        index=0 if LANG == "EN" else 1,
        key="lang_sel",
    )
    LANG = "ZH" if lang_disp.startswith("ZH") else "EN"
    if I18N_OK:
        def _t(key, **kw): return _ti(key, LANG, **kw)

    # Auth
    if AUTH_OK:
        with st.expander("👤 Account", expanded=False):
            render_auth_sidebar()

    st.markdown("---")
    st.markdown(f"### {_t('where_heading')}")

    all_c = sorted(WORLD_CITIES.keys())
    prev_c = st.session_state.get("sel_country","")
    sel_country = st.selectbox(
        _t("pick_country"), [""] + all_c,
        index=([""] + all_c).index(prev_c) if prev_c in all_c else 0,
        key="sel_country",
    )
    if sel_country:
        co = WORLD_CITIES.get(sel_country, [])
        pc = st.session_state.get("sel_city_name","")
        sel_city = st.selectbox(
            _t("pick_city"), co,
            index=co.index(pc) if pc in co else 0,
            key="sel_city_name",
        )
    else:
        sel_city = ""

    city_ov = st.text_input(
        _t("city_override"), "",
        placeholder=_t("city_placeholder"), key="city_override",
    )
    if city_ov.strip():   city_input = city_ov.strip()
    elif sel_city:        city_input = sel_city
    elif sel_country:     city_input = sel_country
    else:                 city_input = "Tokyo"

    city_key  = city_input.strip().lower()
    is_cn     = city_key in CN_CITIES
    intl_d    = INTL_CITIES.get(city_key)
    if is_cn:      city_lat, city_lon = CN_CITIES[city_key]; country = "CN"
    elif intl_d:   city_lat, city_lon, country = intl_d[0], intl_d[1], intl_d[2]
    else:          city_lat = city_lon = None; country = COUNTRY_CODES.get(sel_country,"INT")

    hotel_addr  = st.text_input(_t("hotel_label"),  "", placeholder=_t("hotel_placeholder"))
    depart_addr = st.text_input(_t("depart_label"), "", placeholder=_t("depart_placeholder"))
    arrive_addr = st.text_input(_t("arrive_label"), "", placeholder=_t("arrive_placeholder"))
    st.markdown("---")

    st.markdown(f"### {_t('plan_heading')}")
    days  = st.number_input(_t("how_many_days"), min_value=1, max_value=10, value=3, step=1)
    ndays = int(days)

    st.markdown(
        f'<div style="font-size:.85rem;color:#888;margin-bottom:4px">{_t("what_todo")}</div>',
        unsafe_allow_html=True,
    )
    sel_types = st.multiselect(
        "place_types",
        list(PTYPES.keys()),
        default=["🏛️ Attraction","🍜 Restaurant"],
        label_visibility="collapsed",
    )
    if not sel_types: sel_types = ["🏛️ Attraction"]

    # Districts
    dk = f"dists_{city_key}"
    if dk not in st.session_state:
        if is_cn:
            with st.spinner(_t("loading_districts") + " " + city_input):
                st.session_state[dk] = _amap_get_districts(city_input)
        else:
            st.session_state[dk] = []

    amap_dists = st.session_state.get(dk, [])
    adcode_map: dict = {}; center_map: dict = {}
    for d in amap_dists:
        n, a, la, lo = d.get("name",""), d.get("adcode",""), d.get("lat"), d.get("lon")
        if n and a: adcode_map[n] = a
        if n and la is not None: center_map[n] = (la, lo)

    if is_cn and amap_dists:
        pdo = ["Auto (city-wide)"] + [d["name"] for d in amap_dists]
    elif intl_d and len(intl_d) > 3:
        pdo = ["Auto (city-wide)"] + intl_d[3]
    else:
        dnk = f"dyn_{city_key}"
        if dnk not in st.session_state and city_lat:
            with st.spinner(_t("loading_neighbourhoods")):
                st.session_state[dnk] = _get_nominatim_districts(city_input)
        dyn = st.session_state.get(dnk, [])
        pdo = (["Auto (city-wide)"] + dyn) if dyn else ["Auto (city-wide)"]

    st.markdown(f'<div class="sec-head">{_t("day_prefs_heading")}</div>',
                unsafe_allow_html=True)
    st.caption(_t("day_prefs_caption"))

    day_quotas=[]; day_adcodes=[]; day_district_names=[]
    day_anchor_lats=[]; day_anchor_lons=[]; day_min_ratings=[]; day_budgets=[]

    if ndays <= 7:
        tabs = st.tabs([f"D{d+1}" for d in range(ndays)])
        for di, tab in enumerate(tabs):
            with tab:
                ds = st.selectbox(
                    _t("area_label"), pdo,
                    key=f"da_{di}", label_visibility="collapsed",
                )
                auto = (ds == "Auto (city-wide)")
                if auto:
                    day_adcodes.append(""); day_district_names.append("")
                    day_anchor_lats.append(city_lat); day_anchor_lons.append(city_lon)
                else:
                    day_adcodes.append(adcode_map.get(ds,""))
                    day_district_names.append(ds)
                    dlat, dlon = center_map.get(ds, (city_lat, city_lon))
                    day_anchor_lats.append(dlat); day_anchor_lons.append(dlon)

                mr = st.slider(_t("min_rating_label"), 0., 5., 3.5, .5, key=f"mr_{di}")
                day_min_ratings.append(mr)

                du = st.slider(_t("daily_budget_label"), 10, 500, 60, 5,
                               format="$%d", key=f"bud_{di}")
                cr = fmt_currency_row(du, country)
                lp = cr.split("≈",1)[-1].strip() if "≈" in cr else ""
                st.markdown(
                    f'<div class="budget-pill">${du}/day'
                    + (f'  ≈ {lp}' if lp else '') + '</div>',
                    unsafe_allow_html=True,
                )
                day_budgets.append(du)

                quota = {}
                for tl in sel_types:
                    n = st.slider(tl, 0, 5, 1, 1, key=f"q_{di}_{tl}")
                    if n > 0: quota[tl] = n
                if not quota: quota = {sel_types[0]: 1}
                day_quotas.append(quota)
    else:
        ds = st.selectbox(_t("all_area_label"), pdo, key="da_all",
                          label_visibility="collapsed")
        auto = (ds == "Auto (city-wide)")
        _adc = "" if auto else adcode_map.get(ds,"")
        _dn  = "" if auto else ds
        _alat, _alon = center_map.get(ds, (city_lat, city_lon)) if not auto else (city_lat, city_lon)
        day_adcodes = [_adc]*ndays; day_district_names = [_dn]*ndays
        day_anchor_lats = [_alat]*ndays; day_anchor_lons = [_alon]*ndays

        mr = st.slider(_t("min_rating_label"), 0., 5., 3.5, .5, key="mr_all")
        day_min_ratings = [mr]*ndays

        du = st.slider(_t("daily_budget_label"), 10, 500, 60, 5, format="$%d", key="bud_all")
        cr = fmt_currency_row(du, country)
        lp = cr.split("≈",1)[-1].strip() if "≈" in cr else ""
        st.markdown(
            f'<div class="budget-pill">${du}/day' + (f'  ≈ {lp}' if lp else '') + '</div>',
            unsafe_allow_html=True,
        )
        day_budgets = [du]*ndays

        quota = {}
        for tl in sel_types:
            n = st.slider(tl, 0, 5, 1, 1, key=f"qa_{tl}")
            if n > 0: quota[tl] = n
        if not quota: quota = {sel_types[0]: 1}
        day_quotas = [dict(quota)]*ndays

    total_quota = sum(sum(q.values()) for q in day_quotas) if day_quotas else 4
    lpt = max(30, total_quota * 6)
    daily_usd = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60

    st.markdown("---")
    if "seed" not in st.session_state: st.session_state.seed = 42
    gen = st.button(_t("build_btn"), use_container_width=True)
    ref = st.button(_t("refresh_btn"), use_container_width=True)
    if ref:
        st.session_state.seed = random.randint(1, 99999)
        st.cache_data.clear(); gen = True

    # Wishlist + Points
    user = _cur_user()
    if user and WISHLIST_OK:
        with st.expander(_t("wishlist_heading"), expanded=False):
            render_wishlist_panel(user["username"], LANG)
    if user and POINTS_OK:
        with st.expander(_t("points_heading"), expanded=False):
            render_points_panel(user["username"], LANG)

    st.markdown("---")
    api_src = "高德地图 (Amap)" if is_cn else "Overpass OSM"
    amap_status = "✅ Key loaded" if AMAP_KEY else "⚠️ No key (demo mode)"
    st.caption(f"{_t('data_source')}: {api_src}  ·  {amap_status}")

# ══════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════
st.markdown(
    f'<div class="hero-box">'
    f'<h1>{_t("hero_title")}</h1>'
    f'<p>{_t("hero_subtitle")}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# MAIN DISPLAY FUNCTION
# ══════════════════════════════════════════════════════════════════
def _run_display(it, df, ci, nd, bud, ctr, tys, lat, lon, hc, dc, ac):
    real  = sum(len(v) for v in it.values()) if it else 0
    avg_r = df["rating"].replace(0, float("nan")).mean()
    du    = round(sum(bud)/len(bud)) if bud else 60
    bstr  = f"${sum(bud)}" if len(set(bud)) > 1 else f"${du}/day"

    for c, (lbl, val) in zip(st.columns(5), [
        (_t("metric_places"), str(len(df))),
        (_t("metric_days"),   str(nd)),
        (_t("metric_stops"),  str(real)),
        (_t("metric_rating"), f"{avg_r:.1f}" if not math.isnan(avg_r) else "—"),
        (_t("metric_budget"), bstr),
    ]):
        c.metric(lbl, val)

    # API key status info for CN
    if ctr == "CN":
        if AMAP_KEY:
            st.info(f"🗺️ 高德地图 API Key 已加载 ({AMAP_KEY[:8]}…) — 正在使用真实数据")
        else:
            st.warning("⚠️ 未检测到高德 API Key。请在 Streamlit Cloud → Settings → Secrets 中添加 `APIKEY`。当前显示演示数据。")

    st.markdown(
        f'<div class="sec-head">📋 {ci.title()}  ·  {" + ".join(tys)}</div>',
        unsafe_allow_html=True,
    )

    render_table(df, it, bud, ctr, ci)
    render_budget_summary(it, bud, ctr, nd)
    render_transport_details(it, ctr, ci, bud)

    st.markdown(f'<div class="map-head">{_t("map_heading")}</div>', unsafe_allow_html=True)
    st.caption(_t("map_caption"))
    try:
        m = build_map(df, lat, lon, it, hc, dc, ac)
        st_folium(m, width="100%", height=560, returned_objects=[])
    except Exception as e:
        st.error(_t("err_map_failed", err=str(e)))

    render_collab_panel()
    render_export_panel(it, ci, bud, ctr)


# ══════════════════════════════════════════════════════════════════
# GENERATE
# ══════════════════════════════════════════════════════════════════
if gen:
    # Resolve coordinates
    if is_cn:
        lat, lon = city_lat, city_lon
        if lat is None:
            c = _amap_geocode(city_input)
            if c: lat, lon = c
            else: st.error(_t("err_city_not_found", city=city_input)); st.stop()
    elif intl_d:
        lat, lon = intl_d[0], intl_d[1]
    else:
        with st.spinner(_t("finding_dest")):
            coord = _nominatim(city_input)
            if not coord: st.error(_t("err_city_not_found", city=city_input)); st.stop()
            lat, lon = coord

    hotel_c = depart_c = arrive_c = None
    with st.spinner(_t("looking_up_locations")):
        if hotel_addr:  hotel_c  = _geocode(hotel_addr,  city_input, is_cn)
        if depart_addr: depart_c = _geocode(depart_addr, city_input, is_cn)
        if arrive_addr: arrive_c = _geocode(arrive_addr, city_input, is_cn)

    with st.spinner(f"{_t('finding_places')} {city_input.title()}…"):
        try:
            df, warn = fetch_all_places(
                lat, lon, country, is_cn,
                tuple(sel_types), lpt,
                tuple(day_adcodes), tuple(day_district_names),
                tuple(day_anchor_lats), tuple(day_anchor_lons),
                st.session_state.seed,
            )
        except Exception as e:
            st.error(f"Search error: {e}"); st.stop()

    if warn: st.warning(warn)
    if df is None or df.empty: st.error(_t("err_no_places")); st.stop()

    itinerary = {}
    if not AI_OK:
        st.error(f"ai_planner error: {_AI_ERR}")
    else:
        with st.spinner(_t("building_itin")):
            try:
                itinerary = generate_itinerary(
                    df, ndays, day_quotas,
                    hotel_lat=hotel_c[0]  if hotel_c  else None,
                    hotel_lon=hotel_c[1]  if hotel_c  else None,
                    depart_lat=depart_c[0] if depart_c else None,
                    depart_lon=depart_c[1] if depart_c else None,
                    arrive_lat=arrive_c[0] if arrive_c else None,
                    arrive_lon=arrive_c[1] if arrive_c else None,
                    day_min_ratings=day_min_ratings,
                    day_anchor_lats=day_anchor_lats,
                    day_anchor_lons=day_anchor_lons,
                    country=country, city=city_input,
                    day_budgets=day_budgets,
                )
            except Exception as e:
                st.error(_t("err_itinerary_failed", err=str(e)))

    if itinerary:
        st.session_state.update({
            "_itin": itinerary, "_df": df, "_city": city_input,
            "_ndays": ndays, "_budgets": day_budgets, "_country": country,
            "_types": list(sel_types), "_lat": lat, "_lon": lon,
            "_hotel": hotel_c, "_depart": depart_c, "_arrive": arrive_c, "_lang": LANG,
        })
        user = _cur_user()
        if user and WISHLIST_OK:
            try: _save_itin(user["username"], itinerary, city_input, city_input.title())
            except Exception: pass
        if user and POINTS_OK:
            try: add_points(user["username"], "share", note=city_input)
            except Exception: pass

    _run_display(itinerary, df, city_input, ndays, day_budgets, country,
                 sel_types, lat, lon, hotel_c, depart_c, arrive_c)

elif "_itin" in st.session_state and "_df" in st.session_state:
    _run_display(
        st.session_state["_itin"],
        st.session_state["_df"],
        st.session_state.get("_city", city_input),
        st.session_state.get("_ndays", ndays),
        st.session_state.get("_budgets", day_budgets),
        st.session_state.get("_country", country),
        st.session_state.get("_types", list(sel_types)),
        st.session_state.get("_lat", city_lat or 35.),
        st.session_state.get("_lon", city_lon or 139.),
        st.session_state.get("_hotel"),
        st.session_state.get("_depart"),
        st.session_state.get("_arrive"),
    )

else:
    # Welcome state
    st.markdown("---")
    for col, (icon, title, desc) in zip(st.columns(4), [
        (_t("welcome_1_icon"), _t("welcome_1_title"), _t("welcome_1_desc")),
        (_t("welcome_2_icon"), _t("welcome_2_title"), _t("welcome_2_desc")),
        (_t("welcome_3_icon"), _t("welcome_3_title"), _t("welcome_3_desc")),
        (_t("welcome_4_icon"), _t("welcome_4_title"), _t("welcome_4_desc")),
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
Key Fixes Summary

elif "_itin" in st.session_state and "_df" in st.session_state:
    _run_display(
        st.session_state["_itin"],
        st.session_state["_df"],
        st.session_state.get("_city", city_input),
        st.session_state.get("_ndays", ndays),
        st.session_state.get("_budgets", day_budgets),
        st.session_state.get("_country", country),
        st.session_state.get("_types", list(sel_types)),
        st.session_state.get("_lat", city_lat or 35.0),
        st.session_state.get("_lon", city_lon or 139.0),
        st.session_state.get("_hotel"),
        st.session_state.get("_depart"),
        st.session_state.get("_arrive"),
    )

else:
    st.markdown("---")
    for col, (icon, title, desc) in zip(st.columns(4), [
        (_t("welcome_1_icon"), _t("welcome_1_title"), _t("welcome_1_desc")),
        (_t("welcome_2_icon"), _t("welcome_2_title"), _t("welcome_2_desc")),
        (_t("welcome_3_icon"), _t("welcome_3_title"), _t("welcome_3_desc")),
        (_t("welcome_4_icon"), _t("welcome_4_title"), _t("welcome_4_desc")),
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
