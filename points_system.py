"""points_system.py — Points, check-ins, and voucher system"""

import json
import time
import uuid
from pathlib import Path
from typing import Optional
import streamlit as st

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ── Point values ─────────────────────────────────────────────────────────────
POINTS = {
    "checkin":        50,    # check in at a listed place
    "checkin_bonus":  20,    # extra if place is in itinerary
    "first_visit":    30,    # first time visiting a new city
    "share":          40,    # sharing an itinerary
    "review":         25,    # leaving a rating/review
    "daily_login":    10,    # logging in
    "invite_friend":  100,   # invited friend registers
    "complete_day":   80,    # completes all stops in a day
}

# ── Vouchers ─────────────────────────────────────────────────────────────────
VOUCHER_CATALOG = [
    {"id": "v10",  "name": "10% Travel Discount",         "cost": 300,  "emoji": "🎫", "desc": "10% off on your next booking"},
    {"id": "v20",  "name": "20% Dining Voucher",          "cost": 500,  "emoji": "🍽️", "desc": "20% off at partner restaurants"},
    {"id": "v50",  "name": "$5 Transport Credit",         "cost": 200,  "emoji": "🚇", "desc": "$5 off on taxi or transit"},
    {"id": "v100", "name": "$10 Activity Voucher",        "cost": 800,  "emoji": "🎟️", "desc": "$10 off on attraction tickets"},
    {"id": "vip",  "name": "Priority Route Planning",     "cost": 1500, "emoji": "⭐", "desc": "Skip-the-queue AI priority slot"},
    {"id": "vgold","name": "Free Premium PDF Export",     "cost": 250,  "emoji": "📄", "desc": "One premium itinerary download"},
]


def _load_users() -> dict:
    p = DATA_DIR / "users.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_users(data: dict):
    p = DATA_DIR / "users.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Points operations ────────────────────────────────────────────────────────

def add_points(username: str, action: str, bonus: int = 0, note: str = "") -> int:
    """Add points for an action. Returns new total."""
    pts = POINTS.get(action, 0) + bonus
    if pts <= 0:
        return get_points(username)
    users = _load_users()
    user = users.get(username.strip().lower())
    if not user:
        return 0
    user["points"] = user.get("points", 0) + pts
    history = user.setdefault("points_history", [])
    history.append({
        "action": action,
        "pts": pts,
        "note": note,
        "ts": int(time.time()),
    })
    if len(history) > 100:
        user["points_history"] = history[-100:]
    _save_users(users)
    return user["points"]

def get_points(username: str) -> int:
    users = _load_users()
    return users.get(username.strip().lower(), {}).get("points", 0)

def get_points_history(username: str, limit: int = 10) -> list:
    users = _load_users()
    hist = users.get(username.strip().lower(), {}).get("points_history", [])
    return list(reversed(hist[-limit:]))


# ── Check-in ─────────────────────────────────────────────────────────────────

def checkin(username: str, place_name: str, in_itinerary: bool = False) -> tuple[int, str]:
    """Check in at a place. Returns (pts_earned, message)."""
    users = _load_users()
    user = users.get(username.strip().lower())
    if not user:
        return 0, "User not found."
    checkins = user.setdefault("checkins", [])
    # Prevent double check-in within 4 hours
    now = int(time.time())
    recent = [c for c in checkins if c.get("place") == place_name and now - c.get("ts", 0) < 14400]
    if recent:
        return 0, "Already checked in here recently. Come back later!"
    checkins.append({"place": place_name, "ts": now})
    _save_users(users)
    bonus = POINTS["checkin_bonus"] if in_itinerary else 0
    total = add_points(username, "checkin", bonus=bonus, note=place_name)
    earned = POINTS["checkin"] + bonus
    msg = f"+{earned} points! {'Bonus for itinerary stop! 🎉' if bonus else ''}"
    return earned, msg


# ── Voucher system ────────────────────────────────────────────────────────────

