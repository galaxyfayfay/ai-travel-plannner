"""ai_planner.py v8 — strict 8 km clustering, per-day type quota, district anchors"""
import math

TIME_SLOTS = [
    "9:00 AM","10:30 AM","12:00 PM","1:30 PM",
    "3:00 PM","4:30 PM","6:00 PM","7:30 PM","9:00 PM",
]
MAX_KM = 8.0


def hav(lat1, lon1, lat2, lon2):
    R = 6371
    dl = math.radians(lat2 - lat1)
    dg = math.radians(lon2 - lon1)
    a = (math.sin(dl / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dg / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(min(1.0, a)))


def transport(dist_km):
    if dist_km < 0.5:
        return {"mode": "🚶 Walking",      "duration": f"~{max(5,  int(dist_km*1000/75))} min", "desc": "Easy walk"}
    elif dist_km < 2.0:
        return {"mode": "🚲 Bike",         "duration": f"~{max(5,  int(dist_km/0.22))} min",   "desc": "Short bike ride"}
    elif dist_km < 5.0:
        return {"mode": "🚌 Bus/Metro",    "duration": f"~{max(8,  int(dist_km/0.33))} min",   "desc": "Hop on local transit"}
    elif dist_km < 15.0:
        return {"mode": "🚇 Metro/Taxi",   "duration": f"~{max(12, int(dist_km/0.42))} min",   "desc": "Metro or taxi"}
    else:
        return {"mode": "🚕 Taxi",         "duration": f"~{max(20, int(dist_km/0.50))} min",   "desc": "Ride-hailing recommended"}


def dist_matrix(pts):
    n = len(pts)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = hav(pts[i]["lat"], pts[i]["lon"], pts[j]["lat"], pts[j]["lon"])
            D[i][j] = D[j][i] = d
    return D


def greedy_route(indices, D, start=None):
    if not indices:
        return []
    rem = list(indices)
    if start is not None and start in rem:
        cur = start; rem.remove(cur)
    else:
        cur = rem.pop(0)
    route = [cur]
    while rem:
        nxt = min(rem, key=lambda j: D[cur][j])
        route.append(nxt); rem.remove(nxt); cur = nxt
    return route


def two_opt(route, D):
    if len(route) < 4:
        return route
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                a, b = best[i - 1], best[i]
                c, d_ = best[j], best[(j + 1) % len(best)]
                if D[a][b] + D[c][d_] > D[a][c] + D[b][d_] + 1e-9:
                    best[i:j + 1] = best[i:j + 1][::-1]
                    improved = True
    return best


def cluster_days(pts, days, day_quotas, D,
                 hotel_lat=None, hotel_lon=None,
                 depart_lat=None, depart_lon=None,
                 day_min_ratings=None,
                 day_anchor_lats=None, day_anchor_lons=None):
    """
    Strict ≤8 km same-day clustering with per-day type quota.
    Priority for day anchor: day_anchor (district centroid) > depart (day 0) > hotel > centroid
    """
    groups = {}
    for i, p in enumerate(pts):
        t = p.get("type_label", "other")
        groups.setdefault(t, []).append(i)
    for t in groups:
        groups[t].sort(key=lambda i: pts[i].get("rating", 0), reverse=True)

    assigned = set()
    day_groups = []

    for day_idx in range(days):
        quota = day_quotas[day_idx] if day_idx < len(day_quotas) else {}
        if not quota:
            day_groups.append([])
            continue

        min_rating = (day_min_ratings[day_idx]
                      if day_min_ratings and day_idx < len(day_min_ratings)
                      else 0.0)

        def ok_rating(i):
            return pts[i].get("rating", 0) >= min_rating

        # Resolve anchor for this day
        if day_anchor_lats and day_idx < len(day_anchor_lats) and day_anchor_lats[day_idx] is not None:
            anchor = (day_anchor_lats[day_idx], day_anchor_lons[day_idx])
        elif day_idx == 0 and depart_lat is not None:
            anchor = (depart_lat, depart_lon)
        elif hotel_lat is not None:
            anchor = (hotel_lat, hotel_lon)
        elif day_groups and day_groups[-1]:
            last = day_groups[-1][-1]
            anchor = (pts[last]["lat"], pts[last]["lon"])
        else:
            cands = [i for tl in quota for i in groups.get(tl, []) if i not in assigned]
            if cands:
                anchor = (sum(pts[i]["lat"] for i in cands) / len(cands),
                          sum(pts[i]["lon"] for i in cands) / len(cands))
            else:
                anchor = None

        group = []
        type_done = {}

        # Seed: one per type, nearest anchor, prefer rating threshold
        seeds = []
        for tl, cnt in quota.items():
            pool = [i for i in groups.get(tl, []) if i not in assigned]
            rated = [i for i in pool if ok_rating(i)]
            p2 = rated if rated else pool
            if not p2:
                continue
            if anchor:
                p2.sort(key=lambda i: hav(pts[i]["lat"], pts[i]["lon"], anchor[0], anchor[1]))
            seeds.append((tl, p2[0]))

        if not seeds:
            day_groups.append([])
            continue

        if anchor:
            seeds.sort(key=lambda x: hav(pts[x[1]]["lat"], pts[x[1]]["lon"], anchor[0], anchor[1]))
        first_tl, first_seed = seeds[0]
        assigned.add(first_seed)
        group.append(first_seed)
        type_done[first_tl] = 1

        # Greedy fill respecting 8 km constraint and quota
        for _ in range(sum(quota.values()) * 5):
            if all(type_done.get(tl, 0) >= cnt for tl, cnt in quota.items()):
                break
            best_i, best_d = None, float("inf")
            for tl, cnt in quota.items():
                if type_done.get(tl, 0) >= cnt:
                    continue
                pool = [i for i in groups.get(tl, []) if i not in assigned]
                rated = [i for i in pool if ok_rating(i)]
                for req in [True, False]:
                    cands = rated if req else pool
                    for ci in cands:
                        d = min(D[g][ci] for g in group) if group else 0.0
                        if d <= MAX_KM and d < best_d:
                            best_d = d
                            best_i = ci
                    if best_i is not None:
                        break
            if best_i is None:
                break
            assigned.add(best_i)
            group.append(best_i)
            tl = pts[best_i].get("type_label", "other")
            type_done[tl] = type_done.get(tl, 0) + 1

        day_groups.append(group)

    return day_groups


def generate_itinerary(df, days, day_quotas,
                       hotel_lat=None, hotel_lon=None,
                       depart_lat=None, depart_lon=None,
                       arrive_lat=None, arrive_lon=None,
                       day_min_ratings=None,
                       day_anchor_lats=None, day_anchor_lons=None):
    if df.empty:
        return {}
    try:
        pts = df.to_dict("records")
        D = dist_matrix(pts)
        day_groups = cluster_days(
            pts, days, day_quotas, D,
            hotel_lat, hotel_lon, depart_lat, depart_lon,
            day_min_ratings, day_anchor_lats, day_anchor_lons,
        )
        itinerary = {}
        for day_idx, group in enumerate(day_groups):
            lbl = f"Day {day_idx + 1}"
            if not group:
                itinerary[lbl] = []
                continue

            # Choose route start
            if day_anchor_lats and day_idx < len(day_anchor_lats) and day_anchor_lats[day_idx] is not None:
                alat, alon = day_anchor_lats[day_idx], day_anchor_lons[day_idx]
                start = min(group, key=lambda i: hav(pts[i]["lat"], pts[i]["lon"], alat, alon))
            elif day_idx == 0 and depart_lat is not None:
                start = min(group, key=lambda i: hav(pts[i]["lat"], pts[i]["lon"], depart_lat, depart_lon))
            elif hotel_lat is not None:
                start = min(group, key=lambda i: hav(pts[i]["lat"], pts[i]["lon"], hotel_lat, hotel_lon))
            else:
                start = max(group, key=lambda i: pts[i].get("rating", 0))

            route = greedy_route(group, D, start)
            if len(route) > 3:
                route = two_opt(route, D)

            stops = []
            for si, gi in enumerate(route):
                p = pts[gi]
                tr = None
                if si < len(route) - 1:
                    dist = D[gi][route[si + 1]]
                    tr = {**transport(dist), "distance_km": round(dist, 2)}
                end_tr = None
                if si == len(route) - 1 and arrive_lat is not None and day_idx == days - 1:
                    d2 = hav(p["lat"], p["lon"], arrive_lat, arrive_lon)
                    end_tr = {**transport(d2), "distance_km": round(d2, 2), "to_label": "🏁 Departure Point"}
                stops.append({
                    "name":        p.get("name", ""),
                    "rating":      p.get("rating", 0.0),
                    "address":     p.get("address", ""),
                    "phone":       p.get("phone", ""),
                    "website":     p.get("website", ""),
                    "lat":         p.get("lat", 0),
                    "lon":         p.get("lon", 0),
                    "district":    p.get("district", ""),
                    "description": p.get("description", ""),
                    "type":        p.get("type", ""),
                    "type_label":  p.get("type_label", ""),
                    "time_slot":   TIME_SLOTS[si % len(TIME_SLOTS)],
                    "transport_to_next": tr,
                    "end_transport":     end_tr,
                })
            itinerary[lbl] = stops

        for e in range(len(day_groups), days):
            itinerary[f"Day {e + 1}"] = []
        return itinerary
    except Exception:
        return {}