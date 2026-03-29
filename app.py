"""
app.py v14 — AI Travel Planner Pro
Fixes: encoding/garbled text, itinerary wishlist, add-to-day from extras,
       AI daily must-see, lavender+white+glass UI
"""

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

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# API KEYS
# ══════════════════════════════════════════════════════════════════
def _get_secret(key: str) -> str:
    try:
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, "")

AMAP_KEY     = _get_secret("APIKEY")
DEEPSEEK_KEY = _get_secret("DEEPSEEKKEY")

# ══════════════════════════════════════════════════════════════════
# LANG
# ══════════════════════════════════════════════════════════════════
if "lang_sel" not in st.session_state:
    st.session_state["lang_sel"] = "EN — English"
LANG = "ZH" if st.session_state["lang_sel"].startswith("ZH") else "EN"

# ══════════════════════════════════════════════════════════════════
# i18n — pure ASCII fallback keys to avoid encoding issues
# ══════════════════════════════════════════════════════════════════
try:
    from i18n import t as _ti
    def _t(key, **kw): return _ti(key, LANG, **kw)
    I18N_OK = True
except Exception:
    I18N_OK = False
    _FB = {
        "hero_title":        "Travel Planner",
        "hero_subtitle":     "Your intelligent journey companion",
        "where_heading":     "Destination",
        "pick_country":      "Country / Region",
        "pick_city":         "City",
        "city_override":     "Or type any city",
        "city_placeholder":  "e.g. Kyoto, Paris, Dubai",
        "hotel_label":       "Hotel / Accommodation",
        "hotel_placeholder": "Hotel name or address",
        "depart_label":      "Starting point",
        "depart_placeholder":"e.g. Tokyo Station",
        "arrive_label":      "Final departure point",
        "arrive_placeholder":"e.g. Narita Airport",
        "plan_heading":      "Trip Details",
        "how_many_days":     "Duration (days)",
        "what_todo":         "Interests",
        "day_prefs_heading": "Daily Preferences",
        "day_prefs_caption": "Customize each day's focus and budget.",
        "area_label":        "Area",
        "min_rating_label":  "Min Rating",
        "daily_budget_label":"Daily Budget (USD)",
        "all_area_label":    "Area (all days)",
        "build_btn":         "Build Itinerary",
        "refresh_btn":       "Shuffle Places",
        "loading_districts": "Loading districts...",
        "loading_nbhds":     "Loading neighbourhoods...",
        "finding_dest":      "Finding destination...",
        "looking_up":        "Looking up locations...",
        "finding_places":    "Discovering places in",
        "building_itin":     "Crafting your itinerary...",
        "metric_places":     "Places",
        "metric_days":       "Days",
        "metric_stops":      "Stops",
        "metric_rating":     "Avg Rating",
        "metric_budget":     "Budget",
        "map_heading":       "Route Map",
        "map_caption":       "Tap markers for details",
        "budget_heading":    "Cost Estimate",
        "budget_over":       "Some days may exceed budget.",
        "budget_total":      "Total",
        "budget_breakdown":  "Breakdown",
        "export_heading":    "Export",
        "export_dl":         "Download HTML",
        "export_dl_btn":     "Download",
        "export_cal":        "Google Calendar",
        "export_date":       "Start date",
        "export_caption":    "Open in browser > Print > Save as PDF",
        "rec_heading":       "Explore More",
        "rec_caption":       "Places worth discovering.",
        "rec_refresh":       "Shuffle",
        "wishlist_heading":  "Wishlist",
        "wishlist_empty":    "Your wishlist is empty.",
        "wishlist_save_itin":"Save Itinerary",
        "wishlist_saved":    "Saved",
        "points_heading":    "Points",
        "auth_login":        "Sign In",
        "auth_register":     "Register",
        "auth_logout":       "Sign Out",
        "auth_username":     "Username",
        "auth_password":     "Password",
        "auth_email":        "Email",
        "auth_login_req":    "Sign in to continue.",
        "collab_heading":    "Collaborate",
        "collab_share":      "Share Code",
        "err_city_nf":       "City '{city}' not found.",
        "err_itin_fail":     "Itinerary error: {err}",
        "err_map_fail":      "Map error: {err}",
        "err_no_places":     "No places found.",
        "err_export_fail":   "Export error: {err}",
        "data_source":       "Data",
        "last_stop":         "Last stop",
        "transport_cmp":     "Transport Options",
        "swap_heading":      "Swap Stop",
        "ai_rec_heading":    "AI Must-See Picks",
        "ai_rec_caption":    "Curated highlights for your destination",
        "add_to_day":        "Add to Day",
        "added_to_day":      "Added!",
        "save_place":        "Save Place",
    }
    def _t(key, **kw):
        text = _FB.get(key, key)
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
# LAVENDER + WHITE + GLASS CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* Background — soft lavender gradient */
.stApp {
    background: linear-gradient(135deg,
        #f3f0ff 0%,
        #ede9fe 25%,
        #f5f3ff 50%,
        #faf5ff 75%,
        #f8f4ff 100%) !important;
    min-height: 100vh;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.68) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    border-right: 1px solid rgba(139,92,246,0.12) !important;
}

/* Main container */
.main .block-container {
    padding: 1.8rem 2.2rem 4rem;
    max-width: 1080px;
}

/* ── Glass card base ── */
.glass {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255,255,255,0.90);
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(109,40,217,0.06),
                0 1px 4px rgba(0,0,0,0.04);
}

/* ── Hero ── */
.hero-box {
    background: linear-gradient(135deg,
        rgba(237,233,254,0.85) 0%,
        rgba(245,243,255,0.85) 50%,
        rgba(250,245,255,0.85) 100%);
    backdrop-filter: blur(30px) saturate(180%);
    -webkit-backdrop-filter: blur(30px) saturate(180%);
    border: 1px solid rgba(255,255,255,0.92);
    border-radius: 28px;
    padding: 38px 36px 32px;
    margin-bottom: 24px;
    box-shadow: 0 8px 40px rgba(109,40,217,0.08),
                0 1px 0 rgba(255,255,255,0.9) inset;
    position: relative;
    overflow: hidden;
}
.hero-box::before {
    content: '';
    position: absolute; top: -80px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle,
        rgba(139,92,246,0.14) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-box::after {
    content: '';
    position: absolute; bottom: -50px; left: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle,
        rgba(196,181,253,0.18) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(139,92,246,0.10);
    border: 1px solid rgba(139,92,246,0.20);
    border-radius: 20px; padding: 4px 14px;
    font-size: .76rem; color: #7c3aed; font-weight: 600;
    letter-spacing: .03em; margin-bottom: 14px;
}
.hero-title {
    font-size: 2.3rem; font-weight: 700;
    letter-spacing: -0.03em; color: #1e1b4b;
    margin: 0 0 8px; line-height: 1.1;
}
.hero-sub {
    font-size: 1rem; color: #6b7280;
    font-weight: 400; margin: 0;
}

/* ── Section label ── */
.sec-label {
    font-size: .68rem; font-weight: 700;
    color: #a78bfa; text-transform: uppercase;
    letter-spacing: .08em; margin: 24px 0 10px;
}

/* ── Day header ── */
.day-header {
    display: flex; align-items: center; gap: 12px;
    padding: 13px 18px;
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.92);
    border-radius: 16px;
    margin: 20px 0 6px;
    box-shadow: 0 2px 12px rgba(109,40,217,0.05);
}
.day-dot {
    width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}
