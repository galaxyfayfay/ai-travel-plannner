"""
Voyager AI Travel Planner v4
White + Gold + Glass · Apple Design System
All 7 issues addressed
"""

import math, random, re, json, os, time
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Voyager",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Secrets ───────────────────────────────────────────────────────
def _get_secret(k):
    try:
        v = st.secrets.get(k, "")
        if v: return str(v)
    except: pass
    return os.getenv(k, "")

AMAP_KEY      = _get_secret("APIKEY")
DEEPSEEK_KEY  = _get_secret("DEEPSEEKKEY")
ANTHROPIC_KEY = _get_secret("ANTHROPIC_API_KEY")

# ── Optional modules ──────────────────────────────────────────────
try:
    from ai_planner import generate_itinerary; AI_OK = True
except Exception as _e: AI_OK = False; _AI_ERR = str(_e)
try:
    from transport_planner import build_day_schedule, estimate_travel; TRANSPORT_OK = True
except: TRANSPORT_OK = False
try:
    from auth_manager import register_user, login_user, get_user_from_session, logout_user, create_collab_link, join_collab; AUTH_OK = True
except: AUTH_OK = False
try:
    from wishlist_manager import (add_to_wishlist as _wl_add, remove_from_wishlist as _wl_remove,
        get_wishlist as _wl_get, is_in_wishlist as _wl_check,
        save_itinerary as _save_itin_ext, swap_place_in_itinerary); WISHLIST_EXT = True
except: WISHLIST_EXT = False
try:
    from points_system import add_points, get_points; POINTS_OK = True
except: POINTS_OK = False
try:
    import folium; from streamlit_folium import st_folium; FOLIUM_OK = True
except: FOLIUM_OK = False

# ═══════════════════════════════════════════════════════════════
# I18N
# ═══════════════════════════════════════════════════════════════
LANG_DATA = {
    "EN": {
        "brand": "VOYAGER",
        "tagline": "AI Travel Planner",
        "welcome_title": "Plan your perfect journey",
        "welcome_sub": "AI-curated itineraries for discerning travellers worldwide",
        "sign_in": "Sign In",
        "guest": "Continue as Guest",
        "register": "Create Account",
        "username_ph": "Enter your username",
        "password_ph": "Enter your password",
        "email_ph": "your@email.com",
        "reg_user_ph": "Choose a username (min 3 chars)",
        "reg_pass_ph": "Create a password (min 6 chars)",
        "guest_features": ["AI itinerary generation", "Real-time place discovery", "Interactive maps", "Cost estimation"],
        "where_title": "Where are you going?",
        "where_sub": "Search any city or pick from popular destinations",
        "search_city_ph": "Search any city, e.g. Kyoto, Santorini, Cusco…",
        "country_label": "Filter by country",
        "popular": "Popular destinations",
        "more_cities": "Show more",
        "selected": "Selected destination",
        "next": "Next →",
        "back": "← Back",
        "pref_title": "Craft your experience",
        "pref_sub": "Set your dates, interests, and daily preferences",
        "duration": "Trip duration",
        "days_label": "days",
        "base_budget": "Daily budget (USD)",
        "interests": "What do you love?",
        "must_visit": "Must-visit places",
        "must_visit_sub": "Add specific places — they'll be included in your itinerary",
        "add_place_ph": "e.g. Eiffel Tower, Jiro's Sushi, Central Park…",
        "add": "+ Add",
        "per_day": "Per-day settings",
        "per_day_sub": "Customize budget & stops for each day",
        "stops_per_type": "Stops per type",
        "optional_logistics": "Start / End / Hotel (optional)",
        "start_ph": "e.g. Tokyo Station, Airport",
        "end_ph": "e.g. Narita Airport",
        "hotel_ph": "Hotel name or address",
        "build": "Build My Itinerary ✦",
        "overview_title": "Your Itinerary",
        "tap_day": "Tap any day to plan in detail →",
        "plan_day": "Plan this day →",
        "wishlist": "My Wishlist",
        "collab": "Collaborate",
        "collab_sub": "Share a code so friends can co-edit your trip",
        "gen_code": "Generate share code",
        "join_code": "Join with a code",
        "join_code_ph": "Paste share code here",
        "join": "Join trip",
        "day_title": "Day detail",
        "schedule": "Schedule",
        "day_map": "Day map",
        "ai_picks": "AI Must-See",
        "add_to_day": "Add to this day",
        "add_name_ph": "Place name, e.g. Louvre Museum, hidden café…",
        "or_discover": "Or pick from nearby discovered places",
        "save_day": "Save & back to overview →",
        "ask_ai": "Ask AI",
        "ai_title": "Voyager AI Assistant",
        "ai_sub": "Powered by Claude",
        "ai_ph": "Ask anything about your trip…",
        "send": "Send →",
        "clear": "Clear chat",
        "shuffle": "🔀 Shuffle",
        "save": "♥ Save",
        "export": "⬇ Export",
        "edit_prefs": "← Edit",
        "days_unit": "days",
        "stops_unit": "stops",
        "est": "Est. total",
        "avg_day": "avg/day",
        "add_here": "Add here",
        "remove": "Remove",
        "swap": "Swap",
        "cancel": "Cancel",
        "select": "Select",
        "alternatives": "Alternatives",
        "in_schedule": "✓ In schedule",
        "reorder_hint": "Drag cards to reorder · Tap ✕ to remove",
        "no_alt": "No alternatives found for this type.",
        "discovering": "Discovering places",
        "crafting": "Crafting your itinerary…",
        "locating": "Locating…",
        "budget_label": "Daily budget",
        "quick_q": "Quick questions:",
    },
    "ZH": {
        "brand": "旅行家",
        "tagline": "AI 智能旅行规划",
        "welcome_title": "规划你的完美旅程",
        "welcome_sub": "为精致旅行者量身定制的 AI 行程规划",
        "sign_in": "登录",
        "guest": "以游客身份继续",
        "register": "注册账户",
        "username_ph": "请输入用户名",
        "password_ph": "请输入密码",
        "email_ph": "your@email.com",
        "reg_user_ph": "选择用户名（至少3个字符）",
        "reg_pass_ph": "创建密码（至少6个字符）",
        "guest_features": ["AI 智能行程生成", "实时地点发现", "互动地图", "费用估算"],
        "where_title": "你想去哪里？",
        "where_sub": "搜索任意城市，或从热门目的地中选择",
        "search_city_ph": "搜索城市，如 京都、圣托里尼、库斯科…",
        "country_label": "按国家筛选",
        "popular": "热门目的地",
        "more_cities": "更多城市",
        "selected": "已选择",
        "next": "下一步 →",
        "back": "← 返回",
        "pref_title": "定制你的旅行体验",
        "pref_sub": "设置行程天数、兴趣偏好和每日预算",
        "duration": "行程天数",
        "days_label": "天",
        "base_budget": "每日预算（美元）",
        "interests": "你喜欢什么？",
        "must_visit": "必去地点",
        "must_visit_sub": "添加特定地点——它们会被纳入行程",
        "add_place_ph": "如 埃菲尔铁塔、中央公园、故宫…",
        "add": "+ 添加",
        "per_day": "每日详细设置",
        "per_day_sub": "为每一天单独设置预算和景点数量",
        "stops_per_type": "每类型景点数量",
        "optional_logistics": "出发 / 目的地 / 酒店（可选）",
        "start_ph": "如 东京站、机场",
        "end_ph": "如 成田机场",
        "hotel_ph": "酒店名称或地址",
        "build": "生成我的行程 ✦",
        "overview_title": "我的行程",
        "tap_day": "点击任意一天进行详细规划 →",
        "plan_day": "规划这一天 →",
        "wishlist": "我的心愿单",
        "collab": "协作编辑",
        "collab_sub": "分享代码，邀请朋友共同编辑行程",
        "gen_code": "生成分享码",
        "join_code": "加入协作",
        "join_code_ph": "粘贴分享码",
        "join": "加入",
        "day_title": "当日详情",
        "schedule": "行程安排",
        "day_map": "当日地图",
        "ai_picks": "AI 推荐",
        "add_to_day": "添加到今天",
        "add_name_ph": "地点名称，如 卢浮宫、当地咖啡馆…",
        "or_discover": "或从附近发现的地点中选择",
        "save_day": "保存并返回总览 →",
        "ask_ai": "问问 AI",
        "ai_title": "旅行家 AI 助手",
        "ai_sub": "由 Claude 提供支持",
        "ai_ph": "关于行程的任何问题…",
        "send": "发送 →",
        "clear": "清除对话",
        "shuffle": "🔀 重新生成",
        "save": "♥ 保存",
        "export": "⬇ 导出",
        "edit_prefs": "← 修改",
        "days_unit": "天",
        "stops_unit": "个景点",
        "est": "预计总费用",
        "avg_day": "均/天",
        "add_here": "添加",
        "remove": "删除",
        "swap": "替换",
        "cancel": "取消",
        "select": "选择",
        "alternatives": "可替换选项",
        "in_schedule": "✓ 已在行程中",
        "reorder_hint": "拖拽卡片重新排序 · 点击 ✕ 删除",
        "no_alt": "未找到同类型的替换选项",
        "discovering": "正在发现景点",
        "crafting": "正在生成行程…",
        "locating": "正在定位…",
        "budget_label": "每日预算",
        "quick_q": "快捷提问：",
    }
}

def T(key):
    lang = st.session_state.get("lang", "EN")
    return LANG_DATA.get(lang, LANG_DATA["EN"]).get(key, key)

# ═══════════════════════════════════════════════════════════════
# CSS — White / Gold / Apple Glass
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Background: warm white with subtle gradient ── */
.stApp {
  background: linear-gradient(145deg, #fdfcf8 0%, #f9f6ee 40%, #faf8f2 100%) !important;
  min-height: 100vh;
}

/* Hide sidebar & streamlit chrome */
section[data-testid="stSidebar"] { display: none !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── CSS Variables ── */
:root {
  --gold: #b8943a;
  --gold-light: #d4aa52;
  --gold-pale: #f0e8d0;
  --gold-glass: rgba(184, 148, 58, 0.08);
  --gold-border: rgba(184, 148, 58, 0.22);
  --gold-border-strong: rgba(184, 148, 58, 0.45);
  --white-glass: rgba(255, 255, 255, 0.72);
  --white-glass-strong: rgba(255, 255, 255, 0.88);
  --border: rgba(0, 0, 0, 0.07);
  --border-mid: rgba(0, 0, 0, 0.11);
  --text-1: #1a1610;
  --text-2: #5a5040;
  --text-3: #9a8c78;
  --text-gold: #8a6c28;
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.08);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.10);
}

/* ── Glass card ── */
.glass {
  background: var(--white-glass);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  border: 1px solid var(--border);
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}
.glass::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent);
}

/* ── Progress bar ── */
.prog-wrap {
  display: flex; align-items: flex-start; justify-content: center;
  max-width: 520px; margin: 0 auto; padding: 24px 0 0;
}
.prog-step { display: flex; flex-direction: column; align-items: center; flex: 1; }
.prog-dot {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600;
  transition: all 0.3s ease;
}
.prog-dot.done {
  background: linear-gradient(135deg, var(--gold), var(--gold-light));
  color: white;
  box-shadow: 0 2px 12px rgba(184,148,58,0.35);
}
.prog-dot.active {
  background: white;
  border: 2px solid var(--gold);
  color: var(--gold);
  box-shadow: 0 0 0 4px rgba(184,148,58,0.12);
}
.prog-dot.pending {
  background: #f0ede8;
  border: 1.5px solid #d8d0c0;
  color: #b0a090;
}
.prog-lbl {
  font-size: 10px; font-weight: 500;
  margin-top: 6px; letter-spacing: 0.06em; text-transform: uppercase;
}
.prog-lbl.active  { color: var(--gold); }
.prog-lbl.done    { color: var(--text-3); }
.prog-lbl.pending { color: #c0b8a8; }
.prog-line {
  flex: 1; height: 1px; background: #e0d8c8; position: relative; top: -17px;
}
.prog-line.done { background: linear-gradient(90deg, var(--gold-light), #e0d8c8); }

/* ── Typography ── */
.page-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 32px; font-weight: 500;
  color: var(--text-1); letter-spacing: -0.02em;
  line-height: 1.2; margin: 0 0 8px;
}
.page-title em { font-style: italic; color: var(--gold); }
.page-sub {
  font-size: 15px; color: var(--text-2);
  line-height: 1.6; margin-bottom: 28px; font-weight: 400;
}
.section-label {
  font-size: 10px; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-gold);
  margin-bottom: 10px; display: block;
}

/* ── Buttons ── */
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important; font-size: 14px !important;
  border-radius: 12px !important;
  transition: all 0.2s ease !important;
  border: none !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%) !important;
  color: white !important; font-weight: 600 !important;
  box-shadow: 0 4px 16px rgba(184,148,58,0.30) !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(184,148,58,0.40) !important;
}
.stButton > button:not([kind="primary"]) {
  background: var(--white-glass) !important;
  border: 1px solid var(--border-mid) !important;
  color: var(--text-2) !important;
  backdrop-filter: blur(8px) !important;
}
.stButton > button:not([kind="primary"]):hover {
  background: white !important; color: var(--text-1) !important;
  border-color: var(--gold-border) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
  background: white !important;
  border: 1.5px solid var(--border-mid) !important;
  border-radius: 12px !important;
  color: var(--text-1) !important;
  font-size: 14px !important;
  font-family: 'Inter', sans-serif !important;
  transition: border-color 0.2s !important;
  box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--gold-border-strong) !important;
  box-shadow: 0 0 0 3px rgba(184,148,58,0.10) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: #c0b0a0 !important; }
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stMultiSelect label, .stSlider label {
  color: var(--text-2) !important; font-size: 12px !important;
  font-weight: 600 !important; letter-spacing: 0.05em !important;
}
.stSelectbox > div > div {
  background: white !important;
  border: 1.5px solid var(--border-mid) !important;
  border-radius: 12px !important; color: var(--text-1) !important;
  box-shadow: var(--shadow-sm) !important;
}
.stSlider > div > div > div > div { background: var(--gold) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.7) !important;
  border-radius: 12px !important;
  border: 1px solid var(--border) !important;
  padding: 3px !important; gap: 2px !important;
  box-shadow: var(--shadow-sm) !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 9px !important;
  color: var(--text-3) !important;
  font-size: 13px !important; font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
  background: white !important; color: var(--text-1) !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ── Metrics ── */
