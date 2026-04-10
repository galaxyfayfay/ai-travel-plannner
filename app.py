"""
Voyager AI Travel Planner v5
All 16 issues addressed
Apple iOS Glass Design · White + Gold
"""

import math, random, re, json, os, time
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Voyager", page_icon="✦",
    layout="wide", initial_sidebar_state="collapsed"
)

# ── Secrets ───────────────────────────────────────────────────
def _secret(k):
    try:
        v = st.secrets.get(k, "")
        if v: return str(v)
    except: pass
    return os.getenv(k, "")

AMAP_KEY      = _secret("APIKEY")
DEEPSEEK_KEY  = _secret("DEEPSEEKKEY")
ANTHROPIC_KEY = _secret("ANTHROPIC_API_KEY")

# ── Optional modules ──────────────────────────────────────────
try:
    from ai_planner import generate_itinerary; AI_OK = True
except: AI_OK = False
try:
    from transport_planner import build_day_schedule, estimate_travel; TRANSPORT_OK = True
except: TRANSPORT_OK = False
try:
    from auth_manager import (register_user, login_user, get_user_from_session,
                               logout_user, create_collab_link, join_collab); AUTH_OK = True
except: AUTH_OK = False
try:
    from wishlist_manager import (add_to_wishlist as _wl_add,
        remove_from_wishlist as _wl_remove, get_wishlist as _wl_get,
        is_in_wishlist as _wl_check, save_itinerary as _save_itin_ext,
        swap_place_in_itinerary); WISHLIST_EXT = True
except: WISHLIST_EXT = False
try:
    from points_system import add_points, get_points; POINTS_OK = True
except: POINTS_OK = False
try:
    import folium; from streamlit_folium import st_folium; FOLIUM_OK = True
except: FOLIUM_OK = False

# ════════════════════════════════════════════════════════════════
# I18N
# ════════════════════════════════════════════════════════════════
STRINGS = {
"EN": {
    "brand":"VOYAGER", "tagline":"AI Travel Planner",
    "welcome_h":"Plan your perfect journey",
    "welcome_sub":"Personalised itineraries for discerning travellers",
    "signin":"Sign In", "guest_btn":"Explore as Guest",
    "register":"Create Account",
    "username_ph":"Username", "password_ph":"Password",
    "email_ph":"Email address",
    "reg_u_ph":"Choose a username (3+ characters)",
    "reg_p_ph":"Create a password (6+ characters)",
    "guest_perks":["Personalised AI itinerary","Live place discovery","Interactive route map","Cost breakdown"],
    "where_h":"Where to?", "where_sub":"Pick a destination to begin",
    "select_country":"Select a country first",
    "select_cities":"Then choose cities",
    "cities_ph":"Search any city worldwide…",
    "popular_h":"Popular right now",
    "trip_type_h":"What kind of trip?",
    "trip_type_sub":"We'll tailor your recommendations accordingly",
    "COMMANDO":"Commando mode","COMMANDO_sub":"Pack it all in — maximum stops, maximum experiences",
    "VALUE":"Best value","VALUE_sub":"Great experiences without breaking the bank",
    "DEEP":"Deep dive","DEEP_sub":"Slow down, go deeper, discover the real local life",
    "FAMILY":"Family trip","FAMILY_sub":"Kid-friendly, manageable pace, unforgettable memories",
    "HONEYMOON":"Romantic escape","HONEYMOON_sub":"Intimate, curated, once-in-a-lifetime moments",
    "SOLO":"Solo adventure","SOLO_sub":"Freedom, flexibility, and meeting fellow travellers",
    "pref_h":"Shape your trip",
    "pref_sub":"Set your duration, interests, and daily rhythm",
    "duration_label":"How many days?",
    "budget_label":"Daily budget (USD)",
    "interests_h":"What do you enjoy?",
    "must_visit_h":"Any must-see places?",
    "must_visit_sub":"We'll make sure to include them",
    "add_ph":"e.g. Eiffel Tower, a local ramen shop, Central Park…",
    "add_btn":"Add",
    "per_day_h":"Day by day",
    "per_day_sub":"Fine-tune each day's budget and number of stops",
    "day_budget":"Budget for this day",
    "stops_label":"Stops per category",
    "logistics_h":"Getting there & staying",
    "start_ph":"Where do you start? (e.g. Heathrow Airport)",
    "end_ph":"Where do you finish? (e.g. Charles de Gaulle Airport)",
    "hotel_ph":"Where are you staying? (hotel name or area)",
    "build_btn":"Build my itinerary",
    "overview_h":"Your itinerary",
    "tap_day":"Select a day below to refine it",
    "plan_btn":"Refine this day →",
    "days_lbl":"days", "stops_lbl":"stops", "est_lbl":"Est. spend",
    "overview_reorder":"Drag days to reorder (coming soon) — use ↑ ↓ to adjust order",
    "move_up":"↑ Move up", "move_down":"↓ Move down",
    "wishlist_h":"Saved places",
    "wishlist_empty":"Places you save will appear here",
    "collab_h":"Plan together",
    "collab_sub":"Share a link so friends can co-edit your trip",
    "gen_link":"Generate share link",
    "join_h":"Join a shared trip",
    "join_ph":"Paste share code here",
    "join_btn":"Join",
    "guest_cta_h":"Save your trip",
    "guest_cta_body":"Create a free account to save this itinerary, build a wishlist, and share with friends.",
    "guest_cta_btn":"Create free account",
    "day_h":"Planning", "schedule_h":"Today's schedule",
    "add_stop_h":"Add a stop",
    "add_stop_ph":"Search for a place, landmark, or restaurant…",
    "pick_nearby":"Or pick from nearby",
    "swap_h":"Find a replacement",
    "no_swap":"No alternatives found for this category.",
    "save_day":"Save and back to overview",
    "prev_day":"← Previous day", "next_day":"Next day →",
    "ask_ai_btn":"Ask AI",
    "ai_h":"Your travel expert",
    "ai_close":"Close",
    "ai_ph":"Ask me anything about your trip…",
    "ai_send":"Send",
    "ai_clear":"Clear",
    "back":"Back", "next":"Continue →",
    "select_sel":"Select",
    "remove":"Remove",
    "swap_lbl":"Swap",
    "cancel":"Cancel",
    "in_itin":"✓ Already added",
    "building":"One moment — putting your itinerary together…",
    "finding":"Finding great places in",
    "locating":"Looking that up…",
    "no_places":"No places found. Try a different city or category.",
    "shuffle":"Regenerate",
    "save_itin":"Save itinerary",
    "export":"Export",
    "edit_prefs":"← Adjust",
    "total_lbl":"Total",
    "per_day_est":"per day",
    "add_to_itin":"Add to today",
    "reorder_days_h":"Reorder days",
},
"ZH": {
    "brand":"旅行家", "tagline":"AI 旅行规划",
    "welcome_h":"规划你的完美旅程",
    "welcome_sub":"为品质旅行者量身打造的智能行程规划",
    "signin":"登录", "guest_btn":"以游客身份体验",
    "register":"注册账户",
    "username_ph":"用户名", "password_ph":"密码",
    "email_ph":"邮箱地址",
    "reg_u_ph":"设置用户名（至少3个字符）",
    "reg_p_ph":"设置密码（至少6个字符）",
    "guest_perks":["AI 个性化行程","实时发现好去处","互动路线地图","费用明细估算"],
    "where_h":"想去哪儿？", "where_sub":"选择目的地，开启你的旅程",
    "select_country":"先选择国家",
    "select_cities":"再选择城市",
    "cities_ph":"搜索全球任意城市…",
    "popular_h":"热门推荐",
    "trip_type_h":"这次是什么风格的旅行？",
    "trip_type_sub":"我们会根据你的选择推荐最合适的行程",
    "COMMANDO":"特种兵模式","COMMANDO_sub":"时间有限，景点全收——高密度打卡",
    "VALUE":"性价比之旅","VALUE_sub":"花最少的钱，玩最精彩的地方",
    "DEEP":"深度慢游","DEEP_sub":"慢下来，深入体验当地真实生活",
    "FAMILY":"亲子游","FAMILY_sub":"轻松节奏，适合全家，留下珍贵回忆",
    "HONEYMOON":"蜜月之旅","HONEYMOON_sub":"浪漫、精致、此生难忘的两人时光",
    "SOLO":"独自旅行","SOLO_sub":"自由、灵活，遇见有趣的人和风景",
    "pref_h":"定制你的旅程",
    "pref_sub":"设置天数、兴趣偏好和每日节奏",
    "duration_label":"旅行几天？",
    "budget_label":"每日预算（美元）",
    "interests_h":"你喜欢什么类型的体验？",
    "must_visit_h":"有特别想去的地方吗？",
    "must_visit_sub":"告诉我们，我们会把它加入行程",
    "add_ph":"例如：故宫、一家当地的面馆、西湖…",
    "add_btn":"添加",
    "per_day_h":"每日细化设置",
    "per_day_sub":"为每一天单独调整预算和各类景点的数量",
    "day_budget":"当天预算",
    "stops_label":"各类别景点数量",
    "logistics_h":"出发与落脚",
    "start_ph":"从哪里出发？（如：首都机场）",
    "end_ph":"在哪里结束？（如：浦东机场）",
    "hotel_ph":"住在哪里？（酒店名称或区域）",
    "build_btn":"生成我的行程",
    "overview_h":"我的行程",
    "tap_day":"选择某一天，进行精细化规划",
    "plan_btn":"规划这一天 →",
    "days_lbl":"天", "stops_lbl":"个景点", "est_lbl":"预计花费",
    "overview_reorder":"可用 ↑ ↓ 调整天数顺序",
    "move_up":"↑ 上移", "move_down":"↓ 下移",
    "wishlist_h":"我的收藏",
    "wishlist_empty":"收藏的地方会出现在这里",
    "collab_h":"一起规划",
    "collab_sub":"生成分享链接，邀请朋友共同编辑行程",
    "gen_link":"生成分享链接",
    "join_h":"加入别人的行程",
    "join_ph":"粘贴分享码",
    "join_btn":"加入",
    "guest_cta_h":"保存你的行程",
    "guest_cta_body":"注册免费账户，即可保存行程、建立收藏夹，并与朋友分享协作。",
    "guest_cta_btn":"免费注册",
    "day_h":"规划中", "schedule_h":"今日行程",
    "add_stop_h":"添加地点",
    "add_stop_ph":"搜索景点、地标或餐厅…",
    "pick_nearby":"或从附近发现的地方中选择",
    "swap_h":"寻找替代地点",
    "no_swap":"暂无同类替换选项。",
    "save_day":"保存并返回总览",
    "prev_day":"← 上一天", "next_day":"下一天 →",
    "ask_ai_btn":"问问 AI",
    "ai_h":"你的旅行顾问",
    "ai_close":"关闭",
    "ai_ph":"关于行程，随时提问…",
    "ai_send":"发送",
    "ai_clear":"清除",
    "back":"返回", "next":"继续 →",
    "select_sel":"选择",
    "remove":"删除",
    "swap_lbl":"换一个",
    "cancel":"取消",
    "in_itin":"✓ 已在行程中",
    "building":"稍候，正在生成你的行程…",
    "finding":"正在搜索",
    "locating":"正在定位…",
    "no_places":"未找到合适的地方，换个城市或类别试试。",
    "shuffle":"重新生成",
    "save_itin":"保存行程",
    "export":"导出",
    "edit_prefs":"← 修改偏好",
    "total_lbl":"合计",
    "per_day_est":"每天",
    "add_to_itin":"加入今日行程",
    "reorder_days_h":"调整天数顺序",
},
}

def T(k):
    return STRINGS.get(st.session_state.get("lang","EN"),STRINGS["EN"]).get(k,k)

# ════════════════════════════════════════════════════════════════
# CSS — Apple iOS Glass · White + Gold
# ════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Inter:wght@300;400;500;600&display=swap');

*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"]{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  -webkit-font-smoothing:antialiased;color-scheme:light;
}

/* ── Background ── */
.stApp{
  background:
    radial-gradient(ellipse 80% 60% at 20% -10%, rgba(212,170,82,0.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 110%, rgba(184,148,58,0.08) 0%, transparent 55%),
    linear-gradient(160deg,#fcfaf5 0%,#f8f4ec 50%,#faf7f0 100%) !important;
  min-height:100vh;
}

section[data-testid="stSidebar"]{display:none!important}
.main .block-container{padding:0!important;max-width:100%!important}
#MainMenu,footer,header{visibility:hidden}
.stDeployButton{display:none}

:root{
  --gold:#b8943a;
  --gold-l:#d4aa52;
  --gold-xl:#e8c97a;
  --gold-glass:rgba(184,148,58,0.09);
  --gold-glass2:rgba(184,148,58,0.16);
  --gold-bd:rgba(184,148,58,0.22);
  --gold-bd2:rgba(184,148,58,0.42);
  --wg:rgba(255,255,255,0.68);
  --wg2:rgba(255,255,255,0.85);
  --wg3:rgba(255,255,255,0.95);
  --bd:rgba(0,0,0,0.07);
  --bd2:rgba(0,0,0,0.12);
  --t1:#18140c;
  --t2:#52472e;
  --t3:#9a8c72;
  --t4:#c0b090;
  --sh1:0 2px 8px rgba(0,0,0,0.06);
  --sh2:0 6px 24px rgba(0,0,0,0.08);
  --sh3:0 16px 48px rgba(0,0,0,0.10);
}

/* ── iOS Glass Card ── */
.ios-card{
  background:var(--wg);
  backdrop-filter:blur(28px) saturate(180%);
  -webkit-backdrop-filter:blur(28px) saturate(180%);
  border:1px solid rgba(255,255,255,0.60);
  border-radius:22px;
  box-shadow:var(--sh2),0 0 0 0.5px rgba(255,255,255,0.40) inset;
  position:relative;overflow:hidden;
}
.ios-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent 5%,rgba(255,255,255,0.90) 40%,rgba(255,255,255,0.90) 60%,transparent 95%);
}

/* ── Gold card variant ── */
.gold-card{
  background:linear-gradient(145deg,rgba(232,201,122,0.10),rgba(184,148,58,0.05));
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border:1px solid var(--gold-bd);border-radius:22px;
  box-shadow:var(--sh1),0 0 0 0.5px rgba(184,148,58,0.10) inset;
  position:relative;overflow:hidden;
}

