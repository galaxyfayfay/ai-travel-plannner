"""
AI Travel Planner — Multi-Step Wizard
Luxury-grade, Apple-glass aesthetic, Purple/Translucent
Steps: 1) Login/Guest  2) Destination  3) Preferences  4) Itinerary
"""

import math
import random
import re
import json
import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Voyager — AI Travel Planner",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Secret helpers ────────────────────────────────────────────────
def _get_secret(key: str) -> str:
    try:
        val = st.secrets.get(key, "")
        if val: return str(val)
    except Exception:
        pass
    return os.getenv(key, "")

AMAP_KEY     = _get_secret("APIKEY")
DEEPSEEK_KEY = _get_secret("DEEPSEEKKEY")

# ── Optional module imports ───────────────────────────────────────
try:
    from ai_planner import generate_itinerary
    AI_OK = True
except Exception as _e:
    AI_OK = False; _AI_ERR = str(_e)

try:
    from transport_planner import render_transport_comparison, build_day_schedule, estimate_travel
    TRANSPORT_OK = True
except Exception:
    TRANSPORT_OK = False

try:
    from auth_manager import register_user, login_user, get_user_from_session, logout_user, create_collab_link, join_collab
    AUTH_OK = True
except Exception:
    AUTH_OK = False

try:
    from wishlist_manager import add_to_wishlist as _wl_add, remove_from_wishlist as _wl_remove, get_wishlist as _wl_get, is_in_wishlist as _wl_check, save_itinerary as _save_itin_ext, swap_place_in_itinerary
    WISHLIST_EXT = True
except Exception:
    WISHLIST_EXT = False

try:
    from points_system import add_points, get_points, render_points_panel
    POINTS_OK = True
except Exception:
    POINTS_OK = False

try:
    from data_manager import get_must_see
    DATA_MGR_OK = True
except Exception:
    DATA_MGR_OK = False

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except Exception:
    FOLIUM_OK = False

# ══════════════════════════════════════════════════════════════════
# GLOBAL CSS — Luxury Apple Glass
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── App Background ── */
.stApp {
  background: linear-gradient(135deg, #0f0a1e 0%, #1a0f3c 30%, #0d1a3a 60%, #0a0f2e 100%) !important;
  min-height: 100vh;
}

/* Hide default sidebar */
section[data-testid="stSidebar"] { display: none !important; }
.main .block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── Orb Background Effects ── */
.orb-container {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 0; overflow: hidden;
}
.orb {
  position: absolute; border-radius: 50%;
  filter: blur(80px); opacity: 0.18;
  animation: orbFloat 12s ease-in-out infinite alternate;
}
.orb-1 { width: 500px; height: 500px; background: #7c3aed; top: -100px; left: -100px; animation-delay: 0s; }
.orb-2 { width: 400px; height: 400px; background: #4f46e5; top: 30%; right: -80px; animation-delay: 3s; }
.orb-3 { width: 350px; height: 350px; background: #9333ea; bottom: 10%; left: 20%; animation-delay: 6s; }
.orb-4 { width: 300px; height: 300px; background: #6d28d9; top: 60%; right: 30%; animation-delay: 2s; }

@keyframes orbFloat {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(30px, -30px) scale(1.1); }
}

/* ── Wizard Container ── */
.wizard-wrap {
  position: relative; z-index: 1;
  min-height: 100vh;
  display: flex; flex-direction: column; align-items: center;
  padding: 32px 20px 60px;
}

/* ── Progress Bar ── */
.progress-bar-outer {
  width: 100%; max-width: 720px; margin: 0 auto 40px;
}
.progress-steps {
  display: flex; align-items: center; justify-content: center; gap: 0;
  position: relative;
}
.progress-step {
  display: flex; flex-direction: column; align-items: center; flex: 1;
  position: relative; z-index: 1;
}
.step-circle {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 600; font-family: 'DM Sans', sans-serif;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
}
.step-circle.done {
  background: linear-gradient(135deg, #7c3aed, #9333ea);
  border: 2px solid rgba(167,139,250,0.6);
  color: white;
  box-shadow: 0 0 20px rgba(124,58,237,0.5), 0 0 40px rgba(124,58,237,0.2);
}
.step-circle.active {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  border: 2px solid rgba(196,181,253,0.8);
  color: white;
  box-shadow: 0 0 30px rgba(139,92,246,0.7), 0 0 60px rgba(139,92,246,0.3);
  transform: scale(1.12);
}
.step-circle.pending {
  background: rgba(255,255,255,0.04);
  border: 2px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.3);
}
.step-label {
  margin-top: 8px; font-size: 0.68rem; font-weight: 500;
  letter-spacing: 0.06em; text-transform: uppercase;
  transition: color 0.3s;
}
.step-label.active { color: #c4b5fd; }
.step-label.done   { color: rgba(167,139,250,0.8); }
.step-label.pending{ color: rgba(255,255,255,0.25); }

.step-connector {
  flex: 1; height: 2px; margin: 0;
  background: rgba(255,255,255,0.08);
  position: relative; top: -22px; z-index: 0;
}
.step-connector.done-connector {
  background: linear-gradient(90deg, #7c3aed, #9333ea);
  box-shadow: 0 0 8px rgba(124,58,237,0.4);
}

/* ── Glass Card ── */
.glass-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 28px;
  padding: 44px 48px;
  width: 100%; max-width: 720px;
  box-shadow:
    0 0 0 1px rgba(139,92,246,0.08) inset,
    0 40px 80px rgba(0,0,0,0.4),
    0 0 60px rgba(124,58,237,0.08);
  position: relative; overflow: hidden;
}
.glass-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(196,181,253,0.3), transparent);
}

/* ── Hero Title ── */
.step-hero-label {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: rgba(167,139,250,0.7);
  margin-bottom: 10px;
}
.step-hero-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.8rem; font-weight: 300; color: #fff;
  line-height: 1.1; margin: 0 0 10px;
  letter-spacing: -0.02em;
}
.step-hero-title em {
  font-style: italic; color: #c4b5fd;
}
.step-hero-sub {
  font-size: 0.88rem; color: rgba(255,255,255,0.4);
  font-weight: 300; margin-bottom: 36px; line-height: 1.6;
}

/* ── Option Cards (for Step 1, 2, 3 choices) ── */
.opt-grid {
  display: grid; gap: 14px; margin: 24px 0;
}
.opt-grid-2 { grid-template-columns: 1fr 1fr; }
.opt-grid-3 { grid-template-columns: 1fr 1fr 1fr; }
.opt-card {
  background: rgba(255,255,255,0.04);
  border: 1.5px solid rgba(255,255,255,0.08);
  border-radius: 18px; padding: 22px 20px;
  cursor: pointer; transition: all 0.25s ease;
  text-align: center; position: relative; overflow: hidden;
}
.opt-card::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.15), transparent 70%);
  opacity: 0; transition: opacity 0.25s;
}
.opt-card:hover::before { opacity: 1; }
.opt-card:hover {
  border-color: rgba(139,92,246,0.4);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(124,58,237,0.2);
}
.opt-card.selected {
  background: rgba(139,92,246,0.12);
  border-color: rgba(167,139,250,0.6);
  box-shadow: 0 0 0 1px rgba(167,139,250,0.2) inset, 0 12px 40px rgba(124,58,237,0.25);
}
.opt-card.selected::before { opacity: 1; }
.opt-icon { font-size: 2rem; margin-bottom: 10px; }
.opt-title { font-weight: 600; font-size: 0.88rem; color: #fff; margin-bottom: 4px; }
.opt-sub   { font-size: 0.75rem; color: rgba(255,255,255,0.35); }

/* ── Destination Pills ── */
.dest-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 100px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 0.8rem; color: rgba(255,255,255,0.55);
  cursor: pointer; transition: all 0.2s;
  margin: 4px; white-space: nowrap;
}
.dest-pill:hover {
  background: rgba(139,92,246,0.15);
  border-color: rgba(167,139,250,0.4);
  color: #c4b5fd;
}
.dest-pill.selected {
  background: rgba(139,92,246,0.2);
  border-color: rgba(167,139,250,0.6);
  color: #c4b5fd;
}
.pills-wrap { display: flex; flex-wrap: wrap; gap: 0; margin: 16px 0; }

/* ── Nav Buttons ── */
.nav-row {
  display: flex; gap: 12px; margin-top: 36px;
  justify-content: space-between; align-items: center;
}
.btn-back {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 12px 24px; border-radius: 12px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.5); font-size: 0.84rem;
  cursor: pointer; font-family: 'DM Sans', sans-serif;
  font-weight: 500; transition: all 0.2s;
  text-decoration: none;
}
.btn-back:hover {
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.8);
}
.btn-next {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; border-radius: 12px;
  background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%);
  border: 1px solid rgba(167,139,250,0.3);
  color: white; font-size: 0.88rem; font-weight: 600;
  cursor: pointer; font-family: 'DM Sans', sans-serif;
  box-shadow: 0 8px 32px rgba(124,58,237,0.4), 0 0 0 1px rgba(167,139,250,0.15) inset;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  text-decoration: none; flex: 1; justify-content: center;
}
.btn-next:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 16px 48px rgba(124,58,237,0.5), 0 0 0 1px rgba(196,181,253,0.25) inset;
}

/* ── Streamlit Widget Overrides ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background: rgba(255,255,255,0.05) !important;
  border: 1.5px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  color: #fff !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.88rem !important;
  padding: 14px 18px !important;
  transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: rgba(167,139,250,0.5) !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: rgba(255,255,255,0.25) !important; }
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stMultiSelect label, .stSlider label {
  color: rgba(255,255,255,0.5) !important;
  font-size: 0.75rem !important; font-weight: 500 !important;
  letter-spacing: 0.06em !important; text-transform: uppercase !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div {
  background: rgba(255,255,255,0.05) !important;
  border: 1.5px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  color: #fff !important;
}
.stMultiSelect > div > div {
  background: rgba(255,255,255,0.05) !important;
  border: 1.5px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
}
.stMultiSelect span[data-baseweb="tag"] {
  background: rgba(124,58,237,0.3) !important;
  border-color: rgba(167,139,250,0.4) !important;
  color: #c4b5fd !important;
}
.stSlider > div > div > div > div { background: #7c3aed !important; }
.stSlider > div > div > div[data-testid="stSlider"] > div { background: rgba(255,255,255,0.1) !important; }

/* ── Streamlit Button override ── */
.stButton > button {
  background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%) !important;
  color: white !important; border: none !important;
  border-radius: 12px !important; font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important; font-size: 0.88rem !important;
  padding: 14px 28px !important;
  box-shadow: 0 8px 24px rgba(124,58,237,0.35) !important;
  transition: all 0.25s !important; width: 100% !important;
  letter-spacing: 0.02em !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 16px 40px rgba(124,58,237,0.5) !important;
}
.stButton > button[kind="secondary"] {
  background: rgba(255,255,255,0.06) !important;
  color: rgba(255,255,255,0.6) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: rgba(255,255,255,0.1) !important;
  color: rgba(255,255,255,0.9) !important;
  transform: translateY(-1px) !important;
  box-shadow: none !important;
}

