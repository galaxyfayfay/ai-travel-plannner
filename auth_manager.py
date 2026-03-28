"""auth_manager.py — Lightweight local auth (JSON-based, upgradeable to Firebase/Supabase)"""

import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

# Storage path (local JSON file — swap for DB in production)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

# ── Helpers ──────────────────────────────────────────────────────────────────

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ── User management ──────────────────────────────────────────────────────────

def register_user(username: str, password: str, email: str = "") -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    username = username.strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    users = _load_json(USERS_FILE)
    if username in users:
        return False, "Username already taken."

    users[username] = {
        "username": username,
        "email": email.strip(),
        "password_hash": _hash_pw(password),
        "created_at": int(time.time()),
        "points": 0,
        "checkins": [],
        "vouchers": [],
        "wishlist": [],
        "itineraries": [],
        "collaborations": [],
    }
    _save_json(USERS_FILE, users)
    return True, "Account created successfully!"

def login_user(username: str, password: str) -> tuple[bool, str, str]:
    """Login. Returns (success, message, session_token)."""
    username = username.strip().lower()
    users = _load_json(USERS_FILE)
    user = users.get(username)
    if not user:
        return False, "User not found.", ""
    if user["password_hash"] != _hash_pw(password):
        return False, "Incorrect password.", ""

    # Create session
    token = str(uuid.uuid4())
    sessions = _load_json(SESSIONS_FILE)
    sessions[token] = {
        "username": username,
        "created_at": int(time.time()),
        "expires_at": int(time.time()) + 86400 * 7,  # 7 days
    }
    _save_json(SESSIONS_FILE, sessions)
    return True, f"Welcome back, {username}!", token

def get_user_from_session(token: str) -> Optional[dict]:
    """Return user data if session is valid."""
    if not token:
        return None
    sessions = _load_json(SESSIONS_FILE)
    session = sessions.get(token)
    if not session:
        return None
    if session["expires_at"] < int(time.time()):
        return None  # expired
    users = _load_json(USERS_FILE)
    return users.get(session["username"])

def logout_user(token: str):
    """Invalidate session token."""
    sessions = _load_json(SESSIONS_FILE)
    sessions.pop(token, None)
    _save_json(SESSIONS_FILE, sessions)

def update_user(username: str, updates: dict):
    """Merge updates into user record."""
    users = _load_json(USERS_FILE)
    if username in users:
        users[username].update(updates)
        _save_json(USERS_FILE, users)

def get_user(username: str) -> Optional[dict]:
    users = _load_json(USERS_FILE)
    return users.get(username.strip().lower())

# ── Collaboration ────────────────────────────────────────────────────────────

COLLAB_FILE = DATA_DIR / "collaborations.json"

def create_collab_link(owner: str, itinerary_id: str) -> str:
    """Create a shareable collaboration link token."""
    collabs = _load_json(COLLAB_FILE)
    token = str(uuid.uuid4())[:12].upper()
    collabs[token] = {
        "owner": owner,
        "itinerary_id": itinerary_id,
        "created_at": int(time.time()),
        "editors": [],
    }
    _save_json(COLLAB_FILE, collabs)
    return token

def join_collab(username: str, token: str) -> tuple[bool, str]:
    """Join a collaboration via token."""
    collabs = _load_json(COLLAB_FILE)
    collab = collabs.get(token.upper())
    if not collab:
        return False, "Invalid or expired link."
    if username in collab["editors"]:
        return True, "Already a collaborator."
    collab["editors"].append(username)
    collabs[token.upper()] = collab
    _save_json(COLLAB_FILE, collabs)
    return True, f"Joined as collaborator on {collab['owner']}'s itinerary!"

def get_collab(token: str) -> Optional[dict]:
    collabs = _load_json(COLLAB_FILE)
    return collabs.get(token.upper())
wishlist_manager.py - Wishlist & Place Replacement
"""wishlist_manager.py — Wishlist, saved itineraries, place swap"""

import json
import time
from pathlib import Path
from typing import Optional
import streamlit as st

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

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