/* ── Topbar ── */
.topbar{
  background:var(--wg2);
  backdrop-filter:blur(32px) saturate(200%);
  -webkit-backdrop-filter:blur(32px) saturate(200%);
  border-bottom:1px solid var(--bd);
  padding:10px 24px;
  position:sticky;top:0;z-index:100;
  box-shadow:0 1px 0 rgba(255,255,255,0.8),0 2px 12px rgba(0,0,0,0.05);
}

/* ── Progress ── */
.prog-row{
  display:flex;align-items:flex-start;justify-content:center;
  max-width:540px;margin:0 auto;padding:20px 0 0;
}
.prog-step{display:flex;flex-direction:column;align-items:center;flex:1;cursor:pointer;}
.prog-step:hover .prog-dot{transform:scale(1.08);}
.prog-dot{
  width:36px;height:36px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:600;
  transition:all 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
.prog-dot.done{
  background:linear-gradient(135deg,var(--gold),var(--gold-l));
  color:#fff;box-shadow:0 3px 12px rgba(184,148,58,0.38),0 0 0 3px rgba(184,148,58,0.12);
}
.prog-dot.active{
  background:var(--wg3);border:2px solid var(--gold);color:var(--gold);
  box-shadow:0 0 0 5px rgba(184,148,58,0.12),var(--sh1);transform:scale(1.12);
}
.prog-dot.pending{background:#f2ede4;border:1.5px solid #ddd5c0;color:#b0a080;}
.prog-lbl{font-size:10px;font-weight:500;margin-top:6px;letter-spacing:0.06em;text-transform:uppercase;}
.prog-lbl.active{color:var(--gold)}.prog-lbl.done{color:var(--t3)}.prog-lbl.pending{color:var(--t4)}
.prog-line{flex:1;height:1px;background:#e8e0cc;position:relative;top:-18px;}
.prog-line.done{background:linear-gradient(90deg,var(--gold-l),#e8e0cc);}

/* ── Page wrapper ── */
.page-wrap{max-width:820px;margin:0 auto;padding:28px 20px 80px;}
.page-wrap-wide{max-width:1060px;margin:0 auto;padding:24px 20px 80px;}

/* ── Type ── */
.h1{font-family:'Playfair Display',Georgia,serif;font-size:30px;font-weight:500;
    color:var(--t1);letter-spacing:-0.02em;line-height:1.2;margin:0 0 8px;}
.h1 em{font-style:italic;color:var(--gold);}
.sub{font-size:14px;color:var(--t2);line-height:1.65;margin-bottom:24px;}
.sec-label{font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
            color:var(--gold);margin-bottom:8px;display:block;}

/* ── Buttons ── */
.stButton>button{
  font-family:'Inter',sans-serif!important;font-weight:500!important;
  font-size:14px!important;border-radius:14px!important;
  transition:all 0.2s ease!important;border:none!important;
  min-height:42px!important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--gold),var(--gold-l))!important;
  color:#fff!important;font-weight:600!important;
  box-shadow:0 4px 18px rgba(184,148,58,0.32),0 1px 0 rgba(255,255,255,0.20) inset!important;
}
.stButton>button[kind="primary"]:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 8px 28px rgba(184,148,58,0.42)!important;
}
.stButton>button:not([kind="primary"]){
  background:var(--wg)!important;
  border:1px solid var(--bd2)!important;
  color:var(--t2)!important;
  backdrop-filter:blur(12px)!important;
  box-shadow:var(--sh1)!important;
}
.stButton>button:not([kind="primary"]):hover{
  background:var(--wg3)!important;color:var(--t1)!important;
  border-color:var(--gold-bd)!important;transform:translateY(-1px)!important;
}

/* ── Inputs ── */
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea{
  background:var(--wg3)!important;border:1.5px solid var(--bd2)!important;
  border-radius:14px!important;color:var(--t1)!important;
  font-size:14px!important;font-family:'Inter',sans-serif!important;
  box-shadow:var(--sh1),0 0 0 0.5px rgba(255,255,255,0.6) inset!important;
  transition:border-color 0.2s,box-shadow 0.2s!important;
}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{
  border-color:var(--gold-bd2)!important;
  box-shadow:0 0 0 4px rgba(184,148,58,0.10),var(--sh1)!important;
}
.stTextInput>div>div>input::placeholder,.stTextArea>div>div>textarea::placeholder{color:var(--t4)!important;}
.stTextInput label,.stNumberInput label,.stSelectbox label,.stSlider label{
  color:var(--t2)!important;font-size:11px!important;font-weight:600!important;
  letter-spacing:0.05em!important;text-transform:uppercase!important;
}
.stSelectbox>div>div{
  background:var(--wg3)!important;border:1.5px solid var(--bd2)!important;
  border-radius:14px!important;color:var(--t1)!important;
  box-shadow:var(--sh1)!important;
}
.stSlider>div>div>div>div{background:var(--gold)!important;}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{
  background:var(--wg)!important;border-radius:14px!important;
  border:1px solid var(--bd)!important;padding:3px!important;gap:2px!important;
  box-shadow:var(--sh1)!important;backdrop-filter:blur(16px)!important;
}
.stTabs [data-baseweb="tab"]{
  border-radius:11px!important;color:var(--t3)!important;
  font-size:13px!important;font-weight:500!important;min-height:36px!important;
}
.stTabs [aria-selected="true"]{
  background:var(--wg3)!important;color:var(--t1)!important;
  box-shadow:var(--sh1)!important;
}

/* ── Metrics ── */
div[data-testid="stMetric"]{
  background:var(--wg)!important;border:1px solid var(--bd)!important;
  border-radius:18px!important;padding:16px 20px!important;
  box-shadow:var(--sh1)!important;backdrop-filter:blur(16px)!important;
}
div[data-testid="stMetric"] label{
  color:var(--t3)!important;font-size:10px!important;font-weight:700!important;
  text-transform:uppercase!important;letter-spacing:0.1em!important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
  color:var(--t1)!important;font-size:22px!important;font-weight:700!important;
}

/* ── Expanders ── */
.stExpander{
  background:var(--wg)!important;border:1px solid var(--bd)!important;
  border-radius:16px!important;box-shadow:var(--sh1)!important;
  backdrop-filter:blur(16px)!important;
}
.stExpander>div>div>div>div>p{color:var(--t2)!important;font-size:13px!important;}

/* ── Download ── */
div[data-testid="stDownloadButton"] button{
  background:var(--gold-glass)!important;color:var(--gold)!important;
  border:1px solid var(--gold-bd)!important;
}

/* ── Multiselect ── */
.stMultiSelect>div>div{
  background:var(--wg3)!important;border:1.5px solid var(--bd2)!important;border-radius:14px!important;
}
.stMultiSelect span[data-baseweb="tag"]{
  background:var(--gold-glass)!important;border-color:var(--gold-bd)!important;color:var(--gold)!important;
}

/* ── Form submit ── */
.stFormSubmitButton>button{
  background:linear-gradient(135deg,var(--gold),var(--gold-l))!important;
  color:#fff!important;font-weight:600!important;border:none!important;
  border-radius:14px!important;box-shadow:0 4px 18px rgba(184,148,58,0.32)!important;
}

/* ── Alerts ── */
.stAlert{border-radius:14px!important;}
.stCaption{color:var(--t3)!important;font-size:12px!important;}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-thumb{background:rgba(184,148,58,0.25);border-radius:4px}

/* ── Trip type card ── */
.tt-card{
  background:var(--wg);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1.5px solid var(--bd);border-radius:18px;padding:18px 16px;
  cursor:pointer;transition:all 0.2s ease;text-align:center;
  box-shadow:var(--sh1);position:relative;overflow:hidden;
}
.tt-card:hover{box-shadow:var(--sh2);border-color:var(--gold-bd);transform:translateY(-2px);}
.tt-card.sel{
  background:linear-gradient(145deg,rgba(232,201,122,0.12),rgba(184,148,58,0.06));
  border-color:var(--gold-bd2);
  box-shadow:var(--sh2),0 0 0 3px rgba(184,148,58,0.10);
}
.tt-card.sel::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--gold),var(--gold-l));
}
.tt-icon{font-size:28px;margin-bottom:8px;}
.tt-title{font-weight:600;font-size:13px;color:var(--t1);margin-bottom:4px;}
.tt-sub{font-size:11px;color:var(--t3);line-height:1.4;}

/* ── City pill ── */
.city-pill-sel{
  display:inline-flex;align-items:center;gap:5px;
  padding:5px 12px;border-radius:100px;
  background:linear-gradient(135deg,rgba(184,148,58,0.12),rgba(212,170,82,0.08));
  border:1px solid var(--gold-bd2);font-size:12px;color:var(--gold);font-weight:600;
  margin:3px;white-space:nowrap;
}

/* ── Stop card ── */
.stop-card{
  background:var(--wg3);border:1px solid var(--bd);
  border-radius:14px;padding:12px 14px;margin:5px 0;
  box-shadow:var(--sh1);transition:box-shadow 0.15s;
}
.stop-card:hover{box-shadow:var(--sh2);border-color:var(--gold-bd);}

/* ── Day overview card ── */
.day-ov-card{
  background:var(--wg);border:1px solid var(--bd);
  border-radius:18px;padding:16px 18px;margin:7px 0;
  box-shadow:var(--sh1);transition:all 0.2s;
  backdrop-filter:blur(16px);
}
.day-ov-card:hover{box-shadow:var(--sh2);border-color:var(--gold-bd);transform:translateY(-1px);}

