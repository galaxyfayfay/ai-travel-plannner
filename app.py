import streamlit as st
import requests
import math
import random
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
import re
from datetime import datetime, timedelta

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── MUST be defined BEFORE use ──────────────────────────────────
def _get_secret(key: str) -> str:
    try:
        val = st.secrets.get(key, "")
        if val: return str(val)
    except Exception:
        pass
    return os.getenv(key, "")

# Now safe to call
AMAP_KEY     = _get_secret("APIKEY")
DEEPSEEK_KEY = _get_secret("DEEPSEEKKEY")
        

# ══════════════════════════════════════════════════════════════════
# LANG
# ══════════════════════════════════════════════════════════════════
if "lang_sel" not in st.session_state:
    st.session_state["lang_sel"] = "EN"
LANG = "ZH" if st.session_state.get("lang_sel","EN") == "ZH" else "EN"

# ══════════════════════════════════════════════════════════════════
# i18n
# ══════════════════════════════════════════════════════════════════
try:
    from i18n import t as _ti
    def _t(key, **kw): return _ti(key, LANG, **kw)
    I18N_OK = True
except Exception:
    I18N_OK = False
    def _t(key, **kw):
        FB = {
            "build_btn": "Build Itinerary",
            "refresh_btn": "Shuffle",
            "auth_login": "Sign In",
            "auth_register": "Register",
            "auth_logout": "Sign Out",
            "auth_username": "Username",
            "auth_password": "Password",
            "auth_email": "Email",
            "wishlist_heading": "Wishlist",
            "points_heading": "Points",
            "budget_heading": "Cost Estimate",
            "budget_total": "Total",
            "budget_breakdown": "Breakdown",
            "budget_over": "Some days may exceed budget.",
            "export_heading": "Export",
            "map_heading": "Route Map",
            "map_caption": "Tap markers for details",
            "transport_cmp": "Transport Options",
            "last_stop": "Last stop",
            "rec_heading": "Explore More",
            "rec_caption": "More places worth visiting.",
            "ai_rec_heading": "AI Must-See",
            "ai_rec_caption": "Famous highlights",
            "add_to_day": "Add to Day",
            "err_city_nf": "City not found: {city}",
            "err_itin_fail": "Itinerary error: {err}",
            "err_map_fail": "Map error: {err}",
            "err_no_places": "No places found.",
            "err_export_fail": "Export error: {err}",
            "collab_heading": "Collaborate",
            "auth_login_req": "Sign in to continue.",
        }
        text = FB.get(key, key)
        if kw:
            try: text = text.format(**kw)
            except Exception: pass
        return text

# ══════════════════════════════════════════════════════════════════
# MODULE IMPORTS
# ══════════════════════════════════════════════════════════════════
try:
    from ai_planner import generate_itinerary
    AI_OK = True
except Exception as _e:
    AI_OK = False; _AI_ERR = str(_e)

try:
    from transport_planner import render_transport_comparison
    TRANSPORT_OK = True
except Exception:
    TRANSPORT_OK = False

try:
    from meal_planner import render_meal_panel
    MEAL_OK = True
except Exception:
    MEAL_OK = False

try:
    from data_manager import get_must_see
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

# ── Wishlist — in-memory fallback so it ALWAYS works ──────────────
try:
    from wishlist_manager import (
        add_to_wishlist as _wl_add,
        remove_from_wishlist as _wl_remove,
        get_wishlist as _wl_get,
        is_in_wishlist as _wl_check,
        save_itinerary as _save_itin_ext,
        render_wishlist_panel as _render_wl_ext,
        swap_place_in_itinerary,
    )
    WISHLIST_EXT = True
except Exception:
    WISHLIST_EXT = False

WISHLIST_OK = True  # always available via session fallback

def _wl_key(username): return f"_wl_{username}"
def _itin_key(username): return f"_saved_itins_{username}"

def wl_add(username, place):
    if WISHLIST_EXT:
        try: _wl_add(username, place); return
        except Exception: pass
    k = _wl_key(username)
    lst = st.session_state.get(k, [])
    names = {p.get("name","") for p in lst}
    if place.get("name","") not in names:
        lst.append(place)
        st.session_state[k] = lst

def wl_remove(username, name):
    if WISHLIST_EXT:
        try: _wl_remove(username, name); return
        except Exception: pass
    k = _wl_key(username)
    lst = st.session_state.get(k, [])
    st.session_state[k] = [p for p in lst if p.get("name","") != name]

def wl_get(username):
    if WISHLIST_EXT:
        try: return _wl_get(username)
        except Exception: pass
    return st.session_state.get(_wl_key(username), [])

def wl_check(username, name):
    if WISHLIST_EXT:
        try: return _wl_check(username, name)
        except Exception: pass
    lst = st.session_state.get(_wl_key(username), [])
    return any(p.get("name","") == name for p in lst)