/* ── Day Card (Step 4) ── */
.day-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1.5px solid rgba(255,255,255,0.08);
  border-radius: 20px; padding: 24px;
  margin-bottom: 16px; cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative; overflow: hidden;
}
.day-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  opacity: 0; transition: opacity 0.3s;
}
.day-card:hover, .day-card.expanded {
  border-color: rgba(167,139,250,0.4);
  box-shadow: 0 20px 60px rgba(124,58,237,0.2);
  transform: translateY(-2px);
}
.day-card.expanded::before { opacity: 1; }
.day-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 100px; font-size: 0.7rem;
  font-weight: 600; letter-spacing: 0.06em; margin-bottom: 12px;
}
.stop-timeline {
  position: relative; padding-left: 28px;
}
.stop-timeline::before {
  content: ''; position: absolute; left: 10px; top: 14px; bottom: 14px;
  width: 1.5px; background: rgba(167,139,250,0.2);
}
.stop-item {
  position: relative; padding: 10px 0 10px 16px;
  border-radius: 10px; margin: 2px 0;
  transition: background 0.2s;
}
.stop-item:hover { background: rgba(255,255,255,0.04); }
.stop-dot {
  position: absolute; left: -22px; top: 50%;
  transform: translateY(-50%);
  width: 8px; height: 8px; border-radius: 50%;
}
.stop-name-txt { font-size: 0.88rem; color: #fff; font-weight: 500; }
.stop-meta-txt { font-size: 0.72rem; color: rgba(255,255,255,0.4); margin-top: 2px; }
.time-chip {
  display: inline-flex; align-items: center;
  background: rgba(139,92,246,0.12);
  border: 1px solid rgba(167,139,250,0.2);
  border-radius: 100px; padding: 2px 10px;
  font-size: 0.68rem; color: #c4b5fd; font-weight: 500;
  margin-right: 6px;
}
.tr-chip {
  display: inline-flex; align-items: center;
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.18);
  border-radius: 100px; padding: 2px 10px;
  font-size: 0.68rem; color: #7dd3fc; font-weight: 500;
}

/* ── Budget Summary ── */
.budget-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin: 16px 0; }
.budget-cell {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 16px; text-align: center;
}
.budget-amt { font-size: 1.4rem; font-weight: 700; color: #fff; letter-spacing: -0.03em; }
.budget-lbl { font-size: 0.65rem; color: rgba(167,139,250,0.7); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.budget-sub { font-size: 0.68rem; color: rgba(255,255,255,0.3); margin-top: 4px; }

/* ── Map container ── */
.map-wrap {
  border-radius: 20px; overflow: hidden;
  border: 1.5px solid rgba(255,255,255,0.08);
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
  margin: 20px 0;
}

/* ── AI Picks Panel ── */
.ai-panel {
  background: rgba(124,58,237,0.06);
  border: 1px solid rgba(167,139,250,0.15);
  border-radius: 16px; padding: 18px; margin: 12px 0;
}
.ai-item {
  background: rgba(255,255,255,0.04);
  border-left: 3px solid #a78bfa;
  border-radius: 10px; padding: 12px 14px; margin: 6px 0;
}

/* ── Tab override ── */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  gap: 4px !important; padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important; color: rgba(255,255,255,0.4) !important;
  font-size: 0.80rem !important; font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(139,92,246,0.2) !important;
  color: #c4b5fd !important;
  box-shadow: 0 0 0 1px rgba(167,139,250,0.2) inset !important;
}

/* ── Metric ── */
div[data-testid="stMetric"] {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 16px !important;
  padding: 16px 20px !important;
}
div[data-testid="stMetric"] label {
  color: rgba(167,139,250,0.7) !important;
  font-size: 0.67rem !important; font-weight: 600 !important;
  text-transform: uppercase !important; letter-spacing: 0.08em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: #fff !important; font-size: 1.35rem !important; font-weight: 700 !important;
}

/* ── Expander ── */
.stExpander {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 14px !important;
}
.stExpander summary {
  color: rgba(255,255,255,0.6) !important; font-size: 0.82rem !important;
}

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
  background: rgba(139,92,246,0.12) !important;
  color: #c4b5fd !important;
  border: 1px solid rgba(167,139,250,0.25) !important;
  box-shadow: none !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 12px !important; }
div[data-testid="stSuccess"] { background: rgba(34,197,94,0.08) !important; border-color: rgba(34,197,94,0.2) !important; }
div[data-testid="stError"]   { background: rgba(239,68,68,0.08) !important; border-color: rgba(239,68,68,0.2) !important; }
div[data-testid="stWarning"] { background: rgba(245,158,11,0.08) !important; border-color: rgba(245,158,11,0.2) !important; }
div[data-testid="stInfo"]    { background: rgba(139,92,246,0.08) !important; border-color: rgba(139,92,246,0.2) !important; }

/* ── Caption ── */
.stCaption { color: rgba(167,139,250,0.5) !important; font-size: 0.72rem !important; }

/* ── Dataframe ── */
.stDataFrame { background: rgba(255,255,255,0.03) !important; border-radius: 12px !important; }

/* ── Drag reorder handle ── */
.reorder-hint { font-size: 0.72rem; color: rgba(167,139,250,0.5); margin-bottom: 8px; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.5); }
</style>

<!-- Orb background -->
<div class="orb-container">
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  <div class="orb orb-3"></div>
  <div class="orb orb-4"></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
CHAIN_BL = ["kfc","mcdonald","starbucks","seven-eleven","family mart","711","lawson","costa coffee"]
def is_chain(n): return any(k in n.lower() for k in CHAIN_BL)

def _ss(s):
    if s is None: return ""
    s = str(s)
    for o, n in {"\u2014":"-","\u2013":"-","\u2019":"'","\u2018":"'","\u201c":'"',"\u201d":'"',"\u2026":"..."}.items():
        s = s.replace(o, n)
    return s

def _hav(la1, lo1, la2, lo2):
    R = 6371000
    dl = math.radians(la2 - la1); dg = math.radians(lo2 - lo1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dg/2)**2
    return R * 2 * math.asin(math.sqrt(min(1., a)))

def _hkm(la1, lo1, la2, lo2): return _hav(la1,lo1,la2,lo2)/1000

PTYPES = {
    "🏛️ Attraction": {"osm":("tourism","attraction"), "amap":"110000","color":"#8b5cf6"},
    "🍜 Restaurant":  {"osm":("amenity","restaurant"), "amap":"050000","color":"#f59e0b"},
    "☕ Cafe":         {"osm":("amenity","cafe"),        "amap":"050500","color":"#a78bfa"},
    "🌿 Park":         {"osm":("leisure","park"),        "amap":"110101","color":"#34d399"},
    "🛍️ Shopping":    {"osm":("shop","mall"),            "amap":"060000","color":"#f472b6"},
    "🍺 Bar/Nightlife":{"osm":("amenity","bar"),         "amap":"050600","color":"#fb923c"},
    "🏨 Hotel":        {"osm":("tourism","hotel"),        "amap":"100000","color":"#38bdf8"},
}
DAY_COLORS = ["#8b5cf6","#f59e0b","#34d399","#f472b6","#fb923c","#38bdf8","#a78bfa","#6ee7b7"]

DURATION_MAP = {
    "🏛️ Attraction":90, "🍜 Restaurant":60, "☕ Cafe":45,
    "🌿 Park":60, "🛍️ Shopping":90, "🍺 Bar/Nightlife":90, "🏨 Hotel":20,
}
DURATION_SPECIAL = {
    "museum":120,"palace":120,"castle":120,"temple":60,"shrine":45,"cathedral":60,
    "market":75,"bazaar":75,"gallery":75,"park":60,"garden":75,"nature":90,
    "tower":45,"viewpoint":30,"crossing":20,"restaurant":60,"cafe":45,"mall":90,
    "beach":90,"hot spring":120,"aquarium":90,"zoo":120,
}
def estimate_duration(name, type_label):
    name_lc = (name or "").lower()
    for kw, mins in DURATION_SPECIAL.items():
        if kw in name_lc: return mins
    return DURATION_MAP.get(type_label, 60)

def format_duration(mins):
    if mins < 60: return f"{mins}min"
    h = mins // 60; m = mins % 60
    return f"{h}h {m}min" if m else f"{h}h"

def _parse_dur(s):
    if not s: return 20
    s = s.lower().strip(); total = 0
    h = re.search(r'(\d+)\s*h', s)
    m = re.search(r'(\d+)\s*m', s)
    if h: total += int(h.group(1))*60
    if m: total += int(m.group(1))
    return total if total > 0 else 20

def build_timeline(stops, start_hour=9):
    result = []; cur = start_hour * 60
    for i, s in enumerate(stops):
        tl = s.get("type_label","🏛️ Attraction")
        nm = s.get("name","")
        dur = estimate_duration(nm, tl)
        if i > 0:
            tr = stops[i-1].get("transport_to_next") or {}
            cur += _parse_dur(tr.get("duration",""))
        arr_h = cur//60; arr_m = cur%60
        dep = cur + dur
        dep_h = dep//60; dep_m = dep%60
        enriched = dict(s)
        enriched["arrive_time"] = f"{arr_h:02d}:{arr_m:02d}"
        enriched["depart_time"] = f"{dep_h:02d}:{dep_m:02d}"
        enriched["duration_min"] = dur
        result.append(enriched)
        cur = dep + 15
    return result

WORLD_CITIES = {
    "Japan":["Tokyo","Osaka","Kyoto","Sapporo","Fukuoka","Nagoya","Hiroshima","Nara"],
    "South Korea":["Seoul","Busan","Incheon","Jeju","Daegu"],
    "Thailand":["Bangkok","Chiang Mai","Phuket","Pattaya","Koh Samui"],
    "Vietnam":["Ho Chi Minh City","Hanoi","Da Nang","Hoi An","Nha Trang"],
    "Indonesia":["Bali","Jakarta","Yogyakarta"],
    "Malaysia":["Kuala Lumpur","Penang","Malacca","Langkawi"],
    "Singapore":["Singapore"],
    "India":["Mumbai","Delhi","Bangalore","Jaipur","Goa","Agra"],
    "UAE":["Dubai","Abu Dhabi"],
    "Turkey":["Istanbul","Cappadocia","Antalya"],
    "France":["Paris","Lyon","Nice","Bordeaux"],
    "Italy":["Rome","Milan","Florence","Venice","Naples"],
    "Spain":["Barcelona","Madrid","Seville","Valencia","Granada"],
    "United Kingdom":["London","Edinburgh","Manchester","Bath","Oxford"],
    "Germany":["Berlin","Munich","Hamburg","Frankfurt","Cologne"],
    "Netherlands":["Amsterdam","Rotterdam","Utrecht"],
    "Switzerland":["Zurich","Geneva","Lucerne","Interlaken","Zermatt"],
    "Austria":["Vienna","Salzburg","Innsbruck"],
    "Greece":["Athens","Santorini","Mykonos","Crete"],
    "Portugal":["Lisbon","Porto","Algarve","Sintra"],
    "Czech Republic":["Prague","Cesky Krumlov"],
    "Hungary":["Budapest"],
    "Poland":["Warsaw","Krakow","Gdansk"],
    "Croatia":["Dubrovnik","Split","Zagreb"],
    "Norway":["Oslo","Bergen","Tromso"],
    "Sweden":["Stockholm","Gothenburg"],
    "Denmark":["Copenhagen"],
    "Iceland":["Reykjavik"],
    "USA":["New York","Los Angeles","Chicago","San Francisco","Miami","Boston","Seattle","Las Vegas","Washington DC"],
    "Canada":["Toronto","Vancouver","Montreal","Banff","Quebec City"],
    "Mexico":["Mexico City","Cancun","Oaxaca"],
    "Brazil":["Rio de Janeiro","Sao Paulo"],
    "Argentina":["Buenos Aires","Patagonia"],
    "Peru":["Lima","Cusco","Machu Picchu"],
    "Australia":["Sydney","Melbourne","Brisbane","Perth","Cairns"],
    "New Zealand":["Auckland","Queenstown","Wellington"],
    "Morocco":["Marrakech","Fes","Chefchaouen"],
    "Egypt":["Cairo","Luxor"],
    "South Africa":["Cape Town","Johannesburg"],
    "Kenya":["Nairobi","Masai Mara"],
    "China":["Beijing","Shanghai","Guangzhou","Shenzhen","Chengdu","Hangzhou","Xi'an","Chongqing"],
    "Hong Kong":["Hong Kong"],
    "Taiwan":["Taipei","Tainan","Kaohsiung"],
}
COUNTRY_CODES = {
    "China":"CN","Japan":"JP","South Korea":"KR","Thailand":"TH","Vietnam":"VN",
    "Indonesia":"ID","Malaysia":"MY","Singapore":"SG","Philippines":"PH","India":"IN",
    "UAE":"AE","Turkey":"TR","France":"FR","Italy":"IT","Spain":"ES",
    "United Kingdom":"GB","Germany":"DE","Netherlands":"NL","Switzerland":"CH",
    "Austria":"AT","Greece":"GR","Portugal":"PT","Czech Republic":"CZ","Hungary":"HU",
    "Poland":"PL","Croatia":"HR","Norway":"NO","Sweden":"SE","Denmark":"DK",
    "Finland":"FI","Iceland":"IS","Russia":"RU","USA":"US","Canada":"CA","Mexico":"MX",
    "Brazil":"BR","Argentina":"AR","Peru":"PE","Colombia":"CO","Australia":"AU",
    "New Zealand":"NZ","Morocco":"MA","Egypt":"EG","South Africa":"ZA","Kenya":"KE",
    "Hong Kong":"HK","Taiwan":"TW",
}