div[data-testid="stMetric"] {
  background: var(--white-glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px !important; padding: 16px 20px !important;
  box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stMetric"] label {
  color: var(--text-3) !important; font-size: 10px !important;
  font-weight: 600 !important; text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: var(--text-1) !important; font-size: 22px !important;
  font-weight: 700 !important;
}

/* ── Expander ── */
.stExpander {
  background: var(--white-glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
  background: var(--gold-glass) !important;
  color: var(--text-gold) !important;
  border: 1px solid var(--gold-border) !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 12px !important; }
.stCaption { color: var(--text-3) !important; font-size: 12px !important; }

/* ── Day overview card ── */
.day-overview-card {
  background: var(--white-glass-strong);
  border: 1px solid var(--border);
  border-radius: 16px; padding: 18px 20px;
  margin: 8px 0; cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}
.day-overview-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--gold-border);
  transform: translateY(-1px);
}

/* ── Stop card (day detail) ── */
.stop-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 14px; padding: 14px 16px; margin: 6px 0;
  transition: all 0.2s; box-shadow: var(--shadow-sm);
  cursor: grab;
}
.stop-card:hover { box-shadow: var(--shadow-md); border-color: var(--gold-border); }

/* ── Pill tags ── */
.tag-gold {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 100px;
  background: var(--gold-glass); border: 1px solid var(--gold-border);
  font-size: 11px; font-weight: 600; color: var(--text-gold);
}
.tag-time {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 100px;
  background: rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.08);
  font-size: 11px; font-weight: 500; color: var(--text-2);
}
.tag-transport {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 100px;
  background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.14);
  font-size: 11px; font-weight: 500; color: #3b82f6;
}

/* ── Map wrapper ── */
.map-wrap {
  border-radius: 16px; overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}

/* ── AI bubble ── */
.ai-bubble-btn {
  position: fixed; bottom: 24px; right: 24px; z-index: 9999;
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, var(--gold), var(--gold-light));
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; cursor: pointer;
  box-shadow: 0 4px 20px rgba(184,148,58,0.40), 0 0 0 4px rgba(184,148,58,0.10);
  transition: all 0.2s;
}
.ai-bubble-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 8px 28px rgba(184,148,58,0.50);
}

/* ── AI chat panel ── */
.ai-panel {
  background: var(--white-glass-strong);
  border: 1px solid var(--gold-border);
  border-radius: 20px; padding: 20px;
  box-shadow: var(--shadow-lg);
  margin: 8px 0 16px;
}
.chat-user {
  display: flex; justify-content: flex-end; margin: 6px 0;
}
.chat-user > div {
  background: linear-gradient(135deg, var(--gold), var(--gold-light));
  color: white; padding: 9px 14px; border-radius: 16px 16px 4px 16px;
  font-size: 13px; max-width: 75%; line-height: 1.5;
}
.chat-ai > div {
  background: white; color: var(--text-1);
  padding: 9px 14px; border-radius: 4px 16px 16px 16px;
  border: 1px solid var(--border); font-size: 13px;
  max-width: 85%; line-height: 1.6;
  box-shadow: var(--shadow-sm);
}

/* ── Swap panel ── */
.swap-panel {
  background: rgba(255,251,240,0.95);
  border: 1.5px solid var(--gold-border);
  border-radius: 14px; padding: 16px; margin: 6px 0;
}

/* ── Wishlist item ── */
.wl-item {
  background: white; border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 14px; margin: 4px 0;
  display: flex; align-items: center; gap: 12px;
}

/* ── Collab box ── */
.collab-code {
  background: var(--gold-glass);
  border: 1px solid var(--gold-border);
  border-radius: 12px; padding: 12px 16px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 22px; font-weight: 700;
  color: var(--text-gold); letter-spacing: 0.15em;
  text-align: center;
}

/* ── Budget progress bar ── */
.bud-bar-wrap {
  background: #f0ede8; border-radius: 4px; height: 5px; overflow: hidden;
}
.bud-bar-fill {
  height: 5px; border-radius: 4px;
  transition: width 0.4s ease;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f5f0e8; }
::-webkit-scrollbar-thumb { background: #d4aa52; border-radius: 4px; }

/* ── Multiselect ── */
.stMultiSelect > div > div {
  background: white !important;
  border: 1.5px solid var(--border-mid) !important;
  border-radius: 12px !important;
}
.stMultiSelect span[data-baseweb="tag"] {
  background: var(--gold-glass) !important;
  border-color: var(--gold-border) !important;
  color: var(--text-gold) !important;
}

/* Form submit button override */
.stFormSubmitButton > button {
  background: linear-gradient(135deg, var(--gold), var(--gold-light)) !important;
  color: white !important; font-weight: 600 !important;
  box-shadow: 0 4px 16px rgba(184,148,58,0.30) !important;
  border: none !important; border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
CHAIN_BL = ["kfc","mcdonald","starbucks","seven-eleven","family mart","711","lawson","costa coffee"]
def is_chain(n): return any(k in n.lower() for k in CHAIN_BL)

def _ss(s):
    if s is None: return ""
    s = str(s)
    for o, n in {"\u2014":"-","\u2013":"-","\u2019":"'","\u201c":'"',"\u201d":'"',"\u2026":"..."}.items():
        s = s.replace(o, n)
    return s

def _hkm(la1, lo1, la2, lo2):
    R = 6371.0; dl = math.radians(la2-la1); dg = math.radians(lo2-lo1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dg/2)**2
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))

PTYPES = {
    "🏛️ Attraction":   {"osm":("tourism","attraction"), "amap":"110000","color":"#b8943a"},
    "🍜 Restaurant":   {"osm":("amenity","restaurant"),  "amap":"050000","color":"#c9765a"},
    "☕ Cafe":          {"osm":("amenity","cafe"),         "amap":"050500","color":"#8b7355"},
    "🌿 Park":          {"osm":("leisure","park"),         "amap":"110101","color":"#5a8a5a"},
    "🛍️ Shopping":     {"osm":("shop","mall"),            "amap":"060000","color":"#c9607a"},
    "🍺 Bar/Nightlife": {"osm":("amenity","bar"),          "amap":"050600","color":"#7a6ab0"},
    "🏨 Hotel":         {"osm":("tourism","hotel"),         "amap":"100000","color":"#4a8ab0"},
}
DAY_COLORS = ["#b8943a","#c9765a","#5a8a5a","#c9607a","#7a6ab0","#4a8ab0","#8b7355","#a07040"]

AMAP_KW = {
    "🏛️ Attraction":["旅游景点","博物馆"],"🍜 Restaurant":["餐馆","美食"],
    "☕ Cafe":["咖啡","下午茶"],"🌿 Park":["公园","花园"],
    "🛍️ Shopping":["商场","购物中心"],"🍺 Bar/Nightlife":["酒吧","夜店"],
    "🏨 Hotel":["酒店","宾馆"],
}

DURATION_MAP = {"🏛️ Attraction":90,"🍜 Restaurant":60,"☕ Cafe":45,"🌿 Park":60,
                "🛍️ Shopping":90,"🍺 Bar/Nightlife":90,"🏨 Hotel":20}
DURATION_SPEC = {"museum":120,"palace":120,"castle":120,"temple":60,"shrine":45,"cathedral":60,
                 "market":75,"gallery":75,"park":60,"garden":75,"tower":45,"viewpoint":30,
                 "crossing":20,"restaurant":60,"cafe":45,"mall":90,"beach":90,"aquarium":90}

def est_dur(name, tl):
    nl = (name or "").lower()
    for k, v in DURATION_SPEC.items():
        if k in nl: return v
    return DURATION_MAP.get(tl, 60)

def fmt_dur(m):
    if m < 60: return f"{m}min"
    h = m//60; r = m%60
    return f"{h}h {r}min" if r else f"{h}h"

def _parse_dur(s):
    if not s: return 20
    s = s.lower().strip(); total = 0
    h = re.search(r'(\d+)\s*h', s); m = re.search(r'(\d+)\s*m', s)
    if h: total += int(h.group(1))*60
    if m: total += int(m.group(1))
    return total if total > 0 else 20

CURRENCIES = {"CN":("¥",7.25),"JP":("¥",155),"KR":("₩",1350),"TH":("฿",36),
              "SG":("S$",1.35),"FR":("€",0.92),"GB":("£",0.79),"IT":("€",0.92),
              "ES":("€",0.92),"US":("$",1.0),"AU":("A$",1.53),"AE":("AED",3.67),
              "NL":("€",0.92),"TR":("₺",32),"HK":("HK$",7.82),"TW":("NT$",32),"INT":("$",1.0)}
def local_rate(cc): return CURRENCIES.get(cc, ("$",1.0))

COST_W  = {"🏛️ Attraction":0.18,"🍜 Restaurant":0.25,"☕ Cafe":0.10,"🌿 Park":0.04,
           "🛍️ Shopping":0.22,"🍺 Bar/Nightlife":0.16,"🏨 Hotel":0.00}
COST_FL = {"🏛️ Attraction":4,"🍜 Restaurant":6,"☕ Cafe":3,"🌿 Park":0,
           "🛍️ Shopping":8,"🍺 Bar/Nightlife":5,"🏨 Hotel":0}

def cost_est(tl, daily, cc):
    w = COST_W.get(tl,.12); fl = COST_FL.get(tl,2)
    pv = max(fl, daily*w/2); lo = pv*.65; hi = pv*1.45
    sym, rate = local_rate(cc)
    if cc == "US": return f"${round(lo)}–${round(hi)}"
    return f"${round(lo)}–${round(hi)} ({sym}{round(lo*rate)}–{sym}{round(hi*rate)})"