def save_itin(username, itinerary, city, title):
    if WISHLIST_EXT:
        try: _save_itin_ext(username, itinerary, city, title); return
        except Exception: pass
    k = _itin_key(username)
    saved = st.session_state.get(k, [])
    saved.append({"city": city, "title": title, "data": itinerary,
                  "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
    st.session_state[k] = saved[-10:]  # keep last 10

def render_wishlist_sidebar(username):
    lst = wl_get(username)
    if not lst:
        st.caption("Nothing saved yet.")
        return
    for p in lst:
        nm = p.get("name","")
        tp = p.get("type","")
        col1, col2 = st.columns([5,1])
        with col1:
            st.markdown(
                f'<div style="font-size:.8rem;font-weight:600;color:#1e1b4b">{nm}</div>'
                f'<div style="font-size:.70rem;color:#a78bfa">{tp}</div>',
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("×", key=f"wl_rm_{nm[:8]}", help="Remove"):
                wl_remove(username, nm)
                st.rerun()
    # Saved itineraries
    saved_it = st.session_state.get(_itin_key(username), [])
    if saved_it:
        st.markdown("---")
        st.caption("Saved itineraries")
        for s in saved_it[-3:]:
            st.markdown(
                f'<div style="font-size:.78rem;color:#1e1b4b">'
                f'{s.get("title","")} &nbsp;'
                f'<span style="color:#c4b5fd">{s.get("saved_at","")}</span></div>',
                unsafe_allow_html=True,
            )

try:
    from points_system import add_points, get_points, render_points_panel
    POINTS_OK = True
except Exception:
    POINTS_OK = False

# ══════════════════════════════════════════════════════════════════
# PLACE DURATION ESTIMATES (minutes)
# ══════════════════════════════════════════════════════════════════
DURATION_MAP = {
    "🏛️ Attraction": 90,
    "🍜 Restaurant":  60,
    "☕ Cafe":         45,
    "🌿 Park":         60,
    "🛍️ Shopping":   90,
    "🍺 Bar/Nightlife": 90,
    "🏨 Hotel":        20,
}

DURATION_SPECIAL = {
    # key words → minutes
    "museum":     120, "palace":    120, "castle":   120,
    "temple":      60, "shrine":     45, "cathedral": 60,
    "market":      75, "bazaar":     75, "gallery":   75,
    "park":        60, "garden":     75, "nature":    90,
    "tower":       45, "viewpoint":  30, "crossing":  20,
    "restaurant":  60, "dining":     75, "food":      60,
    "cafe":        45, "coffee":     45,
    "mall":        90, "shopping":   90, "district": 75,
    "bar":         90, "nightlife": 120, "lounge":    90,
    "beach":       90, "hot spring": 120,
    "aquarium":    90, "zoo":       120,
}

def estimate_duration(name: str, type_label: str) -> int:
    """Return estimated visit duration in minutes."""
    name_lc = (name or "").lower()
    for kw, mins in DURATION_SPECIAL.items():
        if kw in name_lc:
            return mins
    return DURATION_MAP.get(type_label, 60)

def format_duration(mins: int) -> str:
    if mins < 60: return f"{mins}min"
    h = mins // 60; m = mins % 60
    return f"{h}h {m}min" if m else f"{h}h"

def build_day_timeline(stops: list, start_hour: int = 9) -> list:
    """
    Given a list of stops (dicts), assign arrival/departure times.
    Returns enriched stops with 'arrive_time', 'depart_time', 'duration_min'.
    """
    result = []
    current_minutes = start_hour * 60  # minutes since midnight

    for i, s in enumerate(stops):
        tl   = s.get("type_label", "🏛️ Attraction")
        nm   = s.get("name", "")
        dur  = estimate_duration(nm, tl)

        # Travel time from prev stop (use transport info if available)
        if i > 0:
            tr = stops[i-1].get("transport_to_next") or {}
            travel_str = tr.get("duration", "")
            travel_min = _parse_duration_str(travel_str)
            current_minutes += travel_min
        
        # Lunch break: if arriving 12:00-13:30 and this is NOT a restaurant, add 45min buffer
        if 720 <= current_minutes <= 810 and "Restaurant" not in tl and "Cafe" not in tl:
            if i > 0:  # not first stop
                current_minutes = max(current_minutes, 780)  # push to at least 13:00

        arrive_h = current_minutes // 60
        arrive_m = current_minutes % 60
        depart_minutes = current_minutes + dur
        depart_h = depart_minutes // 60
        depart_m = depart_minutes % 60

        enriched = dict(s)
        enriched["arrive_time"]  = f"{arrive_h:02d}:{arrive_m:02d}"
        enriched["depart_time"]  = f"{depart_h:02d}:{depart_m:02d}"
        enriched["duration_min"] = dur

        result.append(enriched)
        current_minutes = depart_minutes

        # Short break between stops (15 min)
        if i < len(stops) - 1:
            current_minutes += 15

    return result

def _parse_duration_str(s: str) -> int:
    """Parse '25 min', '1 hr 10 min', '1h30m' etc → minutes."""
    if not s: return 20
    s = s.lower().strip()
    total = 0
    h = re.search(r'(\d+)\s*h', s)
    m = re.search(r'(\d+)\s*m', s)
    if h: total += int(h.group(1)) * 60
    if m: total += int(m.group(1))
    return total if total > 0 else 20

# ══════════════════════════════════════════════════════════════════
# LAVENDER GLASS CSS — simplified
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html,body,[class*="css"]{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.stApp{
  background:linear-gradient(150deg,#f5f3ff 0%,#ede9fe 40%,#faf5ff 100%) !important;
  min-height:100vh;
}
section[data-testid="stSidebar"]{
  background:rgba(255,255,255,0.75) !important;
  backdrop-filter:blur(24px) !important;
  border-right:1px solid rgba(139,92,246,0.10) !important;
}
.main .block-container{ padding:1.6rem 2rem 3rem; max-width:1060px; }

/* Glass card */
.g-card{
  background:rgba(255,255,255,0.75);
  backdrop-filter:blur(18px);
  border:1px solid rgba(255,255,255,0.90);
  border-radius:18px;
  box-shadow:0 3px 20px rgba(109,40,217,0.06);
  padding:18px;
  margin-bottom:12px;
}

/* Hero */
.hero{
  background:linear-gradient(135deg,rgba(237,233,254,.90),rgba(250,245,255,.90));
  backdrop-filter:blur(30px);
  border:1px solid rgba(255,255,255,0.92);
  border-radius:24px;
  padding:32px 30px;
  margin-bottom:20px;
  box-shadow:0 6px 32px rgba(109,40,217,0.08);
  position:relative; overflow:hidden;
}
.hero::before{
  content:'';position:absolute;top:-60px;right:-50px;
  width:200px;height:200px;
  background:radial-gradient(circle,rgba(139,92,246,.14) 0%,transparent 70%);
  border-radius:50%;pointer-events:none;
}
.hero-badge{
  display:inline-flex;align-items:center;gap:5px;
  background:rgba(139,92,246,.10);border:1px solid rgba(139,92,246,.20);
  border-radius:20px;padding:3px 12px;
  font-size:.73rem;color:#7c3aed;font-weight:600;
  letter-spacing:.04em;margin-bottom:12px;
}
.hero-title{
  font-size:2.1rem;font-weight:700;letter-spacing:-.03em;
  color:#1e1b4b;margin:0 0 6px;line-height:1.1;
}
.hero-sub{font-size:.95rem;color:#6b7280;margin:0;}

/* Section label */
.s-lbl{
  font-size:.67rem;font-weight:700;color:#a78bfa;
  text-transform:uppercase;letter-spacing:.08em;
  margin:22px 0 8px;
}

/* Day header */
.day-hdr{
  display:flex;align-items:center;gap:10px;
  padding:11px 16px;
  background:rgba(255,255,255,0.80);
  backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,0.92);
  border-radius:14px;
  margin:18px 0 6px;
  box-shadow:0 2px 10px rgba(109,40,217,0.05);
}
.day-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.day-ttl{font-weight:700;font-size:.86rem;color:#1e1b4b;flex:1;}
.day-info{font-size:.72rem;color:#9ca3af;}

/* Stop row */
.stop-row{
  background:rgba(255,255,255,0.70);
  border:1px solid rgba(255,255,255,0.88);
  border-radius:13px;
  padding:12px 14px;
  margin-bottom:6px;
}
.sn{
  width:24px;height:24px;border-radius:50%;
  display:inline-flex;align-items:center;justify-content:center;
  color:#fff;font-size:10px;font-weight:700;flex-shrink:0;
}
.stop-name{font-weight:600;font-size:.86rem;color:#1e1b4b;}
.stop-meta{font-size:.72rem;color:#9ca3af;margin-top:1px;}
.time-badge{
  display:inline-flex;align-items:center;gap:4px;
  background:rgba(139,92,246,.09);
  border:1px solid rgba(139,92,246,.16);
  border-radius:20px;padding:2px 9px;
  font-size:.70rem;color:#7c3aed;font-weight:500;
}
.dur-badge{
  display:inline-flex;align-items:center;gap:4px;
  background:rgba(245,158,11,.09);
  border:1px solid rgba(245,158,11,.18);
  border-radius:20px;padding:2px 9px;
  font-size:.70rem;color:#d97706;font-weight:500;
}
.tr-chip{
  display:inline-flex;align-items:center;gap:4px;
  background:rgba(56,189,248,.08);
  border:1px solid rgba(56,189,248,.18);
  border-radius:20px;padding:2px 8px;
  font-size:.70rem;color:#0284c7;font-weight:500;
}

/* Budget card */
.b-card{
  background:rgba(255,255,255,0.72);
  border:1px solid rgba(255,255,255,0.90);
  border-radius:14px;padding:14px;text-align:center;
  box-shadow:0 2px 10px rgba(109,40,217,0.04);
}
.b-amt{font-size:1.4rem;font-weight:700;color:#1e1b4b;letter-spacing:-.02em;}
.b-lbl{font-size:.67rem;color:#a78bfa;font-weight:600;text-transform:uppercase;
       letter-spacing:.05em;margin-bottom:5px;}
.b-sub{font-size:.69rem;color:#c4b5fd;margin-top:3px;}

/* Rec card — simpler */
.r-card{
  background:rgba(255,255,255,0.72);
  border:1px solid rgba(255,255,255,0.88);
  border-radius:13px;padding:12px 14px;
  box-shadow:0 1px 6px rgba(109,40,217,0.04);
  margin-bottom:8px;
}
.r-name{font-weight:600;font-size:.83rem;color:#1e1b4b;margin-bottom:2px;}
.r-meta{font-size:.71rem;color:#9ca3af;}
.r-cost{font-size:.70rem;color:#a78bfa;font-weight:500;margin-top:4px;}

/* AI panel */
.ai-panel{
  background:rgba(255,255,255,0.68);
  border:1px solid rgba(255,255,255,0.88);
  border-radius:16px;padding:16px;margin:10px 0;
  box-shadow:0 3px 16px rgba(109,40,217,0.05);
}
.ai-item{
  background:rgba(255,255,255,0.80);
  border-radius:10px;padding:10px 12px;margin:5px 0;
  border-left:3px solid #a78bfa;
}

/* Swap panel */
.sw-panel{
  background:rgba(255,255,255,0.68);
  border:1px solid rgba(255,255,255,0.88);
  border-radius:14px;padding:14px;margin:6px 0;
}

/* Banners */
.ok{background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.18);
    border-radius:10px;padding:8px 12px;font-size:.79rem;color:#15803d;}
.warn{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.18);
      border-radius:10px;padding:8px 12px;font-size:.79rem;color:#b45309;}
.info{background:rgba(139,92,246,.08);border:1px solid rgba(139,92,246,.18);
      border-radius:10px;padding:8px 12px;font-size:.79rem;color:#6d28d9;}

/* Sidebar */
.sb-lbl{
  font-size:.65rem;font-weight:700;color:#a78bfa;
  text-transform:uppercase;letter-spacing:.08em;margin:12px 0 5px;
}
.user-card{
  background:rgba(139,92,246,.07);
  border:1px solid rgba(139,92,246,.14);
  border-radius:12px;padding:10px 12px;
  display:flex;align-items:center;gap:9px;
  margin-bottom:8px;
}
.u-av{
  width:32px;height:32px;border-radius:50%;
  background:linear-gradient(135deg,#8b5cf6,#a78bfa);
  display:flex;align-items:center;justify-content:center;
  color:#fff;font-weight:700;font-size:.84rem;flex-shrink:0;
}
.u-name{font-weight:600;font-size:.82rem;color:#1e1b4b;}
.u-pts{font-size:.70rem;color:#a78bfa;}

/* Welcome */
.wc-grid{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px;}
.wc{
  background:rgba(255,255,255,.72);
  border:1px solid rgba(255,255,255,.90);
  border-radius:16px;padding:20px 16px;
  flex:1;min-width:140px;text-align:center;
  box-shadow:0 2px 10px rgba(109,40,217,0.04);
}
.wc-i{font-size:1.4rem;margin-bottom:8px;}
.wc-t{font-weight:700;font-size:.84rem;color:#1e1b4b;margin-bottom:3px;}
.wc-d{font-size:.74rem;color:#9ca3af;line-height:1.4;}

/* Streamlit overrides */
.stButton>button{
  border-radius:10px !important;
  font-family:'Inter',sans-serif !important;
  font-weight:500 !important;font-size:.81rem !important;
  border:1px solid rgba(139,92,246,.16) !important;
  background:rgba(255,255,255,.82) !important;
  color:#1e1b4b !important;
  transition:all .15s !important;
}
.stButton>button:hover{
  background:rgba(255,255,255,.96) !important;
  box-shadow:0 2px 12px rgba(109,40,217,.12) !important;
  border-color:rgba(139,92,246,.28) !important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#8b5cf6,#7c3aed) !important;
  color:#fff !important;border:none !important;
  box-shadow:0 3px 14px rgba(109,40,217,.28) !important;
}
.stButton>button[kind="primary"]:hover{
  box-shadow:0 5px 20px rgba(109,40,217,.36) !important;
}
.stSelectbox>div>div,
.stMultiSelect>div>div,
.stTextInput>div>div>input,
.stNumberInput>div>div>input{
  border-radius:9px !important;
  border:1px solid rgba(139,92,246,.14) !important;
  background:rgba(255,255,255,.82) !important;
  font-size:.81rem !important;color:#1e1b4b !important;
}
.stSlider>div>div>div>div{background:#8b5cf6 !important;}
.stTabs [data-baseweb="tab-list"]{
  background:rgba(255,255,255,.65) !important;
  border-radius:11px !important;padding:3px !important;
  border:1px solid rgba(255,255,255,.84) !important;
}
.stTabs [data-baseweb="tab"]{
  border-radius:8px !important;font-size:.77rem !important;
  font-weight:500 !important;padding:4px 10px !important;color:#9ca3af !important;
}
.stTabs [aria-selected="true"]{
  background:rgba(255,255,255,.92) !important;
  color:#1e1b4b !important;box-shadow:0 1px 4px rgba(109,40,217,.08) !important;
}
.stExpander{
  background:rgba(255,255,255,.68) !important;
  border:1px solid rgba(255,255,255,.88) !important;
  border-radius:12px !important;overflow:hidden !important;
}
div[data-testid="stMetric"]{
  background:rgba(255,255,255,.72) !important;
  border-radius:13px !important;padding:11px 15px !important;
  border:1px solid rgba(255,255,255,.90) !important;
  box-shadow:0 2px 8px rgba(109,40,217,.04) !important;
}
div[data-testid="stMetric"] label{
  font-size:.67rem !important;color:#a78bfa !important;
  text-transform:uppercase !important;letter-spacing:.06em !important;font-weight:600 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
  font-size:1.3rem !important;font-weight:700 !important;color:#1e1b4b !important;
}
div[data-testid="stDownloadButton"] button{
  background:rgba(139,92,246,.10) !important;color:#7c3aed !important;
  border:1px solid rgba(139,92,246,.20) !important;border-radius:10px !important;
}
.stAlert{border-radius:11px !important;border:none !important;}
.stCaption{color:#c4b5fd !important;font-size:.71rem !important;}
hr{border:none;border-top:1px solid rgba(139,92,246,.09) !important;margin:14px 0 !important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
BUDGET_LEVELS = [(0,30,"Economy","#16a34a"),(30,80,"Standard","#d97706"),
                 (80,200,"Comfort","#dc2626"),(200,9999,"Luxury","#7c3aed")]
def budget_level(usd):
    for lo,hi,lb,bc in BUDGET_LEVELS:
        if usd<hi: return lb,bc
    return "Luxury","#7c3aed"

CURRENCIES = {
    "CN":[("USD","$",1.0),("CNY","CNY ",7.25)],
    "JP":[("USD","$",1.0),("JPY","JPY ",155)],
    "KR":[("USD","$",1.0),("KRW","KRW ",1350)],
    "TH":[("USD","$",1.0),("THB","THB ",36)],
    "SG":[("USD","$",1.0),("SGD","SGD ",1.35)],
    "FR":[("USD","$",1.0),("EUR","EUR ",0.92)],
    "GB":[("USD","$",1.0),("GBP","GBP ",0.79)],
    "IT":[("USD","$",1.0),("EUR","EUR ",0.92)],
    "ES":[("USD","$",1.0),("EUR","EUR ",0.92)],
    "US":[("USD","$",1.0)],
    "AU":[("USD","$",1.0),("AUD","AUD ",1.53)],
    "AE":[("USD","$",1.0),("AED","AED ",3.67)],
    "NL":[("USD","$",1.0),("EUR","EUR ",0.92)],
    "TR":[("USD","$",1.0),("TRY","TRY ",32)],
    "HK":[("USD","$",1.0),("HKD","HKD ",7.82)],
    "TW":[("USD","$",1.0),("TWD","TWD ",32)],
    "ID":[("USD","$",1.0),("IDR","IDR ",16000)],
    "VN":[("USD","$",1.0),("VND","VND ",25000)],
    "MY":[("USD","$",1.0),("MYR","MYR ",4.7)],
    "INT":[("USD","$",1.0)],
}
def _local_rate(country):
    p=CURRENCIES.get(country,[("USD","$",1.0)])
    return (p[1][1],p[1][2]) if len(p)>1 else (p[0][1],p[0][2])

def fmt_cur(usd,country):
    p=CURRENCIES.get(country,[("USD","$",1.0)])
    parts=[f"${usd}/day"]
    for _,sym,rate in p[1:]:
        a=round(usd*rate)
        parts.append(f"{sym}{a:,}" if a>=10000 else f"{sym}{a}")
    return " / ".join(parts)

COST_W  = {"🏛️ Attraction":0.18,"🍜 Restaurant":0.25,"☕ Cafe":0.10,
           "🌿 Park":0.04,"🛍️ Shopping":0.22,"🍺 Bar/Nightlife":0.16,
           "🏨 Hotel":0.00,"Transport":0.12}
COST_FL = {"🏛️ Attraction":4,"🍜 Restaurant":6,"☕ Cafe":3,
           "🌿 Park":0,"🛍️ Shopping":8,"🍺 Bar/Nightlife":5,
           "🏨 Hotel":0,"Transport":1}

def cost_est(tl,daily_usd,country):
    w=COST_W.get(tl,.12); fl=COST_FL.get(tl,2)
    pv=max(fl,daily_usd*w/2); lo=pv*.65; hi=pv*1.45; mid=(lo+hi)/2
    sym,rate=_local_rate(country)
    if country=="US": return mid,f"${round(lo)}-${round(hi)}"
    return mid,f"${round(lo)}-${round(hi)} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})"

def tr_cost(dist_km,daily_usd,country):
    base=max(1,daily_usd*.12/5); f=max(1.,dist_km/3.)
    lo=base*f*.7; hi=base*f*1.4; mid=(lo+hi)/2
    sym,rate=_local_rate(country)
    if country=="US": return mid,f"${round(lo)}-${round(hi)}"
    return mid,f"${round(lo)}-${round(hi)} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})"

CN_CITIES={
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
INTL_CITIES={
    "tokyo":(35.6762,139.6503,"JP",["Shinjuku","Shibuya","Asakusa","Harajuku","Ginza"]),
    "osaka":(34.6937,135.5023,"JP",["Dotonbori","Namba","Umeda","Shinsekai"]),
    "kyoto":(35.0116,135.7681,"JP",["Gion","Arashiyama","Higashiyama","Fushimi"]),
    "seoul":(37.5665,126.9780,"KR",["Gangnam","Hongdae","Myeongdong","Itaewon"]),
    "bangkok":(13.7563,100.5018,"TH",["Sukhumvit","Silom","Rattanakosin","Chatuchak"]),
    "singapore":(1.3521,103.8198,"SG",["Marina Bay","Clarke Quay","Orchard","Chinatown"]),
    "paris":(48.8566,2.3522,"FR",["Le Marais","Montmartre","Saint-Germain","Bastille"]),
    "london":(51.5072,-0.1276,"GB",["Soho","Covent Garden","Shoreditch","South Bank"]),
    "rome":(41.9028,12.4964,"IT",["Trastevere","Prati","Vatican","Campo de Fiori"]),
    "barcelona":(41.3851,2.1734,"ES",["Gothic Quarter","Eixample","Gracia","El Born"]),
    "new york":(40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Midtown"]),
    "new york city":(40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Midtown"]),
    "sydney":(-33.8688,151.2093,"AU",["Circular Quay","Surry Hills","Newtown","Bondi"]),
    "dubai":(25.2048,55.2708,"AE",["Downtown","Dubai Marina","Deira","JBR"]),
    "amsterdam":(52.3676,4.9041,"NL",["Jordaan","De Pijp","Centrum","Oost"]),
    "istanbul":(41.0082,28.9784,"TR",["Beyoglu","Sultanahmet","Besiktas","Kadikoy"]),
    "hong kong":(22.3193,114.1694,"HK",["Central","Tsim Sha Tsui","Mong Kok","Causeway Bay"]),
    "taipei":(25.0330,121.5654,"TW",["Daan","Xinyi","Zhongzheng","Shilin"]),
    "bali":(-8.3405,115.0920,"ID",["Seminyak","Ubud","Canggu","Kuta"]),
    "ho chi minh city":(10.7769,106.7009,"VN",["District 1","District 3","Bui Vien"]),
    "kuala lumpur":(3.1390,101.6869,"MY",["KLCC","Bukit Bintang","Bangsar","Chow Kit"]),
}
PTYPES={
    "🏛️ Attraction":{"cn":"jingdian","osm":("tourism","attraction"),"amap":"110000","color":"#8b5cf6"},
    "🍜 Restaurant": {"cn":"canting",  "osm":("amenity","restaurant"), "amap":"050000","color":"#f59e0b"},
    "☕ Cafe":        {"cn":"kafei",    "osm":("amenity","cafe"),        "amap":"050500","color":"#a78bfa"},
    "🌿 Park":        {"cn":"gongyuan","osm":("leisure","park"),        "amap":"110101","color":"#34d399"},
    "🛍️ Shopping":   {"cn":"gouwu",   "osm":("shop","mall"),           "amap":"060000","color":"#f472b6"},
    "🍺 Bar/Nightlife":{"cn":"jiuba",  "osm":("amenity","bar"),         "amap":"050600","color":"#fb923c"},
    "🏨 Hotel":       {"cn":"jiudian", "osm":("tourism","hotel"),       "amap":"100000","color":"#38bdf8"},
}
AMAP_KW={
    "🏛️ Attraction":["旅游景点","博物馆","历史景区"],
    "🍜 Restaurant": ["餐馆","美食","特色菜"],
    "☕ Cafe":        ["咖啡","下午茶"],
    "🌿 Park":        ["公园","花园","广场"],
    "🛍️ Shopping":   ["商场","购物中心"],
    "🍺 Bar/Nightlife":["酒吧","夜店"],
    "🏨 Hotel":       ["酒店","宾馆"],
}
DAY_COLORS=["#8b5cf6","#f59e0b","#34d399","#f472b6","#fb923c","#38bdf8","#a78bfa","#6ee7b7"]

WORLD_CITIES={
    "China":["Beijing","Shanghai","Guangzhou","Shenzhen","Chengdu","Hangzhou",
             "Xi'an","Chongqing","Nanjing","Wuhan","Suzhou","Tianjin",
             "Qingdao","Xiamen","Kunming","Sanya","Changsha","Zhengzhou"],
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya","Hiroshima","Nara"],
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
    "Italy":["Rome","Milan","Florence","Venice","Naples","Amalfi"],
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
    "Norway":["Oslo","Bergen","Tromso","Lofoten Islands"],
    "Sweden":["Stockholm","Gothenburg","Kiruna"],
    "Denmark":["Copenhagen","Aarhus"],
    "Finland":["Helsinki","Rovaniemi"],
    "Iceland":["Reykjavik","Akureyri"],
    "Russia":["Moscow","St. Petersburg","Vladivostok"],
    "USA":["New York","Los Angeles","Chicago","San Francisco","Miami","Boston",
           "Seattle","Las Vegas","Washington DC","Nashville"],
    "Canada":["Toronto","Vancouver","Montreal","Banff","Quebec City"],
    "Mexico":["Mexico City","Cancun","Playa del Carmen","Oaxaca"],
    "Brazil":["Rio de Janeiro","Sao Paulo","Salvador","Iguazu Falls"],
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
COUNTRY_CODES={
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

def _ss(s):
    if s is None: return ""
    s=str(s)
    for o,n in {"\u2014":"-","\u2013":"-","\u2019":"'","\u2018":"'",
                "\u201c":'"',"\u201d":'"',"\u2026":"..."}.items():
        s=s.replace(o,n)
    return s

def _hav(la1,lo1,la2,lo2):
    R=6371000; dl=math.radians(la2-la1); dg=math.radians(lo2-lo1)
    a=math.sin(dl/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dg/2)**2
    return R*2*math.asin(math.sqrt(min(1.,a)))

def geo_dedup(places,r=120.):
    if not places: return []
    merged=[False]*len(places); kept=[]
    for i,p in enumerate(places):
        if merged[i]: continue
        best=p
        for j in range(i+1,len(places)):
            if merged[j]: continue
            d=_hav(best["lat"],best["lon"],places[j]["lat"],places[j]["lon"])
            sl=places[j]["name"].strip().lower(); bl=best["name"].strip().lower()
            sim=(sl==bl) or (len(sl)>=3 and sl in bl) or (len(bl)>=3 and bl in sl)
            if d<50 or (d<r and sim):
                merged[j]=True
                if places[j]["rating"]>best["rating"]: best=places[j]
        kept.append(best)
    return kept

def tdesc(s):
    D={"attraction":"Worth a visit","景点":"Worth a visit",
       "restaurant":"Great for a meal","餐":"Great for a meal",
       "cafe":"Perfect coffee stop","咖":"Perfect coffee stop",
       "park":"Relax outdoors","公园":"Relax outdoors",
       "mall":"Shopping stop","购物":"Shopping stop",
       "bar":"Evening out","酒吧":"Evening out",
       "hotel":"Place to stay","酒店":"Place to stay"}
    for k,v in D.items():
        if k in str(s).lower(): return v
    return "Local favourite"

CHAIN_BL=["kfc","mcdonald","starbucks","seven-eleven","family mart","711","lawson","costa coffee"]
def is_chain(n): return any(k in n.lower() for k in CHAIN_BL)

# ══════════════════════════════════════════════════════════════════
# AI MUST-SEE
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_mustsee(city:str, country:str, days:int, types_t:tuple, lang:str="EN") -> list:
    types=list(types_t)
    if DEEPSEEK_KEY:
        try:
            t_str=", ".join(types[:5])
            prompt=(
                f"Recommend {min(days*3,12)} must-visit famous places in {city} "
                f"for a {days}-day trip. Types: {t_str}. "
                f"Only real well-known landmarks. "
                f"Return JSON array only. Each item: "
                f"name (English), name_local (local script), type, "
                f"why (max 10 words), tip (max 10 words), "
                f"rating (4.0-5.0), lat (number), lon (number), "
                f"duration_min (suggested visit time in minutes, integer)."
            )
            if lang=="ZH":
                prompt=(
                    f"为{city}{days}天行程推荐{min(days*3,12)}个必去著名地点，类型：{t_str}。"
                    f"只推荐真实存在的知名地点。"
                    f"仅返回JSON数组，每项：name(英文名), name_local(中文名), type, "
                    f"why(英文,10词内), tip(英文,10词内), "
                    f"rating(4.0-5.0), lat(数字), lon(数字), duration_min(建议游览分钟数,整数)。"
                )
            resp=requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat",
                      "messages":[{"role":"user","content":prompt}],
                      "temperature":0.3,"max_tokens":1400},
                timeout=20,
            )
            if resp.status_code==200:
                content=resp.json()["choices"][0]["message"]["content"].strip()
                m=re.search(r'\[.*\]',content,re.DOTALL)
                if m:
                    items=json.loads(m.group())
                    if isinstance(items,list) and items:
                        cleaned=[]
                        for it in items[:12]:
                            if not isinstance(it,dict): continue
                            cleaned.append({
                                "name":      _ss(it.get("name","")),
                                "name_local":_ss(it.get("name_local","")),
                                "type":      _ss(it.get("type","🏛️ Attraction")),
                                "why":       _ss(it.get("why","")),
                                "tip":       _ss(it.get("tip","")),
                                "rating":    float(it.get("rating",4.5)),
                                "lat":       float(it.get("lat",0)),
                                "lon":       float(it.get("lon",0)),
                                "duration_min": int(it.get("duration_min",60)),
                            })
                        if cleaned: return cleaned
        except Exception: pass

    BUILTIN={
        "tokyo":[
            {"name":"Senso-ji Temple","name_local":"浅草寺","type":"🏛️ Attraction",
             "why":"Tokyo oldest temple","tip":"Visit at 6am","rating":4.9,
             "lat":35.7148,"lon":139.7967,"duration_min":60},
            {"name":"Shibuya Crossing","name_local":"涩谷十字路口","type":"🏛️ Attraction",
             "why":"World busiest crossing","tip":"Watch from Starbucks above","rating":4.8,
             "lat":35.6595,"lon":139.7004,"duration_min":20},
            {"name":"Shinjuku Gyoen","name_local":"新宿御苑","type":"🌿 Park",
             "why":"Beautiful imperial garden","tip":"April for cherry blossoms","rating":4.8,
             "lat":35.6851,"lon":139.7103,"duration_min":90},
            {"name":"Tsukiji Outer Market","name_local":"筑地外市场","type":"🍜 Restaurant",
             "why":"Freshest sushi breakfast","tip":"Arrive before 9am","rating":4.7,
             "lat":35.6654,"lon":139.7707,"duration_min":60},
        ],
        "paris":[
            {"name":"Eiffel Tower","name_local":"埃菲尔铁塔","type":"🏛️ Attraction",
             "why":"Iconic symbol of Paris","tip":"Book summit tickets ahead","rating":4.8,
             "lat":48.8584,"lon":2.2945,"duration_min":90},
            {"name":"Louvre Museum","name_local":"卢浮宫","type":"🏛️ Attraction",
             "why":"World largest art museum","tip":"Wednesday evening less crowded","rating":4.8,
             "lat":48.8606,"lon":2.3376,"duration_min":180},
            {"name":"Montmartre","name_local":"蒙马特","type":"🏛️ Attraction",
             "why":"Charming hilltop artist village","tip":"Morning for fewer tourists","rating":4.7,
             "lat":48.8867,"lon":2.3431,"duration_min":90},
        ],
        "london":[
            {"name":"British Museum","name_local":"大英博物馆","type":"🏛️ Attraction",
             "why":"Free world class museum","tip":"Free entry, book timed slot","rating":4.8,
             "lat":51.5194,"lon":-0.1270,"duration_min":120},
            {"name":"Tower of London","name_local":"伦敦塔","type":"🏛️ Attraction",
             "why":"900 years of royal history","tip":"Buy tickets online","rating":4.7,
             "lat":51.5081,"lon":-0.0759,"duration_min":90},
            {"name":"Borough Market","name_local":"波罗市场","type":"🍜 Restaurant",
             "why":"London best food market","tip":"Thursday to Saturday only","rating":4.8,
             "lat":51.5055,"lon":-0.0910,"duration_min":60},
        ],
        "beijing":[
            {"name":"Forbidden City","name_local":"故宫","type":"🏛️ Attraction",
             "why":"World largest palace complex","tip":"Book online, sell out fast","rating":4.9,
             "lat":39.9163,"lon":116.3972,"duration_min":180},
            {"name":"Great Wall Mutianyu","name_local":"慕田峪长城","type":"🏛️ Attraction",
             "why":"Best restored Great Wall section","tip":"Cable car up, toboggan down","rating":4.9,
             "lat":40.4319,"lon":116.5651,"duration_min":180},
            {"name":"Temple of Heaven","name_local":"天坛","type":"🏛️ Attraction",
             "why":"Ming dynasty ceremonial park","tip":"Early morning for tai chi","rating":4.8,
             "lat":39.8822,"lon":116.4066,"duration_min":90},
        ],
        "singapore":[
            {"name":"Marina Bay Sands SkyPark","name_local":"滨海湾金沙空中花园","type":"🏛️ Attraction",
             "why":"Iconic skyline views","tip":"Sunset is best time","rating":4.8,
             "lat":1.2834,"lon":103.8607,"duration_min":60},
            {"name":"Gardens by the Bay","name_local":"滨海湾花园","type":"🌿 Park",
             "why":"Futuristic Supertree Grove","tip":"Free outdoor, paid conservatories","rating":4.9,
             "lat":1.2816,"lon":103.8636,"duration_min":120},
            {"name":"Maxwell Hawker Centre","name_local":"麦士威熟食中心","type":"🍜 Restaurant",
             "why":"Legendary Hainanese chicken rice","tip":"Tian Tian stall, queue early","rating":4.8,
             "lat":1.2800,"lon":103.8444,"duration_min":45},
        ],
        "dubai":[
            {"name":"Burj Khalifa","name_local":"哈利法塔","type":"🏛️ Attraction",
             "why":"World tallest building views","tip":"Book At the Top online","rating":4.8,
             "lat":25.1972,"lon":55.2744,"duration_min":90},
            {"name":"Dubai Museum","name_local":"迪拜博物馆","type":"🏛️ Attraction",
             "why":"History in an old fort","tip":"Only AED 3 entry fee","rating":4.5,
             "lat":25.2637,"lon":55.2972,"duration_min":60},
        ],
    }
    city_lc=city.strip().lower()
    for k,v in BUILTIN.items():
        if k in city_lc: return v
    return []


def get_day_picks(city,country,day_idx,days,types,lang="EN"):
    all_r=get_ai_mustsee(city,country,days,tuple(types),lang)
    if not all_r: return []
    n=len(all_r); start=(day_idx*3)%n
    return [all_r[(start+i)%n] for i in range(min(3,n))]

# ══════════════════════════════════════════════════════════════════
# GEOCODING
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600,show_spinner=False)
def _amap_districts(city):
    if not city.strip() or not AMAP_KEY: return []
    try:
        r=requests.get("https://restapi.amap.com/v3/config/district",
                       params={"key":AMAP_KEY,"keywords":city,"subdistrict":1,
                               "extensions":"base","output":"json"},timeout=9).json()
        if str(r.get("status"))!="1" or not r.get("districts"): return []
        out=[]
        for d in r["districts"][0].get("districts",[]):
            n=(d.get("name") or "").strip(); a=(d.get("adcode") or "").strip()
            c=(d.get("center") or "").strip()
            if not (n and a): continue
            lat=lon=None
            if "," in c:
                try: lon,lat=map(float,c.split(","))
                except Exception: pass
            out.append({"name":n,"adcode":a,"lat":lat,"lon":lon})
        return out
    except Exception: return []

@st.cache_data(ttl=3600,show_spinner=False)
def _amap_geo(addr):
    if not AMAP_KEY: return None
    try:
        r=requests.get("https://restapi.amap.com/v3/geocode/geo",
                       params={"key":AMAP_KEY,"address":addr,"output":"json"},timeout=8).json()
        if str(r.get("status"))=="1" and r.get("geocodes"):
            loc=r["geocodes"][0].get("location","")
            if "," in loc:
                lon,lat=map(float,loc.split(","))
                return lat,lon
    except Exception: pass
    return None

@st.cache_data(ttl=3600,show_spinner=False)
def _nom(q):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
                       params={"q":q,"format":"json","limit":1},
                       headers={"User-Agent":"TravelPlannerPro/15"},timeout=9).json()
        if r: return float(r[0]["lat"]),float(r[0]["lon"])
    except Exception: pass
    return None

def _geocode(addr,city,is_cn):
    if not addr.strip(): return None
    if is_cn: return _amap_geo(f"{addr} {city}") or _nom(f"{addr} {city}")
    return _nom(f"{addr} {city}") or _nom(addr)

@st.cache_data(ttl=3600,show_spinner=False)
def _nom_districts(city):
    if not city.strip(): return []
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
                       params={"q":city,"format":"json","limit":1},
                       headers={"User-Agent":"TravelPlannerPro/15"},timeout=8).json()
        if not r: return []
        lat,lon=float(r[0]["lat"]),float(r[0]["lon"])
        q=(f'[out:json][timeout:20];'
           f'(relation["place"~"suburb|neighbourhood|quarter|district"](around:20000,{lat},{lon});'
           f'node["place"~"suburb|neighbourhood|quarter"](around:20000,{lat},{lon}););out tags 30;')
        els=[]
        for url in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
            try:
                els=requests.post(url,data={"data":q},timeout=18).json().get("elements",[])
                if els: break
            except Exception: continue
        names=[]
        for el in els:
            n=el.get("tags",{}).get("name:en") or el.get("tags",{}).get("name","")
            if n and n not in names and len(n)>1: names.append(n)
        return sorted(names[:20])
    except Exception: return []

# ══════════════════════════════════════════════════════════════════
# PLACE SEARCH
# ══════════════════════════════════════════════════════════════════
def _parse_amap(pois,kw,tl,limit,seen):
    out=[]
    for p in pois:
        if len(out)+len(seen)>=limit: break
        nm=p.get("name","")
        if not nm or is_chain(nm): continue
        loc=p.get("location","")
        if "," not in (loc or ""): continue
        try: plon,plat=map(float,loc.split(","))
        except Exception: continue
        k=(nm,round(plat,4),round(plon,4))
        if k in seen: continue
        seen.add(k)
        biz=p.get("biz_ext") or {}
        try: rating=float(biz.get("rating") or 0) or 0.0
        except Exception: rating=0.0
        tel=biz.get("tel") or p.get("tel") or ""
        if isinstance(tel,list): tel="; ".join(t for t in tel if t)
        addr=p.get("address") or ""
        if isinstance(addr,list): addr="".join(addr)
        out.append({"name":_ss(nm),"lat":plat,"lon":plon,"rating":rating,
                    "address":_ss(str(addr).strip()),"phone":_ss(str(tel).strip()),
                    "website":"","type":kw,"type_label":tl,
                    "district":_ss(p.get("adname") or ""),"description":tdesc(kw)})
    return out

def search_cn(lat,lon,tls,lpt,adcode=""):
    all_p=[]; errs=[]
    for tl in tls:
        for kw in AMAP_KW.get(tl,[])[:2]:
            try:
                if adcode:
                    p={"key":AMAP_KEY,"keywords":kw,"city":adcode,"citylimit":"true",
                       "offset":20,"page":1,"extensions":"all","output":"json"}
                    at=PTYPES.get(tl,{}).get("amap","")
                    if at: p["types"]=at
                    d=requests.get("https://restapi.amap.com/v3/place/text",params=p,timeout=10).json()
                else:
                    p={"key":AMAP_KEY,"keywords":kw,"location":f"{lon},{lat}","radius":8000,
                       "offset":20,"page":1,"extensions":"all","output":"json"}
                    at=PTYPES.get(tl,{}).get("amap","")
                    if at: p["types"]=at
                    d=requests.get("https://restapi.amap.com/v3/place/around",params=p,timeout=10).json()
                seen=set()
                if str(d.get("status"))=="1":
                    all_p.extend(_parse_amap(d.get("pois") or [],kw,tl,lpt,seen))
            except Exception as e: errs.append(str(e))
    seen2,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen2: seen2.add(k); out.append(p)
    return out,errs

def search_intl(lat,lon,tls,lpt,district=""):
    all_p=[]
    for tl in tls:
        ok,ov=PTYPES[tl]["osm"]
        clat,clon=lat,lon
        if district:
            try:
                g=requests.get("https://nominatim.openstreetmap.org/search",
                               params={"q":district,"format":"json","limit":1},
                               headers={"User-Agent":"TravelPlannerPro/15"},timeout=5).json()
                if g: clat,clon=float(g[0]["lat"]),float(g[0]["lon"])
            except Exception: pass
        q=(f'[out:json][timeout:30];(node["{ok}"="{ov}"](around:5000,{clat},{clon});'
           f'way["{ok}"="{ov}"](around:5000,{clat},{clon}););out center {lpt*3};')
        els=[]
        for url in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
            try:
                r=requests.post(url,data={"data":q},timeout=28).json().get("elements",[])
                if r: els=r; break
            except Exception: continue
        for el in els:
            tags=el.get("tags",{})
            nm=tags.get("name:en") or tags.get("name","")
            if not nm or is_chain(nm): continue
            elat=el.get("lat",0) if el["type"]=="node" else el.get("center",{}).get("lat",0)
            elon=el.get("lon",0) if el["type"]=="node" else el.get("center",{}).get("lon",0)
            if not elat or not elon: continue
            pts=[tags.get(k,"") for k in ["addr:housenumber","addr:street","addr:suburb","addr:city"] if tags.get(k)]
            all_p.append({"name":_ss(nm),"lat":elat,"lon":elon,
                          "rating":round(random.uniform(3.8,5.0),1),
                          "address":_ss(", ".join(pts)),"phone":_ss(tags.get("phone","")),
                          "website":_ss(tags.get("website","")),"type":ov,"type_label":tl,
                          "district":_ss(tags.get("addr:suburb","")),"description":tdesc(ov)})
            if len(all_p)>=lpt*len(tls): break
    seen,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],3),round(p["lon"],3))
        if k not in seen: seen.add(k); out.append(p)
    return out

def demo_places(lat,lon,tls,n,seed):
    random.seed(seed)
    NAMES={
        "🏛️ Attraction":["Grand Museum","Sky Tower","Ancient Temple","Art Gallery","Historic Castle","Night Market"],
        "🍜 Restaurant": ["Sakura Dining","Ramen House","Sushi Master","Street Food Alley","Harbour Grill","Noodle King"],
        "☕ Cafe":        ["Blue Bottle","Artisan Brew","Matcha Corner","Morning Pour","The Cozy Cup"],
        "🌿 Park":        ["Riverside Park","Sakura Garden","Central Park","Bamboo Grove"],
        "🛍️ Shopping":   ["Central Mall","Night Bazaar","Vintage Market","Designer District"],
        "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Garden"],
        "🏨 Hotel":       ["Grand Palace Hotel","Boutique Inn","City View Hotel"],
    }
    centers=[(lat+random.uniform(-.02,.02),lon+random.uniform(-.02,.02)) for _ in range(3)]
    out=[]
    for tl in tls:
        nms=list(NAMES.get(tl,["Local Spot"])); random.shuffle(nms)
        for i,nm in enumerate(nms[:n]):
            ci=i%3; clat,clon=centers[ci]
            out.append({"name":nm,"lat":round(clat+random.uniform(-.005,.005),5),
                        "lon":round(clon+random.uniform(-.005,.005),5),
                        "rating":round(random.uniform(4.0,4.9),1),
                        "address":"Sample data","phone":"","website":"",
                        "type":tl,"type_label":tl,
                        "district":["North","Central","South"][ci],"description":tdesc(tl)})
    return out

@st.cache_data(ttl=180,show_spinner=False)
def fetch_places(clat,clon,country,is_cn,tls_t,lpt,
                 adcodes_t,dnames_t,alats_t,alons_t,_seed):
    random.seed(_seed); tls=list(tls_t); all_raw=[]; warn=None; seen_k=set()
    for i in range(len(adcodes_t)):
        adc=adcodes_t[i]; dn=dnames_t[i]
        dlat=alats_t[i] if alats_t[i] is not None else clat
        dlon=alons_t[i] if alons_t[i] is not None else clon
        ck=adc or f"{round(dlat,3)},{round(dlon,3)}"
        if ck in seen_k: continue
        seen_k.add(ck)
        if is_cn:
            ps,_=search_cn(dlat,dlon,tls,lpt,adc)
        else:
            ps=search_intl(dlat,dlon,tls,lpt,dn)
        all_raw.extend(ps)
    seen,out=set(),[]
    for p in all_raw:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    out=geo_dedup(out)
    if not out:
        out=demo_places(clat,clon,tls,lpt,_seed)
        warn=("Amap API unavailable - showing sample data." if is_cn
              else "Live data unavailable - showing sample places.")
    df=pd.DataFrame(out)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c]=""
    df["rating"]=pd.to_numeric(df["rating"],errors="coerce").fillna(0.)
    for c in ["name","address","phone","district","description","type_label","type"]:
        df[c]=df[c].apply(_ss)
    return df.sort_values("rating",ascending=False).reset_index(drop=True),warn

# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    try:
        tok=st.session_state.get("_auth_token","")
        if not tok: return None
        return get_user_from_session(tok)
    except Exception: return None

def render_auth():
    user=_cur_user()
    if user:
        pts=0
        if POINTS_OK:
            try: pts=get_points(user["username"])
            except Exception: pass
        st.markdown(
            f'<div class="user-card">'
            f'<div class="u-av">{user["username"][0].upper()}</div>'
            f'<div><div class="u-name">{user["username"]}</div>'
            f'<div class="u-pts">&#10022; {pts} pts</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(_t("auth_logout"),key="auth_lo",use_container_width=True):
            try: logout_user(st.session_state.get("_auth_token",""))
            except Exception: pass
            st.session_state.pop("_auth_token",None); st.rerun()
    else:
        t1,t2=st.tabs([_t("auth_login"),_t("auth_register")])
        with t1:
            u=st.text_input(_t("auth_username"),key="li_u",placeholder="username")
            p=st.text_input(_t("auth_password"),type="password",key="li_p",placeholder="password")
            if st.button(_t("auth_login"),key="li_b",use_container_width=True):
                try:
                    ok,msg,tok=login_user(u,p)
                    if ok:
                        st.session_state["_auth_token"]=tok
                        if POINTS_OK:
                            try: add_points(u,"daily_login")
                            except Exception: pass
                        st.success(msg); st.rerun()
                    else: st.error(msg)
                except Exception as e: st.error(f"Login error: {e}")
        with t2:
            ru=st.text_input(_t("auth_username"),key="re_u",placeholder="new username")
            re=st.text_input(_t("auth_email"),key="re_e",placeholder="email@example.com")
            rp=st.text_input(_t("auth_password"),type="password",key="re_p",placeholder="password")
            if st.button(_t("auth_register"),key="re_b",use_container_width=True):
                try:
                    ok,msg=register_user(ru,rp,re)
                    (st.success if ok else st.error)(msg)
                except Exception as e: st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════
# WISHLIST HEART BUTTON
# ══════════════════════════════════════════════════════════════════
def wl_button(place_dict:dict, key:str):
    user=_cur_user()
    if not user: return
    uname=user["username"]; nm=place_dict.get("name","")
    saved=wl_check(uname,nm)
    icon="♥" if saved else "♡"
    if st.button(icon,key=key,help="Remove" if saved else "Save to wishlist"):
        if saved:
            wl_remove(uname,nm); st.toast(f"Removed {nm}")
        else:
            wl_add(uname,{"name":nm,"lat":place_dict.get("lat",0),
                          "lon":place_dict.get("lon",0),
                          "type":place_dict.get("type_label",""),
                          "rating":place_dict.get("rating",0),
                          "address":place_dict.get("address",""),
                          "district":place_dict.get("district","")})
            st.toast(f"Saved {nm}!")
            if POINTS_OK:
                try: add_points(uname,"wishlist_add",note=nm)
                except Exception: pass
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# ADD TO DAY
# ══════════════════════════════════════════════════════════════════
def add_to_day(place_dict:dict, day_key:str) -> bool:
    itin=st.session_state.get("_itin",{})
    if not itin or day_key not in itin: return False
    stops=itin.get(day_key,[])
    if not isinstance(stops,list): stops=[]
    if place_dict.get("name","") in {s.get("name","") for s in stops}:
        st.toast("Already in this day!",icon="ℹ️"); return False
    stops.append({
        "name":      place_dict.get("name",""),
        "lat":       place_dict.get("lat",0),
        "lon":       place_dict.get("lon",0),
        "type_label":place_dict.get("type_label",place_dict.get("type","🏛️ Attraction")),
        "rating":    place_dict.get("rating",4.5),
        "address":   place_dict.get("address",""),
        "district":  place_dict.get("district",""),
        "description":place_dict.get("description",""),
        "time_slot": "TBD",
        "transport_to_next": None,
    })
    itin[day_key]=stops; st.session_state["_itin"]=itin; return True

# ══════════════════════════════════════════════════════════════════
# MAP
# ══════════════════════════════════════════════════════════════════
def build_map(df,lat,lon,itinerary,hotel_c=None,depart_c=None,arrive_c=None):
    m=folium.Map(location=[lat,lon],zoom_start=13,tiles="CartoDB positron")
    vi={}
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops): vi[s["name"]]=(di,si+1,s)
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or len(stops)<2: continue
            dc=DAY_COLORS[di%len(DAY_COLORS)]
            for si in range(len(stops)-1):
                a,b=stops[si],stops[si+1]
                if not (a.get("lat") and b.get("lat")): continue
                folium.PolyLine([[a["lat"],a["lon"]],[b["lat"],b["lon"]]],
                                color=dc,weight=2.8,opacity=.55,dash_array="5 4").add_to(m)
    for _,row in df.iterrows():
        v=vi.get(row["name"])
        if v:
            di,sn,_=v; color=DAY_COLORS[di%len(DAY_COLORS)]; label=str(sn)
            day_info=f"Day {di+1} Stop {sn}"
        else:
            color="#d1d5db"; label="."; day_info="Not scheduled"
        addr=_ss(row.get("address",""))
        dur=estimate_duration(_ss(row.get("name","")),row.get("type_label",""))
        pop=(f"<div style='font-family:-apple-system,sans-serif;min-width:160px'>"
             f"<b style='font-size:.87rem'>{_ss(row['name'])}</b><br>"
             f"<span style='color:#9ca3af;font-size:.74rem'>&#9733; {row['rating']:.1f} &middot; {day_info}</span><br>"
             f"<span style='color:#a78bfa;font-size:.72rem'>&#128337; {format_duration(dur)}</span>"
             f"{'<br><span style=font-size:.72rem;color:#6b7280>'+addr[:50]+'</span>' if addr and 'Sample' not in addr else ''}"
             f"</div>")
        folium.Marker(
            [row["lat"],row["lon"]],
            popup=folium.Popup(pop,max_width=220),
            tooltip=f"{_ss(row['name'])} - {format_duration(dur)}",
            icon=folium.DivIcon(
                html=(f'<div style="width:22px;height:22px;border-radius:50%;background:{color};'
                      f'border:2px solid rgba(255,255,255,.9);display:flex;align-items:center;'
                      f'justify-content:center;color:white;font-size:10px;font-weight:700;'
                      f'box-shadow:0 2px 8px rgba(109,40,217,.22)">{label}</div>'),
                icon_size=(22,22),icon_anchor=(11,11),
            ),
        ).add_to(m)
    def sm(c,ic,tip):
        folium.Marker(list(c),tooltip=tip,
            icon=folium.DivIcon(html=f'<div style="font-size:18px">{ic}</div>',
                                icon_size=(24,24),icon_anchor=(12,12))).add_to(m)
    if hotel_c:  sm(hotel_c,"🏨","Hotel")
    if depart_c: sm(depart_c,"🚩","Start")
    if arrive_c: sm(arrive_c,"🏁","End")
    return m

# ══════════════════════════════════════════════════════════════════
# INLINE SWAP
# ══════════════════════════════════════════════════════════════════
def render_swap(itinerary,df,day_key,stop_idx):
    stops=itinerary.get(day_key,[])
    if not isinstance(stops,list) or stop_idx>=len(stops): return
    cur=stops[stop_idx]; cur_type=cur.get("type_label","")
    used={s["name"] for sl in itinerary.values() if isinstance(sl,list) for s in sl}
    cands=(df[(df["type_label"]==cur_type)&(~df["name"].isin(used))]
           .sort_values("rating",ascending=False).head(4))
    if cands.empty: st.warning("No alternatives found."); return
    st.markdown(
        f'<div class="sw-panel"><div style="font-weight:600;font-size:.82rem;'
        f'color:#1e1b4b;margin-bottom:8px">Swap: <b>{_ss(cur["name"])}</b></div>',
        unsafe_allow_html=True,
    )
    cols=st.columns(min(len(cands),4))
    for i,(_,alt) in enumerate(cands.iterrows()):
        with cols[i%min(len(cands),4)]:
            nm=_ss(alt["name"]); rat=alt.get("rating",0)
            dur=estimate_duration(nm,alt.get("type_label",""))
            st.markdown(
                f'<div style="background:rgba(255,255,255,.80);border-radius:9px;'
                f'padding:9px;border:1px solid rgba(255,255,255,.9);margin-bottom:3px">'
                f'<div style="font-weight:600;font-size:.80rem;color:#1e1b4b">{nm}</div>'
                f'<div style="font-size:.70rem;color:#9ca3af">&#9733; {rat:.1f} &middot; {format_duration(dur)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Select",key=f"swc_{day_key}_{stop_idx}_{nm[:6]}",use_container_width=True):
                try:
                    if WISHLIST_EXT:
                        new_it=swap_place_in_itinerary(
                            st.session_state.get("_itin",itinerary),day_key,stop_idx,alt.to_dict())
                    else: raise Exception("no ext")
                except Exception:
                    new_it=dict(st.session_state.get("_itin",itinerary))
                    ds=list(new_it.get(day_key,[])); ds[stop_idx]=alt.to_dict()
                    new_it[day_key]=ds
                st.session_state["_itin"]=new_it
                st.session_state.pop(f"_sw_{day_key}_{stop_idx}",None)
                st.toast(f"Replaced with {nm}"); st.rerun()
    if st.button("Cancel",key=f"swcancel_{day_key}_{stop_idx}"):
        st.session_state.pop(f"_sw_{day_key}_{stop_idx}",None); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AI PICKS PANEL (per day)
# ══════════════════════════════════════════════════════════════════
def render_ai_picks(city,country,day_idx,district,sel_types,ndays,day_key):
    picks=get_day_picks(city,country,day_idx,ndays,sel_types,LANG)
    if not picks: return
    current_itin=st.session_state.get("_itin",{})
    existing={s.get("name","") for s in current_itin.get(day_key,[])
              if isinstance(current_itin.get(day_key,[]),list)}

    st.markdown(
        f'<div class="ai-panel">'
        f'<div style="font-weight:700;font-size:.80rem;color:#1e1b4b;margin-bottom:2px">'
        f'&#10022; {_t("ai_rec_heading")}</div>'
        f'<div style="font-size:.70rem;color:#a78bfa;margin-bottom:10px">'
        f'{"AI-powered" if DEEPSEEK_KEY else "Curated"} must-see highlights</div>',
        unsafe_allow_html=True,
    )
    cols=st.columns(min(len(picks),3))
    for i,rec in enumerate(picks):
        with cols[i%min(len(picks),3)]:
            nm=_ss(rec.get("name","")); nl=_ss(rec.get("name_local",""))
            tp=_ss(rec.get("type","")); why=_ss(rec.get("why",""))
            tip=_ss(rec.get("tip","")); rat=rec.get("rating",4.5)
            dur=rec.get("duration_min",estimate_duration(nm,tp))
            already=nm in existing
            nm_disp=f"{nm}" + (f'<span style="color:#a78bfa;font-size:.69rem;display:block">{nl}</span>' if nl else "")
            st.markdown(
                f'<div class="ai-item">'
                f'<div style="font-weight:600;font-size:.82rem;color:#1e1b4b">{nm_disp}</div>'
                f'<div style="color:#a78bfa;font-size:.70rem">{tp}</div>'
                f'<div style="color:#6b7280;font-size:.74rem;margin-top:2px">{why}</div>'
                f'{"<div style=color:#f59e0b;font-size:.69rem;margin-top:1px>Tip: "+tip+"</div>" if tip else ""}'
                f'<div style="display:flex;gap:8px;margin-top:4px;align-items:center">'
                f'<span style="font-size:.69rem;color:#c4b5fd">&#9733; {rat}</span>'
                f'<span class="dur-badge">&#128337; {format_duration(dur)}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            if already:
                st.markdown('<div style="font-size:.70rem;color:#16a34a;margin-top:2px">&#10003; In itinerary</div>',
                            unsafe_allow_html=True)
            else:
                if st.button(f"+ Add",key=f"ai_add_{day_key}_{i}_{nm[:6]}",use_container_width=True):
                    pd_={
                        "name":nm,"lat":rec.get("lat",0),"lon":rec.get("lon",0),
                        "type_label":tp,"rating":rat,"address":"",
                        "district":district or "","description":why,
                    }
                    if add_to_day(pd_,day_key):
                        st.toast(f"Added {nm}!"); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ITINERARY TABLE
# ══════════════════════════════════════════════════════════════════
def render_table(df,itinerary,day_budgets,country,city="",
                 day_districts=None,sel_types=None):
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    if day_districts is None: day_districts=[""]* 30
    if sel_types is None: sel_types=list(PTYPES.keys())

    stop_map={}
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops): stop_map[s["name"]]=(di,si,dl,s)

    n2r={row["name"]:row for _,row in df.iterrows()}
    scheduled=[]
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops):
                if s["name"] in n2r: scheduled.append((di,si,dl,s["name"]))

    snames={x[3] for x in scheduled}
    unscheduled=[row for _,row in df.iterrows() if row["name"] not in snames]
    cur_day=-1; user=_cur_user()
    current_itin=st.session_state.get("_itin",itinerary)

    for di,si,dl,nm in scheduled:
        row=n2r[nm]; color=DAY_COLORS[di%len(DAY_COLORS)]
        d_usd=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]

        # Day header
        if di!=cur_day:
            cur_day=di; day_key=f"Day {di+1}"
            day_stops=list((current_itin or {}).get(day_key,[]))
            lb,_=budget_level(d_usd)
            district=day_districts[di] if di<len(day_districts) else ""

            # Build timeline for this day
            timeline=build_day_timeline(day_stops)
            total_dur=sum(s.get("duration_min",60) for s in timeline)

            st.markdown(
                f'<div class="day-hdr">'
                f'<div class="day-dot" style="background:{color}"></div>'
                f'<div class="day-ttl">{day_key}</div>'
                f'<div class="day-info">'
                f'{len(day_stops)} stops &nbsp;&middot;&nbsp; '
                f'${d_usd}/day &nbsp;&middot;&nbsp; {lb} &nbsp;&middot;&nbsp; '
                f'~{format_duration(total_dur)} total</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # AI picks for this day
            render_ai_picks(city,country,di,district,sel_types,len(itinerary),day_key)

        # Build timeline dict for lookup
        day_key2=f"Day {di+1}"
        day_stops2=list((current_itin or {}).get(day_key2,[]))
        tl_map={s.get("name",""):s for s in build_day_timeline(day_stops2)}
        tl_data=tl_map.get(nm,{})

        sd=stop_map.get(nm,(None,None,None,{}))[3]
        sw_key=f"_sw_Day {di+1}_{si}"

        with st.container():
            c_num,c_info,c_time,c_act=st.columns([1,5,3,1])

            with c_num:
                st.markdown(
                    f'<div style="text-align:center;padding-top:8px">'
                    f'<div class="sn" style="background:{color}">{si+1}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with c_info:
                tl_label=_ss(row.get("type_label","") or row.get("type",""))
                rat=row.get("rating",0); dist=_ss(row.get("district",""))
                addr=_ss(row.get("address","")); ph=_ss(row.get("phone",""))
                _,cs=cost_est(tl_label,d_usd,country) if tl_label else (0,"")
                dur=estimate_duration(_ss(nm),tl_label)

                h=(f'<div style="padding:5px 0">'
                   f'<div class="stop-name">{_ss(nm)}</div>'
                   f'<div class="stop-meta">{tl_label}'
                   f'{"&nbsp;·&nbsp;&#9733; "+str(rat) if rat else ""}'
                   f'{"&nbsp;·&nbsp;"+dist if dist else ""}</div>')
                if cs: h+=f'<div style="font-size:.70rem;color:#a78bfa;margin-top:2px">&#128176; {cs}</div>'
                if addr and "Sample" not in addr:
                    h+=f'<div style="font-size:.69rem;color:#c4b5fd;margin-top:1px">&#128205; {addr[:55]}</div>'
                h+='</div>'
                st.markdown(h,unsafe_allow_html=True)

            with c_time:
                arrive=tl_data.get("arrive_time","")
                depart=tl_data.get("depart_time","")
                dur_min=tl_data.get("duration_min",dur)
                tr=sd.get("transport_to_next") if sd else None
                tr_str=""
                if tr:
                    dk=tr.get("distance_km",0) or 0
                    tr_str=(f'<div class="tr-chip" style="margin-top:4px">'
                            f'&#128663; {_ss(tr.get("mode",""))} &middot; {_ss(tr.get("duration",""))}</div>')

                time_html=(
                    f'<div style="padding:5px 0">'
                )
                if arrive:
                    time_html+=(
                        f'<div class="time-badge">&#128336; {arrive} - {depart}</div>'
                        f'<div class="dur-badge" style="margin-top:3px">&#128337; {format_duration(dur_min)}</div>'
                    )
                else:
                    time_html+=f'<div class="dur-badge">&#128337; ~{format_duration(dur_min)}</div>'
                time_html+=tr_str+"</div>"
                st.markdown(time_html,unsafe_allow_html=True)

            with c_act:
                if user:
                    wl_button(dict(row),key=f"wl_{di}_{si}_{nm[:5]}")
                sw_open=st.session_state.get(sw_key,False)
                if st.button("↔" if not sw_open else "✕",
                             key=f"sw_{di}_{si}",
                             help="Swap" if not sw_open else "Cancel",
                             use_container_width=True):
                    st.session_state[sw_key]=not sw_open; st.rerun()

        if st.session_state.get(sw_key,False):
            render_swap(current_itin,df,f"Day {di+1}",si)

        st.markdown(
            '<div style="height:1px;background:rgba(139,92,246,.07);margin:2px 0 4px"></div>',
            unsafe_allow_html=True,
        )

    if unscheduled:
        _render_extra(unscheduled,day_budgets,country,current_itin)

# ══════════════════════════════════════════════════════════════════
# EXTRA RECS — simplified grid
# ══════════════════════════════════════════════════════════════════
def _render_extra(unscheduled,day_budgets,country,itinerary=None):
    avg=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    CATS=[("Sights",["🏛️ Attraction"]),("Dining",["🍜 Restaurant","☕ Cafe"]),
          ("Nature",["🌿 Park"]),("Shopping",["🛍️ Shopping"]),
          ("Nightlife",["🍺 Bar/Nightlife"]),("Hotels",["🏨 Hotel"])]
    by_type={}
    for r in unscheduled:
        tl=r.get("type_label","") or r.get("type","")
        by_type.setdefault(tl,[]).append(r)
    cat_data=[]; covered=set()
    for cn,tls in CATS:
        items=[]
        for tl in tls: items.extend(by_type.get(tl,[]))
        for tl in tls: covered.add(tl)
        if items: cat_data.append((cn,items))
    others=[r for tl,rs in by_type.items() if tl not in covered for r in rs]
    if others: cat_data.append(("Other",others))
    if not cat_data: return

    day_keys=list(itinerary.keys()) if itinerary else []
    user=_cur_user()

    st.markdown(f'<div class="s-lbl">{_t("rec_heading")}</div>',unsafe_allow_html=True)

    import random as _r
    for cn,places in cat_data:
        sk=f"_rec_{cn}"
        if sk not in st.session_state: st.session_state[sk]=0
        c1,c2=st.columns([9,1])
        with c1:
            st.markdown(
                f'<div style="font-weight:600;font-size:.82rem;color:#1e1b4b;margin:10px 0 5px">'
                f'{cn} <span style="color:#c4b5fd;font-size:.71rem">({min(8,len(places))}/{len(places)})</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("&#8635;",key=f"rf_{cn}",use_container_width=True):
                st.session_state[sk]=(st.session_state[sk]+1)%9999

        _r.seed(st.session_state[sk])
        picks=sorted(_r.sample(places,min(8,len(places))),
                     key=lambda r:r.get("rating",0),reverse=True)

        # Show in rows of 4
        for row_s in range(0,len(picks),4):
            chunk=picks[row_s:row_s+4]
            cols=st.columns(len(chunk))
            for ci,p in enumerate(chunk):
                with cols[ci]:
                    nm=_ss(p.get("name","")); tl=_ss(p.get("type_label","") or p.get("type",""))
                    rat=p.get("rating",0); dist=_ss(p.get("district","") or "")
                    addr=_ss(p.get("address","") or "")[:45]
                    _,cs=cost_est(tl,avg,country)
                    dur=estimate_duration(nm,tl)

                    st.markdown(
                        f'<div class="r-card">'
                        f'<div class="r-name">{nm}</div>'
                        f'<div class="r-meta">{tl}{"&nbsp;·&nbsp;"+dist if dist else ""}</div>'
                        f'{"<div style=font-size:.69rem;color:#c4b5fd>"+addr+"</div>" if addr and "Sample" not in addr else ""}'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:5px">'
                        f'<span style="font-size:.72rem;color:#1e1b4b">{"&#9733; "+str(rat) if rat else ""}</span>'
                        f'<span class="dur-badge">&#128337; {format_duration(dur)}</span>'
                        f'</div>'
                        f'<div class="r-cost">&#128176; {cs}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    # Actions
                    act_cols=st.columns([1,2]) if (user and day_keys) else ([1] if user else [2])
                    if user and day_keys:
                        with act_cols[0]:
                            wl_button(dict(p),key=f"wl_ex_{cn}_{nm[:5]}_{ci}")
                        with act_cols[1]:
                            sel_day=st.selectbox("",["day..."]+day_keys,
                                                  key=f"atd_{cn}_{nm[:5]}_{ci}",
                                                  label_visibility="collapsed")
                            if sel_day!="day..." and st.button("+",
                                                                key=f"atdb_{cn}_{nm[:5]}_{ci}",
                                                                use_container_width=True):
                                if add_to_day({"name":nm,"lat":p.get("lat",0),"lon":p.get("lon",0),
                                               "type_label":tl,"rating":rat,"address":addr,
                                               "district":dist,"description":_ss(p.get("description",""))},
                                              sel_day):
                                    st.toast(f"Added {nm}!"); st.rerun()
                    elif user:
                        wl_button(dict(p),key=f"wl_ex_{cn}_{nm[:5]}_{ci}")

# ══════════════════════════════════════════════════════════════════
# BUDGET SUMMARY
# ══════════════════════════════════════════════════════════════════
def render_budget(itinerary,day_budgets,country,days):
    if not itinerary: return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*days
    sym,rate=_local_rate(country); tots=[]
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        du=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
        t=sum(cost_est(s.get("type_label",""),du,country)[0]
              +tr_cost((s.get("transport_to_next") or {}).get("distance_km",0) or 0,du,country)[0]
              for s in stops)
        tots.append((dl,t,du))
    if not tots: return
    st.markdown(f'<div class="s-lbl">{_t("budget_heading")}</div>',unsafe_allow_html=True)
    gt=sum(t for _,t,_ in tots); gb=sum(d for _,_,d in tots)
    nc=min(len(tots),4)+1; cols=st.columns(nc); any_over=False
    for i,(dl,t,du) in enumerate(tots):
        with cols[i%(nc-1)]:
            over=t>du*1.1
            if over: any_over=True
            lb,_=budget_level(du)
            lo_u=round(t*.8); hi_u=round(t*1.2)
            rng=(f"${lo_u}-${hi_u}" if country=="US"
                 else f"${lo_u}-${hi_u} ({sym}{round(lo_u*rate)}-{sym}{round(hi_u*rate)})")
            st.markdown(
                f'<div class="b-card"><div class="b-lbl">{_ss(dl)}</div>'
                f'<div class="b-amt">${round(t)}{"!" if over else ""}</div>'
                f'<div class="b-sub">{rng}</div>'
                f'<div class="b-sub">{lb} &middot; ${du}/day</div></div>',
                unsafe_allow_html=True,
            )
    with cols[-1]:
        lo=round(gt*.8); hi=round(gt*1.2)
        gs=(f"${lo}-${hi}" if country=="US"
            else f"${lo}-${hi} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})")
        st.markdown(
            f'<div class="b-card" style="border:1.5px solid rgba(139,92,246,.20)">'
            f'<div class="b-lbl">{_t("budget_total")}</div>'
            f'<div class="b-amt" style="font-size:1.55rem;color:#7c3aed">${round(gt)}</div>'
            f'<div class="b-sub">{gs}</div>'
            f'<div class="b-sub">{days}d &middot; ${gb} budget</div></div>',
            unsafe_allow_html=True,
        )
    if any_over:
        st.markdown(f'<div class="warn" style="margin-top:6px">{_t("budget_over")}</div>',
                    unsafe_allow_html=True)
    with st.expander(_t("budget_breakdown")):
        rows=[]
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or not stops: continue
            du=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
            for s in stops:
                tl=s.get("type_label",""); _,cr=cost_est(tl,du,country)
                dur=estimate_duration(_ss(s.get("name","")),tl)
                rows.append({"Day":_ss(dl),"Place":_ss(s.get("name","")),"Type":tl,
                              "Duration":format_duration(dur),"Est.Cost":cr})
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════
# COLLAB
# ══════════════════════════════════════════════════════════════════
def render_collab():
    if not AUTH_OK: return
    user=_cur_user()
    if not user:
        with st.expander(_t("collab_heading"),expanded=False):
            st.caption(_t("auth_login_req"))
        return
    with st.expander(_t("collab_heading"),expanded=False):
        uname=user["username"]
        if st.button(_t("collab_share"),key="cb_gen"):
            import uuid as _u
            try:
                tok=create_collab_link(uname,str(_u.uuid4())[:8])
                st.session_state["_ct"]=tok
            except Exception as e: st.error(str(e))
        if "_ct" in st.session_state:
            st.success(f"Code: **{st.session_state['_ct']}**")
        jc=st.text_input("Join code",key="cb_jc",placeholder="ABCDEFGH")
        if st.button("Join",key="cb_jb"):
            try:
                ok,msg=join_collab(uname,jc)
                (st.success if ok else st.error)(msg)
            except Exception as e: st.error(str(e))

# ══════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════
def build_html(itinerary,city,day_budgets,country):
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    avg=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    def esc(s):
        s=_ss(s)
        return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
    DC=DAY_COLORS; lb,_=budget_level(avg)
    total_stops=sum(len(v) for v in itinerary.values() if isinstance(v,list))
    mjs=[]; pjs=[]; mlats=[]; mlons=[]
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        c=DC[di%len(DC)]; pc=[]
        for si,s in enumerate(stops):
            lat=s.get("lat",0); lon=s.get("lon",0)
            if not lat or not lon: continue
            mlats.append(lat); mlons.append(lon); pc.append(f"[{lat},{lon}]")
            nm_js=esc(s.get("name","")).replace("'","&#39;")
            mjs.append(f'{{"lat":{lat},"lon":{lon},"n":"{nm_js}","d":{di+1},"s":{si+1},"c":"{c}"}}')
        if len(pc)>1: pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')
    clat=sum(mlats)/len(mlats) if mlats else 35.
    clon=sum(mlons)/len(mlons) if mlons else 139.

    # Build timeline for each day
    days_html=""
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        du=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
        c=DC[di%len(DC)]
        tl_stops=build_day_timeline(stops)
        rows_html=""
        for si,s in enumerate(tl_stops):
            arrive=s.get("arrive_time",""); depart=s.get("depart_time","")
            dur=s.get("duration_min",60)
            tr=s.get("transport_to_next") or {}
            route=esc(f"{tr.get('mode','--')} {tr.get('duration','')}") if tr else "Last stop"
            time_str=f"{arrive} - {depart}" if arrive else "--"
            rows_html+=(
                f"<tr><td>{si+1}</td>"
                f"<td>{esc(time_str)}</td>"
                f"<td><b>{esc(s.get('name',''))}</b></td>"
                f"<td>{esc(s.get('type_label',''))}</td>"
                f"<td>{format_duration(dur)}</td>"
                f"<td>{'&#9733; '+str(s.get('rating',0)) if s.get('rating') else '--'}</td>"
                f"<td>{route}</td></tr>"
            )
        total_dur=sum(s.get("duration_min",60) for s in tl_stops)
        days_html+=(
            f"<h3 style='color:{c}'>{esc(dl)} "
            f"&#8212; {len(stops)} stops &middot; ${du}/day &middot; ~{format_duration(total_dur)}</h3>"
            f"<table><thead><tr>"
            f"<th>#</th><th>Time</th><th>Place</th><th>Type</th>"
            f"<th>Duration</th><th>Rating</th><th>Getting There</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>"
        )

    html=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Itinerary - {esc(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:#f5f3ff;color:#1e1b4b;max-width:960px;margin:0 auto;padding:24px}}
h1{{font-size:1.9rem;font-weight:700;letter-spacing:-.03em;margin:0 0 6px}}
h3{{font-size:.98rem;font-weight:700;margin:22px 0 7px}}
.badge{{display:inline-flex;align-items:center;
       background:rgba(139,92,246,.10);border:1px solid rgba(139,92,246,.20);
       border-radius:20px;padding:3px 12px;font-size:.73rem;color:#7c3aed;
       font-weight:600;margin-bottom:14px}}
.summary{{background:rgba(139,92,246,.06);border:1px solid rgba(139,92,246,.14);
         border-radius:11px;padding:10px 14px;font-size:.82rem;color:#6d28d9;margin-bottom:18px}}
#map{{height:400px;border-radius:16px;margin:18px 0;
      box-shadow:0 4px 20px rgba(109,40,217,.10)}}
table{{width:100%;border-collapse:collapse;font-size:.81rem;
       background:rgba(255,255,255,.8);border-radius:10px;overflow:hidden;margin-bottom:6px}}
thead tr{{background:rgba(139,92,246,.08)}}
th,td{{padding:7px 10px;border-bottom:1px solid rgba(139,92,246,.07);text-align:left}}
th{{font-weight:600;color:#7c3aed;font-size:.73rem;text-transform:uppercase;letter-spacing:.04em}}
tr:hover td{{background:rgba(139,92,246,.03)}}
footer{{color:#c4b5fd;font-size:.72rem;margin-top:32px;text-align:center}}
</style>
</head>
<body>
<div class="badge">&#10022; AI Travel Planner</div>
<h1>&#9992; {esc(city.title())}</h1>
<div class="summary">
  ${sum(day_budgets)} total &nbsp;&middot;&nbsp;
  {len(itinerary)} days &nbsp;&middot;&nbsp;
  {total_stops} stops &nbsp;&middot;&nbsp;
  avg ${avg}/day &nbsp;&middot;&nbsp; {lb}
</div>
<div id="map"></div>
{days_html}
<footer>AI Travel Planner &nbsp;&middot;&nbsp; Ctrl+P to save as PDF</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var m=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
  {{attribution:'CartoDB'}}).addTo(m);
[{",".join(mjs)}].forEach(function(mk){{
  var ic=L.divIcon({{
    html:'<div style="width:22px;height:22px;border-radius:50%;background:'+mk.c+
         ';border:2px solid rgba(255,255,255,.9);display:flex;align-items:center;'+
         'justify-content:center;color:white;font-size:10px;font-weight:700">'+mk.s+'</div>',
    iconSize:[22,22],iconAnchor:[11,11]}});
  L.marker([mk.lat,mk.lon],{{icon:ic}})
   .bindPopup('<b>'+mk.n+'</b><br>Day '+mk.d+' Stop '+mk.s).addTo(m);
}});
[{",".join(pjs)}].forEach(function(pl){{
  L.polyline(pl.pts,{{color:pl.c,weight:3,opacity:.55,dashArray:'5 4'}}).addTo(m);
}});
</script>
</body>
</html>"""
    return html.encode("utf-8")

def render_export(itinerary,city,day_budgets,country):
    if not itinerary or not any(isinstance(v,list) and v for v in itinerary.values()): return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    st.markdown(f'<div class="s-lbl">{_t("export_heading")}</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div style="font-weight:600;font-size:.82rem;color:#1e1b4b;margin-bottom:6px">HTML Report</div>',
                    unsafe_allow_html=True)
        try:
            data=build_html(itinerary,city,day_budgets,country)
            st.download_button("Download",data=data,
                               file_name=f"itinerary_{city.lower().replace(' ','_')}.html",
                               mime="text/html;charset=utf-8",use_container_width=True)
            st.caption("Open in browser > Ctrl+P > Save as PDF")
        except Exception as e: st.error(f"Export error: {e}")
    with c2:
        st.markdown('<div style="font-weight:600;font-size:.82rem;color:#1e1b4b;margin-bottom:6px">Google Calendar</div>',
                    unsafe_allow_html=True)
        sd=st.date_input("Start date",key="exp_date",label_visibility="collapsed")
        if sd and itinerary:
            bd=datetime.combine(sd,datetime.min.time())
            SM={"9:00 AM":(9,0),"10:30 AM":(10,30),"12:00 PM":(12,0),"1:30 PM":(13,30),
                "3:00 PM":(15,0),"4:30 PM":(16,30),"6:00 PM":(18,0),"7:30 PM":(19,30)}
            import urllib.parse
            for di,(dl,stops) in enumerate(itinerary.items()):
                if not isinstance(stops,list): continue
                with st.expander(f"{_ss(dl)} ({len(stops)} events)",expanded=False):
                    for si,s in enumerate(stops):
                        nm=_ss(s.get("name","Stop"))
                        hh,mm=SM.get(s.get("time_slot","9:00 AM"),(9+si,0))
                        dd=bd+timedelta(days=di)
                        st2=dd.replace(hour=min(hh,23),minute=mm,second=0)
                        et=st2+timedelta(hours=1,minutes=30)
                        p={"action":"TEMPLATE","text":f"{nm} ({city.title()})",
                           "location":_ss(s.get("address","") or city)[:100],
                           "dates":f"{st2.strftime('%Y%m%dT%H%M%S')}/{et.strftime('%Y%m%dT%H%M%S')}"}
                        url="https://calendar.google.com/calendar/render?"+urllib.parse.urlencode(p)
                        st.markdown(
                            f'<a href="{url}" target="_blank" '
                            f'style="text-decoration:none;color:#7c3aed;font-size:.80rem">'
                            f'+ Stop {si+1}: {nm[:28]}</a>',
                            unsafe_allow_html=True,
                        )

# ══════════════════════════════════════════════════════════════════
# SIDEBAR — simplified
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # Language toggle (compact)
    lang_col1,lang_col2=st.columns(2)
    with lang_col1:
        if st.button("EN",key="lang_en",
                     type="primary" if LANG=="EN" else "secondary",
                     use_container_width=True):
            st.session_state["lang_sel"]="EN"; st.rerun()
    with lang_col2:
        if st.button("ZH",key="lang_zh",
                     type="primary" if LANG=="ZH" else "secondary",
                     use_container_width=True):
            st.session_state["lang_sel"]="ZH"; st.rerun()

    st.markdown("---")

    # Auth (collapsed)
    if AUTH_OK:
        with st.expander("Account",expanded=False):
            render_auth()

    # ── Destination ──
    st.markdown('<div class="sb-lbl">Destination</div>',unsafe_allow_html=True)
    all_c=sorted(WORLD_CITIES.keys())
    prev_c=st.session_state.get("sel_country","")
    sel_country=st.selectbox("Country",[""]+all_c,
                              index=([""] + all_c).index(prev_c) if prev_c in all_c else 0,
                              key="sel_country",label_visibility="collapsed")
    sel_city=""
    if sel_country:
        co=WORLD_CITIES.get(sel_country,[])
        pc=st.session_state.get("sel_city_name","")
        sel_city=st.selectbox("City",co,
                               index=co.index(pc) if pc in co else 0,
                               key="sel_city_name",label_visibility="collapsed")

    city_ov=st.text_input("","",placeholder="Or type any city...",key="city_override")
    if city_ov.strip():   city_input=city_ov.strip()
    elif sel_city:        city_input=sel_city
    elif sel_country:     city_input=sel_country
    else:                 city_input="Tokyo"

    city_key=city_input.strip().lower()
    is_cn=city_key in CN_CITIES; intl_d=INTL_CITIES.get(city_key)
    if is_cn:    city_lat,city_lon=CN_CITIES[city_key]; country="CN"
    elif intl_d: city_lat,city_lon,country=intl_d[0],intl_d[1],intl_d[2]
    else:        city_lat=city_lon=None; country=COUNTRY_CODES.get(sel_country,"INT")

    # ── Optional logistics (collapsed) ──
    with st.expander("Hotel / Start / End points",expanded=False):
        hotel_addr =st.text_input("Hotel", "",placeholder="Hotel name or address",key="h_addr")
        depart_addr=st.text_input("Start","",placeholder="e.g. Tokyo Station",key="d_addr")
        arrive_addr=st.text_input("End",  "",placeholder="e.g. Narita Airport",key="a_addr")

    st.markdown("---")

    # ── Trip settings ──
    st.markdown('<div class="sb-lbl">Trip</div>',unsafe_allow_html=True)
    days=st.number_input("Days",min_value=1,max_value=10,value=3,step=1)
    ndays=int(days)

    sel_types=st.multiselect("Interests",list(PTYPES.keys()),
                              default=["🏛️ Attraction","🍜 Restaurant"],
                              label_visibility="collapsed")
    if not sel_types: sel_types=["🏛️ Attraction"]

    # Budget (single slider — per day)
    budget_usd=st.slider("Daily budget",10,500,60,5,format="$%d")
    cr=fmt_cur(budget_usd,country)
    st.markdown(
        f'<div class="info" style="font-size:.74rem;text-align:center">{cr}/day</div>',
        unsafe_allow_html=True,
    )

    # ── Day areas (collapsed) ──
    # Districts
    dk=f"dists_{city_key}"
    if dk not in st.session_state:
        if is_cn:
            with st.spinner("Loading districts..."):
                st.session_state[dk]=_amap_districts(city_input)
        else: st.session_state[dk]=[]
    amap_dists=st.session_state.get(dk,[])
    adcode_map:dict={}; center_map:dict={}
    for d in amap_dists:
        n,a,la,lo=d.get("name",""),d.get("adcode",""),d.get("lat"),d.get("lon")
        if n and a: adcode_map[n]=a
        if n and la is not None: center_map[n]=(la,lo)
    if is_cn and amap_dists:
        pdo=["Auto"]+[d["name"] for d in amap_dists]
    elif intl_d and len(intl_d)>3:
        pdo=["Auto"]+intl_d[3]
    else:
        dnk=f"dyn_{city_key}"
        if dnk not in st.session_state and city_lat:
            with st.spinner("Loading areas..."):
                st.session_state[dnk]=_nom_districts(city_input)
        dyn=st.session_state.get(dnk,[])
        pdo=(["Auto"]+dyn) if dyn else ["Auto"]

    with st.expander("Day areas & stops",expanded=False):
        day_quotas=[]; day_adcodes=[]; day_district_names=[]
        day_anchor_lats=[]; day_anchor_lons=[]; day_min_ratings=[]
        day_budgets=[]

        if ndays<=7:
            tabs=st.tabs([f"D{d+1}" for d in range(ndays)])
            for di,tab in enumerate(tabs):
                with tab:
                    ds=st.selectbox("Area",pdo,key=f"da_{di}",label_visibility="collapsed")
                    auto=(ds=="Auto")
                    if auto:
                        day_adcodes.append(""); day_district_names.append("")
                        day_anchor_lats.append(city_lat); day_anchor_lons.append(city_lon)
                    else:
                        day_adcodes.append(adcode_map.get(ds,""))
                        day_district_names.append(ds)
                        dlat,dlon=center_map.get(ds,(city_lat,city_lon))
                        day_anchor_lats.append(dlat); day_anchor_lons.append(dlon)
                    mr=st.slider("Min rating",0.,5.,3.5,.5,key=f"mr_{di}")
                    day_min_ratings.append(mr)
                    day_budgets.append(budget_usd)
                    quota={}
                    for tl in sel_types:
                        n=st.slider(tl,0,5,1,1,key=f"q_{di}_{tl}")
                        if n>0: quota[tl]=n
                    if not quota: quota={sel_types[0]:1}
                    day_quotas.append(quota)
        else:
            ds=st.selectbox("Area",pdo,key="da_all",label_visibility="collapsed")
            auto=(ds=="Auto")
            _adc="" if auto else adcode_map.get(ds,"")
            _dn="" if auto else ds
            _alat,_alon=(center_map.get(ds,(city_lat,city_lon)) if not auto else (city_lat,city_lon))
            day_adcodes=[_adc]*ndays; day_district_names=[_dn]*ndays
            day_anchor_lats=[_alat]*ndays; day_anchor_lons=[_alon]*ndays
            mr=st.slider("Min rating",0.,5.,3.5,.5,key="mr_all")
            day_min_ratings=[mr]*ndays; day_budgets=[budget_usd]*ndays
            quota={}
            for tl in sel_types:
                n=st.slider(tl,0,5,1,1,key=f"qa_{tl}")
                if n>0: quota[tl]=n
            if not quota: quota={sel_types[0]:1}
            day_quotas=[dict(quota)]*ndays

    total_quota=sum(sum(q.values()) for q in day_quotas) if day_quotas else 4
    lpt=max(25,total_quota*5)

    st.markdown("---")

    # ── Build buttons ──
    if "seed" not in st.session_state: st.session_state.seed=42
    gen=st.button("Build Itinerary",use_container_width=True,type="primary",key="gen_btn")
    ref=st.button("Shuffle Places",use_container_width=True,key="ref_btn")
    if ref:
        st.session_state.seed=random.randint(1,99999)
        st.cache_data.clear(); gen=True

    # ── Wishlist (collapsed) ──
    _su=_cur_user()
    if _su:
        with st.expander("Wishlist",expanded=False):
            render_wishlist_sidebar(_su["username"])
        if POINTS_OK:
            with st.expander("Points",expanded=False):
                try: render_points_panel(_su["username"],LANG)
                except Exception as _e: st.error(f"Points: {_e}")

    # API status (tiny)
    st.markdown("---")
    if is_cn:
        if AMAP_KEY:
            st.markdown('<div class="ok" style="font-size:.70rem">&#10003; Amap API connected</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="warn" style="font-size:.70rem">Amap key missing — add APIKEY in Secrets</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Data: OpenStreetMap")

# ══════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════
st.markdown(
    f'<div class="hero">'
    f'<div class="hero-badge">&#10022; AI-Powered Travel</div>'
    f'<div class="hero-title">Travel Planner</div>'
    f'<div class="hero-sub">Your intelligent journey companion</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# MAIN DISPLAY
# ══════════════════════════════════════════════════════════════════
def _display(it,df,ci,nd,bud,ctr,tys,lat,lon,hc,dc,ac,d_dist=None):
    real=sum(len(v) for v in it.values() if isinstance(v,list)) if it else 0
    avg_r=df["rating"].replace(0,float("nan")).mean()
    du=round(sum(bud)/len(bud)) if bud else 60
    bstr=f"${sum(bud)}" if len(set(bud))>1 else f"${du}/day"

    for c,(lbl,val) in zip(st.columns(5),[
        ("Places",str(len(df))),("Days",str(nd)),("Stops",str(real)),
        ("Avg Rating",f"{avg_r:.1f}" if not math.isnan(avg_r) else "--"),
        ("Budget",bstr),
    ]):
        c.metric(lbl,val)

    # Save itinerary to wishlist
    user=_cur_user()
    if user and it:
        c1,_=st.columns([1,3])
        with c1:
            if st.button(f"♥ Save itinerary",key="save_itin",use_container_width=True):
                save_itin(user["username"],it,ci,ci.title())
                st.toast(f"Itinerary for {ci.title()} saved!")

    st.markdown(
        f'<div class="s-lbl">&#128203; {_ss(ci).title()}'
        f'{"&nbsp;&middot;&nbsp;"+("&nbsp;·&nbsp;".join(_ss(t) for t in tys)) if tys else ""}</div>',
        unsafe_allow_html=True,
    )

    render_table(df,it,bud,ctr,ci,day_districts=d_dist or [""]*nd,sel_types=tys)
    render_budget(it,bud,ctr,nd)

    if TRANSPORT_OK and it:
        with st.expander(_t("transport_cmp"),expanded=False):
            for di,(dl,stops) in enumerate(it.items()):
                if not isinstance(stops,list) or len(stops)<2: continue
                du=bud[di] if di<len(bud) else 60
                st.markdown(f"**{_ss(dl)}**")
                for si in range(len(stops)-1):
                    a,b=stops[si],stops[si+1]
                    if not (a.get("lat") and b.get("lat")): continue
                    try:
                        st.markdown(render_transport_comparison(
                            a["lat"],a["lon"],b["lat"],b["lon"],
                            _ss(a["name"]),_ss(b["name"]),
                            country=ctr,city=ci,daily_usd=du,lang=LANG),
                            unsafe_allow_html=True)
                    except Exception: pass

    st.markdown(f'<div class="s-lbl">{_t("map_heading")}</div>',unsafe_allow_html=True)
    st.caption(_t("map_caption"))
    try:
        m=build_map(df,lat,lon,it,hc,dc,ac)
        st_folium(m,width="100%",height=500,returned_objects=[])
    except Exception as e:
        st.error(_t("err_map_fail",err=str(e)))

    render_collab()
    render_export(it,ci,bud,ctr)

# ══════════════════════════════════════════════════════════════════
# GENERATE
# ══════════════════════════════════════════════════════════════════
if gen:
    if is_cn:
        lat,lon=city_lat,city_lon
        if lat is None:
            c=_amap_geo(city_input)
            if c: lat,lon=c
            else: st.error(_t("err_city_nf",city=city_input)); st.stop()
    elif intl_d:
        lat,lon=intl_d[0],intl_d[1]
    else:
        with st.spinner("Finding destination..."):
            coord=_nom(city_input)
            if not coord: st.error(_t("err_city_nf",city=city_input)); st.stop()
            lat,lon=coord

    hotel_c=depart_c=arrive_c=None
    with st.spinner("Looking up locations..."):
        if hotel_addr:  hotel_c =_geocode(hotel_addr, city_input,is_cn)
        if depart_addr: depart_c=_geocode(depart_addr,city_input,is_cn)
        if arrive_addr: arrive_c=_geocode(arrive_addr,city_input,is_cn)

    with st.spinner(f"Discovering places in {city_input.title()}..."):
        try:
            df,warn=fetch_places(
                lat,lon,country,is_cn,
                tuple(sel_types),lpt,
                tuple(day_adcodes),tuple(day_district_names),
                tuple(day_anchor_lats),tuple(day_anchor_lons),
                st.session_state.seed,
            )
        except Exception as e: st.error(f"Search error: {e}"); st.stop()

    if warn: st.markdown(f'<div class="warn">{warn}</div>',unsafe_allow_html=True)
    if df is None or df.empty: st.error(_t("err_no_places")); st.stop()

    itinerary={}
    if not AI_OK:
        st.error(f"ai_planner error: {_AI_ERR}")
    else:
        with st.spinner("Crafting your itinerary..."):
            try:
                itinerary=generate_itinerary(
                    df,ndays,day_quotas,
                    hotel_lat  =hotel_c[0]  if hotel_c  else None,
                    hotel_lon  =hotel_c[1]  if hotel_c  else None,
                    depart_lat =depart_c[0] if depart_c else None,
                    depart_lon =depart_c[1] if depart_c else None,
                    arrive_lat =arrive_c[0] if arrive_c else None,
                    arrive_lon =arrive_c[1] if arrive_c else None,
                    day_min_ratings=day_min_ratings,
                    day_anchor_lats=day_anchor_lats,
                    day_anchor_lons=day_anchor_lons,
                    country=country,city=city_input,
                    day_budgets=day_budgets,
                )
            except Exception as e:
                st.error(_t("err_itin_fail",err=str(e)))

    if itinerary:
        st.session_state.update({
            "_itin":itinerary,"_df":df,"_city":city_input,
            "_ndays":ndays,"_budgets":day_budgets,"_country":country,
            "_types":list(sel_types),"_lat":lat,"_lon":lon,
            "_hotel":hotel_c,"_depart":depart_c,"_arrive":arrive_c,
            "_lang":LANG,"_districts":list(day_district_names),
        })
        user=_cur_user()
        if user:
            save_itin(user["username"],itinerary,city_input,city_input.title())
            if POINTS_OK:
                try: add_points(user["username"],"share",note=city_input)
                except Exception: pass

    _display(itinerary,df,city_input,ndays,day_budgets,country,
             sel_types,lat,lon,hotel_c,depart_c,arrive_c,
             d_dist=day_district_names)

elif "_itin" in st.session_state and "_df" in st.session_state:
    _display(
        st.session_state["_itin"],
        st.session_state["_df"],
        st.session_state.get("_city",    city_input),
        st.session_state.get("_ndays",   ndays),
        st.session_state.get("_budgets", day_budgets),
        st.session_state.get("_country", country),
        st.session_state.get("_types",   list(sel_types)),
        st.session_state.get("_lat",     city_lat or 35.),
        st.session_state.get("_lon",     city_lon or 139.),
        st.session_state.get("_hotel"),
        st.session_state.get("_depart"),
        st.session_state.get("_arrive"),
        d_dist=st.session_state.get("_districts",[""] * ndays),
    )

else:
    # Welcome
    st.markdown(
        '<div class="wc-grid">'
        '<div class="wc"><div class="wc-i">&#10022;</div>'
        '<div class="wc-t">Personalised</div><div class="wc-d">Mix any place types</div></div>'
        '<div class="wc"><div class="wc-i">&#128336;</div>'
        '<div class="wc-t">Time-accurate</div><div class="wc-d">Each stop has duration</div></div>'
        '<div class="wc"><div class="wc-i">&#9711;</div>'
        '<div class="wc-t">AI Must-See</div><div class="wc-d">Daily famous highlights</div></div>'
        '<div class="wc"><div class="wc-i">&#9825;</div>'
        '<div class="wc-t">Wishlist</div><div class="wc-d">Save & re-add places</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center;color:#c4b5fd;font-size:.82rem;margin-top:24px">'
        'Choose a destination in the sidebar &#8594; tap <b>Build Itinerary</b></div>',
        unsafe_allow_html=True,
    )