INTL_CITIES = {
    "tokyo":(35.6762,139.6503,"JP"),
    "osaka":(34.6937,135.5023,"JP"),
    "kyoto":(35.0116,135.7681,"JP"),
    "seoul":(37.5665,126.9780,"KR"),
    "bangkok":(13.7563,100.5018,"TH"),
    "singapore":(1.3521,103.8198,"SG"),
    "paris":(48.8566,2.3522,"FR"),
    "london":(51.5072,-0.1276,"GB"),
    "rome":(41.9028,12.4964,"IT"),
    "barcelona":(41.3851,2.1734,"ES"),
    "new york":(40.7128,-74.0060,"US"),
    "new york city":(40.7128,-74.0060,"US"),
    "sydney":(-33.8688,151.2093,"AU"),
    "dubai":(25.2048,55.2708,"AE"),
    "amsterdam":(52.3676,4.9041,"NL"),
    "istanbul":(41.0082,28.9784,"TR"),
    "hong kong":(22.3193,114.1694,"HK"),
    "taipei":(25.0330,121.5654,"TW"),
    "bali":(-8.3405,115.0920,"ID"),
    "ho chi minh city":(10.7769,106.7009,"VN"),
    "kuala lumpur":(3.1390,101.6869,"MY"),
    "beijing":(39.9042,116.4074,"CN"),
    "shanghai":(31.2304,121.4737,"CN"),
    "chengdu":(30.5728,104.0668,"CN"),
    "vienna":(48.2082,16.3738,"AT"),
    "berlin":(52.5200,13.4050,"DE"),
    "munich":(48.1351,11.5820,"DE"),
    "prague":(50.0755,14.4378,"CZ"),
    "budapest":(47.4979,19.0402,"HU"),
    "santorini":(36.3932,25.4615,"GR"),
    "athens":(37.9838,23.7275,"GR"),
    "lisbon":(38.7223,-9.1393,"PT"),
    "marrakech":(31.6295,-7.9811,"MA"),
    "cairo":(30.0444,31.2357,"EG"),
    "cape town":(-33.9249,18.4241,"ZA"),
    "miami":(25.7617,-80.1918,"US"),
    "los angeles":(34.0522,-118.2437,"US"),
    "san francisco":(37.7749,-122.4194,"US"),
    "chicago":(41.8781,-87.6298,"US"),
    "las vegas":(36.1699,-115.1398,"US"),
    "cancun":(21.1619,-86.8515,"MX"),
    "rio de janeiro":(-22.9068,-43.1729,"BR"),
    "buenos aires":(-34.6037,-58.3816,"AR"),
    "cusco":(-13.5320,-71.9675,"PE"),
    "reykjavik":(64.1265,-21.8174,"IS"),
    "queenstown":(-45.0312,168.6626,"NZ"),
    "melbourne":(-37.8136,144.9631,"AU"),
    "edinburgh":(55.9533,-3.1883,"GB"),
    "florence":(43.7696,11.2558,"IT"),
    "venice":(45.4408,12.3155,"IT"),
    "zurich":(47.3769,8.5417,"CH"),
    "interlaken":(46.6863,7.8632,"CH"),
    "dubrovnik":(42.6507,18.0944,"HR"),
    "krakow":(50.0647,19.9450,"PL"),
}

CN_CITIES = {
    "beijing":(39.9042,116.4074),"shanghai":(31.2304,121.4737),
    "guangzhou":(23.1291,113.2644),"shenzhen":(22.5431,114.0579),
    "chengdu":(30.5728,104.0668),"hangzhou":(30.2741,120.1551),
    "xian":(34.3416,108.9398),"xi'an":(34.3416,108.9398),
    "chongqing":(29.5630,106.5516),"nanjing":(32.0603,118.7969),
}

AMAP_KW = {
    "🏛️ Attraction":["旅游景点","博物馆"], "🍜 Restaurant":["餐馆","美食"],
    "☕ Cafe":["咖啡","下午茶"], "🌿 Park":["公园","花园"],
    "🛍️ Shopping":["商场","购物中心"], "🍺 Bar/Nightlife":["酒吧","夜店"],
    "🏨 Hotel":["酒店","宾馆"],
}

CURRENCIES = {
    "CN":[("USD","$",1.0),("CNY","¥",7.25)],
    "JP":[("USD","$",1.0),("JPY","¥",155)],
    "KR":[("USD","$",1.0),("KRW","₩",1350)],
    "TH":[("USD","$",1.0),("THB","฿",36)],
    "SG":[("USD","$",1.0),("SGD","S$",1.35)],
    "FR":[("USD","$",1.0),("EUR","€",0.92)],
    "GB":[("USD","$",1.0),("GBP","£",0.79)],
    "IT":[("USD","$",1.0),("EUR","€",0.92)],
    "ES":[("USD","$",1.0),("EUR","€",0.92)],
    "US":[("USD","$",1.0)],
    "AU":[("USD","$",1.0),("AUD","A$",1.53)],
    "AE":[("USD","$",1.0),("AED","AED ",3.67)],
    "NL":[("USD","$",1.0),("EUR","€",0.92)],
    "TR":[("USD","$",1.0),("TRY","₺",32)],
    "HK":[("USD","$",1.0),("HKD","HK$",7.82)],
    "TW":[("USD","$",1.0),("TWD","NT$",32)],
    "INT":[("USD","$",1.0)],
}
def _local_rate(country):
    p = CURRENCIES.get(country,[("USD","$",1.0)])
    return (p[1][1],p[1][2]) if len(p)>1 else ("$",1.0)

COST_W  = {"🏛️ Attraction":0.18,"🍜 Restaurant":0.25,"☕ Cafe":0.10,
           "🌿 Park":0.04,"🛍️ Shopping":0.22,"🍺 Bar/Nightlife":0.16,"🏨 Hotel":0.00}
COST_FL = {"🏛️ Attraction":4,"🍜 Restaurant":6,"☕ Cafe":3,
           "🌿 Park":0,"🛍️ Shopping":8,"🍺 Bar/Nightlife":5,"🏨 Hotel":0}

def cost_est(tl, daily_usd, country):
    w = COST_W.get(tl,.12); fl = COST_FL.get(tl,2)
    pv = max(fl,daily_usd*w/2); lo = pv*.65; hi = pv*1.45
    sym, rate = _local_rate(country)
    if country=="US": return (lo+hi)/2, f"${round(lo)}-${round(hi)}"
    return (lo+hi)/2, f"${round(lo)}-${round(hi)} ({sym}{round(lo*rate)}-{sym}{round(hi*rate)})"

def geo_dedup(places, r=120.):
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
    D={"attraction":"Worth a visit","restaurant":"Great for a meal","cafe":"Perfect coffee stop",
       "park":"Relax outdoors","mall":"Shopping stop","bar":"Evening out","hotel":"Place to stay"}
    for k,v in D.items():
        if k in str(s).lower(): return v
    return "Local favourite"

# ══════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════
DEFAULTS = {
    "step": 1,
    "user_mode": None,   # "guest" or "logged_in"
    "_auth_token": "",
    "dest_country": "",
    "dest_city": "",
    "dest_lat": None,
    "dest_lon": None,
    "dest_country_code": "INT",
    "trip_days": 3,
    "trip_types": ["🏛️ Attraction","🍜 Restaurant"],
    "trip_budget": 80,
    "trip_quotas": None,
    "day_budgets": None,
    "_itin": None,
    "_df": None,
    "seed": 42,
    "expanded_day": None,
    "generating": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════════
def _cur_user():
    if not AUTH_OK: return None
    try:
        tok = st.session_state.get("_auth_token","")
        if not tok: return None
        return get_user_from_session(tok)
    except Exception: return None

# ══════════════════════════════════════════════════════════════════
# GEOCODING
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def _nom(q):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q":q,"format":"json","limit":1},
                         headers={"User-Agent":"VoyagerTravelApp/1.0"},timeout=9).json()
        if r: return float(r[0]["lat"]),float(r[0]["lon"])
    except Exception: pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def _amap_geo(addr):
    if not AMAP_KEY: return None
    try:
        r = requests.get("https://restapi.amap.com/v3/geocode/geo",
                         params={"key":AMAP_KEY,"address":addr,"output":"json"},timeout=8).json()
        if str(r.get("status"))=="1" and r.get("geocodes"):
            loc = r["geocodes"][0].get("location","")
            if "," in loc:
                lon,lat = map(float,loc.split(","))
                return lat,lon
    except Exception: pass
    return None

# ══════════════════════════════════════════════════════════════════
# PLACE SEARCH
# ══════════════════════════════════════════════════════════════════
def search_intl(lat,lon,tls,lpt):
    all_p=[]
    for tl in tls:
        ok,ov = PTYPES[tl]["osm"]
        q=(f'[out:json][timeout:30];(node["{ok}"="{ov}"](around:6000,{lat},{lon});'
           f'way["{ok}"="{ov}"](around:6000,{lat},{lon}););out center {lpt*3};')
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
            pts=[tags.get(k,"") for k in ["addr:housenumber","addr:street","addr:city"] if tags.get(k)]
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

def _parse_amap(pois,kw,tl,limit,seen):
    out=[]
    for p in pois:
        if len(out)>=limit: break
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
            except Exception: pass
    seen2,out=set(),[]
    for p in all_p:
        k=(p["name"],round(p["lat"],4),round(p["lon"],4))
        if k not in seen2: seen2.add(k); out.append(p)
    return out

def demo_places(lat,lon,tls,n,seed):
    random.seed(seed)
    NAMES={
        "🏛️ Attraction":["Grand Museum","Sky Tower","Ancient Temple","Art Gallery","Historic Castle","Night Market","Cultural Centre","Heritage Site"],
        "🍜 Restaurant":["Sakura Dining","Ramen House","Sushi Master","Street Food Alley","Harbour Grill","Noodle King","Garden Restaurant"],
        "☕ Cafe":["Blue Bottle","Artisan Brew","Matcha Corner","Morning Pour","The Cozy Cup","Rooftop Café"],
        "🌿 Park":["Riverside Park","Sakura Garden","Central Park","Bamboo Grove","Waterfront Green"],
        "🛍️ Shopping":["Central Mall","Night Bazaar","Vintage Market","Designer District","Night Market"],
        "🍺 Bar/Nightlife":["Rooftop Bar","Jazz Lounge","Craft Beer Hall","Cocktail Garden","Speakeasy"],
        "🏨 Hotel":["Grand Palace Hotel","Boutique Inn","City View Hotel","Heritage Mansion"],
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
                        "type":tl,"type_label":tl,"district":["North","Central","South"][ci],
                        "description":tdesc(tl)})
    return out

