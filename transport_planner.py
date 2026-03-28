"""transport_planner.py — Multi-modal transport planning & time estimation"""

import math
from typing import Optional

# ── Transport mode definitions ──────────────────────────────────────────────
TRANSPORT_MODES = {
    "walk":    {"emoji": "🚶", "en": "Walk",          "zh": "步行",    "color": "#3aaa7a"},
    "taxi":    {"emoji": "🚕", "en": "Taxi/Ride-hail","zh": "打车",    "color": "#f39c12"},
    "transit": {"emoji": "🚇", "en": "Public Transit","zh": "公共交通","color": "#3a8fd4"},
    "drive":   {"emoji": "🚗", "en": "Self-drive",    "zh": "自驾",    "color": "#9b59b6"},
    "bike":    {"emoji": "🚲", "en": "Cycling",       "zh": "骑行",    "color": "#1abc9c"},
    "bus":     {"emoji": "🚌", "en": "Bus",           "zh": "公交",    "color": "#e67e22"},
    "ferry":   {"emoji": "⛴️", "en": "Ferry",         "zh": "轮渡",    "color": "#2980b9"},
}

# Speed (km/h) by mode
MODE_SPEED = {
    "walk": 4.5,
    "bike": 14,
    "taxi": 28,
    "transit": 22,
    "drive": 30,
    "bus": 18,
    "ferry": 20,
}

# Cost per km (USD) by mode
MODE_COST_PER_KM = {
    "walk": 0.0,
    "bike": 0.05,
    "taxi": 0.45,
    "transit": 0.10,
    "drive": 0.20,
    "bus": 0.08,
    "ferry": 0.30,
}

# Base fixed cost (USD) by mode
MODE_BASE_COST = {
    "walk": 0.0,
    "bike": 0.5,
    "taxi": 2.5,
    "transit": 0.8,
    "drive": 1.5,
    "bus": 0.6,
    "ferry": 1.5,
}

