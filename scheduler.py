cat << 'EOF' > scheduler.py
STAY_MINUTES = {
    "🏛️ Attraction": 90,
    "🍜 Restaurant": 75,
    "☕ Café": 40,
    "🌿 Park": 45,
    "🛍️ Shopping": 60,
    "🍺 Bar/Nightlife": 90,
}

def build_day_schedule(stops, start_min=9*60, end_min=21*60):
    t = start_min
    output = []
    for s in stops:
        stay = STAY_MINUTES.get(s.get("type_label"), 60)
        if t + stay > end_min:
            break
        s["start_min"] = t
        s["end_min"] = t + stay
        output.append(s)
        t += stay
    return output
EOF
