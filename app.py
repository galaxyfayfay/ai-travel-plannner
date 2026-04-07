"""
Voyager AI Travel Planner — Complete Rewrite v3
Apple-style, Gold/Glass, 6-step wizard, per-day editing,
map+list sync, AI assistant bubble, wishlist, collab
"""

import math, random, re, json, os, time
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Voyager", page_icon="✦", layout="wide",
                   initial_sidebar_state="collapsed")

# ── secrets ──────────────────────────────────────────────────────
def _get_secret(k):
    try:
        v = st.secrets.get(k, "")
        if v: return str(v)
    except: pass
    return os.getenv(k, "")

AMAP_KEY     = _get_secret("APIKEY")
DEEPSEEK_KEY = _get_secret("DEEPSEEKKEY")
ANTHROPIC_KEY= _get_secret("ANTHROPIC_API_KEY")

# ── optional modules ─────────────────────────────────────────────
try:
    from ai_planner import generate_itinerary; AI_OK=True
except Exception as _e: AI_OK=False; _AI_ERR=str(_e)
try:
    from transport_planner import build_day_schedule, estimate_travel; TRANSPORT_OK=True
except: TRANSPORT_OK=False
try:
    from auth_manager import register_user,login_user,get_user_from_session,logout_user,create_collab_link,join_collab; AUTH_OK=True
except: AUTH_OK=False
try:
    from wishlist_manager import (add_to_wishlist as _wl_add, remove_from_wishlist as _wl_remove,
        get_wishlist as _wl_get, is_in_wishlist as _wl_check,
        save_itinerary as _save_itin_ext, swap_place_in_itinerary); WISHLIST_EXT=True
except: WISHLIST_EXT=False
try:
    from points_system import add_points,get_points; POINTS_OK=True
except: POINTS_OK=False
try:
    import folium; from streamlit_folium import st_folium; FOLIUM_OK=True
except: FOLIUM_OK=False

# ══════════════════════════════════════════════════════════════════
# GLOBAL CSS — Apple + Gold Glass
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{
  font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Inter',sans-serif;
  -webkit-font-smoothing:antialiased;
}

/* App background */
.stApp{
  background:linear-gradient(160deg,#0a0a0f 0%,#111018 50%,#0d0c14 100%) !important;
  min-height:100vh;
}

/* Hide sidebar */
section[data-testid="stSidebar"]{display:none!important}
.main .block-container{padding:0!important;max-width:100%!important}

/* Subtle noise texture overlay */
.stApp::before{
  content:'';position:fixed;inset:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events:none;z-index:0;opacity:.4;
}

/* Gold accent variables */
:root{
  --gold:#c9a84c;
  --gold-light:#e8c97a;
  --gold-dim:rgba(201,168,76,0.15);
  --gold-border:rgba(201,168,76,0.25);
  --glass-bg:rgba(255,255,255,0.04);
  --glass-border:rgba(255,255,255,0.09);
  --glass-hover:rgba(255,255,255,0.07);
  --text-primary:#f0ece4;
  --text-secondary:rgba(240,236,228,0.55);
  --text-dim:rgba(240,236,228,0.30);
}

/* === PROGRESS BAR === */
.prog-wrap{
  display:flex;align-items:center;justify-content:center;
  gap:0;padding:28px 0 0;max-width:560px;margin:0 auto;
}
.prog-step{display:flex;flex-direction:column;align-items:center;flex:1}
.prog-dot{
  width:36px;height:36px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:600;transition:all 0.35s ease;
}
.prog-dot.done{
  background:linear-gradient(135deg,var(--gold),var(--gold-light));
  color:#000;box-shadow:0 0 16px rgba(201,168,76,0.4);
}
.prog-dot.active{
  background:transparent;
  border:2px solid var(--gold);
  color:var(--gold);
  box-shadow:0 0 20px rgba(201,168,76,0.3);
  transform:scale(1.1);
}
.prog-dot.pending{
  background:rgba(255,255,255,0.05);
  border:1.5px solid rgba(255,255,255,0.12);
  color:var(--text-dim);
}
.prog-lbl{
  font-size:10px;font-weight:500;letter-spacing:0.08em;
  text-transform:uppercase;margin-top:6px;
}
.prog-lbl.active{color:var(--gold)}
.prog-lbl.done{color:rgba(201,168,76,0.6)}
.prog-lbl.pending{color:var(--text-dim)}
.prog-line{flex:1;height:1px;background:rgba(255,255,255,0.08);position:relative;top:-18px}
.prog-line.done{background:linear-gradient(90deg,var(--gold),rgba(201,168,76,0.3));box-shadow:0 0 6px rgba(201,168,76,0.3)}

/* === GLASS CARD === */
.g{
  background:var(--glass-bg);
  backdrop-filter:blur(24px) saturate(160%);
  -webkit-backdrop-filter:blur(24px) saturate(160%);
  border:1px solid var(--glass-border);
  border-radius:20px;
  position:relative;overflow:hidden;
}
.g::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(201,168,76,0.2),transparent);
}

/* === WORDMARK === */
.wordmark{
  font-size:13px;font-weight:300;letter-spacing:0.35em;
  color:rgba(240,236,228,0.5);text-transform:uppercase;
  text-align:center;padding:24px 0 0;
}
.wordmark span{color:var(--gold);font-weight:500}

/* === STEP TITLE === */
.step-title{
  font-size:28px;font-weight:600;color:var(--text-primary);
  letter-spacing:-0.02em;line-height:1.15;margin-bottom:6px;
}
.step-sub{font-size:14px;color:var(--text-secondary);line-height:1.6;margin-bottom:24px}
.step-eyebrow{
  font-size:10px;font-weight:600;letter-spacing:0.12em;
  text-transform:uppercase;color:var(--gold);margin-bottom:8px;
}

/* === BUTTONS === */
.stButton>button{
  font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Inter',sans-serif!important;
  border-radius:12px!important;font-weight:500!important;font-size:14px!important;
  transition:all 0.2s!important;border:none!important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--gold),var(--gold-light))!important;
  color:#000!important;font-weight:600!important;
  box-shadow:0 4px 20px rgba(201,168,76,0.35)!important;
}
.stButton>button[kind="primary"]:hover{
  box-shadow:0 8px 28px rgba(201,168,76,0.5)!important;
  transform:translateY(-1px)!important;
}
.stButton>button:not([kind="primary"]){
  background:var(--glass-bg)!important;
  border:1px solid var(--glass-border)!important;
  color:var(--text-secondary)!important;
}
.stButton>button:not([kind="primary"]):hover{
  background:var(--glass-hover)!important;
  color:var(--text-primary)!important;
  border-color:var(--gold-border)!important;
}

/* === INPUTS === */
.stTextInput>div>div>input,.stNumberInput>div>div>input{
  background:rgba(255,255,255,0.05)!important;
  border:1px solid var(--glass-border)!important;
  border-radius:12px!important;color:var(--text-primary)!important;
  font-size:14px!important;padding:12px 16px!important;
  font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif!important;
}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{
  border-color:var(--gold-border)!important;
  box-shadow:0 0 0 3px rgba(201,168,76,0.1)!important;outline:none!important;
}
.stTextInput>div>div>input::placeholder{color:var(--text-dim)!important}
.stTextInput label,.stNumberInput label,.stSelectbox label,
.stMultiSelect label,.stSlider label,.stTextArea label{
  font-size:11px!important;font-weight:600!important;letter-spacing:0.08em!important;
  text-transform:uppercase!important;color:var(--text-secondary)!important;
}
.stSelectbox>div>div{
  background:rgba(255,255,255,0.05)!important;
  border:1px solid var(--glass-border)!important;
  border-radius:12px!important;color:var(--text-primary)!important;
  font-size:14px!important;
}
.stTextArea textarea{
  background:rgba(255,255,255,0.05)!important;
  border:1px solid var(--glass-border)!important;
  border-radius:12px!important;color:var(--text-primary)!important;
  font-size:14px!important;
}
.stSlider>div>div>div>div{background:var(--gold)!important}

/* === TABS === */
.stTabs [data-baseweb="tab-list"]{
  background:rgba(255,255,255,0.03)!important;
  border-radius:12px!important;border:1px solid var(--glass-border)!important;
  padding:3px!important;gap:2px!important;
}
.stTabs [data-baseweb="tab"]{
  border-radius:10px!important;color:var(--text-dim)!important;
  font-size:13px!important;font-weight:500!important;padding:6px 14px!important;
}
.stTabs [aria-selected="true"]{
  background:var(--gold-dim)!important;color:var(--gold)!important;
  border:1px solid var(--gold-border)!important;
}

/* === METRICS === */
div[data-testid="stMetric"]{
  background:var(--glass-bg)!important;border:1px solid var(--glass-border)!important;
  border-radius:16px!important;padding:16px 20px!important;
}
div[data-testid="stMetric"] label{
  color:var(--text-dim)!important;font-size:10px!important;font-weight:600!important;
  text-transform:uppercase!important;letter-spacing:0.1em!important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
  color:var(--text-primary)!important;font-size:22px!important;font-weight:700!important;
}

/* === EXPANDER === */
.stExpander{
  background:var(--glass-bg)!important;
  border:1px solid var(--glass-border)!important;border-radius:14px!important;
}
.stExpander>div>div>div>div>div>p{color:var(--text-secondary)!important;font-size:13px!important}

/* === MULTISELECT === */
.stMultiSelect>div>div{
  background:rgba(255,255,255,0.05)!important;
  border:1px solid var(--glass-border)!important;border-radius:12px!important;
}
.stMultiSelect span[data-baseweb="tag"]{
  background:var(--gold-dim)!important;border-color:var(--gold-border)!important;
  color:var(--gold)!important;
}

/* === DOWNLOAD === */
div[data-testid="stDownloadButton"] button{
  background:var(--gold-dim)!important;color:var(--gold)!important;
  border:1px solid var(--gold-border)!important;font-weight:500!important;
}

/* === ALERTS === */
.stAlert{border-radius:12px!important}
.stCaption{color:var(--text-dim)!important;font-size:12px!important}

/* === CITY PILL === */
.cpill{
  display:inline-flex;align-items:center;gap:6px;
  padding:7px 14px;border-radius:100px;
  background:var(--glass-bg);border:1px solid var(--glass-border);
  font-size:13px;color:var(--text-secondary);cursor:pointer;
  transition:all 0.2s;white-space:nowrap;margin:3px;
}
.cpill:hover{background:var(--gold-dim);border-color:var(--gold-border);color:var(--gold)}
.cpill.sel{background:var(--gold-dim);border-color:var(--gold);color:var(--gold);font-weight:500}

/* === PLACE TYPE CHIP === */
.type-chip{
  display:inline-flex;align-items:center;gap:5px;
  padding:6px 12px;border-radius:100px;
  font-size:12px;font-weight:500;cursor:pointer;
  transition:all 0.2s;margin:3px;
  background:var(--glass-bg);border:1px solid var(--glass-border);
  color:var(--text-secondary);
}
.type-chip.sel{border-color:var(--gold);color:var(--gold);background:var(--gold-dim)}

/* === DAY CARD === */
.day-card{
  background:var(--glass-bg);border:1px solid var(--glass-border);
  border-radius:18px;padding:20px 22px;margin:8px 0;
  cursor:pointer;transition:all 0.25s;position:relative;overflow:hidden;
}
.day-card:hover,.day-card.open{
  border-color:var(--gold-border);
  box-shadow:0 8px 32px rgba(0,0,0,0.3);
}
.day-card.open::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--gold),transparent);
}
.day-tag{
  display:inline-flex;align-items:center;
  padding:3px 10px;border-radius:100px;
  font-size:11px;font-weight:600;letter-spacing:0.05em;
}

/* === STOP ROW === */
.stop-row{
  display:flex;align-items:center;gap:12px;
  padding:10px 12px;border-radius:12px;margin:4px 0;
  background:rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.05);
  transition:background 0.15s;
  cursor:grab;
}
.stop-row:hover{background:rgba(255,255,255,0.06);border-color:var(--gold-border)}
.stop-num{
  width:26px;height:26px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:#000;
}
.stop-name{font-size:14px;font-weight:500;color:var(--text-primary);flex:1}
.stop-meta{font-size:12px;color:var(--text-dim);margin-top:2px}
.time-badge{
  display:inline-flex;align-items:center;
  background:var(--gold-dim);border:1px solid var(--gold-border);
  border-radius:100px;padding:2px 9px;font-size:11px;color:var(--gold);font-weight:500;
}
.tr-badge{
  display:inline-flex;align-items:center;
  background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.15);
  border-radius:100px;padding:2px 9px;font-size:11px;color:#7dd3fc;font-weight:500;
}

