cat << 'EOF' > transport.py
TRANSPORT_SPEED = {
    "walk": 4.5,
    "taxi": 35,
    "drive": 45,
    "transit": 22,
}

def travel_minutes(dist_km: float, mode: str = "walk") -> int:
    speed = TRANSPORT_SPEED.get(mode, 4.5)
    return max(3, int(dist_km / speed * 60))
EOF