WORLD_CITIES = {
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nara"],
    "South Korea":["Seoul","Busan","Jeju"],
    "Thailand":["Bangkok","Chiang Mai","Phuket"],
    "Vietnam":["Ho Chi Minh City","Hanoi","Da Nang","Hoi An"],
    "Indonesia":["Bali","Jakarta"],
    "Malaysia":["Kuala Lumpur","Penang"],
    "Singapore":["Singapore"],
    "India":["Mumbai","Delhi","Jaipur","Goa"],
    "UAE":["Dubai","Abu Dhabi"],
    "Turkey":["Istanbul","Cappadocia"],
    "France":["Paris","Nice","Lyon"],
    "Italy":["Rome","Milan","Florence","Venice"],
    "Spain":["Barcelona","Madrid","Seville"],
    "United Kingdom":["London","Edinburgh"],
    "Germany":["Berlin","Munich"],
    "Netherlands":["Amsterdam"],
    "Switzerland":["Zurich","Lucerne","Zermatt"],
    "Austria":["Vienna","Salzburg"],
    "Greece":["Athens","Santorini","Mykonos"],
    "Portugal":["Lisbon","Porto"],
    "Czech Republic":["Prague"],
    "Hungary":["Budapest"],
    "Croatia":["Dubrovnik","Split"],
    "Norway":["Oslo","Bergen"],
    "Iceland":["Reykjavik"],
    "USA":["New York","Los Angeles","San Francisco","Miami","Chicago","Las Vegas"],
    "Canada":["Toronto","Vancouver","Banff"],
    "Mexico":["Mexico City","Cancun"],
    "Brazil":["Rio de Janeiro"],
    "Peru":["Cusco","Lima"],
    "Australia":["Sydney","Melbourne","Cairns"],
    "New Zealand":["Auckland","Queenstown"],
    "Morocco":["Marrakech","Fes"],
    "Egypt":["Cairo"],
    "South Africa":["Cape Town"],
    "China":["Beijing","Shanghai","Chengdu","Hangzhou","Xi'an"],
    "Hong Kong":["Hong Kong"],
    "Taiwan":["Taipei"],
}
COUNTRY_CODES = {
    "China":"CN","Japan":"JP","South Korea":"KR","Thailand":"TH","Vietnam":"VN",
    "Indonesia":"ID","Malaysia":"MY","Singapore":"SG","India":"IN","UAE":"AE","Turkey":"TR",
    "France":"FR","Italy":"IT","Spain":"ES","United Kingdom":"GB","Germany":"DE",
    "Netherlands":"NL","Switzerland":"CH","Austria":"AT","Greece":"GR","Portugal":"PT",
    "Czech Republic":"CZ","Hungary":"HU","Croatia":"HR","Norway":"NO","Iceland":"IS",
    "USA":"US","Canada":"CA","Mexico":"MX","Brazil":"BR","Peru":"PE","Australia":"AU",
    "New Zealand":"NZ","Morocco":"MA","Egypt":"EG","South Africa":"ZA",
    "Hong Kong":"HK","Taiwan":"TW",
}
INTL_CITIES = {
    "tokyo":(35.6762,139.6503,"JP"),"osaka":(34.6937,135.5023,"JP"),
    "kyoto":(35.0116,135.7681,"JP"),"nara":(34.6851,135.8050,"JP"),
    "sapporo":(43.0642,141.3469,"JP"),"fukuoka":(33.5904,130.4017,"JP"),
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
    "mykonos":(37.4467,25.3289,"GR"),
    "lisbon":(38.7223,-9.1393,"PT"),"porto":(41.1579,-8.6291,"PT"),
    "prague":(50.0755,14.4378,"CZ"),"budapest":(47.4979,19.0402,"HU"),
    "dubrovnik":(42.6507,18.0944,"HR"),
    "reykjavik":(64.1265,-21.8174,"IS"),
    "new york":(40.7128,-74.0060,"US"),"los angeles":(34.0522,-118.2437,"US"),
    "san francisco":(37.7749,-122.4194,"US"),"miami":(25.7617,-80.1918,"US"),
    "chicago":(41.8781,-87.6298,"US"),"las vegas":(36.1699,-115.1398,"US"),
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
    "kuala lumpur":(3.1390,101.6869,"MY"),"penang":(5.4164,100.3327,"MY"),
    "beijing":(39.9042,116.4074,"CN"),"shanghai":(31.2304,121.4737,"CN"),
    "chengdu":(30.5728,104.0668,"CN"),"hangzhou":(30.2741,120.1551,"CN"),
    "xi'an":(34.3416,108.9398,"CN"),
    "mumbai":(19.0760,72.8777,"IN"),"delhi":(28.6139,77.2090,"IN"),
    "jaipur":(26.9124,75.7873,"IN"),"goa":(15.2993,74.1240,"IN"),
    "cancun":(21.1619,-86.8515,"MX"),
    "rio de janeiro":(-22.9068,-43.1729,"BR"),
    "cusco":(-13.5320,-71.9675,"PE"),
    "zurich":(47.3769,8.5417,"CH"),"lucerne":(47.0502,8.3093,"CH"),
    "zermatt":(46.0207,7.7491,"CH"),
    "oslo":(59.9139,10.7522,"NO"),"bergen":(60.3913,5.3221,"NO"),
    "abu dhabi":(24.4539,54.3773,"AE"),
    "seville":(37.3891,-5.9845,"ES"),
    "munich":(48.1351,11.5820,"DE"),
    "lyon":(45.7640,4.8357,"FR"),
    "naples":(40.8518,14.2681,"IT"),
}
CN_CITIES = {
    "beijing":(39.9042,116.4074),"shanghai":(31.2304,121.4737),
    "guangzhou":(23.1291,113.2644),"shenzhen":(22.5431,114.0579),
    "chengdu":(30.5728,104.0668),"hangzhou":(30.2741,120.1551),
    "xi'an":(34.3416,108.9398),"xian":(34.3416,108.9398),
    "chongqing":(29.5630,106.5516),"nanjing":(32.0603,118.7969),
}

POPULAR = [
    ("🗼","Tokyo","Japan"),("🌆","Dubai","UAE"),("🗽","New York","USA"),
    ("🗺️","Paris","France"),("🏖️","Bali","Indonesia"),("🏰","Rome","Italy"),
    ("🌸","Kyoto","Japan"),("🎭","London","United Kingdom"),
    ("🌃","Barcelona","Spain"),("🌴","Bangkok","Thailand"),
    ("🏔️","Santorini","Greece"),("🎋","Singapore","Singapore"),
    ("🦁","Cape Town","South Africa"),("🌊","Lisbon","Portugal"),
    ("🏯","Seoul","South Korea"),("🎠","Prague","Czech Republic"),
    ("🎆","Sydney","Australia"),("❄️","Reykjavik","Iceland"),
    ("🏔️","Queenstown","New Zealand"),("🌺","Marrakech","Morocco"),
]

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
_DEFS = {
    "lang":"EN","step":1,"user_mode":None,"_auth_token":"",
    "dest_city":"","dest_country":"","dest_lat":None,"dest_lon":None,
    "dest_cc":"INT","dest_is_cn":False,
    "trip_days":3,"trip_types":["🏛️ Attraction","🍜 Restaurant"],"trip_budget":100,
    "day_configs":{},"custom_places":[],
    "_itin":None,"_df":None,"seed":42,
    "active_day":None,"ai_chat":[],"ai_open":False,
    "collab_code":"","popular_page":0,
}
for k, v in _DEFS.items():
    if k not in st.session_state: st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    try:
        tok = st.session_state.get("_auth_token","")
        if not tok: return None
        return get_user_from_session(tok)
    except: return None

def _wl_add_fn(u, p):
    if WISHLIST_EXT:
        try: _wl_add(u, p); return
        except: pass
    k = f"_wl_{u}"; lst = st.session_state.get(k, [])
    if p.get("name","") not in {x.get("name","") for x in lst}:
        lst.append(p); st.session_state[k] = lst

def _wl_rm_fn(u, name):
    if WISHLIST_EXT:
        try: _wl_remove(u, name); return
        except: pass
    k = f"_wl_{u}"
    st.session_state[k] = [p for p in st.session_state.get(k,[]) if p.get("name","") != name]

def _wl_get_fn(u):
    if WISHLIST_EXT:
        try: return _wl_get(u)
        except: pass
    return st.session_state.get(f"_wl_{u}", [])

def _wl_chk_fn(u, name):
    if WISHLIST_EXT:
        try: return _wl_check(u, name)
        except: pass
    return any(p.get("name","") == name for p in st.session_state.get(f"_wl_{u}",[]))

def _save_itin(u, itin, city, title):
    if WISHLIST_EXT:
        try: _save_itin_ext(u, itin, city, title); return
        except: pass
    k = f"_saved_{u}"; s = st.session_state.get(k, [])
    s.append({"city":city,"title":title,"data":itin,"at":datetime.now().strftime("%Y-%m-%d")})
    st.session_state[k] = s[-10:]

def build_timeline(stops, start_h=9):
    result = []; cur = start_h * 60
    for i, s in enumerate(stops):
        tl = s.get("type_label","🏛️ Attraction")
        nm = s.get("name",""); dur = est_dur(nm, tl)
        if i > 0:
            tr = stops[i-1].get("transport_to_next") or {}
            cur += _parse_dur(tr.get("duration",""))
        arr_h = cur//60; arr_m = cur%60
        dep = cur+dur; dep_h = dep//60; dep_m = dep%60
        e = dict(s)
        e["arrive_time"] = f"{arr_h:02d}:{arr_m:02d}"
        e["depart_time"] = f"{dep_h:02d}:{dep_m:02d}"
        e["duration_min"] = dur
        result.append(e); cur = dep + 15
    return result

def geo_dedup(places, r=100.):
    if not places: return []
    merged = [False]*len(places); kept = []
    for i, p in enumerate(places):
        if merged[i]: continue
        best = p
        for j in range(i+1, len(places)):
            if merged[j]: continue
            d = _hkm(best["lat"],best["lon"],places[j]["lat"],places[j]["lon"])*1000
            sl = places[j]["name"].strip().lower(); bl = best["name"].strip().lower()
            sim = (sl==bl) or (len(sl)>=4 and sl in bl) or (len(bl)>=4 and bl in sl)
            if d < 40 or (d < r and sim):
                merged[j] = True
                if places[j]["rating"] > best["rating"]: best = places[j]
        kept.append(best)
    return kept

def tdesc(s):
    D = {"attraction":"Sightseeing","restaurant":"Dining","cafe":"Coffee & Drinks",
         "park":"Nature & Outdoors","mall":"Shopping","bar":"Nightlife","hotel":"Accommodation"}
    for k, v in D.items():
        if k in str(s).lower(): return v
    return "Local highlight"

# ═══════════════════════════════════════════════════════════════
# GEOCODING
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def _nom(q):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q":q,"format":"json","limit":1},
                         headers={"User-Agent":"VoyagerApp/4.0"}, timeout=9).json()
        if r: return float(r[0]["lat"]), float(r[0]["lon"])
    except: pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def _amap_geo(addr):
    if not AMAP_KEY: return None
    try:
        r = requests.get("https://restapi.amap.com/v3/geocode/geo",
                         params={"key":AMAP_KEY,"address":addr,"output":"json"}, timeout=8).json()
        if str(r.get("status"))=="1" and r.get("geocodes"):
            loc = r["geocodes"][0].get("location","")
            if "," in loc:
                lon, lat = map(float, loc.split(","))
                return lat, lon
    except: pass
    return None

# ═══════════════════════════════════════════════════════════════
# PLACE SEARCH
# ═══════════════════════════════════════════════════════════════
def search_intl(lat, lon, tls, lpt):
    all_p = []
    for tl in tls:
        ok, ov = PTYPES[tl]["osm"]
        q = (f'[out:json][timeout:30];(node["{ok}"="{ov}"](around:6000,{lat},{lon});'
             f'way["{ok}"="{ov}"](around:6000,{lat},{lon}););out center {lpt*3};')
        els = []
        for url in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
            try:
                r = requests.post(url, data={"data":q}, timeout=28).json().get("elements",[])
                if r: els = r; break
            except: continue
        for el in els:
            tags = el.get("tags",{})
            nm = tags.get("name:en") or tags.get("name","")
            if not nm or is_chain(nm): continue
            elat = el.get("lat",0) if el["type"]=="node" else el.get("center",{}).get("lat",0)
            elon = el.get("lon",0) if el["type"]=="node" else el.get("center",{}).get("lon",0)
            if not elat or not elon: continue
            pts = [tags.get(k,"") for k in ["addr:housenumber","addr:street","addr:city"] if tags.get(k)]
            all_p.append({"name":_ss(nm),"lat":elat,"lon":elon,
                          "rating":round(random.uniform(3.8,5.0),1),
                          "address":_ss(", ".join(pts)),"phone":"","website":"",
                          "type":ov,"type_label":tl,
                          "district":_ss(tags.get("addr:suburb","")),"description":tdesc(ov)})
            if len(all_p) >= lpt*len(tls): break
    seen, out = set(), []
    for p in all_p:
        k = (p["name"], round(p["lat"],3), round(p["lon"],3))
        if k not in seen: seen.add(k); out.append(p)
    return out

def _parse_amap(pois, kw, tl, limit, seen):
    out = []
    for p in pois:
        if len(out) >= limit: break
        nm = p.get("name","")
        if not nm or is_chain(nm): continue
        loc = p.get("location","")
        if "," not in (loc or ""): continue
        try: plon, plat = map(float, loc.split(","))
        except: continue
        k = (nm, round(plat,4), round(plon,4))
        if k in seen: continue
        seen.add(k)
        biz = p.get("biz_ext") or {}
        try: rating = float(biz.get("rating") or 0) or 0.0
        except: rating = 0.0
        addr = p.get("address") or ""
        if isinstance(addr, list): addr = "".join(addr)
        out.append({"name":_ss(nm),"lat":plat,"lon":plon,"rating":rating,
                    "address":_ss(str(addr).strip()),"phone":"","website":"",
                    "type":kw,"type_label":tl,"district":"","description":tdesc(kw)})
    return out

def search_cn(lat, lon, tls, lpt):
    all_p = []; seen = set()
    for tl in tls:
        for kw in AMAP_KW.get(tl,[])[:2]:
            try:
                p = {"key":AMAP_KEY,"keywords":kw,"location":f"{lon},{lat}","radius":8000,
                     "offset":20,"page":1,"extensions":"all","output":"json"}
                at = PTYPES.get(tl,{}).get("amap","")
                if at: p["types"] = at
                d = requests.get("https://restapi.amap.com/v3/place/around",params=p,timeout=10).json()
                if str(d.get("status"))=="1":
                    all_p.extend(_parse_amap(d.get("pois") or [],kw,tl,lpt,seen))
            except: pass
    seen2, out = set(), []
    for p in all_p:
        k = (p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen2: seen2.add(k); out.append(p)
    return out

def demo_places(lat, lon, tls, n, seed):
    random.seed(seed)
    NAMES = {"🏛️ Attraction":["Grand Museum","Sky Observatory","Ancient Temple","Art Gallery","Historic Castle","Old Town Square","Royal Palace","Heritage District"],
             "🍜 Restaurant":["The Local Table","Harbour Grill","Garden Restaurant","Night Market Kitchen","Chef's Table","Street Food Lane"],
             "☕ Cafe":["Morning Roast","The Corner Café","Artisan Brew","Rooftop Café","Matcha House"],
             "🌿 Park":["Riverside Park","Botanical Garden","Central Green","Waterfront Promenade"],
             "🛍️ Shopping":["Grand Market","Designer Quarter","Vintage Arcade","Night Bazaar"],
             "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Club"],
             "🏨 Hotel":["Grand Palace Hotel","Boutique Inn","City View Hotel"]}
    centers = [(lat+random.uniform(-.02,.02), lon+random.uniform(-.02,.02)) for _ in range(3)]
    out = []
    for tl in tls:
        nms = list(NAMES.get(tl,["Local Spot"])); random.shuffle(nms)
        for i, nm in enumerate(nms[:n]):
            ci = i%3; clat, clon = centers[ci]
            out.append({"name":nm,"lat":round(clat+random.uniform(-.005,.005),5),
                        "lon":round(clon+random.uniform(-.005,.005),5),
                        "rating":round(random.uniform(4.0,4.9),1),
                        "address":"Sample destination","phone":"","website":"",
                        "type":tl,"type_label":tl,"district":["North","Central","South"][ci],
                        "description":tdesc(tl)})
    return out

