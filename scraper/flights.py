"""
scraper/flights.py
------------------
Core Google Flights scraper using fast-flights get_flights().

Public API
----------
    scrape(departure, destination, date, trip, seat, adults, use_cache) -> list[dict]

Each dict contains:
    airline, price, price_str, departure_str, arrival_str,
    duration, duration_min, stops, stops_raw,
    from_code, to_code, travel_date, plane, carbon_g
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from config.settings import CACHE_DIR, SCRAPER_MAX_RETRIES
from scraper.iata import city_to_iata
from scraper.date_parser import parse_date

try:
    from fast_flights import FlightQuery, Passengers, create_query, get_flights
except ImportError as exc:
    raise ImportError(
        "fast-flights is not installed.\n"
        "Run: pip install 'fast-flights @ git+https://github.com/AWeirdDev/flights.git@dev'"
    ) from exc


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
_TRIP_MAP: dict[str, str] = {
    "one way":    "one-way",
    "one-way":    "one-way",
    "oneway":     "one-way",
    "round trip": "round-trip",
    "round-trip": "round-trip",
    "return":     "round-trip",
    "multi city": "multi-city",
    "multi-city": "multi-city",
}


def _fmt_dt(dt) -> str:
    """
    Safely convert a fast-flights SimpleDatetime object to a readable string.

    Google sometimes omits date or minute fields — return 'N/A' instead of
    crashing or showing '0000-00-00'.
    """
    try:
        d = dt.date   # (year, month, day)
        t = dt.time   # (hour,) or (hour, minute)

        if not d or len(d) < 3 or (d[0] == 0 and d[1] == 0 and d[2] == 0):
            return "N/A"

        if not t or len(t) == 0:
            time_str = "00:00"
        elif len(t) == 1:
            time_str = f"{t[0]:02d}:00"
        else:
            time_str = f"{t[0]:02d}:{t[1]:02d}"

        return f"{d[0]}-{d[1]:02d}-{d[2]:02d} {time_str}"
    except Exception:
        return "N/A"


def _cache_path(departure: str, destination: str, date: str) -> Path:
    dep = departure.lower().replace(" ", "_")
    dst = destination.lower().replace(" ", "_")
    return CACHE_DIR / f"{dep}_to_{dst}_{date}.csv"


def _flight_to_row(f, dep_code: str, dest_code: str, date: str) -> dict:
    """Convert a single fast-flights result object to a flat dict."""
    legs      = f.flights
    stops     = max(0, len(legs) - 1)
    total_min = sum(lg.duration for lg in legs)
    first     = legs[0]
    last_leg  = legs[-1]
    price     = (f.price * 100) if f.price else 0

    return {
        "airline":       ", ".join(f.airlines) if f.airlines else "Unknown",
        "price":         price,
        "price_str":     f"Rs.{price:,}" if price else "N/A",
        "departure_str": _fmt_dt(first.departure),
        "arrival_str":   _fmt_dt(last_leg.arrival),
        "duration":      f"{total_min // 60}h {total_min % 60}m",
        "duration_min":  total_min,
        "stops":         "Non-stop" if stops == 0 else f"{stops} stop(s)",
        "stops_raw":     stops,
        "from_code":     dep_code,
        "to_code":       dest_code,
        "travel_date":   date,
        "plane":         first.plane_type or "",
        "carbon_g":      f.carbon.emission if f.carbon else 0,
    }


# ─────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────
def scrape(
    departure:   str,
    destination: str,
    date:        str,
    trip:        str  = "one-way",
    seat:        str  = "economy",
    adults:      int  = 1,
    use_cache:   bool = True,
    max_retries: int  = SCRAPER_MAX_RETRIES,
) -> list[dict]:
    """
    Fetch flights from Google Flights via fast-flights.

    Parameters
    ----------
    departure    : City name or IATA code
    destination  : City name or IATA code
    date         : Any format supported by date_parser.parse_date()
    trip         : "one-way" | "round-trip" | "multi-city"
    seat         : "economy" | "business" | "first"
    adults       : Number of adult passengers
    use_cache    : Read/write CSV cache in CACHE_DIR
    max_retries  : Retry attempts on network errors

    Returns
    -------
    List of flight dicts.  Raises RuntimeError if all attempts fail.
    """
    date     = parse_date(date)
    trip_key = _TRIP_MAP.get(trip.lower().strip(), "one-way")
    path     = _cache_path(departure, destination, date)

    # ── Cache hit ─────────────────────────────────────────────
    if use_cache and path.exists():
        df = pd.read_csv(path)
        print(f"[scraper] Cache hit: {path.name} ({len(df)} flights)")
        return df.to_dict(orient="records")

    dep_code  = city_to_iata(departure)
    dest_code = city_to_iata(destination)

    print(f"[scraper] {departure} ({dep_code}) → {destination} ({dest_code})")
    print(f"[scraper] Date: {date}  Trip: {trip_key}  Seat: {seat}  Adults: {adults}")

    query = create_query(
        flights=[FlightQuery(date=date, from_airport=dep_code, to_airport=dest_code)],
        seat=seat,
        trip=trip_key,
        passengers=Passengers(adults=adults),
        language="en-US",
    )
    print(f"[scraper] URL: {query.url()}")

    last_error: Exception | str = "unknown"

    for attempt in range(1, max_retries + 1):
        print(f"[scraper] Attempt {attempt}/{max_retries}…")
        try:
            result = get_flights(query)
            rows   = [_flight_to_row(f, dep_code, dest_code, date) for f in result]

            if not rows:
                last_error = "0 flights returned"
                print(f"[scraper] {last_error}. Try a date 7–30 days from today.")
                continue

            df = pd.DataFrame(rows)
            df.to_csv(path, index=False)
            print(f"[scraper] {len(df)} flights saved → {path.name}")

            # Quick preview
            print("\nTop 5 cheapest:")
            for _, r in df.nsmallest(5, "price").iterrows():
                print(
                    f"  {str(r['airline']):<30} "
                    f"{r['departure_str']} → {r['arrival_str']}  "
                    f"{r['duration']:<8}  {r['stops']:<12}  {r['price_str']}"
                )

            return rows

        except Exception as exc:
            last_error = exc
            print(f"[scraper] Error: {str(exc)[:120]}")
            if attempt < max_retries:
                print("[scraper] Retrying…")

    raise RuntimeError(
        f"All {max_retries} scrape attempts failed.\n"
        f"Last error: {last_error}\n"
        f"Route: {dep_code}→{dest_code} on {date}. "
        "Try a date 7–30 days from today."
    )