@st.cache_data(ttl=180, show_spinner=False)
def fetch_places(clat,clon,country,is_cn,tls_t,lpt,_seed):
    random.seed(_seed); tls=list(tls_t)
    if is_cn:
        raw=search_cn(clat,clon,tls,lpt)
    else:
        raw=search_intl(clat,clon,tls,lpt)
    raw=geo_dedup(raw)
    warn=None
    if not raw:
        raw=demo_places(clat,clon,tls,lpt,_seed)
        warn="Live data unavailable — showing curated sample places."
    df=pd.DataFrame(raw)
    for c in ["address","phone","website","type","type_label","district","description"]:
        if c not in df.columns: df[c]=""
    df["rating"]=pd.to_numeric(df["rating"],errors="coerce").fillna(0.)
    for c in ["name","address","district","description","type_label","type"]:
        df[c]=df[c].apply(_ss)
    return df.sort_values("rating",ascending=False).reset_index(drop=True), warn

# ══════════════════════════════════════════════════════════════════
# WISHLIST HELPERS
# ══════════════════════════════════════════════════════════════════
def wl_key(u): return f"_wl_{u}"
def wl_add(username,place):
    if WISHLIST_EXT:
        try: _wl_add(username,place); return
        except Exception: pass
    k=wl_key(username); lst=st.session_state.get(k,[])
    if place.get("name","") not in {p.get("name","") for p in lst}:
        lst.append(place); st.session_state[k]=lst

def wl_remove(username,name):
    if WISHLIST_EXT:
        try: _wl_remove(username,name); return
        except Exception: pass
    k=wl_key(username)
    st.session_state[k]=[p for p in st.session_state.get(k,[]) if p.get("name","")!=name]

def wl_get(username):
    if WISHLIST_EXT:
        try: return _wl_get(username)
        except Exception: pass
    return st.session_state.get(wl_key(username),[])

def wl_check(username,name):
    if WISHLIST_EXT:
        try: return _wl_check(username,name)
        except Exception: pass
    return any(p.get("name","")==name for p in st.session_state.get(wl_key(username),[]))

def save_itin_fn(username,itinerary,city,title):
    if WISHLIST_EXT:
        try: _save_itin_ext(username,itinerary,city,title); return
        except Exception: pass
    k=f"_saved_itins_{username}"
    saved=st.session_state.get(k,[])
    saved.append({"city":city,"title":title,"data":itinerary,
                  "saved_at":datetime.now().strftime("%Y-%m-%d %H:%M")})
    st.session_state[k]=saved[-10:]

# ══════════════════════════════════════════════════════════════════
# AI MUST-SEE
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600,show_spinner=False)
def get_ai_mustsee(city,country,days,types_t):
    types=list(types_t)
    if DEEPSEEK_KEY:
        try:
            t_str=", ".join(types[:5])
            prompt=(f"Recommend {min(days*3,12)} must-visit famous places in {city} "
                    f"for a {days}-day trip. Types: {t_str}. Only real well-known landmarks. "
                    f"Return JSON array only. Each item: name, type, why (max 10 words), "
                    f"rating (4.0-5.0), lat (number), lon (number), duration_min (integer).")
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
                        cleaned=[]
                        for it in items[:12]:
                            if not isinstance(it,dict): continue
                            cleaned.append({"name":_ss(it.get("name","")),
                                            "type":_ss(it.get("type","🏛️ Attraction")),
                                            "why":_ss(it.get("why","")),
                                            "rating":float(it.get("rating",4.5)),
                                            "lat":float(it.get("lat",0)),
                                            "lon":float(it.get("lon",0)),
                                            "duration_min":int(it.get("duration_min",60))})
                        if cleaned: return cleaned
        except Exception: pass
    BUILTIN={
        "tokyo":[
            {"name":"Senso-ji Temple","type":"🏛️ Attraction","why":"Tokyo oldest temple","rating":4.9,"lat":35.7148,"lon":139.7967,"duration_min":60},
            {"name":"Shibuya Crossing","type":"🏛️ Attraction","why":"World busiest crossing","rating":4.8,"lat":35.6595,"lon":139.7004,"duration_min":20},
            {"name":"Shinjuku Gyoen","type":"🌿 Park","why":"Imperial garden with cherry blossoms","rating":4.8,"lat":35.6851,"lon":139.7103,"duration_min":90},
        ],
        "paris":[
            {"name":"Eiffel Tower","type":"🏛️ Attraction","why":"Iconic symbol of Paris","rating":4.8,"lat":48.8584,"lon":2.2945,"duration_min":90},
            {"name":"Louvre Museum","type":"🏛️ Attraction","why":"World largest art museum","rating":4.8,"lat":48.8606,"lon":2.3376,"duration_min":180},
        ],
        "london":[
            {"name":"British Museum","type":"🏛️ Attraction","why":"Free world class museum","rating":4.8,"lat":51.5194,"lon":-0.1270,"duration_min":120},
            {"name":"Tower of London","type":"🏛️ Attraction","why":"900 years of royal history","rating":4.7,"lat":51.5081,"lon":-0.0759,"duration_min":90},
        ],
        "singapore":[
            {"name":"Gardens by the Bay","type":"🌿 Park","why":"Futuristic Supertree Grove","rating":4.9,"lat":1.2816,"lon":103.8636,"duration_min":120},
            {"name":"Marina Bay Sands SkyPark","type":"🏛️ Attraction","why":"Iconic skyline views","rating":4.8,"lat":1.2834,"lon":103.8607,"duration_min":60},
        ],
        "dubai":[
            {"name":"Burj Khalifa","type":"🏛️ Attraction","why":"World tallest building","rating":4.8,"lat":25.1972,"lon":55.2744,"duration_min":90},
        ],
        "bali":[
            {"name":"Tanah Lot Temple","type":"🏛️ Attraction","why":"Sunset cliff temple","rating":4.8,"lat":-8.6215,"lon":115.0865,"duration_min":90},
            {"name":"Tegallalang Rice Terraces","type":"🌿 Park","why":"Iconic green terraces","rating":4.7,"lat":-8.4319,"lon":115.2786,"duration_min":60},
        ],
    }
    city_lc=city.strip().lower()
    for k,v in BUILTIN.items():
        if k in city_lc: return v
    return []

# ══════════════════════════════════════════════════════════════════
# MAP BUILDER
# ══════════════════════════════════════════════════════════════════
def build_map(df,lat,lon,itinerary):
    if not FOLIUM_OK: return None
    m=folium.Map(location=[lat,lon],zoom_start=13,tiles="CartoDB dark_matter")
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
                                color=dc,weight=3,opacity=.6,dash_array="4 4").add_to(m)
    for _,row in df.iterrows():
        v=vi.get(row["name"])
        if v:
            di,sn,_=v; color=DAY_COLORS[di%len(DAY_COLORS)]; label=str(sn)
        else:
            color="#374151"; label="·"
        nm=_ss(row.get("name",""))
        dur=estimate_duration(nm,row.get("type_label",""))
        pop=(f"<div style='font-family:-apple-system,sans-serif;background:#1a1040;color:#fff;"
             f"padding:12px;border-radius:10px;min-width:160px'>"
             f"<b style='font-size:.88rem'>{nm}</b><br>"
             f"<span style='color:#c4b5fd;font-size:.74rem'>⭐ {row['rating']:.1f}</span><br>"
             f"<span style='color:#a78bfa;font-size:.72rem'>⏱ {format_duration(dur)}</span>"
             f"</div>")
        folium.Marker([row["lat"],row["lon"]],
            popup=folium.Popup(pop,max_width=200),
            tooltip=f"{nm}",
            icon=folium.DivIcon(
                html=(f'<div style="width:26px;height:26px;border-radius:50%;background:{color};'
                      f'border:2px solid rgba(255,255,255,.85);display:flex;align-items:center;'
                      f'justify-content:center;color:white;font-size:10px;font-weight:700;'
                      f'box-shadow:0 2px 12px rgba(0,0,0,.4)">{label}</div>'),
                icon_size=(26,26),icon_anchor=(13,13),
            )).add_to(m)
    return m

