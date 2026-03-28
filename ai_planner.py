"""ai_planner.py — Builds day-by-day itinerary from candidate DataFrame"""

import math
import pandas as pd

try:
    from transport_planner import estimate_travel, dwell_time_minutes, build_day_schedule
    _TP_OK = True
except Exception:
    _TP_OK = False


def _hkm(lat1, lon1, lat2, lon2):
    R = 6371.0
    dl = math.radians(lat2-lat1); dg = math.radians(lon2-lon1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dg/2)**2
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


BASE_SLOTS = ["9:00 AM","10:30 AM","12:00 PM","1:30 PM",
              "3:00 PM","4:30 PM","6:00 PM","7:30 PM","9:00 PM"]


def _simple_schedule(stops, country="INT", city="", daily_usd=60):
    """Fallback scheduler when transport_planner is unavailable."""
    enriched = []
    for i, s in enumerate(stops):
        slot = BASE_SLOTS[i] if i < len(BASE_SLOTS) else "9:00 PM"
        tr = {}
        if i < len(stops) - 1:
            nxt = stops[i+1]
            dist = round(_hkm(s.get("lat",0), s.get("lon",0),
                               nxt.get("lat",0), nxt.get("lon",0)), 2)
            tr = {"mode": "🚇 Transit", "duration": f"{max(5,int(dist*3))} min",
                  "distance_km": dist, "cost_str": f"${round(dist*0.3+0.5,1)}–${round(dist*0.5+1,1)}",
                  "transit_info": "", "color": "#3a8fd4"}
        enriched.append({**s, "time_slot": slot, "dwell_min": 60,
                         "transport_to_next": tr if tr else None})
    return enriched


def generate_itinerary(
    df: pd.DataFrame,
    n_days: int,
    day_quotas: list,
    hotel_lat=None, hotel_lon=None,
    depart_lat=None, depart_lon=None,
    arrive_lat=None, arrive_lon=None,
    day_min_ratings=None,
    day_anchor_lats=None,
    day_anchor_lons=None,
    country="INT",
    city="",
    day_budgets=None,
) -> dict:
    if day_min_ratings is None: day_min_ratings = [3.5]*n_days
    if day_budgets     is None: day_budgets     = [60]*n_days
    if day_anchor_lats is None: day_anchor_lats = [None]*n_days
    if day_anchor_lons is None: day_anchor_lons = [None]*n_days

    used_names: set = set()
    itinerary:  dict = {}
    wdf = df.copy()

    for d in range(n_days):
        quota  = day_quotas[d] if d < len(day_quotas) else day_quotas[-1]
        min_r  = day_min_ratings[d] if d < len(day_min_ratings) else 3.5
        d_usd  = day_budgets[d]     if d < len(day_budgets)     else 60
        a_lat  = day_anchor_lats[d] if day_anchor_lats[d] is not None else (wdf["lat"].mean() if not wdf.empty else 0)
        a_lon  = day_anchor_lons[d] if day_anchor_lons[d] is not None else (wdf["lon"].mean() if not wdf.empty else 0)
        day_key = f"Day {d+1}"
        stops_raw = []

        for type_label, count in quota.items():
            if count <= 0: continue
            pool = wdf[
                (wdf["type_label"] == type_label) &
                (~wdf["name"].isin(used_names)) &
                (wdf["rating"] >= min_r)
            ].copy()
            if not pool.empty and a_lat and a_lon:
                pool["_dist"] = pool.apply(
                    lambda r: _hkm(a_lat, a_lon, r["lat"], r["lon"]), axis=1)
                pool["_score"] = pool["rating"] / (1 + pool["_dist"] / 5)
                pool = pool.sort_values("_score", ascending=False)
            taken = 0
            for _, row in pool.iterrows():
                if taken >= count: break
                stops_raw.append(row.to_dict())
                used_names.add(row["name"]); taken += 1

        if not stops_raw:
            itinerary[day_key] = []; continue

        # Nearest-neighbour ordering
        if d == 0 and depart_lat and depart_lon: slat, slon = depart_lat, depart_lon
        elif hotel_lat and hotel_lon:            slat, slon = hotel_lat, hotel_lon
        else:                                    slat, slon = a_lat, a_lon

        ordered = []; remaining = list(stops_raw); clat, clon = slat, slon
        while remaining:
            remaining.sort(key=lambda r: _hkm(clat, clon, r["lat"], r["lon"]))
            nxt = remaining.pop(0); ordered.append(nxt)
            clat, clon = nxt["lat"], nxt["lon"]

        # Schedule
        if _TP_OK:
            enriched = build_day_schedule(ordered, 9, country, city, d_usd)
        else:
            enriched = _simple_schedule(ordered, country, city, d_usd)

        # End transport
        if enriched:
            end_lat = (arrive_lat if d == n_days-1 and arrive_lat else hotel_lat if hotel_lat else None)
            end_lon = (arrive_lon if d == n_days-1 and arrive_lon else hotel_lon if hotel_lon else None)
            if end_lat and end_lon:
                last = enriched[-1]
                if _TP_OK:
                    et = estimate_travel(last["lat"], last["lon"], end_lat, end_lon,
                                        country=country, city=city, daily_usd=d_usd)
                    enriched[-1]["end_transport"] = {
                        "mode": et["mode_label"], "duration": et["duration_str"],
                        "distance_km": et["distance_km"], "cost_str": et["cost_str"],
                        "to_label": "Arrival Point" if d == n_days-1 else "Hotel",
                    }
                else:
                    dist = round(_hkm(last["lat"], last["lon"], end_lat, end_lon), 2)
                    enriched[-1]["end_transport"] = {
                        "mode": "🚇 Transit",
                        "duration": f"{max(5,int(dist*3))} min",
                        "distance_km": dist, "cost_str": "",
                        "to_label": "Arrival Point" if d == n_days-1 else "Hotel",
                    }

        itinerary[day_key] = enriched
    return itinerary