.day-title {
    font-weight: 700; font-size: .88rem; color: #1e1b4b; flex: 1;
}
.day-meta { font-size: .74rem; color: #9ca3af; }

/* ── Stop card ── */
.stop-card {
    background: rgba(255,255,255,0.68);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.88);
    border-radius: 14px; padding: 13px 15px;
    margin-bottom: 7px;
    box-shadow: 0 1px 8px rgba(109,40,217,0.04);
}
.stop-num {
    width: 25px; height: 25px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    color: #fff; font-size: 10px; font-weight: 700;
}
.stop-name  { font-weight: 600; font-size: .87rem; color: #1e1b4b; }
.stop-meta  { font-size: .73rem; color: #9ca3af; }
.stop-cost  { font-size: .72rem; color: #7c3aed; font-weight: 500; }

/* ── Transport chip ── */
.tr-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.16);
    border-radius: 20px; padding: 2px 9px;
    font-size: .71rem; color: #7c3aed; font-weight: 500;
}

/* ── Pill variants ── */
.pill {
    display: inline-flex; align-items: center; gap: 5px;
    border-radius: 20px; padding: 3px 10px;
    font-size: .73rem; font-weight: 500;
}
.pill-violet { background:rgba(139,92,246,.10);color:#7c3aed;border:1px solid rgba(139,92,246,.20); }
.pill-rose   { background:rgba(244,63,94,.09); color:#e11d48;border:1px solid rgba(244,63,94,.18);  }
.pill-green  { background:rgba(34,197,94,.09); color:#16a34a;border:1px solid rgba(34,197,94,.18);  }
.pill-amber  { background:rgba(245,158,11,.09);color:#d97706;border:1px solid rgba(245,158,11,.18); }
.pill-sky    { background:rgba(56,189,248,.09);color:#0284c7;border:1px solid rgba(56,189,248,.18); }

/* ── Budget card ── */
.bsum-card {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.90);
    border-radius: 16px; padding: 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(109,40,217,0.05);
}
.bsum-card .d-lbl {
    font-size: .68rem; color: #a78bfa; font-weight: 600;
    text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px;
}
.bsum-card .d-amt {
    font-size: 1.5rem; font-weight: 700;
    color: #1e1b4b; letter-spacing: -.02em;
}
.bsum-card .d-rng  { font-size: .69rem; color: #c4b5fd; margin-top: 2px; }
.bsum-card .d-bud  { font-size: .70rem; color: #9ca3af; margin-top: 4px; }

/* ── Rec card ── */
.rec-grid { display:flex; flex-wrap:wrap; gap:10px; margin:8px 0; }
.rec-card {
    background: rgba(255,255,255,0.68);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.88);
    border-radius: 14px; padding: 13px;
    flex: 1; min-width: 170px; max-width: 230px;
    box-shadow: 0 1px 8px rgba(109,40,217,0.04);
    position: relative;
}
.rc-name { font-weight: 600; font-size: .83rem; color: #1e1b4b; margin-bottom: 3px; }
.rc-meta { color: #9ca3af; font-size: .72rem; }
.rc-badge {
    position: absolute; top: 10px; right: 10px;
    background: rgba(139,92,246,0.08);
    border-radius: 8px; padding: 2px 7px;
    font-size: .70rem; color: #7c3aed; font-weight: 500;
}

/* ── AI rec panel ── */
.ai-panel {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.88);
    border-radius: 18px; padding: 18px; margin: 14px 0;
    box-shadow: 0 4px 20px rgba(109,40,217,0.06);
}
.ai-item {
    background: rgba(255,255,255,0.78);
    border-radius: 10px; padding: 11px 13px; margin: 6px 0;
    border-left: 3px solid #a78bfa;
}

/* ── Swap panel ── */
.swap-panel {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.88);
    border-radius: 16px; padding: 16px; margin: 8px 0;
    box-shadow: 0 4px 16px rgba(109,40,217,0.05);
}

/* ── User card ── */
.user-card {
    background: rgba(139,92,246,0.06);
    border: 1px solid rgba(139,92,246,0.14);
    border-radius: 14px; padding: 12px 14px;
    margin-bottom: 10px;
    display: flex; align-items: center; gap: 10px;
}
.user-av {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg,#8b5cf6,#a78bfa);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 700; font-size: .88rem; flex-shrink: 0;
}
.user-name { font-weight: 600; font-size: .84rem; color: #1e1b4b; }
.user-pts  { font-size: .71rem; color: #a78bfa; }

/* ── Welcome cards ── */
.welcome-grid { display:flex; gap:12px; flex-wrap:wrap; margin-top:8px; }
.welcome-card {
    background: rgba(255,255,255,0.70);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.88);
    border-radius: 18px; padding: 22px 18px;
    flex:1; min-width:145px;
    box-shadow: 0 2px 12px rgba(109,40,217,0.05);
    text-align: center; transition: all .2s ease;
}
.welcome-card:hover {
    box-shadow: 0 8px 28px rgba(109,40,217,0.10);
    transform: translateY(-2px);
}
.wc-icon  { font-size:1.5rem; margin-bottom:10px; }
.wc-title { font-weight:700; font-size:.87rem; color:#1e1b4b; margin-bottom:4px; }
.wc-desc  { font-size:.75rem; color:#9ca3af; line-height:1.4; }

/* ── Banners ── */
.banner-ok   { background:rgba(34,197,94,.08); border:1px solid rgba(34,197,94,.18);
               border-radius:12px; padding:10px 14px; font-size:.81rem; color:#15803d; margin:6px 0; }
.banner-warn { background:rgba(245,158,11,.08); border:1px solid rgba(245,158,11,.18);
               border-radius:12px; padding:10px 14px; font-size:.81rem; color:#b45309; margin:6px 0; }
.banner-info { background:rgba(139,92,246,.08); border:1px solid rgba(139,92,246,.18);
               border-radius:12px; padding:10px 14px; font-size:.81rem; color:#6d28d9; margin:6px 0; }

/* ── Map heading ── */
.map-head {
    font-size: .68rem; font-weight: 700; color: #a78bfa;
    text-transform: uppercase; letter-spacing: .08em; margin: 22px 0 8px;
}

/* ── Streamlit widget overrides ── */
.stButton > button {
    border-radius: 11px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important; font-size: .82rem !important;
    border: 1px solid rgba(139,92,246,0.18) !important;
    background: rgba(255,255,255,0.82) !important;
    color: #1e1b4b !important;
    backdrop-filter: blur(10px) !important;
    transition: all .15s ease !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.96) !important;
    box-shadow: 0 2px 14px rgba(109,40,217,0.12) !important;
    border-color: rgba(139,92,246,0.30) !important;
}
/* Primary button */
div[data-testid="stButton"] button[kind="primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#8b5cf6,#7c3aed) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 4px 16px rgba(109,40,217,0.28) !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg,#7c3aed,#6d28d9) !important;
    box-shadow: 0 6px 22px rgba(109,40,217,0.38) !important;
}
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: 10px !important;
    border: 1px solid rgba(139,92,246,0.14) !important;
    background: rgba(255,255,255,0.80) !important;
    backdrop-filter: blur(10px) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: .82rem !important; color: #1e1b4b !important;
}
.stSlider > div > div > div > div { background: #8b5cf6 !important; }
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.60) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 12px !important; padding: 3px !important;
    gap: 2px !important;
    border: 1px solid rgba(255,255,255,0.82) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important; font-size: .78rem !important;
    font-weight: 500 !important; padding: 5px 12px !important;
    color: #9ca3af !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.92) !important;
    color: #1e1b4b !important;
    box-shadow: 0 1px 4px rgba(109,40,217,0.08) !important;
}
.stExpander {
    background: rgba(255,255,255,0.65) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255,255,255,0.88) !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 6px rgba(109,40,217,0.04) !important;
    overflow: hidden !important;
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.72) !important;
    border-radius: 14px !important; padding: 12px 16px !important;
    border: 1px solid rgba(255,255,255,0.90) !important;
    box-shadow: 0 2px 8px rgba(109,40,217,0.04) !important;
    backdrop-filter: blur(12px) !important;
}
div[data-testid="stMetric"] label {
    font-size: .68rem !important; color: #a78bfa !important;
    text-transform: uppercase !important; letter-spacing: .06em !important;
    font-weight: 600 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 1.35rem !important; font-weight: 700 !important;
    color: #1e1b4b !important; letter-spacing: -.02em !important;
}
.stAlert { border-radius: 12px !important; border: none !important; }
.stCaption { color: #c4b5fd !important; font-size: .72rem !important; }
hr { border:none; border-top:1px solid rgba(139,92,246,0.10) !important; margin:16px 0 !important; }
.sidebar-lbl {
    font-size: .67rem; font-weight: 700; color: #a78bfa;
    text-transform: uppercase; letter-spacing: .08em; margin: 14px 0 6px;
}
div[data-testid="stDownloadButton"] button {
    background: rgba(139,92,246,0.10) !important;
    color: #7c3aed !important;
    border: 1px solid rgba(139,92,246,0.20) !important;
    border-radius: 11px !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
BUDGET_LEVELS_USD = [
    (0,   30,  "Economy",  "#16a34a"),
    (30,  80,  "Standard", "#d97706"),
    (80,  200, "Comfort",  "#dc2626"),
    (200, 9999,"Luxury",   "#7c3aed"),
]

def budget_level(usd):
    for lo, hi, lb, bc in BUDGET_LEVELS_USD:
        if usd < hi: return lb, bc
    return "Luxury", "#7c3aed"

CURRENCIES = {
    "CN": [("USD","$",1.0),("CNY","CNY ",7.25)],
    "JP": [("USD","$",1.0),("JPY","JPY ",155)],
    "KR": [("USD","$",1.0),("KRW","KRW ",1350)],
    "TH": [("USD","$",1.0),("THB","THB ",36)],
    "SG": [("USD","$",1.0),("SGD","SGD ",1.35)],
    "FR": [("USD","$",1.0),("EUR","EUR ",0.92)],
    "GB": [("USD","$",1.0),("GBP","GBP ",0.79)],
    "IT": [("USD","$",1.0),("EUR","EUR ",0.92)],
    "ES": [("USD","$",1.0),("EUR","EUR ",0.92)],
    "US": [("USD","$",1.0)],
    "AU": [("USD","$",1.0),("AUD","AUD ",1.53)],
    "AE": [("USD","$",1.0),("AED","AED ",3.67)],
    "NL": [("USD","$",1.0),("EUR","EUR ",0.92)],
    "TR": [("USD","$",1.0),("TRY","TRY ",32)],
    "HK": [("USD","$",1.0),("HKD","HKD ",7.82)],
    "TW": [("USD","$",1.0),("TWD","TWD ",32)],
    "ID": [("USD","$",1.0),("IDR","IDR ",16000)],
    "VN": [("USD","$",1.0),("VND","VND ",25000)],
    "MY": [("USD","$",1.0),("MYR","MYR ",4.7)],
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
    return " ~ ".join(parts)

COST_W  = {"🏛️ Attraction":0.18,"🍜 Restaurant":0.25,"☕ Cafe":0.10,
           "🌿 Park":0.04,"🛍️ Shopping":0.22,"🍺 Bar/Nightlife":0.16,
           "🏨 Hotel":0.00,"Transport":0.12}
COST_FL = {"🏛️ Attraction":4,"🍜 Restaurant":6,"☕ Cafe":3,
           "🌿 Park":0,"🛍️ Shopping":8,"🍺 Bar/Nightlife":5,
           "🏨 Hotel":0,"Transport":1}

def cost_estimate(tl, daily_usd, country):
    w  = COST_W.get(tl, .12)
    fl = COST_FL.get(tl, 2)
    pv = max(fl, daily_usd * w / 2)
    lo = pv*.65; hi = pv*1.45; mid = (lo+hi)/2
    sym, rate = _local_rate(country)
    if country == "US":
        return mid, f"${round(lo)}-${round(hi)}"
    return mid, f"${round(lo)}-${round(hi)} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})"

def transport_cost_estimate(dist_km, daily_usd, country):
    base = max(1, daily_usd*.12/5)
    f    = max(1., dist_km/3.)
    lo   = base*f*.7; hi = base*f*1.4; mid = (lo+hi)/2
    sym, rate = _local_rate(country)
    if country == "US":
        return mid, f"${round(lo)}-${round(hi)}"
    return mid, f"${round(lo)}-${round(hi)} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})"

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
    "tokyo":         (35.6762,139.6503,"JP",["Shinjuku","Shibuya","Asakusa","Harajuku","Ginza"]),
    "osaka":         (34.6937,135.5023,"JP",["Dotonbori","Namba","Umeda","Shinsekai"]),
    "kyoto":         (35.0116,135.7681,"JP",["Gion","Arashiyama","Higashiyama","Fushimi"]),
    "seoul":         (37.5665,126.9780,"KR",["Gangnam","Hongdae","Myeongdong","Itaewon"]),
    "bangkok":       (13.7563,100.5018,"TH",["Sukhumvit","Silom","Rattanakosin","Chatuchak"]),
    "singapore":     (1.3521, 103.8198,"SG",["Marina Bay","Clarke Quay","Orchard","Chinatown"]),
    "paris":         (48.8566,2.3522,  "FR",["Le Marais","Montmartre","Saint-Germain","Bastille"]),
    "london":        (51.5072,-0.1276, "GB",["Soho","Covent Garden","Shoreditch","South Bank"]),
    "rome":          (41.9028,12.4964, "IT",["Trastevere","Campo de Fiori","Prati","Vatican"]),
    "barcelona":     (41.3851,2.1734,  "ES",["Gothic Quarter","Eixample","Gracia","El Born"]),
    "new york":      (40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Midtown"]),
    "new york city": (40.7128,-74.0060,"US",["Manhattan","Brooklyn","SoHo","Midtown"]),
    "sydney":        (-33.8688,151.2093,"AU",["Circular Quay","Surry Hills","Newtown","Bondi"]),
    "dubai":         (25.2048,55.2708, "AE",["Downtown","Dubai Marina","Deira","JBR"]),
    "amsterdam":     (52.3676,4.9041,  "NL",["Jordaan","De Pijp","Centrum","Oost"]),
    "istanbul":      (41.0082,28.9784, "TR",["Beyoglu","Sultanahmet","Besiktas","Kadikoy"]),
    "hong kong":     (22.3193,114.1694,"HK",["Central","Tsim Sha Tsui","Mong Kok","Causeway Bay"]),
    "taipei":        (25.0330,121.5654,"TW",["Daan","Xinyi","Zhongzheng","Shilin"]),
    "bali":          (-8.3405,115.0920,"ID",["Seminyak","Ubud","Canggu","Kuta"]),
    "ho chi minh city":(10.7769,106.7009,"VN",["District 1","District 3","Bui Vien"]),
    "kuala lumpur":  (3.1390, 101.6869,"MY",["KLCC","Bukit Bintang","Bangsar","Chow Kit"]),
}

PTYPES = {
    "🏛️ Attraction": {"cn":"jingdian","osm":("tourism","attraction"),"amap":"110000","color":"#8b5cf6"},
    "🍜 Restaurant":  {"cn":"canting",  "osm":("amenity","restaurant"), "amap":"050000","color":"#f59e0b"},
    "☕ Cafe":         {"cn":"kafei",    "osm":("amenity","cafe"),        "amap":"050500","color":"#a78bfa"},
    "🌿 Park":         {"cn":"gongyuan","osm":("leisure","park"),        "amap":"110101","color":"#34d399"},
    "🛍️ Shopping":    {"cn":"gouwu",   "osm":("shop","mall"),           "amap":"060000","color":"#f472b6"},
    "🍺 Bar/Nightlife":{"cn":"jiuba",   "osm":("amenity","bar"),         "amap":"050600","color":"#fb923c"},
    "🏨 Hotel":        {"cn":"jiudian", "osm":("tourism","hotel"),       "amap":"100000","color":"#38bdf8"},
}

# AMAP search keywords
AMAP_KW = {
    "🏛️ Attraction": ["旅游景点","博物馆","历史","景区"],
    "🍜 Restaurant":  ["餐馆","美食","饭店","特色菜"],
    "☕ Cafe":         ["咖啡","下午茶","cafe"],
    "🌿 Park":         ["公园","花园","绿地","广场"],
    "🛍️ Shopping":    ["商场","购物中心","超市","市集"],
    "🍺 Bar/Nightlife":["酒吧","KTV","夜店"],
    "🏨 Hotel":        ["酒店","宾馆","民宿"],
}

DAY_COLORS = ["#8b5cf6","#f59e0b","#34d399","#f472b6","#fb923c","#38bdf8","#a78bfa","#6ee7b7"]

TDESC = {
    "attraction":"Worth a visit","景点":"Worth a visit",
    "restaurant":"Great for a meal","餐":"Great for a meal",
    "cafe":"Perfect coffee break","咖":"Perfect coffee break",
    "park":"Relax outdoors","公园":"Relax outdoors",
    "mall":"Shopping stop","购物":"Shopping stop",
    "bar":"Evening out","酒吧":"Evening out",
    "hotel":"Place to stay","酒店":"Place to stay",
}

def tdesc(s):
    for k, v in TDESC.items():
        if k in str(s).lower(): return v
    return "Local favourite"

CHAIN_BL = ["kfc","mcdonald","starbucks","seven-eleven","family mart","711",
            "lawson","costa coffee"]
def is_chain(n):
    return any(k in n.lower() for k in CHAIN_BL)

def _hav_m(la1, lo1, la2, lo2):
    R = 6371000
    dl = math.radians(la2-la1); dg = math.radians(lo2-lo1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dg/2)**2
    return R*2*math.asin(math.sqrt(min(1.,a)))

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
                if places[j]["rating"] > best["rating"]: best = places[j]
        kept.append(best)
    return kept

def _safe_str(s):
    """Return a clean ASCII-safe string, replacing problematic chars."""
    if s is None: return ""
    s = str(s)
    # Replace common garble-causing chars
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00b7": "·",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s

WORLD_CITIES = {
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
# AI RECOMMENDATIONS — per-day must-see via DeepSeek
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_mustsee(city: str, country: str, days: int,
                   types_tuple: tuple, lang: str = "EN") -> list:
    """
    Returns list of dicts: {name, type, why, tip, rating, lat, lon}
    Uses DeepSeek if available, otherwise curated fallback.
    Always returns English-friendly names to avoid encoding issues.
    """
    types = list(types_tuple)

    # ── DeepSeek ──
    if DEEPSEEK_KEY:
        try:
            type_str = ", ".join(types[:5])
            if lang == "ZH":
                prompt = (
                    f"请为{city}推荐{min(days*3, 15)}个必去的著名景点和体验，"
                    f"适合{days}天行程，类型包括：{type_str}。"
                    f"重要：请给出真实存在的著名地点，不要虚构。"
                    f"返回JSON数组，每项字段：name(英文或拼音名), "
                    f"name_local(当地文字名), type(类型), "
                    f"why(英文推荐理由,15词内), tip(英文实用贴士,12词内), "
                    f"rating(4.0-5.0数字), lat(纬度数字), lon(经度数字)。"
                    f"只返回JSON，不含其他文字。"
                )
            else:
                prompt = (
                    f"Recommend {min(days*3, 15)} must-visit famous attractions in {city} "
                    f"for a {days}-day trip. Types: {type_str}. "
                    f"IMPORTANT: Only real, well-known places. No fictional locations. "
                    f"Return JSON array only. Each item fields: "
                    f"name (English name), name_local (local script name, optional), "
                    f"type (one of the types listed), "
                    f"why (reason to visit, max 12 words), "
                    f"tip (practical tip, max 10 words), "
                    f"rating (number 4.0-5.0), "
                    f"lat (latitude as number), lon (longitude as number). "
                    f"No other text, pure JSON array."
                )
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}",
                         "Content-Type": "application/json"},
                json={"model": "deepseek-chat",
                      "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.4, "max_tokens": 1200},
                timeout=20,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                m = re.search(r'\[.*\]', content, re.DOTALL)
                if m:
                    items = json.loads(m.group())
                    if isinstance(items, list) and items:
                        cleaned = []
                        for it in items[:15]:
                            if not isinstance(it, dict): continue
                            cleaned.append({
                                "name":       _safe_str(it.get("name", "")),
                                "name_local": _safe_str(it.get("name_local", "")),
                                "type":       _safe_str(it.get("type", "Attraction")),
                                "why":        _safe_str(it.get("why", "")),
                                "tip":        _safe_str(it.get("tip", "")),
                                "rating":     float(it.get("rating", 4.5)),
                                "lat":        float(it.get("lat", 0)),
                                "lon":        float(it.get("lon", 0)),
                            })
                        if cleaned:
                            return cleaned
        except Exception:
            pass

    # ── Built-in curated fallback ──
    BUILTIN = {
        "tokyo": [
            {"name":"Senso-ji Temple","type":"🏛️ Attraction","why":"Tokyo oldest temple, stunning gate",
             "tip":"Visit at 6am before crowds","rating":4.9,"lat":35.7148,"lon":139.7967},
            {"name":"Shibuya Crossing","type":"🏛️ Attraction","why":"World famous scramble crossing",
             "tip":"View from Starbucks above","rating":4.8,"lat":35.6595,"lon":139.7004},
            {"name":"Shinjuku Gyoen","type":"🌿 Park","why":"Beautiful garden in city center",
             "tip":"Cherry blossoms in April","rating":4.8,"lat":35.6851,"lon":139.7103},
            {"name":"Tsukiji Outer Market","type":"🍜 Restaurant","why":"Freshest sushi breakfast spot",
             "tip":"Arrive before 9am","rating":4.7,"lat":35.6654,"lon":139.7707},
            {"name":"teamLab Borderless","type":"🏛️ Attraction","why":"Immersive digital art museum",
             "tip":"Book tickets weeks ahead","rating":4.8,"lat":35.6248,"lon":139.7755},
        ],
        "paris": [
            {"name":"Eiffel Tower","type":"🏛️ Attraction","why":"Iconic symbol of Paris",
             "tip":"Book summit tickets 2 weeks ahead","rating":4.8,"lat":48.8584,"lon":2.2945},
            {"name":"Louvre Museum","type":"🏛️ Attraction","why":"World largest art museum",
             "tip":"Wednesday evening has shorter queues","rating":4.8,"lat":48.8606,"lon":2.3376},
            {"name":"Musee d'Orsay","type":"🏛️ Attraction","why":"Best Impressionist collection",
             "tip":"Less crowded than Louvre","rating":4.9,"lat":48.8600,"lon":2.3266},
            {"name":"Montmartre & Sacre-Coeur","type":"🏛️ Attraction","why":"Charming hilltop village",
             "tip":"Go early morning for views","rating":4.7,"lat":48.8867,"lon":2.3431},
            {"name":"Le Marais","type":"🛍️ Shopping","why":"Trendy historic district",
             "tip":"Explore on Sunday afternoon","rating":4.6,"lat":48.8568,"lon":2.3579},
        ],
        "london": [
            {"name":"British Museum","type":"🏛️ Attraction","why":"World class free museum",
             "tip":"Free entry, book timed slot","rating":4.8,"lat":51.5194,"lon":-0.1270},
            {"name":"Tower of London","type":"🏛️ Attraction","why":"900 years of royal history",
             "tip":"Buy tickets online to skip queue","rating":4.7,"lat":51.5081,"lon":-0.0759},
            {"name":"Borough Market","type":"🍜 Restaurant","why":"London best food market",
             "tip":"Thursday to Saturday only","rating":4.8,"lat":51.5055,"lon":-0.0910},
            {"name":"Hyde Park","type":"🌿 Park","why":"Iconic royal park in city center",
             "tip":"Hire a Santander bike","rating":4.7,"lat":51.5073,"lon":-0.1657},
        ],
        "beijing": [
            {"name":"Forbidden City","type":"🏛️ Attraction","why":"World largest palace complex",
             "tip":"Book online tickets in advance","rating":4.9,"lat":39.9163,"lon":116.3972},
            {"name":"Great Wall Mutianyu","type":"🏛️ Attraction","why":"Best restored Great Wall section",
             "tip":"Take cable car up, toboggan down","rating":4.9,"lat":40.4319,"lon":116.5651},
            {"name":"Temple of Heaven","type":"🏛️ Attraction","why":"Ming dynasty ceremonial complex",
             "tip":"Early morning for tai chi","rating":4.8,"lat":39.8822,"lon":116.4066},
            {"name":"Summer Palace","type":"🌿 Park","why":"Imperial garden on lakeside",
             "tip":"Rent a rowboat on Kunming Lake","rating":4.8,"lat":40.0003,"lon":116.2755},
        ],
        "singapore": [
            {"name":"Marina Bay Sands SkyPark","type":"🏛️ Attraction","why":"Iconic skyline views",
             "tip":"Hotel guests get free access","rating":4.8,"lat":1.2834,"lon":103.8607},
            {"name":"Gardens by the Bay","type":"🌿 Park","why":"Futuristic Supertree Grove",
             "tip":"Free outdoor, paid conservatories","rating":4.9,"lat":1.2816,"lon":103.8636},
            {"name":"Hawker Centre Maxwell","type":"🍜 Restaurant","why":"Legendary Hainanese chicken rice",
             "tip":"Tian Tian stall, queue early","rating":4.8,"lat":1.2800,"lon":103.8444},
            {"name":"Chinatown Heritage Centre","type":"🏛️ Attraction","why":"Authentic history of early settlers",
             "tip":"Buy tickets online","rating":4.6,"lat":1.2831,"lon":103.8448},
        ],
        "dubai": [
            {"name":"Burj Khalifa","type":"🏛️ Attraction","why":"World tallest building, iconic views",
             "tip":"Book At the Top tickets online","rating":4.8,"lat":25.1972,"lon":55.2744},
            {"name":"Dubai Mall","type":"🛍️ Shopping","why":"World largest mall experience",
             "tip":"See Dubai Fountain show at 6pm","rating":4.7,"lat":25.1979,"lon":55.2796},
            {"name":"Dubai Museum","type":"🏛️ Attraction","why":"History of Dubai in old fort",
             "tip":"Only AED 3 entry","rating":4.5,"lat":25.2637,"lon":55.2972},
            {"name":"Dubai Frame","type":"🏛️ Attraction","why":"Glass bridge between old and new Dubai",
             "tip":"Best views at sunset","rating":4.7,"lat":25.2353,"lon":55.3003},
        ],
    }
    city_lc = city.strip().lower()
    for k, v in BUILTIN.items():
        if k in city_lc:
            return [dict(it, name_local="") for it in v]
    return []


def get_ai_daily_mustsee(city: str, country: str, day_idx: int,
                          district: str, types: list, lang: str = "EN") -> list:
    """
    Get AI-recommended must-see places for a specific day/district.
    Returns max 4 items.
    """
    all_recs = get_ai_mustsee(city, country, 5, tuple(types), lang)
    if not all_recs:
        return []
    # Rotate recommendations by day so each day shows different picks
    n = len(all_recs)
    if n == 0: return []
    start = (day_idx * 3) % n
    picks = []
    for i in range(min(4, n)):
        picks.append(all_recs[(start + i) % n])
    return picks


# ══════════════════════════════════════════════════════════════════
# GEOCODING
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def _amap_get_districts(city):
    if not city.strip() or not AMAP_KEY: return []
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/config/district",
            params={"key":AMAP_KEY,"keywords":city,"subdistrict":1,
                    "extensions":"base","output":"json"},
            timeout=9,
        ).json()
        if str(r.get("status")) != "1" or not r.get("districts"): return []
        out = []
        for d in r["districts"][0].get("districts", []):
            n = (d.get("name") or "").strip()
            a = (d.get("adcode") or "").strip()
            c = (d.get("center") or "").strip()
            if not (n and a): continue
            lat = lon = None
            if "," in c:
                try: lon, lat = map(float, c.split(","))
                except Exception: pass
            out.append({"name":n,"adcode":a,"lat":lat,"lon":lon})
        return out
    except Exception: return []

@st.cache_data(ttl=3600, show_spinner=False)
def _amap_geocode(addr):
    if not AMAP_KEY: return None
    try:
        r = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"key":AMAP_KEY,"address":addr,"output":"json"},
            timeout=8,
        ).json()
        if str(r.get("status")) == "1" and r.get("geocodes"):
            loc = r["geocodes"][0].get("location","")
            if "," in loc:
                lon, lat = map(float, loc.split(","))
                return lat, lon
    except Exception: pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def _nominatim(q):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q":q,"format":"json","limit":1},
            headers={"User-Agent":"TravelPlannerPro/14"},
            timeout=9,
        ).json()
        if r: return float(r[0]["lat"]), float(r[0]["lon"])
    except Exception: pass
    return None

def _geocode(addr, city, is_cn):
    if not addr.strip(): return None
    if is_cn: return _amap_geocode(f"{addr} {city}") or _nominatim(f"{addr} {city}")
    return _nominatim(f"{addr} {city}") or _nominatim(addr)

@st.cache_data(ttl=3600, show_spinner=False)
def _get_nominatim_districts(city):
    if not city.strip(): return []
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q":city,"format":"json","limit":1},
            headers={"User-Agent":"TravelPlannerPro/14"},
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
                els = requests.post(url,data={"data":q},timeout=18).json().get("elements",[])
                if els: break
            except Exception: continue
        names = []
        for el in els:
            n = el.get("tags",{}).get("name:en") or el.get("tags",{}).get("name","")
            if n and n not in names and len(n) > 1: names.append(n)
        return sorted(names[:25])
    except Exception: return []

# ══════════════════════════════════════════════════════════════════
# PLACE SEARCH
# ══════════════════════════════════════════════════════════════════
def _parse_amap(pois, kw_used, tl, limit, seen):
    out = []
    for p in pois:
        if len(out) + len(seen) >= limit: break
        nm = p.get("name","")
        if not nm or is_chain(nm): continue
        loc = p.get("location","")
        if "," not in (loc or ""): continue
        try: plon, plat = map(float, loc.split(","))
        except Exception: continue
        k = (nm, round(plat,4), round(plon,4))
        if k in seen: continue
        seen.add(k)
        biz = p.get("biz_ext") or {}
        try: rating = float(biz.get("rating") or 0) or 0.0
        except Exception: rating = 0.0
        tel = biz.get("tel") or p.get("tel") or ""
        if isinstance(tel, list): tel = "; ".join(t for t in tel if t)
        addr = p.get("address") or ""
        if isinstance(addr, list): addr = "".join(addr)
        out.append({
            "name":_safe_str(nm),"lat":plat,"lon":plon,"rating":rating,
            "address":_safe_str(str(addr).strip()),
            "phone":_safe_str(str(tel).strip()),
            "website":"","type":kw_used,"type_label":tl,
            "district":_safe_str(p.get("adname") or ""),
            "description":tdesc(kw_used),
        })
    return out

def _amap_search(city_or_adcode, kw, tl, limit, by_adcode=True, lat=None, lon=None):
    if not AMAP_KEY: return [], "No AMAP_KEY"
    places=[]; seen=set(); at=PTYPES.get(tl,{}).get("amap",""); err=None
    url = "https://restapi.amap.com/v3/place/text"

    for pg in range(1, 6):
        if len(places) >= limit: break
        try:
            params = {"key":AMAP_KEY,"keywords":kw,"offset":25,
                      "page":pg,"extensions":"all","output":"json"}
            if by_adcode:
                params.update({"city":city_or_adcode,"citylimit":"true"})
            else:
                params.update({"location":f"{lon},{lat}","radius":8000})
                url = "https://restapi.amap.com/v3/place/around"
            if at: params["types"] = at
            d = requests.get(url, params=params, timeout=10).json()
            if str(d.get("status")) != "1": err=f"{d.get('infocode')}"; break
            ps = d.get("pois") or []
            if not ps: break
            places.extend(_parse_amap(ps, kw, tl, limit, seen))
        except Exception as e: err=str(e); break
    return places[:limit], err

def search_cn(lat, lon, tls, lpt, adcode=""):
    all_p=[]; errs=[]
    for tl in tls:
        kws = AMAP_KW.get(tl, [tl])
        for kw in kws[:2]:
            if adcode:
                ps, e = _amap_search(adcode, kw, tl, lpt//2, by_adcode=True)
            else:
                ps, e = _amap_search(None, kw, tl, lpt//2, by_adcode=False, lat=lat, lon=lon)
            if e: errs.append(e)
            all_p.extend(ps)
    seen, out = set(), []
    for p in all_p:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    return out, errs

def _osm_single(lat, lon, ok, ov, tl, limit, district=""):
    clat, clon = lat, lon
    if district:
        try:
            g = requests.get("https://nominatim.openstreetmap.org/search",
                             params={"q":district,"format":"json","limit":1},
                             headers={"User-Agent":"TravelPlannerPro/14"},timeout=5).json()
            if g: clat, clon = float(g[0]["lat"]), float(g[0]["lon"])
        except Exception: pass
    q = (f'[out:json][timeout:30];(node["{ok}"="{ov}"](around:5000,{clat},{clon});'
         f'way["{ok}"="{ov}"](around:5000,{clat},{clon}););out center {limit*4};')
    els = []
    for url in ["https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter"]:
        try:
            result = requests.post(url,data={"data":q},timeout=28).json().get("elements",[])
            if result: els=result; break
        except Exception: continue
    places = []
    for el in els:
        tags = el.get("tags",{})
        nm = tags.get("name:en") or tags.get("name","")
        if not nm or is_chain(nm): continue
        elat = el.get("lat",0) if el["type"]=="node" else el.get("center",{}).get("lat",0)
        elon = el.get("lon",0) if el["type"]=="node" else el.get("center",{}).get("lon",0)
        if not elat or not elon: continue
        pts = [tags.get(k,"") for k in ["addr:housenumber","addr:street","addr:suburb","addr:city"] if tags.get(k)]
        places.append({
            "name":_safe_str(nm),"lat":elat,"lon":elon,
            "rating":round(random.uniform(3.8,5.0),1),
            "address":_safe_str(", ".join(pts)),
            "phone":_safe_str(tags.get("phone","")),
            "website":_safe_str(tags.get("website","")),
            "type":ov,"type_label":tl,
            "district":_safe_str(tags.get("addr:suburb","")),
            "description":tdesc(ov),
        })
        if len(places) >= limit: break
    return places

def search_intl(lat, lon, tls, lpt, district=""):
    all_p=[]
    for tl in tls:
        ok, ov = PTYPES[tl]["osm"]
        all_p.extend(_osm_single(lat,lon,ok,ov,tl,lpt,district))
    seen, out = set(), []
    for p in all_p:
        k=(p["name"],round(p["lat"],3),round(p["lon"],3))
        if k not in seen: seen.add(k); out.append(p)
    return out

def demo_places(lat, lon, tls, n, seed, district=""):
    random.seed(seed)
    NAMES = {
        "🏛️ Attraction": ["Grand Museum","Sky Tower","Ancient Temple","Art Gallery","Historic Castle","Night Market"],
        "🍜 Restaurant":  ["Sakura Dining","Ramen House","Sushi Master","Street Food Alley","Harbour Grill"],
        "☕ Cafe":         ["Blue Bottle","Artisan Brew","Matcha Corner","Morning Pour","The Cozy Cup"],
        "🌿 Park":         ["Riverside Park","Sakura Garden","Central Park","Bamboo Grove"],
        "🛍️ Shopping":    ["Central Mall","Night Bazaar","Vintage Market","Designer District"],
        "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Garden"],
        "🏨 Hotel":        ["Grand Palace Hotel","Boutique Inn","City View Hotel"],
    }
    centers = [(lat+random.uniform(-.02,.02), lon+random.uniform(-.02,.02)) for _ in range(3)]
    out = []
    for tl in tls:
        nms = list(NAMES.get(tl,["Local Spot"])); random.shuffle(nms)
        for i, nm in enumerate(nms[:n]):
            ci=i%3; clat,clon=centers[ci]
            out.append({
                "name":nm,"lat":round(clat+random.uniform(-.005,.005),5),
                "lon":round(clon+random.uniform(-.005,.005),5),
                "rating":round(random.uniform(4.0,4.9),1),
                "address":"Sample — connect to internet for real data",
                "phone":"","website":"","type":tl,"type_label":tl,
                "district":district or ["North","Central","South"][ci],
                "description":tdesc(tl),
            })
    return out

@st.cache_data(ttl=180, show_spinner=False)
def fetch_all_places(clat, clon, country, is_cn, tls_t, lpt,
                     adcodes_t, dnames_t, alats_t, alons_t, _seed):
    random.seed(_seed)
    tls=list(tls_t); all_raw=[]; warn=None; api_errs=[]; seen_k=set()
    for i in range(len(adcodes_t)):
        adc=adcodes_t[i]; dn=dnames_t[i]
        dlat=alats_t[i] if alats_t[i] is not None else clat
        dlon=alons_t[i] if alons_t[i] is not None else clon
        ck=adc or f"ll_{round(dlat,3)}_{round(dlon,3)}"
        if ck in seen_k: continue
        seen_k.add(ck)
        if is_cn:
            ps, errs = search_cn(dlat, dlon, tls, lpt, adc)
            api_errs.extend(errs)
        else:
            ps = search_intl(dlat, dlon, tls, lpt, dn)
        all_raw.extend(ps)
    seen, out = set(), []
    for p in all_raw:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen: seen.add(k); out.append(p)
    out = geo_dedup(out)
    if not out:
        out = demo_places(clat, clon, tls, lpt, _seed)
        warn = ("Amap API unavailable - showing sample data. Check API key and IP whitelist."
                if is_cn else "Live data unavailable - showing sample places.")
    df = pd.DataFrame(out)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c] = ""
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.)
    # Ensure all string columns are clean
    for c in ["name","address","phone","district","description","type_label","type"]:
        df[c] = df[c].apply(lambda x: _safe_str(x))
    return df.sort_values("rating",ascending=False).reset_index(drop=True), warn

# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    try:
        tok = st.session_state.get("_auth_token","")
        if not tok: return None
        return get_user_from_session(tok)
    except Exception: return None

def render_auth_sidebar():
    if not AUTH_OK: return
    user = _cur_user()
    if user:
        pts = 0
        if POINTS_OK:
            try: pts = get_points(user["username"])
            except Exception: pass
        initial = user["username"][0].upper()
        st.markdown(
            f'<div class="user-card">'
            f'<div class="user-av">{initial}</div>'
            f'<div><div class="user-name">{user["username"]}</div>'
            f'<div class="user-pts">✦ {pts} points</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(_t("auth_logout"), key="auth_lo", use_container_width=True):
            try: logout_user(st.session_state.get("_auth_token",""))
            except Exception: pass
            st.session_state.pop("_auth_token",None)
            st.rerun()
    else:
        t1, t2 = st.tabs([_t("auth_login"), _t("auth_register")])
        with t1:
            u = st.text_input(_t("auth_username"), key="li_u", placeholder="username")
            p = st.text_input(_t("auth_password"), type="password", key="li_p", placeholder="password")
            if st.button(_t("auth_login"), key="li_b", use_container_width=True):
                try:
                    ok, msg, tok = login_user(u, p)
                    if ok:
                        st.session_state["_auth_token"] = tok
                        if POINTS_OK:
                            try: add_points(u,"daily_login")
                            except Exception: pass
                        st.success(msg); st.rerun()
                    else: st.error(msg)
                except Exception as e: st.error(f"Login error: {e}")
        with t2:
            ru  = st.text_input(_t("auth_username"), key="re_u", placeholder="new username")
            re_e = st.text_input(_t("auth_email"),   key="re_e", placeholder="email@example.com")
            rp  = st.text_input(_t("auth_password"), type="password", key="re_p", placeholder="password")
            if st.button(_t("auth_register"), key="re_b", use_container_width=True):
                try:
                    ok, msg = register_user(ru,rp,re_e)
                    (st.success if ok else st.error)(msg)
                except Exception as e: st.error(f"Register error: {e}")

# ══════════════════════════════════════════════════════════════════
# ADD-TO-DAY helper (for extra recs + AI picks)
# ══════════════════════════════════════════════════════════════════
def _add_place_to_day(place_dict: dict, day_key: str):
    """
    Add a place dict to a specific day in the session itinerary.
    place_dict must have: name, lat, lon, type_label, rating
    """
    itin = st.session_state.get("_itin", {})
    if not itin or day_key not in itin:
        st.toast(f"Day {day_key} not found in itinerary", icon="⚠️")
        return False
    stops = itin.get(day_key, [])
    if not isinstance(stops, list): stops = []
    # Check not already in
    existing_names = {s.get("name","") for s in stops}
    if place_dict.get("name","") in existing_names:
        st.toast("Already in this day's itinerary!", icon="ℹ️")
        return False
    # Build stop entry
    new_stop = {
        "name":        place_dict.get("name",""),
        "lat":         place_dict.get("lat", 0),
        "lon":         place_dict.get("lon", 0),
        "type_label":  place_dict.get("type_label", place_dict.get("type","🏛️ Attraction")),
        "rating":      place_dict.get("rating", 4.5),
        "address":     place_dict.get("address",""),
        "district":    place_dict.get("district",""),
        "description": place_dict.get("description",""),
        "time_slot":   "TBD",
        "transport_to_next": None,
    }
    stops.append(new_stop)
    itin[day_key] = stops
    st.session_state["_itin"] = itin
    return True

# ══════════════════════════════════════════════════════════════════
# WISHLIST BUTTON
# ══════════════════════════════════════════════════════════════════
def render_wishlist_button(place_row: dict, btn_key: str):
    if not WISHLIST_OK: return
    user = _cur_user()
    if not user: return
    uname = user["username"]
    nm = place_row.get("name","")
    try: saved = is_in_wishlist(uname, nm)
    except Exception: saved = False
    label = "♥" if saved else "♡"
    if st.button(label, key=btn_key, help="Remove from wishlist" if saved else "Save to wishlist"):
        if saved:
            try: remove_from_wishlist(uname, nm); st.toast(f"Removed {nm}")
            except Exception as e: st.error(str(e))
        else:
            try:
                add_to_wishlist(uname, {
                    "name":place_row.get("name",""),
                    "lat":place_row.get("lat",0),
                    "lon":place_row.get("lon",0),
                    "type":place_row.get("type_label",""),
                    "rating":place_row.get("rating",0),
                    "address":place_row.get("address",""),
                    "district":place_row.get("district",""),
                })
                st.toast(f"Saved {nm}!")
                if POINTS_OK:
                    try: add_points(uname,"wishlist_add",note=nm)
                    except Exception: pass
            except Exception as e: st.error(str(e))
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# MAP
# ══════════════════════════════════════════════════════════════════
def build_map(df, lat, lon, itinerary, hotel_c=None, depart_c=None, arrive_c=None):
    m = folium.Map(location=[lat,lon], zoom_start=13, tiles="CartoDB positron")
    vi = {}
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops):
                vi[s["name"]] = (di, si+1, s)
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or len(stops)<2: continue
            dc = DAY_COLORS[di%len(DAY_COLORS)]
            for si in range(len(stops)-1):
                a,b = stops[si],stops[si+1]
                if not (a.get("lat") and b.get("lat")): continue
                folium.PolyLine([[a["lat"],a["lon"]],[b["lat"],b["lon"]]],
                                color=dc,weight=3,opacity=.60,dash_array="5 4").add_to(m)
    for _,row in df.iterrows():
        v = vi.get(row["name"])
        if v:
            di,sn,_ = v; color=DAY_COLORS[di%len(DAY_COLORS)]; label=str(sn)
            day_info=f"Day {di+1} Stop {sn}"
        else:
            color="#d1d5db"; label="."; day_info="Not scheduled"
        addr = _safe_str(row.get("address",""))
        pop  = (f"<div style='font-family:-apple-system,sans-serif;min-width:160px'>"
                f"<b style='font-size:.88rem'>{_safe_str(row['name'])}</b><br>"
                f"<span style='color:#9ca3af;font-size:.76rem'>&#9733; {row['rating']:.1f} &middot; {day_info}</span>"
                f"{'<br><span style=font-size:.73rem>' + addr[:50] + '</span>' if addr and 'Sample' not in addr else ''}"
                f"</div>")
        folium.Marker(
            [row["lat"],row["lon"]],
            popup=folium.Popup(pop,max_width=220),
            tooltip=f"{day_info} - {_safe_str(row['name'])}",
            icon=folium.DivIcon(
                html=(f'<div style="width:23px;height:23px;border-radius:50%;background:{color};'
                      f'border:2.5px solid rgba(255,255,255,.92);display:flex;align-items:center;'
                      f'justify-content:center;color:white;font-size:10px;font-weight:700;'
                      f'box-shadow:0 2px 8px rgba(109,40,217,.25)">{label}</div>'),
                icon_size=(23,23),icon_anchor=(11,11),
            ),
        ).add_to(m)
    def sm(c,ic,tip):
        folium.Marker(list(c),tooltip=tip,
            icon=folium.DivIcon(html=f'<div style="font-size:20px">{ic}</div>',
                                icon_size=(26,26),icon_anchor=(13,13))).add_to(m)
    if hotel_c:  sm(hotel_c,"🏨","Hotel")
    if depart_c: sm(depart_c,"🚩","Start")
    if arrive_c: sm(arrive_c,"🏁","End")
    return m

# ══════════════════════════════════════════════════════════════════
# INLINE SWAP
# ══════════════════════════════════════════════════════════════════
def render_inline_swap(itinerary, df, day_key, stop_idx):
    if not WISHLIST_OK: st.info("Swap not available."); return
    stops = itinerary.get(day_key,[])
    if not isinstance(stops,list) or stop_idx >= len(stops): return
    cur      = stops[stop_idx]
    cur_type = cur.get("type_label","")
    used     = {s["name"] for sl in itinerary.values() if isinstance(sl,list) for s in sl}
    cands    = (df[(df["type_label"]==cur_type) & (~df["name"].isin(used))]
                .sort_values("rating",ascending=False).head(5))
    if cands.empty: st.warning("No alternatives found."); return
    st.markdown(
        f'<div class="swap-panel"><div style="font-weight:600;font-size:.83rem;'
        f'color:#1e1b4b;margin-bottom:10px">Swap: <b>{_safe_str(cur["name"])}</b></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(min(len(cands),3))
    for i,(_,alt) in enumerate(cands.iterrows()):
        with cols[i%min(len(cands),3)]:
            nm=_safe_str(alt["name"]); rat=alt.get("rating",0); dist=_safe_str(alt.get("district",""))
            st.markdown(
                f'<div style="background:rgba(255,255,255,.78);border-radius:10px;'
                f'padding:10px;border:1px solid rgba(255,255,255,.9);margin-bottom:4px">'
                f'<div style="font-weight:600;font-size:.81rem;color:#1e1b4b">{nm}</div>'
                f'<div style="font-size:.71rem;color:#9ca3af">&#9733; {rat:.1f} &middot; {dist}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Select", key=f"swc_{day_key}_{stop_idx}_{nm[:6]}", use_container_width=True):
                try:
                    new_it = swap_place_in_itinerary(
                        st.session_state.get("_itin",itinerary),day_key,stop_idx,alt.to_dict())
                    st.session_state["_itin"] = new_it
                except Exception:
                    new_it = dict(st.session_state.get("_itin",itinerary))
                    ds = list(new_it.get(day_key,[])); ds[stop_idx]=alt.to_dict()
                    new_it[day_key]=ds; st.session_state["_itin"]=new_it
                st.session_state.pop(f"_swap_{day_key}_{stop_idx}",None)
                st.toast(f"Replaced with {nm}"); st.rerun()
    if st.button("Cancel", key=f"swcancel_{day_key}_{stop_idx}"):
        st.session_state.pop(f"_swap_{day_key}_{stop_idx}",None); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AI MUST-SEE PANEL — shown per day inside itinerary
# ══════════════════════════════════════════════════════════════════
def render_daily_ai_picks(city, country, day_idx, district, sel_types, ndays, day_key):
    """Renders the AI must-see picks for one day with 'Add to Day' buttons."""
    picks = get_ai_daily_mustsee(city, country, day_idx, district, sel_types, LANG)
    if not picks: return

    current_itin = st.session_state.get("_itin", {})
    existing = {s.get("name","") for s in current_itin.get(day_key,[])
                if isinstance(current_itin.get(day_key,[]), list)}

    st.markdown(
        f'<div class="ai-panel">'
        f'<div style="font-weight:700;font-size:.82rem;color:#1e1b4b;margin-bottom:3px">'
        f'&#10022; {_t("ai_rec_heading")}</div>'
        f'<div style="font-size:.72rem;color:#a78bfa;margin-bottom:10px">'
        f'{"AI-powered" if DEEPSEEK_KEY else "Curated"} &nbsp;&middot;&nbsp; {_t("ai_rec_caption")}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(picks), 4))
    for i, rec in enumerate(picks):
        with cols[i % min(len(picks), 4)]:
            nm       = _safe_str(rec.get("name",""))
            nm_local = _safe_str(rec.get("name_local",""))
            tp       = _safe_str(rec.get("type",""))
            why      = _safe_str(rec.get("why",""))
            tip      = _safe_str(rec.get("tip",""))
            rat      = rec.get("rating", 4.5)
            already  = nm in existing

            display_name = f"{nm}<br><span style='color:#a78bfa;font-size:.70rem'>{nm_local}</span>" if nm_local else nm

            st.markdown(
                f'<div class="ai-item">'
                f'<div style="font-weight:600;font-size:.83rem;color:#1e1b4b">{display_name}</div>'
                f'<div style="color:#a78bfa;font-size:.71rem">{tp}</div>'
                f'<div style="color:#6b7280;font-size:.75rem;margin-top:3px">{why}</div>'
                f'{"<div style=color:#f59e0b;font-size:.71rem;margin-top:2px>Tip: "+tip+"</div>" if tip else ""}'
                f'<div style="color:#c4b5fd;font-size:.70rem;margin-top:3px">&#9733; {rat}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if already:
                st.markdown(
                    '<div class="pill pill-green" style="font-size:.69rem;margin-top:2px">&#10003; In itinerary</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(f"+ Add to {day_key}",
                             key=f"ai_add_{day_key}_{i}_{nm[:8]}",
                             use_container_width=True):
                    place = {
                        "name":       nm,
                        "lat":        rec.get("lat", 0),
                        "lon":        rec.get("lon", 0),
                        "type_label": tp,
                        "rating":     rat,
                        "address":    "",
                        "district":   district or "",
                        "description": why,
                    }
                    if _add_place_to_day(place, day_key):
                        st.toast(f"Added {nm} to {day_key}!")
                        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ITINERARY TABLE
# ══════════════════════════════════════════════════════════════════
def render_table(df, itinerary, day_budgets, country, city="",
                 day_districts=None, sel_types=None):
    if isinstance(day_budgets, int): day_budgets = [day_budgets]*30
    if day_districts is None: day_districts = [""] * 30
    if sel_types is None: sel_types = list(PTYPES.keys())

    stop_map = {}
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops):
                stop_map[s["name"]] = (di,si,dl,s)

    n2r = {row["name"]: row for _,row in df.iterrows()}
    scheduled = []
    if itinerary:
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops):
                if s["name"] in n2r: scheduled.append((di,si,dl,s["name"]))

    snames      = {x[3] for x in scheduled}
    unscheduled = [row for _,row in df.iterrows() if row["name"] not in snames]
    cur_day     = -1
    current_itin = st.session_state.get("_itin", itinerary)
    user = _cur_user()

    for di,si,dl,nm in scheduled:
        row   = n2r[nm]
        color = DAY_COLORS[di%len(DAY_COLORS)]
        d_usd = day_budgets[di] if di < len(day_budgets) else day_budgets[-1]

        # ── Day header + AI picks ──
        if di != cur_day:
            cur_day   = di
            day_key   = f"Day {di+1}"
            day_stops = list((current_itin or {}).get(day_key, []))
            lb, bc    = budget_level(d_usd)
            district  = day_districts[di] if di < len(day_districts) else ""

            st.markdown(
                f'<div class="day-header">'
                f'<div class="day-dot" style="background:{color}"></div>'
                f'<div class="day-title">{day_key}</div>'
                f'<div class="day-meta">{len(day_stops)} stops &nbsp;&middot;&nbsp; '
                f'${d_usd}/day &nbsp;&middot;&nbsp; {lb}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # AI must-see for this day
            render_daily_ai_picks(city, country, di, district, sel_types, len(itinerary), day_key)

        # ── Stop row ──
        sd       = stop_map.get(nm, (None,None,None,{}))[3]
        swap_key = f"_swap_Day {di+1}_{si}"

        with st.container():
            c_num, c_info, c_tr, c_act = st.columns([1, 5, 3, 2])

            with c_num:
                st.markdown(
                    f'<div style="text-align:center;padding-top:10px">'
                    f'<div class="stop-num" style="background:{color}">{si+1}</div>'
                    f'<div style="color:#c4b5fd;font-size:.66rem;margin-top:3px">'
                    f'{_safe_str(sd.get("time_slot","")) if sd else ""}</div></div>',
                    unsafe_allow_html=True,
                )

            with c_info:
                tl   = _safe_str(row.get("type_label","") or row.get("type",""))
                rat  = row.get("rating",0)
                dist = _safe_str(row.get("district",""))
                addr = _safe_str(row.get("address",""))
                ph   = _safe_str(row.get("phone",""))
                desc = _safe_str(row.get("description",""))
                _, cs = cost_estimate(tl, d_usd, country) if tl else (0,"")

                h = (f'<div style="padding:6px 0">'
                     f'<div class="stop-name">{_safe_str(nm)}</div>'
                     f'<div class="stop-meta">{tl}'
                     f'{"&nbsp;&middot;&nbsp;&#9733; "+str(rat) if rat else ""}'
                     f'{"&nbsp;&middot;&nbsp;"+dist if dist else ""}</div>')
                if desc: h += f'<div style="color:#c4b5fd;font-size:.71rem">{desc}</div>'
                if cs:   h += f'<div class="stop-cost">&#128176; {cs}</div>'
                if addr and "Sample" not in addr:
                    h += f'<div style="color:#c4b5fd;font-size:.70rem;margin-top:2px">&#128205; {addr[:60]}</div>'
                if ph:   h += f'<div style="color:#c4b5fd;font-size:.70rem">&#128222; {ph}</div>'
                h += '</div>'
                st.markdown(h, unsafe_allow_html=True)

            with c_tr:
                tr = sd.get("transport_to_next") if sd else None
                if tr:
                    dk  = tr.get("distance_km",0) or 0
                    _,tcost = transport_cost_estimate(dk, d_usd, country)
                    ti  = _safe_str(tr.get("transit_info",""))
                    st.markdown(
                        f'<div style="padding:8px 0">'
                        f'<div class="tr-chip">&#128663; {_safe_str(tr["mode"])}</div>'
                        f'<div style="color:#9ca3af;font-size:.71rem;margin-top:4px">'
                        f'&#9201; {_safe_str(tr["duration"])} &nbsp; &#128207; {dk} km</div>'
                        f'<div style="color:#a78bfa;font-size:.70rem">&#128176; {tr.get("cost_str",tcost)}</div>'
                        f'{"<div style=color:#c4b5fd;font-size:.69rem>"+ti+"</div>" if ti else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    et = sd.get("end_transport") if sd else None
                    if et:
                        st.markdown(
                            f'<div style="font-size:.77rem;color:#9ca3af;padding:8px 0">'
                            f'<div class="tr-chip">&#127937; {_safe_str(et["mode"])}</div>'
                            f'<div style="margin-top:4px">to {_safe_str(et.get("to_label","End"))}</div></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="font-size:.72rem;color:#c4b5fd;padding:8px 0">'
                            f'&#9711; {_t("last_stop")}</div>',
                            unsafe_allow_html=True,
                        )

            with c_act:
                # Wishlist button
                if user and WISHLIST_OK:
                    render_wishlist_button(dict(row), btn_key=f"wl_{di}_{si}_{nm[:6]}")
                # Swap button
                swap_open = st.session_state.get(swap_key, False)
                if st.button("↔" if not swap_open else "✕",
                             key=f"swbtn_{di}_{si}",
                             help="Swap" if not swap_open else "Cancel",
                             use_container_width=True):
                    st.session_state[swap_key] = not swap_open; st.rerun()

        if st.session_state.get(swap_key, False):
            render_inline_swap(current_itin, df, f"Day {di+1}", si)

        st.markdown(
            '<div style="height:1px;background:rgba(139,92,246,.08);margin:2px 0 5px"></div>',
            unsafe_allow_html=True,
        )

    # Meal panel
    if MEAL_OK and itinerary:
        avg_u = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or not stops: continue
            d_u = day_budgets[di] if di < len(day_budgets) else avg_u
            try:
                st.markdown(render_meal_panel(city,di,d_u,country,LANG,di*7+42),
                            unsafe_allow_html=True)
            except Exception: pass

    if unscheduled:
        _render_extra(unscheduled, day_budgets, country, itinerary)

# ══════════════════════════════════════════════════════════════════
# EXTRA RECOMMENDATIONS — with Add-to-Day buttons
# ══════════════════════════════════════════════════════════════════
def _render_extra(unscheduled, day_budgets, country, itinerary=None):
    avg = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    CATS = [
        ("Sights",    ["🏛️ Attraction"]),
        ("Dining",    ["🍜 Restaurant","☕ Cafe"]),
        ("Nature",    ["🌿 Park"]),
        ("Shopping",  ["🛍️ Shopping"]),
        ("Nightlife", ["🍺 Bar/Nightlife"]),
        ("Hotels",    ["🏨 Hotel"]),
    ]
    by_type = {}
    for r in unscheduled:
        tl = r.get("type_label","") or r.get("type","")
        by_type.setdefault(tl,[]).append(r)

    cat_data=[]; covered=set()
    for cn,tls in CATS:
        items=[]
        for tl in tls: items.extend(by_type.get(tl,[]))
        for tl in tls: covered.add(tl)
        if items: cat_data.append((cn,items))
    others = [r for tl,rs in by_type.items() if tl not in covered for r in rs]
    if others: cat_data.append(("Other",others))
    if not cat_data: return

    # Day keys for "Add to Day" dropdown
    day_keys = list(itinerary.keys()) if itinerary else []

    st.markdown(f'<div class="sec-label">{_t("rec_heading")}</div>', unsafe_allow_html=True)
    st.caption(_t("rec_caption"))

    user = _cur_user()

    import random as _r
    for cn, places in cat_data:
        sk = f"_rec_{cn}"
        if sk not in st.session_state: st.session_state[sk] = 0
        c1, c2 = st.columns([8,1])
        with c1:
            st.markdown(
                f'<div style="font-weight:600;font-size:.83rem;color:#1e1b4b;margin:12px 0 6px">'
                f'{cn} <span style="color:#c4b5fd;font-size:.72rem">({min(10,len(places))}/{len(places)})</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button(_t("rec_refresh"), key=f"rf_{cn}", use_container_width=True):
                st.session_state[sk] = (st.session_state[sk]+1) % 9999

        _r.seed(st.session_state[sk])
        picks = sorted(_r.sample(places, min(10,len(places))),
                       key=lambda r: r.get("rating",0), reverse=True)

        for row_start in range(0, len(picks), 4):
            chunk = picks[row_start:row_start+4]
            cols  = st.columns(len(chunk))
            for ci, p in enumerate(chunk):
                with cols[ci]:
                    nm   = _safe_str(p.get("name",""))
                    tl   = _safe_str(p.get("type_label","") or p.get("type",""))
                    rat  = p.get("rating",0)
                    dist = _safe_str(p.get("district","") or "")
                    addr = _safe_str(p.get("address","") or "")[:45]
                    ph   = _safe_str(p.get("phone","") or "")
                    _,cs = cost_estimate(tl, avg, country)

                    st.markdown(
                        f'<div class="rec-card">'
                        f'<div class="rc-name">{nm}</div>'
                        f'<div class="rc-meta">{tl}'
                        f'{"&nbsp;&middot;&nbsp;"+dist if dist else ""}</div>'
                        f'{"<div style=font-size:.70rem;color:#c4b5fd>"+addr+"</div>" if addr and "Sample" not in addr else ""}'
                        f'{"<div style=font-size:.70rem;color:#c4b5fd>"+ph+"</div>" if ph else ""}'
                        f'<div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center">'
                        f'<div style="font-size:.74rem;color:#1e1b4b">{"&#9733; "+str(rat) if rat else ""}</div>'
                        f'<div style="font-size:.71rem;color:#a78bfa;font-weight:500">&#128176; {cs}</div></div>'
                        f'<span class="rc-badge">{tl.split()[0] if tl else ""}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    # Wishlist button
                    if user and WISHLIST_OK:
                        render_wishlist_button(dict(p), btn_key=f"wl_ex_{cn}_{nm[:6]}_{ci}")

                    # Add to Day
                    if day_keys:
                        sel_day = st.selectbox(
                            "Add to",
                            ["-- pick day --"] + day_keys,
                            key=f"atd_sel_{cn}_{nm[:6]}_{ci}",
                            label_visibility="collapsed",
                        )
                        if sel_day != "-- pick day --":
                            if st.button("+ Add", key=f"atd_btn_{cn}_{nm[:6]}_{ci}",
                                         use_container_width=True):
                                place_d = {
                                    "name":       nm,
                                    "lat":        p.get("lat",0),
                                    "lon":        p.get("lon",0),
                                    "type_label": tl,
                                    "rating":     rat,
                                    "address":    addr,
                                    "district":   dist,
                                    "description": _safe_str(p.get("description","")),
                                }
                                if _add_place_to_day(place_d, sel_day):
                                    st.toast(f"Added {nm} to {sel_day}!")
                                    st.rerun()

# ══════════════════════════════════════════════════════════════════
# BUDGET SUMMARY
# ══════════════════════════════════════════════════════════════════
def render_budget_summary(itinerary, day_budgets, country, days):
    if not itinerary: return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*days
    sym, rate = _local_rate(country)
    tots=[]
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        du = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
        t  = sum(
            cost_estimate(s.get("type_label",""),du,country)[0]
            + transport_cost_estimate((s.get("transport_to_next") or {}).get("distance_km",0) or 0,du,country)[0]
            for s in stops
        )
        tots.append((dl,t,du))
    if not tots: return
    st.markdown(f'<div class="sec-label">{_t("budget_heading")}</div>', unsafe_allow_html=True)
    gt=sum(t for _,t,_ in tots); gb=sum(d for _,_,d in tots)
    nc=min(len(tots),4)+1; cols=st.columns(nc); any_over=False
    for i,(dl,t,du) in enumerate(tots):
        with cols[i%(nc-1)]:
            over = t>du*1.1
            if over: any_over=True
            lb, bc = budget_level(du)
            lo_u=round(t*.8); hi_u=round(t*1.2)
            rng=(f"${lo_u}-${hi_u}" if country=="US"
                 else f"${lo_u}-${hi_u} ({sym}{round(lo_u*rate)}-{sym}{round(hi_u*rate)})")
            st.markdown(
                f'<div class="bsum-card">'
                f'<div class="d-lbl">{_safe_str(dl)}</div>'
                f'<div class="d-amt">${round(t)}{"  !" if over else ""}</div>'
                f'<div class="d-rng">{rng}</div>'
                f'<div class="d-bud">{lb} &nbsp; ${du}/day</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with cols[-1]:
        lo=round(gt*.8); hi=round(gt*1.2)
        gs=(f"${lo}-${hi}" if country=="US"
            else f"${lo}-${hi} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})")
        st.markdown(
            f'<div class="bsum-card" style="border:1.5px solid rgba(139,92,246,.22);'
            f'background:rgba(139,92,246,.04)">'
            f'<div class="d-lbl">{_t("budget_total")}</div>'
            f'<div class="d-amt" style="font-size:1.65rem;color:#7c3aed">${round(gt)}</div>'
            f'<div class="d-rng">{gs}</div>'
            f'<div class="d-bud">{days}d &nbsp; ${gb} budget</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if any_over:
        st.markdown(f'<div class="banner-warn">&#9888; {_t("budget_over")}</div>',
                    unsafe_allow_html=True)
    with st.expander(_t("budget_breakdown")):
        rows=[]
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or not stops: continue
            du = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
            for s in stops:
                tl=s.get("type_label",""); _,cr=cost_estimate(tl,du,country)
                rows.append({"Day":_safe_str(dl),"Place":_safe_str(s.get("name","")),"Type":tl,
                              "Budget":f"${du}/day","Est.":cr})
                tr=s.get("transport_to_next") or {}
                if tr:
                    dk=tr.get("distance_km",0) or 0
                    _,tr2=transport_cost_estimate(dk,du,country)
                    rows.append({"Day":_safe_str(dl),"Place":f"-> {_safe_str(tr.get('mode',''))}",
                                 "Type":"Transport","Budget":f"${du}/day","Est.":tr2})
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════
# TRANSPORT COMPARISON
# ══════════════════════════════════════════════════════════════════
def render_transport_details(itinerary, country, city, day_budgets):
    if not TRANSPORT_OK or not itinerary: return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    with st.expander(_t("transport_cmp"), expanded=False):
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or len(stops)<2: continue
            du = day_budgets[di] if di<len(day_budgets) else 60
            st.markdown(f"**{_safe_str(dl)}**")
            for si in range(len(stops)-1):
                a,b=stops[si],stops[si+1]
                if not (a.get("lat") and b.get("lat")): continue
                try:
                    st.markdown(render_transport_comparison(
                        a["lat"],a["lon"],b["lat"],b["lon"],
                        _safe_str(a["name"]),_safe_str(b["name"]),
                        country=country,city=city,daily_usd=du,lang=LANG),
                        unsafe_allow_html=True)
                except Exception: pass

# ══════════════════════════════════════════════════════════════════
# SAVE WHOLE ITINERARY TO WISHLIST
# ══════════════════════════════════════════════════════════════════
def render_save_itinerary_button(itinerary, city):
    """Button to save entire itinerary to wishlist."""
    if not WISHLIST_OK: return
    user = _cur_user()
    if not user: return
    if st.button(f"♥ {_t('wishlist_save_itin')} — {city.title()}",
                 key="save_whole_itin", use_container_width=True):
        try:
            _save_itin(user["username"], itinerary, city, city.title())
            st.toast(f"Itinerary for {city.title()} saved to wishlist!")
            if POINTS_OK:
                try: add_points(user["username"],"save_itinerary",note=city)
                except Exception: pass
        except Exception as e:
            st.error(f"Could not save: {e}")

# ══════════════════════════════════════════════════════════════════
# COLLAB
# ══════════════════════════════════════════════════════════════════
def render_collab_panel():
    if not AUTH_OK: return
    user = _cur_user()
    if not user:
        with st.expander(_t("collab_heading"),expanded=False):
            st.caption(_t("auth_login_req"))
        return
    with st.expander(_t("collab_heading"),expanded=False):
        uname = user["username"]
        if st.button(_t("collab_share"),key="cb_gen"):
            import uuid as _uu
            try:
                tok=create_collab_link(uname,str(_uu.uuid4())[:8])
                st.session_state["_collab_tok"]=tok
            except Exception as e: st.error(str(e))
        if "_collab_tok" in st.session_state:
            st.success(f"Code: **{st.session_state['_collab_tok']}**")
        jc = st.text_input("Join code",key="cb_jc",placeholder="ABCDEFGH")
        if st.button("Join",key="cb_jb"):
            try:
                ok,msg=join_collab(uname,jc)
                (st.success if ok else st.error)(msg)
            except Exception as e: st.error(str(e))

# ══════════════════════════════════════════════════════════════════
# EXPORT — encoding-safe HTML
# ══════════════════════════════════════════════════════════════════
def build_html_report(itinerary, city, day_budgets, country):
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    avg = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60

    def esc(s):
        s = _safe_str(s)
        return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                 .replace('"',"&quot;").replace("'","&#39;"))

    DC = DAY_COLORS
    lb, _ = budget_level(avg)
    total_stops = sum(len(v) for v in itinerary.values() if isinstance(v,list))
    mjs=[]; pjs=[]; mlats=[]; mlons=[]

    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        c=DC[di%len(DC)]; pc=[]
        for si,s in enumerate(stops):
            lat=s.get("lat",0); lon=s.get("lon",0)
            if not lat or not lon: continue
            mlats.append(lat); mlons.append(lon); pc.append(f"[{lat},{lon}]")
            nm_js = esc(s.get("name","")).replace("'","&#39;")
            mjs.append(
                f'{{"lat":{lat},"lon":{lon},"n":"{nm_js}",'
                f'"d":{di+1},"s":{si+1},"c":"{c}"}}'
            )
        if len(pc)>1:
            pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')

    clat = sum(mlats)/len(mlats) if mlats else 35.
    clon = sum(mlons)/len(mlons) if mlons else 139.
    days_html = ""

    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        du  = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
        c   = DC[di%len(DC)]; rows_html=""
        for si,s in enumerate(stops):
            tr    = s.get("transport_to_next") or {}
            route = esc(f"{tr.get('mode','--')} {tr.get('duration','')}") if tr else "Last stop"
            rows_html += (
                f"<tr><td>{si+1}</td>"
                f"<td>{esc(s.get('time_slot','--'))}</td>"
                f"<td><b>{esc(s.get('name',''))}</b></td>"
                f"<td>{esc(s.get('type_label',''))}</td>"
                f"<td>{esc(s.get('district',''))}</td>"
                f"<td>{'&#9733; '+str(s.get('rating',0)) if s.get('rating') else '--'}</td>"
                f"<td>{route}</td></tr>"
            )
        days_html += (
            f"<h3 style='color:{c};letter-spacing:-.01em'>{esc(dl)} "
            f"&#8212; {len(stops)} stops &middot; ${du}/day</h3>"
            f"<table><thead><tr>"
            f"<th>#</th><th>Time</th><th>Place</th><th>Type</th>"
            f"<th>District</th><th>Rating</th><th>Getting There</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Itinerary - {esc(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:#f5f3ff;color:#1e1b4b;max-width:960px;margin:0 auto;padding:24px;
     -webkit-font-smoothing:antialiased}}
h1{{font-size:2rem;font-weight:700;letter-spacing:-.03em;margin:0 0 8px}}
h3{{font-size:1.05rem;font-weight:700;margin:24px 0 8px}}
.badge{{display:inline-flex;align-items:center;gap:6px;
       background:rgba(139,92,246,.10);border:1px solid rgba(139,92,246,.20);
       border-radius:20px;padding:4px 14px;font-size:.78rem;color:#7c3aed;
       font-weight:600;letter-spacing:.03em;margin-bottom:16px}}
.summary{{background:rgba(139,92,246,.06);border:1px solid rgba(139,92,246,.14);
         border-radius:12px;padding:12px 16px;font-size:.84rem;
         color:#6d28d9;margin-bottom:20px}}
#map{{height:420px;border-radius:18px;margin:20px 0;
      box-shadow:0 4px 24px rgba(109,40,217,.12)}}
table{{width:100%;border-collapse:collapse;font-size:.83rem;
       background:rgba(255,255,255,.8);border-radius:12px;overflow:hidden}}
thead tr{{background:rgba(139,92,246,.08)}}
th,td{{padding:8px 11px;border-bottom:1px solid rgba(139,92,246,.08);
       text-align:left}}
th{{font-weight:600;color:#7c3aed;font-size:.76rem;
    text-transform:uppercase;letter-spacing:.04em}}
tr:hover td{{background:rgba(139,92,246,.04)}}
footer{{color:#c4b5fd;font-size:.74rem;margin-top:36px;text-align:center}}
</style>
</head>
<body>
<div class="badge">&#10022; AI Travel Planner</div>
<h1>&#9992; {esc(city.title())}</h1>
<div class="summary">
  ${sum(day_budgets)} total budget &nbsp;&middot;&nbsp;
  {len(itinerary)} days &nbsp;&middot;&nbsp;
  {total_stops} stops &nbsp;&middot;&nbsp;
  avg ${avg}/day &nbsp;&middot;&nbsp;
  {lb}
</div>
<div id="map"></div>
{days_html}
<footer>Generated by AI Travel Planner &nbsp;&middot;&nbsp; Open in browser &rarr; Ctrl+P &rarr; Save as PDF</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var m=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
  {{attribution:'CartoDB'}}).addTo(m);
var markers=[{",".join(mjs)}];
markers.forEach(function(mk){{
  var ic=L.divIcon({{
    html:'<div style="width:23px;height:23px;border-radius:50%;background:'+mk.c+
         ';border:2.5px solid rgba(255,255,255,.9);display:flex;align-items:center;'+
         'justify-content:center;color:white;font-size:10px;font-weight:700;'+
         'box-shadow:0 2px 8px rgba(109,40,217,.25)">'+mk.s+'</div>',
    iconSize:[23,23],iconAnchor:[11,11]
  }});
  L.marker([mk.lat,mk.lon],{{icon:ic}})
   .bindPopup('<b>'+mk.n+'</b><br>Day '+mk.d+' Stop '+mk.s).addTo(m);
}});
var paths=[{",".join(pjs)}];
paths.forEach(function(pl){{
  L.polyline(pl.pts,{{color:pl.c,weight:3,opacity:.60,dashArray:'5 4'}}).addTo(m);
}});
</script>
</body>
</html>"""
    return html.encode("utf-8")

def build_calendar_urls(itinerary, start_date_str, city):
    import urllib.parse
    from datetime import datetime, timedelta
    try: bd = datetime.strptime(start_date_str,"%Y-%m-%d")
    except Exception: bd = None
    SM = {"9:00 AM":(9,0),"10:30 AM":(10,30),"12:00 PM":(12,0),"1:30 PM":(13,30),
          "3:00 PM":(15,0),"4:30 PM":(16,30),"6:00 PM":(18,0),"7:30 PM":(19,30)}
    out=[]
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list): continue
        for si,s in enumerate(stops):
            nm=_safe_str(s.get("name","Stop"))
            addr=_safe_str(s.get("address","") or city)
            hh,mm=SM.get(s.get("time_slot","9:00 AM"),(9,0)); ds=""
            if bd:
                dd=bd+timedelta(days=di); st2=dd.replace(hour=hh,minute=mm,second=0)
                et=st2+timedelta(hours=1,minutes=30)
                ds=f"{st2.strftime('%Y%m%dT%H%M%S')}/{et.strftime('%Y%m%dT%H%M%S')}"
            p={"action":"TEMPLATE","text":f"{nm} ({city.title()})",
               "location":addr[:100],"details":f"{city.title()} Day {di+1} Stop {si+1}"}
            if ds: p["dates"]=ds
            out.append({"day":_safe_str(dl),"stop":si+1,"name":nm,
                        "url":"https://calendar.google.com/calendar/render?"+
                              urllib.parse.urlencode(p)})
    return out

def render_export_panel(itinerary, city, day_budgets, country):
    if not itinerary or not any(isinstance(v,list) and v for v in itinerary.values()): return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    st.markdown(f'<div class="sec-label">{_t("export_heading")}</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="font-weight:600;font-size:.83rem;color:#1e1b4b;margin-bottom:8px">HTML Report</div>', unsafe_allow_html=True)
        try:
            data = build_html_report(itinerary, city, day_budgets, country)
            st.download_button(
                _t("export_dl_btn"), data=data,
                file_name=f"itinerary_{city.lower().replace(' ','_')}.html",
                mime="text/html;charset=utf-8", use_container_width=True,
            )
            st.caption(_t("export_caption"))
        except Exception as e: st.error(_t("err_export_fail",err=str(e)))
    with c2:
        st.markdown('<div style="font-weight:600;font-size:.83rem;color:#1e1b4b;margin-bottom:8px">Google Calendar</div>', unsafe_allow_html=True)
        sd  = st.date_input(_t("export_date"),key="exp_date",label_visibility="collapsed")
        ss  = sd.strftime("%Y-%m-%d") if sd else ""
        urls = build_calendar_urls(itinerary,ss,city)
        if urls:
            dseen={}
            for it in urls: dseen.setdefault(it["day"],[]).append(it)
            for dl,items in dseen.items():
                with st.expander(f"{_safe_str(dl)} ({len(items)} events)",expanded=False):
                    for it in items:
                        st.markdown(
                            f'<a href="{it["url"]}" target="_blank" '
                            f'style="text-decoration:none;color:#7c3aed;font-size:.81rem">'
                            f'+ Stop {it["stop"]}: {it["name"][:30]}</a>',
                            unsafe_allow_html=True,
                        )

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    lang_disp = st.selectbox(
        "Language",
        ["EN — English","ZH — Chinese"],
        index=0 if LANG=="EN" else 1,
        key="lang_sel",
    )
    LANG = "ZH" if lang_disp.startswith("ZH") else "EN"
    if I18N_OK:
        def _t(key, **kw): return _ti(key, LANG, **kw)

    if AUTH_OK:
        with st.expander("Account", expanded=False):
            render_auth_sidebar()

    st.markdown("---")
    st.markdown(f'<div class="sidebar-lbl">{_t("where_heading")}</div>', unsafe_allow_html=True)

    all_c       = sorted(WORLD_CITIES.keys())
    prev_c      = st.session_state.get("sel_country","")
    sel_country = st.selectbox(
        _t("pick_country"), [""]+all_c,
        index=([""] + all_c).index(prev_c) if prev_c in all_c else 0,
        key="sel_country",
    )
    sel_city = ""
    if sel_country:
        co = WORLD_CITIES.get(sel_country,[])
        pc = st.session_state.get("sel_city_name","")
        sel_city = st.selectbox(_t("pick_city"),co,
                                index=co.index(pc) if pc in co else 0,
                                key="sel_city_name")

    city_ov = st.text_input(_t("city_override"),"",
                             placeholder=_t("city_placeholder"),key="city_override")
    if city_ov.strip():   city_input = city_ov.strip()
    elif sel_city:        city_input = sel_city
    elif sel_country:     city_input = sel_country
    else:                 city_input = "Tokyo"

    city_key = city_input.strip().lower()
    is_cn    = city_key in CN_CITIES
    intl_d   = INTL_CITIES.get(city_key)
    if is_cn:    city_lat,city_lon = CN_CITIES[city_key]; country="CN"
    elif intl_d: city_lat,city_lon,country = intl_d[0],intl_d[1],intl_d[2]
    else:        city_lat=city_lon=None; country=COUNTRY_CODES.get(sel_country,"INT")

    st.markdown('<div class="sidebar-lbl">Logistics</div>', unsafe_allow_html=True)
    hotel_addr  = st.text_input(_t("hotel_label"), "",placeholder=_t("hotel_placeholder"))
    depart_addr = st.text_input(_t("depart_label"),"",placeholder=_t("depart_placeholder"))
    arrive_addr = st.text_input(_t("arrive_label"),"",placeholder=_t("arrive_placeholder"))

    st.markdown("---")
    st.markdown(f'<div class="sidebar-lbl">{_t("plan_heading")}</div>', unsafe_allow_html=True)
    days  = st.number_input(_t("how_many_days"),min_value=1,max_value=10,value=3,step=1)
    ndays = int(days)

    st.markdown(f'<div class="sidebar-lbl">{_t("what_todo")}</div>', unsafe_allow_html=True)
    sel_types = st.multiselect("place_types",list(PTYPES.keys()),
                               default=["🏛️ Attraction","🍜 Restaurant"],
                               label_visibility="collapsed")
    if not sel_types: sel_types=["🏛️ Attraction"]

    # Districts
    dk = f"dists_{city_key}"
    if dk not in st.session_state:
        if is_cn:
            with st.spinner(_t("loading_districts")+" "+city_input):
                st.session_state[dk]=_amap_get_districts(city_input)
        else:
            st.session_state[dk]=[]
    amap_dists=st.session_state.get(dk,[])
    adcode_map:dict={}; center_map:dict={}
    for d in amap_dists:
        n,a,la,lo=d.get("name",""),d.get("adcode",""),d.get("lat"),d.get("lon")
        if n and a: adcode_map[n]=a
        if n and la is not None: center_map[n]=(la,lo)

    if is_cn and amap_dists:
        pdo=["Auto (city-wide)"]+[d["name"] for d in amap_dists]
    elif intl_d and len(intl_d)>3:
        pdo=["Auto (city-wide)"]+intl_d[3]
    else:
        dnk=f"dyn_{city_key}"
        if dnk not in st.session_state and city_lat:
            with st.spinner(_t("loading_nbhds")):
                st.session_state[dnk]=_get_nominatim_districts(city_input)
        dyn=st.session_state.get(dnk,[])
        pdo=(["Auto (city-wide)"]+dyn) if dyn else ["Auto (city-wide)"]

    st.markdown(f'<div class="sidebar-lbl">{_t("day_prefs_heading")}</div>', unsafe_allow_html=True)
    st.caption(_t("day_prefs_caption"))
    day_quotas=[]; day_adcodes=[]; day_district_names=[]
    day_anchor_lats=[]; day_anchor_lons=[]; day_min_ratings=[]; day_budgets=[]

    if ndays <= 7:
        tabs = st.tabs([f"D{d+1}" for d in range(ndays)])
        for di,tab in enumerate(tabs):
            with tab:
                ds   = st.selectbox(_t("area_label"),pdo,key=f"da_{di}",label_visibility="collapsed")
                auto = (ds=="Auto (city-wide)")
                if auto:
                    day_adcodes.append(""); day_district_names.append("")
                    day_anchor_lats.append(city_lat); day_anchor_lons.append(city_lon)
                else:
                    day_adcodes.append(adcode_map.get(ds,""))
                    day_district_names.append(ds)
                    dlat,dlon=center_map.get(ds,(city_lat,city_lon))
                    day_anchor_lats.append(dlat); day_anchor_lons.append(dlon)
                mr=st.slider(_t("min_rating_label"),0.,5.,3.5,.5,key=f"mr_{di}")
                day_min_ratings.append(mr)
                du=st.slider(_t("daily_budget_label"),10,500,60,5,format="$%d",key=f"bud_{di}")
                cr=fmt_currency_row(du,country)
                lp=cr.split("~",1)[-1].strip() if "~" in cr else ""
                st.markdown(
                    f'<div class="pill pill-violet">${du}/day'
                    f'{("  ~  "+lp) if lp else ""}</div>',
                    unsafe_allow_html=True,
                )
                day_budgets.append(du)
                quota={}
                for tl in sel_types:
                    n=st.slider(tl,0,5,1,1,key=f"q_{di}_{tl}")
                    if n>0: quota[tl]=n
                if not quota: quota={sel_types[0]:1}
                day_quotas.append(quota)
    else:
        ds  =st.selectbox(_t("all_area_label"),pdo,key="da_all",label_visibility="collapsed")
        auto=(ds=="Auto (city-wide)")
        _adc="" if auto else adcode_map.get(ds,"")
        _dn ="" if auto else ds
        _alat,_alon=(center_map.get(ds,(city_lat,city_lon)) if not auto else (city_lat,city_lon))
        day_adcodes=[_adc]*ndays; day_district_names=[_dn]*ndays
        day_anchor_lats=[_alat]*ndays; day_anchor_lons=[_alon]*ndays
        mr=st.slider(_t("min_rating_label"),0.,5.,3.5,.5,key="mr_all")
        day_min_ratings=[mr]*ndays
        du=st.slider(_t("daily_budget_label"),10,500,60,5,format="$%d",key="bud_all")
        cr=fmt_currency_row(du,country); lp=cr.split("~",1)[-1].strip() if "~" in cr else ""
        st.markdown(
            f'<div class="pill pill-violet">${du}/day{("  ~  "+lp) if lp else ""}</div>',
            unsafe_allow_html=True,
        )
        day_budgets=[du]*ndays
        quota={}
        for tl in sel_types:
            n=st.slider(tl,0,5,1,1,key=f"qa_{tl}")
            if n>0: quota[tl]=n
        if not quota: quota={sel_types[0]:1}
        day_quotas=[dict(quota)]*ndays

    total_quota=sum(sum(q.values()) for q in day_quotas) if day_quotas else 4
    lpt=max(30,total_quota*6)
    daily_usd=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60

    st.markdown("---")
    if "seed" not in st.session_state: st.session_state.seed=42
    gen=st.button(_t("build_btn"),use_container_width=True,type="primary")
    ref=st.button(_t("refresh_btn"),use_container_width=True)
    if ref:
        st.session_state.seed=random.randint(1,99999)
        st.cache_data.clear(); gen=True

    _su = _cur_user()
    if _su and WISHLIST_OK:
        with st.expander(_t("wishlist_heading"),expanded=False):
            try: render_wishlist_panel(_su["username"],LANG)
            except Exception as _e: st.error(f"Wishlist error: {_e}")
    if _su and POINTS_OK:
        with st.expander(_t("points_heading"),expanded=False):
            try: render_points_panel(_su["username"],LANG)
            except Exception as _e: st.error(f"Points error: {_e}")

    st.markdown("---")
    if is_cn:
        if AMAP_KEY:
            st.markdown('<div class="banner-ok">&#10003; Amap API connected</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="banner-warn">Amap API key missing<br>'
                '<span style="font-size:.71rem">Add APIKEY in Streamlit Secrets</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="font-size:.70rem;color:#c4b5fd">Data: OpenStreetMap / Overpass</div>',
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════
st.markdown(
    f'<div class="hero-box">'
    f'<div class="hero-badge">&#10022; AI-Powered</div>'
    f'<div class="hero-title">{_t("hero_title")}</div>'
    f'<div class="hero-sub">{_t("hero_subtitle")}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# MAIN DISPLAY
# ══════════════════════════════════════════════════════════════════
def _run_display(it, df, ci, nd, bud, ctr, tys, lat, lon, hc, dc, ac,
                 d_districts=None):
    real  = sum(len(v) for v in it.values() if isinstance(v,list)) if it else 0
    avg_r = df["rating"].replace(0,float("nan")).mean()
    du    = round(sum(bud)/len(bud)) if bud else 60
    bstr  = f"${sum(bud)}" if len(set(bud))>1 else f"${du}/day"

    for c,(lbl,val) in zip(st.columns(5),[
        (_t("metric_places"),str(len(df))),
        (_t("metric_days"),  str(nd)),
        (_t("metric_stops"), str(real)),
        (_t("metric_rating"),f"{avg_r:.1f}" if not math.isnan(avg_r) else "--"),
        (_t("metric_budget"),bstr),
    ]):
        c.metric(lbl,val)

    # Save whole itinerary button
    col_sv, col_sp = st.columns([3,1])
    with col_sv:
        st.markdown(
            f'<div class="sec-label">&#128203; {_safe_str(ci).title()} &nbsp;&middot;&nbsp; '
            f'{" &middot; ".join(_safe_str(t) for t in tys)}</div>',
            unsafe_allow_html=True,
        )
    with col_sp:
        render_save_itinerary_button(it, ci)

    render_table(df, it, bud, ctr, ci,
                 day_districts=d_districts or ([""] * nd),
                 sel_types=tys)
    render_budget_summary(it, bud, ctr, nd)
    render_transport_details(it, ctr, ci, bud)

    st.markdown(f'<div class="map-head">{_t("map_heading")}</div>', unsafe_allow_html=True)
    st.caption(_t("map_caption"))
    try:
        m = build_map(df, lat, lon, it, hc, dc, ac)
        st_folium(m, width="100%", height=520, returned_objects=[])
    except Exception as e:
        st.error(_t("err_map_fail", err=str(e)))

    render_collab_panel()
    render_export_panel(it, ci, bud, ctr)

# ══════════════════════════════════════════════════════════════════
# GENERATE
# ══════════════════════════════════════════════════════════════════
if gen:
    if is_cn:
        lat, lon = city_lat, city_lon
        if lat is None:
            c = _amap_geocode(city_input)
            if c: lat,lon=c
            else: st.error(_t("err_city_nf",city=city_input)); st.stop()
    elif intl_d:
        lat, lon = intl_d[0], intl_d[1]
    else:
        with st.spinner(_t("finding_dest")):
            coord = _nominatim(city_input)
            if not coord: st.error(_t("err_city_nf",city=city_input)); st.stop()
            lat, lon = coord

    hotel_c=depart_c=arrive_c=None
    with st.spinner(_t("looking_up")):
        if hotel_addr:  hotel_c  = _geocode(hotel_addr, city_input, is_cn)
        if depart_addr: depart_c = _geocode(depart_addr,city_input, is_cn)
        if arrive_addr: arrive_c = _geocode(arrive_addr,city_input, is_cn)

    with st.spinner(f"{_t('finding_places')} {city_input.title()}..."):
        try:
            df, warn = fetch_all_places(
                lat, lon, country, is_cn,
                tuple(sel_types), lpt,
                tuple(day_adcodes), tuple(day_district_names),
                tuple(day_anchor_lats), tuple(day_anchor_lons),
                st.session_state.seed,
            )
        except Exception as e: st.error(f"Search error: {e}"); st.stop()

    if warn:
        st.markdown(f'<div class="banner-warn">{warn}</div>', unsafe_allow_html=True)
    if df is None or df.empty: st.error(_t("err_no_places")); st.stop()

    itinerary={}
    if not AI_OK:
        st.error(f"ai_planner import error: {_AI_ERR}")
    else:
        with st.spinner(_t("building_itin")):
            try:
                itinerary = generate_itinerary(
                    df, ndays, day_quotas,
                    hotel_lat  =hotel_c[0]   if hotel_c   else None,
                    hotel_lon  =hotel_c[1]   if hotel_c   else None,
                    depart_lat =depart_c[0]  if depart_c  else None,
                    depart_lon =depart_c[1]  if depart_c  else None,
                    arrive_lat =arrive_c[0]  if arrive_c  else None,
                    arrive_lon =arrive_c[1]  if arrive_c  else None,
                    day_min_ratings =day_min_ratings,
                    day_anchor_lats =day_anchor_lats,
                    day_anchor_lons =day_anchor_lons,
                    country=country, city=city_input,
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
        if user and WISHLIST_OK:
            try: _save_itin(user["username"],itinerary,city_input,city_input.title())
            except Exception: pass
        if user and POINTS_OK:
            try: add_points(user["username"],"share",note=city_input)
            except Exception: pass

    _run_display(itinerary, df, city_input, ndays, day_budgets, country,
                 sel_types, lat, lon, hotel_c, depart_c, arrive_c,
                 d_districts=day_district_names)

elif "_itin" in st.session_state and "_df" in st.session_state:
    _run_display(
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
        d_districts=st.session_state.get("_districts",[""] * ndays),
    )

else:
    # Welcome
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    cards_html = '<div class="welcome-grid">'
    for icon, title, desc in [
        ("✦","Personalised","Mix any place types"),
        ("◈","Budget Smart","Local currency costs"),
        ("⬡","By District","Clusters nearby stops"),
        ("◎","AI-Powered","Must-see picks every day"),
    ]:
        cards_html += (f'<div class="welcome-card">'
                       f'<div class="wc-icon">{icon}</div>'
                       f'<div class="wc-title">{title}</div>'
                       f'<div class="wc-desc">{desc}</div>'
                       f'</div>')
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;color:#c4b5fd;font-size:.82rem">'
        'Choose a destination in the sidebar, then tap <b>Build Itinerary</b></div>',
        unsafe_allow_html=True,
    )
