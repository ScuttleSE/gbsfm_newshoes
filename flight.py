#!/usr/bin/env python3
"""
Usage:
    python flight.py BA112
    python flight.py --discord BA112
    python flight.py          # will prompt
"""

import argparse
import math
import re
import sys
from FlightRadar24 import FlightRadar24API


# ── Helpers ──────────────────────────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def fmt_time(hours):
    h = int(hours)
    m = round((hours - h) * 60)
    if m == 60:
        h, m = h + 1, 0
    return f"{h}h {m:02d}m"


def fmt_dist(km):
    return f"{km:,.0f} km  ({km * 0.539957:,.0f} nm)"


# ── Main ─────────────────────────────────────────────────────────────────────

def get_flight_info(flight_number: str, discord: bool = False):
    flight_number = flight_number.upper().replace(" ", "")

    # Airline IATA code = leading letters (e.g. "BA" from "BA112")
    m = re.match(r'^([A-Z]+)', flight_number)
    airline_iata = m.group(1) if m else ""
    if not airline_iata:
        sys.exit("Cannot determine airline from flight number.")

    api = FlightRadar24API()
    if not discord:
        print(f"Searching for {flight_number} …")

    flights = api.get_flights(airline=airline_iata)

    # Match on flight number OR callsign
    matches = [
        f for f in flights
        if (f.number   or "").upper() == flight_number
        or (f.callsign or "").upper() == flight_number
    ]

    if not matches:
        sys.exit(f"No active flight found for {flight_number}.")

    if len(matches) > 1 and not discord:
        print(f"  ⚠  {len(matches)} flights matched — using the first one.")

    flight = matches[0]

    # Fetch full details
    details = api.get_flight_details(flight)
    flight.set_flight_details(details)

    if flight.on_ground:
        sys.exit(f"{flight_number} is currently on the ground.")

    curr_lat, curr_lon = flight.latitude, flight.longitude
    speed_kts = flight.ground_speed or 0
    speed_kmh = speed_kts * 1.852

    # Airport lat/lon lives in the raw details dict
    try:
        orig = details["airport"]["origin"]
        dest = details["airport"]["destination"]
        orig_lat  = orig["position"]["latitude"]
        orig_lon  = orig["position"]["longitude"]
        orig_name = orig["name"]
        dest_lat  = dest["position"]["latitude"]
        dest_lon  = dest["position"]["longitude"]
        dest_name = dest["name"]
    except (KeyError, TypeError):
        sys.exit("Airport position data unavailable in API response.")

    # Distances
    d_from = haversine_km(orig_lat, orig_lon, curr_lat, curr_lon)
    d_to   = haversine_km(curr_lat, curr_lon, dest_lat, dest_lon)

    # Times (based on current ground speed — rough estimate)
    t_from = fmt_time(d_from / speed_kmh) if speed_kmh else "—"
    t_to   = fmt_time(d_to   / speed_kmh) if speed_kmh else "—"

    # ── Output ───────────────────────────────────────────────────────────────
    if discord:
        lines = [
            f"**✈ {flight_number}**  {flight.aircraft_code or ''}  {flight.registration or ''}",
            f"> **Altitude:** {flight.altitude:,} ft  |  **Speed:** {speed_kmh:.0f} km/h ({speed_kts:.0f} kts)",
            f"> 🛫 **From:** {orig_name} ({flight.origin_airport_iata}) — {fmt_dist(d_from)} ago ({t_from} at current speed)",
            f"> 🛬 **To:** {dest_name} ({flight.destination_airport_iata}) — {fmt_dist(d_to)} remaining (ETA in {t_to})",
        ]
        print("\n".join(lines))
    else:
        sep = "─" * 50
        print(f"\n{sep}")
        print(f"  ✈  {flight_number}   {flight.aircraft_code or ''}   {flight.registration or ''}")
        print(sep)
        print(f"  Altitude : {flight.altitude:,} ft")
        print(f"  Speed    : {speed_kmh:.0f} km/h  ({speed_kts:.0f} kts)")
        print()
        print(f"  🛫  From — {orig_name} ({flight.origin_airport_iata})")
        print(f"      Distance : {fmt_dist(d_from)}")
        print(f"      Time ago : {t_from}  (at current speed)")
        print()
        print(f"  🛬  To   — {dest_name} ({flight.destination_airport_iata})")
        print(f"      Distance : {fmt_dist(d_to)}")
        print(f"      ETA in   : {t_to}  (at current speed)")
        print(f"{sep}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("flight_number", nargs="?")
    parser.add_argument("--discord", action="store_true", help="Output formatted for Discord")
    args = parser.parse_args()

    fn = args.flight_number or input("Flight number: ").strip()
    get_flight_info(fn, discord=args.discord)