/* === WISHLIST BADGE === */
.wl-badge{
  display:inline-flex;align-items:center;gap:4px;
  background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.15);
  border-radius:100px;padding:2px 9px;font-size:11px;color:#fca5a5;font-weight:500;
}

/* === AI BUBBLE === */
.ai-bubble-wrap{
  position:fixed;bottom:28px;right:28px;z-index:9999;
}
.ai-bubble{
  width:54px;height:54px;border-radius:50%;
  background:linear-gradient(135deg,var(--gold),var(--gold-light));
  display:flex;align-items:center;justify-content:center;
  font-size:22px;cursor:pointer;
  box-shadow:0 4px 24px rgba(201,168,76,0.5),0 0 0 4px rgba(201,168,76,0.1);
  transition:all 0.25s;
}
.ai-bubble:hover{transform:scale(1.08);box-shadow:0 8px 32px rgba(201,168,76,0.6)}

/* === COLLAB BADGE === */
.collab-dot{
  width:8px;height:8px;border-radius:50%;background:#34d399;
  display:inline-block;margin-right:5px;
  box-shadow:0 0 8px rgba(52,211,153,0.6);
}

/* === SCROLLBAR === */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:rgba(255,255,255,0.02)}
::-webkit-scrollbar-thumb{background:rgba(201,168,76,0.2);border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:rgba(201,168,76,0.35)}

/* === MAP WRAP === */
.map-wrap{border-radius:16px;overflow:hidden;border:1px solid var(--glass-border)}

/* Hide streamlit branding */
#MainMenu,footer,header{visibility:hidden}
.stDeployButton{display:none}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS & DATA
# ══════════════════════════════════════════════════════════════════
CHAIN_BL=["kfc","mcdonald","starbucks","seven-eleven","family mart","711","lawson","costa coffee"]
def is_chain(n): return any(k in n.lower() for k in CHAIN_BL)

def _ss(s):
    if s is None: return ""
    s=str(s)
    for o,n in {"\u2014":"-","\u2013":"-","\u2019":"'","\u201c":'"',"\u201d":'"',"\u2026":"..."}.items():
        s=s.replace(o,n)
    return s

def _hkm(la1,lo1,la2,lo2):
    R=6371.0; dl=math.radians(la2-la1); dg=math.radians(lo2-lo1)
    a=math.sin(dl/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dg/2)**2
    return R*2*math.asin(min(1.0,math.sqrt(a)))

PTYPES={
    "🏛️ Attraction":{"osm":("tourism","attraction"),"amap":"110000","color":"#c9a84c"},
    "🍜 Restaurant": {"osm":("amenity","restaurant"),"amap":"050000","color":"#e8c97a"},
    "☕ Cafe":        {"osm":("amenity","cafe"),       "amap":"050500","color":"#d4a853"},
    "🌿 Park":        {"osm":("leisure","park"),       "amap":"110101","color":"#6ee7b7"},
    "🛍️ Shopping":   {"osm":("shop","mall"),          "amap":"060000","color":"#f9a8d4"},
    "🍺 Bar/Nightlife":{"osm":("amenity","bar"),      "amap":"050600","color":"#fbbf24"},
    "🏨 Hotel":       {"osm":("tourism","hotel"),      "amap":"100000","color":"#93c5fd"},
}
DAY_COLORS=["#c9a84c","#e8c97a","#6ee7b7","#f9a8d4","#fbbf24","#93c5fd","#d4a853","#a78bfa"]
AMAP_KW={
    "🏛️ Attraction":["旅游景点","博物馆"],"🍜 Restaurant":["餐馆","美食"],
    "☕ Cafe":["咖啡","下午茶"],"🌿 Park":["公园","花园"],
    "🛍️ Shopping":["商场","购物中心"],"🍺 Bar/Nightlife":["酒吧","夜店"],
    "🏨 Hotel":["酒店","宾馆"],
}
DURATION_MAP={"🏛️ Attraction":90,"🍜 Restaurant":60,"☕ Cafe":45,"🌿 Park":60,"🛍️ Shopping":90,"🍺 Bar/Nightlife":90,"🏨 Hotel":20}
DURATION_SPEC={"museum":120,"palace":120,"castle":120,"temple":60,"shrine":45,"cathedral":60,
               "market":75,"gallery":75,"park":60,"garden":75,"tower":45,"viewpoint":30,
               "crossing":20,"restaurant":60,"cafe":45,"mall":90,"beach":90,"aquarium":90,"zoo":120}

def est_dur(name,tl):
    nl=(name or "").lower()
    for k,v in DURATION_SPEC.items():
        if k in nl: return v
    return DURATION_MAP.get(tl,60)

def fmt_dur(m):
    if m<60: return f"{m}min"
    h=m//60; r=m%60
    return f"{h}h {r}min" if r else f"{h}h"

def _parse_dur(s):
    if not s: return 20
    s=s.lower().strip(); total=0
    h=re.search(r'(\d+)\s*h',s); m=re.search(r'(\d+)\s*m',s)
    if h: total+=int(h.group(1))*60
    if m: total+=int(m.group(1))
    return total if total>0 else 20

CURRENCIES={"CN":("¥",7.25),"JP":("¥",155),"KR":("₩",1350),"TH":("฿",36),"SG":("S$",1.35),
            "FR":("€",0.92),"GB":("£",0.79),"IT":("€",0.92),"ES":("€",0.92),"US":("$",1.0),
            "AU":("A$",1.53),"AE":("AED",3.67),"NL":("€",0.92),"TR":("₺",32),"HK":("HK$",7.82),
            "TW":("NT$",32),"INT":("$",1.0)}
def local_rate(cc): return CURRENCIES.get(cc,("$",1.0))

COST_W={"🏛️ Attraction":0.18,"🍜 Restaurant":0.25,"☕ Cafe":0.10,"🌿 Park":0.04,
        "🛍️ Shopping":0.22,"🍺 Bar/Nightlife":0.16,"🏨 Hotel":0.00}
COST_FL={"🏛️ Attraction":4,"🍜 Restaurant":6,"☕ Cafe":3,"🌿 Park":0,
         "🛍️ Shopping":8,"🍺 Bar/Nightlife":5,"🏨 Hotel":0}

def cost_est(tl,daily,cc):
    w=COST_W.get(tl,.12); fl=COST_FL.get(tl,2)
    pv=max(fl,daily*w/2); lo=pv*.65; hi=pv*1.45
    sym,rate=local_rate(cc)
    if cc=="US": return f"${round(lo)}-${round(hi)}"
    return f"${round(lo)}-${round(hi)} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})"

WORLD_CITIES={
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya","Hiroshima","Nara"],
    "South Korea":["Seoul","Busan","Jeju","Incheon"],
    "Thailand":["Bangkok","Chiang Mai","Phuket","Koh Samui"],
    "Vietnam":["Ho Chi Minh City","Hanoi","Da Nang","Hoi An"],
    "Indonesia":["Bali","Jakarta","Yogyakarta"],
    "Malaysia":["Kuala Lumpur","Penang","Malacca"],
    "Singapore":["Singapore"],
    "India":["Mumbai","Delhi","Bangalore","Jaipur","Goa"],
    "UAE":["Dubai","Abu Dhabi"],
    "Turkey":["Istanbul","Cappadocia","Antalya"],
    "France":["Paris","Lyon","Nice","Bordeaux"],
    "Italy":["Rome","Milan","Florence","Venice","Naples"],
    "Spain":["Barcelona","Madrid","Seville","Valencia"],
    "United Kingdom":["London","Edinburgh","Manchester","Bath"],
    "Germany":["Berlin","Munich","Hamburg","Frankfurt"],
    "Netherlands":["Amsterdam"],
    "Switzerland":["Zurich","Geneva","Lucerne","Zermatt"],
    "Austria":["Vienna","Salzburg"],
    "Greece":["Athens","Santorini","Mykonos","Crete"],
    "Portugal":["Lisbon","Porto","Algarve"],
    "Czech Republic":["Prague"],
    "Hungary":["Budapest"],
    "Croatia":["Dubrovnik","Split"],
    "Norway":["Oslo","Bergen"],
    "Iceland":["Reykjavik"],
    "USA":["New York","Los Angeles","Chicago","San Francisco","Miami","Las Vegas","Boston"],
    "Canada":["Toronto","Vancouver","Montreal","Banff"],
    "Mexico":["Mexico City","Cancun"],
    "Brazil":["Rio de Janeiro","Sao Paulo"],
    "Peru":["Lima","Cusco"],
    "Australia":["Sydney","Melbourne","Brisbane","Cairns"],
    "New Zealand":["Auckland","Queenstown"],
    "Morocco":["Marrakech","Fes"],
    "Egypt":["Cairo","Luxor"],
    "South Africa":["Cape Town","Johannesburg"],
    "China":["Beijing","Shanghai","Chengdu","Hangzhou","Xi'an"],
    "Hong Kong":["Hong Kong"],
    "Taiwan":["Taipei"],
}
COUNTRY_CODES={
    "China":"CN","Japan":"JP","South Korea":"KR","Thailand":"TH","Vietnam":"VN",
    "Indonesia":"ID","Malaysia":"MY","Singapore":"SG","India":"IN","UAE":"AE","Turkey":"TR",
    "France":"FR","Italy":"IT","Spain":"ES","United Kingdom":"GB","Germany":"DE",
    "Netherlands":"NL","Switzerland":"CH","Austria":"AT","Greece":"GR","Portugal":"PT",
    "Czech Republic":"CZ","Hungary":"HU","Croatia":"HR","Norway":"NO","Iceland":"IS",
    "USA":"US","Canada":"CA","Mexico":"MX","Brazil":"BR","Peru":"PE","Australia":"AU",
    "New Zealand":"NZ","Morocco":"MA","Egypt":"EG","South Africa":"ZA",
    "Hong Kong":"HK","Taiwan":"TW","Poland":"PL",
}
INTL_CITIES={
    "tokyo":(35.6762,139.6503,"JP"),"osaka":(34.6937,135.5023,"JP"),
    "kyoto":(35.0116,135.7681,"JP"),"nara":(34.6851,135.8050,"JP"),
    "sapporo":(43.0642,141.3469,"JP"),"fukuoka":(33.5904,130.4017,"JP"),
    "hiroshima":(34.3853,132.4553,"JP"),"nagoya":(35.1815,136.9066,"JP"),
    "seoul":(37.5665,126.9780,"KR"),"busan":(35.1796,129.0756,"KR"),
    "jeju":(33.4996,126.5312,"KR"),
    "bangkok":(13.7563,100.5018,"TH"),"chiang mai":(18.7883,98.9853,"TH"),
    "phuket":(7.8804,98.3923,"TH"),
    "singapore":(1.3521,103.8198,"SG"),
    "paris":(48.8566,2.3522,"FR"),"nice":(43.7102,7.2620,"FR"),
    "london":(51.5072,-0.1276,"GB"),"edinburgh":(55.9533,-3.1883,"GB"),
    "rome":(41.9028,12.4964,"IT"),"milan":(45.4654,9.1859,"IT"),
    "florence":(43.7696,11.2558,"IT"),"venice":(45.4408,12.3155,"IT"),
    "barcelona":(41.3851,2.1734,"ES"),"madrid":(40.4168,-3.7038,"ES"),
    "berlin":(52.5200,13.4050,"DE"),"munich":(48.1351,11.5820,"DE"),
    "amsterdam":(52.3676,4.9041,"NL"),
    "vienna":(48.2082,16.3738,"AT"),"salzburg":(47.8095,13.0550,"AT"),
    "santorini":(36.3932,25.4615,"GR"),"athens":(37.9838,23.7275,"GR"),
    "mykonos":(37.4467,25.3289,"GR"),"crete":(35.2401,24.8093,"GR"),
    "lisbon":(38.7223,-9.1393,"PT"),"porto":(41.1579,-8.6291,"PT"),
    "prague":(50.0755,14.4378,"CZ"),"budapest":(47.4979,19.0402,"HU"),
    "dubrovnik":(42.6507,18.0944,"HR"),
    "reykjavik":(64.1265,-21.8174,"IS"),
    "new york":(40.7128,-74.0060,"US"),"los angeles":(34.0522,-118.2437,"US"),
    "chicago":(41.8781,-87.6298,"US"),"san francisco":(37.7749,-122.4194,"US"),
    "miami":(25.7617,-80.1918,"US"),"las vegas":(36.1699,-115.1398,"US"),
    "toronto":(43.6532,-79.3832,"CA"),"vancouver":(49.2827,-123.1207,"CA"),
    "banff":(51.1784,-115.5708,"CA"),
    "sydney":(-33.8688,151.2093,"AU"),"melbourne":(-37.8136,144.9631,"AU"),
    "queenstown":(-45.0312,168.6626,"NZ"),
    "dubai":(25.2048,55.2708,"AE"),
    "istanbul":(41.0082,28.9784,"TR"),"cappadocia":(38.6431,34.8289,"TR"),
    "marrakech":(31.6295,-7.9811,"MA"),
    "cairo":(30.0444,31.2357,"EG"),
    "cape town":(-33.9249,18.4241,"ZA"),
    "hong kong":(22.3193,114.1694,"HK"),
    "taipei":(25.0330,121.5654,"TW"),
    "bali":(-8.3405,115.0920,"ID"),
    "ho chi minh city":(10.7769,106.7009,"VN"),"hanoi":(21.0285,105.8542,"VN"),
    "da nang":(16.0544,108.2022,"VN"),"hoi an":(15.8801,108.3380,"VN"),
    "kuala lumpur":(3.1390,101.6869,"MY"),
    "beijing":(39.9042,116.4074,"CN"),"shanghai":(31.2304,121.4737,"CN"),
    "chengdu":(30.5728,104.0668,"CN"),"hangzhou":(30.2741,120.1551,"CN"),
    "xi'an":(34.3416,108.9398,"CN"),
    "mumbai":(19.0760,72.8777,"IN"),"delhi":(28.6139,77.2090,"IN"),
    "jaipur":(26.9124,75.7873,"IN"),"goa":(15.2993,74.1240,"IN"),
    "cancun":(21.1619,-86.8515,"MX"),
    "rio de janeiro":(-22.9068,-43.1729,"BR"),
    "cusco":(-13.5320,-71.9675,"PE"),
    "zurich":(47.3769,8.5417,"CH"),"zermatt":(46.0207,7.7491,"CH"),
    "lucerne":(47.0502,8.3093,"CH"),
    "oslo":(59.9139,10.7522,"NO"),"bergen":(60.3913,5.3221,"NO"),
}
CN_CITIES={"beijing":(39.9042,116.4074),"shanghai":(31.2304,121.4737),
           "guangzhou":(23.1291,113.2644),"shenzhen":(22.5431,114.0579),
           "chengdu":(30.5728,104.0668),"hangzhou":(30.2741,120.1551),
           "xi'an":(34.3416,108.9398),"xian":(34.3416,108.9398),
           "chongqing":(29.5630,106.5516),"nanjing":(32.0603,118.7969)}