def redeem_voucher(username: str, voucher_id: str) -> tuple[bool, str]:
    """Attempt to redeem a voucher. Returns (success, message)."""
    voucher = next((v for v in VOUCHER_CATALOG if v["id"] == voucher_id), None)
    if not voucher:
        return False, "Voucher not found."
    users = _load_users()
    user = users.get(username.strip().lower())
    if not user:
        return False, "User not found."
    pts = user.get("points", 0)
    if pts < voucher["cost"]:
        return False, f"Not enough points. You need {voucher['cost']} but have {pts}."
    user["points"] = pts - voucher["cost"]
    vouchers_used = user.setdefault("vouchers", [])
    vouchers_used.append({
        "id": voucher_id,
        "name": voucher["name"],
        "code": str(uuid.uuid4())[:8].upper(),
        "redeemed_at": int(time.time()),
    })
    # Record points deduction
    history = user.setdefault("points_history", [])
    history.append({
        "action": "redeem",
        "pts": -voucher["cost"],
        "note": voucher["name"],
        "ts": int(time.time()),
    })
    _save_users(users)
    code = vouchers_used[-1]["code"]
    return True, f"🎉 Redeemed! Your code: **{code}**. Valid 30 days."

def get_vouchers(username: str) -> list:
    users = _load_users()
    return users.get(username.strip().lower(), {}).get("vouchers", [])


# ── Streamlit UI Components ───────────────────────────────────────────────────

def render_points_panel(username: str, lang: str = "EN"):
    """Render points + voucher UI."""
    from i18n import t as _t

    pts = get_points(username)
    hist = get_points_history(username, limit=8)

    # Points balance card
    level = "Bronze 🥉" if pts < 500 else "Silver 🥈" if pts < 1500 else "Gold 🥇" if pts < 5000 else "Platinum 💎"
    pct = min(100, int((pts % 500) / 500 * 100)) if pts < 5000 else 100

    st.markdown(
        f"""<div style='background:linear-gradient(135deg,#c97d35,#e8a558);
        border-radius:14px;padding:16px;color:white;margin-bottom:12px'>
        <div style='font-size:1.6rem;font-weight:800'>{pts:,} pts</div>
        <div style='font-size:0.85rem;opacity:0.9'>{level} · {_t("points_balance",lang)}</div>
        <div style='background:rgba(255,255,255,0.3);border-radius:4px;height:6px;margin-top:8px'>
          <div style='background:white;height:6px;border-radius:4px;width:{pct}%'></div>
        </div></div>""",
        unsafe_allow_html=True,
    )

    # Voucher shop
    st.markdown(f"**{_t('points_redeem',lang)} — Voucher Shop**")
    cols = st.columns(2)
    for i, v in enumerate(VOUCHER_CATALOG):
        with cols[i % 2]:
            can = pts >= v["cost"]
            btn_label = f"{v['emoji']} {v['name']} ({v['cost']} pts)"
            if st.button(
                btn_label,
                key=f"redeem_{v['id']}_{username}",
                disabled=not can,
                use_container_width=True,
                help=v["desc"],
            ):
                ok, msg = redeem_voucher(username, v["id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # Points history
    if hist:
        with st.expander(f"📜 {_t('points_history',lang)}", expanded=False):
            import pandas as pd
            rows = []
            for h in hist:
                ts = time.strftime("%m/%d %H:%M", time.localtime(h["ts"]))
                sign = "+" if h["pts"] > 0 else ""
                rows.append({"Time": ts, "Action": h["action"], "Note": h.get("note",""), "Pts": f"{sign}{h['pts']}"})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_checkin_button(
    username: str,
    place_name: str,
    in_itinerary: bool = False,
    lang: str = "EN",
):
    """Render a check-in button for a single place."""
    from i18n import t as _t
    key = f"ci_{username}_{place_name[:20]}"
    if st.button(_t("points_checkin", lang), key=key, use_container_width=True):
        earned, msg = checkin(username, place_name, in_itinerary)
        if earned > 0:
            st.success(f"{_t('points_checkin_done', lang)} {msg}")
        else:
            st.info(msg)
