"""ai_planner.py — Builds a day-by-day itinerary from a candidate DataFrame."""

import math
import random
import pandas as pd
from transport_planner import estimate_travel, dwell_time_minutes, build_day_schedule

# ── Time slot bank ───────────────────────────────────────────────────────────
BASE_SLOTS = [
    "9:00 AM", "10:30 AM", "12:00 PM",
    "1:30 PM", "3:00 PM", "4:30 PM",
    "6:00 PM", "7:30 PM", "9:00 PM",
]


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dl = math.radians(lat2 - lat1)
    dg = math.radians(lon2 - lon1)
    a = (math.sin(dl / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dg / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def _anchor(row_pool: pd.DataFrame, lat: float, lon: float, radius_km: float) -> pd.DataFrame:
    """Filter pool to rows within radius_km of (lat, lon)."""
    dists = row_pool.apply(
        lambda r: _haversine_km(lat, lon, r["lat"], r["lon"]), axis=1
    )
    return row_pool[dists <= radius_km].copy()


def generate_itinerary(
    df: pd.DataFrame,
    n_days: int,
    day_quotas: list[dict],
    hotel_lat: float = None,
    hotel_lon: float = None,
    depart_lat: float = None,
    depart_lon: float = None,
    arrive_lat: float = None,
    arrive_lon: float = None,
    day_min_ratings: list[float] = None,
    day_anchor_lats: list[float] = None,
    day_anchor_lons: list[float] = None,
    country: str = "INT",
    city: str = "",
    day_budgets: list[int] = None,
) -> dict:
    """
    Build an ordered itinerary dict: {"Day 1": [stop, ...], "Day 2": [...], ...}
    Each stop is a dict with name, lat, lon, type_label, time_slot,
    transport_to_next (optional), end_transport (optional).
    """
    if day_min_ratings is None:
        day_min_ratings = [3.5] * n_days
    if day_budgets is None:
        day_budgets = [60] * n_days
    if day_anchor_lats is None:
        day_anchor_lats = [None] * n_days
    if day_anchor_lons is None:
        day_anchor_lons = [None] * n_days

    used_names: set = set()
    itinerary: dict = {}
    working_df = df.copy()

    for d in range(n_days):
        quota = day_quotas[d] if d < len(day_quotas) else day_quotas[-1]
        min_r = day_min_ratings[d] if d < len(day_min_ratings) else 3.5
        d_usd = day_budgets[d] if d < len(day_budgets) else 60
        a_lat = day_anchor_lats[d] if day_anchor_lats[d] is not None else (
            working_df["lat"].mean() if not working_df.empty else 0
        )
        a_lon = day_anchor_lons[d] if day_anchor_lons[d] is not None else (
            working_df["lon"].mean() if not working_df.empty else 0
        )

        day_key = f"Day {d + 1}"
        stops_raw: list[dict] = []

        for type_label, count in quota.items():
            if count <= 0:
                continue
            pool = working_df[
                (working_df["type_label"] == type_label) &
                (~working_df["name"].isin(used_names)) &
                (working_df["rating"] >= min_r)
            ].copy()

            # Prefer places near today's anchor
            if not pool.empty and a_lat and a_lon:
                pool["_dist"] = pool.apply(
                    lambda r: _haversine_km(a_lat, a_lon, r["lat"], r["lon"]), axis=1
                )
                # Score = rating / (1 + dist) → balances quality & proximity
                pool["_score"] = pool["rating"] / (1 + pool["_dist"] / 5)
                pool = pool.sort_values("_score", ascending=False)

            taken = 0
            for _, row in pool.iterrows():
                if taken >= count:
                    break
                stops_raw.append(row.to_dict())
                used_names.add(row["name"])
                taken += 1

        if not stops_raw:
            itinerary[day_key] = []
            continue

        # ── Greedy nearest-neighbour ordering ─────────────────────────
        # Start from anchor / depart point / hotel
        if d == 0 and depart_lat and depart_lon:
            start_lat, start_lon = depart_lat, depart_lon
        elif hotel_lat and hotel_lon:
            start_lat, start_lon = hotel_lat, hotel_lon
        else:
            start_lat, start_lon = a_lat, a_lon

        ordered: list[dict] = []
        remaining = list(stops_raw)
        cur_lat, cur_lon = start_lat, start_lon

        while remaining:
            remaining.sort(
                key=lambda r: _haversine_km(cur_lat, cur_lon, r["lat"], r["lon"])
            )
            nxt = remaining.pop(0)
            ordered.append(nxt)
            cur_lat, cur_lon = nxt["lat"], nxt["lon"]

        # ── Assign time slots & compute transport legs ─────────────────
        enriched = build_day_schedule(
            stops=ordered,
            start_hour=9,
            country=country,
            city=city,
            daily_usd=d_usd,
        )

        # ── Last stop: add end transport to arrive/hotel ───────────────
        if enriched:
            last = enriched[-1]
            end_lat = (arrive_lat if d == n_days - 1 and arrive_lat else
                       hotel_lat if hotel_lat else None)
            end_lon = (arrive_lon if d == n_days - 1 and arrive_lon else
                       hotel_lon if hotel_lon else None)
            if end_lat and end_lon:
                et = estimate_travel(
                    last["lat"], last["lon"],
                    end_lat, end_lon,
                    country=country, city=city, daily_usd=d_usd,
                )
                label = "Arrival Point" if d == n_days - 1 else "Hotel"
                enriched[-1]["end_transport"] = {
                    "mode": et["mode_label"],
                    "duration": et["duration_str"],
                    "distance_km": et["distance_km"],
                    "cost_str": et["cost_str"],
                    "to_label": label,
                }

        itinerary[day_key] = enriched

    return itinerary