@st.cache_data(ttl=180, show_spinner=False)
def fetch_places(clat, clon, cc, is_cn, tls_t, lpt, _seed):
    random.seed(_seed); tls = list(tls_t)
    raw = search_cn(clat,clon,tls,lpt) if is_cn else search_intl(clat,clon,tls,lpt)
    raw = geo_dedup(raw); warn = None
    if not raw:
        raw = demo_places(clat,clon,tls,lpt,_seed)
        warn = "Live data unavailable — showing sample places."
    df = pd.DataFrame(raw)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c] = ""
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.)
    for c in ["name","address","district","description","type_label","type"]: df[c] = df[c].apply(_ss)
    return df.sort_values("rating", ascending=False).reset_index(drop=True), warn

# ═══════════════════════════════════════════════════════════════
# AI MUST-SEE
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_mustsee(city, cc, days, types_t):
    BUILTIN = {
        "tokyo":[{"name":"Senso-ji Temple","type":"🏛️ Attraction","why":"Tokyo's oldest, most atmospheric temple","rating":4.9,"lat":35.7148,"lon":139.7967,"duration_min":60},
                 {"name":"Shibuya Crossing","type":"🏛️ Attraction","why":"World's busiest pedestrian crossing","rating":4.8,"lat":35.6595,"lon":139.7004,"duration_min":20},
                 {"name":"Shinjuku Gyoen","type":"🌿 Park","why":"Stunning imperial garden","rating":4.8,"lat":35.6851,"lon":139.7103,"duration_min":90},
                 {"name":"Tsukiji Outer Market","type":"🍜 Restaurant","why":"Freshest sushi breakfast in the world","rating":4.7,"lat":35.6654,"lon":139.7707,"duration_min":60}],
        "paris":[{"name":"Eiffel Tower","type":"🏛️ Attraction","why":"The icon of Paris — unmissable","rating":4.8,"lat":48.8584,"lon":2.2945,"duration_min":90},
                 {"name":"Louvre Museum","type":"🏛️ Attraction","why":"World's largest art museum","rating":4.8,"lat":48.8606,"lon":2.3376,"duration_min":180},
                 {"name":"Le Marais","type":"🛍️ Shopping","why":"Medieval streets, galleries, falafel","rating":4.7,"lat":48.8566,"lon":2.3522,"duration_min":90}],
        "london":[{"name":"British Museum","type":"🏛️ Attraction","why":"Free world-class museum","rating":4.8,"lat":51.5194,"lon":-0.1270,"duration_min":120},
                  {"name":"Borough Market","type":"🍜 Restaurant","why":"London's best food market","rating":4.7,"lat":51.5055,"lon":-0.0910,"duration_min":60},
                  {"name":"Tower of London","type":"🏛️ Attraction","why":"900 years of royal history","rating":4.7,"lat":51.5081,"lon":-0.0759,"duration_min":90}],
        "bali":[{"name":"Tanah Lot Temple","type":"🏛️ Attraction","why":"Magical clifftop sunset temple","rating":4.8,"lat":-8.6215,"lon":115.0865,"duration_min":90},
                {"name":"Tegallalang Rice Terraces","type":"🌿 Park","why":"Iconic UNESCO-listed terraces","rating":4.7,"lat":-8.4319,"lon":115.2786,"duration_min":60},
                {"name":"Ubud Monkey Forest","type":"🌿 Park","why":"Ancient forest with playful monkeys","rating":4.6,"lat":-8.5188,"lon":115.2587,"duration_min":75}],
        "singapore":[{"name":"Gardens by the Bay","type":"🌿 Park","why":"Futuristic Supertree Grove, free light show","rating":4.9,"lat":1.2816,"lon":103.8636,"duration_min":120},
                     {"name":"Maxwell Food Centre","type":"🍜 Restaurant","why":"Famous Tian Tian chicken rice","rating":4.8,"lat":1.2800,"lon":103.8444,"duration_min":60}],
        "dubai":[{"name":"Burj Khalifa","type":"🏛️ Attraction","why":"World's tallest building, breathtaking views","rating":4.8,"lat":25.1972,"lon":55.2744,"duration_min":90},
                 {"name":"Gold Souk","type":"🛍️ Shopping","why":"Dazzling traditional gold market","rating":4.6,"lat":25.2697,"lon":55.3094,"duration_min":60}],
    }
    if DEEPSEEK_KEY:
        try:
            types = list(types_t)
            prompt = (f"Recommend {min(days*3,10)} must-visit famous places in {city} for a {days}-day trip. "
                      f"Types requested: {', '.join(types[:4])}. Only real, well-known landmarks. "
                      f"Return ONLY a JSON array, no other text. Each object must have: "
                      f"name (English), type (from list above), why (max 8 words), "
                      f"rating (4.0-5.0), lat (decimal number), lon (decimal number), duration_min (integer).")
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":prompt}],
                      "temperature":0.3,"max_tokens":1200}, timeout=18)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                m = re.search(r'\[.*\]', content, re.DOTALL)
                if m:
                    items = json.loads(m.group())
                    if isinstance(items, list) and items:
                        cleaned = [{"name":_ss(it.get("name","")),"type":_ss(it.get("type","🏛️ Attraction")),
                                    "why":_ss(it.get("why","")),"rating":float(it.get("rating",4.5)),
                                    "lat":float(it.get("lat",0)),"lon":float(it.get("lon",0)),
                                    "duration_min":int(it.get("duration_min",60))}
                                   for it in items[:10] if isinstance(it,dict) and it.get("name","")]
                        if cleaned: return cleaned
        except: pass
    cl = city.strip().lower()
    for k, v in BUILTIN.items():
        if k in cl: return v
    return []

# ═══════════════════════════════════════════════════════════════
# MAP
# ═══════════════════════════════════════════════════════════════
def build_map(df, lat, lon, itin, active_day=None, zoom=13):
    if not FOLIUM_OK: return None
    m = folium.Map(location=[lat,lon], zoom_start=zoom, tiles="CartoDB positron")
    vi = {}
    if itin:
        for di,(dk,stops) in enumerate(itin.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops): vi[s.get("name","")] = (di,si+1,dk)
    if itin:
        for di,(dk,stops) in enumerate(itin.items()):
            if not isinstance(stops,list) or len(stops)<2: continue
            if active_day and dk != active_day: continue
            dc = DAY_COLORS[di%len(DAY_COLORS)]
            for si in range(len(stops)-1):
                a, b = stops[si], stops[si+1]
                if not(a.get("lat") and b.get("lat")): continue
                folium.PolyLine([[a["lat"],a["lon"]],[b["lat"],b["lon"]]],
                                color=dc, weight=3, opacity=0.7, dash_array="5 4").add_to(m)
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            v = vi.get(row["name"])
            if active_day and v and v[2] != active_day: continue
            if v:
                di, sn, dk2 = v; color = DAY_COLORS[di%len(DAY_COLORS)]; label = str(sn)
            else:
                if active_day: continue
                color = "#d0c8b8"; label = "·"
            nm = _ss(row.get("name",""))
            dur = est_dur(nm, row.get("type_label",""))
            pop = (f"<div style='font-family:-apple-system,sans-serif;background:white;color:#1a1610;"
                   f"padding:12px;border-radius:12px;min-width:150px;border:1px solid #e8e0d0;"
                   f"box-shadow:0 4px 12px rgba(0,0,0,0.1)'>"
                   f"<b style='font-size:13px'>{nm}</b><br>"
                   f"<span style='color:#b8943a;font-size:11px'>⭐ {row['rating']:.1f} · {fmt_dur(dur)}</span>"
                   f"</div>")
            folium.Marker([row["lat"],row["lon"]],
                popup=folium.Popup(pop, max_width=200), tooltip=nm,
                icon=folium.DivIcon(
                    html=(f'<div style="width:28px;height:28px;border-radius:50%;background:{color};'
                          f'border:2.5px solid white;display:flex;align-items:center;justify-content:center;'
                          f'color:white;font-size:11px;font-weight:700;'
                          f'box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:-apple-system,sans-serif">{label}</div>'),
                    icon_size=(28,28), icon_anchor=(14,14))).add_to(m)
    return m