# ── Wishlist ─────────────────────────────────────────────────────────────────

def add_to_wishlist(username: str, place: dict) -> bool:
    """Add a place to user's wishlist. Returns True if newly added."""
    users = _load_users()
    user = users.get(username.strip().lower())
    if not user:
        return False
    wl = user.setdefault("wishlist", [])
    # Dedup by name
    existing_names = {w.get("name","") for w in wl}
    if place.get("name","") in existing_names:
        return False
    wl.append({
        "name": place.get("name",""),
        "lat": place.get("lat"),
        "lon": place.get("lon"),
        "type_label": place.get("type_label",""),
        "rating": place.get("rating", 0),
        "address": place.get("address",""),
        "city": place.get("_city",""),
        "added_at": int(time.time()),
    })
    users[username.strip().lower()] = user
    _save_users(users)
    return True

def remove_from_wishlist(username: str, place_name: str):
    users = _load_users()
    user = users.get(username.strip().lower())
    if not user:
        return
    user["wishlist"] = [w for w in user.get("wishlist", []) if w.get("name") != place_name]
    _save_users(users)

def get_wishlist(username: str) -> list:
    users = _load_users()
    user = users.get(username.strip().lower(), {})
    return user.get("wishlist", [])

def is_in_wishlist(username: str, place_name: str) -> bool:
    return any(w.get("name") == place_name for w in get_wishlist(username))

# ── Saved itineraries ────────────────────────────────────────────────────────

def save_itinerary(username: str, itinerary: dict, city: str, label: str = ""):
    """Save a complete itinerary to user's history."""
    users = _load_users()
    user = users.get(username.strip().lower())
    if not user:
        return
    itins = user.setdefault("itineraries", [])
    if len(itins) >= 20:  # cap at 20
        itins = itins[-19:]
    itins.append({
        "label": label or city,
        "city": city,
        "saved_at": int(time.time()),
        "days": len(itinerary),
        "stops": sum(len(v) for v in itinerary.values()),
        "data": itinerary,
    })
    user["itineraries"] = itins
    _save_users(users)

def get_saved_itineraries(username: str) -> list:
    users = _load_users()
    user = users.get(username.strip().lower(), {})
    return list(reversed(user.get("itineraries", [])))

# ── Place swap ───────────────────────────────────────────────────────────────

def swap_place_in_itinerary(
    itinerary: dict,
    day_label: str,
    stop_idx: int,
    new_place: dict,
) -> dict:
    """Replace a single stop in an itinerary with a different place."""
    import copy
    result = copy.deepcopy(itinerary)
    if day_label in result and 0 <= stop_idx < len(result[day_label]):
        old = result[day_label][stop_idx]
        # Preserve scheduling fields
        new_place_copy = dict(new_place)
        new_place_copy["time_slot"] = old.get("time_slot", "")
        new_place_copy["dwell_min"] = old.get("dwell_min", 60)
        result[day_label][stop_idx] = new_place_copy
    return result


# ── Streamlit Wishlist UI Component ─────────────────────────────────────────

def render_wishlist_panel(username: str, lang: str = "EN"):
    """Render wishlist management UI (call inside a Streamlit context)."""
    from i18n import t as _t

    wl = get_wishlist(username)
    st.markdown(
        f'<div style="font-weight:700;font-size:1rem;margin-bottom:8px">'
        f'{_t("wishlist_heading", lang)}</div>',
        unsafe_allow_html=True,
    )
    if not wl:
        st.caption(_t("wishlist_empty", lang))
        return

    for item in wl:
        col1, col2 = st.columns([5, 1])
        with col1:
            rat = item.get("rating", 0)
            st.markdown(
                f"**{item['name']}** "
                f"{'⭐ ' + str(rat) if rat else ''} "
                f"· {item.get('type_label','')}"
                f"{'  · ' + item['city'] if item.get('city') else ''}",
                unsafe_allow_html=False,
            )
        with col2:
            if st.button("💔", key=f"wl_rm_{item['name']}", help="Remove"):
                remove_from_wishlist(username, item["name"])
                st.rerun()
