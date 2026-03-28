"""transport_planner.py — Multi-modal transport planning"""

import math
from typing import Optional

TRANSPORT_MODES = {
    "walk":    {"emoji": "🚶", "en": "Walk",           "zh": "步行",    "color": "#3aaa7a"},
    "taxi":    {"emoji": "🚕", "en": "Taxi/Ride-hail", "zh": "打车",    "color": "#f39c12"},
    "transit": {"emoji": "🚇", "en": "Public Transit", "zh": "公共交通", "color": "#3a8fd4"},
    "drive":   {"emoji": "🚗", "en": "Self-drive",     "zh": "自驾",    "color": "#9b59b6"},
    "bike":    {"emoji": "🚲", "en": "Cycling",        "zh": "骑行",    "color": "#1abc9c"},
}

MODE_SPEED    = {"walk": 4.5, "bike": 14, "taxi": 28, "transit": 22, "drive": 30}
MODE_CPK      = {"walk": 0.0, "bike": 0.05, "taxi": 0.45, "transit": 0.10, "drive": 0.20}
MODE_BASE     = {"walk": 0.0, "bike": 0.5,  "taxi": 2.5,  "transit": 0.8,  "drive": 1.5}

TRANSIT_INFO = {
    "CN": {"beijing":"地铁/公交","shanghai":"地铁/公交","guangzhou":"地铁/公交",
           "shenzhen":"地铁/公交","default":"地铁/公交"},
    "JP": {"tokyo":"Tokyo Metro / Suica","osaka":"Osaka Metro / ICOCA",
           "kyoto":"Kyoto Subway / ICOCA","default":"Local Subway"},
    "KR": {"seoul":"Seoul Metro / T-money","default":"Metro / T-money"},
    "TH": {"bangkok":"BTS Skytrain / MRT","default":"Local bus"},
    "SG": {"singapore":"MRT / EZ-Link","default":"MRT"},
    "GB": {"london":"Underground / Oyster","default":"Local bus"},
    "FR": {"paris":"Métro / Navigo","default":"Metro"},
    "US": {"new york":"NYC Subway / MetroCard","default":"Local bus / Uber"},
    "AU": {"sydney":"Sydney Trains / Opal","default":"Train / Transit Card"},
    "INT":{"default":"Local transit"},
}

DWELL_MIN = {
    "🏛️ Attraction": 90, "🍜 Restaurant": 75, "☕ Café": 45,
    "🌿 Park": 60, "🛍️ Shopping": 90, "🍺 Bar/Nightlife": 90, "🏨 Hotel": 20,
}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dl = math.radians(lat2 - lat1)
    dg = math.radians(lon2 - lon1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dg/2)**2
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def recommend_mode(dist_km, country="INT"):
    if dist_km < 0.7:
        return "walk"
    if dist_km < 8:
        return "transit"
    if dist_km < 20:
        return "taxi"
    return "drive"


def estimate_travel(lat1, lon1, lat2, lon2, mode=None, country="INT", city="", daily_usd=60):
    dist_km = round(haversine_km(lat1, lon1, lat2, lon2), 2)
    if mode is None:
        mode = recommend_mode(dist_km, country)
    speed = MODE_SPEED.get(mode, 20)
    dur_min = max(2, round((dist_km / speed) * 60))
    dur_str = f"{dur_min} min" if dur_min < 60 else f"{dur_min//60}h {dur_min%60}m"

    bf = max(0.7, min(2.0, daily_usd / 60)) if mode not in ("walk","bike") else 1.0
    cost_mid = (MODE_BASE.get(mode,1.0) + MODE_CPK.get(mode,0.15) * dist_km) * bf
    lo_u = round(cost_mid * 0.7, 1)
    hi_u = round(cost_mid * 1.4, 1)

    city_lc = city.strip().lower()
    cd = TRANSIT_INFO.get(country, TRANSIT_INFO["INT"])
    ti = next((v for k, v in cd.items() if k != "default" and k in city_lc), cd.get("default",""))

    md = TRANSPORT_MODES.get(mode, TRANSPORT_MODES["transit"])
    return {
        "mode": mode,
        "mode_label": f"{md['emoji']} {md['en']}",
        "mode_emoji": md["emoji"],
        "duration_min": dur_min,
        "duration_str": dur_str,
        "distance_km": dist_km,
        "cost_usd_lo": lo_u,
        "cost_usd_hi": hi_u,
        "cost_str": f"${lo_u}–${hi_u}",
        "transit_info": ti,
        "color": md["color"],
    }