# ═══════════════════════════════════════════════════════════════
# HTML EXPORT
# ═══════════════════════════════════════════════════════════════
def build_html(itin, city, day_budgets, cc):
    if isinstance(day_budgets,int): day_budgets = [day_budgets]*30
    avg = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 80
    def esc(s): return _ss(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    total_stops = sum(len(v) for v in itin.values() if isinstance(v,list))
    mjs=[]; pjs=[]; mlats=[]; mlons=[]
    for di,(dl,stops) in enumerate(itin.items()):
        if not isinstance(stops,list) or not stops: continue
        c = DAY_COLORS[di%len(DAY_COLORS)]; pc=[]
        for si,s in enumerate(stops):
            la=s.get("lat",0); lo=s.get("lon",0)
            if not la or not lo: continue
            mlats.append(la); mlons.append(lo); pc.append(f"[{la},{lo}]")
            mjs.append(f'{{"lat":{la},"lon":{lo},"n":"{esc(s.get("name",""))}","d":{di+1},"s":{si+1},"c":"{c}"}}')
        if len(pc)>1: pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')
    clat = sum(mlats)/len(mlats) if mlats else 35.
    clon = sum(mlons)/len(mlons) if mlons else 139.
    days_html = ""
    for di,(dl,stops) in enumerate(itin.items()):
        if not isinstance(stops,list) or not stops: continue
        du = day_budgets[di] if di<len(day_budgets) else avg
        c = DAY_COLORS[di%len(DAY_COLORS)]
        tl_stops = build_timeline(stops)
        rows = "".join(
            f"<tr><td>{si+1}</td><td>{esc(s.get('arrive_time',''))}–{esc(s.get('depart_time',''))}</td>"
            f"<td><b>{esc(s.get('name',''))}</b></td><td>{esc(s.get('type_label',''))}</td>"
            f"<td>{fmt_dur(s.get('duration_min',60))}</td><td>{'⭐ '+str(s.get('rating','')) if s.get('rating') else '–'}</td></tr>"
            for si,s in enumerate(tl_stops))
        total_dur = sum(s.get("duration_min",60) for s in tl_stops)
        days_html += (f"<h3 style='color:{c}'>{esc(dl)} — {len(stops)} stops · ~{fmt_dur(total_dur)}</h3>"
                      f"<table><thead><tr><th>#</th><th>Time</th><th>Place</th><th>Type</th><th>Duration</th><th>Rating</th></tr></thead>"
                      f"<tbody>{rows}</tbody></table>")
    return (f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Voyager — {esc(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#fdfcf8;color:#1a1610;max-width:960px;margin:0 auto;padding:32px 24px}}
h1{{font-family:Georgia,serif;font-size:28px;font-weight:400;color:#1a1610;margin:0 0 8px;letter-spacing:-.02em}}
h3{{font-size:14px;font-weight:600;color:#5a5040;margin:24px 0 8px}}
.badge{{display:inline-flex;padding:3px 14px;border-radius:100px;background:rgba(184,148,58,.1);border:1px solid rgba(184,148,58,.3);font-size:11px;color:#8a6c28;font-weight:600;margin-bottom:16px;letter-spacing:.08em;text-transform:uppercase}}
.sum{{background:rgba(184,148,58,.06);border:1px solid rgba(184,148,58,.15);border-radius:12px;padding:12px 18px;font-size:13px;color:#8a6c28;margin-bottom:20px}}
#map{{height:380px;border-radius:16px;margin:20px 0;border:1px solid rgba(0,0,0,.08);box-shadow:0 4px 16px rgba(0,0,0,.08)}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:white;border-radius:12px;overflow:hidden;margin:4px 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
thead tr{{background:rgba(184,148,58,.06)}}
th,td{{padding:8px 14px;border-bottom:1px solid rgba(0,0,0,.06);text-align:left}}
th{{font-weight:600;color:#8a6c28;font-size:10px;text-transform:uppercase;letter-spacing:.06em}}
tr:hover td{{background:#fdf9f2}}
footer{{color:#c0b090;font-size:11px;margin-top:40px;text-align:center;padding-top:20px;border-top:1px solid rgba(0,0,0,.07)}}
</style></head><body>
<div class="badge">✦ Voyager AI Travel Planner</div>
<h1>✈ {esc(city.title())}</h1>
<div class="sum">${sum(day_budgets[:len(itin)])} total &nbsp;·&nbsp; {len(itin)} days &nbsp;·&nbsp; {total_stops} stops &nbsp;·&nbsp; avg ${avg}/day</div>
<div id="map"></div>{days_html}
<footer>Voyager AI Travel Planner &nbsp;·&nbsp; Ctrl+P to save as PDF</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
var m=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',{{attribution:'CartoDB'}}).addTo(m);
[{",".join(mjs)}].forEach(function(mk){{
var ic=L.divIcon({{html:'<div style="width:26px;height:26px;border-radius:50%;background:'+mk.c+';border:2px solid white;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:700;box-shadow:0 2px 8px rgba(0,0,0,0.2)">'+mk.s+'</div>',iconSize:[26,26],iconAnchor:[13,13]}});
L.marker([mk.lat,mk.lon],{{icon:ic}}).bindPopup('<b>Day '+mk.d+' Stop '+mk.s+'</b><br>'+mk.n).addTo(m);
}});
[{",".join(pjs)}].forEach(function(pl){{L.polyline(pl.pts,{{color:pl.c,weight:3,opacity:.7,dashArray:'5 4'}}).addTo(m);}});
</script></body></html>""").encode("utf-8")

# ═══════════════════════════════════════════════════════════════
# AI ASSISTANT
# ═══════════════════════════════════════════════════════════════
def call_ai(messages, city, itin_summary):
    system = (f"You are Voyager, a luxury travel assistant helping plan a trip to {city}. "
              f"Current itinerary: {itin_summary}. Be concise (max 100 words), warm, and specific. "
              f"Give practical, expert advice tailored to {city}.")
    if ANTHROPIC_KEY:
        try:
            resp = requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
                json={"model":"claude-sonnet-4-20250514","max_tokens":250,"system":system,"messages":messages},timeout=20)
            if resp.status_code == 200:
                for block in resp.json().get("content",[]):
                    if block.get("type")=="text": return block["text"]
        except: pass
    if DEEPSEEK_KEY:
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"system","content":system}]+messages,
                      "temperature":0.7,"max_tokens":250}, timeout=15)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except: pass
    TIPS = {
        "tokyo":"Get a Suica card for all transit. Visit Tsukiji before 8am for the best sushi. Avoid crowds at Senso-ji by going at dawn.",
        "paris":"Book Eiffel Tower tickets 6 weeks ahead. Wednesday evenings at Louvre are less crowded. Try lunch menus at bistros — same food, half the price.",
        "london":"Oyster card saves money on the Tube. Most major museums are free. Borough Market is best for a hearty lunch Thursday–Saturday.",
        "bali":"Rent a scooter for flexibility. Visit temples at dawn. Always carry a sarong for temple entry.",
        "dubai":"Book Burj Khalifa sunset slot online in advance. Friday brunches are a must-try Dubai experience.",
        "singapore":"EZ-Link card for MRT. Hawker centres offer incredible food from $3. Book Gardens by the Bay light show viewing spot early.",
    }
    cl = city.strip().lower()
    for k, v in TIPS.items():
        if k in cl: return v
    return f"For {city}: Start mornings at top landmarks before crowds arrive, explore local neighborhoods in the afternoon, and save evenings for dining and nightlife. Always check Google Maps for real-time transit options."

# ═══════════════════════════════════════════════════════════════
# PROGRESS BAR
# ═══════════════════════════════════════════════════════════════
def render_progress(cur):
    lang = st.session_state.get("lang","EN")
    if lang == "ZH":
        steps = [("✦","欢迎"),("◎","目的地"),("◈","偏好"),("◉","总览"),("⊛","每日")]
    else:
        steps = [("✦","Welcome"),("◎","Destination"),("◈","Preferences"),("◉","Overview"),("⊛","Day Detail")]
    html = '<div class="prog-wrap">'
    for i,(icon,label) in enumerate(steps):
        n = i+1
        state = "done" if n<cur else ("active" if n==cur else "pending")
        circle = "✓" if n<cur else icon
        html += f'<div class="prog-step"><div class="prog-dot {state}">{circle}</div><div class="prog-lbl {state}">{label}</div></div>'
        if i < len(steps)-1:
            lc = "done" if n<cur else ""
            html += f'<div class="prog-line {lc}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TOP BAR (lang switch + user)
# ═══════════════════════════════════════════════════════════════
def render_topbar():
    user = _cur_user()
    tc1,tc2,tc3 = st.columns([1,3,1])
    with tc1:
        lang = st.session_state.get("lang","EN")
        lc1,lc2 = st.columns(2)
        with lc1:
            if st.button("EN", key="tb_en", use_container_width=True,
                         type="primary" if lang=="EN" else "secondary"):
                st.session_state["lang"]="EN"; st.rerun()
        with lc2:
            if st.button("中文", key="tb_zh", use_container_width=True,
                         type="primary" if lang=="ZH" else "secondary"):
                st.session_state["lang"]="ZH"; st.rerun()
    with tc2:
        st.markdown(f"""
        <div style="text-align:center;padding:8px 0">
          <span style="font-family:'Playfair Display',Georgia,serif;font-size:18px;font-weight:500;
          color:#5a4020;letter-spacing:0.15em">V O Y A G E R</span>
          <span style="font-size:11px;color:#b0a080;margin-left:8px;letter-spacing:0.06em">{T('tagline')}</span>
        </div>
        """, unsafe_allow_html=True)
    with tc3:
        if user:
            st.markdown(f'<div style="text-align:right;padding:8px 0;font-size:12px;color:#8a6c28;font-weight:500">◉ {user["username"]}</div>', unsafe_allow_html=True)
            if st.button(T("sign_in")[:5]+"out" if st.session_state.get("lang")=="EN" else "退出",
                         key="tb_logout", use_container_width=True):
                try: logout_user(st.session_state.get("_auth_token",""))
                except: pass
                st.session_state.pop("_auth_token",None)
                st.session_state["user_mode"] = None; st.rerun()

    st.markdown('<hr style="border:none;border-top:1px solid rgba(0,0,0,0.07);margin:4px 0 0">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# STEP 1 — WELCOME
# ═══════════════════════════════════════════════════════════════
def step_1():
    render_topbar()
    render_progress(1)
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    _,col,_ = st.columns([1,2,1])
    with col:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:36px">
          <div style="font-family:'Playfair Display',Georgia,serif;font-size:36px;font-weight:400;
          color:#1a1610;letter-spacing:-0.02em;line-height:1.2;margin-bottom:10px">
            {T('welcome_title')}
          </div>
          <div style="font-size:15px;color:#9a8c78;line-height:1.6">{T('welcome_sub')}</div>
        </div>
        """, unsafe_allow_html=True)

        c1,c2 = st.columns(2, gap="medium")
        with c1:
            st.markdown(f"""
            <div style="background:linear-gradient(145deg,rgba(184,148,58,0.06),rgba(184,148,58,0.02));
            border:1px solid rgba(184,148,58,0.22);border-radius:20px;padding:24px;
            text-align:center;min-height:220px">
              <div style="font-size:32px;margin-bottom:12px">◉</div>
              <div style="font-weight:600;font-size:16px;color:#1a1610;margin-bottom:6px">{T('sign_in')}</div>
              <div style="font-size:12px;color:#9a8c78;line-height:1.6">
                {T('wishlist')} · Points<br>Saved trips · {T('collab')}
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if AUTH_OK:
                with st.form("login_form"):
                    st.text_input(T("sign_in"), placeholder=T("username_ph"), key="li_u", label_visibility="collapsed")
                    st.text_input(T("password_ph"), placeholder=T("password_ph"), type="password", key="li_p", label_visibility="collapsed")
                    submitted = st.form_submit_button(T("sign_in"), use_container_width=True)
                    if submitted:
                        u = st.session_state.get("li_u","").strip()
                        p = st.session_state.get("li_p","")
                        if u and p:
                            ok, msg, tok = login_user(u, p)
                            if ok:
                                st.session_state["_auth_token"] = tok
                                st.session_state["user_mode"] = "logged_in"
                                if POINTS_OK:
                                    try: add_points(u,"daily_login")
                                    except: pass
                                st.session_state["step"] = 2; st.rerun()
                            else: st.error(msg)
                        else: st.warning(T("username_ph"))

                with st.expander(T("register"), expanded=False):
                    with st.form("reg_form"):
                        st.text_input(T("reg_user_ph"), placeholder=T("reg_user_ph"), key="re_u", label_visibility="collapsed")
                        st.text_input(T("email_ph"), placeholder=T("email_ph"), key="re_e", label_visibility="collapsed")
                        st.text_input(T("reg_pass_ph"), placeholder=T("reg_pass_ph"), type="password", key="re_p", label_visibility="collapsed")
                        if st.form_submit_button(T("register"), use_container_width=True):
                            ok, msg = register_user(st.session_state.get("re_u","").strip(),
                                                     st.session_state.get("re_p",""),
                                                     st.session_state.get("re_e","").strip())
                            (st.success if ok else st.error)(msg)
            else:
                if st.button(T("sign_in"), use_container_width=True, type="primary"):
                    st.session_state["user_mode"]="logged_in"; st.session_state["step"]=2; st.rerun()

        with c2:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.7);border:1px solid rgba(0,0,0,0.08);
            border-radius:20px;padding:24px;text-align:center;min-height:220px">
              <div style="font-size:32px;margin-bottom:12px">◎</div>
              <div style="font-weight:600;font-size:16px;color:#1a1610;margin-bottom:6px">{T('guest')}</div>
              <div style="font-size:12px;color:#9a8c78;line-height:2">
                {"<br>".join("✦ " + f for f in T("guest_features"))}
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button(T("guest"), key="guest_btn", use_container_width=True, type="primary"):
                st.session_state["user_mode"]="guest"; st.session_state["step"]=2; st.rerun()

# ═══════════════════════════════════════════════════════════════
# STEP 2 — DESTINATION
# ═══════════════════════════════════════════════════════════════
def step_2():
    render_topbar()
    render_progress(2)
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    _,col,_ = st.columns([1,3,1])
    with col:
        st.markdown(f'<div class="page-title">{T("where_title")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="page-sub">{T("where_sub")}</div>', unsafe_allow_html=True)

        c1,c2 = st.columns([3,2], gap="small")
        with c1:
            city_ov = st.text_input(T("where_title"), placeholder=T("search_city_ph"),
                                     value="", key="s2_ov", label_visibility="collapsed")
        with c2:
            all_countries = [""] + sorted(WORLD_CITIES.keys())
            prev_cc = st.session_state.get("dest_country","")
            sel_cc = st.selectbox(T("country_label"), all_countries,
                                   index=all_countries.index(prev_cc) if prev_cc in all_countries else 0,
                                   key="s2_cc")

        # City grid
        st.markdown(f'<span class="section-label">{T("popular")}</span>', unsafe_allow_html=True)

        if sel_cc and not city_ov:
            cities = WORLD_CITIES.get(sel_cc, [])
            cur_city = st.session_state.get("dest_city","")
            rows = [cities[i:i+4] for i in range(0,len(cities),4)]
            for row in rows:
                cols = st.columns(len(row))
                for ci,city in enumerate(row):
                    with cols[ci]:
                        sel = (city == cur_city)
                        if st.button(("✓ " if sel else "")+city, key=f"cp_{city}",
                                     use_container_width=True, type="primary" if sel else "secondary"):
                            st.session_state["dest_city"] = city
                            st.session_state["dest_country"] = sel_cc; st.rerun()
        else:
            page = st.session_state.get("popular_page",0)
            page_size = 12
            chunk = POPULAR[page*page_size:(page+1)*page_size]
            if not chunk: chunk = POPULAR[:page_size]
            rows = [chunk[i:i+4] for i in range(0,len(chunk),4)]
            for row in rows:
                cols = st.columns(len(row))
                for ci,(icon,city,country) in enumerate(row):
                    with cols[ci]:
                        sel = (city == st.session_state.get("dest_city",""))
                        if st.button(f"{icon} {city}", key=f"pop_{city}_{page}",
                                     use_container_width=True, type="primary" if sel else "secondary"):
                            st.session_state["dest_city"] = city
                            st.session_state["dest_country"] = country; st.rerun()
            rc,_ = st.columns([1,3])
            with rc:
                if st.button(T("more_cities"), key="pop_more", use_container_width=True):
                    st.session_state["popular_page"] = (page+1) % (len(POPULAR)//page_size+1); st.rerun()

        # Selected indicator
        final_city = city_ov.strip() or st.session_state.get("dest_city","")
        if final_city:
            cc_name = sel_cc or st.session_state.get("dest_country","")
            st.markdown(f"""
            <div style="margin:20px 0 0;padding:14px 18px;
            background:linear-gradient(135deg,rgba(184,148,58,0.08),rgba(184,148,58,0.04));
            border:1px solid rgba(184,148,58,0.25);border-radius:14px;
            display:flex;align-items:center;gap:12px">
              <span style="font-size:22px">✈️</span>
              <div>
                <div style="font-weight:600;font-size:16px;color:#1a1610">{final_city}</div>
                <div style="font-size:12px;color:#b8943a">{cc_name}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        nc1,nc2 = st.columns(2, gap="small")
        with nc1:
            if st.button(T("back"), key="s2_back", use_container_width=True):
                st.session_state["step"]=1; st.rerun()
        with nc2:
            if st.button(T("next"), key="s2_next", use_container_width=True, type="primary"):
                fc = final_city
                if not fc: st.warning(T("search_city_ph")); return
                ck = fc.strip().lower()
                cc_name = sel_cc or st.session_state.get("dest_country","")
                cc = COUNTRY_CODES.get(cc_name,"INT")
                is_cn = ck in CN_CITIES
                intl = INTL_CITIES.get(ck)
                if is_cn: lat,lon = CN_CITIES[ck]
                elif intl: lat,lon,cc = intl[0],intl[1],intl[2]
                else:
                    with st.spinner(T("locating")):
                        coord = _nom(fc)
                        if not coord: st.error(f"Cannot find '{fc}'. Try a different spelling."); return
                        lat,lon = coord
                st.session_state.update({"dest_city":fc,"dest_country":cc_name,
                    "dest_lat":lat,"dest_lon":lon,"dest_cc":cc,"dest_is_cn":is_cn})
                st.session_state["step"]=3; st.rerun()

# ═══════════════════════════════════════════════════════════════
# STEP 3 — PREFERENCES
# ═══════════════════════════════════════════════════════════════
def step_3():
    render_topbar()
    render_progress(3)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    city = st.session_state.get("dest_city","")
    cc = st.session_state.get("dest_cc","INT")

    _,col,_ = st.columns([1,3,1])
    with col:
        st.markdown(f'<div class="page-title">{T("pref_title")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="page-sub">{T("pref_sub")}</div>', unsafe_allow_html=True)

        # ── Row 1: Duration + Budget ──
        ga,gb = st.columns(2, gap="medium")
        with ga:
            days = st.number_input(T("duration"), min_value=1, max_value=10,
                                    value=st.session_state.get("trip_days",3), step=1, key="s3_days")
        with gb:
            base_budget = st.slider(T("base_budget"), 20, 500,
                                     st.session_state.get("trip_budget",100), 5, format="$%d", key="s3_budget")
            sym,rate = local_rate(cc)
            st.markdown(f'<div style="font-size:11px;color:#b8943a;margin-top:2px">${base_budget} ≈ {sym}{round(base_budget*rate):,} per day</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── Row 2: Interests ──
        st.markdown(f'<span class="section-label">{T("interests")}</span>', unsafe_allow_html=True)
        sel_types = list(st.session_state.get("trip_types",["🏛️ Attraction","🍜 Restaurant"]))
        type_list = list(PTYPES.keys())
        rows_t = [type_list[i:i+4] for i in range(0,len(type_list),4)]
        for row in rows_t:
            tcols = st.columns(len(row))
            for tci,tl in enumerate(row):
                with tcols[tci]:
                    is_sel = tl in sel_types
                    if st.button(("✓ " if is_sel else "")+tl, key=f"tp_{tl}",
                                 use_container_width=True, type="primary" if is_sel else "secondary"):
                        if is_sel and len(sel_types)>1: sel_types.remove(tl)
                        elif not is_sel: sel_types.append(tl)
                        st.session_state["trip_types"] = sel_types; st.rerun()

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── Row 3: Must-visit places ──
        st.markdown(f'<span class="section-label">{T("must_visit")}</span>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;color:#9a8c78;margin-bottom:10px">{T("must_visit_sub")}</div>', unsafe_allow_html=True)

        custom_places = list(st.session_state.get("custom_places",[]))
        for ci,cp in enumerate(custom_places):
            cc1,cc2 = st.columns([5,1])
            with cc1:
                st.markdown(f"""
                <div style="padding:10px 14px;background:linear-gradient(135deg,rgba(184,148,58,0.06),rgba(184,148,58,0.02));
                border:1px solid rgba(184,148,58,0.2);border-radius:10px;font-size:13px;color:#5a4020;
                display:flex;align-items:center;gap:8px">
                  <span>📍</span> <span style="font-weight:500">{_ss(cp.get("name",""))}</span>
                </div>""", unsafe_allow_html=True)
            with cc2:
                if st.button("✕", key=f"rm_cp_{ci}", use_container_width=True):
                    custom_places.pop(ci); st.session_state["custom_places"]=custom_places; st.rerun()

        np1,np2 = st.columns([4,1], gap="small")
        with np1:
            new_place = st.text_input(T("must_visit"), placeholder=T("add_place_ph"),
                                       key="new_cp", label_visibility="collapsed")
        with np2:
            if st.button(T("add"), key="add_cp_btn", use_container_width=True, type="primary"):
                if new_place.strip():
                    custom_places.append({"name":new_place.strip(),"lat":0,"lon":0,
                                           "type_label":"🏛️ Attraction","rating":5.0,
                                           "address":"","district":"Custom","description":"User added"})
                    st.session_state["custom_places"] = custom_places; st.rerun()

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── Row 4: Per-day settings ──
        st.markdown(f'<span class="section-label">{T("per_day")}</span>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;color:#9a8c78;margin-bottom:12px">{T("per_day_sub")}</div>', unsafe_allow_html=True)

        int_days = int(days)
        day_configs = dict(st.session_state.get("day_configs",{}))
        dtabs = st.tabs([f"Day {d+1}" for d in range(int_days)])
        for di,dtab in enumerate(dtabs):
            with dtab:
                dk = f"Day {di+1}"
                cfg = day_configs.get(dk, {"budget":int(base_budget),"quotas":{}})
                d_bud = st.slider(f"{T('budget_label')} — Day {di+1}", 20, 500,
                                   int(cfg.get("budget",base_budget)), 5, format="$%d", key=f"d_bud_{di}")
                st.markdown(f'<span class="section-label" style="margin-top:10px;display:block">{T("stops_per_type")}</span>', unsafe_allow_html=True)
                quotas = {}
                q_cols = st.columns(min(len(sel_types),4))
                for tci,tl in enumerate(sel_types):
                    with q_cols[tci%len(q_cols)]:
                        prev_q = cfg.get("quotas",{}).get(tl,1)
                        n = st.number_input(tl, 0, 5, int(prev_q), 1, key=f"q_{di}_{tl}")
                        if n > 0: quotas[tl] = n
                if not quotas and sel_types: quotas = {sel_types[0]:1}
                day_configs[dk] = {"budget":d_bud,"quotas":quotas}

        # ── Optional logistics ──
        with st.expander(T("optional_logistics"), expanded=False):
            ol1,ol2 = st.columns(2, gap="small")
            with ol1:
                st.text_input(T("start_ph"), placeholder=T("start_ph"), key="s3_dep", label_visibility="visible")
                st.text_input(T("hotel_ph"), placeholder=T("hotel_ph"), key="s3_hotel", label_visibility="visible")
            with ol2:
                st.text_input(T("end_ph"), placeholder=T("end_ph"), key="s3_arr", label_visibility="visible")

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        nc1,nc2 = st.columns(2, gap="small")
        with nc1:
            if st.button(T("back"), key="s3_back", use_container_width=True):
                st.session_state["step"]=2; st.rerun()
        with nc2:
            if st.button(T("build"), key="s3_next", use_container_width=True, type="primary"):
                if not sel_types: st.warning(T("interests")); return
                st.session_state["trip_days"] = int_days
                st.session_state["trip_budget"] = int(base_budget)
                st.session_state["trip_types"] = sel_types
                st.session_state["day_configs"] = day_configs
                st.session_state["trip_depart"] = st.session_state.get("s3_dep","")
                st.session_state["trip_arrive"] = st.session_state.get("s3_arr","")
                st.session_state["trip_hotel"]  = st.session_state.get("s3_hotel","")
                _generate_itinerary()

# ═══════════════════════════════════════════════════════════════
# GENERATE ITINERARY
# ═══════════════════════════════════════════════════════════════
def _generate_itinerary():
    city  = st.session_state["dest_city"]
    lat   = st.session_state["dest_lat"]
    lon   = st.session_state["dest_lon"]
    cc    = st.session_state["dest_cc"]
    is_cn = st.session_state.get("dest_is_cn",False)
    ndays = st.session_state["trip_days"]
    day_configs = st.session_state.get("day_configs",{})
    custom_places = st.session_state.get("custom_places",[])

    day_quotas = []; day_budgets = []
    for d in range(ndays):
        dk = f"Day {d+1}"; cfg = day_configs.get(dk,{})
        day_budgets.append(int(cfg.get("budget", st.session_state.get("trip_budget",100))))
        q = cfg.get("quotas",{})
        if not q: q = {st.session_state.get("trip_types",["🏛️ Attraction"])[0]:1}
        day_quotas.append(q)

    sel_types = st.session_state.get("trip_types",["🏛️ Attraction"])
    total_q = sum(sum(q.values()) for q in day_quotas)
    lpt = max(20, total_q*5)

    with st.spinner(f"{T('discovering')} in {city}…"):
        try:
            df,warn = fetch_places(lat,lon,cc,is_cn,tuple(sel_types),lpt,st.session_state.get("seed",42))
        except Exception as e: st.error(f"Search error: {e}"); return

    if warn: st.info(warn)
    if df is None or df.empty: st.error("No places found. Try another city."); return

    # Inject custom places
    if custom_places:
        cp_rows = []
        for cp in custom_places:
            if not cp.get("lat"):
                with st.spinner(f"{T('locating')} {cp['name']}…"):
                    coord = _nom(f"{cp['name']} {city}") or _nom(cp["name"])
                    if coord: cp["lat"],cp["lon"] = coord[0],coord[1]
                    else: cp["lat"]=lat+random.uniform(-.01,.01); cp["lon"]=lon+random.uniform(-.01,.01)
            cp_rows.append(cp)
        cp_df = pd.DataFrame(cp_rows)
        for c in df.columns:
            if c not in cp_df.columns: cp_df[c] = ""
        cp_df["rating"] = 5.0
        df = pd.concat([cp_df, df], ignore_index=True)

    def _gc(addr):
        if not addr: return None
        if is_cn: return _amap_geo(f"{addr} {city}") or _nom(f"{addr} {city}")
        return _nom(f"{addr} {city}") or _nom(addr)

    hotel_c = depart_c = arrive_c = None
    with st.spinner(T("locating")):
        hotel_c  = _gc(st.session_state.get("trip_hotel",""))
        depart_c = _gc(st.session_state.get("trip_depart",""))
        arrive_c = _gc(st.session_state.get("trip_arrive",""))

    itin = {}
    if AI_OK:
        with st.spinner(T("crafting")):
            try:
                itin = generate_itinerary(df, ndays, day_quotas,
                    hotel_lat=hotel_c[0] if hotel_c else None, hotel_lon=hotel_c[1] if hotel_c else None,
                    depart_lat=depart_c[0] if depart_c else None, depart_lon=depart_c[1] if depart_c else None,
                    arrive_lat=arrive_c[0] if arrive_c else None, arrive_lon=arrive_c[1] if arrive_c else None,
                    day_min_ratings=[3.5]*ndays, day_anchor_lats=[lat]*ndays, day_anchor_lons=[lon]*ndays,
                    country=cc, city=city, day_budgets=day_budgets)
            except Exception as e: st.error(f"Itinerary error: {e}")

    if not itin:
        used = set()
        for d in range(ndays):
            dk = f"Day {d+1}"; stops = []; q = day_quotas[d]
            for tl,cnt in q.items():
                pool = df[(df["type_label"]==tl)&(~df["name"].isin(used))].head(cnt)
                for _,row in pool.iterrows(): stops.append(row.to_dict()); used.add(row["name"])
            itin[dk] = stops

    # Inject custom places if missing
    if custom_places:
        in_itin = {s.get("name","") for sl in itin.values() if isinstance(sl,list) for s in sl}
        missing = [cp for cp in custom_places if cp["name"] not in in_itin]
        for cp in missing:
            d1 = list(itin.keys())[0] if itin else "Day 1"
            itin.setdefault(d1,[]).insert(0,{**cp,"time_slot":"TBD","transport_to_next":None})

    st.session_state["_itin"] = itin
    st.session_state["_df"] = df
    st.session_state["day_budgets"] = day_budgets
    st.session_state["active_day"] = None
    st.session_state["ai_chat"] = []

    user = _cur_user()
    if user:
        _save_itin(user["username"], itin, city, city.title())
        if POINTS_OK:
            try: add_points(user["username"],"share",note=city)
            except: pass

    st.session_state["step"] = 4; st.rerun()

# ═══════════════════════════════════════════════════════════════
# STEP 4 — OVERVIEW
# ═══════════════════════════════════════════════════════════════
def step_4():
    render_topbar()
    render_progress(4)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    city       = st.session_state.get("dest_city","")
    cc         = st.session_state.get("dest_cc","INT")
    lat        = st.session_state.get("dest_lat",35.)
    lon        = st.session_state.get("dest_lon",139.)
    ndays      = st.session_state.get("trip_days",3)
    day_budgets= st.session_state.get("day_budgets",[100]*ndays)
    itin       = st.session_state.get("_itin",{})
    df         = st.session_state.get("_df",pd.DataFrame())
    user       = _cur_user()

    total_stops = sum(len(v) for v in itin.values() if isinstance(v,list))
    avg_r = df["rating"].replace(0,float("nan")).mean() if df is not None and not df.empty else 0

    _,main,_ = st.columns([1,5,1])
    with main:
        # Header
        hc1,hc2 = st.columns([3,2], gap="medium")
        with hc1:
            st.markdown(f"""
            <div>
              <span class="section-label">{T("overview_title")}</span>
              <div style="font-family:'Playfair Display',Georgia,serif;font-size:28px;font-weight:500;
              color:#1a1610;letter-spacing:-0.02em">{city.title()}</div>
              <div style="font-size:13px;color:#9a8c78;margin-top:4px">
                {ndays} {T("days_unit")} · {total_stops} {T("stops_unit")} · {T("avg_day")} ${round(sum(day_budgets)/len(day_budgets)) if day_budgets else 0}
              </div>
            </div>""", unsafe_allow_html=True)
        with hc2:
            a1,a2 = st.columns(2, gap="small")
            with a1:
                if st.button(T("edit_prefs"), key="s4_back", use_container_width=True):
                    st.session_state["step"]=3; st.rerun()
                if st.button(T("shuffle"), key="s4_shuf", use_container_width=True):
                    st.session_state["seed"]=random.randint(1,99999)
                    st.cache_data.clear(); _generate_itinerary()
            with a2:
                if user:
                    if st.button(T("save"), key="s4_save", use_container_width=True):
                        _save_itin(user["username"],itin,city,city.title())
                        st.toast(f"Saved {city.title()}!")
                if itin:
                    try:
                        hd = build_html(itin,city,day_budgets,cc)
                        st.download_button(T("export"), data=hd,
                            file_name=f"voyager_{city.lower().replace(' ','_')}.html",
                            mime="text/html;charset=utf-8", use_container_width=True)
                    except: pass

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Metrics
        m1,m2,m3,m4 = st.columns(4)
        m1.metric(T("days_unit").upper(), str(ndays))
        m2.metric(T("stops_unit").upper(), str(total_stops))
        m3.metric("AVG ⭐", f"{avg_r:.1f}" if avg_r else "—")
        m4.metric(T("est").upper(), f"${sum(day_budgets)}")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Overview map (compact)
        map_col,days_col = st.columns([2,3], gap="medium")

        with map_col:
            st.markdown(f'<span class="section-label">Overview Map</span>', unsafe_allow_html=True)
            if FOLIUM_OK and df is not None and not df.empty:
                m = build_map(df,lat,lon,itin,active_day=None,zoom=12)
                if m:
                    st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
                    st_folium(m, width="100%", height=300, returned_objects=[])
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Install streamlit-folium for maps.")

        with days_col:
            st.markdown(f'<span class="section-label">{T("tap_day")}</span>', unsafe_allow_html=True)
            for di,(dk,stops) in enumerate(itin.items()):
                if not isinstance(stops,list): continue
                color = DAY_COLORS[di%len(DAY_COLORS)]
                d_bud = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
                tl_stops = build_timeline(stops)
                total_dur = sum(s.get("duration_min",60) for s in tl_stops)
                type_counts = {}
                for s in stops: t=s.get("type_label",""); type_counts[t]=type_counts.get(t,0)+1
                preview = " · ".join(_ss(s.get("name",""))[:20] for s in stops[:3])
                if len(stops)>3: preview += f" +{len(stops)-3}"

                dc1,dc2 = st.columns([4,1], gap="small")
                with dc1:
                    st.markdown(f"""
                    <div style="background:white;border:1px solid rgba(0,0,0,0.07);
                    border-left:3px solid {color};border-radius:14px;
                    padding:14px 16px;margin:5px 0;box-shadow:0 1px 6px rgba(0,0,0,0.05)">
                      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                        <div style="width:28px;height:28px;border-radius:50%;background:{color};
                        display:flex;align-items:center;justify-content:center;
                        font-size:12px;font-weight:700;color:white;flex-shrink:0">{di+1}</div>
                        <div>
                          <span style="font-weight:600;font-size:14px;color:#1a1610">{dk}</span>
                          <span style="font-size:11px;color:#9a8c78;margin-left:8px">{len(stops)} stops · ${d_bud}/day · ~{fmt_dur(total_dur)}</span>
                        </div>
                      </div>
                      <div style="font-size:12px;color:#9a8c78;line-height:1.5">{preview}</div>
                    </div>""", unsafe_allow_html=True)
                with dc2:
                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                    if st.button(T("plan_day"), key=f"open_{dk}", use_container_width=True, type="primary"):
                        st.session_state["active_day"] = dk
                        st.session_state["step"] = 5; st.rerun()

        # Wishlist
        if user:
            wl = _wl_get_fn(user["username"])
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            with st.expander(f"♥ {T('wishlist')} ({len(wl)})", expanded=False):
                if not wl:
                    st.markdown(f'<div style="font-size:13px;color:#9a8c78;padding:8px">{T("add_here")} — add places from Day Detail view</div>', unsafe_allow_html=True)
                else:
                    day_keys = list(itin.keys())
                    for wi,wp in enumerate(wl):
                        wc1,wc2,wc3,wc4 = st.columns([3,2,1,1], gap="small")
                        with wc1:
                            st.markdown(f'<div style="font-size:13px;font-weight:500;color:#1a1610;padding:6px 0">📍 {_ss(wp.get("name",""))}</div>', unsafe_allow_html=True)
                        with wc2:
                            sel_wl = st.selectbox("",["add to…"]+day_keys,key=f"wl_dd_{wi}",label_visibility="collapsed")
                        with wc3:
                            if sel_wl!="add to…" and st.button(T("add_here"),key=f"wl_add_{wi}",use_container_width=True,type="primary"):
                                stops_list = list(itin.get(sel_wl,[]))
                                nm = wp.get("name","")
                                if nm not in {s.get("name","") for s in stops_list}:
                                    stops_list.append({**wp,"time_slot":"TBD","transport_to_next":None})
                                    new_itin = dict(itin); new_itin[sel_wl] = stops_list
                                    st.session_state["_itin"] = new_itin
                                    st.toast(f"Added {nm}!"); st.rerun()
                        with wc4:
                            if st.button("✕",key=f"wl_rm_{wi}",use_container_width=True):
                                _wl_rm_fn(user["username"],wp.get("name","")); st.rerun()

        # Collab
        if AUTH_OK and user:
            with st.expander(f"🤝 {T('collab')}", expanded=False):
                st.markdown(f'<div style="font-size:12px;color:#9a8c78;margin-bottom:12px">{T("collab_sub")}</div>', unsafe_allow_html=True)
                cb1,cb2 = st.columns(2, gap="medium")
                with cb1:
                    if st.button(T("gen_code"), use_container_width=True, type="primary"):
                        import uuid
                        try:
                            tok = create_collab_link(user["username"],str(uuid.uuid4())[:8])
                            st.session_state["collab_code"] = tok
                        except Exception as e: st.error(str(e))
                    if st.session_state.get("collab_code"):
                        st.markdown(f'<div class="collab-code">{st.session_state["collab_code"]}</div>', unsafe_allow_html=True)
                with cb2:
                    jc = st.text_input(T("join_code"), placeholder=T("join_code_ph"), key="jc_input")
                    if st.button(T("join"), use_container_width=True) and jc:
                        try:
                            ok,msg = join_collab(user["username"],jc.upper())
                            (st.success if ok else st.error)(msg)
                        except Exception as e: st.error(str(e))

    _render_ai_bubble()

# ═══════════════════════════════════════════════════════════════
# STEP 5 — DAY DETAIL
# ═══════════════════════════════════════════════════════════════
def step_5():
    render_topbar()
    render_progress(5)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    dk          = st.session_state.get("active_day","Day 1")
    city        = st.session_state.get("dest_city","")
    cc          = st.session_state.get("dest_cc","INT")
    lat         = st.session_state.get("dest_lat",35.)
    lon         = st.session_state.get("dest_lon",139.)
    itin        = dict(st.session_state.get("_itin",{}))
    df          = st.session_state.get("_df",pd.DataFrame())
    day_budgets = st.session_state.get("day_budgets",[100])
    user        = _cur_user()

    all_days = list(itin.keys())
    di = all_days.index(dk) if dk in all_days else 0
    color = DAY_COLORS[di%len(DAY_COLORS)]
    d_bud = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
    stops = list(itin.get(dk,[]))

    _,main,_ = st.columns([1,5,1])
    with main:
        # Nav row
        nc1,nc2,nc3 = st.columns([2,3,2], gap="small")
        with nc1:
            if st.button(T("back"), key="s5_back", use_container_width=True):
                # Save current state before leaving
                itin[dk] = stops; st.session_state["_itin"] = itin
                st.session_state["step"]=4; st.rerun()
        with nc2:
            st.markdown(f"""
            <div style="text-align:center;padding:6px 0">
              <div style="font-weight:600;font-size:18px;color:#1a1610">{dk}</div>
              <div style="font-size:12px;color:#b8943a">{city.title()}</div>
            </div>""", unsafe_allow_html=True)
        with nc3:
            sel_dk = st.selectbox("", all_days, index=di, key="day_sw", label_visibility="collapsed")
            if sel_dk != dk:
                itin[dk] = stops; st.session_state["_itin"] = itin
                st.session_state["active_day"] = sel_dk; st.rerun()

        # Budget bar
        sym,rate = local_rate(cc)
        total_est = sum(max(COST_FL.get(s.get("type_label",""),2),
                            d_bud*COST_W.get(s.get("type_label",""),.12)/2) for s in stops)
        pct = min(100, round(total_est/d_bud*100)) if d_bud>0 else 0
        bar_c = "#c0392b" if pct>100 else "#b8943a"
        st.markdown(f"""
        <div style="background:white;border:1px solid rgba(0,0,0,0.07);border-radius:14px;
        padding:14px 18px;margin:10px 0;box-shadow:0 1px 6px rgba(0,0,0,0.05)">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:13px;font-weight:500;color:#5a5040">{T('budget_label')}</span>
            <span style="font-size:13px;color:{bar_c};font-weight:600">~${round(total_est)} / ${d_bud}</span>
          </div>
          <div class="bud-bar-wrap">
            <div class="bud-bar-fill" style="width:{pct}%;background:{bar_c}"></div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Main split: list | map
        list_col,map_col = st.columns([1,1], gap="medium")
        tl_stops = build_timeline(stops)

        with list_col:
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
              <span class="section-label" style="margin:0">{T('schedule')} · {len(stops)} stops · ~{fmt_dur(sum(s.get("duration_min",60) for s in tl_stops))}</span>
              <span style="font-size:11px;color:#c0b090">{T('reorder_hint')}</span>
            </div>""", unsafe_allow_html=True)

            for si,s in enumerate(tl_stops):
                nm   = _ss(s.get("name",""))
                tl   = _ss(s.get("type_label",""))
                rat  = s.get("rating",0)
                arr  = s.get("arrive_time","")
                dep  = s.get("depart_time","")
                dur  = s.get("duration_min",60)
                tr   = s.get("transport_to_next") or {}
                cs   = cost_est(tl, d_bud, cc)
                is_custom = s.get("district","")=="Custom"

                sc1,sc2,sc3 = st.columns([1,6,1], gap="small")
                with sc1:
                    # Move up/down
                    if si > 0:
                        if st.button("↑", key=f"up5_{dk}_{si}", use_container_width=True):
                            stops[si],stops[si-1] = stops[si-1],stops[si]
                            itin[dk]=stops; st.session_state["_itin"]=itin; st.rerun()
                    if si < len(stops)-1:
                        if st.button("↓", key=f"dn5_{dk}_{si}", use_container_width=True):
                            stops[si],stops[si+1] = stops[si+1],stops[si]
                            itin[dk]=stops; st.session_state["_itin"]=itin; st.rerun()

                with sc2:
                    custom_tag = f'<span class="tag-gold" style="font-size:10px;padding:2px 8px;margin-left:6px">custom</span>' if is_custom else ""
                    transport_html = f'<div style="margin-top:5px"><span class="tag-transport">🚇 {_ss(tr.get("mode",""))} · {_ss(tr.get("duration",""))}</span></div>' if tr else ""
                    st.markdown(f"""
                    <div style="background:white;border:1px solid rgba(0,0,0,0.07);
                    border-left:3px solid {color};border-radius:12px;
                    padding:12px 14px;margin:3px 0;box-shadow:0 1px 4px rgba(0,0,0,0.05)">
                      <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">
                        <div style="width:24px;height:24px;border-radius:50%;background:{color};flex-shrink:0;
                        display:flex;align-items:center;justify-content:center;
                        font-size:11px;font-weight:700;color:white">{si+1}</div>
                        <span style="font-weight:600;font-size:14px;color:#1a1610">{nm}</span>{custom_tag}
                      </div>
                      <div style="font-size:12px;color:#9a8c78">{tl}{'&nbsp;·&nbsp;⭐ '+str(rat) if rat else ''}</div>
                      <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:5px;align-items:center">
                        {'<span class="tag-time">⏰ '+arr+'–'+dep+'</span>' if arr else ''}
                        <span style="font-size:11px;color:#b8943a">⏱ {fmt_dur(dur)}</span>
                        <span style="font-size:11px;color:#9a8c78">💰 {cs}</span>
                      </div>
                      {transport_html}
                    </div>""", unsafe_allow_html=True)

                with sc3:
                    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"rm5_{dk}_{si}", use_container_width=True):
                        stops.pop(si); itin[dk]=stops
                        st.session_state["_itin"]=itin; st.rerun()
                    if user:
                        saved = _wl_chk_fn(user["username"],nm)
                        if st.button("♥" if saved else "♡", key=f"wl5_{dk}_{si}", use_container_width=True):
                            if saved: _wl_rm_fn(user["username"],nm); st.toast("Removed")
                            else:
                                _wl_add_fn(user["username"],{"name":nm,"lat":s.get("lat",0),"lon":s.get("lon",0),"type_label":tl,"rating":rat,"address":s.get("address","")})
                                st.toast("Saved ♥")
                            st.rerun()
                    sw_key = f"_sw5_{dk}_{si}"
                    if st.button(T("swap"), key=f"sw5b_{dk}_{si}", use_container_width=True):
                        st.session_state[sw_key] = not st.session_state.get(sw_key,False); st.rerun()

                if st.session_state.get(f"_sw5_{dk}_{si}",False):
                    _render_swap(itin,df,dk,si,cc,d_bud)

                st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)

            # Add place
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            with st.expander(f"+ {T('add_to_day')}", expanded=False):
                a1,a2 = st.columns([4,1], gap="small")
                with a1:
                    add_nm = st.text_input(T("add_to_day"), placeholder=T("add_name_ph"),
                                            key=f"add_{dk}_nm", label_visibility="collapsed")
                with a2:
                    if st.button(T("add"), key=f"add_{dk}_go", use_container_width=True, type="primary"):
                        if add_nm.strip():
                            coord = None
                            with st.spinner(T("locating")):
                                coord = _nom(f"{add_nm.strip()} {city}") or _nom(add_nm.strip())
                            new_stop = {"name":add_nm.strip(),
                                        "lat":coord[0] if coord else lat+random.uniform(-.01,.01),
                                        "lon":coord[1] if coord else lon+random.uniform(-.01,.01),
                                        "type_label":"🏛️ Attraction","rating":4.5,
                                        "address":"","district":"Custom","description":"User added",
                                        "time_slot":"TBD","transport_to_next":None}
                            stops.append(new_stop)
                            itin[dk] = stops; st.session_state["_itin"] = itin
                            st.toast(f"Added {add_nm}!"); st.rerun()

                if df is not None and not df.empty:
                    in_day = {s.get("name","") for s in stops}
                    avail = df[~df["name"].isin(in_day)].head(30)
                    if not avail.empty:
                        st.markdown(f'<div style="font-size:12px;color:#9a8c78;margin:10px 0 6px">{T("or_discover")}</div>', unsafe_allow_html=True)
                        sel_place = st.selectbox("", ["–"]+list(avail["name"]), key=f"add_{dk}_sel", label_visibility="collapsed")
                        if sel_place != "–":
                            row = avail[avail["name"]==sel_place].iloc[0]
                            if st.button(f"+ {sel_place[:28]}", key=f"add_{dk}_sel_go", use_container_width=True, type="primary"):
                                stops.append({**row.to_dict(),"time_slot":"TBD","transport_to_next":None})
                                itin[dk]=stops; st.session_state["_itin"]=itin
                                st.toast(f"Added!"); st.rerun()

        with map_col:
            st.markdown(f'<span class="section-label">{T("day_map")} — {dk}</span>', unsafe_allow_html=True)
            if FOLIUM_OK:
                # Rebuild df to include any newly added stops
                all_stops = list(itin.get(dk,[]))
                extra_rows = []
                if df is not None and not df.empty:
                    in_df = set(df["name"].tolist())
                else:
                    in_df = set()
                for s in all_stops:
                    if s.get("name","") not in in_df and s.get("lat"):
                        extra_rows.append(s)
                if extra_rows:
                    extra_df = pd.DataFrame(extra_rows)
                    for c in (df.columns if df is not None and not df.empty else []):
                        if c not in extra_df.columns: extra_df[c] = ""
                    if df is not None and not df.empty:
                        map_df = pd.concat([df, extra_df], ignore_index=True)
                    else:
                        map_df = extra_df
                else:
                    map_df = df

                m = build_map(map_df, lat, lon, itin, active_day=dk, zoom=14)
                if m:
                    st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
                    st_folium(m, width="100%", height=420, returned_objects=[])
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:11px;color:#9a8c78;margin-top:6px">Numbered markers match your schedule</div>', unsafe_allow_html=True)
            else:
                st.info("Install streamlit-folium for the interactive map.")

            # AI Must-See picks
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            with st.expander(f"✦ {T('ai_picks')}", expanded=False):
                sel_types = st.session_state.get("trip_types",["🏛️ Attraction"])
                picks = get_ai_mustsee(city, cc, st.session_state.get("trip_days",3), tuple(sel_types))
                if picks:
                    in_day = {s.get("name","") for s in stops}
                    for pi,rec in enumerate(picks[:5]):
                        nm = _ss(rec.get("name",""))
                        already = nm in in_day
                        rc1,rc2 = st.columns([4,1], gap="small")
                        with rc1:
                            st.markdown(f"""
                            <div style="background:rgba(184,148,58,0.04);border:1px solid rgba(184,148,58,0.15);
                            border-radius:10px;padding:10px 12px;margin:3px 0">
                              <div style="font-weight:600;font-size:13px;color:#1a1610">{nm}</div>
                              <div style="font-size:11px;color:#b8943a;margin-top:2px">{_ss(rec.get("why",""))}</div>
                              <div style="font-size:11px;color:#9a8c78">⭐ {rec.get("rating",4.5)} · {fmt_dur(rec.get("duration_min",60))}</div>
                            </div>""", unsafe_allow_html=True)
                        with rc2:
                            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                            if already:
                                st.markdown(f'<div style="font-size:10px;color:#5a8a5a;text-align:center">{T("in_schedule")}</div>', unsafe_allow_html=True)
                            else:
                                if st.button(T("add"), key=f"ai5_{dk}_{pi}", use_container_width=True, type="primary"):
                                    new_stop = {"name":nm,
                                                "lat":rec.get("lat",lat+random.uniform(-.01,.01)),
                                                "lon":rec.get("lon",lon+random.uniform(-.01,.01)),
                                                "type_label":_ss(rec.get("type","🏛️ Attraction")),
                                                "rating":rec.get("rating",4.5),"address":"",
                                                "district":"AI Pick","description":_ss(rec.get("why","")),
                                                "time_slot":"TBD","transport_to_next":None}
                                    stops.append(new_stop)
                                    itin[dk]=stops; st.session_state["_itin"]=itin
                                    st.toast(f"Added {nm}!"); st.rerun()
                else:
                    st.caption("No AI picks for this city.")

        # ── Save & return / navigate ──
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<hr style="border:none;border-top:1px solid rgba(0,0,0,0.07);margin:4px 0">', unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        bn1,bn2,bn3 = st.columns([1,2,1], gap="small")
        with bn1:
            if di > 0:
                prev_dk = all_days[di-1]
                if st.button(f"← {prev_dk}", key="s5_prev", use_container_width=True):
                    itin[dk]=stops; st.session_state["_itin"]=itin
                    st.session_state["active_day"]=prev_dk; st.rerun()
        with bn2:
            if st.button(T("save_day"), key="s5_save_back", use_container_width=True, type="primary"):
                # Save stops back and return to overview
                itin[dk] = stops
                st.session_state["_itin"] = itin
                st.session_state["step"] = 4; st.rerun()
        with bn3:
            if di < len(all_days)-1:
                next_dk = all_days[di+1]
                if st.button(f"{next_dk} →", key="s5_next", use_container_width=True):
                    itin[dk]=stops; st.session_state["_itin"]=itin
                    st.session_state["active_day"]=next_dk; st.rerun()

    _render_ai_bubble()

# ═══════════════════════════════════════════════════════════════
# SWAP PANEL
# ═══════════════════════════════════════════════════════════════
def _render_swap(itin, df, dk, si, cc, d_bud):
    stops = itin.get(dk,[]); cur = stops[si]; cur_type = cur.get("type_label","")
    used = {s.get("name","") for sl in itin.values() if isinstance(sl,list) for s in sl}
    st.markdown(f"""
    <div class="swap-panel">
      <div style="font-size:12px;font-weight:600;color:#8a6c28;margin-bottom:10px">
        {T('alternatives')} for: <span style="color:#1a1610">{_ss(cur.get('name',''))}</span>
      </div>""", unsafe_allow_html=True)
    if df is not None and not df.empty:
        cands = df[(df["type_label"]==cur_type)&(~df["name"].isin(used))].sort_values("rating",ascending=False).head(4)
        if not cands.empty:
            sc_cols = st.columns(min(len(cands),4), gap="small")
            for i,(_,alt) in enumerate(cands.iterrows()):
                with sc_cols[i%4]:
                    nm = _ss(alt["name"]); rat = alt.get("rating",0); dur = est_dur(nm,cur_type); cs = cost_est(cur_type,d_bud,cc)
                    st.markdown(f"""
                    <div style="background:white;border-radius:10px;padding:10px;
                    border:1px solid rgba(0,0,0,0.08);margin-bottom:6px;box-shadow:0 1px 4px rgba(0,0,0,0.05)">
                      <div style="font-weight:600;font-size:12px;color:#1a1610">{nm}</div>
                      <div style="font-size:11px;color:#9a8c78">⭐ {rat} · {fmt_dur(dur)}</div>
                      <div style="font-size:11px;color:#b8943a">💰 {cs}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button(T("select"), key=f"swx_{dk}_{si}_{nm[:6]}", use_container_width=True, type="primary"):
                        new_itin = dict(itin); ds = list(new_itin.get(dk,[])); ds[si] = alt.to_dict()
                        new_itin[dk] = ds; st.session_state["_itin"] = new_itin
                        st.session_state.pop(f"_sw5_{dk}_{si}",None)
                        st.toast(f"Replaced with {nm}"); st.rerun()
        else:
            st.markdown(f'<div style="font-size:12px;color:#9a8c78">{T("no_alt")}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button(T("cancel"), key=f"swxcancel_{dk}_{si}"):
        st.session_state.pop(f"_sw5_{dk}_{si}",None); st.rerun()

# ═══════════════════════════════════════════════════════════════
# AI BUBBLE
# ═══════════════════════════════════════════════════════════════
def _render_ai_bubble():
    city = st.session_state.get("dest_city","")
    itin = st.session_state.get("_itin",{})
    itin_summary = f"{len(itin)} days in {city}, {sum(len(v) for v in itin.values() if isinstance(v,list))} stops"
    ai_open = st.session_state.get("ai_open",False)

    _,btncol = st.columns([5,1])
    with btncol:
        if st.button(f"✦ {T('ask_ai')}", key="ai_toggle", use_container_width=True,
                     type="primary" if ai_open else "secondary"):
            st.session_state["ai_open"] = not ai_open; st.rerun()

    if ai_open:
        st.markdown(f"""
        <div class="ai-panel">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
            <div style="width:32px;height:32px;border-radius:50%;
            background:linear-gradient(135deg,#b8943a,#d4aa52);
            display:flex;align-items:center;justify-content:center;font-size:14px;color:white">✦</div>
            <div>
              <div style="font-weight:600;font-size:14px;color:#1a1610">{T('ai_title')}</div>
              <div style="font-size:11px;color:#9a8c78">{T('ai_sub')}</div>
            </div>
          </div>""", unsafe_allow_html=True)

        chat = st.session_state.get("ai_chat",[])
        for msg in chat[-8:]:
            role = msg.get("role",""); content = msg.get("content","")
            if role == "user":
                st.markdown(f'<div class="chat-user"><div>{_ss(content)}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-ai"><div>{_ss(content)}</div></div>', unsafe_allow_html=True)

        if not chat:
            lang = st.session_state.get("lang","EN")
            if lang == "ZH":
                qps = [f"{city}有什么隐藏宝藏？","怎么最高效地游览？","第一天吃什么好？","如何省钱旅行？"]
            else:
                qps = [f"Best hidden gems in {city}?","How to get around efficiently?","What to eat on Day 1?","Tips for saving money?"]
            st.markdown(f'<div style="font-size:12px;color:#9a8c78;margin-bottom:8px">{T("quick_q")}</div>', unsafe_allow_html=True)
            for qi,qp in enumerate(qps):
                if st.button(qp, key=f"qp_{qi}", use_container_width=True):
                    chat.append({"role":"user","content":qp})
                    with st.spinner("…"):
                        reply = call_ai(chat,city,itin_summary)
                    chat.append({"role":"assistant","content":reply})
                    st.session_state["ai_chat"] = chat; st.rerun()

        ai_q = st.text_input(T("ai_title"), placeholder=T("ai_ph"),
                               key="ai_input", label_visibility="collapsed")
        ai1,ai2 = st.columns([4,1], gap="small")
        with ai2:
            if st.button(T("send"), key="ai_send", use_container_width=True, type="primary"):
                if ai_q.strip():
                    chat.append({"role":"user","content":ai_q.strip()})
                    with st.spinner("…"):
                        reply = call_ai(chat,city,itin_summary)
                    chat.append({"role":"assistant","content":reply})
                    st.session_state["ai_chat"] = chat; st.rerun()
        with ai1:
            if chat and st.button(T("clear"), key="ai_clear", use_container_width=True):
                st.session_state["ai_chat"] = []; st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════
step = st.session_state.get("step",1)
if   step == 1: step_1()
elif step == 2: step_2()
elif step == 3: step_3()
elif step == 4: step_4()
elif step == 5: step_5()
else: st.session_state["step"]=1; st.rerun()

st.markdown("""
<div style="text-align:center;padding:32px 0 16px;font-size:10px;letter-spacing:0.12em;
text-transform:uppercase;color:rgba(90,80,64,0.3)">
Voyager · AI Travel Planning
</div>""", unsafe_allow_html=True)