/* ── Budget bar ── */
.bud-track{background:#ede8dc;border-radius:4px;height:4px;overflow:hidden;}
.bud-fill{height:4px;border-radius:4px;transition:width 0.4s ease;}

/* ── Map ── */
.map-wrap{border-radius:18px;overflow:hidden;border:1px solid var(--bd);box-shadow:var(--sh2);}

/* ── AI panel ── */
.ai-panel{
  background:var(--wg2);backdrop-filter:blur(28px) saturate(180%);
  border:1px solid var(--gold-bd);border-radius:22px;padding:20px;
  box-shadow:var(--sh3);margin:8px 0 16px;
}
.chat-me{display:flex;justify-content:flex-end;margin:5px 0;}
.chat-me>div{
  background:linear-gradient(135deg,var(--gold),var(--gold-l));color:#fff;
  padding:9px 14px;border-radius:18px 18px 4px 18px;
  font-size:13px;max-width:75%;line-height:1.55;box-shadow:0 2px 8px rgba(184,148,58,0.25);
}
.chat-ai{display:flex;margin:5px 0;}
.chat-ai>div{
  background:var(--wg3);color:var(--t1);
  padding:9px 14px;border-radius:4px 18px 18px 18px;
  border:1px solid var(--bd);font-size:13px;max-width:85%;line-height:1.65;box-shadow:var(--sh1);
}

/* ── Guest CTA ── */
.guest-cta{
  background:linear-gradient(145deg,rgba(232,201,122,0.10),rgba(184,148,58,0.05));
  border:1px solid var(--gold-bd);border-radius:20px;padding:22px 24px;margin:16px 0;
  backdrop-filter:blur(16px);
}

/* ── Collab code ── */
.collab-code{
  background:var(--gold-glass);border:1px solid var(--gold-bd);
  border-radius:12px;padding:12px;text-align:center;
  font-family:'SF Mono','Fira Code',monospace;
  font-size:22px;font-weight:700;color:var(--gold);letter-spacing:0.15em;
}

/* ── Swap panel ── */
.swap-panel{
  background:rgba(252,248,240,0.95);border:1px solid var(--gold-bd);
  border-radius:14px;padding:14px;margin:5px 0;
  backdrop-filter:blur(12px);
}

/* ── Sticky bottom nav ── */
.bottom-nav{
  position:fixed;bottom:0;left:0;right:0;z-index:90;
  background:var(--wg2);backdrop-filter:blur(32px) saturate(200%);
  border-top:1px solid var(--bd);padding:10px 24px;
  box-shadow:0 -4px 24px rgba(0,0,0,0.06);
  display:flex;align-items:center;justify-content:space-between;gap:12px;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════════════
CHAIN_BL = ["kfc","mcdonald","starbucks","seven-eleven","711","lawson","costa coffee"]
def is_chain(n): return any(k in n.lower() for k in CHAIN_BL)

def _ss(s):
    if s is None: return ""
    s = str(s)
    for o,n in {"\u2014":"-","\u2013":"-","\u2019":"'","\u201c":'"',"\u201d":'"'}.items():
        s = s.replace(o,n)
    return s

def _hkm(a,b,c,d):
    R=6371.0; dl=math.radians(c-a); dg=math.radians(d-b)
    x=math.sin(dl/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(dg/2)**2
    return R*2*math.asin(min(1.0,math.sqrt(x)))

PTYPES = {
    "🏛️ Attraction":  {"osm":("tourism","attraction"), "amap":"110000","color":"#b8943a"},
    "🍜 Restaurant":  {"osm":("amenity","restaurant"),  "amap":"050000","color":"#c0684a"},
    "☕ Cafe":         {"osm":("amenity","cafe"),         "amap":"050500","color":"#7a6040"},
    "🌿 Park":         {"osm":("leisure","park"),         "amap":"110101","color":"#4a7a4a"},
    "🛍️ Shopping":    {"osm":("shop","mall"),            "amap":"060000","color":"#a05878"},
    "🍺 Bar/Nightlife":{"osm":("amenity","bar"),          "amap":"050600","color":"#605898"},
    "🏨 Hotel":        {"osm":("tourism","hotel"),         "amap":"100000","color":"#3878a8"},
}
DAY_COLORS = ["#b8943a","#c0684a","#4a7a4a","#a05878","#605898","#3878a8","#7a6040","#806030"]

AMAP_KW = {
    "🏛️ Attraction":["旅游景点","博物馆"],"🍜 Restaurant":["餐馆","美食"],
    "☕ Cafe":["咖啡","下午茶"],"🌿 Park":["公园","花园"],
    "🛍️ Shopping":["商场","购物中心"],"🍺 Bar/Nightlife":["酒吧","夜店"],
    "🏨 Hotel":["酒店","宾馆"],
}

# Trip-type → adjusted quotas modifier
TRIP_TYPE_MODS = {
    "COMMANDO":  {"quota_mul":2.0, "min_rating":3.5},
    "VALUE":     {"quota_mul":1.0, "min_rating":4.0},
    "DEEP":      {"quota_mul":0.6, "min_rating":4.2},
    "FAMILY":    {"quota_mul":1.0, "min_rating":4.2, "preferred":["🏛️ Attraction","🌿 Park"]},
    "HONEYMOON": {"quota_mul":0.7, "min_rating":4.5, "preferred":["🌿 Park","🍜 Restaurant"]},
    "SOLO":      {"quota_mul":1.2, "min_rating":4.0},
}

DURATION_MAP = {"🏛️ Attraction":90,"🍜 Restaurant":60,"☕ Cafe":45,"🌿 Park":60,
                "🛍️ Shopping":90,"🍺 Bar/Nightlife":90,"🏨 Hotel":20}
DURATION_SPEC = {"museum":120,"palace":120,"castle":120,"temple":60,"shrine":45,
                 "cathedral":60,"market":75,"gallery":75,"park":60,"garden":75,
                 "tower":45,"viewpoint":30,"crossing":20,"restaurant":60,"cafe":45,
                 "mall":90,"beach":90,"aquarium":90,"zoo":120}

def est_dur(name,tl):
    nl=(name or "").lower()
    for k,v in DURATION_SPEC.items():
        if k in nl: return v
    return DURATION_MAP.get(tl,60)

def fmt_dur(m):
    if m<60: return f"{m}min"
    h=m//60;r=m%60
    return f"{h}h {r}min" if r else f"{h}h"

def _parse_dur(s):
    if not s: return 20
    s=s.lower().strip();total=0
    h=re.search(r'(\d+)\s*h',s);m=re.search(r'(\d+)\s*m',s)
    if h: total+=int(h.group(1))*60
    if m: total+=int(m.group(1))
    return total if total>0 else 20

CURRENCIES={"CN":("¥",7.25),"JP":("¥",155),"KR":("₩",1350),"TH":("฿",36),
             "SG":("S$",1.35),"FR":("€",0.92),"GB":("£",0.79),"IT":("€",0.92),
             "ES":("€",0.92),"US":("$",1.0),"AU":("A$",1.53),"AE":("AED",3.67),
             "NL":("€",0.92),"TR":("₺",32),"HK":("HK$",7.82),"TW":("NT$",32),"INT":("$",1.0)}
def local_rate(cc): return CURRENCIES.get(cc,("$",1.0))

COST_W  = {"🏛️ Attraction":0.18,"🍜 Restaurant":0.25,"☕ Cafe":0.10,"🌿 Park":0.04,
           "🛍️ Shopping":0.22,"🍺 Bar/Nightlife":0.16,"🏨 Hotel":0.00}
COST_FL = {"🏛️ Attraction":4,"🍜 Restaurant":6,"☕ Cafe":3,"🌿 Park":0,
           "🛍️ Shopping":8,"🍺 Bar/Nightlife":5,"🏨 Hotel":0}

def cost_est(tl,daily,cc):
    w=COST_W.get(tl,.12);fl=COST_FL.get(tl,2)
    pv=max(fl,daily*w/2);lo=pv*.65;hi=pv*1.45
    sym,rate=local_rate(cc)
    if cc=="US": return f"${round(lo)}–${round(hi)}"
    return f"${round(lo)}–${round(hi)} ({sym}{round(lo*rate)}–{sym}{round(hi*rate)})"

WORLD_CITIES = {
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya","Hiroshima","Nara"],
    "South Korea":["Seoul","Busan","Jeju","Gyeongju"],
    "Thailand":["Bangkok","Chiang Mai","Phuket","Koh Samui","Pai"],
    "Vietnam":["Ho Chi Minh City","Hanoi","Da Nang","Hoi An","Nha Trang"],
    "Indonesia":["Bali","Jakarta","Yogyakarta","Lombok"],
    "Malaysia":["Kuala Lumpur","Penang","Malacca","Langkawi"],
    "Singapore":["Singapore"],
    "India":["Mumbai","Delhi","Jaipur","Goa","Agra","Varanasi","Bangalore"],
    "UAE":["Dubai","Abu Dhabi"],
    "Turkey":["Istanbul","Cappadocia","Antalya","Bodrum"],
    "France":["Paris","Nice","Lyon","Bordeaux","Marseille"],
    "Italy":["Rome","Milan","Florence","Venice","Naples","Amalfi"],
    "Spain":["Barcelona","Madrid","Seville","Valencia","Granada","Bilbao"],
    "United Kingdom":["London","Edinburgh","Manchester","Bath","Oxford"],
    "Germany":["Berlin","Munich","Hamburg","Frankfurt","Cologne"],
    "Netherlands":["Amsterdam","Rotterdam","Utrecht"],
    "Switzerland":["Zurich","Geneva","Lucerne","Zermatt","Interlaken"],
    "Austria":["Vienna","Salzburg","Innsbruck"],
    "Greece":["Athens","Santorini","Mykonos","Crete","Rhodes"],
    "Portugal":["Lisbon","Porto","Algarve","Sintra"],
    "Czech Republic":["Prague","Cesky Krumlov"],
    "Hungary":["Budapest"],
    "Croatia":["Dubrovnik","Split","Zagreb"],
    "Norway":["Oslo","Bergen","Tromso"],
    "Sweden":["Stockholm","Gothenburg"],
    "Denmark":["Copenhagen"],
    "Iceland":["Reykjavik","Akureyri"],
    "USA":["New York","Los Angeles","San Francisco","Miami","Chicago","Las Vegas","Boston","Seattle","New Orleans"],
    "Canada":["Toronto","Vancouver","Montreal","Banff","Quebec City"],
    "Mexico":["Mexico City","Cancun","Oaxaca","Tulum"],
    "Brazil":["Rio de Janeiro","Sao Paulo","Salvador"],
    "Peru":["Cusco","Lima","Machu Picchu"],
    "Colombia":["Bogota","Cartagena","Medellin"],
    "Australia":["Sydney","Melbourne","Brisbane","Cairns","Perth"],
    "New Zealand":["Auckland","Queenstown","Wellington","Rotorua"],
    "Morocco":["Marrakech","Fes","Chefchaouen"],
    "Egypt":["Cairo","Luxor","Aswan"],
    "South Africa":["Cape Town","Johannesburg","Durban"],
    "Kenya":["Nairobi","Masai Mara","Mombasa"],
    "China":["Beijing","Shanghai","Chengdu","Hangzhou","Xi'an","Guilin","Zhangjiajie"],
    "Hong Kong":["Hong Kong"],
    "Taiwan":["Taipei","Tainan","Hualien"],
    "Philippines":["Manila","Palawan","Cebu","Boracay"],
    "Cambodia":["Siem Reap","Phnom Penh"],
    "Nepal":["Kathmandu","Pokhara"],
    "Sri Lanka":["Colombo","Kandy","Ella","Galle"],
    "Jordan":["Amman","Petra","Wadi Rum"],
    "Israel":["Tel Aviv","Jerusalem"],
}
COUNTRY_CODES={
    "China":"CN","Japan":"JP","South Korea":"KR","Thailand":"TH","Vietnam":"VN",
    "Indonesia":"ID","Malaysia":"MY","Singapore":"SG","India":"IN","UAE":"AE","Turkey":"TR",
    "France":"FR","Italy":"IT","Spain":"ES","United Kingdom":"GB","Germany":"DE",
    "Netherlands":"NL","Switzerland":"CH","Austria":"AT","Greece":"GR","Portugal":"PT",
    "Czech Republic":"CZ","Hungary":"HU","Croatia":"HR","Norway":"NO","Sweden":"SE",
    "Denmark":"DK","Iceland":"IS","USA":"US","Canada":"CA","Mexico":"MX","Brazil":"BR",
    "Peru":"PE","Colombia":"CO","Australia":"AU","New Zealand":"NZ","Morocco":"MA",
    "Egypt":"EG","South Africa":"ZA","Kenya":"KE","Hong Kong":"HK","Taiwan":"TW",
    "Philippines":"PH","Cambodia":"KH","Nepal":"NP","Sri Lanka":"LK","Jordan":"JO",
    "Israel":"IL",
}
INTL_CITIES={
    "tokyo":(35.6762,139.6503,"JP"),"osaka":(34.6937,135.5023,"JP"),
    "kyoto":(35.0116,135.7681,"JP"),"nara":(34.6851,135.8050,"JP"),
    "sapporo":(43.0642,141.3469,"JP"),"fukuoka":(33.5904,130.4017,"JP"),
    "nagoya":(35.1815,136.9066,"JP"),"hiroshima":(34.3853,132.4553,"JP"),
    "seoul":(37.5665,126.9780,"KR"),"busan":(35.1796,129.0756,"KR"),"jeju":(33.4996,126.5312,"KR"),
    "bangkok":(13.7563,100.5018,"TH"),"chiang mai":(18.7883,98.9853,"TH"),"phuket":(7.8804,98.3923,"TH"),
    "singapore":(1.3521,103.8198,"SG"),
    "paris":(48.8566,2.3522,"FR"),"nice":(43.7102,7.2620,"FR"),"lyon":(45.7640,4.8357,"FR"),
    "bordeaux":(44.8378,-0.5792,"FR"),"marseille":(43.2965,5.3698,"FR"),
    "london":(51.5072,-0.1276,"GB"),"edinburgh":(55.9533,-3.1883,"GB"),
    "rome":(41.9028,12.4964,"IT"),"milan":(45.4654,9.1859,"IT"),
    "florence":(43.7696,11.2558,"IT"),"venice":(45.4408,12.3155,"IT"),"naples":(40.8518,14.2681,"IT"),
    "barcelona":(41.3851,2.1734,"ES"),"madrid":(40.4168,-3.7038,"ES"),
    "seville":(37.3891,-5.9845,"ES"),"valencia":(39.4699,-0.3763,"ES"),
    "granada":(37.1773,-3.5986,"ES"),
    "berlin":(52.5200,13.4050,"DE"),"munich":(48.1351,11.5820,"DE"),
    "amsterdam":(52.3676,4.9041,"NL"),
    "vienna":(48.2082,16.3738,"AT"),"salzburg":(47.8095,13.0550,"AT"),
    "zurich":(47.3769,8.5417,"CH"),"geneva":(46.2044,6.1432,"CH"),
    "lucerne":(47.0502,8.3093,"CH"),"zermatt":(46.0207,7.7491,"CH"),
    "santorini":(36.3932,25.4615,"GR"),"athens":(37.9838,23.7275,"GR"),"mykonos":(37.4467,25.3289,"GR"),
    "lisbon":(38.7223,-9.1393,"PT"),"porto":(41.1579,-8.6291,"PT"),
    "prague":(50.0755,14.4378,"CZ"),"budapest":(47.4979,19.0402,"HU"),
    "dubrovnik":(42.6507,18.0944,"HR"),"oslo":(59.9139,10.7522,"NO"),
    "stockholm":(59.3293,18.0686,"SE"),"reykjavik":(64.1265,-21.8174,"IS"),
    "new york":(40.7128,-74.0060,"US"),"los angeles":(34.0522,-118.2437,"US"),
    "san francisco":(37.7749,-122.4194,"US"),"miami":(25.7617,-80.1918,"US"),
    "chicago":(41.8781,-87.6298,"US"),"las vegas":(36.1699,-115.1398,"US"),
    "boston":(42.3601,-71.0589,"US"),"seattle":(47.6062,-122.3321,"US"),
    "toronto":(43.6532,-79.3832,"CA"),"vancouver":(49.2827,-123.1207,"CA"),
    "montreal":(45.5017,-73.5673,"CA"),"banff":(51.1784,-115.5708,"CA"),
    "dubai":(25.2048,55.2708,"AE"),"abu dhabi":(24.4539,54.3773,"AE"),
    "istanbul":(41.0082,28.9784,"TR"),"cappadocia":(38.6431,34.8289,"TR"),
    "marrakech":(31.6295,-7.9811,"MA"),"fes":(34.0181,-5.0078,"MA"),
    "cairo":(30.0444,31.2357,"EG"),"luxor":(25.6872,32.6396,"EG"),
    "cape town":(-33.9249,18.4241,"ZA"),
    "hong kong":(22.3193,114.1694,"HK"),
    "taipei":(25.0330,121.5654,"TW"),
    "bali":(-8.3405,115.0920,"ID"),"jakarta":(-6.2088,106.8456,"ID"),
    "ho chi minh city":(10.7769,106.7009,"VN"),"hanoi":(21.0285,105.8542,"VN"),
    "da nang":(16.0544,108.2022,"VN"),"hoi an":(15.8801,108.3380,"VN"),
    "kuala lumpur":(3.1390,101.6869,"MY"),"penang":(5.4164,100.3327,"MY"),
    "beijing":(39.9042,116.4074,"CN"),"shanghai":(31.2304,121.4737,"CN"),
    "chengdu":(30.5728,104.0668,"CN"),"hangzhou":(30.2741,120.1551,"CN"),
    "xi'an":(34.3416,108.9398,"CN"),"guilin":(25.2735,110.2900,"CN"),
    "mumbai":(19.0760,72.8777,"IN"),"delhi":(28.6139,77.2090,"IN"),
    "jaipur":(26.9124,75.7873,"IN"),"goa":(15.2993,74.1240,"IN"),
    "cancun":(21.1619,-86.8515,"MX"),"mexico city":(19.4326,-99.1332,"MX"),
    "rio de janeiro":(-22.9068,-43.1729,"BR"),
    "cusco":(-13.5320,-71.9675,"PE"),
    "cartagena":(10.3910,-75.4794,"CO"),"medellin":(6.2442,-75.5812,"CO"),
    "sydney":(-33.8688,151.2093,"AU"),"melbourne":(-37.8136,144.9631,"AU"),
    "queenstown":(-45.0312,168.6626,"NZ"),
    "siem reap":(13.3671,103.8448,"KH"),
    "kathmandu":(27.7172,85.3240,"NP"),
    "colombo":(6.9271,79.8612,"LK"),"galle":(6.0535,80.2210,"LK"),
    "petra":(30.3285,35.4444,"JO"),
    "tel aviv":(32.0853,34.7818,"IL"),
}
CN_CITIES={
    "beijing":(39.9042,116.4074),"shanghai":(31.2304,121.4737),
    "guangzhou":(23.1291,113.2644),"shenzhen":(22.5431,114.0579),
    "chengdu":(30.5728,104.0668),"hangzhou":(30.2741,120.1551),
    "xi'an":(34.3416,108.9398),"xian":(34.3416,108.9398),
    "chongqing":(29.5630,106.5516),"guilin":(25.2735,110.2900),
}

POPULAR_ROWS = [
    [("🗼","Tokyo","Japan"),("🌆","Dubai","UAE"),("🗽","New York","USA"),("🗺️","Paris","France")],
    [("🏖️","Bali","Indonesia"),("🏰","Rome","Italy"),("🌸","Kyoto","Japan"),("🌃","Barcelona","Spain")],
    [("🏔️","Santorini","Greece"),("🎠","Prague","Czech Republic"),("🌊","Lisbon","Portugal"),("🎋","Singapore","Singapore")],
    [("🦁","Cape Town","South Africa"),("🌴","Bangkok","Thailand"),("❄️","Reykjavik","Iceland"),("🏯","Seoul","South Korea")],
    [("🎆","Sydney","Australia"),("🏔️","Queenstown","New Zealand"),("🌺","Marrakech","Morocco"),("🌸","Hanoi","Vietnam")],
]

TRIP_TYPES = [
    ("COMMANDO","⚡"),("VALUE","💰"),("DEEP","🔍"),
    ("FAMILY","👨‍👩‍👧"),("HONEYMOON","💍"),("SOLO","🎒"),
]

# ════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════
_DEFS={
    "lang":"EN","step":1,"user_mode":None,"_auth_token":"",
    "dest_countries":[],"dest_cities":[],"dest_lat":None,"dest_lon":None,
    "dest_city":"","dest_cc":"INT","dest_is_cn":False,
    "trip_type":"VALUE","trip_days":3,"trip_types":["🏛️ Attraction","🍜 Restaurant"],
    "trip_budget":100,"day_configs":{},"custom_places":[],
    "_itin":None,"_df":None,"seed":42,
    "active_day":None,"ai_chat":[],"ai_open":False,
    "collab_code":"","pop_row":0,
}
for k,v in _DEFS.items():
    if k not in st.session_state: st.session_state[k]=v

# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    try:
        tok=st.session_state.get("_auth_token","")
        if not tok: return None
        return get_user_from_session(tok)
    except: return None

def _wl_add_fn(u,p):
    if WISHLIST_EXT:
        try: _wl_add(u,p); return
        except: pass
    k=f"_wl_{u}"; lst=st.session_state.get(k,[])
    if p.get("name","") not in {x.get("name","") for x in lst}:
        lst.append(p); st.session_state[k]=lst

def _wl_rm_fn(u,name):
    if WISHLIST_EXT:
        try: _wl_remove(u,name); return
        except: pass
    k=f"_wl_{u}"
    st.session_state[k]=[p for p in st.session_state.get(k,[]) if p.get("name","")!=name]

def _wl_get_fn(u):
    if WISHLIST_EXT:
        try: return _wl_get(u)
        except: pass
    return st.session_state.get(f"_wl_{u}",[])

def _wl_chk_fn(u,name):
    if WISHLIST_EXT:
        try: return _wl_check(u,name)
        except: pass
    return any(p.get("name","")==name for p in st.session_state.get(f"_wl_{u}",[]))

def _save_itin(u,itin,city,title):
    if WISHLIST_EXT:
        try: _save_itin_ext(u,itin,city,title); return
        except: pass
    k=f"_saved_{u}"; s=st.session_state.get(k,[])
    s.append({"city":city,"title":title,"data":itin,"at":datetime.now().strftime("%Y-%m-%d")})
    st.session_state[k]=s[-10:]

def build_timeline(stops,start_h=9):
    result=[]; cur=start_h*60
    for i,s in enumerate(stops):
        tl=s.get("type_label","🏛️ Attraction"); nm=s.get("name",""); dur=est_dur(nm,tl)
        if i>0:
            tr=stops[i-1].get("transport_to_next") or {}
            cur+=_parse_dur(tr.get("duration",""))
        arr_h=cur//60; arr_m=cur%60; dep=cur+dur; dep_h=dep//60; dep_m=dep%60
        e=dict(s); e["arrive_time"]=f"{arr_h:02d}:{arr_m:02d}"
        e["depart_time"]=f"{dep_h:02d}:{dep_m:02d}"; e["duration_min"]=dur
        result.append(e); cur=dep+15
    return result

def geo_dedup(places,r=100.):
    if not places: return []
    merged=[False]*len(places); kept=[]
    for i,p in enumerate(places):
        if merged[i]: continue
        best=p
        for j in range(i+1,len(places)):
            if merged[j]: continue
            d=_hkm(best["lat"],best["lon"],places[j]["lat"],places[j]["lon"])*1000
            sl=places[j]["name"].strip().lower(); bl=best["name"].strip().lower()
            sim=(sl==bl)or(len(sl)>=4 and sl in bl)or(len(bl)>=4 and bl in sl)
            if d<40 or (d<r and sim):
                merged[j]=True
                if places[j]["rating"]>best["rating"]: best=places[j]
        kept.append(best)
    return kept

def tdesc(s):
    D={"attraction":"Sightseeing","restaurant":"Dining","cafe":"Café",
       "park":"Outdoors","mall":"Shopping","bar":"Nightlife","hotel":"Stay"}
    for k,v in D.items():
        if k in str(s).lower(): return v
    return "Highlight"

# Primary city for geocoding (first in list)
def _primary_city():
    cities=st.session_state.get("dest_cities",[])
    return cities[0] if cities else st.session_state.get("dest_city","")

# ════════════════════════════════════════════════════════════════
# GEOCODING
# ════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600,show_spinner=False)
def _nom(q):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
                       params={"q":q,"format":"json","limit":1},
                       headers={"User-Agent":"VoyagerApp/5.0"},timeout=9).json()
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
                lon,lat=map(float,loc.split(","))
                return lat,lon
    except: pass
    return None

# ════════════════════════════════════════════════════════════════
# PLACE SEARCH
# ════════════════════════════════════════════════════════════════
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
            all_p.append({"name":_ss(nm),"lat":elat,"lon":elon,
                          "rating":round(random.uniform(3.8,5.0),1),
                          "address":"","phone":"","website":"","type":ov,"type_label":tl,
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
    all_p=[];seen=set()
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
    NAMES={
        "🏛️ Attraction":["Grand Museum","Sky Tower","Ancient Temple","Art Gallery","Historic Castle","Old Quarter","Royal Palace","Heritage Site","Cultural Centre","Night Market"],
        "🍜 Restaurant":["The Local Table","Harbour Grill","Garden Restaurant","Night Kitchen","Chef's Table","Street Food Lane","Old Town Bistro"],
        "☕ Cafe":["Morning Roast","Corner Café","Artisan Brew","Rooftop Coffee","Matcha House"],
        "🌿 Park":["Riverside Park","Botanical Garden","Central Green","Waterfront Walk"],
        "🛍️ Shopping":["Grand Market","Designer Quarter","Vintage Arcade","Night Bazaar"],
        "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Hall","Cocktail Club"],
        "🏨 Hotel":["Grand Palace Hotel","Boutique Inn","City View Hotel"],
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
                        "address":"Sample destination","phone":"","website":"",
                        "type":tl,"type_label":tl,"district":["North","Central","South"][ci],
                        "description":tdesc(tl)})
    return out

@st.cache_data(ttl=180,show_spinner=False)
def fetch_places(clat,clon,cc,is_cn,tls_t,lpt,_seed):
    random.seed(_seed); tls=list(tls_t)
    raw=search_cn(clat,clon,tls,lpt) if is_cn else search_intl(clat,clon,tls,lpt)
    raw=geo_dedup(raw); warn=None
    if not raw:
        raw=demo_places(clat,clon,tls,lpt,_seed)
        warn="Live data temporarily unavailable — showing sample places."
    df=pd.DataFrame(raw)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c]=""
    df["rating"]=pd.to_numeric(df["rating"],errors="coerce").fillna(0.)
    for c in ["name","address","district","description","type_label","type"]: df[c]=df[c].apply(_ss)
    return df.sort_values("rating",ascending=False).reset_index(drop=True),warn

# ════════════════════════════════════════════════════════════════
# AI ASSISTANT
# ════════════════════════════════════════════════════════════════
def call_ai(messages,city,itin_summary,lang="EN"):
    if lang=="ZH":
        system=(f"你是旅行家AI，正在帮用户规划{city}的行程。"
                f"当前行程：{itin_summary}。"
                f"回答简洁（不超过120字）、专业、接地气。全程使用中文回答。")
    else:
        system=(f"You are a Voyager travel expert helping plan a trip to {city}. "
                f"Current itinerary: {itin_summary}. "
                f"Reply concisely (max 120 words), warmly, and with specific local expertise.")
    if ANTHROPIC_KEY:
        try:
            resp=requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
                json={"model":"claude-sonnet-4-20250514","max_tokens":280,"system":system,"messages":messages},timeout=20)
            if resp.status_code==200:
                for blk in resp.json().get("content",[]):
                    if blk.get("type")=="text": return blk["text"]
        except: pass
    if DEEPSEEK_KEY:
        try:
            resp=requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
                json={"model":"deepseek-chat",
                      "messages":[{"role":"system","content":system}]+messages,
                      "temperature":0.7,"max_tokens":280},timeout=15)
            if resp.status_code==200:
                return resp.json()["choices"][0]["message"]["content"]
        except: pass
    # Fallback (language-aware)
    if lang=="ZH":
        return f"关于{city}：建议上午游览核心景区，避开人流高峰；下午探索当地街区和市集；晚上在当地人推荐的餐厅享用美食。记得提前在网上购买热门景点门票！"
    return f"For {city}: head to the main landmarks in the morning before crowds, explore local neighbourhoods in the afternoon, and save evenings for dining where locals eat. Book popular tickets online in advance."

