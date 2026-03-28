"""points_system.py — Points, check-ins, vouchers"""

import json, time, uuid
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

POINTS_MAP = {
    "checkin": 50, "checkin_bonus": 20, "share": 40,
    "daily_login": 10, "invite_friend": 100, "complete_day": 80,
}

VOUCHER_CATALOG = [
    {"id":"v10",  "name":"10% Travel Discount",    "cost":300,  "emoji":"🎫", "desc":"10% off next booking"},
    {"id":"v20",  "name":"20% Dining Voucher",      "cost":500,  "emoji":"🍽️","desc":"20% off partner restaurants"},
    {"id":"v50",  "name":"$5 Transport Credit",     "cost":200,  "emoji":"🚇", "desc":"$5 off taxi/transit"},
    {"id":"v100", "name":"$10 Activity Voucher",    "cost":800,  "emoji":"🎟️","desc":"$10 off attraction tickets"},
    {"id":"vgold","name":"Free Premium PDF Export", "cost":250,  "emoji":"📄", "desc":"One premium itinerary download"},
]


def _load():
    p = DATA_DIR / "users.json"
    try: return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception: return {}

def _save(d):
    p = DATA_DIR / "users.json"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def add_points(username, action, bonus=0, note=""):
    pts = POINTS_MAP.get(action, 0) + bonus
    if pts <= 0: return get_points(username)
    users = _load(); u = users.get(username.strip().lower())
    if not u: return 0
    u["points"] = u.get("points", 0) + pts
    h = u.setdefault("points_history",[])
    h.append({"action":action,"pts":pts,"note":note,"ts":int(time.time())})
    if len(h) > 100: u["points_history"] = h[-100:]
    _save(users); return u["points"]


def get_points(username):
    return _load().get(username.strip().lower(), {}).get("points", 0)


def get_points_history(username, limit=10):
    h = _load().get(username.strip().lower(), {}).get("points_history",[])
    return list(reversed(h[-limit:]))


def checkin(username, place_name, in_itinerary=False):
    users = _load(); u = users.get(username.strip().lower())
    if not u: return 0, "User not found."
    now = int(time.time())
    cis = u.setdefault("checkins",[])
    if any(c.get("place") == place_name and now - c.get("ts",0) < 14400 for c in cis):
        return 0, "Already checked in here recently."
    cis.append({"place": place_name, "ts": now}); _save(users)
    bonus = POINTS_MAP["checkin_bonus"] if in_itinerary else 0
    total = add_points(username, "checkin", bonus=bonus, note=place_name)
    earned = POINTS_MAP["checkin"] + bonus
    return earned, f"+{earned} pts!" + (" Bonus! 🎉" if bonus else "")


def redeem_voucher(username, voucher_id):
    v = next((x for x in VOUCHER_CATALOG if x["id"] == voucher_id), None)
    if not v: return False, "Voucher not found."
    users = _load(); u = users.get(username.strip().lower())
    if not u: return False, "User not found."
    pts = u.get("points",0)
    if pts < v["cost"]: return False, f"Need {v['cost']} pts (you have {pts})."
    u["points"] = pts - v["cost"]
    code = str(uuid.uuid4())[:8].upper()
    u.setdefault("vouchers",[]).append({"id":voucher_id,"name":v["name"],"code":code,"ts":int(time.time())})
    u.setdefault("points_history",[]).append({"action":"redeem","pts":-v["cost"],"note":v["name"],"ts":int(time.time())})
    _save(users)
    return True, f"🎉 Code: **{code}** — valid 30 days."


def render_points_panel(username, lang="EN"):
    import streamlit as st
    import pandas as pd
    from i18n import t as _ti
    pts = get_points(username)
    level = ("Bronze 🥉" if pts < 500 else "Silver 🥈" if pts < 1500
             else "Gold 🥇" if pts < 5000 else "Platinum 💎")
    pct = min(100, int((pts % 500) / 500 * 100)) if pts < 5000 else 100
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#c97d35,#e8a558);"
        f"border-radius:14px;padding:16px;color:white;margin-bottom:12px'>"
        f"<div style='font-size:1.6rem;font-weight:800'>{pts:,} pts</div>"
        f"<div style='font-size:.85rem;opacity:.9'>{level} · {_ti('points_balance',lang)}</div>"
        f"<div style='background:rgba(255,255,255,.3);border-radius:4px;height:6px;margin-top:8px'>"
        f"<div style='background:white;height:6px;border-radius:4px;width:{pct}%'></div>"
        f"</div></div>", unsafe_allow_html=True)
    st.markdown(f"**{_ti('points_redeem',lang)}**")
    cols = st.columns(2)
    for i, v in enumerate(VOUCHER_CATALOG):
        with cols[i % 2]:
            can = pts >= v["cost"]
            if st.button(f"{v['emoji']} {v['name']} ({v['cost']} pts)",
                         key=f"redeem_{v['id']}_{username}",
                         disabled=not can, use_container_width=True, help=v["desc"]):
                ok, msg = redeem_voucher(username, v["id"])
                (st.success if ok else st.error)(msg)
                if ok: st.rerun()
    hist = get_points_history(username, 8)
    if hist:
        with st.expander(f"📜 {_ti('points_history',lang)}", expanded=False):
            rows = [{"Time": time.strftime("%m/%d %H:%M", time.localtime(h["ts"])),
                     "Action": h["action"], "Note": h.get("note",""),
                     "Pts": ("+" if h["pts"]>0 else "")+str(h["pts"])}
                    for h in hist]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_checkin_button(username, place_name, in_itinerary=False, lang="EN"):
    import streamlit as st
    from i18n import t as _ti
    if st.button(_ti("points_checkin", lang), key=f"ci_{username}_{place_name[:15]}",
                 use_container_width=True):
        earned, msg = checkin(username, place_name, in_itinerary)
        (st.success if earned > 0 else st.info)(
            f"{_ti('points_checkin_done',lang)} {msg}" if earned > 0 else msg)