POPULAR=[
    ("🗼","Tokyo","Japan"),("🌆","Dubai","UAE"),("🗽","New York","USA"),
    ("🗺️","Paris","France"),("🏖️","Bali","Indonesia"),("🏰","Rome","Italy"),
    ("🌸","Kyoto","Japan"),("🎭","London","United Kingdom"),("🌃","Barcelona","Spain"),
    ("🌴","Bangkok","Thailand"),("🏔️","Santorini","Greece"),("🎋","Singapore","Singapore"),
    ("🦁","Cape Town","South Africa"),("🌊","Lisbon","Portugal"),
    ("🏯","Seoul","South Korea"),("🎠","Prague","Czech Republic"),
]

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
_DEFS={
    "step":1,"user_mode":None,"_auth_token":"",
    "dest_city":"","dest_country":"","dest_lat":None,"dest_lon":None,"dest_cc":"INT","dest_is_cn":False,
    "trip_days":3,"trip_types":["🏛️ Attraction","🍜 Restaurant"],"trip_budget":100,
    "trip_quotas":{},"day_configs":{},"custom_places":[],
    "_itin":None,"_df":None,"seed":42,
    "active_day":None,"ai_chat":[],"ai_open":False,
    "collab_code":"","collab_users":[],
    "popular_page":0,"popular_seed":0,
}
for k,v in _DEFS.items():
    if k not in st.session_state: st.session_state[k]=v

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    try:
        tok=st.session_state.get("_auth_token","")
        if not tok: return None
        return get_user_from_session(tok)
    except: return None

def _wl_add_fn(username,place):
    if WISHLIST_EXT:
        try: _wl_add(username,place); return
        except: pass
    k=f"_wl_{username}"; lst=st.session_state.get(k,[])
    if place.get("name","") not in {p.get("name","") for p in lst}:
        lst.append(place); st.session_state[k]=lst

def _wl_rm_fn(username,name):
    if WISHLIST_EXT:
        try: _wl_remove(username,name); return
        except: pass
    k=f"_wl_{username}"
    st.session_state[k]=[p for p in st.session_state.get(k,[]) if p.get("name","")!=name]

def _wl_get_fn(username):
    if WISHLIST_EXT:
        try: return _wl_get(username)
        except: pass
    return st.session_state.get(f"_wl_{username}",[])

def _wl_chk_fn(username,name):
    if WISHLIST_EXT:
        try: return _wl_check(username,name)
        except: pass
    return any(p.get("name","")==name for p in st.session_state.get(f"_wl_{username}",[]))

def _save_itin(username,itin,city,title):
    if WISHLIST_EXT:
        try: _save_itin_ext(username,itin,city,title); return
        except: pass
    k=f"_saved_{username}"; s=st.session_state.get(k,[])
    s.append({"city":city,"title":title,"data":itin,"at":datetime.now().strftime("%Y-%m-%d")})
    st.session_state[k]=s[-10:]

def build_timeline(stops,start_h=9):
    result=[]; cur=start_h*60
    for i,s in enumerate(stops):
        tl=s.get("type_label","🏛️ Attraction"); nm=s.get("name","")
        dur=est_dur(nm,tl)
        if i>0:
            tr=stops[i-1].get("transport_to_next") or {}
            cur+=_parse_dur(tr.get("duration",""))
        arr_h=cur//60; arr_m=cur%60
        dep=cur+dur; dep_h=dep//60; dep_m=dep%60
        e=dict(s)
        e["arrive_time"]=f"{arr_h:02d}:{arr_m:02d}"
        e["depart_time"]=f"{dep_h:02d}:{dep_m:02d}"
        e["duration_min"]=dur
        result.append(e); cur=dep+15
    return result

def geo_dedup(places,r=120.):
    if not places: return []
    merged=[False]*len(places); kept=[]
    for i,p in enumerate(places):
        if merged[i]: continue
        best=p
        for j in range(i+1,len(places)):
            if merged[j]: continue
            d=_hkm(best["lat"],best["lon"],places[j]["lat"],places[j]["lon"])*1000
            sl=places[j]["name"].strip().lower(); bl=best["name"].strip().lower()
            sim=(sl==bl) or (len(sl)>=3 and sl in bl) or (len(bl)>=3 and bl in sl)
            if d<50 or (d<r and sim):
                merged[j]=True
                if places[j]["rating"]>best["rating"]: best=places[j]
        kept.append(best)
    return kept

def tdesc(s):
    D={"attraction":"Worth a visit","restaurant":"Great for a meal","cafe":"Perfect coffee stop",
       "park":"Relax outdoors","mall":"Shopping stop","bar":"Evening out","hotel":"Place to stay"}
    for k,v in D.items():
        if k in str(s).lower(): return v
    return "Local favourite"

# ══════════════════════════════════════════════════════════════════
# GEOCODING
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600,show_spinner=False)
def _nom(q):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
                       params={"q":q,"format":"json","limit":1},
                       headers={"User-Agent":"VoyagerApp/3.0"},timeout=9).json()
        if r: return float(r[0]["lat"]),float(r[0]["lon"])
    except: pass
    return None

@st.cache_data(ttl=3600,show_spinner=False)
def _amap_geo(addr):
    if not AMAP_KEY: return None
    try:
        r=requests.get("https://restapi.amap.com/v3/geocode/geo",
                       params={"key":AMAP_KEY,"address":addr,"output":"json"},timeout=8).json()
        if str(r.get("status"))=="1" and r.get("geocodes"):
            loc=r["geocodes"][0].get("location","")
            if "," in loc:
                lon,lat=map(float,loc.split(",")); return lat,lon
    except: pass
    return None

# ══════════════════════════════════════════════════════════════════
# PLACE SEARCH
# ══════════════════════════════════════════════════════════════════
def search_intl(lat,lon,tls,lpt):
    all_p=[]
    for tl in tls:
        ok,ov=PTYPES[tl]["osm"]
        q=(f'[out:json][timeout:30];(node["{ok}"="{ov}"](around:6000,{lat},{lon});'
           f'way["{ok}"="{ov}"](around:6000,{lat},{lon}););out center {lpt*3};')
        els=[]
        for url in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
            try:
                r=requests.post(url,data={"data":q},timeout=28).json().get("elements",[])
                if r: els=r; break
            except: continue
        for el in els:
            tags=el.get("tags",{})
            nm=tags.get("name:en") or tags.get("name","")
            if not nm or is_chain(nm): continue
            elat=el.get("lat",0) if el["type"]=="node" else el.get("center",{}).get("lat",0)
            elon=el.get("lon",0) if el["type"]=="node" else el.get("center",{}).get("lon",0)
            if not elat or not elon: continue
            pts=[tags.get(k,"") for k in ["addr:housenumber","addr:street","addr:city"] if tags.get(k)]
            all_p.append({"name":_ss(nm),"lat":elat,"lon":elon,"rating":round(random.uniform(3.8,5.0),1),
                          "address":_ss(", ".join(pts)),"phone":"","website":"","type":ov,"type_label":tl,
                          "district":_ss(tags.get("addr:suburb","")),"description":tdesc(ov)})
            if len(all_p)>=lpt*len(tls): break
    seen,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],3),round(p["lon"],3))
        if k not in seen: seen.add(k); out.append(p)
    return out

def _parse_amap(pois,kw,tl,limit,seen):
    out=[]
    for p in pois:
        if len(out)>=limit: break
        nm=p.get("name","")
        if not nm or is_chain(nm): continue
        loc=p.get("location","")
        if "," not in (loc or ""): continue
        try: plon,plat=map(float,loc.split(","))
        except: continue
        k=(nm,round(plat,4),round(plon,4))
        if k in seen: continue
        seen.add(k)
        biz=p.get("biz_ext") or {}
        try: rating=float(biz.get("rating") or 0) or 0.0
        except: rating=0.0
        addr=p.get("address") or ""
        if isinstance(addr,list): addr="".join(addr)
        out.append({"name":_ss(nm),"lat":plat,"lon":plon,"rating":rating,
                    "address":_ss(str(addr).strip()),"phone":"","website":"",
                    "type":kw,"type_label":tl,"district":"","description":tdesc(kw)})
    return out

def search_cn(lat,lon,tls,lpt):
    all_p=[]; seen=set()
    for tl in tls:
        for kw in AMAP_KW.get(tl,[])[:2]:
            try:
                p={"key":AMAP_KEY,"keywords":kw,"location":f"{lon},{lat}","radius":8000,
                   "offset":20,"page":1,"extensions":"all","output":"json"}
                at=PTYPES.get(tl,{}).get("amap","")
                if at: p["types"]=at
                d=requests.get("https://restapi.amap.com/v3/place/around",params=p,timeout=10).json()
                if str(d.get("status"))=="1":
                    all_p.extend(_parse_amap(d.get("pois") or [],kw,tl,lpt,seen))
            except: pass
    seen2,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen2: seen2.add(k); out.append(p)
    return out

def demo_places(lat,lon,tls,n,seed):
    random.seed(seed)
    NAMES={"🏛️ Attraction":["Grand Museum","Sky Tower","Ancient Temple","Art Gallery","Historic Castle","Night Market","Cultural Centre","Heritage Site","Royal Palace","Old Town Square"],
           "🍜 Restaurant":["Sakura Dining","Ramen House","Sushi Master","Street Food Alley","Harbour Grill","Noodle King","Garden Restaurant","The Local Table"],
           "☕ Cafe":["Blue Bottle","Artisan Brew","Matcha Corner","Morning Pour","The Cozy Cup","Rooftop Café"],
           "🌿 Park":["Riverside Park","Sakura Garden","Central Park","Bamboo Grove","Waterfront Green"],
           "🛍️ Shopping":["Central Mall","Night Bazaar","Vintage Market","Designer District","Night Market"],
           "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Garden","Speakeasy"],
           "🏨 Hotel":["Grand Palace Hotel","Boutique Inn","City View Hotel"]}
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
                        "type":tl,"type_label":tl,"district":["North","Central","South"][ci],"description":tdesc(tl)})
    return out

@st.cache_data(ttl=180,show_spinner=False)
def fetch_places(clat,clon,cc,is_cn,tls_t,lpt,_seed):
    random.seed(_seed); tls=list(tls_t)
    raw=search_cn(clat,clon,tls,lpt) if is_cn else search_intl(clat,clon,tls,lpt)
    raw=geo_dedup(raw); warn=None
    if not raw:
        raw=demo_places(clat,clon,tls,lpt,_seed)
        warn="Live data unavailable — showing curated sample places."
    df=pd.DataFrame(raw)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c]=""
    df["rating"]=pd.to_numeric(df["rating"],errors="coerce").fillna(0.)
    for c in ["name","address","district","description","type_label","type"]: df[c]=df[c].apply(_ss)
    return df.sort_values("rating",ascending=False).reset_index(drop=True),warn