# ══════════════════════════════════════════════════════════════════
# HTML EXPORT
# ══════════════════════════════════════════════════════════════════
def build_html(itinerary, city, day_budgets, country):
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    avg=round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    def esc(s):
        s=_ss(s)
        return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
    total_stops=sum(len(v) for v in itinerary.values() if isinstance(v,list))
    mjs=[]; pjs=[]; mlats=[]; mlons=[]
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        c=DAY_COLORS[di%len(DAY_COLORS)]; pc=[]
        for si,s in enumerate(stops):
            lat=s.get("lat",0); lon=s.get("lon",0)
            if not lat or not lon: continue
            mlats.append(lat); mlons.append(lon); pc.append(f"[{lat},{lon}]")
            nm_js=esc(s.get("name","")).replace("'","&#39;")
            mjs.append(f'{{"lat":{lat},"lon":{lon},"n":"{nm_js}","d":{di+1},"s":{si+1},"c":"{c}"}}')
        if len(pc)>1: pjs.append(f'{{"c":"{c}","pts":[{",".join(pc)}]}}')
    clat=sum(mlats)/len(mlats) if mlats else 35.
    clon=sum(mlons)/len(mlons) if mlons else 139.
    days_html=""
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        du=day_budgets[di] if di<len(day_budgets) else avg
        c=DAY_COLORS[di%len(DAY_COLORS)]
        tl_stops=build_timeline(stops)
        rows_html=""
        for si,s in enumerate(tl_stops):
            arrive=s.get("arrive_time",""); depart=s.get("depart_time","")
            dur=s.get("duration_min",60)
            tr=s.get("transport_to_next") or {}
            route=esc(f"{tr.get('mode','--')} {tr.get('duration','')}") if tr else "Last stop"
            rows_html+=(f"<tr><td>{si+1}</td><td>{esc(arrive)}-{esc(depart)}</td>"
                        f"<td><b>{esc(s.get('name',''))}</b></td>"
                        f"<td>{esc(s.get('type_label',''))}</td>"
                        f"<td>{format_duration(dur)}</td>"
                        f"<td>{'⭐ '+str(s.get('rating',0)) if s.get('rating') else '--'}</td>"
                        f"<td>{route}</td></tr>")
        total_dur=sum(s.get("duration_min",60) for s in tl_stops)
        days_html+=(f"<h3 style='color:{c};margin:24px 0 8px'>{esc(dl)} — {len(stops)} stops · ~{format_duration(total_dur)}</h3>"
                    f"<table><thead><tr><th>#</th><th>Time</th><th>Place</th><th>Type</th>"
                    f"<th>Duration</th><th>Rating</th><th>Getting There</th></tr></thead><tbody>{rows_html}</tbody></table>")
    return (f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Voyager — {esc(city.title())}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{{box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
background:linear-gradient(135deg,#0f0a1e,#1a0f3c);color:#f8f8ff;max-width:980px;margin:0 auto;padding:32px 24px}}
h1{{font-size:2rem;font-weight:300;letter-spacing:-.02em;margin:0 0 8px;color:#e0d9ff}}
h3{{font-size:.96rem;font-weight:600;margin:20px 0 8px}}
.badge{{display:inline-flex;align-items:center;background:rgba(139,92,246,.15);border:1px solid rgba(167,139,250,.3);
border-radius:20px;padding:3px 14px;font-size:.72rem;color:#c4b5fd;font-weight:600;margin-bottom:14px}}
.summary{{background:rgba(139,92,246,.08);border:1px solid rgba(139,92,246,.15);border-radius:12px;
padding:12px 16px;font-size:.82rem;color:#a78bfa;margin-bottom:20px}}
#map{{height:420px;border-radius:18px;margin:20px 0;border:1px solid rgba(139,92,246,.2)}}
table{{width:100%;border-collapse:collapse;font-size:.80rem;background:rgba(255,255,255,.04);
border-radius:12px;overflow:hidden;margin:4px 0}}
thead tr{{background:rgba(139,92,246,.10)}}
th,td{{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.06);text-align:left}}
th{{font-weight:600;color:#a78bfa;font-size:.70rem;text-transform:uppercase;letter-spacing:.05em}}
tr:hover td{{background:rgba(139,92,246,.05)}}
footer{{color:rgba(167,139,250,.4);font-size:.70rem;margin-top:40px;text-align:center;padding-top:20px;border-top:1px solid rgba(255,255,255,.06)}}
</style></head><body>
<div class="badge">✦ Voyager AI Travel Planner</div>
<h1>✈ {esc(city.title())}</h1>
<div class="summary">${sum(day_budgets[:len(itinerary)])} total &nbsp;·&nbsp; {len(itinerary)} days &nbsp;·&nbsp; {total_stops} stops &nbsp;·&nbsp; avg ${avg}/day</div>
<div id="map"></div>{days_html}
<footer>Voyager AI Travel Planner &nbsp;·&nbsp; Ctrl+P to save as PDF</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
var m=L.map('map').setView([{clat},{clon}],13);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{attribution:'CartoDB'}}).addTo(m);
[{",".join(mjs)}].forEach(function(mk){{
var ic=L.divIcon({{html:'<div style="width:24px;height:24px;border-radius:50%;background:'+mk.c+';border:2px solid rgba(255,255,255,.85);display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:700">'+mk.s+'</div>',iconSize:[24,24],iconAnchor:[12,12]}});
L.marker([mk.lat,mk.lon],{{icon:ic}}).bindPopup('<b>'+mk.n+'</b><br>Day '+mk.d+' Stop '+mk.s).addTo(m);
}});
[{",".join(pjs)}].forEach(function(pl){{L.polyline(pl.pts,{{color:pl.c,weight:3,opacity:.6,dashArray:'4 4'}}).addTo(m);}});
</script></body></html>""").encode("utf-8")

# ══════════════════════════════════════════════════════════════════
# PROGRESS BAR RENDERER
# ══════════════════════════════════════════════════════════════════
def render_progress(current_step):
    steps = [
        ("✦", "Welcome"),
        ("◎", "Destination"),
        ("◈", "Preferences"),
        ("◉", "Itinerary"),
    ]
    circles_html = ""
    for i, (icon, label) in enumerate(steps):
        n = i + 1
        if n < current_step:
            state = "done"
            circle_content = "✓"
        elif n == current_step:
            state = "active"
            circle_content = icon
        else:
            state = "pending"
            circle_content = str(n)

        circles_html += f"""
        <div class="progress-step">
            <div class="step-circle {state}">{circle_content}</div>
            <div class="step-label {state}">{label}</div>
        </div>
        """
        if i < len(steps) - 1:
            connector_class = "done-connector" if n < current_step else ""
            circles_html += f'<div class="step-connector {connector_class}"></div>'

    st.markdown(f"""
    <div class="progress-bar-outer">
        <div class="progress-steps">{circles_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# STEP 1 — Login / Guest
# ══════════════════════════════════════════════════════════════════
def step_1():
    render_progress(1)
    st.markdown("""
    <div class="glass-card">
      <div class="step-hero-label">Welcome to Voyager</div>
      <div class="step-hero-title">Your <em>intelligent</em><br>travel companion</div>
      <div class="step-hero-sub">Plan extraordinary journeys with AI-powered itineraries tailored exclusively to you.</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown("""
        <div style="background:rgba(124,58,237,0.08);border:1.5px solid rgba(167,139,250,0.2);
        border-radius:20px;padding:28px;text-align:center;margin-bottom:4px">
          <div style="font-size:2.2rem;margin-bottom:12px">◉</div>
          <div style="font-weight:600;font-size:1rem;color:#fff;margin-bottom:6px">Sign In</div>
          <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);line-height:1.5">
            Access your saved itineraries, wishlist & travel points
          </div>
        </div>
        """, unsafe_allow_html=True)

        if AUTH_OK:
            with st.form("login_form", clear_on_submit=False):
                uname = st.text_input("Username", placeholder="Enter username", key="li_u")
                pw    = st.text_input("Password", type="password", placeholder="Enter password", key="li_p")
                sub = st.form_submit_button("Sign In →", use_container_width=True)
                if sub:
                    if uname and pw:
                        ok, msg, tok = login_user(uname.strip(), pw)
                        if ok:
                            st.session_state["_auth_token"] = tok
                            st.session_state["user_mode"] = "logged_in"
                            if POINTS_OK:
                                try: add_points(uname.strip(), "daily_login")
                                except Exception: pass
                            st.session_state["step"] = 2
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter your credentials.")

            st.markdown('<div style="text-align:center;color:rgba(255,255,255,0.3);font-size:0.75rem;margin:8px 0">New here?</div>', unsafe_allow_html=True)
            with st.expander("Create Account", expanded=False):
                with st.form("reg_form"):
                    ru = st.text_input("Username", placeholder="Choose username", key="re_u")
                    re_email = st.text_input("Email", placeholder="your@email.com", key="re_e")
                    rp = st.text_input("Password", type="password", placeholder="Min 6 chars", key="re_p")
                    rsub = st.form_submit_button("Create Account", use_container_width=True)
                    if rsub:
                        ok, msg = register_user(ru.strip(), rp, re_email.strip())
                        if ok: st.success(msg + " Please sign in.")
                        else:  st.error(msg)
        else:
            if st.button("Continue as Signed In →", use_container_width=True):
                st.session_state["user_mode"] = "logged_in"
                st.session_state["step"] = 2
                st.rerun()

    with col_b:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1.5px solid rgba(255,255,255,0.08);
        border-radius:20px;padding:28px;text-align:center;margin-bottom:4px">
          <div style="font-size:2.2rem;margin-bottom:12px">◎</div>
          <div style="font-weight:600;font-size:1rem;color:#fff;margin-bottom:6px">Continue as Guest</div>
          <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);line-height:1.5">
            Jump straight in — no account required. Full planning access.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Feature bullets
        features = ["✦  AI-powered itinerary generation","✦  Real-time place discovery",
                    "✦  Interactive route mapping","✦  Cost estimation & budgeting",
                    "✦  Day-by-day schedule"]
        for f in features:
            st.markdown(f'<div style="font-size:0.78rem;color:rgba(255,255,255,0.4);padding:5px 0;padding-left:4px">{f}</div>',
                        unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if st.button("Explore as Guest →", key="guest_btn", use_container_width=True):
            st.session_state["user_mode"] = "guest"
            st.session_state["step"] = 2
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# STEP 2 — Destination
# ══════════════════════════════════════════════════════════════════
def step_2():
    render_progress(2)

    user = _cur_user()
    if user:
        greeting = f"Welcome back, {user['username']}."
    else:
        greeting = "Where shall we take you?"

    st.markdown(f"""
    <div class="glass-card">
      <div class="step-hero-label">Step 2 of 4</div>
      <div class="step-hero-title">Choose your<br><em>destination</em></div>
      <div class="step-hero-sub">{greeting} Every great journey begins with a destination.</div>
    </div>
    """, unsafe_allow_html=True)

    # Country selector
    col1, col2 = st.columns([1, 1], gap="medium")
    all_countries = sorted(WORLD_CITIES.keys())

    with col1:
        sel_country = st.selectbox(
            "Country / Region",
            [""] + all_countries,
            index=([""] + all_countries).index(st.session_state.get("dest_country","")) if st.session_state.get("dest_country","") in all_countries else 0,
            key="s2_country"
        )
    with col2:
        city_override = st.text_input("Or type any city", placeholder="e.g. Kyoto, Cusco, Santorini…", key="s2_city_ov")

    # City pills if country selected
    if sel_country and not city_override:
        cities = WORLD_CITIES.get(sel_country, [])
        cur_city = st.session_state.get("dest_city","")
        st.markdown("<div style='margin-top:4px;font-size:0.72rem;color:rgba(167,139,250,0.6);text-transform:uppercase;letter-spacing:0.06em;font-weight:600'>Select city</div>", unsafe_allow_html=True)
        # Use clickable buttons in a horizontal flow
        n_cols = min(len(cities), 5)
        if n_cols > 0:
            rows = [cities[i:i+5] for i in range(0, len(cities), 5)]
            for row in rows:
                cols = st.columns(len(row))
                for ci, city in enumerate(row):
                    with cols[ci]:
                        selected = (city == cur_city and sel_country == st.session_state.get("dest_country",""))
                        btn_label = f"✓ {city}" if selected else city
                        if st.button(btn_label, key=f"cpill_{city}", use_container_width=True):
                            st.session_state["dest_city"] = city
                            st.session_state["dest_country"] = sel_country
                            st.rerun()

    # Popular destinations
    POPULAR = [
        ("🗼","Tokyo","Japan"),("🗽","New York","USA"),("🗺️","Paris","France"),
        ("🏖️","Bali","Indonesia"),("🌆","Dubai","UAE"),("🏰","Rome","Italy"),
        ("🌸","Kyoto","Japan"),("🎭","London","United Kingdom"),
        ("🌃","Barcelona","Spain"),("🌴","Bangkok","Thailand"),
    ]
    st.markdown("<div style='margin-top:20px;font-size:0.72rem;color:rgba(167,139,250,0.6);text-transform:uppercase;letter-spacing:0.06em;font-weight:600'>Popular destinations</div>", unsafe_allow_html=True)
    rows_p = [POPULAR[i:i+5] for i in range(0,len(POPULAR),5)]
    for row in rows_p:
        cols = st.columns(len(row))
        for ci, (icon, city, country) in enumerate(row):
            with cols[ci]:
                sel = (city == st.session_state.get("dest_city",""))
                lbl = f"✓ {icon} {city}" if sel else f"{icon} {city}"
                if st.button(lbl, key=f"pop_{city}", use_container_width=True):
                    st.session_state["dest_city"] = city
                    st.session_state["dest_country"] = country
                    if city_override:
                        st.session_state["s2_city_ov"] = ""
                    st.rerun()

    # Determine final city
    if city_override.strip():
        final_city = city_override.strip()
        final_country_name = sel_country or ""
    elif st.session_state.get("dest_city",""):
        final_city = st.session_state["dest_city"]
        final_country_name = st.session_state.get("dest_country","")
    else:
        final_city = ""
        final_country_name = ""

    # Show selected
    if final_city:
        cc = COUNTRY_CODES.get(final_country_name,"INT")
        st.markdown(f"""
        <div style="margin-top:20px;padding:16px 20px;background:rgba(124,58,237,0.1);
        border:1px solid rgba(167,139,250,0.3);border-radius:14px;
        display:flex;align-items:center;gap:12px">
          <div style="font-size:1.5rem">✈️</div>
          <div>
            <div style="font-weight:600;color:#fff;font-size:0.95rem">{final_city}</div>
            <div style="font-size:0.75rem;color:rgba(167,139,250,0.7)">{final_country_name} · {cc}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Nav
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    nav_col1, nav_col2 = st.columns([1,1], gap="small")
    with nav_col1:
        if st.button("← Back", key="s2_back", use_container_width=True):
            st.session_state["step"] = 1
            st.rerun()
    with nav_col2:
        if st.button("Next: Preferences →", key="s2_next", use_container_width=True):
            if not final_city:
                st.warning("Please select a destination.")
            else:
                # Geocode
                city_key = final_city.strip().lower()
                cc = COUNTRY_CODES.get(final_country_name,"INT")
                is_cn = city_key in CN_CITIES
                intl_d = INTL_CITIES.get(city_key)
                if is_cn:
                    lat,lon = CN_CITIES[city_key]
                elif intl_d:
                    lat,lon = intl_d[0],intl_d[1]
                    cc = intl_d[2]
                else:
                    with st.spinner("Locating destination…"):
                        coord = _nom(final_city)
                        if not coord:
                            st.error(f"Could not find '{final_city}'. Please try a different spelling.")
                            st.stop()
                        lat,lon = coord

                st.session_state["dest_city"] = final_city
                st.session_state["dest_country"] = final_country_name
                st.session_state["dest_lat"] = lat
                st.session_state["dest_lon"] = lon
                st.session_state["dest_country_code"] = cc
                st.session_state["dest_is_cn"] = is_cn
                st.session_state["step"] = 3
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# STEP 3 — Preferences
# ══════════════════════════════════════════════════════════════════
def step_3():
    render_progress(3)

    city  = st.session_state.get("dest_city","Your City")
    cc    = st.session_state.get("dest_country_code","INT")

    st.markdown(f"""
    <div class="glass-card">
      <div class="step-hero-label">Step 3 of 4</div>
      <div class="step-hero-title">Craft your<br><em>experience</em></div>
      <div class="step-hero-sub">Tell us how you like to travel and we'll build a perfectly curated itinerary for {city}.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown('<div style="font-size:0.72rem;color:rgba(167,139,250,0.7);text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:8px">Trip Duration</div>', unsafe_allow_html=True)
        days = st.number_input("Number of days", min_value=1, max_value=10, value=st.session_state.get("trip_days",3), step=1, key="s3_days", label_visibility="collapsed")

        st.markdown('<div style="font-size:0.72rem;color:rgba(167,139,250,0.7);text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin:20px 0 8px">Daily Budget (USD)</div>', unsafe_allow_html=True)
        budget = st.slider("Daily budget", 10, 500, st.session_state.get("trip_budget",80), 5, format="$%d", key="s3_budget", label_visibility="collapsed")

        sym, rate = _local_rate(cc)
        local_amt = round(budget * rate)
        st.markdown(f'<div style="font-size:0.78rem;color:rgba(167,139,250,0.5);margin-top:4px">${budget} USD ≈ {sym}{local_amt:,} per day</div>', unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.72rem;color:rgba(167,139,250,0.7);text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin:20px 0 8px">Start Point (Optional)</div>', unsafe_allow_html=True)
        depart_addr = st.text_input("Start point", placeholder="e.g. Tokyo Station, Airport…", key="s3_depart", label_visibility="collapsed")
        arrive_addr = st.text_input("End point", placeholder="e.g. Narita Airport…", key="s3_arrive", label_visibility="collapsed")
        hotel_addr  = st.text_input("Hotel / Accommodation", placeholder="Hotel name or address…", key="s3_hotel", label_visibility="collapsed")

    with col2:
        st.markdown('<div style="font-size:0.72rem;color:rgba(167,139,250,0.7);text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:8px">What do you love?</div>', unsafe_allow_html=True)

        type_options = list(PTYPES.keys())
        prev_types = st.session_state.get("trip_types", ["🏛️ Attraction","🍜 Restaurant"])

        # Grid of toggleable type buttons
        selected_types = list(prev_types)
        rows_t = [type_options[i:i+2] for i in range(0,len(type_options),2)]
        for row in rows_t:
            tcols = st.columns(len(row))
            for tci, tl in enumerate(row):
                with tcols[tci]:
                    is_sel = tl in selected_types
                    color = PTYPES[tl]["color"]
                    label_txt = f"✓ {tl}" if is_sel else tl
                    if st.button(label_txt, key=f"type_{tl}", use_container_width=True):
                        if is_sel and len(selected_types) > 1:
                            selected_types.remove(tl)
                        elif not is_sel:
                            selected_types.append(tl)
                        st.session_state["trip_types"] = selected_types
                        st.rerun()

        st.markdown('<div style="font-size:0.72rem;color:rgba(167,139,250,0.7);text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin:20px 0 8px">Stops per day (each type)</div>', unsafe_allow_html=True)
        quotas = {}
        for tl in selected_types:
            prev_q = (st.session_state.get("trip_quotas") or {}).get(tl, 1)
            n = st.slider(f"{tl}", 0, 4, prev_q, 1, key=f"quota_{tl}")
            if n > 0: quotas[tl] = n
        if not quotas and selected_types:
            quotas = {selected_types[0]: 1}

    # Nav
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    nav_c1, nav_c2 = st.columns([1,1], gap="small")
    with nav_c1:
        if st.button("← Back", key="s3_back", use_container_width=True):
            st.session_state["step"] = 2
            st.rerun()
    with nav_c2:
        if st.button("Build My Itinerary ✦", key="s3_next", use_container_width=True):
            st.session_state["trip_days"] = int(days)
            st.session_state["trip_budget"] = int(budget)
            st.session_state["trip_types"] = selected_types
            st.session_state["trip_quotas"] = quotas
            st.session_state["trip_depart"] = depart_addr.strip()
            st.session_state["trip_arrive"] = arrive_addr.strip()
            st.session_state["trip_hotel"]  = hotel_addr.strip()
            st.session_state["day_budgets"] = [int(budget)] * int(days)

            # Generate itinerary
            _generate_itinerary()

# ══════════════════════════════════════════════════════════════════
# ITINERARY GENERATION
# ══════════════════════════════════════════════════════════════════
def _generate_itinerary():
    city    = st.session_state["dest_city"]
    lat     = st.session_state["dest_lat"]
    lon     = st.session_state["dest_lon"]
    country = st.session_state["dest_country_code"]
    is_cn   = st.session_state.get("dest_is_cn", False)
    ndays   = st.session_state["trip_days"]
    budget  = st.session_state["trip_budget"]
    types   = st.session_state["trip_types"]
    quotas  = st.session_state["trip_quotas"]
    day_budgets = [budget] * ndays
    seed    = st.session_state.get("seed", 42)

    total_q = sum(quotas.values()) if quotas else 4
    lpt = max(20, total_q * 5)

    with st.spinner(f"Discovering places in {city}…"):
        try:
            df, warn = fetch_places(lat, lon, country, is_cn, tuple(types), lpt, seed)
        except Exception as e:
            st.error(f"Place search error: {e}")
            return

    if warn:
        st.info(warn)

    if df is None or df.empty:
        st.error("No places found. Please try a different city or types.")
        return

    # Geocode start/end/hotel
    depart_c = arrive_c = hotel_c = None
    depart_addr = st.session_state.get("trip_depart","")
    arrive_addr = st.session_state.get("trip_arrive","")
    hotel_addr  = st.session_state.get("trip_hotel","")

    def _gc(addr):
        if not addr: return None
        if is_cn: return _amap_geo(f"{addr} {city}") or _nom(f"{addr} {city}")
        return _nom(f"{addr} {city}") or _nom(addr)

    with st.spinner("Looking up locations…"):
        if hotel_addr:  hotel_c  = _gc(hotel_addr)
        if depart_addr: depart_c = _gc(depart_addr)
        if arrive_addr: arrive_c = _gc(arrive_addr)

    itinerary = {}
    if AI_OK:
        day_quotas = [dict(quotas)] * ndays
        with st.spinner("Crafting your itinerary…"):
            try:
                itinerary = generate_itinerary(
                    df, ndays, day_quotas,
                    hotel_lat  =hotel_c[0]  if hotel_c  else None,
                    hotel_lon  =hotel_c[1]  if hotel_c  else None,
                    depart_lat =depart_c[0] if depart_c else None,
                    depart_lon =depart_c[1] if depart_c else None,
                    arrive_lat =arrive_c[0] if arrive_c else None,
                    arrive_lon =arrive_c[1] if arrive_c else None,
                    day_min_ratings=[3.5]*ndays,
                    day_anchor_lats=[lat]*ndays,
                    day_anchor_lons=[lon]*ndays,
                    country=country, city=city,
                    day_budgets=day_budgets,
                )
            except Exception as e:
                st.error(f"Itinerary error: {e}")
    else:
        # Fallback: simple assignment
        used = set(); d_idx = 0
        for d in range(ndays):
            day_key = f"Day {d+1}"; stops = []
            for tl, cnt in (quotas or {}).items():
                pool = df[(df["type_label"]==tl)&(~df["name"].isin(used))].head(cnt)
                for _,row in pool.iterrows():
                    stops.append(row.to_dict()); used.add(row["name"])
            itinerary[day_key] = stops

    st.session_state["_itin"] = itinerary
    st.session_state["_df"]   = df
    st.session_state["_hotel_c"]  = hotel_c
    st.session_state["_depart_c"] = depart_c
    st.session_state["_arrive_c"] = arrive_c
    st.session_state["day_budgets"] = day_budgets

    # Save for logged-in user
    user = _cur_user()
    if user and itinerary:
        save_itin_fn(user["username"], itinerary, city, city.title())
        if POINTS_OK:
            try: add_points(user["username"],"share",note=city)
            except Exception: pass

    st.session_state["step"] = 4
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# STEP 4 — Itinerary View
# ══════════════════════════════════════════════════════════════════
def step_4():
    render_progress(4)

    city        = st.session_state.get("dest_city","")
    country     = st.session_state.get("dest_country_code","INT")
    lat         = st.session_state.get("dest_lat",35.)
    lon         = st.session_state.get("dest_lon",139.)
    ndays       = st.session_state.get("trip_days",3)
    day_budgets = st.session_state.get("day_budgets",[60]*ndays)
    itinerary   = st.session_state.get("_itin",{})
    df          = st.session_state.get("_df",pd.DataFrame())
    user        = _cur_user()

    total_stops = sum(len(v) for v in itinerary.values() if isinstance(v,list))
    avg_rating  = df["rating"].replace(0,float("nan")).mean() if df is not None and not df.empty else 0
    total_budget = sum(day_budgets[:len(itinerary)]) if day_budgets else 0

    # Hero
    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:0">
      <div class="step-hero-label">Your Journey</div>
      <div class="step-hero-title">{city.title()}</div>
      <div class="step-hero-sub">AI-curated across {ndays} days · {total_stops} handpicked stops</div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("📍 Places",  str(len(df)) if df is not None else "0")
    m2.metric("📅 Days",    str(ndays))
    m3.metric("🗓️ Stops",  str(total_stops))
    m4.metric("⭐ Avg",     f"{avg_rating:.1f}" if avg_rating else "—")
    m5.metric("💰 Total",   f"${total_budget}")

    # Action bar
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    ab1, ab2, ab3, ab4 = st.columns(4)
    with ab1:
        if st.button("← Edit Preferences", key="s4_back", use_container_width=True):
            st.session_state["step"] = 3
            st.rerun()
    with ab2:
        if st.button("🔀 Shuffle & Rebuild", key="s4_shuffle", use_container_width=True):
            st.session_state["seed"] = random.randint(1,99999)
            st.cache_data.clear()
            st.session_state["step"] = 3
            _generate_itinerary()
    with ab3:
        if user and st.button("♥ Save Itinerary", key="s4_save", use_container_width=True):
            save_itin_fn(user["username"], itinerary, city, city.title())
            st.toast(f"Itinerary for {city.title()} saved!")
    with ab4:
        if itinerary:
            try:
                html_data = build_html(itinerary, city, day_budgets, country)
                st.download_button("⬇️ Export HTML", data=html_data,
                    file_name=f"voyager_{city.lower().replace(' ','_')}.html",
                    mime="text/html;charset=utf-8", use_container_width=True)
            except Exception:
                st.button("⬇️ Export", disabled=True, use_container_width=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Main tabs
    tab_itin, tab_map, tab_budget, tab_ai, tab_explore = st.tabs([
        "📋 Itinerary", "🗺️ Map", "💰 Budget", "✦ AI Picks", "🔍 Explore More"
    ])

    with tab_itin:
        _render_itinerary_tab(itinerary, df, day_budgets, country, city, user)

    with tab_map:
        _render_map_tab(df, lat, lon, itinerary)

    with tab_budget:
        _render_budget_tab(itinerary, day_budgets, country, ndays)

    with tab_ai:
        _render_ai_tab(city, country, ndays, st.session_state.get("trip_types",[]), itinerary)

    with tab_explore:
        _render_explore_tab(df, itinerary, day_budgets, country, user)

# ── Itinerary Tab ─────────────────────────────────────────────────
def _render_itinerary_tab(itinerary, df, day_budgets, country, city, user):
    if not itinerary:
        st.info("No itinerary generated yet.")
        return

    if isinstance(day_budgets, int): day_budgets=[day_budgets]*30
    current_itin = st.session_state.get("_itin", itinerary)

    for di, (day_key, stops) in enumerate(current_itin.items()):
        if not isinstance(stops, list): continue
        color = DAY_COLORS[di % len(DAY_COLORS)]
        d_usd = day_budgets[di] if di < len(day_budgets) else day_budgets[-1]
        tl_stops = build_timeline(stops)
        total_dur = sum(s.get("duration_min",60) for s in tl_stops)

        is_expanded = st.session_state.get(f"exp_{day_key}", di==0)

        # Day header card
        exp_icon = "▲" if is_expanded else "▼"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1.5px solid rgba(255,255,255,0.08);
        border-left:3px solid {color};border-radius:16px;padding:18px 22px;margin:10px 0 6px;
        cursor:pointer;position:relative;overflow:hidden">
          <div style="position:absolute;top:0;left:0;right:0;height:1px;
          background:linear-gradient(90deg,{color},transparent)"></div>
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:36px;height:36px;border-radius:50%;background:{color}22;
            border:1.5px solid {color}66;display:flex;align-items:center;justify-content:center;
            font-size:0.8rem;font-weight:700;color:{color}">{di+1}</div>
            <div style="flex:1">
              <div style="font-weight:600;font-size:0.95rem;color:#fff">{day_key}</div>
              <div style="font-size:0.72rem;color:rgba(255,255,255,0.4);margin-top:2px">
                {len(stops)} stops · ${d_usd}/day · ~{format_duration(total_dur)}
              </div>
            </div>
            <div style="font-size:0.72rem;color:rgba(167,139,250,0.5)">{exp_icon} Details</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        toggle_col, _ = st.columns([1,5])
        with toggle_col:
            if st.button(f"{'Collapse' if is_expanded else 'Expand'} {day_key}", key=f"toggle_{day_key}", use_container_width=True):
                st.session_state[f"exp_{day_key}"] = not is_expanded
                st.rerun()

        if is_expanded:
            # Timeline of stops
            for si, s in enumerate(tl_stops):
                nm   = _ss(s.get("name",""))
                tl   = _ss(s.get("type_label",""))
                rat  = s.get("rating",0)
                dist = _ss(s.get("district",""))
                arr  = s.get("arrive_time","")
                dep  = s.get("depart_time","")
                dur  = s.get("duration_min",60)
                tr   = s.get("transport_to_next") or {}
                _, cs = cost_est(tl, d_usd, country)

                with st.container():
                    sc1, sc2, sc3, sc4 = st.columns([1,5,3,1])

                    with sc1:
                        st.markdown(f"""
                        <div style="text-align:center;padding-top:6px">
                          <div style="width:28px;height:28px;border-radius:50%;
                          background:linear-gradient(135deg,{color},{color}88);
                          display:flex;align-items:center;justify-content:center;
                          color:#fff;font-size:11px;font-weight:700;margin:auto">{si+1}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with sc2:
                        st.markdown(f"""
                        <div style="padding:8px 0">
                          <div style="font-weight:600;font-size:0.88rem;color:#fff">{nm}</div>
                          <div style="font-size:0.72rem;color:rgba(255,255,255,0.4);margin-top:2px">
                            {tl}{'&nbsp;·&nbsp;⭐ '+str(rat) if rat else ''}{'&nbsp;·&nbsp;'+dist if dist else ''}
                          </div>
                          <div style="font-size:0.70rem;color:rgba(167,139,250,0.6);margin-top:3px">💰 {cs}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with sc3:
                        time_html = '<div style="padding:8px 0">'
                        if arr:
                            time_html += f'<span class="time-chip">⏰ {arr}–{dep}</span>'
                        time_html += f'<div style="margin-top:4px"><span style="font-size:0.70rem;color:rgba(245,158,11,0.7)">⏱ {format_duration(dur)}</span></div>'
                        if tr:
                            time_html += f'<div style="margin-top:3px"><span class="tr-chip">🚇 {_ss(tr.get("mode",""))} · {_ss(tr.get("duration",""))}</span></div>'
                        time_html += '</div>'
                        st.markdown(time_html, unsafe_allow_html=True)

                    with sc4:
                        # Swap button
                        sw_key = f"_sw_{day_key}_{si}"
                        sw_open = st.session_state.get(sw_key, False)
                        if st.button("↔" if not sw_open else "✕", key=f"sw_{day_key}_{si}", help="Swap stop"):
                            st.session_state[sw_key] = not sw_open
                            st.rerun()
                        if user:
                            if st.button("♡" if not wl_check(user["username"],nm) else "♥",
                                         key=f"wl_{day_key}_{si}_{nm[:4]}"):
                                if wl_check(user["username"],nm):
                                    wl_remove(user["username"],nm); st.toast(f"Removed {nm}")
                                else:
                                    wl_add(user["username"],{"name":nm,"lat":s.get("lat",0),"lon":s.get("lon",0),
                                                              "type_label":tl,"rating":rat,"address":s.get("address","")})
                                    st.toast(f"Saved {nm}!")
                                st.rerun()

                # Swap panel
                if st.session_state.get(f"_sw_{day_key}_{si}", False):
                    _render_swap(current_itin, df if df is not None else pd.DataFrame(), day_key, si)

                st.markdown('<div style="height:1px;background:rgba(255,255,255,0.04);margin:2px 8px"></div>', unsafe_allow_html=True)

            # Reorder stops
            with st.expander(f"↕️ Reorder stops in {day_key}", expanded=False):
                stops_list = list(current_itin.get(day_key,[]))
                if len(stops_list) > 1:
                    st.markdown('<div class="reorder-hint">Move stops up or down to reorder your day</div>', unsafe_allow_html=True)
                    for si, s in enumerate(stops_list):
                        nm = _ss(s.get("name",""))
                        rc1,rc2,rc3 = st.columns([5,1,1])
                        with rc1:
                            st.markdown(f'<div style="font-size:0.83rem;color:#fff;padding:6px 0">{si+1}. {nm}</div>', unsafe_allow_html=True)
                        with rc2:
                            if si > 0 and st.button("↑", key=f"up_{day_key}_{si}"):
                                stops_list[si], stops_list[si-1] = stops_list[si-1], stops_list[si]
                                new_itin = dict(current_itin); new_itin[day_key] = stops_list
                                st.session_state["_itin"] = new_itin; st.rerun()
                        with rc3:
                            if si < len(stops_list)-1 and st.button("↓", key=f"dn_{day_key}_{si}"):
                                stops_list[si], stops_list[si+1] = stops_list[si+1], stops_list[si]
                                new_itin = dict(current_itin); new_itin[day_key] = stops_list
                                st.session_state["_itin"] = new_itin; st.rerun()

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Swap Panel ────────────────────────────────────────────────────
def _render_swap(itinerary, df, day_key, stop_idx):
    stops = itinerary.get(day_key,[])
    if not isinstance(stops,list) or stop_idx>=len(stops): return
    cur = stops[stop_idx]; cur_type = cur.get("type_label","")
    used = {s["name"] for sl in itinerary.values() if isinstance(sl,list) for s in sl}

    if df.empty:
        st.warning("No alternatives available."); return

    cands = (df[(df["type_label"]==cur_type)&(~df["name"].isin(used))]
             .sort_values("rating",ascending=False).head(4))

    st.markdown(f"""
    <div style="background:rgba(124,58,237,0.08);border:1px solid rgba(167,139,250,0.2);
    border-radius:14px;padding:16px;margin:6px 0">
      <div style="font-weight:600;font-size:0.82rem;color:#c4b5fd;margin-bottom:10px">
        Swap: <span style="color:#fff">{_ss(cur.get('name',''))}</span>
      </div>
    """, unsafe_allow_html=True)

    if cands.empty:
        st.markdown('<div style="color:rgba(255,255,255,0.4);font-size:0.78rem">No alternatives found for this type.</div>', unsafe_allow_html=True)
    else:
        cols = st.columns(min(len(cands),4))
        for i,(_,alt) in enumerate(cands.iterrows()):
            with cols[i%4]:
                nm = _ss(alt["name"]); rat = alt.get("rating",0)
                dur = estimate_duration(nm, alt.get("type_label",""))
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:10px;
                border:1px solid rgba(255,255,255,0.08);margin-bottom:6px">
                  <div style="font-weight:600;font-size:0.79rem;color:#fff">{nm}</div>
                  <div style="font-size:0.68rem;color:rgba(255,255,255,0.4)">⭐ {rat} · {format_duration(dur)}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Select", key=f"swc_{day_key}_{stop_idx}_{nm[:6]}", use_container_width=True):
                    new_it = dict(st.session_state.get("_itin", itinerary))
                    ds = list(new_it.get(day_key,[])); ds[stop_idx] = alt.to_dict()
                    new_it[day_key] = ds
                    st.session_state["_itin"] = new_it
                    st.session_state.pop(f"_sw_{day_key}_{stop_idx}", None)
                    st.toast(f"Replaced with {nm}"); st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Cancel swap", key=f"swcancel_{day_key}_{stop_idx}"):
        st.session_state.pop(f"_sw_{day_key}_{stop_idx}", None); st.rerun()

# ── Map Tab ───────────────────────────────────────────────────────
def _render_map_tab(df, lat, lon, itinerary):
    if not FOLIUM_OK:
        st.info("Install streamlit-folium for interactive maps.")
        return
    st.caption("Dark-mode route map · Tap markers for details")
    try:
        m = build_map(df, lat, lon, itinerary)
        if m:
            st.markdown('<div class="map-wrap">', unsafe_allow_html=True)
            st_folium(m, width="100%", height=520, returned_objects=[])
            st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Map error: {e}")

# ── Budget Tab ────────────────────────────────────────────────────
def _render_budget_tab(itinerary, day_budgets, country, ndays):
    if not itinerary: return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*ndays
    sym, rate = _local_rate(country)
    tots=[]
    for di,(dl,stops) in enumerate(itinerary.items()):
        if not isinstance(stops,list) or not stops: continue
        du = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
        t = sum(cost_est(s.get("type_label",""),du,country)[0] for s in stops)
        tots.append((dl,t,du))
    if not tots: return

    gt = sum(t for _,t,_ in tots)
    gb = sum(d for _,_,d in tots)

    # Budget grid
    st.markdown('<div class="budget-grid">', unsafe_allow_html=True)
    for dl,t,du in tots:
        over = t > du*1.1
        lo_u=round(t*.8); hi_u=round(t*1.2)
        rng = f"${lo_u}-${hi_u}"
        flag = "⚠️" if over else "✓"
        st.markdown(f"""
        <div class="budget-cell" style="{'border-color:rgba(239,68,68,0.3)' if over else ''}">
          <div class="budget-lbl">{_ss(dl)}</div>
          <div class="budget-amt">${round(t)}{' !' if over else ''}</div>
          <div class="budget-sub">{rng}</div>
          <div class="budget-sub">${du}/day {flag}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Total card
    lo=round(gt*.8); hi=round(gt*1.2)
    gs = f"${lo}–${hi}"
    if country!="US":
        gs += f" ({sym}{round(lo*rate)}–{sym}{round(hi*rate)})"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(124,58,237,0.12),rgba(147,51,234,0.08));
    border:1.5px solid rgba(167,139,250,0.25);border-radius:18px;padding:24px;text-align:center;margin:12px 0">
      <div style="font-size:0.68rem;color:rgba(167,139,250,0.7);text-transform:uppercase;letter-spacing:0.1em;font-weight:600;margin-bottom:8px">TOTAL ESTIMATED COST</div>
      <div style="font-size:2.2rem;font-weight:700;color:#fff;letter-spacing:-0.03em">${round(gt)}</div>
      <div style="font-size:0.82rem;color:rgba(255,255,255,0.4);margin-top:6px">{gs}</div>
      <div style="font-size:0.72rem;color:rgba(167,139,250,0.5);margin-top:4px">{ndays if ndays else len(tots)}d · ${gb} budget · per person</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📊 Full cost breakdown", expanded=False):
        rows=[]
        for di,(dl,stops) in enumerate(itinerary.items()):
            if not isinstance(stops,list): continue
            du = day_budgets[di] if di<len(day_budgets) else day_budgets[-1]
            for s in stops:
                tl=s.get("type_label",""); _,cr=cost_est(tl,du,country)
                dur=estimate_duration(_ss(s.get("name","")),tl)
                rows.append({"Day":_ss(dl),"Place":_ss(s.get("name","")),"Type":tl,
                              "Duration":format_duration(dur),"Est. Cost":cr})
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    # Google Calendar export
    with st.expander("📅 Add to Google Calendar", expanded=False):
        sd = st.date_input("Trip start date", key="cal_date")
        if sd and itinerary:
            import urllib.parse
            bd = datetime.combine(sd, datetime.min.time())
            SM={"9:00 AM":(9,0),"10:30 AM":(10,30),"12:00 PM":(12,0),"1:30 PM":(13,30),
                "3:00 PM":(15,0),"4:30 PM":(16,30),"6:00 PM":(18,0),"7:30 PM":(19,30)}
            for di,(dl,stops) in enumerate(itinerary.items()):
                if not isinstance(stops,list): continue
                st.markdown(f"**{_ss(dl)}**")
                for si,s in enumerate(stops):
                    nm=_ss(s.get("name","Stop"))
                    hh,mm=SM.get(s.get("time_slot","9:00 AM"),(9+si,0))
                    dd=bd+timedelta(days=di)
                    st2=dd.replace(hour=min(hh,23),minute=mm,second=0)
                    et=st2+timedelta(hours=1,minutes=30)
                    p={"action":"TEMPLATE","text":f"{nm} ({st.session_state.get('dest_city','').title()})",
                       "dates":f"{st2.strftime('%Y%m%dT%H%M%S')}/{et.strftime('%Y%m%dT%H%M%S')}"}
                    url="https://calendar.google.com/calendar/render?"+urllib.parse.urlencode(p)
                    st.markdown(f'<a href="{url}" target="_blank" style="color:#c4b5fd;font-size:.80rem;text-decoration:none">+ {nm[:35]}</a>', unsafe_allow_html=True)

# ── AI Picks Tab ──────────────────────────────────────────────────
def _render_ai_tab(city, country, ndays, sel_types, itinerary):
    picks = get_ai_mustsee(city, country, ndays, tuple(sel_types))
    if not picks:
        st.info("AI recommendations unavailable for this city.")
        return

    existing = {s.get("name","") for stops in itinerary.values()
                if isinstance(stops,list) for s in stops}
    current_itin = st.session_state.get("_itin", itinerary)
    day_keys = list(current_itin.keys())

    st.markdown(f"""
    <div class="ai-panel">
      <div style="font-weight:700;font-size:0.88rem;color:#c4b5fd;margin-bottom:4px">✦ AI Must-See Picks</div>
      <div style="font-size:0.72rem;color:rgba(167,139,250,0.5);margin-bottom:14px">
        {"AI-powered" if DEEPSEEK_KEY else "Curated"} highlights for {city}
      </div>
    """, unsafe_allow_html=True)

    rows_ai = [picks[i:i+3] for i in range(0,len(picks),3)]
    for row in rows_ai:
        cols = st.columns(len(row))
        for ci, rec in enumerate(row):
            with cols[ci]:
                nm = _ss(rec.get("name",""))
                tp = _ss(rec.get("type",""))
                why = _ss(rec.get("why",""))
                rat = rec.get("rating",4.5)
                dur = rec.get("duration_min",60)
                already = nm in existing

                st.markdown(f"""
                <div class="ai-item">
                  <div style="font-weight:600;font-size:0.83rem;color:#fff">{nm}</div>
                  <div style="color:#a78bfa;font-size:0.70rem;margin-top:2px">{tp}</div>
                  <div style="color:rgba(255,255,255,0.4);font-size:0.73rem;margin-top:4px">{why}</div>
                  <div style="display:flex;gap:8px;margin-top:6px;align-items:center">
                    <span style="font-size:0.68rem;color:#c4b5fd">⭐ {rat}</span>
                    <span style="font-size:0.68rem;color:rgba(245,158,11,0.7)">⏱ {format_duration(dur)}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if already:
                    st.markdown('<div style="font-size:0.70rem;color:#34d399;margin-top:4px">✓ In itinerary</div>', unsafe_allow_html=True)
                elif day_keys:
                    sel_day = st.selectbox("Add to:", ["Choose day…"]+day_keys,
                                           key=f"ai_day_{nm[:8]}_{ci}", label_visibility="collapsed")
                    if sel_day != "Choose day…":
                        if st.button("+ Add", key=f"ai_add_{nm[:8]}_{ci}", use_container_width=True):
                            pd_ = {"name":nm,"lat":rec.get("lat",0),"lon":rec.get("lon",0),
                                   "type_label":tp,"rating":rat,"address":"","district":"","description":why}
                            stops_list = list(current_itin.get(sel_day,[]))
                            if nm not in {s.get("name","") for s in stops_list}:
                                stops_list.append({**pd_,"time_slot":"TBD","transport_to_next":None})
                                new_itin = dict(current_itin); new_itin[sel_day]=stops_list
                                st.session_state["_itin"]=new_itin
                                st.toast(f"Added {nm}!"); st.rerun()
                            else:
                                st.toast("Already in itinerary!", icon="ℹ️")

    st.markdown("</div>", unsafe_allow_html=True)

# ── Explore Tab ───────────────────────────────────────────────────
def _render_explore_tab(df, itinerary, day_budgets, country, user):
    if df is None or df.empty:
        st.info("No additional places to explore.")
        return
    if isinstance(day_budgets,int): day_budgets=[day_budgets]*30
    avg = round(sum(day_budgets)/len(day_budgets)) if day_budgets else 60
    current_itin = st.session_state.get("_itin", itinerary)
    day_keys = list(current_itin.keys())
    snames = {s.get("name","") for stops in current_itin.values()
              if isinstance(stops,list) for s in stops}
    unscheduled = [row for _,row in df.iterrows() if row["name"] not in snames]
    if not unscheduled:
        st.info("All discovered places are already in your itinerary! Try shuffling for new options.")
        return

    CATS=[("Attractions",["🏛️ Attraction"]),("Dining",["🍜 Restaurant","☕ Cafe"]),
          ("Nature",["🌿 Park"]),("Shopping",["🛍️ Shopping"]),("Nightlife",["🍺 Bar/Nightlife"])]
    by_type={}
    for r in unscheduled:
        tl=r.get("type_label","") or r.get("type","")
        by_type.setdefault(tl,[]).append(r)
    cat_data=[]
    covered=set()
    for cn,tls in CATS:
        items=[]; 
        for tl in tls: items.extend(by_type.get(tl,[])); covered.add(tl)
        if items: cat_data.append((cn,items))
    others=[r for tl,rs in by_type.items() if tl not in covered for r in rs]
    if others: cat_data.append(("Other",others))

    for cn,places in cat_data:
        sk=f"_rec_{cn}"
        if sk not in st.session_state: st.session_state[sk]=0
        hdr1,hdr2=st.columns([8,1])
        with hdr1:
            st.markdown(f'<div style="font-weight:600;font-size:0.88rem;color:#fff;margin:16px 0 8px">{cn} <span style="font-size:0.72rem;color:rgba(167,139,250,0.5)">({min(8,len(places))}/{len(places)})</span></div>', unsafe_allow_html=True)
        with hdr2:
            if st.button("↺",key=f"rf_{cn}",use_container_width=True):
                st.session_state[sk]=(st.session_state[sk]+1)%9999

        import random as _r
        _r.seed(st.session_state[sk])
        picks=sorted(_r.sample(places,min(8,len(places))),key=lambda r:r.get("rating",0),reverse=True)

        rows_e=[picks[i:i+4] for i in range(0,len(picks),4)]
        for row in rows_e:
            cols=st.columns(len(row))
            for ci,p in enumerate(row):
                with cols[ci]:
                    nm=_ss(p.get("name","")); tl=_ss(p.get("type_label","") or p.get("type",""))
                    rat=p.get("rating",0); dist=_ss(p.get("district","") or "")
                    addr=_ss(p.get("address","") or "")[:45]
                    _,cs=cost_est(tl,avg,country)
                    dur=estimate_duration(nm,tl)

                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px;padding:14px;margin-bottom:6px">
                      <div style="font-weight:600;font-size:0.83rem;color:#fff;margin-bottom:3px">{nm}</div>
                      <div style="font-size:0.72rem;color:rgba(255,255,255,0.4)">{tl}{'&nbsp;·&nbsp;'+dist if dist else ''}</div>
                      {"<div style='font-size:0.68rem;color:rgba(167,139,250,0.5);margin-top:2px'>"+addr+"</div>" if addr and "Sample" not in addr else ""}
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
                        <span style="font-size:0.72rem;color:#fff">{'⭐ '+str(rat) if rat else ''}</span>
                        <span style="font-size:0.68rem;color:rgba(245,158,11,0.7)">⏱ {format_duration(dur)}</span>
                      </div>
                      <div style="font-size:0.70rem;color:rgba(167,139,250,0.6);margin-top:4px">💰 {cs}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if day_keys:
                        sel_day = st.selectbox("",["day…"]+day_keys,
                                               key=f"ex_day_{cn}_{nm[:5]}_{ci}",
                                               label_visibility="collapsed")
                        ec1,ec2=st.columns(2)
                        with ec1:
                            if sel_day!="day…" and st.button("+",key=f"exadd_{cn}_{nm[:5]}_{ci}",use_container_width=True):
                                stops_list=list(current_itin.get(sel_day,[]))
                                if nm not in {s.get("name","") for s in stops_list}:
                                    stops_list.append({"name":nm,"lat":p.get("lat",0),"lon":p.get("lon",0),
                                                       "type_label":tl,"rating":rat,"address":addr,
                                                       "district":dist,"description":_ss(p.get("description","")),
                                                       "time_slot":"TBD","transport_to_next":None})
                                    new_itin=dict(current_itin); new_itin[sel_day]=stops_list
                                    st.session_state["_itin"]=new_itin
                                    st.toast(f"Added {nm}!"); st.rerun()
                                else: st.toast("Already added!",icon="ℹ️")
                        with ec2:
                            if user:
                                saved=wl_check(user["username"],nm)
                                if st.button("♥" if saved else "♡",key=f"exwl_{cn}_{nm[:5]}_{ci}",use_container_width=True):
                                    if saved: wl_remove(user["username"],nm); st.toast(f"Removed {nm}")
                                    else: wl_add(user["username"],{"name":nm,"lat":p.get("lat",0),"lon":p.get("lon",0),"type_label":tl,"rating":rat}); st.toast(f"Saved {nm}!")
                                    st.rerun()

# ══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="wizard-wrap">', unsafe_allow_html=True)

# Voyager wordmark
st.markdown("""
<div style="text-align:center;margin-bottom:32px">
  <div style="font-family:'Cormorant Garamond',serif;font-size:1.6rem;font-weight:300;
  color:rgba(255,255,255,0.9);letter-spacing:0.12em">
    V O Y A G E R
  </div>
  <div style="font-size:0.62rem;color:rgba(167,139,250,0.5);letter-spacing:0.2em;
  text-transform:uppercase;margin-top:3px">AI Travel Planner</div>
</div>
""", unsafe_allow_html=True)

step = st.session_state.get("step", 1)

if step == 1:
    step_1()
elif step == 2:
    step_2()
elif step == 3:
    step_3()
elif step == 4:
    step_4()
else:
    st.session_state["step"] = 1
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center;padding:24px;color:rgba(167,139,250,0.25);font-size:0.68rem;
letter-spacing:0.08em;text-transform:uppercase">
  Voyager · AI-Powered Luxury Travel Planning · All rights reserved
</div>
""", unsafe_allow_html=True)