# City-country specific transit systems
TRANSIT_SYSTEMS = {
    "CN": {
        "beijing":   {"subway": "地铁", "bus": "公交", "bike": "共享单车(美团/滴滴)", "taxi": "滴滴出行"},
        "shanghai":  {"subway": "地铁", "bus": "公交", "bike": "共享单车", "taxi": "滴滴出行"},
        "guangzhou": {"subway": "地铁", "bus": "公交", "bike": "共享单车", "taxi": "滴滴出行"},
        "shenzhen":  {"subway": "地铁", "bus": "公交", "bike": "共享单车", "taxi": "滴滴出行"},
        "chengdu":   {"subway": "地铁", "bus": "公交", "bike": "共享单车", "taxi": "滴滴出行"},
        "hangzhou":  {"subway": "地铁", "bus": "公交", "bike": "共享单车(哈罗)", "taxi": "滴滴出行"},
        "default":   {"subway": "地铁/公交", "bike": "共享单车", "taxi": "滴滴出行"},
    },
    "JP": {
        "tokyo":  {"subway": "Tokyo Metro / Toei", "bus": "都バス", "ic_card": "Suica / Pasmo"},
        "osaka":  {"subway": "Osaka Metro", "bus": "市バス", "ic_card": "ICOCA"},
        "kyoto":  {"subway": "Kyoto Municipal Subway", "bus": "市バス", "ic_card": "ICOCA"},
        "default": {"subway": "Local Subway", "ic_card": "IC Card (Suica/PASMO)"},
    },
    "KR": {
        "seoul":  {"subway": "Seoul Metro", "bus": "Bus", "ic_card": "T-money"},
        "default": {"subway": "Metro", "ic_card": "T-money / Cashbee"},
    },
    "TH": {
        "bangkok": {"subway": "BTS Skytrain / MRT", "bus": "Bus", "tuk_tuk": "Tuk-tuk"},
        "default": {"subway": "Metro", "bus": "Songthaew"},
    },
    "SG": {
        "singapore": {"subway": "MRT", "bus": "SBS/SMRT Bus", "ic_card": "EZ-Link"},
        "default": {"subway": "MRT", "ic_card": "EZ-Link"},
    },
    "GB": {
        "london": {"subway": "London Underground (Tube)", "bus": "TfL Bus", "ic_card": "Oyster Card"},
        "default": {"bus": "Local Bus", "ic_card": "Contactless"},
    },
    "FR": {
        "paris": {"subway": "Métro / RER", "bus": "Bus RATP", "ic_card": "Navigo Pass"},
        "default": {"subway": "Metro", "bus": "Bus"},
    },
    "DE": {
        "berlin":  {"subway": "U-Bahn / S-Bahn", "bus": "BVG Bus", "ic_card": "BVG Ticket"},
        "default": {"subway": "U-Bahn/S-Bahn", "bus": "Bus"},
    },
    "US": {
        "new york": {"subway": "NYC Subway", "bus": "MTA Bus", "ic_card": "MetroCard / OMNY"},
        "default": {"bus": "Local Bus", "taxi": "Uber/Lyft"},
    },
    "AU": {
        "sydney": {"subway": "Sydney Trains", "bus": "Sydney Buses", "ic_card": "Opal Card"},
        "default": {"subway": "Train", "ic_card": "Transit Card"},
    },
    "INT": {
        "default": {"taxi": "Local taxi", "transit": "Public transport"},
    },
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two lat/lon points."""
    R = 6371.0
    dl = math.radians(lat2 - lat1)
    dg = math.radians(lon2 - lon1)
    a = (math.sin(dl / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dg / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def recommend_mode(dist_km: float, country: str = "INT", city: str = "") -> str:
    """Choose the most sensible transport mode for a given distance."""
    if dist_km < 0.6:
        return "walk"
    if dist_km < 2.5:
        if country in ("JP", "KR", "SG", "CN"):
            return "transit"
        return "walk" if dist_km < 1.2 else "transit"
    if dist_km < 8:
        return "transit"
    if dist_km < 20:
        return "taxi"
    return "drive"


def estimate_travel(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    mode: Optional[str] = None,
    country: str = "INT",
    city: str = "",
    daily_usd: int = 60,
) -> dict:
    """
    Estimate travel between two points.
    Returns dict with mode, duration_min, duration_str, distance_km,
    cost_usd_lo, cost_usd_hi, cost_str, transit_info.
    """
    dist_km = round(haversine_km(lat1, lon1, lat2, lon2), 2)
    if mode is None:
        mode = recommend_mode(dist_km, country, city)

    speed = MODE_SPEED.get(mode, 20)
    duration_min = max(2, round((dist_km / speed) * 60))

    # Format duration
    if duration_min < 60:
        dur_str = f"{duration_min} min"
    else:
        h = duration_min // 60
        m = duration_min % 60
        dur_str = f"{h}h {m}m" if m else f"{h}h"

    # Cost estimate
    base = MODE_BASE_COST.get(mode, 1.0)
    per_km = MODE_COST_PER_KM.get(mode, 0.15)
    # Slight scaling by daily budget (luxury travelers tip more, etc.)
    budget_factor = max(0.7, min(2.0, daily_usd / 60))
    if mode in ("walk", "bike"):
        budget_factor = 1.0

    cost_mid = (base + per_km * dist_km) * budget_factor
    cost_lo = round(cost_mid * 0.7, 1)
    cost_hi = round(cost_mid * 1.4, 1)

    # Transit system info
    transit_info = _get_transit_info(mode, country, city)

    # Emoji + label
    md = TRANSPORT_MODES.get(mode, TRANSPORT_MODES["transit"])
    mode_label = f"{md['emoji']} {md['en']}"

    return {
        "mode": mode,
        "mode_label": mode_label,
        "mode_emoji": md["emoji"],
        "duration_min": duration_min,
        "duration_str": dur_str,
        "distance_km": dist_km,
        "cost_usd_lo": cost_lo,
        "cost_usd_hi": cost_hi,
        "cost_str": f"${cost_lo}–${cost_hi}",
        "transit_info": transit_info,
        "color": md["color"],
    }


def estimate_all_modes(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    country: str = "INT",
    city: str = "",
    daily_usd: int = 60,
) -> dict:
    """Estimate travel for all available modes (for comparison UI)."""
    dist_km = haversine_km(lat1, lon1, lat2, lon2)
    results = {}
    candidate_modes = ["walk", "transit", "taxi", "drive"]
    if country in ("CN", "JP", "KR", "NL"):
        candidate_modes.insert(1, "bike")

    for mode in candidate_modes:
        # Skip walk for very long distances
        if mode == "walk" and dist_km > 3.0:
            continue
        results[mode] = estimate_travel(
            lat1, lon1, lat2, lon2,
            mode=mode, country=country, city=city, daily_usd=daily_usd,
        )
    return results


def _get_transit_info(mode: str, country: str, city: str) -> str:
    """Return human-readable transit system name."""
    if mode not in ("transit", "bus"):
        return ""
    city_lc = city.strip().lower()
    country_data = TRANSIT_SYSTEMS.get(country, TRANSIT_SYSTEMS["INT"])

    # Try exact city match
    for key, info in country_data.items():
        if key != "default" and key in city_lc:
            if mode == "transit":
                return info.get("subway", info.get("transit", ""))
            return info.get("bus", "")

    # Fallback to default
    default = country_data.get("default", {})
    if mode == "transit":
        return default.get("subway", default.get("transit", "Local transit"))
    return default.get("bus", "Local bus")


def dwell_time_minutes(type_label: str) -> int:
    """Estimated time to spend at a place (minutes)."""
    DWELL = {
        "🏛️ Attraction": 90,
        "🍜 Restaurant": 75,
        "☕ Café": 45,
        "🌿 Park": 60,
        "🛍️ Shopping": 90,
        "🍺 Bar/Nightlife": 90,
        "🏨 Hotel": 20,
    }
    return DWELL.get(type_label, 60)


def build_day_schedule(
    stops: list,
    start_hour: int = 9,
    country: str = "INT",
    city: str = "",
    daily_usd: int = 60,
) -> list:
    """
    Given ordered stops (each with lat, lon, type_label),
    assign time slots and compute travel legs.
    Returns enriched stop list.
    """
    enriched = []
    current_min = start_hour * 60  # minutes since midnight

    for i, stop in enumerate(stops):
        lat = stop.get("lat", 0)
        lon = stop.get("lon", 0)
        tl = stop.get("type_label", "")

        # Format arrival time
        h = current_min // 60
        m = current_min % 60
        slot = f"{h}:{m:02d} {'AM' if h < 12 else 'PM'}" if h <= 12 else f"{h-12}:{m:02d} PM"
        if h == 12:
            slot = f"12:{m:02d} PM"

        dwell = dwell_time_minutes(tl)

        # Travel to next stop
        transport_info = {}
        if i < len(stops) - 1:
            nxt = stops[i + 1]
            nlat, nlon = nxt.get("lat", lat), nxt.get("lon", lon)
            tr = estimate_travel(
                lat, lon, nlat, nlon,
                country=country, city=city, daily_usd=daily_usd,
            )
            transport_info = {
                "mode": tr["mode_label"],
                "duration": tr["duration_str"],
                "distance_km": tr["distance_km"],
                "cost_str": tr["cost_str"],
                "transit_info": tr["transit_info"],
                "color": tr["color"],
            }
            current_min += dwell + tr["duration_min"]
        else:
            current_min += dwell

        enriched.append({
            **stop,
            "time_slot": slot,
            "dwell_min": dwell,
            "transport_to_next": transport_info if transport_info else None,
        })

    return enriched


def render_transport_comparison(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    from_name: str,
    to_name: str,
    country: str = "INT",
    city: str = "",
    daily_usd: int = 60,
    lang: str = "EN",
) -> str:
    """Build HTML card showing transport options side-by-side."""
    modes = estimate_all_modes(lat1, lon1, lat2, lon2, country, city, daily_usd)
    dist_km = haversine_km(lat1, lon1, lat2, lon2)

    rows = ""
    for mode_key, tr in modes.items():
        md = TRANSPORT_MODES.get(mode_key, {})
        label = md.get("zh" if lang == "ZH" else "en", mode_key)
        ti = tr.get("transit_info", "")
        ti_html = f"<br><small style='color:#888'>{ti}</small>" if ti else ""
        rows += (
            f"<tr>"
            f"<td style='padding:4px 8px'>{md.get('emoji','')} {label}{ti_html}</td>"
            f"<td style='padding:4px 8px;text-align:center'>{tr['duration_str']}</td>"
            f"<td style='padding:4px 8px;text-align:center'>{tr['cost_str']}</td>"
            f"</tr>"
        )

    return (
        f"<div style='background:#f8f6f0;border-radius:10px;padding:12px;margin:8px 0'>"
        f"<div style='font-size:0.85rem;color:#888;margin-bottom:6px'>"
        f"📍 {from_name[:25]} → {to_name[:25]} · {dist_km:.1f} km</div>"
        f"<table style='width:100%;font-size:0.82rem;border-collapse:collapse'>"
        f"<thead><tr style='color:#666'>"
        f"<th style='text-align:left;padding:2px 8px'>Mode</th>"
        f"<th style='padding:2px 8px'>Time</th>"
        f"<th style='padding:2px 8px'>Cost</th>"
        f"</tr></thead><tbody>{rows}</tbody></table></div>"
    )