def estimate_all_modes(lat1, lon1, lat2, lon2, country="INT", city="", daily_usd=60):
    dist_km = haversine_km(lat1, lon1, lat2, lon2)
    modes = ["walk", "transit", "taxi", "drive"]
    if country in ("CN","JP","KR","NL"): modes.insert(1, "bike")
    return {
        m: estimate_travel(lat1, lon1, lat2, lon2, m, country, city, daily_usd)
        for m in modes
        if not (m == "walk" and dist_km > 3.0)
    }


def render_transport_comparison(lat1, lon1, lat2, lon2, from_name, to_name,
                                 country="INT", city="", daily_usd=60, lang="EN"):
    modes = estimate_all_modes(lat1, lon1, lat2, lon2, country, city, daily_usd)
    dist_km = haversine_km(lat1, lon1, lat2, lon2)
    rows = ""
    for mk, tr in modes.items():
        md = TRANSPORT_MODES.get(mk, {})
        label = md.get("zh" if lang == "ZH" else "en", mk)
        ti = tr.get("transit_info","")
        ti_h = f"<br><small style='color:#888'>{ti}</small>" if ti else ""
        rows += (f"<tr><td style='padding:4px 8px'>{md.get('emoji','')} {label}{ti_h}</td>"
                 f"<td style='padding:4px 8px;text-align:center'>{tr['duration_str']}</td>"
                 f"<td style='padding:4px 8px;text-align:center'>{tr['cost_str']}</td></tr>")
    return (f"<div style='background:#f8f6f0;border-radius:10px;padding:12px;margin:8px 0'>"
            f"<div style='font-size:.85rem;color:#888;margin-bottom:6px'>"
            f"📍 {from_name[:25]} → {to_name[:25]} · {dist_km:.1f} km</div>"
            f"<table style='width:100%;font-size:.82rem;border-collapse:collapse'>"
            f"<thead><tr style='color:#666'><th style='text-align:left;padding:2px 8px'>Mode</th>"
            f"<th style='padding:2px 8px'>Time</th><th style='padding:2px 8px'>Cost</th>"
            f"</tr></thead><tbody>{rows}</tbody></table></div>")


def dwell_time_minutes(type_label):
    return DWELL_MIN.get(type_label, 60)


def build_day_schedule(stops, start_hour=9, country="INT", city="", daily_usd=60):
    enriched = []
    cur_min = start_hour * 60
    for i, stop in enumerate(stops):
        lat, lon = stop.get("lat", 0), stop.get("lon", 0)
        tl = stop.get("type_label", "")
        h, m = cur_min // 60, cur_min % 60
        if h < 12:   slot = f"{h}:{m:02d} AM"
        elif h == 12: slot = f"12:{m:02d} PM"
        else:         slot = f"{h-12}:{m:02d} PM"
        dwell = dwell_time_minutes(tl)
        transport_info = {}
        if i < len(stops) - 1:
            nxt = stops[i + 1]
            tr = estimate_travel(lat, lon, nxt.get("lat", lat), nxt.get("lon", lon),
                                 country=country, city=city, daily_usd=daily_usd)
            transport_info = {
                "mode": tr["mode_label"],
                "duration": tr["duration_str"],
                "distance_km": tr["distance_km"],
                "cost_str": tr["cost_str"],
                "transit_info": tr["transit_info"],
                "color": tr["color"],
            }
            cur_min += dwell + tr["duration_min"]
        else:
            cur_min += dwell
        enriched.append({
            **stop,
            "time_slot": slot,
            "dwell_min": dwell,
            "transport_to_next": transport_info if transport_info else None,
        })
    return enriched