# ══════════════════════════════════════════════════════════════════
# AI MUST-SEE
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600,show_spinner=False)
def get_ai_mustsee(city,cc,days,types_t):
    types=list(types_t)
    if DEEPSEEK_KEY:
        try:
            prompt=(f"Recommend {min(days*3,12)} must-visit famous places in {city} for a {days}-day trip."
                    f" Types: {', '.join(types[:5])}. Only real well-known landmarks."
                    f" Return JSON array only. Each item: name, type, why(max 10 words), "
                    f"rating(4.0-5.0), lat(number), lon(number), duration_min(integer).")
            resp=requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":prompt}],
                      "temperature":0.3,"max_tokens":1400},timeout=20)
            if resp.status_code==200:
                content=resp.json()["choices"][0]["message"]["content"].strip()
                m=re.search(r'\[.*\]',content,re.DOTALL)
                if m:
                    items=json.loads(m.group())
                    if isinstance(items,list) and items:
                        cleaned=[{"name":_ss(it.get("name","")),"type":_ss(it.get("type","🏛️ Attraction")),
                                  "why":_ss(it.get("why","")),"rating":float(it.get("rating",4.5)),
                                  "lat":float(it.get("lat",0)),"lon":float(it.get("lon",0)),
                                  "duration_min":int(it.get("duration_min",60))}
                                 for it in items[:12] if isinstance(it,dict) and it.get("name")]
                        if cleaned: return cleaned
        except: pass
    BUILTIN={
        "tokyo":[{"name":"Senso-ji Temple","type":"🏛️ Attraction","why":"Tokyo oldest temple","rating":4.9,"lat":35.7148,"lon":139.7967,"duration_min":60},
                 {"name":"Shibuya Crossing","type":"🏛️ Attraction","why":"World busiest crossing","rating":4.8,"lat":35.6595,"lon":139.7004,"duration_min":20},
                 {"name":"Shinjuku Gyoen","type":"🌿 Park","why":"Imperial garden","rating":4.8,"lat":35.6851,"lon":139.7103,"duration_min":90}],
        "paris":[{"name":"Eiffel Tower","type":"🏛️ Attraction","why":"Icon of Paris","rating":4.8,"lat":48.8584,"lon":2.2945,"duration_min":90},
                 {"name":"Louvre Museum","type":"🏛️ Attraction","why":"World largest art museum","rating":4.8,"lat":48.8606,"lon":2.3376,"duration_min":180}],
        "london":[{"name":"British Museum","type":"🏛️ Attraction","why":"Free world class museum","rating":4.8,"lat":51.5194,"lon":-0.1270,"duration_min":120},
                  {"name":"Borough Market","type":"🍜 Restaurant","why":"Best London food market","rating":4.7,"lat":51.5055,"lon":-0.0910,"duration_min":60}],
        "dubai":[{"name":"Burj Khalifa","type":"🏛️ Attraction","why":"World tallest building","rating":4.8,"lat":25.1972,"lon":55.2744,"duration_min":90}],
        "bali":[{"name":"Tanah Lot Temple","type":"🏛️ Attraction","why":"Sunset cliff temple","rating":4.8,"lat":-8.6215,"lon":115.0865,"duration_min":90},
                {"name":"Tegallalang Rice Terraces","type":"🌿 Park","why":"Iconic green terraces","rating":4.7,"lat":-8.4319,"lon":115.2786,"duration_min":60}],
        "singapore":[{"name":"Gardens by the Bay","type":"🌿 Park","why":"Futuristic Supertree Grove","rating":4.9,"lat":1.2816,"lon":103.8636,"duration_min":120}],
    }
    cl=city.strip().lower()
    for k,v in BUILTIN.items():
        if k in cl: return v
    return []

# ══════════════════════════════════════════════════════════════════
# MAP BUILDER
# ══════════════════════════════════════════════════════════════════
def build_map(df,lat,lon,itinerary,active_day=None):
    if not FOLIUM_OK: return None
    m=folium.Map(location=[lat,lon],zoom_start=13,tiles="CartoDB dark_matter")
    vi={}
    if itinerary:
        for di,(dk,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops): vi[s.get("name","")]=(di,si+1,dk)
    # Routes
    if itinerary:
        for di,(dk,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list) or len(stops)<2: continue
            if active_day and dk!=active_day: continue
            dc=DAY_COLORS[di%len(DAY_COLORS)]
            for si in range(len(stops)-1):
                a,b=stops[si],stops[si+1]
                if not(a.get("lat") and b.get("lat")): continue
                folium.PolyLine([[a["lat"],a["lon"]],[b["lat"],b["lon"]]],
                                color=dc,weight=3,opacity=.7,dash_array="4 4").add_to(m)
    # Markers
    if df is not None and not df.empty:
        for _,row in df.iterrows():
            v=vi.get(row["name"])
            if active_day and v and v[2]!=active_day: continue
            if v:
                di,sn,dk2=v; color=DAY_COLORS[di%len(DAY_COLORS)]; label=str(sn)
            else:
                color="rgba(100,100,100,0.5)"; label="·"
            nm=_ss(row.get("name",""))
            dur=est_dur(nm,row.get("type_label",""))
            pop=(f"<div style='font-family:-apple-system,sans-serif;background:#1a1407;color:#f0ece4;"
                 f"padding:12px;border-radius:10px;min-width:150px;border:1px solid rgba(201,168,76,0.2)'>"
                 f"<b style='font-size:13px'>{nm}</b><br>"
                 f"<span style='color:#c9a84c;font-size:11px'>⭐ {row['rating']:.1f} · {fmt_dur(dur)}</span>"
                 f"</div>")
            folium.Marker([row["lat"],row["lon"]],
                popup=folium.Popup(pop,max_width=200),tooltip=nm,
                icon=folium.DivIcon(
                    html=(f'<div style="width:26px;height:26px;border-radius:50%;background:{color};'
                          f'border:2px solid rgba(255,255,255,0.85);display:flex;align-items:center;'
                          f'justify-content:center;color:#000;font-size:10px;font-weight:700;'
                          f'box-shadow:0 2px 8px rgba(0,0,0,0.5)">{label}</div>'),
                    icon_size=(26,26),icon_anchor=(13,13))).add_to(m)
    return m

