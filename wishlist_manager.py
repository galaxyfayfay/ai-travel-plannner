"""wishlist_manager.py — Wishlist, saved itineraries, place swap"""

import json
import time
import copy
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def _load():
    p = DATA_DIR / "users.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


def _save(d):
    p = DATA_DIR / "users.json"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def add_to_wishlist(username, place):
    users = _load()
    u = users.get(username.strip().lower())
    if not u:
        return False
    wl = u.setdefault("wishlist", [])
    if any(w.get("name") == place.get("name") for w in wl):
        return False
    wl.append({
        "name":       place.get("name", ""),
        "lat":        place.get("lat"),
        "lon":        place.get("lon"),
        "type_label": place.get("type_label", ""),
        "rating":     place.get("rating", 0),
        "address":    place.get("address", ""),
        "city":       place.get("_city", ""),
        "added_at":   int(time.time()),
    })
    _save(users)
    return True


def remove_from_wishlist(username, place_name):
    users = _load()
    u = users.get(username.strip().lower())
    if not u:
        return
    u["wishlist"] = [w for w in u.get("wishlist", []) if w.get("name") != place_name]
    _save(users)


def get_wishlist(username):
    return _load().get(username.strip().lower(), {}).get("wishlist", [])


def is_in_wishlist(username, place_name):
    return any(w.get("name") == place_name for w in get_wishlist(username))


def save_itinerary(username, itinerary, city, label=""):
    users = _load()
    u = users.get(username.strip().lower())
    if not u:
        return
    itins = u.setdefault("itineraries", [])
    if len(itins) >= 20:
        itins = itins[-19:]
    itins.append({
        "label":    label or city,
        "city":     city,
        "saved_at": int(time.time()),
        "days":     len(itinerary),
        "stops":    sum(len(v) for v in itinerary.values()),
        "data":     itinerary,
    })
    u["itineraries"] = itins
    _save(users)


def get_saved_itineraries(username):
    return list(reversed(_load().get(username.strip().lower(), {}).get("itineraries", [])))


def swap_place_in_itinerary(itinerary, day_label, stop_idx, new_place):
    result = copy.deepcopy(itinerary)
    if day_label in result and 0 <= stop_idx < len(result[day_label]):
        old = result[day_label][stop_idx]
        np2 = dict(new_place)
        np2["time_slot"] = old.get("time_slot", "")
        np2["dwell_min"] = old.get("dwell_min", 60)
        result[day_label][stop_idx] = np2
    return result


def render_wishlist_panel(username, lang="EN"):
    """Render wishlist UI — NO i18n import, uses inline strings."""
    import streamlit as st

    LABELS = {
        "EN": {"empty": "Your wishlist is empty. Add places you'd like to visit!",
               "remove": "💔 Remove"},
        "ZH": {"empty": "心愿单是空的，快添加你想去的地方吧！",
               "remove": "💔 移除"},
    }
    lb = LABELS.get(lang, LABELS["EN"])

    wl = get_wishlist(username)
    if not wl:
        st.caption(lb["empty"])
        return

    for item in wl:
        c1, c2 = st.columns([5, 1])
        with c1:
            rat = item.get("rating", 0)
            city_str = f" · {item['city']}" if item.get("city") else ""
            st.markdown(
                f"**{item['name']}** "
                f"{'⭐ ' + str(rat) if rat else ''} "
                f"· {item.get('type_label', '')}"
                f"{city_str}"
            )
        with c2:
            if st.button(lb["remove"], key=f"wl_rm_{item['name'][:15]}",
                         help="Remove from wishlist"):
                remove_from_wishlist(username, item["name"])
                st.rerun()