# ════════════════════════════════════════════════════════════════
# MAP
# ════════════════════════════════════════════════════════════════
def build_map(df,lat,lon,itin,active_day=None,zoom=13,planned_only=False):
    if not FOLIUM_OK: return None
    m=folium.Map(location=[lat,lon],zoom_start=zoom,tiles="CartoDB positron")
    # index by name
    vi={}
    if itin:
        for di,(dk,stops) in enumerate(itin.items()):
            if not isinstance(stops,list): continue
            for si,s in enumerate(stops): vi[s.get("name","")]=(di,si+1,dk)
    # routes
    if itin:
        for di,(dk,stops) in enumerate(itin.items()):
            if not isinstance(stops,list) or len(stops)<2: continue
            if active_day and dk!=active_day: continue
            dc=DAY_COLORS[di%len(DAY_COLORS)]
            for si in range(len(stops)-1):
                a,b=stops[si],stops[si+1]
                if not(a.get("lat") and b.get("lat")): continue
                folium.PolyLine([[a["lat"],a["lon"]],[b["lat"],b["lon"]]],
                                color=dc,weight=3,opacity=0.7,dash_array="5 4").add_to(m)
    # markers
    if df is not None and not df.empty:
        for _,row in df.iterrows():
            v=vi.get(row["name"])
            if planned_only and not v: continue
            if active_day and v and v[2]!=active_day: continue
            if v:
                di,sn,dk2=v; color=DAY_COLORS[di%len(DAY_COLORS)]; label=str(sn)
            else:
                if active_day: continue
                color="#c8bea0"; label="·"
            nm=_ss(row.get("name",""))
            dur=est_dur(nm,row.get("type_label",""))
            pop=(f"<div style='font-family:-apple-system,sans-serif;background:white;color:#18140c;"
                 f"padding:12px;border-radius:12px;min-width:150px;border:1px solid #e8ddc8;"
                 f"box-shadow:0 4px 16px rgba(0,0,0,0.10)'>"
                 f"<b style='font-size:13px'>{nm}</b><br>"
                 f"<span style='color:#b8943a;font-size:11px'>⭐ {row['rating']:.1f} · {fmt_dur(dur)}</span>"
                 f"</div>")
            folium.Marker([row["lat"],row["lon"]],
                popup=folium.Popup(pop,max_width=200),tooltip=nm,
                icon=folium.DivIcon(
                    html=(f'<div style="width:28px;height:28px;border-radius:50%;background:{color};'
                          f'border:2.5px solid white;display:flex;align-items:center;justify-content:center;'
                          f'color:white;font-size:11px;font-weight:700;'
                          f'box-shadow:0 2px 10px rgba(0,0,0,0.22)">{label}</div>'),
                    icon_size=(28,28),icon_anchor=(14,14))).add_to(m)
    # unscheduled pins for day-detail (so user can click "add to today")
    if active_day and df is not None and not df.empty:
        in_today={s.get("name","") for s in itin.get(active_day,[]) if isinstance(itin.get(active_day),list)}
        for _,row in df.iterrows():
            nm=_ss(row.get("name",""))
            if nm in vi or nm in in_today: continue
            elat=row.get("lat",0); elon=row.get("lon",0)
            if not elat or not elon: continue
            folium.CircleMarker([elat,elon],radius=5,color="#c8bea0",fill=True,
                fill_color="#f0e8d0",fill_opacity=0.7,
                popup=folium.Popup(
                    f"<div style='font-family:-apple-system,sans-serif;padding:8px;min-width:130px'>"
                    f"<b>{nm}</b><br><span style='color:#9a8c72;font-size:11px'>{row.get('type_label','')}</span>"
                    f"</div>",max_width=180),
                tooltip=f"+ {nm}").add_to(m)
    return m

