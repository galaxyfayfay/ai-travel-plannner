"""auth_manager.py — Simple JSON-based auth"""

import hashlib, json, os, time, uuid
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE    = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"


def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def _load(p):
    try: return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception: return {}

def _save(p, d): p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def register_user(username, password, email=""):
    username = username.strip().lower()
    if len(username) < 3: return False, "Username must be ≥3 characters."
    if len(password) < 6: return False, "Password must be ≥6 characters."
    users = _load(USERS_FILE)
    if username in users: return False, "Username already taken."
    users[username] = {
        "username": username, "email": email.strip(),
        "password_hash": _hash(password), "created_at": int(time.time()),
        "points": 0, "checkins": [], "vouchers": [],
        "wishlist": [], "itineraries": [], "points_history": [],
    }
    _save(USERS_FILE, users)
    return True, "Account created!"


def login_user(username, password):
    username = username.strip().lower()
    users = _load(USERS_FILE)
    user = users.get(username)
    if not user: return False, "User not found.", ""
    if user["password_hash"] != _hash(password): return False, "Incorrect password.", ""
    token = str(uuid.uuid4())
    sessions = _load(SESSIONS_FILE)
    sessions[token] = {"username": username, "expires_at": int(time.time()) + 86400*7}
    _save(SESSIONS_FILE, sessions)
    return True, f"Welcome back, {username}!", token


def get_user_from_session(token):
    if not token: return None
    sessions = _load(SESSIONS_FILE)
    s = sessions.get(token)
    if not s or s["expires_at"] < int(time.time()): return None
    return _load(USERS_FILE).get(s["username"])


def logout_user(token):
    sessions = _load(SESSIONS_FILE)
    sessions.pop(token, None)
    _save(SESSIONS_FILE, sessions)


def update_user(username, updates):
    users = _load(USERS_FILE)
    if username in users:
        users[username].update(updates)
        _save(USERS_FILE, users)


def get_user(username):
    return _load(USERS_FILE).get(username.strip().lower())


COLLAB_FILE = DATA_DIR / "collaborations.json"

def create_collab_link(owner, itin_id):
    collabs = _load(COLLAB_FILE)
    token = str(uuid.uuid4())[:8].upper()
    collabs[token] = {"owner": owner, "itin_id": itin_id,
                      "created_at": int(time.time()), "editors": []}
    _save(COLLAB_FILE, collabs)
    return token


def join_collab(username, token):
    collabs = _load(COLLAB_FILE)
    c = collabs.get(token.upper())
    if not c: return False, "Invalid code."
    if username in c["editors"]: return True, "Already a collaborator."
    c["editors"].append(username)
    _save(COLLAB_FILE, collabs)
    return True, f"Joined {c['owner']}'s itinerary!"