# ══════════════════════════════════════════════════════════════════
# HTML EXPORT
# ══════════════════════════════════════════════════════════════════
def build_html(itin,city,day_budgets,cc):
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    avg=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    def esc(s):
        s=_ss(s); return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    total_stops=sum(len(v) for v in itin.values() if isinstance(v,list))
    mjs=[]; pjs=[]; mlats=[]; mlons=[]
    for di,(dl,stops) in enumerate(itin.items()):
        if not isinstance(stops,list) or not stops: continue
        c=DAY_COLORS[di%len(DAY_COLORS)]; pc=[]
        for si,s in enumerate(stops):
            la=s.get("lat",0); lo=s.get("lon",0)
            if not la or not lo: continue
            mlats.append(la); mlons.append(lo); pc.append(f"[{la},{lo}]")
            mjs.append(f'{{"lat":{la},"lon":{lo},"n":"{esc(s.get("name","")).replace(chr(34),chr(39))}","d":{di+1},"s":{si+1},"c":"{c}"}}')
        if len(pc)>1: pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')
    clat=sum(mlats)/len(mlats) if mlats else 35.
    clon=sum(mlons)/len(mlons) if mlons else 139.
    days_html=""
    for di,(dl,stops) in enumerate(itin.items()):
        if not isinstance(stops,list) or not stops: continue
        du=day_budgets[di] if di<len(day_budgets) else avg
        c=DAY_COLORS[di%len(DAY_COLORS)]
        tl_stops=build_timeline(stops)
        rows_html="".join(
            f"<tr><td>{si+1}</td><td>{esc(s.get('arrive_time',''))}–{esc(s.get('depart_time',''))}</td>"
            f"<td><b>{esc(s.get('name',''))}</b></td><td>{esc(s.get('type_label',''))}</td>"
            f"<td>{fmt_dur(s.get('duration_min',60))}</td>"
            f"<td>{'⭐'+str(s.get('rating',0)) if s.get('rating') else '–'}</td></tr>"
            for si,s in enumerate(tl_stops))
        total_dur=sum(s.get("duration_min",60) for s in tl_stops)
        days_html+=(f"<h3 style='color:{c};margin:24px 0 8px'>{esc(dl)} — {len(stops)} stops · ~{fmt_dur(total_dur)}</h3>"
                    f"<table><thead><tr><th>#</th><th>Time</th><th>Place</th><th>Type</th><th>Duration</th><th>Rating</th></tr></thead>"
                    f"<tbody>{rows_html}</tbody></table>")
    return (f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Voyager — {esc(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{{box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#0a0a0f;color:#f0ece4;max-width:960px;margin:0 auto;padding:32px 24px}}
h1{{font-size:28px;font-weight:300;color:#e8d9a0;margin:0 0 8px;letter-spacing:-0.02em}}
h3{{font-size:14px;font-weight:600;margin:20px 0 8px}}
.badge{{display:inline-flex;padding:3px 12px;border-radius:100px;background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.3);font-size:11px;color:#c9a84c;font-weight:600;margin-bottom:16px;letter-spacing:0.08em;text-transform:uppercase}}
.sum{{background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.15);border-radius:12px;padding:12px 16px;font-size:13px;color:#c9a84c;margin-bottom:20px}}
#map{{height:400px;border-radius:16px;margin:20px 0;border:1px solid rgba(201,168,76,.2)}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:rgba(255,255,255,.03);border-radius:12px;overflow:hidden;margin:4px 0}}
thead tr{{background:rgba(201,168,76,.08)}}th,td{{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.05);text-align:left}}
th{{font-weight:600;color:#c9a84c;font-size:10px;text-transform:uppercase;letter-spacing:.06em}}
tr:hover td{{background:rgba(201,168,76,.04)}}
footer{{color:rgba(201,168,76,.3);font-size:11px;margin-top:40px;text-align:center;padding-top:20px;border-top:1px solid rgba(255,255,255,.05)}}
</style></head><body>
<div class="badge">✦ Voyager AI Travel Planner</div>
<h1>✈ {esc(city.title())}</h1>
<div class="sum">${sum(day_budgets[:len(itin)])} total &nbsp;·&nbsp; {len(itin)} days &nbsp;·&nbsp; {total_stops} stops &nbsp;·&nbsp; avg ${avg}/day</div>
<div id="map"></div>{days_html}
<footer>Voyager AI Travel Planner &nbsp;·&nbsp; Ctrl+P to save as PDF</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
var m=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{attribution:'CartoDB'}}).addTo(m);
[{",".join(mjs)}].forEach(function(mk){{var ic=L.divIcon({{html:'<div style="width:24px;height:24px;border-radius:50%;background:'+mk.c+';border:2px solid rgba(255,255,255,.85);display:flex;align-items:center;justify-content:center;color:#000;font-size:10px;font-weight:700">'+mk.s+'</div>',iconSize:[24,24],iconAnchor:[12,12]}});L.marker([mk.lat,mk.lon],{{icon:ic}}).bindPopup('<b>'+mk.n+'</b>').addTo(m);}});
[{",".join(pjs)}].forEach(function(pl){{L.polyline(pl.pts,{{color:pl.c,weight:3,opacity:.7,dashArray:'4 4'}}).addTo(m);}});
</script></body></html>""").encode("utf-8")

# ══════════════════════════════════════════════════════════════════
# AI ASSISTANT (Claude API)
# ══════════════════════════════════════════════════════════════════
def call_ai_assistant(messages, city, itin_summary):
    system = (f"You are Voyager, a luxury travel planning AI assistant helping a user plan their trip to {city}. "
              f"Current itinerary summary: {itin_summary}. "
              f"Give concise, specific, expert advice. Max 120 words per response. Be warm and helpful.")
    if ANTHROPIC_KEY:
        try:
            payload={"model":"claude-sonnet-4-20250514","max_tokens":300,
                     "system":system,"messages":messages}
            resp=requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
                json=payload,timeout=20)
            if resp.status_code==200:
                content=resp.json().get("content",[])
                for block in content:
                    if block.get("type")=="text": return block["text"]
        except Exception as e: return f"Connection error: {e}"
    if DEEPSEEK_KEY:
        try:
            msgs=[{"role":"system","content":system}]+messages
            resp=requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":msgs,"temperature":0.7,"max_tokens":300},timeout=15)
            if resp.status_code==200:
                return resp.json()["choices"][0]["message"]["content"]
        except: pass
    # Fallback
    city_tips={"tokyo":"Tip: Get a Suica card for all transit. Visit Tsukiji market early morning for best sushi breakfast!",
               "paris":"Tip: Book Eiffel Tower tickets 2 months ahead. Museum Pass saves money on multiple visits.",
               "london":"Tip: Oyster card for transit. Many museums are free. Borough Market is perfect for lunch.",
               "bali":"Tip: Rent a scooter to get around. Visit temples early morning to avoid crowds.",
               "default":f"For {city}: I'd recommend starting mornings at the top attractions, then exploring local neighborhoods in the afternoon. Check Google Maps for real-time transit options."}
    cl=city.strip().lower()
    for k,v in city_tips.items():
        if k in cl: return v
    return city_tips["default"]

# ══════════════════════════════════════════════════════════════════
# PROGRESS BAR
# ══════════════════════════════════════════════════════════════════
def render_progress(cur):
    steps=[("✦","Welcome"),("◎","Destination"),("◈","Preferences"),("◉","Overview"),("⊛","Day Detail")]
    html='<div class="prog-wrap">'
    for i,(icon,label) in enumerate(steps):
        n=i+1
        state="done" if n<cur else ("active" if n==cur else "pending")
        circle=("✓" if n<cur else icon)
        html+=f'<div class="prog-step"><div class="prog-dot {state}">{circle}</div><div class="prog-lbl {state}">{label}</div></div>'
        if i<len(steps)-1:
            lc="done" if n<cur else ""
            html+=f'<div class="prog-line {lc}"></div>'
    html+='</div>'
    st.markdown(html,unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# STEP 1 — WELCOME / AUTH
# ══════════════════════════════════════════════════════════════════
def step_1():
    render_progress(1)
    st.markdown("<div style='height:32px'></div>",unsafe_allow_html=True)

    # Center column
    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown("""
        <div style='text-align:center;margin-bottom:32px'>
          <div style='font-size:42px;font-weight:700;color:#f0ece4;letter-spacing:-0.03em;line-height:1.1'>
            Plan your next<br><span style='color:#c9a84c'>great journey</span>
          </div>
          <div style='font-size:15px;color:rgba(240,236,228,0.5);margin-top:12px;line-height:1.6'>
            AI-curated itineraries for discerning travellers
          </div>
        </div>
        """,unsafe_allow_html=True)

        # Two cards
        c1,c2=st.columns(2,gap="small")
        with c1:
            st.markdown("""
            <div style='background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.2);
            border-radius:16px;padding:24px;text-align:center;min-height:200px'>
              <div style='font-size:28px;margin-bottom:10px'>◉</div>
              <div style='font-weight:600;font-size:15px;color:#f0ece4;margin-bottom:6px'>Sign In</div>
              <div style='font-size:12px;color:rgba(240,236,228,0.4);line-height:1.5'>
                Wishlist · Points<br>Saved trips · Collab
              </div>
            </div>
            """,unsafe_allow_html=True)
            if AUTH_OK:
                with st.form("lf"):
                    u=st.text_input("Username",placeholder="username",key="li_u",label_visibility="collapsed")
                    p=st.text_input("Password",type="password",placeholder="password",key="li_p",label_visibility="collapsed")
                    if st.form_submit_button("Sign In",use_container_width=True,type="primary"):
                        if u and p:
                            ok,msg,tok=login_user(u.strip(),p)
                            if ok:
                                st.session_state["_auth_token"]=tok
                                st.session_state["user_mode"]="logged_in"
                                if POINTS_OK:
                                    try: add_points(u.strip(),"daily_login")
                                    except: pass
                                st.session_state["step"]=2; st.rerun()
                            else: st.error(msg)
                        else: st.warning("Enter credentials")
                with st.expander("Create Account"):
                    with st.form("rf"):
                        ru=st.text_input("Username",placeholder="username",key="re_u",label_visibility="collapsed")
                        re=st.text_input("Email",placeholder="email@example.com",key="re_e",label_visibility="collapsed")
                        rp=st.text_input("Password",type="password",placeholder="min 6 chars",key="re_p",label_visibility="collapsed")
                        if st.form_submit_button("Create Account",use_container_width=True):
                            ok,msg=register_user(ru.strip(),rp,re.strip())
                            (st.success if ok else st.error)(msg)
            else:
                if st.button("Continue",use_container_width=True,type="primary",key="li_demo"):
                    st.session_state["user_mode"]="logged_in"; st.session_state["step"]=2; st.rerun()

        with c2:
            st.markdown("""
            <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
            border-radius:16px;padding:24px;text-align:center;min-height:200px'>
              <div style='font-size:28px;margin-bottom:10px'>◎</div>
              <div style='font-weight:600;font-size:15px;color:#f0ece4;margin-bottom:6px'>Guest</div>
              <div style='font-size:12px;color:rgba(240,236,228,0.4);line-height:1.5'>
                Full planning access<br>No account needed
              </div>
            </div>
            """,unsafe_allow_html=True)
            st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
            st.markdown("""
            <div style='font-size:12px;color:rgba(240,236,228,0.35);line-height:2'>
            ✦ AI itinerary generation<br>✦ Real-time places<br>✦ Interactive maps<br>✦ Cost estimates
            </div>""",unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
            if st.button("Explore as Guest →",use_container_width=True,key="guest_btn"):
                st.session_state["user_mode"]="guest"; st.session_state["step"]=2; st.rerun()

# ══════════════════════════════════════════════════════════════════
# STEP 2 — DESTINATION
# ══════════════════════════════════════════════════════════════════
def step_2():
    render_progress(2)
    st.markdown("<div style='height:24px'></div>",unsafe_allow_html=True)
    _,col,_=st.columns([1,3,1])
    with col:
        st.markdown('<div class="step-eyebrow">Step 1 of 3</div>',unsafe_allow_html=True)
        st.markdown('<div class="step-title">Where are you going?</div>',unsafe_allow_html=True)
        st.markdown('<div class="step-sub">Choose a destination or type any city in the world.</div>',unsafe_allow_html=True)

        # Search + country row
        c1,c2=st.columns([3,2],gap="small")
        with c1:
            city_ov=st.text_input("Search any city",placeholder="e.g. Kyoto, Santorini, Cusco…",
                                   value=st.session_state.get("dest_city","") if st.session_state.get("dest_city","") not in [c for cs in WORLD_CITIES.values() for c in cs] else "",
                                   key="s2_ov",label_visibility="visible")
        with c2:
            all_countries=[""] + sorted(WORLD_CITIES.keys())
            prev_cc=st.session_state.get("dest_country","")
            sel_cc=st.selectbox("Country",all_countries,
                                index=all_countries.index(prev_cc) if prev_cc in all_countries else 0,
                                key="s2_cc",label_visibility="visible")

        # Popular cities — paginated, 8 at a time
        st.markdown("<div style='margin:20px 0 8px;font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(201,168,76,0.7)'>Popular destinations</div>",unsafe_allow_html=True)

        # If country selected, show its cities; else show popular list paginated
        if sel_cc and not city_ov:
            cities=WORLD_CITIES.get(sel_cc,[])
            cur_city=st.session_state.get("dest_city","")
            rows=[cities[i:i+4] for i in range(0,len(cities),4)]
            for row in rows:
                cols=st.columns(len(row))
                for ci,city in enumerate(row):
                    with cols[ci]:
                        sel=(city==cur_city)
                        if st.button(("✓ " if sel else "")+city,key=f"cp_{city}",use_container_width=True,
                                     type="primary" if sel else "secondary"):
                            st.session_state["dest_city"]=city
                            st.session_state["dest_country"]=sel_cc
                            st.rerun()
        else:
            page=st.session_state.get("popular_page",0)
            page_size=8
            start=page*page_size; end=start+page_size
            chunk=POPULAR[start:end] if start<len(POPULAR) else POPULAR[:page_size]
            rows=[chunk[i:i+4] for i in range(0,len(chunk),4)]
            for row in rows:
                cols=st.columns(len(row))
                for ci,(icon,city,country) in enumerate(row):
                    with cols[ci]:
                        sel=(city==st.session_state.get("dest_city",""))
                        if st.button(f"{icon} {city}",key=f"pop_{city}_{page}",use_container_width=True,
                                     type="primary" if sel else "secondary"):
                            st.session_state["dest_city"]=city
                            st.session_state["dest_country"]=country
                            st.rerun()
            # Refresh button
            rc,_=st.columns([1,3])
            with rc:
                if st.button("↺ More cities",key="pop_more",use_container_width=True):
                    st.session_state["popular_page"]=(page+1)%(len(POPULAR)//page_size+1)
                    st.rerun()

        # Selected indicator
        final_city=(city_ov.strip() or st.session_state.get("dest_city",""))
        if final_city:
            st.markdown(f"""
            <div style='margin-top:16px;padding:12px 16px;background:rgba(201,168,76,0.08);
            border:1px solid rgba(201,168,76,0.25);border-radius:12px;
            display:flex;align-items:center;gap:10px'>
              <span style='font-size:18px'>✈️</span>
              <div>
                <div style='font-weight:600;color:#f0ece4;font-size:15px'>{final_city}</div>
                <div style='font-size:11px;color:rgba(201,168,76,0.6)'>{sel_cc or st.session_state.get("dest_country","")}</div>
              </div>
            </div>""",unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
        nc1,nc2=st.columns([1,1])
        with nc1:
            if st.button("← Back",key="s2_back",use_container_width=True):
                st.session_state["step"]=1; st.rerun()
        with nc2:
            if st.button("Next →",key="s2_next",use_container_width=True,type="primary"):
                fc=final_city
                if not fc: st.warning("Please select a destination."); return
                ck=fc.strip().lower()
                fcc_name=sel_cc or st.session_state.get("dest_country","")
                cc=COUNTRY_CODES.get(fcc_name,"INT")
                is_cn=ck in CN_CITIES
                intl=INTL_CITIES.get(ck)
                if is_cn: lat,lon=CN_CITIES[ck]
                elif intl: lat,lon,cc=intl[0],intl[1],intl[2]
                else:
                    with st.spinner("Locating…"):
                        coord=_nom(fc)
                        if not coord: st.error(f"Could not find '{fc}'."); return
                        lat,lon=coord
                st.session_state.update({"dest_city":fc,"dest_country":fcc_name,
                    "dest_lat":lat,"dest_lon":lon,"dest_cc":cc,"dest_is_cn":is_cn})
                st.session_state["step"]=3; st.rerun()

# ══════════════════════════════════════════════════════════════════
# STEP 3 — PREFERENCES (per-day)
# ══════════════════════════════════════════════════════════════════
def step_3():
    render_progress(3)
    st.markdown("<div style='height:24px'></div>",unsafe_allow_html=True)
    city=st.session_state.get("dest_city","your destination")
    cc=st.session_state.get("dest_cc","INT")

    _,col,_=st.columns([1,3,1])
    with col:
        st.markdown('<div class="step-eyebrow">Step 2 of 3</div>',unsafe_allow_html=True)
        st.markdown(f'<div class="step-title">Craft your {city} experience</div>',unsafe_allow_html=True)
        st.markdown('<div class="step-sub">Set your trip duration, interests, and per-day preferences.</div>',unsafe_allow_html=True)

        # ── Global settings ──
        ga,gb=st.columns(2,gap="medium")
        with ga:
            days=st.number_input("Trip duration (days)",min_value=1,max_value=10,
                                  value=st.session_state.get("trip_days",3),step=1,key="s3_days")
        with gb:
            base_budget=st.slider("Default daily budget ($)",10,500,
                                   st.session_state.get("trip_budget",100),5,format="$%d",key="s3_base_budget")
            sym,rate=local_rate(cc)
            st.markdown(f'<div style="font-size:11px;color:rgba(201,168,76,0.6);margin-top:4px">${base_budget} ≈ {sym}{round(base_budget*rate):,}/day</div>',unsafe_allow_html=True)

        # ── Interests ──
        st.markdown("<div style='margin:20px 0 8px;font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(201,168,76,0.7)'>Interests</div>",unsafe_allow_html=True)
        sel_types=list(st.session_state.get("trip_types",["🏛️ Attraction","🍜 Restaurant"]))
        rows_t=[list(PTYPES.keys())[i:i+4] for i in range(0,len(PTYPES),4)]
        for row in rows_t:
            tcols=st.columns(len(row))
            for tci,tl in enumerate(row):
                with tcols[tci]:
                    is_sel=tl in sel_types
                    if st.button(("✓ " if is_sel else "")+tl,key=f"tp_{tl}",use_container_width=True,
                                 type="primary" if is_sel else "secondary"):
                        if is_sel and len(sel_types)>1: sel_types.remove(tl)
                        elif not is_sel: sel_types.append(tl)
                        st.session_state["trip_types"]=sel_types; st.rerun()

        # ── Must-visit custom places ──
        st.markdown("<div style='margin:20px 0 8px;font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(201,168,76,0.7)'>Must-visit places (optional)</div>",unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px;color:rgba(240,236,228,0.4);margin-bottom:8px">Add specific places you don\'t want to miss — they\'ll be included in your itinerary.</div>',unsafe_allow_html=True)

        custom_places=list(st.session_state.get("custom_places",[]))
        # Show existing
        for ci,cp in enumerate(custom_places):
            cc1,cc2=st.columns([5,1])
            with cc1:
                st.markdown(f'<div style="padding:8px 12px;background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.15);border-radius:10px;font-size:13px;color:#e8d9a0">📍 {_ss(cp.get("name",""))}</div>',unsafe_allow_html=True)
            with cc2:
                if st.button("✕",key=f"rm_cp_{ci}",use_container_width=True):
                    custom_places.pop(ci); st.session_state["custom_places"]=custom_places; st.rerun()

        # Add new
        np1,np2=st.columns([4,1])
        with np1:
            new_place=st.text_input("Add a place",placeholder="e.g. Eiffel Tower, Jiro's Sushi, Central Park…",key="new_cp",label_visibility="collapsed")
        with np2:
            if st.button("+ Add",key="add_cp_btn",use_container_width=True):
                if new_place.strip():
                    custom_places.append({"name":new_place.strip(),"lat":0,"lon":0,"type_label":"🏛️ Attraction","rating":5.0,"address":"","district":"Custom","description":"User added"})
                    st.session_state["custom_places"]=custom_places
                    st.rerun()

        # ── Per-day configuration ──
        st.markdown("<div style='margin:24px 0 8px;font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(201,168,76,0.7)'>Per-day settings</div>",unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px;color:rgba(240,236,228,0.4);margin-bottom:12px">Customize each day — budget, number of stops per category.</div>',unsafe_allow_html=True)

        day_configs=dict(st.session_state.get("day_configs",{}))
        int_days=int(days)
        dtabs=st.tabs([f"Day {d+1}" for d in range(int_days)])
        for di,dtab in enumerate(dtabs):
            with dtab:
                dk=f"Day {di+1}"
                cfg=day_configs.get(dk,{"budget":int(base_budget),"quotas":{}})
                d_bud=st.slider(f"Budget Day {di+1}",10,500,int(cfg.get("budget",base_budget)),5,format="$%d",key=f"d_bud_{di}")
                st.markdown('<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(240,236,228,0.4);margin:12px 0 6px">Stops per type</div>',unsafe_allow_html=True)
                quotas={}
                q_cols=st.columns(min(len(sel_types),3))
                for tci,tl in enumerate(sel_types):
                    with q_cols[tci%len(q_cols)]:
                        prev_q=cfg.get("quotas",{}).get(tl,1)
                        n=st.number_input(tl,0,5,int(prev_q),1,key=f"q_{di}_{tl}")
                        if n>0: quotas[tl]=n
                if not quotas and sel_types: quotas={sel_types[0]:1}
                day_configs[dk]={"budget":d_bud,"quotas":quotas}

        # ── Optional logistics ──
        with st.expander("🚩 Optional: Start / End / Hotel",expanded=False):
            oa,ob=st.columns(2)
            with oa:
                depart=st.text_input("Start point",placeholder="e.g. Tokyo Station",key="s3_dep",label_visibility="visible")
                hotel=st.text_input("Hotel / Accommodation",placeholder="Hotel name or address",key="s3_hotel",label_visibility="visible")
            with ob:
                arrive=st.text_input("End point",placeholder="e.g. Narita Airport",key="s3_arr",label_visibility="visible")

        st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
        nc1,nc2=st.columns([1,1])
        with nc1:
            if st.button("← Back",key="s3_back",use_container_width=True):
                st.session_state["step"]=2; st.rerun()
        with nc2:
            if st.button("Build Itinerary ✦",key="s3_next",use_container_width=True,type="primary"):
                if not sel_types: st.warning("Select at least one interest."); return
                st.session_state["trip_days"]=int_days
                st.session_state["trip_budget"]=int(base_budget)
                st.session_state["trip_types"]=sel_types
                st.session_state["day_configs"]=day_configs
                st.session_state["trip_depart"]=st.session_state.get("s3_dep","")
                st.session_state["trip_arrive"]=st.session_state.get("s3_arr","")
                st.session_state["trip_hotel"]=st.session_state.get("s3_hotel","")
                _generate_itinerary()

# ══════════════════════════════════════════════════════════════════
# GENERATE ITINERARY
# ══════════════════════════════════════════════════════════════════
def _generate_itinerary():
    city=st.session_state["dest_city"]; lat=st.session_state["dest_lat"]
    lon=st.session_state["dest_lon"]; cc=st.session_state["dest_cc"]
    is_cn=st.session_state.get("dest_is_cn",False)
    ndays=st.session_state["trip_days"]
    day_configs=st.session_state.get("day_configs",{})
    custom_places=st.session_state.get("custom_places",[])

    # Build per-day quotas and budgets
    day_quotas=[]; day_budgets=[]
    for d in range(ndays):
        dk=f"Day {d+1}"; cfg=day_configs.get(dk,{})
        day_budgets.append(int(cfg.get("budget",st.session_state.get("trip_budget",100))))
        q=cfg.get("quotas",{})
        if not q: q={st.session_state.get("trip_types",["🏛️ Attraction"])[0]:1}
        day_quotas.append(q)

    total_q=sum(sum(q.values()) for q in day_quotas)
    lpt=max(20,total_q*5)
    sel_types=st.session_state.get("trip_types",["🏛️ Attraction"])

    with st.spinner(f"Discovering places in {city}…"):
        try:
            df,warn=fetch_places(lat,lon,cc,is_cn,tuple(sel_types),lpt,st.session_state.get("seed",42))
        except Exception as e:
            st.error(f"Search error: {e}"); return

    if warn: st.info(warn)
    if df is None or df.empty: st.error("No places found."); return

    # Inject custom places into df
    if custom_places:
        cp_rows=[]
        for cp in custom_places:
            # Try geocode if no coords
            if not cp.get("lat"):
                with st.spinner(f"Locating {cp['name']}…"):
                    coord=_nom(f"{cp['name']} {city}") or _nom(cp["name"])
                    if coord: cp["lat"],cp["lon"]=coord[0],coord[1]
                    else: cp["lat"]=lat+random.uniform(-.01,.01); cp["lon"]=lon+random.uniform(-.01,.01)
            cp_rows.append(cp)
        cp_df=pd.DataFrame(cp_rows)
        for c in df.columns:
            if c not in cp_df.columns: cp_df[c]=""
        cp_df["rating"]=5.0; df=pd.concat([cp_df,df],ignore_index=True)

    # Geocode optional points
    def _gc(addr):
        if not addr: return None
        if is_cn: return _amap_geo(f"{addr} {city}") or _nom(f"{addr} {city}")
        return _nom(f"{addr} {city}") or _nom(addr)

    hotel_c=depart_c=arrive_c=None
    with st.spinner("Looking up locations…"):
        hotel_c=_gc(st.session_state.get("trip_hotel",""))
        depart_c=_gc(st.session_state.get("trip_depart",""))
        arrive_c=_gc(st.session_state.get("trip_arrive",""))

    itin={}
    if AI_OK:
        with st.spinner("Crafting your itinerary…"):
            try:
                itin=generate_itinerary(df,ndays,day_quotas,
                    hotel_lat=hotel_c[0] if hotel_c else None,hotel_lon=hotel_c[1] if hotel_c else None,
                    depart_lat=depart_c[0] if depart_c else None,depart_lon=depart_c[1] if depart_c else None,
                    arrive_lat=arrive_c[0] if arrive_c else None,arrive_lon=arrive_c[1] if arrive_c else None,
                    day_min_ratings=[3.5]*ndays,day_anchor_lats=[lat]*ndays,day_anchor_lons=[lon]*ndays,
                    country=cc,city=city,day_budgets=day_budgets)
            except Exception as e:
                st.error(f"Itinerary error: {e}")
    if not itin:
        used=set()
        for d in range(ndays):
            dk=f"Day {d+1}"; stops=[]; q=day_quotas[d]
            for tl,cnt in q.items():
                pool=df[(df["type_label"]==tl)&(~df["name"].isin(used))].head(cnt)
                for _,row in pool.iterrows(): stops.append(row.to_dict()); used.add(row["name"])
            itin[dk]=stops

    # Ensure custom places are in itin (inject into day 1 if missing)
    if custom_places:
        in_itin={s.get("name","") for sl in itin.values() if isinstance(sl,list) for s in sl}
        missing=[cp for cp in custom_places if cp["name"] not in in_itin]
        for cp in missing:
            d1=list(itin.keys())[0] if itin else "Day 1"
            if d1 not in itin: itin[d1]=[]
            itin[d1].insert(0,{**cp,"time_slot":"TBD","transport_to_next":None})

    st.session_state["_itin"]=itin; st.session_state["_df"]=df
    st.session_state["day_budgets"]=day_budgets
    st.session_state["active_day"]=None; st.session_state["ai_chat"]=[]

    user=_cur_user()
    if user:
        _save_itin(user["username"],itin,city,city.title())
        if POINTS_OK:
            try: add_points(user["username"],"share",note=city)
            except: pass
    st.session_state["step"]=4; st.rerun()

# ══════════════════════════════════════════════════════════════════
# STEP 4 — OVERVIEW
# ══════════════════════════════════════════════════════════════════
def step_4():
    render_progress(4)
    st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)

    city=st.session_state.get("dest_city","")
    cc=st.session_state.get("dest_cc","INT")
    lat=st.session_state.get("dest_lat",35.)
    lon=st.session_state.get("dest_lon",139.)
    ndays=st.session_state.get("trip_days",3)
    day_budgets=st.session_state.get("day_budgets",[100]*ndays)
    itin=st.session_state.get("_itin",{})
    df=st.session_state.get("_df",pd.DataFrame())
    user=_cur_user()

    total_stops=sum(len(v) for v in itin.values() if isinstance(v,list))
    avg_r=df["rating"].replace(0,float("nan")).mean() if df is not None and not df.empty else 0

    # ── Header ──
    _,hcol,_=st.columns([1,4,1])
    with hcol:
        st.markdown(f"""
        <div style='margin-bottom:20px'>
          <div style='font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:rgba(201,168,76,0.7);margin-bottom:6px'>Your Itinerary</div>
          <div style='font-size:32px;font-weight:600;color:#f0ece4;letter-spacing:-0.02em'>{city.title()}</div>
          <div style='font-size:14px;color:rgba(240,236,228,0.45);margin-top:4px'>{ndays} days · {total_stops} stops · avg ${round(sum(day_budgets)/len(day_budgets)) if day_budgets else 0}/day</div>
        </div>
        """,unsafe_allow_html=True)

    # ── Metrics ──
    _,mc,_=st.columns([1,4,1])
    with mc:
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Days",str(ndays))
        m2.metric("Stops",str(total_stops))
        m3.metric("Avg Rating",f"{avg_r:.1f}" if avg_r else "—")
        m4.metric("Est. Total",f"${sum(day_budgets)}")

    # ── Action row ──
    _,ac,_=st.columns([1,4,1])
    with ac:
        a1,a2,a3,a4=st.columns(4)
        with a1:
            if st.button("← Edit",key="s4_back",use_container_width=True):
                st.session_state["step"]=3; st.rerun()
        with a2:
            if st.button("🔀 Shuffle",key="s4_shuf",use_container_width=True):
                st.session_state["seed"]=random.randint(1,99999)
                st.cache_data.clear(); _generate_itinerary()
        with a3:
            if user and st.button("♥ Save",key="s4_save",use_container_width=True):
                _save_itin(user["username"],itin,city,city.title())
                st.toast(f"Saved {city.title()}!")
        with a4:
            if itin:
                try:
                    hd=build_html(itin,city,day_budgets,cc)
                    st.download_button("⬇ Export",data=hd,
                        file_name=f"voyager_{city.lower().replace(' ','_')}.html",
                        mime="text/html;charset=utf-8",use_container_width=True)
                except: pass

    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)

    # ── Overview Map + Day Cards ──
    _,mc2,_=st.columns([1,4,1])
    with mc2:
        # Mini overview map
        if FOLIUM_OK and df is not None and not df.empty:
            m=build_map(df,lat,lon,itin,active_day=None)
            if m:
                st.markdown('<div class="map-wrap">',unsafe_allow_html=True)
                st_folium(m,width="100%",height=280,returned_objects=[])
                st.markdown("</div>",unsafe_allow_html=True)

        st.markdown("<div style='font-size:11px;color:rgba(201,168,76,0.6);margin:16px 0 8px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase'>Tap a day to plan in detail</div>",unsafe_allow_html=True)

        # Day overview cards
        for di,(dk,stops) in enumerate(itin.items()):
            if not isinstance(stops,list): continue
            color=DAY_COLORS[di%len(DAY_COLORS)]
            d_bud=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
            tl_stops=build_timeline(stops)
            total_dur=sum(s.get("duration_min",60) for s in tl_stops)

            # Summary of stop types
            type_counts={}
            for s in stops:
                t=s.get("type_label",""); type_counts[t]=type_counts.get(t,0)+1
            type_summary=" · ".join(f"{v}× {k.split()[0]}" for k,v in list(type_counts.items())[:3])

            # Preview of first 3 stop names
            preview=" → ".join(_ss(s.get("name",""))[:18] for s in stops[:3])
            if len(stops)>3: preview+=f" +{len(stops)-3} more"

            col_card,col_btn=st.columns([5,1])
            with col_card:
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                border-left:3px solid {color};border-radius:14px;padding:16px 18px;margin:6px 0;
                position:relative;overflow:hidden'>
                  <div style='position:absolute;top:0;left:0;right:0;height:1px;
                  background:linear-gradient(90deg,{color}40,transparent)'></div>
                  <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>
                    <div style='width:30px;height:30px;border-radius:50%;background:{color}22;
                    border:1.5px solid {color}66;display:flex;align-items:center;justify-content:center;
                    font-size:12px;font-weight:700;color:{color};flex-shrink:0'>{di+1}</div>
                    <div style='flex:1'>
                      <span style='font-weight:600;font-size:15px;color:#f0ece4'>{dk}</span>
                      <span style='font-size:12px;color:rgba(240,236,228,0.4);margin-left:10px'>{len(stops)} stops · ${d_bud}/day · ~{fmt_dur(total_dur)}</span>
                    </div>
                  </div>
                  <div style='font-size:12px;color:rgba(201,168,76,0.7);margin-bottom:4px'>{type_summary}</div>
                  <div style='font-size:12px;color:rgba(240,236,228,0.35);line-height:1.5'>{preview}</div>
                </div>
                """,unsafe_allow_html=True)
            with col_btn:
                st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
                if st.button("Plan →",key=f"open_day_{dk}",use_container_width=True,type="primary"):
                    st.session_state["active_day"]=dk
                    st.session_state["step"]=5; st.rerun()

        # ── Wishlist Panel ──
        if user:
            wl=_wl_get_fn(user["username"])
            if wl:
                st.markdown("<div style='margin-top:24px'></div>",unsafe_allow_html=True)
                with st.expander(f"♥ My Wishlist ({len(wl)} places)",expanded=False):
                    for wi,wp in enumerate(wl):
                        wc1,wc2,wc3=st.columns([4,2,1])
                        with wc1:
                            st.markdown(f'<div style="font-size:13px;color:#f0ece4;font-weight:500">{_ss(wp.get("name",""))}</div><div style="font-size:11px;color:rgba(240,236,228,0.4)">{_ss(wp.get("type_label",""))}</div>',unsafe_allow_html=True)
                        with wc2:
                            # Add to day selector
                            day_keys=list(itin.keys())
                            sel_wl_day=st.selectbox("",["add to…"]+day_keys,key=f"wl_add_day_{wi}",label_visibility="collapsed")
                        with wc3:
                            if sel_wl_day!="add to…":
                                if st.button("+",key=f"wl_add_btn_{wi}",use_container_width=True):
                                    stops_list=list(itin.get(sel_wl_day,[]))
                                    nm=wp.get("name","")
                                    if nm not in {s.get("name","") for s in stops_list}:
                                        stops_list.append({**wp,"time_slot":"TBD","transport_to_next":None})
                                        new_itin=dict(itin); new_itin[sel_wl_day]=stops_list
                                        st.session_state["_itin"]=new_itin
                                        st.toast(f"Added {nm}!"); st.rerun()
                            elif st.button("✕",key=f"wl_rm_{wi}",use_container_width=True):
                                _wl_rm_fn(user["username"],wp.get("name","")); st.rerun()

        # ── Collab Panel ──
        if AUTH_OK and user:
            st.markdown("<div style='margin-top:16px'></div>",unsafe_allow_html=True)
            with st.expander("🤝 Collaborate (shared editing)",expanded=False):
                st.markdown('<div style="font-size:12px;color:rgba(240,236,228,0.4);margin-bottom:10px">Share a code so friends can view and edit this itinerary together.</div>',unsafe_allow_html=True)
                cb1,cb2=st.columns(2)
                with cb1:
                    if st.button("Generate share code",use_container_width=True):
                        import uuid
                        try:
                            tok=create_collab_link(user["username"],str(uuid.uuid4())[:8])
                            st.session_state["collab_code"]=tok
                        except Exception as e: st.error(str(e))
                    if st.session_state.get("collab_code"):
                        st.markdown(f"""
                        <div style='background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.2);
                        border-radius:10px;padding:10px 14px;margin-top:8px'>
                          <div style='font-size:10px;color:rgba(201,168,76,0.6);text-transform:uppercase;letter-spacing:0.1em'>Share code</div>
                          <div style='font-size:20px;font-weight:700;color:#c9a84c;letter-spacing:0.15em;font-family:monospace'>{st.session_state["collab_code"]}</div>
                        </div>""",unsafe_allow_html=True)
                with cb2:
                    jc=st.text_input("Join code",placeholder="Enter code to join",key="jc_input",label_visibility="collapsed")
                    if st.button("Join trip",use_container_width=True) and jc:
                        try:
                            ok,msg=join_collab(user["username"],jc.upper())
                            (st.success if ok else st.error)(msg)
                        except Exception as e: st.error(str(e))

    _render_ai_bubble()

# ══════════════════════════════════════════════════════════════════
# STEP 5 — DAY DETAIL
# ══════════════════════════════════════════════════════════════════
def step_5():
    render_progress(5)
    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)

    dk=st.session_state.get("active_day","Day 1")
    city=st.session_state.get("dest_city","")
    cc=st.session_state.get("dest_cc","INT")
    lat=st.session_state.get("dest_lat",35.)
    lon=st.session_state.get("dest_lon",139.)
    itin=st.session_state.get("_itin",{})
    df=st.session_state.get("_df",pd.DataFrame())
    day_budgets=st.session_state.get("day_budgets",[100])
    user=_cur_user()

    all_days=list(itin.keys())
    di=all_days.index(dk) if dk in all_days else 0
    color=DAY_COLORS[di%len(DAY_COLORS)]
    d_bud=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
    stops=list(itin.get(dk,[]))

    # ── Top nav ──
    nav1,nav2,nav3=st.columns([1,3,1])
    with nav1:
        if st.button("← Overview",key="s5_back",use_container_width=True):
            st.session_state["step"]=4; st.rerun()
    with nav2:
        st.markdown(f'<div style="text-align:center"><span style="font-size:22px;font-weight:600;color:#f0ece4">{dk}</span> <span style="font-size:13px;color:rgba(240,236,228,0.4)">— {city.title()}</span></div>',unsafe_allow_html=True)
    with nav3:
        # Day switcher
        sel_dk=st.selectbox("",all_days,index=di,key="day_switch",label_visibility="collapsed")
        if sel_dk!=dk:
            st.session_state["active_day"]=sel_dk; st.rerun()

    # ── Budget bar ──
    sym,rate=local_rate(cc)
    total_est=sum(max(COST_FL.get(s.get("type_label",""),2), d_bud*COST_W.get(s.get("type_label",""),.12)/2) for s in stops)
    pct=min(100,round(total_est/d_bud*100)) if d_bud>0 else 0
    bar_color="#ef4444" if pct>100 else "#c9a84c"
    st.markdown(f"""
    <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
    border-radius:14px;padding:14px 18px;margin:12px 0'>
      <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
        <span style='font-size:13px;font-weight:500;color:#f0ece4'>Daily budget</span>
        <span style='font-size:13px;color:{bar_color};font-weight:600'>~${round(total_est)} / ${d_bud}</span>
      </div>
      <div style='background:rgba(255,255,255,0.08);border-radius:4px;height:4px'>
        <div style='background:{bar_color};height:4px;border-radius:4px;width:{pct}%;transition:width 0.3s'></div>
      </div>
    </div>
    """,unsafe_allow_html=True)

    # ── Main layout: list (left) + map (right) ──
    list_col,map_col=st.columns([1,1],gap="medium")

    tl_stops=build_timeline(stops)

    with list_col:
        st.markdown(f'<div style="font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(201,168,76,0.7);margin-bottom:8px">Schedule · {len(stops)} stops · ~{fmt_dur(sum(s.get("duration_min",60) for s in tl_stops))}</div>',unsafe_allow_html=True)

        # ── Stop list with reorder ──
        for si,s in enumerate(tl_stops):
            nm=_ss(s.get("name",""))
            tl=_ss(s.get("type_label",""))
            rat=s.get("rating",0)
            arr=s.get("arrive_time","")
            dep=s.get("depart_time","")
            dur=s.get("duration_min",60)
            tr=s.get("transport_to_next") or {}
            cs=cost_est(tl,d_bud,cc)

            # Custom badge for user-added places
            is_custom=s.get("district","")=="Custom"

            sc1,sc2,sc3=st.columns([1,5,1])
            with sc1:
                # Reorder buttons
                if si>0 and st.button("↑",key=f"up_{dk}_{si}",use_container_width=True):
                    stops[si],stops[si-1]=stops[si-1],stops[si]
                    new_itin=dict(itin); new_itin[dk]=stops
                    st.session_state["_itin"]=new_itin; st.rerun()
                if si<len(stops)-1 and st.button("↓",key=f"dn_{dk}_{si}",use_container_width=True):
                    stops[si],stops[si+1]=stops[si+1],stops[si]
                    new_itin=dict(itin); new_itin[dk]=stops
                    st.session_state["_itin"]=new_itin; st.rerun()

            with sc2:
                custom_tag=f'<span style="background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.3);border-radius:100px;padding:1px 7px;font-size:10px;color:#c9a84c;margin-left:6px">custom</span>' if is_custom else ""
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                border-left:3px solid {color};border-radius:12px;padding:12px 14px;margin:3px 0'>
                  <div style='display:flex;align-items:center;gap:6px;margin-bottom:4px'>
                    <div style='width:22px;height:22px;border-radius:50%;background:{color};
                    display:flex;align-items:center;justify-content:center;
                    font-size:10px;font-weight:700;color:#000;flex-shrink:0'>{si+1}</div>
                    <span style='font-weight:600;font-size:14px;color:#f0ece4'>{nm}</span>{custom_tag}
                  </div>
                  <div style='font-size:12px;color:rgba(240,236,228,0.4)'>{tl}{'&nbsp;·&nbsp;⭐ '+str(rat) if rat else ''}</div>
                  <div style='margin-top:6px;display:flex;flex-wrap:wrap;gap:5px'>
                    {"<span class='time-badge'>"+arr+"–"+dep+"</span>" if arr else ""}
                    <span style='font-size:11px;color:rgba(245,158,11,0.7)'>⏱ {fmt_dur(dur)}</span>
                    <span style='font-size:11px;color:rgba(201,168,76,0.6)'>💰 {cs}</span>
                  </div>
                  {"<div style='margin-top:5px'><span class='tr-badge'>🚇 "+_ss(tr.get("mode",""))+" · "+_ss(tr.get("duration",""))+"</span></div>" if tr else ""}
                </div>
                """,unsafe_allow_html=True)

            with sc3:
                st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
                # Remove
                if st.button("✕",key=f"rm_{dk}_{si}",use_container_width=True):
                    stops.pop(si); new_itin=dict(itin); new_itin[dk]=stops
                    st.session_state["_itin"]=new_itin; st.rerun()
                # Wishlist
                if user:
                    saved=_wl_chk_fn(user["username"],nm)
                    if st.button("♥" if saved else "♡",key=f"wl5_{dk}_{si}",use_container_width=True):
                        if saved: _wl_rm_fn(user["username"],nm); st.toast(f"Removed")
                        else:
                            _wl_add_fn(user["username"],{"name":nm,"lat":s.get("lat",0),"lon":s.get("lon",0),"type_label":tl,"rating":rat,"address":s.get("address","")})
                            st.toast(f"Saved ♥")
                        st.rerun()
                # Swap toggle
                sw_key=f"_sw5_{dk}_{si}"
                if st.button("↔",key=f"sw5_{dk}_{si}",use_container_width=True,help="Swap"):
                    st.session_state[sw_key]=not st.session_state.get(sw_key,False); st.rerun()

            # Swap panel
            if st.session_state.get(f"_sw5_{dk}_{si}",False):
                _render_swap_panel(itin,df,dk,si,cc,d_bud)

        # ── Add place ──
        st.markdown("<div style='margin-top:16px'></div>",unsafe_allow_html=True)
        with st.expander("+ Add a place to this day",expanded=False):
            at1,at2=st.columns([4,1])
            with at1:
                add_nm=st.text_input("Place name",placeholder="e.g. Eiffel Tower, local restaurant…",key=f"add_{dk}_nm",label_visibility="collapsed")
            with at2:
                if st.button("Add",key=f"add_{dk}_btn",use_container_width=True,type="primary") and add_nm.strip():
                    coord=None
                    with st.spinner("Locating…"):
                        coord=_nom(f"{add_nm.strip()} {city}") or _nom(add_nm.strip())
                    new_stop={"name":add_nm.strip(),
                              "lat":coord[0] if coord else lat+random.uniform(-.01,.01),
                              "lon":coord[1] if coord else lon+random.uniform(-.01,.01),
                              "type_label":"🏛️ Attraction","rating":4.5,"address":"","district":"Custom",
                              "description":"User added","time_slot":"TBD","transport_to_next":None}
                    stops.append(new_stop); new_itin=dict(itin); new_itin[dk]=stops
                    st.session_state["_itin"]=new_itin; st.toast(f"Added {add_nm}!"); st.rerun()

            # Search from discovered places
            if df is not None and not df.empty:
                in_day={s.get("name","") for s in stops}
                avail=df[~df["name"].isin(in_day)].head(20)
                if not avail.empty:
                    st.markdown('<div style="font-size:11px;color:rgba(240,236,228,0.35);margin:10px 0 6px">Or pick from discovered places:</div>',unsafe_allow_html=True)
                    sel_place=st.selectbox("Discovered places",["–"]+list(avail["name"]),key=f"add_{dk}_sel",label_visibility="collapsed")
                    if sel_place!="–":
                        row=avail[avail["name"]==sel_place].iloc[0]
                        if st.button(f"Add {sel_place[:30]} →",key=f"add_{dk}_go",use_container_width=True,type="primary"):
                            stops.append({**row.to_dict(),"time_slot":"TBD","transport_to_next":None})
                            new_itin=dict(itin); new_itin[dk]=stops
                            st.session_state["_itin"]=new_itin; st.toast(f"Added!"); st.rerun()

    with map_col:
        st.markdown(f'<div style="font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(201,168,76,0.7);margin-bottom:8px">{dk} Map</div>',unsafe_allow_html=True)
        if FOLIUM_OK:
            m=build_map(df,lat,lon,itin,active_day=dk)
            if m:
                st.markdown('<div class="map-wrap">',unsafe_allow_html=True)
                st_folium(m,width="100%",height=480,returned_objects=[])
                st.markdown("</div>",unsafe_allow_html=True)
                st.markdown('<div style="font-size:11px;color:rgba(240,236,228,0.3);margin-top:6px">Numbered markers match your schedule · Tap for details</div>',unsafe_allow_html=True)
        else:
            st.info("Install streamlit-folium for the interactive map.")

        # AI Must-See for this day
        st.markdown("<div style='margin-top:16px'></div>",unsafe_allow_html=True)
        with st.expander("✦ AI Must-See picks",expanded=False):
            sel_types=st.session_state.get("trip_types",["🏛️ Attraction"])
            picks=get_ai_mustsee(city,cc,st.session_state.get("trip_days",3),tuple(sel_types))
            if picks:
                in_day={s.get("name","") for s in stops}
                for pi,rec in enumerate(picks[:4]):
                    nm=_ss(rec.get("name",""))
                    already=nm in in_day
                    rc1,rc2=st.columns([4,1])
                    with rc1:
                        st.markdown(f"""
                        <div style='background:rgba(201,168,76,0.05);border:1px solid rgba(201,168,76,0.12);
                        border-radius:10px;padding:10px 12px;margin:4px 0'>
                          <div style='font-weight:600;font-size:13px;color:#f0ece4'>{nm}</div>
                          <div style='font-size:11px;color:rgba(201,168,76,0.6);margin-top:2px'>{_ss(rec.get("why",""))}</div>
                          <div style='font-size:11px;color:rgba(240,236,228,0.3)'>⭐ {rec.get("rating",4.5)} · {fmt_dur(rec.get("duration_min",60))}</div>
                        </div>""",unsafe_allow_html=True)
                    with rc2:
                        if already:
                            st.markdown('<div style="font-size:11px;color:#6ee7b7;text-align:center;padding-top:16px">✓ In</div>',unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
                            if st.button("+",key=f"ai5_{dk}_{pi}",use_container_width=True):
                                new_stop={"name":nm,"lat":rec.get("lat",lat+random.uniform(-.01,.01)),
                                          "lon":rec.get("lon",lon+random.uniform(-.01,.01)),
                                          "type_label":_ss(rec.get("type","🏛️ Attraction")),
                                          "rating":rec.get("rating",4.5),"address":"",
                                          "district":"AI Pick","description":_ss(rec.get("why","")),
                                          "time_slot":"TBD","transport_to_next":None}
                                stops.append(new_stop); new_itin=dict(itin); new_itin[dk]=stops
                                st.session_state["_itin"]=new_itin; st.toast(f"Added {nm}!"); st.rerun()
            else:
                st.caption("No AI picks available for this city.")

    _render_ai_bubble()

# ══════════════════════════════════════════════════════════════════
# SWAP PANEL
# ══════════════════════════════════════════════════════════════════
def _render_swap_panel(itin,df,dk,si,cc,d_bud):
    stops=itin.get(dk,[]); cur=stops[si]; cur_type=cur.get("type_label","")
    used={s.get("name","") for sl in itin.values() if isinstance(sl,list) for s in sl}
    st.markdown(f"""
    <div style='background:rgba(201,168,76,0.04);border:1px solid rgba(201,168,76,0.15);
    border-radius:12px;padding:14px;margin:6px 0'>
      <div style='font-size:12px;font-weight:600;color:#c9a84c;margin-bottom:10px'>
        Swap: <span style='color:#f0ece4'>{_ss(cur.get("name",""))}</span>
      </div>
    """,unsafe_allow_html=True)
    if df is not None and not df.empty:
        cands=df[(df["type_label"]==cur_type)&(~df["name"].isin(used))].sort_values("rating",ascending=False).head(4)
        if not cands.empty:
            sc_cols=st.columns(min(len(cands),4))
            for i,(_,alt) in enumerate(cands.iterrows()):
                with sc_cols[i%4]:
                    nm=_ss(alt["name"]); rat=alt.get("rating",0); dur=est_dur(nm,cur_type)
                    cs=cost_est(cur_type,d_bud,cc)
                    st.markdown(f"""
                    <div style='background:rgba(255,255,255,0.04);border-radius:10px;padding:10px;
                    border:1px solid rgba(255,255,255,0.07);margin-bottom:6px'>
                      <div style='font-weight:600;font-size:12px;color:#f0ece4'>{nm}</div>
                      <div style='font-size:11px;color:rgba(240,236,228,0.4)'>⭐ {rat} · {fmt_dur(dur)}</div>
                      <div style='font-size:11px;color:rgba(201,168,76,0.5)'>💰 {cs}</div>
                    </div>""",unsafe_allow_html=True)
                    if st.button("Select",key=f"swx_{dk}_{si}_{nm[:6]}",use_container_width=True,type="primary"):
                        new_itin=dict(itin); ds=list(new_itin.get(dk,[])); ds[si]=alt.to_dict()
                        new_itin[dk]=ds; st.session_state["_itin"]=new_itin
                        st.session_state.pop(f"_sw5_{dk}_{si}",None)
                        st.toast(f"Replaced with {nm}"); st.rerun()
        else:
            st.markdown('<div style="font-size:12px;color:rgba(240,236,228,0.35)">No alternatives found.</div>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)
    if st.button("Cancel",key=f"swxcancel_{dk}_{si}"):
        st.session_state.pop(f"_sw5_{dk}_{si}",None); st.rerun()

# ══════════════════════════════════════════════════════════════════
# AI BUBBLE & CHAT
# ══════════════════════════════════════════════════════════════════
def _render_ai_bubble():
    city=st.session_state.get("dest_city","")
    itin=st.session_state.get("_itin",{})
    itin_summary=f"{len(itin)} days in {city}, total {sum(len(v) for v in itin.values() if isinstance(v,list))} stops"

    ai_open=st.session_state.get("ai_open",False)

    # Floating bubble (CSS positioned)
    st.markdown("""
    <div class="ai-bubble-wrap">
      <div class="ai-bubble" title="AI Travel Assistant">✦</div>
    </div>
    """,unsafe_allow_html=True)

    # Toggle via streamlit button (positioned near bubble)
    with st.container():
        _,btncol=st.columns([5,1])
        with btncol:
            if st.button("✦ Ask AI",key="ai_toggle",use_container_width=True,
                         type="primary" if ai_open else "secondary"):
                st.session_state["ai_open"]=not ai_open; st.rerun()

    if ai_open:
        with st.container():
            st.markdown("""
            <div style='background:rgba(15,12,26,0.96);border:1px solid rgba(201,168,76,0.25);
            border-radius:20px;padding:20px;margin:8px 0 16px;
            box-shadow:0 20px 60px rgba(0,0,0,0.5)'>
              <div style='font-size:13px;font-weight:600;color:#c9a84c;margin-bottom:12px;
              display:flex;align-items:center;gap:8px'>
                <span>✦</span> <span>Voyager AI Assistant</span>
                <span style="font-size:10px;color:rgba(240,236,228,0.3);margin-left:4px">Powered by Claude</span>
              </div>
            """,unsafe_allow_html=True)

            # Chat history
            chat=st.session_state.get("ai_chat",[])
            for msg in chat[-8:]:
                role=msg.get("role",""); content=msg.get("content","")
                if role=="user":
                    st.markdown(f'<div style="text-align:right;margin:6px 0"><div style="display:inline-block;background:rgba(201,168,76,0.12);border:1px solid rgba(201,168,76,0.2);border-radius:12px 12px 3px 12px;padding:8px 12px;font-size:13px;color:#f0ece4;max-width:80%;text-align:left">{_ss(content)}</div></div>',unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="margin:6px 0"><div style="display:inline-block;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:3px 12px 12px 12px;padding:8px 12px;font-size:13px;color:#f0ece4;max-width:90%;line-height:1.6">{_ss(content)}</div></div>',unsafe_allow_html=True)

            # Quick prompts
            if not chat:
                st.markdown('<div style="font-size:11px;color:rgba(240,236,228,0.35);margin-bottom:8px">Quick questions:</div>',unsafe_allow_html=True)
                qp_cols=st.columns(2)
                quick_prompts=[f"Best hidden gems in {city}?","How to get around efficiently?",
                               "What to eat on Day 1?","Tips for saving money?"]
                for qi,qp in enumerate(quick_prompts):
                    with qp_cols[qi%2]:
                        if st.button(qp,key=f"qp_{qi}",use_container_width=True):
                            chat.append({"role":"user","content":qp})
                            with st.spinner("Thinking…"):
                                reply=call_ai_assistant(chat,city,itin_summary)
                            chat.append({"role":"assistant","content":reply})
                            st.session_state["ai_chat"]=chat; st.rerun()

            # Input
            user_q=st.text_input("Ask anything about your trip…",key="ai_input",label_visibility="collapsed",
                                  placeholder=f"Ask about {city}, restaurants, transport, tips…")
            ac1,ac2=st.columns([4,1])
            with ac2:
                if st.button("Send →",key="ai_send",use_container_width=True,type="primary") and user_q.strip():
                    chat.append({"role":"user","content":user_q.strip()})
                    with st.spinner("…"):
                        reply=call_ai_assistant(chat,city,itin_summary)
                    chat.append({"role":"assistant","content":reply})
                    st.session_state["ai_chat"]=chat; st.rerun()
            with ac1:
                if chat and st.button("Clear chat",key="ai_clear",use_container_width=True):
                    st.session_state["ai_chat"]=[]; st.rerun()

            st.markdown("</div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════
# Wordmark
st.markdown("""
<div class="wordmark">V O <span>Y</span> A G E R</div>
""",unsafe_allow_html=True)

step=st.session_state.get("step",1)
if   step==1: step_1()
elif step==2: step_2()
elif step==3: step_3()
elif step==4: step_4()
elif step==5: step_5()
else: st.session_state["step"]=1; st.rerun()

# Footer
st.markdown("""
<div style='text-align:center;padding:32px 0 16px;font-size:11px;letter-spacing:0.1em;
text-transform:uppercase;color:rgba(201,168,76,0.2)'>
Voyager · AI Travel Planning · All rights reserved
</div>
""",unsafe_allow_html=True)