# ════════════════════════════════════════════════════════════════
# HTML EXPORT
# ════════════════════════════════════════════════════════════════
def build_html(itin,city,day_budgets,cc):
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    avg=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 80
    def esc(s): return _ss(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    total_stops=sum(len(v) for v in itin.values() if isinstance(v,list))
    mjs=[];pjs=[];mlats=[];mlons=[]
    for di,(dl,stops) in enumerate(itin.items()):
        if not isinstance(stops,list) or not stops: continue
        c=DAY_COLORS[di%len(DAY_COLORS)];pc=[]
        for si,s in enumerate(stops):
            la=s.get("lat",0);lo=s.get("lon",0)
            if not la or not lo: continue
            mlats.append(la);mlons.append(lo);pc.append(f"[{la},{lo}]")
            mjs.append(f'{{"lat":{la},"lon":{lo},"n":"{esc(s.get("name",""))}","d":{di+1},"s":{si+1},"c":"{c}"}}')
        if len(pc)>1: pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')
    clat=sum(mlats)/len(mlats) if mlats else 35.
    clon=sum(mlons)/len(mlons) if mlons else 139.
    days_html=""
    for di,(dl,stops) in enumerate(itin.items()):
        if not isinstance(stops,list) or not stops: continue
        du=day_budgets[di] if di<len(day_budgets) else avg
        c=DAY_COLORS[di%len(DAY_COLORS)]
        tl_stops=build_timeline(stops)
        rows="".join(
            f"<tr><td>{si+1}</td><td>{esc(s.get('arrive_time',''))}–{esc(s.get('depart_time',''))}</td>"
            f"<td><b>{esc(s.get('name',''))}</b></td><td>{esc(s.get('type_label',''))}</td>"
            f"<td>{fmt_dur(s.get('duration_min',60))}</td>"
            f"<td>{'⭐ '+str(s.get('rating','')) if s.get('rating') else '–'}</td></tr>"
            for si,s in enumerate(tl_stops))
        total_dur=sum(s.get("duration_min",60) for s in tl_stops)
        days_html+=(f"<h3 style='color:{c};margin:24px 0 8px'>{esc(dl)} — {len(stops)} stops · ~{fmt_dur(total_dur)}</h3>"
                    f"<table><thead><tr><th>#</th><th>Time</th><th>Place</th><th>Type</th><th>Duration</th><th>Rating</th></tr></thead><tbody>{rows}</tbody></table>")
    return (f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Voyager — {esc(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{{box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#fcfaf5;color:#18140c;max-width:960px;margin:0 auto;padding:32px 24px}}
h1{{font-family:Georgia,serif;font-size:28px;font-weight:400;color:#18140c;margin:0 0 8px;letter-spacing:-.02em}}
.badge{{display:inline-flex;padding:3px 14px;border-radius:100px;background:rgba(184,148,58,.10);border:1px solid rgba(184,148,58,.30);font-size:11px;color:#8a6c28;font-weight:600;margin-bottom:16px;letter-spacing:.08em;text-transform:uppercase}}
.sum{{background:rgba(184,148,58,.06);border:1px solid rgba(184,148,58,.14);border-radius:12px;padding:12px 18px;font-size:13px;color:#8a6c28;margin-bottom:20px}}
#map{{height:380px;border-radius:16px;margin:20px 0;border:1px solid rgba(0,0,0,.08);box-shadow:0 4px 20px rgba(0,0,0,.08)}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:white;border-radius:12px;overflow:hidden;margin:4px 0;box-shadow:0 1px 6px rgba(0,0,0,.05)}}
thead tr{{background:rgba(184,148,58,.06)}}th,td{{padding:8px 14px;border-bottom:1px solid rgba(0,0,0,.06);text-align:left}}
th{{font-weight:600;color:#8a6c28;font-size:10px;text-transform:uppercase;letter-spacing:.06em}}
tr:hover td{{background:#fdf9f2}}
footer{{color:#c0b090;font-size:11px;margin-top:40px;text-align:center;padding-top:20px;border-top:1px solid rgba(0,0,0,.07)}}
</style></head><body>
<div class="badge">✦ Voyager AI Travel Planner</div>
<h1>✈ {esc(city.title())}</h1>
<div class="sum">${sum(day_budgets[:len(itin)])} total &nbsp;·&nbsp; {len(itin)} days &nbsp;·&nbsp; {total_stops} stops &nbsp;·&nbsp; avg ${avg}/day</div>
<div id="map"></div>{days_html}
<footer>Voyager · Ctrl+P to save as PDF</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
var m=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',{{attribution:'CartoDB'}}).addTo(m);
[{",".join(mjs)}].forEach(function(mk){{
var ic=L.divIcon({{html:'<div style="width:26px;height:26px;border-radius:50%;background:'+mk.c+';border:2px solid white;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:700;box-shadow:0 2px 8px rgba(0,0,0,0.2)">'+mk.s+'</div>',iconSize:[26,26],iconAnchor:[13,13]}});
L.marker([mk.lat,mk.lon],{{icon:ic}}).bindPopup('<b>Day '+mk.d+' #'+mk.s+'</b><br>'+mk.n).addTo(m);
}});
[{",".join(pjs)}].forEach(function(pl){{L.polyline(pl.pts,{{color:pl.c,weight:3,opacity:.7,dashArray:'5 4'}}).addTo(m);}});
</script></body></html>""").encode("utf-8")

# ════════════════════════════════════════════════════════════════
# PROGRESS + TOPBAR
# ════════════════════════════════════════════════════════════════
STEP_LABELS_EN = ["Welcome","Destination","Trip style","Preferences","Overview","Day detail"]
STEP_LABELS_ZH = ["首页","目的地","旅行风格","行程偏好","行程总览","每日规划"]
STEP_ICONS = ["✦","◎","◈","◉","⊞","⊛"]
MAX_STEP = 6

def render_topbar():
    user=_cur_user()
    lang=st.session_state.get("lang","EN")
    labels=STEP_LABELS_EN if lang=="EN" else STEP_LABELS_ZH
    cur=st.session_state.get("step",1)

    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    tc1,tc2,tc3=st.columns([1,4,1])
    with tc1:
        lc1,lc2=st.columns(2,gap="small")
        with lc1:
            if st.button("EN",key="lang_en",use_container_width=True,
                         type="primary" if lang=="EN" else "secondary"):
                st.session_state["lang"]="EN"; st.rerun()
        with lc2:
            if st.button("中文",key="lang_zh",use_container_width=True,
                         type="primary" if lang=="ZH" else "secondary"):
                st.session_state["lang"]="ZH"; st.rerun()
    with tc2:
        st.markdown(f"""<div style="text-align:center;padding:2px 0">
          <span style="font-family:'Playfair Display',Georgia,serif;font-size:17px;
          font-weight:500;color:#52412a;letter-spacing:0.18em">{T("brand")}</span>
          <span style="font-size:10px;color:#b0a080;margin-left:8px;letter-spacing:0.08em">{T("tagline")}</span>
        </div>""", unsafe_allow_html=True)
    with tc3:
        if user:
            st.markdown(f'<div style="text-align:right;font-size:12px;color:#b8943a;font-weight:500;padding:6px 0">◉ {user["username"]}</div>', unsafe_allow_html=True)
            if st.button("Sign out" if lang=="EN" else "退出",key="tb_lo",use_container_width=True):
                try: logout_user(st.session_state.get("_auth_token",""))
                except: pass
                st.session_state.pop("_auth_token",None)
                st.session_state["user_mode"]=None; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Clickable progress bar
    html='<div class="prog-row">'
    for i,(icon,label) in enumerate(zip(STEP_ICONS[:MAX_STEP], labels[:MAX_STEP])):
        n=i+1
        state="done" if n<cur else ("active" if n==cur else "pending")
        circle="✓" if n<cur else icon
        # Clickable only for completed steps
        onclick = f'data-step="{n}"'
        html+=(f'<div class="prog-step" title="{label}" style="{"cursor:pointer" if n<cur else ""}">'
               f'<div class="prog-dot {state}">{circle}</div>'
               f'<div class="prog-lbl {state}">{label}</div></div>')
        if i<MAX_STEP-1:
            lc="done" if n<cur else ""
            html+=f'<div class="prog-line {lc}"></div>'
    html+='</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Clickable step buttons (use columns for clickability)
    if cur > 1:
        step_cols=st.columns(MAX_STEP)
        for i in range(MAX_STEP):
            n=i+1
            if n<cur:
                with step_cols[i]:
                    if st.button(f" ",key=f"jump_{n}",use_container_width=True,
                                 help=labels[i]):
                        st.session_state["step"]=n; st.rerun()

# ════════════════════════════════════════════════════════════════
# SHARED NAV FOOTER
# ════════════════════════════════════════════════════════════════
def nav_footer(back_step=None,next_label=None,next_key="nxt",next_fn=None,
               back_label=None,next_type="primary",extra_cols=None):
    st.markdown("<div style='height:60px'></div>",unsafe_allow_html=True)
    cols=st.columns([1,2,1] if not extra_cols else [1,1,1,1])
    with cols[0]:
        if back_step is not None:
            bl=back_label or T("back")
            if st.button(bl,key=f"back_{back_step}",use_container_width=True):
                st.session_state["step"]=back_step; st.rerun()
    with cols[-1] if not extra_cols else cols[2]:
        if next_label:
            if st.button(next_label,key=next_key,use_container_width=True,type=next_type):
                if next_fn: next_fn()
    if extra_cols:
        for ec_i,(ec_lbl,ec_fn,ec_key) in enumerate(extra_cols):
            with cols[ec_i+1]:
                if st.button(ec_lbl,key=ec_key,use_container_width=True):
                    ec_fn()

# ════════════════════════════════════════════════════════════════
# STEP 1 — WELCOME
# ════════════════════════════════════════════════════════════════
def step_1():
    render_topbar()
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown(f"""<div style="text-align:center;padding:20px 0 32px">
      <div style="font-family:'Playfair Display',Georgia,serif;font-size:34px;font-weight:500;
      color:#18140c;letter-spacing:-0.02em;line-height:1.2;margin-bottom:10px">
        {T("welcome_h")}
      </div>
      <div style="font-size:15px;color:#9a8c72;line-height:1.65">{T("welcome_sub")}</div>
    </div>""", unsafe_allow_html=True)

    c1,c2=st.columns(2,gap="medium")
    with c1:
        st.markdown(f"""<div class="gold-card" style="padding:24px;text-align:center;min-height:200px;margin-bottom:12px">
          <div style="font-size:30px;margin-bottom:10px">◉</div>
          <div style="font-weight:600;font-size:16px;color:#18140c;margin-bottom:6px">{T("signin")}</div>
          <div style="font-size:12px;color:#9a8c72;line-height:1.8">
            {T("wishlist_h")} &nbsp;·&nbsp; {T("collab_h")}<br>Saved trips &nbsp;·&nbsp; Points
          </div>
        </div>""", unsafe_allow_html=True)
        if AUTH_OK:
            with st.form("lf",clear_on_submit=False):
                u=st.text_input("",placeholder=T("username_ph"),key="li_u",label_visibility="collapsed")
                p=st.text_input("",placeholder=T("password_ph"),type="password",key="li_p",label_visibility="collapsed")
                if st.form_submit_button(T("signin"),use_container_width=True):
                    if u.strip() and p:
                        ok,msg,tok=login_user(u.strip(),p)
                        if ok:
                            st.session_state["_auth_token"]=tok
                            st.session_state["user_mode"]="logged_in"
                            if POINTS_OK:
                                try: add_points(u.strip(),"daily_login")
                                except: pass
                            st.session_state["step"]=2; st.rerun()
                        else: st.error(msg)
                    else: st.warning(T("username_ph"))
            with st.expander(T("register")):
                with st.form("rf"):
                    ru=st.text_input("",placeholder=T("reg_u_ph"),key="re_u",label_visibility="collapsed")
                    re_e=st.text_input("",placeholder=T("email_ph"),key="re_e",label_visibility="collapsed")
                    rp=st.text_input("",placeholder=T("reg_p_ph"),type="password",key="re_p",label_visibility="collapsed")
                    if st.form_submit_button(T("register"),use_container_width=True):
                        ok,msg=register_user(ru.strip(),rp,re_e.strip())
                        (st.success if ok else st.error)(msg)
        else:
            if st.button(T("signin"),use_container_width=True,type="primary",key="li_demo"):
                st.session_state["user_mode"]="logged_in"; st.session_state["step"]=2; st.rerun()

    with c2:
        st.markdown(f"""<div class="ios-card" style="padding:24px;text-align:center;min-height:200px;margin-bottom:12px">
          <div style="font-size:30px;margin-bottom:10px">◎</div>
          <div style="font-weight:600;font-size:16px;color:#18140c;margin-bottom:6px">{T("guest_btn")}</div>
          <div style="font-size:12px;color:#9a8c72;line-height:1.9">
            {"<br>".join("✦ "+f for f in T("guest_perks"))}
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button(T("guest_btn"),key="guest_go",use_container_width=True,type="primary"):
            st.session_state["user_mode"]="guest"; st.session_state["step"]=2; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# STEP 2 — DESTINATION (country first → multi-city)
# ════════════════════════════════════════════════════════════════
def step_2():
    render_topbar()
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown(f'<div class="h1">{T("where_h")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub">{T("where_sub")}</div>', unsafe_allow_html=True)

    # ── Row 1: Country (full width) ──
    all_countries=[""] + sorted(WORLD_CITIES.keys())
    prev_cc=st.session_state.get("dest_countries",[None])[0] or ""
    sel_cc=st.selectbox(T("select_country"), all_countries,
                        index=all_countries.index(prev_cc) if prev_cc in all_countries else 0,
                        key="s2_country")

    # ── Row 2: Multi-city picker ──
    sel_cities=list(st.session_state.get("dest_cities",[]))
    if sel_cc:
        st.markdown(f'<span class="sec-label">{T("select_cities")}</span>', unsafe_allow_html=True)
        avail_cities=WORLD_CITIES.get(sel_cc,[])
        # Show as grid of toggle buttons
        city_rows=[avail_cities[i:i+5] for i in range(0,len(avail_cities),5)]
        for row in city_rows:
            rcols=st.columns(len(row))
            for ci,city in enumerate(row):
                with rcols[ci]:
                    is_sel=city in sel_cities
                    if st.button(("✓ " if is_sel else "")+city,key=f"cp_{city}",
                                 use_container_width=True,type="primary" if is_sel else "secondary"):
                        if is_sel: sel_cities.remove(city)
                        else: sel_cities.append(city)
                        st.session_state["dest_cities"]=sel_cities
                        st.session_state["dest_countries"]=[sel_cc]; st.rerun()
        # Show selected
        if sel_cities:
            pills=" ".join(f'<span class="city-pill-sel">✓ {c}</span>' for c in sel_cities)
            st.markdown(f'<div style="margin:10px 0 4px">{pills}</div>', unsafe_allow_html=True)

    # ── Custom city search ──
    st.markdown(f'<span class="sec-label" style="margin-top:16px">{T("popular_h")}</span>', unsafe_allow_html=True)
    city_ov=st.text_input("",placeholder=T("cities_ph"),key="s2_ov",label_visibility="collapsed")

    # ── Popular row (fixed 4, refresh-able) ──
    pop_row=st.session_state.get("pop_row",0)
    chunk=POPULAR_ROWS[pop_row%len(POPULAR_ROWS)]
    pcols=st.columns(len(chunk)+1)
    for ci,(icon,city,country) in enumerate(chunk):
        with pcols[ci]:
            is_sel=city in sel_cities
            if st.button(f"{icon} {city}",key=f"pop_{city}_{pop_row}",
                         use_container_width=True,type="primary" if is_sel else "secondary"):
                if is_sel: sel_cities.remove(city)
                else:
                    sel_cities.append(city)
                    if not st.session_state.get("dest_countries"): st.session_state["dest_countries"]=[country]
                st.session_state["dest_cities"]=sel_cities; st.rerun()
    with pcols[-1]:
        if st.button("↺",key="pop_rf",use_container_width=True,help="Refresh"):
            st.session_state["pop_row"]=(pop_row+1)%len(POPULAR_ROWS); st.rerun()

    # Selected summary
    custom_city=city_ov.strip()
    all_sel=list(sel_cities)
    if custom_city and custom_city not in all_sel: all_sel.append(custom_city)
    if all_sel:
        cc_name=st.session_state.get("dest_countries",[""])[0] if not custom_city else sel_cc or ""
        st.markdown(f"""<div style="margin-top:18px;padding:14px 18px;
          background:linear-gradient(135deg,rgba(184,148,58,0.09),rgba(184,148,58,0.04));
          border:1px solid rgba(184,148,58,0.24);border-radius:14px;
          display:flex;align-items:center;gap:12px">
          <span style="font-size:22px">✈️</span>
          <div>
            <div style="font-weight:600;font-size:15px;color:#18140c">{" + ".join(all_sel)}</div>
            <div style="font-size:11px;color:#b8943a">{cc_name}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Nav
    nc1,_,nc2=st.columns([1,2,1])
    with nc1:
        if st.button(T("back"),key="s2_back",use_container_width=True):
            st.session_state["step"]=1; st.rerun()
    with nc2:
        if st.button(T("next"),key="s2_next",use_container_width=True,type="primary"):
            if not all_sel: st.warning(T("select_country")); return
            # Geocode first city
            primary=all_sel[0]
            ck=primary.strip().lower()
            cc_name=st.session_state.get("dest_countries",[""])[0] if not custom_city else sel_cc or ""
            cc=COUNTRY_CODES.get(cc_name,"INT")
            is_cn=ck in CN_CITIES
            intl=INTL_CITIES.get(ck)
            if is_cn: lat,lon=CN_CITIES[ck]
            elif intl: lat,lon,cc=intl[0],intl[1],intl[2]
            else:
                with st.spinner(T("locating")):
                    coord=_nom(primary)
                    if not coord: st.error(f"Cannot find '{primary}'."); return
                    lat,lon=coord
            st.session_state.update({
                "dest_city":primary,"dest_cities":all_sel,"dest_countries":[cc_name],
                "dest_lat":lat,"dest_lon":lon,"dest_cc":cc,"dest_is_cn":is_cn
            })
            st.session_state["step"]=3; st.rerun()

# ════════════════════════════════════════════════════════════════
# STEP 3 — TRIP TYPE
# ════════════════════════════════════════════════════════════════
def step_3():
    render_topbar()
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown(f'<div class="h1">{T("trip_type_h")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub">{T("trip_type_sub")}</div>', unsafe_allow_html=True)

    cur_tt=st.session_state.get("trip_type","VALUE")
    cols=st.columns(3,gap="medium")
    for i,(code,icon) in enumerate(TRIP_TYPES):
        with cols[i%3]:
            is_sel=(code==cur_tt)
            title=T(code); sub=T(f"{code}_sub")
            st.markdown(f"""<div class="tt-card {'sel' if is_sel else ''}" style="margin-bottom:8px">
              <div class="tt-icon">{icon}</div>
              <div class="tt-title">{title}</div>
              <div class="tt-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(("✓ Selected" if (st.session_state.get("lang","EN")=="EN") else "✓ 已选") if is_sel else title,
                         key=f"tt_{code}",use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["trip_type"]=code; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    nc1,_,nc2=st.columns([1,2,1])
    with nc1:
        if st.button(T("back"),key="s3_back",use_container_width=True):
            st.session_state["step"]=2; st.rerun()
    with nc2:
        if st.button(T("next"),key="s3_next",use_container_width=True,type="primary"):
            st.session_state["step"]=4; st.rerun()

# ════════════════════════════════════════════════════════════════
# STEP 4 — PREFERENCES (per-day, spacious)
# ════════════════════════════════════════════════════════════════
def step_4():
    render_topbar()
    city=st.session_state.get("dest_city","")
    cc=st.session_state.get("dest_cc","INT")
    tt=st.session_state.get("trip_type","VALUE")
    tt_mod=TRIP_TYPE_MODS.get(tt,{})
    preferred_types=tt_mod.get("preferred",[])

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown(f'<div class="h1">{T("pref_h")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub">{T("pref_sub")}</div>', unsafe_allow_html=True)

    # Duration + Budget in their own clear row
    da,db=st.columns(2,gap="large")
    with da:
        days=st.number_input(T("duration_label"),1,14,
                             st.session_state.get("trip_days",3),1,key="s4_days")
    with db:
        base_bud=st.slider(T("budget_label"),20,500,
                           st.session_state.get("trip_budget",100),5,format="$%d",key="s4_bud")
        sym,rate=local_rate(cc)
        st.markdown(f'<div style="font-size:11px;color:#b8943a;margin-top:2px">≈ {sym}{round(base_bud*rate):,} {T("per_day_est")}</div>',unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

    # Interests
    st.markdown(f'<span class="sec-label">{T("interests_h")}</span>',unsafe_allow_html=True)
    sel_types=list(st.session_state.get("trip_types",["🏛️ Attraction","🍜 Restaurant"]))
    # Pre-select preferred based on trip type
    if preferred_types:
        for pt in preferred_types:
            if pt not in sel_types: sel_types.append(pt)
    type_list=list(PTYPES.keys())
    it_cols=st.columns(4,gap="small")
    for ti,tl in enumerate(type_list):
        with it_cols[ti%4]:
            is_sel=tl in sel_types
            if st.button(("✓ " if is_sel else "")+tl,key=f"tp_{tl}",
                         use_container_width=True,type="primary" if is_sel else "secondary"):
                if is_sel and len(sel_types)>1: sel_types.remove(tl)
                elif not is_sel: sel_types.append(tl)
                st.session_state["trip_types"]=sel_types; st.rerun()

    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

    # Must-visit
    st.markdown(f'<span class="sec-label">{T("must_visit_h")}</span>',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:12px;color:#9a8c72;margin-bottom:10px">{T("must_visit_sub")}</div>',unsafe_allow_html=True)
    custom_places=list(st.session_state.get("custom_places",[]))
    for ci,cp in enumerate(custom_places):
        cc1,cc2=st.columns([5,1],gap="small")
        with cc1:
            st.markdown(f"""<div style="padding:10px 14px;background:rgba(184,148,58,0.06);
              border:1px solid rgba(184,148,58,0.20);border-radius:10px;
              font-size:13px;color:#52412a;display:flex;align-items:center;gap:8px">
              <span>📍</span> <span style="font-weight:500">{_ss(cp.get("name",""))}</span>
            </div>""",unsafe_allow_html=True)
        with cc2:
            if st.button("✕",key=f"rm_cp_{ci}",use_container_width=True):
                custom_places.pop(ci); st.session_state["custom_places"]=custom_places; st.rerun()
    np1,np2=st.columns([5,1],gap="small")
    with np1:
        new_place=st.text_input("",placeholder=T("add_ph"),key="new_cp",label_visibility="collapsed")
    with np2:
        if st.button(T("add_btn"),key="add_cp",use_container_width=True,type="primary"):
            if new_place.strip():
                custom_places.append({"name":new_place.strip(),"lat":0,"lon":0,
                                       "type_label":"🏛️ Attraction","rating":5.0,
                                       "address":"","district":"Custom","description":"User added"})
                st.session_state["custom_places"]=custom_places; st.rerun()

    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

    # Per-day — SPACIOUS: full expander per day
    st.markdown(f'<span class="sec-label">{T("per_day_h")}</span>',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:12px;color:#9a8c72;margin-bottom:12px">{T("per_day_sub")}</div>',unsafe_allow_html=True)
    int_days=int(days)
    day_configs=dict(st.session_state.get("day_configs",{}))
    # Apply trip-type quota multiplier
    mul=tt_mod.get("quota_mul",1.0)
    for di in range(int_days):
        dk=f"Day {di+1}"
        cfg=day_configs.get(dk,{"budget":int(base_bud),"quotas":{}})
        with st.expander(f"📅 {dk}",expanded=(di==0)):
            st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
            d_bud=st.slider(T("day_budget"),20,500,int(cfg.get("budget",base_bud)),5,
                            format="$%d",key=f"db_{di}")
            st.markdown(f'<span class="sec-label" style="margin-top:12px;display:block">{T("stops_label")}</span>',unsafe_allow_html=True)
            quotas={}
            q_cols=st.columns(min(len(sel_types),3),gap="medium")
            for tci,tl in enumerate(sel_types):
                with q_cols[tci%min(len(sel_types),3)]:
                    def_q=int(round(cfg.get("quotas",{}).get(tl,1)*mul)) if mul!=1.0 else cfg.get("quotas",{}).get(tl,1)
                    def_q=max(0,min(5,int(def_q)))
                    n=st.number_input(tl,0,5,def_q,1,key=f"q_{di}_{tl}")
                    if n>0: quotas[tl]=n
            if not quotas and sel_types: quotas={sel_types[0]:1}
            day_configs[dk]={"budget":d_bud,"quotas":quotas}
        st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)

    # Logistics
    with st.expander(T("logistics_h"),expanded=False):
        lo1,lo2=st.columns(2,gap="medium")
        with lo1:
            st.text_input("",placeholder=T("start_ph"),key="s4_dep",label_visibility="collapsed")
            st.text_input("",placeholder=T("hotel_ph"),key="s4_hotel",label_visibility="collapsed")
        with lo2:
            st.text_input("",placeholder=T("end_ph"),key="s4_arr",label_visibility="collapsed")

    st.markdown("</div>",unsafe_allow_html=True)

    nc1,_,nc2=st.columns([1,2,1])
    with nc1:
        if st.button(T("back"),key="s4_back",use_container_width=True):
            st.session_state["step"]=3; st.rerun()
    with nc2:
        if st.button(T("build_btn"),key="s4_build",use_container_width=True,type="primary"):
            if not sel_types: st.warning(T("interests_h")); return
            st.session_state.update({
                "trip_days":int_days,"trip_budget":int(base_bud),
                "trip_types":sel_types,"day_configs":day_configs,
                "trip_depart":st.session_state.get("s4_dep",""),
                "trip_arrive":st.session_state.get("s4_arr",""),
                "trip_hotel":st.session_state.get("s4_hotel",""),
            })
            _generate_itinerary()

# ════════════════════════════════════════════════════════════════
# GENERATE
# ════════════════════════════════════════════════════════════════
def _generate_itinerary():
    city=st.session_state["dest_city"]; lat=st.session_state["dest_lat"]
    lon=st.session_state["dest_lon"]; cc=st.session_state["dest_cc"]
    is_cn=st.session_state.get("dest_is_cn",False)
    ndays=st.session_state["trip_days"]
    day_configs=st.session_state.get("day_configs",{})
    custom_places=st.session_state.get("custom_places",[])
    tt=st.session_state.get("trip_type","VALUE")
    tt_mod=TRIP_TYPE_MODS.get(tt,{})
    min_rating=tt_mod.get("min_rating",3.8)

    day_quotas=[]; day_budgets=[]
    for d in range(ndays):
        dk=f"Day {d+1}"; cfg=day_configs.get(dk,{})
        day_budgets.append(int(cfg.get("budget",st.session_state.get("trip_budget",100))))
        q=cfg.get("quotas",{})
        if not q: q={st.session_state.get("trip_types",["🏛️ Attraction"])[0]:1}
        day_quotas.append(q)

    sel_types=st.session_state.get("trip_types",["🏛️ Attraction"])
    total_q=sum(sum(q.values()) for q in day_quotas)
    lpt=max(20,total_q*5)

    lang=st.session_state.get("lang","EN")
    find_msg=f"{T('finding')} {city}…" if lang=="EN" else f"正在搜索 {city} 的好去处…"
    with st.spinner(find_msg):
        try: df,warn=fetch_places(lat,lon,cc,is_cn,tuple(sel_types),lpt,st.session_state.get("seed",42))
        except Exception as e: st.error(f"Search error: {e}"); return

    if warn: st.info(warn)
    if df is None or df.empty: st.error(T("no_places")); return

    # Inject custom
    if custom_places:
        cp_rows=[]
        for cp in custom_places:
            if not cp.get("lat"):
                with st.spinner(T("locating")):
                    coord=_nom(f"{cp['name']} {city}") or _nom(cp["name"])
                    if coord: cp["lat"],cp["lon"]=coord[0],coord[1]
                    else: cp["lat"]=lat+random.uniform(-.01,.01); cp["lon"]=lon+random.uniform(-.01,.01)
            cp_rows.append(cp)
        cp_df=pd.DataFrame(cp_rows)
        for c in df.columns:
            if c not in cp_df.columns: cp_df[c]=""
        cp_df["rating"]=5.0
        df=pd.concat([cp_df,df],ignore_index=True)

    def _gc(addr):
        if not addr: return None
        if is_cn: return _amap_geo(f"{addr} {city}") or _nom(f"{addr} {city}")
        return _nom(f"{addr} {city}") or _nom(addr)

    hotel_c=depart_c=arrive_c=None
    with st.spinner(T("locating")):
        hotel_c=_gc(st.session_state.get("trip_hotel",""))
        depart_c=_gc(st.session_state.get("trip_depart",""))
        arrive_c=_gc(st.session_state.get("trip_arrive",""))

    itin={}
    if AI_OK:
        with st.spinner(T("building")):
            try:
                itin=generate_itinerary(df,ndays,day_quotas,
                    hotel_lat=hotel_c[0] if hotel_c else None,hotel_lon=hotel_c[1] if hotel_c else None,
                    depart_lat=depart_c[0] if depart_c else None,depart_lon=depart_c[1] if depart_c else None,
                    arrive_lat=arrive_c[0] if arrive_c else None,arrive_lon=arrive_c[1] if arrive_c else None,
                    day_min_ratings=[min_rating]*ndays,day_anchor_lats=[lat]*ndays,day_anchor_lons=[lon]*ndays,
                    country=cc,city=city,day_budgets=day_budgets)
            except Exception as e: st.error(f"Itinerary error: {e}")

    if not itin:
        used=set()
        for d in range(ndays):
            dk=f"Day {d+1}"; stops=[]; q=day_quotas[d]
            for tl,cnt in q.items():
                pool=df[(df["type_label"]==tl)&(~df["name"].isin(used))].head(cnt)
                for _,row in pool.iterrows(): stops.append(row.to_dict()); used.add(row["name"])
            itin[dk]=stops

    # Ensure custom in itin
    if custom_places:
        in_itin={s.get("name","") for sl in itin.values() if isinstance(sl,list) for s in sl}
        for cp in custom_places:
            if cp["name"] not in in_itin:
                d1=list(itin.keys())[0] if itin else "Day 1"
                itin.setdefault(d1,[]).insert(0,{**cp,"time_slot":"TBD","transport_to_next":None})

    st.session_state["_itin"]=itin; st.session_state["_df"]=df
    st.session_state["day_budgets"]=day_budgets
    st.session_state["active_day"]=None; st.session_state["ai_chat"]=[]

    user=_cur_user()
    if user:
        _save_itin(user["username"],itin,city,city.title())
        if POINTS_OK:
            try: add_points(user["username"],"share",note=city)
            except: pass

    st.session_state["step"]=5; st.rerun()

# ════════════════════════════════════════════════════════════════
# STEP 5 — OVERVIEW
# ════════════════════════════════════════════════════════════════
def step_5():
    render_topbar()
    city=st.session_state.get("dest_city","")
    cc=st.session_state.get("dest_cc","INT")
    lat=st.session_state.get("dest_lat",35.)
    lon=st.session_state.get("dest_lon",139.)
    ndays=st.session_state.get("trip_days",3)
    day_budgets=st.session_state.get("day_budgets",[100]*ndays)
    itin=dict(st.session_state.get("_itin",{}))
    df=st.session_state.get("_df",pd.DataFrame())
    user=_cur_user()
    lang=st.session_state.get("lang","EN")

    total_stops=sum(len(v) for v in itin.values() if isinstance(v,list))

    st.markdown('<div class="page-wrap-wide">', unsafe_allow_html=True)

    # Header row
    hc1,hc2=st.columns([3,2],gap="medium")
    with hc1:
        cities_str=" + ".join(st.session_state.get("dest_cities",[city]))
        st.markdown(f"""<div>
          <span class="sec-label">{T("overview_h")}</span>
          <div class="h1">{cities_str}</div>
          <div style="font-size:13px;color:#9a8c72;margin-top:4px">
            {ndays} {T("days_lbl")} · {total_stops} {T("stops_lbl")} · avg ${round(sum(day_budgets)/len(day_budgets)) if day_budgets else 0}/{T("per_day_est")}
          </div>
        </div>""", unsafe_allow_html=True)
    with hc2:
        ba,bb,bc=st.columns(3,gap="small")
        with ba:
            if st.button(T("edit_prefs"),key="s5_back",use_container_width=True):
                st.session_state["step"]=4; st.rerun()
        with bb:
            if st.button(T("shuffle"),key="s5_shuf",use_container_width=True):
                st.session_state["seed"]=random.randint(1,99999)
                st.cache_data.clear(); _generate_itinerary()
        with bc:
            if itin:
                try:
                    hd=build_html(itin,city,day_budgets,cc)
                    st.download_button(T("export"),data=hd,
                        file_name=f"voyager_{city.lower().replace(' ','_')}.html",
                        mime="text/html;charset=utf-8",use_container_width=True)
                except: pass

    st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)

    # Metrics
    m1,m2,m3,m4=st.columns(4)
    m1.metric(T("days_lbl").upper(),str(ndays))
    m2.metric(T("stops_lbl").upper(),str(total_stops))
    m3.metric("AVG ⭐","%.1f"%df["rating"].replace(0,float("nan")).mean() if df is not None and not df.empty else "—")
    m4.metric(T("total_lbl").upper(),f"${sum(day_budgets)}")

    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)

    # Overview map (planned stops only) + Day list
    map_col,days_col=st.columns([2,3],gap="medium")
    with map_col:
        st.markdown('<span class="sec-label">Overview map</span>',unsafe_allow_html=True)
        if FOLIUM_OK and df is not None and not df.empty:
            m=build_map(df,lat,lon,itin,active_day=None,zoom=12,planned_only=True)
            if m:
                st.markdown('<div class="map-wrap">',unsafe_allow_html=True)
                st_folium(m,width="100%",height=300,returned_objects=[])
                st.markdown("</div>",unsafe_allow_html=True)
        else:
            st.caption("Map requires streamlit-folium")

    with days_col:
        # Reorder days header
        st.markdown(f'<span class="sec-label">{T("tap_day")} · {T("reorder_days_h")}</span>',unsafe_allow_html=True)
        all_days=list(itin.keys())
        for di,dk in enumerate(all_days):
            stops=itin.get(dk,[])
            if not isinstance(stops,list): continue
            color=DAY_COLORS[di%len(DAY_COLORS)]
            d_bud=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
            tl_stops=build_timeline(stops)
            total_dur=sum(s.get("duration_min",60) for s in tl_stops)
            preview=" · ".join(_ss(s.get("name",""))[:18] for s in stops[:3])
            if len(stops)>3: preview+=f" +{len(stops)-3}"

            dc1,dc2,dc3=st.columns([4,1,1],gap="small")
            with dc1:
                st.markdown(f"""<div class="day-ov-card" style="border-left:3px solid {color}">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                    <div style="width:28px;height:28px;border-radius:50%;background:{color};flex-shrink:0;
                    display:flex;align-items:center;justify-content:center;
                    font-size:12px;font-weight:700;color:white">{di+1}</div>
                    <div>
                      <span style="font-weight:600;font-size:14px;color:#18140c">{dk}</span>
                      <span style="font-size:11px;color:#9a8c72;margin-left:8px">{len(stops)} stops · ${d_bud} · ~{fmt_dur(total_dur)}</span>
                    </div>
                  </div>
                  <div style="font-size:12px;color:#9a8c72">{preview}</div>
                </div>""", unsafe_allow_html=True)
            with dc2:
                st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
                mv1,mv2=st.columns(2,gap="small")
                with mv1:
                    if di>0 and st.button("↑",key=f"day_up_{di}",use_container_width=True):
                        ks=list(itin.keys()); ks[di],ks[di-1]=ks[di-1],ks[di]
                        new_itin={k:itin[k] for k in ks}
                        db2=list(day_budgets)
                        if di<len(db2) and di-1<len(db2): db2[di],db2[di-1]=db2[di-1],db2[di]
                        st.session_state["_itin"]=new_itin; st.session_state["day_budgets"]=db2; st.rerun()
                with mv2:
                    if di<len(all_days)-1 and st.button("↓",key=f"day_dn_{di}",use_container_width=True):
                        ks=list(itin.keys()); ks[di],ks[di+1]=ks[di+1],ks[di]
                        new_itin={k:itin[k] for k in ks}
                        db2=list(day_budgets)
                        if di<len(db2) and di+1<len(db2): db2[di],db2[di+1]=db2[di+1],db2[di]
                        st.session_state["_itin"]=new_itin; st.session_state["day_budgets"]=db2; st.rerun()
            with dc3:
                st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
                if st.button(T("plan_btn"),key=f"plan_{dk}",use_container_width=True,type="primary"):
                    st.session_state["active_day"]=dk; st.session_state["step"]=6; st.rerun()

    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)

    # ── Guest CTA ──
    if st.session_state.get("user_mode")=="guest" and AUTH_OK:
        st.markdown(f"""<div class="guest-cta">
          <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
            <div style="flex:1;min-width:200px">
              <div style="font-weight:600;font-size:15px;color:#18140c;margin-bottom:4px">{T("guest_cta_h")}</div>
              <div style="font-size:13px;color:#9a8c72">{T("guest_cta_body")}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        gc1,_=st.columns([1,2])
        with gc1:
            if st.button(T("guest_cta_btn"),key="guest_cta_go",use_container_width=True,type="primary"):
                st.session_state["step"]=1; st.rerun()

    # ── Logged-in extras ──
    if user:
        wl=_wl_get_fn(user["username"])
        with st.expander(f"♥ {T('wishlist_h')} ({len(wl)})",expanded=False):
            if not wl:
                st.markdown(f'<div style="font-size:13px;color:#9a8c72;padding:8px">{T("wishlist_empty")}</div>',unsafe_allow_html=True)
            else:
                day_keys=list(itin.keys())
                for wi,wp in enumerate(wl):
                    wc1,wc2,wc3,wc4=st.columns([3,2,1,1],gap="small")
                    with wc1:
                        st.markdown(f'<div style="font-size:13px;font-weight:500;color:#18140c;padding:6px 0">📍 {_ss(wp.get("name",""))}</div>',unsafe_allow_html=True)
                    with wc2:
                        if day_keys:
                            sel_d=st.selectbox("",["–"]+day_keys,key=f"wl_d_{wi}",label_visibility="collapsed")
                    with wc3:
                        if day_keys and sel_d!="–":
                            if st.button(T("add_btn"),key=f"wl_add_{wi}",use_container_width=True,type="primary"):
                                sl=list(itin.get(sel_d,[]))
                                nm=wp.get("name","")
                                if nm not in {s.get("name","") for s in sl}:
                                    sl.append({**wp,"time_slot":"TBD","transport_to_next":None})
                                    ni=dict(itin); ni[sel_d]=sl
                                    st.session_state["_itin"]=ni; st.toast(f"Added {nm}"); st.rerun()
                    with wc4:
                        if st.button("✕",key=f"wl_rm_{wi}",use_container_width=True):
                            _wl_rm_fn(user["username"],wp.get("name","")); st.rerun()

        with st.expander(f"🤝 {T('collab_h')}",expanded=False):
            st.markdown(f'<div style="font-size:12px;color:#9a8c72;margin-bottom:12px">{T("collab_sub")}</div>',unsafe_allow_html=True)
            cb1,cb2=st.columns(2,gap="medium")
            with cb1:
                if st.button(T("gen_link"),use_container_width=True,type="primary"):
                    import uuid
                    try:
                        tok=create_collab_link(user["username"],str(uuid.uuid4())[:8])
                        st.session_state["collab_code"]=tok
                    except Exception as e: st.error(str(e))
                if st.session_state.get("collab_code"):
                    st.markdown(f'<div class="collab-code">{st.session_state["collab_code"]}</div>',unsafe_allow_html=True)
            with cb2:
                jc=st.text_input("",placeholder=T("join_ph"),key="jc_inp",label_visibility="collapsed")
                if st.button(T("join_btn"),use_container_width=True) and jc:
                    try:
                        ok,msg=join_collab(user["username"],jc.upper())
                        (st.success if ok else st.error)(msg)
                    except Exception as e: st.error(str(e))
        if st.button(T("save_itin"),key="s5_save",use_container_width=True):
            _save_itin(user["username"],itin,city,city.title())
            st.toast(f"Saved!" if lang=="EN" else "已保存！")

    st.markdown("</div>",unsafe_allow_html=True)
    _render_ai(city,itin,lang)

# ════════════════════════════════════════════════════════════════
# STEP 6 — DAY DETAIL
# ════════════════════════════════════════════════════════════════
def step_6():
    render_topbar()
    dk=st.session_state.get("active_day","Day 1")
    city=st.session_state.get("dest_city","")
    cc=st.session_state.get("dest_cc","INT")
    lat=st.session_state.get("dest_lat",35.)
    lon=st.session_state.get("dest_lon",139.)
    itin=dict(st.session_state.get("_itin",{}))
    df=st.session_state.get("_df",pd.DataFrame())
    day_budgets=list(st.session_state.get("day_budgets",[100]))
    user=_cur_user()
    lang=st.session_state.get("lang","EN")

    all_days=list(itin.keys())
    di=all_days.index(dk) if dk in all_days else 0
    color=DAY_COLORS[di%len(DAY_COLORS)]
    d_bud=day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
    stops=list(itin.get(dk,[]))

    st.markdown('<div class="page-wrap-wide">', unsafe_allow_html=True)

    # Top nav
    tn1,tn2,tn3=st.columns([1,3,1],gap="small")
    with tn1:
        if st.button(T("back"),key="s6_back_top",use_container_width=True):
            # SAVE before leaving
            itin[dk]=stops; st.session_state["_itin"]=itin
            st.session_state["step"]=5; st.rerun()
    with tn2:
        st.markdown(f"""<div style="text-align:center;padding:4px 0">
          <span style="font-weight:700;font-size:18px;color:#18140c">{dk}</span>
          <span style="font-size:13px;color:#b8943a;margin-left:8px">— {city.title()}</span>
        </div>""",unsafe_allow_html=True)
    with tn3:
        sel_dk=st.selectbox("",all_days,index=di,key="day_sw",label_visibility="collapsed")
        if sel_dk!=dk:
            itin[dk]=stops; st.session_state["_itin"]=itin
            st.session_state["active_day"]=sel_dk; st.rerun()

    # Budget bar
    sym,rate=local_rate(cc)
    total_est=sum(max(COST_FL.get(s.get("type_label",""),2),
                      d_bud*COST_W.get(s.get("type_label",""),.12)/2) for s in stops)
    pct=min(100,round(total_est/d_bud*100)) if d_bud>0 else 0
    bar_c="#b8943a" if pct<=100 else "#c0584a"
    st.markdown(f"""<div class="ios-card" style="padding:14px 18px;margin:12px 0">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-size:13px;font-weight:500;color:#52472e">{T("budget_label")}</span>
        <span style="font-size:13px;color:{bar_c};font-weight:600">~${round(total_est)} / ${d_bud}</span>
      </div>
      <div class="bud-track">
        <div class="bud-fill" style="width:{pct}%;background:{bar_c}"></div>
      </div>
    </div>""",unsafe_allow_html=True)

    # Split: list | map
    list_col,map_col=st.columns([1,1],gap="medium")
    tl_stops=build_timeline(stops)

    with list_col:
        st.markdown(f'<span class="sec-label">{T("schedule_h")} · {len(stops)} stops · ~{fmt_dur(sum(s.get("duration_min",60) for s in tl_stops))}</span>',unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:11px;color:#c0b090;margin-bottom:8px">{T("reorder_hint")}</div>',unsafe_allow_html=True)

        for si,s in enumerate(tl_stops):
            nm=_ss(s.get("name","")); tl=_ss(s.get("type_label",""))
            rat=s.get("rating",0); arr=s.get("arrive_time",""); dep=s.get("depart_time","")
            dur=s.get("duration_min",60); tr=s.get("transport_to_next") or {}
            cs=cost_est(tl,d_bud,cc); is_custom=s.get("district","")=="Custom"

            sc1,sc2,sc3=st.columns([1,6,1],gap="small")
            with sc1:
                if si>0 and st.button("↑",key=f"up_{dk}_{si}",use_container_width=True):
                    stops[si],stops[si-1]=stops[si-1],stops[si]
                    itin[dk]=stops; st.session_state["_itin"]=itin; st.rerun()
                if si<len(stops)-1 and st.button("↓",key=f"dn_{dk}_{si}",use_container_width=True):
                    stops[si],stops[si+1]=stops[si+1],stops[si]
                    itin[dk]=stops; st.session_state["_itin"]=itin; st.rerun()
            with sc2:
                cust_tag=f'<span style="background:rgba(184,148,58,0.12);border:1px solid rgba(184,148,58,0.28);border-radius:100px;padding:1px 7px;font-size:10px;color:#b8943a;margin-left:6px">custom</span>' if is_custom else ""
                tr_html=f'<div style="margin-top:5px"><span style="font-size:11px;color:#4a7aaa;background:rgba(74,122,170,0.08);border:1px solid rgba(74,122,170,0.15);border-radius:100px;padding:2px 9px">🚇 {_ss(tr.get("mode",""))} · {_ss(tr.get("duration",""))}</span></div>' if tr else ""
                st.markdown(f"""<div class="stop-card" style="border-left:3px solid {color}">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <div style="width:24px;height:24px;border-radius:50%;background:{color};flex-shrink:0;
                    display:flex;align-items:center;justify-content:center;
                    font-size:11px;font-weight:700;color:white">{si+1}</div>
                    <span style="font-weight:600;font-size:14px;color:#18140c">{nm}</span>{cust_tag}
                  </div>
                  <div style="font-size:12px;color:#9a8c72">{tl}{'&nbsp;·&nbsp;⭐ '+str(rat) if rat else ''}</div>
                  <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:5px;align-items:center">
                    {'<span style="font-size:11px;color:#52472e;background:rgba(0,0,0,0.05);border-radius:100px;padding:2px 9px">⏰ '+arr+'–'+dep+'</span>' if arr else ''}
                    <span style="font-size:11px;color:#b8943a">⏱ {fmt_dur(dur)}</span>
                    <span style="font-size:11px;color:#9a8c72">💰 {cs}</span>
                  </div>
                  {tr_html}
                </div>""",unsafe_allow_html=True)
            with sc3:
                st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
                if st.button("✕",key=f"rm_{dk}_{si}",use_container_width=True):
                    stops.pop(si); itin[dk]=stops; st.session_state["_itin"]=itin; st.rerun()
                if user:
                    saved=_wl_chk_fn(user["username"],nm)
                    if st.button("♥" if saved else "♡",key=f"wl_{dk}_{si}",use_container_width=True):
                        if saved: _wl_rm_fn(user["username"],nm); st.toast("Removed")
                        else:
                            _wl_add_fn(user["username"],{"name":nm,"lat":s.get("lat",0),"lon":s.get("lon",0),"type_label":tl,"rating":rat,"address":s.get("address","")})
                            st.toast("♥")
                        st.rerun()
                sw_key=f"_sw_{dk}_{si}"
                if st.button(T("swap_lbl"),key=f"sw_{dk}_{si}",use_container_width=True):
                    st.session_state[sw_key]=not st.session_state.get(sw_key,False); st.rerun()

            if st.session_state.get(f"_sw_{dk}_{si}",False):
                _render_swap(itin,df,dk,si,cc,d_bud)
            st.markdown("<div style='height:2px'></div>",unsafe_allow_html=True)

        # Add stop
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
        with st.expander(f"+ {T('add_stop_h')}",expanded=False):
            a1,a2=st.columns([4,1],gap="small")
            with a1:
                add_nm=st.text_input("",placeholder=T("add_stop_ph"),key=f"add_{dk}",label_visibility="collapsed")
            with a2:
                if st.button(T("add_btn"),key=f"add_{dk}_go",use_container_width=True,type="primary"):
                    if add_nm.strip():
                        coord=None
                        with st.spinner(T("locating")):
                            coord=_nom(f"{add_nm.strip()} {city}") or _nom(add_nm.strip())
                        ns={"name":add_nm.strip(),
                            "lat":coord[0] if coord else lat+random.uniform(-.01,.01),
                            "lon":coord[1] if coord else lon+random.uniform(-.01,.01),
                            "type_label":"🏛️ Attraction","rating":4.5,
                            "address":"","district":"Custom","description":"Added by you",
                            "time_slot":"TBD","transport_to_next":None}
                        stops.append(ns); itin[dk]=stops; st.session_state["_itin"]=itin
                        st.toast(f"Added — {add_nm}"); st.rerun()
            if df is not None and not df.empty:
                in_day={s.get("name","") for s in stops}
                avail=df[~df["name"].isin(in_day)].head(30)
                if not avail.empty:
                    st.markdown(f'<div style="font-size:12px;color:#9a8c72;margin:10px 0 6px">{T("pick_nearby")}</div>',unsafe_allow_html=True)
                    sp=st.selectbox("",["–"]+list(avail["name"]),key=f"sel_{dk}",label_visibility="collapsed")
                    if sp!="–":
                        row=avail[avail["name"]==sp].iloc[0]
                        if st.button(f"+ {sp[:30]}",key=f"sel_{dk}_go",use_container_width=True,type="primary"):
                            stops.append({**row.to_dict(),"time_slot":"TBD","transport_to_next":None})
                            itin[dk]=stops; st.session_state["_itin"]=itin
                            st.toast(f"Added — {sp}"); st.rerun()

    with map_col:
        st.markdown(f'<span class="sec-label">{T("day_map")} — {dk}</span>' if lang=="EN" else f'<span class="sec-label">{dk} · 地图</span>',unsafe_allow_html=True)
        if FOLIUM_OK:
            # Include any user-added stops in map
            all_stops=list(itin.get(dk,[]))
            extra_rows=[]
            in_df=set(df["name"].tolist()) if df is not None and not df.empty else set()
            for s in all_stops:
                if s.get("name","") not in in_df and s.get("lat"):
                    extra_rows.append(s)
            if extra_rows:
                xdf=pd.DataFrame(extra_rows)
                for c in (df.columns if df is not None and not df.empty else []):
                    if c not in xdf.columns: xdf[c]=""
                map_df=pd.concat([df,xdf],ignore_index=True) if df is not None and not df.empty else xdf
            else:
                map_df=df
            m=build_map(map_df,lat,lon,itin,active_day=dk,zoom=14)
            if m:
                st.markdown('<div class="map-wrap">',unsafe_allow_html=True)
                st_folium(m,width="100%",height=440,returned_objects=[])
                st.markdown("</div>",unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:11px;color:#9a8c72;margin-top:6px">{"Numbered markers = today\'s schedule · Faint dots = nearby places" if lang=="EN" else "数字标记 = 今日行程 · 浅色点 = 附近地点"}</div>',unsafe_allow_html=True)
        else:
            st.info("Install streamlit-folium for the map.")

        # AI chat (same as overview, no must-see)
        st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
        _render_ai(city,itin,lang,compact=True)

    # Bottom nav
    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
    st.markdown('<div style="border-top:1px solid rgba(0,0,0,0.07);padding-top:16px;margin-top:4px">',unsafe_allow_html=True)
    bn1,bn2,bn3=st.columns([1,2,1],gap="small")
    with bn1:
        if di>0:
            if st.button(T("prev_day"),key="s6_prev",use_container_width=True):
                itin[dk]=stops; st.session_state["_itin"]=itin
                st.session_state["active_day"]=all_days[di-1]; st.rerun()
    with bn2:
        if st.button(T("save_day"),key="s6_save",use_container_width=True,type="primary"):
            itin[dk]=stops; st.session_state["_itin"]=itin  # SAVE
            st.session_state["step"]=5; st.rerun()
    with bn3:
        if di<len(all_days)-1:
            if st.button(T("next_day"),key="s6_next",use_container_width=True):
                itin[dk]=stops; st.session_state["_itin"]=itin
                st.session_state["active_day"]=all_days[di+1]; st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# SWAP PANEL
# ════════════════════════════════════════════════════════════════
def _render_swap(itin,df,dk,si,cc,d_bud):
    stops=itin.get(dk,[]); cur=stops[si]; cur_type=cur.get("type_label","")
    used={s.get("name","") for sl in itin.values() if isinstance(sl,list) for s in sl}
    st.markdown(f"""<div class="swap-panel">
      <div style="font-size:12px;font-weight:600;color:#8a6c28;margin-bottom:10px">
        {T("swap_h")} — <span style="color:#18140c">{_ss(cur.get("name",""))}</span>
      </div>""",unsafe_allow_html=True)
    if df is not None and not df.empty:
        cands=df[(df["type_label"]==cur_type)&(~df["name"].isin(used))].sort_values("rating",ascending=False).head(4)
        if not cands.empty:
            swcols=st.columns(min(len(cands),4),gap="small")
            for i,(_,alt) in enumerate(cands.iterrows()):
                with swcols[i%4]:
                    nm=_ss(alt["name"]); rat=alt.get("rating",0); dur=est_dur(nm,cur_type); cs=cost_est(cur_type,d_bud,cc)
                    st.markdown(f"""<div style="background:white;border-radius:10px;padding:10px;
                      border:1px solid rgba(0,0,0,0.08);margin-bottom:6px;box-shadow:0 1px 4px rgba(0,0,0,0.05)">
                      <div style="font-weight:600;font-size:12px;color:#18140c">{nm}</div>
                      <div style="font-size:11px;color:#9a8c72">⭐ {rat} · {fmt_dur(dur)}</div>
                      <div style="font-size:11px;color:#b8943a">💰 {cs}</div>
                    </div>""",unsafe_allow_html=True)
                    if st.button(T("select_sel"),key=f"swx_{dk}_{si}_{nm[:6]}",use_container_width=True,type="primary"):
                        ni=dict(itin); ds=list(ni.get(dk,[])); ds[si]=alt.to_dict()
                        ni[dk]=ds; st.session_state["_itin"]=ni
                        st.session_state.pop(f"_sw_{dk}_{si}",None)
                        st.toast(f"Replaced — {nm}"); st.rerun()
        else:
            st.markdown(f'<div style="font-size:12px;color:#9a8c72">{T("no_swap")}</div>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)
    if st.button(T("cancel"),key=f"swcancel_{dk}_{si}"):
        st.session_state.pop(f"_sw_{dk}_{si}",None); st.rerun()

# ════════════════════════════════════════════════════════════════
# AI PANEL
# ════════════════════════════════════════════════════════════════
def _render_ai(city,itin,lang,compact=False):
    itin_summary=f"{len(itin)} days in {city}, {sum(len(v) for v in itin.values() if isinstance(v,list))} stops"
    ai_open=st.session_state.get("ai_open",False)

    _,btncol=st.columns([5,1])
    with btncol:
        if st.button(T("ask_ai_btn"),key="ai_toggle",use_container_width=True,
                     type="primary" if ai_open else "secondary"):
            st.session_state["ai_open"]=not ai_open; st.rerun()

    if not ai_open: return

    st.markdown(f"""<div class="ai-panel">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;
          background:linear-gradient(135deg,#b8943a,#d4aa52);
          display:flex;align-items:center;justify-content:center;font-size:15px;color:white">✦</div>
          <div>
            <div style="font-weight:600;font-size:14px;color:#18140c">{T("ai_h")}</div>
            <div style="font-size:11px;color:#9a8c72">{"Powered by Claude" if lang=="EN" else "由 Claude 提供支持"}</div>
          </div>
        </div>
      </div>""",unsafe_allow_html=True)

    chat=st.session_state.get("ai_chat",[])
    n_show=4 if compact else 8
    for msg in chat[-n_show:]:
        role=msg.get("role",""); content=msg.get("content","")
        if role=="user":
            st.markdown(f'<div class="chat-me"><div>{_ss(content)}</div></div>',unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai"><div>{_ss(content)}</div></div>',unsafe_allow_html=True)

    if not chat:
        st.markdown(f'<div style="font-size:12px;color:#9a8c72;margin-bottom:8px">{T("quick_q")}</div>' if lang=="EN" else '<div style="font-size:12px;color:#9a8c72;margin-bottom:8px">快捷提问：</div>',unsafe_allow_html=True)
        if lang=="ZH":
            qps=[f"{city}有什么不能错过的？","怎么省钱玩转{city}？","第一天应该从哪里开始？","当地必吃的美食是什么？"]
        else:
            qps=[f"What are the must-dos in {city}?","Any money-saving tips?","Best way to start Day 1?","What should I eat there?"]
        qc=st.columns(2,gap="small")
        for qi,qp in enumerate(qps):
            with qc[qi%2]:
                if st.button(qp,key=f"qp_{qi}",use_container_width=True):
                    chat.append({"role":"user","content":qp})
                    with st.spinner("…"):
                        reply=call_ai(chat,city,itin_summary,lang)
                    chat.append({"role":"assistant","content":reply})
                    st.session_state["ai_chat"]=chat; st.rerun()

    ai_q=st.text_input("",placeholder=T("ai_ph"),key="ai_inp",label_visibility="collapsed")
    ai_c1,ai_c2,ai_c3=st.columns([4,1,1],gap="small")
    with ai_c2:
        if st.button(T("ai_send"),key="ai_send",use_container_width=True,type="primary"):
            if ai_q.strip():
                chat.append({"role":"user","content":ai_q.strip()})
                with st.spinner("…"):
                    reply=call_ai(chat,city,itin_summary,lang)
                chat.append({"role":"assistant","content":reply})
                st.session_state["ai_chat"]=chat; st.rerun()
    with ai_c3:
        if chat and st.button(T("ai_clear"),key="ai_clear",use_container_width=True):
            st.session_state["ai_chat"]=[]; st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# ROUTER
# ════════════════════════════════════════════════════════════════
step=st.session_state.get("step",1)
if   step==1: step_1()
elif step==2: step_2()
elif step==3: step_3()
elif step==4: step_4()
elif step==5: step_5()
elif step==6: step_6()
else: st.session_state["step"]=1; st.rerun()

st.markdown("""<div style="text-align:center;padding:28px 0 14px;font-size:10px;
letter-spacing:0.14em;text-transform:uppercase;color:rgba(90,80,60,0.28)">
Voyager · AI Travel Planning
</div>""",unsafe_allow_html=True)
